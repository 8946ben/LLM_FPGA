"""Independent full raw-TV/numeric and actual bounded-FIFO review; run after return."""
from pathlib import Path
import json,csv,re,datetime
from scan_xsim_evidence_20261104 import scan_xsim_log
from review_memory_repaired_preview_20261103 import ROOT,M,S,baseline,sha
NAME='memory_repaired_full_20261103_r1';E=M/'experiments'/NAME;R=M/'reports'/NAME

def parse_stage_row(row):
 # status has no validity strobe in this passive profile and is X before output.
 # Preserve it as unknown. The actual returned status TV must still equal [0].
 return {key:(None if key=='status' and re.fullmatch('[xXzZ]+',value) else int(value)) for key,value in row.items()}

def rle_stats(path,allowed):
 total=0;counts={};minimum=None;maximum=None;records=0
 for n,v in csv.reader(path.open()):
  n=int(n);v=int(v);assert n>0 and allowed(v),(path,n,v)
  total+=n;counts[v]=counts.get(v,0)+n;records+=1
  minimum=v if minimum is None else min(minimum,v);maximum=v if maximum is None else max(maximum,v)
 assert total>0
 return dict(samples=total,counts=counts,min=minimum,max=maximum,records=records,sha256=sha(path))

def main():
 work=json.loads((R/'WORKFLOW.json').read_text());assert work['state']=='GENERATED_XSIM_AND_C_POSTCHECK_PASS_AWAITING_NUMERIC_AND_FIFO_REVIEW' and work['process_after']==[]
 after=json.loads((R/'PROCESS_AFTER.json').read_text());assert not after['parent_identity_alive'] and after['owned_process_group_members']==[] and after['active_locks']==0
 plan=json.loads((R/'PLAN.json').read_text());compiled=json.loads((R/'COMPILED_SOURCES.json').read_text())
 mapping={'reference_model':'reference_model.sv','mem_model':'mem_model.sv','axi_state':'axi_state.sv','test_sequence':'lm_head_v4_partial_proto_subsys_test_sequence_lib.sv','axi_transfer':'axi_transfer.sv','axi_monitor':'axi_monitor.sv','axi_slave_seq_lib':'axi_slave_seq_lib.sv','fifo_monitor':'df_fifo_monitor.svh'};mapped={}
 for field,j in json.loads((E/'CHANGES.json').read_text()).items():
  original=baseline(j['original']);assert sha(original)==j['original_sha256'];text=(E/mapping[field]).read_text();mapped[j['original'].replace('\\','/')]=E/mapping[field]
  for before,changed in reversed(j['edits']):assert text.count(changed)==j.get('occurrences',1);text=text.replace(changed,before)
  assert text==original.read_text(),field
 for name,h in compiled['actual'].items():
  path=mapped.get(name,E/name if (E/name).exists() else baseline(name));assert sha(path)==h,name
 for name,h in plan['source_sha256'].items():assert sha(ROOT/name)==h,name
 for n,j in plan['gate_reviews'].items():assert sha(E/n)==j['sha256'] and json.loads((E/n).read_text())['state']==j['state']
 # Explicitly bind the audited numeric parser to this run; no historical PASS reuse.
 text=(ROOT/'tools/review_partial_full_bank_20261026.py').read_text().replace("R=M/'reports/full_bank_cosim_20261026_r1'","R=M/'reports/"+NAME+"'").replace("R/'FULL_WORKFLOW.json'","R/'WORKFLOW.json'")
 log_facts=scan_xsim_log(R/'xsim.log');assert log_facts['error_count']==0,log_facts['error_examples']
 old_log="log=(R/'xsim.log').read_text(errors='replace');assert not re.search(r'^(UVM_FATAL|UVM_ERROR|ERROR:|Fatal:)',log,re.M)"
 assert text.count(old_log)==1;text=text.replace(old_log,"assert log_facts['error_count']==0,log_facts['error_examples']")
 old_sentinel="assert re.search(r'^BANK_FULL_INPUT_SENTINEL_PASS checked=1522$',log,re.M)"
 assert text.count(old_sentinel)==1;text=text.replace(old_sentinel,"assert log_facts['sentinel_pass_count']>0")
 old_guard="guard=re.findall(r'^LMH_RANGE_GUARD_SUMMARY meta_read_bursts=(\\d+) meta_write_bursts=(\\d+) weight_read_bursts=(\\d+)$',log,re.M)"
 assert text.count(old_guard)==1;text=text.replace(old_guard,"guard=log_facts['range_guard_rows'];assert log_facts['range_guard_count']==1")
 old_profile="profile=[{a:int(b) for a,b in row.items()} for row in csv.DictReader(f)]"
 new_profile="profile=[parse_stage_row(row) for row in csv.DictReader(f)]"
 assert text.count(old_profile)==1;text=text.replace(old_profile,new_profile)
 scope={'__file__':str(ROOT/'tools/review_partial_full_bank_20261026.py'),'__name__':'bound_full_review','parse_stage_row':parse_stage_row,'log_facts':log_facts};exec(compile(text,'bound_full_review','exec'),scope);scope['main']()
 numeric=json.loads((R/'NUMERIC_REVIEW.json').read_text());assert numeric['state']=='PASS_ONE_FULL_GENERATED_RTL_NUMERIC_CALL_FIFO_PENDING'
 rows=log_facts['fifo_summary_rows'];assert log_facts['fifo_summary_count']==5 and len(rows)==5
 info={Path(x[0]).name:list(map(int,x[1:])) for x in rows};assert len(info)==5
 binding=baseline('dataflow_monitor.sv').read_text();rtl=baseline('lm_head_v4_partial_proto_p_anonymous_namespace_candidate_dataflow.v').read_text();fifos={}
 for i,(instance,capacity,module) in enumerate([('weights_1_U',128,'fifo_w128_d128_A'),('ids_U',32,'fifo_w32_d32_S'),('contexts_U',32,'fifo_w256_d32_A'),('count_c_U',2,'fifo_w32_d2_S'),('raw_U',32,'fifo_w32_d32_S')],1):
  assert re.search(r'lm_head_v4_partial_proto_'+module+r'\s+'+instance+r'\(',rtl)
  for field in ['rd_en','wr_en']:assert re.search(r'assign fifo_intf_'+str(i)+r'\.'+field+r' = .*\.'+instance+r'\.if_',binding)
  block=re.search(r'lm_head_v4_partial_proto_'+module+r'\s+'+instance+r'\((.*?)\);',rtl,re.S).group(1)
  assert ".if_read_ce(1'b1)" in block and ".if_write_ce(1'b1)" in block
  fifo_source=baseline('lm_head_v4_partial_proto_'+module+'.v');fifo_text=fifo_source.read_text();depth=int(re.search(r'\bDEPTH\s*=\s*(\d+)',fifo_text).group(1));assert capacity==depth+(1 if module.endswith('_A') else 0)
  d=rle_stats(R/('depth%d.csv.depth.rle'%i),lambda v:0<=v<=capacity);b=rle_stats(R/('depth%d.csv.block.rle'%i),lambda v:v in [0,1,2])
  ds,bs,end,maximum,pushes,pops,clamped=info['depth%d.csv'%i]
  assert ds==bs==d['samples']==b['samples'] and end==0 and pushes==pops and pushes>0 and clamped==0
  assert d['max']==maximum<=capacity
  status=[int(x[0]) for x in csv.reader((R/('chan_status%d.csv'%i)).open())];assert len(status)==5
  expected=[int(b['counts'].get(1,0)>0)+2*int(b['counts'].get(2,0)>0),b['counts'].get(1,0),b['counts'].get(2,0),bs,maximum];assert status==expected
  fifos[instance]=dict(capacity=capacity,max_occupancy=maximum,pushes=pushes,pops=pops,end_depth=end,clamped_reads=clamped,depth=d,blocking=b,source_sha256=sha(fifo_source))
 warnings=log_facts['dsp_warning_examples']
 out=dict(state='PASS_ONE_FULL_GENERATED_RTL_NUMERIC_AND_FINITE_FIFO_CALL',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),numeric_review_sha256=sha(R/'NUMERIC_REVIEW.json'),compiled_sources_sha256=sha(R/'COMPILED_SOURCES.json'),reviewer_sha256=sha(Path(__file__)),stream_log_scanner_sha256=sha(ROOT/'tools/scan_xsim_evidence_20261104.py'),fifos=fifos,dsp_warning_lines=warnings,dsp_warning_count=log_facts['dsp_warning_count'],log_scan=log_facts,
  profile_status_scope='Passive status sampled without validity; X preserved as null. Returned status TV still required exact known zero; no numeric comparison relaxed.',
  warning_scope='Used preview/exact outputs checked bit-for-bit for this call; no general claim that all DSP warnings are harmless',
  limits=['One original fixed old_chinese input/debug1 only; continuous A/B/A and other modes remain separate gates','Generated XSIM and C postcheck; official cosim_design formatter NOT_RUN','Strong random delays; stage cycles are not normal-response or physical FPGA decode performance'],board='NOT_RUN',automatic_next_stage=False)
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
