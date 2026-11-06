"""Final independent12case audit. Refuses running/incomplete or unproven receipts."""
from pathlib import Path
import json,csv,datetime,hashlib,re
import numpy as np
from review_d64_state_payload_20261104 import read_hex_image,review_case,review_control,META_WORDS
from review_d64_state_requests_20261104 import replay_requests
from review_memory_repaired_full_20261103 import parse_stage_row
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/d64_state_suite_20261105_r1';M=ROOT/'module_14_lm_head_v4'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as source:
  for chunk in iter(lambda:source.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def main():
 work=read(R/'WORKFLOW.json');assert work['state']=='SUITE_RETURNED_AWAITING_INDEPENDENT_ARRAY_CONTROL_ADDRESS_REVIEW' and work['process_after']==[]
 proof=read(R/'TERMINAL_EXPORT_PROOF.json')
 for key in ['original_parent_identity_absent','all_observed_identities_absent','final_owned_group_empty','active_lock_absent','compile_cache_current_matches']:assert proof[key],key
 for n,h in proof['artifact_sha256'].items():assert sha(R/n)==h,n
 plan=read(R/'EXECUTION_PLAN.json');assert proof['tv_sha256']==plan['tv_sha256']
 for n,h in {**plan['bindings'],**plan['input_sha256']}.items():assert sha(ROOT/n)==h,n
 compiled=read(M/'reports/d64_state_compile_20261105_r2/COMPILED_SOURCES.json');assert proof['compile_cache_source_sha256']==compiled
 scenarios=read(M/'reports/d64_state_fixtures_20261104_r2/MANIFEST.json')['scenarios'];assert len(scenarios)==12
 assert set(work['phases'])=={'elaborate','suite'};resources={}
 for phase,metric in work['phases'].items():
  peak=0;count=0;last=None
  for line in (R/phase/'resources.jsonl').open(encoding='utf-8'):
   sample=json.loads(line);count+=1;assert sample['rss_kib']==sum(p['rss_kib'] for p in sample['members']);assert sample['rss_kib']<=16*1048576 and sample['available_kib']>=32*1048576
   peak=max(peak,sample['rss_kib']);last=sample
  assert count>0 and peak==metric['peak_group_rss_kib'] and last['elapsed_s']==metric['elapsed_s'] and metric['returncode']==0
  assert metric['elapsed_s']<=(300 if phase=='elaborate' else 21600)
  assert sha(R/phase/'tool.log')==metric['tool_log_sha256']
  resources[phase]=dict(samples=count,peak_group_gib=peak/1048576,elapsed_s=metric['elapsed_s'])
 counts=dict(load=0,sentinel=0,finish=0);case_lines=[]
 with (R/'suite/tool.log').open(encoding='utf-8',errors='replace') as stream:
  for line in stream:
   line=line.rstrip('\r\n')
   assert not (line.startswith(('Fatal:','ERROR:','UVM_FATAL','UVM_ERROR')) and not re.fullmatch(r'UVM_(?:FATAL|ERROR)\s*:\s*0\s*',line)),line
   if line=='STREAM_LOAD_PASS bytes=545685504 offset=0 words=34105344':counts['load']+=1
   if line=='STATE_WEIGHT_SENTINEL_PASS checked=1522':counts['sentinel']+=1
   if line=='D64_STATE_SUITE_RETURNED calls=12 no_inter_call_reset=1':counts['finish']+=1
   assert not line.startswith('STATE_LOAD_ONLY_PASS')
   if line.startswith('STATE_CASE_RETURNED '):case_lines.append(line)
 assert counts==dict(load=1,sentinel=1,finish=1) and len(case_lines)==12
 metrics=[]
 for row in csv.DictReader((R/'suite/case_metrics.csv').open(encoding='utf-8')):metrics.append({k:(v if k=='label' else int(v)) for k,v in row.items()})
 assert len(metrics)==12
 results=[];previous=None
 for s,m in zip(scenarios,metrics,strict=True):
  before=read_hex_image(R/'suite'/(s['label']+'.before.hex'));after=read_hex_image(R/'suite'/(s['label']+'.after.hex'))
  if previous is not None:assert np.array_equal(before[META_WORDS:],previous[META_WORDS:]),'Workspace/guard changed between cases'
  result=review_case(s,before,after,m);results.append(result);previous=after
 assert results[0]['assembled_sha256']==results[2]['assembled_sha256']==results[11]['assembled_sha256']
 control=review_control(scenarios,list(csv.reader((R/'suite/control_trace.csv').open(encoding='utf-8'))))
 addresses=replay_requests(R/'suite/address_requests.csv',metrics,R/'suite/address_summary.csv')
 profile=[parse_stage_row(row) for row in csv.DictReader((R/'suite/stage_profile.csv').open(encoding='utf-8'))]
 assert {row['frame'] for row in profile}==set(range(1,13))
 timing=[]
 for i,m in enumerate(metrics):
  rows=[row for row in profile if row['frame']==i+1];total=[row for row in rows if row['stage']==-1];assert len(total)==1;total=total[0]
  assert total['cycles']==m['ip_cycles'] and [total[k] for k in ['weight_reads','meta_reads','meta_writes']]==[m[k] for k in ['weight_reads','meta_reads','meta_writes']]
  if m['status']==0:assert sorted(row['stage'] for row in rows)==[-1,0,1,2,3,4]
  else:assert not any(row['stage']==4 for row in rows)
  timing.append(dict(case=i,label=m['label'],status=m['status'],debug=m['debug'],ip_cycles=m['ip_cycles'],control_call_cycles=m['control_call_cycles'],normal_model_ip_ms=m['ip_cycles']/200000,normal_model_control_ms=m['control_call_cycles']/200000))
 out=dict(state='PASS_FULL_PERSISTENT_DUT_12CASE_ARRAY_CONTROL_ADDRESS_AND_NORMAL_CYCLES',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=results,control=control,addresses=addresses,normal_model_timing=timing,resources=resources,source_count=len(compiled),proof_sha256=sha(R/'TERMINAL_EXPORT_PROOF.json'),reviewer_sha256=sha(Path(__file__)),helper_sha256={n:sha(ROOT/'tools'/n) for n in ['review_d64_state_payload_20261104.py','review_d64_state_requests_20261104.py','review_memory_repaired_full_20261103.py']},scope='12 persistent DUT scenarios, full defined debug arrays/common production arrays/raw preservation/error effects, actual control/address traces and model cycles. Physical FPGA/MIG/decode timing and board acceptance NOT_RUN. Passive profile status X preserved as null; actual returned CSR status exact.',board='NOT_RUN')
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+chr(10),encoding='utf-8');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
