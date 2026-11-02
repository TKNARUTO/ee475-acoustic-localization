"""Receiver-only radar UI. Beacon files are played externally on the phone."""
from datetime import datetime
from collections import deque
import ctypes
import json
import math
import os
import queue
from statistics import median
import time
import tkinter as tk
from tkinter import ttk
from app_controls import ScanControls,PROFILES
from radar_canvas import RadarCanvas,DirectionState
from sen0325_view import Levels,db,COLORS
from runtime_tuning import UI_REFRESH_MS,DETAIL_REFRESH_SECONDS,DISPLAY_TRANSITION_SECONDS


class SimpleView:
    def __init__(self,Session,root,channels,auto_close=None,initial_profile='coded-audible'):
        self.root=root
        self.channels=channels
        self.auto_close=auto_close
        self.session=Session()
        self.controls=ScanControls(self.session)
        self.controls.select_profile(initial_profile)
        self.levels=Levels(channels)
        self.tones={};self.tone_times={};self.info={}
        self.direction=DirectionState(transition_seconds=DISPLAY_TRANSITION_SECONDS)
        self.detection_intervals=deque(maxlen=20)
        self.last_detection_time=None
        self.render_intervals=deque(maxlen=120)
        self.last_refresh_time=0
        self.last_detail_refresh=0
        self.last_chart_refresh=0
        self.last_frame=0;self.closing=False;self.range_check=None
        self.callback_errors=[];self.checks={}
        self.window=tk.Tk()
        self.window.title('EE475 | Acoustic Localizer')
        self.window.geometry('1180x780')
        self.window.minsize(1100,760)
        self.window.configure(background='#0d1b2a')
        style=ttk.Style(self.window);style.theme_use('clam')
        style.configure('TFrame',background='#0d1b2a')
        style.configure('TLabel',background='#0d1b2a',foreground='#c6d9e6',font=('Segoe UI',10))
        style.configure('TButton',background='#213b50',foreground='#e5f1f8',font=('Segoe UI',10),padding=7)
        style.map('TButton',background=[('active','#31566f')])
        style.configure('TCheckbutton',background='#0d1b2a',foreground='#c6d9e6',font=('Segoe UI',10))
        style.map('TCheckbutton',background=[('active','#0d1b2a')])
        style.configure('TLabelframe',background='#0d1b2a',bordercolor='#31566f')
        style.configure('TLabelframe.Label',background='#0d1b2a',foreground='#7ed7cc',font=('Segoe UI',10))
        self.pane=ttk.Frame(self.window,padding=16);self.pane.pack(fill='both',expand=True)
        ttk.Label(self.pane,text='Acoustic Localizer',font=('Segoe UI',20,'bold')).pack(anchor='w')
        self.connection=tk.StringVar(value='Connecting to Pico...')
        ttk.Label(self.pane,textvariable=self.connection,wraplength=1020).pack(anchor='w',pady=(3,12))
        self.main_controls=ttk.Frame(self.pane);self.main_controls.pack(fill='x',pady=(0,10))
        self.radar_button=ttk.Button(self.main_controls,text='Start Scan',command=self.toggle_radar)
        self.radar_button.pack(side='left')
        ttk.Button(self.main_controls,text='Set Front',command=self.set_front).pack(side='left',padx=8)
        ttk.Button(self.main_controls,text='Advanced',command=self.show_advanced).pack(side='right')
        self.radar_state=tk.StringVar(value='Scan: OFF')
        ttk.Label(self.main_controls,textvariable=self.radar_state,foreground='#7ed7cc').pack(side='left',padx=10)
        self.receiver_panel=ttk.LabelFrame(self.pane,text='Receiver | Play the matching file on your phone',padding=9)
        self.receiver_panel.pack(fill='x',pady=(0,10))
        self.audio_name=tk.StringVar(value=next(name for name,profile in PROFILES.items() if profile==initial_profile))
        self.audio_menu=ttk.Combobox(self.receiver_panel,textvariable=self.audio_name,values=tuple(PROFILES),state='readonly',width=30)
        self.audio_menu.pack(side='left',padx=(0,8));self.audio_menu.bind('<<ComboboxSelected>>',self.change_audio)
        ttk.Label(self.receiver_panel,text='Receive only. No computer playback.').pack(side='left',padx=8)
        body=ttk.Frame(self.pane);body.pack(fill='both',expand=True)
        self.radar=RadarCanvas(body,width=640,height=420);self.radar.pack(side='left',fill='both',expand=True)
        readout=ttk.Frame(body,padding=(18,25,0,0));readout.pack(side='right',fill='y')
        self.bearing=tk.StringVar(value='—°')
        ttk.Label(readout,text='Estimated bearing',font=('Segoe UI',11)).pack(anchor='w')
        ttk.Label(readout,textvariable=self.bearing,font=('Segoe UI',36,'bold'),foreground='#42e3b3').pack(anchor='w',pady=(3,8))
        self.quality=tk.StringVar(value='Ready to start scan')
        ttk.Label(readout,textvariable=self.quality,wraplength=270).pack(anchor='w',pady=(0,8))
        self.signal=tk.StringVar(value='Code: --')
        ttk.Label(readout,textvariable=self.signal).pack(anchor='w')
        self.band_level=tk.StringVar(value='Band level: -- dBFS')
        ttk.Label(readout,textvariable=self.band_level,foreground='#7ed7cc',wraplength=270).pack(anchor='w',pady=(5,0))
        self.probe_level=tk.StringVar(value='Tone levels (dBFS): --')
        ttk.Label(readout,textvariable=self.probe_level,foreground='#789aa5',wraplength=270).pack(anchor='w',pady=(7,0))
        self.update_rate=tk.StringVar(value='Detection rate: --')
        ttk.Label(readout,textvariable=self.update_rate,foreground='#789aa5').pack(anchor='w',pady=(6,0))
        self.heading=tk.StringVar(value='Front reference saved' if self.session.direction_estimator.config['heading_calibrated'] else 'Front reference: not set')
        ttk.Label(readout,textvariable=self.heading,foreground='#7ed7cc',wraplength=240).pack(anchor='w',pady=(16,0))
        self.help=tk.StringVar(value='Loop 01_LOCATE_16-18kHz.mp3 on your phone, then select Start Scan.' if initial_profile=='coded-16-18' else 'Loop 02_LOCATE_Audible.mp3 on your phone, then select Start Scan.')
        ttk.Label(self.pane,textvariable=self.help,wraplength=1020,foreground='#7ed7cc').pack(anchor='w',pady=(8,3))
        ttk.Label(self.pane,text='Bearing only: rings do not show distance. High-frequency localization is experimental.',foreground='#789aa5',font=('Segoe UI',9)).pack(anchor='w')
        self.build_advanced()
        self.window.report_callback_exception=self.callback_error
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.session.start()
        self.window.after(100,self.refresh)
        if auto_close:
            self.window.after(1000,self.smoke_idle)
            self.window.after(int(auto_close*1000),self.close)

    def callback_error(self,error_type,error,tb):
        import traceback
        detail=''.join(traceback.format_exception(error_type,error,tb))
        self.callback_errors.append(detail)
        (self.root/'logs/simple-ui-error.txt').write_text(detail,encoding='utf-8')
        self.help.set('Operation failed. See logs/simple-ui-error.txt.')

    def sync_switches(self):
        self.radar_button.configure(text='Stop Scan' if self.controls.running else 'Start Scan')
        self.radar_state.set('Scan: ON' if self.controls.running else 'Scan: OFF')

    def toggle_radar(self):
        self.finish_range(cancelled=True)
        self.controls.toggle_scan()
        self.detection_intervals.clear();self.last_detection_time=None
        self.direction.update({'valid':False},time.monotonic())
        self.sync_switches()
        self.help.set('Scanning. Play the matching LOCATE file on your phone. TONE files update levels only.' if self.controls.running else 'Scan stopped. Start and stop playback on your phone.')

    def change_audio(self,event=None):
        self.finish_range(cancelled=True)
        self.controls.select_profile(PROFILES[self.audio_name.get()])
        self.detection_intervals.clear();self.last_detection_time=None
        self.tones.clear();self.tone_times.clear();self.info.clear()
        self.levels.power.clear();self.levels.history.clear()
        self.direction.update({'valid':False},time.monotonic())
        self.sync_switches()
        self.help.set('16-18 kHz selected: phone file 01_LOCATE_16-18kHz.mp3. TONE files measure level, not direction.' if self.controls.profile=='coded-16-18' else 'Audible selected: phone file 02_LOCATE_Audible.mp3.')

    def open_audio_folder(self):
        folder=self.root.parent/'audio'/'phone'/'HF1-MP3'
        os.startfile(folder if folder.exists() else self.root/'beacon-audio')

    def set_front(self):
        try:self.session.set_front()
        except ValueError:
            self.help.set('Start scan and play the beacon. Set Front after a stable bearing appears.');return
        self.heading.set('Front reference: saved')
        self.direction.update({'valid':False},time.monotonic())
        self.help.set('Current source saved as front. Keep the array fixed and move the phone to check left and right.')

    def build_advanced(self):
        self.advanced=tk.Toplevel(self.window);self.advanced.title('Acoustic Localizer | Advanced')
        self.advanced.configure(background='#0d1b2a');self.advanced.geometry('610x620')
        self.advanced.protocol('WM_DELETE_WINDOW',self.advanced.withdraw)
        pane=ttk.Frame(self.advanced,padding=15);pane.pack(fill='both',expand=True)
        row=ttk.Frame(pane);row.pack(fill='x')
        ttk.Button(row,text='Reconnect Pico',command=self.reconnect).pack(side='left')
        ttk.Button(row,text='Signal History',command=self.show_chart).pack(side='left',padx=8)
        ttk.Button(row,text='Phone Audio Files',command=self.open_audio_folder).pack(side='left')
        self.mirror=tk.BooleanVar(value=self.session.direction_estimator.config['mirror_view'])
        ttk.Checkbutton(pane,text='Mirror view (set front again after changing)',variable=self.mirror,command=self.change_mirror).pack(anchor='w',pady=12)
        record=ttk.LabelFrame(pane,text='Distance-Tagged Trial',padding=9);record.pack(fill='x',pady=(0,14))
        ttk.Label(record,text='Measured distance (m)').pack(side='left')
        self.distance=tk.StringVar(value='1.0')
        ttk.Entry(record,textvariable=self.distance,width=6).pack(side='left',padx=7)
        ttk.Button(record,text='Record 10 s',command=self.start_range).pack(side='left')
        ttk.Label(pane,text='Live Signals | Seven Channels',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,7))
        table=ttk.Frame(pane);table.pack(fill='x')
        for col,name in enumerate(('Channel','Target RMS','Code PNR','Hit')):
            ttk.Label(table,text=name).grid(row=0,column=col,sticky='w',padx=8,pady=5)
        self.channel_values={}
        for row,name in enumerate(self.channels,1):
            ttk.Label(table,text=name.replace('D3R_CENTER','D3R Center'),foreground=COLORS[row-1]).grid(row=row,column=0,sticky='w',padx=8,pady=6)
            values=[tk.StringVar(value='—') for _ in range(3)]
            for col,value in enumerate(values,1):ttk.Label(table,textvariable=value,width=11).grid(row=row,column=col,sticky='e',padx=8,pady=6)
            self.channel_values[name]=values
        self.counters=tk.StringVar(value='Waiting for capture')
        ttk.Label(pane,textvariable=self.counters,wraplength=550).pack(anchor='w',pady=(15,7))
        ttk.Label(pane,text='Distance is a manually entered trial label. Detailed records are saved in the application logs folder.',wraplength=550).pack(anchor='w')
        self.advanced.withdraw()
        self.chart_window=tk.Toplevel(self.window);self.chart_window.title('Acoustic Localizer | Signal History')
        self.chart_window.configure(background='#0d1b2a');self.chart_window.geometry('840x310')
        ttk.Label(self.chart_window,text='Last 12 seconds | Target-band energy | Colors identify channels').pack(anchor='w',padx=12,pady=8)
        self.chart=tk.Canvas(self.chart_window,background='#071722',highlightthickness=0)
        self.chart.pack(fill='both',expand=True,padx=12,pady=(0,12))
        self.chart_window.protocol('WM_DELETE_WINDOW',self.chart_window.withdraw);self.chart_window.withdraw()

    def show_advanced(self):self.advanced.deiconify();self.advanced.lift()
    def show_chart(self):self.chart_window.deiconify();self.chart_window.lift()
    def reconnect(self):
        self.session.reconnect.set()
        self.help.set('Reconnecting. Scan switch state is preserved.')
    def change_mirror(self):
        self.session.set_mirror(self.mirror.get())
        self.direction.update({'valid':False},time.monotonic())
        self.heading.set('View changed: set front again')

    def start_range(self):
        if not self.controls.running or time.monotonic()-self.last_frame>1.5:
            self.help.set('Start scan and wait for capture before recording a trial.');return False
        try:
            distance=float(self.distance.get())
            if not math.isfinite(distance) or not 0<distance<=100:raise ValueError()
        except ValueError:
            self.help.set('Enter the measured distance, such as 0.5, 1 or 1.5 m.');return False
        self.finish_range(cancelled=True)
        self.range_check={'start':time.monotonic(),'distance':distance,'profile':self.controls.profile,'events':[]}
        self.help.set('Recording for 10 seconds. Keep playback, phone position and array orientation fixed.')
        return True

    def finish_range(self,cancelled=False):
        if self.range_check is None:return
        test=self.range_check;rows=test['events'];valid=[r for r in rows if r['valid']]
        report={'time':datetime.now().astimezone().isoformat(),'profile':test['profile'],
            'distance_m_user_entered':test['distance'],'cancelled':cancelled,'windows':len(rows),'valid_windows':len(valid),
            'valid_fraction':round(len(valid)/len(rows),3) if rows else 0,
            'code_hit_fraction':round(sum(r.get('code_channels',0)>=4 for r in rows)/len(rows),3) if rows else 0,
            'median_code_pnr_db':median(r.get('code_pnr_db',0) for r in rows) if rows else None,
            'events':rows,'raw_log':str(self.session.log_path),
            'limitation':'Distance entered by user; no ground-truth angle. Stability is not angular accuracy.'}
        name='range-test-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json'
        (self.root/'logs'/name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        self.range_check=None
        if not cancelled:self.help.set(f'Trial saved: {len(valid)}/{len(rows)} windows have valid bearings. See logs/{name}.')

    def refresh(self):
        if self.closing:return
        now=time.monotonic()
        if self.last_refresh_time and 0<now-self.last_refresh_time<.5:self.render_intervals.append(now-self.last_refresh_time)
        self.last_refresh_time=now
        for _ in range(200):
            try:kind,value=self.session.events.get_nowait()
            except queue.Empty:break
            if kind=='status':self.connection.set(value.replace('Paused; microphone clocks stopped','Connected; ready to start scan'))
            elif kind=='direction':
                if not self.controls.running:
                    self.direction.update({'valid':False},now)
                    continue
                self.info=value;self.direction.update(value,now)
                if value.get('method','').startswith('coded_matched_filter_'):
                    received=value['received_at']
                    if self.last_detection_time is not None and 0<received-self.last_detection_time<1.2:
                        self.detection_intervals.append(received-self.last_detection_time)
                    self.last_detection_time=received
                if self.range_check and value.get('profile')==self.range_check['profile']:self.range_check['events'].append(dict(value))
            elif kind=='frame':
                self.last_frame=now
                self.counters.set(f'48 kHz | {value.get("frames",0)} frames/burst | Drops {value.get("dropped",0)} | RX stalls {value.get("rx_stall",0)}')
            elif kind=='tone':
                name,data=value
                self.tones[name]=data;self.tone_times[name]=now
                if data['frequency']==self.session.frequency:self.levels.update(name,data['rms'],now)
        hits=0
        update_details=now-self.last_detail_refresh>=DETAIL_REFRESH_SECONDS
        if update_details:self.last_detail_refresh=now
        for name in self.channels:
            values=self.channel_values[name];data=self.tones.get(name)
            fresh=self.controls.running and data and data['frequency']==self.session.frequency and now-self.tone_times.get(name,0)<1.5
            if fresh:
                if update_details:
                    values[0].set(f'{data["rms"]:.1f}');values[1].set(f'{data["snr_db"]:.1f} dB');values[2].set('Hit' if data['present'] else '—')
                hits+=data['present']
            elif update_details:
                for value in values:value.set('—')
        angle,quality=self.direction.current(now) if self.controls.running else (None,None)
        reasons={'beacon_not_detected':'Waiting for selected beacon','ambiguous_beacon_direction':'Beacon detected; ambiguous bearing',
            'group_delay_inconsistent':'Beacon detected; inconsistent delay','confirming_beacon_direction':'Beacon detected; confirming bearing',
            'capture_gap':'Capture interrupted; recovering','clipping':'Input clipping; reduce volume'}
        message='Radar stopped' if not self.controls.running else 'Waiting for Pico capture' if now-self.last_frame>1.5 else reasons.get(self.info.get('reason'),'Waiting for valid bearing')
        self.radar.render(angle,quality,False,message)
        self.bearing.set(f'{angle:.1f}°' if angle is not None else '—°')
        self.quality.set(f'Quality score {quality:.0%}' if quality is not None else message)
        self.signal.set(f'Code: {hits}/7 channels matched' if self.controls.running else 'Code: capture stopped')
        band_fresh=self.controls.running and self.info.get('profile')=='coded-16-18' and now-self.info.get('received_at',0)<1.5
        self.band_level.set(f'16-18 kHz level: {self.info["band_level_dbfs"]:.1f} dBFS' if band_fresh and 'band_level_dbfs' in self.info else 'Band level: -- dBFS')
        probe=self.info.get('probe_bands_dbfs',{}) if self.controls.running and now-self.info.get('received_at',0)<1.5 else {}
        self.probe_level.set('Tone levels (dBFS, +/-150 Hz)\n'+'\n'.join(f'{hz/1000:g} kHz: {probe.get(str(hz),"--")}' for hz in (1000,16000,17000,17500,18000)) if probe else 'Tone levels (dBFS): --')
        self.update_rate.set(f'Detection rate: {1/median(self.detection_intervals):.1f} Hz' if self.controls.running and self.detection_intervals and now-self.last_frame<1.5 else 'Detection rate: --')
        if self.range_check and now-self.range_check['start']>=10:self.finish_range()
        self.draw_chart(now)
        self.window.after(UI_REFRESH_MS,self.refresh)

    def draw_chart(self,now):
        if self.chart_window.state()!='normal':return
        if now-self.last_chart_refresh<DETAIL_REFRESH_SECONDS:return
        self.last_chart_refresh=now
        chart=self.chart;chart.delete('all');width,height=chart.winfo_width(),chart.winfo_height()
        left,top,right,bottom=42,12,max(100,width-12),height-22
        for value in (-90,-60,-30,0):
            y=bottom-(value+90)/90*(bottom-top)
            chart.create_line(left,y,right,y,fill='#19434b');chart.create_text(left-6,y,text=str(value),anchor='e',fill='#97b8c4')
        for i,name in enumerate(self.channels):
            points=[]
            for timestamp,values in self.levels.history:
                if now-12<=timestamp<=now and name in values:
                    points.extend((right-(now-timestamp)/12*(right-left),bottom-(max(-90,values[name])+90)/90*(bottom-top)))
            if len(points)>=4:chart.create_line(*points,fill=COLORS[i],width=2)

    def smoke_idle(self):
        self.checks['startup_scan_off']=not self.controls.running and self.session.frames==0
        self.checks['no_playback_controller']=not hasattr(self,'player') and not hasattr(self,'toggle_playback')
        self.checks['advanced_hidden_by_default']=self.advanced.state()=='withdrawn'
        self.toggle_radar()
        self.checks['scan_starts']=self.controls.running
        self.window.after(2000,self.smoke_capture)

    def smoke_capture(self):
        self.checks['real_pico_coded_capture']=self.session.raw_bursts>=2 and len(self.session.last_tones)==7
        self.checks['probe_levels_received']=len(self.info.get('probe_bands_dbfs',{}))==5
        self.toggle_radar()
        self.checks['scan_stops']=not self.controls.running
        self.window.after(750,self.smoke_stopped)

    def smoke_stopped(self):
        self.checks['stopped_scan_has_no_arrow']=not any(self.radar.type(item)=='line' for item in self.radar.find_withtag('target'))
        self.toggle_radar()
        self.audio_name.set('16-18 kHz beacon (Stage 1)');self.change_audio()
        self.checks['receiver_choice_preserves_scan_state']=self.controls.running
        self.window.after(1800,self.smoke_high_frequency)

    def smoke_high_frequency(self):
        self.checks['high_frequency_receiver_configured']=self.session.mode=='coded-16-18' and len(self.session.last_tones)==7 and all(r['frequency']==17000 for r in self.session.last_tones.values())
        self.audio_name.set('Audible beacon');self.change_audio()
        self.window.after(1800,self.smoke_details)

    def smoke_details(self):
        self.checks['audible_receiver_configured']=self.session.mode=='coded-audible' and all(r['frequency']==2400 for r in self.session.last_tones.values())
        self.show_advanced();self.show_chart();self.window.update_idletasks()
        self.checks['advanced_opens']=self.advanced.state()=='normal' and len(self.channel_values)==7
        self.checks['curve_opens']=self.chart_window.state()=='normal'
        self.advanced.withdraw();self.chart_window.withdraw()
        self.distance.set('invalid')
        self.checks['bad_distance_rejected']=not self.start_range() and self.range_check is None
        self.distance.set('1.0')
        self.checks['two_receiver_choices']=len(self.audio_menu['values'])==2

    def close(self):
        if self.closing:return
        self.closing=True;self.finish_range(cancelled=True);self.controls.close();self.sync_switches()
        self.connection.set('Stopping capture and releasing serial port...')
        for frame in (self.main_controls,self.receiver_panel):
            for child in frame.winfo_children():
                if 'state' in child.keys():child.configure(state='disabled')
        self.await_close()

    def await_close(self):
        if self.session.thread.is_alive():self.window.after(100,self.await_close);return
        if self.auto_close:
            self.window.update_idletasks()
            count=sum(isinstance(w,ttk.Button) for frame in (self.main_controls,self.receiver_panel) for w in frame.winfo_children())
            report={'title':self.window.title(),'frames':self.session.frames,'raw_bursts':self.session.raw_bursts,
                'channels':sorted(self.session.seen),'main_button_count':count,'checks':self.checks,
                'content_height':self.pane.winfo_reqheight(),'available_height':self.pane.winfo_height(),
                'content_width':self.pane.winfo_reqwidth(),'available_width':self.pane.winfo_width(),
                'callback_errors':self.callback_errors,'audio_output':'not implemented; receive only',
                'raw_log':str(self.session.log_path)}
            report['observed_ui_refresh_hz']=round(1/median(self.render_intervals),2) if self.render_intervals else None
            report['observed_detection_hz']=round(1/median(self.detection_intervals),2) if self.detection_intervals else None
            report['target_ui_refresh_ms']=UI_REFRESH_MS
            report['closed_scan_off']=not self.controls.running
            report['passed']=len(self.checks)>=15 and all(self.checks.values()) and report['closed_scan_off'] and len(self.session.seen)==7 and count==3 and not self.callback_errors and report['content_height']<=report['available_height'] and report['content_width']<=report['available_width']
            (self.root/'logs/simple-ui-smoke-test.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        self.window.destroy()


def run(Session,root,channels,auto_close=None,initial_profile='coded-audible'):
    kernel=ctypes.windll.kernel32
    kernel.CreateMutexW.argtypes=(ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p)
    kernel.CreateMutexW.restype=ctypes.c_void_p
    mutex=kernel.CreateMutexW(None,False,'Local\\EE475_SEN0325_Diagnostic')
    if kernel.GetLastError()==183:
        ctypes.windll.user32.MessageBoxW(None,'Acoustic Localizer is already open. Switch to its existing window.','EE475',0)
        kernel.CloseHandle.argtypes=(ctypes.c_void_p,);kernel.CloseHandle(mutex);return 0
    try:
        app=SimpleView(Session,root,channels,auto_close,initial_profile);app.window.mainloop()
    finally:
        kernel.CloseHandle.argtypes=(ctypes.c_void_p,);kernel.CloseHandle(mutex)
    return 0
