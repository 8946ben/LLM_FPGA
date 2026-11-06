"""Create a portable v3.1 delivery only after engineering/board acceptance."""
from pathlib import Path
import argparse
import copy
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

M = Path(__file__).resolve().parents[1]
ROOT = M.parent
E = M / 'experiments/board_v31_20261019'
R = M / 'reports/board_v31_20261019'
V3 = ROOT / 'deliverables/20261019_M14_V3_r1/M14_V3_20261019_r1'
NS = {'s': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(8 << 20), b''): h.update(chunk)
    return h.hexdigest()


def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def dump(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.Xil', 'build', 'workspace', '.cache'))


def stage(out, version):
    c = read(R / 'comparison.json')
    assert c['state'] == c['candidate']['state'] == c['baseline']['state'] == 'PASS'
    assert c['hardware']['cdc_critical'] == 0
    assert not out.exists(), 'Preserve existing delivery'
    p = out / version
    m = p / M.name
    m.mkdir(parents=True)
    shutil.copytree(E, m / 'experiments/board_v31_20261019', ignore=shutil.ignore_patterns(
        '__pycache__', '*.pyc', 'validate_host.py', 'compare_results.py'))
    for name in ('src', 'include', 'drivers'): tree(E / name, m / name)
    for name in ('tb', 'reference', 'golden'):
        tree(V3 / 'module_14_lm_head_v3' / name, m / name)
    for name in ('constraints', 'tests'): tree(M / name, m / name)
    (m / 'scripts').mkdir()
    for name in ('summarize_acceptance.py', 'verify_delivery_v31.py', 'verify_delivery_ip.tcl', 'finalize_acceptance.py'):
        shutil.copy2(M / 'scripts' / name, m / 'scripts' / name)
    standalone = m / 'standalone'
    standalone.mkdir()
    tree(M / 'standalone/src', standalone / 'src')
    (standalone / 'scripts').mkdir()
    for name in ('board_profile.py', 'parse_mailbox.py', 'prepare_mailbox.py', 'program_board_tcp.ps1',
                 'run_step.ps1', 'run_negative.ps1', 'run_failure_regression.ps1', 'run_acceptance.ps1',
                 'upload_weight_tcp.py', 'test_tcp_loader_board.py', 'initialize_selftest.ps1', 'inspect_memory_diag.py',
                 'run_pl_ddr_acceptance.ps1'):
        shutil.copy2(M / 'standalone' / name, standalone / name)
    for name in ('word_u32.tcl', 'capture_final_state.tcl', 'initialize_selftest.tcl', 'probe_retained_state.tcl', 'read_tcp_diagnostics.tcl',
                 'recover_debug_access.tcl', 'run_step.tcl', 'start_tcp_loader.tcl', 'verify_weight_sentinels.tcl'):
        shutil.copy2(M / 'standalone/scripts' / name, standalone / 'scripts' / name)
    ip = m / 'ip_repo/lm_head_v2'
    exported = M / 'build/board_v31_20261019/hls/solution1/impl/ip'
    ip.mkdir(parents=True)
    for name in ('constraints', 'doc', 'drivers', 'example', 'hdl', 'misc', 'subcore', 'xgui'):
        if (exported / name).exists(): tree(exported / name, ip / name)
    for name in ('component.xml', 'auxiliary.xml', 'lm_head_v2_info.xml', 'sysgen_info.xml'):
        if (exported / name).exists(): shutil.copy2(exported / name, ip / name)
    generated = next((ip / 'drivers').glob('*/src'))
    tree(generated, m / 'drivers/generated')
    reports = m / 'reports/board_v31_20261019'
    tree(R / 'package', reports / 'package')
    for f in R.iterdir():
        if f.is_file() and f.suffix in ('.json', '.md', '.log', '.asm', '.bin', '.elf') and not f.name.startswith(('OFFLINE_PREPARATION','PREPARATION_STATUS')):
            shutil.copy2(f, reports / f.name)
    hw = reports / 'hardware'
    hw.mkdir()
    for f in (R / 'hardware').iterdir():
        if f.suffix in ('.rpt', '.dcp', '.json', '.tcl', '.txt', '.bit', '.xsa'): shutil.copy2(f, hw / f.name)
    tree(M / 'build/board_v31_20261019/hls/solution1/syn/report', reports / 'hls')
    launch = reports / 'build_logs'
    launch.mkdir()
    for f in (M / 'build/board_v31_20261019/launch').iterdir():
        if f.is_file() and f.suffix in ('.log', '.json', '.jou'): shutil.copy2(f, launch / f.name)
    campaigns = []
    relocations = []
    copied = set()

    def copy_run(directory):
        directory = Path(directory).resolve()
        if directory not in copied:
            tree(directory, m / 'reports/board_runs' / directory.name)
            copied.add(directory)
        return 'reports/board_runs/' + directory.name

    baseline_profile = m / 'reports/baseline_v3_profile_only'
    baseline_profile.mkdir()
    old_package = ROOT / 'module_14_lm_head_v2/reports/board200_20261019/package'
    for name in ('RUN_PROFILE.json', 'ARTIFACTS.sha256'): shutil.copy2(old_package / name, baseline_profile / name)
    (baseline_profile / 'README.md').write_text('仅供离线解析本轮同板 v3 基线；不是可部署硬件包。\n', encoding='utf-8')
    for key, package in (('baseline_campaign', 'reports/baseline_v3_profile_only'),
                         ('candidate_campaign', 'reports/board_v31_20261019/package')):
        path = Path(c[key])
        campaign = read(path)
        dest = copy_run(path.parent)
        portable = copy.deepcopy(campaign)
        portable['package_dir'] = package
        for row in portable['records']:
            original = row['source_run']
            row['source_run'] = copy_run(original)
            row['profile_source'] = package + '/RUN_PROFILE.json'
            relocations.append(dict(original=original, portable=row['source_run']))
        target = m / dest / 'campaign_portable.json'
        dump(target, portable)
        campaigns.append(target.relative_to(m).as_posix())
    for key in ('baseline_upload', 'candidate_upload'): copy_run(c[key])
    for f in c['diagnostic_files']: copy_run(Path(f).parent)
    fault = Path(c['loader_faults_file'])
    if fault.parent.resolve() != R.resolve(): copy_run(fault.parent)
    else: shutil.copy2(fault, reports / fault.name)
    tree(ROOT / 'artifacts/module14_v2_assets', p / 'artifacts/module14_v2_assets')
    tree(V3 / 'specifications', p / 'specifications')
    shutil.copy2(V3 / 'requirements.txt', p / 'requirements.txt')
    (p / 'ref').mkdir()
    shutil.copy2(ROOT / 'ref/xemacpsif_physpeed.c', p / 'ref/xemacpsif_physpeed.c')
    shutil.copy2(V3 / 'module_14_lm_head_v3/NUMERIC_CONTRACT.md', m / 'NUMERIC_CONTRACT.md')
    readme=(M / 'README.md').read_text(encoding='utf-8')
    start=readme.index('当前状态：')
    end=readme.index('v3.1 是 v3',start)
    readme=readme[:start]+('当前状态：本次独立板卡工程验收通过；8步生产/8步完整logits、PL DDR校验、'
        '30次计时和1000次稳定性调用通过。具体数值与范围见 reports/board_v31_20261019/RESULT.md。\n\n')+readme[end:]
    readme=readme.replace('1. 当前尚无 v3.1 完整时序及真实板测通过结论；以正式报告为准。',
                          '1. 验收范围限于独立M14和归档输入；详细限制以正式报告为准。')
    readme=readme.replace('1. 离线时序已通过；本版板测尚未运行，不能据此宣告工程验收通过。',
                          '1. 验收范围限于独立M14和归档输入；详细限制以正式报告为准。')
    readme=readme.replace('当前不生成“已板测通过”的正式交付版本。当前验收总入口与交付脚本尚未在板卡/最终交付上执行。',
                          '本交付在真实板测通过后生成；交付ZIP及解压副本还需通过离线校验。')
    (m / 'README.md').write_text(readme,encoding='utf-8')
    contract = read(V3 / 'module_14_lm_head_v3/interface/interface_contract.json')
    contract['identity'].update(name='lm_head_v3_1', revision=3, release_name='lm_head v3.1')
    contract['build_config']['value'] = '0x30c08011'
    contract['build_config']['decode']['module_revision'].update(encoded=3, decoded=3)
    contract['capabilities']['value'] = '0x00000382'
    contract['capabilities']['local_bits']['9'] = 'PL_DDR_DATA'
    profile = read(R / 'package/RUN_PROFILE.json')
    contract['memory_profile'] = profile
    for b in contract['buffers']:
        b['system_connection'] = 'SmartConnect -> async AXI clock converter -> PL DDR4 MIG; no PS DDR fallback'
        b['address_semantics'] = 'Mailbox/driver/HLS use the same 64-bit system address in [0x400000000,0x480000000); MIG low 31 bits select DRAM offset'
    contract['counters']['compute_and_total'] = 'count_until_done HLS dataflow cycle counter; total=compute+112 hidden words. Not an external APM or pin-to-pin stopwatch; A53 wall is measured separately.'
    regs = []
    for r in ET.parse(ip / 'component.xml').getroot().findall('s:memoryMaps/s:memoryMap/s:addressBlock/s:register', NS):
        reset = r.find('s:reset/s:value', NS)
        regs.append(dict(name=r.findtext('s:name', namespaces=NS),
                         offset=int(r.findtext('s:addressOffset', namespaces=NS), 0),
                         width_bits=int(r.findtext('s:size', namespaces=NS), 0),
                         access=r.findtext('s:access', namespaces=NS), reset=int(reset.text, 0) if reset is not None else None))
    assert len(regs) == 68
    contract['control_registers'] = regs
    contract['status_implementation_note'] = 'HLS validates ABI/dim/flags/numeric; driver validates active PL DDR system spans/alignment; A53 validates PL aperture and calibration. Ownership/layout/generation/alias remain integration responsibilities.'
    contract['timeout'].update(worst_measured_single_ip_ms=c['candidate']['performance']['ip_ms_max'],
                               worst_measured_single_a53_ms=c['candidate']['performance']['a53_wall_ms_max'],
                               tested_1000_call_wall_seconds=c['candidate']['stability_wall_seconds'])
    contract['tests'].update(decode_T1_penalty_on='This release BOARD PASS: 8 production +8 full logits',
                             boundary_address='PL DDR address-bit/end memory probes and range rejection PASS; not exhaustive capacity sweep',
                             tcp_faults='This release 6 real-loader cases PASS; full canonical reload afterward',
                             calibration_timeout='Software injection on real A53 only; physical MIG not forced to fail')
    limitations = ['Independent dense M14 H896/V151936 Decode penalty ON; no whole-LLM throughput claim.',
                  'Native M06, global ABI integration, sparsity and upstream streaming weights are outside this release.',
                  'Calibration timeout is software injection; sparse address probes are not an exhaustive 2GiB memory test.',
                  'Finite archived inputs verified bit-exact; extended modes/extreme/subnormal values remain unverified.',
                  'No external frequency-counter or AXI/MIG APM measurement; config and internal counters are reported.']
    contract['known_limitations'] = limitations
    dump(m / 'interface/interface_contract.json', contract)
    dump(m / 'interface/hardware_profile_summary.json', profile)
    with (m / 'interface/axi_lite_registers.csv').open('w', newline='', encoding='utf-8') as stream:
        w = csv.DictWriter(stream, fieldnames=list(regs[0])); w.writeheader(); w.writerows(regs)
    source_hashes = {}
    for source in E.rglob('*'):
        if source.is_file() and source.suffix in ('.c', '.cpp', '.h'):
            target = m / 'experiments/board_v31_20261019' / source.relative_to(E)
            assert sha(source) == sha(target)
            source_hashes[target.relative_to(m).as_posix()] = sha(target)
    for source in (M / 'standalone/src').iterdir():
        if source.is_file(): source_hashes['standalone/src/' + source.name] = sha(source)
    dump(m / 'module_manifest.json', dict(version=version, release_name='lm_head v3.1', module_id=14,
         hardware_top='lm_head_v2', abi_version=2, module_revision=3, build_config='0x30c08011', capabilities='0x382',
         ip_vlnv='user.org:llm_fpga:lm_head_v2:2.2', target_clock_hz=200000000,
         memory='PL_DDR', implementation=c['hardware'], acceptance=c['candidate'],
         portable_campaigns=campaigns, tested_source_sha256=source_hashes, known_limitations=limitations))
    dump(p / 'provenance/evidence_path_relocations.json', relocations)
    dump(p / 'provenance/source_identity.json', dict(tested_source_sha256=source_hashes,
         package_only_changes='Campaign path relocation and README acceptance-state wording; hardware/C/C++ copies remain identical.',
         tested_package={f.name: sha(f) for f in (R / 'package').iterdir() if f.is_file()}))
    (p / 'README_交付入口.md').write_text(f'''# lm_head v3.1 交付

本版为200 MHz完整词表 PL DDR 迁移版本，独立板卡验收通过。
入口：`{M.name}/README.md`；真实报告：`{M.name}/reports/board_v31_20261019/RESULT.md`。
ABI仍为2，硬件top仍为lm_head_v2，IP2.2，build_config=0x30c08011。
源码、MIG/引脚/复位、bit/XSA/PS init/ELF/loader、BF16权重与原始证据一并交付。
基线profile目录仅供离线解析，不能用于部署。切换镜像必须完整初始化，大权重走TCP。
修改任何文件后需重算内部SHA256SUMS；改ZIP后重算外部ZIP SHA256。
离线校验：`python {M.name}/scripts/verify_delivery_v31.py <本目录绝对路径>`。
''', encoding='utf-8')
    print('M14_V31_DELIVERY_STAGED=' + str(p))


def seal(out, version):
    p = out / version
    m = p / M.name
    catalog = out / 'ip_catalog.log'
    assert 'M14_V31_DELIVERY_IP_CATALOG=PASS' in catalog.read_text(encoding='utf-8-sig')
    shutil.copy2(catalog, m / 'reports/board_v31_20261019/hls/delivery_ip_catalog.log')
    files = sorted(f for f in p.rglob('*') if f.is_file() and f.name != 'SHA256SUMS')
    (p / 'SHA256SUMS').write_text(''.join(sha(f) + '  ' + f.relative_to(p).as_posix() + '\n' for f in files), encoding='utf-8')

    def verify(base, log):
        r = subprocess.run([sys.executable, str(base / M.name / 'scripts/verify_delivery_v31.py'), str(base)], capture_output=True, text=True)
        log.write_text(r.stdout + r.stderr, encoding='utf-8')
        assert r.returncode == 0, str(log)

    verify(p, out / 'STAGING_VALIDATION.log')
    archive = out / (version + '.zip')
    assert not archive.exists()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for f in files + [p / 'SHA256SUMS']: z.write(f, version + '/' + f.relative_to(p).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(files) + 1
        extracted = out / 'verify_extracted'
        assert not extracted.exists()
        z.extractall(extracted)
    verify(extracted / version, out / 'EXTRACTED_VALIDATION.log')
    result = dict(state='PASS', release='lm_head v3.1', archive=archive.name,
                  sha256=sha(archive), bytes=archive.stat().st_size, files=len(files) + 1,
                  board_acceptance='PASS', extracted_validation='PASS', hardware_access_during_packaging=False)
    dump(out / 'DELIVERY_VALIDATION.json', result)
    (out / 'ZIP_SHA256SUMS.txt').write_text(result['sha256'] + '  ' + archive.name + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'seal'))
    parser.add_argument('--date', required=True, help='YYYYMMDD actual release date')
    a = parser.parse_args()
    assert len(a.date) == 8 and a.date.isdigit()
    output = ROOT / f'deliverables/{a.date}_M14_V3_1_r1'
    name = f'M14_V3_1_{a.date}_r1'
    stage(output, name) if a.action == 'stage' else seal(output, name)
