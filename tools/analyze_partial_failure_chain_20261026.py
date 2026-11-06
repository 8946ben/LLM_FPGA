from pathlib import Path
import sys,json,hashlib,zlib,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
sys.path.insert(0,str(M))
from reference.numeric_contract import compute_raw_logits
F=M/'experiments/partial_hw_20261024/fixtures';R=M/'reports/partial_rtl_20261024_r1/full_r3';O=M/'reports/partial_rtl_20261026_diagnosis_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def policy(raw,ids,hist):
 p=raw.copy();seen=((hist[ids>>5]>>(ids&31))&1)!=0
 neg=seen&(p<0);pos=seen&~(p<0)
 p[neg]=np.multiply(p[neg],np.float32(1.1),dtype=np.float32)
 p[pos]=np.divide(p[pos],np.float32(1.1),dtype=np.float32)
 return p
def main():
 a=np.fromfile(R/'RTL_RETURNED_WORKSPACE.u32.bin','<u4');v=np.arange(151936,dtype='u4')
 raw=a[37984*4:37984*4+151936];keys=a[:151936]
 meta=(F/'old_chinese.meta.bin').read_bytes();h=np.frombuffer(meta[:1792],'<u2');hist=np.frombuffer(meta[5376:],'<u4')
 pp=policy(raw.view('f4'),v,hist);b=pp.view('u4').copy();b[pp==0]=0
 computedkeys=np.where(b&0x80000000,~b,b^np.uint32(0x80000000)).astype('u4')
 ids=a[75969*4:75969*4+4109];reconstructed=np.union1d(np.lexsort((v,-pp))[:4096],np.arange(151643,151657)).astype('u4')
 pairs=a[76997*4:76997*4+2*4109].reshape(-1,2)
 w=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin','<u2',mode='r',shape=(151936,896))
 exact=compute_raw_logits(h,w[ids]);actual=pairs[:,1]
 final=policy(exact,ids,hist);win=int(np.argmax(final));token=int(ids[win]);score=int(final[win].view('u4'));crc=zlib.crc32(struct.pack('<II',token,score))
 result=dict(state='RETURNED_STAGE_CHAIN_ANALYZED',
  input_workspace_sha256=sha(R/'RTL_RETURNED_WORKSPACE.u32.bin'),
  keys_vs_policy_of_actual_preview_mismatches=int(np.count_nonzero(keys!=computedkeys)),
  ids_vs_stable_top4096_of_actual_preview_mismatches=int(np.count_nonzero(ids!=reconstructed)),
  raw_record_ids_mismatches=int(np.count_nonzero(pairs[:,0]!=ids)),
  exact_raw_vs_canonical_for_actual_ids_mismatches=int(np.count_nonzero(actual!=exact.view('u4'))),
  computed_output=dict(token=token,score_bits=score,crc=crc),
  preview_is_first_observed_bad_stage=True,
  limitation='Offline audit of returned arrays, not an additional RTL run or proof of the cause')
 (O/'STAGE_CHAIN_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
