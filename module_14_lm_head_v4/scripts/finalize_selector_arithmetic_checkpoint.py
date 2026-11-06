"""Update checkpoint docs only after the independently audited stage exists."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json
M=Path(__file__).resolve().parents[1];ROOT=M.parent;R=M/'reports'
def main():
    result=json.loads((R/'SELECTOR_ARITHMETIC_STAGE_20261021.json').read_text(encoding='utf-8'))
    assert result['state']=='INDEPENDENT_COMPONENTS_AND_C_CHAIN_PASS'
    for file,digest in result['source_sha256'].items():assert hashlib.sha256((M/file).read_bytes()).hexdigest()==digest
    now=datetime.now(timezone(timedelta(hours=8))).isoformat();p=M/'PROGRESS.json';d=json.loads(p.read_text(encoding='utf-8'))
    d.update(updated=now,stage='P4_COMPONENTS_AND_C_CHAIN_VERIFIED_INTEGRATION_PENDING',
      active_work='NONE: own HLS/RTL/GPU/C-chain jobs completed; no automatic background continuation',runtime_processes='NONE',
      next='Integrate actual selector control/status and64bit PL-DDR scratch/address/alias checks, full selector RTL and system200MHz STA/CDC; board needs new exclusive arrangement')
    d['milestones']['P4']='PASS_COMPONENTS: lowrank Csim5+10+3 and RTL3; router Csim6+10+2 and RTL3; linked C-chain4 full candidate raw logits/token/score/CRC PASS; host29. Both new components HLS3.650ns, no full selector HLS/RTL or P&R.'
    d['selector_quality']='CPU_R2B_HISTORICAL_RECALL_PASS; new arithmetic calibration-only audit PASS, not recertified holdout'
    d['dependencies']=['Full selector control/status/scratch/alias/64bit PL-DDR integration pending',
      'Full selector RTL and complete system STA/CDC pending; new components lack P&R',
      'Revised arithmetic has calibration audit only; opened holdouts cannot be reused to tune/certify',
      'No FPGA board access authorized; upstream direct weights deferred']
    d['arithmetic_components']=result['components'];d['arithmetic_stage_report']='reports/SELECTOR_ARITHMETIC_STAGE_20261021.json'
    for file in ['reports/SELECTOR_ARITHMETIC_STAGE_20261021.json','reports/SELECTOR_ARITHMETIC_STAGE_20261021.md','reports/failure_router_bitstore_20261021/EVIDENCE.json','reports/hls_selector_chain_csim_r3_20261021.log']:
        if file not in d['evidence']:d['evidence'].append(file)
    temp=p.with_suffix('.tmp');temp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
    heading='## 2026-10-21 低秩/路由独立核与完整C链完成（当前最新）'
    paragraph=heading+'''\n\n- 主模型完成低秩、聚类路由两个独立HLS组件，各3事务Verilog/XSim协同仿真PASS；HLS均估计3.650ns，未做这两核P&R。\n- 低秩CSim5正确/10非法/3非有限，路由6正确/10非法/2非有限；29项host测试PASS。四类真实完整C流程串接路由→低秩→Top-K/并集→canonical候选精算，所有候选raw logits及dense轨迹token/score bits/CRC一致。\n- 低秩A扫描采用8路beat树与独立16路context流水归约，理想供数16拍/行；全词表A扫描预算12.15488ms@200MHz，非整核/板上decode。\n- 路由r1曾Csim通过但RTL位图丢位（8527→2501，tie18→4）；已改为完整128bit缓存mask OR写回，r2正式RTL通过。失败源码预处理/RTL输出和日志保留，禁止部署r1。\n- 新固定算术模型仅重做同校准集4775decode，聚类/低秩/混合漏选15/84/0、路由顺序变化0；没有打开holdout调参或重新宣称独立质量通过。历史r2b99.9933%为原CPU实现结果，不能自动继承为新RTL质量。\n- 所有本轮HLS/XSim/GPU/C链作业已结束，无后台续跑；无FPGA操作，旧wb/心跳不恢复。\n- 证据：module_14_lm_head_v4/reports/SELECTOR_ARITHMETIC_STAGE_20261021.*；续办：doc/LM_HEAD_V4_HANDOFF_20261021.md。下一步完整selector硬件调度、PL DDR地址/别名/容量合同、整链RTL与系统200MHz/CDC；板测仍需新安排。\n\n'''
    agent=ROOT/'AGENTS.md';text=agent.read_text(encoding='utf-8');assert heading not in text
    prefix,rest=text.split('\n',1);agent.write_text(prefix+'\n\n'+paragraph+rest.lstrip('\n'),encoding='utf-8')
    handoff=ROOT/'doc/LM_HEAD_V4_HANDOFF_20261021.md';old=handoff.read_text(encoding='utf-8')
    new='''# lm_head v4 离线续办检查点\n\n## 最新：低秩/路由组件及完整C串接通过\n\n时间：'''+now+'''。主模型作业均已结束；无后台任务、不操作或探测板卡，不恢复旧wb/luyou/心跳。\n\n- 首先读module_14_lm_head_v4/PROGRESS.json及reports/SELECTOR_ARITHMETIC_STAGE_20261021.md/.json。\n- 新增router/lowrank独立top，固定参数未拟合；各CSim/HLS及3事务RTL PASS。新HLS均3.650ns估计，不是P&R。\n- 四类完整C链对全词表preview、候选ID/全部候选raw logits以及dense token/score/CRC验证通过；只是C函数串接，不是完整RTL或真实DDR系统。\n- 新算术全校准集4775 decode：route15/lowrank84/hybrid0漏选、路线顺序变化0。GPU显式算术模型与四类完整NumPy/CSim preview逐位一致；不把模型审计冒充4775笔RTL。\n- 路由r1 RTL曾真实失败，同字节bit-store丢位；r2整128位cache-mask修复后官方RTL PASS。原始证据在reports/failure_router_bitstore_20261021，r1禁用于后续集成。\n- 低秩内部A扫描达到一beat/拍，16beat/行，理想12.15488ms；含DDR/其余阶段的完整decode仍未测。\n\n## 下一步：完整selector硬件与PL DDR系统\n\n1. 设计真正父级调度/状态与错误传播，将4组件连接为系统；目前selector_chain_csim_unit.cpp只是测试用unity编译单元，不能导出当完整硬件top。\n2. 冻结64位PL DDR布局、参数包/BT无损转置SHA、norms512B、排名列表、scratch容量/对齐/别名与不可变合同；A53软件可留PS DDR，计算数据不得回退。\n3. 完整selector数值/RTL验证，注意lowrank非有限A可能部分写preview，必须以本次status门控后续Top-K；routed/union头最后发布。\n4. 完整PL DDR BD的200MHz实现/CDC/STA、身份/bit/XSA/PS init/ELF/loader配套；独立候选核的历史OOC不能覆盖新增三核。\n5. 新算术若做独立泛化认证，另留新测试问题组；旧holdout/r2b均已打开，禁止用于选型/重复认证。新板卡独占安排前不探测、不上板。\n6. 真正计时覆盖route+lowrank+Top-K+union+candidate+policy+schedule；v4 token/s/ms/token/TTFT均NOT_RUN。\n\n详见module_14_lm_head_v4/HLS_SELECTOR_ARITHMETIC.md。上游直接供权重仍等待总负责人框架文档。\n\n---\n\n## 以下为16:43历史检查点（由上文覆盖当前状态）\n\n'''
    handoff.write_text(new+old,encoding='utf-8')
    readme=M/'README.md';text=readme.read_text(encoding='utf-8');anchor='## 当前可验证成果'
    block='''## 最新离线阶段（低秩/路由与C链）\n\n低秩与路由独立核均已通过CSim、HLS与3事务RTL；修复路由r1在RTL中的同字节位图丢位。\n四类完整C链的候选ID、全部候选raw logits、dense token/score/CRC通过。\n同校准集4775 decode的新固定顺序模型漏选数仍为15/84/0，但不是新独立质量认证。\n本轮组件没有P&R或完整selector RTL/系统STA，板上decode/TTFT仍未测。\n详见[阶段报告](reports/SELECTOR_ARITHMETIC_STAGE_20261021.md)与[算术/接口说明](HLS_SELECTOR_ARITHMETIC.md)。\n当前全部自有作业结束，无后台续跑。下方保留此前阶段历史成果。\n\n'''
    readme.write_text(text.replace(anchor,block+anchor,1),encoding='utf-8')
    execution=ROOT/'doc/LM_HEAD_V4_EXECUTION_20261021.md'
    with execution.open('a',encoding='utf-8') as f:f.write('\n\n## 后续阶段：低秩/路由独立RTL与完整C流程\n\n'+paragraph.split('\n\n',1)[1]+'详细阶段证据与各事务周期见上述报告；未进行完整系统HLS/P&R或板卡操作。\n')
    print('CHECKPOINT_UPDATED own_jobs_finished no_hardware')
if __name__=='__main__':main()
