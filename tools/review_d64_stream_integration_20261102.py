from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/d64_stream_integration_20261102_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=json.loads((R/'PLAN.json').read_text());w=json.loads((R/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW' and w['process_after']==[] and not (R/'ACTIVE.lock').exists()
 for n,h in p['source_sha256'].items():assert sha(ROOT/n)==h,n
 model=M/'experiments/d64_stream_integration_20261102_r2/mem_model.sv'
 old=M/'experiments/d64_stream_loader_20261102/mem_model.sv'
 a=model.read_text();b=old.read_text();key='class mem_model_pages_with_diffofst#';assert a[a.index(key):]==b[b.index(key):]
 expected=bytes((i*17+3)&255 for i in range(256))*32
 evidence={}
 for case in p['cases']:
  assert (R/case/'mapping_bytes.bin').read_bytes()==expected,case
  lines=(R/case/'simulate.log').read_text(errors='replace').splitlines()
  assert lines.count('MAPPING_INTEGRATION_PASS bytes=8192 offsets=0,4096 page_ofst=0 pipe_reads=513 fallback=1')==1
  assert (case=='stream_mapping') == ('STREAM_LOAD_PASS bytes=8192 offset=0 words=512' in lines)
  assert not any(x.startswith(('UVM_FATAL','UVM_ERROR','Fatal:','ERROR:')) for x in lines)
  evidence[case]={'bytes_sha256':sha(R/case/'mapping_bytes.bin'),'log_sha256':sha(R/case/'simulate.log')}
 result={'state':'PASS_ORIGINAL_OFFSET_SUBCLASS_STREAM_AND_PIPE_CALLBACKS','bytes_compared':16384,
  'offset_metadata':[0,4096],'cross4KiB_callback':'PASS','ordinary_file_fallback':'PASS','original_subclass_suffix_unchanged':True,
  'evidence':evidence,'model_sha256':sha(model),'limits':['Real original file_agent offset subclass and pipe callbacks; no DUT or AXI VIP bus instantiated',
   'Full weights helper/all-byte qualification is from separate full_input_preflight; full integrated RTL remains pending'],
  'process_after':[],'board':'NOT_RUN'}
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
