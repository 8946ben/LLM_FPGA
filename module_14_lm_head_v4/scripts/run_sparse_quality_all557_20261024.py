"""Supplementary census on the already-opened1000 cohort; no tuning/training/EDA."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time
from datetime import datetime,timezone,timedelta
import numpy as np
import torch
M=Path(__file__).resolve().parents[1];ROOT=M.parent
sys.path[:0]=[str(M),str(M/'experiments/sparse_methods_20261024')]
import sparse_methods as S
from reference.hyperparameter_study import V,H,SPECIAL,dot_batch_gpu,exact_gpu,preview_gpu,apply_seen_gpu,tree_gpu
from reference.quality_data import load_split,recall_report
from reference.numeric_contract import bf16_bits_to_float32
OUT=M/'reports/sparse_quality_all557_20261024_r1';FIRST=S.FIRST
PREVIOUS=M/'reports/sparse_quality_20261024_r1';DATA=M/'data/hidden_sparse_quality_20261024/holdout'
WIDTH=V//8;LUT=np.array([x.bit_count() for x in range(256)],dtype='u1')
mandatory=np.zeros(V,bool);mandatory[SPECIAL]=True;MANDATORY=np.packbits(mandatory,bitorder='little')
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(p)
def progress(stage,**kw):
    d=dict(stage=stage,updated=now(),pid=os.getpid(),board='NOT_RUN',eda='NOT_RUN',cohort='ALREADY_OPENED_SUPPLEMENTARY_ANALYSIS',**kw);write(OUT/'PROGRESS.json',d);print(json.dumps(d,ensure_ascii=False),flush=True)
def stop():
    if (OUT/'STOP_REQUESTED').exists():raise InterruptedError('Safe batch/config boundary stop requested')
def fp(x):return torch.from_numpy(bf16_bits_to_float32(x)).to('cuda')
def params():return read(FIRST/'PARAMETERS.json')['files']
def model(key):
    with np.load(FIRST/params()[key]['path'],allow_pickle=False) as a:return {k:a[k].copy() for k in a.files}
def pairs():return read(OUT/'PLAN.json')['configurations']
def route_key(p):return f'C{p["C"]}_R{p["R"]}_L{p["L"]}'
def low_key(p):return f'r{p["r"]}_T{p["T"]}'
def packpath(family,key):return OUT/'cache'/f'{family}_{key}.u8'
def check():
    plan=read(OUT/'PLAN.json')
    for p,h in plan['source_sha256'].items():assert sha(ROOT/p)==h,p
    assert sha(DATA/'MANIFEST.json')==plan['collection_manifest_sha256']
    return plan
def freeze():
    OUT.mkdir(exist_ok=True);assert not (OUT/'PLAN.json').exists(),'Do not overwrite run'
    original=M/'reports/sparse_methods_20261024_r1/benchmark/RESULT.json'
    configs=[{k:p[k] for k in ['id','config','mode','parameters','experiments']} for p in read(original)['configurations']]
    assert len(configs)==len({p['id'] for p in configs})==557
    paths=[Path(__file__),M/'scripts/benchmark_sparse_quality_all557_20261024.py',Path(S.__file__),M/'reference/hyperparameter_study.py',M/'reference/quality_data.py',M/'reference/numeric_contract.py',M/'reference/candidate_head.py',original,PREVIOUS/'QUALITY.json',PREVIOUS/'INDEPENDENT_REVIEW.json',DATA/'MANIFEST.json',M/'data/sparse_quality_20261024/MANIFEST.json',M/'data/sparse_quality_20261024/holdout.jsonl',FIRST/'PARAMETERS.json',S.R/'PARAMETERS.json',ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',M/'scripts/benchmark_sparse_methods_20261024.py',M/'scripts/benchmark_summary_20261024.py',M/'scripts/run_hyperparameter_studies_20261023.py']
    for k,a in params().items():
        p=FIRST/a['path'];assert sha(p)==a['sha256'];paths.append(p)
        if k.startswith('C'):p=FIRST/f'parameters/norms_{k}.npy';assert sha(p)==a['norms_sha256'];paths.append(p)
    for a in read(S.R/'PARAMETERS.json')['files'].values():
        p=S.R/a['path'];assert sha(p)==a['sha256'];paths.append(p)
    for c in ['chinese','english','code','math']:
        for kind in ['hidden','history']:paths.append(M/f'reports/lowrank_fixture_20261021/{c}.{kind}.bin')
    write(OUT/'PLAN.json',dict(created=now(),state='FROZEN_SUPPLEMENTARY_ALL557_NO_TUNING',authorization='User: run all configurations corresponding to original calibration',configurations=configs,original557_sha256=sha(original),collection_manifest_sha256=sha(DATA/'MANIFEST.json'),source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in paths},quality='Same already-opened1000 prompts/15956 predictions/14956 decode; six preregistered results remain untouched. All557 are supplementary characterization, no new certification or parameter fitting.',threshold='Report overall and every category decode>=99%; all failed points retained; full-vocabulary endpoints/fallback distinguished',cache='Untimed actual per-query candidate membership/K, reuse shared primitive results across frozen points; never use cache for timed inference',timing='All557 in one runtime, eight fixed inputs: original4 plus same preregistered new4. Every point3warmup+30/category/cohort=240 measurements,133680 total; separate120/cohort summaries; complete uncached M14 Eager calls, no transformer or FPGA.',stop='This directory STOP_REQUESTED; benchmark/STOP_REQUESTED for active benchmark; safe batch/config/call boundary, no automatic EDA',board='NOT_RUN',eda='NOT_RUN'))
    progress('FROZEN',configurations=557)

def cache():
    plan=check();data=load_split(DATA);assert data['manifest']['prompts']==1000 and len(data['hidden'])==15956
    assert not (OUT/'CACHE.json').exists();(OUT/'cache').mkdir(exist_ok=True)
    items={};points=pairs();n=len(data['hidden']);h=fp(data['hidden'])
    hp=h.reshape(n,7,16,8);s=torch.zeros((n,16,8),device='cuda')
    for g in range(7):s=s+hp[:,g]*hp[:,g]
    for w in (8,4,2,1):s=s[:,:w]+s[:,w:2*w]
    hn=tree_gpu(s[:,0])[:,None];del s,hp
    routes={route_key(p['parameters']):p['parameters'] for p in points if p['mode'] in ['cluster','hybrid']}
    lows={low_key(p['parameters']):p['parameters'] for p in points if p['mode'] in ['lowrank','hybrid']}
    def done(family,key,path,aux=None):
        d=dict(path=path.relative_to(OUT).as_posix(),sha256=sha(path))
        if aux:d.update(aux=aux.relative_to(OUT).as_posix(),aux_sha256=sha(aux))
        items[family+':'+key]=d;write(OUT/'CACHE.partial.json',items);progress('CACHE_FILE_COMPLETE',family=family,key=key,files=len(items))
    for c in sorted({p['C'] for p in routes.values()}):
        stop();m=model(f'C{c}');norms=np.load(FIRST/f'parameters/norms_C{c}.npy');dist=(hn+torch.from_numpy(norms).to('cuda')[None,:])-torch.tensor(2.,device='cuda')*dot_batch_gpu(h,fp(m['centers_bf16']));order=torch.argsort(dist,dim=1,stable=True).cpu().numpy();np.save(OUT/f'cache/routes_C{c}.npy',order,allow_pickle=False)
        for key,p in routes.items():
            if p['C']!=c:continue
            stop();membership=np.zeros((c,WIDTH),'u1')
            for j in range(c):
                ids=m['ranked_ids'][j,:min(p['L'],int(m['counts'][j]))];np.bitwise_or.at(membership[j],ids//8,(np.uint8(1)<<(ids%8)).astype('u1'))
            path=packpath('route',key);assert not path.exists();packed=np.memmap(path,dtype='u1',mode='w+',shape=(n,WIDTH));fallback=np.any(m['counts'][order[:,:p['R']]]==0,axis=1)
            entries=np.minimum(m['counts'][order[:,:p['R']]],p['L']).sum(axis=1).astype('u4');pure_hits=np.empty(n,bool);pure_k=np.empty(n,'u4');memo={}
            for i,rr in enumerate(order[:,:p['R']]):
                if i%512==0:stop()
                k=tuple(sorted(map(int,rr)))
                if k not in memo:
                    union=np.bitwise_or.reduce(membership[list(k)],axis=0)|MANDATORY;memo[k]=(union,int(LUT[union].sum()))
                union,count=memo[k];packed[i]=255 if fallback[i] else union;winner=int(data['winner'][i]);pure_hits[i]=bool((union[winner//8]>>(winner%8))&1);pure_k[i]=count
            packed.flush();del packed,memo;aux=OUT/f'cache/route_{key}.npz';np.savez_compressed(aux,fallback=fallback,list_entries=entries,pure_hits=pure_hits,pure_k=pure_k);done('route',key,path,aux)
        del m,dist;torch.cuda.empty_cache()
    del hn
    for rank in sorted({p['r'] for p in lows.values()}):
        stop();m=model(f'r{rank}');a=fp(m['a_bf16']);z=dot_batch_gpu(h,fp(m['b_bf16'].T.copy()));subset={k:p for k,p in lows.items() if p['r']==rank};maps={k:np.memmap(packpath('lowrank',k),dtype='u1',mode='w+',shape=(n,WIDTH)) for k in subset};batch=4
        for start in range(0,n,batch):
            stop();end=min(n,start+batch);preview=apply_seen_gpu(preview_gpu(z[start:end],a),data['seen'][start:end]);assert bool(torch.isfinite(preview).all());order=torch.argsort(preview,dim=1,descending=True,stable=True).cpu().numpy()
            for local,i in enumerate(range(start,end)):
                for key,p in subset.items():
                    mask=np.zeros(V,bool);mask[order[local,:p['T']]]=True;mask[SPECIAL]=True;maps[key][i]=np.packbits(mask,bitorder='little')
            if start%512==0:progress('LOWRANK_CACHE',rank=rank,done=end,total=n)
        for key,mm in maps.items():mm.flush();done('lowrank',key,packpath('lowrank',key))
        del maps,a,z,m,preview,order;torch.cuda.empty_cache()
    # New partial/bucket/hash primitives, same frozen implementation and parameters.
    weights=torch.from_numpy(np.array(np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(V,H)))).view(torch.bfloat16).to('cuda');engine=S.Engine(None,weights)
    for choice,d in sorted({(p['parameters']['choice'],p['parameters']['d']) for p in points if p['mode']=='partial'}):
        subset=[p for p in points if p['mode']=='partial' and (p['parameters']['choice'],p['parameters']['d'])==(choice,d)];maps={p['id']:np.memmap(packpath('extra',p['id']),dtype='u1',mode='w+',shape=(n,WIDTH)) for p in subset};max_t=max(p['parameters']['T'] for p in subset)
        for i in range(n):
            stop();preview,_=engine.partial_gpu(dict(choice=choice,d=d),h[i]);seen=torch.from_numpy(data['seen'][i].astype('i8')).to('cuda');old=preview[seen];preview[seen]=torch.where(old<0,old*engine.penalty,old/engine.penalty);order=torch.argsort(preview,descending=True,stable=True)[:max_t].cpu().numpy()
            for p in subset:
                mask=np.zeros(V,bool);mask[order[:p['parameters']['T']]]=True;mask[SPECIAL]=True;maps[p['id']][i]=np.packbits(mask,bitorder='little')
            if (i+1)%512==0:progress('PARTIAL_CACHE',choice=choice,d=d,done=i+1,total=n)
        for key,mm in maps.items():mm.flush();done('extra',key,packpath('extra',key))
        del maps
    for mode in ['affinity','learned','lsh']:
        keys=sorted({(p['parameters']['C'],p['parameters']['P']) for p in points if p['mode']==mode}) if mode!='lsh' else sorted({(p['parameters']['kind'],p['parameters']['b']) for p in points if p['mode']==mode})
        for x,y in keys:
            stop();key=f'bucket_C{x}_P{y}' if mode!='lsh' else f'hash_{x}_b{y}';m=engine.cpu[key];g=engine.gpu[key]
            scores=dot_batch_gpu(h,g['prototypes_bf16'] if mode=='affinity' else g['screen_bf16'] if mode=='learned' else g['planes_bf16'])
            if mode=='learned':scores=scores+g['bias'][None,:]
            if mode=='lsh':codes=((scores.cpu().numpy().reshape(-1,8,y)>=0).astype('u4')*(np.uint32(1)<<np.arange(y,dtype='u4'))).sum(axis=2,dtype='u4')
            else:order=torch.argsort(scores,dim=1,descending=True,stable=True).cpu().numpy()
            groups=x if mode!='lsh' else 8*(1<<y);membership=np.zeros((groups,WIDTH),'u1')
            for j in range(groups):
                ids=m['ids'][int(m['offsets'][j]):int(m['offsets'][j+1])];np.bitwise_or.at(membership[j],ids//8,(np.uint8(1)<<(ids%8)).astype('u1'))
            subset=[p for p in points if p['mode']==mode and ((p['parameters'].get('C'),p['parameters'].get('P'))==(x,y) if mode!='lsh' else (p['parameters']['kind'],p['parameters']['b'])==(x,y))]
            for pair in subset:
                p=pair['parameters'];path=packpath('extra',pair['id']);assert not path.exists();packed=np.memmap(path,dtype='u1',mode='w+',shape=(n,WIDTH))
                for i in range(n):
                    if i%512==0:stop()
                    if mode=='lsh':
                        masks=np.array([0]+([1<<j for j in range(y)] if p['radius'] else []),'u4');chosen=((codes[i,:p['tables'],None]^masks[None,:])+np.arange(p['tables'],dtype='u4')[:,None]*np.uint32(1<<y)).reshape(-1)
                    else:chosen=order[i,:p['R']]
                    packed[i]=np.bitwise_or.reduce(membership[chosen],axis=0)|MANDATORY
                packed.flush();del packed;done('extra',pair['id'],path)
            del membership,scores;torch.cuda.empty_cache()
    check();write(OUT/'CACHE.json',dict(state='COMPLETE_FROZEN557_MEMBERSHIP_PRIMITIVES',rows=n,width=WIDTH,items=items,collection_manifest_sha256=sha(DATA/'MANIFEST.json')));progress('CACHE_COMPLETE',files=len(items))

def evaluate():
    check();data=load_split(DATA);cache=read(OUT/'CACHE.json');n=len(data['hidden']);assert n==cache['rows'];assert not (OUT/'QUALITY.json').exists();results=[];(OUT/'coverage').mkdir(exist_ok=True)
    for item in cache['items'].values():assert sha(OUT/item['path'])==item['sha256']
    def mmap(family,key):return np.memmap(OUT/cache['items'][family+':'+key]['path'],dtype='u1',mode='r',shape=(n,WIDTH))
    for index,pair in enumerate(pairs()):
        stop();p=pair['parameters'];mode=pair['mode'];a=bb=None;fallback=np.zeros(n,bool)
        if mode in ['cluster','hybrid']:
            key=route_key(p);a=mmap('route',key);aux=np.load(OUT/cache['items']['route:'+key]['aux']);fallback=aux['fallback'].copy()
        if mode in ['lowrank','hybrid']:bb=mmap('lowrank',low_key(p))
        if mode in S.MODES:a=mmap('extra',pair['id'])
        hits=np.ones(n,bool);k=np.full(n,V,'u4')
        if mode!='dense':
            for start in range(0,n,128):
                stop();end=min(n,start+128);union=a[start:end]|bb[start:end] if mode=='hybrid' else bb[start:end] if mode=='lowrank' else a[start:end];k[start:end]=LUT[union].sum(axis=1);w=data['winner'][start:end].astype('i8');hits[start:end]=((union[np.arange(end-start),w//8]>>(w%8))&1)!=0
        path=OUT/'coverage'/(pair['id']+'.npz');np.savez_compressed(path,hits=hits,k=k,fallback=fallback);q=recall_report(hits,data);mask=data['decode'];kv=k[mask];gate=q['decode']['recall']>=.99 and all(v['recall']>=.99 for v in q['decode']['by_category'].values())
        row=dict(**pair,quality=q,candidate_decode=dict(mean=float(kv.mean()),median=float(np.median(kv)),p95=int(np.sort(kv)[int(np.ceil(.95*len(kv)))-1]),max=int(kv.max()),min=int(kv.min())),gate99='PASS' if gate else 'FAIL',fallback_decode=int(fallback[mask].sum()),arrays=path.relative_to(OUT).as_posix(),sha256=sha(path))
        if mode=='cluster':row['pure_lists_all_misses']=int((~aux['pure_hits']).sum())
        results.append(row)
        if (index+1)%10==0 or index==556:write(OUT/'QUALITY.partial.json',dict(configurations=results));progress('QUALITY_CONFIGS',completed=index+1,total=557)
        del a,bb
    old=read(PREVIOUS/'QUALITY.json')
    for previous in old['configurations']:
        current=next(x for x in results if x['id']==previous['id']);a=np.load(OUT/current['arrays']);b=np.load(ROOT/previous['coverage']);np.testing.assert_array_equal(a['hits'],b['hits']);np.testing.assert_array_equal(a['k'],b['k']);assert current['quality']==previous['report']
    check();write(OUT/'QUALITY.json',dict(state='COMPLETE557_SUPPLEMENTARY_ON_ALREADY_OPENED1000',completed=now(),configurations=results,prompts=1000,predictions=n,decode=int(data['decode'].sum()),excluded=0,first_six_reproduced_exactly=True,collection_manifest_sha256=sha(DATA/'MANIFEST.json'),plan_sha256=sha(OUT/'PLAN.json'),limits='Membership coverage, not new independent certification or closed-loop generation; exact head numeric proofs separately in benchmark. No tuning/training/new labels.'))
    progress('QUALITY_COMPLETE',configurations=557)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['freeze','cache','evaluate'],required=True);a=ap.parse_args();OUT.mkdir(exist_ok=True)
    if a.phase=='freeze':freeze();return
    torch.set_num_threads(4);torch.set_grad_enabled(False);stop();assert not (OUT/'ACTIVE.lock').exists();write(OUT/'ACTIVE.lock',dict(pid=os.getpid(),started=now(),phase=a.phase))
    try:cache() if a.phase=='cache' else evaluate()
    finally:(OUT/'ACTIVE.lock').unlink(missing_ok=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if OUT.exists():progress('STOPPED_NO_COMPLETION_VERDICT',error=repr(exc))
        raise
