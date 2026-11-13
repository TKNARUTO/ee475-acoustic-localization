"""EE475 experimental phase-based sound localization and selected-tone view."""
from collections import deque
from datetime import datetime
import ctypes
import json
import math
import os
import queue
from statistics import median
import time

COLORS = ("#6ab7ff", "#ff9a83", "#67d59b", "#d4a1ff", "#f2d46f", "#5ed9df", "#ff8db4")


def db(power):
    return max(-120.0, 10 * math.log10(max(power, 1e-12) / (32768 ** 2)))


class Levels:
    def __init__(self, channels):
        self.channels = channels
        self.power = {}
        self.last = {}
        self.baseline = {}
        self.history = deque(maxlen=100)

    def update(self, name, rms, now):
        power = rms * rms
        alpha = 1 - math.exp(-max(0, now - self.last.get(name, now - 1)) / 0.6)
        self.power[name] = self.power.get(name, power) * (1 - alpha) + power * alpha
        self.last[name] = now
        if name == self.channels[-1]:
            self.history.append((now, {key: db(value) for key, value in self.power.items()}))

    def delta(self, name):
        return db(self.power[name]) - db(self.baseline[name]) if name in self.baseline else None


class Pattern:
    """Three seconds quiet, then four repetitions of 3 s tone / 3 s quiet."""
    def __init__(self, channels, start, guided=True, frequency=1000):
        self.start = start
        self.guided = guided
        self.channels = channels
        self.samples = {kind: {ch: [] for ch in channels} for kind in ("baseline", "on", "off")}
        self.bad_capture = False
        self.frequency = frequency
        self.tone_samples = {kind: {ch: [] for ch in channels} for kind in ("baseline", "on", "off")}
        self.tone_hits = {kind: {ch: [] for ch in channels} for kind in ("baseline", "on", "off")}
        self.cycles = {ch: [[] for _ in range(8)] for ch in channels}
        self.issues = []
        self.previous_dropped = None
        self.playback_events = []

    def phase(self, now):
        elapsed = now - self.start
        if elapsed < 3:
            return -1
        return int((elapsed - 3) // 3) if self.guided and elapsed < 27 else 8

    def record(self, name, rms, now):
        elapsed = now - self.start
        phase = self.phase(now)
        if phase == -1:
            kind = "baseline"
        elif phase < 8:
            # Discard transitions: each firmware report integrates ~250 ms.
            within = (elapsed - 3) % 3
            if within < 0.6 or within > 2.7:
                return
            kind = "on" if phase % 2 == 0 else "off"
        else:
            return
        self.samples[kind][name].append(rms * rms)

    def baseline(self):
        return {ch: median(values) for ch, values in self.samples["baseline"].items() if len(values) >= 6}

    def record_tone(self, name, data, now):
        if data["frequency"] != self.frequency:
            return
        phase = self.phase(now)
        if phase == -1:
            kind = "baseline"
        elif phase < 8:
            within = (now - self.start - 3) % 3
            if within < 0.6 or within > 2.7:
                return
            kind = "on" if phase % 2 == 0 else "off"
            self.cycles[name][phase].append(data["present"])
        else:
            return
        self.tone_samples[kind][name].append(data["rms"] ** 2)
        self.tone_hits[kind][name].append(data["present"])

    def issue(self, kind, now, **details):
        self.bad_capture = True
        self.issues.append({"kind": kind, "elapsed": round(now-self.start,3), **details})

    def health(self, frame, now):
        if frame.get("frames",0)==0:
            self.issue("no_samples",now)
        dropped = frame.get("dropped",0)
        if self.previous_dropped is not None and dropped != self.previous_dropped:
            self.issue("dropped_or_capture_restart",now,previous=self.previous_dropped,current=dropped)
        self.previous_dropped = dropped
        if frame.get("rx_stall",0):
            self.issue("rx_stall",now)

    def report(self):
        channels = {}
        for ch in self.channels:
            on, off = self.samples["on"][ch], self.samples["off"][ch]
            channels[ch] = {"on_windows": len(on), "off_windows": len(off),
                            "on_minus_off_db": round(db(median(on)) - db(median(off)), 2) if on and off else None}
        valid = all(v["on_windows"] >= 12 and v["off_windows"] >= 12 for v in channels.values())
        matched = []
        for ch in self.channels:
            on,off = self.tone_samples["on"][ch],self.tone_samples["off"][ch]
            on_hits,off_hits = self.tone_hits["on"][ch],self.tone_hits["off"][ch]
            delta = db(median(on))-db(median(off)) if on and off else None
            on_rate = sum(on_hits)/len(on_hits) if on_hits else 0
            off_rate = sum(off_hits)/len(off_hits) if off_hits else 1
            good_cycles = sum(bool(self.cycles[ch][2*i]) and bool(self.cycles[ch][2*i+1])
                and sum(self.cycles[ch][2*i])/len(self.cycles[ch][2*i]) >= .6
                and sum(self.cycles[ch][2*i+1])/len(self.cycles[ch][2*i+1]) <= .25 for i in range(4))
            match = len(on)>=12 and len(off)>=12 and delta is not None and delta>=6 and on_rate>=.6 and off_rate<=.25 and good_cycles>=3
            channels[ch].update(target_on_windows=len(on),target_off_windows=len(off),
                target_on_minus_off_db=round(delta,2) if delta is not None else None,
                on_hit_rate=round(on_rate,3),off_hit_rate=round(off_rate,3),matched_cycles=good_cycles,preset_match=match)
            if match:
                matched.append(ch)
        return {"time": datetime.now().isoformat(), "stimulus": f"{self.frequency} Hz, 3 s on / 3 s off, 4 repetitions",
                "target_frequency_hz":self.frequency,"matched_channels":matched,
                "preset_recognized":len(matched)>=2 and valid and not self.bad_capture,
                "valid_capture": valid and not self.bad_capture, "capture_error": self.bad_capture,
                "issues":self.issues,"playback_events":self.playback_events,
                "channels": channels,
                "limitation": "Selected-frequency and known on/off cadence recognition only; this report does not validate bearing accuracy or a final beacon codec."}



def run(Session, root, channels, auto_close=None):
    from sen0325_simple_view import run as simple_run
    return simple_run(Session, root, channels, auto_close)
