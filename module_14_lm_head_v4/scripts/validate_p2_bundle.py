"""Read-only provenance and phase audit after the locked holdout experiment."""
from pathlib import Path
import hashlib,json,sys
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split,assert_group_disjoint,assert_compatible_collections

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    base=M/'reports/selector_p2_20261021';out=M/'reports/selector_hybrid_p2_20261021'
    splits=[load_split(M/'data/hidden_v1'/name) for name in ('train','calibration','holdout')]
    assert_group_disjoint(*splits);assert_compatible_collections(*splits)
    train,cal,test=splits;assert [x['manifest']['prompts'] for x in splits]==[1500,320,1000]
    corpus=M/'data/public_corpus_v1';corpus_manifest=read(corpus/'MANIFEST.json')
    assert sha(corpus/'sources.lock.json')==corpus_manifest['sources_lock_sha256']
    for data in splits:
        split=data['manifest']['split'];entry=corpus_manifest['files'][split+'.jsonl']
        assert sha(corpus/(split+'.jsonl'))==entry['sha256']==data['manifest']['settings']['corpus_sha256']
        counts={category:sum(r.get('category')==category and 'excluded' not in r for r in data['manifest']['records']) for category in ('chinese','english','code','math')}
        assert all(counts[c]==corpus_manifest['counts'][c+':'+split] for c in counts)
    original=read(base/'EXPERIMENT.lock.json');hybrid=read(out/'EXPERIMENT.lock.json')
    for key,rel in [('evaluator_sha256','scripts/evaluate_selectors.py'),('router_sha256','reference/routing.py'),('quality_data_sha256','reference/quality_data.py')]:assert sha(M/rel)==original[key]
    assert sha(M/'scripts/evaluate_hybrid_selectors.py')==hybrid['evaluator_sha256']
    assert sha(base/'EXPERIMENT.lock.json')==hybrid['base_experiment_lock_sha256']
    assert sha(base/'PARAMETERS.json')==hybrid['base_parameter_manifest_sha256']
    for name,expected in read(base/'PARAMETERS.json').items():assert sha(base/name)==expected
    calibration=read(out/'CALIBRATION.json');lock=read(out/'SELECTION_LOCK.json');holdout=read(out/'HOLDOUT.json');online=read(out/'ONLINE_CALIBRATION_AUDIT.json')
    assert calibration['train_manifest_sha256']==train['manifest_sha256'] and calibration['calibration_manifest_sha256']==cal['manifest_sha256']
    assert lock['calibration_sha256']==sha(out/'CALIBRATION.json')
    assert holdout['selection_lock_sha256']==online['selection_lock_sha256']==sha(out/'SELECTION_LOCK.json')
    assert lock['chosen']==holdout['chosen']==online['chosen']==calibration['chosen_calibration_configuration']
    assert holdout['holdout_manifest_sha256']==test['manifest_sha256']
    assert sha(M/'reference/hybrid_selector.py')==online['online_source_sha256']
    assert sha(M/'scripts/audit_online_selector.py')==online['audit_source_sha256']
    for data in splits:
        settings=data['manifest']['settings']
        assert sha(M/'scripts/collect_hidden.py')==settings['collector_sha256']
        assert sha(M/'reference/gpu_exact_head.py')==settings['gpu_head_sha256']
        assert sha(M/'data/model/MODEL.lock.json')==settings['model_lock_sha256']
    assert sha(M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin')==train['manifest']['settings']['canonical_weight_sha256']
    report=dict(provenance_state='PASS',quality_state=holdout['state'],chosen=holdout['chosen'],
        split_summary=[dict(split=d['manifest']['split'],prompts=d['manifest']['prompts'],predictions=len(d['winner']),decode=int(d['decode'].sum()),manifest_sha256=d['manifest_sha256']) for d in splits],
        source_hashes={str(p.relative_to(M)).replace('\\','/'):sha(p) for folder in ['scripts','reference','tests'] for p in (M/folder).glob('*.py')},
        checked='All collected NPZ SHAs/schema/settings; cross-split exact group isolation; fitted parameters; frozen selection and unchanged evaluators; collected/model source identities.',
        limits='Provenance PASS is distinct from quality gate, release acceptance, full generation, HLS/FPGA or timing verification. Semantic duplicates/pretraining contamination unmeasured.',hardware_access='NONE')
    (M/'reports/P2_BUNDLE_VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('P2_BUNDLE_PROVENANCE=PASS QUALITY='+holdout['state'])
if __name__=='__main__':main()
