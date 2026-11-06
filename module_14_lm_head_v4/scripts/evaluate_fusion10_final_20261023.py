"""One frozen selected-point + original-baseline fresh quality audit, no fit."""
from pathlib import Path
import hashlib,json,math,sys,time
import numpy as np
import torch
import fusion_experiment10_20261023 as e
from reference.quality_data import load_split,recall_report,assert_group_disjoint
M=e.M;R=e.R;D=M/'data/fusion10_quality_20261023';b=e.b
def main():
    assert not (R/'FINAL_QUALITY.json').exists(),'Do not reopen completed final test'
    entry=e.read(D/'EVALUATION_ENTRY_LOCK.json');assert b.sha(R/'SELECTION_LOCK.json')==entry['selection_lock_sha256']
    for name,h in entry['source_sha256'].items():assert b.sha(M/name)==h,name
    reservation=e.read(D/'MANIFEST.json');assert b.sha(D/'holdout.jsonl')==entry['corpus_sha256']==reservation['corpus_sha256']
    selected=e.read(R/'SELECTION_LOCK.json');parameters=e.bind();data=load_split(M/'data/hidden_fusion10_20261023/holdout');cal=load_split(M/'data/hidden_v1/calibration');assert_group_disjoint(data,cal)
    rows=[json.loads(s) for s in (D/'holdout.jsonl').read_text(encoding='utf-8').splitlines()];expected={r['id']:(r['group_sha256'],r['prompt_sha256'],r['category']) for r in rows};manifest=data['manifest'];assert len(manifest['records'])==len(expected)==1000 and all('excluded' not in r for r in manifest['records']);assert {r['id']:(r['group_sha256'],r['prompt_sha256'],r['category']) for r in manifest['records']}==expected
    assert int(data['decode'].sum())>=10000 and len(set(data['groups']))==1000;settings=manifest['settings'];assert settings['corpus_sha256']==entry['corpus_sha256'] and settings['collector_sha256']==b.sha(M/'scripts/collect_hidden_fusion10_20261023.py') and settings['penalty']==1.1 and settings['max_new_tokens']==16 and settings['max_input_tokens']==2048
    torch.set_num_threads(4);torch.set_grad_enabled(False);assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=3*2**30
    report={};h=b.fp(data['hidden']);n=len(h)
    for label,p in [('selected',selected['parameters']),('frozen_baseline',e.BASE)]:
        m=e.model(parameters,f'C{p["C"]}');factor=e.model(parameters,f'r{p["r"]}');norm=np.load(e.SOURCE/f'parameters/norms_C{p["C"]}.npy');dot=e.dot_batch_gpu(h,b.fp(m['centers_bf16']));from reference.hyperparameter_study import tree_gpu
        hp=h.reshape(n,7,16,8);part=torch.zeros((n,16,8),device='cuda',dtype=torch.float32)
        for i in range(7):part=part+hp[:,i]*hp[:,i]
        for w in [8,4,2,1]:part=part[:,:w]+part[:,w:2*w]
        dist=(tree_gpu(part[:,0])[:,None]+torch.from_numpy(norm).to('cuda')[None,:])-torch.tensor(2.,device='cuda')*dot;assert bool(torch.isfinite(dist).all());routes=torch.argsort(dist,dim=1,stable=True)[:,:p['R']].cpu().numpy();z=e.dot_batch_gpu(h,b.fp(factor['b_bf16'].T.copy()));a=b.fp(factor['a_bf16']);membership=np.zeros((p['C'],e.V),bool)
        for i in range(p['C']):membership[i,m['ranked_ids'][i,:min(p['L'],int(m['counts'][i]))]]=True
        fallback=np.any(m['counts'][routes]==0,axis=1);route_hit=membership[routes,data['winner'][:,None]].any(axis=1)|np.isin(data['winner'],e.SPECIAL)|fallback;lr_hit=np.zeros(n,bool);hybrid_hit=np.zeros(n,bool);k=np.zeros(n,'u4');started=time.perf_counter()
        for start in range(0,n,4):
            b.stop();end=min(n,start+4);preview=e.apply_seen_gpu(e.preview_gpu(z[start:end],a),data['seen'][start:end]);assert bool(torch.isfinite(preview).all());top=torch.argsort(preview,dim=1,descending=True,stable=True)[:,:p['T']].cpu().numpy()
            for row in range(start,end):
                mask=membership[routes[row]].any(axis=0);lr=top[row-start];lr_hit[row]=int(data['winner'][row]) in e.SPECIAL or bool(np.any(lr==data['winner'][row]));mask[lr]=True;mask[e.SPECIAL]=True
                if fallback[row]:mask[:]=True
                k[row]=mask.sum();hybrid_hit[row]=mask[int(data['winner'][row])]
            if start%256==0 or end==n:b.progress('EXP10_FRESH_QUALITY',configuration=label,predictions_done=end,total=n,audit_s=time.perf_counter()-started)
        np.testing.assert_array_equal(hybrid_hit,route_hit|lr_hit);file=R/f'final_{label}.npz';np.savez_compressed(file,hits=hybrid_hit,route_hits=route_hit,lowrank_hits=lr_hit,k=k,fallback=fallback);q=recall_report(hybrid_hit,data);gate=q['decode']['recall']>=.999 and all(c['recall']>=.999 for c in q['decode']['by_category'].values());report[label]=dict(parameters=p,report=q,route=recall_report(route_hit,data),lowrank=recall_report(lr_hit,data),candidate_decode=b.count_stats(k[data['decode']]),fallback_calls=int(fallback.sum()),proposed_point_gate=gate,arrays=file.name,sha256=b.sha(file))
        del m,factor,a,z,membership,dot,dist;torch.cuda.empty_cache()
    result=dict(state='PASS_FROZEN_NEW_INDEPENDENT_POINT_GATE' if report['selected']['proposed_point_gate'] else 'QUALITY_FAIL_NO_RELEASE_NO_RETUNE',selected=report['selected'],frozen_baseline=report['frozen_baseline'],prompt_groups=1000,decode_steps=int(data['decode'].sum()),exclusions=0,entry_lock_sha256=b.sha(D/'EVALUATION_ENTRY_LOCK.json'),collection_manifest_sha256=data['manifest_sha256'],selection_lock_sha256=b.sha(R/'SELECTION_LOCK.json'),scope='Conditional canonical-dense trajectory coverage; not free generation/lossless/full RTL replay/FPGA acceptance. Original baseline is a predeclared same-new-cohort control; no old holdout was reopened.',board='NOT_RUN')
    b.write(R/'FINAL_QUALITY.json',result);b.progress('EXP10_FRESH_QUALITY_COMPLETE',state=result['state'])
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if R.exists():b.progress('EXP10_FINAL_QUALITY_STOPPED',error=repr(exc))
        raise
