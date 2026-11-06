"""Finish16 hash points; preserve the first52 and the failed NumPy-index run.

Only correction: explicitly uint32 codes, masks and table offsets. NumPy uint64
plus int64 can promote to float64, which is not a valid bitmap index.
"""
from pathlib import Path
import json,os,sys
import numpy as np
import torch
import run_sparse_methods_20261024 as q
s=q.s;R=q.R;b=q.b
def main():
    torch.set_num_threads(4);torch.set_grad_enabled(False)
    assert not (R/'ACTIVE.lock').exists() and not (R/'CALIBRATION.json').exists()
    original=s.read(R/'PLAN.json');assert all(b.sha(b.ROOT/p)==h for p,h in original['source_sha256'].items())
    previous=s.read(R/'CALIBRATION.partial.json')['configurations'];assert len(previous)==52 and not any(p['mode']=='lsh' for p in previous)
    dest=R/'resume_lsh_r2';dest.mkdir(exist_ok=True)
    assert not (dest/'ENTRY_LOCK.json').exists(),'Do not overwrite a prior resume'
    b.write(dest/'FAILED_PROGRESS.json',s.read(R/'PROGRESS.json'))
    b.write(dest/'ENTRY_LOCK.json',dict(script_sha256=b.sha(__file__),frozen_plan_sha256=b.sha(R/'PLAN.json'),first52_partial_sha256=b.sha(R/'CALIBRATION.partial.json'),parameters_sha256=b.sha(R/'PARAMETERS.json'),correction='Cast all hash bucket index arithmetic to uint32; no selector/model/calibration inputs or previous52 arrays changed',first52_arrays={p['arrays']:p['sha256'] for p in previous}))
    b.write(R/'ACTIVE.lock',dict(pid=os.getpid(),started=b.now(),phase='resume_lsh16_host_index_dtype_fix'))
    try:
        cal=q.load_split(b.M/'data/hidden_v1/calibration');h=b.fp(cal['hidden']);n=len(h);parameters=s.read(R/'PARAMETERS.json')['files'];lut=np.array([i.bit_count() for i in range(256)],dtype='u1');special=np.zeros(s.V,bool);special[s.SPECIAL]=True;mandatory=np.packbits(special,bitorder='little');fresh=[]
        for kind in ['angular','mips']:
            for nbits in [8,10]:
                q.stop();key=f'hash_{kind}_b{nbits}';cpu=b.load_model(R/parameters[key]['path']);scores=q.dot_batch_gpu(h,b.fp(cpu['planes_bf16']));sign=scores.cpu().numpy().reshape(-1,8,nbits)>=0
                codes=(sign.astype('u4')*(np.uint32(1)<<np.arange(nbits,dtype='u4'))).sum(axis=2,dtype=np.uint32);membership=q.bitmap(cpu,8*(1<<nbits))
                for pair in [p for p in s.configurations() if p['mode']=='lsh' and p['parameters']['kind']==kind and p['parameters']['b']==nbits]:
                    p=pair['parameters'];masks=np.array([0]+([1<<j for j in range(nbits)] if p['radius'] else []),'u4');hits=np.empty(n,bool);ks=np.empty(n,'u4')
                    for i in range(n):
                        if i%256==0:q.stop()
                        groups=((codes[i,:p['tables'],None]^masks[None,:])+np.arange(p['tables'],dtype='u4')[:,None]*np.uint32(1<<nbits)).reshape(-1)
                        assert groups.dtype==np.uint32
                        union=np.bitwise_or.reduce(membership[groups],axis=0)|mandatory;ks[i]=lut[union].sum();w=int(cal['winner'][i]);hits[i]=bool((union[w//8]>>(w%8))&1)
                    path=R/f'coverage/{pair["id"]}.npz';assert not path.exists();np.savez_compressed(path,hits=hits,k=ks)
                    row=dict(**pair,quality=q.recall_report(hits,cal),candidate_decode=b.count_stats(ks[cal['decode']]),candidate_all=b.count_stats(ks),arrays=path.relative_to(R).as_posix(),sha256=b.sha(path),fallback_decode=0);fresh.append(row)
                    b.write(dest/'LSH_CALIBRATION.partial.json',dict(configurations=fresh));q.progress('RESUMED_LSH_CALIBRATION',id=pair['id'],completed=52+len(fresh),total=68)
                del membership,cpu,scores
        assert len(fresh)==16
        assert all(b.sha(R/p['arrays'])==p['sha256'] for p in previous)
        b.write(dest/'LSH_CALIBRATION.json',dict(state='COMPLETE16_HASH_HOST_DTYPE_CORRECTED',configurations=fresh,entry_sha256=b.sha(dest/'ENTRY_LOCK.json')))
        b.write(R/'CALIBRATION.json',dict(state='COMPLETE68_EXPLORATORY_CALIBRATION_NOT_FINAL',configurations=previous+fresh,calibration_manifest_sha256=cal['manifest_sha256'],plan_sha256=b.sha(R/'PLAN.json'),parameters_sha256=b.sha(R/'PARAMETERS.json'),resume_entry_sha256=b.sha(dest/'ENTRY_LOCK.json'),prior_failure_preserved=True));q.progress('CALIBRATION_COMPLETE',configurations=68)
    finally:(R/'ACTIVE.lock').unlink(missing_ok=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:q.progress('RESUME_STOPPED_NO_COMPLETION_VERDICT',error=repr(e));raise
