"""Synthetic telemetry fixtures only; no serial, raw audio or hardware claims."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/analyze_link_trial.py"
SPEC = importlib.util.spec_from_file_location("analyze_link_trial", SCRIPT)
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def ack(seq, status=1, session="1234ABCD", kind=2):
    payload = f"A,1,{session},{seq},{kind},{status},{seq + 1}"
    return f"@{payload}*{analysis.crc16(payload.encode()):04X}"


def row(port, now, line):
    return {"port": port, "elapsed_s": now, "line": line}


def gap(seq, **overrides):
    data = {"seq": seq, "fit_valid": 1, "valid": 0, "confirmed": 1, "code_channels": 7,
        "angle_deg": 12.34, "quality": .678, "reason": "stale_measurement", "age_ms": 700,
        "dsp_us": 655000, "dsp_wall_us": 655000, "tx_result_seq": seq, "uart_seq": seq,
        "tx_age_ms": 700, "tx_valid": 0, "tx_angle_cdeg": 1234, "tx_quality": 678,
        "ack_seq": seq - 1, "ack_status": 1 if seq > 1 else analysis.UINT32,
        "ack_roundtrip_us": 4500}
    data.update(overrides)
    return row("PICO", float(seq), "GAP " + json.dumps(data))


def bearing(seq, **overrides):
    data = {"seq": seq, "class": "DIAG_STALE", "ack_status": 1, "source_valid": 0,
            "raw_cdeg": 1234, "raw_q": 678, "source_age_ms": 700, "target_valid": 0}
    data.update(overrides)
    return row("ESP", float(seq) + .002, "BEARING " + " ".join(f"{k}={v}" for k,v in data.items()))


def trial():
    result = []
    for seq in (1, 2, 3):
        result.extend([gap(seq), row("ESP", seq + .001, ack(seq)), bearing(seq)])
    return result


class LinkAnalysisTests(unittest.TestCase):
    def test_complete_overlap_and_tail_ack_boundary(self):
        result = analysis.analyze(trial())
        self.assertEqual(result["overall_verdict"], "consistent_observed_overlap")
        self.assertTrue(result["matched_field_checks_passed"])
        self.assertEqual(result["counts"]["matched_packets"], 3)
        self.assertEqual(result["counts"]["esp_and_pico_ack_confirmed"], 2)
        self.assertEqual(result["matches"][-1]["missing_ack_location"], "boundary_unmatched")

    def test_bad_crc_never_becomes_ack(self):
        events = trial(); events[1]["line"] = events[1]["line"][:-4] + "0000"
        result = analysis.analyze(events)
        self.assertEqual(result["parse_errors"][0]["reason"], "ack_bad_crc")
        self.assertFalse(result["matches"][0]["esp_ack_observed"])
        self.assertEqual(result["overall_verdict"], "inconsistent_observation")

    def test_wrong_ack_sequence(self):
        events = trial(); events[4]["line"] = ack(99)
        result = analysis.analyze(events)
        self.assertFalse(result["matches"][1]["esp_ack_observed"])
        self.assertEqual(result["overall_verdict"], "incomplete_interior_observations")
        self.assertEqual(result["orphan_bearing_acks"][0]["seq"], 99)

    def test_multiple_sessions_never_match_by_seq_alone(self):
        events = trial(); events[4]["line"] = ack(2, session="87654321")
        result = analysis.analyze(events)
        self.assertEqual(result["overall_verdict"], "ambiguous")
        self.assertFalse(result["matched_field_checks_passed"])
        self.assertEqual(result["matches"], [])

    def test_status_session_conflicts_with_ack(self):
        events = trial() + [row("PICO", 4, 'STATUS {"session":"DEADBEEF"}')]
        self.assertEqual(analysis.analyze(events)["overall_verdict"], "ambiguous")

    def test_old_tx_metadata_is_not_current(self):
        events = trial(); events[3] = gap(2, tx_result_seq=1, uart_seq=1)
        result = analysis.analyze(events)
        self.assertEqual(result["counts"]["current_tx"], 2)
        self.assertEqual(result["ignored_tx_metadata"][0]["reason"], "old_tx_metadata_not_this_result")
        self.assertEqual(result["overall_verdict"], "incomplete_interior_observations")

    def test_field_difference(self):
        events = trial(); events[5] = bearing(2, raw_cdeg=9999)
        result = analysis.analyze(events)
        self.assertFalse(result["matched_field_checks_passed"])
        self.assertEqual(result["matches"][1]["fields"]["tx_angle_cdeg"]["esp"], 9999)

    def test_zero_degree_is_exact_not_missing(self):
        events = trial(); events[3] = gap(2, tx_angle_cdeg=0); events[5] = bearing(2, raw_cdeg=0)
        self.assertTrue(analysis.analyze(events)["matched_field_checks_passed"])

    def test_interior_missing_vs_boundary(self):
        events = trial(); del events[5]
        result = analysis.analyze(events)
        self.assertEqual(result["missing_tx_observations"][0]["location"], "interior_missing_observation")
        events = trial(); del events[8]
        result = analysis.analyze(events)
        self.assertEqual(result["missing_tx_observations"][0]["location"], "boundary_unmatched")

    def test_pico_ack_status_conflict(self):
        events = trial(); events[3] = gap(2, ack_status=0)
        result = analysis.analyze(events)
        self.assertTrue(result["matches"][0]["pico_ack_conflict"])
        self.assertEqual(result["overall_verdict"], "inconsistent_observation")

    def test_stat_delta_and_reset(self):
        events = trial() + [row("ESP", 4, "STAT count=10 valid=0 bad=2 lines=0 ack_drop=0 usb_drop=1"),
                            row("ESP", 5, "STAT count=14 valid=0 bad=4 lines=1 ack_drop=0 usb_drop=3")]
        result = analysis.analyze(events)
        self.assertEqual(result["esp_counter_deltas"]["bad"]["observed_delta"], 2)
        events.append(row("ESP", 6, "STAT count=0 valid=0 bad=0 lines=0 ack_drop=0 usb_drop=0"))
        result = analysis.analyze(events)
        self.assertEqual(result["overall_verdict"], "ambiguous")
        self.assertIsNone(result["esp_counter_deltas"]["bad"]["observed_delta"])

    def test_repeat_boot_banner_is_ambiguous(self):
        events = trial() + [row("PICO", 4, "PICO_GAP_STANDALONE v0.2"), row("PICO", 5, "PICO_GAP_STANDALONE v0.2")]
        self.assertEqual(analysis.analyze(events)["overall_verdict"], "ambiguous")

    def test_nonfinite_telemetry_is_rejected(self):
        events = trial(); events[3] = gap(2, dsp_us=float("nan"))
        self.assertIn("gap_nonfinite", [e["reason"] for e in analysis.analyze(events)["parse_errors"]])

    def test_no_ack_session_means_no_identity_claim(self):
        events = [gap(1), bearing(1)]
        result = analysis.analyze(events)
        self.assertEqual(result["overall_verdict"], "ambiguous")
        self.assertEqual(result["matches"], [])

    def test_rejected_class_priority(self):
        events = trial(); events[4]["line"] = ack(2, status=3)
        events[5] = bearing(2, ack_status=3, **{"class": "RX_REJECTED"})
        events[6] = gap(3, ack_status=3)
        result = analysis.analyze(events)
        self.assertEqual(result["display_errors"], [])
        self.assertEqual(result["matches"][1]["ack_status"], 3)

    def test_input_not_mutated(self):
        events = trial(); before = copy.deepcopy(events)
        analysis.analyze(events)
        self.assertEqual(events, before)


if __name__ == "__main__": unittest.main()
