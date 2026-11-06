"""P2 second experiment: union complementary routing and low-rank candidates.

Reuses immutable train-fitted parameters from the first experiment. No holdout
access during the calibration grid. Union size is conservatively upper-bounded
until online top-K and merge are implemented; no latency claim is made.
"""
from pathlib import Path
import argparse,importlib.util,json,sys,time
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
spec=importlib.util.spec_from_file_location('_p2_base',M/'scripts/evaluate_selectors.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from reference.quality_data import load_split,assert_group_disjoint,assert_compatible_collections,recall_report

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=M/'data/hidden_v1')
    ap.add_argument('--base',type=Path,default=M/'reports/selector_p2_20261021')
    ap.add_argument('--out',type=Path,default=M/'reports/selector_hybrid_p2_20261021');ap.add_argument('--holdout-only',action='store_true')
    args=ap.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
    train=load_split(args.data/'train');cal=load_split(args.data/'calibration')
    assert_group_disjoint(train,cal);assert_compatible_collections(train,cal)
    old=read(args.base/'EXPERIMENT.lock.json');params=read(args.base/'PARAMETERS.json');required=base.mandatory_ids()
    assert old['train_manifest_sha256']==train['manifest_sha256'] and old['calibration_manifest_sha256']==cal['manifest_sha256']
    assert old['evaluator_sha256']==base.sha(M/'scripts/evaluate_selectors.py') and old['router_sha256']==base.sha(M/'reference/routing.py') and old['quality_data_sha256']==base.sha(M/'reference/quality_data.py')
    identity=dict(train_manifest_sha256=train['manifest_sha256'],calibration_manifest_sha256=cal['manifest_sha256'],
        evaluator_sha256=base.sha(Path(__file__)),base_experiment_lock_sha256=base.sha(args.base/'EXPERIMENT.lock.json'),
        base_parameter_manifest_sha256=base.sha(args.base/'PARAMETERS.json'),mandatory_global_ids=required.tolist())
    lock=out/'EXPERIMENT.lock.json'
    if lock.exists():assert read(lock)==identity
    else:base.write(lock,identity)
    models={}
    def load(name):
        if name not in models:
            p=args.base/name;assert base.sha(p)==params[name]
            with np.load(p,allow_pickle=False) as z:models[name]={k:z[k].copy() for k in z.files}
        return models[name]
    if args.holdout_only:
        if (out/'HOLDOUT.json').exists():raise ValueError('Do not repeatedly evaluate/tune locked holdout')
        summary=read(out/'CALIBRATION.json');chosen_name=summary['chosen_calibration_configuration']
        if chosen_name is None:print('HOLDOUT_NOT_OPENED_NO_FEASIBLE_HYBRID');return
        chosen=next(r for r in summary['configurations'] if r['name']==chosen_name);c=chosen['config']
        selection=dict(chosen=chosen_name,calibration_sha256=base.sha(out/'CALIBRATION.json'),base_parameter_manifest_sha256=identity['base_parameter_manifest_sha256'])
        sl=out/'SELECTION_LOCK.json'
        if sl.exists():assert read(sl)==selection
        else:base.write(sl,selection)
        test=load_split(args.data/'holdout');assert_group_disjoint(train,cal,test);assert_compatible_collections(train,cal,test)
        router=load('route_r128.npz');hits,counts,fallback=base.route_eval(router,test,c['route_count'],c['route_k'],required)
        selector_bytes=2*128*896
        if chosen['family']=='hybrid':
            low=load(f"lowrank_r{c['rank']}.npz")
            ranks=base.lowrank_eval(low['a_bf16'],low['b_bf16'],test,required)
            hits=hits|(ranks<c['lowrank_k']);counts=np.minimum(151936,counts+c['lowrank_k'])
            selector_bytes+=2*c['rank']*(896+151936)
        q=recall_report(hits,test);scale=q['prompt_groups']>=1000 and q['decode']['steps']>=10000
        state=('P2_RECALL_PASS' if scale else 'INSUFFICIENT_SCALE') if base.preliminary_gate(q) else 'QUALITY_FAIL'
        base.write(out/'HOLDOUT.json',dict(state=state,chosen=chosen_name,report=q,
            candidates=base.describe_counts(counts[test['decode']],selector_bytes),fallback_steps=fallback,
            minimum_scale_met=scale,holdout_manifest_sha256=test['manifest_sha256'],selection_lock_sha256=base.sha(sl),
            candidate_count_note='Conservative route count + preview K upper bound for union; overlap not materialized',
            quality_scope='Conditional dense-trajectory recall; not free-generation task quality or FPGA acceptance'))
        print('P2_HYBRID_HOLDOUT='+state,flush=True);return
    if (out/'CALIBRATION.json').exists():raise ValueError('Preserve finished experiment; use --holdout-only')
    route_model=load('route_r128.npz');ranks_by_rank={};results=[]
    for rank in (64,128):
        low=load(f'lowrank_r{rank}.npz');ranks_by_rank[rank]=base.lowrank_eval(low['a_bf16'],low['b_bf16'],cal,required)
    def add(name,family,config,hits,counts,selector_bytes):
        q=recall_report(hits,cal);stats=base.describe_counts(counts[cal['decode']],selector_bytes)
        row=dict(name=name,family=family,config=config,calibration=q,candidates=stats,
            preliminary_quality_gate=base.preliminary_gate(q),candidate_count_scope='decode only; union upper bound for hybrids',
            parameters='immutable files in ../'+args.base.name,base_parameter_hashes=params,
            timing_scope='Quality/membership only; no online top-K/merge timing, no FPGA latency')
        results.append(row);base.write(out/'calibration_partial.json',results)
        print(f"HYBRID_CALIBRATION {name} recall={q['decode']['recall']:.6f} maxK_bound={stats['max']}",flush=True)
    for routes in (2,3,4):
        for k in (8192,16384):
            route_hits,route_counts,fallback=base.route_eval(route_model,cal,routes,k,required)
            c=dict(clusters=128,route_count=routes,route_k=k,fallback_steps=fallback)
            add(f'route_R128_routes{routes}_K{k}','route',c,route_hits,route_counts,2*128*896)
            for rank in (64,128):
                for lk in (4096,8192,16384):
                    hits=route_hits|(ranks_by_rank[rank]<lk)
                    counts=np.minimum(151936,route_counts+lk)
                    add(f'route{routes}_K{k}_UNION_lr{rank}_K{lk}','hybrid',dict(c,rank=rank,lowrank_k=lk),
                        hits,counts,2*128*896+2*rank*(896+151936))
    eligible=[r for r in results if r['preliminary_quality_gate'] and r['candidates']['mean_logical_bytes']<272269312 and r['candidates']['p95']<151936]
    chosen=min(eligible,key=lambda r:r['candidates']['mean_logical_bytes']) if eligible else None
    summary=dict(state='COMPLETE',quality_state='PRELIMINARY_CALIBRATION_PASS' if chosen else 'NO_FEASIBLE_CONFIGURATION',
        expected_configuration_count=42,train_manifest_sha256=train['manifest_sha256'],calibration_manifest_sha256=cal['manifest_sha256'],
        configurations=results,chosen_calibration_configuration=chosen['name'] if chosen else None,
        selection_rule='Proposed overall and each-category decode recall >=99.9%, conservative mean logical bytes < dense, P95 candidate count < V; then lowest conservative mean bytes.',
        quality_limits='Hybrid candidate membership exact, count conservative upper bound; no online top-K/merge or FPGA timing; no free-generation quality',
        fpga_performance='NOT_RUN',holdout='NOT_OPENED')
    base.write(out/'CALIBRATION.json',summary)
    print('P2_HYBRID_SWEEP='+summary['quality_state'],flush=True)
if __name__=='__main__':main()
