# 模块 16 仿真阶段验证报告

## 结论

模块 16 的功能基线已经完成三层验证：真实 Qwen 数据的全尺寸 HLS C 仿真、综合后 RTL 的接口级联合仿真，以及 CPU↔TCP↔板端服务模拟器的端到端回环。三层均通过。

这不等于真实开发板已经验证：当前已经按 AXU9EGB 的精确 FPGA part 完成芯片级综合与 RTL 仿真，但还没有 PS 系统、以太网 MAC/TCP 栈、DDR4 数据通路和 bitstream。全尺寸串行核的估计性能也只有约 5.489 s/token，后续必须并行化。

## 环境与口径

- 工具：Xilinx Vitis HLS / Vivado 2021.1。
- 开发板：ALINX AXU9EGB。
- 精确目标器件：`XCZU9EG-2FFVB1156I`，Vivado part 为 `xczu9eg-ffvb1156-2-i`。
- 目标时钟：200 MHz（5 ns）。
- 板上资源：ZU9EG，2,520 DSP、274,080 LUT、548,160 FF、32.1 Mb BRAM；PS DDR4 4 GB/64 bit，PL DDR4 2 GB/32 bit；PS 与 PL 各一路千兆以太网。
- 当前 Vivado 能识别上述 part，但尚未安装 AXU9EGB board preset、厂商 XDC 与参考工程，所以本报告不声称已完成板级引脚和网口验证。
- 模型：Qwen2.5-0.5B-Instruct。
- LM Head：`[151936, 896] FP16 weight × [896] FP16 hidden`，FP32 累加后转 FP16。
- token 策略：对 FP16 raw logits 应用 repetition penalty 1.1，再执行 greedy argmax；分数相同保留较小 token ID。

## 1. 全尺寸 HLS C 仿真

8 个真实生成步骤一次加载官方权重后全部通过：

| step | token | max abs error | cosine | Top-5 |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 104198 | 0.0156250 | 1.0 | 5/5 |
| 1 | 48 | 0.0117188 | 1.0 | 5/5 |
| 2 | 16948 | 0.0078125 | 1.0 | 5/5 |
| 3 | 3837 | 0.0156250 | 1.0 | 5/5 |
| 4 | 67071 | 0.0117188 | 1.0 | 5/5 |
| 5 | 102661 | 0.0156250 | 1.0 | 5/5 |
| 6 | 99718 | 0.0078125 | 1.0 | 5/5 |
| 7 | 100013 | 0.0078125 | 1.0 | 5/5 |

判定：`HLS_CSIM_OVERALL=PASS`，token 8/8 完全匹配。

HLS 逐项累加与生成 trace 的 GPU GEMM 归约顺序不同，所以部分 FP16 位模式不完全相同；最大误差很小，Top-5 与最终 token 均一致。

## 2. 全尺寸 C 综合

| 指标 | 结果 |
| --- | ---: |
| 目标时钟 | 5.000 ns（200 MHz） |
| 估计时钟 | 3.650 ns（约 273.97 MHz） |
| 最大延迟 | 1,097,890,446 cycles / 5.489 s |
| BRAM18K | 14 / 1,824 |
| DSP | 5 |
| FF | 4,880 / 548,160 |
| LUT | 5,816 / 274,080 |
| URAM | 0 |

综合通过，但点积内层由于 FP32 累加依赖，自动流水达到的 II 为 8。资源占用低正是串行实现的结果，不能将其解读为性能良好。与先前 U280/4 ns 临时目标的 II=6 相比，ZU9EG/5 ns 下浮点加法流水更深，因此周期数增加；这反映器件与时钟约束变化，并非功能退化。

## 3. RTL co-simulation

Vitis 2021.1 会按 m_axi 的最大 depth 序列化测试向量；直接对 260 MiB 全尺寸权重做 RTL co-simulation 会先产生约 1.2 GiB 文本向量。因此采用 `LMH_COSIM_SMALL` 构建 4×4 同构核，验证相同的：

- 四路 m_axi 端口与 AXI-Lite 控制；
- FP16 输入、FP32 累加、FP16 输出；
- repetition penalty；
- argmax 与低 token ID 平局规则。

结果：以 `xczu9eg-ffvb1156-2-i` 和 5 ns 时钟生成 Verilog，XSim `Pass`，1/1 事务，延迟 542 cycles，`C/RTL co-simulation finished: PASS`。

这里的 542 cycles 只属于 4×4 接口级用例，不代表全尺寸性能。

## 4. TCP 端到端回环

真实 Qwen 的 8 个 trace 均经过 `127.0.0.1` TCP：CPU 客户端发送 hidden/history，板端服务模拟器计算并回传 token 与完整 FP16 logits。

| step | token | max abs error | Top-5 |
| ---: | ---: | ---: | ---: |
| 0 | 104198 | 0.00390625 | 5/5 |
| 1 | 48 | 0.00390625 | 5/5 |
| 2 | 16948 | 0.00390625 | 5/5 |
| 3 | 3837 | 0.00781250 | 5/5 |
| 4 | 67071 | 0.00781250 | 5/5 |
| 5 | 102661 | 0.00781250 | 5/5 |
| 6 | 99718 | 0.00781250 | 5/5 |
| 7 | 100013 | 0.00781250 | 5/5 |

判定：8/8 PASS，token 8/8 完全匹配，Top-5 全部 5/5。

协议单元测试另覆盖：帧收发、CRC32 错误拒绝、FP16 权重分块上传、PING/READY、重复惩罚和 argmax 平局。

## 后续工作

1. 安装 ALINX AXU9EGB board files/XDC，或从厂商参考设计提取 PS、DDR4、RGMII、时钟和复位约束。
2. 建立推荐数据路径：上位机 TCP → PS 千兆网/Linux A53 → PS DDR4/AXI HP(HPC) → PL HLS kernel → PS → TCP 回传。第一版优先使用 PS 网口，避免在 PL 中自行实现完整 TCP/IP 栈。
3. 将权重按 token 行分片，采用多 PE 并行点积、分 bank 累加，消除当前单累加器 II=8 瓶颈，并根据 4 GB PS DDR 与 2 GB PL DDR 决定权重驻留位置。
4. 将网口服务端的 NumPy 后端替换为板上 DMA/DDR 分配、kernel 启动与结果读取；CPU 客户端和二进制协议保持不变。
5. 生成 bitstream 后，先做网线直连的 PING/LOAD_WEIGHT/RUN_TOKEN 单步验证，再运行 8 步真实 trace 和长期稳定性测试。
