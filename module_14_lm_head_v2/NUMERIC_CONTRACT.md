# M14 V2 数值合同（2026-10-09）

本合同冻结当前独立模块已有 C++/RTL 的运算顺序，reference 修正为与其逐位一致。
合同标识：`bf16_rne_h8_interleave16_fp32_adjacent_tree_v2`。
这是 reference/golden 的版本更新，硬件 ABI、build_config、bitstream 均未改变。
整体框架的公共 V2 ABI 仍需在集成阶段另行统一。

## 点积顺序

BF16 little-endian bits 左移 16 位解释为 FP32；生产 hidden=896，8 lane、112 word。
对每个 lane 的 16 个 accumulator 置 +0。按 word=0..111 顺序执行：

```text
slot = word & 15
product = fp32(hidden[word*8+lane] * weight[token*896+word*8+lane])
partial[lane][slot] = fp32(partial[lane][slot] + product)
```

每次乘法和加法分别舍入为 FP32，软件 reference 不融合乘加。对每个 lane 的
16 个 partial，依次按距离 8、4、2、1 合并，每次加法后舍入：

```text
for width in [8,4,2,1]:
    for i in range(width): partial[i] = fp32(partial[i] + partial[i+width])
```

最后 8 路 lane sum 必须按相邻路合并：

```text
sum01 = fp32(lane0 + lane1); sum23 = fp32(lane2 + lane3)
sum45 = fp32(lane4 + lane5); sum67 = fp32(lane6 + lane7)
raw = fp32(fp32(sum01 + sum23) + fp32(sum45 + sum67))
```

旧 Python 最后按距离 4、2、1 合并 lane，虽然数学等价，FP32 舍入并不等价。
构造 `[2^24,1,-2^24,1,0,0,0,0]` 时，正确树输出 1，旧树输出 2；第二个 token
分数 1.5 时甚至改变 top-1。Python 和 HLS testbench 均增加此回归。

## Penalty、argmax 与 CRC

可选 logits 保存 **penalty 前** FP32 raw bits。history bitmap 为 little-endian uint32，
token 的 bit 为 `history[token>>5] >> (token&31)` 的最低位。
penalty 参数先转 FP32；seen 且 raw<0 时 FP32 乘 penalty，否则 FP32 除 penalty；
未出现 token 保留 raw。penalty 启用时必须有限且 ≥1；非有限结果返回 NUMERIC_ERROR。
逐 token 扫描，只有严格大于当前最大分数才更新，平分选择较小 token。

CRC32 覆盖 `<uint32 token, uint32 selected_score_bits>` 的 8 个 little-endian byte。
保留严格 CRC/score-bit/logits SHA256 校验，误差统计只用于诊断，不能替代通过条件。
数值承诺针对当前正常、有限 BF16 trace；极端输入、subnormal 与其他浮点 IP 版本
不能仅从这次归档比对推断已完成验证。

## 修正证据与 golden 迁移

`scripts/diagnose_reduction.py` 仅替换最终 lane tree，未修改任何输入或板上数据。
归档 step_00 的 151,936 个 raw logits 全部 exact，相同 SHA256 为
`d7ada7553c6ff9bc48899776732e8269ca791874363cf64cc17a4aebe1245acc`；
token=104198、score_bits=1101012901、CRC=2154663276 与板上匹配。
完整统计位于 `reports/numeric_20261009/reduction_diagnosis.json`。

修正全部 8-step golden 前，旧 manifest/raw/processed/result 保存至
`reports/numeric_20261009/legacy_golden/`；hidden/history/weight 的原始 bits 与 SHA256
不变。新资产从修正后的 reference 重新计算，禁止直接拷贝板上 logits 作为 golden。
8-step 离线 token 不变仍不能替代 8-step 实板验收。

2026-10-10 新实板 8-step 生产/debug、全 raw logits SHA256、score bits/CRC 已逐项
通过，详见 `reports/20261010_BOARD_ACCEPTANCE.md`。权重/输入与归约合同未改变。
