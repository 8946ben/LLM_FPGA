"""Deterministic preview arithmetic experiment; not the CPU BLAS contract.

B projection retains H8/interleave16. A uses adjacent tree8 per 128bit beat,
then adjacent tree16 over beats. Only screening changes; final exact head is
untouched. This module never reads a holdout or fits parameters.
"""
import numpy as np
from .numeric_contract import bf16_bits_to_float32,compute_raw_logits

def adjacent_tree(values):
    x=np.asarray(values,dtype=np.float32)
    if x.shape[-1]==0 or x.shape[-1]&(x.shape[-1]-1):raise ValueError('power of two required')
    while x.shape[-1]>1:x=np.add(x[...,0::2],x[...,1::2],dtype=np.float32)
    return x[...,0]

def lowrank_preview(hidden_bf16,a_bf16,b_bf16,seen=(),penalty=1.1,enable=True):
    a=np.asarray(a_bf16);b=np.asarray(b_bf16)
    if a.dtype!=np.uint16 or a.ndim!=2 or a.shape[1]!=128 or not 1<=len(a)<=151936 or b.dtype!=np.uint16 or b.shape!=(896,128):raise ValueError('BF16 rank128 factors required')
    if enable and (not np.isfinite(np.float32(penalty)) or penalty<1):raise ValueError('invalid penalty')
    z=compute_raw_logits(hidden_bf16,b.T.copy())
    p=np.multiply(bf16_bits_to_float32(a).reshape(-1,16,8),z.reshape(1,16,8),dtype=np.float32)
    scores=adjacent_tree(adjacent_tree(p))
    if enable:
        raw_ids=np.asarray(seen)
        if raw_ids.ndim!=1 or (raw_ids.size and raw_ids.dtype.kind not in 'iu') or np.any(raw_ids<0) or np.any(raw_ids>=len(a)):raise ValueError('invalid global history')
        ids=np.unique(raw_ids.astype(np.int64));v=scores[ids]
        scores[ids]=np.where(v<0,np.multiply(v,np.float32(penalty),dtype=np.float32),np.divide(v,np.float32(penalty),dtype=np.float32))
    if not np.all(np.isfinite(scores)):raise FloatingPointError('nonfinite preview')
    return scores,z

def router_ids(hidden_bf16,centers_bf16,center_norms):
    h=np.asarray(hidden_bf16,dtype=np.uint16);centers=np.asarray(centers_bf16,dtype=np.uint16)
    if h.shape!=(896,) or centers.shape!=(128,896):raise ValueError('router dimensions')
    norm=np.asarray(center_norms,dtype=np.float32)
    if norm.shape!=(128,) or not np.all(np.isfinite(norm)) or np.any(norm<0):raise ValueError('center norms')
    hn=compute_raw_logits(h,h.reshape(1,-1))[0]
    dot=compute_raw_logits(h,centers)
    distance=np.subtract(np.add(hn,norm,dtype=np.float32),np.multiply(np.float32(2),dot,dtype=np.float32),dtype=np.float32)
    if not np.all(np.isfinite(distance)):raise FloatingPointError('nonfinite distance')
    return np.argsort(distance,kind='stable')[:4].astype('u4'),distance
