# LM Head V2 开发与板测交接（2026-10-09）

## 2026-10-19 lm_head v3 命名、交付与板卡占用（最新）

- 用户已将通过200 MHz真实板测的版本命名为 **lm_head v3**；发布名v3，ABI仍为2，
  HLS top仍为lm_head_v2，IP版本2.1，build_config=0x20c08011；已测试的源/镜像字节保留。
- 新交付目录：`deliverables/20261019_M14_V3_r1/M14_V3_20261019_r1/`；
  模块目录`module_14_lm_head_v3/`，完整936文件；ZIP 278245732 bytes，
  SHA256 `a411ad6f181f653cd6bcc692427f72fc4bfa388a7d7c7c7cc5ccafcb4eb261a2`。
  压缩前/解压后离线复核PASS，完整源/IP/驱动/镜像/BF16资产/同板原始证据齐备；尚未发送。
- 开发日志已更新至v3实测与交付，原53条历史记录及Markdown保留。发布说明：
  `doc/LM_HEAD_V3_RELEASE_20261019.md`。
- **用户最新要求：板卡由另一agent使用。本任务仅做本地文件整理，不连接或读取JTAG，
  不做网络探测、初始化、加载、验收或任何板卡操作，也不查询当前镜像/DDR状态。**
  下方实板状态是先前验收结束时的历史记录，后续板卡操作需用户新的明确安排。

## 2026-10-19 200 MHz 上板验收 PASS（当前，优先于下文）

- 用户已连接板卡并授权上板测试；有线 PC 为 `192.168.0.12/24`，本次 loader 为
  `192.168.0.190:1414`。不需要更改 PC 网卡；旧冻结 loader 的 `.8` 网段仍保留。
- 正式独立 200 MHz 候选：`module_14_lm_head_v2/experiments/board200_20261019/`。
  算术源码与 reduce_layers 候选逐字节一致；42 份 RTL 仅顶层 build_config 常量变化。
  新身份 `0x20c08011`（CLOCK_CODE=3、revision=2），HLS IP VLNV 2.1。
- 新 bit/XSA/PS init/test ELF/修复版 TCP loader 配套包已生成：
  `module_14_lm_head_v2/reports/board200_20261019/package/`。
  布线后 WNS +0.943 ns、WHS +0.010 ns、WPWS +1.000 ns，约束检查问题 0；
  LUT23148、FF40194、BRAM tile22、DSP59；DRC Error/Critical Warning 均0，192 Warning/52 Advisory保留。
- 冻结 100 MHz 同板 55 项复测 PASS（含30独立计时、1000连续调用）；IP median/P95
  224.868020 ms，campaign `reports/board_runs/20261019_112423_810_acceptance/`。
- 200 MHz 已烧录，PS 时钟链寄存器回读 PASS；完整 BF16 TCP 加载/DDR/sentinel PASS，
  8.3686665 s、31.0271953 MiB/s。8 步生产和完整 logits SHA256、错误路径、30次独立计时、
  1000次连续稳定性均通过；55项campaign及严格汇总 PASS。
  campaign `module_14_lm_head_v2/reports/board_runs/20261019_114631_333_acceptance/`。
- 200 MHz IP median/P95/max：117.751805/117.751890/117.751990 ms；
  A53 wall median/P95：117.767347673/117.767677677 ms；1000次连续调用117.759180272 s。
  相对同板100 MHz：IP median加速1.909677903倍，延迟降低47.635148%；A53 wall加速1.909579805倍。
- 报告：`module_14_lm_head_v2/reports/board200_20261019/RESULT.md`；
  `comparison.json`、两份严格summary、时钟回读、包内ARTIFACTS.sha256及证据清单均保留。
- 本任务该次验收结束时无运行中板测或构建，当时保留200 MHz PL/DDR和已校验BF16权重；
  后续当前板卡状态以用户占用安排为准，本任务不再现场查询；断电后需重载。
  后续使用新包时同时传入 `-PackageDir`、`-LoaderPackageDir`、`-BoardIP 192.168.0.190`。
  切换100/200版本需完整初始化，不用-RetainHardware。原100 MHz源码及原候选交付ZIP未改。

## 2026-10-16 工具恢复后续办（历史诊断）

- G:已由用户重新连接，Vitis/Vivado 2021.1可用；不再等待工具盘。
- reduce_layers候选Vitis CSim通过。生产尺寸5ns/1.35ns综合：顶层3.650ns / 273.97MHz估算，
  归约三层II=1、每行102cycles，dot II=1/159cycles；LUT30085、FF32925、BRAM_18K95、DSP59。
- IP隔离导出成功；独立BD实际PL0=199.998001MHz。独立物理项目：
  `module_14_lm_head_v2/board/build/m14_v2_200_layers/`，已完成200MHz完整布局布线；WNS+1.067ns、WHS+0.010ns、WPWS+1.000ns，约束/时钟问题0。
  post-route LUT23161、FF40192、BRAM tile22、DSP59；DRC Error/Critical Warning均0，普通DSP警告保留。
  进程已于2026-10-16T23:03:06+08:00退出，无本轮运行中构建，未生成/下载bit或板测。
- 首次CoSim C向量包装器按生产权重depth复制64词表测试缓冲而越界。
  新测试副本只修正仿真接口depth，源码绑定验证算术未变；`cosim_full_hidden`停滞后已保留并停止。
  短工程`rtl896`完成15笔事务，含512个随机raw logits的C post-check全部PASS；
  应用已知hidden_size_r向量命名修复后XSIM重跑通过，原始自动CoSim失败日志保留。
- 进程完成前不得把HLS273.97MHz当作布线后或实板可达频率。当前详细状态与日志位置见
  `module_14_lm_head_v2/reports/frequency_200_20261016/reduce_layers/RESULT.md`及`hls_summary.json`。

## 2026-10-16 续办：归约候选完成主机回归（最新）

- 本轮目标仍为独立M14 200 MHz，未开展公共ABI/原生M06/整体LLM集成。
- 隔离候选`module_14_lm_head_v2/experiments/frequency_200_20261016/reduce_layers/`
  将归约层改为独立数组并取消输入写回，保持FP32加法配对/舍入顺序；生产源码和交付包未改。
- 主机g++回归PASS：原版/候选归约50,004组逐位一致；两版整核分别在hidden=896、vocab=64下
  通过8组/512个raw logits逐位对照，top-1/score/CRC和已有边界测试通过。
- 测试只借用2017.4仿真头文件，不是Vitis CSim、HLS综合、RTL、时序或板测通过。
- 本轮沙箱及本机均再次看不到G:工具盘；已询问用户恢复或新路径。
  新候选的II/时钟/资源未知，未开始2021.1综合。旧187.71MHz结果只属于未改源码的首次诊断。
- 恢复工具后运行候选`run_hls.ps1 -Mode csim/csynth/cosim`，比较同5ns/1.35ns下的
  归约II/每行周期/时钟/资源，随后决定物理实现。脚本拒绝覆盖已有工程。
- 结果与源码绑定：`module_14_lm_head_v2/reports/frequency_200_20261016/reduce_layers/RESULT.md`、
  `native_validation.json`、`tested_sources.json`、`source.diff`。

## 2026-10-16 当前范围与200 MHz初步诊断（优先于旧待办）

- 用户明确本轮不做“公共ABI / 原生M06 / 整体LLM集成”；RSystem已从开发日志当前路线表和待办移除。
  历史记录保留，但不再以这些条件阻塞独立模块升频。250 MHz只保留历史评估，本轮目标为200 MHz。
- 已保留生产100 MHz源码、bit/XSA/ELF、原HLS/实现工程和交付包，新增隔离诊断目录。
- G:工具盘初始不可见，用户表示恢复后路径已重新可见；实际完成Vitis HLS 2021.1、5ns/1.35ns诊断。
- 综合exit=0，进程于2026-10-16T19:25:45+08:00退出；HLS估算5.328ns / 187.71MHz，**尚未达到200 MHz目标**。
- dot_word_loop II=1保持；dot每行调度152→159cycles，归约各层II3→5、每行100→147cycles。
  HLS资源为44664 LUT / 37664 FF / 95 BRAM_18K / 59 DSP，不能与旧post-route资源直接混为同口径。
- 下一候选优先评估归约层临时数组/固定索引和局部CE控制，保持FP32舍入及加法树。
  尚未改算法、运行新RTL/布局布线/板测；当前无运行中构建，不把187.71MHz当实板可达频率。
- 分析：`module_14_lm_head_v2/reports/frequency_200_20261016/ANALYSIS.md`；
  结果：同目录`diagnostic_summary.json`、`hls_5ns/`及`DIAGNOSTIC.sha256`。
- 后续验证仍遵守canonical BF16 TCP加载与DDR/sentinel门槛；正式200 MHz候选需同步clock/build身份、
  host周期换算及匹配的bit/XSA/PS init/ELF。

## 2026-10-10 汇总交付包（最新）

- 已按 0924 两份统一集成规范生成 M14_V2_20261010_r1，供发送给喻燕萍；尚未发送。
- ZIP：`deliverables/20261010_M14_V2_r1/M14_V2_20261010_r1.zip`，252,055,661 bytes。
- SHA256：`215b7bf756c57e637fa2943baacef582307fc53db545a1a42f50aca7d76aa514`。
- 已保留用户人工修改的 README 措辞及 `交付说明.md` 改名，重算根目录清单后重新压缩；
  压缩前、解压后离线复核与冻结二进制校验 PASS。模块文件不变，旧清单/验证记录已备份。
- 完整包含源码/IP/驱动/机器接口表/报告/全部 BF16 资产/原始板测证据；压缩前与解压后
  离线复核、Vivado IP Catalog、脚本语法和冻结二进制 hash 均通过。
- 状态为“独立模块板测通过、待统一集成候选版”。公共 ABI、原生 M06、Prefill 36/64、
  其他性能矩阵、边界地址和 HP2 APM 仍待完成；此次打包未操作板卡。
- 详细记录：`module_14_lm_head_v2/reports/delivery_20261010/DELIVERY_REPORT.md`。

## 2026-10-10 恢复与实板验收更新（最新，优先于下文）

- 用户恢复工作并再次主电源重启；PS/PL 正常初始化。已按要求切换大权重到网口。
- 独立 TCP loader 完整 BF16 上传、DDR 每块/整份 CRC32、sentinel 与 6 项错误路径
  板测通过；修复分段小请求回应的 tcp_output 重试。端到端实测 8.33–8.39 秒，
  约 31 MiB/s，较 30 分钟 JTAG 大文件阶段约快 215 倍。
- `standalone/program_board_tcp.ps1` 默认使用并校验
  `reports/tcp_loader_package_20261010/`。复用冻结包再传一次、切回原数值 ELF 的
  step_00 生产/debug 冒烟均 PASS；不必重新生成 BSP。旧 JTAG 脚本保留显式回退。
- 完整 55-run Decode/penalty-ON campaign 严格 PASS：8-step 生产/debug logits hash、
  score bits/CRC、4 类负例、受控错误 CRC 计时、30 次独立性能与 1,000 次稳定性。
  campaign 为 `reports/board_runs/20261010_104006_168_acceptance/`，summary failures=[]。
- IP median/P95=224.868020 ms；A53 wall median=224.886284 ms、P95=224.886629 ms；
  1,000 次耗时 224.8792944 s。未把 1,000-repeat 最终 mailbox 当成独立性能样本。
- 生产 HLS、PL bit/XSA、数值 test ELF 和原 BF16 输入未改；昨日 PAUSED/初版网口失败
  与本轮修复后 PASS 证据均保留，STOP_REQUESTED 已归档（恢复指令解除暂停）。
- 当前完成独立 Decode 验收，尚未完成全模式/APM/公共 ABI/M06 V2 真实 BF16 trace
  或整体集成；当前仓库未检索到公共 V2 ABI 头文件或对应真实 trace，后续需要提供。

完整报告：`module_14_lm_head_v2/reports/20261010_BOARD_ACCEPTANCE.md`。
使用步骤：`module_14_lm_head_v2/standalone/TCP_WEIGHT_LOADING.md`。
当前板卡停留在最后一次成功的 step_00 debug 数值程序，权重仍在 DDR；该程序没有
以太网服务，ping/TCP 不响应不等于 FPGA/DAP 故障。下一次上传才启动 TCP loader。

## 2026-10-09 收工更新（最新，优先于下文）

用户要求今天完成小阶段后停止，当前已停止板测进程。

- 用户已授权重初始化/权重加载，并实际断电重启；本轮 JTAG PS init、PL program、
  272,269,312-byte BF16 加载和独立首尾 sentinel 均 PASS。有线 PC 已由用户改成
  `192.168.8.12/24`。
- 8-step 生产/debug 严格数值及全 logits SHA256 全部 PASS，受控 golden-failure
  wall_ticks 回归 PASS，BAD_ABI/BAD_FLAGS 两项负例 PASS；隔离 campaign 19 条完成记录，
  `reports/board_runs/20261009_205439_951_acceptance/campaign.json` 状态 PAUSED。
- BAD_DIMENSION/NUMERIC_ERROR、30 次性能采样和 1,000 次稳定性尚未执行，不能声明整体验收。
- 已根据用户请求新增独立 TCP 权重加载器、主机发送器和 CRC32 DDR 回读校验，ELF 编译、
  离线协议边界测试通过；**未启动新 loader、未进行网口上板测试**。
- 明天优先验证 `standalone/program_board_tcp.ps1`；参考根目录 AGENTS.md 和
  `module_14_lm_head_v2/standalone/TCP_WEIGHT_LOADING.md`。保留初始化时可用
  `-RetainHardware`；只在没有板测运行时启动。
- 板卡若不断电，明天先只读检查 retained state；若断电，DDR 丢失，优先网口重载。
  `reports/board_runs/STOP_REQUESTED` 保留防止误续跑，用户继续后再删除。

详细证据、暂停原因与下一步见
`module_14_lm_head_v2/reports/20261009_BOARD_STAGE_PAUSED.md`。

## 2026-10-09 续办更新（优先读取）

下文原交接基线保留用于审计；其“数值差异未闭环”的状态已经更新：

- 根因是旧 Python 最后 8 lane 的归约树与 C++/RTL 不一致；修正为相邻 pair 后，
  step_00 归档的 151,936 个 logits **全部逐位匹配**，score bits/CRC 完全一致。
- `module_14_lm_head_v2/NUMERIC_CONTRACT.md` 冻结独立模块严格数值合同；8-step
  golden 重算且 token 不变，旧 golden 已备份，权重/hidden/history 未改动。
- Python 8/8、CSim、含归约反例的 7/7 RTL CoSim、资产/source contract、ELF 构建
  及失败采集 mock 回归通过。没有放宽校验，也没有修改生产 HLS/RTL。
- wall_ticks 与 run_step 的失败记录顺序已修复。新 ELF SHA256 为
  `cf22f2cc8b8c812a1848fc2f475ed67afce589c440bed34940d3b0429a3cfabd`，281,336 bytes。
- 当前 runner 默认使用 `reports/board_package_20261009/`；旧包保留，bit/XSA 不变。
- 本轮只读 JTAG 检查 DAP 报 AXI AP transaction error，不能读取 DDR，后一次没有
  可用 PSU target；未复位/下载板卡，完整初始化与权重加载仍需用户确认。
- 有线 PC 为 `192.168.0.12/24`，与旧网络固件 `192.168.8.190/24` 不同子网；
  ping 无 FPGA 回复。本轮 M14 standalone 使用 JTAG，没有网络服务，网卡配置
  与 DAP 错误无关；未修改电脑 IP。

完整证据与后续门禁见
`module_14_lm_head_v2/reports/20261009_NUMERIC_CLOSURE.md`。

## 1. 交接结论

M14 LM Head V2 的 HLS、RTL CoSim、Vivado 2021.1 实现、bitstream/XSA、standalone
驱动与板测工具链已经完成。2026-09-30 的首次实板测试证明：

- 生产尺寸任务能够在 AXU9EGB/XCZU9EG 上完整运行；
- step_00 的 top-1 token 精确命中 golden：`104198`；
- IP 计数为 `22,486,802` cycle，100 MHz 下为 `224.86802 ms`；
- 旧版实测为约 `11.09 s`，按 IP 周期口径约提升 `49.3x`；
- FP32 logits 与主机 golden 存在微小逐位差异，导致 score/CRC 的严格校验失败；
- 当前阶段结论是：**功能 token 与性能已通过首步冒烟，bit-exact 数值合同尚未闭环**。

下一会话应先完成数值差异根因与验收标准冻结，再继续 8-step、重复性能、稳定性和
整体模型集成。不要在未分析完差异前直接修改 golden CRC 或放宽所有校验。

## 2. 项目目标与边界

目标板卡为 ALINX AXU9EGB，器件为 XCZU9EG。当前工作聚焦独立的 M14 LM Head V2，
总体顺序为：

1. 完成模块升级与离线验证；
2. 在板上独立测试准确度、性能和稳定性；
3. 单模块门槛全部通过后，再集成到整体大模型框架。

优化计划位于：

- `D:\program\LLM_FPGA\doc\0924\M14_LM_HEAD_V2优化实施计划.md`

模块根目录：

- `D:\program\LLM_FPGA\module_14_lm_head_v2`

旧 `module16_lm_head_hls` 保留为 FP16、单 MAC、II=8、约 11.09 s 的基线，没有被覆盖。

## 3. 已实现的硬件结构

生产数据路径如下：

```text
BF16 hidden 128-bit read
  -> 8-bank FP32 hidden cache
  -> BF16 weight 128-bit stream
  -> 8 parallel FP32 products/cycle
  -> 16-way interleaved accumulators
  -> two-context FIFO / DATAFLOW reduction
  -> history bitmap repetition penalty
  -> streaming argmax
  -> optional pre-penalty FP32 logits
```

关键点：

- hidden 与 weight 为 BF16；点积、penalty 与 argmax 使用 FP32；
- 每拍处理 8 个 BF16 元素，对应 8 个 FP32 multiplier 和 8 个 FP32 adder；
- 16 组交错累加器把同一 accumulator 的反馈距离拉到 16；
- `dot_word_loop` 综合 achieved II=1；
- DATAFLOW 让下一词表行的点积与上一行的归约重叠；
- 四个 M_AXI 口为 128-bit 数据、64-bit 地址；
- 生产配置 H8/V1、100 MHz，默认 `write_logits=0`；
- 一行权重为 112 个 128-bit beat，完整词表为 17,016,832 beat。

## 4. 已完成的离线验证

### 4.1 Vitis HLS 2021.1

- CSim 通过；
- Verilog RTL CoSim 6/6 事务通过；
- 生产综合 `dot_word_loop achieved II=1`；
- 资源中有 8 个点积 FP32 multiplier 和 8 个点积 FP32 adder；
- HLS 估算时钟周期为 8.660 ns；
- 资源估算为 95 BRAM18K、59 DSP、35,124 FF、43,280 LUT；
- IP 已导出为 `user.org:llm_fpga:lm_head_v2:2.0`。

2021.1 CoSim 有一个已处理的工具兼容问题：RTL 标量端口名为 `hidden_size_r`，但 C
wrapper 只生成 `hidden_size` 向量。脚本只在严格匹配该问题时复制别名并重跑完整仿真。

证据：

- `module_14_lm_head_v2/reports/20260930_HLS_VALIDATION_2021_1.md`

### 4.2 Vivado 2021.1

- 100 MHz post-route WNS `+3.649 ns`，WHS `+0.010 ns`；
- 资源：31,290 CLB LUT、42,618 register、22 BRAM tile、59 DSP；
- DRC：0 error、0 critical warning、301 warning、52 advisory；
- 四路 M_AXI 均连接 HP2；
- 四路均验证 64-bit 地址；
- 显式地址窗为 `DDR_LOW=[0, 2 GiB)`、`DDR_HIGH=[32 GiB, 34 GiB)`；
- AXI-Lite 控制口为 `0xA0000000 / 64 KiB`。

证据：

- `module_14_lm_head_v2/reports/20260930_VIVADO_VALIDATION_2021_1.md`

### 4.3 软件与资产

- mailbox 已从 128-byte V1 升级为 **256-byte V2**；
- V2 回传完整 perf/workload counters、build config、capabilities、result job/status 和
  timer frequency；
- 正常任务保持严格 host validation；
- 只有 `run_negative.ps1` 显式开启 bypass 时，非法任务才会送入硬件；
- `record_result()` 会在 golden 校验失败时保留硬件结果，便于排错；
- Python reference 4/4 通过；
- source contract 为 33 个参数、34 个 AXI-Lite port；
- 8 个 trace 资产校验通过。

最终 ELF：

| 项目 | 值 |
| --- | --- |
| 路径 | `module_14_lm_head_v2/standalone/build/m14_v2_test.elf` |
| 文件大小 | 281,312 bytes |
| SHA256 | `001613bef87a76f2d394c2083a2ca620bcf913b711a3f0ce95af6cf93f70cc2c` |
| map SHA256 | `a3fc28f27dd0b88dfe26b155d3deb23e5aec28055cd7fcceefb1124532f3afe2` |

板测包中的 ELF 与该文件一致。构建说明：

- `module_14_lm_head_v2/reports/20260930_STANDALONE_BUILD_2021_1.md`

## 5. 固定资产与哈希

BF16 权重：

- 路径：`artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin`
- 大小：272,269,312 bytes
- SHA256：`4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f`

8-step V2 golden token：

```text
step_00 104198
step_01 48
step_02 16948
step_03 3837
step_04 67071
step_05 102661
step_06 99718
step_07 100048
```

注意：这些 hidden trace 是旧 FP16 最终 RMS trace 转成的 BF16，适合单模块固定输入验收，
不能代替完整 V2 端到端 trace。整体集成前必须从 M06 V2 记录真实 BF16 trace，并冻结
FP32 penalty/argmax 的公共语义。旧语义下 step_07 token 为 100013，V2 FP32 语义为
100048，这个差异已经记录，不应误判为本次硬件随机错误。

板测归档：

| 资产 | SHA256 |
| --- | --- |
| XSA | `df88b0a2ae6b6a99d00bf6cd0f38970e4a08356f3bd8bdedd170a8a1902c8a9c` |
| bitstream | `d6223bcf8b36f5cbe2032c4aa6e75f248438fbe9faa4e6aae36ee41951a736ef` |
| ELF | `001613bef87a76f2d394c2083a2ca620bcf913b711a3f0ce95af6cf93f70cc2c` |

归档目录：`module_14_lm_head_v2/reports/board_package_20260930/`。

## 6. 2026-09-30 实板执行记录

### 6.1 JTAG 与下载

Vivado/Vitis/XSCT 路径为 `G:\Xilinx`，版本为 2021.1。只读 JTAG 探测成功枚举：

- PS TAP / PMU / PL / PSU；
- 4 个 Cortex-A53；
- 2 个 Cortex-R5。

只读证据：

- `module_14_lm_head_v2/reports/20260930_BOARD_READY_CHECK.md`
- `module_14_lm_head_v2/reports/board_runs/20260930_jtag_probe.log`

首次 program/load 在 PL 已配置后，因为 APU L2 仍在 reset 而停在 `stop`：

- `module_14_lm_head_v2/reports/board_runs/20260930_113830_program_and_load.log`

脚本后来把 `stop` 改为容错调用并执行 `rst -processor`，第二次成功完成 PS init、PL
program 和权重写入：

- `module_14_lm_head_v2/reports/board_runs/20260930_114043_program_and_load.log`

权重经 JTAG 传输约 30–31 分钟。板端首尾 4 个 word 与主机文件完全一致：

```text
first: 1026014250 949107743 3141778654 3164650136
last:  1000782885 1014709306 3154558069 1016708102
```

脚本还修复了一个重要问题：XSCT 经 `Tee-Object` 时可能掩盖内部失败并返回 0。现在
PowerShell wrapper 会扫描 `_ERROR`，并要求最终 PASS marker，不能只信 `$LASTEXITCODE`。

### 6.2 step_00 生产模式

完整结果位于：

- `module_14_lm_head_v2/reports/board_runs/20260930_122136_step_00/`

mailbox 因 exact CRC 不一致返回 FAIL，但硬件自身 `status_code=0`，任务完整结束。关键值：

| 字段 | 板上结果 |
| --- | ---: |
| selected token | 104198 |
| golden token | 104198 |
| selected score bits | 1101012901 |
| selected score | 20.015451431274414 |
| golden score | 20.015453338623047 |
| score 差值 | -1.9073486328125e-6（1 ULP） |
| output CRC | 2154663276 |
| golden CRC | 2463638146 |
| total cycles | 22,486,802 |
| compute cycles | 22,486,690 |
| weight wait cycles | 5,469,571 |
| dot active cycles | 17,016,832 |
| read beats | 17,018,131 |
| write beats | 0 |
| vocab rows | 151,936 |
| history words | 4,748 |
| build config | `0x10008011` |
| capabilities | `0x00000182` |
| IP time @ 100 MHz | 0.22486802 s |

`wall_ticks=0` 不是运行时间为 0，而是当前失败路径在读取结束时间之前调用
`record_result()`。本轮性能值只能使用 IP cycle 推导，不应报告 A53 wall time。下次代码
修改应先修复该记录顺序。

`reports/board_runs/results.json` 中第一条记录来自旧 ELF，只保留 FAIL 状态且结果字段为
0；第二条记录才是加入 `record_result()` 后的有效硬件结果。分析时不要对两条取平均。

### 6.3 全量 logits 调试模式

完整结果位于：

- `module_14_lm_head_v2/reports/board_runs/20260930_122201_step_00/`

调试模式写出 607,744-byte FP32 logits：

| 项目 | 值 |
| --- | --- |
| board logits SHA256 | `d7ada7553c6ff9bc48899776732e8269ca791874363cf64cc17a4aebe1245acc` |
| golden logits SHA256 | `be1f9b77d1ed6cecf64b2a30cf15ad713e38e9dedfc760391f1ac7a445875ed8` |
| total cycles | 22,486,841 |
| write beats | 37,984 |
| logits written | 1 |

离线统计文件：

- `module_14_lm_head_v2/reports/board_runs/20260930_122201_step_00/logits_comparison.json`
- 生成脚本：`module_14_lm_head_v2/scripts/analyze_board_logits.py`

统计结果：

| 指标 | 结果 |
| --- | ---: |
| 元素数 | 151,936 |
| 逐位完全相同 | 72,260（47.56%） |
| ULP ≤ 1 | 119,836（78.87%） |
| ULP ≤ 4 | 144,041（94.80%） |
| ULP p50 / p90 / p99 | 1 / 3 / 32 |
| 平均绝对误差 | 1.2308748e-7 |
| 最大绝对误差 | 1.9073486e-6 |
| 绝对误差 ≤ 1e-6 | 151,930 / 151,936 |
| board/golden argmax | 均为 token 104198 |

最大 ULP 为 16,384，出现在约 `1e-4` 的近零分数；其绝对误差仅 `5.96e-8` 或
`2.38e-7`。因此不能只按最大 ULP 判断误差严重程度。

## 7. 当前阻塞问题与判断

当前唯一直接阻塞 8-step 严格验收的问题是：**板上 HLS RTL 与 Python/C reference 的
FP32 reduction 结果不逐位一致**。

已知证据支持以下判断：

1. 输入尺寸、访问量、权重 beat、history word、build config 和 capabilities 均正确；
2. top-1 token 正确，top-10 中大多数分数为 0 或 1 ULP 差异；
3. 最大绝对误差只有约 `1.9e-6`；
4. 更可能的根因是 HLS 浮点 IP 的运算顺序、融合行为或舍入细节与主机 reference 不同；
5. 目前不能排除 reference reduction 树、FP32 cast 点或 penalty 运算顺序仍有差异。

CRC 覆盖 token/score 的精确 IEEE bit，因此 1 ULP 也必然失败。下一步需要决定并固化：

- RTL bit-exact reference：让软件严格模拟 HLS 浮点树；或
- 数值容差 + token/top-k 合同：CRC 只用于传输完整性，不再作为跨实现数值一致性；或
- 调整 RTL 运算，使其匹配当前 golden 的逐位结果。

这个决定必须结合整体框架的统一 ABI 和精度要求，不能只为了让 step_00 变绿而修改。

## 8. 下一会话建议执行顺序

### 阶段 A：只读恢复现场

1. 阅读本文件、`开发日志.md` 和三个 2021.1 报告；
2. 检查 `git status --short`，不要覆盖与 LM Head 无关的 wiki/图文改动；
3. 使用 2021.1 XSCT 做只读 JTAG probe；
4. 板卡在 2026-10-09 是否仍上电、PL 是否仍配置、DDR 是否仍保留均未知；
5. 如可能，先读取权重首尾 sentinel 或状态寄存器，确认资产是否仍在 DDR。

若板卡保持原配置和 DDR 内容，**不要重新运行 `program_board.ps1`**，因为重新传权重需
30 分钟以上。若板卡已经断电、重新配置或 DDR 丢失，再按状态变更流程取得用户确认后
执行 program/load。

### 阶段 B：离线闭环数值差异

1. 用 `analyze_board_logits.py` 保留当前 step_00 基线；
2. 对照 HLS CSim、RTL CoSim 与板上 logits，确认差异首先在哪一层出现；
3. 检查 16-way partial 的最终归约顺序、乘法/加法 cast 点、是否存在 fused operation；
4. 生成与 RTL 运算顺序完全一致的 bit-aware reference；
5. 比较 exact/absolute/relative/ULP、top-k 排名和 top-1 margin；
6. 在文档中冻结准确度门槛后，再改 manifest/CRC 检查逻辑。

### 阶段 C：修复测试框架的两个小问题

1. `main.c` 的失败路径先读取 `XTime_GetTime(&end)`，再记录 `wall_ticks`；
2. `run_step.ps1 -WriteLogits` 即使 hash 不匹配，也应先解析并保存 mailbox，再以明确状态
   退出，避免丢失计数器；
3. 清理或标记 `results.json` 中旧 ELF 产生的全零记录，禁止汇总脚本误用；
4. 重建 ELF 后更新 build report、board package 与哈希清单。

### 阶段 D：继续独立模块板测

数值合同冻结后再执行：

1. step_00 修复回归；
2. step_00..step_07 全部准确度测试；
3. 至少 30 次稳态性能，报告 median/P95；
4. 1,000 次稳定性测试；
5. BAD_ABI、BAD_FLAGS、BAD_DIMENSION、NUMERIC_ERROR 受控负向测试；
6. 完成单模块验收报告。

### 阶段 E：整体集成

只有单模块门槛通过后才开始：

1. 与公共 V2 ABI 对齐，消除驱动与 HLS 中重复枚举；
2. 接入 M06 V2 真实 BF16 trace；
3. 对齐共享权重地址、生命周期和缓存策略；
4. 做端到端 token、性能与长序列稳定性测试。

## 9. 常用命令

以下命令均从 `D:\program\LLM_FPGA\module_14_lm_head_v2` 执行。

离线比较现有 board logits：

```powershell
$py = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py .\scripts\analyze_board_logits.py `
  .\reports\board_runs\20260930_122201_step_00\raw_logits.fp32.bin `
  ..\artifacts\module14_v2_assets\trace\step_00\raw_logits.fp32.bin `
  --processed ..\artifacts\module14_v2_assets\trace\step_00\processed_scores.fp32.bin `
  --json .\reports\board_runs\20260930_122201_step_00\logits_comparison.json
```

重新编译 standalone ELF：

```powershell
.\standalone\scripts\build_elf.ps1
```

板卡与 DDR 已确认可复用时，执行单步：

```powershell
$py = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
.\standalone\run_step.ps1 -Step step_00 -PythonExe $py
.\standalone\run_step.ps1 -Step step_00 -WriteLogits -PythonExe $py
```

板卡断电或 DDR 丢失后，取得状态变更确认再重新配置和加载权重：

```powershell
.\standalone\program_board.ps1
```

受控负向测试：

```powershell
.\standalone\run_negative.ps1 -Test bad_abi -PythonExe $py
.\standalone\run_negative.ps1 -Test bad_flags -PythonExe $py
.\standalone\run_negative.ps1 -Test bad_dimension -PythonExe $py
.\standalone\run_negative.ps1 -Test numeric_error -PythonExe $py
```

## 10. 关键文件索引

| 内容 | 路径 |
| --- | --- |
| 模块说明 | `module_14_lm_head_v2/README.md` |
| 板测计划 | `module_14_lm_head_v2/BOARD_TEST_PLAN.md` |
| HLS 源码 | `module_14_lm_head_v2/src/` |
| HLS 头文件 | `module_14_lm_head_v2/include/` |
| reference | `module_14_lm_head_v2/reference/` |
| MMIO driver | `module_14_lm_head_v2/drivers/lm_head_v2_mmio.c` |
| standalone 主程序 | `module_14_lm_head_v2/standalone/src/main.c` |
| mailbox 定义 | `module_14_lm_head_v2/standalone/src/lm_head_v2_mailbox.h` |
| program/load wrapper | `module_14_lm_head_v2/standalone/program_board.ps1` |
| step wrapper | `module_14_lm_head_v2/standalone/run_step.ps1` |
| negative wrapper | `module_14_lm_head_v2/standalone/run_negative.ps1` |
| 实板原始输出 | `module_14_lm_head_v2/reports/board_runs/` |
| 板测固定包 | `module_14_lm_head_v2/reports/board_package_20260930/` |
| 持续开发日志 | `开发日志.md` |

## 11. 工作区注意事项

当前工作区并非干净状态。除本模块和本交接文档外，还存在 wiki、硬件图、图片、
`debug.log` 等未提交或未跟踪内容。这些内容与本次 LM Head V2 交接无关，不要清理、
reset 或覆盖。尤其不要改动：

- `doc/wiki/assets/wiki-init.js`
- `doc/wiki/assets/wiki.css`
- `doc/wiki/index.html`

开发与板测过程中继续把每次尝试、问题、修复和证据路径追加到 `开发日志.md`，不要只在
会话消息中记录。

## 12. 新会话建议首条指令

可以在新会话中直接发送：

> 请先阅读 `D:\program\LLM_FPGA\doc\LM_HEAD_V2_HANDOFF_20261009.md` 和
> `D:\program\LLM_FPGA\开发日志.md`，从“阶段 A：只读恢复现场”开始继续。先不要重新
> 下载 bitstream 或权重；先检查 2021.1 JTAG、当前 PL 状态和 DDR 权重 sentinel。随后
> 优先闭环 step_00 的 FP32 bit-exact 差异与 wall_ticks/run_step 记录问题，并持续更新
> 开发日志。
