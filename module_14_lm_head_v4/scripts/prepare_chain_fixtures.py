from pathlib import Path
import hashlib,json,struct,sys,zlib
import numpy as np
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.numeric_contract import compute_raw_logits
from reference.candidate_head import select_candidate
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=M/'reports/selector_chain_fixture_20261021';out.mkdir(exist_ok=True)
    weight_file=M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
    assert sha(weight_file)=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    weights=np.memmap(weight_file,dtype='<u2',mode='r',shape=(151936,896))
    low=M/'reports/lowrank_fixture_20261021';top=M/'reports/topk_fixture_20261021'
    cal=M/'data/hidden_v1/calibration';manifest=json.loads((cal/'MANIFEST.json').read_text())
    rows=[]
    def save(name,content):
        p=out/name
        if p.exists():assert p.read_bytes()==content
        else:p.write_bytes(content)
    for fixture in json.loads((low/'MANIFEST.json').read_text())['rows']:
        cat=fixture['category'];i=fixture['index'];offset=0
        for record in manifest['records']:
            if offset<=i<offset+record['steps']:
                p=cal/record['npz'];assert sha(p)==record['npz_sha256']
                with np.load(p,allow_pickle=False) as z:token=int(z['dense_token'][i-offset]);score_bits=int(z['dense_score_bits'][i-offset])
                break
            offset+=record['steps']
        else:raise AssertionError('row missing')
        ids=np.fromfile(top/f'{cat}.expected.bin',dtype='<u4');h=np.fromfile(low/f'{cat}.hidden.bin',dtype='<u2')
        raw=compute_raw_logits(h,weights[ids]);history=np.fromfile(low/f'{cat}.history.bin',dtype='<u4')
        policy,actual,score=select_candidate(raw,ids,151936,history,penalty=1.1)
        assert actual==token and int(score.view('u4'))==score_bits
        sparse=np.empty(len(ids),dtype=[('id','<u4'),('raw','<f4')]);sparse['id']=ids;sparse['raw']=raw
        crc=zlib.crc32(struct.pack('<II',token,score_bits))&0xffffffff
        save(cat+'.sparse.bin',sparse.tobytes());save(cat+'.result.bin',struct.pack('<III',token,score_bits,crc))
        rows.append(dict(category=cat,index=i,union_k=len(ids),token=token,score_bits=score_bits,output_crc=crc))
    result=dict(state='PASS',scope='Four calibration-only complete C-chain fixtures, canonical selected-row reference and frozen dense labels',
        canonical_weight_sha256=sha(weight_file),rows=rows,files={p.name:sha(p) for p in out.glob('*.bin')},
        fixture_manifest_sha256={f:sha(M/'reports'/f/'MANIFEST.json') for f in ('lowrank_fixture_20261021','router_fixture_20261021','topk_fixture_20261021')},
        source_sha256=sha(Path(__file__)))
    (out/'MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(state='PASS',rows=rows)))
if __name__=='__main__':main()
