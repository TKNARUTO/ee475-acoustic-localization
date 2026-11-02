"""Bounded RX4 raw capture for two phone loops and a deliberate quiet gap."""
from pathlib import Path
import argparse
from datetime import datetime
import hashlib
import json
import math
import queue
import sys
import threading
import time

import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
APP=PROJECT/'SEN0325-Pico-Setup'
sys.path.insert(0,str(APP))
from sen0325_launcher import Session,DESKTOP_CHECKPOINT

class GuiTrialRecorder:
    def __init__(self,seconds):
        self.seconds=seconds;self.start=None;self.done=False;self.finish_at=None
        self.audio=[];self.events=[];self.lock=threading.Lock();self.session=None
        self.destination=PROJECT/'stages/06-joint-delay/trials'/datetime.now().strftime('phone-trial-%Y%m%d-%H%M%S')
        self.destination.mkdir(parents=True,exist_ok=False)
        print('RX4_TRIAL_FOLDER '+str(self.destination),flush=True)

    def observe(self,session,estimate):
        if self.done or estimate.get('profile')!='coded-20' or 'pipeline_timing' not in estimate:return
        sequence=estimate['pipeline_timing']['seq']
        with self.lock:
            if self.done:return
            assert session.last_frame['seq']==sequence
            if self.start is None:
                self.start=time.monotonic()
                print('RX4_TRIAL_READY '+str(self.destination),flush=True)
            if len(self.audio)>=math.ceil(self.seconds*12):return
            self.audio.append(session.last_raw_audio.copy())
            self.events.append({'sequence':sequence,'health':dict(session.last_frame),
                'received_at':estimate['received_at'],'wall_time':datetime.now().astimezone().isoformat(),
                'estimate':dict(estimate)})

    def monitor(self):
        while not self.done:
            time.sleep(.25)
            if self.start is None:continue
            if self.finish_at is None and (self.destination/'finish.request').exists():self.finish_at=time.monotonic()+5
            if time.monotonic()-self.start>=self.seconds or (self.finish_at and time.monotonic()>=self.finish_at):
                self.finish('complete')

    def finish(self,completion):
        with self.lock:
            if self.done:return
            self.done=True;audio=self.audio;events=self.events;self.audio=[];self.events=[]
        raw=self.destination/'raw-seven-channel.npz'
        if audio:np.savez(raw,audio=np.stack(audio),sequence=np.array([e['sequence'] for e in events]),
            received_at=np.array([e['received_at'] for e in events]))
        report={'checkpoint':DESKTOP_CHECKPOINT,'profile':'coded-20','requested_seconds':self.seconds,
            'completion':completion,'windows':len(events),'events':events,
            'start_wall_time':events[0]['wall_time'] if events else None,
            'end_wall_time':events[-1]['wall_time'] if events else None,
            'duration_s':round(events[-1]['received_at']-events[0]['received_at'],3) if events else 0,
            'raw_file':raw.name if audio else None,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest() if audio else None,
            'launcher_log':str(self.session.log_path),'geometry':json.loads((APP/'array_geometry.json').read_text(encoding='utf-8-sig')),
            'protocol':'User plans two loops of the same LOCATE file with a phone pause of a few seconds. Exact playback transitions and true bearing are not synchronized.',
            'audio_output':'receive-only; no computer playback'}
        (self.destination/'trial.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('RX4_TRIAL_SAVED '+str(self.destination/'trial.json'),flush=True)

def capture_gui(seconds):
    if not 20<=seconds<=120:raise ValueError('Trial duration must be 20–120 seconds')
    recorder=GuiTrialRecorder(seconds)
    class TrialSession(Session):
        def __init__(self):
            super().__init__();recorder.session=self
        def emit(self,kind,value):
            super().emit(kind,value)
            if kind=='direction':recorder.observe(self,value)
        def run(self):
            try:super().run()
            finally:recorder.finish('session_closed')
    from sen0325_simple_view import run
    threading.Thread(target=recorder.monitor,daemon=True).start()
    run(TrialSession,APP,('D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER'),initial_profile='coded-20')

def capture(seconds):
    if not 20<=seconds<=120:raise ValueError('Trial duration must be 20–120 seconds')
    assert DESKTOP_CHECKPOINT=='RX4'
    destination=PROJECT/'stages/06-joint-delay/trials'/datetime.now().strftime('phone-trial-%Y%m%d-%H%M%S')
    destination.mkdir(parents=True,exist_ok=False)
    session=Session();session.set_mode('coded-20');session.set_running(True);session.start()
    audio=[];events=[];health={};start=None;deadline=time.monotonic()+35
    next_progress=None;finish_requested=False;failure=None
    print('RX4_TRIAL_FOLDER '+str(destination),flush=True)
    try:
        while time.monotonic()<deadline:
            if (destination/'finish.request').exists() and not finish_requested and start is not None:
                deadline=min(deadline,time.monotonic()+5);finish_requested=True
            try:kind,value=session.events.get(timeout=.3)
            except queue.Empty:continue
            if kind=='status':print('STATUS '+str(value),flush=True)
            if kind=='frame':health[value['seq']]=dict(value)
            if kind!='direction' or value.get('profile')!='coded-20' or 'pipeline_timing' not in value:continue
            sequence=value['pipeline_timing']['seq']
            with session.recent_audio_lock:
                block=next((r for r in reversed(session.recent_audio) if r['seq']==sequence and r['profile']=='coded-20'),None)
                sample=None if block is None else block['audio'].copy()
            if sample is None:raise RuntimeError('Raw block missing; do not pair an estimate with another sequence')
            if start is None:
                start=time.monotonic();deadline=start+seconds;next_progress=start+10
                print('RX4_TRIAL_READY '+str(destination),flush=True)
            audio.append(sample)
            events.append({'sequence':sequence,'health':health.pop(sequence),
                'received_at':value['received_at'],'wall_time':datetime.now().astimezone().isoformat(),'estimate':dict(value)})
            if time.monotonic()>=next_progress:
                print(json.dumps({'elapsed_s':round(time.monotonic()-start,1),'windows':len(events),
                    'code_hits':sum(e['estimate'].get('code_channels',0)>=4 for e in events),
                    'valid':sum(e['estimate'].get('valid',False) for e in events),'last_reason':value['reason']}),flush=True)
                next_progress=time.monotonic()+10
            if len(audio)>math.ceil(seconds*12):raise RuntimeError('Raw trial memory bound exceeded')
    except Exception as error:
        failure=repr(error)
    finally:
        session.set_running(False);session.stop.set();session.thread.join(12)
    raw=destination/'raw-seven-channel.npz'
    if audio:
        np.savez(raw,audio=np.stack(audio),sequence=np.array([e['sequence'] for e in events]),
            received_at=np.array([e['received_at'] for e in events]))
    report={'checkpoint':DESKTOP_CHECKPOINT,'profile':'coded-20','requested_seconds':seconds,
        'start_wall_time':events[0]['wall_time'] if events else None,'end_wall_time':events[-1]['wall_time'] if events else None,
        'duration_s':round(events[-1]['received_at']-events[0]['received_at'],3) if events else 0,
        'windows':len(events),'events':events,'raw_file':raw.name if audio else None,
        'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest() if audio else None,
        'launcher_log':str(session.log_path),'geometry':json.loads((APP/'array_geometry.json').read_text(encoding='utf-8-sig')),
        'worker_stopped':not session.thread.is_alive(),'failure':failure,
        'protocol':'User plans two loops of the same LOCATE file, with a deliberate phone pause of a few seconds. Exact playback transition times are not synchronized; no absolute bearing was measured.',
        'finish_requested':finish_requested,'audio_output':'receive-only; no computer playback'}
    (destination/'trial.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('checkpoint','windows','duration_s','worker_stopped','failure')},indent=2),flush=True)
    print('RX4_TRIAL_SAVED '+str(destination/'trial.json'),flush=True)
    if failure or not audio or session.thread.is_alive():raise SystemExit(1)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=float,default=75)
    parser.add_argument('--gui',action='store_true')
    args=parser.parse_args()
    (capture_gui if args.gui else capture)(args.seconds)
