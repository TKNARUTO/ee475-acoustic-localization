"""Reject abrupt reversed bearings; calibrate circularly from stable samples."""
from pathlib import Path
import json
import math
import sys
import tempfile
import time
import numpy as np

PROJECT=Path(__file__).resolve().parents[1];ROOT=PROJECT/'SEN0325-Pico-Setup'
sys.path.insert(0,str(ROOT))
from beacon_dsp import BeaconEstimator,template,SIZE,RATE
from direction_estimator import PhaseEstimator
from sen0325_launcher import Session
from radar_canvas import DirectionState
report={'stage':'HF2','checks':{}}
checks=report['checks']
config=json.loads((ROOT/'array_geometry.json').read_text(encoding='utf-8-sig'))
config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)
code,spectrum,_=template('coded-20');spectrum/=np.std(code)
frequency=np.fft.rfftfreq(SIZE,1/RATE);rng=np.random.default_rng(475002)
def plane(angle):
    rows=[]
    for ch in range(7):
        tau=0 if ch==6 else .04*math.cos(math.radians(angle-ch*60))/343
        rows.append(120*np.fft.irfft(spectrum*np.exp(2j*np.pi*frequency*(tau-.015)),SIZE)+rng.normal(0,15,SIZE))
    return np.rint(np.column_stack(rows)).astype('<i2')
with tempfile.TemporaryDirectory() as temporary:
    geometry=Path(temporary)/'geometry.json';geometry.write_text(json.dumps(config),encoding='utf-8')
    receiver=BeaconEstimator(geometry,'coded-20');display=DirectionState()
    for i in range(6):
        result,_=receiver.estimate(plane(0),{},1+i*.22)
    assert result['valid'],result
    last_good=result['received_at'];checks['initial_stable_direction_accepted']=True
    results=[]
    for i in range(6):
        now=last_good+(i+1)*.22
        result,_=receiver.estimate(plane(180),{},now)
        display.update(result,now)
        results.append(result)
        assert not result['valid'],result
        assert display.current(now)[0] is None
    checks['180_degree_jump_suppressed']=any(r['reason']=='direction_jump_rejected' for r in results)
    checks['rejected_jump_clears_ui_arrow']=True
    for i in range(6):
        result,_=receiver.estimate(plane(180),{},last_good+5.2+i*.22)
    checks['deliberate_new_position_can_reacquire']=result['valid']
    report['jump_reasons']=[r['reason'] for r in results]
    session=Session();session.direction_estimator=PhaseEstimator(geometry)
    session.set_mode('coded-20');session.set_running(True)
    now=time.monotonic()
    session.last_direction={'valid':True,'frequency':20000,'profile':'coded-20','received_at':now,'raw_angle_deg':0}
    session.recent_directions.append(dict(session.last_direction))
    try:session.set_front()
    except ValueError:checks['single_sample_calibration_rejected']=True
    else:raise AssertionError('One direction was enough to set front')
    session.recent_directions.clear()
    for i,angle in enumerate((359.,0.,1.)):
        session.recent_directions.append(dict(session.last_direction,raw_angle_deg=angle,received_at=now-.6+i*.2))
    session.set_front()
    offset=session.direction_estimator.config['heading_offset_deg']
    checks['front_calibration_uses_circular_mean']=min(offset,360-offset)<.01
    previous=geometry.read_bytes();session.recent_directions.clear()
    for i,angle in enumerate((0,170,180)):
        session.recent_directions.append(dict(session.last_direction,raw_angle_deg=angle,received_at=now-.6+i*.2))
    try:session.set_front()
    except ValueError:checks['unstable_calibration_rejected']=True
    else:raise AssertionError('Unstable directions changed the heading')
    checks['failed_calibration_preserves_saved_heading']=geometry.read_bytes()==previous
    session.stop.set()
report['passed']=all(checks.values())
(PROJECT/'stages/02-20kHz/direction-guard-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
