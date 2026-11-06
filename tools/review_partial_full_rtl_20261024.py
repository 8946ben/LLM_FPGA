from pathlib import Path
import hashlib,json,re,struct,sys,zlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/partial_rtl_20261024_r1/full_r3';E=M/'experiments/partial_hw_20261024';sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32 as fp,compute_raw_logits
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    work=json.loads((R/'FULL_WORKFLOW.json').read_text());assert work['state']=='TOOL_COMPLETE_AWAITING_FULL_ARRAY_AND_FIFO_REVIEW'
    after=json.loads((R/'PROCESS_AFTER.json').read_text());assert after['owned_process_group_members']==[] and after['active_locks']==0
    plan=json.loads((R/'PLAN.json').read_text())
    for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
    log=(R/'cosim.log').read_text(errors='replace');assert 'PARTIAL_FULL_COSIM_TOOL_PASS' in log and 'PARTIAL_FULL_RTL_REFERENCE_PASS calls=1 full_arrays=1' in log
    assert 'Simulation failed' not in log and 'ERROR:' not in log
    rpt=list((R/'tool_artifacts/sim/report').glob('*cosim.rpt'));assert len(rpt)==1
    report=rpt[0].read_text();match=re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)',report,re.I);assert match,report
    cycles=list(map(int,match.groups()))
    actual=R/'actual_RTL_full_chinese.bin';arr=np.fromfile(actual,'<u4');token,score,crc,k=map(int,arr[:4]);assert k==4109 and len(arr)==4+64+2*151936+2*k
    assert actual.read_bytes()==(M/'reports/partial_hw_20261024_r1/r3/csim_actual/actual_A0.bin').read_bytes()
    dims=arr[4:68];preview=arr[68:68+151936];keys=arr[68+151936:68+2*151936];ids=arr[68+2*151936:68+2*151936+k];raw=arr[-k:]
    meta=(E/'fixtures/old_chinese.meta.bin').read_bytes();hidden=np.frombuffer(meta[:1792],'<u2');h=fp(hidden);rms=np.frombuffer(meta[1792:5376],'<f4');history=np.frombuffer(meta[5376:],'<u4')
    order=np.lexsort((np.arange(896),-np.multiply(np.abs(h),rms,dtype=np.float32)))[:64];assert np.array_equal(dims,order)
    w=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(151936,896))
    for start in range(0,151936,1024):
        p=np.multiply(fp(w[start:start+1024][:,dims]),h[dims],dtype=np.float32)
        while p.shape[1]>1:p=np.add(p[:,::2],p[:,1::2],dtype=np.float32)
        assert np.array_equal(preview[start:start+len(p)],p[:,0].view('u4')),(start,'preview tree')
    policy=preview.view('f4').copy();vid=np.arange(151936);seen=((history[vid>>5]>>(vid&31))&1)!=0
    negative=seen&(policy<0);positive=seen&~(policy<0);policy[negative]=np.multiply(policy[negative],np.float32(1.1),dtype=np.float32);policy[positive]=np.divide(policy[positive],np.float32(1.1),dtype=np.float32)
    b=policy.view('u4').copy();b[policy==0]=0;computedkeys=np.where(b&0x80000000,~b,b^np.uint32(0x80000000)).astype('u4');assert np.array_equal(keys,computedkeys)
    expectedids=np.union1d(np.lexsort((vid,-policy))[:4096],np.arange(151643,151657)).astype('u4');assert np.array_equal(ids,expectedids)
    exact=compute_raw_logits(hidden,w[ids]);assert np.array_equal(raw,exact.view('u4'))
    used=((history[ids>>5]>>(ids&31))&1)!=0;pp=exact.copy();negative=used&(exact<0);positive=used&~(exact<0);pp[negative]=np.multiply(exact[negative],np.float32(1.1),dtype=np.float32);pp[positive]=np.divide(exact[positive],np.float32(1.1),dtype=np.float32)
    ix=int(np.argmax(pp));assert token==ids[ix] and score==pp[ix].view('u4') and crc==zlib.crc32(struct.pack('<II',token,score))
    result=dict(state='PASS_SINGLE_FULL_CONFIG_RTL_ALL_NUMERIC_ARRAYS',calls=1,fixture='old_chinese',candidate_count=k,
                actual_sha256=sha(actual),all_dims_preview_keys_candidates_exact_raw_final_bits='PASS_CANONICAL_CPU_RECOMPUTE_AND_CSIM_BYTES',
                official_latency_cycles_min_average_max=cycles,token=token,score_bits=score,crc=crc,
                config='d64/T4096/B1024/dualW; canonical FP32 H8/interleave16 exact',
                official_cosim_options='binary_tv + random_stall + dataflow_profiling; no_fifo_sizing',
                report_sha256=sha(rpt[0]),source_sha_verified=len(plan['source_sha256']),reviewer_sha256=sha(Path(__file__)),
                fifo_profile_review='PENDING_SEPARATE_REPORT_INSPECTION',
                limitations=['One full nonzero fixture, not full8state/ABA RTL','AXI model cycle count not FPGA DDR timing or decode speed','No200MHz implementation/BSP/ELF/board/TTFT','No new algorithm quality certification'])
    (R/'NUMERIC_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(state=result['state'],K=k,cycles=cycles)))
if __name__=='__main__':main()
