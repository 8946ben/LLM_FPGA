# AXU9EGB 模块 16 真实板卡调试日志

> 开始日期：2026-07-24  
> 操作者：zb  
> 板卡 IP：`192.168.8.190`  
> 上位机有线 IP：`192.168.8.12/24`  
> 记录规则：每一步记录目的、命令/操作、结果、问题、原因、修复和后续动作。

## 日志索引

| 编号 | 阶段 | 内容 | 状态 |
| --- | --- | --- | --- |
| 001 | 基础连接 | 上位机网卡、Ping、ARP、TCP 端口检查 | 完成 |
| 002 | 阶段 A | Python 单元测试 | 完成 |
| 003 | 阶段 A | 黄金数据 SHA-256 | 完成 |
| 004 | 阶段 A | 全尺寸 HLS C 真实 trace 回归 | 完成 |
| 005 | 阶段 B | 新增 HLS IP 导出脚本 | 完成 |
| 006 | 阶段 B | 首次导出与 `core_revision` 溢出 | 已修复 |
| 007 | 阶段 B | 沙箱内重打包写权限失败 | 已修复 |
| 008 | 阶段 B | 沙箱外 Vivado 重打包 | 完成 |
| 009 | 阶段 B | IP 文件、驱动和 AXI 接口核对 | 完成 |
| 010 | 阶段 B | Vivado Catalog 验证参数顺序错误 | 已修复 |
| 011 | 阶段 B | 兼容脚本误判 Vitis 退出码 | 已修复 |
| 012 | 阶段 B | 兼容导出与最终 Catalog 验收 | 完成 |
| 013 | 阶段 C | 同事资料、板卡手册和官方资料核对 | 完成 |
| 014 | 阶段 C | 探测 Vivado 2021.1 Zynq PS 属性 | 完成 |
| 015 | 阶段 C | Block Design 第 1～4 次创建与修复 | 已修复 |
| 016 | 阶段 C | 第 1～4 次综合/实现尝试与修复 | 已修复 |
| 017 | 阶段 C | 首版 XSA 内容审计发现 PS DDR 未启用 | 已修复 |
| 018 | 阶段 C | 补齐 4 GB DDR 暂定配置并重建 BD | 完成 |
| 019 | 阶段 C | 第 5 次综合、实现、bitstream 和 XSA | 完成 |
| 020 | 阶段 C | DDR4-2400 暂定版 XSA、时序和摘要核验 | 已归档 |
| 021 | 阶段 C 校准 | 清点同事完整 AXU9EGB Vivado 工程 | 完成 |
| 022 | 阶段 C 校准 | 1111 项 PS 参数对比及 DDR 判断更正 | 完成 |
| 023 | 阶段 C 校准 | 对齐参考工程并重建 Block Design | 完成 |
| 024 | 阶段 C 校准 | 参考对齐版综合、实现、bitstream 和 XSA | 完成 |
| 025 | 阶段 C 校准 | DDR 初始化精确比对与最终基线验收 | 完成 |

---

## 001 - 基础网络连接检查

### 目的

在下载任何 bitstream 或发送模型数据前，确认物理网口、IPv4 网段和板卡基础网络可达。

### 操作和命令

```powershell
ipconfig.exe
ping.exe -n 4 192.168.8.190
arp.exe -a 192.168.8.190
Test-NetConnection -ComputerName 192.168.8.190 -Port 50052
```

### 结果

```text
上位机有线 IPv4：192.168.8.12/24
板卡 IPv4：192.168.8.190/24
板卡 MAC：00-0a-35-00-01-02
Ping：4/4 成功，0% 丢包
RTT：0-1 ms
TCP 50052：未监听
```

### 遇到的问题

沙箱权限下执行 `Get-NetIPConfiguration` 时，Windows CIM/WMI 返回“拒绝访问”；当前 PowerShell 的 `Test-Connection` 版本也不支持 `-TargetName` 参数。

### 修复

改用无需 CIM 权限的传统只读命令：

```powershell
ipconfig.exe
ping.exe
arp.exe
```

### 结论

物理链路和 IPv4 连接正常。TCP 50052 未监听只表示当前板端没有运行 RMSNorm 示例服务或使用了其他端口，不属于网络连接失败。

---

## 002 - Python 单元测试

### 目的

冻结协议、CRC、FP16、repetition penalty 和 argmax 的主机侧行为。

### 命令

```powershell
python -m unittest discover -s tests -v
```

实际使用 Codex 工作区 Python：

```text
C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

### 结果

```text
Ran 10 tests
OK
10/10 PASS
```

---

## 003 - 黄金文件 SHA-256

### 目的

后续上传权重和 trace 时，用摘要排除文件被替换或损坏。

### 命令

```powershell
Get-FileHash -Algorithm SHA256 `
  artifacts\model.embed_tokens.weight.fp16.npy, `
  artifacts\module16_hls_fixtures\step_00\hidden.fp16.bin, `
  artifacts\module16_hls_fixtures\step_00\history_bitmap.u32.bin, `
  artifacts\module16_hls_fixtures\step_00\golden_logits.fp16.bin
```

### 结果

```text
F4E43CEC9B007816CB7C81940C13CAB0CE644A69236DA97F13F1C4064D65112D  artifacts/model.embed_tokens.weight.fp16.npy
1A3187539B5DE201933F7195B460A8C358C6489495209BC73178A5FB44BC84B3  artifacts/module16_hls_fixtures/step_00/hidden.fp16.bin
F364F5E37109D19C35F42F2FB9B1AE8F6D210B437BC228B3C3F88C9C49C30EF4  artifacts/module16_hls_fixtures/step_00/history_bitmap.u32.bin
ED458EDFDDE7B51024A30F9BC7042B0C8C3B79BC2BCB9123241CD984EED53873  artifacts/module16_hls_fixtures/step_00/golden_logits.fp16.bin
```

---

## 004 - 全尺寸 HLS C 回归

### 目的

在上板前确认当前 HLS 源码、官方权重和 8 步真实 trace 的数值行为未发生变化。

### 命令

```powershell
D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat `
  -f module16_lm_head_hls\run_csim.tcl
```

### 时间

```text
开始：2026-07-24 16:33:30
结束：2026-07-24 16:36:47
Vitis 报告耗时：195.574 s
```

### 结果

```text
synthetic：PASS
step_00 至 step_07：8/8 PASS
token：8/8 完全匹配
Top-5：每步 5/5
最大绝对误差：0.015625
HLS_CSIM_OVERALL=PASS
```

### 误差说明

`max_abs_error` 比较的是：

```text
HLS 内核计算的 FP16 raw_logits
与
Qwen/PyTorch 保存的 lm_head_vocab_logits 转换后的 FP16 golden logits
```

它不直接比较 repetition penalty 后的 processed scores。`0.015625` 等于 16-32 数值区间的一个典型 FP16 间隔；结合 cosine=1、Top-5=5/5 和 token 8/8，属于不同浮点归约顺序造成的正常舍入差异。

---

## 005 - 新增 HLS IP 导出脚本

### 目的

把已验证的 `lm_head_argmax` 从 HLS 工程导出为 Vivado IP Catalog 包。

### 新增文件

```text
module16_lm_head_hls/run_export_ip.tcl
```

### 关键配置

```tcl
set_top lm_head_argmax
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5 -name default
csynth_design
export_design -format ip_catalog -rtl verilog
```

---

## 006 - 首次 IP 导出失败：core_revision 溢出

### 命令

```powershell
D:\install\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat `
  -f module16_lm_head_hls\run_export_ip.tcl
```

### 时间

```text
开始：2026-07-24 16:39:03
失败：2026-07-24 16:39:34
```

### 已成功的部分

```text
目标器件：xczu9eg-ffvb1156-2-i
目标周期：5 ns
HLS 综合成功
Estimated Fmax：273.97 MHz
点积 Final II：8
Verilog 和驱动源文件已生成
```

### 错误

```text
ERROR: '2607241639' is an invalid argument. Please specify an integer value.
rdi::set_property core_revision 2607241639
ERROR: [IMPL 213-28] Failed to generate IP.
```

### 原因

Vitis HLS 2021.1 把当前时间按 `YYMMDDHHMM` 写入 `core_revision`。2026-07-24 16:39 被编码成 `2607241639`，超过 Vivado 该属性允许的 signed 32-bit integer 范围。

这不是 HLS 内核、AXI 接口或板卡器件错误。

### 修复

修改自动生成的：

```text
module16_lm_head_hls/build/lm_head_export/solution1/impl/ip/run_ippack.tcl
```

把：

```tcl
set Revision "2607241639"
```

改为稳定合法值：

```tcl
set Revision "1"
```

---

## 007 - 沙箱内重打包失败：Vivado 写权限

### 第一次重试

```powershell
.\pack.bat
```

错误：

```text
Failed to open handle vivado.jou
Failed to open handle vivado.log
error deleting "hdl/ip": permission denied
```

### 第二次重试

为避开首次失败留下的生成目录，将打包脚本临时改为：  

```tcl
set ipdir "hdl/ip_repack"
set prj "tmp_repack"
```

并使用新日志名：

```powershell
vivado.bat -notrace -mode batch -source run_ippack.tcl `
  -log repack.log -journal repack.jou
```

错误：

```text
Failed to open handle repack.jou
Failed to open handle repack.log
can't create directory "hdl/ip_repack": permission denied
```

### 原因

Vivado 子进程在当前沙箱权限下不能向 HLS build 的打包目录创建日志和子目录。目录本身不是 Windows 只读，且没有残留的 Vivado/Vitis HLS 进程。

### 修复

仅对 Vivado batch 打包命令申请工作区外层执行权限；目标仍限定为：

```text
module16_lm_head_hls/build/lm_head_export/solution1/impl/ip
```

不会连接、下载或修改开发板。

---

## 008 - Vivado 重打包成功

### 命令

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -notrace -mode batch `
  -source run_ippack.tcl `
  -log repack.log `
  -journal repack.jou
```

### 时间

```text
完成：2026-07-24 16:52:20
退出码：0
```

### 结果

Vivado 成功生成所有浮点子 IP 的 synthesis/simulation target，并正常退出。下一步需核对：

- `component.xml`；
- IP archive ZIP；
- 四个 m_axi 接口；
- AXI-Lite 控制接口；
- 自动生成驱动函数和寄存器。

---

## 009 - IP 文件、驱动和接口核对

### 操作

检查最终 IP 目录、ZIP 内容、驱动 API、寄存器和 `component.xml`：

```powershell
tar.exe -tf xilinx_com_hls_lm_head_argmax_1_0.zip
rg XLm_head_argmax_ drivers/lm_head_argmax_v1_0/src/xlm_head_argmax.h
rg ADDR_ drivers/lm_head_argmax_v1_0/src/xlm_head_argmax_hw.h
rg m_axi_gmem component.xml
```

### 一次无副作用的命令错误

首次组合查询的 PowerShell 字符串中包含未正确转义的双引号，解释器返回：

```text
字符串缺少终止符
```

该命令在语法解析阶段失败，没有读取、生成或修改 IP 文件。修复方法是把 `rg` 正则改用单引号并拆分查询。

### 产物

```text
component.xml
xilinx_com_hls_lm_head_argmax_1_0.zip
drivers/lm_head_argmax_v1_0/
hdl/verilog/lm_head_argmax.v
```

ZIP 内确认包含：

```text
component.xml
hdl/verilog/lm_head_argmax.v
drivers/lm_head_argmax_v1_0/src/xlm_head_argmax.h
```

### 驱动接口

确认存在：

```text
XLm_head_argmax_Initialize
XLm_head_argmax_Start
XLm_head_argmax_IsDone
XLm_head_argmax_IsIdle
XLm_head_argmax_IsReady
XLm_head_argmax_Set_hidden
XLm_head_argmax_Set_weight
XLm_head_argmax_Set_history_bitmap
XLm_head_argmax_Set_raw_logits
XLm_head_argmax_Set_hidden_size
XLm_head_argmax_Set_vocab_size
XLm_head_argmax_Set_write_logits
XLm_head_argmax_Set_enable_repetition_penalty
XLm_head_argmax_Set_repetition_penalty
XLm_head_argmax_Get_selected_token
XLm_head_argmax_Get_selected_score
```

四个地址参数均为 `u64`。`repetition_penalty` 和 `selected_score` 在寄存器驱动中以 `u32` 传递其 IEEE-754 bit pattern，板端软件必须使用按位拷贝转换。

### AXI 接口

确认 `component.xml` 包含：

```text
s_axi_control
m_axi_gmem_hidden
m_axi_gmem_weight
m_axi_gmem_history
m_axi_gmem_logits
ap_clk
ap_rst_n
```

当前四个 m_axi 数据宽度均为 32 bit。该宽度满足功能上板要求，但会限制带宽，记录为后续性能优化项；第一次上板不修改接口。

---

## 010 - Vivado Catalog 验证参数顺序错误

### 新增验证脚本

```text
realFpga/vivado/verify_lm_head_ip.tcl
```

它创建内存工程、加载用户 IP Repository，并要求只找到一个 `lm_head_argmax` IP definition。

### 首次命令

首次把 `-log/-journal` 放在 `-tclargs` 之后，Vivado 将它们也传给 Tcl：

```text
Usage: ... -tclargs <ip_repository>
$argc != 1
```

此时 IP 尚未加载，所以不是 IP 错误。

### 修复

将参数顺序改为：

```powershell
vivado.bat `
  -mode batch `
  -log <log> `
  -journal <jou> `
  -source verify_lm_head_ip.tcl `
  -tclargs <ip_repository>
```

### 复测结果

```text
LMH_IP_VERIFY=PASS
LMH_IP_VLNV=xilinx.com:hls:lm_head_argmax:1.0
LMH_IP_NAME=lm_head_argmax
LMH_IP_VERSION=1.0
```

---

## 011 - 兼容脚本误判 Vitis 退出码

### 目的

新增可重复执行的：

```text
module16_lm_head_hls/run_export_ip_2021_compat.ps1
```

预期自动执行：

```text
HLS 综合
-> 尝试导出
-> 识别 2026 core_revision 溢出
-> revision 固定为 1
-> Vivado 重新打包
```

### 首次复测发现的问题

Vitis HLS 日志明确报告：

```text
ERROR: [IMPL 213-28] Failed to generate IP.
```

但 Windows `vitis_hls.bat` 返回的 `$LASTEXITCODE` 仍为 0。兼容脚本只检查退出码，因此错误输出：

```text
LMH IP export completed without compatibility workaround.
```

同时 HLS reset 已移除上一份 `component.xml`。

### 原因

Vitis HLS 2021.1 的 batch 包装层没有可靠地把内部 `export_design` 错误传播到 Windows 进程退出码。

### 修复

兼容脚本改为同时检查：

```powershell
$hlsExitCode -eq 0
并且
Test-Path component.xml
```

只有两个条件都成立才判断原生导出成功。否则检查 `run_ippack.tcl` 中 revision 是否超过 signed 32-bit，并执行兼容打包。

---

## 012 - 兼容导出与最终 Catalog 验收

### 完整复测命令

```powershell
module16_lm_head_hls\run_export_ip_2021_compat.ps1
```

### 时间和结果

```text
开始：2026-07-24 17:02:01
HLS 原生打包按预期触发 revision 溢出
兼容脚本自动改写 revision
Vivado 重打包完成：2026-07-24 17:02:33
脚本退出码：0
```

最终输出：

```text
LMH IP export completed after applying the Vitis HLS 2021.1 core_revision workaround.
```

### 最终 Vivado Catalog 验收

```text
完成：2026-07-24 17:05:48
LMH_IP_VERIFY=PASS
VLNV=xilinx.com:hls:lm_head_argmax:1.0
```

验证日志：

```text
realFpga/results/20260724_baseline/verify_lm_head_ip_final.log
```

### 最终摘要

```text
D5B518DDB45B96E5AFAE078F2332B283D99C6C51F536077E364A654944772E64  xilinx_com_hls_lm_head_argmax_1_0.zip
0DFF90C8F6D2DB53B447729D0D20200AB505904260F4A812A6CABFF1F9EC85D9  component.xml
```

### 阶段 B 判定

```text
HLS 综合：PASS
IP 打包：PASS
ZIP 内容：PASS
驱动 API：PASS
AXI 接口：PASS
Vivado IP Catalog：PASS
阶段 B：完成
```

---

## 013 - 同事资料、板卡手册和官方资料核对

> 补充时间：2026-07-24  
> 记录人：zb

### 目的

确认同事工程中可以复用的 PS/PL 拓扑，并从 AXU9EGB 手册核对器件、DDR、网口、串口和参考时钟。

### 操作

递归清点：

```text
D:\program\LLM_FPGA\ref\RMS
```

读取并渲染检查：

```text
D:\program\LLM_FPGA\ref\RMS\Orin-PS-PL 协同通用开发流程.pdf
D:\program\LLM_FPGA\AXU9EGB开发板用户手册.pdf
```

同时查阅 ALINX 的 Zynq UltraScale+ PS 配置教程，核对 MIO 和 DDR preset 名称。

### 结果

同事目录包含 PS C 服务端、Python backend、工具和流程 PDF，但不包含可直接复用的：

```text
.xpr
.bd
.xsa
.xdc
HLS IP repository
```

从资料中确定：

```text
器件：xczu9eg-ffvb1156-2-i
PS DDR：四颗 x16、每颗 1 GB，总容量 4 GB
PS 参考时钟：33.333 MHz
GEM3 RGMII：MIO 64..75
MDIO：MIO 76..77
板卡 UART 引脚：MIO 42..43
```

同事方案的可复用拓扑：

```text
PS M_AXI_HPM0_FPD -> 控制 SmartConnect -> HLS AXI-Lite
HLS m_axi -> 数据 SmartConnect -> PS S_AXI_HP0_FPD -> PS DDR
```

模块 16 比同事的 RMSNorm 多一个数据 master，因此数据 SmartConnect 使用四个 SI。

### 遇到的问题与修复

1. 首次 PDF 文本输出在 Windows GBK 控制台遇到 `U+F06C` 编码错误。  
   修复：使用 UTF-8 输出环境和 UTF-8 控制台。
2. 首次将 PDF 页面渲染到 `C:\tmp` 时没有写权限。  
   修复：改到工作区：

```text
D:\program\LLM_FPGA\tmp\pdfs\lmh_stage_c_review
```

3. 同事目录没有 Vivado/Vitis 工程。  
   处理：保留同事的连接拓扑，板级 PS 参数根据手册和 Vivado 属性重建；明确把同事的已验证 PS 配置列为真实上板前的校准资料。

---

## 014 - 探测 Vivado 2021.1 Zynq PS 属性

### 目的

避免直接套用其他 Vivado 版本的属性名。

### 新增脚本

```text
realFpga/vivado/inspect_zynq_ps_properties.tcl
```

### 命令

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch -nojournal `
  -log D:\program\LLM_FPGA\realFpga\results\20260724_stage_c\ps_property_probe.log `
  -source realFpga\vivado\inspect_zynq_ps_properties.tcl
```

### 结果

确认使用 `zynq_ultra_ps_e:3.3`，并取得时钟、AXI、GEM、UART 和 DDR 属性的实际名称及合法取值。

### 非阻断警告

```text
No write access right to the local Tcl store at 'C'.
XilinxTclStore is reverted to the installation area.
```

原因是 Vivado 将本地 Tcl store 路径解析为 `C` 且不可写；工具自动回退到安装目录，IP Catalog 和建图不受影响。

---

## 015 - Block Design 第 1～4 次创建与修复

### 新增脚本

```text
realFpga/vivado/create_lm_head_axu9eg_bd.tcl
```

每次均用以下形式执行，并把日志分别保存为 `create_bd_attempt1.log` 到 `create_bd_attempt4.log`：

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch -nojournal `
  -log <本次日志> `
  -source realFpga\vivado\create_lm_head_axu9eg_bd.tcl
```

### 第 1 次问题

```text
PSU__M_AXI_GP0__FREQMHZ：只读
PSU__S_AXI_GP2__FREQMHZ：只读
UART1 不接受 MIO 42..43
```

修复：

- 删除只读频率属性，由连接的 `pl_clk0` 自动传播；
- 在 Vivado 2021.1 的 `zynq_ultra_ps_e:3.3` 中使用 `UART0` 属性选择 MIO 42..43。

这里的 `UART0` 是 Vivado IP 属性命名，物理 MIO 与板卡手册一致。

### 第 2 次问题

```text
C_EXT_RESET_HIGH：只读
找不到 DDR/FIXED_IO Block Design 外部接口
```

修复：

- 删除只读复位极性属性；
- 不再创建 DDR/FIXED_IO BD port。Zynq UltraScale+ MPSoC 的 PS DDR 和 MIO 是器件专用引脚，由 PS IP 配置并导出到 XSA，不像旧版 processing_system7 那样显示为普通 BD 外部端口。

### 第 3 次问题

未使用但默认开启的 `M_AXI_HPM0_LPD` 产生未连接时钟错误。

修复：

```tcl
CONFIG.PSU__USE__M_AXI_GP2 {0}
```

### 第 4 次结果

```text
LMH_STAGE_C_CREATE=PASS
目标器件正确
PL 时钟实际 99.999001 MHz
GEM3/MDIO/UART MIO 正确
控制地址 0xA0000000
四条 m_axi 均映射到 HP0 DDR
```

此时仅证明 BD 结构通过，后续 XSA 内容审计发现 DDR 控制器并未真正启用，详见 017。

---

## 016 - 第 1～4 次综合/实现尝试与修复

### 新增脚本

```text
realFpga/vivado/build_lm_head_axu9eg.tcl
```

### 第 1 次问题：沙箱内子进程失败

Vivado 启动综合子进程时：

```text
rundef.js Access denied
```

主批处理一直等待。精确停止本次 Vivado PID 19148 和遗留 `cmd` PID 26352，没有删除工程源文件。

原因：Vivado 的 run manager 需要在工作区外层权限下启动子进程。

修复：仅对 Vivado batch 构建申请工作区外层执行权限，构建目标仍限制在本工程。

### 第 2 次问题：run 状态未复位

```text
synth_1 needs reset
```

修复：在脚本中对 `synth_1` 和 `impl_1` 调用 `reset_run`。

### 第 3 次问题：中断后 OOC run 命令损坏

PS OOC run 的生成命令变成：

```text
vivado -log  -m64 -product Vivado ... -source
```

空的 `-log` 和 `-source` 导致：

```text
Invalid project file name 'Vivado'
```

这不是 PS IP 配置本身失败，而是第一次强制中止后保留的损坏 run 元数据。

修复：构建脚本在启动前执行：

```tcl
delete_runs *_synth_1
reset_target all <bd>
generate_target all <bd>
export_ip_user_files
create_ip_run <bd>
reset_run synth_1
reset_run impl_1
```

### 第 4 次结果

综合、布局布线、bitstream 和 XSA 均成功；但随后的 XSA 内容审计发现 PS DDR 未启用，所以不能将这次结果判定为最终阶段 C 产物。

---

## 017 - 首版 XSA 内容审计与当时的 DDR 状态误判

### 目的

不只检查 Vivado 的 `PASS` 和地址映射，而是检查 XSA 中传给 Vitis 的真实 PS 元数据。

### 操作

列出 XSA 内容并读取：

```text
lm_head_system.hwh
psu_init.c
```

搜索：

```text
PSU__USE__DDR_INTF_REQUESTED
PSU__DDRC__ENABLE
```

### 发现

首次成功构建的 XSA 中：

```text
PSU__USE__DDR_INTF_REQUESTED = 0
```

当时将这个字段解释为“PS DDR 控制器本身没有启用”，因此暂停使用该
bitstream/XSA。后来在 022 中拿同事完整工程复核后证明，这个结论不准确：
同事工程也是 `PSU__USE__DDR_INTF_REQUESTED=0`，但
`PSU__DDRC__ENABLE=1` 且包含完整 DDR 初始化。

### 根因

当时只依据一个 GUI/request bookkeeping 字段下结论，没有同时检查
`PSU__DDRC__ENABLE` 和 `psu_ddr_init_data()`。`assign_bd_address` 只证明
AXI 地址可达关系，这一点仍然成立；但 `USE__DDR_INTF_REQUESTED` 也不能单独
证明 DDR 开关状态。

### 处理原则

先撤销“阶段 C 已完成”的判断，构建 DDR4-2400 暂定版；取得同事工程后，再
以同事的完整 1111 项 PS 参数和 DDR 初始化代码作最终依据。该误判及更正完整
保留，避免以后重复把 `USE__DDR_INTF_REQUESTED` 当成唯一 DDR 状态位。

---

## 018 - 补齐 4 GB DDR 暂定配置并重建 BD

### 依据

Vivado 2021.1 内置相近预设：

```text
D:\install\Xilinx\Vivado\2021.1\data\ip\xilinx\zynq_ultra_ps_e_v3_3\
subpreset\SUBPRESET1\DDR4_MICRON_MT40A256M16GE_083E.tcl
```

该预设是 4 Gbit/片、x16；AXU9EGB 手册描述的是 8 Gbit/片、x16、四颗、总容量 4 GB。

### 修复

保留内置预设的 DDR4-2400、64-bit、x16、训练和时序参数，调整：

```text
PSU__USE__DDR_INTF_REQUESTED = 1
PSU__DDRC__ENABLE            = 1
PSU__DDRC__DEVICE_CAPACITY   = 8192 MBits
PSU__DDRC__ROW_ADDR_COUNT    = 16
```

### 第 5 次建图命令

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch -nojournal `
  -log D:\program\LLM_FPGA\realFpga\results\20260724_stage_c\create_bd_attempt5.log `
  -source realFpga\vivado\create_lm_head_axu9eg_bd.tcl
```

### 结果

```text
退出码：0
LMH_STAGE_C_CREATE=PASS
DDR_REQUESTED=1
DDR_ENABLE=1
DDR_BUS_WIDTH=64 Bit
DDR_DRAM_WIDTH=16 Bits
DDR_DEVICE_CAPACITY=8192 MBits
DDR_ROW_ADDR_COUNT=16
DDR_FREQ_MHZ=1200
DDR_PRESET_STATUS=PROVISIONAL_MT40A512M16_4GB
```

### 风险记录

该配置足以生成描述真实 DDR 控制器的 XSA，但仓库仍没有厂商板级走线延迟/完整 preset。真实下载前必须取得同事或 ALINX 的已验证 PS 配置，或把独立 DDR 压测作为第一项上板测试。

---

## 019 - 第 5 次综合、实现、bitstream 和 XSA

### 命令

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch -nojournal `
  -log D:\program\LLM_FPGA\realFpga\results\20260724_stage_c\build_bitstream_attempt5.log `
  -source realFpga\vivado\build_lm_head_axu9eg.tcl
```

### 时间

```text
综合启动：2026-07-24 18:52:21
综合完成：2026-07-24 18:56:49
实现启动：2026-07-24 18:57:42
bitstream 完成：2026-07-24 19:03:44
XSA 完成并退出：2026-07-24 19:04:19
```

### 结果

```text
退出码：0
LMH_STAGE_C_SYNTH_STATUS=synth_design Complete!
LMH_STAGE_C_IMPL_STATUS=write_bitstream Complete!
LMH_STAGE_C_BUILD=PASS
LMH_STAGE_C_WORST_SLACK_NS=4.102
```

布线结果：

```text
可布线网络：21451
完全布线：21451
路由错误：0
```

时序结果：

```text
WNS = +4.102 ns
WHS = +0.012 ns
TNS = 0
THS = 0
所有用户时序约束满足
```

### DRC

```text
Errors = 0
Warnings = 15
Advisories = 5
```

15 条 warning 是 HLS 浮点 DSP 的 `AVAL-318`、`DPIP-2`、`DPOP-3`、`DPOP-4`、`DPREG-7`。它们没有阻止 bitstream 且 100 MHz 时序通过；其中 AVAL-318/DPREG-7 仍需在首次真实板 trace 中做数值验证，不能只按性能告警处理。

---

## 020 - DDR4-2400 暂定版 XSA、时序、布线、DRC 和摘要核验

> 后续状态：该版本已由 021～025 的同事参考工程校准版取代。以下内容作为
> 历史调试轨迹保留，不再代表最终交付产物。

### 操作

```powershell
tar -tf realFpga\results\20260724_stage_c\lm_head_axu9eg.xsa
Get-FileHash -Algorithm SHA256 <bitstream/XSA/XPR/BD>
```

读取 XSA 中的 `lm_head_system.hwh` 和 `psu_init.c`，搜索 DDR、LM Head 控制地址和 DDR 初始化序列；读取 post-route utilization/timing/DRC 和 route-status 报告。

首次组合哈希查询曾因直接把 `foreach` 结果接到管道而产生 PowerShell parser error，命令在语法解析阶段失败、没有副作用。修复为先生成数组/逐项格式化后重新查询。

### XSA 内容结果

```text
PSU__USE__DDR_INTF_REQUESTED = 1
PSU__DDRC__ENABLE            = 1
PSU__DDRC__BUS_WIDTH         = 64 Bit
PSU__DDRC__DRAM_WIDTH        = 16 Bits
PSU__DDRC__DEVICE_CAPACITY   = 8192 MBits
PSU__DDRC__ROW_ADDR_COUNT    = 16
PSU__CRF_APB__DDR_CTRL__FREQMHZ = 1200
C_S_AXI_CONTROL_BASEADDR     = 0xA0000000
```

`psu_init.c` 已包含 DDR 控制器和 DDR PHY 初始化序列，不再是 DDR disabled 平台。

### 资源

```text
CLB LUT：10441 / 274080 = 3.81%
CLB Register：15603 / 548160 = 2.85%
Block RAM Tile：6 / 912 = 0.66%
DSP：5 / 2520 = 0.20%
```

### 最终产物摘要

```text
52EB3F91905820FE12B2F166A313DA7CF21DEEB2732F8A847703DFD6C9F9119A
realFpga/vivado/build/lm_head_axu9eg/lm_head_axu9eg.runs/impl_1/lm_head_system_wrapper.bit

1307B0CAC90E477EE7DABEC9E58CFEC55FAD865D6981909DCFF36E9A1F4BEC1C
realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa
```

详细报告：

```text
realFpga/results/20260724_stage_c/README.md
```

### 当时的阶段 C 判定（后续已由 025 更新）

```text
Block Design：PASS
综合：PASS
实现：PASS
布线：PASS
100 MHz 时序：PASS
bitstream：PASS
XSA 内容：PASS
PS DDR 元数据：已启用
真实板 DDR 训练/稳定性：尚未验证
阶段 C 离线构建：完成
```

在用户下达下一阶段命令前暂停，不下载 bitstream、不建立 Vitis 应用、不向板卡发送数据。

---

## 021 - 清点同事完整 AXU9EGB Vivado 工程

> 补充时间：2026-07-24  
> 记录人：zb

### 输入

```text
D:\program\LLM_FPGA\ref\rmsnorm_axu9eg
```

### 命令和操作

```powershell
rg --files D:\program\LLM_FPGA\ref\rmsnorm_axu9eg
Get-ChildItem -LiteralPath D:\program\LLM_FPGA\ref\rmsnorm_axu9eg
tar -tf ref\rmsnorm_axu9eg\system_wrapper_wrapper.xsa
Get-FileHash -Algorithm SHA256 <XSA/XPR/BD/bitstream>
```

### 结果

目录共 1012 个文件，包含完整而非裁剪过的工程：

```text
rmsnorm_axu9eg.xpr
rmsnorm_axu9eg.srcs/sources_1/bd/system_wrapper/system_wrapper.bd
rmsnorm_axu9eg.gen/.../hw_handoff/system_wrapper.hwh
rmsnorm_axu9eg.gen/.../hw_handoff/system_wrapper_bd.tcl
rmsnorm_axu9eg.runs/impl_1/system_wrapper_wrapper.bit
system_wrapper_wrapper.xsa
psu_init.c/.h/.tcl
```

工程和本项目使用相同工具及器件：

```text
Vivado v2021.1
xczu9eg-ffvb1156-2-i
```

参考工程实现日志：

```text
route_design completed successfully
write_bitstream completed successfully
WNS = +2.815 ns
WHS = +0.002 ns
All user specified timing constraints are met.
```

参考文件 SHA-256：

```text
80AD784D99824820AD7688C4557CABE01C54BE34A92FD249A7A2A14CA0FA872A  system_wrapper_wrapper.xsa
BDAC7FBE27B8A503070839748CD23D0444E6FEF75FC83DA92394F1AF882A8886  rmsnorm_axu9eg.xpr
79E137AEBB528C50B370431B4C465544E082FE3594B65985DB5232E474E33334  system_wrapper.bd
DDB1CBA0510A9B7ED07E61C5AAC41468E1EB277AC52CCD9D35FE2C1BE39F765C  system_wrapper_wrapper.bit
```

本步骤只读参考工程，没有打开、保存或修改同事的 `.xpr/.bd`。

---

## 022 - 1111 项 PS 参数对比及 DDR 判断更正

### 方法

分别从以下 XSA 的 HWH 中解析所有 `PSU__*` 参数：

```text
ref/rmsnorm_axu9eg/system_wrapper_wrapper.xsa::system_wrapper.hwh
realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa::lm_head_system.hwh
```

使用正则：

```text
<PARAMETER NAME="(PSU__...)" VALUE="..."/>
```

合并参数名后逐项比较 Reference 和 Ours。

### 首次比较结果

```text
参考参数数：1111
本项目参数数：1111
不同参数数：24
```

器件、容量、总线、MIO 和 AXI 已一致：

```text
DDRC ENABLE：1 / 1
总容量：8192 MBits / 8192 MBits
总线：64 Bit / 64 Bit
颗粒宽度：16 Bits / 16 Bits
行地址：16 / 16
PS 参考时钟：33.333 / 33.333 MHz
PL0 实际时钟：99.999001 / 99.999001 MHz
GEM3：MIO 64..75 / MIO 64..75
MDIO：MIO 76..77 / MIO 76..77
UART0：MIO 42..43 / MIO 42..43
M_AXI_HPM0_FPD、S_AXI_HP0_FPD：一致
```

主要差异：

```text
参考 DDR speed bin：DDR4_1600J
暂定版：DDR4_2400P

参考 DDR requested frequency：800 MHz
暂定版：1200 MHz

参考 CL/CWL：10/9
暂定版：16/12

参考 PL0 source/divisor：DPLL/4
暂定版：IOPLL/10（生成后的实际属性）

参考 TTC0：Enabled
暂定版：Disabled
```

### 关键更正

参考工程：

```text
PSU__USE__DDR_INTF_REQUESTED = 0
PSU__DDRC__ENABLE            = 1
psu_ddr_init_data()          = 存在
DDR 控制器/PHY 匹配行数      = 2040
```

因此 017 中把 `USE__DDR_INTF_REQUESTED=0` 单独解释为“DDR 控制器未启用”是
错误的。该字段是 Vivado 的请求/GUI bookkeeping 属性；实际判断必须组合：

```text
PSU__DDRC__ENABLE
DDR 容量、时序和地址范围
psu_ddr_init_data()
真实板 DDR 读写
```

---

## 023 - 对齐参考工程并重建 Block Design

### 旧版归档

在覆盖最终 XSA 前保留 DDR4-2400 暂定版：

```powershell
Copy-Item `
  realFpga\results\20260724_stage_c\lm_head_axu9eg.xsa `
  realFpga\results\20260724_stage_c\lm_head_axu9eg_attempt5_provisional_ddr2400.xsa
```

归档 SHA-256：

```text
1307B0CAC90E477EE7DABEC9E58CFEC55FAD865D6981909DCFF36E9A1F4BEC1C
```

### 修改

在 `realFpga/vivado/create_lm_head_axu9eg_bd.tcl` 中按参考工程设置：

```text
DDR speed bin：DDR4_1600J
DDR requested frequency：800 MHz
CL/CWL：10/9
tRCD/tRP：10/10
tRC/tRAS/tFAW：47.5/35/35
DDR4 address mapping：1
PL0 clock source/divisor：DPLL/4
TTC0：Enabled
USE__RST0：0
USE__DDR_INTF_REQUESTED：0
DDRC__ENABLE：1
```

### 第 6 次建图

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch -nojournal `
  -log realFpga\results\20260724_stage_c\create_bd_attempt6_reference_aligned.log `
  -source realFpga\vivado\create_lm_head_axu9eg_bd.tcl
```

结果：

```text
退出码：0
LMH_STAGE_C_CREATE=PASS
DDR_ENABLE=1
DDR_FREQ_MHZ=800
DDR_SPEED_BIN=DDR4_1600J
DDR_PRESET_STATUS=REFERENCE_ALIGNED_RMSNORM_AXU9EGB
```

第一次对齐后只剩一个差异：

```text
PSU__CRL_APB__UART1_REF_CTRL__ACT_FREQMHZ
Reference = 99.999001
Ours      = 100
```

UART1 已在两边禁用。仍显式加入参考工程的 UART1 divider 15/1，并执行第 7 次
建图：

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch -nojournal `
  -log realFpga\results\20260724_stage_c\create_bd_attempt7_reference_exact.log `
  -source realFpga\vivado\create_lm_head_axu9eg_bd.tcl
```

Vivado 仍将本项目已禁用 UART1 的派生值显示为 `100`，但所有 UART1 source/
divider 配置值相同。该差异不影响 UART0、GEM、DDR、PL 时钟或 LM Head。

### 对比脚本的小问题

当差异仅剩一个对象时，PowerShell 将结果折叠为标量，直接输出
`$diffs.Count` 得到空值。修复为：

```powershell
$diffs = @(foreach (...) { ... })
```

修复后正确输出：

```text
POST_ALIGNMENT_DIFFERENCES=1
```

---

## 024 - 参考对齐版综合、实现、bitstream 和 XSA

### 命令

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch -nojournal `
  -log realFpga\results\20260724_stage_c\build_bitstream_attempt6_reference_aligned.log `
  -source realFpga\vivado\build_lm_head_axu9eg.tcl
```

Vivado run manager 需要启动综合/实现子进程，因此使用此前已批准的 Vivado
工作区外层执行权限；目标文件仍全部位于本项目目录。

### 时间和结果

```text
综合启动：2026-07-24 21:42:18
综合完成：2026-07-24 21:46:00
实现启动：2026-07-24 21:46:53
bitstream 完成：2026-07-24 21:50:54
XSA 完成并退出：2026-07-24 21:51:27
退出码：0
```

```text
LMH_STAGE_C_SYNTH_STATUS=synth_design Complete!
LMH_STAGE_C_IMPL_STATUS=write_bitstream Complete!
LMH_STAGE_C_BUILD=PASS
LMH_STAGE_C_WORST_SLACK_NS=4.262
```

时序：

```text
WNS = +4.262 ns
WHS = +0.010 ns
TNS = 0
THS = 0
All user specified timing constraints are met.
```

布线：

```text
可布线网络：21455
完全布线：21455
路由错误：0
```

DRC：

```text
Errors = 0
Warnings = 15
Advisories = 5
```

warning 类型仍为 HLS 浮点 DSP 的 AVAL-318、DPIP-2、DPOP-3、DPOP-4 和
DPREG-7，与 DDR/PS 校准无关。

---

## 025 - DDR 初始化精确比对与最终基线验收

### XSA 参数复核

从最终 XSA 重新提取全部 PS 参数：

```text
参考 XSA：1111 项
本项目 XSA：1111 项
差异：1 项
```

唯一差异：

```text
PSU__CRL_APB__UART1_REF_CTRL__ACT_FREQMHZ
Reference = 99.999001
Ours      = 100
```

UART1 在两份设计中均为 Disabled；其配置 source/divider 一致，因此归类为
禁用外设的派生显示差异，功能相关 PS 参数差异为 0。

### DDR 初始化代码复核

分别从两份 XSA 的 `psu_init.c` 提取：

```c
unsigned long psu_ddr_init_data(void)
```

直到 `psu_peripherals_init_data()` 前的完整函数体，逐字符比较：

```text
参考长度：523694
本项目长度：523694
DDR_INIT_EXACT_MATCH=True
```

这比只比较 DDR 的几个 GUI 字段更严格：最终用于初始化 DDRC 和 DDR PHY 的
寄存器写入序列与同事工程完全一致。

### 最终资源

```text
CLB LUT：10428 / 274080 = 3.80%
CLB Register：15603 / 548160 = 2.85%
Block RAM Tile：6 / 912 = 0.66%
DSP：5 / 2520 = 0.20%
```

### 最终产物

```text
723F56E9AF239B6DE20EFCB542F3E72A5BA0789D437F0344311568E3D4BA939E
realFpga/vivado/build/lm_head_axu9eg/lm_head_axu9eg.runs/impl_1/lm_head_system_wrapper.bit

B72DD60AFD2FCB7355F59F638A393A07250F0B6A878E300720D1AEEA36AB652C
realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa
```

### 阶段 C 最终判定

```text
同事参考工程完整性：PASS
PS 功能相关配置对齐：PASS
DDR 初始化逐字节对齐：PASS
Block Design：PASS
综合：PASS
实现：PASS
布线：PASS
100 MHz 时序：PASS
bitstream：PASS
XSA：PASS
本开发板真实 DDR 读写：待阶段 D
阶段 C 最终板级基线：完成
```

本步骤结束后暂停，没有连接 Vivado Hardware Manager、没有下载 bitstream、
没有修改同事工程，也没有向 `192.168.8.190` 发送数据。

---

## 后续日志规则

从本条开始，每次执行命令后立即追加：

1. 操作目的；
2. 完整命令或 GUI 路径；
3. 输入和目标文件；
4. 退出码及关键输出；
5. 遇到的问题；
6. 原因判断依据；
7. 实际修复；
8. 修复后的复测结果；
9. 是否满足当前阶段验收条件。

---

## 026 - 断电后网络现状与 PHY 补丁审计

记录时间：2026-07-24  
记录人：zb

### 操作目的

确认 `192.168.8.190` 失联的直接现象，定位同事提供的
`xemacpsif_physpeed.c` 与 Xilinx Vitis 2021.1 原版的差异。

### 执行命令

```powershell
ping -n 4 192.168.8.190
arp -a 192.168.8.190
Get-FileHash -Algorithm SHA256 D:\program\LLM_FPGA\ref\xemacpsif_physpeed.c
Get-FileHash -Algorithm SHA256 D:\install\Xilinx\Vitis\2021.1\data\embeddedsw\ThirdParty\sw_services\lwip211_v1_5\src\contrib\ports\xilinx\netif\xemacpsif_physpeed.c
git diff --no-index <Vitis原文件> <同事提供文件>
```

### 结果

```text
ping：4/4 超时
ARP：No ARP Entries Found
同事文件 SHA256：
4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
Vitis 2021.1 原文件 SHA256：
26A9497C5AF0AAF1FF037C40A135BAC87444B9A65253169A4AF313F9B45B2600
差异：80 insertions, 1 deletion
```

补丁新增 `get_Generic_phy_speed()`，对未知 PHY 读取标准寄存器 2、3、5、10，
等待链路和自协商，并推导 1000/100/10 Mbps。原版代码把所有未识别 PHY
都错误地转入 Marvell 专用分支；补丁仅让明确识别为 Marvell 的 PHY 进入该分支，
其余进入通用分支。

### 判断

断电后 ping 不通不能单独证明 lwIP 失败，因为通过 JTAG 下载的 bitstream 和 ELF
均为易失内容，断电后必然丢失。但补丁针对未知 PHY 的处理逻辑确实合理，应应用于
本项目生成的 BSP，而不应修改 Xilinx 全局安装目录。

---

## 027 - XSCT 命令探测与失败返回机制

记录时间：2026-07-24  
记录人：zb

### 操作

创建并执行：

```text
realFpga/vitis/xsct_probe.tcl
```

执行命令：

```powershell
& D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat D:\program\LLM_FPGA\realFpga\vitis\xsct_probe.tcl
```

### 遇到的问题

首次使用 `version -short`，XSCT 2021.1 报错：

```text
bad option '-short': -help -server
```

### 修复

改为调用无参数 `version`，并在后续 Tcl 脚本中统一使用 `catch` 捕获内部错误，
打印 `STAGE_D_ERROR` 后显式 `exit 1`，避免工具内部失败而外层批处理仍返回 0。

---

## 028 - 从最终 XSA 创建 Vitis 平台

记录时间：2026-07-24  
记录人：zb

### 输入

```text
D:\program\LLM_FPGA\realFpga\results\20260724_stage_c\lm_head_axu9eg.xsa
```

### 脚本与命令

```text
D:\program\LLM_FPGA\realFpga\vitis\create_platform.tcl
```

```powershell
& D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat D:\program\LLM_FPGA\realFpga\vitis\create_platform.tcl
```

### 关键配置

```text
workspace = D:/program/LLM_FPGA/realFpga/vitis/workspace
platform  = lm_head_axu9eg_platform
processor = psu_cortexa53_0
os        = standalone
domain    = standalone_domain
```

### 结果

```text
FSBL：生成并编译成功
PMUFW：生成并编译成功
standalone BSP：生成并编译成功
自定义驱动 lm_head_argmax_v1_0：进入 BSP
脚本标记：STAGE_D_PLATFORM_PASS
退出码：0
```

编译器输出中的 unused parameter、unused label 和 deprecated API 为 Xilinx
自带库警告，不是构建失败。

---

## 029 - 启用 lwIP211 并创建网络诊断程序

记录时间：2026-07-24  
记录人：zb

### 脚本与命令

```text
D:\program\LLM_FPGA\realFpga\vitis\create_net_diag_app.tcl
```

```powershell
& D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat D:\program\LLM_FPGA\realFpga\vitis\create_net_diag_app.tcl
```

### 第一次失败

直接创建 `lwIP Echo Server`，内部错误：

```text
This application requires lwIP library in the Board Support Package.
```

修复：先执行：

```tcl
bsp setlib -name lwip211
bsp write
bsp regenerate
```

### 第二次失败

BSP 的 `system.mss` 和 `platform.spr` 已包含 `lwip211:1.5`，但创建模板仍提示
没有 lwIP。原因是平台导出的 XPFM/Domain 尚未刷新，Vitis IDE 读取的是旧导出内容。

修复：增加：

```tcl
platform write
platform generate -domains standalone_domain
```

### 复测结果

```text
应用：lm_head_net_diag
模板：lwIP Echo Server
BSP library：lwip211 1.5
脚本标记：STAGE_D_NET_APP_CREATE_PASS
退出码：0
```

---

## 030 - 将同事的 PHY 修复精确应用到项目 BSP

记录时间：2026-07-24  
记录人：zb

### 源文件

```text
D:\program\LLM_FPGA\ref\xemacpsif_physpeed.c
```

### 目标文件

```text
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_axu9eg_platform\psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0\libsrc\lwip211_v1_5\src\contrib\ports\xilinx\netif\xemacpsif_physpeed.c
```

使用补丁方式修改项目 BSP 文件，没有修改
`D:\install\Xilinx\Vitis\2021.1` 下的全局安装文件。

### 校验

```text
源文件 SHA256：
4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
目标文件 SHA256：
4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
逐字节一致：PASS
```

---

## 031 - 网络诊断应用配置与 DDR 冒烟测试

记录时间：2026-07-24  
记录人：zb

### 修改文件

```text
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\src\main.c
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\src\echo.c
```

### 配置

```text
板卡 IP：192.168.8.190
掩码：255.255.255.0
网关：192.168.8.1
MAC：00:0a:35:00:01:02
TCP 回显端口：7
lwIP API：RAW API
DHCP：关闭
链路速度：自动检测
```

在 `main.c` 中增加 64 KiB DDR 冒烟测试：

```text
地址：0x10000000
长度：4096 个 u32，即 65536 字节
模式：0xA5A50000 XOR index
流程：写入 -> cache flush -> cache invalidate -> 逐字比较
```

如果 DDR 比较失败，程序在网络初始化前直接停止。因此后续网络成功可作为
“DDR 冒烟测试已经通过”的间接且严格的程序路径证据。

主机网卡通过 `ipconfig` 确认为：

```text
IPv4：192.168.8.12
掩码：255.255.255.0
```

曾尝试 `Get-NetIPConfiguration`，因当前进程无 CIM 查询权限而报“拒绝访问”，
随后使用只读的 `ipconfig` 成功取得相同所需信息。

---

## 032 - 识别 Vitis 应用构建假成功并改用 Makefile

记录时间：2026-07-24  
记录人：zb

### 初始命令

```powershell
& D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat D:\program\LLM_FPGA\realFpga\vitis\build_net_diag.tcl
```

XSCT 输出：

```text
PHY_PATCH_MARKER=PASS
STAGE_D_NET_APP_BUILD_PASS
退出码：0
```

### 问题

验收时发现 `Debug` 目录没有 `lm_head_net_diag.elf`。Vitis 的 `IDE.log` 中记录：

```text
In XSCT Case We should not reach here.
xsct server communication channel has closed unexpectedly.
```

说明 `app build` 的后台构建没有真正执行，Tcl 返回不代表 ELF 已生成。

### 修复命令

```powershell
cmd.exe /d /s /c ""D:\install\Xilinx\Vitis\2021.1\settings64.bat" && make -C "D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\Debug" all"
```

### 复测结果

```text
make 退出码：0
text：121303 bytes
data：7424 bytes
bss：6443317 bytes
ELF：
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\Debug\lm_head_net_diag.elf
ELF 大小：1028096 bytes
构建：PASS
```

后续应用构建的验收条件改为同时满足：编译退出码为 0、ELF 存在且大小非零。

---

## 033 - JTAG 枚举

记录时间：2026-07-24  
记录人：zb

### 脚本与命令

```text
D:\program\LLM_FPGA\realFpga\vitis\probe_jtag.tcl
```

```powershell
& D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat D:\program\LLM_FPGA\realFpga\vitis\probe_jtag.tcl
```

### 结果

```text
PS TAP：发现
PMU：发现
PL：发现
PSU：发现
APU：发现
Cortex-A53 #0..#3：发现
RPU/Cortex-R5 #0..#1：发现
脚本标记：STAGE_D_JTAG_PROBE_PASS
退出码：0
```

Windows 未枚举出可用 COM 口，因此本轮不能直接保存 UART 文本日志；
改用程序控制流和网络结果完成 DDR/网络验收。后续连接 USB-UART 后应补充串口日志。

---

## 034 - 下载 bitstream 与网络诊断 ELF

记录时间：2026-07-24  
记录人：zb

### 输入

```text
bit：
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_axu9eg_platform\export\lm_head_axu9eg_platform\hw\lm_head_axu9eg.bit

PS 初始化：
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_axu9eg_platform\export\lm_head_axu9eg_platform\hw\psu_init.tcl

ELF：
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\Debug\lm_head_net_diag.elf
```

### 脚本与命令

```text
D:\program\LLM_FPGA\realFpga\vitis\program_net_diag.tcl
```

```powershell
& D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat D:\program\LLM_FPGA\realFpga\vitis\program_net_diag.tcl
```

### 实际顺序

```text
连接 hw_server
系统复位
下载 bitstream
复位 Cortex-A53 #0
执行 psu_init
解除 PS-PL isolation
配置 PS-PL reset
下载 ELF
启动 Cortex-A53 #0
```

### 结果

```text
FPGA_PROGRAM_END
PS_INITIALIZATION_END
APPLICATION_DOWNLOAD_END
Cortex-A53 #0：Running
脚本标记：STAGE_D_BOARD_PROGRAM_PASS
退出码：0
```

工具输出过一次“复位后建议在 reset vector 写 bootloop”的通用警告；
本脚本随后显式复位 A53、完成 PS 初始化并下载 ELF，A53 最终为 Running，
未形成阻断。

---

## 035 - 上板网络与 DDR 路径验收

记录时间：2026-07-24  
记录人：zb

### Ping 与 ARP

```powershell
ping -n 8 -w 1000 192.168.8.190
arp -a 192.168.8.190
```

结果：

```text
发送：8
接收：8
丢失：0
丢包率：0%
最小/最大 RTT：0/1 ms
ARP：192.168.8.190 -> 00-0a-35-00-01-02
```

### TCP 回显

首次在受限执行环境内使用 `Test-NetConnection` 和 `.NET TcpClient`，
套接字创建被本机权限策略拒绝，错误为：

```text
以一种访问权限不允许的方式做了一个访问套接字的尝试
```

该错误发生在主机权限层，不是板卡拒绝连接。获得网络访问授权后执行：

```powershell
$client.Connect('192.168.8.190', 7)
发送 ASCII：LM_HEAD_ECHO_TEST
读取板卡回显
```

结果：

```text
TCP_CONNECTED=True
TCP_SENT=LM_HEAD_ECHO_TEST
TCP_REPLY=LM_HEAD_ECHO_TEST
TCP_ECHO_MATCH=True
```

### 当前结论

```text
DDR 64 KiB 写入/回读路径：PASS
PHY 通用识别补丁进入 BSP：PASS
以太网链路与自协商：PASS（可稳定收发）
静态 IP：PASS
ICMP ping：PASS
TCP 建连：PASS
TCP 双向载荷回显：PASS
```

DDR 的判定依据是：程序只有在 DDR 冒烟测试逐字比较通过后才初始化 lwIP；
当前 ping 和 TCP 均成功，因此程序必然已经执行并通过 DDR 测试。由于本轮没有
可用串口，尚未取得 PHY ID、协商速率和 `DDR smoke test PASS` 的直接 UART 文本，
这部分在连接 USB-UART 后补录。

---

## 036 - 阶段 E 基线内存审计

记录时间：2026-07-24  
记录人：zb

### 操作目的

在放置约 260 MiB 权重之前，确认当前 standalone 应用、lwIP、堆、栈和
PS DDR 的真实地址范围，避免使用未经证明的固定地址。

### 检查对象

```text
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\src\lscript.ld
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\Debug\lm_head_net_diag.elf
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_axu9eg_platform\psu_cortexa53_0\standalone_domain\bsp\psu_cortexa53_0\include\xparameters.h
```

### 执行命令

```powershell
Get-Content ...\src\lscript.ld -Tail 180
cmd.exe /d /s /c ""D:\install\Xilinx\Vitis\2021.1\settings64.bat" && aarch64-none-elf-size -A "...Debug\lm_head_net_diag.elf""
rg -n "DDR.*BASEADDR|DDR.*HIGHADDR" ...\xparameters.h
```

### 基线结果

```text
低地址 PS DDR：
  ORIGIN = 0x00000000
  LENGTH = 0x7FF00000
  可用末端（开区间）= 0x7FF00000

应用主要占用：
  .text/.data 等结束约为 0x00021080
  .bss = 6,357,184 bytes，起始 0x00200000
  heap 起始 = 0x008100C0，大小 0xA000
  stack 起始 = 0x0081A0C0，大小 0xB000
  runtime_end = 0x008250C0

原 ELF 文件大小：
  1,028,096 bytes
```

当前运行时末端约为 8.15 MiB。LM Head 缓冲区最终选择从
`0x40000000`（1 GiB）开始，和当前程序之间保留了非常大的安全距离，
同时完整位于低地址 2 GiB DDR region 内。

### 遇到的小问题

计算各缓冲区总字节数时，PowerShell 对 `Measure-Object` 返回类型使用
`{0:X}` 格式化报“格式说明符无效”。该错误只影响辅助显示，没有修改文件。
修复为显式使用 64-bit 整数并调用 `.ToString("X")`，得到：

```text
未计对齐填充的缓冲区总和 = 273,642,544 bytes = 0x104F7430
```

---

## 037 - 实现 LM Head PS DDR NOLOAD 布局

记录时间：2026-07-24  
记录人：zb

### 修改文件

```text
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\src\lscript.ld
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\src\lmh_buffers.h
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\src\main.c
D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\Debug\makefile
```

### 链接器设计

新增：

```ld
.lmh_buffers 0x40000000 (NOLOAD)
```

其中依次放置：

```text
weight      272,269,312 B
hidden            1,792 B
history          18,992 B
alignment padding    16 B
raw logits      303,872 B
network RX    1,048,576 B
```

所有缓冲区起始地址执行 64 字节对齐。新增两个链接器断言：

```text
runtime_end <= lmh_buffers_start
lmh_buffers_end <= ORIGIN(psu_ddr_0_MEM_0) + LENGTH(psu_ddr_0_MEM_0)
```

### 地址接口

新增 `lmh_buffers.h`，统一定义：

```text
LMH_HIDDEN_SIZE      = 896
LMH_VOCAB_SIZE       = 151936
LMH_HISTORY_WORDS    = 4748
LMH_WEIGHT_ADDR
LMH_HIDDEN_ADDR
LMH_HISTORY_ADDR
LMH_LOGITS_ADDR
LMH_NETWORK_RX_ADDR
```

这些地址来自 linker symbol，不在 C 文件里再次硬编码。

在 `main.c` 增加启动时布局检查：

1. 核对每个区域的实际字节数；
2. 核对所有首地址为 64 字节对齐；
3. 失败时在 lwIP 初始化之前停止；
4. 成功时通过 UART 输出每个地址范围。

Makefile 链接参数增加：

```text
-Wl,-Map=lm_head_net_diag.map
-Wl,--cref
```

用于每次构建生成可审计的链接器 map。

---

## 038 - 阶段 E 重建与 ELF/Map 验证

记录时间：2026-07-24  
记录人：zb

### 构建命令

```powershell
cmd.exe /d /s /c ""D:\install\Xilinx\Vitis\2021.1\settings64.bat" && make -C "D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\Debug" all"
```

### 构建结果

```text
编译退出码：0
链接退出码：0
text：122303 bytes
data：7424 bytes
bss：280085901 bytes
```

`size` 显示约 280 MB bss 是预期结果：它统计了 `NOLOAD` 的虚拟地址空间，
不代表 ELF 文件包含约 280 MB 零数据。

### ELF 结构检查

执行：

```powershell
aarch64-none-elf-readelf -S -l lm_head_net_diag.elf
```

关键结果：

```text
.lmh_buffers Type = NOBITS
.lmh_buffers Address = 0x40000000
.lmh_buffers Size = 0x104F7440

对应 LOAD segment：
FileSiz = 0
MemSiz  = 0x104F7440
```

因此大缓冲区没有存入 ELF 文件，也没有需要通过 JTAG 下载的 273 MB 文件内容。

### 最终 Map 地址

```text
runtime_end = 0x008250C0

weight      0x40000000 - 0x503A8000  272269312 B
hidden      0x503A8000 - 0x503A8700       1792 B
history     0x503A8700 - 0x503AD130      18992 B
logits      0x503AD140 - 0x503F7440     303872 B
network_rx  0x503F7440 - 0x504F7440    1048576 B

buffers_end = 0x504F7440
DDR limit   = 0x7FF00000
```

`history` 结束到 `logits` 起始之间有 16 字节对齐填充，属于预期，不是数据丢失。

### 自动验收脚本

新增：

```text
D:\program\LLM_FPGA\realFpga\vitis\verify_stage_e.ps1
```

执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\program\LLM_FPGA\realFpga\vitis\verify_stage_e.ps1
```

输出：

```text
alignment=PASS
sizes=PASS
overlap=PASS
noload=PASS
STAGE_E_VERIFY_PASS
```

产物：

```text
lm_head_net_diag.elf
大小：1,030,104 bytes
SHA256：
C79BFC9F1C375B8FBEF8584D5D3D72F80A3268D571F95EE28235BB75A67B6480

lm_head_net_diag.map
大小：553,566 bytes
SHA256：
D602DF96E2845481A40035E8411AF5F3CF04C91E8B9D27BFCEE4C448D62EB6EA
```

与阶段 E 修改前相比，ELF 只增加 2,008 字节，证明权重空间没有进入文件。

---

## 039 - 新 DDR 布局上板回归

记录时间：2026-07-24  
记录人：zb

### 下载命令

```powershell
Measure-Command {
    & D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat D:\program\LLM_FPGA\realFpga\vitis\program_net_diag.tcl
}
```

结果：

```text
总用时：31.8992206 秒
```

`Measure-Command` 捕获了 XSCT 的普通输出，只显示总时间；下载脚本仍按既定顺序
完成系统复位、bitstream、PS 初始化、ELF 下载和 A53 启动。随后通过网络验证
程序确实运行到 lwIP 主循环。

### 网络回归

```powershell
ping -n 8 -w 1000 192.168.8.190
arp -a 192.168.8.190
```

结果：

```text
Ping：8/8 成功
丢包率：0%
RTT：0-2 ms
ARP：192.168.8.190 -> 00-0a-35-00-01-02
```

程序在 `lmh_buffer_layout_check()` 和 DDR 冒烟测试通过后才进入 lwIP，
因此本次 ping 成功同时证明：

```text
运行时链接地址检查：PASS
64 字节对齐检查：PASS
DDR 冒烟测试：PASS
网络基线未回归：PASS
```

---

## 040 - 阶段 E 最终判定

记录时间：2026-07-24  
记录人：zb

```text
PS DDR 可用范围确认：PASS
程序/堆/栈边界确认：PASS
权重 NOLOAD：PASS
hidden/history/logits/RX 地址规划：PASS
所有起始地址 64 字节对齐：PASS
缓冲区尺寸：PASS
缓冲区无重叠：PASS
未超过 DDR 上限：PASS
ELF 大小正常：PASS
链接器 map 生成：PASS
自动验收脚本：PASS
重新下载后网络回归：PASS
阶段 E：完成
```

本阶段没有上传模型权重，没有启动 `lm_head_argmax` HLS IP，也没有执行
LM Head、repetition penalty 或 argmax。下一阶段为阶段 F：在当前 lwIP
应用中实现 LMH1 协议、权重分块接收、Cache 同步和 HLS IP 控制。

---

## 041 - 阶段 F 接口审计与 LMH1 服务端实现

记录时间：2026-07-24  
记录人：zb

### 审计对象

通过 `Get-Content`、`rg` 和生成驱动头文件核对：

```text
module16_lm_head_hls/NETWORK_PROTOCOL.md
module16_lm_head_hls/net/lmh_protocol.py
module16_lm_head_hls/net/cpu_client.py
module16_lm_head_hls/net/fpga_server_emulator.py
ref/RMS/Vitis_IDE/lwip_rmsnorm_raw_server.c
xlm_head_argmax.h
xlm_head_argmax_hw.h
xparameters.h
```

确认：

```text
LMH1 帧头：24 bytes，小端
LOAD_WEIGHT / RUN_TOKEN / PING：1 / 2 / 3
HLS IP device id：0
AXI-Lite base：0xA0000000
hidden/weight/history/logits：64-bit DDR 地址参数
repetition_penalty：驱动参数为 uint32 bits
selected_score：驱动返回 uint32 bits
```

### 新增服务端

文件：

```text
realFpga/vitis/workspace/lm_head_net_diag/src/lwip_lm_head_raw_server.c
```

删除原模板 `echo.c`，实现：

1. 可跨任意 TCP pbuf 边界接收 24 B 帧头和 payload；
2. 同一连接连续执行多个 LMH1 请求；
3. `PING` 返回当前权重 READY 状态；
4. `LOAD_WEIGHT` 一边接收、一边写 `0x40000000` 权重区；
5. 每帧使用与 Python `zlib.crc32` 兼容的 IEEE CRC32；
6. 每个正确权重分块执行 `Xil_DCacheFlushRange`；
7. `RUN_TOKEN` 检查 shape、payload、history 和 penalty；
8. Flush hidden/history，设置 HLS IP 寄存器，Start/IsDone 超时轮询；
9. 可选 logits 完成后 Invalidate，并通过 `tcp_sent` 分段发送；
10. 错误响应使用 opcode `0xffff`；
11. 连接断开后保留已完整上传的权重，未完成上传作废。

权重数据不先复制到 1 MiB RX 缓冲：主机默认分块为 4 MiB，而权重总量约
260 MiB，必须使用流式写 DDR。CRC32 查表在启动时生成，避免对 260 MiB
数据逐字节执行 8 次位循环。

`main.c` 同时改为：LMH1/HLS IP 初始化失败时不再静默进入网络主循环。

### 首次构建

```powershell
cmd.exe /d /s /c ""D:\install\Xilinx\Vitis\2021.1\settings64.bat" &&
make -C D:\program\LLM_FPGA\realFpga\vitis\workspace\lm_head_net_diag\Debug all"
```

结果：

```text
编译：PASS
链接：PASS
HLS driver undefined symbol：0
```

---

## 042 - lwIP 大数据参数配置及两次问题修复

记录时间：2026-07-24  
记录人：zb

### 参数探测

命令：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  D:\program\LLM_FPGA\realFpga\vitis\probe_lwip_params.tcl
```

模板初值：

```text
MEM_SIZE         131072
TCP_SND_BUF        8192
TCP_WND            2048
MEMP_NUM_TCP_SEG    256
PBUF_POOL_SIZE      256
```

这组值能做小回显，但会严重限制 260 MiB 权重上传和 303872 B logits 回传。

### 问题 1：`bsp config` 参数形式错误

第一次写成：

```tcl
bsp config mem_size 262144 -lib lwip211
```

XSCT 报错：

```text
Wrong # of args: should be "bsp config <param> <value>"
```

修复为：

```tcl
bsp config mem_size 262144
```

其他 lwIP 参数同样去掉 `-lib lwip211`。

### 问题 2：BSP regenerate 覆盖 PHY 补丁

执行 `bsp regenerate` 后哈希变为：

```text
目标文件：26A9497C5AF0AAF1FF037C40A135BAC87444B9A65253169A4AF313F9B45B2600
同事版本：4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
```

通过：

```powershell
git diff --no-index -- <BSP目标文件> D:\program\LLM_FPGA\ref\xemacpsif_physpeed.c
```

确认 regenerate 删除了 `get_Generic_phy_speed()` 及其 fallback 分支。重新应用
同事补丁后，两者 SHA256 恢复完全一致。

`configure_lmh_lwip.tcl` 已固化为：每次 `bsp regenerate` 后自动复制同事版本，
并检查 `get_Generic_phy_speed` 标记。

### 问题 3：lwIP TCP segment 编译期检查失败

首次把发送缓冲调到 32768 后，`platform generate` 失败：

```text
MEMP_NUM_TCP_SEG should be at least as big as TCP_SND_QUEUELEN
```

原因：

```text
TCP_SND_QUEUELEN = 16 * TCP_SND_BUF / TCP_MSS
                 ≈ 16 * 32768 / 1460
                 ≈ 359
```

模板 `MEMP_NUM_TCP_SEG=256` 不足。修复：

```tcl
bsp config memp_n_tcp_seg 512
```

最终参数：

```text
MEM_SIZE          262144
TCP_SND_BUF        32768
TCP_WND            32768
MEMP_NUM_TCP_SEG     512
PBUF_POOL_SIZE       256
```

命令：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  D:\program\LLM_FPGA\realFpga\vitis\configure_lmh_lwip.tcl

D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  D:\program\LLM_FPGA\realFpga\vitis\generate_stage_f_platform.tcl
```

结果：

```text
PHY_PATCH_RESTORED=PASS
STAGE_F_BSP_CONFIG_PASS
STAGE_F_PLATFORM_GENERATE_PASS
```

---

## 043 - Vitis app build 表面成功但 ELF 缺失

记录时间：2026-07-24  
记录人：zb

### 现象

执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  D:\program\LLM_FPGA\realFpga\vitis\build_net_diag.tcl
```

输出含：

```text
STAGE_D_NET_APP_BUILD_PASS
```

但随后 `verify_stage_f.ps1` 发现：

```text
Debug/lm_head_net_diag.elf 不存在
```

Vitis 在该次调用中重建了 managed Makefile、清理了旧 ELF，却没有产生新 ELF；
同时重新生成的 Makefile 丢失原先手工加入的 map 参数。

### 修复

1. 在 `.cproject` 的 Debug linker 中固化：

```text
-Wl,-Map=lm_head_net_diag.map -Wl,--cref
```

2. 在 `build_net_diag.tcl` 的 `app build` 后明确执行：

```tcl
exec make -C $app_debug_dir all
```

3. 脚本最后必须同时检查：

```text
lm_head_net_diag.elf 存在
lm_head_net_diag.map 存在
```

最终真实输出：

```text
APP_DIRECT_MAKE_END
APP_ELF_AND_MAP=PASS
```

这次问题再次说明：Vitis/XSCT 的表面 PASS 或退出码不能单独作为验收依据，
必须检查具体产物和独立验证标记。

---

## 044 - 阶段 F 第一次上板协议测试与错误响应修复

记录时间：2026-07-24  
记录人：zb

### 下载

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  D:\program\LLM_FPGA\realFpga\vitis\program_net_diag.tcl
```

结果：

```text
STAGE_D_BOARD_PROGRAM_PASS
Cortex-A53 #0 Running
ping 192.168.8.190：6/6，0% 丢包
```

### 测试环境问题

第一次直接执行 `python`：

```text
python 不是可识别的命令
```

修复为使用 Codex 工作区 Python：

```text
C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

沙箱内第一次连接局域网出现 `WinError 10013`，随后按权限流程允许该固定测试脚本
访问 `192.168.8.190:19016`。

### 第一次协议结果

```text
fragmented_header=PASS
run_before_weight_status=PASS
same_connection_multi_frame=PASS
crc_error_and_recovery=PASS
unknown_opcode：ConnectionResetError
```

原因：未知 opcode 的错误帧刚通过 `tcp_write` 排队，服务端就立即关闭 PCB，
客户端可能先收到 TCP reset 而不是错误帧。

修复：新增 `tx_acked`，由 `tcp_sent` 累计对端确认的字节数；只有错误响应的
header 和 payload 全部被确认后才关闭连接。

重新编译和下载后：

```text
fragmented_header=PASS
run_before_weight_status=PASS
same_connection_multi_frame=PASS
crc_error_and_recovery=PASS
unknown_opcode_error=PASS
STAGE_F_BOARD_SMOKE_PASS
```

---

## 045 - 阶段 F 最终验收

记录时间：2026-07-24  
记录人：zb

### 自动静态验收

命令：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File D:\program\LLM_FPGA\realFpga\vitis\verify_stage_f.ps1
```

结果：

```text
lmh1_source=PASS
streaming_weight_rx=PASS
segmented_tcp_tx=PASS
cache_sync_calls=PASS
hls_driver_symbols=PASS
undefined_symbols=0
lwip_mem_size=262144
lwip_tcp_snd_buf=32768
lwip_tcp_wnd=32768
lwip_memp_num_tcp_seg=512
phy_patch_sha256=4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
STAGE_F_VERIFY_PASS
```

### 最终产物

```text
lm_head_net_diag.elf
大小：1,103,160 bytes
SHA256：7F595FA201202241FCF773C1D012FBF6FC12A87BA80EE4AB712D1E2766E21358

lm_head_net_diag.map
大小：585,314 bytes
SHA256：5E18B1A3A482FADDE16ED2BD00F8A10ED2957CB5C3F03648C0DBD80C9002314E

lwip_lm_head_raw_server.c
SHA256：CB4040D999A683191F00950B49E6FBA5AF8392A997AED3F0E6711E4B93EE2EDA
```

### 最终上板回归

```text
Ping：4/4 成功，0% 丢包，RTT 0-1 ms
LMH1 board smoke：PASS
```

阶段 F 已完成：

```text
LMH1 PING：完成
流式 LOAD_WEIGHT 接收/CRC/DDR Flush：完成
RUN_TOKEN 解析与 HLS driver 控制：完成
repetition_penalty 参数通路：完成
可选 logits 分段回传：完成
多帧同连接状态机：完成
错误帧和 CRC 恢复：完成
静态链接/map/HLS symbol：完成
真实板卡协议冒烟：完成
```

本阶段没有上传真实 260 MiB 权重，也没有调用 `XLm_head_argmax_Start` 执行
完整 LM Head；`RUN_TOKEN` 在权重未 READY 时正确返回 `STATUS_NOT_READY`。
下一阶段为阶段 G：实现/整理直接读取
`qwen25_0p5b_instruct_full_generation_trace` fixture 的上位机脚本，并先对软件
模拟器完成 step 0 回归。

---

## 046 - 阶段 G-1 上位机程序实现与输入检查

记录时间：2026-07-24  
记录人：zb

### 本步目标

实现统一上位机入口：

```text
D:\program\LLM_FPGA\tools\run_module16_board_trace.py
```

该程序直接读取已经从
`qwen25_0p5b_instruct_full_generation_trace` 整理出的 fixture，不启动完整
Qwen 推理。程序既可以连接本机软件模拟器，也可以连接
`192.168.8.190:19016` 的真实板端 LMH1 服务。

### 检查操作

检查了以下现有代码和数据：

```text
module16_lm_head_hls/net/cpu_client.py
module16_lm_head_hls/net/fpga_server_emulator.py
module16_lm_head_hls/net/lmh_protocol.py
tools/run_module16_tcp_loopback.py
tools/prepare_lm_head_hls_fixture.py
artifacts/model.embed_tokens.weight.fp16.npy
artifacts/module16_hls_fixtures/step_00/*
qwen25_0p5b_instruct_full_generation_trace/metadata.json
qwen25_0p5b_instruct_full_generation_trace/generation_token_vocab_logits/*
```

使用的主要检查命令：

```powershell
rg --files qwen25_0p5b_instruct_full_generation_trace `
  artifacts/module16_hls_fixtures/step_00

Get-Content -Encoding UTF8 `
  module16_lm_head_hls/net/fpga_server_emulator.py

rg -n "LMH1|TCP|repetition|fixture|step_00|19016" `
  module16_lm_head_hls/README.md `
  realFpga/AXU9EGB_MODULE16_BOARD_BRINGUP_PLAN.md
```

第一次对整个 trace 目录执行 `rg --files`，输出约 7,474 行并被终端截断。
这不是数据缺失；原因是 trace 保存了全部 24 层中间张量。后续改为只检查模块
16 需要的文件名和阶段 G 计划段落。第一次未指定编码读取调试日志时出现中文
乱码，随后固定使用 `Get-Content -Encoding UTF8`。

### 输入数据确认

```text
weight shape       = (151936, 896)
weight dtype       = float16
weight data bytes  = 272269312
hidden elements    = 896
history words      = 4748
history set bits   = 27
golden logits      = 151936
processed scores   = (1, 151936), float32
expected token     = 104198
```

历史位图有 27 个置位 token，少于 prompt 的 36 个 token，是因为位图只记录
“是否出现过”，重复 token 只占一个 bit。

### 实现内容

新增的上位机程序支持：

```text
--host
--port
--weight
--fixture-root
--trace-root
--step
--load-weight
--chunk-bytes
--return-logits
--repetition-penalty
--disable-repetition-penalty
--timeout
--start-emulator
```

主要行为：

1. 使用 `np.load(..., mmap_mode="r")` 映射 260 MiB 权重；
2. 校验 weight/hidden/history/logits 的类型和维度；
3. PING 读取加载前状态；
4. 按指定大小分块发送 `LOAD_WEIGHT`；
5. 再次 PING，确认 hidden、vocab 和 weight bytes；
6. 发送 `RUN_TOKEN`；
7. 比较 raw logits、raw Top-5、processed scores、processed Top-5、
   服务端 argmax、上位机 argmax、selected score 和 expected token。

同时增强 `cpu_client.py`：

- 正确的 FP16 C-contiguous mmap 不再被无条件复制；
- 增加权重上传进度回调；
- 拒绝小于等于 0 的分块大小。

静态检查命令：

```powershell
C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  -m py_compile `
  module16_lm_head_hls/net/cpu_client.py `
  tools/run_module16_board_trace.py

C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  tools/run_module16_board_trace.py --help
```

结果：语法检查通过，命令行参数可正常显示。

---

## 047 - 阶段 G-1 软件模拟器 step 0 回归

记录时间：2026-07-24  
记录人：zb

### 完整回归命令

```powershell
C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  tools/run_module16_board_trace.py `
  --start-emulator `
  --load-weight `
  --chunk-bytes 1048576 `
  --step 0 `
  --return-logits `
  --repetition-penalty 1.1 `
  --timeout 300
```

该命令启动一个初始无权重的软件模拟器，再通过真实本机 TCP 上传权重和执行
step 0。关键结果：

```text
ping_before:
  hidden=0
  vocab=0
  weight_bytes=0

weight upload:
  bytes=272269312
  chunk_bytes=1048576
  seconds=1.287
  throughput=201.821 MiB/s

ping_after:
  hidden=896
  vocab=151936
  weight_bytes=272269312

run_seconds=0.230
selected_token=104198
expected_token=104198
selected_score=20.015625
raw_max_abs=0.00390625
raw_top5_overlap=5/5
processed_max_abs=0.00390625
processed_top5_overlap=5/5
server_vs_host_argmax=PASS
server_score=PASS
MODULE16_TRACE status=PASS
```

`raw_max_abs=0.00390625` 比较的是软件模拟器根据 FP16 weight 和 FP16 hidden
重新计算得到的 raw logits，与 fixture 中由原始 Qwen trace 转换得到的 FP16
golden logits。误差低于当前验收阈值 0.02。processed 误差则是在模拟器 raw
logits 上按历史位图重新应用 repetition penalty=1.1 后，与
`generation_token_vocab_logits/prefill_next_token_vocab_logits.npy` 比较。

所有检查：

```text
selected_token=PASS
raw_logits_atol=PASS
raw_top5=PASS
processed_scores_atol=PASS
processed_top5=PASS
server_vs_host_argmax=PASS
server_score=PASS
```

### 兼容性回归

旧入口回归命令：

```powershell
C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  tools/run_module16_tcp_loopback.py --step 0
```

结果：

```text
token=104198
expected=104198
max_abs=0.00390625
top5_overlap=5/5
status=PASS
```

不回传 logits 的正常运行模式：

```powershell
C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  tools/run_module16_board_trace.py `
  --start-emulator `
  --load-weight `
  --chunk-bytes 1048576 `
  --step 0 `
  --repetition-penalty 1.1 `
  --timeout 300
```

结果：

```text
selected_token=104198
expected_token=104198
status=PASS
```

### 阶段结论

阶段 G-1 完成。上位机的文件读取、mmap 权重、LMH1 分块上传、CRC、连续会话、
PING READY、RUN_TOKEN、完整 logits 回传、repetition penalty 和 argmax
验证链路已经在软件模拟器上通过。

本阶段没有向真实板卡上传 260 MiB 权重，也没有执行真实 PL 内核。下一大阶段
应按规划进入真实板卡逐级验证；由于阶段 H 要避免直接跳到全量权重，先检查
当前板卡程序、网络服务和 HLS IP 状态，再选择小尺寸/受控上传测试。

---

## 048 - 阶段 H-4：真实板卡 4×4 受控计算准备与首次故障

记录时间：2026-07-24～2026-07-25  
记录人：zb

### 目标

在上传 260 MiB 完整 LM Head 权重前，先使用 4×4 权重、4 元素 hidden 和
1 个历史位图 word 验证真实 PL 内核。测试覆盖：

1. 无 repetition penalty 的普通 argmax；
2. `repetition_penalty=2.0` 后 token 发生预期变化；
3. 相同 logit 时选择编号更小的 token；
4. 回传完整 logits 和只回传 token 两种模式；
5. 尺寸不匹配错误及同一 TCP 连接的恢复能力。

### 板端服务改造

修改：

```text
realFpga/vitis/workspace/lm_head_net_diag/src/lwip_lm_head_raw_server.c
```

原服务只接受 Qwen2.5-0.5B 固定尺寸 `896×151936`，且 HLS 控制寄存器也写死
这两个尺寸。本次改为在上限内接受运行时尺寸，并动态处理：

```text
hidden_size
vocab_size
weight_bytes = hidden_size × vocab_size × 2
history_words = ceil(vocab_size / 32)
hidden/logits 的收发字节数
HLS hidden_size/vocab_size 控制参数
```

同时加入只用于 `hidden_size<=4 && vocab_size<=4` 的低地址诊断缓冲区：

```text
small_hidden
small_weight
small_history
small_logits
```

重新链接后的 ELF 符号地址为：

```text
small_hidden  = 0x00200600
small_weight  = 0x00200640
small_history = 0x00200680
small_logits  = 0x002006c0
```

这样可以把“小尺寸计算是否成功”和“PL 是否能访问 0x40000000 以上的大块保留
DDR”两个问题分开定位；完整模型仍然使用原来的高地址保留 DDR。

### 上位机测试程序

新增：

```text
tools/stage_h4_board_small_test.py
```

测试权重为：

```text
[ 10, 5, 0, 0 ]
[  6, 5, 0, 0 ]
[ -2, 1, 0, 0 ]
[ -3, 0, 0, 0 ]
```

预期：

```text
hidden=[1,0,0,0]，无 penalty       -> token 0，score 10
history 含 token 0，penalty=2.0    -> token 1，score 6
hidden=[0,1,0,0]，token 0/1 均为 5 -> token 0（较小编号优先）
```

### 首次真实板运行及故障

板卡起初：

```text
ping 192.168.8.190：4/4 成功
```

使用旧 bitstream 和已改造软件上传 32 字节 4×4 权重后：

```text
PING before：hidden=0, vocab=0, bytes=0
PING after ：hidden=4, vocab=4, bytes=32
```

第一次 `RUN_TOKEN` 后，上位机收到：

```text
ConnectionResetError: [WinError 10054]
```

随后：

```text
板卡 IP 不再响应 ping
A53 无法 halt（timeout）
通过 PS TAP 读取 0xA0000000 HLS 控制地址失败
AXI AP transaction error, DAP status 0x3C000021
```

判断：上传、协议解析和 DDR 写入已完成，故障发生在启动 HLS IP 后；A53 很可能
在 AXI 访问中等待，且 AXI/DAP 通道已进入无法正常恢复的状态。这不是普通 TCP
异常，也不是上位机数值比较失败。

相关诊断脚本：

```text
realFpga/vitis/inspect_hls_runtime.tcl
realFpga/vitis/recover_ps_tap.tcl
```

尝试 `rst -system` 时，当前 XSCT 目标不支持该 reset 类型；改为重新配置 PL 后，
DAP 错误仍存在。说明本次锁死状态需要物理断电重启才能清除。

排查文件时曾对整个 Vivado 构建目录执行过一次范围过大的文本搜索，输出约
913k tokens 并被终端截断。后续改为只检查 BD Tcl、地址配置和同事工程中的
对应连接。

---

## 049 - 阶段 H-4：发现并修复 AXI 复位拓扑错误

记录时间：2026-07-25  
记录人：zb

### 根因对比

将本工程 BD 与同事已上板运行的 RMSNorm 工程逐项比较，发现复位连接不同：

```text
同事工程：
  proc_sys_reset/interconnect_aresetn -> AXI SmartConnect
  proc_sys_reset/peripheral_aresetn   -> HLS IP ap_rst_n

原 LM Head 工程：
  proc_sys_reset/peripheral_aresetn   -> AXI SmartConnect 和 HLS IP
```

原连接把互连和外设放在同一类复位输出上，可能造成复位释放顺序/同步关系不符合
AXI 基础设施要求，与“启动 HLS 后 AXI/DAP 锁死”的现象一致。

修改：

```text
realFpga/vivado/create_lm_head_axu9eg_bd.tcl
```

修正为：

```text
interconnect_aresetn -> 控制 SmartConnect、内存 SmartConnect
peripheral_aresetn   -> lm_head_argmax/ap_rst_n
```

### Vivado 构建问题与处理

主要构建命令：

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch `
  -source D:\program\LLM_FPGA\realFpga\vivado\build_lm_head_axu9eg.tcl
```

第一次在受限环境运行时，Vivado 子进程 `rundef.js` 出现 `Access denied`，并留下
状态为 Running 的 OOC run。改为在获准的非受限环境重跑。

重跑时 `delete_runs` 拒绝删除残留的 Running run。最初尝试使用
`stop_runs`，但 Vivado 2021.1 不存在该命令；最终修改：

```text
realFpga/vivado/build_lm_head_axu9eg.tcl
```

在删除 OOC run 前，对 Running/Queued 状态执行 `reset_run`。工具提示找不到旧
PID，但成功清理残留状态并重新创建 run。

诊断过程中有一次 PowerShell 使用了 `$error` 作为临时变量名；该名字是只读的
自动变量，因此命令报错。此错误不涉及工程文件，后续不再使用系统保留变量名。

### 构建结果

最终结果：

```text
LMH_STAGE_C_SYNTH_STATUS=synth_design Complete!
LMH_STAGE_C_IMPL_STATUS=write_bitstream Complete!
LMH_STAGE_C_BUILD=PASS
LMH_STAGE_C_WORST_SLACK_NS=3.921
route failed nets=0
timing WNS/TNS/WHS/THS 均通过
```

产物：

```text
realFpga/vivado/build/lm_head_axu9eg/lm_head_axu9eg.runs/impl_1/lm_head_system_wrapper.bit
realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa
```

bitstream 生成期间有 DSP48 未完全流水化和一个 DSP PCIN 布置类警告：

```text
0 Errors
0 Critical Warnings
write_bitstream completed successfully
```

这些警告主要影响进一步的性能/功耗优化，不阻止本轮 100 MHz 功能验证。

---

## 050 - 阶段 H-4：使用新 XSA 更新 Vitis 平台并重建板端程序

记录时间：2026-07-25  
记录人：zb

### 更新平台

新增：

```text
realFpga/vitis/update_platform_hardware.tcl
```

执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  D:\program\LLM_FPGA\realFpga\vitis\update_platform_hardware.tcl
```

脚本对已有平台执行：

```tcl
platform config -updatehw <new lm_head_axu9eg.xsa>
platform write
platform generate -domains standalone_domain
```

结果：

```text
H4_PLATFORM_UPDATE_PASS
FSBL BSP 与新硬件同步
PMUFW BSP 与新硬件同步
standalone_domain BSP 与新硬件同步
lm_head_argmax 驱动重新生成
```

### PHY 补丁核验

比较：

```text
ref/xemacpsif_physpeed.c
realFpga/vitis/workspace/lm_head_axu9eg_platform/.../xemacpsif_physpeed.c
```

结果：

```text
两者 SHA256：
4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
PHY_PATCH_IDENTICAL=PASS
get_Generic_phy_speed 标记存在
```

因此本次平台更新没有丢失 AXU9EGB 网口 PHY 兼容补丁。

### 重建应用

执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  D:\program\LLM_FPGA\realFpga\vitis\build_net_diag.tcl
```

结果：

```text
PHY_PATCH_MARKER=PASS
PHY_PATCH_AFTER_PLATFORM_GENERATE=PASS
APP_ELF_AND_MAP=PASS
STAGE_D_NET_APP_BUILD_PASS
```

新 ELF：

```text
realFpga/vitis/workspace/lm_head_net_diag/Debug/lm_head_net_diag.elf
text=138587
data=7432
bss=280085877
```

第一次直接运行 `verify_stage_f.ps1` 时，被 Windows PowerShell ExecutionPolicy
拦截：

```text
PSSecurityException：此系统上禁止运行脚本
```

改用仅影响本次子进程的命令：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File realFpga\vitis\verify_stage_f.ps1
```

静态验证结果：

```text
lmh1_source=PASS
streaming_weight_rx=PASS
segmented_tcp_tx=PASS
cache_sync_calls=PASS
hls_driver_symbols=PASS
undefined_symbols=0
phy_patch_sha256=4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
elf_bytes=1103960
STAGE_F_VERIFY_PASS
```

### 当前状态

修正后的 bitstream、XSA、BSP 和板端 ELF 已全部准备好。板卡仍处于前一次
HLS 启动造成的 DAP/AXI 锁死状态，软件方式未能恢复。因此在下载新产物并执行
4×4 测试前，需要对开发板做一次物理断电再上电。

---

## 051 - 阶段 H-4：修复版首次上板仍在 PL 控制访问处锁死

记录时间：2026-07-25  
记录人：zb

### 重新上电和下载

用户对开发板物理断电并重新上电后，执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  realFpga\vitis\probe_jtag.tcl
```

结果：

```text
PS TAP：存在
PMU：存在
PL：存在
STAGE_D_JTAG_PROBE_PASS
```

下载前比较 Vitis 平台导出的 bitstream 与修复复位拓扑后的 Vivado bitstream：

```text
length=26510907
SHA256=C47E323CB658D47A81CC3438184BE333ACA65B8DBA40E40188CD0EF4F79F3FC7
两者完全相同
```

执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  realFpga\vitis\program_net_diag.tcl
```

结果：

```text
系统复位成功
PL 配置成功
PS 初始化成功
ELF 下载成功
Cortex-A53 #0 (Running)
STAGE_D_BOARD_PROGRAM_PASS
```

网络检查：

```text
ping 192.168.8.190：10/10 成功
丢包率：0%
往返时间：0～2 ms
```

### 第二次 4×4 测试

执行：

```powershell
C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  tools\stage_h4_board_small_test.py
```

结果：

```text
ping_before={"hidden":0,"vocab":0,"weight_bytes":0}
ping_after ={"hidden":4,"vocab":4,"weight_bytes":32,"status":"PASS"}
第一次 RUN_TOKEN：
ConnectionResetError: [WinError 10054]
```

随后：

```text
ping 192.168.8.190：0/4
读取 0xA0000000：AXI AP transaction error
DAP status=0x3C000021
```

结论：

1. 修复后的 bitstream 确实已下载，排除了误用旧文件；
2. 网络、协议和 32 字节权重上传正常；
3. 使用的是约 `0x00200600` 的低地址诊断缓冲区，因此不是 0x40000000 以上
   大块 DDR 地址导致；
4. 故障仍发生在进入 `run_lm_head_ip()` 后、服务端返回结果前；
5. 复位拓扑修正不是完整根因。

### 离线对比

新增并执行：

```text
realFpga/vivado/compare_ps_reset_properties.tcl
```

本工程与同事 RMSNorm 工程得到相同结果：

```text
USE_FABRIC_RST=1
NUM_FABRIC_RESETS=1
USE_RST0=0
PL_RESETN0_PIN_COUNT=1
S_AXI_HP0_FPD protection enabled
```

本工程的四个 HLS AXI master 均包含：

```text
HP0_DDR_LOW : offset 0x00000000, range 2G
HP0_DDR_HIGH: offset 0x0800000000, range 32G
HP0_LPS_OCM : excluded
```

这些映射与同事工程一致。HLS 寄存器定义也与板端驱动一致：

```text
AP_CTRL     = 0x00
hidden      = 0x10/0x14
weight      = 0x1c/0x20
history     = 0x28/0x2c
raw_logits  = 0x34/0x38
hidden_size = 0x40
vocab_size  = 0x48
```

锁死后尝试读取 PS GPIO/PL 时钟/AFI 状态，但此时 XSCT 只识别到：

```text
DAP (AXI AP transaction error, DAP status 0x30000021)
```

无法继续在线读取。新增诊断脚本：

```text
realFpga/vitis/inspect_ps_pl_state.tcl
```

### 下一次上电的改进

发现原 `program_net_diag.tcl` 的顺序为“先配置 PL、后执行 psu_init”。已调整为：

```text
system reset
-> psu_init（时钟、DDR、AFI）
-> fpga -file（配置 PL）
-> PS-PL isolation removal
-> PS-PL reset config
-> HLS AXI-Lite 无启动预检
-> 下载并运行 ELF
```

预检只执行：

```text
读取 AP_CTRL
写 hidden_size=4
读回 hidden_size
恢复 hidden_size=0
```

不会写 `ap_start`，因此能把“AXI-Lite 控制从未可用”和“启动内核后数据 master
访问出错”区分开。当前 DAP 已再次锁死，执行该预检前需要再次物理断电上电。

---

## 052 - 阶段 H-4：AXI-Lite 无启动预检定位到永久复位

记录时间：2026-07-25  
记录人：zb

### 本次上电后的 JTAG 检查

用户再次物理重启开发板后，首先执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  realFpga\vitis\probe_jtag.tcl
```

结果：

```text
PS TAP：存在
PMU：存在
PL：存在
STAGE_D_JTAG_PROBE_PASS
```

这说明本轮开始时 JTAG 链和器件识别正常。

### 改进后的下载顺序和无启动预检

执行改进后的：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  realFpga\vitis\program_net_diag.tcl
```

脚本依次执行：

```text
system reset
-> psu_init
-> fpga -file
-> PS-PL isolation removal
-> PS-PL reset config
-> 读取 HLS AXI-Lite 控制寄存器
```

第一次以 Cortex-A53 #0 为目标读取 `0xA0000000` 时失败：

```text
Memory read error at 0xA0000000
Cortex-A53 #0: EDITR timeout
```

此时重新执行 JTAG probe 仍能识别 PS/PMU/PL，说明问题不是 JTAG 线缆掉线。
随后新增并执行：

```text
realFpga/vitis/inspect_ps_pl_state.tcl
```

在错误进一步扩散前读到：

```text
GPIO_DATA_5_PL_RESETN0=80000000
PL0_REF_CTRL=01010403
RST_FPD_TOP=000F8002
```

为了把“处理器调试指令执行失败”和“PL AXI 从设备不响应”区分开，修改
`program_net_diag.tcl`：

```tcl
targets -set -filter {name =~ "PSU"}
configparams force-mem-accesses 1
```

然后直接通过 DAP/PSU 访问 HLS AXI-Lite 地址，不依赖 A53 执行调试指令。结果：

```text
Memory read error at 0xA0000000. AP transaction timeout
后续 DAP status：AXI AP transaction error
```

预检没有写 `AP_START`，甚至第一次读取 `AP_CTRL` 就超时。因此故障已经被定位为：

```text
HLS AXI-Lite 控制从设备在内核启动前就处于不响应状态
```

这排除了计算循环、DDR 数据地址、权重长度和 cache flush 是本次首次超时的直接
触发因素。

### 最终根因

对本工程和同事 RMSNorm 工程的 `proc_sys_reset` XCI 属性继续比较，二者均为：

```text
C_AUX_RESET_HIGH=0
```

即 `aux_reset_in` 是低有效输入：

```text
aux_reset_in=0：请求复位
aux_reset_in=1：不请求复位
```

原 LM Head BD 生成脚本中却存在：

```text
const_zero -> proc_sys_reset/aux_reset_in
const_zero -> proc_sys_reset/mb_debug_sys_rst
```

因此 `aux_reset_in` 被永久置 0，`proc_sys_reset` 一直收到有效复位请求，
AXI SmartConnect 和 HLS IP 的 `aresetn/ap_rst_n` 无法正常释放。此前修正
`interconnect_aresetn` 与 `peripheral_aresetn` 的分类是必要的拓扑改进，但
无法解除这个永久复位，所以不是完整根因。

同事 RMSNorm 工程的 `aux_reset_in` 没有连接到低电平常量，不存在该问题。

### 修复

修改：

```text
realFpga/vivado/create_lm_head_axu9eg_bd.tcl
```

新连接为：

```text
const_zero -> mb_debug_sys_rst
const_one  -> aux_reset_in
const_one  -> dcm_locked
```

其中 `aux_reset_in=1` 表示辅助复位未触发，`dcm_locked=1` 表示输入时钟稳定。
脚本内增加了 `C_AUX_RESET_HIGH=0` 的说明，防止后续再次把有效电平理解反。

---

## 053 - 阶段 H-4：永久复位修复后的硬件与板端软件重建

记录时间：2026-07-25  
记录人：zb

### 重新生成 BD 前的一次流程纠正

最初修改 BD 生成脚本后，误先启动了：

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch `
  -source realFpga\vivado\build_lm_head_axu9eg.tcl
```

这会继续使用磁盘上尚未重新生成的旧 BD，因而该次构建产物无效。确认只有该
Vivado 批处理进程后，终止 PID `13068`，再按正确流程执行。该次中止导致原
批处理会话退出码为 1，属于主动取消错误顺序的构建，不是综合实现失败。

正确顺序：

```text
create_lm_head_axu9eg_bd.tcl
-> build_lm_head_axu9eg.tcl
-> update_platform_hardware.tcl
-> build_net_diag.tcl
-> verify_stage_f.ps1
```

### 重新生成 BD

执行：

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch `
  -source realFpga\vivado\create_lm_head_axu9eg_bd.tcl
```

日志明确显示 `const_one` 已连接到：

```text
proc_sys_reset/aux_reset_in
proc_sys_reset/dcm_locked
```

结果：

```text
LMH_STAGE_C_CREATE=PASS
```

### 重新综合、实现和生成 bitstream/XSA

执行：

```powershell
D:\install\Xilinx\Vivado\2021.1\bin\vivado.bat `
  -mode batch `
  -source realFpga\vivado\build_lm_head_axu9eg.tcl
```

结果：

```text
LMH_STAGE_C_SYNTH_STATUS=synth_design Complete!
LMH_STAGE_C_IMPL_STATUS=write_bitstream Complete!
LMH_STAGE_C_BUILD=PASS
LMH_STAGE_C_WORST_SLACK_NS=3.921
```

新产物：

```text
realFpga/vivado/build/lm_head_axu9eg/
  lm_head_axu9eg.runs/impl_1/lm_head_system_wrapper.bit
realFpga/results/20260724_stage_c/lm_head_axu9eg.xsa
```

属性：

```text
bit bytes=26510907
bit SHA256=53BAE4015574E8C01535CE5089BB9FB41FE2C81E8FF94EB9D03B1F6DA4F420DC
XSA bytes=1255845
XSA SHA256=F06E0DD687AED3ABC0A28530C030E2ECAD8324C93D19134A8210FA085F94402F
```

新 bit 的 SHA256 与上一版
`C47E323CB658D47A81CC3438184BE333ACA65B8DBA40E40188CD0EF4F79F3FC7`
不同，证明永久复位修复已产生新的硬件配置文件。

### 更新 Vitis 平台

执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  realFpga\vitis\update_platform_hardware.tcl
```

结果：

```text
H4_PLATFORM_UPDATE_PASS
```

Vivado 输出 bit 与 Vitis 平台中的三份 bit 哈希完全一致：

```text
Vivado impl_1/lm_head_system_wrapper.bit
Vitis export/.../hw/lm_head_axu9eg.bit
Vitis hw/lm_head_axu9eg.bit
Vitis tempdsa/lm_head_axu9eg.bit

SHA256：
53BAE4015574E8C01535CE5089BB9FB41FE2C81E8FF94EB9D03B1F6DA4F420DC
```

### 重建板端应用

执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  realFpga\vitis\build_net_diag.tcl
```

结果：

```text
PHY_PATCH_MARKER=PASS
PHY_PATCH_AFTER_PLATFORM_GENERATE=PASS
APP_ELF_AND_MAP=PASS
STAGE_D_NET_APP_BUILD_PASS
```

ELF：

```text
realFpga/vitis/workspace/lm_head_net_diag/Debug/lm_head_net_diag.elf
bytes=1103960
SHA256=84288B93D9A68BD008486C2EC407622AE55AE3FD7B387C07C7AB86A259D9307F
```

PHY 修补文件与参考文件的 SHA256 均为：

```text
4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
```

因此平台重建没有覆盖同事提供的 AXU9EGB PHY 兼容修补。

### 静态验收

执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File realFpga\vitis\verify_stage_f.ps1
```

结果：

```text
lmh1_source=PASS
streaming_weight_rx=PASS
segmented_tcp_tx=PASS
cache_sync_calls=PASS
hls_driver_symbols=PASS
undefined_symbols=0
lwip_mem_size=262144
lwip_tcp_snd_buf=32768
lwip_tcp_wnd=32768
lwip_memp_num_tcp_seg=512
phy_patch_sha256=4AD6F6537C3F9C648EA84435714B282C9B82AB7E36D45EB46DB94AB0865BEDF5
elf_bytes=1103960
STAGE_F_VERIFY_PASS
```

补充哈希核验时，第一次 PowerShell 命令把 `foreach` 结果直接连接到管道，产生：

```text
ParserError: EmptyPipeElement
```

改为先把 `foreach` 结果保存到 `$rows`，再执行 `$rows | Format-List` 后成功。
这是核验命令语法问题，不涉及工程产物。

### 当前状态与下一步

本次无启动预检使用的仍是永久复位修复前的旧 bitstream；该预检发生 AXI AP
超时后，当前 DAP 已锁死。永久复位修复后的 bit、XSA、BSP 和 ELF 已在电脑端
准备并核验完成，但尚未下载到开发板。

下一步必须先物理断电再上电，然后：

```text
1. probe_jtag.tcl
2. program_net_diag.tcl
3. 确认无启动 AXI-Lite 预检通过
4. ping 192.168.8.190
5. tools/stage_h4_board_small_test.py
```

若第 3 步通过，将首次证明复位已正常释放；随后才执行 4×4 真实 HLS 计算。

---

## 054 - 同事 RMSNorm 工程的 aux_reset_in 设置核验

记录时间：2026-07-25  
记录人：zb

为确认同事工程为何没有永久复位问题，检查了其 BD、XCI 和 Vivado 生成的综合
HDL。

同事工程的 `proc_sys_reset` 参数为：

```text
C_AUX_RESET_HIGH=0
C_EXT_RESET_HIGH=0
```

因此 `aux_reset_in` 和 `ext_reset_in` 都是低有效。

在 BD 的 nets 中，同事只显式连接：

```text
zynq_ultra_ps_e_0/pl_resetn0 -> proc_sys_reset_0/ext_reset_in
```

`aux_reset_in`、`dcm_locked` 和 `mb_debug_sys_rst` 没有画出显式连线。但 Vivado
没有让这些输入在最终硬件中悬空，而是在生成的 `system_wrapper.v` 中补为：

```verilog
.aux_reset_in(1'b1),
.dcm_locked(1'b1),
.ext_reset_in(zynq_ultra_ps_e_0_pl_resetn0),
.mb_debug_sys_rst(1'b0)
```

这三个常量分别表示：

```text
aux_reset_in=1    ：低有效辅助复位未触发
dcm_locked=1      ：时钟已稳定
mb_debug_sys_rst=0：高有效调试复位未触发
```

所以同事工程的最终综合设置是正确的。其图中未连接的端口被 Vivado 补成了安全
的非复位常量，不等于 FPGA 输入悬空。

原 LM Head TCL 的错误是把 `aux_reset_in` 主动、显式接到 `const_zero`。由于该
端口低有效，这等价于永久请求复位。当前 LM Head 工程显式使用：

```text
const_one  -> aux_reset_in
const_one  -> dcm_locked
const_zero -> mb_debug_sys_rst
```

其最终逻辑状态与同事工程相同，但显式连接更便于代码审查和自动重建。

---

## 055 - 阶段 H-4：永久复位修复版真实板卡 4×4 验收通过

记录时间：2026-07-25  
记录人：zb

### 上电后 JTAG 检查

用户物理重启开发板后执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  realFpga\vitis\probe_jtag.tcl
```

结果：

```text
PS TAP：存在
PMU：存在
PL：存在
STAGE_D_JTAG_PROBE_PASS
```

### 修复版首次烧录与 AXI-Lite 预检

执行：

```powershell
D:\install\Xilinx\Vitis\2021.1\bin\xsct.bat `
  realFpga\vitis\program_net_diag.tcl
```

新 bitstream 成功配置，PS-PL isolation/reset 配置完成。无启动预检首次得到：

```text
HLS_AP_CTRL=A0000000: 00000004
HLS_HIDDEN_SIZE_TEST=A0000040: 00000004
HLS_CONTROL_PREFLIGHT_PASS
```

`AP_CTRL=0x4` 表示 HLS IP 的 `ap_idle` 位为 1。`hidden_size` 写入 4 后可以正确
读回，且整个过程没有写 `AP_START`。这在真实板卡上证明：

```text
proc_sys_reset 已正常释放
AXI SmartConnect 已响应
HLS AXI-Lite 控制从设备已响应
```

永久复位根因和修复均得到上板验证。

### ELF 下载上下文问题与修复

第一次预检通过后，`dow` 报错：

```text
STAGE_D_ERROR: Code 16 ... Invalid context
```

原因是预检为了绕过 A53 调试指令执行，主动选择了顶层 `PSU`：

```tcl
targets -set -filter {name =~ "PSU"}
configparams force-mem-accesses 1
```

但下载 ELF 前没有重新选择处理器。`dow` 必须在 Cortex-A53 上下文执行。

修改：

```text
realFpga/vitis/program_net_diag.tcl
```

在 `dow` 前增加：

```tcl
targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
```

重新执行后结果：

```text
HLS_CONTROL_PREFLIGHT_PASS
APPLICATION_DOWNLOAD_END
Cortex-A53 #0 (Running)
STAGE_D_BOARD_PROGRAM_PASS
```

这次问题是 XSCT 目标上下文错误，不是硬件或 ELF 构建错误。

### 网络检查

执行：

```powershell
ping -n 10 192.168.8.190
```

结果：

```text
发送 10，接收 10，丢失 0
丢包率 0%
最短 0 ms，最长 1 ms
```

### 真实 FPGA 4×4 计算

第一次从受限执行环境运行：

```powershell
C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  tools\stage_h4_board_small_test.py
```

Windows 返回：

```text
PermissionError: [WinError 10013]
```

这是执行环境禁止创建到局域网板卡的 TCP socket；请求并取得本地网络权限后，
以完全相同的脚本重新运行。该错误发生在 `socket.connect()`，请求没有到达
板卡。

测试结果：

```text
ping_before={"hidden":0,"vocab":0,"weight_bytes":0}
ping_after ={"hidden":4,"vocab":4,"weight_bytes":32,"status":"PASS"}
```

四个计算用例：

```text
raw_argmax_no_penalty:
  token=0, score=10.0, logits_max_abs=0.0, PASS

penalty_changes_top1:
  token=1, score=6.0, logits_max_abs=0.0, PASS

tie_keeps_lower_token:
  token=0, score=5.0, logits_max_abs=0.0, PASS

token_only_response:
  token=1, score=6.0, PASS
```

异常与恢复测试：

```text
dimension_mismatch：正确返回错误，PASS
same_connection_recovery：同一 TCP 连接继续可用，PASS
STAGE_H4_BOARD_SMALL_TEST=PASS
```

其中 `logits_max_abs=0.0` 是 FPGA 返回的 4 个 raw logits 与上位机用同一组
hidden/weight 计算出的 CPU 参考 logits 逐项比较所得最大绝对误差。本轮小规模
输入数值均可被当前数据类型精确表示，因此结果完全一致。

`penalty_changes_top1` 用例也证明当前 FPGA 核内的 repetition penalty 路径真实
生效，而不仅是单纯矩阵乘法和 argmax。

### 计算后存活检查

4 个正常计算、1 个错误请求和同连接恢复完成后，再次执行网络与 JTAG 检查：

```text
ping 192.168.8.190：10/10，丢包率 0%
Cortex-A53 #0：Running
PS/PMU/PL/PSU/APU：均可识别
STAGE_D_JTAG_PROBE_PASS
```

此前的“第一次 RUN_TOKEN 后网络消失、DAP AXI AP transaction error”没有再次
发生。因此阶段 H-4 的受控小规模真实 FPGA 计算验收完成。

### 下一阶段建议

下一大阶段从受控 4×4 数据扩展到真实 trace：

```text
1. 先用 trace step 0 的真实 hidden，并选取小 vocab 切片；
2. 验证分块权重上传、FPGA logits/token 与 CPU 参考一致；
3. 再逐步扩大 vocab，观察 DDR 占用、TCP 时间和 HLS 执行时间；
4. 最后执行 qwen25_0p5b_instruct_full_generation_trace 的多 step 验证。
```

按约定，本阶段完成后暂停，等待用户确认再进入下一大阶段。

---

## 056 - 阶段 H-5：真实 trace step 0、vocab 128 上板验证

记录时间：2026-07-25  
记录人：zb

### 目标

从人工 4×4 数据扩展到：

```text
qwen25_0p5b_instruct_full_generation_trace
step 0
真实 hidden_size=896
真实 Qwen LM Head 权重
真实 history bitmap
```

为控制第一次真实数据测试的风险，先选择词表前 128 行，不直接上传完整
151936×896 权重。

### 上位机程序扩展

修改：

```text
tools/run_module16_board_trace.py
```

新增：

```text
--vocab-limit N：使用完整权重的前 N 个 token 行
--inspect-only ：只检查输入和参考结果，不建立 TCP 连接
```

切片处理包括：

```text
weight  -> 前 N 行
golden  -> 前 N 个 logits
history -> 前 ceil(N/32) 个 u32，末字按 N 掩码
processed score reference -> 前 N 项
expected token -> 在当前切片和当前 penalty 设置下重新 argmax
```

权重通过 NumPy mmap 读取，前缀切片不需要在磁盘上生成第二份 `.npy` 文件。

原程序直接使用 fixture 中完整词表的 `expected_token=104198`；该 token 对
vocab=128 不可用，因此切片必须重新计算参考 token，不能直接复用完整词表结果。

### 一次只读统计命令引号问题

第一次尝试用 PowerShell 调用很长的 Python `-c` 单行命令时，内层引号被
PowerShell 处理掉，Python 报：

```text
SyntaxError: invalid syntax
```

该命令只读且在导入/解析阶段失败，没有修改数据。后续不再使用嵌套引号复杂的
单行命令，而是通过正式加入程序的 `--inspect-only` 完成检查。

### 切片只读检查

执行 vocab 128、1024、8192、151936 四档检查，结果全部：

```text
MODULE16_TRACE_INSPECT status=PASS
```

step 0 各档摘要：

```text
vocab=128:
  weight=229376 bytes
  history_words=4
  repeated tokens=2
  token=1
  top5=[1,48,40,39,54]

vocab=1024:
  weight=1835008 bytes
  history_words=32
  repeated tokens=7
  token=1

vocab=8192:
  weight=14680064 bytes
  history_words=256
  repeated tokens=12
  token=2073

vocab=151936:
  weight=272269312 bytes
  history_words=4748
  repeated tokens=27
  token=104198
```

完整档重新计算得到的 token `104198` 与 fixture 一致。

### 软件模拟器回归

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --vocab-limit 128 `
  --load-weight `
  --return-logits `
  --start-emulator `
  --timeout 120
```

结果：

```text
selected_token=1
raw_max_abs=0.0001220703125
processed_max_abs=0.0001220703125
raw_top5_overlap=5
processed_top5_overlap=5
全部 checks=true
MODULE16_TRACE status=PASS
```

这证明切片、history、repetition penalty 和参考比较逻辑在上板前一致。

### 真实 AXU9EGB 验证

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --vocab-limit 128 `
  --load-weight `
  --return-logits `
  --timeout 120
```

板卡原先保存的是 4×4 权重：

```text
ping_before hidden=4 vocab=4 weight_bytes=32
```

上传真实切片权重后：

```text
ping_after hidden=896 vocab=128 weight_bytes=229376
weight_upload_seconds=0.0106885
throughput=20.466 MiB/s
```

计算结果：

```text
selected_token=1
expected_token=1
selected_score=12.8515625
raw_max_abs=0.0078125
processed_max_abs=0.0078125
raw_top5_actual=[1,48,40,39,54]
raw_top5_golden=[1,48,40,39,54]
processed_top5_actual=[1,48,40,39,54]
processed_top5_reference=[1,48,40,39,54]
run_seconds=0.0115289
全部 checks=true
MODULE16_TRACE step=0 status=PASS
```

最大绝对误差 `0.0078125` 小于既定 `0.02` 容差，且 token 和 Top-5 均未
改变。HLS 内核将 FP16 hidden/weight 转为 float，按 896 项顺序累加，最后转回
FP16；trace golden 的矩阵乘法实现可能采用不同的并行归约/FMA 顺序。浮点加法
不满足结合律，因此出现约一个 FP16 量化步长的差异是正常现象。

### 计算后存活检查

执行：

```text
ping 192.168.8.190：10/10，丢包率 0%
Cortex-A53 #0：Running
PS/PMU/PL/PSU/APU：均可识别
STAGE_D_JTAG_PROBE_PASS
```

真实 `896×128` 计算没有造成网络或 DAP 锁死。

### 阶段结论与下一步

阶段 H-5 第一档通过：

```text
CPU -> 网口 -> PS DDR -> FPGA HLS -> PS -> 网口 -> CPU
```

已用真实 Qwen trace 数据完整跑通。下一档建议使用 `vocab=1024`：

```text
权重约 1.75 MiB
计算量为 128 档的 8 倍
参考 token 仍为 1
```

按约定，本大阶段完成后暂停，等待用户确认再执行 1024 档。

---

## 057 - 阶段 H-5：真实 trace step 0、vocab 1024 上板验证

记录时间：2026-07-25  
记录人：zb

### 测试规模

第二档使用：

```text
step=0
hidden_size=896
vocab_size=1024
weight shape=1024×896
weight bytes=1835008
history words=32
history set bits=7
repetition_penalty=1.1
reference token=1
reference top5=[1,48,40,854,675]
```

计算量约为：

```text
1024×896=917504 次乘加
```

### 软件模拟器回归

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --vocab-limit 1024 `
  --load-weight `
  --return-logits `
  --start-emulator `
  --timeout 120
```

结果：

```text
selected_token=1
expected_token=1
raw_max_abs=0.001953125
processed_max_abs=0.001953125
raw_top5_overlap=5
processed_top5_overlap=5
全部 checks=true
MODULE16_TRACE status=PASS
```

### 一次受限网络执行

第一次在默认受限环境连接板卡时，再次在 `socket.connect()` 报：

```text
PermissionError: [WinError 10013]
```

请求没有到达板卡，也没有上传权重。使用已授权的局域网执行权限重跑同一命令。

### 真实 AXU9EGB 结果

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --vocab-limit 1024 `
  --load-weight `
  --return-logits `
  --timeout 120
```

上传前板卡保存的是上一阶段 128 行权重：

```text
ping_before hidden=896 vocab=128 weight_bytes=229376
```

权重按两个 LMH1 chunk 上传：

```text
chunk 1：1048576 bytes
chunk 2：786432 bytes
total  ：1835008 bytes
```

上传结果：

```text
ping_after hidden=896 vocab=1024 weight_bytes=1835008
weight_upload_seconds=0.0739834
throughput=23.654 MiB/s
```

计算与比较：

```text
selected_token=1
expected_token=1
selected_score=12.8515625
raw_max_abs=0.0078125
processed_max_abs=0.0078125
raw_top5_actual=[1,48,40,854,675]
raw_top5_golden=[1,48,40,854,675]
processed_top5_actual=[1,48,40,854,675]
processed_top5_reference=[1,48,40,854,675]
run_seconds=0.0771779
全部 checks=true
MODULE16_TRACE step=0 status=PASS
```

所有 1024 个 raw logits 和 repetition penalty 后的 processed scores 都在
`0.02` 容差内；Top-5 顺序与 token 完全一致。

### 计算后存活检查

```text
ping 192.168.8.190：10/10，丢包率 0%
Cortex-A53 #0：Running
PS/PMU/PL/PSU/APU：均可识别
STAGE_D_JTAG_PROBE_PASS
```

`896×1024` 的真实 HLS 计算没有造成网络或 DAP 锁死。

### 下一档

建议下一档使用：

```text
vocab=8192
weight bytes=14680064（约 14 MiB）
history words=256
reference token=2073
reference top5=[2073,1,48,40,3925]
计算量=7340032 次乘加
```

该档将首次验证超过默认 1 MiB LMH1 chunk 很多的连续分块上传，并把计算规模再
扩大 8 倍。按约定，本档完成后暂停。

---

## 058 - 阶段 H-5：真实 trace step 0、vocab 8192 上板验证

记录时间：2026-07-25  
记录人：zb

### 测试规模

第三档使用：

```text
step=0
hidden_size=896
vocab_size=8192
weight shape=8192×896
weight bytes=14680064
history words=256
history set bits=12
repetition_penalty=1.1
reference token=2073
reference top5=[2073,1,48,40,3925]
计算量=8192×896=7340032 次乘加
```

### 软件模拟器回归

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --vocab-limit 8192 `
  --load-weight `
  --return-logits `
  --start-emulator `
  --timeout 120
```

结果：

```text
selected_token=2073
expected_token=2073
raw_max_abs=0.00390625
processed_max_abs=0.00390625
raw_top5_overlap=5
processed_top5_overlap=5
全部 checks=true
MODULE16_TRACE status=PASS
```

### 真实 AXU9EGB 结果

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --vocab-limit 8192 `
  --load-weight `
  --return-logits `
  --timeout 120
```

上传前板卡保存的是上一阶段 1024 行权重：

```text
ping_before hidden=896 vocab=1024 weight_bytes=1835008
```

上传后：

```text
ping_after hidden=896 vocab=8192 weight_bytes=14680064
weight_upload_seconds=0.5601367
throughput=24.994 MiB/s
```

计算与比较：

```text
selected_token=2073
expected_token=2073
selected_score=15.265625
raw_max_abs=0.0078125
processed_max_abs=0.0078125
raw_top5_actual=[2073,1,48,40,3925]
raw_top5_golden=[2073,1,48,40,3925]
processed_top5_actual=[2073,1,48,40,3925]
processed_top5_reference=[2073,1,48,40,3925]
run_seconds=0.6031513
total_seconds=1.1746126
全部 checks=true
MODULE16_TRACE step=0 status=PASS
```

约 14 MiB 权重通过 14 个 1 MiB 级 LMH1 chunk 连续上传成功；8192 个 raw
logits 和 processed scores 全部在 `0.02` 容差内，Top-5 顺序和 token 完全
一致。

### 计算后存活检查

```text
ping 192.168.8.190：10/10，丢包率 0%
Cortex-A53 #0：Running
PS/PMU/PL/PSU/APU：均可识别
STAGE_D_JTAG_PROBE_PASS
```

`896×8192` 真实计算没有造成网络或 DAP 锁死。

### 完整 vocab 风险评估与下一档

完整模型规模：

```text
vocab=151936
weight bytes=272269312（约 259.66 MiB）
计算量=136134656 次乘加
返回 logits=303872 bytes
```

按本档实测粗略线性外推：

```text
权重上传约 10.4 秒
HLS 计算约 11.2 秒
```

协议、板端预留 DDR 和 120 秒上位机超时均能覆盖完整规模。但从 8192 直接到
151936 是约 18.5 倍跳变。为先验证大范围 DDR 连续读写，建议保持约 8 倍递增：

```text
下一档 vocab=65536
weight bytes=117440512（112 MiB）
history words=2048
history set bits=20
计算量=58720256 次乘加
reference token=35946
reference top5=[35946,9707,2073,56568,1]
```

65536 档 `--inspect-only` 已通过。若该档通过，再从 65536 以约 2.32 倍扩到完整
151936 vocab。按约定，本档完成后暂停。

---

## 059 - 阶段 H-5：真实 trace step 0、vocab 65536 上板验证

记录时间：2026-07-25  
记录人：zb

### 测试规模

第四档使用：

```text
step=0
hidden_size=896
vocab_size=65536
weight shape=65536×896
weight bytes=117440512（112 MiB）
history words=2048
history set bits=20
repetition_penalty=1.1
reference token=35946
reference top5=[35946,9707,2073,56568,1]
计算量=65536×896=58720256 次乘加
```

### 软件模拟器回归

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --vocab-limit 65536 `
  --load-weight `
  --return-logits `
  --start-emulator `
  --timeout 120
```

结果：

```text
selected_token=35946
expected_token=35946
raw_max_abs=0.00390625
processed_max_abs=0.00390625
raw_top5_overlap=5
processed_top5_overlap=5
全部 checks=true
MODULE16_TRACE status=PASS
```

### 真实 AXU9EGB 结果

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --vocab-limit 65536 `
  --load-weight `
  --return-logits `
  --timeout 120
```

上传前：

```text
ping_before hidden=896 vocab=8192 weight_bytes=14680064
```

112 MiB 权重按 112 个 1 MiB LMH1 chunk 连续上传。上传后：

```text
ping_after hidden=896 vocab=65536 weight_bytes=117440512
weight_upload_seconds=3.4163172
throughput=32.784 MiB/s
```

计算与比较：

```text
selected_token=35946
expected_token=35946
selected_score=19.3125
raw_max_abs=0.015625
processed_max_abs=0.015625
raw_top5_actual=[35946,9707,2073,56568,1]
raw_top5_golden=[35946,9707,2073,56568,1]
processed_top5_actual=[35946,9707,2073,56568,1]
processed_top5_reference=[35946,9707,2073,56568,1]
run_seconds=4.8153749
total_seconds=8.2612668
全部 checks=true
MODULE16_TRACE step=0 status=PASS
```

最大绝对误差从小档的 `0.0078125` 增大到 `0.015625`，仍小于既定 `0.02`
容差。对应参考最高分为 `19.296875`，FPGA 返回 `19.3125`，差值同样为
`0.015625`。Top-5 顺序和最终 token 均未改变。

该差异仍符合 FP16 输出量化和不同浮点归约顺序的预期，但完整 vocab 验证时继续
保持 `0.02` 门限；若超过门限，将先分析误差分布和排名间隔，而不是仅凭 token
一致判定通过。

### 计算后存活检查

```text
ping 192.168.8.190：10/10，丢包率 0%
Cortex-A53 #0：Running
PS/PMU/PL/PSU/APU：均可识别
STAGE_D_JTAG_PROBE_PASS
```

112 MiB DDR 连续权重和约 5872 万次真实计算没有造成网络或 DAP 锁死。

### 完整 vocab 执行参数

下一阶段可直接使用完整模型，不传 `--vocab-limit`：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --load-weight `
  --return-logits `
  --timeout 120
```

完整规模：

```text
vocab=151936
weight=272269312 bytes（259.65625 MiB）
LMH1 chunk=260 个（259×1 MiB + 688128 bytes）
history words=4748
history set bits=27
raw logits response=303872 bytes
计算量=136134656 次乘加
reference token=104198
reference top5=[104198,35946,108386,111308,9707]
```

按本档实测估算：

```text
上传约 7.9 秒
计算约 11.2 秒
总计约 19～20 秒
```

均低于 120 秒超时。按约定，本档完成后暂停，等待用户确认再执行完整 vocab。

---

## 060 - 阶段 H-6：真实 trace step 0、完整 vocab 上板验证

记录时间：2026-07-25  
记录人：zb

### 完整规模

本阶段不再使用 `--vocab-limit`：

```text
step=0
hidden_size=896
vocab_size=151936
weight shape=151936×896
weight bytes=272269312（259.65625 MiB）
history words=4748
history set bits=27
repetition_penalty=1.1
raw logits response=303872 bytes
计算量=136134656 次乘加
reference token=104198
reference top5=[104198,35946,108386,111308,9707]
```

### 软件模拟器回归

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --load-weight `
  --return-logits `
  --start-emulator `
  --timeout 120
```

结果：

```text
selected_token=104198
expected_token=104198
raw_max_abs=0.00390625
processed_max_abs=0.00390625
raw_top5_overlap=5
processed_top5_overlap=5
全部 checks=true
MODULE16_TRACE status=PASS
```

### 真实 AXU9EGB 完整权重上传

执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --load-weight `
  --return-logits `
  --timeout 120
```

上传前板卡保存的是上一阶段 65536 行权重：

```text
ping_before hidden=896 vocab=65536 weight_bytes=117440512
```

完整权重使用 260 个 LMH1 chunk：

```text
259×1048576 bytes
1×688128 bytes
total=272269312 bytes
```

上传结果：

```text
ping_after hidden=896 vocab=151936 weight_bytes=272269312
weight_upload_seconds=7.6917031
throughput=33.758 MiB/s
```

### 完整 FPGA 计算结果

```text
selected_token=104198
expected_token=104198
selected_score=20.015625
raw_max_abs=0.015625
processed_max_abs=0.015625
raw_top5_actual=[104198,35946,108386,111308,9707]
raw_top5_golden=[104198,35946,108386,111308,9707]
processed_top5_actual=[104198,35946,108386,111308,9707]
processed_top5_reference=[104198,35946,108386,111308,9707]
raw_top5_overlap=5
processed_top5_overlap=5
run_seconds=11.1649511
total_seconds=18.9332007
全部 checks=true
MODULE16_TRACE step=0 status=PASS
```

全部 151936 个 raw logits 和 repetition penalty 后的 processed scores 都在
`0.02` 门限内。最大误差与 65536 档相同，均为 `0.015625`，没有随 vocab
继续增加；最高分本身与参考值完全一致，Top-5 顺序和生成 token 完全一致。

### 计算后存活检查

```text
ping 192.168.8.190：10/10，丢包率 0%
Cortex-A53 #0：Running
PS/PMU/PL/PSU/APU：均可识别
STAGE_D_JTAG_PROBE_PASS
```

完整 259.66 MiB 权重、1.36 亿次乘加和 303872 字节 logits 回传后，网络、PS
和 DAP 均保持正常。

### 阶段结论

模块 16 的单步完整链路已真实跑通：

```text
完整 Qwen 权重 mmap
-> 260 个 TCP/LMH1 权重分块
-> PS DDR 完整权重区
-> FPGA HLS LM Head
-> repetition penalty
-> argmax
-> 151936 个 raw logits 回传
-> CPU 与 trace golden/processed scores 比较
```

### 下一阶段：step 1～7

板端目前仍保存完整权重：

```text
hidden=896
vocab=151936
weight_bytes=272269312
```

下一阶段不再传 `--load-weight`，只为每个 step 发送新的：

```text
hidden.fp16.bin
history_bitmap.u32.bin
repetition_penalty 参数
```

逐步执行：

```powershell
python tools\run_module16_board_trace.py --step 1 --return-logits --timeout 120
...
python tools\run_module16_board_trace.py --step 7 --return-logits --timeout 120
```

每个 step 预计约 11.2 秒，七步总计算约 79 秒。每步分别检查：

```text
generated token
151936 个 raw logits 最大误差
raw Top-5
processed scores 最大误差
processed Top-5
FPGA token 与 CPU argmax
```

按约定，完整 step 0 阶段完成后暂停，等待用户确认再运行 step 1～7。

---

## 061 - 阶段 H-7：完整权重复用的 step 1～7 真实板卡验证

记录时间：2026-07-25  
记录人：zb

### 验证方式

阶段 H-6 已将完整权重保存在板端 PS DDR：

```text
hidden=896
vocab=151936
weight_bytes=272269312
```

本阶段每个 step 都不传 `--load-weight`，分别执行：

```powershell
python tools\run_module16_board_trace.py `
  --step N `
  --return-logits `
  --timeout 120
```

其中 `N=1..7`。每次建立新 TCP 连接后，先用 PING 确认完整权重仍在，再发送新的
hidden/history，执行 HLS 并返回全部 151936 个 logits。

### 逐 step 结果

```text
step  expected/actual  history bits  max abs       run seconds  status
0     104198/104198    27            0.015625      11.1649511   PASS
1     48/48            28            0.01171875    11.1694467   PASS
2     16948/16948      29            0.0078125     11.1712603   PASS
3     3837/3837        29            0.015625      11.1670045   PASS
4     67071/67071      30            0.01171875    11.1720685   PASS
5     102661/102661    31            0.015625      11.1685476   PASS
6     99718/99718      32            0.0078125     11.1694906   PASS
7     100013/100013    33            0.0078125     11.1684629   PASS
```

step 1～7 累计 HLS 请求往返时间：

```text
78.1862811 秒
平均 11.1694687 秒/step
```

包括 step 0 在内的 8 次完整计算累计约：

```text
89.3512322 秒
```

所有 step 均满足：

```text
selected_token=true
server_vs_host_argmax=true
server_score=true
raw_logits_atol=true
processed_scores_atol=true
raw_top5=true
processed_top5=true
```

最坏最大绝对误差：

```text
0.015625 < 0.02
```

### repetition penalty 的实际影响

部分 step 的 raw Top-5 与 processed Top-5 不同，例如：

```text
step 3 raw      =[3837,9909,96050,11,104455]
step 3 processed=[3837,9909,96050,104455,8545]

step 5 raw      =[102661,107076,54364,58695,15469]
step 5 processed=[102661,107076,58695,15469,2101]

step 6 raw      =[99718,93488,100338,14817,107692]
step 6 processed=[99718,93488,100338,107692,9437]
```

这说明 history bitmap 随生成过程更新，FPGA 内的 repetition penalty 确实改变
了部分历史 token 的排名。FPGA 的 raw 和 processed 列表分别都与各自 CPU/trace
参考完全一致。

### generated_ids 最终核对

读取：

```text
qwen25_0p5b_instruct_full_generation_trace/metadata.json
```

FPGA step 0～7 输出：

```text
[104198,48,16948,3837,67071,102661,99718,100013]
```

`metadata.json.generated_ids`：

```text
[104198,48,16948,3837,67071,102661,99718,100013]
```

结果：

```text
generated_ids：8/8 完全匹配
生成文本：我是Qwen，由阿里云开发
metadata response：我是Qwen，由阿里云开发
```

### 最终存活检查

七个连续完整计算、七次 TCP 重新连接和完整 logits 回传后：

```text
ping 192.168.8.190：10/10，丢包率 0%
Cortex-A53 #0：Running
PS/PMU/PL/PSU/APU：均可识别
STAGE_D_JTAG_PROBE_PASS
```

板端完整权重在所有重连之间均保持：

```text
hidden=896
vocab=151936
weight_bytes=272269312
```

### 阶段 H-7 总结

真实 AXU9EGB 上的模块 16 已完成完整 8-step trace 验收：

```text
完整权重上传：PASS
权重复用：7/7 PASS
完整 raw logits：8/8 PASS
processed scores：8/8 PASS
raw Top-5：8/8 PASS
processed Top-5：8/8 PASS
generated_ids：8/8 PASS
最坏最大绝对误差：0.015625
网络/JTAG 稳定性：PASS
```

按当前验证范围，模块 16 的“CPU 读取 trace -> 网口 -> PS DDR -> FPGA LM Head +
repetition penalty + argmax -> 网口返回 CPU”功能验收通过。

按约定，本大阶段完成后暂停。

---

## 063 - 按目标 GitHub 仓库规范整理并生成 Module 16 交付 ZIP

记录时间：2026-07-25  
记录人：zb

### 目标

将已经通过真实 AXU9EGB 验收的模块 16 整理为目标仓库：

```text
https://github.com/Makiyo6230/Fpga_deploy_qwen25
```

中的：

```text
module/16_lm_head_optional
```

格式。参考目录：

```text
module/_example_rmsnorm_minimal
```

本阶段只生成 ZIP，交由相关负责人上传，不直接修改远程仓库。

### 获取并核对仓库规范

GitHub 页面直接读取未取得稳定内容后，改用 shallow clone：

```powershell
git clone --depth 1 `
  https://github.com/Makiyo6230/Fpga_deploy_qwen25.git `
  D:\program\LLM_FPGA\tmp\Fpga_deploy_qwen25_template
```

核对结果：

```text
_example_rmsnorm_minimal/
├─ README.md
├─ manifest.yaml
├─ hls/
├─ ip_repo/
├─ vivado/
├─ vitis_ps/
├─ orin_backend/
├─ tests/
└─ reports/
```

仓库 `.gitignore` 明确忽略：

```text
*.elf
*.bit
*.xsa
*.jou
*.log
.Xil/
Debug/
Release/
```

因此面向 GitHub 的包不包含预构建 bitstream、XSA、ELF、模型权重、完整 trace
或 Vivado/Vitis workspace/cache。三项已验收二进制的 SHA-256 写入
`reports/BOARD_ACCEPTANCE.md`，源码和 Tcl 保留用于重建。

### 整理的文件

交付目录：

```text
D:\program\LLM_FPGA\realFpga\deliverables\
  20260725_module16_v1\16_lm_head_optional
```

内容映射：

```text
hls/
  HLS 源码、header、testbench、csim/csynth/cosim/export Tcl

ip_repo/lm_head_argmax/
  从 xilinx_com_hls_lm_head_argmax_1_0.zip 干净解包
  包含 component.xml、HDL、xgui 和 HLS driver

vivado/
  AXU9EGB Block Design、implementation 和检查 Tcl

vitis_ps/
  Cortex-A53 standalone/lwIP 服务端源码、linker script、
  Vitis/XSCT 脚本和 AXU9EGB PHY speed 补丁

orin_backend/
  LMH1 TCP 协议、CPU 客户端、NumPy 板端模拟器和 trace 程序

tests/
  权重导出、fixture 生成和 4x4 真实板卡小测试

reports/
  HLS csynth/cosim、Vivado timing/utilization/power、
  真实板卡 penalty ON/OFF 8-step 验收摘要
```

顶层 `README.md` 与 `manifest.yaml` 补充了：

```text
计算公式和模块边界
FP16/FP32 数值顺序
repetition penalty 默认关闭、逐请求可开
完整 logits 与仅 token 两种输出
AXI 接口、寄存器、DDR buffer 和 cache 操作
LMH1 TCP 协议
数据准备与重建命令
真实板卡验收数据
未上传文件及原因
当前串行 correctness baseline 的性能限制
```

### 遇到的问题与修复

#### 1. `Copy-Item -LiteralPath ...\src\*` 没有展开通配符

现象：

```text
vitis_ps/src 初次检查为空
```

原因：`-LiteralPath` 将 `*` 当普通字符，不执行 wildcard 展开。

修复：

```powershell
Get-ChildItem -LiteralPath <original-src> -File |
  Copy-Item -Destination <package-src>
```

复查得到 16 个 Vitis PS 源文件。

#### 2. Vivado Tcl 仍指向原始工作区 IP 路径

初始副本使用：

```text
../../module16_lm_head_hls/build/lm_head_export/solution1/impl/ip
```

该路径在目标仓库模块目录中不存在。修复为基于脚本位置的相对路径：

```text
../ip_repo/lm_head_argmax
```

implementation 输出也改到：

```text
vivado/build/results
```

避免依赖 `realFpga/results/20260724_stage_c`。

#### 3. 打包后的 Python 上位机默认 artifacts 路径多了一层

脚本移动到：

```text
orin_backend/tools/
```

后，原 `parents[1]` 同时作为 import root 和 artifact root 会把数据定位到
`orin_backend/artifacts`。修复为：

```text
BACKEND_ROOT = parents[1]  # Python import
MODULE_ROOT  = parents[2]  # artifacts / trace
```

`stage_h4_board_small_test.py` 同步将 `orin_backend` 加入 `sys.path`。

#### 4. 本地没有 PyYAML/Node yaml

尝试读取 manifest 时分别出现：

```text
ModuleNotFoundError: No module named 'yaml'
Error: Cannot find module 'yaml'
```

没有为一次结构检查安装额外依赖。改用目标仓库自带：

```powershell
python tools\validate_ip_manifest.py <package>\manifest.yaml
```

该脚本要求兼容字段：

```text
name:
top_function:
control_interface:
data_interfaces:
dtype:
```

manifest 补充这些字段后验证通过。

#### 5. Vivado 验证临时目录首次选在不可用的 `C:\tmp`

首次启动前工作目录不存在，随后创建 `C:\tmp` 子目录又被权限拒绝。改用工作区
可写目录：

```text
D:\program\LLM_FPGA\tmp\lmh_package_ip_verify_20260725
```

Vivado batch 验证正常完成。

### 验证

#### Python 与 manifest

```text
PYTHON_AST_PASS files=10
CLI help exit codes=0,0,0
manifest looks structurally complete
MANIFEST_VALIDATOR_EXIT=0
```

#### 使用打包后代码运行真实 fixture 的软件模拟器

执行：

```powershell
python orin_backend\tools\run_module16_board_trace.py `
  --weight D:\program\LLM_FPGA\artifacts\model.embed_tokens.weight.fp16.npy `
  --fixture-root D:\program\LLM_FPGA\artifacts\module16_hls_fixtures `
  --trace-root D:\program\LLM_FPGA\qwen25_0p5b_instruct_full_generation_trace `
  --step 0 `
  --load-weight `
  --return-logits `
  --start-emulator `
  --timeout 120
```

结果：

```text
repetition_penalty enabled=0
selected_token=104198
expected_token=104198
raw_max_abs=0.00390625
raw_top5_overlap=5
MODULE16_TRACE status=PASS
PACKAGED_EMULATOR_EXIT=0
```

#### Vivado 直接识别交付 IP repository

执行：

```powershell
vivado.bat -mode batch `
  -source vivado\verify_lm_head_ip.tcl `
  -tclargs ip_repo\lm_head_argmax
```

结果：

```text
LMH_IP_VERIFY=PASS
LMH_IP_VLNV=xilinx.com:hls:lm_head_argmax:1.0
LMH_IP_NAME=lm_head_argmax
LMH_IP_VERSION=1.0
PACKAGED_IP_VIVADO_VERIFY_EXIT=0
```

#### ZIP 内容

生成命令：

```powershell
Compress-Archive `
  -LiteralPath <package>\16_lm_head_optional `
  -DestinationPath <package>\16_lm_head_optional_20260725.zip `
  -CompressionLevel Optimal
```

检查内容：

```text
源码目录文件数：126
未压缩总字节：2470869
ZIP entries：129
ZIP CRC：PASS
唯一根目录：16_lm_head_optional/
必需文件：PASS
禁止扩展名/模型/缓存：0
```

最终文件：

```text
D:\program\LLM_FPGA\realFpga\deliverables\
20260725_module16_v1\16_lm_head_optional_20260725.zip
```

大小：

```text
363447 bytes
```

SHA-256：

```text
8F68017C6C8B117ABF380195AAED0E05888C8D63EFB21AAD67D893C7013D4DB0
```

### 阶段结论

Module 16 已按目标仓库示例目录完成整理。包中包含可审阅、可综合、可重建、
可运行软件模拟器和可接真实板卡的源码与报告，同时遵守目标仓库对二进制、
模型、trace 和生成目录的排除规则。交付 ZIP 完整性与关键执行路径均验证通过。

按用户约定，本大阶段完成后暂停，等待确认后再进行上传前复核或负责人反馈修改。

---

## 062 - 阶段 H-8：默认关闭 repetition penalty 后重测完整 8 step

记录时间：2026-07-25  
记录人：zb

### 默认策略修改

用户要求默认不启用 repetition penalty。板端固件本身按每个 `RUN_TOKEN` 请求的
flag 动态控制，不存在需要重新生成 bitstream/ELF 的全局默认值。因此修改标准
trace 上位机：

```text
tools/run_module16_board_trace.py
```

新策略：

```text
不带参数：
  enable_repetition_penalty=false

显式带 --enable-repetition-penalty：
  enable_repetition_penalty=true

--disable-repetition-penalty：
  为兼容旧命令仍可接受，但默认关闭后无需再写
```

程序输出和 metrics 中新增：

```text
repetition_penalty enabled=0/1
repetition_penalty_enabled=false/true
repetition_penalty=<请求数值>
```

README 同步补充，注释时间与人员：

```text
2026-07-25
zb
```

修改文件：

```text
module16_lm_head_hls/README.md
```

### 默认关闭的软件检查

对 step 0～7 执行 `--inspect-only`，全部明确输出：

```text
repetition_penalty enabled=0 value=1.1
MODULE16_TRACE_INSPECT status=PASS
```

注意：数值 `1.1` 仍随请求结构提供，但 enable flag 为 0，因此 HLS 不应用该
数值。

使用完整软件模拟器回归 step 0：

```powershell
python tools\run_module16_board_trace.py `
  --step 0 `
  --load-weight `
  --return-logits `
  --start-emulator `
  --timeout 120
```

结果：

```text
repetition_penalty_enabled=false
selected_token=104198
raw_max_abs=0.00390625
raw_top5_overlap=5
全部适用 checks=true
MODULE16_TRACE status=PASS
```

关闭模式不再把 FPGA 结果与 `generation_token_vocab_logits` 的 processed scores
比较，因为该文件明确包含 penalty=1.1；关闭模式应与 raw
`lm_head_vocab_logits` 比较。

### 真实板卡执行方式

板端继续复用阶段 H-6 上传的完整权重，不重新上传。逐步执行：

```powershell
python tools\run_module16_board_trace.py `
  --step N `
  --return-logits `
  --timeout 120
```

其中 `N=0..7`，命令中没有 `--enable-repetition-penalty`。

每步 PING 均确认：

```text
hidden=896
vocab=151936
weight_bytes=272269312
```

### 无 penalty 的 8-step 结果

```text
step  expected/actual  raw max abs   run seconds   status
0     104198/104198    0.015625      11.0900220    PASS
1     48/48            0.01171875    11.0886199    PASS
2     16948/16948      0.0078125     11.0899902    PASS
3     3837/3837        0.015625      11.0903150    PASS
4     67071/67071      0.01171875    11.0894621    PASS
5     102661/102661    0.015625      11.0875152    PASS
6     99718/99718      0.0078125     11.0937842    PASS
7     100013/100013    0.0078125     11.0916765    PASS
```

累计：

```text
8 step run_seconds=88.7213851
平均=11.0901731 秒/step
最坏 raw 最大绝对误差=0.015625 < 0.02
raw Top-5=8/8 PASS
raw argmax token=8/8 PASS
server score=8/8 PASS
```

无 penalty 输出 token：

```text
[104198,48,16948,3837,67071,102661,99718,100013]
```

它仍与 `metadata.json.generated_ids` 8/8 相同。这不是 penalty 仍在生效，而是
当前 trace 恰好满足 raw Top-1 与 processed Top-1 相同；因此只检查 token 无法
区分开关状态。

### 证明 penalty 确实已关闭

step 2 的 token `16948` 已在历史中且 raw score 为正。两种模式：

```text
关闭：
  selected_score=30.046875

开启 penalty=1.1：
  selected_score=27.315340042114258
  约等于 30.046875 / 1.1
```

真实板卡默认关闭测试返回 `30.046875`，证明 FPGA 接收到的
`enable_repetition_penalty` 为 0，而不是仅修改了上位机参考。

另外，关闭后部分 Top-5 保持 raw 排名：

```text
step 3 raw/off =[3837,9909,96050,11,104455]
step 5 raw/off =[102661,107076,54364,58695,15469]
step 6 raw/off =[99718,93488,100338,14817,107692]
```

与开启 penalty 时的 processed Top-5 不同。

最后执行：

```powershell
python tools\run_module16_board_trace.py `
  --step 2 `
  --enable-repetition-penalty `
  --inspect-only
```

输出恢复为：

```text
repetition_penalty enabled=1
score=27.315340042114258
```

证明显式开启接口仍然可用。

### 最终存活检查

```text
ping 192.168.8.190：10/10，丢包率 0%
Cortex-A53 #0：Running
PS/PMU/PL/PSU/APU：均可识别
STAGE_D_JTAG_PROBE_PASS
```

### 当前最终口径

```text
标准 trace 客户端默认：repetition penalty 关闭
显式 --enable-repetition-penalty：开启
板端固件/HLS：保持每请求动态开关
无 penalty 完整 8-step：PASS
有 penalty 完整 8-step：PASS（阶段 H-7）
```

按约定，本大阶段完成后暂停。

---

## 064 - 澄清 `orin_backend` 当前定位并补充 repetition penalty 计算说明

记录时间：2026-07-25  
记录人：zb

### 用户确认

目录名称保持目标仓库模板要求的：

```text
orin_backend/
```

不移动或改名，但必须在 README 中明确：当前内容是 PC 上位机和板卡验证程序，
尚未实现接入 `orin_runtime` 的真实 Orin 推理 backend。

### README 修改

修改：

```text
realFpga/deliverables/20260725_module16_v1/
16_lm_head_optional/orin_backend/README.md
```

新增当前实际链路：

```text
PC 读取 trace/权重
  -> LMH1 TCP
  -> 开发板 PS
  -> FPGA LM Head + 可选 repetition penalty + argmax
  -> token/score/可选 raw logits 返回 PC
  -> PC 对比 golden
```

明确当前未实现：

```text
未接入目标仓库 orin_runtime
未从运行中的 Qwen 推理拦截 LM Head tensor
未处理 CUDA/torch tensor
未通过 fpga-modules 参数替换模型 LM Head
```

同时说明现有 Python 协议和客户端将来可以在 Orin 复用，但不能据此宣称已经完成
Orin backend。

### `--enable-repetition-penalty` 补充内容

README 已详细记录：

```text
不带参数：
  LMH1 flags bit 0 = 0
  enable_repetition_penalty = 0
  直接 argmax(raw_logits)

显式 --enable-repetition-penalty：
  LMH1 flags bit 0 = 1
  enable_repetition_penalty = 1
  使用 history bitmap 和 penalty 计算 policy score
```

history bitmap：

```text
word_index = token_id / 32
bit_index  = token_id % 32
seen       = (history_bitmap[word_index] >> bit_index) & 1
```

LM Head：

```text
acc_v = sum(hidden[i] * weight[v, i]), i=0..895
raw_logit_v = FP16(acc_v)
```

penalty 计算，`p=repetition_penalty`：

```text
未启用或 token 未出现：
  score_v = raw_logit_v

已启用且 token 已出现：
  raw_logit_v < 0  -> score_v = raw_logit_v * p
  raw_logit_v >= 0 -> score_v = raw_logit_v / p
```

最终：

```text
selected_token = argmax(score_v)
selected_score = max(score_v)
```

并补充：

```text
raw_logits 缓冲区始终保存 penalty 之前的 FP16 logits
penalty 只用于临时 score 和 token 选择
--return-logits 返回 raw logits，不是 processed scores
开关由每个 RUN_TOKEN 请求独立携带，不是板端永久状态
```

### 重新打包

为保留此前交付包并避免混淆，生成新版：

```text
D:\program\LLM_FPGA\realFpga\deliverables\20260725_module16_v1\
16_lm_head_optional_20260725_v2.zip
```

大小：

```text
365270 bytes
```

SHA-256：

```text
AFD53294251564FCDB03B824749F4540C3FAA39F3239E506A218D41DFF2DFFC4
```

### ZIP 验证

首次验证命令把中文检查字符串直接嵌入 `python -c`，经过 Windows PowerShell
命令行编码后出现乱码和：

```text
SyntaxError: unterminated string literal
```

修复为只使用 ASCII 关键字检查 README 内容，同时仍用 UTF-8 解码文件。

最终结果：

```text
ZIP_V2_VALIDATION_PASS
entries=129
CRC=PASS
README checks=7/7
forbidden files=0
```

后续应发送 `v2.zip`，旧的无 `v2` ZIP 仅保留作为修改前版本。

---

## 065 - 单独打包完整 Vivado 工程、bitstream 与完整 trace

记录时间：2026-07-25  
记录人：zb

### 用户要求

目标仓库 README 提示大文件应单独沟通存放。用户要求将此前未进入 GitHub 主提交
包的以下三类内容再打成一个独立压缩包：

```text
1. 完整 Vivado 工程
2. bitstream
3. 完整 trace 数据
```

主提交：

```text
16_lm_head_optional_20260725_v2.zip
```

保持不变。

### 原始路径和统计

完整 Vivado 2021.1 工程：

```text
D:\program\LLM_FPGA\realFpga\vivado\build\lm_head_axu9eg
1147 files
321561882 bytes
```

已验收 bitstream：

```text
D:\program\LLM_FPGA\realFpga\vivado\build\lm_head_axu9eg\
lm_head_axu9eg.runs\impl_1\lm_head_system_wrapper.bit
26510907 bytes
SHA-256:
53BAE4015574E8C01535CE5089BB9FB41FE2C81E8FF94EB9D03B1F6DA4F420DC
```

完整 trace：

```text
D:\program\LLM_FPGA\qwen25_0p5b_instruct_full_generation_trace
7732 files
302147718 bytes
```

trace 目录完整保留，没有删减，其中包括：

```text
00_prefill_full_prompt
01_decode_token_01 ... 07_decode_token_07
generation_token_vocab_logits
metadata.json
name_mapping.json
flightllm_test_demo
```

bitstream 本来已经存在于完整 Vivado 工程中。为满足“工程、bitstream、trace”
三个独立类别并方便直接取用，附件包在 `bitstream/` 下有意再保存同一文件，
因此逻辑源数据约有 26.5 MB 重复。

### 附件结构

```text
16_lm_head_optional_large_artifacts/
├─ README.md
├─ vivado_project/
│  └─ lm_head_axu9eg/
├─ bitstream/
│  └─ lm_head_system_wrapper.bit
└─ trace/
   └─ qwen25_0p5b_instruct_full_generation_trace/
```

README 说明了内容、原始统计、Vivado 版本、板卡型号、关键文件校验值，以及生成
工程换机器后可能需要重新指定 HLS IP repository 的注意事项。

### 打包方法

新增可复现脚本：

```text
realFpga/package_module16_large_artifacts.py
```

脚本直接把三个不同源路径映射到统一 ZIP 根目录，不先复制约 650 MB staging
数据。使用 ZIP64 和 Deflate level 6，并在出现重复归档路径、缺失源文件或符号
链接时停止。

执行：

```powershell
python realFpga\package_module16_large_artifacts.py `
  --vivado-project realFpga\vivado\build\lm_head_axu9eg `
  --bitstream realFpga\vivado\build\lm_head_axu9eg\`
lm_head_axu9eg.runs\impl_1\lm_head_system_wrapper.bit `
  --trace qwen25_0p5b_instruct_full_generation_trace `
  --readme realFpga\deliverables\20260725_module16_v1\`
16_lm_head_optional_large_artifacts\README.md `
  --output realFpga\deliverables\20260725_module16_v1\`
16_lm_head_optional_large_artifacts_20260725.zip
```

结果：

```text
PACKAGER_AST_PASS
ZIP_CREATED
files=8881
source_bytes=650222770
zip_bytes=329806547
LARGE_ZIP_CREATE_EXIT=0
```

### 完整性验证

验证不是只读取 central directory，而是执行了 `ZipFile.testzip()`，流式解压并
检查每个 entry 的 CRC。同时检查：

```text
唯一 ZIP 根目录正确
README：1 file
Vivado 工程：1147 files
独立 bitstream：1 file
完整 trace：7732 files
总 entry：8881
总原始字节：650222770
```

还从 ZIP 内分别读取并计算：

```text
bitstream/ 下的独立 bit
Vivado 工程 impl_1 内的 bit
trace/metadata.json
```

结果：

```text
LARGE_ZIP_VALIDATION_PASS
CRC=PASS
两份 bitstream SHA-256 相同且等于已验收值
trace metadata SHA-256 等于原始值
LARGE_ZIP_VALIDATION_EXIT=0
```

### 最终附件

```text
D:\program\LLM_FPGA\realFpga\deliverables\20260725_module16_v1\
16_lm_head_optional_large_artifacts_20260725.zip
```

大小：

```text
329806547 bytes
约 314.5 MiB
```

SHA-256：

```text
0FAA1F16396392F4B02DFEAB64B6F2E71F52C7AF3B1ABE4A496C557D7D53CD65
```

该大文件附件不应直接提交目标 GitHub 仓库；应按仓库说明与负责人单独协商网盘、
Release、LFS 或其他大文件存储方式。

---

## 066 - 按 FPGA 模块 PR 投递规则执行最终只读核查

记录时间：2026-07-25  
记录人：zb

### 核查范围

用户更新了：

```text
realFpga/deliverables/20260725_module16_v1/
16_lm_head_optional/README.md
```

本次不修改模块提交文件，只按目标仓库“模块投递区”规则检查：

```text
hls/
ip_repo/
vivado/
vitis_ps/
orin_backend/
tests/
reports/
```

以及 8 项必须接口信息、主包大文件排除和 ZIP 同步状态。

### README 技术内容

用户新增的三阶段说明中，下列内容正确：

```text
weight [151936,896] @ hidden [896] -> raw_logits [151936]
FP16 输入/权重、FP32 累加、FP16 raw logits
penalty OFF 对 raw logits argmax
penalty ON 对 processed scores argmax
selected_token 是最大分数的索引
selected_score 是对应分数
raw/processed trace 文件区分正确
```

发现两处说明问题：

```text
1. 顶层仍写“从 CPU/Orin 接收”，但 orin_backend/README 已明确尚未接入 Orin。
2. 引用的 Qwen2.5-0.5B_FPGA模块拆分与验证指南.md 不在目标 GitHub
   仓库或本模块提交包中，reviewer 无法从 PR 访问该文件。
```

另外“不随包上传的内容”后统一写成“这些产物可由本目录源码和 Tcl
重新生成”范围过大：bit/XSA/ELF 可以重建，但模型权重与完整 trace 需要另行
取得模型和运行 trace 生成流程，不能仅由 HLS/Vivado Tcl 产生。

### 目录核查

```text
hls/           9 files      PASS
ip_repo/       55 files     PASS
vivado/        6 files      PASS
vitis_ps/      33 files     PASS
orin_backend/  9 files      PASS（明确为 PC 上位机，尚非 Orin runtime backend）
tests/         4 files      PASS
reports/       8 files      PASS
```

关键内容：

```text
HLS source/header/testbench/Tcl：存在
IP component.xml/HDL/driver：存在
Vivado BD/build Tcl、地址/复位说明：存在
PS driver/DDR/cache/lwIP/PHY patch：存在
LMH1 payload/dtype/TCP client/emulator：存在
golden 准备、板卡小测试、误差阈值：存在
HLS/Vivado/真实板卡报告：存在
```

### 8 项接口信息

```text
1. 顶层函数名和签名：
   函数名与参数列表在 README，完整带类型签名在 hls/include 头文件。
   建议 README 也直接给出带类型签名，但当前源码信息完整。

2. tensor shape/dtype/layout：
   manifest.yaml 完整，PASS。

3. AXI-Lite 寄存器：
   manifest.yaml 包含地址和位宽，导出 driver hw header 包含完整寄存器表，PASS。

4. m_axi 端口含义：
   manifest.yaml 四路端口含义完整，PASS。

5. PS DDR buffer 读写顺序：
   vitis_ps/README 和源码说明 write/flush -> set registers/start/done
   -> invalidate/readback，PASS。

6. cache flush/invalidate：
   vitis_ps/README 和 C 源码均明确，PASS。

7. golden 路径：
   manifest 使用 ../../integration_tests/golden_traces/
   qwen25_0p5b_instruct_full_generation_trace，PASS。

8. prefill/decode：
   manifest 标记二者均支持，并说明每次只处理 final-token hidden vector。
   对“prefill 最后一个位置产生下一 token”语义成立，不支持一次输出全部
   prompt 位置的 vocab logits；建议在顶层 README 再明确该边界。
```

### 明确矛盾

`manifest.yaml` 当前：

```yaml
status: orin-tested
```

但 `orin_backend/README.md` 明确：

```text
尚未接入 orin_runtime
未处理 CUDA/torch tensor
当前是 PC 上位机读取保存数据
```

因此 `orin-tested` 不成立。目标模板允许的准确状态为：

```yaml
status: ps-tested
```

这是提交前必须修复项。

### 主包大文件与结构

工作目录：

```text
126 files
约 2.47 MB
```

检查：

```text
.bit/.xsa/.elf/.log/.jou/.npy/.bin/.pyc：NONE
model.safetensors：NONE
__pycache__/.Xil/Debug/Release/build/tmp cache：NONE
```

完整 Vivado 工程、bitstream、trace 已按要求进入独立大文件附件，主提交包的
排除策略正确。

### 自动检查

```text
目标仓库 validate_ip_manifest.py：PASS
Python AST：10/10 PASS
IP component.xml parse：PASS
主包禁入文件：0
主包禁入目录：0
```

### ZIP 同步检查

比较工作目录与：

```text
16_lm_head_optional_20260725_v2.zip
```

结果：

```text
ZIP files=126
working files=126
only in ZIP=0
only in working=0
changed=['README.md']
ZIP_SYNC_PASS=False
```

原因是用户更新了工作目录中的顶层 README，但尚未重新生成 ZIP。完成文档修正后
必须重新打包并采用新文件名或新校验值，不能直接发送当前 v2 ZIP。

### 最终只读核查结论

提交材料和核心接口信息基本完整，功能证据充分，但当前还不能把现有 v2 ZIP
作为最终件。提交前至少要：

```text
1. manifest status: orin-tested -> ps-tested
2. 顶层 README 将当前链路明确为 PC 上位机，Orin 仅为未来可复用接口
3. 完成 README 定稿后重新生成并验证 ZIP
```

建议同时修正：

```text
4. 不引用 PR 中不存在的本地指南文件
5. 区分“硬件产物可重建”与“模型/trace 需另行取得或生成”
6. 顶层 README 明确 prefill 仅处理最后一个位置的 hidden
```

---

## 067 - 执行最终核查中的三项必须修正并生成 v3 提交包

记录时间：2026-07-25  
记录人：zb

### 修改 1：manifest 状态

文件：

```text
realFpga/deliverables/20260725_module16_v1/
16_lm_head_optional/manifest.yaml
```

修改：

```yaml
# 修改前
status: orin-tested

# 修改后
status: ps-tested
```

原因：真实 AXU9EGB、PS/lwIP 和 PC 上位机链路已验收，但尚未接入目标仓库的
`orin_runtime`，不能标记为 `orin-tested`。

### 修改 2：顶层 README 当前链路

文件：

```text
realFpga/deliverables/20260725_module16_v1/
16_lm_head_optional/README.md
```

修改为：

```text
当前由 PC 上位机读取保存数据并发送最后一个 token 的 hidden state 至 FPGA；
同一协议未来可复用于 Orin 侧。
```

该表述与 `orin_backend/README.md` 保持一致，不再暗示已经完成 Orin runtime
集成。

### 修改前验证

执行目标仓库自带 manifest validator、语义断言、Python AST 和禁入文件检查：

```text
manifest looks structurally complete
SEMANTIC_ASSERTIONS_PASS
PYTHON_AST_PASS files=10
PREPACK_VALIDATION_PASS
files=126
bytes=2476559
forbidden=0
```

### 修改 3：重新打包

保留旧 v2 作为历史版本，生成：

```text
D:\program\LLM_FPGA\realFpga\deliverables\20260725_module16_v1\
16_lm_head_optional_20260725_v3.zip
```

使用：

```powershell
Compress-Archive `
  -LiteralPath <deliverable-root>\16_lm_head_optional `
  -DestinationPath <deliverable-root>\16_lm_head_optional_20260725_v3.zip `
  -CompressionLevel Optimal
```

### ZIP 归档级验证

执行：

```text
完整 ZipFile.testzip() CRC 检查
唯一根目录检查
工作目录与 ZIP 文件集合比较
126 个文件逐 SHA-256 内容比较
ZIP 内 README/manifest 语义断言
大文件、模型、缓存和禁入扩展名检查
```

结果：

```text
V3_ZIP_VALIDATION_PASS
entries=129
files=126
crc=PASS
sync=PASS
semantics=PASS
forbidden=0
V3_ZIP_VALIDATION_EXIT=0
```

最终大小：

```text
365895 bytes
```

最终 SHA-256：

```text
45E7974CD71CB0CC93B0B3CCC0A19C0D15BF293C7CD995D1476DAD40FAA8DE6A
```

### 结论

三项必须修正已全部完成。后续主提交应发送 `v3.zip`，不再发送 v2。独立大文件
附件内容和校验值未发生变化。

## 2026-08-28：AXU9EGB 可部署模型容量与新模型适配性核查（zb）

### 核查目的

根据当前 AXU9EGB 板卡、现有 Module 16 工程和已实测性能，区分以下三个问题：

1. 当前工程已经支持的整模型规模；
2. 现有数据通路可访问 DDR 的纯权重容量上限；
3. Qwen3.8-27B、Qwen3.8-Flash/Flash-Next 和 DeepSeek-V4-Flash 是否可在板上独立部署。

### 当前工程事实

- 当前工程仅实现 `LM Head + optional repetition penalty + argmax`，不是完整 Transformer
  推理运行时，因此当前“已支持的完整模型参数量”不能按 DDR 容量直接宣称。
- 当前 Vivado 实现使用 `10438 / 274080` LUT、`5 / 2520` DSP，资源占用低是因为
  内核采用小规模复用计算结构，不表示数百亿参数权重能够存入 PL。
- 当前 HLS `m_axi` 通过 PS 高性能端口访问 PS DDR；当前工程未接入板卡 PL 侧独立
  DDR4 控制器。
- 板卡物理上有 PS 侧 4 GB DDR4 和 PL 侧 2 GB DDR4；当前可直接用于本工程的模型
  数据空间是 PS 侧 4 GB，且还必须扣除固件、网络缓冲、激活、KV cache 和工作区。

### 纯容量理论值

按当前可访问的 4 GiB PS DDR、不扣除任何运行时开销计算：

| 权重格式 | 理论参数上限 |
|---|---:|
| FP16/BF16（2 byte/param） | 2.147B |
| INT8/FP8（1 byte/param） | 4.295B |
| INT4（0.5 byte/param） | 8.590B |

这些数值只是“所有 DDR 都装纯权重”的上限，并非可运行模型规格。实际还需量化 scale、
zero-point、对齐、激活、KV cache 和收发缓冲，因此工程目标应明显低于该表。当前内核只
支持 FP16 路径，也没有完整 INT8/INT4 Transformer 内核。

若后续重新设计 Vivado 工程并接入 PL 侧 2 GB DDR，物理总容量可达到 6 GiB，但 PS DDR
和 PL DDR 是两个独立存储系统，不能自动合并。即使按 6 GiB 全部存纯权重，理论上限也
只有 FP16 3.221B、INT8 6.442B、INT4 12.885B。

### 三个候选模型核查

- Qwen3.8-27B 是 27B dense 模型。FP8 官方仓库约 30.9 GB；INT4 纯权重理论值也约
  13.5 GB，均超过当前 4 GB 和板上物理 6 GB，不能在本板独立常驻部署。
- 精确名称 `Qwen3.8-Flash` 指云端生产服务；可下载评估的是开放权重
  `Qwen3.8-Flash-Next`。其主模型约 125B、每 token 激活约 6B，另有约 51B n-gram
  embeddings 和约 4B MTP。激活参数少只降低每 token 计算量，不代表其余专家权重不需
  存储，不能在本板独立部署。
- DeepSeek-V4-Flash 约 284B 总参数、每 token 激活约 13B；官方混合 FP4/FP8 仓库约
  167 GB。MoE 专家会随 token 路由变化，不能只保存 13B 激活参数，因此不能在本板独立
  部署。

### 仅替换 Module 16 时的规模估算

若 CPU/主机继续运行完整模型、FPGA 只承担 LM Head，则三者的 LM Head FP16 权重分别约：

| 模型 | LM Head shape | FP16 权重 | 按当前串行内核吞吐粗估 |
|---|---:|---:|---:|
| Qwen3.8-27B | `248320 x 5120` | 2.368 GiB | 103.6 s/token |
| Qwen3.8-Flash-Next | `248320 x 2560` | 1.184 GiB | 51.8 s/token |
| DeepSeek-V4-Flash | `129280 x 4096` | 0.986 GiB | 43.1 s/token |

上述仅是按当前 Qwen2.5-0.5B LM Head 实测约 `11.09 s/token` 等比例外推，不是完成适配
后的性能承诺。现有 HLS 最大 shape、协议字段、DDR 地址规划和权重加载流程均需修改；
Qwen3.8-27B 的 LM Head 单算子虽然理论上可装入 4 GB DDR，但剩余空间很紧，且当前速度
不具备实用性。

### 结论

- 当前工程的合理下一目标仍是先完成 Qwen2.5-0.5B 的整链路模块集成。
- 若建设完整板上运行时，比较稳妥的容量目标是 FP16 约 0.5B～1.5B，或在新增量化内核
  后尝试约 3B INT8；7B INT4 仅在纯权重容量上接近极限，运行时空间和性能风险很高。
- 三个候选大模型均不能以完整、独立常驻方式部署在当前 AXU9EGB；可以采用“主机运行
  大模型、FPGA 只卸载个别算子”的异构方案，但需要逐模型重做接口并评估是否值得。

## 2026-08-28：Orin 64 GB + AXU9EGB 异构推理技术路线分析（zb）

### 总体分工

- Orin 作为主控和主要推理设备：保存模型主体、运行 tokenizer/prefill/decode 循环、
  未卸载层、KV cache 与采样控制。
- AXU9EGB PS 作为网络和调度端：接收 TCP 请求、管理 PS DDR、执行 cache
  flush/invalidate、启动 HLS IP 并返回结果。
- AXU9EGB PL 作为算子加速端：执行权重已经常驻 DDR 的 LM Head 或后续融合算子。

### 当前最小可行路线

1. 在 Orin 上先运行 Qwen2.5-0.5B 手动 prefill/decode，保留 `past_key_values`。
2. 每个 step 在 final RMSNorm 后取得最后 token 的 FP16 hidden。
3. 复用现有 `orin_backend` 中 LMH1 客户端，通过持久 TCP 连接发送 `RUN_TOKEN`。
4. FPGA 执行 LM Head、可选 repetition penalty 和 greedy argmax，只回传 token/score，
   正式运行不请求完整 logits。
5. Orin 将 token 追加到序列，使用自身 KV cache 继续下一次 decode。
6. LM Head 权重只在板卡启动后用 `LOAD_WEIGHT` 上传一次；TCP 重连后通过 `PING`
   检查 DDR 中权重是否仍然有效，严禁每 token 重传权重。

### 千兆网边界判断

当前实测上传吞吐约 33.758 MiB/s。对 Qwen2.5-0.5B：hidden 仅 1792 bytes，历史
bitmap 约 18.5 KiB，若只返回 token，decode 单步网络数据很小；完整 FP16 logits 则约
304 KiB。因此 LM Head 是合理的网络切分边界，但当前 HLS 计算约 11.09 s/token，仍需
先做 PE/DSP/DDR burst 并行化才能讨论加速收益。

对 hidden=5120 的模型，单 token FP16 hidden 也只有 10 KiB；但是 2048-token prefill
hidden 单程约 20 MiB。若每一层或每个小算子都跨网，会把延迟和传输量乘以层数。因此
后续只能卸载连续融合层/融合 block，不能把 RMSNorm、RoPE、Residual 等小算子分别做
一次网络 RPC。

### 推荐卸载顺序

1. `final RMSNorm + LM Head + repetition penalty + argmax` 融合岛；
2. 优化为多 PE LM Head，并默认只返回 token；
3. 若需要 sampling，在 FPGA 内继续融合 temperature/top-k/top-p，避免回传完整 logits；
4. 再评估一个完整 Transformer block 或若干连续 block；相应层的 KV cache 应和 attention
   一起留在 FPGA，避免每 token 搬运 KV；
5. MoE 模型只在更后期研究“常驻热门专家 + Orin fallback”，不能把每 token 选中的专家
   权重临时经千兆网加载。

### 不推荐的切分

- 只卸载 RMSNorm、RoPE、SiLU、Residual 或单独 argmax：计算量太小，网络调度开销更大。
- 每 token 从 Orin 向 FPGA 流式传送权重：千兆网比 Orin LPDDR 带宽低多个数量级。
- attention 在 FPGA、KV cache 在 Orin：会形成持续的双向 KV 数据搬运。
- prefill 每层跨网：序列长度会放大边界 tensor，应让 prefill 暂留 Orin，优先卸载 decode，
  或一次卸载连续多层。

### 软件集成与验证阶段

- 阶段 O1：确认 Orin 型号、JetPack/CUDA、可用内存、功耗模式和网口；建立 Orin-only
  tokens/s、TTFT、显存/统一内存与功耗基线。
- 阶段 O2：不修改模型，先在 Orin 运行现有 8-step trace 客户端，完成 PING、一次权重上传、
  8-step、断线重连和 CRC 错误回归。
- 阶段 O3：实现 `FpgaLmHeadBackend`，接入手动 prefill/decode 循环；hidden 必须是 final
  RMSNorm 后、连续 little-endian FP16 数据。
- 阶段 O4：逐级比较 Orin GPU golden、FPGA raw logits、selected token、完整文本，并执行
  长时间稳定性与错误恢复测试。
- 阶段 O5：用端到端 tokens/s 判断是否保留卸载；单算子正确但整机变慢时不能称为加速。
- 阶段 O6：优化 HLS 并扩展协议的 capability/model hash/weight hash/session/op id；随后才考虑
  融合层和更高速互联。

### 模型适用性

- Qwen2.5-0.5B：适合作为第一条完整异构链路基线。
- Qwen3.8-27B：可考虑在 Orin 上使用 INT4/INT8 保存主体，仅将 LM Head 或融合尾部卸载；
  当前 Qwen2.5 固定 shape HLS 不能直接复用，且现有 LM Head 粗估约 103.6 s/token。
- Qwen3.8-Flash-Next、DeepSeek-V4-Flash：Orin 64 GB 也不能常驻完整权重；需要更大的
  GPU 服务器承担模型主体。Orin 只能作为前端/调度节点，不能因 MoE 激活参数较小就按
  6B 或 13B 估算存储。

## 2026-08-28：千兆以太网、NVLink 与 PCIe 5.0 比较（zb）

### 理论带宽口径

- 1GbE：每方向 1 Gbit/s，即理论 0.125 GB/s；当前 LMH1 权重上传实测约
  33.758 MiB/s（约 0.035 GB/s）。
- PCIe 5.0：32 GT/s/lane、128b/130b 编码；每方向理论约 x1 3.94 GB/s、x4
  15.75 GB/s、x8 31.51 GB/s、x16 63.02 GB/s，并且全双工。
- NVLink 必须注明代际和 GPU 总链路数；NVIDIA 公布的单 GPU 汇总双向带宽为
  NVLink 4 约 900 GB/s、NVLink 5 约 1800 GB/s、NVLink 6 约 3600 GB/s。该数值是
  GPU 专用互联的聚合指标，不能当作通用 FPGA 端口带宽。

### 语义与工程差异

- 以太网是可路由分组网络，使用 TCP/socket，部署和调试最简单，但软件栈、复制和协议
  处理使小请求延迟较高，也没有共享地址空间。
- PCIe 是主机 Root Complex 与 Endpoint 之间的本地总线，通过 BAR/MMIO、DMA、MSI/MSI-X
  工作。吞吐和延迟明显优于以太网，但需要 FPGA PCIe endpoint、DMA、Orin Linux 驱动、
  IOMMU/连续缓冲及链路恢复处理。
- NVLink 是 NVIDIA GPU/CPU-GPU 专用内存互联，适合 GPU P2P、模型并行和 collective；
  普通 AXU9EGB FPGA 不能作为 NVLink 设备，Jetson AGX Orin 也没有可用于连接本 FPGA 的
  外部 NVLink 接口。

### 当前硬件核查

- AXU9EGB 手册第 37 页确认板上有 PS、PL 各一路 10/100/1000 Mb/s RGMII 网口。
- 第 34 页的标准 M.2 是 PCIe x1、连接 PS MGT、用途为 NVMe SSD，不是 PCIe 5.0
  加速卡连接器。
- 第 41 页提供两路 SFP+，每路 GTH 收发速率最高 12.5 Gb/s；第 45 页 FMC HPC 提供
  8 对 GTH，可作为自定义高速接口/PCIe endpoint 的硬件出口。
- Jetson AGX Orin 对外最高为 PCIe Gen4，开发套件标准插槽为电气 x8；即使另一端是
  PCIe 5.0，链路也只能协商到双方共同支持的较低代际和宽度。

### 对当前项目的结论

1. 当前继续使用 1GbE 完成功能、协议和算子正确性验证。
2. 第一优先性能升级应评估板载 SFP+ 的 10GbE 路线；它保留网络协议和调试方式，改动
   小于 PCIe DMA 全栈重构。
3. 若目标是频繁搬运 prefill tensor、多个融合层或 FPGA 侧 KV cache，长期最合适的是经
   FMC 实现 PCIe endpoint/DMA；受 Orin Gen4 和 ZU9EG/板级通道限制，不可能得到
   PCIe 5.0 x16 的理论带宽。
4. NVLink 不属于这套 Orin + AXU9EGB 的可选互联，只适用于支持 NVLink 的 NVIDIA
   GPU/平台之间。
