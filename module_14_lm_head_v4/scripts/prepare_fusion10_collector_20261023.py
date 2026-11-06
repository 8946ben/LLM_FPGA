"""Derive path-only collector revision with selection/entry guards."""
from pathlib import Path
import hashlib,json
M=Path(__file__).resolve().parents[1];D=M/'data/fusion10_quality_20261023'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=M/'scripts/collect_hidden_fixed_20261022.py';old_settings=json.loads((M/'data/hidden_fixed_20261022/holdout/SETTINGS.json').read_text(encoding='utf-8'));assert sha(source)==old_settings['collector_sha256']
    text=source.read_text(encoding='utf-8');changes={"default=M/'data/hidden_fixed_20261022'":"default=M/'data/hidden_fusion10_20261023'","corpus=M/'data/fixed_quality_20261022'/(a.split+'.jsonl')":"corpus=M/'data/fusion10_quality_20261023'/(a.split+'.jsonl')"}
    for a,b in changes.items():assert text.count(a)==1;text=text.replace(a,b)
    guard='''    # Fail closed before any new labels unless selection and numerical entry are frozen.
    entry=json.loads((M/'data/fusion10_quality_20261023/EVALUATION_ENTRY_LOCK.json').read_text(encoding='utf-8'))
    selected=M/'reports/fusion_exp10_20261023_r1/SELECTION_LOCK.json'
    assert sha(selected)==entry['selection_lock_sha256']
    for relative,expected in entry['source_sha256'].items():assert sha(M/relative)==expected,relative
    assert sha(M/'data/fusion10_quality_20261023/holdout.jsonl')==entry['corpus_sha256']
'''
    needle='    head=GpuExactHead(weight);validate(head,a.out/\'GPU_HEAD_VALIDATION.json\')';assert text.count(needle)==1;text=text.replace(needle,guard+needle)
    target=M/'scripts/collect_hidden_fusion10_20261023.py';assert not target.exists();target.write_text(text,encoding='utf-8');report=dict(state='DERIVED_PATHS_AND_PRE_LABEL_GUARDS_ONLY',old_sha256=sha(source),new_sha256=sha(target),changes=changes,guard=guard,arithmetic='Canonical head,transformer,tokenizer/history and generation logic unchanged')
    (D/'COLLECTOR_DERIVATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(report['state'])
if __name__=='__main__':main()
