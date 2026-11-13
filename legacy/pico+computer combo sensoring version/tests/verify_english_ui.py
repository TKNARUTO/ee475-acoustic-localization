"""Validate the actual English Tk view while leaving any open hardware session alone."""
from pathlib import Path
import json
import queue
import re
import sys
import tempfile
import threading
import time
import argparse
from tkinter import ttk
from unittest.mock import patch

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
sys.path.insert(0,str(ROOT))
from sen0325_launcher import CHANNELS
from direction_estimator import PhaseEstimator
from sen0325_simple_view import SimpleView
from signal_scope import signal_payload
import numpy as np

class DisconnectedWorker:
    """No serial device, no simulated bearings, no microphone-capture claims."""
    def __init__(self):
        self.events=queue.Queue()
        self.want_running=threading.Event()
        self.stop=threading.Event()
        self.reconnect=threading.Event()
        self.thread=threading.Thread()
        self.frames=0
        self.raw_bursts=0
        self.frequency=2400
        self.seen=set()
        self.last_tones={}
        self.direction_estimator=PhaseEstimator(ROOT/'array_geometry.json')
        self.log_path=ROOT/'logs/offline-ui-stub.txt'
        self.events.put(('status','Disconnected test worker; no serial device opened'))
    def start(self):pass
    def set_running(self,value):
        self.want_running.set() if value else self.want_running.clear()
    def set_mode(self,mode):
        self.mode=mode
        from beacon_dsp import PROFILES
        self.frequency=PROFILES[mode]['center']
    def mark_event(self,*args,**kwargs):pass
    def set_front(self):raise ValueError('No stable bearing')

def descendants(widget):
    yield widget
    for child in widget.winfo_children():
        yield from descendants(child)

class OfflineInstance:
    """No instance files, restart requests, or focus actions during UI tests."""
    def __init__(self,root,checkpoint):
        pass
    def restart_requested(self,now=None,on_focus=None):
        return False
    def closed(self):
        pass

# SimpleView imports AppInstance inside its constructor. Replace that dependency
# before construction; the stub remains attached for all refresh/close callbacks.
# Never save/restore live instance files: that could race a real app or updater.
with patch('app_instance.AppInstance',OfflineInstance):
    app=SimpleView(DisconnectedWorker,ROOT,CHANNELS,initial_profile='coded-gap')
report={'mode':'Offline English UI validation; no hardware capture and no sound emitted','checks':{}}
checks=report['checks']
def exercise():
    try:
        app.window.update_idletasks()
        checks['startup_scan_off']=not app.controls.running
        checks['gap_selected_on_launch']=app.controls.profile=='coded-gap' and app.session.frequency==20000
        checks['english_title']=app.window.title()=='EE475 | Acoustic Localizer | Gap 18-22 kHz'
        buttons=[w for frame in (app.main_controls,app.receiver_panel) for w in frame.winfo_children() if isinstance(w,ttk.Button)]
        report['main_buttons']=[w['text'] for w in buttons]
        checks['four_main_buttons']=len(buttons)==4
        checks['no_playback_controller']=not hasattr(app,'player') and not hasattr(app,'toggle_playback')
        checks['only_gap_builtin']=tuple(app.audio_menu['values'])==('Gap test | 18-22 kHz',)
        app.toggle_radar()
        checks['scan_starts']=app.controls.running
        samples=np.tile((2000*np.sin(2*np.pi*17000*np.arange(4096)/48000))[:,None],(1,7))
        app.session.events.put(('signal',signal_payload(samples,99,time.monotonic())))
        app.last_detail_refresh=0;app.refresh()
        checks['secondary_spectrum_visible_without_direction']=bool(app.scope.spectrum.find_withtag('spectrum_trace')) and app.direction.current(time.monotonic())[0] is None
        checks['actual_waveform_drawn']=bool(app.scope.waveform.find_withtag('waveform_trace'))
        app.toggle_radar()
        app.last_detail_refresh=0;app.refresh()
        checks['scan_stops']=not app.controls.running
        checks['stopped_signal_trace_clears']=not app.scope.spectrum.find_withtag('spectrum_trace')
        app.audio_name.set('Gap test | 18-22 kHz');app.change_audio()
        checks['gap_profile_resolves']=app.controls.profile=='coded-gap'
        from beacon_importer import import_reference
        with tempfile.TemporaryDirectory() as imported_fixture:
            reference=import_reference(PROJECT/'audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav',imported_fixture)
        app.toggle_radar()
        app.import_busy=True;app.import_button.configure(state='disabled')
        app.import_events.put(('ok',reference));app.poll_import()
        checks['import_selects_reference']=app.controls.profile==reference['profile'] and app.audio_name.get()=='Imported beacon'
        checks['import_keeps_scan_state']=app.controls.running and app.scope.target_band==(reference['spec']['low'],reference['spec']['high'])
        previous=app.controls.profile
        app.import_events.put(('error','unsupported test reference'));app.poll_import()
        checks['import_error_keeps_previous_reference']=app.controls.profile==previous and 'Import rejected' in app.help.get()
        app.toggle_radar()
        app.set_front()
        checks['uncalibrated_front_rejected']='stable bearing' in app.help.get()
        app.show_advanced();app.show_chart();app.window.update_idletasks()
        checks['diagnostic_windows_open']=app.advanced.state()=='normal' and app.chart_window.state()=='normal'
        chinese=[]
        for widget in descendants(app.window):
            if 'text' in widget.keys() and re.search(r'[\u4e00-\u9fff]',str(widget['text'])):
                chinese.append(str(widget['text']))
        report['remaining_chinese_labels']=chinese
        checks['all_widget_labels_english']=not chinese
        report['layout']={'required_width':app.pane.winfo_reqwidth(),'available_width':app.pane.winfo_width(),
                          'required_height':app.pane.winfo_reqheight(),'available_height':app.pane.winfo_height()}
        checks['main_content_fits']=report['layout']['required_width']<=report['layout']['available_width'] and report['layout']['required_height']<=report['layout']['available_height']
        checks['audio_folder_resolves']=(ROOT.parent/'audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3').is_file()
        checks['no_callback_errors']=not app.callback_errors
        checks['no_hardware_claim']=app.session.frames==0
        checks['no_audio_output_api']=not any(token in (ROOT/'app_controls.py').read_text(encoding='utf-8') for token in ('winsound','PlaySound','sounddevice','pyaudio'))
        report['passed']=all(checks.values())
    except Exception:
        import traceback
        report['error']=traceback.format_exc();report['passed']=False
    finally:
        app.close()

app.window.after(600,exercise)
app.window.mainloop()
report['callback_errors']=app.callback_errors
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=PROJECT/'stages/10-gap-active/english-ui-validation.json')
args=parser.parse_args()
destination=args.output
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)

