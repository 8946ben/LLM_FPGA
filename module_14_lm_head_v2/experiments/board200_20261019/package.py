"""Freeze matched 200 MHz hardware, PS init, test ELF and fixed TCP loader."""
from pathlib import Path
import difflib, hashlib, json, shutil
from audit_hardware import audit

m=Path(__file__).resolve().parents[2]
out=m/'reports/board200_20261019'
build=m/'build/board200_20261019'
package=out/'package'
assert not package.exists(), 'Preserve existing frozen package'
audit_result=audit()
files={
    'm14_v2_system_wrapper.bit':out/'hardware/m14_v2_system_wrapper.bit',
    'm14_v2_single.xsa':out/'hardware/m14_v2_single.xsa',
    'm14_v2_test.elf':build/'software/m14_v2_test.elf',
    'm14_tcp_loader.elf':build/'software/m14_tcp_loader.elf',
    'psu_init.tcl':build/'workspace/m14_board200_platform/hw/psu_init.tcl',
}
assert all(p.is_file() and p.stat().st_size for p in files.values())
psu=files['psu_init.tcl'].read_text(encoding='utf-8')
bd_psu=m/'board/build/m14_board200_20261019/m14_board200_20261019.gen/sources_1/bd/m14_200_system/ip/m14_200_system_zynq_ultra_ps_e_0_0/psu_init.tcl'
assert psu==bd_psu.read_text(encoding='utf-8'), 'Platform init differs from generated BD init'
old_psu=(m/'reports/tcp_loader_package_20261010/psu_init.tcl').read_text(encoding='utf-8')
normalized=psu.replace('0x01010203','0x01010403')
normalized=normalized.replace('PL0_REF_CTRL_DIVISOR0                                               0x2',
                              'PL0_REF_CTRL_DIVISOR0                                               0x4')
assert normalized==old_psu,'Unexpected PS/DDR initialization changes'
(out/'psu_init_delta.diff').write_text(''.join(difflib.unified_diff(old_psu.splitlines(True),psu.splitlines(True),
    fromfile='frozen_100mhz/psu_init.tcl',tofile='board_200mhz/psu_init.tcl')),encoding='utf-8')
package.mkdir()
for name,src in files.items(): shutil.copy2(src,package/name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
profile=dict(format='M14_BOARD_RUN_PROFILE_V1',build_config='0x20c08011',
    ip_clock_hz=200_000_000,clock_basis='nominal PL user clock',
    configured_pl_clock_hz=round(audit_result['configured_clock_mhz']*1_000_000),
    configured_clock_note='Vivado PS configuration model; not a frequency-counter measurement',
    hardware_xsa_sha256=sha(package/'m14_v2_single.xsa'),
    psu_init_sha256=sha(package/'psu_init.tcl'),board_ip='192.168.0.190',
    numeric_identity='bf16_rne_h8_interleave16_fp32_adjacent_tree_v2')
(package/'RUN_PROFILE.json').write_text(json.dumps(profile,indent=2)+'\n')
(package/'ARTIFACTS.sha256').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(package.iterdir()) if p.is_file()))
print('M14_BOARD200_PACKAGE='+str(package))
