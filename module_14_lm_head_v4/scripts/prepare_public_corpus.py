"""Download pinned public prompt sources; split complete prompt groups reproducibly.

Never executes dataset scripts, generated code, pickle, or archive members.
Answers are excluded from prompts. This prepares text only, not hidden labels.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,hashlib,io,json,re,unicodedata,urllib.request,zipfile

M=Path(__file__).resolve().parents[1];D=M/'data/public_corpus_v1';RAW=D/'raw'
SOURCES={
 'dolly':dict(kind='github',repo='databrickslabs/dolly',revision='5f9bfba300181fb35854d64c8bf1180ea75105f7',files=['data/databricks-dolly-15k.jsonl','README.md','LICENSE'],
    page='https://github.com/databrickslabs/dolly',license='CC-BY-SA-3.0 dataset; historical author-repository copy before move to HF, not claimed identical to current HF revision'),
 'cmmlu':dict(kind='archive',repo='haonan-li/CMMLU',revision='d6e7b716d8ac694f38969a6c0407437d1fded799',files=['cmmlu.zip'],
    page='https://github.com/haonan-li/CMMLU',license='See pinned author README; do not infer a dataset license from code license'),
 'gsm8k':dict(kind='github',repo='openai/grade-school-math',files=['grade_school_math/data/train.jsonl','grade_school_math/data/test.jsonl','README.md','LICENSE'],
    page='https://github.com/openai/grade-school-math',license='See pinned LICENSE'),
 'mbpp':dict(kind='github',repo='google-research/google-research',files=['mbpp/mbpp.jsonl','mbpp/README.md','LICENSE'],
    page='https://github.com/google-research/google-research/tree/master/mbpp',license='See pinned dataset README and repository LICENSE; preserve both'),
}
def digest(b):return hashlib.sha256(b).hexdigest()
def fetch(url):
    headers={'User-Agent':'LLM-FPGA-v4-corpus/1.0'}
    if '/contents/' in url:headers['Accept']='application/vnd.github.raw+json'
    request=urllib.request.Request(url,headers=headers)
    # Windows system proxy currently fails TLS; use an explicit direct opener.
    # Does not change OS settings or disable certificate verification.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request,timeout=45) as response:
        b=response.read(25*1024*1024+1)
        if len(b)>25*1024*1024:raise ValueError('Source exceeds 25MiB bound')
        return b
def raw_path(source,name):return RAW/source/Path(name).name
def get_sources(verify_only):
    lock=D/'sources.lock.json'
    if lock.exists():
        meta=json.loads(lock.read_text(encoding='utf-8'))
    else:
        if verify_only:raise FileNotFoundError('No source lock yet')
        RAW.mkdir(parents=True,exist_ok=True);entries=[];revisions={}
        for source,spec in SOURCES.items():
            rev=spec.get('revision')
            if rev is None:rev=json.loads(fetch(f"https://api.github.com/repos/{spec['repo']}/commits/master"))['sha']
            assert re.fullmatch('[0-9a-f]{40}',rev);revisions[source]=rev
            for filename in spec['files']:
                url=(f"https://codeload.github.com/{spec['repo']}/zip/{rev}" if spec['kind']=='archive'
                     else f"https://api.github.com/repos/{spec['repo']}/contents/{filename}?ref={rev}")
                entries.append(dict(source=source,revision=rev,url=url,sha256=None,bytes=None,
                    local_path=raw_path(source,filename).relative_to(D).as_posix(),license=spec['license'],official_page=spec['page']))
        meta=dict(state='FETCHING',format='M14_V4_PUBLIC_SOURCES_V1',fetched_at_utc=datetime.now(timezone.utc).isoformat(),revisions=revisions,files=entries)
    def save():
        temp=lock.with_suffix('.tmp');temp.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(lock)
    for entry in meta['files']:
        p=D/entry['local_path']
        if entry['sha256'] and p.exists():
            if digest(p.read_bytes())!=entry['sha256']:raise ValueError('Source hash mismatch: '+str(p))
            continue
        if verify_only:raise ValueError('Incomplete corpus download: '+str(p))
        save();b=fetch(entry['url']);p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and p.read_bytes()!=b:raise ValueError('Preserve existing different raw source: '+str(p))
        if entry['sha256'] and digest(b)!=entry['sha256']:raise ValueError('Redownload hash mismatch')
        p.write_bytes(b);entry.update(sha256=digest(b),bytes=len(b));save()
        print('SOURCE_LOCKED '+entry['source']+' '+p.name+' '+digest(b),flush=True)
    meta['state']='COMPLETE';save();return meta
def normalize(s):return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())
def bucket(group):return int(digest(('m14-v4-v1:'+group).encode())[:8],16)%100
def jsonlines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def build():
    rows=[]
    def add(source,source_id,category,prompt,group,split):
        prompt=prompt.strip();group_hash=digest(normalize(group).encode());prompt_hash=digest(normalize(prompt).encode())
        if not prompt or len(prompt)>12000:return
        rows.append(dict(id=source+':'+str(source_id),source=source,source_id=str(source_id),category=category,
            split=split,prompt=prompt,prompt_sha256=prompt_hash,group_sha256=group_hash))
    for i,row in enumerate(jsonlines(raw_path('dolly','databricks-dolly-15k.jsonl'))):
        instruction=row['instruction'].strip();b=bucket(normalize(instruction));split='train' if b<70 else 'calibration' if b<85 else 'holdout'
        prompt=instruction+('\n\nContext:\n'+row['context'].strip() if row['context'].strip() else '')
        add('dolly',i,'english',prompt,instruction,split)
    for original in ('train','test'):
        for i,row in enumerate(jsonlines(raw_path('gsm8k',original+'.jsonl'))):
            question=row['question'];split='holdout' if original=='test' else 'calibration' if bucket(normalize(question))<20 else 'train'
            add('gsm8k',original+':'+str(i),'math',question,question,split)
    for row in jsonlines(raw_path('mbpp','mbpp.jsonl')):
        task=int(row['task_id'])
        if task<=10:continue # original few-shot examples never used as training
        split='holdout' if task<=510 else 'calibration' if task<=600 else 'train'
        prompt='Write a Python function for the following task.\n'+row['text'].strip()
        add('mbpp',task,'code',prompt,row['text'],split)
    with zipfile.ZipFile(raw_path('cmmlu','cmmlu.zip')) as z:
        for name in sorted(z.namelist()):
            if not name.endswith('.csv') or '__MACOSX' in name:continue
            original=Path(name).parent.name
            if original not in ('dev','test'):continue
            for index,original_row in enumerate(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig')))):
                row={k.lower() if k not in 'ABCD' else k:v for k,v in original_row.items()}
                split='train' if original=='dev' else 'calibration' if bucket(normalize(row['question']))<20 else 'holdout'
                prompt=row['question'].strip()+'\n'+'\n'.join(k+'. '+row[k].strip() for k in 'ABCD')+'\n请给出答案并简要说明理由。'
                add('cmmlu',name+':'+str(index),'chinese',prompt,row['question'],split)
    # Holdout wins if identical questions appear across official partitions.
    rows.sort(key=lambda r:({'holdout':0,'calibration':1,'train':2}[r['split']],r['id']))
    groups={};prompts=set();clean=[];dropped=0
    for row in rows:
        g=row['group_sha256']
        if (g in groups and groups[g]!=row['split']) or row['prompt_sha256'] in prompts:dropped+=1;continue
        groups[g]=row['split'];prompts.add(row['prompt_sha256']);clean.append(row)
    selected=[];counts={}
    for category in ('chinese','english','code','math'):
        for split,limit in [('train',400),('calibration',80),('holdout',250)]:
            pool=[r for r in clean if r['category']==category and r['split']==split]
            pool.sort(key=lambda r:digest(('sample:'+r['id']).encode()))
            if split=='holdout':
                unique_groups=set();independent=[]
                for row in pool:
                    if row['group_sha256'] not in unique_groups:
                        independent.append(row);unique_groups.add(row['group_sha256'])
                pool=independent
            chosen=pool[:limit]
            if split=='holdout' and len(chosen)<250:raise ValueError('Insufficient holdout '+category)
            selected+=chosen;counts[category+':'+split]=len(chosen)
    # Recheck after sampling: zero exact normalized-prompt/group overlap by split.
    for key in ('group_sha256','prompt_sha256'):
        owned={}
        for row in selected:
            if row[key] in owned and owned[row[key]]!=row['split']:raise ValueError('Split leakage')
            owned[row[key]]=row['split']
    files={}
    for split in ('train','calibration','holdout'):
        p=D/(split+'.jsonl');content=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in selected if r['split']==split)
        if p.exists() and p.read_text(encoding='utf-8')!=content:raise ValueError('Refuse to replace changed corpus split')
        p.write_text(content,encoding='utf-8');files[p.name]=dict(sha256=digest(p.read_bytes()),records=content.count('\n'))
    result=dict(state='PASS',format='M14_V4_PROMPT_CORPUS_V1',sources_lock_sha256=digest((D/'sources.lock.json').read_bytes()),
        counts=counts,files=files,excluded_duplicate_or_cross_split_rows=dropped,split_unit='Complete prompt/question group; normalized NFKC/casefold whitespace; no adjacent-token split',
        sampling='SHA256 deterministic ordering with m14-v4-v1 and sample namespaces; holdout uses at most one record per normalized question group',
        near_duplicate_check='NOT_DONE: only exact normalized prompt/question grouping; semantic/template leakage remains possible',
        model_pretraining_contamination='UNKNOWN',hidden_states='NOT_COLLECTED',holdout_steps='NOT_COLLECTED',
        coverage_limit='Initial Chinese exam / English instruction / Python code / math corpus; rare names, long-context and penalty stress need additional explicit suites')
    (D/'MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PUBLIC_CORPUS=PASS '+json.dumps(counts),flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--verify-only',action='store_true');args=a.parse_args()
    get_sources(args.verify_only);build()
