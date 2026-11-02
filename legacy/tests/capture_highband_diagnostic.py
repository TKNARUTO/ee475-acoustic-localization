"""Short, local raw snapshot for HF1 debugging. No sound output."""
from pathlib import Path
import json
import queue
import sys
import time
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'SEN0325-Pico-Setup'))
from sen0325_launcher import Session

destination=PROJECT/'stages/01-16-18kHz/phone-debug'
destination.mkdir(exist_ok=True)
session=Session();session.set_mode('coded-16-18');session.set_running(True);session.start()
audio=[];metrics=[];last_sequence=None
deadline=time.monotonic()+18
try:
    while time.monotonic()<deadline:
        try:kind,value=session.events.get(timeout=.5)
        except queue.Empty:continue
        if kind=='status':print(value,flush=True)
        if kind=='direction' and session.last_raw_audio is not None:
            sequence=session.last_frame.get('seq')
            if sequence!=last_sequence:
                audio.append(session.last_raw_audio.copy());metrics.append(dict(value,sequence=sequence))
                last_sequence=sequence
                print(json.dumps({k:value.get(k) for k in ['valid','reason','code_channels','band_level_dbfs','candidate_angle_deg','all_pair_rms_samples']}),flush=True)
            if len(audio)>=48:break
finally:
    session.set_running(False);session.stop.set();session.thread.join(6)
if not audio:raise RuntimeError('No capture available')
np.savez_compressed(destination/'phone-capture.npz',audio=np.array(audio))
(destination/'phone-capture-metrics.json').write_text(json.dumps({'log':str(session.log_path),'frames':metrics},indent=2),encoding='utf-8')
print('Saved',len(audio),'raw blocks to',destination,flush=True)
