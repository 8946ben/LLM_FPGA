# vivado

本目录用 Tcl 重建 AXU9EGB/ZU9EG Block Design，不提交生成工程和 bitstream。

## 关键连接

```text
PS M_AXI_HPM0_FPD
  -> axi_smc_ctrl
  -> lm_head_argmax/s_axi_control

lm_head_argmax 的 4 个 m_axi
  -> axi_smc_mem（4 SI / 1 MI）
  -> PS S_AXI_HP0_FPD
  -> PS DDR
```

AXI-Lite 地址：

```text
lm_head_argmax = 0xA0000000
range          = 0x00010000
```

PL 时钟使用 PS `pl_clk0=100 MHz`。复位连接是本工程真实上板成功的必要条件：

```text
PS pl_resetn0 -> proc_sys_reset/ext_reset_in
const 1       -> proc_sys_reset/aux_reset_in
const 1       -> proc_sys_reset/dcm_locked
const 0       -> proc_sys_reset/mb_debug_sys_rst
interconnect_aresetn -> 两个 SmartConnect
peripheral_aresetn   -> HLS ap_rst_n
```

`aux_reset_in` 不能接常量 0：该实例 `C_AUX_RESET_HIGH=0`，常量 0 会一直断言
辅助复位，使 AXI 与 HLS IP 保持复位状态。

## 重建

先把 `../ip_repo` 作为 IP repository，再在 Vivado 2021.1 Tcl Shell 中运行：

```tcl
source create_lm_head_axu9eg_bd.tcl
source build_lm_head_axu9eg.tcl
```

`verify_lm_head_ip.tcl` 检查 IP 可见性；其余 inspect/compare Tcl 用于核对 PS 与
reset 属性。实现报告见 `../reports/vivado/`。

