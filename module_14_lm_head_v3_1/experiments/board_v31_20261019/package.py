"""Freeze the matched v3.1 hardware, PS init, test ELF and TCP loader."""
from pathlib import Path
import hashlib
import json
import shutil
from audit_hardware import audit

m = Path(__file__).resolve().parents[2]
out = m / 'reports/board_v31_20261019'
build = m / 'build/board_v31_20261019'
package = out / 'package'
assert not package.exists(), 'Preserve existing frozen package'
audit_result = audit()
files = {
    'BUILD_SOURCES.json': build / 'software/BUILD_SOURCES.json',
    'm14_v31_system_wrapper.bit': out / 'hardware/m14_v31_system_wrapper.bit',
    'm14_v31_single.xsa': out / 'hardware/m14_v31_single.xsa',
    'm14_v2_test.elf': build / 'software/m14_v2_test.elf',
    'm14_tcp_loader.elf': build / 'software/m14_tcp_loader.elf',
    'm14_pl_ddr_diag.elf': build / 'software/m14_pl_ddr_diag.elf',
    'm14_calib_timeout_test.elf': build / 'software/m14_calib_timeout_test.elf',
    'psu_init.tcl': build / 'workspace/m14_board_v31_platform/hw/psu_init.tcl',
}
assert all(p.is_file() and p.stat().st_size for p in files.values())
identity=json.loads(files['BUILD_SOURCES.json'].read_text(encoding='utf-8-sig'))
hash_file=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert identity['hardware_xsa_sha256']==hash_file(files['m14_v31_single.xsa'])
for name,digest in identity['source_sha256'].items():
    assert hash_file(m/name)==digest, 'Source changed after compilation: '+name
for name,digest in identity['elf_sha256'].items():
    assert hash_file(build/'software'/name)==digest, 'ELF changed after compilation: '+name
bd_psu = (m / 'board/build/m14_board_v31_20261019/m14_board_v31_20261019.gen/sources_1/bd'
          '/m14_v31_system/ip/m14_v31_system_zynq_ultra_ps_e_0_0/psu_init.tcl')
assert files['psu_init.tcl'].read_text(encoding='utf-8') == bd_psu.read_text(encoding='utf-8'), \
    'Platform init differs from generated BD init'
package.mkdir()
for name, src in files.items():
    shutil.copy2(src, package / name)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
profile = {
    'format': 'M14_BOARD_RUN_PROFILE_V2',
    'release': 'lm_head v3.1',
    'build_config': '0x30c08011',
    'capabilities': '0x00000382',
    'ip_clock_hz': 200_000_000,
    'clock_basis': 'nominal PL user clock (PS PL0 200 MHz); MIG ui_clk 200 MHz',
    'configured_pl_clock_hz': round(audit_result['configured_clock_mhz'] * 1_000_000),
    'configured_clock_note': 'Vivado PS configuration model; not a frequency-counter measurement',
    'data_memory': 'PL_DDR',
    'ps_ddr_data_fallback': False,
    'pl_ddr': {
        'device': '2 x Micron MT40A512M16LY (x16, single rank)',
        'phy_width_bits': 32,
        'capacity_bytes': 0x80000000,
        'mig_axi_data_width': 128,
        'mig_axi_addr_width': 31,
        'memory_clock_mhz': 800,
        'data_rate_mtps': 1600,
        'ui_clock_mhz': 200,
        'reference_clock_hz': 200_000_000,
        'reference_clock_pins': ['AL8', 'AL7'],
        'reset_pin': 'AM5',
        'reset_iostandard': 'LVCMOS12',
        'reset_drive_ma': 8,
    },
    'address_map': {
        'a53_window_base': '0x400000000',
        'a53_window_bytes': '0x80000000',
        'mig_local_bytes': '0x80000000',
        'hls_system_base': '0x400000000',
        'hls_address_kind': 'shared_system_address',
        'control_base': '0xA0000000',
        'calib_gpio_base': '0xA0020000',
        'weight_a53': '0x400100000',
        'weight_hls': '0x400100000',
        'weight_local': '0x00100000',
        'hidden_a53': '0x4104A8000',
        'hidden_hls': '0x4104A8000',
        'hidden_local': '0x104A8000',
        'history_a53': '0x4104A8700',
        'history_hls': '0x4104A8700',
        'history_local': '0x104A8700',
        'logits_a53': '0x4104AD140',
        'logits_hls': '0x4104AD140',
        'logits_local': '0x104AD140',
    },
    'hardware_xsa_sha256': sha(package / 'm14_v31_single.xsa'),
    'psu_init_sha256': sha(package / 'psu_init.tcl'),
    'board_ip': '192.168.0.190',
    'numeric_identity': 'bf16_rne_h8_interleave16_fp32_adjacent_tree_v2',
    'hls_source_sha256': {name:sha(m/'experiments/board_v31_20261019'/name)
                          for name in ('src/lm_head_v2.cpp','include/lm_head_v2.hpp')},
    'ip_component_sha256':sha(build/'hls/solution1/impl/ip/component.xml'),
}
(package / 'RUN_PROFILE.json').write_text(json.dumps(profile, indent=2) + '\n')
(package / 'ARTIFACTS.sha256').write_text(
    ''.join(sha(p) + '  ' + p.name + '\n' for p in sorted(package.iterdir()) if p.is_file()))
print('M14_V31_PACKAGE=' + str(package))
