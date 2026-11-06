"""Bounded head-only GPTQ and AWQ-style study; no final labels or board calls."""
from pathlib import Path
import hashlib,json,os,time
import run_quantization as R
import numpy as np
import torch

def train_partition(train):
    fit=[];validation=[];groups=[]
    for cat in R.CASES:
        candidates=sorted(set(train['groups'][train['category']==cat]))
        count=max(1,int(len(candidates)*.8));selected=set(candidates[:count]);groups.extend(candidates[count:])
        fit.extend(np.flatnonzero((train['category']==cat)&np.isin(train['groups'],list(selected))).tolist())
        held=np.flatnonzero((train['category']==cat)&~np.isin(train['groups'],list(selected)))
        held=sorted(held,key=lambda i:(train['groups'][i],i))
        validation.extend(held[:64])
    assert len(validation)==256 and not set(train['groups'][fit])&set(train['groups'][validation])
    return np.array(fit),np.array(validation)

@torch.inference_mode()
def gptq(w,hessian,bits,group):
    start=time.perf_counter();scale,zero=R.Q.parameters(w,bits,group,False)
    W=R.gpu(w).clone();S=R.gpu(scale);Z=torch.from_numpy(zero).to(device='cuda',dtype=torch.float32)
    H=hessian.clone();dead=torch.diag(H)==0
    if bool(dead.any()):raise ValueError('Zero training Hessian diagonal; no silent dead-channel substitution')
    damp=torch.diag(H).mean()*.01;diag=torch.arange(896,device='cuda');H[diag,diag]+=damp
    chol=torch.linalg.cholesky(H);inverse=torch.cholesky_inverse(chol);upper=torch.linalg.cholesky(inverse,upper=True)
    assert bool(torch.isfinite(upper).all())
    codes=torch.empty(W.shape,dtype=torch.int16,device='cuda')
    for block_start in range(0,896,128):
        R.stop();end=block_start+128;part=W[:,block_start:end].clone();errors=torch.empty_like(part)
        U=upper[block_start:end,block_start:end]
        for j in range(128):
            col=block_start+j;g=col//group;before=part[:,j].clone()
            code=torch.clamp(torch.round(before/S[:,g])+Z[:,g],0,(1<<bits)-1)
            quant=(code-Z[:,g])*S[:,g];codes[:,col]=code.to(torch.int16)
            err=(before-quant)/U[j,j];errors[:,j]=err
            part[:,j:]-=err[:,None]*U[j,j:][None,:]
        if end<896:W[:,end:]-=errors@upper[block_start:end,end:]
        R.progress('GPTQ_FITTING',bits=bits,group=group,columns=end,total=896)
    q=codes.cpu().numpy().reshape(len(w),896//group,group)
    deq=np.multiply(q.astype('f4')-zero[:,:,None].astype('f4'),scale[:,:,None],dtype='f4').reshape(len(w),896)
    torch.cuda.synchronize()
    fit=dict(algorithm='GPTQ head-only static-grid block128',damp_fraction=.01,damp_value=float(damp.item()),act_order=False,
      static_groups=True,training='all old train1500 hidden rows; no calibration hidden',
      hessian='2/N X^T X FP32; TF32 disabled; FP32 Cholesky inverse upper factor',
      dead_channels=int(dead.sum()),seconds=time.perf_counter()-start,
      source_reference='https://github.com/IST-DASLab/gptq/blob/main/gptq.py',
      adaptation='New independent head-only implementation, no Transformer/embedding quantization; no BF16 rounding of reconstructed W')
    del W,S,Z,H,chol,inverse,upper,codes,part,errors;torch.cuda.empty_cache()
    return dict(q=q,scale=scale,zero=zero,deq=deq,fitting=fit)

@torch.inference_mode()
def awq(w,train,fit_indices,val_indices,bits,group):
    start=time.perf_counter();x=R.fp(train['hidden']);mean=np.mean(np.abs(x[fit_indices]),axis=0,dtype='f8').astype('f4')
    assert np.all(mean>0)
    validation=R.gpu(x[val_indices]);wg=R.gpu(w)
    target=validation@wg.T
    losses=[];best=None
    for alpha in [0,.25,.5,.75,1]:
        R.stop();s=np.maximum(np.power(mean,np.float32(alpha)),np.float32(1e-4)).astype('f4')
        s=np.divide(s,np.sqrt(np.float32(s.max()*s.min())),dtype='f4')
        changed=np.multiply(w,s,dtype='f4');q,scale,zero,deq=R.Q.quantize(changed,bits,group,False)
        # Candidate selection is wholly inside training, using FP32 GEMM reconstruction loss.
        # Evaluation later uses the accepted non-FMA arithmetic and an explicit FP32 h/s.
        val_scaled=R.gpu(np.divide(x[val_indices],s,dtype='f4'))
        dqg=R.gpu(deq);pred=val_scaled@dqg.T
        loss=float(torch.mean((pred-target).square(),dtype=torch.float32).item())
        losses.append(dict(alpha=alpha,mse=loss));R.progress('AWQ_TRAINING_INNER_SEARCH',bits=bits,group=group,alpha=alpha,mse=loss)
        if best is None or loss<best['loss']:
            best=dict(loss=loss,alpha=alpha,channel_scale=s.copy())
        del changed,q,scale,zero,deq,val_scaled,dqg,pred;torch.cuda.empty_cache()
    s=best['channel_scale'];q,scale,zero,deq=R.Q.quantize(np.multiply(w,s,dtype='f4'),bits,group,False)
    fit=dict(algorithm='AWQ-style head-only activation scaling (not full official AWQ pipeline)',
      alpha=best['alpha'],candidates=losses,clipping_search=False,scale_formula='s=clamp(mean_abs_h**alpha,1e-4)/sqrt(max(s)*min(s))',
      train_fit_rows=len(fit_indices),train_validation_rows=len(val_indices),group_split='per category sorted prompt-group SHA 80/20; no crossing groups',
      validation_selection='first64 hidden rows per category by group SHA then step',
      training_loss='FP32 GEMM logit MSE only within training; no calibration/final labels',
      seconds=time.perf_counter()-start,source_reference='https://github.com/mit-han-lab/llm-awq/blob/main/awq/quantize/auto_scale.py',
      online='FP32 h/s; weight reconstructed in FP32, no upstream scale absorption')
    del target,wg,validation;torch.cuda.empty_cache()
    return dict(q=q,scale=scale,zero=zero,deq=deq,channel_scale=s,fitting=fit)

def main():
    R.OUT.mkdir(parents=True,exist_ok=True);torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    R.checked();R.stop();assert (R.OUT/'RTN_CALIBRATION.json').exists(),'Finish the bounded RTN sweep before methods'
    entry_path=R.OUT/'METHODS_ENTRY_LOCK.json'
    current=dict(source_sha256=R.sha(Path(__file__)),core_entry_sha256=R.sha(R.OUT/'ENTRY_LOCK.json'),
      method_protocol=dict(GPTQ=dict(bits=[4,8],groups=[64,128],damp=.01,block=128,static_grid=True,act_order=False),
        AWQ_STYLE=dict(bits=[4,8],groups=[64,128],alphas=[0,.25,.5,.75,1],train_group_split='per-category sorted SHA 80/20',inner_validation_rows_per_category=64,clipping=False)),
      final_labels_opened=False)
    if entry_path.exists():assert json.loads(entry_path.read_text())==current
    else:R.write(entry_path,current)
    handle=None
    try:
        handle=(R.OUT/'ACTIVE.lock').open('x');handle.write(json.dumps(dict(pid=os.getpid(),phase='methods',started=R.now())));handle.flush()
        train,cal=R.data();fit_idx,val_idx=train_partition(train)
        R.write(R.OUT/'TRAIN_INNER_SPLIT.json',dict(fit_indices=fit_idx.tolist(),validation_indices=val_idx.tolist(),
          fit_prompt_groups=len(set(train['groups'][fit_idx])),validation_prompt_groups=len(set(train['groups'][val_idx])),
          train_manifest_sha256=train['manifest_sha256'],calibration_used_for_fitting=False))
        x=R.gpu(R.fp(train['hidden']));hessian=(x.T@x)*np.float32(2/len(x));del x
        np.save(R.OUT/'train_hessian.npy',hessian.cpu().numpy(),allow_pickle=False)
        w=R.fp(np.memmap(R.WEIGHT,dtype='<u2',mode='r',shape=(151936,896)));engine=R.CUDA.ExactCuda(R.OUT/'cuda');results=[]
        for bits in [4,8]:
          for group in [64,128]:
            control=json.loads((R.OUT/f'points/RTN_W{bits}_G{group}_A/RESULT.json').read_text());results.append(control)
            for method in ['GPTQ','AWQ_STYLE']:
                R.stop();key=f'{method}_W{bits}_G{group}_A';dest=R.OUT/'points'/key
                if (dest/'RESULT.json').exists():
                    result=json.loads((dest/'RESULT.json').read_text());assert R.sha(dest/'outcomes.npz')==result['outcomes_sha256']
                else:
                    extra=gptq(w,hessian,bits,group) if method=='GPTQ' else awq(w,train,fit_idx,val_idx,bits,group)
                    result=R.evaluate_point(dict(id=key,method=method,bits=bits,group=group,symmetric=False),w,cal,engine,extra)
                    del extra
                results.append(result);R.write(R.OUT/'METHODS_CALIBRATION.partial.json',dict(configurations=results))
        R.write(R.OUT/'METHODS_CALIBRATION.json',dict(state='COMPLETE_8_NEW_4_CONTROLS_CALIBRATION_ONLY',configurations=results,
          entry_sha256=R.sha(entry_path),qualified=[r['id'] for r in results if r['conservative_calibration_gate']]))
        R.progress('METHODS_COMPLETE',new_points=8,controls=4)
    except Exception as exc:R.progress('STOPPED_ON_ERROR_OR_PAUSE',phase='methods',error=repr(exc));raise
    finally:
        if handle:handle.close();(R.OUT/'ACTIVE.lock').unlink(missing_ok=True)

if __name__=='__main__':main()
