# 阶段 C：AXU9EGB Vivado Block Design 与 bitstream 构建报告

> 日期：2026-07-24  
> 操作者：zb  
> 工具：Vivado 2021.1  
> 目标器件：`xczu9eg-ffvb1156-2-i`  
> 本阶段只进行了离线建图、综合、实现和硬件平台导出，没有连接或下载到开发板。

## 1. 阶段结论

阶段 C 的可重复离线构建已完成：

- `lm_head_argmax` HLS IP 已加入 Vivado IP Catalog；
- PS 到 PL 的 AXI-Lite 控制通路已建立；
- LM Head 的四条 AXI 数据通路已接到 PS `S_AXI_HP0_FPD`；
- PS DDR 已在最终 XSA 中启用；
- Block Design 验证、综合、布局布线、bitstream 和 XSA 生成全部成功；
- 布线后没有失败或未布线网络；
- 100 MHz 设计满足时序。

2026-07-24 晚些时候取得了同事在 AXU9EGB 上使用的完整 Vivado 2021.1
工程 `ref/rmsnorm_axu9eg`。本项目最终版已按该工程校准 PS 参数并重新完成
综合实现。两份最终 XSA 的 1111 个 `PSU__*` 参数中，1110 项完全相同；
唯一差异是已禁用 UART1 的派生参考频率显示值（`99.999001` 与 `100` MHz），
不参与当前设计。

更重要的是，两份 XSA 中 `psu_ddr_init_data()` 的 523,694 个字符逐字节完全
一致。这证明最终 DDR 控制器与 PHY 初始化序列已经对齐同事工程。我们仍将在
第一次下载后执行独立 DDR 读写测试，因为“配置与已验证工程相同”和“本次新
bitstream 已在本板验证”是两个不同层次的结论。

## 2. 最终硬件结构

### 控制通路

```text
A53 / PS M_AXI_HPM0_FPD
  -> axi_smc_ctrl
  -> lm_head_argmax_0/s_axi_control
```

控制寄存器地址：

```text
0xA0000000 .. 0xA000FFFF
```

### 数据通路

```text
lm_head_argmax_0/m_axi_gmem_hidden  -> axi_smc_mem/S00_AXI
lm_head_argmax_0/m_axi_gmem_weight  -> axi_smc_mem/S01_AXI
lm_head_argmax_0/m_axi_gmem_history -> axi_smc_mem/S02_AXI
lm_head_argmax_0/m_axi_gmem_logits  -> axi_smc_mem/S03_AXI

axi_smc_mem/M00_AXI
  -> zynq_ultra_ps_e_0/S_AXI_HP0_FPD
  -> PS DDR
```

### 时钟和复位

```text
PS pl_clk0 实际频率：99.999001 MHz
PS pl_resetn0 -> Processor System Reset
Processor System Reset peripheral_aresetn
  -> HLS IP 和两个 SmartConnect
```

HLS IP 的 `interrupt` 未连接是有意设计：第一版 PS 软件使用寄存器轮询 `ap_done`，不使用中断。

## 3. PS 板级配置

依据 AXU9EGB 手册和 Vivado 2021.1 可用属性配置：

```text
PS 参考时钟：33.333 MHz
GEM3 RGMII：MIO 64..75
GEM3 MDIO：MIO 76..77
UART：MIO 42..43（Vivado 2021.1 的 IP 属性名为 UART0）
```

### DDR 参考工程对齐配置

板卡手册描述为四颗 8 Gbit、x16 DDR4 颗粒，总线 64 bit，总容量 4 GB。
最终参数以同事的 `ref/rmsnorm_axu9eg/system_wrapper_wrapper.xsa` 为基准：

```text
PSU__USE__DDR_INTF_REQUESTED = 0
PSU__DDRC__ENABLE            = 1
Memory type                  = DDR4
Bus width                    = 64 Bit
DRAM width                   = 16 Bits
Device capacity              = 8192 MBits
Row address count            = 16
Speed bin                    = DDR4_1600J
DDR controller requested     = 800 MHz
DDR controller actual        = 399.996002 MHz
DDR data-rate field          = 799.992004 MHz
ECC                          = Disabled
Read-gate/data-eye/write-level training = Enabled
```

这里必须纠正早期判断：`PSU__USE__DDR_INTF_REQUESTED=0` 是 Vivado
GUI/request bookkeeping 字段，不能单独用来判断 DDR 是否关闭。同事工程该
字段同样为 0，但 `PSU__DDRC__ENABLE=1`，并且 XSA 包含完整 DDRC/DDR PHY
初始化。判断依据应组合检查 `DDRC__ENABLE`、容量/时序、内存地址范围和
`psu_ddr_init_data()`。

同事工程还确认了以下板级设置：

```text
PL0 时钟源：DPLL
PL0 实际频率：99.999001 MHz
TTC0：Enabled
GEM3、MDIO、UART0 MIO：与本项目一致
M_AXI_HPM0_FPD、S_AXI_HP0_FPD：与本项目一致
```

## 4. 构建结果

### Vivado 状态

```text
LMH_STAGE_C_CREATE=PASS
LMH_STAGE_C_SYNTH_STATUS=synth_design Complete!
LMH_STAGE_C_IMPL_STATUS=write_bitstream Complete!
LMH_STAGE_C_BUILD=PASS
```

### 时序

```text
WNS = +4.262 ns
TNS = 0.000 ns
WHS = +0.010 ns
THS = 0.000 ns
All user specified timing constraints are met.
```

WNS/WHS 均为正，表示 100 MHz 版本没有 setup/hold 时序违例。

### 布线

```text
Routable nets          = 21455
Fully routed nets      = 21455
Nets with route errors = 0
```

### 资源占用

| 资源 | 使用量 | 可用量 | 占用率 |
| --- | ---: | ---: | ---: |
| CLB LUT | 10,428 | 274,080 | 3.80% |
| CLB Register | 15,603 | 548,160 | 2.85% |
| Block RAM Tile | 6 | 912 | 0.66% |
| DSP | 5 | 2,520 | 0.20% |

参考工程对齐后，资源占用仍然很低，不构成上板限制。

### DRC

```text
Errors     = 0
Warnings   = 15
Advisories = 5
```

15 条 warning 分布：

| 类型 | 数量 | 含义 |
| --- | ---: | --- |
| AVAL-318 | 1 | HLS 浮点 DSP 的动态 PCIN/布局提醒 |
| DPIP-2 | 5 | DSP 输入流水线优化建议 |
| DPOP-3 | 6 | DSP PREG 输出流水线优化建议 |
| DPOP-4 | 2 | DSP MREG 输出流水线优化建议 |
| DPREG-7 | 1 | 动态 OPMODE 与 PREG 的方法学提醒 |

这些 warning 来自 Vitis HLS 2021.1 生成的浮点 DSP 网络，未阻止 bitstream 生成且当前时序满足。但 AVAL-318/DPREG-7 不能仅按“性能建议”忽略：第一次真实板验证必须用 8 步 trace 对比 token、Top-5、logits 误差，确认实际数值行为。

## 5. 最终产物

### bitstream

```text
路径：
realFpga/vivado/build/lm_head_axu9eg/lm_head_axu9eg.runs/impl_1/lm_head_system_wrapper.bit

大小：
26,510,907 bytes

SHA-256：
723F56E9AF239B6DE20EFCB542F3E72A5BA0789D437F0344311568E3D4BA939E
```

### XSA

```text
路径：
realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa

大小：
1,264,635 bytes

SHA-256：
B72DD60AFD2FCB7355F59F638A393A07250F0B6A878E300720D1AEEA36AB652C
```

XSA 已确认包含：

- bitstream；
- `lm_head_system.hwh`；
- `psu_init.c/.h/.tcl`；
- `lm_head_argmax` standalone 驱动；
- SmartConnect 硬件描述；
- `sysdef.xml` 和 XSA 元数据。

对 `lm_head_system.hwh` 的内容核验结果：

```text
PSU__USE__DDR_INTF_REQUESTED = 0
PSU__DDRC__ENABLE            = 1
PSU__DDRC__BUS_WIDTH         = 64 Bit
PSU__DDRC__DRAM_WIDTH        = 16 Bits
PSU__DDRC__DEVICE_CAPACITY   = 8192 MBits
PSU__DDRC__ROW_ADDR_COUNT    = 16
PSU__DDRC__SPEED_BIN         = DDR4_1600J
PSU__CRF_APB__DDR_CTRL__FREQMHZ = 800
C_S_AXI_CONTROL_BASEADDR     = 0xA0000000
```

最终核验：

```text
同事 XSA PSU 参数数：1111
本项目 XSA PSU 参数数：1111
功能相关差异：0
仅有差异：已禁用 UART1 的 ACT_FREQ 显示值
psu_ddr_init_data() 长度：523694 / 523694
psu_ddr_init_data() 精确匹配：True
```

先前 DDR4-2400 暂定版 XSA 已保留为：

```text
realFpga/results/20260724_stage_c/lm_head_axu9eg_attempt5_provisional_ddr2400.xsa
```

它只用于保留调试轨迹，不再作为后续 Vitis 平台输入。

## 6. 可重复执行脚本和原始日志

```text
realFpga/vivado/create_lm_head_axu9eg_bd.tcl
realFpga/vivado/build_lm_head_axu9eg.tcl

realFpga/results/20260724_stage_c/create_bd_attempt7_reference_exact.log
realFpga/results/20260724_stage_c/build_bitstream_attempt6_reference_aligned.log
realFpga/results/20260724_stage_c/post_synth_utilization.rpt
realFpga/results/20260724_stage_c/post_synth_timing_summary.rpt
realFpga/results/20260724_stage_c/post_route_utilization.rpt
realFpga/results/20260724_stage_c/post_route_timing_summary.rpt
realFpga/results/20260724_stage_c/post_route_drc.rpt
```

## 7. 下一阶段入口（尚未执行）

下一阶段首先导入 `lm_head_axu9eg.xsa` 建立 Vitis standalone 平台，然后只做最小风险的 PS 验证：

1. 串口启动与基础 platform 初始化；
2. 小范围 PS DDR walking-bit/地址线/随机数据读写；
3. 网络接口和板卡 IP 验证；
4. HLS 控制寄存器读写；
5. 小尺寸 LM Head 调用；
6. 最后才执行完整 8 步 trace。

在用户明确命令前，不进入下一阶段，也不向板卡下载 bitstream。
