"""Freeze six existing configurations, fresh text, sources and tokenizer before labels."""
import hashlib,json,sys
from pathlib import Path
import sparse_quality_common_20261024 as R
from transformers import AutoTokenizer

def main():
    assert not (R.DATA/'EVALUATION_ENTRY_LOCK.json').exists()
    R.OUT.mkdir(exist_ok=True)
    manifest=R.read(R.DATA/'MANIFEST.json');assert manifest['corpus_sha256']==R.sha(R.DATA/'holdout.jsonl') and not manifest['final_labels_opened']
    base=R.read(R.M/'reports/sparse_methods_20261024_r1/benchmark/RESULT.json')
    keys=['cluster_C128_R2_L16384','cluster_C128_R4_L16384','partial_dynamic_d64_T4096','partial_dynamic_d128_T1024','partial_dynamic_d128_T4096','dense']
    rows={p['id']:p for p in base['configurations']};configs=[{k:rows[id][k] for k in ['id','config','mode','parameters','experiments']} for id in keys]
    lock=dict(created=R.now(),state='FROZEN_BEFORE_NEW_LABELS',configurations=configs,threshold=dict(overall_decode_recall=.99,each_category_decode_recall=.99,numerical_implementation='BIT_EXACT'),no_retuning=True,old_result_sha256=R.sha(R.M/'reports/sparse_methods_20261024_r1/benchmark/RESULT.json'),purpose='Confirm six preregistered configurations, no claim of global optimum; all results reported',timing_input_rule='First reserved prompt per category with >=2 predictions, decode step1; not chosen by outcome',generation=dict(max_new_tokens=16,max_input_tokens=2048,penalty=1.1))
    R.write(R.OUT/'SELECTION_LOCK.json',lock)
    tok=AutoTokenizer.from_pretrained(R.M/'data/model',local_files_only=True,trust_remote_code=False)
    corpus=[json.loads(s) for s in (R.DATA/'holdout.jsonl').read_text(encoding='utf-8').splitlines()]
    records=[]
    for row in corpus:
        text=tok.apply_chat_template([dict(role='system',content='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'),dict(role='user',content=row['prompt'])],tokenize=False,add_generation_prompt=True)
        ids=tok(text,add_special_tokens=False)['input_ids'];assert len(ids)<=2048
        records.append(dict(id=row['id'],input_tokens=len(ids),input_ids_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()))
    legacy=R.read(R.ROOT/'qwen25_0p5b_instruct_full_generation_trace/metadata.json')
    assert tok(tok.apply_chat_template(legacy['messages'],tokenize=False,add_generation_prompt=True),add_special_tokens=False)['input_ids']==legacy['input_ids']
    R.write(R.DATA/'TOKENIZER_PREFLIGHT.json',dict(state='PASS1000_NO_TRUNCATION_AND_ARCHIVED_TEMPLATE',records=records,minimum=min(x['input_tokens'] for x in records),maximum=max(x['input_tokens'] for x in records)))
    paths=[Path(__file__),R.M/'data/model/MODEL.lock.json',R.DATA/'holdout.jsonl',R.DATA/'MANIFEST.json',R.DATA/'TOKENIZER_PREFLIGHT.json',R.CUDA_FILE,R.WEIGHT]
    for name in ['reserve_sparse_quality_20261024.py','sparse_quality_common_20261024.py','collect_sparse_quality_20261024.py','evaluate_sparse_quality_20261024.py','benchmark_sparse_quality_20261024.py']:paths.append(R.M/'scripts'/name)
    paths += [R.M/'reference'/name for name in ['quality_data.py','numeric_contract.py','hyperparameter_study.py']]
    paths += [R.M/'experiments/sparse_methods_20261024/sparse_methods.py',R.M/'reports/sparse_methods_20261024_r1/PARAMETERS.json',R.M/'reports/hyperparameters_20261023_r1/PARAMETERS.json',R.M/'reports/hyperparameters_20261023_r1/parameters/norms_C128.npy']
    param=R.read(R.M/'reports/hyperparameters_20261023_r1/PARAMETERS.json')['files']['C128'];path=R.M/'reports/hyperparameters_20261023_r1'/param['path'];assert R.sha(path)==param['sha256'];paths.append(path)
    for item in R.read(R.M/'reports/sparse_methods_20261024_r1/PARAMETERS.json')['files'].values():
        path=R.M/'reports/sparse_methods_20261024_r1'/item['path'];assert R.sha(path)==item['sha256'];paths.append(path)
    for relative,sha in manifest['prior_prompt_files_sha256'].items():assert R.sha(R.ROOT/relative)==sha
    R.write(R.DATA/'EVALUATION_ENTRY_LOCK.json',dict(state='FROZEN_BEFORE_NEW_LABELS',created=R.now(),selection_lock_sha256=R.sha(R.OUT/'SELECTION_LOCK.json'),corpus_sha256=R.sha(R.DATA/'holdout.jsonl'),sources={p.relative_to(R.ROOT).as_posix():R.sha(p) for p in paths},final_labels_opened=False,retuning_prohibited=True))
    R.progress('ENTRY_FROZEN_NO_LABELS',configurations=6,prompts=1000,token_minimum=min(x['input_tokens'] for x in records),token_maximum=max(x['input_tokens'] for x in records))
if __name__=='__main__':main()
