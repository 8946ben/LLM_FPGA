# v4 selector 后续实现草案

## 当前实现边界（2026-10-21 后续实施）

已有四个独立实验top：`lm_head_v4_router`、`lm_head_v4_lowrank`、
`lm_head_v4_topk_union`、`lm_head_v4_candidate`。它们还不是一个已集成/发布的IP，
没有v4 bit/XSA/ELF、板卡profile或完整系统200MHz签核。
router和lowrank新增数值合同见`../HLS_SELECTOR_ARITHMETIC.md`。
其中lowrank先将B无损转置为128×896，A保留151936×128；所有参数仍来自冻结文件，未重新拟合。

原CPU BLAS质量结论不直接继承给PL算术。新固定顺序模型已在同一校准集复核：
4775 decode步中聚类/低秩/混合仍为15/84/0漏选；这是校准算术审计，不是新独立holdout、完整RTL或板测。
已打开的r2b不用于为新实现重新选参数或认证泛化。

rank128对每步需要`896*128+151936*128=19562496`次乘加，BF16因子共39124992字节。
当前选型实际使用4路候选表（每路最多16384 ID）与低秩top16384并集；预算加大后的正确性要先测，
不把候选K、乘加数或逻辑字节比直接折算成token/s。

## top-K采用有界scratch的候选方案

1. 按global ID顺序生成151936个penalty后preview FP32分数并写PL DDR。
2. 4轮8-bit radix直方图逐步确定第K大分数的32-bit阈值。每轮256个计数，保留选中前缀，整表顺序扫描。
3. 最后一轮按global ID升序扫描，选择大于阈值的行及阈值相等时较小ID，直至恰好K。
4. 与路由候选合并成递增唯一的global ID表，写完payload与K/header后再启动精算。

浮点单调位序键：正数翻转符号位，负数按位取反；-0/+0必须先统一为+0，保持数值相同分数的ID tie规则。
NaN/Inf先拒绝，不能混入排序键。`reference/radix_topk.py`是算法参考；
`src/lm_head_v4_topk.cpp`已完成独立CSim/HLS与3事务RTL协同仿真，尚无本核P&R。

单份preview存储为607744B；4轮直方图加最终输出扫描读取3038720B，合计最少3646464B score scratch流量。
还需另计路由列表读取、并集bitset/表写回、候选ID验证两遍、hidden/history、读写padding和AXI transaction开销。
这不是实际总线或时延测量。当前256-bin直方图用4个bank、II=2，每次4分数；不能宣称II=1。

当前独立HLS采用151936-bit位图并集（原始位空间18992B），有BRAM端口/初始化/扫描开销。
router按最近4簇读取排名列表，加入14个mandatory ID；选中空簇时显式输出整个词表并设置fallback，仍读取PL DDR原权重，不回退PS DDR。
所有计算数据仍按PL DDR范围规划，A53加载缓冲可以PS DDR；不添加上游直供流端口。

端到端计时必须覆盖`route + lowrank + topK + union + exact + policy + schedule`，从hidden可用到token/score可用。
独立候选IP时序、P2点估计召回、完整系统板测和生成任务质量应分别报告。
