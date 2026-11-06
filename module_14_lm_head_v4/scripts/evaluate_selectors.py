"""Train-only fit, calibration sweep, optional locked holdout evaluation.

P2 CPU experiments. No FPGA or automatic end-to-end speedup claim.
Low-rank recall is computed from a known target's exact rank in the defined
preview scores; this is a quality evaluator, not an online top-K timing test.
"""
from pathlib import Path
import argparse,hashlib,json,sys,time
import numpy as np
M=Path(__file__).resolve().parents[1];ROOT=M.parent;sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32,float32_to_bf16_bits
from reference.routing import train_router,nearest_centers,routed_candidates
from reference.quality_data import load_split,assert_group_disjoint,assert_compatible_collections,recall_report,penalty_aware_target_ranks
KS=(2048,4096,8192,16384)
V,H=151936,896
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
def mandatory_ids():
    t=json.loads((M/'data/model/tokenizer_config.json').read_text(encoding='utf-8'))
    ids={int(k) for k,v in t['added_tokens_decoder'].items() if v.get('special')}
    g=json.loads((M/'data/model/generation_config.json').read_text())
    eos=g['eos_token_id'];ids.update(eos if isinstance(eos,list) else [eos]);return np.array(sorted(ids),dtype='u4')
def route_eval(model,data,route_count,k,mandatory):
    x=bf16_bits_to_float32(data['hidden']);centers=bf16_bits_to_float32(model['centers_bf16'])
    routes=nearest_centers(x,centers,route_count);memo={};hits=[];counts=[];fallbacks=[]
    for chosen,winner in zip(routes,data['winner']):
        key=tuple(map(int,chosen))
        if key not in memo:memo[key]=routed_candidates(model,chosen,k,mandatory)
        ids,fallback=memo[key];at=np.searchsorted(ids,winner)
        hits.append(at<len(ids) and ids[at]==winner);counts.append(len(ids));fallbacks.append(fallback)
    return np.array(hits),np.array(counts),int(sum(fallbacks))
def lowrank_eval(a_bits,b_bits,data,mandatory):
    a=bf16_bits_to_float32(a_bits);b=bf16_bits_to_float32(b_bits);x=bf16_bits_to_float32(data['hidden'])
    ranks=[]
    for start in range(0,len(x),32):
        stop=min(start+32,len(x));z=np.matmul(x[start:stop],b);preview=np.matmul(z,a.T)
        ranks.extend(penalty_aware_target_ranks(preview,data['winner'][start:stop],data['seen'][start:stop],mandatory))
    return np.array(ranks)
def describe_counts(counts,selector_bytes):
    if len(counts)==0:raise ValueError('No decode candidates to summarize')
    p95_index=(95*len(counts)+99)//100-1
    return dict(mean=float(np.mean(counts)),p95=int(np.sort(counts)[p95_index]),max=int(np.max(counts)),percentile_method='nearest rank ceil(0.95*N)',
        mean_logical_bytes=float(np.mean(counts*(1792+4)+selector_bytes)),
        scope='Logical selector+candidate-ID+weight bytes only; hidden/history/control, metadata, padding/burst overhead not included; not measured AXI bandwidth')
def preliminary_gate(report):
    d=report['decode']
    return d['steps']>0 and d['recall']>=.999 and all(c['steps'] and c['recall']>=.999 for c in d['by_category'].values())
def holdout_phase(args,out,train,cal,summary,required,parameter_hashes):
    if not summary['chosen_calibration_configuration']:
        print('HOLDOUT_NOT_OPENED_NO_FEASIBLE_CALIBRATION',flush=True);return
    if (out/'HOLDOUT.json').exists():raise ValueError('Preserve completed holdout result; do not repeatedly tune against it')
    chosen=next(r for r in summary['configurations'] if r['name']==summary['chosen_calibration_configuration'])
    selection=dict(chosen=chosen['name'],calibration_sha256=sha(out/'CALIBRATION.json'),parameters_sha256=sha(out/'PARAMETERS.json'),rule=summary['selection_rule'])
    path=out/'SELECTION_LOCK.json'
    if path.exists():assert json.loads(path.read_text())==selection
    else:write(path,selection)
    test=load_split(args.data/'holdout');assert_group_disjoint(train,cal,test)
    assert_compatible_collections(train,cal,test)
    c=chosen['config'];parameter_path=out/chosen['parameters']
    assert sha(parameter_path)==parameter_hashes[chosen['parameters']]==chosen['parameters_sha256']
    with np.load(parameter_path,allow_pickle=False) as z:model={k:z[k].copy() for k in z.files}
    if chosen['family']=='route':hits,counts,fallback=route_eval(model,test,c['route_count'],c['k_per_route'],required)
    else:
        ranks=lowrank_eval(model['a_bf16'],model['b_bf16'],test,required)
        hits=ranks<c['k'];counts=np.full(len(hits),c['k']+len(required));fallback=0
    report=recall_report(hits,test);enough=report['prompt_groups']>=1000 and report['decode']['steps']>=10000
    state=('P2_RECALL_PASS' if enough else 'INSUFFICIENT_SCALE') if preliminary_gate(report) else 'QUALITY_FAIL'
    selector_bytes=2*c['clusters']*H if chosen['family']=='route' else 2*c['rank']*(H+V)
    write(out/'HOLDOUT.json',dict(state=state,chosen=chosen['name'],report=report,
        candidates=describe_counts(counts[test['decode']],selector_bytes),candidate_count_scope='decode steps only',
        all_prediction_candidates=describe_counts(counts,selector_bytes),fallback_steps=fallback,holdout_manifest_sha256=test['manifest_sha256'],
        minimum_scale_met=enough,selection_lock_sha256=sha(out/'SELECTION_LOCK.json'),
        quality_scope='Proposed screening threshold, not release acceptance; no free-generation task quality or FPGA measurement'))
    print('P2_LOCKED_HOLDOUT='+state,flush=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=M/'data/hidden_v1');ap.add_argument('--out',type=Path,default=M/'reports/selector_p2_20261021')
    ap.add_argument('--holdout',action='store_true',help='Only evaluate the preselected calibration configuration if it passes proposed gate')
    ap.add_argument('--holdout-only',action='store_true',help='Reuse locked calibration/parameters; no refit or repeated calibration sweep')
    args=ap.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
    train=load_split(args.data/'train');cal=load_split(args.data/'calibration');assert_group_disjoint(train,cal)
    assert_compatible_collections(train,cal)
    required=mandatory_ids();results=[];models={}
    identity=dict(train_manifest_sha256=train['manifest_sha256'],calibration_manifest_sha256=cal['manifest_sha256'],
        evaluator_sha256=sha(Path(__file__)),router_sha256=sha(M/'reference/routing.py'),
        quality_data_sha256=sha(M/'reference/quality_data.py'),mandatory_global_ids=required.tolist())
    identity_file=out/'EXPERIMENT.lock.json'
    if identity_file.exists():assert json.loads(identity_file.read_text())==identity,'Preserve outputs from a different experiment'
    else:write(identity_file,identity)
    parameter_file=out/'PARAMETERS.json'
    parameter_hashes=json.loads(parameter_file.read_text()) if parameter_file.exists() else {}
    def existing(path):
        if not path.exists():return False
        assert parameter_hashes.get(path.name)==sha(path),'Unbound or changed parameter artifact: '+path.name
        return True
    def register(path):
        parameter_hashes[path.name]=sha(path);write(parameter_file,parameter_hashes)
    if args.holdout_only:
        holdout_phase(args,out,train,cal,json.loads((out/'CALIBRATION.json').read_text()),required,parameter_hashes)
        return
    if (out/'CALIBRATION.json').exists():raise ValueError('Calibration sweep already completed; use --holdout-only or a new experiment directory')
    def add(name,family,config,hits,counts,selector_bytes,seconds,path):
        q=recall_report(hits,cal)
        row=dict(name=name,family=family,config=config,calibration=q,preliminary_quality_gate=preliminary_gate(q),
            candidates=describe_counts(counts[cal['decode']],selector_bytes),candidate_count_scope='decode steps only',
            all_prediction_candidates=describe_counts(counts,selector_bytes),cpu_fit_and_quality_seconds=seconds,
            parameters=path.name,parameters_sha256=sha(path),
            timing_scope='CPU experiment incl. fit/quality work; not online selector latency or FPGA speedup')
        results.append(row);write(out/'calibration_partial.json',results)
        print(f"SELECTOR_CALIBRATION {name} decode_recall={q['decode']['recall']:.6f} maxK={row['candidates']['max']}",flush=True)
    for r in (128,256,512):
        path=out/f'route_r{r}.npz';started=time.perf_counter()
        if existing(path):
            with np.load(path,allow_pickle=False) as z:model={k:z[k].copy() for k in z.files}
        else:
            model=train_router(train['hidden'],train['raw_top_ids'],train['winner'],V,r);np.savez_compressed(path,**model);register(path)
        models['route',r]=model
        fit=time.perf_counter()-started
        for route_count in (1,2):
            for k in KS:
                started=time.perf_counter();hits,counts,fallback=route_eval(model,cal,route_count,k,required)
                config=dict(clusters=r,route_count=route_count,k_per_route=k,mandatory_global_ids=required.tolist(),fallback_steps=fallback,
                    fit_manifest_sha256=train['manifest_sha256'],seed=20261021,iterations=12,route_metric='L2 / BF16 centers',candidate_votes='raw top256 rank reciprocal plus 4*dense winner count')
                add(f'route_R{r}_routes{route_count}_K{k}','route',config,hits,counts,2*r*H,fit+time.perf_counter()-started,path)
    weight_file=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin';assert sha(weight_file)=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    # Weight-only truncated SVD via W.T @ W; train/cal/holdout labels not used.
    basis_path=out/'svd_basis128.npy';started=time.perf_counter()
    weights=bf16_bits_to_float32(np.memmap(weight_file,dtype='<u2',mode='r',shape=(V,H)))
    if existing(basis_path):basis=np.load(basis_path,allow_pickle=False)
    else:
        gram=np.matmul(weights.T,weights);_,vectors=np.linalg.eigh(gram)
        basis=vectors[:,::-1][:,:128].copy()
        for column in range(128):
            pivot=np.argmax(np.abs(basis[:,column]));basis[:,column]*=1 if basis[pivot,column]>=0 else -1
        np.save(basis_path,basis);register(basis_path)
    svd_seconds=time.perf_counter()-started
    for rank in (32,64,128):
        path=out/f'lowrank_r{rank}.npz';started=time.perf_counter()
        if existing(path):
            with np.load(path,allow_pickle=False) as z:a_bits,b_bits=z['a_bf16'],z['b_bf16']
        else:
            a_bits=float32_to_bf16_bits(np.matmul(weights,basis[:,:rank]));b_bits=float32_to_bf16_bits(basis[:,:rank]);np.savez_compressed(path,a_bf16=a_bits,b_bf16=b_bits);register(path)
        models['lowrank',rank]=(a_bits,b_bits)
        ranks=lowrank_eval(a_bits,b_bits,cal,required)
        elapsed=svd_seconds+time.perf_counter()-started
        for k in KS:
            hits=ranks<k;counts=np.full(len(hits),k+len(required),dtype='u4')
            # TopK UNION specials actual overlap is not materialized by rank evaluator.
            # Charge the conservative upper-bound K+specials explicitly, never exact-K.
            add(f'lowrank_r{rank}_K{k}','lowrank',dict(rank=rank,k=k,mandatory_global_ids=required.tolist(),
                candidate_count_note='K+specials upper bound; overlap not materialized',preview='BF16 parameters; CPU FP32 BLAS with penalty applied by global ID; not PL arithmetic qualified'),
                hits,counts,2*rank*(H+V),elapsed,path)
    feasible=[r for r in results if r['preliminary_quality_gate'] and r['candidates']['mean_logical_bytes']<272269312]
    chosen=min(feasible,key=lambda r:r['candidates']['mean_logical_bytes']) if feasible else None
    summary=dict(state='COMPLETE',quality_state='PRELIMINARY_CALIBRATION_PASS' if chosen else 'NO_FEASIBLE_CONFIGURATION',
        calibration_manifest_sha256=cal['manifest_sha256'],train_manifest_sha256=train['manifest_sha256'],configurations=results,
        selection_rule='Proposed >=99.9% decode winner recall overall AND each category on calibration, and lower mean logical bytes than dense; then minimum conservative logical bytes. Decode-only K statistics. No latency-optimality claim.',
        chosen_calibration_configuration=chosen['name'] if chosen else None,
        quality_limits='Dense-trajectory conditional recall only; free generation, rare-name/long-context suites and publication thresholds remain unvalidated',
        fpga_performance='NOT_RUN',holdout='NOT_OPENED')
    write(out/'CALIBRATION.json',summary) # selection frozen before touching holdout labels
    if args.holdout:holdout_phase(args,out,train,cal,summary,required,parameter_hashes)
    print('P2_SELECTOR_SWEEP='+summary['quality_state'],flush=True)
if __name__=='__main__':main()
