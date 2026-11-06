"""Independent prompt/lock audit, no NumPy/GPU/labels/network/board required."""
from pathlib import Path
import hashlib,json,unicodedata
M=Path(__file__).resolve().parents[1];D=M/'data/fixed_quality_20261022'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def audit():
    meta=read(D/'MANIFEST.json');freeze=read(D/'IMPLEMENTATION_FREEZE.json');entry=read(D/'EVALUATION_ENTRY_LOCK.json')
    assert sha(D/'IMPLEMENTATION_FREEZE.json')==meta['implementation_freeze_sha256']
    assert sha(D/'holdout.jsonl')==meta['holdout_sha256']==entry['corpus_sha256']
    for lock in (freeze,entry):
        for n,h in lock['source_sha256'].items():assert sha(M/n)==h,n
    public=M/'data/public_corpus_v1';assert sha(public/'sources.lock.json')==meta['public_sources_lock_sha256']
    for e in read(public/'sources.lock.json')['files']:assert sha(public/e['local_path'])==e['sha256']
    assert sha(D/'HumanEval_sources.lock.json')==meta['humaneval_sources_lock_sha256']
    for n,e in read(D/'HumanEval_sources.lock.json')['files'].items():assert sha(D/'raw'/Path(n).name)==e['sha256']
    groups=set();prompts=set()
    for n,h in meta['prior_prompt_files_sha256'].items():
        assert sha(M/n)==h
        for r in lines(M/n):groups.add(r['group_sha256']);prompts.add(r['prompt_sha256'])
    rows=lines(D/'holdout.jsonl');newg={r['group_sha256'] for r in rows};newp={r['prompt_sha256'] for r in rows}
    assert len(rows)==len(newg)==len(newp)==len({r['id'] for r in rows})==1000
    assert not groups&newg and not prompts&newp
    actual={c:sum(r['category']==c for r in rows) for c in freeze['counts']}
    assert actual==meta['counts']==freeze['counts']
    for r in rows:
        normalized=' '.join(unicodedata.normalize('NFKC',r['prompt']).casefold().split())
        assert hashlib.sha256(normalized.encode()).hexdigest()==r['prompt_sha256']
        assert len(r['prompt'].encode())<=1536 and r['split']=='holdout'
    # Verify tied current selection parameters against the earlier frozen
    # configuration, rather than merely trusting a fresh hash of any NPZ.
    old=read(M/'reports/conservative_r2b_20261021/SELECTION_LOCK.json')
    for n,h in old['parameter_sha256'].items():assert sha(M/'reports/selector_p2_20261021'/n)==h
    assert freeze['configuration']==old['chosen']
    return dict(state='PASS_FROZEN_PROMPT_INPUTS_ONLY',groups=1000,counts=actual,
                group_overlap_with_prior=0,prompt_overlap_with_prior=0,
                maximum_prompt_utf8_bytes=max(len(r['prompt'].encode()) for r in rows),
                corpus_sha256=sha(D/'holdout.jsonl'),entry_lock_sha256=sha(D/'EVALUATION_ENTRY_LOCK.json'),
                independent_quality='NOT_RUN_NO_LABELS_COLLECTED',board='NOT_RUN',
                caveat='Conservative byte-length prefilter only; actual tokenizer/canonical-GPU-head/model identities must be checked before/every collection. Near-duplicates and pretraining contamination unknown.')
if __name__=='__main__':
    out=M/'reports/board_preparation_20261022/QUALITY_RESERVATION_AUDIT.json';assert not out.exists()
    out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(audit(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('QUALITY_RESERVATION_AUDIT=PASS_PROMPT_ONLY; QUALITY_NOT_RUN')
