# module_14_lm_head_v3_1 — lm_head v3.1（PL DDR，200 MHz，完整词表）

当前状态：真实板卡工程验收 PASS（2026-10-20），正式交付目录、ZIP及解压副本校验PASS。
200 MHz / 完整词表 / 计算数据 PL DDR；8步生产及8份完整FP32 logits逐位一致，
4项内核错误路径、错误golden拒绝、6项加载错误、30次独立计时、1000次连续调用通过。
IP median/P95=117.751830/117.752020 ms；
A53 median=117.770033 ms；canonical加载39.980274s，含实际目标逐块/全量CRC。
同板v3对照为本任务10/19断电前复测；候选为10/20新启动，非同一次启动测量。
最终硬件签核WNS/WHS=+0.632/+0.010ns，源码/四ELF/bit/XSA/profile匹配。
报告：`reports/board_v31_20261019/RESULT.md`；配套包：`reports/board_v31_20261019/package/`。

v3.1 是 v3 的存储归属迁移版本：数学源码、ABI 2、H8/V1 交错累加与相邻 lane 规约顺序
与 v3 相同，只把 M14 的权重、hidden、history 和完整 logits 从 PS DDR 迁到 PL DDR，
并新增独立镜像身份。不做候选词表稀疏化，不实现上游直接供权重，不开展公共 ABI/M06。

## 拓扑

```
A53 (HPM0_FPD, 128-bit)
  └─ axi_smc (5 SI / 3 MI)
       ├─ M00 → lm_head_v2 AXI-Lite    0xA0000000
       ├─ M01 → calib_gpio             0xA0020000   (init_calib_complete)
       └─ M02 → axi_clock_converter (pl_clk0 200 MHz → ui_clk 200 MHz)
                   └─ ddr4_0 (MIG, 2 x MT40A512M16LY, 32-bit, 2 GiB, DDR4-1600)
HLS 四个 m_axi → axi_smc S01..S04，使用与 A53 相同的 64 位系统地址
```

- PS 侧 PL 窗口：`0x4_00000000..0x4_7FFFFFFF`（2 GiB，PS 高地址窗口），与 HLS 本地地址的换算是
  `A53/HLS系统地址 = 0x400000000 + DRAM偏移`；低窗口 0xA0000000 只有 256 MiB，放不下 259.7 MiB 权重。
  **五个 master 均映射到同一个高地址窗口**；MIG 31位接口接收地址低31位。
  驱动直接写入完整64位系统地址，不做减基址转换；旧局部偏移会被拒绝。
  初始候选把同一DDR从不同master映射到不同偏移，Vivado报告不合法；该方案已弃用。
- 校准门控：`init_calib_complete` 通过 `util_vector_logic` 与 UI 域同步复位相与后驱动
  AXI 时钟转换器的 `m_axi_aresetn`，校准完成前用户事务无法进入 MIG；软件另外通过
  AXI GPIO 读该位并设 10 s 超时。
- `sys_rst` 固定为 0，控制器复位由 `c0_ddr4_aresetn`（同步于 ui_clk 的 PS 复位）
  控制；`c0_ddr4_reset_n` 映射到手册物理第18页的 `PL_DDR4_RST / AM5`。

## 地址布局（偏移用于描述 DRAM 位置；寄存器传系统地址）

| 区域 | DRAM 偏移 | 字节 | A53/HLS 系统地址 |
| --- | ---: | ---: | ---: |
| 保护区/自测 | 0x00000000 | 1 MiB | 0x400000000 |
| 权重 | 0x00100000 | 272269312 | 0x400100000 |
| hidden | 0x104A8000 | 1792 | 0x4104A8000 |
| history | 0x104A8700 | 18992 | 0x4104A8700 |
| logits | 0x104AD140 | 607744 | 0x4104AD140 |

容量合计约 261 MiB，位于 2 GiB A53 窗口内；四个区域互不重叠，均 64 B 对齐。

## 身份

| 字段 | v3 | v3.1 |
| --- | --- | --- |
| build_config | 0x20c08011 | 0x30c08011（module_revision 3） |
| capabilities | 0x00000182 | 0x00000382（新增 bit 9 = PL DDR 数据面） |
| HLS IP | lm_head_v2 2.1 | lm_head_v2 2.2 |
| 数值实现 | 不变 | 不变 |
| RUN_PROFILE | M14_BOARD_RUN_PROFILE_V1 | V2，含 PL DDR 与地址映射字段 |

## 构建

```powershell
cd module_14_lm_head_v3_1\experiments\board_v31_20261019
.\run_hardware.ps1 -Stage hls        # csynth（build_config 0x30c08011）
.\export.ps1                         # IP 2.2（含 revision 溢出恢复）
.\run_hardware.ps1 -Stage create_bd  # MIG BD + 地址映射
python make_pin_xdc.py               # 由板卡手册 PL DDR 表生成引脚 XDC
.\run_hardware.ps1 -Stage build      # 5 ns 实现、时序/DRC/CDC、bit/XSA
.\build_software.ps1                 # 新XSA platform + test/loader/diag/timeout-test ELF
python package.py                    # 冻结配套 package
```

## 板测复现（需独占已连接板卡）

```powershell
cd module_14_lm_head_v3_1\standalone
.\run_pl_ddr_acceptance.ps1 -PackageDir ..\reports\board_v31_20261019\package
```

注意：100/200 MHz 或 PS/PL DDR 镜像切换必须完整初始化，不能使用 `-RetainHardware`。
总入口先完整初始化/自测，再检查PS地址、末端越界、整数溢出、软件注入的校准超时，
恢复自测后加载canonical BF16，执行6项TCP错误测试并整份重传，最后执行8步生产/
8步完整logits/3次预热/30次独立计时/1000次稳定性调用。详见 `reports/board_v31_20261019/BOARD_PLAN.md`。

`m14_calib_timeout_test.elf` 仅为软件故障注入测试：屏蔽软件读到的ready，不改变物理MIG，
不能当作物理校准失败实测。`m14_pl_ddr_diag.elf` 不执行lm_head点积；冷配置身份查询会调用BAD_ABI且要求DDR读写计数均0。

## 正式交付门槛

`scripts/finalize_acceptance.py` 从实际记录核验后生成 `comparison.json/RESULT.md`；
`scripts/package_delivery_v31.py stage --date YYYYMMDD` 只接受工程验收PASS。
随后用 `verify_delivery_ip.tcl` 检查导出IP，再 `seal` 生成ZIP/SHA并验证解压副本。
真实板测已通过；本轮总入口在高地址JTAG下载处失败后，修正控制脚本并独立重跑完整数值campaign通过。原失败记录保留，最终证据组装见 `reports/board_v31_20261019/ENGINEERING_RESUME.json`；ZIP完成状态以交付目录的DELIVERY_VALIDATION.json为准。

## 已知限制

1. 独立M14归档有限输入已通过；不代表整体LLM、所有运行模式或极端数值矩阵验收。
2. 本版本的 PL DDR 布局用于独立 M14，整体工程的 KV cache 等共享分配需要统一安排。
3. A53 使用 Normal Non-cacheable 映射访问 PL DDR；加载校验必须针对目标 PL DDR
   实际回读，不能用 PS 接收缓存 CRC 代替。

## 加载路径说明

PL DDR采用Normal Non-cacheable。早期逐字节回读CRC使整份加载约255.17s；
最终loader用对齐64位volatile读取实际目标，经16KiB PS暂存计算CRC，仍保留逐块与整份回读校验。
TCP响应等待时每250ms检查GEM：有待发送DMA描述符且TXGO=0时重触发现有队列，
不重复入队；原tcp_output内存不足重试保留。6项实际协议错误及10轮×5小数据回归通过。
PL DDR整份加载约39.98s，仍慢于本任务PS DDR的8.52663s；该加载/校验差异不能当作IP运行速度变化。
JTAG只处理PS初始化、bit/小ELF/输入/结果，大权重仍通过TCP。
XSCT输入下载前导入包内SHA验证过的最终XSA，以识别0x4_00000000高地址窗口。

正式交付：`../deliverables/20261020_M14_V3_1_r1/`；ZIP外部SHA见该目录ZIP_SHA256SUMS.txt。A53#0已halt，PL DDR权重断电后需重载。
