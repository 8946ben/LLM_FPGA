# lm_head v3 发布与交付（2026-10-19）

用户将已通过真实板测的200 MHz独立M14版本命名为 **lm_head v3**。
发布名称对应：ABI=2、HLS top=`lm_head_v2`、IP VLNV=`user.org:llm_fpga:lm_head_v2:2.1`、
build_config=`0x20c08011`。保留已验收计算源码与镜像字节，交付目录使用`module_14_lm_head_v3`。
工作区正式200 MHz实现仍在`module_14_lm_head_v2/experiments/board200_20261019/`；
原模块根目录100 MHz源码及原v2交付包保留。

交付文件夹：`deliverables/20261019_M14_V3_r1/M14_V3_20261019_r1/`。
压缩包：同级`M14_V3_20261019_r1.zip`；936文件，278245732 bytes。
ZIP SHA256：`a411ad6f181f653cd6bcc692427f72fc4bfa388a7d7c7c7cc5ccafcb4eb261a2`。
入口：`README_交付入口.md`；交付负责人张本，拟接收人喻燕萍，尚未发送。

包内包含源码、完整IP、驱动、机器接口表、HLS/布线/RTL/数值报告、匹配的bit/XSA/PS init/ELF、
canonical BF16权重、8步输入与golden、两版本同板110份原始mailbox及logits、规范快照与provenance。
204个IP引用和68寄存器、11项Python回归、资产完整性、原始mailbox与两份55项campaign复核通过；
Vivado2021.1目录识别IP2.1；压缩前与独立解压后的离线校验PASS。

实板结果：IP median/P95=117.751805/117.751890 ms，A53 median=117.767348 ms；
相对同板v2/100 MHz速度1.9096779倍，延迟降低47.635148%；8步完整logits逐位一致、
30次独立计时与1000次连续调用通过。范围为独立M14 H896/V151936 Decode/penalty ON。
详细实测见`module_14_lm_head_v2/reports/board200_20261019/RESULT.md`。

本次命名/日志/交付操作仅访问本地文件，未重新上板。用户明确板卡当前由另一agent使用，
本任务不进行JTAG连接/读取、网络探测、初始化、加载或验收，也不查询当前板卡状态。
后续接收人使用包内上板命令需自行安排独占板卡；历史验收不表示当前现场仍是该镜像。

修改包内文档后应重新生成根/模块SHA256清单，并重新压缩及计算ZIP SHA256；保留原实测镜像身份。
