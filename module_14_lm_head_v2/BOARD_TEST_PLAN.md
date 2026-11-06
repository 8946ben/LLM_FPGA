# M14 V2 单模块上板验收

2026-10-10 执行状态：独立 Decode/penalty-ON 的 8-step 生产/debug、4 负例、
30 次独立性能、1,000 次连续调用已 PASS。TCP 上传及 6 项错误路径 PASS。
详见 `reports/20261010_BOARD_ACCEPTANCE.md`。以下为全部目标，未覆盖的模式/APM、
真实 M06 V2 trace 与公共 ABI 仍是整体集成前门槛，不能因本次 campaign PASS 自动勾选。

## 前置门槛

1. Reference 单测和 8-step golden 通过；
2. HLS compact CSim/RTL co-sim 通过；
3. 综合确认 `dot_word_loop` achieved II=1，并核对实际 FP multiplier/adder 数量；
4. 100 MHz 实现 WNS ≥ 0、post-route DRC 通过；
5. IP 的 `build_config`、capabilities 和生成寄存器头与 manifest 一致。

任一门槛失败时不进入板测。

## 独立硬件结构

- ZynqMP PS + M14 V2 + AXI SmartConnect；
- 四个 M_AXI bundle 均为 128 bit；
- 单模块环境优先连接 `S_AXI_HP2_FPD`，与完整系统分配一致；
- PL 用户时钟 100 MHz；
- AXI-Lite 控制口连接 PS `M_AXI_HPM0_FPD`；
- DDR 地址使用 40 bit，buffer 完整落在一个已登记的 PS DDR region；
- 权重、hidden、history、logits 均 64-byte 对齐。

## 准确度测试

先核对 BF16 权重 SHA256，然后依次执行：

1. synthetic penalty 改变 Top-1；
2. tie 选择较小 token；
3. penalty OFF 且 `write_logits=0`，确认 history/logits 无 AXI 事务；
4. 8 个真实 trace，debug 模式 `write_logits=1`；
5. 同一 8 步生产模式 `write_logits=0`；
6. BAD_ABI、BAD_FLAGS、BAD_DIMENSION、NUMERIC_ERROR；
7. 连续 1,000 次调用，检查结果和计数器无漂移。

大权重优先使用 `standalone/program_board_tcp.ps1`；JTAG 回退为
`standalone/program_board.ps1`。调用与负例入口为 `standalone/run_step.ps1` 和
`standalone/run_negative.ps1`。每次执行的 XSCT 原始日志、mailbox dump、可选 logits
和结构化 JSON 都写入 `reports/board_runs/`。

8-step 必须比较 raw logits、processed scores、selected token、selected score bits 和
CRC。只有 token 相同不足以证明 penalty 或矩阵乘正确。

2026-10-09 独立模块合同已冻结在 `NUMERIC_CONTRACT.md`：最终 8 lane 采用相邻
pair 的 FP32 树。修正 reference 后生成全新 golden，旧版保留用于审计；当前
`compare_board_results.py` 默认严格检查 score bits/CRC，并拒绝失败 mailbox。
标记 `excluded_from_acceptance` 的历史样本不进入验收和性能统计。

## 性能测试

权重只加载并 clean 一次。每种模式预热 3 次、正式运行至少 30 次，记录 median、
P95 和最大值：

- `write_logits=0/1`；
- penalty OFF/ON；
- Prefill/Decode；
- PS 侧 wall time；
- IP `perf_cycles_total/compute`；
- `weight_wait_cycles`、`dot_active_cycles`；
- HP2 APM 读带宽、burst、stall；
- CPU cache clean/invalidate 字节数。

生产模式不变量：

```text
vocab_rows_done        = 151936
weight_read_beats_128  = 17016832
logits_written         = 0
logits_write_beats_128 = 0
processed_rows         = 1
```

性能目标为 0.3～0.6 s，且相对旧 11.09 s RTT 至少提升 15 倍。如果 HP2 实测顺序
读带宽低于 0.8 GB/s，先检查 BD、SmartConnect、burst/outstanding 和 DDR，再考虑
增加计算 lane。

## 进入整体集成的条件

- 8-step V2 golden 全部通过；
- 30 次生产模式结果稳定；
- 100 MHz WNS ≥ 0；
- 无 DRC/AXI protocol 错误；
- 性能计数与 APM、PS wall time能互相解释；
- IP、driver、manifest、报告和 SHA256 已归档；
- `valid_rows`、optional logits、CRC 和数值合同已由公共 ABI 冻结。
