"""Persist a fresh observer snapshot, never infer numerical completion from liveness."""
from pathlib import Path
import datetime,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
R=M/'reports/memory_runtime_repair_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
    assert sys.argv[1:] in [[],['--verified-wait'],['--state-tb-preparation'],['--payload-auditor-preparation'],['--request-guard-preparation']]
    wait_only = sys.argv[1:] == ['--verified-wait']
    state_tb_prepared = sys.argv[1:] == ['--state-tb-preparation']
    payload_prepared = sys.argv[1:] == ['--payload-auditor-preparation']
    request_prepared = sys.argv[1:] == ['--request-guard-preparation']
    file=sorted((M/'reports/memory_repaired_full_20261103_r1/observations').glob('*/RUNTIME_SNAPSHOT.json'))[-1]
    snapshot=json.loads(file.read_text(encoding='utf-8'));utc=datetime.datetime.fromisoformat(snapshot['utc'])
    age=(datetime.datetime.now(datetime.timezone.utc)-utc).total_seconds();assert 0<=age<180,'Get a fresh real observation first'
    assert snapshot['workflow']['state']=='EXECUTING_XSIM' and snapshot['parent_identity_alive']
    assert snapshot['owned_process_group_members'] and snapshot['active_locks']==1
    assert not snapshot['actual_compiled_source_mismatches'] and snapshot['actual_sources_identical_to_qualified_first5']
    assert not snapshot['original_frozen_source_mismatches'] and not snapshot['original_reused_source_mismatches']
    assert len(snapshot['returned_tv_sizes'])==7 and all(x==0 for x in snapshot['returned_tv_sizes'].values())
    rss=sum(x['rss_kib'] for x in snapshot['owned_process_group_members']);gib=rss/1048576
    kernel=next(x for x in snapshot['owned_process_group_members'] if x['pid']==7537)
    assert kernel['start_ticks']=='332143178'
    precheck=M/'reports/d64_native_memory_20261103_r1/AUDITOR_SYNTHETIC_PRECHECK.json'
    pc=json.loads(precheck.read_text());assert pc['state']=='PASS_SYNTHETIC_HOST_AUDITOR_CONTROLS_ONLY'
    assert pc['auditor_sha256']==sha(ROOT/'tools/review_d64_native_gate_20261104.py')
    summary=json.loads((R/'SUMMARY.json').read_text(encoding='utf-8'))
    summary.update(updated_utc=snapshot['utc'],verified_utc=snapshot['utc'],latest_snapshot=rel(file),latest_group_rss_kib=rss,
        goal_turn_classification='VERIFIED_WAIT' if wait_only else 'PROGRESS_AND_VERIFIED_WAIT',native_auditor_synthetic_precheck=rel(precheck),
        progress=('Read-only observation of the same full RTL process confirmed live now;7 actual return TVs empty. No new numerical result or qualification. Existing preparations and auditor controls unchanged.' if wait_only else
                  'Same full RTL process confirmed live now;7 actual return TVs empty. Native host auditor synthetic positive trace and11 deliberate corruptions checked; no actual native model or full DUT qualification from these controls.'),full_m14='INCOMPLETE')
    suite_review=M/'reports/d64_state_tb_20261104_r1/INDEPENDENT_PREPARATION_REVIEW.json'
    if state_tb_prepared:
        suite=json.loads(suite_review.read_text());assert suite['state']=='PASS_INDEPENDENT_STRUCTURAL_PREPARATION_ONLY'
        assert suite['testbench_sha256']==sha(M/'experiments/d64_state_tb_20261104_r1/d64_state_tb.sv')
        summary.update(next_state_testbench_preparation=rel(suite_review),
            progress='Same full RTL confirmed live;7TV0B. Prepared persistent full-DUT12-case bench, independently checked110 ports/1522 sentinel literals/control schedule/one weight load/no inter-call reset. Structural preparation only; no SV compile, native-model qualification or full state/mode/numeric result.')
    payload_review=M/'reports/d64_state_tb_20261104_r1/HOST_AUDITOR_SYNTHETIC_PRECHECK.json'
    if payload_prepared:
        payload=json.loads(payload_review.read_text())
        assert payload['state']=='PASS_SYNTHETIC_STATE_PAYLOAD_AND_CONTROL_AUDITOR_CONTROLS_ONLY'
        assert len(payload['negative_controls_rejected'])==22
        assert payload['source_sha256']==sha(ROOT/'tools/review_d64_state_payload_20261104.py')
        summary.update(state_payload_auditor_precheck=rel(payload_review),
            progress='Same full RTL confirmed live;7TV0B. Prepared full state payload/register auditors and verified12 synthetic cases plus22 corruptions. No real RTL/model/state/mode/performance qualification; actual AXI address-span audit remains required.')
    request_review=M/'reports/d64_state_tb_20261104_r1/REQUEST_GUARD_PREPARATION_REVIEW.json'
    if request_prepared:
        request=json.loads(request_review.read_text());assert request['state']=='PASS_SYNTHETIC_REQUEST_AUDITOR_AND_GUARD_STRUCTURE_ONLY'
        assert len(request['negative_controls_rejected'])==13
        for name,digest in request['sources'].items():assert sha(ROOT/name)==digest
        summary.update(state_request_guard_preparation=rel(request_review),
            progress='Same full RTL confirmed live;7TV0B. Prepared passive17-port per-frame accepted AXI address guard/log and independent request replay with beat-count cross-check;13 synthetic corruptions rejected. Guard not compiled/run; actual model/suite/numeric/timing qualification remains pending.')
    (R/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    matrix=json.loads((R/'SIMULATION_ACCEPTANCE_MATRIX.json').read_text());matrix['utc']=snapshot['utc']
    for requirement in matrix['requirements']:
        if requirement['id']=='preservation':requirement['evidence']=[dict(path=rel(file),sha256=sha(file))]
    matrix['preparation_only']=[x for x in matrix.get('preparation_only',[]) if x['path']!=rel(precheck)]
    matrix['preparation_only'].append(dict(path=rel(precheck),sha256=sha(precheck),scope='Synthetic host replay positive/11 negative controls only; NOT tool/AXI/DUT evidence'))
    if state_tb_prepared:
        matrix['preparation_only']=[x for x in matrix['preparation_only'] if x['path']!=rel(suite_review)]
        matrix['preparation_only'].append(dict(path=rel(suite_review),sha256=sha(suite_review),scope='Persistent full-DUT12-case bench structural preparation only; NOT compiled or executed'))
    if payload_prepared:
        matrix['preparation_only']=[x for x in matrix['preparation_only'] if x['path']!=rel(payload_review)]
        matrix['preparation_only'].append(dict(path=rel(payload_review),sha256=sha(payload_review),scope='12 synthetic state payload/control cases and22 corruptions only; not actual AXI/RTL evidence'))
    if request_prepared:
        matrix['preparation_only']=[x for x in matrix['preparation_only'] if x['path']!=rel(request_review)]
        matrix['preparation_only'].append(dict(path=rel(request_review),sha256=sha(request_review),scope='Passive address guard structure and13 synthetic host replay controls; not compiled or executed monitor/DUT'))
    (R/'SIMULATION_ACCEPTANCE_MATRIX.json').write_text(json.dumps(matrix,indent=2)+'\n')
    local=utc.astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime('%m月%d日%H:%M:%S')
    line=f'- {local}北京时间真实核原父/所属组身份匹配；kernel7537/start332143178 CPU{kernel["cpu_ticks"]}ticks，组{gib:.6f}GiB；stage0/1完成，7返回TV仍0B、完整0/1。144实际编译源同已通过前5块，原148冻结/121复用源未变。快照{rel(file)}。当前为已验证等待，未获得完整数值/FIFO或decode资格。'
    agents=ROOT/'AGENTS.md';text=agents.read_text(encoding='utf-8');start=text.index('- ',text.index('## 2026-11-04'));end=text.index('\n',start)
    text=text[:start]+line+text[end:]
    marker='- 主入口reports/memory_runtime_repair_20261103_r1/RESUME.md、SUMMARY.json及SIMULATION_ACCEPTANCE_MATRIX.json。'
    if '- 正常响应模型主机验收器的合成控制通过：' not in text:
        assert text.count(marker)==1
        text=text.replace(marker,'- 正常响应模型主机验收器的合成控制通过：1038AR/131108R/11AW/152W/10B期望轨迹及11种位/ID/LAST/RESP/WSTRB/越界/X转0/RESET/计数破坏均被正确处理。仅验收器控制，不是实际SV/AXI/M14资格，见AUDITOR_SYNTHETIC_PRECHECK.json。\n'+marker)
    if state_tb_prepared:
        assert '- 新d64_state_tb_20261104_r1：' not in text
        text=text.replace(marker,'- 新d64_state_tb_20261104_r1：12场景持久DUT测试台草稿、一次完整权重加载/1522哨兵、逐次全工作区前后镜像/输入及末尾保护、寄存器读回/有效位/真实start-done/IP及调用周期、生产raw写禁止和早期错误副作用检查。110端口/12配置/1522字节常量及无中途复位结构独立核对通过；仅PREPARED_NOT_COMPILED，非SV/模型/完整模式/性能资格。无上载/新EDA；完整强压力和新模型门槛先后通过后才决定独立有界执行。\n'+marker)
    if payload_prepared:
        assert '- 连续调用载荷/寄存器主机验收器准备：' not in text
        text=text.replace(marker,'- 连续调用载荷/寄存器主机验收器准备：review_d64_state_payload_20261104.py区分调试全数组/生产无新raw且原raw保持/错误副作用，保留metadata错误读取无固定拍数约束；12个参考构造场景及22种破坏控制通过。只验收器控制，不是新RTL/模型/状态/性能资格；实际AXI地址范围仍须另审。见d64_state_tb_20261104_r1/HOST_AUDITOR_SYNTHETIC_PRECHECK.json。\n'+marker)
    if request_prepared:
        assert '- 连续调用AXI范围监视器准备：' not in text
        text=text.replace(marker,'- 连续调用AXI范围监视器准备：d64_state_tb_20261104_r1/state_request_guard.sv被动记录每帧MR/MW/WR及地址/len，检查输入/工作区/权重/4KiB/溢出/错误访问；17端口结构核对及主机回放13种合成破坏控制通过。REQUEST_GUARD_SUPPLEMENT.json要求未来编译加入此新文件，原bench SHA未变。仅准备，未编译/运行监视器；实际AXI范围/拍数和全量载荷仍须工具返回后绑定审计。\n'+marker)
    agents.write_text(text,encoding='utf-8')
    resume=R/'RESUME.md';note=line+('\n本轮为已验证等待；既有验收器控制和所有准备保持，无新数值/FIFO资格，无重启/新EDA。\n\n' if wait_only else
                       '\n本轮新增AUDITOR_SYNTHETIC_PRECHECK.json：期望轨迹回放及11种破坏拒绝，仅主机验收器控制。模型/SV/M14/性能仍未取得新资格。\n\n')
    if state_tb_prepared:
        note=line+'\n新experiments/reports/d64_state_tb_20261104_r1持久完整DUT12场景草稿；110端口/12配置/1522哨兵/一次权重加载及无中途复位结构独立核对通过。前后全工作区、有效位/实际start-done、生产raw保护、错误副作用及周期记录入口已准备。仍NOT_COMPILED/NOT_EXECUTED；需要当前完整独立PASS、新模型真实门槛PASS及后续有界入口/真实数组审计。无上载/新EDA。\n\n'
    if payload_prepared:
        note=line+'\n连续调用载荷/寄存器纯主机验收器已准备：完整有效数组/标量、生产无新raw与原raw保持、早期错误无工作区/权重副作用、输入/guard、fresh有效位/参数读回/done读清。12个参考构造场景及22种刻意破坏控制通过，只验收器控制；不是实际SV/模型/完整状态/性能资格。错误metadata读取不要求固定拍数，实际AXI地址范围仍另审。见d64_state_tb_20261104_r1/HOST_AUDITOR_SYNTHETIC_PRECHECK.json。原完整作业未改。\n\n'
    if request_prepared:
        note=line+'\n新增d64_state_tb_20261104_r1/state_request_guard.sv与review_d64_state_requests_20261104.py。被动逐帧地址/len日志与summary，对照真实R/W拍数、容量/flag零访问、metadata错误只读输入/无权重、预览错误不读canonical等。17端口结构及13种合成主机破坏控制通过；未编译/运行监视器或DUT。未来独立冻结工程必须加入REQUEST_GUARD_SUPPLEMENT.json的新源；原bench/当前完整源未改，完整结果及新模型门槛仍前置。\n\n'
    resume.write_text(note+resume.read_text(encoding='utf-8'),encoding='utf-8')
    print(json.dumps(dict(state='VERIFIED_WAIT' if wait_only else 'PROGRESS_AND_VERIFIED_WAIT',utc=snapshot['utc'],rss_gib=gib,full_m14='INCOMPLETE',native_host_auditor='SYNTHETIC_CONTROLS_ONLY'),indent=2))
if __name__=='__main__':main()
