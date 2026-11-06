# LM Head 量化方向：v4b 论文与实验路线

整理日期：2026-10-23。定向调研，非穷尽检索。工程父版本为已实板通过的v3.1，和v4稀疏候选路线并行。收录16篇作者arXiv原文，保留获取时版本、页数、来源元数据与SHA256；没有改写原PDF。论文版权与许可归原作者；收集用于本地研究，不推定再分发许可。

## 结论与优先级

优先做 **RTN W8/W4（另加W6/W12边界）→ GPTQ/AWQ head-only → HiRE-Q式预筛精算**。前两条保持全词表，压缩每行权重；第三条以全词表量化扫描选候选，再读canonical BF16行，保留赢家时可恢复原始score bits。W8A8/W4A8是独立计算优化阶段；残差、码本、旋转和向量查表条件推进。此排序是基于本项目独立M14与FPGA的工程判断，不是本地实验结论。

**直接量化通常不能保持原始logits逐位一致。** 必须区分量化实现对新golden的逐位正确性、对BF16赢家的一致率、闭环任务质量和性能。GPTQ原文Practical Speedups段（本地PDF第8页）明确其示例保留embedding/output layer为FP16；不能把整网量化精度直接当成head量化验证。作者OPT代码也在量化加载路径排除lm_head：[官方代码](https://github.com/IST-DASLab/gptq/blob/main/opt.py)。AWQ需审计实际head覆盖，不能仅看算法名。

## 本项目边界

- Qwen2.5-0.5B-Instruct，H896、V151936；canonical W=272269312B=259.65625MiB；hidden BF16仅1792B。模型配置tie_word_embeddings=true，必须克隆输出层，不能在量化head时连带改变输入embedding。
- v3.1实板200MHz、PL DDR、全词表；IP median/P95=117.751830/117.752020ms，来源[原RESULT](../../../module_14_lm_head_v3_1/reports/board_v31_20261019/RESULT.md)。这是有限归档输入的历史基线，不是本轮同轮实测。
- 本次核对原package清单9成员以及源码/头的profile SHA，保存[来源快照](../../../module_14_lm_head_v4b/baseline/SOURCE_LOCK.json)。没有重新校验整份canonical权重、跑模型、GPU、EDA或接触目标。
- FP32乘加/归约、全局history、repetition penalty正负分支、小ID同分规则必须明确；筛选按policy后的近似logits，防止raw赢家与惩罚后赢家不一致。
- b位主体理论体积=V×H×b/8；这不含scale、zero、残差、codebook、padding、ID、workspace和实际AXI流量。W4/W8理论分别64.9140625/129.828125MiB；W4-G128、FP32 scale、行64B对齐的拟议格式为74.1875MiB（不含256B文件头）。
- 量化精算要同时保存packed和BF16 W，W4上述格式合计333.84375MiB，已超过v4的320MiB arena；v4b拟另立512MiB布局，须重新审计，不复制v4地址/descriptor。
- 量化扫描字节Bq＋1792×K只是主要读取预算。还要Top-K、排序/gather和算术；不把压缩率当加速比，不用GPU论文数字预言AXU9EGB性能。

## 论文目录与本地笔记

阅读顺序：Q01/Q02 → Q12 → Q03/Q04/Q13 → Q14；Q05/Q06/Q07与Q08–Q11/Q15/Q16用于条件扩展。以下仅概括方法，不转载论文正文或把论文性能表转成本地结果。各篇的准确版本/作者/页数在manifest与BibTeX中。

### Q01 · GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers

Frantar, Elias; Ashkboos, Saleh; Hoefler, Torsten; Alistarh, Dan。2210.17323v2，16页。优先级：首轮。

[作者条目](https://arxiv.org/abs/2210.17323v2) · [原文PDF](Q01_GPTQ_2210.17323v2.pdf) · [对应实验](../../design/V4bValidation.html#q02)

方法：近似二阶信息补偿逐列权重量化误差，作为RTN之外的重建基线。

本项目改法：仅对输出矩阵拟合，Hessian来自训练hidden；冻结阻尼、列顺序和静态分组，导出回原hidden次序，避免FPGA在线置换。

边界：原整网结果不能证明lm_head已量化；原OPT示例逐Transformer block处理，不能直接照搬其整网精度。

重点阅读：方法与算法、分组和act-order；另核对作者opt.py的层遍历范围。


### Q02 · AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration

Lin, Ji; Tang, Jiaming; Tang, Haotian; Yang, Shang; Chen, Wei-Ming; Wang, Wei-Chen; Xiao, Guangxuan; Dang, Xingyu; Gan, Chuang; Han, Song。2306.00978v6，15页。优先级：首轮。

[作者条目](https://arxiv.org/abs/2306.00978v6) · [原文PDF](Q02_AWQ_2306.00978v6.pdf) · [对应实验](../../design/V4bValidation.html#q02)

方法：按激活统计做通道缩放，改善重要权重的低比特表示。

本项目改法：令W'=W diag(s)，在线h'=diag(s)^-1 h；单独M14不能假定上游已吸收缩放，计入896维变换和FP32舍入。

边界：不把AWQ名称等同于输出层已量化，也不把其整网GPU收益移植到本板。

重点阅读：activation-aware scaling、硬件packing和校准流程。


### Q03 · SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models

Xiao, Guangxuan; Lin, Ji; Seznec, Mickael; Wu, Hao; Demouth, Julien; Han, Song。2211.10438v7，13页。优先级：第二阶段。

[作者条目](https://arxiv.org/abs/2211.10438v7) · [原文PDF](Q03_SmoothQuant_2211.10438v7.pdf) · [对应实验](../../design/V4bValidation.html#q04)

方法：通过等价缩放将激活离群值的量化困难转移到权重，支持W8A8。

本项目改法：只变换head的h/W，比较alpha=0/0.5/1；group局部整数点积后按scale恢复FP32，再做原penalty。

边界：通道缩放会引入有限精度误差；hidden只有1792B，量化激活主要为了计算而非DDR节约。

重点阅读：平滑公式、激活量化粒度、W8A8实现。


### Q04 · LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale

Dettmers, Tim; Lewis, Mike; Belkada, Younes; Zettlemoyer, Luke。2208.07339v2，20页。优先级：第二阶段。

[作者条目](https://arxiv.org/abs/2208.07339v2) · [原文PDF](Q04_LLM_int8_2208.07339v2.pdf) · [对应实验](../../design/V4bValidation.html#q04)

方法：向量量化配合高精度离群通道分解。

本项目改法：对比全INT8与固定离群通道BF16补偿；单列离群索引、残差及额外访存。

边界：论文强调FFN与attention投影；非本head的直接验收，不能把99.9%整数乘法当本项目token一致率。

重点阅读：vector-wise quantization及mixed-precision decomposition。


### Q05 · SpQR: A Sparse-Quantized Representation for Near-Lossless LLM Weight Compression

Dettmers, Tim; Svirschevski, Ruslan; Egiazarian, Vage; Kuznedelev, Denis; Frantar, Elias; Ashkboos, Saleh; Borzunov, Alexander; Hoefler, Torsten; Alistarh, Dan。2306.03078v1，26页。优先级：条件扩展。

[作者条目](https://arxiv.org/abs/2306.03078v1) · [原文PDF](Q05_SpQR_2306.03078v1.pdf) · [对应实验](../../design/V4bValidation.html#q05)

方法：低比特主体与高精度离群权重结合，另压缩量化元数据。

本项目改法：固定残差率后量化主体与稀疏补偿相加；统计索引、scale/zero及解码开销。

边界：这里的sparse是残差权重稀疏，不是v4候选词表稀疏；near-lossless不表示逐位相同。

重点阅读：离群选择、双层量化、编码与解码。


### Q06 · SqueezeLLM: Dense-and-Sparse Quantization

Kim, Sehoon; Hooper, Coleman; Gholami, Amir; Dong, Zhen; Li, Xiuyu; Shen, Sheng; Mahoney, Michael W.; Keutzer, Kurt。2306.07629v4，23页。优先级：条件扩展。

[作者条目](https://arxiv.org/abs/2306.07629v4) · [原文PDF](Q06_SqueezeLLM_2306.07629v4.pdf) · [对应实验](../../design/V4bValidation.html#q05)

方法：敏感度加权非均匀量化和dense-and-sparse分解。

本项目改法：先做head-only标量码本对照，再考虑残差；查表吞吐和BRAM端口是独立工程变量。

边界：码本索引不是普通有符号INT4，不能直接使用INT4 DSP吞吐估计。

重点阅读：敏感度目标、非均匀码本、稀疏分解与GPU kernel。


### Q07 · OmniQuant: Omnidirectionally Calibrated Quantization for Large Language Models

Shao, Wenqi; Chen, Mengzhao; Zhang, Zhaoyang; Xu, Peng; Zhao, Lirui; Li, Zhiqian; Zhang, Kaipeng; Gao, Peng; Qiao, Yu; Luo, Ping。2308.13137v3，25页。优先级：条件扩展。

[作者条目](https://arxiv.org/abs/2308.13137v3) · [原文PDF](Q07_OmniQuant_2308.13137v3.pdf) · [对应实验](../../design/V4bValidation.html#q03)

方法：学习权重裁剪和等价变换以降低重建误差。

本项目改法：只训练head量化参数，不更新canonical模型；固定训练预算和未变换对照。

边界：需要优化过程，不能标为无需拟合；不能只按训练logit MSE选最终配置。

重点阅读：LWC、LET与优化设置。


### Q08 · QuaRot: Outlier-Free 4-Bit Inference in Rotated LLMs

Ashkboos, Saleh; Mohtashami, Amirkeivan; Croci, Maximilian L.; Li, Bo; Cameron, Pashmina; Jaggi, Martin; Alistarh, Dan; Hoefler, Torsten; Hensman, James。2404.00456v2，21页。优先级：条件扩展。

[作者条目](https://arxiv.org/abs/2404.00456v2) · [原文PDF](Q08_QuaRot_2404.00456v2.pdf) · [对应实验](../../design/V4bValidation.html#q06)

方法：正交旋转降低激活离群程度，辅助低比特计算。

本项目改法：测试head局部h'=Rh/W'=WR^T；896=7×128，先用7个128维块旋转，不直接调用全896点二次幂Hadamard。

边界：块旋转是本项目派生方法，不是QuaRot完整复现；旋转与padding成本必须计入。

重点阅读：计算不变性、在线Hadamard和精度设置。


### Q09 · SpinQuant: LLM quantization with learned rotations

Liu, Zechun; Zhao, Changsheng; Fedorov, Igor; Soran, Bilge; Choudhary, Dhruv; Krishnamoorthi, Raghuraman; Chandra, Vikas; Tian, Yuandong; Blankevoort, Tijmen。2405.16406v4，24页。优先级：条件扩展。

[作者条目](https://arxiv.org/abs/2405.16406v4) · [原文PDF](Q09_SpinQuant_2405.16406v4.pdf) · [对应实验](../../design/V4bValidation.html#q06)

方法：学习旋转以改善低比特误差，揭示随机旋转质量差异。

本项目改法：若随机块旋转有收益，再以相同预算测试学习式head局部旋转；固定seed和训练划分。

边界：全网旋转不自动兼容独立M14接口；论文整网W4A4KV4指标不能视作head一致率。

重点阅读：旋转参数化、优化目标和随机旋转对照。


### Q10 · QuIP#: Even Better LLM Quantization with Hadamard Incoherence and Lattice Codebooks

Tseng, Albert; Chee, Jerry; Sun, Qingyao; Kuleshov, Volodymyr; De Sa, Christopher。2402.04396v2，27页。优先级：背景。

[作者条目](https://arxiv.org/abs/2402.04396v2) · [原文PDF](Q10_QuIP_sharp_2402.04396v2.pdf) · [对应实验](../../design/V4bValidation.html#q06)

方法：Hadamard不相干处理与E8格码本结合，并使用微调改善保真。

本项目改法：用于评估规则标量量化之外的精度上界及码本硬件成本，暂不作为首个HLS实现。

边界：E8向量解码和训练成本不能省略；论文包含微调，不等同于简单PTQ打包。

重点阅读：不相干处理、格码本、微调范围。


### Q11 · QLoRA: Efficient Finetuning of Quantized LLMs

Dettmers, Tim; Pagnoni, Artidoro; Holtzman, Ari; Zettlemoyer, Luke。2305.14314v1，26页。优先级：背景。

[作者条目](https://arxiv.org/abs/2305.14314v1) · [原文PDF](Q11_QLoRA_2305.14314v1.pdf) · [对应实验](../../design/V4bValidation.html#q06)

方法：NF4与量化常数压缩为低bit存储提供码本对照。

本项目改法：只借用NF4表示做head-only存储/误差对照；不进行LoRA训练。

边界：QLoRA是微调方案，训练显存收益不代表独立M14推理收益；NF4不是整数乘法。

重点阅读：NF4、double quantization；不将训练性能代入推理。


### Q12 · HiRE: High Recall Approximate Top-$k$ Estimation for Efficient LLM Inference

L, Yashas Samaga B; Yerram, Varun; You, Chong; Bhojanapalli, Srinadh; Kumar, Sanjiv; Jain, Prateek; Netrapalli, Praneeth。2402.09360v1，14页。优先级：首轮。

[作者条目](https://arxiv.org/abs/2402.09360v1) · [原文PDF](Q12_HiRE_2402.09360v1.pdf) · [对应实验](../../design/V4bValidation.html#q07)

方法：压缩矩阵估计Top-K，再仅对候选作高精度计算；含int4预筛。

本项目改法：独立量化全V预筛，无v4聚类/低秩；按penalty后preview选候选，再用v3.1 canonical算术精算。

边界：候选漏选仍有风险，固定K不保证无损；整网softmax+FFN收益不等于head单独收益。

重点阅读：HiRE-Q、候选召回、top-k与精排成本。


### Q13 · QServe: W4A8KV4 Quantization and System Co-design for Efficient LLM Serving

Lin, Yujun; Tang, Haotian; Yang, Shang; Zhang, Zhekai; Xiao, Guangxuan; Gan, Chuang; Han, Song。2405.04532v3，19页。优先级：第二阶段。

[作者条目](https://arxiv.org/abs/2405.04532v3) · [原文PDF](Q13_QServe_2405.04532v3.pdf) · [对应实验](../../design/V4bValidation.html#q04)

方法：W4A8及系统协同设计，关注反量化和部分和恢复开销。

本项目改法：借用W4A8与融合解码的成本分析；在本板重新测量AXI吞吐、DSP、BRAM及端到端M14延迟。

边界：GPU大batch服务与KV4不是独立head范围；不复制Tensor Core性能数字。

重点阅读：progressive quantization、反量化、kernel开销。


### Q14 · FlightLLM: Efficient Large Language Model Inference with a Complete Mapping Flow on FPGAs

Zeng, Shulin; Liu, Jun; Dai, Guohao; Yang, Xinhao; Fu, Tianyu; Wang, Hongyi; Ma, Wenheng; Sun, Hanbo; Li, Shiyao; Huang, Zixiao; Dai, Yadong; Li, Jintao; Wang, Zehao; Zhang, Ruoyu; Wen, Kairui; Ning, Xuefei; Wang, Yu。2401.03868v2，12页。优先级：第二阶段。

[作者条目](https://arxiv.org/abs/2401.03868v2) · [原文PDF](Q14_FlightLLM_2401.03868v2.pdf) · [对应实验](../../design/V4bValidation.html#q08)

方法：可配置DSP链、混合精度与片上数据管理的FPGA协同设计。

本项目改法：参考低位宽DSP映射与访存并行，但使用本项目AXU9EGB/PL DDR/200MHz重新实现。

边界：U280/Versal资源与带宽不同，不能继承论文速度或将混合稀疏优势当作纯量化收益。

重点阅读：DSP链、memory hierarchy和性能模型。


### Q15 · LUT-LLM: Efficient Large Language Model Inference with Memory-based Computations on FPGAs

He, Zifan; Ye, Shengyu; Ma, Rui; Wang, Yang; Cong, Jason。2511.06174v2，11页。优先级：背景。

[作者条目](https://arxiv.org/abs/2511.06174v2) · [原文PDF](Q15_LUT_LLM_2511.06174v2.pdf) · [对应实验](../../design/V4bValidation.html#q06)

方法：激活和权重向量协同量化，将部分乘法转为片上表查询。

本项目改法：作为后续FPGA查表路线评审；先统计head所需码本训练、查表端口和容量。

边界：FCCM2026版本使用AMD V80及定制Qwen3训练配方，不是v3.1可直接替换的权重格式。

重点阅读：性能模型、centroid search、2D table lookup和训练配方。


### Q16 · AAAC: Activation-Aware Adaptive Codebooks for 4-bit LLM Weight Quantization

IslamBouli, Beshr; Jin, David。2605.08692v2，10页。优先级：条件扩展。

[作者条目](https://arxiv.org/abs/2605.08692v2) · [原文PDF](Q16_AAAC_2605.08692v2.pdf) · [对应实验](../../design/V4bValidation.html#q06)

方法：激活加权选择两个小型标量码本的2026预印本路线。

本项目改法：与固定NF4/均匀INT4比较，显式保存码本选择、scale符号和版本，不能复用普通正scale解析器。

边界：预印本结论需本地复核；本文的元数据编码约定不自动兼容现loader。

重点阅读：自适应码本目标、选择bit编码和训练成本。

## 实验组织与后续执行

[V4bValidation.html](../../design/V4bValidation.html)含12组实验、参数、控制变量、步骤、指标、门槛、依赖、论文映射及打包预算计算器；[PLAN.json](../../../module_14_lm_head_v4b/experiments/quantization_study/PLAN.json)为同源机器数据。所有结果为null/NOT_RUN，页面操作只浏览计划。

训练/校准仅拟复用旧train1500/calibration320的只读资产；新最终1000题必须排除所有旧分组和快照、重审代码题来源，锁入口后只评估一次。直接量化记录token一致率，预筛记录policy后赢家召回；校准保守准入要求零错误/零漏选，最终整体及每类decode点估计≥99.9%，并报告按问题分组的区间与整题一致率。该门槛不是数学无损保证。

本轮不打开新测试标签，不量化权重、不拟合/测速、不做EDA、不连接/探测/操作板卡，不恢复wb/luyou/心跳，不改v3.1/v4冻结包。v4实验10既有质量失败保持原结论；两版本融合须另立新计划与新认证组。

## 文件与核验

- catalog.json：筛选理由、方法笔记与实验映射。
- manifest.json / SHA256SUMS.txt：实际下载版本、大小、页数与SHA；源条目HTML另存Qxx_source.html。
- sources.bib：以arXiv版本作为来源，年份按arXiv标识年份，不混淆会议年。
- Qxx_extracted.txt：全文文字抽取辅助定位，可能存在公式/字符抽取缺陷，原PDF为阅读事实源。
- download_papers.py：显式执行才获取论文；不含模型/EDA/板卡控制。
