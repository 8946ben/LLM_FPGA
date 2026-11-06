"""Frozen-arithmetic independent coverage audit, NOT FPGA timing/free generation."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,time
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def write(p,o):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');t.replace(p)

def main():
    import numpy as np
    import torch
    from qualify_selector_arithmetic import dot896,tree
    from reference.numeric_contract import bf16_bits_to_float32
    from reference.quality_data import load_split,recall_report
    d=M/'data/fixed_quality_20261022';r=M/'reports/fixed_quality_20261022';r.mkdir(exist_ok=True)
    result_path=r/'RESULT.json';assert not result_path.exists(),'Do not reopen completed quality test'
    lock=json.loads((d/'IMPLEMENTATION_FREEZE.json').read_text())
    for n,h in lock['source_sha256'].items():assert sha(M/n)==h,n
    entry=json.loads((d/'EVALUATION_ENTRY_LOCK.json').read_text())
    for n,h in entry['source_sha256'].items():assert sha(M/n)==h,n
    cal=json.loads((M/'reports/PL_ARITHMETIC_CALIBRATION.json').read_text())
    assert cal['state']=='CALIBRATION_AUDIT_PASS' and cal['source_sha256']==sha(M/'scripts/qualify_selector_arithmetic.py')
    assert set(cal['numpy_csim_fixture_full_preview_bit_matches'])=={'chinese','english','code','math'}
    assert cal['reference_sha256']==sha(M/'reference/selector_arithmetic.py')
    for name,h in cal['parameter_sha256'].items():assert sha(M/'reports/selector_p2_20261021'/name)==h
    torch.set_num_threads(4);torch.set_grad_enabled(False)
    assert torch.cuda.is_available(),'CUDA required; never replace fixed arithmetic with BLAS'
    assert torch.cuda.mem_get_info()[0]>=2*2**30,'Need free GPU memory; do not compete with another task'
    collection=M/'data/hidden_fixed_20261022/holdout'
    settings=json.loads((collection/'SETTINGS.json').read_text())
    assert settings['corpus_sha256']==sha(d/'holdout.jsonl')==entry['corpus_sha256']
    assert settings['collector_sha256']==sha(M/'scripts/collect_hidden_fixed_20261022.py')
    assert settings['gpu_head_sha256']==sha(M/'reference/gpu_exact_head.py')
    assert settings['model_lock_sha256']==sha(M/'data/model/MODEL.lock.json')
    assert settings['canonical_weight_sha256']=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    assert settings['max_new_tokens']==16 and settings['max_input_tokens']==2048 and settings['limit_per_category'] is None
    assert settings['penalty']==1.1 and settings['head_dtype']=='FP32_H8_INTERLEAVE16_SEPARATE_MULTIPLY_ADD'
    manifest=json.loads((collection/'MANIFEST.json').read_text())
    rows=[json.loads(s) for s in (d/'holdout.jsonl').read_text().splitlines()]
    expected={r['id']:(r['group_sha256'],r['prompt_sha256'],r['category']) for r in rows}
    assert len(manifest['records'])==len(expected)==1000
    assert all('excluded' not in r for r in manifest['records']),'Do not discard new test groups after looking at labels'
    assert {r['id']:(r['group_sha256'],r['prompt_sha256'],r['category']) for r in manifest['records']}==expected
    data=load_split(M/'data/hidden_fixed_20261022/holdout');n=len(data['hidden'])
    assert len(set(data['groups']))>=1000 and int(data['decode'].sum())>=10000
    folder=M/'reports/selector_p2_20261021'
    with np.load(folder/'lowrank_r128.npz',allow_pickle=False) as z:a_bits=z['a_bf16'];b_bits=z['b_bf16']
    with np.load(folder/'route_r128.npz',allow_pickle=False) as z:router={k:z[k] for k in z.files}
    assert router['ranked_ids'].shape==(128,16384) and np.all(router['counts']<=16384)
    h=torch.from_numpy(bf16_bits_to_float32(data['hidden'])).to('cuda')
    a=torch.from_numpy(bf16_bits_to_float32(a_bits)).to('cuda');bt=torch.from_numpy(bf16_bits_to_float32(b_bits.T.copy())).to('cuda')
    centers=torch.from_numpy(bf16_bits_to_float32(router['centers_bf16'])).to('cuda')
    norms=np.fromfile(M/'reports/router_fixture_20261021/router.norms.bin',dtype='<f4')
    z=dot896(h,bt);dots=dot896(h,centers)
    hp=torch.zeros((n,8,16),dtype=torch.float32,device='cuda');hw=h.reshape(n,112,8)
    for word in range(112):hp[:,:,word&15]=hp[:,:,word&15]+hw[:,word,:]*hw[:,word,:]
    for width in (8,4,2,1):hp[...,:width]=hp[...,:width]+hp[...,width:2*width]
    distance=(tree(hp[:,:,0])[:,None]+torch.from_numpy(norms).to('cuda')[None,:])-torch.tensor(2.,device='cuda')*dots
    assert torch.isfinite(z).all() and torch.isfinite(distance).all()
    routes=torch.argsort(distance,dim=1,stable=True)[:,:4].cpu().numpy()
    del distance,dots,hp;torch.cuda.empty_cache()
    membership=np.zeros((128,151936),dtype=bool)
    for i in range(128):membership[i,router['ranked_ids'][i,:int(router['counts'][i])]]=True
    mandatory=np.arange(151643,151657);mandatory_hit=np.isin(data['winner'],mandatory)
    fallback=np.any(router['counts'][routes]==0,axis=1)
    route_hit=membership[routes,data['winner'][:,None]].any(axis=1)|mandatory_hit|fallback
    lr_hit=np.zeros(n,dtype=bool);hybrid_hit=np.zeros(n,dtype=bool);counts=np.zeros(n,dtype='u4');started=time.perf_counter()
    for start in range(0,n,8):
        if (r/'STOP_REQUESTED').exists():raise RuntimeError('Stop requested at batch boundary; result NOT complete')
        stop=min(n,start+8);p=(a[None,:,:]*z[start:stop,None,:]).reshape(stop-start,151936,16,8)
        preview=tree(tree(p));del p
        ii=[];jj=[]
        for row in range(start,stop):ii.extend([row-start]*len(data['seen'][row]));jj.extend(map(int,data['seen'][row]))
        ri=torch.tensor(ii,device='cuda',dtype=torch.int64);ci=torch.tensor(jj,device='cuda',dtype=torch.int64)
        old=preview[ri,ci];preview[ri,ci]=torch.where(old<0,old*torch.tensor(1.1,device='cuda'),old/torch.tensor(1.1,device='cuda'))
        assert torch.isfinite(preview).all()
        top=torch.argsort(preview,dim=1,descending=True,stable=True)[:,:16384].cpu().numpy()
        for row in range(start,stop):
            ids=top[row-start];winner=int(data['winner'][row]);lr_hit[row]=bool(np.any(ids==winner) or mandatory_hit[row])
            mask=membership[routes[row]].any(axis=0);mask[ids]=True;mask[mandatory]=True
            if fallback[row]:mask[:]=True
            counts[row]=int(mask.sum());hybrid_hit[row]=mask[winner]
        assert np.array_equal(hybrid_hit[start:stop],(route_hit|lr_hit)[start:stop])
        if start%128==0 or stop==n:
            write(r/'PROGRESS.json',dict(state='RUNNING_FIXED_CONFIG_NO_FIT',predictions_done=stop,total=n,elapsed_s=time.perf_counter()-started))
            print(f'FIXED_QUALITY {stop}/{n}',flush=True)
    reports={name:recall_report(hit,data) for name,hit in [('route',route_hit),('lowrank',lr_hit),('hybrid',hybrid_hit)]}
    hr=reports['hybrid']['decode'];passed=hr['recall']>=.999 and all(v['recall']>=.999 for v in hr['by_category'].values())
    measured=counts[data['decode']];np.save(r/'candidate_counts_all.npy',counts,allow_pickle=False)
    result=dict(state='PASS_PROPOSED_INDEPENDENT_POINT_RECALL_GATE' if passed else 'QUALITY_FAIL_NO_RELEASE',
                updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),configuration=lock['configuration'],fit='NONE',
                corpus_sha256=sha(d/'holdout.jsonl'),implementation_freeze_sha256=sha(d/'IMPLEMENTATION_FREEZE.json'),
                entry_lock_sha256=sha(d/'EVALUATION_ENTRY_LOCK.json'),collection_manifest_sha256=data['manifest_sha256'],
                reused_arithmetic_fixture_proof='Frozen GPU primitive and calibration source hash match four complete Csim/GPU fixture proofs; new coverage audit is model-based, not full new RTL replay',
                route=reports['route'],lowrank=reports['lowrank'],hybrid=reports['hybrid'],
                candidate_decode=dict(mean=float(measured.mean()),median=float(np.median(measured)),p95=int(np.sort(measured)[int(np.ceil(.95*len(measured)))-1]),maximum=int(measured.max()),dense_fallback_calls=int(fallback[data['decode']].sum())),
                counts_sha256=sha(r/'candidate_counts_all.npy'),board='NOT_RUN',ttft='NOT_MEASURED',
                timing='Audit wall time not FPGA latency',limitations=lock['limitations'])
    write(result_path,result);print(result['state'],flush=True)

if __name__=='__main__':main()
