"""Read-only raw-observation audit; stdlib only, no CUDA initialization."""
from pathlib import Path
import hashlib,json,math,statistics
M=Path(__file__).resolve().parents[1];R=M/'reports/fusion_exp10_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    timing=read(R/'GPU_TIMING_PLAN.json');result=read(R/'GPU_BENCHMARK.json');proof=read(R/'GPU_NUMERIC_PROOF.json')['records'];short=read(R/'SHORTLIST.json');selection=read(R/'SELECTION_LOCK.json');stable=read(R/'GPU_STABILITY.json');assert result['measurements']==len(timing['pairs'])*120 and len(proof)==len(timing['pairs'])*4 and all(x['full_ids_raw_bits'] for x in proof)
    assert timing['script_sha256']==sha(M/'scripts/benchmark_fusion10_20261023.py') and result['plan_sha256']==sha(R/'GPU_TIMING_PLAN.json') and result['proof_sha256']==sha(R/'GPU_NUMERIC_PROOF.json')
    lookup={(x['id'],x['case']):x for x in proof}
    for row in result['configurations']:
        path=R/row['raw'];assert sha(path)==row['sha256'];obs=read(path);assert len(obs)==row['calls']==120 and {(x['case'],x['round']) for x in obs}=={(c,i) for c in ['chinese','english','code','math'] for i in range(30)}
        times=[x['wall_ms'] for x in obs];assert all(math.isfinite(x) and x>0 for x in times) and statistics.median(times)==row['wall_median_ms'] and sorted(times)[113]==row['wall_p95_ms'] and 120000/sum(times)==row['equivalent_m14_per_s']
        for x in obs:assert x['k']==lookup[row['id'],x['case']]['k']
    assert len(stable['observations'])==1000 and stable['selected']==selection['chosen']==short['configurations'][0]['id']
    for i,actual in enumerate(stable['observations']):
        assert actual['index']==i and actual['case']==['chinese','english','code','math'][i%4];gold=lookup[selection['chosen'],actual['case']]
        for k in ['k','token','score_bits','crc']:assert actual[k]==gold[k]
    out=dict(state='PASS_RAW_TIMING_NUMERIC_PAIRS_AND1000_CHANGING_INPUT_CALLS',source_sha256=sha(Path(__file__)),gpu_pairs=len(timing['pairs']),full_numeric_pairs=len(proof),measured_calls=result['measurements'],stable_calls=1000,selected=selection['chosen'],selection_sha256=sha(R/'SELECTION_LOCK.json'),board='NOT_RUN',scope='Independent arithmetic of saved times/observations and result/CRC bindings, no new GPU call or quality labels')
    (R/'GPU_REVIEW.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
