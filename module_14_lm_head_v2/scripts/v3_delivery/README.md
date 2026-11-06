# lm_head v3 · M14 独立 200 MHz

发布版本：`M14_V3_20261019_r1`，2026-10-19，负责人张本。
在 ALINX AXU9EGB / XCZU9EG-2FFVB1156I 上完成真实板测。

| 指标 | lm_head v2 / 100 MHz 同板复测 | lm_head v3 / 200 MHz |
|---|---:|---:|
| IP median | 224.868020 ms | 117.751805 ms |
| IP P95 | 224.868020 ms | 117.751890 ms |
| A53 wall median | 224.886149 ms | 117.767348 ms |
| 连续1000调用 | 224.879291 s | 117.759180 s |

`速度比 = 224.868020 / 117.751805 = 1.9096779`；延迟降低47.635148%。
每版本30次独立生产调用，另有3次预热；P95为nearest-rank第29/30个有序样本。
IP值按包内标称时钟换算；A53 timer为33333000 counts/s，包含提交/轮询/结果校验。
两者均不含首次权重加载和主机JTAG搬运；不代表整体LLM token速度。

发布名v3对应 ABI V2、HLS top `lm_head_v2`、IP `user.org:llm_fpga:lm_head_v2:2.1`、
build_config `0x20c08011`、capabilities `0x182`。接口寄存器结构沿用原版。
保留技术符号便于复用驱动；镜像和计算源码与已板测版本逐文件SHA256一致。

## 内容与入口

- `src/`、`include/`、`tb/`：正式200 MHz源码、头文件和测试台。
- `ip_repo/lm_head_v2/`：完整导出IP，VLNV版本2.1；`drivers/`：逻辑与生成PS驱动。
- `interface/`：机器接口JSON、寄存器CSV、硬件profile；`module_manifest.json`：版本/验证身份。
- `reports/hls/`、`reports/implementation/`：真实综合和布线报告，含post-route DCP。
- `reports/board_package_lm_head_v3/`：匹配的bit/XSA/ELF/PS init/profile及ARTIFACTS.sha256。
- `reports/board200_20261019/RESULT.md`：完整实测对比；`reports/board_runs/`：两版本原始mailbox/logits。
- `reference/`、`golden/`、包根`artifacts/module14_v2_assets/`：Python参考、8步golden与一份canonical BF16权重。
- `reports/rtl/`、`verification/`：规约候选历史RTL/Native验证证据；正式板测见board200报告。
- 包根`provenance/`：源/镜像身份与路径迁移。原始报告中的绝对路径是历史证据。

## 离线复核

先在包根目录安装 `requirements.txt`（现有Python已具备numpy时无需重复安装），然后执行：

```powershell
python -B .\module_14_lm_head_v3\scripts\run_tests.py
```

检查SHA256完整性、IP文件引用/寄存器、镜像配套、11项Python回归、源码合同、
BF16权重与8步资产、110份原始mailbox及两份55项campaign。执行过程不访问板卡。
`campaign.json`保留原始路径，`campaign_portable.json`只重定位路径，数值未改。

## 上板使用

PC有线 `192.168.0.12/24`，连接板卡PS网口。修复版loader使用 `192.168.0.190:1414`。
以下在模块目录（本README所在目录）执行，需Xilinx Vitis 2021.1 XSCT与Python：

```powershell
$py=(Get-Command python -ErrorAction Stop).Source
$pkg=Join-Path $PWD 'reports\board_package_lm_head_v3'
& .\standalone\program_board_tcp.ps1 -PythonExe $py -PackageDir $pkg -LoaderPackageDir $pkg -BoardIP 192.168.0.190
# 上一步所有校验PASS后：
& .\standalone\run_step.ps1 -Step step_00 -PythonExe $py -PackageDir $pkg
& .\standalone\run_acceptance.ps1 -PythonExe $py -PackageDir $pkg
```

XSCT默认路径为`G:\Xilinx\Vitis\2021.1\bin\xsct.bat`，可用`-Xsct`指定其它安装位置。
大权重走TCP，JTAG用于初始化/PL配置、小ELF/输入/mailbox和采集；不默认通过JTAG传272MB权重。
主机SHA256、逐块DDR回读CRC、最终全DDR CRC和首尾sentinel通过后才启动IP。
加载失败整份重传。100/200版本切换需完整初始化，不用`-RetainHardware`。
PS初始化必须与镜像配套。权重断电丢失，测试ELF运行后无lwIP，ping/TCP不响应属预期。

## 重建入口

Xilinx Vitis HLS/Vivado/Vitis 2021.1；器件`xczu9eg-ffvb1156-2-i`；HLS 5.000 ns、uncertainty1.350 ns。
在模块目录执行：

```powershell
& .\scripts\run_hls.ps1 -Action csim -VitisHls 'G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat'
& .\scripts\run_hls.ps1 -Action export -VitisHls 'G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat'
& .\board\run_vivado.ps1 -Action create_bd
& .\board\run_vivado.ps1 -Action build
& .\standalone\build_software.ps1
```

HLS小尺寸cosim入口为`-Action cosim`；已包含2021.1向量别名与core_revision局部修复。
board脚本优先选新导出的IP，否则使用随包IP。重建硬件输出`reports/rebuilt_hardware/`；
软件输出`build/board200_20261019/software/`，冻结包保持原实测身份。
修改/重建后的新产物需形成新匹配包并重新验收。

## 验证边界

H=896、V=151936、Decode、penalty ON、H8/V1；8步生产/完整logits逐位一致，
错误参数/数值路径、受控错误golden、30独立计时及1000连续调用通过。
当前trace来自既有FP16输入转换BF16。原生M06、Prefill36/64、全模型集成、
扩展模式/地址边界/极值矩阵均未在本次验证；不作为本轮已完成事项。
PS时钟链寄存器已回读，配置模型约199.998001 MHz；无外部频率计或HP2 APM测量。
完整接口约束与计数器语义见interface JSON及NUMERIC_CONTRACT.md。
