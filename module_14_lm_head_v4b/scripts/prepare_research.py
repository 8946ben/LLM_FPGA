"""Build v4b research documents. No model, accelerator, EDA or target operations."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, html, json, shutil

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'module_14_lm_head_v4b'
PAP = ROOT / 'doc/paper/lm_head_quantization'
OUT = ROOT / 'doc/design/V4bValidation.html'
STAMP = datetime.now(timezone(timedelta(hours=8))).isoformat()

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def experiment(id, title, priority, question, variables, fixed, variants, steps, metrics, gate, papers, dependency):
    return dict(id=id,title=title,priority=priority,status='NOT_RUN',question=question,
                variables=variables,fixed=fixed,variants=variants,steps=steps,metrics=metrics,
                gate=gate,papers=papers,dependency=dependency,
                results=dict(quality=None,gpu=None,csim=None,hls=None,rtl=None,implementation=None,board=None))

experiments = [
experiment('q01','实验1 · v3.1基线与数值契约','必须完成',
 '独立M14是否准确复现已上板v3.1的算术与policy？先排除参考实现差异。',
 '原归档8步与四类训练/校准夹具；penalty OFF/ON、raw输出 OFF/ON。',
 ['H896/V151936；canonical BF16 W/h；H8、16槽交错累加、相邻lane FP32规约；分开乘加，禁用FMA/TF32。','完整全局history；penalty=1.1；同分取小ID；保留prefill/decode的原语义。','MODEL.lock与tokenizer身份；tied embedding仅只读，不修改模型共享参数。'],
 ['归档8步生产回放','归档8步全logits回放','四类校准夹具×penalty OFF/ON','无量化W16/hBF16控制'],
 ['重核baseline/SOURCE_LOCK.json及原package成员SHA。','复现原hidden/history和所有raw/token/score bits/CRC；记录浮点舍入与有限值规则。','测量同轮dense参考；保留117.751830ms历史实板值，后续同板重新测量前不称同轮对照。'],
 ['全部raw bits、token、score bits、CRC','首输出与decode分别计数','原源文件/权重/模型/夹具SHA'],
 '无量化控制必须逐位一致；失败时不得开展量化质量归因。研究阶段已核验小型基线快照，新的数值回放尚未运行。',[],[]),
experiment('q02','实验2 · 位宽、分组与对称性边界','必须完成',
 '最简单RTN能否以可接受赢家一致率减少真实打包字节？',
 'W bits=[4,6,8,12]；沿每token行hidden轴分组G=[32,64,128,896]；对称/非对称，共32点＋W16控制。',
 ['h保持BF16；权重解包后先以FP32恢复，再用v3.1归约顺序；不把该路径叫INT4整数点积。','scale FP32；RNE；对称q范围[-(2^(b-1)-1), +(2^(b-1)-1)]；非对称q=[0,2^b-1]。','对称s=maxabs/qmax；非对称lo=min(minW,0)、hi=max(maxW,0)、s=(hi-lo)/qmax、z=clip(RNE(-lo/s))；全零组s=1/z=0。'],
 ['W4：4组长×2对称性','W6：4组长×2对称性','W8：4组长×2对称性','W12：4组长×2对称性','W16控制：canonical BF16，无量化'],
 ['仅用训练权重/训练统计构造32份小型元数据，先冻结packing再校准。','校准320问题按四类/首输出/decode统计；批量计算可分块，不保留32份全量展开W。','输出逻辑payload、scale/zero、64B行对齐后镜像字节及解包成本的Pareto图。'],
 ['policy后top1一致率与错选数','logit maxabs/RMSE、top1-top2 margin与翻转率','payload/元数据/填充/总字节、有效bits/weight','构造耗时、峰值RAM/VRAM'],
 '首轮仅32点；整体与各类decode均≥99.9%、全部校准预测零错选、无NaN/溢出者才进入保守候选；未合格不扩扫已打开最终组。',['Q01','Q02'],['q01']),
experiment('q03','实验3 · RTN、GPTQ与AWQ的head-only比较','必须完成',
 '在相同位宽/组长/存储预算下，校准补偿能否改善输出层赢家？',
 'RTN/GPTQ/AWQ × W4/W8 × G64/G128，共12点（含4个已在实验2的RTN控制）；最多2个OmniQuant条件扩展。',
 ['首轮统一非对称格式与FP32 scale，避免算法与元数据精度混杂。','只读hidden_v1/train1500拟合，calibration320选型；记录训练样本与SHA、seed、算法代码commit。','GPTQ固定damp=0.01×mean(diag(H))、act-order OFF、静态分组；奇异/空统计拒绝或预声明阻尼，不静默fallback。','AWQ缩放alpha=[0,0.25,0.5,0.75,1]仅在训练内部子划分选择；首轮禁用另行裁剪搜索。'],
 ['RTN W4/W8 × G64/G128（复用4点）','GPTQ W4/W8 × G64/G128（4新点）','AWQ W4/W8 × G64/G128（4新点）','条件扩展：OmniQuant W4-G128，最多2个预算设置，另立计划'],
 ['明确代码包含head量化；不能直接调用默认跳过lm_head的整网脚本。','AWQ在线执行h/s，W离线乘s，变换及有限精度误差计入整次调用。','按实际总字节与policy后错误选型，记录GPTQ重建MSE、训练/校准差距。'],
 ['各类top1一致率及错误清单','logit误差、KL诊断、margin翻转','校准耗时/峰值内存、packing总字节','运行时预处理耗时'],
 '采用与实验2相同质量门槛；算法名和重建误差下降不能代替输出层验证。',['Q01','Q02','Q07'],['q02']),
experiment('q04','实验4 · W8A8 / W4A8整数计算','建议完成',
 '量化hidden并引入整数MAC，能否克服仅反量化权重后仍做FP32乘法的计算瓶颈？',
 'W4/W8 × G64/G128 × SmoothQuant alpha=[0,0.5,1]共12点；同W/G的hBF16控制4点，共16场景。',
 ['激活A8为每token对称动态scale；scale=0/非有限值显式处理；正负均保留。','先做组内INT32点积，再乘sW×sH；非对称W另减zW×sum(qH)，禁止跨不同scale组直接整数相加。','证明累加上界；G≤896、对称A8和W8最坏127×127×896=14451584，非对称W另核验补偿中间量。','前级模型与embedding保持原始BF16，A8只存在M14入口内部。'],
 ['W8A8：2组长×3个alpha','W4A8：2组长×3个alpha','W8/hBF16与W4/hBF16：每种2组长，共4控制'],
 ['先精确整数参考与边界测试，再统计校准赢家。','单列变换、激活量化、整数dot、scale恢复和policy的时间/资源。','只有收益明确才增加A4，另限2点；不得自动扩大首轮。'],
 ['整数和与组后FP32逐位对照','饱和率、离群通道、溢出/NaN拒绝','校准一致率与整次时间'],
 '整数参考逐位通过且满足质量门槛才替换选定算术；新加法顺序必须新建数值身份。',['Q03','Q04','Q13'],['q02','q03']),
experiment('q05','实验5 · 高精度离群残差的收益与代价','可做可不做',
 '少量BF16残差是否比增加全局位宽更划算？',
 'W4/W8-G128固定主体，残差率=[0,0.1%,0.5%,1%]，共8点；仅当首轮质量/容量不合格时启用。',
 ['残差按训练集激活加权误差选定；不读取最终问题标签。','同时保存index与BF16 residual，固定token/hidden排序；将稀疏分解与候选词表稀疏明确区分。'],
 ['W4：4残差预算','W8：4残差预算'],
 ['主体解码加残差，建立单一确定归约顺序。','统计额外索引、对齐、解码与随机访问，和同字节W6/W8对照。'],
 ['赢家错误与margin','残差/索引/scale总字节','带宽与BRAM/DSP预算'],
 '同总字节质量或同质量整次时间无优势则停止，不因论文near-lossless声称逐位无损。',['Q04','Q05','Q06'],['q02','q03']),
experiment('q06','实验6 · 码本与局部旋转的有限探索','可做可不做',
 '均匀量化遇到精度边界时，码本或旋转是否值得增加硬件复杂度？',
 '条件启用：INT4/NF4/AAAC-like × G64/G128共6点；另加W4/W8-G128块旋转2点，总上限8点。',
 ['NF4只借格式，不训练LoRA；AAAC-like与论文完整复现分列。','896=7×128：7个128维正交块，h′=Rh、W′=WRᵀ；固定seed与归一化，先证非量化变换误差。','只在hidden轴旋转，不能混合token轴后省去逆变换；权重变换离线、hidden变换在线计费。'],
 ['均匀INT4/NF4/双码本：每种2组长','块旋转W4-G128、W8-G128：2点'],
 ['训练码本/旋转只使用训练数据，记录参数和预算。','无量化旋转控制检查logits及token；再量化比较误差。','统计码本容量、lookup端口和变换时间；QuIP#/SpinQuant/LUT-LLM完整实现另评审。'],
 ['top1一致率、长尾错误','在线旋转/查表成本','真实bits/weight与片上存储'],
 '同预算无收益则终止；块旋转不是QuaRot复现，NF4不是INT4整数MAC。',['Q06','Q08','Q09','Q10','Q11','Q15','Q16'],['q02','q03']),
experiment('q07','实验7 · 量化全表预筛＋BF16候选精算','必须完成',
 '若直接量化输出改变赢家，能否用量化预筛保留高召回并减少BF16读取？',
 'W4/W8、G128对称RTN；K=[512,2048,8192,16384,32768,V]，共12点＋dense/直接W4/直接W8共3控制。',
 ['不使用v4聚类/低秩路由；本实验自身就是独立两阶段量化路线。','先全V近似logits，再对全V应用原history/penalty后取Top-K，小ID打破同分；候选升序去重后BF16精算。','候选精算用原始W/h和v3.1接受算术；不沿用经AWQ缩放的hidden。所有V个token可入选，不偷偷删EOS/特殊ID。','K=V是完整精算退化端点；不把它计作有效稀疏收益。'],
 ['W4 preview：6个K','W8 preview：6个K','全BF16 dense与直接W4/W8：3控制'],
 ['同时核对原始raw赢家与policy后赢家，主指标是后者候选覆盖。','读取量=Bpacked_preview + K×896×2 + IDs/工作区；计入全V预筛、Top-K、排序、gather和policy。','可行点最多取3个，以校准零漏选/预算选择，禁止在最终组改K。'],
 ['policy后候选召回、最终token/score bits/CRC','K与预筛/精算/总字节','全流程耗时和峰值容量'],
 '全部校准预测零漏选且各类decode≥99.9%；选中dense赢家时score bits/CRC应与dense一致。有限K不保证无损。',['Q12'],['q01','q02']),
experiment('q08','实验8 · Packing、AXI与GPU参考成本','必须完成',
 '压缩文件是否真正转化为更少AXI拍数和更低整次M14耗时？',
 '最多2个质量合格配置；微核设计点(lanes,AXI bits)=[(8,128),(16,128),(16,256),(32,256)]，最多8组合；先微核再选1个整系统。',
 ['v3.1实际HLS/MIG为128bit；256bit仅为待验证宽度转换提案，不假定DDR带宽翻倍。','payload按hidden顺序低bit优先小端打包，scale FP32；非对称zero用ceil(b/8)字节；每行64B对齐。','GPU batch1、四类原校准固定夹具；每方案3warmup+30计时，按输入/方法交错轮换。'],
 ['packed解码＋FP32算术控制','整数MAC或选定量化微核','同轮BF16 dense','量化预筛全流程（若入围）'],
 ['验证bitstream pack/unpack、首末token/组边界/填充；禁止只测fake-quant展开W。','GPU同时报告软件参考和真正packed kernel，kernel不存在则后者NOT_RUN；含CPU收到token/score的墙钟及device分段。','FPGA分别测payload/meta/填充读取拍数、burst和反压；内部等待计数不代替实际AXI监控。'],
 ['真实镜像字节和AXI beats','解包/反量化/Top-K/精算/总时间','DSP/BRAM/LUT/FF、II/Fmax','GPU版本、频率、内存、原始计时'],
 '静态字节模型是预算，GPU速率不是FPGA预测；满足质量后以整次耗时与资源选型。',['Q13','Q14','Q15'],['q02','q03','q07']),
experiment('q09','实验9 · 锁点与全新独立质量认证','必须完成',
 '锁定量化方法能否在未参与选择的问题上保持预定质量？',
 '最多1个直接量化点＋1个量化精算点＋dense控制；全新1000问题，拟中400/英250/代码100/数学250。',
 ['计划尚未冻结语料与入口；必须在首次标签采集前生成EVALUATION_ENTRY_LOCK、所有SHA和DATA_SPLIT_MANIFEST。','精确与规范化去重覆盖全部旧train/calibration、v4所有保留组、快照与实验10；旧已打开组只作诊断，不再认证。','HumanEval旧题已耗尽，不承诺剩余题量；代码候选来源MBPP官方未用任务，排除prompt/参考解/同任务近重复后若不足，先修订来源/配额再锁定。','问题分组bootstrap/区间；不能把同一问题的约16个token视为独立样本；99.9%是点估计门槛，不是总体保证。'],
 ['canonical dense控制','锁定直接量化（若合格）','锁定量化预筛精算（若合格）'],
 ['用未量化前级、canonical head贪心轨迹收集hidden/history：max_input2048、max_new16，首输出和后续decode分开。','一次性在相同轨迹比较所有锁点；零静默排除，缺失和超长单列，不补选有利样本。','主门槛：整体与各类decode一致率≥99.9%，并报告首输出/每题全步一致率、错误token/margin、95%区间。','直接量化另做固定文本teacher-forced NLL/ΔNLL和分布KL诊断；KL仅主机计算分布，不改变线上argmax。'],
 ['直接路径token一致率；精算路径候选召回与最终一致率','首输出/各类decode/整题一致率及置信区间','NLL/ΔNLL、KL、全部错误清单','锁点和来源SHA、实际样本数'],
 '失败保留，不在已打开组改参数重认证；工程通过不能替代质量通过。下游任务分数/允许退化阈值需在实验11rollout前单独预声明。',['Q01','Q12'],['q03','q07','q08']),
experiment('q10','实验10 · 新算术Csim / HLS / RTL与200MHz实现','必须完成',
 '量化格式与算术是否在硬件中按定义执行，并满足目标时序？',
 '仅1个锁定实现；生产/debug、四类真实输入、量化边界与拒绝路径。',
 ['私有v4b descriptor/IP VLNV/build ID/CSR/layout/配置tag全部新分配，当前为UNASSIGNED；不冒用v3.1或v4镜像。','保持PL DDR和200MHz目标；新IP、新XSA、匹配BSP/ELF和镜像必须重建，不能继承旧PASS。','直接量化RTL对照新定点/浮点golden逐位；另行与BF16对照质量。'],
 ['Csim：边界与真实夹具','HLS综合：II/资源/时钟估计','完整RTL：所有输出/工作区/guard','200MHz整系统与匹配软件'],
 ['构造零/全幅/半步舍入/负值/重复惩罚正负分支/同分小ID/NaNscale/越界zero/尾组/别名等用例。','官方RTL真实PASS及逐位内存/scalar审计，再导出私有IP；Windows EDA优先项目内短路径并保留失败。','STA setup/hold、DRC/CDC、时钟复位/PL DDR映射审计，bit/XSA/CSR身份核验后构建BSP/ELF。','直接与refine布局分开评估：固定320MiB不继承；refine同时保存canonical和packed W时拟512MiB arena（仍须实际布局审计）。'],
 ['C/RTL bits与所有guards','II、估计周期、资源','实际200MHz WNS/WHS、CDC/DRC','镜像/BSP/ELF身份和SHA'],
 '新golden逐位通过与BF16质量通过是两项条件；HLS估计/AXI仿真周期不填作实板decode。',['Q14'],['q08','q09']),
experiment('q11','实验11 · 独占板测与闭环生成评估','必须完成',
 '在真实板卡及量化生成轨迹上，收益和质量是否仍成立？',
 '未来用户明确独占安排后：同板v3.1/v4b对照、30次计时、四夹具轮换1000调用、多步输入；闭环生成另采集。',
 ['本次不连接、探测或操作FPGA；不启动wb/luyou/心跳。','板测前冻结实板计划；确认板卡、包、PL DDR布局与匹配软件。','Qwen配置tie_word_embeddings=true；整网评测必须克隆独立输出层，保留输入embedding BF16，禁止原位覆盖共享参数。'],
 ['板测生产与debug分开','同次安排的v3.1全BF16基线','真实多步更新hidden/history','直接量化闭环与canonical闭环'],
 ['新镜像加载后目标逐块/全量CRC、身份/guard/错误路径；多步与四输入轮换排除残留状态。','3warmup+30独立样本，median/P95（ceil定义）和1000连续调用；量化头整次时间包括预处理/返回。','闭环生成在相同prompt/seed下各自产生hidden/history；报告长度、EOS、首次分叉与任务分数，不能复用dense轨迹当量化自由生成。','整网TTFT/TPOT只在真实端到端系统测量后填写；独立M14输出/s仅为1/本核时间。'],
 ['IP cycles/median/P95、A53wall','有效AXI/DDR读写字节、冷加载与常驻分别计时','1000调用正确性/超时/连续稳定性','闭环分叉率/任务指标、整网TTFT/TPOT（若实测）'],
 '实板数值/系统与独立质量均通过才形成v4b候选交付；不得从压缩率或历史117.751830ms推断实际加速。',[],['q09','q10']),
experiment('q12','实验12 · 与v4的后续合并评审','可做可不做',
 '两条独立路线稳定后，是否值得融合候选稀疏化与量化？',
 '未来另立四臂消融：v3.1、v4稀疏、v4b量化、融合；本次仅预留，不实施。',
 ['当前v4与v4b并行开发；保留独立源码/参数/语料锁/包/身份。','融合新命名、新布局、新数值资格、新最终问题组；不得拼接v4或v4b的旧验收结论。'],
 ['v3.1全BF16','合格v4稀疏点','合格v4b量化点','未来融合候选'],
 ['先比较误差是否叠加以及preview/scale/候选精算的存储是否重复。','在新实验授权后建立同轮四臂质量/时间/流量消融。'],
 ['质量/总字节/整次时间/资源四臂对照'],
 '本次不锁融合参数，不将实验10失败点发布或作为默认合并对象。',[],['q11'])
]

def baseline():
    paths = [
      'module_14_lm_head_v3_1/experiments/board_v31_20261019/src/lm_head_v2.cpp',
      'module_14_lm_head_v3_1/experiments/board_v31_20261019/include/lm_head_v2.hpp',
      'module_14_lm_head_v3_1/reports/board_v31_20261019/RESULT.md',
      'module_14_lm_head_v3_1/reports/board_v31_20261019/comparison.json',
      'module_14_lm_head_v3_1/reports/board_v31_20261019/package/RUN_PROFILE.json',
      'module_14_lm_head_v3_1/reports/board_v31_20261019/package/BUILD_SOURCES.json',
      'module_14_lm_head_v3_1/reports/board_v31_20261019/package/ARTIFACTS.sha256',
      'module_14_lm_head_v4/data/model/MODEL.lock.json',
      'module_14_lm_head_v4/data/model/config.json'
    ]
    receipts=[]
    base=MOD/'baseline/v31'
    for source in paths:
        original=ROOT/source
        target=base/Path(source).name
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and sha(target)!=sha(original):
            raise ValueError('Existing snapshot changed: '+str(target))
        if not target.exists():
            shutil.copyfile(original,target)
        receipts.append(dict(source=source,snapshot=target.relative_to(MOD).as_posix(),sha256=sha(target),bytes=target.stat().st_size))
    package=ROOT/'module_14_lm_head_v3_1/reports/board_v31_20261019/package'
    checked=[]
    for line in (package/'ARTIFACTS.sha256').read_text().splitlines():
        expected, name=line.split(maxsplit=1)
        actual=sha(package/name)
        if expected!=actual: raise ValueError('Baseline package mismatch: '+name)
        checked.append(dict(file=name,sha256=actual))
    profile=json.loads((base/'RUN_PROFILE.json').read_text())
    assert sha(base/'lm_head_v2.cpp')==profile['hls_source_sha256']['src/lm_head_v2.cpp']
    assert sha(base/'lm_head_v2.hpp')==profile['hls_source_sha256']['include/lm_head_v2.hpp']
    lock=dict(format='M14_V4B_BASELINE_RESEARCH_LOCK_V1',created=STAMP,
      status='PASS_SOURCE_SNAPSHOT_AND_V31_PACKAGE_HASHES_ONLY',
      note='v3.1 is the engineering parent. v4 supplies read-only canonical model identity only; no v4 selector is copied. No numerical rerun, EDA or board operation.',
      files=receipts,package_members_checked=checked,historical_board_result='PASS_2026-10-20',
      historical_ip_median_ms=117.751830,historical_ip_p95_ms=117.752020,
      canonical_weight_file_rehashed_this_session=False)
    dump(MOD/'baseline/SOURCE_LOCK.json',lock)
    return lock

def main():
    if (MOD/'reports/quantization_20261023_r1/ENTRY_LOCK.json').exists():
        raise RuntimeError('Execution has started. Do not reset research plan/results; use sync_execution.py.')
    papers=json.loads((PAP/'manifest.json').read_text(encoding='utf-8'))['papers']
    assert len(papers)==16
    lock=baseline()
    plan=dict(format='M14_V4B_QUANTIZATION_RESEARCH_PLAN_V1',created=STAMP,version='v4b',
      status='DESIGNED_NOT_EXECUTED',engineering_parent='v3.1',parallel_branch='v4',
      scope='Research, original paper collection, baseline source snapshot and experiment design only.',
      research_complete=True,experiment_entry_frozen=False,
      forbidden_actions=['board connection/probe/run','automatic model/GPU/EDA experiments','wb/luyou/heartbeat','editing frozen v3.1/v4 packages'],
      phases=['q01','q02','q03','q07','q08','q09','q10','q11'],
      proposed_data=dict(train='read-only hidden_v1/train1500',calibration='read-only hidden_v1/calibration320',
        final='new 1000 questions; not selected, not collected, labels not opened',final_quota=[400,250,100,250],
        lock_status='PENDING_SOURCE_AVAILABILITY_AND_EXCLUSION_AUDIT'),
      direct_gate=dict(decode_agreement_overall_min=0.999,decode_agreement_each_category_min=0.999,calibration_all_predictions_errors_max=0),
      refine_gate=dict(decode_policy_winner_recall_overall_min=0.999,decode_policy_winner_recall_each_category_min=0.999,calibration_all_predictions_misses_max=0),
      experiments=experiments)
    dump(MOD/'experiments/quantization_study/PLAN.json',plan)
    dump(MOD/'PROGRESS.json',dict(version='v4b',status='RESEARCH_DESIGN_COMPLETE_EXPERIMENTS_NOT_RUN',updated=STAMP,
      page='doc/design/V4bValidation.html',papers=16,experiments=len(experiments),baseline_hash_check='PASS',
      numerical='NOT_RUN',gpu='NOT_RUN',csim='NOT_RUN',hls='NOT_RUN',rtl='NOT_RUN',implementation='NOT_RUN',board='NOT_RUN',
      next='Execute only after a new explicit experiment instruction; no automatic resume.'))
    (MOD/'README.md').write_text('''# lm_head v4b · 量化方向并行研究

工程父版本为已上板通过的 **v3.1**，与候选稀疏化 **v4** 并行。当前阶段：论文调研、基线快照与实验设计完成；量化实现、模型测试、GPU、EDA、板测全部 **NOT_RUN**。

- [交互实验页](../doc/design/V4bValidation.html)
- [论文综述与16篇原文](../doc/paper/lm_head_quantization/README.md)
- [机器可读实验计划](experiments/quantization_study/PLAN.json)
- [基线来源与校验](baseline/SOURCE_LOCK.json)

baseline/v31 保存原源码/头、原验收报告和身份清单的小型逐字节快照。它是只读参考，不是可发布v4b内核。新量化kernel、descriptor、VLNV、build tag、CSR/layout均待分配，不复制旧bit/XSA/ELF或继承旧资格。v4仅提供只读模型身份，不作为v4b工程父版本。

首轮顺序：基线算术复现 → 32点RTN边界 → 8个新GPTQ/AWQ点与4控制 → 量化预筛12点与3控制 → packed/GPU/硬件成本 → 锁点后全新问题质量 → 新Csim/HLS/RTL/200MHz → 等待独占板测安排。W8A8、残差、码本/旋转按条件推进，不自动扩扫。

Qwen tie_word_embeddings=true；整网评估须克隆独立输出层，保留输入embedding BF16。所有旧已打开测试只作诊断，不能用于新认证。实验计划与参数尚未冻结为执行入口，不自动训练、量化、测速、EDA或操作板卡，不启用wb/luyou/心跳。后续融合另立实验。
''',encoding='utf-8')
    header='''# LM Head 量化方向：v4b 论文与实验路线

整理日期：2026-10-23。定向调研，非穷尽检索。工程父版本为已实板通过的v3.1，和v4稀疏候选路线并行。收录16篇作者arXiv原文，保留获取时版本、页数、来源元数据与SHA256；没有改写原PDF。论文版权与许可归原作者；收集用于本地研究，不推定再分发许可。

## 结论与优先级

优先做 **RTN W8/W4（另加W6/W12边界）→ GPTQ/AWQ head-only → HiRE-Q式预筛精算**。前两条保持全词表，压缩每行权重；第三条以全词表量化扫描选候选，再读canonical BF16行，保留赢家时可恢复原始score bits。W8A8/W4A8是独立计算优化阶段；残差、码本、旋转和向量查表条件推进。此排序是基于本项目独立M14与FPGA的工程判断，不是本地实验结论。

**直接量化通常不能保持原始logits逐位一致。** 必须区分量化实现对新golden的逐位正确性、对BF16赢家的一致率、闭环任务质量和性能。GPTQ原文Practical Speedups段（本地PDF第8页）明确其示例保留embedding/output layer为FP16；不能把整网量化精度直接当成head量化验证。作者OPT代码也在量化加载路径排除lm_head：[官方代码](https://github.com/IST-DASLab/gptq/blob/main/opt.py)。AWQ需审计实际head覆盖，不能仅看算法名。

## 本项目边界

- Qwen2.5-0.5B-Instruct，H896、V151936；canonical W=272269312B=259.65625MiB；hidden BF16仅1792B。模型配置tie_word_embeddings=true，必须克隆输出层，不能在量化head时连带改变输入embedding。
- v3.1实板200MHz、PL DDR、全词表；IP median/P95=117.751830/117.752020ms，来源[原RESULT](../../../module_14_lm_head_v3_1/reports/board_v31_20261019/RESULT.md)。这是有限归档输入的历史基线，不是本轮同轮实测。
- 本次核对原package清单9成员以及源码/头的profile SHA，保存[来源快照](../../../module_14_lm_head_v4b/baseline/SOURCE_LOCK.json)。没有重新校验整份canonical权重、跑模型、GPU、EDA或接触目标。
- FP32乘加/归约、全局history、repetition penalty正负分支、小ID同分规则必须明确；筛选按policy后的近似logits，防止raw赢家与惩罚后赢家不一致。
- b位主体理论体积=V×H×b/8；这不含scale、zero、残差、codebook、padding、ID、workspace和实际AXI流量。W4/W8理论分别64.9140625/129.828125MiB；W4-G128、FP32 scale、行64B对齐的拟议格式为74.1875MiB（不含256B文件头）。
- 量化精算要同时保存packed和BF16 W，W4上述格式合计333.84375MiB，已超过v4的320MiB arena；v4b拟另立512MiB布局，须重新审计，不复制v4地址/descriptor。
- 量化扫描字节Bq＋1792×K只是主要读取预算。还要Top-K、排序/gather和算术；不把压缩率当加速比，不用GPU论文数字预言AXU9EGB性能。

## 论文目录与本地笔记

阅读顺序：Q01/Q02 → Q12 → Q03/Q04/Q13 → Q14；Q05/Q06/Q07与Q08–Q11/Q15/Q16用于条件扩展。以下仅概括方法，不转载论文正文或把论文性能表转成本地结果。各篇的准确版本/作者/页数在manifest与BibTeX中。
'''
    sections=[]
    for p in papers:
        sections.append(f"\n### {p['id']} · {p['title']}\n\n"
          f"{'; '.join(p['authors'])}。{p['version']}，{p['pages']}页。优先级：{p['priority']}。\n\n"
          f"[作者条目]({p['source_url']}) · [原文PDF]({p['file']}) · [对应实验](../../design/V4bValidation.html#{p['experiments'][0]})\n\n"
          f"方法：{p['idea']}\n\n本项目改法：{p['adaptation']}\n\n边界：{p['limit']}\n\n重点阅读：{p['read']}\n")
    tail='''
## 实验组织与后续执行

[V4bValidation.html](../../design/V4bValidation.html)含12组实验、参数、控制变量、步骤、指标、门槛、依赖、论文映射及打包预算计算器；[PLAN.json](../../../module_14_lm_head_v4b/experiments/quantization_study/PLAN.json)为同源机器数据。所有结果为null/NOT_RUN，页面操作只浏览计划。

训练/校准仅拟复用旧train1500/calibration320的只读资产；新最终1000题必须排除所有旧分组和快照、重审代码题来源，锁入口后只评估一次。直接量化记录token一致率，预筛记录policy后赢家召回；校准保守准入要求零错误/零漏选，最终整体及每类decode点估计≥99.9%，并报告按问题分组的区间与整题一致率。该门槛不是数学无损保证。

本轮不打开新测试标签，不量化权重、不拟合/测速、不做EDA、不连接/探测/操作板卡，不恢复wb/luyou/心跳，不改v3.1/v4冻结包。v4实验10既有质量失败保持原结论；两版本融合须另立新计划与新认证组。

## 文件与核验

- catalog.json：筛选理由、方法笔记与实验映射。
- manifest.json / SHA256SUMS.txt：实际下载版本、大小、页数与SHA；源条目HTML另存Qxx_source.html。
- sources.bib：以arXiv版本作为来源，年份按arXiv标识年份，不混淆会议年。
- Qxx_extracted.txt：全文文字抽取辅助定位，可能存在公式/字符抽取缺陷，原PDF为阅读事实源。
- download_papers.py：显式执行才获取论文；不含模型/EDA/板卡控制。
'''
    (PAP/'README.md').write_text(header+'\n'.join(sections)+tail,encoding='utf-8')
    data=dict(plan=plan,papers=papers,baseline=lock)
    template=Path(__file__).with_name('research_page.html').read_text(encoding='utf-8')
    OUT.write_text(template.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')),encoding='utf-8')
    print(json.dumps(dict(page=str(OUT),papers=len(papers),experiments=len(experiments),baseline_files=len(lock['files']),package_members=len(lock['package_members_checked'])),ensure_ascii=False))

if __name__=='__main__': main()
