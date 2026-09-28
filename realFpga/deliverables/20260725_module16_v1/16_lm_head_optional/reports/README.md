# reports

```text
hls/lm_head_argmax_csynth.rpt       HLS 综合、latency 与资源
hls/lm_head_argmax_cosim.rpt        Verilog/XSim 联合仿真
hls/SIMULATION_REPORT.md            仿真阶段总结
vivado/*timing_summary*.rpt         routed timing
vivado/*utilization*.rpt            placed utilization
vivado/*power*.rpt                  routed power estimate
BOARD_ACCEPTANCE.md                 真实 AXU9EGB 验收摘要
```

HLS 综合目标周期为 5 ns；实际 Block Design 使用 100 MHz。完整报告保持原始
Vivado/Vitis HLS 文本格式，便于 reviewer 直接搜索 WNS、latency 和资源表。

