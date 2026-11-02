from pathlib import Path
import json
import math
import sys
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
sys.path.insert(0,str(ROOT))
from beacon_dsp import BeaconEstimator,SIZE,RATE

capture=PROJECT/'stages/01-16-18kHz/phone-debug'
audio=np.load(capture/'phone-capture.npz')['audio']
receiver=BeaconEstimator(ROOT/'array_geometry.json','coded-16-18')
frequencies=np.fft.rfftfreq(SIZE,1/RATE)
positions=np.array([(0,0) if ch==6 else (.04*math.sin(math.radians(ch*60)),.04*math.cos(math.radians(ch*60))) for ch in range(7)])
matrix=np.column_stack((positions*RATE/343,np.ones(7)))

def peaks(samples,white=False):
    x=np.fft.rfft(samples-samples.mean(axis=0),axis=0).T
    band=x[:,receiver.indices]
    mag=np.abs(band)
    ref=np.maximum(np.median(mag,axis=1,keepdims=True),1e-9)
    gain=np.clip((ref/np.maximum(mag,ref*.12))**.65,.025,3.) if white else 1
    matched=np.zeros((7,SIZE),complex)
    matched[:,receiver.indices]=band*np.conj(receiver.spectrum[receiver.indices])*gain
    impulse=np.fft.ifft(matched,axis=1)
    envelope=np.abs(impulse)
    tau=[]
    for row in envelope:
        peak=int(row.argmax());a,b,c=np.log(np.maximum(row[(np.array([-1,0,1])+peak)%SIZE],1e-20))
        fraction=.5*(a-c)/(a-2*b+c) if abs(a-2*b+c)>1e-15 else 0
        tau.append(peak+fraction)
    tau=np.array(tau);tau=(tau-tau[-1]+SIZE/2)%SIZE-SIZE/2
    fit=np.linalg.lstsq(matrix,tau,rcond=None)[0]
    residual=tau-matrix@fit
    return {'tau':np.round(tau,2).tolist(),'angle':round(math.degrees(math.atan2(fit[0],fit[1]))%360,2),
            'norm':round(float(np.linalg.norm(fit[:2])),2),'rms':round(float(np.sqrt(np.mean(residual**2))),2),
            'residual':np.round(residual,2).tolist()}

rows=[]
for i,samples in enumerate(audio):
    result,channels=receiver.estimate(samples,{},1+i*.22)
    if result.get('code_channels',0)<6:continue
    row={'block':i,'level':result['band_level_dbfs'],'old_angle':result.get('candidate_angle_deg'),
         'old_rms':result.get('all_pair_rms_samples'),'direct_peak':peaks(samples),
         'whitened_peak':peaks(samples,True)}
    rows.append(row)
    print(json.dumps(row))
(capture/'peak-analysis.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
