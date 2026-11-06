"""Publish real stage-C evidence; no tool run or remote action."""
from pathlib import Path
import hashlib,json,html,re
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/partial_hw_20261024_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def loops(d):return {x['loop']:x['achieved_ii'] for x in d['pipeline_results']}
def main():
    h2=read(R/'r2/HLS_QUALIFICATION.json');h3=read(R/'r3/HLS_QUALIFICATION.json')
    for rev in ['r2','r3']:assert read(R/rev/'CSIM_QUALIFICATION.json')['state']=='PASS_FULL_CSIM_ARRAYS'
    q=read(R/'r3/CSIM_QUALIFICATION.json');good=h3['resources_fit_device'] and h3['estimate_within_internal_budget']
    stage='CSIM_PASS_HLS_ESTIMATE_PASS_RTL_PENDING' if good else 'CSIM_PASS_HLS_TIMING_OR_RESOURCE_FAIL_NO_RTL'
    rows=[]
    for name,d in [('r2',h2),('r3',h3)]:
        ii=loops(d)
        rows.append(dict(revision=name,estimate_ns=d['estimate_ns'],resources=d['top']['resources'],fits=d['resources_fit_device'],budget_gate=d['estimate_within_internal_budget'],
            preview_ii=next(v for k,v in ii.items() if 'preview_channel_loop_preview_beat_loop'==k),
            histogram_ii=next(v for k,v in ii.items() if k in ['radix_key_loop','radix_cached_key_loop']),
            candidate_ii=next(v for k,v in ii.items() if k in ['candidate_word_loop_candidate_lane_loop','candidate_cached_scan']),
            key_scan_cycles=next(x['latency']['Worst-caseLatency'] for x in d['all_units'] if x['unit']=='p_anonymous_namespace_radix_candidates')))
    verdict='HLS内部时序估计与资源门槛通过；后续仍须RTL和实现。' if good else '当前HLS估计未达到内部时序/资源门槛；停止重EDA，保留结果，下一步需针对关键路径设计。'
    md=f'''# d64/Top4096最小硬件原型 · STHL HLS2022.2 · 2026-10-24

状态：{stage}。{verdict}

主配置仍为动态d64/Top4096、双BF16权重、B1024预览；没有调参、训练、重采质量或操作板卡。该方案既有新1000题召回99.9465%、最低类别99.8381%，不是本轮重新认证。Csim证明的是相同稀疏算法CPU/GPU参考数值一致，而非全部问题均与dense相同。

## 已做的真实工作

- 本机2021.1头文件的native C++功能仿真通过；它不是正式HLS Csim。
- 用户指定STHL后，显式zhangben/7626连接nvidia-Super-Server；Linux Vitis_HLS2022.2单列环境。包传输SHA、canonical和服务器重建B1024权重SHA、110源/输入及各修订新增源验证通过，只有权重路径绑定从D盘改为Linux。
- r1正式Csim通过，但综合HLS200-1013/984失败：两个DATAFLOW进程共读meta AXI。失败日志保留r1_failed，不将包装器返回或Csim当综合通过。
- r2在DATAFLOW前预取ID/history（35432B本地数据容量），Csim11有效/6负向及全数组复核通过；综合完成，但关键路径10.383ns、候选发出II14，未达到200MHz目标。
- r3是唯一针对性缓存调度变体：额外624184B键/ID数据缓存在片上，键长循环、候选先入RAM再独立AXI打包写回；通道排序用等价64位组合键。无假依赖pragma，FP32树/penalty/canonical精算均未改。正式Csim和全数组复核通过，11个actual与r1/r2逐字一致。

## 实际综合对照

目标周期5ns、uncertainty1.35ns，内部预算3.65ns。下面全部是HLS估计，未做布线STA。

|项目|r2|r3|
|---|---:|---:|
'''
    for label,a,b in [('估计关键路径ns',rows[0]['estimate_ns'],rows[1]['estimate_ns']),('预览主循环II',rows[0]['preview_ii'],rows[1]['preview_ii']),('直方图更新II',rows[0]['histogram_ii'],rows[1]['histogram_ii']),('候选发出II',rows[0]['candidate_ii'],rows[1]['candidate_ii']),('radix函数估计周期范围上界',rows[0]['key_scan_cycles'],rows[1]['key_scan_cycles'])]+[(k,rows[0]['resources'][k],rows[1]['resources'][k]) for k in ['BRAM_18K','DSP','FF','LUT']]:md+=f'|{label}|{a}|{b}|\n'
    md+='''
两个实际生成的AXI master均64位地址/128位数据。128拍预览连续读由HLS推断，但真实突发/4KiB拆分、仲裁、背压仍待RTL；推断记录不是板卡流量。

## 结果界限与下一步

有效测试包含8真实状态、A→B→A、全平局zero-hidden、生产debug=0，共11有效调用；另外6个坏配置/NaN门控。每次核对64通道、151936预览raw bits/排序键、完整候选ID/raw bits及token/score/CRC，独立脚本还从canonical BF16重算候选raw。不是新的独立语料质量评估。

不要把top XML的best/average绝对延迟换算为decode速度：best含坏配置直接返回，average不是输入样本平均，工具也会用其估计周期显示绝对时间。当前没有FPGA M14 token/s、整网decode或TTFT测量。

Csim中软件hls::stream峰值460320是无界CPU队列；不是实际FIFO深度128活性的证明。精算DATAFLOW合并至两条顶层AXI后，必须在RTL核验缓存/PIPO/FIFO活性及AXI仲裁背压。原型还总是写完整预览debug workspace，不能直接套用阶段B最小生产流量。

下一步先按真实时序结论决定是否需要局部再设计；达到门槛后，优先对关键选择器、预览块及有界FIFO做分段RTL，再安排一次完整配置联合RTL。分段通过不能替代最终完整RTL/200MHz系统实现。当前不自动启动RTL/实现、不导出旧IP身份、不操作板卡，不恢复wb/luyou/心跳，不改冻结/封存包。

证据：PLAN.json；NATIVE_QUALIFICATION；CSIM_QUALIFICATION；r1_failed；r2/r3各PLAN、remote_csim、CSIM_QUALIFICATION、remote_hls/syn/report、HLS_QUALIFICATION。失败与全部源快照均保留。
'''
    (R/'RESULT.md').write_text(md,encoding='utf-8')
    result=dict(state=stage,configuration=dict(d=64,T=4096,tile=1024),rows=rows,verdict=verdict,
        tool='Vitis_HLS2022.2 Linux STHL; local native2021.1 separately recorded',
        qualification=dict(quality='Existing99%gate unchanged, not recertified',native='PASS',csim_r1='PASS',csynth_r1='FAIL_DATAFLOW_SHARED_AXI',csim_r2='PASS',csim_r3='PASS',hls_r3=good,RTL='NOT_RUN',implementation='NOT_RUN',board='NOT_RUN',decode_speed='NOT_MEASURED'),
        evidence_sha256={p.relative_to(R).as_posix():sha(p) for p in [R/'PLAN.json',R/'NATIVE_QUALIFICATION.json',R/'CSIM_QUALIFICATION.json',R/'r2/PLAN.json',R/'r2/CSIM_QUALIFICATION.json',R/'r2/HLS_QUALIFICATION.json',R/'r3/PLAN.json',R/'r3/CSIM_QUALIFICATION.json',R/'r3/HLS_QUALIFICATION.json',R/'RESULT.md']},
        no_automatic_next_stage=True,visual_QA='NOT_RUN')
    write(R/'RESULT.json',result)
    table='<table><thead><tr><th>指标</th><th>r2</th><th>r3</th></tr></thead><tbody>'
    for label,a,b in [('HLS关键路径 / ns',rows[0]['estimate_ns'],rows[1]['estimate_ns']),('预览主循环 II',rows[0]['preview_ii'],rows[1]['preview_ii']),('直方图更新 II',rows[0]['histogram_ii'],rows[1]['histogram_ii']),('候选发出 II',rows[0]['candidate_ii'],rows[1]['candidate_ii'])]+[(k,rows[0]['resources'][k],rows[1]['resources'][k]) for k in ['BRAM_18K','DSP','FF','LUT']]:table+=f'<tr><td>{label}</td><td>{a}</td><td>{b}</td></tr>'
    table+='</tbody></table>'
    links=[('RESULT.md','完整阶段报告'),('r1_failed/csynth.log','r1原始接口失败'),('r2/CSIM_QUALIFICATION.json','r2全数组复核'),('r2/HLS_QUALIFICATION.json','r2综合审计'),('r3/PLAN.json','r3冻结参数与源SHA'),('r3/CSIM_QUALIFICATION.json','r3全数组及r1逐字对照'),('r3/HLS_QUALIFICATION.json','r3综合审计'),('r3/remote_hls/syn/report/lm_head_v4_partial_proto_csynth.rpt','r3原始顶层综合报告')]
    body=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>v4 最小硬件原型 · STHL</title><style>body{{background:#f2f5ef;color:#233f3c;font:16px/1.8 system-ui,'Microsoft YaHei',sans-serif}}main{{max-width:1100px;margin:auto;padding:24px}}section{{background:white;border:1px solid #d5e2d9;border-radius:16px;margin:22px 0;padding:24px}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;border-bottom:1px solid #dbe3dc;text-align:left}}th{{background:#edf4ee}}a{{color:#287267}}.note{{background:#fff3d6;padding:18px}}.flow{{background:#edf5ef;padding:18px}}code{{overflow-wrap:anywhere}}</style><main><a href="V4Validation.html#gpu-summary">← GPU汇总</a> · <a href="V4LayoutTopK.html">布局与Top-T评审</a><h1>d64 / Top4096 最小硬件原型</h1><p>2026-10-24 · STHL / Linux / Vitis HLS2022.2</p><section><h2>当前结论</h2><p><b>{html.escape(verdict)}</b></p><p>正式Csim：11/11调用通过，另6项错误门控通过；r3与r1/r2完整输出逐字一致。新FPGA decode速度和TTFT仍未测。</p><p class="note">数值正确、HLS估计、RTL验证、布线时序、板卡验收分别记录。Csim通过不能替代RTL，HLS周期和资源不能直接作为实板性能。</p></section><section><h2>每轮解决了什么</h2><p><b>r1：</b>复用canonical精算，Csim通过；综合因两个DATAFLOW进程共读meta AXI失败。</p><p><b>r2：</b>DATAFLOW前预取ID/history，增加35432B片上数据容量，综合生成RTL；但候选扫描中AXI读→判断→写反馈使II14、关键路径10.383ns。</p><p><b>r3：</b>用片上key/ID缓存分开读、计算和写回，保留r2修复；通道排序改为等价64位组合键。没有更换d、Top-T、权重、FP32归约或质量口径。</p><div class="flow">动态通道 → 分块FP32预览 → penalty / 排序键 → key片上缓存 → 4轮radix阈值 → 全局ID扫描 → 候选RAM → 独立AXI写回 → canonical候选精算</div></section><section><h2>真实HLS报告对照</h2><p>5ns目标、1.35ns uncertainty，内部预算3.65ns；资源均为HLS估计。没有布局布线或实板测量。</p>{table}<p>两个生成AXI master均64位地址、128位数据；预览推断128拍连续读。真实AXI突发、背压和仲裁仍需RTL核验。</p></section><section><h2>验证边界与下一步</h2><p>8个真实状态来自既有GPU轮次的原4＋新4固定输入，另有zero-hidden全平局、ABA和生产模式，共11有效调用。核对64通道、全151936预览/排序键、完整候选/raw logits、token/score/CRC。原新1000题质量结果保持99.9465%整体、99.8381%最低类别，未用已打开组调参。</p><p>top XML的best包含坏配置返回路径，average不是输入数据均值，不能换算成decode吞吐。Csim软件stream峰值460320不能证明深度128 FIFO不会阻塞。</p><p>后续先根据关键路径决定局部设计，再做关键选择器、预览块、有界FIFO的分段RTL，最后一次完整配置联合RTL与新200MHz系统资格。当前无自动RTL/实现或板卡操作。</p></section><section><h2>原始证据</h2><ul>'''
    body+=''.join(f'<li><a href="../../module_14_lm_head_v4/reports/partial_hw_20261024_r1/{path}">{label}</a></li>' for path,label in links)
    body+='</ul><p>页面无需网络或脚本；浏览器视觉检查尚未运行。</p></section></main></html>'
    page=ROOT/'doc/design/V4PartialHardware.html';page.write_text(body,encoding='utf-8')
    result['page_sha256']=sha(page);write(R/'RESULT.json',result)
    for dest in [R/'PROGRESS.json',R/'r3/PROGRESS.json']:write(dest,dict(stage='STAGE_C_COMPLETE',verdict=stage,no_active_workflow=True,next='No automatic RTL/implementation',board='NOT_RUN'))
    print(json.dumps(dict(state=stage,rows=rows)))
if __name__=='__main__':main()
