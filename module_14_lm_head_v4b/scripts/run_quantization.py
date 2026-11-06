"""Authorized v4b offline study. Manual phases; stop at config/batch boundaries.

No board/network/EDA calls. Train/calibration only. Final labels are never read.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,json,math,os,shutil,sys,time,zlib,struct
os.environ.setdefault('OMP_NUM_THREADS','4')
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
os.environ.setdefault('MKL_NUM_THREADS','4')
import numpy as np
import torch
M=Path(__file__).resolve().parents[1];ROOT=M.parent;V4=ROOT/'module_14_lm_head_v4'
sys.path.insert(0,str(M));sys.path.insert(0,str(V4))
from reference.quality_data import load_split,assert_group_disjoint,assert_compatible_collections,recall_report
# Import v4b primitives by an unambiguous package file, despite the old reference namespace.
import importlib.util
def local(name):
    spec=importlib.util.spec_from_file_location('v4b_'+name,M/'reference'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
Q=local('quantization');CUDA=local('exact_cuda')
OUT=M/'reports/quantization_20261023_r1'
WEIGHT=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
CASES=['chinese','english','code','math']

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*2**20),b''):h.update(b)
    return h.hexdigest()
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def progress(stage,**info):
    d=dict(stage=stage,updated=now(),pid=os.getpid(),board='NOT_RUN',**info)
    write(OUT/'PROGRESS.json',d);print(json.dumps(d,ensure_ascii=False),flush=True)
def stop():
    if (OUT/'STOP_REQUESTED').exists():raise InterruptedError('STOP_REQUESTED at safe boundary')
def fp(bits):return (np.asarray(bits,dtype='u2').astype('u4')<<16).view('f4')
def gpu(a):return torch.from_numpy(np.ascontiguousarray(a,dtype='f4')).to('cuda')
def policy(raw,seen):
    result=np.array(raw,dtype='f4',copy=True)
    for i,ids in enumerate(seen):
        old=result[i,ids];result[i,ids]=np.where(old<0,np.multiply(old,np.float32(1.1),dtype='f4'),np.divide(old,np.float32(1.1),dtype='f4'))
    return result
def source_files():
    return [Path(__file__),M/'reference/quantization.py',M/'reference/exact_cuda.py',V4/'reference/quality_data.py']
def lock():
    return {p.relative_to(ROOT).as_posix():sha(p) for p in source_files()}
def checked():
    p=json.loads((OUT/'ENTRY_LOCK.json').read_text(encoding='utf-8'))
    assert p['sources']==lock(),'Execution source drift; preserve results and qualify new entry separately'
    assert sha(WEIGHT)==p['canonical_weight_sha256']
    return p
def fixtures():
    folder=V4/'reports/lowrank_fixture_20261021'
    manifest=json.loads((folder/'MANIFEST.json').read_text())
    result={}
    for cat in CASES:
        for suffix in ['hidden.bin','history.bin']:
            assert sha(folder/f'{cat}.{suffix}')==manifest['files'][f'{cat}.{suffix}']
        h=np.fromfile(folder/f'{cat}.hidden.bin',dtype='<u2');history=np.fromfile(folder/f'{cat}.history.bin',dtype='<u4')
        ids=np.arange(151936,dtype='u4');seen=ids[((history[ids>>5]>>(ids&31))&1)!=0]
        result[cat]=(fp(h),seen)
    return result
def data():
    train=load_split(V4/'data/hidden_v1/train');cal=load_split(V4/'data/hidden_v1/calibration')
    assert_group_disjoint(train,cal);assert_compatible_collections(train,cal)
    expected=[]
    for item in cal['manifest']['records']:
        assert 'excluded' not in item
        with np.load(V4/'data/hidden_v1/calibration'/item['npz'],allow_pickle=False) as a:expected.extend(a['dense_score_bits'])
    cal['expected_score_bits']=np.array(expected,dtype='u4')
    assert len(cal['hidden'])==5095 and cal['decode'].sum()==4775
    assert len(train['hidden'])==23933
    return train,cal
def statistics(hits,cal):return recall_report(hits,cal)
def qualified(quality):
    return quality['all']['misses']==0 and quality['decode']['recall']>=.999 and all(x['recall']>=.999 for x in quality['decode']['by_category'].values())

def preflight():
    assert not (OUT/'ENTRY_LOCK.json').exists(),'Inspect existing run; do not overwrite entry'
    assert sha(WEIGHT)=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    original=json.loads((M/'baseline/SOURCE_LOCK.json').read_text())
    for f in original['files']:assert sha(ROOT/f['source'])==f['sha256'] and sha(M/f['snapshot'])==f['sha256']
    model=V4/'data/model';model_lock=json.loads((model/'MODEL.lock.json').read_text())
    for f in model_lock['files']:assert sha(model/f['name'])==f['sha256'],f['name']
    train,cal=data()
    study=json.loads((M/'experiments/quantization_study/PLAN.json').read_text(encoding='utf-8'))
    points=[dict(id=f'RTN_W{b}_G{g}_{"S" if sym else "A"}',method='RTN',bits=b,group=g,symmetric=sym)
            for b in [12,8,6,4] for g in [32,64,128,896] for sym in [True,False]]
    plan=dict(format='M14_V4B_EXECUTION_PLAN_V1',created=now(),authorization='2026-10-23 user: 可以开展v4b方向的实验',
      scope='Local offline v4b phases, no board, no opened holdout retuning',research_plan_sha256=sha(M/'experiments/quantization_study/PLAN.json'),
      RTN=points,methods=dict(names=['RTN','GPTQ','AWQ_STYLE_HEAD_ONLY'],bits=[4,8],groups=[64,128],symmetric=False),
      refine=dict(bits=[4,8],group=128,symmetric=True,K=[512,2048,8192,16384,32768,151936]),
      gate=study['direct_gate'],train_manifest_sha256=train['manifest_sha256'],calibration_manifest_sha256=cal['manifest_sha256'],
      labels='old train/calibration only; no old holdout or new final labels read',
      evaluator='NVRTC exact H8/interleave16 evaluator; fitting and evaluation timing are not benchmark results')
    write(OUT/'PLAN.json',plan)
    entry=dict(created=now(),sources=lock(),plan_sha256=sha(OUT/'PLAN.json'),canonical_weight_sha256=sha(WEIGHT),
      model_lock_sha256=sha(model/'MODEL.lock.json'),gpu=torch.cuda.get_device_name(),torch=torch.__version__,
      train_groups=len(set(train['groups'])),calibration_groups=len(set(cal['groups'])),
      final_labels_opened=False,board='NOT_RUN')
    write(OUT/'ENTRY_LOCK.json',entry)
    engine=CUDA.ExactCuda(OUT/'cuda')
    w=fp(np.memmap(WEIGHT,dtype='<u2',mode='r',shape=(151936,896)));wg=gpu(w)
    trace=json.loads((ROOT/'artifacts/module14_v2_assets/manifest.json').read_text())['trace'];proof=[]
    for item in trace:
        stop();p=ROOT/'artifacts/module14_v2_assets/trace'/item['step']
        assert sha(p/'hidden.bf16.bin')==item['hidden_sha256'] and sha(p/'history_bitmap.u32.bin')==item['history_sha256']
        h=fp(np.fromfile(p/'hidden.bf16.bin',dtype='<u2'))
        actual=engine(wg,gpu(h[None,:])).cpu().numpy()[0]
        assert hashlib.sha256(actual.astype('<f4').tobytes()).hexdigest()==item['raw_logits_sha256'],item['step']
        history=np.fromfile(p/'history_bitmap.u32.bin',dtype='<u4');ids=np.arange(151936,dtype='u4');seen=ids[((history[ids>>5]>>(ids&31))&1)!=0]
        score=policy(actual[None,:],[seen])[0];token=int(np.argmax(score));bits=int(score[token].view('u4'))
        assert hashlib.sha256(score.astype('<f4').tobytes()).hexdigest()==item['processed_scores_sha256']
        assert token==item['selected_token'] and bits==item['selected_score_bits']
        assert zlib.crc32(struct.pack('<II',token,bits))==item['output_crc']
        proof.append(dict(case=item['step'],full_raw_sha=True,full_policy_sha=True,token=token,score_bits=bits,crc=item['output_crc']))
        progress('BASELINE_ARCHIVE_PROOF',case=item['step'])
    for name,(h,seen) in fixtures().items():
        cpu=Q.raw_fp32(h,w);actual=engine(wg,gpu(h[None,:])).cpu().numpy()[0]
        np.testing.assert_array_equal(actual.view('u4'),cpu.view('u4'))
        np.testing.assert_array_equal(policy(actual[None,:],[seen]).view('u4'),policy(cpu[None,:],[seen]).view('u4'))
        proof.append(dict(case=name,full_raw_cpu_gpu_bit_match=True,penalty_off_on=True,values=151936))
    # Signed/unsigned non-byte-aligned formats and exact RNE boundary cases.
    crafted=np.zeros((5,896),dtype='f4');crafted[1]=np.linspace(-1,1,896,dtype='f4');crafted[2]=1;crafted[3]=-1;crafted[4]=np.tile(np.array([.5,1.5,2.5,-.5,-1.5,-2.5,0,3],dtype='f4'),112)
    boundary=[]
    for b in [4,6,8,12]:
      for g in [32,64,128,896]:
       for sym in [True,False]:
        q,s,z,deq=Q.quantize(crafted,b,g,sym);p=OUT/'boundary.bin';Q.pack(p,q,s,z,b,g,sym)
        _,uq,us,uz,ud=Q.unpack(p)
        np.testing.assert_array_equal(q,uq);np.testing.assert_array_equal(s.view('u4'),us.view('u4'));np.testing.assert_array_equal(z,uz);np.testing.assert_array_equal(deq.view('u4'),ud.view('u4'))
        boundary.append(dict(bits=b,group=g,symmetric=sym,pass_pack=True))
    write(OUT/'Q01_BASELINE.json',dict(state='PASS_BASELINE_ARCHIVE_AND_FOUR_FIXTURES',cases=proof,quantization_format_boundaries=boundary,
      cuda_options=engine.options,scope='Software arithmetic and packing proof, no new Csim/RTL/board result'))
    # Independently regenerate every dense calibration label and cache complete raw arrays.
    rawpath=OUT/'dense_calibration.raw.f32';raw=np.memmap(rawpath,dtype='<f4',mode='w+',shape=(len(cal['hidden']),151936))
    tokens=[];scorebits=[];margins=[];hg=gpu(fp(cal['hidden']))
    for start in range(0,len(hg),32):
        stop();end=min(start+32,len(hg));batch=engine(wg,hg[start:end]).cpu().numpy();raw[start:end]=batch
        score=policy(batch,cal['seen'][start:end]);token=score.argmax(axis=1);bits=score[np.arange(len(score)),token].view('u4')
        np.testing.assert_array_equal(token,cal['winner'][start:end]);np.testing.assert_array_equal(bits,cal['expected_score_bits'][start:end])
        top=np.partition(score,-2,axis=1)[:,-2:];margins.extend((top[:,1]-top[:,0]).tolist());tokens.extend(token.tolist());scorebits.extend(bits.tolist())
        if start%512==0 or end==len(hg):progress('DENSE_CALIBRATION_PROOF',done=end,total=len(hg))
    raw.flush();del raw
    np.savez_compressed(OUT/'dense_calibration.npz',token=np.array(tokens,dtype='u4'),score_bits=np.array(scorebits,dtype='u4'),margin=np.array(margins,dtype='f4'))
    write(OUT/'DENSE_CALIBRATION.json',dict(state='PASS_ALL_5095_LABELS_AND_SCORE_BITS',predictions=5095,decode=4775,
      arrays_sha256=sha(OUT/'dense_calibration.npz'),raw_sha256=sha(rawpath),bytes=rawpath.stat().st_size))
    progress('PREFLIGHT_COMPLETE',archive_steps=8,fixtures=4,calibration_predictions=5095)

def evaluate_point(config,w,cal,engine,extra=None):
    stop();key=config['id'];dest=OUT/'points'/key;dest.mkdir(parents=True,exist_ok=True)
    if (dest/'RESULT.json').exists():
        result=json.loads((dest/'RESULT.json').read_text());assert result['entry_lock_sha256']==sha(OUT/'ENTRY_LOCK.json')
        assert sha(dest/'outcomes.npz')==result['outcomes_sha256'] and sha(dest/'weights.bin')==result['packed_sha256']
        return result
    progress('QUANTIZING_POINT',config=key);started=time.perf_counter()
    if extra is None:q,s,z,deq=Q.quantize(w,config['bits'],config['group'],config['symmetric'])
    else:q,s,z,deq=extra['q'],extra['scale'],extra['zero'],extra['deq']
    packing=Q.pack(dest/'weights.bin',q,s,z,config['bits'],config['group'],config['symmetric'])
    _,q2,s2,z2,d2=Q.unpack(dest/'weights.bin')
    np.testing.assert_array_equal(q,q2);np.testing.assert_array_equal(s.view('u4'),s2.view('u4'));np.testing.assert_array_equal(z,z2);np.testing.assert_array_equal(deq.view('u4'),d2.view('u4'))
    del q2,s2,z2,d2
    qg=gpu(deq);transform=None if extra is None else extra.get('channel_scale')
    h=fp(cal['hidden']);h=h if transform is None else np.divide(h,transform,dtype='f4')
    hg=gpu(h);proof=[]
    for name,(fixture_h,seen) in fixtures().items():
        fixture_h=fixture_h if transform is None else np.divide(fixture_h,transform,dtype='f4')
        cpu=Q.raw_fp32(fixture_h,deq);actual=engine(qg,gpu(fixture_h[None,:])).cpu().numpy()[0]
        np.testing.assert_array_equal(cpu.view('u4'),actual.view('u4'))
        score=policy(actual[None,:],[seen])[0];token=int(score.argmax());bits=int(score[token].view('u4'))
        # Save complete arrays for independent post-run verification.
        np.savez_compressed(dest/f'{name}.npz',raw=actual,token=np.array(token,dtype='u4'),score_bits=np.array(bits,dtype='u4'))
        proof.append(dict(case=name,full_cpu_gpu_raw_bits=True,values=151936,token=token,score_bits=bits,crc=zlib.crc32(struct.pack('<II',token,bits))))
    n=len(hg);tokens=np.empty(n,dtype='u4');bits=np.empty(n,dtype='u4');ranks=np.empty(n,dtype='u4')
    maxerr=0.;squared=0.;count=0;dense=np.memmap(OUT/'dense_calibration.raw.f32',dtype='<f4',mode='r',shape=(n,151936));ids=np.arange(151936,dtype='u4')
    for start in range(0,n,32):
        stop();end=min(start+32,n);raw=engine(qg,hg[start:end]).cpu().numpy();assert np.isfinite(raw).all()
        delta=raw-dense[start:end];maxerr=max(maxerr,float(np.abs(delta).max()));squared+=float(np.sum(delta.astype('f8')**2));count+=delta.size
        score=policy(raw,cal['seen'][start:end]);token=score.argmax(axis=1);tokens[start:end]=token;bits[start:end]=score[np.arange(len(score)),token].view('u4')
        target=score[np.arange(len(score)),cal['winner'][start:end]]
        rank=(score>target[:,None]).sum(axis=1)+((score==target[:,None])&(ids[None,:]<cal['winner'][start:end,None])).sum(axis=1)
        ranks[start:end]=rank
        if start%512==0 or end==n:progress('CALIBRATING_POINT',config=key,done=end,total=n,elapsed_seconds=time.perf_counter()-started)
    hits=tokens==cal['winner'];quality=statistics(hits,cal)
    np.savez_compressed(dest/'outcomes.npz',token=tokens,score_bits=bits,hits=hits,policy_dense_winner_rank=ranks)
    if transform is not None:np.save(dest/'channel_scale.npy',transform,allow_pickle=False)
    result=dict(**config,state='COMPLETE_CALIBRATION_ONLY',entry_lock_sha256=sha(OUT/'ENTRY_LOCK.json'),
      quality=quality,conservative_calibration_gate=qualified(quality),packing=packing,
      packed_bytes=(dest/'weights.bin').stat().st_size,packed_sha256=sha(dest/'weights.bin'),
      outcomes_sha256=sha(dest/'outcomes.npz'),cpu_gpu_proof=proof,
      logit_error=dict(max_absolute=maxerr,rmse=math.sqrt(squared/count)),
      runtime_seconds=time.perf_counter()-started,
      transform=None if transform is None else dict(sha256=sha(dest/'channel_scale.npy'),online='FP32 h/s before accepted dot; included in method definition'),
      fitting=None if extra is None else extra.get('fitting'),
      scope='Old calibration only; elapsed is job time, not inference benchmark or FPGA speed')
    write(dest/'RESULT.json',result)
    progress('POINT_COMPLETE',config=key,misses=quality['decode']['misses'],all_misses=quality['all']['misses'],gate=result['conservative_calibration_gate'])
    del qg,hg;torch.cuda.empty_cache();return result

def rtn():
    checked();assert json.loads((OUT/'DENSE_CALIBRATION.json').read_text())['state'].startswith('PASS')
    _,cal=data();plan=json.loads((OUT/'PLAN.json').read_text());engine=CUDA.ExactCuda(OUT/'cuda')
    w=fp(np.memmap(WEIGHT,dtype='<u2',mode='r',shape=(151936,896)));results=[]
    for config in plan['RTN']:
        results.append(evaluate_point(config,w,cal,engine));write(OUT/'RTN_CALIBRATION.partial.json',dict(configurations=results))
    write(OUT/'RTN_CALIBRATION.json',dict(state='COMPLETE_32_POINTS_CALIBRATION_NOT_FINAL',configurations=results,
      qualified=[r['id'] for r in results if r['conservative_calibration_gate']]))
    progress('RTN_COMPLETE',points=32,qualified=sum(r['conservative_calibration_gate'] for r in results))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['preflight','rtn'],required=True);args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=4*2**30
    lockpath=OUT/'ACTIVE.lock';handle=None
    try:
        handle=lockpath.open('x');handle.write(json.dumps(dict(pid=os.getpid(),started=now(),phase=args.phase)));handle.flush()
        stop();preflight() if args.phase=='preflight' else rtn()
    except Exception as exc:
        progress('STOPPED_ON_ERROR_OR_PAUSE',phase=args.phase,error=repr(exc));raise
    finally:
        if handle:handle.close();lockpath.unlink(missing_ok=True)

if __name__=='__main__':main()
