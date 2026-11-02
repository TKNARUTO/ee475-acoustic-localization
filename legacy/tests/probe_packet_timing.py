"""Bounded receiver-only hardware timing run; no audio output or calibration."""
import argparse
from collections import Counter
import json
from pathlib import Path
import queue
import sys
import time
import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
APP = PROJECT / 'SEN0325-Pico-Setup'
sys.path.insert(0, str(APP))
from sen0325_launcher import Session


def summarize(log_path):
    packets, estimates, errors, renders = [], [], [], []
    for line in log_path.read_text(encoding='utf-8').splitlines():
        if line.startswith('# PACKET '): packets.append(json.loads(line[9:]))
        if line.startswith('# PACKET_ERROR '): errors.append(json.loads(line[15:]))
        if line.startswith('# EVENT '):
            event = json.loads(line[8:])
            if event['event'] == 'beacon_estimate': estimates.append(event)
            if event['event'] == 'direction_render': renders.append(event)

    def stats(values):
        return {k: round(float(v), 3) for k, v in zip(('median', 'p95', 'max'),
                (np.median(values), np.percentile(values, 95), max(values)))} if values else None

    steady = [p for p in packets if p['packet_total_ms'] < 450]
    metrics = {key: stats([p[key] for p in steady if key in p]) for key in (
        'command_write_ms', 'header_wait_ms', 'payload_read_ms', 'crc_check_ms',
        'trailer_wait_ms', 'packet_total_ms')}
    metrics.update({key: stats([p['pipeline_timing'][key] for p in estimates])
                    for key in ('dsp_ms', 'postprocess_ms')})
    metrics['request_to_queue_ms'] = stats([e['request_to_queue_ms'] for e in estimates])
    for key in ('queue_to_draw_ms', 'request_to_draw_ms'):
        metrics[key] = stats([r[key] for r in renders])
    intervals = np.diff([p['request_perf_counter'] for p in packets]) * 1000
    seqs = [p['seq'] for p in packets]
    return {'log': str(log_path), 'packets': len(packets), 'steady_packets': len(steady),
        'errors': errors, 'first_packet': packets[0] if packets else None,
        'seq_discontinuities': sum(b != a+1 for a,b in zip(seqs, seqs[1:])),
        'dropped_max': max((e.get('dropped', 0) for e in estimates), default=None),
        'reasons': dict(Counter(e.get('reason') for e in estimates)),
        'metrics_ms': metrics, 'request_interval_ms': stats(intervals.tolist()),
        'read_sizes': dict(Counter(tuple(p['payload_read_sizes']) for p in packets)),
        'render_count': len(renders)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=float, default=35)
    parser.add_argument('--name', default='host-baseline')
    parser.add_argument('--log', type=Path)
    args = parser.parse_args()
    if args.log:
        result = summarize(args.log)
    else:
        session = Session()
        session.set_mode('coded-20')
        session.start()
        deadline = time.monotonic()+args.seconds
        while time.monotonic() < deadline:
            try:
                kind, value = session.events.get(timeout=.2)
                if kind == 'status': print(value, flush=True)
            except queue.Empty: pass
        session.stop.set()
        session.thread.join(timeout=12)
        if session.thread.is_alive(): raise RuntimeError('Worker did not stop')
        # Preserve the final queued event after stream's loop exits.
        with session.log_path.open('a', encoding='utf-8') as log:
            while not session.notes.empty():
                log.write('# EVENT '+json.dumps(session.notes.get_nowait())+'\n')
        result = summarize(session.log_path)
        result['worker_stopped'] = True
    # JSON mapping keys must be strings.
    result['read_sizes'] = {str(k): v for k,v in result['read_sizes'].items()}
    folder = PROJECT / 'stages/03-packet-timing'
    folder.mkdir(exist_ok=True)
    (folder/(args.name+'.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
