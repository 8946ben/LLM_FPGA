"""FP32 scale + low-bit, per-token/hidden-axis groups; versioned local format."""
import hashlib,json,math,struct
from pathlib import Path
import numpy as np

H=896

def parameters(w,bits,group,symmetric):
    if bits not in (4,6,8,12) or H%group:raise ValueError('Unsupported quantization format')
    a=np.asarray(w,dtype=np.float32).reshape(len(w),-1,group)
    if not np.isfinite(a).all():raise ValueError('Nonfinite source')
    if symmetric:
        limit=(1<<(bits-1))-1
        scale=np.max(np.abs(a),axis=2)/np.float32(limit)
        scale=np.where(scale==0,np.float32(1),scale).astype('f4')
        zero=np.zeros_like(scale,dtype='i4')
    else:
        lo=np.minimum(a.min(axis=2),np.float32(0));hi=np.maximum(a.max(axis=2),np.float32(0))
        scale=(hi-lo)/np.float32((1<<bits)-1)
        scale=np.where(scale==0,np.float32(1),scale).astype('f4')
        zero=np.clip(np.rint(-lo/scale),0,(1<<bits)-1).astype('i4')
    return scale,zero

def quantize(w,bits,group,symmetric,grid=None):
    scale,zero=parameters(w,bits,group,symmetric) if grid is None else grid
    a=np.asarray(w,dtype='f4').reshape(len(w),-1,group)
    q=np.rint(a/scale[:,:,None])+zero[:,:,None]
    low,high=(-(1<<(bits-1))+1,(1<<(bits-1))-1) if symmetric else (0,(1<<bits)-1)
    q=np.clip(q,low,high).astype('i2')
    deq=np.multiply(q.astype('f4')-zero[:,:,None].astype('f4'),scale[:,:,None],dtype='f4').reshape(len(w),H)
    return q,scale,zero,deq

def pack(path,q,scale,zero,bits,group,symmetric):
    rows=len(q);values=8//math.gcd(8,bits);nbytes=values*bits//8
    a=(q.astype('i4')&((1<<bits)-1)).astype('u8').reshape(rows,H//group,-1,values)
    accum=np.zeros(a.shape[:-1],dtype='<u8')
    for k in range(values):accum|=a[:,:,:,k]<<np.uint64(k*bits)
    payload=accum.view('u1').reshape(*accum.shape,8)[...,:nbytes].reshape(rows,H//group,-1)
    sb=np.asarray(scale,dtype='<f4').view('u1').reshape(rows,H//group,4)
    parts=[payload,sb]
    if not symmetric:
        zb=np.asarray(zero,dtype='<u2').view('u1').reshape(rows,H//group,2)[:,:,:math.ceil(bits/8)]
        parts.append(zb)
    records=np.concatenate(parts,axis=2).reshape(rows,-1)
    row_bytes=((records.shape[1]+63)//64)*64
    image=np.zeros((rows,row_bytes),dtype='u1');image[:,:records.shape[1]]=records
    meta=dict(format='M14_V4B_PACKED_WEIGHT_V1',rows=rows,hidden=H,bits=bits,group=group,symmetric=symmetric,
              scale='FP32_LE',zero_bytes=0 if symmetric else math.ceil(bits/8),row_bytes=row_bytes,header_bytes=256)
    header=json.dumps(meta,separators=(',',':')).encode()
    if len(header)>255:raise ValueError('Header too large')
    path=Path(path)
    with path.open('wb') as f:f.write(header+b'\0'*(256-len(header)));f.write(image.tobytes())
    return meta

def unpack(path):
    path=Path(path)
    with path.open('rb') as f:m=json.loads(f.read(256).split(b'\0')[0])
    rows,group,bits=m['rows'],m['group'],m['bits'];ng=H//group
    raw=np.memmap(path,dtype='u1',offset=256,mode='r',shape=(rows,m['row_bytes']))
    payload_bytes=group*bits//8;record_bytes=payload_bytes+4+m['zero_bytes']
    records=np.array(raw[:,:ng*record_bytes]).reshape(rows,ng,record_bytes)
    # Independent bit-position extraction (not a reversal of the packing loop).
    q=np.empty((rows,ng,group),dtype='i2');p=records[:,:,:payload_bytes]
    for k in range(group):
        bit=k*bits;byte=bit//8;shift=bit%8
        word=p[:,:,byte].astype('u4')
        if byte+1<payload_bytes:word|=p[:,:,byte+1].astype('u4')<<8
        if shift+bits>16:word|=p[:,:,byte+2].astype('u4')<<16
        val=((word>>shift)&((1<<bits)-1)).astype('i4')
        if m['symmetric']:val=np.where(val>=(1<<(bits-1)),val-(1<<bits),val)
        q[:,:,k]=val
    scale=records[:,:,payload_bytes:payload_bytes+4].copy().view('<f4').reshape(rows,ng)
    zero=np.zeros((rows,ng),dtype='i4')
    if m['zero_bytes']:
        zero=records[:,:,payload_bytes+4].astype('i4')
        if m['zero_bytes']==2:zero|=records[:,:,payload_bytes+5].astype('i4')<<8
    if not np.isfinite(scale).all() or np.any(scale<=0):raise ValueError('Invalid packed scale')
    deq=np.multiply(q.astype('f4')-zero[:,:,None].astype('f4'),scale[:,:,None],dtype='f4').reshape(rows,H)
    return m,q,scale,zero,deq

def raw_fp32(hidden,weight,block=4096):
    """Independent CPU reference in the original word/slot update order."""
    h=np.asarray(hidden,dtype='f4').reshape(112,8);out=np.empty(len(weight),dtype='f4')
    for start in range(0,len(weight),block):
        w=np.asarray(weight[start:start+block],dtype='f4').reshape(-1,112,8)
        p=np.zeros((len(w),8,16),dtype='f4')
        for word in range(112):
            slot=word&15
            p[:,:,slot]=np.add(p[:,:,slot],np.multiply(w[:,word],h[word],dtype='f4'),dtype='f4')
        for width in (8,4,2,1):p[:,:,:width]=np.add(p[:,:,:width],p[:,:,width:2*width],dtype='f4')
        lanes=p[:,:,0]
        pairs=np.add(lanes[:,0::2],lanes[:,1::2],dtype='f4')
        halves=np.add(pairs[:,0::2],pairs[:,1::2],dtype='f4')
        out[start:start+len(w)]=np.add(halves[:,0],halves[:,1],dtype='f4')
    return out
