from pathlib import Path
import hashlib,tarfile,subprocess,json
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
archive=ROOT/'full_bank_entry_20261026.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='1579af1f1de9444a4d02bf8c0dad22ac678454fc0c585092de5162f16f838bca'
R=ROOT/'module_14_lm_head_v4/reports/full_bank_cosim_20261026_r1'
assert not (R/'FULL_WORKFLOW.json').exists()
with tarfile.open(archive) as t:
 for m in t.getmembers():
  p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile();data=t.extractfile(m).read()
  if p.exists():assert p.read_bytes()==data,str(p)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
entry=ROOT/'module_14_lm_head_v4/experiments/full_bank_cosim_20261026/run_full.py'
plan=json.loads((R/'PLAN.json').read_text())
for n,h in plan['gate_reviews'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h['sha256']
with (R/'launcher.log').open('w') as out:
 p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps(dict(parent_pid_snapshot=p.pid,workflow=str(R/'FULL_WORKFLOW.json'),automatic_next_stage=False)))
