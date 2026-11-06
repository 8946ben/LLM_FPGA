"""Experiments8/9: train/calibration-only fit, coverage and actual GPU timing.

Isolated output r1; no board/EDA/network, no opened holdout evaluation. Stop at
safe batch/config boundaries using reports/hyperparameters_20261023_r1/STOP_REQUESTED.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,json,math,os,statistics,struct,sys,time,zlib
os.environ.setdefault('OMP_NUM_THREADS','4');os.environ.setdefault('OPENBLAS_NUM_THREADS','4');os.environ.setdefault('MKL_NUM_THREADS','4')
import numpy as np
import torch
M=Path(__file__).resolve().parents[1];ROOT=M.parent;sys.path.insert(0,str(M))
from reference.hyperparameter_study import (V,H,SPECIAL,preview_numpy,route_numpy,vote_lists,pure_route_candidates,exact_gpu,dot_batch_gpu,preview_gpu,apply_seen_gpu)
from reference.numeric_contract import bf16_bits_to_float32,float32_to_bf16_bits
from reference.quality_data import load_split,assert_group_disjoint,assert_compatible_collections,recall_report
from reference.hyperparameter_router_recipe import train_router
from reference.candidate_head import run_candidate_head
OUT=M/'reports/hyperparameters_20261023_r1';OLD=M/'reports/selector_p2_20261021'
CASES=['chinese','english','code','math'];START=time.perf_counter()
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');t.replace(p)
def progress(stage,**extra):
    d=dict(stage=stage,updated=now(),pid=os.getpid(),elapsed_s=time.perf_counter()-START,board='NOT_RUN',holdout_read=False,**extra)
    write(OUT/'PROGRESS.json',d);print(json.dumps(d,ensure_ascii=False),flush=True)
def stop():
    if (OUT/'STOP_REQUESTED').exists():raise InterruptedError('Requested safe stop at batch/config boundary')
def load_model(path):
    with np.load(path,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def fp(bits):return torch.from_numpy(bf16_bits_to_float32(bits)).to('cuda')
def configs():
    journal=(ROOT/'开发日志.html').read_text(encoding='utf-8');import re
    v=json.loads(re.search(r'<script id="dev-log-data" type="application/json">(.*?)</script>',journal,re.S)[1])['v4_validation']
    return {family:[dict(id=x['id'],parameters=x['parameters'],axes=x['axes']) for x in next(g for g in v['comparisons'] if g['id']==group)['variants']] for family,group in [('cluster','cluster-hyperparameters'),('lowrank','lowrank-hyperparameters')]}
def count_stats(a):
    return dict(mean=float(a.mean()),median=float(np.median(a)),p95=int(np.sort(a)[math.ceil(.95*len(a))-1]),max=int(a.max()),min=int(a.min()))
def summary(hit,k,cal):return dict(quality=recall_report(hit,cal),candidate_decode=count_stats(k[cal['decode']]),candidate_all=count_stats(k))
def qualify_sources(plan):
    assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=4*2**30,'Need4GiB free CUDA memory'
    lock=json.loads((OLD/'PARAMETERS.json').read_text())
    for name in ['route_r128.npz','route_r256.npz','route_r512.npz','lowrank_r128.npz','svd_basis128.npy']:assert sha(OLD/name)==lock[name],name
    weight=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
    assert sha(weight)=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    frozen=json.loads((M/'data/fixed_quality_20261022/IMPLEMENTATION_FREEZE.json').read_text())
    for name,h in frozen['source_sha256'].items():assert sha(M/name)==h,name
    recipe=M/'reference/hyperparameter_router_recipe.py';old_experiment=json.loads((OLD/'EXPERIMENT.lock.json').read_text())
    assert sha(recipe)==old_experiment['router_sha256'],'Isolated training recipe must equal original frozen recipe'
    write(OUT/'SOURCE_AUDIT.json',dict(isolated_training_recipe_sha256=sha(recipe),historical_training_recipe_sha256=old_experiment['router_sha256'],working_routing_sha256=sha(M/'reference/routing.py'),working_routing_preserved=True,frozen_implementation_sha_all_match=True))
    return dict(weight=weight,source_sha256={p.relative_to(M).as_posix():sha(p) for p in [Path(__file__),M/'reference/hyperparameter_study.py',recipe,M/'reference/quality_data.py']},old_parameters=lock)
def prepare(plan,train,source):
    dest=OUT/'parameters';dest.mkdir(exist_ok=True)
    parameters={};proof={}
    for c in sorted(set(x['parameters']['C'] for x in plan['cluster'])):
        stop();path=dest/f'cluster_C{c}.npz';progress('PREPARING_CLUSTER',C=c)
        if c in (128,256,512):centers=load_model(OLD/f'route_r{c}.npz')['centers_bf16']
        else:centers=train_router(train['hidden'],train['raw_top_ids'],train['winner'],V,c,max_k=1)['centers_bf16']
        model=vote_lists(train,centers)
        if c in (128,256,512):
            old=load_model(OLD/f'route_r{c}.npz');np.testing.assert_array_equal(model['ranked_ids'][:,:16384],old['ranked_ids']);np.testing.assert_array_equal(np.minimum(model['counts'],16384),old['counts'])
        np.savez_compressed(path,**model);norms=np.sum(bf16_bits_to_float32(centers)**2,axis=1,dtype=np.float32);np.save(dest/f'norms_C{c}.npy',norms,allow_pickle=False)
        if c==128:np.testing.assert_array_equal(norms.view('u4'),np.fromfile(M/'reports/router_fixture_20261021/router.norms.bin',dtype='<u4'))
        parameters[f'C{c}']=dict(path=path.relative_to(OUT).as_posix(),sha256=sha(path),norms_sha256=sha(dest/f'norms_C{c}.npy'),valid_lengths=model['counts'].tolist(),empty_clusters=int((model['counts']==0).sum()),old_prefix_bit_match=c in (128,256,512))
        write(OUT/'PARAMETERS.partial.json',parameters)
    stop();progress('BUILDING_FULL_WEIGHT_ONLY_BASIS')
    w=bf16_bits_to_float32(np.memmap(source['weight'],dtype='<u2',mode='r',shape=(V,H)))
    gram=w.T@w;values,vectors=np.linalg.eigh(gram);basis=vectors[:,::-1].copy()
    for col in range(H):
        pivot=np.argmax(np.abs(basis[:,col]));basis[:,col]*=1 if basis[pivot,col]>=0 else -1
    old_basis=np.load(OLD/'svd_basis128.npy',allow_pickle=False);same=np.array_equal(basis[:,:128].view('u4'),old_basis.view('u4'))
    np.save(dest/'basis896.npy',basis,allow_pickle=False);np.save(dest/'eigenvalues.npy',values[::-1],allow_pickle=False)
    write(OUT/'BASIS_CHECK.json',dict(old128_prefix_bit_identical=same,max_absolute_delta=float(np.abs(basis[:,:128]-old_basis).max()),basis_sha256=sha(dest/'basis896.npy'),fitting='canonical W only, no problem labels'))
    assert same,'Expanded basis differs from frozen128; preserve this run and separately qualify new series before continuing'
    for r in sorted(set(x['parameters']['r'] for x in plan['lowrank'])):
        stop();progress('PREPARING_LOWRANK',rank=r);a=float32_to_bf16_bits(w@basis[:,:r]);b=float32_to_bf16_bits(basis[:,:r]);path=dest/f'lowrank_r{r}.npz'
        if r==128:
            old=load_model(OLD/'lowrank_r128.npz');np.testing.assert_array_equal(a,old['a_bf16']);np.testing.assert_array_equal(b,old['b_bf16']);proof['rank128_factors']='BF16_BIT_IDENTICAL'
        np.savez_compressed(path,a_bf16=a,b_bf16=b);parameters[f'r{r}']=dict(path=path.relative_to(OUT).as_posix(),sha256=sha(path),logical_factor_bytes=2*r*(V+H),rank=r)
        write(OUT/'PARAMETERS.partial.json',parameters)
    del w;write(OUT/'PARAMETERS.json',dict(state='PREPARED',files=parameters,basis_proof=proof,basis_sha256=sha(dest/'basis896.npy')))
    return parameters
def fixture_inputs():
    return {c:(np.fromfile(M/f'reports/lowrank_fixture_20261021/{c}.hidden.bin',dtype='<u2'),np.fromfile(M/f'reports/lowrank_fixture_20261021/{c}.history.bin',dtype='<u4')) for c in CASES}
def seen_ids(history):
    ids=np.arange(V,dtype='u4');return ids[((history[ids>>5]>>(ids&31))&1)!=0]
def arithmetic_proofs(parameters):
    records=[];inputs=fixture_inputs()
    for key,item in parameters.items():
        stop();model=load_model(OUT/item['path']);progress('NUMERIC_CPU_GPU_PROOF',parameter=key)
        for cat,(hidden,history) in inputs.items():
            h=fp(hidden)
            if key.startswith('C'):
                c=int(key[1:]);norms=np.load(OUT/f'parameters/norms_C{c}.npy');order,d=route_numpy(hidden,model['centers_bf16'],norms)
                dist=(exact_gpu(h,h.reshape(1,H))[0]+torch.from_numpy(norms).to('cuda'))-torch.tensor(2.,device='cuda')*exact_gpu(h,fp(model['centers_bf16']))
                np.testing.assert_array_equal(dist.cpu().numpy().view('u4'),d.view('u4'));np.testing.assert_array_equal(torch.argsort(dist,stable=True).cpu().numpy(),order)
            else:
                r=int(key[1:]);p,z=preview_numpy(hidden,model['a_bf16'],model['b_bf16'],seen_ids(history))
                zg=exact_gpu(h,fp(model['b_bf16'].T.copy()));pg=apply_seen_gpu(preview_gpu(zg[None,:],fp(model['a_bf16'])),[seen_ids(history)])[0]
                np.testing.assert_array_equal(zg.cpu().numpy().view('u4'),z.view('u4'));np.testing.assert_array_equal(pg.cpu().numpy().view('u4'),p.view('u4'))
                if r==128:np.testing.assert_array_equal(p.view('u4'),np.fromfile(M/f'reports/lowrank_fixture_20261021/{cat}.scores.bin',dtype='<u4'))
            records.append(dict(parameter=key,case=cat,full_values_bit_match=True))
        del model;torch.cuda.empty_cache();write(OUT/'NUMERIC_PROOF.partial.json',records)
    write(OUT/'NUMERIC_PROOF.json',dict(state='PASS_CPU_GPU_VARIABLE_SHAPE_ARITHMETIC',records=records,scope='Full4 calibration fixture previews/distances per shape, not new RTL'))
def evaluate_cluster(plan,parameters,cal):
    results=[];h=fp(cal['hidden']);hn=torch.cat([exact_gpu(x,x.reshape(1,H)) for x in h]).reshape(-1,1)
    bitcounts=np.array([i.bit_count() for i in range(256)],dtype=np.uint8)
    for c in sorted(set(x['parameters']['C'] for x in plan['cluster'])):
        model=load_model(OUT/parameters[f'C{c}']['path']);norms=np.load(OUT/f'parameters/norms_C{c}.npy');dots=dot_batch_gpu(h,fp(model['centers_bf16']))
        distance=hn+torch.from_numpy(norms).to('cuda')[None,:]-torch.tensor(2.,device='cuda')*dots
        assert bool(torch.isfinite(distance).all());routes=torch.argsort(distance,dim=1,stable=True).cpu().numpy()
        for config in [x for x in plan['cluster'] if x['parameters']['C']==c]:
            stop();p=config['parameters'];R,L=p['R'],p['L'];packed=[]
            for i in range(c):
                mask=np.zeros(V,dtype=bool);mask[model['ranked_ids'][i,:min(L,int(model['counts'][i]))]]=True;packed.append(np.packbits(mask,bitorder='little'))
            packed=np.stack(packed);mandatory=np.zeros(V,dtype=bool);mandatory[SPECIAL]=True;mandatory=np.packbits(mandatory,bitorder='little')
            hits=np.zeros(len(h),bool);k=np.zeros(len(h),dtype='u4');fallback=np.any(model['counts'][routes[:,:R]]==0,axis=1);cache={}
            for row,(chosen,winner) in enumerate(zip(routes[:,:R],cal['winner'])):
                key=tuple(sorted(map(int,chosen)))
                if key not in cache:
                    mask=np.bitwise_or.reduce(packed[list(key)],axis=0)|mandatory;cache[key]=(mask,int(bitcounts[mask].sum()))
                mask,count=cache[key];k[row]=count;hits[row]=bool((mask[int(winner)//8]>>(int(winner)%8))&1)
            used=hits|fallback;effective=np.where(fallback,V,k).astype('u4');path=OUT/f'coverage/cluster_{config["id"]}.npz';path.parent.mkdir(exist_ok=True);np.savez_compressed(path,pure_hits=hits,pure_k=k,fallback=fallback,hits=used,k=effective)
            result=dict(**config,**summary(used,effective,cal),pure_lists=summary(hits,k,cal),dense_fallback_decode_calls=int(fallback[cal['decode']].sum()),dense_fallback_all_calls=int(fallback.sum()),arrays=path.relative_to(OUT).as_posix(),sha256=sha(path),centers_bytes=2*c*H,stored_list_bytes=4*sum(min(L,int(n)) for n in model['counts']))
            results.append(result);write(OUT/'CLUSTER_CALIBRATION.partial.json',results);progress('CLUSTER_CALIBRATION',config=config['id'],completed=len(results),total=len(plan['cluster']),decode_misses=result['quality']['decode']['misses'],K_mean=result['candidate_decode']['mean'])
    baseline=next(r for r in results if r['parameters']==dict(C=128,R=4,L=16384));old=json.loads((M/'reports/PL_ARITHMETIC_CALIBRATION.json').read_text());assert baseline['quality']==old['route'],'Baseline cluster quality drift'
    write(OUT/'CLUSTER_CALIBRATION.json',dict(state='COMPLETE_CALIBRATION_NOT_INDEPENDENT_TEST',configurations=results,baseline_reproduced=True));return results
def evaluate_lowrank(plan,parameters,cal):
    results=[];h=fp(cal['hidden']);n=len(h)
    for r in sorted(set(x['parameters']['r'] for x in plan['lowrank'])):
        stop();model=load_model(OUT/parameters[f'r{r}']['path']);a=fp(model['a_bf16']);z=dot_batch_gpu(h,fp(model['b_bf16'].T.copy()));cs=[x for x in plan['lowrank'] if x['parameters']['r']==r]
        hits={x['id']:np.zeros(n,bool) for x in cs};ks={x['id']:np.zeros(n,dtype='u4') for x in cs}
        for start in range(0,n,4):
            stop();end=min(n,start+4);p=apply_seen_gpu(preview_gpu(z[start:end],a),cal['seen'][start:end]);assert bool(torch.isfinite(p).all())
            order=torch.argsort(p,dim=1,descending=True,stable=True).cpu().numpy()
            for row in range(start,end):
                inverse=np.empty(V,dtype='u4');inverse[order[row-start]]=np.arange(V,dtype='u4');winner=int(cal['winner'][row])
                for config in cs:
                    t=config['parameters']['T'];hits[config['id']][row]=inverse[winner]<t or winner in SPECIAL;ks[config['id']][row]=t+len(SPECIAL)-int(np.sum(inverse[SPECIAL]<t))
            if start%128==0 or end==n:progress('LOWRANK_CALIBRATION',rank=r,predictions_done=end,total=n)
        for config in cs:
            key=config['id'];path=OUT/f'coverage/lowrank_{key}.npz';np.savez_compressed(path,hits=hits[key],k=ks[key]);result=dict(**config,**summary(hits[key],ks[key],cal),factor_logical_bytes=2*r*(V+H),preview_multiply_add_terms=r*(V+H),arrays=path.relative_to(OUT).as_posix(),sha256=sha(path))
            if config['parameters']['T']==V:assert result['quality']['all']['misses']==0 and result['candidate_all']['min']==V
            results.append(result);write(OUT/'LOWRANK_CALIBRATION.partial.json',results)
        del a,z,model;torch.cuda.empty_cache()
    baseline=next(x for x in results if x['parameters']==dict(r=128,T=16384));old=json.loads((M/'reports/PL_ARITHMETIC_CALIBRATION.json').read_text());assert baseline['quality']==old['lowrank'],'Baseline lowrank quality drift'
    write(OUT/'LOWRANK_CALIBRATION.json',dict(state='COMPLETE_CALIBRATION_NOT_INDEPENDENT_TEST',configurations=results,baseline_reproduced=True));return results
def benchmark(plan,parameters,source):
    """Full online Eager pipeline, not the membership shortcuts used above."""
    weight_bits=np.memmap(source['weight'],dtype='<u2',mode='r',shape=(V,H));weights=torch.from_numpy(np.array(weight_bits)).view(torch.bfloat16).to('cuda');inputs=fixture_inputs();mandatory=torch.tensor(SPECIAL.astype('i8'),device='cuda');vocab=torch.arange(V,device='cuda');penalty=torch.tensor(1.1,device='cuda',dtype=torch.float32)
    payload={c:(fp(h),torch.from_numpy(np.isin(np.arange(V),seen_ids(history))).to('cuda')) for c,(h,history) in inputs.items()}
    all_results=[];all_proof=[]
    for family in ['cluster','lowrank']:
        current=None;model=None
        for config in plan[family]:
            stop();p=config['parameters'];key=f'C{p["C"]}' if family=='cluster' else f'r{p["r"]}'
            if current!=key:
                model=load_model(OUT/parameters[key]['path']);current=key
                if family=='cluster':
                    centers=fp(model['centers_bf16']);norms=torch.from_numpy(np.load(OUT/f'parameters/norms_C{p["C"]}.npy')).to('cuda');ranked=torch.from_numpy(model['ranked_ids'].astype('i8')).to('cuda');counts=torch.from_numpy(model['counts'].astype('i8')).to('cuda')
                else:a=fp(model['a_bf16']);bt=fp(model['b_bf16'].T.copy())
            def call(cat,debug=False):
                h,seen=payload[cat]
                if family=='cluster':
                    distance=(exact_gpu(h,h.reshape(1,H))[0]+norms)-torch.tensor(2.,device='cuda')*exact_gpu(h,centers);rr=torch.argsort(distance,stable=True)[:p['R']]
                    pos=torch.arange(p['L'],device='cuda');chosen=ranked[rr,:p['L']];valid=pos[None,:]<counts[rr,None]
                    ids=torch.unique(torch.cat([chosen[valid],mandatory]),sorted=True)
                    if bool((counts[rr]==0).any().item()):ids=vocab
                else:
                    z=exact_gpu(h,bt);preview=apply_seen_gpu(preview_gpu(z[None,:],a),[seen_ids(inputs[cat][1])])[0];top=torch.argsort(preview,descending=True,stable=True)[:p['T']];ids=torch.unique(torch.cat([top,mandatory]),sorted=True)
                raw=exact_gpu(h,weights[ids].to(torch.float32));sc=torch.where(seen[ids],torch.where(raw<0,raw*penalty,raw/penalty),raw);slot=torch.argmax(sc);token=int(ids[slot].item());bits=int(sc[slot].view(torch.int32).item())&0xffffffff;crc=zlib.crc32(struct.pack('<II',token,bits));out=dict(k=ids.numel(),token=token,score_bits=bits,crc=crc)
                if debug:out.update(ids=ids.cpu().numpy().astype('u4'),raw=raw.cpu().numpy())
                return out
            gold={};progress('GPU_FULL_PIPELINE_NUMERIC',family=family,config=config['id'])
            for cat,(hidden,history) in inputs.items():
                if family=='cluster':
                    rr,_=route_numpy(hidden,model['centers_bf16'],np.load(OUT/f'parameters/norms_C{p["C"]}.npy'));ids,fallback=pure_route_candidates(model,rr[:p['R']],p['L']);ids=np.arange(V,dtype='u4') if fallback else ids
                else:
                    preview,_=preview_numpy(hidden,model['a_bf16'],model['b_bf16'],seen_ids(history));ids=np.union1d(np.argsort(-preview,kind='stable')[:p['T']],SPECIAL).astype('u4')
                ref=run_candidate_head(hidden,weight_bits,ids,history);actual=call(cat,True);np.testing.assert_array_equal(actual['ids'],ids);np.testing.assert_array_equal(actual['raw'].view('u4'),ref['raw_scores'].view('u4'))
                gold[cat]=dict(token=ref['selected_token'],score_bits=ref['selected_score_bits'],crc=ref['output_crc'])
                for k,v in gold[cat].items():assert actual[k]==v,(family,config['id'],cat,k)
                all_proof.append(dict(family=family,config=config['id'],case=cat,full_ids_and_raw_bits=True,k=len(ids),**gold[cat]));write(OUT/'GPU_NUMERIC_PROOF.partial.json',all_proof)
            for _ in range(3):
                for cat in CASES:call(cat)
            observations=[]
            for round_id in range(30):
                stop()
                for ci in range(4):
                    cat=CASES[(ci+round_id)%4];torch.cuda.synchronize();t=time.perf_counter_ns();actual=call(cat);torch.cuda.synchronize();elapsed=(time.perf_counter_ns()-t)/1e6
                    for k,v in gold[cat].items():assert actual[k]==v
                    observations.append(dict(case=cat,round=round_id,wall_ms=elapsed,k=actual['k']))
            wall=[x['wall_ms'] for x in observations];result=dict(family=family,**config,calls=len(wall),wall_median_ms=statistics.median(wall),wall_p95_ms=sorted(wall)[math.ceil(.95*len(wall))-1],equivalent_m14_per_s=len(wall)*1000/sum(wall),cases={cat:dict(k=next(x['k'] for x in observations if x['case']==cat),median_ms=statistics.median(x['wall_ms'] for x in observations if x['case']==cat)) for cat in CASES})
            raw=OUT/f'timing/{family}_{config["id"]}.json';write(raw,observations);result.update(raw=raw.relative_to(OUT).as_posix(),sha256=sha(raw));all_results.append(result);write(OUT/'GPU_BENCHMARK.partial.json',all_results);progress('GPU_TIMING',family=family,config=config['id'],completed=len(all_results),total=44,median_ms=result['wall_median_ms'])
    write(OUT/'GPU_NUMERIC_PROOF.json',dict(state='PASS176_FULL_IDS_RAW_BITS_TOKEN_SCORE_CRC',records=all_proof))
    write(OUT/'GPU_BENCHMARK.json',dict(state='COMPLETE_GPU_EAGER_REFERENCE_NOT_FPGA_OR_LLM',configurations=all_results,measurements=sum(x['calls'] for x in all_results),scope='4 fixed calibration fixtures, batch1,3 warmups+30 measurements/case/config; setup/transfer excluded; includes selector, gather, exact, policy, host token/score/CRC; no transformer or TTFT. Sequential config order and thermal drift are limitations. Stage times NOT_MEASURED; no optimized GPU production claim.'))
    return all_results
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['all','prepare','evaluate','benchmark'],default='all');args=ap.parse_args()
    OUT.mkdir(exist_ok=True);assert not (OUT/'RESULT.json').exists(),'Do not overwrite completed experiment'
    torch.set_num_threads(4);torch.set_grad_enabled(False);plan=configs();source=qualify_sources(plan)
    plan_file=OUT/'PLAN.json'
    identity=dict(configurations=plan,source_sha256=source['source_sha256'],train_manifest_sha256=sha(M/'data/hidden_v1/train/MANIFEST.json'),calibration_manifest_sha256=sha(M/'data/hidden_v1/calibration/MANIFEST.json'),canonical_weight_sha256=sha(source['weight']),seed=20261021,iterations=12,fit_scope='train only for clusters; canonical W only for factors',selection_scope='calibration only; no holdout opened',arithmetic='B H8/interleave16 separate FP32 multiply/add; A adjacent8 then nextpow2(ceil(rank/8)) beat tree with positive zero padding; stable ID ties; BF16 RNE',gpu_benchmark='4 frozen calibration fixtures,3 warmup+30timed calls each/config; complete Eager pipeline not FPGA/full LLM',excluded='No holdout labels, board, RTL, EDA or automatic release',torch=torch.__version__,numpy=np.__version__,device=torch.cuda.get_device_name(0))
    if plan_file.exists():assert json.loads(plan_file.read_text(encoding='utf-8'))==identity,'Run source/config drift: preserve existing run and make a new revision'
    else:write(plan_file,identity)
    progress('LOADING_TRAIN_AND_CALIBRATION');train=load_split(M/'data/hidden_v1/train');cal=load_split(M/'data/hidden_v1/calibration');assert_group_disjoint(train,cal);assert_compatible_collections(train,cal)
    assert len(set(train['groups']))==1500 and len(set(cal['groups']))==320 and int(cal['decode'].sum())==4775
    if args.phase in ['all','prepare']:
        assert not (OUT/'PARAMETERS.json').exists(),'Preserve completed parameters; use evaluate/benchmark phase'
        parameters=prepare(plan,train,source);arithmetic_proofs(parameters)
    else:parameters=json.loads((OUT/'PARAMETERS.json').read_text())['files']
    for item in parameters.values():assert sha(OUT/item['path'])==item['sha256']
    if args.phase in ['all','evaluate']:
        assert not (OUT/'CLUSTER_CALIBRATION.json').exists() and not (OUT/'LOWRANK_CALIBRATION.json').exists(),'Do not overwrite completed evaluation'
        assert (OUT/'NUMERIC_PROOF.json').is_file();evaluate_cluster(plan,parameters,cal);evaluate_lowrank(plan,parameters,cal)
    if args.phase in ['all','benchmark']:
        assert not (OUT/'GPU_BENCHMARK.json').exists();benchmark(plan,parameters,source)
    if all((OUT/f).is_file() for f in ['CLUSTER_CALIBRATION.json','LOWRANK_CALIBRATION.json','GPU_BENCHMARK.json']):
        write(OUT/'RESULT.json',dict(state='COMPLETE_FIRST_ROUND_CALIBRATION_AND_GPU_REFERENCE',updated=now(),cluster_configurations=23,lowrank_configurations=21,calibration_prompts=320,decode_steps=4775,gpu_measurements=5280,independent_quality='NOT_RUN_NEW_FINAL_GROUP_REQUIRED_AFTER_SELECTION',joint_search='NOT_STARTED',fpga='NOT_RUN',ttft='NOT_MEASURED',plan_sha256=sha(plan_file),artifacts={n:sha(OUT/n) for n in ['PARAMETERS.json','NUMERIC_PROOF.json','CLUSTER_CALIBRATION.json','LOWRANK_CALIBRATION.json','GPU_NUMERIC_PROOF.json','GPU_BENCHMARK.json']},elapsed_s=time.perf_counter()-START))
        progress('COMPLETE_FIRST_ROUND_NOT_INDEPENDENT_OR_FPGA')
    else:progress('PHASE_COMPLETE',phase=args.phase)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        if OUT.exists():progress('STOPPED_NO_COMPLETION_VERDICT',error=repr(e))
        raise
