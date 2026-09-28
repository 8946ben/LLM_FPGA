# 16 LM Head + Argmax 可选模块

负责人：zb  
目标模型：Qwen2.5-0.5B-Instruct  
目标板卡：ALINX AXU9EGB（`xczu9eg-ffvb1156-2-i`）  
工具版本：Vitis HLS / Vivado / Vitis 2021.1  
当前状态：HLS C/RTL 仿真、Vivado 实现、PS 裸机程序、TCP 上位机和真实板卡 8-step trace 均已通过。

## 模块边界

当前由 PC 上位机读取保存数据并发送最后一个 token 的 hidden state 至 FPGA；
同一协议未来可复用于 Orin 侧。模块完成：

```text
hidden[896]
  -> LM Head: FP16 权重 × FP16 hidden，FP32 累加 
  -> FP16 raw logits[151936]
  -> 可选 repetition penalty 
  -> greedy argmax 
  -> selected_token + selected_score
```

> 人工补充说明（zb，2026-07-25）

该模块可归纳为三个计算阶段：

1. LM Head 线性映射

   输入是长度为 896 的 hidden vector，权重按 `[vocab_size, hidden_size]`
   存储，即 `[151936, 896]`：

   ```text
   raw_logits = weight @ hidden
   [151936] = [151936, 896] @ [896]
   ```

   输入和权重为 FP16，点积采用 FP32 累加，最后转换为 FP16 raw logits。

2. repetition penalty

   对已经出现在输入或已生成历史中的 token，根据 raw logit 的符号调整分数。
   当前标准 PC 上位机默认关闭该功能，以便与Qwen2.5-0.5B_FPGA模块拆分与验证指南.md中的 raw LM Head
   计算保持一致；使用 `--enable-repetition-penalty` 可显式开启。

   当前给的 trace 中：

   ```text
   各 step 的 lm_head_vocab_logits.npy
     = penalty 之前的 raw LM Head logits

   generation_token_vocab_logits/*.npy
     = model.generate() 经 repetition penalty 处理后的 scores
   ```

3. Argmax token 选择

   在 penalty 关闭时，对 raw logits 执行 argmax；开启时，对 penalty 处理后的
   scores 执行 argmax：

   ```text
   selected_token = argmax(scores)
   selected_score = scores[selected_token]
   ```

   `selected_token` 是最大分数所在位置的 token ID，而 `selected_score` 是该
   token 的分数。分数相同时保留较小 token ID。

权重采用 Qwen2.5-0.5B-Instruct 的 tied embedding：

```text
model.embed_tokens.weight
shape = [151936, 896]
dtype = FP16 little-endian
```

对第 `v` 个词元：

```text
acc_v = sum(hidden[i] * weight[v, i]), i = 0..895
raw_logit_v = FP16(acc_v)
```

若词元 `v` 已在历史中且启用了 repetition penalty：

```text
score_v = raw_logit_v * penalty    , raw_logit_v < 0
score_v = raw_logit_v / penalty    , raw_logit_v >= 0
```

否则 `score_v = raw_logit_v`。最后选择 `argmax(score_v)`；分数相同时保留较小
token ID。

当前标准上位机默认关闭 repetition penalty。只有显式传入
`--enable-repetition-penalty` 时才开启，默认 penalty 数值为 `1.1`。板端和 HLS
内核始终保留逐请求动态开关能力。

## 接口与输出选择

HLS 顶层函数为：

```cpp
lm_head_argmax(
    hidden,
    weight,
    history_bitmap,
    raw_logits,
    hidden_size,
    vocab_size,
    write_logits,
    enable_repetition_penalty,
    repetition_penalty,
    selected_token,
    selected_score);
```

数据接口包括四个独立的 AXI4 master：

```text
m_axi_gmem_hidden
m_axi_gmem_weight
m_axi_gmem_history
m_axi_gmem_logits
```

控制接口为 `s_axi_control`。`write_logits=1` 时写回完整
`raw_logits[151936]`；为 `0` 时只返回 token 和 score，适合正常推理。

## 目录

```text
hls/           HLS 源码、testbench 和构建 Tcl
ip_repo/       Vitis HLS 导出的 Vivado IP repository
vivado/        AXU9EGB Block Design 和实现 Tcl
vitis_ps/      Cortex-A53 裸机 lwIP 服务端、链接脚本和 BSP PHY 补丁
orin_backend/  LMH1 TCP 协议、客户端、模拟器和 trace 上位机
tests/         权重导出、fixture 准备和板卡小矩阵测试
reports/       HLS、Vivado 和真实板卡验收报告
```

## 数据准备

仓库不提交模型权重和完整 trace。先取得模型：

[Qwen2.5-0.5B-Instruct（ModelScope）](https://www.modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct)

在本模块目录运行：

```powershell
python tests\export_lm_head_weight.py `
  D:\models\Qwen2.5-0.5B-Instruct `
  artifacts\model.embed_tokens.weight.fp16.npy

python tests\prepare_lm_head_hls_fixture.py `
  --trace-dir D:\data\qwen25_0p5b_instruct_full_generation_trace `
  --output-dir artifacts\module16_hls_fixtures
```

`prepare_lm_head_hls_fixture.py` 从每一步读取：

```text
lm_head_input.npy
lm_head_vocab_logits.npy
metadata.json
```

并生成 HLS/网口测试使用的 hidden、raw logits、history bitmap 和 expected token。

## HLS 复现

```powershell
vitis_hls.bat -f hls\run_csim.tcl
vitis_hls.bat -f hls\run_csynth.tcl
vitis_hls.bat -f hls\run_cosim.tcl
powershell -ExecutionPolicy Bypass -File hls\run_export_ip_2021_compat.ps1
```

2026 年使用 Vitis HLS 2021.1 导出 IP 时，自动生成的 `core_revision` 可能超过
Vivado 接受的 signed 32-bit 范围；兼容脚本会在 HLS 主流程失败后把临时打包
Tcl 中溢出的 revision 改为 `1`，再调用 Vivado 完成打包。

## 真实板卡运行

板端默认静态地址：

```text
IP   192.168.8.190
TCP  19016
协议 LMH1 version 1
```

先按 `vivado/README.md` 和 `vitis_ps/README.md` 重建并烧写工程。完整权重只需在
板卡重启后上传一次：

```powershell
cd orin_backend

python tools\run_module16_board_trace.py `
  --weight ..\artifacts\model.embed_tokens.weight.fp16.npy `
  --fixture-root ..\artifacts\module16_hls_fixtures `
  --trace-root D:\data\qwen25_0p5b_instruct_full_generation_trace `
  --step 0 `
  --load-weight `
  --return-logits
```

后续 step 复用板端 DDR 权重，去掉 `--load-weight`。默认关闭 penalty；复现
`model.generate()` 的 processed scores 时增加：

```text
--enable-repetition-penalty
```

## 验收摘要

```text
HLS C 仿真：8/8 trace PASS
RTL co-simulation：Verilog/XSim PASS，542 cycles（4x4 同构小核）
Vivado implementation：100 MHz，WNS 3.921 ns，所有时序约束满足
真实板卡默认 penalty OFF：8/8 generated IDs、raw Top-5、raw logits PASS
真实板卡 penalty ON(1.1)：8/8 processed scores、Top-5、generated IDs PASS
真实板卡最坏 raw logits 最大绝对误差：0.015625，阈值 0.02
完整权重上传：272269312 bytes，约 7.692 s
全尺寸 FPGA 计算：约 11.09 s/token
```

详细结果见 `reports/BOARD_ACCEPTANCE.md`。

## 不随提交包上传的内容

目标仓库 `.gitignore` 排除了 `.bit`、`.xsa`、`.elf`、日志和 Vivado/Vitis
生成目录，本提交包遵守该约定，并且不包含：

```text
Qwen 模型权重或 model.safetensors
完整 qwen25_0p5b_instruct_full_generation_trace
Vivado/Vitis workspace、cache、backup、journal、log
预构建 bitstream、XSA、ELF
```

这些产物可由本目录源码和 Tcl 重新生成。本地已验收产物的 SHA-256 记录在
`reports/BOARD_ACCEPTANCE.md`，便于内部复核。

> 人工补充说明（zb，2026-07-25）

完整 Vivado 工程、bitstream 和完整 trace 已另行打包为大文件附件，我单独发。

## 当前限制

当前实现是 correctness baseline：每个词表行串行完成 896 维点积，尚未进行多
PE、权重分片、多 DDR/HBM 通道或流水并行优化。它适合验证模块语义、接口和真实
板卡数据通路，不代表最终吞吐性能。
