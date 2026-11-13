"""Run only checks that are reproducible from the shared source package."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,default=ROOT/'stages/07-team-handoff/verification')
args=parser.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
checks=[]
for folder in ('SEN0325-Pico-Setup','tests','tools'):
    for file in (ROOT/folder).glob('*.py'):
        compile(file.read_text(encoding='utf-8-sig'),str(file),'exec')
checks.append({'name':'active_python_syntax','passed':True})
commands=[
 ('launcher_source_check',['SEN0325-Pico-Setup/refresh_and_start.py','--check-only']),
 ('ram_only_image',['SEN0325-Pico-Setup/verify_ram.py','SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.uf2']),
 ('receive_only_controls',['tests/verify_controls.py','--output',str(out/'controls.json')]),
 ('packet_faults',['tests/verify_raw_packet.py','--output',str(out/'packet-faults.json')]),
 ('gap_model',['tests/verify_gap_beacon.py','--output',str(out/'gap-model.json')]),
]
for name,argv in commands:
    result=subprocess.run([sys.executable,*argv],cwd=ROOT,capture_output=True,text=True,timeout=180)
    checks.append({'name':name,'passed':result.returncode==0,'returncode':result.returncode,
                   'stdout':result.stdout,'stderr':result.stderr})
    print(name+': '+('PASS' if result.returncode==0 else 'FAIL'),flush=True)
    if result.returncode: print(result.stdout,result.stderr,flush=True)
report={'passed':all(x['passed'] for x in checks),'checked_at_utc':datetime.now(timezone.utc).isoformat(),
        'desktop':'RX4','checks':checks,
        'firmware_sha256':hashlib.sha256((ROOT/'SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.uf2').read_bytes()).hexdigest(),
        'not_run':['private raw recording replay','physical Pico scan','known-angle/range validation','Android physical device test']}
(out/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'report':str(out/'validation.json')}))
sys.exit(0 if report['passed'] else 1)
