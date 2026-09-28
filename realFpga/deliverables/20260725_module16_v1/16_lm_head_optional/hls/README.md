# hls

本目录包含可综合的 HLS 内核、头文件、testbench 和构建脚本。

```text
src/lm_head_kernel.cpp       顶层实现与 AXI pragma
include/lm_head_kernel.hpp   shape 上限和函数签名
tb/lm_head_tb.cpp            synthetic penalty 用例与真实 trace 对比
run_csim.tcl                 全尺寸 8-step C 仿真
run_csynth.tcl               AXU9EGB HLS 综合
run_cosim.tcl                4x4 同构接口 RTL co-simulation
run_export_ip.tcl            Vivado IP 导出
run_export_ip_2021_compat.ps1  Vitis HLS 2021.1 core_revision 兼容入口
```

生产配置为 hidden size 896、vocab size 151936；`LMH_COSIM_SMALL` 只用于将
RTL 联合仿真的 AXI 存储镜像缩小到 4x4，数据通路、控制寄存器和 penalty/argmax
语义不变。

`run_csim.tcl` 期望本模块根目录下存在：

```text
artifacts/model.embed_tokens.weight.fp16.npy
artifacts/module16_hls_fixtures/
```

工具脚本见 `../tests/`。综合目标是 `xczu9eg-ffvb1156-2-i`，HLS 目标周期为
5 ns。真实 Vivado Block Design 以 100 MHz 驱动该 IP。

