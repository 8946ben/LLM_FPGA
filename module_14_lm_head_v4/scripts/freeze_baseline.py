from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import importlib.metadata as metadata
M=Path(__file__).resolve().parents[1];ROOT=M.parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    source=ROOT/'module_14_lm_head_v3_1/reports/board_v31_20261019'
    comp=read(source/'comparison.json');delivery=read(ROOT/'deliverables/20261020_M14_V3_1_r1/DELIVERY_VALIDATION.json')
    assert comp['state']==delivery['state']=='PASS'
    frozen=ROOT/'deliverables/20261020_M14_V3_1_r1/M14_V3_1_20261020_r1/module_14_lm_head_v3_1'
    bound={}
    for name in ('src/lm_head_v2.cpp','include/lm_head_v2.hpp','reference/lm_head_v2_ref.py',
                 'reports/board_v31_20261019/package/ARTIFACTS.sha256','reports/board_v31_20261019/package/RUN_PROFILE.json'):
        p=frozen/name;bound[p.relative_to(ROOT).as_posix()]=sha(p)
    archive=ROOT/'deliverables/20261020_M14_V3_1_r1'/delivery['archive'];assert sha(archive)==delivery['sha256']
    model=ROOT/'artifacts/Qwen2.5-0.5B-Instruct/model.safetensors'
    with model.open('rb') as f:
        n=int.from_bytes(f.read(8),'little');header=json.loads(f.read(n))
    assert header['model.embed_tokens.weight']['shape']==[151936,896]
    assert header['model.embed_tokens.weight']['dtype']=='BF16'
    start,stop=header['model.embed_tokens.weight']['data_offsets']
    with model.open('rb') as f:
        f.seek(8+n+start);weight_sha=hashlib.sha256(f.read(stop-start)).hexdigest()
    assert weight_sha=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    result=dict(state='PASS',date='2026-10-21',scope='v4 offline baseline; v3.1 P1 reused without hardware rebuild',
        baseline_name='lm_head v3.1 PL DDR / dense / 200MHz',baseline_build_config='0x30c08011',
        baseline_capabilities='0x382',baseline_numeric_sha256=bound,
        canonical_weight_sha256=weight_sha,source_model_sha256=sha(model),baseline_performance=comp['candidate']['performance'],
        baseline_decode_equivalent_tokens_s=1000/comp['candidate']['performance']['ip_ms_median'],
        baseline_accepted_zip_sha256=delivery['sha256'],v4_hardware_identity='NOT_ASSIGNED',
        v4_hardware='NOT_BUILT_NOT_TESTED',source_numeric_reference='Frozen accepted reference copied byte-for-byte',
        upstream_direct_weights='DEFERRED: awaiting framework documents',board_access='NONE')
    (M/'BASELINE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('V4_BASELINE=PASS',flush=True)
if __name__=='__main__':main()
