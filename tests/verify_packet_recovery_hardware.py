"""Inject host-side faults into live Pico reads, never write altered firmware/audio.

Requires exclusive access to the Pico port. Does not play sound or change GPIO.
"""
import argparse
import json
from pathlib import Path
import queue
import sys
import time
import serial

PROJECT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output-folder',type=Path,default=PROJECT/'stages/06-joint-delay')
args=parser.parse_args()
sys.path.insert(0,str(PROJECT/'SEN0325-Pico-Setup'))
from sen0325_launcher import Session

OriginalSerial=serial.Serial
injections=[]


class FaultSerial(OriginalSerial):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.requests=0;self.flip_done=False;self.stall_done=False;self.stall_until=0

    def write(self,data):
        if data==b'RECORD\n':self.requests+=1
        if data==b'STOP\n':self.stall_until=0
        return super().write(data)

    def read(self,size=1):
        if size>10000 and self.requests==10 and not self.stall_done:
            self.stall_done=True;self.stall_until=time.perf_counter()+.75
            injections.append({'type':'host_payload_stall','request':self.requests,'perf_counter':time.perf_counter()})
        if size>10000 and time.perf_counter()<self.stall_until:
            time.sleep(.02)
            return b''
        data=super().read(size)
        if size>10000 and data and self.requests==3 and not self.flip_done:
            self.flip_done=True
            data=bytes([data[0]^1])+data[1:]
            injections.append({'type':'host_crc_bit_flip','request':self.requests,'perf_counter':time.perf_counter()})
        return data


serial.Serial=FaultSerial
session=Session();session.set_mode('coded-20');session.start()
deadline=time.monotonic()+12
try:
    while time.monotonic()<deadline:
        try:
            kind,value=session.events.get(timeout=.2)
            if kind=='status':print(value,flush=True)
        except queue.Empty:pass
finally:
    session.stop.set();session.thread.join(timeout=10)
    serial.Serial=OriginalSerial
assert not session.thread.is_alive()
with session.log_path.open('a',encoding='utf-8') as log:
    while not session.notes.empty():log.write('# EVENT '+json.dumps(session.notes.get_nowait())+'\n')
lines=session.log_path.read_text(encoding='utf-8').splitlines()
packets=[json.loads(l[9:]) for l in lines if l.startswith('# PACKET ')]
errors=[json.loads(l[15:]) for l in lines if l.startswith('# PACKET_ERROR ')]
recoveries=[json.loads(l[11:]) for l in lines if l.startswith('# RECOVERY ')]
assert [e['error'] for e in errors]==['crc_mismatch','short_payload'],errors
assert len(recoveries)==2 and all(r['recovered'] for r in recoveries),recoveries
assert len(packets)>=15
for error in errors:
    detected=error['request_perf_counter']+error['packet_total_ms']/1000
    following=next(p for p in packets if p['request_perf_counter']>detected)
    error['detected_to_next_valid_packet_ms']=round((following['packet_done_perf_counter']-detected)*1000,3)
assert all(e['detected_to_next_valid_packet_ms']<1600 for e in errors),errors
assert not any(l.startswith('ERROR:') for l in lines),lines[-10:]
banner=next((l for l in lines if l.startswith('SEN0325_SETUP ')),None)
result={'passed':True,'hardware':'connected Pico; host-side faults only','firmware_banner':banner,
    'injections':injections,'accepted_packets':len(packets),'errors':errors,'recoveries':recoveries,
    'bad_packets_suppressed':len(errors),'worker_stopped':True,'audio_played':False,
    'log':str(session.log_path),'limits':'Injected host faults validate recovery, not the cause of historical USB anomalies or physical bearing accuracy.'}
args.output_folder.mkdir(exist_ok=True)
(args.output_folder/'hardware-recovery-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
