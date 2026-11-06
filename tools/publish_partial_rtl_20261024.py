from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import hashlib,json,re,statistics
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    selector=read(R/'r4/INDEPENDENT_REVIEW.json');assert selector['state']=='PASS_SELECTOR_RTL_FULL_ARRAYS_AND_AXI_STALLS'
    full=read(R/'full_r3/FULL_WORKFLOW.json') if (R/'full_r3/FULL_WORKFLOW.json').exists() else dict(state='NOT_RUN')
    qualification=read(R/'full_r3/INDEPENDENT_REVIEW.json') if (R/'full_r3/INDEPENDENT_REVIEW.json').exists() else None
    snapshot_paths=sorted((R/'full_r3/observations').glob('*/RUNTIME_SNAPSHOT.json'))
    snapshots=[read(p) for p in snapshot_paths]
    snapshot_path=snapshot_paths[-1] if snapshot_paths else None
    snapshot=snapshots[-1] if snapshots else None
    diagnosis_path=R/'full_r3/diagnostics/20261025_dsp_r1/WARNING_DIAGNOSIS.json'
    diagnosis=read(diagnosis_path) if diagnosis_path.exists() else None
    verdict='完整联合 RTL 通过（单个真实输入）' if qualification else ('完整联合 RTL 运行中' if full['state']=='EXECUTING' else '完整联合 RTL 待复核/未通过')
    state='SELECTOR_PASS_FULL_RTL_PASS_SINGLE_CASE' if qualification else 'SELECTOR_PASS_FULL_RTL_PENDING'
    if diagnosis and not qualification and full['state']=='EXECUTING':
        verdict='完整联合 RTL 运行中，DSP告警待核验';state='SELECTOR_PASS_FULL_RTL_RUNNING_WITH_DSP_WARNINGS'
    failure_path=R/'full_r3/FAILURE_REVIEW.json'
    failure=read(failure_path) if failure_path.exists() else None
    if full['state']=='FAILED_NO_AUTOMATIC_RETRY':
        assert not qualification,'Failed official CoSim cannot carry a passing qualification'
        verdict='完整联合 RTL 已结束，数值验证失败';state='SELECTOR_PASS_FULL_RTL_NUMERICAL_FAIL'
    alias_path=R.parent/'partial_rtl_20261026_diagnosis_r1/ROOT_CAUSE_REVIEW.json'
    alias=read(alias_path) if alias_path.exists() else None
    if alias:
        assert failure and alias['aliased_reconstruction_mismatches']==0
        verdict='完整CoSim失败：已定位XSim仿真内存地址别名';state='FULL_COSIM_FAIL_SIMULATOR_ALIAS_ROOT_CAUSE_CONFIRMED'
    bank_dir=R.parent/'sim_memory_bank_20261026_r1'
    bank_unit=read(bank_dir/'UNIT_REVIEW.json') if (bank_dir/'UNIT_REVIEW.json').exists() else None
    bank_preview=read(bank_dir/'PREVIEW_WORKFLOW.json') if (bank_dir/'PREVIEW_WORKFLOW.json').exists() else None
    bank_input=read(bank_dir/'FULL_TV_INPUT_REVIEW.json') if (bank_dir/'FULL_TV_INPUT_REVIEW.json').exists() else None
    bank_review=read(bank_dir/'PREVIEW_REVIEW.json') if (bank_dir/'PREVIEW_REVIEW.json').exists() else None
    if bank_unit:
        verdict='仿真内存分bank单元通过；完整RTL资格仍待验证'
        state='BANK_MEMORY_UNIT_PASS_COMPLETE_RTL_PENDING'
        if bank_preview and bank_preview['state'].startswith('EXECUTING_'):
            verdict='仿真内存分bank单元通过；前5块RTL检查进行中';state='BANK_MEMORY_UNIT_PASS_PREVIEW5_RUNNING'
        if bank_preview and bank_preview['state']=='FAILED_NO_AUTOMATIC_RETRY':
            verdict='仿真内存单元通过；前5块检查失败，保留现场';state='BANK_MEMORY_UNIT_PASS_PREVIEW5_FAILED'
        if bank_review:
            verdict='仿真内存单元及前5块RTL通过；完整CoSim仍待验证';state='BANK_MEMORY_UNIT_AND_PREVIEW5_PASS_COMPLETE_RTL_PENDING'
    full_bank_dir=R.parent/'full_bank_cosim_20261026_r1'
    full_bank=read(full_bank_dir/'FULL_WORKFLOW.json') if (full_bank_dir/'FULL_WORKFLOW.json').exists() else None
    full_bank_numeric=read(full_bank_dir/'NUMERIC_REVIEW.json') if (full_bank_dir/'NUMERIC_REVIEW.json').exists() else None
    if full_bank:
        verdict='前5块RTL独立验收通过；完整联合验证执行中';state='PREVIEW5_PASS_FULL_BANKED_VALIDATION_RUNNING'
        if full_bank['state']=='FAILED_NO_AUTOMATIC_RETRY':
            verdict='前5块RTL通过；完整联合验证失败，待定位';state='PREVIEW5_PASS_FULL_BANKED_VALIDATION_FAILED'
        elif full_bank_numeric:
            verdict='单输入完整数值复核通过；有限FIFO资格待审核';state='FULL_BANKED_NUMERIC_PASS_FIFO_PENDING'
    rows=''.join(f'<tr><td>{c["index"]+1}</td><td>{escape(c["name"])}</td><td>{c["K"]}</td><td>{c["cycles"]:,}</td><td>逐位通过</td></tr>' for c in selector['cases'])
    base='../../module_14_lm_head_v4/reports/partial_rtl_20261024_r1/'
    links=[('r4/INDEPENDENT_REVIEW.json','13例独立数组复核'),('r4/simulate.log','实际逐例RTL日志'),('r4/PLAN.json','选择器冻结入口与源SHA'),('r4/PROCESS_AFTER.json','选择器终态与进程审计'),('full_r3/PLAN.json','完整CoSim冻结入口')]
    for name,title in [('full_r3/FULL_WORKFLOW.json','完整CoSim真实状态'),('full_r3/INDEPENDENT_REVIEW.json','完整CoSim独立审计'),('full_r3/cosim.log','完整CoSim日志')]:
        if (R/name).exists():links.append((name,title))
    for i,p in enumerate(snapshot_paths):links.append((str(p.relative_to(R)).replace('\\','/'),'只读观测'+str(i+1)+'与实际背压配置'))
    pressure_model=read(R/'PRESSURE_SCALE_MODEL.json') if (R/'PRESSURE_SCALE_MODEL.json').exists() else None
    if pressure_model:links.append(('PRESSURE_SCALE_MODEL.json','压力开销量级模型（非实测）'))
    if diagnosis:links.append((str(diagnosis_path.relative_to(R)).replace('\\','/'),'DSP告警诊断：样本、原语条件与未决结论'))
    if failure:
        links.extend([('full_r3/FAILURE_REVIEW.json','完整CoSim返回数组失败复核'),('full_r3/PROCESS_AFTER.json','完整作业退出与133份源SHA审计'),('full_r3/tool_artifacts/sim/report/lm_head_v4_partial_proto_cosim.rpt','官方CoSim最终Fail报告')])
    if alias:
        links.extend([('../partial_rtl_20261026_diagnosis_r1/ROOT_CAUSE_REVIEW.json','512MiB别名根因与完整预览逐位复现'),('../partial_rtl_20261026_diagnosis_r1/alias_minimal/alias_diag.sv','不含lm_head的最小SV复现'),('../partial_rtl_20261026_diagnosis_r1/alias_minimal/r2.log','最小复现实际XSim日志'),('../partial_rtl_20261026_diagnosis_r1/STAGE_CHAIN_REVIEW.json','排序及候选精算逐段复核'),('../partial_rtl_20261026_diagnosis_r1/r6/AXI_TRACE_REVIEW.json','有限输入对照实际AXI与写回'),('../partial_rtl_20261026_diagnosis_r1/PROCESS_AFTER.json','定位阶段全部进程停止与冻结源审计')])
    if bank_unit:
        for name,title in [('UNIT_REVIEW.json','分bank单元2093事件独立回放'),('PREVIEW_PLAN.json','前5块冻结验证范围'),('FULL_TV_INPUT_REVIEW.json','全原始TV权重SHA重建'),('PREVIEW_WORKFLOW.json','前5块工具阶段快照'),('PREVIEW_REVIEW.json','前5块完整数组独立审计')]:
            if (bank_dir/name).exists():links.append(('../sim_memory_bank_20261026_r1/'+name,title))
    if full_bank:
        for name,title in [('PLAN.json','本次完整联合验证冻结范围'),('FULL_WORKFLOW.json','本次完整联合验证状态快照'),('NUMERIC_REVIEW.json','本次完整实际返回数值复核')]:
            if (full_bank_dir/name).exists():links.append(('../full_bank_cosim_20261026_r1/'+name,title))
        links.extend([('../perf_observer_20261026_r1/INDEPENDENT_REVIEW.json','阶段/AXI计数器独立审计'),('../range_observer_20261026_r1/INDEPENDENT_REVIEW.json','实际AXI地址检查器独立审计'),('../postcheck_control_20261026_r1/RESULT.json','原C后检查器正负控制')])
    evidence=''.join(f'<li><a href="{base}{name}">{title}</a></li>' for name,title in links)
    details=escape(json.dumps(qualification,ensure_ascii=False,indent=2)) if qualification else '<p>尚无完整RTL PASS结论。查看冻结入口与实际工作流；进程存活、C参考通过或包装器exit0均不能代替RTL通过。</p>'
    if failure:
        details='<p class="note">2026年10月26日00:33（北京时间），官方完整CoSim结束并报Fail：CSIM_FAIL full preview bits RTL_full_chinese。作业已退出、无活动锁，133份冻结源SHA未变；没有自动重跑或后续实现。</p><p>直接比较官方RTL返回TV与C参考及冻结夹具：词ID 0–5119（前5个1024词块）的5120个预览值、5120个排序键不一致，其余词的预览与键相同。候选列表4033个位置不同；集合中参考独有316词、RTL独有316词。64个通道ID、最终token/score/CRC及候选数4109相同，仍不能覆盖完整数组失败。</p><p>根因未定位，不能将预览差异直接归因于后续精算路径的DSP告警。实际返回TV已保存；参考阶段生成的actual文件不能冒充RTL实际输出。单次压力模型延迟83748670周期不是FPGA实测decode速度。当前不具备完整RTL或200MHz实现资格。</p>'
    if alias:
        details=details.replace('根因未定位，不能将预览差异直接归因于后续精算路径的DSP告警。','根因已通过独立最小仿真及全部预览数组重建定位为XSim动态字节数组地址别名。实际4109个候选raw已与canonical逐位一致，原DSP告警不构成本次预览差异根因。')
    if full_bank:
        details='<p><strong>以下保留原full_r3失败记录；本次修复模型后的完整运行是另一份独立证据，当前状态见下方“本次完整联合验证”。</strong></p>'+details
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>lm_head v4 · RTL验证</title>
<style>body{margin:0;background:#f4f6f2;color:#243c38;font:16px/1.75 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:32px 20px}section{background:white;border:1px solid #dce4dd;border-radius:16px;padding:26px;margin:20px 0}h1{line-height:1.4}a{color:#176557}table{border-collapse:collapse;width:100%}td,th{text-align:left;border-bottom:1px solid #dce4dd;padding:9px}th{background:#edf3ed}.note{border-left:5px solid #ad8747;padding:12px 18px;background:#faf3df}.ok{color:#286f58}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}.steps{display:flex;flex-wrap:wrap;gap:10px}.steps span{padding:9px 14px;background:#eaf3ec;border-radius:6px}small{color:#61716c}</style>
<main><a href="V4Validation.html#gpu-summary">← 返回GPU/质量汇总</a><h1>lm_head v4：选择器分段RTL与完整联合RTL</h1><p>固定动态部分通道 d64 / Top4096 / B1024 / 双份 BF16 权重；STHL Vitis HLS / Vivado 2022.2。工程验证不改变既有质量结果。</p>
<section><h2 class="ok">选择器 13 / 13 例通过</h2><p>独立复核共 4,125,212 个保存的32位值；候选ID、表头、末拍填充、输入键与全部guard逐位一致。A→B→A完整工作区一致。</p><p class="note">当前FPGA实测decode效率：未测。选择器周期只覆盖筛选分段及行为AXI停顿；不等于整次M14/整网decode，也不是200MHz布局布线通过。</p></section>
<section><h2>VERDICT</h2><div class="steps"><span>动态通道64维</span><span>全151936词FP32预览</span><span>稳定Top4096＋14特殊ID</span><span>canonical BF16候选精算</span></div><p>完整测试使用同一冻结old_chinese真实hidden/history及真实双份权重；这是原8状态回归中的一个固定输入，不是新采集问题集，也不重新认证质量。完整Csim已有11次有效调用、6负向门控；RTL范围以本页独立审计为准。</p><p>克隆已完成的r3综合，只替换测试台。官方CoSim启用binary TV、random_stall和DATAFLOW profiling；不启用FIFO自动扩容。权重FIFO128、ID/context/raw FIFO32保持原设计。完整测试需核对64通道、151936预览raw与policy键、4109候选ID/精算raw及token/score/CRC。</p>FULLDETAIL</section>
<section><h2>选择器是怎样测的</h2><p>直接实例化已冻结r3生成的radix模块和同份meta AXI适配器，没有重新综合或改数值。每例输入全部151936个键，T固定4096，最终并入特殊ID151643–151656；词ID升序输出，相同分数取较小ID。</p><p>AXI地址从0x400000ff0开始，超过32位且逼近4KiB边界。存储模型限制为读写各一个未完成事务，在AR/R/AW/W/B通道设置确定性停顿，周期性700拍停顿。监测地址/数据停顿稳定性、burst长度、WLAST、4KiB边界、越界及完整工作区。它不是物理DDR时序模型，也不用于推导带宽。</p><p>13例合计读493792拍、写13373拍；AR背压1027652周期、R供数间隙516474周期、AW背压1468周期、W背压42272周期、B应答延迟1430周期；1937次读突发从4KiB边界起始。</p><div style="overflow:auto"><table><thead><tr><th>用例</th><th>输入/边界场景</th><th>实际K</th><th>该模型周期</th><th>完整内存对照</th></tr></thead><tbody>ROWS</tbody></table></div></section>
<section><h2>数据来源与验证边界</h2><p>8个真实状态复用原校准集/新独立集已固定的中、英、代码、数学hidden/history；原始来源、冻结版本、问题划分与质量结果见<a href="V4Validation.html#gpu-summary">双数据集GPU汇总图</a>。零hidden和三个排序边界是构造向量。它们用于工程等价验证，没有用已打开测试组调参。</p><p>原型质量仍为已保存新组整体99.9465%、最低类别99.8381%；不能据此声称所有输出dense无损。HLS估计3.650ns仍只是综合估计。新200MHz实现、BSP/ELF、板卡、多步板测、整网decode/TTFT均未完成。</p><p>前三次选择器测试入口失败（漏两依赖、空闲done采样）和完整CoSim r1绝对项目名失败均保留；测试台修复不改变核RTL、模型或向量。</p></section>
<section><h2>可复查证据</h2><ul>EVIDENCE</ul><a href="V4PartialHardware.html">前一阶段：Csim/HLS资源与时序估计</a></section></main></html>'''
    if snapshot:
        progress=snapshot['last_progress'];stamp=escape(snapshot['observed_at_china'])
        pressure='<section><h2>压力配置与历史观测 · '+stamp+'</h2><p>官方random_stall实际生成meta、weights两个master的地址/数据/响应通道延迟回调：每次取0～256拍，权重读数据逐拍调用。它是背压压力测试，不是正常DDR带宽模型。</p><p>该观测时模拟时钟已推进到'+str(progress['simulation_time_ms'])+' ms，完成事务'+str(progress['completed_transactions'])+'/'+str(progress['total_transactions'])+'。日志中的'+str(progress['latency_vs_estimate_percent'])+'%是“已耗周期/HLS估计周期”，不是完成百分比。没有据此估算剩余时间或decode速率。</p><p>观测保存了实际生成的模型、工作流/日志快照和73份冻结综合文件SHA核对。运行中的条件和FIFO均未更改，没有新启仿真或自动200MHz实现。这里的毫秒是模拟时间，不是主机运行耗时。</p></section>'
        history=''.join('<tr><td>'+escape(s['observed_at_china'])+'</td><td>'+str(round(s['workflow_elapsed_wall_seconds']/3600,2))+' 小时</td><td>'+str(s['last_progress']['simulation_time_ms'])+' ms</td><td>'+str(s['last_progress']['completed_transactions'])+'/'+str(s['last_progress']['total_transactions'])+'</td></tr>' for s in snapshots)
        pressure=pressure.replace('</section>','<p>模拟时钟推进只说明仿真引擎继续运行，不能单独证明AXI数据传输进度或某个计算阶段已完成；需等待最终返回与FIFO监测。</p><div style="overflow:auto"><table><thead><tr><th>观测时间（北京时间）</th><th>主机运行时长</th><th>日志最近模拟时间</th><th>完整事务</th></tr></thead><tbody>'+history+'</tbody></table></div></section>')
        details+=pressure
    page=page.replace('VERDICT',verdict).replace('FULLDETAIL',('<pre>'+escape(json.dumps(qualification,ensure_ascii=False,indent=2))+'</pre>'+pressure) if qualification and snapshot else (('<pre>'+details+'</pre>') if qualification else details)).replace('ROWS',rows).replace('EVIDENCE',evidence)
    if pressure_model:
        cost_panel='<section><h2>为什么本轮压力测试会很慢</h2><p>固定夹具预览权重读取1,220,608拍，4109候选精算再读460,208拍，共1,680,816个128位权重数据拍。生成的随机延迟分布允许每拍停顿0～256周期。</p><p>若按分布项的相加权重、独立抽样和逐拍串行延迟建立抽象模型，平均每拍插入约42.67周期；仅权重读通道的“传输＋随机间隔”量级约7339.6万周期，即5ns模拟时钟下约367ms。这解释了压力周期可能远大于无停顿HLS估计；它不是实际总延迟，也没有包含所有计算、仲裁和重叠。</p><p class="note">不能用当前模拟时间除以367ms计算完成率，也不能据此承诺剩余主机时间或排除死锁。最终以真实AXI计数、返回数组和FIFO报告判定。正常decode性能须使用另行明确的性能测试条件或实板计时。</p></section>'
        page=page.replace('<section><h2>可复查证据</h2>',cost_panel+'<section><h2>可复查证据</h2>')
    if diagnosis:
        warning_panel='<section><h2>DSP告警历史观测 · '+escape(diagnosis['observed_at_china'])+'</h2><p>日志出现'+str(diagnosis['opmode_warning_count'])+'条DSP48E1 OPMODE含X告警，首次模拟时间'+str(diagnosis['first_warning_sim_time_ms'])+'ms，最近告警'+str(diagnosis['last_warning_sim_time_ms'])+'ms。路径包括候选精算的点积和归约；周期性进度打印为'+str(diagnosis['last_periodic_sim_time_ms'])+'ms，和告警事件时间的采样频率不同。</p><p class="note">该观测中没有匹配到UVM_ERROR/UVM_FATAL/CSIM_FAIL或明确死锁报错，但7份返回文件仍为0字节。原语源码在非法控制模式时设置output_x_sig并发出Warning；是否影响有效输出尚未核对，不能简单认定无害或宣告失败，也不能把相关路径活动当作正确完成。</p><p>全部告警及压力条件保留，未屏蔽告警、改FIFO或重启EDA；最终结论须结合返回数组和FIFO报告。经验库未命中同类记录。</p></section>'
        page=page.replace('<section><h2>可复查证据</h2>',warning_panel+'<section><h2>可复查证据</h2>')
    if alias:
        alias_panel='''<section id="alias-root-cause"><h2>已定位：仿真内存超过512MiB后发生地址别名</h2><p class="note">这次完整CoSim读到了被仿真模型覆盖的权重。原Fail保留；不能据此判定lm_head计算逻辑有错，也不能直接改成RTL通过。定位阶段诊断已全部退出，133份冻结源SHA未变，无板卡操作；后续分bank门控见下一节。</p><table><thead><tr><th>权重</th><th>容量</th><th>仿真地址范围（字节，末端不含）</th></tr></thead><tbody><tr><td>分块预览W</td><td>260.75 MiB</td><td>0 → 273416192</td></tr><tr><td>canonical精算W</td><td>259.65625 MiB</td><td>273416192 → 545685504</td></tr><tr><td>合计</td><td>520.40625 MiB</td><td>跨过536870912（512 MiB）边界</td></tr></tbody></table><div class="steps"><span>canonical尾部8,814,592字节</span><span>地址相差0x20000000发生别名</span><span>覆盖预览W开头8.40625MiB</span><span>影响前5个词表块</span></div><p>原生成模型使用logic[7:0]动态数组存储字节。在同机同版XSim 2022.2最小SV中，先写0x1200=0x12，再写0x20001200=0x34，两个位置均读回0x34；该复现完全不含lm_head。</p><p>按这个地址覆盖关系重建权重并计算全部151936词预览，与原RTL返回值<strong>151936 / 151936逐位一致</strong>，包括原先5120个差异。覆盖4个完整分块及第5块前720个通道，其中52个被本输入选中，因此第5块全部1024词也受影响。</p><p>有限输入因果对照保留原RTL、原随机停顿，仅提供前7块可达数据以避免地址别名：第1块64次突发、8192拍AXI数据全部正确，首个128位预览写回4个FP32值与参考一致。该对照只到第一个写回，不是完整配置RTL资格。原失败的排序键、稳定Top4096及4109个实际候选canonical精算均与其实际输入一致。</p><p>下一步应在新隔离仿真环境中将大动态数组拆为小bank，先验证512MiB及高地址边界不别名，再测试受影响预览块，最后重做完整CoSim。保持d64/Top4096、数值合同与核RTL不变；200MHz实现和板测仍未进行。</p></section>'''
        page=page.replace('<section><h2>可复查证据</h2>',alias_panel+'<section><h2>可复查证据</h2>')
    if bank_unit:
        phase=bank_preview['state'] if bank_preview else 'NOT_RUN'
        stage='前5块尚未完成，等待完整VCD及边界回读结果。'
        if bank_review:stage='前5块5120个raw、5120个key、64通道及40960拍权重已独立逐位核对通过。'
        if phase=='FAILED_NO_AUTOMATIC_RETRY':stage='前5块门控失败，现场已保留；不得自动重复启动。'
        inp='原全量TV身份检查待完成。'
        if bank_input:inp='原始34105344拍TV已全部解码，两份权重SHA与冻结BF16文件完全一致；没有截短输入。'
        panel='<section id="bank-memory-fix"><h2>分bank仿真内存修复 · 当前阶段</h2><p>每个独立小数组最多1048576个元素，按需分配；保留未写地址X、读写标记、越界及批量访问语义。核RTL、算法参数、原随机停顿及FIFO保持原样。</p><p><strong>单元检查通过：</strong>512组相差512MiB地址独立，32/128位和X/Z断言通过；2093条实际事件经独立回放一致，15次边界拒绝及13次X返回正确（11次越界、2次未写）。</p><p>'+inp+'</p><p>完整权重加载后还需从实际模型回读1522个边界字节，覆盖每bank端点、512MiB和两权重分界；这是边界回读，不能冒充全模型SHA。</p><p>工具阶段快照：<code>'+escape(phase)+'</code>；'+stage+'</p><p class="note">本轮只观察同一输入的前5个受影响块，到第6块首个地址请求即停。全部前5块通过后才能决定完整联合CoSim；原官方Fail保留，不自动实现或板测。页面中的运行阶段是保存快照，实时状态以远端PREVIEW_WORKFLOW和实际日志为准。</p></section>'
        page=page.replace('<section><h2>可复查证据</h2>',panel+'<section><h2>可复查证据</h2>')
    if full_bank:
        panel='<section id="full-bank-validation"><h2>本次完整联合验证 · 2026-10-26</h2><p><strong>前5块门控已独立通过：</strong>5120个预览raw、5120个key、64通道、40960拍权重读取及1522个模型边界字节均正确；原133份冻结源不变，前5块作业已退出。</p><p>本次阶段快照：<code>'+escape(full_bank['state'])+'</code>，启动UTC '+escape(full_bank['started'])+'。采用同一old_chinese真实输入、d64/Top4096/B1024/双W/debug1及原强随机停顿，权重FIFO128/其余原有限FIFO保持。被动阶段和地址观察器均无输出，不驱动DUT。</p><p>直接执行原HLS生成的XSIM与原C后检查程序，复用完整原TV并修复仿真存储；不再生成覆盖修复的模型。cosim_design格式化报告未重新生成，不复制旧报告或伪标官方Pass。工具返回后仍需全部151936预览/key、完整候选/raw/标量及实际FIFO报告独立复核。</p><p>新输出目录不放任何预生成actual；正/负控制证明原C后检查器能接受正确完整数组，并拒绝仅preview一位错误而标量不变的情况。返回TV不包含额外end guard，实际读写越界、4KiB、长度/对齐、高位/溢出及权重写由已验证的被动AXI检查器覆盖。</p><p class="note">当前没有新的完整RTL通过、正常decode测速或200MHz实现结论。此轮是强压力功能验证；阶段周期和AXI拍数另存CSV。48小时/内存余量8GiB/STOP_REQUESTED保护，不自动ABA、性能测试、实现或上板。</p></section>'
        page=page.replace('<section><h2>可复查证据</h2>',panel+'<section><h2>可复查证据</h2>')
    path=ROOT/'doc/design/V4PartialRTL.html';path.write_text(page,encoding='utf-8')
    nav=ROOT/'doc/design/V4Validation.html';before=nav.read_text(encoding='utf-8');embedded=re.findall(r'<script[^>]*>.*?</script>',before,re.S)
    section='<section class="panel" id="partial-rtl-review"><h2>RTL验证：选择器13例通过</h2><p>'+verdict+'。已保存完整工作区、AXI停顿统计和失败记录；这些结果不等于FPGA实测decode速度。</p><p><a href="V4PartialRTL.html">查看RTL场景、实际数组及完整联合验证进展 →</a></p></section>'
    if 'id="partial-rtl-review"' in before:after=re.sub(r'<section class="panel" id="partial-rtl-review">.*?</section>',lambda _:section,before,flags=re.S)
    else:
        anchor=re.search(r'<section class="panel" id="partial-hardware-review">.*?</section>',before,re.S);assert anchor;after=before[:anchor.end()]+section+before[anchor.end():]
    assert embedded==re.findall(r'<script[^>]*>.*?</script>',after,re.S);nav.write_text(after,encoding='utf-8')
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.href=[]
        def handle_starttag(self,t,a):
            d=dict(a)
            if t=='a':self.href.append(d['href'])
            assert not (t in ['script','img','iframe'] and d.get('src'))
    parser=Links();parser.feed(page)
    for s in parser.href:
        u=urlsplit(s);assert not u.scheme;assert (path.parent/unquote(u.path)).exists(),s
    result=dict(state=state,selector_review_sha256=sha(R/'r4/INDEPENDENT_REVIEW.json'),full_workflow=full,full_qualification=qualification,
                page=str(path.relative_to(ROOT)).replace('\\','/'),page_sha256=sha(path),local_links=len(parser.href),external_dependencies=0,
                embedded_validation_scripts_unchanged=True,browser_visual='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
    if snapshot:
        result['runtime_observation']=snapshot;result['runtime_observation_sha256']=sha(snapshot_path)
        result['runtime_observation_history']=[dict(path=str(p.relative_to(R)).replace('\\','/'),sha256=sha(p),observed_at=read(p)['observed_at_china']) for p in snapshot_paths]
    if pressure_model:result['pressure_scale_model_sha256']=sha(R/'PRESSURE_SCALE_MODEL.json')
    if diagnosis:result['dsp_warning_diagnosis']=diagnosis;result['dsp_warning_diagnosis_sha256']=sha(diagnosis_path)
    if failure:result['full_failure_review']=failure;result['full_failure_review_sha256']=sha(failure_path)
    if alias:result['simulator_alias_root_cause']=alias;result['simulator_alias_root_cause_sha256']=sha(alias_path)
    if bank_unit:result['bank_memory_unit_review']=bank_unit;result['bank_preview_workflow_snapshot']=bank_preview;result['bank_preview_review']=bank_review
    if full_bank:result['full_bank_workflow_snapshot']=full_bank;result['full_bank_numeric_review']=full_bank_numeric
    (R/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (R/'RESULT.md').write_text('# d64 / Top4096 RTL验证\n\n选择器13例及4125212个保存值独立复核通过；'+verdict+'。\n\n不代表FPGA/整网decode速度或200MHz实现通过。完整范围、失败记录、实际数组与入口SHA见同目录RESULT.json及doc/design/V4PartialRTL.html。\n',encoding='utf-8')
    print(json.dumps(dict(state=state,links=len(parser.href),embedded_scripts_unchanged=True)))
if __name__=='__main__':main()
