"""Local, nonce-scoped graceful restart for the project's one-click launcher."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import time

class AppInstance:
    def __init__(self,root,checkpoint):
        self.root=Path(root);self.folder=self.root/'logs';self.folder.mkdir(exist_ok=True)
        self.path=self.folder/'desktop-instance.json';self.request=self.folder/'desktop-restart.json'
        self.token=secrets.token_hex(16);self.next_poll=0
        self.info={'pid':os.getpid(),'token':self.token,'checkpoint':checkpoint,'state':'running',
            'started_at':datetime.now().astimezone().isoformat(),'script':str(self.root/'sen0325_launcher.py'),
            'joint_source_sha256':hashlib.sha256((self.root/'joint_delay_dsp.py').read_bytes()).hexdigest()}
        self.write()
    def write(self):
        temp=self.path.with_suffix('.json.tmp');temp.write_text(json.dumps(self.info,indent=2),encoding='utf-8');temp.replace(self.path)
    def restart_requested(self,now=None):
        now=time.monotonic() if now is None else now
        if now<self.next_poll:return False
        self.next_poll=now+.5
        try:data=json.loads(self.request.read_text(encoding='utf-8'))
        except (OSError,ValueError):return False
        if data.get('token')!=self.token or data.get('action')!='restart':return False
        self.info['state']='closing';self.write();return True
    def closed(self):
        self.info['state']='closed';self.info['closed_at']=datetime.now().astimezone().isoformat();self.write()
