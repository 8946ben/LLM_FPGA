"""Publish reviewed supplementary557; preserve the first-six self-contained page."""
from pathlib import Path
import collections,hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/sparse_quality_all557_20261024_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    review=read(R/'INDEPENDENT_REVIEW.json');assert review['state'].startswith('PASS_ALL557')
    quality=read(R/'QUALITY.json');bench=read(R/'benchmark/RESULT.json')
    assert review['quality_sha256']==sha(R/'QUALITY.json') and review['benchmark_sha256']==sha(R/'benchmark/RESULT.json')
    current=ROOT/'doc/design/V4Validation.html';snapshot=current.with_name('V4Validation_first6_20261024.html')
    if not snapshot.exists():
        prior=read(M/'reports/sparse_quality_20261024_r1/PAGE_REVIEW.json');assert sha(current)==prior['page_sha256'],'Do not archive an unexpected page revision'
        snapshot.write_bytes(current.read_bytes())
    modes=collections.Counter(p['mode'] for p in quality['configurations']);passed=collections.Counter(p['mode'] for p in quality['configurations'] if p['gate99']=='PASS')
    sparse_pass=collections.Counter(p['mode'] for p in quality['configurations'] if p['gate99']=='PASS' and p['candidate_decode']['min']<151936 and p['fallback_decode']==0 and p['mode']!='dense')
    historical=read(M/'reports/sparse_methods_20261024_r1/benchmark/RESULT.json')
    old_pass=collections.Counter(p['mode'] for p in historical['configurations'] if p['quality']['decode']['recall']>=.99 and all(v['recall']>=.99 for v in p['quality']['decode']['by_category'].values()))
    names=dict(cluster='仅聚类',lowrank='仅低秩',hybrid='融合',partial='部分通道',affinity='完整倒排桶',learned='学习桶路由',lsh='LSH',dense='dense')
    lines=['# 全557配置：新1000题补充质量与新旧配对GPU测速','',f'完成：{bench["completed"]}。全部557配置ID/参数与原校准图一致，新1000题15956预测/14956decode，零排除。','', '| 方法 | 配置数 | 原校准整体及各类≥99% | 新组整体及各类≥99% | 新组其中非始终全词表且无dense回退 |','|---|---:|---:|---:|---:|']
    for mode,n in modes.items():lines.append(f'| {names[mode]} | {n} | {old_pass[mode]} | {passed[mode]} | {sparse_pass[mode]} |')
    lines+=['','- 复用已打开的同一新1000题，没有重新采集或调整参数。后追加551点为补充分析，不能重新命名为独立最终认证；首轮标签前冻结六点的hits/K逐步完全复现，原产物与页面另存。','- 原校准图和新组图都557点，同一配置ID可按名称/方案/实验/类别筛选；可仅看首轮六点。两组都采用本轮全部557配置驻留、8固定输入交错测速，分别汇总各120次/配置；原557轮及首轮六配置速度仍保留为历史。','- 质量缓存是实际候选位图/并集/K，仅用于未计时评价。全部133680计时调用完整重算筛选、排序、并集、gather、BF16精算、penalty与主机返回，不读取缓存候选或预览。另660 dense哨兵。','- 4456组八输入CPU/GPU完整候选ID/raw bits/token/score/CRC证明；独立复核全部557数组、分项门槛和全部原始计时；另8个decode状态重建4456配置候选并核对hits/K。','- 横轴为对应数据集完整decode召回，纵轴仅四固定输入GPU M14等效输出率；不是整批语料速度、整网decode、TTFT或FPGA预测。','- 全词表端点、dense回退和真稀疏路径区别报告；上表最后一列只是排除始终全词表/回退，不能据此推断硬件收益。','- 原校准代码来自MBPP，新组代码来自DS-1000；新旧质量差同时包含抽样与来源分布变化。官网、冻结提交、来源文件SHA/许可、划分/去重和prompt规则在图下分别列出。','- 观察边界是本样本描述，不宣称全局最优或闭环任务质量；原实验10失败、v3.1/v4/v4b冻结资产均不改变。新板卡/EDA均NOT_RUN。','','## 事实源','', '- PLAN.json / QUALITY.json / CACHE.json / coverage/*.npz','- benchmark/PLAN.json / GPU_NUMERIC_PROOF.json / timing/*.json / RESULT.json','- INDEPENDENT_REVIEW.json / cohorts/old与new/TIMING_SUMMARY.json / SUMMARY.csv','- doc/design/V4Validation.html#gpu-summary；首轮页面存档doc/design/V4Validation_first6_20261024.html。']
    (R/'RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (R/'RESULT.json').write_text(json.dumps(dict(state='COMPLETE_ALL557_SUPPLEMENTARY_QUALITY_AND_PAIRED_GPU',completed=bench['completed'],quality_sha256=sha(R/'QUALITY.json'),benchmark_sha256=sha(R/'benchmark/RESULT.json'),review_sha256=sha(R/'INDEPENDENT_REVIEW.json'),mode_counts=dict(modes),gate99_pass_counts=dict(passed),nonfull_no_fallback_pass_counts=dict(sparse_pass),first_six_snapshot_sha256=sha(snapshot),board='NOT_RUN',eda='NOT_RUN'),indent=2)+'\n',encoding='utf-8')
    import render_v4_validation
    render_v4_validation.render();print('ALL557_PAIRED_COHORT_PAGE_PUBLISHED',flush=True)
if __name__=='__main__':main()
