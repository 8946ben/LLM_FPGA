"""Independent finite-segment review; never grants complete CoSim qualification."""
from pathlib import Path
import sys,runpy,json,hashlib,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/sim_memory_bank_20261026_r1';E=M/'experiments/sim_memory_bank_20261026'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 work=json.loads((R/'PREVIEW_WORKFLOW.json').read_text());assert work['state']=='SEGMENT_RETURNED_AWAITING_INDEPENDENT_VCD_REVIEW'
 plan=json.loads((R/'PREVIEW_PLAN.json').read_text())
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 full=json.loads((R/'FULL_TV_INPUT_REVIEW.json').read_text());assert full['state']=='PASS_FULL_ORIGINAL_TV_RECONSTRUCTION_SHA' and full['total_beats']==34105344
 expected=json.loads((E/'sentinels.json').read_text());actual=[]
 for line in (R/'weights_readback.csv').read_text().splitlines():
  a,v,err=line.split(',');assert int(err)==0;actual.append(dict(address=int(a),value=int(v,16)))
 assert expected==actual and len(actual)==1522
 parser=ROOT/'tools/analyze_partial_signal_vcd_20261026.py';saved=sys.argv
 sys.argv=[str(parser),str(R/'preview5.vcd'),str(R/'AXI_TRACE_REVIEW.json')]
 try:g=runpy.run_path(str(parser))
 finally:sys.argv=saved
 reads,writes=g['reads'],g['writes'];assert len(reads)==40960 and all(x['equal'] for x in reads)
 assert all(x['address']<9175040 for x in reads)
 raw={};keys={};dims={};origin=1523*16
 for w in writes:
  assert w['strobe']==65535
  offset=w['address']-origin
  for base,count,dst in [(37984*16,5120,raw),(0,5120,keys),(79052*16,64,dims)]:
   if base<=offset<base+count*4:
    first=(offset-base)//4;value=int(w['data'],16)
    for lane in range(4):
     idx=first+lane;assert idx not in dst,(base,idx);dst[idx]=(value>>(lane*32))&0xffffffff
 fixtures=M/'experiments/partial_hw_20261024/fixtures'
 for name,count,values in [('preview',5120,raw),('keys',5120,keys),('dims',64,dims)]:
  assert set(values)==set(range(count)),(name,len(values))
  a=np.array([values[i] for i in range(count)],dtype='<u4');e=np.fromfile(fixtures/('old_chinese.'+name+'.bin'),'<u4')[:count]
  assert np.array_equal(a,e),(name,np.flatnonzero(a!=e)[:10])
  a.tofile(R/('RTL_PREVIEW5_'+name+'.u32.bin'))
 log=(R/'preview_simulate.log').read_text();assert re.search(r'^BANK_FULL_INPUT_SENTINEL_PASS checked=1522$',log,re.M) and re.search(r'^BANK_PREVIEW5_STOP \d+ ps$',log,re.M)
 result=dict(state='PASS_FIRST5_PREVIEW_FULL_ARRAYS_AND_FULL_INPUT_SENTINELS',
  raw_values=5120,key_values=5120,dims=64,weight_read_beats=len(reads),read_data_mismatches=0,sentinel_bytes=1522,
  original_full_input_sha_review=full,trace_sha256=sha(R/'preview5.vcd'),
  actual_array_sha256={p.name:sha(p) for p in R.glob('RTL_PREVIEW5_*.u32.bin')},
  independent_reviewer_sha256=sha(Path(__file__)),
  scope='First5 blocks of one original hidden/history only; exact candidate path and full151936 preview not executed in this segment',
  full_cosim_qualification=False,implementation_200mhz='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
 (R/'PREVIEW_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
