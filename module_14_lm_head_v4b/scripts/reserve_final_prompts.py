"""Reserve new whole question groups without reading any model outcomes."""
from pathlib import Path
import csv,gzip,hashlib,io,json,re,unicodedata,zipfile
M=Path(__file__).resolve().parents[1];ROOT=M.parent;V4=ROOT/'module_14_lm_head_v4';D=M/'data/final_quality_20261023';BASE=V4/'data/public_corpus_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def normalize(s):return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def grams(s):
    words=re.findall(r'\w+',normalize(s));return set(zip(words,words[1:],words[2:]))
def main():
    D.mkdir(parents=True,exist_ok=True);assert not (D/'MANIFEST.json').exists(),'Never resample a reserved group'
    public=json.loads((BASE/'sources.lock.json').read_text(encoding='utf-8'))
    for e in public['files']:assert sha(BASE/e['local_path'])==e['sha256']
    dsdir=D/'raw/ds1000';dslock=json.loads((dsdir/'SOURCE_LOCK.json').read_text())
    for e in dslock['files']:assert sha(dsdir/e['local'])==e['sha256']
    prior=sorted(set(list(BASE.glob('*.jsonl'))+list((BASE/'snapshots').glob('*.jsonl'))+list(V4.glob('data/*/holdout.jsonl'))))
    used_g=set();used_p=set();old_code=[];prior_sha={}
    for path in prior:
        prior_sha[path.relative_to(ROOT).as_posix()]=sha(path)
        for row in lines(path):
            used_g.add(row['group_sha256']);used_p.add(row['prompt_sha256'])
            if row['category']=='code':old_code.append(grams(row['prompt']))
    pool=[];near_rejected=0
    def add(source,sid,cat,prompt,group,extra=None):
        prompt=prompt.strip();g=digest(normalize(group));p=digest(normalize(prompt))
        if not prompt or len(prompt.encode())>1536 or g in used_g or p in used_p:return
        row=dict(id=f'{source}:{sid}',source=source,source_id=str(sid),category=cat,split='holdout',prompt=prompt,group_sha256=g,prompt_sha256=p)
        if extra:row.update(extra)
        pool.append(row)
    for i,r in enumerate(lines(BASE/'raw/dolly/databricks-dolly-15k.jsonl')):
        add('dolly',i,'english',r['instruction']+('\n\nContext:\n'+r['context'].strip() if r['context'].strip() else ''),r['instruction'])
    for split in ['test','train']:
        for i,r in enumerate(lines(BASE/f'raw/gsm8k/{split}.jsonl')):add('gsm8k',f'{split}:{i}','math',r['question'],r['question'])
    with zipfile.ZipFile(BASE/'raw/cmmlu/cmmlu.zip') as z:
        for name in sorted(z.namelist()):
            if not name.endswith('.csv') or Path(name).parent.name!='test':continue
            for i,raw in enumerate(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig')))):
                r={k.lower() if k not in 'ABCD' else k:v for k,v in raw.items()}
                add('cmmlu',f'{name}:{i}','chinese',r['question'].strip()+'\n'+'\n'.join(k+'. '+r[k].strip() for k in 'ABCD')+'\n请给出答案并简要说明理由。',r['question'])
    ds=[json.loads(line) for line in gzip.open(dsdir/'ds1000.jsonl.gz','rt',encoding='utf-8')]
    # Origin families collapse variants of one question before any label is available.
    for r in ds:
        meta=r['metadata'];family=f"{meta['library']}:{meta['perturbation_origin_id']}"
        prompt='Complete the following Python data-science task. Return Python code.\n'+r['prompt']
        if len(prompt.encode())>1536:continue
        candidate=grams(r['prompt'])
        if any(len(candidate&old)/max(1,len(candidate|old))>=.5 for old in old_code):near_rejected+=1;continue
        add('ds1000',meta['problem_id'],'code',prompt,'ds1000-origin-family:'+family,
          dict(origin_family=family,library=meta['library'],original_prompt_sha256=digest(normalize(r['prompt']))))
    quotas=dict(chinese=400,english=250,code=100,math=250);available={c:0 for c in quotas};selected={c:0 for c in quotas};chosen=[];groups=set();prompts=set()
    seed='m14-v4b-final-prompts-20261023-v1';pool.sort(key=lambda r:digest(seed+':'+r['id']))
    ds_grams=[]
    for row in pool:
        c=row['category']
        if row['group_sha256'] in groups or row['prompt_sha256'] in prompts:continue
        if c=='code':
            candidate=grams(row['prompt'])
            if any(len(candidate&other)/max(1,len(candidate|other))>=.5 for other in ds_grams):continue
            ds_grams.append(candidate)
        groups.add(row['group_sha256']);prompts.add(row['prompt_sha256']);available[c]+=1
        if selected[c]<quotas[c]:chosen.append(row);selected[c]+=1
    assert selected==quotas,(selected,available)
    assert len(chosen)==len({r['group_sha256'] for r in chosen})==len({r['prompt_sha256'] for r in chosen})==1000
    text=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in chosen)
    (D/'holdout.jsonl').write_text(text,encoding='utf-8')
    meta=dict(state='PASS_FRESH_PROMPTS_ONLY_NO_LABELS',created='2026-10-23',counts=quotas,available_unused=available,
      seed=seed,corpus_sha256=sha(D/'holdout.jsonl'),script_sha256=sha(Path(__file__)),prior_prompt_files_sha256=prior_sha,
      public_sources_lock_sha256=sha(BASE/'sources.lock.json'),ds1000_sources_lock_sha256=sha(dsdir/'SOURCE_LOCK.json'),
      source_change='MBPP has only10 unused non-fewshot tasks; replace code quota100 with official DS-1000 at pinned revision before labels.',
      math_source='Unused normalized groups from official GSM8K train/test, excluding all actual prior reserved groups; official train split does not mean used for this head fitting.',
      ds1000_origin_family_grouping=True,code_prior_trigram_jaccard_rejection_threshold=.5,code_prior_near_rejections=near_rejected,
      exact_normalized_group_overlap=0,exact_normalized_prompt_overlap=0,
      near_duplicate_limit='Origin families and exact/trigram checks only; semantic equivalence and model pretraining contamination remain unknown.',
      answers='Only prompt field; no reference_code/code_context/solutions executed or supplied as prompt',
      final_labels_opened=False,model_or_head_labels_collected=False,selection_lock_required=True,
      generation=dict(max_new_tokens=16,max_input_tokens=2048,penalty=1.1),byte_limit=1536)
    (D/'MANIFEST.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(state=meta['state'],counts=quotas,available_unused=available),ensure_ascii=False))
if __name__=='__main__':main()
