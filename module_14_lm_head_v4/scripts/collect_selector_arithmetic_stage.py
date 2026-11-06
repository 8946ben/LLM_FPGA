"""Audit completed independent components and the linked C chain, not a release."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,re,xml.etree.ElementTree as ET
M=Path(__file__).resolve().parents[1];R=M/'reports'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def transactions(run):
    p=M/'build'/run/'hls/solution1'
    rpt=(p/'sim/report'/f'lm_head_v4_{"lowrank" if run.startswith("lowrank") else "router"}_cosim.rpt').read_text()
    assert re.search(r'\|\s*Verilog\|\s*Pass\|',rpt)
    return [dict(index=int(i),cycles=int(t),nominal_model_ms=int(t)*5/1e6) for i,t in re.findall(r'transaction\s+(\d+):\s+(\d+)',(p/'sim/report/verilog/result.transaction.rpt').read_text())]
def main():
    checks=[('hls_lowrank_csim_r3_20261021.log','M14_V4_LOWRANK_CSIM=PASS exact=5 invalid=10 numeric=3'),
      ('hls_router_csim_r2_20261021.log','M14_V4_ROUTER_CSIM=PASS exact=6 invalid=10 numeric=2'),
      ('hls_lowrank_cosim_r1_20261021.log','M14_V4_LOWRANK_cosim=PASS'),
      ('hls_router_cosim_r2_20261021.log','M14_V4_ROUTER_cosim=PASS'),
      ('hls_selector_chain_csim_r3_20261021.log','M14_V4_SELECTOR_CHAIN_CSIM=PASS cases4 full_sparse_logits_and_dense_outputs')]
    for name,marker in checks:assert marker in (R/name).read_text(encoding='utf-8'),name
    for name in ('hls_lowrank_cosim_r1_20261021.log','hls_router_cosim_r2_20261021.log'):
        text=(R/name).read_text(encoding='utf-8')
        assert 'C/RTL co-simulation finished: PASS' in text and 'All loop constraints were satisfied.' in text
    host=(R/'host_tests_projection_20261021.log').read_text(encoding='utf-8');assert 'Ran 29 tests' in host and re.search(r'\bOK\b',host)
    fixtures={}
    for name in ('lowrank_fixture_20261021','router_fixture_20261021','selector_chain_fixture_20261021'):
        data=load(R/name/'MANIFEST.json')
        for file,digest in data['files'].items():assert sha(R/name/file)==digest,(name,file)
        if isinstance(data.get('source_sha256'),dict):
            for file,digest in data['source_sha256'].items():assert sha(M/file)==digest,file
        else:assert sha(M/'scripts/prepare_chain_fixtures.py')==data['source_sha256']
        fixtures[name]=sha(R/name/'MANIFEST.json')
    chain=load(R/'selector_chain_fixture_20261021/MANIFEST.json')
    for name,digest in chain['fixture_manifest_sha256'].items():assert sha(R/name/'MANIFEST.json')==digest
    assert sha(M.parent/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin')==chain['canonical_weight_sha256']
    quality=load(R/'PL_ARITHMETIC_CALIBRATION.json')
    assert quality['reference_sha256']==sha(M/'reference/selector_arithmetic.py') and quality['source_sha256']==sha(M/'scripts/qualify_selector_arithmetic.py')
    assert quality['holdout_read'] is False and [quality[k]['decode']['misses'] for k in ('route','lowrank','hybrid')]==[15,84,0]
    assert quality['hybrid']['decode']['steps']==4775 and quality['changed_route_order_vs_cpu_blas']==0
    parts={}
    for name,run in [('lowrank','lowrank_cosim_r1'),('router','router_cosim_r2')]:
        p=M/'build'/run/'hls/solution1/syn/report'/f'lm_head_v4_{name}_csynth.xml';x=ET.parse(p)
        cases=transactions(run);assert len(cases)==3
        parts[name]=dict(hls_estimated_ns=float(x.findtext('.//EstimatedClockPeriod')),
            resources={e.tag:int(e.text) for e in x.find('.//AreaEstimates/Resources')},
            rtl_cases=cases,csynth_xml=p.relative_to(M).as_posix(),csynth_xml_sha256=sha(p))
    parts['lowrank']['rtl_case_labels']=['real_chinese_first256_scores','repeat_zero_rows3','hidden_nan_error_exit']
    parts['router']['rtl_case_labels']=['real_chinese_full_route_table','tie_four_clusters_and_specials','empty_cluster_dense_fallback']
    # Preserve and describe the real C/RTL failure before the bitset fix.
    failed=(R/'hls_router_cosim_r1_20261021.log').read_text(encoding='utf-8');assert 'C/RTL co-simulation finished: FAIL' in failed
    files=['src/lm_head_v4_lowrank.cpp','src/lm_head_v4_router.cpp','src/selector_chain_csim_unit.cpp',
      'include/lm_head_v4_lowrank.hpp','include/lm_head_v4_router.hpp','src/accepted_numeric_core.hpp',
      'src/lm_head_v4_topk.cpp','src/lm_head_v4_candidate.cpp','reference/selector_arithmetic.py',
      'tests/lowrank_csim.cpp','tests/lowrank_cosim.cpp','tests/router_csim.cpp','tests/selector_chain_csim.cpp','tests/test_selector_arithmetic.py',
      'hls_lowrank.tcl','hls_router.tcl','hls_selector_chain_csim.tcl','scripts/qualify_selector_arithmetic.py','scripts/collect_selector_arithmetic_stage.py']
    core=load(R/'HLS_NUMERIC_CORE_PROVENANCE.json')
    assert sha(M/'src/accepted_numeric_core.hpp')==core['extracted_core_sha256']
    # Imported core remains separately covered by its existing provenance;
    # this audit adds the current byte hash rather than rewriting that record.
    result=dict(state='INDEPENDENT_COMPONENTS_AND_C_CHAIN_PASS',updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),
      scope='Lowrank/router independent Csim+HLS+RTL subset; four production-sized linked C-chain examples; calibration arithmetic audit',
      hardware_access='NONE',full_selector_hls='NOT_RUN',full_selector_rtl='NOT_RUN',full_system_sta_cdc='NOT_RUN',fpga_decode='NOT_RUN',ttft='NOT_RUN',
      components=parts,csim=dict(lowrank=dict(exact=5,invalid=10,numeric=3),router=dict(exact=6,invalid=10,numeric=2),linked_chain_cases=4,host_tests=29),
      c_chain=chain['rows'],calibration=dict(groups=320,all_predictions=5095,decode=4775,route_misses=15,lowrank_misses=84,hybrid_misses=0,changed_route_order=0,report_sha256=sha(R/'PL_ARITHMETIC_CALIBRATION.json')),
      timing_boundary='RTL AXI memory model at200MHz; valid/zero/error/fallback cases separate; no average used as performance claim',
      a_scan_budget=dict(words_per_row=16,rows=151936,ideal_read_cycles=2430976,nominal_model_ms=12.15488,note='Structural floor, excludes real DDR stalls and all other stages; not whole-head latency'),
      failure_history=[dict(run='lowrank_csim_r1',cause='Testbench ap_uint vector default construction was not explicit zero initialization',result='Four real cases passed; synthetic zero failed; fixture fixed and full regression passed'),
        dict(run='lowrank_csynth_r1',cause='Vitis HLS2021.1 forbids return value on non-top DATAFLOW region',result='Converted to output reference and explicit flag-join task; Csim and RTL rerun'),
        dict(run='router_csynth_r1',cause='norm/count share AXI metadata port, II1 cannot sustain two reads; outer list loop auto-pipeline unsupported',result='Declared meta II2 and sequential list control; final all constraints satisfied'),
        dict(run='router_cosim_r1',observed='Real K2501 instead of8527; tie K4 instead of18, survivors1/151647/151655/151656',
             cause='Memory bit-reference updates lowered to byte-enable stores in this generated RTL and lost neighboring bits',
             result='Full128bit register mask OR plus cached-word flush/load; same-byte ties, real full table and dense fallback RTL revalidated')],
      source_sha256={f:sha(M/f) for f in files},fixture_manifests=fixtures,
      evidence_sha256={name:sha(R/name) for name,_ in checks},
      remaining=['Integrated selector scheduling/status/64bit PL-DDR allocation and alias/capacity checks',
        'Full selector RTL and complete200MHz system STA/CDC; no topK/lowrank/router P&R yet',
        'Independent quality for new arithmetic not certified by reusing opened holdout',
        'New exclusive board arrangement and complete decode measurements'])
    (R/'SELECTOR_ARITHMETIC_STAGE_20261021.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# v4 低秩/路由独立核及完整C链阶段验收','',f"状态：**{result['state']}**。不是完整硬件/板卡/发布验收。",'',
      '- 低秩CSim：5正确/10配置错误/3非有限数；路由：6正确/10非法/2非有限数。29项host测试PASS。',
      '- 两核各3事务Verilog/XSim正式协同仿真PASS；低秩真实RTL仅前256个preview，路由真实RTL为完整8527个候选。',
      '- 四类完整C流程串接路由→低秩→Top-K/并集→canonical精算；全部候选ID/raw logit、dense轨迹token/score bits/CRC一致。',
      '- 固定参数新算术模型对同校准集4775 decode：聚类15漏选、低秩84、混合0，路由顺序变化0。未打开holdout，不代表新的独立质量认证。','',
      '| 组件 | HLS估计ns | BRAM18K | DSP | RTL用例 | 周期 | 200MHz模型ms |','| --- | ---: | ---: | ---: | --- | ---: | ---: |']
    for name,data in parts.items():
        for case,label in zip(data['rtl_cases'],data['rtl_case_labels']):lines.append(f"| {name} | {data['hls_estimated_ns']:.3f} | {data['resources']['BRAM_18K']} | {data['resources']['DSP']} | {label} | {case['cycles']} | {case['nominal_model_ms']:.6f} |")
    lines+=['','有效/零输入/错误/fallback分列，不混合平均，也不把本表换算成完整decode token/s。','',
      '## 实际发现并修复的失败','',
      'router r1的C仿真通过，但RTL把8527个候选变成2501；同分小例仅剩1/151647/151655/151656四项，原应18项。',
      '本次生成RTL的memory bit-reference/byte-enable写丢失同字节其他置位。改为完整128位寄存器mask的OR、按block写回/读入，再以相同RTL用例验收。原失败日志与输出不删。',
      '另保留低秩测试夹具未显式清零、DATAFLOW返回值不兼容及路由共享AXI端口II约束失败；不得把工具退出码0视为成功，核对测试标记和官方C/RTL PASS。','',
      '## 预算与未完成范围','',
      'A扫描理想供数下16拍/行，完整151936行2430976拍=12.15488ms@200MHz；不是整核或板上计时。',
      '低秩/路由/Top-K尚无本轮P&R。仍需完整selector硬件集成、PL DDR父级调度/地址及别名检查、全系统STA/CDC、配套镜像和新板卡安排。',
      'v3.1仍是最后实板dense基线；v4完整ms/token、token/s、TTFT保持NOT_RUN。','',
      '可复核入口：SELECTOR_ARITHMETIC_STAGE_20261021.json、PL_ARITHMETIC_CALIBRATION.json、hls_*日志及build/*/sim/report。']
    (R/'SELECTOR_ARITHMETIC_STAGE_20261021.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('SELECTOR_ARITHMETIC_STAGE=PASS independentRTL3+3 Cchain4 host29 calibration4775; NOT_BOARD')
if __name__=='__main__':main()
