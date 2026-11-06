"""Freeze fixed-arithmetic quality inputs; prompt-only reservation, no labels/fit.

Downloads only official HumanEval data/LICENSE/README when explicitly requested.
Does not execute dataset code, collect GPU labels, or evaluate heldout outcomes.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,csv,gzip,hashlib,importlib.util,io,json,re,zipfile
M=Path(__file__).resolve().parents[1];D=M/'data/fixed_quality_20261022'
spec=importlib.util.spec_from_file_location('public_sources',M/'scripts/prepare_public_corpus.py')
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
def source():
    lock=D/'HumanEval_sources.lock.json'
    if lock.exists():meta=json.loads(lock.read_text());rev=meta['revision']
    else:
        rev=json.loads(src.fetch('https://api.github.com/repos/openai/human-eval/commits/master'))['sha']
        assert re.fullmatch('[0-9a-f]{40}',rev)
        meta=dict(repository='https://github.com/openai/human-eval',revision=rev,files={})
        save(lock,meta)
    for n in ('data/HumanEval.jsonl.gz','LICENSE','README.md'):
        p=D/'raw'/Path(n).name;p.parent.mkdir(exist_ok=True)
        if n in meta['files']:
            assert sha(p)==meta['files'][n]['sha256'];continue
        url=f'https://raw.githubusercontent.com/openai/human-eval/{rev}/{n}'
        b=src.fetch(url)
        if p.exists():assert p.read_bytes()==b
        else:p.write_bytes(b)
        meta['files'][n]=dict(url=url,sha256=sha(p),bytes=len(b))
        temp=lock.with_suffix('.tmp');temp.write_text(json.dumps(meta,indent=2)+'\n');temp.replace(lock)
    return meta

def freeze():
    path=D/'IMPLEMENTATION_FREEZE.json'
    ip=json.loads((M/'reports/SELECTOR_PRIVATE_IP_MANIFEST.json').read_text())
    files=list(ip['source_sha256'])+['reports/SELECTOR_PRIVATE_IP_MANIFEST.json','reference/selector_arithmetic.py',
           'scripts/qualify_selector_arithmetic.py','scripts/prepare_fixed_quality_20261022.py',
           'reports/selector_p2_20261021/lowrank_r128.npz','reports/selector_p2_20261021/route_r128.npz',
           'data/model/MODEL.lock.json']
    for n,h in ip['source_sha256'].items():assert sha(M/n)==h,n
    hashes={n:sha(M/n) for n in files}
    current=dict(configuration='route4_K16384_UNION_lr128_K16384',source_sha256=hashes,
                 gate=dict(overall_point_recall=.999,each_category_point_recall=.999,min_groups=1000,min_decode_steps=10000),
                 counts=dict(chinese=400,english=250,code=100,math=250),seed='m14-fixed-arithmetic-independent-20261022',
                 input_limit='UTF8 prompt bytes<=1536; 512 bytes reserved for fixed chat template, conservative upper bound, not measured tokenizer count',
                 generation=dict(max_new_tokens=16,max_input_tokens=2048),
                 policy='No parameter/threshold fit, no old outcome reuse. Reserve fresh complete question groups, then collect canonical dense trajectories. Report route/lowrank/hybrid ablation for this frozen arithmetic. Point estimates only, not lossless/free-generation proof.',
                 limitations='Exact normalized dedup only; near-duplicates/model pretraining contamination unknown. Smaller and changed code source than historical test.',
                 created=datetime.now(timezone(timedelta(hours=8))).isoformat())
    if path.exists():
        prior=json.loads(path.read_text());current['created']=prior['created'];assert current==prior,'Frozen implementation/config changed'
    else:save(path,current)

def reserve():
    if (D/'MANIFEST.json').exists():raise FileExistsError('Preserve frozen reservation; no resampling')
    base=M/'data/public_corpus_v1';lock=json.loads((base/'sources.lock.json').read_text())
    for e in lock['files']:assert sha(base/e['local_path'])==e['sha256']
    usedg=set();usedp=set();prior={}
    files=[base/(s+'.jsonl') for s in ('train','calibration','holdout')]
    files+=sorted((base/'snapshots').glob('*.jsonl'))
    files+=[M/f'data/fresh_holdout_{rev}_20261021/holdout.jsonl' for rev in ('r2','r2b')]
    for p in files:
        if not p.exists():continue
        prior[p.relative_to(M).as_posix()]=sha(p)
        for r in src.jsonlines(p):usedg.add(r['group_sha256']);usedp.add(r['prompt_sha256'])
    pool=[]
    def add(source,sid,cat,prompt,group):
        prompt=prompt.strip();g=src.digest(src.normalize(group).encode());h=src.digest(src.normalize(prompt).encode())
        if not prompt or len(prompt.encode('utf-8'))>1536 or g in usedg or h in usedp:return
        pool.append(dict(id=f'{source}:{sid}',source=source,source_id=str(sid),category=cat,split='holdout',prompt=prompt,group_sha256=g,prompt_sha256=h))
    for i,r in enumerate(src.jsonlines(src.raw_path('dolly','databricks-dolly-15k.jsonl'))):
        if src.bucket(src.normalize(r['instruction']))>=85:add('dolly',i,'english',r['instruction']+('\n\nContext:\n'+r['context'].strip() if r['context'].strip() else ''),r['instruction'])
    for i,r in enumerate(src.jsonlines(src.raw_path('gsm8k','test.jsonl'))):add('gsm8k',f'test:{i}','math',r['question'],r['question'])
    with zipfile.ZipFile(src.raw_path('cmmlu','cmmlu.zip')) as z:
        for n in sorted(z.namelist()):
            if not n.endswith('.csv') or Path(n).parent.name!='test':continue
            for i,row in enumerate(csv.DictReader(io.StringIO(z.read(n).decode('utf-8-sig')))):
                r={k.lower() if k not in 'ABCD' else k:v for k,v in row.items()}
                if src.bucket(src.normalize(r['question']))>=20:add('cmmlu',f'{n}:{i}','chinese',r['question'].strip()+'\n'+'\n'.join(k+'. '+r[k].strip() for k in 'ABCD')+'\n请给出答案并简要说明理由。',r['question'])
    # Prompt field only. Canonical solutions/tests are never executed or used.
    with gzip.open(D/'raw/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:
        for line in f:
            row=json.loads(line);prompt=row['prompt'];add('humaneval',row['task_id'],'code','Complete the following Python function.\n'+prompt,prompt)
    freeze_data=json.loads((D/'IMPLEMENTATION_FREEZE.json').read_text());seed=freeze_data['seed'];counts=freeze_data['counts']
    pool.sort(key=lambda r:src.digest((seed+':'+r['id']).encode()))
    groups=set();prompts=set();chosen=[];available={k:0 for k in counts};selected={k:0 for k in counts}
    for row in pool:
        if row['group_sha256'] in groups or row['prompt_sha256'] in prompts:continue
        groups.add(row['group_sha256']);prompts.add(row['prompt_sha256']);c=row['category'];available[c]+=1
        if selected[c]<counts[c]:chosen.append(row);selected[c]+=1
    assert selected==counts,(selected,counts,available)
    assert len(chosen)==1000 and len({r['group_sha256'] for r in chosen})==1000
    path=D/'holdout.jsonl'
    with path.open('x',encoding='utf-8') as f:
        for row in chosen:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
    save(D/'MANIFEST.json',dict(state='PASS_PROMPT_RESERVATION_ONLY_LABELS_NOT_COLLECTED',counts=selected,available_unused=available,
         implementation_freeze_sha256=sha(D/'IMPLEMENTATION_FREEZE.json'),holdout_sha256=sha(path),
         prior_prompt_files_sha256=prior,excluded_prior_groups=len(usedg),excluded_prior_prompts=len(usedp),
         group_overlap_with_all_prior=0,prompt_overlap_with_all_prior=0,
         public_sources_lock_sha256=sha(base/'sources.lock.json'),humaneval_sources_lock_sha256=sha(D/'HumanEval_sources.lock.json'),
         label_or_outcome_access='NONE; raw reference-solution fields not used',quality='NOT_EVALUATED',input_length_rule=freeze_data['input_limit'],
         limitations=freeze_data['limitations']))
    print('FIXED_QUALITY_RESERVATION=PASS 1000 fresh groups; no labels/quality claim')

def main():
    p=argparse.ArgumentParser();p.add_argument('--download-humaneval',action='store_true');p.add_argument('--reserve',action='store_true');a=p.parse_args()
    D.mkdir(exist_ok=True);freeze()
    if a.download_humaneval:source()
    if a.reserve:reserve()
    if not a.download_humaneval and not a.reserve:print('FIXED_QUALITY_IMPLEMENTATION=FROZEN_ONLY; no network, labels or GPU')

if __name__=='__main__':main()
