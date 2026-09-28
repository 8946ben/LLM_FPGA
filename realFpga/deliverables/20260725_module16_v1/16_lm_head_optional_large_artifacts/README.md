# Module 16 大文件附件包

生成日期：2026-07-25  
整理人：zb

此附件与面向 GitHub 的：

```text
16_lm_head_optional_20260725_v2.zip
```

配套使用。主提交包只包含必要源码、IP repository、报告和说明；本附件单独保存
不适合直接提交 GitHub 的大文件。

## 内容

```text
vivado_project/lm_head_axu9eg/
  完整 Vivado 2021.1 生成工程，包括 .xpr、Block Design、cache、gen、
  ip_user_files、runs、DCP、reports、journal 和 bitstream。

bitstream/lm_head_system_wrapper.bit
  从已通过真实 AXU9EGB 验收的 impl_1 目录单独复制的 bitstream。
  该文件在完整 Vivado 工程中也存在；这里单独保留是为了便于直接取用。

trace/qwen25_0p5b_instruct_full_generation_trace/
  当前 Module 16 验证使用的完整 trace 原始目录，包括 prefill、7 个 decode
  step、generation processed scores、metadata、name mapping，以及原目录内
  已存在的 flightllm_test_demo。
```

## 原始内容统计

```text
完整 Vivado 工程：1147 files，321561882 bytes
独立 bitstream：1 file，26510907 bytes
完整 trace：7732 files，302147718 bytes
```

独立 bitstream 与 Vivado 工程中的同名文件内容相同，因此附件包的逻辑内容会
有约 26.5 MB 重复；这是有意保留的便捷取用副本。

## 环境

```text
板卡：ALINX AXU9EGB
FPGA：xczu9eg-ffvb1156-2-i
Vivado：2021.1
PL 时钟：100 MHz
HLS AXI-Lite base：0xA0000000
板卡服务：192.168.8.190:19016 / TCP LMH1
```

Vivado 工程包含机器生成的路径和缓存。换电脑打开时，可能需要重新指定 HLS IP
repository，并让 Vivado Upgrade/Regenerate IP。可移植重建 Tcl 和 HLS IP
位于主提交包，不应只依赖此生成工程。

## 关键文件 SHA-256

```text
lm_head_system_wrapper.bit
53BAE4015574E8C01535CE5089BB9FB41FE2C81E8FF94EB9D03B1F6DA4F420DC

lm_head_axu9eg.xpr
E5C0B95D9CED17815BF74CBCE7D5A00681F1314D6E30946290286A15B31C10CF

lm_head_system.bd
6F18D6B30DA27258591F31ED3A69D0BC313843BEB81DE58B5825345CAC906C88

trace/metadata.json
43DE0B21EA6F6F5303CCEA4C858E42D871F9651C46619730F902BF6E182560D6
```

压缩包本身的大小和 SHA-256 记录在项目 `realFpga/DEBUG_LOG.md` 的对应打包条目
中。

