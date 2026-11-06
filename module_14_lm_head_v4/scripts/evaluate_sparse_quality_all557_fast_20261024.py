"""Same reports with pre-indexed groups; frozen selector/cache evaluator unchanged."""
import numpy as np
_context=None
def fast_report(hits,data):
    global _context
    hits=np.asarray(hits,dtype=bool);assert hits.shape==data['winner'].shape
    if _context is None or _context[0] is not data:
        groups,inv=np.unique(data['groups'],return_inverse=True)
        totals=np.bincount(inv[data['decode']],minlength=len(groups)).astype('i8')
        _context=(data,inv,totals,totals>0,len(groups))
    _,inv,totals,valid,group_count=_context
    result={}
    for phase,mask in [('all',np.ones(len(hits),bool)),('decode',data['decode']),('prefill',~data['decode'])]:
        by={}
        for c in sorted(set(data['category'])):
            use=mask&(data['category']==c);by[str(c)]=dict(steps=int(use.sum()),misses=int((~hits[use]).sum()),recall=float(hits[use].mean()) if use.any() else None)
        result[phase]=dict(steps=int(mask.sum()),misses=int((~hits[mask]).sum()),recall=float(hits[mask].mean()) if mask.any() else None,by_category=by)
    if valid.any():
        success=np.bincount(inv[data['decode']&hits],minlength=group_count).astype('i8')[valid];totals=totals[valid]
        rng=np.random.default_rng(20261021);samples=rng.integers(len(totals),size=(300,len(totals)))
        estimates=success[samples].sum(axis=1)/totals[samples].sum(axis=1)
        result['decode_prompt_bootstrap_interval95']=np.quantile(estimates,[.025,.975]).tolist()
        n=len(totals);rate=float(np.mean(success==totals));z=1.959963984540054
        center=(rate+z*z/(2*n))/(1+z*z/n);half=z*np.sqrt(rate*(1-rate)/n+z*z/(4*n*n))/(1+z*z/n)
        result['complete_prompt_decode_match']=dict(prompts=n,all_steps_match_prompts=int(np.sum(success==totals)),rate=rate,wilson_interval95=[max(0,center-half),min(1,center+half)])
        result['uncertainty_note']='Prompt bootstrap describes this sample; with zero misses it degenerates to [1,1] and is not a zero-risk certificate. Wilson interval is for whole-prompt exact-match events assuming independent prompt groups; semantic/template correlation and pretraining contamination remain unmeasured.'
    result['prompt_groups']=group_count
    return result
def main():
    import sys
    from pathlib import Path
    import run_sparse_quality_all557_20261024 as U
    from reference.quality_data import load_split,recall_report
    U.check();assert not (U.OUT/'QUALITY.json').exists()
    data=load_split(U.DATA);prior=U.read(U.PREVIOUS/'QUALITY.json');checked=[]
    for row in prior['configurations']:
        a=np.load(U.ROOT/row['coverage']);assert fast_report(a['hits'],data)==row['report'];checked.append(row['id'])
    rng=np.random.default_rng(20261024)
    for hits in [np.ones(len(data['hidden']),bool),np.zeros(len(data['hidden']),bool),rng.random(len(data['hidden']))>.05]:assert fast_report(hits,data)==recall_report(hits,data)
    entry=U.OUT/'EVALUATION_REPORT_OPTIMIZATION_ENTRY.json';assert not entry.exists()
    U.write(entry,dict(state='PASS6_PRIOR_AND3_REFERENCE_PARITY_BEFORE_EVALUATION',created=U.now(),source_sha256=U.sha(__file__),frozen_evaluator_sha256=U.sha(U.M/'scripts/run_sparse_quality_all557_20261024.py'),plan_sha256=U.sha(U.OUT/'PLAN.json'),prior6=checked,change='Only replace repeated string-group scans with once-sorted group indices and integer bincount. Masks/arrays/selectors/parameters and bootstrap seed/300 resamples/Wilson formula unchanged. Original frozen file preserved.'))
    del data
    U.recall_report=fast_report
    sys.argv=[str(Path(__file__)), '--phase','evaluate'];U.main()
if __name__=='__main__':main()
