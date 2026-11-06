"""Independent saved-array and Python-integer bit-count audit; no GPU/fit."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split
R=M/'reports/fusion_exp10_20261023_r1';V=151936
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    plan=read(R/'PLAN.json');result=read(R/'CALIBRATION.json');short=read(R/'SHORTLIST.json');cal=load_split(M/'data/hidden_v1/calibration');mask=cal['decode'];n=len(mask);assert len(result['configurations'])==432 and sha(R/'CALIBRATION.json')==short['calibration_sha256']
    cache=read(R/'CACHE.json');saved={};qualified=[]
    for row in result['configurations']:
        path=R/row['arrays'];assert sha(path)==row['sha256']
        with np.load(path,allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
        assert a['hits'].shape==(n,);np.testing.assert_array_equal(a['hits'],a['route_hits']|a['lowrank_hits']);assert np.all(a['k']>=np.maximum(a['route_k'],a['lowrank_k'])) and np.all(a['k']<=np.minimum(V,a['route_k']+a['lowrank_k']))
        for phase,use in [('all',np.ones(n,bool)),('decode',mask),('prefill',~mask)]:
            q=row['quality'][phase];assert q['misses']==int((~a['hits'][use]).sum()) and q['steps']==int(use.sum()) and q['recall']==float(a['hits'][use].mean())
            for cat,item in q['by_category'].items():
                selected=use&(cal['category']==cat);assert item['misses']==int((~a['hits'][selected]).sum()) and item['recall']==float(a['hits'][selected].mean())
        p=row['parameters'];logical=2*p['r']*(V+896)+2*p['C']*896+4*a['list_entries'].astype('u8')+1792*a['k'].astype('u8');assert row['logical_mean_decode_bytes']==float(logical[mask].mean());q=row['quality']['decode'];gate=q['recall']>=.999 and all(x['recall']>=.999 for x in q['by_category'].values());valid=gate and row['quality']['all']['misses']==0 and not a['fallback'].any() and row['estimated_arena_bytes']<=320*2**20 and int(a['k'][mask].max())<=3*V//4 and int(np.sort(a['k'][mask])[int(np.ceil(.95*mask.sum()))-1])<=V//2;assert row['selection_qualified']==bool(valid)
        if valid:qualified.append(row)
        if any(row['id']==x['id'] for x in short['configurations']):saved[row['id']]=a
    qualified.sort(key=lambda x:(x['logical_mean_decode_bytes'],x['candidate_decode']['p95'],x['id']));expected=qualified[:5]
    for rank in [32,64,128]:
        row=next((x for x in qualified if x['parameters']['r']==rank),None)
        if row and not any(x['id']==row['id'] for x in expected):expected.append(row)
    assert [x['id'] for x in expected]==[x['id'] for x in short['configurations']]
    independent=[]
    for row in short['configurations']:
        p=row['parameters'];route=cache['items'][f'route:C{p["C"]}_R{p["R"]}_L{p["L"]}'];lr=cache['items'][f'lowrank:r{p["r"]}_T{p["T"]}'];assert sha(R/route['path'])==route['sha256'] and sha(R/lr['path'])==lr['sha256'];rp=np.memmap(R/route['path'],mode='r',dtype='u1',shape=(n,V//8));lp=np.memmap(R/lr['path'],mode='r',dtype='u1',shape=(n,V//8));a=saved[row['id']]
        for i in range(n):
            merged=int.from_bytes(rp[i].tobytes(),'little')|int.from_bytes(lp[i].tobytes(),'little');assert merged.bit_count()==int(a['k'][i]);assert bool((merged>>int(cal['winner'][i]))&1)==bool(a['hits'][i])
        independent.append(dict(id=row['id'],all_rows_python_integer_union_bit_count_match=True))
    out=dict(state='PASS432_COUNTS_COVERAGE_OBJECTIVE_SHORTLIST_AND_INTEGER_UNION',source_sha256=sha(Path(__file__)),calibration_manifest_sha256=cal['manifest_sha256'],configurations=432,qualified=len(qualified),shortlist=independent,selected_objective_minimum=expected[0]['id'],independent_test='NOT_OPENED',board='NOT_RUN');(R/'CALIBRATION_REVIEW.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
