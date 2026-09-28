# AXU9EGB LM Head 性能分析与优化方案

分析日期：2026-09-16。对象：本仓库 Qwen2.5-0.5B Module 16、Vitis HLS/Vivado/Vitis 2021.1。

本文基于本地源码、导出 IP 的综合报告、生成 RTL、Vivado 连接和 2026-07-25 的板上验收记录。没有重新连接板卡、运行综合或执行新的性能测试。若当前板上已换用其他 bitstream，应先重新建立版本与测量基线。

## 1. 结论

现有 LM Head 的主要瓶颈是单个 FP32 累加器的循环依赖：点积循环 II=8，外层词表循环顺序执行。当前板上为 100 MHz，综合最大周期数 1,097,890,446 换算得到 10.9789 秒；历史客户端请求时间为 11.0902 秒，两者非常接近。

推荐顺序：分段计时 → 交错累加、II=1 → 128 位连续读 + 8 路乘加 + 片上分 bank → 数据流重叠 → 150/200 MHz 实现验证。多 HP、PL DDR、量化属于后续阶段。

当前内核仅使用 5/2520 个 DSP。低资源占用反映并行度低，并不意味着 ZU9EG 的能力已经耗尽。

## 2. 证据及计时口径

| 项目 | 核查结果 | 本地依据 |
|---|---|---|
| 权重 | 151936 × 896、FP16、272269312 bytes | `include/lm_head_kernel.hpp`、板端 `lmh_buffers.h` |
| 内层 II | target 1、achieved 8、iteration latency 18 | `build/lm_head_export/solution1/syn/report/lm_head_argmax_Pipeline_dot_product_csynth.rpt` |
| 依赖根因 | HLS 200-880，accumulator 的 carried dependence | `build/lm_head_export/solution1/solution1.log` |
| 外层 | vocab_loop 未流水，最大约 7226 cycles/词元 | `lm_head_argmax_csynth.rpt` |
| 综合周期 | 最大 1097890446 cycles | 同上 |
| 时钟 | HLS 约束 5 ns；实际系统 PL0 100 MHz | `run_export_ip.tcl`、`realFpga/vivado/create_lm_head_axu9eg_bd.tcl` |
| 权重 AXI | 外部 DATA_WIDTH=32，内部 USER_DW=16 | 导出 IP `syn/verilog/lm_head_argmax.v` |
| Burst | 权重循环已推导出 16 位变量长度 burst；max_read_burst_length=256、outstanding=16 | 综合日志和生成 RTL |
| PS 端口 | HP0 已是 128 位；四个 HLS master 汇入同一个 HP0 | Vivado 生成 PS RTL、BD Tcl |
| 片上输入缓存 | hidden_cache 为单端口 BRAM | `src/lm_head_kernel.cpp` |
| 原始实测 | 八步平均 run_seconds=11.0901731 | `realFpga/DEBUG_LOG.md` 阶段 H-8 |

当前源码与交付包 `hls/src/lm_head_kernel.cpp` 的 SHA256 相同：
`C3646E958783D9A1DAA94A1668D3F78382EE0FDCAEEE8416878EDFC3407E0D0C`。
这能关联本地源码和交付包，不能代替对当前板上 bitstream 的版本确认。

### 计时口径需要更正

验收摘要把 11.09 秒称作 FPGA time，但原始日志列名是 `run_seconds`。在 `tools/run_module16_board_trace.py` 中，它包围整个 `client.run_token()`，包含请求发送、板端处理、硬件执行和响应接收。

板端 `lwip_lm_head_raw_server.c` 在 `Start()` 前、`IsDone()` 后用 XTime 计时，产生 `hw_time_us`，通过串口输出：

```text
LMH1 RUN_TOKEN id=... token=... hw_us=... logits=...
```

该值目前没有放进 LMH1 响应，Python 的 TokenResult 也没有此字段。板端计时还包含少量 MMIO 启动/轮询检测开销，不是纯 PL 周期计数。

因此：可以判断计算调度是主因，但不能把 11.0902−10.9789=0.1113 秒全部归为网络，也不能把推算的约 99% 当作实测占比。HLS 数字包含其调度假设，真实 AXI 等待和开关路径需要实际计时确认。

## 3. 工作量与带宽模型

每次计算最后一个 token 的输出：

```text
logits = W @ hidden
W: [151936, 896]
hidden: [896]
```

- 点积项数：136134656 MAC；按一乘一加计算，约 272.27 MFLOP。
- 每步权重逻辑读量：272269312 bytes = 259.65625 MiB。
- hidden：1792 bytes；完整 history bitmap：18992 bytes；完整 raw logits：303872 bytes。
- 权重传至 DDR 后可跨 token 复用，但每次 hidden 不同，PL 仍需从 DDR 重新扫描权重。
- 权重远大于本板片上存储，不适合将整个 LM Head 权重放进 BRAM；片上空间应用于 hidden、history、权重 tile 和累加器。

当前按端到端时间折算，仅约 12.28 MMAC/s、0.02455 GFLOP/s，权重有效消耗速率约 24.55 MB/s。这里的有效速率不是 DDR 峰值实测，也不包含可能的总线放大。

单累加器理论吞吐：100 MHz / 8 = 12.5 MMAC/s，和上述值吻合。

若有 U 路计算、循环实际 II 为 I、时钟为 f：

```text
Tcompute >= 136134656 × I / (U × f)
Tmemory  >= 272269312 / 实测有效权重带宽
Tkernel  >= max(Tcompute, Tmemory) + 尚未被重叠隐藏的开销
```

最后一个公式假设读与算能重叠；没有 DATAFLOW/双缓冲时，可能接近相加。

| 权重有效带宽（十进制 GB/s） | 单次读完整 FP16 权重的下限 |
|---:|---:|
| 0.2 | 1.361 s |
| 0.4 | 0.681 s |
| 0.8 | 0.340 s |
| 1.0 | 0.272 s |
| 1.6 | 0.170 s |
| 2.0 | 0.136 s |
| 2.4 | 0.113 s |
| 3.2 | 0.085 s |

HP0 为 128 bit，100 MHz 理论为 1.6 GB/s；200 MHz 理论为 3.2 GB/s。这里是端口峰值，实效受 DDR 仲裁、burst、backpressure 和其他主设备影响。将 HLS 端口改为 512 位不能突破同频单个 128 位 HP0 的上限。

## 4. 各个瓶颈的具体含义

### 4.1 FP32 加法依赖是第一瓶颈

当前内层是：

```cpp
accumulator += activation * coefficient;
```

每轮依赖上一轮的 accumulator。综合日志已确认这条真实依赖导致 II=8。仅添加 `PIPELINE II=1` 不会消除依赖；不能用 `DEPENDENCE inter false` 隐藏真实依赖来强迫调度。

外层逐个计算 151936 行，当前没有多个词元的点积同时执行。

### 4.2 数据通路会限制下一阶段吞吐

当前权重 AXI 是 32 位外部接口、16 位元素访问；已存在 burst，不能断言每个 FP16 都是一笔独立 DDR 请求。实际 ARLEN、ARSIZE、RVALID/RREADY 需要总线测量。

四个 gmem bundle 最终共享 HP0，并不是四个独立 DDR 通道。权重是绝大部分读流量；先改善单权重通路，再决定是否拆多 HP。

### 4.3 单端口 hidden_cache 无法直接支持 8 个不同索引读取

如果将 hidden 维直接 UNROLL=8，而仍保留单端口 RAM，则缓存端口会限制 II。必须同时将片上缓存按 lane 分 bank，或采用宽字缓存一次读取 8 个 half。

### 4.4 系统没有在 HLS 目标频率运行

HLS 的 5 ns 是调度约束，Vivado Tcl 的 PL0 实际是 100 MHz。保留同一调度提高到 200 MHz，理想约 5.49 秒，仍然慢。

综合 Estimated period=3.650 ns 不是板上可直接运行 274 MHz 的保证。必须检查新系统的实现时序、时钟、复位和 DDR 路径；不能只看 HLS 估计，也不能把 100 MHz 的正 WNS 当作 200 MHz 已验收。

### 4.5 网络不是当前最先应升级的部分

权重上传历史约 7.692 秒，为一次性冷启动成本。客户端已有显式 `--load-weight` 开关；当前代码不是自动每 token 重传权重。

正式生成只需 hidden/history 和 token/score；完整 logits 回传用于调试。303872 bytes 的千兆网纯数据理论时间约 2.43 ms，实际包含软件栈和分包开销，不能由这个理论值代替实测。

现有客户端 penalty 关闭时仍可发送完整 history；可以改为空历史来减少约 19 KB 传输，但这不是解决 11 秒瓶颈的主要手段。缓存维护也没有在每个正常 RUN_TOKEN 中 flush 全部权重；应保留必要的数据一致性操作。

## 5. 分阶段实施方案

### P0：补齐性能测量，建立可比较基线

1. 固定完整 shape、同一权重、同一测试 step；记录源码/IP/bit/XSA/ELF 标识、时钟、工具版本。
2. 一次上传权重，保持同一 TCP 连接，重复请求至少 30 次；将首次请求和上传时间单独报告。
3. 记录 median、p95：host RTT、板端 hw_us、输入复制/cache、输出/cache、logits 发送。已有串口 hw_us 可先直接利用，避免立即改协议。
4. 正式扩展可增加版本化 STATS 命令或 capability；不要直接改变旧 RESULT_PREFIX 的布局而不更新两端。
5. 分别测 penalty OFF/ON、logits OFF/ON；性能主表采用实际生产策略及 logits OFF，数值对拍时另开 logits。
6. 对 vocab=128、1024、8192、65536、151936，固定 hidden=896，观察时间线性项和固定开销。小词表只用于定位，不能作为完整 LM Head 加速成果。
7. 增加独立 DDR 顺序读取测试核，输出 checksum 防止 HLS 优化掉读取，测同一地址范围、同一 HP 路径的有效带宽；用 APM/ILA 观察突发长度、有效字节、等待和 backpressure。
8. 如果目标已达到毫秒级，关闭热路径逐请求串口日志；UART 和忙轮询此时才可能成为明显开销。超时建议改成真实时间 deadline，避免轮询次数随 CPU/AXI 频率变化。

### P1：单 lane + 16 路交错累加，先消除 II=8

以 K=16 个 FP32 partial sums 替换一个 accumulator，使同一个 partial 每 16 次迭代才更新一次。K 必须覆盖实际反馈延迟；16 是针对当前 8-cycle 依赖的保守起点，不是所有版本都保证成立的魔法数字。

概念示意（不是已经综合验证的替换代码）：

```cpp
float partial[16];
#pragma HLS ARRAY_PARTITION variable=partial complete
// 每行开始全部清零
for (int i = 0; i < 896; ++i) {
#pragma HLS PIPELINE II=1
    partial[i & 15] += float(hidden_cache[i]) * float(weight[row * 896 + i]);
}
// 用固定、明确的归约树合并 partial，再转换为 FP16。
```

要求：检查 HLS 是否正确识别 bank/索引依赖、是否 achieved II=1；必要时把循环结构改成工具能够明确分析的形式，不通过虚假 DEPENDENCE 绕过。

此时理想计算下限为 1.361 秒 @100 MHz。第一验收目标可设约 1.5～2 秒/完整调用，实际还取决于权重供给和行结束归约开销。这个版本的价值在于独立确认依赖消除收益，不是最终结构。

### P2：128-bit 权重读 + 8 lanes + 每 lane 16 个 partial

推荐首个正式优化架构：

```text
PS DDR → HP0 128 bit → 顺序 burst reader
                              ↓ FIFO / 双缓冲
                      8 个 FP16 权重/拍
                              ↓
hidden 8 banks → 8 路乘法 + FP32 交错累加
                              ↓
                    FP32 归约 → FP16 raw logit
                              ↓
              可选 penalty → argmax → token/score
                              └→ 调试时写 raw logits
```

参数起点：U=8，K=16，权重端口 `const ap_uint<128>*`，hidden cyclic partition factor=8，partial[8][16] 完全分区。

每行 896 个 half 恰为 112 个 128-bit word；每拍处理一个 word，lane 循环完全展开，word 循环目标 II=1。每个 partial 每 16 个 word 才更新一次，最后归约 128 个 FP32 partial。

存储和兼容性：

- 现有 FP16 行主序字节布局可原样保留，每行 1792 bytes，恰好 128-bit 对齐。现有共享缓冲区按 64 bytes 对齐。
- `ap_uint<128>` 的各 16-bit slice 必须按浮点位模式解释为 half，不能把位模式整数做数值转换。沿用经验证的 bit-cast 方式。
- 固定 896 的专用实现可减少动态边界开销。若还要支持 H=4 等调试 shape，应提供通用尾部处理或独立小尺寸配置；不能简单使用 hidden_size/8 使小测试变空循环。
- 新接口可能改变寄存器生成结果，必须核对 AXI-Lite offset，并重新生成驱动、XSA/平台/ELF；上层网络权重布局可保持不变。

数据流：将顺序 reader、dot/reduce、policy/write 分为可并发阶段。使用 stream 或 ping-pong tile，避免“读完整块→算完整块”串行。权重 tile 可从 32 行开始：32×896×2=57344 bytes，双缓冲 112 KiB；合理分 bank，避免不必要的完整数组分区。

处理每行结束归约不能在每个 partial 上串行停顿很久，否则 151936 次会累积明显开销。优先流水归约树、双组 partial、让下一行点积与上一行归约重叠。具体是否重叠，以 schedule 和 co-sim 为准。

先以 128-bit、burst length=16、outstanding=16 为试验起点，再测 32/64/256 等配置。AMD 文档指出 HP 接口会拆分超过 16 拍的 burst，重负载下可能影响性能。因此不能认为 burst 越长越快；比较的是 HP 侧实际事务与有效 GB/s。

这一版的计算下限约 170 ms @100 MHz，刚好对应单 HP0 理论带宽下限。若实效带宽只有 0.8 GB/s，仅读权重就需 340 ms。合理首轮工程目标为约 0.3～0.6 秒/完整调用，必须由新的板上测量确认。

### P3：在并行结构稳定后，评估 150/200 MHz

修改系统时钟而不仅是 HLS create_clock；核对 PS PL clock、HLS ap_clk、SmartConnect、HP aclk 和 reset 同步。若保留 100 MHz 控制域而独立提高数据/计算域，需要正确的时钟转换和复位设计。

跑完整 Vivado 实现和时序，必要时加寄存器级、减小扇出、调整 tile，而不是依靠 HLS Estimated period 宣称完成。

U=8、II=1、200 MHz 理想计算下限 85 ms；若有效带宽为 1.5～2.5 GB/s，权重读约 182～109 ms。可将约 0.15～0.30 秒设为下一阶段完整调用目标，但只有带宽、归约和时序同时满足才成立。

### P4：只有测量显示需要时，才扩展多端口/量化

- 两个真正独立的权重 master 分别接不同 HP，按词表行段分配数据；各自计算局部 argmax，再全局归并。仅增加 bundle 并仍连接同一 HP0 不会提供两个 HP 的吞吐。
- 多 HP 仍共享 PS DDR 和内部互连，不能按端口数保证线性加速。结合本芯片互连拓扑测组合，先确认单口接近饱和。
- PL DDR 是另一条可选路线，但要新增 DDR 控制器、引脚约束、权重装载路径和验收，不是第一轮必须工作。
- 权重 INT8 约 129.83 MiB、INT4 约 64.91 MiB，另计 scale/元数据。只有压缩访问和对应解量化/整数内核同时实现，才有容量和带宽收益；直接将 FP16 文件转整数不够。
- batch=1 的 LM Head 权重读取强度高；多独立会话 batching 可复用同一次权重读，但不能把同一条自回归序列尚未产生的未来 token 当作独立 batch。

## 6. 数值一致性是优化的验收条件

交错累加和归约树改变 FP32 求和顺序，不保证与旧逐项累加逐位相同。当前 trace 的 step 7 已有 FP16 同分：token 100013 与 100048 都可能为 20.203125。必须在转 FP16 后执行 policy 和 argmax，平局保留较小 token ID。

每版检查：

1. 全部 8-step 的 raw logits 最大/均方误差、Top-5、selected token、selected score。
2. penalty OFF/ON 分开验证；ON 要检查完整 processed scores，不能只比 token。
3. 构造 penalty 真正改变 Top-1 的用例；覆盖 FP16 平局、负 logits、全零 hidden、混合符号相消、历史 bitmap 边界、尾部尺寸。
4. 现有 0.02 阈值可作初始对照，出现偏差应分析归约顺序和 margin，不能为了通过自动放宽阈值。
5. 保留当前同分用例，扩展多 prompt/更长 decode 数据；八步全过不能证明所有输入语义一致。
6. 新结构 RTL co-sim 必须覆盖 U=8/K=16、多行、至少一次 accumulator bank 复用、跨 burst/跨 tile 和连续调用。例如 H=896、V=64 的确定性输入，可验证两个 32-row tile；原 4×4 不足以覆盖新结构。

若要求尽可能保持旧求和顺序，可采用“不同输出行交错”的替代结构：每 lane 维护至少 8 个不同词元行，依次更新这些行，但每行仍按 i=0..895 累加。U=8、8 个行上下文需要 64 行权重 tile，双缓冲约 224 KiB。通过 tile reader 保留 DDR 连续访问，片上重排调度；该方案比 partial reduction 复杂，但减少每行求和重排。仍需约束/核查浮点运算融合和舍入行为，最终以对拍为准。

## 7. 具体代码改动清单

| 文件 | 建议修改 |
|---|---|
| `module16_lm_head_hls/src/lm_head_kernel.cpp` | P1 partial；P2 packed reader、8 lanes、缓存分 bank、流水归约、DATAFLOW；可选 history 缓存 |
| `module16_lm_head_hls/include/lm_head_kernel.hpp` | U/K/tile 参数、packed 接口、固定与小尺寸配置 |
| `module16_lm_head_hls/tb/lm_head_tb.cpp` | 扩展多 lane、多 bank、跨 tile、平局和数值用例 |
| `module16_lm_head_hls/run_csynth.tcl`、`run_export_ip.tcl` | 独立优化 solution 和输出目录，记录 U/K/目标时钟；避免覆盖基线 |
| `realFpga/vivado/create_lm_head_axu9eg_bd.tcl` | 核查 128-bit 连接与转换器；后续改系统频率/新增 HP |
| `realFpga/vitis/workspace/lm_head_net_diag/src/lwip_lm_head_raw_server.c` | 暴露分段统计、日志开关、真实时间超时；保留必要 cache 管理 |
| `module16_lm_head_hls/net/cpu_client.py` | 版本化读取硬件统计、关闭 penalty 时允许空 history |
| `tools/run_module16_board_trace.py` | 持久连接多 step/重复 benchmark，分离上传、RTT、hw、对拍时间 |

先保留可回退的基线 bit/XSA/ELF/IP 和结果，再逐版导出、集成、对拍。不要跳过“新内核通过综合但板上仍加载旧 bitstream”的版本核对。

## 8. 阶段目标汇总

以下均为模型下限或工程目标，不是新实测，也不是完整 Qwen 模型 tokens/s。

| 阶段 | 参数 | 理想计算下限 | 建议完整调用目标 |
|---|---|---:|---:|
| 历史基线 | 单 lane，II=8，100 MHz | 综合约 10.979 s | 历史 RTT 约 11.090 s |
| P1 | 单 lane，K=16，II=1，100 MHz | 1.361 s | 1.5～2 s |
| P2 | 8 lanes，128 bit，II=1，100 MHz | 0.170 s | 0.3～0.6 s |
| P3 | P2 + 200 MHz | 0.085 s | 0.15～0.30 s，取决于 DDR 实效和时序 |

同频单个 HP0 的内存下限必须同时满足。达到目标后仍需与主机原生 LM Head、整条生成链路比较；模块快了不自动代表异构推理快于 Orin/GPU。

## 9. 外部技术依据

只使用 AMD 官方资料；具体实现能力以项目的 2021.1 工具验证为准。

- [UG1399 2021.1：ARRAY_PARTITION](https://docs.amd.com/r/2021.1-English/ug1399-vitis-hls/pragma-HLS-array_partition)：增加片上数组并发访问；不应将此指令直接用于顶层 M_AXI 权重数组来替代接口设计。
- [UG1399 2021.1：DATAFLOW](https://docs.amd.com/r/2021.1-English/ug1399-vitis-hls/pragma-HLS-dataflow)：使阶段重叠执行；FIFO 容量和死锁需通过 co-sim 检查。
- [AMD Wiki：Traffic Shaping of HP Ports on Zynq UltraScale+](https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/688128001/1000)：128-bit HP 接口、16-beat burst、较长 burst 的拆分及 issuing/QoS。

本次经验库按 HLS 检索无命中；结论来自项目证据和上述官方资料。
