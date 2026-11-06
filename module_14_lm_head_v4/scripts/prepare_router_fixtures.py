from pathlib import Path
import hashlib,json,sys
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.numeric_contract import bf16_bits_to_float32
from reference.selector_arithmetic import router_ids
from reference.quality_data import load_split
from reference.routing import nearest_centers,routed_candidates
from reference.candidate_head import encode_candidate_table
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=M/'reports/selector_p2_20261021';lock=json.loads((folder/'PARAMETERS.json').read_text())
    assert sha(folder/'route_r128.npz')==lock['route_r128.npz']
    with np.load(folder/'route_r128.npz',allow_pickle=False) as a:router={k:a[k] for k in a.files}
    c=bf16_bits_to_float32(router['centers_bf16']);norm=np.sum(np.multiply(c,c,dtype=np.float32),axis=1,dtype=np.float32)
    data=load_split(M/'data/hidden_v1/calibration');out=M/'reports/router_fixture_20261021';out.mkdir(exist_ok=True)
    def save(name,content):
        p=out/name
        if p.exists():assert p.read_bytes()==content
        else:p.write_bytes(content)
    for name,array in [('centers',router['centers_bf16'].astype('<u2')),('norms',norm.astype('<f4')),('counts',router['counts'].astype('<u4')),('ranked',router['ranked_ids'].astype('<u4'))]:save('router.'+name+'.bin',array.tobytes())
    rows=[]
    for category in ('chinese','english','code','math'):
        i=int(np.flatnonzero(data['decode']&(data['category']==category))[0]);h=data['hidden'][i]
        ids,distance=router_ids(h,router['centers_bf16'],norm);prior=nearest_centers(bf16_bits_to_float32(h)[None,:],c,4)[0]
        candidates,fallback=routed_candidates(router,ids,16384,range(151643,151657));assert not fallback
        save(category+'.hidden.bin',h.astype('<u2').tobytes());save(category+'.routes.bin',ids.astype('<u4').tobytes());save(category+'.table.bin',encode_candidate_table(candidates,151936))
        prior_table=(M/'reports/topk_fixture_20261021'/f'{category}.routes.bin').read_bytes()
        rows.append(dict(category=category,index=i,selected_routes=ids.tolist(),prior_routes=prior.tolist(),same_route_order=bool(np.array_equal(ids,prior)),same_candidate_table=encode_candidate_table(candidates,151936)==prior_table,candidates=len(candidates)))
    result=dict(state='PASS',scope='Four calibration-only deterministic L2 examples; not independent quality certification',parameter_sha256=lock['route_r128.npz'],
        calibration_manifest_sha256=data['manifest_sha256'],center_norms='Frozen FP32 NumPy sum(center*center); no new fitting',
        hidden_norm_dot='H8/interleave16 separate FP32 mul/add',rows=rows,files={p.name:sha(p) for p in out.glob('*.bin')},
        source_sha256={p.relative_to(M).as_posix():sha(p) for p in [Path(__file__),M/'reference/selector_arithmetic.py']})
    (out/'MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(state='PASS',rows=rows)))
if __name__=='__main__':main()
