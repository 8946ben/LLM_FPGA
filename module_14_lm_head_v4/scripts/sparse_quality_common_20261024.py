"""Isolated fresh-quality run utilities. No EDA, target or network access."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,importlib.util,json,os,sys
import numpy as np
M=Path(__file__).resolve().parents[1];ROOT=M.parent;V4=M
DATA=M/'data/sparse_quality_20261024'
OUT=M/'reports/sparse_quality_20261024_r1'
WEIGHT=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
CUDA_FILE=ROOT/'module_14_lm_head_v4b/reference/exact_cuda.py'
sys.path.insert(0,str(M))
spec=importlib.util.spec_from_file_location('_sparse_quality_exact_cuda',CUDA_FILE)
CUDA=importlib.util.module_from_spec(spec);spec.loader.exec_module(CUDA)

def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(p)
def progress(stage,**kw):
    d=dict(stage=stage,updated=now(),pid=os.getpid(),board='NOT_RUN',eda='NOT_RUN',**kw)
    write(OUT/'PROGRESS.json',d);print(json.dumps(d,ensure_ascii=False),flush=True)
def stop():
    if (OUT/'STOP_REQUESTED').exists():raise InterruptedError('STOP at prompt/config boundary')
def checked():
    entry=read(DATA/'EVALUATION_ENTRY_LOCK.json')
    assert sha(DATA/'holdout.jsonl')==entry['corpus_sha256']
    assert sha(OUT/'SELECTION_LOCK.json')==entry['selection_lock_sha256']
    for p,h in entry['sources'].items():assert sha(ROOT/p)==h,p
    return entry
def fp(x):return (np.asarray(x,dtype='u2').astype('u4')<<16).view('f4')
def gpu(x):
    import torch
    return torch.from_numpy(np.ascontiguousarray(x)).to('cuda')
def policy(raw,seen):
    a=raw.copy();p=np.float32(1.1)
    for i,ids in enumerate(seen):
        old=a[i,ids];a[i,ids]=np.where(old<0,np.multiply(old,p,dtype=np.float32),np.divide(old,p,dtype=np.float32))
    return a
def validate_dense(engine,wg):
    import torch
    manifest=read(ROOT/'artifacts/module14_v2_assets/manifest.json');rows=[]
    for g in manifest['trace']:
        p=ROOT/'artifacts/module14_v2_assets/trace'/g['step']
        h=np.fromfile(p/'hidden.bf16.bin',dtype='<u2');raw=engine(wg,gpu(fp(h)[None,:])).cpu().numpy()[0]
        assert hashlib.sha256(raw.astype('<f4').tobytes()).hexdigest()==g['raw_logits_sha256']
        bitmap=np.fromfile(p/'history_bitmap.u32.bin',dtype='<u4');ids=np.arange(151936,dtype='u4');seen=ids[((bitmap[ids>>5]>>(ids&31))&1)!=0]
        scores=policy(raw[None,:],[seen])[0]
        assert hashlib.sha256(scores.astype('<f4').tobytes()).hexdigest()==g['processed_scores_sha256']
        assert int(scores.argmax())==g['selected_token'] and int(scores[g['selected_token']].view('u4'))==g['selected_score_bits']
        rows.append(dict(step=g['step'],raw_sha256=g['raw_logits_sha256'],policy_sha256=g['processed_scores_sha256']))
    write(OUT/'DENSE_BASELINE_REVIEW.json',dict(state='PASS_ARCHIVED8_FULL_RAW_POLICY_BITS',records=rows,backend_sha256=sha(CUDA_FILE)))
