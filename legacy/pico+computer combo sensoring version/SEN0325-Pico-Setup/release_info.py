"""Identity of the local desktop release (independent of the DSP checkpoint)."""
from pathlib import Path
import hashlib

RELEASE = "Gap 18-22 kHz + UART bridge | 2026-11-05"
DEFAULT_PROFILE = "coded-gap"
SOURCE_FILES = (
    "sen0325_launcher.py", "sen0325_simple_view.py", "app_controls.py",
    "beacon_dsp.py", "beacon_importer.py", "highband_dsp.py", "arrival_dsp.py", "joint_delay_dsp.py",
    "direction_diagnostics.py", "radar_canvas.py", "signal_scope.py",
    "app_instance.py", "release_info.py", "esp32_bridge.py",
)

def source_fingerprint(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in SOURCE_FILES:
        digest.update(name.encode("utf-8") + b"\0")
        digest.update((root / name).read_bytes())
    return digest.hexdigest()
