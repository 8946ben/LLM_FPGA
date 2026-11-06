"""Descriptive view of already frozen calibration, never another selection."""
from pathlib import Path
import hashlib,json
M=Path(__file__).resolve().parents[1];R=M/'reports/fusion_exp10_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cal=read(R/'CALIBRATION.json');plan=read(R/'PLAN.json');gate=plan['gate'];points=[]
    for c in cal['configurations']:
        k=c['candidate_decode'];budget=c['estimated_arena_bytes']<=gate['arena_bytes'] and c['fallback_decode']==0 and k['p95']<=gate['max_p95_K'] and k['max']<=gate['max_K']
        points.append(dict(id=c['id'],logical_mib=c['logical_mean_decode_bytes']/2**20,misses=c['quality']['decode']['misses'],K_mean=k['mean'],overlap_mean=c['overlap_decode']['mean'],arena_mib=c['estimated_arena_bytes']/2**20,budget_feasible=budget,selection_qualified=c['selection_qualified']))
    best=float('inf');frontier=[]
    for c in sorted((x for x in points if x['budget_feasible']),key=lambda x:(x['logical_mib'],x['misses'],x['id'])):
        if c['misses']<best:frontier.append(c['id']);best=c['misses']
    chosen=read(R/'SELECTION_LOCK.json')['chosen'];assert chosen in frontier
    baseline='_'.join(f'{k}{v}' for k,v in plan['baseline'].items());assert baseline in {x['id'] for x in points}
    report=dict(state='DERIVED_FROZEN_CALIBRATION_VIEW_NO_SELECTION_CHANGE',points=points,frontier=frontier,chosen=chosen,baseline=baseline,scope='Calibration320/4775decode only; x is the predeclared partial logical-read proxy, not measured AXI bytes or speed. Frontier enforces arena/K/no-fallback budgets. Fresh1000 labels are not used; chosen remains locked and independently quality-failed.',calibration_sha256=sha(R/'CALIBRATION.json'),selection_lock_sha256=sha(R/'SELECTION_LOCK.json'),source_sha256=sha(Path(__file__)),board='NOT_RUN')
    (R/'PARETO_CALIBRATION_VIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('CALIBRATION_VIEW',len(points),'budget_feasible',sum(x['budget_feasible'] for x in points),'frontier',len(frontier))
if __name__=='__main__':main()
