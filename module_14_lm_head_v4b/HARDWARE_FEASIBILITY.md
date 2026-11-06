# v4b 后续硬件可行性检查单（设计推导，尚未执行）

此文件整理本轮锁点之后需要验证的问题。它不是HLS/RTL/时序/带宽或实板结果；当前有限CPU/GPU流程不会启动EDA。两个锁点的新质量结论以FINAL_QUALITY.json为准，失败点不能发布或拿打开组重调。

## 1. 两条锁点路径的硬件差异

| 路径 | 权重主体 | 额外流程 | 必须保留的数值行为 |
| --- | ---: | --- | --- |
| 直接W12/G896/非对称 | 204.015625MiB | 12bit解码、每行FP32 scale与uint16 zero | q-z先精确转FP32、乘scale单独舍入，再乘原BF16 hidden并保持v3.1归约 |
| W4/G128对称预筛＋K512 BF16精算 | preview74.1875MiB＋canonical259.65625MiB | 全V preview、全局policy、稳定Top-K、512行BF16读取与原算术精算 | preview为同样的FP32解码/点积；精算必须使用原hidden和canonical W，重新由raw施加policy |

两路径都改变了权重读取格式；即使W12接口形状接近v3.1，也不能把旧bit/XSA/BSP/ELF配上新权重使用。私有descriptor、VLNV、build/GPIO/config tag、CSR及arena版本均待分配。

## 2. 减少字节不等于减少计算周期

v3.1每行896维，以8 lane覆盖112个word。仅把权重换成低bit并在读取后恢复FP32，点积仍需同样的896项；还增加q×scale的恢复成本。不能从W4的文件压缩率推出FPGA加速。

W4/G128的一行是7组，每组64B nibble payload＋4B FP32 scale，共476B并填充至512B。可以先顺序读整行到本地buffer，再解码，避免每次nibble/scale访问都向DDR发起小事务。这只是访存方案，须测burst、反压、实际读拍数与资源。

若每周期并行多个原H8 word，必须检查**同一FP32累加槽的反馈间隔**：v3.1的16槽使同槽隔16个word更新；四字并行会缩短同槽反馈间隔。若adder流水延迟大于新间隔，II就会受反馈依赖限制。可以考虑多行交错、各行保留独立16槽，仍按原次序更新每槽；不能擅自改成更多槽、不同加法树或FMA后继承逐位结论。

首轮微核仍按实验8有限设计点(lanes,AXI bits)=(8,128)/(16,128)/(16,256)/(32,256)，最多两个合格配置。先证完整数值，再看II/DSP/BRAM/LUT/Fmax。256bit master还要经过实际128bit MIG接口宽度转换，不能把接口数字直接当DDR带宽翻倍。

## 3. Top-K不能被忽略

GPU参考中量化精算比同轮dense慢，说明排序/gather/额外阶段值得单独分析；该观察不能外推FPGA输赢。

FPGA可评估512项最小堆：root是“最低分，分数相同则最大ID”的最差候选。每个preview token使用全局history施加policy后再参与堆，保证小ID边界规则。堆建立/更新、读写端口、最坏路径与状态清零都须Csim/RTL证明。堆输出可再按全局ID排序，以便检查/组织DDR读取；即使不排序，最终argmax也必须显式同分取小ID。

原校准最差rank=7不构成把K减到8的授权或无损证明；本轮锁定K512。未来改变K/Top-K算法属于新配置/实现，不能在本轮已打开最终组上重认证。

## 4. 布局、总线与身份

- 精算路径两份完整W已经333.84375MiB，旧320MiB arena不足。拟议512MiB还需容纳hidden、history、heap/ID、debug raw、mailbox或descriptor及guards，必须重新逐区审计。
- 工程拓扑从v3.1派生：独立M14、PL DDR、 nominal 200MHz，保留PS程序/TCP暂存/mailbox的既有归属，不能把v4 selector BD或实验10包复制为父版本。
- 64位系统地址及0x400000000高地址窗口的语义必须保持一致；不得把MIG局部偏移冒充A53/HLS系统地址。新布局的地址、容量、溢出、别名、alignment与末端拒绝都重新验证。
- 文件头/行stride/bitwidth/group/zero编码是新格式。实验内部unpack不是已资格验证的host loader；非法版本、长度、scale/zero、padding、边界/CRC与身份不匹配须补齐拒绝测试。
- canonical W及packed W分别SHA/分块CRC，runtime scratch不预填golden。旧软件/旧镜像不得混装；新XSA必须匹配新BSP/ELF。

## 5. 验证顺序与停止条件

1. 明确采用哪条已锁定路径及其质量是否合格；保留所有失败，不从最终组换新参数。
2. 从v3.1源码建立独立v4b内核/身份；C参考同时证明新量化golden与原始BF16质量，两者不混为一个PASS。
3. 小边界、四类真实夹具、连续A→B→A、全局history/penalty正负分支、同分边界、NaN/越界/别名/错误身份与guard。
4. Csim通过后HLS；完整RTL及所有内存/scalar逐位审计通过后才导出IP，Windows EDA使用项目内短路径（例如.cache/e4b），不覆盖旧e10工程或失败日志。
5. 新200MHz整系统STA/hold/CDC/DRC、bit/XSA/CSR审计，再构建匹配BSP/ELF及离线包。
6. 真实板测等待用户新的独占安排。仿真周期、HLS估计和理论字节都不填成实板decode、TTFT或端到端LLM吞吐。

当前上述硬件步骤全部NOT_RUN；此文是后续评审依据，不启动工具或连接目标。
