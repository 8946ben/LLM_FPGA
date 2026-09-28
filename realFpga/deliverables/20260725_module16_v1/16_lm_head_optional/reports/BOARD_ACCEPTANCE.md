# AXU9EGB 真实板卡验收

验收日期：2026-07-25  
执行人：zb  
板卡：ALINX AXU9EGB / XCZU9EG-2FFVB1156I  
网络：`192.168.8.190:19016`，TCP LMH1  
PL 时钟：100 MHz

## 构建结果

```text
HLS target period       5.000 ns
HLS estimated period    3.650 ns
HLS max latency         1097890446 cycles / 5.489 s at 200 MHz estimate
HLS resources           BRAM_18K 14, DSP 5, FF 4880, LUT 5816

Vivado WNS              3.921 ns
Vivado TNS              0
Vivado CLB LUTs         10438 / 274080 (3.81%)
Vivado CLB registers    15607 / 548160 (2.85%)
Vivado Block RAM tiles  6 / 912 (0.66%)
Vivado DSPs             5 / 2520 (0.20%)
Timing constraints      MET
```

## 软件与网络

```text
Weight shape       [151936, 896]
Weight dtype       FP16 little-endian
Weight bytes       272269312
Upload time        7.692 s
Upload throughput  33.758 MiB/s
```

板端 lwIP 服务已验证权重跨 TCP 重连保持在 DDR。每次 RUN_TOKEN 均通过 HLS
driver 设置地址、shape、write_logits、penalty 开关与数值，并完成 cache
flush/invalidate。

## 默认 repetition penalty OFF

标准客户端不带 `--enable-repetition-penalty`，step 0..7：

| Step | Expected/actual token | Raw max abs | FPGA seconds | Result |
| ---: | --- | ---: | ---: | --- |
| 0 | 104198 / 104198 | 0.015625 | 11.0900220 | PASS |
| 1 | 48 / 48 | 0.01171875 | 11.0886199 | PASS |
| 2 | 16948 / 16948 | 0.0078125 | 11.0899902 | PASS |
| 3 | 3837 / 3837 | 0.015625 | 11.0903150 | PASS |
| 4 | 67071 / 67071 | 0.01171875 | 11.0894621 | PASS |
| 5 | 102661 / 102661 | 0.015625 | 11.0875152 | PASS |
| 6 | 99718 / 99718 | 0.0078125 | 11.0937842 | PASS |
| 7 | 100013 / 100013 | 0.0078125 | 11.0916765 | PASS |

汇总：

```text
generated IDs       8/8 PASS
raw logits atol     8/8 PASS (threshold 0.02)
raw Top-5           8/8 PASS
server score        8/8 PASS
mean FPGA time      11.0901731 s/token
worst raw max abs   0.015625
```

step 2 的 token 16948 已在历史中：

```text
penalty OFF selected_score = 30.046875
penalty ON  selected_score = 27.315340042114258
30.046875 / 1.1 ~= 27.31534
```

这证明默认 OFF 测试确实把 `enable_repetition_penalty=0` 传到硬件，并非只修改
CPU golden。

## 显式 repetition penalty ON

使用 `--enable-repetition-penalty --repetition-penalty 1.1`：

```text
processed scores    8/8 PASS
processed Top-5     8/8 PASS
generated IDs       8/8 PASS
worst max abs       0.015625
```

当前 trace 的 raw Top-1 与 processed Top-1 恰好相同，所以 penalty 的验收同时
检查完整 processed scores 和专门构造的 Top-1 改变用例。

## 稳定性

完整 8-step、多次 TCP 重连和 full logits 回传后：

```text
ping 10/10, packet loss 0%
Cortex-A53 #0 Running
PS/PMU/PL/PSU/APU JTAG targets visible
weight metadata still [896, 151936, 272269312]
```

## 本地已验证但未随 GitHub 包提交的产物

目标仓库忽略以下扩展名，因此这里只记录内部验收校验值：

```text
lm_head_system_wrapper.bit
SHA-256 53BAE4015574E8C01535CE5089BB9FB41FE2C81E8FF94EB9D03B1F6DA4F420DC

lm_head_axu9eg.xsa
SHA-256 F06E0DD687AED3ABC0A28530C030E2ECAD8324C93D19134A8210FA085F94402F

lm_head_net_diag.elf
SHA-256 84288B93D9A68BD008486C2EC407622AE55AE3FD7B387C07C7AB86A259D9307F
```

