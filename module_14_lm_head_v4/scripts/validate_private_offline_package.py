"""Read-only verification of internal bundle; never opens a target connection."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, zipfile
from audit_ps_elf import audit as audit_elf

M=Path(__file__).resolve().parents[1]
R=M/'reports'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    dest=R/'board_v4_20261021/private_package_r1'
    out=R/'resume_20261022/PRIVATE_PACKAGE_VALIDATION.json'
    assert not out.exists(),'Preserve previous validation'
    sums={}
    for line in (dest/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split('  ',1)
        assert Path(name).name==name and name not in sums
        assert sha(dest/name)==digest,name
        sums[name]=digest
    assert set(sums)=={p.name for p in dest.iterdir() if p.is_file()}-{'SHA256SUMS.txt'}
    profile=read(dest/'PRIVATE_PROFILE.json');hw=read(dest/'HARDWARE_AUDIT.json')
    rtl=read(dest/'RTL_RESULT.json');sw=read(dest/'SOFTWARE_BUILD.json')
    assert profile['state']=='OFFLINE_PRIVATE_PACKAGE_NOT_BOARD_ACCEPTED'
    assert profile['board_acceptance']=='NOT_RUN' and profile['public_abi_build']=='NOT_ASSIGNED'
    assert hw['state']=='PASS_OFFLINE_SYSTEM' and rtl['state']=='PASS_OFFLINE_INTEGRATED_SELECTOR_RTL'
    assert sw['state']=='PASS_MATCHING_V4_BSP_ELF_BUILD_ONLY'
    assert profile['hardware_xsa_sha256']==hw['xsa_sha256']==sw['hardware_xsa_sha256']==sums['m14_v4_single.xsa']
    assert profile['bit_sha256']==hw['bit_sha256']==sw['bit_sha256']==sums['m14_v4_system_wrapper.bit']
    with zipfile.ZipFile(dest/'m14_v4_single.xsa') as z:
        bits=[n for n in z.namelist() if n.endswith('.bit')]
        assert len(bits)==1 and hashlib.sha256(z.read(bits[0])).hexdigest()==profile['bit_sha256']
        for n in ('psu_init.tcl','psu_init.c','psu_init.h'): assert z.read(n)==(dest/n).read_bytes(),n
    elf=[audit_elf(dest/n) for n in sw['elf_sha256']]
    assert all(e['sha256']==sums[e['file']]==sw['elf_sha256'][e['file']] for e in elf)
    assert elf==read(dest/'ELF_LAYOUT_AUDIT.json')['files']
    arenas={}
    for case,fixture in profile['workspace_arena_fixtures'].items():
        preflight=read(R/f'resume_20261022/ARENA_PREFLIGHT_{case}.json')
        manifest=M/fixture['manifest'];meta=read(manifest)
        assert fixture['manifest_sha256']==preflight['manifest_sha256']==sha(manifest)
        assert fixture['image_sha256']==preflight['image_sha256']==sha(manifest.parent/meta['image'])
        assert preflight['state']=='PASS_HOST_PREFLIGHT_TARGET_NOT_RUN'
        assert meta['source_files']['weight']['sha256']==profile['canonical_bf16_sha256']
        arenas[case]=fixture['image_sha256']
    result=dict(state='PASS_INTERNAL_OFFLINE_PACKAGE_ONLY',updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),
                package=dest.relative_to(M).as_posix(),files_checked=len(sums),files_sha256=sums,
                elf_layout=elf,arena_sha256=arenas,board='NOT_RUN',quality='INDEPENDENT_REVISED_ARITHMETIC_NOT_CERTIFIED',
                scope='Internal workspace bundle, not portable release/ZIP or board acceptance')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('M14_V4_PRIVATE_PACKAGE_VALIDATION=PASS_OFFLINE_ONLY; NOT_BOARD')

if __name__=='__main__': main()
