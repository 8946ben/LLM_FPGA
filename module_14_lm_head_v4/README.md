# lm_head v4 · 动态候选词表（离线实施中）

v3.1 已完成 PL DDR dense 迁移与真实板测，作为本轮基线保留。
本轮在独立目录实施 P2 软件筛选与 P3 候选精算，目标是降低 lm_head 每 token 耗时、提高等效 decode token/s。
当前已有 v4 实验 bit/XSA 和完整系统离线实现审计，匹配BSP/两个A53 ELF和内部离线包已完成，尚无板测或正式交付；不修改 v2/v3/v3.1 封存资产，不操作板卡。

## 当前：统一selector与PL DDR系统集成

用户已恢复v4离线工作。真正父级selector完成C仿真6正确/24预检拒绝/5运行错误、HLS综合和私有IP冻结；
32项host测试、25项PS fake-MMIO测试及寄存器映射审计通过。结构与调用合同见[集成说明](SELECTOR_INTEGRATION.md)。
新BD中两条64位数据AXI都只访问MIG PL DDR；完整系统综合、布局布线、STA/CDC/DRC及bit-XSA审计已完成，
200MHz WNS+0.652ns、WHS+0.010ns，CDC严重项0、MIG警告0。DRC仍有816 Warning/211 Advisory，不宣称零警告。
详见[完整系统实现报告](reports/board_v4_20261021/HARDWARE_RESULT_R2.md)，该结论不能替代RTL功能或板卡验收。
完整CoSim r2的原HLS包装流程因生成testbench同名块冲突FAIL；局部修复仅改仿真块名称，原失败与修改SHA均保留。
2026-10-22已完成完整RTL的41943040内存值/18标量比较、原C postcheck及冻结证据审计，整链离线资格PASS；原始HLS包装FAIL保留。
当前真实状态以[PROGRESS.json](PROGRESS.json)及[续办记录](../doc/LM_HEAD_V4_HANDOFF_20261021.md)为准；不操作板卡。
私有生产arena和M4AR loader/测试ELF已准备，目标PL DDR回读和实际运行仍NOT_RUN。

2026-10-22：新增私有M4AR arena loader及主机上传器，宿主C检查/13项Python（mock socket）通过；
PS计时程序与M4PT文件解析器8项测试及只读历史BSP语法预检通过，最终匹配BSP/两个ELF已真实构建并通过独立ELF布局审计。
4类真实C参考生产arena均已生成并通过本机预检，目标加载均NOT_RUN。
本轮资格/软件构建流程已exit0；新GPU独立质量流程另见下文；内部工作区包位于`reports/board_v4_20261021/private_package_r1/`，
独立复核报告为`reports/resume_20261022/PRIVATE_PACKAGE_VALIDATION.json`。不是正式ZIP或板卡验收。
板卡控制/GEM DMA停机交接脚本和新算术独立质量点门槛评估均已完成，真实硬件行为与工程验收仍未测。用户明确暂不上板，继续离线准备。

## 2026-10-22 性能评估与下一阶段

| 指标 | 已核对结果 | 边界 |
| --- | ---: | --- |
| v3.1输出等效率 | 8.4924/s | 实板IP median117.751830ms，30次 |
| v4整链RTL换算 | 29.2984/s | 单正确中文debug样例6826306拍/34.131530ms@200MHz，未板测 |
| 精算行减少 | 85.8302% | K21529/V151936，筛选开销另计 |

跨证据时间之比3.4499不等于实测加速；生产median/P95、A53同边界与整体LLM TTFT尚待测量。
详见[性能评估](reports/PERFORMANCE_ASSESSMENT_20261022.md)。

下一阶段已开始：上板入口`standalone/private_board.py`默认仅本机计划，13项host/Tk Tcl模拟测试通过；
读回停用GEM3之前不替换ELF，真实硬件仍NOT_RUN。当前有效计划为`reports/board_preparation_20261022/plan_chinese_r2/`。
新独立质量1000问题（中400/英250/代码100/数学250）与历次保留组规范化哈希无重叠；配置/语料/入口均在标签前冻结。
HumanEval固定官方提交和许可证/数据SHA已保留，未执行数据集代码。点门槛不等于无损或正式发布。
新GPU流程已exit0，1000问题/14958 decode/零排除：聚类80漏选（99.4652%）、低秩356（97.6200%）、混合1（99.9933%）。混合通过预先拟议整体及分项99.9%点门槛；不等于无损、15958步完整RTL回放或自由生成质量。结果见`reports/fixed_quality_20261022/RESULT.json`，历史质量失败和CPU r2b结果保留，互不替代。
新候选数均值29300.93、中位28183/P9541630/最大56075，高于旧RTL单例；不能将29.30/s推广到总体。
K17071/28184/41630/56075四组CPU精算与dense token/score bits/CRC一致，四份320MiB生产arena及本机预检、未发送的计时请求就绪。详见[候选规模性能用例](reports/performance_cases_20261022/README.md)。当前上板CLI仅支持原四类夹具，新用例campaign绑定仍待扩展；本轮全部流程已结束，没有后台GPU/EDA工作。
用户已明确“暂不上板，继续离线准备”；本轮没有板卡连接/探测/操作。后续先做新规模campaign及多步/debug/错误路径离线准备，实际板测须新的独占安排。

## 历史离线阶段（低秩/路由与C链）

低秩与路由独立核均已通过CSim、HLS与3事务RTL；修复路由r1在RTL中的同字节位图丢位。
四类完整C链的候选ID、全部候选raw logits、dense token/score/CRC通过。
同校准集4775 decode的新固定顺序模型漏选数仍为15/84/0，但不是新独立质量认证。
该历史组件阶段未做P&R/整链RTL/系统STA；后续完整系统与RTL结论见上方当前状态，板上decode/TTFT仍未测。
详见[阶段报告](reports/SELECTOR_ARITHMETIC_STAGE_20261021.md)与[算术/接口说明](HLS_SELECTOR_ARITHMETIC.md)。
该阶段自有作业当时已结束。下方保留此前阶段历史成果。

## 当前可验证成果

- `reference/numeric_contract.py` 原样复制自已验收 v3.1 交付的参考模型，保留 BF16/FP32 H8、16 槽交错和相邻 lane 规约顺序。
- `reference/candidate_head.py` 先按全局 ID gather 原始行，再精算；不先计算全词表后裁输出。
- 8 步真实 canonical trace × 6 组候选 = 48 组回归通过，包含全词表、随机非连续 2K/4K/8K/16K、边界 ID。
  raw 与 penalty 后分数逐位一致；全候选时 token/score/CRC 及完整 logits SHA 与 dense 一致。
- 数据格式、重复/越界/空表/长度/版本检查、global history 与 tie-break、跳过行 NaN 检测范围有独立测试。
  聚类路由、质量分项、校准失败不打开holdout、稳定top-K与Windows共享锁恢复等检查也已加入（23项测试）。
- 四类公开 prompt 已固定作者来源版本和 SHA；训练 1500、校准 320、holdout 1000，按完整问题分组，不按相邻 token 拆分。
- GPU 逐位 head 在 8 步完整 logits/processed score SHA 对照通过；四类试采及独立CPU标签复核通过；正式训练采集1500 prompt/22433 decode步、校准320 prompt/4775 decode步通过。
- 首轮36组聚类/低秩配置均未达到拟议分项门槛，保留完整失败结果。第二轮42组组合扫描选定3路聚类（每路最多16384）与rank64/top8192并集，校准decode召回99.9581%，漏选2步。
- 实际在线候选生成无需dense标签输入，已在全部5095个校准预测步复核。decode平均K20390.12/P95 29010/最大43721；18个候选精算连接样本通过预期行为检查，其中2个漏选样本如实分叉。
- 锁定方案holdout已完成：1000个独立问题、14970 decode步，召回99.8464%，漏选23步（中文15、英文7、代码1、数学0）。**QUALITY_FAIL：不推进v4发布**。979/1000问题的dense decode轨迹每步均被覆盖；不代表自由生成质量。
- 数据/参数/代码/选择锁的独立审计PASS；不能用审计PASS覆盖质量失败。全部采集/评估进程已退出。
- **后续保守对照r2b**：4路聚类（每路最多16384）∪rank128/top16384，先冻结再测新1000个独立问题，与v1所有问题组无精确重叠。14969 decode仅1次中文漏选，召回99.9933%，拟议P2召回门槛PASS；不能称为无损或正式发布通过。
- G:工具盘已恢复，2021.1启动验证通过。独立候选HLS内核C仿真17组真实数值/13类非法/4项特殊路径PASS；HLS估计3.830ns，最终独立OOC结论以reports/OFFLINE_STAGE_RESULT_20261021.json为准。
- 新增有界scratch的radix top-K算法参考，与完整稳定排序独立比较通过；host测试共26项。后续独立HLS实现见下一条，完整selector全成本仍须另测。
- 后续已完成独立top-K/并集HLS：8精确/10非法C仿真与3事务Verilog/XSim协同仿真PASS；HLS估计3.650ns、64 BRAM18K/0DSP。真实英文preview用例的RTL模型耗时3.66449ms，非板测，不含低秩投影和候选精算。本核尚无P&R，详见reports/TOPK_STAGE_RESULT_20261021.md。

**软件候选覆盖验证不是FPGA稀疏加速或整体LLM decode实测。**
随机候选仅为精算测试夹具，不能当作筛选算法；CPU/GPU 计时不代表 FPGA 时延。

## 离线运行

工具自带 Python 可运行 NumPy 精算测试；本机系统 Python 另有 CUDA/PyTorch/Transformers，供 hidden 采集。

```powershell
cd D:\program\LLM_FPGA\module_14_lm_head_v4
python -m unittest discover -s tests -v
python scripts\freeze_baseline.py
python scripts\smoke_candidates.py
python scripts\prepare_public_corpus.py --verify-only
# 需要联网的首次数据准备：不加 --verify-only；使用作者官方固定提交，下载只读数据，不执行数据脚本。
python scripts\prepare_model.py
# 仅在具备 CUDA 和完整推理依赖的 Python 中运行：
python scripts\collect_hidden.py --split train --out data\hidden_v1 --max-new-tokens 16
python scripts\collect_hidden.py --split calibration --out data\hidden_v1 --max-new-tokens 16
python scripts\collect_hidden.py --split holdout --out data\hidden_v1 --max-new-tokens 16
# 拟合与校准（只读train/calibration，不先看holdout）：
python scripts\evaluate_selectors.py
# 仅在校准选型通过后，以锁定配置评估holdout，不重跑拟合/校准：
python scripts\evaluate_selectors.py --holdout-only
python scripts\report_selector_results.py
# 第二轮：复用首轮train拟合参数，只在calibration比较互补并集：
python scripts\evaluate_hybrid_selectors.py
python scripts\audit_online_selector.py
# 全部holdout采集完成、选型已冻结后仅评一次：
python scripts\evaluate_hybrid_selectors.py --holdout-only
python scripts\report_selector_results.py reports\selector_hybrid_p2_20261021
python scripts\validate_p2_bundle.py
# 保守对照r2b：需具备Transformers的Python准备输入长度过滤和GPU采集。
python scripts\prepare_fresh_holdout.py --token-filter
python scripts\prepare_r2_collector.py --revision r2b
python scripts\evaluate_conservative_r2.py
python scripts\collect_hidden_r2b.py --split holdout --max-new-tokens 16
# 仅在锁定和采集完成后评估一次；当前已存在的结果禁止重复评估：
python scripts\evaluate_conservative_r2.py --evaluate
# 候选内核离线复现与契约见HLS_CANDIDATE.md。
```

采集可在 prompt 边界停止：在输出目录创建 `STOP_REQUESTED`；已完成的每个 prompt 有 NPZ SHA 和 JSON 身份，
只有模型/语料/精度/脚本/设置一致才恢复。正式采集前先用 `--limit-per-category 1` 独立目录试跑。
已实际完成的四类试采位于`data/hidden_pilot_v2/calibration/`，并经独立CPU复核16步标签；
GPU head在8步完整golden上逐位通过，不把GPU采集吞吐写成FPGA性能。
每条记录保存 BF16 hidden、raw top-256 全局 ID、penalty 后 dense 赢家、输入与生成 token，可重建 history。
prefill 首个预测步和 decode 后续步数量分开统计；不把采集吞吐当作 FPGA 性能。
语料/模型版本和本轮已保存hidden均绑定SHA；跨GPU或推理库版本重新采集Transformer hidden不保证逐位相同，
应形成新的数据版本，不能只因prompt相同就混用原选型结论。

## 公开语料与划分

实际版本、SHA、URL：`data/public_corpus_v1/sources.lock.json`；划分：`MANIFEST.json` 和三个 JSONL。

| 方向 | 作者公开来源 | 实际取用 |
| --- | --- | --- |
| 中文 | [CMMLU](https://github.com/haonan-li/CMMLU) | dev 用于训练；test 按问题哈希进一步隔离校准与 holdout |
| 英文指令 | [Databricks Dolly](https://github.com/databrickslabs/dolly) | 作者迁移 HF 前的固定历史提交；不冒称与当前 HF 修订相同 |
| Python 代码 | [Google MBPP](https://github.com/google-research/google-research/tree/master/mbpp) | 保留官方 task ID train/validation/test 分区；不执行题目代码 |
| 数学 | [OpenAI GSM8K](https://github.com/openai/grade-school-math) | 官方 train 内分训练/校准，test 留作 holdout；答案不放入 prompt |

只做 NFKC/大小写/空白标准化后的精确重复与完整问题分组，**未做语义/模板近重复检测**；
模型预训练污染未知。现有语料不是罕见词、长上下文或 penalty 极端场景的充分覆盖，需要另补压力集。
保留上游 README/LICENSE，来源各自许可独立，不从代码许可证推断数据许可，也不把混合数据统一宣称为一个许可。

## 候选软件契约（非已冻结硬件 ABI）

候选表实验格式：16 B 小端 `<4sHHII>`：`M4ID`、版本1、元素4 B、K、完整词表 V，后接 K 个递增且唯一的 uint32 全局 ID。
表必须非空、K≤V、ID<V；非法输入报错，不静默裁剪、去重或回退到 PS DDR。
原行地址为 `weight_base + global_id * 1792`，不是读取权重前 K 行。
policy 用全局 ID 查 history；相同 score 取较小全局 ID。

稀疏调试结果只写 K 个 `(uint32 global_id, float32 raw_score)`，每项8 B。
`candidate_records_crc32` 只校验这些记录，不能冒充完整 logits CRC；生产 token/score CRC 仍单独计算。
未选行不输出、不补零；跳过行的 NaN/Inf 或运行期内存损坏不会被本次候选精算发现。

## 下一道门槛

首轮组合方案的1000问题holdout失败，证据保留，未用其继续调参；摘要见reports/P2_SUMMARY_20261021.md。
r2b改用更保守预算并预留新问题组，已达到拟议点估计召回门槛。它和首轮使用不同测试问题，不能当作同测试集收益。
r2初版输入长度预检有2条超过2048token，304条采集记录已暂停保留且不用于选型/统计；r2b先按固定输入长度规则过滤，再冻结和从头采集，未读输出标签决定替换。
当前阶段结果见reports/OFFLINE_STAGE_RESULT_20261021.md/json，独立质量原始数据在reports/conservative_r2b_20261021/HOLDOUT.json。
报告 penalty 后赢家召回、分项结果、候选平均/P95/最大。当前逻辑字节只包括中心/低秩因子、候选ID及精算权重，
尚未计路由列表读取、并集写回、preview/top-K scratch、history/control、总线padding和burst，不能冒充selector全成本或加速倍数。
现有 99.9% 是规划中的初筛建议，尚未批准为发布阈值；高召回不等于任意输入无损，点估计不代表置信下界达到同一门槛。
独立候选读取/精算及top-K/并集HLS已实现；低秩投影/路由HLS、完整selector质量、PL DDR系统集成、200MHz实现和重新安排后的板测仍在后续阶段。
候选IP点积行周期159，gather模型190~191；全部候选模式数学相同但吞吐未必等同原dense路径，后续需保留dense回退。
“上游直接提供权重”仍等待负责人框架文档，本轮不加外部流端口。
