"""Freeze selected numerical implementation and final-test entry after Csim."""
from pathlib import Path
import hashlib,json
M=Path(__file__).resolve().parents[1];R=M/'reports/fusion_exp10_20261023_r1';D=M/'data/fusion10_quality_20261023';X=M/'experiments/fusion_exp10_20261023'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not (D/'EVALUATION_ENTRY_LOCK.json').exists(),'Never replace a final-test entry lock'
    assert not (M/'data/hidden_fusion10_20261023/holdout/MANIFEST.json').exists(),'No pre-freeze test labels'
    hls=read(R/'HLS_CSIM.json');assert hls['stage']=='EXP10_HLS_PHASE_COMPLETE' and hls['mode']=='csim'
    text=(R/f'hls_{hls["run"]}.log').read_text(encoding='utf-8',errors='replace');assert 'M14_V4_SELECTOR_CSIM=PASS valid=7 preflight_invalid=24 stage_errors=5 rtl_subset=0' in text,'Require genuine5 real(A-B-A) plus2 valid descriptor,24 rejection,5 child-error Csim'
    manifest=read(X/'MANIFEST.json');selection=read(R/'SELECTION_LOCK.json');assert manifest['parameters']==selection['parameters']
    for n,h in manifest['source_sha256'].items():assert sha(X/n)==h,n
    for n,h in manifest['fixture_sha256'].items():assert sha(X/'fixture'/n)==h,n
    reservation=read(D/'MANIFEST.json');preflight=read(D/'TOKENIZER_PREFLIGHT.json');assert preflight['state']=='PASS1000_TOKENIZER_LENGTH_IDENTITY_NO_LABELS' and preflight['corpus_sha256']==reservation['corpus_sha256']==sha(D/'holdout.jsonl')
    names=['scripts/collect_hidden_fusion10_20261023.py','scripts/evaluate_fusion10_final_20261023.py','scripts/fusion_experiment10_20261023.py','reference/hyperparameter_study.py','reference/numeric_contract.py','reference/candidate_head.py','reference/gpu_exact_head.py','reference/quality_data.py','data/model/MODEL.lock.json','experiments/fusion_exp10_20261023/MANIFEST.json','experiments/fusion_exp10_20261023/hls_selector.tcl']
    names += ['experiments/fusion_exp10_20261023/'+n for n in manifest['source_sha256']]
    entry=dict(state='FROZEN_BEFORE_NEW_DENSE_TRAJECTORIES',selection_lock_sha256=sha(R/'SELECTION_LOCK.json'),corpus_sha256=sha(D/'holdout.jsonl'),reservation_sha256=sha(D/'MANIFEST.json'),source_sha256={n:sha(M/n) for n in names},hardware_csim_log_sha256=sha(R/f'hls_{hls["run"]}.log'),parameters=selection['parameters'],registered_evaluations=['selected','frozen_baseline'],gate=dict(groups=1000,minimum_decode=10000,overall=.999,each_category=.999,exclusions=0),policy='One final evaluation after lock; preserve quality failures, never tune this cohort. Same-new-cohort baseline predeclared. No board/RTL/general lossless claim.')
    with (D/'EVALUATION_ENTRY_LOCK.json').open('x',encoding='utf-8') as f:json.dump(entry,f,ensure_ascii=False,indent=2);f.write('\n')
    print(entry['state'])
if __name__=='__main__':main()
