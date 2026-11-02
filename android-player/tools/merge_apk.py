from pathlib import Path
import sys,zipfile
resource,dex,out=map(Path,sys.argv[1:])
with zipfile.ZipFile(resource) as original,zipfile.ZipFile(out,'w') as merged:
    for info in original.infolist():merged.writestr(info,original.read(info.filename))
    merged.write(dex,'classes.dex',compress_type=zipfile.ZIP_DEFLATED)
