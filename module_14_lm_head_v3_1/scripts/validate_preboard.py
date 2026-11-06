"""Verify offline readiness without accessing hardware or claiming board PASS."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

M = Path(__file__).resolve().parents[1]
R = M / 'reports/board_v31_20261019'
P = R / 'package'
sys.path.insert(0, str(M / 'standalone'))
from board_profile import load_profile, check_loader_pair


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
    sums = {}
    for line in (P / 'ARTIFACTS.sha256').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        assert name not in sums and (P / name).is_file()
        assert sha(P / name) == digest, name
        sums[name] = digest
    assert set(sums) == {f.name for f in P.iterdir() if f.is_file() and f.name != 'ARTIFACTS.sha256'}
    profile = load_profile(P)
    assert check_loader_pair(P, P, '192.168.0.190')
    assert profile['build_config'] == 0x30c08011
    hw = read(R / 'hardware_audit.json')
    assert hw['state'] == 'PASS' and hw['cdc_critical'] == 0
    assert hw['bit_sha256'] == sha(P / 'm14_v31_system_wrapper.bit')
    assert hw['implemented_bd_sha256'] == sha(R / 'hardware/implemented_bd.json')
    assert hw['pin_constraints_sha256'] == sha(M / 'constraints/lm_head_v31_ddr4_pins.xdc')
    with zipfile.ZipFile(P / 'm14_v31_single.xsa') as z:
        bits = [n for n in z.namelist() if n.endswith('.bit')]
        assert len(bits) == 1 and hashlib.sha256(z.read(bits[0])).hexdigest() == hw['bit_sha256']
    identity = read(P / 'BUILD_SOURCES.json')
    assert identity['hardware_xsa_sha256'] == sha(P / 'm14_v31_single.xsa')
    for name, digest in identity['source_sha256'].items(): assert sha(M / name) == digest, name
    for name, digest in identity['elf_sha256'].items(): assert sha(P / name) == digest, name
    numeric_sha = sha(M / 'experiments/board_v31_20261019/src/lm_head_v2.cpp')
    assert numeric_sha == '926911392a1664c05072ac3df2c9c494e55b9d94e72776c67ee5e642d5a5ef91'
    weight=M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
    weight_sha=sha(weight)
    assert weight.stat().st_size==272269312 and weight_sha=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
    result = dict(state='OFFLINE_READY_BOARD_NOT_RUN', release='lm_head v3.1',
                  offline_hardware='PASS', offline_software_binding='PASS', package_hashes='PASS',
                  numeric_source_identical_to_v3=True, numeric_source_sha256=numeric_sha,
                  build_config='0x30c08011', capabilities='0x382', data_memory='PL_DDR',
                  host_only_weight_sha256=weight_sha, target_pl_ddr_crc='NOT_RUN',
                  hardware=hw, package_sha256=sums,
                  board_tests={name:'NOT_RUN' for name in ('calibration_and_memory', 'canonical_pl_ddr_load_crc_sentinel',
                               '8_production_and_8_full_logits', 'loader_and_address_faults', '30_timing_samples', '1000_stability_calls')},
                  engineering_acceptance='PENDING_BOARD', formal_delivery='NOT_CREATED',
                  board_policy='User says board is not ready; no hardware access until user confirms readiness',
                  next_entry='standalone/run_pl_ddr_acceptance.ps1')
    (R / 'OFFLINE_PREPARATION.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    (R / 'OFFLINE_PREPARATION.md').write_text('''# lm_head v3.1 上板前准备

离线准备通过；**v3.1 板测全部 NOT_RUN，工程验收待板卡，不是正式发布交付**。

- 200 MHz 实现/时序/DRC/CDC、PL DDR统一地址通路已审计。
- bit/XSA/PS init、生产/TCP loader/独立内存诊断/校准超时注入四个ELF已配套冻结。
- BUILD_SOURCES.json记录正式编译时的XSA、源码及ELF身份；ARTIFACTS.sha256覆盖加载包。
- HLS数学CPP与已验收v3相同；不能据此代替本版的板上数值/性能测试。

等用户明确板卡就绪后，按 BOARD_PLAN.md 先检查占用/连线，再运行
`standalone/run_pl_ddr_acceptance.ps1`。此入口将完整初始化，PL DDR自测与错误拒绝，
canonical BF16 TCP加载、加载错误测试后整份重传，再做数值/计时/稳定性验收。
校准超时测试仅为软件注入，物理MIG不会被强制失败。

当前不自动轮询、连接或操作板卡。正式交付ZIP要在真实验收后生成。
完整离线审计与hash见 OFFLINE_PREPARATION.json；当前运行状态以PROGRESS.json和续办记录为准。
''', encoding='utf-8')
    print('M14_V31_OFFLINE_PREPARATION=PASS_BOARD_NOT_RUN')


if __name__ == '__main__': main()
