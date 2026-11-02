"""RX4: identical-input replay, geometry/noise rejection, cache and turn checks."""
from pathlib import Path
from collections import Counter
import hashlib
import importlib.util
import json
import math
import sys
import tempfile
import time
import zipfile
import argparse
from datetime import datetime, timezone

import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
APP=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/06-joint-delay'
sys.path.insert(0,str(APP))
from beacon_dsp import BeaconEstimator, template, SIZE, RATE, CHANNELS
from joint_delay_dsp import fit_joint_spectral
from direction_diagnostics import DirectionDiagnostics
import highband_dsp

checks={};evidence={};rng=np.random.default_rng(475404)
f=np.fft.rfftfreq(SIZE,1/RATE)
code,spectrum,_=template('coded-20');spectrum=spectrum/np.std(code)
config=json.loads((APP/'array_geometry.json').read_text(encoding='utf-8-sig'))
config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)
with tempfile.TemporaryDirectory() as temporary:
    folder=Path(temporary);geometry=folder/'geometry.json';geometry.write_text(json.dumps(config))
    with zipfile.ZipFile(STAGE/'backups/before-RX4.zip') as archive:
        baseline_path=folder/'rx3.py';baseline_path.write_bytes(archive.read('SEN0325-Pico-Setup/highband_dsp.py'))
    spec=importlib.util.spec_from_file_location('rx3_before_joint',baseline_path)
    baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)

    def receiver():return BeaconEstimator(geometry,'coded-20')
    r=receiver();pairs=np.arange(21)
    position=np.zeros((7,2))
    for ch in range(6):
        pair=np.flatnonzero((r.pairs[:,0]==ch)&(r.pairs[:,1]==6))[0]
        position[ch]=r.delta[pair]*RATE/r.speed
    design=np.column_stack((position,np.ones(7)))
    frequencies=f[r.indices]

    def pair_spectra(arrivals,carrier=None):
        lag=arrivals[r.pairs[:,0]]-arrivals[r.pairs[:,1]]
        phase=2*np.pi*lag[:,None]*frequencies[None,:]/RATE
        if carrier is not None:phase=phase+(carrier[r.pairs[:,0]]-carrier[r.pairs[:,1]])[:,None]
        return np.exp(1j*phase)*r.weights[None,:]

    direct=[]
    for angle in (0,23,45,91,179,210,271,359):
        for projection in (.4,.7,1.):
            v=np.array([math.sin(math.radians(angle)),math.cos(math.radians(angle))])*projection
            band=pair_spectra(position@v,rng.uniform(-np.pi,np.pi,7))
            raw,q,d=fit_joint_spectral(r,band,pairs)
            assert raw is not None,d
            error=abs((raw-angle+180)%360-180)
            assert error<=2.1,(angle,projection,raw,d)
            direct.append({'angle':angle,'projection':projection,'error_deg':round(error,3)})
    checks['physical_delay_fields_and_carrier_offsets']=True
    evidence['direct_physical_fields']=direct

    # Previous display direction must have no influence on this frame's fit.
    band=pair_spectra(position@np.array([1.,0.]))
    outputs=[]
    for previous in (0,90,180,270):
        r.candidate=previous;r.last_trusted_raw=previous
        outputs.append(fit_joint_spectral(r,band,pairs)[0])
    assert len(set(outputs))==1 and outputs[0]==90
    checks['joint_fit_has_no_previous_angle_or_turn_veto']=True

    raw,q,d=fit_joint_spectral(r,np.ones_like(band)*r.weights[None,:],pairs)
    assert raw is None and 'physical_projection' in d['joint_rejections']
    checks['zero_horizontal_projection_has_no_invented_bearing']=True
    raw,q,d=fit_joint_spectral(r,band,np.arange(10))
    assert raw is None
    checks['insufficient_independent_pair_support_rejected']=True

    negative=[]
    for _ in range(200):
        a=rng.uniform(0,2*np.pi)
        times=position@np.array([np.sin(a),np.cos(a)])+rng.normal(0,5,7)
        fitted=design@np.linalg.lstsq(design,times,rcond=None)[0]
        residual=float(np.sqrt(np.mean((times-fitted)**2)))
        if residual<2:continue
        raw,q,d=fit_joint_spectral(r,pair_spectra(times),pairs)
        assert raw is None,(residual,d)
        negative.append({'nonphysical_rms_samples':round(residual,3),'rejections':d.get('joint_rejections')})
    assert len(negative)>=150
    checks['strong_coded_nonphysical_delay_fields_rejected']=True
    evidence['nonphysical_delay_fields']={'count':len(negative),'accepted':0,'rows':negative}

    # Reusing the pair curves must be numerically identical, without a second
    # expensive einsum, and a different input object must bypass stale cache.
    highband_dsp.fit_delays(r,band,pairs)
    uncached=fit_joint_spectral(receiver(),band,pairs)
    einsum=np.einsum
    def unexpected(*args,**kwargs):raise AssertionError('Pair-score search repeated despite cache')
    np.einsum=unexpected
    try:cached=fit_joint_spectral(r,band,pairs)
    finally:np.einsum=einsum
    assert cached[2]['joint_score_cache_reused'] and cached[:2]==uncached[:2]
    assert not fit_joint_spectral(r,band.copy(),pairs)[2]['joint_score_cache_reused']
    checks['score_cache_preserves_result_and_avoids_repeated_search']=True
    checks['new_input_does_not_reuse_stale_curves']=True
    highband_dsp.reset(r,'test_gap')
    assert r._highband_pair_scores is None
    checks['capture_reset_clears_score_cache']=True

    def plane(angle,noise=20,offsets=None):
        rows=[]
        for ch in range(7):
            tau=0 if ch==6 else .04*math.cos(math.radians(angle-ch*60))/343
            if offsets is not None:tau+=offsets[ch]/RATE
            rows.append(100*np.fft.irfft(spectrum*np.exp(2j*np.pi*f*(tau-.018)),SIZE)+rng.normal(0,noise,SIZE))
        return np.rint(np.column_stack(rows)).astype('<i2')
    old=receiver();new=receiver()
    for i,angle in enumerate((30,30,210,90,270,0)):
        sample=plane(angle)
        before,_=baseline.estimate_highband(old,sample,{},1+i*.2)
        after,_=new.estimate(sample,{},1+i*.2)
        assert before.get('raw_angle_deg')==after.get('raw_angle_deg'),(before,after)
        assert before.get('confidence')==after.get('confidence')
        if i:assert after['valid']
    checks['original_accepted_fits_preserved_during_large_turns']=True
    checks['first_window_still_requires_repeated_code']=not baseline.estimate_highband(receiver(),plane(30),{},1)[0]['valid']

    new=receiver()
    for i in range(4):
        after,_=new.estimate(plane(90,offsets=[0,5,-4,6,-5,3,0]),{},1+i*.2)
        assert not after['valid'] and after['reason']=='group_delay_inconsistent',after
    checks['full_pipeline_rejects_mutually_inconsistent_coded_channels']=True
    for name,sample,health in [('silence',np.zeros((SIZE,7)),{}),('capture_gap',plane(0),{'dropped':1}),
                               ('clipping',np.full((SIZE,7),32767),{}),('bad_shape',np.zeros((8,7)),{})]:
        result,_=new.estimate(sample,health,5)
        assert not result['valid'] and 'joint_attempt' not in result
    checks['invalid_capture_and_no_code_do_not_enter_rescue']=True

    replays=[];timings={'RX3':[],'RX4':[]};preserved=0;added=0;cache_hits=0
    for name in ('launcher-20261027-175338-954951-delay_rejection-seq6635.json',
                 'launcher-20261027-175338-954951-delay_rejection-seq6725.json'):
        path=PROJECT/'legacy/stages/05-direction-diagnostics/evidence/captures'/name
        meta=json.loads(path.read_text(encoding='utf-8'))
        assert hashlib.sha256(path.with_suffix('.npz').read_bytes()).hexdigest()==meta['raw_sha256']
        with np.load(path.with_suffix('.npz'),allow_pickle=False) as z:
            audio=z['audio'].copy();times=z['received_at'].copy()
        old=receiver();new=receiver();before=[];after=[]
        for sample,now,event in zip(audio,times,meta['events']):
            b,_=baseline.estimate_highband(old,sample,event['health'],float(now))
            a,_=new.estimate(sample,event['health'],float(now))
            before.append(b);after.append(a)
            if b['valid']:
                assert a['valid'] and b['raw_angle_deg']==a['raw_angle_deg'] and b['confidence']==a['confidence']
                preserved+=1
            if a['valid'] and not b['valid']:added+=1
            if 'joint_attempt' in a:
                assert a['joint_attempt']['joint_score_cache_reused']
                cache_hits+=1
        replays.append({'capture':str(path),'raw_sha256':meta['raw_sha256'],
            'RX3_reasons':dict(Counter(r['reason'] for r in before)),
            'RX4_reasons':dict(Counter(r['reason'] for r in after)),
            'rows':[{'sequence':e['health']['seq'],'RX3':b,'RX4':a} for e,b,a in zip(meta['events'],before,after)]})
        # Balanced ordering includes cold construction, all capture windows and
        # serialization fields in the estimator result. No acoustical latency claim.
        for order in (('RX3','RX4'),('RX4','RX3')):
            for key in order:
                rec=receiver();func=baseline.estimate_highband if key=='RX3' else highband_dsp.estimate_highband
                for sample,now,event in zip(audio,times,meta['events']):
                    result,_=func(rec,sample,event['health'],float(now))
                    timings[key].append(result['processing_ms'])
    assert preserved==7 and added>=2 and cache_hits>0,(preserved,added,cache_hits)
    checks['identical_raw_input_adds_bearings_without_losing_existing_seven']=True
    checks['live_rescue_reuses_original_score_curves']=True
    evidence['phone_replay']={'snapshots':2,'windows':40,'previous_bearings_preserved':preserved,
        'additional_bearings':added,'rows':replays,'selection':'Failure-triggered snapshots, not a representative success-rate test; true bearing is unknown.'}
    evidence['processing_timing']={key:{'windows':len(values),'median_ms':round(float(np.median(values)),3),
        'p95_ms':round(float(np.percentile(values,95)),3),'max_ms':max(values)} for key,values in timings.items()}

    # RX4 metadata labels must survive the asynchronous writer.
    diag=DirectionDiagnostics(folder/'local','rx4-test',geometry,checkpoint='RX4')
    for seq in range(1,7):
        diag.observe(np.zeros((SIZE,7),dtype='<i2'),{'seq':seq},
            {'profile':'coded-20','received_at':seq*.2,'code_channels':7,'reason':'group_delay_inconsistent','valid':False})
    diag.close()
    meta=json.loads(next(diag.folder.glob('*.json')).read_text())
    assert meta['checkpoint']=='RX4' and meta['block_count']==6 and meta['completion']=='session_closed'
    checks['automatic_snapshot_metadata_labels_RX4']=True

report={'passed':all(checks.values()),'checkpoint':'RX4','completed_date':datetime.now(timezone.utc).date().isoformat(),
        'checks':checks,'evidence':evidence,'limitations':'Model and saved-audio evidence only; no new physical known-angle or range validation. Joint consistency is a model constraint, not proof of correct bearing.'}
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=STAGE/'joint-delay-validation.json')
destination=parser.parse_args().output
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'nonphysical_cases':len(negative),
    'preserved_phone_bearings':preserved,'additional_phone_bearings':added,'timing':evidence['processing_timing']},indent=2))
