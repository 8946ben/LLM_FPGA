"""Reframe the documentation as controlled comparisons; reuse saved results only."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';PREFIX='module_14_lm_head_v4/'
def ev(label,path):return dict(label=label,href=PREFIX+path)
def variant(id,title,configuration,expected,status,results=None):
    return dict(id=id,title=title,configuration=configuration,expected=expected,status=status,results=results or {})
def metric(id,label,unit,digits=0,direction='越少越好',scope=''):
    return dict(id=id,label=label,unit=unit,digits=digits,direction=direction,scope=scope)
def group(id,title,question,changing,fixed,variants,metrics,decision,next,evidence,scope):
    return dict(id=id,title=title,question=question,changing=changing,fixed=fixed,variants=variants,metrics=metrics,decision=decision,next=next,evidence=evidence,scope=scope)

def main():
    path=ROOT/'开发日志.html';html=path.read_text(encoding='utf-8');match=re.search(r'(<script id="dev-log-data" type="application/json">)(.*?)(</script>)',html,re.S)
    d=json.loads(match[2]);before=json.loads(json.dumps(d['entries']));v=d['v4_validation'];qpath=M/'reports/fixed_quality_20261022/RESULT.json';q=json.loads(qpath.read_text())
    groups=[];variants=[]
    for id,title,config in [('route','场景1：仅聚类',['开启128中心L2路由，选择最近4簇','每簇最多16384 IDs；并入14特殊ID','关闭低秩投影和低秩Top-K分支','对候选仍用canonical BF16权重精算']),
       ('lowrank','场景2：仅低秩',['关闭聚类路由分支','开启rank128低秩：A[151936,128]、BT[128,896]','稳定Top16384后并入14特殊ID','对候选仍用canonical BF16权重精算']),
       ('hybrid','场景3：聚类 + 低秩混合',['开启场景1的4簇路由和场景2的rank128/Top16384','最终候选 = 两分支与14特殊ID的升序去重并集','用相同canonical BF16权重精算','不修改已冻结预算，不用新测试集调参'])]:
        decode=q[id]['decode'];r=dict(misses=decode['misses'],recall=decode['recall']*100,steps=decode['steps'])
        item=variant(id,title,config,'比较dense赢家是否被覆盖；不预设每步都一致','已完成：固定算术GPU候选覆盖审计',r)
        item['categories']={name:dict(misses=value['misses'],recall=value['recall']*100,steps=value['steps']) for name,value in decode['by_category'].items()}
        item['categories']['all']=r;variants.append(item)
    g=group('quality','实验1 · 三种筛选方案，谁漏选更少？','在同一批hidden/history上，混合是否能补回单一方案漏掉的dense赢家？',
       '只切换“聚类分支 / 低秩分支”的开关；每个启用分支的预算不变。',
       ['同一新1000问题：中文400/英文250/代码100/数学250；同一14958个decode步，零排除','相同BF16输入、模型权重、history、penalty=1.1和FP32算术合同','相同dense赢家标签；相同14特殊ID 151643–151656','分支预算固定，但最终候选K不相等；这不是同K算法排名或硬件速度比较'],variants,
       [metric('misses','漏选次数','次',scope='已完成固定算术GPU覆盖审计；相同测试集'),metric('recall','dense赢家召回率','%',4,'越高越好','已完成固定算术GPU覆盖审计')],
       '全部14958个decode步的综合结论：混合漏1次，较仅聚类少79次、较仅低秩少355次；混合通过预先拟议的整体及分项99.9%点门槛。仍有漏选，不能称无损。',
       '保持冻结混合方案继续工程验证。额外候选和低秩扫描的速度代价，需实验2测量，当前没有三方案硬件速度结论。',
       [ev('本次三方案真实结果','reports/fixed_quality_20261022/RESULT.json'),ev('独立证据复核','reports/fixed_quality_20261022/INDEPENDENT_REVIEW.json'),ev('冻结配置','data/fixed_quality_20261022/IMPLEMENTATION_FREEZE.json')],
       '本次检查候选集合是否覆盖已知dense赢家，未对14958步的每个候选重新运行精算head。场景卡中的canonical精算是方法合同，不是新增全量精算记录。本图不是完整RTL重放、自由生成得分或实板性能；拟议99.9%点门槛不是统计保证。')
    g['category_selection']=True;g['quality_result_sha256']=hashlib.sha256(qpath.read_bytes()).hexdigest();groups.append(g)
    groups.append(group('method-speed','实验2 · 三方案的质量收益，付出了多少时间？','仅聚类、仅低秩、混合相对dense，真实M14每步各需多少ms，能否提高decode效率？',
       '只改变候选生成方案；各方案若需要不同bit/ELF，分别建立匹配身份。',
       ['同一组待冻结的hidden/history和权重；同一块板、200MHz目标、PL DDR','相同生产模式、预加载条件、相同A53完整token-ready计时边界','每输入3 warmup +30计时 +1000稳定调用；正确性先行','当前硬件只集成混合；单一方案要新增实现和验收，不能在现bit上点击切换'],
       [variant('dense','场景0：完整词表dense',['不筛选；精算全部151936行','v3.1只作历史参考，未来须补同边界测量'],'完整dense结果','同口径新对照未测'),
        variant('route','场景1：仅聚类',['与实验1场景1相同；生产debug关闭','新增匹配硬件构建，尚未实现'],'按对应候选参考验证','硬件实现/计时待安排'),
        variant('lowrank','场景2：仅低秩',['与实验1场景2相同；生产debug关闭','新增匹配硬件构建，尚未实现'],'按对应候选参考验证','硬件实现/计时待安排'),
        variant('hybrid','场景3：混合',['与实验1场景3相同；生产flags6','已有离线bit/XSA/两ELF；目标尚未运行'],'按对应候选参考验证','实板未测')],
       [metric('median_ms','M14调用中位耗时','ms',3),metric('p95_ms','固定输入调用P95','ms',3),metric('token_s','M14等效token/s','次/s',3,'越高越好')],
       '尚不能判断三方案真实快慢。GPU程序用时、理论乘加数和召回率都不能填进这个耗时图。',
       '优先完成当前混合的验收准备。需要三方案速度结论时另立单一方案构建；本轮不启动EDA或板测。',
       [ev('当前性能口径与限制','reports/PERFORMANCE_ASSESSMENT_20261022.md'),ev('实际PS计时边界','standalone/selector_ps_main.c')],
       '全部实板结果留空。历史v3.1的117.751830ms属于IP计数口径，不放入同边界实板比较图。'))
    kv=[]
    for n,(name,label) in enumerate([('small','最小K'),('median','中位附近K'),('p95','P95 K'),('max','最大K')],1):
        folder=M/'reports/performance_cases_20261022'/name;gold=json.loads((folder/'GOLDEN_RESULT.json').read_text());sel=json.loads((folder/'MANIFEST.json').read_text())['selection'];e=gold['expected']
        kv.append(variant(name,f'场景{n}：{label} = {gold["candidates"]:,}',
          [f"输入：{sel['category']} / {sel['prompt_id']} / step{sel['step']}",f"实际候选K={gold['candidates']}，其余筛选参数保持冻结",'复用已保存hidden/history，不预填候选或preview到运行scratch'],
          f"CPU已比对dense：token{e['token']} / score{e['score_bits']} / CRC{e['crc32']}",'CPU参考与镜像就绪；新RTL/实板未测',dict(k=gold['candidates'])) )
    groups.append(group('k-sensitivity','实验3 · 候选数变大，decode会慢多少？','候选从17071增到56075时，精算和整次M14调用的耗时如何变化？',
       '使用四个K-only选出的真实输入；K及hidden/history随输入变化。',
       ['相同混合方案、权重/因子/路由表、penalty1.1、生产flags6','相同200MHz目标和PL DDR；未来计时边界一致','这是实际工作负载敏感性对照，hidden/history也变，不能声称只有K单一变量变化'],kv,
       [metric('k','已准备输入的实际候选数','行',scope='已完成CPU参考，并与GPU记录核对；不是耗时'),metric('median_ms','生产调用中位耗时','ms',3),metric('p95_ms','固定输入调用P95','ms',3),metric('token_s','M14等效token/s','次/s',3,'越高越好')],
       '四组CPU最终token/score bits/CRC与dense一致；镜像校验通过。当前只能画候选数图，不能画尚未测量的速度曲线。',
       '先扩展新K用例绑定，优先补P95/max RTL，再在获准上板后测四组生产耗时。',
       [ev('四组CPU/镜像/请求资格','reports/performance_cases_20261022/QUALIFICATION.json'),ev('具体输入与限制','reports/performance_cases_20261022/README.md')],
       '四个代表点不等于全语料耗时分布；候选数P95不是时延P95。'))
    groups.append(group('debug-comparison','实验4 · 打开debug，会改变结果或增加多少开销？','同一输入只打开候选raw输出时，token/分数是否一致，额外周期是多少？',
       '只切换flags.bit0 debug：生产6 ↔ debug7。',
       ['同一输入：优先P95 K41630，之后复验max K56075','同一权重、因子、路由表、history、penalty与fallback；同一RTL内存模型','各自建立描述符/镜像SHA；不覆盖生产镜像'],
       [variant('production','场景1：生产 flags=6',['debug关闭；penalty/fallback开启','输出token/score/CRC；无候选raw导出'],'与对应CPU精算参考一致','新输入RTL/实板未测'),
        variant('debug','场景2：debug flags=7',['只增加debug输出','完整preview151936项；ID与K个8B raw记录逐位核对'],'token/score/CRC与场景1及CPU相同','专用debug入口待准备')],
       [metric('cycles','同输入RTL周期','拍'),metric('median_ms','同输入实板调用中位耗时','ms',3)],
       '已有旧中文debug RTL样例，缺同输入生产配对，不能由此计算debug开销。',
       '先完成两模式配对参考与专用入口。当前计时ELF只接受flags6，不能直接用于flags7。',
       [ev('已有单例RTL范围','reports/SELECTOR_INTEGRATION_RESULT_20261021.json'),ev('固件flags6限制','standalone/selector_ps_main.c')],
       '旧中文K21529/6826306拍不放入新P95/max输入的对比结果；两组测试条件不同。'))
    groups.append(group('state-reuse','实验5 · 连续换输入，会不会用到上一次结果？','history和scratch反复更新后，每一步是否仍等于该步独立参考？',
       '改变调用顺序及每步hidden/history，保留同一套已加载权重/筛选参数。',
       ['A=已准备median K28184；B=已准备max K56075','每次确认空闲后才写输入；调用期间输入不可变','多步真实轨迹拟选中/英/代码/数学各1组，具体prompt和SHA待冻结'],
       [variant('AA','场景1：A → A',['相同hidden/history连续两次','检查重复调用稳定，不把warmup算新输入'],'两次结果都等于A参考','新增整链场景未运行'),
        variant('AB','场景2：A → B',['第二次替换hidden/history','不得沿用A的候选表K或token'],'第一次=A参考，第二次=B参考','新增整链场景未运行'),
        variant('BA','场景3：B → A',['反向从大K切回小K','重点检查候选尾部与旧结果残留'],'第一次=B参考，第二次=A参考','新增整链场景未运行'),
        variant('trajectory','场景4：完整dense轨迹回放',['每组最多16次预测，EOS自然结束','每步hidden读取NPZ；history累计prompt和先前dense tokens'],'逐步匹配各自CPU候选精算；漏选明确记分叉','多步golden/runner待准备')],
       [metric('mismatches','参考不一致次数','次'),metric('stale_results','旧结果误发布次数','次')],
       '这组用于发现状态复用错误，尚无新增整链结果，不预填“0次”。',
       '先整理每步golden和history，再用相同顺序做RTL/未来目标回放。',
       [ev('已有A/B参考','reports/performance_cases_20261022/QUALIFICATION.json'),ev('dense轨迹采集配置','data/hidden_fixed_20261022/holdout/settings.json')],
       '这些是故障探测刺激，不作等输入性能排名；dense轨迹回放不是稀疏模型自由生成。'))
    groups.append(group('policy-comparison','实验6 · history与penalty是否按约定改变赢家？','固定raw scores时，开启/关闭历史惩罚与改变历史位图，赢家应如何变化？',
       '逐项切换history、penalty开关或p；raw FP32分数保持不变。',
       ['拟议小型合成策略夹具：global ID10和20，raw score均为+2.0，其余严格更低','同分取较小ID；空history作为基础；单次只修改一项','属于策略单元测试，不将合成raw分数冒充H896真实模型输出'],
       [variant('empty','场景1：history空，penalty开',['p=1.1；两候选均未见过'],'预期token10（同分小ID）','拟议，夹具未运行'),
        variant('seen','场景2：只将ID10置为已见',['p=1.1；ID10分数除以1.1；ID20保持2.0'],'预期token20','拟议，夹具未运行'),
        variant('disabled','场景3：沿用场景2 history，关闭penalty',['只关闭penalty；两候选raw仍为2.0'],'预期token10','拟议，夹具未运行'),
        variant('identity','场景4：沿用场景2 history，p=1.0',['只将p改为1.0；惩罚启用但应为恒等'],'预期token10','拟议，夹具未运行'),
        variant('negative','场景5：重复前两场景的负分配对',['两候选raw改为−2.0；空history和只标ID10分别运行','已见负分乘p=1.1，不能除p'],'预期空history选10，标ID10后选20','拟议，夹具未运行')],
       [metric('wrong_winners','赢家不符次数','次'),metric('wrong_bits','FP32分数位模式不符次数','次')],
       '这里给出的是按合同推导的预期；没有把预期填入实测结果栏。',
       '先固定合成夹具并验证CPU策略单元，再扩展RTL；生产固件flags6不能直接覆盖关闭penalty场景。',
       [ev('策略参考实现','reference/candidate_head.py'),ev('固定筛选算术','reference/selector_arithmetic.py')],
       '负分、±0、跨32/128bit位图边界等余项仍保留在工程清单；这些不改变当前冻结生产配置。'))
    groups.append(group('error-comparison','实验7 · 每种错误能否被正确拒绝？','只破坏一个字段或一个数值时，是否在预期阶段停止，且不发布旧token？',
       '正常描述符/参数为对照，每次只注入一处错误；错误用例独立记录。',
       ['H896/V151936、320MiB arena、描述符offset0x100000；输入身份逐项冻结','检查status/stage/child_status、token_valid以及scratch/guard','历史Csim24项预检拒绝/5项运行错误已通过，不自动当作新增RTL/目标证据'],
       [variant('valid','场景0：合法输入',['不注入错误；生产flags6'],'status0/stage6/token与参考一致','已有原始夹具证据；新增用例未运行'),
        variant('magic','场景1：magic改为0',['其余保持合法'],'BAD_DESCRIPTOR1 / stage1 / 无token','已有历史Csim；新增RTL/目标未运行'),
        variant('flags','场景2：flags改为8',['仅引入未知flag位'],'BAD_CONFIG4 / stage1 / 无token','已有历史Csim；新增RTL/目标未运行'),
        variant('alignment','场景3：weight offset+1',['仅使地址不对齐'],'BAD_REGION2 / stage1 / 无token','已有历史Csim；新增RTL/目标未运行'),
        variant('overlap','场景4：routed起址改为merged起址',['两活动区域重叠'],'OVERLAP3 / stage1 / scratch不被计算改写','历史中文RTL有该拒绝；新输入未运行'),
        variant('nonfinite','场景5：BT首项改为BF16 NaN 0x7fc0',['不改描述符，其余数值保持合法'],'CHILD_FAILED5 / LOWRANK stage3 / 无token','已有历史Csim；新增RTL/目标未运行'),
        variant('fallback-no','场景6：counts全0，flags3禁止fallback',['选择空簇；debug+penalty开启，allow_fallback关闭'],'FALLBACK_FORBIDDEN6 / stage2 / fallback1/K0','已有历史Csim；新增RTL/目标未运行'),
        variant('fallback-yes','场景7：相同counts全0，flags7允许fallback',['与场景6相比只开启allow_fallback位','debug/penalty不变，需全V精算预算'],'允许显式fallback，精算V151936并与dense一致','整链允许路径待补')],
       [metric('unexpected_accepts','非法输入被误接受次数','次'),metric('stale_publishes','失败仍发布token次数','次')],
       '已有历史错误路径证据，新增大规模/多步RTL与目标覆盖仍未运行。预期状态不是已跑出的新结果。',
       '复用历史具体注入值，建立新run的逐项清单；不将错误事务计入正确调用性能平均。',
       [ev('现有实际Csim注入','tests/selector_csim.cpp'),ev('状态枚举','include/lm_head_v4_selector.hpp')],
       '不同错误测试的是拒绝/门控正确性，不应画成不同算法的速度比较。'))
    groups.append(group('transfer-comparison','实验8 · 加载和DMA交接的正常/异常对照',
       '只有数据真实进入PL DDR并且DMA停止后，才允许启动匹配的测试ELF吗？',
       '以正常加载/交接为对照，分别改变CRC、分片/断线或DMA停机读回。',
       ['M4AR/v1/TCP1415；320MiB、320×1MiB；每次READ≤512B，共34项','目标逐块/整份CRC和sentinel；GEM3 base0xff0e0000；不得默认回退PS DDR','当前只有本机镜像预检、mock传输/Tcl证据；板卡不连接'],
       [variant('normal','场景1：正常加载与停机',['正确序号/CRC；完整目标验证','先halt CPU，再GEM TX halt/禁RX-TX并读回'],'全部身份/CRC及TXGO=0等条件通过后才进入测试ELF','实际目标未测'),
        variant('fragment','场景2：合法TCP分片',['数据和CRC不变；只拆分网络接收边界'],'与场景1得到相同arena SHA/目标CRC','实际目标未测'),
        variant('bad-crc','场景3：单块CRC错误或传输断线',['明确损坏一块或中断会话'],'拒绝后续IP测试，恢复后整份重传','实际目标未测'),
        variant('dma-busy','场景4：DMA TXGO不清零 / RX-TX读回不符',['模拟或实际注入停机失败'],'禁止替换ELF和启动campaign；保留失败状态','宿主门控已有mock证据；实际目标未测')],
       [metric('unsafe_launches','未满足门槛仍启动次数','次'),metric('load_s','含目标校验的加载时间','s',3)],
       '没有真实目标加载时间和DMA行为数据；图中留空，不把mock PASS当板测。',
       '继续离线准备新K入口和异常测试。获得新的明确独占安排后才能执行目标对照。',
       [ev('默认本机预检的上传器','standalone/upload_arena_tcp.py'),ev('DMA交接mock证据','reports/board_preparation_20261022/HOST_CONTROL_RESULT_r2.json')],
       '加载时间不属于预加载M14 token-ready调用；本轮不触发网络/JTAG。'))
    v['comparisons']=groups;v['updated']=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S Asia/Shanghai')
    v['intro']='每组只回答一个问题：先列固定条件，再逐项写出场景配置，最后把同口径结果画图对比。已有数据立即展示；未运行的指标留空，预期与实测分开。'
    v['summary']=[['8组实验','筛选质量、速度、候选规模、debug、多步状态、策略、错误与加载'],['3个筛选场景','仅聚类 / 仅低秩 / 两者混合'],['已有质量图','同一14958 decode步，直接读取封存结果'],['实板未测','当前仅编辑文档，不运行新实验']]
    entry_id='20261022-v4-controlled-comparison-page'
    if not any(e['id']==entry_id for e in d['entries']):d['entries'].append(dict(id=entry_id,date='2026-10-22',title='将验证清单改为8组明确对照实验，已有质量结果直接画图',status='已验证',importance='重要成果',
       summary='按要回答的问题、固定条件、逐场景开关和参数、指标、结果图与结论组织。实验1明确仅聚类/仅低秩/混合三场景，画同一独立集漏选与召回图；未测速度留空。',
       attempt='根据用户指出的阅读问题，逐组明确比较对象、控制变量和待确定事项。',problem='上一版17个工程检查项没有清楚列出对照场景，用户无法判断每组实验要比较或确定什么。',
       solution='新增8组对照视图作为主界面；原17项参数/工程细节保留为折叠附录。场景卡、结果表和图读取主日志同一份数据，质量图支持整体与四类切换。',
       verification='读取封存RESULT中的80/356/1漏选和分项数据绘图；数值/结构/链接/JS语法静态检查，未重跑GPU/RTL/板测。file://视觉预览仍受工具策略限制。',
       next='继续按明确对照定义准备新K入口、多步与异常夹具；板卡暂不上板。',tags=['v4','对照实验','结果图','参数'],evidence=[dict(label='8组对照实验与结果图',href='doc/design/V4Validation.html#quality'),ev('质量结果原始数据','reports/fixed_quality_20261022/RESULT.json')],related=['20261022-v4-validation-scenarios-parameters']))
    assert d['entries'][:len(before)]==before
    d['project']['updated']='2026-10-22';d['project']['source']='原有日志保留；验证页按8组对照实验重新组织。只是文档更新，未启动新计算或板卡操作。'
    d['presentation']['checks']='新增对照实验与已有质量结果图，保留全部历史条目；静态数据/链接/JS语法检查。file://视觉预览受工具策略限制。'
    html=html[:match.start(2)]+'\n'+json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False).replace('<',r'\u003c')+'\n'+html[match.end(2):]
    html=html.replace('按 CPU/GPU、RTL、未来实板查看：固定参数、四组候选规模、多步、debug、错误注入及计时门槛。明确区分已验证、输入就绪与拟开展。','按8组对照实验查看：要回答的问题、场景1/2/3的配置、统一指标、结果图及结论；已有质量数据直接画图，未测留空。')
    path.write_text(html,encoding='utf-8');sys.path.insert(0,str(ROOT/'tools'))
    import render_v4_validation
    render_v4_validation.render()
    print(f'COMPARISON_DOCUMENTATION=UPDATED groups={len(groups)} variants={sum(len(g["variants"]) for g in groups)}; historical_entries_preserved={len(before)}; experiments_NOT_EXECUTED')
if __name__=='__main__':main()
