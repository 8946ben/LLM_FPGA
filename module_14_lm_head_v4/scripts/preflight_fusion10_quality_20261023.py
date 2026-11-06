"""Actual tokenizer length/identity check before any new dense labels."""
from pathlib import Path
import hashlib,json
from transformers import AutoTokenizer
M=Path(__file__).resolve().parents[1];D=M/'data/fusion10_quality_20261023'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=json.loads((M/'data/model/MODEL.lock.json').read_text(encoding='utf-8'))
    for row in lock['files']:assert sha(M/'data/model'/row['name'])==row['sha256']
    reservation=json.loads((D/'MANIFEST.json').read_text(encoding='utf-8'));assert sha(D/'holdout.jsonl')==reservation['corpus_sha256'];rows=[json.loads(s) for s in (D/'holdout.jsonl').read_text(encoding='utf-8').splitlines()];assert len(rows)==1000
    tok=AutoTokenizer.from_pretrained(M/'data/model',local_files_only=True,trust_remote_code=False);legacy=json.loads((M.parent/'qwen25_0p5b_instruct_full_generation_trace/metadata.json').read_text(encoding='utf-8'));text=tok.apply_chat_template(legacy['messages'],tokenize=False,add_generation_prompt=True);assert tok(text,add_special_tokens=False)['input_ids']==legacy['input_ids']
    records=[]
    for row in rows:
        messages=[dict(role='system',content='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'),dict(role='user',content=row['prompt'])];text=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True);ids=tok(text,add_special_tokens=False)['input_ids'];assert len(ids)<=2048,(row['id'],len(ids));records.append(dict(id=row['id'],tokens=len(ids),input_ids_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()))
    result=dict(state='PASS1000_TOKENIZER_LENGTH_IDENTITY_NO_LABELS',source_sha256=sha(Path(__file__)),corpus_sha256=sha(D/'holdout.jsonl'),model_lock_sha256=sha(M/'data/model/MODEL.lock.json'),max_input_tokens=max(r['tokens'] for r in records),records=records,label_access='NONE',network='NONE')
    target=D/'TOKENIZER_PREFLIGHT.json';assert not target.exists();target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(result['state'],result['max_input_tokens'])
if __name__=='__main__':main()
