"""Validate the local RX4 sources and gracefully start/restart this app only."""
from pathlib import Path
import argparse
import ctypes
from datetime import datetime
import hashlib
import json
import subprocess
import sys
import time
from release_info import RELEASE,DEFAULT_PROFILE,SOURCE_FILES,source_fingerprint

ROOT=Path(__file__).resolve().parent
CHECKPOINT='RX4'
NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)

def running(pid):
    kernel=ctypes.windll.kernel32
    kernel.OpenProcess.argtypes=(ctypes.c_uint,ctypes.c_bool,ctypes.c_uint);kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes=(ctypes.c_void_p,ctypes.c_uint)
    kernel.CloseHandle.argtypes=(ctypes.c_void_p,)
    handle=kernel.OpenProcess(0x100000,False,int(pid))
    if not handle:return False
    try:return kernel.WaitForSingleObject(handle,0)==258
    finally:kernel.CloseHandle(handle)

def main(check_only=False,start_only=False):
    (ROOT/'logs').mkdir(exist_ok=True)
    required=SOURCE_FILES
    for name in required:compile((ROOT/name).read_text(encoding='utf-8-sig'),str(ROOT/name),'exec')
    from sen0325_launcher import DESKTOP_CHECKPOINT
    assert DESKTOP_CHECKPOINT==CHECKPOINT
    digest=hashlib.sha256((ROOT/'joint_delay_dsp.py').read_bytes()).hexdigest()
    sources=source_fingerprint(ROOT)
    if check_only:return {'passed':True,'checkpoint':CHECKPOINT,'release':RELEASE,'default_profile':DEFAULT_PROFILE,'source_sha256':sources,'files_checked':len(required),'joint_source_sha256':digest}
    info_path=ROOT/'logs/desktop-instance.json'
    try:old=json.loads(info_path.read_text(encoding='utf-8'))
    except (OSError,ValueError):old={}
    if old.get('state') in ('running','closing') and running(old.get('pid',0)):
        assert Path(old['script']).resolve()==ROOT/'sen0325_launcher.py'
        if start_only and old.get('state')=='running' and old.get('source_sha256')==sources:
            (ROOT/'logs/desktop-restart.json').write_text(json.dumps({'action':'focus','token':old['token']}),encoding='utf-8')
            return {'passed':True,'release':RELEASE,'action':'focused_existing','pid':old['pid'],'source_sha256':sources}
        request={'action':'restart','token':old['token'],'requested_at':datetime.now().astimezone().isoformat()}
        (ROOT/'logs/desktop-restart.json').write_text(json.dumps(request),encoding='utf-8')
        deadline=time.monotonic()+20
        while running(old['pid']) and time.monotonic()<deadline:time.sleep(.2)
        if running(old['pid']):raise RuntimeError('The current recording is still closing. Wait for it to save, then retry. No process was forcibly stopped.')
    pythonw=Path(sys.executable).with_name('pythonw.exe')
    subprocess.Popen([str(pythonw),str(ROOT/'sen0325_launcher.py'),'--profile',DEFAULT_PROFILE],cwd=ROOT,creationflags=NO_WINDOW)
    deadline=time.monotonic()+15;info={}
    while time.monotonic()<deadline:
        try:info=json.loads(info_path.read_text(encoding='utf-8'))
        except (OSError,ValueError):info={}
        if info.get('token')!=old.get('token') and info.get('state')=='running' and info.get('checkpoint')==CHECKPOINT:break
        time.sleep(.2)
    else:raise RuntimeError('A fresh RX4 window was not confirmed. Close any earlier app window and retry.')
    assert info['joint_source_sha256']==digest and info.get('source_sha256')==sources and running(info['pid'])
    result={'passed':True,'checkpoint':CHECKPOINT,'release':RELEASE,'default_profile':DEFAULT_PROFILE,'source_sha256':sources,'new_pid':info['pid'],'new_token':info['token'],
        'previous_pid':old.get('pid'),'graceful_restart':bool(old.get('state') in ('running','closing')),
        'joint_source_sha256':digest,'completed_at':datetime.now().astimezone().isoformat()}
    (ROOT/'logs/one-click-update-status.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');parser.add_argument('--start-only',action='store_true');args=parser.parse_args()
    try:print(json.dumps(main(args.check_only,args.start_only),indent=2))
    except Exception as error:
        (ROOT/'logs').mkdir(exist_ok=True)
        (ROOT/'logs/one-click-update-error.txt').write_text(str(error),encoding='utf-8')
        if sys.executable.lower().endswith('pythonw.exe'):
            ctypes.windll.user32.MessageBoxW(None,str(error),'EE475 update/start',0)
        raise
