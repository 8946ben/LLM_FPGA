# 200 MHz 独立上板候选（2026-10-19）

状态：真实板测 PASS。两版本同板各55项验收完成，200 MHz的IP median/P95为
117.751805/117.751890 ms，相对100 MHz提升1.90968倍，1000次连续调用通过。
完整报告：[`RESULT.md`](../../reports/board200_20261019/RESULT.md)。

保持 2026-10-16 `reduce_layers` 候选的计算源码逐字节不变；头文件仅把
`build_config` 从 `0x10008011` 改为 `0x20c08011`。其中 CLOCK_CODE=3、
MODULE_REVISION=2，采用 `doc/0924/PS_PL 全模块参数与接口字段说明书.md` 4.2 的编码。
算术仍为 BF16 输入、H8/V1、16 交错累加、FP32 相邻 lane 树，ABI 仍为 V2。
该目录是独立 M14 工程，不涉及整体 LLM 集成。

构建使用 G: 的 Xilinx 2021.1。原 100 MHz 源码、工程、已验收交付包和
2026-10-16 诊断证据均保留。新产物位于 `build/board200_20261019/`、
`board/build/m14_board200_20261019/` 和 `reports/board200_20261019/`。

在模块目录执行，按顺序检查每步成功标志：

```powershell
& .\experiments\board200_20261019\run_hardware.ps1 -Stage hls
& .\experiments\board200_20261019\export.ps1
& .\experiments\board200_20261019\run_hardware.ps1 -Stage create_bd
& .\experiments\board200_20261019\run_hardware.ps1 -Stage build
& .\experiments\board200_20261019\build_software.ps1
$py='C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py .\experiments\board200_20261019\package.py
$pkg=Join-Path $PWD 'reports\board200_20261019\package'
& .\standalone\program_board_tcp.ps1 -PackageDir $pkg -LoaderPackageDir $pkg -BoardIP 192.168.0.190
& .\standalone\run_acceptance.ps1 -PackageDir $pkg -PythonExe $py
```

完整构建脚本保护已有项目；重试失败步骤前先分析原因，不覆盖已有证据。
PS 初始化必须来自这份 200 MHz XSA。不要沿用旧 loader 包的 100 MHz `psu_init.tcl`。
切换 100/200 MHz 版本时必须完整初始化，不使用 `-RetainHardware`；仅同一镜像和
时钟配置已确认保留时，才可使用该选项。
本次 loader 保留已修复的 tcp_output 重试逻辑，只改变 IP 到 `192.168.0.190/24`，
网关为 0（直连），配合 PC 有线 `192.168.0.12/24`。旧加载器及其默认 `.8` 网段保留。
加载权重需要完整 SHA256、逐块 DDR CRC、最终 DDR CRC 和 JTAG sentinel 均通过。

`RUN_PROFILE.json` 与 bit、XSA、初始化脚本及 ELF 一起冻结并记录 SHA256。
加载前校验硬件/loader 配套和 IP；mailbox 解析与严格验收根据该 profile 检查
`build_config` 并换算 IP 耗时。200 MHz 数据写入 `ip_seconds`，不会冒用
`ip_seconds_100mhz`。无 profile 的历史包仍按原 100 MHz 处理。

IP 时间 = `perf_cycles_total / 200000000`；A53 时间 = `wall_ticks / timer_counts_per_second`。
前者使用标称 PL 时钟；Vivado 配置模型约 199.998001 MHz，仅约 10 ppm 差异，
不能称为频率计实测。A53 时间包含提交、轮询和结果校验，不含初次加载权重和主机 JTAG。
30 次独立单调用统计 median/P95/max；1000 次连续调用用于稳定性验证。
预估与真实上板结果必须区分，结论以 `reports/board200_20261019/` 后续测试报告为准。
