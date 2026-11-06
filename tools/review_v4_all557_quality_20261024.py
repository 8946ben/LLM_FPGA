"""Independent complete saved-array/timing audit and extra NumPy candidate reconstruction."""
from pathlib import Path
import collections,hashlib,json,math,statistics,sys,zlib,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
sys.path[:0]=[str(M),str(M/'scripts'),str(M/'experiments/sparse_methods_20261024')]
import run_sparse_quality_all557_20261024 as U
from reference.hyperparameter_study import SPECIAL,route_numpy,pure_route_candidates,preview_numpy
from reference.quality_data import load_split
import sparse_methods as S
R=U.OUT;B=R/'benchmark'
def main():
    U.check();quality=U.read(R/'QUALITY.json');bench=U.read(B/'RESULT.json');plan=U.read(B/'PLAN.json');locked=U.read(R/'PLAN.json')
    assert not (R/'ACTIVE.lock').exists() and not (B/'ACTIVE.lock').exists()
    assert len(quality['configurations'])==len(bench['configurations'])==557
    assert bench['plan_sha256']==U.sha(B/'PLAN.json')
    optimization=U.read(R/'EVALUATION_REPORT_OPTIMIZATION_ENTRY.json')
    assert optimization['source_sha256']==U.sha(M/'scripts/evaluate_sparse_quality_all557_fast_20261024.py')
    assert optimization['frozen_evaluator_sha256']==U.sha(M/'scripts/run_sparse_quality_all557_20261024.py')
    count_entry=U.read(R/'GPU_COUNT_ENTRY.json');qualification=U.read(R/'GPU_COUNT_QUALIFICATION.json')
    assert count_entry['source_sha256']==U.sha(M/'scripts/evaluate_sparse_quality_all557_gpu_counts_20261024.py')
    assert qualification['state']=='PASS_EXACT_INTEGER_COUNTER_AND_ALL_PRIOR_ARRAYS' and qualification['first2_configs']==556
    assert qualification['entry_sha256']==U.sha(R/'GPU_COUNT_ENTRY.json')
    assert all(U.sha(ROOT/p)==h for p,h in plan['source_sha256'].items())
    assert [(p['id'],p['parameters']) for p in quality['configurations']]==[(p['id'],p['parameters']) for p in locked['configurations']]
    data=load_split(U.DATA);assert len(data['hidden'])==15956 and int(data['decode'].sum())==14956
    records=data['manifest']['records'];totals0=np.array([r['steps']-1 for r in records],dtype='i8');assert (totals0>0).all()
    starts=np.r_[0,np.cumsum(totals0)[:-1]];group_order=np.argsort([r['group_sha256'] for r in records]);group_totals=totals0[group_order]
    bootstrap=np.random.default_rng(20261021).integers(len(group_totals),size=(300,len(group_totals)))
    numeric=U.read(B/'GPU_NUMERIC_PROOF.json')['records'];gold={(p['id'],p['case']):p for p in numeric};assert len(gold)==4456
    original_proof={(p['id'],p['case']):p for p in U.read(S.R/'benchmark/GPU_NUMERIC_PROOF.json')['records']}
    six_proof={(p['config'],p['case']):p for p in U.read(U.PREVIOUS/'benchmark/NUMERIC_PROOF.json')['records']}
    six_inputs=U.read(U.PREVIOUS/'benchmark/PLAN.json')['inputs']
    for c in ['chinese','english','code','math']:
        assert plan['input_sha256']['old_'+c]==dict(hidden=U.sha(M/f'reports/lowrank_fixture_20261021/{c}.hidden.bin'),history=U.sha(M/f'reports/lowrank_fixture_20261021/{c}.history.bin'))
        assert plan['input_sha256']['new_'+c]==dict(hidden=six_inputs[c]['hidden_sha256'],history=six_inputs[c]['history_sha256'])
    for (id,case),g in gold.items():
        prior=original_proof.get((id,case[4:])) if case.startswith('old_') else six_proof.get((id,case[4:]))
        if prior:
            for key in ['k','token','score_bits','crc']:assert g[key]==prior[key]
            for key in ['ids_sha256','raw_sha256']:
                if key in prior:assert g[key]==prior[key]
    bm={p['id']:p for p in bench['configurations']};arrays={};total=0;cohort_rows={'old':[],'new':[]};cases=['chinese','english','code','math'];checks=[]
    for index,pair in enumerate(quality['configurations']):
        U.stop();path=R/pair['arrays'];assert U.sha(path)==pair['sha256'];a=np.load(path);hit=a['hits'];k=a['k'];arrays[pair['id']]={name:a[name].copy() for name in ['hits','k','fallback']};assert hit.shape==k.shape==(15956,)
        for phase,mask in [('all',np.ones(15956,bool)),('decode',data['decode']),('prefill',~data['decode'])]:
            q=pair['quality'][phase];assert q['steps']==int(mask.sum()) and q['misses']==int((~hit[mask]).sum()) and q['recall']==float(hit[mask].mean())
            for cat,v in q['by_category'].items():
                use=mask&(data['category']==cat);assert v==dict(steps=int(use.sum()),misses=int((~hit[use]).sum()),recall=float(hit[use].mean()))
        kv=k[data['decode']];assert pair['candidate_decode']==dict(mean=float(kv.mean()),median=float(np.median(kv)),p95=int(np.sort(kv)[math.ceil(.95*len(kv))-1]),max=int(kv.max()),min=int(kv.min()))
        q=pair['quality']['decode'];gate=q['recall']>=.99 and all(v['recall']>=.99 for v in q['by_category'].values());assert pair['gate99']==('PASS' if gate else 'FAIL')
        successes=np.add.reduceat(hit[data['decode']].astype('i8'),starts)[group_order]
        complete=pair['quality']['complete_prompt_decode_match'];assert complete['prompts']==1000 and complete['all_steps_match_prompts']==int(np.sum(successes==group_totals))
        ci=np.quantile(successes[bootstrap].sum(axis=1)/group_totals[bootstrap].sum(axis=1),[.025,.975]).tolist();assert pair['quality']['decode_prompt_bootstrap_interval95']==ci
        b=bm[pair['id']];assert b['parameters']==pair['parameters'];raw=B/b['raw'];assert U.sha(raw)==b['sha256'];obs=U.read(raw);assert len(obs)==240
        assert collections.Counter((x['case'],x['round']) for x in obs)=={(c,i):1 for c in plan['cases'] for i in range(30)}
        times=[x['wall_ms'] for x in obs];assert b['equivalent_m14_per_s']==240000/sum(times)
        for x in obs:
            assert math.isfinite(x['wall_ms']) and x['wall_ms']>0
            g=gold[pair['id'],x['case']]
            for key in ['k','token','score_bits','crc']:assert x[key]==g[key]
            assert x['crc']==zlib.crc32(struct.pack('<II',x['token'],x['score_bits']))
        for cohort in ['old','new']:
            subset=[dict(x,case=x['case'].split('_',1)[1]) for x in obs if x['case'].startswith(cohort+'_')];assert len(subset)==120
            dest=R/f'cohorts/{cohort}/timing/{pair["id"]}.json';U.write(dest,subset);ms=[x['wall_ms'] for x in subset]
            cohort_rows[cohort].append(dict(id=pair['id'],calls=120,rate=120000/sum(ms),mean_ms=statistics.mean(ms),median_ms=statistics.median(ms),p95_ms=sorted(ms)[113],cases={c:dict(calls=30,k=gold[pair['id'],cohort+'_'+c]['k'],mean_ms=statistics.mean(x['wall_ms'] for x in subset if x['case']==c)) for c in cases},raw=dest.relative_to(ROOT).as_posix(),sha256=U.sha(dest)))
        total+=len(obs);checks.append(dict(id=pair['id'],gate99=pair['gate99'],decode_misses=q['misses']))
        if (index+1)%50==0:U.progress('REVIEW_ARRAYS_AND_TIMINGS',completed=index+1,total=557)
    assert total==bench['measurements']==133680
    sentinels=U.read(B/'DENSE_SENTINELS.json');assert len(sentinels)==660
    for x in sentinels:assert math.isfinite(x['wall_ms']) and x['wall_ms']>0
    # Additional8 decode states, independent of the8 timed fixtures.
    bits=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(U.V,U.H))
    engine=S.Engine.__new__(S.Engine);engine.bits=bits;engine.cpu={k:dict(np.load(S.R/a['path'])) for k,a in U.read(S.R/'PARAMETERS.json')['files'].items()}
    centers={};factors={}
    for key in U.params():
        if key.startswith('C'):centers[int(key[1:])]=(U.model(key),np.load(U.FIRST/f'parameters/norms_{key}.npy'))
        else:factors[int(key[1:])]=U.model(key)
    indices=[]
    for c in cases:
        v=np.flatnonzero(data['decode']&(data['category']==c));indices.extend([int(v[31]),int(v[-37])])
    cache=U.read(R/'CACHE.json');primitive_checks=0;point_checks=0
    for ii,i in enumerate(indices):
        U.stop();h=data['hidden'][i];seen=data['seen'][i];history=np.zeros((U.V+31)//32,'u4')
        for token in seen:history[int(token)>>5]|=np.uint32(1<<(int(token)&31))
        route_orders={c:route_numpy(h,m['centers_bf16'],norm)[0] for c,(m,norm) in centers.items()};loworders={}
        for rank,m in factors.items():
            preview,_=preview_numpy(h,m['a_bf16'],m['b_bf16'],seen);loworders[rank]=np.argsort(-preview,kind='stable')
        independent={}
        for key,item in cache['items'].items():
            family,name=key.split(':',1)
            if family=='route':
                import re
                c,rr,ll=map(int,re.fullmatch(r'C(\d+)_R(\d+)_L(\d+)',name).groups());m=centers[c][0];ids,fallback=pure_route_candidates(m,route_orders[c][:rr],ll);ids=np.arange(U.V,dtype='u4') if fallback else ids
            elif family=='lowrank':
                import re
                rank,t=map(int,re.fullmatch(r'r(\d+)_T(\d+)',name).groups());ids=np.union1d(loworders[rank][:t],SPECIAL).astype('u4')
            else:
                pair=next(p for p in locked['configurations'] if p['id']==name);ids=engine.cpu_ids(pair,h,history)
            packed=np.memmap(R/item['path'],dtype='u1',mode='r',shape=(15956,U.WIDTH));mask=np.unpackbits(packed[i],bitorder='little').astype(bool);actual=np.flatnonzero(mask).astype('u4');np.testing.assert_array_equal(actual,ids);independent[key]=ids;primitive_checks+=1
        for pair in locked['configurations']:
            p=pair['parameters'];mode=pair['mode']
            if mode=='dense':ids=np.arange(U.V,dtype='u4')
            elif mode=='hybrid':ids=np.union1d(independent['route:'+U.route_key(p)],independent['lowrank:'+U.low_key(p)])
            elif mode=='cluster':ids=independent['route:'+U.route_key(p)]
            elif mode=='lowrank':ids=independent['lowrank:'+U.low_key(p)]
            else:ids=independent['extra:'+pair['id']]
            a=arrays[pair['id']];assert int(a['k'][i])==len(ids) and bool(a['hits'][i])==bool(np.any(ids==data['winner'][i]));point_checks+=1
        U.progress('REVIEW_EXTRA_NUMPY_STATES',completed=ii+1,total=8,point_checks=point_checks)
    previous=U.read(U.PREVIOUS/'QUALITY.json')
    for p in previous['configurations']:
        a=np.load(ROOT/p['coverage']);np.testing.assert_array_equal(arrays[p['id']]['hits'],a['hits']);np.testing.assert_array_equal(arrays[p['id']]['k'],a['k'])
    U.check();assert point_checks==4456
    for cohort,rows in cohort_rows.items():U.write(R/f'cohorts/{cohort}/TIMING_SUMMARY.json',dict(state='PASS_PAIRED557_SAME_RUN',configurations=rows,measurements=66840,scope='4 fixed inputs per cohort; not whole corpus/LLM decode'))
    U.write(R/'INDEPENDENT_REVIEW.json',dict(state='PASS_ALL557_ARRAYS_PAIRED133680_TIMINGS_AND_EXTRA4456_NUMPY_CASES',completed=U.now(),quality_sha256=U.sha(R/'QUALITY.json'),benchmark_sha256=U.sha(B/'RESULT.json'),configurations=557,measurements=total,numeric_pairs=4456,extra_numpy_primitives=primitive_checks,extra_numpy_points=point_checks,first_six_arrays_unchanged=True,mode_counts=dict(collections.Counter(p['mode'] for p in quality['configurations'])),gate99_pass_counts=dict(collections.Counter(p['mode'] for p in quality['configurations'] if p['gate99']=='PASS')),records=checks,board='NOT_RUN',eda='NOT_RUN'))
    print('ALL557_INDEPENDENT_REVIEW=PASS',flush=True)
if __name__=='__main__':main()
