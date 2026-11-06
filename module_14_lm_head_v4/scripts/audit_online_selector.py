"""Materialize chosen calibration candidates without exposing labels to selector."""
from pathlib import Path
import hashlib,importlib.util,json,sys,time
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split,recall_report
from reference.hybrid_selector import candidate_batches
from reference.candidate_head import run_candidate_head
spec=importlib.util.spec_from_file_location('_base',M/'scripts/evaluate_selectors.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def main():
    out=M/'reports/selector_hybrid_p2_20261021';p=M/'reports/selector_p2_20261021'
    summary=json.loads((out/'CALIBRATION.json').read_text());name=summary['chosen_calibration_configuration']
    chosen=next(x for x in summary['configurations'] if x['name']==name);c=chosen['config']
    selection=dict(chosen=name,calibration_sha256=base.sha(out/'CALIBRATION.json'),base_parameter_manifest_sha256=base.sha(p/'PARAMETERS.json'))
    lock=out/'SELECTION_LOCK.json'
    if lock.exists():assert json.loads(lock.read_text())==selection
    else:base.write(lock,selection)
    data=load_split(M/'data/hidden_v1/calibration');assert data['manifest_sha256']==summary['calibration_manifest_sha256']
    hashes=json.loads((p/'PARAMETERS.json').read_text())
    def load(n):
        assert base.sha(p/n)==hashes[n]
        with np.load(p/n,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
    router=load('route_r128.npz');low=load(f"lowrank_r{c['rank']}.npz")
    hits=[];counts=[];overlaps=[];exact=[];fallbacks=0
    # Four decode predictions per category, chosen by order before inspecting hits.
    sample=set()
    for category in sorted(set(data['category'])):
        sample.update(np.flatnonzero((data['category']==category)&data['decode'])[:4].tolist())
    weights=np.memmap(M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(151936,896))
    source_rows=data['manifest']['records'];score_bits=[]
    for record in source_rows:
        if 'excluded' not in record:
            with np.load(M/'data/hidden_v1/calibration'/record['npz'],allow_pickle=False) as z:score_bits.extend(z['dense_score_bits'].tolist())
    started=time.perf_counter();exact_seconds=0.
    for row,ids,meta in candidate_batches(data['hidden'],data['seen'],router,low['a_bf16'],low['b_bf16'],base.mandatory_ids(),
        route_count=c['route_count'],route_k=c['route_k'],lowrank_k=c['lowrank_k']):
        winner=int(data['winner'][row]);slot=np.searchsorted(ids,winner);hit=slot<len(ids) and ids[slot]==winner
        hits.append(bool(hit));counts.append(len(ids));overlaps.append(meta['overlap']);fallbacks+=meta['explicit_dense_fallback']
        # Include actual missed winners to verify expected behavior as well as covered rows.
        if row in sample or not hit:
            history=np.zeros((151936+31)//32,dtype='u4')
            for token in data['seen'][row]:history[int(token)>>5]|=np.uint32(1)<<np.uint32(int(token)&31)
            t=time.perf_counter();got=run_candidate_head(data['hidden'][row],weights,ids,history);exact_seconds+=time.perf_counter()-t
            assert (got['selected_token']==winner)==hit
            if hit:assert got['selected_score_bits']==int(score_bits[row])
            exact.append(dict(row=row,category=str(data['category'][row]),k=len(ids),dense_winner_present=bool(hit),
                token_matches_dense=got['selected_token']==winner,score_bits_match_dense=got['selected_score_bits']==int(score_bits[row])))
        if (row+1)%500==0:print(f'ONLINE_CALIBRATION {row+1}/{len(data["winner"])}',flush=True)
    elapsed=time.perf_counter()-started;quality=recall_report(np.array(hits),data)
    assert quality['decode']==chosen['calibration']['decode'] and quality['prefill']==chosen['calibration']['prefill']
    counts=np.array(counts);decode=data['decode'];selector_bytes=2*128*896+2*c['rank']*(896+151936)
    result=dict(state='PASS',chosen=name,selection_lock_sha256=base.sha(lock),
        online_source_sha256=base.sha(M/'reference/hybrid_selector.py'),audit_source_sha256=base.sha(Path(__file__)),
        calibration_manifest_sha256=data['manifest_sha256'],report=quality,
        candidates=base.describe_counts(counts[decode],selector_bytes),overlap_mean=float(np.mean(np.array(overlaps)[decode])),
        explicit_dense_fallback_steps=fallbacks,candidate_exact_head_cases=exact,
        cpu_materialization_seconds_excluding_exact_head=elapsed-exact_seconds,
        evidence='Actual online top-K/union constructed for all calibration predictions without labels as selector inputs; stable lower-ID ties; selected-row exact head independently checked on listed examples.',
        limits='CPU FP32 BLAS/batch32 preview only; not PL arithmetic, online FPGA latency, free-generation quality or board acceptance. K stats are calibration only.',
        uncounted_traffic='Base logical bytes omit route-list reads, merged-table writes, preview/top-K scratch traffic, history/control and bus transaction overhead; do not infer speedup from byte ratio.')
    base.write(out/'ONLINE_CALIBRATION_AUDIT.json',result);print('ONLINE_CALIBRATION_AUDIT=PASS',flush=True)
if __name__=='__main__':main()
