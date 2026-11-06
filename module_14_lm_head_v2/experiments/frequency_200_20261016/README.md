# M14 200 MHz：第一阶段诊断（2026-10-16）

续办新增[`reduce_layers/README.md`](reduce_layers/README.md)：归约层独立数组候选已实现，
50,004组归约及hidden=896/vocab=64整核主机回归通过。
G:工具恢复后，新候选2021.1 HLS为3.650ns估算、归约II=1，RTL/XSim及C post-check通过；
完整200MHz BD布线后时序也已通过（WNS+1.067ns、WHS+0.010ns）。尚未生成上板版本或板测；详见reports内RESULT.md。

本轮目标是独立 M14 的 200 MHz，公共 ABI/原生 M06/整机集成已由用户明确移出当前范围。
已验收 100 MHz 的源码、bit/XSA/ELF、报告和交付 ZIP 均保留。

本目录提供 **仅综合、不导出 IP、不操作板卡** 的隔离诊断入口，读取当前生产源码，
在 `module_14_lm_head_v2/build/frequency_200_20261016/` 创建独立工程。
没有使用 `open_project -reset`，重复运行会拒绝覆盖原诊断结果。

已完成静态分析和首次 **2021.1 / 5 ns HLS 诊断**。起初 G: 工具盘不可见，
用户表示将恢复后再次检查路径已可见，随后执行；进程已于2026-10-16 19:25:45+08:00退出。
诊断完成不等于200 MHz达标：顶层估算5.328 ns / 187.71 MHz，点积II=1保持，
部分归约循环II从旧构建的3增至5，尚未新RTL验证、布局布线或上板。
完整结论见 `../../reports/frequency_200_20261016/diagnostic_summary.json`。

```powershell
./module_14_lm_head_v2/experiments/frequency_200_20261016/run_csynth_200.ps1
# 如果工具安装位置不同：
./module_14_lm_head_v2/experiments/frequency_200_20261016/run_csynth_200.ps1 -VitisHls '实际路径/vitis_hls.bat'
```

诊断使用 `create_clock -period 5.000`、显式 HLS uncertainty=1.350 ns（27%），
保留 64-bit M_AXI 配置和 H8/V1/16-slot 数值结构。
它不会修改 `scripts/run_csynth.tcl` 的 100 MHz 默认值，
也不会改写 `build/lm_head_v2_export` 或正式 IP repository。

HLS 能生成 RTL 不等于 200 MHz 达标。完成后检查：

1. `dot_word_loop` achieved II 是否仍为 1，依赖相关警告和 FP operator latency。
2. `read_context_slot`、归约、policy 的调度是否使每行处理成为新瓶颈。
3. HLS 时钟估算、资源变化和所有 warning；不能用 HLS 估算代替 post-route。
4. 再进入保持相同数值合同的 CSim/RTL 和独立 200 MHz BD/实现。

此诊断还没有创建正式 200 MHz build identity。当前源码 `build_config=0x10008011`
仍代表已验收 100 MHz；它不是可直接下载宣称为 200 MHz 的板测产物。
正式候选上板前需同步时钟身份、PS/PL 初始化、主机周期换算与 checker，
不继续沿用 `ip_seconds_100mhz` 或旧 ELF/bit 配对。

分析与门槛见 `../../reports/frequency_200_20261016/ANALYSIS.md`。
