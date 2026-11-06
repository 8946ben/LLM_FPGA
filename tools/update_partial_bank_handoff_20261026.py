"""Publish current handoff notes; no execution or frozen-source edits."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
M = ROOT / 'module_14_lm_head_v4'
B = M / 'reports/sim_memory_bank_20261026_r1'
F = M / 'reports/full_bank_cosim_20261026_r1'

def write(path, text):
    path.write_text(text.strip() + '\n', encoding='utf-8')

write(B/'RESULT.md', '''
# 仿真内存分bank修复：单元与前5块RTL独立验收通过

隔离模型每个bank最多1048576元素，按需独立分配；原核RTL、算法参数、原随机停顿和FIFO未改。原完整CoSim Fail及512MiB别名定位证据保持。

UNIT_REVIEW.json独立回放2093事件通过：512组512MiB别名对不再互相覆盖，15次边界拒绝正确；13次X返回中2次是范围内未写、11次是越界。32/128位和X/Z测试由实际XSim断言通过。UNIT_X_CLASSIFICATION.json给出细分类别，原冻结单元报告未改。

FULL_TV_INPUT_REVIEW.json确认原完整34105344拍TV逐记录重建的tiled/canonical SHA与冻结BF16一致，未截短输入。PREVIEW_REVIEW.json独立核对：1522个实际模型边界字节、40960拍权重读（320突发）、64通道、5120 raw、5120 key及2576写拍全部正确。该分段于北京时间12:29:37退出，模拟时间10.5931725ms；不作为正常DDR速度或完整M14延迟。

PROCESS_AFTER.json核对所属组为空、无锁，原133份冻结源及复用RTL/压力模型SHA不变。终态证据归档SHA为91744f3fab0ca434b811a295ffe820467cd9e7070033bd765fa35ebca58062e8，已核验取回。原入口失败及running1前缀观测完整保留。

这里只通过前5块预览，不是完整151936词联合RTL资格。下一阶段已另行冻结、手动启动于../full_bank_cosim_20261026_r1；本阶段不再重跑。无板卡操作、200MHz实现或自动后续阶段。
''')
write(B/'RESUME.md', '''
# 本分段已完成，不重跑

PREVIEW_REVIEW.json为PASS_FIRST5_PREVIEW_FULL_ARRAYS_AND_FULL_INPUT_SENTINELS，PROCESS_AFTER.json确认进程组为空、无锁和冻结源身份不变。完整VCD及实际数组已保留，归档SHA见RESULT.md。原running1和入口失败仍为历史证据，不用历史PID操作进程。

当前执行转到../full_bank_cosim_20261026_r1/RESUME.md。不得因本报告PREVIEW_WORKFLOW使用“等待独立审计”的工具返回状态而重复运行；独立审计是后产生的PREVIEW_REVIEW.json。不操作板卡，不启动wb/luyou/心跳，不改算法/质量/封存版本。
''')
write(F/'RESULT.md', '''
# 完整分bank联合验证：执行中，尚未取得完整资格

2026-10-26北京时间12:39:36启动。最新保存阶段EXECUTING_XSIM，展开日志已确认Built simulation snapshot full_bank_cosim_r1。本地工作流只是快照，实时状态以STHL本轮FULL_WORKFLOW.json、ACTIVE.lock及xsim.log为准。

前5块完整数组/权重读拍独立审计、被动阶段计时器、被动AXI边界观察器、原C后检查器正负控制四项门槛已通过并在PLAN.json钉住SHA。入口冻结SHA为1579af1f1de9444a4d02bf8c0dad22ac678454fc0c585092de5162f16f838bca。

只运行一次old_chinese/debug1完整配置，d64/T4096/B1024/双W不变，原RTL/浮点/FIFO/强随机停顿不变。修复隔离仿真内存，加实际模型1522字节回读及仅输入的阶段/AXI范围观察器。原全TV、生成XSIM和cosim.pc.exe复用；使用独立空actual目录。原完整Fail报告保留，cosim_design格式化报告NOT_RUN，不伪造官方PASS。

XSIM及原C后检查返回后，仍需独立核对全151936预览raw/key、64通道、完整候选ID/canonical raw、token/score/CRC以及实际有限FIFO/告警/AXI范围。tools/review_partial_full_bank_20261026.py已准备但未运行；它只核对本次完整单输入数值，不能代替FIFO审计。

计时观察器记录的是当前debug1强压力条件下的各阶段及全调用周期，尚无实际结果。不能据此声称正常DDR/生产模式decode速度、真实FPGA加速比或TTFT。ABA/模式切换、正常条件性能决策、200MHz实现均后置；无自动下阶段。未操作板卡。
''')
write(F/'RESUME.md', '''
# 当前完整验证续办

1. 显式STHL：ssh -p7626 -lzhangben 124.16.71.7；根目录/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1。不能使用默认7627助教容器。只读本报告FULL_WORKFLOW.json、ACTIVE.lock、elaborate.log、xsim.log、c_postcheck.log及/proc父身份/所属组；不重复启动入口。
2. 当前缓存.cache/p64_full_bank_cosim_20261026_r1/sim。完整TV初始化结束须有实际行首BANK_FULL_INPUT_SENTINEL_PASS checked=1522。时钟/日志/进程活动不代表完整完成；需真实返回数组及C后检查结果。
3. 若仍执行，保留已有作业。暂停时在本报告目录写STOP_REQUESTED；父看护每10秒检查，停止所属子PGID。核对父/proc创建时间、所属树为空及ACTIVE.lock清除后才报告停止；不使用历史PID。48小时及MemAvailable低于8GiB同样保护停止。停止不重试。
4. 工具终态后先审计所属组空/无锁，按PLAN逐份SHA复核冻结源（只有父计划声明的一处Linux权重路径重绑定），RTL_AND_STALL_REUSE和实际缓存逐份一致，保存PROCESS_AFTER.json。不得把生成XSIM/C后检查PASS直接当完整工程验收通过。
5. 静态收集本轮报告、实际7份returned_tv、actual_RTL_full_chinese.bin、weights_readback.csv、stage_profile.csv、实际FIFO/channel CSV及错误/告警原日志，生成归档SHA后取回核验。运行中只取固定大小日志前缀或静态快照，不能直接SCP追随增长VCD/日志。失败时也保留缓存和所有已产生返回，不创建预期actual冒充RTL。
6. 仅在真实状态GENERATED_XSIM_AND_C_POSTCHECK_PASS_AWAITING_NUMERIC_AND_FIFO_REVIEW及PROCESS_AFTER通过时，运行本地tools/review_partial_full_bank_20261026.py：直接解析实际TV并独立canonical重算全数组、回读及AXI事件；NUMERIC_REVIEW通过仍明确FIFO_PENDING。对有限FIFO配置/峰值/阻塞/完成和DSP告警有效输出关联另做独立审计；不套用旧失败full_r3的PASS审计器。
7. 原返回TV只含1523输入拍+79068工作区拍，未序列化额外end guard，不能用空切片“0差异”证明RTL无越界。本轮真实AXI范围观察器覆盖该缺口；软件guard只证明其本身范围。
8. 通过单输入完整数值与FIFO门槛后，由主模型再审代表性ABA/生产模式计划及正常存储响应条件的性能测试，不自动连跑或实施200MHz系统。当前debug1强随机停顿周期不代表FPGA生产decode效率。板卡仍需另行确认连接/独占；不连接、探测或操作，不恢复wb/luyou/心跳，不改封存/冻结质量/参数。
''')
p = ROOT/'doc/design/V4_NEXT_TASKS_20261026.md'
s = p.read_text(encoding='utf-8')
s = s.replace('- 原完整34105344拍TV重建的两份权重SHA正确。当前前5块门控仍在执行，日志已完成TV文件读取；尚未取得实际模型1522字节回读及全部前5块raw/key通过。实时状态看STHL本轮PREVIEW_WORKFLOW与日志，不能只读本地快照。', '- 原完整34105344拍TV重建的两份权重SHA正确。前5块已独立审计通过：1522模型边界字节、40960权重拍、64通道、5120 raw/key全一致；原133源及RTL/压力身份未变、所属组空、无锁。\n- 被动阶段计时器、AXI范围观察器及原C后检查正负控制通过后，已手动启动修复模型下的一次完整验证；最新保存阶段EXECUTING_XSIM。四门槛及源SHA冻结，尚无完整返回数组或FIFO结论。')
s = s.replace('|1 · 必须完成 · 当前|', '|1 · 必须完成 · 已通过|').replace('|2 · 必须完成|', '|2 · 必须完成 · 当前执行|')
s = s.replace('1. 当前前5块门控只运行已有作业，完成后先做独立VCD回放，不重复已通过单元。', '1. 前5块及独立VCD回放已完成，不重复；当前只保留已有的一次完整生成XSIM/C后检查，不并行第二份完整验证。')
s = s.replace('本次为规划更新，未启动任何新执行阶段；已有前5块门控继续。', '用户已授权按规划实施。完整验证使用原old_chinese/debug1、原RTL/有限FIFO/强随机停顿和全TV，仅修仿真存储并加被动观察器。手动运行原生成XSIM及原C后检查器，cosim_design格式化报告NOT_RUN，原Fail保留。工具返回后还需独立数值/FIFO审计，无自动下阶段。实时状态以STHL本轮FULL_WORKFLOW及锁/日志为准；本地只是快照。48小时/低于8GiB余量/本轮STOP_REQUESTED保护仅停止所属树。')
s += '\n当前执行：[完整验证与续办](../../module_14_lm_head_v4/reports/full_bank_cosim_20261026_r1/RESUME.md)、[前5块独立审计](../../module_14_lm_head_v4/reports/sim_memory_bank_20261026_r1/PREVIEW_REVIEW.json)、[网页报告](V4PartialRTL.html#full-bank-validation)。\n'
write(p, s)
print('Updated stage results, resume notes and current roadmap; frozen execution sources untouched.')
