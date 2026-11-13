"""Host-only check: execute the actual PIO text against an independent I2S source.

Checks constant clock periods, falling-edge WS changes, the one-bit I2S delay,
four-lane packing, channel order, and signed 24-to-16-bit conversion. It does
not replace testing the real sensor, its power rail, or wires.
"""
import json
import random
import re
from pathlib import Path

rng = random.Random(325)
source = [[rng.randrange(-(1 << 23), 1 << 23) for _ in range(8)] for _ in range(48)]
for frame in source:
    frame[6] = 0  # Central microphone is on D3 right; D3 left is unused.
source[0] = [-8388608, 8388607, -256, 256, 0, -1, 0, 0x123456]

instructions = []
labels = {}
wrap_start = wrap_end = None
for raw in Path(__file__).with_name("sen0325_i2s.pio").read_text().splitlines():
    line = raw.split(";", 1)[0].strip()
    if not line:
        continue
    if line == ".wrap_target":
        wrap_start = len(instructions)
    elif line == ".wrap":
        wrap_end = len(instructions) - 1
    elif line.startswith("."):
        continue
    elif line.endswith(":"):
        labels[line[:-1]] = len(instructions)
    else:
        op, side = line.rsplit("side", 1)
        instructions.append((op.strip(), int(side.strip(), 0)))

pc = x = cycle = previous_clock = previous_ws = 0
slot = bit = frame_index = 0
pending_slot = None
isr = count = 0
words, rising, ws_edges = [], [], []
while len(words) < 32 * 8:
    op, side = instructions[pc]
    clock, ws = side & 1, (side >> 1) & 1
    falling = previous_clock == 1 and clock == 0
    changed_ws = ws != previous_ws
    if changed_ws:
        assert falling, "WS must change on a falling BCLK edge"
        ws_edges.append(cycle)
    if falling:
        if pending_slot is not None:
            slot, bit = pending_slot, 0
            if slot == 0:
                frame_index += 1
            pending_slot = None
        else:
            bit += 1
        if changed_ws:
            assert bit == 31, "WS must change during the preceding slot's last bit"
            pending_slot = ws
    if previous_clock == 0 and clock == 1:
        rising.append(cycle)
    next_pc = pc + 1
    if op.startswith("set x,"):
        x = int(op.split(",")[1])
    elif op.startswith("jmp x--"):
        old_x = x
        x = (x - 1) & 0xffffffff
        if old_x:
            next_pc = labels[op.split()[-1]]
    elif op == "in pins, 4":
        assert clock == 1, "Samples must be taken on the BCLK high phase"
        assert 0 <= bit < 32
        nibble = 0
        if bit < 24:
            for lane in range(4):
                raw24 = source[frame_index][lane * 2 + slot] & 0xffffff
                nibble |= ((raw24 >> (23 - bit)) & 1) << lane
        isr = ((isr << 4) | nibble) & 0xffffffff
        count += 4
        if count == 32:
            words.append(isr)
            isr = count = 0
    elif op != "nop":
        raise AssertionError(f"Unhandled PIO instruction: {op}")
    if pc == wrap_end and next_pc == pc + 1:
        next_pc = wrap_start
    pc = next_pc
    previous_clock, previous_ws = clock, ws
    cycle += 1

assert all(b - a == 2 for a, b in zip(rising, rising[1:])), "Non-uniform BCLK"
assert all(b - a == 64 for a, b in zip(ws_edges, ws_edges[1:])), "Wrong WS half-period"

def gather(word, lane):
    value = (word >> lane) & 0x11111111
    value = (value | (value >> 3)) & 0x03030303
    value = (value | (value >> 6)) & 0x000f000f
    return (value | (value >> 12)) & 0xff

for frame in range(32):
    for lane in range(4):
        for lr in range(2):
            offset = frame * 8 + lr * 4
            raw24 = (gather(words[offset], lane) << 16) | (gather(words[offset + 1], lane) << 8) | gather(words[offset + 2], lane)
            signed24 = raw24 - (1 << 24) if raw24 & (1 << 23) else raw24
            assert signed24 >> 8 == source[frame][lane * 2 + lr] >> 8

print(json.dumps({"passed": True, "frames": 32, "decoded_channel_samples": 256,
                  "pio_cycles_per_frame": 128, "sample_rate_hz": 48000,
                  "bclk_hz": 3072000, "ws_changes_on_falling_edge": True,
                  "i2s_one_bit_delay": True, "hardware_sensor_test": "not performed"}, indent=2))
