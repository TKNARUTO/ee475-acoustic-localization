"""HF1.1 regression: strong multipath repair, captured replay, actual signal plot."""
from pathlib import Path
import importlib.util
import json
import math
import sys
import tempfile
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/01-16-18kHz'
sys.path.insert(0,str(ROOT))
from beacon_dsp import BeaconEstimator,template,SIZE,RATE
from signal_scope import signal_payload
oldspec=importlib.util.spec_from_file_location('hf_before_fix',STAGE/'phone-debug/highband-before-fix.py')
old=importlib.util.module_from_spec(oldspec);oldspec.loader.exec_module(old)
rng=np.random.default_rng(475011)
frequency=np.fft.rfftfreq(SIZE,1/RATE)
code,spectrum,_=template('coded-16-18')
spectrum/=np.std(code)
config=json.loads((ROOT/'array_geometry.json').read_text(encoding='utf-8-sig'))
config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)
report={'stage':'HF1.1','purpose':'Generated multipath and saved physical capture replay; no independent physical angle truth',
        'multipath':[]}
with tempfile.TemporaryDirectory() as temporary:
    geometry=Path(temporary)/'geometry.json';geometry.write_text(json.dumps(config),encoding='utf-8')
    for angle in (0,45,90,180,270,359):
        before=BeaconEstimator(geometry,'coded-16-18');after=BeaconEstimator(geometry,'coded-16-18')
        newresults=[];oldresults=[]
        for i in range(6):
            channels=[]
            for ch in range(7):
                tau=0 if ch==6 else .04*math.cos(math.radians(angle-ch*60))/343
                reflected=0 if ch==6 else .04*math.cos(math.radians(210-ch*60))/343
                direct=spectrum*np.exp(2j*np.pi*frequency*(tau-.018))
                echo=spectrum*np.exp(2j*np.pi*frequency*(reflected-.019))
                amplitude=(2.,1.5,1.4,.2,.2,.2,.2)[ch]
                channels.append(120*np.fft.irfft(direct+amplitude*echo,SIZE)+rng.normal(0,25,SIZE))
            samples=np.rint(np.column_stack(channels)).astype('<i2')
            b,_=old.estimate_highband(before,samples,{},1+i*.22)
            a,_=after.estimate(samples,{},1+i*.22)
            oldresults.append(b);newresults.append(a)
        accepted=[r for r in newresults if r['valid']]
        errors=[abs((r['raw_angle_deg']-angle+180)%360-180) for r in accepted]
        row={'angle':angle,'before_valid':sum(r['valid'] for r in oldresults),
             'after_valid':len(accepted),'fallback_valid':sum(r.get('direction_source')=='strong_code_arrival_consensus' for r in accepted),
             'max_generated_error_deg':round(max(errors),3) if errors else None}
        report['multipath'].append(row)
        print(json.dumps(row))
        if errors and max(errors)>=15:print(json.dumps(newresults[-1]))
        if errors:assert max(errors)<15,row

    captures=np.load(STAGE/'phone-debug/phone-capture.npz')['audio']
    before=BeaconEstimator(geometry,'coded-16-18');after=BeaconEstimator(geometry,'coded-16-18')
    oldrows=[];newrows=[]
    for i,samples in enumerate(captures):
        b,_=old.estimate_highband(before,samples,{},1+i*.22)
        a,_=after.estimate(samples,{},1+i*.22)
        oldrows.append(b);newrows.append(a)
    report['physical_capture_replay']={'blocks':len(captures),'before_valid':sum(r['valid'] for r in oldrows),
        'after_valid':sum(r['valid'] for r in newrows),'rows_after':newrows,
        'limitation':'Recorded position was not independently measured; acceptance rate is not angular accuracy.'}
    assert report['physical_capture_replay']['after_valid']>report['physical_capture_replay']['before_valid']

    # The secondary plot must show captured sound even for a plain, uncoded tone.
    samples=np.tile((2000*np.sin(2*np.pi*17000*np.arange(SIZE)/RATE))[:,None],(1,7))
    payload=signal_payload(samples,123,4.5)
    assert abs(payload['peak_frequency_hz']-17000)<RATE/SIZE
    assert len(payload['spectrum_dbfs_bin'])==320 and len(payload['waveform16'])==256
    assert payload['sequence']==123 and payload['received_at']==4.5
    ch=('D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER').index(payload['waveform_channel'])
    expected=samples[:256,ch]-samples[:,ch].mean()
    assert np.max(np.abs(np.array(payload['waveform16'])-expected))<=.051
    receiver=BeaconEstimator(geometry,'coded-16-18')
    direction,_=receiver.estimate(samples,{},1)
    assert not direction['valid']
    report['signal_scope']={'plain_17000_hz_peak_visible':True,'plain_tone_has_no_direction':True,
                            'waveform_matches_capture':True,'sample_sequence_preserved':True,
                            'measured_peak_hz':payload['peak_frequency_hz']}
assert sum(r['fallback_valid'] for r in report['multipath'])>=6
assert sum(r['after_valid'] for r in report['multipath'])>sum(r['before_valid'] for r in report['multipath'])
report['passed']=True
(STAGE/'arrival-scope-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('HF1.1 validation passed')
