"""HF1 receiver regression on generated signals, not physical range acceptance."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import tempfile
import time
import wave
import zipfile
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
sys.path.insert(0,str(ROOT))
from beacon_dsp import BeaconEstimator,template,prepare_beacon,RATE,SIZE

PROFILE='coded-20'
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=PROJECT/'stages/06-joint-delay/model-validation.json')
args=parser.parse_args()
rng=np.random.default_rng(1618001)
frequency=np.fft.rfftfreq(SIZE,1/RATE)
code,spectrum,mask=template(PROFILE)
spectrum=spectrum/np.std(code)
config=json.loads((ROOT/'array_geometry.json').read_text(encoding='utf-8-sig'))
config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)

def plane(angle,rms=80,noise=80,colored=False,spur=0,phase_offsets=False,echo=0):
    rows=[]
    for ch in range(7):
        tau=0 if ch==6 else .04*math.cos(math.radians(angle-ch*60))/343
        phase=np.exp(2j*np.pi*frequency*(tau-.018))
        transfer=np.ones(len(frequency))
        if colored:
            transfer*=10**(-16*np.clip((frequency-19000)/2000,0,1)/20)
            transfer*=1+.15*np.sin((frequency-19000)/140+ch*.05)
        source=spectrum*phase*transfer
        if phase_offsets:source*=np.exp(1j*ch*.57)
        if echo:
            delay=0 if ch==6 else .04*math.cos(math.radians(210-ch*60))/343
            source+=echo*spectrum*np.exp(2j*np.pi*frequency*(delay-.024))
        signal=rms*np.fft.irfft(source,SIZE)
        if spur:signal+=spur*np.sin(2*np.pi*20062.5*np.arange(SIZE)/RATE+ch*.2)
        rows.append(signal+rng.normal(0,noise,SIZE))
    return np.rint(np.column_stack(rows)).astype(np.int16)

results=[];negatives=[];processing=[];sensitivity=[]
with tempfile.TemporaryDirectory() as temporary:
    geometry=Path(temporary)/'geometry.json';geometry.write_text(json.dumps(config),encoding='utf-8')
    cases=[dict(name='strong',rms=80,noise=80),
           dict(name='weak_colored',rms=35,noise=80,colored=True),
           dict(name='narrow_interference',rms=45,noise=80,spur=1200),
           dict(name='carrier_phase_offsets',rms=80,noise=60,phase_offsets=True),
           dict(name='delayed_echo',rms=80,noise=60,echo=.35)]
    for scenario in cases:
        settings={k:v for k,v in scenario.items() if k!='name'}
        for angle in (0,45,90,180,270,359):
            receiver=BeaconEstimator(geometry,PROFILE)
            captures=[]
            for i in range(8 if scenario['name']=='weak_colored' else 4):
                result,channels=receiver.estimate(plane(angle,**settings),{'frames':SIZE},1+i*.22)
                captures.append(result);processing.append(result['processing_ms'])
            accepted=[r for r in captures if r['valid']]
            errors=[abs((r['raw_angle_deg']-angle+180)%360-180) for r in accepted]
            row={'scenario':scenario['name'],'true_angle_deg':angle,'error_deg':round(max(errors),3) if errors else None,
                 'final':result,'code_hit_windows':sum(r['code_channels']>=4 for r in captures)}
            results.append(row)
            assert row['code_hit_windows']>=3,row
            if scenario['name']!='weak_colored':assert result['valid'],row
            if errors:assert max(errors)<15,row
    for kind in ('silence','white_noise','correlated_noise','1000_hz','20000_hz','wrong_code','20_22_code'):
        for trial in range(12):
            receiver=BeaconEstimator(geometry,PROFILE)
            for i in range(3):
                if kind=='silence':samples=np.zeros((SIZE,7))
                elif kind=='white_noise':samples=rng.normal(0,150,(SIZE,7))
                elif kind=='correlated_noise':samples=np.tile(rng.normal(0,150,SIZE)[:,None],(1,7))
                elif kind.endswith('_hz'):
                    hz=int(kind.split('_')[0]);samples=np.tile((1500*np.sin(2*np.pi*hz*np.arange(SIZE)/RATE))[:,None],(1,7))
                elif kind=='wrong_code':
                    wrong=spectrum*np.exp(1j*rng.uniform(-np.pi,np.pi,len(spectrum)))
                    samples=np.tile((100*np.fft.irfft(wrong,SIZE))[:,None],(1,7))
                else:
                    old,_,_=template('coded-ultrasonic')
                    samples=np.tile((100*old/np.std(old))[:,None],(1,7))
                result,_=receiver.estimate(samples,{'frames':SIZE},1+i*.22)
                assert not result['valid'],(kind,trial,result)
            negatives.append({'input':kind,'trial':trial,'reason':result['reason'],'code_channels':result['code_channels']})
    # Packet faults, clipping and malformed samples must clear temporal evidence.
    guards=[]
    for name,data,health in [('capture_gap',plane(90),{'dropped':1}),
                             ('clipping',np.full((SIZE,7),32767),{}),
                             ('invalid_raw_audio',np.zeros((16,7)),{})]:
        receiver=BeaconEstimator(geometry,PROFILE)
        for i in range(3):receiver.estimate(plane(90),{},1+i*.22)
        result,_=receiver.estimate(data,health,2)
        assert not result['valid'] and result['reason']==name and not receiver.history,(name,result)
        guards.append(name)
    # Keep legacy estimators and emitted audible waveform identical to rollback copy.
    with zipfile.ZipFile(PROJECT/'legacy/stages/01-16-18kHz/before-stage-1.zip') as z:
        old_module=z.read('beacon_dsp.py').decode('utf-8')
    namespace={};exec(compile(old_module,'before_stage_1.py','exec'),namespace)
    old_code=namespace['template']('coded-audible')[0]
    assert np.array_equal(old_code,template('coded-audible')[0])
    old_receiver=namespace['BeaconEstimator'](geometry,'coded-audible')
    new_receiver=BeaconEstimator(geometry,'coded-audible')
    _,audible_spectrum,_=template('coded-audible')
    for i in range(4):
        data=[]
        for ch in range(7):
            tau=0 if ch==6 else .04*math.cos(math.radians(45-ch*60))/343
            data.append(5000*np.fft.irfft(audible_spectrum*np.exp(2j*np.pi*frequency*(tau-.018)),SIZE)+rng.normal(0,30,SIZE))
        data=np.column_stack(data)
        before,_=old_receiver.estimate(data.copy(),{},1+i*.22)
        after,_=new_receiver.estimate(data.copy(),{},1+i*.22)
        before.pop('processing_ms');after.pop('processing_ms')
        assert before==after,(before,after)
    # Receiver-only A/B: same 16-18 kHz samples and the SAME new template on both
    # sides. The reference is the old detector retuned to this band, not 20-22 kHz.
    namespace['PROFILES'][PROFILE]={'low':16000,'high':18000,'center':17000}
    namespace['template']=template
    for scenario,spur in [('colored_noise',0),('colored_plus_narrow_tone',800)]:
        for amplitude in (8,12,18,25):
            counts={'before':0,'after':0};windows=0
            for trial in range(6):
                before=namespace['BeaconEstimator'](geometry,PROFILE)
                after=BeaconEstimator(geometry,PROFILE)
                for i in range(3):
                    data=plane(45,rms=amplitude,noise=80,colored=True,spur=spur)
                    a,_=before.estimate(data.copy(),{},1+i*.22)
                    b,_=after.estimate(data.copy(),{},1+i*.22)
                    counts['before']+=a.get('code_channels',0)>=4
                    counts['after']+=b.get('code_channels',0)>=4
                    windows+=1
            sensitivity.append({'scenario':scenario,'source_rms16_before_response_tilt':amplitude,
                                'windows':windows,'old_detector_code_hits':int(counts['before']),
                                'hf1_code_hits':int(counts['after'])})

report={'passed':True,'profile':PROFILE,'positive_cases':results,'negative_trials':negatives,'guard_checks':guards,
        'receiver_only_sensitivity_sweep':sensitivity,
        'audible_template_and_estimator_unchanged':True,
        'maximum_simulated_error_deg':max(r['error_deg'] for r in results if r['error_deg'] is not None),
        'median_processing_ms':round(float(np.median(processing)),2),'maximum_processing_ms':max(processing),
        'limitation':'Generated samples including response tilt, independent carrier phase offsets, a narrow tone and one delayed echo. No real phone, physical angular accuracy, range or hearing acceptance claim.'}
destination=args.output
destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({key:report[key] for key in ('passed','maximum_simulated_error_deg','median_processing_ms','maximum_processing_ms')},indent=2))
