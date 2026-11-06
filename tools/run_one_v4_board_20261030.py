"""Run exactly one already frozen private board campaign, never auto-advance."""
from pathlib import Path
import argparse,json,sys,os,datetime,hashlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline_hybrid','exp10']);p.add_argument('case',choices=['chinese','english','code','math']);a=p.parse_args()
base=M if a.variant=='baseline_hybrid' else M/'experiments/fusion_exp10_20261023'
sys.path.insert(0,str(base/'standalone'))
import private_board
out=base/'reports/board_acceptance_20261030_r1'/a.case
plan=json.loads((out/'PLAN.json').read_text());assert plan['case']==a.case
assert not any((out/n).exists() for n in ['EXECUTION.json','FAILURE.json','CAPTURE_RESULT.json','initialize_loader.log'])
lock=M/'reports/dual_board_20261030_r1/ACTIVE.lock'
with lock.open('x') as f:f.write(str(os.getpid()))
state=dict(state='EXECUTING',variant=a.variant,case=a.case,pid=os.getpid(),started=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    user_exclusive_authorization=True,automatic_next_case=False)
def save():(out/'EXECUTION.json').write_text(json.dumps(state,indent=2)+'\n')
save()
try:
    result=private_board.execute(plan,out)
    state.update(state='FIXED_INPUT_CAMPAIGN_RETURNED_PENDING_INDEPENDENT_REVIEW',result_state=result['state'])
except BaseException as exc:
    state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(exc));raise
finally:
    state['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();lock.unlink()
print(json.dumps(state,indent=2))
