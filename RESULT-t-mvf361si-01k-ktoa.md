# RESULT t-mvf361si-01k-ktoa · v3.1 代码/BD/构建完成，真实板测因板卡未连接无法执行（NOT_RUN）
[luyou:t-mvf361si-01k-ktoa:failed]

## 结论

lm_head v3.1（200 MHz、完整词表、计算数据走 PL DDR）的源码、MIG 块设计、引脚约束、
软件/loader 适配与构建脚本已完成；**M2 真实板测无法执行**：本机 JTAG 无任何目标
（`M14_V31_JTAG_TARGETS=0`），有线网口 `Disconnected`、`192.168.0.190:1414` 不可达。
按任务书要求立即升级，未虚报任何数值/性能结果。

## 做了什么

### M0 基线

- 复核 v3 已验收资产：权重 SHA256 `4e96b0df…223f`、272269312 B；v3 build_config
  `0x20c08011`、IP 2.1、基线 IP median/P95 117.751805/117.751890 ms。
- 从 `AXU9EGB开发板用户手册.pdf`（2-3 节）提取 PL DDR4 完整引脚表：2 片
  MT40A512M16LY-062E、32-bit、2 GiB、BANK64/65、200 MHz 差分参考 AL8/AL7。
  历史 MIG 工程不存在，未伪造任何引脚。
- 工具链复核：Vivado/Vitis/Vitis_HLS 2021.1 可用；板卡不可达（见上）。

### M1 实现

- 新模块 `module_14_lm_head_v3_1/`，未改动 v3 源码、reports、deliverables、ZIP 与根开发日志。
- HLS：复制 v3 数值源码，仅改身份常量
  - `build_config 0x20c08011 → 0x30c08011`（module_revision 2→3）
  - `capabilities 0x00000182 → 0x00000382`（新增 bit9 = PL DDR 数据面）
  - IP 版本 2.1 → 2.2；csynth 估计 3.650 ns @ 5 ns，与 v3 逐项一致。
- BD `m14_v31_system`：
  - `ddr4_0`（MIG 2.2）：MT40A512M16LY-075、32-bit、DDR4-1600（800 MHz）、4:1、
    AXI 128 bit / 31 bit、2 GiB、单 rank、DM_NO_DBI、无 ECC、无 parity。
  - PS HPM0 128-bit 单端口 → SmartConnect（5 SI / 3 MI）：M00 HLS AXI-Lite
    `0xA0000000`、M01 calib GPIO `0xA0020000`、M02 → AXI clock converter
    （pl_clk0 200 MHz → ui_clk 200 MHz）→ MIG。
  - HLS 四个 m_axi 本地地址 `0x00000000..0x7FFFFFFF`。
  - PS 侧 PL DDR 窗口使用高地址 aperture `0x4_00000000`（低窗口
    `0xA0000000` 只有 256 MiB，装不下 259.7 MiB 权重），range `0x80000000`。
  - 校准门控：`init_calib_complete` AND pl 复位 → converter `m_axi_aresetn`，
    校准前用户事务无法进入 MIG；软件再读 GPIO 并设 10 s 超时。
- 约束：`constraints/lm_head_v31_ddr4_pins.xdc` 由 `make_pin_xdc.py` 从手册表生成，
  72 个网络；IOSTANDARD 按 MIG 要求区分 `SSTL12_DCI`（地址/命令）、`POD12_DCI`
  （DQ/DM）、`DIFF_POD12_DCI`（DQS）、`DIFF_SSTL12_DCI`（CK）、`DIFF_SSTL12`（参考时钟）。
- 软件：
  - `pl_ddr_layout.h`：唯一地址布局真源（A53 = `0x400000000` + local）。
  - test ELF：PL DDR 2 GiB 映射为 Normal Non-cacheable（1 GiB 块）、校准等待、
    A53 地址范围拒绝、1 MiB 保护区数据/地址线/边界自测、A53 地址到 HLS 本地地址翻译。
  - TCP loader：目标改为 `0x400100000`，启动前校准等待与 MMU 设置，CRC 仍按
    **目标 PL DDR 实际回读**计算（非接收缓冲）。
  - `RUN_PROFILE` V2 + `board_profile.py` 新增 `0x30C08011` 识别。

## 自测（离线）

- HLS csynth PASS（3.650 ns 估计，与 v3 相同）。
- IP export PASS（revision 溢出恢复后生成 `lm_head_v2:2.2`）。
- BD 创建 PASS，地址编辑器导出：
  PS `0x0400000000/0x80000000`、HLS 四个空间 `0x0/0x80000000`、
  控制 `0xA0000000`、GPIO `0xA0020000`。
- 实现阶段发现并修正 MIG IOSTANDARD 三处错误（SSTL12 → SSTL12_DCI/POD12_DCI/
  DIFF_POD12_DCI），原始失败日志保留。
- 真实板测：NOT_RUN（无 JTAG 目标、网口断开）。

## 改动文件

新增（均在新模块内）：

- `module_14_lm_head_v3_1/README.md`、`PROGRESS.json`
- `module_14_lm_head_v3_1/experiments/board_v31_20261019/`：`create_bd.tcl`、
  `build.tcl`、`hls.tcl`、`export.tcl`、`export.ps1`、`build_software.ps1`、
  `package.py`、`make_pin_xdc.py`、`platform.tcl`、`src/`、`include/`、`drivers/`、`loader/`
- `module_14_lm_head_v3_1/constraints/lm_head_v31_ddr4_pins.xdc`
- `module_14_lm_head_v3_1/standalone/`：`src/pl_ddr_layout.h`、`src/main.c`、
  `scripts/*`、`prepare_mailbox.py`、`board_profile.py`、`program_board_tcp.ps1`
- `module_14_lm_head_v3_1/reports/board_v31_20261019/BOARD_PLAN.md` 与 `evidence/`
- 根 `BLOCKER-t-mvf361si-01k-ktoa.md`

未修改：v3 源码/报告/交付/ZIP、根 `AGENTS.md`、`开发日志.*`。

## 遗留问题

1. **板卡物理不可达**（阻塞 M2）：需接 JTAG、上电、接 PS 网口并把 PC 设回
   192.168.0.12/24；恢复后按 `reports/board_v31_20261019/BOARD_PLAN.md` 继续。
2. 实现/时序/DRC 与本轮 bit/XSA 结果以 `reports/board_v31_20261019/hardware/` 为准
   （若本文件写成时构建尚未收尾，则为 NOT_RUN，不得引用为 PASS）。
3. PL 侧 DDR4 RESET 在手册第 18 页的确切引脚是 `IO_L14N_T2L_N3_GC_64 / AM5`
   （首次提取时被截断，已补入 XDC 与生成器）；MIG 要求该端口必须落位，
   否则 opt_design 报 `Port(s) c0_ddr4_reset_n_0 is/are not placed`。
4. M2 的数值、性能、稳定性和 DDR 带宽均为 NOT_RUN，不得以离线结果替代。
