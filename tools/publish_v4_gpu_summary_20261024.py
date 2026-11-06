"""Publish only a completed independently audited GPU census; preserve history."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/gpu_summary_20261024_r1'
sys.path.insert(0,str(ROOT/'tools'))
from render_v4_validation import render
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    result=read(R/'RESULT.json');audit=read(R/'INDEPENDENT_REVIEW.json')
    assert audit['result_sha256']==sha(R/'RESULT.json')
    assert not (R/'ACTIVE.lock').exists()
    rows=result['configurations'];dense=next(p for p in rows if p['mode']=='dense')
    def quality(p):return p['quality']['decode']
    baseline_ids=['cluster_C128_R4_L16384','cluster_C256_R4_L16384','lowrank_r128_T16384','hybrid_C128_R4_L16384_r128_T16384','hybrid_C256_R4_L8192_r64_T16384','dense']
    highlights=[next(p for p in rows if p['id']==k) for k in baseline_ids]
    feasible=[p for p in rows if quality(p)['recall']>=.99 and all(c['recall']>=.99 for c in quality(p)['by_category'].values())]
    fastest=max(feasible,key=lambda p:p['equivalent_m14_per_s'])
    report=['# 实验1/8/9/10：统一GPU召回率—速度汇总','',f"完成：{result['completed']}。489个去重配置、58680次完整调用计时，另570次dense哨兵；1956组全候选ID/raw位/token/score/CRC证明和独立数组/计时/SHA复核通过。",'',
      '主图全部使用原320校准题/4775decode的召回率和本轮统一4夹具计时。质量与速度样本并非相同总体：速度只测中文/英文/代码/数学4个固定hidden/history，每配置每类3预热+30测量；不能视为1000题总体速度或整网decode/FPGA/TTFT。历史独立质量只在详情单列；没有新打开最终标签、调参、锁点或发布。','',
      '纵轴=120000/sum(120次wall_ms)，常驻BF16权重，PyTorch Eager固定FP32算术，预览分块32768行。每次完整重算路由/预览、候选并集、精算、policy和主机输出；无预览/候选缓存参与计时。CPU全词表raw缓存仅作为计时外逐位oracle，GPU仍每次只计算实际候选行。','',
      '| 配置 | 校准召回 | 漏选/decode | GPU M14 次/s | 相对同轮dense | K均值 |','|---|---:|---:|---:|---:|---:|']
    for p in highlights:
        q=quality(p);report.append(f"| {p['id']} | {q['recall']*100:.5f}% | {q['misses']}/{q['steps']} | {p['equivalent_m14_per_s']:.3f} | {p['equivalent_m14_per_s']/dense['equivalent_m14_per_s']:.3f}× | {p['candidate_decode']['mean']:.2f} |")
    q=quality(fastest);report+=['',f"仅作本轮描述性观察：整体及每类校准decode≥99%的配置共有{len(feasible)}个，实测最快是{fastest['id']}，{fastest['equivalent_m14_per_s']:.3f}次/s、校准召回{q['recall']*100:.5f}%。这不是新选型，也未在新独立组认证；不替代原实验10质量失败。",'',
      '图与表：doc/design/V4Validation.html#gpu-summary。同一配置合并实验归属；dense在实验筛选中作为共同控制。可按方案、实验、召回区间、类别和参数搜索，支持CSV。', '',
      '事实源：PLAN.json、RESULT.json、GPU_NUMERIC_PROOF.json、INDEPENDENT_REVIEW.json、timing/*.json；历史输入和冻结资产原样保留。无EDA/板卡作业。浏览器视觉检查与离线DOM逻辑检查分别记录。']
    (R/'RESULT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    # Renderer integration keeps this panel when any later journal renderer runs.
    journal_sha=sha(ROOT/'开发日志.html');render();assert sha(ROOT/'开发日志.html')==journal_sha
    p=ROOT/'AGENTS.md';source=p.read_text(encoding='utf-8')
    title='## 2026-10-24 实验1/8/9/10统一GPU汇总已完成（当前状态）'
    if title not in source:
        text=f'''{title}

- 有限入口benchmark_summary_20261024.py已完成并退出，ACTIVE.lock不存在；事实源module_14_lm_head_v4/reports/gpu_summary_20261024_r1/RESULT.json、INDEPENDENT_REVIEW.json、RESULT.md。489去重配置（23聚类/33低秩/432融合/1dense），1956组完整数值证明、58680次统一计时、570次交错dense哨兵完成，原覆盖数组/分项计数/全部原始计时/SHA独立复核PASS。下方进行中说明为历史，不重启已有入口。
- V4Validation.html在10组实验报告上方新增同轮召回率—GPU输出率交互图，全部主图横轴用原320校准题/4775decode；历史独立质量在点详情单列。每配置4原校准夹具、每类3预热+30测量；无新最终标签、调参、锁点或发布。旧实验速度保留，不混接旧轮次。
- 页面仅展示离线数据；CSV/摘要/原始证据可追溯。纵轴是M14 GPU Eager等效输出率，不是整网decode/FPGA/TTFT；原实验10质量失败和v3.1/v4/v4b冻结/封存结论不变。不连接/探测/操作FPGA，不恢复wb/luyou/心跳，不自动EDA或新实验。

'''
        source=source.replace('# FPGA 权重传输与续办\n','# FPGA 权重传输与续办\n\n'+text,1);p.write_text(source,encoding='utf-8')
    print(json.dumps(dict(state='PUBLISHED_COMPLETED_GPU_CENSUS',configurations=489,journal_unchanged=True,fastest_observed_cal99=fastest['id'],result_md=str(R/'RESULT.md')),ensure_ascii=False))
if __name__=='__main__':main()
