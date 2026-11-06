"""Reconstruct question hashes independently from pinned raw public sources."""
from pathlib import Path
import csv,gzip,hashlib,io,json,unicodedata,zipfile
M=Path(__file__).resolve().parents[1];B=M/'data/public_corpus_v1';D=M/'data/fusion10_quality_20261023';R=M/'reports/fusion_exp10_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def normalized_sha(s):return hashlib.sha256(' '.join(unicodedata.normalize('NFKC',s).casefold().split()).encode('utf-8')).hexdigest()
def main():
    reservation=read(D/'MANIFEST.json');entry=read(D/'EVALUATION_ENTRY_LOCK.json');assert sha(D/'MANIFEST.json')==entry['reservation_sha256'];lock=read(B/'sources.lock.json');human=M/'data/fixed_quality_20261022';hlock=read(human/'HumanEval_sources.lock.json')
    assert sha(B/'sources.lock.json')==reservation['public_sources_lock_sha256'] and sha(human/'HumanEval_sources.lock.json')==reservation['humaneval_sources_lock_sha256']
    for e in lock['files']:assert sha(B/e['local_path'])==e['sha256'],e['local_path']
    for name,e in hlock['files'].items():assert sha(human/'raw'/Path(name).name)==e['sha256']
    questions={}
    for i,row in enumerate(lines(B/'raw/dolly/databricks-dolly-15k.jsonl')):questions['dolly',str(i)]=row['instruction']
    for split in ['train','test']:
        for i,row in enumerate(lines(B/f'raw/gsm8k/{split}.jsonl')):questions['gsm8k',f'{split}:{i}']=row['question']
    for row in lines(B/'raw/mbpp/mbpp.jsonl'):questions['mbpp',str(row['task_id'])]=row['text']
    with zipfile.ZipFile(B/'raw/cmmlu/cmmlu.zip') as z:
        for name in z.namelist():
            if name.endswith('.csv'):
                for i,row in enumerate(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig')))):
                    row={k.lower():v for k,v in row.items()};questions['cmmlu',f'{name}:{i}']=row['question']
    with gzip.open(human/'raw/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:
        for line in f:
            row=json.loads(line);questions['humaneval',row['task_id']]=row['prompt']
    checked={};new=lines(D/'holdout.jsonl');old_g=set();old_p=set()
    paths=[D/'holdout.jsonl']+[M/n for n in reservation['prior_prompt_files_sha256']]
    for p in paths:
        if p!=paths[0]:assert sha(p)==reservation['prior_prompt_files_sha256'][p.relative_to(M).as_posix()]
        rows=lines(p)
        for row in rows:
            group=questions[row['source'],str(row['source_id'])];assert normalized_sha(group)==row['group_sha256'],row['id'];assert normalized_sha(row['prompt'])==row['prompt_sha256'],row['id']
            if p!=paths[0]:old_g.add(normalized_sha(group));old_p.add(normalized_sha(row['prompt']))
        checked[p.relative_to(M).as_posix()]=len(rows)
    assert not {r['group_sha256'] for r in new}&old_g and not {r['prompt_sha256'] for r in new}&old_p
    report=dict(state='PASS_RAW_SOURCE_RECONSTRUCTED_GROUP_AND_PROMPT_HASHES',files=checked,fresh_groups=len(new),raw_question_keys=len(questions),group_overlap=0,prompt_overlap=0,reservation_sha256=sha(D/'MANIFEST.json'),source_sha256=sha(Path(__file__)),scope='Exact NFKC/casefold/whitespace question and prompt identity, independently reconstructed from pinned raw text. Does not establish semantic/template separation or absence of pretraining contamination. No selector/quality rerun, no fitting.',board='NOT_RUN')
    (R/'PUBLIC_SOURCE_RESERVATION_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report['state'],checked)
if __name__=='__main__':main()
