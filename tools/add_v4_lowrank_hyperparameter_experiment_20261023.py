"""Document rank/Top-T ablations; no factor construction, evaluation or EDA."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,json,re,sys
ROOT=Path(__file__).resolve().parents[1];P='module_14_lm_head_v4/'
def ev(label,path):return dict(label=label,href=P+path)
def main():
    file=ROOT/'开发日志.html';s=file.read_text(encoding='utf-8');m=re.search(r'(<script id="dev-log-data" type="application/json">)(.*?)(</script>)',s,re.S);d=json.loads(m[2]);previous=copy.deepcopy(d['entries']);v=d['v4_validation']
    ranks=[8,16,32,64,128,256,512,896];tops=[256,512,1024,2048,4096,8192,16384,32768,65536];points={}
    def add(r,t,axis):
        assert 1<=r<=896 and 1<=t<=151936
        points.setdefault((r,t),[]).append(axis)
    for r in ranks:add(r,16384,'低秩维度r')
    for t in tops:add(128,t,'预筛Top-T')
    assert len(points)==16
    for r,t,label in [(1,16384,'秩下限端点'),(128,1,'Top-T下限端点'),(1,1,'最小联合预算端点'),(128,151936,'Top-T全词表端点'),(896,151936,'全秩/全词表端点')]:add(r,t,label)
    assert len(points)==21
    variants=[]
    for i,((r,t),axes) in enumerate(points.items(),1):
        variants.append(dict(id=f'r{r}_T{t}',title=f'场景{i}：仅低秩 r={r} / Top-T={t}',short_label=f'r{r}/T{t}',parameters=dict(r=r,T=t),axes=axes,
          configuration=[f"扫描所属：{' / '.join(axes)}",f'关闭聚类；A[151936,{r}]，BT[{r},896]，z=h×BTᵀ，preview=A×z',f'全V preview按global history做penalty1.1，再稳定Top-{t}；并入14特殊ID并按ID去重升序',f'最终候选K满足max({t},14)≤K≤min(151936,{t}+14)；仅这些原始权重行进行canonical精算'],
          expected='统计整体/分项召回、漏选、真实K、GPU/FPGA分阶段和整次时间、因子/DDR成本；新配置当前未运行',status='未开始',results={}))
    report=dict(symbol_text='r/Top-T',parameter_keys=['r','T'],plot_axes=[['低秩维度r','r'],['预筛Top-T','T']],data_heading='因子构造、校准选型与全新最终测试',
      parameters=[['r：低秩投影维度','128','8 / 16 / 32 / 64 / 128 / 256 / 512 / 896','只使用canonical W构造r个主方向及对应A；r变化会改变preview排序，不保证赢家召回率单调。1作为额外下限端点。'],
        ['T：低秩预筛Top-T数量','16384','256 / 512 / 1024 / 2048 / 4096 / 8192 / 16384 / 32768 / 65536','固定r、因子、输入和policy，仅改变同一preview排序的截取位置。1和V作为额外边界；不是最终K。']],
      baseline='仅低秩基线(r,T)=(128,16384)，聚类分支完全关闭。流程：hidden → 低秩投影z → 全151936词preview → penalty → 稳定Top-T ∪14特殊ID → 最终K → 原始BF16权重的K行精算 → token。',
      bound_rows=[['r的软件下限/上限','1≤r≤min(V,H)=896；这里的r与实验8最近选簇数R是不同参数。896为矩阵维度上限，不代表该点最快或质量最佳。'],
        ['T的软件下限/上限','1≤T≤V=151936。稳定Top-T始终保留T个唯一ID；14特殊ID并入后，max(T,14)≤K≤min(V,T+14)。'],
        ['T=V的质量上限对照','只要preview均有限、精算与policy合同正确，Top-V包含全部词表，最终K=V，token/score/CRC应等于dense；但仍多做低秩预估，不能当作等成本dense。'],
        ['r=H不保证近似排名完全等于dense','未量化的全秩分解在实数算术下可重构W，但A/BT的BF16量化和FP32求和顺序仍可能改变排名。r896且T<V不能直接宣称100%召回。'],
        ['单调性边界','固定r及同一preview时，增T使候选集合嵌套，K和候选覆盖不会下降；增r不保证dense赢家召回单调，实际时延也不保证严格单调。'],
        ['当前实现边界','现低秩参考/HLS固定rank128，统一selector描述符固定Top16384。独立Top-K核接口虽允许1≤top_k≤V，整核与其余容量/软件仍需新资格，不代表当前bit可直接换r/T。'],
        ['归约和存储padding','rank非8倍数时需定义行打包补零；beat数非2幂时需定义归约树补零，例如r896的112个8路beat须在归约树补至128。分别记录逻辑r、行pack和树padding；不继承旧rank128格式/时序资格。']],
      scan_rows=[['A 单参：低秩维度r',','.join(map(str,ranks)),'T=16384；其他输入/策略一致','各r使用同一主基前缀及一致量化/符号约定；高于128时先扩基并核对基线。'],
        ['B 单参：预筛Top-T',','.join(map(str,tops)),'r=128；同一因子/preview排序','截取同一稳定排序，候选并入14特殊ID；不重算/拟合因子来改变T。'],
        ['C 下限/上限端点','(1,16384)、(128,1)、(1,1)、(128,V)、(896,V)','仅低秩；特殊ID和canonical精算一致','隔离秩/候选数下限及全词表上限；全词表点单列成本，不能冒充有效稀疏加速。'],
        ['D 联合可行边界','在校准Pareto邻域追加≤12个(r,T)组合','只用校准结果选点，最终测试仍未打开','寻找高r低T/低r高T的成本补偿；边缘最优则扩扫，不能以有限点宣称全局最优。']],
      scan_count='A/B合计16个去重配置（r128/T16384只计一次），加5个边界点，共21个首轮具体配置。联合阶段另锁≤12个配置。本次只设计计划，没有构造新因子或执行测试。',
      controls=['聚类始终关闭；固定canonical BF16权重、H896/V151936、模型输入、history、penalty1.1、14特殊ID、同分小ID及canonical候选精算。变化的只是r与T。',
        '因子只从原始W构造：由WᵀW主方向B取前r列，A=W×B；A/B量化为BF16。不读取新测试标签拟合因子，不通过调penalty掩盖漏选。',
        '同一主基下按前缀比较各r，固定特征向量排序/符号约定、软件版本与factor SHA。现只有128维冻结主基；扩至896维后须检查旧128前缀，若不同则另立新系列并重做基线，不能拼接旧结果。',
        '为可变r单独冻结FP32运算顺序、行/树补零规则，先对每个r做CPU/GPU位一致。rank128必须复现接受的8路/16beat顺序；其他r不使用BLAS质量继承旧RTL结论。',
        '同一r下T扫描复用同一preview及稳定分数/ID排序；这些缓存只能用于质量审计，计时必须实际运行完整低秩、选择和精算，不能把离线预计算收益算入速度。'],
      data_protocol=['因子构造只使用权重，不训练新语言模型。已有train1500问题可供数值/实现预检；已有calibration320问题/4775 decode用于r/T选型，按完整问题分组。',
        '旧v1/r2/r2b/fixed_quality_20261022独立测试均已打开，只保留历史对照，不用于新超参选点或复认证。先锁定(r,T)/算法/阈值/测量口径，再用全新未打开问题组一次最终核验。',
        '可与实验8共用同一批新的最终问题，但两条路线都必须在第一次打开该批标签前锁定配置；不能先看仅聚类的结果再调整仅低秩。新来源/配额/规模/SHA尚待冻结。'],
      evaluation=['质量：整体与中英代码数学decode召回、漏选、首输出及问题级全步覆盖；拟议整体/分项99.9%只作校准初筛，不是无损或统计保证。',
        '候选：记录Top-T配置和真实K mean/median/P95/max，不能用T+14上界替代实际并集。仅低秩没有聚类空簇fallback；任何额外dense回退须单列，不能当自然稀疏高召回。',
        'GPU：同一冻结校准输入集、batch1，每组合3 warmup+30测量；包含z、全V预览、policy、实际Top-T/并集、权重gather、精算及token/score/CRC返回。初筛用同一4夹具，少数入选点再扩大输入样本。',
        '分别记录B投影、A全词表预览、Top-T/并集、候选精算及整次M14的时间。若没有独立阶段计时就保留未测，不从总时间倒推；记录FP32数值实现与GPU内存布局。',
        '资源：逻辑/打包因子字节、真实K行精算量、preview读写/Top-T扫描量及目标DDR实际传输分别报告。只为少数校准合格点做匹配FPGA实现，板测仍待用户授权。'],
      budgets=[['因子逻辑存储','2×r×(V+H) B；r128=39124992B，r896=273874944B。实际行pack和元数据另算。'],
        ['低秩预估工作量','r×(H+V)个乘加项/步：r128=19562496；与T无关，固定r时即使T很小仍须扫全V的A。'],
        ['候选精算工作量','K×H个乘加项；权重逻辑量1792×K B/步。T增大主要扩大这部分，但GPU/DDR事务不等于公式字节。'],
        ['Top-T选择成本','当前radix实现以多遍全V扫描选择阈值，成本不简单正比T；计时应包含真实选择/并集，不能只计算preview。'],
        ['全秩资源端点','r896仅因子已约261.2MiB，再加原始W约259.7MiB，逻辑合计超过当前320MiB arena。需要新布局，不能把2GiB物理DDR可容纳等同于当前包可执行。']],
      outputs=['固定T时以r为横轴、固定r时以T为横轴，并列画召回/漏选与GPU/FPGA耗时；标真实K与因子存储。两个扫描轴分开。',
        '绘r×T质量和速度热图及召回—延迟/容量Pareto图，标出不达门槛和资源不可行点。',
        '回答达到冻结质量门槛时的最小rank/最小候选预算组合、最高实测速率及何时接近或超过dense成本；这些是联合边界，不把两个独立最小值拼成有效配置。',
        '直接dense不含低秩预估，r128/T=V和r896/T=V虽能全词表精算但有额外成本，单列为质量上限/冗余工作对照。有限扫描不证明全局最优。'])
    g=dict(id='lowrank-hyperparameters',title='实验9 · 仅低秩方案超参数（低秩维度r/预筛Top-T）的质量—速度边界',status='未开始',stage_status=[['实验计划','已完成'],['因子扩展/校准搜索','未开始'],['新独立测试/FPGA','未开始']],
      importance=dict(level='必须完成',kind='核心研究 / 单一路线可行边界',reason='原rank128/Top16384仅低秩漏356/14958步，只代表一个点；需要判断提高rank或候选预算能否满足质量门槛并替代混合，以及其真实成本。',minimum='完成隔离的r/T校准质量—速度边界分析；选定点锁定后用新独立问题核验。',extension='更多中间rank/Top-T、稠密重构误差专题与多个FPGA构建可按Pareto结果追加，不要求全部21点做bit。',order='与仅聚类实验8并列为核心方案研究；先离线参考与校准，不改冻结生产实现。'),
      question='仅低秩的rank128与Top16384分别改大或改小时，dense赢家覆盖、最终K、因子存储和完整调用速度如何变化？是否存在满足质量要求且比混合更合算的(r,T)组合？',changing='关闭聚类，分别扫描低秩维度r和预筛Top-T，再围绕校准可行边界做少量联合搜索；每个候选仍用原始BF16权重精算。',fixed=report['controls'],variants=variants,sweep_report=report,
      metrics=[dict(id='recall',label='校准decode召回率',unit='%',digits=4,direction='越高越好',scope='新r/T扫描未运行'),dict(id='gpu_ms',label='GPU完整调用中位耗时',unit='ms',digits=3,direction='越少越好',scope='未测'),dict(id='fpga_ms',label='FPGA完整调用中位耗时',unit='ms',digits=3,direction='越少越好',scope='未测')],
      decision='本次仅新增实验设计，21个新配置全部未运行。旧rank128/Top16384的质量与GPU结果保留为实验1历史单点，不能证明其余rank/Top-T的上下限。',
      next='先另立可变r数值参考、主基/因子扩展及Top-T边界检查，验证rank128重现；然后仅在校准集扫描、做真实GPU测速，锁点后准备全新最终问题组。',
      evidence=[ev('实际权重分解/量化构造','scripts/evaluate_selectors.py'),ev('现固定rank128算术','reference/selector_arithmetic.py'),ev('rank128 HLS接口','include/lm_head_v4_lowrank.hpp'),ev('独立Top-K范围检查','src/lm_head_v4_topk.cpp'),ev('统一selector固定Top16384','src/lm_head_v4_selector.cpp'),ev('现有因子文件SHA','reports/selector_p2_20261021/PARAMETERS.json')],
      scope='这是仅低秩参数实验，聚类不参与；r是低秩维度，T是预筛截取数，K是并入特殊ID后的精算行数。不同r的新数值/容量/时序不继承原rank128资格，尚未开始实验。')
    assert not any(x['id']==g['id'] for x in v['comparisons'])
    v['comparisons'].append(g);v['summary'][-1]=['重要性分级','必须5组 / 建议3组 / 可选1组；新增仅低秩超参研究'];v['updated']=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S Asia/Shanghai')
    d['entries'].append(dict(id='20261023-v4-lowrank-hyperparameter-study-plan',date='2026-10-23',title='新增仅低秩r/Top-T边界实验：16个单参点与5个端点',status='待验证',importance='重要成果',
      summary='实验9列为必须：r8–896、Top-T256–65536单参共16去重点，加r1/T1/全词表等5端点共21配置。明确T、最终K与rank的不同，所有新配置均未运行。',
      attempt='根据实际权重Gram分解、固定rank128算术及Top-K接口设计，分别控制rank和筛选截取数。',problem='单点rank128不足以判断仅低秩可行边界；全rank经过BF16量化并不保证排名等于dense，且新rank需要定义归约padding与内存容量。',
      solution='设计单参/端点/有限联合扫描、因子主基与基线一致检查、质量—速度—存储Pareto，校准选型与新测试严格隔离。Top-V作为保证全精算的质量上限对照，额外预览成本单列。',
      verification='只完成文档数据/链接/JS语法检查，不构造因子、不训练、不测速、不启动RTL或板卡操作。',next=g['next'],tags=['v4','仅低秩','超参数','研究计划'],related=['20261022-v4-cluster-hyperparameter-study-plan'],evidence=[dict(label='实验9参数与边界',href='doc/design/V4Validation.html#lowrank-hyperparameters')]))
    assert d['entries'][:len(previous)]==previous
    d['project']['updated']='2026-10-23';d['project']['phase']=d['project']['phase'].replace('8组','9组')+' 新增仅低秩r/T计划，未执行。'
    d['todos'].insert(0,dict(text='核心研究实验9：仅低秩r/Top-T超参边界，先可变rank数值资格与校准选型；不复用旧测试集，目前未开始。',status='待验证'))
    d['presentation']['checks']='保留71条历史，新增仅低秩超参设计记录；静态数据/链接/JS语法检查，不执行新增计算或板测。'
    s=s[:m.start(2)]+'\n'+json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False).replace('<',r'\u003c')+'\n'+s[m.end(2):];s=s.replace('按8组实验报告查看：','按9组实验报告查看：');file.write_text(s,encoding='utf-8')
    sys.path.insert(0,str(ROOT/'tools'));import render_v4_validation;render_v4_validation.render()
    print(f'LOWRANK_HYPERPARAMETERS=PLANNED_ONLY configs={len(variants)} groups={len(v["comparisons"])} history_preserved={len(previous)}')
if __name__=='__main__':main()
