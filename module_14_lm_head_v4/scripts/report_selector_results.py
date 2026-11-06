"""Create a readable P2 result from completed evidence; no model fitting."""
from pathlib import Path
import argparse,json,os
M=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('experiment',nargs='?',type=Path,default=M/'reports/selector_p2_20261021');args=ap.parse_args();out=args.experiment
    result=json.loads((out/'CALIBRATION.json').read_text(encoding='utf-8'))
    assert result['state']=='COMPLETE'
    rows=result['configurations'];assert len(rows)==result.get('expected_configuration_count',36)
    lines=['# v4 P2 软件筛选结果','',f"校准结论：**{result['quality_state']}**。不是v4硬件/板卡验收。",'',
        'v3.1 dense基线IP median=117.751830ms，等效lm_head吞吐约8.49 token/s。v4 FPGA ms/token、token/s和整体模型TTFT均未测。','',
        '候选精算的逐位正确性另见candidate_smoke报告。本表只评价在线可定义的路由/低秩候选是否覆盖penalty后的dense赢家；使用dense轨迹history，不等同自由生成任务质量。','',
        '| 配置 | decode步数 | 赢家召回 | 中文 | 英文 | 代码 | 数学 | 平均候选K | P95 K | 最大K | 逻辑MiB/步 | 初筛 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for r in rows:
        q=r['calibration']['decode'];c=r['candidates'];category=q['by_category']
        values=[r['name'],str(q['steps']),f"{q['recall']*100:.4f}%"]
        values += [f"{category[k]['recall']*100:.4f}%" if category[k]['recall'] is not None else '未测' for k in ('chinese','english','code','math')]
        values += [f"{c['mean']:.1f}",str(c['p95']),str(c['max']),f"{c['mean_logical_bytes']/2**20:.3f}",'达到拟议门槛' if r['preliminary_quality_gate'] else '未达到']
        lines.append('| '+' | '.join(values)+' |')
    lines += ['',f"校准选定：{result['chosen_calibration_configuration'] or '无可用配置；未打开holdout用于选型'}。",'',
        '门槛为规划中的初筛建议：decode整体和每类点估计均≥99.9%，不是已批准发布阈值。',
        '只在质量通过且平均逻辑字节低于dense后暂选配置，不代表实际时延最优；K/字节统计只使用decode步，选择与参数SHA在holdout之前锁定。',
        '逻辑字节包含BF16路由矩阵或低秩因子、候选ID和精算原权重；不含hidden/history、索引校验额外遍数、总线padding/burst、搬运调度。',
        '低秩K额外补特殊token，候选数量按K+specials上界计费；聚类按实际并集/回退K计费。组合表按route实际K+lowrank K上界计费，尚未扣重叠。',
        '表格和曲线的逻辑字节还未计入路由列表读取、合并候选表写回及preview/top-K scratch流量；不是完整selector成本或实际AXI流量。',
        'CPU拟合/质量计算时间不是在线selector耗时，不能据此计算FPGA加速倍数。',
        'prefill、decode分项、miss数、prompt bootstrap及整prompt匹配区间见CALIBRATION.json。',
        '数学/代码完整解题、自由生成分叉、罕见词与长上下文仍须另外验证。','']
    if (out/'ONLINE_CALIBRATION_AUDIT.json').exists():
        a=json.loads((out/'ONLINE_CALIBRATION_AUDIT.json').read_text(encoding='utf-8'));c=a['candidates']
        lines += ['## 实际候选生成复核（校准集）','',f"状态：{a['state']}。已实际执行无需dense标签输入的top-K与全局ID并集；召回与排名评估一致。",
            f"decode平均K={c['mean']:.2f}，P95={c['p95']}，最大={c['max']}；平均重叠去除{a['overlap_mean']:.2f}行。",
            f"候选精算连接复核{len(a['candidate_exact_head_cases'])}例：覆盖时token和score位一致；漏选时如实产生分叉。",
            'CPU FP32 BLAS / batch32，未来PL selector算术仍须独立验证。细节见ONLINE_CALIBRATION_AUDIT.json；CPU耗时不代表FPGA时延。','']
    if (out/'HOLDOUT.json').exists():
        h=json.loads((out/'HOLDOUT.json').read_text(encoding='utf-8'));q=h['report']
        lines += ['## 锁定方案holdout','',f"状态：{h['state']}；方案：{h['chosen']}。",f"独立问题组{q['prompt_groups']}；有效decode步{q['decode']['steps']}；召回{q['decode']['recall']*100:.4f}%；规模门槛达到={h['minimum_scale_met']}。",'发布验收、自由生成质量和FPGA性能仍未通过。','']
        lines += ['| 类别 | decode步数 | 漏选 | 召回 |','| --- | ---: | ---: | ---: |']
        for category,values in q['decode']['by_category'].items():
            lines.append(f"| {category} | {values['steps']} | {values['misses']} | {values['recall']*100:.4f}% |")
        lines += ['',f"完整prompt的decode轨迹均覆盖：{q['complete_prompt_decode_match']['all_steps_match_prompts']}/{q['complete_prompt_decode_match']['prompts']}。",
            '该项仍以dense轨迹为条件，不是实际自由生成任务得分或任意输入无损证明。','']
    (out/'RESULT.md').write_text('\n'.join(lines),encoding='utf-8')
    try:
        os.environ.setdefault('MPLCONFIGDIR',str(out/'.mplconfig'))
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(10,6))
        colors={'route':'#287568','lowrank':'#be7037','hybrid':'#526bb5'}
        for family,label,marker in [('route','Cluster routing','o'),('lowrank','Low-rank preview','s'),('hybrid','Routing UNION low-rank','^')]:
            group=[r for r in rows if r['family']==family]
            if not group:continue
            ax.scatter([r['candidates']['mean_logical_bytes']/2**20 for r in group],
                [r['calibration']['decode']['recall']*100 for r in group],c=colors[family],marker=marker,s=55,label=label,alpha=.8)
        ax.scatter([259.65625],[100],c='#65758b',marker='D',s=65,label='Dense reference label (weight bytes)')
        ax.axhline(99.9,color='#ad4a5b',linestyle='--',linewidth=1,label='Proposed calibration gate: 99.9%')
        ax.set_xscale('log');ax.set_xlabel('Logical selector + IDs + exact weight bytes / step (MiB)')
        ax.set_ylabel('Penalty-aware dense winner recall (%)')
        ax.set_title('Calibration only: quality vs logical bytes (not FPGA latency)')
        ax.grid(True,alpha=.2);ax.legend(loc='lower right',fontsize=9)
        fig.text(.01,.01,'Conditional on dense trajectories; no free-generation quality or FPGA speedup measured.',fontsize=9,color='#556070')
        fig.tight_layout(rect=[0,.035,1,1]);fig.savefig(out/'quality_bytes.svg');fig.savefig(out/'quality_bytes.png',dpi=150);plt.close(fig)
    except ImportError:print('P2_PLOT=NOT_RUN matplotlib unavailable')
    print('P2_READABLE_REPORT='+str(out/'RESULT.md'))
if __name__=='__main__':main()
