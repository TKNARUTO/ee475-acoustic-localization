"""HF1.1: fit a common coded arrival without combining separate echoes."""
import math
import numpy as np

def fit_arrivals(receiver,envelope,present):
    size=envelope.shape[1]
    normalized=envelope/np.maximum(envelope.max(axis=1,keepdims=True),1e-12)
    active=np.flatnonzero(present)
    center=int(normalized[active].mean(axis=0).argmax())
    config=receiver.geometry_for_arrivals
    radius=config['radius_m'];speed=config['sound_speed_m_s']
    coordinates=[]
    for name in receiver.arrival_channels:
        angle=math.radians(config['clockwise_degrees_from_U7_M0'].get(name,0))
        coordinates.append((0,0) if name=='D3R_CENTER' else (radius*math.sin(angle),radius*math.cos(angle)))
    matrix=np.column_stack((np.array(coordinates)*48000/speed,np.ones(7)))
    span=radius*48000/speed*1.3+2
    candidates=[];origins=[]
    for ch,row in enumerate(normalized):
        peaks=np.flatnonzero((row>np.roll(row,1))&(row>=np.roll(row,-1))&(row>=.45)) if present[ch] else []
        values=[]
        for peak in peaks:
            relative=float((peak-center+size/2)%size-size/2)
            if abs(relative)>96:continue
            a,b,c=np.log(np.maximum(row[(peak+np.array([-1,0,1]))%size],1e-12))
            offset=float(np.clip(.5*(a-c)/(a-2*b+c),-.5,.5)) if abs(a-2*b+c)>1e-12 else 0
            values.append((relative+offset,float(row[peak])))
            origins.append(relative+offset)
        candidates.append(values)
    fits=[];seen=set();rejected={};evaluated=0
    def reject(reason):rejected[reason]=rejected.get(reason,0)+1
    for origin in origins:
        selected=[]
        for ch,values in enumerate(candidates):
            nearby=[(i,p) for i,p in enumerate(values) if abs(p[0]-origin)<=span]
            if nearby:
                index,peak=min(nearby,key=lambda item:abs(item[1][0]-origin))
                selected.append((ch,index,*peak))
        signature=tuple((r[0],r[1]) for r in selected)
        if signature in seen:continue
        seen.add(signature)
        evaluated+=1
        if len(selected)<5:reject('fewer_than_five_channels');continue
        channels=np.array([r[0] for r in selected])
        target=-np.array([r[2] for r in selected])
        weights=np.array([r[3]**2 for r in selected])
        design=matrix[channels]
        if np.linalg.matrix_rank(design)<3:reject('rank_deficient');continue
        keep=np.ones(len(selected),bool)
        for attempt in range(2):
            w=weights[keep]
            solution=np.linalg.lstsq(design[keep]*np.sqrt(w[:,None]),target[keep]*np.sqrt(w),rcond=None)[0]
            residual=design@solution-target
            if attempt==0 and len(selected)>=6 and np.max(np.abs(residual))>1.5:
                keep[np.argmax(np.abs(residual))]=False
            else:break
        norm=float(np.linalg.norm(solution[:2]))
        rms=float(np.sqrt(np.average(residual[keep]**2,weights=weights[keep])))
        all_rms=float(np.sqrt(np.average(residual**2,weights=weights)))
        support=int(keep.sum());strength=float(np.median(np.sqrt(weights[keep])))
        # The fit must contain actual local maxima on >=5 microphones, not
        # arbitrary points sampled from the broad matched-filter envelopes.
        if support<5:reject('insufficient_retained_channels');continue
        if not .25<=norm<=1.3:reject('projection');continue
        if rms>.9:reject('retained_rms');continue
        if all_rms>2.0:reject('all_channel_rms');continue
        if strength<.55:reject('weak_cluster');continue
        raw=math.degrees(math.atan2(solution[0],solution[1]))%360
        quality=min(1,support/6)*strength*math.exp(-.5*(rms/1.25)**2)
        if quality<.48:reject('quality');continue
        fits.append({'raw':raw,'quality':quality,'arrival_center_samples':-float(solution[2]),
                     'arrival_channels':support,'arrival_selected_channels':len(selected),
                     'arrival_rms_samples':round(rms,4),'arrival_all_rms_samples':round(all_rms,4),
                     'arrival_strength':round(strength,3),'horizontal_projection':round(norm,4),
                     'arrival_channel_names':[receiver.arrival_channels[ch] for ch,k in zip(channels,keep) if k],
                     'arrival_channel_diagnostics':[{'channel':receiver.arrival_channels[ch],
                         'relative_peak_samples':round(float(-target[i]),4),
                         'residual_samples':round(float(residual[i]),4),'retained':bool(keep[i])}
                         for i,ch in enumerate(channels)]})
    details={'delay_fit':'coded_envelope_arrival_consensus','arrival_candidate_fits':len(fits),
             'arrival_clusters_evaluated':evaluated,'arrival_rejection_counts':rejected,
             'arrival_peak_counts':{name:len(peaks) for name,peaks in zip(receiver.arrival_channels,candidates)}}
    if not fits:return None,0,{**details,'group_delay_reason':'no_consistent_arrival_cluster'}
    # Prefer the earliest well-supported lobe, rather than mixing a strong
    # later reflection from one microphone with direct arrivals from others.
    maximum_support=max(f['arrival_channels'] for f in fits)
    plausible=[f for f in fits if f['arrival_channels']>=max(5,maximum_support-1)]
    best=min(plausible,key=lambda f:(f['arrival_center_samples'],-f['quality']))
    raw=best.pop('raw');quality=best.pop('quality')
    return raw,quality,{**details,**best,'candidate_angle_deg':round(raw,2)}
