"""Offline resident-GPU PyTorch eager reference benchmark, NOT FPGA/LLM speed.

Preserves fixed FP32 arithmetic; no FMA/GEMM/Tensor-Core substitution. Does not
reopen quality selection, train, invoke EDA, use networking or touch the board.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,math,statistics,struct,sys,time,zlib
import numpy as np
import torch
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.selector_arithmetic import lowrank_preview,router_ids
from reference.routing import routed_candidates
from reference.candidate_head import run_candidate_head
from reference.numeric_contract import bf16_bits_to_float32

OUT=M/'reports/gpu_method_benchmark_20261022_r2'
MODES=['dense','route','lowrank','hybrid'];CASES=['chinese','english','code','math']
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def progress(d):
    temp=OUT/'PROGRESS.tmp';temp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(OUT/'PROGRESS.json')
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def tree(x):
    while x.shape[-1]>1:x=x[...,0::2]+x[...,1::2]
    return x[...,0]
def exact(h,rows):
    w=rows.reshape(-1,7,16,8);hidden=h.reshape(7,16,8)
    partial=torch.zeros((len(w),16,8),dtype=torch.float32,device='cuda')
    for group in range(7):partial=partial+w[:,group]*hidden[group]
    for width in (8,4,2,1):partial=partial[:,:width]+partial[:,width:2*width]
    return tree(partial[:,0])
def policy(scores,seen,p):return torch.where(seen,torch.where(scores<0,scores*p,scores/p),scores)

def main():
    OUT.mkdir(exist_ok=False);started=time.perf_counter()
    torch.set_num_threads(4);torch.set_grad_enabled(False)
    assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=3*2**30,'Need3GiB free GPU; do not compete'
    layout=json.loads((M/'reports/selector_integration_fixture_20261021/MANIFEST.json').read_text())
    sources={n:M.parent/v['path'] for n,v in layout['binding'].items()}
    for n,p in sources.items():assert sha(p)==layout['binding'][n]['sha256'],n
    frozen=json.loads((M/'data/fixed_quality_20261022/IMPLEMENTATION_FREEZE.json').read_text())
    for n,h in frozen['source_sha256'].items():assert sha(M/n)==h,n
    inputs={c:{kind:M/f'reports/lowrank_fixture_20261021/{c}.{kind}.bin' for kind in ['hidden','history']} for c in CASES}
    plan=dict(created=now(),modes=MODES,cases=CASES,source_cohort='Four previously frozen calibration C-chain fixtures, not the fresh1000 quality set',
      samples='1 fixed input per category,4 total; selected before timing; not representative population latency',
      warmups_per_case_mode=3,measurements_per_case_mode=30,batch=1,thread_limit=4,
      operation_order='Fixed FP32 H8/interleave16/separate multiply-add; adjacent lowrankA trees; stable GPU sort; lower ID tie',
      implementation='PyTorch eager resident GPU reference, NOT optimized GEMM/Tensor-Core production GPU inference',
      timed_scope='Wall clock from GPU resident hidden/history through candidate construction, weight gather+BF16-to-FP32, exact head, policy, host token/score+CRC return; synchronize before each call',
      excluded='Model transformer/prefill, setup/weight transfer/hidden-history transfer, CPU reference validation; no full LLM TTFT',
      cuda_events='Secondary same-stream interval, may include CPU dispatch gaps; not a hardware compute-only counter',
      allocation='Resident BF16 canonical W; resident FP32 factors/centers; dynamic eager temporaries allocated via torch cache',
      ordering='All pairs warmed; cyclic mode and case order changes each round to limit order bias; raw observations retained',
      wall_budget_seconds=600,fpga='NOT_RUN',quality_parameters_changed=False,
      source_sha256={n:sha(p) for n,p in sources.items()},script_sha256=sha(__file__),
      inputs={c:{k:dict(path=p.relative_to(M).as_posix(),sha256=sha(p)) for k,p in ps.items()} for c,ps in inputs.items()})
    save(OUT/'PLAN.json',plan)
    (OUT/'benchmark_source.py').write_bytes(Path(__file__).read_bytes())
    wb=np.memmap(sources['weight'],dtype='<u2',mode='r',shape=(151936,896))
    a_bits=np.fromfile(sources['a'],dtype='<u2').reshape(151936,128);bt_bits=np.fromfile(sources['bt'],dtype='<u2').reshape(128,896)
    center_bits=np.fromfile(sources['centers'],dtype='<u2').reshape(128,896);norm_np=np.fromfile(sources['norms'],dtype='<f4')
    router=dict(vocab_size=151936,ranked_ids=np.fromfile(sources['ranked'],dtype='<u4').reshape(128,16384),counts=np.fromfile(sources['counts'],dtype='<u4'))
    def fp32(bits):return torch.from_numpy(bf16_bits_to_float32(bits)).to('cuda')
    weights=torch.from_numpy(np.array(wb)).view(torch.bfloat16).to('cuda')
    a=fp32(a_bits);bt=fp32(bt_bits);centers=fp32(center_bits);norms=torch.from_numpy(norm_np).to('cuda')
    ranked=torch.from_numpy(router['ranked_ids'].astype('int64')).to('cuda');counts=torch.from_numpy(router['counts'].astype('int64')).to('cuda')
    positions=torch.arange(16384,device='cuda');vocab=torch.arange(151936,device='cuda');mandatory=torch.arange(151643,151657,device='cuda')
    penalty=torch.tensor(1.1,dtype=torch.float32,device='cuda')
    payload={};goldens={};proof=[]
    for c in CASES:
        h=np.fromfile(inputs[c]['hidden'],dtype='<u2');history=np.fromfile(inputs[c]['history'],dtype='<u4')
        ids=np.arange(151936,dtype='u4');seen=((history[ids>>5]>>(ids&31))&1)!=0
        routes,_=router_ids(h,center_bits,norm_np);preview,_=lowrank_preview(h,a_bits,bt_bits.T.copy(),ids[seen])
        route,fallback=routed_candidates(router,routes,16384,range(151643,151657));assert not fallback
        lowrank=np.union1d(np.argsort(-preview,kind='stable')[:16384],np.arange(151643,151657)).astype('u4')
        sets=dict(dense=ids,route=route,lowrank=lowrank,hybrid=np.union1d(route,lowrank).astype('u4'))
        payload[c]=(fp32(h),torch.from_numpy(seen).to('cuda'))
        goldens[c]={}
        for mode,subset in sets.items():
            ref=run_candidate_head(h,wb,subset,history)
            goldens[c][mode]=dict(ids=subset,raw=ref['raw_scores'],token=ref['selected_token'],score_bits=ref['selected_score_bits'],crc=ref['output_crc'])
        print('CPU_GOLDENS_READY '+c,flush=True)
    def call(c,mode,debug=False):
        h,seen=payload[c]
        if mode in ['route','hybrid']:
            dist=(exact(h,h.reshape(1,896))[0]+norms)-2*exact(h,centers)
            rr=torch.argsort(dist,stable=True)[:4]
            chosen=ranked[rr];valid=positions[None,:]<counts[rr,None]
            routed=torch.unique(torch.cat([chosen[valid],mandatory]),sorted=True)
            # Fixtures have no empty cluster; don't omit explicit policy check.
            if bool((counts[rr]==0).any().item()):routed=vocab
        if mode in ['lowrank','hybrid']:
            z=exact(h,bt);preview=policy(tree(tree((a*z).reshape(151936,16,8))),seen,penalty)
            top=torch.argsort(preview,descending=True,stable=True)[:16384]
            lowrank=torch.unique(torch.cat([top,mandatory]),sorted=True)
        ids=vocab if mode=='dense' else routed if mode=='route' else lowrank if mode=='lowrank' else torch.unique(torch.cat([routed,lowrank]),sorted=True)
        selected_weights=weights if mode=='dense' else weights[ids]
        raw=exact(h,selected_weights.to(torch.float32));scores=policy(raw,seen[ids],penalty);slot=torch.argmax(scores)
        token=int(ids[slot].item());bits=int(scores[slot].view(torch.int32).item())&0xffffffff
        crc=zlib.crc32(struct.pack('<II',token,bits));out=dict(k=ids.numel(),token=token,score_bits=bits,crc=crc)
        if debug:out.update(ids=ids.cpu().numpy().astype('u4'),raw=raw.cpu().numpy(),preview=preview.cpu().numpy() if mode=='hybrid' else None)
        return out
    for c in CASES:
        for mode in MODES:
            actual=call(c,mode,True);gold=goldens[c][mode]
            np.testing.assert_array_equal(actual['ids'],gold['ids']);np.testing.assert_array_equal(actual['raw'].view('u4'),gold['raw'].view('u4'))
            for key in ['token','score_bits','crc']:assert actual[key]==gold[key],(c,mode,key)
            if mode=='hybrid':
                # Existing fixed GPU arithmetic proof binds this serialized output.
                # Old fixture scores used BLAS; compare fixed reference directly instead.
                h=np.fromfile(inputs[c]['hidden'],dtype='<u2');history=np.fromfile(inputs[c]['history'],dtype='<u4');vv=np.arange(151936,dtype='u4')
                fixed,_=lowrank_preview(h,a_bits,bt_bits.T.copy(),vv[((history[vv>>5]>>(vv&31))&1)!=0])
                np.testing.assert_array_equal(actual['preview'].view('u4'),fixed.view('u4'))
            proof.append(dict(case=c,mode=mode,k=actual['k'],token=actual['token'],score_bits=f"0x{actual['score_bits']:08x}",crc32=f"{actual['crc']:08x}",all_ids_raw_bits_match=True))
        print('GPU_BIT_PROOF_PASS '+c,flush=True)
    save(OUT/'NUMERIC_PROOF.json',dict(state='PASS16_FULL_CANDIDATE_ID_RAW_BITS_AND_FINAL_RESULT',records=proof))
    for _ in range(3):
        for c in CASES:
            for mode in MODES:call(c,mode)
    observations=[];aevent=torch.cuda.Event(enable_timing=True);bevent=torch.cuda.Event(enable_timing=True)
    for round in range(30):
        if (OUT/'STOP_REQUESTED').exists():raise RuntimeError('Stopped before next complete round')
        assert time.perf_counter()-started<600,'Wall budget exhausted; no partial PASS'
        for ci in range(4):
            c=CASES[(ci+round)%4]
            for mi in range(4):
                mode=MODES[(mi+round+ci)%4]
                torch.cuda.synchronize();t=time.perf_counter_ns();aevent.record();actual=call(c,mode);bevent.record();bevent.synchronize();elapsed=(time.perf_counter_ns()-t)/1e6
                gold=goldens[c][mode]
                for key in ['token','score_bits','crc']:assert actual[key]==gold[key]
                observations.append(dict(case=c,mode=mode,round=round,k=actual['k'],wall_ms=elapsed,cuda_event_ms=aevent.elapsed_time(bevent)))
        progress(dict(state='MEASURING',rounds_done=round+1,rounds=30,calls=len(observations),elapsed_seconds=time.perf_counter()-started))
        if round%5==0:print(f'GPU_TIMING_ROUNDS {round+1}/30',flush=True)
    save(OUT/'RAW_OBSERVATIONS.json',observations)
    summary={}
    for mode in MODES:
        values=[v for v in observations if v['mode']==mode];wall=[v['wall_ms'] for v in values]
        summary[mode]=dict(calls=len(values),wall_median_ms=statistics.median(wall),wall_p95_ms=sorted(wall)[math.ceil(.95*len(wall))-1],
          aggregate_equivalent_m14_per_s=len(values)*1000/sum(wall),cuda_event_median_ms=statistics.median(v['cuda_event_ms'] for v in values),
          cases={c:dict(k=next(v['k'] for v in values if v['case']==c),median_ms=statistics.median(v['wall_ms'] for v in values if v['case']==c)) for c in CASES})
    props=torch.cuda.get_device_properties(0)
    result=dict(state='PASS_GPU_REFERENCE_BENCHMARK_NOT_FPGA_OR_LLM',updated=now(),summary=summary,
      plan_sha256=sha(OUT/'PLAN.json'),raw_sha256=sha(OUT/'RAW_OBSERVATIONS.json'),numeric_proof_sha256=sha(OUT/'NUMERIC_PROOF.json'),
      torch=torch.__version__,cuda=torch.version.cuda,device=props.name,total_gpu_memory_bytes=props.total_memory,
      elapsed_seconds=time.perf_counter()-started,fpga='NOT_RUN',quality_set='UNCHANGED_NOT_REEVALUATED',
      interpretation='Resident batch1 eager fixed-arithmetic reference across4 calibration fixtures/30 rounds. Not optimized GPU production inference, quality population latency, full LLM decode or FPGA prediction.')
    save(OUT/'RESULT.json',result);progress(dict(state='COMPLETE',result='RESULT.json',elapsed_seconds=result['elapsed_seconds']))
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        if OUT.exists():progress(dict(state='FAILED_NO_BENCHMARK_PASS',error=repr(exc)))
        raise
