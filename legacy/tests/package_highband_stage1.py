"""Snapshot the reviewed HF1 host sources, test assets and stage documents."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/01-16-18kHz'
OUT=Path(r'C:\Users\33296\Documents\Codex\2026-10-08\w\outputs')

reports=['model-validation.json','controls-validation.json','english-ui-validation.json',
         'mp3-validation.json','pico-ui-validation.json']
for name in reports:
    assert json.loads((STAGE/name).read_text(encoding='utf-8'))['passed'],name

files=[PROJECT/'README.md',PROJECT/'Start-Localizer.cmd',PROJECT/'Start-16-18kHz.cmd',
       PROJECT/'docs/USER_GUIDE.md',PROJECT/'docs/HARDWARE.md',PROJECT/'docs/ARCHITECTURE.md',
       PROJECT/'docs/VALIDATION.md']
for pattern in ('*.py','*.json','*.ps1','*.pio','*.h','*.c','*.txt','*.cmd','README.md'):
    files.extend(ROOT.glob(pattern))
files.extend((ROOT/'firmware').glob('*'))
files.extend(p for p in STAGE.iterdir() if p.is_file())
files.extend((PROJECT/'tests').glob('*.py'))
files.append(PROJECT/'tests/requirements-audio.txt')
files.extend((PROJECT/'audio/phone').glob('*.wav'))
files.append(PROJECT/'audio/phone/README.txt')
files.extend((PROJECT/'audio/phone/HF1-MP3').glob('*'))
files=sorted({p for p in files if p.is_file()})

manifest={'stage':'HF1','status':'ready for phone test; no physical range acceptance',
          'date':'2026-10-22','files':{p.relative_to(PROJECT).as_posix():
              hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(STAGE/'release-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
files.append(STAGE/'release-manifest.json')
target=PROJECT/'releases/EE475-HF1-16-18kHz-2026-10-22.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as package:
    for path in files:package.write(path,'EE475-HF1/'+path.relative_to(PROJECT).as_posix())
with zipfile.ZipFile(target) as package:
    assert package.testzip() is None
    for path in files:
        name='EE475-HF1/'+path.relative_to(PROJECT).as_posix()
        assert hashlib.sha256(package.read(name)).hexdigest()==hashlib.sha256(path.read_bytes()).hexdigest()
shutil.copy2(target,OUT/target.name)
summary={'file':str(target),'bytes':target.stat().st_size,'files':len(files),
         'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
         'limitation':'Source and assets for configured toolchain; not a standalone installer.'}
(STAGE/'release-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
