from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/range_observer_20261026_r1';E=M/'experiments/full_bank_cosim_20261026'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p in (R/'remote').iterdir():
  q=R/p.name
  if q.exists():assert q.read_bytes()==p.read_bytes()
  else:q.write_bytes(p.read_bytes())
 assert json.loads((R/'WORKFLOW.json').read_text())['state']=='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW'
 plan=json.loads((R/'PLAN.json').read_text())
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h
 results=[]
 for mode in range(7):
  log=(R/('mode'+str(mode)+'.log')).read_text()
  done=bool(re.search(r'^RANGE_UNIT_DONE mode='+str(mode)+'$',log,re.M))
  reject=bool(re.search(r'^Fatal: RANGE_OBSERVER_REJECT ',log,re.M))
  if mode==0:assert done and not reject and 'meta_read_bursts=2 meta_write_bursts=1 weight_read_bursts=3' in log
  else:assert reject and not done
  results.append(dict(mode=mode,completed=done,rejected=reject,log_sha256=sha(R/('mode'+str(mode)+'.log'))))
 assert 'Built simulation snapshot range_actual_bind_r1' in (R/'actual_bind_elaborate.log').read_text()
 src=(E/'range_observer.sv').read_text();ports=src[src.index('module lmh_range_observer'):src.index(');')];assert not re.search(r'\b(output|inout)\b',ports)
 result=dict(state='PASS_PASSIVE_AXI_RANGE_UNIT_AND_REAL_BIND',cases=results,interface_has_no_outputs=True,
  real_bind='Actual frozen DUT elaboration only; no M14 simulated by this unit',
  map_scope='Zero-based generated CoSim meta1289456B/weights545685504B only; not a physical DDR profile',
  reviewer_sha256=sha(Path(__file__)),plan_sha256=sha(R/'PLAN.json'),automatic_next_stage=False,board='NOT_RUN')
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(state=result['state'],cases=len(results))))
if __name__=='__main__':main()
