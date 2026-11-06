"""Freeze four calibration-only deterministic projection fixtures; no fitting."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split
from reference.selector_arithmetic import lowrank_preview
from reference.hybrid_selector import stable_topk_ids

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=M/'reports/selector_p2_20261021';lock=json.loads((folder/'PARAMETERS.json').read_text())
    assert sha(folder/'lowrank_r128.npz')==lock['lowrank_r128.npz']
    with np.load(folder/'lowrank_r128.npz',allow_pickle=False) as a:af=a['a_bf16'];bf=a['b_bf16']
    data=load_split(M/'data/hidden_v1/calibration');out=M/'reports/lowrank_fixture_20261021';out.mkdir(exist_ok=True)
    rows=[]
    def save(name,values):
        p=out/name;content=np.ascontiguousarray(values).tobytes()
        if p.exists():assert p.read_bytes()==content
        else:p.write_bytes(content)
    save('a.bf16.bin',af.astype('<u2'));save('bt.bf16.bin',bf.T.astype('<u2'))
    for category in ('chinese','english','code','math'):
        index=int(np.flatnonzero(data['decode']&(data['category']==category))[0]);h=data['hidden'][index]
        scores,z=lowrank_preview(h,af,bf,data['seen'][index]);history=np.zeros(151936//32,dtype='<u4')
        for id in data['seen'][index]:history[int(id)//32]|=np.uint32(1<<int(id%32))
        save(category+'.hidden.bin',h.astype('<u2'));save(category+'.history.bin',history)
        save(category+'.scores.bin',scores.astype('<f4'));save(category+'.z.bin',z.astype('<f4'))
        original=np.fromfile(M/'reports/topk_fixture_20261021'/f'{category}.scores.bin',dtype='<f4')
        # Scores already have penalty, so do not apply penalty a second time.
        current=stable_topk_ids(scores,np.empty(0,dtype='u4'),16384)
        prior=stable_topk_ids(original,np.empty(0,dtype='u4'),16384)
        route=np.fromfile(M/'reports/topk_fixture_20261021'/f'{category}.routes.bin',dtype='<u4')[4:]
        union=np.union1d(route,current);winner=int(data['winner'][index])
        rows.append(dict(category=category,index=index,changed_preview_bits=int(np.sum(scores.view('u4')!=original.view('u4'))),
            max_abs_error=float(np.max(np.abs(scores-original))),topk_symmetric_difference=len(np.setxor1d(current,prior)),
            hybrid_covers_dense_winner=bool(winner in union),dense_winner=winner))
    result=dict(state='PASS',scope='Four calibration decode rows; not independent holdout or full calibration quality',
        parameter_sha256=lock['lowrank_r128.npz'],calibration_manifest_sha256=data['manifest_sha256'],rows=rows,
        arithmetic='B:H8/interleave16; A:adjacent8 then adjacent16, separate FP32 mul/add, global-history penalty1.1',
        files={p.name:sha(p) for p in out.glob('*.bin')},source_sha256={p.relative_to(M).as_posix():sha(p) for p in [Path(__file__),M/'reference/selector_arithmetic.py']})
    (out/'MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(state='PASS',rows=rows),ensure_ascii=False))
if __name__=='__main__':main()
