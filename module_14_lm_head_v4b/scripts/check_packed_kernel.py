"""Small actual-buffer CUDA proof before benchmarking."""
import run_quantization as R
import numpy as np
import torch
P=R.local('packed_cuda')
def main():
    torch.set_num_threads(4);rng=np.random.default_rng(20261023)
    weights=rng.normal(size=(7,896)).astype('f4');hidden=rng.normal(size=(3,896)).astype('f4')
    out=R.OUT/'packed_kernel_precheck';out.mkdir(parents=True,exist_ok=True);proofs=[]
    for b in [4,6,8,12]:
     for g in [32,64,128,896]:
      for sym in [True,False]:
        name=f'W{b}_G{g}_{sym}';q,s,z,deq=R.Q.quantize(weights,b,g,sym)
        path=out/(name+'.bin');meta=R.Q.pack(path,q,s,z,b,g,sym)
        engine=P.PackedCuda(out/name,meta)
        buffer=torch.from_numpy(np.fromfile(path,dtype='u1')).to('cuda');h=R.gpu(hidden)
        actual=engine(buffer,h,7).cpu().numpy();expected=np.stack([R.Q.raw_fp32(x,deq) for x in hidden])
        np.testing.assert_array_equal(actual.view('u4'),expected.view('u4'))
        proofs.append(dict(bits=b,group=g,symmetric=sym,rows=7,hidden_inputs=3,full_bits_match=True))
        print('PACKED_KERNEL_PASS',name,flush=True)
    bf16=(weights.view('u4')>>16).astype('u2');actual_weights=R.fp(bf16)
    engine=P.PackedCuda(out/'dense_bf16');buffer=torch.from_numpy(bf16).view(torch.bfloat16).to('cuda')
    actual=engine(buffer,R.gpu(hidden),7).cpu().numpy();expected=np.stack([R.Q.raw_fp32(x,actual_weights) for x in hidden])
    np.testing.assert_array_equal(actual.view('u4'),expected.view('u4'))
    R.write(out/'RESULT.json',dict(state='PASS_32_PACKED_FORMATS_AND_BF16_BUFFER',records=proofs,
      source_sha256=R.sha(R.M/'reference/packed_cuda.py'),scope='7 rows x3 random hidden each; no performance or final quality'))
if __name__=='__main__':main()
