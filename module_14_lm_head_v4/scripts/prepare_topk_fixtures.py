"""Real calibration coarse-score fixtures; no fresh-test labels used."""
from pathlib import Path
import importlib.util,json,sys
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split
from reference.numeric_contract import bf16_bits_to_float32
from reference.routing import nearest_centers,routed_candidates
from reference.candidate_head import encode_candidate_table
from reference.radix_topk import radix_topk_ids
spec=importlib.util.spec_from_file_location('_base',M/'scripts/evaluate_selectors.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def main():
    out=M/'reports/topk_fixture_20261021';out.mkdir(parents=True,exist_ok=True)
    folder=M/'reports/selector_p2_20261021';hashes=json.loads((folder/'PARAMETERS.json').read_text());data=load_split(M/'data/hidden_v1/calibration')
    def load(n):
        assert base.sha(folder/n)==hashes[n]
        with np.load(folder/n,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
    router=load('route_r128.npz');low=load('lowrank_r128.npz');a=bf16_bits_to_float32(low['a_bf16']);b=bf16_bits_to_float32(low['b_bf16']);centers=bf16_bits_to_float32(router['centers_bf16'])
    rows=[]
    for category in ('chinese','english','code','math'):
        index=int(np.flatnonzero(data['decode']&(data['category']==category))[0]);start=(index//32)*32
        x=bf16_bits_to_float32(data['hidden'][start:start+32]);preview=((x@b)@a.T)[index-start].copy();seen=data['seen'][index]
        v=preview[seen];preview[seen]=np.where(v<0,v*np.float32(1.1),v/np.float32(1.1))
        routes=nearest_centers(x,centers,4)[index-start];ids,fallback=routed_candidates(router,routes,16384,base.mandatory_ids());assert not fallback
        coarse,meta=radix_topk_ids(preview,16384);full=np.sort(np.lexsort((np.arange(len(preview)),-preview))[:16384]);np.testing.assert_array_equal(coarse,full)
        union=np.union1d(ids,coarse).astype('<u4')
        files={category+'.scores.bin':preview.astype('<f4').tobytes(),category+'.routes.bin':encode_candidate_table(ids,151936),category+'.expected.bin':union.tobytes()}
        for name,content in files.items():
            p=out/name
            if p.exists():assert p.read_bytes()==content
            else:p.write_bytes(content)
        rows.append(dict(category=category,calibration_prediction=index,route_k=len(ids),top_k=16384,union_k=len(union),
            files={n:base.sha(out/n) for n in files},radix=meta))
    base.write(out/'MANIFEST.json',dict(state='PASS',source='Calibration only, BF16 rank128 factors and FP32 CPU BLAS; policy1.1 already applied globally',
        calibration_sha256=data['manifest_sha256'],parameter_sha256={n:hashes[n] for n in ('route_r128.npz','lowrank_r128.npz')},
        fixture_source_sha256=base.sha(Path(__file__)),rows=rows));print('REAL_TOPK_FIXTURES=PASS four categories')
if __name__=='__main__':main()
