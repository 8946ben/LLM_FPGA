# 阶段 B：LM Head Vivado IP 导出报告

> 日期：2026-07-24  
> 结论：完成  
> 本阶段没有下载或修改真实开发板。

## 最终产物

IP Repository：

```text
module16_lm_head_hls/build/lm_head_export/solution1/impl/ip
```

关键文件：

```text
component.xml
xilinx_com_hls_lm_head_argmax_1_0.zip
drivers/lm_head_argmax_v1_0/
hdl/verilog/lm_head_argmax.v
```

最终摘要：

```text
D5B518DDB45B96E5AFAE078F2332B283D99C6C51F536077E364A654944772E64  xilinx_com_hls_lm_head_argmax_1_0.zip
0DFF90C8F6D2DB53B447729D0D20200AB505904260F4A812A6CABFF1F9EC85D9  component.xml
```

## Vivado Catalog 验收

```text
LMH_IP_VERIFY=PASS
LMH_IP_VLNV=xilinx.com:hls:lm_head_argmax:1.0
LMH_IP_NAME=lm_head_argmax
LMH_IP_VERSION=1.0
```

## 接口

```text
s_axi_control
m_axi_gmem_hidden
m_axi_gmem_weight
m_axi_gmem_history
m_axi_gmem_logits
ap_clk
ap_rst_n
```

四个 m_axi 当前均为 32-bit 数据宽度。第一次上板保持不变，后续性能阶段再评估扩宽。

## 可重复执行命令

由于 Vitis HLS 2021.1 在 2026 年存在 `core_revision` signed 32-bit 溢出，使用兼容入口：

```powershell
module16_lm_head_hls\run_export_ip_2021_compat.ps1
```

不要仅依据 `vitis_hls.bat` 的退出码判断成功；该版本可能在内部 IP 打包失败时仍返回 0。兼容脚本还会检查 `component.xml` 是否实际生成。

## 详细故障与修复

见：

```text
realFpga/DEBUG_LOG.md
```
