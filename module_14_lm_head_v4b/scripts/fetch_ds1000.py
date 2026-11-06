"""Pin official DS-1000 raw public data. Never executes downloaded code."""
from pathlib import Path
import hashlib,json,urllib.request
M=Path(__file__).resolve().parents[1];D=M/'data/final_quality_20261023/raw/ds1000'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'M14-v4b-research/1.0'})
    with urllib.request.urlopen(req,timeout=90) as r:return r.read()
def main():
    D.mkdir(parents=True,exist_ok=True);lock=D/'SOURCE_LOCK.json'
    if lock.exists():
        meta=json.loads(lock.read_text())
        for e in meta['files']:assert hashlib.sha256((D/e['local']).read_bytes()).hexdigest()==e['sha256']
        print('DS1000_SOURCE_ALREADY_PINNED');return
    commit=get('https://api.github.com/repos/xlang-ai/DS-1000/commits/main');revision=json.loads(commit)['sha']
    (D/'commit.json').write_bytes(commit);files=[]
    for name in ['data/ds1000.jsonl.gz','README.md','LICENSE']:
        url=f'https://raw.githubusercontent.com/xlang-ai/DS-1000/{revision}/{name}';raw=get(url);target=D/Path(name).name
        if target.exists():assert target.read_bytes()==raw,'Preserve differing previous source'
        else:target.write_bytes(raw)
        files.append(dict(path=name,local=target.name,url=url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    meta=dict(repository='https://github.com/xlang-ai/DS-1000',revision=revision,files=files,
      scope='Public source, prompt-only reservation. code_context/reference_code never run or supplied as prompt.',
      license='CC-BY-SA-4.0 per pinned author LICENSE; local research source retained with attribution')
    lock.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('DS1000_SOURCE_PINNED',revision)
if __name__=='__main__':main()
