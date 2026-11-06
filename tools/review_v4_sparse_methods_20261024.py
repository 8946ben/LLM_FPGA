"""Independent read-only arithmetic/count/timing audit; no torch or hardware."""
from pathlib import Path
import collections, hashlib, json, math, statistics, sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/sparse_methods_20261024_r1/benchmark'
sys.path.insert(0,str(M))
from reference.quality_data import load_split
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    result=read(R/'RESULT.json');plan=read(R/'PLAN.json')
    assert not (R/'ACTIVE.lock').exists(),'Wait for actual completion'
    assert result['state']=='COMPLETE_ALL557_SAME_RUN_GPU_CALIBRATION_SUMMARY'
    assert result['plan_sha256']==sha(R/'PLAN.json')
    assert all(sha(ROOT/p)==h for p,h in plan['source_sha256'].items())
    pairs=result['configurations'];assert len(pairs)==len({p['id'] for p in pairs})==557
    assert collections.Counter(p['mode'] for p in pairs)==dict(cluster=23,lowrank=33,hybrid=432,dense=1,partial=16,affinity=18,learned=18,lsh=16)
    proof=read(R/'GPU_NUMERIC_PROOF.json')['records'];assert len(proof)==2228
    assert result['numeric_proof_sha256']==sha(R/'GPU_NUMERIC_PROOF.json')
    gold={(p['id'],p['case']):p for p in proof};assert len(gold)==2228
    cal=load_split(M/'data/hidden_v1/calibration');assert cal['decode'].sum()==4775 and len(set(cal['groups']))==320
    source_cache={};quality_checked=set();total=0;array_checks=[]
    for p in pairs:
        if p['mode']!='dense':
            source=p['calibration_source']
            if source not in source_cache:source_cache[source]={r['id']:r for r in read(ROOT/source)['configurations']}
            row=source_cache[source][p['config']];assert row['parameters']==p['parameters'] and row['quality']==p['quality']
            path=(ROOT/source).parent/row['arrays'];assert sha(path)==row['sha256']
            with np.load(path,allow_pickle=False) as a:
                hits=a['hits'];ks=a['k'];assert hits.shape==ks.shape==cal['winner'].shape
                for phase,mask in [('all',np.ones(len(hits),bool)),('decode',cal['decode']),('prefill',~cal['decode'])]:
                    q=p['quality'][phase];assert q['steps']==int(mask.sum()) and q['misses']==int((~hits[mask]).sum()) and q['recall']==float(hits[mask].mean())
                    for cat,c in q['by_category'].items():
                        selected=mask&(cal['category']==cat);assert c['steps']==int(selected.sum()) and c['misses']==int((~hits[selected]).sum()) and c['recall']==float(hits[selected].mean())
                d=ks[cal['decode']];actual=dict(mean=float(d.mean()),median=float(np.median(d)),p95=int(np.sort(d)[math.ceil(.95*len(d))-1]),max=int(d.max()),min=int(d.min()))
                assert p['candidate_decode']==actual
            array_checks.append(dict(id=p['id'],sha256=sha(path)))
        raw=R/p['raw'];assert sha(raw)==p['sha256'];obs=read(raw);assert len(obs)==120
        assert collections.Counter((x['case'],x['round']) for x in obs)=={(c,i):1 for c in plan['cases'] for i in range(30)}
        ms=[x['wall_ms'] for x in obs];assert all(math.isfinite(x) and x>0 for x in ms)
        assert p['wall_mean_ms']==statistics.mean(ms) and p['wall_median_ms']==statistics.median(ms) and p['wall_p95_ms']==sorted(ms)[113]
        assert p['equivalent_m14_per_s']==120000/sum(ms)
        for x in obs:
            expected=gold[p['id'],x['case']];assert expected['full_ids_raw_bits']
            for k in ['k','token','score_bits','crc']:assert x[k]==expected[k]
        for cat,c in p['cases'].items():
            rows=[x for x in obs if x['case']==cat];assert c==dict(calls=30,k=gold[p['id'],cat]['k'],mean_ms=statistics.mean(x['wall_ms'] for x in rows))
        total+=len(obs)
    assert total==result['measurements']==66840
    sentinels=read(R/'DENSE_SENTINELS.json');assert len(sentinels)==660
    byround=[]
    for i in range(30):
        rows=[x['wall_ms'] for x in sentinels if x['round']==i];assert len(rows)==22
        byround.append(dict(round=i,mean_ms=statistics.mean(rows),min_ms=min(rows),max_ms=max(rows)))
    # Preserve old quality failure independently of the new descriptive census.
    old=read(M/'reports/fusion_exp10_20261023_r1/FINAL_QUALITY.json')
    assert old['selected']['report']['decode']['misses']==19
    audit=dict(state='PASS_INDEPENDENT_557_COUNTS_ARRAYS_RAW_TIMINGS_AND_SOURCE_SHA',updated=result['completed'],result_sha256=sha(R/'RESULT.json'),plan_sha256=sha(R/'PLAN.json'),calibration_manifest_sha256=cal['manifest_sha256'],configurations=557,calibration_arrays_verified=len(array_checks),full_numeric_pairs=len(proof),timed_calls=total,dense_sentinel_calls=660,dense_sentinel_rounds=byround,quality='Original calibration only; historical independent groups stay separate; no final certification or new selection',board='NOT_RUN',eda='NOT_RUN',checks='Every source SHA; full coverage/K arrays and category counts; all120/case-round and output tuples per config; exact raw-time aggregations')
    (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='dense_sentinel_rounds'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
