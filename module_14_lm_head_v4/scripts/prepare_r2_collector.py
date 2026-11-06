"""Create isolated collector revision with explicit, auditable path/I-O changes."""
from pathlib import Path
import argparse,hashlib,json
M=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--revision',choices=['r2','r2b'],default='r2');args=ap.parse_args();revision=args.revision
    original=M/'scripts/collect_hidden.py';assert sha(original)=='5de4546c9ba936ba49cb81d641fad212ec3aa02dc92086d52a9e2f3b1652fc26'
    text=original.read_text(encoding='utf-8')
    changes={"default=M/'data/hidden_v1'":f"default=M/'data/hidden_{revision}_20261021'",
        "corpus=M/'data/public_corpus_v1'/(a.split+'.jsonl')":f"corpus=M/'data/fresh_holdout_{revision}_20261021'/(a.split+'.jsonl')",
        "if __name__=='__main__':main()":"# Reuse bounded atomic-I/O only; numerical collection function is unchanged.\nfrom collect_hidden_resumable import atomic_write as write\nif __name__=='__main__':main()"}
    for before,after in changes.items():assert text.count(before)==1;text=text.replace(before,after)
    target=M/f'scripts/collect_hidden_{revision}.py'
    if target.exists():assert target.read_text(encoding='utf-8')==text
    else:target.write_text(text,encoding='utf-8')
    report=dict(original_sha256=sha(original),r2_sha256=sha(target),atomic_io_sha256=sha(M/'scripts/collect_hidden_resumable.py'),changes=changes,
        scope='Only corpus/default-output path and bounded JSON writer changed; distinct truthful collector SHA, no mixing old settings/NPZ.')
    (M/f'data/fresh_holdout_{revision}_20261021/COLLECTOR_DERIVATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('R2_COLLECTOR_DERIVATION=PASS')
if __name__=='__main__':main()
