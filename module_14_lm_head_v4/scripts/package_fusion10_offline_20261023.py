"""Bind Exp10 research-only offline assets, explicitly retain quality failure."""
from pathlib import Path
import hashlib,json,shutil,sys,zipfile
M=Path(__file__).resolve().parents[1];X=M/'experiments/fusion_exp10_20261023';R=M/'reports/fusion_exp10_20261023_r1'
sys.path.insert(0,str(X));sys.path.insert(0,str(X/'standalone'));sys.path.insert(0,str(X/'scripts'))
from upload_arena_tcp import inspect_image
from audit_ps_elf import audit as audit_elf
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    hw=X/'reports/board_v4_20261021/hardware_r2';audit=read(hw.parent/'hardware_audit_r2.json');swroot=X/'reports/ps_software_20261022_r1';sw=read(swroot/'BUILD_SOURCES.json');rtl=read(R/'RTL_QUALIFICATION.json');ip=read(R/'PRIVATE_IP_AUDIT.json');quality=read(R/'FINAL_QUALITY.json')
    assert audit['state']=='PASS_OFFLINE_SYSTEM' and rtl['state'].startswith('PASS_') and sw['state']=='PASS_MATCHING_V4_BSP_ELF_BUILD_ONLY'
    assert quality['state']=='QUALITY_FAIL_NO_RELEASE_NO_RETUNE';assert ip['signature']==sw['private_gpio_signature']=='0x4D345A0A'
    assert sha(hw/'m14_v4_system_wrapper.bit')==audit['bit_sha256']==sw['bit_sha256'];assert sha(hw/'m14_v4_single.xsa')==audit['xsa_sha256']==sw['hardware_xsa_sha256']
    for n,h in sw['source_sha256'].items():assert sha(X/n)==h,n
    for n,h in ip['files'].items():assert sha(X/'ip_repo/lm_head_v4_selector'/n)==h,n
    arenas={}
    for case in ['chinese','english','code','math']:
        manifest=X/f'reports/selector_arena_{case}_20261021/MANIFEST.json';meta=read(manifest);check=inspect_image(manifest.parent/meta['image'],manifest)
        arenas[case]=dict(manifest=manifest.relative_to(X).as_posix(),manifest_sha256=sha(manifest),image_sha256=check['sha256'],expected=meta['expected'],target='NOT_RUN',scope='Full C fixture, Chinese additionally RTL; not corpus-wide RTL')
    dest=X/'reports/board_v4_20261021/private_package_r1';dest.mkdir(exist_ok=False)
    for n in ['m14_v4_system_wrapper.bit','m14_v4_single.xsa']:shutil.copy2(hw/n,dest/n)
    with zipfile.ZipFile(hw/'m14_v4_single.xsa') as z:
        for n in ['psu_init.tcl','psu_init.c','psu_init.h']:(dest/n).write_bytes(z.read(n))
    elfs=[]
    for n,h in sw['elf_sha256'].items():
        p=X/'build/board_v4_20261021/software_r1'/n;assert sha(p)==h;shutil.copy2(p,dest/n);elfs.append(audit_elf(dest/n))
    assert sorted(elfs,key=lambda e:e['file'])==sorted(read(swroot/'ELF_LAYOUT_AUDIT.json')['files'],key=lambda e:e['file'])
    for src,n in [(hw.parent/'hardware_audit_r2.json','HARDWARE_AUDIT.json'),(R/'RTL_QUALIFICATION.json','RTL_RESULT.json'),(swroot/'BUILD_SOURCES.json','SOFTWARE_BUILD.json'),(swroot/'ELF_LAYOUT_AUDIT.json','ELF_LAYOUT_AUDIT.json'),(R/'FINAL_QUALITY.json','QUALITY_FAIL.json'),(R/'SELECTION_LOCK.json','SELECTION_LOCK.json')]:shutil.copy2(src,dest/n)
    meta=read(X/arenas['chinese']['manifest']);profile=dict(state='OFFLINE_RESEARCH_ONLY_QUALITY_FAILED_NOT_RELEASE',parameters=read(R/'SELECTION_LOCK.json')['parameters'],gpio_signature='0x4D345A0A',descriptor_version=2,config_tag='0x8507826e',public_abi_build='NOT_ASSIGNED',board_acceptance='NOT_RUN',arithmetic_quality=quality['state'],hardware_xsa_sha256=audit['xsa_sha256'],bit_sha256=audit['bit_sha256'],ethernet_base=sw['ethernet_base'],phy_patch_sha256=sw['phy_patch_sha256'],workspace_arena_fixtures=arenas,board_ip='192.168.0.190',loader_protocol='M4AR/v1/port1415',pl_ddr_base='0x400000000',arena_bytes=335544320,canonical_bf16_sha256=meta['source_files']['weight']['sha256'],clock_target_mhz=200,timing_scope='AXI-model RTL and offline STA; no physical FPGA decode/TTFT',scope='Workspace research bundle; no release qualification; no portable ZIP, no board operation')
    (dest/'PRIVATE_PROFILE.json').write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
    (dest/'README.md').write_text('# 实验10离线研究包：质量失败，禁止作为发布版本\n\nC256/R4/L8192+r64/Top16384。新问题decode漏19/14986，不满足整体和各类99.9%门槛。硬件功能、实现、配套软件的通过不能替代质量通过。\n\n本包绑定同一XSA、bit、PS初始化和两ELF。私有GPIO0x4D345A0A、descriptor_v2/config_tag0x8507826e，禁止混用原v4/v3.1镜像、descriptor或初始化。\n\n完整320MiB arena与源文件、host工具仍在本实验工作区；不是便携正式交付ZIP。loader是M4AR/v1/1415，使用64位PL DDR窗口0x400000000。BSP导出的实际GEM地址见profile，不能假设GEM0。\n\n没有连接、探测或操作板卡，真实MIG校准/目标CRC/RTL生产耗时/30次板测/1000次稳定性/整网decode及TTFT均未测试。未来若研究板测，必须重新安排板卡独占并明确接受此研究配置的质量失败；不要直接部署为生产版本。\n',encoding='utf-8')
    sums={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file()};(dest/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sums.items()),encoding='ascii')
    for n,h in sums.items():assert sha(dest/n)==h,n
    with zipfile.ZipFile(dest/'m14_v4_single.xsa') as z:
        bits=[n for n in z.namelist() if n.endswith('.bit')];assert len(bits)==1 and hashlib.sha256(z.read(bits[0])).hexdigest()==audit['bit_sha256']
        for n in ['psu_init.tcl','psu_init.c','psu_init.h']:assert z.read(n)==(dest/n).read_bytes()
    result=dict(state='PASS_OFFLINE_ASSET_BINDINGS_QUALITY_FAILED_NOT_RELEASE',package=str(dest.relative_to(M)),files_sha256=sums,arena=arenas,elf=elfs,quality=quality['state'],board='NOT_RUN',no_hardware_or_network=True)
    (R/'OFFLINE_PACKAGE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['state'],len(sums))
if __name__=='__main__':main()
