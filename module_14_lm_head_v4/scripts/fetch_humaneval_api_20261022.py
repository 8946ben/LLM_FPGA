"""Bounded official GitHub contents fallback for the already-pinned revision."""
from pathlib import Path
import base64,gzip,hashlib,importlib.util,json
M=Path(__file__).resolve().parents[1];D=M/'data/fixed_quality_20261022'
spec=importlib.util.spec_from_file_location('public_source',M/'scripts/prepare_public_corpus.py')
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
lock=D/'HumanEval_sources.lock.json';meta=json.loads(lock.read_text());rev=meta['revision']
assert len(rev)==40 and set(rev)<=set('0123456789abcdef')
for n in ('data/HumanEval.jsonl.gz','LICENSE','README.md'):
    p=D/'raw'/Path(n).name;p.parent.mkdir(exist_ok=True)
    if n in meta['files']:
        assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['files'][n]['sha256'];continue
    url=f'https://api.github.com/repos/openai/human-eval/contents/{n}?ref={rev}'
    b=src.fetch(url)
    if b.lstrip().startswith(b'{'):
        envelope=json.loads(b)
        if envelope.get('encoding')=='base64':
            b=base64.b64decode(envelope['content']);assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==envelope['sha']
    if n.endswith('.gz'):
        data=gzip.decompress(b);assert len(data)<5*1024*1024
        rows=[json.loads(s) for s in data.decode('utf-8').splitlines() if s.strip()]
        assert len(rows)==164 and len({r['task_id'] for r in rows})==164 and all(isinstance(r['prompt'],str) for r in rows)
    if n=='LICENSE':assert b'MIT License' in b
    if p.exists():assert p.read_bytes()==b
    else:p.write_bytes(b)
    meta['files'][n]=dict(url=url,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
    temp=lock.with_suffix('.tmp');temp.write_text(json.dumps(meta,indent=2)+'\n');temp.replace(lock)
    print('HUMANEVAL_PINNED_FILE '+n+' '+meta['files'][n]['sha256'],flush=True)
print('HUMANEVAL_SOURCES=PASS_PINNED_DATA_ONLY_NO_CODE_EXECUTION')
