"""Optional USB -> Pico -> UART bearing link. No motor commands or serial owner."""
from collections import OrderedDict
import json
import math
from pathlib import Path
import re
import secrets
import time

MAX_LINE = 128
MAX_AGE_MS = 500

def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

def frame(*fields):
    payload = ",".join(str(x) for x in fields)
    raw = payload.encode("ascii")
    if any(c in payload for c in "@*\r\n") or not all(32 <= b < 127 for b in raw):
        raise ValueError("Invalid bridge payload")
    result = f"@{payload}*{crc16(raw):04X}\n"
    if len(result) > MAX_LINE:
        raise ValueError("Bridge frame too long")
    return result

def decode(line):
    if not isinstance(line, str) or len(line) > MAX_LINE:
        raise ValueError("Invalid bridge length")
    match = re.fullmatch(r"@([^@*\r\n]+)\*([0-9A-Fa-f]{4})\n?", line)
    if not match:
        raise ValueError("Malformed bridge frame")
    payload, check = match.groups()
    if crc16(payload.encode("ascii")) != int(check, 16):
        raise ValueError("Bridge CRC mismatch")
    return payload.split(",")

def ack(line):
    fields = decode(line)
    if len(fields) != 7 or fields[:2] != ["A", "1"] or not re.fullmatch(r"[0-9A-Fa-f]{8}", fields[2]):
        raise ValueError("Invalid ACK fields")
    if not all(re.fullmatch(r"[0-9]+", f) for f in fields[3:]):
        raise ValueError("Invalid ACK integer")
    seq, kind, status, count = map(int, fields[3:])
    if seq > 0xFFFFFFFF or count > 0xFFFFFFFF or kind not in (0,1,2) or status not in range(5):
        raise ValueError("ACK out of range")
    return {"session":fields[2].upper(),"seq":seq,"type":kind,"status":status,"count":count}

class BridgeClient:
    """Called only by the existing Session serial worker, between raw packets."""
    def __init__(self, root, event=None, status=None):
        self.root = Path(root)
        self.event = event or (lambda *args, **kwargs: None)
        self.status = status or (lambda value: None)
        try:
            self.enabled = json.loads((self.root/"bridge_config.json").read_text(encoding="utf-8")).get("enabled") is True
        except (OSError, ValueError, AttributeError):
            self.enabled = False
        self.reset(False)

    def reset(self, capable):
        self.capable = capable
        self.session = secrets.token_hex(4).upper()
        self.ready = False
        self.seq = 0
        self.last_hello = float("-inf")
        self.last_ack = None
        self.pending = OrderedDict()
        self.last_capture = None
        self.sent = self.acked = 0

    def _send(self, send, text, seq=None):
        send("LINK " + text.rstrip("\n"))
        if seq is not None:
            self.pending[seq] = time.perf_counter()
            while len(self.pending) > 32:
                self.pending.popitem(last=False)

    def ensure_ready(self, send):
        if not self.enabled or not self.capable:
            return False
        now = time.perf_counter()
        if self.ready and (self.last_ack is None or now-self.last_ack > 1.5):
            self.ready = False
            self.status("ESP32: ACK timeout; checking UART connection")
        if not self.ready and now-self.last_hello >= 1:
            self._send(send, frame("H",1,self.session))
            self.last_hello = now
            self.status("ESP32: waiting for UART handshake")
        return self.ready

    def on_line(self, line):
        if not line.startswith("LINKRX "):
            return
        try:
            response = ack(line[7:].strip())
        except (ValueError, UnicodeError):
            self.event("esp32_bad_ack")
            return
        if response["session"] != self.session:
            return
        if response["type"] == 0 and response["status"] == 0:
            self.ready = True
            self.last_ack = time.perf_counter()
            self.event("esp32_handshake", **response)
            self.status("ESP32: UART connected; receive-only bench firmware")
        elif response["type"] == 2 and response["seq"] in self.pending:
            started = self.pending.pop(response["seq"])
            self.last_ack = time.perf_counter()
            self.acked += 1
            if response["status"] == 4:
                self.ready = False
            self.event("esp32_ack", **response, host_observed_ack_ms=round((self.last_ack-started)*1000,3))
            self.status(f"ESP32: ACK {self.acked}/{self.sent} | status {response['status']} | no motor output")

    def observation(self, send, estimate, generation=0):
        if not self.ensure_ready(send):
            return
        timing = estimate.get("pipeline_timing", {})
        identity = (generation, timing.get("seq"))
        if timing.get("seq") is None or identity == self.last_capture:
            return
        self.last_capture = identity
        age = round(max(0, (time.perf_counter()-timing["request_perf_counter"])*1000))
        angle = estimate.get("raw_angle_deg")
        quality = estimate.get("confidence", 0)
        valid = bool(estimate.get("valid") and angle is not None and
                     math.isfinite(angle) and math.isfinite(quality) and age+20 <= MAX_AGE_MS)
        angle_cdeg = round((angle % 360)*100) % 36000 if valid else 0
        quality_int = round(min(1,max(0,quality))*1000) if valid else 0
        self.seq = (self.seq+1) & 0xFFFFFFFF
        self._send(send, frame("B",1,self.session,self.seq,min(age,60000),int(valid),angle_cdeg,quality_int),self.seq)
        self.sent += 1
        self.event("esp32_tx",session=self.session,seq=self.seq,capture_seq=timing["seq"],valid=valid,
                   angle_cdeg=angle_cdeg,quality=quality_int,age_ms=age,coordinate_frame="array_raw")
        if self.last_ack is None or time.perf_counter()-self.last_ack > 1:
            self.status("ESP32: no recent ACK; acoustic scan continues")

    def invalidate(self, send):
        if self.enabled and self.capable and self.ready:
            self.seq = (self.seq+1) & 0xFFFFFFFF
            self._send(send,frame("B",1,self.session,self.seq,0,0,0,0),self.seq)
            self.sent += 1
