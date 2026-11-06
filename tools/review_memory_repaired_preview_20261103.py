"""Audit repaired real-DUT prefix; no full-RTL qualification is granted here."""
from pathlib import Path
import json,hashlib,csv,re,sys,runpy,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='memory_repaired_preview_20261103_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME;S=M/'reports/memory_growth_diagnosis_20261103_r1/sources';H=M/'reports/memory_full_startup_20261103_r1/baseline_headers'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def baseline(n):
 p=S/str(n).replace('\\','/')
 return p if p.exists() else H/n
def main():
 p=json.loads((R/'PLAN.json').read_text());w=json.loads((R/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_FIRST5_MEMORY_REPAIRED_AWAITING_INDEPENDENT_REVIEW' and w['process_after']==[] and not (R/'ACTIVE.lock').exists()
 for n,h in p['source_sha256'].items():assert sha(ROOT/n)==h,n
 for n,g in p['gate_reviews'].items():assert sha(E/n)==g['sha256'] and json.loads((E/n).read_text())['state']==g['state']
 mapping={'reference_model':'reference_model.sv','mem_model':'mem_model.sv','axi_state':'axi_state.sv','test_sequence':'lm_head_v4_partial_proto_subsys_test_sequence_lib.sv','axi_transfer':'axi_transfer.sv','axi_monitor':'axi_monitor.sv','axi_slave_seq_lib':'axi_slave_seq_lib.sv','fifo_monitor':'df_fifo_monitor.svh'}
 mapped={}
 for k,j in json.loads((E/'CHANGES.json').read_text()).items():
  original=baseline(j['original']);assert sha(original)==j['original_sha256'],k
  target=E/mapping[k];text=target.read_text();mapped[j['original'].replace('\\','/')]=target
  for before,after in reversed(j['edits']):
   assert text.count(after)==(j.get('occurrences',1));text=text.replace(after,before)
  assert text==original.read_text(),k
 compiled=json.loads((R/'COMPILED_SOURCES.json').read_text())
 for n,h in compiled['actual'].items():
  path=mapped.get(n,E/n if (E/n).exists() else baseline(n));assert path.exists() and sha(path)==h,n
 assert len(compiled['unchanged_reused'])==116
 for n,h in compiled['unchanged_reused'].items():assert sha(baseline(n))==h,n
 for phase,metric in w['phases'].items():
  samples=[json.loads(x) for x in (R/(phase+'_resources.jsonl')).read_text().splitlines()]
  assert max(x['group_rss_kib'] for x in samples)==metric['peak_group_rss_kib']
  for x in samples:assert x['group_rss_kib']==sum(y['rss_kib'] for y in x['members']) and x['group_rss_kib']<=32*1048576 and x['available_kib']>=32*1048576
 # Reuse the previously audited wire-array parser with this report explicitly rebound.
 original=(ROOT/'tools/review_partial_bank_preview_20261026.py').read_text()
 original=original.replace("R=M/'reports/sim_memory_bank_20261026_r1'","R=M/'reports/"+NAME+"'")
 original=original.replace("work=json.loads((R/'PREVIEW_WORKFLOW.json').read_text());assert work['state']=='SEGMENT_RETURNED_AWAITING_INDEPENDENT_VCD_REVIEW'", "work=json.loads((R/'WORKFLOW.json').read_text());assert work['state']=='TOOL_PASS_FIRST5_MEMORY_REPAIRED_AWAITING_INDEPENDENT_REVIEW'")
 original=original.replace("plan=json.loads((R/'PREVIEW_PLAN.json').read_text())", "plan=json.loads((R/'PLAN.json').read_text())")
 original=original.replace("(R/'FULL_TV_INPUT_REVIEW.json')", "(M/'reports/sim_memory_bank_20261026_r1/FULL_TV_INPUT_REVIEW.json')")
 original=original.replace("(R/'preview_simulate.log')", "(R/'xsim.log')")
 space={'__file__':str(ROOT/'tools/review_partial_bank_preview_20261026.py'),'__name__':'rebound_review'};exec(compile(original,'rebound_prefix_reviewer','exec'),space);space['main']()
 result=json.loads((R/'PREVIEW_REVIEW.json').read_text());assert result['state']=='PASS_FIRST5_PREVIEW_FULL_ARRAYS_AND_FULL_INPUT_SENTINELS'
 phases=list(csv.reader((R/'memory_phases.csv').open()));bylabel={x[0]:x for x in phases}
 before=int(bylabel['before_weights_load'][3]);after=int(bylabel['after_weights_load'][3])
 out={'state':'PASS_INDEPENDENT_REPAIRED_REAL_DUT_FIRST5','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'compiled_source_count':len(compiled['actual']),'unchanged_reused_sources':116,'all_declared_source_edits_reversible':True,'arrays':{k:result[k] for k in ['raw_values','key_values','dims','weight_read_beats','sentinel_bytes']},'weight_load_growth_gib':(after-before)/1048576,'resource':w['phases'],'evidence_sha256':{n:sha(R/n) for n in ['WORKFLOW.json','PLAN.json','COMPILED_SOURCES.json','AXI_TRACE_REVIEW.json','PREVIEW_REVIEW.json','memory_phases.csv','weights_readback.csv']},'limits':['First5 blocks only; candidate exact path, complete preview, actual finite FIFO and C postcheck still incomplete','Partial-stop RLE may lack final tail; never used as full FIFO evidence','No FPGA performance/board/200MHz implementation qualification'],'full_m14':'INCOMPLETE','automatic_next_stage':False}
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
