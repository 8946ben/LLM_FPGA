"""Independent post-terminal prefix-only audit; never a full12case result."""
from pathlib import Path
import json,csv,hashlib,datetime,sys
import numpy as np
from review_d64_state_payload_20261104 import read_hex_image,META_WORDS
from scan_xsim_evidence_20261104 import scan_xsim_log
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/d64_prefix_options_20261105_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 w=read(R/'WORKFLOW.json');assert w['state']=='PREFIX_COMPARISON_TOOLS_RETURNED_REVIEW_PENDING' and w['process_after']==[]
 proof=read(R/'PREFIX_TERMINAL_PROOF.json')
 for k in ['all_observed_identities_absent','final_group_empty','lock_absent','original_cache_sources_unchanged','actual_compile_maps_match','tv_sha_matches']:assert proof[k],k
 for n,h in proof['artifact_sha256'].items():assert sha(R/n)==h,n
 plan=read(R/'EXECUTION_PLAN.json')
 for n,h in plan['bindings'].items():assert sha(ROOT/n)==h,n
 old=M/'reports/d64_state_suite_20261105_r1';oldreview=read(M/'experiments/d64_prefix_options_20261105_r1/INDEPENDENT_ONE_CASE_REVIEW.json');assert sha(old/'TERMINAL_EXPORT_PROOF.json')==oldreview['proof_sha256'];seal=read(old/'TERMINAL_EXPORT_PROOF.json')
 for name in ['A0_debug.before.hex','A0_debug.after.hex']:assert sha(old/'suite'/name)==seal['artifact_sha256']['suite/'+name]
 original_before=read_hex_image(old/'suite/A0_debug.before.hex');reference=read_hex_image(old/'suite/A0_debug.after.hex');results={}
 previous=None
 for label in ['baseline','optimized']:
  phase=R/(label+'_prefix');before=read_hex_image(phase/'A0_debug.before.hex');after=read_hex_image(phase/'prefix_after.hex');assert np.array_equal(before,original_before)
  expected=before.copy()
  for a,b in [(META_WORDS,META_WORDS+5120),(META_WORDS+37984*4,META_WORDS+37984*4+5120),(META_WORDS+79052*4,META_WORDS+79052*4+64)]:expected[a:b]=reference[a:b]
  assert np.array_equal(after,expected),'Prefix bytes or untouched metadata/workspace/guard differ'
  rows=list(csv.DictReader((phase/'prefix_metrics.csv').open()));assert len(rows)==1;metric={k:int(v) for k,v in rows[0].items()};assert metric['rows']==5120 and metric['starts']==1 and metric['dones']==0 and metric['meta_reads']==1523 and metric['meta_writes']==2576 and 40960<=metric['weight_reads']<=41088
  counts=[0]*7;last=-1
  for event,frame,tick,address,length in csv.reader((phase/'address_requests.csv').open()):
   tick,a,n=int(tick),int(address,16),int(length);end=a+16*(n+1);assert frame=='0' and tick>=last and 0<=n<128 and a%16==0 and a%4096+16*(n+1)<=4096;last=tick
   if event=='MR':assert 0<=a<end<=24368;counts[0]+=1;counts[1]+=n+1
   elif event=='MW':
    assert any(lo<=a<end<=hi for lo,hi in [(24368,44848),(24368+37984*16,24368+37984*16+20480),(24368+79052*16,1289456)]);counts[2]+=1;counts[3]+=n+1
   else:assert event=='WR' and 0<=a<end<=6*896*128*16;counts[4]+=1;counts[5]+=n+1
  assert counts[1]==1523 and counts[3]==2576 and metric['weight_reads']<=counts[5]<=metric['weight_reads']+128
  summary=[[int(v) for v in row] for row in csv.reader((phase/'address_summary.csv').open())];assert summary==[[i,*(counts if i==0 else [0]*7)] for i in range(12)]
  controls=list(csv.reader((phase/'control_trace.csv').open()));assert all(len(row)==5 and row[1]=='0' for row in controls);starts=[i for i,row in enumerate(controls) if row[0]=='W' and int(row[3],16)==0 and int(row[4],16)==1];assert len(starts)==1
  oldcontrols=[]
  for row in csv.reader((old/'suite/control_trace.csv').open()):
   if row[1]!='0':break
   oldcontrols.append(row)
  assert [[x[0],x[1],x[3],x[4]] for x in controls[:starts[0]+1]]==[[x[0],x[1],x[3],x[4]] for x in oldcontrols[:starts[0]+1]]
  for row in controls[starts[0]+1:]:assert row[0]=='R' and int(row[3],16)==0 and int(row[4],16)==1
  simstart=int((phase/'compute_start.marker').read_text());simend=int((phase/'compute_end.marker').read_text());assert simend-simstart==metric['cycles']*5000
  times=read(R/(label+'_HOST_TIMES.json'));assert proof['marker_mtime_ns'][label]==times;seconds=(times['compute_end.marker']-times['compute_start.marker'])/1e9;assert seconds>0
  facts=scan_xsim_log(phase/'tool.log');assert facts['error_count']==0
  with (phase/'tool.log').open(errors='replace') as log:assert sum(line.startswith('PREFIX_DIAGNOSTIC_RETURNED rows=5120 complete_call=0') for line in log)==1
  compiled=read(R/(label+'_COMPILED_SOURCES.json'));assert set(compiled)==set(plan['original_cached_sha'])|{'prefix_probe.sv'}
  for n,h in plan['original_cached_sha'].items():
   if n!='state.prj':assert compiled[n]==h,n
  resources={}
  for step in [label+'_elaborate',label+'_prefix']:
   peak=0;count=0
   for line in (R/step/'resources.jsonl').open():
    v=json.loads(line);count+=1;assert v['rss_kib']==sum(p['rss_kib'] for p in v['members']) and v['rss_kib']<=16*1048576 and v['available_kib']>=32*1048576;peak=max(peak,v['rss_kib'])
   recorded=w['phases'][step];assert recorded['returncode']==0 and recorded['elapsed_s']<=(300 if step.endswith('elaborate') else 1200) and peak==recorded['peak_group_rss_kib'] and sha(R/step/'tool.log')==recorded['tool_log_sha256'];resources[step]=dict(samples=count,peak_gib=peak/1048576)
  result=dict(metric=metric,compute_marker_wall_seconds=seconds,array_sha256=sha(phase/'prefix_after.hex'),request_sha256=sha(phase/'address_requests.csv'),control_sha256=sha(phase/'control_trace.csv'),compiled=compiled,resources=resources)
  if previous:
   for k in ['metric','array_sha256','request_sha256','control_sha256','compiled']:assert result[k]==previous[k],k
  results[label]=result;previous=result
 out=dict(state='PASS_TWO_IDENTICAL_DUT_PREFIXES_AND_MEASURED_COMPUTE_INTERVAL_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),variants=results,prefix_wall_speedup=results['baseline']['compute_marker_wall_seconds']/results['optimized']['compute_marker_wall_seconds'],reviewer_sha256=sha(Path(__file__)),proof_sha256=sha(R/'PREFIX_TERMINAL_PROOF.json'),scope='5120preview raw/key,64dims,metadata/guard/all untouched bytes,identical accepted requests/control/cycles;full original weights and same DUT. Markers bracket prefix computation with small filesystem overhead;exclude loading/export. Only one sample each.',limits=['NOT complete M14 call','NOT12persistent case acceptance','NOT candidate exact FP32 path qualification','NOT physical FPGA/MIG/decode timing','Do not treat this prefix gain as whole-DUT gain without complete measurements'],automatic_next_stage=False)
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
