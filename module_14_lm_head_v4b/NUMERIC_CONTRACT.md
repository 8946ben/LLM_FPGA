# v4b 当前离线数值与压缩格式

本契约描述2026-10-23本机实验。FPGA ABI、descriptor、VLNV、CSR、build/GPIO identity尚未分配，不能据此加载任何旧bit/ELF或当作硬件协议已验收。

## 工程与算术来源

父版本为已上板v3.1，H896/V151936、canonical BF16权重与hidden、全局history、正负分支repetition penalty1.1及小ID同分规则。来源见baseline/SOURCE_LOCK.json。v4仅供只读模型与旧train/calibration数据身份；不复制v4候选selector作为父实现。

CPU与GPU评估均保持H8/interleave16：word=j//8、slot=word%16、lane=j%8；112个word依序更新。槽归约按8/4/2/1半分相加，lane按相邻对(0+1、2+3、4+5、6+7)规约。FP32乘法和加法分别舍入，禁用FMA/TF32。新的NVRTC评估器通过原8步全部raw/policy SHA及全部5095校准token/score bits证明；性能不同于旧Eager实现，禁止拿两者绝对速率比较成算法收益。

## 标量均匀量化

- 位宽4/6/8/12，hidden轴组长32/64/128/896，均整除896，token行彼此独立。
- scale为FP32正有限值。对称q∈[-(2^(b-1)-1), +(2^(b-1)-1)]，不使用最负编码；s=maxabs/qmax。全零组s=1、z=0。
- 非对称q∈[0,2^b-1]；lo=min(minW,0)、hi=max(maxW,0)、s=(hi-lo)/qmax；全零组s=1；z=clip(RNE(-lo/s))。
- RTN：q=clip(RNE(W/s)+z)。RNE为ties-to-even。重建Wq=FP32((q-z)×s)，保持FP32，不再回舍BF16。
- head先用Wq与原BF16展开hidden执行接受的归约，再对history中token应用正数除p、负数乘p，最终argmax同分取小ID。
- GPTQ：训练hidden构造FP32 Hessian，静态原W分组grid、block128、damp0.01、act-order关闭；误差补偿只用于离线拟合整数编码。对角Hessian退化RTN的小型证明见报告。
- AWQ-style：s_channel=mean_abs(h)^alpha，经clamp/几何归一化；alpha=0/.25/.5/.75/1在旧训练内部80/20问题分组上选。W离线乘s_channel，hidden在线FP32除s_channel，全部有限精度误差纳入质量。禁用额外裁剪搜索，不宣称完整官方AWQ复现。

## M14_V4B_PACKED_WEIGHT_V1

文件头256B：UTF-8 JSON并以0填满，记录rows/hidden/bits/group/symmetric/scale/zero_bytes/row_bytes。之后逐token行保存组记录，整行对齐64B，padding为0。

每组：`[G*b/8 bytes payload][4B FP32 LE scale][zero_bytes zero point]`。对称zero_bytes=0；非对称ceil(b/8)。数值按hidden次序，低bit优先、小端，带符号q为b位二补码编码。6bit每4值占3B，12bit每2值占3B；zero的未用高位为0。每行stride为align64((896/G)×(G*b/8+4+zero_bytes))。

CPU pack与独立按位提取unpack核验全部编码、scale、zero、重建FP32 bits；四类完整raw数组CPU/GPU核验。GPU packed参考直接读取实际文件buffer并在kernel内解码，没有预先展开W替代打包成本。BF16控制也直接从2B原始权重buffer读取。

W4-G128对称行stride512B、全W主体74.1875MiB（另256B头）；并存BF16 W时两份主体333.84375MiB。不能套用旧320MiB arena；未来512MiB布局仍待地址/guard/loader审计。当前unpack只是实验内部读取器，非法header/版本/布局的完整宿主拒绝路径与硬件接入尚未资格验证。

## 两条输出路径与验证边界

直接量化输出改变logits；量化golden逐位正确与BF16赢家一致率分别验收。

量化预筛：全V近似raw → 全局history/penalty → 稳定Top-K → 候选按ID升序 → 原BF16行与原hidden精算 → 原penalty/argmax。没有v4聚类/低秩，也不偷偷强制加入特殊ID；全部词表均可参与。K=V只是退化控制。旧校准阶段的rank-membership统计不充当在线Top-K计时；实际完整管线与真实packed计时另有证明。

校准准入为全部5095预测零错选/零漏选，并满足整体及每类decode≥99.9%；新最终组只在候选、源码、packing和题目入口锁定后打开一次。新组按问题分组统计首输出/decode/整题一致率和区间；固定dense轨迹的条件一致性不等于自由生成、任务正确率或数学无损。
