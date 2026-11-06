# M14 V2 交付说明（2026-10-10，r1）

交付给：汇总负责人喻燕萍；模块负责人：张本。范围为优化后的 M14 LM Head V2。
交付状态为 **独立 Decode/penalty ON 板测通过、待统一集成的候选版**。
公共 ABI 枚举及地址、超时 class 尚待架构负责人冻结；本包不宣称最终统一集成验收。

## 规范对应与内容

依据包内 `specifications/` 的两份 0924 文档：架构计划 §20、§27、§32.2，字段说明 §27～§29。
模块目录包含源码、HLS 头文件、testbench、reference/golden、可综合 IP、PS 驱动、
HLS/实现/数值报告、接口 JSON/寄存器 CSV、manifest、SHA256SUMS。
包根目录额外包含 canonical BF16 权重、8 步输入与完整 golden、PHY 支持文件、
规范快照、来源记录和交付复核说明。权重仅保存一份，M05 与 M14 可共享只读权重。

| 交付问题 | 当前答案 |
| --- | --- |
| 输入 | final RMSNorm 的最后一行，896 个 BF16；共享 `[151936,896]` BF16 权重；可选 history bitmap |
| 输出 | token uint32、penalty 后 selected_score FP32；debug 可写 penalty 前 raw logits |
| 布局与容量 | 详见 `interface/interface_contract.json`，所有活动 buffer 64-byte 对齐，little-endian |
| Prefill/Decode | 同一物理 IP；run_mode=0/1；两者 valid_rows=1。上游 T=36/64 时由 PS 选择最后一行，不把整段传给 M14 |
| reference 一致性 | 实板 8 步生产/debug token、score bits、CRC 和全部 151936 logits/step 逐位一致 |
| T=1 与最大 Prefill | 独立 Decode T=1 已板测；原生 Prefill T=36/64 的上游最后一行选择与 M06 V2 链路待集成验证 |
| 资源与时序 | 完整单模块 BD post-route：LUT 31290、FF 42618、BRAM tile 22、DSP 59；100 MHz WNS +3.649 ns、WHS +0.010 ns，DRC error=0 |
| 性能 | 30 次独立生产采样，IP median/P95=224.868020 ms，A53 wall median=224.886284 ms、P95=224.886629 ms；1000 次连续调用 PASS |
| 大权重加载 | 修复版 TCP loader：272269312 bytes，含块/全 DDR CRC 校验 8.3338715 s，31.1567 MiB/s；JTAG 仅初始化与小文件/结果 |
| 当前问题 | 公共 ABI、Prefill/penalty OFF 等性能矩阵、边界地址与 M03 校验、HP2 外部 APM、M06 原生 BF16 trace、整机集成待完成 |

资源是现有单模块实现的整张 BD 统计，不能当作纯 HLS kernel 独立占用；
性能只对应 Decode/penalty ON/H8/V1，不外推其他模式。旧 11.09 s 与新 IP 时间为跨口径比较，
本交付不把其比值作为整机端到端加速承诺。8 步 hidden 来源为历史 FP16 trace 转 BF16，
不是原生 M06 V2 输出。HLS 的顶层 latency 为动态/未知；dot_word_loop II=1。

## 接收与离线复核

完整解压 ZIP，保留模块与 `artifacts/` 的兄弟目录关系。Python 3.12 + NumPy 2.3.5
为此次复核环境，依赖在 `requirements.txt`。在包根目录执行：

```powershell
python -m pip install -r requirements.txt
python module_14_lm_head_v2/scripts/run_tests.py
```

该入口检查包内文件 SHA256、IP 文件引用、生成寄存器表、11 项 Python 回归、
源代码合同、全部资产 hash、55-run campaign 的独立统计和 raw logits SHA256。
不连接板卡，不自动重新综合或下载。输出 `DELIVERY_OFFLINE_VERIFY=PASS` 才视为离线复核通过。
板测 evidence 是历史真实运行记录，离线复核不构成新一轮板测。

`campaign.json`、mailbox、logits、日志等原始证据保留原样；`campaign_portable.json`
仅将 source_run/package_dir 改为相对路径，其他数值不变。
原始日志中的 `D:\program\LLM_FPGA` 为测试时路径，不是接收端依赖。
`SHA256SUMS` 覆盖归档内容；顶层校验不包括其自身。执行复核后生成的 build 目录不属于冻结交付内容。

## IP 与驱动接入

Vivado/Vitis HLS/Vitis 均使用 **2021.1**，器件 `xczu9eg-ffvb1156-2-i`。
将 `module_14_lm_head_v2/ip_repo/lm_head_v2` 加入 Vivado IP repository，
VLNV `user.org:llm_fpga:lm_head_v2:2.0`。源码重建可运行：

```powershell
./module_14_lm_head_v2/scripts/run_hls.ps1 -Action export -VitisHls '你的路径/vitis_hls.bat'
./module_14_lm_head_v2/board/run_vivado.ps1 -Action create -VivadoBin '你的路径/vivado.bat'
./module_14_lm_head_v2/board/run_vivado.ps1 -Action build -VivadoBin '你的路径/vivado.bat'
```

HLS wrapper 包含 2021.1 日期溢出导致 IP 打包 core_revision 失败的修复。
解压后没有 HLS build 时 BD 使用冻结 `ip_repo`；执行 export 后若新 build 的 component.xml 存在，
BD/verify-ip 优先使用新导出目录。接收端仅集成冻结 IP 时无需先执行 export。
重新导出的 IP 与本包冻结 IP 是不同构建产物，需重新实现与验收，不直接沿用历史板测结论。
驱动使用 `drivers/lm_head_v2_driver.*`、`lm_head_v2_mmio.*` 和 HLS 生成驱动/BSP；
`drivers/generated/xlm_head_v2_hw.h` 是寄存器偏移的来源。不要直接把 job struct 当 M00 网络 wire format。
示例 control base `0xA0000000` 和 DDR 分配仅用于独立板测，汇总后由 M02/M03 分配。

提交前 M03 验证 active buffers 的物理范围、容量、布局、owner/generation、alias；
clean 输入/只读权重，权重 immutable 时可只 clean 一次；运行后 invalidate debug logits。
生产 write_logits=0 时不要求 logits buffer，不发生 logits 写事务。
M05/M14 可指向同一 canonical 只读权重，禁止输出与活动输入重叠；当前本地驱动不替代 M03 范围/alias 检查。
flags 0～3 合法，CRC 由 bit0 控制；perf 当前始终填写，bit2/3 不提供额外 snapshot/全系统 strict validation。
`write_logits` 是独立参数，不能仅设置 flags bit2 来要求 logits。

## 独立板测复现

板卡 AXU9EGB，PC 有线 `192.168.8.12/24`，板卡 `192.168.8.190:1414`。
先确认没有其他板测正在运行，加载会替换 A53 程序并覆盖整个权重区。断电后必须重载。
工具实际路径通过参数传入；Python 路径必须为真实可执行文件路径。

```powershell
$pythonExe = (Get-Command python).Source
$xsctExe = '你的路径/xsct.bat'
./module_14_lm_head_v2/standalone/program_board_tcp.ps1 -PythonExe $pythonExe -Xsct $xsctExe
./module_14_lm_head_v2/standalone/run_step.ps1 -Step step_00 -PythonExe $pythonExe -Xsct $xsctExe
./module_14_lm_head_v2/standalone/run_step.ps1 -Step step_00 -WriteLogits -PythonExe $pythonExe -Xsct $xsctExe
```

冷启动默认初始化 PS/PL；只有 PL/DDR 已初始化且无任务运行时才用 `-RetainHardware`。
主机 canonical SHA256、每块 DDR CRC32、整份 DDR CRC32、首尾 sentinel 全部通过后才测 IP。
中断/错误后整份重传，不支持续传。详见 `standalone/TCP_WEIGHT_LOADING.md`。
默认使用冻结数值包 `reports/board_package_20261009` 与修复版
`reports/tcp_loader_package_20261010`，保留原日期便于对应真实板测产物。
需重建 A53 程序时运行 `standalone/run_build.ps1`；TCP loader 用 `build_tcp_loader.ps1`。
新 ELF 不自动替换冻结板测包，须显式归档并重新验证。

## 待汇总负责人处理的集成门槛

1. 用统一生成的公共 ABI header 替换本地 enum/结构，冻结 layout/dtype/owner/instance 枚举、地址和 timeout class；当前 instance_id 留空待分配。
2. 补原生 M06 V2 BF16 trace；验证 Prefill 36/64 最后一行选择和同一 IP 的 Prefill 分支，以及 penalty OFF/debug 性能矩阵。
3. 在 M03 侧完成容量、越界、重叠和 descriptor 生命周期验证，补边界地址测试；声明的错误状态码不代表硬件已实现所有对应检查。
4. 补 HP2 外部 APM/protocol monitor；内部拍计数含模型计数，不能充当总线实测。
5. 单模块使用 PS DDR、四个 master 经同一 HP2；不含 PL DDR/MIG。整机互连、DDR ready/reset/profile 门槛由 M02 复核。

以上门槛已填入 manifest 和机器接口表，未完成项均标为 pending，不以 N/A 掩盖。
