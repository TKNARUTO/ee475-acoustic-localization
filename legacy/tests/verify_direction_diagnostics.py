"""RX3 evidence: confirmation behavior, unchanged fits, bounded async raw capture."""
from pathlib import Path
import collections
import importlib.util
import json
import math
import sys
import tempfile
import zipfile

import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
APP=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/05-direction-diagnostics'
sys.path.insert(0,str(APP))
from beacon_dsp import BeaconEstimator, template, SIZE, RATE
from direction_diagnostics import DirectionDiagnostics
import highband_dsp

rng=np.random.default_rng(475103)
frequency=np.fft.rfftfreq(SIZE,1/RATE)
code,spectrum,_=template('coded-20')
spectrum=spectrum/np.std(code)

def plane(angle, delays=None):
    rows=[]
    for ch in range(7):
        tau=(0 if ch==6 else .04*math.cos(math.radians(angle-ch*60))/343)
        if delays is not None:tau+=delays[ch]/RATE
        rows.append(100*np.fft.irfft(spectrum*np.exp(2j*np.pi*frequency*(tau-.018)),SIZE)
                    +rng.normal(0,20,SIZE))
    return np.rint(np.column_stack(rows)).astype('<i2')

checks={};evidence={}
with tempfile.TemporaryDirectory() as temporary:
    folder=Path(temporary)
    config=json.loads((APP/'array_geometry.json').read_text(encoding='utf-8-sig'))
    config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)
    geometry=folder/'geometry.json';geometry.write_text(json.dumps(config),encoding='utf-8')
    with zipfile.ZipFile(STAGE/'backups/before-RX3.zip') as archive:
        source=archive.read('SEN0325-Pico-Setup/highband_dsp.py')
    baseline_path=folder/'baseline.py';baseline_path.write_bytes(source)
    spec=importlib.util.spec_from_file_location('rx2_highband',baseline_path)
    baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
    old=BeaconEstimator(geometry,'coded-20');new=BeaconEstimator(geometry,'coded-20')
    comparisons=[]
    for i,angle in enumerate([30,30,30,210,210,120,300,0]):
        samples=plane(angle)
        a,_=baseline.estimate_highband(old,samples,{},1+i*.2)
        b,_=new.estimate(samples,{},1+i*.2)
        assert a.get('candidate_angle_deg')==b.get('candidate_angle_deg'),(a,b)
        for key in ('group_delay_rms_samples','all_pair_rms_samples','horizontal_projection'):
            assert a.get(key)==b.get(key),(key,a,b)
        if i==0:assert not b['valid'] and b['reason']=='confirming_beacon_direction'
        else:
            assert b['valid'],b
            assert abs((b['raw_angle_deg']-angle+180)%360-180)<3,b
        comparisons.append({'angle':angle,'before_valid':a['valid'],'after_valid':b['valid'],
                            'candidate':b.get('candidate_angle_deg'),'turn':b.get('candidate_turn_deg')})
    checks['primary_fit_and_residuals_unchanged']=True
    checks['large_real_turns_do_not_wait_for_angle_confirmation']=True
    checks['first_code_window_still_requires_repeat']=True
    evidence['turn_sequence']=comparisons

    receiver=BeaconEstimator(geometry,'coded-20')
    for i in range(3):r,_=receiver.estimate(plane(90),{},1+i*.2)
    assert r['valid']
    bad=plane(90,[0,5,-4,6,-5,3,0])
    rejected,_=receiver.estimate(bad,{},1.6)
    assert rejected['code_channels']>=6 and rejected['reason']=='group_delay_inconsistent',rejected
    resumed,_=receiver.estimate(plane(90),{},1.8)
    assert resumed['valid'],resumed
    assert resumed['code_confirmation_windows']==2
    checks['fit_failure_does_not_erase_confirmed_code']=True
    checks['inconsistent_geometry_is_still_rejected']=True
    evidence['rejection_and_resume']=[rejected,resumed]
    assert len(rejected['code_channel_diagnostics'])==7
    assert len(rejected['pair_delay_diagnostics'])==21
    used=[p for p in rejected['pair_delay_diagnostics'] if p['used_in_fit']]
    assert all('residual_samples' in p for p in used)
    assert 'arrival_rejection_counts' in rejected
    checks['per_channel_pair_and_arrival_diagnostics_present']=True

    for label,samples,health in [('no_code',np.zeros((SIZE,7)),{}),
                                ('capture_gap',plane(90),{'dropped':1}),
                                ('clipping',np.full((SIZE,7),32767),{}),
                                ('invalid_raw',np.zeros((4,7)),{})]:
        r,_=receiver.estimate(samples,health,2)
        assert not r['valid'] and receiver.confirmations==0,r
        resumed,_=receiver.estimate(plane(90),{},2.2)
        assert not resumed['valid'] and resumed['reason']=='confirming_beacon_direction',resumed
        receiver.estimate(plane(90),{},2.4)
        checks[label+'_clears_confirmation']=True
    after_gap,_=receiver.estimate(plane(90),{},5)
    assert not after_gap['valid'] and after_gap['code_confirmation_reset_reason']=='code_time_gap'
    checks['long_time_gap_requires_fresh_code_repeat']=True

    # Replay only the state machine over frozen events, never reconstruct audio
    # or claim new physical directions. Fit decisions in this calculation stay fixed.
    frozen=PROJECT/'reports/phone-observation-2026-10-27/launcher-20261027-172051-289267.txt'
    events=[json.loads(line[8:]) for line in frozen.read_text(encoding='utf-8').splitlines() if line.startswith('# EVENT ')]
    rows=[r for r in events if r.get('event')=='beacon_estimate']
    repeat=0;last=None;recoverable=first=0
    for row in rows:
        hit=row.get('code_channels',0)>=4
        now=row['monotonic']
        repeat=min(2,repeat+1) if hit and last is not None and 0<now-last<.75 else int(hit)
        last=now if hit else None
        if row['reason']=='confirming_beacon_direction':
            recoverable+=repeat>=2;first+=repeat<2
    assert (recoverable,first)==(121,5),(recoverable,first)
    checks['frozen_log_state_replay_matches_121_redundant_waits']=True
    evidence['state_only_replay']={'previous_confirming_windows':126,'code_already_repeated':recoverable,
        'first_hit_after_gap':first,'limitation':'Replays logged confirmation state only; no raw-audio re-estimation or angle-accuracy claim.'}

    # All recorder checks use deterministic bytes, independent of DSP internals.
    captured=[]
    recorder=DirectionDiagnostics(folder/'recordings','test',geometry,lambda name,**kw:captured.append((name,kw)))
    def feed(seq,reason='group_delay_inconsistent',generation=0,valid=False):
        audio=np.full((SIZE,7),seq,dtype='<i2')
        recorder.observe(audio,{'seq':seq,'fs':RATE,'frames':SIZE,'dropped':0,'rx_stall':0},
            {'profile':'coded-20','received_at':10+seq*.2,'code_channels':7 if reason!='beacon_not_detected' else 0,
             'reason':reason,'valid':valid},generation,'2026-10-27T18:00:00-07:00')
    for i in range(1,5):feed(i,'beacon_not_detected')
    assert recorder.pending is None
    for i in range(5,23):feed(i)
    recorder.close()
    paths=list(recorder.folder.glob('*.json'));assert len(paths)==1,paths
    meta=json.loads(paths[0].read_text());raw=np.load(paths[0].with_suffix('.npz'),allow_pickle=False)
    assert meta['completion']=='complete' and meta['block_count']==20
    assert raw['audio'].shape==(20,SIZE,7)
    assert np.array_equal(raw['audio'][:,0,0],raw['sequence'])
    assert raw['sequence'].tolist()==list(range(3,23))
    assert len(meta['events'])==20
    raw.close()
    checks['automatic_raw_capture_preserves_sequence_and_samples']=True
    checks['silence_alone_does_not_trigger_raw_save']=True

    recorder=DirectionDiagnostics(folder/'limits','test',geometry)
    # Advance continuously beyond cooldowns and alternate valid/failed blocks.
    for i in range(1,501):
        valid=(i//100)%2==1
        feed(i,'estimated' if valid else 'group_delay_inconsistent',valid=valid)
        if recorder.pending is None and recorder.worker is not None:recorder.jobs.join()
    recorder.close()
    assert recorder.saved['delay_rejection']==2 and recorder.saved['valid_reference']==2,recorder.saved
    assert len(list(recorder.folder.glob('*.npz')))==4
    checks['session_raw_capture_is_capped_at_four_short_files']=True

    recorder=DirectionDiagnostics(folder/'context','test',geometry)
    for i in range(1,7):feed(i)
    feed(7,'beacon_not_detected',generation=1)
    recorder.close()
    meta=json.loads(next(recorder.folder.glob('*.json')).read_text())
    assert meta['completion']=='capture_context_changed'
    assert all(b['generation']==0 for b in meta['events'])
    checks['mode_or_scan_generation_does_not_mix_capture_contexts']=True

    recorder=DirectionDiagnostics(folder/'shutdown','test',geometry)
    for i in range(1,7):feed(i)
    recorder.close()
    meta=json.loads(next(recorder.folder.glob('*.json')).read_text())
    assert meta['completion']=='session_closed' and meta['block_count']==6
    checks['shutdown_flushes_partial_snapshot']=True

    # A local disk failure must report a diagnostic error, without changing DSP.
    recorder=DirectionDiagnostics(folder/'unwritable','test',geometry,lambda name,**kw:captured.append((name,kw)))
    recorder.folder.parent.mkdir(parents=True,exist_ok=True)
    recorder.folder.write_text('not a directory')
    for i in range(1,19):feed(i)
    recorder.close()
    assert any(name=='direction_diagnostic_error' for name,kw in captured)
    checks['diagnostic_write_failure_is_isolated_from_scan']=True

    from replay_direction_diagnostics import analyze
    replay,_=analyze(paths[0],folder/'replay-validation.json')
    assert replay['raw_sha256_verified'] and replay['blocks']==20
    assert replay['rx2_reasons']==replay['rx3_reasons']=={'beacon_not_detected':20}
    checks['saved_snapshot_replays_with_verified_hash_and_sequence']=True
    corrupted=json.loads(paths[0].read_text());corrupted['raw_sha256']='0'*64
    corrupt_path=paths[0].with_name('tampered.json')
    corrupt_path.write_text(json.dumps(corrupted),encoding='utf-8')
    try:analyze(corrupt_path,folder/'should-not-exist.json')
    except AssertionError as error:assert 'checksum' in str(error).lower()
    else:raise AssertionError('Mismatched raw audio was accepted')
    checks['replay_rejects_raw_checksum_mismatch']=True

report={'passed':all(checks.values()),'checks':checks,'evidence':evidence,
        'limitation':'Synthetic signals, frozen event-state replay and temporary local files. Not a new phone playback or physical bearing/range acceptance test.'}
(STAGE/'confirmation-diagnostics-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'state_only_redundant_waits':recoverable},indent=2))
