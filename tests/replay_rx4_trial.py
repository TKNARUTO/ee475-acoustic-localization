"""Identical-input RX3/RX4 comparison of a full local phone trial."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,importlib.util,json,sys,tempfile,zipfile
import numpy as np
PROJECT=Path(__file__).resolve().parents[1];APP=PROJECT/'SEN0325-Pico-Setup';STAGE=PROJECT/'stages/06-joint-delay'
sys.path.insert(0,str(APP))
from beacon_dsp import BeaconEstimator

def replay(path):
    trial=json.loads(path.read_text(encoding='utf-8-sig'));raw_path=path.with_name(trial['raw_file'])
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest()==trial['raw_sha256']
    with np.load(raw_path,allow_pickle=False) as z:audio=z['audio'].copy();times=z['received_at'].copy()
    with tempfile.TemporaryDirectory() as temporary:
        folder=Path(temporary);geometry=folder/'geometry.json';geometry.write_text(json.dumps(trial['geometry']))
        with zipfile.ZipFile(STAGE/'backups/before-RX4.zip') as z:
            source=folder/'rx3.py';source.write_bytes(z.read('SEN0325-Pico-Setup/highband_dsp.py'))
        spec=importlib.util.spec_from_file_location('rx3_phone_trial',source)
        rx3=importlib.util.module_from_spec(spec);spec.loader.exec_module(rx3)
        old=BeaconEstimator(geometry,'coded-20');new=BeaconEstimator(geometry,'coded-20');rows=[]
        for sample,now,event in zip(audio,times,trial['events']):
            a,_=rx3.estimate_highband(old,sample,event['health'],float(now))
            b,_=new.estimate(sample,event['health'],float(now))
            rows.append({'sequence':event['sequence'],'time_s':float(now-times[0]),'RX3':a,'RX4':b})
    lost=[r['sequence'] for r in rows if r['RX3']['valid'] and not r['RX4']['valid']]
    altered=[r['sequence'] for r in rows if r['RX3']['valid'] and r['RX4']['valid'] and abs(r['RX3']['raw_angle_deg']-r['RX4']['raw_angle_deg'])>1e-8]
    report={'source_trial':str(path),'raw_sha256_verified':True,'windows':len(rows),
        'RX3_reasons':dict(Counter(r['RX3']['reason'] for r in rows)),
        'RX4_reasons':dict(Counter(r['RX4']['reason'] for r in rows)),
        'lost_previous_valid_sequences':lost,'altered_previous_raw_angles':altered,
        'additional_valid_windows':sum(r['RX4']['valid'] and not r['RX3']['valid'] for r in rows),'rows':rows,
        'limitation':'Same recorded input and fresh starting state. More accepted bearings do not prove physical accuracy; manual interruptions and phone motion were not synchronized.'}
    (path.parent/'RX3-RX4-replay.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','limitation')},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('trial',type=Path);replay(parser.parse_args().trial)
