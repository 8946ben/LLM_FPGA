"""Canonical dense trajectories on the frozen v4b fresh question groups."""
from pathlib import Path
import hashlib,json,os,time
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import sparse_quality_common_20261024 as R
import numpy as np
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
D=R.DATA;OUTPUT=R.M/'data/hidden_sparse_quality_20261024';FOLDER=OUTPUT/'holdout'
def guards():
    R.checked();entry=json.loads((D/'EVALUATION_ENTRY_LOCK.json').read_text())
    assert R.sha(R.OUT/'SELECTION_LOCK.json')==entry['selection_lock_sha256']
    assert R.sha(D/'holdout.jsonl')==entry['corpus_sha256']
    for path,h in entry['sources'].items():assert R.sha(R.ROOT/path)==h,path
    return entry
def stop():
    R.stop()
    if (D/'STOP_REQUESTED').exists() or (OUTPUT/'STOP_REQUESTED').exists():raise InterruptedError('Final collection pause requested')
@torch.inference_mode()
def main():
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    entry=guards();stop();assert torch.cuda.mem_get_info()[0]>=4*2**30
    handle=None
    try:
        handle=(R.OUT/'ACTIVE.lock').open('x');handle.write(json.dumps(dict(pid=os.getpid(),phase='fresh_collection',started=R.now())));handle.flush()
        FOLDER.mkdir(parents=True,exist_ok=True);model_dir=R.V4/'data/model'
        lock=json.loads((model_dir/'MODEL.lock.json').read_text())
        for f in lock['files']:assert R.sha(model_dir/f['name'])==f['sha256']
        tok=AutoTokenizer.from_pretrained(model_dir,local_files_only=True,trust_remote_code=False)
        model=AutoModelForCausalLM.from_pretrained(model_dir,dtype=torch.bfloat16,local_files_only=True,trust_remote_code=False).eval().to('cuda')
        bits=model.get_input_embeddings().weight.detach().cpu().view(torch.uint16).numpy().astype('<u2')
        assert hashlib.sha256(bits.tobytes()).hexdigest()==R.sha(R.WEIGHT);del bits
        # Only model.model is used; tied embedding/head tensors are never modified.
        wg=R.gpu(R.fp(np.memmap(R.WEIGHT,dtype='<u2',mode='r',shape=(151936,896))));engine=R.CUDA.ExactCuda(R.OUT/'cuda');R.validate_dense(engine,wg)
        rows=[json.loads(s) for s in (D/'holdout.jsonl').read_text(encoding='utf-8').splitlines()]
        preflight=json.loads((D/'TOKENIZER_PREFLIGHT.json').read_text())
        by_id={p['id']:p for p in preflight['records']}
        eos=model.generation_config.eos_token_id;eos=set(eos if isinstance(eos,list) else [eos])
        settings=dict(corpus_sha256=entry['corpus_sha256'],model_lock_sha256=R.sha(model_dir/'MODEL.lock.json'),
          canonical_weight_sha256=R.sha(R.WEIGHT),collector_sha256=R.sha(Path(__file__)),gpu_head_sha256=R.sha(R.CUDA_FILE),
          torch=torch.__version__,transformer_dtype='BF16',head_dtype='FP32_H8_INTERLEAVE16_SEPARATE_MULTIPLY_ADD',penalty=1.1,
          system_prompt='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.',max_input_tokens=2048,max_new_tokens=16,raw_top_k=256,
          selection_lock_sha256=entry['selection_lock_sha256'],teacher_forcing='Canonical dense autoregressive trajectory, not dataset-answer labels')
        old=FOLDER/'SETTINGS.json'
        if old.exists():assert json.loads(old.read_text())==settings
        else:R.write(old,settings)
        summaries=[];started=time.perf_counter()
        R.write(R.OUT/'FINAL_LABEL_ACCESS.json',dict(state='LABEL_COLLECTION_STARTED_AFTER_SELECTION_LOCK',started=R.now(),
          corpus_sha256=entry['corpus_sha256'],selection_lock_sha256=entry['selection_lock_sha256'],
          note='Reservation/entry false flags are historical pre-label snapshots; runtime access is recorded here and in the collection manifest.'))
        for index,row in enumerate(rows):
            stop();stem=hashlib.sha256(row['id'].encode()).hexdigest()[:24];meta=FOLDER/(stem+'.json');data=FOLDER/(stem+'.npz')
            if meta.exists():
                prior=json.loads(meta.read_text());assert R.sha(data)==prior['npz_sha256'] and prior['prompt_sha256']==row['prompt_sha256'];summaries.append(prior);continue
            assert not data.exists(),'Orphan prior NPZ requires explicit audit, not overwrite'
            text=tok.apply_chat_template([dict(role='system',content=settings['system_prompt']),dict(role='user',content=row['prompt'])],tokenize=False,add_generation_prompt=True)
            tokens=tok(text,add_special_tokens=False)['input_ids'];assert len(tokens)<=2048
            assert hashlib.sha256(json.dumps(tokens,separators=(',',':')).encode()).hexdigest()==by_id[row['id']]['input_ids_sha256']
            current=torch.tensor([tokens],device='cuda');cache=None;seen=set(tokens);hs=[];tops=[];winners=[];scorebits=[];start=time.perf_counter()
            for step in range(16):
                attn=torch.ones((1,len(tokens)+step),device='cuda',dtype=torch.long)
                output=model.model(input_ids=current,attention_mask=attn,past_key_values=cache,use_cache=True)
                cache=output.past_key_values;hidden=output.last_hidden_state[0,-1].to(torch.bfloat16)
                h=hidden.float().reshape(1,896);raw=engine(wg,h).cpu().numpy()[0];assert np.isfinite(raw).all()
                score=R.policy(raw[None,:],[np.array(sorted(seen),dtype='u4')])[0];winner=int(score.argmax())
                cutoff=np.partition(raw,-256)[-256];above=np.flatnonzero(raw>cutoff);tie=np.flatnonzero(raw==cutoff)
                ids=np.concatenate([above,tie[:256-len(above)]]);ids=ids[np.lexsort((ids,-raw[ids]))]
                hs.append(hidden.cpu().view(torch.uint16).numpy().copy());tops.append(ids.astype('u4'));winners.append(winner);scorebits.append(int(score[winner].view('u4')))
                if winner in eos:break
                seen.add(winner);current=torch.tensor([[winner]],device='cuda')
            np.savez_compressed(data,hidden_bf16=np.stack(hs).astype('<u2'),raw_top_ids=np.stack(tops),dense_token=np.array(winners,dtype='<u4'),dense_score_bits=np.array(scorebits,dtype='<u4'),input_ids=np.array(tokens,dtype='<u4'))
            item=dict(id=row['id'],category=row['category'],split='holdout',prompt_sha256=row['prompt_sha256'],group_sha256=row['group_sha256'],steps=len(winners),decode_steps=len(winners)-1,
              npz=data.name,npz_sha256=R.sha(data),generated_ids=winners,input_tokens=len(tokens),seconds=time.perf_counter()-start,
              scope='Canonical dense trajectory on fresh text; no task solution execution or board')
            R.write(meta,item);summaries.append(item)
            R.write(FOLDER/'PROGRESS.json',dict(state='RUNNING',completed=len(summaries),planned=1000,steps=sum(r['steps'] for r in summaries),elapsed_seconds=time.perf_counter()-started))
            if index%10==0 or index==999:R.progress('COLLECTING_NEW_FINAL_LABELS',prompts=index+1,total=1000,seconds=time.perf_counter()-started)
        summary=dict(state='PASS',split='holdout',prompts=1000,planned=1000,steps=sum(r['steps'] for r in summaries),decode_steps=sum(r['decode_steps'] for r in summaries),excluded_prompts=0,
          settings=settings,records=summaries,runtime_seconds=time.perf_counter()-started,gpu=torch.cuda.get_device_name())
        R.write(FOLDER/'MANIFEST.json',summary)
        R.write(R.OUT/'FINAL_LABEL_ACCESS.json',dict(state='FINAL_GROUP_OPENED_COLLECTION_COMPLETE',completed=R.now(),
          corpus_sha256=entry['corpus_sha256'],selection_lock_sha256=entry['selection_lock_sha256'],prompts=1000,predictions=summary['steps'],
          collection_manifest_sha256=R.sha(FOLDER/'MANIFEST.json'),retuning_prohibited=True))
        R.progress('FRESH_COLLECTION_COMPLETE',prompts=1000,predictions=summary['steps'])
    except Exception as exc:R.progress('STOPPED_ON_ERROR_OR_PAUSE',phase='fresh_collection',error=repr(exc));raise
    finally:
        if handle:handle.close();(R.OUT/'ACTIVE.lock').unlink(missing_ok=True)
if __name__=='__main__':main()
