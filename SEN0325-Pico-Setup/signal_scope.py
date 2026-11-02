"""Actual microphone spectrum and sampled waveform; independent of code hits."""
import math
import tkinter as tk
from tkinter import ttk
import numpy as np

CHANNELS=('D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER')

def signal_payload(samples,sequence,now):
    raw=np.asarray(samples,dtype=np.float64)
    centered=raw-raw.mean(axis=0)
    n=len(raw);window=np.hanning(n)
    spectra=np.fft.rfft(centered*window[:,None],axis=0)
    power=2*np.mean(np.abs(spectra)**2,axis=1)/(n*np.sum(window**2))
    power[0]*=.5;power[-1]*=.5
    dbfs=10*np.log10(np.maximum(power,1e-18)/(32768**2))
    frequencies=np.fft.rfftfreq(n,1/48000)
    # Preserve narrow spectral peaks when reducing the display payload.
    bins=np.array_split(np.arange(len(power)),320)
    selected=np.array([b[np.argmax(power[b])] for b in bins])
    channel=int(np.argmax(np.std(centered,axis=0)))
    waveform=centered[:256,channel]
    peak=int(np.argmax(power[1:])+1)
    return {'sequence':sequence,'received_at':now,'sample_rate_hz':48000,'fft_frames':n,
            'frequency_hz':np.round(frequencies[selected],2).tolist(),
            'spectrum_dbfs_bin':np.round(dbfs[selected],2).tolist(),
            'peak_frequency_hz':round(float(frequencies[peak]),1),
            'waveform16':np.round(waveform,1).tolist(),'waveform_channel':CHANNELS[channel],
            'waveform_peak16':round(float(np.max(np.abs(waveform))),1),
            'spectrum_definition':'Hann-window power, mean across 7 channels, dBFS per FFT bin',
            'waveform_definition':'DC-removed PCM16, strongest-RMS channel, first 256 samples'}

class SignalScope(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.payload=None;self.running=False;self.fresh=False
        self.target_band=(19000,21000)
        ttk.Label(self,text='Microphone Signal | All captured sound',foreground='#7ed7cc').pack(anchor='w',pady=(6,3))
        self.spectrum=tk.Canvas(self,height=160,background='#071722',highlightthickness=0)
        self.spectrum.pack(fill='x')
        self.waveform=tk.Canvas(self,height=65,background='#071722',highlightthickness=0)
        self.waveform.pack(fill='x',pady=(4,0))
        self.spectrum.bind('<Configure>',lambda event:self.draw())

    def update_signal(self,payload):
        self.payload=payload

    def draw(self,running=None,fresh=None):
        if running is not None:self.running=running
        if fresh is not None:self.fresh=fresh
        canvas=self.spectrum;canvas.delete('all')
        width=max(canvas.winfo_width(),280);height=160
        left,top,right,bottom=38,20,width-12,height-22
        def fx(hz):return left+(right-left)*hz/24000
        def fy(level):return bottom-(max(-120,min(0,level))+120)/120*(bottom-top)
        low,high=self.target_band
        canvas.create_rectangle(fx(low),top,fx(high),bottom,fill='#173c48',outline='')
        for level in (-120,-90,-60,-30,0):
            y=fy(level);canvas.create_line(left,y,right,y,fill='#193744')
            canvas.create_text(left-4,y,text=str(level),anchor='e',fill='#789aa5',font=('Segoe UI',7))
        for hz in (0,6000,12000,18000,24000):
            canvas.create_text(fx(hz),bottom+10,text=str(hz//1000),fill='#97b8c4',font=('Segoe UI',8))
        canvas.create_text(left,9,text='Spectrum | dBFS/bin',anchor='w',fill='#97b8c4',font=('Segoe UI',8))
        canvas.create_text(right,9,text=f'kHz | {low/1000:g}-{high/1000:g} shaded',anchor='e',fill='#97b8c4',font=('Segoe UI',8))
        data=self.payload if self.running and self.fresh else None
        if data:
            points=[]
            for hz,level in zip(data['frequency_hz'],data['spectrum_dbfs_bin']):points.extend((fx(hz),fy(level)))
            canvas.create_line(*points,fill='#42e3b3',width=1.4,tags='spectrum_trace')
        else:
            canvas.create_text((left+right)/2,(top+bottom)/2,text='Waiting for capture' if self.running else 'Scan stopped',fill='#789aa5')
        wave=self.waveform;wave.delete('all');w=max(wave.winfo_width(),280)
        wave.create_line(8,39,w-8,39,fill='#31505d')
        if data:
            peak=max(float(data['waveform_peak16']),1)
            points=[];values=data['waveform16']
            for i,value in enumerate(values):points.extend((8+(w-16)*i/(len(values)-1),39-value/peak*21))
            wave.create_line(*points,fill='#57b6ec',width=1,tags='waveform_trace')
            label=f"Waveform | {data['waveform_channel']} | 5.33 ms | +/-{peak:.0f} PCM"
        else:label='Waveform | sampled microphone audio'
        wave.create_text(8,8,text=label,anchor='w',fill='#97b8c4',font=('Segoe UI',8))
