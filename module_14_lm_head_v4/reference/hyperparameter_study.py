"""Isolated variable-dimension study primitives; no production/RTL claims."""
import numpy as np
from .numeric_contract import bf16_bits_to_float32,compute_raw_logits

V,H=151936,896
SPECIAL=np.arange(151643,151657,dtype=np.uint32)

def tree_numpy(x):
    x=np.asarray(x,dtype=np.float32)
    if not x.shape[-1] or x.shape[-1]&(x.shape[-1]-1):raise ValueError('power-of-two tree required')
    while x.shape[-1]>1:x=np.add(x[...,0::2],x[...,1::2],dtype=np.float32)
    return x[...,0]

def preview_numpy(hidden,a_bits,b_bits,seen=(),block=4096):
    """H8/interleave16 B dot; adjacent tree8, padded beat tree for A."""
    r=a_bits.shape[1]
    if not 1<=r<=H or b_bits.shape!=(H,r) or a_bits.shape[0]!=V:raise ValueError('factor shape')
    z=compute_raw_logits(hidden,b_bits.T.copy());out=np.empty(V,dtype=np.float32)
    beats=(r+7)//8;tree_beats=1<<(beats-1).bit_length()
    for start in range(0,V,block):
        a=bf16_bits_to_float32(a_bits[start:start+block]);p=np.zeros((len(a),tree_beats*8),dtype=np.float32)
        p[:,:r]=np.multiply(a,z,dtype=np.float32)
        out[start:start+len(a)]=tree_numpy(tree_numpy(p.reshape(len(a),tree_beats,8)))
    ids=np.asarray(seen,dtype=np.int64);old=out[ids];p=np.float32(1.1)
    out[ids]=np.where(old<0,np.multiply(old,p,dtype=np.float32),np.divide(old,p,dtype=np.float32))
    if not np.isfinite(out).all():raise FloatingPointError('nonfinite preview')
    return out,z

def route_numpy(hidden,centers_bits,norms):
    hn=compute_raw_logits(hidden,np.asarray(hidden).reshape(1,H))[0]
    d=np.subtract(np.add(hn,norms,dtype=np.float32),np.multiply(np.float32(2),compute_raw_logits(hidden,centers_bits),dtype=np.float32),dtype=np.float32)
    return np.argsort(d,kind='stable').astype('u4'),d

def vote_lists(train,centers_bits,capacity=V):
    """Original train-only vote recipe, retaining every positive-vote ID."""
    from .hyperparameter_router_recipe import nearest_centers
    x=bf16_bits_to_float32(train['hidden']);labels=nearest_centers(x,bf16_bits_to_float32(centers_bits))[:,0]
    c=len(centers_bits);ranked=np.full((c,capacity),0xffffffff,dtype='u4');counts=np.zeros(c,dtype='u4')
    weights=np.float64(1)/np.arange(1,train['raw_top_ids'].shape[1]+1,dtype=np.float64)
    for i in range(c):
        rows=np.flatnonzero(labels==i)
        if not len(rows):continue
        votes=np.bincount(train['raw_top_ids'][rows].reshape(-1),weights=np.tile(weights,len(rows)),minlength=V)
        votes+=4*np.bincount(train['winner'][rows],minlength=V)
        present=np.flatnonzero(votes>0);ids=present[np.lexsort((present,-votes[present]))][:capacity]
        ranked[i,:len(ids)]=ids;counts[i]=len(ids)
    return dict(centers_bf16=centers_bits,ranked_ids=ranked,counts=counts,training_rows=np.bincount(labels,minlength=c).astype('u4'),vocab_size=np.array(V,dtype='u4'))

def pure_route_candidates(model,routes,limit):
    ids=np.unique(np.concatenate([model['ranked_ids'][i,:min(int(model['counts'][i]),limit)] for i in routes]+[SPECIAL])).astype('u4')
    fallback=bool(np.any(model['counts'][routes]==0))
    return ids,fallback

def tree_gpu(x):
    while x.shape[-1]>1:x=x[...,0::2]+x[...,1::2]
    return x[...,0]

def exact_gpu(h,rows):
    import torch
    w=rows.reshape(-1,7,16,8);hh=h.reshape(7,16,8)
    partial=torch.zeros((len(w),16,8),dtype=torch.float32,device=h.device)
    for group in range(7):partial=partial+w[:,group]*hh[group]
    for width in (8,4,2,1):partial=partial[:,:width]+partial[:,width:2*width]
    return tree_gpu(partial[:,0])

def dot_batch_gpu(h,rows,batch=32):
    import torch
    result=[];w=rows.reshape(-1,7,16,8)
    for start in range(0,len(h),batch):
        hh=h[start:start+batch].reshape(-1,7,16,8)
        p=torch.zeros((len(hh),len(w),16,8),dtype=torch.float32,device=h.device)
        for g in range(7):p=p+w[None,:,g]*hh[:,None,g]
        for width in (8,4,2,1):p=p[:,:,:width]+p[:,:,width:2*width]
        result.append(tree_gpu(p[:,:,0]))
    return torch.cat(result)

def preview_gpu(z,a,block=32768):
    """Batch z[N,r], A[V,r], padding after multiplication, rank128 order unchanged."""
    import torch
    r=a.shape[1];beats=(r+7)//8;tree_beats=1<<(beats-1).bit_length();parts=[]
    for start in range(0,len(a),block):
        product=a[None,start:start+block,:]*z[:,None,:]
        if r!=tree_beats*8:product=torch.nn.functional.pad(product,(0,tree_beats*8-r))
        parts.append(tree_gpu(tree_gpu(product.reshape(len(z),-1,tree_beats,8))))
    return torch.cat(parts,dim=1)

def apply_seen_gpu(preview,seen):
    import torch
    ii=[];jj=[]
    for row,ids in enumerate(seen):ii.extend([row]*len(ids));jj.extend(map(int,ids))
    ri=torch.tensor(ii,device=preview.device,dtype=torch.int64);ci=torch.tensor(jj,device=preview.device,dtype=torch.int64)
    p=torch.tensor(1.1,device=preview.device,dtype=torch.float32);old=preview[ri,ci]
    preview[ri,ci]=torch.where(old<0,old*p,old/p)
    return preview
