"""Launch a frozen, isolated, explicitly approved d64 offline stage once."""
from pathlib import Path
import subprocess,json,base64,sys
root=Path(__file__).resolve().parents[1];stage=sys.argv[1];assert stage in ['d64_matching_ps_20261106_r2','d64_matching_ps_20261106_r3','d64_matching_ps_20261106_r4','d64_matching_ps_20261106_r5','d64_matching_ps_20261106_r6'];e=root/'module_14_lm_head_v4/experiments'/stage;files={str(p.relative_to(e)).replace('\\','/'):base64.b64encode(p.read_bytes()).decode() for p in e.rglob('*') if p.is_file()}
remote=r'''
from pathlib import Path
import json,base64,subprocess
root=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');stage=STAGE;e=root/'module_14_lm_head_v4/experiments'/stage;r=root/'module_14_lm_head_v4/reports'/stage
assert not e.exists() and not r.exists() and not list((root/'module_14_lm_head_v4/reports').rglob('ACTIVE.lock'))
e.mkdir();r.mkdir()
for name,b in FILES.items():
 assert not Path(name).is_absolute() and '..' not in Path(name).parts
 p=e/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
f=(r/'launcher.log').open('wb');p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(e/'run_build.py'),'--execute'],cwd=root,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);f.close()
v=dict(pid=p.pid,proc_stat=(Path('/proc')/str(p.pid)/'stat').read_text());(r/'LAUNCH_IDENTITY.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''.replace('STAGE',repr(stage)).replace('FILES',repr(files))
p=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=remote.encode(),capture_output=True,timeout=90);assert p.returncode==0,p.stderr.decode(errors='replace');r=root/'module_14_lm_head_v4/reports'/stage;r.mkdir();(r/'LAUNCH_RAW.json').write_bytes(p.stdout);print(p.stdout.decode())
