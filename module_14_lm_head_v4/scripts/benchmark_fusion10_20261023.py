"""Balanced shortlist+matched controls and1000 changing-input GPU calls."""
from pathlib import Path
import json,math,statistics,struct,time,zlib
import numpy as np
import torch
import fusion_experiment10_20261023 as e
b=e.b;M=e.M;R=e.R
def main():
    torch.set_num_threads(4);torch.set_grad_enabled(False);assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=4*2**30
    assert not (R/'GPU_BENCHMARK.json').exists();pars=e.bind();short=e.read(R/'SHORTLIST.json');pairs=[dict(id=x['id'],mode='fusion',parameters=x['parameters']) for x in short['configurations']]
    pairs+=[dict(id='frozen_hybrid',mode='fusion',parameters=e.BASE),dict(id='cluster_only',mode='route',parameters=e.BASE),dict(id='lowrank_only',mode='lowrank',parameters=e.BASE),dict(id='dense',mode='dense',parameters={})]
    e.b.write(R/'GPU_TIMING_PLAN.json',dict(script_sha256=b.sha(__file__),shortlist_sha256=b.sha(R/'SHORTLIST.json'),plan_sha256=b.sha(R/'PLAN.json'),pairs=pairs,warmups=3,measurements_per_case=30,cases=b.CASES,scope='Same4 fixed calibration fixtures, GPU resident assets/hidden/history, complete fixed-arithmetic Eager M14 pipeline. Excludes setup/input transfer/transformer/TTFT. Not optimized GPU or FPGA predictor.',ordering='Round cyclic shift1 across configs and round+config case rotation; original observations retained',preview_block_rows=32768,stability_calls=1000))
    bits=np.memmap(b.ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(e.V,e.H));weights=torch.from_numpy(np.array(bits)).view(torch.bfloat16).to('cuda');inputs=b.fixture_inputs();payload={c:(b.fp(h),torch.from_numpy(np.isin(np.arange(e.V),b.seen_ids(history))).to('cuda')) for c,(h,history) in inputs.items()};special=torch.tensor(e.SPECIAL.astype('i8'),device='cuda');vocab=torch.arange(e.V,device='cuda');penalty=torch.tensor(1.1,dtype=torch.float32,device='cuda');two=torch.tensor(2.,device='cuda',dtype=torch.float32)
    cpu={};gpu={}
    keys={f'C{p["parameters"]["C"]}' for p in pairs if p['mode'] in ['fusion','route']}|{f'r{p["parameters"]["r"]}' for p in pairs if p['mode'] in ['fusion','lowrank']}
    for key in sorted(keys):
        m=e.model(pars,key);cpu[key]=m
        if key.startswith('C'):
            c=int(key[1:]);limit=max(p['parameters']['L'] for p in pairs if p['mode'] in ['fusion','route'] and p['parameters']['C']==c);gpu[key]=dict(centers=b.fp(m['centers_bf16']),norms=torch.from_numpy(np.load(e.SOURCE/f'parameters/norms_C{c}.npy')).to('cuda'),ranked=torch.from_numpy(m['ranked_ids'][:,:limit].astype('i8')).to('cuda'),counts=torch.from_numpy(m['counts'].astype('i8')).to('cuda'))
        else:gpu[key]=dict(a=b.fp(m['a_bf16']),bt=b.fp(m['b_bf16'].T.copy()))
    def call(pair,cat,debug=False):
        p=pair['parameters'];mode=pair['mode'];h,seen=payload[cat]
        if mode in ['fusion','route']:
            m=gpu[f'C{p["C"]}'];dist=(e.exact_gpu(h,h.reshape(1,e.H))[0]+m['norms'])-two*e.exact_gpu(h,m['centers']);rr=torch.argsort(dist,stable=True)[:p['R']];chosen=m['ranked'][rr,:p['L']];valid=torch.arange(p['L'],device='cuda')[None,:]<m['counts'][rr,None];routed=torch.unique(torch.cat([chosen[valid],special]),sorted=True)
            if bool((m['counts'][rr]==0).any().item()):routed=vocab
        if mode in ['fusion','lowrank']:
            m=gpu[f'r{p["r"]}'];z=e.exact_gpu(h,m['bt']);preview=e.preview_gpu(z[None,:],m['a'])[0];preview=torch.where(seen,torch.where(preview<0,preview*penalty,preview/penalty),preview);top=torch.argsort(preview,descending=True,stable=True)[:p['T']];low=torch.unique(torch.cat([top,special]),sorted=True)
        ids=vocab if mode=='dense' else routed if mode=='route' else low if mode=='lowrank' else torch.unique(torch.cat([routed,low]),sorted=True)
        raw=e.exact_gpu(h,(weights if mode=='dense' else weights[ids]).to(torch.float32));scores=torch.where(seen[ids],torch.where(raw<0,raw*penalty,raw/penalty),raw);slot=torch.argmax(scores);token=int(ids[slot].item());score=int(scores[slot].view(torch.int32).item())&0xffffffff;out=dict(k=ids.numel(),token=token,score_bits=score,crc=zlib.crc32(struct.pack('<II',token,score)))
        if debug:out.update(ids=ids.cpu().numpy().astype('u4'),raw=raw.cpu().numpy())
        return out
    gold={};proof=[];observations={p['id']:[] for p in pairs}
    for pair in pairs:
        b.stop();p=pair['parameters'];mode=pair['mode'];gold[pair['id']]={}
        for cat,(hidden,history) in inputs.items():
            if mode in ['fusion','route']:
                m=cpu[f'C{p["C"]}'];rr,_=e.route_numpy(hidden,m['centers_bf16'],np.load(e.SOURCE/f'parameters/norms_C{p["C"]}.npy'));routed,fallback=e.pure_route_candidates(m,rr[:p['R']],p['L']);routed=np.arange(e.V,dtype='u4') if fallback else routed
            if mode in ['fusion','lowrank']:
                m=cpu[f'r{p["r"]}'];preview,_=e.preview_numpy(hidden,m['a_bf16'],m['b_bf16'],b.seen_ids(history));low=np.union1d(np.argsort(-preview,kind='stable')[:p['T']],e.SPECIAL).astype('u4')
            ids=np.arange(e.V,dtype='u4') if mode=='dense' else routed if mode=='route' else low if mode=='lowrank' else np.union1d(routed,low).astype('u4');ref=e.run_candidate_head(hidden,bits,ids,history);actual=call(pair,cat,True);np.testing.assert_array_equal(actual['ids'],ids);np.testing.assert_array_equal(actual['raw'].view('u4'),ref['raw_scores'].view('u4'));expected=dict(token=ref['selected_token'],score_bits=ref['selected_score_bits'],crc=ref['output_crc'])
            for k,v in expected.items():assert actual[k]==v
            gold[pair['id']][cat]=expected;proof.append(dict(id=pair['id'],case=cat,k=len(ids),full_ids_raw_bits=True,**expected))
        b.write(R/'GPU_NUMERIC_PROOF.partial.json',proof);b.progress('EXP10_GPU_NUMERIC',completed=len(proof),total=len(pairs)*4)
    b.write(R/'GPU_NUMERIC_PROOF.json',dict(state='PASS_FULL_CANDIDATE_IDS_RAW_TOKEN_SCORE_CRC',records=proof))
    for _ in range(3):
        b.stop()
        for pair in pairs:
            for cat in b.CASES:call(pair,cat)
    for round_id in range(30):
        b.stop()
        for pi in range(len(pairs)):
            pair=pairs[(pi+round_id)%len(pairs)]
            for ci in range(4):
                cat=b.CASES[(ci+round_id+pi)%4];torch.cuda.synchronize();start=time.perf_counter_ns();actual=call(pair,cat);torch.cuda.synchronize();elapsed=(time.perf_counter_ns()-start)/1e6
                for k,v in gold[pair['id']][cat].items():assert actual[k]==v
                observations[pair['id']].append(dict(case=cat,round=round_id,k=actual['k'],wall_ms=elapsed))
        b.write(R/'GPU_RAW_ROUNDS.partial.json',observations);b.progress('EXP10_GPU_TIMING',rounds=round_id+1,total=30,calls=sum(map(len,observations.values())))
    results=[]
    for pair in pairs:
        obs=observations[pair['id']];times=[x['wall_ms'] for x in obs];raw=R/f'timing/{pair["id"]}.json';b.write(raw,obs);results.append(dict(**pair,calls=len(times),wall_median_ms=statistics.median(times),wall_p95_ms=sorted(times)[113],equivalent_m14_per_s=120000/sum(times),raw=raw.relative_to(R).as_posix(),sha256=b.sha(raw)))
    selected=short['configurations'][0];pair=next(p for p in pairs if p['id']==selected['id']);stability=[]
    for i in range(1000):
        if i%32==0:b.stop()
        cat=b.CASES[i%4];actual=call(pair,cat)
        for k,v in gold[pair['id']][cat].items():assert actual[k]==v
        stability.append(dict(index=i,case=cat,**actual))
        if (i+1)%200==0:b.progress('EXP10_GPU_STABILITY',completed=i+1,total=1000)
    b.write(R/'GPU_STABILITY.json',dict(state='PASS1000_CHANGING_INPUT_CALLS',selected=selected['id'],observations=stability,scope='GPU functional repetition, not FPGA stability'))
    b.write(R/'GPU_BENCHMARK.json',dict(state='PASS_SHORTLIST_GPU_REFERENCE',configurations=results,measurements=len(pairs)*120,plan_sha256=b.sha(R/'GPU_TIMING_PLAN.json'),proof_sha256=b.sha(R/'GPU_NUMERIC_PROOF.json'),scope=e.read(R/'GPU_TIMING_PLAN.json')['scope']))
    b.write(R/'SELECTION_LOCK.json',dict(state='LOCKED_BEFORE_NEW_FINAL_LABELS',chosen=selected['id'],parameters=selected['parameters'],objective=e.read(R/'PLAN.json')['final_selection'],calibration_sha256=b.sha(R/'CALIBRATION.json'),shortlist_sha256=b.sha(R/'SHORTLIST.json'),gpu_sha256=b.sha(R/'GPU_BENCHMARK.json'),source_sha256=b.sha(__file__),factor_manifest_sha256=b.sha(e.SOURCE/'PARAMETERS.json'),selected_metrics=selected))
    b.progress('EXP10_SELECTION_LOCKED',chosen=selected['id'],parameters=selected['parameters'])
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if R.exists():b.progress('EXP10_BENCHMARK_STOPPED',error=repr(exc))
        raise
