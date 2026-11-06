"""Create a private offline PL-DDR arena fixture. Does not upload or open sockets."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,json,struct,zlib
M=Path(__file__).resolve().parents[1];R=M/'reports'
BLOCK=1048576
def digest_region(f,offset,size):
    f.seek(offset);h=hashlib.sha256();crc=0;first=None;last=b''
    while size:
        b=f.read(min(size,BLOCK));assert b,'Truncated arena image'
        h.update(b);crc=zlib.crc32(b,crc);first=b[:16] if first is None else first;last=b[-16:];size-=len(b)
    return dict(sha256=h.hexdigest(),crc32=f'{crc:08x}',first16_hex=first.hex(),last16_hex=last.hex())
def main():
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['chinese','english','code','math'],default='chinese');args=p.parse_args()
    layout=json.loads((M/'interface/PL_DDR_LAYOUT_V4.json').read_text(encoding='utf-8'))
    bind=json.loads((R/'selector_integration_fixture_20261021/MANIFEST.json').read_text(encoding='utf-8'))
    out=R/f'selector_arena_{args.case}_20261021';out.mkdir(exist_ok=False)
    image=out/'arena_production.bin';regions={r['name']:r for r in layout['regions']}
    descriptor=R/'selector_integration_fixture_20261021/descriptor_production.bin'
    assert hashlib.sha256(descriptor.read_bytes()).hexdigest()==bind['files'][descriptor.name]
    sources={name:M.parent/data['path'] for name,data in bind['binding'].items()}
    sources['hidden']=R/f'lowrank_fixture_20261021/{args.case}.hidden.bin'
    sources['history']=R/f'lowrank_fixture_20261021/{args.case}.history.bin'
    source_info={}
    with image.open('w+b') as f:
        f.truncate(layout['arena_bytes'])
        f.seek(layout['descriptor_offset']);f.write(descriptor.read_bytes())
        for name,src in sources.items():
            region=regions[name];assert src.stat().st_size==region['capacity'],name
            h=hashlib.sha256();f.seek(region['offset'])
            with src.open('rb') as reader:
                while b:=reader.read(BLOCK):f.write(b);h.update(b)
            actual=h.hexdigest()
            if name in bind['binding']:assert actual==bind['binding'][name]['sha256'],name
            source_info[name]=dict(path=src.relative_to(M.parent).as_posix(),bytes=src.stat().st_size,sha256=actual)
        guard=(0xabcdef).to_bytes(16,'little')
        for region in regions.values():f.seek(region['offset']+region['capacity']);f.write(guard)
        f.flush()
        readback={}
        for name,data in source_info.items():
            region=regions[name];readback[name]=digest_region(f,region['offset'],data['bytes'])
            assert readback[name]['sha256']==data['sha256'],name
        f.seek(layout['descriptor_offset']);assert f.read(240)==descriptor.read_bytes()
        for region in regions.values():f.seek(region['offset']+region['capacity']);assert f.read(16)==guard
        full=digest_region(f,0,layout['arena_bytes']);chunks=[];f.seek(0);offset=0
        while b:=f.read(BLOCK):
            chunks.append(dict(offset=offset,bytes=len(b),crc32=f'{zlib.crc32(b):08x}'));offset+=len(b)
        assert offset==layout['arena_bytes']
    expected=(R/f'selector_chain_fixture_20261021/{args.case}.result.bin').read_bytes()
    token,bits,crc=struct.unpack_from('<III',expected)
    manifest=dict(state='PASS_OFFLINE_IMAGE_NOT_LOADED',updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),
      case=args.case,image=image.name,image_bytes=layout['arena_bytes'],physical_base=layout['physical_base'],
      image_digest=full,layout_sha256=hashlib.sha256((M/'interface/PL_DDR_LAYOUT_V4.json').read_bytes()).hexdigest(),
      descriptor_sha256=hashlib.sha256(descriptor.read_bytes()).hexdigest(),descriptor_offset=layout['descriptor_offset'],
      flags=6,source_files=source_info,source_regions_readback=readback,chunk_bytes=BLOCK,chunks=chunks,
      guards_verified=13,expected=dict(token=token,score_bits=f'0x{bits:08x}',crc32=f'{crc:08x}'),
      expected_scope='Existing full C reference fixture; not a new quality test or board result',
      hardware_access='NONE',loader='NOT_IMPLEMENTED_FOR_THIS_ARENA',target_pl_ddr_readback='NOT_RUN',
      warning='Do not use the v3.1 fixed weight loader or its manifest with this full arena image; future loader must check image identity, total size, target CRC and input immutability')
    (out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'SELECTOR_ARENA=PASS offline {layout["arena_bytes"]}B chunks={len(chunks)} source_regions={len(readback)}; target=NOT_RUN')
if __name__=='__main__':main()
