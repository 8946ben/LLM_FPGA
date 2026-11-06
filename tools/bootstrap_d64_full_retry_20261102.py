from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
archive=ROOT/'full_retry_entry_20261102.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='e6edab60108e6ffd680a7fc5d642552ad629004495f963935d6b4204f89cd936'
R=ROOT/'module_14_lm_head_v4/reports/full_bank_cosim_20261102_r1'
assert not (R/'FULL_WORKFLOW.json').exists() and not (R/'launcher.log').exists()
for folder in ['full_bank_cosim_20261026_r1','d64_full_input_preflight_20261102_r2','d64_resource_recovery_20261102_r1','d64_stream_loader_20261102_r1']:
 assert not (ROOT/'module_14_lm_head_v4/reports'/folder/'ACTIVE.lock').exists(),folder
with tarfile.open(archive) as tar:
 for member in tar.getmembers():
  p=(ROOT/member.name).resolve();assert ROOT in p.parents and member.isfile()
  data=tar.extractfile(member).read()
  if p.exists():assert p.read_bytes()==data,str(p)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
plan=json.loads((R/'PLAN.json').read_text())
for name,e in plan['gate_reviews'].items():
 p=ROOT/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'] and json.loads(p.read_text())['state']==e['state'],name
entry=ROOT/'module_14_lm_head_v4/experiments/full_bank_cosim_20261102/run_full.py'
with (R/'launcher.log').open('w') as out:
 p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'full_parent_pid_snapshot':p.pid,'workflow':str(R/'FULL_WORKFLOW.json'),'automatic_next_stage':False,'board':'NOT_RUN'}))
