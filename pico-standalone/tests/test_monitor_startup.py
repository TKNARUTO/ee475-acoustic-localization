"""Fake serial startup/buffer tests; no ports opened and no hardware claims."""
import base64
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/monitor.py"
SPEC = importlib.util.spec_from_file_location("monitor_under_test", SCRIPT)
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


class Clock:
    def __init__(self): self.value = 0.
    def __call__(self): return self.value
    def sleep(self, seconds): self.value += max(seconds, .000001)


class Port:
    def __init__(self, startup, after_reset, limit=4096):
        self.data = bytearray(startup); self.after_reset = after_reset
        self.limit = limit; self.resets = 0; self.read_requests = []
    @property
    def in_waiting(self): return len(self.data)
    def read(self, count):
        self.read_requests.append(count)
        actual = min(count, self.limit)
        chunk = bytes(self.data[:actual]); del self.data[:actual]
        return chunk
    def reset_input_buffer(self):
        self.resets += 1; self.data[:] = self.after_reset
    def write(self, data): raise AssertionError("Recorder must not write serial commands")


def warmup(ports, **kwargs):
    clock = Clock(); records = []
    options = dict(seconds=.01, max_bytes=10000, align_seconds=.1, align_max_bytes=10000)
    options.update(kwargs)
    summary, buffers = monitor.isolate_startup(ports, records.append, clock=clock, sleep=clock.sleep, **options)
    return summary, buffers, records


class StartupTests(unittest.TestCase):
    def test_consumption_exact_under_chunk_boundaries(self):
        source = b"fragment\n" + b"STAT same\n" * 1597 + b"invalid \xff body\nlast\npartial"
        expected = source.split(b"\n")[:-1]
        for size in (1, 7, 4096):
            buffer = bytearray(); actual = []; dropped = 0
            for offset in range(0, len(source), size):
                rows, count = monitor.consume_lines(buffer, source[offset:offset+size])
                actual.extend(rows); dropped += count
            self.assertEqual(actual, expected)
            self.assertEqual(buffer, b"partial")
            self.assertEqual(dropped, 0)
            self.assertEqual(monitor.consume_lines(buffer, b""), ([], 0))

    def test_repeated_startup_bytes_preserved_not_deduplicated(self):
        startup = b"old STAT\n" * 20
        port = Port(startup, b"partial-tail\nNEW complete\n")
        summary, buffers, records = warmup({"ESP": port})
        saved = b"".join(base64.b64decode(r["raw_base64"]) for r in records if r["phase"] == "warmup_raw")
        self.assertEqual(saved, startup)
        self.assertEqual(summary["captured_startup_bytes"], len(startup))
        self.assertEqual(port.resets, 1)
        self.assertEqual(buffers["ESP"], b"NEW complete\n")
        self.assertEqual(summary["unresolved_ports"], [])

    def test_reset_discard_budget_explicit(self):
        port = Port(b"x" * 10000, b"tail\nnext\n")
        summary, _, records = warmup({"ESP": port}, max_bytes=64)
        self.assertEqual(summary["captured_startup_bytes"], 64)
        self.assertTrue(summary["drain_budget_exhausted"])
        reset = next(r for r in records if r["phase"] == "input_buffer_reset_once")
        self.assertEqual(reset["pending_bytes_before"], 9936)
        self.assertTrue(reset["unread_bytes_discarded_not_raw_preserved"])
        self.assertEqual(port.resets, 1)

    def test_alignment_handles_split_newline(self):
        port = Port(b"old", b"tail-no-newline-yet\nKEPT\n", limit=3)
        summary, buffers, _ = warmup({"PICO": port})
        self.assertEqual(summary["unresolved_ports"], [])
        remaining = bytes(buffers["PICO"]) + bytes(port.data)
        self.assertEqual(remaining, b"KEPT\n")
        self.assertEqual(port.resets, 1)

    def test_alignment_no_newline_times_out_without_trial(self):
        port = Port(b"old\n", b"incomplete")
        summary, _, records = warmup({"ESP": port})
        self.assertEqual(summary["unresolved_ports"], ["ESP"])
        self.assertFalse(summary["formal_trial_started"])
        self.assertEqual(records[-1]["phase"], "alignment_failed")
        self.assertLess(summary["elapsed_seconds"], .12)

    def test_alignment_byte_budget_is_bounded(self):
        port = Port(b"old", b"a" * 10000)
        summary, _, _ = warmup({"ESP": port}, align_max_bytes=32)
        self.assertEqual(summary["alignment_bytes"], 32)
        self.assertEqual(summary["unresolved_ports"], ["ESP"])
        self.assertEqual(port.resets, 1)

    def test_every_port_must_align(self):
        a = Port(b"old-a", b"tail\nA\n"); b = Port(b"old-b", b"no-newline")
        summary, _, _ = warmup({"PICO": a, "ESP": b})
        self.assertEqual(summary["unresolved_ports"], ["ESP"])
        self.assertFalse(summary["formal_trial_started"])
        self.assertEqual((a.resets, b.resets), (1, 1))

    def test_mid_trial_errors_and_duplicates_preserved(self):
        buffer = bytearray()
        rows, dropped = monitor.consume_lines(buffer, b"STAT duplicate\nSTAT duplicate\n@badCRC\npartial-fragment\n")
        self.assertEqual(rows, [b"STAT duplicate", b"STAT duplicate", b"@badCRC", b"partial-fragment"])
        self.assertEqual(dropped, 0)

    def test_existing_oversize_counting_remains_bounded(self):
        buffer = bytearray()
        rows, dropped = monitor.consume_lines(buffer, b"x" * 2049 + b"\nvalid\n")
        self.assertEqual(rows, [b"valid"])
        self.assertEqual(dropped, 1)
        rows, dropped = monitor.consume_lines(buffer, b"x" * 8193)
        self.assertEqual((rows, dropped, buffer), ([], 1, bytearray()))


if __name__ == "__main__": unittest.main()
