"""Derive isolated system/PS/host-image tooling; never access any board."""
from pathlib import Path
import hashlib,json,re,shutil
M=Path(__file__).resolve().parents[1];X=M/'experiments/fusion_exp10_20261023';R=M/'reports/fusion_exp10_20261023_r1';SIGNATURE='0x4D345A0A'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=json.loads((X/'MANIFEST.json').read_text(encoding='utf-8'));p=manifest['parameters'];tag=manifest['config_tag'];sizes=[r['capacity'] for r in manifest['regions']]
    marker=X/'OFFLINE_SUPPORT_DERIVATION.json';assert not marker.exists(),'Preserve generated support revision'
    for d in ['scripts','reference','standalone','interface','constraints','experiments/board_v4_20261021','reports/selector_integration_fixture_20261021']:(X/d).mkdir(parents=True,exist_ok=True)
    originals={};derived={}
    def save(source,target,changes=()):
        text=source.read_text(encoding='utf-8');originals[source.relative_to(M).as_posix()]=sha(source)
        for old,new in changes:
            assert old in text,(source.name,old);text=text.replace(old,new)
        target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists(),target;target.write_text(text,encoding='utf-8');derived[target.relative_to(X).as_posix()]=sha(target)
    profile=M/'experiments/board_v4_20261021'
    for name in ['create_bd.tcl','build.tcl','apply_io_constraints.tcl']:
        changes=[('user.org:hls:lm_head_v4_selector:*','exp10.local:hls:lm_head_v4_selector:*')] if name=='create_bd.tcl' else []
        if name=='create_bd.tcl':changes += [('0x4D345301',SIGNATURE),('general.maxThreads 4','general.maxThreads 2')]
        if name=='build.tcl':changes += [('reports board_v4_20261021 hardware]','reports board_v4_20261021 hardware_r2]'),('-jobs 4','-jobs 1')]
        save(profile/name,X/'experiments/board_v4_20261021'/name,changes)
    shutil.copy2(M/'constraints/lm_head_v4_ddr4_pins.xdc',X/'constraints/lm_head_v4_ddr4_pins.xdc')
    save(M/'scripts/audit_selector_system.py',X/'scripts/audit_selector_system.py',[
        ("'user.org:hls:lm_head_v4_selector:4.0'","'exp10.local:hls:lm_head_v4_selector:4.10'"),('0x4D345301',SIGNATURE),("accepted=M.parent/'module_14_lm_head_v3_1/constraints/lm_head_v31_ddr4_pins.xdc'","accepted=Path("+repr(str(M.parent/'module_14_lm_head_v3_1/constraints/lm_head_v31_ddr4_pins.xdc'))+")")])
    # Source-neutral ELF architecture/LOAD audit; matching BSP is generated later.
    shutil.copy2(M/'scripts/audit_ps_elf.py',X/'scripts/audit_ps_elf.py')
    for name in ['platform.tcl','prepare_ps_platform.ps1','build_ps_software.ps1']:
        changes=[]
        if name=='platform.tcl':changes=[('set root [file dirname $module]',f'set root [file normalize {{{M.parent.as_posix()}}}]')]
        if name=='build_ps_software.ps1':changes=[('drivers/lm_head_v4_selector_v4_0/src','drivers/lm_head_v4_selector_v4_10/src'),("Join-Path (Split-Path -Parent $taskModule) 'ref/xemacpsif_physpeed.c'",f"Join-Path '{M.parent.as_posix()}' 'ref/xemacpsif_physpeed.c'"),('0x4D345301',SIGNATURE)]
        save(profile/name,X/'experiments/board_v4_20261021'/name,changes)
    # Copy PS/host support as separate sources; only descriptor/schema/signature change.
    for source in (M/'standalone').rglob('*'):
        if not source.is_file() or '__pycache__' in source.parts or source.suffix not in ['.c','.h','.ld','.py','.tcl']:continue
        target=X/'standalone'/source.relative_to(M/'standalone');changes=[]
        if source.name=='selector_control.c':
            changes=[('0x4D345301',SIGNATURE),('0x000d0001u','0x000d0002u'),('d[6]!=16384',f'd[6]!={p["T"]}'),('d[7]!=0',f'd[7]!={tag}u'),('{272269312,1792,18992,38895616,229376,229376,512,8388608,512,607744,607760,607760,1215488}','{'+','.join(map(str,sizes))+'}')]
        elif source.name=='arena_layout.h':changes=[('0x4D345301',SIGNATURE)]
        save(source,target,changes)
    save(M/'reference/selector_layout.py',X/'reference/selector_layout.py',[
        ('272269312,1792,18992,38895616,229376,229376,512,8388608,512,607744,607760,607760,1215488',','.join(map(str,sizes))),('k!=16384',f'k!={p["T"]}'),('reserved or (flags&2',f'reserved!={tag} or (flags&2'),('(0x4353344d,1,13,240,0)','(0x4353344d,2,13,240,0)')])
    (X/'reference/__init__.py').write_text('',encoding='utf-8')
    for name in ['selector_control_test.c','arena_loader_core_test.c','test_arena_transport.py','test_selector_ps_mailbox.py']:
        changes=[('0x4d345301',SIGNATURE)] if name=='selector_control_test.c' else []
        save(M/'tests'/name,X/'tests'/name,changes)
    save(M/'scripts/prepare_selector_memory_image.py',X/'scripts/prepare_selector_memory_image.py',[
        ("sources['hidden']=R/f'lowrank_fixture_20261021/{args.case}.hidden.bin'","sources['hidden']=M/f'fixture/{args.case}.hidden.bin'"),("sources['history']=R/f'lowrank_fixture_20261021/{args.case}.history.bin'","sources['history']=M/f'fixture/{args.case}.history.bin'"),('path=src.relative_to(M.parent).as_posix()','path=src.as_posix()'),("R/f'selector_chain_fixture_20261021/{args.case}.result.bin'","M/f'fixture/{args.case}.result.bin'")])
    regions=[dict(r,physical_address=hex(r['address'])) for r in manifest['regions']];layout=dict(state='EXP10_PRIVATE_OFFLINE_LAYOUT_NOT_RELEASED',physical_base='0x400000000',arena_bytes=320*2**20,physical_ddr_total_bytes=2*2**30,descriptor_offset=1048576,descriptor_bytes=240,alignment=64,regions=regions,allocated_end=manifest['allocated_end'],descriptor_version=2,parameters=p,config_tag=tag,signature=SIGNATURE)
    (X/'interface/PL_DDR_LAYOUT_V4.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    bindings={name:(M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin' if name=='weight' else X/'fixture'/file) for name,file in [('weight',''),('a','a.bf16.bin'),('bt','bt.bf16.bin'),('centers','router.centers.bin'),('norms','router.norms.bin'),('ranked','router.ranked.bin'),('counts','router.counts.bin')]}
    fixture=X/'reports/selector_integration_fixture_20261021'
    for name in ['descriptor_debug.bin','descriptor_production.bin']:shutil.copy2(X/'fixture'/name,fixture/name)
    bound=dict(state='PASS_SELECTED_CONFIG_ASSET_BINDING',files={n:sha(fixture/n) for n in ['descriptor_debug.bin','descriptor_production.bin']},binding={name:dict(path=path.as_posix(),sha256=sha(path),bytes=path.stat().st_size) for name,path in bindings.items()});(fixture/'MANIFEST.json').write_text(json.dumps(bound,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,h in originals.items():assert sha(M/name)==h,'Original source modified while deriving'
    marker.write_text(json.dumps(dict(state='DERIVED_OFFLINE_SUPPORT_NOT_YET_TESTED',signature=SIGNATURE,parameters=p,source_sha256=originals,derived_sha256=derived,layout_sha256=sha(X/'interface/PL_DDR_LAYOUT_V4.json'),scope='All tools/outputs in isolated experiment. No sockets/JTAG/target commands run.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('EXP10_OFFLINE_SUPPORT_DERIVED',len(derived))
if __name__=='__main__':main()
