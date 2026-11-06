# lm_head v3 交付身份

发布名：lm_head v3；版本：M14_V3_20261019_r1；负责人张本；拟接收人喻燕萍。
ABI=2；HLS top=lm_head_v2；IP VLNV=user.org:llm_fpga:lm_head_v2:2.1；build_config=0x20c08011。

v3来自已通过板测的200 MHz规约分层实现。计算源码、驱动、bit/XSA/ELF/PS init
按SHA256绑定；重命名和交付打包阶段未重新综合或连接板卡。
原v2的100 MHz生产源码、用户修改的交付文档与ZIP均保留。

待接收的候选包未发送。本轮仅独立M14；未把整体LLM集成列为当前工作要求。
规范快照保留，未验证边界见README与interface/interface_contract.json。
