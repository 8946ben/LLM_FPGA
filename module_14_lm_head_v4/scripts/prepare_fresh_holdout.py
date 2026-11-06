"""Reserve fresh prompt groups using pinned public raw files; no label access."""
from pathlib import Path
import argparse,csv,hashlib,importlib.util,io,json,zipfile
M=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('_public_v1',M/'scripts/prepare_public_corpus.py')
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--token-filter',action='store_true');args=ap.parse_args()
    original=M/'data/public_corpus_v1';out=M/('data/fresh_holdout_r2b_20261021' if args.token_filter else 'data/fresh_holdout_r2_20261021');out.mkdir(parents=True,exist_ok=True)
    tokenizer=None
    if args.token_filter:
        from transformers import AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(M/'data/model',local_files_only=True,trust_remote_code=False)
    lock=json.loads((original/'sources.lock.json').read_text(encoding='utf-8'))
    for entry in lock['files']:assert sha(original/entry['local_path'])==entry['sha256']
    used_groups=set();used_prompts=set()
    for split in ('train','calibration','holdout'):
        for row in src.jsonlines(original/(split+'.jsonl')):used_groups.add(row['group_sha256']);used_prompts.add(row['prompt_sha256'])
    rows=[]
    def add(source,sid,category,prompt,group):
        prompt=prompt.strip();g=src.digest(src.normalize(group).encode());p=src.digest(src.normalize(prompt).encode())
        if not prompt or len(prompt)>12000 or g in used_groups or p in used_prompts:return
        rows.append(dict(id=source+':'+str(sid),source=source,source_id=str(sid),category=category,split='holdout',prompt=prompt,group_sha256=g,prompt_sha256=p))
    for i,r in enumerate(src.jsonlines(src.raw_path('dolly','databricks-dolly-15k.jsonl'))):
        if src.bucket(src.normalize(r['instruction']))>=85:
            add('dolly',i,'english',r['instruction']+('\n\nContext:\n'+r['context'].strip() if r['context'].strip() else ''),r['instruction'])
    for i,r in enumerate(src.jsonlines(src.raw_path('gsm8k','test.jsonl'))):add('gsm8k','test:'+str(i),'math',r['question'],r['question'])
    for r in src.jsonlines(src.raw_path('mbpp','mbpp.jsonl')):
        if 11<=int(r['task_id'])<=510:add('mbpp',r['task_id'],'code','Write a Python function for the following task.\n'+r['text'].strip(),r['text'])
    with zipfile.ZipFile(src.raw_path('cmmlu','cmmlu.zip')) as z:
        for name in sorted(z.namelist()):
            if not name.endswith('.csv') or Path(name).parent.name!='test':continue
            for i,original_row in enumerate(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig')))):
                r={k.lower() if k not in 'ABCD' else k:v for k,v in original_row.items()}
                if src.bucket(src.normalize(r['question']))>=20:
                    add('cmmlu',name+':'+str(i),'chinese',r['question'].strip()+'\n'+'\n'.join(k+'. '+r[k].strip() for k in 'ABCD')+'\n请给出答案并简要说明理由。',r['question'])
    rows.sort(key=lambda r:src.digest(('m14-v4-r2-reserve:'+r['id']).encode()))
    groups=set();prompts=set();pool={k:[] for k in ('chinese','english','code','math')}
    for row in rows:
        if row['group_sha256'] in groups or row['prompt_sha256'] in prompts:continue
        groups.add(row['group_sha256']);prompts.add(row['prompt_sha256']);pool[row['category']].append(row)
    code=min(250,len(pool['code']));counts=dict(chinese=500-code,english=250,code=code,math=250)
    assert code>=150
    selected=[];over_limit=[];lengths=[]
    for category,n in counts.items():
        chosen=[]
        for row in pool[category]:
            if tokenizer is not None:
                text=tokenizer.apply_chat_template([dict(role='system',content='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'),dict(role='user',content=row['prompt'])],tokenize=False,add_generation_prompt=True)
                length=len(tokenizer(text,add_special_tokens=False)['input_ids'])
                if length>2048:over_limit.append(dict(id=row['id'],input_tokens=length));continue
                lengths.append(length)
            chosen.append(row)
            if len(chosen)==n:break
        assert len(chosen)==n;selected.extend(chosen)
    assert len(selected)==len({r['group_sha256'] for r in selected})==1000
    content=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in selected);path=out/'holdout.jsonl'
    if path.exists():assert path.read_text(encoding='utf-8')==content
    else:path.write_text(content,encoding='utf-8')
    report=dict(state='PASS',format='M14_V4_FRESH_HOLDOUT_R2',counts=counts,available_unused_groups={k:len(v) for k,v in pool.items()},
        holdout_sha256=sha(path),sources_lock_sha256=sha(original/'sources.lock.json'),excluded_prior_prompt_groups=len(used_groups),
        excluded_prior_prompts=len(used_prompts),group_overlap_with_v1=0,prompt_overlap_with_v1=0,
        prior_split_sha256={s:sha(original/(s+'.jsonl')) for s in ('train','calibration','holdout')},
        rule='Only unused original official-test/heldout-pool groups; hash order fixed without labels; MBPP scarcity assigned to Chinese, total1000 independent groups.',
        input_filter=dict(enabled=args.token_filter,max_input_tokens=max(lengths) if lengths else None,excluded_over_2048=over_limit,scope='Input tokenizer length only; no output labels examined'),
        limitations='Exact normalized grouping only; semantic/template similarity and model pretraining contamination unknown.')
    (out/'MANIFEST.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
