"""RX2 live receiver-only benchmark. Requires exclusive Pico port access."""
import argparse
from collections import Counter
import json
from pathlib import Path
import queue
import sys
import time
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
APP=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/06-joint-delay'
sys.path.insert(0,str(APP))
from sen0325_launcher import Session


def stats(values):
    return dict(zip(('median','p95','max'),[round(float(v),3) for v in
        (np.median(values),np.percentile(values,95),max(values))])) if values else None


def summarize(path):
    packets=[];timings={};estimates=[];renders=[];errors=[];cancels=[];outer_errors=[];headers=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('# PACKET '):packets.append(json.loads(line[9:]))
        elif line.startswith('AUDIO frames='):
            fields=dict(token.split('=',1) for token in line.split()[1:]);headers.append(fields)
        elif line.startswith('AUDIO_TIMING '):
            fields=dict(token.split('=',1) for token in line.split()[1:])
            fields={k:int(v) for k,v in fields.items()};timings[fields['seq']]=fields
        elif line.startswith('# PACKET_ERROR '):errors.append(json.loads(line[15:]))
        elif line.startswith('# PACKET_CANCEL '):cancels.append(json.loads(line[16:]))
        elif line.startswith('ERROR:'):outer_errors.append(line)
        elif line.startswith('# EVENT '):
            event=json.loads(line[8:])
            if event['event']=='beacon_estimate':estimates.append(event)
            elif event['event']=='direction_render':renders.append(event)
    steady=[p for p in packets if p['packet_total_ms']<450]
    seqs={p['seq'] for p in steady}
    device=[row for seq,row in timings.items() if seq in seqs and row['capture_us']<450000]
    metrics={k:stats([p[k] for p in steady]) for k in
             ('header_wait_ms','payload_read_ms','crc_check_ms','packet_total_ms')}
    metrics.update({'device_'+k.replace('_us','_ms'):stats([r[k]/1000 for r in device])
                    for k in ('capture_us','crc_us','tx_us')})
    estimates=[e for e in estimates if e.get('pipeline_timing',{}).get('seq') in seqs]
    for k in ('dsp_ms','postprocess_ms'):
        metrics[k]=stats([e['pipeline_timing'][k] for e in estimates])
    metrics['request_to_queue_ms']=stats([e['request_to_queue_ms'] for e in estimates])
    for k in ('request_to_draw_ms','queue_to_draw_ms'):
        metrics[k]=stats([r[k] for r in renders if r.get('packet_seq') in seqs])
    intervals=[]
    for a,b in zip(steady,steady[1:]):
        if b['seq']==a['seq']+1:
            intervals.append((b['request_perf_counter']-a['request_perf_counter'])*1000)
    configs=sorted({(r['fifo'],r['ep']) for r in device})
    result={'log':str(path),'packets':len(packets),'steady_packets':len(steady),
        'matched_device_timings':len(device),'usb_configs':configs,'metrics_ms':metrics,
        'request_interval_ms':stats(intervals),'errors':errors,'outer_errors':outer_errors,
        'expected_cancellations':len(cancels),'reasons':dict(Counter(e.get('reason') for e in estimates)),
        'hardware_health':{k:max((int(h[k]) for h in headers),default=None)
                           for k in ('dropped','rx_stall','process_us')},
        'render_count':len(renders),'limits':'Ambient transport timing; not phone-to-correct-bearing latency.'}
    if intervals:result['capture_rate_hz']=round(1000/np.median(intervals),3)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--name',required=True)
    parser.add_argument('--packets',type=int,default=100)
    parser.add_argument('--log',type=Path)
    args=parser.parse_args()
    if args.log:result=summarize(args.log)
    else:
        session=Session();session.set_mode('coded-20');session.start()
        deadline=time.monotonic()+55
        while session.raw_bursts<args.packets and time.monotonic()<deadline:
            try:
                kind,value=session.events.get(timeout=.15)
                if kind=='status':print(value,flush=True)
            except queue.Empty:pass
        session.stop.set();session.thread.join(timeout=12)
        assert not session.thread.is_alive(),'Worker failed to stop'
        with session.log_path.open('a',encoding='utf-8') as log:
            while not session.notes.empty():log.write('# EVENT '+json.dumps(session.notes.get_nowait())+'\n')
        result=summarize(session.log_path)
        assert result['packets']>=args.packets,result
        assert not result['errors'] and not result['outer_errors'],result
    STAGE.mkdir(exist_ok=True)
    (STAGE/(args.name+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
