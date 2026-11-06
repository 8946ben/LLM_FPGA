# FPGA 权重传输与续办

## 2026-11-06 d64 200MHz离线验收与实验上板包完成（最新）

- r4路由已独立验收：setup +0.019ns/hold +0.009ns，158100可路由net全部完成/0路由错误；73个DDR端口核对；14组bus skew最小+4.381ns。4条CDC-15限定调试核；64条DPREG-7经实际OPMODE网表保守枚举排除P反馈，三种强制错误负控制均被拒绝。原WORKFLOW历史许可行导致收尾AssertionError的记录保留，不改写原失败。INDEPENDENT_ROUTE_REVIEW.json及TERMINAL_COLLECTION_R1.json为入口。
- bit/XSA真实生成并独立核验：reports/d64_bit_xsa_20261106_r1，bit SHA e31fe053531256505a461eff365fa92b72844942f66a9785544c18b97e81e43b，XSA SHA 84091057b578442731cb0761bd381ff17381f024af97817d9103074fde942978；XSA内嵌bit逐字节一致，PS init从此XSA提取。15观察身份退出，无锁。
- 匹配PS最终在experiments/reports/d64_matching_ps_20261106_r6完成：直接HSI无显示生成BSP；r1缺Xvfb/r2 Eclipse Channel closed/r3检查头文件过早/r4缺lwip包含路径/r5固定物理地址memcpy被新版GCC拒绝均原样封存。r6只对诊断/结果发布使用现有volatile目标copy及volatile邮箱，算术/控制/协议核心未变；按SHA复用已编译r5 BSP。实际-Wall -Wextra -Werror编译两个AArch64 ELF、链接无未解析符号、LOAD均在PS软件0..0x0fffffff内，实际BSP驱动与XSA一致、PHY补丁一致。计时33333000counts/s，GEM0xff0e0000。六轮全部已观察身份均退出，当前无本任务EDA/锁。
- 实验包deliverables/20261106_M14_D64_200M_r1/M14_D64_200M_20261106_r1，ZIP 443936547B/SHA 0a7c787ea0996c3dbd4e67fac653c9f4d51b1f2060a65b2041b8265e295b3d16；107个payload文件及MANIFEST/SHA256SUMS，ZIP CRC、全部文件SHA、576块镜像CRC真实通过；含bit/XSA/PS init/ELF/576MiB镜像/冻结参考/源与证据。许可正文不在包内。未新增开发日志HTML。
- 方案为|hidden|×RMS Top64动态通道预览→Top4096并14特殊ID→canonical BF16候选精算，非早期聚类＋低秩。整个本轮无板卡连接/操作、无其他agent/wb/luyou/sudo/自动心跳。旧12场景RTL仍用户停止未完成，不恢复或标通过；无整机decode/TTFT或本轮物理板卡速度。
- 下一步是未来独占板卡验收：初次PLDDR加载CRC/sentinel、12场景全数组及生产raw保留/错误恢复、四类各3+30+1000调用。tools/review_d64_board_results_20261106.py已准备和语法检查，未在物理数据执行；不冒充AXI逐拍/IP硬件周期证明。板卡操作须按用户后续安排，当前仅离线包准备完成。


## 2026-11-06 r4实际已结束：布线时序正裕量，历史日志触发收尾断言（最新）

- 本次只读核验：9个子IP串行完成，主综合完成，route报告setup +0.019ns/hold +0.009ns、158100可布线net全部完成/0路由错误；组峰11.560GiB，约57分40秒结束。父及179个观察创建身份实际不在、组空、锁无。当前没有本任务EDA在执行。
- 原WORKFLOW保留FAILED_NO_AUTOMATIC_RETRY/AssertionError：收尾扫描匹配复制calib_gate日志中11月5日20:07:18的旧许可ERROR，随后本轮真实获取许可并综合成功；实际route PASS marker仅一次。不能将该原失败状态改写PASS，也不因此重跑实现。
- 当前仅证明真实报告正裕量，尚待独立审CDC/DRC警告/DDR reset缺output delay/引脚时钟源绑定，尚无bit/XSA/匹配ELF或本轮板测。STATUS_CHECK_20261106.json记录本次检查；不恢复RTL/监控/其他agent/板卡。


## 2026-11-06 用户再次确认继续200MHz实现，r3内存保护终态，r4显式串行执行中（最高优先）

- 用户明确选择“继续200 MHz系统实现和上板包准备”。旧自动目标仍叫“完成当前方案的仿真”，已依该选择update_goal返回paused，不恢复RTL；不要把旧目标自动active视为重启原12场景授权。200MHz离线实现作为当前任务继续，不改成功范围。
- 真实r3于2026-11-05 23:42:39北京时间触发GROUP_RSS_ABOVE_16GIB（16806928KiB，111.30秒）；许可获取真实成功，但多个Vivado子进程同时占用内存，未完成整体综合/route。44个实际观察身份均不在、组空、锁无独立核验。静态收件50859B/SHA6ec742f5fcbca145fb65c658370b6513ef325479d72ab2e55b56cd123c83d2b9，r3/RESOURCE_FAILURE_COLLECTION.json。不是时序/数值FAIL，不再将r3写执行中。
- 主模型手动准备独立experiments/reports/d64_system_200m_20261106_r4，新工程board/build/m14_d64_200m_r4：保持16GiB组/32GiB余量/21600秒，线程2/jobs1；逐IP launch→wait→检查成功，全部OOC完成后才主综合和route。没有升资源上限/改计算RTL/覆写旧副本；未启动其他EDA/板卡/agent/wb/luyou/sudo/心跳。
- 当前唯一真实父7321/start353578131，阶段组7322，entry源SHA匹配，最新组约5.33GiB、无组外后代。真实串行标记已有axi_cc_ddr BEGIN→END，随后axi_smc BEGIN；前者synth_design成功且0 errors/0 critical warnings，后者综合中。普通comm=vivado还包括轻量包装进程，不能把全部进程数量等同并行综合数。当前只证明已观察前两IP串行顺序，不证明全程资源/综合/route通过。
- 只读观察tools/observe_d64_system_route_r4_20261106.py，实际工作流reports/d64_system_200m_20261106_r4/route/WORKFLOW.json及LATEST_SNAPSHOT/observations；父/源码/组/锁/新日志需现查，不重复启动或改运行副本。停止仅本轮route/STOP_REQUESTED并核当前实际身份/组/锁。
- 终态后先核父和所有观察创建身份不在/组空/锁无，收原始报告；审实际setup/hold、未约束路径、时钟/CDC/DRC/路由/DDR引脚后才手动bit/XSA，再匹配BSP/PS init/ELF与加载包。当前无bit/XSA/匹配ELF及物理板卡结果，旧12RTL仍未完成。主入口r4/RESUME.md；根开发日志未改。

## 2026-11-05 用户已授权许可复制，STHL真实获取综合许可，r3系统实现执行中（当前最高优先）

- 用户最新明确“允许，继续”，覆盖下方仅本机查找的审批边界。许可证副本已按SHA核验复制至STHL /home/zhangben/.cache/d64_license_probe_20261105_r1/candidate.lic，目录700/文件600；只设置本任务进程XILINXD_LICENSE_FILE，不改全局/原许可，不把许可正文放项目/交付物。下方“未上传/等待授权”均历史。
- 初始lmutil有文件但因缺/lib64/ld-lsb-x86-64.so.3无法启动，非许可拒绝；用已有/lib64/ld-linux-x86-64.so.2加载原版2022.2 lmutil后实际诊断return0识别Synthesis。未sudo/安装库/改系统/改二进制。证据r1/STHL_LICENSE_DIAGNOSTIC_WITH_SYSTEM_LOADER.json；不能只凭诊断泛化综合通过。
- r2启动前复制工程后，路径assert把m14_d64_200m_r2中的旧名称前缀误判残留，尚未创建WORKFLOW/启动EDA。父21798/start350755471实际不在，无锁；PREFLIGHT_FAILURE_RECEIPT.json保留。r3仅改检查为旧目录后带斜线的路径边界，补齐与冻结r1逐字节一致的pre-place XDC；未覆盖r2或r1失败工程。
- 当前唯一执行experiments/reports/d64_system_200m_20261105_r3，父26678/start350778299；独立副本board/build/m14_d64_200m_r3，原r1失败工程/73综合源/计算RTL保留。16GiB组/32GiB余量/21600秒，4线程/2jobs，无自动retry/bit/BSP/板卡。工作流EXECUTING_ROUTE是总阶段标签，实际目前处于子IP综合，尚未布局布线通过。
- 本轮新日志已实际出现Common17-349 Got license Synthesis/xczu9eg，PS子系统synth_design成功且0 errors/0 critical warnings，DDR及d64计算核仍推进。最新快照源SHA匹配、父身份存活、子进程全部在受保护组内，约5.29GiB；不是完整综合/200MHz时序/bit/XSA通过。复制工程保留的20:07旧许可错误日志已标COPIED_HISTORICAL_R1，不当成本轮错误。
- 观察入口tools/observe_d64_system_route_r3_20261105.py，只读本轮真实身份/源码/组/锁/新日志；当前终态前不重复launch/copy/reset。若需停止，只向reports/d64_system_200m_20261105_r3/route/STOP_REQUESTED写请求，再核实际身份/组空/锁无。终态独立审setup/hold、约束、时钟、CDC/DRC/路由与I/O后，才能手动生成bit/XSA及匹配BSP/PS init/ELF。完整12RTL仍用户停止未完成，不恢复；本轮未操作板卡/其他agent/wb/luyou/sudo/自动心跳。
- 主入口r3/RESUME.md及reports/d64_board_20261105_r1/RESUME.md/SUMMARY.json。576MiB镜像及离线主机资格保留，尚未形成完整可上板包。根开发日志未改。

## 2026-11-05 本机Vivado2017.4及许可已找到，远端复制审批被拒（当前）

- 用户只要求“在我电脑上找一下，我电脑有vivado2017”。已找到D:/Xilinx/Vivado/2017.4/bin/vivado.bat与D:/Xilinx/License_2037.lic；许可SHA b6524ede15f7896cd4198d2e89c7f782b733083d5c4d36071c5e7e2278a6e45c，D:/install/VIVADO_lic/1/License_2037.lic为相同副本。只保存脱敏路径/元数据，不把许可正文放项目或交付物。
- 本机正确加载settings64.bat环境后，lmutil lmdiag -n -c ... Synthesis实际return0，识别Synthesis v2037.05/hostidANY且无诊断错误。最初直接调用未配环境return-63无输出，之后一次cmd引号失败均非许可失效结论；正确环境结果在reports/d64_system_200m_20261105_r1/LOCAL_LICENSE_DISCOVERY.json。仅本机2017工具识别，尚不能证明STHL2022.2可checkout。
- 拟将原文件副本复制到STHL权限600任务私有目录、仅做2022.2 lmutil诊断的命令被自动审批拒绝，命令未执行、未上传、未改全局配置、未启动综合/板卡。拒绝原因为用户仅授权本机查找，未明确授权将含授权材料的许可外传到STHL。已经在聊天明确解释，须用户明确许可这项远端复制后才能续办，不得换工具/间接传输绕过。
- 200MHz系统实际综合仍保留原Common17-345许可阻塞；旧RTL继续paused/未完成，无本任务后台EDA或心跳。其余IP/BD/离线镜像/主机测试通过范围按下方记录，不扩展为实现/板卡通过。

## 2026-11-05 d64 IP/BD和离线镜像通过，综合因许可证阻塞（当前最高优先）

- 延续用户“停止RTL回归，转200MHz系统实现及上板包准备”；旧仿真目标paused/12场景未完成，禁止恢复旧回归。当前没有本任务远端EDA；无新心跳/其他agent/wb/luyou/sudo/板卡操作。
- 新IP在隔离目录真实导出并独立通过：reports/d64_board_20261105_r1/EXPORT_INDEPENDENT_REVIEW.json。73原综合文件不变；68导出计算Verilog字节相同，顶层精确增加未使用死锁寄存器与translate_off include；4浮点核完整参数/版本与真实仿真核一致。不是新完整RTL PASS。
- 系统BD实际生成并独立通过：reports/d64_system_200m_20261105_r1/BD_INDEPENDENT_REVIEW.json；真实BD SHA d800cb1b622890f10baa460c94bdf0361bf976f2112f514cce816624415af662。双64地址/128数据AXI只映射2GiB PLDDR，校准门控/跨域/引脚来源保持；PS实际配置199.998001MHz，签名0x4D344401。不是路由200MHz已通过。
- 实际综合在STHL Vivado2022.2因Common17-345缺Synthesis/xczu9eg许可失败，未进入route，未生成bit/XSA。父39898/start349485707及55已观察创建身份实际退出、组空、锁无，无任务残留Vivado；失败日志已按原始字节封存于system报告/license_failure_receipt，ROUTE_TERMINAL_REVIEW.json核实。默认许可环境未设，仅发现工具附带核许可；已在聊天请求用户/管理员配置合法综合许可，等待输入，不盲重试/伪造许可。
- 离线OFFLINE_PREPARATION_REVIEW.json通过：576MiB镜像SHA6dc780c58540b21e1cf659126823205894b17f4cd1c3ab06e2489424c53815e9/CRC569536e6、双权重canonical/tiled SHA/CRC、16输入与18实际CSR字段匹配；host_ps_r2的15mock控制及协议CRC/边界/read_only/ACK实际通过。旧host_r1严格编译格式告警保留，未禁Werror。仅主机/资产资格，非BSP/ELF/RTL/板卡。
- ps目录新增d64驱动、独立D64A magic0x41343644/1416/576MiB加载器、默认无socket的upload_d64.py、12持久场景+四类各3+30+1000测试程序源码。PS测试程序尚未用匹配BSP编译；bit/XSA/PS init/BSP/ELF均未生成，不得称可直接上板。READ_ONLY回收模式不证明初次加载通过，物理AXI逐拍计数未提供。下一步许可恢复后独立新attempt系统实现，真实STA/CDC/DRC通过后才bit/XSA及匹配软件；本轮不连接板卡。
- 主续办入口module_14_lm_head_v4/reports/d64_board_20261105_r1/RESUME.md与SUMMARY.json；system入口reports/d64_system_200m_20261105_r1。根开发日志未改。下方“尚未导出/准备上传/当前执行”等均历史。

## 2026-11-05 用户明确停止RTL回归，切换200MHz系统实现与上板包准备（最高优先）

- 用户选择“停止当前回归，转200 MHz系统实现及上板包准备”。已核实际42095/start347854432后只向本轮r2写STOP_REQUESTED，原watcher协作停止；真实原因STOP_REQUESTED，父不在/组空/锁无。首次命令因Windows stdin编码解析失败未执行，已用明确UTF-8字节修正后实际完成，不是重复停止其他进程。
- r2静态18件510889B归档SHA4909d87011c23adf0e32f5713542688ae9b7ccfbbb77c68469a25a4f15695007；107源/TV/全部观察身份核验并封存。仿真目标update_goal实际返回paused，未标完成；整个12场景仍未完整验收，旧单例/有限FIFO/模型/前缀真实通过证据保留，不用板测计划冒充RTL PASS。禁止旧自动goal接续恢复仿真。
- 新用户任务在experiments/reports/d64_board_20261105_r1，PLAN.json：先隔离导出既有合格r3 HLS综合IP，再复用已板测平台的2GiB PL DDR/校准门控/引脚约束，接入d64的m_axi_meta/m_axi_weights两条64地址/128数据AXI，200MHz，part xczu9eg-ffvb1156-2-i，独立签名0x4D344401，控制仍0xA0000000，PLDDR0x400000000。当前只准备新Tcl/约束/源manifest，尚未导出/实现/生成bit。
- STHL2022.2 Vivado/Vitis_HLS/XSCT及原.cache/p64_r3/csynth/hls均存在，当前无ACTIVE.lock，板级旧Tcl/XDC尚未在服务器；将仅上传新目录/副本。无sudo/板卡/其他agent/wb/luyou或心跳。用户授权到系统实现和上板包准备，未授权本轮直接连接板卡。

## 2026-11-05 16:51 r2实际只读核验，首场景预览执行中

- 原父42095/start347854432及内核42480/start347858089实际存活，107源SHA匹配；完整545685504B加载/1522哨兵返回，stage0/1完成，实际AXI完整请求到tick604600。组4925456KiB约4.697GiB，0/12场景返回；不代表数值通过。
- 证据r2/observations/20261105_085146/RUNTIME_SNAPSHOT.json。48h/16GiB/32GiB余量保护不变，无STOP/重启/副本修改/新EDA/恢复定时监控。本轮为已核实等待；终态工具已准备，继续等待同一完整作业，避免冗余准备及密集查询。

## 2026-11-05 15:39 r2专属终态工具准备完成（未收活跃结果）

- tools/collect_d64_state_suite_r2_20261105.py --collect-terminal固定绑定实际父42095/start347854432，并与远端LAUNCH_IDENTITY.json及WORKFLOW双重相等；终态后核全部观察身份/组/锁/107源/完整TV/输入与绑定，按原始字节收件。
- tools/review_d64_state_suite_r2_completed_20261105.py保留原12case全数组/控制/地址/生产raw/A-B-A/错误恢复断言，新增新启动身份与手动EXECUTION_DECISION计划SHA/48h范围核对。16GiB/32GiB余量/300s保持；只运行期核对新冻结172800s。
- 本地导入/远端代码语法与真实启动pair正控制、父PID/启动PID/父start/启动start四种破坏拒绝通过；unpack/self_test AST与已通过原收件器相同，所有数值helper未改。这只是工具准备，不是本轮仿真通过。证据r2/TERMINAL_AUDIT_TOOLS_PRECHECK.json。没有对正在运行作业执行收件或新EDA。
- 最近远端实采仍15:35（新r2加载中、0/12），不把本地准备时间冒充新采样。后续不密集轮询或恢复定时监控，等待同一有界完整作业实际返回后再按全范围验收。

## 2026-11-05 15:35 前缀独立通过，完整12场景优化配置48h有界回归已启动（当前）

- 前缀reports/d64_prefix_options_20261105_r1已实际终态且独立通过：全5120preview raw/key、64dims、metadata/guard/全部未触及字节一致，124740周期/40960权重拍/控制与地址轨迹字节一致；两份108编译文件一致，原107缓存不变且项目追加可逆。25观察身份不在/组空/锁无。计算段marker墙钟581.992375秒对522.512673秒，1.113834x（耗时降低约10.22%），只有单次同前缀样本，不外推完整DUT或FPGA。收件304449B/SHA b45020d41b7c1e2abad8675b4d2800c02384ee06bd9d7097d130c24c9198813b。
- 主模型在真实模型21门槛、同DUT前缀和原首例全数组独立通过后，手动冻结新完整计划reports/experiments/d64_state_suite_20261105_r2；预算用7×首例5.133h≈35.93h，+25%≈44.91h取48h，不依赖前缀加速外推。16GiB组/32GiB系统余量/300秒编译不变；单次完整12场景运行172800秒，不自动加时/重试/后续阶段。原6h失败及所有原证据封存。
- 当前唯一父42095/start347854432，组42422/内核42480/start347858089实际存活；15:35实采展开30.6536秒return0，107缓存原源SHA一致。新cache .cache/d64_state_suite_20261105_r2复制原107文件，明确不含prefix_probe及对应项目行；根仅d64_state_tb/glbl，-debug off --O3；12原fixture/持久DUT/no inter-call reset/全数组与模式要求不减。加载原完整权重中，新本轮0/12返回，绝非数值已通过。
- 观察入口tools/observe_d64_state_suite_r2_20261105.py，资源日志已用16KiB尾读取。按合理间隔核同一实际创建身份，勿自动密集查询或恢复已删除半小时定时监控；无板卡/实现/sudo/其他agent/wb/luyou。暂停只向本轮reports/d64_state_suite_20261105_r2/STOP_REQUESTED请求，再核当前身份/组/锁，不用旧PID。
- r2的收件器/最终验收器还需在独立新文件适配newR/newcache/真实LAUNCH_IDENTITY/48h；禁止直接调用固定r1父6752/6h的collect/review工具误收旧结果。终态后核父/全部观察身份不在、组空、锁无；核107源码/完整TV/12输入/marker身份，再独立审12幅before/after全数组、control/address、生产raw保留、A-B-A/zero/ties/六错误恢复及各调用正常模型周期。目标仍未完成。

## 2026-11-05 14:46 真实DUT两配置有界前缀对照已执行

- 当前唯一执行reports/experiments/d64_prefix_options_20261105_r1，原父32252/start347561461。baseline展开实际31.3869秒返回0，14:46核同父及组32735/内核33106/start347565195存活，正在加载原545685504B完整权重。两配置顺序执行，不并行；16GiB组/32GiB余量/300秒展开/1200秒单前缀保护，不自动整轮重试。
- 原107缓存文件在复制前逐一SHA核验，计算RTL/FP32/内存模型/FIFO/原12场景bench不改；只追加新prefix_probe.sv到隔离state.prj。probe在第五tile最后key地址44832的AW及对应B握手后，于负沿导出全80592字镜像及marker。只允许frame0、meta idle且未done；原12场景在诊断停点前被$finish截断，这不是完整调用/12场景PASS。
- baseline -debug all --O2；optimized -debug off --O3，均-stats；相同根d64_state_tb/glbl，不启用load-only根。前缀5120raw/key/64dims及metadata/guard/未触及区域须独立逐位核验。计算起止marker的文件mtime_ns用于对比计算段墙钟，包含小额文件系统开销，初始化/导出在区间外；周期与地址工作量也必须相等，才可解释加速比。
- 观察入口tools/observe_d64_prefix_options_20261105.py；先读真实WORKFLOW和当前创建身份，不重跑prepare/bootstrap。终态后收静态全数组/地址/控制/资源/标记时间及108实际编译文件（state.prj追加可逆，其余原文件不变）。当前未获得任何前缀数值或加速通过，完整目标仍含原未完成11场景，不能用诊断代替。无板卡/实现/sudo/其他agent/心跳。

## 2026-11-05 14:38 优化编译21项模型门槛独立通过，完整DUT对照未执行

- 新隔离reports/experiments/d64_native_opt_gate_20261105_r2实际工具返回后已独立审计：1正例+20错误拒绝通过，四态AXI完整轨迹SHA及全部字节与原model门槛一致；8份实际编译源相同，91个观察创建身份均不在，最终组/锁空。峰0.842091GiB，原8GiB/32GiB余量/300秒编译/180秒单例保护不变。
- 原r1命令采用文档分隔-O 3，被实际xelab参数解析拒绝，未进入仿真；原失败WORKFLOW/log及停止身份保存。实际帮助明确--O3，新r2仅改写法及隔离路径，使用-debug off --O3和xsim-stats。原7SV/model/计算RTL/阈值均未改。
- 正例wall6.013560秒、原6.019574秒，含启动开销，不认定完整DUT加速。INDEPENDENT_REVIEW.json只证明优化选项下模型21门槛，不能替代M14完整12场景；原套件仍1/12且超时封存。
- 静态收件614402B/SHA2837acdb8c340cfbc4201746c387eec7fb7bc340f93781e077b5b7a69094456a。下一步主模型手动冻结真实DUT有界同一前缀的数值/访存/耗时对照，保留原完整权重及107源码身份；通过后再决定完整12场景运行预算，未启动自动后续阶段。观察入口tools/observe_d64_native_opt_gate_20261105.py仅r2。
- 准备r1时首次自动审批担心旧授权被覆盖而拒绝，命令未执行。随后只在新目录排他创建OPT_GATE_DECISION.json并核原授权SHA不变，安全替代获准；无审批绕过、sudo/板卡/其他agent/心跳。当前本任务无后台EDA。

## 2026-11-05 14:17 本轮因6小时保护终止，首个正常模型调用独立通过

- 原作业14:15:24以PHASE_TIMEOUT终止，elapsed21600.179秒；原父6752/start345222604及全部观察身份不在、最终组7027空、锁无已独立核验。107源/冻结绑定/完整TV SHA一致，静态17件4907436B归档SHA2de36c9bb71dc922b999dd188a9b25662f6d2789b890e9e7e819ea7ee0c6fcbe。未发人工STOP/升上限/自动重试。
- INDEPENDENT_ONE_CASE_REVIEW.json仅首个A0_debug通过：全151936preview raw/key、64dims、4109IDs及精算raw、token/score/CRC、完整case0控制及地址请求计数逐位一致。正常响应IP3866131周期=19.330655ms@200MHz，不是物理FPGA/MIG测速。before到after文件末次写间隔18478.466秒约5.133h，含控制设置和after导出，不是精确DUT墙钟。
- 33321资源记录组峰4.873924GiB；实际160251条DSP告警保留，此单例输出逐位一致，不泛化其余输入。第二场景B0未完成，frame1控制/地址尾被保护截断，原字节保留；address_summary.csv为0B，不伪写完整汇总。整体1/12，A-B-A/生产/zero/errors恢复仍待完成。
- 本轮分类为时间预算不足、验证未完成；原WORKFLOW失败原文保留，不改成数值PASS或数值FAIL。下一步主模型手动冻结隔离有界编译选项对照及短前缀/模型门槛；先测收益和精度，再决定完整12场景预算，不照原配置自动长跑。当前无本任务后台EDA，无板卡/实现/sudo/其他agent/wb/luyou；半小时监控继续删除。

## 2026-11-05 12:17 首个完整预览阶段返回，候选筛选执行中

- 原父6752/start345222604及内核7084/start345226343实际存活，107源SHA匹配；组4943272KiB约4.714GiB，当前运行14550.44秒。首帧stage0/1/2完成，stage2为1589914周期/1220608权重读拍/75968元数据写拍；stage3筛选中，仍0/12场景返回，不能判全数组/模式通过。
- 预览周期在正常响应模型中折合7.94957ms@200MHz，只是该模型阶段周期，不是物理FPGA测速，也不是本轮整体完成率。真实阶段结束墙钟时刻未逐行记录，不伪报精确阶段墙钟耗时。
- 证据d64_state_suite_20261105_r1/observations/20261105_041754/RUNTIME_SNAPSHOT.json。16GiB/32GiB余量/21600秒保护不变；未STOP/重启/改副本/新EDA/板卡/恢复定时监控。终态后才静态收件及独立全数组/control/address审计。

## 2026-11-05 08:42 当前12场景只读核验与续办摘要范围修正

- 原父6752/start345222604及内核7084/start345226343实际存活；组4942828KiB约4.714GiB，0/12场景返回、阶段0/1完成、107源SHA匹配。仅已核实等待，无完整模式/数值通过；未STOP/重启/改运行副本/板卡。16GiB/32GiB余量/6h保护不变。
- SUMMARY残留的旧强压力组内存、144源码、五阶段等指标已归档到historical_strong_call_last_live_observation，当前字段绑定本轮真实快照。原摘要另存SUMMARY_BEFORE_CURRENT_SCOPE_REPAIR_20261105_0042.json；不是改写历史证据。
- tools/review_d64_state_suite_completed_20261105.py已完成真实Python导入检查，FINAL_AUDITOR_READINESS.json只表示验收器准备，不代表实际12场景通过；终态收件及全数组/control/address/模式审计仍待实际返回。半小时监控已删除，未恢复排期；本轮为目标接续的单次必要核验。

## 2026-11-05 用户确认部署完成后停掉半小时自动监控（最新）

- 用户回应监控选项：“你的仿真部署完成了吗，完成了就可以停掉”。已告知STHL部署成功并已启动；按该监控上下文删除新建半小时监控t04-30，automation_update返回deleted，automation.toml已核不存在。应用复用此ID的新条目绑定的是12场景任务，旧强压力任务未恢复。
- 未向远端写STOP、未停止仿真或修改运行副本；d64_state_suite_20261105_r1/父6752/start345222604继续保留，服务器内置16GiB/32GiB余量/6h保护仍由远端执行。当前没有半小时自动心跳。用户没有明确暂停整个仿真目标，此处只停止定时监控；若进一步要求暂停本会话/目标，按实际范围处理，不擅自停止远端。
- 新监控页面doc/design/D64StateSuiteMonitor.html已生成、JS/JSON检查通过且实际Edge渲染截图检查通过；原T04SimulationMonitor.html保留已通过强压力结果并链接新页。最近真实采样仍08:22:48（0/12报告返回、阶段0/1完成、107源SHA匹配、约4.71GiB），不得冒充之后当前状态。页面停用自动采集后只展示已有数据，网页刷新不会连接服务器。最终12场景全数组/控制/地址/模式独立验收仍待完成。

## 2026-11-05 08:18 完整加载独立验收通过，12场景持续DUT回归执行中（当前）

- d64_state_init_20261105_r2已实际返回并独立验收：原TV SHA c877e6e9c370fba405e215c6e1281ea5d10c74a670aefd8ba2a68424befa74e1；545685504B/34105344字/1522哨兵通过；starts/dones=0、control/address请求均0、profile与case_metrics仅表头。99.486308秒/采样组峰4.690151GiB/154条资源记录，实际5个创建身份不在。仅完整初始化资格，不是M14运行资格。r1真实SV加载成功但采集漏import shutil导致流程FAILED，原日志/缓存/失败状态均保留；r2仅补导入，未改SV/数据/断言/阈值。
- 当前唯一实际任务：experiments/reports/d64_state_suite_20261105_r1；入口run_suite.py，复用cache .cache/d64_state_compile_20261105_r2，快照d64_state_suite_20261105_r1的根仅d64_state_tb/glbl（不包含load-only根）。未改计算RTL/FP32/FIFO，107份源码实际SHA匹配；注册式正常内存响应不是MIG/物理FPGA。
- 08:18:05北京时间真实核父6752/start345222604及组7027存活，内核7084/start345226343；阶段EXECUTING_SUITE，完整加载和1522哨兵已结束，测试台报告0/12场景返回，尚无数值/模式通过结论。16GiB组/32GiB系统余量/300s编译/21600s运行保护，6h上限不自动升或重试。运行器保留原已验证控制逻辑；日志分类改为流式保留所有错误/判断相关行，已对22份真实模型门槛日志做保留核对；SHA也流式，避免大告警日志装入内存。原始日志全部保存。
- 观察入口tools/observe_d64_state_suite_20261105.py（只读STHL zhangben@124.16.71.7:7626）。先读真实WORKFLOW/ACTIVE.lock/suite/tool.log/resources.jsonl/case_metrics.csv及107源SHA；观察超时或网络失败不是终态。暂停只向本轮reports/d64_state_suite_20261105_r1/STOP_REQUESTED写请求，再独立核当前父创建身份/组空/锁无，不凭旧PID。不得并行第二个EDA/板卡/实现/其他agent/wb/luyou/sudo。
- 真实返回后独立审12幅before/after全工作区+guard、control trace/有效位/start-done、地址请求界限、生产raw不写/保持、错误副作用/恢复、A-B-A逐位和正常响应周期；仅bench显示12次返回不等于工程通过。原强压力单调用与模型21项资格保留。整体目标未完成；原t04-30已删除，不恢复旧任务监控。下方“无后台/未编译/未加载”均历史。

## 2026-11-05 正常响应模型21门槛已独立通过，完整状态回归尚未启动（当前）

- 已在原完整单调用/有限FIFO真实PASS后，主模型手动冻结MANUAL_GATE_AUTHORIZATION.json（绑定真实full review/workflow/execution plan SHA），执行唯一d64_native_memory_20261103_r1的21项有界模型门槛。9项实际提取运行器watcher控制先通过，RSS/余量阈值使用注入采样而非实际分配8GiB；原runner/source/计划SHA未改。
- 工具22阶段（展开+21例）返回，03:50独立INDEPENDENT_REVIEW_20261105.json通过：正例四态AXI重放1038AR/131108R/11AW/152W/10B、2次reset取消、2次未写X读、118036连续R握手；20类错误按预期被拒绝。跨512MiB/ID/LAST/RESP/WSTRB/边界检查保留。模型门槛采样组峰0.904728GiB，不代表完整DUT内存/性能资格。
- 首次审计因把退出前资源末行误当终态而拒绝，未改真实日志或放宽数值。已额外实际核全部89个观察PID及创建身份均退出，锁无；保留INDEPENDENT_REVIEW_INITIAL_REJECTION_20261105.json与ALL_OBSERVED_PROCESSES_AFTER_20261105.json。静态收件SHA c62da9ce280f56ba6cbb84bb2782ea4de1b2fd5569a2468eaa0af1582a0a6621。
- 当前本任务无后台执行；原t04-30已删除，不恢复旧心跳。下一步复核experiments/d64_state_tb_20261104_r1/{d64_state_tb.sv,state_request_guard.sv,state_schedule.svh,state_weight_sentinels.svh}及12场景fixture r2与payload/request审计器，冻结真正编译源码和有界运行计划。bench仍PREPARED_NOT_COMPILED，须加入额外request guard与被动stage observer并保护完整权重加载/资源；不得把已通过模型门槛冒充M14 A/B/A、模式/错误或正常周期通过。
- 整体“完成当前方案的仿真”仍未完成；原单次完整强压力数值/FIFO通过保留。无需再跑原31小时调用，不自动无界启动12例，不启动板卡/实现/其他agent/wb/luyou/sudo。证据module_14_lm_head_v4/reports/d64_native_memory_20261103_r1/{WATCHER_CONTROL_PRECHECK_20261105.json,INDEPENDENT_REVIEW_20261105.json,RESULT_20261105.md}。

<!-- T04_MONITOR_CURRENT_BEGIN -->
## 原完整RTL已返回并独立验收单调用（当前）

- 原作业于2026-11-05 03:22:05北京时间真实返回；03:37核原父7002/start332138782不在、最终组4361空/锁无，静态收件再次核原xsim组7438及4361均空。144实际编译源/148冻结/121复用源SHA无差异。无STOP/重启/改运行副本/新EDA/板卡。
- 03:39独立INDEPENDENT_REVIEW.json通过：全151936预览raw/keys、64dims、4109候选ID及canonical BF16精算raw、token20412/score/CRC逐位一致；5有限FIFO容量128/32/32/2/32、占用边界/出入平衡/结束清空/阻塞及原AXI范围通过。160251条DSP告警保留/计数/散列，本次已用输出无位差；不泛化所有输入无害。
- 真实xsim113212.946965秒约31.448小时；实际组峰50.218628GiB，全部98634条xsim资源记录满足原64GiB/32GiB余量/48h保护。总83821539拍=419.107695ms为强随机延迟仿真，不是物理FPGA decode性能，也不证明16GiB可运行。官方cosim_design格式器NOT_RUN，历史失败保留。
- 证据module_14_lm_head_v4/reports/memory_repaired_full_20261103_r1/{INDEPENDENT_REVIEW.json,NUMERIC_REVIEW.json,RESOURCE_REVIEW.json,COLLECTION_MANIFEST.json,PROCESS_AFTER.json}；收件archive SHA29b1e00eec17de2a53e9b8429c75d69e1834e42ef9721788d49d6779338e3dcf。最终HTML doc/design/T04SimulationMonitor.html，47点/17正式实采；t04-30已通过automation_update删除并核automation.toml不存在，不再采样原终态作业。
- 整体目标尚未完成：完整RTL A/B/A、生产/debug/zero-ties/错误恢复、正常响应模型及周期仍须完成。下一步主模型先读d64_native_memory_20261103_r1的GATE_PREPARATION_PLAN/EXECUTION_PREPARATION_PLAN与run_gate.py，复核watcher/STOP/资源端到端前置并手动决定有界21门槛资格；不自动跳过门槛运行12场景，不启动板卡/实现/其他agent/wb/luyou/sudo。此处单调用通过不能替代剩余要求。下方所有执行中/未返回均为历史。
<!-- T04_MONITOR_CURRENT_END -->

## 2026-11-04 20:17 半小时实采，候选精算继续（当前）

- 离线完整验收日志读取已改为流式：全部错误/哨兵/范围/FIFO标记严格计数，所有DSP告警按序计数/散列并最多保留8种示例，日志本体SHA保留。实际旧前5块日志与旧解析相同；10万告警4,089,721B/末尾错误控制通过，tracemalloc峰2,109,970B；原数值数组断言文本相同、实际绑定代码编译通过。证据AUDITOR_STREAMING_LOG_PRECHECK.json；仅验收器控制，不是RTL/DSP/FIFO通过。运行副本未改。下一次既定采样将附带日志大小，当前大小仍未知。

- 原父/组创建身份核实时仍存活，kernel7537/start332143178 CPU8773569ticks；组37.967793GiB，系统可用209.173882GiB，1847.92秒区间CPU100.396%（单核100%），xsim约24.372小时。日志时间从319.9311725推进至326.5346775ms；stage0/1/2/3完成，stage4未观察完成，7TV仍全0B。DSP告警保留待最终数值审计；144实际源/148冻结/121复用源未变。
- 同一原作业及64GiB/48h保护保留，无STOP/重启/改源/新EDA/板卡。HTML已刷新34点/4正式实采，最近间隔30.80分钟。证据reports/memory_runtime_repair_20261103_r1/STATUS_CHECK_20261104_2017.json和reports/memory_repaired_full_20261103_r1/observations/20261104_121711/RUNTIME_SNAPSHOT.json；本轮为真实核验等待，工程目标仍未完成。

## 2026-11-04 19:46 原完整RTL阶段3完成，候选精算执行中（当前）

- 按半小时节奏实际采样，同一原父/组创建身份核实存活，kernel7537/start332143178 CPU8588770ticks；组37.329704GiB、系统可用209.840706GiB、最近1888.57秒CPU均值100.346%（单核100%），xsim约23.858小时。未STOP/重启/改运行副本/新EDA/板卡；原64GiB/48h保护保留。
- stage0/1/2/3已观察完成，stage3候选排序3224705拍、37984元数据读拍、1029写拍。日志真实进入候选精算reduce_rows/reduce_partials，DSP48E1 OPMODE含X告警已保留；影响尚待全量逐位审计，不判无害/数值失败。完整仍0/1、7TV全0B，有限FIFO及模式/ABA仍未通过。
- 告警刷屏使有界日志尾不再含HLS进度行；本地监控已补解析真实诊断Time:319931172500ps→319.9311725ms，并在HTML显式展示DSP告警。实际新/旧快照时间319.9311725/300.005638及页面JS/JSON核验通过；未改正在运行的RTL/日志/模型。
- HTML已有33点/3正式实采，最新两次实采相隔31.48分钟；此前约179分钟空档仍保留。t04-30继续每30分钟记录，无重复采样或新任务。证据reports/memory_runtime_repair_20261103_r1/STATUS_CHECK_20261104_1946.json及reports/memory_repaired_full_20261103_r1/observations/20261104_114623/RUNTIME_SNAPSHOT.json。本轮为真实核验等待且新增阶段证据，工程目标尚未完成。

## 2026-11-04 19:14 半小时监控续办核验，完整预览stage2已完成（当前）

- 本轮自动接续只完成离线收件依赖核验：NumPy2.3.5/数值合同可导入、16份冻结入口文件SHA/144份本地可用源码（按已通过前5块清单）/启动归档与runner绑定一致。证据RESULT_RECEIPT_READINESS_20261104.json；实际完整COMPILED_SOURCES.json仍待终态收件，不拿历史清单替代本轮审计。明确0973a03f…为entry.tar.gz归档SHA，runner本身SHA95c597db…；无额外远端轮询或新EDA，最近实采仍19:14，按半小时节奏等待。

- 同一原父/所属组创建身份核验存活，stage0/1/2已观察完成：stage2完整预览60009568拍、1220608权重读拍、75968元数据写拍。7个实际返回TV仍全部0B，完整0/1；不能当作全数组数值或FIFO通过。144实际编译源与前5块相同，148冻结/121复用源无差异。
- 19:14:54北京时间实际采样组36.953213GiB，服务器可用210.223202GiB，日志已打印300.005638ms；CPU100.318%为与上次相隔约179分钟的均值（单核100%），不是瞬时利用率。本轮真实核验等待原作业，不STOP/重启/改源/新EDA/板卡。原64GiB/48h保护保留。
- t04-30已view核实仍ACTIVE，每30分钟安排保留；本地真实采集只有16:16和19:14两次，中间约179分钟未形成定时记录，原因尚未证明。HTML保留空档并注明缺采，绝不回填假快照。任务调度ACTIVE不等于每次已实际执行。
- 证据：reports/memory_runtime_repair_20261103_r1/STATUS_CHECK_20261104_1914.json与reports/memory_repaired_full_20261103_r1/observations/20261104_111455/RUNTIME_SNAPSHOT.json。doc/design/T04SimulationMonitor.html已刷新32点/2正式实采。前一目标轮为监控与HTML建设进展；本轮为真实身份确认且新增阶段证据的验证等待，工程目标仍未完成。

## 2026-11-04 用户授权每30分钟记录进展与资源（当前监控安排）

- 用户要求每半小时记录一次原完整仿真进展、资源并绘制HTML。已创建并view核实当前聊天心跳 t04-30，ACTIVE，每30分钟；此前5-t04已删除，不重建。下方“无下一次自动核验/暂停不主动核验”是历史，本条授权覆盖监控部分。用户已恢复目标active，但本阶段仍等待原唯一完整作业，不额外密集轮询、不启动新EDA。
- 采集入口：在D:/program/LLM_FPGA执行 C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe tools/t04_monitor.py --sample。仅只读STHL zhangben@124.16.71.7:7626的memory_repaired_full_20261103_r1，绑定父7002/start332138782。原64GiB/48h保护保留；不STOP/重启/改运行副本/板卡/实现/其他agent/wb/luyou。
- HTML：doc/design/T04SimulationMonitor.html；原始汇总和每次采集事件：module_14_lm_head_v4/reports/t04_half_hour_monitor_20261104/{DATA.json,samples/}。首次16:16:04北京时间实采，组33.393791GiB，CPU区间均值100.296%（单核100%，真实系统100Hz/64逻辑CPU），日志下界250.005633ms，stage0/1完成、完整0/1、7TV0B，身份/源SHA匹配。31个历史及实采点中1个为新监控实采；历史不规则点明确分色，不能当作已完成的半小时记录。
- 页面4图展示组内存/CPU/日志仿真时间/服务器可用内存，含阶段/原始证据链接及采集失败；无网络依赖。Edge独立profile实际渲染截图PREVIEW.png已检查，Python数据及链接检查、页面JS语法检查通过。根开发日志未改。
- 后续正常运行只记录HTML，重大变化才通知；采集失败保存错误并保留旧数据，不当作作业终态、不重启，连续3次失败协调。实际终态必须核原父不在/所属组空/锁无，保存最终图后通过automation_update删除t04-30并核实。工具返回与独立全数组/有限FIFO验收分开，未审计不得写数值通过；工程目标仍未完成。

## 2026-11-04 16:05 用户询问进度的单次核验，完整RTL仍运行（当前）

- 16:05:21北京时间只读核原父/所属组身份匹配，kernel7537/start332143178 CPU7262584ticks，组33.167351GiB；stage0/1完成、7TV仍全0B、完整0/1。日志最后已见250.005633ms（14:06时200.005628ms），这只是仿真时钟推进，不是总体完成率/数值或FIFO通过。真实xsim阶段已约20小时10分。144实际源同已通过前5块，原148冻结/121复用源SHA无差异。
- 保持原作业及64GiB/48h保护，未STOP/重启/改源/新EDA/板卡；本次仅进度查询，不恢复自动目标或排期。无下一次自动核验。
- 证据reports/memory_runtime_repair_20261103_r1/STATUS_CHECK_20261104_1605.json及reports/memory_repaired_full_20261103_r1/observations/20261104_080522/RUNTIME_SNAPSHOT.json。完整结果待真实返回后按原全数组/有限FIFO流程独立审计。

## 2026-11-04 14:06 第二次五小时后单次核验已结束，完整RTL仍运行（当前）

- 用户授权的14:05后一次核验已于14:06:02北京时间执行。原父/所属组创建身份匹配，kernel7537/start332143178 CPU6546650ticks，组30.645962GiB，仍stage0/1完成、7TV全0B、完整0/1；日志最后已见200.005628ms。144实际源同已通过前5块，原148冻结/121复用源无差异。不将时钟/CPU/RSS或HLS百分比当数值通过/完成率，完整数值/FIFO仍无结论。
- 新一次性安排5-t04已通过automation_update删除，工具返回deleted且原automation.toml已核无；未再次排期。本会话自动目标仍暂停，原远端作业和64GiB/48h保护保留，未发STOP/重启/改源/新EDA/板卡。
- 证据reports/memory_runtime_repair_20261103_r1/SCHEDULED_CHECK_20261104_1406.json及reports/memory_repaired_full_20261103_r1/observations/20261104_060603/RUNTIME_SNAPSHOT.json。当前没有下一次自动核验；下方14:05 ACTIVE/等待均为历史。

## 2026-11-04 09:11 用户临时授权提前核验一次，完整RTL仍运行（当前）

- 用户明确要求“你当前检查一次”，本次作为14:05前不核验规则的单次例外，已于09:11:34北京时间只读核验。原父/所属组创建身份匹配，kernel7537/start332143178 CPU4779820ticks，组24.436344GiB；stage0/1完成、7TV全0B、完整0/1。144实际编译源同已通过前5块，原148冻结/121复用源SHA无差异；无完整数值/FIFO通过结论。
- 原作业及64GiB/48h保护保持，未发STOP/重启/改源/新EDA/板卡。本次仅一次检查，不恢复自动目标推进。原今日14:05一次安排5-t04继续保留，已本地核实ACTIVE/COUNT=1；此前仍不再主动核验，除非用户另行明确要求。
- 证据reports/memory_runtime_repair_20261103_r1/IMMEDIATE_CHECK_20261104_0911.json及reports/memory_repaired_full_20261103_r1/observations/20261104_011135/RUNTIME_SNAPSHOT.json。

## 2026-11-04 用户再次要求5小时后核验，14:05前不核验（当前优先）

- 用户最新要求“五个小时后再核验一次”。已通过automation_update创建并view核实新的单次安排5-t04，ACTIVE，今日14:05北京时间（UTC2026-11-04 06:05），COUNT=1。旧同名ID的06:35安排已完成删除；此次是用户新授权的下一次，不是每5小时循环。
- 14:05前不连接服务器或核验仿真，不启动新EDA/板卡/实现/其他agent/wb/luyou或额外开发；原远端memory_repaired_full_20261103_r1及64GiB/48h保护保留，未发STOP，本会话自动目标保持暂停。定时单次核验由用户授权，到时先读最新安排再核真实身份/组/锁/日志/7TV/源SHA；执行后删除该安排并核实。
- 记录reports/memory_runtime_repair_20261103_r1/USER_WAIT_UNTIL_20261104_1405.json。本次未查询远端，最后真实快照仍为06:36；不得冒充当前状态。下方“没有下一次自动核验”及06:35等待规则均为历史。

## 2026-11-04 06:36 五小时后一次核验已执行，完整RTL仍运行（当前）

- 用户授权的06:35后一次核验已于06:36:18北京时间执行。原父与所属组创建身份匹配，kernel7537/start332143178 CPU3848140ticks，组21.106041GiB，仍stage0/1完成、7TV全0B、完整0/1。日志最后已见100.005618ms；不把时钟/CPU/RSS当数值通过或物理decode性能。144实际源同已通过前5块，原148冻结/121复用源SHA全无差异。
- 一次性安排5-t04已按心跳清理规则通过automation_update删除（不是再次排期）；工具返回deleted，原automation.toml已核无。原远端作业及64GiB/48h保护保持，未发STOP/重启/改源/新EDA/板卡操作；本会话自动目标仍暂停，没有下一次自动核验。
- 证据reports/memory_runtime_repair_20261103_r1/SCHEDULED_CHECK_20261104_0636.json及reports/memory_repaired_full_20261103_r1/observations/20261103_223619/RUNTIME_SNAPSHOT.json。完整数值/FIFO及后续模型/状态/性能门槛仍未完成。下方“等待06:35/5-t04 ACTIVE”均为历史。

## 2026-11-04 用户要求等待5小时，06:35前不核验（当前优先）

- 为执行用户明确的五小时等待，本会话自动目标推进暂时暂停，避免自动goal接续在约定时间前反复唤醒。暂停仅指本会话工作，不向远端仿真发送STOP。已授权的06:35一次核验安排5-t04保持ACTIVE；该定时核验按用户原要求到时执行并报告，不提前、不中途重启或扩展为新EDA。
- 用户最新明确要求“请等待5个小时再核验”。北京时间2026-11-04 06:35（UTC2026-11-03 22:35）前，不再连接服务器或核验仿真，也不启动新EDA/板卡/实现/其他agent/wb/luyou及额外开发；自动goal接续不能提前复查，除非用户明确改期。保留原memory_repaired_full_20261103_r1运行，未发STOP，不改64GiB/48h保护。
- 已通过automation_update创建并view核实一次安排5-t04，ACTIVE，06:35、COUNT=1，目标为本聊天；执行一次后暂停并核实，不能改为每5小时循环。此一次安排由用户最新请求授权，覆盖下方“无自动心跳”的旧默认，仅限此次延后核验。
- 记录reports/memory_runtime_repair_20261103_r1/USER_WAIT_UNTIL_20261104.json。等待不代表目标完成或受阻；最后实测仍为01:33原进程身份匹配/7TV0B，截止后必须重新核实，不能将旧快照冒充当前。

## 2026-11-04 用户恢复目标，同一完整RTL仍执行（最新）

- 11月04日01:31:37北京时间真实核原父/所属组身份匹配；kernel7537/start332143178 CPU2019946ticks，组14.640114GiB；stage0/1完成，7返回TV仍0B、完整0/1。144实际编译源同已通过前5块，原148冻结/121复用源未变。快照module_14_lm_head_v4/reports/memory_repaired_full_20261103_r1/observations/20261103_173138/RUNTIME_SNAPSHOT.json。当前为已验证等待，未获得完整数值/FIFO或decode资格。
- 当前仍唯一memory_repaired_full_20261103_r1；原64GiB/48h/32GiB余量保护，未重启或改源。返回后按原审计流程，不凭存活/RSS写通过。
- 新独立d64_state_fixtures_20261104_r2共12场景：完整A(debug)→B(debug)→A(debug)、单独A(production)、zero/ties、6类错误及恢复。r1保留；补齐B完整raw覆盖。输入/control、参考及545685504B权重SHA复核通过，仅PREPARED_NOT_SIMULATED。
- d64_native_memory_20261103_r1已形成正常响应模型草稿及native_gate_tb.sv、四态逐拍主机回放器、21项门槛规划。模型SHA48153808aa8c001a9174fa45d161e9a03867df0b6ba6d9f47b758cde3973db38；可逆静态/计划计数检查通过。未编译/运行/资格化；不并行EDA、不替代强压力完整结果。实际新门槛/多调用仍需完整独立通过后主模型手动决定。
- 新模型run_gate.py/EXECUTION_PREPARATION_PLAN.json仅准备；9源绑定、完整独立PASS及真实父/组/锁空前置。8GiB/32GiB余量/300s展开/180s单例保护。4个隔离真实Python所属组清理控制通过，测试进程全空；仅清理资格，watcher/STOP/资源端到端与模型/SV/M14均未资格化。无并行EDA，未生成启动确认文件。
- 正常响应模型主机验收器的合成控制通过：1038AR/131108R/11AW/152W/10B期望轨迹及11种位/ID/LAST/RESP/WSTRB/越界/X转0/RESET/计数破坏均被正确处理。仅验收器控制，不是实际SV/AXI/M14资格，见AUDITOR_SYNTHETIC_PRECHECK.json。
- 新d64_state_tb_20261104_r1：12场景持久DUT测试台草稿、一次完整权重加载/1522哨兵、逐次全工作区前后镜像/输入及末尾保护、寄存器读回/有效位/真实start-done/IP及调用周期、生产raw写禁止和早期错误副作用检查。110端口/12配置/1522字节常量及无中途复位结构独立核对通过；仅PREPARED_NOT_COMPILED，非SV/模型/完整模式/性能资格。无上载/新EDA；完整强压力和新模型门槛先后通过后才决定独立有界执行。
- 连续调用载荷/寄存器主机验收器准备：review_d64_state_payload_20261104.py区分调试全数组/生产无新raw且原raw保持/错误副作用，保留metadata错误读取无固定拍数约束；12个参考构造场景及22种破坏控制通过。只验收器控制，不是新RTL/模型/状态/性能资格；实际AXI地址范围仍须另审。见d64_state_tb_20261104_r1/HOST_AUDITOR_SYNTHETIC_PRECHECK.json。
- 连续调用AXI范围监视器准备：d64_state_tb_20261104_r1/state_request_guard.sv被动记录每帧MR/MW/WR及地址/len，检查输入/工作区/权重/4KiB/溢出/错误访问；17端口结构核对及主机回放13种合成破坏控制通过。REQUEST_GUARD_SUPPLEMENT.json要求未来编译加入此新文件，原bench SHA未变。仅准备，未编译/运行监视器；实际AXI范围/拍数和全量载荷仍须工具返回后绑定审计。
- 主入口reports/memory_runtime_repair_20261103_r1/RESUME.md、SUMMARY.json及SIMULATION_ACCEPTANCE_MATRIX.json。无板卡/实现/sudo/其他agent/wb/luyou/心跳，根开发日志未改。下方最新/NOT_IMPLEMENTED均历史。

## 2026-11-03 前5块独立验收通过，完整RTL一次新调用实际执行中（最新）

- 12:25:14UTC（北京时间20:25:14）最新快照确认同一完整父/成员创建身份匹配，内核PID7537/start_ticks332143178实际CPU181732ticks，组约8.154GiB；stage0/1已结束，7返回TV仍全部0B，完整0/1。144实际编译源与通过前5块完全相同，原148冻结/121复用源未变。观测reports/memory_repaired_full_20261103_r1/observations/20261103_122515。此处为验证等待，不把CPU存活/内存增长当数值进展或通过。
- 本轮离线准备experiments/reports/d64_state_fixtures_20261103_r1：11场景A(debug)→B(production)→A(debug)、全零平局、容量/flag/hidden NaN/rms NaN/负rms/选中预览权重NaN及A恢复。3组既有完整Csim参考按全部数组重组SHA相同，545685504B两权重流式再核SHA，输入变异/ABA同字节、33原RTL寄存器地址及64bit参数/读回/valid flags独立预检通过。仅PREPARED_NOT_SIMULATED；不得写作新RTL/质量/性能通过。新响应模型尚未实现/资格化，不并行EDA，不替代正在执行的强压力完整门槛。
- 后续准备入口tools/prepare_d64_state_fixtures_20261103.py、prepare_d64_state_control_20261103.py及review_d64_state_fixtures_20261103.py。control首次硬编码期望38寄存器拒绝，实际33；已改为显式字段集合相等并通过，CONTROL_PREP_FAILURE.json保留。所有准备在独立目录，无对正在运行副本的写入。完整结果独立通过后主模型再决定新模型门槛与多调用，不自动串接。
- 本轮只改本地验收器：被动stage_profile中status无有效标志且实际前两行X，保留null而非转0；正式返回status==[0]及所有数组逐位比较未变。实际计时表正控制/未知cycle负控制与实际FIFO单元记录、越界/非法block/X深度负控制均通过，见memory_runtime_repair_20261103_r1/AUDITOR_*PRECHECK。运行副本/入口/64GiB保护未改。SIMULATION_ACCEPTANCE_MATRIX.json显式保留完整RTL A/B/A、模式、正常响应周期的未完成范围，历史Csim/selector不能冒充本轮全模块资格。
- 当前目标“完成当前方案的仿真”持续有效。前5块真实工具已返回，11:48:41UTC独立核父身份/组/锁空；INDEPENDENT_REVIEW实际40960权重拍/5120raw/5120key/64dims/1522哨兵逐位通过，144实际编译源/116未改复用源全核、变更可逆。3029.41秒、组峰8.578613GiB；仅前5块10.5878525ms，非完整RTL/正常decode。
- 新唯一完整任务experiments/reports/memory_repaired_full_20261103_r1，真实run_startup.py/WORKFLOW.json/ACTIVE.lock及elaborate/xsim/c_postcheck日志与资源JSONL。entry SHA0973a03f1a49da19b5b6cd81726939aa2313d035b8544a1502d3473b66a96729，绑定全部已审门槛。启动状态须用tools/observe_memory_repaired_20261103.py memory_repaired_full_20261103_r1核实时身份/日志，不凭引导PID或重复prepare/bootstrap。
- 原old_chinese/d64/T4096/B1024/双W/debug1、计算RTL/FP32/有限FIFO/随机延迟类不变；仅已审模型/VIP/MASTER守卫/2000拍轮询/RLE。64GiB组/系统余量32GiB/初始96GiB/展开300秒/运行48h保护，不自动重试/升上限/后续阶段。原df_process_monitor逐拍stall队列仍保留，完整内存理论上界未证明，不承诺16GiB完整资格。
- 工具返回后独立核父创建身份不在/组空/锁无、取回静态证据/核SHA，用tools/review_memory_repaired_full_20261103.py审真实7返回TV、原C后检查、全151936raw/key及4109候选/输出与5有限FIFO；未返回不能提前记通过。cosim_design格式NOT_RUN，原全部Fail保留；ABA/模式/正常性能后置，不把压力周期称物理FPGA decode。
- 主入口reports/memory_runtime_repair_20261103_r1/RESUME.md。无板卡/实现/sudo/其他agent/wb/luyou/自动心跳，根开发日志未改。暂停只向本轮写STOP_REQUESTED再核实际所属组/锁，不用历史PID。下方前5块执行中及无执行均历史。

## 2026-11-03 运行期内存门槛显著改善，真实DUT前5块验证执行中（最新）

- 当前目标“完成当前方案的仿真”持续有效。主入口reports/memory_runtime_repair_20261103_r1/RESUME.md、SUMMARY.json；完整调用尚未启动/未通过。仅STHL7626，无板卡/实现/sudo/其他agent/wb/luyou/心跳，根开发日志未改。
- AXI r1至r5全部wire相同但内存未改善；r6复用R序列item仅改善4.29%且改变随机时序，不采用；r7相同读量改16拍突发也未改善，全部数据主机重放通过并保留不同实验身份。
- r8原AXI monitor每拍循环j/k改为任务生命周期，完整wire SHA仍2dfa61574cd666356f1ec32a49b6744736248a4e83f3ad9ded8edd61771c967e、全部131104R及WSTRB通过，增长7292.656→1918.070MiB（下降73.6986%）。源可逆原文、实际compiled monitor SHA ca682e3dce0c5b0e2a659867da5d8e2f151c3c3926f8637380d0e7ff23ea0651。仅有限因果证据，未证明增长全无或所有模拟器内部根因。
- FIFO RLE审计2万拍精确/200万恒定拍仅0.0742MiB保持。新唯一执行experiments/reports/memory_repaired_preview_20261103_r1，入口run_startup.py，WORKFLOW.json/ACTIVE.lock/xsim.log/xsim_resources.jsonl；原完整权重和原RTL/FP32/FIFO/随机延迟类，修复仅仿真支持源。原MASTER守卫/2000拍轮询已有独立控制门槛，随机流身份不同于旧20拍。32GiB组/32GiB余量/7200秒/15ms模拟上限，第6块首AR主动停止，无自动完整调用。
- 工具返回后用tools/review_memory_repaired_preview_20261103.py核实际40960权重拍/5120raw/5120key/64dims/1522哨兵及全部实际编译源。不得先标通过；部分停止的RLE未flush尾段，不能用于完整有限FIFO资格。通过后再手动冻结完整调用及真实7TV/C后检查/全数组/FIFO审计，不提高128GiB原上限。
- 下方r6执行中及无执行均历史；续办只读实际本轮工作流，不重跑prepare/bootstrap。暂停写本轮STOP_REQUESTED并独立核所属组空/锁无，不能凭历史PID。所有旧失败及冻结资产保留。

## 2026-11-03 继续完成T04仿真：真实AXI运行期门槛与无损FIFO记录（当前）

- 当前目标为“完成当前方案的仿真”。按真实AXI资源/逐位门槛→隔离完整RTL数值及有限FIFO审计→必要连续调用回归推进；门槛未通过不盲长跑、不自动升128GiB上限。仅STHL显式zhangben@124.16.71.7:7626，无sudo/板卡/实现/其他agent/wb/luyou/心跳，根开发日志未改。下方“当前无执行”均历史阶段终态。
- 成组模型07e2f1b17f10b989bdb980cc208c463c914170c14fc598851f71aeba21e74c40已通过真实545685504B初始化/34105344字及语义门槛，初始化增量下降85.22%，仍不证明运行期有界或完整RTL通过。
- 新reports/memory_axi_gate_20261103_r1至r5均工具终态、无锁/所属组，主机独立重放1026AR/131104R/2AW/32W/2B、WSTRB内存与所有返回字通过；五份整个wire CSV SHA相同2dfa61574cd666356f1ec32a49b6744736248a4e83f3ad9ded8edd61771c967e。固定1MiB内存累计约2MiB读，原内核增长7285.055MiB；concat改push、直接beat索引、关闭自动item记录、idx标量约束均未改善增长，不能写成修复。直接索引仅改善主机运行耗时。无M14 DUT、单ID/128bit，原0–256随机延迟类原文未改。
- 当前唯一新执行reports/memory_axi_gate_20261103_r6/WORKFLOW.json，入口experiments同名run_micro.py，8GiB组/32GiB系统余量/300秒各阶段保护。仅尝试SLAVE R序列item在driver item_done之后init复用，AR/monitor/model对象不动；必须核真实workflow和完整wire字节一致后才可评价。不得凭引导PID重启或停止，暂停写本轮STOP_REQUESTED并核组空/锁无。
- FIFO原df_fifo_monitor每拍保存两个无限队列。新experiments/fifo_rle_monitor_20261103_r1/df_fifo_monitor.svh SHA7ca5e013f9a5292d783d7e04d0aea9ddd061c22d0dabe2b69b014e091a0b4af1改为流式无损run_length,value，原channel status字节相同，原队列为空。INDEPENDENT_REVIEW主机展开2万拍与原每拍完全一致；200万恒定拍仅增长0.07421875MiB，两条RLE记录。仅监视器单元资格，非实际有限FIFO/完整RTL资格；输出格式变化明确，cosim_design格式报告不伪写PASS。
- 审计入口tools/review_memory_axi_gate_20261103.py、review_fifo_rle_monitor_20261103.py。原失败/无收益版本、原148冻结源/121复用源、质量/板测封存均保留。新完整调用尚未启动；旧完整RTL仍INCOMPLETE，无新decode性能。

## 2026-11-03 成组仿真模型与真实全权重初始化门槛完成（最新，当前无执行）

- 本轮修正及有限验收全部结束，主入口reports/memory_burst_full_input_20261103_r1/{RESULT.md,RESUME.md,INDEPENDENT_REVIEW.json,FINAL_PROCESS_REVIEW.json}。候选模型experiments/memory_burst_model_20261103_r3/mem_model.sv SHA07e2f1b17f10b989bdb980cc208c463c914170c14fc598851f71aeba21e74c40，未覆盖原模型、RTL/FP32/FIFO、板测/质量/封存资产；根日志未改。
- 真实545685504B权重初始化与34105344个128bit字比对原两份二进制全部通过；两份完整源SHA前后及主机再核、1522实际哨兵主机再次对原二进制通过。SV执行所有全字断言，主机不是导出重比完整内存，独立审计明确分工；全程time0主动结束，未运行M14/AXI计算/C后检查。
- 加载前内核0.402805GiB、后7.012901GiB，额外6.610096GiB；对照原44.725822GiB加载增量下降85.22085%。全字检查后内核11.338402GiB，新增4.320415GiB；xsim阶段197.304秒、采样组峰值12427396KiB约11.852GiB，16GiB保护未触发。不能把这些写成FPGA decode提升、整体仿真加速比或完整16GiB资格。
- 门槛绑定同一模型SHA：完整8MiB全部字节、legacy2093回放（旧r1仅该子阶段通过，整体Fail保留）、r4 paired41805实际位事件/516警告每模型完全一致均独立通过；145实际编译源/119未改复用源检查、CHANGES可逆原文通过。small_r2/r3读回整个夹具仍约480MiB增长且tmp改动无收益，百万scalar写仍76MiB，持续增长未全部消除。
- 所有失败保留：small_r1继承ref地址方向导致编译拒绝；semantic_r1/r2动态切片与队列元素的直接四态比较打印相同X却报告差异；r3明确等宽logic复制后严格四态比较通过，同时记录16432次表达式差异；r4只将实际候选模型返回值导出给主机，不改模型/不转二态/不放宽断言。原失败与详细日志全保存，不泛化工具缺陷结论。
- 16:14:07北京时间最终核对所有本轮父创建身份不在、实际所属组空、无ACTIVE.lock；原148冻结源、121实际复用源SHA零差异。当前无后台计算，不自动完整重跑/升阈值/板卡/实现/其他agent/wb/luyou/心跳。完整RTL/FIFO仍INCOMPLETE。
- 下一阶段先真实AXI固定容量多轮突发资源/逐位门槛，测UVM驱动/监视器+模型回调实际增长并区分验证夹具开销；再决定有限块预览和完整调用。初始化已改善不等于实时读路径资源资格，禁止直接长跑。下方所有“执行中”均历史，续办不要重跑既有bootstrap/prepare。

## 2026-11-03 成组仿真访存候选：小门槛通过，真实全权重仅初始化/读回执行中（最新）

- 用户“下一步”授权仿真模型成组读写修正与有限门槛。candidate experiments/memory_burst_model_20261103_r3/mem_model.sv SHA07e2f1b17f10b989bdb980cc208c463c914170c14fc598851f71aeba21e74c40；增加aligned16元素读/写、read_elems/write_elems成组路径、连续pipepage写快路，未对齐/边缘/不连续仍走原单元素路径。原计算RTL/FP32/FIFO/AXI拍数/握手/随机回调不改，原冻结模型不覆盖。工具入口tools/prepare_memory_burst_model_20261103.py。
- 完整工程8MiB r2/r3均实际全字节通过并独立复核：r3加载增101.824MiB（原702.145，约85.5%下降），成组读路径含队列/逐字节检查仍增480.637MiB（原640），复用tmp的r3对r2无实质改善，不能说持续增长已全部消除。百万scalar写控制仍约76MiB；62500次packed写覆盖100万逻辑元素增27.586MiB，工作负载不同不能直接宣称同地址byte写加速。
- 语义门槛：reports/memory_burst_semantics_20261103_r1/LEGACY_REVIEW.json独立回放原2093事件通过，整体r1失败保留；r4/INDEPENDENT_REVIEW.json新41805位级事件/4575含X或Z读/504越界读、512对相差512MiB地址、generic8/32/128、offset97/跨bank/page/部分及不连续写、reinit、no-page及每模型516警告204消息multiset全一致。当前模型SHA与两个门槛绑定。
- 保留失败：small r1新read_packed16地址形参漏input继承ref，展开失败；r2显式input修正。semantic r1/r2在未写X值直接“动态切片 !== 队列元素”比较失败，详细日志两侧均xxxxxxxx；r3严格复制到等宽logic变量后四态比较通过，并记录16432次直接/等宽表达式差异。r4只把packed/generic返回直接导出为实际模型位以供主机回放，未改模型或把X转0/放宽数值。原2093不反复重跑，后续只paired阶段。
- 当前唯一执行：experiments/reports/memory_burst_full_input_20261103_r1/run_startup.py/WORKFLOW.json/ACTIVE.lock，缓存.cache/memory_burst_full_input_20261103_r1/verilog。一次真实545685504B原TV初始化，1522哨兵加34105344个128bit字与原tiled/canonical二进制全字比较，参考文件SHA前后核；**time0结束，不运行完整M14/C后检查**。入口绑定已通过小门槛/语义审计及同一模型SHA，16GiB组/可用32GiB/初始96GiB/展开300秒/运行1800秒保护，无自动下一阶段。
- 续办先读真实workflow/log/memory_phases.csv/resources，不重跑bootstrap或并行修改工作树；暂停仅本轮报告写STOP_REQUESTED，核父创建身份/所属组空/锁无。只用STHL7626，无sudo/板卡/实现/其他agent/wb/luyou/心跳，根开发日志未改。旧完整RTL仍INCOMPLETE；即使初始化通过也不能承诺完整16GiB或decode性能。

## 2026-11-03 初始化高基线及完整工程模型访问增长已实测定位（最新，当前无执行）

- 用户“下一步”授权的本轮6项有限诊断全部结束并独立复核：真实完整输入初始化/20000拍短前缀1项、8MiB最小环境module/UVM×new/factory对照4项、完整工程参考模型路径8MiB固定容量访问1项。主入口reports/memory_full_startup_20261103_r1/RESULT.md、RESUME.md。无完整M14重跑/C后检查/实现/板卡/wb/luyou/心跳；根开发日志未改。
- 完整DUT top初始内核RSS0.101GiB、权重前0.402645GiB、权重后45.128468GiB；权重加载545685504B实际增44.725822GiB，全在sim time0，倍率88.0067B RSS/B载荷。1522哨兵通过；启动后2万拍增28.847656MiB，实际control AR/R各10、meta AR11、weight AR0，尚未权重计算，不能称完整数值/FIFO或稳定内存资格。运行508.099秒、组峰值47944496KiB约45.723GiB，未触发64GiB保护。
- reports/memory_loader_context_20261103_r1/INDEPENDENT_REVIEW.json：四个8MiB小场景加载增64.547～66.977MiB、全读增0.203～0.340MiB、百万同地址写增0，排除这些最小场景中仅由run_phase/new/factory切换引发巨大增长的解释；不是排除所有完整UVM/编译上下文因素。
- reports/memory_full_loader_small_20261103_r1/INDEPENDENT_REVIEW.json：实际完整编译/参考模型调用路径，私有8MiB模式权重，time0主动结束。加载增702.144531MiB、固定容量全读8388608次再增640MiB（80B/访问）、百万同地址写再增76.109375MiB（79.806B/访问）；bank8/slot65536/word128bit/flags16bit、全字节模式/校验和1069547520/最终写0x3f通过。证明模型访问增长不是有效容量增长；尚未确定模拟器内部分配点，不能武断称堆帧/GC缺陷。该小输入不是有效M14计算权重，不许拿来启动计算。
- 两个完整工程诊断145份实际编译源逐份核对，119份原复用源未改，其余有CHANGES可逆原文；16个原快照漏收的.vh/.svh已补取并核原/新相同。审计首次因缺头文件、再因Windows路径分隔符拒绝，均修复审计覆盖后通过，没有放宽RTL断言。准备首次重复ap_done文本断言失败未运行工具，保留说明。
- 12:52:59北京时间FINAL_PROCESS_REVIEW.json独立核所有memory_*及原full_bank_r2父创建身份不在、实际所属组空、无锁；148原冻结源/121原复用源SHA零差异。当前无后台执行。旧完整RTL仍INCOMPLETE、无新decode结论，不承诺16GiB足够。
- 后续先隔离实现加载128bit成组写、AXI模型成组读/部分写候选，降低逐字节访问次数；在本轮完整工程8MiB场景对照RSS与逐位输出，再补512MiB/跨bank/page/offset/XZ/未写/部分写语义回归，通过后再做全权重仅初始化门槛。不得直接完整重跑或按16字节就宣称省16倍，不修改真实AXI拍数/握手/延迟/FIFO。下方所有执行中均历史；不要重跑既有prepare/bootstrap。

## 2026-11-03 用户“下一步”：完整DUT初始化/2万拍短前缀内存采样（当前执行）

- 只在STHL 7626运行隔离experiments/reports/memory_full_startup_20261103_r1，真实入口run_startup.py、WORKFLOW.json/ACTIVE.lock、elaborate.log/xsim.log及资源JSONL。缓存.cache/memory_full_startup_20261103_r1/verilog。不是完整调用，无C后检查/实现/板卡/wb/luyou/心跳，根日志/冻结原源不改。
- 原148冻结源及121实际复用源先核SHA；新副本只加阶段采样、MASTER守卫、2000拍轮询和绑定20,000拍主动结束器。119份未改复用源逐份匹配；原计算RTL/FP32/FIFO/延迟类保持，轮询变化使随机流身份变化。PLAN/CHANGES记录所有可逆文本改动。初始资源96GiB/组64GiB/系统可用32GiB/展开300秒/运行1800秒保护，不升上限/自动完整重试。
- 12:36:03北京时间实际EXECUTING_XSIM，已展开通过，仿真时间0；权重加载452984832B时内核RSS39353324KiB、组约38.629GiB。初始top内核约0.101GiB、meta前约0.119GiB、权重前约0.403GiB，前64MiB加载后约5.901GiB。高基线增长明确集中在流式加载阶段，尚未完成总量/内部调用归因。阶段原始memory_phases.csv必须在终态独立审计，不能先宣称完整RTL或16GiB资格。
- 已准备但未执行memory_loader_context_20261103_r1四项8MiB无DUT对照（module/UVM run_phase×new/factory，另百万次同地址写），等待前作业真实退出后主模型手动启动；禁止并行EDA/改当前工作副本。独立审计脚本review_memory_full_startup_20261103.py及review_memory_loader_context_20261103.py已准备，不能提前签发通过。
- 暂停只向本轮报告写STOP_REQUESTED，由看护停所属组；随后核WORKFLOW父创建身份/所属组空/锁清除，不凭引导PID。准备入口首次因重复ap_done文本拒绝，未启动工具，已改为唯一run_phase上下文；原失败说明保留。旧完整128GiB保护失败及35项+控制3项资格保持。

## 2026-11-03 恢复完成有限内存归因与控制级修正回归（最新，当前无执行）

- 用户“可以恢复继续”后，只接续内存定位；补审原第6/7组，35项有限对照现全部独立复核。tools/review_memory_growth_20261103.py核对CSV/工具日志/冻结入口SHA及每阶段resources.jsonl峰值和成员加和。原前5组审计另保留INDEPENDENT_REVIEW_FIRST5.json。最终归因报告reports/memory_growth_diagnosis_20261103_r1/RESULT.md；根开发日志未改。
- 新独立experiments/reports/memory_control_regression_20261103_r1运行3个有界控制回归，8GiB/300秒/可用32GiB保护；真实冻结control_s_axi RTL、LEN4及逐字提取的原随机延迟回调，计算由固定激励替代。原20拍MASTER与守卫/2000拍均通过正常A/debugB/固定错误返回/正常A；另缺失done负控制无误报。独立重放31实际编译源SHA、全部读写、结果和64位字段/done读清。不是完整算法错误路径或输入模式资格，不含权重/DDR/FIFO。
- 新小回归原版503轮询/547读/12写，内核RSS增60.699MiB；守卫/2000拍34轮询/78读/12写，增8.289MiB（增量降低86.34%），检测done延后261～1305仿真拍。组峰值573396→599600KiB未降低，不可误称峰值优化或硬件速度改善。低频轮询改变随机调用顺序，后续须新实验身份；未接入完整M14、未实现对象池。
- 归因确认MASTER无人消费SLAVE队列及密集UVM对象分配增长；随机回调2万次另增15.695MiB。尚未分解全部128GiB，尤其完整DUT启动约46GiB仍未解释；64MiB模型对照约1.04GiB组峰值不能替代该归因。不承诺完整仿真能在16GiB运行。
- 11:19:00北京时间RESUMED_PROCESS_REVIEW.json核对所有本任务工作流终态、父创建身份不在、无锁/所属组残留；原148冻结源与121复用源SHA零差异。当前无后台计算，无完整重跑/板卡/实现/wb/luyou/心跳。原完整RTL仍INCOMPLETE。后续先隔离接入修正候选并做完整DUT仅初始化/短前缀资源分阶段采样，资源门槛通过后再决定完整重跑；不自动启动数十小时调用或提高保护阈值。

## 2026-11-03 09:52 用户要求安全暂停，内存归因任务全部无执行（最新）

- 用户明确要求暂停、PC断电，停止推进。09:52:04北京时间显式STHL只读核对：本任务所有memory_*20261103工作流及完整full_bank_cosim_20261102_r2均终态；所属父PID创建身份均不在、ACTIVE.lock全无、process_after均空。当前无本任务后台计算，不需要继续等待，可断电。不自动恢复任何实验/完整仿真/心跳/板卡。
- 用户本轮授权定位内存增长，在独立目录完成7组共35项有限对照（全部工具返回；前5组已本地独立复核）。原128GiB保护停止证据及冻结RTL/质量保持。无板卡操作、无完整M14重跑、无sudo。只用STHL 7626；未使用其他agent。
- 已复核事实：MASTER模式原axi_state.write_ar无条件克隆并入SLAVE队列，无MASTER消费路径，2万完成读仍残留2万对象；守卫变体归零，但仍增长。百万次AXI new/null增加约1211MiB，复用/重置对象0～0.215MiB；去掉-debug all不改善新建增长。嵌套队列计数/读取百万次RSS保持平稳。真实控制总线恒零寄存器/无停顿小fixture：约20万周期原20拍轮询9091次、RSS增488.645MiB；2000拍轮询100次、增6.645MiB（增量降低98.64%）。守卫20拍仍增478.332MiB；其完整wire trace与原20拍逐字相同。此fixture LEN_WIDTH8/无停顿，完整冻结控制口LEN_WIDTH4并随机停顿，不能写成完整压力资格或已解释全部128GiB。
- 本地主入口reports/memory_growth_diagnosis_20261103_r1/RESUME.md、INDEPENDENT_REVIEW.json；审计脚本tools/review_memory_growth_20261103.py。前5组原始CSV/日志/源SHA已独立核验；后两组memory_init_probe_20261103_r1、memory_random_probe_20261103_r2已工具通过/取回，但尚未纳入独立数值审计与最终归因汇总。64MiB初始化4场景均约1.04GiB组峰值，不能直接替代完整DUT约46GiB初始基线归因；其原因未彻底解释。不要承诺全仿真能在16GiB运行。
- 保留所有有限测试失败：allocation_micro_r1缺misc接口编译失败；poll_r1在原监视器延迟收尾前断言导致失败；poll_r2实际完成但包装器误把UVM_ERROR:0汇总当错误；poll_r3只修复包装器，3场景全通过。random_r1仅准备未运行，r2显式构造函数后运行通过。恢复后只补后两组独立复核、汇总报告和针对性修复/小回归，不盲重跑35场景或完整调用。根开发日志未改。

## 2026-11-03 T04完整r2终态：128GiB进程组保护停止，当前无执行（最新）

- 本次仅查询与终态归档，无重跑/改阈值/新EDA/板卡。full_bank_cosim_20261102_r2于北京时间11月3日00:46:11退出，累计12小时33分36秒；真实状态FAILED_NO_AUTOMATIC_RETRY。stop_evidence明确GROUP_RSS_ABOVE_128GIB，触发00:46:06、组RSS128.001549GiB、系统可用118.329796GiB；不是整机内存耗尽、48h超时或数值对比失败。
- 08:54:41北京时间独立快照observations/20261103_005441核对组空、锁无。08:57:12 PROCESS_AFTER.json再次核空/无锁，148份冻结源及121份实际复用RTL/支持源逐份SHA无差异。触发原因已明确，但持续增长来源仍未定位，不把本轮原因追认为20261026旧停因。
- 最后模拟时间150.005948ms，完整事务0/1；仅通道选择与ID写回阶段完成，7返回TV仍0B，无C后检查/actual或完整数值/FIFO资格，无新decode性能。结果见本轮RESULT.md、FULL_WORKFLOW.json、PROCESS_AFTER.json。旧Csim/HLS/分段与GPU质量资格保留，完整RTL仍INCOMPLETE。
- 当前无本任务后台计算，不自动重试或升上限，不启动实现/板卡/wb/luyou/心跳。后续需先对运行期内存增长做有限归因及回归，再决策完整重跑；本次用户仅问进度，未启动新诊断实验。下方所有执行中/接近上限记录均历史。

## 2026-11-03 00:30 T04实时查询：完整r2仍执行，接近128GiB保护（最新观测）

- 本次仅查询，未重启/调阈值/改源/新EDA/板卡。远端原full_bank_cosim_20261102_r2仍EXECUTING_XSIM，父创建身份匹配；原模型SHA一致、复用清单匹配。08:16 UTC旧观测之后，同一作业已运行约12小时18分。
- observations/20261102_162949/RUNTIME_SNAPSHOT.json保存11月3日00:29:49北京时间快照：组RSS126.191GiB、系统余量120.116GiB；00:30:28趋势末样本126.262GiB，近一小时增加6.624GiB（3597.48秒）。按该斜率约15–16分钟触及128GiB，仅趋势外推，不是完成时间，也未实际触发。
- 最后模拟时钟150005948000ps＝150.005948ms，事务0/1；阶段仅通道选择和ID写回完成，全预览无完成标记，7返回TV均0B、无C后检查。不能把时钟推进或823.52%当完成率、数值通过或死锁排除。无新decode结论。
- 保持原作业与既有保护；若终态先读实际stop_evidence和所属组/锁，禁止因旧记录仍EXECUTING盲重跑或自动升内存上限。以下11月2日启动快照均为历史。

## 2026-11-02 T04 d64恢复：资源/映射门槛通过，完整RTL r2执行中（最新）

- 用户确认按恢复方案执行。仅STHL显式zhangben@124.16.71.7:7626，无sudo、无板卡/EDA实现/wb/luyou/心跳，根开发日志和冻结质量未改。先完成资源诊断与有限门槛，再由主模型手动冻结启动一次完整验证。
- 旧20261026作业的具体保护触发项仍UNDETERMINED：旧记录合并STOP/48h/内存，缺终态采样；历史RSS约198.84GiB不证明最终触发内存保护。不得把新准备通过写成已证实旧停止根因。事实源reports/d64_resource_recovery_20261102_r1/RESULT.md及REMOTE_SNAPSHOT。
- packed16小bank语义2093事件与原版相同，新增X/Z/padding/reinit通过；4MiB有限读写峰值938488→864484KiB，仅下降7.885%、耗时基本相同，不能外推硬件性能。流式加载三组全字节与4坏输入通过。无DUT真实全权重34105344word/545685504B逐字节与原两份二进制匹配，主机独立SHA及1522回读通过；624.166秒、组峰值6.392GiB，仅加载/回读资格，非完整DUT内存或decode性能。
- 最终集成保留原virtual tvinload_pagechk_atinit及整个offset子类，仅基类对权重TV后缀选择流式读取。reports/d64_stream_integration_20261102_r2独立核对原/新各8192B、两指针元数据、页映射、跨4KiB pipe回调及普通文件fallback通过；不是AXI总线测试。实际模型源experiments/d64_stream_integration_20261102_r2/mem_model.sv。
- 本轮完整入口experiments/full_bank_cosim_20261102_r2/run_full.py，报告reports/full_bank_cosim_20261102_r2，缓存.cache/p64_full_bank_cosim_20261102_r2/sim。包SHA31a9feeb0c09a2ab1852cdbb17f4a1f322270a8ccbdf8fbcbfe39eb538ebbcaa。9门槛SHA核验；原old_chinese/d64/T4096/B1024/双W/debug1、原RTL/FP32/FIFO及随机停顿不变。04:15:05 UTC静态快照实际EXECUTING_XSIM，父身份匹配，121份复用RTL/模型源匹配、资格模型SHA相同，组RSS约10.069GiB；仍初始化，未有完整数值/FIFO或性能资格。
- 新看护每5秒记录UTC/成员PID-start_ticks/RSS/系统余量；48h、组RSS128GiB、可用低于32GiB或本轮STOP分别记录原因并停止所属树。实际STOP/timeout/正常退出/忽略SIGTERM子进程整树清理控制通过。暂停只写本轮STOP_REQUESTED再核组空/锁清除，不能凭引导PID杀进程。只保留此单作业，无自动重试/后续实现或板卡。
- 保留所有新失败：无DUT r1缺UVM宏在编译退出，r2通过；完整20261102_r1绕过offset初始化被主模型发现后主动STOP，无完整资格，终态即时残留后04:00:09 UTC独立查组空，新看护补齐整组等待并通过真实子进程控制；集成r1测试台static task局部队列累积导致原版fallback失败，r2仅task automatic修正后两版通过。旧Fail、全部原报告/源不覆盖。
- 续办先读本轮RESUME.md与远端真实FULL_WORKFLOW/日志/资源，不重跑bootstrap。tools/observe_d64_full_retry_r2_20261102.py只保存有界静态快照；不追随live VCD。工具结束后审真实7返回TV、C后检查及完整全数组/有限FIFO/范围/DSP有效性；旧review_partial_full_bank_20261026.py硬编码旧目录，不能直接套用。cosim_design格式报告仍NOT_RUN，不造官方PASS。后续ABA/正常条件性能/200MHz/板测均后置；下方无运行状态是历史。

## 2026-10-30 性能快照改为真实方案与四类综合比较（最新，仅文档）

- 用户要求用真实方案名、突出方法、合成综合结果、图按不同方案比较。日志默认改为四类等权综合；方案名为L2聚类128中心＋rank128低秩预筛＋BF16候选精算，以及L2聚类256中心＋rank64低秩预筛＋BF16候选精算。主卡前置说明L2取4簇/每簇L16384或8192、低秩Top16384、14特殊ID并集、原BF16权重按FP32合同精算；历史开发代号只保留在证据/历史中。
- 新综合从各版四类各30次原始measurement记录计算，120/Σ((end-start)/counter_hz)，四类各25%，排除预热和稳定调用。128/r128方案20.86980194次/s、平均47.916123ms；256/r64方案27.43650671次/s、平均36.447789ms。不是四个Median输出率的算术平均；合并Median/P95单列，不能混作分母。doc/log_rebuild_20261030/BOARD_SCHEME_AGGREGATES.json保存原始SHA/公式/分项。
- 项目持久生成入口tools/rebuild_dev_log_20261030.py调用journal_scheme_performance_20261030.py/js，仅定制性能区，其余沿用新版skill。默认两根方法柱，横坐标真实方案；综合/中/英/代码/数学切换同时更新主卡与两方案图。历史IP计数方案另列不混入A53图。旧原79条记录/原ID及原备份保持。
- 修改前另备份bak/开发日志_性能修改前_20261030_213523.html。SCHEME_VIEW_REVIEW.json独立Node原始tick重算240条、5种评价切换/两根柱/点击与键盘/resize/历史口径的离线DOM替身测试通过；CHECK_REVIEW静态脚本与199链接仍通过。浏览器file策略限制保持，未绕过；真实渲染/触屏NOT_RUN。无板卡、服务器、EDA或质量重测。

## 2026-10-30 按新版dev-log重建完成（最新，仅文档）

- 用户明确重建开发日志并备份。原开发日志.html已原样保存在bak/开发日志_20261030_205950.html，SHA e3a9f97e6decd1242b34540731d93bc9bc85e9ce958da8ea8b62ab7657b8cd5a；原路线设计页另备份bak/design_before_20261030/。不覆盖这些备份。
- 使用当前C:/Users/ben/.codex/skills/dev-log/SKILL.md及其新版renderer，项目持久维护入口tools/rebuild_dev_log_20261030.py。事实仍由主HTML的dev-log-data维护，未知扩展字段保留；全部79条旧记录对象/ID完全一致，新增11条真实结果与经验，共90条、16路线、5任务。新页面任务/路线显式双向映射，通栏主性能、月历、归档、统一浮动面板沿用新skill实现。
- 默认实板实验10中文30.3023 M14次/s；两版四类可切换，TTFT未测，历史IP计时与新A53口径区分。仅按证据更新当前路线：两版已完成、d64保护停止、v4b仅GPU研究；无运行中路线。新设计页从同份主JSON生成，旧历史结论不改。
- doc/log_rebuild_20261030/BUILD_REVIEW.json与CHECK_REVIEW.json：21脚本语法、199本地证据目标、历史数据/备份SHA、性能原值及任务映射检查通过，无缺失链接。浏览器file://被工具安全策略拒绝，未绕过；桌面/窄屏/触屏视觉和实际交互NOT_RUN，不能称已视觉验收。
- 本次仅写本地文档，不连接/操作板卡、不启动服务器/EDA/心跳。原板测证据ZIP/冻结包/质量数据未改。未来日志更新从当前主HTML读取并用项目新入口，勿运行.cache旧样式迁移脚本回退布局。

## 2026-10-30 两套v4实板验证完成（最新，当前无执行）

- 用户明确新质量标准99%，实验10达标单列QUALITY_GATE_99（原FINAL_QUALITY/99.9%失败保留）；已确认板卡本任务独占并授权早期v4混合及实验10顺序上板。本轮已完成，不自动重跑或启动下一路线。
- 事实源module_14_lm_head_v4/reports/dual_board_20261030_r1/FINAL_INDEPENDENT_REVIEW.json、RESULT.md、BOARD_FIXED_INPUT_SUMMARY、FINAL_TARGET_STATE及PROCESS_AFTER。两版四类各3warmup/30计时/1000稳定，实际8264条固定输入记录（240计时/8000稳定）独立核对全部nonce/status/token/score/CRC/原始XTime及SHA。每批320MiB TCP、320目标块CRC/全CRC/34回读通过；全部计算数据PL DDR。
- A53完整control_call median早期v4中文44.731572/英文54.955600/代码48.147811/数学43.828893ms；实验10为33.000825/45.404779/35.193607/32.184022ms。同输入加速1.3555/1.2103/1.3681/1.3618倍，仅四冻结校准hidden/history的M14局部输出，不能写成全语料/整网decode/TTFT，亦不与v3.1历史IP计数直接混比。
- 两版四类全151936 preview/完整候选ID及canonical raw/13区域guards均逐位通过：7个单独debug用例，早期v4中文额外由ABA中B提供完整数组。两版均同一硬件数学→中文→数学三调用输入真实回读/全数组与A前后完全相同；各4个有限预检（VALIDATE_ONLY/magic/overlap/command）通过、无旧token、三scratch头保持。不是自动累积history或自由生成/任务准确率验证，正式交付身份尚未发布。
- 各root/reports/board_acceptance_20261030_r3/{case}有原始header/records及独立复核；board_debug_20261030_r2、board_aba_20261030_r2、board_errors_20261030_r1有实际全数组/日志。证据ZIP BOARD_EVIDENCE_20261030_r1.zip SHA6137b007abdbd2df702de2c12fcb9a4ddd358eab52e75ab296b5a30a8d616a05，成员SHA及ZIP CRC独立通过；仅证据，非含权重/镜像的部署交付包。
- 末态保留早期v4镜像与数学输入/生产descriptor/command；实际A53停止、GEM停机、selector空闲、MIG校准1。PL0=0x01010203/DPLL=0x00014800/TO_LPD=0x00000300匹配200MHz配置，非物理频率计数器。所属Python/XSCT执行进程空、无ACTIVE.lock，hw_server只是调试服务；无后台板卡计算。
- 后续入口用每用例隔离运行副本，loadhw会在XSA旁解压文件；原绑定bit/XSA/PS init/ELF与软件源SHA全不变，原额外生成文件保留。Windows xsct.bat exit0不证明Tcl成功，必须动作标志且无错误；初始held-reset与末态Already stopped只接受精确已知状态。首轮初始化/TCP失败与旧cleanup误报、目录污染预检、debug错误夹具路径、ABA mwr未给字数的拒绝（实际需显式字数，与help省略用法不同）、首次收尾Already stopped均保留；不能用失败包装器文字作通过证据。
- 原d64完整仿真仍保护停止，未重启STHL EDA；不恢复wb/luyou/心跳，v3.1/v4/v4b冻结资产/原质量与根开发日志未改。下方执行中及“板卡NOT_RUN”均历史，未来任务先读本轮RESUME和真实目标状态。

## 2026-10-30 实板首轮两中文通过，实验10全数组逐位通过（最新）

- 用户已确认本任务独占，99%新门槛下实验10达标单列记录，原99.9%失败历史不改。STHL d64仍停，不自动EDA/wb/luyou/心跳。
- 早期v4中文实际320MiB装载/320目标块CRC/全目标CRC/34回读通过；3warmup+30计时+1000稳定调用实际1033条原始记录独立重核通过，A53完整control_call median44.7315723157ms/P9544.7424174242ms，22.35557次/s，K21529。
- 实验10中文同口径median33.0008250083ms/P9533.0291002910ms，30.30227次/s，K17764，1033调用独立通过。随后reports/board_debug_20261030_r2/chinese实际151936 preview、17764 IDs/raw、13guards及生产→debug→生产descriptor逐位通过。不是全语料板测、动态history/整网decode或TTFT。
- 汇总reports/dual_board_20261030_r1/BOARD_FIXED_INPUT_SUMMARY.json；各root/reports/board_acceptance_20261030_r3/{case}保存PLAN/控制派生/TRANSFER/实际header/records/CAPTURE_RESULT/INDEPENDENT_REVIEW。tools/run_v4_board_r3_20261030.py每次一个用例，返回后主模型手动审计再推进；当前继续实验10英文，查EXECUTION/日志，不用历史PID。
- 首轮A53初始stop报APU L2 held reset；r2真实trace证明其发生在私有签名/MIG/idle通过后，r3仅放行该特定初始已复位状态再原rst-processor/dow/con。未改bit/XSA/ELF；原Windows xsct.bat会把Tcl错误返回0，所有行动必须有动作专属成功标志、无错误字样，不能仅看exit0。原失败/虚假cleanup说明保留，不当作停机成功。
- XSCT loadhw会在XSA旁解压附加文件；原13份SHA全不变，新增文件已保存preserved_loadhw_generated，原冻结目录恢复仅绑定文件。后续每用例在runtime_packages/{variant}_{case}使用独立原SHA副本，原包不再给loadhw。保留英文第一次本地package污染预检失败及debug首次夹具路径预检失败，均未额外连接目标；实验10fixture实际在模块fixture目录。
- tools/capture_v4_debug_20261030.py只在对应已审计生产调用之后、CPU已停/IP闲时检查完整原descriptor/64位参数，再切冻结debug descriptor，运行一次并回读全数组/13guard/恢复生产descriptor。超时/错误不继续写内存，先确认状态。数值是精确bits，无放宽。

## 2026-10-30 用户授权两套v4独占上板验收（最新）

- 用户明确新质量标准为99%，实验10判达标；保留原FINAL_QUALITY的99.9%失败历史，新增reports/dual_board_20261030_r1/QUALITY_GATE_99.json记录原SHA/各类与整体数据，未重调参/评估。用户已连接板卡并明确“可由本任务独占使用”，覆盖下方禁止板卡操作安排，仅限本次早期v4及实验10板测。
- G盘已恢复，XSCT2021.1可读。以太网192.168.0.12/24、链路100Mbps；JTAG初见PS TAP，第二次连接已出现PSU/A53，已有recover_debug_access未实际执行DAP/POR复位（DAP目标不存在、PSU已可选），不能写成复位修复成功。
- tools/prepare_dual_v4_board_20261030.py完成两套四类共8个离线生产arena/包/软件源SHA/descriptor计划预检，存各root/reports/board_acceptance_20261030_r1/{case}。本轮汇总reports/dual_board_20261030_r1。未修改冻结镜像或软件源。
- tools/run_one_v4_board_20261030.py每次只执行一个已冻结固定输入，真实EXECUTION/initialize_loader/TRANSFER/campaign/header/records/CAPTURE_RESULT保留于对应case；共用汇总ACTIVE.lock避免并发。当前先早期v4中文，实时阶段取日志，不凭旧PID。按完整初始化→TCP320MiB/320目标块CRC/全CRC/34回读→CPU/GEM停机验证→3预热/30计时/1000稳定调用→主机nonce/status/原tick验证。失败不自动重试/切镜像，清理仅在核空闲后停CPU/GEM；超时IP可能仍运行，先查实际状态。
- 固定输入计时不等于全debug数组/多步history/错误路径验收或整网decode/TTFT，后者另核；没有硬件IP周期计数器，以A53完整control_call原tick报告。两套顺序执行；所有新板测结论须独立检查实际记录。新d64保护停止保持，不重启STHL仿真，不恢复wb/luyou/心跳；原封存和GPU质量不改，根开发日志未改。

## 2026-10-30 状态复核：完整分bank验证已保护停止（最新）

- STHL真实FULL_WORKFLOW为FAILED_NO_AUTOMATIC_RETRY，10月27日06:14:25停止，运行约17小时35分，错误stop/time/resource guard: xsim。该错误合并停止请求/48h/低于8GiB内存保护，尚未独立确定触发项，不武断标为数值失败或超时。
- 10月30日18:55只读核验所属组空/无锁；末次模拟时间200.007078ms，完整事务0/1。仅通道选择及ID写回完成，全预览尚无完成记录；7份RTL返回均0B，无actual/C后检查。完整数值及FIFO资格未完成，不能标PASS，无新decode速度结论。
- 事实源reports/full_bank_cosim_20261026_r1/observations/本次RUNTIME_SNAPSHOT、FULL_WORKFLOW及RESULT.md。前5块通过及原失败保留。当前无后台执行，不自动重试/新EDA/实现/板卡/wb/luyou/心跳；后续先查保护触发及仿真内存增长。本次未改核/参数/质量/封存或根开发日志。下方运行中均历史。

## 2026-10-26 前5块独立验收通过，完整分bank联合验证启动（最新执行）

- 前5块于12:29:37退出，PREVIEW_REVIEW.json独立核对5120raw/5120key/64dims、40960权重拍（320突发）、2576写拍及1522模型边界字节全通过；不是完整RTL资格。PROCESS_AFTER核对所属组空、无锁、原133源及复用模型/RTL SHA不变；终态归档SHA91744f3fab0ca434b811a295ffe820467cd9e7070033bd765fa35ebca58062e8已核验取回，原失败/首前缀记录均保留。
- 被动阶段观察器三调用/错误返回与真实RTL绑定、被动范围观察器7场景/真实RTL绑定、原C后检查正负控制均独立通过。范围器检查真实AXI请求的模型边界、4KiB、长度/对齐、64位溢出/未知地址及只读权重写，弥补返回TV未包含额外end guard的观测范围。
- 已手动启动experiments/full_bank_cosim_20261026/run_full.py；reports/full_bank_cosim_20261026_r1/PLAN及entry SHA1579af1f1de9444a4d02bf8c0dad22ac678454fc0c585092de5162f16f838bca冻结4项真实审计门槛及源，真实状态FULL_WORKFLOW.json/ACTIVE.lock/elaborate.log/xsim.log/c_postcheck.log。新.cache/p64_full_bank_cosim_20261026_r1/sim，父/PGID必须读实时文件，不凭引导快照停止其他任务。
- 一次原old_chinese完整d64/T4096/B1024/双W/debug1调用，原RTL/FP32/FIFO及强随机停顿字节不变；仅修仿真存储、加1522读回与无输出观察器。复用原完整TV、原生成XSIM、原cosim.pc.exe，独立空fixtures不放预生成actual；不再运行会覆盖修复的cosim_design生成步骤。报告应写生成XSIM/C后检查的真实结果，cosim_design格式化报告NOT_RUN，严禁复制旧Fail/伪写官方PASS。
- 本阶段只有工具返回后全151936预览/key、完整ID/raw/token/score/CRC及实际有限FIFO独立审计通过，才可取得单输入完整工程资格。ABA/生产切换、正常条件性能、200MHz实现和板卡仍后置。当前不操作板卡、不恢复wb/luyou/心跳、不改封存/质量/算法参数。
- 入口初始内存需200GiB，运行余量低于8GiB或48小时/本轮STOP_REQUESTED时停止所属组；STOP由父看护每10秒检查。暂停可在本轮报告建STOP_REQUESTED后等退出并核身份；没有自动重试或后续阶段。下方“仅规划/前5块运行中/完整未启动”均历史。

## 2026-10-26 用户授权按规划实施（当前执行）

- 被动计时观察器已实际单元及真实DUT bind展开通过，INDEPENDENT_REVIEW核对三调用5行（阶段6/3拍、总8/5拍、错误返回2拍及AXI计数），没有实际M14性能数据。原C后检查器正控制通过；负控制只改preview1bit即失败且不生成新actual，reports/postcheck_control_20261026_r1/RESULT保存。原控制包装器误认为expected头12B、实际16B的断言失败保留；正控制未重跑，续办只补负控制。
- 已只读独立核对完整模型1522字节和running1波形前缀：15638权重拍无差异、64通道与首块1024raw/1024key逐位正确；仍不是全部前5块资格。直接传live VCD迟迟未结束，已核对本任务精确命令行停止其scp进程，仿真未动；保留前缀并成功审计。后续用collect_partial_bank_preview_20261026.py静态压缩快照/终态归档，不能再直接跟随追加文件长传。
- 新完整入口源experiments/full_bank_cosim_20261026/run_full.py已准备但未冻结/未运行；必须先有前5块独立审计、进程退出、观察器及后检查正负控制，再由主模型手动冻结启动。复用原生成XSIM/原cosim.pc.exe及全TV，使用已验证内存修复和被动观察器；不调用会覆盖修复的cosim_design生成步骤、不伪造其格式化报告PASS，实际数组和FIFO另审。fixtures不放预生成actual，C参考专用数据与RTL证据隔离。
- 返回TV不序列化额外end guard，原C测试台guard检查不能冒充RTL越界观测。当前在隔离range_observer_20261026_r1验证无输出AXI范围bind：合法端点、512MiB两侧、错误高位、meta末端/旧256B空隙、4KiB跨界、权重写、64位溢出及X地址7场景，真实WORKFLOW/各mode日志；不修改正在执行的前5块作业。其通过是新完整入口额外门槛。
- 用户“按照你的规划开始实现”已覆盖上一段仅规划范围：按前5块独立验收→完整数值/FIFO→代表性ABA/模式→性能决策→200MHz实现门槛推进；板卡连接/独占仍需另行确认，不操作板卡。当前原PREVIEW门控继续，不重启、不更改其冻结源或压力条件。
- 并行准备性能入口（非并行agent）：新experiments/perf_observer_20261026、reports/perf_observer_20261026_r1。观察器仅input端口，bind冻结DUT；统计通道选择/ID写回/预览/Top-T/精算及整次调用的边沿周期、AXI数据拍和明确的背压事件。空闲done高必须先见busy才算完成，支持三次调用/错误返回测试；auto_restart持续start高尚不在资格内。
- 冻结entry SHA9334f862031b8d5c5e3505f663c3bc4c7154f3b1c5201caf7db1b6e9010a4983；run_partial_observer_20261026.py仅观察器单元仿真及真实RTL bind展开，每阶段300秒，上限后停止所属组。真实WORKFLOW/ACTIVE.lock及各phase日志在本轮observer报告；不运行完整M14，不修改正在执行的bank_preview，不自动启动下阶段。指标含启动/存储等待，阶段可能边界重叠，不可直接相加或换算真实FPGA decode。
- 所有远端仍显式STHL zhangben@124.16.71.7:7626，勿用7627。核RTL/算法参数/冻结质量/原失败保持，不恢复wb/luyou/心跳。暂停分别读当前PREVIEW与observer父创建时间/所属PGID，只停止本轮树，不凭历史PID。

## 2026-10-26 用户要求后续规划（仅规划，不启动新阶段）

- 新规划doc/design/V4_NEXT_TASKS_20261026.md：前5块门控→完整数值/FIFO→代表性ABA及模式切换→统一条件分阶段性能决策→200MHz最小M14实现→另行确认独占后的同板验收。性能入口/统计可先准备，实测结论依赖正确性资格。
- 最新只读查询原PREVIEW_WORKFLOW仍EXECUTING_PREVIEW_SIMULATE，file_read_agent已报告weights文件read done，但无1522字节实际回读或前5块数组终态，不能记通过。已有作业继续，本次没有启动新EDA/完整CoSim/板卡或心跳。
- 规划明确分段承接主要边界/背压测试，少量完整配置检查阶段衔接，不默认每输入重复数十小时强压力完整调用。强压力周期与性能用存储条件分列。主性能指标M14耗时及等效token/s；与v3.1对照需统一条件，历史与本轮同板数据分开，权重加载不冒充TTFT。核参数/冻结质量/封存均保持。

## 2026-10-26 用户继续：仿真byte-memory分bank修复执行（当前）

- 单元实际17秒完成，独立UNIT_REVIEW.json核对2093事件（W1033/R1055/BW2/INIT3）、15边界拒绝/13次X返回（11越界、2未写）通过；512别名对、32/128位及X/Z断言通过。原read_elems作为task调用的warning保留，未影响门控。仅仿真内存修复通过，不是完整RTL通过。
- 已人工启动run_partial_bank_preview_20261026.py，真实PREVIEW_WORKFLOW.json/ACTIVE.lock/preview_elaborate.log/preview_simulate.log；新.cache/p64_bank_preview_20261026_r1/sim。冻结PREVIEW_PLAN及归档SHA06d86a729d2def10a167d9925587899a5e3fed8fa7d67324fa4786f11548edbd：原全34105344拍TV逐字解码重建tiled/canonical完整SHA；1522个每bank端点/512MiB/权重分界/前块/末端字节回读（不是全模型SHA），通过后在原RTL/原随机停顿下观察前5块。到tile5首AR即停，VCD需独立核对40960权重拍与全部5120raw/key。仿真15ms/主机7200秒上限，MemAvailable低于8GiB停止所属组。没有自动完整CoSim/实现/板卡。
- 原完整TV两权重SHA门控已实际通过，完整RTL/压力源复用SHA清单已保存。最新观测仍在file_read_agent载入全weights TV阶段，尚无BANK_FULL_INPUT_SENTINEL_PASS、前5块raw/key或完整RTL通过。tools/review_partial_bank_preview_20261026.py已准备，不能提前运行/签发资格。V4PartialRTL.html及导航同步单元通过/分段进行中；原557双组数据与交互回归保持，根开发日志未改。
- 用户“继续”授权按定位结论推进：新隔离experiments/sim_memory_bank_20261026、reports/sim_memory_bank_20261026_r1，冻结PLAN/entry SHA0ab01b40c27ee8e3faf02441f67aa57fc314090e2a5a10d400b27a8d2efaae81。只改生成仿真内存类，将每个大动态mem/IsWr拆为独立class内最多1048576元素的小数组，按需分配；保留int depth/offset、原longint范围检查、未写X及warning/is_rd、批量读写语义。原模型和核源/参数不改。
- 单元门控512组相差512MiB地址、跨bank、部分越界写、负数/末端/超过4GiB拒绝、offset97/零长度、32/128位及X/Z存储；完整页接口未宣称高物理地址资格。运行入口run_partial_banked_memory_unit_20261026.py，真实UNIT_WORKFLOW.json/ACTIVE.lock/elaborate.log/simulate.log；每阶段240秒上限，所属父/PGID实时记录。不得因入口exit0或回显PASS字符串宣告通过，须实际行首PASS及独立事件回放。
- 当前只执行单元门控。通过且独立核验后主模型手动准备全权重回读预检查及前5个块预览观测，再据结果决定完整CoSim；没有自动下阶段，不改随机停顿/FIFO/RTL或质量，不改原full_r3 Fail。仍显式STHL zhangben@124.16.71.7:7626，不连7627、不操作板卡、不恢复wb/luyou/心跳。暂停按本轮工作流父身份/所属组核对停止，历史PID不能使用。

## 2026-10-26 差异根因已确认：XSim 512MiB动态数组别名（最新，定位阶段结束）

- 用户“请定位差异”已完成定位，未修改核RTL或参数。事实源reports/partial_rtl_20261026_diagnosis_r1/ROOT_CAUSE_REVIEW.json、RESULT.md、STAGE_CHAIN_REVIEW、alias_minimal/r2.log、r6/AXI_TRACE_REVIEW及PROCESS_AFTER。根因是本机STHL XSim2022.2 SW3671981动态logic[7:0] mem[]在相差0x20000000字节的地址发生别名；原生成CoSim mem_model_pages_with_diffofst#(128,8)使用该数组。
- 两权重273416192+272269312=545685504B（520.40625MiB），越过512MiB后canonical尾部8814592B覆盖tiled开头。tools/prove_partial_xsim_alias_20261026.py按覆盖关系重建全部151936词预览，与原RTL返回151936/151936逐位一致（包含所有5120差异）。覆盖4块及第5块前720通道，本输入选中其中52通道，解释为何前5块全错、之后全对。不是浮点舍入或质量召回问题。
- 独立不含lm_head最小SV：先写0x1200=0x12，高地址0x20001200也读0x12；再写高地址=0x34，低/高均读0x34。源码及实际日志保存；首个最小入口库名错误保留，实际work库r2复现成功。原TV前7块802816拍与冻结tiled逐字节相同，原文件没损坏；损坏发生在仿真动态存储中。
- 返回preview→key→稳定Top4096/14特殊ID→实际候选canonical精算→输出链路全一致，4109个实际候选raw逐位正确。DSP告警不是本次预览差异根因，不因此概括其在其他输入无害。原官方full_r3仍Fail，不能改成PASS；需要修仿真存储后重新取得完整RTL资格。
- 有限输入因果对照r6保留前7块可达权重、原RTL及随机停顿，地址哨兵无触发，64突发8192拍权重供数全对，首个预览128位写回4值与正确参考一致；只到首写，绝不是完整RTL通过。r6包装器错误地把日志回显guard字符串当触发，原WORKFLOW保留，PROCESS_AFTER以行首实际事件/exit0/VCD复核真实首写成功并于2.3951625ms主动停止。原全TV r4已核身份安全停在初始化；r1/r2/r3/r5入口失败均保留。
- 所有本轮所属组空、锁无，原133源SHA不变；远端证据归档SHAaa38177d1d27d7518b9d72945aa325f4f9cb219f51bfcc32fe827ff2b4833bd5核验取回。当前没有后台计算。V4PartialRTL及导航同步根因，根开发日志未改。后续只拟隔离byte-memory小bank修复→512MiB/高地址边界→前5块→完整CoSim，不自动新EDA/实现/板卡，不恢复wb/luyou/心跳，不改冻结/封存/质量。下方“执行中/UNRESOLVED”均历史。

## 2026-10-26 用户授权定位：隔离首块信号观测（执行中）

- 最新观测入口为run_partial_compact_probe_r6_20261026.py，真实r6/WORKFLOW.json、ACTIVE.lock、probe.log；.cache/p64_signal_probe_20261026_r5/sim为有限输入副本。r4因全1.19GB TV初始化成本已核对父身份/所属组后主动停止并保留；r5的xsim条件不支持>=、计算前退出保留。r6将范围判断放入标准Tcl，复制原输入TV前7块802816拍且保存prefix SHA，未供给之后数据；AR地址哨兵禁止访问>=12845056。只到首块预览，不是完整CoSim资格，必须对照原失败首词才能称复现。原d64/T4096/RTL/压力不改。r6已进入DUT，首份VCD前缀模拟0.5343975ms尚未有权重AR，不称预览已完成。
- 用户“请定位差异”后，只分析原失败证据并进行有限预览观测，不重跑完整联合验证/新HLS/实现或板卡。新隔离reports/partial_rtl_20261026_diagnosis_r1、.cache/p64_signal_probe_20261026_r1/sim；原full_r3失败、冻结源和质量结果保持。STHL仍显式zhangben@124.16.71.7:7626。
- INPUT_TV_PROBE.json确认原CoSim权重TV前7块802816个128位拍与冻结tiled逐字节一致，canonical起始1024拍相同，两权重SHA不变。STAGE_CHAIN_REVIEW.json确认返回预览→policy键→稳定Top4096+特殊ID→实际候选canonical精算raw→最终token/score/CRC逐段一致，第一处已观察错误在预览raw，非后续排序或精算。尚未定位根因。
- r1原快照无trace信息、r2空时钟匹配、r3条件默认二进制基数三个观测入口错误均发生在计算前，日志保留。r2仅xelab -debug all展开同份RTL（无HLS/逻辑改动），r4观测使用其快照，明确ap_clk与unsigned基数。
- 当前真实阶段见远端新报告r4/WORKFLOW.json、ACTIVE.lock、probe.log；run_partial_signal_probe_r4_20261026.py为入口。复用原TV、原随机停顿和完整配置，只观测权重AXI读及meta写，首块第二个预览写地址632128握手即停止；模拟5ms/主机1200秒上限，不是完整RTL资格。前三个入口已退出，勿重跑其runner；当前PID须读实时工作流，不引用历史。
- 暂停先核对r4父创建时间/所属child_pgid，停止父与所属树，保留VCD/日志；没有自动后续任务。根因确认前不改冻结计算源，不生成PASS。无板卡/wb/luyou/心跳，根开发日志不改。下方“本次仅问状态”已被本轮定位授权覆盖。

## 2026-10-26 完整CoSim结束：预览数组不一致，当前资格FAIL（最新状态）

- STHL原full_r3于北京时间2026-10-26 00:33结束，FULL_WORKFLOW为FAILED_NO_AUTOMATIC_RETRY。官方xsim完成返回后C postcheck报CSIM_FAIL full preview bits RTL_full_chinese，官方cosim报告Verilog Fail；不是仍在运行或超时等待。PROCESS_AFTER核对所属进程组空、锁不存在、133份冻结源SHA不变；未启动重跑、实现或板卡操作。
- 已核验终态归档SHA79094107ad57b399ca2b62c6b349d2b452ec37dbb2b321ce1a27dbb94efc72fc并取回官方报告，另取回C/RTL各7份autotvout。tools/review_partial_full_failure_20261026.py直接解析返回meta总线（输入1523拍后是工作区），FAILURE_REVIEW.json确认C TV与冻结夹具一致，RTL词ID0–5119共5120个预览raw及排序键不同，其余相同；64通道相同。候选4033个位置不同，集合参考独有316/RTL独有316。最终token20412、score_bits、CRC、K4109及预览读拍数均相同，不能代替全数组逐位通过。
- 实际RTL工作区保存full_r3/RTL_RETURNED_WORKSPACE.u32.bin、原始返回数据在returned_tv/。注意full_fixtures_r3/actual_RTL_full_chinese.bin可能来自前置C参考；本轮postcheck在写该文件前已失败，不能当RTL输出。原PASS审计器不要用于此失败终态；当前仅FAILURE_REVIEW，不生成INDEPENDENT_REVIEW PASS。
- 根因UNRESOLVED；DSP告警出现在后续精算路径，尚不能与预览差异建立因果。压力模型实测83748670周期不是正常DDR/FPGA/整网decode速率，不能与v3.1板测直接比较。选择器分段13例、原Csim/HLS及GPU质量结果保留；完整联合RTL未通过，新200MHz/BSP/ELF/板卡仍未完成。
- V4PartialRTL.html及V4Validation导航同步失败终态；原新旧557图脚本保持不变，根开发日志未改。后续需单独定位预览/返回映射差异，保留原失败再拟有限复现；本次用户仅问状态，不自动重跑/修源/新EDA。不连接板卡、不恢复wb/luyou/心跳、不改冻结参数/质量或封存。下方所有运行中描述均为历史。

## 2026-10-25 22:00状态诊断：有路径活动，但DSP告警未决（当前状态）

- 原full_r3仍EXECUTING，运行约25小时，未改条件/重启/开启新EDA。周期性日志已到350.003268ms；DSP告警事件时间继续到384.6486125ms，不能混为完整事务完成。诊断文件full_r3/diagnostics/20261025_dsp_r1/WARNING_DIAGNOSIS.json保存一致快照、样本及官方原语代码片段，原73份综合SHA不变。
- 首次DSP48E1 OPMODE=0110X0X/CARRYINSEL=000告警在317.2029725ms，路径为candidate_dataflow/dot_product_rows；之后reduce_rows亦出现。22:00快照共106197条（点积21784、归约84413），比仅时钟有更多路径活动证据，但不是valid数据/数值正确性证明。
- 未匹配到UVM_ERROR/UVM_FATAL/ERROR:/CSIM_FAIL或明确deadlock detected错误；7份RTL返回文件仍0B，无最终PASS/FIFO报告。官方2022.2 DSP48E1.vhd非法控制分支设置output_x_sig并发severity Warning，是否作用于有效输出尚未核对，不能忽略或直接判失败。经验库OPMODE检索0命中。当前判定RUNNING_WITH_DSP_WARNINGS_UNRESOLVED，不能称已确认正常推进。
- 告警诊断包SHA7177a77241eb279559147be8a33a94e1deb3b34c3c38ff15a233cd16cda256a7已核验取回；不屏蔽告警、不改源/FIFO/停顿条件、不并行新EDA。继续保留原作业，终态后完整数值/FIFO及告警valid关联复核再决定资格；仍不操作板卡/恢复wb/luyou/心跳，不改冻结参数/质量/封存。下方观察仅为历史。

## 2026-10-25 第三次续办观测：200ms，完整事务仍0/1（当前状态）

- 同一full_r3仍EXECUTING，无重启/新EDA/条件变更。第三观测observations/20261025_r3/RUNTIME_SNAPSHOT.json记录模拟时间200003253000ps=200.003253ms、完整事务0/1、相对HLS估计1098.03%；主机已运行约14.42小时，父创建时间匹配，原73份综合SHA不变。还无最终RTL PASS、返回数组或FIFO报告，不能启动200MHz实现。模拟时钟不是AXI数据或计算阶段完成证明。
- 新增PRESSURE_SCALE_MODEL.json只做既有压力配置的量级分析，未运行新测试：149*64*128=1220608拍预览W、4109*112=460208拍精算W，共1680816拍。按生成dist相加权重、独立抽样及逐拍串行间隔的抽象假设，平均延迟128/3拍，仅读通道传输+间隔约73395632周期/366.97816ms。这不是实测总延迟，不包含全部计算/仲裁/重叠，不估剩余主机时间或完成率，也不能排除死锁/证明正常decode速度。
- 第三观测包SHA778aea07c56abb5ff622352627b63691061dc8a760d9496b7f473f8cca0d7820已核验取回，前两份保留。V4PartialRTL.html新增三次带时间对照及压力开销量级解释，13本地链接及内嵌脚本逐字一致检查通过；视觉NOT_RUN。仍只保留原压力作业继续运行、不操作板卡、不恢复wb/luyou/心跳、不改冻结数值参数/质量或封存。终态后按RESUME.md取回并独立核验，勿盲重跑。

## 2026-10-25 07:30续办：同一完整压力作业仍未返回（最新观测）

- 原full_r3仍EXECUTING，父创建时间匹配，未重启/派发/更改条件。第二份独立观测observations/20261025_r2/RUNTIME_SNAPSHOT.json保存最后模拟时间150003248000ps=150.003248ms、事务0/1，相对HLS估计823.52%。较首份50.003238ms多100.000010ms模拟时钟；不能将模拟时钟推进或823.52%当算法阶段完成、完成率或死锁排除证明。没有最终RTL PASS、返回数组或FIFO报告。
- 只读复核原73份综合SHA不变，压力配置同前0～256拍随机回调；未启动第二份仿真或200MHz实现。主机观测已运行约10.47小时，xsim RSS约78.5GiB、可用内存约167.6GiB（同次资源查询），尚无最终工程结论。后续若任务终态，按RESUME.md取回和独立核验，不盲重跑。
- 第二观测包SHA8921a1b82646f81dd2ba85160a4d72052599b2290fb6002ba1528dfde67c5898已取回并验证；首份观测完整保留。V4PartialRTL.html展示两次带时间观测及“主机时长/模拟时钟/完整事务”的区别。仍不操作板卡、不恢复wb/luyou/心跳、不更改冻结/封存/质量结果。

## 2026-10-25 续办只读观测：原完整RTL继续压力运行（当前状态）

- 用户“继续”后未重新派发或重启任何EDA。STHL原full_r3仍EXECUTING；observations/20261025_r1/RUNTIME_SNAPSHOT.json与cosim_snapshot.log保存真实观测。父创建时间匹配、所属组存在、ACTIVE锁仍在；最后事务0/1，模拟时间50003238000ps=50.003238ms，日志274.51%为已耗周期/HLS估计比值，不能标完成率或PASS。无返回数组/最终FIFO报告，不启动200MHz实现。
- 已只读核对实际AXI压力模型：meta/weights的clatency子类在AR/R/AW/W/B每次回调随机0～256拍（分布0:=8,0:=1,256:=1,[0:256]:/2），读数据逐拍调用。sequence的旧isusr_delay=NO_DELAY字段并不绕过这些实际clatency回调。这是压力测试，不是无停顿性能测试或物理DDR时序；不能据总周期推算正常decode。没有为了加快而修改现有停顿/FIFO或再开第二份仿真。
- 73份原冻结综合文件SHA复核不变；观测包SHA37f7a623ac364a61e7d080f290a954ae074d5f489476accccddc8a213ee2e5f3已核验取回，包含生成模型/工作流/日志快照。doc/design/V4PartialRTL.html新增带时间的压力条件和历史观测，10本地链接/内嵌脚本逐字一致/旧新557交互回归通过；视觉NOT_RUN，根开发日志未改。
- 继续只观察已有full_r3；结束后按RESUME.md收集真实报告并做全数组及有界FIFO独立复核。所有下方活动PID是历史，暂停须先读取当前FULL_WORKFLOW并核对/proc创建时间/所属PGID。不操作板卡、不恢复wb/luyou/心跳、不改冻结参数/已打开质量结论或封存包。

## 2026-10-24 选择器RTL13例通过，完整联合CoSim执行（当前执行）

- 新隔离experiments/partial_rtl_20261024及reports/partial_rtl_20261024_r1，不改已完成r3数值源/综合、参数或任何质量结果。选择器直接实例化原生成radix RTL与原meta AXI适配器；完整151936 keys/T4096、64位0x400000ff0起址、4KiB拆分、五通道确定性停顿、A-B-A/全平局/重复桶/特殊ID共13例，逐例比较整个79331拍工作区并保存实际数组。
- 选择器于20:49:53完成退出，r4/INDEPENDENT_REVIEW.json独立复核13例/4125212个32位保存值、稳定Top4096/特殊ID/填充/全guard及A-B-A通过；53源SHA不变、所属组为空和锁不存在见PROCESS_AFTER。总AR背压1027652、R间隙516474、AW背压1468、W背压42272、B延迟1430周期及1937边界起始均实际覆盖。每例约160万模型周期，不换算整M14/FPGA decode。
- 测试入口r1缺两生成依赖、r2/r3测试台过早采样idle-high done的失败均保留。子模块ap_done空闲也为1，测试台r4等start生效后采样；核RTL/适配器/模型/向量未改。原HLS r3与测试台r4是不同层次修订号。
- 手动完整联合CoSim当前为full_r3：克隆既有r3综合，hls.app只替换一条TB路径、RTL逐份SHA复用；原full_r1绝对project名错误、full_r2不存在remove_files命令两次入口失败均保留，均未核计算。实际2022.2命令表已核查，采用相对open_project、无remove_files。当前真实状态full_r3/FULL_WORKFLOW.json/ACTIVE.lock/cosim.log，父启动快照37009仅历史，暂停须重新核对。
- full_r3已进入官方xsim并完成1193687114B权重事务读入；不能据此称完整RTL通过。固定old_chinese一例全配置/4109候选，binary TV/random_stall/DATAFLOW profiling开启，禁止FIFO自动扩容，无新综合/新质量/自动实现。官方RTL返回后须独立核对64dims、151936预览raw/key、完整ID/raw及token/score/CRC和有界FIFO报告；完整多状态/ABA仍未测。doc/design/V4PartialRTL.html已设入口，旧新557图内嵌脚本逐字不变且双组交互回归通过，浏览器视觉NOT_RUN。
- 暂停先查本轮SELECTOR_WORKFLOW或FULL_WORKFLOW真实父PID/创建时间与所属子PGID，停止父及所属树，保留所有失败/事务；不要用历史PID。仍显式zhangben@124.16.71.7:7626，不连默认7627容器、不操作板卡、不恢复wb/luyou/心跳。分段不是完整RTL资格，模型周期不是真实DDR或FPGA/整网decode速率；新200MHz/BSP/ELF均未运行。

## 2026-10-24 STHL阶段C完成：r3数值与HLS估计通过，未开始RTL（当前状态）

- 本轮有限阶段已完成并全部退出。事实源reports/partial_hw_20261024_r1/RESULT.md、RESULT.json、r3/CSIM_QUALIFICATION.json、r3/HLS_QUALIFICATION.json、r3/remote_hls/syn/report与生成Verilog。PROCESS_AFTER.json于2026-10-24T11:30:06Z核对STHL r1/r2/r3所属子进程组均空、ACTIVE.lock均不存在，110/116/123份冻结源/输入SHA及工具入口SHA不变；无自动RTL/实现/板卡下阶段。下方所有活动PID及“综合中”为历史，不重跑已完成阶段。
- r1正式Csim通过/综合共享AXI读失败、r2正式Csim通过/综合10.383ns和候选II14性能失败全部保留。r3为唯一针对性片上RAM调度变体：等价组合通道键、key_cache+ID_cache、扫描判断和AXI写回分开；仍d64/T4096、双W/B1024，所有FP32/penalty/特殊ID/canonical精算数值语义不改，没有在已打开组调参。
- r3官方Csim11有效调用（8真实+zero-hidden+ABA+生产模式）及6负向门控通过，完整actual与r1/r2逐字一致；独立脚本重核64通道、151936预览raw/key、候选ID及完整canonical raw、token/score/CRC。数值正确性不代表算法在所有题dense无损；新组原整体99.9465%、最低类别99.8381%结果保持，不新认证。
- STHL Linux Vitis_HLS2022.2 r3已真实综合完成，全部循环约束满足。HLS估计3.650ns（5ns目标/1.35ns uncertainty预算恰3.65ns，工具Fmax273.97MHz），预览II1、直方图II2、候选发出II2；radix函数上界4256342→1560505周期。资源BRAM18K444/1824、DSP179/2520、FF129572/548160、LUT52680/274080，两个master64位地址/128位数据。是HLS估计，绝不能标布线200MHz/实测FPGA decode速度或TTFT；top XML最小含错误返回、average非数据样本均值，不能换算token/s。
- doc/design/V4PartialHardware.html为离线原型结果页；V4Validation.html已加入口，原新旧557图/历史实验内嵌JSON逐字不变。10本地链接/零外部依赖、原双组557交互回归与所有源SHA/报告SHA通过，浏览器视觉NOT_RUN。当前研发规划V4_NEXT_TASKS_20261024.md已同步；根开发日志未改。
- 下一实际阶段是关键选择器、预览块、精算有界FIFO/AXI背压的分段RTL，再一次完整配置联合RTL及新200MHz系统资格。Csim软件stream峰值460320不是硬件FIFO128活性证明。后续继续用STHL2022.2，显式zhangben@124.16.71.7:7626，默认7627是助教容器不能连接。新系统需匹配2022.2 bit/XSA/BSP/ELF和新身份，不能混旧2021.1包。
- 当前未启动RTL/实现/新BSP/ELF，也不连接/探测/操作FPGA；板卡仍需另行确认独占。不恢复wb/luyou/心跳，不改v3.1/v4/v4b冻结/封存包和实验10失败结论。后续遵照新用户指令推进，不因历史EXECTUING/旧PID自动重启。

## 2026-10-24 STHL r2综合完成但时序未达标，r3有限调度变体执行（当前执行）

- r2 HLS真实完成并取回r2/remote_hls/全部report/生成Verilog、HLS_QUALIFICATION.json。两个master均64位地址/128位数据，预览主循环II1/发出预览II2，实际推断128拍预览读。资源BRAM18K145/DSP179/FF129878/LUT54342；时钟估计10.383ns，未达内部3.65ns预算，工具估计Fmax96.31MHz，绝不标200MHz通过或decode测速。
- 瓶颈明确在candidate_word_loop_candidate_lane_loop：同一meta AXI读→平局/计数→写回反馈，II14、关键路径10.383ns；radix直方图II2且每4个key重启小流水，未形成全局长流水。r2原源/失败性能结论保留，不启动完整RTL/实现。
- 用户“下一步”和指定STHL执行授权内，只新增一个针对性r3有限变体：experiments/partial_hw_20261024/r3/及reports/partial_hw_20261024_r1/r3/PLAN.json。原32位key全部缓存至banked片上RAM、4次长扫描、ID先写片上再分开AXI打包写回；通道排序改等价64位key/补码ID比较。额外key+ID数据容量624184B；仍d64/T4096、B1024、FP32树/penalty/特殊ID/canonical精算不变，r2接口预取修复保留。
- r3只按正式Csim→独立全数组及r1逐字对照→手动综合顺序执行，源/入口已冻结。真实状态在远端r3/ACTIVE.lock、*_WORKFLOW和日志，入口根目录bootstrap_r3.py（prepare成功stdout遗留R2字样，实际r3/REMOTE_ENV_LOCK和PLAN SHA才是版本证据）。r3若仍不达时序/II则保留结果停止重EDA，不无限扩扫。
- 仍显式SSH zhangben@124.16.71.7:7626，不能连默认7627容器；无板卡、RTL、实现、BSP/ELF操作，无wb/luyou/心跳。安全暂停须核对当前r3父/子/PGID，不得凭下方历史PID停止其他任务。

## 2026-10-24 STHL原型r1综合接口失败，r2完整Csim通过后综合中（当前执行）

- STHL正式HLS2022.2 r1 Csim11组/6负向及独立全数组复核通过，CSIM_QUALIFICATION.json为PASS；r1综合在预综合阶段真实失败HLS200-1013/984：DATAFLOW的gather_rows/candidate_policy同时读取meta总线。原日志/状态已取回reports/partial_hw_20261024_r1/r1_failed/，原源码/工程/结论不覆盖。
- 新隔离experiments/partial_hw_20261024/r2/与reports/partial_hw_20261024_r1/r2/PLAN.json：只在DATAFLOW前预取候选ID/history到不同片上RAM，额外数据容量35432B；参数/浮点/排序/输出算法不变。内部history_read_beats改报实际预取1187拍，不再将片上cache访问称外部读。新入口/派生diff/SHA全部冻结，旧110源仍不改。
- r2正式Csim11组/6负向通过，取回的每组actual与r1完整逐字一致，r2/CSIM_QUALIFICATION.json独立复核全部dims/151936 preview/key/ID/raw/token/score/CRC及ABA通过。2022.2 Csim软件stream峰值460320只表示无界CPU队列，不能证明实际FIFO128活性；后续必须RTL核验有界FIFO/AXI背压。
- 已手动启动STHL r2综合（启动返回父PID4537，严禁凭此旧快照操作）；真实状态以远端r2/ACTIVE.lock、csynth_WORKFLOW.json、csynth.log和/proc身份为准。构建.cache/p64_r2/csynth，不重跑r1或r2 Csim。根远程目录仍/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1；显式zhangben@124.16.71.7:7626，勿用默认助教容器7627。
- 只有综合真实Tcl PASS后取回XML/report/生成RTL端口做资源、II、时序估计与接口审计；不是200MHz实现通过或FPGA decode测速。无自动RTL/实现/板卡下阶段，不恢复wb/luyou/心跳，冻结/封存版本和实验10失败不改。用户暂停需远程核对本轮父/子/PGID后停所属树；本地STOP_REQUESTED仅阻止本地旧流程，不代表已停远程。

## 2026-10-24 d64/T4096最小原型，用户要求转STHL执行EDA（当前执行）

- 用户要求“下一步”，已准备新隔离experiments/partial_hw_20261024/及reports/partial_hw_20261024_r1/PLAN.json：d64/T4096、B1024、双W、顺序动态通道/FP32进位树/radix/原canonical候选精算；9夹具/11有效调用/6错误门控。精算源快照和派生副本只调整LOOP_TRIPCOUNT max151936→4110，原源文件/冻结包不改。新原型无已分配板卡ABI或IP版本，不导出旧身份。
- 本机HLS启动前因空闲内存低于3GiB被预检查拦住，未启动官方HLS。另用2021.1头文件和自带g++执行低内存native C++功能仿真，NATIVE_WORKFLOW为COMPLETE；11次/8真实+零hidden/ABA/生产模式及6负向检查全部通过。NATIVE_QUALIFICATION.json独立复核每次dims、全151936 preview/key、候选ID、候选完整raw及token/score/CRC；native不是官方Csim，更不是RTL。actual输出存native_actual，日志保留。STOP_REQUESTED阻止再次启动本地流程，写入前本轮native已自然完成。
- 用户明确“去STHL服务器，使用那里的vivado做”；按server-resources核对hostname=nvidia-Super-Server、用户zhangben/7626，可用约246GiB内存/3TiB磁盘，已有Vivado/Vitis_HLS2022.2。必须显式ssh -p7626 -lzhangben 124.16.71.7，默认ssh配置实指gpuCourse26/7627，绝不能误连助教容器。
- 已授权仅上传冻结源码/夹具/一份canonical权重到专属/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1；服务器逐位重建B1024 W并核SHA，路径文件只做本地D盘→Linux重绑定，其余110源/输入SHA核验；REMOTE_TRANSFER/REMOTE_ENV_LOCK记录。版本2022.2与本机2021.1分列，不覆盖历史结论，不安装软件/改服务/容器或其他任务。
- 远程入口experiments/partial_hw_20261024/remote_run.py，每次仅prepare/csim/csynth一个阶段，后续由主模型读真实完成标记并独立审计后手动启动；没有心跳/wb/luyou/自动下阶段。真实PID/进程组/工具命令/源SHA见远端reports/partial_hw_20261024_r1/ACTIVE.lock和对应*_WORKFLOW.json；本地日志与取回报告也存该目录。安全停止先核对本轮父/子PID及/proc身份，再停止所属树/组，保留构建，不用历史PID。
- 当前远程传输/官方Csim/HLS进度须读本轮真实文件，不能凭本段将其标完成。完整RTL/200MHz实现/BSP/ELF/板卡均NOT_RUN。不连接/探测/操作FPGA，不恢复wb/luyou/心跳，不改v3.1/v4/v4b冻结/封存或实验10失败结论，不在已打开质量组调参再认证。

## 2026-10-24 布局与Top-T阶段B完成，下一阶段为最小硬件原型（当前状态）

- 用户明确“按你的规划开始执行”，已完成有限离线阶段B。事实源module_14_lm_head_v4/reports/layout_topk_20261024_r1/PLAN.json、LAYOUT_PROOF、PL_DDR_LAYOUTS、NUMERIC_PROOF、TOP_T_PROOF、ACCESS_MODEL、COST_SUMMARY、INDEPENDENT_REVIEW、RESULT.md/RESULT.json。2026-10-24T14:39:23+08:00本机CIM查询成功、所属Python0、ACTIVE.lock不存在，无自动EDA下阶段。
- 固定主候选partial_dynamic_d64_T4096、备选partial_dynamic_d128_T1024、聚类C128/R4/L16384对照；不改参数/拟合/重新采集或重认证。现有整体及每类decode≥99%准入保持，数值逐位正确性不放宽；所有当前质量组已打开。
- 新隔离experiments/layout_topk_20261024/、scripts/assess_layout_topk_20261024.py只用CPU。B128/B1024两份完整分块W逆变换SHA等于canonical且padding零；24组8输入完整候选/raw/token/score/CRC匹配既有557证明，32组布局预览/精算、额外32组二进制进位流式相邻树预览逐位通过。16真实Top-T和16边界用例中heap/radix均与稳定排序一致；非法T与NaN/Inf拒绝。独立脚本复核全地址、40访问模型与保存数组PASS；不是第三方审查。
- 源文件确认已有v4为64位地址/128位数据，两master共用128位MIG（不是64位数据，也不是512位MIG）。模型按16B拍、256拍上限、4KiB边界计算；共享单W的候选精算8词组读取放大4.73–7.16倍，非实测AXI/DDR流量。两份W的B1024拟定arena528.75MiB、共享269MiB，均在0x400000000起2GiB窗口；是离线地址提案，未更新旧profile/descriptor/ELF/loader。
- 建议进入最小原型的路径：d64/T4096、双W+B1024、按通道原顺序FP32流式树、radix阈值优先/heap备选。d64预览请求75968→9536、padding80KiB、树栈28KiB；BRAM容量除法/乘法项/理想周期下界均不能冒充HLS II、实际资源或性能。CPU radix较快不用于证明FPGA更快。
- doc/design/V4LayoutTopK.html为可离线交互报告，V4Validation.html新增导航；原图及历史实验内嵌JSON逐字不变。13链接/64交互组合/16保存Top-T哈希及原557双组交互检查通过；浏览器视觉NOT_RUN。doc/design/V4_NEXT_TASKS_20261024.md已重写为当前真实阶段，旧规划快照保存在本轮ROADMAP_BEFORE_STAGE_B.md。
- G:/Xilinx/Vitis_HLS/2021.1/bin/vitis_hls.bat可见，尚未启动EDA。下一实际任务是新隔离d64/T4096最小Csim/HLS内核，冻结入口后顺序验证动态通道、流式预览、radix/候选及canonical精算；当前Csim/HLS/RTL/新200MHz/BSP/ELF均NOT_RUN。板卡仍需另行确认连接/独占；不连接/探测/操作FPGA，不恢复wb/luyou/心跳，不改v3.1/v4/v4b冻结/封存包或实验10失败结论。下方旧流程均为历史，不重跑已完成557或本轮。

## 2026-10-24 全557配置新题补充评价与配对GPU图完成（当前状态）

- 本轮全部流程完成退出，PROCESS_AFTER.json于2026-10-24T13:32:34+08:00核对所属进程0、根/benchmark两ACTIVE.lock均不存在。事实源module_14_lm_head_v4/reports/sparse_quality_all557_20261024_r1/PLAN.json、CACHE.json、QUALITY.json、GPU_COUNT_ENTRY/QUALIFICATION、benchmark/RESULT.json、INDEPENDENT_REVIEW.json、RESULT.md/RESULT.json、PAGE_REVIEW.json。下方进行中及旧PID为历史，不重跑旧入口，无自动EDA/板卡下阶段。
- 全部557点与原校准清单ID/参数逐项一致：23聚类、33低秩、432融合、16部分通道、18完整桶、18学习桶、16LSH、1dense。复用同一已打开新1000题/15956预测/14956decode/零排除，未调参/重拟合/重新采集。后追加551点为补充分析，首轮标签前冻结6点身份不改；原6和r1已完成120点的逐步hits/K及报告全部一致。
- 新组整体及每类decode≥99%：聚类9/23、低秩17/33、融合321/432、部分通道8/16、完整桶2/18、学习桶2/18、LSH0/16、dense1。桶和学习桶的通过点均为全词表端点，不能当作有效稀疏收益；各点真实K、回退及原校准结果分别保留。不追溯修改旧实验的门槛或失败结论。
- 同一运行环境全部557点驻留，原4＋新4固定输入交错，3预热＋每输入30测量，133680计时＋660dense哨兵完成。两组分别每配置120次，独立重算均值/median/P95/输出率与case摘要。4456组8输入完整CPU/GPU候选/raw bits/输出证明及额外8decode状态×557=4456组NumPy候选重建通过；全部数组/分项计数/整题统计/Bootstrap区间/原始计时/来源SHA独立复核PASS。
- 未计时质量计数为GPU精确整数OR/LUT popcount，逐批实际读入158份缓存累计全文件SHA一致；首2真实状态×556非dense配置、9字节边界、120旧完整数组、6原完整数组均通过。原CPU统计主动停止的r1日志/数组/evaluation_r1_preserved保留；缓存只用于质量，计时每次完整重算，不冒充推理加速。
- doc/design/V4Validation.html#gpu-summary新旧两组各557点，均用本轮配对速度；切换保留筛选和选中配置、共享坐标范围，可单看首轮6点。两组分别列官方来源链接/冻结版本/划分/问题与decode数/测试边界/CSV；代码MBPP→DS-1000的来源变化明示。历史557和独立6点数据均未覆盖，首轮页面存档doc/design/V4Validation_first6_20261024.html的SHA与原PAGE_REVIEW一致。
- 35来源/证据链接、1114点的CSV/原始记录路径、内嵌数据/JS语法、DOM替身交互/历史日志快照一致性检查PASS；浏览器视觉NOT_RUN（打开仅queued）。GPU四固定输入M14等效输出率不是整批语料/整网decode/TTFT或FPGA预测。新板卡/HLS/RTL/200MHz均NOT_RUN；不连接/探测/操作FPGA、不恢复wb/luyou/心跳、不改v3.1/v4/v4b冻结/封存。任务结束，后续研发等新指令。

## 2026-10-24 用户授权全部557配置对应补测（当前执行）

- 用户明确“把所有的配置都跑一下，和原校准集的配置对应”，覆盖此前仅六配置范围限制。新隔离reports/sparse_quality_all557_20261024_r1/PLAN.json已冻结与原557清单逐项一致的ID/参数和源码SHA；复用已打开新1000题/15956预测/14956decode，不重新采集、不拟合/调参。此轮标为补充分析，不改首轮六点独立验证身份或旧实验结论。
- 人工分阶段入口scripts/run_sparse_quality_all557_20261024.py --phase freeze/cache/evaluate；当前cache，日志reports/sparse_quality_all557_cache_20261024_r1.log。实际阶段见新报告PROGRESS/ACTIVE.lock及CIM，旧六点完成状态不代表本轮完成。缓存保存真实候选位图，未用于测速；cache完成后人工评价全部557，再benchmark_sparse_quality_all557_20261024.py。
- 12:30 cache已完成158份完整成员位图。评价实际使用scripts/evaluate_sparse_quality_all557_fast_20261024.py：保留冻结原入口，只将反复扫描问题组字符串的统计改为预索引整数计数；先验证原6报告及全真/全假/随机3组与原recall_report逐字段完全一致，入口/来源见EVALUATION_REPORT_OPTIMIZATION_ENTRY.json。评价日志reports/sparse_quality_all557_evaluate_20261024_r1.log；源参数/候选/Bootstrap种子及公式均不变。
- 原CPU逐配置计数完成120点后按STOP安全边界退出（r1日志/数组与evaluation_r1_preserved保留），改人工启动evaluate_sparse_quality_all557_gpu_counts_20261024.py，日志sparse_quality_all557_evaluate_20261024_r2_gpu_counts.log。按256预测一次读取158份位图块，在GPU以精确整数OR/LUT popcount计数并复用给557点；实际读入块累计全文件SHA，先校验字节边界、每点首2状态，并在最终与全部r1完整数组和原6完整数组对照。此优化仅未计时质量评价，原冻结源、缓存/参数与测速完整重算逻辑不变；实际进度以新PROGRESS/GPU_COUNT_ENTRY/QUALIFICATION为准。
- 12:44全557 QUALITY.json完成；GPU_COUNT_QUALIFICATION确认120旧完整数组/原6完整数组及158文件SHA一致，9字节边界与556点首2真实状态通过。新组整体及每类≥99%：聚类9/23、低秩17/33、融合321/432、部分通道8/16、完整桶2/18与学习桶2/18（均全词表端点）、LSH0/16、dense1。这些是补充结果，尚待独立全复核。
- 已人工顺序启动benchmark_sparse_quality_all557_20261024.py；实际阶段/PID看benchmark/PROGRESS.json、benchmark/ACTIVE.lock及reports/sparse_quality_all557_benchmark_20261024_r1.log，根QUALITY_COMPLETE不代表任务结束。不重启计时入口，仍无自动后续任务。补充未计时统计源与r1停止记录已保留。
- 测速拟全部557同一运行环境、旧4＋新4固定输入、每输入3预热＋30实测，133680计时＋dense哨兵；分开生成两组120次/配置摘要。每次完整重算筛选/排序/并集/精算/policy/输出，候选缓存只作未计时质量分析。完成后图中新旧两组均557点对应，原六点/历史557结果保留。
- 安全停止新报告目录STOP_REQUESTED，测速阶段benchmark/STOP_REQUESTED；等batch/config/call边界退出，核对实时进程，勿用历史PID。无后台自动下阶段，不恢复wb/luyou/心跳，不运行EDA/板卡、不改封存/冻结资产。约50GB候选缓存空间已核对D盘有约159GiB空闲。

## 2026-10-24 新1000题独立6配置验证与双标签图完成（当前状态）

- 全部流程已退出；PROCESS_AFTER.json于2026-10-24T11:13:26+08:00核对所属Python进程0、ACTIVE.lock不存在。根PROGRESS最后benchmark_complete仅是阶段快照，不重跑旧入口；无自动EDA/板卡下阶段。
- 事实源module_14_lm_head_v4/reports/sparse_quality_20261024_r1/SELECTION_LOCK.json、QUALITY.json、INDEPENDENT_REVIEW.json、benchmark/RESULT.json、benchmark_calibration_control/RESULT.json、TIMING_COMPARABILITY_REVIEW.json、RESULT.md/RESULT.json。标签前冻结四候选＋两控制；新题1000（中400/英250/DS-1000代码100/数学250）、15956预测/14956decode/零排除，历史9份问题组含v4b最终组精确去重，未调参或扩点。
- 新decode：聚类C128/R2/L16384漏150，98.9971%，最低代码98.2667%，99%门槛FAIL；原R4漏83，99.4450%，最低代码99.0000%，PASS。动态d64/Top4096漏8，99.9465%，最低英文99.8381%，PASS；d128/Top1024和d128/Top4096均零漏选/全输出一致，PASS。dense为定义控制。整体及每类≥99%，不是闭环/任务正确率；零观察不等于总体无损，旧实验门槛与失败不追溯修改。
- canonical原8步完整raw/policy位复现、质量四类24组证明、新4输入24组及旧输入控制24组完整候选/raw/输出证明、额外48组独立CPU重建、全部6逐步数组/门槛/计时SHA复核PASS。GPU新/旧输入各720计时＋各30dense哨兵，权重常驻、完整Eager M14，非整批语料/整网decode/FPGA。
- 新输入GPU参考：R2约478.76、R4约408.59、d64/T4096约527.99、d128/T1024约479.17、d128/T4096约444.81、dense约67.73次/s。旧输入在本轮6点方式下也显著更快（510.24/437.31/546.95/508.28/481.00/67.78），所以不能将相对原557轮绝对速度差归因于新数据或算法；运行条件因果未定位。原557点结果保留，不据此外推硬件收益。control RESULT.report字段沿用新质量元数据，不是校准重评价；配对图横轴从旧校准事实源取。
- doc/design/V4Validation.html#gpu-summary默认新独立集6点，可切换原校准集557点；勾选“仅显示两组共同的6配置”时旧集改用本轮原输入对照计时。两份数据各列官方来源链接、冻结版本、问题/步数、划分/去重、prompt和GPU条件；代码从MBPP换DS-1000的分布变化明确提示。31来源/证据链接、JS语法/静态数据/DOM替身交互与历史日志快照一致性PASS，浏览器视觉NOT_RUN（open_in_codex仅queued）。
- 本授权任务完成；下一步仅待布局/Top-T与FPGA适配评审的后续指令，不自动HLS/RTL/EDA/板测，不连接/探测/操作FPGA，不恢复wb/luyou/心跳，不改v3.1/v4/v4b冻结/封存与实验10失败结论。下方进行中为历史。

## 2026-10-24 用户授权新独立质量与双数据集汇总图（执行中）

- 入口module_14_lm_head_v4/data/sparse_quality_20261024/EVALUATION_ENTRY_LOCK.json已在标签前冻结；四候选cluster_C128_R2_L16384、partial_dynamic_d64_T4096、partial_dynamic_d128_T1024、partial_dynamic_d128_T4096，控制原cluster_C128_R4_L16384及dense，共6点。整体及四类decode≥99%，全数值正确性保持逐位；不在新组调参或扩点。
- 新文本1000题（中400/英250/DS-1000代码100/数学250），排除原train/cal及全部旧最终组，包括v4b最终组；PRELABEL_REVIEW.json确认9份历史分组SHA及零精确重叠。新来源版本/分组/去重见data/sparse_quality_20261024/MANIFEST.json；是否已打开标签须看本轮FINAL_LABEL_ACCESS和实际collection，冻结快照false不是实时状态。
- 当前人工启动scripts/collect_sparse_quality_20261024.py，输出data/hidden_sparse_quality_20261024，日志reports/sparse_quality_collect_20261024_r1.log；真实阶段看reports/sparse_quality_20261024_r1/PROGRESS.json及ACTIVE.lock/本轮CIM，勿凭历史PID。采集后人工顺序evaluate_sparse_quality_20261024.py、benchmark_sparse_quality_20261024.py，随后独立审计/双标签图；没有自动续跑器。
- 暂停在reports/sparse_quality_20261024_r1/STOP_REQUESTED，采集prompt边界/评估prediction边界/测速call边界退出，核对实时进程；源/参数不可直接改后续跑。后续页面新独立6点与旧校准557点标签切换，分别说明公开来源链接、统计总体及4固定输入GPU速度。不测板卡/EDA，不恢复wb/luyou/心跳，不改冻结包和实验10原失败结论。

## 2026-10-24 用户调整后续规划：独立质量优先，召回门槛99%

- 用户明确独立质量验证应提高优先级，召回率99%可接受。后续规划已改为先冻结有限候选及新语料/入口，再做新独立质量；按整体及中/英/代码/数学各类decode≥99%作为分项执行约束，取消上一版规划建议的99.9%及全部校准预测零漏选硬门槛。逐位数值正确性不放宽，旧实验门槛/结果不追溯修改。
- 详见doc/design/V4_NEXT_TASKS_20261024.md：新质量→通过者布局/Top-T评审→选一个硬件点→Csim/HLS→RTL/200MHz→另行独占安排后的板测。本次仅调整规划，未启动新实验/EDA/板测；候选短名单尚待正式冻结，不使用已打开最终组调参再认证。不恢复wb/luyou/心跳，不改冻结/封存资产。

## 2026-10-24 新增4类稀疏方案GPU研究完成（当前状态）

- 本轮所有GPU/CPU作业已完成退出，根和benchmark/的ACTIVE.lock不存在；PROCESS_AFTER.json核对所属Python进程0。下方进行中、父PID及阶段安排均为历史，不重跑旧入口。无自动EDA/板卡/监控下阶段。
- 事实源module_14_lm_head_v4/reports/sparse_methods_20261024_r1/RESULT.json、RESULT.md、benchmark/RESULT.json、INDEPENDENT_REVIEW.json（位于benchmark/）、SELECTOR_REVIEW.json、ANALYSIS.json、STAGE_PROFILE.json、REPORT_REVIEW.json。68新点（16部分通道/18完整桶/18ridge桶/16LSH）加489旧点，同轮557点66840次计时+660dense哨兵、2228组完整数值证明、额外544组独立CPU校准K/命中核对、2880次分阶段计时及557点计算模型/页面检查完成。
- 动态部分通道有6点各类校准decode≥99%、4点≥99.9%；非全桶端点的其他三家族本轮未找到各类≥99%配置。d128/Top1024：1/4775漏选、99.9791%、最低英文99.9149%、GPU129.58次/s；同轮dense65.85、原C128/R4/L16384聚类143.10。均为原320校准题和4固定输入Eager参考，不是新独立质量、整网decode或FPGA预测。
- d64/Top4096约13.41M乘法项/25.57MiB主逻辑读取；d128/Top1024约20.38M/38.87MiB。动态列式副本加行式W至少519.31MiB，超旧320MiB arena；逻辑预算不等于实际AXI或时延。未来需评审布局、TopT及新独立质量，尚未选择硬件发布参数。
- doc/design/V4Validation.html#gpu-summary已扩展557点、4新模式及研究11–14筛选；doc/design/V4SparseMethods.html含逐方案原理/参数/来源/完整负结果/重点比较/资源与访存适配分析。静态链接/数据/JS与DOM替身交互测试PASS，浏览器视觉NOT_RUN。根开发日志历史快照未改。
- 原evaluate的NumPy桶索引float提升失败保留，resume_lsh_r2仅显式uint32续完16点，前52数组SHA不变；不重复旧evaluate。所有已打开最终组未用于本轮拟合或重新认证。v3.1/v4/v4b冻结/封存及实验10质量失败不改；不连接/探测/操作FPGA，不恢复wb/luyou/心跳。本轮新方法HLS/RTL/200MHz/BSP/ELF/板卡均NOT_RUN。


## 2026-10-24 用户授权更多稀疏方案GPU研究（当前任务）

- 当前prepare及68点校准已完成；原evaluate在52点后因NumPy uint64+int64将哈希索引提升float64失败，失败日志/PROGRESS已保留。单独scripts/resume_sparse_lsh_calibration_20261024.py只用显式uint32补完16点，resume_lsh_r2/ENTRY_LOCK绑定前52点SHA；原PLAN/参数/算法源未改，不重复原evaluate。
- 正在人工启动的scripts/benchmark_sparse_methods_20261024.py有限557点同轮GPU流程。真实阶段/父PID看reports/sparse_methods_20261024_r1/benchmark/PROGRESS.json、ACTIVE.lock和sparse_methods_benchmark_20261024_r1.log（研究根目录PROGRESS的calibration_complete不是测速终态）。只在本轮benchmark/STOP_REQUESTED触发安全call边界停止；无自动EDA或板卡下阶段。
- 用户要求更多稀疏方案的GPU结果进入总览，再分析计算量/FPGA适配性后决定硬件方案；本轮不连接/探测/操作板卡、不运行EDA、不恢复wb/luyou/心跳。仅本机离线研究，原v3.1/v4/v4b冻结资产与实验10质量失败不改。
- 新隔离实现experiments/sparse_methods_20261024/sparse_methods.py；手动入口scripts/run_sparse_methods_20261024.py --phase prepare/evaluate；输出reports/sparse_methods_20261024_r1/。PLAN.json预冻结68点：16部分通道/18全支持倒排桶/18训练集ridge学习桶路由/16角度及MIPS多表哈希，4个全桶端点包含在68点内。只用原train1500拟合和原calibration320评价；不打开最终组或宣称独立认证。
- 真实阶段/PID见本轮PROGRESS/ACTIVE.lock及sparse_methods_prepare_20261024_r1.log；勿用历史PID或重跑已完成阶段覆盖文件。安全暂停在本轮目录及其benchmark/创建STOP_REQUESTED，等batch/config/call边界退出并核对进程；无自动后续作业。预备完成后人工顺序运行评价，再全部489旧+68新=557配置统一GPU补测，拟66840次计时+660dense哨兵，禁止缓存预览/候选冒充推理速度。
- 新报告必须区分候选召回/数值逐位正确、GPU参考速度/整网decode、逻辑读取模型/实际AXI及FPGA资格。全量W仍存；新索引/列式预览/桶元数据计入容量，不自动启动HLS/RTL或上板。

## 2026-10-24 实验1/8/9/10统一GPU汇总已完成（当前状态）

- 有限入口benchmark_summary_20261024.py已完成并退出，ACTIVE.lock不存在；事实源module_14_lm_head_v4/reports/gpu_summary_20261024_r1/RESULT.json、INDEPENDENT_REVIEW.json、RESULT.md。489去重配置（23聚类/33低秩/432融合/1dense），1956组完整数值证明、58680次统一计时、570次交错dense哨兵完成，原覆盖数组/分项计数/全部原始计时/SHA独立复核PASS。下方进行中说明为历史，不重启已有入口。
- V4Validation.html在10组实验报告上方新增同轮召回率—GPU输出率交互图，全部主图横轴用原320校准题/4775decode；历史独立质量在点详情单列。每配置4原校准夹具、每类3预热+30测量；无新最终标签、调参、锁点或发布。旧实验速度保留，不混接旧轮次。
- 页面仅展示离线数据；CSV/摘要/原始证据可追溯。纵轴是M14 GPU Eager等效输出率，不是整网decode/FPGA/TTFT；原实验10质量失败和v3.1/v4/v4b冻结/封存结论不变。不连接/探测/操作FPGA，不恢复wb/luyou/心跳，不自动EDA或新实验。


## 2026-10-24 用户授权实验1/8/9/10全配置GPU汇总（当前任务）

- 用户要求在V4Validation.html的10组实验报告上方绘制召回率—decode速度汇总，并补齐缺测。新独立入口module_14_lm_head_v4/scripts/benchmark_summary_20261024.py；输出reports/gpu_summary_20261024_r1/，489去重配置（23聚类/33低秩/432融合/1dense），统一4校准夹具、3预热+每类30次，58680次计时，另有交错dense哨兵。只读原校准召回，不打开新最终标签、不改原实验结论或锁点。
- 最新阶段/PID以本轮PROGRESS.json、ACTIVE.lock、gpu_summary_20261024_r1.log及实时进程核对；不凭进程存活宣称完成。安全暂停在本轮输出目录创建STOP_REQUESTED，等call/config边界退出并核对父树；不得直接重跑已有PLAN入口覆盖旧记录。无后续EDA/板卡自动阶段。
- 纵轴仅为完整M14 GPU Eager等效输出率，不是整网decode/FPGA/TTFT；横轴统一320校准题4775decode。历史独立质量在详情单列，不混为相同评估组。不连接/探测/操作FPGA，不恢复wb/luyou/心跳，不修改v3.1/v4冻结/封存资产及实验10质量失败结论。

## 2026-10-23 v4b首轮CPU/GPU及新1000题质量完成（当前状态）

- 有限流程于2026-10-23T17:34:44+08:00完成并退出；实时CIM复核无本任务父/子进程，ACTIVE.lock不存在。事实源module_14_lm_head_v4b/reports/quantization_20261023_r1/RESULT.json、RESULT.md、FINAL_QUALITY.json、FINAL_INDEPENDENT_REVIEW.json、QUALITY_SEQUENCE.json。下方v4b进行中、未锁定、未打开标签及PID均为历史，不能据此重启作业。
- 32RTN＋4GPTQ＋4AWQ-style新配置/5095校准预测、160组四类完整raw CPU/GPU证明、12预筛K点及720次同轮真实packed GPU计时完成。按校准零错选/漏选和逻辑读取量预先锁定直接RTN W12/G896/A、RTN W4/G128/S＋K512 BF16精算，不按GPU速度或新问题换点。
- 全新1000题（中400/英250/DS-1000代码100/数学250）15948预测/14948decode/零排除，一次性最终评估完成。直接W12错选3（中文2/英文1），decode一致率99.9799%；W4＋K512精算0漏选/输出全一致。两点整体及每类decode≥99.9%通过；整题decode全一致997/1000、1000/1000。独立SHA/来源/旧组零重叠/保存数组/计时复核PASS。固定dense轨迹条件一致性不等于闭环生成、任务正确率或数学无损。
- 同轮GPU独立M14等效输出率BF16约669.76、W12约801.82、W4＋K512约534.57次/s。不是旧Eager绝对速率对比，也不是FPGA/整网decode/TTFT。逻辑读取预算W12约204.02MiB、W4精算约75.06MiB，非实际AXI流量；W4同时存BF16与packed W已超旧320MiB arena。
- 实验页doc/design/V4bValidation.html已同步真实结果，静态数据/本地链接/JS语法通过；本修订浏览器file://观察受工具URL策略拒绝，无绕过，视觉检查NOT_RUN。新内核/身份/布局仍待开发，整数MAC/残差/旋转/NLL/闭环及Csim/HLS/RTL/200MHz/BSP/ELF/板卡均NOT_RUN。下一步评审硬件可行性，此有限流程无自动EDA下阶段。
- 最终标签已打开，不得在该组调参再认证。继续不连接/探测/操作FPGA、不恢复wb/luyou/心跳、不改v3.1/v4冻结/封存包或实验10失败结论。工程父版本仍为已上板v3.1，与v4并行；未来融合另立实验。

## 2026-10-23 v4b首轮校准完成，有限新质量流程执行中（当前状态）

- reports/quantization_20261023_r1/已完成32点RTN＋4GPTQ＋4AWQ-style新点（4RTN控制复用），每点真实packed W、完整解包位核验、四类全raw CPU/GPU证明及5095预测校准。仅RTN_W12_G896_A通过全部校准预测零错选门槛。12个W4/W8-G128预筛K点均校准零漏选（W4最差dense赢家rank=7，仍按预声明最小K512，不缩K）。原v3.1归档8步和5095dense标签/score bits复现通过。
- 已手动启动scripts/run_quality_sequence.ps1 -Run这一份有限CPU/GPU流程：最终独立数组复核→真实packed GPU全管线证明与同轮计时→按门槛/读取量锁点→一次性新1000题采集与质量评估。非wb/监控/心跳；无重试、无EDA自动下阶段。真实父PID/创建时间与阶段见QUALITY_SEQUENCE.json，当前child见ACTIVE.lock/PROGRESS及分阶段log，勿用历史PID。
- 新题文本中400/英250/代码100/数学250已预留并tokenizer预检33–882 tokens；代码改用官方DS-1000提交b39aab71da6d23ef8d3cac59a7c5f834516ab334，origin-family及规范化/trigram去重。MBPP仅剩10非few-shot未用题，不能凑旧题认证。数学可来自未用GSM8K官方train/test，和本项目实际训练分组零重叠。来源/许可/SHA在data/final_quality_20261023；当前是否已打开标签必须看FINAL_LABEL_ACCESS与真实collection manifest，reservation/ENTRY中的false只表示冻结时尚未打开。
- 暂停先核对QUALITY_SEQUENCE本轮父PID/创建时间并停父树，防止启动下一阶段，再核对所属GPU child；或创建reports/quantization_20261023_r1/STOP_REQUESTED等待batch/prompt边界退出。源文件/参数/语料改变不能直接续跑；保留全部失败。禁止在已打开最终组调参再认证。
- 不连接/探测/操作板卡，不恢复wb/luyou/心跳，不改v3.1/v4冻结包。v4b新HLS/RTL/实现/BSP/ELF/实板均NOT_RUN；数值正确性、最终质量与工程资格分别记录，GPU结果不预测FPGA速度。

## 2026-10-23 用户授权开展v4b离线实验（当前新方向执行状态）

- 用户明确“可以开展v4b方向的实验”，解除下方仅调研/未授权执行限制。工程父版本仍是已上板v3.1，v4并行且冻结资产不改；不连接/探测/操作FPGA、不启用wb/luyou/心跳。
- 新入口module_14_lm_head_v4b/scripts/run_quantization.py，手动分阶段preflight→rtn；报告reports/quantization_20261023_r1/，PLAN/ENTRY_LOCK冻结32点及来源。暂停创建该目录STOP_REQUESTED，等batch/config边界并核对最新CIM/ACTIVE.lock，勿用历史PID。没有自动续跑器。
- 真实preflight已完成：canonical W/模型/基线快照及train/calibration NPZ身份通过；原归档8步完整raw/policy SHA、token/score/CRC、四类完整CPU/GPU raw及32格式边界通过；5095校准预测/4775decode的token和score bits全部重算逐位一致。事实源Q01_BASELINE.json、DENSE_CALIBRATION.json。
- 正在执行32点RTN（W12/8/6/4 × G32/64/128/896 × 对称/非对称），每点保存真实packed W及完整解包、四类全raw位证明和5095预测结果；进度看PROGRESS/points/*/RESULT及rtn_r1.log。GPU评估器用本机Torch自带NVRTC保持v3.1 FP32算术；作业耗时不是推理benchmark，不能与旧Eager速率比较成加速。
- 后续GPTQ/AWQ-style head-only及量化预筛按计划推进、各阶段另冻结新入口。所有旧holdout与实验10新组保持只作历史诊断；尚未打开v4b最终标签、未开展新EDA/板测。v4b身份/布局/硬件仍待锁点后开发。

## 2026-10-23 v4b量化并行研究设计完成（新方向，未执行实验）

- 用户要求基于已上板v3.1建立量化方向v4b，与现有v4并行，未来融合另评审。本次只完成调研/论文收集/实验设计；没有授权自动开始量化测试、GPU、EDA或板卡流程。
- 论文目录doc/paper/lm_head_quantization/收录16篇原始PDF、manifest/SHA/BibTeX/阅读笔记；实验页doc/design/V4bValidation.html含12组计划，机器数据module_14_lm_head_v4b/experiments/quantization_study/PLAN.json。所有新实验NOT_RUN，最终1000题来源/执行入口尚未冻结。
- module_14_lm_head_v4b/baseline/v31保存原v3.1源码/头及小型身份/验收快照；SOURCE_LOCK.json记录9份快照及原package9成员SHA核验。v4只提供只读canonical模型身份，不是工程父版本；未复制selector或旧bit/XSA/ELF，v4b内核/descriptor/IP身份仍待开发分配。
- 优先基线复现→32点RTN→GPTQ/AWQ head-only→量化预筛精算→packed成本→锁点新质量→新硬件资格→未来独占板测；条件扩展不能自动扩扫。Qwen tied embedding须克隆独立输出层；直接量化golden正确性与BF16质量分别验收。
- 精算路径同时保留packed及BF16 W可能超过旧320MiB arena，须另立v4b布局；旧已打开问题组不作新认证，不改v3.1/v4封存、冻结或实验10质量失败结论。不连接/探测/操作FPGA，不恢复wb/luyou/心跳。后续等用户新的实验指令。

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

## 2026-10-23 实验10融合调参与全部非板卡测试（当前最高优先级，执行中）

- 用户要求基于实验8/9设计融合实验10并完成板卡之外的所有测试；已授权本机校准/GPU、新独立问题质量和选定配置Csim/HLS/RTL/200MHz实现/离线配套。用户明确G盘已连接、板卡暂未连接；不得连接/探测/操作FPGA，不恢复wb/luyou/心跳，不改冻结v4/IP/private_package或v2/v3/v3.1封存。
- 已在reports/fusion_exp10_20261023_r1/PLAN.json预先冻结432点：C64/128/256/512，R2/4/8，L4096/8192/16384，r32/64/128，T2048/4096/8192/16384。原train资产不重拟合，只用calibration320/4775decode；所有点都实际位图并集/真实K/交集，不用K上界替代。
- 当前入口scripts/fusion_experiment10_20261023.py --phase cache/scan（手动顺序，无续跑器）。缓存完成，scan真实进展看PROGRESS、CALIBRATION.partial及fusion_exp10_scan_20261023_r1.log，不按旧PID/running猜进度；停止标记放本轮reports目录STOP_REQUESTED。
- 入围要求整体/分项decode≥99.9%，且全部5095校准预测零漏选、无fallback、K/320MiB预算合格。按实际K主要逻辑读取量选top5及每rank最优（≤8），再同轮GPU比冻结融合、单分支及dense；GPU速率不作为FPGA预测。选择锁定前不产生新测试标签，不无限扩扫。
- 全新1000问题只预留文本：中400/英250/代码64/数学286；排除全部旧保留组和快照。64为剩余HumanEval，数学补至286在标签前固定；不执行代码解答。data/fusion10_quality_20261023/MANIFEST.json及tokenizer预检为事实源。新参数/实现/入口锁定后一次性评估；失败保留，不在新测试上调参重认证。
- scripts/prepare_fusion10_hardware_20261023.py将从冻结源码派生独立experiments/fusion_exp10_20261023/；仅该目录改变编译期参数、私有descriptor版本/身份、测试fixtures和token输出名以避免旧CoSim包装命名冲突。现在仍未生成/验证硬件，不继承旧RTL/实现结论。
- EDA工具已真实重新确认G:/Xilinx/Vitis_HLS/2021.1及Vivado/2021.1入口可读；早期缺盘问答已解除，无需再问板卡。重EDA顺序运行，先核对新任务状态不重复启动，全部测试按真实结果更新实验页和续办。

## 2026-10-23 实验8/9首轮及12联合点离线阶段完成（当前最终状态）

- 本轮全部作业已退出：23聚类+21低秩首轮+12低秩联合新配置完成校准，首轮5400+联合1680=7080次GPU计时，180+56组完整候选/raw/token/score/CRC证明及64组preview/距离数组证明通过。两份逐步数组/原始计时/来源SHA独立脚本复核PASS，无后台续办，不启动新独立测试或板卡。
- 事实源：reports/hyperparameters_20261023_r1/与reports/hyperparameters_joint_20261023_r1/各PLAN/RESULT/INDEPENDENT_REVIEW、逐点coverage和timing。页面doc/design/V4Validation.html#cluster-hyperparameters及#lowrank-hyperparameters含首轮并列折线和独立联合曲线；新独立问题/新RTL/FPGA/TTFT仍NOT_RUN。
- 仅聚类训练支持集上限99369词，2中文decode赢家不在其中；全簇/全列表上限中文99.8333%，因此本配方下仅调C/R/L无法达到每类99.9%校准门槛，未盲做联合扩扫。不能推断所有聚类方法均无效。
- 低秩首轮r896/T16384零漏选但GPU45.91次/s慢于同轮dense66.31。12联合点最快合格r256/T98304：decode零漏选、18.617ms/52.93次/s；同轮dense15.111ms/66.13次/s。r256/T65536虽只漏3次，英文2/1175使分项门槛失败；r896/T1漏9次，不能把满rank BF16预览当dense精确排名。
- 这只是校准搜索+4固定输入FP32 Eager参考（预览按32768行分块），不是优化生产GPU或FPGA性能预测。旧GPU基准使用不同预览实现，不能把绝对速率变化当生产回退；两个新轮次各保留同轮dense与原基线，曲线不混连。
- 尚未找到本次有限扫描中同时通过校准分项门槛且在此GPU参考实现中快于同轮dense的单方案；不改冻结selector/参数/private_package，不使用已打开测试组再认证。下一步应评审训练支持集候选来源、筛选预览成本及实际硬件可行性，再决定新方法/锁点和新最终问题组；不自动无限扩扫。
- r≥256因子加W已超过现320MiB arena；任何后续硬件方案需新容量/布局、可变rank算术、HLS/实现资格。仍不连接/探测/操作FPGA，不恢复wb/luyou/心跳，v2/v3/v3.1封存不改。原routing.py工作文件改动保留，本轮用历史SHA一致隔离配方。

## 2026-10-23 首轮44点完成，低秩12联合点执行（当前最新）

- 首轮reports/hyperparameters_20261023_r1/已完成23聚类+21低秩校准、64全数组CPU/GPU算术证明、180完整候选/raw/token/score/CRC证明、5400次交错GPU计时（含120次同轮dense），独立数组/原始计时/SHA复核PASS。不是新独立测试或FPGA结果。
- 聚类全部训练raw_top256/winner/特殊ID仅覆盖99369词；全簇/全列表仍漏2中文词（120718、49412），中文99.8333%，没有点通过整体及每类99.9%校准门槛。支持集上界已直接由train并集复核，所以本配方不盲做C/R/L联合扩扫；改变候选来源或fallback属于新方法。
- 低秩r896/T16384校准零漏选但同轮GPU约45.91次/s，慢于dense约66.31次/s；因素含固定FP32 Eager实现，不向FPGA推断。按原计划锁定12联合点：r128/T98304,131072；r256/T32768,65536,98304；r512/T32768,65536；r896/T1,256,1024,4096,8192。另保留原r128/T16384和dense控制。
- 新入口scripts/run_lowrank_joint_20261023.py，输出reports/hyperparameters_joint_20261023_r1/。联合校准已完成12新点+1原基线，当前benchmark单独顺序运行（hyperparameters_joint_gpu_20261023_r1.log）；阶段看新PROGRESS，不重启首轮或旧任务。
- 当前安全暂停标记应放联合输出目录STOP_REQUESTED，不是首轮目录；核对最新PID/日志后等待batch/round边界退出。无自动续跑器。联合GPU准备56组完整候选位证明、1680次计时（12新点+2控制）；未完成前不标测速通过。
- 仍只用旧train/calibration，全部独立测试均不打开；不操作/探测板卡，不恢复wb/心跳，不改封存/冻结/private_package。尚无生产参数更新或部署结论。

## 2026-10-23 用户启动实验8/9（当前最新，覆盖下方未执行计划）

- 用户明确“开始做我们新加的实验8和实验9”，主模型顺序执行本机离线训练/校准及GPU参考测速。仍暂不上板，不连接/探测/操作FPGA，不恢复wb/luyou/心跳，封存资产和冻结selector不改。
- 新入口module_14_lm_head_v4/scripts/run_hyperparameter_studies_20261023.py；输出reports/hyperparameters_20261023_r1/，状态看PROGRESS.json、PLAN.json、各partial/完成JSON及真实日志，不能仅凭PID判断进展。首轮23个聚类和21个低秩配置；新最终测试和联合扩扫另在选型锁定后进行。
- 首次准备进程见hyperparameters_prepare_20261023_r3.log（此前r1/r2为导入预检失败，均未训练）；独立prepare阶段完成后才手动顺序运行evaluate，再benchmark，无自动续跑器。先核对状态，不重复启动。
- 发现reference/routing.py训练函数名被改动，保留原文件；本轮隔离副本reference/hyperparameter_router_recipe.py通过历史原始SHA6e2b4646...匹配。SOURCE_AUDIT.json记录差异，已有冻结selector源文件审计全匹配；不得将本轮隔离使用解释为原工作文件已恢复。
- 新实验只读取hidden_v1/train1500与calibration320/4775decode；因子只从canonical W构造。扩展896维主基须核对旧128维前缀，CPU/GPU四夹具全预览/距离逐位证明及原baseline质量复现后才推进。全部旧测试不得用于这轮选点/再认证。
- 暂停时先在本轮输出目录创建STOP_REQUESTED，等安全batch/config边界停止并核对进程退出；当前prepare的单次NumPy/聚类操作之间检查，若需立即断电则核对新PID后停止本轮树并保留部分文件。不要使用任何历史PID。

## 2026-10-23 新增仅低秩超参数边界实验（当前最新计划，尚未执行）

- 用户要求为仅低秩方案设计类似超参实验；已新增doc/design/V4Validation.html#lowrank-hyperparameters实验9，重要性“必须完成”，状态“未开始”。页面现在9组75场景，原71条日志保留并追加1条；既有质量/GPU/RTL结果不改。
- 首轮固定T16384扫描r=[8,16,32,64,128,256,512,896]，固定r128扫描T=[256,512,1024,2048,4096,8192,16384,32768,65536]，去重16点；加(1,16384)/(128,1)/(1,1)/(128,151936)/(896,151936)共21配置。后续只在校准Pareto附近追加≤12联合点。
- r是低秩维度，区别于实验8选簇数R；T是预筛Top-T，最终K为并入14特殊ID后的并集。固定r增T候选嵌套；增r不保证召回单调。BF16因子/FP32归约下r896不保证近似排名等于dense；T=V且数值/policy正确时全量canonical精算应等于dense，但有额外预览成本。
- 因子只从原始权重构造，不训练新LM。扩展现128维主基前先冻结符号/量化/可变rank归约和padding规则，核对原128前缀；若不同另立新系列。现HLS/selector固定rank128/Top16384，不继承旧资格；r896因子加W超过现320MiB arena，需要新布局。
- 只用校准集选型，旧已打开测试不得重用认证；与实验8共用新最终问题组时，两方案均须在首次打开标签前锁定。计划记录质量、真实K、GPU/FPGA阶段及整次耗时/输出率、存储与DDR成本，未测项保持空值。
- 本次仅文档设计及静态数据/链接/JS语法校验；没有构造因子、训练、GPU测速、EDA或板卡操作，浏览器视觉检查未运行。暂不上板、封存资产不改、旧wb/心跳不恢复继续生效。

## 2026-10-22 新增仅聚类超参数边界实验（当前最新计划，尚未执行）

- 用户要求新增实验，研究仅聚类的中心数C、最近选簇数R、每簇列表上限L对质量与速度的影响及上下限。doc/design/V4Validation.html#cluster-hyperparameters为实验8，重要性“必须完成”，状态“未开始”；不是授权自动训练或上板的完成记录。
- 首轮单参：C=[16,32,64,128,256,512]固定R4/L16384；R=[1,2,4,8,16,32,64,128]固定C128/L16384；L=[256,512,1024,2048,4096,8192,16384,32768,65536]固定C128/R4。共21去重点，加(1,1,1)和(128,128,151936)端点，共23配置；后续仅在校准可行边界追加有限联合点。
- C变化需只用训练集重建；L扩容需从同一训练投票重建长列表并验证旧前缀；R/L单参复用相同中心/排名。所有旧独立测试已打开，不用于这轮搜索或认证；选点锁定后另留全新最终问题组。HumanEval只剩64个未用任务，下一轮代码来源/配额需重新冻结。
- 必须区分有效列表长度n_i与L；R=C且L=V仍可能未覆盖全V；空簇dense fallback须单列纯列表/含fallback质量及比例，不能伪装稀疏高召回。现HLS固定128/4/16384，新参数不继承旧IP/布局资格。
- 本次只更新计划/页面及静态检查，没有新训练、GPU测速、EDA或板卡操作；既有质量与GPU基准不改。暂不上板、封存不改、旧wb/心跳不恢复仍生效。

## 2026-10-22 质量/速度报告合并与GPU参考测速完成（当前最高优先级）

- 用户要求正式实验标题/状态、论文式数据来源、并列折线图，合并质量与速度，并允许先做GPU参考测速。已将doc/design/V4Validation.html改为7组31场景，质量与GPU/FPGA速度同组展示；质量已完成、GPU参考已完成、FPGA未开始，实验整体为部分完成。原17项工程检查及全部历史日志保留。
- 实际GPU基准reports/gpu_method_benchmark_20261022_r2/RESULT.json（相对v4）：RTX5060 Laptop / PyTorch2.13.0+cu130，4个原校准集固定输入，各方案3 warmup+30测量，共480测量；16组合完整候选ID/raw bits及token/score/CRC对CPU参考通过。dense/仅聚类/仅低秩/混合的GPU参考等效输出率约66.33/135.18/164.55/84.36次/s；只是BF16常驻、FP32固定算术PyTorch Eager实现，非优化生产GPU推理、1000问题总体速度、整网decode或FPGA预测。原始记录/方案/数值证明/只读计时审计已保存。
- r1预检发现27个preview值偏差1ULP，未计时。仅修正新benchmark的Python标量除法为显式GPU FP32张量系数，r2完整逐位通过；r1源码/失败记录保留。未改冻结selector/quality脚本、已完成质量结果或private_package_r1。不得从本轮GPU测速调参或重新认证新测试集。
- 新独立质量仍为1000问题/14958 decode、80/356/1漏选；GPU计时用原校准集4个中文/英文/代码/数学夹具，不混合统计。页面已补CMMLU/Dolly/HumanEval/GSM8K官方版本、prompt、分组/采样、采集与指标定义；dense自身0/100%明确为定义对照。
- GPU作业已exit0，无本任务后台GPU/EDA。用户仍明确暂不上板：不连接、探测或操作FPGA，不恢复wb/luyou/心跳，封存资产不改。下一步仍是离线新K绑定、多步/debug/异常准备。页面只做静态数据/链接/JS语法检查，file://浏览器视觉预览受工具策略限制。

## 2026-10-22 新质量与候选规模离线准备完成（当前最高优先级）

- 用户明确“暂不上板，继续离线准备”：不得连接、探测或操作FPGA，不恢复旧wb/luyou/心跳，v2/v3/v3.1封存不改。下方旧活动PID、RUNNING状态均为历史，勿据此停止无关进程或重启流程。
- 新固定算术独立1000问题/14958 decode/零排除评估exit0，聚类漏80/99.4652%、低秩漏356/97.6200%、混合漏1/99.9933%，整体及各类通过拟议99.9%点门槛。配置/算术/来源/入口先冻结，所有旧问题保留组精确规范化去重；不得用本测试组调参重认证。证据module_14_lm_head_v4/reports/fixed_quality_20261022/RESULT.json及INDEPENDENT_REVIEW.json。此为固定算术GPU覆盖模型，不是全新RTL回放、无损/自由生成或发布验收。
- 新decode候选K均值29300.93、中位28183/P9541630/最大56075；已有RTL K21529/6826306拍/34.131530ms/29.2984等效M14输出/s仅单例模型，不代表总体/实板速度。真实v4 decode/P95/TTFT均NOT_RUN。性能报告reports/PERFORMANCE_ASSESSMENT_20261022.*（相对v4目录）。
- K-only选出small17071/median28184/p9541630/max56075，导出hidden/history、固定CPU候选ID/preview/完整raw参考，4组token/score bits/CRC均与dense一致；4份320MiB生产arena全SHA/320块CRC/9源区域/13guards本机预检通过，准备34项目标READ及128B请求但未发送。runtime scratch为零，不预填golden。证据reports/performance_cases_20261022/QUALIFICATION.json及README.md；不是4组RTL/板测。
- private_board.py已有13项host/Tcl mock测试，匹配GEM3/内部包保持不改。现CLI只绑定原中英代码数学四夹具，新K用例campaign绑定仍待扩展；不能直接替换包内manifest或把请求的30/1000次称为已测。
- 当前本轮GPU/CPU/镜像预检流程均退出，无本任务后台GPU/EDA续跑。下一步离线扩展新K用例绑定、多步hidden/history推进、debug全候选及错误路径准备；板卡实际运行必须等用户新的明确安排。续办读PROGRESS.json及doc/LM_HEAD_V4_HANDOFF_20261021.md顶部。

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

## 2026-10-22 继续v4离线实施（当前最新）

- 用户要求继续；仍无板卡连接/探测/操作授权，不恢复旧wb/luyou/心跳，不改v2/v3/v3.1封存资产。
- 昨晚XSim r5/session71531仍在运行，现已进入候选精算阶段；先查日志/结果，不重启同一任务。完整RTL尚未PASS，200MHz系统实现离线审计已PASS。
- 新`standalone/arena_loader/`与`upload_arena_tcp.py`为私有M4AR/version1/1415端口、固定320MiB/64位PL窗口。增加signature/calib/idle检查、有限READ回读和部分ACK跟踪，保留v3.1发送队列与64位CRC修复。
- `reports/arena_loader_20261022/host_r1/RESULT.json`：宿主C测试及13项Python（含真实320MiB文件的mock传输）PASS；网络/PL DDR均未访问，不冒充板测。原始v3.1源码SHA核对不变。
- 新PS计时程序、私有M4PT mailbox/解析器已准备；8项合成文件测试PASS，A53仅用只读历史BSP做语法预检PASS，尚非匹配v4的BSP/ELF。计时保存完整control_call返回已CRC验证token的原始tick，warmup/30次计时/1000稳定调用分开；没有IP周期计数器或LLM TTFT。
- 重EDA必须顺序：等整链RTL/全量trace/原C postcheck完成后再运行`experiments/board_v4_20261021/build_ps_software.ps1`，绑定本次XSA生成BSP与两个ELF，并审计PS LOAD范围。当前未运行BSP生成、未生成最终ELF。详情见续办顶部。
- 已启动一次性本地续建流程session2040/PID24616（`continue_offline_after_rtl.ps1`），状态在`reports/OFFLINE_SEQUENCE_20261022.json`。它等待既有r5真正资格通过后顺序构建BSP/两ELF/内部离线包，无板卡操作。续办先查此状态与真实产物，勿再手工重复启动BSP；用户暂停时须先停此续建流程，再停止既有EDA。

## 2026-10-21 用户恢复v4（当前最高优先级）

- 用户明确“恢复v4”，解除下方安全暂停；主模型继续离线整链RTL与PL DDR系统实现，不恢复旧wb/luyou/心跳。
- 先核对冻结IP/源码/布局/资产SHA；新CoSim使用隔离run selector_full_cosim_r2，保留上次中断产物。
- Vivado复用已完成IP DCP，只重置未完成综合run；本轮系统输出到hardware_r2，日志另立r2，不覆盖上次中断证据。
- 本次恢复不包含板卡连接、探测或操作授权；v4板测仍需新独占安排。v2/v3/v3.1封存资产不改。
- 恢复r2完整系统已完成综合/布局布线/bit/XSA及独立审计：200MHz STA WNS+0.652ns、WHS+0.010ns、WPWS+0.143ns，内部未约束端点0，CDC Critical0、MIG警告0，bit/XSA内嵌bit SHA一致。证据reports/board_v4_20261021/hardware_audit_r2.json（相对v4目录）。仍有816 DRC Warning/211 Advisory，不宣称零警告或板测通过。
- 原官方HLS整链CoSim r2在生成testbench的read_token命名块/同名task冲突处FAIL，原日志保留。仅修复生成包装命名块后，正在顺序执行完整XSim→41943040内存输出值/18标量比较→原C postcheck；不得在这些检查完成前宣称整链RTL PASS。无实际PS BSP/ELF/新loader或板测结果。
- 最新活动仿真为r5/session71531，日志selector_repaired_xsim_r5_20261021.log；Tcl每100us输出窗口，编译payload 9项SHA不变。r3为可观测性主动中断，r4为Windows Tcl路径失败，证据均保留，不当数值结论。继续前先核对活动任务/结果，勿重复启动。详见续办顶部最新说明。

## 2026-10-21 20:03 用户要求安全暂停（当前最高优先级）

- 用户明确“先安全暂停”；主模型已停止本轮v4离线CoSim与Vivado系统综合进程树，复核无EDA进程残留。不得自动续跑，也不恢复旧wb/luyou/心跳。
- 统一selector已完成：Csim 6正确/24预检拒绝/5运行错误门控、32项host测试、HLS综合3.650ns估计、153BRAM18K/247DSP；两个64位AXI master均规划到PL DDR。
- 私有IP已冻结301文件；完整PL DDR BD创建/验证PASS，私有GPIO签名0x4D345301。平台无关PS控制逻辑25项fake-MMIO测试及导出寄存器映射审计PASS；不是实际BSP/ELF/板测。
- 全词表CoSim仅完成C参考生成（1真实/1重叠拒绝），在生成RTL testbench阶段暂停，**没有正式RTL PASS或有效整链周期数**。
- Vivado停在子IP综合：selector和MIG未生成DCP；其余部分已完成DCP保留。顶层综合、布局布线、200MHz STA/CDC、bit/XSA尚未完成。
- 续办先读doc/LM_HEAD_V4_HANDOFF_20261021.md、module_14_lm_head_v4/PROGRESS.json及reports/pause_20261021/。中断日志原样保留，下次用新CoSim run；Vivado仅重置未完成run、复用确实完成的IP检查点，不直接覆盖本次失败/中断证据。
- 本轮未连接、探测或操作板卡；v4实板decode/token/s/TTFT仍NOT_RUN。v2/v3/v3.1封存资产不改。

## 2026-10-21 低秩/路由独立核与完整C链完成（当前最新）

- 主模型完成低秩、聚类路由两个独立HLS组件，各3事务Verilog/XSim协同仿真PASS；HLS均估计3.650ns，未做这两核P&R。
- 低秩CSim5正确/10非法/3非有限，路由6正确/10非法/2非有限；29项host测试PASS。四类真实完整C流程串接路由→低秩→Top-K/并集→canonical候选精算，所有候选raw logits及dense轨迹token/score bits/CRC一致。
- 低秩A扫描采用8路beat树与独立16路context流水归约，理想供数16拍/行；全词表A扫描预算12.15488ms@200MHz，非整核/板上decode。
- 路由r1曾Csim通过但RTL位图丢位（8527→2501，tie18→4）；已改为完整128bit缓存mask OR写回，r2正式RTL通过。失败源码预处理/RTL输出和日志保留，禁止部署r1。
- 新固定算术模型仅重做同校准集4775decode，聚类/低秩/混合漏选15/84/0、路由顺序变化0；没有打开holdout调参或重新宣称独立质量通过。历史r2b99.9933%为原CPU实现结果，不能自动继承为新RTL质量。
- 所有本轮HLS/XSim/GPU/C链作业已结束，无后台续跑；无FPGA操作，旧wb/心跳不恢复。
- 证据：module_14_lm_head_v4/reports/SELECTOR_ARITHMETIC_STAGE_20261021.*；续办：doc/LM_HEAD_V4_HANDOFF_20261021.md。下一步完整selector硬件调度、PL DDR地址/别名/容量合同、整链RTL与系统200MHz/CDC；板测仍需新安排。

## 2026-10-21 v4 离线实施（当前任务）

- 用户回复G盘安排并要求继续；已确认G:工具文件可读且本机Vitis HLS2021.1启动成功。沙箱直接启动报错，本机离线调用正常；不是工具缺失。
- 当前独立候选HLS top最终C仿真17组真实数值/13类非法输入/4项特殊路径PASS。首轮174.5MHz瓶颈修正为固定四路ID解析后，HLS估计3.830ns/261.12MHz；26项host测试PASS。尚无板卡结论。
- 保守4路聚类+rank128/top16384已先冻结再测新问题组：r2b1000问题/14969 decode/1中文漏选，召回99.9933%，P2_RECALL_PASS（拟议点估计门槛，非无损或发布验收）。r2初版304记录因输入长度预检暂停，保留且未用于拟合/选型/统计。
- 旧工具日期core_revision溢出仅在本轮生成脚本局部修复并重打包成功。OOC r1因HD.CLK_SRC未设已停止；clocked r2在显式BUFGCE_X0Y0参考假设下布线完成，200MHz内部WNS+0.808ns/WHS+0.010ns，无未约束内部端点。外部I/O、selector、完整BD/CDC和板测不在该结论内。
- 16:38 top-K/并集HLS阶段完成：C仿真8精确/10非法PASS，Verilog/XSim协同仿真3事务PASS；HLS估计3.650ns、64 BRAM18K/0DSP。此核仅处理已完成policy的preview，不包含低秩矩阵乘或路由算术，尚无本核P&R结论。
- 当前所有本轮采集/综合/仿真/布局布线进程已退出，无后台续跑。最新证据为v4 reports/OFFLINE_STAGE_RESULT_20261021.*及TOPK_STAGE_RESULT_20261021.*；下一步低秩/路由HLS与数值资格验证、再做全链集成，仍不操作板卡。
- 用户要求继续 `doc/LM_HEAD_V4_PLAN_20261019.md`，并选择公开可复现语料、记录来源与划分。
- 在独立 `module_14_lm_head_v4/` 推进候选精算和软件selector；v3.1完成的PL DDR dense基线直接复用，封存资产不改。
- CPU候选精算48组真实对照及23项host测试通过；GPU逐位head和旧tokenizer输入验证通过，公开语料1500/320/1000条已固定来源/划分。
- train1500条/22433 decode、calibration320条/4775 decode、holdout1000条/14970 decode全部采集完成，零排除；采集/评估进程均已退出，无后台待执行任务。
- 首轮36组筛选未达到拟议门槛；第二轮42组组合选型锁定3路聚类+rank64/top8192，校准99.9581%，但独立holdout仅99.8464%（23漏选，中文15/英文7/代码1/数学0），状态QUALITY_FAIL，不推进发布。
- 实际候选生成/18例精算连接复核PASS；数据/代码/参数/选择锁SHA审计PASS与质量失败是不同结论。当前holdout已评估，禁止重用它调参；下一轮须预留新问题组作为最终测试。
- 本轮不连接、探测或操作FPGA板卡；旧wb任务和心跳不恢复。稀疏板测需重新确认独占安排。
- G: EDA工具盘已恢复并验证2021.1可运行。尚无完整v4 selector/bit/板测或正式交付结论；上游直供权重仍等待负责人框架文档。

## 2026-10-20 v3.1 完成（当前最终状态）

- 工程验收PASS且正式交付完成；源码/版本/加载/数值/时序/30次计时/1000次稳定性及ZIP解压复核全部通过。
- 交付：`deliverables/20261020_M14_V3_1_r1/M14_V3_1_20261020_r1/`；ZIP同级，1048成员、306897964B。
- ZIP SHA256：`7b9512bfc3a6126b04654ff1374857edb15f881635965d4f90ed69080c36fb01`；内部SHA256SUMS与外部ZIP_SHA256SUMS.txt已生成，封存后不要直接修改交付文件。
- 真实报告：`module_14_lm_head_v3_1/reports/board_v31_20261019/RESULT.md`；IP median/P95=117.751830/117.752020ms，与v3基本持平；完整目标CRC加载39.980274s。
- 板卡最终为v3.1/build0x30c08011/cap0x382，PL DDR仍保留canonical权重，A53#0已halt并disconnect；无活动加载/板测。断电后需完整初始化/重载。
- 根HTML开发日志已补充真实修复、验收和交付，64条记录保留61条原历史；旧wb任务、心跳保持停止，不自动继续。
- 本轮结束；后续稀疏化和上游直供按v4范围等待新安排。v2/v3原ZIP SHA复核不变。


## 2026-10-20 v3.1真实验收通过，交付整理中（当前最新，覆盖下方历史暂停/未测状态）

- 用户已重启并授权继续；主模型完成v3.1真实验收：8步生产/8份完整logits逐位一致、30独立计时、1000连续调用通过。
- PL DDR目标逐块/整份CRC及sentinel、6项加载错误后整份重载、内存/地址/软件注入校准超时通过。
- 最终loader修复GEM待发送队列重触发及64位目标回读CRC；完整加载约39.98s，较早期255.17s改善，仍慢于PS DDR对照8.52663s。
- 当前C源码/四ELF/package一致；旧实验包和失败campaign不部署、不覆盖。
- IP median/P95=117.751830/117.752020ms，详细口径及同板不同启动说明见reports/board_v31_20261019/RESULT.md（相对模块目录）。
- 正式交付整理中；完成状态以PROGRESS.json和交付目录DELIVERY_VALIDATION.json为准。旧wb任务/心跳不恢复，v2/v3封存不改。


## 2026-10-20 20:18 用户恢复（当前最高优先级）

- 用户明确“请继续”，解除下方暂停；主模型先小数据定位TCP分片响应，再核查PL DDR回读性能，之后完整重跑验收。
- 保留所有失败和实验包，不将当前实验loader当作正式交付；v2/v3封存资产不改，旧wb和心跳不恢复。

## 2026-10-20 用户再次暂停（当前最高优先级）

- 用户要求“先停一下”，正在讨论是否重启及PS/PL DDR加载速度差异。当前停止试验，不自动继续。
- 本任务主机加载/验收进程已退出；已用XSCT停止A53#0的实验loader并disconnect，可以断电。
- 当前v3.1仅内存/地址/校准诊断、一次canonical PL DDR逐块/整份CRC及sentinel通过。
  完整加载约255.17s；合法TCP分片响应超时未解决，数值/性能/稳定性尚未执行，不能验收/交付。
- 当前有实验诊断loader：源码/最新build ELF与package中的诊断第一版不同；下次先读续办记录，禁止直接把当前package当最终已验收发布。
- 续办真源仍为doc/LM_HEAD_V3_1_HANDOFF_20261019.md；旧wb任务和心跳不恢复。

## 2026-10-20 19:34 用户确认板卡连接，恢复验收（当前最新）

- 用户明确“我已连接板卡，请继续”，解除下方等待板卡限制；由Codex主模型继续本轮v3.1初始化、PL配置、TCP加载与验收。
- 本机初检有线链路Up/1Gbps，未发现其他下载/板测进程；继续核对JTAG，再用冻结配套包完整初始化。
- 不恢复旧wb任务或心跳，不改v2/v3封存资产。数值/性能/稳定性以本轮真实结果为准，当前尚未通过。

## 2026-10-20 离线准备检查点（当前最新）

- v3.1完整实现/硬件审计PASS：WNS0.632ns、WHS0.010ns，CDC Critical0、MIG警告0，bit/XSA一致。
- 用户重插工具盘后，已于16:43完成最终XSA配套BSP及四个ELF；软件构建PASS，加载包冻结并通过离线校验。
  当前状态为OFFLINE_READY_BOARD_NOT_RUN，加载包在module_14_lm_head_v3_1/reports/board_v31_20261019/package/。
  原工具盘故障与首次BSP文件占用失败均保留日志；显式恢复成功，不再等待工具盘。
- 板卡仍按用户要求不可用，不连接/探测/初始化/加载/板测；旧wb任务、心跳不恢复。
- 当前状态见 `module_14_lm_head_v3_1/reports/board_v31_20261019/PREPARATION_STATUS.md`；
  续办记录仍为 `doc/LM_HEAD_V3_1_HANDOFF_20261019.md`。
- 硬件及软件离线准备已完成，不需重新实现或编译；下一步仅在用户明确板卡就绪后执行验收。
  v3.1真实板测仍全部NOT_RUN，正式交付ZIP未创建，不能将离线准备PASS称为工程验收PASS。

## 用户恢复（2026-10-19，当前最高优先级）

- 恢复后用户说明“当前板卡不具备状态，先做好其他准备工作，等具备状态后我们再上板卡”。
  当前仅做离线实现、软件、加载包及验收准备；停止板卡连接、探测、初始化、加载和板测，
  等用户确认板卡就绪后再恢复硬件工作。已有独占授权不覆盖本次等待阶段。
- 用户明确要求“恢复 v3.1”，解除下方断电暂停；由 Codex 主模型继续实现、板测与交付。
- 继续使用 `doc/LM_HEAD_V3_1_HANDOFF_20261019.md` 和实际检查点续办；不重启旧 wb 任务或心跳。
- 恢复时已复用placed DCP完成首轮布线；发现原共享网络地址映射和CDC/时钟元数据问题后，
  已改为A53/HLS统一64位高地址、单比特GPIO、UI域门控和正式差分参考时钟接口，重新实现。
  最新进度见续办记录；旧placed DCP只作历史证据，不能用于当前修正版本。断电后权重需重载。

## 历史用户暂停（2026-10-19，已由上方恢复解除）

- 用户明确要求中断本会话，笔记本与板卡需要断电；立即停止工作，不自动继续。
- 主模型已停止本轮 v3.1 的 Vivado 构建进程树，原 luyou 任务 failed，五分钟心跳 PAUSED，
  完成事件桥已一次投递后退出；不要重派或重启旧任务。
- 续办真源：`doc/LM_HEAD_V3_1_HANDOFF_20261019.md`。等待用户明确恢复后继续。
- 当前 v3.1 尚未完成实现/时序/板测/交付；本轮 v3 同板基线已通过。断电后 DDR 权重丢失。

## lm_head v3.1 最新接管安排（2026-10-19，优先于后文 workbuddy 安排）

- 用户明确要求“不用交给 wb 了，你来完成吧”；当前 Codex 主模型接管全部实现、
  板卡操作、验收及交付，不再派回 workbuddy。
- 用户已确认板卡释放并连接；旧任务 `t-mvf361si-01k-ktoa` 已 failed，
  其残留 codebuddy 会话已按任务身份核实后停止，保留原始证据和 Vivado 后台构建。
- 主模型现在独占执行本次已授权的初始化、PL 配置、TCP 加载、内存及数值/性能验收。
  若新发现其他任务占用则先停止冲突操作，不强抢。早期 JTAG/网口断连记录须重新验证。
- 仍保持 v3.1 的 200 MHz 完整词表和 PL DDR 计算数据范围，v3 已验收资产不改。
- 原任务五分钟检查心跳在接管时暂停；主模型活跃工作期间不并发启动旧任务监控或执行器。

## lm_head v3.1 当前执行安排（2026-10-19，优先于下方历史禁操作记录）

- 用户已要求实施 PL DDR 迁移、形成 `lm_head v3.1` 并上板验收，指定通过 luyou
  派发给 wb（真实节点名 `workbuddy`）；随后明确确认“已释放，可由 wb 独占使用”。
- 本次由 workbuddy 独占板卡执行初始化、配置、TCP 加载及验收；规划方不并行操作板卡。
  此安排替代下方“另一个 agent 占用、禁止板卡操作”的历史限制，仅限本任务范围。
- v3.1 只迁移计算数据到 PL DDR，保持 200 MHz、完整词表、原 BF16/FP32 数学语义；
  不实现候选词表稀疏化或上游直接供权重，后两项继续按 v4 规划处理。
- PS 软件、栈、堆、TCP 暂存和主机 mailbox 可保留 PS DDR；权重、hidden、history、
  logits 走 PL DDR，计算路径禁止隐式 PS DDR 回退。v3 已验收源码、证据与交付包不改。
- 执行任务书：`doc/tasks/LM_HEAD_V3_1_PL_DDR_WB_20261019.md`。

## lm_head v4 规划范围（2026-10-19 已确认）

- v4 先规划 PL DDR 迁移与动态候选词表稀疏化，详见
  `doc/LM_HEAD_V4_PLAN_20261019.md`；v3 发布源码、证据和交付包保留。
- 用户确认：lm_head 权重、hidden、history、logits、候选表及筛选参数迁至 PL DDR；
  A53 程序、栈、堆、TCP 加载暂存及主机 mailbox 仍可使用 PS DDR。
  计算路径不得隐式回退读取 PS DDR 权重；加载校验针对 PL DDR 实际回读。
- “上一个模块直接提供权重、不经过 DDR”依赖总负责人更新框架并下发文档，本轮不实现。
- 上述 v4 规划本身不构成板测授权；当前 v3.1 的新板测授权与独占安排见文件顶部。

## 板卡与历史续办约束

- 2026-10-19 历史整理阶段要求（已由顶部 v3.1 安排替代）：板卡当时由另一个 agent 使用，本任务仅做本地日志/交付整理，
  不执行板卡操作（包括 JTAG 连接/读取、初始化、加载、验收或网络探测）。此前板测授权
  不适用于当前整理阶段；如后续需要操作板卡，先取得用户新的明确安排。

- M14 V2 大权重下次优先通过 `module_14_lm_head_v2/standalone/program_board_tcp.ps1`
  加载。JTAG 仅负责 PS 初始化、PL 配置、小 ELF/输入/mailbox 和结果采集；不要直接
  默认用 `dow -data` 上传 272,269,312-byte 权重，它约需 30 分钟。
- 网口加载说明：`module_14_lm_head_v2/standalone/TCP_WEIGHT_LOADING.md`。
  2026-10-10 已完成完整 BF16 网口加载、DDR/sentinel 校验及 6 项错误路径板测。
  实测含逐块与整份 DDR CRC32 为 8.36 秒、31.06 MiB/s；使用修复 tcp_output 重试后的
  loader，不要改回 2026-10-09 初始版本。历史 FP16 测速不作为本次结果。
- 初次使用 TCP loader 时允许保留已初始化的 PL/DDR（`-RetainHardware`），但它会
  替换 A53 程序并覆盖整个权重区；只在没有板测正在运行时启动。
- 权重只接受 canonical BF16 文件。主机 SHA256、每块 DDR 回读 CRC32、最终全 DDR
  CRC32 和首尾 sentinel 都通过后才继续 IP 测试。加载失败或断线后整份重传。
- 用户已于 2026-10-10 要求恢复工作，昨日暂停解除；STOP_REQUESTED 已归档。
  当前进展见 `doc/LM_HEAD_V2_HANDOFF_20261009.md`。已加载 DDR 若断电则丢失。

## lm_head v3 · 200 MHz 独立版本（2026-10-19）

- 本轮范围仍为独立 M14，暂不开展公共 ABI / 原生 M06 / 整体 LLM 集成。
- 用户将已验收的200 MHz发布版命名为 `lm_head v3`；交付目录为
  `deliverables/20261019_M14_V3_r1/M14_V3_20261019_r1/`，模块目录 `module_14_lm_head_v3/`。
  发布名称为v3，ABI仍为2、HLS top仍为lm_head_v2、IP版本仍为2.1，已测镜像身份不变。
- 200 MHz 已通过真实板测：8 步生产/完整 logits 逐位一致、错误路径、30 次独立计时、
  1000 次连续调用；报告 `module_14_lm_head_v2/reports/board200_20261019/RESULT.md`。
  IP median/P95 117.751805/117.751890 ms，相对同板100 MHz提升1.90968倍。
- 正式源码在 `module_14_lm_head_v2/experiments/board200_20261019/`；原生产100 MHz源码
  和20261010交付ZIP保留。新 build_config=`0x20c08011`，HLS IP version=2.1。
- 200 MHz 上板使用 `reports/board200_20261019/package/`（相对模块目录），同时作为
  `program_board_tcp.ps1 -PackageDir` 和 `-LoaderPackageDir`，并传 `-BoardIP 192.168.0.190`。
  PC 有线为 `192.168.0.12/24`；新loader与PC同网段，旧默认loader仍为`.8`网段。
- 100/200 MHz 切换必须完整初始化，不能用 `-RetainHardware`；保留硬件只适用于
  已确认相同镜像/时钟配置。新包绑定 bit/XSA/PS init/ELF/profile，禁止混用旧PS初始化。
  `run_step.ps1` / `run_acceptance.ps1` 也应显式传新 `-PackageDir`，计时按包内profile换算。



