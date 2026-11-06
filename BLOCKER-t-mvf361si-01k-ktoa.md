# BLOCKER t-mvf361si-01k-ktoa · lm_head v3.1 真实板测被物理连接阻塞

## 版本 / 环境

- 任务：t-mvf361si-01k-ktoa（luyou，发起方 codex-1，执行节点 workbuddy）
- 工作树：`D:/program/LLM_FPGA`，新模块 `module_14_lm_head_v3_1/`
- 工具：Vivado / Vitis / Vitis_HLS 2021.1（G:/Xilinx），Python `C:/Users/ben/.cache/codex-runtimes/...`
- 板卡：AXU9EGB（xczu9eg-ffvb1156-2-i），loader 计划 192.168.0.190:1414
- 时间：2026-10-19 18:05 起

## 现象（最小复现）

1. JTAG 无目标：

```powershell
& 'G:\Xilinx\Vitis\2021.1\bin\xsct.bat' -eval "connect; puts [targets]; disconnect"
# TARGETS_BEGIN
# TARGETS_END
# M14_V31_JTAG_TARGETS=0
```

证据：`module_14_lm_head_v3_1/reports/board_v31_20261019/evidence/jtag_probe_20261019.log`

2. 有线网口未连接：

```
以太网  Disconnected
（无 192.168.0.12/24 地址）
ping 192.168.0.190 → 100% 丢失
Test-NetConnection 192.168.0.190 -Port 1414 → False
```

证据：`module_14_lm_head_v3_1/reports/board_v31_20261019/evidence/board_network_20261019.txt`

3. 设备管理器无 Xilinx/Digilent JTAG 设备（`Get-PnpDevice` 过滤为空），也没有其他
   hw_server 占用 3121 端口——不是并发占用，而是物理未连接/未上电。

## 已尝试

- 18:06 与 19:17 两次 JTAG 探测，均为 0 目标。
- 两次网口/端口探测，均不通。
- 未尝试任何烧写、复位或 DDR 访问；未终止任何其他进程。
- 按任务书“明确需要人工断电/接线时立即升级”，不继续消耗预算重试。

## 改动（已完成，等待复核）

- 新增 `module_14_lm_head_v3_1/`：HLS 源码（仅身份常量改为 build_config
  `0x30c08011`、capability 新增 PL DDR bit 9）、MIG BD 脚本、引脚 XDC 生成器、
  loader/测试程序 PL DDR 适配、package/profile 脚本、README/PROGRESS。
- 未修改 v3 源码、reports、deliverables、ZIP 或根开发日志。
- 构建产物位于 `module_14_lm_head_v3_1/build/board_v31_20261019/`。

## 进程与板卡状态

- 本任务启动的 Vivado/HLS 进程在构建结束后退出；未留常驻服务。
- 板卡状态未知（不可达），没有烧写任何镜像，PS DDR / PL DDR 内容未被本任务改变。

## 需要的动作

人工确认并恢复：

1. JTAG（USB 下载器）与板卡 12 V 供电；
2. PC 有线口接到板卡 PS 网口，并确认 PC 为 192.168.0.12/24；
3. 板卡上电后重新派发或续办本任务，从 M2 开始执行
   `module_14_lm_head_v3_1/reports/board_v31_20261019/BOARD_PLAN.md`。

M2 数值/性能/稳定性结论在恢复连接前必须保持 NOT_RUN，不能以离线构建结果替代。
