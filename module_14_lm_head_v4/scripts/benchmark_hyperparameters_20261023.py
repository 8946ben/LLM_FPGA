"""Counterbalanced, GPU-resident complete-reference benchmark for study8/9.

Dedicated measurement entry frozen before timings. No fitting, holdout or board.
"""
from pathlib import Path
import json,math,statistics,struct,time,zlib
import numpy as np
import torch
import run_hyperparameter_studies_20261023 as base
from reference.hyperparameter_study import V,H,SPECIAL,exact_gpu,preview_gpu,preview_numpy,route_numpy,pure_route_candidates
from reference.candidate_head import run_candidate_head
M,OUT=base.M,base.OUT
def main():
    torch.set_num_threads(4);torch.set_grad_enabled(False)
    assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=4*2**30
    assert not (OUT/'GPU_BENCHMARK.json').exists(),'Preserve completed timing run'
    plan=json.loads((OUT/'PLAN.json').read_text(encoding='utf-8'));pars=json.loads((OUT/'PARAMETERS.json').read_text(encoding='utf-8'))['files']
    assert all(base.sha(M/n)==h for n,h in plan['source_sha256'].items()),'Original experiment input drift'
    for family in ['CLUSTER','LOWRANK']:assert (OUT/f'{family}_CALIBRATION.json').is_file()
    inputs=base.fixture_inputs();pairs=[(f,c) for f in ['cluster','lowrank'] for c in plan['configurations'][f]]+[('dense',dict(id='dense',parameters={},axes=['完整词表对照']))]
    timing_plan=dict(script_sha256=base.sha(__file__),calibration_plan_sha256=base.sha(OUT/'PLAN.json'),parameters_sha256=base.sha(OUT/'PARAMETERS.json'),arithmetic_proof_sha256=base.sha(OUT/'NUMERIC_PROOF.json'),warmups=3,rounds=30,cases=base.CASES,research_configurations=44,dense_control_configurations=1,
        timing_scope='Resident BF16 W, resident FP32 selector parameters, GPU hidden/history mask. Per call complete routing/preview, stable sort, union, gather, exact, policy and host token/score/CRC return. No cached previews or candidates.',
        excluded='Setup, H2D initial transfers, CPU goldens, transformer/prefill/TTFT; internal Eager allocations included',
        ordering='All configurations warmed; cyclic config order shifts by7 per round and case order shifts by round+config. Counterbalances early/late and case position; not proof against thermal effects.',
        history='Resident GPU boolean mask; preview penalty uses explicit FP32 GPU scalar tensor, no per-call CPU history reconstruction/upload',
        fpga='NOT_RUN',stage_timings='NOT_MEASURED',quality='Only calibration; no new final labels',scope='PyTorch Eager fixed arithmetic reference; not optimized GPU inference, whole LLM decode or FPGA prediction')
    base.write(OUT/'GPU_TIMING_PLAN.json',timing_plan)
    resident={};weight_bits=np.memmap(base.ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(V,H));weights=torch.from_numpy(np.array(weight_bits)).view(torch.bfloat16).to('cuda')
    payload={c:(base.fp(h),torch.from_numpy(np.isin(np.arange(V),base.seen_ids(history))).to('cuda')) for c,(h,history) in inputs.items()}
    mandatory=torch.tensor(SPECIAL.astype('i8'),device='cuda');vocab=torch.arange(V,device='cuda');penalty=torch.tensor(1.1,device='cuda',dtype=torch.float32);two=torch.tensor(2.,device='cuda',dtype=torch.float32)
    for key,item in pars.items():
        base.stop();assert base.sha(OUT/item['path'])==item['sha256'];model=base.load_model(OUT/item['path'])
        if key.startswith('C'):
            c=int(key[1:]);limit=max(x['parameters']['L'] for f,x in pairs if f=='cluster' and x['parameters']['C']==c)
            resident[key]=dict(centers=base.fp(model['centers_bf16']),norms=torch.from_numpy(np.load(OUT/f'parameters/norms_C{c}.npy')).to('cuda'),ranked=torch.from_numpy(model['ranked_ids'][:,:limit].astype('i8')).to('cuda'),counts=torch.from_numpy(model['counts'].astype('i8')).to('cuda'))
        else:resident[key]=dict(a=base.fp(model['a_bf16']),bt=base.fp(model['b_bf16'].T.copy()))
        del model
    def call(family,config,cat,debug=False):
        p=config['parameters'];h,seen=payload[cat]
        if family=='cluster':
            m=resident[f'C{p["C"]}'];d=(exact_gpu(h,h.reshape(1,H))[0]+m['norms'])-two*exact_gpu(h,m['centers']);rr=torch.argsort(d,stable=True)[:p['R']]
            chosen=m['ranked'][rr,:p['L']];pos=torch.arange(p['L'],device='cuda');valid=pos[None,:]<m['counts'][rr,None]
            ids=torch.unique(torch.cat([chosen[valid],mandatory]),sorted=True)
            if bool((m['counts'][rr]==0).any().item()):ids=vocab
        elif family=='lowrank':
            m=resident[f'r{p["r"]}'];z=exact_gpu(h,m['bt']);preview=preview_gpu(z[None,:],m['a'])[0]
            preview=torch.where(seen,torch.where(preview<0,preview*penalty,preview/penalty),preview)
            top=torch.argsort(preview,descending=True,stable=True)[:p['T']];ids=torch.unique(torch.cat([top,mandatory]),sorted=True)
        else:ids=vocab
        raw=exact_gpu(h,(weights if family=='dense' else weights[ids]).to(torch.float32));scores=torch.where(seen[ids],torch.where(raw<0,raw*penalty,raw/penalty),raw);slot=torch.argmax(scores)
        token=int(ids[slot].item());bits=int(scores[slot].view(torch.int32).item())&0xffffffff;out=dict(k=ids.numel(),token=token,score_bits=bits,crc=zlib.crc32(struct.pack('<II',token,bits)))
        if debug:out.update(ids=ids.cpu().numpy().astype('u4'),raw=raw.cpu().numpy())
        return out
    proof=[];gold={};observations={}
    for family,config in pairs:
        base.stop();p=config['parameters'];key=f'C{p["C"]}' if family=='cluster' else f'r{p["r"]}' if family=='lowrank' else None;model=base.load_model(OUT/pars[key]['path']) if key else None;label=(family,config['id']);gold[label]={};observations[label]=[]
        for cat,(hidden,history) in inputs.items():
            if family=='cluster':
                rr,_=route_numpy(hidden,model['centers_bf16'],np.load(OUT/f'parameters/norms_C{p["C"]}.npy'));ids,fallback=pure_route_candidates(model,rr[:p['R']],p['L']);ids=np.arange(V,dtype='u4') if fallback else ids
            elif family=='lowrank':
                preview,_=preview_numpy(hidden,model['a_bf16'],model['b_bf16'],base.seen_ids(history));ids=np.union1d(np.argsort(-preview,kind='stable')[:p['T']],SPECIAL).astype('u4')
            else:ids=np.arange(V,dtype='u4')
            ref=run_candidate_head(hidden,weight_bits,ids,history);actual=call(family,config,cat,True);np.testing.assert_array_equal(actual['ids'],ids);np.testing.assert_array_equal(actual['raw'].view('u4'),ref['raw_scores'].view('u4'))
            expected=dict(token=ref['selected_token'],score_bits=ref['selected_score_bits'],crc=ref['output_crc'])
            for k,v in expected.items():assert actual[k]==v,(family,config['id'],cat,k)
            gold[label][cat]=expected;proof.append(dict(family=family,config=config['id'],case=cat,full_ids_and_raw_bits=True,k=len(ids),**expected))
        base.write(OUT/'GPU_NUMERIC_PROOF.partial.json',proof);base.progress('GPU_FULL_PIPELINE_NUMERIC',family=family,config=config['id'],completed=len(proof),total=180)
        del model
    assert len(proof)==180;base.write(OUT/'GPU_NUMERIC_PROOF.json',dict(state='PASS180_FULL_IDS_RAW_BITS_TOKEN_SCORE_CRC',records=proof))
    for warmup in range(3):
        base.stop()
        for family,config in pairs:
            for cat in base.CASES:call(family,config,cat)
        base.progress('GPU_WARMUP',round=warmup+1,total=3)
    for round_id in range(30):
        base.stop()
        for pi in range(len(pairs)):
            family,config=pairs[(pi+7*round_id)%len(pairs)];label=(family,config['id'])
            for ci in range(4):
                cat=base.CASES[(ci+pi+round_id)%4];torch.cuda.synchronize();t=time.perf_counter_ns();actual=call(family,config,cat);torch.cuda.synchronize();elapsed=(time.perf_counter_ns()-t)/1e6
                for k,v in gold[label][cat].items():assert actual[k]==v
                observations[label].append(dict(case=cat,round=round_id,wall_ms=elapsed,k=actual['k']))
        base.write(OUT/'GPU_RAW_ROUNDS.partial.json',[dict(family=f,config=i,observations=rows) for (f,i),rows in observations.items()]);base.progress('GPU_TIMING',rounds_done=round_id+1,total_rounds=30,calls=sum(map(len,observations.values())),total_calls=5400)
    results=[]
    for family,config in pairs:
        rows=observations[(family,config['id'])];wall=[x['wall_ms'] for x in rows];raw=OUT/f'timing/{family}_{config["id"]}.json';base.write(raw,rows)
        result=dict(family=family,**config,calls=len(wall),wall_median_ms=statistics.median(wall),wall_p95_ms=sorted(wall)[math.ceil(.95*len(wall))-1],equivalent_m14_per_s=len(wall)*1000/sum(wall),cases={cat:dict(k=next(x['k'] for x in rows if x['case']==cat),median_ms=statistics.median(x['wall_ms'] for x in rows if x['case']==cat)) for cat in base.CASES},raw=raw.relative_to(OUT).as_posix(),sha256=base.sha(raw));results.append(result)
    base.write(OUT/'GPU_BENCHMARK.json',dict(state='COMPLETE_GPU_EAGER_REFERENCE_NOT_FPGA_OR_LLM',configurations=results,measurements=5400,plan_sha256=base.sha(OUT/'GPU_TIMING_PLAN.json'),proof_sha256=base.sha(OUT/'GPU_NUMERIC_PROOF.json'),torch=torch.__version__,device=torch.cuda.get_device_name(0),scope=timing_plan['scope'],limits=timing_plan))
    base.write(OUT/'RESULT.json',dict(state='COMPLETE_FIRST_ROUND_CALIBRATION_AND_GPU_REFERENCE',updated=base.now(),cluster_configurations=23,lowrank_configurations=21,calibration_prompts=320,decode_steps=4775,gpu_measurements=5400,dense_control_calls=120,independent_quality='NOT_RUN_NEW_FINAL_GROUP_REQUIRED_AFTER_SELECTION',joint_search='NOT_STARTED',fpga='NOT_RUN',ttft='NOT_MEASURED',plan_sha256=base.sha(OUT/'PLAN.json'),artifacts={n:base.sha(OUT/n) for n in ['PARAMETERS.json','NUMERIC_PROOF.json','CLUSTER_CALIBRATION.json','LOWRANK_CALIBRATION.json','GPU_TIMING_PLAN.json','GPU_NUMERIC_PROOF.json','GPU_BENCHMARK.json']}))
    base.progress('COMPLETE_FIRST_ROUND_NOT_INDEPENDENT_OR_FPGA')
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if OUT.exists():base.progress('STOPPED_GPU_TIMING_NO_COMPLETION_VERDICT',error=repr(exc))
        raise
