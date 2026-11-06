"""Independent saved-array, source, gate and raw timing audit; no target access."""
from pathlib import Path
import hashlib,json,math,statistics,sys,zlib,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';Q=M/'reports/sparse_quality_20261024_r1';D=M/'data/sparse_quality_20261024'
sys.path[:0]=[str(M),str(M/'scripts'),str(M/'experiments/sparse_methods_20261024')]
import sparse_quality_common_20261024 as R
from reference.quality_data import load_split
from reference.hyperparameter_study import route_numpy,pure_route_candidates
from reference.numeric_contract import compute_raw_logits
import sparse_methods as S

def main():
    entry=R.checked();quality=R.read(Q/'QUALITY.json');bench=R.read(Q/'benchmark/RESULT.json');plan=R.read(Q/'benchmark/PLAN.json')
    assert R.sha(Q/'QUALITY.json')==plan['quality_sha256']
    data=load_split(M/'data/hidden_sparse_quality_20261024/holdout');n=len(data['hidden']);assert len(set(data['groups']))==1000
    dense_bits=np.concatenate([np.load(M/'data/hidden_sparse_quality_20261024/holdout'/r['npz'])['dense_score_bits'] for r in data['manifest']['records']])
    locked=R.read(Q/'SELECTION_LOCK.json')['configurations'];assert [p['id'] for p in quality['configurations']]==[p['id'] for p in locked]
    bm={p['id']:p for p in bench['configurations']};arrays={};checks=[]
    for row in quality['configurations']:
        a=np.load(ROOT/row['coverage'],allow_pickle=False);assert R.sha(ROOT/row['coverage'])==row['coverage_sha256'];arrays[row['id']]=a
        for k,expected in [('decode',data['decode']),('category',data['category']),('groups',data['groups']),('dense_token',data['winner']),('dense_score_bits',dense_bits)]:np.testing.assert_array_equal(a[k],expected)
        hit=a['hits'];assert hit.shape==(n,);np.testing.assert_array_equal(hit,a['token']==data['winner']);np.testing.assert_array_equal(a['score_bits'][hit],dense_bits[hit]);assert (a['k']>=14).all() and (a['k']<=S.V).all()
        for phase,mask in [('all',np.ones(n,bool)),('decode',data['decode']),('prefill',~data['decode'])]:
            saved=row['report'][phase];assert saved['steps']==int(mask.sum()) and saved['misses']==int((~hit[mask]).sum());assert saved['recall']==float(hit[mask].mean())
            for cat,q in saved['by_category'].items():
                m=mask&(data['category']==cat);assert q==dict(steps=int(m.sum()),misses=int((~hit[m]).sum()),recall=float(hit[m].mean()))
        q=row['report']['decode'];gate=q['recall']>=.99 and all(v['recall']>=.99 for v in q['by_category'].values());assert row['gate99']==('PASS' if gate else 'FAIL')
        k=a['k'][data['decode']];assert row['candidate_decode']==dict(mean=float(k.mean()),p95=int(np.quantile(k,.95,method='higher')),maximum=int(k.max()))
        groups=sorted(set(data['groups']));matched=sum(bool(hit[(data['groups']==g)&data['decode']].all()) for g in groups)
        assert row['report']['complete_prompt_decode_match']['all_steps_match_prompts']==matched
        b=bm[row['id']];obs=R.read(ROOT/b['raw']);assert R.sha(ROOT/b['raw'])==b['sha256'];assert len(obs)==120
        ms=[v['wall_ms'] for v in obs];assert all(math.isfinite(x) and x>0 for x in ms)
        assert b['equivalent_m14_per_s']==120000/sum(ms) and b['wall_mean_ms']==statistics.mean(ms) and b['wall_median_ms']==statistics.median(ms) and b['wall_p95_ms']==sorted(ms)[113]
        proof={(x['config'],x['case']):x for x in R.read(Q/'benchmark/NUMERIC_PROOF.json')['records']}
        for cat,c in b['cases'].items():
            chosen=[v for v in obs if v['case']==cat];assert len(chosen)==30 and c['mean_ms']==statistics.mean(v['wall_ms'] for v in chosen)
            expected=proof[row['id'],cat]
            for v in chosen:
                for key in ['k','token','score_bits','crc']:assert v[key]==expected[key]
                assert v['crc']==zlib.crc32(struct.pack('<II',v['token'],v['score_bits']))
        checks.append(dict(id=row['id'],decode_misses=q['misses'],gate99=row['gate99'],timings=120))
    # Independent NumPy selector/output reconstruction on two additional decode rows/category.
    bits=np.memmap(R.WEIGHT,dtype='<u2',mode='r',shape=(S.V,S.H));engine=S.Engine.__new__(S.Engine);engine.bits=bits
    files=R.read(S.R/'PARAMETERS.json')['files'];engine.cpu={'channels':dict(np.load(S.R/files['channels']['path']))}
    param=R.read(S.FIRST/'PARAMETERS.json')['files']['C128'];model=dict(np.load(S.FIRST/param['path']));norms=np.load(S.FIRST/'parameters/norms_C128.npy')
    indices=[]
    for cat in ['chinese','english','code','math']:
        available=np.flatnonzero(data['decode']&(data['category']==cat));indices.extend([int(available[17]),int(available[-19])])
    extra=[]
    for i in indices:
        h=data['hidden'][i];history=np.zeros((S.V+31)//32,'u4')
        for old in data['seen'][i]:history[int(old)>>5]|=np.uint32(1<<(int(old)&31))
        raw=compute_raw_logits(h,bits);score=R.policy(raw[None,:],[data['seen'][i]])[0];assert int(score.argmax())==int(data['winner'][i]) and int(score[data['winner'][i]].view('u4'))==int(dense_bits[i])
        order,_=route_numpy(h,model['centers_bf16'],norms)
        for pair in locked:
            ids=np.arange(S.V,dtype='u4') if pair['mode']=='dense' else pure_route_candidates(model,order[:pair['parameters']['R']],16384)[0] if pair['mode']=='cluster' else engine.cpu_ids(pair,h,history)
            a=arrays[pair['id']];assert hashlib.sha256(ids.tobytes()).hexdigest()==a['candidate_sha256'][i];j=int(score[ids].argmax());assert int(a['token'][i])==int(ids[j]) and int(a['score_bits'][i])==int(score[ids[j]].view('u4'))
            extra.append(dict(config=pair['id'],prediction=i,full_cpu_ids_and_output=True))
    R.checked();assert len(extra)==48 and len(checks)==6
    # Same-input, same six-point runtime control exposed a cross-round speed shift.
    control=R.read(Q/'benchmark_calibration_control/RESULT.json');cp=R.read(Q/'benchmark_calibration_control/PLAN.json')
    old={x['id']:x for x in R.read(S.R/'benchmark/RESULT.json')['configurations']};control_rows=[]
    for c,x in cp['inputs'].items():
        hp=M/f'reports/lowrank_fixture_20261021/{c}.hidden.bin';bp=M/f'reports/lowrank_fixture_20261021/{c}.history.bin'
        assert R.sha(hp)==x['hidden_sha256'] and R.sha(bp)==x['history_sha256']
    for row in control['configurations']:
        obs=R.read(ROOT/row['raw']);assert len(obs)==120 and R.sha(ROOT/row['raw'])==row['sha256']
        ms=[x['wall_ms'] for x in obs];assert row['equivalent_m14_per_s']==120000/sum(ms)
        for c,v in row['cases'].items():
            chosen=[x for x in obs if x['case']==c];assert len(chosen)==30 and v['mean_ms']==statistics.mean(x['wall_ms'] for x in chosen)
            historical=old[row['id']]['cases'][c];assert historical['k']==v['k']
        control_rows.append(dict(id=row['id'],historical557_rate=old[row['id']]['equivalent_m14_per_s'],current6_same_input_rate=row['equivalent_m14_per_s']))
    for name in ['benchmark','benchmark_calibration_control']:
        proof={(x['config'],x['case']):x for x in R.read(Q/name/'NUMERIC_PROOF.json')['records']}
        sentinels=R.read(Q/name/'DENSE_SENTINELS.json');assert len(sentinels)==30
        for s in sentinels:
            assert math.isfinite(s['wall_ms']) and s['wall_ms']>0
            for k in ['k','token','score_bits','crc']:assert s[k]==proof['dense',s['case']][k]
    R.write(Q/'TIMING_COMPARABILITY_REVIEW.json',dict(state='PASS_CONTROL_CONFIRMS_CROSS_ROUND_SHIFT_NOT_INPUT_ONLY',records=control_rows,control_sha256=R.sha(Q/'benchmark_calibration_control/RESULT.json'),conclusion='Original inputs also much faster in limited6 runtime; do not attribute old/new absolute rate change to data or algorithm. No causal diagnosis of driver/thermal/residency/process overhead is claimed. Original557 remains historical; paired6 comparison uses current control.',copied_quality_metadata='Control benchmark row.report was inherited from fresh quality, not a calibration re-evaluation; paired UI takes quality exclusively from original calibration arrays.'))
    R.write(Q/'INDEPENDENT_REVIEW.json',dict(state='PASS_SOURCES_ARRAYS_GATES_TIMINGS_AND48_CPU_RECONSTRUCTIONS',completed=R.now(),quality_sha256=R.sha(Q/'QUALITY.json'),benchmark_sha256=R.sha(Q/'benchmark/RESULT.json'),entry_sha256=R.sha(D/'EVALUATION_ENTRY_LOCK.json'),records=checks,extra_cpu=extra,configurations=6,prompts=1000,predictions=n,decode=int(data['decode'].sum()),measurements=720,board='NOT_RUN',eda='NOT_RUN',browser_visual='NOT_RUN'))
    print('INDEPENDENT_REVIEW=PASS',flush=True)
if __name__=='__main__':main()
