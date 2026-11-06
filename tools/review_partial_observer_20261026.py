from pathlib import Path
import json,csv,hashlib,re
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/perf_observer_20261026_r1';E=M/'experiments/perf_observer_20261026'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p in (R/'remote').iterdir():
  q=R/p.name
  if q.exists():assert q.read_bytes()==p.read_bytes()
  else:q.write_bytes(p.read_bytes())
 work=json.loads((R/'WORKFLOW.json').read_text());assert work['state']=='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW'
 plan=json.loads((R/'PLAN.json').read_text())
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 with (R/'unit_profile.csv').open() as f:rows=[{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
 expected=json.loads((E/'expected_unit.json').read_text());assert len(rows)==len(expected)==5
 for a,e in zip(rows,expected):
  for key,value in e.items():assert a[key]==value,(a,key,value)
  for key in set(a)-set(e):assert a[key]==0,(a,key)
 assert re.search(r'^OBSERVER_STIMULUS_DONE idle_high=2 calls=3 error_call=1$',(R/'unit_simulate.log').read_text(),re.M)
 assert 'Built simulation snapshot observer_actual_bind_r1' in (R/'actual_bind_elaborate.log').read_text()
 for name in ['unit_elaborate.log','unit_simulate.log','actual_bind_elaborate.log']:assert not re.search(r'^ERROR:',(R/name).read_text(),re.M)
 text=(E/'stage_observer.sv').read_text();interface=text[text.index('module lmh_stage_observer'):text.index(');')]
 assert not re.search(r'\b(output|inout)\b',interface)
 result=dict(state='PASS_PASSIVE_OBSERVER_UNIT_AND_REAL_BIND_ELABORATION',
  independent_expected_intervals=dict(call1_stage0=6,call1_total=8,call2_stage3=3,call2_total=5,error_call3=2),
  actual_rows=rows,frame1_ar_stalls=3,frame1_read_and_write_beats=2,
  idle_high_done_not_completed=True,multiple_call_counters_reset=True,interface_has_no_outputs=True,
  real_frozen_top_bind_elaboration='PASS, simulation NOT_RUN',
  source_plan_sha256=sha(R/'PLAN.json'),csv_sha256=sha(R/'unit_profile.csv'),reviewer_sha256=sha(Path(__file__)),
  board='NOT_RUN',full_m14_performance='NOT_MEASURED',automatic_next_stage=False)
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
