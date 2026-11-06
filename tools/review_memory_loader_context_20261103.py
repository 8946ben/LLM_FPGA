"""Audit no-DUT module/UVM and constructor/factory allocation controls."""
from pathlib import Path
import json,csv,re,datetime
from review_memory_growth_20261103 import ROOT,M,ready,rows,sha
NAME='memory_loader_context_20261103_r1'
def main():
 r,p,w=ready(NAME);out={'state':'PASS_INDEPENDENT_LOADER_CONTEXT_CONTROL','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':{}}
 for mode in range(4):
  case='mode_'+str(mode);data=rows(r,case)
  assert [(x[1],x[2]) for x in data]==[(0,0),(1,8388608),(2,8388608),(3,1000000),(4,1000000)]
  for m,stage,count,rss,total in data:
   assert m==mode and rss>0
   assert total==(8388608//256*sum(range(256)) if stage>=2 else 0)
  log=(r/case/'tool.log').read_text().splitlines()
  assert log.count('CONTEXT_BANK_SHAPE banks=8 slots=65536 word_bits=128 flag_bits=16')==1
  assert log.count('STREAM_LOAD_PASS bytes=8388608 offset=0 words=524288')==1
  assert any(x=='ALLOCATION_MICRO_PASS loader_context mode=%d bytes=8388608 repeated_writes=1000000 checksum=1069547520'%mode for x in log)
  out['cases'][str(mode)]={'load_growth_mib':(data[1][3]-data[0][3])/1024,'full_read_growth_mib':(data[2][3]-data[1][3])/1024,
   'same_address_million_writes_growth_mib':(data[3][3]-data[2][3])/1024,
   'kernel_checkpoints_kib':[x[3] for x in data],'sample_sha256':sha(r/case/'allocation_samples.csv'),
   'peak_group_rss_kib':w['phases'][case]['peak_group_rss_kib']}
 out['limits']=['No DUT, eight MiB fixed pattern, one seed/tool environment; not a full-DUT resource guarantee',
  'All-byte assertions and final repeated-overwrite assertion executed in SV; host independently recomputes aggregate checksum',
  'Same-address writes hold storage capacity fixed; no allocation-internal attribution without additional evidence']
 (r/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
