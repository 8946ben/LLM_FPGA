from pathlib import Path
import hashlib,json,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/d64_stream_loader_20261102_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 plan=json.loads((R/'PLAN.json').read_text());w=json.loads((R/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW' and not w['process_after'] and not (R/'ACTIVE.lock').exists()
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 expected=bytes((i*17+3)&255 for i in range(256))*(4194304//256)
 reviewed={}
 for name in plan['tests']:
  log=(R/name/'tool.log').read_text(errors='replace');lines=log.splitlines()
  if name.startswith('reject_'):
   assert any(x.startswith('UVM_FATAL') and '[stream_format]' in x for x in lines),name
   assert not any(x.startswith('LOADER_DIFF_PASS ') for x in lines),name
  else:
   actual=(R/name/'loaded.bin').read_bytes();assert actual==expected,name
   assert any(x.startswith('LOADER_DIFF_PASS bytes=4194304 ') for x in lines),name
  samples=[json.loads(x) for x in (R/name/'resources.jsonl').read_text().splitlines()]
  assert max(x['group_rss_kib'] for x in samples)==w['cases'][name]['peak_group_rss_kib']
  reviewed[name]={**w['cases'][name],'log_sha256':sha(R/name/'tool.log')}
  if not name.startswith('reject_'):reviewed[name]['loaded_sha256']=sha(R/name/'loaded.bin')
 result={'state':'PASS_FINITE_STREAM_LOADER_ALL_BYTES_AND_FOUR_NEGATIVES','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'cases':reviewed,'total_compared_bytes':3*4194304,'limits':['Restricted to one aligned byte/128-bit hex transaction 0',
   'Small input does not establish full-model memory scaling or fix the old runtime growth',
   'Expected UVM_FATAL runs return exit 0 in this environment; audited actual markers and absence of success'],
  'process_after':[],'full_m14':'NOT_RUN','board':'NOT_RUN'}
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
