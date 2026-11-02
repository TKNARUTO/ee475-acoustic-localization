"""Create and decode-audit phone test MP3s. Never play an audio device."""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import wave
import imageio_ffmpeg
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
DEST=PROJECT/'audio/phone/HF2-20kHz'
STAGE=PROJECT/'stages/06-joint-delay'
DEST.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT))
from beacon_dsp import BeaconEstimator,prepare_beacon,RATE,SIZE
from highband_dsp import probe_levels

encoder=imageio_ffmpeg.get_ffmpeg_exe()
options=['-c:a','libmp3lame','-q:a','0','-compression_level','0',
         '-cutoff','22000','-joint_stereo','0','-write_xing','1']
items=[]
for filename,profile in [('01_LOCATE_20kHz_19-21kHz.mp3','coded-20')]:
    path=prepare_beacon(ROOT,profile,single_speaker=True)
    with wave.open(str(path),'rb') as audio:
        pcm=np.frombuffer(audio.readframes(audio.getnframes()),dtype='<i2').reshape(-1,2).copy()
    items.append((filename,pcm,profile,None))

for number,hz in enumerate((19000,19500,20000,20500,21000),11):
    samples=np.arange(RATE*20)/RATE
    signal=.1*math.sqrt(2)*np.sin(2*np.pi*hz*samples)
    fade=round(RATE*.03)
    ramp=.5-.5*np.cos(np.linspace(0,np.pi,fade))
    signal[:fade]*=ramp;signal[-fade:]*=ramp[::-1]
    pcm=np.column_stack((np.zeros(len(signal)),np.rint(signal*32767))).astype('<i2')
    items.append((f'{number:02d}_TONE_{hz}Hz_level-only.mp3',pcm,None,hz))

report={'purpose':'File/decoder verification only; phone speaker and acoustic range NOT tested',
        'ffmpeg':subprocess.check_output([encoder,'-version'],text=True).splitlines()[0],
        'encoding_options':options,'files':[]}
config=json.loads((ROOT/'array_geometry.json').read_text(encoding='utf-8-sig'))
config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)
rng=np.random.default_rng(4751816)
with tempfile.TemporaryDirectory() as temporary:
    geometry=Path(temporary)/'geometry.json';geometry.write_text(json.dumps(config),encoding='utf-8')
    for filename,pcm,profile,hz in items:
        target=DEST/filename
        source=pcm[RATE:-RATE,1]/32768
        gain=1.;initial_ratio=None
        for attempt in range(3):
            command=[encoder,'-hide_banner','-loglevel','error','-y','-f','s16le',
                     '-ar',str(RATE),'-ac','2','-i','pipe:0','-af',f'volume={gain:.9f}',*options,str(target)]
            subprocess.run(command,input=pcm.tobytes(),check=True,capture_output=True)
            raw=subprocess.check_output([encoder,'-hide_banner','-loglevel','error','-i',str(target),
                                         '-f','f32le','-ar',str(RATE),'-ac','2','pipe:1'])
            decoded=np.frombuffer(raw,dtype='<f4').reshape(-1,2).astype(np.float64)
            steady=decoded[RATE:-RATE,1]
            ratio=20*np.log10(max(np.std(steady),1e-12)/np.std(source))
            if initial_ratio is None:initial_ratio=float(ratio)
            if abs(ratio)<.15:break
            gain*=10**(-ratio/20)
            if gain>2.5:raise RuntimeError(f'Encoder cannot preserve {filename}: {ratio:.2f} dB')
        frequency=np.fft.rfftfreq(len(steady),1/RATE)
        power=np.abs(np.fft.rfft(steady))**2
        low,high=(hz-150,hz+150) if hz else (19000,21000) if profile=='coded-20' else (900,3900)
        fraction=float(power[(frequency>=low)&(frequency<=high)].sum()/power.sum())
        entry={'file':filename,'bytes':target.stat().st_size,
               'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
               'duration_decoded_s':len(decoded)/RATE,'sample_rate':RATE,'channels':2,
               'left_channel_rms':float(np.std(decoded[:,0])),
               'peak_decoded':round(float(np.max(np.abs(decoded))),5),
               'rms_change_db':round(float(ratio),3),'intended_band_energy_fraction':round(fraction,6),
               'encoder_initial_rms_change_db':round(initial_ratio,3),'pre_encoding_gain':round(gain,6),
               'purpose':'coded direction beacon' if profile else 'level only; no direction expected'}
        assert abs(ratio)<.5,entry
        assert fraction>.97,entry
        assert np.max(np.abs(decoded))<.99,entry
        assert np.std(decoded[:,0])<1e-5,entry
        if profile:
            receiver=BeaconEstimator(geometry,profile)
            hits=[]
            for offset in np.linspace(RATE,len(decoded)-RATE-SIZE,16,dtype=int):
                signal=decoded[offset:offset+SIZE,1]
                samples=np.tile((signal*32767)[:,None],(1,7))
                result,_=receiver.estimate(samples,{},offset/RATE)
                hits.append(result.get('code_channels',0))
            entry['code_windows']=len(hits);entry['windows_with_at_least_4_code_hits']=sum(h>=4 for h in hits)
            assert all(h>=4 for h in hits),entry
            # Artificial plane-wave delays applied AFTER actual MP3 decoding.
            # This verifies codec compatibility, not a phone or room model.
            angles=[];f=np.fft.rfftfreq(SIZE,1/RATE)
            for angle in (45,90,270):
                receiver=BeaconEstimator(geometry,profile)
                accepted=[]
                for i in range(6):
                    offset=RATE+i*SIZE+317
                    signal=decoded[offset:offset+SIZE,1]
                    spectrum=np.fft.rfft(signal/max(np.std(signal),1e-9))*120
                    channels=[]
                    for ch in range(7):
                        tau=0 if ch==6 else .04*math.cos(math.radians(angle-ch*60))/343
                        shifted=np.fft.irfft(spectrum*np.exp(2j*np.pi*f*tau),SIZE)
                        channels.append(shifted+rng.normal(0,20,SIZE))
                    result,_=receiver.estimate(np.rint(np.column_stack(channels)).astype('<i2'),{},1+i*.22)
                    if result['valid']:accepted.append(abs((result['raw_angle_deg']-angle+180)%360-180))
                row={'angle':angle,'accepted_windows':len(accepted),'max_error_deg':round(max(accepted),3) if accepted else None}
                assert len(accepted)>=3 and max(accepted)<15,row
                angles.append(row)
            entry['synthetic_decoded_direction_checks']=angles
        else:
            captured=np.tile((decoded[RATE:RATE+SIZE,1]*32767)[:,None],(1,7))
            measured=probe_levels(captured)
            entry['measured_probe_dbfs']=measured[str(hz)]
            expected=20*np.log10(np.std(decoded[RATE:RATE+SIZE,1]))
            assert abs(measured[str(hz)]-expected)<.5,entry
            receiver=BeaconEstimator(geometry,'coded-20')
            result,_=receiver.estimate(captured,{},1)
            assert not result['valid'],entry
            entry['plain_tone_not_accepted_as_direction']=True
        report['files'].append(entry)
report['passed']=True
(STAGE/'mp3-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
