"""Read a local RX3 snapshot and compare identical raw blocks with RX2/RX3.

No serial device, playback, calibration change or raw-audio upload.
"""
from pathlib import Path
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile

import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
APP=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/05-direction-diagnostics'
sys.path.insert(0,str(APP))
from beacon_dsp import BeaconEstimator, SIZE

def analyze(path, output=None):
    path=Path(path).resolve()
    meta=json.loads(path.read_text(encoding='utf-8-sig'))
    raw_path=path.with_name(meta['raw_file'])
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest()==meta['raw_sha256'], 'Raw checksum mismatch'
    with np.load(raw_path,allow_pickle=False) as raw:
        audio=raw['audio'].copy();sequences=raw['sequence'].copy();times=raw['received_at'].copy()
    assert audio.shape==(meta['block_count'],SIZE,7) and audio.dtype==np.dtype('<i2')
    assert len(meta['events'])==len(audio)==len(sequences)==len(times)
    assert np.all(np.isfinite(times)) and np.all(np.diff(times)>0)
    pair_residuals=defaultdict(list);arrival_rejections=Counter();results=[]
    with tempfile.TemporaryDirectory() as temporary:
        folder=Path(temporary)
        geometry=folder/'geometry.json';geometry.write_text(json.dumps(meta['geometry']),encoding='utf-8')
        with zipfile.ZipFile(STAGE/'backups/before-RX3.zip') as archive:
            baseline_path=folder/'rx2.py';baseline_path.write_bytes(archive.read('SEN0325-Pico-Setup/highband_dsp.py'))
        spec=importlib.util.spec_from_file_location('rx2_snapshot_replay',baseline_path)
        baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
        old=new=None;last=None;generation=None
        for i,(sample,event,sequence,now) in enumerate(zip(audio,meta['events'],sequences,times)):
            health=event['health']
            assert int(sequence)==health['seq'] and abs(now-event['estimate']['received_at'])<1e-6
            if new is None or generation!=event['generation'] or now-last>=.75:
                old=BeaconEstimator(geometry,meta['profile']);new=BeaconEstimator(geometry,meta['profile'])
            generation=event['generation'];last=float(now)
            before,_=baseline.estimate_highband(old,sample,health,float(now))
            after,_=new.estimate(sample,health,float(now))
            results.append({'sequence':int(sequence),'received_at':float(now),'recorded':event['estimate'],
                            'rx2_replay':before,'rx3_replay':after})
            if after['reason']=='group_delay_inconsistent':
                for pair in after.get('pair_delay_diagnostics',[]):
                    if 'residual_samples' in pair:
                        pair_residuals[' / '.join(pair['pair'])].append(abs(pair['residual_samples']))
                arrival_rejections.update(after.get('arrival_rejection_counts',{}))
    distribution=lambda key:dict(Counter(r[key]['reason'] for r in results))
    report={'source_metadata':str(path),'raw_sha256_verified':True,'blocks':len(audio),'profile':meta['profile'],
            'rx2_reasons':distribution('rx2_replay'),'rx3_reasons':distribution('rx3_replay'),
            'rejected_primary_pair_residuals':sorted([{'pair':pair,'windows':len(values),
                'median_absolute_residual_samples':round(float(np.median(values)),4)}
                for pair,values in pair_residuals.items()],key=lambda p:p['median_absolute_residual_samples'],reverse=True),
            'arrival_cluster_rejections':dict(arrival_rejections),'rows':results,
            'limitation':'Both estimators start fresh at snapshot boundaries. Accepted counts are not angle accuracy. Phone pauses, position and true bearing are unknown unless separately recorded. Pair residuals identify inconsistent relationships, not a proven faulty microphone.'}
    output=Path(output) if output else STAGE/'replays'/(path.stem+'-analysis.json')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report,output

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('metadata',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    report,output=analyze(args.metadata,args.output)
    print(json.dumps({'blocks':report['blocks'],'rx2_reasons':report['rx2_reasons'],
                      'rx3_reasons':report['rx3_reasons'],'output':str(output)},indent=2))
