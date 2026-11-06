"""Rebuild the journal with the current dev-log renderer, preserving old facts.
The embedded JSON remains the maintenance source; this tool never runs EDA/FPGA.
"""
from pathlib import Path
import json,re,hashlib,copy,importlib.util,datetime,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=ROOT/'doc/log_rebuild_20261030';R.mkdir(exist_ok=True)
SKILL=Path('C:/Users/ben/.codex/skills/dev-log');PAGE=ROOT/'开发日志.html'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ev(label,path):return dict(label=label,href=path)
B=read(ROOT/'bak/BACKUP_20261030.json');original=Path(B['file']);assert sha(original)==B['sha256']
def data(p):return json.loads(re.search(r'<script id="dev-log-data" type="application/json">(.*?)</script>',p.read_text(encoding='utf-8'),re.S)[1])
old=data(original);d=data(PAGE);old_entries=copy.deepcopy(old['entries'])
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
board='module_14_lm_head_v4/reports/dual_board_20261030_r1/'
e_board=ev('两版真实板测及计时边界',board+'RESULT.md');e_review=ev('板测独立复核',board+'FINAL_INDEPENDENT_REVIEW.json')
e_quality=ev('实验10新99%门槛',board+'QUALITY_GATE_99.json')
e_stop=ev('d64保护停止快照','module_14_lm_head_v4/reports/full_bank_cosim_20261026_r1/RESULT.md')
e_gpu=ev('新旧各557配置GPU图','doc/design/V4Validation.html#gpu-summary')
e_root=ev('512MiB别名因果复现','module_14_lm_head_v4/reports/partial_rtl_20261026_diagnosis_r1/ROOT_CAUSE_REVIEW.json')
e_bank=ev('前5块独立RTL数组复核','module_14_lm_head_v4/reports/sim_memory_bank_20261026_r1/PREVIEW_REVIEW.json')
d['project'].update(name='LLM_FPGA · M14 lm_head',intro='AXU9EGB / XCZU9EG。保留完整词表v3.1基线，比较聚类＋低秩混合、融合超参、动态部分通道及量化路线。各路线的GPU质量、RTL数值、系统实现与实板性能分别验证。',phase='当前无执行；两套v4固定输入上板任务完成。T04 d64完整仿真资源问题待定位。',updated='2026-10-30',timezone='Asia/Shanghai',source='全部79条原始历史及稳定ID保留；新增10月24日至30日的本地真实报告。本页为离线快照，不轮询板卡或服务器。')
d.setdefault('completed_todos',[])
for item in old['todos']:
    tagged=dict(item,archived_on='2026-10-30',note='旧待办原文；当前状态见任务总览与路线。')
    if tagged not in d['completed_todos']:d['completed_todos'].append(tagged)
d['todos']=[dict(text='定位d64完整XSim的保护触发及内存增长；保留失败，先做有限模型改进再拟恢复。',status='阻塞'),dict(text='如推进集成，先定义真实逐token hidden/history接口与自回归测试；当前ABA只验证固定输入切换。',status='待验证'),dict(text='正式交付前分配版本身份并集成已验证的控制入口；板测证据ZIP不作为部署包。',status='待验证')]
def entry(id,date,title,status,summary,verification,evidence,**kw):
    item=dict(id=id,date=date,title=title,status=status,importance='重要成果',summary=summary,attempt='读取并复核该阶段原始报告与保存数组；不重新运行实验。',problem='无新增阻塞问题',solution='结论按实际验证范围记录，原失败保留。',verification=verification,next='按当前任务总览安排后续；不自动启动新任务。',tags=['lm_head v4'],evidence=evidence)
    item.update(kw)
    if not any(e['id']==id for e in d['entries']):d['entries'].append(item)
entry('20261024-all557-paired','2026-10-24','557配置新题补评与配对GPU图完成','已验证','新旧两组各557点；新1000题14956 decode零排除，后追加配置标为补充分析。','全557点参数逐项对应；133680次计时与660个dense哨兵，GPU不是FPGA/整网速度。',[e_gpu,ev('全557真实结果','module_14_lm_head_v4/reports/sparse_quality_all557_20261024_r1/RESULT.md')])
entry('20261024-partial-hls-r3','2026-10-24','d64/T4096最小原型：数值通过与HLS估计3.650ns','已验证','r1共享AXI综合失败、r2时序10.383ns失败保留；r3片上key/ID缓存调度变体通过。','正式Csim11有效调用、6负向门控及全数组独立复核；HLS预览II1、直方图II2。不是布线200MHz。',[ev('原型阶段C报告','doc/design/V4PartialHardware.html')],importance='关键突破')
entry('20261024-selector-rtl13','2026-10-24','选择器分段RTL13例通过','已验证','完整151936 keys/T4096，64位高地址、4KiB拆分、背压、平局、特殊ID及ABA覆盖。','4125212个保存32位值独立复核通过；分段不是完整联合RTL。',[ev('选择器13例审计','module_14_lm_head_v4/reports/partial_rtl_20261024_r1/r4/INDEPENDENT_REVIEW.json')])
entry('20261026-full-preview-fail','2026-10-26','原完整CoSim返回前5120预览值不一致','阻塞','全事务完成，但预览与候选数组不一致，官方原报告Fail；最终token相同不能代替逐位通过。','直接解析实际返回meta，151936预览中的5120值不同；原失败证据保留。',[ev('原完整失败复核','module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3/FAILURE_REVIEW.json')],importance='关键突破')
entry('20261026-xsim-alias-root','2026-10-26','确认XSim动态字节数组512MiB地址别名','已验证','两份BF16权重共520.40625MiB，尾部8814592字节覆盖仿真内存前缀。','不含lm_head的最小SV复现；按别名覆盖重建全部151936预览，与原错误RTL逐位相同。',[e_root],importance='关键突破',chain=[dict(label='症状',text='前5120词预览错误'),dict(label='定位',text='最小SV复现512MiB别名'),dict(label='修复',text='隔离小bank仿真模型'),dict(label='验证',text='单元及前5块通过；完整新资格仍未完成')])
entry('20261026-memory-bank-first5','2026-10-26','分bank模型与前5块预览独立验收通过','已验证','只修仿真存储；原RTL、FP32、随机停顿和FIFO不变。','2093事件单元回放，实际1522字节边界回读、40960权重拍、5120 raw/key、64 dims全对。',[e_bank,ev('分bank结果','module_14_lm_head_v4/reports/sim_memory_bank_20261026_r1/RESULT.md')])
entry('20261027-full-banked-stop','2026-10-27','修复模型的完整联合验证触发保护停止','阻塞','运行约17小时35分于06:14停止；原停止/超时/资源保护合并消息，具体触发项尚未确定。','末次200.007078ms模拟时间、完整事务0/1、7份返回均0B，无完整数值/FIFO资格；10月30日只读确认已退出。',[e_stop],problem='完整仿真未完成，不能以模拟时钟/进程活动证明正确或完成率。',next='先查保护触发与内存增长，不盲目重跑。')
entry('20261030-board-two-variants','2026-10-30','两套v4完成四类实板计时、稳定性与全数组验证','已验证','实验10在四固定输入上比早期混合方案快1.2103–1.3681倍；按新99%门槛质量达标。','8批共8264条记录、240计时/8000稳定；全预览/ID/raw/13guards逐位通过，两版ABA与各4预检通过。',[e_board,e_review,e_quality],importance='关键突破',impact='四类输入实板通过；实验10 M14等效输出22.02–31.07次/s。',next='真实自回归history/整网TTFT及正式交付另验；当前板卡无计算执行。')
entry('20261030-control-lessons','2026-10-30','XSCT成功判据、XSA解压与复位状态的控制经验','已验证','Windows批处理exit0不证明Tcl成功；loadhw会解压到XSA旁。','要求动作专属标志且无错误；每用例隔离运行副本；只接受精确held-reset/Already stopped状态。原绑定SHA保持。',[e_board,ev('终态与源SHA审计',board+'FINAL_INDEPENDENT_REVIEW.json')],category='经验与教训',tags=['经验与教训','XSCT','板卡控制'],context='Windows XSCT2021.1与已冻结上板包',cause='批处理未可靠传播Tcl退出码；loadhw生成附加文件；stop对已复位或已停CPU返回错误。',solution='用真实动作标志及原始记录判定；隔离副本承受解压副作用；已知状态精确处理，其他错误停止。')
entry('20261030-xsim-lessons','2026-10-30','大容量仿真内存需验证别名与资源边界','已验证','512MiB别名已确认并有限修复；完整分bank验证的资源问题仍未定位。','最小SV、全预览因果重建及前5块逐位通过；全事务尚未通过。',[e_root,e_bank,e_stop],category='经验与教训',tags=['经验与教训','XSim'],context='XSim2022.2的大动态logic字节数组',cause='已确认动态数组512MiB地址别名；停止触发项尚未确定。')
# Preserve every historical entry object, including unknown fields and text.
for old_entry in old_entries:assert next(x for x in d['entries'] if x['id']==old_entry['id'])==old_entry

x=d['exploration'];x.update(title='探索路线图',updated=now,snapshot_note='离线快照；10月30日两版板测结束，d64作业已停止。页面不查询实时设备。',summary='两套混合筛选版本实板固定输入验证完成；d64完整RTL保护停止；v4b仍为GPU研究。',badge='当前无执行',selected='R4Partial',current=[dict(value='8/8',label='两版四类实板批次通过'),dict(value='8000',label='稳定调用逐次一致'),dict(value='0/1',label='d64完整事务未完成')])
for stage in x['stages']:
    if stage['id']=='evaluation':stage['title']='性能评估'
routes={r['id']:r for r in x['routes']}
base=routes['R4Sparse'];base.update(lifecycle='completed',currentStage='evaluation',scope='早期v4 C128/R4/L16384＋rank128/Top16384；固定四类输入实板范围',outcome='四类固定输入、全数组、8000总稳定调用中的4000次、ABA与有限预检通过。',next='真实自回归history与正式发布资格另验。')
for k in ['board','evaluation']:base['cells'][k]=dict(state='verified',note='四类实板验证通过',detail='每类30计时/1000稳定，完整预览/ID/raw、ABA与有限预检；A53完整调用边界。',evidence=[e_board,e_review])
base['evidence']=[e_board,e_review,e_gpu]
base['design']['status_note']='固定四类输入实板验证通过；真实自回归history/整网decode/TTFT未测。'
base['design']['evidence']=[e_board,e_gpu]
base['design']['overview']='按路由→低秩→Top-K/并集→canonical精算运行，计算数据均在PL DDR。200MHz系统、两套版本四类固定输入实板检查已完成；不同K额外扩展及真实自回归链仍待验证。'
for node in base['design']['nodes']:
    if node['id']=='quality':node['detail']='固定算术独立1000题14958 decode：聚类80、低秩356、混合1漏选。10月30日四固定输入实板完整数组/稳定性通过；质量覆盖与实板数值是不同验证，整网TTFT未测。'
stages=[s['id'] for s in x['stages']]
def make_route(id,title,parent,life,scope,goal,outcome,notes,evidence,design):
    r=dict(id=id,title=title,parent=parent,lifecycle=life,currentStage='evaluation',scope=scope,goal=goal,outcome=outcome,next='按任务总览决定后续；当前无执行。',cells={k:dict(state=state,note=note,detail=note,evidence=evidence) for k,(state,note) in zip(stages,notes)},evidence=evidence,design=design)
    if id not in routes:x['routes'].append(r)
    else:routes[id].update(r)
    routes[id]=r
def design(overview,titles,contracts,evidence):
    return dict(overview=overview,status_note=contracts[0],nodes=[dict(id=f'n{i}',row=i//3,col=i%3,title=t,caption=c,detail=v) for i,(t,c,v) in enumerate(titles)],edges=[dict(source=f'n{i}',target=f'n{i+1}',label='数据/控制依赖') for i in range(len(titles)-1)],steps=[dict(title=t,nodes=[f'n{i}'],description=v) for i,(t,c,v) in enumerate(titles)],contracts=contracts,tradeoffs=['减少候选/预筛工作量与质量风险分别评估；GPU参考、HLS估计、实板性能分别记录。'],evidence=evidence)
make_route('R4Exp10','实验10：融合超参优化','R4Sparse','completed','C256/R4/L8192/rank64/Top16384','降低混合筛选与精算成本','新99%门槛达标；四类实板均快于早期v4。',[('verified','参数锁定；99%新门槛达标'),('verified','Csim与宿主通过'),('verified','HLS估计3.650ns'),('verified','完整中文RTL通过'),('verified','200MHz实现通过'),('verified','四类全数组/ABA通过'),('verified','四类30计时/1000稳定')],[e_board,e_quality],design('聚类256中心取4簇，每簇最多8192 ID；rank64低秩Top16384并集后canonical BF16精算。',[('hidden/history','同四个冻结输入','PL DDR保存BF16 hidden和history位图。'),('聚类路由','C256 / R4 / L8192','选最近4簇并收集有限ID。'),('低秩预筛','rank64 / Top16384','低秩投影、全词表预览与稳定Top-T。'),('升序去重并集','加入14特殊ID','路由ID、低秩ID及特殊ID合并。'),('canonical精算','原BF16权重','只读取候选行；固定FP32合同与penalty。'),('token输出','实板四类通过','返回token、score bits、CRC；A53完整调用计时。')],['实板固定输入范围通过，整网与真实逐token链未测。','原99.9%失败不改，新99%点门槛单列。'],[e_board,e_quality]))
make_route('R4Partial','动态部分通道 d64 / Top4096','R4Sparse','stopped','d64 / T4096 / B1024 / 双W','降低预筛扫描与候选精算成本','HLS与选择器/前5块通过；完整RTL保护停止，未上板。',[('verified','独立质量整体99.9465%'),('verified','原型11有效调用通过'),('verified','HLS估计3.650ns'),('failed','完整事务0/1，保护停止'),('planned','新系统未实现'),('planned','未上板'),('planned','实板未测')],[e_stop,e_bank,e_root],design('按动态通道选择做d64全词表近似预览，再稳定Top4096，最终canonical候选精算；保留两份权重布局。',[('通道选择','d=64','由当前hidden与冻结统计量选择通道。'),('分块预览W','B1024 / 额外副本','原通道顺序FP32流式归约。'),('Radix Top-T','T=4096','稳定key排序并入特殊ID。'),('canonical精算','原BF16 W','候选行精算语义不变。'),('仿真存储','分bank模型','修复512MiB别名；前5块通过。'),('完整RTL门槛','保护停止','17小时35分停止，7返回文件0B，无完整资格。')],['未取得完整RTL资格，不继承其他v4镜像板测结果。'],[e_stop,e_bank,e_root]))
make_route('R4GPUStudy','稀疏候选多方法 / 557配置','R4Sparse','completed','聚类/低秩/融合/部分通道/桶/LSH/dense','同组质量和配对GPU参考比较','新旧各557点与来源/划分/计时证据完成。',[('verified','方法及准入定义'),('verified','全部557数值与计数'),('na','本路线为GPU研究'),('na','具体硬件点另立路线'),('na','具体硬件点另立路线'),('na','不是板测'),('verified','配对GPU参考完成')],[e_gpu],design('不同预筛算法生成候选，统一canonical精算；同一配置在校准与新独立问题上配对评价。',[('公开问题','两组分别记录来源','新组1000题与旧校准组不同。'),('冻结配置','557点','全部ID/参数一一对应，追加点标补充分析。'),('候选生成','8类方法','保存逐步覆盖与真实K。'),('质量评价','整体及每类≥99%','沿dense轨迹的候选覆盖，不是问答准确率。'),('GPU计时','四固定输入','完整预筛与精算重算，常驻数据。'),('汇总图','召回×M14输出率','原/新组标签切换，来源及原始证据可追溯。')],['GPU参考不是FPGA或整网decode；已打开组不再用于调参认证。'],[e_gpu]))
v4b_ev=ev('v4b真实GPU质量结果','module_14_lm_head_v4b/reports/quantization_20261023_r1/RESULT.md')
make_route('R4bQuant','v4b：量化与量化预筛精算','R31PLDDR','waiting','W12直接量化 / W4预筛K512精算','降低权重搬运及计算成本','新质量与CPU/GPU通过；硬件核尚未开发。',[('verified','量化预算与锁点'),('verified','packed权重与GPU数值'),('planned','未开始'),('planned','未开始'),('planned','未开始'),('planned','未上板'),('verified','GPU参考；FPGA未测')],[v4b_ev],design('从v3.1出发的独立量化路线：直接量化输出与低比特预筛后BF16精算分别评价。',[('canonical BF16','父版本v3.1','冻结权重作为数值参考。'),('packed量化','RTN/GPTQ/AWQ-style','保存真实packed W与独立解包证明。'),('直接W12','独立质量99.9799%','允许少量token差异。'),('W4预筛','Top512','按量化近似分数选候选。'),('BF16精算','候选行','锁点新组14948 decode零漏选。'),('硬件适配','未开发','整数MAC、布局与新RTL/实现待研究。')],['仅CPU/GPU研究；不能继承v3.1或v4的硬件资格。'],[v4b_ev]))
entry('20261023-v4b-gpu-quality','2026-10-23','v4b量化与预筛精算完成首轮独立质量','已验证','直接W12在14948 decode错3次，W4预筛K512＋BF16精算零漏选。','真实packed权重与独立解包、CPU/GPU数值和新1000问题评估通过；硬件核/HLS/RTL/板卡尚未开展。',[v4b_ev])
routes['R4Partial']['cells']['rtl']['execution']=dict(snapshot_at='2026-10-30T18:55:39+08:00',location='STHL',host='nvidia-Super-Server',tool='Vitis_HLS / XSim 2022.2',cpu='停止时占用未记录',memory_limit='入口需200GiB可用；运行余量8GiB为保护门槛，不是实际RSS',current_task='已退出：stop/time/resource guard: xsim',progress='完整事务0/1；7返回文件0B',completed='通道选择、ID写回及前5块分段资格；完整预览无返回',elapsed='约17小时35分；48小时上限',scope='完整单输入未取得数值与FIFO资格',next='先定位触发项及仿真内存增长，不自动重跑',source='module_14_lm_head_v4/reports/full_bank_cosim_20261026_r1/FULL_WORKFLOW.json')
for id in ['R4Sparse','R4Exp10']:
    routes[id]['cells']['board']['execution']=dict(snapshot_at=read(ROOT/board/'PROCESS_AFTER.json')['observed_local'],location='本机 / AXU9EGB',tool='XSCT/Vivado/Vitis2021.1；已退出',progress='4/4固定输入，每类30计时＋1000稳定',completed='全数组、ABA、有限预检通过；当前A53/GEM停止、IP空闲',scope='不包括真实自回归history或整网TTFT',next='本轮完成，无自动后续',source=board+'FINAL_INDEPENDENT_REVIEW.json')

tasks=[('T01','完整词表基线与PL DDR迁移','已验证','verified',['R2017','R2021','RNumeric','RJTAG','RTCPInitial','RTCP','RDelivery','R250','R200','R200Layers','R31PLDDR'],'v2/v3/v3.1工程及交付历史保留','旧失败与不同计时范围分别记录'),('T02','稀疏方法GPU比较','已验证','verified',['R4GPUStudy'],'新旧各557点，质量/候选数/配对GPU速度','GPU参考，追加点为补充分析'),('T03','两套混合筛选方案上板','已验证','verified',['R4Sparse','R4Exp10'],'8批/240计时/8000稳定；全数组与ABA通过','固定四个校准输入，不是整网或自回归验收'),('T04','d64完整RTL资源问题定位','阻塞','blocked',['R4Partial'],'选择器/前5块通过；完整作业保护停止','当前无执行；具体保护触发项尚未确定'),('T05','v4b量化硬件可行性','待验证','pending',['R4bQuant'],'CPU/GPU独立质量与packed证明完成','新内核/HLS/RTL/板卡尚未开展')]
d['task_overview']=dict(title='任务进展总览',snapshot_at=now,note='当前没有后台计算。完成结果、验证边界与下一步分列；点击任务与路线可双向定位。',rows=[dict(id=i,task=t,task_label=i+' '+t,status=s,state=state,spec='H896 / V151936；具体输入与构建见证据',work=[dict(text=w)],scope=sc,route_ids=rs,evidence=e_board if i=='T03' else e_stop if i=='T04' else e_gpu if i=='T02' else v4b_ev if i=='T05' else ev('v3.1交付入口','deliverables/20261020_M14_V3_1_r1/M14_V3_1_20261020_r1/README_交付入口.md')) for i,t,s,state,rs,w,sc in tasks])

p=d['performance'];legacy_ids={m['id'] for m in p['metrics']}
for m in [dict(id='decode',label='M14等效输出率',unit='次/s',definition='单次M14输出一个token；1000 / A53完整调用Median_ms。30次测量，3次预热。'),dict(id='a53_median',label='A53完整调用Median',unit='ms'),dict(id='ttft',label='整网TTFT',unit='ms')]:
    if m['id'] not in legacy_ids:p['metrics'].append(m)
for v in p['variants']:
    if 'decode' not in v['values']:v['values']['decode']=1000/v['values']['ip_median'] if v['values'].get('ip_median') else None
    v['values'].setdefault('ttft',None)
    if '200mhz-candidate' not in v['id'] and v['values'].get('ip_median'):v.setdefault('specification',[dict(label='计时口径',value='历史IP计数换算；与新A53墙钟另组，不直接计算加速比',priority=True)])
p.update(title='M14局部性能快照',primary_metric_id='decode',default_variant='board-exp10-chinese',candidate_note='默认展示实验10中文固定输入。当前无后台执行；d64实板、整网decode及TTFT未测。切换版本可查看四类与历史基线。',method='本轮两版在同一板卡、同一A53完整control_call范围比较。权重加载、arena整份CRC和主机导出在计时外。不同输入/K分别显示，不把独立收益连成累计收益；历史IP计数不与A53墙钟直接相除。',evidence=[e_board,e_review,e_quality,e_gpu])
summary=read(ROOT/board/'BOARD_FIXED_INPUT_SUMMARY.json');points=[]
for row in summary['rows']:
    variant=row['variant'];case=row['case'];base_dir=M if variant=='baseline_hybrid' else M/'experiments/fusion_exp10_20261023';folder=base_dir/'reports/board_acceptance_20261030_r3'/case;execution=read(folder/'EXECUTION.json');stamp=datetime.datetime.fromisoformat(execution['finished']).astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds');name=('早期v4混合' if variant=='baseline_hybrid' else '实验10融合')+' · '+dict(chinese='中文',english='英文',code='代码',math='数学')[case];id='board-'+('early' if variant=='baseline_hybrid' else 'exp10')+'-'+case
    values={m['id']:None for m in p['metrics']};values.update(decode=row['m14_equivalent_outputs_per_s'],a53_median=row['median_ms'],a53_p95=row['p95_ms'])
    v=dict(id=id,label=name,scope='实板固定输入 · A53完整调用',measured_at=stamp,conditions='200MHz配置 / PL DDR；3预热＋30测量＋1000稳定调用。计时从A53控制调用到token/score/CRC校验返回；不含初始化、TCP、整arena CRC、JTAG导出或Transformer。全预览/候选raw逐位与ABA另测通过。',specification=[dict(label='输入/输出',value=f'H=896 / V=151936；固定hidden/history；K={row["candidate_count"]} → 单token',priority=True),dict(label='方案',value='C128/R4/L16384/rank128/Top16384' if variant=='baseline_hybrid' else 'C256/R4/L8192/rank64/Top16384'),dict(label='数据',value='原校准集四类冻结夹具之一；不是1000题质量集速度分布')],values=values)
    p['variants']=[o for o in p['variants'] if o['id']!=id]+[v]
    points.append(dict(id=id,label=name,variant_id=id,value=values['decode'],comparison_group='board-a53-20261030',workload_key=f'{case}-K{row["candidate_count"]}',workload_label=f'{case} / K{row["candidate_count"]}',measured_at=stamp,kind='独立筛选参数；候选计算量不同',conditions=v['conditions'],source=str((folder/'INDEPENDENT_REVIEW.json').relative_to(ROOT)).replace('\\','/')))
for v in p['variants']:
    if v['id']=='lm-head-v4-sparse-offline':v['label']='早期v4历史离线候选 · 当时未测（保留）'
p['history']=dict(groups={'board-a53-20261030':'同板A53完整调用 · 四类固定输入（不同K不连线）'},points=points)
# Back up generated route pages before explicitly authorized template rebuild.
design_backup=ROOT/'bak'/'design_before_20261030';design_backup.mkdir(exist_ok=True)
for route in old['exploration']['routes']:
    source=ROOT/route.get('design_page','missing');target=design_backup/source.name
    if source.is_file() and not target.exists():shutil.copy2(source,target)
spec=importlib.util.spec_from_file_location('current_dev_log_renderer',SKILL/'scripts/render_log.py');renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
from journal_scheme_performance_20261030 import prepare as prepare_scheme_view,apply as apply_scheme_view
prepare_scheme_view(d,ROOT)
renderer.validate(d)
files=renderer.generate(d,PAGE,force=True)
apply_scheme_view(PAGE)
new=data(PAGE)
assert all(next(e for e in new['entries'] if e['id']==v['id'])==v for v in old_entries)
assert set(old)<=set(new)
report=dict(state='REBUILT_PRESERVING_ALL_HISTORICAL_ENTRIES',backup=B,old_entries=len(old_entries),new_entries=len(new['entries']),old_ids_preserved=True,unknown_top_fields_preserved=True,renderer=str(SKILL/'scripts/render_log.py'),renderer_sha256=sha(SKILL/'scripts/render_log.py'),skill_sha256=sha(SKILL/'SKILL.md'),generated_files=files,board_or_server_operations='NONE',visual='PENDING')
(R/'BUILD_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
