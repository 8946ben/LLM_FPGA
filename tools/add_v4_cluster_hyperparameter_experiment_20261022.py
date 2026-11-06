"""Add the cluster-only hyperparameter study plan; does not fit or evaluate."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,json,re,sys
ROOT=Path(__file__).resolve().parents[1];P='module_14_lm_head_v4/'
def ev(label,path):return dict(label=label,href=P+path)
def main():
    path=ROOT/'开发日志.html';s=path.read_text(encoding='utf-8');match=re.search(r'(<script id="dev-log-data" type="application/json">)(.*?)(</script>)',s,re.S);d=json.loads(match[2]);previous=copy.deepcopy(d['entries']);v=d['v4_validation']
    Cs=[16,32,64,128,256,512];Rs=[1,2,4,8,16,32,64,128];Ls=[256,512,1024,2048,4096,8192,16384,32768,65536]
    configs={}
    def add(c,r,l,axis):
        assert 1<=r<=c and 1<=l<=151936
        configs.setdefault((c,r,l),[]).append(axis)
    for c in Cs:add(c,4,16384,'中心数C')
    for r in Rs:add(128,r,16384,'选簇数R')
    for l in Ls:add(128,4,l,'每簇上限L')
    assert len(configs)==21
    add(1,1,1,'最小合法预算端点');add(128,128,151936,'全簇/最大列表容量端点（不保证覆盖全V）')
    variants=[]
    for i,((c,r,l),axes) in enumerate(configs.items(),1):
        variants.append(dict(id=f'C{c}_R{r}_L{l}',title=f'场景{i}：仅聚类 C={c} / R={r} / L={l}',short_label=f'{c}/{r}/{l}',
          configuration=[f"扫描所属：{'、'.join(axes)}",f'中心C={c}，最近R={r}簇，每簇列表最多L={l}行；并入固定14特殊ID','只启用聚类，不运行低秩/Top-K分支；最终候选升序去重后用canonical权重精算','若列表有效长度小于L，按真实长度读取；空簇fallback必须单列，不能当作纯聚类质量提升'],
          expected='记录整体/分项召回、漏选、真实K、fallback及完整GPU/后续FPGA时间；当前尚无本轮扫描结果',status='未开始',results={},parameters=dict(C=c,R=r,L=l),axes=axes))
    report=dict(
      parameters=[['C：聚类中心总数','128','初始扫描16 / 32 / 64 / 128 / 256 / 512','改变C需要仅用训练集重建中心、norms、簇列表和counts；候选集合不嵌套，不能假设C越大质量越高。'],
        ['R：单步选择最近多少簇','4','1 / 2 / 4 / 8 / 16 / 32 / 64 / 128（固定C128）','相同中心与排序下，增加R只纳入更多簇；合法范围1≤R≤C。联合/边界阶段额外检查R=C。'],
        ['L：每簇候选列表容量上限','16384','256 / 512 / 1024 / 2048 / 4096 / 8192 / 16384 / 32768 / 65536','固定中心与列表排名，只取同一长列表前缀。超过旧16384时须从训练投票重建更长列表并核对旧前缀；不能凭空补ID。']],
      baseline='原仅聚类方案为(C,R,L)=(128,4,16384)，保留不改。128不是隐层维度，4不是低秩rank，16384不是最终去重K；低秩分支在本实验完全关闭。',
      bound_rows=[['C的软件合法下限/上限','1≤C≤N_train_hidden；N_train_hidden为实际冻结训练hidden条数，不等于独立问题数。512只是首轮扫描边界，不是软件/硬件绝对上限。'],
        ['R的软件合法下限/上限','1≤R≤C；R=C表示检查全部簇，但各列表可能未覆盖全词表。'],
        ['L的软件合法下限/上限','1≤L≤V=151936；实际每簇只能取到训练中具有正投票的n_i条ID，读入min(L,n_i)。0不作为合法聚类预算。'],
        ['最终K的范围（未触发fallback）','令S为14个特殊ID，K=|S ∪ ⋃ᵢ list_i[:min(L,n_i)]|。max(14,maxᵢ min(L,n_i))≤K≤min(V,14+Σᵢmin(L,n_i))≤min(V,14+R×L)。'],
        ['空簇fallback','若允许fallback且选中空簇，实际K可直接变成V，以上R×L上界不再适用；必须报告fallback比例、纯列表覆盖率与含fallback的有效覆盖率。'],
        ['质量的理论范围','召回率在0–100%之间；R=C、L=V也不保证100%，因为训练投票列表未必包含所有V个token。显式全V精算对照才是定义上的100%上界。'],
        ['当前FPGA可支持的范围','现有router HLS固定C128/R4/L16384，不是动态参数。新C/R/L须新实验实现与容量/时序验收；不得将新表塞入当前固定容量镜像。']],
      scan_rows=[['A 单参：中心数C',','.join(map(str,Cs)),'R=4，L=16384','每个C单独训练；C128基线优先复用冻结中心。'],
        ['B 单参：选簇数R',','.join(map(str,Rs)),'C=128，L=16384','复用同一中心/列表，仅改变最近簇前缀。'],
        ['C 单参：每簇容量L',','.join(map(str,Ls)),'C=128，R=4','同一排名长列表截取前缀，保证可解释的嵌套。'],
        ['D 两个端点','(1,1,1)；(128,128,151936)','仅聚类；同模型/数据/策略','分别探最小合法预算与全簇/列表容量端点；后者不是保证dense覆盖。'],
        ['E 联合与边界扩展','围绕校准Pareto/可行边界追加≤12组合；补R=C','必须满足R≤C，并按容量/样本支持检查','不是直接跑全部笛卡尔积；若最优点落在扫描边缘，要向外扩，不能称已找到全局上限。']],
      scan_count='首轮A/B/C共21个去重配置（基线只计一次），加D两个端点，共23个具体配置。E的配置须在校准阶段确定并另存清单；本次只是新增实验计划，没有启动训练/测试。',
      controls=['冻结模型、训练hidden/标签、问题级train/calibration划分、数值顺序、14特殊ID、penalty1.1和原始权重。只研究聚类，低秩完全关闭。',
        '拟沿用现有训练方法：K-means主种子20261021、12轮；按raw top256的倒数排名投票并加4倍训练dense赢家计数，按票数排序，同票小ID。数据不足/空簇必须记账，不丢弃难样本。',
        'C扫描需重建中心与列表；R扫描复用相同中心；L扫描只改变同一列表前缀。C128扩容时保持旧中心和计票规则，验证旧16384前缀一致后才能归因于L。',
        '运行路由使用BF16中心及接受的FP32 H8 L2算术；通用C/R/L实验代码另立，不修改冻结生产selector/质量脚本/IP。若换BLAS/GEMM，必须另立数值/质量结果，不能继承原召回。'],
      data_protocol=['训练：仅使用已有train1500问题及其固定轨迹。校准：已有calibration320问题/4775 decode用于全部搜索与参数选择；按完整问题分组，不拆相邻token。',
        '现有v1/r2/r2b及fixed_quality_20261022测试结果均已打开，不能再用于这轮调参或重新认证。参数选定后必须先锁配置，再用全新未打开问题组一次最终测试。',
        '新的最终测试集来源、问题数、类别配额、SHA与门槛还需单独冻结；HumanEval164题已用100题，本来源剩余64题，不足以照搬下一轮100题配额，须新增独立公开代码来源/任务。不可用同题的不同token凑样本。'],
      evaluation=['质量：分别给整体/中英代码数学decode召回与漏选、首输出覆盖、问题级全步覆盖。初筛可沿用拟议整体/分项99.9%点门槛，但校准通过不是独立质量认证。',
        '候选与容量：真实K mean/median/P95/max、每簇实际n_i、空簇率、dense fallback比例、纯列表与含fallback的覆盖率；不能把容量上限L当实际K。',
        'GPU先粗筛：使用同一组冻结校准输入，3预热/30计时，含路由/并集/gather/精算/返回；不只测查表或复用dense预计算结果。入选少数配置再扩大测速样本并报告K分布。',
        '分别记录路由、列表/并集、精算及整次M14的时间；若某层没有独立计时能力，则写未测，不从总耗时倒推阶段。GPU参考与FPGA实测分栏。',
        'FPGA只为校准筛出的少数可行点新建匹配实现/布局与软件，不给23配置全部做bit。正式上板仍需用户新的明确独占安排。'],
      budgets=[['路由点积工作量','约C×896个乘加项/步，外加hidden norm及L2组合；不是实际周期。'],['中心BF16参数','2×C×896 B；C128时229376B。'],['排序列表预留','4×C×L B，另加counts/norms；基线8MiB，C512/L65536为128MiB。真实有效n_i可更小，读取/存储布局须分别报告。'],['候选精算权重逻辑量','1792×K B/步；不是实测DDR流量，burst、cache与重复事务另计。'],['嵌套性与时延','固定中心/列表下增R或L，纯列表集合K和覆盖率不会下降；实际延迟可因实现/缓存/调度波动，不保证严格单调。C改变后没有这种嵌套保证。']],
      outputs=['C、R、L分别作为横轴，质量召回率和GPU/FPGA耗时并列画图，固定另外两项；各点标真实K及fallback。',
        '对联合配置绘召回率—时延/候选规模Pareto图，剔除靠dense fallback伪装的“稀疏高召回”。',
        '在预先冻结质量/容量条件内报告“最小可行预算端”和“最高实测速度端”，以及何时接近dense成本。未达到门槛时如实写未找到可行区域。',
        '边界通常是(C,R,L)的联合可行区域，而非三个互不相关的最小值/最大值；不能把各维单独最小值拼起来保证有效。有限网格只能给已搜索范围内结果，不能宣称全局最优。'])
    g=dict(id='cluster-hyperparameters',title='实验8 · 仅聚类方案超参数（中心数C/选簇数R/每簇上限L）的质量—速度边界',status='未开始',stage_status=[['实验计划','已完成'],['训练/校准搜索','未开始'],['新独立测试/FPGA','未开始']],
      importance=dict(level='必须完成',kind='核心研究 / 方案可行边界',reason='用户核心关注：当前仅聚类未达质量门槛，不能只凭单个128/4/16384点排除整条路线。需要判断能否通过预算调整达到要求，及为此付出的速度/存储代价。',
        minimum='完成隔离的训练/校准超参扫描与质量—速度边界分析；如发现可行点，先锁定再做新独立质量核验。',extension='多训练种子稳定性、更密网格及多个FPGA构建可按主结果追加；当前不要求立即实现全部硬件配置。',order='在决定是否长期保留混合方案、或转向仅聚类之前完成；先软件离线，不直接改生产包。'),
      question='仅聚类方案中的128个中心、最近4簇和每簇16384上限分别变化时，质量、候选规模、GPU/FPGA速度如何变化？在达到冻结质量要求时，最小可行预算和最高实测速度分别在哪里？',
      changing='用C/R/L单参扫描建立因果清晰的对照，再围绕校准可行边界做有限联合搜索。低秩分支始终关闭，14特殊ID保留。',fixed=report['controls'],variants=variants,
      metrics=[dict(id='recall',label='校准decode召回率',unit='%',digits=4,direction='越高越好',scope='尚未运行本轮C/R/L扫描'),dict(id='gpu_ms',label='GPU完整调用中位耗时',unit='ms',digits=3,direction='越少越好',scope='未测'),dict(id='fpga_ms',label='FPGA完整调用中位耗时',unit='ms',digits=3,direction='越少越好',scope='未测')],
      sweep_report=report,
      decision='本轮只新增实验计划，尚无新超参结果。已有仅聚类(C128,R4,L16384)新独立集80/14958漏选只是一个旧基准点，不能证明别的C/R/L无效，也不用于新搜索的参数选择。',
      next='先实现独立、可变C/R/L且数值资格明确的软件扫描器；训练集重建、校准扫描和同口径GPU测速后才锁点与准备新的最终测试。当前冻结生产版本与板卡状态不变。',
      evidence=[ev('实际聚类训练/列表构造','reference/routing.py'),ev('现router固定128/4/16384合同','include/lm_head_v4_router.hpp'),ev('现有参数文件SHA','reports/selector_p2_20261021/PARAMETERS.json'),ev('原train/calibration使用方式','scripts/evaluate_selectors.py'),ev('质量分组与指标定义','reference/quality_data.py'),ev('已打开独立结果，禁止据此调参','reports/fixed_quality_20261022/RESULT.json')],
      scope='本实验研究可变超参数的软件与后续硬件可行范围，不是给现有固定bit传三个新数值。旧质量/GPU基准不重写；全新配置不继承旧RTL/板测资格。')
    assert not any(x['id']==g['id'] for x in v['comparisons']),'Preserve existing experiment; edit its canonical snapshot instead'
    v['comparisons'].append(g);v['updated']=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S Asia/Shanghai')
    v['summary'][-1]=['重要性分级','必须4组 / 建议3组 / 可选1组；新增仅聚类超参研究']
    entryid='20261022-v4-cluster-hyperparameter-study-plan'
    d['entries'].append(dict(id=entryid,date='2026-10-22',title='新增仅聚类C/R/L超参边界实验：23个首轮配置与联合可行区域',status='待验证',importance='重要成果',
      summary='新增实验8（必须完成）：C16–512、R1–128、L256–65536单参扫描，去重21点，加最小预算与全簇/容量端点共23点；均未执行。区分软件合法范围、搜索范围和最终实测可行边界。',
      attempt='读取实际训练投票/列表截断规则与固定HLS合同，明确哪些参数可在软件中改变、哪些需要重建模型与硬件。',problem='单个128/4/16384点不能说明仅聚类路线的最好质量/速度；仅放宽L不一定增加有效ID，全簇/全容量也不保证全V覆盖，空簇fallback可掩盖稀疏代价。',
      solution='给出单参/端点/有限联合扫描、K与内存边界、fallback分项、训练/校准/新测试隔离，以及GPU/FPGA分开计时与Pareto输出。',
      verification='仅计划与页面数据/链接/JS语法检查；没有新训练、GPU测试、RTL或板卡操作。新独立测试集尚待预留冻结，不复用已打开结果调参。',next=g['next'],tags=['v4','仅聚类','超参数','研究计划'],related=['20261022-v4-experiment-importance'],evidence=[dict(label='实验8参数、边界与扫描计划',href='doc/design/V4Validation.html#cluster-hyperparameters')]))
    assert d['entries'][:len(previous)]==previous
    d['presentation']['checks']='保留历史并新增仅聚类超参研究计划；静态检查，不执行新训练/测试或板卡操作。'
    s=s[:match.start(2)]+'\n'+json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False).replace('<',r'\u003c')+'\n'+s[match.end(2):];path.write_text(s,encoding='utf-8')
    sys.path.insert(0,str(ROOT/'tools'));import render_v4_validation;render_v4_validation.render()
    print(f'CLUSTER_HYPERPARAMETER_STUDY=PLANNED_ONLY configs={len(variants)} groups={len(v["comparisons"])} historical_entries_preserved={len(previous)}')
if __name__=='__main__':main()
