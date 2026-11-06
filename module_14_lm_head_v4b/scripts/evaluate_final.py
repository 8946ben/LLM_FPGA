"""Once-only evaluation of frozen selections on fresh canonical trajectories."""
from pathlib import Path
import json,os,struct,zlib
import run_quantization as R
from collect_final import guards
import numpy as np
import torch
P=R.local('packed_cuda')

def gate(q):return q['decode']['recall']>=.999 and all(x['recall']>=.999 for x in q['decode']['by_category'].values())

@torch.inference_mode()
def main():
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    entry=guards();R.stop();assert not (R.OUT/'FINAL_QUALITY.json').exists(),'Do not rerun an opened completed final group'
    handle=None
    try:
        handle=(R.OUT/'ACTIVE.lock').open('x');handle.write(json.dumps(dict(pid=os.getpid(),phase='final_quality',started=R.now())));handle.flush()
        folder=R.M/'data/hidden_final_20261023/holdout';data=R.load_split(folder)
        assert len(set(data['groups']))==1000 and data['manifest']['excluded_prompts']==0
        expected=[]
        for item in data['manifest']['records']:
            with np.load(folder/item['npz'],allow_pickle=False) as a:expected.extend(a['dense_score_bits'])
        expected=np.array(expected,dtype='u4');n=len(expected)
        weights=torch.from_numpy(np.fromfile(R.WEIGHT,dtype='<u2').reshape(151936,896)).view(torch.bfloat16).to('cuda')
        dense_engine=P.PackedCuda(R.OUT/'cuda/packed_dense');h=R.gpu(R.fp(data['hidden']))
        # Verify the independent packed BF16 path against every newly collected token/score.
        for start in range(0,n,32):
            R.stop();end=min(start+32,n);raw=dense_engine(weights,h[start:end],151936).cpu().numpy()
            score=R.policy(raw,data['seen'][start:end]);token=score.argmax(axis=1);bits=score[np.arange(len(score)),token].view('u4')
            np.testing.assert_array_equal(token,data['winner'][start:end]);np.testing.assert_array_equal(bits,expected[start:end])
            if start%1024==0:R.progress('FINAL_DENSE_REFERENCE_PROOF',done=end,total=n)
        selection=json.loads((R.OUT/'SELECTION_LOCK.json').read_text());results=[]
        for selected in selection['selected']:
            R.stop();key=selected['source'];point=R.OUT/'points'/key;info=json.loads((point/'RESULT.json').read_text())
            assert R.sha(point/'weights.bin')==selected['packed_sha256']
            packed=torch.from_numpy(np.fromfile(point/'weights.bin',dtype='u1')).to('cuda')
            engine=P.PackedCuda(R.OUT/'cuda'/('packed_'+key),info['packing'])
            transformed=h
            if info['transform'] is not None:
                s=np.load(point/'channel_scale.npy',allow_pickle=False);assert R.sha(point/'channel_scale.npy')==selected['channel_scale_sha256']
                transformed=R.gpu(np.divide(R.fp(data['hidden']),s,dtype='f4'))
            tokens=np.empty(n,dtype='u4');scorebits=np.empty(n,dtype='u4');ranks=np.empty(n,dtype='u4')
            ids_all=np.arange(151936,dtype='u4')
            for start in range(0,n,32):
                R.stop();end=min(start+32,n);raw=engine(packed,transformed[start:end],151936).cpu().numpy();assert np.isfinite(raw).all()
                score=R.policy(raw,data['seen'][start:end]);target=score[np.arange(len(score)),data['winner'][start:end]]
                rank=(score>target[:,None]).sum(axis=1)+((score==target[:,None])&(ids_all[None,:]<data['winner'][start:end,None])).sum(axis=1)
                ranks[start:end]=rank
                if selected['kind']=='direct':
                    token=score.argmax(axis=1);tokens[start:end]=token;scorebits[start:end]=score[np.arange(len(score)),token].view('u4')
                else:
                    k=selected['K']
                    for row in range(len(score)):
                        cutoff=np.partition(score[row],-k)[-k];above=np.flatnonzero(score[row]>cutoff);ties=np.flatnonzero(score[row]==cutoff)
                        chosen=np.sort(np.concatenate([above,ties[:k-len(above)]]));assert len(chosen)==k
                        ids=torch.from_numpy(chosen.astype('i8')).to('cuda');candidate_weights=weights[ids].contiguous()
                        exact=dense_engine(candidate_weights,h[start+row:start+row+1],k).cpu().numpy()[0]
                        seen=np.isin(chosen,data['seen'][start+row]);old=exact[seen]
                        exact[seen]=np.where(old<0,old*np.float32(1.1),old/np.float32(1.1))
                        slot=int(exact.argmax());tokens[start+row]=chosen[slot];scorebits[start+row]=exact[slot].view('u4')
                if start%512==0 or end==n:R.progress('EVALUATING_FRESH_FINAL',method=selected['id'],done=end,total=n)
            hits=tokens==data['winner'];quality=R.statistics(hits,data)
            if selected['kind']=='refine':
                np.testing.assert_array_equal(hits,ranks<selected['K']);np.testing.assert_array_equal(scorebits[hits],expected[hits])
            path=R.OUT/'final_outcomes'/f'{selected["id"]}.npz';path.parent.mkdir(exist_ok=True)
            np.savez_compressed(path,token=tokens,score_bits=scorebits,hits=hits,policy_dense_winner_rank=ranks)
            errors=[]
            for i in np.flatnonzero(~hits):
                errors.append(dict(index=int(i),prompt_id=str(data['prompt_ids'][i]),group=str(data['groups'][i]),category=str(data['category'][i]),decode=bool(data['decode'][i]),
                  dense_token=int(data['winner'][i]),actual_token=int(tokens[i]),dense_score_bits=int(expected[i]),actual_score_bits=int(scorebits[i]),preview_dense_winner_rank=int(ranks[i])))
            results.append(dict(**selected,quality=quality,quality_gate=gate(quality),errors=errors,
              arrays=path.relative_to(R.OUT).as_posix(),arrays_sha256=R.sha(path),
              scope='All fresh predictions actually executed through packed preview/direct and BF16 candidate pipeline; fixed dense trajectories, not free generation'))
            del packed,transformed;torch.cuda.empty_cache()
        final=dict(state='PASS_FINAL_POINT_GATES_NOT_RELEASED' if all(r['quality_gate'] for r in results) else 'QUALITY_FAIL_PRESERVE_NO_RETUNE',
          created=R.now(),prompts=1000,predictions=n,decode_predictions=int(data['decode'].sum()),excluded_prompts=0,
          selection_lock_sha256=R.sha(R.OUT/'SELECTION_LOCK.json'),evaluation_entry_sha256=R.sha(R.M/'data/final_quality_20261023/EVALUATION_ENTRY_LOCK.json'),
          collection_manifest_sha256=data['manifest_sha256'],canonical_weight_sha256=R.sha(R.WEIGHT),
          dense_reference='All fresh token and score bits verified by separate packed BF16 kernel',results=results,
          nll_natural_text='NOT_RUN',closed_loop_generation='NOT_RUN',hls='NOT_RUN',rtl='NOT_RUN',board='NOT_RUN',
          limitation='Conditional head token agreement, not semantic/task correctness or mathematical losslessness. Opened final group must not be used to retune/re-certify.')
        R.write(R.OUT/'FINAL_QUALITY.json',final);R.progress('FINAL_QUALITY_COMPLETE',state=final['state'],predictions=n)
    except Exception as exc:R.progress('STOPPED_ON_ERROR_OR_PAUSE',phase='final_quality',error=repr(exc));raise
    finally:
        if handle:handle.close();(R.OUT/'ACTIVE.lock').unlink(missing_ok=True)
if __name__=='__main__':main()
