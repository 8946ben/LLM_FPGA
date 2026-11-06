"""Bind offline-qualified v4 hardware/software. No hardware/network access.

Internal workspace package, not a portable release or board acceptance.
Host tools and large source/arena assets remain in the current workspace.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,shutil,zipfile
M=Path(__file__).resolve().parents[1];R=M/'reports'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    hw=R/'board_v4_20261021/hardware_r2';audit=read(hw.parent/'hardware_audit_r2.json')
    rtl=read(R/'SELECTOR_INTEGRATION_RESULT_20261021.json')
    sw_report=R/'ps_software_20261022_r1';sw=read(sw_report/'BUILD_SOURCES.json')
    elf=read(sw_report/'ELF_LAYOUT_AUDIT.json')
    assert audit['state']=='PASS_OFFLINE_SYSTEM' and rtl['state']=='PASS_OFFLINE_INTEGRATED_SELECTOR_RTL'
    assert sw['state']=='PASS_MATCHING_V4_BSP_ELF_BUILD_ONLY' and elf['state']=='PASS_OFFLINE_ELF_LAYOUT'
    assert sha(hw/'m14_v4_system_wrapper.bit')==sw['bit_sha256']==audit['bit_sha256']
    assert sha(hw/'m14_v4_single.xsa')==sw['hardware_xsa_sha256']==audit['xsa_sha256']
    for n,h in sw['source_sha256'].items():assert sha(M/n)==h,n
    for n,h in rtl['source_sha256'].items():assert sha(M/n)==h,n
    for entry in elf['files']:assert entry['sha256']==sw['elf_sha256'][entry['file']]
    dest=hw.parent/'private_package_r1';dest.mkdir(exist_ok=False)
    for n in ('m14_v4_system_wrapper.bit','m14_v4_single.xsa'):shutil.copy2(hw/n,dest/n)
    with zipfile.ZipFile(hw/'m14_v4_single.xsa') as z:
        for n in ('psu_init.tcl','psu_init.c','psu_init.h'):(dest/n).write_bytes(z.read(n))
    for n,h in sw['elf_sha256'].items():
        p=M/'build/board_v4_20261021/software_r1'/n;assert sha(p)==h,n;shutil.copy2(p,dest/n)
    for src,name in [(hw.parent/'hardware_audit_r2.json','HARDWARE_AUDIT.json'),
                     (R/'SELECTOR_INTEGRATION_RESULT_20261021.json','RTL_RESULT.json'),
                     (sw_report/'BUILD_SOURCES.json','SOFTWARE_BUILD.json'),
                     (sw_report/'ELF_LAYOUT_AUDIT.json','ELF_LAYOUT_AUDIT.json')]:shutil.copy2(src,dest/name)
    arena=R/'selector_arena_chinese_20261021/MANIFEST.json';meta=read(arena)
    fixtures={}
    for case in ('chinese','english','code','math'):
        manifest=R/f'selector_arena_{case}_20261021/MANIFEST.json';data=read(manifest)
        fixtures[case]=dict(manifest=manifest.relative_to(M).as_posix(),manifest_sha256=sha(manifest),image_sha256=data['image_digest']['sha256'],
                            expected=data['expected'],target='NOT_RUN',scope='Existing C fixtures; full integrated RTL case is Chinese only')
    profile=dict(state='OFFLINE_PRIVATE_PACKAGE_NOT_BOARD_ACCEPTED',updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),
      release='lm_head v4 private development',public_abi_build='NOT_ASSIGNED',gpio_signature='0x4D345301',
      clock_target_mhz=200,configured_pl0_mhz=audit['generated_ps_pll_actual_mhz'],
      hardware_xsa_sha256=audit['xsa_sha256'],bit_sha256=audit['bit_sha256'],
      pl_ddr_base='0x400000000',arena_bytes=335544320,loader_protocol='M4AR/v1/port1415',board_ip='192.168.0.190',
      ethernet_base=sw['ethernet_base'],phy_patch_sha256=sw['phy_patch_sha256'],
      workspace_arena_manifest=str(arena.relative_to(M)),arena_manifest_sha256=sha(arena),arena_image_sha256=meta['image_digest']['sha256'],
      canonical_bf16_sha256=meta['source_files']['weight']['sha256'],
      workspace_arena_fixtures=fixtures,
      mailbox='M4PT/v1/0x51000000,128B header,128B records at+4096',
      timing_scope='A53 raw ticks around whole verified-token call; no hardware IP-cycle counter or LLM TTFT',
      original_hls_wrapper=rtl['original_hls_wrapper'],arithmetic_quality='Independent revised-arithmetic holdout not certified',
      board_acceptance='NOT_RUN',scope='Internal workspace bundle; host tools and arena/source assets remain in module, not portable release')
    (dest/'PRIVATE_PROFILE.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (dest/'README.md').write_text('''# v4 内部离线加载包（尚未板测）

此包绑定完整200MHz PL DDR系统、同一XSA提取的PS初始化文件和匹配BSP编译的两个ELF。
离线RTL/实现/软件构建通过不代表板卡验收或新算术独立质量通过。
公开M14 ABI/build_config尚未分配，GPIO2使用私有签名0x4D345301。

loader使用M4AR v1、1415端口、完整320MiB arena；不得混用旧M14W固定权重工具。
主机工具与大数据仍在本工作区：standalone/upload_arena_tcp.py（默认只验证本机文件），
standalone/selector_ps_mailbox.py，以及reports/selector_arena_chinese_20261021/。
本目录是内部工作区包，尚未制作正式可移交/可独立运行的ZIP。

取得新的板卡独占安排后，先使用本包的PS初始化与bit完整初始化，再运行loader并验证目标回读；
不要沿用v3.1初始化或未经核实地保留旧镜像。loader到计时ELF的板测交接须先确认GEM DMA停机，再替换ELF。
selector_test RUN只接受生产flags6，要求arena仍为刚加载的原始镜像（含scratch初值），先做目标整份CRC，
随后在本次进程中固定输入运行3次warmup、30次计时和1000次稳定调用。
每批次结束后scratch已变化，新进程RUN前需重新加载完整arena。
mailbox/记录使用PS DDR；其地址与loader诊断区重合，必须在替换loader后使用。

真实板测仍须按standalone/BOARD_ACCEPTANCE_PLAN.md补齐数值、多步、错误路径与实际性能。
本脚本/打包过程没有连接、探测或操作板卡。
''',encoding='utf-8')
    lines=[f'{sha(p)}  {p.name}' for p in sorted(dest.iterdir()) if p.is_file()]
    (dest/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='ascii')
    for line in lines:
        h,n=line.split('  ',1);assert sha(dest/n)==h,n
    progress_path=M/'PROGRESS.json';progress=read(progress_path)
    progress.setdefault('ps_preparation',{}).update(
      matching_software_manifest='reports/ps_software_20261022_r1/BUILD_SOURCES.json',
      private_package_profile='reports/board_v4_20261021/private_package_r1/PRIVATE_PROFILE.json')
    progress['milestones']['P4']='Integrated fullV repaired-wrapper RTL, complete200MHz system, matching BSP/two ELFs and internal package PASS_OFFLINE_ONLY; target/quality/release acceptance pending'
    for name in ('reports/ps_software_20261022_r1/BUILD_SOURCES.json','reports/ps_software_20261022_r1/ELF_LAYOUT_AUDIT.json','reports/board_v4_20261021/private_package_r1/PRIVATE_PROFILE.json'):
        if name not in progress['evidence']:progress['evidence'].append(name)
    progress_path.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('M14_V4_PRIVATE_PACKAGE=PASS_OFFLINE_ONLY '+str(dest)+'; BOARD_NOT_RUN')
if __name__=='__main__':main()
