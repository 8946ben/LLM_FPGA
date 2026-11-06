"""Full recomputed Eager M14 timing on four preregistered new-cohort inputs."""
import hashlib,math,os,statistics,struct,sys,time,zlib
import numpy as np
import torch
import sparse_quality_common_20261024 as R
sys.path.insert(0,str(R.M/'experiments/sparse_methods_20261024'))
import sparse_methods as S
from reference.hyperparameter_study import exact_gpu,route_numpy,pure_route_candidates
from reference.numeric_contract import compute_raw_logits

@torch.inference_mode()
def main():
    torch.set_num_threads(4);R.checked();R.stop();out=R.OUT/'benchmark';out.mkdir(exist_ok=True)
    assert not (out/'RESULT.json').exists()
    active=(R.OUT/'ACTIVE.lock').open('x');active.write(str(os.getpid()));active.flush()
    try:
        quality=R.read(R.OUT/'QUALITY.json');pairs=quality['configurations'];assert len(pairs)==6
        manifest=R.read(R.M/'data/hidden_sparse_quality_20261024/holdout/MANIFEST.json');inputs={};folder=R.M/'data/hidden_sparse_quality_20261024/holdout'
        for row in manifest['records']:
            if row['category'] in inputs or row['steps']<2:continue
            a=np.load(folder/row['npz']);seen=set(map(int,a['input_ids']));seen.add(int(a['dense_token'][0]));history=np.zeros((S.V+31)//32,'u4')
            for t in seen:history[t>>5]|=np.uint32(1<<(t&31))
            inputs[row['category']]=(a['hidden_bf16'][1].copy(),history,row['id'],row['npz_sha256'])
        assert len(inputs)==4;cases=['chinese','english','code','math']
        plan=dict(created=R.now(),input_rule='First reserved prompt in each category with >=2 predictions, decode step1; no quality-dependent selection',inputs={c:dict(prompt_id=x[2],npz_sha256=x[3],hidden_sha256=hashlib.sha256(x[0].tobytes()).hexdigest(),history_sha256=hashlib.sha256(x[1].tobytes()).hexdigest()) for c,x in inputs.items()},device=torch.cuda.get_device_name(),torch=torch.__version__,backend='PyTorch Eager, same frozen reference arithmetic and block32768 as prior557 benchmark',warmups=3,measured_per_case=30,calls=720,quality_sha256=R.sha(R.OUT/'QUALITY.json'),entry_sha256=R.sha(R.DATA/'EVALUATION_ENTRY_LOCK.json'),scope='4 new fixed inputs, not full1000 latency population or wholeLLM decode')
        R.write(out/'PLAN.json',plan)
        bits=np.memmap(R.WEIGHT,dtype='<u2',mode='r',shape=(S.V,S.H));weights=torch.from_numpy(np.array(bits)).view(torch.bfloat16).to('cuda');engine=S.Engine(bits,weights)
        g={};raw_cpu={};cpu_ids={};gold={};proof=[]
        first=S.FIRST;desc=R.read(first/'PARAMETERS.json')['files']['C128'];model=dict(np.load(first/desc['path']));norms=np.load(first/'parameters/norms_C128.npy')
        centers=R.gpu(R.fp(model['centers_bf16']));ng=R.gpu(norms);special=torch.tensor(S.SPECIAL.astype('i8'),device='cuda');vocab=torch.arange(S.V,device='cuda');p=torch.tensor(1.1,device='cuda',dtype=torch.float32);two=torch.tensor(2.,device='cuda')
        for c,(hb,hist,_,_) in inputs.items():
            seen=S.seen_ids(hist);mask=torch.zeros(S.V,device='cuda',dtype=torch.bool);mask[seen.astype('i8')]=True
            g[c]=(R.gpu(R.fp(hb)),mask);raw_cpu[c]=compute_raw_logits(hb,bits);route,_=route_numpy(hb,model['centers_bf16'],norms)
            for pair in pairs:
                ids=np.arange(S.V,dtype='u4') if pair['mode']=='dense' else pure_route_candidates(model,route[:pair['parameters']['R']],16384)[0] if pair['mode']=='cluster' else engine.cpu_ids(pair,hb,hist)
                score=R.policy(raw_cpu[c][None,:],[seen])[0][ids];j=int(score.argmax());token=int(ids[j]);sb=int(score[j].view('u4'));gold[pair['id'],c]=dict(k=len(ids),token=token,score_bits=sb,crc=zlib.crc32(struct.pack('<II',token,sb)));cpu_ids[pair['id'],c]=ids
        def call(pair,c,debug=False):
            h,seen=g[c];a=pair['parameters']
            if pair['mode']=='dense':ids=vocab
            elif pair['mode']=='partial':ids=engine.gpu_ids(pair,h,seen)
            else:
                dist=(exact_gpu(h,h.reshape(1,S.H))[0]+ng)-two*exact_gpu(h,centers);rr=torch.argsort(dist,stable=True)[:a['R']]
                ranked=torch.from_numpy(model['ranked_ids'][:,:a['L']].astype('i8')).to('cuda') if False else ranked_gpu
                chosen=ranked[rr];valid=torch.arange(a['L'],device='cuda')[None,:]<counts_gpu[rr,None]
                ids=torch.unique(torch.cat([chosen[valid],special]),sorted=True)
                if bool((counts_gpu[rr]==0).any().item()):ids=vocab
            raw=exact_gpu(h,(weights if pair['mode']=='dense' else weights[ids]).float());score=torch.where(seen[ids],torch.where(raw<0,raw*p,raw/p),raw);j=torch.argmax(score);token=int(ids[j].item());sb=int(score[j].view(torch.int32).item())&0xffffffff
            result=dict(k=len(ids),token=token,score_bits=sb,crc=zlib.crc32(struct.pack('<II',token,sb)))
            if debug:result.update(ids=ids.cpu().numpy().astype('u4'),raw=raw.cpu().numpy())
            return result
        ranked_gpu=torch.from_numpy(model['ranked_ids'][:,:16384].astype('i8')).to('cuda');counts_gpu=torch.from_numpy(model['counts'].astype('i8')).to('cuda')
        for pair in pairs:
            for c in cases:
                actual=call(pair,c,True);ids=cpu_ids[pair['id'],c];np.testing.assert_array_equal(actual.pop('ids'),ids);np.testing.assert_array_equal(actual.pop('raw').view('u4'),raw_cpu[c][ids].view('u4'));assert actual==gold[pair['id'],c]
                proof.append(dict(config=pair['id'],case=c,full_ids_raw_bits=True,**actual))
        R.write(out/'NUMERIC_PROOF.json',dict(state='PASS24_FULL_IDS_RAW_BITS',records=proof))
        del raw_cpu,cpu_ids
        for _ in range(3):
            for pair in pairs:
                for c in cases:R.stop();call(pair,c)
        obs={pair['id']:[] for pair in pairs};sentinels=[];rng=np.random.default_rng(20261024)
        dense=next(x for x in pairs if x['mode']=='dense')
        for round in range(30):
            for pos,idx in enumerate(rng.permutation(6)):
                pair=pairs[int(idx)]
                for ci in range(4):
                    R.stop();c=cases[(ci+round+pos)%4];torch.cuda.synchronize();start=time.perf_counter_ns();actual=call(pair,c);torch.cuda.synchronize();ms=(time.perf_counter_ns()-start)/1e6;assert actual==gold[pair['id'],c]
                    obs[pair['id']].append(dict(case=c,round=round,wall_ms=ms,**actual))
            c=cases[round%4];torch.cuda.synchronize();start=time.perf_counter_ns();actual=call(dense,c);torch.cuda.synchronize();sentinels.append(dict(case=c,round=round,wall_ms=(time.perf_counter_ns()-start)/1e6,**actual))
        rows=[]
        for pair in pairs:
            values=obs[pair['id']];ms=[v['wall_ms'] for v in values];path=out/'timing'/(pair['id']+'.json');R.write(path,values)
            rows.append(dict(**pair,calls=120,wall_mean_ms=statistics.mean(ms),wall_median_ms=statistics.median(ms),wall_p95_ms=sorted(ms)[113],equivalent_m14_per_s=120000/sum(ms),cases={c:dict(calls=30,k=gold[pair['id'],c]['k'],mean_ms=statistics.mean(x['wall_ms'] for x in values if x['case']==c)) for c in cases},raw=path.relative_to(R.ROOT).as_posix(),sha256=R.sha(path)))
        R.checked();R.write(out/'DENSE_SENTINELS.json',sentinels);R.write(out/'RESULT.json',dict(state='COMPLETE6_NEW_FIXED_INPUTS',completed=R.now(),configurations=rows,measurements=720,additional_dense_sentinels=30,plan_sha256=R.sha(out/'PLAN.json')));R.progress('BENCHMARK_COMPLETE',configurations=6,calls=720)
    finally:active.close();(R.OUT/'ACTIVE.lock').unlink(missing_ok=True)
if __name__=='__main__':main()
