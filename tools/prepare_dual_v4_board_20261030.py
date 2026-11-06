"""Offline plan preparation only; does not connect to the FPGA."""
from pathlib import Path
import json,hashlib,subprocess,sys,datetime
ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'module_14_lm_head_v4'
R=M/'reports/dual_board_20261030_r1'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
assert not R.exists(), 'Preserve previous preparation'
R.mkdir()
quality=M/'reports/fusion_exp10_20261023_r1/FINAL_QUALITY.json'
q=read(quality)['selected'];d=q['report']['decode']
assert d['recall']>=.99 and all(v['recall']>=.99 for v in d['by_category'].values())
save(R/'QUALITY_GATE_99.json',dict(state='PASS_USER_ACCEPTED_99_PERCENT_POINT_ESTIMATE_GATE',
    authorized_date='2026-10-30',gate='Overall and every category decode winner recall >= 99%; numerical equality unchanged',
    source=str(quality.relative_to(ROOT)),source_sha256=sha(quality),parameters=q['parameters'],decode=d,
    original_state_preserved=read(quality)['state'],historical_gate='99.9% failure unchanged',
    scope='Existing independent fixed-dense-trajectory candidate coverage; not new evaluation, whole-task accuracy or FPGA correctness'))
roots={'baseline_hybrid':M,'exp10':M/'experiments/fusion_exp10_20261023'}
plan=dict(state='OFFLINE_PREFLIGHT_IN_PROGRESS',board_connected_and_exclusive_user_confirmed=True,
    user_authorized='Sequential early v4 hybrid and experiment10 board tests; new quality gate99%',
    variants={},board_operations_performed=False,automatic_execution=False,
    required_checks=['matched bit/XSA/PS init/ELF and immutable package hashes',
        'full initialization on every image change; private signature/MIG calibration/idle',
        '320MiB TCP image;320 target chunk CRCs/full target CRC/34 target reads',
        'halt loader CPU and prove GEM DMA quiescence before test ELF replacement',
        '3 warmup+30 timed+1000 stability calls per selected fixed input',
        'full debug arrays/multistep/error-path acceptance separately; fixed campaign alone is limited qualification'],
    not_claimed=['full LLM decode or TTFT','new corpus quality evaluation','IP hardware cycle counter'])
save(R/'PLAN.json',plan)
results=[]
for variant,base in roots.items():
    row=dict(root=str(base.relative_to(ROOT)),cases={})
    for case in ['chinese','english','code','math']:
        out=base/'reports/board_acceptance_20261030_r1'/case
        cmd=[sys.executable,str(base/'standalone/private_board.py'),'--case',case,'--out',str(out),'--timeout','900']
        with (R/(variant+'_'+case+'_preflight.log')).open('x',encoding='utf-8') as log:
            result=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=240)
        item=dict(variant=variant,case=case,returncode=result.returncode,plan=str((out/'PLAN.json').relative_to(ROOT)))
        if result.returncode==0:item['plan_sha256']=sha(out/'PLAN.json')
        results.append(item);row['cases'][case]=item
        save(R/(variant+'_'+case+'_PREFLIGHT.json'),item)
        print(json.dumps(item),flush=True)
        if result.returncode:raise RuntimeError('Preflight failed, preserve log: '+variant+'/'+case)
    plan['variants'][variant]=row
save(R/'OFFLINE_PREFLIGHT.json',dict(state='PASS_EIGHT_FIXED_INPUT_PLANS',results=results,
    quality_gate=str((R/'QUALITY_GATE_99.json').relative_to(ROOT)),board_operations_performed=False))
print('OFFLINE_EIGHT_CASES_PASS_NO_BOARD')
