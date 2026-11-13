"""Start/focus/update only the passive standalone monitor; never flash a board."""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
SCRIPT = ROOT / "tools/desktop.py"
RELEASE = "Pico Standalone Monitor | 2026-11-12"


def fingerprint():
    digest = hashlib.sha256()
    for name in ("tools/desktop.py", "tools/desktop_control.py"):
        data = (ROOT/name).read_bytes()
        compile(data, str(ROOT/name), "exec")
        digest.update(name.encode()+b"\0"+data)
    return digest.hexdigest()


def running(pid):
    if not isinstance(pid, int) or pid <= 0: return False
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.argtypes = (ctypes.c_uint, ctypes.c_bool, ctypes.c_uint)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_uint)
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    handle = kernel.OpenProcess(0x100000, False, pid)
    if not handle: return False
    try: return kernel.WaitForSingleObject(handle, 0) == 258
    finally: kernel.CloseHandle(handle)


def info():
    try: return json.loads((LOGS/"desktop-instance.json").read_text(encoding="utf-8"))
    except (OSError, ValueError): return {}


def main(check_only=False, start_only=False):
    source = fingerprint()
    if check_only: return {"passed": True, "release": RELEASE, "source_sha256": source, "firmware_write": False}
    LOGS.mkdir(exist_ok=True)
    old = info()
    if old.get("state") in ("running", "closing") and running(old.get("pid")):
        if Path(old.get("script", "")).resolve() != SCRIPT.resolve(): raise RuntimeError("Unexpected monitor instance path")
        focus = start_only and old.get("source_sha256") == source and old.get("state") == "running"
        (LOGS/"desktop-request.json").write_text(json.dumps({"token": old["token"], "action": "focus" if focus else "close"}), encoding="utf-8")
        if focus: return {"passed": True, "action": "focused", "pid": old["pid"], "release": RELEASE}
        deadline = time.monotonic()+10
        while running(old["pid"]) and time.monotonic()<deadline: time.sleep(.1)
        if running(old["pid"]): raise RuntimeError("Monitor is still closing; no process was forcibly stopped")
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    subprocess.Popen([str(pythonw if pythonw.exists() else Path(sys.executable)), str(SCRIPT)], cwd=ROOT,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    deadline = time.monotonic()+12
    while time.monotonic()<deadline:
        current = info()
        if current.get("token") != old.get("token") and current.get("state") == "running" and running(current.get("pid")):
            if current.get("source_sha256") != source: raise RuntimeError("Monitor source identity mismatch")
            result = {"passed": True, "action": "started", "pid": current["pid"], "release": RELEASE,
                      "source_sha256": source, "firmware_write": False, "completed_utc": datetime.now(timezone.utc).isoformat()}
            (LOGS/"update-status.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            return result
        time.sleep(.1)
    raise RuntimeError("Monitor did not confirm startup; see logs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--start-only", action="store_true")
    args = parser.parse_args()
    try: print(json.dumps(main(args.check_only, args.start_only), indent=2))
    except Exception as error:
        LOGS.mkdir(exist_ok=True)
        (LOGS/"update-error.txt").write_text(str(error), encoding="utf-8")
        if sys.executable.lower().endswith("pythonw.exe"):
            ctypes.windll.user32.MessageBoxW(None, str(error), "Pico standalone monitor", 0)
        raise
