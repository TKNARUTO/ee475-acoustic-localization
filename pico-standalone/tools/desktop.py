"""Display Pico-computed telemetry. No PC DSP, audio output or firmware loading."""
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import queue
import secrets
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import serial
from serial.tools import list_ports
from desktop_control import ROOT, LOGS, SCRIPT, RELEASE, fingerprint

BG, GRID, TEXT, GREEN, AMBER = "#071722", "#19434b", "#c7e0e7", "#42e3b3", "#ffbb61"


def checked_packet(kind, data):
    if not isinstance(data, dict): return False
    numeric = ("seq", "age_ms", "angle_deg", "quality", "code_channels", "valid", "fit_valid", "confirmed") if kind == "GAP" else ()
    for key in numeric:
        value = data.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value): return False
    for key, value in data.items():
        if key.endswith("_us") and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0): return False
    if kind == "GAP":
        if not (0 <= data["angle_deg"] < 360 and 0 <= data["age_ms"] and 0 <= data["quality"] <= 1 and 0 <= data["code_channels"] <= 7): return False
        if any(data[k] not in (0, 1) for k in ("valid", "fit_valid", "confirmed")): return False
    return True


class Receiver(threading.Thread):
    def __init__(self, events):
        super().__init__(daemon=True)
        self.events = events; self.stop = threading.Event(); self.commands = queue.Queue(maxsize=8)
    def emit(self, kind, value):
        try: self.events.put_nowait((kind, value))
        except queue.Full:
            try: self.events.get_nowait()
            except queue.Empty: pass
            self.events.put_nowait((kind, value))
    def run(self):
        path = LOGS / ("standalone-"+datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")+".jsonl")
        with path.open("x", encoding="utf-8") as log:
            self.emit("log", str(path))
            while not self.stop.is_set():
                ports = [p for p in list_ports.comports() if p.vid == 0x2E8A and p.pid == 0x000A]
                if len(ports) != 1:
                    self.emit("status", "Connect one Pico running standalone firmware; no firmware is loaded by this app")
                    self.stop.wait(1); continue
                try:
                    with serial.Serial(ports[0].device, 115200, timeout=.12, write_timeout=.3) as link:
                        self.emit("status", ports[0].device+" connected | Waiting for Pico telemetry")
                        buffer = bytearray(); last_rx = time.monotonic(); warned = False
                        while not self.stop.is_set():
                            while not self.commands.empty():
                                command = self.commands.get_nowait()
                                if command not in ("START", "STOP"): continue
                                link.write((command+"\n").encode("ascii"))
                                log.write(json.dumps({"command":command,"utc":datetime.now(timezone.utc).isoformat()})+"\n"); log.flush()
                            buffer.extend(link.read(max(1, min(link.in_waiting, 4096))))
                            while b"\n" in buffer:
                                raw, _, tail = buffer.partition(b"\n"); buffer[:] = tail
                                if len(raw)>4096: continue
                                line = raw.decode("utf-8", errors="replace").strip()
                                now = time.monotonic()
                                log.write(json.dumps({"utc":datetime.now(timezone.utc).isoformat(),"mono":now,"line":line})+"\n"); log.flush()
                                if line.startswith(("GAP ", "PROFILE ", "STATUS ")):
                                    kind, payload = line.split(" ", 1)
                                    try:
                                        data = json.loads(payload)
                                        if not checked_packet(kind, data): continue
                                    except (ValueError, TypeError): continue
                                    self.emit("device_state" if kind == "STATUS" else kind.lower(), (data, now)); last_rx = now; warned = False
                                    self.emit("status", ports[0].device+" | PICO COMPUTES | PC displays only")
                                elif line.startswith("PICO_GAP_STANDALONE"):
                                    self.emit("banner", line); last_rx = now
                                elif line.startswith("SEN0325_SETUP"):
                                    self.emit("status", "Combo capture firmware detected. Standalone firmware must be installed separately.")
                            if len(buffer)>16384: buffer.clear()
                            if time.monotonic()-last_rx>8 and not warned:
                                self.emit("status", "No recent Pico telemetry; check firmware and connection")
                                warned = True
                except (serial.SerialException, OSError) as error:
                    self.emit("status", "Pico unavailable: "+str(error))
                    self.stop.wait(1)


class View(tk.Tk):
    def __init__(self, test=False):
        super().__init__(); self.test = test; self.title(RELEASE)
        self.geometry("1120x820"); self.minsize(1000, 780); self.configure(bg=BG)
        self.events = queue.Queue(maxsize=160); self.receiver = Receiver(self.events)
        self.last = None; self.received = 0; self.profile = {}; self.heading = 0.; self.paused = False
        self.token = secrets.token_hex(16); self.closing = False
        style = ttk.Style(self); style.theme_use("clam")
        style.configure("TFrame", background=BG); style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        outer = ttk.Frame(self, padding=16); outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="PICO STANDALONE · ACOUSTIC BEARING", font=("Segoe UI", 18, "bold"), foreground=GREEN).pack(anchor="w")
        ttk.Label(outer, text="HF2 Gap 18–22 kHz | Pico computes direction; this computer only displays telemetry").pack(anchor="w", pady=(4,10))
        self.connection = tk.StringVar(value="Connecting…")
        ttk.Label(outer, textvariable=self.connection, wraplength=1060).pack(anchor="w")
        controls = ttk.Frame(outer); controls.pack(fill="x", pady=10)
        self.pause_button = ttk.Button(controls, text="Pause Pico", command=self.pause); self.pause_button.pack(side="left")
        ttk.Button(controls, text="Set Display Front", command=self.set_front).pack(side="left", padx=8)
        ttk.Button(controls, text="Open Beacon Folder", command=self.open_audio).pack(side="left")
        body = ttk.Frame(outer); body.pack(fill="both", expand=True)
        self.radar = tk.Canvas(body, bg=BG, highlightthickness=0); self.radar.pack(side="left", fill="both", expand=True)
        side = ttk.Frame(body, width=370); side.pack(side="right", fill="y", padx=(12,0)); side.pack_propagate(False)
        self.metrics = tk.StringVar(value="Waiting for Pico measurements")
        ttk.Label(side, textvariable=self.metrics, justify="left", wraplength=360).pack(anchor="w", pady=8)
        self.chart = tk.Canvas(side, width=355, height=200, bg=BG, highlightthickness=0); self.chart.pack(fill="x", pady=10)
        ttk.Label(side, text="Green: fresh confirmed Pico measurement\nAmber: diagnostic fit; not valid for control\nUART reception is reported separately.\nNo angle jump restriction is applied here.\n\nRings show bearing only, not distance.\nClosing this window leaves Pico running.", foreground="#89aebb", wraplength=350).pack(anchor="w")
        self.log_label = tk.StringVar(value="Local telemetry log: preparing")
        ttk.Label(outer, textvariable=self.log_label, font=("Segoe UI", 8), wraplength=1060).pack(anchor="w", pady=(8,0))
        if not test:
            LOGS.mkdir(exist_ok=True); self.write_info("running"); self.receiver.start()
        self.protocol("WM_DELETE_WINDOW", self.close); self.after(80, self.refresh)

    def write_info(self, state):
        data = {"pid":os.getpid(),"token":self.token,"state":state,"script":str(SCRIPT),
                "release":RELEASE,"source_sha256":fingerprint(),"updated_utc":datetime.now(timezone.utc).isoformat()}
        target = LOGS/"desktop-instance.json"; temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2), encoding="utf-8"); temp.replace(target)
    def pause(self):
        command = "START" if self.paused else "STOP"
        try: self.receiver.commands.put_nowait(command)
        except queue.Full: return
        self.paused = not self.paused
        self.pause_button.configure(text="Resume Pico" if self.paused else "Pause Pico")
    def set_front(self):
        if not self.last or not self.last.get("valid") or self.age()>480:
            messagebox.showinfo("Display calibration", "A fresh confirmed Pico bearing is required."); return
        self.heading = float(self.last["angle_deg"])
    def open_audio(self):
        os.startfile(str(ROOT.parent/"audio/phone/HF2-gap-test"))
    def age(self):
        return float(self.last.get("age_ms",0))+(time.monotonic()-self.received)*1000 if self.last else float("inf")
    def draw(self):
        c = self.radar; c.delete("all"); w,h = max(400,c.winfo_width()), max(400,c.winfo_height()); cx,cy=w/2,h/2
        radius = min(w,h)/2-48
        for fraction in (.25,.5,.75,1):
            r=radius*fraction; c.create_oval(cx-r,cy-r,cx+r,cy+r,outline=GRID)
        for angle in range(0,360,30):
            r=math.radians(angle); x,y=cx+radius*math.sin(r),cy-radius*math.cos(r)
            c.create_line(cx,cy,x,y,fill=GRID)
            c.create_text(cx+(radius+20)*math.sin(r),cy-(radius+20)*math.cos(r),text=f"{angle}°",fill=TEXT)
        c.create_oval(cx-5,cy-5,cx+5,cy+5,fill=GREEN,outline="")
        packet=self.last; age=self.age(); angle=packet.get("angle_deg") if packet else None
        if packet and packet.get("fit_valid") and isinstance(angle,(int,float)) and math.isfinite(angle) and time.monotonic()-self.received<8:
            fresh=bool(packet.get("valid") and age<=480); color=GREEN if fresh else AMBER
            shown=(angle-self.heading)%360; r=math.radians(shown)
            c.create_line(cx,cy,cx+radius*.8*math.sin(r),cy-radius*.8*math.cos(r),fill=color,width=3,arrow=tk.LAST,arrowshape=(14,18,7))
            c.create_text(cx,18,text=f"{shown:.1f}°  ·  "+("Fresh target" if fresh else "Diagnostic fit — not a fresh target"),fill=color,font=("Segoe UI",12,"bold"))
        else:
            c.create_text(cx,cy+32,text="No current fitted bearing",fill=TEXT,font=("Segoe UI",13))
        c.create_text(cx,h-12,text="Array reference" if self.heading==0 else "Display front calibrated; UART stays in array coordinates",fill="#89aebb")
        if packet:
            self.metrics.set(f"Pico result #{packet.get('seq','—')}\nReason: {packet.get('reason','—')}\nCode channels: {packet.get('code_channels',0)} / 7\nFit / confirmed / valid: {packet.get('fit_valid',0)} / {packet.get('confirmed',0)} / {packet.get('valid',0)}\nMeasurement age now: {age:.0f} ms\nDSP: {packet.get('dsp_us',0)/1000:.1f} ms\nCycle: {packet.get('cycle_us',packet.get('dsp_us',0)+packet.get('capture_us',0))/1000:.1f} ms\nUnpack: {packet.get('unpack_total_us',0)/1000:.1f} ms\nUART ready: {packet.get('uart_ready',0)} · ACK {packet.get('ack_status','—')}\nDMA drops: {packet.get('dma_drop',0)} · USB log drops: {packet.get('usb_drop',0)}")
        self.chart.delete("all"); self.chart.create_text(0,10,anchor="w",text="PICO DSP PHASE WALL TIME",fill=TEXT,font=("Segoe UI",10,"bold"))
        fields=(("Forward FFT","forward_fft_us"),("Whitening","whitening_us"),("Inverse FFT","inverse_fft_us"),("Envelope","envelope_peaks_us"),("Geometry","arrival_fit_us"))
        peak=max(1,*[self.profile.get(k,0) for _,k in fields])
        for i,(label,key) in enumerate(fields):
            y=38+i*29; value=self.profile.get(key,0)
            self.chart.create_text(0,y,anchor="w",text=label,fill=TEXT)
            self.chart.create_rectangle(95,y-6,95+155*value/peak,y+6,fill=GREEN,outline="")
            self.chart.create_text(260,y,anchor="w",text=f"{value/1000:.1f} ms",fill=TEXT)
    def refresh(self):
        if self.closing: return
        for _ in range(200):
            try: kind,value=self.events.get_nowait()
            except queue.Empty: break
            if kind=="status": self.connection.set(value)
            elif kind=="banner": self.connection.set(value)
            elif kind=="log": self.log_label.set("Local telemetry: "+value)
            elif kind=="gap": self.last,self.received=value
            elif kind=="profile": self.profile=value[0]
            elif kind=="device_state":
                self.paused=not bool(value[0].get("running",1))
                self.pause_button.configure(text="Resume Pico" if self.paused else "Pause Pico")
        if not self.test:
            request=LOGS/"desktop-request.json"
            try: action=json.loads(request.read_text(encoding="utf-8"))
            except (OSError,ValueError): action={}
            if action.get("token")==self.token:
                if action.get("action")=="close": self.close(); return
                if action.get("action")=="focus":
                    request.unlink(missing_ok=True); self.deiconify(); self.lift(); self.focus_force()
        self.draw(); self.after(80,self.refresh)
    def close(self):
        if self.closing: return
        self.closing=True
        if not self.test:
            self.write_info("closing"); self.receiver.stop.set(); self.receiver.join(timeout=2)
            self.write_info("closed")
        self.destroy()


if __name__ == "__main__":
    View().mainloop()
