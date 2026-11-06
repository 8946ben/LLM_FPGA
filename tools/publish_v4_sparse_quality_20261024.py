"""Publish reviewed independent six-point quality; never reruns experiments."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';Q=M/'reports/sparse_quality_20261024_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    review=read(Q/'INDEPENDENT_REVIEW.json');assert review['state'].startswith('PASS')
    quality=read(Q/'QUALITY.json');bench=read(Q/'benchmark/RESULT.json');bm={p['id']:p for p in bench['configurations']}
    assert review['quality_sha256']==sha(Q/'QUALITY.json') and review['benchmark_sha256']==sha(Q/'benchmark/RESULT.json')
    lines=['# v4 全新独立1000题：冻结6配置质量与GPU参考速度','',f'完成：{bench["completed"]}。{quality["predictions"]}预测 / {quality["decode"]} decode / 1000问题 / 零排除。','', '| 配置 | decode漏选 | 整体召回 | 最低类别召回 | 99%整体及各类门槛 | 新4输入GPU M14次/s |','|---|---:|---:|---:|---|---:|']
    for row in quality['configurations']:
        q=row['report']['decode'];minimum=min(x['recall'] for x in q['by_category'].values());lines.append(f'| {row["id"]} | {q["misses"]}/{q["steps"]} | {q["recall"]*100:.5f}% | {minimum*100:.5f}% | {row["gate99"]} | {bm[row["id"]]["equivalent_m14_per_s"]:.2f} |')
    lines+=['','- 新集标签在六个配置、模型、数值规则和采集/评价入口冻结后打开；未调参、扩点或更换问题。','- 中文400：官方CMMLU；英文250：官方Dolly；代码100：官方DS-1000未用origin families；数学250：官方GSM8K未用train/test问题。原320校准集代码来源为MBPP，新旧组不是相同题目/完全相同分布。','- 参考输出为canonical BF16权重、FP32 H8/interleave16和penalty1.1下的dense轨迹；并非数据集答案标签。最多16预测，首预测不计decode。','- 质量保存每步hits/K/token/score/dense/候选SHA；24组四类完整CPU/GPU候选/raw证明及48组额外独立CPU重建通过。','- 新组GPU速度：从每类首个至少有2预测的问题取第1个decode hidden/history；预先声明规则。每配置3预热+每类30测量，共720次，另30dense哨兵。完整重算筛选、排序、合并、gather、BF16精算、policy和主机返回，常驻数据，PyTorch Eager。排除H2D、加载、Transformer、prefill、TTFT。','- 纵轴与质量总体不同：四固定输入的重复速度不等于1000题全部decode总体速度；不代表整网decode或FPGA。旧557点GPU轮次、输入与速度保留，不将二者速度变化直接归因为方法变更。','- 99%允许部分步骤漏选，不保证闭环生成或任务准确率99%。整题一致率与统计区间另见QUALITY.json。','- 不回改旧实验10原99.9%失败结论，不将新门槛追溯为旧认证。新硬件/FPGA均NOT_RUN。','','## 来源与证据','', '- [CMMLU](https://github.com/haonan-li/CMMLU)','- [Dolly](https://github.com/databrickslabs/dolly)','- [DS-1000](https://github.com/xlang-ai/DS-1000)','- [GSM8K](https://github.com/openai/grade-school-math)','- 新组版本/许可/抽样/9份历史分组排除：../../data/sparse_quality_20261024/MANIFEST.json；原公开源锁：../../data/public_corpus_v1/sources.lock.json；DS-1000锁：../../../module_14_lm_head_v4b/data/final_quality_20261023/raw/ds1000/SOURCE_LOCK.json。','- 本轮SELECTION_LOCK.json / QUALITY.json / benchmark/PLAN.json / benchmark/RESULT.json / INDEPENDENT_REVIEW.json。','- 页面：doc/design/V4Validation.html#gpu-summary，新独立集与原校准集标签切换。']
    lines+=['','## GPU轮次可比性补充','', '- 原四校准输入在本轮六配置方式下重测，共720次＋30dense哨兵，候选K与历史完全一致；稀疏方法绝对速率仍明显高于原557点轮次，而dense基本接近。因此新旧速度差不能单独归因于新数据或算法。具体运行条件原因尚未定位，不作硬件收益推断。','- 页面默认保留旧557点历史速度；勾选“两组共同6配置”时，旧集使用本轮原输入重测速度，新集使用本轮新输入速度。质量始终分别来自原320校准数组和新1000独立数组，不混用。','- 证据：TIMING_COMPARABILITY_REVIEW.json、benchmark_calibration_control/DERIVATION.json、PLAN.json、RESULT.json。对照RESULT的report字段沿用新质量元数据，不是再次测得的校准质量；配对图从原校准事实源单独取横轴。']
    (Q/'RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (Q/'RESULT.json').write_text(json.dumps(dict(state='COMPLETE_FRESH1000_SIX_CONFIG_QUALITY_AND_GPU',quality_sha256=sha(Q/'QUALITY.json'),benchmark_sha256=sha(Q/'benchmark/RESULT.json'),review_sha256=sha(Q/'INDEPENDENT_REVIEW.json'),retuning=False,passed_configurations=[r['id'] for r in quality['configurations'] if r['gate99']=='PASS'],board='NOT_RUN',eda='NOT_RUN'),indent=2)+'\n',encoding='utf-8')
    import render_v4_validation
    render_v4_validation.render()
    print('PUBLISHED_FRESH_AND_CALIBRATION_TABS',flush=True)
if __name__=='__main__':main()
