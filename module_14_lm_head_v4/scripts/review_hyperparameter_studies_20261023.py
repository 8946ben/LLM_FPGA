"""Read-only numerical/result audit using saved arrays, no CUDA or fitting."""
from pathlib import Path
import argparse,hashlib,json,math,statistics,sys
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split,assert_group_disjoint
R=M/'reports/hyperparameters_20261023_r1';V=151936
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def gate(row):
    q=row['quality']['decode'];return q['recall']>=.999 and all(c['recall']>=.999 for c in q['by_category'].values())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--calibration-only',action='store_true');args=ap.parse_args()
    train=load_split(M/'data/hidden_v1/train');cal=load_split(M/'data/hidden_v1/calibration');assert_group_disjoint(train,cal);mask=cal['decode'];n=len(mask)
    plan=read(R/'PLAN.json');assert int(mask.sum())==4775 and len(set(cal['groups']))==320
    for name,h in plan['source_sha256'].items():assert sha(M/name)==h
    clusters=read(R/'CLUSTER_CALIBRATION.json')['configurations'];lowrank=read(R/'LOWRANK_CALIBRATION.json')['configurations'];assert len(clusters)==23 and len(lowrank)==21
    records={};checks=0
    for family,rows in [('cluster',clusters),('lowrank',lowrank)]:
        for row in rows:
            p=R/row['arrays'];assert sha(p)==row['sha256']
            with np.load(p,allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
            assert a['hits'].shape==a['k'].shape==(n,) and np.all((14<=a['k'])&(a['k']<=V))
            for phase,selected in [('all',np.ones(n,bool)),('decode',mask),('prefill',~mask)]:
                q=row['quality'][phase];assert q['steps']==int(selected.sum()) and q['misses']==int((~a['hits'][selected]).sum()) and q['recall']==float(a['hits'][selected].mean())
                for category in sorted(set(cal['category'])):
                    use=selected&(cal['category']==category);actual=q['by_category'][str(category)]
                    assert actual['steps']==int(use.sum()) and actual['misses']==int((~a['hits'][use]).sum()) and actual['recall']==float(a['hits'][use].mean())
            k=a['k'][mask];stats=row['candidate_decode'];assert stats==dict(mean=float(k.mean()),median=float(np.median(k)),p95=int(np.sort(k)[math.ceil(.95*len(k))-1]),max=int(k.max()),min=int(k.min()))
            if family=='cluster':
                np.testing.assert_array_equal(a['hits'],a['pure_hits']|a['fallback']);np.testing.assert_array_equal(a['k'],np.where(a['fallback'],V,a['pure_k']))
                assert row['dense_fallback_decode_calls']==int(a['fallback'][mask].sum())
            else:
                t=row['parameters']['T'];assert np.all((max(t,14)<=a['k'])&(a['k']<=min(V,t+14)))
            records[(family,row['id'])]=a;checks+=1
    def monotonic(family,rows,axis,condition):
        selected=sorted([x for x in rows if condition(x['parameters'])],key=lambda x:x['parameters'][axis])
        for left,right in zip(selected,selected[1:]):
            a=records[family,left['id']];b=records[family,right['id']];assert np.all(~a['hits']|b['hits']) and np.all(a['k']<=b['k'])
        return len(selected)
    axes=dict(cluster_R=monotonic('cluster',clusters,'R',lambda p:p['C']==128 and p['L']==16384),cluster_L=monotonic('cluster',clusters,'L',lambda p:p['C']==128 and p['R']==4),lowrank_T=monotonic('lowrank',lowrank,'T',lambda p:p['r']==128))
    vocabulary=np.unique(np.concatenate([train['raw_top_ids'].reshape(-1),train['winner'],np.arange(151643,151657,dtype='u4')]))
    possible=np.isin(cal['winner'],vocabulary);endpoint=next(x for x in clusters if x['parameters']==dict(C=128,R=128,L=V));ep=records['cluster',endpoint['id']]
    np.testing.assert_array_equal(ep['pure_hits'],possible);assert not ep['fallback'].any() and np.all(ep['pure_k']==len(vocabulary))
    with np.load(R/'parameters/cluster_C128.npz',allow_pickle=False) as z:union=np.unique(np.concatenate([z['ranked_ids'][i,:int(z['counts'][i])] for i in range(128)]+[np.arange(151643,151657,dtype='u4')]))
    np.testing.assert_array_equal(union,vocabulary)
    missing=[]
    for idx in np.flatnonzero(mask&~possible):missing.append(dict(index=int(idx),prompt_id=str(cal['prompt_ids'][idx]),category=str(cal['category'][idx]),token=int(cal['winner'][idx])))
    fullrank=next(x for x in lowrank if x['parameters']==dict(r=896,T=16384));feasible=dict(cluster=[x['id'] for x in clusters if gate(x)],lowrank=[x['id'] for x in lowrank if gate(x)])
    result=dict(state='PASS_CALIBRATION_ARRAYS_AND_BOUNDS_REVIEW',review_source_sha256=sha(Path(__file__)),calibration_only=True,independent_test_read=False,fpga='NOT_RUN',configuration_arrays_checked=checks,monotonic_axes=axes,
        cluster_training_support_bound=dict(unique_global_ids=len(vocabulary),decode_irreducible_misses=len(missing),missing=missing,category_recall=endpoint['quality']['decode']['by_category'],gate_pass=gate(endpoint),interpretation='Every positive-vote list under this train recipe is a subset of the same global train raw_top256/winners+specials union. No C/R/L retuning can cover these missing labels without a new source of candidates or explicit dense fallback. This is a bound on this finite calibration cohort/recipe, not universal language-model accuracy.'),
        rank896_T16384=dict(misses=fullrank['quality']['decode']['misses'],recall=fullrank['quality']['decode']['recall'],note='BF16 factorization and FP32 order: full mathematical rank is not a bit-identical dense preview'),
        proposed_calibration_gate='overall AND every category >=99.9% decode point recall; no independent certification',feasible=feasible)
    if not args.calibration_only:
        benchmark=read(R/'GPU_BENCHMARK.json');proof=read(R/'GPU_NUMERIC_PROOF.json');final=read(R/'RESULT.json');assert len(proof['records'])==180 and all(x['full_ids_and_raw_bits'] for x in proof['records'])
        assert len(benchmark['configurations'])==45 and benchmark['measurements']==5400
        for name,h in final['artifacts'].items():assert sha(R/name)==h
        timing=read(R/'GPU_TIMING_PLAN.json');assert sha(M/'scripts/benchmark_hyperparameters_20261023.py')==timing['script_sha256']
        for row in benchmark['configurations']:
            path=R/row['raw'];assert sha(path)==row['sha256'];obs=read(path);assert len(obs)==row['calls']==120
            assert {(x['case'],x['round']) for x in obs}=={(c,i) for c in ['chinese','english','code','math'] for i in range(30)}
            times=[x['wall_ms'] for x in obs];assert min(times)>0 and all(math.isfinite(x) for x in times)
            assert row['wall_median_ms']==statistics.median(times) and row['wall_p95_ms']==sorted(times)[113] and row['equivalent_m14_per_s']==120000/sum(times)
            for cat in ['chinese','english','code','math']:
                expected=next(x for x in proof['records'] if x['family']==row['family'] and x['config']==row['id'] and x['case']==cat)
                assert all(x['k']==expected['k'] for x in obs if x['case']==cat)
        dense=next(x for x in benchmark['configurations'] if x['family']=='dense');lookup={(x['family'],x['id']):x for x in benchmark['configurations']}
        result.update(state='PASS_FIRST_ROUND_CALIBRATION_AND_COUNTERBALANCED_GPU_REVIEW',gpu_measured_calls=5400,gpu_full_numeric_pairs=180,dense_control=dense,
            feasible_gpu=[dict(family=f,id=i,gpu_median_ms=lookup[f,i]['wall_median_ms'],gpu_equivalent_m14_per_s=lookup[f,i]['equivalent_m14_per_s']) for f,ids in feasible.items() for i in ids],
            limitations='Calibration search plus four fixed-input Eager reference timing, not population decode speed, optimized GPU, new independent quality, RTL or FPGA. Stage timings NOT_MEASURED. Parameter capacity/layout qualification remains separate.')
    save(R/('CALIBRATION_REVIEW.json' if args.calibration_only else 'INDEPENDENT_REVIEW.json'),result);print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
