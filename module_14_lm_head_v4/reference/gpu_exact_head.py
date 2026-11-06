"""CUDA vectorization of the accepted H8/interleave16 arithmetic, not GEMM.

Seven word groups update sixteen FP32 accumulators separately. Multiplication
and addition are separate eager operators, so no FMA or alternative reduction.
Validated against all eight accepted raw-logit SHA256s before corpus collection.
"""
import numpy as np
import torch


class GpuExactHead:
    def __init__(self,weight_path,device='cuda:0'):
        bits=np.fromfile(weight_path,dtype='<u2').reshape(151936,896)
        self.device=torch.device(device)
        self.weight=torch.from_numpy(bits).view(torch.bfloat16).to(self.device,dtype=torch.float32).reshape(151936,7,16,8)

    @torch.inference_mode()
    def __call__(self,hidden_bf16):
        if isinstance(hidden_bf16,np.ndarray):
            hidden=torch.from_numpy(np.asarray(hidden_bf16,dtype=np.uint16).copy()).view(torch.bfloat16)
        else:hidden=hidden_bf16
        if hidden.dtype!=torch.bfloat16 or hidden.numel()!=896:raise ValueError('Expected 896 BF16 values')
        h=hidden.to(self.device,dtype=torch.float32).reshape(7,16,8)
        partial=torch.zeros((151936,16,8),device=self.device,dtype=torch.float32)
        for group in range(7):
            product=torch.mul(self.weight[:,group,:,:],h[group])
            partial=torch.add(partial,product)
        for width in (8,4,2,1):partial=torch.add(partial[:,:width,:],partial[:,width:2*width,:])
        lanes=partial[:,0,:]
        pairs=torch.add(lanes[:,0::2],lanes[:,1::2])
        halves=torch.add(pairs[:,0::2],pairs[:,1::2])
        return torch.add(halves[:,0],halves[:,1]).cpu().numpy()
