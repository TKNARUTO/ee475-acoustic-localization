"""Offline diagnostic experiment: cross-burst averaging versus current burst.

Does not edit the active estimator or alter its acceptance thresholds.
"""
from pathlib import Path
from collections import Counter
import argparse
import json
import math
import sys
import tempfile
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
APP=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/05-direction-diagnostics'
sys.path.insert(0,str(APP))
from beacon_dsp import BeaconEstimator
import highband_dsp

def run(paths):
    report={'purpose':'Offline diagnostic ablation, not a deployed algorithm or physical angle validation','captures':[]}
    original=highband_dsp.fit_delays
    try:
        for path in paths:
            meta=json.loads(path.read_text(encoding='utf-8'))
            with np.load(path.with_name(meta['raw_file']),allow_pickle=False) as z:
                audio=z['audio'].copy();times=z['received_at'].copy()
            variants={}
            with tempfile.TemporaryDirectory() as temporary:
                geometry=Path(temporary)/'geometry.json';geometry.write_text(json.dumps(meta['geometry']))
                for variant in ('current_two_or_three_bursts','single_current_burst'):
                    def fitting(receiver,averaged,pairs):
                        return original(receiver,receiver.history[-1][1] if variant=='single_current_burst' else averaged,pairs)
                    highband_dsp.fit_delays=fitting
                    receiver=BeaconEstimator(geometry,meta['profile']);rows=[]
                    for sample,now,event in zip(audio,times,meta['events']):
                        result,_=receiver.estimate(sample,event['health'],float(now));rows.append(result)
                    variants[variant]={'reasons':dict(Counter(r['reason'] for r in rows)),
                        'primary_geometry_passes':sum(r.get('valid',False) and r.get('delay_fit')=='bounded_complex_coherence' for r in rows),
                        'rows':rows}
            report['captures'].append({'metadata':str(path),'variants':variants})
    finally:highband_dsp.fit_delays=original
    output=STAGE/'single-burst-experiment.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps([{'capture':Path(r['metadata']).name,'variants':{k:{s:v[s] for s in ('reasons','primary_geometry_passes')} for k,v in r['variants'].items()}} for r in report['captures']],indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('metadata',type=Path,nargs='+')
    run(parser.parse_args().metadata)
