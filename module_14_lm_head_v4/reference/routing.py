"""P2 CPU clustering baseline. Approximate screening only, no FPGA timing."""
import numpy as np
from .numeric_contract import bf16_bits_to_float32,float32_to_bf16_bits


def nearest_centers(hidden,centers,route_count=1):
    x=np.asarray(hidden,dtype=np.float32);c=np.asarray(centers,dtype=np.float32)
    if x.ndim!=2 or c.ndim!=2 or x.shape[1]!=c.shape[1] or not 1<=route_count<=len(c):raise ValueError('Invalid router dimensions/count')
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(c)):raise ValueError('Nonfinite routing vector')
    # L2, matching the k-means objective; quantized centers are used at runtime.
    distance=np.sum(x*x,axis=1)[:,None]+np.sum(c*c,axis=1)[None,:]-np.float32(2)*np.matmul(x,c.T)
    return np.argsort(distance,axis=1,kind='stable')[:,:route_count]


def 下·(hidden_bf16,raw_top_ids,dense_winners,vocab_size,clusters,*,iterations=12,seed=20261021,max_k=16384):
    x=bf16_bits_to_float32(np.asarray(hidden_bf16,dtype=np.uint16))
    top=np.asarray(raw_top_ids);winner=np.asarray(dense_winners)
    if x.ndim!=2 or len(x)<clusters or clusters<=0 or iterations<=0:raise ValueError('Insufficient training data for clusters')
    if top.ndim!=2 or len(top)!=len(x) or winner.shape!=(len(x),):raise ValueError('Training label shape mismatch')
    if top.dtype.kind not in 'iu' or winner.dtype.kind not in 'iu' or np.any(top<0) or np.any(top>=vocab_size) or np.any(winner<0) or np.any(winner>=vocab_size):raise ValueError('Global label outside vocabulary')
    if not np.all(np.isfinite(x)):raise ValueError('Nonfinite training hidden')
    rng=np.random.default_rng(seed);centers=x[rng.choice(len(x),clusters,replace=False)].copy()
    for _ in range(iterations):
        labels=nearest_centers(x,centers)[:,0]
        for cluster in range(clusters):
            group=x[labels==cluster]
            if len(group):centers[cluster]=np.mean(group,axis=0,dtype=np.float32)
    center_bits=float32_to_bf16_bits(centers)
    labels=nearest_centers(x,bf16_bits_to_float32(center_bits))[:,0]
    capacity=min(max_k,vocab_size);ranked=np.full((clusters,capacity),0xffffffff,dtype=np.uint32)
    counts=np.zeros(clusters,dtype=np.uint32);training_rows=np.bincount(labels,minlength=clusters).astype('u4')
    rank_weights=np.float64(1)/np.arange(1,top.shape[1]+1,dtype=np.float64)
    for cluster in range(clusters):
        indices=np.flatnonzero(labels==cluster)
        if not len(indices):continue # runtime must use explicit dense fallback
        votes=np.bincount(top[indices].reshape(-1),weights=np.tile(rank_weights,len(indices)),minlength=vocab_size)
        votes+=4*np.bincount(winner[indices],minlength=vocab_size)
        present=np.flatnonzero(votes>0)
        order=present[np.lexsort((present,-votes[present]))][:capacity]
        ranked[cluster,:len(order)]=order;counts[cluster]=len(order)
    return dict(centers_bf16=center_bits,ranked_ids=ranked,counts=counts,training_rows=training_rows,
        vocab_size=np.array(vocab_size,dtype='u4'))


def routed_candidates(model,route_ids,k,mandatory=()):
    vocab=int(model['vocab_size']);ranked=model['ranked_ids'];counts=model['counts']
    routes=np.asarray(route_ids)
    if routes.ndim!=1 or routes.dtype.kind not in 'iu' or not routes.size or np.any(routes<0) or np.any(routes>=len(counts)):raise ValueError('Invalid route IDs')
    if not 0<k<=ranked.shape[1]:raise ValueError('Candidate budget out of range')
    extra=np.asarray(mandatory,dtype=np.int64)
    if np.any(extra<0) or np.any(extra>=vocab):raise ValueError('Mandatory global ID out of range')
    if any(counts[i]==0 for i in routes):return np.arange(vocab,dtype='u4'),True
    union=np.unique(np.concatenate([ranked[i,:min(k,int(counts[i]))] for i in routes]+[extra])).astype('u4')
    return union,False
