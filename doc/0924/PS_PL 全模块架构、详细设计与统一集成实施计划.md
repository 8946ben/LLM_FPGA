# PS/PL 全模块架构、详细设计与统一集成实施计划

> 文档状态：总实施设计稿\
> 接口版本：ABI V2\
> 适用模型：当前工程中的 Qwen2.5 结构\
> 目标工程：`D:\FPGA_PRO\llme_SDWeight_proj`\
> 本文已整合原《PS\_PL全模块详细设计说明书》和《PS\_PL全模块架构设计与统一集成调试计划》，作为模块实现、整批集成、调试、性能优化和项目排期的唯一实施依据。\
> 本次未修改任何工程代码。

## 1. 文档目的

本文先说明现有报告的核查结论，再给每个 PS/PL 模块定义可直接实现的设计规格，最后规定所有模块完成后的统一集成、实际调试、性能验收和完成时间表，包括：

* 模块负责什么、不负责什么；
* 输入输出、控制参数和错误状态；
* 张量的数据类型、形状、存储顺序和地址要求；
* 算法执行步骤；
* 建议的 HLS 微架构；
* 需要预留的性能参数和统计项；
* 单模块验证与交付条件；
* 全部模块的整批交付与一次性集成；
* 汇总人的上板定位和性能调试流程；
* 按日历日期给出的项目完成计划。

设计重点是让后续性能优化只改变模块内部参数，尽量不改变外部接口。例如，把 QKV 并行度从 8 增加到 16，原则上只需要重新综合 QKV IP，不应修改 PS 调用参数、Q/K/V 布局或重新定义整套权重语义。

### 1.1 原分析报告核查结论

原报告关于“PS 串行调度、RoPE 多次启动、PS 转置、接口偏窄、LM Head 慢”的方向基本正确，但实施前必须补充以下事实。

#### 结论一：当前最大浪费不只是接口窄，还有无效计算

Decode 每次只有 1 个新 token，但当前 SwiGLU 固定按 36 行执行，RMSNorm 也存在固定行数路径。PS 即使把其余行补零，PL 仍然完成无效计算。新设计因此要求所有 token 维模块使用 `valid_rows` 直接控制循环、DDR 访问和写回范围。

#### 结论二：重复 cache clean 很可能是板级耗时异常的重要来源

权重从 SD 加载后不再被 CPU 修改，本应只 clean 一次。当前 QKV、Attention Out、SwiGLU 等 wrapper 每次调用仍可能清理整块权重。三者合计约 29.8 MiB/层，24 层一次完整步骤约 715 MiB 的重复 cache 操作。新设计把 cache 所有权集中到 M03 管理，模块 wrapper 不再自行清理完整 buffer。

#### 结论三：不能先简单增加大量并行单元

当前实现约使用 97.4% CLB、83.5% BRAM，而 DSP 约 22.7%。限制系统的不是 DSP 数量，而是布局空间、BRAM 和布线。Attention 和 SwiGLU 必须先改成 tile 结构，释放完整 K/V、attention weight 和 MLP 中间数组，再提高 PAR。

#### 结论四：实际不是所有 IP 都挤在 HP3

当前工程已经使用 HP0～HP3：HP0 连接 RMS/RoPE/Attention/Embedding 等，HP1 连接 KV Update 的 PS DDR 侧，HP2 连接 LM Head，HP3 连接 QKV/AttnOut/Residual/SwiGLU；KV Cache 使用 PL DDR。第一版保持该分组，只有 AXI 计数器证明端口拥堵后才重新分配。

#### 结论五：PS HP 的 128 bit 在 PS IP 中确定

`system_wrapper.bd` 中 `PSU__SAXIGP2__DATA_WIDTH` 到 `PSU__SAXIGP5__DATA_WIDTH` 均为 128，分别对应 `S_AXI_HP0_FPD` 到 `S_AXI_HP3_FPD`。HLS IP 的 32/512 bit M\_AXI 是另一层接口，SmartConnect 会在 IP 端宽度和 HP 端 128 bit 之间转换。因此扩大 HLS 端口可能改善 burst 和内部并行，但不能把 PS DDR 物理出口变成 512 bit。

#### 结论六：必须先冻结可追溯版本

现有 bitstream、XSA、ELF、HLS 报告和源码的生成时间不完全一致，HLS 源码仓库还存在未提交或未跟踪内容。任何优化前都必须记录源码 commit/dirty patch，以及 bit、XSA、ELF、component.xml 和权重文件 SHA256。

### 1.2 本次统一设计的范围

本设计覆盖控制面、数据面和验证面，不只覆盖耗时最大的模块：

* 控制面：Host/TCP、Scheduler、Runtime、IP Registry、Driver；
* 内存面：Buffer Manager、cache 所有权、SD Weight Store、manifest；
* 数据面：Embedding、三类 RMSNorm、QKV、RoPE、KV Cache、GQA Attention、AttnOut、两处 Residual、SwiGLU、LM Head；
* 验证面：软件 reference、golden、CRC、snapshot、性能计数和发布 manifest。

旧 GQA Repeat、Attention Value、独立 SiLU、通用 Linear/MLP 和格式转换模块的生产职责已经明确合并或取消，不会在集成时出现“是否还要连接”的歧义。

## 2. 面向后续性能优化的设计原则

### 2.1 稳定项与可调项分离

以下内容一旦冻结，ABI V2 生命周期内不允许随性能优化改变：

* 模块功能和数学公式；
* 参数含义、状态码和完成语义；
* 激活数据布局；
* KV Cache 布局；
* 权重文件的规范布局；
* BF16/FP32 数值边界；
* 输入输出 buffer 的有效范围计算方式。

以下内容允许在不改变 ABI 的情况下调整：

* MAC 并行度；
* token、hidden、intermediate、KV tile 大小；
* BRAM/URAM/FIFO 深度；
* dataflow stage 数量；
* 双缓冲开关；
* AXI outstanding、burst 和内部预取深度；
* exp、rsqrt、SiLU 的实现版本，但必须满足规定误差；
* 模块目标频率。

### 2.2 外部固定 128 bit，内部并行度可扩展

当前 PS HP 的 AXI 数据拍宽度为 128 bit（不是板上 PS DDR 芯片的物理 DQ 宽度）。ABI V2 的 PS DDR 数据接口统一使用 `ap_uint<128>`，每拍包含 8 个 BF16。

模块内部可以把连续 2 拍或 4 拍聚合成 16/32 个 BF16 并行处理。这样未来增加并行度时：

* 不改变 AXI 物理连接；
* 不改变 PS buffer 地址；
* 不需要新增 width converter；
* 不需要仅为了改变并行度重新定义权重文件。

PL DDR 的 KV 端口使用 MIG 原生用户接口宽度，由单独的 `KV_AXI_BITS` 构建参数控制，不影响逻辑布局。

### 2.3 权重采用固定 32 元素物理分组

所有投影类权重采用 32 个 BF16、共 64 byte 的规范物理分组。64 byte 同时满足 cache line 和 DMA/AXI 对齐要求。

对于按输出通道并行的权重：

```text
W_PACKED[output_group32][input_index][lane32]
output_channel = output_group32 × 32 + lane32
```

模块内部并行度可以选择 8、16 或 32：

* PAR=8：每次读取分组中的一个 128-bit 子块；
* PAR=16：每次组合两个子块；
* PAR=32：每次组合四个子块。

物理文件仍是同一个 32-lane 布局。性能调优不需要为 8/16/32 分别维护三套语义不同的权重。

Embedding/LM Head 共享权重保持词表行主序：

```text
E[vocab][hidden_group32][lane32]
```

### 2.4 所有长度都使用有效值

每个支持 token 维度的模块必须接收 `valid_rows`，范围 1～64。循环终止条件必须是 `valid_rows`，不得通过给剩余行补零继续计算最大行数。

同理：

* Attention 使用实际 `cache_len`；
* KV Update 使用实际 `start_pos` 和 `valid_rows`；
* LM Head 使用实际 `vocab_size`，但当前模型需等于 151936；
* Debug snapshot 使用实际 offset/length。

### 2.5 生产数据与调试数据分离

生产 IP 不提供大规模中间张量输出。调试使用：

* 输出 CRC；
* 小范围 snapshot；
* 独立 Debug build；
* 阶段性能计数器。

避免为了调试永久增加大 AXI 写口和 BRAM。

### 2.6 优化必须可测量

每个计算 IP至少输出：

* `perf_cycles_total`；
* `perf_cycles_compute`；
* `perf_read_beats`；
* `perf_write_beats`；
* `processed_rows`。

AXI stall 和系统端口利用率由 Vivado AXI Performance Monitor 统计。模块局部计数器和系统计数器必须使用同一次 job id 对齐。

## 3. 全局模型常量

```text
NUM_LAYERS       = 24
HIDDEN_SIZE      = 896
NUM_Q_HEADS      = 14
NUM_KV_HEADS     = 2
GQA_GROUP_SIZE   = 7
HEAD_DIM         = 64
INTERMEDIATE     = 4864
VOCAB_SIZE       = 151936
MAX_SEQUENCE     = 2048
MAX_BLOCK_ROWS   = 64
EXTERNAL_LANES   = 8 BF16 / 128-bit beat
WEIGHT_GROUP     = 32 BF16 / 64-byte group
```

所有常量同时写入：

* 公共 C/C++ 头文件；
* 权重 manifest；
* PS model config；
* HLS testbench config。

不允许四处分别手写数值。

## 4. 公共类型和数据布局

### 4.1 数值类型

| **名称**   | **存储** | **用途**                 |
| -------- | ------ | ---------------------- |
| `bf16_t` | 16 bit | 外部激活、权重、bias、RoPE 表    |
| `fp32_t` | 32 bit | 点积、归约、softmax、MLP 内部累加 |
| `u32`    | 32 bit | token、状态、维度、标志         |
| `u64`    | 64 bit | 物理地址、cycle counter     |

BF16 转换统一使用 round-to-nearest-even。NaN、Inf、溢出和 underflow 行为由公共数值库定义，模块不得各写一份不同的转换函数。

### 4.2 张量布局

| **Layout ID**     | **含义**                    | **线性索引**                 |
| ----------------- | ------------------------- | ------------------------ |
| `ACT_TH_V2`       | `[T][H]` hidden/residual  | `t×H+h`                  |
| `Q_HTD_V2`        | `[QH][T][D]`              | `(qh×T+t)×D+d`           |
| `KV_HTD_V2`       | `[KVH][T][D]`             | `(kh×T+t)×D+d`           |
| `KVC_LHSD_V2`     | `[L][KVH][S][D]`          | `(((l×KVH+kh)×S+s)×D+d)` |
| `ROPE_SD_V2`      | `[S][D]`                  | `s×D+d`                  |
| `W_OG32_I_L32_V2` | `[ceil(O/32)][I][32]`     | `(og×I+i)×32+lane`       |
| `VOCAB_VH_V2`     | `[V][H]`，每 32 个 hidden 对齐 | `v×H+h`                  |

所有行长度恰好为 64 byte 的整数倍：

* H=896 BF16 = 1792 byte = 28×64 byte；
* D=64 BF16 = 128 byte = 2×64 byte。

因此每一 token row/head row 天然满足 64-byte 对齐，便于长 burst 和 cache range 管理。

### 4.3 公共 job 参数

每个 HLS IP 必须具备：

```c
struct common_job_v2 {
    uint32_t abi_version;       // 必须等于 2
    uint32_t job_id;
    uint32_t run_mode;          // 0=PREFILL，1=DECODE
    uint32_t valid_rows;        // 1..64，不适用时定义等价长度
    uint32_t flags;
};

struct common_result_v2 {
    uint32_t status_code;
    uint32_t processed_rows;
    uint64_t perf_cycles_total;
    uint64_t perf_cycles_compute;
    uint64_t perf_read_beats;
    uint64_t perf_write_beats;
    uint32_t output_crc;
    uint32_t build_config;
};
```

HLS 顶层不一定直接使用 C struct 作为寄存器接口，但生成驱动必须提供等价字段。

`run_mode` 是所有推理计算模块的统一保留字段。当前模块即使 Prefill 和 Decode 使用同一套算法，也必须保留并检查该字段，这样以后可以在不修改 PS 参数结构的情况下增加双模式调度或拆分为两个物理 IP。

统一规则：

* `run_mode=0`：Prefill；通常 `valid_rows=1～64`；
* `run_mode=1`：Decode；所有 token 维计算模块要求 `valid_rows=1`；
* 一个物理 IP 支持双模式时，由该字段选择内部调度；
* 拆成 Prefill/Decode 两个 IP 时，两者保留同一字段和寄存器结构，各自只接受对应模式；
* M04 权重加载、M03 内存管理等非推理计算模块不需要增加 `run_mode`。

### 4.4 `build_config` 编码

为了让后续性能版本可追踪，每个 IP 的只读 `build_config` 至少编码：

```text
bits  0..3   PAR_LANES code: 8/16/32
bits  4..9   ROW_TILE
bits 10..17  MAIN_TILE
bits 18..21  numeric implementation id
bits 22..27  target clock code
bits 28..31  module-specific revision
```

同一 ABI 可以存在多个性能配置，但必须能从寄存器和 manifest 中识别。

### 4.5 公共状态码

```text
0  OK
1  BAD_ABI
2  BAD_DIMENSION
3  BAD_ALIGNMENT
4  BAD_ADDRESS_RANGE
5  BAD_LAYOUT
6  BAD_LAYER
7  BAD_TOKEN
8  BAD_ALIAS
9  NUMERIC_ERROR
10 DRIVER_TIMEOUT
11 BAD_FLAGS
12 INTERNAL_ERROR
```

## 5. 顶层运行数据流

```text
Token IDs
  │
  ▼
M05 Embedding ───────────────────────────────────────────────┐
  │ hidden                                                  │
  ▼                                                         │
每个 Transformer Layer：                                   │
  ├─保存 residual0                                          │
  ├─M06 RMSNorm(input)                                      │
  ├─M07 QKV Projection                                      │
  ├─M08 RoPE                                                │
  ├─M09 KV Cache Update ───────────────► PL DDR KV Cache    │
  ├─M10 GQA Attention ◄──────────────── PL DDR KV Cache     │
  ├─M11 Attention Out                                       │
  ├─M12 Residual Add(residual0)                             │
  ├─保存 residual1                                          │
  ├─M06 RMSNorm(post)                                       │
  ├─M13 SwiGLU                                              │
  └─M12 Residual Add(residual1)                             │
  │                                                         │
  ▼                                                         │
M06 Final RMS                                               │
  │                                                         │
  ▼                                                         │
M14 LM Head / Argmax ──► Next Token ────────────────────────┘
```

M05～M14 之间的数据都通过 buffer descriptor 连接，PS 不改变数据内容或排列。

## 6. M00 Host/TCP Protocol 模块

### 6.1 职责边界

负责：命令解析、输入校验、job 创建、结果返回、build/perf 查询。

不负责：直接配置 IP、执行 tensor 转换、操作 KV Cache。

### 6.2 对外命令

```text
HELLO(protocol_version)
LOAD_MODEL(manifest_id)
CREATE_SESSION(session_id)
RUN_PREFILL(session_id, token_count, token_ids[])
RUN_DECODE(session_id, max_new_tokens, sampling_config)
GET_STATUS(job_id)
GET_PERF(job_id)
ABORT(job_id)
RESET_SESSION(session_id)
GET_BUILD_INFO()
```

每个包包含：magic、protocol version、command、payload length、sequence id、CRC32。

### 6.3 内部算法

1. 接收完整 header；
2. 检查 magic/version/length；
3. 接收 payload 并检查 CRC；
4. 做不涉及硬件的范围校验；
5. 转换为 M01 job；
6. 立即返回 accepted/job\_id 或明确错误；
7. 由状态接口返回最终 token 和性能数据。

### 6.4 性能设计

* 模块运行期间不逐条打印；
* token 数组一次复制到预分配命令 buffer；
* perf 数据采用环形 buffer；
* 网络发送与 PL 计算可以异步，但不得修改当前 job 的 buffer；
* 后续改用 DMA/更高速协议时，不改变 M01 job 格式。

### 6.5 验证

覆盖坏 CRC、短包、超长 token、重复序号、断线、并发 session 冲突和 abort。

## 7. M01 Scheduler/Runtime 模块

### 7.1 职责边界

负责：将一次模型请求转换为模块调用序列，维护 layer、position、cache length 和 buffer generation。

不负责：模块内部数学、权重物理排列、wrapper 内 cache 猜测。

### 7.2 Job 描述符

```c
struct inference_job_v2 {
    uint32_t job_id;
    uint32_t session_id;
    uint32_t mode;              // PREFILL / DECODE
    uint32_t token_count;
    uint32_t start_position;
    uint32_t max_new_tokens;
    uint32_t model_handle;
    uint32_t debug_flags;
};
```

### 7.3 Prefill 算法

1. 把输入按最多 64 token 分 block；
2. M05 查 Embedding；
3. 对 24 层执行固定全链路；
4. 每层 M09 把本 block K/V 写到 `start_position`；
5. M10 使用 `cache_len=start_position+valid_rows`；
6. 每个 block 完成后更新 start position；
7. 最后一个 block 的最后一行进入 Final RMS 和 LM Head。

### 7.4 Decode 算法

每轮只有一个新 token：

1. `valid_rows=1`；
2. 使用当前 `cache_len` 作为 position；
3. 运行 24 层完整链路；
4. Final RMS + LM Head；
5. 把 selected token 加入 history；
6. `cache_len++`；
7. 达到 EOS、最大 token 或错误时停止。

### 7.5 Buffer 调度

使用 hidden ping/pong：

```text
layer_input  = hidden_ping
add1_output  = hidden_pong
layer_output = hidden_ping 或下一空闲 buffer
```

实际映射由 buffer planner 生成，必须满足禁止 alias 的模块规则。Q/K/V、RoPE、Attention buffer 为固定工作区，在层之间复用，但 generation 必须更新。

### 7.6 性能优化接口

Scheduler 预留但初始关闭：

* `prepare_next_layer`：当前 IP 运行时预取下一层描述符；
* 中断完成通知；
* 多 block prefill 的命令流水；
* 模块融合 capability 检测。

即使以后把 QKV+RoPE 融合，Scheduler 通过 capability 表选择调用路径，不改变模型状态机定义。

### 7.7 验证

覆盖 T=1/36/64/65、24 层、position 2047、模块超时、错误注入、abort 和 session reset。

## 8. M02 IP Registry/Driver 模块

### 8.1 注册表

```c
struct ip_entry_v2 {
    uint16_t module_id;
    uint16_t instance_id;
    uint32_t expected_abi;
    uint64_t ctrl_base;
    uint32_t irq_id;
    uint32_t timeout_class;
    uint32_t capabilities;
    const ip_ops_v2 *ops;
};
```

### 8.2 驱动操作

```text
probe → self_check → configure → start → wait → read_result → reset
```

`configure` 只设置寄存器，不做 cache 操作；cache 由 M03 在调用前统一完成。

### 8.3 Capability 位

```text
DYNAMIC_ROWS
DEBUG_CRC
DEBUG_SNAPSHOT
IRQ_COMPLETE
INPLACE_ALLOWED
ONLINE_SOFTMAX
PL_DDR_DIRECT
WRITE_LOGITS_OPTIONAL
```

### 8.4 性能设计

* 地址未变化时不重复写高 32 bit；
* Release 关闭寄存器逐项打印；
* 轮询采用递增 backoff 或中断，不能高速死循环刷总线；
* 保存每模块最近一次寄存器快照用于故障，不在成功路径打印。

## 9. M03 Memory/Buffer Manager 模块

### 9.1 Buffer 描述符

```c
struct buffer_desc_v2 {
    uint64_t phys_addr;
    uint32_t capacity_bytes;
    uint32_t valid_offset;
    uint32_t valid_bytes;
    uint16_t layout_id;
    uint8_t dtype;
    uint8_t owner;
    uint32_t generation;
    uint32_t flags;
};
```

owner：`CPU_CLEAN`、`CPU_DIRTY`、`PL_READABLE`、`PL_WRITTEN`、`IMMUTABLE`。

### 9.2 有效字节公式

```text
ACT_TH       = T × 896 × 2
Q_HTD        = 14 × T × 64 × 2
KV_HTD       = 2 × T × 64 × 2
KV_UPDATE    = 2(K+V) × 2 heads × T × 64 × 2
ATTENTION    = T × 896 × 2
```

### 9.3 所有权算法

* CPU 写、PL 读：clean 对齐后的有效范围；
* PL 写、CPU 读：invalidate 有效范围；
* PL 写、PL 读：只做依赖同步，不做 cache 操作；
* immutable 权重：装载后 clean 一次；
* 每次 PL 写后 generation++，消费者记录期望 generation。

### 9.4 性能设计

* range 操作按 cache line 对齐；
* 多段有效区间使用 scatter list，例如 head-major KV；
* 统计每次 clean/invalidate 字节；
* Debug canary 与生产 buffer 分开构建；
* 后续引入 DMA 或 coherent port 时只替换 owner transition backend。

## 10. M04 SD Weight Store/Manifest 模块

### 10.1 Manifest

```json
{
  "format_version": 2,
  "abi_version": 2,
  "model": {
    "layers": 24,
    "hidden": 896,
    "q_heads": 14,
    "kv_heads": 2,
    "head_dim": 64,
    "intermediate": 4864,
    "vocab": 151936
  },
  "files": [
    {
      "name": "layer00_qkv_w.bin",
      "dtype": "bf16",
      "layout": "W_OG32_I_L32_V2",
      "bytes": 0,
      "sha256": "..."
    }
  ]
}
```

实际 manifest 中 `bytes` 必须是准确非零值。

### 10.2 加载算法

1. 验证 manifest 和模型常量；
2. 预检查所有目标地址和容量；
3. 加载全部文件；
4. 边加载边计算 SHA256；
5. 全部成功后统一 clean；
6. 标记 immutable；
7. 发布 model handle。

采用“两阶段提交”：任何文件失败，model handle 都不变为 READY。

### 10.3 性能设计

* SD 读取使用大块顺序 I/O；
* 文件按层连续排列，减少 seek；
* 允许将多个小 bias/norm 合并为 metadata pack；
* 加载性能与推理性能分开统计；
* 未来迁移权重到 PL DDR 时保持 weight descriptor API 不变。

## 11. M05 Token Embedding IP

### 11.1 功能

根据 token id，从共享 Embedding/LM Head 权重表中取出一行 896 维 BF16，输出 `[T,896]`。

### 11.2 HLS 逻辑接口

```c
void embedding_v2(
    const uint32_t *token_ids,        // [T]
    const ap_uint<128> *table,        // VOCAB_VH_V2
    ap_uint<128> *hidden_out,         // ACT_TH_V2
    uint32_t run_mode,
    uint32_t valid_rows,
    uint32_t hidden_size,
    uint32_t vocab_size,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    common_result_v2 *result);
```

逻辑上 `result` 是 AXI-Lite 输出寄存器集合，不要求通过 DDR 写 struct。

### 11.3 AXI bundle

* `m_axi_ids`：PS DDR，32 bit token id；
* `m_axi_weight`：HP0，128 bit；
* `m_axi_out`：HP0，128 bit；
* `s_axilite_ctrl`：控制。

### 11.4 算法

```text
for t in [0, valid_rows):
    id = token_ids[t]
    if id >= vocab_size: BAD_TOKEN
    src = table + id × (896/8)
    dst = output + t × (896/8)
    burst copy 112 beats
```

### 11.5 微架构

* 读写采用 DATAFLOW：ID 校验、权重读取、输出写入三级；
* 一次 token 行为一个 burst 或少量最大 burst；
* 双 FIFO 解耦读写；
* 不缓存整个词表；
* token 相同也按语义读取，后续可选 1 行 cache，但不改变接口。

### 11.6 性能模型

每 token：读取 1792 byte，写 1792 byte，另读 4 byte id。理论下界主要由内存带宽决定。

### 11.7 可调参数

| **参数**        | **初值** | **后续方向**        |
| ------------- | ------ | --------------- |
| `BURST_BEATS` | 64     | 32/64/112 对比    |
| FIFO depth    | 64     | 根据 AXI stall 调整 |
| row cache     | 关闭     | 重复 token 场景评估   |

### 11.8 验证

id=0、V-1、重复 id、非法 id、T=1/64；输出必须与权重行逐 bit 相等。

## 12. M06 Dynamic RMSNorm IP

### 12.1 数学定义

```text
mean_square = sum(x[h]²) / H
inv_rms     = 1 / sqrt(mean_square + eps)
y[h]        = BF16_RNE(x[h] × inv_rms × weight[h])
```

同一实例用于每层 input norm、post norm 和最终 final norm。

### 12.2 HLS 逻辑接口

```c
void rmsnorm_v2(
    const ap_uint<128> *x,
    const ap_uint<128> *weight,
    ap_uint<128> *y,
    uint32_t run_mode,
    uint32_t valid_rows,
    uint32_t hidden_size,
    float eps,
    uint32_t norm_role,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    common_result_v2 *result);
```

### 12.3 AXI bundle

* `m_axi_x`、`m_axi_weight`、`m_axi_y`：HP0，独立 master bundle；
* 控制：AXI-Lite。

### 12.4 微架构

每个 token：

1. 读取 896 BF16 到 `row_buf[896]`；
2. 8-lane 转 FP32 并用 reduction tree 累加平方；
3. 计算 rsqrt；
4. 第二遍读取 row\_buf，乘 weight 和 inv\_rms；
5. 8-lane 转 BF16 写出。

weight 可在一次调用开始时缓存 896 项，供所有 token 复用。Decode T=1 时也只执行一行。

### 12.5 性能模型

若 weight 每次调用只读一次：

```text
read bytes  = 2×T×H + 2×H
write bytes = 2×T×H
```

瓶颈可能在 FP32 reduction/rsqrt，而不是 DDR。

### 12.6 可调参数

* `LANES=8/16/32`；
* reduction tree 分级；
* rsqrt：HLS math、Newton-Raphson、LUT+迭代；
* token row 双缓冲；
* weight BRAM/URAM 映射。

任何 rsqrt 替换都必须给出全输入范围误差报告。

### 12.7 验证

零向量、常数向量、极大/极小值、随机 BF16、T=1/36/64、不同 eps；检查 NaN 和逐层误差。

## 13. M07 QKV Projection IP

### 13.1 数学定义

```text
Q = X × Wqᵀ + bq     [T,896]
K = X × Wkᵀ + bk     [T,128]
V = X × Wvᵀ + bv     [T,128]
```

V2 把三组权重逻辑合并为 `O_TOTAL=1152` 的一个输出空间，复用同一 X。

### 13.2 HLS 逻辑接口

```c
void qkv_projection_v2(
    const ap_uint<128> *x,             // ACT_TH_V2
    const ap_uint<128> *w_qkv,         // W_OG32_I_L32_V2, O=1152
    const ap_uint<128> *bias_qkv,
    ap_uint<128> *q_raw,               // Q_HTD_V2
    ap_uint<128> *k_raw,               // KV_HTD_V2
    ap_uint<128> *v_out,               // KV_HTD_V2
    uint32_t run_mode,
    uint32_t valid_rows,
    uint32_t hidden_size,
    uint32_t layout_id,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    common_result_v2 *result);
```

### 13.3 权重映射

Q、K、V 合并输出顺序：

```text
0 .. 895      Q
896 .. 1023   K
1024 .. 1151  V
```

存储：`w_qkv[36 output groups][896 inputs][32 lanes]`，Layout ID 为 `W_OG32_I_L32_V2`。

### 13.4 AXI bundle

* `m_axi_x`：HP3，128 bit；
* `m_axi_weight`：HP3，128 bit；
* `m_axi_q`、`m_axi_k`、`m_axi_v`：HP3，独立输出 master；
* 控制：AXI-Lite。

虽然最终接入同一个 SmartConnect，独立 bundle 便于 HLS 重叠读取和写回。

### 13.5 算法和微架构

建议以 token row 为一级 tile：

1. 把一个或多个 X row 读入片上 `x_tile`；
2. 对 output group 初始化 32 个 FP32 accumulator；
3. 遍历 H=896，读取一个 x 和对应权重 group；
4. 根据 `PAR_OUT` 每周期更新 8/16/32 个输出；
5. 加 bias；
6. 输出编号映射到 Q/K/V 的 head、token、D 地址；
7. 直接写 head-major，不生成 token-major 临时结果。

优化版本可使用两级 dataflow：

```text
load_x / load_weight → MAC engine → bias/convert/address-map → write Q/K/V
```

### 13.6 性能模型

每层调用权重约：

```text
896 × 1152 × 2 = 2,064,384 byte
```

主要瓶颈可能是权重带宽和 MAC。输入 X 应在片上复用，不能为 Q、K、V 分别从 DDR 读取三次。

### 13.7 可调参数

| **参数**               | **初值** | **允许范围**  |
| -------------------- | ------ | --------- |
| `ROW_TILE`           | 1      | 1/2/4     |
| `PAR_OUT`            | 8      | 8/16/32   |
| `H_TILE`             | 64     | 32/64/128 |
| weight prefetch FIFO | 64     | 32～256    |
| double buffer        | 开      | 开/关       |

参数变化不改变 `W_OG32_I_L32_V2` 文件。

### 13.8 性能计数

除公共计数外增加：`x_reuse_count`、`weight_wait_cycles`、`mac_active_cycles`。

### 13.9 验证

* Q/K/V 分别比对；
* 输出边界 895/896/1023/1024；
* T=1/64；
* PAR=8/16/32 结果一致；
* 确认未读 padding，未发生 PS 转置。

## 14. M08 Block RoPE IP

### 14.1 数学定义

Qwen rotate-half：将 head\_dim 分成前后两半，`rot(x)=(-x₂,x₁)`：

```text
y = x × cos(position) + rot(x) × sin(position)
```

分别作用于 Q 和 K，V 不处理。

### 14.2 HLS 逻辑接口

```c
void rope_v2(
    const ap_uint<128> *q_raw,
    const ap_uint<128> *k_raw,
    const ap_uint<128> *cos_table,
    const ap_uint<128> *sin_table,
    ap_uint<128> *q_rot,
    ap_uint<128> *k_rot,
    uint32_t run_mode,
    uint32_t valid_rows,
    uint32_t position_base,
    uint32_t max_position,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    common_result_v2 *result);
```

### 14.3 AXI bundle

* Q/K 输入、cos/sin、Q/K 输出各为逻辑独立 bundle，映射 HP0；
* 所有数据 128 bit；
* 可在 Vivado 中根据端口数合并 SmartConnect，但 HLS 代码保留访问并行性。

### 14.4 微架构

1. 为一个 position 读取 64 维 cos/sin；
2. 缓存该 position 的 cos/sin；
3. 依次处理 14 个 Q head 和 2 个 K head；
4. 每次处理 8 个 BF16；
5. 需要前后半向量时，用两个 32-element 小 buffer 或配对读取；
6. 一次调用覆盖整个 block。

### 14.5 性能模型

总元素：`(QH+KVH)×T×D = 1024T`。算法计算量不大，性能应主要取决于 AXI 和启动次数。

### 14.6 可调参数

* `HEAD_PAR=1/2/4`；
* `D_LANES=8/16`；
* cos/sin 缓存方式；
* Q/K read-write dataflow；
* 后续允许与 QKV 写出级融合，但保留独立 ABI capability。

### 14.7 验证

position 0/35/63/64/2047，T=1/36/64；Q/K 分别比对；每个 block 只允许一次启动。

## 15. M09 KV Cache Update IP

### 15.1 HLS 逻辑接口

```c
void kv_cache_update_v2(
    const ap_uint<128> *k_new,
    const ap_uint<128> *v_new,
    kv_axi_t *k_cache,
    kv_axi_t *v_cache,
    uint32_t run_mode,
    uint32_t layer_id,
    uint32_t start_pos,
    uint32_t valid_rows,
    uint32_t max_sequence,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    uint32_t *cache_len_after,
    common_result_v2 *result);
```

`kv_axi_t` 宽度由 PL DDR MIG 决定，逻辑元素仍为 BF16。当前目标工程的 PL DDR 物理 DQ 是 32 bit、MIG AXI 用户口是 128 bit，因此当前实现应使用 `ap_uint<128>`；这两个宽度必须在 `hardware_profile_v2` 中分开记录。

### 15.2 地址公式

```text
dst(l, kh, s, d) = (((l×2 + kh)×2048 + s)×64 + d)
s = start_pos + t
```

K/V 使用互不重叠的 PL DDR 区域。

### 15.3 微架构

* 输入端将 128-bit QKV 输出数据聚合为 PL DDR beat；
* 每个 head/token 的 64 维为连续 128-byte 写；
* K 和 V 使用独立写通道/队列；
* 不做 GQA 复制；
* 不清零未更新位置；
* 写完成后再更新 `cache_len_after`。

### 15.4 性能模型

K+V 总写入：

```text
2 tensors × 2 heads × T × 64 × 2 byte = 512T byte
```

数据量很小，目标是减少启动、聚合和固定 staging 开销。

### 15.5 可调参数

* 输入聚合 FIFO 深度；
* K/V 并行写；
* PL DDR burst length；
* 后续 QKV/RoPE 直连 stream capability。

### 15.6 验证

所有 layer 边界、position 0/2047、T=1/64、跨 64 边界；检查未更新区不改变。

## 16. M10 GQA Online-Softmax Attention IP

### 16.1 功能和边界

负责：GQA head 映射、QK 点积、scale、causal mask、softmax 和乘 V。

不负责：RoPE、KV 写入、Attention Out Projection、输出完整注意力权重。

### 16.2 HLS 逻辑接口

```c
void attention_v2(
    const ap_uint<128> *q_rot,    // Q_HTD_V2
    const kv_axi_t *k_cache,      // KVC_LHSD_V2
    const kv_axi_t *v_cache,
    ap_uint<128> *attn_out,       // ACT_TH_V2
    uint32_t run_mode,            // 0=PREFILL, 1=DECODE
    uint32_t layer_id,
    uint32_t query_pos_base,
    uint32_t valid_rows,
    uint32_t cache_len,
    float scale,
    uint32_t causal,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    common_result_v2 *result);
```

`k_cache/v_cache` 的外部 beat 按 `hardware_profile_v2.pl_ddr_axi_bits` 生成。当前工程为 128 bit；不能因为开发板手册写的是 PL DDR 32 bit 就把 Attention 的 AXI 用户接口改成 32 bit。

### 16.3 GQA 映射

```text
kv_head = q_head / 7
q_head 0..6   → kv_head 0
q_head 7..13  → kv_head 1
```

K/V 只存两份。硬件读取一个 KV tile 后，复用于对应的 7 个 Q head。

### 16.4 Causal 条件

query token `t` 的绝对位置为：

```text
qpos = query_pos_base + t
```

只允许 `key_pos <= qpos`。被 mask 的 score 不进入 tile max、指数和或输出累加。

### 16.5 Online-softmax 公式

对一个 query/head 保存：

```text
m = -INF
l = 0
o[0..63] = 0
```

对每个 KV tile 计算有效 score。设 tile max 为 `mt`，更新：

```text
m_new = max(m, mt)
alpha = exp(m - m_new)
beta_j = exp(score_j - m_new)
l_new = alpha × l + Σ beta_j
o_new[d] = alpha × o[d] + Σ beta_j × V[j,d]
```

结束后：

```text
output[d] = o[d] / l
```

全部 `m/l/o` 使用 FP32。

### 16.6 微架构

建议初始参数：

```text
KV_TILE=64
Q_ROW_TILE=1
Q_HEAD_PAR=1 或 2
D_LANES=8
EXP_UNITS=1 或 2
```

流水阶段：

```text
load Q
  → double-buffer load K tile
  → QK dot + mask
  → tile max / exp / sum
  → double-buffer load V tile
  → weighted V accumulation
  → normalize / reorder to [T,H]
  → write output
```

K/V tile buffer在对应 7 个 Q head 之间复用。不能为每个 q head 重新从 PL DDR 读取相同 K/V。

### 16.7 资源设计

禁止片上数组：

* 完整 `K[2048][64]`；
* 完整 `V[2048][64]`；
* 完整 `weights[64][2048]`。

只允许 KV tile、少量 query、FP32 online state 和 FIFO。资源优化优先级高于第一版的极限并行度。

### 16.8 性能模型

主要计算量与 `QH×T×cache_len×D` 成正比。利用 GQA tile 复用后，PL DDR K/V 读取不应按 14 个 q head 完整重复。

理论字节和计算利用率必须按实际 cache\_len 统计，不能只报告最大 2048。

### 16.9 可调参数

* `KV_TILE=32/64/128`；
* `Q_HEAD_PAR=1/2/7`；
* `D_LANES=8/16`；
* exp 单元数量和实现；
* K/V 双缓冲；
* query row tile；
* PL DDR outstanding。

这些参数不改变输入输出布局。

### 16.10 性能计数

增加：

* `kv_tiles_loaded`；
* `kv_reuse_count`；
* `masked_scores`；
* `exp_active_cycles`；
* `pl_ddr_wait_cycles`。

### 16.11 验证

cache\_len=1/36/64/65/127/128/129/2048；Prefill 与 Decode；全负分数；tile 边界；在线结果与非分块 FP32 reference 比对。

### 16.12 Prefill/Decode 双模式设计

当前 `qwen25_attn_bf16` 同时完成 QK、softmax 和乘 V，因此不建议只把 softmax 单独拆出来，否则需要重新保存和读取完整 score 矩阵。双版本应以整个 M10 Attention 为边界：

| **模式**      | **输入特点**                         | **内部实现重点**                                                        |
| ----------- | -------------------------------- | ----------------------------------------------------------------- |
| `PREFILL=0` | `valid_rows=2～64`，多个 query token | 一次处理多个 query；K/V tile 在多个 query 和 7 个 GQA head 间复用；执行 causal mask |
| `DECODE=1`  | `valid_rows=1`，只计算最新 token       | 单 query 流水；只保存一组 online-softmax 状态；K/V 连续流式读取；不构造二维 causal mask   |

两种模式必须使用完全相同的外部接口、Q/K/V Cache 布局和输出格式。PS 只需要设置 `run_mode`：

```text
run_mode           0=Prefill，1=Decode
q_addr             Q_HTD_V2
k_cache_addr       KVC_LHSD_V2
v_cache_addr       KVC_LHSD_V2
output_addr        ACT_TH_V2
layer_id           0～23
query_pos_base     当前 block 的绝对起始位置
valid_rows         Prefill=2～64，Decode=1
cache_len          当前可访问的 KV 总长度
scale              1/sqrt(64)
causal             Prefill=1，Decode 可固定为1
```

接口检查规则：

* `run_mode=DECODE` 时，`valid_rows` 必须等于 1；
* `run_mode=PREFILL` 时，`valid_rows` 范围为 1～64，T=1 也允许用于测试；
* 两种模式输出都为 `[valid_rows][896]`；
* 两种模式都不输出完整 attention weights；
* 两种模式共享同一套状态码、性能计数器和 Debug CRC。

建议第一版采用**一个物理 IP、两种内部调度模式**：共用 AXI 端口、dot-product、exp 和 V accumulation 单元，由 `run_mode` 选择 Prefill 或 Decode 控制流程。这样不会因为同时实例化两套 Attention 导致资源翻倍。

模块负责人仍需分别提交 Prefill 和 Decode 的性能数据。如果后续完整系统资源充足，可以把两个内部 core 分别打包为 `attention_prefill_v2` 和 `attention_decode_v2`；两者寄存器字段必须相同，PS 驱动只切换 base address，不改变参数结构。

## 17. M11 Attention Out Projection IP

### 17.1 数学定义

```text
Y = Attention × Woᵀ
Attention, Y: [T,896]
Wo: [896,896]
```

### 17.2 HLS 逻辑接口

```c
void attention_out_v2(
    const ap_uint<128> *x,
    const ap_uint<128> *weight,
    ap_uint<128> *y,
    uint32_t run_mode,
    uint32_t valid_rows,
    uint32_t hidden_size,
    uint32_t layout_id,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    common_result_v2 *result);
```

### 17.3 微架构

与 QKV 的线性投影引擎共享设计模板：

* `W_OG32_I_L32_V2`；
* x row 片上缓存；
* 8/16/32 输出并行；
* FP32 累加，BF16 输出；
* load/compute/store dataflow。

建议把公共 linear engine 作为源码模板库，但 QKV 和 AttnOut 分别综合，以便分别设置资源参数。

### 17.4 性能模型

权重：

```text
896 × 896 × 2 = 1,605,632 byte / layer call
```

### 17.5 可调参数

`ROW_TILE`、`PAR_OUT`、`H_TILE`、double buffer、prefetch FIFO，与 QKV 相同但独立配置。

### 17.6 验证

T=1/36/64；所有并行度版本结果一致；无 PS 转置/cache 操作。

## 18. M12 Residual Add IP

### 18.1 数学定义

```text
Y[t,h] = BF16_RNE(FP32(A[t,h]) + FP32(B[t,h]))
```

同一实例复用于 Attention residual 和 MLP residual。

### 18.2 HLS 逻辑接口

```c
void residual_add_v2(
    const ap_uint<128> *a,
    const ap_uint<128> *b,
    ap_uint<128> *y,
    uint32_t run_mode,
    uint32_t valid_rows,
    uint32_t hidden_size,
    uint32_t residual_role,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    common_result_v2 *result);
```

### 18.3 微架构

* 每周期读取 a、b 各一拍；
* 8 lane 并行相加；
* 一拍输出；
* 连续 burst 覆盖 `T×112` 个 128-bit words；
* 初始 ABI 禁止地址 alias；未来若验证原地安全，可用 capability 声明。

### 18.4 性能模型

```text
read  = 2 inputs × T × H × 2 byte
write = T × H × 2 byte
```

完全是带宽型模块。若性能低，优先检查 burst 和 AXI，不应增加 DSP。

### 18.5 可调参数

burst length、FIFO depth、in-place capability、未来与 RMSNorm 融合 capability。

### 18.6 验证

舍入边界、正负溢出、T=1/64、两种 role 结果一致。

## 19. M13 Dynamic Tiled SwiGLU IP

### 19.1 数学定义

```text
G = X × Wgateᵀ
U = X × Wupᵀ
M = SiLU(G) ⊙ U
Y = M × Wdownᵀ
```

```text
X,Y: [T,896]
G,U,M: 逻辑上 [T,4864]，生产实现不完整存储
```

### 19.2 HLS 逻辑接口

```c
void swiglu_v2(
    const ap_uint<128> *x,
    const ap_uint<128> *w_gate,
    const ap_uint<128> *w_up,
    const ap_uint<128> *w_down,
    ap_uint<128> *y,
    uint32_t run_mode,            // 0=PREFILL, 1=DECODE
    uint32_t valid_rows,
    uint32_t hidden_size,
    uint32_t intermediate_size,
    uint32_t layout_id,
    uint32_t abi_version,
    uint32_t job_id,
    uint32_t flags,
    common_result_v2 *result);
```

外部全部 BF16；内部 FP32。生产接口没有 gate/up/mid 完整输出。

### 19.3 权重布局

```text
w_gate: W_OG32_I_L32_V2，O=4864，I=896
w_up:   W_OG32_I_L32_V2，O=4864，I=896
w_down: W_OG32_I_L32_V2，O=896， I=4864
```

### 19.4 分块算法

初始建议：

```text
ROW_TILE=4
MID_TILE=64
GATE_UP_PAR=8
DOWN_OUT_PAR=8
```

伪代码：

```text
for row_block in valid_rows by ROW_TILE:
    load x_tile
    clear out_acc[ROW_TILE][896] as FP32

    for mid0 in 0..4864 by MID_TILE:
        gate_tile = matmul(x_tile, Wgate[mid0:mid0+MID_TILE])
        up_tile   = matmul(x_tile, Wup[mid0:mid0+MID_TILE])
        mid_tile  = silu(gate_tile) * up_tile

        for output block in 0..896:
            out_acc += mid_tile × Wdown[output, mid0:mid0+MID_TILE]

    convert out_acc to BF16 and write y
```

完成一个 MID\_TILE 后即可覆盖 gate/up/mid tile，不保留完整 4864 维中间张量。

### 19.5 微架构

```text
load x / prefetch gate-up weights
  → dual projection MAC
  → SiLU + multiply
  → prefetch down weights
  → down MAC accumulation
  → BF16 convert / write
```

gate 和 up 可以：

* 使用两组并行 MAC，速度快、DSP 多；
* 使用同一组 MAC 分时复用，资源少、速度慢。

通过 `GATE_UP_ENGINES=1/2` 构建参数选择，不改变接口。

### 19.6 SiLU 实现

基准数学：`x/(1+exp(-x))`。可选：

* HLS exp；
* LUT；
* 分段多项式。

每种实现分配 `numeric_impl_id`，必须满足预先确定的最大绝对/相对误差，并在模块 manifest 中声明。

### 19.7 性能模型

每层三组权重合计：

```text
3 × 4864 × 896 × 2 = 26,148,864 byte
```

权重带宽和 MAC 都可能成为瓶颈。性能优化必须同时观察：

* HP3 实际吞吐；
* MAC active ratio；
* gate/up 和 down 之间 FIFO 阻塞；
* BRAM/CLB 占用。

### 19.8 可调参数

* `ROW_TILE=1/2/4/8`；
* `MID_TILE=32/64/128`；
* `GATE_UP_PAR=8/16/32`；
* `DOWN_OUT_PAR=8/16/32`；
* `GATE_UP_ENGINES=1/2`；
* SiLU implementation；
* weight double buffer；
* out accumulator BRAM/URAM 映射。

Decode 使用同一个 IP 和参数，`valid_rows=1`，不允许另复制一套大 Decode IP。

### 19.9 性能计数

增加：`mid_tiles`、`gate_up_active_cycles`、`down_active_cycles`、`weight_wait_cycles`、`fifo_stall_cycles`。

### 19.10 验证

* T=1/36/64；
* tile 边界 63/64/65 和 4864 末尾；
* gate/up/SiLU/mid 通过小范围 Debug snapshot；
* 不访问无效 row；
* 不生成完整中间 DDR 输出；
* 不同性能配置数值一致。

### 19.11 Prefill/Decode 双模式设计

当前 SwiGLU 顶层固定 `T=36`，Decode 时即使只有 1 行也会完成 36 行计算。新设计保留一套权重和一套外部接口，通过 `run_mode` 选择两种内部调度：

| **模式**      | **输入特点**          | **内部实现重点**                              |
| ----------- | ----------------- | --------------------------------------- |
| `PREFILL=0` | `valid_rows=2～64` | `ROW_TILE=4/8`；同一权重 tile 尽量复用于多行输入；提高吞吐 |
| `DECODE=1`  | `valid_rows=1`    | `ROW_TILE=1`；不补零、不访问其他行；降低启动和片上缓冲开销     |

统一接口字段：

```text
run_mode           0=Prefill，1=Decode
x_addr             ACT_TH_V2
w_gate_addr         W_OG32_I_L32_V2
w_up_addr           W_OG32_I_L32_V2
w_down_addr         W_OG32_I_L32_V2
y_addr             ACT_TH_V2
valid_rows         Prefill=2～64，Decode=1
hidden_size        896
intermediate_size  4864
layout_id          V2 packed layout
flags/status/perf  使用公共 ABI V2
```

两种模式必须共享：

* BF16 输入输出和权重格式；
* gate/up/down 权重文件；
* SiLU 数学定义和近似版本；
* 输出布局和数值误差标准；
* 驱动参数结构。

推荐采用**一个物理 IP、两个调度模式、共享一套 MAC 引擎**。Prefill 模式按多行 tile 调度，Decode 模式把同一套计算引擎用于单行。不要在当前资源状态下同时实例化完整 Prefill SwiGLU 和完整 Decode SwiGLU，否则很可能无法布局。

如果后续资源允许拆成两个 IP，则命名为 `swiglu_prefill_v2` 和 `swiglu_decode_v2`，并保持完全相同的地址和控制字段。Scheduler 只根据模式选择 IP base address；权重不复制，两个 IP 指向同一套 immutable 权重。

## 20. M14 LM Head / Repetition Penalty / Argmax IP

### 20.1 数学定义

```text
score[v] = dot(hidden[896], weight[v,896])
```

如启用重复惩罚：

```text
score < 0: score *= penalty
score >=0: score /= penalty
```

返回最大 score 和 token id。并列时固定选择较小 token id。

### 20.2 HLS 逻辑接口

```c
void lm_head_v2(
    const ap_uint<128> *hidden,
    const ap_uint<128> *shared_vocab_weight,
    const uint32_t *history_bitmap,
    ap_uint<128> *optional_logits,
    uint32_t hidden_size,
    uint32_t vocab_size,
    uint32_t run_mode,
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

### 20.3 AXI bundle

* hidden、weight、history、optional logits 分离 bundle；
* weight 主口映射 HP2；
* 生产 `write_logits=0`，不产生大输出流量。

### 20.4 微架构

1. hidden 896 项一次加载并缓存；
2. 按 vocab row 顺序读取权重；
3. 每拍 8 个 hidden 权重，FP32 reduction；
4. 对一个或多个 vocab 输出并行计算；
5. 查询 history bitmap 并应用 penalty；
6. 局部 argmax；
7. 归约所有并行 lane 的局部最大值；
8. 可选写 logits。

### 20.5 性能模型

权重总量：

```text
151936 × 896 × 2 = 272,269,312 byte
```

HP2 128 bit、100 MHz 的理想峰值约 1.6 GB/s，单次扫描的纯带宽下界约 0.17 s；实际会更高。因此第一优化目标是让访问成为连续长 burst，并让 MAC 吞吐跟得上内存，而不是盲目堆叠超过带宽供给的 DSP。

### 20.6 可调参数

* `VOCAB_PAR=1/2/4/8`；
* `H_LANES=8/16/32`，通过组合连续拍实现；
* hidden cache 分区；
* reduction tree；
* weight prefetch FIFO；
* history bitmap cache；
* top-k 单元数量；
* 后续 INT8/FP8 weight capability。

外部 VOCAB\_VH\_V2 布局保持不变，H\_LANES 变化不需重新定义权重。

### 20.7 性能计数

增加：`vocab_rows_done`、`weight_wait_cycles`、`dot_active_cycles`、`logits_written`。

### 20.8 验证

vocab 首尾、随机 score、正负 penalty、history 命中、并列最大值、write\_logits 开关；selected token/score 与软件逐项一致。

## 21. M15 Debug/Performance 模块

### 21.1 目的

在不改变生产数据流的前提下，提供完整系统定位和性能调优证据。

### 21.2 调用记录

```c
struct perf_record_v2 {
    uint32_t job_id;
    uint16_t module_id;
    uint16_t layer_id;
    uint32_t valid_rows;
    uint32_t status;
    uint64_t ps_start;
    uint64_t ps_end;
    uint64_t pl_cycles_total;
    uint64_t pl_cycles_compute;
    uint64_t read_beats;
    uint64_t write_beats;
    uint64_t cache_clean_bytes;
    uint64_t cache_invalidate_bytes;
    uint32_t input_crc;
    uint32_t output_crc;
};
```

### 21.3 Snapshot

```text
snapshot(job, layer, module, tensor_id, byte_offset, byte_length)
```

* 只有指定范围被复制；
* 默认最大长度受限；
* 生产构建关闭；
* snapshot 结果附带布局、dtype、generation 和 CRC。

### 21.4 AXI 性能监测

在 HP0～HP3 和 PL DDR 关键路径放置系统级 monitor，至少统计：

* read/write bytes；
* average burst length；
* outstanding；
* address/data stall；
* port utilization。

monitor 的插入方式要允许 Release 构建关闭详细 trace，只保留累加计数，避免监测本身造成拥塞。

## 22. 旧模块和兼容模块设计

### 22.1 不进入生产链的旧模块

以下代码保留用于 reference 或旧版回归，不连接到 ABI V2 生产 Block Design：

* GQA Repeat：功能并入 M10，禁止复制 K/V 到 14 heads；
* Attention Value：功能并入 M10 online-softmax；
* 独立 QK Softmax：功能并入 M10；
* 独立 SiLU：功能并入 M13；
* 通用 MLP/Linear：仅作 reference；
* BF16/FP16 大 buffer 转换：生产链取消。

### 22.2 Format Adapter

为读取旧 golden 或做兼容测试，可以保留一个软件/低资源 PL adapter：

```text
BF16 ↔ FP16
token-major ↔ head-major
Layout V1 ↔ Layout V2
```

它必须满足：

* 不进入性能测试路径；
* Scheduler production mode 无法调用；
* 输出明确标记 `COMPAT_ONLY`；
* 发布统计不把 adapter 时间隐藏在其他模块中。

## 23. 模块间 buffer 和 alias 规则

| **生产者**       | **输出**          | **消费者**            | **Alias 规则**        |
| ------------- | --------------- | ------------------ | ------------------- |
| Embedding/上一层 | hidden `[T,H]`  | Input RMS          | 初版不原地               |
| Input RMS     | norm `[T,H]`    | QKV                | 只读                  |
| QKV           | q\_raw/k\_raw/v | RoPE/KV            | Q/K 独立；V 只读         |
| RoPE          | q\_rot/k\_rot   | Attention/KV       | 独立输出，便于调试           |
| KV Update     | PL DDR cache    | Attention          | 写完成后读               |
| Attention     | `[T,H]`         | AttnOut            | 只读                  |
| AttnOut       | `[T,H]`         | Residual           | 与 residual0 不重叠     |
| Residual 1    | `[T,H]`         | Post RMS、residual1 | 保留到 MLP residual 完成 |
| Post RMS      | `[T,H]`         | SwiGLU             | 只读                  |
| SwiGLU        | `[T,H]`         | Residual 2         | 与 residual1 不重叠     |
| Final RMS     | `[H]`           | LM Head            | 只读                  |

后续如要启用 in-place，必须由 module capability 声明，并在 C/RTL cosim 和板测证明所有 AXI 读完成后才覆盖。不能只因地址看起来相同就默认安全。

## 24. 模块性能优化矩阵

| **模块**    | **首要瓶颈假设**      | **第一调节参数**    | **第二调节参数**   | **不应先做**        |
| --------- | --------------- | ------------- | ------------ | --------------- |
| Embedding | DDR 顺序读写        | burst/FIFO    | 行 cache      | 增加 DSP          |
| RMSNorm   | reduction/rsqrt | lanes/tree    | rsqrt 实现     | 复制多个 IP         |
| QKV       | 权重带宽+MAC        | PAR\_OUT      | ROW/H tile   | 改输出布局           |
| RoPE      | 启动和搬运           | block 调用      | head/D 并行    | 每 token 启动      |
| KV Update | 小传输固定开销         | 聚合/burst      | K/V 双通道      | 固定 64 行 staging |
| Attention | 计算+PL DDR       | KV tile/GQA复用 | head/D/exp并行 | 保存完整 weight 矩阵  |
| AttnOut   | 权重带宽+MAC        | PAR\_OUT      | ROW/H tile   | 改权重语义           |
| Residual  | DDR 带宽          | burst/FIFO    | 合法 in-place  | 增加乘法器           |
| SwiGLU    | 权重+MAC+资源       | MID/ROW tile  | 并行引擎         | 完整中间数组          |
| LM Head   | HP2 带宽          | burst/H lanes | vocab并行      | 默认写完整 logits    |

## 25. 系统级资源和时序门槛

当前工程实现已接近布局上限，因此模块优化不能只看单 IP HLS latency。

完整 V2 系统的初始门槛：

* 目标时钟：先保证 100 MHz；
* 全系统 WNS ≥ 0；
* CLB 占用目标 \<85%；
* BRAM 占用目标 \<70%；
* DSP 使用需保留后续调优余量；
* 无高严重度拥塞和 critical warning。

每个模块负责人提交 HLS 结果后，架构负责人建立 `resource_budget.csv`。预算以完整系统实现结果为准，不允许某个模块因为单独有空余资源就无限扩张。

若完整系统资源不达标，调整顺序：

1. 删除非生产 Debug 大数组和端口；
2. 缩小 Attention/SwiGLU tile 和数组分区；
3. 降低大模块并行度；
4. 共享昂贵 math 单元；
5. 最后才降低频率目标。

## 26. 单模块验证统一规范

### 26.1 四级测试

1. 纯软件 FP32/BF16 reference；
2. HLS C simulation；
3. HLS C/RTL cosimulation；
4. 单 IP 板测或 AXI VIP 测试。

### 26.2 每个计算模块必须覆盖

* `valid_rows=1`；
* `valid_rows=MAX`；
* 首尾地址；
* 非法 ABI、维度、地址和布局；
* 随机数据；
* 全零、常数、极值；
* 旧问题的回归样例；
* 至少两个性能配置之间的数值一致性。

### 26.3 数值报告

每个模块报告：

* max absolute error；
* max relative error；
* mean absolute error；
* cosine similarity；
* NaN/Inf 数量；
* 对最终 token 可能产生影响的边界案例。

Attention、SiLU、rsqrt 使用近似实现时必须额外报告全定义域误差。

## 27. 模块交付包

```text
module_<id>_<name>_v2/
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

`module_manifest.json` 至少记录：

* module id/name/version；
* ABI、layout、dtype；
* HLS/Vivado 版本；
* build\_config；
* 端口宽度和 bundle；
* 目标时钟；
* HLS latency/II；
* implemented LUT/FF/BRAM/DSP/WNS；
* golden hash；
* IP/component hash；
* 已知限制。

## 28. 后续性能版本的兼容规则

### 28.1 不需要升级 ABI 的变化

* PAR、tile、FIFO、double buffer；
* 内部 BRAM/URAM 映射；
* HLS pragma；
* 等价数值实现且仍满足误差合同；
* 目标频率；
* 计数器内部实现。

这类变化只增加 module revision 和 build\_config。

### 28.2 必须升级 ABI 或 Layout 的变化

* 改变输入输出张量顺序；
* 改变权重的数学维度或规范文件布局；
* 改变 BF16/FP16/INT8 的外部类型；
* 新增影响数学结果的运行参数；
* 改变 KV Cache 的线性地址公式；
* 改变 repetition penalty、tie-break 等可见语义。

### 28.3 模块融合

未来 QKV+RoPE+KV Write、Attention+AttnOut、Residual+RMS 可以融合，但必须：

* 保留原始逻辑接口的 capability 映射；
* 产生相同布局和数值语义；
* 调试模式仍能导出各逻辑边界 CRC；
* Scheduler 根据 capability 选择融合路径；
* 不直接删除离散 reference 实现。

## 29. 模块设计完成判定

一个模块只有满足以下条件才算“设计和实现完成”：

* 接口与 ABI V2 完全一致；
* layout 和有效范围无歧义；
* 算法步骤和数值规则有 reference；
* HLS C/RTL 测试通过；
* 错误输入能够返回标准状态码；
* 性能计数有效；
* 至少一个基准配置完成 implementation；
* 资源和时序符合预算；
* 性能参数可以调整且不改变接口；
* 交付包完整、哈希可追溯。

本说明书冻结后，各模块可以独立实现和优化；后续整批集成时，汇总人只需要依据统一的 ABI、layout、manifest 和测试向量连接模块，不需要重新解释每个模块的数据含义。

## 30. 结合当前代码的模块优化建议

以下建议针对目前实际代码，不只是理论上的优化方向。

| **模块**                 | **当前代码的主要问题**                                                   | **本次具体优化**                                                          | **Prefill/Decode 设计**                                             |
| ---------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------- |
| M00 Host/TCP           | 运行过程中打印较多，协议与性能数据混在一起                                           | 运行时只保留错误信息；性能记录先存内存，推理结束后再返回                                        | 保留 mode 字段，用于区分 Prefill 和 Decode 统计                               |
| M01 Scheduler/Runtime  | 按模块轮询；RoPE 按 token 启动；存在 shadow、Q/K/V 转置和格式转换                   | 保留清晰的顺序调度；删除 fast path 的 shadow/转置；RoPE 按 block 启动；统一 BF16          | Scheduler 为每次调用设置 run\_mode 和 valid\_rows                         |
| M02 IP Registry/Driver | wrapper 内重复打印、重复 cache 操作，部分等待循环没有统一超时                          | 日志分级；统一启动/等待/超时；wrapper 不再自行清理完整 buffer                             | 同一个 driver 参数结构支持单 IP 双模式或两个同接口 IP                                |
| M03 Buffer Manager     | 当前常按整个 descriptor 做 clean/invalidate                            | 只处理实际有效范围；增加 owner、valid\_bytes、generation；PL 到 PL 不做 cache 操作      | Prefill 按多行范围处理，Decode 只处理一行范围                                    |
| M04 Weight Store       | 权重已固定在 DDR，但调用前仍可能重复 clean；没有严格布局版本                             | 权重加载后只 clean 一次；增加 layout、ABI、文件大小和哈希检查                             | Prefill/Decode 共用同一套权重，不复制权重                                      |
| M05 Embedding          | 当前接口使用 half，最大 token 数固定为 36，数据口不利于宽 burst                      | 外部统一 BF16；支持 1～64 行；128-bit 连续读取词表行                                 | 先使用同一实现；Prefill 多 token，Decode 一 token；保留 run\_mode               |
| M06 RMSNorm            | 当前 legacy 核固定处理 36 行，Decode 仍做无效计算                              | 增加 valid\_rows；缓存 896 个 norm weight；128-bit 读写；FP32 reduction       | 共用一个物理 IP；Prefill 多行，Decode 强制一行                                  |
| M07 QKV                | 当前 Q/K/V 分三次计算，OUT\_PAR=4，多个接口为 32 bit，输出还需 PS 转置               | 合并 Q/K/V；X 只读一次；权重按 32 元素分组；基准 PAR=8；直接输出 head-major                | 可采用两种调度：Prefill 使用 ROW\_TILE，Decode 使用 ROW\_TILE=1；接口不变           |
| M08 RoPE               | PS 当前为每个 token 启动一次，启动和 cache 开销大                               | Prefill 一次处理整个 block；直接读写 head-major Q/K；cos/sin 按绝对位置访问            | Prefill block 模式；Decode 单 token 模式；共用一个物理 IP                      |
| M09 KV Cache           | 当前有固定 64-token staging、完整清零和 debug repeat 输出                    | 只写 valid\_rows；按 K/V head 连续 burst；关闭生产 debug repeat；直接写 PL DDR     | 共用一个物理 IP；Prefill 连续写多 token，Decode 只写当前位置                        |
| M10 Attention/Softmax  | 当前保存完整 K/V 和 attention weights，占用大量 BRAM；Prefill/Decode 使用同一大循环 | 改为 KV tile online-softmax；K/V 在 7 个 Q head 间复用；生产不输出完整 weights      | 明确双模式：Prefill 多 query、causal、重用 KV tile；Decode 单 query、流式扫描 cache |
| M11 Attention Out      | 当前 OUT\_PAR=4，接口多为 32 bit                                       | 使用 packed weight、128-bit AXI、PAR=8 起步、X row 片上复用                    | Prefill 使用多行 tile；Decode 使用单行调度；保留相同接口                            |
| M12 Residual Add       | 当前 uint16\_t 指针接口实际较窄                                           | 128-bit 读 A/B 和写 Y；8 个 BF16 并行；只处理有效行                               | 共用一个物理 IP，模式只影响 valid\_rows                                       |
| M13 SwiGLU             | 当前固定 T=36；Decode 仍算 36 行；使用完整中间数组，占 BRAM 多；PS 还做 BF16/FP16 转换   | 外部统一 BF16；增加 valid\_rows；MID\_TILE/ROW\_TILE；不保存完整 gate/up/mid；共享权重 | 明确双模式：Prefill 多行复用权重；Decode ROW\_TILE=1、不补零                       |
| M14 LM Head            | 当前权重和 hidden 使用 half 接口，端口较窄；每 token 扫描大词表；Debug 可写完整 logits    | 128-bit 连续读取；hidden 缓存；PL 内 argmax；生产关闭完整 logits 写回                 | 两种模式输入都是最后一个 token，可共用实现；保留 mode 用于统计                             |
| M15 Debug/Performance  | 当前时间、日志和模块状态统计不统一                                               | 每次调用记录 mode、行数、周期、读写字节、CRC 和状态；Debug snapshot 只抓指定范围                | 分别汇总 Prefill 和 Decode 性能                                          |

## 31. Prefill/Decode 统一接口设计

### 31.1 所有计算模块保留的公共参数

```
abi_version      接口版本
job_id           本次调用编号
run_mode         0=Prefill，1=Decode
valid_rows       本次真实 token 行数
flags            Debug、CRC 等控制
status_code      执行结果
processed_rows   实际处理行数
perf_cycles      硬件运行周期
output_crc       输出检查值
```

统一检查规则：

* run\_mode=DECODE 时，token 维模块必须满足 valid\_rows=1；
* run\_mode=PREFILL 时，valid\_rows=1～64；
* Decode 模式不能读取或写入第 1 行以后的数据；
* 两种模式必须使用相同 dtype、布局、权重和错误码；
* 即使当前实现不区分两种算法，也要保留 run\_mode 参数。

### 31.2 模块采用哪种方式

| **模块**            | **推荐方式**                 | **原因**                                        |
| ----------------- | ------------------------ | --------------------------------------------- |
| M05 Embedding     | 一个 IP、保留双模式接口            | 主要区别只有 token 数量                               |
| M06 RMSNorm       | 一个 IP、保留双模式接口            | 使用 valid\_rows 即可消除无效计算                       |
| M07 QKV           | 一个 IP、两种内部调度             | Prefill 可做多行 tile，Decode 做单行                  |
| M08 RoPE          | 一个 IP、两种内部调度             | Prefill block 与 Decode 单 token 差别明显，但计算单元可共享  |
| M09 KV Update     | 一个 IP、保留双模式接口            | 写入长度不同，地址公式相同                                 |
| M10 Attention     | 一个 IP、两个专用调度 core，共享计算资源 | Prefill 和 Decode 的 query 数、mask 和 KV 复用方式差别最大 |
| M11 Attention Out | 一个 IP、两种内部调度             | 与 QKV 类似，接口和权重完全相同                            |
| M12 Residual      | 一个 IP、保留双模式接口            | 算法相同，只是行数不同                                   |
| M13 SwiGLU        | 一个 IP、两个专用调度 core，共享 MAC | Prefill 需要多行复用，Decode 必须只做一行                  |
| M14 LM Head       | 一个 IP、保留双模式接口            | 两种模式最终都只输入最后一个 token                          |

### 31.3 如果以后拆成两个物理 IP

可以把 M10 或 M13 拆成：

```
attention_prefill_v2 / attention_decode_v2
swiglu_prefill_v2    / swiglu_decode_v2
```

但必须遵守：

1. 两个 IP 的参数名称、顺序和含义一致；
2. 两个 IP 使用相同的数据布局和权重文件；
3. Prefill IP 只接受 run\_mode=0，Decode IP 只接受 run\_mode=1；
4. PS Runtime 使用同一个参数结构，只根据 mode 选择不同 base address；
5. 两个 IP 的输出都能直接连接同一个下游模块；
6. 必须先确认完整工程资源允许，不能让 CLB/BRAM 超限。

PS 侧选择方式：

```
base = (run_mode == DECODE) ? decode_ip_base : prefill_ip_base;
configure_same_registers(base, &params);
start_and_wait(base);
```

当前工程 CLB、BRAM 已经较紧，因此第一版优先采用一个物理 IP、两个内部模式。接口先保留好，后续有资源时再拆物理 IP，不需要重写 PS 调度。

## 32. 2026-10-10 模块交付计划

所有模块最晚在 **2026-10-10** 交给喻燕萍汇总。交付内容至少包括：源码、可综合 IP、驱动、接口说明、单模块测试结果、资源报告和已知问题。

| **人员**  | **工作内容**                                     | **计划完成时间**       |
| ------- | -------------------------------------------- | ---------------- |
| 林家豪     | 整体架构、统一接口、数据布局和 Prefill/Decode 规则            | 2026-09-25       |
| 林家豪、喻燕萍 | AXU9EGB 板级 profile（DDR、HP/MIG 位宽、时钟、复位）核对并冻结 | 2026-09-25       |
| 喻燕萍     | PS Runtime、调度、驱动、内存管理和整体框架                   | 2026-09-30       |
| 喻燕萍     | M04、M06、M09、权重加载和验证                          | 2026-10-10       |
| 姜小平     | M08、M10；完成 Prefill/Decode 两种模式测试             | 2026-10-10       |
| 卖鑫盛     | M05；保留 Prefill/Decode 接口                     | 2026-10-10       |
| 朱凌      | M13；完成 Prefill/Decode 两种模式测试                 | 2026-10-10       |
| 张本      | M14；保留 Prefill/Decode 接口                     | 2026-10-10       |
| 胡明阳     | M12、M07、M11；保留统一双模式接口                        | 2026-10-10       |
| 全体      | 模块源码、IP、驱动、测试结果和资源报告交给喻燕萍                    | 2026-10-10       |
| 喻燕萍（汇总） | 一次性集成全部模块，完成第一版完整工程                          | 2026-10-23       |
| 全体      | 完整系统功能调试和性能优化                                | 2026-10-24～11-13 |
| 林家豪、喻燕萍 | 最终检查、整理版本和发布资料                               | 2026-11-20       |

### 32.1 汇总后的工作

1. 10 月 10 日前，各负责人完成自己的模块和单模块测试。
2. 10 月 11 日开始，喻燕萍一次性把全部模块加入完整工程。
3. 10 月 23 日前生成可运行的 bitstream、XSA、ELF 和对应权重。
4. 10 月 24 日到 11 月 13 日，全体一起解决功能、资源、时序和性能问题。
5. 11 月 20 日前完成最终版本。

### 32.2 10 月 10 日交付标准

每个模块交付时必须能够回答：

* 输入、输出、dtype 和布局是什么；
* Prefill 和 Decode 分别怎样设置 run\_mode/valid\_rows；
* 是否使用同一个物理 IP；
* 单模块结果是否与 reference 一致；
* T=1 和最大 Prefill 行数是否通过；
* 使用多少 LUT、BRAM、DSP，目标频率是否通过；
* 当前还存在哪些问题。

没有接口说明、测试结果或资源报告的 IP，不算完成交付。

## 33. 两个月完成目标

* 模块统一交付：**2026-10-10**
* 第一版完整工程：**2026-10-23**
* 系统功能和性能调试完成：**2026-11-13**
* 最终版本完成：**2026-11-20**

计划按所有模块并行开发安排。M10 和 M13 是双模式优化的重点；其他计算模块统一保留 run\_mode，以后可以在不改变 PS 接口的情况下继续增加 Prefill/Decode 专用实现。

## 34. 结合 AXU9EGB 开发板手册后的板级核查与调整

本节把“开发板固有能力”和“当前 Vivado 工程的配置”分开记录。开发板手册来源为：

`D:\master\yan\LLM\0921\AXU9EGB开发板用户手册\AXU9EGB开发板用户手册\AXU9EGB开发板用户手册.md`

### 34.1 手册确认的硬件事实

| **项目**      | **手册确认内容**                        | **对本项目的直接影响**                                                               |
| ----------- | --------------------------------- | --------------------------------------------------------------------------- |
| FPGA 器件     | `XCZU9EG-2FFVB1156I`              | 约束文件、器件选择和 bitstream 必须保持一致；不能把设计描述成其它 ZU9/封装。                              |
| PS DDR4     | 4 GB、64 bit，连接 PS BANK504         | PS buffer、权重和激活可以放在 PS DDR；M03 必须按实际可用区间做范围检查。                              |
| PL DDR4     | 2 GB、32 bit，连接 PL BANK64/65       | M09/M10 的 KV Cache 放在 PL DDR；物理数据总线是 32 bit，但不等于 MIG AXI 用户口也是 32 bit。      |
| PS 参考时钟     | 单端 33.333333 MHz                  | 这是 PS 输入参考，不是 HLS/AXI 计算频率。PS 时钟由 PS 配置产生，不能在文档中把 33.333333 MHz 当作 PL 目标频率。 |
| PL/DDR 参考时钟 | 差分 200 MHz                        | 用于 PL DDR 控制器和相关时钟生成；不能直接等同于所有用户逻辑的工作时钟。                                    |
| 板载复位/启动     | 外部复位按键低有效；支持 JTAG、QSPI、eMMC、SD 启动 | 复位按键的电平不能直接当作所有 `ap_rst_n` 的时序定义；M02 仍需按 BD 导出的复位链路检查。                      |
| 其它接口        | FMC、GTH、以太网、USB 等均有扩展             | 当前 LLM 推理数据面没有使用它们，不把这些接口误写成模型计算的必需通路。                                      |

手册中 DDR 器件速度级别存在不同写法（如 `MT40A512M16GE`、`MT40A512M16LY-062E`）。因此“2400 Mbps”只能看作手册给出的板卡能力上限，不能替代实际板卡 BOM、MIG 参数和校准结果。

### 34.2 当前工程中已核对的 Vivado 配置

以下内容来自目标工程 `system_wrapper.bd`/DDR4 XCI，而不是开发板手册，后续重新生成 BD 时必须自动复核：

核查文件为：

* `D:\FPGA_PRO\llme_SDWeight_proj\rmsnorm_axu9egkv_gqa_lmhead\rmsnorm_axu9eg.srcs\sources_1\bd\system_wrapper\system_wrapper.bd`
* `D:\FPGA_PRO\llme_SDWeight_proj\rmsnorm_axu9egkv_gqa_lmhead\rmsnorm_axu9eg.srcs\sources_1\bd\system_wrapper\ip\system_wrapper_ddr4_0_0\system_wrapper_ddr4_0_0.xci`

| **项目**                       | **当前工程值**                                                            | **说明**                                                             |
| ---------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------ |
| PS `S_AXI_HP0_FPD`～`HP3_FPD` | 128 bit                                                              | 这是当前 PS IP 配置，不是 AXU9EGB 板卡固定的物理属性。                                |
| PS HP 地址宽度                   | 40 bit                                                               | 当前 Zynq PS HP 主口可覆盖高地址 PS DDR 段；descriptor 仍使用 64 bit 物理地址。        |
| PL DDR 物理数据宽度                | 32 bit                                                               | 与手册的 BANK64/65、32 bit 物理总线一致。                                      |
| PL DDR MIG AXI 数据宽度          | 128 bit                                                              | 当前 XCI 的 `DDR4_AXI_DATA_WIDTH=128`；`kv_axi_t` 应以该值生成，不能写死为 32 bit。 |
| PL DDR AXI 地址宽度/容量           | 31 bit、2 GiB                                                         | 当前 MIG 地址块为 2 GiB；M03/M09 需要把容量作为运行时 profile，而不是凭接口宽度推断。           |
| PL DDR 参考输入                  | 200 MHz（约 5003 ps）                                                   | 与手册的差分 200 MHz 参考时钟相符。                                             |
| PL DDR MIG UI 时钟             | 266.5 MHz                                                            | 当前 XCI 的 UI 配置；它不是手册中“200 MHz 参考时钟”，也不是 HLS 用户逻辑时钟。                |
| 当前 HLS/AXI 设计目标              | 100 MHz 优先                                                           | 这是当前实现/时序目标，后续以 XDC 和实现报告为准；`CLOCK_CODE` 记录的是用户逻辑目标档位。             |
| PS DDR 地址段                   | `DDR_LOW: 0x00000000～0x7FFFFFFF`；`DDR_HIGH: 0x800000000～0x87FFFFFFF` | 当前 BD 将 4 GB PS DDR 表现为两个 2 GiB 段，M03 不能只用一个“连续 4 GB”区间判断地址合法性。    |

### 34.3 必须落实到设计的调整

1. **M03 地址检查改为“区间表”**。PS DDR 用 `ps_ddr_regions[]` 登记每个可访问段；PL DDR 单独登记容量、AXI 位宽和基地址。任何 descriptor 必须完整落在一个已登记区间内，不能跨越两个区间自动拼接。
2. **M09/M10 同时记录物理宽度和 AXI 用户宽度**。`pl_ddr_phy_bits=32` 只描述板上 DDR4 的 DQ 总线；当前 `pl_ddr_axi_bits=128` 才是 HLS 侧 `kv_axi_t` 的外部 beat 宽度。两者分别进入 hardware profile 和 module manifest。
3. **M02 启动前增加板级自检**。至少检查 PS DDR 可用、PL DDR `init_calib_complete`、HP0～HP3 宽度、MIG AXI 宽度、用户逻辑时钟和复位释放；任何一项不匹配时，不进入推理调度。
4. **M04 权重验证使用实际文件大小**。按 V2 形状估算，权重（Embedding/LM Head 共享）约 942 MiB，K/V Cache 满容量约 24 MiB（K 12 MiB + V 12 MiB）；最终仍以 manifest 文件大小、padding 和 SHA256 为准，不能只按理论公式放地址。
5. **性能模型使用工程时钟**。PS HP 峰值、PL DDR 峰值和模块 `perf_cycles` 必须分别使用 HP 128 bit、MIG AXI 128 bit、实际用户时钟/DDR UI 时钟计算；不能拿板卡 200 MHz 参考时钟直接计算 HLS 吞吐。
6. **保留板卡可移植性**。`EXTERNAL_BEAT_BITS`、`pl_ddr_axi_bits`（构建别名 `KV_AXI_BITS`）、PS DDR 区间和用户时钟都写入 `hardware_profile_v2`，模块公共 ABI 只引用 profile，不把本次板卡数值散落到每个模块源码中。

### 34.4 不需要因开发板手册而改变的内容

* Qwen2.5 的模型常量、BF16 外部类型、固定 32 元素权重分组、`ACT/Q/KV/KVC` 布局不因板卡手册改变；
* M05～M14 的 `run_mode`、`valid_rows`、状态码和 Prefill/Decode 统一接口继续保持；
* HP0～HP3 的当前分组可以继续使用，但它属于当前 BD 的实现选择，性能优化时只能依据 APM/ILA 实测再调整；
* M10/M13 先采用一个物理 IP、两种内部调度的方案不变，板卡资源紧张时不能仅因 DDR 容量大就复制两套计算核。

### 34.5 集成前新增的板级验收顺序

1. 由架构负责人和汇总人冻结 `hardware_profile_v2`，把手册事实、BD/XCI 实际值和 SHA256 记录在版本 manifest；
2. 在所有模块交给喻燕萍前完成 DDR 校准、HP/MIG 位宽和复位自检；
3. 单独测量 HP0～HP3 和 PL DDR 的连续读写吞吐，更新 M07/M10/M13/M14 的性能预算；
4. 全部模块一次性集成时，M03 依据 profile 分配 PS/PL DDR 区域，M02 依据 profile 检查 IP 能力；
5. 最终报告同时给出“手册理论能力、当前 BD 配置、板上实测能力”三组数据，避免把三者混为一个数字。
