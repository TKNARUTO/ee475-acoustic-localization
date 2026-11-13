"""Finite receive-only recorder with explicit bounded startup isolation.

Startup UART bytes go to warmup.jsonl (base64), followed by one input-buffer
reset per port and LF alignment. The requested trial duration starts afterward.
No filtering/deduplication occurs during the formal trial. Never starts a scan.
"""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time
import serial


def consume_lines(buffer, chunk):
    """Consume each byte once; preserve even repeated/malformed short lines."""
    buffer.extend(chunk)
    lines = []; oversized = 0
    while b"\n" in buffer:
        raw, _, remaining = buffer.partition(b"\n")
        buffer[:] = remaining
        if len(raw) > 2048:
            oversized += 1
        else:
            lines.append(bytes(raw))
    if len(buffer) > 8192:
        buffer.clear(); oversized += 1
    return lines, oversized


def isolate_startup(links, emit, seconds=.75, max_bytes=524288,
                    align_seconds=3., align_max_bytes=65536,
                    clock=time.monotonic, sleep=time.sleep):
    """Bounded, dependency-injected startup reader; no writes/scan commands.

    reset_input_buffer intentionally discards unread OS/driver bytes once. Its
    pre-reset in_waiting count is recorded; these discarded bytes are not claimed
    to have been preserved when the raw capture byte budget has been reached.
    Alignment chunks are preserved in full; bytes after their first LF are also
    retained for the formal reader, with that boundary stated in the event.
    """
    began = clock(); captured = 0; per_port = Counter(); reset_counts = Counter()
    def record(phase, port=None, **values):
        item = {"phase": phase, "warmup_elapsed_s": round(clock()-began, 6),
                "wall_utc": datetime.now(timezone.utc).isoformat()}
        if port is not None: item["port"] = port
        item.update(values); emit(item)
    def raw_record(phase, port, chunk, **values):
        record(phase, port, bytes=len(chunk), raw_base64=base64.b64encode(chunk).decode("ascii"), **values)
    record("warmup_start", seconds=seconds, max_bytes=max_bytes,
           align_seconds=align_seconds, align_max_bytes=align_max_bytes)
    while clock()-began < seconds:
        for port, link in links.items():
            budget = max_bytes-captured
            count = min(max(0, int(link.in_waiting)), 4096, budget)
            if count:
                chunk = link.read(count)
                if len(chunk) > count: raise ValueError("Serial read exceeded the requested bound")
                captured += len(chunk); per_port[port] += len(chunk)
                if chunk: raw_record("warmup_raw", port, chunk)
        sleep(min(.002, max(0., seconds-(clock()-began))))
    record("warmup_drain_end", captured_bytes=captured, budget_exhausted=captured >= max_bytes)
    for port, link in links.items():
        pending = int(link.in_waiting)
        link.reset_input_buffer(); reset_counts[port] += 1
        record("input_buffer_reset_once", port, pending_bytes_before=pending,
               unread_bytes_discarded_not_raw_preserved=True)
    aligned = {}; initial = {port: bytearray() for port in links}; alignment_bytes = 0
    alignment_started = clock()
    while len(aligned) < len(links) and clock()-alignment_started < align_seconds and alignment_bytes < align_max_bytes:
        for port, link in links.items():
            if port in aligned: continue
            count = min(max(0, int(link.in_waiting)), 4096, align_max_bytes-alignment_bytes)
            if not count: continue
            chunk = link.read(count)
            if len(chunk) > count: raise ValueError("Serial read exceeded the requested bound")
            alignment_bytes += len(chunk)
            newline = chunk.find(b"\n")
            retained = len(chunk)-newline-1 if newline >= 0 else 0
            if chunk: raw_record("align_raw", port, chunk,
                discarded_prefix_bytes=newline+1 if newline >= 0 else len(chunk), retained_for_formal_bytes=retained)
            if newline >= 0:
                initial[port].extend(chunk[newline+1:])
                aligned[port] = round(clock()-began, 6)
        if len(aligned) < len(links): sleep(.002)
    summary = {"enabled": True, "requested_seconds": seconds, "drain_max_bytes": max_bytes,
        "captured_startup_bytes": captured, "captured_startup_bytes_per_port": dict(per_port),
        "drain_budget_exhausted": captured >= max_bytes, "input_resets_per_port": dict(reset_counts),
        "alignment_max_seconds": align_seconds, "alignment_max_bytes": align_max_bytes,
        "alignment_bytes": alignment_bytes, "aligned_at_warmup_s": aligned,
        "unresolved_ports": [port for port in links if port not in aligned],
        "retained_prefix_bytes": {port: len(value) for port, value in initial.items()},
        "elapsed_seconds": round(clock()-began, 6), "formal_trial_started": False,
        "scope": "Startup bytes and one reset only; no mid-trial filtering or serial writes"}
    record("alignment_complete" if not summary["unresolved_ports"] else "alignment_failed",
           unresolved_ports=summary["unresolved_ports"], alignment_bytes=alignment_bytes)
    return summary, initial


def numbers(values):
    values = sorted(v for v in values if isinstance(v, (int, float)))
    if not values:
        return None
    return {"median": statistics.median(values), "p95": values[min(len(values)-1, int(.95*(len(values)-1)))], "max": max(values)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", action="append", required=True)
    parser.add_argument("--seconds", type=float, default=15)
    parser.add_argument("--output", type=Path, required=True, help="New local output directory")
    parser.add_argument("--reset-esp32", help="Optional named receiver port to reset once for its startup self-test")
    parser.add_argument("--warmup-seconds", type=float, default=.75, help="Startup raw capture, 0.5..1 second; excluded from formal duration")
    parser.add_argument("--warmup-max-bytes", type=int, default=524288, help="Total startup raw-byte budget, default 512 KiB")
    parser.add_argument("--align-seconds", type=float, default=3., help="Maximum wait for first LF on every port after one input reset")
    parser.add_argument("--align-max-bytes", type=int, default=65536, help="Total post-reset LF-alignment byte budget")
    args = parser.parse_args()
    if not 1 <= args.seconds <= 300 or len(set(args.port)) != len(args.port):
        parser.error("Use 1..300 seconds and distinct ports")
    if args.reset_esp32 and args.reset_esp32 not in args.port:
        parser.error("Reset port must be one of the monitored ports")
    if not .5 <= args.warmup_seconds <= 1 or not .1 <= args.align_seconds <= 5:
        parser.error("Warmup must be 0.5..1 seconds and LF alignment 0.1..5 seconds")
    if not 4096 <= args.warmup_max_bytes <= 4194304 or not 4096 <= args.align_max_bytes <= 4194304:
        parser.error("Byte budgets must be 4096..4194304")
    project = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if output == project or project in output.parents:
        parser.error("Recording output must be outside the shareable project tree")
    args.output.mkdir(parents=True, exist_ok=False)
    links = {}; buffers = {}; results = {p: [] for p in args.port}; text_rows = {p: [] for p in args.port}
    profiles = {p: [] for p in args.port}
    overflow = Counter(); errors = Counter(); started = time.monotonic(); warmup = None
    try:
        for port in args.port:
            link = serial.Serial(port, 115200, timeout=0, write_timeout=.25)
            links[port] = link; buffers[port] = bytearray()
        with (args.output / "warmup.jsonl").open("x", encoding="utf-8") as startup_log:
            def record_startup(item):
                startup_log.write(json.dumps(item, ensure_ascii=False) + "\n")
            warmup, buffers = isolate_startup(links, record_startup, args.warmup_seconds,
                args.warmup_max_bytes, args.align_seconds, args.align_max_bytes)
        (args.output / "warmup-summary.json").write_text(json.dumps(warmup, indent=2), encoding="utf-8")
        if warmup["unresolved_ports"]:
            raise RuntimeError("No formal trial started: LF alignment failed; inspect warmup evidence")
        if args.reset_esp32:
            # Preserve boot/self-test output: the requested reset occurs AFTER
            # startup isolation. Do not flush this fresh boot output afterward.
            warmup["pre_reset_retained_bytes_discarded"] = len(buffers[args.reset_esp32])
            buffers[args.reset_esp32].clear()
            from esptool.reset import HardReset
            HardReset(links[args.reset_esp32]).reset()
            warmup["explicit_esp32_reset_after_warmup"] = args.reset_esp32
        started = time.monotonic()
        warmup["formal_trial_started"] = True
        warmup["formal_trial_start_wall_utc"] = datetime.now(timezone.utc).isoformat()
        (args.output / "warmup-summary.json").write_text(json.dumps(warmup, indent=2), encoding="utf-8")
        with (args.output / "events.jsonl").open("x", encoding="utf-8") as log:
            while time.monotonic()-started < args.seconds:
                for port, link in links.items():
                    chunk = link.read(min(link.in_waiting, 4096))
                    raw_lines, dropped = consume_lines(buffers[port], chunk)
                    overflow[port] += dropped
                    for raw in raw_lines:
                        line = raw.decode("utf-8", errors="replace").rstrip("\r")
                        row = {"port": port, "elapsed_s": round(time.monotonic()-started, 6),
                               "wall_utc": datetime.now(timezone.utc).isoformat(), "line": line}
                        if line.startswith("GAP "):
                            try:
                                data = json.loads(line[4:])
                                if not isinstance(data, dict): raise ValueError("Not an object")
                                row["gap"] = data; results[port].append(row)
                            except (ValueError, TypeError):
                                errors[port] += 1
                        elif line.startswith("PROFILE "):
                            try:
                                data = json.loads(line[8:])
                                if not isinstance(data, dict): raise ValueError("Not an object")
                                row["profile"] = data; profiles[port].append(data)
                            except (ValueError, TypeError):
                                errors[port] += 1
                        text_rows[port].append(line)
                        log.write(json.dumps(row, ensure_ascii=False) + "\n")
                time.sleep(.002)
    finally:
        for link in links.values(): link.close()
    summary = {"duration_s": round(time.monotonic()-started, 3), "scan_commands_sent": 0,
               "optional_esp32_reset": args.reset_esp32, "warmup": warmup,
               "recording_scope": "Formal duration excludes bounded startup isolation; no mid-trial deduplication", "ports": {}}
    for port in args.port:
        rows = results[port]; data = [r["gap"] for r in rows]
        summary["ports"][port] = {
            "lines": len(text_rows[port]), "windows": len(data),
            "valid": sum(d.get("valid") == 1 for d in data),
            "fit_valid": sum(d.get("fit_valid") == 1 for d in data),
            "uart_ready": sum(d.get("uart_ready") == 1 for d in data),
            "reasons": dict(Counter(d.get("reason", "unknown") for d in data)),
            "dsp_us": numbers([d.get("dsp_us") for d in data]),
            "capture_us": numbers([d.get("capture_us") for d in data]),
            "age_ms": numbers([d.get("age_ms") for d in data]),
            "result_interval_ms": numbers([(b["elapsed_s"]-a["elapsed_s"])*1000 for a,b in zip(rows, rows[1:])]),
            "last_gap": data[-1] if data else None,
            "pipeline_fields_us": {key: numbers([d.get(key) for d in data]) for key in
                ("unpack_total_us", "max_block_us", "capture_wait_us", "cycle_us", "result_interval_us")},
            "profile_fields_us": {key: numbers([d.get(key) for d in profiles[port]]) for key in
                sorted({k for d in profiles[port] for k in d if k.endswith("_us")})},
            "banners_and_selftests": [s for s in text_rows[port] if s.startswith(("READY ", "SELFTEST ", "PICO_GAP_STANDALONE", "STAT "))],
            "bad_json": errors[port], "line_overflows": overflow[port],
        }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
