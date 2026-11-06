"""Manual finite prepare/evaluate phases. No EDA, board, final holdout or monitor."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time
import numpy as np
import torch
import run_hyperparameter_studies_20261023 as b
M=b.M;ROOT=b.ROOT;sys.path.insert(0,str(M/'experiments/sparse_methods_20261024'))
import sparse_methods as s
from reference.numeric_contract import bf16_bits_to_float32,float32_to_bf16_bits
from reference.hyperparameter_study import V,H,SPECIAL,exact_gpu,dot_batch_gpu
from reference.quality_data import load_split,recall_report,assert_group_disjoint
R=s.R
def write(name,d):b.write(R/name,d)
def progress(stage,**kw):
    d=dict(stage=stage,updated=b.now(),pid=os.getpid(),board='NOT_RUN',eda='NOT_RUN',new_final_labels=False,**kw);write('PROGRESS.json',d);print(json.dumps(d,ensure_ascii=False),flush=True)
def stop():
    if (R/'STOP_REQUESTED').exists():raise InterruptedError('Requested pause at bounded configuration/batch boundary')
def save(key,**arrays):
    path=R/f'parameters/{key}.npz';path.parent.mkdir(exist_ok=True);np.savez_compressed(path,**arrays);return dict(path=path.relative_to(R).as_posix(),sha256=b.sha(path),bytes=path.stat().st_size,logical_bytes=sum(a.nbytes for a in arrays.values()))
def freeze():
    R.mkdir(exist_ok=True);entry=Path(__file__);sources=[entry,Path(s.__file__),M/'reference/hyperparameter_study.py',M/'reference/numeric_contract.py',M/'reference/quality_data.py',s.FIRST/'PARAMETERS.json',ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',M/'data/hidden_v1/train/MANIFEST.json',M/'data/hidden_v1/calibration/MANIFEST.json']
    d=dict(created_namespace='20261024_sparse_methods_r1',authorization='User: more sparse methods, GPU results in overview, then complexity and FPGA suitability; no board/EDA',configurations=s.configurations(),new_configurations=68,train='Only original1500 prompts/23933 predictions. Canonical W constructs indexes. No calibration fitting.',calibration='Only original320 prompts/5095 predictions/4775 decode. Exploratory, not final certification.',partial='16 points: dynamic dims16/32/64/128 x Top1024/4096/16384; static dims32/128 xTop4096/16384. Dynamic rank |hidden|*columnRMS; static rank columnRMS. Adjacent FP32 tree, then policy/TopT/specials.',affinity='18 points: C128/256 x P1/2 weight assignments x R4/8/16/32; plus C128/256,P1,R=C full-vocabulary controls. Canonical W assigned to topP normalized frozen hidden prototypes. Complete lists, no truncation/fallback.',learned='Same18 buckets/point budgets; supervised ridge screen target=winner membership +0.25 normalized harmonic rawTop256 memberships. Only train fit; centered/channel-standardized X, lambda0.01 in mean-loss objective, fold transforms into BF16[C,896] and FP32bias. No LM changes.',lsh='16 points: angular/MIPS-sphere transform x bits8/10 x tables4/8 x Hamming radius0/1. Fixed seed20261024, master8x10 BF16 random planes; complete sorted inverted lists. MIPS w/M,sqrt(1-||w||²/M²), query[h,0]. Not literal ALSH2014 implementation or guaranteed sublinear performance.',numerical='Canonical BF16 candidate rows remain exact FP32H8/interleave16 and penalty1.1; stable small-ID ties;14 specials. Approximation only affects candidate membership.',quality_rules='Report all points/misses/K/categories and full-support endpoints. Do not suppress failed points. Existing final groups not reopened or used for fitting/retuning. No production parameter lock.',gpu='After calibration, all489 old+68new=557 configs same-run4 fixed calibration fixtures,3warmup+30/case,66840 timings+660dense sentinels. No cached previews/IDs in timed calls. CPU fullraw only untimed oracle.',analysis='Per-stage actual GPU timings for representative fixed budgets; exact operation/byte models separately from physical traffic; evaluate sorting, gather, layouts, BRAM and capacity; no EDA qualification',stop='Create this report STOP_REQUESTED and benchmark/STOP_REQUESTED if benchmark running, wait boundary; current actualPID/creation time from ACTIVE.lock/CIM; no automatic next phase',references=[dict(title='Learning to Screen (ICLR2019), inspiration only',url='https://research.google/pubs/learning-to-screen-for-fast-softmax-inference-on-large-vocabulary-neural-networks/'),dict(title='On Symmetric and Asymmetric LSHs for Inner Product Search (ICML2015)',url='https://proceedings.mlr.press/v37/neyshabur15.html')],source_sha256={p.relative_to(ROOT).as_posix():b.sha(p) for p in sources},board='NOT_RUN',eda='NOT_RUN')
    if (R/'PLAN.json').exists():
        assert json.loads((R/'PLAN.json').read_text(encoding='utf-8'))==d,'Preserve prior frozen source/configuration; new revision required for changes'
    else:write('PLAN.json',d)
    return d

def prepare():
    assert not (R/'PARAMETERS.json').exists(),'Preserve completed assets'
    train=load_split(M/'data/hidden_v1/train');cal=load_split(M/'data/hidden_v1/calibration');assert_group_disjoint(train,cal)
    assert len(set(train['groups']))==1500 and len(train['hidden'])==23933
    bits=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(V,H));w=torch.from_numpy(np.array(bits)).view(torch.bfloat16).to('cuda').float();files={};proof=[]
    rms=torch.sqrt((w*w).mean(dim=0)).cpu().numpy();order=np.argsort(-rms,kind='stable').astype('u4');files['channels']=save('channels',rms=rms,order=order);progress('PREPARE_CHANNELS')
    # One normalized ridge Gram, fit strictly on the original training split.
    x=bf16_bits_to_float32(train['hidden']).astype('f8');mu=x.mean(axis=0);scale=x.std(axis=0);scale=np.maximum(scale,1e-6);xn=(x-mu)/scale;gram=xn.T@xn;gram.flat[::H+1]+=.01*len(x)
    params=s.read(s.FIRST/'PARAMETERS.json')['files'];harmonic=(1/np.arange(1,257,dtype='f8'));harmonic*=.25/harmonic.sum();rows=np.arange(len(x))
    for c in [128,256]:
        stop();item=params[f'C{c}'];assert b.sha(s.FIRST/item['path'])==item['sha256'];old=b.load_model(s.FIRST/item['path']);centers=bf16_bits_to_float32(old['centers_bf16']);del old
        centers=centers/np.maximum(np.linalg.norm(centers,axis=1,keepdims=True),1e-12);prototypes=float32_to_bf16_bits(centers);protos=torch.from_numpy(bf16_bits_to_float32(prototypes)).to('cuda')
        affinities=[]
        for i,h in enumerate(protos):
            if i%16==0:stop()
            affinities.append(exact_gpu(h,w))
        affinities=torch.stack(affinities,dim=1);assignment=torch.argsort(affinities,dim=1,descending=True,stable=True)[:,:2].cpu().numpy().astype('u4');del affinities,protos
        for pp in [1,2]:
            stop();lists=[np.flatnonzero((assignment[:,:pp]==i).any(axis=1)).astype('u4') for i in range(c)];lengths=np.array(list(map(len,lists)),dtype='u4');offsets=np.r_[np.uint32(0),np.cumsum(lengths,dtype='u4')];ids=np.concatenate(lists)
            assert len(ids)==V*pp and np.array_equal(np.unique(ids),np.arange(V,dtype='u4'))
            y=np.zeros((len(x),c),'f8')
            for j in range(pp):
                np.add.at(y,(rows,assignment[train['winner'],j]),1/pp)
                for rank in range(256):np.add.at(y,(rows,assignment[train['raw_top_ids'][:,rank],j]),harmonic[rank]/pp)
            ymu=y.mean(axis=0);coeff=np.linalg.solve(gram,xn.T@(y-ymu));folded=coeff/scale[:,None];bias=(ymu-mu@folded).astype('f4');screen=float32_to_bf16_bits(folded.T.astype('f4'))
            assert np.isfinite(folded).all() and np.isfinite(bias).all()
            key=f'bucket_C{c}_P{pp}';files[key]=save(key,prototypes_bf16=prototypes,screen_bf16=screen,bias=bias,offsets=offsets,ids=ids,assignment=assignment[:,:pp].copy())
            proof.append(dict(key=key,full_support_tokens=int(len(np.unique(ids))),entries=len(ids),empty_buckets=int((lengths==0).sum()),max_bucket=int(lengths.max()),min_bucket=int(lengths.min()),ridge_mean_loss_lambda=.01,fit_train_predictions=len(x)))
            write('PARAMETERS.partial.json',dict(files=files));progress('PREPARE_BUCKETS_AND_RIDGE',C=c,P=pp,entries=len(ids),max_bucket=int(lengths.max()))
    del x,xn,gram,y,train,cal;torch.cuda.empty_cache()
    rng=np.random.default_rng(20261024);master=float32_to_bf16_bits((rng.standard_normal((8,10,H))/np.sqrt(H)).astype('f4'));extra=(rng.standard_normal((8,10))/np.sqrt(H)).astype('f4');norm=torch.sqrt((w*w).sum(dim=1));maximum=norm.max();augmentation=torch.sqrt(torch.clamp(1-(norm/maximum)**2,min=0))
    for nbits in [8,10]:
        stop();planes=master[:,:nbits].reshape(-1,H).copy();planesfp=torch.from_numpy(bf16_bits_to_float32(planes)).to('cuda');projections=[]
        for h in planesfp:projections.append(exact_gpu(h,w))
        projections=torch.stack(projections).reshape(8,nbits,V)
        for kind in ['angular','mips']:
            scores=projections if kind=='angular' else projections/maximum+torch.from_numpy(extra[:,:nbits].copy()).to('cuda')[:,:,None]*augmentation[None,None,:]
            codes=((scores>=0).to(torch.int64)*(1<<torch.arange(nbits,device='cuda'))[None,:,None]).sum(dim=1).cpu().numpy().astype('u4');ids=[];counts=[]
            for table in range(8):
                a=np.argsort(codes[table],kind='stable').astype('u4');assert np.array_equal(np.sort(a),np.arange(V,dtype='u4'));ids.append(a);counts.append(np.bincount(codes[table],minlength=1<<nbits).astype('u4'))
            ids=np.concatenate(ids);counts=np.concatenate(counts);offsets=np.r_[np.uint32(0),np.cumsum(counts,dtype='u4')]
            key=f'hash_{kind}_b{nbits}';files[key]=save(key,planes_bf16=planes,extra=extra[:,:nbits].copy(),max_weight_norm=np.array(float(maximum),'f4'),codes=codes,offsets=offsets,ids=ids)
            proof.append(dict(key=key,tables=8,each_table_full_vocab=True,entries=len(ids),max_bucket=int(counts.max()),empty_buckets=int((counts==0).sum())))
            progress('PREPARE_HASH_INDEX',kind=kind,bits=nbits,max_bucket=int(counts.max()));write('PARAMETERS.partial.json',dict(files=files))
        del projections,scores;torch.cuda.empty_cache()
    write('PARAMETERS.json',dict(state='PREPARED_TRAIN_ONLY_AND_FULL_CANONICAL_WEIGHT_INDEXES',files=files,proof=proof,plan_sha256=b.sha(R/'PLAN.json')));progress('PREPARE_COMPLETE',files=len(files))

def bitmap(model,groups):
    packed=np.zeros((groups,V//8),'u1')
    for g in range(groups):
        ids=model['ids'][model['offsets'][g]:model['offsets'][g+1]];np.bitwise_or.at(packed[g],ids//8,(np.uint8(1)<<(ids%8)).astype('u1'))
    return packed

def evaluate():
    assert not (R/'CALIBRATION.json').exists();cal=load_split(M/'data/hidden_v1/calibration');assert len(cal['hidden'])==5095 and int(cal['decode'].sum())==4775
    bits=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(V,H));weights=torch.from_numpy(np.array(bits)).view(torch.bfloat16).to('cuda');engine=s.Engine(bits,weights);points=s.configurations();results=[];h=torch.from_numpy(bf16_bits_to_float32(cal['hidden'])).to('cuda');lut=np.array([i.bit_count() for i in range(256)],dtype='u1');special=np.zeros(V,bool);special[SPECIAL]=True;mandatory=np.packbits(special,bitorder='little')
    def save_result(pair,hits,ks):
        path=R/f'coverage/{pair["id"]}.npz';path.parent.mkdir(exist_ok=True);np.savez_compressed(path,hits=hits,k=ks)
        row=dict(**pair,quality=recall_report(hits,cal),candidate_decode=b.count_stats(ks[cal['decode']]),candidate_all=b.count_stats(ks),arrays=path.relative_to(R).as_posix(),sha256=b.sha(path),fallback_decode=0)
        results.append(row);write('CALIBRATION.partial.json',dict(configurations=results));progress('CALIBRATION_CONFIG',id=pair['id'],completed=len(results),total=68)
    for choice,ds in [('dynamic',[16,32,64,128]),('static',[32,128])]:
        for dim in ds:
            group=[p for p in points if p['mode']=='partial' and p['parameters']['choice']==choice and p['parameters']['d']==dim];max_t=max(p['parameters']['T'] for p in group);stats={p['id']:(np.empty(len(h),bool),np.empty(len(h),'u4')) for p in group}
            for i in range(len(h)):
                stop();preview,_=engine.partial_gpu(group[0]['parameters'],h[i]);seen=cal['seen'][i].astype('i8');ii=torch.from_numpy(seen).to('cuda');old=preview[ii];preview[ii]=torch.where(old<0,old*engine.penalty,old/engine.penalty);assert bool(torch.isfinite(preview).all())
                order=torch.argsort(preview,descending=True,stable=True)[:max_t].cpu().numpy()
                for pair in group:
                    t=pair['parameters']['T'];ids=order[:t];hits,ks=stats[pair['id']];hits[i]=bool(cal['winner'][i] in ids or cal['winner'][i] in SPECIAL);ks[i]=t+len(SPECIAL)-int(np.isin(SPECIAL,ids).sum())
                if (i+1)%512==0:progress('PARTIAL_PREVIEW_CALIBRATION',choice=choice,d=dim,done=i+1,total=len(h))
            for pair in group:save_result(pair,*stats[pair['id']])
    for mode in ['affinity','learned']:
        for c in [128,256]:
            for pp in [1,2]:
                stop();key=f'bucket_C{c}_P{pp}';cpu=engine.cpu[key];gpu=engine.gpu[key];scores=dot_batch_gpu(h,gpu['prototypes_bf16'] if mode=='affinity' else gpu['screen_bf16'])+(0 if mode=='affinity' else gpu['bias'][None,:]);order=torch.argsort(scores,descending=True,stable=True).cpu().numpy();membership=bitmap(cpu,c)
                for pair in [p for p in points if p['mode']==mode and p['parameters']['C']==c and p['parameters']['P']==pp]:
                    stop();rr=pair['parameters']['R'];hits=np.empty(len(h),bool);ks=np.empty(len(h),'u4')
                    for i in range(len(h)):
                        union=np.bitwise_or.reduce(membership[order[i,:rr]],axis=0)|mandatory;ks[i]=lut[union].sum();w=int(cal['winner'][i]);hits[i]=bool((union[w//8]>>(w%8))&1)
                    if rr==c:assert hits.all() and (ks==V).all()
                    save_result(pair,hits,ks)
                del membership
    for kind in ['angular','mips']:
        for nbits in [8,10]:
            stop();key=f'hash_{kind}_b{nbits}';cpu=engine.cpu[key];gpu=engine.gpu[key];scores=dot_batch_gpu(h,gpu['planes_bf16']);sign=scores.cpu().numpy().reshape(-1,8,nbits)>=0;codes=(sign.astype('u4')*(np.uint32(1)<<np.arange(nbits,dtype='u4'))).sum(axis=2);membership=bitmap(cpu,8*(1<<nbits))
            for pair in [p for p in points if p['mode']=='lsh' and p['parameters']['kind']==kind and p['parameters']['b']==nbits]:
                p=pair['parameters'];masks=np.array([0]+([1<<j for j in range(nbits)] if p['radius'] else []),'u4');hits=np.empty(len(h),bool);ks=np.empty(len(h),'u4')
                for i in range(len(h)):
                    if i%256==0:stop()
                    groups=((codes[i,:p['tables'],None]^masks[None,:])+np.arange(p['tables'])[:,None]*(1<<nbits)).reshape(-1);union=np.bitwise_or.reduce(membership[groups],axis=0)|mandatory;ks[i]=lut[union].sum();w=int(cal['winner'][i]);hits[i]=bool((union[w//8]>>(w%8))&1)
                save_result(pair,hits,ks)
            del membership
    assert len(results)==68
    write('CALIBRATION.json',dict(state='COMPLETE68_EXPLORATORY_CALIBRATION_NOT_FINAL',configurations=results,calibration_manifest_sha256=cal['manifest_sha256'],plan_sha256=b.sha(R/'PLAN.json'),parameters_sha256=b.sha(R/'PARAMETERS.json')));progress('CALIBRATION_COMPLETE',configurations=68)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['prepare','evaluate'],required=True);a=ap.parse_args();torch.set_num_threads(4);torch.set_grad_enabled(False);assert torch.cuda.is_available();freeze();stop()
    assert not (R/'ACTIVE.lock').exists();write('ACTIVE.lock',dict(pid=os.getpid(),started=b.now(),phase=a.phase))
    try:prepare() if a.phase=='prepare' else evaluate()
    finally:(R/'ACTIVE.lock').unlink(missing_ok=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if R.exists():progress('STOPPED_NO_COMPLETION_VERDICT',error=repr(exc))
        raise
