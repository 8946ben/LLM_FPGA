"""Collect real candidate HLS/OOC and fresh-test evidence, keeping gates distinct."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,re,sys,xml.etree.ElementTree as ET
M=Path(__file__).resolve().parents[1];sys.path.insert(0,str(M))
from reference.quality_data import load_split,assert_group_disjoint
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    reports=M/'reports';sources=read(reports/'HLS_CANDIDATE_SOURCE_MANIFEST.json')
    for name,digest in sources['files'].items():assert sha(M/name)==digest
    csim=(reports/sources['csim_log'].removeprefix('reports/')).read_text(encoding='utf-8')
    cases=re.search(r'M14_V4_CSIM=PASS exact_cases=(\d+) invalid_cases=(\d+) special_cases=(\d+)',csim);assert cases
    xml=ET.parse(M/sources['csynth_report']);resources=xml.find('.//AreaEstimates/Resources')
    hls=dict(state='PASS',clock_target_ns=float(xml.findtext('.//TargetClockPeriod')),estimated_ns=float(xml.findtext('.//EstimatedClockPeriod')),
        resources={x.tag:int(x.text) for x in resources},csim_cases=dict(zip(['exact','invalid','special'],map(int,cases.groups()))),
        dot_row_cycles=159,gather_row_cycles_range=[190,191],scope='Candidate exact-head only, selector not included; HLS estimate is not physical timing')
    fresh=M/'data/fresh_holdout_r2b_20261021';out=reports/'conservative_r2b_20261021';q=read(out/'HOLDOUT.json');lock=read(out/'SELECTION_LOCK.json')
    assert q['selection_lock_sha256']==sha(out/'SELECTION_LOCK.json')
    assert lock['evaluator_sha256']==sha(M/'scripts/evaluate_conservative_r2.py')
    assert lock['base_evaluator_sha256']==sha(M/'scripts/evaluate_selectors.py') and lock['quality_data_sha256']==sha(M/'reference/quality_data.py')
    assert lock['fresh_corpus_sha256']==sha(fresh/'holdout.jsonl')==read(fresh/'MANIFEST.json')['holdout_sha256']
    assert lock['prior_calibration_sha256']==sha(reports/'selector_hybrid_p2_20261021/CALIBRATION.json')
    for n,d in lock['parameter_sha256'].items():assert sha(reports/'selector_p2_20261021'/n)==d
    train=load_split(M/'data/hidden_v1/train');cal=load_split(M/'data/hidden_v1/calibration');test=load_split(M/'data/hidden_r2b_20261021/holdout')
    assert_group_disjoint(train,cal,test);assert test['manifest_sha256']==q['holdout_manifest_sha256']
    rows=[json.loads(s) for s in (fresh/'holdout.jsonl').read_text(encoding='utf-8').splitlines()];lookup={r['id']:r for r in rows}
    for r in test['manifest']['records']:
        assert r['group_sha256']==lookup[r['id']]['group_sha256'] and r['prompt_sha256']==lookup[r['id']]['prompt_sha256']
    ooc=M/'build/candidate_ooc_clocked_r2';timing=(ooc/'timing_summary.rpt').read_text(encoding='utf-8');check=(ooc/'check_timing.rpt').read_text(encoding='utf-8')
    assert (ooc/'routed.dcp').exists()
    lines=timing.splitlines();i=next(i for i,line in enumerate(lines) if line.strip().startswith('WNS(ns)'))
    values=lines[i+2].split();wns,tns,whs,ths,wpws=map(float,[values[j] for j in (0,1,4,5,8)])
    checks={name:int(n) for name,n in re.findall(r'checking (\w+) \((\d+)\)',check)}
    physical_pass=wns>=0 and whs>=0 and wpws>=0 and tns==0 and ths==0 and all(checks.get(k)==0 for k in ('no_clock','unconstrained_internal_endpoints','loops'))
    physical=dict(state='OOC_INTERNAL_TIMING_PASS' if physical_pass else 'OOC_TIMING_FAIL',clock_ns=5,setup_uncertainty_ns=.2,hold_uncertainty_ns=.05,
        wns_ns=wns,tns_ns=tns,whs_ns=whs,ths_ns=ths,wpws_ns=wpws,check_timing=checks,
        reference_clock_source='HD.CLK_SRC=BUFGCE_X0Y0 on ap_clk (OOC assumption, not board placement)',
        scope='Standalone candidate IP internal paths only; external AXI/PS/PL-DDR, CDC, selector and board are not verified')
    result=dict(updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),provenance='PASS',hls=hls,physical=physical,
        selector_quality=q['state'],selector_report=q['report'],chosen=q['chosen'],candidate_count_upper_bound=q['candidates'],
        fresh_counts=read(fresh/'MANIFEST.json')['counts'],hardware_access='NONE',v4_release='NOT_ACCEPTED',
        remaining=['实现PL低秩预筛、top-K与并集HLS，并核算全部开销','在新问题组验证自由生成、较长轨迹、罕见词和penalty压力','集成完整PL DDR系统，验证200MHz STA与CDC','重新确认板卡独占后执行真实数值、性能和稳定性验收'])
    (reports/'OFFLINE_STAGE_RESULT_20261021.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# v4 候选内核与保守筛选：离线阶段结果','',f"质量初筛：**{q['state']}**；独立IP内部时序：**{physical['state']}**；正式v4验收仍未完成。",'',
        '本轮未操作板卡。上轮99.8464%的失败证据保留，未重复用其holdout调参；本轮另预留问题组。','',
        '## 新测试集与召回','',f"方案：{q['chosen']}。训练参数复用原train；在原校准零漏选的较大预算配置上建立保守对照，未宣称扩大训练已经完成。",
        f"新测试独立问题组{q['report']['prompt_groups']}，decode步{q['report']['decode']['steps']}，漏选{q['report']['decode']['misses']}，召回{q['report']['decode']['recall']*100:.4f}%。",'',
        '| 类别 | decode步 | 漏选 | 召回 |','| --- | ---: | ---: | ---: |']
    for c,v in q['report']['decode']['by_category'].items():lines.append(f"| {c} | {v['steps']} | {v['misses']} | {v['recall']*100:.4f}% |")
    lines += ['',f"完整dense decode轨迹全部步被覆盖：{q['report']['complete_prompt_decode_match']['all_steps_match_prompts']}/{q['report']['prompt_groups']}；仍不是自由生成任务得分或无损保证。",
        '初筛为总体和每类≥99.9%的点估计，尚非批准的发布容忍度。候选K按路由实际K加lowrank K上界计费，不冒称实际去重K。',
        'r2初版输入预检有2条超过2048token；先暂停保留304条记录，在不查看输出标签的情况下建立r2b输入过滤修订集，重新冻结配置并从头采集。r2暂停数据未用于拟合、选型或本轮计数。','',
        '## 候选精算与时序','',f"C仿真：真实数值{cases.group(1)}组、非法输入{cases.group(2)}类、特殊路径{cases.group(3)}项PASS，包含全词表完整raw分数逐位对照。",
        f"HLS估计{hls['estimated_ns']:.3f}ns；OOC 5ns约束：WNS={wns:.3f}ns，WHS={whs:.3f}ns，WPWS={wpws:.3f}ns。",
        'OOC仅覆盖独立候选IP内部路径，外部I/O时序未作板级约束，不包括selector、PS/PL-DDR互联或CDC。当前没有RTL协同仿真或v4板测。',
        'dot每行159拍，gather模型190~191拍。需要实测selector+topK+union+gather+精算+policy全成本，不能按151936/K计算吞吐。',
        '旧版工具日期版本号溢出已仅在本轮生成脚本局部修复，源码/安装/系统时间和v3.1封存不改。','',
        '## 下一步','',*[f'{i+1}. {x}' for i,x in enumerate(result['remaining'])],'',
        '详见OFFLINE_STAGE_RESULT_20261021.json、HLS_CANDIDATE.md及conservative_r2b_20261021/HOLDOUT.json。']
    (reports/'OFFLINE_STAGE_RESULT_20261021.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('OFFLINE_STAGE_PROVENANCE=PASS QUALITY='+q['state']+' PHYSICAL='+physical['state'])
if __name__=='__main__':main()
