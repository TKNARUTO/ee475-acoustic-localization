"""Fault injection for binary framing, checksums and diagnostic categories."""
import json
from pathlib import Path
import sys
import zlib

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT/'SEN0325-Pico-Setup'))
from raw_packet import receive_packet, PacketError, stop_and_resynchronize

PAYLOAD = bytes(range(256)) * 224  # Includes LF, CR, NUL and all byte values.
assert len(PAYLOAD) == 57344
CRC = zlib.crc32(PAYLOAD)


class FakeSerial:
    def __init__(self, *, data=PAYLOAD, crc=CRC, seq=1, trailer=b'AUDIO_END seq=1\n',
                 fragment=57344, no_header=False, bad_shape=False):
        self.now = 0.
        self.data = bytearray(data)
        self.fragment = fragment
        header = (f'AUDIO frames={2048 if bad_shape else 4096} fs=48000 channels=7 bytes=57344 '
                  f'seq={seq} dropped=0 rx_stall=0 process_us=4000 crc32={crc:08x}\n').encode()
        self.lines = [] if no_header else [b'RAW_STARTED frames=4096 channels=7\n', header, b'\n', trailer]

    @property
    def in_waiting(self): return len(self.data)

    def readline(self):
        self.now += .01
        return self.lines.pop(0) if self.lines else b''

    def read(self, count):
        self.now += .01
        count = min(count, self.fragment, len(self.data))
        result = bytes(self.data[:count]); del self.data[:count]
        return result


checks = []


def read(fake):
    return receive_packet(fake, lambda: None, lambda line: None,
                          clock=lambda: fake.now, header_timeout=.08,
                          payload_timeout=.6, trailer_timeout=.06)


for fragment in (57344, 4096, 2048):
    packet = read(FakeSerial(fragment=fragment))
    assert packet.data == PAYLOAD
    assert packet.timing['actual_crc32'] == f'{CRC:08x}'
    assert packet.timing['received_bytes'] == len(PAYLOAD)
    assert packet.timing['payload_read_calls'] == (len(PAYLOAD)+fragment-1)//fragment
    assert all(packet.timing[k] >= 0 for k in ('header_wait_ms','payload_read_ms','crc_check_ms','trailer_wait_ms'))
    checks.append(f'complete_binary_payload_fragment_{fragment}')

for category, arguments in (
    ('short_payload', {'data': PAYLOAD[:-11]}),
    ('crc_mismatch', {'crc': CRC ^ 1}),
    ('trailer_mismatch', {'trailer': b'AUDIO_END seq=2\n'}),
    ('trailer_timeout', {'trailer': b''}),
    ('header_timeout', {'no_header': True}),
    ('header_format', {'bad_shape': True}),
):
    try: read(FakeSerial(**arguments))
    except PacketError as exc:
        assert exc.category == category, (category, exc.details)
        assert exc.details['error'] == category
        if category == 'short_payload': assert exc.details['received_bytes'] == len(PAYLOAD)-11
        if category == 'crc_mismatch':
            assert exc.details['received_bytes'] == len(PAYLOAD)
            assert exc.details['actual_crc32'] != exc.details['expected_crc32']
    else: raise AssertionError(f'{category} was not rejected')
    checks.append(category)

# Header/trailer may be fragmented across serial timeout boundaries.
fake=FakeSerial()
header=fake.lines[1];trailer=fake.lines[-1]
fake.lines=[fake.lines[0],header[:43],header[43:],b'\n',trailer[:8],trailer[8:]]
assert read(fake).data==PAYLOAD
assert fake.timeout is None
checks.append('partial_header_and_trailer_accumulated')

fake=FakeSerial();fake.timeout=.15
try:
 receive_packet(fake,lambda:None,lambda line:None,clock=lambda:fake.now,cancelled=lambda:fake.now>=.03)
except PacketError as exc:
 assert exc.category=='capture_cancelled' and fake.timeout==.15
else:raise AssertionError('Cancellation was ignored')
checks.append('cancellation_and_timeout_restoration')

fake=FakeSerial(data=PAYLOAD[:12000]+b'\nAUDIO_END seq=1\n')
fake.timeout=.15
recovery=stop_and_resynchronize(fake,lambda:fake.data.extend(b'STOPPED; clocks LOW\n'),clock=lambda:fake.now)
assert recovery['recovered'] and fake.timeout==.15
checks.append('resynchronize_after_binary_remainder')
fake=FakeSerial(data=b'\nAUDIO_END seq=1\n');attempts=[]
def acknowledge_second_stop():
 attempts.append(True)
 if len(attempts)==2:fake.data.extend(b'STOPPED; clocks LOW\n')
recovery=stop_and_resynchronize(fake,acknowledge_second_stop,clock=lambda:fake.now)
assert recovery['recovered'] and recovery['stop_attempts']==2
checks.append('lost_first_stop_ack_is_retried')
fake=FakeSerial(data=b'not a stop acknowledgement\n')
recovery=stop_and_resynchronize(fake,lambda:None,clock=lambda:fake.now,timeout=.05)
assert not recovery['recovered'] and .05<=fake.now<.08
checks.append('missing_stop_ack_is_bounded_and_rejected')

result = {'passed': True, 'checks': checks, 'hardware_test': False, 'audio_played': False}
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=PROJECT/'stages/06-joint-delay/packet-fault-validation.json')
destination=parser.parse_args().output
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
