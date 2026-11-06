from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
a=ROOT/'memory_control_regression_20261103_r1.tar.gz';assert hashlib.sha256(a.read_bytes()).hexdigest()=='816b17f29cea5a90f3562e3fdbeea06a8731b673860b66ec947faf2849cf4948'
r=ROOT/'module_14_lm_head_v4/reports/memory_control_regression_20261103_r1';assert not (r/'WORKFLOW.json').exists()
assert not list((ROOT/'module_14_lm_head_v4/reports').glob('memory_*/ACTIVE.lock'))
assert not (ROOT/'module_14_lm_head_v4/reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()
with tarfile.open(a) as t:
 for m in t.getmembers():
  p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile();data=t.extractfile(m).read()
  if p.exists():assert p.read_bytes()==data
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
entry=ROOT/'module_14_lm_head_v4/experiments/memory_control_regression_20261103_r1/run_micro.py'
with (r/'launcher.log').open('w') as f:p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'pid_snapshot':p.pid,'workflow':str(r/'WORKFLOW.json'),'full_m14':'NOT_RUN'}))
