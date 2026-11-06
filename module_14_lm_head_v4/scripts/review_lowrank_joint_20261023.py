"""Read-only audit of locked joint-study coverage and original observations."""
from pathlib import Path
import hashlib,json,math,statistics,sys
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split
R=M/'reports/hyperparameters_joint_20261023_r1';FIRST=M/'reports/hyperparameters_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def gate(row):
    q=row['quality']['decode'];return q['recall']>=.999 and all(x['recall']>=.999 for x in q['by_category'].values())
def main():
    plan=read(R/'PLAN.json');final=read(R/'RESULT.json');cal=load_split(M/'data/hidden_v1/calibration');assert len(set(cal['groups']))==320 and int(cal['decode'].sum())==4775
    assert plan['first_result_sha256']==sha(FIRST/'RESULT.json') and plan['script_sha256']==sha(M/'scripts/run_lowrank_joint_20261023.py')
    for name,h in final['artifacts'].items():assert sha(R/name)==h
    rows=read(R/'LOWRANK_CALIBRATION.json')['configurations'];assert len(rows)==13 and len({(x['parameters']['r'],x['parameters']['T']) for x in rows})==13
    proof=read(R/'GPU_NUMERIC_PROOF.json')['records'];assert len(proof)==56 and all(x['full_ids_raw_bits'] for x in proof)
    timing=read(R/'GPU_BENCHMARK.json');assert len(timing['configurations'])==14 and timing['measurements']==1680
    lookup={x['id']:x for x in timing['configurations']};arrays={};frontier=[]
    for row in rows:
        p=R/row['arrays'];assert sha(p)==row['sha256']
        with np.load(p,allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
        arrays[row['id']]=a
        for phase,mask in [('all',np.ones(len(cal['decode']),bool)),('decode',cal['decode']),('prefill',~cal['decode'])]:
            q=row['quality'][phase];assert q['steps']==int(mask.sum()) and q['misses']==int((~a['hits'][mask]).sum()) and q['recall']==float(a['hits'][mask].mean())
            for cat,value in q['by_category'].items():
                selected=mask&(cal['category']==cat);assert value['steps']==int(selected.sum()) and value['misses']==int((~a['hits'][selected]).sum()) and value['recall']==float(a['hits'][selected].mean())
        t=row['parameters']['T'];assert np.all((max(t,14)<=a['k'])&(a['k']<=min(151936,t+14)))
        if gate(row):
            b=lookup[row['id']];frontier.append(dict(id=row['id'],parameters=row['parameters'],misses=row['quality']['decode']['misses'],prefill_misses=row['quality']['prefill']['misses'],gpu_median_ms=b['wall_median_ms'],gpu_equivalent_m14_per_s=b['equivalent_m14_per_s'],factor_bytes=row['factor_logical_bytes'],K_mean=row['candidate_decode']['mean']))
    baseline=next(x for x in rows if x['id']=='r128_T16384');old=next(x for x in read(FIRST/'LOWRANK_CALIBRATION.json')['configurations'] if x['id']=='r128_T16384');assert baseline['quality']==old['quality'] and baseline['candidate_decode']==old['candidate_decode']
    for r in [128,256,512,896]:
        selected=sorted([x for x in rows if x['parameters']['r']==r],key=lambda x:x['parameters']['T'])
        for left,right in zip(selected,selected[1:]):assert np.all(~arrays[left['id']]['hits']|arrays[right['id']]['hits']) and np.all(arrays[left['id']]['k']<=arrays[right['id']]['k'])
    for b in timing['configurations']:
        path=R/b['raw'];assert sha(path)==b['sha256'];obs=read(path);assert len(obs)==120 and {(x['round'],x['case']) for x in obs}=={(i,c) for i in range(30) for c in ['chinese','english','code','math']}
        times=[x['wall_ms'] for x in obs];assert min(times)>0 and all(math.isfinite(t) for t in times);assert b['wall_median_ms']==statistics.median(times) and b['wall_p95_ms']==sorted(times)[113] and b['equivalent_m14_per_s']==120000/sum(times)
        for cat in ['chinese','english','code','math']:
            expected=next(x for x in proof if x['config']==b['id'] and x['case']==cat);assert all(x['k']==expected['k'] for x in obs if x['case']==cat)
    dense=lookup['dense'];fastest=min(frontier,key=lambda x:x['gpu_median_ms']);result=dict(state='PASS12_JOINT_CALIBRATION_AND_GPU_REFERENCE_REVIEW',new_configurations=12,control_configurations=2,gpu_numeric_pairs=56,measured_calls=1680,calibration_decode=4775,source_sha256=sha(Path(__file__)),feasible_points=frontier,fastest_feasible_joint_point=fastest,dense_control=dense,baseline_control=lookup['r128_T16384'],independent_test='NOT_RUN',board='NOT_RUN',scope='Calibration point gate only;4 fixed-input resident eager GPU performance reference. No new independent certification/FPGA/whole-LLM throughput. Finite joint scan is not a global optimum.')
    (R/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
