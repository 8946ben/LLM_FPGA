# 模块 16 Vitis HLS 仿真工程

目标数据流：

```text
CPU/网口 -> hidden + history bitmap -> LM Head -> FP16 logits
         -> repetition penalty -> argmax -> token ID -> CPU/网口
```

<!-- 补充时间：2026-07-21；补充人：zb；内容：AXU9EGB 精确器件适配、综合与 RTL 联合仿真结果。 -->
当前环境使用 Vitis HLS 2021.1，综合目标已切换为 AXU9EGB 搭载的
`XCZU9EG-2FFVB1156I`（Vivado part：`xczu9eg-ffvb1156-2-i`），目标时钟为
200 MHz（5 ns）。当前 Vivado 已安装该芯片 part，但没有安装 ALINX 的
AXU9EGB board preset；因此当前结果属于“精确芯片级 HLS/RTL 验证”，尚不包含
PS、DDR4、RGMII 网口引脚和板级时钟复位设计。

## 生成真实 trace fixture

```powershell
python tools\prepare_lm_head_hls_fixture.py
```

<!-- 补充时间：2026-07-21；补充人：zb；内容：trace 来源、repetition penalty 与验证口径经验。 -->
## Trace 来源与 repetition penalty 验证经验

### 当前 FPGA 内核的实际计算顺序

当前 `lm_head_argmax` 内核执行：

```text
hidden[896] 写入片上缓存
  -> 对 151936 个 token 分别计算 FP16 权重 × FP16 hidden、FP32 累加
  -> FP32 accumulator 转换为 FP16 raw_logit
  -> 可选写回 raw_logits[151936]
  -> 可选 repetition penalty
  -> argmax（分数相同时保留较小 token ID）
  -> selected_token + selected_score
```

repetition penalty 是可开关功能，由以下参数控制：

```text
enable_repetition_penalty
repetition_penalty
history_bitmap
```

当前真实 trace 的 HLS C 仿真与 TCP 回环均使用：

```text
enable_repetition_penalty = 1
repetition_penalty = 1.1
```

关闭 `enable_repetition_penalty`，或使用 penalty `1.0`，内核就退化为 raw LM Head logits 直接 argmax。

<!-- 补充时间：2026-07-25；补充人：zb；内容：真实板卡 trace 客户端默认关闭 repetition penalty。 -->
### 当前上位机默认策略

`tools/run_module16_board_trace.py` 默认不设置 LMH1 的
`ENABLE_REPETITION_PENALTY` 标志，即默认执行 raw LM Head logits 直接
argmax：

```text
enable_repetition_penalty = 0
```

如需复现本节所述 `model.generate()` trace 的 processed scores，必须显式使用：

```powershell
python tools\run_module16_board_trace.py `
  --enable-repetition-penalty `
  ...
```

板端没有跨请求的 penalty 全局状态；是否启用以及 penalty 数值都由每个
`RUN_TOKEN` 请求携带。为兼容旧命令，`--disable-repetition-penalty` 仍可接受，
但在当前默认关闭策略下无需再写。

### 当前 trace 不是由 manual_prefill_decode.py 生成的

`qwen25_0p5b_instruct_full_generation_trace` 的 `metadata.json` 包含：

```text
full_sequence_ids
full_text
record_step_count
record_steps
generation_score_shapes
```

这些字段与 `run_full_generate_trace.py` 的输出一致。metadata 还说明当前目录是原始 `generate_002` 数据为模块级 FPGA 对齐而生成的重命名副本。

`manual_prefill_decode.py` 则会写出 `manual_prefill_decode_metadata.json`，并使用不同的字段结构。因此当前 trace 的生成路径应理解为：

```text
run_full_generate_trace.py
  -> model.generate(..., do_sample=False, output_scores=True)
  -> 原始 generate_002 trace
  -> 目录与文件名整理
  -> qwen25_0p5b_instruct_full_generation_trace
```

### 为什么脚本没有显式写 1.1，但 generate 数据仍包含 penalty

`run_full_generate_trace.py` 没有在 `model.generate()` 参数中显式传入 `repetition_penalty=1.1`，但 `from_pretrained()` 会加载模型目录的 `generation_config.json`。Qwen2.5-0.5B-Instruct 的 generation config 配置了：

```json
"repetition_penalty": 1.1
```

`do_sample=False` 只关闭随机采样，不会关闭 repetition penalty。因此 `model.generate()` 的实际 token 选择流程是：

```text
raw LM Head logits
  -> RepetitionPenaltyLogitsProcessor(1.1)
  -> processed generation scores
  -> greedy argmax
```

### trace 中存在两类不同含义的“logits”

| 数据 | 实际含义 | 是否包含 repetition penalty | FPGA 验证用途 |
| --- | --- | --- | --- |
| 每个 step 的 `lm_head_vocab_logits.npy` | 模型 forward 内部记录的 FP16 raw LM Head logits | 否 | 验证矩阵向量乘和 FP16 输出 |
| `generation_token_vocab_logits/*.npy` | `model.generate()` 返回的 FP32 processed scores | 是，1.1 | 验证 repetition penalty 后的完整分数 |
| `metadata.json` 的 `generated_ids` | processed scores 的 greedy argmax 结果 | 间接包含生成策略 | 验证最终 token |

`generation_token_vocab_logits` 这个目录名容易被误认为 raw logits；更准确的语义是 `generation_processed_scores`。

### manual_prefill_decode.py 的行为

当前 `manual_prefill_decode.py` 每一步直接执行：

```python
next_token = torch.argmax(outputs.logits[:, -1, :], dim=-1, keepdim=True)
```

它保存的也是 `outputs.logits`，没有维护历史 token 集合，也没有应用 repetition penalty。因此其流程是：

```text
raw LM Head logits -> direct argmax
```

如果要让 FPGA 严格复现这个脚本，应关闭 `enable_repetition_penalty`。如果要复现当前 `model.generate()` trace，则应开启 penalty 并设置为 `1.1`。

### 数值反算结论

使用 trace 的 raw logits 和完整 token 历史进行反算：

| 设置 | 与 `generation_token_vocab_logits` 的比较结果 |
| --- | --- |
| repetition penalty = `1.1` | 8/8 PASS，最大误差 `1.90735e-06` |
| repetition penalty = `1.0` | 8/8 FAIL，各步最大误差约 `1.07`～`2.73` |

因此可以从数据本身确认：当前 generation scores 确实应用了 repetition penalty `1.1`。

### 重要验证陷阱：只比较 generated_ids 不足以验证 penalty

当前 8 个步骤中均满足：

```text
raw_top1 == processed_top1 == metadata.generated_ids
```

也就是说，这组输入中 repetition penalty 改变了部分历史 token 的分数，但没有改变最终 Top-1。因此，即使错误地关闭 penalty，8 个 token ID 仍可能全部匹配。

验证 repetition penalty 时必须同时检查：

1. raw FPGA logits 是否匹配 `lm_head_vocab_logits.npy`；
2. 对 raw logits 应用 history bitmap 和 penalty 后，完整 processed scores 是否匹配 `generation_token_vocab_logits/*.npy`；
3. processed argmax 是否匹配 `metadata.generated_ids`；
4. 增加一个专门构造的用例，使 repetition penalty 能真正改变 Top-1 token。

当前 HLS testbench 的 synthetic case 已覆盖第 4 项：token 0 的 raw score 最大，但因其出现在历史中并受到 penalty，最终应选择 token 1。

### 后续 trace 记录建议

为避免再次混淆，后续生成 trace 时建议在 metadata 中显式记录：

```json
{
  "do_sample": false,
  "repetition_penalty": 1.1,
  "scores_semantics": "processed_generation_scores",
  "raw_logits_semantics": "lm_head_output_before_logits_processors"
}
```

同时建议把 raw logits 与 processed scores 分开命名、分别验证，不能仅凭最终 token 一致就判断所有生成策略均已实现。

## C 仿真

默认一次加载权重并验证全部 8 个真实 trace step：

```powershell
D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat `
  -f module16_lm_head_hls\run_csim.tcl
```

指定其他 step：

```powershell
D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat `
  -f module16_lm_head_hls\run_csim.tcl -tclargs 0
```

## C 综合

```powershell
D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat `
  -f module16_lm_head_hls\run_csynth.tcl
```

## 导出 Vivado IP

2026 年运行 Vitis HLS 2021.1 时，自动生成的 `core_revision` 会超过
Vivado 接受的 signed 32-bit 范围。请使用兼容入口：

```powershell
module16_lm_head_hls\run_export_ip_2021_compat.ps1
```

导出目录：

```text
module16_lm_head_hls/build/lm_head_export/solution1/impl/ip
```

Vivado Catalog 中的 VLNV 为：

```text
xilinx.com:hls:lm_head_argmax:1.0
```

## RTL co-simulation

RTL co-simulation 使用小矩阵验证综合后的 AXI/控制 RTL。全尺寸数值验证由默认的 8 步 C 仿真负责：

```powershell
D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat `
  -f module16_lm_head_hls\run_cosim.tcl
```

当前版本首先建立 correctness baseline，点积尚未做多 PE/HBM 通道优化。性能优化应在 C 仿真、真实 trace 和接口协议稳定后进行。

## TCP 回环仿真

以下命令通过真实的本机 TCP 栈完成 CPU 客户端 → 板端服务模拟器 → LM Head → token/logits 回传：

```powershell
python tools\run_module16_tcp_loopback.py --step 0
```

完整 8 步验证可对 `--step 0` 到 `--step 7` 依次执行。模拟器只替代尚不存在的板卡驱动、DDR/HBM 调度和网口栈；计算核本身仍以 HLS C/RTL 仿真结果为准。

## 当前验证结论

- 全尺寸 HLS C 仿真：8/8 真实 Qwen trace 通过，token 8/8 完全匹配。
- AXU9EGB/ZU9EG 全尺寸 C 综合：通过；目标周期 5 ns（200 MHz），估计周期 3.650 ns（约 273.97 MHz）。
- AXU9EGB/ZU9EG 缩小同构核 RTL co-simulation：Verilog/XSim 通过，1/1 事务，542 cycles。
- TCP 回环：8/8 真实 trace 通过，token 8/8 完全匹配，Top-5 均为 5/5。
- 全尺寸串行基线综合估计：1,097,890,446 cycles，在 5 ns 目标周期下约 5.489 s/token；点积 II=8。它是功能基线，不是最终性能方案。

详细数据见 `SIMULATION_REPORT.md`。
