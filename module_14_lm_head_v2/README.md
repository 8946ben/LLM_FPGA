# M14 LM Head V2

本目录是旧 `module16_lm_head_hls` 的独立 V2 升级实现。旧目录继续作为 FP16、
单 MAC、II=8 和 11.09 s 板测基线，不被覆盖。

2026-10-10：完整独立 Decode/penalty-ON 55-run campaign 严格通过，包括 8-step
生产/debug、4 类负例、30 次独立性能和 1,000 次稳定性。IP median 224.868 ms。
见[实板验收报告](reports/20261010_BOARD_ACCEPTANCE.md)。优先使用
[TCP 网口权重加载](standalone/TCP_WEIGHT_LOADING.md)，完整权重与 DDR 校验实测 8.36 秒；
默认冻结 loader 包已上板。其他模式/APM/公共 ABI/M06 V2 trace/全系统集成门槛仍待补齐。

## 当前实现

```text
BF16 hidden 128-bit read -> 8-bank FP32 hidden cache
BF16 weight 128-bit stream -> 8 parallel FP32 products/cycle
16-way interleaved accumulators -> two-context FIFO -> fixed FP32 reduction
history bitmap -> repetition penalty -> streaming argmax
optional pre-penalty FP32 logits
```

生产配置为 H8/V1、100 MHz、`write_logits=0`。一行权重恰好是 112 个 128-bit
beat，完整词表是 17,016,832 beat。交错 accumulator 将同一状态的反馈距离从 1
拉到 16，目标是 `dot_word_loop` achieved II=1。深度 32 的 256-bit context FIFO
容纳两行 partial snapshot，使下一行点积与上一行归约通过 DATAFLOW 重叠。

## 目录

- `include/`、`src/`：HLS 顶层和 ABI 兼容常量；
- `tb/`：HLS 小尺寸功能/错误用例；
- `reference/`：BF16 bit-aware reference 和真实资产导出；
- `golden/`：小型 manifest；大数据位于被忽略的 `artifacts/`；
- `scripts/`：CSim、co-sim、综合和 IP 导出；
- `board/`：M14 V2/HP2 单模块 Vivado 工程脚本；
- `drivers/`：PS 侧逻辑 job/result 合同；
- `reports/`：经审核的验证、综合和板测结果；
- `BOARD_TEST_PLAN.md`：单模块上板验收流程。

## 软件验证

```powershell
$env:PYTHON = '<python.exe>'
.\scripts\run_reference_tests.ps1

.\scripts\generate_assets.ps1 `
  -ModelPath ..\artifacts\Qwen2.5-0.5B-Instruct `
  -FixtureRoot ..\artifacts\module16_hls_fixtures `
  -OutputRoot ..\artifacts\module14_v2_assets

python .\reference\verify_assets.py `
  --asset-root ..\artifacts\module14_v2_assets `
  --manifest .\golden\v2_trace_manifest.json
```

必须从原始 safetensors 提取 BF16 权重。旧 FP16 NPY 只保留为兼容 fallback，不能
作为完整系统共享权重的最终来源。

## HLS 验证

```powershell
$env:VITIS_HLS_BIN = '<Vitis_HLS_2021.1>\bin\vitis_hls.bat'
.\scripts\run_hls.ps1 csim
.\scripts\run_hls.ps1 cosim
.\scripts\run_hls.ps1 csynth
.\scripts\run_hls.ps1 export
```

综合后必须检查 `dot_word_loop` 的 achieved II，而不能只看顶层 latency。导出 IP
前还要核对 M_AXI 数据宽度、burst/outstanding、FP 运算单元数量、DSP/BRAM/LUT 和
100 MHz 时序。

## 2021.1 离线验证状态

- Vitis HLS：CSim 通过；6/6 RTL 事务及 C post-check 通过；生产
  `dot_word_loop achieved II=1`，8 个 FP32 multiplier 与 8 个 FP32 adder；
- Vivado：100 MHz post-route WNS `+3.649 ns`、WHS `+0.010 ns`，0 DRC error，
  31,290 CLB LUT、42,618 register、22 BRAM tile、59 DSP；
- standalone：AArch64 ELF 已用 2021.1 BSP/driver 构建，无 undefined symbol；
- 原始板测输入：`reports/board_package_20260930/`；当前脚本默认使用
  `reports/board_package_20261009/`（原 bit/XSA + 修复失败计时的新 ELF）。

详细证据见 `reports/20260930_HLS_VALIDATION_2021_1.md`、
`reports/20260930_VIVADO_VALIDATION_2021_1.md` 和
`reports/20260930_STANDALONE_BUILD_2021_1.md`。

## 实板验证状态

2026-09-30 已完成 PS/DDR 初始化、PL 配置、272,269,312-byte BF16 权重加载和
step_00 单步测试。硬件 top-1 token 与 V2 golden 一致，IP 总周期为 22,486,802，
100 MHz 下为 224.86802 ms。2026-10-09 确认旧 Python 最后 8 lane 的归约树与
C++/RTL 不同；修正为相邻 lane 合并后，归档 step_00 的 151,936 个 raw logits
全部逐位一致，score bits/CRC 完全匹配。数值合同见 `NUMERIC_CONTRACT.md`。
Python 8/8、CSim、新增反例的 7/7 RTL CoSim 通过；8-step golden 已重新计算，
输入权重/hidden/history 不变，旧 golden 保留于 `reports/numeric_20261009/legacy_golden/`。
当前 JTAG/DDR 状态无法复用，尚未开始本轮 8-step、稳定性和整机集成。

完整交接、证据路径和恢复命令见 `../doc/LM_HEAD_V2_HANDOFF_20261009.md`。

板测程序按 `BOARD_TEST_PLAN.md` 记录 JSON 后，可用
`reference/compare_board_results.py` 自动检查 8-step token/CRC、工作量计数器以及
生产模式延迟的 median/P95。

## 尚待公共 ABI 冻结

当前按优化计划的建议实现 `valid_rows=1`、pre-penalty FP32 optional logits、
token/score 的 IEEE CRC32。公共头发布后，这些枚举和语义应从统一生成源替换，
不得在驱动和 HLS 中继续维护两份定义。
