"""Freeze the complete entry only AFTER independent five-block review exists."""
from pathlib import Path
import json,hashlib,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/full_bank_cosim_20261026';R=M/'reports/full_bank_cosim_20261026_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not (R/'PLAN.json').exists();R.mkdir(exist_ok=True)
 gates={}
 required=[(M/'reports/sim_memory_bank_20261026_r1/PREVIEW_REVIEW.json','PASS_FIRST5_PREVIEW_FULL_ARRAYS_AND_FULL_INPUT_SENTINELS'),
           (M/'reports/perf_observer_20261026_r1/INDEPENDENT_REVIEW.json','PASS_PASSIVE_OBSERVER_UNIT_AND_REAL_BIND_ELABORATION'),
           (M/'reports/postcheck_control_20261026_r1/RESULT.json','PASS_ORIGINAL_POSTCHECK_POSITIVE_AND_NEGATIVE_CONTROLS'),
           (M/'reports/range_observer_20261026_r1/INDEPENDENT_REVIEW.json','PASS_PASSIVE_AXI_RANGE_UNIT_AND_REAL_BIND')]
 for p,state in required:
  assert p.exists() and json.loads(p.read_text())['state']==state,'Gate missing: '+str(p)
  gates[str(p.relative_to(ROOT)).replace('\\','/')]=dict(state=state,sha256=sha(p))
 after=M/'reports/sim_memory_bank_20261026_r1/PROCESS_AFTER.json'
 assert json.loads(after.read_text())['owned_process_group_members']==[]
 parent=json.loads((M/'reports/partial_rtl_20261024_r1/full_r3/PLAN.json').read_text())
 sources=parent['source_sha256'].copy();rebind=parent['only_path_rebind'];sources[rebind['path']]=rebind['remote_sha256']
 files=list(E.iterdir())+[M/'experiments/sim_memory_bank_20261026/mem_model.sv',M/'experiments/sim_memory_bank_20261026/weights_preflight.svh',M/'experiments/perf_observer_20261026/stage_observer.sv',M/'experiments/perf_observer_20261026/stage_bind.sv']
 for p in files:sources[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
 control=json.loads(required[2][0].read_text());inp=json.loads((M/'reports/sim_memory_bank_20261026_r1/FULL_TV_INPUT_REVIEW.json').read_text())
 plan=dict(state='FROZEN_GATED_FULL_GENERATED_XSIM_AND_C_POSTCHECK_ENTRY',gate_reviews=gates,source_sha256=sources,
  reuse_sources=json.loads((M/'reports/sim_memory_bank_20261026_r1/PREVIEW_RTL_AND_STALL_REUSE.json').read_text()),
  postchecker_sha256=control['postchecker_sha256'],full_tv_sha256=inp['tv_sha256'],
  case='old_chinese; one full call d64/T4096/B1024/dualW/debug1; original strong random_stall',
  flow='Original generated XSIM and C postchecker run manually; original C-reference TV reused only as input; no pre-generated actual',
  formatted_cosim_design_report='NOT_RUN, never copy old Fail report as new evidence',
  scopes_pending_after_tool_pass=['All151936 preview/key, full candidate/raw and scalar independent reconstruction','Actual finite FIFO depth/occupancy/blocking audit','ABA/mode followup','Performance/200MHz/board'],
  safety=dict(wall_timeout_seconds=172800,minimum_initial_available_gib=200,minimum_running_available_gib=8,stop_file='STOP_REQUESTED'),
  automatic_next_stage=False,board='NOT_RUN')
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 archive=R/'entry.tar.gz'
 with tarfile.open(archive,'w:gz') as t:
  for p in list(E.iterdir())+[R/'PLAN.json']+[x[0] for x in required]+[after]:t.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps(dict(state=plan['state'],archive=str(archive),sha256=sha(archive))))
if __name__=='__main__':main()
