"""Choose by predeclared calibration gates/bytes, then freeze before new labels."""
from pathlib import Path
import json
import run_quantization as R
def main():
    R.checked();R.stop();assert not (R.OUT/'ACTIVE.lock').exists()
    assert (R.OUT/'GPU_BENCHMARK.json').exists() and (R.OUT/'INDEPENDENT_REVIEW.json').exists()
    D=R.M/'data/final_quality_20261023';manifest=json.loads((D/'MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['final_labels_opened'] is False and (D/'TOKENIZER_PREFLIGHT.json').exists()
    assert not (R.OUT/'SELECTION_LOCK.json').exists(),'Do not reselect after final-entry freezing'
    candidates=[]
    for path in sorted((R.OUT/'points').glob('*/RESULT.json')):
        p=json.loads(path.read_text())
        if p['conservative_calibration_gate']:candidates.append(p)
    selected=[]
    if candidates:
        p=min(candidates,key=lambda p:(p['packed_bytes']+(896*4 if p['transform'] else 0),p['id']))
        selected.append(dict(id='DIRECT_'+p['id'],kind='direct',source=p['id'],packed_sha256=p['packed_sha256'],
          channel_scale_sha256=None if p['transform'] is None else p['transform']['sha256'],main_read_bytes=p['packed_bytes']-256))
    refine=json.loads((R.OUT/'REFINE_CALIBRATION.json').read_text())
    viable=[p for p in refine['configurations'] if p['conservative_calibration_gate'] and p['K']<151936]
    if viable:
        p=min(viable,key=lambda p:(p['main_read_bytes'],p['preview'],p['K']))
        point=json.loads((R.OUT/'points'/p['preview']/'RESULT.json').read_text())
        selected.append(dict(id='REFINE_'+p['preview']+'_K'+str(p['K']),kind='refine',source=p['preview'],K=p['K'],
          packed_sha256=point['packed_sha256'],main_read_bytes=p['main_read_bytes']))
    assert selected,'No conservative calibration candidate; do not open final labels'
    selection=dict(state='LOCKED_BEFORE_NEW_LABELS',created=R.now(),selected=selected,
      selection_rule='Complete calibration zero errors/misses plus >=99.9% each decode category; minimum actual packed+transform bytes for direct; minimum preview+BF16_K row bytes for refine; lexical ID tie-break. GPU rate does not change selection.',
      canonical_weight_sha256=R.sha(R.WEIGHT),plan_sha256=R.sha(R.OUT/'PLAN.json'),
      calibration_result_sha256={n:R.sha(R.OUT/n) for n in ['RTN_CALIBRATION.json','METHODS_CALIBRATION.json','REFINE_CALIBRATION.json','GPU_BENCHMARK.json','INDEPENDENT_REVIEW.json']},
      corpus_sha256=manifest['corpus_sha256'],final_labels_opened=False,board='NOT_RUN')
    R.write(R.OUT/'SELECTION_LOCK.json',selection)
    sources=R.source_files()+[Path(__file__),R.M/'scripts/collect_final.py',R.M/'scripts/evaluate_final.py',R.M/'reference/packed_cuda.py']
    entry=dict(created=R.now(),selection_lock_sha256=R.sha(R.OUT/'SELECTION_LOCK.json'),
      corpus_sha256=manifest['corpus_sha256'],reservation_manifest_sha256=R.sha(D/'MANIFEST.json'),
      tokenizer_preflight_sha256=R.sha(D/'TOKENIZER_PREFLIGHT.json'),
      sources={p.relative_to(R.ROOT).as_posix():R.sha(p) for p in sources},
      final_protocol=dict(prompts=1000,max_new_tokens=16,max_input_tokens=2048,penalty=1.1,
        gates='overall and every category decode agreement/recall >=0.999; no retune on opened group',
        code_source='DS-1000 prompt only; original perturbation family collapsed; reference code never executed'),
      final_labels_opened=False)
    R.write(D/'EVALUATION_ENTRY_LOCK.json',entry);print(json.dumps(selection,ensure_ascii=False))
if __name__=='__main__':main()
