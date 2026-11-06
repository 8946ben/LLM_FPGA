"""Audit a read-only live prefix; never marks a complete segment PASS."""
from pathlib import Path
import json,sys,runpy,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/sim_memory_bank_20261026'
S=Path(sys.argv[1]).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expect=json.loads((E/'sentinels.json').read_text());actual=[]
for line in (S/'weights_readback.csv').read_text().splitlines():
 a,v,err=line.split(',');assert int(err)==0;actual.append(dict(address=int(a),value=int(v,16)))
assert expect==actual and len(actual)==1522
saved=sys.argv;parser=ROOT/'tools/analyze_partial_signal_vcd_20261026.py'
sys.argv=[str(parser),str(S/'preview_partial.vcd'),str(S/'AXI_PREFIX.json')]
try:g=runpy.run_path(str(parser))
finally:sys.argv=saved
assert all(x['equal'] for x in g['reads'])
fixture=M/'experiments/partial_hw_20261024/fixtures';raw=np.fromfile(fixture/'old_chinese.preview.bin','<u4');keys=np.fromfile(fixture/'old_chinese.keys.bin','<u4');dims=np.fromfile(fixture/'old_chinese.dims.bin','<u4');counts={};origin=1523*16
for name,base,e in [('raw',37984*16,raw[:5120]),('keys',0,keys[:5120]),('dims',79052*16,dims)]:
 values={}
 for w in g['writes']:
  off=w['address']-origin-base
  if 0<=off<len(e)*4:
   assert w['strobe']==65535;first=off//4;value=int(w['data'],16)
   for lane in range(4):
    idx=first+lane;got=(value>>(lane*32))&0xffffffff
    assert got==int(e[idx]),(name,idx,hex(got),hex(int(e[idx])))
    assert idx not in values;values[idx]=got
 counts[name]=len(values)
result=dict(state='PASS_SAVED_PREFIX_ONLY_NOT_COMPLETE_QUALIFICATION',model_sentinel_bytes=1522,all_saved_read_beats=len(g['reads']),read_data_mismatches=0,
 verified_written_values=counts,last_time_ps=g['time'],trace_sha256=sha(S/'preview_partial.vcd'),readback_sha256=sha(S/'weights_readback.csv'),
 full_first5_complete=False,board='NOT_RUN',scope='Copied while simulation ran; incomplete tail line ignored; original job untouched')
(S/'PREFIX_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
