"""Assemble local model using existing weights and author-published sidecars.

Uses the Qwen author repository on ModelScope, pins every file revision/SHA.
No executable Python model files are downloaded. No global environment changes.
"""
from pathlib import Path
import hashlib,json,shutil,urllib.parse,urllib.request
M=Path(__file__).resolve().parents[1];ROOT=M.parent;OUT=M/'data/model'
BASE='https://modelscope.cn/api/v1/models/Qwen/Qwen2.5-0.5B-Instruct/repo'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def fetch(url):
    op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with op.open(urllib.request.Request(url,headers={'User-Agent':'M14-v4'}),timeout=45) as r:
        b=r.read(10*1024*1024+1)
        if len(b)>10*1024*1024:raise ValueError('Only small model sidecar downloads allowed')
        return b
def main():
    OUT.mkdir(parents=True,exist_ok=True);lock=OUT/'MODEL.lock.json'
    if lock.exists():
        info=json.loads(lock.read_text(encoding='utf-8'))
    else:
        files=json.loads(fetch(BASE+'/files?Revision=master&Recursive=true'))['Data']['Files']
        selected={'config.json','generation_config.json','tokenizer.json','tokenizer_config.json','vocab.json','merges.txt','LICENSE','README.md','model.safetensors'}
        info=dict(format='M14_V4_QWEN_MODEL_LOCK_V1',official_page='https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct',
            files=[dict(name=f['Path'],revision=f['Revision'],sha256=f['Sha256'],bytes=f['Size']) for f in files if f['Path'] in selected])
        assert {f['name'] for f in info['files']}==selected
        lock.write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    for f in info['files']:
        p=OUT/f['name']
        if f['name']=='model.safetensors':
            source=ROOT/'artifacts/Qwen2.5-0.5B-Instruct/model.safetensors'
            assert sha(source)==f['sha256'],'Existing full model differs from author revision'
            if not p.exists() or p.samefile(source):
                # Keep the experiment copy independent from accepted source assets.
                # Atomic replacement detaches any earlier read-only hardlink.
                temp=p.with_suffix('.copying')
                shutil.copyfile(source,temp)
                assert sha(temp)==f['sha256']
                temp.replace(p)
        elif not p.exists():
            url=BASE+'?'+urllib.parse.urlencode(dict(Revision=f['revision'],FilePath=f['name']))
            b=fetch(url);assert hashlib.sha256(b).hexdigest()==f['sha256'];p.write_bytes(b)
        assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],p
        print('MODEL_FILE_PASS '+f['name'],flush=True)
    config=json.loads((OUT/'config.json').read_text())
    assert config['hidden_size']==896 and config['vocab_size']==151936 and config['tie_word_embeddings']
    print('V4_LOCAL_MODEL=PASS',flush=True)
if __name__=='__main__':main()
