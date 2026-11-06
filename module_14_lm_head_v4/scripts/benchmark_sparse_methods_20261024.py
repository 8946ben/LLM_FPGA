"""Finite, same-run GPU census for experiments 1/8/9/10. No board or EDA.

Historical calibration arrays are read-only. All timed calls recompute selectors
and exact candidate logits. A dense CPU raw cache is ONLY an untimed oracle:
row-independent canonical arithmetic permits indexing it for every candidate set.
"""
from pathlib import Path
import argparse, json, math, os, platform, statistics, struct, time, zlib
import numpy as np
import torch
import run_hyperparameter_studies_20261023 as b
import benchmark_summary_20261024 as legacy
import sys
sys.path.insert(0,str(b.M/'experiments/sparse_methods_20261024'))
import sparse_methods as research
from reference.hyperparameter_study import V, H, SPECIAL, exact_gpu, preview_gpu, preview_numpy, route_numpy, pure_route_candidates
from reference.numeric_contract import compute_raw_logits
from reference.candidate_head import select_candidate

M=b.M; ROOT=b.ROOT; FIRST=M/'reports/hyperparameters_20261023_r1'
JOINT=M/'reports/hyperparameters_joint_20261023_r1'; FUSION=M/'reports/fusion_exp10_20261023_r1'
OUT=research.R/'benchmark'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):b.write(p,d)
def progress(stage,**kw):
    d=dict(stage=stage,updated=b.now(),pid=os.getpid(),board='NOT_RUN',new_final_labels_opened=False,**kw)
    write(OUT/'PROGRESS.json',d); print(json.dumps(d,ensure_ascii=False),flush=True)
def stop():
    if (OUT/'STOP_REQUESTED').exists():raise InterruptedError('Stop requested at call/config boundary')

def configurations():
    old=legacy.configurations()
    fresh=read(research.R/'CALIBRATION.json')['configurations']
    assert len(fresh)==68
    rows=old[:-1]+[dict(id=r['id'],config=r['id'],mode=r['mode'],parameters=r['parameters'],experiments=r['experiments'],quality=r['quality'],candidate_decode=r['candidate_decode'],calibration_source=(research.R/'CALIBRATION.json').relative_to(ROOT).as_posix()) for r in fresh]+old[-1:]
    rows[-1]['experiments'] += [11,12,13,14]
    assert len(rows)==len({r['id'] for r in rows})==557
    return rows

def run():
    torch.set_num_threads(4);torch.set_grad_enabled(False)
    assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=4*2**30
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'PLAN.json').exists(),'Preserve previous run; never silently overwrite or restart'
    pairs=configurations();pars=read(FIRST/'PARAMETERS.json')['files'];inputs=b.fixture_inputs()
    paths=[Path(__file__),M/'reference/hyperparameter_study.py',M/'reference/numeric_contract.py',M/'reference/candidate_head.py',FIRST/'PLAN.json',FIRST/'PARAMETERS.json',FIRST/'CLUSTER_CALIBRATION.json',FIRST/'LOWRANK_CALIBRATION.json',JOINT/'LOWRANK_CALIBRATION.json',FUSION/'CALIBRATION.json']
    paths += [M/f'reports/lowrank_fixture_20261021/{cat}.{kind}.bin' for cat in b.CASES for kind in ['hidden','history']]
    for key,item in pars.items():
        p=FIRST/item['path'];assert b.sha(p)==item['sha256'],key;paths.append(p)
        if key.startswith('C'):
            p=FIRST/f'parameters/norms_{key}.npy';assert b.sha(p)==item['norms_sha256'];paths.append(p)
    weight_path=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
    assert b.sha(weight_path)=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f';paths.append(weight_path)
    paths += [Path(research.__file__),Path(legacy.__file__),research.R/'PLAN.json',research.R/'PARAMETERS.json',research.R/'CALIBRATION.json',M/'scripts/resume_sparse_lsh_calibration_20261024.py',research.R/'resume_lsh_r2/ENTRY_LOCK.json']
    for item in read(research.R/'PARAMETERS.json')['files'].values():
        assert b.sha(research.R/item['path'])==item['sha256'];paths.append(research.R/item['path'])
    plan=dict(created=b.now(),purpose='User-requested full census, not new selection or final-quality certification',configurations=pairs,total=557,warmups_per_case=3,measured_per_case=30,cases=b.CASES,measured_calls=66840,ordering='Seed20261024 per-round permutation of all557 configs; rotate four cases by round+position',sentinel='Additional dense calls every25 configs each round, rotating case; not included in configuration means',quality='All557 x-axis values use original320 calibration groups/4775 decode; no final label recollection or retuning',speed='Full recomputed GPU M14 Eager reference, CUDA synchronized perf_counter_ns wall time through host token/score/CRC return; 120 balanced measurements per config; rate=120000/sum(wall_ms)',included='Routing/lowrank preview as enabled, stable sort, special IDs, sorted union, gather BF16 W, canonical FP32 exact reduction, penalty/tie, host output; no candidate or preview cache inside timed call',excluded='Initial H2D/load, CPU oracle and proofs, transformer/prefill/input upload/history-mask construction/TTFT',cpu_oracle='Untimed full canonical raw per four fixtures; index row-independent raw for each candidate oracle. GPU still gathers/executes exact selected rows each call.',preview_block_rows=32768,device=torch.cuda.get_device_name(0),torch=torch.__version__,cuda=torch.version.cuda,python=platform.python_version(),source_sha256={p.relative_to(ROOT).as_posix():b.sha(p) for p in paths},board='NOT_RUN',eda='NOT_RUN')
    plan['new_method_notes']='LSH query prototype projects all8 stored tables even for tables4 configurations; active-table count only limits bucket probes. Cost report must use8*b*H and not claimL*b*H measured. Dynamic partial keeps a full column-major W duplicate; static-only deployment may keep2*V*d subset.'
    write(OUT/'PLAN.json',plan);write(OUT/'ACTIVE.lock',dict(pid=os.getpid(),started=b.now(),entry=str(Path(__file__).resolve())))
    try:
        bits=np.memmap(weight_path,dtype='<u2',mode='r',shape=(V,H));weights=torch.from_numpy(np.array(bits)).view(torch.bfloat16).to('cuda')
        engine=research.Engine(bits,weights)
        payload={c:(b.fp(h),torch.from_numpy(np.isin(np.arange(V),b.seen_ids(history))).to('cuda')) for c,(h,history) in inputs.items()}
        special=torch.tensor(SPECIAL.astype('i8'),device='cuda');vocab=torch.arange(V,device='cuda');penalty=torch.tensor(1.1,device='cuda',dtype=torch.float32);two=torch.tensor(2.,device='cuda',dtype=torch.float32)
        resident={};route_ids={};low_ids={};primitive_proof=[]
        # CPU/GPU full primitive arrays; only oracle preparation caches results.
        for key,item in pars.items():
            stop();model=b.load_model(FIRST/item['path'])
            if key.startswith('C'):
                c=int(key[1:]);used=[p['parameters'] for p in pairs if p['mode'] in ['cluster','hybrid'] and p['parameters']['C']==c]
                limit=max(p['L'] for p in used);norms=np.load(FIRST/f'parameters/norms_{key}.npy')
                resident[key]=dict(centers=b.fp(model['centers_bf16']),norms=torch.from_numpy(norms).to('cuda'),ranked=torch.from_numpy(model['ranked_ids'][:,:limit].astype('i8')).to('cuda'),counts=torch.from_numpy(model['counts'].astype('i8')).to('cuda'))
                for cat,(h,history) in inputs.items():
                    order,d=route_numpy(h,model['centers_bf16'],norms);hg=payload[cat][0];g=resident[key]
                    gd=(exact_gpu(hg,hg.reshape(1,H))[0]+g['norms'])-two*exact_gpu(hg,g['centers'])
                    np.testing.assert_array_equal(gd.cpu().numpy().view('u4'),d.view('u4'));np.testing.assert_array_equal(torch.argsort(gd,stable=True).cpu().numpy(),order)
                    for r,l in sorted(set((p['R'],p['L']) for p in used)):
                        ids,fallback=pure_route_candidates(model,order[:r],l);route_ids[c,r,l,cat]=np.arange(V,dtype='u4') if fallback else ids
                    primitive_proof.append(dict(parameter=key,case=cat,full_distance_order_bits=True))
            else:
                r=int(key[1:]);resident[key]=dict(a=b.fp(model['a_bf16']),bt=b.fp(model['b_bf16'].T.copy()))
                ts=sorted(set(p['parameters']['T'] for p in pairs if p['mode'] in ['lowrank','hybrid'] and p['parameters']['r']==r))
                for cat,(h,history) in inputs.items():
                    preview,z=preview_numpy(h,model['a_bf16'],model['b_bf16'],b.seen_ids(history));hg,seen=payload[cat];g=resident[key]
                    zg=exact_gpu(hg,g['bt']);pg=preview_gpu(zg[None,:],g['a'])[0];pg=torch.where(seen,torch.where(pg<0,pg*penalty,pg/penalty),pg)
                    np.testing.assert_array_equal(zg.cpu().numpy().view('u4'),z.view('u4'));np.testing.assert_array_equal(pg.cpu().numpy().view('u4'),preview.view('u4'))
                    order=np.argsort(-preview,kind='stable')
                    for t in ts:low_ids[r,t,cat]=np.union1d(order[:t],SPECIAL).astype('u4')
                    primitive_proof.append(dict(parameter=key,case=cat,full_preview_projection_bits=True))
            del model;progress('PRIMITIVE_PROOF',parameter=key,completed=len(primitive_proof))
        write(OUT/'PRIMITIVE_PROOF.json',dict(state='PASS_FULL_CPU_GPU_ARRAYS',records=primitive_proof))
        extra_proof=engine.prove_primitives(inputs,payload)
        write(OUT/'NEW_PRIMITIVE_PROOF.json',dict(state='PASS_FULL_NEW_SELECTOR_ARRAY_BITS',records=extra_proof))
        raw_cpu={}
        for cat,(h,history) in inputs.items():
            stop();raw_cpu[cat]=compute_raw_logits(h,bits);progress('CPU_DENSE_ORACLE',case=cat)

        def call(pair,cat,debug=False):
            p=pair['parameters'];mode=pair['mode'];h,seen=payload[cat]
            if mode in ['cluster','hybrid']:
                g=resident[f'C{p["C"]}'];dist=(exact_gpu(h,h.reshape(1,H))[0]+g['norms'])-two*exact_gpu(h,g['centers']);rr=torch.argsort(dist,stable=True)[:p['R']]
                chosen=g['ranked'][rr,:p['L']];valid=torch.arange(p['L'],device='cuda')[None,:]<g['counts'][rr,None]
                routed=torch.unique(torch.cat([chosen[valid],special]),sorted=True)
                if bool((g['counts'][rr]==0).any().item()):routed=vocab
            if mode in ['lowrank','hybrid']:
                g=resident[f'r{p["r"]}'];z=exact_gpu(h,g['bt']);preview=preview_gpu(z[None,:],g['a'])[0];preview=torch.where(seen,torch.where(preview<0,preview*penalty,preview/penalty),preview)
                top=torch.argsort(preview,descending=True,stable=True)[:p['T']];low=torch.unique(torch.cat([top,special]),sorted=True)
            ids=engine.gpu_ids(pair,h,seen) if mode in research.MODES else vocab if mode=='dense' else routed if mode=='cluster' else low if mode=='lowrank' else torch.unique(torch.cat([routed,low]),sorted=True)
            raw=exact_gpu(h,(weights if mode=='dense' else weights[ids]).to(torch.float32));scores=torch.where(seen[ids],torch.where(raw<0,raw*penalty,raw/penalty),raw);slot=torch.argmax(scores)
            token=int(ids[slot].item());score=int(scores[slot].view(torch.int32).item())&0xffffffff
            out=dict(k=ids.numel(),token=token,score_bits=score,crc=zlib.crc32(struct.pack('<II',token,score)))
            if debug:out.update(ids=ids.cpu().numpy().astype('u4'),raw=raw.cpu().numpy())
            return out

        gold={};proof=[]
        for index,pair in enumerate(pairs):
            stop();p=pair['parameters'];mode=pair['mode'];gold[pair['id']]={}
            for cat,(h,history) in inputs.items():
                if mode in ['cluster','hybrid']:routed=route_ids[p['C'],p['R'],p['L'],cat]
                if mode in ['lowrank','hybrid']:low=low_ids[p['r'],p['T'],cat]
                ids=engine.cpu_ids(pair,h,history) if mode in research.MODES else np.arange(V,dtype='u4') if mode=='dense' else routed if mode=='cluster' else low if mode=='lowrank' else np.union1d(routed,low).astype('u4')
                raw=raw_cpu[cat][ids];_,token,score=select_candidate(raw,ids,V,history,penalty=1.1);sb=int(score.view(np.uint32));expected=dict(k=len(ids),token=token,score_bits=sb,crc=zlib.crc32(struct.pack('<II',token,sb)))
                actual=call(pair,cat,True);np.testing.assert_array_equal(actual['ids'],ids);np.testing.assert_array_equal(actual['raw'].view('u4'),raw.view('u4'))
                for k,v in expected.items():assert actual[k]==v,(pair['id'],cat,k)
                gold[pair['id']][cat]=expected;proof.append(dict(id=pair['id'],case=cat,full_ids_raw_bits=True,ids_sha256=__import__('hashlib').sha256(ids.tobytes()).hexdigest(),raw_sha256=__import__('hashlib').sha256(raw.tobytes()).hexdigest(),**expected))
            if (index+1)%20==0 or index==len(pairs)-1:
                write(OUT/'GPU_NUMERIC_PROOF.partial.json',proof);progress('CONFIG_NUMERIC_PROOF',completed=index+1,total=len(pairs))
        write(OUT/'GPU_NUMERIC_PROOF.json',dict(state='PASS2228_FULL_IDS_RAW_BITS_TOKEN_SCORE_CRC',records=proof))
        del route_ids,low_ids,raw_cpu
        for w in range(3):
            for pair in pairs:
                stop()
                for cat in b.CASES:call(pair,cat)
            progress('WARMUP',completed=w+1,total=3)
        rng=np.random.default_rng(20261024);observations={p['id']:[] for p in pairs};sentinels=[];dense=pairs[-1]
        for rid in range(30):
            order=rng.permutation(len(pairs))
            for position,idx in enumerate(order):
                stop();pair=pairs[int(idx)]
                for ci in range(4):
                    cat=b.CASES[(ci+rid+position)%4];torch.cuda.synchronize();start=time.perf_counter_ns();actual=call(pair,cat);torch.cuda.synchronize();ms=(time.perf_counter_ns()-start)/1e6
                    for k,v in gold[pair['id']][cat].items():assert actual[k]==v
                    observations[pair['id']].append(dict(case=cat,round=rid,position=position,wall_ms=ms,**actual))
                if (position+1)%25==0:
                    cat=b.CASES[(rid+position//25)%4];torch.cuda.synchronize();start=time.perf_counter_ns();actual=call(dense,cat);torch.cuda.synchronize();ms=(time.perf_counter_ns()-start)/1e6
                    assert actual==gold['dense'][cat];sentinels.append(dict(case=cat,round=rid,position=position,wall_ms=ms))
            write(OUT/'GPU_RAW_ROUNDS.partial.json',observations);write(OUT/'DENSE_SENTINELS.json',sentinels);progress('TIMING',rounds_done=rid+1,total_rounds=30,calls=sum(map(len,observations.values())),total_calls=66840)
        result=[]
        for pair in pairs:
            obs=observations[pair['id']];ms=[x['wall_ms'] for x in obs];path=OUT/f'timing/{pair["id"]}.json';write(path,obs)
            result.append(dict(**pair,calls=len(obs),wall_mean_ms=statistics.mean(ms),wall_median_ms=statistics.median(ms),wall_p95_ms=sorted(ms)[math.ceil(.95*len(ms))-1],equivalent_m14_per_s=120000/sum(ms),cases={c:dict(calls=30,k=gold[pair['id']][c]['k'],mean_ms=statistics.mean(x['wall_ms'] for x in obs if x['case']==c)) for c in b.CASES},raw=path.relative_to(OUT).as_posix(),sha256=b.sha(path)))
        assert all(b.sha(ROOT/p)==h for p,h in plan['source_sha256'].items()),'Inputs changed during census'
        write(OUT/'RESULT.json',dict(state='COMPLETE_ALL557_SAME_RUN_GPU_CALIBRATION_SUMMARY',completed=b.now(),configurations=result,measurements=66840,additional_dense_sentinels=len(sentinels),plan_sha256=b.sha(OUT/'PLAN.json'),numeric_proof_sha256=b.sha(OUT/'GPU_NUMERIC_PROOF.json'),board='NOT_RUN',independent_quality='NO_NEW_LABELS_REUSED_HISTORICAL_CALIBRATION',selection='NO_NEW_LOCK_OR_RELEASE'))
        progress('COMPLETE',configurations=557,measurements=66840)
    finally:
        (OUT/'ACTIVE.lock').unlink(missing_ok=True)

if __name__=='__main__':
    try:run()
    except BaseException as exc:
        if OUT.exists():progress('STOPPED_NO_COMPLETION_VERDICT',error=repr(exc))
        raise
