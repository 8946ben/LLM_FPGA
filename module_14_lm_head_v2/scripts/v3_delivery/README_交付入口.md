# lm_head v3 · 200 MHz 交付入口

版本：`M14_V3_20261019_r1`；负责人：张本；日期：2026-10-19。

先阅读 `module_14_lm_head_v3/README.md`。本包包含源码、可综合 IP、PS 驱动、
接口字段表、资源/时序报告、匹配 bit/XSA/ELF/PS init、完整 BF16 权重、
8 步输入/golden，以及 100/200 MHz 同板验收的原始证据。

200 MHz 独立 Decode 板测通过：IP median/P95 为 117.751805/117.751890 ms，
相对原 lm_head v2 的同板100 MHz基线，速度为1.90968倍，延迟降低47.635%。
8步完整 logits 逐位一致，30次独立计时和1000次连续调用通过。

`lm_head v3` 是本次发布名称；接口 ABI=2，HLS top=`lm_head_v2`，
IP VLNV=`user.org:llm_fpga:lm_head_v2:2.1`，build_config=`0x20c08011`。
这些身份与已测试镜像一致，源文件/API 名称保留技术兼容性。

在包根目录执行：

```powershell
python -B .\module_14_lm_head_v3\scripts\run_tests.py
```

本命令只做离线完整性与证据复核。上板加载命令见模块 README。
文件总清单为根目录和模块内的 `SHA256SUMS`；压缩文件校验值在外层 `ZIP_SHA256SUMS.txt`。
交付说明见 `交付说明.md`，两份规范快照位于 `specifications/`。
尚未向接收人发送。本包验证范围为独立 M14，整体 LLM 集成不在本轮范围。
