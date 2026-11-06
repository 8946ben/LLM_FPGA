"""Full raw-TV + independent canonical recomputation; FIFO qualification separate."""
from pathlib import Path
import json,hashlib,re,struct,zlib,sys,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/full_bank_cosim_20261026_r1'
sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32 as fp,compute_raw_logits
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def tv(name):
 p=next((R/'returned_tv').glob('*_'+name+'.dat'));lines=p.read_text().splitlines();assert lines[-1]=='[[[/runtime]]]'
 return [int(x,16) for x in lines if x.startswith('0x')]
def policy(raw,ids,history):
 p=raw.copy();seen=((history[ids>>5]>>(ids&31))&1)!=0;negative=seen&(p<0);positive=seen&~(p<0)
 p[negative]=np.multiply(p[negative],np.float32(1.1),dtype='f4');p[positive]=np.divide(p[positive],np.float32(1.1),dtype='f4');return p
def main():
 work=json.loads((R/'FULL_WORKFLOW.json').read_text());assert work['state']=='GENERATED_XSIM_AND_C_POSTCHECK_PASS_AWAITING_NUMERIC_AND_FIFO_REVIEW'
 after=json.loads((R/'PROCESS_AFTER.json').read_text());assert after['owned_process_group_members']==[] and after['active_locks']==0
 plan=json.loads((R/'PLAN.json').read_text())
 rebind=json.loads((M/'reports/partial_rtl_20261024_r1/full_r3/PLAN.json').read_text())['only_path_rebind']
 for n,h in plan['source_sha256'].items():
  if n==rebind['path']:
   assert h==rebind['remote_sha256'];continue # Exactly one Linux-only path binding, checked remotely.
  assert sha(ROOT/n)==h,n
 data=np.array([[(v>>(32*j))&0xffffffff for j in range(4)] for v in tv('meta')],dtype='<u4').reshape(-1)
 assert len(data)==80591*4;origin=1523*4;ws=data[origin:]
 fixture=M/'experiments/partial_hw_20261024/fixtures';meta=(fixture/'old_chinese.meta.bin').read_bytes()
 assert data[:origin].tobytes()==meta
 count=tv('candidate_count');assert count==[4109];k=count[0]
 dims=ws[79052*4:79052*4+64];preview=ws[37984*4:37984*4+151936];keys=ws[:151936]
 ids=ws[75969*4:75969*4+k];pairs=ws[76997*4:76997*4+2*k].reshape(k,2)
 assert np.array_equal(ws[75968*4:75969*4],np.array([0x4449344d,0x00040001,k,151936],dtype='<u4'))
 assert np.all(ws[75969*4+k:75969*4+((k+3)//4)*4]==0xffffffff)
 if k&1:assert np.all(ws[76997*4+2*k:76997*4+2*k+2]==0)
 assert np.array_equal(pairs[:,0],ids);raw=pairs[:,1]
 assembled=np.concatenate([np.array([tv('token')[0],tv('score_bits')[0],tv('output_crc')[0],k],dtype='<u4'),dims,preview,keys,ids,raw])
 assert assembled.tobytes()==(R/'actual_RTL_full_chinese.bin').read_bytes()
 assert tv('status')==[0] and tv('preview_read_beats')==[1220608]
 hbits=np.frombuffer(meta[:1792],'<u2');h=fp(hbits);rms=np.frombuffer(meta[1792:5376],'<f4');history=np.frombuffer(meta[5376:],'<u4')
 expected_dims=np.lexsort((np.arange(896),-np.multiply(np.abs(h),rms,dtype='f4')))[:64];assert np.array_equal(dims,expected_dims)
 weights=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin','<u2',mode='r',shape=(151936,896))
 for start in range(0,151936,1024):
  p=np.multiply(fp(weights[start:start+1024][:,dims]),h[dims],dtype='f4')
  while p.shape[1]>1:p=np.add(p[:,::2],p[:,1::2],dtype='f4')
  assert np.array_equal(preview[start:start+len(p)],p[:,0].view('u4')),(start,'preview')
 vid=np.arange(151936,dtype='u4');pp=policy(preview.view('f4'),vid,history);b=pp.view('u4').copy();b[pp==0]=0
 computed=np.where(b&0x80000000,~b,b^np.uint32(0x80000000)).astype('u4');assert np.array_equal(keys,computed)
 chosen=np.union1d(np.lexsort((vid,-pp))[:4096],np.arange(151643,151657)).astype('u4');assert np.array_equal(ids,chosen)
 exact=compute_raw_logits(hbits,weights[ids]);assert np.array_equal(raw,exact.view('u4'))
 scores=policy(exact,ids,history);winner=int(np.argmax(scores));token=int(ids[winner]);score=int(scores[winner].view('u4'));crc=zlib.crc32(struct.pack('<II',token,score))
 assert tv('token')==[token] and tv('score_bits')==[score] and tv('output_crc')==[crc]
 log=(R/'xsim.log').read_text(errors='replace');assert not re.search(r'^(UVM_FATAL|UVM_ERROR|ERROR:|Fatal:)',log,re.M)
 assert re.search(r'^BANK_FULL_INPUT_SENTINEL_PASS checked=1522$',log,re.M)
 guard=re.findall(r'^LMH_RANGE_GUARD_SUMMARY meta_read_bursts=(\d+) meta_write_bursts=(\d+) weight_read_bursts=(\d+)$',log,re.M);assert len(guard)==1 and all(int(x)>0 for x in guard[0])
 with (R/'weights_readback.csv').open() as f:sentinels=list(csv.reader(f))
 addresses=[int(row[0]) for row in sentinels]
 expected_addresses=list(map(int,re.findall(r'byte mismatch at (\d+)',(M/'experiments/sim_memory_bank_20261026/weights_preflight.svh').read_text())))
 assert addresses==expected_addresses and len(addresses)==1522
 tiled=np.memmap(M/'reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin','u1',mode='r');canonical=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin','u1',mode='r')
 for row in sentinels:
  addr,value,err=int(row[0]),int(row[1],16),int(row[2]);assert err==0
  assert value==int(tiled[addr] if addr<len(tiled) else canonical[addr-len(tiled)])
 with (R/'stage_profile.csv').open() as f:profile=[{a:int(b) for a,b in row.items()} for row in csv.DictReader(f)]
 assert len(profile)==6 and {x['stage'] for x in profile}=={-1,0,1,2,3,4} and all(x['frame']==1 for x in profile)
 result=dict(state='PASS_ONE_FULL_GENERATED_RTL_NUMERIC_CALL_FIFO_PENDING',calls=1,dims=64,preview_raw_and_keys=151936,candidates=k,token=token,score_bits=score,crc=crc,
  actual_matches_raw_returned_tv=True,actual_sha256=sha(R/'actual_RTL_full_chinese.bin'),axi_bounds_observer_summary=list(map(int,guard[0])),
  end_guard='NOT_SERIALIZED; actual requests checked by qualified passive AXI bounds observer',stage_profile=profile,
  fifo_profile='PENDING_INDEPENDENT_ACTUAL_DEPTH_OCCUPANCY_AND_BLOCKING_REVIEW',
  official_cosim_formatter='NOT_RUN; no fabricated formatted Pass report',raw_tv_files={p.name:sha(p) for p in (R/'returned_tv').iterdir()},
  reviewer_sha256=sha(Path(__file__)),board='NOT_RUN',automatic_next_stage=False)
 (R/'NUMERIC_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
