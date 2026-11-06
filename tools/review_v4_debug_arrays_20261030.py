"""Recheck saved board bytes directly against pinned original C fixtures."""
from pathlib import Path
import json,struct,re,hashlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';rows=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for base in [M,M/'experiments/fusion_exp10_20261023']:
 for d in (base/'reports/board_debug_20261030_r2').glob('*'):
    if not (d/'NUMERIC_REVIEW.json').exists():continue
    p=json.loads((d/'PLAN.json').read_text());case=p['case'];k=p['k'];f=base/'fixture'
    scores=base/'reports/lowrank_fixture_20261021'/(case+'.scores.bin') if base==M else f/(case+'.scores.bin')
    ids=base/'reports/topk_fixture_20261021'/(case+'.expected.bin') if base==M else f/(case+'.expected.bin')
    sparse=base/'reports/selector_chain_fixture_20261021'/(case+'.sparse.bin') if base==M else f/(case+'.sparse.bin')
    final=base/'reports/selector_chain_fixture_20261021'/(case+'.result.bin') if base==M else f/(case+'.result.bin')
    for n,h in p['expected_files'].items():assert sha(ROOT/n)==h
    assert (d/'preview.bin').stat().st_size==151936*4 and (d/'preview.bin').read_bytes()==scores.read_bytes()
    merged=(d/'merged.bin').read_bytes();assert struct.unpack('<4I',merged[:16])==(0x4449344d,0x00040001,k,151936)
    assert merged[16:16+4*k]==ids.read_bytes() and (d/'sparse.bin').read_bytes()[:8*k]==sparse.read_bytes()[:8*k]
    guards=list(d.glob('guard_*.bin'));assert len(guards)==13 and all(g.read_bytes()==(0xabcdef).to_bytes(16,'little') for g in guards)
    fixture=base/'reports/selector_integration_fixture_20261021'
    assert (d/'descriptor_before.bin').read_bytes()==(d/'descriptor_restored.bin').read_bytes()==(fixture/'descriptor_production.bin').read_bytes()
    assert (d/'descriptor_debug.bin').read_bytes()==(fixture/'descriptor_debug.bin').read_bytes()
    log=(d/'capture.log').read_text(errors='replace');assert 'M4_FULL_DEBUG_CAPTURE_RETURNED_PENDING_BIT_REVIEW' in log and 'M4_DEBUG_ERROR:' not in log
    for name,value in zip(['TOKEN','SCORE','CRC'],struct.unpack('<3I',final.read_bytes()[:12])):assert int(re.search(r'^M4_DEBUG_'+name+r'=(\d+)$',log,re.M)[1])==value
    assert int(re.search(r'^M4_DEBUG_COUNT=(\d+)$',log,re.M)[1])==k
    row=dict(state='PASS_INDEPENDENT_FULL_BOARD_ARRAY_REVIEW',variant=p['variant'],case=case,preview=151936,ids=k,raw=k,guards=13,bit_tolerance=0,script_sha_matches=sha(d/'capture.tcl')==p['script_sha256'])
    assert row['script_sha_matches'];(d/'INDEPENDENT_REVIEW.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
print(json.dumps(rows,indent=2))
