"""Audit full-model source hashes, actual sentinels and frozen SV byte checker."""
from pathlib import Path
import csv,datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/d64_full_input_preflight_20261102_r2'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def main():
 plan=json.loads((R/'PLAN.json').read_text());w=json.loads((R/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW'
 assert w['source_before']==w['source_after']=='SHA_PASS' and not w['process_after']
 assert not (R/'ACTIVE.lock').exists()
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 for n,h in plan['weight_sha256'].items():assert sha(ROOT/n)==h,n
 lines=(R/'simulate.log').read_text(errors='replace').splitlines()
 markers=['STREAM_LOAD_PASS bytes=545685504 offset=0 words=34105344','BANK_FULL_INPUT_SENTINEL_PASS checked=1522',
  'FULL_INPUT_BINARY_PASS base=0 bytes=273416192','FULL_INPUT_BINARY_PASS base=273416192 bytes=272269312',
  'FULL_INPUT_MEMORY_PASS bytes=545685504 words=34105344 sentinel=1522 all_bytes=1 dut=0']
 for marker in markers:assert lines.count(marker)==1,marker
 assert not any(x.startswith(('UVM_FATAL','UVM_ERROR','Fatal:','ERROR:')) for x in lines)
 files=[ROOT/'module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin',ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin']
 rows=list(csv.reader((R/'weights_readback.csv').open()))
 assert len(rows)==1522
 with files[0].open('rb') as tiled,files[1].open('rb') as canonical:
  for row in rows:
   address=int(row[0]);value=int(row[1],16);status=int(row[2]);assert status==0
   assert 0<=address<545685504
   source,offset=(tiled,address) if address<273416192 else (canonical,address-273416192)
   source.seek(offset);assert source.read(1)==bytes([value]),address
 samples=[json.loads(x) for x in (R/'simulate_resources.jsonl').read_text().splitlines()]
 peak=max(x['group_rss_kib'] for x in samples)
 assert peak==w['phases']['simulate']['peak_group_rss_kib']
 assert all(x['available_kib']>=32*1024*1024 and x['group_rss_kib']<=32*1024*1024 for x in samples)
 result={'state':'PASS_NO_DUT_FULL_INPUT_ALL_BYTES_AND_SENTINELS','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'tool_byte_comparisons':545685504,'host_independent_sentinel_comparisons':1522,
  'input_words':34105344,'weight_sha256':plan['weight_sha256'],'input_tv_sha256_before_after':plan['full_tv_sha256'],
  'resource':w['phases']['simulate'],'peak_group_rss_gib':peak/1048576,
  'evidence_sha256':{name:sha(R/name) for name in ['simulate.log','weights_readback.csv','simulate_resources.jsonl','WORKFLOW.json']},
  'limits':['No DUT instantiated; this does not qualify full RTL, FIFO or runtime memory growth',
    '545685504 comparisons are actual assertions in frozen SV checker; host independently rechecks 1522 saved bytes and both complete source SHA256',
    'Sampled process-group RSS includes frontend and kernel; not a measured M14 latency or FPGA performance'],
  'process_after':[],'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
