"""Analyze monitor.py events.jsonl offline; never imports serial or edits input.

Usage: python analyze_link_trial.py <events.jsonl-or-trial-dir> [--output NEW_DIR]
Without --output, the complete JSON summary is printed. USB observation time is
not wire latency. Missing observations are not automatically lost wire packets.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

UINT32 = 0xffffffff
TX_FIELDS = {"seq": UINT32, "tx_result_seq": UINT32, "uart_seq": UINT32,
             "tx_age_ms": 60000, "tx_valid": 1, "tx_angle_cdeg": 35999, "tx_quality": 1000}
ESP_FIELDS = {"seq": UINT32, "ack_status": 4, "source_valid": 1,
              "raw_cdeg": 35999, "raw_q": 1000, "source_age_ms": 60000, "target_valid": 1}
COMPARISONS = {"tx_angle_cdeg": "raw_cdeg", "tx_quality": "raw_q",
               "tx_age_ms": "source_age_ms", "tx_valid": "source_valid"}
CLASSES = {"ACCEPTED", "DIAG_STALE", "DIAG_INVALID", "RX_REJECTED"}


def crc16(payload):
    crc = 0xffff
    for byte in payload:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 0xffff
    return crc


def integer(value, maximum=UINT32):
    return type(value) is int and 0 <= value <= maximum


def parse_ack(line):
    """Strict wire ACK parser; raises ValueError, including for bad CRC."""
    if len(line) + 1 > 128 or not re.fullmatch(r"@[!-~]+\*[0-9A-Fa-f]{4}", line):
        raise ValueError("ack_frame_format")
    payload, supplied = line[1:].rsplit("*", 1)
    if crc16(payload.encode("ascii")) != int(supplied, 16):
        raise ValueError("ack_bad_crc")
    fields = payload.split(",")
    if len(fields) != 7 or fields[:2] != ["A", "1"] or not re.fullmatch(r"[0-9A-Fa-f]{8}", fields[2]):
        raise ValueError("ack_fields")
    values = []
    for field, maximum in zip(fields[3:], (UINT32, 2, 4, UINT32)):
        if not re.fullmatch(r"[0-9]+", field) or int(field) > maximum:
            raise ValueError("ack_field_range")
        values.append(int(field))
    return dict(session=fields[2].upper(), seq=values[0], type=values[1],
                status=values[2], count=values[3])


def fields(line, prefix):
    if not line.startswith(prefix + " "):
        raise ValueError("wrong_prefix")
    result = {}
    for token in line[len(prefix) + 1:].split():
        if "=" not in token:
            raise ValueError("malformed_key_value")
        key, value = token.split("=", 1)
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = int(value) if re.fullmatch(r"[0-9]+", value) else value
    return result


def distribution(values):
    values = sorted(v for v in values if type(v) in (int, float) and math.isfinite(v))
    if not values:
        return {"count": 0, "min": None, "median": None, "p95": None, "max": None}
    return {"count": len(values), "min": values[0], "median": statistics.median(values),
            "p95": values[max(0, math.ceil(.95 * len(values)) - 1)], "max": values[-1]}


def expected_class(bearing):
    if bearing["ack_status"] in (3, 4):
        return "RX_REJECTED"
    if bearing["ack_status"] == 2 or bearing["source_age_ms"] + 20 > 500:
        return "DIAG_STALE"
    if bearing["ack_status"] == 1 or not bearing["source_valid"]:
        return "DIAG_INVALID"
    return "ACCEPTED"


def missing_position(position, matched_positions):
    if not matched_positions:
        return "unresolved_no_overlap"
    if min(matched_positions) < position < max(matched_positions):
        return "interior_missing_observation"
    return "boundary_unmatched"


def analyze(events, pico_port=None, esp_port=None):
    errors = []; gaps = []; bearings = []; acks = []; stats = []; statuses = []
    banners = defaultdict(list); rejected = []; observations = []
    for index, event in enumerate(events):
        try:
            if not isinstance(event, dict) or not isinstance(event.get("port"), str) or not isinstance(event.get("line"), str):
                raise ValueError("event_schema")
            now = event.get("elapsed_s")
            if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
                raise ValueError("event_time")
            record = {"index": index, "port": event["port"], "elapsed_s": now}
            observations.append(record)
            line = event["line"]
            if line.startswith("GAP "):
                data = json.loads(line[4:])
                if not isinstance(data, dict): raise ValueError("gap_not_object")
                if "gap" in event and event["gap"] != data: raise ValueError("gap_copy_differs_from_line")
                if any(type(v) is float and not math.isfinite(v) for v in data.values()):
                    raise ValueError("gap_nonfinite")
                if not integer(data.get("seq")): raise ValueError("gap_sequence")
                gaps.append(dict(record, data=data))
            elif line.startswith("BEARING "):
                data = fields(line, "BEARING")
                if any(not integer(data.get(k), maximum) for k, maximum in ESP_FIELDS.items()):
                    raise ValueError("bearing_fields")
                if data.get("class") not in CLASSES: raise ValueError("bearing_class")
                bearings.append(dict(record, data=data))
            elif line.startswith("@"):
                acks.append(dict(record, data=parse_ack(line)))
            elif line.startswith("STAT "):
                data = fields(line, "STAT")
                if any(not integer(data.get(k)) for k in ("count", "bad", "lines", "ack_drop", "usb_drop")):
                    raise ValueError("stat_fields")
                stats.append(dict(record, data=data))
            elif line.startswith("STATUS "):
                data = json.loads(line[7:]); session = data.get("session")
                if not isinstance(session, str) or not re.fullmatch(r"[0-9A-Fa-f]{8}", session):
                    raise ValueError("status_session")
                statuses.append(dict(record, data=dict(data, session=session.upper())))
            elif line.startswith(("PICO_GAP_STANDALONE", "READY EE475_GAP_RECEIVER", "SELFTEST ")):
                banners[event["port"]].append(dict(record, line=line))
            elif line.startswith("RX_REJECTED "):
                rejected.append(dict(record, line=line))
        except (ValueError, TypeError, KeyError) as exc:
            errors.append({"index": index, "reason": str(exc), "port": event.get("port") if isinstance(event, dict) else None})

    pico_candidates = sorted({r["port"] for r in gaps})
    esp_candidates = sorted({r["port"] for r in bearings + acks + stats})
    ambiguities = []
    if pico_port is None:
        if len(pico_candidates) == 1: pico_port = pico_candidates[0]
        else: ambiguities.append("expected_one_pico_port")
    if esp_port is None:
        if len(esp_candidates) == 1: esp_port = esp_candidates[0]
        else: ambiguities.append("expected_one_esp_port")
    gaps = [r for r in gaps if r["port"] == pico_port]
    bearings = [r for r in bearings if r["port"] == esp_port]
    acks = [r for r in acks if r["port"] == esp_port]
    stats = [r for r in stats if r["port"] == esp_port]
    statuses = [r for r in statuses if r["port"] == pico_port]
    sessions = sorted({r["data"]["session"] for r in acks + statuses})
    if len(sessions) != 1:
        ambiguities.append("multiple_sessions_unsegmented" if sessions else "session_not_observed")
    # Same-session ESP reboot or repeated Pico banners need manual segmentation;
    # a banner may mean USB reconnect rather than reboot, so do not invent either.
    for port, prefix in ((pico_port, "PICO_GAP_STANDALONE"), (esp_port, "READY EE475_GAP_RECEIVER")):
        if sum(r["line"].startswith(prefix) for r in banners.get(port, [])) > 1:
            ambiguities.append("multiple_banners_reconnect_or_reboot:" + str(port))
    session = sessions[0] if len(sessions) == 1 else None
    session_evidence = "pico_status_and_ack" if statuses and acks else "unique_observed_ack_session_assuming_single_boot" if acks else "pico_status_only"

    current_tx = []; ignored_tx = []; pico_ack_reports = defaultdict(list)
    windows = []
    for r in gaps:
        d = r["data"]
        window = {"event_index": r["index"], "elapsed_s": r["elapsed_s"]}
        window.update({k: d.get(k) for k in ("seq", "fit_valid", "valid", "confirmed", "code_channels", "angle_deg", "quality", "reason", "age_ms", "dsp_us", "dsp_wall_us", "capture_us", "cycle_us", "uart_ready", "uart_seq", "tx_result_seq", "tx_age_ms", "tx_valid", "tx_angle_cdeg", "tx_quality", "ack_seq", "ack_status", "ack_roundtrip_us")})
        windows.append(window)
        if any(not integer(d.get(k), maximum) for k, maximum in TX_FIELDS.items()):
            ignored_tx.append({"index": r["index"], "seq": d["seq"], "reason": "missing_or_invalid_tx_metadata"})
        elif d["tx_result_seq"] != d["seq"]:
            ignored_tx.append({"index": r["index"], "seq": d["seq"], "reason": "old_tx_metadata_not_this_result"})
        else: current_tx.append(r)
        if integer(d.get("ack_seq")) and integer(d.get("ack_status"), 4) and integer(d.get("ack_roundtrip_us")):
            pico_ack_reports[d["ack_seq"]].append(r)

    tx_by_seq = defaultdict(list); esp_by_seq = defaultdict(list); ack_by_seq = defaultdict(list)
    for r in current_tx: tx_by_seq[r["data"]["uart_seq"]].append(r)
    for r in bearings: esp_by_seq[r["data"]["seq"]].append(r)
    for r in acks:
        if r["data"]["type"] == 2: ack_by_seq[r["data"]["seq"]].append(r)
    if any(len(rows) > 1 for rows in tx_by_seq.values()):
        ambiguities.append("repeated_current_tx_sequence")
    matching_allowed = not ambiguities
    matches = []; matched_tx_positions = []; matched_esp_positions = []
    esp_positions = {r["index"]: i for i, r in enumerate(bearings)}
    missing_tx = []; display_errors = []
    for r in bearings:
        if r["data"]["class"] != expected_class(r["data"]):
            display_errors.append({"index": r["index"], "reported": r["data"]["class"], "expected": expected_class(r["data"])})
    if matching_allowed:
        for position, tx in enumerate(current_tx):
            d = tx["data"]; seq = d["uart_seq"]; candidates = esp_by_seq[seq]
            if len(candidates) != 1:
                missing_tx.append({"position": position, "uart_seq": seq, "reason": "multiple_esp_observations" if candidates else "esp_observation_missing"})
                continue
            esp = candidates[0]; e = esp["data"]
            matched_tx_positions.append(position); matched_esp_positions.append(esp_positions[esp["index"]])
            field_checks = {key: {"pico": d[key], "esp": e[other], "equal": d[key] == e[other]} for key, other in COMPARISONS.items()}
            wire_acks = [r for r in ack_by_seq[seq] if r["data"]["session"] == session]
            matching_ack = [r for r in wire_acks if r["data"]["status"] == e["ack_status"]]
            ack_status_conflict = any(r["data"]["status"] != e["ack_status"] for r in wire_acks)
            reports = pico_ack_reports[seq]
            report_values = {(r["data"]["ack_status"], r["data"]["ack_roundtrip_us"]) for r in reports}
            pico_ack_conflict = len(report_values) > 1 or any(status != e["ack_status"] for status, _ in report_values)
            acknowledged = bool(reports) and not pico_ack_conflict
            matches.append({"session": session, "uart_seq": seq, "result_seq": d["seq"],
                "pico_event_index": tx["index"], "esp_event_index": esp["index"],
                "usb_observation_delta_ms_not_wire_latency": (esp["elapsed_s"] - tx["elapsed_s"]) * 1000,
                "fields": field_checks, "exact_fields": all(v["equal"] for v in field_checks.values()),
                "class": e["class"], "target_valid": e["target_valid"], "ack_status": e["ack_status"],
                "esp_ack_observed": bool(matching_ack), "esp_ack_event_indices": [r["index"] for r in matching_ack],
                "esp_ack_status_conflict": ack_status_conflict, "pico_ack_observed": acknowledged,
                "pico_ack_event_indices": [r["index"] for r in reports], "pico_ack_conflict": pico_ack_conflict,
                "ack_roundtrip_us_including_foreground_delay": next(iter(report_values))[1] if acknowledged else None})
        for row in missing_tx:
            row["location"] = missing_position(row["position"], matched_tx_positions)
    else:
        missing_tx = [{"position": i, "uart_seq": r["data"]["uart_seq"], "location": "ambiguous", "reason": "session_or_boot_not_uniquely_bound"} for i, r in enumerate(current_tx)]
    matched_esp_indices = {r["esp_event_index"] for r in matches}
    unmatched_esp = [{"index": r["index"], "seq": r["data"]["seq"],
        "location": missing_position(i, matched_esp_positions) if matching_allowed else "ambiguous"}
        for i, r in enumerate(bearings) if r["index"] not in matched_esp_indices]
    # Missing ACK at the final result may simply not appear until the next GAP.
    tx_seq_positions = {r["data"]["uart_seq"]: i for i, r in enumerate(current_tx)}
    ack_evidence_positions = [tx_seq_positions[r["uart_seq"]] for r in matches if r["esp_ack_observed"] and r["pico_ack_observed"]]
    for row in matches:
        row["missing_ack_location"] = None if row["esp_ack_observed"] and row["pico_ack_observed"] else missing_position(tx_seq_positions[row["uart_seq"]], ack_evidence_positions)

    counter_summary = {}
    for key in ("count", "bad", "lines", "ack_drop", "usb_drop"):
        values = [r["data"][key] for r in stats]
        resets = [stats[i]["index"] for i in range(1, len(values)) if values[i] < values[i-1]]
        counter_summary[key] = {"samples": len(values), "first": values[0] if values else None,
            "last": values[-1] if values else None, "observed_delta": values[-1] - values[0] if len(values) >= 2 and not resets else None,
            "decrease_reset_or_wrap_event_indices": resets}
    if any(value["decrease_reset_or_wrap_event_indices"] for value in counter_summary.values()):
        ambiguities.append("counter_decrease_possible_reboot_or_wrap")
    if ambiguities and matches:
        # A reset discovered through counters invalidates otherwise tempting seq-only matches.
        for row in matches: row["association_ambiguous"] = True

    matched_ack_indices = [i for row in matches for i in row["esp_ack_event_indices"]]
    orphan_acks = [{"index": r["index"], **r["data"],
                   "location": missing_position(r["index"], matched_ack_indices) if matching_allowed else "ambiguous"}
                  for r in acks if r["data"]["type"] == 2 and not any(r["index"] in m["esp_ack_event_indices"] for m in matches)]
    mismatch_count = sum(not r["exact_fields"] for r in matches)
    ack_conflicts = sum(r["esp_ack_status_conflict"] or r["pico_ack_conflict"] for r in matches)
    field_passed = bool(matches) and not ambiguities and not mismatch_count
    interior = sum(r.get("location") == "interior_missing_observation" for r in missing_tx + unmatched_esp)
    interior += sum(r["missing_ack_location"] == "interior_missing_observation" for r in matches)
    interior += sum(r["location"] == "interior_missing_observation" for r in orphan_acks)
    if ambiguities: verdict = "ambiguous"
    elif mismatch_count or ack_conflicts or display_errors or errors: verdict = "inconsistent_observation"
    elif not matches: verdict = "insufficient_overlap"
    elif interior: verdict = "incomplete_interior_observations"
    elif not any(r["pico_ack_observed"] and r["esp_ack_observed"] for r in matches): verdict = "receive_observed_ack_not_confirmed"
    else: verdict = "consistent_observed_overlap"
    raw_data = [r["data"] for r in gaps]
    return {"schema": "ee475-link-trial-v1", "scope": "offline analysis of recorded telemetry; not an independently performed hardware test",
        "overall_verdict": verdict, "matched_field_checks_passed": field_passed,
        "pico_port": pico_port, "esp_port": esp_port, "session": session, "observed_sessions": sessions,
        "session_evidence": session_evidence, "ambiguities": ambiguities, "parse_errors": errors,
        "counts": {"events": len(events), "pico_windows": len(gaps), "current_tx": len(current_tx),
            "ignored_tx_metadata": len(ignored_tx), "esp_bearings": len(bearings), "valid_crc_acks": len(acks),
            "matched_packets": len(matches), "exact_packets": sum(r["exact_fields"] for r in matches),
            "mismatched_packets": mismatch_count, "ack_conflicts": ack_conflicts,
            "esp_and_pico_ack_confirmed": sum(r["esp_ack_observed"] and r["pico_ack_observed"] for r in matches),
            "interior_missing_observations": interior},
        "pico_statistics": {"fit_valid": sum(d.get("fit_valid") == 1 for d in raw_data),
            "valid": sum(d.get("valid") == 1 for d in raw_data), "code_channels": dict(Counter(str(d.get("code_channels")) for d in raw_data)),
            "reasons": dict(Counter(str(d.get("reason")) for d in raw_data)),
            **{key: distribution([d.get(key) for d in raw_data]) for key in ("age_ms", "tx_age_ms", "dsp_us", "dsp_wall_us", "cycle_us")},
            "unique_matched_ack_roundtrip_us": distribution([r["ack_roundtrip_us_including_foreground_delay"] for r in matches])},
        "esp_classes": dict(Counter(r["data"]["class"] for r in bearings)), "esp_counter_deltas": counter_summary,
        "display_errors": display_errors, "rejection_lines": rejected, "matches": matches,
        "missing_tx_observations": missing_tx, "unmatched_esp_observations": unmatched_esp,
        "orphan_bearing_acks": orphan_acks, "ignored_tx_metadata": ignored_tx, "windows": windows,
        "limitations": ["GAP and BEARING lack session fields; a unique observed session is inferred only under the single-boot trial assumption.",
            "Multiple sessions/banners or counter resets require manual trial segmentation; seq alone does not establish identity.",
            "Boundary unmatched means observation-window uncertainty, not a proven harmless packet or proven packet loss.",
            "Interior missing observations can result from USB logging drops; they do not prove UART wire loss.",
            "ESP ACK logs show ACK generation/queueing; matching later Pico metadata supplies receipt evidence.",
            "Pico ACK roundtrip includes foreground parsing delay and is not isolated UART propagation latency.",
            "Raw diagnostics may be stale/invalid; eight B fields cannot distinguish no fit from confirmation state."]}


def analyze_file(path, pico_port=None, esp_port=None):
    path = Path(path)
    if path.is_dir(): path = path / "events.jsonl"
    path = path.resolve()
    before = path.read_bytes(); events = []; input_errors = []
    for index, line in enumerate(before.decode("utf-8-sig").splitlines()):
        if not line.strip(): continue
        try: events.append(json.loads(line))
        except ValueError: input_errors.append({"input_line": index + 1, "reason": "invalid_jsonl"})
    result = analyze(events, pico_port, esp_port)
    result["input"] = {"file": str(path), "sha256": hashlib.sha256(before).hexdigest(), "jsonl_errors": input_errors}
    if input_errors: result["overall_verdict"] = "inconsistent_observation"
    if path.read_bytes() != before: raise RuntimeError("Input changed during analysis; finish the capture before analyzing")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("--output", type=Path, help="Write summary.json in this NEW directory; never overwrite logs")
    parser.add_argument("--pico-port")
    parser.add_argument("--esp-port")
    args = parser.parse_args()
    result = analyze_file(args.events, args.pico_port, args.esp_port)
    rendered = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "summary.json").write_text(rendered, encoding="utf-8")
        print(json.dumps({"overall_verdict": result["overall_verdict"], "counts": result["counts"],
                          "summary": str((args.output / "summary.json").resolve())}, ensure_ascii=False))
    else: print(rendered, end="")


if __name__ == "__main__": main()
