# PS/PL 全模块参数与接口字段说明书

版本：V2 设计稿

日期：2026-09-22

配套文档：《PS/PL 全模块架构、详细设计与统一集成实施计划》

适用工程：`D:\FPGA_PRO\llme_SDWeight_proj`

> 本文是接口和字段说明书，不是当前代码已经全部实现的声明。文中“V2 规定”表示统一集成时应采用的目标接口；“当前工程”表示现有代码状态。本文不修改任何工程代码。

## 1. 阅读说明

### 1.1 M00～M15 是什么

M00～M15 是软件/硬件功能模块编号，用来划分责任和交付边界。它们不是 Vivado Block Design 中 `M00_AXI`、`M01_AXI` 之类的 AXI 端口编号。

例如：

* M00：接收上位机请求；
* M01：安排整次推理的执行顺序；
* M02：找到并驱动具体 PL IP；
* M03：管理计算使用的内存；
* M04：加载和验证权重；
* M05～M14：实际推理计算模块；
* M15：调试和性能记录。

### 1.2 一次请求经过哪些接口

```text
上位机
  │ M00 网络包
  ▼
M00 Host/TCP ── inference_job_v2 ──► M01 Scheduler
                                        │
                                        ├─向 M03 申请/检查 buffer descriptor
                                        ├─向 M02 提交模块参数
                                        ▼
                                   M02 Driver
                                        │ AXI-Lite 寄存器
                                        ▼
                                   M05～M14 PL IP
                                        │ AXI 主口读写数据
                                        ▼
                               PS DDR / PL DDR / KV Cache

M15 在各阶段记录 job、模块、周期、流量和 CRC。
```

### 1.3 字段类型约定

| **类型**         | **宽度**  | **用途**                     |
| -------------- | ------- | -------------------------- |
| `uint8_t`      | 8 bit   | 小枚举、状态                     |
| `uint16_t`     | 16 bit  | 模块号、实例号、布局号                |
| `uint32_t`     | 32 bit  | 长度、模式、标志、token、寄存器         |
| `uint64_t`     | 64 bit  | 物理地址、时间戳、周期计数              |
| `bf16_t`       | 16 bit  | 外部激活、权重和表数据                |
| `float`/FP32   | 32 bit  | 累加、softmax、比例和分数           |
| `ap_uint<128>` | 128 bit | PS HP 口上的一个数据拍，容纳 8 个 BF16 |

除网络协议明确规定为小端外，结构体不能直接依赖编译器自然布局跨设备传输；网络结构应使用固定宽度字段、显式序列化和长度检查。

## 2. 全局常量和枚举

### 2.1 模型常量

| **名称**               | **V2 值** | **含义**                               | **校验规则**                                |
| -------------------- | -------- | ------------------------------------ | --------------------------------------- |
| `NUM_LAYERS`         | 24       | Transformer 层数                       | `layer_id` 必须为 0～23                     |
| `HIDDEN_SIZE`        | 896      | hidden 维度                            | V2 固定为 896                              |
| `NUM_Q_HEADS`        | 14       | Query head 数                         | V2 固定为 14                               |
| `NUM_KV_HEADS`       | 2        | K/V head 数                           | V2 固定为 2                                |
| `GQA_GROUP_SIZE`     | 7        | 每个 KV head 服务的 Q head 数              | `14 / 2 = 7`                            |
| `HEAD_DIM`           | 64       | 每个 head 的维度                          | V2 固定为 64                               |
| `INTERMEDIATE_SIZE`  | 4864     | SwiGLU 中间维度                          | V2 固定为 4864                             |
| `VOCAB_SIZE`         | 151936   | 词表大小                                 | token 必须小于该值                            |
| `MAX_SEQUENCE`       | 2048     | KV Cache 最大序列长度                      | 位置范围 0～2047                             |
| `MAX_BLOCK_ROWS`     | 64       | 单次 Prefill 最大 token 行数               | `valid_rows` 最大为 64                     |
| `EXTERNAL_BEAT_BITS` | 128      | 当前 `system_wrapper.bd` 中 PS HP 数据拍宽度 | 8 个 BF16/拍；这是当前 Vivado 配置，不是开发板固定值      |
| `CACHE_LINE_BYTES`   | 64       | PS 软件 buffer 和 cache 操作对齐合同          | 地址和范围按 64 byte 处理，最终由运行时确认 CPU cache 属性 |

### 2.2 运行模式 `run_mode`

| **值** | **名称**    | **含义**                  | **`valid_rows`** |
| ----- | --------- | ----------------------- | ---------------- |
| 0     | `PREFILL` | 一次处理提示词中的一个 token block | 1～64             |
| 1     | `DECODE`  | 一次只生成链路中的一个新 token      | 必须为 1            |

`run_mode` 是长期保留字段。某模块当前即使两种模式使用相同算法，也必须接受并检查它，以便以后只改变内部调度，不改变 PS 接口。

### 2.3 数据类型 `dtype`

建议冻结以下编号：

| **值** | **名称**          | **单元素字节数** | **用途**               |
| ----- | --------------- | ---------- | -------------------- |
| 0     | `DTYPE_INVALID` | 0          | 未初始化/非法              |
| 1     | `DTYPE_BF16`    | 2          | 激活、权重、bias、RoPE 表    |
| 2     | `DTYPE_FP32`    | 4          | 调试中间量、logit/score    |
| 3     | `DTYPE_U32`     | 4          | token、history bitmap |
| 4     | `DTYPE_U8`      | 1          | 原始字节或辅助表             |

### 2.4 布局 `layout_id`

建议冻结编号，不允许不同模块自行重新编号：

| **建议值** | **名称**              | **逻辑形状**              | **线性索引/说明**                |
| ------- | ------------------- | --------------------- | -------------------------- |
| 0       | `LAYOUT_INVALID`    | 无                     | 未初始化                       |
| 1       | `ACT_TH_V2`         | `[T][896]`            | `t×896+h`                  |
| 2       | `Q_HTD_V2`          | `[14][T][64]`         | `(qh×T+t)×64+d`            |
| 3       | `KV_HTD_V2`         | `[2][T][64]`          | `(kh×T+t)×64+d`            |
| 4       | `KVC_LHSD_V2`       | `[24][2][2048][64]`   | `(((l×2+kh)×2048+s)×64+d)` |
| 5       | `ROPE_SD_V2`        | `[2048][64]`          | `s×64+d`                   |
| 6       | `W_OG32_I_L32_V2`   | `[ceil(O/32)][I][32]` | 32 输出为一组                   |
| 7       | `VOCAB_VH_V2`       | `[151936][896]`       | 词表/Embedding 共享表           |
| 8       | `TOKEN_U32_V2`      | `[T]`                 | 32-bit token id            |
| 9       | `HISTORY_BITMAP_V2` | `[ceil(V/32)]`        | 每个 token 占一位               |

布局编号描述数据如何排列；它与 AXI 端口宽度不同。端口可以由 128 bit 改为其他物理宽度，但逻辑布局不能因此悄悄改变。

### 2.5 AXU9EGB 板级参数与工程参数

开发板手册来源：

`D:\master\yan\LLM\0921\AXU9EGB开发板用户手册\AXU9EGB开发板用户手册\AXU9EGB开发板用户手册.md`

必须把“板卡事实”和“Vivado 可配置值”分开。前者决定容量和可用引脚，后者决定当前 bitstream 的接口宽度、时钟和地址映射。

#### 2.5.1 板卡事实

| **字段**                      | **值**                | **说明**                                |
| --------------------------- | -------------------- | ------------------------------------- |
| `BOARD_PART`                | `XCZU9EG-2FFVB1156I` | AXU9EGB 核心板上的器件型号                     |
| `PS_DDR_PHY_BITS`           | 64                   | PS BANK504 外接 DDR4 物理数据总线             |
| `PS_DDR_CAPACITY_BYTES`     | `4 GiB`              | 4 片 DDR4 的总容量                         |
| `PL_DDR_PHY_BITS`           | 32                   | PL BANK64/65 外接 DDR4 物理数据总线           |
| `PL_DDR_CAPACITY_BYTES`     | `2 GiB`              | 2 片 DDR4 的总容量                         |
| `PS_REF_CLOCK_HZ`           | 33,333,333（约）        | 板载 PS 单端参考时钟                          |
| `PL_DDR_REF_CLOCK_HZ`       | 200,000,000          | 板载 PL DDR 差分参考时钟                      |
| `RESET_BUTTON_ACTIVE_LEVEL` | 0                    | 板上外部复位按键低有效；不等同于每个 IP 的 `ap_rst_n` 时序 |

手册对 DDR4 速度级别有 `MT40A512M16GE`、`MT40A512M16LY-062E` 等不同写法；当前工程 XCI 使用 `MT40A512M16LY-075`。因此手册中的 2400 Mbps 应看作器件/板卡能力说明，实际工作速率必须以板卡 BOM、MIG 参数和校准结果为准。

#### 2.5.2 当前工程配置（不是板卡固定值）

本表核对的工程文件是 `D:\FPGA_PRO\llme_SDWeight_proj\rmsnorm_axu9egkv_gqa_lmhead\rmsnorm_axu9eg.srcs\sources_1\bd\system_wrapper\system_wrapper.bd` 及其 `system_wrapper_ddr4_0_0.xci`。重新生成 BD 或更换 bitstream 后，应重新导出这些字段。

| **字段**                   | **当前值**         | **来源/使用规则**                                                     |
| ------------------------ | --------------- | --------------------------------------------------------------- |
| `PS_HP_BITS`             | 128             | `system_wrapper.bd` 的 `PSU__SAXIGP2...5__DATA_WIDTH`；对应 HP0～HP3 |
| `PS_HP_ADDR_BITS`        | 40              | 当前 Zynq PS HP 主口地址宽度；必须能覆盖已登记的 PS DDR 高地址段                      |
| `PL_DDR_AXI_BITS`        | 128             | 当前 DDR4 XCI 的 `DDR4_AXI_DATA_WIDTH=128`；HLS `kv_axi_t` 按它生成     |
| `PL_DDR_AXI_ADDR_BITS`   | 31              | 当前 MIG 地址宽度；对应 2 GiB 地址块                                        |
| `PL_DDR_UI_CLOCK_HZ`     | 266,500,000     | 当前 XCI UI 配置；不是板载 200 MHz 参考时钟                                  |
| `PL_DDR_INPUT_PERIOD_PS` | 5003            | 约 200 MHz 的 MIG 参考输入                                            |
| `PL_USER_CLOCK_HZ`       | 100,000,000（目标） | 当前实现优先保证 100 MHz；最终以 XDC/实现报告为准                                 |
| `PS_DDR_REGIONS`         | 见下表             | 当前 BD 把 PS 4 GiB 表现为两个 2 GiB 段，不能按单一连续区间处理                      |

当前 BD 的 PS DDR 段登记为：

| **region** | **起始地址**      | **大小**              | **备注**             |
| ---------- | ------------- | ------------------- | ------------------ |
| `DDR_LOW`  | `0x00000000`  | `0x80000000`（2 GiB） | 低地址段               |
| `DDR_HIGH` | `0x800000000` | `0x80000000`（2 GiB） | 高地址段；重新生成 BD 后必须复核 |

PL DDR 的物理 DQ 宽度为 32 bit，但当前 MIG AXI 用户口为 128 bit。`PL_DDR_PHY_BITS` 和 `PL_DDR_AXI_BITS` 必须作为两个独立字段，不能用一个 `width` 字段代替。

#### 2.5.3 只读硬件 profile

M02 启动时读取只读 `hardware_profile_v2`，M03/M04/M09/M10 只能使用 profile 中的值，不在模块内部写死板卡参数：

```c
struct hw_mem_region_v2 {
    uint64_t base;
    uint64_t bytes;
    uint16_t phy_bits;
    uint8_t  memory_kind;   // 0=PS_DDR, 1=PL_DDR
    uint8_t  flags;
};

struct hardware_profile_v2 {
    uint32_t profile_version;
    uint32_t board_part_id;       // manifest 同时保存可读器件名
    uint32_t ps_ref_clock_hz;
    uint32_t pl_ddr_ref_clock_hz;
    uint32_t pl_ddr_ui_clock_hz;
    uint32_t pl_user_clock_hz;
    uint32_t ps_hp_bits;
    uint32_t ps_hp_addr_bits;
    uint32_t pl_ddr_axi_bits;
    uint32_t pl_ddr_axi_addr_bits;
    uint32_t ps_ddr_region_count;
    uint32_t flags;               // DDR ready、MIG calibrated、reset released
    uint64_t ps_ddr_capacity_bytes;
    uint64_t pl_ddr_capacity_bytes;
    struct hw_mem_region_v2 ps_ddr_regions[2];
    struct hw_mem_region_v2 pl_ddr_region;
};
```

`hardware_profile_v2.flags` 建议定义为：bit0=`PS_DDR_READY`，bit1=`MIG_CALIBRATED`，bit2=`RESET_RELEASED`，bit3=`HP_WIDTH_MATCH`，bit4=`MIG_AXI_WIDTH_MATCH`；其余位保留为 0。M02 只有在必需位全部为 1 时才把计算 IP 标记为可用。

该 profile 是 M02/M15 的硬件识别信息，不放进每次模块调用的 `common_job_v2`；它变化时更新 manifest 和 `build_config`，不改变 tensor layout。

### 2.6 公共状态码

| **值** | **名称**              | **通俗解释**     | **常见触发条件**           |
| ----- | ------------------- | ------------ | -------------------- |
| 0     | `OK`                | 成功           | 全部处理完成               |
| 1     | `BAD_ABI`           | 接口版本不匹配      | `abi_version != 2`   |
| 2     | `BAD_DIMENSION`     | 维度/长度不合法     | Decode 行数不是 1        |
| 3     | `BAD_ALIGNMENT`     | 地址没有按要求对齐    | 128-bit/64-byte 对齐失败 |
| 4     | `BAD_ADDRESS_RANGE` | 地址越界         | 有效范围超过容量或 DDR 区间     |
| 5     | `BAD_LAYOUT`        | 数据排列方式不匹配    | Q 接口收到 ACT 布局        |
| 6     | `BAD_LAYER`         | 层号不合法        | `layer_id >= 24`     |
| 7     | `BAD_TOKEN`         | token 不合法    | `token_id >= 151936` |
| 8     | `BAD_ALIAS`         | 不允许的输入输出地址重叠 | residual 输入被提前覆盖     |
| 9     | `NUMERIC_ERROR`     | 数值异常         | 非法 scale、NaN/Inf 异常  |
| 10    | `DRIVER_TIMEOUT`    | IP 超时        | 到时仍未完成               |
| 11    | `BAD_FLAGS`         | 出现未定义标志位     | `flags` 含未知 bit      |
| 12    | `INTERNAL_ERROR`    | 内部错误         | 无法归入以上类型             |

## 3. 公共调用字段

### 3.1 `common_job_v2`

```c
struct common_job_v2 {
    uint32_t abi_version;
    uint32_t job_id;
    uint32_t run_mode;
    uint32_t valid_rows;
    uint32_t flags;
};
```

| **字段**        | **方向** | **含义**             | **合法值/规则**            |
| ------------- | ------ | ------------------ | --------------------- |
| `abi_version` | PS→PL  | 本次调用所用寄存器和数据语义版本   | V2 必须为 2              |
| `job_id`      | PS→PL  | 本次模块调用所属的全局任务编号    | 同一推理任务保持一致；不能用作地址     |
| `run_mode`    | PS→PL  | Prefill 或 Decode   | 0/1                   |
| `valid_rows`  | PS→PL  | 本次真正需要处理的 token 行数 | Prefill 1～64；Decode=1 |
| `flags`       | PS→PL  | 可选控制位              | 未定义位必须为 0             |

建议公共 `flags` 位：

| **bit** | **名称**                   | **含义**              |
| ------- | ------------------------ | ------------------- |
| 0       | `FLAG_ENABLE_OUTPUT_CRC` | 计算并返回输出 CRC         |
| 1       | `FLAG_ENABLE_PERF`       | 开启详细性能计数            |
| 2       | `FLAG_DEBUG_SNAPSHOT`    | 允许 M15 截取指定小范围数据    |
| 3       | `FLAG_STRICT_CHECK`      | 执行完整地址、布局和 alias 检查 |
| 4～31    | 保留                       | 必须写 0               |

模块专用标志不能与公共位冲突，应在模块说明中定义；未定义标志返回 `BAD_FLAGS`。

### 3.2 `common_result_v2`

```c
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

| **字段**                | **方向**   | **含义**         | **使用要求**             |
| --------------------- | -------- | -------------- | -------------------- |
| `status_code`         | PL→PS    | 执行结果           | 非 0 时 PS 不得把输出当成有效数据 |
| `processed_rows`      | PL→PS    | 实际成功处理的行数      | 成功时应等于 `valid_rows`  |
| `perf_cycles_total`   | PL→PS    | 从启动到完成的总周期     | 包括等 AXI、计算和写回        |
| `perf_cycles_compute` | PL→PS    | 核心计算活跃周期       | 不包含纯等待；定义要在模块内固定     |
| `perf_read_beats`     | PL→PS    | AXI 实际读拍数      | 按端口实际 beat 计数        |
| `perf_write_beats`    | PL→PS    | AXI 实际写拍数      | 按端口实际 beat 计数        |
| `output_crc`          | PL→PS    | 有效输出范围的 CRC    | 未开启 CRC 时写 0         |
| `build_config`        | PL→PS/只读 | 当前 IP 的综合配置身份证 | 不随 job 改变            |

逻辑上的 `result` 可以映射为一组 AXI-Lite 只读寄存器，不要求 IP 向 DDR 写一个 C 结构体。

## 4. `build_config` 详细说明

### 4.1 它是什么

`build_config` 是一个 32-bit 只读值，用来说明这个 bitstream 里的某个 IP 是按什么性能参数综合出来的。它回答的是“板子上现在是哪一版硬件”，不是“本次运行想采用什么参数”。

它主要用于：

* M02 启动时识别 IP；
* 确认软件、驱动和 bitstream 是否配套；
* 区分同一 ABI 下的 8-lane、16-lane、不同 tile 版本；
* 给性能数据加上可追溯标签；
* 出现问题时确认实际烧录版本。

`build_config` 不用于传递 `valid_rows`、地址、层号或运行模式，也不能在运行时改写。

### 4.2 位定义

| **bit** | **字段**            | **含义**             | **建议编码**                                                                          |
| ------- | ----------------- | ------------------ | --------------------------------------------------------------------------------- |
| 0～3     | `PAR_LANES_CODE`  | 主并行 lane 数         | 0=未声明，1=8，2=16，3=32                                                               |
| 4～9     | `ROW_TILE`        | 一次片上并行处理的 token 行数 | 直接保存 1～63；0 表示不适用                                                                 |
| 10～17   | `MAIN_TILE`       | 模块主要 tile 大小       | 直接保存 1～255；具体含义由模块定义                                                              |
| 18～21   | `NUMERIC_IMPL_ID` | 数值实现版本             | 0=标准/基准，其他值查模块表                                                                   |
| 22～27   | `CLOCK_CODE`      | PL 用户逻辑/HLS 目标时钟档位 | 建议 0=100MHz，1=125MHz，2=150MHz，3=200MHz；不表示板载 PS 33.333333MHz 或 PL DDR 200MHz 参考输入 |
| 28～31   | `MODULE_REVISION` | 模块内部实现修订号          | 0～15                                                                              |

`MAIN_TILE` 的模块语义：

| **模块**        | **`MAIN_TILE` 表示**               |
| ------------- | -------------------------------- |
| M05 Embedding | burst beat 数或 0（必须在 manifest 声明） |
| M06 RMSNorm   | reduction 分块宽度                   |
| M07 QKV       | `H_TILE`                         |
| M08 RoPE      | D 维 tile                         |
| M09 KV Update | PL DDR burst/tile                |
| M10 Attention | `KV_TILE`                        |
| M11 AttnOut   | `H_TILE`                         |
| M12 Residual  | burst beat 数                     |
| M13 SwiGLU    | `MID_TILE`                       |
| M14 LM Head   | hidden tile                      |

模块负责人必须同时提供解码表。若某个参数超过字段可表达范围，不得截断；应升级编码方案或在扩展 build 信息寄存器中表达。

### 4.3 与 ABI 的区别

* `abi_version` 变化：字段、地址布局、调用语义发生不兼容改变，软件必须适配；
* `build_config` 变化：接口不变，只是并行度、tile、数值实现或时钟不同，通常不需要重写 PS 调用流程；
* `module_revision` 变化：同一模块内部实现修订，但仍遵守当前 ABI。

### 4.4 启动检查

M02 在系统启动时应依次读取：

```text
module_id → abi_version → capabilities → build_config → self_check
```

检查失败时，该 IP 标为不可用，不进入推理。M15 的每份性能报告都应记录 `build_config`。

### 4.5 当前工程状态

当前 `ip_registry` 只有 `name/baseaddr/device_id/available`，现有公共 IP 接口尚未统一提供上述 `build_config`。因此本文定义属于 V2 要实施的新增只读字段，不应误认为当前 bitstream 已支持。

## 5. Buffer Descriptor 详细说明

### 5.1 它是什么

Buffer descriptor（缓冲区描述符）是一张“内存使用单”。它不保存 tensor 数据，而是告诉 M01、M02、M03：数据在哪里、最多有多大、这次哪一段有效、是什么格式、现在由 CPU 还是 PL 持有，以及是不是最新一代数据。

```c
struct buffer_desc_v2 {
    uint64_t phys_addr;
    uint32_t capacity_bytes;
    uint32_t valid_offset;
    uint32_t valid_bytes;
    uint16_t layout_id;
    uint8_t  dtype;
    uint8_t  owner;
    uint32_t generation;
    uint32_t flags;
};
```

### 5.2 字段说明

| **字段**           | **含义**         | **规则**                     | **错误示例**                  |
| ---------------- | -------------- | -------------------------- | ------------------------- |
| `phys_addr`      | buffer 起始物理地址  | PL 能访问；满足端口/缓存对齐           | 把普通虚拟地址直接交给 PL            |
| `capacity_bytes` | 整块 buffer 的总容量 | 分配后通常不变                    | 把有效长度误写成容量                |
| `valid_offset`   | 本次有效数据距起始地址的偏移 | `offset <= capacity`       | 从未对齐偏移开始突发访问              |
| `valid_bytes`    | 本次真正有效的字节数     | `offset+bytes <= capacity` | Decode 仍标记 36 行有效         |
| `layout_id`      | tensor 的线性排列方式 | 必须与模块端口要求一致                | ACT 布局冒充 Q head-major     |
| `dtype`          | 单元素类型          | V2 推理外部通常是 BF16            | 权重是 FP16 却标为 BF16         |
| `owner`          | 当前谁写过、谁可直接读    | 按所有权状态机迁移                  | PL 写后 CPU 未 invalidate 就读 |
| `generation`     | 内容版本号          | 每次生产者完成写入后递增               | 消费者读到上一层旧数据               |
| `flags`          | buffer 属性      | 只允许已定义 bit                 | 可写区错误标为只读                 |

### 5.3 `owner` 所有权

建议冻结编号：

| **值** | **名称**          | **含义**                | **下一步常见操作**                 |
| ----- | --------------- | --------------------- | --------------------------- |
| 0     | `OWNER_INVALID` | 未初始化                  | 禁止提交                        |
| 1     | `CPU_CLEAN`     | CPU 可读，cache 与 DDR 一致 | CPU 可读；PL 读无需额外写回           |
| 2     | `CPU_DIRTY`     | CPU 改过，DDR 可能还是旧数据    | PL 读前 clean 有效范围            |
| 3     | `PL_READABLE`   | 已保证 PL 可读到最新数据        | 可启动 PL 读                    |
| 4     | `PL_WRITTEN`    | PL 刚写完，CPU cache 可能陈旧 | CPU 读前 invalidate；PL 可直接继续读 |
| 5     | `IMMUTABLE`     | 权重/常量，加载后不再修改         | 首次 clean 后长期复用              |

典型迁移：

```text
CPU 填数据：CPU_DIRTY
    └─M03 clean(valid range)──► PL_READABLE
                                  └─PL 只读：状态不变

PL 写输出：PL_WRITTEN，generation++
    ├─下一个 PL 模块读：只做完成依赖，不做 invalidate
    └─CPU 要读：M03 invalidate(valid range)──► CPU_CLEAN

权重加载：CPU_DIRTY ──一次 clean──► IMMUTABLE
```

### 5.4 `generation`

`generation` 用于发现“地址没变但内容已经换代”的情况。例如 hidden ping buffer 在第 0 层和第 2 层可能使用同一地址，但 generation 不同。

规则：

* 新分配 buffer 可从 1 开始；0 表示尚无有效内容；
* CPU 完成一份新内容时递增；
* PL 成功写完输出时递增；
* 消费者在提交时记录期望 generation；
* 实际 generation 不符时不得继续执行；
* 32-bit 回绕应按“不相等即失配”处理，不用大小比较。

### 5.5 建议的 `buffer flags`

| **bit** | **名称**              | **含义**                      |
| ------- | ------------------- | --------------------------- |
| 0       | `BUF_READ_ONLY`     | 本次调用禁止写入                    |
| 1       | `BUF_WRITE_ONLY`    | 不要求保留旧内容                    |
| 2       | `BUF_ALLOW_INPLACE` | 仅当模块 capability 同时允许时可原地写   |
| 3       | `BUF_CPU_CACHED`    | PS 通过 cache 访问，需要 M03 维护一致性 |
| 4       | `BUF_PL_DDR`        | 位于 PL DDR，不走普通 PS cache 维护  |
| 5       | `BUF_SCATTER`       | 有效数据由区间表描述，不是单连续段           |
| 6       | `BUF_DEBUG_GUARD`   | Debug 构建包含保护区/canary        |
| 7～31    | 保留                  | 必须为 0                       |

### 5.6 有效长度例子

BF16 每元素 2 byte：

| **数据**          | **公式**       | **Prefill T=36** | **Decode T=1** |
| --------------- | ------------ | ---------------- | -------------- |
| Hidden/Residual | `T×896×2`    | 64,512 B         | 1,792 B        |
| Q               | `14×T×64×2`  | 64,512 B         | 1,792 B        |
| 单个 K 或 V block  | `2×T×64×2`   | 9,216 B          | 256 B          |
| K+V 更新          | `2×2×T×64×2` | 18,432 B         | 512 B          |

Decode 时 M03 只能 clean/invalidate 1 行实际范围，不能因为底层 buffer 容量很大就处理整块容量。

### 5.7 当前工程状态

当前 `fpga_buffer_t` 只有 `addr` 和 `bytes`，buffer pool 使用固定静态数组，`fpga_flush_buffer()` 和 `fpga_invalidate_buffer()` 按传入的整个 `bytes` 操作。当前没有 `layout_id`、`owner`、`generation` 和有效区间状态。V2 的 M03 是在现有 `fpga_buffers` 基础上的结构化升级。

## 6. M00 Host/TCP Protocol 字段说明

### 6.1 责任

M00 负责接收网络包、验证包、建立任务、返回接受/完成/错误结果。M00 不直接写 IP 寄存器，不执行 tensor 转换，不管理 KV Cache。

### 6.2 V2 通用包头

建议固定为显式序列化格式：

```c
struct protocol_header_v2 {
    uint8_t  magic[8];
    uint16_t protocol_version;
    uint16_t command;
    uint32_t flags;
    uint32_t payload_bytes;
    uint64_t sequence_id;
    uint32_t payload_crc32;
    uint32_t header_crc32;
};
```

| **字段**             | **含义**        | **校验**                |
| ------------------ | ------------- | --------------------- |
| `magic`            | 协议识别串         | 必须完全匹配请求 magic        |
| `protocol_version` | 网络协议版本        | V2 为 2；与 HLS ABI 分开管理 |
| `command`          | 命令编号          | 必须是已支持命令              |
| `flags`            | 包级控制          | 未定义位为 0               |
| `payload_bytes`    | 后续 payload 长度 | 不超过服务端预分配容量           |
| `sequence_id`      | 上位机请求序号       | 用于匹配应答和识别重复包          |
| `payload_crc32`    | payload 校验    | 空 payload 也使用约定 CRC   |
| `header_crc32`     | 包头校验          | 计算时该字段按 0 处理          |

### 6.3 命令和 payload

| **命令**           | **主要请求字段**                      | **主要响应字段**                   |
| ---------------- | ------------------------------- | ---------------------------- |
| `HELLO`          | `protocol_version`、客户端能力        | 服务端版本、最大包长、能力                |
| `LOAD_MODEL`     | `manifest_id`、加载 flags          | `model_handle`、权重校验结果        |
| `CREATE_SESSION` | 请求的 `session_id` 或自动分配标志        | 最终 `session_id`              |
| `RUN_PREFILL`    | session、token\_count、token\_ids | accepted、`job_id`            |
| `RUN_DECODE`     | session、max\_new\_tokens、采样配置   | accepted、`job_id`            |
| `GET_STATUS`     | `job_id`                        | 状态、进度、错误模块                   |
| `GET_PERF`       | `job_id`、查询范围                   | M15 记录                       |
| `ABORT`          | `job_id`                        | 是否已进入安全停止状态                  |
| `RESET_SESSION`  | `session_id`                    | KV/history 是否清除成功            |
| `GET_BUILD_INFO` | 可选 module\_id                   | ABI、capability、build\_config |

`RUN_PREFILL` token 数组长度必须与 `token_count×4` 一致。`RUN_DECODE` 中的采样参数若第一版只支持 argmax，其他采样模式应明确返回“不支持”，不能静默忽略。

### 6.4 与当前工程的对应

当前包头是 `magic/request_id/opcode/flags/payload_bytes/reserved0`；已有高层 `RUN_GENERATE=104`，由 TCP 层转交 scheduler。当前包头没有独立 `protocol_version` 和 CRC32，V2 字段是统一集成时的目标升级。

## 7. M01 Scheduler/Runtime 字段说明

### 7.1 `inference_job_v2`

```c
struct inference_job_v2 {
    uint32_t job_id;
    uint32_t session_id;
    uint32_t mode;
    uint32_t token_count;
    uint32_t start_position;
    uint32_t max_new_tokens;
    uint32_t model_handle;
    uint32_t debug_flags;
};
```

| **字段**           | **含义**                  | **规则**                             |
| ---------------- | ----------------------- | ---------------------------------- |
| `job_id`         | 一次高层推理任务编号              | 由 M00/M01 分配，全流程唯一                 |
| `session_id`     | 会话编号                    | 关联 KV Cache、history 和当前位置          |
| `mode`           | 初始任务模式                  | `PREFILL` 或 `DECODE`               |
| `token_count`    | 本次输入 token 数            | Prefill >0；纯 Decode 可为 1 个起始 token |
| `start_position` | 本 block 第一个 token 的绝对位置 | `start+rows <= 2048`               |
| `max_new_tokens` | 最多生成多少新 token           | 不包含输入 prompt                       |
| `model_handle`   | M04 成功发布的模型实例           | 必须处于 READY                         |
| `debug_flags`    | 任务级 trace/snapshot 控制   | 生产版本默认 0                           |

### 7.2 M01 维护的会话状态

| **字段**                  | **含义**               | **更新时机**                         |
| ----------------------- | -------------------- | -------------------------------- |
| `layer_id`              | 当前执行层                | 每完成一层加 1                         |
| `cache_len`             | 当前每层可读取的 KV 总长度      | block/单 token 全层成功后更新            |
| `current_token`         | 下一轮 Decode 的输入 token | LM Head 选出后更新                    |
| `generated_len`         | 已生成 token 数          | 每次 LM Head 成功后加 1                |
| `stop_token_id`         | EOS/停止 token         | 命中后完成任务                          |
| `state`                 | 状态机状态                | Embedding、Layer、Final Head 等阶段切换 |
| `expected_generation[]` | 各输入应有的 buffer 版本     | 提交模块前检查                          |

### 7.3 调度规则

Prefill：按最多 64 行切 block，执行 Embedding，然后对 24 层按 M06→M07→M08→M09→M10→M11→M12→M06→M13→M12 的顺序运行，最后一行进入 Final RMS 和 M14。

Decode：`valid_rows=1`，对新 token 执行相同的 24 层链路；成功后 `cache_len++`，再执行 Final RMS 和 M14，直至 EOS、数量达到上限、abort 或错误。

M01 只决定“谁先谁后、用哪块 buffer、参数是什么”，不实现各模块的数学公式。

### 7.4 当前工程状态

当前 scheduler 已有 Prefill/Decode 状态机和模块耗时统计；当前最大 prompt 为 36，Prefill 一次处理整个 prompt，层间串行执行。V2 目标是将 block 上限统一为 64，并通过 descriptor 管理 generation 和有效范围。

## 8. M02 IP Registry/Driver 字段说明

### 8.1 `ip_entry_v2`

```c
struct ip_entry_v2 {
    uint16_t module_id;
    uint16_t instance_id;
    uint32_t expected_abi;
    uint64_t ctrl_base;
    uint32_t irq_id;
    uint32_t timeout_class;
    uint32_t capabilities;
    const struct ip_ops_v2 *ops;
};
```

| **字段**          | **含义**            | **规则**                            |
| --------------- | ----------------- | --------------------------------- |
| `module_id`     | M05～M14 等逻辑模块编号   | 同类功能固定编号                          |
| `instance_id`   | 同模块的物理实例号         | 单实例为 0；拆 Prefill/Decode 后区分实例     |
| `expected_abi`  | 驱动期望的 IP ABI      | 必须与 IP 只读 ABI 相等                  |
| `ctrl_base`     | AXI-Lite 控制寄存器基地址 | 来自 xparameters/硬件设计               |
| `irq_id`        | 完成中断号             | 不使用中断时采用约定无效值                     |
| `timeout_class` | 超时档位编号            | 映射到时间，不直接把毫秒散落在 wrapper 中         |
| `capabilities`  | IP 能力位图           | Scheduler 据此选择路径                  |
| `ops`           | 统一驱动操作表           | 指向 probe/configure/start/wait 等函数 |

### 8.2 `capabilities`

| **bit** | **名称**                  | **含义**                      |
| ------- | ----------------------- | --------------------------- |
| 0       | `DYNAMIC_ROWS`          | 支持运行时 `valid_rows`          |
| 1       | `DEBUG_CRC`             | 支持输出 CRC                    |
| 2       | `DEBUG_SNAPSHOT`        | 支持受控中间快照                    |
| 3       | `IRQ_COMPLETE`          | 支持完成中断                      |
| 4       | `INPLACE_ALLOWED`       | 至少一种经过验证的原地模式               |
| 5       | `ONLINE_SOFTMAX`        | Attention 使用在线 softmax      |
| 6       | `PL_DDR_DIRECT`         | 可直接访问 PL DDR                |
| 7       | `WRITE_LOGITS_OPTIONAL` | LM Head 可关闭完整 logits 写回     |
| 8       | `DUAL_RUN_MODE`         | 单 IP 内有 Prefill/Decode 两套调度 |
| 9～31    | 保留                      | 必须为 0                       |

### 8.3 统一驱动过程

| **操作**        | **输入**        | **输出**               | **作用**            |
| ------------- | ------------- | -------------------- | ----------------- |
| `probe`       | `ip_entry`    | 是否存在、ID/ABI/build 信息 | 识别硬件              |
| `self_check`  | 可选测试参数        | 状态                   | 做轻量自检             |
| `configure`   | 模块参数和地址       | 状态                   | 只写寄存器，不做 cache 操作 |
| `start`       | 无/控制位         | 状态                   | 启动 IP             |
| `wait`        | timeout class | 完成/超时                | 中断或退避轮询           |
| `read_result` | 无             | `common_result_v2`   | 读取状态和性能           |
| `reset`       | 原因            | 状态                   | 超时或错误后恢复          |

M03 必须在 `configure/start` 前完成 buffer 所有权转换。M02 不允许各 wrapper 再各自猜测并清理整个 buffer。

### 8.4 当前工程状态

当前 registry 只有 `name/baseaddr/device_id/available`，具体 IP 操作散布在 `op_*.c` wrapper 中。V2 要把 ABI、能力、超时和统一操作表补齐。

## 9. M03 Memory/Buffer Manager 接口说明

### 9.1 建议 API

```c
int buffer_alloc(uint32_t capacity, uint32_t alignment,
                 uint16_t layout_id, uint8_t dtype,
                 uint32_t flags, buffer_desc_v2 *out);

int buffer_set_valid(buffer_desc_v2 *buf,
                     uint32_t offset, uint32_t bytes);

int buffer_prepare_pl_read(buffer_desc_v2 *buf,
                           uint32_t expected_generation);

int buffer_prepare_pl_write(buffer_desc_v2 *buf);

int buffer_mark_pl_written(buffer_desc_v2 *buf,
                           uint32_t produced_bytes);

int buffer_prepare_cpu_read(buffer_desc_v2 *buf,
                            uint32_t expected_generation);

int buffer_check_alias(const buffer_desc_v2 *a,
                       const buffer_desc_v2 *b,
                       uint32_t alias_policy);
```

每个 API 都要检查 64-bit 地址加法溢出、`offset+bytes` 越界、对齐、owner 和 generation。cache 操作范围向下/向上对齐到 cache line，但统计字段保存实际处理和对齐后处理的字节数。

### 9.2 Alias 规则

| **生产者输出**              | **消费者**                  | **初版规则**   |
| ---------------------- | ------------------------ | ---------- |
| Embedding/上一层 hidden   | RMSNorm                  | 不原地        |
| RMSNorm 输出             | QKV                      | QKV 只读     |
| QKV Q/K/V              | RoPE/KV Update           | Q、K、V 各自独立 |
| RoPE Q/K               | Attention/KV Update      | 独立输出       |
| Attention 输出           | AttnOut                  | 只读         |
| AttnOut 输出 + residual0 | Residual                 | 两输入与输出不重叠  |
| Residual1              | Post RMS、最终 MLP residual | 必须保留       |
| SwiGLU 输出 + residual1  | Residual                 | 不重叠        |

以后只有当 M02 capability 和模块验证同时声明安全时，才能允许 in-place。

## 10. M04 SD Weight Store/Manifest 字段说明

### 10.1 Manifest 顶层

| **字段**                | **类型**     | **含义**          | **规则**        |
| --------------------- | ---------- | --------------- | ------------- |
| `format_version`      | u32        | manifest 文件格式版本 | V2 为 2        |
| `abi_version`         | u32        | 权重与模块接口所需 ABI   | V2 为 2        |
| `model`               | object     | 模型常量集合          | 必须与公共头文件一致    |
| `files`               | array      | 权重/表文件列表        | 所有必需文件均存在且唯一  |
| `manifest_id`         | string/u32 | 模型包身份           | 建议由内容 hash 派生 |
| `build_compatibility` | object     | 可兼容的布局/数值实现     | 与 M02 启动检查配合  |

### 10.2 单个文件项

| **字段**        | **含义**    | **规则**                      |
| ------------- | --------- | --------------------------- |
| `name`        | 相对文件名     | 禁止目录越界                      |
| `module_id`   | 使用该权重的模块  | 如 M07/M13                   |
| `layer_id`    | 层号        | 共享权重使用约定无效值                 |
| `tensor_role` | 权重角色      | 如 qkv\_w、rms\_input、w\_gate |
| `dtype`       | 数据类型      | 通常 bf16                     |
| `layout`      | 物理布局名称/ID | 必须与模块端口一致                   |
| `bytes`       | 文件准确字节数   | 必须非 0，且等于期望公式               |
| `sha256`      | 内容摘要      | 边读取边验证                      |
| `target_addr` | 目标地址或分配策略 | 必须落入允许的 DDR 区间              |

M04 全部文件成功且统一 clean 后才发布 `model_handle=READY`；任一文件失败，不能让 M01 使用半套权重。

## 11. M05 Token Embedding 接口字段

```c
void embedding_v2(token_ids, table, hidden_out,
                  run_mode, valid_rows, hidden_size, vocab_size,
                  abi_version, job_id, flags, result);
```

| **参数**        | **方向/布局**            | **含义**               | **校验**            |
| ------------- | -------------------- | -------------------- | ----------------- |
| `token_ids`   | 入，`TOKEN_U32_V2 [T]` | token 编号数组           | 每项 `< vocab_size` |
| `table`       | 入，`VOCAB_VH_V2`      | 共享词表权重               | BF16、immutable    |
| `hidden_out`  | 出，`ACT_TH_V2`        | 查表得到的 hidden         | 容量≥`T×896×2`      |
| `run_mode`    | 入                    | Prefill/Decode       | Decode 时 T=1      |
| `valid_rows`  | 入                    | token 数              | 1～64              |
| `hidden_size` | 入                    | 每行维度                 | 必须为 896           |
| `vocab_size`  | 入                    | 词表行数                 | 必须为 151936        |
| 公共字段          | 入/出                  | ABI、job、flags、result | 按第 3 章            |

每个 token 读取词表中一行 1792 byte，输出同样大小；不缓存整个词表。

## 12. M06 Dynamic RMSNorm 接口字段

```c
void rmsnorm_v2(x, weight, y,
                run_mode, valid_rows, hidden_size, eps, norm_role,
                abi_version, job_id, flags, result);
```

| **参数**        | **方向/布局**     | **含义**         | **校验**                 |
| ------------- | ------------- | -------------- | ---------------------- |
| `x`           | 入，`ACT_TH_V2` | 待归一化 hidden    | BF16，有效 T 行            |
| `weight`      | 入，`[896]`     | RMSNorm scale  | BF16、immutable         |
| `y`           | 出，`ACT_TH_V2` | 归一化结果          | 初版禁止与 x 重叠             |
| `run_mode`    | 入             | Prefill/Decode | 0/1                    |
| `valid_rows`  | 入             | 实际行数           | Decode=1               |
| `hidden_size` | 入             | H              | 896                    |
| `eps`         | 入             | 防止除零的小量        | 必须为正且有限                |
| `norm_role`   | 入             | 权重角色           | 0=input，1=post，2=final |

`norm_role` 只用于检查、统计和选择权重，不改变 RMSNorm 数学公式。

## 13. M07 QKV Projection 接口字段

```c
void qkv_projection_v2(x, w_qkv, bias_qkv, q_raw, k_raw, v_out,
                       run_mode, valid_rows, hidden_size, layout_id,
                       abi_version, job_id, flags, result);
```

| **参数**      | **方向/布局**           | **含义**      | **校验**                |
| ----------- | ------------------- | ----------- | --------------------- |
| `x`         | 入，`ACT_TH_V2`       | RMSNorm 输出  | `[T,896]`             |
| `w_qkv`     | 入，`W_OG32_I_L32_V2` | 合并 Q/K/V 权重 | O=1152、I=896          |
| `bias_qkv`  | 入，合并输出顺序            | Q/K/V bias  | 1152 个 BF16           |
| `q_raw`     | 出，`Q_HTD_V2`        | 未做 RoPE 的 Q | `[14,T,64]`           |
| `k_raw`     | 出，`KV_HTD_V2`       | 未做 RoPE 的 K | `[2,T,64]`            |
| `v_out`     | 出，`KV_HTD_V2`       | V           | `[2,T,64]`            |
| `layout_id` | 入                   | 权重布局        | 必须为 `W_OG32_I_L32_V2` |
| 其余公共参数      | 入/出                 | 模式、行数、ABI 等 | Decode 仅一行            |

合并输出编号：0～895 为 Q，896～1023 为 K，1024～1151 为 V。模块直接写 head-major，PS 不再转置。

## 14. M08 Block RoPE 接口字段

```c
void rope_v2(q_raw, k_raw, cos_table, sin_table, q_rot, k_rot,
             run_mode, valid_rows, position_base, max_position,
             abi_version, job_id, flags, result);
```

| **参数**          | **方向/布局**      | **含义**               | **校验**                           |
| --------------- | -------------- | -------------------- | -------------------------------- |
| `q_raw`         | 入，`Q_HTD_V2`   | Q 输入                 | `[14,T,64]`                      |
| `k_raw`         | 入，`KV_HTD_V2`  | K 输入                 | `[2,T,64]`                       |
| `cos_table`     | 入，`ROPE_SD_V2` | cos 表                | 至少覆盖所需位置                         |
| `sin_table`     | 入，`ROPE_SD_V2` | sin 表                | 与 cos 同版本                        |
| `q_rot`         | 出，`Q_HTD_V2`   | 旋转后的 Q               | 不改变布局                            |
| `k_rot`         | 出，`KV_HTD_V2`  | 旋转后的 K               | 不改变布局                            |
| `position_base` | 入              | 本 block 首 token 绝对位置 | 0～2047                           |
| `max_position`  | 入              | 表可用位置数/上界            | `base+T <= max_position <= 2048` |

一次调用处理整个 block，禁止 PS 按 token 循环启动 IP。

## 15. M09 KV Cache Update 接口字段

```c
void kv_cache_update_v2(k_new, v_new, k_cache, v_cache,
                        run_mode, layer_id, start_pos, valid_rows,
                        max_sequence, abi_version, job_id, flags,
                        cache_len_after, result);
```

| **参数**            | **方向/布局**       | **含义**                | **校验**                       |
| ----------------- | --------------- | --------------------- | ---------------------------- |
| `k_new`           | 入，`KV_HTD_V2`   | 新 K block             | `[2,T,64]`                   |
| `v_new`           | 入，`KV_HTD_V2`   | 新 V block             | `[2,T,64]`                   |
| `k_cache`         | 出，`KVC_LHSD_V2` | PL DDR K Cache        | 与 V 区域不重叠                    |
| `v_cache`         | 出，`KVC_LHSD_V2` | PL DDR V Cache        | 与 K 区域不重叠                    |
| `run_mode`        | 入               | 写 block 或单 token      | Decode=1 行                   |
| `layer_id`        | 入               | 写入哪一层                 | 0～23                         |
| `start_pos`       | 入               | 第一个新 token 的 cache 位置 | 0～2047                       |
| `valid_rows`      | 入               | 连续写入 token 数          | `start+rows <= max_sequence` |
| `max_sequence`    | 入               | cache 每 head 容量       | 2048                         |
| `cache_len_after` | 出               | 成功写完后的可见长度            | 通常 `max(old_len,start+rows)` |

地址公式：`(((layer×2+kv_head)×2048+position)×64+dim)`。只有所有 K/V 写响应完成后，才能更新 `cache_len_after` 和 generation。

`k_cache`/`v_cache` 的逻辑元素仍是 BF16，但外部 beat 使用 `hardware_profile_v2.pl_ddr_axi_bits`。当前工程为 128 bit；开发板 PL DDR 的 32 bit 是物理 DQ 宽度，两者不能混写。

## 16. M10 GQA Online-Softmax Attention 接口字段

```c
void attention_v2(q_rot, k_cache, v_cache, attn_out,
                  run_mode, layer_id, query_pos_base, valid_rows,
                  cache_len, scale, causal,
                  abi_version, job_id, flags, result);
```

| **参数**           | **方向/布局**       | **含义**                | **校验**                |
| ---------------- | --------------- | --------------------- | --------------------- |
| `q_rot`          | 入，`Q_HTD_V2`    | RoPE 后的 Query         | `[14,T,64]`           |
| `k_cache`        | 入，`KVC_LHSD_V2` | 指定层 K Cache           | 至少有 `cache_len` 个有效位置 |
| `v_cache`        | 入，`KVC_LHSD_V2` | 指定层 V Cache           | generation 与 K 匹配     |
| `attn_out`       | 出，`ACT_TH_V2`   | GQA 输出                | `[T,896]`             |
| `run_mode`       | 入               | Prefill/Decode 调度     | Decode=1              |
| `layer_id`       | 入               | 读取的 cache 层           | 0～23                  |
| `query_pos_base` | 入               | 第一个 query 的绝对位置       | `qpos=base+t`         |
| `valid_rows`     | 入               | Query 行数              | Prefill 1～64；Decode=1 |
| `cache_len`      | 入               | 当前允许访问的 key/value 总长度 | 1～2048                |
| `scale`          | 入               | QK 缩放                 | 默认 `1/sqrt(64)=0.125` |
| `causal`         | 入               | 是否屏蔽未来位置              | 0/1；生产推理为 1           |

Q head 0～6 使用 KV head 0，Q head 7～13 使用 KV head 1。Prefill 和 Decode 使用相同接口；前者复用多个 query，后者只保留一组在线 softmax 状态。两种模式均不输出完整 attention score/weight 矩阵。

M10 读取 PL DDR 前必须检查 `mig_calibrated=1`、K/V generation 一致、`cache_len` 不超过 2048；AXI beat 宽度由 profile 提供，不能在模块内部直接按开发板的 32 bit 物理总线假设。

## 17. M11 Attention Out Projection 接口字段

```c
void attention_out_v2(x, weight, y,
                      run_mode, valid_rows, hidden_size, layout_id,
                      abi_version, job_id, flags, result);
```

| **参数**      | **方向/布局**           | **含义**           | **校验**              |
| ----------- | ------------------- | ---------------- | ------------------- |
| `x`         | 入，`ACT_TH_V2`       | M10 输出           | `[T,896]`           |
| `weight`    | 入，`W_OG32_I_L32_V2` | Wo               | O=896、I=896         |
| `y`         | 出，`ACT_TH_V2`       | Attention 线性投影结果 | `[T,896]`           |
| `layout_id` | 入                   | 权重布局             | V2 固定 packed layout |
| 其余公共参数      | 入/出                 | 模式、行数、ABI 等      | Decode=1 行          |

## 18. M12 Residual Add 接口字段

```c
void residual_add_v2(a, b, y,
                     run_mode, valid_rows, hidden_size, residual_role,
                     abi_version, job_id, flags, result);
```

| **参数**          | **方向/布局**     | **含义**       | **校验**                              |
| --------------- | ------------- | ------------ | ----------------------------------- |
| `a`             | 入，`ACT_TH_V2` | 新分支输出        | `[T,896]`                           |
| `b`             | 入，`ACT_TH_V2` | 保留的 residual | `[T,896]`                           |
| `y`             | 出，`ACT_TH_V2` | BF16 加法结果    | 初版与 a/b 均不重叠                        |
| `residual_role` | 入             | 本次加法位置       | 0=Attention residual，1=MLP residual |
| 其余公共参数          | 入/出           | 模式、行数、ABI 等  | H=896                               |

`residual_role` 用于统计和检查，不改变 `y=a+b` 的数学定义。

## 19. M13 Dynamic Tiled SwiGLU 接口字段

```c
void swiglu_v2(x, w_gate, w_up, w_down, y,
               run_mode, valid_rows, hidden_size, intermediate_size,
               layout_id, abi_version, job_id, flags, result);
```

| **参数**              | **方向/布局**       | **含义**      | **校验**             |
| ------------------- | --------------- | ----------- | ------------------ |
| `x`                 | 入，`ACT_TH_V2`   | Post RMS 输出 | `[T,896]`          |
| `w_gate`            | 入，packed layout | Gate 权重     | O=4864、I=896       |
| `w_up`              | 入，packed layout | Up 权重       | O=4864、I=896       |
| `w_down`            | 入，packed layout | Down 权重     | O=896、I=4864       |
| `y`                 | 出，`ACT_TH_V2`   | SwiGLU 最终输出 | `[T,896]`          |
| `run_mode`          | 入               | 选择多行或单行调度   | Prefill=0，Decode=1 |
| `valid_rows`        | 入               | 实际 token 行数 | Decode=1，不补算其他行    |
| `hidden_size`       | 入               | H           | 896                |
| `intermediate_size` | 入               | I           | 4864               |
| `layout_id`         | 入               | 三组权重布局      | `W_OG32_I_L32_V2`  |

生产接口不包含完整 gate/up/mid 输出；这些中间量只能通过受限 Debug snapshot 查看。Prefill 与 Decode 共用权重和 MAC，按 `run_mode` 选择 `ROW_TILE>1` 或 `ROW_TILE=1` 调度。

## 20. M14 LM Head / Penalty / Argmax 接口字段

```c
void lm_head_v2(hidden, shared_vocab_weight, history_bitmap,
                optional_logits, hidden_size, vocab_size,
                run_mode, write_logits, enable_penalty,
                repetition_penalty, abi_version, job_id, flags,
                selected_token, selected_score, result);
```

| **参数**                | **方向/布局**       | **含义**                  | **校验**                    |
| --------------------- | --------------- | ----------------------- | ------------------------- |
| `hidden`              | 入，单行 ACT        | 最后 token 的 final RMS 输出 | 896 个 BF16                |
| `shared_vocab_weight` | 入，`VOCAB_VH_V2` | 与 Embedding 共享的词表权重     | `[151936,896]`            |
| `history_bitmap`      | 入，bitmap        | 已出现 token 集合            | 至少 `ceil(V/32)` words     |
| `optional_logits`     | 可选出             | 完整词表分数                  | `write_logits=0` 时可为空/不访问 |
| `hidden_size`         | 入               | H                       | 896                       |
| `vocab_size`          | 入               | V                       | 151936                    |
| `run_mode`            | 入               | 来源模式                    | 两种模式都只消费最后一行              |
| `write_logits`        | 入               | 是否写完整 logits            | 生产默认 0                    |
| `enable_penalty`      | 入               | 是否启用重复惩罚                | 0/1                       |
| `repetition_penalty`  | 入               | 惩罚系数                    | 启用时必须为正且有限，通常 ≥1          |
| `selected_token`      | 出               | 最大分数 token              | 并列时选较小 ID                 |
| `selected_score`      | 出               | 被选 token 的最终分数          | FP32                      |

`write_logits=0` 时仍必须完成 argmax，但不得向 `optional_logits` 产生大规模写流量。

## 21. M15 Debug/Performance 字段说明

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

| **字段**                   | **含义**             | **说明**              |
| ------------------------ | ------------------ | ------------------- |
| `job_id`                 | 关联的任务              | 与公共 job 一致          |
| `module_id`              | 哪个模块               | M05～M14 或扩展编号       |
| `layer_id`               | 哪一层                | 非分层模块使用约定值 `0xFFFF` |
| `valid_rows`             | 实际处理行数             | 不能填最大容量代替           |
| `status`                 | 模块结果               | 采用公共状态码             |
| `ps_start/ps_end`        | PS 侧时间戳            | 必须注明计时频率            |
| `pl_cycles_total`        | PL 总周期             | 与 common result 一致  |
| `pl_cycles_compute`      | PL 计算周期            | 定义需固定               |
| `read_beats/write_beats` | AXI 数据拍            | 要注明端口 beat 宽度       |
| `cache_clean_bytes`      | M03 clean 字节数      | 建议同时记录实际和对齐后范围      |
| `cache_invalidate_bytes` | M03 invalidate 字节数 | PL→PL 应为 0          |
| `input_crc/output_crc`   | 数据检查值              | Debug/抽检使用          |

每条记录还应关联 `build_config`、bitstream ID 和 model manifest ID；可以放在任务级公共头中，避免每条重复存储。

## 22. 模块间接口对照表

| **上游**     | **输出 descriptor**              | **下游**            | **下游关键参数**             |
| ---------- | ------------------------------ | ----------------- | ---------------------- |
| M00        | `inference_job_v2`             | M01               | session、mode、token 数   |
| M04        | 权重 descriptors + model\_handle | M01/M03           | layout、dtype、immutable |
| M05        | hidden `ACT_TH_V2`             | M06               | T、H、generation         |
| M06 Input  | norm `ACT_TH_V2`               | M07               | T、H                    |
| M07        | Q/K/V descriptors              | M08/M09           | head-major、T           |
| M08        | q\_rot/k\_rot                  | M10/M09           | position、generation    |
| M09        | PL DDR KV Cache                | M10               | layer、cache\_len       |
| M10        | attention `ACT_TH_V2`          | M11               | T、H                    |
| M11        | projection `ACT_TH_V2`         | M12               | residual role 0        |
| M12 #1     | residual1                      | M06 Post / M12 #2 | 必须保留到第二次加法             |
| M06 Post   | normalized hidden              | M13               | T、H                    |
| M13        | MLP output                     | M12 #2            | residual role 1        |
| M12 #2/最后层 | hidden                         | M06 Final         | 只取最后有效行                |
| M06 Final  | final hidden                   | M14               | 单行 896                 |
| M14        | token/score                    | M01               | 更新 history 和 decode 状态 |

## 23. PS 写寄存器的统一顺序

为避免 IP 读到半套参数，建议所有计算 IP 使用以下顺序：

1. M01 生成模块调用参数；
2. M03 检查输入/输出 descriptor、alias 和 generation；
3. M03 对 CPU\_DIRTY 输入 clean 有效范围；
4. M02 检查 IP ABI、capability 和可用状态；
5. M02 先写所有地址的低/高 32 bit；
6. 写维度、layer、position、mode、flags；
7. 清除上一次完成/错误状态；
8. 最后写 start；
9. 中断或退避轮询等待完成；
10. 读取 status、processed\_rows、性能和 CRC；
11. 成功后由 M03 标记输出 `PL_WRITTEN` 并递增 generation；
12. 只有 CPU 要读取时才 invalidate；若直接给下一个 PL IP，不做 cache 操作。

任何一步失败都要记录 `job_id/module_id/layer_id/status/build_config`，并停止依赖该输出的后续模块。

## 24. 地址和范围校验公式

对每个连续 descriptor，必须满足：

```text
phys_addr != 0
capacity_bytes > 0
valid_offset <= capacity_bytes
valid_bytes <= capacity_bytes - valid_offset
phys_addr + valid_offset 不发生 64-bit 溢出
有效范围落在已登记的 DDR 区间
起始地址满足模块要求的对齐
```

两个范围 `[a0,a1)`、`[b0,b1)` 重叠条件：

```text
a0 < b1 && b0 < a1
```

只有 capability 和本次 alias policy 都允许时，重叠才合法。

## 25. Prefill/Decode 的统一接口规则

1. M05～M14 都保留 `run_mode`；
2. Decode 的 token 维模块必须 `valid_rows=1`；
3. Prefill 的 `valid_rows=1～64`，T=1 可用于边界测试；
4. 两种模式使用相同 dtype、布局、权重、状态码和驱动参数结构；
5. Decode 禁止读写第 1 行之后的数据；
6. M10、M13 第一版采用一个物理 IP、两种内部调度并共享计算资源；
7. 若以后拆为两个物理 IP，字段名称、顺序和语义保持一致，M01/M02 只根据 mode 选择 `ctrl_base`；
8. M03/M04 是管理模块，不要求 `run_mode`。

## 26. 当前工程到 V2 字段的对应关系

| **V2 概念**     | **当前工程已有内容**                                      | **主要缺口**                                                |
| ------------- | ------------------------------------------------- | ------------------------------------------------------- |
| M00 协议        | request magic、request\_id、opcode、flags、payload 长度 | 独立版本、CRC、统一命令 payload                                   |
| M01 Scheduler | Prefill/Decode 状态机、layer/cache/token 状态、耗时        | 64 行分 block、统一 job、descriptor generation                |
| M02 Registry  | name、baseaddr、device\_id、available                | expected ABI、capability、timeout、ops、build\_config       |
| M03 Buffer    | addr、bytes、固定 pool、flush/invalidate               | valid range、layout、dtype、owner、generation、alias planner |
| 公共结果          | 部分 wrapper 状态/耗时                                  | 统一 status、processed rows、周期、beat、CRC                    |
| 双模式字段         | 调度层区分 Prefill/Decode                              | 所有计算 IP 的统一 `run_mode/valid_rows` 寄存器                   |

## 27. 模块负责人交付时必须填写的接口清单

每个 M05～M14 模块交付时，应附一页机器可核对的表：

| **项目** | **必填内容**                              |
| ------ | ------------------------------------- |
| 模块身份   | module\_id、instance\_id、模块名称、revision |
| 版本     | abi\_version、build\_config 解码结果       |
| 能力     | capabilities 位图                       |
| 控制寄存器  | 偏移、位宽、读写属性、复位值                        |
| 数据端口   | 端口名、AXI 宽度、bundle、连接 HP/PL DDR        |
| 每个地址参数 | layout、dtype、最小容量、对齐、读/写属性            |
| 维度参数   | 合法范围和固定值                              |
| 模式     | Prefill/Decode 是否共用实现、模式检查规则          |
| flags  | 每一位定义，未定义位处理                          |
| 结果     | 状态码、性能计数、CRC 定义                       |
| alias  | 哪些地址允许/禁止重叠                           |
| 超时     | timeout class 和最坏测试时间                 |
| 数值     | FP32/BF16 转换、近似实现 ID、误差门槛             |
| 测试     | T=1/36/64、错误参数、边界地址、两种模式              |

接口表不完整的模块不能进入最终统一集成；汇总人不应通过阅读模块内部源码来猜测字段语义。

## 28. 需要架构负责人最终冻结的项目

以下项目在写入公共头文件前需要由两位架构负责人共同确认一次，之后模块负责人不得自行修改：

1. enum 的最终数值：module、layout、dtype、owner、capability；
2. `flags` 的公共位和各模块保留区；
3. M00 网络包字节序、CRC 多项式和最大 payload；
4. 所有 AXI-Lite 寄存器偏移；
5. `build_config` 中 lane、clock、numeric ID 的最终映射；
6. 物理地址范围和 PS DDR/PL DDR 分配；
7. 超时 class 对应的实际时间；
8. BF16 舍入、NaN/Inf 和近似数学误差标准；
9. 是否允许任何 in-place；
10. Debug snapshot 的最大长度和生产版关闭方式。

冻结后生成同一份公共 C/C++ 头文件、HLS 头文件、驱动寄存器说明和测试端协议定义，避免四处手工复制。

## 29. AXU9EGB 硬件核查后的字段调整

本节是结合开发板手册和当前 `system_wrapper.bd`/DDR4 XCI 后新增的板级约束。它不改变 M05～M14 的数学接口，但补齐了容量、位宽、时钟、地址段和校准状态，防止把“器件规格”误当成“当前 bitstream 配置”。

### 29.1 需要区分的三种宽度

| **名称**            | **当前值** | **人话解释**                                 | **不能替代的字段**       |
| ----------------- | ------- | ---------------------------------------- | ----------------- |
| `PS_DDR_PHY_BITS` | 64      | 板上 PS DDR4 芯片到 ZU9EG 的物理 DQ 宽度           | `PS_HP_BITS`      |
| `PS_HP_BITS`      | 128     | PS HP 端口每个 AXI beat 的宽度，由 Vivado PS 配置决定 | `PS_DDR_PHY_BITS` |
| `PL_DDR_PHY_BITS` | 32      | 板上 PL DDR4 的物理 DQ 宽度                     | `PL_DDR_AXI_BITS` |
| `PL_DDR_AXI_BITS` | 128     | 当前 MIG 给 HLS/SmartConnect 的 AXI 用户口宽度    | `PL_DDR_PHY_BITS` |

因此：

* `ap_uint<128>` 是当前 PS HP/PL DDR AXI 的工程接口选择，不是说开发板上的每颗 DDR 芯片都直接输出 128 bit；
* PL DDR 物理 32 bit 不能让 `kv_axi_t` 自动变成 32 bit，`kv_axi_t` 应读取 `hardware_profile_v2.pl_ddr_axi_bits`；
* HLS IP 的 32 bit 或 512 bit M\_AXI 仍可能通过 SmartConnect/width converter 接到 128 bit HP，外部 ABI 不应跟着某个 IP 的内部端口宽度漂移。

### 29.2 板卡事实、工程配置和必须验证项

| **项目**      | **手册/工程信息**                                    | **字段或动作**                                       |
| ----------- | ---------------------------------------------- | ----------------------------------------------- |
| 器件          | `XCZU9EG-2FFVB1156I`                           | `board_part_id` 和 manifest 器件字符串                |
| PS DDR4     | 4 GiB、64 bit、BANK504                           | `ps_ddr_capacity_bytes`、`ps_ddr_regions[]`      |
| PL DDR4     | 2 GiB、32 bit、BANK64/65                         | `pl_ddr_capacity_bytes`、`pl_ddr_phy_bits`       |
| PS 参考时钟     | 33.333333 MHz                                  | `ps_ref_clock_hz`；不写入 `CLOCK_CODE`              |
| PL DDR 参考时钟 | 200 MHz 差分                                     | `pl_ddr_ref_clock_hz`                           |
| 当前 MIG AXI  | 128 bit、2 GiB 地址块                              | `pl_ddr_axi_bits=128`、`pl_ddr_axi_addr_bits=31` |
| 当前 MIG UI   | 266.5 MHz                                      | `pl_ddr_ui_clock_hz`；不要和 200 MHz 参考输入混淆         |
| 当前 HP       | HP0～HP3 均 128 bit                              | `ps_hp_bits=128`；来自 BD，不是手册结论                   |
| 当前 HP 地址宽度  | 40 bit                                         | `ps_hp_addr_bits=40`；用于覆盖高地址 DDR 段              |
| 当前用户逻辑目标    | 100 MHz 优先                                     | `pl_user_clock_hz`；以 XDC/实现报告最终确认               |
| 复位          | 板上外部 RESET 低有效                                 | 仍需读取 BD 导出的复位极性和释放时序                            |
| DDR 型号/速度级别 | 手册存在 `...GE`、`...-062E` 等写法；当前 XCI 为 `...-075` | M04/集成以实际 BOM、XCI 和校准结果为准，不把 2400 Mbps 写成硬性实测值  |

### 29.3 PS DDR 地址必须按多个区间检查

当前 BD 的 PS DDR 地址段为：

```text
DDR_LOW  : [0x00000000, 0x80000000)   // 2 GiB
DDR_HIGH : [0x800000000, 0x880000000) // 2 GiB
```

`buffer_desc_v2.phys_addr + valid_offset + valid_bytes` 必须完整落在某一个 region 内。M03 不得用“起始地址小于 4 GiB”作为唯一合法性判断，也不能让一个 burst 跨越两个 region。重新生成 BD、修改 PS DDR 映射或启用 Linux reserved-memory 后，应重新导出这张表。

### 29.4 KV Cache 容量和对齐

按 `KVC_LHSD_V2=[24][2][2048][64]` 计算：

```text
一个 K cache = 24×2×2048×64×2 bytes = 12 MiB
一个 V cache = 24×2×2048×64×2 bytes = 12 MiB
K+V 总计    = 24 MiB
```

这只是满序列的逻辑容量，不包含 tile、双缓冲、debug snapshot 和对齐余量。M03 要为 K、V 分配不重叠的 PL DDR 区域；M09 写入前检查 `layer_id/head/position` 范围；M10 读取前检查同一 generation 和 `cache_len`。

### 29.5 权重容量的板级预算

按 V2 形状、BF16、Embedding 与 LM Head 共享权重的理论值估算：

| **内容**                   | **估算大小**    |
| ------------------------ | ----------- |
| 词表/Embedding（共享 LM Head） | 约 259.7 MiB |
| 24 层 QKV                 | 约 47.3 MiB  |
| 24 层 Attention Out       | 约 36.8 MiB  |
| 24 层 Gate/Up/Down        | 约 598.5 MiB |
| Norm、bias 及少量表           | 小于 1 MiB 量级 |
| 合计（未计文件头和额外 padding）     | 约 942 MiB   |

4 GiB PS DDR 在理论上可以容纳上述权重、激活和运行时 buffer，但 M04 仍必须按实际 manifest 文件大小、32 元素分组 padding、地址段和 Linux/固件保留区做最终分配；如果 LM Head 不共享 Embedding，还要额外预留约 259.7 MiB。

### 29.6 M02 启动返回的硬件 profile 字段

除每个 IP 的 `ip_entry_v2` 外，M02 应提供一次只读板级探测结果：

| **字段**                  | **方向**  | **含义**           | **验收规则**                  |
| ----------------------- | ------- | ---------------- | ------------------------- |
| `profile_version`       | M02→M01 | profile 结构版本     | 与驱动支持版本一致                 |
| `board_part_id`         | M02→M01 | 器件/板卡标识          | 必须匹配 `XCZU9EG-2FFVB1156I` |
| `ps_ref_clock_hz`       | M02→M01 | PS 输入参考频率        | 记录约 33.333333 MHz         |
| `pl_ddr_ref_clock_hz`   | M02→M01 | PL DDR 参考输入      | 记录 200 MHz                |
| `pl_ddr_ui_clock_hz`    | M02→M01 | MIG UI 时钟        | 与 XCI/状态寄存器一致             |
| `pl_user_clock_hz`      | M02→M01 | HLS/AXI 用户逻辑频率   | 与 XDC/实现报告一致              |
| `ps_hp_bits`            | M02→M01 | HP0～HP3 的 AXI 宽度 | 当前应为 128                  |
| `ps_hp_addr_bits`       | M02→M01 | HP 主口地址宽度        | 当前应为 40，能覆盖 `DDR_HIGH`    |
| `pl_ddr_phy_bits`       | M02→M01 | PL DDR 物理 DQ 宽度  | 当前应为 32                   |
| `pl_ddr_axi_bits`       | M02→M01 | PL DDR AXI 用户口宽度 | 当前应为 128                  |
| `pl_ddr_axi_addr_bits`  | M02→M01 | PL DDR AXI 地址宽度  | 当前应为 31                   |
| `ps_ddr_regions[]`      | M02→M01 | PS DDR 可访问区间     | 每段 base/bytes 合法且不重叠      |
| `ps_ddr_capacity_bytes` | M02→M01 | PS DDR 总容量       | 当前约 4 GiB；与 region 总和核对   |
| `pl_ddr_capacity_bytes` | M02→M01 | PL DDR 总容量       | 当前约 2 GiB                 |
| `ddr_ready`             | M02→M01 | PS DDR 已就绪       | 未就绪时禁止加载权重                |
| `mig_calibrated`        | M02→M01 | PL DDR 校准完成      | 未完成时禁止 M09/M10            |
| `reset_released`        | M02→M01 | 用户逻辑复位已正确释放      | 不满足时 IP 标记不可用             |

### 29.7 对现有字段和计划的具体修订

1. `EXTERNAL_BEAT_BITS=128` 保持不变，但字段说明改为“当前 BD 配置”；如果未来 HP 改宽，必须由 profile、manifest 和 `build_config` 同步报告。
2. `CLOCK_CODE` 只编码 PL 用户逻辑/HLS 目标时钟；33.333333 MHz 和 200 MHz 参考输入另行记录。
3. `phys_addr` 的范围校验从单区间改为 `ps_ddr_regions[]`/`pl_ddr_region`；错误仍返回 `BAD_ADDRESS_RANGE`。
4. M09/M10 的 `kv_axi_t` 默认当前 128 bit，但代码设计必须接受 profile 生成的宽度，不能把“PL 物理 32 bit”写进 HLS 接口。
5. M02 的 `probe/self_check` 在所有模块集成前增加 DDR ready、MIG calibration、HP/MIG 宽度和 reset 检查；模块负责人交付包增加硬件 profile 摘要。
6. 性能报告增加 `board_part_id`、`ps_hp_bits`、`pl_ddr_axi_bits`、`pl_user_clock_hz`、`pl_ddr_ui_clock_hz`，这样不同 bitstream/板卡的结果才可比较。

### 29.8 本次核查结论

现有 ABI、tensor layout、固定 32 元素物理分组和 Prefill/Decode 双模式不需要推翻；需要调整的是板级字段和验收流程：把 PS/PL DDR 容量、物理总线宽度、AXI 用户口宽度、分段地址、参考/UI/用户时钟、DDR 校准状态全部纳入统一 profile。这样后续优化 M07、M10、M13、M14 时只改内部并行参数，不会因为误把 32 bit、128 bit、200 MHz 或 100 MHz 混为同一个“硬件宽度/频率”而返工。
