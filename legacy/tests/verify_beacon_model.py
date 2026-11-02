"""Synthetic signal/noise/echo and negative identity checks, not distance acceptance."""
import json
import math
from pathlib import Path
import sys
import tempfile
import time
import numpy as np
root=Path(__file__).resolve().parents[1]/'SEN0325-Pico-Setup'
sys.path.insert(0,str(root))
from beacon_dsp import BeaconEstimator,PROFILES,template,SIZE,RATE,prepare_beacon
rng=np.random.default_rng(475)
config=json.loads((root/'array_geometry.json').read_text(encoding='utf-8-sig'))
config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)
results=[]
def plane(profile,angle,amplitude=4000,noise=40,echo=False):
    _,spec,_=template(profile)
    freq=np.fft.rfftfreq(SIZE,1/RATE)
    rows=[]
    for i in range(7):
        delta=0 if i==6 else .04*math.cos(math.radians(angle-i*60))/343
        signal=spec*np.exp(2j*np.pi*freq*(delta-.018))
        if echo:
            reflected=0 if i==6 else .04*math.cos(math.radians(200-i*60))/343
            signal+=.45*spec*np.exp(2j*np.pi*freq*(reflected-.023))
        rows.append(amplitude*np.fft.irfft(signal,SIZE)+rng.normal(0,noise,SIZE))
    return np.array(rows).T
with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'geometry.json';path.write_text(json.dumps(config),encoding='utf-8')
    for profile in PROFILES:
        prepare_beacon(root,profile)
        for angle in (0,45,90,180,270,359):
            est=BeaconEstimator(path,profile)
            for i in range(3):
                result,_=est.estimate(plane(profile,angle,echo=True),{'frames':SIZE},i*.4+1)
            error=abs((result.get('raw_angle_deg',result.get('candidate_angle_deg',-999))-angle+180)%360-180)
            results.append({'profile':profile,'source_deg':angle,'error_deg':error,'result':result})
            assert error<5,results[-1]
            assert result['valid'],results[-1]
        for kind in ('silence','noise','single_tone','wrong_code'):
            est=BeaconEstimator(path,profile)
            for i in range(3):
                if kind=='silence': samples=np.zeros((SIZE,7))
                elif kind=='noise': samples=rng.normal(0,200,(SIZE,7))
                elif kind=='single_tone': samples=np.tile((1000*np.sin(2*np.pi*PROFILES[profile]['center']*np.arange(SIZE)/RATE))[:,None],(1,7))
                else:
                    _,spec,_=template(profile)
                    spec*=np.exp(1j*rng.uniform(-np.pi,np.pi,len(spec)))
                    samples=np.tile((4000*np.fft.irfft(spec,SIZE))[:,None],(1,7))
                result,_=est.estimate(samples,{'frames':SIZE},i*.4+1)
            assert not result['valid'] and result['reason']=='beacon_not_detected',(profile,kind,result)
    report={'passed':True,'positive_cases':results,'negative_cases_per_profile':['silence','noise','single_tone','wrong_code'],
            'limitation':'Synthetic delayed known-code signals with noise and 45% delayed reflection; not a physical range or hearing test.'}
    (root.parent/'reports/validation/beacon-model-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'cases':len(results),'maximum_synthetic_error_deg':max(r['error_deg'] for r in results),
                      'max_processing_ms':max(r['result']['processing_ms'] for r in results)},indent=2))
