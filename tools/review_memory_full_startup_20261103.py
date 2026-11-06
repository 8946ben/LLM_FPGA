"""Independent checkpoint/source/sentinel audit; never a full-M14 PASS."""
from pathlib import Path
import csv,json,hashlib,re,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='memory_full_startup_20261103_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME;S=M/'reports/memory_growth_diagnosis_20261103_r1/sources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=json.loads((R/'PLAN.json').read_text());w=json.loads((R/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_FINITE_PREFIX_AWAITING_INDEPENDENT_REVIEW' and w['process_after']==[] and not (R/'ACTIVE.lock').exists()
 for n,h in p['source_sha256'].items():assert sha(ROOT/n)==h,n
 changes=json.loads((E/'CHANGES.json').read_text())
 modified={'reference_model':'reference_model.sv','mem_model':'mem_model.sv','axi_state':'axi_state.sv','test_sequence':'lm_head_v4_partial_proto_subsys_test_sequence_lib.sv'}
 mapped={}
 for key,info in changes.items():
  assert sha(S/info['original'])==info['original_sha256']
  text=(E/modified[key]).read_text();mapped[info['original'].replace('\\','/')]=E/modified[key]
  for old,new in reversed(info['edits']):assert text.count(new)==1;text=text.replace(new,old)
  assert text==(S/info['original']).read_text()
 compiled=json.loads((R/'COMPILED_SOURCES.json').read_text())
 for n,h in compiled['actual'].items():
  local=mapped.get(n,E/n if (E/n).exists() else S/n if (S/n).exists() else R/'baseline_headers'/n)
  assert local.exists() and sha(local)==h,n
 assert len(compiled['unchanged_reused'])==119
 for n,h in compiled['unchanged_reused'].items():assert sha(S/n)==h
 phases=[]
 for row in csv.reader((R/'memory_phases.csv').open()):
  label=row[0];time_ps,amount,rss,vm,anon,file_rss,shared=map(int,row[1:])
  assert rss>0 and vm>=rss and rss==anon+file_rss+shared
  phases.append(dict(label=label,time_ps=time_ps,amount=amount,rss_kib=rss,vm_kib=vm,anon_kib=anon,file_kib=file_rss,shared_kib=shared))
 def one(label):
  found=[x for x in phases if x['label']==label];assert len(found)==1,label;return found[0]
 for name in ['top_initial','reference_constructed','reference_run_enter','control_regions_ready','before_meta_load','after_meta_load','before_weights_load','stream_before_open','stream_page_created','stream_after_load','after_weights_load','after_1522_sentinels','dut_start']:one(name)
 loading=[x for x in phases if x['label']=='stream_progress']+[one('stream_after_load')]
 assert [x['amount'] for x in loading]==list(range(16777216,545685504,16777216))+[545685504]
 assert all(x['time_ps']==0 for x in phases if x['label']!='running_prefix' and x['label']!='dut_start')
 prefix=[x for x in phases if x['label']=='running_prefix'];assert [x['amount'] for x in prefix]==[5000,10000,15000,20000]
 start=one('dut_start');assert start['time_ps']>0
 for x in prefix:assert x['time_ps']-start['time_ps']==x['amount']*5000
 source=(S/'lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_reference_model.sv').read_text()
 expected=[(int(a),int(b,16)) for a,b in re.findall(r"err=mem_blk_pages_weights.pages\[0\].read_one_elem\(got,64'd(\d+)\);.*?if\(err \|\| got !== 8'h([0-9a-fA-F]+)\)",source,re.S)]
 actual=[(int(a),int(b,16),int(c)) for a,b,c in csv.reader((R/'weights_readback.csv').open())]
 assert len(actual)==len(expected)==1522
 assert [(a,b) for a,b,c in actual]==expected and all(c==0 for a,b,c in actual)
 log=(R/'xsim.log').read_text(errors='replace').splitlines()
 assert log.count('BANK_FULL_INPUT_SENTINEL_PASS checked=1522')==1
 marker=[x for x in log if x.startswith('MEMORY_PREFIX_PASS ')];assert len(marker)==1
 numbers={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',marker[0])};assert numbers['cycles']==20000
 assert numbers['control_ar']==numbers['master_guard_ar'] and numbers['control_r']<=numbers['control_ar']
 assert not any(x.startswith(('UVM_ERROR','UVM_FATAL','ERROR:','Fatal:')) and not re.fullmatch(r'UVM_(?:ERROR|FATAL)\s*:\s*0\s*',x) for x in log)
 resources={}
 for name,metrics in w['phases'].items():
  samples=[json.loads(x) for x in (R/(name+'_resources.jsonl')).read_text().splitlines()]
  assert max(x['group_rss_kib'] for x in samples)==metrics['peak_group_rss_kib']
  for x in samples:
   assert sum(m['rss_kib'] for m in x['members'])==x['group_rss_kib']
   assert x['group_rss_kib']<=64*1048576 and x['available_kib']>=32*1048576
  resources[name]=metrics
 before=one('before_weights_load');after=one('after_weights_load')
 points=[one('stream_page_created')]+loading
 increments=[{'bytes':b['amount']-a['amount'] if a['label']=='stream_progress' else b['amount'],
  'rss_growth_mib':(b['rss_kib']-a['rss_kib'])/1024} for a,b in zip(points,points[1:])]
 # The page-created amount is configured capacity, not bytes loaded.
 out={'state':'PASS_INDEPENDENT_FULL_DUT_STARTUP_AND_FINITE_PREFIX_DIAGNOSIS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'compiled_source_count':len(compiled['actual']),'unchanged_reused_source_count':119,'phase_checkpoints':phases,'resource':resources,
  'weight_load_kernel_growth_gib':(after['rss_kib']-before['rss_kib'])/1048576,
  'kernel_gib_before_weights':before['rss_kib']/1048576,'kernel_gib_after_weights':after['rss_kib']/1048576,
  'weight_load_rss_bytes_per_payload_byte':(after['rss_kib']-before['rss_kib'])*1024/545685504,
  'kernel_gib_at_dut_start':start['rss_kib']/1048576,
  'kernel_growth_mib_during_20000_cycle_prefix':(prefix[-1]['rss_kib']-start['rss_kib'])/1024,
  'load_intervals':increments,'wire_counters':numbers,'sentinels_checked':1522,
  'evidence_sha256':{n:sha(R/n) for n in ['PLAN.json','WORKFLOW.json','COMPILED_SOURCES.json','memory_phases.csv','weights_readback.csv','xsim.log','xsim_resources.jsonl']},
  'limits':['Only initialization and 20000 cycles, not full numeric/FIFO/decode qualification',
   'Original random latency class source unchanged; changed polling alters RNG call order',
   'Known input TV SHA plus 1522 source-anchored readbacks, not all actual DUT data returned',
   'Loader phase attribution is measured; storage versus allocator/call-context decomposition needs orthogonal controls',
   'No 16GiB full-simulation budget qualification'],'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['phase_checkpoints','load_intervals','evidence_sha256']},indent=2))
if __name__=='__main__':main()
