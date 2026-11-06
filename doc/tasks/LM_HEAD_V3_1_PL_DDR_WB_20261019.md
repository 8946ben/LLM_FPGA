# lm_head v3.1：PL DDR 迁移与真实板卡验收（workbuddy 执行任务书）

接管更新（2026-10-19）：原任务 `t-mvf361si-01k-ktoa` 已 failed，用户随后明确要求
“不用交给 wb 了，你来完成吧”。以下任务目标与验收标准继续有效，执行归属改为
当前 Codex 主模型；不再重派 workbuddy。原执行会话已停止，原始 RESULT/BLOCKER
保留为历史交接记录，不能将其旧连接状态或“构建完成”文字当作当前验收结果。

## 授权与目标

用户要求：“先来做 PL DDR 迁移并进行验收，形成一个 v3.1 的版本去板卡验收，可以通过 luyou 派发给 wb”。
用户随后确认：“已释放，可由 wb 独占使用”。这是新的明确板测安排，替代此前另一 agent 占板的限制。
规划方为 codex-1，执行节点为 workbuddy；由你独占板卡和本次实现写入，规划方不并行操作硬件。

用户连接更新（2026-10-19，初次连通性检查之后）：用户回复“已连接，请让 wb 后续复查”。
此前无 JTAG/有线断开的记录仅代表早期检查，不应直接沿用为最终板测阻塞结论。
进入 M2 前由 workbuddy 重新枚举 JTAG、核对有线链路/IP，并在启动匹配 loader 后检查服务；
保存新的带时间记录。此消息是用户对物理连接的确认，不能代替实际连通性或验收 PASS。

请先读 `LUYOU_TASK_FILE`、根 `AGENTS.md` 顶部最新安排和本文件，然后执行。
仅在 `D:/program/LLM_FPGA` 下修改项目文件，不 commit、不 push、不向第三方发消息，不再派发其他节点。
使用本节点当前默认模型；不要自行切换模型或执行器。

目标是完成可验收的 **lm_head v3.1（200 MHz，完整词表，计算数据走 PL DDR）**，并完成真实板测和交付整理。
不是仅写方案或仅生成脚本；如外部依赖确实阻塞，保留已完成产物并按后文升级，不虚报 PASS。

## 范围

- 权重、hidden、history、可选完整 logits 都从/向 PL DDR 访问。
- PS 程序、栈、堆、TCP 接收暂存、mailbox 可保留 PS DDR。
- 完整词表 151936、hidden 896、canonical BF16 输入/权重、FP32 计算和原 repetition penalty/argmax 语义保持。
- 原 v3 H8/V1、16 槽交错累加、相邻 lane 规约算术顺序保持；尽量复用其数值源码。
- 本轮不做稀疏化、不实现上游直接供权重、不开展公共 ABI/M06/整体 LLM 集成。
- 既有 v3 源码、已验收 reports、交付文件夹和 ZIP 均不修改、不覆盖，不改根 `开发日志.html/md`。
- 正常情况下不需要重新向用户请求初始化或加载授权；只在需要人工断电/接线等动作时向规划方升级。

## 真源、工具与建议输出位置

- 总规划：`doc/LM_HEAD_V4_PLAN_20261019.md`，本任务覆盖其 P0/P1/P1 对应验收，版本名称改为 v3.1。
- 约束说明：`doc/0924/PS_PL 全模块参数与接口字段说明书.md`、`PS_PL 全模块架构、详细设计与统一集成实施计划.md`。
- v3 已测源码：`module_14_lm_head_v2/experiments/board200_20261019/`。
- v3 原始证据：`module_14_lm_head_v2/reports/board200_20261019/RESULT.md`、`comparison.json`、`hardware/`、`package/`。
- v3 成品参考：`deliverables/20261019_M14_V3_r1/M14_V3_20261019_r1/module_14_lm_head_v3/`。
- canonical BF16 权重 272269312 bytes，SHA256=`4e96b0df6d274768cbb7e72404011853d23349999b658dc2f4dfb3c431ea223f`；从现有 package/资产清单定位真实文件，勿重新量化或误用 FP16。
- v3 build_config=`0x20c08011`；v3 bit SHA256=`2f639238441566fef6e76dcb2f1e66b3f2e21f859e25d9da42fa15580505a575`。
- v3 基线：IP median/P95=117.751805/117.751890 ms；A53 median=117.76734767347673 ms，名义 200 MHz。
- 板卡 AXU9EGB/xczu9eg-ffvb1156-2-i；本地有 `AXU9EGB开发板用户手册.pdf`。
- G:/Xilinx 2021.1 的 Vivado、Vitis_HLS、Vitis/xsct；先核实可用性。Python 可用 `C:/Users/ben/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。
- PC 有线用户先前配置 192.168.0.12/24，板卡 loader 计划 192.168.0.190/24；读取现有配置核实，不擅自改变 PC 网络设置。
- 建议新模块 `module_14_lm_head_v3_1/`，新硬件/实验报告均放该目录；交付根 `deliverables/20261019_M14_V3_1_r1/`（若实际完成日期变化用真实日期）。不要用 v3 文件夹存新版本。

## 步骤与里程碑

### M0：基线与板级资料

1. 固定数值源码、权重和 v3 资产 hash 清单，记录已有改动，不还原用户或其他任务的文件。
2. 查找可复用 MIG/XDC/板级约束，核实 DDR 颗粒、DQ/DQS/地址/控制、BANK64/65、参考时钟和复位。
   说明书记录 PL DDR 2 GiB/物理 32 bit、旧工程 MIG AXI 128 bit/UI 266.5 MHz，但不是本次已验证配置。
   历史外部 `D:/FPGA_PRO/llme_SDWeight_proj/.../system_wrapper.bd` 在规划方本地不存在；可检查当前真实文件，不能伪造引脚或直接把旧文字当作可用 XDC。
   可只读检索仓库 `realFpga/`、历史 XSA/工程及明确引用的本地旧工程；实际修改仅在本工作区。
3. 不确定颗粒/引脚、工具缺失或权限问题需升级；不能试错烧写未核实的 DDR 约束。

### M1：PL DDR 通路和配套软件

1. 从 v3 建独立模块和新 BD，引入 DDR4 MIG，M14 用户逻辑保持 200 MHz。
2. M14 数据 masters 经互连直接访问 MIG；CPU 经 HPM 的 PL 窗口访问 MIG，AXI-Lite 控制另保留。
   正确处理 MIG UI 与用户时钟、CDC、复位同步和 `init_calib_complete` 超时门控，校准前禁止 DDR 访问。
3. 导出实际 A53 物理地址/HLS 地址/MIG 偏移和范围，地址位宽/64-bit 指针/loader/驱动一致；不能只换旧基址，不能隐式落回 PS DDR。
4. PL DDR 分配权重、hidden、history、logits，检查容量/对齐/边界/重叠。PS mailbox 与软件保留原机制。
5. 新增明确镜像身份、build_config、IP version/capability、RUN_PROFILE 及硬件 profile，不能冒用 v3 身份。
   保留数学 ABI 语义；若控制字段扩展必须在新驱动、软件、package、解析器间一致，并说明兼容性。
6. 适配 TCP loader 到 PL DDR 窗口，保留已修复的 tcp_output 重试与断线处理；先明确 BSP/MMU/cache 属性和写完成屏障。
   主机 SHA256、每块目标 PL DDR 回读 CRC32、完整目标 DDR CRC32、首尾 sentinel 全通过后才运行数值验收。
   禁止以接收缓冲 CRC 冒充目标内存 CRC；权重仍走网口，不默认 JTAG 上传整份 272 MB。
7. 生成 bit/XSA/PS init/ELF/loader/profile 配套 package，完整实现检查 5 ns 时序、CDC、约束覆盖及 DRC；保留原始日志。
   PS DDR 与 PL DDR 镜像切换必须完整初始化；禁止使用 -RetainHardware 混用旧镜像和 PS init。

### M2：真实板卡验收（已授权，执行节点独占）

1. 先检查板卡/JTAG/网口连接；任何新发现的并发占用立即停止硬件操作并升级，不强抢板卡或终止其他任务进程。
2. 记录实际配置、时钟、校准状态，做 PL DDR 数据模式/地址线/边界区间读写、范围拒绝、CRC/sentinel 与初始化超时等测试。
3. 使用 canonical BF16 完整网口加载，记录加载时间、吞吐及全部校验。
4. 运行现有 8 步生产结果和 8 步完整 FP32 logits 对比，均应逐位一致；原 penalty/同分规则不变。
5. 运行原 bad ABI/flags/dimension/numeric 等错误路径、错误 golden 被正确拒绝，并增加 PL DDR profile/地址/校准与 loader 目标边界错误测试。
   不可达硬件状态不强行伪造，明确软件注入、仿真与物理测试的区别。
6. 至少 3 次预热、30 次独立单调用计时，报告 IP cycles、按实际 profile 换算的 median/P95/max 和 A53 wall；1000 次连续调用稳定性。
   优先在同一板卡/相同输入和统计方法下与 v3 做 A/B，必要时临时加载匹配的 v3 基线包，再完整切换到 v3.1。
   若不能重跑 v3，明确标注引用 2026-10-19 历史基线，不能冒称本轮同板 A/B。
7. 记录连续读写吞吐和真实 lm_head 读取量/背压中可获取的证据；未实现总线监测时明确限制，不伪造带宽数据。
8. PL DDR 不预先承诺加速，若性能回退也应报告真实比例与原因，不能用更换存储本身充当性能 PASS。

### M3：交付与收尾

- 形成 `lm_head v3.1` 独立目录、必要源码、约束与 MIG 配置、构建/加载/验收脚本、可移植配套 package。
- 报告数值、内存、时序、性能、稳定性分别 PASS/FAIL/NOT_RUN；所有结论绑定原始记录和 artifact hash。
- 参考 v3 的交付结构生成新交付文件夹/ZIP/内部 SHA256SUMS/ZIP 外部 SHA256；离线复核文件清单、归档和脚本路径。
- 最终写明板卡所留镜像、DDR 是否加载、A53 程序状态、你启动的服务/进程、使用资源及收尾情况。
- 规划方在任务终态后独立复核；luyou done 不自动等于工程通过。

## 进度、瓶颈、时间与回报格式

在新模块目录维护 `PROGRESS.json`：当前 M0/M1/M2/M3、最近可验证成果、证据路径、下一步、阻塞和时间。
正常综合/实现有可见进度时等待即可，不频繁重启或重复建工程。

单次 luyou 任务时限为 7200 秒，按注入的 timeoutSec 核实；接近时限仍未完成时安全交接，记录真实状态与续办命令，不能压缩验收或虚报完成。
同一问题经 3 条有实质区别的路径仍失败，或连续 60 分钟没有新可验证进展，停止该问题重试并升级。
明确需要人工断电/接线、配额、权限或决策时立即升级，不耗满预算；原始重试预算不因续任务重置。

升级：写根目录 `BLOCKER-<LUYOU_TASK_ID>.md`，含版本/环境、最小复现、尝试和证据、改动、进程和板卡状态、所需主模型动作；停止同一工作树写入并安全交接。
在根目录写任务专属 `RESULT-<LUYOU_TASK_ID>.md`，前两行：

```text
# RESULT <LUYOU_TASK_ID> · 具体结论
[luyou:<LUYOU_TASK_ID>:done]
```

未完成或需主模型接手时第二行用 failed，并 `luyou report --status failed --summary "ESCALATE_MAIN: ..."`，不要把等待人工动作记成硬件功能失败。
成功也必须显式 `luyou report --task <ID> --status done --summary "..." --artifacts "任务专属RESULT;实际报告路径;交付目录" --result-file "任务专属RESULT"`。
不要写公共 RESULT.md，也不要覆盖旧任务证据。不依赖聊天文字代替文件和 report。
