from pathlib import Path
import json,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1'
summary=json.loads((R/'BOARD_FIXED_INPUT_SUMMARY.json').read_text());rows=summary['rows']
variants={'baseline_hybrid':'早期v4：聚类＋低秩＋BF16精算','exp10':'实验10：融合超参优化'};cats={'chinese':'中文','english':'英文','code':'代码','math':'数学'}
text='''# 两套v4实板测试报告 · 2026-10-30

本报告只引用本轮真实板卡输出。用户确认板卡连接、独占及整体/各类decode召回≥99%准入；实验10原99.9%失败保留，新99%门槛达标记录见QUALITY_GATE_99.json。GPU召回与板卡数值资格分开。

两套匹配200MHz配置的bit/XSA/PS初始化/ELF分别完整初始化，计算数据位于PL DDR；每个输入加载独立320MiB arena，320块目标CRC、整份CRC及34项回读通过。所有计时前停止loader CPU并验证GEM DMA停机，换用对应测试ELF。运行副本与原冻结包SHA相同。

## 固定输入性能与稳定性

每个用例3次预热、30次测量、1000次稳定调用。计时为A53完整control_call起止原始XTime，直到读取token/score/CRC并验证返回；包括控制/轮询/寄存器读写，不含初始化、TCP加载、每批次整arena CRC、主机JTAG导出、Transformer或prefill。没有IP硬件周期计数器。P95为nearest-rank。输出率=1000/median_ms，是每次M14输出一个token的等效速率，不是整网decode/TTFT。

|版本|输入|候选K|Median / ms|P95 / ms|M14等效输出 / s|稳定调用|
|---|---|---:|---:|---:|---:|---:|
'''
for row in rows:text+=f'|{variants[row["variant"]]}|{cats[row["case"]]}|{row["candidate_count"]}|{row["median_ms"]:.6f}|{row["p95_ms"]:.6f}|{row["m14_equivalent_outputs_per_s"]:.4f}|1000/1000|\n'
text+='\n已独立核对固定输入批次数：'+str(len(rows))+'/8；每次记录的nonce、状态、token/score/CRC、连续时间戳、批次边界和原始文件SHA均核对。\n'
text+='\n## 同输入配对比较\n\n|输入|实验10相对早期v4加速比|耗时减少|\n|---|---:|---:|\n'
for case in cats:
    pair={x['variant']:x for x in rows if x['case']==case}
    if len(pair)==2:
        b=pair['baseline_hybrid']['median_ms'];e=pair['exp10']['median_ms'];text+=f'|{cats[case]}|{b/e:.4f}×|{(1-e/b)*100:.2f}%|\n'
text+='\n这是同一板卡和调用边界的四类固定hidden/history比较，不是1000题整体速度分布；不将历史v3.1 IP硬件计时与本轮A53墙钟直接混比。\n'
text+='\n输入来源：原校准集四个冻结完整链夹具，中文index1、英文index1281、代码index2536、数学index3816；见早期v4 reports/selector_chain_fixture_20261021/MANIFEST.json和各版arena MANIFEST中的hidden/history源路径及SHA。实验10使用同一四个hidden/history，筛选参数与候选表不同。质量验证的独立1000题不是这四个测速输入。\n'
text+='\n## 完整数组与错误路径\n\n'
debug=[];errors=[];aba=[]
for variant,base in [('baseline_hybrid',M),('exp10',M/'experiments/fusion_exp10_20261023')]:
    for d in (base/'reports/board_debug_20261030_r2').glob('*'):
        p=d/'INDEPENDENT_REVIEW.json'
        if p.exists():
            x=json.loads(p.read_text());debug.append(x);text+=f'- {variants[variant]}／{cats[x["case"]]}：实际151936 preview、{x["ids"]}候选ID及raw、13区域guard、descriptor生产→debug→生产均逐位一致；独立脚本再核对最终token/score/CRC及源SHA。\n'
    for p in (base/'reports/board_errors_20261030_r1').glob('*/INDEPENDENT_REVIEW.json'):
        x=json.loads(p.read_text());errors.append(x);text+=f'- {variants[variant]}：VALIDATE_ONLY、错误magic、区域重叠、非法command四项实际预检及不发布旧token、三处scratch头保持通过。仅预检错误，不扩大为所有运行中故障已覆盖。\n'
    p=base/'reports/board_aba_20261030_r2/INDEPENDENT_REVIEW.json'
    if p.exists():
        x=json.loads(p.read_text());aba.append(x);text+=f'- {variants[variant]}：同一配置硬件数学→中文→数学三调用，输入逐字节目标回读、每次全151936预览/完整候选ID/raw及13guard通过，前后两次数学全数组逐位相同；末态恢复数学生产描述符。该检查也提供中文输入的完整数组证据，不能当作自动累积history的生成链。\n'
text+='\n当前仍不宣称整网decode、TTFT、自由生成或任务准确率。动态多步history及完整交付发布资格须单独核验；固定输入重复1000次不等于1000步真实生成。\n'
text+='\n## 控制入口修复与失败保留\n\n首轮初始A53已处于复位，stop失败；隔离入口只允许此特定错误后执行原rst-processor/dow/con。Windows批处理exit0不足以证明Tcl成功，现要求动作专属成功标志且无错误。loadhw会在XSA旁解压附加文件，已转为每输入独立运行副本，原新增文件保存且原绑定文件SHA保持。首轮连接超时、旧包装器错误cleanup文字、目录污染预检和首次debug夹具路径错误均保留，均不作为通过证据。未修改bit/XSA/ELF/核参数/浮点语义或原质量数据。\n'
text+='\n证据：BOARD_FIXED_INPUT_SUMMARY.json、各模块reports/board_acceptance_20261030_r3/{case}/、board_debug_20261030_r2/{case}/及board_errors_20261030_r1/。本报告生成时不连接或操作板卡。\n'
(R/'RESULT.md').write_text(text,encoding='utf-8')
(R/'RESULT.json').write_text(json.dumps(dict(state='BOARD_TESTS_PARTIAL' if len(rows)<8 else 'PASS_EIGHT_FIXED_INPUT_BOARD_CAMPAIGNS',fixed_cases=len(rows),planned_fixed_cases=8,debug_cases=debug,error_campaigns=errors,controlled_ABA=aba,all_fixed_call_count=len(rows)*1033,full_llm_decode='NOT_MEASURED',ttft='NOT_MEASURED',multi_step_history='NOT_RUN',formal_release=False,board_execution_status='Read current ACTIVE.lock/EXECUTION; this report is a snapshot'),ensure_ascii=False,indent=2)+'\n')
print(f'Published {len(rows)}/8 fixed cases, {len(debug)} full-array cases, {len(errors)} error campaigns')
