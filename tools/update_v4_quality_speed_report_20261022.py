"""Merge quality/speed report and import reviewed GPU measurements; no testing."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,json,math,re,statistics,sys
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';P='module_14_lm_head_v4/'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def metric(id,label,unit,digits=0,direction='越少越好',scope=''):return dict(id=id,label=label,unit=unit,digits=digits,direction=direction,scope=scope)
def evidence(label,path):return dict(label=label,href=P+path)
def main():
    b=M/'reports/gpu_method_benchmark_20261022_r2';result=read(b/'RESULT.json');plan=read(b/'PLAN.json');raw=read(b/'RAW_OBSERVATIONS.json');proof=read(b/'NUMERIC_PROOF.json')
    assert result['state']=='PASS_GPU_REFERENCE_BENCHMARK_NOT_FPGA_OR_LLM' and len(raw)==480 and len(proof['records'])==16
    for name,key in [('PLAN.json','plan_sha256'),('RAW_OBSERVATIONS.json','raw_sha256'),('NUMERIC_PROOF.json','numeric_proof_sha256')]:assert sha(b/name)==result[key]
    assert sha(b/'benchmark_source.py')==plan['script_sha256']
    for mode in ['dense','route','lowrank','hybrid']:
        samples=[r for r in raw if r['mode']==mode];assert len(samples)==120
        vals=[r['wall_ms'] for r in samples];assert all(math.isfinite(x) and x>0 for x in vals)
        s=result['summary'][mode]
        assert s['wall_median_ms']==statistics.median(vals) and s['wall_p95_ms']==sorted(vals)[113]
        assert s['aggregate_equivalent_m14_per_s']==120000/sum(vals)
        for c in ['chinese','english','code','math']:
            rows=[r for r in samples if r['case']==c];assert {r['round'] for r in rows}==set(range(30))
            p=next(p for p in proof['records'] if p['mode']==mode and p['case']==c);assert p['all_ids_raw_bits_match'] and all(r['k']==p['k'] for r in rows)
    review=dict(state='PASS_SAVED_GPU_TIMING_EVIDENCE_REVIEW',result_sha256=sha(b/'RESULT.json'),pairs=16,measurement_calls=480,per_pair=30,
        verified=['plan/raw/proof/source hashes','raw observation counts/rounds/K','aggregate/median/nearest-rankP95 recomputation'],
        scope='Read-only saved output audit; not rerun of GPU numeric proof or hardware acceptance',fpga='NOT_RUN')
    save(b/'INDEPENDENT_REVIEW.json',review)
    file=ROOT/'开发日志.html';text=file.read_text(encoding='utf-8');match=re.search(r'(<script id="dev-log-data" type="application/json">)(.*?)(</script>)',text,re.S);d=json.loads(match[2]);old=copy.deepcopy(d['entries']);v=d['v4_validation']
    q=read(M/'reports/fixed_quality_20261022/RESULT.json');g=v['comparisons'][0]
    assert g['id']=='quality';v['archived_method_speed_comparison']=next(x for x in v['comparisons'] if x['id']=='method-speed')
    v['comparisons']=[x for x in v['comparisons'] if x['id']!='method-speed']
    dense=copy.deepcopy(g['variants'][0]);dense.update(id='dense',title='场景0：完整词表 dense',configuration=['不运行候选筛选；精算全部151936行','相同canonical BF16权重、FP32点积、history和penalty1.1','质量图的0漏选/100%为与dense自身比较的定义对照'])
    dense['results']=dict(misses=0,recall=100.,steps=14958)
    dense['categories']={name:dict(misses=0,recall=100.,steps=value['steps']) for name,value in g['variants'][0]['categories'].items()}
    dense['definition_baseline']=True;g['variants'].insert(0,dense)
    names={'dense':'dense','route':'仅聚类','lowrank':'仅低秩','hybrid':'混合'}
    for i,variant in enumerate(g['variants']):
        variant['short_label']=names[variant['id']];variant['title']=f'场景{i}：'+names[variant['id']]
        s=result['summary'][variant['id']]
        variant['gpu_results']=dict(gpu_median_ms=s['wall_median_ms'],gpu_p95_ms=s['wall_p95_ms'],gpu_token_s=s['aggregate_equivalent_m14_per_s'],fpga_median_ms=None,fpga_token_s=None)
    g.update(title='实验1 · lm_head稀疏化方案（仅聚类/仅低秩/混合）的质量与速度对比',status='部分完成',
       stage_status=[['质量对比','已完成'],['GPU参考测速','已完成'],['FPGA测速','未开始']],
       question='在相同输入和数值策略下，三种稀疏化方案分别漏选多少、运行多快，相对完整词表dense有什么取舍？',
       changing='切换候选筛选方案：dense / 仅聚类 / 仅低秩 / 混合；各启用分支的冻结预算不变。',
       fixed=['H=896，V=151936；canonical BF16权重；FP32接受算术；global history与penalty1.1；同分取小ID','同一质量集比较候选覆盖，同一测速输入比较四种GPU实现；两份数据的来源/用途分开说明','聚类128中心/最近4簇/每簇最多16384；低秩rank128/Top16384；特殊ID151643–151656','各方案最终候选K不同；不将其解释为同K算法比较。GPU计时包含实际候选构造与精算'],
       metrics=[metric('misses','漏选次数','次'),metric('recall','dense赢家召回率','%',4,'越高越好')],
       gpu_metrics=[metric('gpu_median_ms','GPU调用中位耗时','ms',3),metric('gpu_p95_ms','GPU调用P95','ms',3),metric('gpu_token_s','GPU参考等效输出率','次/s',2,'越高越好'),metric('fpga_median_ms','FPGA调用中位耗时','ms',3),metric('fpga_token_s','FPGA等效输出率','次/s',2,'越高越好')],
       decision='质量：仅聚类/仅低秩/混合分别漏80/356/1次，混合达到预先拟议的99.9%整体及分项点门槛。GPU参考：混合约84.36次/s，高于dense约66.33次/s；在这个Eager参考实现和4输入批次中，仅低秩约164.55次/s、仅聚类约135.18次/s更快。速度和质量来自不同用途的数据，不据此调参或宣称总体/FPGA收益。',
       next='保持参数冻结，继续准备同四输入的FPGA生产计时与数值验收；用户暂不上板。真实FPGA结果获得后填入同一表和图，GPU结果不代填。',
       scope='质量是新独立集的候选覆盖审计；GPU速度是4个校准输入的单请求参考实现。未测整网decode/TTFT，不使用官方答案评价答题能力；FPGA尚未连接/测速。')
    sources=read(M/'data/public_corpus_v1/SOURCES.lock.json');human=read(M/'data/fixed_quality_20261022/HumanEval_sources.lock.json')
    g['report']=dict(
       model='Qwen2.5-0.5B-Instruct；H896/V151936。权重与tokenizer版本及每个文件SHA由MODEL.lock.json固定。采集前已用8步canonical head与tokenizer证明校验。',
       source_rows=[dict(category='中文',name='CMMLU',revision=sources['revisions']['cmmlu'],subset='官方test CSV中的题目与A–D选项；按问题分组',count=400,prompt='题目 + A–D选项 + 请给出答案并简要说明理由',url='https://github.com/haonan-li/CMMLU/tree/'+sources['revisions']['cmmlu']),
         dict(category='英文',name='Databricks Dolly-15k',revision=sources['revisions']['dolly'],subset='instruction哈希落入保留区间的未使用问题',count=250,prompt='instruction + 非空context；不使用response作标签',url='https://github.com/databrickslabs/dolly/tree/'+sources['revisions']['dolly']),
         dict(category='代码',name='HumanEval',revision=human['revision'],subset='官方164任务中的100个未使用prompt；不执行测试/解答',count=100,prompt='Complete the following Python function + 函数prompt',url=human['repository']+'/tree/'+human['revision']),
         dict(category='数学',name='GSM8K',revision=sources['revisions']['gsm8k'],subset='官方test.jsonl中的未使用question',count=250,prompt='仅question；不使用answer作标签',url='https://github.com/openai/grade-school-math/tree/'+sources['revisions']['gsm8k'])],
       split_rows=[['训练集','1500问题 / 22433 decode','训练路由列表；低秩因子由权重构造，不用测试标签拟合'],['校准集','320问题 / 4775 decode','历史配置选型与算术检查；本次GPU测速4夹具来自这里'],['本次新独立质量集','1000问题 / 14958 decode','仅一次冻结质量核验，不训练/调参；与所有旧保留组精确规范化去重']],
       selection='按完整问题分组，使用NFKC/casefold/空白规范化哈希；排除旧train/calibration/holdout、998快照与r2/r2b全部保留问题。排除3822旧group、3824旧prompt后，按固定seed m14-fixed-arithmetic-independent-20261022 的SHA排序选取各类配额。与旧组的规范化group/prompt重叠均为0。',
       collection='固定系统提示与chat模板，max_input_tokens=2048、max_new_tokens=16，实际tokenizer输入33–425 tokens。用BF16模型前级采集hidden，并由canonical FP32精确dense head贪心生成轨迹；history含prompt及先前生成token。得到15958次预测，其中首输出1000次单列，后续14958次为decode，零排除。没有把数据集标准答案作为下一token标签。',
       metric_definitions=[['dense赢家','相同hidden/history经完整151936行canonical精算及penalty/argmax选出的token'],['漏选次数','该dense赢家不在当前候选集合中的decode步数'],['召回率','(decode步数 − 漏选次数) / decode步数 ×100%'],['dense基线','与dense自身对照，定义为0漏选/100%召回；不冒充重新测量的独立质量结果']],
       limitations='只检查与dense的一步一致性潜力，不是CMMLU/GSM8K答题得分、HumanEval pass@k或自由生成质量。精确规范化去重不排除近重复/模板相关或预训练污染。代码训练/校准使用过MBPP，本次独立代码源为HumanEval；不与旧测试混合统计。99.9%是预先拟议点门槛，不是无损或统计保证。',
       corpus_sha256=q['corpus_sha256'],
       evidence=[evidence('公开源版本/URL/许可证/SHA','data/public_corpus_v1/SOURCES.lock.json'),evidence('HumanEval版本/文件SHA','data/fixed_quality_20261022/HumanEval_sources.lock.json'),evidence('问题预留与去重记录（保留原阶段状态）','data/fixed_quality_20261022/MANIFEST.json'),evidence('采样与prompt构造源码','scripts/prepare_fixed_quality_20261022.py'),evidence('实际采集参数','data/hidden_fixed_20261022/holdout/SETTINGS.json'),evidence('模型与tokenizer文件锁','data/model/MODEL.lock.json'),evidence('最终质量结果（以此为完成结论）','reports/fixed_quality_20261022/RESULT.json')])
    g['gpu_report']=dict(state='已完成',device=result['device'],torch=result['torch'],cuda=result['cuda'],
       cohort='原校准集四个已冻结真实hidden/history：中文index1、英文1281、代码2536、数学3816。每类1输入，4种方案共16个case-method组合；不是新1000问题的总体测速。',
       protocol='batch=1；权重BF16常驻GPU，因子/中心FP32常驻。每组合3次warmup、30次测量；共48次warmup、480次测量，各方案120个测量。轮换方案/输入顺序；保留所有原始时间。',
       boundary='主指标为CPU墙钟：GPU常驻hidden/history → 筛选/排序/并集 → BF16行gather与FP32展开 → 精确head → penalty/argmax → CPU收到token/score并计算CRC。调用前同步；排除初始化、权重/输入上传和Transformer前级。',
       arithmetic='PyTorch Eager固定FP32算术参考，不用GEMM、FMA、Tensor Core或torch.compile加速。16组合完整ID/raw位模式及最终结果与CPU逐位一致后才计时；不是优化后的GPU生产推理性能。',
       aggregation='GPU等效输出率 =120次成功调用 / 该方案120次墙钟总秒数；中位/P95按120次统计。它们只描述四个固定输入的均衡批次。FPGA后续必须用相同输入与返回边界，才可做跨设备比较。',
       prior_failure='r1在预检发现27项preview相差1 ULP，停止且未计时。新脚本改为显式FP32 GPU张量惩罚系数后，r2完整逐位检查及480次测量通过；r1证据保留，不修改冻结质量脚本或生产源码。',
       cases=[dict(category=c,**{mode:result['summary'][mode]['cases'][c] for mode in ['dense','route','lowrank','hybrid']}) for c in ['chinese','english','code','math']],
       evidence=[evidence('测速方案与输入SHA','reports/gpu_method_benchmark_20261022_r2/PLAN.json'),evidence('GPU结果','reports/gpu_method_benchmark_20261022_r2/RESULT.json'),evidence('480条原始记录','reports/gpu_method_benchmark_20261022_r2/RAW_OBSERVATIONS.json'),evidence('16组合全量数值证明','reports/gpu_method_benchmark_20261022_r2/NUMERIC_PROOF.json'),evidence('计时数据独立复核','reports/gpu_method_benchmark_20261022_r2/INDEPENDENT_REVIEW.json'),evidence('首轮失败预检保留','reports/gpu_method_benchmark_20261022_r1/PROGRESS.json')])
    titles=[('k-sensitivity','候选词表规模对精算正确性与运行速度的影响','部分完成',[['CPU参考/镜像','已完成'],['新RTL/实板','未开始']]),
        ('debug-comparison','debug输出对数值一致性与运行开销的影响','未开始',[['同输入配对验证','未开始']]),
        ('state-reuse','连续调用中hidden/history更新与结果独立性验证','未开始',[['新增多步回放','未开始']]),
        ('policy-comparison','重复惩罚与全局history对赢家选择的影响','未开始',[['新增策略夹具','未开始']]),
        ('error-comparison','非法输入及数值异常的拒绝行为验证','部分完成',[['历史Csim','已完成'],['新增RTL/实板','未开始']]),
        ('transfer-comparison','PL DDR加载完整性与GEM DMA交接验证','部分完成',[['宿主模拟','已完成'],['实板','未开始']])]
    for i,(id,title,status,stages) in enumerate(titles,2):
        group=next(x for x in v['comparisons'] if x['id']==id);group.update(title=f'实验{i} · {title}',status=status,stage_status=stages)
        for case in group['variants']:case.setdefault('short_label',case['title'].split('：')[-1])
    v.update(schema='V4_EXPERIMENT_REPORT_V3',updated=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S Asia/Shanghai'),
       intro='按实验报告组织：数据来源与划分、方法配置、评价指标、质量结果、GPU参考速度和未来FPGA速度。已有结果并列展示；尚未测试的指标保留为空。',
       summary=[['质量：已完成','1000独立问题 / 14958 decode；混合漏1次'],['GPU测速：已完成','4校准输入×4方案×30次；参考实现'],['FPGA测速：未开始','当前暂不上板，不能用GPU或RTL结果代填'],['7组实验','正式名称、分阶段状态、并列结果图']],hash_aliases={'method-speed':'quality'})
    v['platform']=[(k,'仅离线；本次新增GPU参考测速已完成；仍不连接FPGA' if k=='当前授权' else val) for k,val in v['platform']]
    entry_id='20261022-v4-quality-speed-merged-gpu-reference'
    if not any(e['id']==entry_id for e in d['entries']):d['entries'].append(dict(id=entry_id,date='2026-10-22',title='合并稀疏化质量与速度实验，补齐语料说明与GPU参考测速',status='已验证',importance='重要成果',
       summary='实验1合并dense/仅聚类/仅低秩/混合质量与GPU/FPGA速度；漏选与召回并列折线图。GPU r2四校准输入/16组合逐位核对通过，480次计时完成；实板未测。',
       attempt='按用户意见改用正式实验名称和明确状态，补齐公开数据来源、冻结版本、分组采样、模型采集、标签与指标定义。为GPU速度另立固定算术参考实现。',
       problem='原页面质量与速度重复分组，卡片标签冗余、图需切换且来源说明不足。GPU r1标量除法路径有27项preview偏差1 ULP，未通过预检即停止。',
       solution='新benchmark以显式GPU FP32张量系数保持除法语义；保留r1失败，r2按相同CPU参考全量逐位检查。页面合并为7组，质量与GPU/FPGA图同时展示，删掉场景卡冗余标签。',
       verification='16组合的全部候选ID/raw分数和最终结果与CPU一致；每组合3 warmup+30测量，共480测量。GPU dense/聚类/低秩/混合等效率66.33/135.18/164.55/84.36次/s；只是4输入PyTorch Eager参考，不是整体LLM或FPGA性能。页面静态检查，不宣称浏览器视觉验收。',
       next='参数不调优，新质量集不复用调参；继续准备同输入的FPGA验收。用户暂不上板。',tags=['v4','质量与速度','GPU参考','实验报告'],evidence=g['gpu_report']['evidence']+[dict(label='合并实验报告',href='doc/design/V4Validation.html#quality')],related=['20261022-v4-controlled-comparison-page']))
    assert d['entries'][:len(old)]==old
    d['project'].update(updated='2026-10-22',phase='v4离线：质量与GPU参考测速完成；FPGA暂不上板。7组实验报告并列质量与设备速度。',source='保留历史，新增GPU参考测速r1失败/r2通过记录和实验报告改版。没有FPGA操作。')
    d['performance']['candidate_note']='v4新独立质量与GPU参考测速完成，GPU不是优化后的生产实现；v4实板decode/P95/TTFT仍未测。质量与速度报告从侧栏进入。'
    d['exploration']['updated']=v['updated'];d['exploration']['summary']='完整RTL/200MHz系统离线通过；新独立质量和GPU参考速度已完成。GPU四输入与质量1000问题分开报告，实板未测。'
    d['presentation']['checks']='保留68条历史，新增1条GPU参考/报告记录；数据、图表来源、链接与JS语法静态检查。未做file://浏览器视觉验收。'
    text=text[:match.start(2)]+'\n'+json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False).replace('<',r'\u003c')+'\n'+text[match.end(2):]
    text=text.replace('按8组对照实验查看：要回答的问题、场景1/2/3的配置、统一指标、结果图及结论；已有质量数据直接画图，未测留空。','按7组实验报告查看：稀疏方案质量与GPU/FPGA速度、语料来源、正式实验状态和并列折线图；未测留空。')
    file.write_text(text,encoding='utf-8');sys.path.insert(0,str(ROOT/'tools'));import render_v4_validation,render_v4_design
    render_v4_validation.render();render_v4_design.render()
    progress=read(M/'PROGRESS.json');progress['gpu_reference_benchmark']=dict(state=result['state'],result='reports/gpu_method_benchmark_20261022_r2/RESULT.json',calls=480,pairs=16,fpga='NOT_RUN',scope=result['interpretation'])
    progress['active_work']='NONE: offline resident-GPU benchmark finished exit0; no FPGA/EDA processes started';save(M/'PROGRESS.json',progress)
    print(f'QUALITY_SPEED_REPORT=UPDATED groups=7 variants={sum(len(x["variants"]) for x in v["comparisons"])} history_preserved={len(old)} measurements=480 FPGA_NOT_RUN')
if __name__=='__main__':main()
