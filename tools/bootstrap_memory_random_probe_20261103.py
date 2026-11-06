from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
a=ROOT/'memory_random_probe_20261103_r2.tar.gz'
assert hashlib.sha256(a.read_bytes()).hexdigest()=='5f15372ac74da6605ccc238e11eb6ed85108d9c9ca2e3d7aa969c7e0f02743da'
r=ROOT/'module_14_lm_head_v4/reports/memory_random_probe_20261103_r2'
assert not (r/'WORKFLOW.json').exists()
assert not (ROOT/'module_14_lm_head_v4/reports/memory_init_probe_20261103_r1/ACTIVE.lock').exists()
with tarfile.open(a) as t:
 for m in t.getmembers():
  p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile();data=t.extractfile(m).read()
  if p.exists():assert p.read_bytes()==data
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
entry=ROOT/'module_14_lm_head_v4/experiments/memory_random_probe_20261103_r2/run_micro.py'
with (r/'launcher.log').open('w') as f:p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'pid_snapshot':p.pid,'workflow':str(r/'WORKFLOW.json'),'full_m14':'NOT_RUN'}))
