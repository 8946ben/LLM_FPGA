# lm_head v3 验收复现

已完成的2026-10-19真实板测见 `reports/board200_20261019/RESULT.md`。
使用匹配的200 MHz镜像/PS init/test ELF/TCP loader，完整BF16加载和DDR/sentinel检查通过后，
执行模块README中的 `standalone/run_acceptance.ps1`。

每版本55项：8步生产、8步完整logits、1受控错误golden、4错误路径、3预热、30独立计时、
1组1000连续调用。raw logits用SHA256严格比较；top1/score bits/CRC与golden一致。
连续调用只在mailbox保留最后一次IP计数，不能当作1000份独立延迟样本。

离线审阅 `campaign_portable.json` 与原始 mailbox 的逐字段一致性，由 `scripts/run_tests.py` 验证。
它只复核已有证据，不表示新运行了一次板测。修改后的源码或镜像需重新上板验收。
