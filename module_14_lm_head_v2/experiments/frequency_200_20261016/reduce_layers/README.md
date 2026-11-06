# 200 MHz 候选：分离归约层数组

候选只改 `reduce_partials`：16→8、8→4、4→2分别写入独立数组，最后2→1写入
`lane_sum`；输入 `partial` 改为只读。每一次FP32加法的配对、操作数顺序和层次保持原样。
没有修改点积、H8/V1、16-slot、外部接口，也没有添加虚假依赖、多周期例外或完全展开归约循环。

假设：消除原地动态索引读写后，HLS能减少保守的distance=1相关限制。
2021.1生产尺寸综合已完成：三层归约II=1，每行102cycles（原5ns诊断为147），
顶层估算3.650ns；同口径HLS LUT=30085、FF=32925、BRAM_18K=95、DSP=59。
CSim和hidden=896/vocab=64的RTL/XSim重跑及C post-check通过。
这些结果不能代替200 MHz布线后时序或实板验收；当前物理验证见报告目录。

## 已完成验证

`run_native.ps1` 使用本机MinGW g++ 16.1.0，关闭fast-math及FMA收缩：

- 从真实原版和候选函数提取的归约代码：50,004组 × 128个FP32输入，输出逐位一致。
  含正负零、slot配对/相邻lane配对敏感的消减用例和固定种子随机输入。
- 实际原版及候选整核，分别使用hidden=896、vocab=64运行8组输入；各512个raw logits
  与数值合同参考逐位一致，top-1、score bits及CRC通过。
- 原有penalty、并列选择/关闭IO、lane消减、非法参数测试通过。
- `validate_sources.py` 核对生产源码/头文件SHA256，确认候选只改变归约函数，
  且被测提取函数与真实源码一致。结果见报告目录的`tested_sources.json`和`source.diff`。

整核软件测试借用本机2017.4的`ap_int`/`hls_stream`仿真头文件。
**这是主机软件回归，不是2017.4或2021.1 HLS综合、Vitis CSim、RTL仿真或板测。**
测试头文件只在测试模式下把vocab缩到64，保持真实hidden=896和全部112个hidden word。
生产候选综合使用`include/`中原有生产头文件，仍为vocab=151936。
已有`LMH_V2_TEST_SMALL`只覆盖4个hidden word，不能代替本轮全16-slot测试。

## 复跑

从项目根目录执行：

```powershell
# 当前可以执行的主机回归
./module_14_lm_head_v2/experiments/frequency_200_20261016/reduce_layers/run_native.ps1

# 2021.1首次执行入口（本轮工程已完成/存在，会拒绝覆盖）
./module_14_lm_head_v2/experiments/frequency_200_20261016/reduce_layers/run_hls.ps1 -Mode csim
./module_14_lm_head_v2/experiments/frequency_200_20261016/reduce_layers/run_hls.ps1 -Mode csynth
./module_14_lm_head_v2/experiments/frequency_200_20261016/reduce_layers/run_hls.ps1 -Mode rtl896
```

默认工具`G:\Xilinx\Vitis_HLS\2021.1\bin\vitis_hls.bat`，可用`-VitisHls`指定恢复后的路径。
用户重新连接G:盘后已完成CSim、生产综合及`rtl896`验证。
每种模式写入独立工程`build/frequency_200_20261016/reduce_layers/{mode}`；
已存在的工程会被拒绝覆盖。脚本仅针对已确认的2021.1 `hidden_size_r`向量命名缺失
提供局部修复，并要求重跑RTL及C post-check成功，不把生成RTL或进程退出0当作通过。
首次`cosim`工程因接口depth仍为生产尺寸导致C包装器越界；测试副本修正为112/7168/1/16，
只改测试接口深度。`cosim_full_hidden`曾停滞并保留；短工程`rtl896`重试成功，
停滞的具体工具根因未确认。生产候选仍读取原生产深度，不依赖测试宏。

RTL为15笔事务，512个随机raw logits逐位一致；应用`hidden_size_r`向量命名修复后，
生成的XSIM重跑和C post-check通过。原自动CoSim失败日志保留，不能只看它或进程exit=0下结论。

综合比较使用5.000 ns、HLS uncertainty=1.350 ns，与首次诊断一致。
检查三层归约的achieved II、每行周期、时钟估算和资源；同时保住点积II=1。
已确认调度/资源收益，完整200MHz BD布线后时序通过：WNS+1.067ns、WHS+0.010ns、WPWS+1.000ns。未上板；最终以报告状态为准。

本候选保留旧100 MHz `build_config`，**仅供诊断，不可下载上板作为正式200 MHz版本**。
没有导出IP、覆盖生产工程、修改交付ZIP或连接板卡。正式身份/时钟计时配套仍是上板前门槛。
