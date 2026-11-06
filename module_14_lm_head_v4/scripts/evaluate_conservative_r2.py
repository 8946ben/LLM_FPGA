"""Predeclare conservative configuration, then evaluate fresh test once."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,sys
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split,assert_group_disjoint,recall_report
spec=importlib.util.spec_from_file_location('_base',M/'scripts/evaluate_selectors.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evaluate',action='store_true');ap.add_argument('--revision',choices=['r2b'],default='r2b');args=ap.parse_args();revision=args.revision
    original=M/'reports/selector_p2_20261021';prior=M/'reports/selector_hybrid_p2_20261021';out=M/f'reports/conservative_{revision}_20261021';out.mkdir(parents=True,exist_ok=True)
    # Quality-first, fixed largest tested budget; not chosen using this fresh test.
    chosen='route4_K16384_UNION_lr128_K16384';cal=read(prior/'CALIBRATION.json');row=next(r for r in cal['configurations'] if r['name']==chosen)
    assert row['calibration']['decode']['misses']==0 and row['preliminary_quality_gate']
    corpus=M/f'data/fresh_holdout_{revision}_20261021';manifest=read(corpus/'MANIFEST.json')
    assert base.sha(corpus/'holdout.jsonl')==manifest['holdout_sha256']
    parameters=read(original/'PARAMETERS.json')
    identity=dict(chosen=chosen,config=row['config'],prior_calibration_sha256=base.sha(prior/'CALIBRATION.json'),
        parameter_sha256={n:parameters[n] for n in ('route_r128.npz','lowrank_r128.npz')},fresh_corpus_sha256=manifest['holdout_sha256'],
        evaluator_sha256=base.sha(Path(__file__)),base_evaluator_sha256=base.sha(M/'scripts/evaluate_selectors.py'),quality_data_sha256=base.sha(M/'reference/quality_data.py'),
        decision='Conservative fixed maximum existing calibration-tested routing/rank/K budget; original calibration zero decode misses. No new test labels read to choose it.',
        gate='Point recall>=99.9% overall and each category; >=1000 independent groups and >=10000 decode steps; proposed screening gate only.')
    lock=out/'SELECTION_LOCK.json'
    if lock.exists():
        saved=read(lock);assert {k:v for k,v in saved.items() if k!='locked_at_utc'}==identity
    else:base.write(lock,dict(identity,locked_at_utc=datetime.now(timezone.utc).isoformat()))
    if not args.evaluate:print('R2_SELECTION_FROZEN='+chosen,flush=True);return
    if (out/'HOLDOUT.json').exists():raise ValueError('Do not repeatedly evaluate or tune on opened fresh holdout')
    train=load_split(M/'data/hidden_v1/train');caldata=load_split(M/'data/hidden_v1/calibration')
    test=load_split(M/f'data/hidden_{revision}_20261021/holdout');assert_group_disjoint(train,caldata,test)
    prior_groups={json.loads(s)['group_sha256'] for s in (M/'data/public_corpus_v1/holdout.jsonl').read_text(encoding='utf-8').splitlines()}
    assert not prior_groups.intersection(test['groups']) and test['manifest']['excluded_prompts']==0
    before=train['manifest']['settings'];after=test['manifest']['settings']
    assert {k:v for k,v in before.items() if k not in ('corpus_sha256','collector_sha256')}=={k:v for k,v in after.items() if k not in ('corpus_sha256','collector_sha256')}
    derivation=read(corpus/'COLLECTOR_DERIVATION.json');assert after['collector_sha256']==base.sha(M/f'scripts/collect_hidden_{revision}.py')==derivation['r2_sha256']
    expected=(M/'scripts/collect_hidden.py').read_text(encoding='utf-8')
    for a,b in derivation['changes'].items():assert expected.count(a)==1;expected=expected.replace(a,b)
    assert (M/f'scripts/collect_hidden_{revision}.py').read_text(encoding='utf-8')==expected
    models={}
    for name,digest in identity['parameter_sha256'].items():
        p=original/name;assert base.sha(p)==digest
        with np.load(p,allow_pickle=False) as z:models[name]={k:z[k].copy() for k in z.files}
    c=row['config'];router=models['route_r128.npz'];low=models['lowrank_r128.npz'];required=base.mandatory_ids()
    hits,counts,fallback=base.route_eval(router,test,c['route_count'],c['route_k'],required)
    ranks=base.lowrank_eval(low['a_bf16'],low['b_bf16'],test,required);hits|=ranks<c['lowrank_k'];counts=np.minimum(151936,counts+c['lowrank_k'])
    q=recall_report(hits,test);scale=q['prompt_groups']>=1000 and q['decode']['steps']>=10000
    state='P2_RECALL_PASS' if scale and base.preliminary_gate(q) else 'QUALITY_FAIL'
    base.write(out/'HOLDOUT.json',dict(state=state,chosen=chosen,report=q,minimum_scale_met=scale,
        candidates=base.describe_counts(counts[test['decode']],2*128*896+2*128*(896+151936)),candidate_count_note='Conservative union upper bound; actual overlap not materialized',
        explicit_fallback_steps=fallback,selection_lock_sha256=base.sha(lock),holdout_manifest_sha256=test['manifest_sha256'],corpus_manifest_sha256=base.sha(corpus/'MANIFEST.json'),
        scope='Fresh groups, dense-trajectory recall only; not lossless guarantee, free-generation quality, release acceptance or FPGA timing.'))
    print('R2_FRESH_HOLDOUT='+state,flush=True)
if __name__=='__main__':main()
