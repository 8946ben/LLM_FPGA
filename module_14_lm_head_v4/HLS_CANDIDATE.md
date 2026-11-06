# 独立候选精算 HLS 原型

当前top为`lm_head_v4_candidate`，固定V151936/H896、128-bit AXI、64-bit地址。
这是独立实验接口，尚未冻结公开ABI、板卡profile、驱动或v4发布身份；不包含在线selector。
v2/v3/v3.1封存源码与板卡设计保持原样。

## 数学和内存契约

- `src/accepted_numeric_core.hpp`原文提取已验收v3.1的转换、点积和规约函数；8 lane、16交错槽、独立FP32乘加及规约顺序不变。
- 权重按`weight_base + global_id*1792`寻址，只读取候选行；全候选应与dense数学结果一致。
- 候选表沿用软件M4ID/V1头，后接递增唯一uint32 ID；读取前完整校验。调用期间该表必须保持不变，不能校验后由PS并发改写。
- `candidate_capacity_beats`包含16B header及ceil(K/4)个payload beat；payload尾部无效lane忽略。容量按整beat检查，验证完成前不读hidden/权重、不写分数。
- 软件文件的逻辑长度仍为16+4*K字节；搬到DDR时分配/填充至16*(1+ceil(K/4))字节，不能将未分配尾部当作可读padding。软件文件解码仍校验逻辑长度，不把DMA padding冒充额外ID。
- 校验和执行各读一遍ID，`index_read_beats=1+2*ceil(K/4)`；不能只计一遍。
- sparse debug每项8B（global ID、raw FP32），每beat放两项，奇数K尾部高64位写零；输出容量需ceil(K/2)整beat。
- history按global ID的`>>7`和低7bit定位，缓存相邻候选的同一128-bit history块；计数报告真实读取beat数。
- 相同分数取较小global ID，首个候选不要求ID0。选中行NaN/Inf置错误状态并使生产CRC无效；跳过行的异常不在本次检测覆盖内。
- 物理地址范围/别名/PL-DDR profile与PS驱动仍需完整集成验证，当前实验top不代替这些检查。
- 计数按代码请求的128-bit beat记录，不是独立的物理DDR监测；控制器预取、burst padding和宽度转换还需实际AXI监测。

## 已有离线证据

最终C仿真日志`reports/hls_candidate_csim_r5_20261021.log`：17组真实canonical对照（包含全151936行），13类非法输入，4项特殊路径通过。
覆盖原始分数逐位、penalty赢家/分数位、CRC、全局history块、非连续ID、奇数尾部、无效padding、debug/penalty关闭、跳过/选中NaN。
这是C仿真；当前没有RTL协同仿真或v4真实板测结论。

首轮综合的动态ID解析路径为5.73063ns（约174.5MHz）；固定四路beat校验后报告估计3.830ns（工具显示约261.12MHz），所有循环约束满足。
实际数字以`build/candidate_csynth_r2/hls/solution1/syn/report/`为准，HLS时钟估计不代表布局布线。

点积每行仍159拍；候选gather在当前HLS模型中每行190~191拍，慢于dot。
因此不能用`151936/K`直接乘v3.1吞吐，也不能将全候选模式称为性能无回退。
gather的DDR延迟、突发边界和实际并发必须在RTL/板测中进一步量化；全词表回退后续应保留独立dense通路。

## 复现与续办

Vitis HLS/Vivado 2021.1；器件xczu9eg-ffvb1156-2-i。HLS时钟5ns、uncertainty1.35ns。
独立OOC时钟5ns、setup uncertainty0.2ns/hold0.05ns，边界I/O路径不代表板级接口时序。

```powershell
python scripts\prepare_hls_numeric_core.py
$env:LMH4_HLS_MODE='csim' # 或csynth
$env:LMH4_HLS_RUN='新的唯一构建目录名'
& G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat -f hls_candidate.tcl
```

已有项目不会自动覆盖；使用新run名。HLS运行须读取G盘动态库，本轮沙箱直接启动失败，本机启动正常。
首次`export_design -flow impl`因旧版工具日期261021xxxx溢出core_revision的signed32范围而失败，日志保留。
已复用本项目既有方法：仅将本轮生成的run_ippack.tcl的Revision换为合法Unix秒版本号，备份原文件及SHA；重跑pack.bat成功。
修复记录`reports/LOCAL_IP_REVISION_REPAIR.json`；不修改工具安装、系统时间或旧版本元数据。
初次独立布局布线入口`candidate_ooc.tcl`从生成RTL/四个浮点子核建立新工程；因未设HD.CLK_SRC已停止，不使用其时序作结论。
后续`candidate_ooc_clocked.tcl`复用综合DCP，按BUFGCE_X0Y0作为显式OOC时钟参考来源重做放置布线；这是独立假设，不是板上时钟placement声明。现有run也不覆盖。
最终是否通过200MHz，以OOC实际timing报告和阶段RESULT为准。完整含selector/PL DDR系统、CDC和板测仍待后续。
