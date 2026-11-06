"""Reserve fresh complete question groups from pinned local public sources.

Text only, no hidden/dense labels, no network or fitting. Code quota64 reflects
the64 unconsumed HumanEval tasks; math286 keeps1000 groups, frozen pre-label.
"""
from pathlib import Path
import csv,gzip,hashlib,importlib.util,io,json,zipfile
M=Path(__file__).resolve().parents[1];D=M/'data/fusion10_quality_20261023';BASE=M/'data/public_corpus_v1';OLD=M/'data/fixed_quality_20261022'
spec=importlib.util.spec_from_file_location('_sources',M/'scripts/prepare_public_corpus.py');src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    D.mkdir(exist_ok=True);assert not (D/'MANIFEST.json').exists(),'Never resample completed reservation'
    lock=json.loads((BASE/'sources.lock.json').read_text(encoding='utf-8'))
    for e in lock['files']:assert sha(BASE/e['local_path'])==e['sha256']
    human=json.loads((OLD/'HumanEval_sources.lock.json').read_text(encoding='utf-8'))
    for n,e in human['files'].items():assert sha(OLD/'raw'/Path(n).name)==e['sha256']
    prior=set(BASE/(s+'.jsonl') for s in ['train','calibration','holdout']);prior.update((BASE/'snapshots').glob('*.jsonl'));prior.update(M.glob('data/*/holdout.jsonl'));prior.discard(D/'holdout.jsonl')
    used_g=set();used_p=set();prior_hash={}
    for p in sorted(prior):
        if not p.exists():continue
        prior_hash[p.relative_to(M).as_posix()]=sha(p)
        for row in src.jsonlines(p):used_g.add(row['group_sha256']);used_p.add(row['prompt_sha256'])
    pool=[]
    def add(source,sid,category,prompt,group):
        prompt=prompt.strip();g=src.digest(src.normalize(group).encode());h=src.digest(src.normalize(prompt).encode())
        if not prompt or len(prompt.encode('utf-8'))>1536 or g in used_g or h in used_p:return
        pool.append(dict(id=f'{source}:{sid}',source=source,source_id=str(sid),category=category,split='holdout',prompt=prompt,group_sha256=g,prompt_sha256=h))
    for i,r in enumerate(src.jsonlines(src.raw_path('dolly','databricks-dolly-15k.jsonl'))):
        if src.bucket(src.normalize(r['instruction']))>=85:add('dolly',i,'english',r['instruction']+('\n\nContext:\n'+r['context'].strip() if r['context'].strip() else ''),r['instruction'])
    for i,r in enumerate(src.jsonlines(src.raw_path('gsm8k','test.jsonl'))):add('gsm8k',f'test:{i}','math',r['question'],r['question'])
    with zipfile.ZipFile(src.raw_path('cmmlu','cmmlu.zip')) as z:
        for name in sorted(z.namelist()):
            if not name.endswith('.csv') or Path(name).parent.name!='test':continue
            for i,row in enumerate(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig')))):
                r={k.lower() if k not in 'ABCD' else k:v for k,v in row.items()}
                if src.bucket(src.normalize(r['question']))>=20:add('cmmlu',f'{name}:{i}','chinese',r['question'].strip()+'\n'+'\n'.join(k+'. '+r[k].strip() for k in 'ABCD')+'\n请给出答案并简要说明理由。',r['question'])
    with gzip.open(OLD/'raw/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);add('humaneval',r['task_id'],'code','Complete the following Python function.\n'+r['prompt'],r['prompt'])
    counts=dict(chinese=400,english=250,code=64,math=286);chosen=[];groups=set();prompts=set();available={k:0 for k in counts};selected={k:0 for k in counts};seed='m14-fusion-exp10-20261023-independent-v1'
    pool.sort(key=lambda r:src.digest((seed+':'+r['id']).encode()))
    for row in pool:
        if row['group_sha256'] in groups or row['prompt_sha256'] in prompts:continue
        groups.add(row['group_sha256']);prompts.add(row['prompt_sha256']);c=row['category'];available[c]+=1
        if selected[c]<counts[c]:chosen.append(row);selected[c]+=1
    assert selected==counts,(selected,counts,available);assert len(chosen)==len({r['group_sha256'] for r in chosen})==1000
    with (D/'holdout.jsonl').open('x',encoding='utf-8') as f:
        for row in chosen:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
    write(D/'MANIFEST.json',dict(state='PASS_FRESH_PROMPTS_ONLY_NO_LABELS',counts=counts,available_unused=available,seed=seed,corpus_sha256=sha(D/'holdout.jsonl'),source_sha256=sha(Path(__file__)),public_sources_lock_sha256=sha(BASE/'sources.lock.json'),humaneval_sources_lock_sha256=sha(OLD/'HumanEval_sources.lock.json'),prior_prompt_files_sha256=prior_hash,group_overlap=0,prompt_overlap=0,selection_lock_required='reports/fusion_exp10_20261023_r1/SELECTION_LOCK.json',quota_reason='100 old HumanEval tasks opened; remaining64 unused tasks retained, math286 instead of250 for total1000, fixed before labels',split='Whole normalized question group; exclude every previous reserved group, exact NFKC/casefold/whitespace matching',limits='Conditional dense-trajectory recall; semantic duplicates/pretraining contamination unknown; no free-generation/task-score or board acceptance',outcome_access='NONE',generation=dict(max_new_tokens=16,max_input_tokens=2048,penalty=1.1)))
    print('EXP10_FRESH_PROMPTS=PASS '+json.dumps(counts)+'; labels NOT_COLLECTED')
if __name__=='__main__':main()
