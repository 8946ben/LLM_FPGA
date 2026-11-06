"""Compare strict same-board campaigns, preserving independent timing samples."""
from pathlib import Path
import argparse, hashlib, json

m=Path(__file__).resolve().parents[2]
out=m/'reports/board200_20261019'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline-campaign',type=Path,required=True)
    parser.add_argument('--candidate-campaign',type=Path,required=True)
    parser.add_argument('--baseline-upload',type=Path,required=True)
    parser.add_argument('--candidate-upload',type=Path,required=True)
    args=parser.parse_args()
    load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    a=load(out/'baseline_summary.json'); b=load(out/'candidate_summary.json')
    hw=load(out/'hardware_audit.json')
    assert a['state']==b['state']==hw['state']=='PASS'
    assert a['build_config']==0x10008011 and b['build_config']==0x20c08011
    ca=load(args.baseline_campaign); cb=load(args.candidate_campaign)
    for campaign in (ca,cb):
        assert campaign['state']=='PASS' and len(campaign['records'])==55
    uploads=[load(p/'upload.json') for p in (args.baseline_upload,args.candidate_upload)]
    for path,upload in zip((args.baseline_upload,args.candidate_upload),uploads):
        assert upload['state']=='PASS' and upload['ddr_crc32']=='7acfde43'
        assert upload['weight_sha256']=='4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f'
        assert 'M14_SENTINEL_VERIFY=PASS' in (path/'sentinels.log').read_text(encoding='utf-8-sig')
    for frequency in (100,200):
        assert f'M14_BOARD{frequency}_CLOCK_REGISTERS=PASS' in (out/f'clock_{frequency}.log').read_text(encoding='utf-8-sig')
    perf_a=a['performance']; perf_b=b['performance']
    median=perf_a['ip_ms_median']/perf_b['ip_ms_median']
    p95=perf_a['ip_ms_p95']/perf_b['ip_ms_p95']
    wall=perf_a['a53_wall_ms_median']/perf_b['a53_wall_ms_median']
    report=dict(state='PASS',baseline=a,candidate=b,hardware=hw,
        speedup_ip_median=median,speedup_ip_p95=p95,speedup_a53_wall_median=wall,
        latency_reduction_percent=(1-1/median)*100,
        baseline_campaign=str(args.baseline_campaign.resolve()),candidate_campaign=str(args.candidate_campaign.resolve()),
        baseline_upload=str(args.baseline_upload.resolve()),candidate_upload=str(args.candidate_upload.resolve()),
        interpretation='Independent M14 Decode/penalty-ON using existing converted BF16 trace, not full-model token latency. IP uses nominal clocks; A53 timer is an independent elapsed-time measure.')
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    rows='\n'.join(f'| {label} | {perf_a[key]:.6f} | {perf_b[key]:.6f} |' for label,key in (
        ('IP median / ms','ip_ms_median'),('IP P95 / ms','ip_ms_p95'),('IP max / ms','ip_ms_max'),
        ('A53 wall median / ms','a53_wall_ms_median'),('A53 wall P95 / ms','a53_wall_ms_p95'),('A53 wall max / ms','a53_wall_ms_max')))
    text=f'''# 200 MHz 独立 M14 同板验证（2026-10-19）

结论：PASS。200 MHz 版本已完成真实板测，IP median 相比本次复测的 100 MHz
提升 **{median:.4f} 倍**，延迟降低 **{report['latency_reduction_percent']:.2f}%**；
A53 wall median 提升 **{wall:.4f} 倍**。

| 指标 | 冻结 LM Head V2 / 100 MHz | 规约分层版本 / 200 MHz |
|---|---:|---:|
{rows}

IP 周期范围：100 MHz `{perf_a['ip_cycles_min']}..{perf_a['ip_cycles_max']}`；
200 MHz `{perf_b['ip_cycles_min']}..{perf_b['ip_cycles_max']}`。
每版本均包含 30 次独立单调用样本；P95 采用 nearest-rank（第 29/30 个有序样本）。
1000 次连续调用均通过，100/200 MHz 各用时
`{a['stability_wall_seconds']:.6f}` / `{b['stability_wall_seconds']:.6f}` 秒。
稳定性循环的 mailbox 只保留最后一次 IP 计数，不作为 1000 份独立时延样本。

## 精度与传输

两版本各 55 项运行通过：8 步生产模式、8 步写 logits 模式、4 项参数/数值错误路径、
1 项故意错误 golden、3 次预热、30 次性能样本、1 组 1000 次连续调用。
每步 hidden=896、vocab=151936，生产与调试模式的 top1/score bits/CRC 与既有黄金结果一致；
8 步完整 FP32 logits 均通过文件 SHA256 严格一致检查。
权重是同一份 canonical BF16，完整 SHA256、逐块 DDR CRC32、最终 DDR CRC32 `7acfde43`
和 JTAG 首尾 sentinel 均通过。两次加载（含逐块和全 DDR CRC）耗时
`{uploads[0]['elapsed_seconds']:.6f}` / `{uploads[1]['elapsed_seconds']:.6f}` 秒。

## 时钟、版本与时序

100/200 MHz 硬件身份分别为 `0x10008011` / `0x20c08011`。
200 MHz HLS IP 为 `user.org:llm_fpga:lm_head_v2:2.1`，测试 ELF、PS init、XSA 和 bit
来自同一匹配包。XSA 内嵌 bit 与独立 bit 的 SHA256 相同。PS 时钟链寄存器回读通过，
PL0 从 DPLL 的 /4 /1 改为 /2 /1；Vivado 配置模型为 {hw['configured_clock_mhz']:.6f} MHz，
该数值不是频率计实测。IP 耗时按标称 200 MHz 换算，并由 A53 独立计时交叉验证。

新上板镜像布线后：WNS `{hw['wns_ns']:+.3f} ns`、WHS `{hw['whs_ns']:+.3f} ns`、
WPWS `{hw['wpws_ns']:+.3f} ns`，setup/hold/pulse-width 失败端点均为 0，
无未约束端点或无时钟项。DRC {hw['drc_severity_counts']['Error']} Error /
{hw['drc_severity_counts']['Critical Warning']} Critical Warning /
{hw['drc_severity_counts']['Warning']} Warning / {hw['drc_severity_counts']['Advisory']} Advisory。
普通警告包括既有 DSP pipeline/AVAL 项，以及 1 项 SmartConnect 内部
`s00_w_node/.../mi_handler_m_sc_areset_pipe` 的 RTSTAT-10（无可布线负载）；原始报告保留。
资源 LUT {hw['resources']['lut']:.0f}、FF {hw['resources']['ff']:.0f}、
BRAM tile {hw['resources']['bram_tile']:g}、DSP {hw['resources']['dsp']:.0f}。

## 计算与口径

`IP_ms = perf_cycles_total × 1000 / ip_clock_hz`；
`A53_wall_ms = wall_ticks × 1000 / timer_counts_per_second`；
`提升倍数 = median_100 / median_200 = {perf_a['ip_ms_median']:.6f} / {perf_b['ip_ms_median']:.6f} = {median:.6f}`。
A53 wall 包含提交、轮询、结果校验，不含初次权重加载及主机 JTAG。
源码中的 `perf_cycles_total = compute_cycles + 112`，前者来自 DATAFLOW 完成计数器，
112 为 hidden 读取 word 数；IP 指标沿用旧版同一计数口径，A53 wall 提供独立耗时交叉验证。
该结果针对独立 M14、Decode、penalty ON 的既有 BF16 trace，不能称为完整 LLM 的 token 速度。
真实数据替代此前条件性性能估计，原始估计与工具证据保留。

## 证据

- `baseline_summary.json` / `candidate_summary.json`：两次严格验收统计。
- `comparison.json`：原始 campaign 与权重加载目录、完整对比数据。
- `hardware_audit.json` / `hardware/`：本次上板镜像时序、资源、DRC 和 bit/XSA。
- `identity_validation.json`：42 份 RTL 只改变 build_config 常量，计算逻辑与已验证候选一致。
- `clock_100.log` / `clock_200.log`：真实板卡 PS 时钟链回读。
- `package/`：匹配的 200 MHz bit/XSA/PS init/test ELF/TCP loader 及 SHA256。
- `baseline_100_package/`：原冻结 100 MHz bit/XSA/test ELF 不变，仅 loader 适配当前 `.0` 网段。

复现命令及网络配置见 `experiments/board200_20261019/README.md`。
测试结束后 DDR 权重在本次上电期间保留，断电后需重新加载。
'''
    (out/'RESULT.md').write_text(text,encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k.startswith('speedup') or k in ('state','latency_reduction_percent')},indent=2))

if __name__=='__main__': main()
