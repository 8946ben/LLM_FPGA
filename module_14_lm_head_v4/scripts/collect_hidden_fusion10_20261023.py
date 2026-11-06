"""Collect prompt-grouped dense trajectories with canonical BF16/FP32 head.

GPU/model runtime is a corpus source, not FPGA or whole-system performance.
Resume only when model, corpus, precision and collection settings all match.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys,time
import numpy as np
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
M=Path(__file__).resolve().parents[1];ROOT=M.parent;sys.path.insert(0,str(M))
from reference.gpu_exact_head import GpuExactHead
from reference.numeric_contract import apply_repetition_penalty

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');t.replace(p)
def validate(head,out):
    assets=ROOT/'artifacts/module14_v2_assets';manifest=json.loads((assets/'manifest.json').read_text(encoding='utf-8'))
    rows=[]
    for g in manifest['trace']:
        p=assets/'trace'/g['step'];hidden=np.fromfile(p/'hidden.bf16.bin',dtype='<u2')
        assert sha(p/'hidden.bf16.bin')==g['hidden_sha256']
        started=time.perf_counter();raw=head(hidden);elapsed=time.perf_counter()-started
        assert hashlib.sha256(raw.astype('<f4').tobytes()).hexdigest()==g['raw_logits_sha256'],g['step']
        history=np.fromfile(p/'history_bitmap.u32.bin',dtype='<u4');scores=apply_repetition_penalty(raw,history,1.1)
        assert hashlib.sha256(scores.astype('<f4').tobytes()).hexdigest()==g['processed_scores_sha256']
        token=int(np.argmax(scores));assert token==g['selected_token'] and int(scores[token].view('u4'))==g['selected_score_bits']
        rows.append(dict(step=g['step'],raw_logits_sha256=g['raw_logits_sha256'],cpu_gpu_wall_seconds=elapsed))
        print('GPU_EXACT_HEAD_PASS '+g['step'],flush=True)
    write(out,dict(state='PASS',device=torch.cuda.get_device_name(),torch=torch.__version__,steps=rows,
        scope='Exact canonical head arithmetic on CUDA; no FPGA timing or full transformer equivalence claim',
        implementation_sha256=sha(M/'reference/gpu_exact_head.py')))

@torch.inference_mode()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--split',choices=['train','calibration','holdout'],default='train')
    ap.add_argument('--out',type=Path,default=M/'data/hidden_fusion10_20261023');ap.add_argument('--max-new-tokens',type=int,default=16)
    ap.add_argument('--limit-per-category',type=int);ap.add_argument('--validate-only',action='store_true')
    ap.add_argument('--max-input-tokens',type=int,default=2048);a=ap.parse_args()
    if not 1<=a.max_new_tokens<=128 or not 1<=a.max_input_tokens<=8192:raise ValueError('Invalid input/generation budget')
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False
    if not torch.cuda.is_available():raise RuntimeError('CUDA is required for this collector')
    if torch.cuda.mem_get_info()[0]<3*2**30:raise RuntimeError('Need at least 3GiB free GPU memory; do not compete for occupied device')
    a.out.mkdir(parents=True,exist_ok=True)
    weight=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
    assert sha(weight)=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    # Fail closed before any new labels unless selection and numerical entry are frozen.
    entry=json.loads((M/'data/fusion10_quality_20261023/EVALUATION_ENTRY_LOCK.json').read_text(encoding='utf-8'))
    selected=M/'reports/fusion_exp10_20261023_r1/SELECTION_LOCK.json'
    assert sha(selected)==entry['selection_lock_sha256']
    for relative,expected in entry['source_sha256'].items():assert sha(M/relative)==expected,relative
    assert sha(M/'data/fusion10_quality_20261023/holdout.jsonl')==entry['corpus_sha256']
    head=GpuExactHead(weight);validate(head,a.out/'GPU_HEAD_VALIDATION.json')
    if a.validate_only:return
    model_dir=M/'data/model';lock=json.loads((model_dir/'MODEL.lock.json').read_text())
    for f in lock['files']:assert sha(model_dir/f['name'])==f['sha256'],f['name']
    tok=AutoTokenizer.from_pretrained(model_dir,local_files_only=True,trust_remote_code=False)
    legacy=json.loads((ROOT/'qwen25_0p5b_instruct_full_generation_trace/metadata.json').read_text(encoding='utf-8'))
    legacy_text=tok.apply_chat_template(legacy['messages'],tokenize=False,add_generation_prompt=True)
    legacy_ids=tok(legacy_text,add_special_tokens=False,return_tensors='pt')['input_ids'][0].tolist()
    assert legacy_ids==legacy['input_ids'],'Tokenizer/chat template differs from archived original trace'
    write(a.out/'TOKENIZER_VALIDATION.json',dict(state='PASS',scope='Archived 36-token prompt/chat template input IDs exact',input_ids=legacy_ids))
    model=AutoModelForCausalLM.from_pretrained(model_dir,dtype=torch.bfloat16,local_files_only=True,trust_remote_code=False).eval().to('cuda:0')
    # Verify tied embedding weights are exactly the existing canonical BF16 head.
    embed=model.get_input_embeddings().weight.detach().cpu().view(torch.uint16).numpy().astype('<u2')
    assert hashlib.sha256(embed.tobytes()).hexdigest()==sha(weight)
    corpus=M/'data/fusion10_quality_20261023'/(a.split+'.jsonl')
    rows=[json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines()]
    settings=dict(corpus_sha256=sha(corpus),model_lock_sha256=sha(model_dir/'MODEL.lock.json'),
        canonical_weight_sha256=sha(weight),collector_sha256=sha(Path(__file__)),
        gpu_head_sha256=sha(M/'reference/gpu_exact_head.py'),torch=torch.__version__,
        transformer_dtype='BF16',head_dtype='FP32_H8_INTERLEAVE16_SEPARATE_MULTIPLY_ADD',penalty=1.1,
        system_prompt='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.',
        max_input_tokens=a.max_input_tokens,max_new_tokens=a.max_new_tokens,
        limit_per_category=a.limit_per_category,raw_top_k=256,
        teacher_forcing='Dense autoregressive trajectory, token labels from canonical exact head; not dataset-answer teacher forcing')
    folder=a.out/a.split;folder.mkdir(exist_ok=True);settings_file=folder/'SETTINGS.json'
    if settings_file.exists():assert json.loads(settings_file.read_text(encoding='utf-8'))==settings,'Resume settings/source mismatch'
    else:write(settings_file,settings)
    if a.limit_per_category is not None:
        if a.limit_per_category<=0:raise ValueError('Positive per-category limit required')
        selected=[];counts={}
        for row in rows:
            cat=row['category'];counts[cat]=counts.get(cat,0)+1
            if counts[cat]<=a.limit_per_category:selected.append(row)
        rows=selected
    eos=set(model.generation_config.eos_token_id if isinstance(model.generation_config.eos_token_id,list) else [model.generation_config.eos_token_id])
    summaries=[];start=time.perf_counter()
    for index,row in enumerate(rows):
        if (a.out/'STOP_REQUESTED').exists():print('COLLECT_PAUSED_AT_PROMPT_BOUNDARY',flush=True);break
        stem=hashlib.sha256(row['id'].encode()).hexdigest()[:24];meta=folder/(stem+'.json');data=folder/(stem+'.npz')
        if meta.exists():
            prior=json.loads(meta.read_text(encoding='utf-8'));assert prior['prompt_sha256']==row['prompt_sha256'] and sha(data)==prior['npz_sha256']
            summaries.append(prior);continue
        messages=[dict(role='system',content=settings['system_prompt']),dict(role='user',content=row['prompt'])]
        text=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        tokens=tok(text,add_special_tokens=False,return_tensors='pt')['input_ids'][0].tolist()
        if len(tokens)>a.max_input_tokens:
            # No silent truncation. Exclusions count against holdout coverage.
            summaries.append(dict(id=row['id'],category=row['category'],excluded='INPUT_TOO_LONG',input_tokens=len(tokens),steps=0));continue
        current=torch.tensor([tokens],device='cuda:0');cache=None;hidden_rows=[];top_rows=[];winners=[];score_bits=[]
        seen=set(tokens);prompt_start=time.perf_counter()
        for step in range(a.max_new_tokens):
            attn=torch.ones((1,len(tokens)+step),device='cuda:0',dtype=torch.long)
            output=model.model(input_ids=current,attention_mask=attn,past_key_values=cache,use_cache=True)
            cache=output.past_key_values;hidden=output.last_hidden_state[0,-1].to(torch.bfloat16)
            bits=hidden.detach().cpu().view(torch.uint16).numpy().copy();raw=head(hidden)
            if not np.all(np.isfinite(raw)):raise FloatingPointError('Non-finite full-head logits during collection')
            history=np.zeros((151936+31)//32,dtype='u4')
            for token in seen:history[token>>5]|=np.uint32(1<<(token&31))
            scores=apply_repetition_penalty(raw,history,1.1);winner=int(np.argmax(scores))
            # Stable global-ID ordering at equal boundary scores.
            cutoff=np.partition(raw,-256)[-256];above=np.flatnonzero(raw>cutoff);ties=np.flatnonzero(raw==cutoff)
            top=np.concatenate([above,ties[:256-len(above)]])
            top=top[np.lexsort((top,-raw[top]))].astype('<u4')
            hidden_rows.append(bits);top_rows.append(top);winners.append(winner);score_bits.append(int(scores[winner].view('u4')))
            if winner in eos:break
            seen.add(winner);current=torch.tensor([[winner]],device='cuda:0')
        np.savez_compressed(data,hidden_bf16=np.stack(hidden_rows).astype('<u2'),raw_top_ids=np.stack(top_rows),
            dense_token=np.array(winners,dtype='<u4'),dense_score_bits=np.array(score_bits,dtype='<u4'),input_ids=np.array(tokens,dtype='<u4'))
        result=dict(id=row['id'],category=row['category'],split=a.split,prompt_sha256=row['prompt_sha256'],
            group_sha256=row['group_sha256'],steps=len(winners),decode_steps=max(0,len(winners)-1),
            input_tokens=len(tokens),seconds=time.perf_counter()-prompt_start,npz=data.name,npz_sha256=sha(data),
            generated_ids=winners,collection_scope='Dense CPU/GPU model trajectory; no FPGA operations or performance claim')
        write(meta,result);summaries.append(result)
        write(folder/'PROGRESS.json',dict(state='RUNNING',completed=len(summaries),planned=len(rows),steps=sum(r['steps'] for r in summaries),elapsed_seconds=time.perf_counter()-start))
        print(f"COLLECT_PASS {a.split} {index+1}/{len(rows)} {row['category']} steps={len(winners)} seconds={result['seconds']:.3f}",flush=True)
    complete=len(summaries)==len(rows)
    summary=dict(state='PASS' if complete else 'PAUSED',split=a.split,prompts=len(summaries),planned=len(rows),
        steps=sum(r['steps'] for r in summaries),decode_steps=sum(r.get('decode_steps',0) for r in summaries),
        excluded_prompts=sum('excluded' in r for r in summaries),settings=settings,records=summaries,
        runtime_seconds=time.perf_counter()-start,gpu=torch.cuda.get_device_name())
    write(folder/'MANIFEST.json',summary);write(folder/'PROGRESS.json',{k:v for k,v in summary.items() if k not in ('settings','records')})
    print('HIDDEN_COLLECTION='+summary['state'],flush=True)

# Reuse bounded atomic-I/O only; numerical collection function is unchanged.
from collect_hidden_resumable import atomic_write as write
if __name__=='__main__':main()
