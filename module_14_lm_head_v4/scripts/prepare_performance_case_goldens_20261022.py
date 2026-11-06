"""K-only workload preparation after quality closure; no fitting or hardware access."""
from pathlib import Path
import hashlib,json,struct,sys,zlib
import numpy as np

M=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(M))
from reference.selector_arithmetic import lowrank_preview,router_ids
from reference.routing import routed_candidates
from reference.candidate_head import run_candidate_head,encode_candidate_table
from prepare_selector_memory_image import digest_region,BLOCK

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def save(path,data):
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    root=M/'reports/performance_cases_20261022'
    quality=M/'reports/fixed_quality_20261022/RESULT.json'
    assert json.loads(quality.read_text())['state']=='PASS_PROPOSED_INDEPENDENT_POINT_RECALL_GATE'
    layout_path=M/'interface/PL_DDR_LAYOUT_V4.json';layout=json.loads(layout_path.read_text())
    regions={r['name']:r for r in layout['regions']}
    binding=json.loads((M/'reports/selector_integration_fixture_20261021/MANIFEST.json').read_text())
    sources={name:M.parent/info['path'] for name,info in binding['binding'].items()}
    for name,path in sources.items():assert sha(path)==binding['binding'][name]['sha256'],name
    # Read exactly the production-bound serialized parameters, not a fitted copy.
    a=np.fromfile(sources['a'],dtype='<u2').reshape(151936,128)
    bt=np.fromfile(sources['bt'],dtype='<u2').reshape(128,896)
    centers=np.fromfile(sources['centers'],dtype='<u2').reshape(128,896)
    norms=np.fromfile(sources['norms'],dtype='<f4')
    router=dict(vocab_size=151936,ranked_ids=np.fromfile(sources['ranked'],dtype='<u4').reshape(128,16384),counts=np.fromfile(sources['counts'],dtype='<u4'))
    weight=np.memmap(sources['weight'],mode='r',dtype='<u2',shape=(151936,896))
    descriptor=M/'reports/selector_integration_fixture_20261021/descriptor_production.bin'
    assert sha(descriptor)==binding['files'][descriptor.name]
    results={}
    for case in ['small','median','p95','max']:
        out=root/case;meta=json.loads((out/'MANIFEST.json').read_text())
        assert sha(out/'hidden.bf16.bin')==meta['hidden_sha256']
        assert sha(out/'history_bitmap.u32.bin')==meta['history_sha256']
        assert sha(M/meta['selection']['npz'])==meta['selection']['npz_sha256']
        assert not (out/'GOLDEN_RESULT.json').exists(),'Preserve prior result'
        hidden=np.fromfile(out/'hidden.bf16.bin',dtype='<u2')
        history=np.fromfile(out/'history_bitmap.u32.bin',dtype='<u4')
        vocab_ids=np.arange(151936,dtype='u4')
        seen=vocab_ids[((history[vocab_ids>>5]>>(vocab_ids&31))&1)!=0]
        routes,distances=router_ids(hidden,centers,norms)
        scores,z=lowrank_preview(hidden,a,bt.T.copy(),seen)
        routed,fallback=routed_candidates(router,routes,16384,range(151643,151657))
        top=np.argsort(-scores,kind='stable')[:16384].astype('u4')
        ids=vocab_ids if fallback else np.union1d(routed,top).astype('u4')
        assert len(ids)==meta['selection']['candidates'],'CPU/GPU candidate count differs'
        exact=run_candidate_head(hidden,weight,ids,history)
        ids.astype('<u4').tofile(out/'candidate_ids.u32.bin')
        (out/'candidate_table.m4id.bin').write_bytes(encode_candidate_table(ids,151936))
        scores.astype('<f4').tofile(out/'preview.f32.bin')
        exact['records'].tofile(out/'candidate_records.bin')
        exact['policy_scores'].astype('<f4').tofile(out/'policy_scores.f32.bin')
        expected=dict(token=exact['selected_token'],score_bits=f"0x{exact['selected_score_bits']:08x}",crc32=f"{exact['output_crc']:08x}")
        # A quality miss must remain visible; never select a replacement workload.
        dense_match=expected==meta['expected_dense']
        golden=dict(state='PASS_CPU_REFERENCE_NOT_RTL_OR_BOARD',case=case,candidates=len(ids),routes=routes.tolist(),fallback=bool(fallback),
          expected=expected,expected_dense=meta['expected_dense'],matches_dense=bool(dense_match),
          quality_result_sha256=sha(quality),selection=meta['selection'],
          candidate_records_crc32=f"{exact['candidate_records_crc32']:08x}",
          logical_weight_bytes=exact['logical_weight_bytes'],
          selection_rule=meta['selection_rule'],hardware_access='NONE',
          files={p.name:sha(p) for p in out.iterdir() if p.is_file()},
          reference_sources={p:sha(M/p) for p in ['reference/selector_arithmetic.py','reference/routing.py','reference/candidate_head.py','reference/numeric_contract.py']})
        save(out/'GOLDEN_RESULT.json',golden)
        arena=out/'arena';arena.mkdir(exist_ok=False);image=arena/'arena_production.bin'
        case_sources={**sources,'hidden':out/'hidden.bf16.bin','history':out/'history_bitmap.u32.bin'}
        info={}
        with image.open('w+b') as f:
            f.truncate(layout['arena_bytes']);f.seek(layout['descriptor_offset']);f.write(descriptor.read_bytes())
            for name,src in case_sources.items():
                r=regions[name];assert src.stat().st_size==r['capacity'],name
                f.seek(r['offset']);h=hashlib.sha256()
                with src.open('rb') as reader:
                    while chunk:=reader.read(BLOCK):f.write(chunk);h.update(chunk)
                info[name]=dict(path=src.relative_to(M.parent).as_posix(),bytes=src.stat().st_size,sha256=h.hexdigest())
            guard=(0xabcdef).to_bytes(16,'little')
            for r in regions.values():f.seek(r['offset']+r['capacity']);f.write(guard)
            f.flush();readback={}
            for name,data in info.items():
                readback[name]=digest_region(f,regions[name]['offset'],data['bytes'])
                assert readback[name]['sha256']==data['sha256'],name
            f.seek(layout['descriptor_offset']);assert f.read(240)==descriptor.read_bytes()
            for r in regions.values():f.seek(r['offset']+r['capacity']);assert f.read(16)==guard
            full=digest_region(f,0,layout['arena_bytes']);chunks=[];f.seek(0);offset=0
            while chunk:=f.read(BLOCK):
                chunks.append(dict(offset=offset,bytes=len(chunk),crc32=f'{zlib.crc32(chunk):08x}'));offset+=len(chunk)
            assert offset==layout['arena_bytes']
        save(arena/'MANIFEST.json',dict(state='PASS_OFFLINE_IMAGE_NOT_LOADED',case=case,image=image.name,image_bytes=layout['arena_bytes'],physical_base=layout['physical_base'],
          image_digest=full,layout_sha256=sha(layout_path),descriptor_sha256=sha(descriptor),descriptor_offset=layout['descriptor_offset'],flags=6,
          source_files=info,source_regions_readback=readback,chunk_bytes=BLOCK,chunks=chunks,guards_verified=len(regions),expected=expected,
          expected_scope='Frozen arithmetic CPU reference; K-only representative workload, not new quality certification or board result',
          hardware_access='NONE',loader='MATCHING_PRIVATE_M4AR_ELF_BUILT_TARGET_NOT_RUN',target_pl_ddr_readback='NOT_RUN',
          runtime_scratch='Zero initialized; candidate/preview goldens are external and are not preloaded into scratch',
          board_controller='Existing private_board CLI supports only original four fixtures; new case campaign binding still required'))
        results[case]=dict(candidates=len(ids),matches_dense=bool(dense_match),expected=expected,golden_sha256=sha(out/'GOLDEN_RESULT.json'),arena_sha256=full['sha256'])
        print(json.dumps(dict(case=case,**results[case])),flush=True)
    save(root/'PREPARATION_RESULT.json',dict(state='PASS_CPU_GOLDENS_AND_OFFLINE_IMAGES_LOCAL_PREFLIGHT_PENDING',cases=results,board='NOT_RUN',parameter_changes='NONE',script_sha256=sha(__file__)))

if __name__=='__main__':main()
