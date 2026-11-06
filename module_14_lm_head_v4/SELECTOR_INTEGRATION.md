# v4 统一selector实验顶层与PL DDR合同

当前状态以PROGRESS.json及真实报告为准。不是公开M14 ABI、正式发布镜像或板卡验收。
四个独立子核原文件保持不变，新顶层`lm_head_v4_selector`顺序调用它们。

## 结构和调度

`预检 → 路由 → 低秩 → Top-K/并集 → canonical候选精算 → 提交token/score/CRC`。
先建立串行完整基线，不提前声称路由/低秩已在硬件并行。

HLS2021.1不允许一个AXI读端口在同一个DATAFLOW区域内被多个进程读取。
首次单读端口设计真实综合失败，记录为`hls_selector_csynth_r1_20261021.log`。
当前为两个64位地址、128位数据的AXI master：

- `m_axi_plmem`：权重、参数、descriptor、hidden与读写scratch。
- `m_axi_histmem`：仅全局history bitmap，1187个128-bit beat。

两个端口在BD中都只映射MIG PL DDR，排除PS DDR和控制寄存器段。
主机/PS调用者必须校验并读回两个实际指针寄存器：`pl_ddr=0x400000000`，
`history_bitmap=pl_ddr+HISTORY.offset`。HLS检查相对范围，不能冒充其已验证外部寄存器物理值；
主机相应检查见`reference/selector_layout.py`。调用中descriptor/输入/history不可变。

## 私有320MiB布局

源布局在`interface/PL_DDR_LAYOUT_V4.json`，描述符由`scripts/prepare_selector_integration.py`生成。
复用v3.1的2GiB物理PL DDR窗口，本独立M14实验仅预留其中320MiB，当前约309MiB已分配。
不构成整个LLM的共享内存分配。区域间留64B guard，便于离线检测越界。

descriptor位于相对1MiB位置，共240B：

| 字段 | 格式 |
| --- | --- |
| 头16B | magic=M4SC / version1 / region_count13 / bytes240 / reserved0 |
| 配置16B | uint32 flags / FP32 penalty / uint32 topK16384 / reserved0 |
| 13区域，各16B | uint64 byte_offset / uint64 byte_capacity |

区域顺序为weight、hidden、history、A、BT、centers、norms、ranked、counts、preview、routed、merged、sparse。
所有偏移和容量须16B对齐，最小容量由固定H896/V151936/rank128计算，不能uint32截断。
头/配置、窗口范围、offset+capacity溢出、区域彼此及descriptor重叠都在计算前拒绝。
容量全部互斥，包含只读区域；当前故意不允许输入缓冲别名。

flags：bit0输出稀疏debug；bit1启用重复惩罚；bit2允许选中空簇后的显式全词表fallback。
生产flags6不导出debug，对应sparse descriptor必须offset=capacity=0；debug flags7预留完整输出容量。
这只是私有测试参数，不是公开ABI新版本或上游直供权重接口。

## 提交与错误合同

`command=RUN(0)`执行计算；`VALIDATE_ONLY(1)`只检查descriptor，不写scratch或计算token。
VALIDATE_ONLY的status0不代表产生token；RUN必须同时status0、stageDONE才可发布结果。

预检失败保持所有旧scratch内容不变，但返回token/score/CRC清零。
预检通过后先清零routed与merged的头，阻止误把旧表识别为本轮候选。
任一子核失败：返回父级CHILD_FAILED、失败stage及子核状态，不启动后续子核，不提交最终token。
低秩A非有限数允许partial preview写入，父级必须阻止Top-K继续；该路径已列入C仿真。
精算发现非有限数时debug可能已有部分写入，调用者只认本次父级status/stage，不能自行发布debug或旧token。

## 验证与剩余工作

完整PL DDR系统离线实现r2已通过独立审计：200MHz STA WNS+0.652ns、WHS+0.010ns，
CDC Critical0、MIG警告0、bit/XSA内嵌bit一致。仍有工具DRC Warning/Advisory，
详情见`reports/board_v4_20261021/HARDWARE_RESULT_R2.md`及`hardware_audit_r2.json`。
它不代表整链RTL或板测通过：当前整链RTL正使用局部修复后的生成包装验证，
原官方HLS包装因同名块冲突FAIL的证据保留；最终须核对全内存trace与原C postcheck。

### PS控制逻辑与离线加载镜像

`standalone/selector_control.c/.h`使用可替换的read32/write32/barrier/now_us后端。
先核对GPIO第二通道的私有镜像签名0x4D345301，再检查校准；读取目标描述符，
完成相同容量/别名预检，写入并读回完整64位PL与history指针后才启动IP。
RUN还必须有实际目标读回校验通过的资产ticket；当前fake-MMIO测试不会产生此ticket。
结果须满足本次status、stage、计数、全局token范围、有限score及输出CRC才标记token_valid。
超时会返回may_still_be_running，不能自动复位、重载或修改计算输入。
25项fake-MMIO测试和导出IP头文件寄存器偏移审计已通过，尚不代表实际BSP/ELF/板测。

`scripts/prepare_selector_memory_image.py`生成生产flags6的完整320MiB私有arena文件，
包含canonical权重、A/BT、路由参数、指定hidden/history、描述符、清零scratch和13处guard。
它会逐源区域读回SHA、检查guard，再生成整份SHA/CRC、320个1MiB分块CRC及区域首尾sentinel。
当前中文镜像在`reports/selector_arena_chinese_20261021/`，状态为OFFLINE_IMAGE_NOT_LOADED。
这些是主机文件校验，不能替代目标PL DDR回读；旧v3.1固定权重loader不支持此整份arena，禁止直接混用。
本脚本不会连接板卡或网络。参数包是私有集成夹具，不是公开M14版本发布。

统一顶层C仿真覆盖四类真实完整preview/候选ID/raw logits/token/score/CRC，
生产模式、合法相邻区域、24类预检拒绝和5类运行中错误门控；32项host测试覆盖64位PL地址和随机合法/非法布局。
HLS综合、完整尺寸RTL、BD/CDC/STA、bit/XSA与软件配套须各自核实真实结果，不由C仿真自动推出。
当前尚无新硬件身份/正式profile/配套ELF；板卡操作仍需新安排。

真实decode计时为hidden可用到最终token可用的整个流程；不能累加子核小用例平均值当实板性能。
原CPU r2b质量结果保留为历史，不能自动继承给新RTL；已打开的测试集不重新用于选型或认证。
