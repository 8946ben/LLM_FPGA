"""Collect official whole-selector C/RTL results, never infer PASS from tool exit."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse, hashlib, json, re, xml.etree.ElementTree as ET
from selector_rtl_completion import transactions
M=Path(__file__).resolve().parents[1];R=M/'reports'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def text(p):return p.read_text(encoding='utf-8-sig')
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',default='selector_full_cosim_r2');p.add_argument('--log',default='hls_selector_full_cosim_r2_20261021.log');p.add_argument('--repaired',action='store_true');args=p.parse_args()
    assert re.fullmatch('[a-zA-Z0-9_-]+',args.run)
    run=M/'build'/args.run/'hls/solution1'
    log=text(R/args.log)
    if args.repaired:
        assert 'C/RTL co-simulation finished: FAIL' in log,'Preserve original tool-wrapper failure'
        trace=json.loads(text(R/'SELECTOR_RTL_TRACE_AUDIT.json'))
        assert trace['state']=='PASS_FULL_RTL_TRACE_COMPARE' and trace['whole_memory_values']==41943040
        pc=text(R/'selector_repaired_postcheck_r2_20261021.log')
        assert 'M14_V4_SELECTOR_CSIM=PASS valid=1 preflight_invalid=1 stage_errors=0 rtl_subset=1' in pc
        assert 'SELECTOR_REPAIRED_POSTCHECK_EXIT=0' in pc
    else:
        assert 'C/RTL co-simulation finished: PASS' in log,'Official RTL PASS missing'
        assert 'M14_V4_SELECTOR_FULL_RTL_COSIM=PASS' in log,'Tcl completion marker missing'
    assert 'M14_V4_SELECTOR_CSIM=PASS valid=1 preflight_invalid=1 stage_errors=0 rtl_subset=1' in log
    rpt=run/'sim/report/lm_head_v4_selector_cosim.rpt'
    if not args.repaired:assert re.search(r'\|\s*Verilog\|\s*Pass\|',text(rpt)),'Verilog report not Pass'
    tr=run/'sim/verilog/lm_head_v4_selector.performance.result.transaction.xml'
    cases=transactions(tr)
    assert len(cases)==2,'Expected fullV Chinese and a separate overlap rejection'
    for case,label in zip(cases,['chinese_fullV_debug_complete_preview_ID_rawlogits_dense_bits','overlap_rejection_no_token']):
        case.update(label=label,model_ms_at_200MHz=case['cycles']/200000)
    csim=text(R/'hls_selector_csim_r2_20261021.log')
    assert 'M14_V4_SELECTOR_CSIM=PASS valid=6 preflight_invalid=24 stage_errors=5 rtl_subset=0' in csim
    host=text(R/'host_tests_selector_20261021.log');assert 'Ran 32 tests' in host and re.search(r'\bOK\b',host)
    assert 'SELECTOR_CONTROL_HOST_TEST=PASS cases=25 fake_MMIO_only' in text(R/'selector_control_test_20261021.log')
    ip=json.loads(text(R/'SELECTOR_PRIVATE_IP_MANIFEST.json'))
    for name,digest in ip['files'].items():assert sha(M/ip['path']/name)==digest,name
    for name,digest in ip['source_sha256'].items():assert sha(M/name)==digest,name
    assert sha(M/'interface/PL_DDR_LAYOUT_V4.json')==ip['layout_sha256']
    x=ET.parse(run/'syn/report/lm_head_v4_selector_csynth.xml')
    original=M/'build/selector_csynth_r2/hls/solution1/syn/report/lm_head_v4_selector_csynth.xml'
    assert sha(original)==sha(run/'syn/report/lm_head_v4_selector_csynth.xml'),'Cloned synthesis differs'
    evidence=[R/args.log,tr,original,R/'SELECTOR_CONTROL_REGISTER_AUDIT.json']
    if args.repaired:evidence += [R/'SELECTOR_COSIM_NAME_REPAIR.json',R/'SELECTOR_RTL_TRACE_AUDIT.json',R/'SELECTOR_RTL_IP_EQUIVALENCE.json',R/'XSIM_OBSERVABILITY_CONTROL.json',R/'selector_repaired_xsim_r5_20261021.log',R/'selector_repaired_postcheck_r2_20261021.log']
    else:evidence.append(rpt)
    if args.repaired and trace.get('preserved_completion_recovery_sha256'):
        recovery=R/'SELECTOR_COMPLETION_RECOVERY_20261022.json'
        assert sha(recovery)==trace['preserved_completion_recovery_sha256']
        evidence.append(recovery)
    result=dict(state='PASS_OFFLINE_INTEGRATED_SELECTOR_RTL',updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),
      validation_route='Repaired generated-XSim wrapper, full memory/scalar trace comparison and original C postcheck' if args.repaired else 'Official HLS C/RTL wrapper PASS',
      original_hls_wrapper='FAIL_GENERATED_TESTBENCH_NAME_COLLISION_PRESERVED' if args.repaired else 'PASS',
      board='NOT_RUN',whole_system_implementation='SEE_SEPARATE_HARDWARE_AUDIT',
      hls_estimated_ns=float(x.findtext('.//EstimatedClockPeriod')),
      resources={e.tag:int(e.text) for e in x.find('.//AreaEstimates/Resources')},
      csim={'valid':6,'preflight_invalid':24,'stage_errors':5},host_tests=32,control_fake_mmio_tests=25,
      fullV_rtl_valid_cases=1,rtl_negative_cases=1,transactions=cases,
      numeric_reference='Four full C cases; one fullV RTL Chinese: preview151936, all K21529 IDs/rawlogits, dense token20412/score0x41de477c/CRC',
      timing_scope='AXI simulation memory model, debug sparse enabled; not real MIG/production/board decode/TTFT',
      hardware_identity='Private GPIO signature0x4D345301; not public ABI/build_config',
      quality='Calibration audit only for revised arithmetic; historical CPU r2b holdout cannot certify RTL quality',
      source_sha256=ip['source_sha256'],ip_manifest_sha256=sha(R/'SELECTOR_PRIVATE_IP_MANIFEST.json'),
      evidence_sha256={str(p.relative_to(M)):sha(p) for p in evidence})
    (R/'SELECTOR_INTEGRATION_RESULT_20261021.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rows=['# v4 统一selector离线RTL验收','',f"状态：{result['state']}。未操作板卡，未形成正式发布。",'',
      '统一父级顺序执行预检、路由、低秩、Top-K/并集、canonical候选精算。两条数据AXI均面向PL DDR。',
      'C仿真6正确/24预检拒绝/5运行错误；32项host测试及25项PS fake-MMIO测试通过。',
      '验证路径：'+result['validation_route']+'；原始HLS包装流程状态：'+result['original_hls_wrapper']+'。',
      '整链RTL使用真实完整151936词表中文样例，逐位检查完整preview、21529候选ID及所有raw logits、最终dense token/score bits/CRC；另测重叠拒绝。','',
      '| RTL事务 | 周期 | 200MHz仿真模型ms |','| --- | ---: | ---: |']
    rows += [f"| {c['label']} | {c['cycles']} | {c['model_ms_at_200MHz']:.6f} |" for c in cases]
    rows += ['','计时包含debug稀疏输出和仿真AXI模型，不是板上生产decode，不能作为整机token/s或TTFT。',
      '200MHz全系统STA/CDC/DRC、bit/XSA和PS软件配套须另外验收；新算术质量仍需未打开的独立测试。',
      '原单端口DATAFLOW失败、日期Revision溢出及用户暂停的中断日志均保留。']
    (R/'SELECTOR_INTEGRATION_RESULT_20261021.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    # Persist a genuine terminal RTL result even when this long simulation is
    # left running between chat turns. Do not mark software/quality/board done.
    progress_path=M/'PROGRESS.json'
    progress=json.loads(text(progress_path))
    hardware_path=R/'board_v4_20261021/hardware_audit_r2.json'
    hardware=json.loads(text(hardware_path)) if hardware_path.exists() else {}
    hardware_ok=hardware.get('state')=='PASS_OFFLINE_SYSTEM'
    if hardware_ok:
        hw=hardware_path.parent/'hardware_r2'
        hardware_ok=(sha(hw/'m14_v4_system_wrapper.bit')==hardware['bit_sha256'] and
                     sha(hw/'m14_v4_single.xsa')==hardware['xsa_sha256'])
    progress.update(updated=result['updated'],
      stage='P4_OFFLINE_RTL_SYSTEM_PASS_PS_PENDING' if hardware_ok else 'P4_INTEGRATED_RTL_PASS_SYSTEM_AUDIT_PENDING',
      active_work='RTL sequence completed; no automatic BSP, loader, board or old WB/heartbeat work',
      runtime_processes='No further EDA launched by this sequence',
      next='Complete matching PS BSP/ELF and target-readback arena loader offline; independent quality and newly authorized exclusive board acceptance still required')
    sequence_path=R/'OFFLINE_SEQUENCE_20261022.json'
    if sequence_path.exists() and json.loads(text(sequence_path)).get('stage') in ('WAITING_EXISTING_RTL','QUALIFYING_PRESERVED_RTL'):
        progress['active_work']='RTL qualification finished; existing dependent BSP/ELF/private-package workflow is tracked by reports/OFFLINE_SEQUENCE_20261022.json; no board jobs'
        progress['runtime_processes']='Check existing offline-sequence status/PID; do not duplicate launches'
        progress['next']='Observe existing dependent offline sequence and review terminal artifacts; board and independent quality remain pending'
    progress['milestones']['P4']='Integrated repaired-wrapper fullV RTL PASS; '+('complete offline 200MHz system audit PASS' if hardware_ok else 'system audit pending')+'; not board/release acceptance'
    progress['dependencies']=['Actual PS BSP/ELF and target-readback arena loader pending',
      'New arithmetic independent quality not certified; opened holdouts not reusable',
      'No FPGA board access authorized; upstream direct weights deferred']
    if not hardware_ok:progress['dependencies'].insert(0,'Complete system implementation audit pending')
    progress['integrated_rtl']={'state':result['state'],'validation_route':result['validation_route'],
      'report':'reports/SELECTOR_INTEGRATION_RESULT_20261021.json','transactions':cases,
      'timing_scope':result['timing_scope'],'board':'NOT_RUN'}
    for name in ('reports/SELECTOR_INTEGRATION_RESULT_20261021.json','reports/SELECTOR_RTL_TRACE_AUDIT.json'):
        if name not in progress['evidence']:progress['evidence'].append(name)
    progress_path.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SELECTOR_INTEGRATION=PASS fullV RTL1+negative1; route='+result['validation_route']+'; NOT_BOARD')
if __name__=='__main__':main()
