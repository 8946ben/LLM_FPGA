"""Logical operation/storage/traffic models from real calibration candidates.

Pure NumPy post-analysis; no FPGA or EDA. Does not turn GPU throughput into an
FPGA estimate. Byte models require the stated compact/column layouts.
"""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/sparse_methods_20261024_r1';B=R/'benchmark';FIRST=M/'reports/hyperparameters_20261023_r1'
sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32
from reference.hyperparameter_study import H,V,tree_numpy
from reference.quality_data import load_split
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def model(path):
    with np.load(path,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def batch_dot(hidden,rows,batch=16):
    hidden=bf16_bits_to_float32(hidden).reshape(-1,7,16,8);w=bf16_bits_to_float32(rows).reshape(-1,7,16,8);out=[]
    for start in range(0,len(hidden),batch):
        hh=hidden[start:start+batch];p=np.zeros((len(hh),len(w),16,8),'f4')
        for g in range(7):p=np.add(p,np.multiply(w[None,:,g],hh[:,None,g],dtype=np.float32),dtype=np.float32)
        for width in (8,4,2,1):p=np.add(p[:,:,:width],p[:,:,width:2*width],dtype=np.float32)
        out.append(tree_numpy(p[:,:,0]))
    return np.concatenate(out)

def main():
    result=read(B/'RESULT.json');review=read(B/'INDEPENDENT_REVIEW.json');assert review['result_sha256']==sha(B/'RESULT.json')
    cal=load_split(M/'data/hidden_v1/calibration');mask=cal['decode'];rows=result['configurations'];params=read(R/'PARAMETERS.json')['files'];original=read(FIRST/'PARAMETERS.json')['files'];metadata={};entries={};sources={}
    for c in [1,16,32,64,128,256,512]:
        m=model(FIRST/original[f'C{c}']['path']);norms=np.load(FIRST/f'parameters/norms_C{c}.npy');dots=batch_dot(cal['hidden'],m['centers_bf16'])
        h=bf16_bits_to_float32(cal['hidden']).reshape(-1,7,16,8);p=np.zeros((len(h),16,8),'f4')
        for g in range(7):p=np.add(p,np.multiply(h[:,g],h[:,g],dtype=np.float32),dtype=np.float32)
        for w in (8,4,2,1):p=np.add(p[:,:w],p[:,w:2*w],dtype=np.float32)
        hn=tree_numpy(p[:,0]);distance=np.subtract(np.add(hn[:,None],norms,dtype=np.float32),np.multiply(np.float32(2),dots,dtype=np.float32),dtype=np.float32);order=np.argsort(distance,kind='stable',axis=1)
        for row in rows:
            a=row['parameters']
            if row['mode']=='cluster' and a['C']==c:
                e=np.minimum(m['counts'][order[:,:a['R']]],a['L']).sum(axis=1).astype('u4');entries[row['id']]=e
                metadata[row['id']]=2*c*H+4*int(np.minimum(m['counts'],a['L']).sum())+8*(c+1)
        print('COST_OLD_ROUTE',c,flush=True);del m,dots,h,p
    for mode in ['affinity','learned']:
        for c in [128,256]:
            for pp in [1,2]:
                key=f'bucket_C{c}_P{pp}';m=model(R/params[key]['path']);scores=batch_dot(cal['hidden'],m['prototypes_bf16'] if mode=='affinity' else m['screen_bf16'])+(np.float32(0) if mode=='affinity' else m['bias'][None,:]);order=np.argsort(-scores,axis=1,kind='stable');counts=np.diff(m['offsets'])
                for row in rows:
                    a=row['parameters']
                    if row['mode']==mode and a['C']==c and a['P']==pp:
                        entries[row['id']]=counts[order[:,:a['R']]].sum(axis=1).astype('u4');metadata[row['id']]=2*c*H+(4*c if mode=='learned' else 0)+4*(c+1)+4*V*pp
                print('COST_NEW_BUCKET',mode,c,pp,flush=True)
    for kind in ['angular','mips']:
        for bits in [8,10]:
            key=f'hash_{kind}_b{bits}';m=model(R/params[key]['path']);scores=batch_dot(cal['hidden'],m['planes_bf16']).reshape(-1,8,bits);codes=((scores>=0).astype('u4')*(np.uint32(1)<<np.arange(bits,dtype='u4'))).sum(axis=2,dtype=np.uint32);counts=np.diff(m['offsets'])
            for row in rows:
                a=row['parameters']
                if row['mode']=='lsh' and a['kind']==kind and a['b']==bits:
                    masks=np.array([0]+([1<<j for j in range(bits)] if a['radius'] else []),'u4');groups=(codes[:,:a['tables'],None]^masks[None,None,:])+np.arange(a['tables'],dtype='u4')[None,:,None]*(1<<bits);entries[row['id']]=counts[groups].sum(axis=(1,2)).astype('u4');metadata[row['id']]=2*8*bits*H+4*(8*(1<<bits)+1)+4*8*V
            print('COST_HASH',kind,bits,flush=True)
    rms=model(R/params['channels']['path'])['rms'];hidden=bf16_bits_to_float32(cal['hidden']);energy={}
    for choice,ds in [('dynamic',[16,32,64,128]),('static',[32,128])]:
        order=np.argsort(-np.abs(hidden)*rms[None,:],axis=1,kind='stable') if choice=='dynamic' else np.broadcast_to(np.argsort(-rms,kind='stable'),hidden.shape)
        for d in ds:
            ratio=np.take_along_axis(hidden*hidden,order[:,:d],axis=1).sum(axis=1)/(hidden*hidden).sum(axis=1);energy[f'{choice}_{d}']=dict(mean=float(ratio[mask].mean()),p05=float(np.quantile(ratio[mask],.05)),min=float(ratio[mask].min()))
    costs=[]
    for row in rows:
        a=row['parameters'];mode=row['mode'];k=row['candidate_decode']['mean'];exact=k*H;selector=0;preview_bytes=0;meta=0;sort_rows=[];layout='Canonical row-major BF16 W';notes=[];e=entries.get(row['id']);logical_list=0
        if mode=='dense':exact=V*H
        elif mode=='cluster':selector=a['C']*H;meta=metadata[row['id']];preview_bytes=2*a['C']*H;sort_rows=[a['C']];notes=['Router also computes hidden norm; ID bitmap dedup/sorted scan required.']
        elif mode=='lowrank':selector=a['r']*(H+V);meta=2*a['r']*(H+V);preview_bytes=meta;sort_rows=[V];notes=['Full-vocabulary approximate score + TopT; BF16 factors kept in addition to canonical W.']
        elif mode=='hybrid':
            selector=a['C']*H+a['r']*(H+V);meta=2*a['r']*(H+V)+2*a['C']*H+4*a['C']*a['L']+8*a['C'];preview_bytes=2*a['C']*H+2*a['r']*(H+V);sort_rows=[a['C'],V]
            source=row['calibration_source']
            if source not in sources:sources[source]={r['id']:r for r in read(ROOT/source)['configurations']}
            old=sources[source][row['config']]
            with np.load((ROOT/source).parent/old['arrays']) as z:
                e=z['list_entries'].copy();assert np.all(e+14>=z['route_k'])
            notes=['Fusion storage uses old cap C*L allocation, not compact valid entries.']
        elif mode=='partial':
            selector=V*a['d']+(H if a['choice']=='dynamic' else 0);preview_bytes=2*V*a['d'];sort_rows=([H] if a['choice']=='dynamic' else [])+[V]
            meta=2*V*(H if a['choice']=='dynamic' else a['d'])+4*H+4*a['d'];layout='Separate column-major preview W plus canonical row-major exact W'
            notes=['Actual GPU Engine stores full column-major W for all partial points. Static FPGA layout can trim it to chosen d columns; dynamic may choose any896 channels and needs all columns or another access design.','Logical2*V*d preview bytes assumes that column-oriented layout; original row-major AXI reads do not automatically shrink to this budget.']
        elif mode in ['affinity','learned']:
            selector=a['C']*H;meta=metadata[row['id']];preview_bytes=2*a['C']*H+(4*a['C'] if mode=='learned' else 0);sort_rows=[a['C']];layout='Complete compact sorted-ID bucket lists + canonical row-major W'
            notes=['P assignments cover every vocabulary ID; full R=C yields exact dense candidate set. No such quality guarantee for small R.','Duplicate bucket IDs need hazard-safe OR/bitmap and global sorted enumeration; ridge bias/rounding need a new hardware contract.']
        elif mode=='lsh':
            selector=8*a['b']*H;meta=metadata[row['id']];preview_bytes=2*8*a['b']*H;sort_rows=[];layout='8-table compact hash bucket index + canonical row-major W'
            notes=['Actual prototype projects8 tables even when active tables=4; reported multiplication terms and stored index reflect8. Active-table-only hardware is a later optimization.','Probe count L*(1+b) for radius1; random bucket offsets and skewed lengths affect DDR and maximum buffers; MIPS vs angular differ at index construction only.']
        if e is not None:
            assert np.all(e>=0);logical_list=4*float(e[mask].mean())
        minimal=2*V*H+meta;logical=2*k*H+preview_bytes+logical_list
        cost=dict(id=row['id'],mode=mode,selector_multiplication_terms=selector,exact_multiplication_terms=exact,total_multiplication_terms=selector+exact,ratio_to_dense_multiplications=(selector+exact)/(V*H),logical_weight_read_bytes=2*k*H,logical_preview_read_bytes=preview_bytes,logical_list_read_bytes=logical_list,logical_main_read_bytes=logical,main_read_ratio_to_dense=logical/(2*V*H),candidate_K_mean=k,candidate_K_p95=row['candidate_decode']['p95'],list_entries_mean=float(e[mask].mean()) if e is not None else 0,sort_lengths=sort_rows,stored_weight_and_index_lower_bound_bytes=minimal,exceeds320MiB_before_common_buffers=minimal>320*2**20,layout=layout,notes=notes,energy_capture=energy.get(f'{a.get("choice")}_{a.get("d")}') if mode=='partial' else None)
        if e is not None:
            path=R/f'cost_arrays/{row["id"]}.npz';path.parent.mkdir(exist_ok=True);np.savez_compressed(path,list_entries=e);cost['list_entries_array']=path.relative_to(R).as_posix();cost['list_entries_array_sha256']=sha(path)
        costs.append(cost)
    analysis=dict(state='COMPLETE_LOGICAL_MODELS_NOT_FPGA_MEASUREMENTS',result_sha256=sha(B/'RESULT.json'),calibration_manifest_sha256=cal['manifest_sha256'],script_sha256=sha(Path(__file__)),rows=costs,definitions=dict(multiplications='Scalar product terms, not hardware MAC cycles. Exact K*896; selector terms are actual current algorithm, separate multiply/add FP32. Tree additions/policy/sorting/union not included in this multiplication count.',logical_bytes='BF16 row/preview parameter reads plus actual list-entry reads. Excludes burst waste/cache/history/score buffers/sorting traffic/AXI control; not measured GPU bandwidth or AXI traffic.',storage='Minimum persistent canonical W plus required preview/index layout, before common scratch/guards/output/arena alignment. <=320MiB is not a fit certificate; >320MiB already needs new layout.',time='For bandwidth B and multiplier lanes P at f, max(logical_bytes/B,multiplications/(P*f)) is only an idealized lower bound with stated layouts, not a predicted FPGA time.'),fpga='NOT_RUN',eda='NOT_RUN',new_final_quality='NOT_RUN')
    write(R/'ANALYSIS.json',analysis);print('COST_ANALYSIS_COMPLETE',len(costs),flush=True)
if __name__=='__main__':main()
