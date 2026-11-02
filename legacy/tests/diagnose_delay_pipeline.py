"""Read-only log/source diagnosis. Does not open Pico or change the algorithm."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
DEST=PROJECT/'reports/delay-diagnosis-2026-10-22'
DEST.mkdir(exist_ok=True)

def distribution(values):
    values=[v for v in values if v is not None and np.isfinite(v)]
    if not values:return None
    return {'count':len(values),'p05':round(float(np.percentile(values,5)),3),
            'median':round(float(np.median(values)),3),'p95':round(float(np.percentile(values,95)),3),
            'maximum':round(float(max(values)),3)}

sessions=[('before_new_vetoes','launcher-20261022-175059-237468.txt'),
          ('with_new_vetoes','launcher-20261022-180338-889744.txt'),
          ('pico_ui_import_smoke','launcher-20261022-180253-514264.txt')]
report={'scope':'Diagnostic snapshot only; no new algorithm or firmware change.',
        'warning':'These sessions have different uncontrolled phone positions/volumes and playback intervals. Rates are not a controlled A/B accuracy comparison.',
        'sessions':[]}
for label,name in sessions:
    path=ROOT/'logs'/name
    raw=path.read_bytes()
    (DEST/name).write_bytes(raw)
    lines=raw.decode('utf-8',errors='replace').splitlines()
    events=[];headers=[];incomplete=0
    for line in lines:
        if line.startswith('# EVENT '):
            try:events.append(json.loads(line[8:]))
            except ValueError:incomplete+=1
        elif line.startswith('AUDIO '):headers.append(dict(re.findall(r'(\w+)=(\S+)',line)))
    rows=[r for r in events if r.get('event')=='beacon_estimate' and r.get('frequency')==20000]
    valid=[r for r in rows if r.get('valid')]
    matched=[r for r in rows if r.get('code_channels',0)>=4]
    strong=[r for r in rows if r.get('code_channels',0)>=6 and r.get('code_pnr_db',0)>=24]
    inconsistent=[r for r in matched if r.get('reason')=='group_delay_inconsistent']
    pairs=[]
    for a,b in zip(valid,valid[1:]):
        dt=b['received_at']-a['received_at']
        delta=abs((b['raw_angle_deg']-a['raw_angle_deg']+180)%360-180)
        if delta>=120 and dt<15:
            pairs.append({'time_before':a.get('wall_time'),'time_after':b.get('wall_time'),
                          'gap_s':round(dt,3),'raw_change_deg':round(delta,2),
                          'source_before':a.get('direction_source','primary_complex_delay'),
                          'source_after':b.get('direction_source','primary_complex_delay')})
    intervals=[b['received_at']-a['received_at'] for a,b in zip(rows,rows[1:]) if 0<b['received_at']-a['received_at']<1]
    cycles=[r['capture_cycle_ms'] for r in rows if r.get('capture_cycle_ms',0)<450]
    matched_cycles=[r['capture_cycle_ms'] for r in strong if r.get('capture_cycle_ms',0)<450]
    residual=[r['capture_cycle_ms']-r['processing_ms'] for r in rows if 0<r.get('capture_cycle_ms',0)<450 and 'processing_ms' in r]
    violations={
        'retained_pair_residual_over_1_sample':sum(r.get('group_delay_rms_samples',0)>1 for r in inconsistent),
        'all_pair_residual_over_1_5_samples':sum(r.get('all_pair_rms_samples',0)>1.5 for r in inconsistent),
        'projection_outside_0_25_to_1_3':sum('horizontal_projection' in r and not .25<=r['horizontal_projection']<=1.3 for r in inconsistent),
        'insufficient_group_delays':sum(r.get('group_delay_reason')=='insufficient_group_delays' for r in inconsistent)}
    example=max(inconsistent,key=lambda r:r.get('code_pnr_db',0)) if inconsistent else None
    if example:example={k:example.get(k) for k in ('wall_time','reason','code_channels','code_pnr_db','band_level_dbfs','median_pair_coherence','group_delay_pairs','group_delay_rms_samples','all_pair_rms_samples','horizontal_projection','group_delay_reason','capture_cycle_ms','processing_ms')}
    record={'label':label,'log':name,'snapshot_bytes':len(raw),'snapshot_sha256':hashlib.sha256(raw).hexdigest(),
            'incomplete_event_lines_ignored':incomplete,'windows_20khz':len(rows),
            'reasons':dict(Counter(r['reason'] for r in rows)),
            'code_matched_windows':len(matched),'matched_reasons':dict(Counter(r['reason'] for r in matched)),
            'strong_code_windows':len(strong),'strong_reasons':dict(Counter(r['reason'] for r in strong)),
            'valid_windows':len(valid),'valid_sources':dict(Counter(r.get('direction_source','primary_complex_delay') for r in valid)),
            'packet_headers':len(headers),'max_dropped':max([int(h.get('dropped',0)) for h in headers] or [0]),
            'max_rx_stall':max([int(h.get('rx_stall',0)) for h in headers] or [0]),
            'error_lines':[line for line in lines if line.startswith('ERROR:')],
            'sequence_regressions':sum(int(b['seq'])<=int(a['seq']) for a,b in zip(headers,headers[1:])),
            'calibration_events':[e for e in events if e.get('event') in ('set_front','mirror_view')],
            'capture_cycle_steady_ms':distribution(cycles),'strong_code_cycle_steady_ms':distribution(matched_cycles),
            'dsp_ms_all':distribution([r.get('processing_ms') for r in rows]),
            'dsp_ms_strong_code':distribution([r.get('processing_ms') for r in strong]),
            'device_io_wait_before_dsp_ms':distribution(residual),
            'steady_estimate_interval_ms':distribution([t*1000 for t in intervals]),
            'startup_or_restart_cycles_ms':[r['capture_cycle_ms'] for r in rows if r.get('capture_cycle_ms',0)>=450],
            'pico_unpack_max_per_1024_frames_us':distribution([int(h.get('process_us',0)) for h in headers]),
            'primary_reject_subtypes':dict(Counter(r.get('group_delay_reason','not_recorded') for r in inconsistent)),
            'overlapping_threshold_violations':violations,'strong_code_rejection_example':example,
            'opposite_new_bearings_within_15s':pairs}
    report['sessions'].append(record)

report['source_snapshot']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
    ('main.c','sen0325_i2s.pio','sen0325_launcher.py','highband_dsp.py','arrival_dsp.py','runtime_tuning.py','sen0325_simple_view.py','array_geometry.json')}
source=(ROOT/'highband_dsp.py').read_text(encoding='utf-8')
report['on_disk_rollback']={'angle_jump_veto_removed':"finish('direction_jump_rejected'" not in source,
                           'hard_dual_estimator_veto_removed':"finish('estimator_disagreement'" not in source,
                           'two_candidate_confirmation_restored':'if receiver.confirmations<2:' in source,
                           'runtime_note':'The running process may still use loaded guarded code until restarted. Logs are classified by emitted reasons, not current source hashes.'}
report['not_measured']=['separate host header wait vs USB payload duration','microphone channel timing offsets on physical hardware',
                        'measured source bearing/height/distance for these log sessions','event-queue-to-visible-frame latency',
                        'raw 20 kHz microphone waveforms for these historical sessions']
(DEST/'diagnostic-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
compact=[]
for r in report['sessions']:
    compact.append({k:r[k] for k in ('label','windows_20khz','reasons','code_matched_windows','matched_reasons','strong_code_windows','strong_reasons','max_dropped','max_rx_stall','error_lines','capture_cycle_steady_ms','strong_code_cycle_steady_ms','dsp_ms_strong_code','device_io_wait_before_dsp_ms','steady_estimate_interval_ms','overlapping_threshold_violations','strong_code_rejection_example','opposite_new_bearings_within_15s')})
print(json.dumps(compact,ensure_ascii=False,indent=2))
