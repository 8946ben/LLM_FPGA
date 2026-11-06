"""Tokenize reserved prompts only; no model inference or labels."""
from pathlib import Path
import hashlib,json,os
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
from transformers import AutoTokenizer
M=Path(__file__).resolve().parents[1];ROOT=M.parent;V4=ROOT/'module_14_lm_head_v4';D=M/'data/final_quality_20261023'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=json.loads((D/'MANIFEST.json').read_text(encoding='utf-8'));assert sha(D/'holdout.jsonl')==manifest['corpus_sha256']
    model=V4/'data/model';lock=json.loads((model/'MODEL.lock.json').read_text())
    for f in lock['files']:
        if f['name']!='model.safetensors':assert sha(model/f['name'])==f['sha256']
    tokenizer=AutoTokenizer.from_pretrained(model,local_files_only=True,trust_remote_code=False)
    legacy=json.loads((ROOT/'qwen25_0p5b_instruct_full_generation_trace/metadata.json').read_text(encoding='utf-8'))
    text=tokenizer.apply_chat_template(legacy['messages'],tokenize=False,add_generation_prompt=True)
    assert tokenizer(text,add_special_tokens=False)['input_ids']==legacy['input_ids']
    records=[]
    for line in (D/'holdout.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(line);messages=[dict(role='system',content='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'),dict(role='user',content=r['prompt'])]
        text=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True);ids=tokenizer(text,add_special_tokens=False)['input_ids']
        assert len(ids)<=2048,(r['id'],len(ids))
        records.append(dict(id=r['id'],category=r['category'],tokens=len(ids),input_ids_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()))
    assert len(records)==1000
    result=dict(state='PASS_ALL_1000_PROMPTS_BEFORE_LABELS',corpus_sha256=manifest['corpus_sha256'],source_sha256=sha(Path(__file__)),
      model_lock_sha256=sha(model/'MODEL.lock.json'),min_input_tokens=min(r['tokens'] for r in records),max_input_tokens=max(r['tokens'] for r in records),
      canonical_archived_chat_template_input_ids_match=True,labels_collected=False,records=records)
    (D/'TOKENIZER_PREFLIGHT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(result['state'],result['min_input_tokens'],result['max_input_tokens'])
if __name__=='__main__':main()
