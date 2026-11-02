"""Receiver-only controls, plus rejection of a burst arriving after stop."""
import io
import argparse
import json
from pathlib import Path
import sys
import zlib
root=Path(__file__).resolve().parents[1]/'SEN0325-Pico-Setup'
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=root.parent/'stages/06-joint-delay/controls-validation.json')
args=parser.parse_args()
sys.path.insert(0,str(root))
from sen0325_launcher import Session
from app_controls import ScanControls

session=Session();controls=ScanControls(session)
assert not controls.running
assert not hasattr(controls,'player') and not hasattr(controls,'toggle_playback')
controls.toggle_scan()
assert controls.running
controls.select_profile('coded-16-18')
assert controls.running and session.frequency==17000
controls.toggle_scan()
controls.select_profile('coded-audible')
assert not controls.running and session.frequency==2400
try:controls.select_profile('invalid')
except ValueError:pass
else:raise AssertionError('Unknown receiver was accepted')
controls.close()
assert not controls.running and session.stop.is_set()

session=Session();session.set_mode('coded-audible');session.set_running(True)
payload=bytes(4096*7*2)
header=f'AUDIO frames=4096 fs=48000 channels=7 bytes={len(payload)} seq=1 dropped=0 rx_stall=0 process_us=3800 crc32={zlib.crc32(payload):08x}\n'
class StopDuringRead:
    def __init__(self):self.lines=iter([header.encode(),b'\n',b'AUDIO_END seq=1\n'])
    def write(self,command):pass
    def readline(self):return next(self.lines)
    def read(self,count):
        session.set_running(False)
        return payload
from raw_packet import PacketError
try:session.record_beacon(StopDuringRead(),io.StringIO(),'coded-audible')
except PacketError as error:assert error.category=='capture_cancelled'
else:raise AssertionError('Stopped burst was not cancelled')
assert session.frames==0 and not session.last_direction['valid']
assert not any(kind=='frame' for kind,value in list(session.events.queue))
report={'passed':True,'scan_only_controls':True,'no_playback_implementation':True,
    'receiver_selection_keeps_scan_state':True,'unknown_profile_rejected':True,
    'late_burst_after_stop_is_discarded':True,'test_audio_emitted':False}
args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))

