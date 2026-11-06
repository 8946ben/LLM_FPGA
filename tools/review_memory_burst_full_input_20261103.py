"""Host independent audit of real all-word initialization qualification only."""
from pathlib import Path
import json,csv,hashlib,re,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='memory_burst_full_input_20261103_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME;S=M/'reports/memory_growth_diagnosis_20261103_r1/sources';H=M/'reports/memory_full_startup_20261103_r1/baseline_headers'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((R/'PLAN.json').read_text());w=json.loads((R/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_BURST_FULL_INPUT_AWAITING_INDEPENDENT_REVIEW' and w['process_after']==[] and not (R/'ACTIVE.lock').exists()
 for n,h in p['source_sha256'].items():assert sha(ROOT/n)==h,n
 digest=sha(E/'mem_model.sv')
 for name,state in [('gate_small.json','PASS_INDEPENDENT_BURST_FULL_PROJECT_SMALL_COMPARISON'),('gate_semantics.json','PASS_INDEPENDENT_BURST_MODEL_SEMANTICS')]:
  j=json.loads((E/name).read_text());assert j['state']==state and j['model_sha256']==digest
 changes=json.loads((E/'CHANGES.json').read_text());files={'reference_model':'reference_model.sv','mem_model':'mem_model.sv','axi_state':'axi_state.sv','test_sequence':'lm_head_v4_partial_proto_subsys_test_sequence_lib.sv'};mapped={}
 for key,info in changes.items():
  text=(E/files[key]).read_text();mapped[info['original'].replace('\\','/')]=E/files[key]
  assert sha(S/info['original'])==info['original_sha256']
  for old,new in reversed(info['edits']):assert text.count(new)==1;text=text.replace(new,old)
  assert text==(S/info['original']).read_text()
 comp=json.loads((R/'COMPILED_SOURCES.json').read_text())
 for n,h in comp['actual'].items():
  local=mapped.get(n,E/n if (E/n).exists() else S/n if (S/n).exists() else H/n)
  assert local.exists() and sha(local)==h,n
 assert len(comp['unchanged_reused'])==119
 for n,h in comp['unchanged_reused'].items():assert sha(S/n)==h,n
 checks=w['weight_source_sha256_checks'];assert len(checks)==2 and all(c['digests']==p['weight_sha256'] for c in checks)
 for n,h in p['weight_sha256'].items():assert sha(ROOT/n)==h,n
 original=(S/'lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_reference_model.sv').read_text()
 expected=[(int(a),int(b,16)) for a,b in re.findall(r"err=mem_blk_pages_weights.pages\[0\].read_one_elem\(got,64'd(\d+)\);.*?if\(err \|\| got !== 8'h([0-9a-fA-F]+)\)",original,re.S)]
 readback=[(int(a),int(b,16),int(c)) for a,b,c in csv.reader((R/'weights_readback.csv').open())]
 assert len(expected)==len(readback)==1522 and [(a,b) for a,b,c in readback]==expected and all(c==0 for a,b,c in readback)
 tiled=ROOT/'module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin';canon=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
 with tiled.open('rb') as a,canon.open('rb') as b:
  for addr,value,status in readback:
   f,pos=(a,addr) if addr<273416192 else (b,addr-273416192);f.seek(pos);assert f.read(1)==bytes([value]),addr
 log=(R/'xsim.log').read_text(errors='replace').splitlines()
 markers=['BANK_FULL_INPUT_SENTINEL_PASS checked=1522','BURST_FULL_BINARY_PASS base=0 bytes=273416192 words=17088512','BURST_FULL_BINARY_PASS base=273416192 bytes=272269312 words=17016832','BURST_FULL_INPUT_INIT_PASS bytes=545685504 words=34105344 sentinel=1522 all_bytes=1 time0=1']
 for marker in markers:assert log.count(marker)==1,marker
 assert not any(x.startswith(('UVM_ERROR','UVM_FATAL','ERROR:','Fatal:')) and not re.fullmatch(r'UVM_(?:ERROR|FATAL)\s*:\s*0\s*',x) for x in log)
 assert not any(x.startswith('MEMORY_PREFIX_PASS') for x in log)
 raw=list(csv.reader((R/'memory_phases.csv').open()));stages=[]
 for label,t,amount,rss,vm,anon,file_rss,shared in raw:
  assert int(t)==0 and int(rss)==int(anon)+int(file_rss)+int(shared) and int(vm)>=int(rss)
  stages.append(dict(label=label,amount=int(amount),rss_kib=int(rss)))
 def one(label):
  matches=[x for x in stages if x['label']==label];assert len(matches)==1,label;return matches[0]
 for label in ['before_weights_load','after_weights_load','after_1522_sentinels','before_full_binary_verify','after_full_binary_verify']:one(label)
 assert not any(x['label'] in ['dut_start','running_prefix'] for x in stages)
 assert one('after_full_binary_verify')['amount']==545685504
 resources={}
 for phase,metrics in w['phases'].items():
  samples=[json.loads(x) for x in (R/(phase+'_resources.jsonl')).read_text().splitlines()]
  assert max(x['group_rss_kib'] for x in samples)==metrics['peak_group_rss_kib']
  for x in samples:
   assert sum(m['rss_kib'] for m in x['members'])==x['group_rss_kib']
   assert x['group_rss_kib']<=16*1048576 and x['available_kib']>=32*1048576
  resources[phase]=metrics
 before=one('before_weights_load')['rss_kib'];after=one('after_weights_load')['rss_kib'];verified=one('after_full_binary_verify')['rss_kib']
 baseline=json.loads((M/'reports/memory_full_startup_20261103_r1/INDEPENDENT_REVIEW.json').read_text())
 out={'state':'PASS_INDEPENDENT_BURST_REAL_FULL_INPUT_INIT_AND_ALL_WORDS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'model_sha256':digest,'actual_compiled_sources_checked':len(comp['actual']),'unchanged_reused_sources_checked':119,
  'verified_words_in_sv':34105344,'verified_bytes_in_sv':545685504,'host_independent_actual_sentinel_bytes':1522,'weight_sha256':p['weight_sha256'],
  'kernel_gib_before_weights':before/1048576,'kernel_gib_after_weights':after/1048576,'kernel_gib_after_all_word_check':verified/1048576,
  'load_growth_gib':(after-before)/1048576,'all_word_check_growth_gib':(verified-one('before_full_binary_verify')['rss_kib'])/1048576,
  'load_growth_reduction_percent_vs_full_baseline':100*(1-(after-before)/1048576/baseline['weight_load_kernel_growth_gib']),
  'resource':resources,'stages':stages,'all_observed_simulation_time_ps':0,
  'evidence_sha256':{n:sha(R/n) for n in ['PLAN.json','WORKFLOW.json','COMPILED_SOURCES.json','memory_phases.csv','weights_readback.csv','xsim.log','xsim_resources.jsonl']},
  'limits':['Actual full-project initialization only; no full M14 call, FIFO, numeric output, performance or board qualification',
   '34105344 all-word comparisons execute in frozen SV with original binary inputs; host rechecks complete source SHA and1522 actual saved bytes, not a complete returned memory dump',
   'Observed initialization resource budget does not guarantee a complete simulation fits16GiB',
   'Packed reader check is distinct from byte queue AXI runtime; known residual readpath growth remains to qualify'],
  'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['stages','evidence_sha256']},indent=2))
if __name__=='__main__':main()
