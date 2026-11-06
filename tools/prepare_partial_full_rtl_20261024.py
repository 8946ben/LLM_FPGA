from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/partial_rtl_20261024';R=M/'reports/partial_rtl_20261024_r1/full_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'PLAN.json').exists();R.mkdir(exist_ok=True)
parent=json.loads((M/'reports/partial_hw_20261024_r1/r3/PLAN.json').read_text())
env=json.loads((M/'reports/partial_hw_20261024_r1/r3/remote_hls/REMOTE_ENV_LOCK.json').read_text())
files=[E/'full_tb.cpp',E/'full_cosim.tcl',E/'run_full.py',Path(__file__)]
sources=dict(parent['source_sha256'])
for p in files:sources[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
plan=dict(state='FROZEN_FULL_RTL_ENTRY',parent_r3_plan_sha256=sha(M/'reports/partial_hw_20261024_r1/r3/PLAN.json'),
          method='Clone completed r3 synthesis; replace TB only; one full old_chinese transaction, official binary TV, random_stall and DATAFLOW profiling; FIFO sizing disabled',
          prerequisites='13case selector independent full-memory/AXI-stall review PASS',source_sha256=sources,
          only_path_rebind=dict(path=env['only_path_rebind']['path'],remote_sha256=env['only_path_rebind']['after_sha256']),
          expected=dict(calls=1,fixture='old_chinese',K=4109,preview_keys=151936,preview_raw=151936,dims=64),
          limitations=['One full configured nonzero transaction; not all9 states RTL regression','Random AXI model is not physical DDR or board speed','No200MHz implementation or board'],automatic_next_stage=False)
(R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
with tarfile.open(R/'entry.tar.gz','w:gz') as tar:
    for p in files+[R/'PLAN.json']:tar.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'))
print('FULL_RTL_ENTRY_FROZEN')
