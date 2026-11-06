"""Full compilation/reference-context fixed-capacity access audit."""
from pathlib import Path
import csv,hashlib,json,re,datetime,sys
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME=sys.argv[1] if len(sys.argv)>1 else 'memory_burst_small_20261103_r3'
E=M/'experiments'/NAME;R=M/'reports'/NAME;S=M/'reports/memory_growth_diagnosis_20261103_r1/sources'
H=M/'reports/memory_full_startup_20261103_r1/baseline_headers'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=json.loads((R/'PLAN.json').read_text());w=json.loads((R/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_BURST_SMALL_AWAITING_INDEPENDENT_REVIEW' and w['process_after']==[] and not (R/'ACTIVE.lock').exists()
 for n,h in p['source_sha256'].items():assert sha(ROOT/n)==h,n
 changed=json.loads((E/'CHANGES.json').read_text());mapped={};files={'reference_model':'reference_model.sv','mem_model':'mem_model.sv','axi_state':'axi_state.sv','test_sequence':'lm_head_v4_partial_proto_subsys_test_sequence_lib.sv'}
 for key,info in changed.items():
  text=(E/files[key]).read_text();mapped[info['original'].replace('\\','/')]=E/files[key]
  assert sha(S/info['original'])==info['original_sha256']
  for a,b in reversed(info['edits']):assert text.count(b)==1;text=text.replace(b,a)
  assert text==(S/info['original']).read_text()
 c=json.loads((R/'COMPILED_SOURCES.json').read_text())
 for n,h in c['actual'].items():
  local=mapped.get(n,E/n if (E/n).exists() else S/n if (S/n).exists() else H/n)
  assert local.exists() and sha(local)==h,n
 assert len(c['unchanged_reused'])==119
 for n,h in c['unchanged_reused'].items():assert sha(S/n)==h
 raw=list(csv.reader((R/'memory_phases.csv').open()));stages={}
 for label,time_ps,amount,rss,vm,anon,file_rss,shared in raw:
  assert int(time_ps)==0 and int(rss)==int(anon)+int(file_rss)+int(shared) and int(vm)>=int(rss)
  assert label not in stages;stages[label]=dict(amount=int(amount),rss_kib=int(rss))
 for name in ['before_weights_load','after_weights_load','small_after_full_read','small_after_repeated_write']:assert name in stages
 assert stages['after_weights_load']['amount']==stages['small_after_full_read']['amount']==8388608
 assert stages['small_after_repeated_write']['amount']==1000000
 log=(R/'xsim.log').read_text(errors='replace').splitlines()
 assert log.count('STREAM_LOAD_PASS bytes=8388608 offset=0 words=524288')==1
 assert log.count('SMALL_BANK_SHAPE banks=8 slots=65536 word_bits=128 flag_bits=16')==1
 assert log.count('BURST_FULL_CONTEXT_PASS bytes=8388608 scalar_writes=1000000 bulk_elements_written=1000000 checksum=1069547520')==1
 assert not any(x.startswith(('UVM_ERROR','UVM_FATAL','ERROR:','Fatal:')) and not re.fullmatch(r'UVM_(?:ERROR|FATAL)\s*:\s*0\s*',x) for x in log)
 pattern=bytes((i*17+3)&255 for i in range(256));block=''.join('0x'+pattern[i:i+16][::-1].hex()+'\n' for i in range(0,256,16)).encode()
 h=hashlib.sha256(b'[[[runtime]]]\n[[transaction]] 0\n')
 for i in range(8388608//256):h.update(block)
 h.update(b'[[/transaction]]\n[[[/runtime]]]\n');assert h.hexdigest()==p['input_tv_sha256']
 assert (8388608//256)*sum(range(256))==1069547520
 for phase,metrics in w['phases'].items():
  samples=[json.loads(x) for x in (R/(phase+'_resources.jsonl')).read_text().splitlines()]
  assert max(x['group_rss_kib'] for x in samples)==metrics['peak_group_rss_kib']
  for x in samples:
   assert sum(y['rss_kib'] for y in x['members'])==x['group_rss_kib']
   assert x['group_rss_kib']<=8*1048576 and x['available_kib']>=32*1048576
 def diff(a,b):return stages[b]['rss_kib']-stages[a]['rss_kib']
 a=diff('before_weights_load','after_weights_load');b=diff('after_weights_load','small_after_full_read');d=diff('small_after_full_read','small_after_repeated_write')
 out={'state':'PASS_INDEPENDENT_BURST_FULL_PROJECT_SMALL_COMPARISON','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'actual_source_count':len(c['actual']),'unchanged_reused':119,'weights_bytes':8388608,'checksum':1069547520,'same_address_writes':1000000,'bulk_write_calls':62500,'bulk_elements_written':1000000,
  'model_sha256':sha(E/'mem_model.sv'),'bulk_million_elements_growth_mib':diff('small_after_repeated_write','small_after_bulk_write')/1024,'load_growth_mib':a/1024,'full_read_growth_mib':b/1024,'same_address_write_growth_mib':d/1024,
  'load_rss_bytes_per_payload_byte':a*1024/8388608,'readpath_rss_bytes_per_returned_byte':b*1024/8388608,'rss_bytes_per_scalar_write_access':d*1024/1000000,
  'stages':stages,'resources':w['phases'],'input_tv_sha256':p['input_tv_sha256'],
  'evidence_sha256':{n:sha(R/n) for n in ['PLAN.json','WORKFLOW.json','COMPILED_SOURCES.json','memory_phases.csv','xsim.log','xsim_resources.jsonl']},
  'limits':['Only eight-MiB fixed-pattern input in full project; no valid M14 compute input, no clock progress, no decode or FIFO qualification',
   'Scalar-million-write control unchanged; bulk phase writes a sixteen-element window, not same scalar-address workload',
   'All-byte and repeated-overwrite assertions execute in SV; host independently recomputes pattern SHA/checksum and phase differences',
   'Readpath includes model API, output queue and all-byte checker; per-returned-byte arithmetic is not per-method-call allocation or guaranteed asymptotic slope',
   'Module/UVM and new/factory minimal controls do not isolate every full-project compilation difference'],
  'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['stages','evidence_sha256']},indent=2))
if __name__=='__main__':main()
