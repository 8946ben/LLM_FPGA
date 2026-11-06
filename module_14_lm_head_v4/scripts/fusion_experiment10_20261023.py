"""Experiment10 bounded fusion study: immutable train assets, calibration only.

Every grid point has a materialized bitset union (real K, not K-route+Top-T).
No network, board, release-package mutation or opened holdout inputs.
"""
from pathlib import Path
import argparse,itertools,json,math,os,statistics,struct,time,zlib
import numpy as np
import torch
import run_hyperparameter_studies_20261023 as b
from reference.hyperparameter_study import V,H,SPECIAL,exact_gpu,dot_batch_gpu,preview_gpu,apply_seen_gpu,preview_numpy,route_numpy,pure_route_candidates
from reference.quality_data import load_split,recall_report
from reference.candidate_head import run_candidate_head
M=b.M;SOURCE=b.OUT;R=M/'reports/fusion_exp10_20261023_r1';b.OUT=R
CS=[64,128,256,512];RS=[2,4,8];LS=[4096,8192,16384];RANKS=[32,64,128];TS=[2048,4096,8192,16384]
BASE=dict(C=128,R=4,L=16384,r=128,T=16384)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def name(p):return '_'.join(f'{k}{p[k]}' for k in ['C','R','L','r','T'])
def bind():
    source=read(SOURCE/'PLAN.json');assert all(b.sha(M/n)==h for n,h in source['source_sha256'].items())
    assert read(SOURCE/'INDEPENDENT_REVIEW.json')['state']=='PASS_FIRST_ROUND_CALIBRATION_AND_COUNTERBALANCED_GPU_REVIEW'
    parameters=read(SOURCE/'PARAMETERS.json')['files']
    for key in [f'C{x}' for x in CS]+[f'r{x}' for x in RANKS]:assert b.sha(SOURCE/parameters[key]['path'])==parameters[key]['sha256']
    return parameters
def freeze(parameters):
    R.mkdir(exist_ok=True);plan=dict(title='实验10 · 聚类路由＋低秩补充的超参数融合：质量、候选并集与速度',created_namespace='20261023_exp10_r1',source_sha256=b.sha(__file__),arithmetic_source_sha256=b.sha(M/'reference/hyperparameter_study.py'),parameter_manifest_sha256=b.sha(SOURCE/'PARAMETERS.json'),experiment8_9_result_sha256=b.sha(SOURCE/'RESULT.json'),experiment9_joint_result_sha256=b.sha(SOURCE.with_name('hyperparameters_joint_20261023_r1')/'RESULT.json'),grid=dict(C=CS,R=RS,L=LS,r=RANKS,T=TS),grid_points=432,baseline=BASE,
       training='Only original1500 group-fitted centers/lists and weight-only factors; no refit or new data',calibration='Original320 groups/5095 predictions/4775 decode; no opened-test selection',
       fixed='canonical BF16 W/H896/V151936; accepted FP32 arithmetic; penalty1.1;14 special IDs; stable smaller-ID ties; same pure route lists + lowrank Top-T sorted-unique union',
       measurements='All432 points actual bitset union/hits/K/overlap. No conservative K bound substituted for real K.',
       shortlist='Rank by actual mean logical step read bytes among zero-all-prediction-miss, no-fallback, budget-feasible points. Take top5 plus best per rank, at most8 unique; baseline always separate control.',
       final_selection='Minimum actual mean logical step read bytes among qualified shortlist; GPU Eager speed reported separately, not FPGA predictor. Ties by P95 K then lexicographic ID. No outcome-dependent expansion.',
       gate=dict(proposed_decode_overall=.999,proposed_decode_each_category=.999,selection_all_prediction_misses=0,max_p95_K=V//2,max_K=3*V//4,arena_bytes=320*2**20),
       byte_model='2*r*(V+H) +2*C*H +4*selected_valid_list_entries +1792*actualK, excluding common preview/radix/history/control/burst overhead; logical model not measured AXI traffic or latency',
       offline_acceptance=['train/cal identity and primitive numeric proofs','432 actual unions and count/coverage review','shortlist full CPU/GPU ID/raw/token/score/CRC proof and balanced GPU timing','selection lock and fresh complete-group1000 quality, zero exclusions','selected-config Csim/numeric/error/multi-call tests','selected HLS synthesis,Verilog co-sim,200MHz implementation/CDC/DRC','offline PL arena/host-control/source-identity checks and matching hardware/software assets'],
       final_test_policy='Freeze selected config/implementation/entry, then new unopened complete question groups. All old reservations excluded. No final-test tuning or repeated certification.',board='NOT_RUN_NOT_IN_SCOPE',ttft='No FPGA/wholeLLM claim')
    if (R/'PLAN.json').exists():assert read(R/'PLAN.json')==plan,'Source/grid changed; preserve run and make a new revision'
    else:b.write(R/'PLAN.json',plan)
    return plan
def model(parameters,key):return b.load_model(SOURCE/parameters[key]['path'])
def pack_path(family,key):return R/'cache'/f'{family}_{key}.u8'
def cache(parameters,cal):
    assert not (R/'CACHE.json').exists(),'Use saved cache rather than overwrite'
    (R/'cache').mkdir(exist_ok=True);h=b.fp(cal['hidden']);n=len(h);width=V//8;manifest={}
    hp=h.reshape(n,7,16,8);partial=torch.zeros((n,16,8),device='cuda',dtype=torch.float32)
    for i in range(7):partial=partial+hp[:,i]*hp[:,i]
    for w in (8,4,2,1):partial=partial[:,:w]+partial[:,w:2*w]
    hn=b.tree_gpu(partial[:,0])[:,None] if hasattr(b,'tree_gpu') else None
    # base deliberately does not export tree_gpu; exact same adjacent lane tree.
    if hn is None:
        from reference.hyperparameter_study import tree_gpu
        hn=tree_gpu(partial[:,0])[:,None]
    required=np.zeros(V,bool);required[SPECIAL]=True;mandatory_pack=np.packbits(required,bitorder='little')
    for c in CS:
        b.stop();m=model(parameters,f'C{c}');norm=np.load(SOURCE/f'parameters/norms_C{c}.npy');dots=dot_batch_gpu(h,b.fp(m['centers_bf16']));dist=(hn+torch.from_numpy(norm).to('cuda')[None,:])-torch.tensor(2.,device='cuda')*dots
        assert bool(torch.isfinite(dist).all());routes=torch.argsort(dist,dim=1,stable=True).cpu().numpy();np.save(R/f'cache/routes_C{c}.npy',routes,allow_pickle=False)
        for routes_n,limit in itertools.product(RS,LS):
            b.stop();key=f'C{c}_R{routes_n}_L{limit}';path=pack_path('route',key);packed=np.memmap(path,dtype='u1',mode='w+',shape=(n,width));membership=np.zeros((c,width),dtype='u1')
            for i in range(c):
                mask=np.zeros(V,bool);mask[m['ranked_ids'][i,:min(limit,int(m['counts'][i]))]]=True;membership[i]=np.packbits(mask,bitorder='little')
            fallback=np.any(m['counts'][routes[:,:routes_n]]==0,axis=1);reads=np.minimum(m['counts'][routes[:,:routes_n]],limit).sum(axis=1).astype('u4')
            memo={}
            for row,rr in enumerate(routes[:,:routes_n]):
                chosen=tuple(sorted(map(int,rr)))
                if chosen not in memo:memo[chosen]=np.bitwise_or.reduce(membership[list(chosen)],axis=0)|mandatory_pack
                packed[row]=255 if fallback[row] else memo[chosen]
            packed.flush();del packed;aux=R/f'cache/route_{key}.npz';np.savez_compressed(aux,fallback=fallback,list_entries=reads)
            manifest['route:'+key]=dict(path=path.relative_to(R).as_posix(),sha256=b.sha(path),aux=aux.relative_to(R).as_posix(),aux_sha256=b.sha(aux))
            b.write(R/'CACHE.partial.json',manifest);b.progress('EXP10_ROUTE_CACHE',config=key,done=len(manifest),total=48)
        del m;torch.cuda.empty_cache()
    for rank in RANKS:
        b.stop();m=model(parameters,f'r{rank}');a=b.fp(m['a_bf16']);z=dot_batch_gpu(h,b.fp(m['b_bf16'].T.copy()));maps={t:np.memmap(pack_path('lowrank',f'r{rank}_T{t}'),dtype='u1',mode='w+',shape=(n,width)) for t in TS}
        for start in range(0,n,4):
            b.stop();end=min(n,start+4);preview=apply_seen_gpu(preview_gpu(z[start:end],a),cal['seen'][start:end]);assert bool(torch.isfinite(preview).all());order=torch.argsort(preview,dim=1,descending=True,stable=True)[:,:max(TS)].cpu().numpy()
            for local,row in enumerate(range(start,end)):
                for t in TS:
                    mask=np.zeros(V,bool);mask[order[local,:t]]=True;mask[SPECIAL]=True;maps[t][row]=np.packbits(mask,bitorder='little')
            if start%256==0 or end==n:b.progress('EXP10_LOWRANK_CACHE',rank=rank,predictions_done=end,total=n)
        for t,p in maps.items():
            p.flush();path=pack_path('lowrank',f'r{rank}_T{t}');manifest[f'lowrank:r{rank}_T{t}']=dict(path=path.relative_to(R).as_posix(),sha256=b.sha(path))
        del maps,a,z,m;torch.cuda.empty_cache();b.write(R/'CACHE.partial.json',manifest)
    b.write(R/'CACHE.json',dict(state='COMPLETE_FIXED_ARITHMETIC_CANDIDATE_MEMBERSHIP',rows=n,width=width,calibration_manifest_sha256=cal['manifest_sha256'],items=manifest))
def stats(values):return b.count_stats(values)
def scan(parameters,cal,plan):
    assert not (R/'CALIBRATION.json').exists();cache=read(R/'CACHE.json');assert cache['calibration_manifest_sha256']==cal['manifest_sha256'];n=len(cal['hidden']);width=V//8;mask=cal['decode'];lut=np.array([i.bit_count() for i in range(256)],dtype='u1');results=[];(R/'coverage').mkdir(exist_ok=True)
    # Validate every cache SHA once before deriving any fusion results.
    for item in cache['items'].values():assert b.sha(R/item['path'])==item['sha256']
    for c,routes_n,limit in itertools.product(CS,RS,LS):
        route_key=f'C{c}_R{routes_n}_L{limit}';item=cache['items']['route:'+route_key];rp=np.memmap(R/item['path'],dtype='u1',mode='r',shape=(n,width));aux=b.load_model(R/item['aux']);fallback=aux['fallback'];entries=aux['list_entries']
        for rank,t in itertools.product(RANKS,TS):
            b.stop();p=dict(C=c,R=routes_n,L=limit,r=rank,T=t);key=name(p);lp=np.memmap(R/cache['items'][f'lowrank:r{rank}_T{t}']['path'],dtype='u1',mode='r',shape=(n,width));k=np.empty(n,'u4');route_k=np.empty(n,'u4');lr_k=np.empty(n,'u4');hits=np.empty(n,bool);route_hits=np.empty(n,bool);lr_hits=np.empty(n,bool)
            for start in range(0,n,128):
                end=min(n,start+128);a=rp[start:end];bb=lp[start:end];merged=a|bb;k[start:end]=lut[merged].sum(axis=1);route_k[start:end]=lut[a].sum(axis=1);lr_k[start:end]=lut[bb].sum(axis=1);local=np.arange(end-start);w=cal['winner'][start:end].astype('i8');at=w//8;bit=w%8
                hits[start:end]=((merged[local,at]>>bit)&1)!=0;route_hits[start:end]=((a[local,at]>>bit)&1)!=0;lr_hits[start:end]=((bb[local,at]>>bit)&1)!=0
            np.testing.assert_array_equal(hits,route_hits|lr_hits);q=recall_report(hits,cal);logical=2*rank*(V+H)+2*c*H+4*entries.astype('u8')+1792*k.astype('u8');arena=1048576+256+272269312+1792+18992+2*V*rank+2*H*rank+2*c*H+8*c+4*c*limit+607744+2*607760+1215488+13*128
            gate=q['decode']['recall']>=.999 and all(v['recall']>=.999 for v in q['decode']['by_category'].values());qualified=gate and q['all']['misses']==0 and not fallback.any() and arena<=plan['gate']['arena_bytes'] and int(k[mask].max())<=plan['gate']['max_K'] and stats(k[mask])['p95']<=plan['gate']['max_p95_K']
            path=R/f'coverage/{key}.npz';np.savez_compressed(path,hits=hits,k=k,route_hits=route_hits,lowrank_hits=lr_hits,route_k=route_k,lowrank_k=lr_k,fallback=fallback,list_entries=entries)
            row=dict(id=key,parameters=p,quality=q,proposed_point_gate=gate,selection_qualified=bool(qualified),candidate_decode=stats(k[mask]),overlap_decode=stats((route_k+lr_k-k)[mask]),route_only_decode_misses=int((~route_hits[mask]).sum()),lowrank_only_decode_misses=int((~lr_hits[mask]).sum()),both_missed_decode=int((~hits[mask]).sum()),logical_mean_decode_bytes=float(logical[mask].mean()),estimated_arena_bytes=int(arena),fallback_decode=int(fallback[mask].sum()),arrays=path.relative_to(R).as_posix(),sha256=b.sha(path))
            results.append(row)
        b.write(R/'CALIBRATION.partial.json',results);b.progress('EXP10_GRID',completed=len(results),total=432,qualified=sum(x['selection_qualified'] for x in results))
    qualified=sorted([r for r in results if r['selection_qualified']],key=lambda r:(r['logical_mean_decode_bytes'],r['candidate_decode']['p95'],r['id']));assert qualified,'No qualified calibration fusion; preserve failure rather than open test'
    chosen=qualified[:5]
    for rank in RANKS:
        item=next((x for x in qualified if x['parameters']['r']==rank),None)
        if item and not any(x['id']==item['id'] for x in chosen):chosen.append(item)
    assert len(chosen)<=8;baseline=next(r for r in results if r['parameters']==BASE);assert baseline['quality']==read(M/'reports/PL_ARITHMETIC_CALIBRATION.json')['hybrid'],'Frozen hybrid calibration drift'
    b.write(R/'CALIBRATION.json',dict(state='COMPLETE432_CALIBRATION_ACTUAL_UNIONS',configurations=results,qualified=len(qualified),shortlist=[x['id'] for x in chosen],objective=plan['final_selection'],baseline=baseline['id'],calibration_manifest_sha256=cal['manifest_sha256']))
    b.write(R/'SHORTLIST.json',dict(state='FROZEN_BEFORE_GPU_TIMING_AND_FINAL_LABELS',configurations=chosen,baseline=baseline,plan_sha256=b.sha(R/'PLAN.json'),calibration_sha256=b.sha(R/'CALIBRATION.json')))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['cache','scan'],required=True);args=ap.parse_args();torch.set_num_threads(4);torch.set_grad_enabled(False);assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=3*2**30
    parameters=bind();plan=freeze(parameters);cal=load_split(M/'data/hidden_v1/calibration');assert len(set(cal['groups']))==320 and int(cal['decode'].sum())==4775
    if args.phase=='cache':cache(parameters,cal)
    else:scan(parameters,cal,plan)
    b.progress('EXP10_PHASE_COMPLETE',phase=args.phase)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        if R.exists():b.progress('EXP10_STOPPED',error=repr(e))
        raise
