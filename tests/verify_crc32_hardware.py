"""Check the actual Pico implementation against independent zlib vectors."""
import json
from pathlib import Path
import sys
import time
import zlib
import serial

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'SEN0325-Pico-Setup'))
from sen0325_launcher import pico_ports

deadline=time.monotonic()+8
ports=pico_ports()
while not ports and time.monotonic()<deadline:
    time.sleep(.1);ports=pico_ports()
assert len(ports)==1,ports
expected={'standard':zlib.crc32(b'123456789'),'empty':zlib.crc32(b''),
          'ramp':zlib.crc32(bytes(range(256)))}
received=None;banner=None
with serial.Serial(ports[0].device,115200,timeout=.1,write_timeout=1) as link:
    time.sleep(.35);link.write(b'\nSTOP\nHELP\nCRC32CHECK\n')
    deadline=time.monotonic()+4
    while time.monotonic()<deadline:
        line=link.readline().decode('ascii','replace').strip()
        if line.startswith('SEN0325_SETUP '):banner=line
        if line.startswith('CRC32CHECK standard='):
            received={k:int(v,16) for k,v in (token.split('=',1) for token in line.split()[1:])}
            break
assert received==expected,(received,expected)
result={'passed':True,'firmware_banner':banner,'expected':{k:f'{v:08x}' for k,v in expected.items()},
        'received':{k:f'{v:08x}' for k,v in received.items()},'port':ports[0].device,
        'hardware':True,'audio_played':False}
(PROJECT/'stages/06-joint-delay/crc32-hardware-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
