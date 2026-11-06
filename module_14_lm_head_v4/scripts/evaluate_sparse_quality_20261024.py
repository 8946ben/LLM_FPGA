"""One frozen six-configuration independent audit, not a tuning sweep."""
import os,sys,time,hashlib
import numpy as np
import torch
import sparse_quality_common_20261024 as R
sys.path.insert(0,str(R.M/'experiments/sparse_methods_20261024'))
import sparse_methods as S
from reference.hyperparameter_study import SPECIAL,route_numpy,pure_route_candidates
from reference.quality_data import load_split,recall_report
from reference.numeric_contract import compute_raw_logits

@torch.inference_mode()
def main():
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False
    R.checked();R.stop();assert not (R.OUT/'QUALITY.json').exists(),'Final result cannot be overwritten'
    assert torch.cuda.mem_get_info()[0]>=4*2**30
    active=(R.OUT/'ACTIVE.lock').open('x');active.write(str(os.getpid()));active.flush()
    try:
        data=load_split(R.M/'data/hidden_sparse_quality_20261024/holdout');assert data['manifest']['prompts']==1000 and data['manifest']['excluded_prompts']==0
        configs=R.read(R.OUT/'SELECTION_LOCK.json')['configurations'];n=len(data['hidden'])
        bits=np.memmap(R.WEIGHT,dtype='<u2',mode='r',shape=(S.V,S.H))
        weights=torch.from_numpy(np.array(bits)).view(torch.bfloat16).to('cuda')
        engine=S.Engine(bits,weights);wg=weights.float();cuda=R.CUDA.ExactCuda(R.OUT/'cuda_eval')
        R.validate_dense(cuda,wg)
        first=S.FIRST;entry=R.read(first/'PARAMETERS.json')['files']['C128'];model=dict(np.load(first/entry['path'],allow_pickle=False));norms=np.load(first/'parameters/norms_C128.npy')
        centers=R.gpu(R.fp(model['centers_bf16']));ng=R.gpu(norms)
        from reference.hyperparameter_study import exact_gpu
        penalty=torch.tensor(1.1,device='cuda',dtype=torch.float32)
        special=torch.tensor(SPECIAL.astype('i8'),device='cuda');vocab=torch.arange(S.V,device='cuda')
        outputs={p['id']:dict(hits=np.zeros(n,bool),k=np.zeros(n,'u4'),token=np.zeros(n,'u4'),score_bits=np.zeros(n,'u4'),candidate_sha256=np.empty(n,'U64')) for p in configs}
        proof=[];tested=set();start=time.perf_counter()
        dense_bits=np.concatenate([np.load(R.M/'data/hidden_sparse_quality_20261024/holdout'/r['npz'])['dense_score_bits'] for r in data['manifest']['records']])
        for i,hbits in enumerate(data['hidden']):
            R.stop();h=R.gpu(R.fp(hbits));seen=torch.zeros(S.V,device='cuda',dtype=torch.bool);seen[data['seen'][i].astype('i8')]=True
            dist=(exact_gpu(h,h.reshape(1,S.H))[0]+ng)-torch.tensor(2.,device='cuda')*exact_gpu(h,centers)
            order=torch.argsort(dist,stable=True).cpu().numpy();routes={}
            for rr in (2,4):
                ids,fallback=pure_route_candidates(model,order[:rr],16384)
                assert not fallback,'Unexpected dense fallback must be explicitly reviewed'
                routes[rr]=torch.from_numpy(ids.astype('i8')).to('cuda')
            partial={}
            for d in (64,128):
                raw,dims=engine.partial_gpu(dict(choice='dynamic',d=d),h)
                scores=torch.where(seen,torch.where(raw<0,raw*penalty,raw/penalty),raw)
                partial[d]=torch.argsort(scores,descending=True,stable=True)
            category=str(data['category'][i]);audit_case=category not in tested
            if audit_case:
                cpu_raw=compute_raw_logits(hbits,bits)
                refroute,_=route_numpy(hbits,model['centers_bf16'],norms);np.testing.assert_array_equal(order,refroute)
                full=cuda(wg,h.reshape(1,-1)).cpu().numpy()[0]
                np.testing.assert_array_equal(full.view('u4'),cpu_raw.view('u4'))
            for pair in configs:
                key=pair['id'];p=pair['parameters'];o=outputs[key]
                ids=vocab if pair['mode']=='dense' else routes[p['R']] if pair['mode']=='cluster' else torch.unique(torch.cat([partial[p['d']][:p['T']],special]),sorted=True)
                idcpu=ids.cpu().numpy().astype('u4');hit=bool(np.any(idcpu==data['winner'][i]))
                if pair['mode']=='dense':token=int(data['winner'][i]);scorebits=int(dense_bits[i])
                else:
                    raw=cuda(wg[ids].contiguous(),h.reshape(1,-1))[0]
                    scores=torch.where(seen[ids],torch.where(raw<0,raw*penalty,raw/penalty),raw)
                    slot=int(torch.argmax(scores).item());token=int(idcpu[slot]);scorebits=int(scores[slot].view(torch.int32).item())&0xffffffff
                if hit:assert token==int(data['winner'][i]) and scorebits==int(dense_bits[i]),(key,i,'Covered winner must reproduce canonical output')
                if audit_case:
                    bitmap=np.zeros((S.V+31)//32,'u4')
                    for old in data['seen'][i]:bitmap[int(old)>>5]|=np.uint32(1<<(int(old)&31))
                    if pair['mode']=='partial':
                        idsref=engine.cpu_ids(pair,hbits,bitmap);np.testing.assert_array_equal(idcpu,idsref)
                    elif pair['mode']=='cluster':
                        idsref,_=pure_route_candidates(model,refroute[:p['R']],p['L']);np.testing.assert_array_equal(idcpu,idsref)
                    cpu_scores=R.policy(cpu_raw[None,:],[data['seen'][i]])[0][idcpu];j=int(cpu_scores.argmax())
                    assert token==int(idcpu[j]) and scorebits==int(cpu_scores[j].view('u4'))
                    if pair['mode']!='dense':np.testing.assert_array_equal(raw.cpu().numpy().view('u4'),cpu_raw[idcpu].view('u4'))
                    proof.append(dict(config=key,case=category,prediction=i,full_ids_and_raw_bits=True,token=token,score_bits=scorebits))
                o['hits'][i]=hit;o['k'][i]=len(idcpu);o['token'][i]=token;o['score_bits'][i]=scorebits;o['candidate_sha256'][i]=hashlib.sha256(idcpu.tobytes()).hexdigest()
            tested.add(category)
            if (i+1)%100==0:R.progress('EVALUATING_FROZEN_CONFIGURATIONS',predictions_done=i+1,total=n,configs=len(configs),seconds=time.perf_counter()-start)
        rows=[]
        for pair in configs:
            o=outputs[pair['id']];path=R.OUT/'coverage'/(pair['id']+'.npz');path.parent.mkdir(exist_ok=True)
            np.savez_compressed(path,**o,decode=data['decode'],category=data['category'],groups=data['groups'],dense_token=data['winner'],dense_score_bits=dense_bits)
            q=recall_report(o['hits'],data);match=o['token']==data['winner'];assert np.array_equal(o['hits'],match)
            mask=data['decode'];k=o['k'][mask];gate=q['decode']['recall']>=.99 and all(c['recall']>=.99 for c in q['decode']['by_category'].values())
            rows.append(dict(**pair,report=q,gate99='PASS' if gate else 'FAIL',candidate_decode=dict(mean=float(k.mean()),p95=int(np.quantile(k,.95,method='higher')),maximum=int(k.max())),coverage=path.relative_to(R.ROOT).as_posix(),coverage_sha256=R.sha(path)))
        assert len(proof)==24
        R.checked()
        R.write(R.OUT/'QUALITY.json',dict(state='COMPLETE_NEW1000_FROZEN6_NO_RETUNING',completed=R.now(),configurations=rows,prompts=1000,predictions=n,decode=int(data['decode'].sum()),excluded=0,collection_manifest_sha256=data['manifest_sha256'],selection_lock_sha256=R.sha(R.OUT/'SELECTION_LOCK.json'),proof=proof,scope='Fixed canonical dense trajectories; not closed-loop generation/task correctness/FPGA',threshold='overall and each category decode recall >=99%; numerical implementation remains bit exact'))
        R.progress('QUALITY_COMPLETE',predictions=n,configurations=len(rows))
    finally:active.close();(R.OUT/'ACTIVE.lock').unlink(missing_ok=True)
if __name__=='__main__':main()
