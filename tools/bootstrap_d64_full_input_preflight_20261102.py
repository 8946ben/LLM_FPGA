from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
archive=ROOT/'d64_full_input_entry_20261102.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='26c2ab15c3d5693ef7c916b3d7e8e171ee2abad89dc8861c87cf66e759ce6a59'
R=ROOT/'module_14_lm_head_v4/reports/d64_full_input_preflight_20261102_r1'
assert not (R/'WORKFLOW.json').exists() and not (R/'launcher.log').exists()
with tarfile.open(archive) as tar:
 for member in tar.getmembers():
  p=(ROOT/member.name).resolve();assert ROOT in p.parents and member.isfile()
  data=tar.extractfile(member).read()
  if p.exists():assert p.read_bytes()==data,str(p)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
entry=ROOT/'module_14_lm_head_v4/experiments/d64_full_input_preflight_20261102/run_preflight.py'
with (R/'launcher.log').open('w') as out:
 p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'input_only_parent_pid':p.pid,'workflow':str(R/'WORKFLOW.json'),'automatic_next_stage':False,'dut':'NOT_INSTANTIATED'}))
