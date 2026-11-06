"""Publish v3.1 acceptance only from completed real-board evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

M = Path(__file__).resolve().parents[1]
ROOT = M.parent
R = M / 'reports/board_v31_20261019'
WEIGHT_SHA = '4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign', type=Path, required=True)
    p.add_argument('--upload-dir', type=Path, required=True)
    p.add_argument('--diagnostics', type=Path, nargs='+', required=True)
    p.add_argument('--loader-faults', type=Path, required=True)
    a = p.parse_args()
    subprocess.run([sys.executable, str(M / 'scripts/summarize_acceptance.py'),
                    str(a.campaign), '--manifest', str(ROOT / 'artifacts/module14_v2_assets/manifest.json'),
                    '--output', str(R / 'candidate_summary.json')], check=True)
    old, new = read(R / 'baseline_v3_summary.json'), read(R / 'candidate_summary.json')
    assert old['state'] == new['state'] == 'PASS'
    assert old['build_config'] == 0x20c08011 and new['build_config'] == 0x30c08011
    hw = read(R / 'hardware_audit.json')
    assert hw['state'] == 'PASS'
    build = read(R / 'package/BUILD_SOURCES.json')
    for name, digest in build['source_sha256'].items():
        assert hashlib.sha256((M / name).read_bytes()).hexdigest() == digest, name
    for name, digest in build['elf_sha256'].items():
        assert hashlib.sha256((R / 'package' / name).read_bytes()).hexdigest() == digest, name
    session = read(R / 'BOARD_SESSION_20261020.json')
    assert session['same_physical_board'] == 'USER_CONFIRMED'
    source_sha = hashlib.sha256((M / 'experiments/board_v31_20261019/src/lm_head_v2.cpp').read_bytes()).hexdigest()
    assert source_sha == '926911392a1664c05072ac3df2c9c494e55b9d94e72776c67ee5e642d5a5ef91'
    diagnostics = [read(f) for f in a.diagnostics]
    assert all(d['state'] == 'PASS' and d['lm_head_projection_invoked'] is False
               and (not d['lm_head_invoked'] or d['identity_probe_no_ddr']) for d in diagnostics)
    assert {d['driver_status'] for d in diagnostics} >= {0, 4, 13}
    assert any(d.get('calibration_timeout_software_injection') for d in diagnostics)
    upload = read(a.upload_dir / 'upload.json')
    assert upload['state'] == 'PASS' and upload['bytes'] == 272269312
    assert upload['weight_sha256'] == WEIGHT_SHA and upload['ddr_crc32'] == '7acfde43'
    sentinel = (a.upload_dir / 'sentinels.log').read_text(encoding='utf-8-sig')
    assert all(s in sentinel for s in ('M14_SENTINEL_FIRST=PASS', 'M14_SENTINEL_LAST=PASS',
                                       'M14_SENTINEL_VERIFY=PASS'))
    faults = read(a.loader_faults)
    expected = {'bad_chunk_crc_invalidates_image', 'fragmented_frame_and_duplicate_rejection',
                'oversized_chunk_rejection', 'truncated_commit_rejection',
                'mid_payload_disconnect_invalidates_image', 'full_ddr_crc_rejects_wrong_expected_crc'}
    assert faults['state'] == 'PASS' and faults['weight_sha256'] == WEIGHT_SHA
    assert {t['test'] for t in faults['tests'] if t['state'] == 'PASS'} == expected
    assert (a.upload_dir / 'upload.json').stat().st_mtime >= a.loader_faults.stat().st_mtime, 'Full reload required after faults'
    speedups = {k: old['performance'][k] / new['performance'][k]
                for k in ('ip_ms_median', 'ip_ms_p95', 'ip_ms_max',
                          'a53_wall_ms_median', 'a53_wall_ms_p95', 'a53_wall_ms_max')}
    baseline = M / 'reports/board_runs/20261019_201218_472_acceptance/campaign.json'
    baseline_upload = M / 'reports/board_runs/20261019_201046_440_tcp_weight'
    result = dict(state='PASS', release='lm_head v3.1', baseline_kind='v3 PS DDR recaptured for this task on 2026-10-19 before power-off; candidate uses a separate boot',
                  baseline_campaign=str(baseline.resolve()), candidate_campaign=str(a.campaign.resolve()),
                  baseline_upload=str(baseline_upload.resolve()), candidate_upload=str(a.upload_dir.resolve()),
                  baseline=old, candidate=new, hardware=hw, speedup_v31_vs_v3=speedups,
                  diagnostic_files=[str(f.resolve()) for f in a.diagnostics],
                  loader_faults_file=str(a.loader_faults.resolve()),
                  loading=upload, calibration_timeout_method='software injection on real A53; physical MIG unchanged',
                  effective_weight_mib_s=272269312 / (new['performance']['ip_ms_median'] / 1000) / 2**20,
                  bandwidth_note='Weight bytes / IP latency; not measured AXI/MIG bus bandwidth',
                  performance_method='30 independent production calls after 3 warmups; P95 nearest rank ceil(0.95*N)',
                  source_sha256=source_sha, board_session=session,
                  software_build=build,
                  baseline_loading=read(baseline_upload / 'upload.json'))
    (R / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    op, np = old['performance'], new['performance']
    report = f'''# lm_head v3.1 PL DDR 验收

状态：PASS。200 MHz、完整词表，计算数据走 PL DDR；PS 程序/TCP暂存/mailbox保留 PS DDR。

8 步生产与 8 步完整 logits 逐位一致；30 次独立计时；1000 次连续调用通过。
PL DDR 数据模式、地址位和末端探测通过（非全2GiB逐字穷举）；地址范围拒绝通过。
校准超时为真实 A53 上的软件故障注入，不代表物理 MIG 校准失败测试。
加载 SHA256、目标 PL DDR 逐块/完整 CRC32、首尾 sentinel 通过；6项加载错误测试后已整份重传。

| 指标 | 本任务10/19断电前 v3 PS DDR 对照 | v3.1 PL DDR | 倍率（v3时间/v3.1时间） |
| --- | ---: | ---: | ---: |
| IP median ms | {op['ip_ms_median']:.6f} | {np['ip_ms_median']:.6f} | {speedups['ip_ms_median']:.6f} |
| IP P95 ms | {op['ip_ms_p95']:.6f} | {np['ip_ms_p95']:.6f} | {speedups['ip_ms_p95']:.6f} |
| A53 median ms | {op['a53_wall_ms_median']:.6f} | {np['a53_wall_ms_median']:.6f} | {speedups['a53_wall_ms_median']:.6f} |

IP毫秒 = cycles / 200000000 × 1000；A53毫秒 = wall_ticks / timer_counts_per_second × 1000。
P95取排序后第ceil(0.95×30)=29个样本；倍率大于1表示加速。
用户确认两个版本使用同一块AXU9EGB。v3对照为本任务重新采集的记录，早于本次断电；两个版本为不同启动，不能称为同一次启动的测量。
加载 {upload['elapsed_seconds']:.6f}s，{upload['throughput_mib_s']:.6f}MiB/s。
其中发送及逐块目标回读CRC {upload.get('data_and_chunk_crc_seconds', float('nan')):.6f}s，最后整份目标回读CRC {upload.get('full_target_crc_commit_seconds', float('nan')):.6f}s。
本任务v3 PS DDR加载 {result['baseline_loading']['elapsed_seconds']:.6f}s；该差异是A53加载/校验路径的成本，不能等同于lm_head计算性能变化。
早期PL DDR逐字节回读加载约255.17s；改为64位目标读取及16KiB PS暂存后，仍逐块/整份校验实际PL DDR。
单次256KiB目标回读微基准与TCP队列修复证据分别见target_crc_bench.json和TCP_LOADER_FIX_VERIFICATION.json。
时序 WNS/WHS/WPWS：{hw['wns_ns']}/{hw['whs_ns']}/{hw['wpws_ns']}ns。

原始路径、完整统计、版本与 hash 见 comparison.json 和配套 RUN_PROFILE/ARTIFACTS.sha256。
范围限于独立 M14 的归档有限输入；未验证整体 LLM、候选稀疏化、上游直供权重或极端数值矩阵。
内部权重等待计数与“权重字节/IP时间”不能代替外部 AXI/MIG 带宽监测。
'''
    (R / 'RESULT.md').write_text(report, encoding='utf-8')
    print('M14_V31_ENGINEERING_ACCEPTANCE=PASS')


if __name__ == '__main__': main()
