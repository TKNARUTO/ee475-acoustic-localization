"""Reference import, source preservation, rejection and real detector checks."""
from pathlib import Path
import hashlib
import json
import math
import sys
import tempfile
import wave
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/06-joint-delay'
sys.path.insert(0,str(ROOT))
from beacon_importer import import_reference,load_active
from beacon_dsp import BeaconEstimator,template,SIZE,RATE
report={'stage':'HF2','checks':{}}
checks=report['checks']
preset=PROJECT/'audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3'
digest=hashlib.sha256(preset.read_bytes()).hexdigest()
data=import_reference(preset,ROOT)
checks['mp3_preset_imports']=data['spec']['low']==19000 and data['spec']['high']==21000
checks['source_file_preserved']=hashlib.sha256(preset.read_bytes()).hexdigest()==digest
checks['active_reference_reloads']=load_active(ROOT)==data

rng=np.random.default_rng(9825475)
with tempfile.TemporaryDirectory() as temporary:
    folder=Path(temporary)
    frequency=np.fft.rfftfreq(SIZE,1/RATE)
    mask=(frequency>=19000)&(frequency<=21000)
    spectrum=np.zeros(SIZE//2+1,complex)
    spectrum[mask]=np.hanning(mask.sum())*np.exp(1j*rng.uniform(-np.pi,np.pi,mask.sum()))
    code=np.fft.irfft(spectrum,SIZE);code*=.3/max(abs(code))
    custom=folder/'custom different code.wav'
    with wave.open(str(custom),'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(RATE)
        audio.writeframes(np.rint(np.tile(code,32)*32767).astype('<i2').tobytes())
    imported=import_reference(custom,ROOT)
    checks['different_user_code_imports']=imported['profile']!=data['profile'] and imported['periodicity']>.99
    code,spectrum,mask=template(imported['profile'])
    config=json.loads((ROOT/'array_geometry.json').read_text(encoding='utf-8-sig'))
    config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)
    geometry=folder/'geometry.json';geometry.write_text(json.dumps(config),encoding='utf-8')
    accepted=[]
    for angle in (0,45,90,180,270,359):
        receiver=BeaconEstimator(geometry,imported['profile'])
        for i in range(5):
            rows=[]
            for ch in range(7):
                tau=0 if ch==6 else .04*math.cos(math.radians(angle-ch*60))/343
                signal=np.fft.irfft(spectrum/np.std(code)*120*np.exp(2j*np.pi*frequency*(tau-.015)),SIZE)
                rows.append(signal+rng.normal(0,25,SIZE))
            result,_=receiver.estimate(np.rint(np.column_stack(rows)).astype('<i2'),{},1+i*.22)
            if result['valid']:
                error=abs((result['raw_angle_deg']-angle+180)%360-180)
                accepted.append(error)
                assert error<5,result
        assert result['valid'],result
    checks['imported_code_runs_actual_direction_estimator']=len(accepted)>=18
    report['maximum_generated_direction_error_deg']=round(max(accepted),3)
    active_before=(ROOT/'beacon_profiles/active.json').read_bytes()
    for name,path in [('pure_tone',PROJECT/'audio/phone/HF2-20kHz/13_TONE_20000Hz_level-only.mp3')]:
        try:import_reference(path,ROOT)
        except ValueError as error:report[name+'_message']=str(error)
        else:raise AssertionError(name+' was incorrectly accepted')
    noise=folder/'random nonperiodic.wav'
    f=np.fft.rfftfreq(RATE*2,1/RATE)
    band=(f>=19000)&(f<=21000)
    random_spectrum=np.zeros(len(f),complex)
    random_spectrum[band]=np.exp(1j*rng.uniform(-np.pi,np.pi,band.sum()))
    random_audio=np.fft.irfft(random_spectrum,RATE*2)
    random_audio*=1000/np.std(random_audio)
    with wave.open(str(noise),'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(RATE)
        audio.writeframes(np.rint(random_audio).astype('<i2').tobytes())
    try:import_reference(noise,ROOT)
    except ValueError as error:report['nonperiodic_message']=str(error)
    else:raise AssertionError('Nonperiodic audio was accepted')
    checks['bad_import_preserves_previous_reference']=(ROOT/'beacon_profiles/active.json').read_bytes()==active_before
    checks['pure_tone_rejected']='narrow' in report['pure_tone_message']
    checks['nonperiodic_audio_rejected']=bool(report['nonperiodic_message'])
    # Wrong code in the SAME band must not authorize a direction.
    _,wrong_spectrum,_=template('coded-20')
    receiver=BeaconEstimator(geometry,imported['profile'])
    for i in range(4):
        sample=np.tile((200*np.fft.irfft(wrong_spectrum,SIZE)/np.std(code))[:,None],(1,7))
        result,_=receiver.estimate(sample,{},1+i*.22)
        assert not result['valid'],result
    checks['wrong_code_same_band_rejected']=True

import_reference(preset,ROOT)
checks['configured_preset_reference_restored']=load_active(ROOT)['source_name']==preset.name
report['passed']=all(checks.values())
(STAGE/'import-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
