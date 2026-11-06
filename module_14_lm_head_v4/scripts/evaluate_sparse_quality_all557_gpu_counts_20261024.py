"""Untimed exact integer bitmap counts, batched across frozen557 configurations."""
import hashlib,os,time
from pathlib import Path
import numpy as np
import torch
import run_sparse_quality_all557_20261024 as U
from evaluate_sparse_quality_all557_fast_20261024 import fast_report

@torch.inference_mode()
def main():
    torch.set_num_threads(4);U.check();assert not (U.OUT/'ACTIVE.lock').exists() and not (U.OUT/'QUALITY.json').exists()
    preserved=U.OUT/'evaluation_r1_preserved';preserved.mkdir(exist_ok=True)
    if (U.OUT/'STOP_REQUESTED').exists():(U.OUT/'STOP_REQUESTED').replace(preserved/'STOP_REQUESTED')
    committed=U.read(U.OUT/'QUALITY.partial.json')['configurations'];U.write(preserved/'QUALITY.partial.after_stop.json',dict(configurations=committed))
    assert not (U.OUT/'GPU_COUNT_ENTRY.json').exists()
    cache=U.read(U.OUT/'CACHE.json');data=U.load_split(U.DATA);points=U.pairs();n=len(data['hidden']);assert n==15956
    U.write(U.OUT/'GPU_COUNT_ENTRY.json',dict(created=U.now(),source_sha256=U.sha(__file__),report_function_sha256=U.sha(Path(__file__).with_name('evaluate_sparse_quality_all557_fast_20261024.py')),plan_sha256=U.sha(U.OUT/'PLAN.json'),cache_manifest_sha256=U.sha(U.OUT/'CACHE.json'),preserved_committed_configs=len(committed),change='Untimed only: transfer each actual bitmap block once, reuse across557 combinations; exact uint8 OR, integer lookup popcount/sum and winner bit. No floating numeric head or selector change; no timed cache reads.',qualification='All-zero/all-one/random byte arrays; first2 real states for every557 combo; every completed r1 array and original6 arrays compared; complete cache SHA accumulated from actual ingested blocks.'))
    U.write(U.OUT/'ACTIVE.lock',dict(pid=os.getpid(),started=U.now(),phase='gpu_integer_bitmap_counts'))
    try:
        assert torch.cuda.is_available() and torch.cuda.mem_get_info()[0]>=3*2**30
        lut=torch.from_numpy(U.LUT.astype('i8')).to('cuda')
        rng=np.random.default_rng(20261024);sample=np.concatenate([np.zeros((1,U.WIDTH),'u1'),np.full((1,U.WIDTH),255,'u1'),rng.integers(0,256,(7,U.WIDTH),dtype='u1')])
        actual=lut[torch.from_numpy(sample).to('cuda').long()].sum(dim=1).cpu().numpy();np.testing.assert_array_equal(actual,U.LUT[sample].sum(axis=1))
        maps={k:np.memmap(U.OUT/x['path'],dtype='u1',mode='r',shape=(n,U.WIDTH)) for k,x in cache['items'].items()};digests={k:hashlib.sha256() for k in maps}
        stats={p['id']:(np.empty(n,bool),np.empty(n,'u4')) for p in points};first_proof=[];started=time.perf_counter()
        for start in range(0,n,256):
            U.stop();end=min(n,start+256);resident={};cpu_first={}
            for key,m in maps.items():
                block=np.array(m[start:end],copy=True);digests[key].update(memoryview(block));resident[key]=torch.from_numpy(block).to('cuda')
                if start==0:cpu_first[key]=block[:2].copy()
            winner=torch.from_numpy(data['winner'][start:end].astype('i8')).to('cuda');row=torch.arange(end-start,device='cuda');at=winner//8;bit=winner%8
            for pair in points:
                p=pair['parameters'];mode=pair['mode'];a=b=None
                if mode in ['cluster','hybrid']:a=resident['route:'+U.route_key(p)]
                if mode in ['lowrank','hybrid']:b=resident['lowrank:'+U.low_key(p)]
                if mode in U.S.MODES:a=resident['extra:'+pair['id']]
                hits,ks=stats[pair['id']]
                if mode=='dense':hits[start:end]=True;ks[start:end]=U.V;continue
                union=a|b if mode=='hybrid' else b if mode=='lowrank' else a
                count=lut[union.long()].sum(dim=1);hit=((union[row,at].long()>>bit)&1)
                result=torch.stack([count,hit],dim=1).cpu().numpy();ks[start:end]=result[:,0];hits[start:end]=result[:,1].astype(bool)
                if start==0:
                    aa=cpu_first['route:'+U.route_key(p)] if mode in ['cluster','hybrid'] else cpu_first['extra:'+pair['id']] if mode in U.S.MODES else None
                    bb=cpu_first['lowrank:'+U.low_key(p)] if mode in ['lowrank','hybrid'] else None
                    expected=aa|bb if mode=='hybrid' else bb if mode=='lowrank' else aa
                    np.testing.assert_array_equal(result[:2,0],U.LUT[expected].sum(axis=1));w=data['winner'][:2].astype('i8');np.testing.assert_array_equal(result[:2,1],((expected[np.arange(2),w//8]>>(w%8))&1))
                    first_proof.append(pair['id'])
            del resident,union,count,hit,result
            U.progress('GPU_INTEGER_COUNTS',predictions_done=end,total=n,configurations=557,seconds=time.perf_counter()-started)
        for key,item in cache['items'].items():assert digests[key].hexdigest()==item['sha256'],key
        rows=[];dest=U.OUT/'coverage_gpu_counts_r2';dest.mkdir(exist_ok=True)
        for pair in points:
            U.stop();p=pair['parameters'];hits,k=stats[pair['id']];mode=pair['mode'];fallback=np.zeros(n,bool);aux=None
            if mode in ['cluster','hybrid']:
                aux=np.load(U.OUT/cache['items']['route:'+U.route_key(p)]['aux']);fallback=aux['fallback'].copy()
            path=dest/(pair['id']+'.npz');assert not path.exists();np.savez_compressed(path,hits=hits,k=k,fallback=fallback)
            q=fast_report(hits,data);kv=k[data['decode']];gate=q['decode']['recall']>=.99 and all(v['recall']>=.99 for v in q['decode']['by_category'].values())
            r=dict(**pair,quality=q,candidate_decode=dict(mean=float(kv.mean()),median=float(np.median(kv)),p95=int(np.sort(kv)[int(np.ceil(.95*len(kv)))-1]),max=int(kv.max()),min=int(kv.min())),gate99='PASS' if gate else 'FAIL',fallback_decode=int(fallback[data['decode']].sum()),arrays=path.relative_to(U.OUT).as_posix(),sha256=U.sha(path))
            if mode=='cluster':r['pure_lists_all_misses']=int((~aux['pure_hits']).sum())
            rows.append(r)
        byid={r['id']:r for r in rows}
        for prior in committed:
            fresh=byid[prior['id']];a=np.load(U.OUT/prior['arrays']);b=np.load(U.OUT/fresh['arrays']);np.testing.assert_array_equal(a['hits'],b['hits']);np.testing.assert_array_equal(a['k'],b['k']);assert prior['quality']==fresh['quality']
        for prior in U.read(U.PREVIOUS/'QUALITY.json')['configurations']:
            current=byid[prior['id']];a=np.load(U.ROOT/prior['coverage']);b=np.load(U.OUT/current['arrays']);np.testing.assert_array_equal(a['hits'],b['hits']);np.testing.assert_array_equal(a['k'],b['k']);assert prior['report']==current['quality']
        U.check();assert len(first_proof)==556
        U.write(U.OUT/'GPU_COUNT_QUALIFICATION.json',dict(state='PASS_EXACT_INTEGER_COUNTER_AND_ALL_PRIOR_ARRAYS',first2_configs=len(first_proof),byte_boundary_cases=9,prior_r1_full_arrays=len(committed),original6_full_arrays=6,all158_ingested_cache_sha=True,entry_sha256=U.sha(U.OUT/'GPU_COUNT_ENTRY.json')))
        U.write(U.OUT/'QUALITY.json',dict(state='COMPLETE557_SUPPLEMENTARY_ON_ALREADY_OPENED1000',completed=U.now(),configurations=rows,prompts=1000,predictions=n,decode=int(data['decode'].sum()),excluded=0,first_six_reproduced_exactly=True,collection_manifest_sha256=U.sha(U.DATA/'MANIFEST.json'),plan_sha256=U.sha(U.OUT/'PLAN.json'),count_entry_sha256=U.sha(U.OUT/'GPU_COUNT_ENTRY.json'),limits='Already-opened cohort supplemental membership coverage, not new certification; GPU integer masks/counts are untimed and never used by inference benchmark.'))
        U.progress('QUALITY_COMPLETE',configurations=557)
    finally:(U.OUT/'ACTIVE.lock').unlink(missing_ok=True)
if __name__=='__main__':main()
