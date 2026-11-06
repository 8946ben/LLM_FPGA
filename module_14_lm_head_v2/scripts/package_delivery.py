"""Create an immutable, portable M14 handoff snapshot (no board access)."""
from __future__ import annotations
import argparse
import csv
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parent
VERSION = 'M14_V2_20261010_r1'
NS = {'s': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
LIMITS = [
    'Public ABI enum/header, instance id, address assignment and timeout class pending architecture freeze',
    'Board acceptance limited to independent Decode/penalty ON/H8/V1; other mode performance matrix pending',
    'Input trace is historical FP16 converted to BF16; native M06 V2 BF16 trace pending',
    'Prefill T=36/64 upstream last-row selection and integrated path pending',
    'M03 must enforce range/capacity/layout/owner/generation/alias; boundary address tests pending',
    'Internal AXI counters do not replace external HP2 APM; external monitor pending',
    'No PL DDR/MIG in independent image; full system integration pending',
    'Numeric bit-exact guarantee scoped to archived finite trace and tool version; extreme/subnormal matrix pending',
]

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def copy_tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        '__pycache__', '*.pyc', '.Xil', 'build', 'workspace', 'tcp_workspace', '.cache'))

def registers(component):
    root = ET.parse(component).getroot()
    output = []
    for r in root.findall('s:memoryMaps/s:memoryMap/s:addressBlock/s:register', NS):
        reset = r.find('s:reset/s:value', NS)
        output.append(dict(name=r.findtext('s:name', namespaces=NS),
                           offset=int(r.findtext('s:addressOffset', namespaces=NS), 0),
                           width_bits=int(r.findtext('s:size', namespaces=NS), 0),
                           access=r.findtext('s:access', namespaces=NS),
                           reset=int(reset.text, 0) if reset is not None else None))
    return output

def write_sums(base):
    files = sorted(p for p in base.rglob('*') if p.is_file() and p != base / 'SHA256SUMS')
    (base / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(base).as_posix()}\n' for p in files), encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory, must not exist')
    parser.add_argument('--catalog-log', type=Path, help='Successful Vivado catalog validation log of this unchanged exported IP')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT.resolve()) or output.exists():
        raise ValueError('Output must be a new directory within this workspace')
    package = output / VERSION
    m = package / MODULE.name
    m.mkdir(parents=True)
    for name in ['src', 'include', 'tb', 'reference', 'golden', 'scripts', 'drivers', 'standalone', 'board']:
        copy_tree(MODULE / name, m / name)
    for name in ['NUMERIC_CONTRACT.md', 'BOARD_TEST_PLAN.md', 'DELIVERY_NOTES.md']:
        shutil.copy2(MODULE / name, m / name)
    # IP runtime files, without the generated Vivado project/cache or nested zip.
    exported = MODULE / 'build/lm_head_v2_export/solution1/impl/ip'
    ip = m / 'ip_repo/lm_head_v2'
    ip.mkdir(parents=True)
    for name in ['constraints', 'doc', 'drivers', 'example', 'hdl', 'misc', 'subcore', 'xgui']:
        if (exported / name).exists():
            copy_tree(exported / name, ip / name)
    for name in ['component.xml', 'auxiliary.xml', 'lm_head_v2_info.xml', 'sysgen_info.xml']:
        shutil.copy2(exported / name, ip / name)
    if sha(ip / 'component.xml') != sha(MODULE / 'reports/hls_2021_1/component.xml'):
        raise AssertionError('Exported IP differs from archived component.xml')
    generated = next((ip / 'drivers').glob('*/src'))
    shutil.copytree(generated, m / 'drivers/generated')
    if sha(generated / 'xlm_head_v2_hw.h') != sha(MODULE / 'reports/hls_2021_1/xlm_head_v2_hw.h'):
        raise AssertionError('Generated register header differs from archived header')
    reports = m / 'reports'
    reports.mkdir()
    mapping = {'hls_2021_1': 'hls', 'board_build': 'implementation', 'numeric_20261009': 'numeric',
               'board_package_20261009': 'board_package_20261009', 'tcp_loader_package_20261010': 'tcp_loader_package_20261010'}
    for source, dest in mapping.items():
        copy_tree(MODULE / 'reports' / source, reports / dest)
    if args.catalog_log:
        catalog_text = args.catalog_log.read_text(encoding='utf-8', errors='replace')
        if '\nM14_V2_IP_VERIFY=PASS' not in catalog_text or '\nM14_V2_IP_VLNV=user.org:llm_fpga:lm_head_v2:2.0' not in catalog_text:
            raise AssertionError('Catalog log lacks actual PASS/VLNV markers')
        shutil.copy2(args.catalog_log, reports / 'hls/delivery_ip_catalog.log')
    numeric_map = MODULE / 'standalone/build/m14_v2_test.map'
    if sha(numeric_map) != 'a99c7dc56f6aa357ae77fd2fe7a4f45382ad12dd862485c3c5fe195bd949e6e0':
        raise AssertionError('Numeric ELF linker map changed from accepted build')
    shutil.copy2(numeric_map, reports / 'numeric/m14_v2_test.map')
    # Stable legacy aliases keep the existing rebuild scripts usable.
    (reports / 'board_build').mkdir()
    shutil.copy2(reports / 'board_package_20261009/m14_v2_single.xsa', reports / 'board_build/m14_v2_single.xsa')
    for name in ['20260930_HLS_VALIDATION_2021_1.md', '20260930_VIVADO_VALIDATION_2021_1.md',
                 '20260930_STANDALONE_BUILD_2021_1.md', '20261009_NUMERIC_CLOSURE.md',
                 '20261010_BOARD_ACCEPTANCE.md', '20261010_ACCEPTANCE_METADATA.json']:
        shutil.copy2(MODULE / 'reports' / name, reports / name)
    runs = reports / 'board_runs'
    runs.mkdir()
    for directory in (MODULE / 'reports/board_runs').glob('20261010*'):
        if directory.is_dir():
            copy_tree(directory, runs / directory.name)
    # Preserve raw original evidence. Only this derivative relocates directory references.
    campaign_dir = runs / '20261010_104006_168_acceptance'
    original = json.loads((campaign_dir / 'campaign.json').read_text(encoding='utf-8-sig'))
    portable = json.loads(json.dumps(original))
    portable['package_dir'] = 'reports/board_package_20261009'
    relocations = []
    for r in portable['records']:
        old = r['source_run']
        name = old.replace('\\', '/').split('/')[-1]
        new = 'reports/board_runs/' + name
        if not (m / new / 'mailbox_output.bin').is_file():
            raise AssertionError('Missing campaign run ' + new)
        r['source_run'] = new
        relocations.append({'original': old, 'portable': new})
    dump(campaign_dir / 'campaign_portable.json', portable)
    dump(package / 'provenance/evidence_path_relocations.json', relocations)
    # Actual assets, sufficient for reproduction without the original safetensors.
    assets = package / 'artifacts/module14_v2_assets'
    shutil.copytree(ROOT / 'artifacts/module14_v2_assets', assets)
    ref = package / 'ref'
    ref.mkdir()
    shutil.copy2(ROOT / 'ref/xemacpsif_physpeed.c', ref / 'xemacpsif_physpeed.c')
    specs = package / 'specifications'
    specs.mkdir()
    for name in ['PS_PL 全模块参数与接口字段说明书.md', 'PS_PL 全模块架构、详细设计与统一集成实施计划.md']:
        shutil.copy2(ROOT / 'doc/0924' / name, specs / name)
    # Package-only portability edits; production C++ and PS software remain bit-identical.
    changes = []
    def replace(relative, old, new):
        path = m / relative
        before = path.read_text(encoding='utf-8-sig')
        if old not in before:
            raise AssertionError('Missing portability edit anchor: ' + relative)
        after = before.replace(old, new)
        path.write_text(after, encoding='utf-8')
        changes.append({'file': relative, 'reason': old + ' -> ' + new})
    replace('board/create_m14_v2_single_bd.tcl',
            '"build" "lm_head_v2_export" "solution1" "impl" "ip"', '"ip_repo" "lm_head_v2"')
    replace('board/create_m14_v2_single_bd.tcl', 'set project_name "m14_v2_single"',
            'set rebuilt_ip [file join $repo_root "module_14_lm_head_v2" "build" "lm_head_v2_export" "solution1" "impl" "ip"]\n'
            'if {[file exists [file join $rebuilt_ip "component.xml"]]} { set ip_repo $rebuilt_ip }\n\n'
            'set project_name "m14_v2_single"')
    replace('board/run_vivado.ps1', "'build\\lm_head_v2_export\\solution1\\impl\\ip'", "'ip_repo\\lm_head_v2'")
    replace('board/run_vivado.ps1', '$script = switch ($Action)',
            "$rebuiltIp = Join-Path $moduleDir 'build\\lm_head_v2_export\\solution1\\impl\\ip'\n"
            "if (Test-Path -LiteralPath (Join-Path $rebuiltIp 'component.xml')) { $ipRepository = $rebuiltIp }\n"
            '$script = switch ($Action)')
    replace('standalone/program_board.ps1',
            'Join-Path $standaloneDir "workspace\\m14_v2_platform\\hw\\psu_init.tcl"',
            'Join-Path $moduleDir "reports\\tcp_loader_package_20261010\\psu_init.tcl"')
    replace('standalone/build_tcp_loader.ps1',
            "foreach ($file in @('platform_zynqmp.c','platform.h','platform_config.h')) {\n    Copy-Item -LiteralPath (Join-Path $root \"realFpga\\vitis\\workspace\\lm_head_net_diag\\src\\$file\") -Destination (Join-Path $src $file) -Force\n}",
            "# Platform support sources are already included in tcp_loader; retain their Xilinx license headers.")
    replace('standalone/program_board_tcp.ps1',
            "[string]$PythonExe='C:\\Users\\ben\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'",
            '[string]$PythonExe=$env:PYTHON')
    replace('standalone/program_board_tcp.ps1', "$ErrorActionPreference='Stop'",
            "$ErrorActionPreference='Stop'\nif (-not $PythonExe) { $PythonExe=(Get-Command python -ErrorAction Stop).Source }")
    dump(package / 'provenance/package_only_edits.json', changes)
    # Record every delivered source difference for a reviewer.
    patch = []
    for rel in dict.fromkeys(c['file'] for c in changes):
        before = (MODULE / rel).read_text(encoding='utf-8-sig').splitlines(keepends=True)
        after = (m / rel).read_text(encoding='utf-8').splitlines(keepends=True)
        patch.extend(difflib.unified_diff(before, after, fromfile='workspace/' + rel, tofile='delivery/' + rel))
    (package / 'provenance/portability.patch').write_text(''.join(patch), encoding='utf-8')
    # Public enum values must not be invented. Local implemented values are explicit.
    base = json.loads((MODULE / 'module_manifest.json').read_text(encoding='utf-8'))
    base.update(version=VERSION, delivery_date='2026-10-10', module_owner='张本', recipient='喻燕萍',
                delivery_state='independent_board_pass_integration_candidate', instance_id=None,
                numeric_impl='bf16_rne_h8_interleave16_fp32_adjacent_tree_v2',
                tool_versions={'vitis_hls': '2021.1 build 3247384', 'vivado': '2021.1 build 3247384', 'vitis': '2021.1'},
                hls={'top_latency_cycles': None, 'top_latency_reason': 'dynamic dataflow; report shows ?',
                     'dot_word_loop_ii': 1, 'estimated_clock_ns': 8.660, 'clock_uncertainty_ns': 2.70},
                implementation={'scope': 'entire independent single-module BD post-route, not isolated kernel',
                                'LUT': 31290, 'FF': 42618, 'BRAM_tile': 22, 'RAMB36': 18, 'RAMB18': 8,
                                'DSP': 59, 'WNS_ns': 3.649, 'WHS_ns': 0.010, 'DRC_errors': 0,
                                'actual_pl_clock_hz': 99999001},
                golden_sha256=sha(m / 'golden/v2_trace_manifest.json'),
                ip_component_sha256=sha(ip / 'component.xml'),
                ip_vlnv='user.org:llm_fpga:lm_head_v2:2.0',
                known_limitations=LIMITS,
                interface_contract='interface/interface_contract.json',
                hardware_profile='interface/hardware_profile_summary.json',
                acceptance_metadata='reports/20261010_ACCEPTANCE_METADATA.json')
    for b in base['buffers']:
        b['system_connection'] = 'PS S_AXI_HP2_FPD via single-module SmartConnect (integration allocation pending)'
        b['endianness'] = 'little'
        b['layout_enum_value'] = None
        b['dtype_enum_value'] = None
    base['provisional_contract']['note'] = 'Local ABI 2 is implemented. Global generated header/enums/instance/address/timeout mapping remain pending architecture freeze.'
    for b, hls_name, job_name in zip(base['buffers'],
            ['hidden_offset', 'shared_vocab_weight', 'history_bitmap', 'optional_logits'],
            ['hidden_phys_addr', 'weight_phys_addr', 'history_phys_addr', 'logits_phys_addr']):
        b['hls_address_parameter'] = hls_name
        b['driver_address_parameter'] = job_name
    dump(m / 'module_manifest.json', base)
    interface_dir = m / 'interface'
    regs = registers(ip / 'component.xml')
    build_decode = {'h_lanes': {'bits': [0, 3], 'encoded': 1, 'decoded': 8},
                    'row_tile': {'bits': [4, 9], 'encoded': 1, 'decoded': 1},
                    'hidden_tile': {'bits': [10, 17], 'encoded': 32, 'decoded': 32},
                    'numeric_impl': {'bits': [18, 21], 'encoded': 0, 'decoded': 'current FP32 tree hardware'},
                    'clock': {'bits': [22, 27], 'encoded': 0, 'decoded_hz': 100000000},
                    'module_revision': {'bits': [28, 31], 'encoded': 1, 'decoded': 1}}
    result_fields = [{'name': n, 'bits': bits} for n, bits in [
        ('selected_token', 32), ('selected_score', 32), ('result_job_id', 32), ('status_code', 32),
        ('processed_rows', 32), ('perf_cycles_total', 64), ('perf_cycles_compute', 64),
        ('perf_read_beats', 64), ('perf_write_beats', 64), ('output_crc', 32), ('build_config', 32),
        ('capabilities', 32), ('vocab_rows_done', 32), ('weight_read_beats_128', 64),
        ('history_read_words', 32), ('logits_write_beats_128', 64), ('weight_wait_cycles', 64),
        ('dot_active_cycles', 64), ('logits_written', 32)]]
    contract = dict(schema='m14_interface_contract_v2_delivery_1',
        identity={'module_id': 14, 'instance_id': None, 'instance_assignment': 'pending system integration',
                  'name': 'lm_head_v2', 'revision': 1, 'abi_version': 2},
        build_config={'value': '0x10008011', 'decode': build_decode},
        capabilities={'value': '0x00000182', 'local_bits': {'1': 'DEBUG_CRC', '7': 'WRITE_LOGITS_OPTIONAL', '8': 'DUAL_RUN_MODE'},
                      'public_enum_freeze': 'pending'},
        control_base={'standalone_example': '0xA0000000', 'aperture_bytes': 65536, 'integration_assignment': None},
        control_register_source='ip_repo/lm_head_v2/component.xml', control_registers=regs,
        control_register_side_effect_source='drivers/generated/xlm_head_v2_hw.h',
        buffers=base['buffers'],
        dimensions={'hidden_size': [896, 896], 'vocab_size': [151936, 151936], 'valid_rows': [1, 1],
                    'run_mode': [0, 1], 'write_logits': [0, 1], 'enable_penalty': [0, 1],
                    'repetition_penalty': 'FP32 finite >=1 when enable_penalty=1; ignored otherwise'},
        modes={'same_physical_ip': True, 'prefill': {'run_mode': 0, 'valid_rows': 1},
               'decode': {'run_mode': 1, 'valid_rows': 1},
               'upstream_T36_T64': 'M03/PS selects final RMSNorm last row; full-sequence integration test pending'},
        flags={'valid_mask': '0x0000000f', 'bits': {'0': 'ENABLE_OUTPUT_CRC', '1': 'ENABLE_PERF',
               '2': 'DEBUG_SNAPSHOT', '3': 'STRICT_CHECK'}, 'unknown_bits': 'BAD_FLAGS (11), no work',
               'actual_behavior': 'bit0 gates CRC; counters always populated; bit2/3 accepted without additional snapshot/full-system strict checks; write_logits is separate'},
        results=result_fields,
        status_codes={'0': 'OK', '1': 'BAD_ABI', '2': 'BAD_DIMENSION', '3': 'BAD_ALIGNMENT',
            '4': 'BAD_ADDRESS_RANGE', '5': 'BAD_LAYOUT', '6': 'BAD_LAYER', '7': 'BAD_TOKEN',
            '8': 'BAD_ALIAS', '9': 'NUMERIC_ERROR', '10': 'DRIVER_TIMEOUT', '11': 'BAD_FLAGS',
            '12': 'INTERNAL_ERROR', '13': 'NOT_READY (host driver only)'},
        status_implementation_note='Declared vocabulary is not proof of enforcement. HLS checks ABI/dim/mode/flags/penalty/numeric; local driver adds active pointer/alignment; range/layout/alias/etc belong to M03.',
        counters={'read_write_unit': '128-bit beat', 'history_read_words_unit': '32-bit logical word',
            'compute_and_total': 'HLS modeled dataflow/weight timing; total=compute+hidden_words, not external APM',
            'a53_timer': '33333000 counts/s; includes submit/wait/verify loop'},
        crc={'algorithm': 'IEEE CRC32 reflected polynomial 0xedb88320 init/final xor 0xffffffff',
             'bytes': 'little-endian uint32 selected_token followed by uint32 selected_score_bits', 'enabled_by': 'flags bit0'},
        alias={'allowed': ['M05/M14 shared canonical immutable weight read/read'],
               'forbidden': ['active output overlaps active input or weight', 'in-place output'],
               'validator': 'M03 range/capacity/layout/owner/generation/alias validation required; not implemented by local driver'},
        timeout={'class': None, 'class_state': 'pending architecture freeze', 'single_host_default_seconds': 30,
                 'repeat_host_max_seconds': 600, 'driver_poll_budget_is_iterations': True,
                 'worst_measured_single_ip_ms': 224.86814, 'worst_measured_single_a53_ms': 224.88671886718868,
                 'tested_1000_call_wall_seconds': 224.87929442294424},
        numeric={'id': base['numeric_impl'], 'conversion': 'FP32->BF16 RNE; BF16->FP32 bits shifted left16',
                 'accumulation': 'FP32 multiply/add separately rounded; 8 lanes,16 interleave; adjacent lane tree',
                 'penalty': 'seen raw<0 multiply, otherwise divide; argmax ties smaller token',
                 'debug_logits': 'raw pre-penalty FP32', 'gate': 'token/score bits/CRC/raw logits SHA256 exact, tolerance=0',
                 'special_values': 'finite archived trace tested; extreme/subnormal matrix pending; NUMERIC_ERROR on nonfinite output'},
        tests={'decode_T1_penalty_on': 'BOARD PASS 8 production +8 debug',
               'prefill_T1': 'pending dedicated mode test; same source datapath',
               'upstream_T36_T64': 'pending native last-row integrated test',
               'errors': 'BOARD PASS ABI/flags/dimension/penalty; controlled golden failure timing PASS',
               'boundary_address': 'pending M03 and board boundary matrix',
               'penalty_off': 'compact CSim/RTL CoSim functionality evidence; production-size board/performance pending',
               'performance': '30 independent runs PASS;1000-call stability PASS', 'tcp_faults': '6 board cases PASS'},
        known_limitations=LIMITS)
    dump(interface_dir / 'interface_contract.json', contract)
    with (interface_dir / 'registers.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'offset', 'width_bits', 'access', 'reset'])
        writer.writeheader()
        writer.writerows([{**r, 'offset': f"0x{r['offset']:03x}"} for r in regs])
    dump(interface_dir / 'hardware_profile_summary.json', {
        'board': 'ALINX AXU9EGB', 'part': 'xczu9eg-ffvb1156-2-i', 'scope': 'independent archived M14 image',
        'PS_DDR_physical_data_bits': 64, 'PS_DDR_capacity_bytes': 4294967296,
        'PS_DDR_regions': [{'base': '0x000000000', 'bytes': 2147483648}, {'base': '0x800000000', 'bytes': 2147483648}],
        'HP2_axi_bits': 128, 'HP2_address_bits': 49, 'M14_axi_pointer_bits': 64, 'project_phys_addr_bits': 40,
        'target_PL_clock_hz': 100000000, 'reported_PL_clock_hz': 99999001,
        'PS_reference_clock_MHz': 33.333, 'PL_DDR_used': False, 'MIG_instantiated': False,
        'MIG_calibration_ready': None, 'MIG_calibration_note': 'not applicable to this image; do not assert system MIG ready',
        'ready_checks': 'Full DDR CRC/sentinels/board campaign passed historically; live DDR/clock/reset ready must be checked by M02 at each boot',
        'standalone_allocations': {'weights': '0x40000000', 'hidden': '0x503A8000',
            'history': '0x503A8700', 'logits': '0x503AD140', 'mailbox': '0x51000000'},
        'integration_allocation': 'pending M02/M03; standalone example addresses not global fixed allocations'})
    shutil.copy2(m / 'DELIVERY_NOTES.md', m / 'README.md')
    (package / 'requirements.txt').write_text('numpy==2.3.5\n', encoding='utf-8')
    (package / 'README_交付入口.md').write_text(
        '# M14 V2 提交喻燕萍的交付候选版\n\n'
        '版本：M14_V2_20261010_r1；负责人张本；2026-10-10。\n\n'
        '先阅读 `module_14_lm_head_v2/README.md`，再执行其中的离线复核命令。\n'
        '源码/IP/驱动/完整 BF16 权重/8 步输入与 golden/真实板测原始证据均已包含。\n'
        '**独立 Decode 板测通过；公共 ABI、原生 M06、Prefill/全模块集成仍待验证。**\n'
        '送审说明见 `交付说明_喻燕萍.md`；对应规范快照位于 `specifications/`。\n', encoding='utf-8')
    (package / '交付说明_喻燕萍.md').write_text(
        '# M14 LM Head V2 模块交付\n\n喻燕萍：\n\n'
        '现提交张本负责的 M14 LM Head V2 优化版，版本 M14_V2_20261010_r1。'
        '附件包括源码、可综合 IP、PS 驱动、机器接口表、资源/时序报告、BF16 资产和完整单模块测试证据。\n\n'
        '8 步生产/debug bit-exact、30 次独立性能、1000 次连续调用及 TCP 权重加载/6 类错误路径均通过。'
        '100 MHz IP median/P95 224.868020 ms；272269312-byte 权重含 DDR 校验的 TCP 加载约 8.33 s。\n\n'
        '请以待统一集成候选版汇总：公共 ABI 枚举/instance/地址/timeout 冻结、原生 M06 BF16、'
        'Prefill 36/64 最后一行链路、其余性能矩阵、边界地址和外部 HP2 监测仍需完成。'
        '具体接入与待办见模块 README 和 interface_contract.json。\n\n'
        '接收后先核对 ZIP SHA256，并执行 scripts/run_tests.py 完成包内完整性和离线证据复核。\n', encoding='utf-8')
    provenance = package / 'provenance'
    git = lambda *args: subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    dump(provenance / 'source_snapshot.json', {'git_head': git('rev-parse', 'HEAD').strip(),
        'branch': git('branch', '--show-current').strip(), 'module_status': git('status', '--short', '--', MODULE.name),
        'note': 'Module is untracked in original repository. Commit alone does not identify this module; delivered source hashes identify the snapshot.',
        'hardware_rebuilt_during_packaging': False, 'board_access_during_packaging': False,
        'production_sources_identical': all(sha(MODULE / d / p.name) == sha(p) for d in ['src', 'include', 'drivers']
             for p in (m / d).iterdir() if p.is_file()),
        'source_sha256': {p.relative_to(m).as_posix(): sha(p) for d in ['src', 'include', 'drivers', 'standalone/src', 'standalone/tcp_loader'] for p in (m / d).rglob('*') if p.is_file()}})
    (provenance / 'tracked_module.patch').write_text(git('diff', '--', MODULE.name), encoding='utf-8')
    write_sums(m)
    write_sums(package)
    print(f'DELIVERY_STAGING={package}', flush=True)
    print('Verifying staged snapshot...', flush=True)
    verify = subprocess.run([sys.executable, '-B', str(m / 'scripts/run_tests.py')], cwd=package,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (output / 'STAGING_VALIDATION.log').write_text(verify.stdout, encoding='utf-8')
    if verify.returncode:
        print(verify.stdout, flush=True)
        raise RuntimeError('Staged package validation failed')
    print('STAGING_VALIDATION=PASS', flush=True)
    archive = output / (VERSION + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for path in sorted(package.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and 'build' not in path.relative_to(package).parts:
                z.write(path, path.relative_to(output).as_posix())
    expected_files = {line.split('  ', 1)[1] for line in (package / 'SHA256SUMS').read_text(encoding='utf-8').splitlines()} | {'SHA256SUMS'}
    # Ensure no newly generated test temporary files entered the archive.
    with zipfile.ZipFile(archive) as z:
        actual = {str(Path(n).relative_to(VERSION)).replace('\\', '/') for n in z.namelist()}
        if actual != expected_files or z.testzip() is not None:
            raise AssertionError('ZIP file inventory/CRC mismatch')
        extracted = output / 'verify_extracted'
        z.extractall(extracted)
    clean = extracted / VERSION
    verify = subprocess.run([sys.executable, '-B', str(clean / MODULE.name / 'scripts/run_tests.py')], cwd=clean,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (output / 'EXTRACTED_VALIDATION.log').write_text(verify.stdout, encoding='utf-8')
    if verify.returncode:
        print(verify.stdout, flush=True)
        raise RuntimeError('Extracted package validation failed')
    result = {'state': 'PASS', 'version': VERSION, 'archive': archive.name, 'bytes': archive.stat().st_size,
              'sha256': sha(archive), 'files': len(actual), 'staging_validation': 'PASS', 'extracted_validation': 'PASS',
              'vivado_catalog_validation': 'PASS' if args.catalog_log else 'not rerun',
              'hardware_access': False, 'scope': base['delivery_state'], 'known_limitations': LIMITS}
    dump(output / 'DELIVERY_VALIDATION.json', result)
    (output / 'ZIP_SHA256SUMS.txt').write_text(f"{result['sha256']}  {archive.name}\n", encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
