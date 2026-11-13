"""RX4: score a shared physical delay field against complete pair curves.

Used only after the original high-band fit and arrival fallback fail. Code
presence, packet health and temporal confirmation are handled by the caller.
Coherence budgets are engineering thresholds, not calibrated probabilities.
"""
import math
import numpy as np

def fit_joint_spectral(receiver,averaged,valid_pairs):
    frequencies=np.fft.rfftfreq(4096,1/48000)[receiver.indices]
    centered=frequencies-frequencies.mean()
    if not hasattr(receiver,'_highband_delay_bank'):
        extent=math.ceil(np.linalg.norm(receiver.delta,axis=1).max()/receiver.speed*48000*1.25)+1
        grid=np.arange(-extent,extent+.0625,.125)
        bank=np.exp(-2j*np.pi*centered[:,None]*grid[None,:]/48000)
        receiver._highband_delay_bank=(grid,bank)
    grid,bank=receiver._highband_delay_bank
    cached=getattr(receiver,'_highband_pair_scores',None)
    cache_hit=(cached is not None and cached[0] is averaged and np.array_equal(cached[1],valid_pairs))
    if cache_hit:
        _,_,grid,scores,totals,amplitude=cached
    else:
        band=averaged[valid_pairs];amplitude=np.abs(band)
        totals=np.maximum(amplitude.sum(axis=1),1e-12)
        scores=np.abs(np.einsum('pf,fg->pg',band,bank,optimize=False))/totals[:,None]
    rows=[];best=[];curves=[];spreads=[]
    for row,pair in enumerate(valid_pairs):
        allowed=np.abs(grid)<=np.linalg.norm(receiver.delta[pair])/receiver.speed*48000*1.25+.25
        peak=float(scores[row,allowed].max())
        support=float(totals[row]**2/max(np.sum(amplitude[row]**2),1e-12))
        spread=peak-float(scores[row,allowed].min())
        if peak<.60 or support<32 or spread<.012:continue
        rows.append(int(pair));best.append(float(scores[row].max()));curves.append(scores[row]);spreads.append(spread)
    details={'delay_fit':'joint_spectral_delay_consensus','joint_spectral_pairs':len(rows),
             'joint_score_cache_reused':bool(cache_hit)}
    if len(rows)<max(6,math.ceil(len(valid_pairs)/2)):
        return None,0,{**details,'group_delay_reason':'insufficient_joint_spectral_pairs'}
    rows=np.array(rows);best=np.array(best)
    # Geometry constrains all pair delays BEFORE scores are combined. No
    # independent pair argmax is projected into a fabricated consistent set.
    if not hasattr(receiver,'_joint_spectral_geometry'):
        angles=np.arange(0,360,2.)
        # Include nonphysical guard radii so a maximum outside the allowed
        # range is rejected rather than forced onto a physical boundary.
        projection=np.arange(0.,1.6001,.05)
        rad=np.radians(angles)
        unit=np.stack((np.sin(rad),np.cos(rad)),axis=1)
        vectors=(projection[:,None,None]*unit[None,:,:]).reshape(-1,2)
        lags=vectors@receiver.delta.T*48000/receiver.speed
        receiver._joint_spectral_geometry=(angles,projection,vectors,lags)
    angles,projection,vectors,lags=receiver._joint_spectral_geometry
    predicted=np.array([np.interp(lags[:,p],grid,curve) for p,curve in zip(rows,curves)])
    weights=best**4
    aggregate=np.average(predicted,axis=0,weights=weights)
    index=int(aggregate.argmax());vector=vectors[index];angle=float(math.degrees(math.atan2(vector[0],vector[1]))%360)
    angular=aggregate.reshape(len(projection),len(angles)).max(axis=0)
    distance=np.abs((angles-angle+180)%360-180)
    winner=float(aggregate[index]);peak=float(np.average(best,weights=weights))
    loss=peak-winner
    margin=winner-float(angular[distance>=45].max())
    opposite=winner-float(angular[distance>=120].max())
    support_channels=len(set(int(ch) for p in rows for ch in receiver.pairs[p]))
    details.update(joint_spectral_coherence=round(winner,5),joint_unconstrained_coherence=round(peak,5),
        joint_coherence_loss=round(loss,5),joint_margin_45_deg=round(margin,5),
        joint_opposite_margin=round(opposite,5),joint_channels=support_channels,
        horizontal_projection=round(float(np.linalg.norm(vector)),4),candidate_angle_deg=round(angle,2),
        joint_pair_coherence_min=round(float(predicted[:,index].min()),5))
    budget=min(.02,max(.002,1.5*(1-peak)))
    details['joint_loss_budget']=round(budget,5)
    quality=winner*math.exp(-.5*(loss/budget)**2)
    norm=float(np.linalg.norm(vector))
    checks={'six_channels':support_channels>=6,'twelve_pairs':len(rows)>=12,
            'physical_projection':.25<=norm<=1.30001,'mean_coherence':winner>=.94,
            'bounded_spectral_loss':loss<=budget,'current_frame_peak_separation':margin>=.005,
            'current_frame_opposite_separation':opposite>=.01,
            'worst_pair_coherence':predicted[:,index].min()>=.80}
    details['joint_rejections']=[name for name,passed in checks.items() if not passed]
    details['joint_pair_diagnostics']=[{'pair':[('D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER')[ch] for ch in receiver.pairs[p]],
        'phase_delay_samples':round(float(lags[index,p]),4),
        'coherence_at_model':round(float(predicted[i,index]),5),
        'independent_best_coherence':round(float(best[i]),5)} for i,p in enumerate(rows)]
    # Arrival-time gauge: center microphone = 0; phase delay uses the opposite sign.
    arrivals={}
    names=('D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER')
    for ch,name in enumerate(names):
        if ch==6:arrivals[name]=0.
        else:
            pair=int(np.flatnonzero((receiver.pairs[:,0]==ch)&(receiver.pairs[:,1]==6))[0])
            arrivals[name]=round(-float(lags[index,pair]),4)
    details['joint_relative_arrival_samples']=arrivals
    if not all(checks.values()):
        return None,quality,{**details,'group_delay_reason':'joint_spectral_evidence_weak'}
    return angle,quality,details
