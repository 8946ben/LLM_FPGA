"""Exact coarse-score top-K reference for a bounded-scratch PL design.

Four 8-bit histogram passes find a FP32 cutoff; a final global-ID scan emits
sorted IDs. This is a software design reference, not synthesized selector RTL.
"""
import numpy as np

def radix_topk_ids(policy_scores,k):
    scores=np.asarray(policy_scores,dtype=np.float32)
    if scores.ndim!=1 or not len(scores) or not np.all(np.isfinite(scores)):raise ValueError('Finite FP32 score vector required')
    if isinstance(k,(bool,np.bool_)) or not isinstance(k,(int,np.integer)) or not 0<k<=len(scores):raise ValueError('Integer top-K budget in [1,V] required')
    # Numeric tie semantics treat -0 and +0 equally; raw bit order would not.
    values=scores.copy();values[values==0]=np.float32(0)
    bits=values.view(np.uint32)
    keys=np.where((bits&np.uint32(0x80000000))!=0,~bits,bits^np.uint32(0x80000000)).astype('u4')
    active=np.ones(len(keys),dtype=bool);rank=int(k);prefix=0;passes=[]
    for shift in (24,16,8,0):
        buckets=((keys>>np.uint32(shift))&np.uint32(255)).astype(np.int32)
        histogram=np.bincount(buckets[active],minlength=256)
        descending=np.cumsum(histogram[::-1]);bucket=255-int(np.searchsorted(descending,rank,side='left'))
        rank-=int(histogram[bucket+1:].sum());prefix|=bucket<<shift;active&=buckets==bucket
        passes.append(dict(shift=shift,selected_bucket=bucket,active_scores=int(active.sum()),rank_inside_bucket=rank))
    cutoff=np.uint32(prefix);above=np.flatnonzero(keys>cutoff);ties=np.flatnonzero(keys==cutoff)
    ids=np.sort(np.concatenate((above,ties[:int(k)-len(above)]))).astype('u4')
    assert len(ids)==k
    return ids,dict(passes=passes,strictly_above=len(above),cutoff_ties=len(ties),
        global_id_tie_order='ascending',signed_zero='normalized to +0 for numeric ties',
        proposed_score_store_bytes=4*len(scores),proposed_score_read_bytes=5*4*len(scores),
        scope='Logical score scratch traffic for proposed 4 histograms + final scan only; not measured AXI bytes, HLS cycles or total selector cost')
