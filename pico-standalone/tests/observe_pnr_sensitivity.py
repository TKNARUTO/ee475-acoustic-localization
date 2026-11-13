"""Observation only: explore PNR thresholds in an isolated Python reference.

Production C and Python source files are never edited. This does not promote a
threshold or turn an observational result into a production acceptance result.
The C binary at --baseline is the unchanged 12.5 dB build. Higher thresholds are
Python-reference experiments, with raw geometry and full-PC confirmation separate.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys

import numpy as np

from run_offline_validation import (N, RATE, CHANNELS, angular_difference,
    arrival_only_reference, digest, pc_summary, plane_wave, recorded_cases,
    run_native, statistics, synthetic_cases, write_json, resolve_reference_app)


@contextmanager
def temporary_pnr(threshold):
    import highband_dsp
    original = highband_dsp.PNR_MIN
    try:
        highband_dsp.PNR_MIN = threshold
        yield
    finally:
        highband_dsp.PNR_MIN = original


def expanded_wrong_codes(count):
    cases = []
    frequencies = np.fft.rfftfreq(N, 1 / RATE)
    bins = np.flatnonzero((frequencies >= 18000) & (frequencies <= 22000))
    taper = np.minimum(1, np.minimum((frequencies[bins] - 18000 + 12) / 100,
                                    (22000 - frequencies[bins] + 12) / 100))
    window = np.zeros(N); window[:2048] = 1
    ramp = .5 - .5 * np.cos(np.linspace(0, np.pi, 64))
    window[:64] *= ramp; window[1984:2048] *= ramp[::-1]
    for i in range(count):
        seed = 2026111200 + i
        rng = np.random.default_rng(seed)
        spectrum = np.zeros(N // 2 + 1, dtype=complex)
        spectrum[bins] = taper * np.exp(1j * rng.uniform(-np.pi, np.pi, len(bins)))
        period = np.fft.irfft(spectrum, N) * window
        cases.append({"id": f"expanded-wrong-{i}", "seed": seed,
            "kind": "wrong_random_code_same_band_and_gap",
            "audio": plane_wave(period, (i * 137.508) % 360, (i * 37.125) % N, 120, 10, rng)})
    return cases


def reference_sequence(cases, geometry, estimator_class):
    full = estimator_class(geometry, "coded-gap")
    full_rows = []
    for i, case in enumerate(cases):
        result, _ = full.estimate(case["audio"], case.get("health", {}),
                                  case.get("received_at", 1 + i * .187))
        full_rows.append(pc_summary(result))
    arrival = estimator_class(geometry, "coded-gap")
    rows = []
    with arrival_only_reference():
        for i, case in enumerate(cases):
            result, _ = arrival.estimate(case["audio"], case.get("health", {}),
                                         case.get("received_at", 1 + i * .187))
            summary = pc_summary(result)
            summary["channel_pnr_db_rounded"] = [d["pnr_db"] for d in result.get("code_channel_diagnostics", [])]
            rows.append({"id": case["id"], "sequence": case.get("sequence"),
                         "received_at": case.get("received_at"),
                         "arrival_geometry": summary, "pc_full": full_rows[i]})
    return rows


def summarize(rows):
    return {"frames": len(rows),
        "code_at_least_4": sum(r["arrival_geometry"].get("code_channels", 0) >= 4 for r in rows),
        "code_at_least_6": sum(r["arrival_geometry"].get("code_channels", 0) >= 6 for r in rows),
        "geometry_valid": sum(bool(r["arrival_geometry"].get("valid")) for r in rows),
        "full_pc_valid": sum(bool(r["pc_full"].get("valid")) for r in rows),
        "code_channels_histogram": dict(Counter(r["arrival_geometry"].get("code_channels", 0) for r in rows))}


def weak_sweep(project, app, baseline, output, estimator_class, period):
    """Separate edge-of-detection experiment; no automatic threshold choice."""
    import highband_dsp
    if highband_dsp.PNR_MIN != 12.5:
        raise ValueError("weak observation expects the unchanged 12.5 dB production reference")
    source_paths = [app / "highband_dsp.py",
                    project / "pico-standalone/dsp/gap_dsp.c"]
    before = {str(path): digest(path) for path in source_paths}
    config = json.loads((app / "array_geometry.json").read_text("utf-8-sig"))
    geometry = output / "weak-synthetic-geometry.json"
    write_json(geometry, dict(config, heading_offset_deg=0, mirror_view=False, heading_calibrated=False))
    rng = np.random.default_rng(2026111209)
    cases = []
    for amplitude in (.25, .5, .75, 1., 1.5, 2., 3., 5.):
        for angle in (0, 90, 180, 270):
            for offset in (511.25, 4093.5):
                cases.append({"id": f"weak-{amplitude}-{angle}-{offset}", "amplitude": amplitude,
                    "true_synthetic_angle_deg": angle, "offset_samples": offset,
                    "audio": plane_wave(period, angle, offset, amplitude, 20, rng)})
    build = json.loads((baseline / "native-build.json").read_text("utf-8"))
    env = dict(os.environ)
    env["PATH"] = str(Path(build["command"][0]).parent) + os.pathsep + env.get("PATH", "")
    native, _ = run_native(baseline / "native-build/gap_dsp_harness.exe", env, output,
                           [r["audio"] for r in cases])
    thresholds, concise, original_ids = [], [], set()
    for threshold in (12.5, 13., 14., 15.):
        with temporary_pnr(threshold):
            rows = reference_sequence(cases, geometry, estimator_class)
        for row, case, c in zip(rows, cases, native):
            row.update(amplitude=case["amplitude"], true_synthetic_angle_deg=case["true_synthetic_angle_deg"],
                       offset_samples=case["offset_samples"], baseline_c12_5=c)
            if row["arrival_geometry"].get("valid"):
                row["synthetic_error_deg"] = angular_difference(row["arrival_geometry"]["raw_angle_deg"], case["true_synthetic_angle_deg"])
        ids = {r["id"] for r in rows if r["arrival_geometry"].get("valid")}
        if threshold == 12.5: original_ids = ids
        by_amplitude = []
        for amplitude in (.25, .5, .75, 1., 1.5, 2., 3., 5.):
            selected = [r for r in rows if r["amplitude"] == amplitude]
            by_amplitude.append({"signal_rms_pcm": amplitude, "noise_sd_pcm": 20,
                **summarize(selected), "synthetic_error_deg": statistics([r["synthetic_error_deg"] for r in selected if "synthetic_error_deg" in r])})
        summary = {"threshold_db": threshold, **summarize(rows),
            "lost_geometry_ids_vs12_5": sorted(original_ids - ids),
            "gained_geometry_ids_vs12_5": sorted(ids - original_ids),
            "synthetic_error_deg": statistics([r["synthetic_error_deg"] for r in rows if "synthetic_error_deg" in r]),
            "by_amplitude": by_amplitude}
        concise.append(summary); thresholds.append({"summary": summary, "rows": rows})
        print(json.dumps({"weak_threshold_db": threshold, "geometry_valid": len(ids), "frames": len(rows),
                          "lost_vs12_5": len(original_ids - ids)}), flush=True)
    after = {str(path): digest(path) for path in source_paths}
    result = {"observational_only": True, "production_threshold_changed": False,
        "source_files_unchanged": before == after, "process_threshold_restored": highband_dsp.PNR_MIN == 12.5,
        "source_sha256_before": before, "source_sha256_after": after,
        "native12_5_valid": sum(bool(r["valid"]) for r in native), "threshold_summary": concise,
        "thresholds": thresholds, "seed": 2026111209,
        "limitations": ["Weak ideal-plane-wave threshold experiment, not a physical phone/range measurement.",
            "Higher threshold may lose geometrically valid but noisy true-code observations.",
            "Baseline C is unchanged 12.5 dB; other thresholds are Python reference only.",
            "Quantization to PCM16 is included. No raw microphone recording is generated or copied."]}
    write_json(output / "pnr-weak-observations.json", result)
    if before != after or highband_dsp.PNR_MIN != 12.5:
        raise AssertionError("source or threshold changed")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--reference-app", type=Path,
                        help="override the frozen legacy combo Python reference directory")
    parser.add_argument("--recording", type=Path, action="append", default=[])
    parser.add_argument("--skip-real", action="store_true",
                        help="use only public synthetic input; no private recordings are required")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wrong-code-count", type=int, default=128)
    parser.add_argument("--weak-only", action="store_true",
                        help="separate 64-case edge-of-detection sweep; does not rerun expanded wrong codes")
    args = parser.parse_args()
    project, baseline, output = args.project.resolve(), args.baseline.resolve(), args.output.resolve()
    app = resolve_reference_app(project, args.reference_app)
    if not args.weak_only and not args.skip_real and not args.recording:
        parser.error("select --skip-real for public observations, or provide --recording")
    if output == project or project in output.parents:
        raise ValueError("keep observational output outside the public project")
    if not 1 <= args.wrong_code_count <= 1024:
        raise ValueError("wrong-code count must be bounded to 1..1024")
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(app))
    from beacon_dsp import BeaconEstimator, template
    import highband_dsp
    if args.weak_only:
        period, _, _ = template("coded-gap")
        return weak_sweep(project, app, baseline, output, BeaconEstimator, period)
    protected = [app / "highband_dsp.py", app / "beacon_dsp.py", app / "arrival_dsp.py",
                 project / "pico-standalone/dsp/gap_dsp.c"]
    before = {str(path): digest(path) for path in protected}
    original_threshold = highband_dsp.PNR_MIN
    if original_threshold != 12.5:
        raise ValueError("this observation expects the unchanged 12.5 dB production reference")
    period, _, _ = template("coded-gap")
    positives, original_negatives, _ = synthetic_cases(period)
    wrong = expanded_wrong_codes(args.wrong_code_count)
    known_control = dict(next(c for c in original_negatives if c["id"] == "wrongcode-5"),
                         id="known-wrongcode-5-control")
    config = json.loads((app / "array_geometry.json").read_text("utf-8-sig"))
    geometry = output / "synthetic-geometry.json"
    write_json(geometry, dict(config, heading_offset_deg=0, mirror_view=False, heading_calibrated=False))
    groups = [("synthetic144", positives, geometry)]
    real_manifests = []
    for index, path in enumerate([] if args.skip_real else args.recording):
        cases, geo, manifest = recorded_cases(path, output, config)
        groups.append((f"real-{index + 1}", cases, geo)); real_manifests.append(manifest)
    build = json.loads((baseline / "native-build.json").read_text("utf-8"))
    exe = baseline / "native-build/gap_dsp_harness.exe"
    env = dict(os.environ)
    env["PATH"] = str(Path(build["command"][0]).parent) + os.pathsep + env.get("PATH", "")
    c_baseline, _ = run_native(exe, env, output, [r["audio"] for r in wrong + [known_control]])
    real_pnr = []
    for path in ([] if args.skip_real else sorted(baseline.glob("real-launcher*.json"))):
        for row in json.loads(path.read_text("utf-8"))["rows"]:
            if row["c"]["valid"]:
                pnr = sorted(row["c"]["pnr_db"], reverse=True)
                real_pnr.append({"sequence": row["sequence"], "received_at": row["received_at"],
                    "pnr_db_by_channel": row["c"]["pnr_db"], "fifth_highest_db": pnr[4],
                    "sixth_highest_db": pnr[5], "weakest_db": pnr[6], "strongest_db": pnr[0]})
    all_thresholds, concise = [], []
    baseline_valid_ids = {}
    for threshold in (12.5, 13., 14., 15.):
        with temporary_pnr(threshold):
            group_rows, group_summary = {}, {}
            for name, cases, geo in groups:
                rows = reference_sequence(cases, geo, BeaconEstimator)
                summary = summarize(rows)
                ids = {r["id"] for r in rows if r["arrival_geometry"].get("valid")}
                if threshold == 12.5: baseline_valid_ids[name] = ids
                summary["lost_geometry_ids_vs12_5"] = sorted(baseline_valid_ids[name] - ids)
                summary["gained_geometry_ids_vs12_5"] = sorted(ids - baseline_valid_ids[name])
                group_rows[name], group_summary[name] = rows, summary
            wrong_rows = []
            for i, case in enumerate(wrong + [known_control]):
                # Repeat the exact same wrong-code waveform: confirmation is not identity validation.
                repeated = [dict(case, id=case["id"] + f"-repeat{j}") for j in range(3)]
                rows = reference_sequence(repeated, geometry, BeaconEstimator)
                wrong_rows.append({"id": case["id"], "seed": case.get("seed"),
                    "baseline_c12_5": c_baseline[i], "repeat_rows": rows,
                    "geometry_valid": rows[0]["arrival_geometry"].get("valid", False),
                    "full_pc_any_valid_over3": any(r["pc_full"].get("valid") for r in rows),
                    "code_channels": rows[0]["arrival_geometry"].get("code_channels", 0)})
            random_rows = wrong_rows[:-1]
            row = {"threshold_db": threshold, "synthetic_geometry_valid": group_summary["synthetic144"]["geometry_valid"],
                "real_geometry_valid": sum(v["geometry_valid"] for n, v in group_summary.items() if n.startswith("real-")),
                "real_full_pc_valid": sum(v["full_pc_valid"] for n, v in group_summary.items() if n.startswith("real-")),
                "random_wrong_code_count": len(random_rows),
                "random_wrong_geometry_valid": sum(bool(r["geometry_valid"]) for r in random_rows),
                "random_wrong_full_pc_any_valid_over3": sum(bool(r["full_pc_any_valid_over3"]) for r in random_rows),
                "known_wrong_control_geometry_valid": bool(wrong_rows[-1]["geometry_valid"]),
                "known_wrong_control_full_pc_any_valid_over3": bool(wrong_rows[-1]["full_pc_any_valid_over3"])}
            concise.append(row)
            all_thresholds.append({"threshold_db": threshold, "summary": row,
                                   "groups": group_summary, "rows": group_rows, "wrong_codes": wrong_rows})
            print(json.dumps(row), flush=True)
    after = {str(path): digest(path) for path in protected}
    c_valid = sum(bool(row["valid"]) for row in c_baseline[:-1])
    baseline_wrong_rows = all_thresholds[0]["wrong_codes"]
    c_reference_mismatches = [r["id"] for r in baseline_wrong_rows
                              if bool(r["baseline_c12_5"]["valid"]) != bool(r["geometry_valid"])]
    result = {"observational_only": True, "production_threshold_changed": False,
        "source_files_unchanged": before == after,
        "process_threshold_restored": highband_dsp.PNR_MIN == original_threshold,
        "production_source_sha256_before": before, "production_source_sha256_after": after,
        "baseline_c_build": build, "expanded_negative_c12_5_valid": c_valid,
        "c_vs_reference12_5_validity_mismatch_ids": c_reference_mismatches,
        "threshold_summary": concise, "real_baseline_geometry_valid_pnr": real_pnr,
        "real_valid_pnr_ranges": {key: {**statistics([r[key] for r in real_pnr]),
                                       "min": min((r[key] for r in real_pnr), default=None)}
                                  for key in ("fifth_highest_db", "sixth_highest_db", "weakest_db", "strongest_db")},
        "real_recordings": real_manifests, "thresholds": all_thresholds,
        "reference_app": str(app), "real_recordings_skipped": args.skip_real,
        "limitations": ["Higher thresholds evaluated only in isolated Python reference; production C untouched.",
            "No new recordings, serial, playback or flash access.",
            "Synthetic weak signals are finite ideal-plane-wave fixtures, not phone range measurements.",
            "Any explicitly selected local recordings do not cover all weak/distant/noisy deployment conditions.",
            "Full PC uses its original temporal confirmation; arrival-only bypasses it for geometry comparison.",
            "No threshold guarantees beacon identity or authentication."]}
    write_json(output / "pnr-observations.json", result)
    if before != after or highband_dsp.PNR_MIN != original_threshold:
        raise AssertionError("production source or process threshold changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
