"""Stage 1: 16-18 kHz known-code reception; no hardware gain/latency claims.

Partial spectral whitening reduces narrow electronic tones and response tilt.
Delay fitting uses a bounded complex phase-ramp search with a free intercept,
so the 17 kHz carrier phase does not choose a spatially aliased direction.
Only the new profile uses this module. The audible/20-22 kHz paths are intact.
"""
import json
import math
import time
import numpy as np

RATE=48000
SIZE=4096
CHANNELS=('D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER')
PNR_MIN=12.5
CONCENTRATION_MIN=.12
MIN_CHANNELS=4

PROBE_FREQUENCIES=(1000,16000,17000,17500,18000)

def probe_levels(samples=None,spectra=None):
    """Median channel RMS in +/-150 Hz windows, dBFS; no gain or SPL claim.

    Diagnostic windows respond to pure tones independently of code acceptance.
    Reuse the capture FFT when the high-band receiver has it.
    """
    if spectra is None:
        audio=np.asarray(samples,dtype=np.float64)
        if audio.shape!=(SIZE,7) or not np.all(np.isfinite(audio)):
            return {}
        spectra=np.fft.rfft(audio-audio.mean(axis=0),axis=0).T
    frequencies=np.fft.rfftfreq(SIZE,1/RATE)
    levels={}
    for hz in PROBE_FREQUENCIES:
        bins=np.abs(frequencies-hz)<=150
        rms=np.sqrt(2*np.sum(np.abs(spectra[:,bins])**2,axis=1))/SIZE
        levels[str(hz)]=round(float(np.median(20*np.log10(np.maximum(rms,1e-9)/32768))),1)
    return levels


def reset(receiver):
    receiver.history.clear()
    receiver.confirmations=0
    receiver.candidate=None
    receiver.smoothed=None
    receiver.last_valid_time=0


def fit_delays(receiver,averaged,valid_pairs):
    frequencies=np.fft.rfftfreq(SIZE,1/RATE)[receiver.indices]
    centered=frequencies-frequencies.mean()
    if not hasattr(receiver,'_highband_delay_bank'):
        extent=math.ceil(np.linalg.norm(receiver.delta,axis=1).max()/receiver.speed*RATE*1.25)+1
        grid=np.arange(-extent,extent+.0625,.125)
        bank=np.exp(-2j*np.pi*centered[:,None]*grid[None,:]/RATE)
        receiver._highband_delay_bank=(grid,bank)
    grid,bank=receiver._highband_delay_bank
    band=averaged[valid_pairs]
    weights=np.abs(band)
    totals=np.maximum(weights.sum(axis=1),1e-12)
    # einsum has predictable small-matrix cost without spawning BLAS workers.
    scores=np.abs(np.einsum('pf,fg->pg',band,bank,optimize=False))/totals[:,None]
    delays=[];rows=[];pair_weights=[];coherences=[]
    for row,pair in enumerate(valid_pairs):
        allowed=np.abs(grid)<=np.linalg.norm(receiver.delta[pair])/receiver.speed*RATE*1.25+.25
        curve=np.where(allowed,scores[row],-1.)
        index=int(curve.argmax());coherence=float(curve[index])
        support=float(totals[row]**2/max(np.sum(weights[row]**2),1e-12))
        spread=coherence-float(np.min(curve[allowed]))
        if coherence<.60 or support<32 or spread<.012:
            continue
        lag=float(grid[index])
        if 0<index<len(grid)-1 and allowed[index-1] and allowed[index+1]:
            a,b,c=scores[row,index-1:index+2]
            curvature=a-2*b+c
            if curvature<0:lag+=float(np.clip(.5*(a-c)/curvature,-1,1))*.125
        delays.append(lag*receiver.speed/RATE)
        rows.append(receiver.delta[pair])
        pair_weights.append(coherence**4)
        coherences.append(coherence)
    count=len(rows)
    details={'group_delay_pairs':count,'delay_fit':'bounded_complex_coherence',
             'median_pair_coherence':round(float(np.median(coherences)),3) if count else 0}
    if count<max(6,math.ceil(len(valid_pairs)/2)):
        return None,0,{**details,'group_delay_reason':'insufficient_group_delays'}
    matrix=np.array(rows);target=np.array(delays);weights=np.array(pair_weights)
    robust=weights.copy()
    for _ in range(4):
        vector=np.linalg.lstsq(matrix*np.sqrt(robust[:,None]),target*np.sqrt(robust),rcond=None)[0]
        residual=(matrix@vector-target)*RATE/receiver.speed
        robust=weights*np.minimum(1,.65/np.maximum(np.abs(residual),1e-9))
    # Trim no more than 20% of pairs, then report BOTH retained and all-pair
    # residuals. This prevents one poor microphone pair dominating a weak trial
    # without allowing the fit to silently discard most contradictory evidence.
    keep=np.ones(count,dtype=bool)
    if count>=10:
        keep[np.argsort(np.abs(residual))[-int(count*.2):]]=False
        vector=np.linalg.lstsq(matrix[keep]*np.sqrt(weights[keep,None]),
                               target[keep]*np.sqrt(weights[keep]),rcond=None)[0]
        residual=(matrix@vector-target)*RATE/receiver.speed
    all_rms=float(np.sqrt(np.sum(weights*residual**2)/np.sum(weights)))
    rms=float(np.sqrt(np.sum(weights[keep]*residual[keep]**2)/np.sum(weights[keep])))
    projection=float(np.linalg.norm(vector))
    raw=float(np.degrees(np.arctan2(vector[0],vector[1]))%360)
    quality=float(np.median(coherences))*math.exp(-.5*(rms/.9)**2)*int(keep.sum())/len(valid_pairs)
    details.update(group_delay_rms_samples=round(rms,4),all_pair_rms_samples=round(all_rms,4),
                   retained_delay_pairs=int(keep.sum()),horizontal_projection=round(projection,4),
                   candidate_angle_deg=round(raw,2))
    if not .25<=projection<=1.3 or rms>1.0 or all_rms>1.5 or quality<.48:
        return None,quality,{**details,'group_delay_reason':'geometry_mismatch'}
    return raw,quality,details


def estimate_highband(receiver,samples,health,now=None):
    started=time.perf_counter()
    now=time.monotonic() if now is None else now
    base={'valid':False,'frequency':17000,'profile':'coded-16-18',
          'method':'coded_matched_filter_highband_delay','received_at':now,'stage':'HF1',
          'band_low_hz':16000,'band_high_hz':18000}
    telemetry={}
    def finish(reason,**details):
        return {**base,'reason':reason,'processing_ms':round((time.perf_counter()-started)*1000,2),**details},telemetry
    if health.get('dropped',0) or health.get('rx_stall',0):
        reset(receiver);return finish('capture_gap')
    audio=np.asarray(samples,dtype=np.float64)
    if audio.shape!=(SIZE,7) or not np.all(np.isfinite(audio)):
        reset(receiver);return finish('invalid_raw_audio')
    if np.any(np.abs(audio)>=32760):
        reset(receiver);return finish('clipping')
    audio=audio-audio.mean(axis=0)
    spectra=np.fft.rfft(audio,axis=0).T
    base['probe_bands_dbfs']=probe_levels(spectra=spectra)
    band=spectra[:,receiver.indices]
    magnitude=np.abs(band)
    rms=np.sqrt(2*np.sum(magnitude**2,axis=1))/SIZE
    level=20*np.log10(np.maximum(rms,1e-9)/32768)
    # Bounded, partial whitening: cap narrow spectral spikes while preserving
    # phase and keeping gain finite in spectral nulls. RMS remains UNAMPLIFIED.
    reference=np.maximum(np.median(magnitude,axis=1,keepdims=True),1e-9)
    whitening=(reference/np.maximum(magnitude,reference*.12))**.65
    whitening=np.clip(whitening,.025,3.)
    matched=np.zeros((7,SIZE),dtype=np.complex128)
    matched[:,receiver.indices]=band*np.conj(receiver.spectrum[receiver.indices])*whitening
    impulse=np.fft.ifft(matched,axis=1)
    envelope=np.abs(impulse)
    positions=np.arange(SIZE)
    width=max(16,round(2*RATE/2000))
    pnr=[];concentrations=[];present=[]
    for ch,name in enumerate(CHANNELS):
        peak=int(envelope[ch].argmax())
        distance=np.minimum((positions-peak)%SIZE,(peak-positions)%SIZE)
        noise=np.sqrt(np.mean(envelope[ch,distance>width]**2))
        ratio=float(20*np.log10(max(envelope[ch,peak],1e-12)/max(noise,1e-12)))
        fraction=float(np.sum(envelope[ch,distance<=width]**2)/max(np.sum(envelope[ch]**2),1e-12))
        hit=bool(ratio>=PNR_MIN and fraction>=CONCENTRATION_MIN and rms[ch]>=.25)
        pnr.append(ratio);concentrations.append(fraction);present.append(hit)
        telemetry[name]={'frequency':17000,'rms':round(float(rms[ch]),2),'band_dbfs':round(float(level[ch]),1),
                         'ratio':round(fraction,4),'snr_db':round(ratio,2),'present':hit}
    hits=int(sum(present))
    details={'code_channels':hits,'code_pnr_db':round(float(np.median(pnr)),2),
             'code_concentration':round(float(np.median(concentrations)),3),
             'band_rms16':round(float(np.median(rms)),3),'band_level_dbfs':round(float(np.median(level)),1),
             'receiver_pnr_threshold_db':PNR_MIN,'receiver_gain_is_hardware':False}
    if hits<MIN_CHANNELS:
        reset(receiver);return finish('beacon_not_detected',**details)
    normalized=envelope/np.maximum(envelope.max(axis=1,keepdims=True),1e-12)
    center=int(np.mean(normalized[np.array(present)],axis=0).argmax())
    distance=np.minimum((positions-center)%SIZE,(center-positions)%SIZE)
    gate=np.where(distance<96,.5+.5*np.cos(np.pi*np.minimum(distance,96)/96),0)
    isolated=np.fft.fft(impulse*gate,axis=1)[:,:SIZE//2+1]
    left,right=receiver.pairs.T
    cross=isolated[left][:,receiver.indices]*np.conj(isolated[right][:,receiver.indices])
    amplitude=np.abs(cross)
    reliability=np.minimum(1,amplitude/np.maximum(np.median(amplitude,axis=1,keepdims=True),1e-12))
    pair_valid=np.array(present)[left]&np.array(present)[right]
    weighted=cross/np.maximum(amplitude,1e-12)*reliability*receiver.weights[None,:]*pair_valid[:,None]
    while receiver.history and now-receiver.history[0][0]>.75:
        receiver.history.popleft()
    receiver.history.append((now,weighted))
    # Two bursts for strong code, at most three for weak code. No long accumulator.
    count=2 if hits>=6 and details['code_pnr_db']>=20 else 3
    history=list(receiver.history)[-count:]
    averaged=sum(row[1] for row in history)/len(history)
    valid_pairs=np.flatnonzero(pair_valid)
    details.update(channels=hits,pairs=len(valid_pairs),averaged_bursts=len(history))
    raw,quality,fit=fit_delays(receiver,averaged,valid_pairs)
    details.update(fit)
    if raw is None:
        receiver.confirmations=0
        return finish('group_delay_inconsistent',**details)
    difference=abs((raw-(receiver.candidate if receiver.candidate is not None else raw)+180)%360-180)
    receiver.confirmations=receiver.confirmations+1 if difference<=20 and now-receiver.last_candidate_time<.75 else 1
    receiver.candidate=raw;receiver.last_candidate_time=now
    if receiver.confirmations<2:return finish('confirming_beacon_direction',**details)
    config=json.loads(receiver.path.read_text(encoding='utf-8-sig'))
    angle=((-1 if config['mirror_view'] else 1)*raw+config['heading_offset_deg'])%360
    vector=complex(math.sin(math.radians(angle)),math.cos(math.radians(angle)))
    smoothing=.18 if count==2 else .28
    if receiver.smoothed is not None and now-receiver.last_valid_time<.75:
        alpha=1-math.exp(-max(.001,now-receiver.last_valid_time)/smoothing)
        vector=receiver.smoothed*(1-alpha)+vector*alpha
    vector/=max(abs(vector),1e-12)
    receiver.smoothed=vector;receiver.last_valid_time=now
    return finish('estimated',valid=True,angle_deg=round(math.degrees(math.atan2(vector.real,vector.imag))%360,2),
                  raw_angle_deg=raw,confidence=round(quality,3),heading_calibrated=config['heading_calibrated'],
                  motion_smoothing_s=smoothing,**details)
