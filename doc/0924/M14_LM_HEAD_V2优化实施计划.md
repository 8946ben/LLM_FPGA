# M14 LM Head V2 优化实施计划

版本：V1.0  
编制日期：2026-09-28  
模块：M14 LM Head / Repetition Penalty / Argmax  
负责人：张本  
目标器件：ALINX AXU9EGB / `XCZU9EG-2FFVB1156I`  
工具基线：Vitis HLS / Vivado / Vitis 2021.1

配套依据：

1. `doc/0924/PS_PL 全模块架构、详细设计与统一集成实施计划.md`；
2. `doc/0924/PS_PL 全模块参数与接口字段说明书.md`；
3. `doc/LM_HEAD_PERFORMANCE_ANALYSIS_20260916.md`；
4. 当前 `module16_lm_head_hls`、真实板卡验收记录和已有 8-step golden trace。

本文是 M14 从现有独立 FP16 LM Head 基线迁移到统一 ABI V2，并完成第一轮计算与访存优化的执行计划。文中的性能目标是设计门槛，不是已经取得的实测结果。

### 2026-09-29 实施状态

- 已建立独立实现目录 `module_14_lm_head_v2`，旧 `module16_lm_head_hls` 保持不变；
- 已实现 128-bit BF16 接口、H8 FP32 点积、16 路交错累加、双 context FIFO、独立归约/penalty/argmax DATAFLOW 和可选 FP32 logits；
- 已实现 ABI V2 参数检查、build/capability、公共与 M14 扩展计数器、PS 侧逻辑 driver 合同；
- 已从原始 safetensors 提取共享 BF16 权重并生成 8-step V2 golden；
- 已准备 M14 V2/HP2/100 MHz 单模块 Vivado 创建与构建脚本，以及板测结果自动检查器；
- Python reference 单元测试 4/4 通过；
- 当前 Vitis HLS 安装 junction 指向未挂载的 `F:\Xilinx`，CSim、综合、co-sim、IP 导出和单模块板测仍待工具恢复后执行；
- `step_07` 在新 FP32 argmax 语义下选择 token `100048`，旧 FP16-round 语义为 `100013`，整体集成前必须冻结这一外部可见差异。

---

## 1. 目标与边界

### 1.1 交付目标

2026-10-10 前交付一个可以进入完整 V2 系统集成的 M14 包，满足：

- ABI V2、公共状态码、`build_config`、性能计数和 capability 完整；
- 外部激活和共享词表权重均为 BF16；
- PS DDR 数据口为 `ap_uint<128>`，权重主口在完整系统中连接 HP2；
- Embedding 与 LM Head 使用同一份 `VOCAB_VH_V2` 权重，不复制约 259.7 MiB 词表权重；
- 单物理 IP 同时接受 Prefill/Decode 两种 `run_mode`，两种模式都只消费最后一个 token 的 final RMS 输出；
- 生产路径 `write_logits=0`，在 PL 内完成 penalty 和 argmax，只返回 token/score；
- 基准优化配置为 `H_LANES=8`、`VOCAB_PAR=1`、交错 FP32 累加、100 MHz；
- 软件 reference、HLS C sim、C/RTL cosim、单 IP 板测或 AXI VIP 测试均有记录；
- 源码、IP、驱动、接口表、资源/时序/数值报告、manifest 和 SHA256 完整。

### 1.2 不在 10 月 10 日强制交付范围内

- 200 MHz 完整系统；
- `VOCAB_PAR>1` 的多词表 PE；
- HP2 之外的多 HP 分片；
- INT8/FP8 权重；
- top-k/top-p/temperature sampling；
- 生产路径完整 logits 回传；
- 修改 `VOCAB_VH_V2` 布局来迎合某一个并行度。

这些内容只能在 100 MHz 完整系统通过、HP2 APM 数据证明瓶颈位置、资源预算允许之后推进。

### 1.3 当前基线与 V2 目标的区别

| 项目 | 当前独立基线 | V2 目标 |
|---|---|---|
| 外部类型 | FP16 `half` | BF16 bit pattern |
| 权重 | LM Head 独立 FP16 导出 | 与 Embedding 共享 `VOCAB_VH_V2` |
| HLS 数据口 | 主要为 32-bit M_AXI | PS DDR 统一 128-bit beat |
| 点积 | 单乘法器、单加法器、单 accumulator，II=8 | 8 MAC lanes，每 lane 交错累加，目标 II=1 |
| 系统连接 | 独立工程接 HP0 | 完整 V2 系统 M14 接 HP2 |
| 频率 | 板上 100 MHz；HLS 曾按 200 MHz 综合 | 第一版全系统先保证 100 MHz |
| 输出 | 可写 FP16 raw logits | 生产只返回 token/score；debug 输出受控 |
| 接口 | LMH1 专用字段 | ABI V2 公共 job/result/capability |
| 性能统计 | host RTT、串口 `hw_us` | PL 周期、compute 周期、beat、stall、CRC、job 关联 |

现有 11.09 s 是旧版客户端整个 `RUN_TOKEN` 请求时间，不等于纯 PL 实测时间。旧综合最大周期 1,097,890,446 cycles 在板上 100 MHz 对应约 10.98 s，足以证明单 accumulator 的 II=8 是主瓶颈，但 V2 必须用新计数器重新测量。

---

## 2. 必须先冻结的语义

下列项目属于外部可见语义或公共 ABI。在 G0 评审后不得由 M14 单独修改。

### 2.1 数值合同

本计划建议冻结为：

1. hidden 和权重以 BF16 bit pattern 存储；
2. BF16 使用公共库 round-to-nearest-even 规则；
3. 读入 BF16 后扩展为 FP32；
4. 乘法为 FP32，累加为 FP32；
5. raw score 在 FP32 域执行 repetition penalty 和 argmax；
6. `selected_score` 为 penalty 后的 FP32；
7. 相同 score 时选择较小 token id；
8. NaN、Inf、overflow、underflow 按公共数值库和公共 `NUMERIC_ERROR` 规则处理。

这与旧内核“FP32 accumulator 先转 FP16 raw logit，再执行 penalty/argmax”的语义不同。旧 FP16 token 结果只能作为回归参考，不能直接替代 V2 BF16 golden。若架构负责人要求在 argmax 前增加 BF16 round，必须在 G0 修改 reference、接口说明和 numeric implementation ID，之后不允许只改硬件。

### 2.2 `optional_logits` 语义

0924 文档尚未明确 debug logits 的 dtype 和 penalty 前后位置。本计划建议冻结为：

- `optional_logits` 保存 penalty 前的 FP32 raw dot score；
- `ap_uint<128>` 每拍打包 4 个 FP32；
- `write_logits=0` 时指针可为 0，IP 不得产生任何 logits 写事务；
- `write_logits=1` 时有效字节数为 `151936×4=607744` bytes；
- penalty 后完整分数由软件结合 history 复算，或由受限 debug snapshot 提供，不进入生产接口。

原因是 raw dot score 更适合定位矩阵乘法误差，也与现有“raw logits 与 processed scores 分开验证”的经验一致。如果统一设计决定输出 penalty 后 score，该变化必须在 G0 冻结。

### 2.3 `valid_rows` 的接口缺口

全局规则要求 M05～M14 保留 `run_mode/valid_rows`，但 0924 文档给出的 `lm_head_v2` 原型遗漏了 `valid_rows`。本计划要求最终 M14 AXI-Lite 接口补充该字段：

```text
run_mode=PREFILL：valid_rows 必须为 1
run_mode=DECODE ：valid_rows 必须为 1
```

Scheduler 只把 final RMS 的最后一个有效 token row 传给 M14。`processed_rows` 成功时固定返回 1。若架构负责人决定 M14 不暴露 `valid_rows`，需要同步修订公共接口规则和驱动生成源，不能由模块实现自行省略。

### 2.4 CRC 合同

建议公共 `output_crc` 定义为以下 8 bytes 的 CRC：

```text
selected_token       uint32 little-endian
selected_score_bits  IEEE754 uint32 little-endian
```

Debug logits 另设只读 `logits_crc` 扩展寄存器。这样生产与 debug 模式的公共 output CRC 含义保持一致。CRC 多项式和寄存器偏移由架构负责人统一冻结。

### 2.5 必须由架构负责人冻结的剩余项

- module/layout/dtype/capability enum 数值；
- 公共和 M14 flags 位；
- AXI-Lite 寄存器偏移；
- BF16 公共转换函数及 NaN/Inf 规则；
- timeout class；
- Debug snapshot 上限；
- `build_config` 和 M14 扩展配置编码。

这些字段未冻结时，可以开发纯计算 core 和 testbench，但不能发布最终驱动/IP。

---

## 3. V2 逻辑接口与系统集成合同

### 3.1 顶层逻辑接口

最终顶层应等价于：

```c
void lm_head_v2(
    const ap_uint<128> *hidden,
    const ap_uint<128> *shared_vocab_weight,
    const uint32_t *history_bitmap,
    ap_uint<128> *optional_logits,
    uint32_t hidden_size,
    uint32_t vocab_size,
    uint32_t run_mode,
    uint32_t valid_rows,
    uint32_t write_logits,
    uint32_t enable_penalty,
    float repetition_penalty,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    uint32_t *selected_token,
    float *selected_score,
    common_result_v2 *result);
```

`common_result_v2` 在实际 HLS 顶层映射为 AXI-Lite 只读寄存器，不要求向 DDR 写 C struct。

### 3.2 地址、布局和有效范围

| Buffer | Layout / dtype | 有效范围 | 对齐 | 属性 |
|---|---|---:|---:|---|
| hidden | `ACT_TH_V2` / BF16 | 1792 bytes | 64 bytes | Final RMS 最后一行，只读 |
| shared vocab weight | `VOCAB_VH_V2` / BF16 | 272269312 bytes | 64 bytes | M05/M14 共享、immutable |
| history | `HISTORY_BITMAP_V2` / U32 | 18992 bytes | 64 bytes | PS 更新、M14 只读 |
| optional logits | debug FP32 | 607744 bytes | 64 bytes | `write_logits=1` 才需要 |

所有范围必须完整落入一个已登记的 PS DDR region，不能跨 `DDR_LOW` 和 `DDR_HIGH`。四个地址禁止互相 alias。`write_logits=0` 时不校验 logits 容量、不访问 logits 地址。

### 3.3 AXI bundle 与物理连接

HLS 中保留四个独立 bundle：

```text
m_axi_hidden
m_axi_weight
m_axi_history
m_axi_logits
```

数据 beat：hidden、weight、logits 使用 128 bit；history 逻辑元素为 U32，保持规范接口并在 manifest 中明确实际 AXI beat。完整系统中 weight 必须连接 HP2；其余 M14 低流量 bundle 默认经 M14 SmartConnect 汇入 HP2，除非集成架构根据 APM 数据调整。

四个 bundle 不代表四条独立物理 DDR 通道。性能报告必须按当前 BD 写明最终连接关系。

### 3.4 Scheduler、Memory Manager 和 Weight Store 约定

- M01 将 Final RMS 最后一行 descriptor 传给 M14，并透传本次 `run_mode/job_id`；
- M03 校验 dtype/layout/alignment/range/generation/alias；
- Final RMS 输出若由 PL 直接交给 M14，不做无意义 CPU invalidate/clean；
- M04 只加载一次共享 BF16 vocab 权重，校验 manifest/SHA256 后统一 clean；推理期间不重复 clean 259.7 MiB 权重；
- history 每次仅 clean CPU 实际修改的 cache line，不重复 clean 整个 bitmap；
- `selected_token/selected_score` 经 AXI-Lite 返回，不占用 PS DDR output buffer；
- `write_logits=1` 且 CPU 要读取时，M03 只 invalidate 有效 logits 范围。

### 3.5 capability

M14 至少声明：

- `WRITE_LOGITS_OPTIONAL`；
- `DUAL_RUN_MODE`；
- BF16 外部类型和 `VOCAB_VH_V2` 支持对应的统一 capability；
- performance counter / output CRC capability（按统一 enum）。

不支持的 sampling 参数由上层明确返回不支持，不能静默忽略。

---

## 4. 基准优化微架构

### 4.1 构建参数

10 月 10 日交付版采用：

```text
H_LANES             = 8
VOCAB_PAR           = 1
ACC_INTERLEAVE      = 16（综合后可在 8/16 中选满足 II=1 且资源更优者）
HIDDEN_TILE         = 32 BF16
WEIGHT_BURST        = 16 beats 起步
WEIGHT_OUTSTANDING  = 16 起步
WEIGHT_FIFO_DEPTH   = 128 beats 起步
DOUBLE_ACC_CONTEXT  = 1
TARGET_CLOCK        = 100 MHz
WRITE_LOGITS_DEFAULT= 0
```

`H_LANES=8` 正好匹配一个 128-bit beat 中的 8 个 BF16。第一版不以 `VOCAB_PAR>1` 消耗额外计算和带宽资源。

### 4.2 hidden 加载

1. 从 `ACT_TH_V2` 读取 112 个 128-bit beat；
2. 解包 896 个 BF16；
3. 使用公共转换函数一次性扩展为 FP32；
4. 保存到 8-bank FP32 hidden cache；
5. 后续所有 vocab row 复用，不再重复做 1.36 亿次 hidden BF16→FP32 转换。

FP32 hidden cache 仅 3584 bytes，远小于全系统 BRAM 预算；分 bank 是为了每拍向 8 个 MAC lane 提供 8 个值。

### 4.3 权重读取

权重布局固定为：

```text
E[vocab][hidden_group32][lane32]
```

一行 896 个 BF16：

```text
1792 bytes
= 112 个 128-bit beats
= 28 个 64-byte groups
= 7 个 16-beat bursts
```

完整扫描期望权重拍数：

```text
151936 × 112 = 17016832 beats
```

权重 reader 连续递增地址，使用 burst + outstanding + FIFO 吸收 PS DDR 延迟和 SmartConnect backpressure。第一版比较 `burst=16/32/64`、`FIFO=64/128/256`；最终选择以 HP2 APM 的有效带宽、stall 和完整系统时序为准，不按 HLS 单 IP 估计拍脑袋决定。

### 4.4 8-lane 点积

每拍解包 8 个 BF16 权重，扩展为 FP32，与 8-bank hidden cache 的 8 个 FP32 值并行相乘：

```text
8 weight/cycle × 8 hidden/cycle → 8 FP32 products/cycle
```

每个 lane 使用多个交错 partial accumulator，避免单 accumulator 的 FP32 加法反馈导致 II=8：

```text
partial[H_LANES][ACC_INTERLEAVE]
```

目标是权重 word 循环 achieved II=1，即每周期消费一个 128-bit weight beat。不能通过虚假的 `DEPENDENCE inter false` 隐藏真实依赖；必须由独立 partial state 消除反馈冲突。

每行前 `ACC_INTERLEAVE` 轮采用首次覆盖而不是先做 128 项串行清零，避免初始化 bubble。两个 accumulator context 采用 ping-pong：一组计算下一 vocab row 时，另一组执行归约。

### 4.5 归约

一行完成后，把 `8×ACC_INTERLEAVE` 个 FP32 partial 用固定归约树合并。要求：

- 归约顺序在 reference 中显式实现；
- 归约流水化；
- 不阻塞下一 vocab row 的权重读取和点积；
- 数值报告比较标量 reference、H8 和至少另一个性能配置；
- tie case 必须按最终 FP32 score 和较小 token id 规则验收。

### 4.6 history、penalty 和 argmax

词表按 token id 顺序扫描，因此不需要对同一个 history word 发起 32 次外部读取：

```text
读取 history[word_index]
→ 在寄存器内依次使用 32 个 bit
→ 再读取下一个 word
```

启用 penalty 时总共读取 4748 个 U32；关闭时不访问 history bundle。

基准 numeric implementation 保留直接 FP32 乘/除，保证语义清晰。把除法改为预计算倒数乘法属于另一个 `NUMERIC_IMPL_ID`，只有完整 processed-score 误差合同通过后才可启用。

每个 vocab row 产生一个最终 score，流式更新：

```text
best_score
best_token
```

`VOCAB_PAR=1` 时不需要大型 argmax tree。未来 `VOCAB_PAR>1` 时，每个 PE 维护局部最大值，末尾再做全局归约。

### 4.7 Dataflow

顶层划分为：

```text
load_hidden
read_weight_stream
dot_and_reduce
policy_and_argmax
optional_logits_write
```

使用 FIFO 和双 context 让主要稳态接近：

```text
Tkernel ≈ max(Tweight_read, Tdot_compute)
```

而不是 `Tweight_read + Tdot_compute + Treduce`。DATAFLOW FIFO 深度、生产/消费数量和退出条件必须在 RTL co-sim 中覆盖，防止只在 C sim 正常、RTL 死锁。

---

## 5. 性能模型和验收目标

### 5.1 理论下界

每次调用：

```text
MAC count        = 151936×896 = 136134656
weight bytes     = 272269312
weight beats128  = 17016832
```

`H_LANES=8`、II=1、100 MHz：

```text
compute lower bound = 136134656 / (8×100M)
                    = 0.17016832 s

HP2 peak lower bound = 272269312 / 1.6GB/s
                     = 0.17016832 s
```

两个下界相同，说明 H8 是单个 128-bit HP2 在 100 MHz 下自然的带宽匹配点。实际性能会受 DDR 仲裁、burst、stall、归约和系统竞争影响。

### 5.2 分级目标

| 阶段 | 目标 |
|---|---|
| 旧基线 | 保留 11.09 s RTT 和旧 bit/XSA/ELF/hash 作为回退证据 |
| V2 HLS | weight word loop II=1；连续消费 128-bit beat；无 dataflow deadlock |
| V2 单 IP 100 MHz | 生产模式完整词表目标 0.3～0.6 s；至少相对旧 RTT 提升 15× |
| V2 完整系统 | WNS≥0，功能正确；记录 HP2 竞争后的真实 P50/P95，不用单 IP 数字代替 |
| 系统调优阶段 | 依据 APM 判断是否调整 burst/FIFO/H lanes/vocab parallel |

0.3～0.6 s 是工程目标，不作为没有板级带宽数据时的虚假承诺。如果 HP2 顺序读基准本身低于 0.8 GB/s，应先定位 BD、SmartConnect、DDR 和 outstanding，而不是继续增加 DSP。

### 5.3 必须实现的计数器

公共：

- `perf_cycles_total`：从参数检查后启动到结果有效；
- `perf_cycles_compute`：从首个有效 weight beat 被计算 core 接收到最终 argmax 完成；
- `perf_read_beats`、`perf_write_beats`：按 manifest 声明的实际端口 beat 统计；
- `processed_rows=1`；
- `output_crc`；
- `build_config`。

M14 扩展：

- `vocab_rows_done`；
- `weight_read_beats_128`；
- `history_read_words`；
- `logits_write_beats_128`；
- `weight_wait_cycles`；
- `dot_active_cycles`；
- `logits_written`；
- 可选 `argmax_active_cycles`、FIFO high-water mark。

生产模式的期望不变量：

```text
vocab_rows_done          = 151936
weight_read_beats_128    = 17016832
logits_written           = 0
logits_write_beats_128   = 0
processed_rows           = 1
```

history 关闭时 `history_read_words=0`；开启时应为 4748，而不是 151936。

### 5.4 `build_config`

基准交付建议编码：

```text
PAR_LANES_CODE = 1    // 8 lanes
ROW_TILE       = 1
MAIN_TILE      = 32   // hidden tile 32 BF16
NUMERIC_IMPL_ID= 0    // 标准 BF16→FP32、FP32 penalty
CLOCK_CODE     = 0    // 100 MHz
MODULE_REVISION= 1
```

`VOCAB_PAR`、`ACC_INTERLEAVE`、FIFO、burst/outstanding 放入只读 M14 扩展构建寄存器和 `module_manifest.json`，不能只存在于源码宏中。

---

## 6. 验证计划

### 6.1 软件 reference 和 golden

新增 V2 reference，禁止沿用 FP16 half 计算冒充 BF16：

1. 从原始 BF16 `model.embed_tokens.weight` 导出共享 vocab 权重；
2. 以 raw `uint16` 或明确支持 BF16 的格式存储，manifest 写明 dtype/layout/shape/padding/SHA256；
3. final hidden 按公共 RNE 规则量化为 BF16；
4. BF16 扩展 FP32后，按冻结的归约顺序生成 raw score；
5. 分别生成 penalty OFF/ON 的 processed score、Top-5、selected token/score；
6. golden 记录 numeric implementation id 和生成脚本 hash。

### 6.2 功能用例

必须覆盖：

- 当前 8-step 真实 trace 的 V2 BF16 重生版本；
- penalty OFF/ON；
- `write_logits=0/1`；
- vocab 0、vocab 151935 和 history bit 31/32 边界；
- 正负 score；
- penalty 能真正改变 Top-1 的构造样例；
- 最大值并列时选择较小 token id；
- 全零、常数、极值、混合符号相消；
- 连续多次调用，确认 state 不串扰；
- Prefill/Decode 两种 `run_mode`，均 `valid_rows=1`；
- 至少 H8 与 H16（或另一个已声明配置）之间的数值一致性。

### 6.3 错误和接口用例

- `abi_version!=2` → `BAD_ABI`；
- hidden/vocab/valid_rows 非法 → `BAD_DIMENSION`；
- 地址不满足 64-byte/128-bit 对齐 → `BAD_ALIGNMENT`；
- descriptor 越界/跨 DDR region → PS 侧 `BAD_ADDRESS_RANGE`；
- dtype/layout 不匹配 → `BAD_LAYOUT`；
- `run_mode`、`write_logits`、`enable_penalty` 非法 → `BAD_FLAGS` 或 `BAD_DIMENSION`；
- penalty 非正、NaN、Inf → `NUMERIC_ERROR`；
- 未定义 flags 位 → `BAD_FLAGS`；
- `write_logits=1` 且指针/容量非法 → 对应错误；
- `write_logits=0` 且 logits 指针为空 → 正常完成且无写拍。

完整物理地址 region 和容量由 M03 校验；IP 自身至少校验 ABI、固定维度、模式、flags、可见地址对齐和运行参数，避免把 PS 的职责重复实现成大型 PL 比较网络。

### 6.4 四级验证

1. 软件 BF16/FP32 reference；
2. HLS C simulation：小尺寸结构用例 + 全尺寸 8-step；
3. C/RTL cosimulation：覆盖 H8、交错 accumulator 复用、两个 accumulator context、跨 burst/FIFO、连续多行和连续调用；
4. 单 IP 板测或 AXI VIP：HP2 路径、完整权重、production/debug、penalty、counter、timeout。

原有 4×4 cosim 不足以覆盖 H8/K16。建议 RTL 用例至少为 `H=896, V=64`，使两组 32-row tile、完整 hidden bank 和多次 accumulator 复用都被执行；全尺寸数值仍由 C sim 和板测承担。

### 6.5 数值报告

每个配置报告：

- max absolute / relative / mean absolute error；
- cosine similarity；
- NaN/Inf 数量；
- raw score Top-5 overlap；
- processed score Top-5 overlap；
- selected token/score；
- 最小 Top-1 margin 和所有 tie case；
- 标量 reference 与不同归约树的差异。

误差门槛必须针对 V2 BF16 reference 重新冻结，不能直接复制旧 FP16 `atol=0.02`。

### 6.6 性能测试矩阵

固定同一权重、hidden 和 bitstream，每项至少 30 次，报告 median/P95：

| 维度 | 取值 |
|---|---|
| mode | Prefill / Decode |
| penalty | OFF / ON |
| logits | OFF / ON |
| vocab | 128 / 1024 / 8192 / 65536 / 151936（小值只用于定位） |
| build | H8/V1、第二数值一致配置 |
| 环境 | 单 IP、完整系统 |

分别报告权重冷加载、首次调用和稳态调用。生产性能以权重已驻留、持久连接、`write_logits=0` 为准。

### 6.7 代码与交付产物改造矩阵

旧目录 `module16_lm_head_hls` 保留为 FP16 性能基线，不在 V2 验收前原地覆盖。M14 V2 建议建立独立模块目录 `module_14_lm_head_v2`，最终名称服从集成仓库统一规范。

| 产物 | V2 计划内容 | 主要验收点 |
|---|---|---|
| `include/lm_head_v2.hpp` | V2 顶层声明、常量、flags/status、`build_config` 位域 | 与统一 ABI 头文件无重复定义，地址和计数器均使用统一类型 |
| `include/bf16_utils.hpp` 或公共库引用 | BF16/FP32 转换、打包和解包 | 与 M01/M03/M04 共用实现和位级测试向量 |
| `src/lm_head_v2.cpp` | 128-bit AXI、hidden cache、权重 burst、H8 点积、交错累加、归约、penalty、argmax、可选 logits | C synthesis 达到目标 II；综合报告中乘加资源与配置一致 |
| `tb/lm_head_v2_tb.cpp` | 小词表 RTL 用例、完整词表 Csim、异常参数和 tie case | 覆盖 Prefill/Decode、penalty/logits 开关及状态码 |
| `reference/lm_head_v2_ref.py` | BF16 输入量化、FP32 计算、penalty、argmax、CRC | 作为唯一 golden 生成入口，记录模型和 tokenizer 版本 |
| `golden/` | 固定 8 步样本、小词表边界样本、manifest/SHA256 | 可复现并可追溯到 reference 版本 |
| `scripts/` | Csim、cosim、synthesis、IP export、报告提取 | 一条命令重跑；失败返回非零状态 |
| `drivers/` | V2 寄存器结构、job/result 提交、buffer 对齐检查、counter 读取 | 与 M03 调度和 40-bit 地址约束一致 |
| `reports/` | Csim/cosim、latency/II、资源、时序、板测和数值报告 | 每个配置带工具版本、时钟和 commit/SHA256 |
| `ip/` | 已验证的 H8/V1 基线 IP，必要时附第二配置 | 只交付通过 G3/G4 的配置 |
| `manifest.json`、`README.md`、`SHA256SUMS` | 参数、接口、依赖、生成方式、已知限制和全包校验 | 满足 0924 模块包结构和交接要求 |

旧工程中的测试数据不能直接当作 V2 golden：必须通过导出脚本把 hidden 和共享词表矩阵量化为 BF16，并记录新二进制的尺寸、布局、CRC/SHA256。旧工程继续承担“改造前 11.09 s”和旧 FP16 数值路径的回归对照。

---

## 7. 实施阶段、任务和退出条件

### G0：接口和数值冻结（2026-09-28～09-29）

任务：

- 与架构负责人确认第 2 章五项语义；
- 获取统一 enum、公共 BF16 库、公共头文件和寄存器生成源；
- 冻结 `valid_rows`、optional logits、CRC、flags、counter 定义；
- 保存旧源码/IP/bit/XSA/ELF/权重/报告 SHA256。

退出条件：形成签字/版本化接口表；未冻结项全部有负责人和截止日期。

### G1：BF16 V2 reference 与数据（2026-09-29～09-30）

任务：

- 导出共享 `VOCAB_VH_V2` BF16 权重；
- 建立 V2 scalar reference；
- 生成 8-step BF16 golden 和构造用例；
- 生成 manifest 与 SHA256；
- 确认 M05 Embedding 对同一权重文件的解释一致。

退出条件：软件 reference 可重复生成相同 hash；M05/M14 对随机词表行 bitwise 读取一致。

### G2：HLS core 实现与 C sim（2026-10-01～10-04）

任务：

- 实现128-bit BF16 unpack、8-bank hidden FP32 cache；
- 实现 H8、交错累加、ping-pong context、归约树；
- 实现 sequential history word、penalty、stream argmax；
- 实现 `write_logits` 门控；
- 加入 ABI/status/build/perf/CRC 寄存器；
- 跑小尺寸、错误路径和全尺寸 8-step C sim。

退出条件：功能用例通过；weight loop achieved II=1；HLS 报告无未解释的 missed burst/II violation；counter 在 C/RTL 模型中自洽。

### G3：RTL、综合和配置比较（2026-10-04～10-06）

任务：

- 完成 `H=896,V=64` C/RTL cosim；
- 综合 H8/V1 和第二配置；
- 比较 ACC_INTERLEAVE 8/16、FIFO 和 burst 起始组合；
- 检查 LUT/FF/BRAM/DSP、端口宽度、寄存器图和 100 MHz；
- 选择交付配置并写入 `build_config`。

退出条件：cosim 无死锁；100 MHz HLS 时序满足；两配置数值一致；资源报告可提交给 `resource_budget.csv`。

### G4：IP、驱动和单 IP 集成（2026-10-06～10-08）

任务：

- 导出 IP 和驱动；
- 生成完整寄存器说明；
- 在目标 BD/验证 BD 中确认 weight→HP2、128-bit、40-bit 地址和 reset；
- M02 probe 能读取 module id/ABI/capability/build/self-check；
- M03/M04 descriptor、cache、共享权重流程打通；
- 跑 AXI VIP 或板上完整权重测试。

退出条件：软件不依赖硬编码旧寄存器；IP 与 driver hash 匹配；production 模式无 logits 写；完整 token/score 正确。

### G5：交付包与评审（2026-10-09～10-10）

目标目录：

```text
module_14_lm_head_v2/
  src/
  include/
  tb/
  reference/
  golden/
  scripts/build_hls.tcl
  scripts/run_tests.*
  ip_repo/
  drivers/
  reports/hls/
  reports/implementation/
  reports/numeric/
  module_manifest.json
  README.md
  SHA256SUMS
```

退出条件：10 月 10 日交付清单逐项签收；已知限制明确；旧基线可恢复；没有用“待补文档”替代接口说明或资源报告。

### G6：完整系统集成（2026-10-11～10-23）

- M14 接入 HP2 分组；
- 与 Final RMS、Scheduler、M03/M04/M15 联调；
- 完整系统实现满足 WNS≥0、CLB<85%、BRAM<70%，无高严重度拥塞；
- 记录 HP2 APM、M14 counter、PS 时间和 cache bytes；
- 完成 prefill→LM Head→decode 至少一条端到端生成链路。

这一阶段优先保证功能和可测量性，不因为单 IP HLS 报告好看而突破全系统资源预算。

### G7：系统性能优化（2026-10-24～11-13）

依据测量按以下顺序调整：

1. burst/outstanding/FIFO；
2. history 和 logits 非生产流量；
3. reduction/accumulator bubble；
4. H_LANES=16/32 的聚合调度；
5. `VOCAB_PAR=2/4/8`；
6. 多 HP/权重分片；
7. 125/150/200 MHz；
8. 新 numeric implementation 或量化。

每一步只改变 build configuration/revision，不改变 ABI/layout；每一步都必须重新跑数值、实现和端到端测试。

---

## 8. 性能调优决策树

```text
完整调用仍慢
  │
  ├─ weight_wait_cycles 高、HP2 接近实测带宽上限
  │    ├─ burst/FIFO/outstanding 尚未调优 → 先调 AXI
  │    ├─ HP2 被其他模块竞争 → 调 Scheduler/端口时序或分配
  │    └─ 单 HP2 已饱和 → 再评估多 HP、量化；不要继续堆 DSP
  │
  ├─ dot_active_cycles 高、weight_wait 低
  │    ├─ II>1 → 修复累加/存储依赖
  │    ├─ reduction bubble 高 → 双 context/流水树
  │    └─ 资源允许 → 增 H_LANES 或 VOCAB_PAR
  │
  ├─ PL cycles 正常、PS RTT 高
  │    ├─ 重复 cache 操作 → 修正 owner/valid range
  │    ├─ debug logits/日志仍开启 → 关闭生产流量
  │    └─ 轮询/协议开销 → 中断或退避轮询、持久连接
  │
  └─ 数值错误
       ├─ BF16 unpack/RNE/端序
       ├─ reduction 顺序/tie-break
       ├─ history bit/penalty 正负规则
       └─ 新旧权重或 bitstream/driver 不匹配
```

### 8.1 何时增加 `H_LANES`

只有当 dot compute 明显高于权重等待，且资源/时序允许时，从 8 增至 16/32。单 HP2 平均每拍仍只有 8 个 BF16；H16/H32 需要先聚合 2/4 个 beat，不能把计算阵列峰值误当作持续 DDR 吞吐。

### 8.2 何时增加 `VOCAB_PAR`

只有在归约/控制导致权重口无法连续、或者增加独立权重带宽之后才考虑。单 HP2 已持续一拍一个 128-bit weight word 时，复制 vocab PE 不会降低必须扫描的 272269312 bytes。

### 8.3 何时提高频率

先完成 100 MHz 全系统 implementation。提高频率必须同时调整 HLS、PL 用户时钟、SmartConnect/clock converter/reset，并通过完整实现；不能把 PL DDR 200 MHz 参考输入、266.5 MHz MIG UI 时钟或 HLS Estimated period 当作 M14 已运行频率。

---

## 9. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| FP16 基线与 BF16 V2 语义混用 | token/误差报告失真 | 新建 V2 golden、manifest、numeric ID；旧数据只作参考 |
| optional logits/valid_rows 尚未冻结 | driver/IP 返工 | G0 冻结，公共生成源唯一化 |
| 归约顺序改变 Top-1 | 功能不一致 | 显式 reference、margin/tie 报告、固定归约树 |
| H8 计算快但 HP2 供数不足 | 性能达不到理论值 | 独立 HP2 顺序读基准、APM、weight_wait counter |
| 资源单 IP 可过、全系统拥塞 | 无法集成 | 以完整系统 resource_budget/WNS 为门槛；先降 tile/并行度 |
| DATAFLOW C sim 通过但 RTL 死锁 | IP 不可用 | 统计每级 token 数、设置有限 FIFO、强制 RTL cosim |
| Debug logits 常开 | HP2/网络流量污染 | 生产默认关；capability 和 counter 验证零写拍 |
| M05/M14 权重解释不同 | Embedding/LM Head 错误 | 共享 manifest，随机行 bitwise 联合测试 |
| driver、IP、bitstream 版本错配 | 上板结果不可追踪 | ABI/build/self-check、SHA256、任务记录绑定 |
| 200 MHz 过早推进 | 时序和复位返工 | 第一版只承诺 100 MHz；后续按完整系统实现决策 |

---

## 10. 交付检查表

### 接口

- [ ] ABI V2、module id、capability、build config 可读；
- [ ] `run_mode/valid_rows/job_id/flags` 齐全；
- [ ] 128-bit BF16 数据口和 HP2 连接记录齐全；
- [ ] `VOCAB_VH_V2` 与 M05 共享且 hash 一致；
- [ ] 地址、对齐、alias、dtype、layout、错误码明确；
- [ ] 寄存器偏移、复位值、读写属性完整。

### 功能与数值

- [ ] BF16 软件 reference 和 golden 可复现；
- [ ] penalty OFF/ON、logits OFF/ON 通过；
- [ ] tie、首尾 token、history 边界通过；
- [ ] Prefill/Decode 两模式通过；
- [ ] H8 与第二配置一致性报告完成；
- [ ] C sim、RTL cosim、板测/VIP 完成。

### 性能与实现

- [ ] weight loop II=1；
- [ ] `weight_read_beats_128=17016832`；
- [ ] production logits 写拍为 0；
- [ ] total/compute/wait/beat counter 与 job 对齐；
- [ ] 100 MHz implementation WNS≥0；
- [ ] LUT/FF/BRAM/DSP/拥塞提交全系统资源预算；
- [ ] 单 IP和完整系统 P50/P95 分开报告。

### 包和追溯

- [ ] 源码、IP、driver、XSA/bit/ELF（如适用）hash；
- [ ] module manifest、hardware profile 摘要；
- [ ] HLS/implementation/numeric 报告；
- [ ] 已知限制和回退步骤；
- [ ] README 能让汇总人无需阅读内部源码即可接入。

---

## 11. 完成判定

M14 只有同时满足以下条件才算完成，而不是“C 仿真 token 对了”即完成：

1. ABI V2、BF16、布局、共享权重和错误语义冻结；
2. 128-bit H8 optimized core 达到 II=1；
3. 软件/C sim/RTL/板测四级验证通过；
4. 性能计数能解释计算、等待和实际 AXI 流量；
5. 至少一个 100 MHz implementation 通过；
6. 完整系统资源和时序门槛通过；
7. Prefill/Decode 端到端生成链路使用同一个 M14 IP 成功；
8. 交付包、manifest、驱动、hash 和已知限制完整；
9. 后续修改 H lanes、vocab parallel、FIFO、burst、频率时不需要改变 ABI 或权重布局。

