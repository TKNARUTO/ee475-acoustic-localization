"""Visualize the original digital beacon without changing its audio file."""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
import importlib.util
if importlib.util.find_spec('PIL') is None:sys.path.append(str(Path(sys.base_prefix)/'Lib/site-packages'))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import imageio_ffmpeg

PROJECT=Path(__file__).resolve().parents[1]
source=PROJECT/'audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3'
out=PROJECT/'reports/RX4-2026-10-29/figures';out.mkdir(parents=True,exist_ok=True)
decoded=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(source),'-f','f32le','-ac','2','-ar','48000','pipe:1'],capture_output=True,check=True)
audio=np.frombuffer(decoded.stdout,dtype='<f4').reshape(-1,2)
channel=int(np.argmax(np.mean(audio.astype(float)**2,axis=0)));x=audio[:,channel].astype(float);rate=48000
fig,axes=plt.subplots(3,1,figsize=(11,9),constrained_layout=True)
size=480;usable=len(x)//size;blocks=x[:usable*size].reshape(-1,size)
t=(np.arange(usable)+.5)*size/rate
axes[0].fill_between(t,blocks.min(axis=1),blocks.max(axis=1),color='#247c9e',alpha=.85)
axes[0].set(xlabel='Time (s)',ylabel='Digital amplitude (full scale = 1)',ylim=(-.45,.45),
    title=f'Original LOCATE beacon | 19–21 kHz | decoded duration {len(x)/rate:.3f} s')
axes[0].grid(alpha=.2)
start=rate;period=x[start:start+4096]
up=np.fft.irfft(np.fft.rfft(period),4096*8)*8
begin=960;length=96
axes[1].plot(np.arange(length*8)/(rate*8)*1000,up[begin*8:(begin+length)*8],color='#156c91',lw=1,label='Band-limited interpolation for display')
axes[1].scatter(np.arange(length)/rate*1000,period[begin:begin+length],s=9,color='#d47b27',label='Actual 48 kHz decoded samples')
axes[1].set(xlabel='Time within a 2 ms excerpt (ms)',ylabel='Digital amplitude',title='Zoom: rapidly oscillating coded waveform, not a single fixed sine wave')
axes[1].grid(alpha=.2);axes[1].legend(fontsize=8,loc='upper right')
clip=x[rate:2*rate];window=np.hanning(1024);hop=128
frames=np.array([clip[i:i+1024]*window for i in range(0,len(clip)-1024+1,hop)])
power=np.abs(np.fft.rfft(frames,axis=1))**2
relative=10*np.log10(np.maximum(power/power.max(),1e-12))
freq=np.fft.rfftfreq(1024,1/rate);take=(freq>=17500)&(freq<=22500)
im=axes[2].pcolormesh((np.arange(len(frames))*hop+512)/rate,freq[take]/1000,relative[:,take].T,shading='auto',vmin=-65,vmax=0,cmap='magma')
axes[2].axhline(19,color='cyan',lw=.6,ls='--');axes[2].axhline(21,color='cyan',lw=.6,ls='--')
axes[2].set(xlabel='Time within a 1 s excerpt (s)',ylabel='Frequency (kHz)',title='Spectrogram: energy occupies a coded 19–21 kHz band, rather than sweeping up and down')
fig.colorbar(im,ax=axes[2],label='Power relative to excerpt peak (dB)')
path=out/'original-beacon-waveform.png';fig.savefig(path,dpi=170);plt.close(fig)
metadata={'source_file':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'decoded_sample_rate':rate,
    'decoded_duration_s':len(x)/rate,'plotted_channel':'right' if channel else 'left','source_modified':False,
    'description':'Decoded digital source waveform, not a microphone recording. Zoom interpolation adds no measured samples. Spectrogram power is relative to its own peak.'}
(out/'original-beacon-waveform.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print(json.dumps({'image':str(path),'duration_s':len(x)/rate,'source_modified':False}))
