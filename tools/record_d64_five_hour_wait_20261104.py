"""Record the user's explicit five-hour no-check window; no remote operation."""
from pathlib import Path
import datetime,json
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'module_14_lm_head_v4/reports/memory_runtime_repair_20261103_r1'
def main():
    record=dict(state='USER_REQUESTED_WAIT_UNTIL',user_request='请等待5个小时再核验',
        recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        not_before_utc='2026-11-03T22:35:00+00:00',not_before_beijing='2026-11-04 06:35:00 +08:00',
        automation_id='5-t04',automation_status='ACTIVE',automation_kind='heartbeat_one_occurrence_COUNT_1',
        original_remote_job='memory_repaired_full_20261103_r1',remote_stop_sent=False,
        instructions=['No remote connection or simulation verification before the deadline unless user explicitly overrides',
                      'Keep the existing remote simulation and64GiB/48h protections unchanged',
                      'No new EDA/board/implementation/agents/wb/luyou work during the wait',
                      'At deadline perform the single authorized verification; pause5-t04 after use',
                      'Waiting is not simulation completion or numerical/FIFO qualification'])
    path=R/'USER_WAIT_UNTIL_20261104.json';assert not path.exists()
    path.write_text(json.dumps(record,indent=2)+'\n')
    note=('## 2026-11-04 用户要求等待5小时，06:35前不核验（当前优先）\n\n'
          '- 用户最新明确要求“请等待5个小时再核验”。北京时间2026-11-04 06:35（UTC2026-11-03 22:35）前，不再连接服务器或核验仿真，也不启动新EDA/板卡/实现/其他agent/wb/luyou及额外开发；自动goal接续不能提前复查，除非用户明确改期。保留原memory_repaired_full_20261103_r1运行，未发STOP，不改64GiB/48h保护。\n'
          '- 已通过automation_update创建并view核实一次安排5-t04，ACTIVE，06:35、COUNT=1，目标为本聊天；执行一次后暂停并核实，不能改为每5小时循环。此一次安排由用户最新请求授权，覆盖下方“无自动心跳”的旧默认，仅限此次延后核验。\n'
          '- 记录reports/memory_runtime_repair_20261103_r1/USER_WAIT_UNTIL_20261104.json。等待不代表目标完成或受阻；最后实测仍为01:33原进程身份匹配/7TV0B，截止后必须重新核实，不能将旧快照冒充当前。\n\n')
    agents=ROOT/'AGENTS.md';text=agents.read_text(encoding='utf-8');first,rest=text.split('\n',1)
    agents.write_text(first+'\n\n'+note+rest.lstrip('\n'),encoding='utf-8')
    resume=R/'RESUME.md';resume.write_text(note+resume.read_text(encoding='utf-8'),encoding='utf-8')
    summary=json.loads((R/'SUMMARY.json').read_text(encoding='utf-8'))
    summary.update(scheduling_state='USER_REQUESTED_WAIT_UNTIL',not_before_utc=record['not_before_utc'],
                   next_verification_beijing=record['not_before_beijing'],verification_automation_id='5-t04',
                   goal_turn_classification='PROGRESS_USER_REQUESTED_DEFERRED_VERIFICATION',
                   progress='User explicitly deferred verification five hours. One06:35 COUNT1 callback created/viewed; no remote stop or check sent after this request. Existing remote simulation retained.')
    (R/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(record,indent=2))
if __name__=='__main__':main()
