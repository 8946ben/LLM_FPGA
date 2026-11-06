"""Run under the GPU Python BEFORE collecting any new labels; no inference."""
from pathlib import Path
import hashlib,json
M=Path(__file__).resolve().parents[1];D=M/'data/fixed_quality_20261022'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    import sys,torch,transformers
    from transformers import AutoTokenizer
    freeze=json.loads((D/'IMPLEMENTATION_FREEZE.json').read_text())
    entry=json.loads((D/'EVALUATION_ENTRY_LOCK.json').read_text())
    for lock in (freeze,entry):
        for n,h in lock['source_sha256'].items():assert sha(M/n)==h,n
    assert sha(D/'holdout.jsonl')==entry['corpus_sha256']
    model=M/'data/model';model_lock=json.loads((model/'MODEL.lock.json').read_text())
    for f in model_lock['files']:assert sha(model/f['name'])==f['sha256'],f['name']
    tok=AutoTokenizer.from_pretrained(model,local_files_only=True,trust_remote_code=False)
    legacy=json.loads((M.parent/'qwen25_0p5b_instruct_full_generation_trace/metadata.json').read_text(encoding='utf-8'))
    old=tok.apply_chat_template(legacy['messages'],tokenize=False,add_generation_prompt=True)
    assert tok(old,add_special_tokens=False)['input_ids']==legacy['input_ids']
    rows=[json.loads(s) for s in (D/'holdout.jsonl').read_text().splitlines()];lengths=[];invalid=[]
    for row in rows:
        text=tok.apply_chat_template([dict(role='system',content='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'),dict(role='user',content=row['prompt'])],tokenize=False,add_generation_prompt=True)
        n=len(tok(text,add_special_tokens=False)['input_ids']);lengths.append(n)
        if not 1<=n<=2048:invalid.append(dict(id=row['id'],input_tokens=n))
    assert not invalid,('Input budget fails before any labels; preserve frozen set and inspect',invalid)
    assert torch.cuda.is_available(),'CUDA unavailable; do not silently collect on CPU'
    free,total=torch.cuda.mem_get_info();assert free>=3*2**30,'Need free3GiB; preserve other GPU workloads'
    report=dict(state='PASS_INPUT_RUNTIME_ONLY_NO_LABELS',python=sys.executable,torch=torch.__version__,transformers=transformers.__version__,device=torch.cuda.get_device_name(),
                free_gpu_bytes=free,total_gpu_bytes=total,groups=len(rows),min_input_tokens=min(lengths),max_input_tokens=max(lengths),
                corpus_sha256=entry['corpus_sha256'],model_lock_sha256=sha(model/'MODEL.lock.json'),source_sha256=sha(Path(__file__)),
                labels='NOT_COLLECTED_BY_PREFLIGHT',board='NOT_RUN')
    out=M/'reports/fixed_quality_20261022/TOKENIZER_RUNTIME_PREFLIGHT.json';out.parent.mkdir(exist_ok=True)
    assert not out.exists(),'Preserve prior preflight; verify it before explicit resume'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FIXED_QUALITY_PREFLIGHT=PASS1000_TOKENIZED_NO_LABELS')
if __name__=='__main__':main()
