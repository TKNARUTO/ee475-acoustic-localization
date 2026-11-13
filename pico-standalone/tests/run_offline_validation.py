"""Native C validation against generated input and optional local recordings.

Public synthetic check: --output OUTSIDE the public project --skip-real.
Local recordings must be selected explicitly with --recording /local/capture.npz.
This never opens a device, changes DSP thresholds, plays audio, or copies recordings
into the project. Compiler input snapshots and JSON evidence live in --output.
Temporary PCM there is removed after each invocation, including failures.

Ideal-plane-wave angular errors are simulation results. C/PC angle differences on
recordings are implementation agreement, not physical accuracy. Native wall timing
does not establish Pico speed. Full PC confirmation is reported separately from
the arrival-only reference, whose temporal confirmation is deliberately bypassed.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np

N, CHANNELS, RATE = 4096, 7, 48000
DEFAULT_GCC = Path("gcc")
REFERENCE_APP = Path("legacy") / "pico+computer combo sensoring version" / "SEN0325-Pico-Setup"


def resolve_reference_app(project, override=None):
    """Use the frozen shared baseline; never silently import the old root app."""
    app = Path(override).resolve() if override is not None else (project / REFERENCE_APP).resolve()
    required = ("beacon_dsp.py", "highband_dsp.py", "arrival_dsp.py", "array_geometry.json")
    missing = [name for name in required if not (app / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing reference files: " + ", ".join(missing) +
                                "; use --reference-app to select a complete baseline directory")
    return app


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_json(value):
    if isinstance(value, dict):
        return {str(k): finite_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [finite_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return finite_json(value.tolist())
    if isinstance(value, np.generic):
        return finite_json(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path, data):
    Path(path).write_text(json.dumps(finite_json(data), indent=2, allow_nan=False), encoding="utf-8")


def pcm16(samples):
    """Validate BEFORE conversion: a C int16_t sample cannot encode NaN/Inf."""
    a = np.asarray(samples)
    if a.shape != (N, CHANNELS):
        raise ValueError(f"expected {(N, CHANNELS)}, got {a.shape}")
    if not np.issubdtype(a.dtype, np.number) or np.iscomplexobj(a) or not np.isfinite(a).all():
        raise ValueError("input must contain finite real numbers")
    rounded = np.rint(a)
    if np.min(rounded) < -32768 or np.max(rounded) > 32767:
        raise ValueError("PCM16 overflow; the test adapter does not silently clip")
    return np.ascontiguousarray(rounded, dtype="<i2")


def angular_difference(a, b):
    return abs((float(a) - float(b) + 180) % 360 - 180)


def statistics(values):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return {"count": 0, "median": None, "p95": None, "max": None}
    return {"count": len(values), "median": float(np.median(values)),
            "p95": float(np.percentile(values, 95)), "max": float(np.max(values))}


def build_native(project, output, gcc):
    compiler = shutil.which(str(gcc))
    if compiler is None and Path(gcc).is_file():
        compiler = str(Path(gcc).resolve())
    if compiler is None:
        raise FileNotFoundError("Native GCC not found; install a host compiler or pass --gcc /path/to/gcc")
    gcc = Path(compiler).resolve()
    build = output / "native-build"
    (build / "dsp").mkdir(parents=True, exist_ok=True)
    (build / "tests").mkdir(exist_ok=True)
    source = project / "pico-standalone"
    if not (source / "dsp/gap_dsp.c").exists():
        raise FileNotFoundError("DSP source is not ready; no tests have been fabricated")
    hashes = {}
    for path in sorted((source / "dsp").glob("*")):
        if path.suffix in (".c", ".h"):
            shutil.copy2(path, build / "dsp" / path.name)
            hashes[str(path.relative_to(project))] = digest(path)
    harness = source / "tests/dsp_harness.c"
    shutil.copy2(harness, build / "tests/dsp_harness.c")
    hashes[str(harness.relative_to(project))] = digest(harness)
    env = dict(os.environ)
    env["PATH"] = str(gcc.parent) + os.pathsep + env.get("PATH", "")
    exe = build / "gap_dsp_harness.exe"
    command = [str(gcc), "-std=c99", "-O2", "-Wall", "-Wextra",
               "dsp/gap_dsp.c", "tests/dsp_harness.c", "-lm", "-o", exe.name]
    version = subprocess.run([str(gcc), "--version"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", env=env, check=True)
    built = subprocess.run(command, cwd=build, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    (output / "native-build.log").write_text(built.stdout + built.stderr, encoding="utf-8")
    manifest = {"command": command, "compiler_version": version.stdout.splitlines()[0],
                "source_sha256": hashes, "returncode": built.returncode,
                "timing_scope": "native Windows/Cygwin monotonic wall time only, not RP2040"}
    write_json(output / "native-build.json", manifest)
    if built.returncode:
        raise RuntimeError("Native compilation failed; see native-build.log")
    manifest["executable_sha256"] = digest(exe)
    write_json(output / "native-build.json", manifest)
    return exe, env, manifest


def run_native(exe, env, output, frames):
    # Private microphone samples only transit a temporary file OUTSIDE the repo.
    fd, name = tempfile.mkstemp(prefix="private-validation-", suffix=".pcm", dir=output)
    os.close(fd)
    temporary = Path(name)
    try:
        with temporary.open("wb") as stream:
            for frame in frames:
                stream.write(pcm16(frame).tobytes())
        started = time.perf_counter()
        proc = subprocess.run([str(exe), temporary.name], cwd=output, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="strict", timeout=300)
        elapsed = time.perf_counter() - started
        if proc.returncode:
            raise RuntimeError(f"native harness exit {proc.returncode}: {proc.stderr}")
        rows = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        if len(rows) != len(frames) or any(row["index"] != i for i, row in enumerate(rows)):
            raise AssertionError("native output frame count/order mismatch")
        return rows, elapsed
    finally:
        temporary.unlink(missing_ok=True)


def input_boundary_tests(exe, env, output):
    checks = []
    for name, value in (("nan", np.nan), ("positive_inf", np.inf), ("negative_inf", -np.inf),
                        ("positive_overflow", 32768), ("negative_overflow", -32769)):
        data = np.zeros((N, CHANNELS), dtype=float)
        data[0, 0] = value
        try:
            pcm16(data)
            rejected = False
        except ValueError:
            rejected = True
        checks.append({"name": "python_input_rejects_" + name, "passed": rejected})
    for shape in ((4095, 7), (4096, 6), (4096, 8), (4096,)):
        try:
            pcm16(np.zeros(shape))
            rejected = False
        except ValueError:
            rejected = True
        checks.append({"name": "python_input_shape_" + str(shape), "passed": rejected})
    for label, data, expected, rows in (("empty_file", b"", 0, 0), ("one_byte", b"\x00", 3, 0),
            ("one_short_frame", bytes(N * CHANNELS * 2 - 2), 3, 0),
            ("complete_then_truncated", bytes(N * CHANNELS * 2 + 1), 3, 1)):
        path = output / ("boundary-" + label + ".pcm")
        try:
            path.write_bytes(data)
            proc = subprocess.run([str(exe), path.name], cwd=output, env=env,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            checks.append({"name": "harness_" + label,
                           "passed": proc.returncode == expected and len(proc.stdout.splitlines()) == rows,
                           "returncode": proc.returncode, "stderr": proc.stderr.strip()})
        finally:
            path.unlink(missing_ok=True)
    frames = []
    for value in (32760, -32760, 32767, -32768):
        data = np.zeros((N, CHANNELS), dtype=np.int16)
        data[-1, -1] = value
        frames.append(data)
    rows, _ = run_native(exe, env, output, frames)
    for value, row in zip((32760, -32760, 32767, -32768), rows):
        checks.append({"name": "c_clipping_" + str(value),
                       "passed": not row["valid"] and row["reason"] == 4, "c": row})
    return checks


def plane_wave(period, angle, offset_samples, rms_amplitude, noise_sd, rng):
    frequency = np.fft.rfftfreq(N, 1 / RATE)
    spectrum = np.fft.rfft(period) / max(float(np.std(period)), 1e-12)
    channels = []
    for ch in range(CHANNELS):
        # theta=0 => microphone0 receives the wave before the centre microphone.
        advance_s = 0 if ch == 6 else .04 * math.cos(math.radians(angle - ch * 60)) / 343
        phase = np.exp(2j * np.pi * frequency * (advance_s - offset_samples / RATE))
        clean = np.fft.irfft(spectrum * phase, N) * rms_amplitude
        channels.append(clean + rng.normal(0, noise_sd, N))
    return pcm16(np.column_stack(channels))


def synthetic_cases(period):
    rng = np.random.default_rng(20261112)
    cases = []
    for angle in range(0, 360, 30):
        for offset in (0., 511.25, 2047.75, 4093.5):
            for label, amplitude, noise, required in (("strong", 120., 20., True),
                    ("moderate", 30., 20., True), ("weak_exploration", 5., 20., False)):
                cases.append({"id": f"circle-{angle}-{offset}-{label}", "kind": "ideal_plane_wave",
                    "true_synthetic_angle_deg": angle, "offset_samples": offset,
                    "signal_rms_pcm": amplitude, "noise_sd_pcm": noise,
                    "required_detection": required,
                    "audio": plane_wave(period, angle, offset, amplitude, noise, rng)})
    negatives = [{"id": "silence", "kind": "silence", "audio": np.zeros((N, CHANNELS), dtype="<i2")}]
    for i in range(12):
        sd = (2., 20., 200.)[i % 3]
        negatives.append({"id": f"noise-{i}", "kind": "independent_gaussian_noise",
                          "noise_sd_pcm": sd, "audio": pcm16(rng.normal(0, sd, (N, CHANNELS)))})
        # Delayed tone channels are generated separately so the source truly stays at 20 kHz.
        tone_channels = []
        for ch in range(CHANNELS):
            advance = 0 if ch == 6 else .04 * math.cos(math.radians(125 - 60 * ch)) / 343
            tone_channels.append((20., 200., 1500.)[i % 3] * np.sin(
                2 * np.pi * 20000 * (np.arange(N) / RATE + advance) + i * .731))
        negatives.append({"id": f"tone20k-{i}", "kind": "pure_20k_tone", "frequency_hz": 20000,
                          "audio": pcm16(np.column_stack(tone_channels) + rng.normal(0, 2, (N, CHANNELS)))})
        frequencies = np.fft.rfftfreq(N, 1 / RATE)
        mask = (frequencies >= 18000) & (frequencies <= 22000)
        bins = np.flatnonzero(mask)
        wrong = np.zeros(N // 2 + 1, dtype=complex)
        taper = np.minimum(1, np.minimum((frequencies[bins] - 18000 + 12) / 100,
                                        (22000 - frequencies[bins] + 12) / 100))
        wrong[bins] = taper * np.exp(1j * rng.uniform(-np.pi, np.pi, len(bins)))
        window = np.zeros(N); window[:2048] = 1
        ramp = .5 - .5 * np.cos(np.linspace(0, np.pi, 64))
        window[:64] *= ramp; window[2048-64:2048] *= ramp[::-1]
        wrong_period = np.fft.irfft(wrong, N) * window
        negatives.append({"id": f"wrongcode-{i}", "kind": "wrong_random_code_same_band_and_gap",
                          "audio": plane_wave(wrong_period, 125, i * 301.25, 120, 10, rng)})
    turns = [{"id": f"turn-{i}-{angle}", "kind": "unrestricted_turn",
              "true_synthetic_angle_deg": angle, "required_detection": True,
              "audio": plane_wave(period, angle, 700, 120, 20, rng)}
             for i, angle in enumerate((10, 200, 45))]
    return cases, negatives, turns


@contextmanager
def arrival_only_reference():
    # Deliberately separate the portable geometry from PC-only rescue and timing.
    import highband_dsp
    import joint_delay_dsp
    old_fit, old_joint, old_confirm = highband_dsp.fit_delays, joint_delay_dsp.fit_joint_spectral, highband_dsp.confirm_code
    def confirm_without_history(receiver, now):
        details = old_confirm(receiver, now)
        receiver.confirmations = 2
        return {**details, "code_confirmation_windows": 2,
                "offline_temporal_confirmation_bypassed": True}
    try:
        highband_dsp.fit_delays = lambda *args: (None, 0, {})
        joint_delay_dsp.fit_joint_spectral = lambda *args: (None, 0, {})
        highband_dsp.confirm_code = confirm_without_history
        yield
    finally:
        highband_dsp.fit_delays, joint_delay_dsp.fit_joint_spectral, highband_dsp.confirm_code = old_fit, old_joint, old_confirm


def pc_summary(estimate):
    keys = ("valid", "reason", "raw_angle_deg", "angle_deg", "confidence", "code_channels",
            "code_pnr_db", "arrival_rms_samples", "horizontal_projection", "code_confirmation_windows",
            "code_confirmation_gap_s", "candidate_angle_deg", "method", "processing_ms")
    return {k: estimate[k] for k in keys if k in estimate}


def evaluate_group(name, cases, geometry, exe, env, output, estimator_class):
    native, elapsed = run_native(exe, env, output, [case["audio"] for case in cases])
    full = estimator_class(geometry, "coded-gap")
    pc_full = []
    for i, case in enumerate(cases):
        estimate, _ = full.estimate(case["audio"], case.get("health", {}), case.get("received_at", 1 + i * .187))
        pc_full.append(pc_summary(estimate))
    arrival = estimator_class(geometry, "coded-gap")
    pc_arrival = []
    with arrival_only_reference():
        for i, case in enumerate(cases):
            estimate, _ = arrival.estimate(case["audio"], case.get("health", {}), case.get("received_at", 1 + i * .187))
            pc_arrival.append(pc_summary(estimate))
    rows = []
    for i, (case, c, pa, pf) in enumerate(zip(cases, native, pc_arrival, pc_full)):
        row = {k: v for k, v in case.items() if k != "audio"}
        row.update(c=c, pc_arrival_only=pa, pc_full=pf)
        if c["valid"] and "true_synthetic_angle_deg" in row:
            row["synthetic_error_deg"] = angular_difference(c["angle_deg"], row["true_synthetic_angle_deg"])
        if c["valid"] and pa.get("valid"):
            row["c_vs_pc_arrival_deg"] = angular_difference(c["angle_deg"], pa["raw_angle_deg"])
        if c["valid"] and pf.get("valid"):
            row["c_vs_pc_full_deg"] = angular_difference(c["angle_deg"], pf["raw_angle_deg"])
        rows.append(row)
    summary = {"name": name, "frames": len(rows), "c_valid": sum(r["c"]["valid"] for r in rows),
        "pc_arrival_valid": sum(bool(r["pc_arrival_only"].get("valid")) for r in rows),
        "pc_full_valid": sum(bool(r["pc_full"].get("valid")) for r in rows),
        "c_vs_pc_arrival_validity_mismatches": sum(bool(r["c"]["valid"]) != bool(r["pc_arrival_only"].get("valid")) for r in rows),
        "c_reasons": dict(Counter(r["c"]["reason_name"] for r in rows)),
        "synthetic_error_deg": statistics([r["synthetic_error_deg"] for r in rows if "synthetic_error_deg" in r]),
        "c_vs_pc_arrival_deg": statistics([r["c_vs_pc_arrival_deg"] for r in rows if "c_vs_pc_arrival_deg" in r]),
        "c_vs_pc_full_deg": statistics([r["c_vs_pc_full_deg"] for r in rows if "c_vs_pc_full_deg" in r]),
        "native_wall_ms": statistics([r["c"]["native_wall_ms"] for r in rows]),
        "workspace_bytes": max((r["c"]["workspace_bytes"] for r in rows), default=0),
        "native_subprocess_wall_s": elapsed,
        "angle_ground_truth": "ideal generated plane wave only" if any("true_synthetic_angle_deg" in r for r in rows) else "unknown / not an angular accuracy test"}
    write_json(output / (name + ".json"), {"summary": summary, "rows": rows})
    print(json.dumps({"group": name, "c_valid": summary["c_valid"], "frames": len(rows),
                      "arrival_validity_mismatches": summary["c_vs_pc_arrival_validity_mismatches"]}), flush=True)
    return summary, rows


def recorded_cases(path, output, fallback_geometry):
    path = path.resolve()
    sidecar = path.with_suffix(".json")
    metadata = json.loads(sidecar.read_text("utf-8-sig")) if sidecar.exists() else None
    if metadata is not None:
        events = metadata.get("events", [])
        geometry = metadata.get("geometry", fallback_geometry)
    else:
        event_path = path.parent / "events.json"
        if not event_path.exists():
            raise ValueError("real replay requires the saved per-sequence timestamps, not invented times")
        events = json.loads(event_path.read_text("utf-8-sig"))
        geometry = fallback_geometry
    event_by_seq = {int(e.get("health", {}).get("seq", e.get("seq"))): e for e in events}
    with np.load(path, allow_pickle=False) as recording:
        audio = recording["audio"]
        seq = recording["sequence"] if "sequence" in recording else recording["seq"]
        times = recording["received_at"] if "received_at" in recording else None
        generation = recording["generation"] if "generation" in recording else None
        if audio.shape != (len(seq), N, CHANNELS) or audio.dtype != np.dtype("<i2"):
            raise ValueError(f"unexpected recording structure: {audio.shape}, {audio.dtype}")
        cases = []
        for i, sequence in enumerate(seq):
            event = event_by_seq.get(int(sequence))
            if event is None:
                raise ValueError(f"missing event metadata for sequence {sequence}")
            recorded = event.get("estimate", {})
            now = float(times[i] if times is not None else recorded["received_at"])
            if not math.isfinite(now):
                raise ValueError("non-finite recorded timestamp")
            if "received_at" in recorded and abs(now - float(recorded["received_at"])) > 1e-6:
                raise ValueError("npz and event timestamps disagree")
            cases.append({"id": f"seq-{int(sequence)}", "kind": "local_recording",
                "sequence": int(sequence), "received_at": now,
                "generation": int(generation[i]) if generation is not None else None,
                "health": dict(event.get("health", {"seq": int(sequence)})),
                "original_pc_output": pc_summary(recorded), "audio": audio[i].copy()})
    geo_path = output / (path.stem + "-geometry.json")
    write_json(geo_path, geometry)
    manifest = {"file": str(path), "sha256": digest(path), "frames": len(cases),
                "sequence": [r["sequence"] for r in cases],
                "received_at": [r["received_at"] for r in cases],
                "timestamp_source": "npz received_at cross-checked with events" if times is not None else "events.json estimate.received_at by seq",
                "physical_angle_truth": None, "replay_starts_with_empty_pc_confirmation_history": True,
                "raw_audio_copied_to_public_project": False}
    return cases, geo_path, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gcc", type=Path, default=DEFAULT_GCC)
    parser.add_argument("--reference-app", type=Path,
                        help="override the frozen legacy combo Python reference directory")
    parser.add_argument("--recording", type=Path, action="append", default=[])
    parser.add_argument("--background", type=Path)
    parser.add_argument("--skip-real", action="store_true")
    args = parser.parse_args()
    project, output = args.project.resolve(), args.output.resolve()
    app = resolve_reference_app(project, args.reference_app)
    if not args.skip_real and not args.recording and not args.background:
        parser.error("select --skip-real for public synthetic checks, or provide --recording/--background")
    if output == project or project in output.parents:
        raise ValueError("--output must be outside the public project to protect local recordings")
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(app))
    from beacon_dsp import BeaconEstimator, template
    period, _, _ = template("coded-gap")
    config = json.loads((app / "array_geometry.json").read_text("utf-8-sig"))
    synthetic_config = dict(config, heading_offset_deg=0, mirror_view=False, heading_calibrated=False)
    geometry = output / "synthetic-geometry.json"
    write_json(geometry, synthetic_config)
    exe, env, build = build_native(project, output, args.gcc)
    checks = input_boundary_tests(exe, env, output)
    positives, negatives, turns = synthetic_cases(period)
    summaries, recorded_manifest = [], []
    repeat = next(case for case in negatives if case["id"] == "wrongcode-5")
    repeated_wrong_code = [dict(repeat, id="wrongcode-5-repeat-" + str(i)) for i in range(3)]
    for name, cases in (("synthetic-circle", positives), ("synthetic-rejection", negatives),
                        ("synthetic-wrongcode-repeat", repeated_wrong_code), ("synthetic-large-turns", turns)):
        summary, rows = evaluate_group(name, cases, geometry, exe, env, output, BeaconEstimator)
        summaries.append(summary)
        if name in ("synthetic-rejection", "synthetic-wrongcode-repeat"):
            checks.append({"name": name + "_negative_inputs_rejected", "passed": summary["c_valid"] == 0,
                           "false_valid": summary["c_valid"], "frames": len(rows)})
        else:
            required = [r for r in rows if r.get("required_detection")]
            failed = [r["id"] for r in required if not r["c"]["valid"] or r.get("synthetic_error_deg", 360) > 10]
            checks.append({"name": name + "_required_detection_and_10deg_ideal_bound", "passed": not failed,
                           "frames_required": len(required), "failed_ids": failed})
        differences = [r["c_vs_pc_arrival_deg"] for r in rows if "c_vs_pc_arrival_deg" in r]
        checks.append({"name": name + "_arrival_reference_agreement",
                       "passed": summary["c_vs_pc_arrival_validity_mismatches"] == 0 and (not differences or max(differences) < .25),
                       "criterion": "same validity and <0.25 degrees on common valid input; implementation agreement only"})
        checks.append({"name": name + "_finite_valid_output_contract", "passed": all(
            not r["c"]["valid"] or (r["c"]["angle_deg"] is not None and 0 <= r["c"]["angle_deg"] < 360
                and r["c"]["quality"] is not None and 0 <= r["c"]["quality"] <= 1
                and 0 <= r["c"]["code_channels"] <= 7) for r in rows)})
    if not args.skip_real:
        recordings = list(args.recording)
        if args.background:
            recordings.append(args.background)
        for i, path in enumerate(recordings):
            cases, recorded_geometry, manifest = recorded_cases(path, output, config)
            name = "real-background" if args.background and path.resolve() == args.background.resolve() else "real-" + path.stem
            summary, rows = evaluate_group(name, cases, recorded_geometry, exe, env, output, BeaconEstimator)
            summaries.append(summary); recorded_manifest.append(manifest)
            differences = [r["c_vs_pc_arrival_deg"] for r in rows if "c_vs_pc_arrival_deg" in r]
            checks.append({"name": name + "_arrival_reference_agreement",
                           "passed": summary["c_vs_pc_arrival_validity_mismatches"] == 0 and (not differences or max(differences) < .25),
                           "criterion": "implementation agreement only, not actual direction accuracy"})
            if name == "real-background":
                checks.append({"name": "recorded_background_no_valid_bearing", "passed": summary["c_valid"] == 0,
                               "frames": len(rows), "condition": "saved user-declared no-playback recording"})
    result = {"schema": 1, "passed": all(check["passed"] for check in checks),
        "profile": "unchanged HF2 gap 18-22 kHz, 48 kHz, N4096, active2048",
        "template_pcm16_sha256": hashlib.sha256(np.rint(period * 32767).astype("<i2").tobytes()).hexdigest(),
        "build": build, "checks": checks, "groups": summaries, "local_recordings": recorded_manifest,
        "reference_app": str(app), "real_recordings_skipped": args.skip_real,
        "background_executed": args.background is not None and not args.skip_real,
        "limitations": ["No hardware capture/serial/flash/audio playback occurred.",
            "Native monotonic wall time is not Pico compute time or end-to-end latency.",
            "C valid rate is accepted geometry rate, not physical angular accuracy.",
            "Real true angle, distance and movement were not recorded; PC output is not ground truth.",
            "Arrival-only reference bypasses PC two-window confirmation; full PC output retains it.",
            "No thresholds or source DSP were modified by this runner.",
            "NaN/Inf rejected in adapter before int16 conversion; PCM16 cannot represent them."]}
    write_json(output / "validation-results.json", result)
    print(json.dumps({"passed": result["passed"], "checks": len(checks), "result": str(output / "validation-results.json")}), flush=True)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
