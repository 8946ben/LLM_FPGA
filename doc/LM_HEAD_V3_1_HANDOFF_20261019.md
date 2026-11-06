# lm_head v3.1 断电前续办记录

## 2026-10-20 v3.1 完成（当前最终状态）

- 工程验收PASS且正式交付完成；源码/版本/加载/数值/时序/30次计时/1000次稳定性及ZIP解压复核全部通过。
- 交付：`deliverables/20261020_M14_V3_1_r1/M14_V3_1_20261020_r1/`；ZIP同级，1048成员、306897964B。
- ZIP SHA256：`7b9512bfc3a6126b04654ff1374857edb15f881635965d4f90ed69080c36fb01`；内部SHA256SUMS与外部ZIP_SHA256SUMS.txt已生成，封存后不要直接修改交付文件。
- 真实报告：`module_14_lm_head_v3_1/reports/board_v31_20261019/RESULT.md`；IP median/P95=117.751830/117.752020ms，与v3基本持平；完整目标CRC加载39.980274s。
- 板卡最终为v3.1/build0x30c08011/cap0x382，PL DDR仍保留canonical权重，A53#0已halt并disconnect；无活动加载/板测。断电后需完整初始化/重载。
- 根HTML开发日志已补充真实修复、验收和交付，64条记录保留61条原历史；旧wb任务、心跳保持停止，不自动继续。
- 本轮结束；后续稀疏化和上游直供按v4范围等待新安排。v2/v3原ZIP SHA复核不变。


## 2026-10-20 真实验收通过检查点（当前最新，覆盖下方历史暂停/未测状态）

- 用户已重启并授权继续；主模型完成v3.1真实验收：8步生产/8份完整logits逐位一致、30独立计时、1000连续调用通过。
- PL DDR目标逐块/整份CRC及sentinel、6项加载错误后整份重载、内存/地址/软件注入校准超时通过。
- 最终loader修复GEM待发送队列重触发及64位目标回读CRC；完整加载约39.98s，较早期255.17s改善，仍慢于PS DDR对照8.52663s。
- 当前C源码/四ELF/package一致；旧实验包和失败campaign不部署、不覆盖。
- IP median/P95=117.751830/117.752020ms，详细口径及同板不同启动说明见reports/board_v31_20261019/RESULT.md（相对模块目录）。
- 正式交付整理中；完成状态以PROGRESS.json和交付目录DELIVERY_VALIDATION.json为准。旧wb任务/心跳不恢复，v2/v3封存不改。


## 2026-10-20 再次暂停：加载与TCP分片排查（当前最新）

**用户要求先停，所有主机试验进程已退出；A53#0实验loader已stop并disconnect，可以断电。等待用户明确恢复。**

- 用户已确认本次是10/19采集v3任务对照的同一块板卡；两版为不同启动，记录在
  `reports/board_v31_20261019/BOARD_SESSION_20261020.json`。
- 网络Up/1Gbps，PC=192.168.0.12/24。PSU/A53枚举正常；最终硬件未重建，bit/XSA保持。
- 实板通过：PL DDR校准、lane/保护区/稀疏地址位/容量末端恢复性自测，3类地址拒绝，
  10s软件校准超时注入及恢复；不是全2GiB逐字穷举，不是物理MIG故障注入。
- 一次完整canonical目标PL DDR逐块/整份CRC7acfde43和首尾sentinel已通过：
  `reports/board_runs/20261020_195434_343_tcp_weight/`，255.1677297000133s、1.0175904700MiB/s。
  字节发送含逐块校验130.17s，随后整份回读约125s。之前120s主机COMMIT等待曾超时；
  uploader与full-CRC错误测试响应等待已调为600s，所有校验条件保留。
- 计算数值、30次计时与1000连续均NOT_RUN。上述慢速是A53加载/校验，不是IP推理耗时。
  代码事实：PL DDR采用NORM_NONCACHE；loader_core.c的CRC逐字节读取目标，跨PS→PL访问开销
  是强相关解释，尚未做分项/宽读取对照，不可声称已量化根因。重启不能改变该软件访问模式。
- 冷启动控制器修正：HLS输出身份寄存器复位0，需完成一次调用；共享
  `standalone/scripts/word_u32.tcl`提供BAD_ABI、零DDR流量、idle及真实身份检查。
  只对刚完整初始化且核对hash的镜像允许查询，Retain仍拒绝零/旧身份；XSCT实际返回十进制，
  已兼容十进制/显式十六进制并统一日志hex；避免读后清零ap_done，使用稳定身份输出等待。
  24项纯mock通过，日志`identity_cold_mock_20261020.log`。诊断结果明确区分HLS身份调用与点积调用。
- 完整权重后错误测试仅首个bad_chunk_crc通过，合法fragmented DATA失败：
  完整帧解码、小块DDR CRC成功且响应排队，最终60s idle abort；不能跳过后标PASS。
  原全链任务`20261020_195327_510_pl_ddr_acceptance/`止于此处。
- 已用小数据重现（不再重复272MB）；诊断loader记录ACK事件、tcp_ticks，证实定时器3→123正常推进。
  仍未定位响应发送/确认停滞的根因。PC pktmon提示OS拒绝访问，无抓包，没有改管理员权限。
  `.cache/v31_board_20261020/tcp_fragment_failure.bin`及`tcp_trace.bin`保存原始环形诊断。
  第二实验版增加PCB与TX ring快照至0x51002000，但暂停前未导出该辅助窗口；断电后需重现。
- **包/源码状态**：原离线包完整保存在
  `reports/board_v31_20261019/package_before_tcp_trace_20261020/`。
  当前`package/`为诊断第一版（新增tcp_ticks/ACK）；最新`build/.../software/m14_tcp_loader.elf`
  及loader/main.c为PCB/TX ring诊断第二版，两者不同，绝非最终发布。实验版均从同一最终XSA/BSP编译。
  最终修复后须保留历史包，重新freeze配套package并全量重跑验收；错误测试后必须整份重传。
- 现场已停止：`.cache/v31_board_20261020/pause_board.log`含A53_STOPPED；查询无本任务upload/test/campaign进程。
  当前DDR已被小数据错误测试改写且不具备可计算权重身份，断电也会丢失；下次不能直接计算。
- 下一步只在用户恢复后：先小数据定位TCP响应问题，再考虑用宽读/PS暂存降低目标回读CRC开销
  （仍须实际读取PL DDR），重新freeze与全套验收。v2/v3封存资产不动，不恢复旧wb/心跳。

## 2026-10-20 16:43 最新检查点（优先于后文）

**离线准备全部完成：OFFLINE_READY_BOARD_NOT_RUN。板卡仍不可用，不连接或操作。**

- 已复用既有200MHz签核硬件，无重新实现；最终XSA SHA256为
  `89ea49af79a8a5dfacc88edd65f4a60b573f1b7290425787f1b24ecc4783c828`。
- 用户重插工具盘后，Vitis能够读取并运行。首次恢复构建遇BSP文件占用/目录不完整，
  失败记录保留在`software_build_restored.log`和`platform_first_restored_attempt.log`。
  不推断具体占用进程；此次未再将进程存活当作成功。
- 同一XSA哈希核验后，`build_software.ps1 -ResumePlatform`恢复现有未完成平台成功；
  exec29568已exit0，日志`build/board_v31_20261019/software_build_resume.log`包含
  `M14_V31_PLATFORM=PASS`及`M14_V31_SOFTWARE=PASS`。
  构建入口增加平台PASS及必需BSP文件门槛，失败时不继续编译。
- 正式BSP和生产/TCP loader/独立内存诊断/软件校准超时注入四个ELF均从最终XSA生成；
  严格编译链接及未解析符号检查通过。BSP内PHY源码与项目补丁SHA256相同。
  `BUILD_SOURCES.json`绑定XSA、C/header/linker源文件及四个ELF。
- `package.py`及`scripts/validate_preboard.py`均实际执行成功：
  `reports/board_v31_20261019/package/`已冻结配套bit/XSA/PS init/四个ELF/profile/hash；
  `OFFLINE_PREPARATION.json/md`已生成，marker=`PASS_BOARD_NOT_RUN`。
  canonical BF16仅检查主机文件SHA，目标PL DDR CRC/sentinel仍NOT_RUN。
- 5项Python主机测试复核PASS，日志`host_unittest_final.log`；构建PowerShell解析PASS。
  软件补充核查在`SOFTWARE_BUILD_VERIFICATION.json`；综合状态见`PREPARATION_STATUS.md`。
- 下一步：用户明确板卡就绪后，按`BOARD_PLAN.md`及
  `standalone/run_pl_ddr_acceptance.ps1`完整初始化、PL DDR诊断、TCP加载和真实验收。
  本版板测均NOT_RUN，正式交付目录/ZIP仍不生成；本轮v3对照继续保留，不能替代v3.1。
- 旧wb任务/心跳不恢复；无需重建已签核硬件，不改v2/v3已验收资产。

## 2026-10-20 00:37 最新检查点（优先于后文）

**硬件离线签核全部通过；软件与加载包未完成，等待工具盘恢复。板卡仍不可用。**

- 当前汇总：`module_14_lm_head_v3_1/reports/board_v31_20261019/PREPARATION_STATUS.md`。
- 硬件：`hardware_audit.json` PASS，WNS/WHS/WPWS=0.632/0.010/0.143ns；
  CDC Critical0、MIG警告0、bus-skew最小余量4.098ns，其他内部时序检查均0。
  bit SHA=f68ee15731011c38398a6fad5181d9b7660d17fa100d61b46db34babf928f433。
  XSA嵌入bit匹配。完整BD资源LUT42205、FF64347、BRAM47.5、DSP62。
- 完成的硬件入口：`resume_from_opt.tcl`，日志 `launch/reset_io_resume.*`；exec44019已exit0。
  不应再运行build.tcl/reset实现。实际package尚未创建，硬件文件在reports/.../hardware/。
- 工具盘故障：G: Seagate Backup Plus，系统事件UASPStor129、disk153（磁盘1 I/O重试），
  证据 `.cache/luyou_v3_1_20261019/tool_disk_events_20261020.json`。
  软件启动曾停在读取G:/Xilinx/Vitis/2021.1/bin/xsct.bat；重试后SDK刚启动又被停止，未完成平台或ELF。
  进程快照 `stopped_for_tool_disk_io.json`；最后核查无本任务SDK写入进程。
  部分工作区已归档为 `build/board_v31_20261019/workspace_tool_disk_attempt_20261020_003344/`。
  IDE.log中的xsct连接关闭为主模型停止客户端后的结果，不能误作原始故障原因。
- 00:39:41本机只读收尾核查：无Vivado/rdi_xsct/Java/hw_server进程，无本机3121端口调试连接。
  软件启动及文件查询exec会话55640/76360/83374均停止，11978只读查询结束。
  不存在本任务继续写入的后台构建；旧五分钟心跳已核实为PAUSED。
- 已在本聊天请求用户确认工具盘恢复，尚待答复；不要继续访问不稳定工具盘或重启旧任务。
  用户未授权恢复板卡可用状态；即使工具盘恢复，也只继续离线工作。
- 恢复工具盘后：确认没有残留SDK写入 → 从现有最终XSA运行build_software.ps1，
  生成新平台及test/loader/diag/calib_timeout四个ELF → package.py → validate_preboard.py。
  新source身份记录/硬件审计门槛都已写好，禁止旧BSP或旧ELF混入。
- 内存诊断新增DSB（含编译器memory clobber）排空写缓冲，且检查8/16/32/64位字节lane；
  此项C代码待正式编译和板测，绝非已通过的物理DDR验证。
- 5项Python主机检查通过；10项Tcl全部硬件命令mock检查通过；v2/v3交付ZIP SHA未改变。
- `OFFLINE_PREPARATION.md/json` 只有validate_preboard真正通过才生成，当前尚不存在。
  当前正式部署package和正式交付ZIP均未生成；v3.1所有板测NOT_RUN。

2026-10-19 22:21，用户明确要求“恢复 v3.1”，主模型已解除断电暂停并继续执行。
原暂停记录保留在后文；旧 wb 任务、旧心跳仍不重启。

**恢复阶段最新地址约定（优先于下文历史局部偏移方案）：**
发现原BD对同一MIG的PS高地址/HLS低地址映射产生BD41-1353/1267严重告警。
已改为PS和4个HLS master统一使用 `0x400000000..0x47FFFFFFF` 系统地址；
MIG31位接口接收地址低位。A53 mailbox地址保持不变，驱动不再减基址，拒绝旧局部偏移。
所有HLS master显式排除控制/GPIO slave。common-map验证已消除分段冲突；
随后发现外部时钟标量端口没有把200MHz传播到MIG差分时钟接口，改为
`pl_ddr_refclk`正式差分接口，物理引脚仍AL8/AL7，XDC生成器已同步。
最新构建入口 `refine_address_map.tcl build`，日志 `launch/final_address_build_3.*`。

新增 `standalone/run_pl_ddr_acceptance.ps1` 为就绪后的总入口；
`scripts/finalize_acceptance.py`、`package_delivery_v31.py`、`verify_delivery_v31.py`
为真实验收后汇总/交付准备，**尚未在真实v3.1产物上完成执行验证**。
当前板卡不可用，不运行任何硬件入口。最终准备完成后更新本记录。

23:33 离线约束复核补充：原引脚生成器误将DDR RESET也归类为SSTL12_DCI，
MIG生成的 `par/*.xdc` 明确要求LVCMOS12、DRIVE8；原候选因此有MIG-55/69警告。
已修复生成器和XDC，并新增 `apply_io_constraints.tcl` 作为place前hook，
从本轮23:30保存的opt DCP继续（不是最早的20:22版本）。
当前入口 `resume_from_opt.tcl`，日志 `launch/reset_io_resume.*`，exec session44019。
审计已要求reset I/O合同正确、无MIG警告、CDC Critical=0、bus-skew非负。
中断的原构建树14736已验证身份并停止；opt DCP及原日志备份于
`.cache/luyou_v3_1_20261019/before_reset_io_fix/`。
`tests/test_retained_identity.tcl` 用普通tclsh、全部硬件命令mock的10个用例已通过，
hardware_access=NONE；不是板测。正式ELF仍待最终XSA生成。

恢复进展：独立确认已保存 placed DCP（48,673,838 bytes）；用 Vivado
`reset_runs -from_step phys_opt_design impl_1` 仅复位中断及后续阶段，日志确认
`open_checkpoint m14_v31_system_wrapper_placed.dcp`。恢复入口为
`experiments/board_v31_20261019/resume_build.tcl`，日志 `launch/resume_build.log`。
恢复时有线网卡 Disconnected，JTAG枚举为空。用户随后明确板卡暂不具备状态，
先做其他准备；当前不再探测或操作板卡，等待用户确认板卡就绪。
另补充可复用驱动的 HLS-local 2 GiB 全跨度检查；主机边界运行测试通过（含A53地址、精确末端、越界和整数溢出）。

22:39，恢复后的首轮实现时序 WNS/WHS/WPWS=0.954/0.010/0.143ns，
但发现校准 GPIO 宽度2导致同一状态复制到两个独立同步通道，CDC-11 Critical 2条。
尚不能作为最终通过；下一轮以单比特GPIO、UI域复位门控重新综合实现，
使用 `refine_cdc.tcl` 更新现有BD（`create_bd.tcl`已同步修正）。
已增强 `audit_hardware.py`：CDC Critical=0、未知CDC警告=0、bus-skew非负，
只接受MIG异步DDR reset输出缺少output-delay和vendor debug FIFO CDC-15的明确例外。

软件准备新增独立 `m14_calib_timeout_test.elf` 构建：只在该测试ELF屏蔽读到的校准状态，
验证10秒NOT_READY与无IP调用；不修改物理MIG，不得称为真实物理校准失败测试。
`initialize_selftest.ps1 -InjectCalibTimeout -RetainHardware` 对应此测试；实际尚未运行。

## 执行归属与停止状态

- 用户已要求由当前 Codex 主模型完成，不再派回 workbuddy。
- 原 luyou 任务 `t-mvf361si-01k-ktoa` 已 failed；其 RESULT/BLOCKER 为历史交接。
- 原 codebuddy 会话 PID23204 已停止。完成事件桥只投递一次后退出。
- 自动化 `v3-1-pl-ddr` 已 PAUSED，不要自动重启或重复派发。
- 主模型构建主进程 PID36816 及其子进程已按任务身份核实后停止。
  清单：`.cache/luyou_v3_1_20261019/paused_processes.json`。
- 当前没有板卡测试或权重传输正在进行。断电前板上最后运行的是已验收 v3，
  v3.1 尚未上板；断电后 PS/PL DDR 均视为无有效权重。

## 范围

v3.1 仅将完整词表 M14 的权重、hidden、history、logits 迁往 PL DDR，保持 200 MHz、
原 BF16/FP32 数学语义；A53 程序/栈/堆/TCP 暂存/mailbox 可保留 PS DDR。
不做稀疏化和上游直接供权重；两者仍留待 v4。

## 已完成

1. HLS csynth 与 IP2.2 导出、MIG BD 创建通过。
   新 build_config=`0x30c08011`，capabilities=`0x382`，top 仍 `lm_head_v2`。
2. 数学 CPP 与 v3 完全相同，SHA256：
   `926911392a1664c05072ac3df2c9c494e55b9d94e72776c67ee5e642d5a5ef91`。
3. 主模型独立修复地址错误：A53 基址 `0x400000000`；权重 `0x400100000`，
   hidden `0x4104A8000`，history `0x4104A8700`，logits `0x4104AD140`。
   原脚本多一位的 `0x40104...` 已修复；末端 sentinel=`0x4104A7FF0`。
4. 统一平台名称 `m14_board_v31_platform`；修复 profile reset_pin=AM5、默认 package 路径、
   严格汇总能力位、新模块 TCP 默认地址；禁用遗留 PS DDR 大权重 JTAG 加载入口。
5. PL DDR RESET 已在手册物理第18页独立核实为 AM5，约束生成器已补齐。
   地址/命令用 SSTL12_DCI，DQ/DM 用 POD12_DCI，DQS 用 DIFF_POD12_DCI。
6. `tests/test_pl_ddr_layout.py` 三项跨语言地址/序列化/绑定检查通过。
   新 test/loader/diag 使用旧 BSP 的严格编译预检通过；仅是语法预检，不可部署。
7. 新增正式自测源码：1 MiB 保护区数据模式、全2GiB地址位探测及末端读写恢复。
   校准超时发布 mailbox NOT_READY；加入独立 `LMH_V31_SELFTEST_ONLY` 诊断 ELF 构建。
   `standalone/initialize_selftest.ps1`、`scripts/initialize_selftest.tcl`、
   `inspect_memory_diag.py` 已写好，**尚未真实运行**。
8. 断电前 PC 有线 Up/1Gbps，192.168.0.12/24；JTAG重新枚举到PSU/4个A53。
   原 wb 的断连结论已过时；新证据位于 `.cache/luyou_v3_1_20261019/main_target_details.log`。
9. 本轮 v3 同板基线已完整通过55项，包括8步生产/8步完整logits、错误路径、30次独立计时、1000次连续调用。
   - campaign：`module_14_lm_head_v3_1/reports/board_runs/20261019_201218_472_acceptance/campaign.json`
   - 严格汇总：`module_14_lm_head_v3_1/reports/board_v31_20261019/baseline_v3_summary.json`
   - IP median/P95：117.751805 / 117.751880 ms；A53 median：117.76728767287673 ms。
   - 基线加载：`reports/board_runs/20261019_201046_440_tcp_weight/`（相对新模块）。
     8.5266304s，30.4523871MiB/s；canonical SHA、DDR CRC32=7acfde43、首尾 sentinel 全通过。
   - 这全部是 **v3 PS DDR 对照**，不能写为 v3.1 PL DDR 板测。

## 中断位置与实现状态

主模型通过受控 exec 会话57545运行 v3.1 `build.tcl`。中断前：

- MIG生成、调试核生成、opt_design通过，布局推进到 Phase4 Post Placement Optimization。
- 没有最终 routed timing、bit/XSA 或可上板 package；不可声称200MHz实现验收通过。
- 已保存 opt checkpoint：
  `module_14_lm_head_v3_1/board/build/m14_board_v31_20261019/m14_board_v31_20261019.runs/impl_1/m14_v31_system_wrapper_opt.dcp`
- 原工程及综合检查点仍在；用户暂停时停止进程，未删除/重置工程。
- 日志：`module_14_lm_head_v3_1/build/board_v31_20261019/launch/main_build.*`
  及同工程 `.runs/impl_1/runme.log`。不要覆盖原 wb 失败证据。

## 恢复后顺序

1. 用户明确恢复后，核实 G:/Xilinx/2021.1、板卡连接和独占安排。
2. 核对工程中断状态。优先从 opt/后续已存在的有效 checkpoint 继续；必要时使用已完成综合重新实现。
   现有 `build.tcl` 会 reset impl_1 后重跑，耗时较多但已修正流程；先保留日志再选择恢复路径。
3. 完成完整STA/CDC/DRC、bit/XSA一致性检查。不得用HLS估计替代物理实现。
4. 从新 XSA 生成 `m14_board_v31_platform`，运行
   `experiments/board_v31_20261019/build_software.ps1` 生成 test/loader/diag 三个正式 ELF。
5. 运行 `package.py`（含硬件审计门槛）冻结本版 package；先离线检查所有路径和 hash。
6. 用 `standalone/initialize_selftest.ps1` 完整初始化并先做 PL DDR 自测；再用
   `-RetainHardware -RejectPsDdrAddress` 验证 PS DDR 地址拒绝（仅同一已核实镜像）。
7. 用配套 `program_board_tcp.ps1` 加载 canonical BF16，完成目标PL DDR逐块/全份CRC及首尾sentinel；
   初次从v3切换v3.1不得retain。若先由自测脚本完成同一新包完整初始化且无其他改动，后续loader可retain。
8. 运行 v3.1 完整 campaign，再用 `scripts/summarize_acceptance.py` 严格汇总；
   增加PL DDR范围/校准/loader错误路径，真实运行与软件注入须分别标明。
9. 与本轮 v3 同板基线比较 IP/A53 P50/P95/max、加载速度、稳定性；不预先承诺PL DDR更快。
10. 完成可移植交付目录、ZIP和SHA256清单。**交付打包脚本尚未编写，文件夹/ZIP尚未生成。**

## 其他注意

- 数学源码、v3已验收报告及交付ZIP不改；原v3包继续作为基线。
- `standalone_v3_baseline/` 是隔离的旧版测试脚本，写出的记录在新模块，勿误用为v3.1部署入口。
- `experiments/.../validate_host.py` 和 `compare_results.py` 来自旧分支，仍需审核后再使用，
  不要将其旧200MHz模拟数据当作本次测试。
- README/BOARD_PLAN已修复明显旧地址和断连说明，仍需在最终验收后更新状态与真实结果。
- 更多修复依据见 `reports/board_v31_20261019/MAIN_TAKEOVER.md`。
