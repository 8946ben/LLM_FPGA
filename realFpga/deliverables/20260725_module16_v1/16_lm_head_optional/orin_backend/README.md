# orin_backend

## 当前定位：PC 上位机，而非已接入 Orin 的推理 backend

本目录沿用目标仓库 `_example_rmsnorm_minimal` 的 `orin_backend/` 分类名称，但
当前放置的是 PC 端独立上位机和验证程序。它不启动整套 Qwen 推理，而是直接
读取上一模块已经保存的 hidden、history 和 golden logits，通过网口调用 FPGA：

```text
PC 读取 trace/权重
  -> LMH1 TCP
  -> 开发板 PS
  -> FPGA LM Head + 可选 repetition penalty + argmax
  -> token/score/可选 raw logits 返回 PC
  -> PC 与 golden 数据比较
```

当前尚未完成以下 Orin 运行时集成：

```text
未接入目标仓库 orin_runtime
未从正在运行的 Qwen 推理中拦截 LM Head tensor
未处理 CUDA/torch tensor
未实现通过 fpga-modules 参数替换原模型 LM Head
```

这些 Python 协议和客户端代码将来可以在 Orin 侧复用，但“可在 Orin 上运行”
不等于“已经实现 Orin backend”。现阶段验收链路明确是 PC 上位机读取保存数据
后调用真实板卡。

```text
module16_lm_head_hls/net/lmh_protocol.py          LMH1 帧格式与 CRC32
module16_lm_head_hls/net/cpu_client.py            PING/LOAD_WEIGHT/RUN_TOKEN
module16_lm_head_hls/net/fpga_server_emulator.py  NumPy 软件板端模拟器
tools/run_module16_board_trace.py                 单 step trace/板卡验收
tools/run_module16_tcp_loopback.py                本机 TCP 回环
```

依赖 Python 3.10+ 和 NumPy。请从本目录运行，以便 Python 找到
`module16_lm_head_hls`：

```powershell
python tools\run_module16_board_trace.py --inspect-only --step 0

python tools\run_module16_board_trace.py `
  --start-emulator `
  --load-weight `
  --return-logits `
  --step 0
```

真实板卡时去掉 `--start-emulator`，默认连接 `192.168.8.190:19016`。

默认关闭 repetition penalty。增加 `--enable-repetition-penalty` 才会设置
LMH1 flag bit 0，并把 history bitmap 送入板端。

## `--enable-repetition-penalty` 的具体作用

### 默认关闭

不带该参数时：

```powershell
python tools\run_module16_board_trace.py --step 0
```

上位机发送的 `RUN_TOKEN` 请求满足：

```text
LMH1 flags bit 0 = 0
enable_repetition_penalty = 0
```

此时即使请求中携带了 history bitmap 和 `repetition_penalty=1.1`，FPGA 也不
应用 penalty，直接对 raw LM Head logits 做 argmax：

```text
selected_token = argmax(raw_logits)
```

### 显式开启

使用：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --enable-repetition-penalty `
  --repetition-penalty 1.1
```

上位机会设置：

```text
LMH1 flags bit 0 = 1
enable_repetition_penalty = 1
repetition_penalty = 1.1
```

板端把该开关、penalty 数值和 history bitmap 传给 HLS IP。history bitmap
使用一个 bit 表示一个 token 是否已经出现在输入或已生成序列中：

```text
word_index = token_id / 32
bit_index  = token_id % 32
seen       = (history_bitmap[word_index] >> bit_index) & 1
```

### 计算公式

首先计算第 `v` 个 token 的 raw LM Head logit：

```text
acc_v = sum(hidden[i] * weight[v, i]), i = 0..895
raw_logit_v = FP16(acc_v)
```

其中输入和权重为 FP16，点积在 FP32 中累加，最终转换成 FP16 raw logit。

若没有启用 penalty，或者 token `v` 没有在历史中出现：

```text
score_v = raw_logit_v
```

若启用了 penalty 且 token 已经出现，设 `p=repetition_penalty`：

```text
raw_logit_v < 0 : score_v = raw_logit_v * p
raw_logit_v >= 0: score_v = raw_logit_v / p
```

最后执行：

```text
selected_token = argmax(score_v)
selected_score = max(score_v)
```

内核使用严格的 `>` 更新最优 token，因此两个 FP16 分数相同时保留较小的
token ID。

当 `p>1` 时，已出现 token 的正分数会变小，负分数会变得更负，因此它们再次
成为 Top-1 的可能性降低。例如真实 trace step 2 中：

```text
raw score                   = 30.046875
penalty=1.1 后的 score      = 30.046875 / 1.1
                            = 27.315340...
```

### raw logits 与 processed scores 的区别

repetition penalty 不会改写 `raw_logits` 输出缓冲区。HLS 内核先将原始 FP16
logit 写入 `raw_logits`，再用 penalty 后的临时 `score_v` 完成 argmax。因此：

```text
--return-logits 返回的仍是 penalty 之前的 raw FP16 logits
selected_score/token 使用的是 penalty 之后的 score（启用时）
```

对应当前验证数据：

```text
lm_head_vocab_logits.npy
  = raw LM Head logits，不包含 repetition penalty

generation_token_vocab_logits/*.npy
  = model.generate() 的 processed scores，包含 repetition penalty=1.1

metadata.json generated_ids
  = processed scores 的 greedy argmax
```

当前 8-step trace 在 penalty 开启和关闭时恰好得到相同 Top-1 token，所以不能
只凭 `generated_ids` 判断 penalty 是否生效；开启模式还必须比较完整 processed
scores，或使用能让 penalty 改变 Top-1 的构造用例。

该开关是每个 `RUN_TOKEN` 请求独立携带的，不是板端永久状态，也不需要为切换
开关重新生成 bitstream 或 ELF。

完整协议见 `LMH1_PROTOCOL.md`。
