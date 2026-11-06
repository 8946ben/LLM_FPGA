"""Isolated exploratory selectors; original LM and canonical exact head unchanged.

Methods are project prototypes inspired by screening/MIPS, not reproductions.
All candidate sets are sorted unions with the original14 special token IDs.
"""
from pathlib import Path
import json
import numpy as np
import torch
from reference.numeric_contract import bf16_bits_to_float32,compute_raw_logits
from reference.hyperparameter_study import V,H,SPECIAL,exact_gpu,tree_gpu,tree_numpy
M=Path(__file__).resolve().parents[2];ROOT=M.parent
R=M/'reports/sparse_methods_20261024_r1';FIRST=M/'reports/hyperparameters_20261023_r1'
MODES={'partial','affinity','learned','lsh'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def configurations():
    points=[]
    for choice,ds,ts in [('dynamic',[16,32,64,128],[1024,4096,16384]),('static',[32,128],[4096,16384])]:
        for d in ds:
            for t in ts:points.append(dict(id=f'partial_{choice}_d{d}_T{t}',config=f'{choice}_d{d}_T{t}',mode='partial',parameters=dict(choice=choice,d=d,T=t),experiments=[11]))
    for mode,exp in [('affinity',12),('learned',13)]:
        for c in [128,256]:
            for p in [1,2]:
                for rr in [4,8,16,32]:points.append(dict(id=f'{mode}_C{c}_P{p}_R{rr}',config=f'C{c}_P{p}_R{rr}',mode=mode,parameters=dict(C=c,P=p,R=rr),experiments=[exp]))
            points.append(dict(id=f'{mode}_C{c}_P1_R{c}',config=f'C{c}_P1_R{c}',mode=mode,parameters=dict(C=c,P=1,R=c),experiments=[exp]))
    for kind in ['angular','mips']:
        for bits in [8,10]:
            for tables in [4,8]:
                for radius in [0,1]:points.append(dict(id=f'lsh_{kind}_b{bits}_L{tables}_p{radius}',config=f'{kind}_b{bits}_L{tables}_p{radius}',mode='lsh',parameters=dict(kind=kind,b=bits,tables=tables,radius=radius),experiments=[14]))
    assert len(points)==len({p['id'] for p in points})==68
    return points

def seen_ids(history):
    ids=np.arange(V,dtype='u4');return ids[((history[ids>>5]>>(ids&31))&1)!=0]
def policy_cpu(values,seen):
    out=values.copy();old=out[seen];p=np.float32(1.1)
    out[seen]=np.where(old<0,np.multiply(old,p,dtype=np.float32),np.divide(old,p,dtype=np.float32));return out
def rows_from_flat(model,groups):
    return np.unique(np.concatenate([model['ids'][int(model['offsets'][g]):int(model['offsets'][g+1])] for g in groups]+[SPECIAL])).astype('u4')
def variable_gather(g,groups):
    offsets=g['offsets'];starts=offsets[groups];counts=offsets[groups+1]-starts
    maximum=int(counts.max().item())
    positions=torch.arange(maximum,device='cuda')[None,:];valid=positions<counts[:,None]
    return g['ids'][(starts[:,None]+positions)[valid]]

class Engine:
    def __init__(self,weight_bits,weight_gpu):
        self.bits=weight_bits;self.weights=weight_gpu;self.columns=weight_gpu.T.contiguous()
        self.cpu={};self.gpu={};self.special=torch.tensor(SPECIAL.astype('i8'),device='cuda');self.penalty=torch.tensor(1.1,device='cuda',dtype=torch.float32)
        manifest=read(R/'PARAMETERS.json')
        for key,item in manifest['files'].items():
            with np.load(R/item['path'],allow_pickle=False) as f:m={k:f[k].copy() for k in f.files}
            self.cpu[key]=m
            if key=='channels':self.gpu[key]={'rms':torch.from_numpy(m['rms']).to('cuda'),'order':torch.from_numpy(m['order'].astype('i8')).to('cuda')}
            else:
                g={}
                for k in ['prototypes_bf16','screen_bf16','planes_bf16']:
                    if k in m:g[k]=torch.from_numpy(bf16_bits_to_float32(m[k])).to('cuda')
                for k in ['bias','offsets','ids']:
                    if k in m:g[k]=torch.from_numpy(m[k].astype('i8') if k in ['ids','offsets'] else m[k]).to('cuda')
                self.gpu[key]=g

    def partial_cpu(self,p,hidden):
        h=bf16_bits_to_float32(hidden);m=self.cpu['channels']
        dims=np.argsort(-np.multiply(np.abs(h),m['rms'],dtype=np.float32),kind='stable')[:p['d']] if p['choice']=='dynamic' else m['order'][:p['d']]
        out=np.empty(V,'f4')
        for start in range(0,V,4096):
            w=bf16_bits_to_float32(self.bits[start:start+4096][:,dims]);out[start:start+len(w)]=tree_numpy(np.multiply(w,h[dims],dtype=np.float32))
        return out,dims.astype('u4')

    def partial_gpu(self,p,h):
        g=self.gpu['channels'];dims=torch.argsort(torch.abs(h)*g['rms'],descending=True,stable=True)[:p['d']] if p['choice']=='dynamic' else g['order'][:p['d']]
        parts=[]
        for start in range(0,V,32768):
            products=self.columns[dims,start:start+32768].to(torch.float32).T*h[dims]
            parts.append(tree_gpu(products))
        return torch.cat(parts),dims

    def bucket_scores_cpu(self,mode,p,hidden):
        m=self.cpu[f'bucket_C{p["C"]}_P{p["P"]}']
        return compute_raw_logits(hidden,m['prototypes_bf16'] if mode=='affinity' else m['screen_bf16'])+(np.float32(0) if mode=='affinity' else m['bias'])

    def bucket_scores_gpu(self,mode,p,h):
        g=self.gpu[f'bucket_C{p["C"]}_P{p["P"]}']
        return exact_gpu(h,g['prototypes_bf16'] if mode=='affinity' else g['screen_bf16'])+(0 if mode=='affinity' else g['bias'])

    def hash_cpu(self,p,hidden):
        m=self.cpu[f'hash_{p["kind"]}_b{p["b"]}'];scores=compute_raw_logits(hidden,m['planes_bf16']);sign=scores.reshape(8,p['b'])>=0
        return (sign.astype('u4')*(np.uint32(1)<<np.arange(p['b'],dtype='u4'))).sum(axis=1).astype('u4'),scores

    def hash_gpu(self,p,h):
        g=self.gpu[f'hash_{p["kind"]}_b{p["b"]}'];scores=exact_gpu(h,g['planes_bf16']);sign=scores.reshape(8,p['b'])>=0
        return (sign.to(torch.int64)*(1<<torch.arange(p['b'],device='cuda'))).sum(dim=1),scores

    def cpu_ids(self,pair,hidden,history):
        p=pair['parameters'];mode=pair['mode']
        if mode=='partial':
            raw,_=self.partial_cpu(p,hidden);order=np.argsort(-policy_cpu(raw,seen_ids(history)),kind='stable');return np.union1d(order[:p['T']],SPECIAL).astype('u4')
        if mode in ['affinity','learned']:
            scores=self.bucket_scores_cpu(mode,p,hidden);groups=np.argsort(-scores,kind='stable')[:p['R']];return rows_from_flat(self.cpu[f'bucket_C{p["C"]}_P{p["P"]}'],groups)
        codes,_=self.hash_cpu(p,hidden);m=self.cpu[f'hash_{p["kind"]}_b{p["b"]}'];masks=[0]+([1<<j for j in range(p['b'])] if p['radius'] else [])
        groups=np.array([i*(1<<p['b'])+(int(codes[i])^mask) for i in range(p['tables']) for mask in masks]);return rows_from_flat(m,groups)

    def gpu_ids(self,pair,h,seen):
        p=pair['parameters'];mode=pair['mode']
        if mode=='partial':
            raw,_=self.partial_gpu(p,h);scores=torch.where(seen,torch.where(raw<0,raw*self.penalty,raw/self.penalty),raw);top=torch.argsort(scores,descending=True,stable=True)[:p['T']]
            return torch.unique(torch.cat([top,self.special]),sorted=True)
        if mode in ['affinity','learned']:
            scores=self.bucket_scores_gpu(mode,p,h);groups=torch.argsort(scores,descending=True,stable=True)[:p['R']];g=self.gpu[f'bucket_C{p["C"]}_P{p["P"]}']
        else:
            codes,_=self.hash_gpu(p,h);masks=torch.tensor([0]+([1<<j for j in range(p['b'])] if p['radius'] else []),device='cuda',dtype=torch.int64)
            groups=((codes[:p['tables'],None]^masks[None,:])+torch.arange(p['tables'],device='cuda')[:,None]*(1<<p['b'])).flatten();g=self.gpu[f'hash_{p["kind"]}_b{p["b"]}']
        return torch.unique(torch.cat([variable_gather(g,groups),self.special]),sorted=True)

    def prove_primitives(self,inputs,payload):
        proof=[]
        for cat,(hidden,history) in inputs.items():
            h=payload[cat][0]
            for choice,ds in [('dynamic',[16,32,64,128]),('static',[32,128])]:
                for d in ds:
                    p=dict(choice=choice,d=d);a,ad=self.partial_cpu(p,hidden);z,zd=self.partial_gpu(p,h)
                    np.testing.assert_array_equal(z.cpu().numpy().view('u4'),a.view('u4'));np.testing.assert_array_equal(zd.cpu().numpy(),ad);proof.append(dict(case=cat,mode='partial',parameters=p,full_preview_and_dims_bits=True))
            for c in [128,256]:
                for pp in [1,2]:
                    for mode in ['affinity','learned']:
                        p=dict(C=c,P=pp);a=self.bucket_scores_cpu(mode,p,hidden);z=self.bucket_scores_gpu(mode,p,h);np.testing.assert_array_equal(z.cpu().numpy().view('u4'),a.view('u4'));proof.append(dict(case=cat,mode=mode,parameters=p,full_bucket_scores_bits=True))
            for kind in ['angular','mips']:
                for bits in [8,10]:
                    p=dict(kind=kind,b=bits);ac,a=self.hash_cpu(p,hidden);zc,z=self.hash_gpu(p,h);np.testing.assert_array_equal(z.cpu().numpy().view('u4'),a.view('u4'));np.testing.assert_array_equal(zc.cpu().numpy(),ac);proof.append(dict(case=cat,mode='lsh',parameters=p,full_projection_and_codes_bits=True))
        return proof
