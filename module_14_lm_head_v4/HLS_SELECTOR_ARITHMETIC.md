# v4 路由与低秩预筛：确定性算术及接口

四个独立实验组件的后续阶段；不表示完整selector硬件、系统STA、板测或发布通过。
最终结果以`reports/SELECTOR_ARITHMETIC_STAGE_20261021.json`为准；没有该报告或报告未完成时不能标为全部通过。

## 低秩：保留因子，改变预筛调度

冻结参数仍为rank128的BF16 A[151936,128]、B[896,128]。
生成BT[128,896]仅改变存储次序，不改任何BF16 bits，A与BT总计39124992B。
先做z=hB，再做preview=zAᵀ；按全局history应用1.1 penalty。
正/零分数除以penalty，负数乘以penalty。Top-K接收已做policy的preview，不能再次惩罚。

z仅128行，使用已接受的H8/interleave16独立FP32乘加与规约顺序。
昂贵的A全词表扫描另行调度：每个128-bit beat读8个BF16系数，与8个FP32 z相乘，
相邻8路加法树得到beat部分和；每16个beat打包成512-bit context。
独立归约任务用完整相邻16路流水树接收context；读A、计算/收集、归约、policy写回通过FIFO连接。
因此不在每个词表行结束后重复等待原候选核的约102拍串行归约。

HLS中`product_word`和`tree_row`均目标II=1。前者每拍处理一个beat，context每16拍才到达一次；
后者具备II=1能力不表示整核每拍产出一个token行。
理想供数下A读入下限为151936×16=2430976拍，200MHz换算12.15488ms。
这只是A阶段结构预算，未计真实DDR停顿、B投影/启动、路由、Top-K、原行精算与系统调度，不是v4 decode实测。

新的FP32求和顺序与CPU BLAS一般不逐位一致，筛选允许这一差别，但必须复核候选覆盖。
最终candidate核仍使用canonical原始BF16行与原FP32合同，未改变最终精算的结合顺序。

### 低秩接口与失败合同

- 固定H896/r128，实验rows允许1..151936；正式调用用151936。
- 输入hidden/BT/A为BF16，history为全局位图，输出为FP32 policy preview。
- 容量单位是128-bit beat，预检hidden112、BT14336、A rows×16、history ceil(rows/128)、output ceil(rows/4)。
- 非法容量/penalty在访问矩阵前拒绝；hidden或BT产生非有限数时不写preview。
- A扫描中的非有限数会导致最终NUMERIC状态；部分preview可能已写入。
  所以下游必须检查本次status，失败时不得使用scratch中的旧值/部分新值继续Top-K。
- 输入在调用中不可变，输出与输入及其他scratch不重叠。组件不做系统地址范围和别名检查，尚待上层驱动实现。

## 聚类：确定性L2、最近4簇与候选表

使用冻结的128×896 BF16中心。norms[128]是对相同中心按FP32 NumPy sum(c*c)预计算并冻结的512B数据，
不是重新训练参数。每步hidden范数和中心dot采用H8/interleave16；
L2依次计算FP32 `hnorm + cnorm`、`2*dot`、二者相减，避免FMA/重结合。
按距离升序稳定选4簇，同距离选择较小cluster ID。

读取每簇至多16384个排名global ID，位图去重，加入151643..151656共14个特殊ID，
最后按global ID升序输出M4ID/V1表。簇内排名列表本来不按ID排序；输出必须排序唯一。
选中空簇时设置显式fallback并输出所有151936行，仍走PL DDR完整权重。
路由meta的norm/count共用AXI，目标II明确为2；列表读/位图更新顺序执行，不强行声明II=1。

容量：hidden112、centers14336、norm32、counts32、ranked524288 beat。
ranked固定128×16384 uint32（8388608B）；counts说明各列表有效长度，尾部sentinel不读取。
输出容量先按选中长度总和+14的保守上界检查，fallback时要求完整词表容量。
非法norm/count/ID或非有限输入在输出M4ID表前拒绝，不发布部分候选表；调用方仍须检查status。

## 数值与质量证据的范围

四类calibration各取一个真实decode hidden，逐位校验完整151936个policy preview；
新preview与原BLAS有约13万项末位不同，但这四例Top-16384集合不变。
router的完整M4ID表与原参考相同。
整个校准集5095预测/4775 decode又用显式乘/加树GPU模型复核；
四类完整preview先与NumPy/CSim fixtures逐位核对，报告记录源代码、参数、manifest SHA。
GPU模型不是HLS执行器；全校准结果不能标成4775次RTL或实板测试，亚正规数行为也未获完整RTL资格。

完整C串接用实际四个C函数、同一hidden/history及canonical权重；
比较完整候选ID、所有候选raw logit、dense轨迹token/score bits/CRC以及容量guard。
`selector_chain_csim_unit.cpp`仅为测试用unity translation unit，避免导入数值头多重定义，
没有生成单一顶层IP或验证多核AXI并行。

## 集成仍需完成

为PL DDR计算缓冲区分配不重叠64位地址，绑定参数/权重SHA与实际目标回读；
定义父级状态机和错误传播、scratch发布顺序、容量/别名/地址检查及多master仲裁。
再做完整selector RTL、200MHz完整BD/CDC/STA、配套加载镜像和新的独占板卡验收。
真实计时覆盖hidden可用到token/score可用的全链；不能用本页12.15ms预算或子模块模型耗时换算实板token/s。
上游直接供权重仍等待负责人框架文档，不新增外部stream合同。
