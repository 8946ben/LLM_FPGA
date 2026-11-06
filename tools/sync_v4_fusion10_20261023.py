"""Experiment10 design/results in the journal's single canonical snapshot."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,itertools,json,os,re,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/fusion_exp10_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else None

def atomic_journal_write(path,expected_sha,text):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected_sha,'Concurrent journal edit; preserve and retry publishing'
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='dev-log-exp10-',suffix='.tmp',delete=False) as f:
        f.write(text);f.flush();os.fsync(f.fileno());temp=Path(f.name)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected_sha,'Concurrent journal edit; prepared temp preserved'
    os.replace(temp,path)
def main():
    plan=read(R/'PLAN.json');assert plan
    expected_journal_sha=hashlib.sha256((ROOT/'开发日志.html').read_bytes()).hexdigest()
    file=ROOT/'开发日志.html';text=file.read_text(encoding='utf-8');match=re.search(r'(<script id="dev-log-data" type="application/json">)(.*?)(</script>)',text,re.S);d=json.loads(match[2]);old=copy.deepcopy(d['entries']);v=d['v4_validation'];progress=read(R/'PROGRESS.json') or dict(stage='准备中');cal=read(R/'CALIBRATION.json') or dict(configurations=read(R/'CALIBRATION.partial.json') or []);gpu=read(R/'GPU_BENCHMARK.json') or dict(configurations=[]);cl={x['id']:x for x in cal['configurations']};bl={x['id']:x for x in gpu['configurations']};base=plan['baseline'];variants=[]
    axes=[['中心数C','C'],['选簇数R','R'],['每簇上限L','L'],['低秩维度r','r'],['预筛Top-T','T']]
    for values in itertools.product(*[plan['grid'][k] for k in ['C','R','L','r','T']]):
        p=dict(zip(['C','R','L','r','T'],values));key='_'.join(f'{k}{p[k]}' for k in p);c=cl.get(key);b=bl.get(key);result={}
        if c:result.update(misses=c['quality']['decode']['misses'],recall=c['quality']['decode']['recall']*100,K_mean=c['candidate_decode']['mean'],logical_mib=c['logical_mean_decode_bytes']/2**20)
        if b:result.update(gpu_ms=b['wall_median_ms'],gpu_rate=b['equivalent_m14_per_s'])
        tags=[label for label,axis in axes if all(p[k]==base[k] for k in p if k!=axis)]
        variants.append(dict(id=key,title=f'C{p["C"]} / R{p["R"]} / L{p["L"]} / r{p["r"]} / T{p["T"]}',short_label=key,parameters=p,axes=tags,configuration=[f'聚类C{p["C"]}/最近R{p["R"]}簇，每簇最多L{p["L"]}；低秩r{p["r"]}/Top-T{p["T"]}', '两分支与14特殊ID做原始global ID升序去重并集，再用canonical BF16权重精算'],expected='逐点真实并集质量/K；入围点实际GPU计时；锁定点另做新独立质量及硬件资格',status='校准/GPU完成' if c and b else '校准完成' if c else '待运行',results=result))
    metrics=[dict(id='misses',label='校准decode漏选',unit='次',digits=0,direction='越少越好'),dict(id='recall',label='校准decode召回',unit='%',digits=4,direction='越高越好'),dict(id='K_mean',label='decode真实K均值',unit='行',digits=2,direction='质量约束下越少越好'),dict(id='logical_mib',label='理论主要读取量均值',unit='MiB',digits=2,direction='逻辑预算，非实测流量'),dict(id='gpu_ms',label='GPU完整参考调用中位',unit='ms',digits=3,direction='越少越好'),dict(id='gpu_rate',label='GPU参考等效M14输出率',unit='次/s',digits=2,direction='越高越好')]
    for m in metrics:m['scope']='校准320问题/4775decode；GPU仅入围点4固定输入，不是总体/FPGA性能'
    qwork=read(R/'QUALITY_WORKFLOW.json') if (R/'QUALITY_WORKFLOW.json').exists() else None
    qprogress=read(M/'data/hidden_fusion10_20261023/holdout/PROGRESS.json');qresult=read(R/'FINAL_QUALITY.json')
    eda=read(R/'EDA_PROGRESS.json');hardware=read(M/'experiments/fusion_exp10_20261023/reports/board_v4_20261021/hardware_audit_r2.json');rtl=read(R/'RTL_QUALIFICATION.json');package=read(R/'OFFLINE_PACKAGE_AUDIT.json');result=read(R/'RESULT.json');workflow=read(R/'OFFLINE_WORKFLOW.json');finished=bool(package and result and result['state']=='OFFLINE_TESTS_COMPLETED_QUALITY_FAIL_NO_RELEASE')
    if eda:progress=dict(stage=eda['stage'])
    if workflow and workflow['stage']=='STOPPED_ON_ERROR_OR_USER_PAUSE':progress=dict(stage='EXP10_STOPPED_OFFLINE_STAGE_FAILED_OR_PAUSED')
    if finished:progress=dict(stage='OFFLINE_TESTS_COMPLETE_QUALITY_FAILED_NOT_RELEASE')
    phase_names={'EXP10_OFFLINE_RTL_SIMULATION':'完整RTL仿真运行中','EXP10_SHORT_COSIM_C_TRANSACTIONS':'RTL输入事务准备中','EXP10_CREATE_FULL_PL_DDR_BD':'新PL DDR系统搭建中','EXP10_200MHZ_IMPLEMENTATION':'200MHz完整系统实现中','EXP10_MATCHING_BSP_AND_ELFS':'匹配BSP及两ELF构建中','EXP10_EXPORT_IP':'私有IP导出中','EXP10_OFFLINE_ASSET_BINDING':'离线资产配套审计中','OFFLINE_TESTS_COMPLETE_QUALITY_FAILED_NOT_RELEASE':'离线测试结束，质量未通过','EXP10_PAUSED_BY_USER':'已安全暂停，无活动EDA','EXP10_STOPPED_OFFLINE_STAGE_FAILED_OR_PAUSED':'离线阶段已停止，需检查报告'}
    phase_label=phase_names.get(progress['stage'],progress['stage'])
    qstatus=(qresult['state'] if qresult else f'采集{qprogress.get("completed",qprogress.get("prompts",0))}/1000' if qprogress else qwork['stage'] if qwork else '未完成')
    stages=[['432点真实并集校准',f'{len(cl)}/432完成'],['入围GPU/1000次稳定性','已完成' if (R/'GPU_STABILITY.json').exists() else '未完成'],['参数锁定','已完成' if (R/'SELECTION_LOCK.json').exists() else '未完成'],['全新1000问题','已完成·质量未通过' if qresult and not qresult['selected']['proposed_point_gate'] else qstatus],['Csim/HLS综合','已通过' if (R/'HLS_SYNTHESIS_AUDIT.json').exists() else '未完成'],['完整RTL','已通过' if rtl else phase_label],['200MHz系统','已通过' if hardware and hardware['state']=='PASS_OFFLINE_SYSTEM' else '未完成'],['配套离线包','已核验·研究用' if package else '未完成'],['板卡','本轮不做']]
    report=dict(symbol_text='C/R/L/r/Top-T',parameter_keys=['C','R','L','r','T'],plot_axes=axes,data_heading='数据来源、校准选择与全新最终组',parameters=[['C / 聚类中心数','128','64 / 128 / 256 / 512','复用同训练集已拟合中心和长列表；不以新问题训练。'],['R / 最近选簇数','4','2 / 4 / 8','决定路由分支覆盖和访问的训练列表。'],['L / 每簇列表上限','16384','4096 / 8192 / 16384','实际有效长度=min(L,n_i)，不是强行用满L。'],['r / 低秩维度','128','32 / 64 / 128','只取同一已核对主基前缀；复用已逐位合格因子及归约。'],['Top-T / 低秩截取数','16384','2048 / 4096 / 8192 / 16384','T不是最终K；实际K是两分支及14特殊ID的去重并集。']],
        baseline='冻结对照：C128/R4/L16384 + r128/Top16384。dense、对照各单分支、冻结融合和入围融合点在同轮GPU口径下比较。',
        source_report='原训练1500问题只用于已拟合中心/列表；原calibration320问题/4775decode用于搜索。新最终组1000问题（中400/英250/代码64/数学286）已按整题去除全部旧保留组，标签仅在选择/数值入口锁定后采集。代码使用剩余64个HumanEval任务，数学补至286；来源版本/配额/去重在采集前冻结。',
        bound_rows=[['融合互补机制','最终漏选=路由漏选∩低秩漏选。训练列表看不到的词可以由低秩补回；两者不是质量分数加权。'],['真实K','432个点均逐位合并151936词位图，再popcount；不把route_K+T当实际K。重叠量也单列。'],['选型质量','门槛为整体及每类decode≥99.9%；校准选择再要求全部5095预测零漏选、无dense fallback。旧已打开测试不参与。'],['容量与硬件边界','仅r≤128，估算320MiB arena，并限制K P95≤V/2及max≤3V/4。参数变化仍需新Csim/RTL/实现；旧bit资格不自动继承。'],['GPU与FPGA','GPU为固定FP32 Eager参考，供同轮对照；FPGA目标按逻辑主要读取量筛选，再做真实HLS/实现。不把GPU速度外推硬件。']],
        scan_rows=[['A 融合网格','4×3×3×3×4=432点','同一train/cal、因子、算术与policy','全部实际并集/质量/K/交集，不打开新测试。'],['B 入围与GPU','全局逻辑成本前5＋每rank最低成本点，至多8个','另加冻结融合/各单分支/dense控制','每输入3 warmup+30测量，交错顺序；1000次变输入功能调用。'],['C 最终锁点与新质量','从合格入围点按逻辑读取量最小选1点','选择、代码、来源及入口先锁定','一次新独立1000问题；质量失败保留，不回头调新测试。'],['D 选定点离线硬件','功能/错误路径、RTL、200MHz实现与布局检查','PL DDR计算路径、canonical精算不变','只为选定点做完整硬件资格，保留旧已封存实现。']],scan_count=f'执行前锁定432个网格点，不无限扩扫。当前校准完成{len(cl)}点。',
        controls=[plan['fixed'],plan['training']],data_protocol=[plan['calibration'],plan['final_test_policy'],'新最终问题配额与来源见data/fusion10_quality_20261023/MANIFEST.json；不执行HumanEval参考解。'],evaluation=['每点整体/分类decode、首输出和问题级全步覆盖；独立报告两分支各自漏选及同时漏选。','每点真实K mean/median/P95/max、重叠量、逻辑主要读取量与估算容量；实际AXI流量及板测未测。','GPU完整M14参考调用及数值证明；选定点CPU/GPU/Csim/RTL、错误与多步、200MHz/CDC/资产配套分别记录状态。'],budgets=[['逻辑主要读取量',plan['byte_model']],['资源限制','320MiB arena；最终布局按实际对齐/guard/源区容量重新验证。']],outputs=['参数对照、入围点质量/速度并列图、K/交集与逻辑成本Pareto、锁定记录、新问题结果及离线硬件报告；未测不填0。'])
    g=dict(id='hybrid-hyperparameters',title='实验10 · 聚类＋低秩融合调参的质量、速度与硬件可行性',status='进行中',stage_status=stages,importance=dict(level='必须完成',kind='核心研究 / 融合选型与离线资格',reason='实验8说明训练支持集存在漏词上界；实验9说明单低秩加预算可能抵消速度。必须研究互补与并集成本。',minimum='432点校准、入围GPU、锁点新独立质量、选定配置Csim/RTL/200MHz及离线配套验证。',extension='板卡不在本轮；若独立质量失败不调参复认证，明确保留失败及未完成项。',order='严格按校准→锁点→新标签；重EDA顺序进行，不触碰板卡。'),question='能否利用聚类与低秩的互补漏选，减少rank或Top-T、控制并集K，同时通过质量门槛并降低可实现硬件的计算/访存成本？',changing='联合变化C/R/L/r/Top-T；每次只在固定算术的候选构建前改变预算，最终canonical精算不变。',fixed=report['controls'],variants=variants,metrics=metrics,sweep_report=report,fusion_report=True,
        decision=f'当前{progress["stage"]}；校准{len(cl)}/432。尚无实验10新独立质量或硬件完成结论。',next='完成真实并集校准与入围GPU，冻结最终配置；再做全新问题及选定配置离线硬件，不操作板卡。',scope='研究调参和离线资格，不是发布或板卡验收；GPU是M14局部参考，不是整体LLM decode/TTFT。',evidence=[])
    hls=read(R/'HLS_SYNTHESIS_AUDIT.json');host=read(R/'HOST_QUALIFICATION.json');engineering=[['当前工程阶段',phase_label],['FPGA局部/整网decode与TTFT','未测；本轮不连接板卡']]
    if eda and eda.get('last_observed_simulation_ps') and not rtl:engineering.append(['最近可见RTL观察',f'{eda.get("last_observed_stage", "未记录")}；仿真绝对时刻至少{eda["last_observed_simulation_ps"]/1e9:.6f}ms。墙钟快照{eda["updated"]}；不是整次调用耗时、百分比或物理板卡计时。'])
    if hls:engineering.extend([['HLS估计时序',f'{hls["hls_estimated_ns"]:.3f}ns；目标5ns/uncertainty1.35ns，尚须系统布线确认'],['HLS资源',f'{hls["resources"]["BRAM_18K"]} BRAM18K / {hls["resources"]["DSP"]} DSP；非全系统资源'],['真实Csim','5次四类/生产/A→B→A调用＋2验证；24预检拒绝、5运行错误门控通过']])
    if host:engineering.append(['宿主与布局/身份',f'{host["python_tests"]}项Python/Tcl、25fake-MMIO、88组loader对齐长度；纯mock/本机文件，非目标测试'])
    if rtl:
        c=rtl['transactions'][0];engineering.extend([['RTL单中文debug',f'{c["cycles"]}周期 / {c["model_ms_at200MHz"]:.6f}ms @200MHz；{200000000/c["cycles"]:.4f}等效M14输出/s'],['RTL适用范围','仅K17764单固定输入/AXI仿真模型；完整preview/ID/raw/token/score/CRC和重叠拒绝。不是生产模式、总体P95或实际MIG性能。']])
    if hardware:engineering.extend([['完整200MHz系统',f'{hardware["state"]}；WNS{hardware["wns_ns"]:+.3f}ns、WHS{hardware["whs_ns"]:+.3f}ns、WPWS{hardware["wpws_ns"]:+.3f}ns'],['结构与报告边界','双AXI64计算仅到PL DDR；内部未约束端点/CDC Critical/MIG警告单独审计，非零警告承诺或板测。']])
    if package:engineering.append(['离线配套','匹配bit/XSA/PS init/BSP/两ELF、四类本机320MiB镜像及研究包SHA已核验；不是发布ZIP'])
    g['fusion_engineering']=dict(rows=engineering,scope='质量失败与工程验证独立记录；既有冻结v4/交付封存未被此研究配置替换。')
    pareto=read(R/'PARETO_CALIBRATION_VIEW.json')
    if pareto:
        assert pareto['calibration_sha256']==hashlib.sha256((R/'CALIBRATION.json').read_bytes()).hexdigest()
        g['fusion_pareto']=pareto
    shortlist=read(R/'SHORTLIST.json')
    if shortlist:
        candidates=[]
        for i,row in enumerate(shortlist['configurations'],1):
            variant=next(x for x in variants if x['id']==row['id']);candidates.append(dict(variant={**variant,'title':f'F{i} · '+variant['title'],'short_label':f'F{i}'},result=variant['results']))
        for key,label in [('frozen_hybrid','冻结融合'),('cluster_only','仅聚类对照'),('lowrank_only','仅低秩对照'),('dense','完整dense')]:
            row=shortlist['baseline'];out={};timing=bl.get(key)
            if key=='dense':out.update(misses=0,recall=100.,K_mean=151936)
            elif key=='frozen_hybrid':out.update(misses=row['quality']['decode']['misses'],recall=row['quality']['decode']['recall']*100,K_mean=row['candidate_decode']['mean'])
            else:
                misses=row['route_only_decode_misses' if key=='cluster_only' else 'lowrank_only_decode_misses'];out.update(misses=misses,recall=(1-misses/4775)*100)
            if timing:out.update(gpu_ms=timing['wall_median_ms'],gpu_rate=timing['equivalent_m14_per_s'])
            candidates.append(dict(variant=dict(title=label,short_label={'frozen_hybrid':'旧融合','cluster_only':'仅聚类','lowrank_only':'仅低秩','dense':'dense'}[key],id=key),result=out))
        g['fusion_shortlist']=dict(records=candidates,selected=(read(R/'SELECTION_LOCK.json') or {}).get('chosen'),scope='质量来自同一校准320问题/4775decode；GPU来自同轮4夹具/30测量，不是同一统计总体。dense质量为定义对照。F编号对应下方完整参数表。')
    if (R/'SELECTION_LOCK.json').exists():
        selected=read(R/'SELECTION_LOCK.json');g['decision']=f'已锁定{selected["chosen"]}，校准全部5095预测零漏选。选定配置真实Csim通过与否单列，当前新质量状态：{qstatus}。未宣称RTL、200MHz或板卡完成。';g['next']='按冻结入口完成新问题质量；随后串行完成选定配置RTL、200MHz系统、离线主机/软件/资产资格。失败保留，不用新问题回调参数。'
    if qresult:
        fresh=[]
        for key,label in [('selected','实验10锁定点'),('frozen_baseline','冻结融合对照')]:
            q=qresult[key];z=q['report']['decode'];fresh.append(dict(variant=dict(title=label,short_label=label),result=dict(misses=z['misses'],recall=z['recall']*100),categories=[[cat,c['steps'],c['misses'],c['recall']*100] for cat,c in z['by_category'].items()],gate=q['proposed_point_gate']))
        g['fusion_fresh']=dict(records=fresh,source='全新1000完整问题：CMMLU中文400、Dolly英文250、HumanEval代码64、GSM8K数学286；先锁参数和数值入口，再首次采集标签。共14986个decode步，零排除；最多16输出，penalty=1.1；按整题规范化哈希排除全部旧训练/校准/保留组。精确去重不能排除语义相似或预训练污染。',scope='质量是沿canonical dense固定轨迹的赢家覆盖，不是自由生成任务准确率、无损保证或整网TTFT；与4775步校准数据分开统计。新组已打开，禁止用它调参或再次认证。',decision='实验10锁定点漏19次，中文11/英文7/代码0/数学1，整体和中英未达99.9%门槛；冻结融合对照漏2次、各类均过门槛。保留质量失败，不发布此锁点。')
        originals=next(x for x in v['comparisons'] if x['id']=='quality')['report']['source_rows'];g['fusion_fresh']['source_rows']=copy.deepcopy(originals)
        quotas={'chinese':400,'english':250,'code':64,'math':286}
        for row in g['fusion_fresh']['source_rows']:
            category={'中文':'chinese','英文':'english','代码':'code','数学':'math'}.get(row['category'],row['category']);row['count']=quotas[category]
        g['decision']=g['fusion_fresh']['decision']+' 校准零漏选未推广到新问题。硬件资格独立继续，不用工程通过替代质量通过。'
        g['next']='串行完成锁定点RTL/200MHz、主机协议/镜像/匹配软件离线资格；质量失败不回调此测试组，不操作板卡。'
        if not any(x['id']=='20261023-v4-fusion-exp10-new-quality-fail' for x in d['entries']):
            d['entries'].append(dict(id='20261023-v4-fusion-exp10-new-quality-fail',date='2026-10-23',title='实验10校准零漏选未推广：新问题decode漏19次',status='已验证',importance='重要成果',summary='锁点C256/R4/L8192+r64/T16384在全新1000问题/14986decode漏19，99.8732%，未达门槛；同组预声明冻结融合对照漏2、99.9867%，各类过门槛。',attempt='完成432点真实并集、入围GPU及1000次变输入后，先锁参数/数值入口，再首次生成全新测试标签。',problem='整体及中英分项未达99.9%点门槛；校准零漏选不保证新问题覆盖。',solution='保留质量失败及包装器R/r解析故障，不重跑或调新测试；继续独立的工程资格研究。',verification='新质量数组/各类计数/并集身份/来源和预留去重独立复核通过；不是质量门槛通过、自由生成或板测。',next=g['next'],tags=['v4','实验10','新独立质量','质量失败'],evidence=[dict(label='新质量独立复核',href='module_14_lm_head_v4/reports/fusion_exp10_20261023_r1/FINAL_QUALITY_REVIEW.json')]))
    for label,p in [('执行前冻结计划',R/'PLAN.json'),('真实进度',R/'PROGRESS.json'),('全新问题预留',M/'data/fusion10_quality_20261023/MANIFEST.json'),('逐点校准',R/'CALIBRATION.json'),('校准成本/漏选/交集边界图数据',R/'PARETO_CALIBRATION_VIEW.json'),('入围列表',R/'SHORTLIST.json'),('同轮GPU',R/'GPU_BENCHMARK.json'),('参数选择锁',R/'SELECTION_LOCK.json')]:
        if p.exists():g['evidence'].append(dict(label=label,href=p.relative_to(ROOT).as_posix()))
    if finished:
        g['status']='已完成';g['next']='保留冻结融合基线；锁点质量未通过，不发布。下一轮新方法/参数须使用新的预声明方案及未打开最终组。板卡仍不在本轮。'
        g['decision']+=' 选定点完整RTL、200MHz系统及匹配软件/资产离线审计已完成；真实FPGA与整网decode/TTFT未测。'
        if not any(x['id']=='20261023-v4-fusion-exp10-offline-complete' for x in d['entries']):d['entries'].append(dict(id='20261023-v4-fusion-exp10-offline-complete',date='2026-10-23',title='实验10离线测试结束：工程链通过，选定点质量未通过',status='已验证',importance='重要成果',summary=g['decision'],attempt='按预定432点校准、入围GPU、锁点、新独立问题、Csim/HLS/完整RTL/200MHz和配套软件顺序验证。',problem='新质量漏19/14986，未达99.9%整体及分项门槛；原始工具/路径失败全部保留。',solution='不发布失败锁点，不用已打开组重新选点认证；通过的硬件/软件只作为研究证据独立封存。',verification='完整逐位RTL及原C后校验、STA/CDC/DRC、匹配XSA/BSP/两ELF、四类本机arena及SHA包审计通过；未操作FPGA。',next=g['next'],tags=['v4','实验10','离线完成','质量失败'],evidence=[dict(label='完整离线结果',href='module_14_lm_head_v4/reports/fusion_exp10_20261023_r1/RESULT.md')]))
    elif progress['stage']=='EXP10_PAUSED_BY_USER':
        g['status']='已暂停';g['decision']+=' 已按用户断电要求安全暂停，无活动续建/EDA；完整系统布局未完成。';g['next']='等待用户明确恢复；先读pause_20261023/CHECKPOINT.json，复用完成综合/opt检查点，另立实现续办脚本与日志。不要重跑已完成RTL/GPU/新质量或操作板卡。'
        stages[6][1]='已暂停·布局未完成'
        if not any(x['id']=='20261023-v4-fusion-exp10-user-poweroff-pause' for x in d['entries']):d['entries'].append(dict(id='20261023-v4-fusion-exp10-user-poweroff-pause',date='2026-10-23',title='实验10安全暂停：完整综合与opt检查点已保存',status='已验证',importance='重要成果',summary='用户要求断电；先停止续建父流程，再停止所属Vivado树，复核无残留。完整RTL及IP资格通过；系统9子IP/顶层综合及opt完成，布局未完成，无新bit/XSA/BSP/ELF或最终时序结论。',attempt='保留首轮导出暂存/版本号溢出和BD旧VLNV失败，修复后依次完成私有IP、拓扑、综合与opt。',problem='用户断电暂停于place_design Phase4.1，未生成placed/routed检查点；质量锁点19/14986漏选仍失败。',solution='保留11份检查点及中断日志，opt DCP ZIP CRC/SHA通过，设置STOP_REQUESTED，不自动恢复。',verification='PROCESS_AFTER无续建/EDA残留；未连接或操作板卡。暂停通过不代表未完成工程阶段通过。',next=g['next'],tags=['v4','实验10','安全暂停'],evidence=[dict(label='断电续办检查点',href='module_14_lm_head_v4/reports/fusion_exp10_20261023_r1/pause_20261023/CHECKPOINT.json')]))
    elif progress['stage']=='EXP10_STOPPED_OFFLINE_STAGE_FAILED_OR_PAUSED':
        g['status']='已停止';g['decision']+=' 当前离线流程已停止，未完成项不能标为通过。';g['next']='读取OFFLINE_WORKFLOW.json与EDA_PROGRESS.json的真实错误/暂停原因，查明后续办；不重测独立质量或操作板卡。'
    for label,p in [('校准并集/排序独立复核',R/'CALIBRATION_REVIEW.json'),('GPU原始计时/1000次功能复核',R/'GPU_REVIEW.json'),('选定硬件派生与完整金标',R/'HARDWARE_DERIVATION.json'),('真实Csim记录',R/'HLS_CSIM.json'),('HLS综合与源身份',R/'HLS_SYNTHESIS_AUDIT.json'),('37宿主测试/25fake-MMIO/身份复核',R/'HOST_QUALIFICATION.json'),('新问题入口冻结',M/'data/fusion10_quality_20261023/EVALUATION_ENTRY_LOCK.json'),('新质量流程状态',R/'QUALITY_WORKFLOW.json'),('新独立质量结果',R/'FINAL_QUALITY.json'),('新质量计数/来源独立复核',R/'FINAL_QUALITY_REVIEW.json'),('原始公开源重建整题/提示哈希',R/'PUBLIC_SOURCE_RESERVATION_REVIEW.json'),('已打开组19漏选的描述性记录',R/'FRESH_MISS_DIAGNOSTICS.json'),('RTL完整比对/原C后校验',R/'RTL_QUALIFICATION.json'),('200MHz系统审计',M/'experiments/fusion_exp10_20261023/reports/board_v4_20261021/hardware_audit_r2.json'),('匹配离线软件/资产包',R/'OFFLINE_PACKAGE_AUDIT.json')]:
        if p.exists():g['evidence'].append(dict(label=label,href=p.relative_to(ROOT).as_posix()))
    existing=next((i for i,x in enumerate(v['comparisons']) if x['id']==g['id']),None)
    if existing is None:v['comparisons'].append(g)
    else:v['comparisons'][existing]=g
    if not any(x['id']=='20261023-v4-fusion-exp10-start' for x in d['entries']):d['entries'].append(dict(id='20261023-v4-fusion-exp10-start',date='2026-10-23',title='实验10启动：融合432点真实并集与完整离线资格',status='进行中',importance='重要成果',summary='由实验8/9设计C/R/L/r/Top-T融合网格432点；先校准和入围GPU，锁点后使用全新1000问题并做硬件离线资格。板卡不在本轮。',attempt='复用训练中心/列表与同一主基BF16因子，逐点位图并集，不用K上界替代实际K。',problem='单聚类有支持集漏词，单低秩高预算成本偏高；不能从单分支独立最优拼出融合最优。',solution='固定网格、门槛、入围规则、逻辑成本及新问题协议，实际跑全点并集和互补漏选，再验证少量候选。',verification='当前仅状态快照与已有完成证据，不把未测新质量/RTL/板卡写为通过。',next=g['next'],tags=['v4','实验10','融合调参'],related=['20261023-v4-hyperparameter-joint-complete'],evidence=[dict(label='实验10',href='doc/design/V4Validation.html#hybrid-hyperparameters')]))
    assert d['entries'][:len(old)]==old;v['updated']=datetime.now(timezone(timedelta(hours=8))).isoformat();v['summary'][-1]=['重要性分级','必须6组 / 建议3组 / 可选1组；实验10'+('离线已完成·质量失败' if finished else '已安全暂停' if progress['stage']=='EXP10_PAUSED_BY_USER' else '执行中')];d['project']['phase']=f'实验10：{phase_label}；不操作板卡。';d['project']['updated']='2026-10-23';text=text[:match.start(2)]+'\n'+json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False).replace('<',r'\u003c')+'\n'+text[match.end(2):];atomic_journal_write(file,expected_journal_sha,text)
    pd=read(M/'PROGRESS.json');pd['active_work']='None; selected offline experiment ended with quality failure, no new automatic study or board work' if finished else f'Experiment10 {progress["stage"]}, check reports/fusion_exp10_20261023_r1/OFFLINE_WORKFLOW.json and EDA_PROGRESS.json';pd['runtime_processes']='No further EDA launched by completed workflow' if finished else 'Read actual one-shot workflow/EDA state and verify current processes; this JSON is a snapshot';pd['stage']='P7_FUSION_EXP10_OFFLINE_DONE_QUALITY_FAIL' if finished else 'P7_FUSION_EXP10_OFFLINE';pd['fusion_exp10']=dict(report='reports/fusion_exp10_20261023_r1/PROGRESS.json',grid_points=432,calibration_done=len(cl),board='NOT_RUN');pd['next']=g['next'];pd['updated']=v['updated'];(M/'PROGRESS.json').write_text(json.dumps(pd,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if progress['stage']=='EXP10_PAUSED_BY_USER':
        pd.update(active_work='None; user requested safe pause for power off',runtime_processes='Verified no owned continuation/EDA; see pause_20261023/PROCESS_AFTER.json',stage='P7_FUSION_EXP10_PAUSED_BY_USER',automatic_restart=False)
        (M/'PROGRESS.json').write_text(json.dumps(pd,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    sys.path.insert(0,str(ROOT/'tools'));import render_v4_validation;render_v4_validation.render();print('EXP10_PAGE_SYNC',len(cl),len(gpu['configurations']),len(d['entries']))
if __name__=='__main__':main()
