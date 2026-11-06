"""CPU online candidate construction. No dense label/logits are inputs.

BF16 factors are expanded to FP32 and evaluated by NumPy BLAS; this is not
the future PL selector's qualified arithmetic or latency contract.
"""
import numpy as np
from .numeric_contract import bf16_bits_to_float32
from .routing import nearest_centers,routed_candidates


def stable_topk_ids(preview,seen,k,penalty=1.1):
    scores=np.asarray(preview,dtype=np.float32).copy()
    history=np.asarray(seen)
    if scores.ndim!=1 or not np.all(np.isfinite(scores)) or not 0<k<=len(scores):raise ValueError('Invalid preview/budget')
    if history.ndim!=1 or history.dtype.kind not in 'iu' or np.any(history<0) or np.any(history>=len(scores)):raise ValueError('Invalid global history')
    if not np.isfinite(penalty) or penalty<1:raise ValueError('Invalid penalty')
    history=np.unique(history);values=scores[history];p=np.float32(penalty)
    scores[history]=np.where(values<0,values*p,values/p)
    if not np.all(np.isfinite(scores)):raise ValueError('Nonfinite policy preview')
    cut=np.partition(scores,len(scores)-k)[len(scores)-k]
    above=np.flatnonzero(scores>cut)
    ties=np.flatnonzero(scores==cut)[:k-len(above)]
    # Output contract is ascending original global ID, not preview-score rank.
    return np.sort(np.concatenate((above,ties))).astype('u4')


def candidate_batches(hidden_bf16,seen,router,a_bf16,b_bf16,mandatory,*,route_count,route_k,lowrank_k,batch_size=32):
    bits=np.asarray(hidden_bf16)
    if bits.dtype!=np.uint16 or bits.ndim!=2 or len(bits)!=len(seen) or batch_size<=0:raise ValueError('Invalid hidden/history batch')
    x=bf16_bits_to_float32(bits);a=bf16_bits_to_float32(a_bf16);b=bf16_bits_to_float32(b_bf16)
    centers=bf16_bits_to_float32(router['centers_bf16'])
    if b.shape[0]!=x.shape[1] or a.shape[1]!=b.shape[1] or a.shape[0]!=int(router['vocab_size']):raise ValueError('Factor/router dimensions differ')
    routes=nearest_centers(x,centers,route_count);memo={}
    for start in range(0,len(x),batch_size):
        stop=min(start+batch_size,len(x));preview=(x[start:stop]@b)@a.T
        for local,row in enumerate(range(start,stop)):
            key=tuple(map(int,routes[row]))
            if key not in memo:memo[key]=routed_candidates(router,routes[row],route_k,mandatory)
            routed,fallback=memo[key]
            coarse=stable_topk_ids(preview[local],seen[row],lowrank_k)
            merged=np.union1d(routed,coarse).astype('u4')
            yield row,merged,dict(route_candidates=len(routed),coarse_candidates=len(coarse),
                overlap=len(routed)+len(coarse)-len(merged),explicit_dense_fallback=bool(fallback),routes=list(key))
