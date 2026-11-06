# lm_head v3.1 PL DDR 验收

状态：PASS。200 MHz、完整词表，计算数据走 PL DDR；PS 程序/TCP暂存/mailbox保留 PS DDR。

8 步生产与 8 步完整 logits 逐位一致；30 次独立计时；1000 次连续调用通过。
PL DDR 数据模式、地址位和末端探测通过（非全2GiB逐字穷举）；地址范围拒绝通过。
校准超时为真实 A53 上的软件故障注入，不代表物理 MIG 校准失败测试。
加载 SHA256、目标 PL DDR 逐块/完整 CRC32、首尾 sentinel 通过；6项加载错误测试后已整份重传。

| 指标 | 本任务10/19断电前 v3 PS DDR 对照 | v3.1 PL DDR | 倍率（v3时间/v3.1时间） |
| --- | ---: | ---: | ---: |
| IP median ms | 117.751805 | 117.751830 | 1.000000 |
| IP P95 ms | 117.751880 | 117.752020 | 0.999999 |
| A53 median ms | 117.767288 | 117.770033 | 0.999977 |

IP毫秒 = cycles / 200000000 × 1000；A53毫秒 = wall_ticks / timer_counts_per_second × 1000。
P95取排序后第ceil(0.95×30)=29个样本；倍率大于1表示加速。
用户确认两个版本使用同一块AXU9EGB。v3对照为本任务重新采集的记录，早于本次断电；两个版本为不同启动，不能称为同一次启动的测量。
加载 39.980274s，6.494609MiB/s。
其中发送及逐块目标回读CRC 22.486244s，最后整份目标回读CRC 17.492864s。
本任务v3 PS DDR加载 8.526630s；该差异是A53加载/校验路径的成本，不能等同于lm_head计算性能变化。
早期PL DDR逐字节回读加载约255.17s；改为64位目标读取及16KiB PS暂存后，仍逐块/整份校验实际PL DDR。
单次256KiB目标回读微基准与TCP队列修复证据分别见target_crc_bench.json和TCP_LOADER_FIX_VERIFICATION.json。
时序 WNS/WHS/WPWS：0.632/0.01/0.143ns。

原始路径、完整统计、版本与 hash 见 comparison.json 和配套 RUN_PROFILE/ARTIFACTS.sha256。
范围限于独立 M14 的归档有限输入；未验证整体 LLM、候选稀疏化、上游直供权重或极端数值矩阵。
内部权重等待计数与“权重字节/IP时间”不能代替外部 AXI/MIG 带宽监测。
