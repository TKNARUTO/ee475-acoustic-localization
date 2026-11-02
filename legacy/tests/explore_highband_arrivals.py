from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]/'SEN0325-Pico-Setup'
sys.path.insert(0,str(ROOT))
from beacon_dsp import BeaconEstimator,SIZE
r=BeaconEstimator(ROOT/'array_geometry.json','coded-16-18')
audio=np.load(ROOT.parent/'stages/01-16-18kHz/phone-debug/phone-capture.npz')['audio']
for block in (0,5,13,15,24,25,28):
    x=np.fft.rfft(audio[block],axis=0).T
    m=np.zeros((7,SIZE),complex);m[:,r.indices]=x[:,r.indices]*np.conj(r.spectrum[r.indices])
    envelope=np.abs(np.fft.ifft(m,axis=1));envelope/=envelope.max(axis=1,keepdims=True)
    center=int(envelope.mean(axis=0).argmax())
    print('BLOCK',block,'center',center)
    for ch,row in enumerate(envelope):
        peaks=np.flatnonzero((row>np.roll(row,1))&(row>np.roll(row,-1))&(row>.15))
        peaks=sorted(peaks,key=lambda p:row[p],reverse=True)[:8]
        print(ch,[(round(float((p-center+SIZE/2)%SIZE-SIZE/2),2),round(float(row[p]),3)) for p in peaks])
