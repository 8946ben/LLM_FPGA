"""Freeze and summarize completed top-K/union Csim, HLS and RTL cosim evidence."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,re,xml.etree.ElementTree as ET
M=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    reports=M/'reports';fixture=json.loads((reports/'topk_fixture_20261021/MANIFEST.json').read_text())
    for row in fixture['rows']:
        for name,digest in row['files'].items():assert sha(reports/'topk_fixture_20261021'/name)==digest
    assert fixture['fixture_source_sha256']==sha(M/'scripts/prepare_topk_fixtures.py')
    csim=(reports/'hls_topk_csim_r3_20261021.log').read_text(encoding='utf-8');assert 'M14_V4_TOPK_CSIM=PASS exact_cases=8 invalid_cases=10' in csim
    log=(reports/'hls_topk_cosim_r1_20261021.log').read_text(encoding='utf-8');assert 'C/RTL co-simulation finished: PASS' in log and 'M14_V4_TOPK_cosim=PASS' in log
    cosim=M/'build/topk_cosim_r1/hls/solution1';x=ET.parse(cosim/'syn/report/lm_head_v4_topk_union_csynth.xml')
    summary=(cosim/'sim/report/lm_head_v4_topk_union_cosim.rpt').read_text();assert re.search(r'\|\s*Verilog\|\s*Pass\|',summary)
    transactions=(cosim/'sim/report/verilog/result.transaction.rpt').read_text()
    values=[(int(i),int(latency)) for i,latency in re.findall(r'transaction\s+(\d+):\s+(\d+)',transactions)];assert len(values)==3
    names=['real_english_valid','repeated_signed_zero_valid','late_nan_error_exit']
    files=['src/lm_head_v4_topk.cpp','include/lm_head_v4_topk.hpp','tests/topk_csim.cpp','tests/topk_cosim.cpp','hls_topk.tcl','reference/radix_topk.py','scripts/prepare_topk_fixtures.py']
    result=dict(updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),state='TOPK_CSIM_CSYNTH_RTL_COSIM_PASS',
        scope='Only policy-preview top-K + routed-ID union. Lowrank/route projection arithmetic, board/full-selector acceptance not covered.',
        clock_target_ns=float(x.findtext('.//TargetClockPeriod')),hls_estimated_ns=float(x.findtext('.//EstimatedClockPeriod')),
        hls_resources={e.tag:int(e.text) for e in x.find('.//AreaEstimates/Resources')},csim=dict(exact_cases=8,invalid_cases=10),
        rtl_cosim_cases=[dict(index=i,case=names[i],cycles=cycles,nominal_model_ms=cycles*5/1e6) for i,cycles in values],
        timing_note='XSim AXI memory model at200MHz; valid and error paths kept separate. No board ms/token or whole-head tokens/s claim.',
        logical_score_reads=dict(passes=5,beats_128_per_valid_call=189920,bytes_per_valid_call=3038720),
        counters_note='Counters describe logical requested128bit beats, not independently monitored physical DDR traffic/burst padding.',
        source_sha256={name:sha(M/name) for name in files},fixture_manifest_sha256=sha(reports/'topk_fixture_20261021/MANIFEST.json'),
        physical_timing='NOT_RUN for topK IP; candidate exact-head separate OOC PASS cannot be inherited',hardware_access='NONE',
        next=['Implement/qualify BF16-factor lowrank and router FP32 arithmetic','Integrate preview/topK/candidate exact head with capacity/address checks','Full PL-DDR system STA/CDC and newly authorized board acceptance'])
    (reports/'TOPK_STAGE_RESULT_20261021.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# v4 top-K / 候选并集 HLS 阶段','',f"状态：**{result['state']}**。不是完整selector或v4发布/板测验收。",'',
        '输入为151936个已经按全局history处理penalty的FP32 preview分数，以及递增唯一的路由候选表。低秩矩阵乘尚不在本核内。',
        '四轮8-bit radix直方图选择第K大阈值，按较小global ID处理相等分数；-0/+0按数值相等处理。并集经151936-bit片上位图去重后递增输出M4ID表。','',
        '## 验证','',
        '- 四类真实校准preview的完整候选ID与独立完整排序/并集参考一致。',
        '- C仿真8组精确候选与10类非法输入PASS，覆盖K1/129/16K/全词表、正负零tie、NaN、容量、重复/逆序/越界route。',
        '- Verilog/XSim协同仿真3笔事务PASS，含真实英文、重复调用清理以及末尾NaN不写输出。','',
        f"HLS约束5ns，估计{result['hls_estimated_ns']:.3f}ns；直方图及标记主体II=2，每次处理4个分数。route采用分阶段控制，未强行声称II=1。",
        f"HLS资源估计：{result['hls_resources']['BRAM_18K']} BRAM18K、{result['hls_resources']['DSP']} DSP、{result['hls_resources']['FF']} FF、{result['hls_resources']['LUT']} LUT。包含本核AXI缓冲，不包含低秩与候选精算。",'',
        '| RTL事务 | 周期 | 200MHz模型耗时 |','| --- | ---: | ---: |']
    for row in result['rtl_cosim_cases']:lines.append(f"| {row['case']} | {row['cycles']} | {row['nominal_model_ms']:.5f}ms |")
    lines += ['', '不把有效调用与NaN早退混合平均；这是XSim AXI模型，不是板卡时延、P95或整个lm_head吞吐。',
        '有效调用5遍读取preview，逻辑189920个128-bit beat=3038720B；另计上游preview写入607744B、route读取、并集表写回。控制器实际总线行为仍需监测。','',
        '## 接口与边界','',
        '候选输入/输出沿用16B M4ID/V1头；DDR容量按16B beat，包括尾部padding。output容量先按min(V,routeK+topK)上界检查，失败不写表。',
        '输入preview及route在调用期间保持不变、与输出不重叠。NaN/Inf在首轮全扫描发现后退出，不写输出；调用者必须检查status，旧表中的magic不是本次成功证明。',
        '当前无公开ABI/板卡profile/driver冻结，无该topK核布局布线；原候选精算IP的200MHz OOC结论不能直接覆盖本核。',
        '下一步实现低秩/路由算术并独立验证近似数值，再集成完整PL DDR流程及验证200MHz/CDC；板测需要新的独占安排。','',
        '证据：hls_topk_csim_r3_20261021.log、hls_topk_cosim_r1_20261021.log及build/topk_cosim_r1/hls/solution1/sim/report。']
    (reports/'TOPK_STAGE_RESULT_20261021.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('TOPK_STAGE=PASS Csim8+10 RTLcosim3 clock_estimate_ns='+str(result['hls_estimated_ns']))
if __name__=='__main__':main()
