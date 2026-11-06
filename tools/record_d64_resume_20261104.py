"""Persist verified Nov4 resume and preparation scope, never start EDA."""
from pathlib import Path
import json,hashlib,datetime

ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
R=M/'reports/memory_runtime_repair_20261103_r1'
def rel(p):return p.relative_to(ROOT).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    snapshots=sorted((M/'reports/memory_repaired_full_20261103_r1/observations').glob('*/RUNTIME_SNAPSHOT.json'))
    p=snapshots[-1];s=json.loads(p.read_text(encoding='utf-8'));w=s['workflow']
    assert s['utc'].startswith('2026-11-03T16:48:50')
    assert w['state']=='EXECUTING_XSIM' and s['parent_identity_alive'] and s['active_locks']==1
    assert s['owned_process_group_members'] and not s['actual_compiled_source_mismatches']
    assert s['actual_sources_identical_to_qualified_first5']
    assert not s['original_frozen_source_mismatches'] and not s['original_reused_source_mismatches']
    assert len(s['returned_tv_sizes'])==7 and set(s['returned_tv_sizes'].values())=={0}
    gib=sum(x['rss_kib'] for x in s['owned_process_group_members'])/1048576
    fixtures=M/'reports/d64_state_fixtures_20261104_r2/INDEPENDENT_PREPARATION_REVIEW.json'
    f=json.loads(fixtures.read_text(encoding='utf-8'));assert f['state']=='PASS_INDEPENDENT_PREPARATION_ONLY' and f['cases']==12
    model=M/'reports/d64_native_memory_20261103_r1/GATE_PREPARATION_PLAN.json'
    gate=json.loads(model.read_text(encoding='utf-8'));assert gate['state']=='PREPARED_NOT_COMPILED_OR_QUALIFIED' and len(gate['cases'])==21
    for n,h in gate['sources'].items():assert sha(ROOT/n)==h,n
    precheck=dict(state='PASS_PYTHON_SYNTAX_AND_PLANNED_EVENT_BUDGET_ONLY',
        read_beats=131108,write_beats=152,read_requests=1038,write_requests=11,b_responses=10,
        source_sha256=gate['sources'],eda='NOT_RUN',simulation_or_auditor_runtime_qualification=False)
    (model.parent/'STIMULUS_STATIC_PRECHECK.json').write_text(json.dumps(precheck,indent=2)+'\n')
    summary=json.loads((R/'SUMMARY.json').read_text(encoding='utf-8'))
    summary.update(updated_utc=s['utc'],verified_utc=s['utc'],latest_snapshot=rel(p),latest_group_rss_kib=sum(x['rss_kib'] for x in s['owned_process_group_members']),
        next_state_fixture_report=rel(fixtures),native_model_preparation=rel(model),goal_turn_classification='PROGRESS_AND_VERIFIED_WAIT',
        progress='User resumed after pause with remote run explicitly retained. Same live process and all compiled/frozen sources verified. Prepared complete debug A/B/A plus separate production A (12 cases), and21-case native-memory gate/testbench draft. Neither additional suite compiled or simulated.',
        full_m14='INCOMPLETE',automatic_next_stage=False)
    (R/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    matrix=json.loads((R/'SIMULATION_ACCEPTANCE_MATRIX.json').read_text(encoding='utf-8'))
    matrix['utc']=s['utc'];matrix['preparation_only']=[dict(path=rel(fixtures),sha256=sha(fixtures),scope='12 input/control cases; NOT RTL qualified'),dict(path=rel(model),sha256=sha(model),scope='21-case native model/testbench draft; NOT compiled/qualified')]
    for item in matrix['requirements']:
        if item['id']=='preservation':item['evidence']=[dict(path=rel(p),sha256=sha(p))]
    (R/'SIMULATION_ACCEPTANCE_MATRIX.json').write_text(json.dumps(matrix,indent=2)+'\n')
    text=(
        '# 2026-11-04 恢复：同一完整RTL继续运行，额外回归仅准备\n\n'
        f'用户已恢复active；此前明确保留远端仿真，暂停期间未发STOP。00:48:50北京时间（16:48:50UTC）真实快照确认原父/所属组创建身份匹配，内核7537/start332143178 CPU1763279ticks，组{gib:.6f}GiB。144实际编译源与已通过前5块一致，原148冻结/121复用源无差异。最新日志曾推进到50.005613ms；只stage0/1完成，7TV仍0B、完整0/1。未获得完整数值/FIFO或decode结论。\n\n'
        f'快照：{rel(p)}。保留原64GiB/48h保护和同一作业；不得重复prepare/bootstrap。按原流程等待真实返回后独立核组空/锁无、取回静态证据及全数组/FIFO审计。\n\n'
        '新独立准备reports/experiments/d64_state_fixtures_20261104_r2：A(debug)→B(debug)→A(debug)，再A(production)、zero/ties及6类错误/恢复，共12场景。相对r1单独补齐B完整raw覆盖与同A模式切换。输入/control、参考SHA与545685504B权重重新流式核SHA通过，仅PREPARED_NOT_SIMULATED。\n\n'
        '额外正常响应模型experiments/d64_native_memory_20261103_r1/d64_native_memory.sv SHA48153808aa8c001a9174fa45d161e9a03867df0b6ba6d9f47b758cde3973db38。已有可逆静态检查和native_gate_tb.sv/逐位四态主机回放器/21用例门槛规划。计划128bit、1读1写outstanding、registered无额外随机等待，明确不是MIG/物理DDR；模型、测试台和回放器均未工具资格化。原强压力完整独立通过后才手动决定有界新模型门槛，再决定多调用；不替代当前完整门槛、不并行EDA。\n\n'
        '无板卡/实现/sudo/其他agent/wb/luyou/心跳；根开发日志未改。当前目标未完成。\n\n---\n\n')
    resume=R/'RESUME.md';resume.write_text(text+resume.read_text(encoding='utf-8'),encoding='utf-8')
    heading=(
        '## 2026-11-04 用户恢复目标，同一完整RTL仍执行（最新）\n\n'
        f'- 00:48:50北京时间（16:48:50UTC）核原父/所属组创建身份匹配；kernel7537/start332143178 CPU1763279ticks，组{gib:.6f}GiB；stage0/1完成，7返回TV仍0B、完整0/1。日志已见50.005613ms，但不当完成率/数值进展。144实际编译源同已通过前5块，原148冻结/121复用源未变。快照{rel(p)}。用户此前要求保留远端运行，未发STOP；现目标已active。\n'
        '- 当前仍唯一memory_repaired_full_20261103_r1；原64GiB/48h/32GiB余量保护，未重启或改源。返回后按原审计流程，不凭存活/RSS写通过。\n'
        '- 新独立d64_state_fixtures_20261104_r2共12场景：完整A(debug)→B(debug)→A(debug)、单独A(production)、zero/ties、6类错误及恢复。r1保留；补齐B完整raw覆盖。输入/control、参考及545685504B权重SHA复核通过，仅PREPARED_NOT_SIMULATED。\n'
        '- d64_native_memory_20261103_r1已形成正常响应模型草稿及native_gate_tb.sv、四态逐拍主机回放器、21项门槛规划。模型SHA48153808aa8c001a9174fa45d161e9a03867df0b6ba6d9f47b758cde3973db38；可逆静态/计划计数检查通过。未编译/运行/资格化；不并行EDA、不替代强压力完整结果。实际新门槛/多调用仍需完整独立通过后主模型手动决定。\n'
        '- 主入口reports/memory_runtime_repair_20261103_r1/RESUME.md、SUMMARY.json及SIMULATION_ACCEPTANCE_MATRIX.json。无板卡/实现/sudo/其他agent/wb/luyou/心跳，根开发日志未改。下方最新/NOT_IMPLEMENTED均历史。\n\n')
    agents=ROOT/'AGENTS.md';a=agents.read_text(encoding='utf-8');first,rest=a.split('\n',1)
    agents.write_text(first+'\n\n'+heading+rest.lstrip('\n'),encoding='utf-8')
    print(json.dumps(dict(state='RESUME_AND_PREPARATION_SCOPE_RECORDED',rss_gib=gib,full_m14='INCOMPLETE',next_stage='NOT_RUN'),indent=2))

if __name__=='__main__':main()
