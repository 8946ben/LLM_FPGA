"""Locked <=12-point calibration neighborhood after the first OAT sweep.

Reuses qualified factors/arithmetic, changes only (r,T), no new final labels.
"""
from pathlib import Path
import argparse,json,math,statistics,struct,time,zlib
import numpy as np
import torch
import run_hyperparameter_studies_20261023 as b
from reference.hyperparameter_study import V,H,SPECIAL,exact_gpu,preview_gpu,preview_numpy
from reference.candidate_head import run_candidate_head
from reference.quality_data import load_split
M=b.M;FIRST=b.OUT;R=M/'reports/hyperparameters_joint_20261023_r1'
POINTS=[(128,98304),(128,131072),(256,32768),(256,65536),(256,98304),(512,32768),(512,65536),(896,1),(896,256),(896,1024),(896,4096),(896,8192)]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['evaluate','benchmark'],required=True);args=ap.parse_args()
    torch.set_num_threads(4);torch.set_grad_enabled(False);assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=4*2**30
    assert len(POINTS)==len(set(POINTS))==12
    review=json.loads((FIRST/'INDEPENDENT_REVIEW.json').read_text(encoding='utf-8'));assert review['state']=='PASS_FIRST_ROUND_CALIBRATION_AND_COUNTERBALANCED_GPU_REVIEW'
    original=json.loads((FIRST/'PLAN.json').read_text(encoding='utf-8'));assert all(b.sha(M/n)==h for n,h in original['source_sha256'].items())
    parameters={k:{**v,'path':str((FIRST/v['path']).resolve())} for k,v in json.loads((FIRST/'PARAMETERS.json').read_text(encoding='utf-8'))['files'].items() if k in ['r128','r256','r512','r896']}
    for x in parameters.values():assert b.sha(Path(x['path']))==x['sha256']
    R.mkdir(exist_ok=True);b.OUT=R;(R/'coverage').mkdir(exist_ok=True)
    configurations=[dict(id=f'r{r}_T{t}',parameters=dict(r=r,T=t),axes=['联合校准']) for r,t in POINTS]+[dict(id='r128_T16384',parameters=dict(r=128,T=16384),axes=['原基线控制'])]
    plan=dict(script_sha256=b.sha(__file__),first_result_sha256=b.sha(FIRST/'RESULT.json'),first_review_sha256=b.sha(FIRST/'INDEPENDENT_REVIEW.json'),original_plan_sha256=b.sha(FIRST/'PLAN.json'),parameters=parameters,configurations=configurations,
        selection='12 joint points frozen before computing their calibration outcomes;320 calibration prompts only. Four original ranks/factors unchanged. Control originalr128/T16384 and same-run dense.',
        rationale='r512/T16384 misses9 but faster than dense, raiseT; r256 raisesT; r128 near denseT; r896 lowerT to quantify full-rank floor. Cluster joint search not pursued: fixed train-vote support bound fails Chinese gate even at all clusters/all lists.',
        final_test='NOT_OPENED',fpga='NOT_RUN',warmup=3,measurements_per_case=30,cases=b.CASES,gpu_scope='Resident4 calibration fixtures, fixed arithmetic Eager complete pipeline; cyclic ordering; not optimized GPU/LLM/FPGA performance')
    if (R/'PLAN.json').exists():assert json.loads((R/'PLAN.json').read_text(encoding='utf-8'))==plan,'Do not overwrite a different joint study'
    else:b.write(R/'PLAN.json',plan)
    if args.phase=='evaluate':
        assert not (R/'LOWRANK_CALIBRATION.json').exists();cal=load_split(M/'data/hidden_v1/calibration');b.evaluate_lowrank(dict(lowrank=configurations),parameters,cal);b.progress('JOINT_CALIBRATION_COMPLETE',new_configurations=12,control_configurations=1);return
    assert not (R/'GPU_BENCHMARK.json').exists() and (R/'LOWRANK_CALIBRATION.json').is_file()
    # Full IDs/raw bits CPU proof for each new candidate set before timing.
    inputs=b.fixture_inputs();weights_bits=np.memmap(b.ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(V,H));weights=torch.from_numpy(np.array(weights_bits)).view(torch.bfloat16).to('cuda')
    models={k:b.load_model(Path(v['path'])) for k,v in parameters.items()};resident={k:dict(a=b.fp(v['a_bf16']),bt=b.fp(v['b_bf16'].T.copy())) for k,v in models.items()}
    payload={c:(b.fp(h),torch.from_numpy(np.isin(np.arange(V),b.seen_ids(history))).to('cuda')) for c,(h,history) in inputs.items()};penalty=torch.tensor(1.1,dtype=torch.float32,device='cuda');special=torch.tensor(SPECIAL.astype('i8'),device='cuda');vocab=torch.arange(V,device='cuda')
    pairs=configurations+[dict(id='dense',parameters={},axes=['同轮dense对照'])]
    b.write(R/'GPU_TIMING_PLAN.json',dict(plan_sha256=b.sha(R/'PLAN.json'),script_sha256=b.sha(__file__),configurations=14,new_research_configurations=12,controls=2,numeric_pairs=56,timed_calls=1680,warmups=3,rounds=30,ordering='cyclic config shift3/round; case shift round+config',scope=plan['gpu_scope'],excluded='Initial transfer/setup/CPU proofs/transformer/TTFT',stage_timings='NOT_MEASURED'))
    def call(config,cat,debug=False):
        h,seen=payload[cat];p=config['parameters']
        if config['id']=='dense':ids=vocab
        else:
            a=resident[f'r{p["r"]}'];z=exact_gpu(h,a['bt']);preview=preview_gpu(z[None,:],a['a'])[0];preview=torch.where(seen,torch.where(preview<0,preview*penalty,preview/penalty),preview);top=torch.argsort(preview,descending=True,stable=True)[:p['T']];ids=torch.unique(torch.cat([top,special]),sorted=True)
        raw=exact_gpu(h,(weights if config['id']=='dense' else weights[ids]).to(torch.float32));score=torch.where(seen[ids],torch.where(raw<0,raw*penalty,raw/penalty),raw);slot=torch.argmax(score);token=int(ids[slot].item());bits=int(score[slot].view(torch.int32).item())&0xffffffff
        actual=dict(token=token,score_bits=bits,crc=zlib.crc32(struct.pack('<II',token,bits)),k=ids.numel())
        if debug:actual.update(ids=ids.cpu().numpy().astype('u4'),raw=raw.cpu().numpy())
        return actual
    proof=[];gold={};observations={}
    for config in pairs:
        b.stop();p=config['parameters'];key=config['id'];gold[key]={};observations[key]=[]
        for cat,(hidden,history) in inputs.items():
            if key=='dense':ids=np.arange(V,dtype='u4')
            else:
                m=models[f'r{p["r"]}'];preview,_=preview_numpy(hidden,m['a_bf16'],m['b_bf16'],b.seen_ids(history));ids=np.union1d(np.argsort(-preview,kind='stable')[:p['T']],SPECIAL).astype('u4')
            ref=run_candidate_head(hidden,weights_bits,ids,history);actual=call(config,cat,True);np.testing.assert_array_equal(actual['ids'],ids);np.testing.assert_array_equal(actual['raw'].view('u4'),ref['raw_scores'].view('u4'));gold[key][cat]=dict(token=ref['selected_token'],score_bits=ref['selected_score_bits'],crc=ref['output_crc'])
            for k,v in gold[key][cat].items():assert actual[k]==v
            proof.append(dict(config=key,case=cat,k=len(ids),full_ids_raw_bits=True,**gold[key][cat]))
        b.write(R/'GPU_NUMERIC_PROOF.partial.json',proof);b.progress('JOINT_GPU_NUMERIC',completed=len(proof),total=56)
    b.write(R/'GPU_NUMERIC_PROOF.json',dict(state='PASS56_FULL_IDS_RAW_TOKEN_SCORE_CRC',records=proof))
    for warmup in range(3):
        b.stop()
        for config in pairs:
            for cat in b.CASES:call(config,cat)
    for round_id in range(30):
        b.stop()
        for pi in range(len(pairs)):
            config=pairs[(pi+3*round_id)%len(pairs)]
            for ci in range(4):
                cat=b.CASES[(ci+round_id+pi)%4];torch.cuda.synchronize();started=time.perf_counter_ns();actual=call(config,cat);torch.cuda.synchronize();elapsed=(time.perf_counter_ns()-started)/1e6
                for k,v in gold[config['id']][cat].items():assert actual[k]==v
                observations[config['id']].append(dict(case=cat,round=round_id,wall_ms=elapsed,k=actual['k']))
        b.write(R/'GPU_RAW_ROUNDS.partial.json',observations);b.progress('JOINT_GPU_TIMING',rounds_done=round_id+1,total_rounds=30,calls=sum(map(len,observations.values())),total_calls=1680)
    results=[]
    for config in pairs:
        obs=observations[config['id']];times=[x['wall_ms'] for x in obs];path=R/f'timing/{config["id"]}.json';b.write(path,obs);results.append(dict(**config,calls=len(obs),wall_median_ms=statistics.median(times),wall_p95_ms=sorted(times)[113],equivalent_m14_per_s=120000/sum(times),raw=path.relative_to(R).as_posix(),sha256=b.sha(path)))
    b.write(R/'GPU_BENCHMARK.json',dict(state='COMPLETE_JOINT_CALIBRATION_GPU_REFERENCE',measurements=1680,configurations=results,scope=plan['gpu_scope']))
    b.write(R/'RESULT.json',dict(state='COMPLETE12_JOINT_CALIBRATION_GPU_REFERENCE_NOT_FINAL',new_configurations=12,control_configurations=2,gpu_measurements=1680,independent_test='NOT_RUN',board='NOT_RUN',artifacts={n:b.sha(R/n) for n in ['PLAN.json','LOWRANK_CALIBRATION.json','GPU_TIMING_PLAN.json','GPU_NUMERIC_PROOF.json','GPU_BENCHMARK.json']}));b.progress('JOINT_COMPLETE_NOT_INDEPENDENT_OR_FPGA')
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if R.exists():b.OUT=R;b.progress('JOINT_STOPPED_NO_COMPLETION_VERDICT',error=repr(exc))
        raise
