"""Fixed-config calibration only; deterministic FP32 operations, no matmul/FMA.

Validates GPU operation-order model against all four NumPy/Csim fixture tables
before using it to audit all calibration decode steps. This is not new holdout
certification, RTL proof, or a timing benchmark of the actual selector.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys,time
os.environ.setdefault('OMP_NUM_THREADS','4')
import numpy as np
import torch
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32
from reference.quality_data import load_split,recall_report
from reference.routing import nearest_centers
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):
    temp=p.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def tree(x):
    while x.shape[-1]>1:x=x[...,0::2]+x[...,1::2]
    return x[...,0]
def dot896(h,rows):
    n=len(h);r=len(rows);p=torch.zeros((n,r,8,16),dtype=torch.float32,device=h.device)
    hw=h.reshape(n,112,8);w=rows.reshape(r,112,8)
    for word in range(112):
        s=word&15;prod=hw[:,None,word,:]*w[None,:,word,:];p[:,:,:,s]=p[:,:,:,s]+prod
    for width in (8,4,2,1):p[...,:width]=p[...,:width]+p[...,width:2*width]
    return tree(p[:,:,:,0])
def main():
    torch.set_num_threads(4);torch.set_grad_enabled(False)
    if not torch.cuda.is_available():raise RuntimeError('CUDA model unavailable; do not substitute BLAS')
    device='cuda';started=time.perf_counter();reports=M/'reports';folder=reports/'selector_p2_20261021'
    lock=json.loads((folder/'PARAMETERS.json').read_text())
    for name in ('lowrank_r128.npz','route_r128.npz'):assert sha(folder/name)==lock[name]
    with np.load(folder/'lowrank_r128.npz',allow_pickle=False) as z:a_bits=z['a_bf16'];b_bits=z['b_bf16']
    with np.load(folder/'route_r128.npz',allow_pickle=False) as z:router={k:z[k] for k in z.files}
    data=load_split(M/'data/hidden_v1/calibration');n=len(data['hidden']);c=bf16_bits_to_float32(router['centers_bf16'])
    norms=np.fromfile(reports/'router_fixture_20261021/router.norms.bin',dtype='<f4');assert norms.shape==(128,)
    h_cpu=bf16_bits_to_float32(data['hidden']);h=torch.from_numpy(h_cpu).to(device)
    a=torch.from_numpy(bf16_bits_to_float32(a_bits)).to(device);bt=torch.from_numpy(bf16_bits_to_float32(b_bits.T.copy())).to(device)
    centers=torch.from_numpy(c).to(device)
    z=dot896(h,bt);dots=dot896(h,centers)
    hp=torch.zeros((n,8,16),dtype=torch.float32,device=device);hw=h.reshape(n,112,8)
    for word in range(112):
        v=hw[:,word,:];hp[:,:,word&15]=hp[:,:,word&15]+v*v
    for width in (8,4,2,1):hp[...,:width]=hp[...,:width]+hp[...,width:2*width]
    hn=tree(hp[:,:,0]);distance=(hn[:,None]+torch.from_numpy(norms).to(device)[None,:])-torch.tensor(2.,device=device)*dots
    routes=torch.argsort(distance,dim=1,stable=True)[:,:4].cpu().numpy().astype('u4')
    if not torch.isfinite(z).all() or not torch.isfinite(distance).all():raise FloatingPointError('nonfinite z/distance')
    del dots,distance,hp;torch.cuda.empty_cache()
    original_routes=nearest_centers(h_cpu,c,4);changes=int(np.any(routes!=original_routes,axis=1).sum())
    # Frozen rank tables already contain unique IDs; only selected-cluster
    # membership is used to audit coverage, not to construct an online output.
    membership=np.zeros((128,151936),dtype=bool)
    for i in range(128):membership[i,router['ranked_ids'][i,:int(router['counts'][i])]]=True
    mandatory=np.arange(151643,151657,dtype='u4');mandatory_hit=np.isin(data['winner'],mandatory)
    route_hit=membership[routes,data['winner'][:,None]].any(axis=1)|mandatory_hit
    fallback=np.any(router['counts'][routes]==0,axis=1);route_hit|=fallback
    lr_hit=np.zeros(n,dtype=bool);vocab=torch.arange(151936,device=device);batch=8
    fixture=json.loads((reports/'lowrank_fixture_20261021/MANIFEST.json').read_text());fixture_rows={r['index']:r['category'] for r in fixture['rows']}
    checked=[];progress=reports/'PL_ARITHMETIC_CALIBRATION_PROGRESS.json'
    for start in range(0,n,batch):
        stop=min(n,start+batch);p=(a[None,:,:]*z[start:stop,None,:]).reshape(stop-start,151936,16,8)
        preview=tree(tree(p));del p
        ii=[];jj=[]
        for row in range(start,stop):ii.extend([row-start]*len(data['seen'][row]));jj.extend(map(int,data['seen'][row]))
        ri=torch.tensor(ii,device=device,dtype=torch.int64);ci=torch.tensor(jj,device=device,dtype=torch.int64)
        old=preview[ri,ci];preview[ri,ci]=torch.where(old<0,old*torch.tensor(1.1,device=device),old/torch.tensor(1.1,device=device))
        if not torch.isfinite(preview).all():raise FloatingPointError('nonfinite preview')
        for row in range(start,stop):
            if row in fixture_rows:
                cat=fixture_rows[row];actual=preview[row-start].cpu().numpy();gold=np.fromfile(reports/'lowrank_fixture_20261021'/f'{cat}.scores.bin',dtype='<f4')
                np.testing.assert_array_equal(actual.view('u4'),gold.view('u4'))
                rt=np.fromfile(reports/'router_fixture_20261021'/f'{cat}.routes.bin',dtype='<u4');np.testing.assert_array_equal(routes[row],rt)
                checked.append(cat)
        winners=torch.tensor(data['winner'][start:stop].astype('i8'),device=device);target=preview[torch.arange(stop-start,device=device),winners]
        ranks=((preview>target[:,None])|((preview==target[:,None])&(vocab[None,:]<winners[:,None]))).sum(dim=1)
        lr_hit[start:stop]=(ranks<16384).cpu().numpy()|mandatory_hit[start:stop]
        if start%128==0 or stop==n:
            write(progress,dict(state='RUNNING',updated=now(),predictions_done=stop,total=n,scope='calibration fixed configuration only; no holdout',elapsed_s=time.perf_counter()-started))
            print(f'ARITHMETIC_CALIBRATION {stop}/{n}',flush=True)
    assert set(checked)=={'chinese','english','code','math'}
    result=dict(state='CALIBRATION_AUDIT_PASS',updated=now(),scope='Fixed existing configuration; calibration only; not new independent quality or RTL/board verification',
        configuration='route4_K16384_UNION_lr128_K16384',fit='NONE',holdout_read=False,source_sha256=sha(Path(__file__)),
        reference_sha256=sha(M/'reference/selector_arithmetic.py'),calibration_manifest_sha256=data['manifest_sha256'],
        parameter_sha256={name:lock[name] for name in ('lowrank_r128.npz','route_r128.npz')},
        gpu=dict(torch=torch.__version__,device=torch.cuda.get_device_name(0),arithmetic='separate FP32 elementwise multiply/add/divide; explicit trees; no matmul'),
        numpy_csim_fixture_full_preview_bit_matches=checked,changed_route_order_vs_cpu_blas=changes,
        route=recall_report(route_hit,data),lowrank=recall_report(lr_hit,data),hybrid=recall_report(route_hit|lr_hit,data),
        elapsed_validation_seconds=time.perf_counter()-started,timing_note='Offline audit runtime; not online selector latency or FPGA performance',
        boundary='GPU/NumPy arithmetic model agrees with Csim on four full-score fixtures; full calibration Csim/RTL and denormal behavior not proven')
    write(reports/'PL_ARITHMETIC_CALIBRATION.json',result);write(progress,dict(state='COMPLETE',updated=now(),predictions_done=n,total=n))
    print(json.dumps({k:result[k]['decode'] for k in ('route','lowrank','hybrid')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
