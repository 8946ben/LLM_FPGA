# lm_head v4 离线续办检查点

## 实验10全部离线测试已结束（当前最高优先级）

- 完成时间：2026-10-23T14:25:51.383584+08:00。事实源：module_14_lm_head_v4/reports/fusion_exp10_20261023_r1/RESULT.json、RESULT.md。
- 432点校准、1080次GPU计时/36完整数值对照/4夹具轮换1000调用、锁点新1000题、Csim/HLS/完整RTL/200MHz系统/匹配BSP两ELF及本地镜像/研究包已核验。锁点C256_R4_L8192_r64_T16384新decode漏19/14986、99.8732%，质量门槛失败；冻结融合对照漏2、99.9867%。工程通过不能替代质量通过，不发布锁点，不用此已打开组调参再认证。
- RTL中文周期4886566仅debug+AXI模型；真实FPGA/整网decode/TTFT均NOT_RUN。200MHz WNS+0.761ns。私有GPIO0x4D345A0A/descriptor_v2/tag0x8507826e与研究包绑定，不混用冻结旧包。
- 不操作板卡，不恢复wb/luyou/心跳，不改封存和冻结基线。此一次性流程已结束；不自动开始新实验。后续等待用户新的研究/独占板卡安排。下方所有活动PID/进行中/旧未开始文字均为历史。


## 2026-10-23T13:44:02.259807+08:00 用户恢复实验10，复用opt DCP续建（当前最高优先级）

- 用户明确恢复；11份检查点/301私有IP/冻结入口23文件/系统输入SHA全部通过，无旧EDA残留，G盘可读。中断impl目录58文件65,294,317B已另存.cache/e10_impl_pause_preserved_20261023并逐文件SHA核对，原暂停和日志保留。
- 使用本机2021.1帮助核对reset_run -from_step place_design；新Tcl experiments/fusion_exp10_20261023/experiments/board_v4_20261021/resume_implementation_20261023.tcl只重置未完成布局及其后阶段，要求既有综合完成/opt DCP存在，复用综合与opt，不重建BD。原build.tcl不改。
- 当前一次性父流程scripts/resume_fusion10_after_pause_20261023.ps1已启动；真实状态/PID见reports/fusion_exp10_20261023_r1/OFFLINE_WORKFLOW.json（启动快照10940），日志resume_20261023_r1/workflow.log、system_build_resumed.log。旧STOP标记已移入本轮恢复目录存档。按布局布线→审计→匹配BSP两ELF→离线包/最终文档顺序，错误或新STOP即停止，不自动重试。暂停先核对当前父PID/创建时间并停止父树，勿用历史PID。
- 不重跑已完成RTL/GPU/新质量；锁点质量失败19/14986保持，不换点、不重认证。仍不连接/探测/操作板卡，不恢复wb/心跳，不改冻结/封存版本。下方暂停与活动进程均为历史，以本节与真实产物为准。


## 2026-10-23T10:33:26.006396+08:00 用户要求断电，实验10已安全暂停（当前最高优先级）

- 已先核对并停止本轮续建父进程，再停止所属Vivado树；PROCESS_AFTER复核无本任务续建/EDA残留，STOP_REQUESTED已创建，不自动恢复，不启动新作业。当前可断电，无板卡操作。
- 事实源：module_14_lm_head_v4/reports/fusion_exp10_20261023_r1/pause_20261023/CHECKPOINT.json。完整官方RTL/41943040内存值/18标量及原C后校验、301私有IP/CSR/数值源身份通过；新9子IP和顶层综合完成。opt_design通过，58,351,687B的opt DCP已保存、ZIP CRC及SHA核验。
- 暂停发生在place_design Phase4.1，尚无完整placed/routed检查点，恢复需重做未保存的布局；不能标200MHz STA/CDC/DRC、bit/XSA/BSP/ELF或完整离线包已通过。旧日志/失败工程全部保留。
- 恢复只在用户明确要求后，先核对G盘、源/入口/IP和检查点SHA及实时进程，复用全部完成综合与opt DCP，另立实现续办脚本/日志；不要直接重跑旧continue/resume脚本（其中含create-BD，现工程已存在）。不重跑已完成RTL/GPU/新质量。
- 锁点新质量仍失败19/14986，对照2/14986；不利用已打开组调参认证。板卡仍不在范围，不恢复wb/luyou/心跳，不改冻结/封存版本。下方所有进行中和PID均为历史。


## 实验10私有IP完成，新200MHz完整系统构建中（当前最高优先级）

- 最新执行更正：首次BD因实例化语句残留旧user.org/4.0失败已保留；已改为exp10.local/4.10，新BD r2验证通过，topology_audit_r2为两AXI64仅PL DDR/实际配置199.998001MHz。当前父流程PID以OFFLINE_WORKFLOW实时为准（快照17848），日志system_resume_r2.log；旧r1不再运行。PS和MIG子综合已通过，现在selector子综合，尚无完整STA/bit/XSA/ELF结果。

- 完整官方RTL及全量逐位核对已通过，不重跑。导出已修复遗漏impl暂存、2021.1布尔语法与2026 core_revision整数溢出，原失败日志及元数据全部保留，见EXPORT_QUALIFICATION.json。导出仅关闭额外死锁监控，96份可综合Verilog严格等价；301私有IP文件、实际CSR偏移/两AXI64审核冻结PASS。
- 正在顺序运行scripts/resume_fusion10_system_20261023.ps1 -Run；真实PID/阶段看reports/fusion_exp10_20261023_r1/OFFLINE_WORKFLOW.json、EDA_PROGRESS.json和system_resume_r1.log，不再运行旧continue脚本。先创建.cache/e10_bd，再200MHz实现/审计、匹配BSP/两ELF、离线包/最终文档，任何失败停止，不自动重试。暂停前核对本轮CIM并停止该父树；无独立旧HLS残留。
- 质量失败19/14986保持，不换锁点、不重跑新问题，不连接或探测板卡、不恢复wb/心跳、不改冻结基线或封存交付。下方旧PID/进行中为历史。


## 实验10完整RTL通过，IP导出修复后继续（当前最高优先级）

- 官方CoSim及41943040内存值/18标量严格对照、原C postcheck通过，见reports/fusion_exp10_20261023_r1/RTL_QUALIFICATION.json；中文debug K17764、4886566周期仅AXI仿真模型。不得重启此CoSim。
- 原一次性流程已因导出缺失impl/verilog而退出，失败状态另存*_export_r1_failure.json。短克隆遗漏综合生成的impl暂存目录，已从同份原综合补齐217文件并核对全部Verilog与已验证syn一致，见EXPORT_STAGING_REPAIR.json。r2选项布尔语法失败保留；r3使用实际帮助认可的无值开关，关闭导出附加死锁监控以保留计算RTL，真实进度看export_existing_r3.log。
- 后续仅在IP导出及PRIVATE_IP_AUDIT通过后手动顺序启动scripts/resume_fusion10_system_20261023.ps1 -Run，完成新200MHz实现、匹配软件与离线包；不重跑质量/参数扫描。下方旧活动PID为历史，暂停前核对本轮CIM。
- 新问题锁点19/14986漏选的质量失败保留。仍不访问板卡、不恢复wb/心跳、不改冻结及封存版本。


## 实验10一次性离线续建流程已启动（当前最高优先级执行安排）

- 当前已有短路径CoSim不重启。一次性顺序流程scripts/continue_fusion10_after_rtl_20261023.ps1正在等待这份既有HLS，真实状态/PID见reports/fusion_exp10_20261023_r1/OFFLINE_WORKFLOW.json；不是wb、luyou、心跳或新参数扫描。
- 只有现有HLS真正输出CoSim PASS并退出，且41943040内存值/18标量严格比对及原C postcheck合格，流程才会执行IP导出→新200MHz完整系统及审计→匹配BSP两ELF→四镜像/研究包审计→最终报告与页面检查。任何错误或STOP_REQUESTED均停止，不自动重试或放宽条件，不碰板卡。已打开质量失败不调参，不重跑。
- 暂停必须先核对并停止OFFLINE_WORKFLOW中本轮续建父进程树，防止它启动下一阶段，再停止当前所属HLS/Xsim/其他EDA树；原HLS最初独立于续建器启动，不一定是其子进程。先以当前CIM命令行/创建时间核对，勿用历史PID。当前原HLS匹配cosim_short.tcl；短构建.cache/e10、系统.cache/e10_bd、BSP.cache/e10_ps及所有失败/日志保留。
- 37项Python/Tcl宿主、25fake-MMIO、88loader组合及原始公开源重建问题/prompt哈希审计PASS。事实源HOST_QUALIFICATION.json、PUBLIC_SOURCE_RESERVATION_REVIEW.json。仍无完整RTL或新bit/XSA/BSP/ELF完成结论；以实际报告为准。

## 实验10 EDA短路径修正（后续以此为准）

首轮exp10_cosim_r1真实C参考通过，但工具在生成浮点IP时因Windows260路径限制失败，尚无RTL计算；原日志完整保留。bat返回0不能代表PASS，原HLS_COSIM.json已转存wrapper_exit0_falsecompletion_r1，新runner要求真实Tcl PASS标记。

正在用.cache/e10/hls重试cosim_short.tcl（报告hls_exp10_cosim_r2_short.log），317份综合输出逐文件SHA与首轮一致，见SHORT_PATH_REUSE.json。只复用综合，不更换源码/参数/数值/最终质量；新生成C事务是同一夹具，不重测独立质量。qualify_fusion10_rtl_20261023.py与freeze_fusion10_ip_20261023.py都绑定短路径。

为避免后续相同问题，隔离完整系统工程改放.cache/e10_bd、BSP工作区.cache/e10_ps；所有路径都在本项目内。报告、镜像、实际src/include/fixtures仍在独立experiments/fusion_exp10_20261023。保留所有失败；不要启动第二份重EDA或操作板卡。

## 2026-10-23 实验10锁点新质量失败，离线硬件资格继续（当前最高优先级）

- 用户确认G盘已连接、板卡未连接；继续完成实验10非板卡测试，不连接/探测/操作FPGA，不恢复wb/luyou/心跳，不改原冻结v4及封存版本。
- reports/fusion_exp10_20261023_r1/已完成432点实际并集校准（56合格）、5入围+4控制GPU共1080次计时/36完整数值证明、锁点1000次变输入稳定性及独立复核。按预定逻辑读取量目标锁定C256/R4/L8192+r64/Top16384，不按新质量或GPU速度更换点。
- 锁点校准5095预测零漏选，decode K均值23001.59/P9530482；主要逻辑读取58.47MiB对照87.49MiB，只是预算，非实际AXI流量/FPGA加速。GPU参考锁点67.955次/s、冻结融合67.683、dense66.504，4固定输入FP32 Eager，不代表整网decode。
- 全新1000问题/15986预测/14986decode/零排除已经采集评估一次。锁点漏19（中文11/英文7/代码0/数学1）、召回99.8732%，整体及中英未达99.9%；状态QUALITY_FAIL_NO_RELEASE_NO_RETUNE。相同新组的预声明冻结融合对照漏2、99.9867%，整体和各类过门槛。FINAL_QUALITY_REVIEW.json来源/数组/计数/并集复核通过；不得用已打开组调参再认证。
- EVALUATION_ENTRY_LOCK在新标签前冻结源码/参数/语料；PowerShell包装器在Python评估exit0后因R/r大小写JSON解析失败，原失败已留QUALITY_WORKFLOW_wrapper_failure_r1.json，不重跑评估；独立复核后修正流程状态。旧generic progress的holdout_read:false字段误导，已保留原快照并在新PROGRESS明确新组已打开。
- 隔离硬件experiments/fusion_exp10_20261023/descriptor_v2、config_tag0x8507826e、GPIO0x4D345A0A。真实Csim7正确（A→B→A及四类/生产）、24预检拒绝/5错误门控PASS；HLS估计3.650ns/153BRAM18K/231DSP。原数值源/fixtures/入口SHA不变，不能因HLS通过抹掉质量失败。
- 当前HLS综合后官方CoSim运行exp10_cosim_r1，真实C参考中文K17764已过，正在完整320MiB事务生成；核对hls_exp10_cosim_r1.log和真实输出，不重复启动。不把C参考/进程存活称为RTL PASS。重EDA顺序：完整RTL+41943040内存值/18标量审计及原C postcheck，再新IP导出/200MHz系统审计/匹配BSP两ELF和离线包。
- 四类320MiB生产arena本机SHA/320块CRC/9源区域/13guard通过；新host_r2 C/13mock协议及镜像预检PASS，host_r1共享数据根目录错误保留；25fake-MMIO/8mailbox/3布局测试通过。均无socket或目标访问。支持脚本的路径修正不改变冻结数值源；尚未生成新bit/XSA/BSP/ELF。
- 暂停须先核对当前真实进程树并停本轮HLS/仿真（报告STOP标记只阻止新阶段，不能中止已运行EDA），保留所有事务和日志；不要使用历史PID。无自动下阶段EDA或心跳续跑。

## 2026-10-23 当前任务：实验10融合432点与非板卡完整验证

用户要求“根据实验8/9设计融合调超参实验10，并完成板卡之外的所有测试”。本机GPU/EDA/新独立质量及选定点离线硬件在授权范围；板卡暂未连接，严禁连接/探测/操作，不恢复旧wb/心跳。G工具盘已恢复并实际确认2021.1入口，不再等待板卡/工具路径。

- 计划及真实阶段：`module_14_lm_head_v4/reports/fusion_exp10_20261023_r1/PLAN.json`、`PROGRESS.json`、`CALIBRATION.partial.json`及各日志。432点全部做真实并集；缓存已完成，当前scan进行中。入口`fusion_experiment10_20261023.py`各阶段手动顺序，不存在自动续建器。
- 网格C=[64,128,256,512]、R=[2,4,8]、L=[4096,8192,16384]、r=[32,64,128]、T=[2048,4096,8192,16384]。calibration320/4775decode，要求零全部预测漏选/无fallback及K/320MiB预算后按主要逻辑读取量入围，GPU仅实际参考，不外推FPGA。
- fresh问题文本已预留1000：中400/英250/代码64/数学286，排除全部旧组；仍无新标签。新参数/实现/入口冻结后才能采集，一次最终质量失败不能调参重认证。实际tokenizer预检在`data/fusion10_quality_20261023/`。
- 下一阶段：完成scan→入围GPU及1000次变输入功能调用→选择锁→派生隔离硬件与真实Csim→冻结算术入口/采集评估新问题→选定点HLS/CoSim/200MHz系统及离线资产测试。保留失败，任何未测不写PASS。
- 实验10代码及生成硬件放新文件/`experiments/fusion_exp10_20261023/`，原src/include/IP/private_package及封存版本不改。暂停在新reports目录放STOP_REQUESTED并核对真实退出，不能误用历史PID。

## 2026-10-22 合并质量/速度报告，GPU参考测速完成（当前最新）

- 用户要求质量和速度合并，正式实验名、明确状态、论文式数据说明，并列质量折线图。doc/design/V4Validation.html现在7组31具体场景；实验1“lm_head稀疏化方案（仅聚类/仅低秩/混合）的质量与速度对比”，含dense对照，质量/GPU已完成、FPGA未开始。数据从主日志v4_validation唯一快照生成；新工具tools/update_v4_quality_speed_report_20261022.py导入已完成结果，不执行GPU。
- 主模型实际执行新GPU参考脚本scripts/benchmark_gpu_methods_20261022.py，r2已exit0。报告reports/gpu_method_benchmark_20261022_r2/RESULT.json；4校准固定输入（中index1/英1281/代码2536/数学3816），16 case×method均完整ID/raw bit/final result对CPU一致后，每组合3预热+30测量，共480次计时。PyTorch2.13.0+cu130 / RTX5060 Laptop；batch1、BF16权重常驻GPU、FP32因子；包含筛选/gather/FP32展开/精算/policy/token-score返回CRC，排除前级及上传。GPU参考速率dense66.33/聚类135.18/低秩164.55/混合84.36次/s，非优化GEMM/Tensor Core生产GPU、全语料速度、整网token/s或FPGA预测。
- 同目录PLAN.json、RAW_OBSERVATIONS.json、NUMERIC_PROOF.json、benchmark_source.py及INDEPENDENT_REVIEW.json保存身份与真实观测；聚合/median/P95已只读重算。不能把质量1000问题与GPU4校准输入当同一个测速总体。
- 首轮r1在质量预检发现27项preview偏1ULP，立即停止且无计时结果，源码与失败PROGRESS保留。新benchmark将Python标量除法换为显式GPU FP32系数张量后r2完整逐位通过；冻结质量/RTL/生产源码和包未改。不能放宽位一致或用新独立测试集调参。
- 用户暂不上板仍生效，当前无GPU/EDA后台续跑，不连接/探测/操作FPGA、不恢复旧wb/心跳。后续离线新K绑定、多步/debug/错误路径；未来FPGA速度必须使用匹配输入/同计时边界重新实际测。图表/报告结构与JS语法通过，file://视觉预览仍受工具策略限制。

## 2026-10-22 新质量与候选规模离线准备完成（当前最高优先级）

- 用户明确“暂不上板，继续离线准备”：不连接、探测或操作FPGA，不恢复旧wb/luyou/心跳，封存v2/v3/v3.1及private_package_r1不改。下方旧PID/执行中记录均为历史；本轮新GPU流程session61971已exit0，不重启。
- 固定算术新独立1000问题/14958 decode/零排除：route80漏选/99.4652%、lowrank356/97.6200%、hybrid1/99.9933%。hybrid中文1/6000，其余0；首输出0/1000，999/1000问题后续dense轨迹全覆盖。通过预先拟议整体/分项99.9%点门槛，非无损/自由生成/完整新RTL回放/板测。规范化哈希与所有旧保留组无重叠，配置/代码/来源/入口在标签前冻结。不得用本已打开组调参认证。读reports/fixed_quality_20261022/RESULT.json及INDEPENDENT_REVIEW.json（相对v4目录）。
- 新K均值29300.93、中位28183、P9541630、max56075，旧RTL K21529偏小；34.131530ms/29.2984仅单例debug仿真模型，与历史v3.1的3.4499倍比值不能称实板加速。完整200MHz实现及匹配BSP/两ELF/内部包保留，v4实板decode/P95/TTFT仍NOT_RUN。
- reports/performance_cases_20261022/四组K17071/28184/41630/56075已导出真实hidden/history；固定CPU候选数匹配GPU记录，候选ID/preview/raw记录/policy/精算golden齐全。4组token/score bits/CRC与dense一致；4份320MiB生产arena各经全SHA、320块CRC、9源区域、13guard本机预检，34项未来目标READ准备完成，128B请求未发送。runtime scratch未预填golden。
- QUALIFICATION.json为离线身份/记录排序/CRC/policy tie-break/dense一致及镜像预检；不是4组新RTL或目标测试。准备脚本prepare_performance_case_goldens_20261022.py与finalize_offline_preparation_20261022.py均保留且拒绝覆盖旧产物，不需要重复运行。所有本轮计算已结束。
- private_board.py已有13项host/Tcl mock检查，默认纯离线。现入口仅允许原四fixture；新性能用例仅完成golden/arena/request，campaign绑定仍待扩展。下一步离线完成新K绑定、多步hidden/history、debug完整候选及错误路径准备；真实30计时/1000稳定性必须等新的独占上板安排后执行。

## 2026-10-22 性能报告与下一阶段执行中（当前最新）

- 用户要求报告v4性能并开始下一步。已保存reports/PERFORMANCE_ASSESSMENT_20261022.*：RTL单正确中文debug样例6826306周期/34.131530ms@200MHz、29.2984等效M14输出/s；与v3.1实板117.751830ms/8.4924之比3.4499仅为跨证据参考，不能声称实板加速。K21529/V151936精算行减少85.8302%；板测P95/整体LLM吞吐/TTFT均未测。
- 新private_board.py及Tcl控制入口已完成12项纯宿主/Tk Tcl mock测试，默认仅生成本机计划，无XSCT/socket/板卡访问。真实GEM3 0xff0e0000须先停loader CPU，再请求TX halt、RX/TX停用并验证TXGO/读回，才允许替换ELF。实际停机行为仍NOT_RUN；默认批次仅固定输入，不覆盖debug/多步/全部错误路径。
- 新独立质量组已冻结1000（中文400/英文250/代码100/数学250），排除v1各split/998快照及r2/r2b全部问题组，规范化哈希无重叠。代码来自HumanEval官方提交b9453e8f1865df0a0057a1383767caa400acfbcf，源/许可证SHA保留，raw下载超时后同提交GitHub contents API成功。仅使用prompt，不执行代码/参考解。
- 当前一次性本机GPU顺序流程scripts/run_fixed_quality_20261022.ps1 -Run（PID14932/session61971）：先全部1000真实tokenizer输入长度预检、8步canonical head证明，再固定轨迹采集和固定算术聚类/低秩/混合评估；不调参、不复用旧outcome。不把预留或校准称为新质量PASS。
- 实际Python为C:/Users/ben/AppData/Local/Programs/Python/Python312/python.exe，Torch2.13.0+cu130/Transformers5.15.0/RTX5060。沙箱看不到该安装，须本机运行；用户无需再找路径。真实阶段看reports/fixed_quality_20261022/WORKFLOW.json与对应日志，勿重复启动。
- 用户暂停时先停止此顺序父进程树（核对最新PID，不用旧PID）；可先在data/hidden_fixed_20261022/STOP_REQUESTED和reports/fixed_quality_20261022/STOP_REQUESTED请求prompt/batch边界停止，防止自动进入后续评估。停止后保留所有数据/失败；续办核对源/参数/语料SHA。无旧wb/luyou/心跳，无FPGA操作，封存资产不改。新板测仍需新独占安排。

## 2026-10-22 v4本轮离线阶段完成（当前最新）

- 用户“恢复v4”后，复用保留的r5结果完成41943040内存值/18标量严格比较、原C postcheck exit0及冻结源码/私有IP审计；整链资格PASS_OFFLINE_INTEGRATED_SELECTOR_RTL。未重跑整夜仿真，原官方HLS包装FAIL仍保留。
- 同一hardware_r2 XSA匹配BSP、arena_loader和selector_test两个A53 ELF已真实构建PASS，寄存器头/PHY补丁SHA/无未解析符号/PS LOAD区间审计通过。实际GEM地址从本轮BSP导出为0xff0e0000，禁止硬编码GEM0。
- 首次BSP生成共享文件占用失败保留在selector_ps_platform_r2_20261021.log；确认生成进程退出后同XSA显式恢复成功，r3日志含M14_V4_PRIVATE_PLATFORM=PASS。软件结果reports/ps_software_20261022_r1/BUILD_SOURCES.json。
- 内部工作区包reports/board_v4_20261021/private_package_r1/共14文件（13成员+SHA清单），独立复核包内SHA、XSA内bit及PS初始化、两ELF架构/LOAD、四类320MiB arena身份PASS。报告reports/resume_20261022/PRIVATE_PACKAGE_VALIDATION.json。不是正式移交ZIP或板卡验收。
- 直接资格/软件流程均exit0；复核无xsim/vivado/vitis_hls/xsct/java/tclsh进程，无后台续办。不恢复旧wb/luyou/心跳，无板卡连接/探测/操作，封存版本不改。
- 后续先离线准备并审阅板卡控制/GEM DMA停机交接脚本；新算术须新问题级独立质量认证（旧holdout不可调参/复认证），实板需新独占安排。本轮v4实板decode/token/s/TTFT仍NOT_RUN；6826306周期是debug+仿真AXI模型，不能填作实测性能。

## 2026-10-22 整链RTL资格通过，匹配软件构建中（当前最新）

- 已复用暂停保留的r5输出完成全部41943040内存值/18标量比较、原生成C postcheck（exit0）及冻结8源码/301私有IP文件审计，状态PASS_OFFLINE_INTEGRATED_SELECTOR_RTL。真实中文K21529/token20412/score0x41de477c及重叠拒绝通过。原官方包装命名冲突FAIL仍保留，不改写为官方CoSim PASS。
- 6826306/726周期只属于5ns AXI仿真内存模型、debug路径，不是实板生产decode/token/s/TTFT。修复了审计报告路径及C/Verilog事务编号空格填充兼容，未修改DUT、golden、已编译快照或原r5输出；未来Tcl另存r6。
- 当前直接顺序执行scripts/finish_v4_offline_20261022.ps1（PID30848/session74525），新XSA BSP/两ELF/内部离线包构建中；无旧续建等待器，进度以OFFLINE_SEQUENCE和真实构建日志/结果为准。用户暂停时停止此新流程树，勿操作旧PID。
- 四类320MiB生产arena本轮重新离线SHA/CRC/源区域/描述符预检通过，未访问目标。200MHz系统实现/bit/XSA保留。不操作板卡、不恢复旧wb/luyou/心跳，封存版本不改。后续仍需新算术独立质量与新独占板测安排。

## 2026-10-22 用户恢复v4（覆盖下方暂停）

- 用户明确“恢复v4”，主模型恢复离线资格校验；不连接/探测/操作板卡，不恢复旧wb/luyou/心跳，封存版本不改。
- 保留r5原始日志、旧Tcl、compiled snapshot及所有输出，不重新仿真。修正审计报告路径，并用暂停SHA、真实testbench finish、两事务及全部输出尾标恢复资格；仍需完整41943040内存值/18标量比较及原C postcheck，未通过前不报整链RTL PASS。
- 后续结束Tcl修正版另存selector_progress_r6.tcl，旧r4及观测manifest不改。新资格序列scripts/qualify_preserved_selector_20261022.ps1仅做校验，不自动重启模拟器/后台等待器。
- 校验通过后再顺序做本次XSA匹配BSP/两ELF/内部离线包；进度以PROGRESS和OFFLINE_SEQUENCE状态及真实产物为准。

## 2026-10-22 08:23 用户安全暂停（当前最高优先级）

- 用户明确“先安全的中断当前的任务，等会儿我们继续”；已先停止一次性续建器PID24616，再停止r5 XSim包装进程树PID3088。复核无EDA或本任务续建器残留；不自动恢复、不启动校验/BSP/ELF/内部包，不恢复旧wb/luyou/心跳。
- 最新发现：r5原始testbench已输出两事务报告及10份完整runtime尾标，日志有真实`$finish`（34134837500ps）；但Tcl结束门和两个审计器误等`sim/report/verilog/result.transaction.rpt`。实际报告在`sim/verilog/lm_head_v4_selector.performance.result.transaction.xml`，导致输出完成后仍空跑。此前仅凭窗口递增判断仍计算不准确。
- 原报告记录6826306/726周期，尚未通过全量41943040内存值/18标量比较或原C postcheck，不能宣称整链RTL PASS，也不作为板上decode/token/s。所有输出、日志、编译快照保留，暂停清单保存SHA；本轮未修正脚本、未运行后校验。
- 恢复先读`module_14_lm_head_v4/reports/pause_20261022/CHECKPOINT.json`及PROGRESS，再修正报告路径/结束门并以明确恢复证据资格验证已有输出，优先避免无必要重跑整夜RTL。资格通过后才顺序构建匹配BSP/两ELF/内部离线包；尚无这些产物。
- 200MHz完整系统实现审计PASS和bit/XSA保留；仍无板卡连接/探测/操作，本轮v4实板decode/token/s/TTFT均NOT_RUN。v2/v3/v3.1封存不改。等待用户明确恢复。

## 2026-10-22 继续：离线软件准备，RTL r5保持运行

**07:02后续建已启动：** `scripts/continue_offline_after_rtl.ps1`，session2040/PID24616；状态`reports/OFFLINE_SEQUENCE_20261022.json`。当前WAITING_EXISTING_RTL，等待r5完整RTL/全量trace/原C postcheck和证据收集真正PASS后，顺序启动匹配BSP/ELF构建、ELF布局审计及内部`private_package_r1`整理。不并行启动重EDA，不操作板卡，任一资格/构建失败会写明状态并停止。之后先读此状态及实际结果，不重复手工启动；用户若暂停，先停止这个续建器，再停止既有EDA，防止后续自动开始BSP。

用户“继续”。不连接/探测/操作板卡，不恢复旧wb/心跳，不修改封存版本。
XSim r5/session71531仍为当前唯一重EDA，已进入候选精算；完整两事务/trace/C后检查尚未完成，不能报RTL PASS。继续前先检查真实日志和结果，不重复启动。

- `standalone/arena_loader/`：从只读v3.1来源派生，私有M4AR v1/port1415，完整335544320B arena，64位0x400000000目标地址，私有GPIO2签名/校准/IP空闲门控，保留GEM发送重触发和64位目标CRC。新增最多512B的READ及完整响应部分ACK跟踪，供34处源区域sentinel/descriptor/guards回读比较。
- `standalone/upload_arena_tcp.py`默认仅验证本机文件；只有显式`--upload`才连接网络。当前只运行本机检查和mock socket测试，未传输到板卡。验收报告`reports/arena_loader_20261022/host_r1/RESULT.json`：C协议/边界/CRC/88种对齐长度与ACK检查、13项Python通过，包含320MiB真实文件的mock收发和错误回复/descriptor不匹配拦截。不是lwIP真实接收链路或PL DDR测试。
- `standalone/selector_ps_main.c`、`selector_ps_mailbox.h/.py`：私有单批次测试程序，RUN先对实际目标完整arena读回CRC，再固定输入运行warmup+计时+稳定调用。独立记录全control_call起止XTime tick（包括PS读取与CRC验证token）及COUNTS_PER_SECOND；`wait_us`仅辅助诊断。随机nonce拒绝旧批次capture，失败/不完整调用不统计性能。文件解析8项测试PASS，合成测试值绝不当板测。
- `reports/arena_loader_20261022/TARGET_SYNTAX_HISTORICAL_BSP.log`为A53编译器对5个C源码的语法检查；仅只读引用历史BSP，无最终目标文件或匹配v4 ELF。新的BSP/ELF仍未生成。
- 待RTL序列完成，再执行`experiments/board_v4_20261021/build_ps_software.ps1`：匹配r2 XSA生成新BSP并编译arena loader与selector test两个ELF，验证BSP寄存器映射/源SHA/无未定义符号/实际ELF64 AArch64 LOAD只在PS软件0..0xfffffff，仍不执行任何板卡操作。脚本拒绝与EDA并行，日志/结果不覆盖。
- 审计脚本改为流式扫描日志和SHA，避免不断增长的DSP警告日志造成整份读入内存；未抑制警告、未改DUT或金标，也未降低完整输出比较范围。
- 额外三类english/code/math生产arena已生成并通过本机完整SHA/320块CRC/9源区域/34回读检查准备；证据在各`selector_arena_<case>_20261021/`和`arena_loader_20261022/HOST_PREFLIGHT_<case>.json`。含中文共4类320MiB文件均未装载板卡，也不是新独立质量测试。

下一阶段仍需匹配软件构建、真实目标加载/功能/计时/稳定性和新算术独立质量认证；v4实板decode/token/s/TTFT均NOT_RUN。

## 最新：用户恢复v4，离线续跑r2

### 23:05 完整系统实现完成，独立硬件审计PASS

**23:48活动状态覆盖下方早期仿真启动记录：** 当前唯一EDA为`run_selector_observable_rtl.ps1`/XSim r5，日志`reports/selector_repaired_xsim_r5_20261021.log`。r3因默认每1000万拍打印一次、不利于长任务诊断而主动停止；部分输出和进程身份已保留。r4因XSim解释Windows反斜杠路径失败、未开始仿真，严格完成审计拦截，失败日志不覆盖。r5仅将Tcl路径改为正斜杠；控制脚本每100us仿真窗口报告一次，最终仍需两事务报告、全部输出runtime尾标、41943040内存值/18标量严格比较及原C postcheck。编译快照二进制/类型/重定位等9个payload SHA与r3相同；HLS源码/DUT/测试输入/金标不改。证据`XSIM_OBSERVABILITY_CONTROL.json`。不要重复启动已有XSim；先核对session71531或活动日志/结果。

23:57已实际完成5个窗口（请求推进至500us），未完成事务，不是有效整链延迟。长仿真保持运行，不是再次暂停。既有顺序脚本会在仿真结束后自动执行严格trace比较、原C后检查和证据收集；仅全部通过后生成`SELECTOR_INTEGRATION_RESULT_20261021.*`并更新PROGRESS终态。不会自动启动BSP或板卡工作。若进程已停止但没有新PASS报告，先读r5日志、trace审计和postcheck日志定位失败，不按旧running字段推断仍在执行。最终报告/真实活动优先于本静态检查点。

计时接口补查：selector没有板上周期计数器，`wait_us`只计启动到AP_DONE轮询，不含结果读取/CRC。未来板测须另存完整token-ready调用的原始A53 tick及COUNTS_PER_SECOND。具体加载/验收/计时口径在`standalone/BOARD_ACCEPTANCE_PLAN.md`；当前BSP/ELF/目标装载均未执行。

- `reports/board_v4_20261021/hardware_audit_r2.json`状态PASS_OFFLINE_SYSTEM。5ns目标：WNS+0.652ns、WHS+0.010ns、WPWS+0.143ns，setup/hold/pulse-width失败端点均0；内部无未约束端点。CDC Critical0，4项CDC-15均为工具dbg_hub；MIG警告0，最小bus skew裕量+4.136ns。
- 全系统资源：69585 LUT、110132 FF、78.5 BRAM tile、250 DSP。不是单核HLS估计资源。
- DRC 0 Error/0 Critical Warning，816 Warning/211 Advisory仍保留：DSP浮点IP流水/PCIN等、dbg_hub LUT项和MIG无负载网络。没有将这些警告消除；实际板卡数值仍待验收，不宣称零警告。
- `hardware_r2/m14_v4_system_wrapper.bit` SHA256 `ac56c15e12c4f48de1687595cfea22c236256313b461f7773585e9053519e660`；`m14_v4_single.xsa` SHA256 `92186811d657c3f311b56fa91d798f348b89c849b6e87d9c46662b9bced0e0d2`，XSA内嵌bit逐字节SHA匹配。工具配置PL0为199.998001MHz、STA约束5ns，不是物理板卡测频。
- Vivado已正常退出。当前只运行`scripts/run_selector_repaired_rtl.ps1`的完整XSim/trace/C后检查序列；原官方HLS包装FAIL仍保留。整链RTL/实际PS软件/板测/发布未通过。
- 已准备`experiments/board_v4_20261021/platform.tcl`与`prepare_ps_platform.ps1`，默认只校验当前bit/XSA与硬件审计SHA，预检PASS。实际生成须`-Build`，并拒绝与EDA进程并行；当前未执行BSP生成。新workspace为`build/board_v4_20261021/ps_workspace_r2`，不复用旧平台。脚本不含板卡连接/下载指令，不代表已有BSP/ELF/loader。

用户明确“恢复v4”，解除下方20:03暂停。冻结301项IP/8项源码/布局/参数SHA全部相符。
本机无原EDA进程冲突后已启动两项离线任务，不连接、探测或操作板卡，旧wb/心跳仍停止。

- CoSim新隔离run：`module_14_lm_head_v4/build/selector_full_cosim_r2/hls/`，仅复用已完成综合，
  使用`LMH4_SELECTOR_COSIM_RUN=selector_full_cosim_r2`运行`cosim_selector_existing.tcl`。
  日志`reports/hls_selector_full_cosim_r2_20261021.log`。必须核对官方C/RTL PASS与事务报告，不能只看C参考。
- Vivado仅重置selector/MIG两个未完成IP，保留7个已完成IP；
  使用`experiments/board_v4_20261021/build_resume_r2.tcl`，日志`reports/selector_system_build_r2_20261021.log`，
  新硬件输出`reports/board_v4_20261021/hardware_r2/`。run状态快照及恢复前SHA在`reports/resume_20261021_r2/`。
- 新独立审计脚本`module_14_lm_head_v4/scripts/audit_selector_system.py`：拓扑only已PASS，
  routed模式必须有完整STA/CDC/DRC/bus skew/引脚/bit-XSA产物才可审计，不因BD验证自动PASS。
- 新整链证据收集`scripts/collect_selector_integration.py`须等待正式RTL PASS后执行。
- 新`reports/selector_arena_chinese_20261021/arena_production.bin`及MANIFEST已完成主机文件校验；
  320MiB/9个源区域/13guards/320分块CRC。目标PL DDR加载与新loader尚未执行/实现，不可套用旧固定权重loader。
- 当前新质量认证和板测性能仍未完成；不要修改冻结HLS源码或IP而让活动仿真/实现继续使用旧版。

### r2恢复过程中新增真实发现（不得误报官方CoSim PASS）

- HLS完整CoSim r2实际完成C参考与输入trace生成，但XSim编译失败：生成控制包装中`initial begin : read_token`与`task read_token`同名（VRFC10-2934）。原始HLS日志保持FAIL，不改写成PASS。
- `scripts/repair_selector_cosim_name.py`仅把生成testbench的命名块改为`read_token_output_block`，原文件及前后SHA在`SELECTOR_COSIM_NAME_REPAIR.json`。冻结HLS源/计算RTL/IP未改。
- 修复后的XSim已能运行，第一次重跑与Vivado并行导致16GiB主机分页压力，现已按任务身份停止该XSim，保留`reports/resume_20261021_r2/selector_xsim_memory_pressure_interrupted.log`和资源诊断，改为Vivado完成后顺序重跑。不得将这个中断当作数值失败或PASS。
- 后续执行`scripts/run_selector_repaired_rtl.ps1`，日志`selector_repaired_xsim_r3_20261021.log`；使用既有r2的完整C trace，不再重新生成。顺序检查完整两事务41943040个128-bit内存输出值及全部标量（`check_selector_rtl_traces.py`），再运行原C postcheck，最后`collect_selector_integration.py --repaired`。这是修复生成包装后的独立RTL验证路径，必须与原始HLS包装FAIL区分。
- `SELECTOR_RTL_IP_EQUIVALENCE.json`：96个DUT Verilog中95个与冻结IP逐字节相同；仅顶层增加translate_off内的仿真死锁检测include/空白，去掉显式非综合区段后相同，diff保留。不能谎称96个都字节相同。
- Vivado已完成顶层综合与布局，布线前WNS+0.605ns，仍待最终route/STA/CDC/DRC/bit-XSA。当前唯一重EDA活动为系统实现；无板卡工作。

---

## 以下为20:03暂停记录（已由用户恢复解除，保留中断证据）

## 最新：2026-10-21 20:03 用户安全暂停

用户明确“先安全暂停”。本轮离线HLS CoSim/Vivado系统综合进程树已停止；进程身份与停止后EDA清单见`module_14_lm_head_v4/reports/pause_20261021/`。不自动恢复、不开板卡连接、不恢复旧wb/luyou/心跳。

### 已完成且可复用

- 真正可综合父级`src/lm_head_v4_selector.cpp`串行调度route→lowrank→topK/union→canonical精算；不同于旧测试专用C链。
- 私有M4SC v1/240B/13region描述符，64位PL DDR地址，320MiB窗口；预检容量/别名/溢出，运行中错误门控，不发布失败token。`SELECTOR_INTEGRATION.md`详述合同。
- `reports/hls_selector_csim_r2_20261021.log`：6正确、24预检拒绝、5运行错误，四类真实全preview/候选ID/raw logits/dense token-score-CRC通过；host32项PASS。
- `build/selector_csynth_r2/hls/solution1/`：综合PASS，估计3.650ns、153 BRAM18K/247 DSP/88775 FF/92410 LUT。关键矩阵循环II1，candidate policy实际II2；不宣称所有循环II1或真实200MHz已通过。
- 单AXI父级第一次综合因DATAFLOW多进程读同端口失败，原r1日志保留；当前两个64位地址/128位数据master：plmem与history专口。
- `reports/SELECTOR_PRIVATE_IP_MANIFEST.json`冻结`ip_repo/lm_head_v4_selector/`301文件、源SHA、布局SHA、VLNV user.org:hls:lm_head_v4_selector:4.0。日期Revision溢出只修本地产物并保留原始脚本。
- `experiments/board_v4_20261021/create_bd.tcl`实际创建/验证PASS；BD在`board/build/m14_v4/`，PL DDR-only双master、MIG时钟CDC/校准门控沿用已验收v3.1拓扑；GPIO2私有签名0x4D345301，不能冒充公开ABI/build。
- `standalone/selector_control.c/.h`为平台无关PS控制逻辑：镜像签名/校准/已校验资产ticket、描述符预检、64位寄存器写回核对、限时等待与最终CRC门控。`selector_control_test_20261021.log`25项fake-MMIO PASS；`SELECTOR_CONTROL_REGISTER_AUDIT.json`导出寄存器匹配PASS。尚未生成实际BSP/ELF/加载包。

### 中断位置和恢复要求

1. `hls_selector_full_cosim_r1_20261021.log`只完成真实中文K21529/token20412/score_bits0x41de477c的C参考及重叠拒绝；停于Generating RTL test bench。官方整链RTL未PASS，不存在有效延迟数据。旧run保留，不将C参考PASS当作RTL PASS。
2. 原CoSim使用320MiB AXI模型（20971520个128bit word）；C参考/序列化约需十多分钟，不能仅凭无新输出判断死锁。恢复优先新建隔离run复用冻结RTL，核实输入trace/仿真阶段和真实进度；不能以缩小词表代替全V验证。
3. Vivado `reports/selector_system_build_r1_20261021.log`停在OOC子IP综合；selector与MIG无DCP。SmartConnect/clock converter/GPIO/PS/reset等已完成DCP保留。无顶层综合或P&R、无当前bit/XSA。恢复先读项目run状态，保存中断日志，仅重置未完成run并复用已完成IP；不要无条件重置全部。
4. 冻结IP和源SHA不变时可继续系统构建；若修改HLS源，必须重新Csim/综合、冻结IP并重做依赖构建。首次导出绝对路径失败/单端口综合失败/Revision修补的历史日志均保留。
5. 后续仍需完整RTL数值与周期、系统200MHz STA/CDC/DRC/bit-XSA一致性、PS配套及loader目标读回校验。新算术独立质量未重认证；旧holdout不再用于调参或认证。板测仍需新独占安排。

v4整链ms/token、token/s、TTFT及真实板测均NOT_RUN。v3.1 dense封存基线117.751830ms保持不变。当前暂停，不自动执行上述恢复步骤。

---

## 以下为18:01历史检查点（当前状态由上文覆盖）

## 最新：低秩/路由组件及完整C串接通过

时间：2026-10-21T18:01:12.401301+08:00。主模型作业均已结束；无后台任务、不操作或探测板卡，不恢复旧wb/luyou/心跳。

- 首先读module_14_lm_head_v4/PROGRESS.json及reports/SELECTOR_ARITHMETIC_STAGE_20261021.md/.json。
- 新增router/lowrank独立top，固定参数未拟合；各CSim/HLS及3事务RTL PASS。新HLS均3.650ns估计，不是P&R。
- 四类完整C链对全词表preview、候选ID/全部候选raw logits以及dense token/score/CRC验证通过；只是C函数串接，不是完整RTL或真实DDR系统。
- 新算术全校准集4775 decode：route15/lowrank84/hybrid0漏选、路线顺序变化0。GPU显式算术模型与四类完整NumPy/CSim preview逐位一致；不把模型审计冒充4775笔RTL。
- 路由r1 RTL曾真实失败，同字节bit-store丢位；r2整128位cache-mask修复后官方RTL PASS。原始证据在reports/failure_router_bitstore_20261021，r1禁用于后续集成。
- 低秩内部A扫描达到一beat/拍，16beat/行，理想12.15488ms；含DDR/其余阶段的完整decode仍未测。

## 下一步：完整selector硬件与PL DDR系统

1. 设计真正父级调度/状态与错误传播，将4组件连接为系统；目前selector_chain_csim_unit.cpp只是测试用unity编译单元，不能导出当完整硬件top。
2. 冻结64位PL DDR布局、参数包/BT无损转置SHA、norms512B、排名列表、scratch容量/对齐/别名与不可变合同；A53软件可留PS DDR，计算数据不得回退。
3. 完整selector数值/RTL验证，注意lowrank非有限A可能部分写preview，必须以本次status门控后续Top-K；routed/union头最后发布。
4. 完整PL DDR BD的200MHz实现/CDC/STA、身份/bit/XSA/PS init/ELF/loader配套；独立候选核的历史OOC不能覆盖新增三核。
5. 新算术若做独立泛化认证，另留新测试问题组；旧holdout/r2b均已打开，禁止用于选型/重复认证。新板卡独占安排前不探测、不上板。
6. 真正计时覆盖route+lowrank+Top-K+union+candidate+policy+schedule；v4 token/s/ms/token/TTFT均NOT_RUN。

详见module_14_lm_head_v4/HLS_SELECTOR_ARITHMETIC.md。上游直接供权重仍等待总负责人框架文档。

---

## 以下为16:43历史检查点（由上文覆盖当前状态）

# lm_head v4 离线续办检查点

2026-10-21。当前全部本轮进程已正常结束；旧OOC r1已按自身命令行核实后停止，保留综合DCP。
不自动恢复旧wb/luyou/心跳，不操作或探测板卡。G:2021.1工具已恢复；沙箱直接运行DLL报错，本机运行已成功。

## 已完成与证据

1. v3.1 PL DDR dense基线保持封存，原ZIP/源码不改。v4独立目录`module_14_lm_head_v4/`。
2. P2初轮99.8464%失败保留。更保守route4_K16384 ∪rank128_K16384先冻结，再测新1000问题；14969decode/1中文漏选，99.9933%，拟议点估计门槛PASS，不是无损或发布通过。
3. 候选精算HLS：真实C仿真17数值/13非法/4特殊路径PASS，包含全词表raw logits逐位；独立200MHz内部OOC WNS+0.808ns/WHS+0.010ns。
   使用显式HD.CLK_SRC=BUFGCE_X0Y0参考假设，外部596输入/521输出不设板级I/O延迟，不能覆盖完整BD/MIG/CDC。
4. top-K/并集HLS：C仿真8精确/10非法PASS；Verilog/XSim三事务PASS；HLS估计3.650ns，64BRAM18K/0DSP/6597FF/14706LUT。尚无本核P&R。
5. top-K输入是已经应用global-history penalty的全表preview FP32，不包括低秩矩阵乘；输出递增M4ID候选表，与候选精算格式兼容。FP32 -0/+0按数值相等tie处理。
6. 真实英文top-K事务732898周期，200MHz模型3.66449ms；重复调用和NaN早退分别563274/77630周期。不要混合平均，不能当板测或整个head token/s。
7. host26项测试PASS。顶层状态`module_14_lm_head_v4/PROGRESS.json`；候选阶段审计`reports/OFFLINE_STAGE_RESULT_20261021.*`；top-K阶段审计`reports/TOPK_STAGE_RESULT_20261021.*`。

## 下一步重点

- 实现低秩投影与路由的确定性PL算术，然后验证实际candidate覆盖；当前CPU BLAS召回不能直接继承给新舍入/规约顺序。
- 先评估低秩A扫描的调度，不要直接复用候选头串行共享的约102拍/行规约：151936*102/200MHz约77.49ms，仅这一项就可能吃掉稀疏收益。
  应比较跨行流水、分层并行规约或更低精度预筛的资源/时延/质量代价；只有最终精算必须保持原BF16/FP32顺序。
- 原完整问题组拆分/来源锁不改，已打开的holdout不能再用于选型。r2b已使用MBPP剩余249个未见test问题组，下一轮代码独立测试需新作者公开来源或新的真实预留组，不能仅换seed重复旧问题。
- 完整计时覆盖route+lowrank+topK+union+候选寻址/精算+policy+调度。候选gather HLS约190~191拍/行，高于dot159拍，不能按V/K直接推算吞吐。
- 集成完整PL DDR系统、驱动/容量/地址/别名校验、200MHz STA/CDC与身份配套后，再确认板卡新独占安排并上板验收。当前没有v4 bit/XSA/ELF发布包。
- 上游直接提供权重仍等待总负责人框架，不新增外部stream接口，不改成其他传输对象。

## 工具与已解故障

HLS入口`hls_candidate.tcl`、`hls_topk.tcl`用独立run名，不覆盖旧构建。
候选IP首次导出触发261021xxxx日期版本号溢出，仅在本轮生成run_ippack.tcl中修复Revision并保留原文件/SHA，重打包成功；未改EDA安装或系统时间。
`candidate_ooc.tcl`是缺少时钟来源的历史初跑；有效内部时序来自`candidate_ooc_clocked.tcl`及`build/candidate_ooc_clocked_r2/`。
top-K有效RTL证据在`build/topk_cosim_r1/hls/solution1/sim/report/`，不是仅看C testbench的PASS行，应同时检查官方C/RTL PASS。
所有路径除本文件和根AGENTS外均相对v4模块目录；详细内存/状态/错误范围见`HLS_CANDIDATE.md`及top-K阶段报告。



