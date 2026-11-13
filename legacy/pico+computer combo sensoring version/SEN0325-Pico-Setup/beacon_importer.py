"""Validate and persist a local reference for the periodic-code receiver."""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import shutil
import numpy as np

RATE=48000
SIZE=4096

def load_active(root):
    root=Path(root)
    try:
        data=json.loads((root/'beacon_profiles/active.json').read_text(encoding='utf-8'))
        token=data['profile'].removeprefix('imported-')
        if len(token)!=16 or any(ch not in '0123456789abcdef' for ch in token):return None
        path=root/'beacon_profiles'/token/'period.npy'
        samples=np.load(path,allow_pickle=False)
        spec=data['spec']
        if spec.get('template_token')!=token:return None
        if samples.shape!=(SIZE,) or not np.isfinite(samples).all():return None
        if not 300<=spec['low']<spec['high']<=22000 or spec['high']-spec['low']<1000:return None
        if hashlib.sha256(path.read_bytes()).hexdigest()!=data['template_sha256']:return None
        return data
    except (OSError,ValueError,KeyError,TypeError):return None

def import_reference(path,root):
    path=Path(path);root=Path(root)
    if path.suffix.lower() not in ('.mp3','.wav'):raise ValueError('Choose an MP3 or WAV file.')
    if not path.is_file() or path.stat().st_size>100*1024*1024:raise ValueError('Choose a local audio file smaller than 100 MB.')
    source_digest=hashlib.sha256(path.read_bytes()).hexdigest()
    # The bundled burst has windowing sidebands outside its intended band.
    # Recognize its exact WAV/MP3 bytes as the existing builtin profile rather
    # than weakening the continuous-code importer for arbitrary customer files.
    project=Path(__file__).resolve().parent.parent
    phone_folder=project/'audio/phone/HF2-gap-test'
    for filename in ('01_LOCATE_18-22kHz_43ms-gap.wav','01_LOCATE_18-22kHz_43ms-gap.mp3'):
        canonical=phone_folder/filename
        if canonical.is_file() and hashlib.sha256(canonical.read_bytes()).hexdigest()==source_digest:
            from beacon_dsp import PROFILES
            return {'profile':'coded-gap','spec':dict(PROFILES['coded-gap']),
                    'source_name':path.name,'source_sha256':source_digest,
                    'builtin_reference':True,'canonical_source':canonical.relative_to(project).as_posix(),
                    'reference_frames':SIZE,'sample_rate':RATE,'selected_channel':'right',
                    'limitation':'Exact bundled gap reference selected; no arbitrary import checks were relaxed.'}
    import imageio_ffmpeg
    decoder=imageio_ffmpeg.get_ffmpeg_exe()
    result=subprocess.run([decoder,'-hide_banner','-loglevel','error','-i',str(path),'-t','12',
                           '-f','f32le','-ar',str(RATE),'-ac','2','pipe:1'],capture_output=True,
                          timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise ValueError('Cannot decode this audio file. Try the lossless WAV reference.')
    audio=np.frombuffer(result.stdout,dtype='<f4')
    if len(audio)%2:raise ValueError('Unexpected decoded audio format.')
    audio=audio.reshape(-1,2).astype(np.float64)
    if len(audio)<RATE:raise ValueError('Use a beacon file lasting at least 1 second.')
    channel=int(np.argmax(np.std(audio,axis=0)))
    signal=audio[:,channel];signal-=signal.mean()
    if np.std(signal)<1e-6:raise ValueError('The selected file is silent.')
    trimmed=signal[RATE//5:]
    count=min(64,len(trimmed)//SIZE-1)
    blocks=np.array([trimmed[i*SIZE:(i+1)*SIZE] for i in range(count+1)])
    spectrum_power=np.mean(np.abs(np.fft.rfft(blocks*np.hanning(SIZE)[None,:],axis=1))**2,axis=0)
    frequencies=np.fft.rfftfreq(SIZE,1/RATE)
    spectrum_power[frequencies<300]=0
    cumulative=np.cumsum(spectrum_power)/max(spectrum_power.sum(),1e-18)
    low_bin=int(np.searchsorted(cumulative,.001));high_bin=int(np.searchsorted(cumulative,.999))
    occupied=float(frequencies[min(high_bin,len(frequencies)-1)]-frequencies[low_bin])
    if occupied<1000:
        raise ValueError('This is too narrow for reliable direction. Pure tones appear in the spectrum, but need a wide coded beacon for localization.')
    low=max(300,int(math.floor(frequencies[low_bin]/250)*250))
    high=min(22000,int(math.ceil(frequencies[min(high_bin,len(frequencies)-1)]/250)*250))
    if frequencies[min(high_bin,len(frequencies)-1)]>22000:
        raise ValueError('The usable reference must stay below 22 kHz for this 48 kHz receiver.')
    correlations=np.sum(blocks[:-1]*blocks[1:],axis=1)/np.maximum(np.linalg.norm(blocks[:-1],axis=1)*np.linalg.norm(blocks[1:],axis=1),1e-18)
    periodicity=float(np.median(correlations))
    if periodicity<.95:
        raise ValueError('This file does not repeat every 4096 samples (85.333 ms at 48 kHz). The current receiver supports periodic coded beacons. Keep the existing reference or use a compatible coded file; arbitrary music/voice/chirps need a different detector.')
    period=np.mean(blocks,axis=0)
    period-=period.mean();period*=.35/max(np.max(np.abs(period)),1e-12)
    mask=(frequencies>=low)&(frequencies<=high)
    # Store only the measured occupied band; no speaker playback or source edit.
    spectrum=np.fft.rfft(period);spectrum[~mask]=0
    period=np.fft.irfft(spectrum,SIZE)
    token=source_digest[:16]
    folder=root/'beacon_profiles'/token;folder.mkdir(parents=True,exist_ok=True)
    template_file=folder/'period.npy';np.save(template_file,period,allow_pickle=False)
    stored_source=folder/path.name
    if stored_source.resolve()!=path.resolve():shutil.copy2(path,stored_source)
    profile='imported-'+token
    spec={'label':'Imported beacon','low':low,'high':high,'center':round((low+high)/2),
          'template_token':token,'source_name':path.name}
    data={'profile':profile,'spec':spec,'source_name':path.name,'source_sha256':source_digest,
          'stored_source':stored_source.relative_to(root).as_posix(),
          'selected_channel':'right' if channel==1 else 'left','periodicity':round(periodicity,6),
          'reference_frames':SIZE,'sample_rate':RATE,'template_sha256':hashlib.sha256(template_file.read_bytes()).hexdigest(),
          'limitation':'Periodic known-code reference only; no source playback or absolute angular calibration.'}
    text=json.dumps(data,ensure_ascii=False,indent=2)
    (folder/'manifest.json').write_text(text,encoding='utf-8')
    temporary=root/'beacon_profiles/active.tmp'
    temporary.write_text(text,encoding='utf-8');temporary.replace(root/'beacon_profiles/active.json')
    from beacon_dsp import PROFILES
    PROFILES[profile]=spec
    return data
