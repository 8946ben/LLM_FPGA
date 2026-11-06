"""Separate instrumented selector/exact timings; not replacements for full calls."""
from pathlib import Path
import hashlib,json,statistics,struct,sys,time,zlib,os
import numpy as np
import torch
import run_hyperparameter_studies_20261023 as b
sys.path.insert(0,str(b.M/'experiments/sparse_methods_20261024'))
import sparse_methods as s
from reference.hyperparameter_study import V,H,exact_gpu,preview_gpu,SPECIAL
R=s.R;B=R/'benchmark'
def main():
    torch.set_num_threads(4);torch.set_grad_enabled(False)
    assert not (R/'STAGE_PROFILE.json').exists()
    assert s.read(B/'INDEPENDENT_REVIEW.json')['result_sha256']==b.sha(B/'RESULT.json')
    allrows=s.read(B/'RESULT.json')['configurations'];points=[p for p in allrows if p['mode'] in s.MODES or p['id'] in ['dense','cluster_C128_R4_L16384','lowrank_r128_T16384','hybrid_C128_R4_L16384_r128_T16384']];assert len(points)==72
    b.write(R/'STAGE_PROFILE_ENTRY.json',dict(source_sha256=b.sha(__file__),benchmark_sha256=b.sha(B/'RESULT.json'),points=[p['id'] for p in points],warmups=3,rounds_per_case=10,measurements=2880,scope='Separate synchronized selector and exact/policy/return stages; extra sync barriers change the call, so sums are not the primary full-M14 benchmark'))
    bits=np.memmap(b.ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(V,H));weights=torch.from_numpy(np.array(bits)).view(torch.bfloat16).to('cuda');engine=s.Engine(bits,weights);inputs=b.fixture_inputs();payload={c:(b.fp(h),torch.from_numpy(np.isin(np.arange(V),b.seen_ids(history))).to('cuda')) for c,(h,history) in inputs.items()}
    legacy=s.read(s.FIRST/'PARAMETERS.json')['files'];old=b.load_model(s.FIRST/legacy['C128']['path']);route=dict(centers=b.fp(old['centers_bf16']),norms=torch.from_numpy(np.load(s.FIRST/'parameters/norms_C128.npy')).to('cuda'),ranked=torch.from_numpy(old['ranked_ids'].astype('i8')).to('cuda'),counts=torch.from_numpy(old['counts'].astype('i8')).to('cuda'));del old
    old=b.load_model(s.FIRST/legacy['r128']['path']);low=dict(a=b.fp(old['a_bf16']),bt=b.fp(old['b_bf16'].T.copy()));del old
    vocab=torch.arange(V,device='cuda');special=engine.special;two=torch.tensor(2.,device='cuda');penalty=engine.penalty
    proof={(p['id'],p['case']):p for p in s.read(B/'GPU_NUMERIC_PROOF.json')['records']};observations=[]
    def selector(p,cat):
        h,seen=payload[cat];mode=p['mode']
        if mode in s.MODES:return engine.gpu_ids(p,h,seen)
        if mode=='dense':return vocab
        if mode in ['cluster','hybrid']:
            dist=(exact_gpu(h,h.reshape(1,H))[0]+route['norms'])-two*exact_gpu(h,route['centers']);rr=torch.argsort(dist,stable=True)[:4];chosen=route['ranked'][rr,:16384];valid=torch.arange(16384,device='cuda')[None,:]<route['counts'][rr,None];routed=torch.unique(torch.cat([chosen[valid],special]),sorted=True)
            if bool((route['counts'][rr]==0).any().item()):routed=vocab
        if mode in ['lowrank','hybrid']:
            z=exact_gpu(h,low['bt']);scores=preview_gpu(z[None,:],low['a'])[0];scores=torch.where(seen,torch.where(scores<0,scores*penalty,scores/penalty),scores);top=torch.argsort(scores,descending=True,stable=True)[:16384];ids=torch.unique(torch.cat([top,special]),sorted=True)
        return routed if mode=='cluster' else ids if mode=='lowrank' else torch.unique(torch.cat([routed,ids]),sorted=True)
    def exact(ids,cat,mode):
        h,seen=payload[cat];raw=exact_gpu(h,(weights if mode=='dense' else weights[ids]).float());scores=torch.where(seen[ids],torch.where(raw<0,raw*penalty,raw/penalty),raw);slot=torch.argmax(scores);token=int(ids[slot].item());sb=int(scores[slot].view(torch.int32).item())&0xffffffff;return dict(k=ids.numel(),token=token,score_bits=sb,crc=zlib.crc32(struct.pack('<II',token,sb)))
    rng=np.random.default_rng(20261024)
    for rid in range(-3,10):
        if (R/'STOP_REQUESTED').exists():raise InterruptedError('Profile stop requested')
        for ix in rng.permutation(len(points)):
            point=points[int(ix)]
            for ci,cat in enumerate(b.CASES):
                torch.cuda.synchronize();t=time.perf_counter_ns();ids=selector(point,cat);torch.cuda.synchronize();mid=time.perf_counter_ns();actual=exact(ids,cat,point['mode']);torch.cuda.synchronize();end=time.perf_counter_ns()
                for key,value in actual.items():assert value==proof[point['id'],cat][key]
                if rid>=0:observations.append(dict(id=point['id'],case=cat,round=rid,selector_wall_ms=(mid-t)/1e6,exact_policy_return_wall_ms=(end-mid)/1e6,**actual))
        b.write(R/'PROGRESS.json',dict(stage='STAGE_PROFILE',pid=os.getpid(),updated=b.now(),round=rid,total_rounds=10,board='NOT_RUN',eda='NOT_RUN'))
        print('STAGE_PROFILE_ROUND',rid,flush=True)
    b.write(R/'STAGE_PROFILE_RAW.json',observations);results=[]
    for p in points:
        obs=[x for x in observations if x['id']==p['id']];assert len(obs)==40;results.append(dict(id=p['id'],calls=40,selector_mean_ms=statistics.mean(x['selector_wall_ms'] for x in obs),exact_policy_return_mean_ms=statistics.mean(x['exact_policy_return_wall_ms'] for x in obs)))
    b.write(R/'STAGE_PROFILE.json',dict(state='PASS_SEPARATE_STAGE_PROFILE_2880_CALLS',records=results,measurements=2880,entry_sha256=b.sha(R/'STAGE_PROFILE_ENTRY.json'),raw_sha256=b.sha(R/'STAGE_PROFILE_RAW.json'),limits=s.read(R/'STAGE_PROFILE_ENTRY.json')['scope']));print('STAGE_PROFILE_COMPLETE',flush=True)
if __name__=='__main__':
    assert not (R/'ACTIVE.lock').exists()
    b.write(R/'ACTIVE.lock',dict(pid=os.getpid(),started=b.now(),phase='STAGE_PROFILE',entry=str(Path(__file__).resolve())))
    try:main()
    finally:(R/'ACTIVE.lock').unlink(missing_ok=True)
