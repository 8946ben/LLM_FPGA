# vitis_ps

本目录包含 Cortex-A53 standalone/lwIP 板端服务。它接收 LMH1 TCP 帧，将权重
和输入写入 PS DDR，通过 HLS driver 启动 IP，并把 token、score 和可选完整
logits 返回上位机。

## 主要文件

```text
src/lwip_lm_head_raw_server.c  LMH1 协议、DDR/cache、HLS 调度
src/lmh_buffers.h              full-size buffer 尺寸与 linker symbol
src/lscript.ld                 约 260 MiB 权重及其他 buffer 的 DDR 保留区
src/main.c                     平台、DDR、网口启动和轮询
patches/xemacpsif_physpeed.c   AXU9EGB PHY speed 协商兼容替换文件
scripts/                       platform/app 创建、构建、下载和 JTAG 检查
```

## DDR 与 cache

链接脚本为 weight、hidden、history、logits 和 network RX 预留互不重叠且
64-byte 对齐的 DDR 区域。关键大小：

```text
weight          272269312 bytes
hidden               1792 bytes
history bitmap      18992 bytes
raw logits         303872 bytes
network RX        1048576 bytes
```

CPU 写入 hidden/weight/history 后调用 `Xil_DCacheFlushRange`；IP 写回 logits
后调用 `Xil_DCacheInvalidateRange`。HLS driver 设置四个 64-bit DDR 地址、
shape、开关和 penalty，调用 `Start` 并轮询 `IsDone`。

## BSP PHY 补丁

AXU9EGB 板载网口与 Vitis 2021.1 `lwip211_v1_5` 默认 PHY speed 文件不兼容。
生成 BSP 后，用：

```text
patches/xemacpsif_physpeed.c
```

替换：

```text
<workspace>/<platform>/psu_cortexa53_0/standalone_psu_cortexa53_0/
bsp/psu_cortexa53_0/libsrc/lwip211_v1_5/src/contrib/ports/xilinx/
netif/xemacpsif_physpeed.c
```

然后重新生成/编译 BSP 与应用。未替换时可能出现板卡重启后网口无法建立、
`192.168.8.190` ping 不通。

## 构建与下载

先由 Vivado 导出 XSA，再使用 `scripts/` 中的 Tcl 创建 platform 和 application。
脚本原始验证环境路径位于 `D:\program\LLM_FPGA\realFpga`，移入其他 workspace
时需修改脚本开头的路径变量。

预构建 `.xsa`、`.bit` 和 `.elf` 因目标仓库 `.gitignore` 规则不在提交包中。

