"""Private PL DDR layout/descriptor and parameter binding; no hardware access."""
from pathlib import Path
import hashlib,json,struct
M=Path(__file__).resolve().parents[1]
NAMES=['weight','hidden','history','a','bt','centers','norms','ranked','counts','preview','routed','merged','sparse']
SIZES=[272269312,1792,18992,38895616,229376,229376,512,8388608,512,607744,607760,607760,1215488]
BASE=0x400000000;WINDOW=320*1024*1024;DESC=1024*1024
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=M/'reports/selector_integration_fixture_20261021';out.mkdir(exist_ok=True)
    regions=[];offset=DESC+256
    for name,size in zip(NAMES,SIZES):
        offset=(offset+63)&~63
        regions.append(dict(name=name,offset=offset,capacity=size,physical_address=hex(BASE+offset),access='read' if len(regions)<9 else 'scratch_write'))
        offset+=size+64 # explicit unmapped guard between all reserved buffers
    assert offset<=WINDOW
    descriptor=struct.pack('<IHHII',0x4353344d,1,13,240,0)+struct.pack('<IfII',7,1.1,16384,0)
    descriptor+=b''.join(struct.pack('<QQ',r['offset'],r['capacity']) for r in regions)
    def save(name,content):
        p=out/name
        if p.exists():assert p.read_bytes()==content
        else:p.write_bytes(content)
    save('descriptor_debug.bin',descriptor)
    production=bytearray(descriptor);struct.pack_into('<I',production,16,6);struct.pack_into('<QQ',production,32+12*16,0,0)
    save('descriptor_production.bin',production)
    binding={
      'weight':M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin',
      'a':M/'reports/lowrank_fixture_20261021/a.bf16.bin','bt':M/'reports/lowrank_fixture_20261021/bt.bf16.bin',
      'centers':M/'reports/router_fixture_20261021/router.centers.bin','norms':M/'reports/router_fixture_20261021/router.norms.bin',
      'ranked':M/'reports/router_fixture_20261021/router.ranked.bin','counts':M/'reports/router_fixture_20261021/router.counts.bin'}
    assert sha(binding['weight'])=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    layout=dict(state='PRIVATE_OFFLINE_LAYOUT_NOT_RELEASED',physical_base=hex(BASE),arena_bytes=WINDOW,
      physical_ddr_total_bytes=2*1024**3,descriptor_offset=DESC,descriptor_bytes=240,
      scope='Standalone M14 reserves320MiB inside2GiB PL DDR; no system-wide allocator or board verification',
      alignment=64,regions=regions,allocated_end=offset,
      source_files={name:dict(path=p.relative_to(M.parent).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for name,p in binding.items()},
      requirements=['m_axi pl_ddr actual base must be0x400000000, topology must exclude PS DDR',
        'm_axi history_bitmap pointer must equal arena_base+HISTORY.offset; host validates/readbacks both64bit registers, both masters map exclusively to MIG',
        'Inputs/descriptor immutable throughout call; all active region capacities disjoint',
        'RUN requires status0 and stageDONE before publishing token; VALIDATE_ONLY never computes',
        'On-board loader must verify target PL DDR readback; host file hashes alone are not loading acceptance'])
    (M/'interface/PL_DDR_LAYOUT_V4.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest=dict(state='PASS',layout_sha256=sha(M/'interface/PL_DDR_LAYOUT_V4.json'),source_sha256=sha(Path(__file__)),
      files={p.name:sha(p) for p in out.glob('*.bin')},binding=layout['source_files'])
    (out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SELECTOR_LAYOUT=PASS bytes='+str(WINDOW)+' occupied='+str(offset)+' actual_board=NOT_RUN')
if __name__=='__main__':main()
