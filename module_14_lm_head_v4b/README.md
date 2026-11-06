# lm_head v4b · 量化方向并行研究

工程父版本为已上板通过的 **v3.1**，与候选稀疏化 **v4** 并行。用户于2026-10-23授权开展离线实验。基线8步完整raw/policy、四类夹具、32格式packing边界、5095校准token/score bits复现、32点RTN＋4GPTQ＋4AWQ-style及12个预筛K点校准、720次真实packed GPU计时已完成。

已按校准门槛与读取量锁定直接W12/G896/非对称、W4/G128预筛＋K512精算，并于2026-10-23 17:34完成同一全新1000题的一次性评估：15948预测、14948decode、零排除。直接W12错选3次（中文2、英文1），decode一致率99.9799%；W4预筛＋BF16精算零漏选且输出一致。两点整体及各类decode均通过99.9%门槛，独立来源/数组/计时复核PASS。这是固定dense轨迹的条件一致性，不是闭环生成或无损证明。新v4b Csim/HLS/RTL/系统实现/板测仍NOT_RUN。

一次性父流程及GPU子进程已退出，ACTIVE.lock已清除，无自动后续EDA。最终标签已打开；reservation/ENTRY里的false仅是锁定时的历史事实，不得在本组调参再认证。

- [最终报告](reports/quantization_20261023_r1/RESULT.md)
- [最终质量与逐类计数](reports/quantization_20261023_r1/FINAL_QUALITY.json)
- [独立复核](reports/quantization_20261023_r1/FINAL_INDEPENDENT_REVIEW.json)

- [本轮执行状态](reports/quantization_20261023_r1/PROGRESS.json)
- [执行计划与入口锁](reports/quantization_20261023_r1/ENTRY_LOCK.json)
- [v3.1数值复现](reports/quantization_20261023_r1/Q01_BASELINE.json)

首轮入口scripts/run_quantization.py（preflight、rtn手动阶段）与run_calibrated_methods.py；后续run_quality_sequence.ps1这一有限流程已完成。历史PID和暂停步骤不再表示作业进行中，不重启最终评估。没有wb/luyou/心跳或EDA/板卡下阶段。

- [交互实验页](../doc/design/V4bValidation.html)
- [论文综述与16篇原文](../doc/paper/lm_head_quantization/README.md)
- [机器可读实验计划](experiments/quantization_study/PLAN.json)
- [基线来源与校验](baseline/SOURCE_LOCK.json)

baseline/v31 保存原源码/头、原验收报告和身份清单的小型逐字节快照。它是只读参考，不是可发布v4b内核。新量化kernel、descriptor、VLNV、build tag、CSR/layout均待分配，不复制旧bit/XSA/ELF或继承旧资格。v4仅提供只读模型身份，不作为v4b工程父版本。

首轮顺序：基线算术复现 → 32点RTN边界 → 8个新GPTQ/AWQ点与4控制 → 量化预筛12点与3控制 → packed/GPU/硬件成本 → 锁点后全新问题质量 → 新Csim/HLS/RTL/200MHz → 等待独占板测安排。W8A8、残差、码本/旋转按条件推进，不自动扩扫。

Qwen tie_word_embeddings=true；整网评估须克隆独立输出层，保留输入embedding BF16。本轮采集核验了输入embedding与canonical W的字节身份。旧train/calibration及最终问题/评估入口均已冻结，两个研究候选通过本轮质量门槛，尚无生产发布资格。当前用户授权覆盖离线实验，不连接/探测/操作板卡，不启用wb/luyou/心跳。后续融合另立实验。
