"""Independent NumPy-only oracle on8 additional calibration rows per new point."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/sparse_methods_20261024_r1'
sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32,compute_raw_logits
from reference.hyperparameter_study import V,H,SPECIAL,tree_numpy
from reference.quality_data import load_split
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def main():
    cal=load_split(M/'data/hidden_v1/calibration');rows=read(R/'CALIBRATION.json')['configurations'];parameters=read(R/'PARAMETERS.json')['files'];models={k:load(R/v['path']) for k,v in parameters.items()};assert len(rows)==68
    for key,v in parameters.items():assert sha(R/v['path'])==v['sha256']
    sample=[]
    for category in ['chinese','english','code','math']:
        positions=np.flatnonzero((cal['category']==category)&cal['decode']);sample.extend([int(positions[len(positions)//3]),int(positions[2*len(positions)//3])])
    bits=np.memmap(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',dtype='<u2',mode='r',shape=(V,H));cache={};records=[]
    for row in rows:
        p=row['parameters'];mode=row['mode'];a=load(R/row['arrays'])
        for i in sample:
            h=cal['hidden'][i]
            if mode=='partial':
                key=('partial',p['choice'],p['d'],i)
                if key not in cache:
                    hf=bf16_bits_to_float32(h);rms=models['channels']['rms'];dims=np.argsort(-np.multiply(np.abs(hf),rms,dtype=np.float32),kind='stable')[:p['d']] if p['choice']=='dynamic' else models['channels']['order'][:p['d']]
                    scores=np.empty(V,'f4')
                    for start in range(0,V,4096):
                        w=bf16_bits_to_float32(bits[start:start+4096][:,dims]);scores[start:start+len(w)]=tree_numpy(np.multiply(w,hf[dims],dtype=np.float32))
                    ii=cal['seen'][i];old=scores[ii];pen=np.float32(1.1);scores[ii]=np.where(old<0,np.multiply(old,pen,dtype=np.float32),np.divide(old,pen,dtype=np.float32));cache[key]=np.argsort(-scores,kind='stable')
                ids=np.union1d(cache[key][:p['T']],SPECIAL).astype('u4')
            else:
                if mode in ['affinity','learned']:
                    m=models[f'bucket_C{p["C"]}_P{p["P"]}'];key=(mode,p['C'],p['P'],i)
                    if key not in cache:
                        scores=compute_raw_logits(h,m['prototypes_bf16'] if mode=='affinity' else m['screen_bf16'])+(np.float32(0) if mode=='affinity' else m['bias']);cache[key]=np.argsort(-scores,kind='stable')
                    groups=cache[key][:p['R']]
                else:
                    m=models[f'hash_{p["kind"]}_b{p["b"]}'];key=(mode,p['kind'],p['b'],i)
                    if key not in cache:
                        values=compute_raw_logits(h,m['planes_bf16']).reshape(8,p['b']);cache[key]=((values>=0).astype('u4')*(np.uint32(1)<<np.arange(p['b'],dtype='u4'))).sum(axis=1,dtype=np.uint32)
                    masks=[0]+([1<<j for j in range(p['b'])] if p['radius'] else []);groups=[table*(1<<p['b'])+(int(cache[key][table])^mask) for table in range(p['tables']) for mask in masks]
                ids=np.unique(np.concatenate([m['ids'][int(m['offsets'][g]):int(m['offsets'][g+1])] for g in groups]+[SPECIAL])).astype('u4')
            hit=bool(cal['winner'][i] in ids);assert hit==bool(a['hits'][i]) and len(ids)==int(a['k'][i]),(row['id'],i)
            records.append(dict(id=row['id'],calibration_row=i,category=str(cal['category'][i]),k=len(ids),hit=hit,full_candidate_ids_sha256=hashlib.sha256(ids.tobytes()).hexdigest()))
        if len(records)%64==0:print('CPU_SELECTOR_REVIEW',len(records),flush=True)
    assert len(records)==544
    primitive=read(R/'benchmark/NEW_PRIMITIVE_PROOF.json');assert len(primitive['records'])==72
    for key,m in models.items():
        if key=='channels':continue
        assert m['offsets'][0]==0 and m['offsets'][-1]==len(m['ids']) and np.all(np.diff(m['offsets'].astype('i8'))>=0)
        assert np.all(m['ids']<V)
        if key.startswith('bucket'):
            pp=int(key.rsplit('P',1)[1]);assert np.array_equal(np.bincount(m['ids'],minlength=V),np.full(V,pp))
        else:
            for table in range(8):assert np.array_equal(np.sort(m['ids'][table*V:(table+1)*V]),np.arange(V,dtype='u4'))
    result=dict(state='PASS_INDEPENDENT_NUMPY544_NEW_CALIBRATION_SELECTOR_CHECKS_AND_INDEX_SUPPORT',calibration_sha256=sha(R/'CALIBRATION.json'),parameter_sha256=sha(R/'PARAMETERS.json'),review_source_sha256=sha(Path(__file__)),sampled_rows=sample,records=records,full_new_primitive_pairs=72,board='NOT_RUN',scope='8 additional calibration rows across four categories; CPU independent full candidate construction/K/hits. Not a new independent quality cohort.')
    (R/'SELECTOR_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(result['state'])
if __name__=='__main__':main()
