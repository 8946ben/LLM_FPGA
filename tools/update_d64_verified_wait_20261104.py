"""Record the latest real live snapshot and separately bounded runner-only checks."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
R=M/'reports/memory_runtime_repair_20261103_r1'
N=M/'reports/d64_native_memory_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
    snapshot=sorted((M/'reports/memory_repaired_full_20261103_r1/observations').glob('*/RUNTIME_SNAPSHOT.json'))[-1]
    s=json.loads(snapshot.read_text(encoding='utf-8'));assert s['utc'].startswith('2026-11-03T16:58:19')
    assert s['parent_identity_alive'] and s['workflow']['state']=='EXECUTING_XSIM' and s['active_locks']==1
    assert s['actual_sources_identical_to_qualified_first5'] and not s['actual_compiled_source_mismatches']
    assert not s['original_frozen_source_mismatches'] and not s['original_reused_source_mismatches']
    group=s['owned_process_group_members'];assert len(group)==4
    kernel=next(x for x in group if x['pid']==7537);assert kernel['start_ticks']=='332143178'
    assert len(s['returned_tv_sizes'])==7 and set(s['returned_tv_sizes'].values())=={0}
    rss=sum(x['rss_kib'] for x in group);gib=rss/1048576
    checks=json.loads((N/'RUNNER_CLEANUP_PRECHECK.json').read_text())
    assert checks['state']=='PASS_OWNED_GROUP_CLEANUP_CONTROLS_ONLY' and checks['all_precheck_owned_groups_empty']
    execution=json.loads((N/'EXECUTION_PREPARATION_PLAN.json').read_text())
    assert execution['state']=='PREPARED_NOT_EXECUTED' and len(execution['cases'])==21
    for n,h in execution['sources'].items():assert sha(ROOT/n)==h,n
    runner=M/'experiments/d64_native_memory_20261103_r1/run_gate.py';assert sha(runner)==checks['runner_sha256']
    assert not (N/'MANUAL_GATE_AUTHORIZATION.json').exists() and not (N/'WORKFLOW.json').exists()
    summary=json.loads((R/'SUMMARY.json').read_text(encoding='utf-8'))
    summary.update(updated_utc=s['utc'],verified_utc=s['utc'],latest_snapshot=rel(snapshot),latest_group_rss_kib=rss,
        native_runner_execution_preparation=rel(N/'EXECUTION_PREPARATION_PLAN.json'),
        native_runner_cleanup_precheck=rel(N/'RUNNER_CLEANUP_PRECHECK.json'),
        goal_turn_classification='PROGRESS_AND_VERIFIED_WAIT',
        progress='Same original full job confirmed live now,7TVs0B. New bounded native-gate runner/input plan prepared with full-PASS/SHA/current-process preconditions. Four actual Python-only owned-group cleanup controls independently returned; no EDA/native AXI/M14 qualification granted.',full_m14='INCOMPLETE')
    (R/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    matrix=json.loads((R/'SIMULATION_ACCEPTANCE_MATRIX.json').read_text())
    matrix['utc']=s['utc']
    for item in matrix['requirements']:
        if item['id']=='preservation':item['evidence']=[dict(path=rel(snapshot),sha256=sha(snapshot))]
    matrix['preparation_only']=[x for x in matrix.get('preparation_only',[]) if 'EXECUTION_PREPARATION_PLAN' not in x['path'] and 'RUNNER_CLEANUP_PRECHECK' not in x['path']]
    matrix['preparation_only'] += [dict(path=rel(N/name),sha256=sha(N/name),scope=scope) for name,scope in [
        ('EXECUTION_PREPARATION_PLAN.json','Bounded runner and9 source identities only; no compilation/runtime watcher qualification'),
        ('RUNNER_CLEANUP_PRECHECK.json','Four actual isolated Python cleanup controls only; no EDA/model/DUT qualification')]]
    (R/'SIMULATION_ACCEPTANCE_MATRIX.json').write_text(json.dumps(matrix,indent=2)+'\n')
    note=(f'最新00:58:19北京时间：原父/组身份匹配，kernel7537/start332143178 CPU{kernel["cpu_ticks"]}ticks，组{gib:.6f}GiB，仍stage0/1、7TV0B、完整0/1。快照{rel(snapshot)}。新增正常响应模型run_gate.py及EXECUTION_PREPARATION_PLAN.json，绑定9输入、完整PASS/SHA/实际父组空锁无前置与8GiB/32GiB余量/300s展开/180s每用例保护。4个真实隔离Python进程组清理控制通过，临时所属组全空；仅清理路径资格，watcher/STOP/资源端到端尚未资格，模型/SV/M14仍NOT_RUN。当前完整仿真未改、无并行EDA，无自动下一阶段。\n\n')
    resume=R/'RESUME.md';resume.write_text(note+resume.read_text(encoding='utf-8'),encoding='utf-8')
    agents=ROOT/'AGENTS.md';text=agents.read_text(encoding='utf-8')
    first=text.index('- 00:48:50北京时间');end=text.index('\n',first)
    text=text[:first]+f'- 00:58:19北京时间（16:58:19UTC）核原父/所属组创建身份匹配；kernel7537/start332143178 CPU{kernel["cpu_ticks"]}ticks，组{gib:.6f}GiB；stage0/1完成，7返回TV仍0B、完整0/1。日志已见50.005613ms，非完成率/数值资格。144实际编译源同已通过前5块，原148冻结/121复用源未变。快照{rel(snapshot)}。当前为已验证等待。'+text[end:]
    anchor='- 主入口reports/memory_runtime_repair_20261103_r1/RESUME.md、SUMMARY.json及SIMULATION_ACCEPTANCE_MATRIX.json。'
    assert text.count(anchor)==1
    text=text.replace(anchor,'- 新模型run_gate.py/EXECUTION_PREPARATION_PLAN.json仅准备；9源绑定、完整独立PASS及真实父/组/锁空前置。8GiB/32GiB余量/300s展开/180s单例保护。4个隔离真实Python所属组清理控制通过，测试进程全空；仅清理资格，watcher/STOP/资源端到端与模型/SV/M14均未资格化。无并行EDA，未生成启动确认文件。\n'+anchor)
    agents.write_text(text,encoding='utf-8')
    print(json.dumps(dict(state='PROGRESS_AND_VERIFIED_WAIT',utc=s['utc'],rss_gib=gib,native_gate='PREPARED_ONLY',full_m14='INCOMPLETE'),indent=2))
if __name__=='__main__':main()
