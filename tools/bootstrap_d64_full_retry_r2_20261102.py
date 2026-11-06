from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
archive=ROOT/'full_retry_entry_20261102_r2.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='31a9feeb0c09a2ab1852cdbb17f4a1f322270a8ccbdf8fbcbfe39eb538ebbcaa'
R=ROOT/'module_14_lm_head_v4/reports/full_bank_cosim_20261102_r2'
assert not (R/'FULL_WORKFLOW.json').exists() and not (R/'launcher.log').exists()
for folder in ['full_bank_cosim_20261102_r1','full_bank_cosim_20261026_r1','d64_full_input_preflight_20261102_r2','d64_stream_integration_20261102_r2']:
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
entry=ROOT/'module_14_lm_head_v4/experiments/full_bank_cosim_20261102_r2/run_full.py'
with (R/'launcher.log').open('w') as out:
 p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'full_parent_pid_snapshot':p.pid,'workflow':str(R/'FULL_WORKFLOW.json'),'automatic_next_stage':False,'board':'NOT_RUN'}))
