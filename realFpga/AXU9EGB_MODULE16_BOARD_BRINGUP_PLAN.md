# AXU9EGB 模块 16 LM Head 真实板卡实施规划

> 编制日期：2026-07-22  
> 负责人：zb  
> 目标板卡：ALINX AXU9EGB  
> FPGA：`XCZU9EG-2FFVB1156I`（Vivado part：`xczu9eg-ffvb1156-2-i`）  
> 工具基线：Vivado / Vitis HLS / Vitis IDE 2021.1

## 1. 文档目的

本文用于指导模块 16 从现有 HLS/RTL 仿真环境迁移到真实 AXU9EGB 开发板。每个阶段都列出：

- 要执行的操作；
- 为什么这样做；
- 应产生的文件或现象；
- 通过条件；
- 常见故障及排查方向。

本项目不依赖上游 FPGA 模块。上位机直接读取已经保存的 LM Head 输入、历史 token 位图和黄金输出，经网口发送给 AXU9EGB，FPGA 完成：

```text
LM Head 矩阵向量乘法
  -> FP16 raw logits
  -> 可选 repetition penalty
  -> greedy argmax
  -> selected token / score
```

## 2. 最终系统结构

第一版采用同事 RMSNorm 工程已经验证过的 `A53 standalone + lwIP raw TCP` 路线：

```text
Windows/Linux 上位机
  │
  │ TCP，发送权重、hidden、history bitmap 和参数
  ▼
AXU9EGB PS
  ├─ Cortex-A53 standalone 程序
  ├─ lwIP raw TCP server
  ├─ PS DDR4 缓冲区管理
  ├─ DCache Flush / Invalidate
  └─ AXI-Lite 配置和启动 HLS IP
          │
          ▼
AXU9EGB PL
  └─ lm_head_argmax HLS IP
       ├─ m_axi 读取 weight
       ├─ m_axi 读取 hidden
       ├─ m_axi 读取 history bitmap
       ├─ 可选 m_axi 写 raw logits
       └─ AXI-Lite 返回 token / score / done
          │
          ▼
PS 经 TCP 将结果回传上位机
```

控制通道与数据通道必须分开理解：

```text
控制通道：PS M_AXI_HPM0_FPD -> AXI-Lite -> HLS IP
数据通道：HLS IP m_axi -> AXI SmartConnect -> PS S_AXI_HP/HPC -> PS DDR4
```

## 3. 当前已有资产

### 3.1 模块 16 已有资产

| 资产 | 路径 | 用途 |
| --- | --- | --- |
| HLS 内核 | `module16_lm_head_hls/src/lm_head_kernel.cpp` | 导出 Vivado IP |
| HLS 接口声明 | `module16_lm_head_hls/include/lm_head_kernel.hpp` | 核对最大尺寸和参数 |
| HLS 仿真脚本 | `module16_lm_head_hls/run_csim.tcl` | 真实 trace C 仿真 |
| HLS 综合脚本 | `module16_lm_head_hls/run_csynth.tcl` | ZU9EG 芯片级综合 |
| RTL 联合仿真脚本 | `module16_lm_head_hls/run_cosim.tcl` | 小尺寸 RTL 验证 |
| 网络协议 | `module16_lm_head_hls/NETWORK_PROTOCOL.md` | CPU 与板端约定 |
| Python 客户端 | `module16_lm_head_hls/net/cpu_client.py` | 上位机通信基础 |
| 软件板端模拟器 | `module16_lm_head_hls/net/fpga_server_emulator.py` | 上板前协议验证 |
| 完整 FP16 权重 | `artifacts/model.embed_tokens.weight.fp16.npy` | 启动时上传一次 |
| 8 步 fixture | `artifacts/module16_hls_fixtures/step_00` 至 `step_07` | 上板对拍 |

当前芯片级结果：

- 目标器件：`xczu9eg-ffvb1156-2-i`；
- 目标时钟：5 ns / 200 MHz；
- HLS C 仿真：真实 Qwen trace 8/8 token 匹配；
- RTL co-simulation：1/1 PASS；
- 当前串行基线估计：约 5.489 s/token @ 200 MHz。

### 3.2 可参考的 RMSNorm 资产

| 资产 | 路径 | 可复用内容 |
| --- | --- | --- |
| PS/PL 开发说明 | `ref/RMS/Orin-PS-PL 协同通用开发流程.pdf` | PS 配置、SmartConnect、XSA、Vitis 流程 |
| lwIP 服务端 | `ref/RMS/Vitis_IDE/lwip_rmsnorm_raw_server.c` | TCP 回调、Cache、HLS 驱动、计时 |
| Python 客户端 | `ref/RMS/qwen25_0p5b_python_reference/rmsnorm_fpga_backend.py` | little-endian 帧、精确收发、超时处理 |

RMSNorm 与模块 16 的关键差异：

| 项目 | RMSNorm | 模块 16 |
| --- | ---: | ---: |
| 输入 | 最多约 64 KiB | hidden 1,792 B + history 18,992 B |
| 权重 | 1,792 B，每请求可重传 | 约 260 MiB，只能启动时分块上传一次 |
| 输出 | 最多约 64 KiB | 正常约 8 B；调试 logits 303,872 B |
| 线端类型 | BF16 | FP16 weight/hidden/logits，history 为 uint32 |
| HLS m_axi 端口 | 3 个 | 4 个 |
| TCP 会话 | 示例按单请求使用 | 必须支持一个连接内连续多帧 |

## 4. 在开始前需要补齐的资料

### 操作 4.1：向同事索取板级工程产物

优先索取：

```text
Vivado .xpr 工程或工程重建 Tcl
Block Design .bd
system_wrapper.xsa
可运行 bitstream
Vitis platform / workspace
BSP 配置
lscript.ld
PS GEM3、MDIO、MIO、时钟配置
lwIP 参数截图或配置文件
```

解释：参考目录目前只有说明、C 服务端和 Python 代码，没有可直接复用的 Vivado/Vitis 工程。尤其是 GEM3/PHY 初始化、PS DDR 和板级时钟配置，复用已验证工程比从截图重建风险更低。

通过条件：至少取得 Vivado 工程 Tcl 或 `.xsa`、BSP 配置和 linker script。若无法取得，可继续按本文从头重建，但要增加网口和 DDR 的独立验证时间。

### 操作 4.2：确认硬件和连接

准备：

- AXU9EGB 开发板及稳定电源；
- JTAG 下载器；
- USB-UART 串口线；
- 千兆网线；
- 上位机有线网口；
- 串口终端，设置 `115200 8N1`；
- 记录板卡拨码/启动模式。

通过条件：板卡上电正常，JTAG 能识别 Zynq UltraScale+，串口端口能在电脑中出现。

## 5. 阶段 A：冻结上板前的软件和数据基线

### 操作 A1：重新执行主机侧单元测试

在仓库根目录执行：

```powershell
python -m unittest discover -s tests -v
```

预期：10/10 PASS。

解释：上板后若出现错误，需要先排除协议、CRC、repetition penalty 和 argmax 规则本身的问题。

### 操作 A2：重新执行 HLS C 仿真

```powershell
D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat `
  -f module16_lm_head_hls\run_csim.tcl
```

预期：`HLS_CSIM_OVERALL=PASS`，8 个真实 trace token 全部匹配。

### 操作 A3：记录黄金文件摘要

对以下文件计算 SHA-256 并写入一次验证日志：

```text
artifacts/model.embed_tokens.weight.fp16.npy
artifacts/module16_hls_fixtures/step_00/hidden.fp16.bin
artifacts/module16_hls_fixtures/step_00/history_bitmap.u32.bin
artifacts/module16_hls_fixtures/step_00/golden_logits.fp16.bin
```

解释：260 MiB 权重经过网络和 DDR 后，如果输出错误，需要判断输入文件是否被替换或损坏。

阶段 A 通过条件：单元测试、HLS C 仿真和文件摘要全部记录完成。

## 6. 阶段 B：导出 HLS IP

### 操作 B1：新增 IP 导出 Tcl

在 `module16_lm_head_hls` 下准备 `run_export_ip.tcl`，主要命令应为：

```tcl
open_project -reset lm_head_export
set_top lm_head_argmax
add_files <lm_head_kernel.cpp> -cflags <include path>
open_solution -reset solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5 -name default
csynth_design
export_design -format ip_catalog
exit
```

解释：`csynth_design` 只生成 RTL 综合结果；`export_design -format ip_catalog` 才会产生 Vivado IP Catalog 可以导入的 `component.xml`、RTL 和驱动文件。

### 操作 B2：执行导出

```powershell
D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat `
  -f module16_lm_head_hls\run_export_ip.tcl
```

### 操作 B3：检查导出结果

确认导出目录中存在：

```text
component.xml
hdl/
drivers/
```

打开生成的驱动头文件，核对实际类名和函数名。预计类似：

```c
XLm_head_argmax
XLm_head_argmax_Initialize
XLm_head_argmax_Set_hidden
XLm_head_argmax_Set_weight
XLm_head_argmax_Set_history_bitmap
XLm_head_argmax_Set_raw_logits
XLm_head_argmax_Set_hidden_size
XLm_head_argmax_Set_vocab_size
XLm_head_argmax_Set_write_logits
XLm_head_argmax_Set_enable_repetition_penalty
XLm_head_argmax_Set_repetition_penalty
XLm_head_argmax_Start
XLm_head_argmax_IsDone
```

注意：最终名称必须以生成的驱动头文件为准，不要凭经验手写。

阶段 B 通过条件：Vivado IP Catalog 能识别 `lm_head_argmax`，接口与 HLS 源码一致。

## 7. 阶段 C：建立 Vivado Block Design

> 执行状态（2026-07-24，zb）：**阶段 C 离线构建已完成。**  
> 100 MHz Block Design、综合、实现、bitstream 和 XSA 均通过，详细结果见
> `realFpga/results/20260724_stage_c/README.md`。取得同事完整工程
> `ref/rmsnorm_axu9eg` 后，已将本项目 PS 配置对齐到其 AXU9EGB Vivado 2021.1
> 基线：DDR4-1600、4 GB、64-bit、DPLL 100 MHz PL 时钟、TTC0、GEM3/MDIO
> 和 UART MIO。两份 XSA 的 DDR 初始化函数逐字节一致；进入阶段 D 后仍先做
> 本板 DDR 读写测试，再运行 LM Head。

### 操作 C1：创建工程

Vivado 2021.1 中选择：

```text
Family       Zynq UltraScale+ MPSoCs
Device       xczu9eg
Package      ffvb1156
Speed        -2
Temperature  i
Part         xczu9eg-ffvb1156-2-i
```

如果已取得同事 Vivado 工程，优先复制工程并另存为模块 16 工程；不要直接修改她的原始工程。

### 操作 C2：添加 HLS IP Repository

```text
Tools -> Settings -> IP -> Repository -> Add
```

选择阶段 B 的 HLS IP 导出目录，刷新 IP Catalog，添加 `lm_head_argmax`。

### 操作 C3：添加并配置 Zynq UltraScale+ MPSoC

添加：

```text
Zynq UltraScale+ MPSoC
```

根据同事已验证配置启用：

- PS DDR4；
- UART；
- GEM3、MDIO 及板卡对应 MIO；
- `M_AXI_HPM0_FPD`：PS 控制 PL；
- `S_AXI_HP0_FPD` 或 `S_AXI_HPC0_FPD`：PL 访问 PS DDR；
- `pl_clk0`；
- `pl_resetn0`。

首次点亮建议 `pl_clk0 = 100 MHz`。现有 HLS IP 按 200 MHz 综合，在 100 MHz 下运行是安全的，但估计计算时间会由约 5.489 秒增加到约 10.979 秒。功能通过后再将 PL 时钟切换到 200 MHz，并重新完成实现和时序检查。

### 操作 C4：添加控制 SmartConnect

实例名建议：

```text
axi_smc_ctrl
```

连接：

```text
zynq_ultra_ps_e_0/M_AXI_HPM0_FPD
  -> axi_smc_ctrl/S00_AXI

axi_smc_ctrl/M00_AXI
  -> lm_head_argmax_0/s_axi_control
```

解释：A53 通过该路径写输入地址、尺寸、开关和 `ap_start`，并读取 `ap_done`、token 和 score。

### 操作 C5：添加数据 SmartConnect

实例名建议：

```text
axi_smc_mem
```

设置：

```text
Number of Slave Interfaces  = 4
Number of Master Interfaces = 1
```

连接：

```text
lm_head_argmax_0/m_axi_gmem_hidden  -> axi_smc_mem/S00_AXI
lm_head_argmax_0/m_axi_gmem_weight  -> axi_smc_mem/S01_AXI
lm_head_argmax_0/m_axi_gmem_history -> axi_smc_mem/S02_AXI
lm_head_argmax_0/m_axi_gmem_logits  -> axi_smc_mem/S03_AXI

axi_smc_mem/M00_AXI
  -> zynq_ultra_ps_e_0/S_AXI_HP0_FPD
     或 zynq_ultra_ps_e_0/S_AXI_HPC0_FPD
```

解释：这四个端口都是 HLS IP 发起访问的 AXI master；PS 侧 HP/HPC 在 PL 看来是通往 PS DDR 的 slave 入口。

### 操作 C6：添加 Processor System Reset

添加：

```text
Processor System Reset
```

统一连接：

```text
pl_clk0    -> HLS IP ap_clk
pl_clk0    -> 两个 SmartConnect aclk
pl_clk0    -> PS AXI port clocks
pl_clk0    -> reset block slowest_sync_clk

pl_resetn0 -> reset block ext_reset_in
reset block peripheral_aresetn -> HLS IP ap_rst_n
reset block peripheral_aresetn -> SmartConnect aresetn
```

### 操作 C7：分配地址

在 Address Editor 中：

1. 给 `lm_head_argmax_0/s_axi_control` 分配 64 KiB 控制空间；
2. 确认四个 HLS m_axi master 都映射到 PS DDR segment；
3. 不允许任何 m_axi 端口悬空；
4. 记录最终控制基地址，不固定假设为 `0xA0000000`。

Vitis 最终应在 `xparameters.h` 中产生对应 HLS IP 的 device ID 或 base address 宏。

### 操作 C8：验证和生成硬件

依次执行：

```text
Validate Design
Generate Output Products
Create HDL Wrapper
Run Synthesis
Run Implementation
Generate Bitstream
```

重点检查：

- 没有 AXI 地址重叠；
- 没有未连接的时钟、复位或 m_axi；
- Implementation 后无负 slack；
- 100 MHz 首次版本先通过；
- 200 MHz 版本必须重新检查真实布线时序，不能只引用 HLS 估计时序。

阶段 C 通过条件：bitstream 生成成功，Address Editor 和时序报告已保存截图或文本。

## 8. 阶段 D：导出 XSA 并建立 Vitis standalone 平台

> 当前状态：阶段 C 构建过程已经提前导出包含 bitstream 的
> `realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa`，可直接作为阶段 D
> 的平台输入；Vitis platform、BSP 和 standalone 应用尚未创建。

### 操作 D1：导出 XSA

```text
File -> Export -> Export Hardware
Include bitstream：勾选
```

建议输出：

```text
realFpga/hardware/system_wrapper.xsa
```

### 操作 D2：创建 Platform Project

Vitis IDE 2021.1：

```text
Processor    psu_cortexa53_0
OS           standalone
Architecture 64-bit
```

### 操作 D3：配置 BSP 和 lwIP

启用 lwIP，第一版使用静态 IP。示例：

```text
Board IP : 192.168.1.10
PC IP    : 192.168.1.20
Netmask  : 255.255.255.0
Gateway  : 192.168.1.1 或不使用
```

实际地址可以调整，但代码、文档和测试命令必须统一。不要混用 RMSNorm 文档中的 `192.168.8.190` 和示例中的 `192.168.1.10`。

建议 lwIP 参数起点：

```text
lwip_dhcp        = false
tcp_snd_buf      = 32768 或更大
tcp_wnd          = 32768 或更大
memp_num_tcp_seg = 512
mem_size         >= 262144
pbuf_pool_size   >= 256
```

解释：lwIP TCP window 不需要等于 1 MiB 应用层分块；TCP 可以经过多次 callback 将一个应用帧逐段写入接收缓冲区。

阶段 D 通过条件：platform 和 BSP 编译成功，能看到自动生成的 HLS IP 驱动。

## 9. 阶段 E：规划 PS DDR 缓冲区

### 9.1 数据大小

| 缓冲区 | 大小 |
| --- | ---: |
| weight | 272,269,312 B，约 259.66 MiB |
| hidden | 1,792 B |
| history bitmap | 18,992 B |
| raw logits | 303,872 B |
| 单个网络接收分块 | 建议 1 MiB + 帧头 |

### 操作 E1：查看 linker memory region

检查 Vitis 生成的 `lscript.ld` 和 platform memory map，确认 PS DDR region 的：

- 起始地址；
- 长度；
- 程序、栈、堆和 lwIP 当前占用范围。

禁止在没有检查 linker map 的情况下随意选择固定地址。

### 操作 E2：为大权重建立 NOLOAD 区域

推荐在 linker script 中建立专用 `NOLOAD` section，使 260 MiB 缓冲区不进入 ELF 文件，也不在启动时被清零。示意：

```ld
.lmh_buffers (NOLOAD) :
{
    . = ALIGN(64);
    KEEP(*(.lmh_weight))
    . = ALIGN(64);
    KEEP(*(.lmh_logits))
    . = ALIGN(64);
    KEEP(*(.lmh_work))
} > psu_ddr_0_MEM_0
```

实际 memory region 名称必须使用当前 XSA 生成的名称。

C 代码示意：

```c
static uint16_t weight_buf[151936U * 896U]
    __attribute__((section(".lmh_weight"), aligned(64)));
```

编译后必须检查 `.map` 文件，确认这些区域：

- 位于 PS DDR；
- 互不重叠；
- 不覆盖程序、栈、堆和 lwIP；
- 权重首地址能由 64-bit AXI 地址寄存器表示。

### 操作 E3：制定 Cache 规则

权重分块写入 DDR 后，对刚写入的区域执行：

```c
Xil_DCacheFlushRange(weight_addr + offset, chunk_bytes);
```

每次运行前：

```c
Xil_DCacheFlushRange(hidden_addr, hidden_bytes);
Xil_DCacheFlushRange(history_addr, history_bytes);
Xil_DCacheFlushRange(logits_addr, logits_bytes);
```

硬件完成后：

```c
Xil_DCacheInvalidateRange(logits_addr, logits_bytes);
```

解释：CPU 写入的数据可能仍在 Cache 中，PL 直接访问 DDR 会读到旧值；PL 写回 logits 后，CPU Cache 中也可能仍保留旧值。

阶段 E 通过条件：linker `.map` 文件证明所有缓冲区地址合法且无重叠。

## 10. 阶段 F：实现模块 16 lwIP 服务端

### 操作 F1：从 RMSNorm 服务端建立独立副本

不要直接修改：

```text
ref/RMS/Vitis_IDE/lwip_rmsnorm_raw_server.c
```

在 `realFpga/vitis_app` 中新建：

```text
lwip_lm_head_raw_server.c
```

保留其以下模式：

- `tcp_accept`、`tcp_recv`、`tcp_sent` 回调；
- 分段 `tcp_write`；
- `XTime` 硬件计时；
- HLS IP Initialize / Start / IsDone；
- Cache Flush / Invalidate；
- 超时保护。

### 操作 F2：实现现有 LMH1 协议

帧头固定 24 字节、little-endian：

```text
magic         4 B  = "LMH1"
version       u16  = 1
opcode        u16
request_id    u32
flags         u32
payload_bytes u32
crc32         u32
```

实现命令：

```text
PING        = 3
LOAD_WEIGHT = 1
RUN_TOKEN   = 2
```

错误响应：

```text
opcode = 0xffff
payload = UTF-8/ASCII 错误消息
```

### 操作 F3：实现可重复使用的 TCP 会话状态机

RMSNorm 示例接受一个请求后没有为同一连接重置 `rx_len/expected_len`，其 Python 客户端通常每次调用重建连接。模块 16 客户端会在同一连接中执行：

```text
LOAD_WEIGHT chunk 0
LOAD_WEIGHT chunk 1
...
PING
RUN_TOKEN step 0
RUN_TOKEN step 1
...
```

因此板端每完成一个响应后必须：

```text
等待 tx 数据发送完毕
清零当前 frame 的 rx_len / expected_len
保留 weight_ready、weight_offset、维度等全局状态
继续接收下一个 24 B 帧头
```

必须正确处理：

- 一个 TCP pbuf 只包含半个帧头；
- 一个 pbuf 包含帧头和部分 payload；
- 多个 pbuf 拼成一个 1 MiB 权重分块；
- 一次 callback 中出现一个完整帧及下一个帧的开头；
- 客户端断开后会话缓冲状态清理，但已完成的权重是否保留要有明确策略。

第一版建议：断开 TCP 后保留 `weight_ready` 和 DDR 权重；板卡复位或新的 `FIRST_CHUNK` 才废弃旧权重。

### 操作 F4：实现分块权重上传

第一版建议 `chunk_bytes = 1 MiB`。每块 payload：

```text
total_bytes  u64
hidden_size u32
vocab_size  u32
offset       u64
chunk_data  FP16 little-endian
```

检查：

1. `FIRST_CHUNK` 时 `offset == 0`；
2. `total_bytes == 151936 * 896 * 2`；
3. `hidden_size == 896`；
4. `vocab_size == 151936`；
5. 后续块 offset 必须连续；
6. 单块不能越过总长度；
7. 帧 CRC32 正确；
8. `LAST_CHUNK` 的末尾必须等于 `total_bytes`；
9. 全部完成后设置 `weight_ready = true`。

每个分块写入权重 DDR 后立即 Flush 对应范围，避免最后一次 Flush 260 MiB 带来的长阻塞和调试困难。

### 操作 F5：实现 PING

返回：

```text
hidden_size = 896
vocab_size  = 151936
weight_bytes = 272269312；未 READY 时为 0 或通过状态字段说明
```

建议后续扩展返回固件版本、协议版本和构建时间，但第一版先保持 Python 客户端兼容。

### 操作 F6：实现 RUN_TOKEN

解析：

```text
hidden_size
vocab_size
repetition_penalty
history_words
hidden FP16
history bitmap uint32
```

执行前检查：

- 权重已经 READY；
- `hidden_size == 896`；
- `vocab_size == 151936`；
- 开启 penalty 时 `history_words == 4748`；
- payload 长度严格匹配；
- repetition penalty 大于 0；
- 所有地址按要求对齐。

设置 HLS IP 寄存器：

```text
hidden address
weight address
history bitmap address
raw logits address
hidden_size = 896
vocab_size = 151936
write_logits = WANT_LOGITS ? 1 : 0
enable_repetition_penalty = flag bit 0
repetition_penalty = 1.1 或请求值
```

启动并轮询：

```c
XLm_head_argmax_Start(&lmh_ip);
while (!XLm_head_argmax_IsDone(&lmh_ip)) {
    if (++polls > timeout_polls) {
        /* 返回超时错误 */
    }
}
```

返回：

```text
status
selected_token
selected_score FP32
logits_bytes
可选 raw_logits FP16
```

`selected_score` 如果由驱动以 `uint32_t` 返回，应通过 `memcpy` 按位转换为 `float`，不要做数值类型转换。

阶段 F 通过条件：Vitis application 编译成功，无未定义 HLS driver symbol，静态内存 map 合法。

## 11. 阶段 G：实现直接读取 fixture 的上位机程序

### 操作 G1：新增真实板卡测试入口

建议新增：

```text
tools/run_module16_board_trace.py
```

支持参数：

```text
--host
--port
--weight
--fixture-root
--step
--load-weight
--chunk-bytes
--return-logits
--repetition-penalty
--timeout
```

程序直接读取：

```text
hidden.fp16.bin
history_bitmap.u32.bin
golden_logits.fp16.bin
expected_token.txt
```

不启动完整 Qwen，不要求 Orin/GPU，也不调用 `manual_prefill_decode.py`。

### 操作 G2：避免把 260 MiB 权重复制多次

使用 NumPy `mmap_mode="r"` 打开 `.npy`，按 1 MiB 分块发送。不要同时创建多份 contiguous weight 副本，否则上位机内存峰值会无谓增加。

### 操作 G3：先保留现有客户端协议

尽量复用：

```text
module16_lm_head_hls/net/lmh_protocol.py
module16_lm_head_hls/net/cpu_client.py
```

必要修改只能增强真实板卡兼容性，不应破坏现有 TCP loopback 单元测试。

阶段 G 通过条件：脚本能连接软件模拟器并完成 step 0；待板卡上线后只需修改 IP 地址即可连接真实板端。

## 12. 阶段 H：真实板卡逐级点亮

必须严格按以下顺序，不要直接跳到完整 260 MiB 权重。

### H1：JTAG、UART 和 Hello World

操作：

1. JTAG 连接板卡；
2. Program FPGA；
3. 用 FSBL 初始化 PS；
4. 下载最小 standalone Hello World；
5. 串口查看输出。

通过条件：连续复位和运行 5 次，串口每次都正常。

### H2：lwIP 网络点亮

操作：

1. 板卡设置静态 IP，例如 `192.168.1.10`；
2. 上位机设置 `192.168.1.20/24`；
3. 关闭或调整会拦截该网段的防火墙；
4. 观察 PHY link 灯；
5. 上位机 `ping 192.168.1.10`；
6. 使用简单 TCP echo 测试。

通过条件：连续 ping 无丢包，TCP 能传输大于 1 MiB 的测试数据。

### H3：AXI-Lite 寄存器访问

暂不运行全尺寸计算，只初始化 HLS IP 并读取 ready/idle 状态，写入尺寸寄存器后回读或通过 ILA/驱动打印确认。

通过条件：HLS IP Initialize 成功，device ID/base address 正确，`IsReady`/`IsIdle` 状态合理。

### H4：4×4 合成数据

使用 HLS testbench 的小矩阵思想：

- hidden size = 4；
- vocab size = 4；
- 构造简单 FP16 权重；
- 构造 history，使 raw top-1 经过 repetition penalty 后发生变化；
- 对比 token 和 score。

通过条件：

1. 不启用 penalty 时结果正确；
2. 启用 penalty 时结果正确；
3. 平分时选择较小 token ID；
4. WANT_LOGITS 开关工作。

### H5：权重分块上传测试

先用较小的模拟权重测试：

- FIRST/LAST 单块；
- 多块连续上传；
- 故意错误 offset；
- 故意错误 CRC；
- 中途断开后重新 FIRST_CHUNK；
- PING READY 状态。

通过条件：合法上传成功，非法上传都返回明确错误且不会把状态误设为 READY。

### H6：完整权重上传

上传约 260 MiB 权重，记录：

- 总耗时；
- 平均吞吐；
- 分块数；
- 是否发生重传/断连；
- 板端最终 offset；
- PING 返回的 weight bytes。

建议增加整个权重的 CRC32 或 SHA-256 校验。帧 CRC 只能证明每个分块，不能单独证明所有块组合后的总文件身份。

### H7：运行真实 step 00

第一次设置：

```text
enable_repetition_penalty = true
repetition_penalty = 1.1
return_logits = true
```

检查：

- selected token 等于 `expected_token.txt`；
- raw logits 最大绝对误差不超过既定 FP16/HLS 容差；
- Top-5 5/5；
- 硬件无超时；
- 重复运行结果稳定。

### H8：运行全部 8 步

权重不重复上传，依次发送 step 00 至 step 07。

通过条件：

- token 8/8 完全匹配；
- Top-5 每步 5/5；
- repetition penalty processed scores 验证通过；
- 没有 TCP、CRC、AXI 或 HLS timeout 错误。

### H9：正常运行模式

关闭完整 logits 回传：

```text
return_logits = false
```

仅返回 token 和 score，测量：

- 网络请求耗时；
- HLS 纯硬件耗时；
- Cache 和内存准备耗时；
- 总端到端耗时。

阶段 H 最终通过条件：8 步真实 trace 在真实 AXU9EGB 上全部通过，并保存原始日志和版本信息。

## 13. 阶段 I：从 100 MHz 切换到 200 MHz

只有 100 MHz 功能完全通过后才能执行：

1. 将 PL/HLS/AXI 相关时钟切换到 200 MHz；
2. 重新 Validate Design；
3. 重新综合、布局布线；
4. 检查 setup/hold timing；
5. 生成新 bitstream/XSA；
6. 重新编译 platform/application；
7. 从 H1 或至少 H3 开始重复验证；
8. 重新运行全部 8 步 trace。

如果 SmartConnect 或 PS AXI port 不适合统一运行在 200 MHz，可使用独立时钟和 AXI Clock Converter，但必须保证每个时钟域有正确复位同步。

通过条件：Implementation 时序收敛，8/8 trace 仍通过，硬件耗时接近或优于综合估计。

## 14. 常见故障排查表

| 现象 | 优先检查 |
| --- | --- |
| JTAG 找不到器件 | 电源、JTAG 驱动、拨码、线缆 |
| 串口无输出 | UART MIO、BSP stdout、115200 8N1、FSBL |
| PHY 不亮 | GEM3/MDIO/MIO、PHY reset、时钟、网线 |
| 能 ping 但 TCP 断开 | lwIP 内存、window、pbuf、session 状态机 |
| 传权重中途卡住 | tcp_recved、pbuf 释放、1 MiB 缓冲、tcp_sent 回调 |
| CRC 错误 | little-endian、帧边界、payload 长度、缓存覆盖 |
| PING 一直未 READY | FIRST/LAST、offset 连续性、总字节数 |
| HLS Initialize 失败 | XSA 是否包含 IP、device ID、驱动名称 |
| IP 永不 done | AXI 地址、m_axi DDR segment、时钟/复位、timeout |
| done 但 token 错误 | Cache、FP16 字节序、weight 布局、hidden/history |
| 仅 penalty 错误 | history bitmap bit 顺序、penalty 正负分支、开关 |
| logits 正确但 token 错 | FP16 转换时机、平分规则、argmax 是否使用 processed score |
| 100 MHz 正常、200 MHz 错 | Implementation timing、CDC、复位同步、电源/温度 |

## 15. 必须保存的实验记录

每次有效实验记录：

```text
日期和操作者
Git commit 或工作区摘要
Vivado/Vitis 版本
FPGA part
bitstream/XSA/ELF 文件摘要
PL 时钟
板卡 IP、上位机 IP、TCP 端口
weight 文件 SHA-256
是否启用 repetition penalty
是否回传 logits
每步 token、误差、Top-5
权重上传耗时
硬件耗时
端到端耗时
串口和上位机完整日志
```

建议输出目录：

```text
realFpga/results/YYYYMMDD_HHMM_<clock>MHz/
```

## 16. 成功定义

只有同时满足以下条件，才可以声明模块 16 完成真实板卡验证：

1. 使用 AXU9EGB 实际 bitstream，不是 HLS C/RTL 仿真；
2. 数据经过真实以太网到达 PS；
3. PS 将数据写入 PS DDR，并由 PL HLS IP 读取；
4. PL 实际完成 LM Head、repetition penalty 和 argmax；
5. 真实 trace 的 token 8/8 与 `generated_ids` 匹配；
6. 至少一次验证完整 raw logits，而不是只验证 token；
7. 有可复现的 Vivado、Vitis、上位机代码和操作记录；
8. 有超时、CRC、错误 offset 等异常路径测试。

以下结果不能单独称为真实板卡验证完成：

- HLS C 仿真 PASS；
- RTL co-simulation PASS；
- 软件 TCP 回环 PASS；
- 只 ping 通板卡；
- 只运行 4×4 合成用例；
- 只匹配 token，但没有检查 logits 和 repetition penalty。

## 17. 推荐执行顺序摘要

```text
1. 补齐同事的 XSA/Vivado/BSP/linker 资料
2. 冻结当前测试、权重和 8 步 fixture
3. 导出 lm_head_argmax Vivado IP
4. 复用 RMSNorm PS 配置建立模块 16 Block Design
5. 100 MHz 生成 bitstream 和 XSA
6. 创建 A53 standalone + lwIP platform
7. 建立 PS DDR NOLOAD 权重区
8. 实现 LMH1 lwIP 多帧服务端
9. 实现直接读取 fixture 的板卡测试脚本
10. Hello World -> ping -> TCP -> AXI-Lite
11. 4×4 -> 分块上传 -> 完整权重
12. step 00 完整 logits
13. 全部 8 步 trace
14. 关闭 logits 测性能
15. 切换 200 MHz 并完整回归
16. 保存结果，开始多 PE 性能优化
```

第一版的目标是建立可信、可重复的真实板卡正确性基线。当前串行内核性能不是最终目标；多 PE、AXI 扩宽、PL DDR 和量化优化应放在真实板卡 8/8 正确性通过之后。
