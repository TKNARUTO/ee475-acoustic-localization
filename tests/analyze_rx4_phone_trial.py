"""Describe received signal, pipeline timing and direction changes; no angle veto."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import math
import csv
import numpy as np

def analyze(path,plots=False):
    path=Path(path).resolve();trial=json.loads(path.read_text(encoding='utf-8-sig'))
    raw_path=path.with_name(trial['raw_file'])
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest()==trial['raw_sha256']
    with np.load(raw_path,allow_pickle=False) as z:audio=z['audio'].copy();seq=z['sequence'].copy();stamp=z['received_at'].copy()
    es=trial['events'];assert len(audio)==len(es)==len(seq)==len(stamp)
    assert all(int(s)==e['sequence']==e['health']['seq'] for s,e in zip(seq,es))
    time=stamp-stamp[0];f=np.fft.rfftfreq(4096,1/48000);band=(f>=19000)&(f<=21000)
    powers=[];levels=[]
    for block in audio:
        x=block.astype(float);x-=x.mean(axis=0)
        power=2*np.abs(np.fft.rfft(x,axis=0))**2/4096**2/32768**2
        powers.append(np.median(power,axis=1));levels.append(10*np.log10(max(float(np.median(power[band].sum(axis=0))),1e-20)))
    powers=np.array(powers);levels=np.array(levels)
    hits=np.array([e['estimate'].get('code_channels',0)>=4 for e in es]);valid=np.array([e['estimate']['valid'] for e in es])
    quiet=(~hits)&(levels<(np.median(levels[hits])-6 if hits.any() else np.median(levels)))
    loud_unmatched=(~hits)&(levels>=(np.median(levels[hits])-3 if hits.any() else np.median(levels)))
    def distribution(values):
        values=[float(v) for v in values if v is not None and np.isfinite(v)]
        return {'n':len(values),'median':round(float(np.median(values)),3),'p95':round(float(np.percentile(values,95)),3),'max':round(max(values),3)} if values else {}
    active_indices=np.flatnonzero(hits);groups=[]
    for i in active_indices:
        if not groups or time[i]-time[groups[-1][-1]]>.5:groups.append([])
        groups[-1].append(int(i))
    groups=[g for g in groups if len(g)>=6]
    group_rows=[]
    for number,indices in enumerate(groups,1):
        ix=np.array(indices);in_span=(time>=time[ix[0]])&(time<=time[ix[-1]])
        group_rows.append({'group':number,'start_s':round(float(time[ix[0]]),3),'end_s':round(float(time[ix[-1]]),3),
            'matched_windows':len(indices),'span_windows':int(in_span.sum()),'valid_windows':int(valid[in_span].sum()),
            'median_band_dbfs':round(float(np.median(levels[ix])),2),
            'valid_sources':dict(Counter(es[i]['estimate'].get('delay_fit','unknown') for i in ix if valid[i]))})
    jumps=[];previous=None;run=0;longest_run=0;failed=0;longest_failed=0
    for i,e in enumerate(es):
        if valid[i]:
            run+=1;longest_run=max(longest_run,run)
            if previous is not None:
                gap=float(time[i]-time[previous]);a=es[previous]['estimate'];b=e['estimate']
                turn=abs((b['raw_angle_deg']-a['raw_angle_deg']+180)%360-180)
                if gap<.75 and turn>=60 and hits[previous:i+1].all():
                    jumps.append({'from_s':round(float(time[previous]),3),'to_s':round(float(time[i]),3),
                        'turn_deg':round(turn,2),'gap_ms':round(gap*1000,1),'from_angle':a['raw_angle_deg'],'to_angle':b['raw_angle_deg'],
                        'from_source':a.get('delay_fit'),'to_source':b.get('delay_fit'),
                        'from_sequence':es[previous]['sequence'],'to_sequence':e['sequence']})
            previous=i
        else:run=0
        failed=failed+1 if hits[i] and not valid[i] else 0;longest_failed=max(longest_failed,failed)
    packet=[e['estimate'].get('pipeline_timing',{}).get('packet_total_ms') for e in es]
    packet=[v for v in packet if v is not None and 0<v<450]
    interval=np.diff(stamp)*1000;interval=interval[(interval>0)&(interval<450)]
    quiet_level=float(np.median(levels[quiet])) if quiet.any() else None
    report={'checkpoint':trial['checkpoint'],'source_trial':str(path),'raw_checksum_verified':True,
        'protocol_correction':'Original two-loop plan abandoned by user. Several playback rounds and intentional interruptions occurred; exact times and true bearing were not recorded. Do not classify pauses as software failures.',
        'windows':len(es),'duration_s':trial['duration_s'],'start_wall_time':trial['start_wall_time'],
        'reasons':dict(Counter(e['estimate']['reason'] for e in es)),
        'matched_reasons':dict(Counter(e['estimate']['reason'] for i,e in enumerate(es) if hits[i])),
        'valid_sources':dict(Counter(e['estimate'].get('delay_fit','unknown') for i,e in enumerate(es) if valid[i])),
        'result_interval_ms':distribution(interval),'packet_ms':distribution(packet),
        'processing_ms':distribution([e['estimate'].get('processing_ms') for e in es]),
        'hardware_nonzero_dropped_or_stall':[e['sequence'] for e in es if e['health'].get('dropped') or e['health'].get('rx_stall')],
        'code_active_groups':group_rows,'direction_changes_over_60_deg_during_code_presence':jumps,
        'longest_valid_run_windows':longest_run,'longest_code_hit_invalid_run_windows':longest_failed,
        'longest_code_hit_invalid_run_approx_s':round(longest_failed*np.median(interval)/1000,3),
        'noise':{'quiet_candidate_windows':int(quiet.sum()),'quiet_candidate_median_band_dbfs':round(quiet_level,2) if quiet_level is not None else None,
            'code_matched_median_band_dbfs':round(float(np.median(levels[hits])),2) if hits.any() else None,
            'matched_to_quiet_level_difference_db':round(float(np.median(levels[hits]))-quiet_level,2) if hits.any() and quiet_level is not None else None,
            'loud_unmatched_windows':int(loud_unmatched.sum()),'loud_unmatched_band_dbfs':distribution(levels[loud_unmatched]),
            'limitation':'Quiet/noise groups are inferred from level and code presence, not synchronized phone pause markers. Levels are digital dBFS, not SPL. Unmatched energy is not automatically noise or a receiver fault.'},
        'angle_limitation':'No true bearing or movement log. Large changes are observed estimates, not proven wrong turns. No signal is blocked based on turn size.'}
    (path.parent/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with (path.parent/'time-series.csv').open('w',encoding='utf-8-sig',newline='') as output:
        writer=csv.writer(output);writer.writerow(['time_s','sequence','band_dbfs','code_channels','valid','reason','raw_angle_deg','source'])
        for i,event in enumerate(es):
            estimate=event['estimate'];writer.writerow([round(float(time[i]),3),event['sequence'],round(float(levels[i]),3),
                estimate.get('code_channels',0),estimate['valid'],estimate['reason'],estimate.get('raw_angle_deg'),estimate.get('delay_fit')])
    np.savez(path.parent/'analysis-series.npz',time_s=time,band_dbfs=levels,code_hits=hits,valid=valid,frequency_hz=f,
        matched_psd=np.mean(powers[hits],axis=0) if hits.any() else np.zeros(len(f)),
        quiet_psd=np.mean(powers[quiet],axis=0) if quiet.any() else np.zeros(len(f)),
        loud_unmatched_psd=np.mean(powers[loud_unmatched],axis=0) if loud_unmatched.any() else np.zeros(len(f)))
    if plots:
        import importlib.util,sys
        if importlib.util.find_spec('PIL') is None:
            sys.path.append(str(Path(sys.base_prefix)/'Lib/site-packages'))
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True,constrained_layout=True)
        axes[0].plot(time,levels,color='#246caa',lw=1,label='19–21 kHz received level')
        axes[0].scatter(time[hits],levels[hits],s=5,color='#209476',label='Code matched')
        axes[0].set(ylabel='Band level (dBFS)',title='RX4 phone trial — multiple rounds and deliberate interruptions')
        axes[0].legend(loc='lower right',fontsize=8)
        axes[1].step(time,[e['estimate'].get('code_channels',0) for e in es],where='mid',color='#8055a3',label='Matched microphones')
        axes[1].step(time,valid.astype(int)*7,where='mid',alpha=.5,color='#209476',label='Valid bearing (7 = yes)')
        axes[1].set(ylabel='Channels / validity',ylim=(-.3,7.6));axes[1].legend(loc='lower right',fontsize=8)
        sources=sorted(set(e['estimate'].get('delay_fit','unknown') for i,e in enumerate(es) if valid[i]))
        for source in sources:
            ix=[i for i,e in enumerate(es) if valid[i] and e['estimate'].get('delay_fit','unknown')==source]
            axes[2].scatter(time[ix],[es[i]['estimate']['raw_angle_deg'] for i in ix],s=12,label=source)
        axes[2].set(ylabel='Raw estimate (degrees)',xlabel='Time since first captured block (s)',ylim=(-5,365))
        axes[2].legend(fontsize=7,loc='upper right')
        for ax in axes:ax.grid(alpha=.2)
        fig.savefig(path.parent/'signal-and-direction.png',dpi=160);plt.close(fig)
        fig,ax=plt.subplots(figsize=(10,4.5),constrained_layout=True)
        for mask,label in [(hits,'Code matched'),(quiet,'Quiet candidates'),(loud_unmatched,'Energy present, code unmatched')]:
            if mask.any():ax.plot(f/1000,10*np.log10(np.maximum(np.median(powers[mask],axis=0),1e-20)),label=label+' (median)',lw=1)
        if loud_unmatched.any():
            ax.plot(f/1000,10*np.log10(np.maximum(np.mean(powers[loud_unmatched],axis=0),1e-20)),label='Unmatched mean, includes transients',lw=.8,ls='--',alpha=.6)
        ax.axvspan(19,21,color='#45b59b',alpha=.13,label='Selected code band')
        ax.set(xlim=(0,24),ylim=(-125,-25),xlabel='Frequency (kHz)',ylabel='Received level (dBFS / FFT bin)',title='Received spectrum — digital levels, not calibrated sound pressure')
        ax.grid(alpha=.2);ax.legend(fontsize=8)
        fig.savefig(path.parent/'received-spectrum.png',dpi=160);plt.close(fig)
        fig,ax=plt.subplots(figsize=(10,4.5),constrained_layout=True)
        for mask,label in [(hits,'Code matched'),(quiet,'Quiet candidates'),(loud_unmatched,'Energy present, code unmatched')]:
            if mask.any():ax.plot(f/1000,10*np.log10(np.maximum(np.median(powers[mask],axis=0),1e-20)),label=label+' (median)',lw=1)
        ax.axvspan(19,21,color='#45b59b',alpha=.13)
        ax.set(xlim=(18,22),ylim=(-115,-65),xlabel='Frequency (kHz)',ylabel='Received level (dBFS / FFT bin)',title='High-band detail — median spectrum limits transient bias')
        ax.grid(alpha=.2);ax.legend(fontsize=8);fig.savefig(path.parent/'high-band-spectrum.png',dpi=160);plt.close(fig)
    print(json.dumps({k:report[k] for k in ('windows','duration_s','matched_reasons','valid_sources','result_interval_ms','packet_ms','noise','direction_changes_over_60_deg_during_code_presence')},ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('trial',type=Path);parser.add_argument('--plots',action='store_true')
    args=parser.parse_args();analyze(args.trial,args.plots)
