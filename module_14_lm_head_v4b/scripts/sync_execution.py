"""Render saved v4b execution evidence without launching experiments."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,re,hashlib
M=Path(__file__).resolve().parents[1];ROOT=M.parent;O=M/'reports/quantization_20261023_r1'
PAGE=ROOT/'doc/design/V4bValidation.html'
def read(p,default=None):return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def main():
    if (O/'FINAL_QUALITY.json').exists():
        import importlib.util
        spec=importlib.util.spec_from_file_location('v4b_finalize_cpu_gpu',Path(__file__).with_name('finalize_cpu_gpu.py'))
        audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit);audit.main()
    saved=read(M/'experiments/quantization_study/PLAN.json');papers=read(ROOT/'doc/paper/lm_head_quantization/manifest.json')['papers']
    baseline=read(M/'baseline/SOURCE_LOCK.json');progress=read(O/'PROGRESS.json',{})
    points=[read(p) for p in sorted((O/'points').glob('*/RESULT.json'))]
    rtn=[r for r in points if r['method']=='RTN'];methods=[r for r in points if r['method']!='RTN']
    baseline_result=read(O/'Q01_BASELINE.json');dense=read(O/'DENSE_CALIBRATION.json')
    refine=read(O/'REFINE_CALIBRATION.json');bench=read(O/'GPU_BENCHMARK.json')
    reserved=read(M/'data/final_quality_20261023/MANIFEST.json');final=read(O/'FINAL_QUALITY.json');access=read(O/'FINAL_LABEL_ACCESS.json')
    for e in saved['experiments']:
        e['execution']=dict(stages={},records=[],evidence=[])
        if e['id']=='q01' and baseline_result:
            e['status']='COMPLETE_OFFLINE' if dense else 'RUNNING'
            e['execution']=dict(stages=dict(quality='PASS_BASELINE' if dense else 'RUNNING'),records=[],
              message='原8步完整raw/policy SHA、token/score/CRC及四类完整CPU/GPU raw通过；'+('5095校准token/score bits逐位通过。' if dense else '完整校准重算中。'),
              evidence=['Q01_BASELINE.json','DENSE_CALIBRATION.json'])
        if e['id']=='q02':
            e['status']='COMPLETE_OFFLINE' if len(rtn)==32 else ('RUNNING' if rtn or progress.get('stage','').startswith(('QUANT','CALIBRAT')) else 'NOT_RUN')
            e['execution']=dict(stages=dict(quality=f'{len(rtn)}/32 校准点'),records=rtn,evidence=['RTN_CALIBRATION.json','RTN_CALIBRATION.partial.json','CALIBRATION_DISCUSSION.md'],
              message='实际packed权重、独立解包逐位核验、四类全raw CPU/GPU证明，以及每点5095预测。仅旧校准集；作业总耗时不是推理benchmark。')
        if e['id']=='q03' and methods:
            e['status']='COMPLETE_OFFLINE' if len(methods)==8 else 'RUNNING'
            controls=[r for r in rtn if r['bits'] in [4,8] and r['group'] in [64,128] and not r['symmetric']]
            e['execution']=dict(stages=dict(quality=f'{len(methods)}/8 新点＋{len(controls)}控制'),records=controls+methods,
              message='GPTQ静态组/无act-order；AWQ-style只借通道缩放，5个alpha在训练内部选择；未宣称完整官方AWQ复现。',evidence=['METHODS_CALIBRATION.json','METHODS_CALIBRATION.partial.json'])
        if e['id']=='q07' and refine:
            e['status']='COMPLETE_OFFLINE';e['execution']=dict(stages=dict(quality='PASS_CALIBRATION_RECALL'),records=[],refine=refine,
              message='全5095步真实量化preview的policy后dense赢家稳定排名；候选召回评估不是在线Top-K测速。完整在线管线数值证明与计时见实验8。',evidence=['REFINE_CALIBRATION.json'])
        if e['id']=='q08' and bench:
            e['status']='PARTIAL_OFFLINE';e['execution']=dict(stages=dict(gpu='PASS_PACKED_GPU_REFERENCE',implementation='NOT_RUN'),records=[],benchmark=bench,
              message='真正packed GPU参考，同轮BF16控制；不是旧Eager速率复测，不推断FPGA加速。AXI微核/HLS资源仍未执行。',evidence=['GPU_BENCHMARK.json','BENCHMARK_NUMERIC_PROOF.json'])
        if e['id']=='q09' and reserved:
            e['fixed']=[line.replace('代码候选来源MBPP官方未用任务，排除prompt/参考解/同任务近重复后若不足，先修订来源/配额再锁定。','代码100题已改用官方DS-1000固定提交，按origin family去重并作trigram检查；原MBPP仅剩10非few-shot未用题。') for line in e['fixed']]
            if (M/'data/final_quality_20261023/EVALUATION_ENTRY_LOCK.json').exists():
                e['fixed']=[line.replace('计划尚未冻结语料与入口；必须在首次标签采集前生成','本轮已在首次标签采集前生成') for line in e['fixed']]
            e['execution']=dict(stages=dict(quality='FINAL_COMPLETE' if final else ('COLLECTING_OR_EVALUATING_FROZEN_GROUP' if access else 'PROMPTS_RESERVED_LABELS_NOT_OPENED')),records=[],
                message='已预留1000题（中400/英250/DS-1000代码100/数学250），零旧规范化group/prompt重叠；输入33–882 tokens。'+('本轮最终质量已完成，禁止用已打开组调参再认证。' if final else ('新组已打开，正在按锁定入口采集/评估；禁止改点重认证。' if access else '最终标签尚未采集，须先锁候选与执行入口。')),
                final=final,evidence=['FINAL_QUALITY.json'] if final else [])
            e['status']='COMPLETE_OFFLINE' if final else ('RUNNING' if access else 'PREPARED')
    saved['status']='AUTHORIZED_OFFLINE_EXECUTION';saved['scope']='User authorized offline experiments on2026-10-23; board remains excluded'
    saved['experiment_entry_frozen']=(O/'ENTRY_LOCK.json').exists()
    saved['forbidden_actions']=['board connection/probe/run','wb/luyou/heartbeat','editing frozen v3.1/v4 packages','unapproved expansion or retuning on opened final group']
    if reserved:
        saved['proposed_data']['final']='Reserved fresh1000: Chinese400/English250/DS-1000code100/math250; live access state in FINAL_LABEL_ACCESS.json'
        saved['proposed_data']['lock_status']='FROZEN_BEFORE_LABELS' if access else 'PROMPTS_RESERVED_ENTRY_PENDING'
    state=dict(updated=progress.get('updated'),stage=progress.get('stage'),pid=progress.get('pid'),
      active=(O/'ACTIVE.lock').exists(),completed_quantization_points=len(points),rtn_points=len(rtn),method_points=len(methods),
      baseline='PASS' if dense else ('RUNNING' if baseline_result else 'NOT_RUN'),
      final_quality=final['state'] if final else ('FROZEN_GROUP_OPENED_COLLECTION_OR_EVALUATION' if access else 'NOT_RUN'),hls='NOT_RUN',rtl='NOT_RUN',board='NOT_RUN',progress=progress)
    calibration_quality=[]
    if bench:
        for method in bench['methods']:
            if method['kind']=='dense':
                q=dict(steps=4775,misses=0,recall=1.0,by_category={c:dict(steps=n,misses=0,recall=1.0) for c,n in [('chinese',1200),('english',1175),('code',1200),('math',1200)]})
                origin='canonical dense definition; all5095 labels/score bits independently reproduced'
            elif method['kind']=='refine':
                point=next(r for r in refine['configurations'] if r['preview']==method['source'] and r['K']==method['K'])
                q=point['quality']['decode'];origin='REFINE_CALIBRATION.json: policy dense winner membership'
            else:
                point=next(r for r in points if r['id']==method['source'])
                q=point['quality']['decode'];origin='points/'+point['id']+'/RESULT.json: actual token agreement'
            calibration_quality.append(dict(id=method['id'],quality=q,origin=origin))
    data=dict(plan=saved,papers=papers,baseline=baseline,execution=state,gpu_benchmark=bench,final_quality=final,calibration_quality=calibration_quality)
    template=Path(__file__).with_name('research_page.html').read_text(encoding='utf-8')
    template=template.replace('实验全部未开始','离线实验已授权开展')
    template=template.replace('此页仅组织研究与计划，任何点击都不执行实验。本次未量化权重、拟合、采集新标签、GPU测速或EDA，未连接、探测或操作板卡。既有v3.1/v4冻结包与v4实验10结论保持。',
      '本页展示实验计划与已保存证据，点击不会执行作业。当前仅本机离线实验；独立最终质量、EDA和板卡状态分别记录。v3.1/v4冻结资产保持，未连接或探测板卡。')
    template=template.replace('32</strong><span>RTN首轮量化点 · 尚未执行','32</strong><span>RTN首轮量化点 · 实际完成 '+str(len(rtn)))
    template=template.replace('<strong>0</strong><span>本次已执行的量化实验','<strong>'+str(len(points))+'</strong><span>已完成的量化配置（校准阶段）')
    template=template.replace('当前只是设计，执行入口、最终语料与候选参数尚未冻结。',
      '执行入口、两个候选及新1000题均在首次标签前锁定；本轮最终质量已完成，硬件资格尚未开展。' if final else '旧train/calibration入口已冻结并开始执行；独立最终语料与生产候选尚未锁定。')
    template=template.replace('状态来自保存证据；所有新结果均为空。','状态来自本轮保存证据；未运行阶段继续保留NOT_RUN。')
    template=template.replace('<a href="../../module_14_lm_head_v4b/README.md">v4b README</a>',
      '<a href="../../module_14_lm_head_v4b/README.md">v4b README</a><a href="../../module_14_lm_head_v4b/NUMERIC_CONTRACT.md">数值与packing契约</a><a href="../../module_14_lm_head_v4b/HARDWARE_FEASIBILITY.md">后续硬件检查</a>')
    template=template.replace('../../module_14_lm_head_v4b/reports/research_design/VALIDATION.json','../../module_14_lm_head_v4b/reports/quantization_20261023_r1/PAGE_VALIDATION.json')
    if reserved:
        template=template.replace('新1000题只是拟议配额：中400 / 英250 / 代码100 / 数学250。尚未选择、冻结或采集。HumanEval旧题已用完，代码拟审查MBPP剩余可用任务；不足时在标签前修订来源或配额，不能把旧已打开题补进认证组。','新1000题文本已预留：中400 / 英250 / DS-1000代码100 / 数学250；origin-family及规范化/词三元组去重，tokenizer输入33–882。候选与执行入口锁定后才采集标签；最终是否已打开见实验9与真实报告。')
    template=template.replace('这里只浏览计划','这里只浏览计划与结果')
    if bench:
        template=template.replace('<section class="panel" id="baseline">','<p class="notice"><a href="#gpu-timing">查看已测GPU时间对比图：6方案中位数/P95与四类输入分项 →</a></p><section class="panel" id="baseline">')
        timing_panel='''<section class="panel" id="gpu-timing"><div class="eyebrow">MEASURED · GPU REFERENCE</div><h2>已测时间对比 · 同轮GPU参考</h2><p>RTX 5060 Laptop GPU · batch=1 · 720次实测。W12直接量化中位耗时1.170ms，BF16为1.346ms，W4预筛＋K512精算为1.722ms。</p><div id="gpu-timing-charts"></div><p class="notice">W4/W8直接量化只是未过质量校准的诊断对照；速度快不能替代质量通过。W12与W4＋K512是通过新问题质量门槛的锁点。两方案仍待硬件资格验证。</p><p class="section-note">计时范围：W、hidden与history已驻留GPU → 实际解包、dot、policy、必要的Top-K/gather/BF16精算 → CPU token/score/CRC，调用前同步。不计初始化、编译、上传、模型前向和语料采集。仅独立M14参考，不是整网decode、TTFT或FPGA性能；也不与旧Eager绝对速率比较。</p><div class="filelinks"><a href="#q08">实验8：完整时间表与方法</a><a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/GPU_BENCHMARK.json">计时汇总</a><a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/GPU_TIMING_RAW.json">720条原始计时</a></div></section>'''
        quality_panel='''<section class="panel" id="quality-comparison"><div class="eyebrow">MEASURED · FINAL QUALITY</div><h2>质量对比 · 新独立1000题</h2><p>与上方时间图中的两个最终锁点对应：W12直接量化与W4预筛＋K512 BF16精算。</p><div id="final-quality-chart"></div><p class="section-note">这是固定dense轨迹下的条件token一致性；本组零错误不能证明数学无损或闭环生成无误。未过校准的W4/W8直接量化未进入本次最终认证。</p><div class="filelinks"><a href="#q09">实验9：最终质量明细</a><a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/FINAL_QUALITY.json">原始质量计数</a></div></section>''' if final else ''
        if quality_panel:
            quality_panel=quality_panel.replace('<div class="eyebrow">MEASURED · FINAL QUALITY</div><h2>质量对比 · 新独立1000题</h2><p>与上方时间图中的两个最终锁点对应：W12直接量化与W4预筛＋K512 BF16精算。</p>',
              '<div class="eyebrow">MEASURED · QUALITY COMPARISON</div><h2>质量对比 · 对应上方全部6个计时方案</h2><h3>同一校准集：6方案完整对照</h3><div id="calibration-quality-chart"></div><h3>新独立1000题：两个预先锁定方案</h3><p>下图单独报告最终认证；其余计时方案未在这组新问题上评估，不能用校准结果补填。</p>')
        template=template.replace('<section class="panel" id="experiments">',timing_panel+quality_panel+'<section class="panel" id="experiments">')
    template=template.replace('全部未开始 · 论文与实验可相互跳转','状态按真实证据更新 · 论文与实验可相互跳转')
    template=template.replace('<span class="pill">未开始</span></button>','<span class="pill">${statusName(x.status)}</span></button>')
    template=template.replace('${esc(k)}：NOT_RUN','${esc(k)}：${esc(x.execution?.stages?.[k]||"NOT_RUN")}')
    template=template.replace('<p class="blank">尚未执行，无质量/速度曲线；测量值为null。计划参数与预算不能代填实验结果。</p>','${evidencePanel(x)}')
    template=template.replace('量化构造 / 校准 / 新独立质量 / GPU</td><td>NOT_RUN</td><td>无实验测量数据；页面不自动执行',
       '量化构造 / 校准</td><td>'+str(len(points))+'配置已完成</td><td>'+('新独立质量已完成；GPU720次测量；硬件NOT_RUN' if final else '新独立质量NOT_RUN；页面不自动执行'))
    template=template.replace('没有重跑数值验收，也没有重新hash整份canonical W。','本轮已重hash canonical W并完成新基线数值复现；详情见实验1。')
    template=template.replace('<section class="panel" id="roadmap">','<section class="panel"><h2>当前执行快照</h2><p>'+str(state['stage'])+' · '+str(state['updated'])+'</p><p>RTN '+str(len(rtn))+'/32，GPTQ/AWQ-style '+str(len(methods))+'/8；基线 '+state['baseline']+'。当前阶段终态以日志与RESULT为准，PID仅用于核对。</p><div class="filelinks"><a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/PROGRESS.json">实时PROGRESS</a><a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/PLAN.json">执行PLAN</a><a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/ENTRY_LOCK.json">入口锁定</a>'+('<a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/RESULT.md">最终报告</a><a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/FINAL_INDEPENDENT_REVIEW.json">独立复核</a>' if final else '')+'</div></section><section class="panel" id="roadmap">')
    helper=r'''
function statusName(s){return ({COMPLETE_OFFLINE:'离线阶段完成',PARTIAL_OFFLINE:'部分完成',RUNNING:'进行中',PREPARED:'文本已准备',NOT_RUN:'未开始'})[s]||s;}
function chart(records,field,label){
 if(!records.length)return '';
 const colors=['#17664e','#335e88','#ad7c33','#8c618c','#427e89','#8e6654','#6e8639','#9a5d66'],series=[];
 for(const group of [32,64,128,896])for(const sym of [true,false]){
   const points=records.filter(r=>r.group===group&&r.symmetric===sym).sort((a,b)=>a.bits-b.bits);
   if(points.length)series.push({name:'G'+group+(sym?' 对称':' 非对称'),points});
 }
 const W=700,H=270,left=55,top=20,right=20,bottom=50;
 const max=Math.max(1,...records.map(field)),xx=b=>left+(b-4)/8*(W-left-right),yy=v=>H-bottom-v/max*(H-top-bottom);
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}" style="width:100%;height:auto;font:12px Microsoft YaHei,sans-serif">`;
 for(let i=0;i<=4;i++){const v=max*i/4,y=yy(v);svg+=`<line x1="${left}" x2="${W-right}" y1="${y}" y2="${y}" stroke="#d9e3d8"/><text x="${left-7}" y="${y+4}" text-anchor="end">${v.toFixed(max>100?0:1)}</text>`;}
 for(const b of [4,6,8,12])svg+=`<text x="${xx(b)}" y="${H-bottom+22}" text-anchor="middle">${b} bit</text>`;
 series.forEach((s,i)=>{const c=colors[i];svg+=`<polyline points="${s.points.map(r=>xx(r.bits)+','+yy(field(r))).join(' ')}" fill="none" stroke="${c}" stroke-width="2"/>`;s.points.forEach(r=>svg+=`<circle cx="${xx(r.bits)}" cy="${yy(field(r))}" r="4" fill="${c}"><title>${esc(r.id)}: ${field(r)}</title></circle>`);});
 return `<h4>${esc(label)}</h4>${svg}</svg><p class="section-note">${series.map((s,i)=>`<span style="color:${colors[i]}">● ${esc(s.name)}</span>`).join('　')}。只连接同组长/同格式的已测点，空缺表示尚未完成。</p>`;
}
function evidencePanel(x){const e=x.execution||{};
 if(!e.message)return '<p class="blank">此阶段尚未执行。计划参数与静态预算不代填结果。</p>';
 let out=`<p class="control">${esc(e.message)}</p>`;
 if(e.records?.length){
  if(x.id==='q02')out+=chart(e.records,r=>r.quality.decode.misses,'校准decode错选数（越低越好）')+chart(e.records,r=>r.packed_bytes/1048576,'真实packed文件大小 / MiB');
  out+='<div class="table-scroll"><table style="min-width:850px"><thead><tr><th>配置</th><th>decode错选</th><th>decode一致率</th><th>全部预测错选</th><th>最差类别decode</th><th>packed MiB</th><th>保守校准门槛</th></tr></thead><tbody>';
  out+=e.records.map(r=>`<tr><td>${esc(r.id)}</td><td>${r.quality.decode.misses}/${r.quality.decode.steps}</td><td>${(100*r.quality.decode.recall).toFixed(4)}%</td><td>${r.quality.all.misses}/${r.quality.all.steps}</td><td>${(100*Math.min(...Object.values(r.quality.decode.by_category).map(x=>x.recall))).toFixed(4)}%</td><td>${(r.packed_bytes/1048576).toFixed(4)}</td><td>${r.conservative_calibration_gate?'通过':'未通过'}</td></tr>`).join('')+'</tbody></table></div>';
 }
 if(e.refine){out+='<div class="table-scroll"><table><thead><tr><th>preview</th><th>K</th><th>decode漏选</th><th>全部漏选</th><th>读取预算MiB</th></tr></thead><tbody>'+e.refine.configurations.map(r=>`<tr><td>${esc(r.preview)}</td><td>${r.K}</td><td>${r.quality.decode.misses}</td><td>${r.quality.all.misses}</td><td>${(r.main_read_bytes/1048576).toFixed(3)}</td></tr>`).join('')+'</tbody></table></div>';}
 if(e.benchmark){out+=gpuTimingCharts(e.benchmark)+'<div class="table-scroll"><table><thead><tr><th>方案</th><th>median ms</th><th>P95 ms</th><th>均衡等效M14输出/s</th></tr></thead><tbody>'+e.benchmark.methods.map(r=>`<tr><td>${esc(r.id)}</td><td>${r.median_ms.toFixed(3)}</td><td>${r.p95_ms.toFixed(3)}</td><td>${r.equivalent_outputs_per_second.toFixed(2)}</td></tr>`).join('')+'</tbody></table></div>';}
 if(e.final){out+=`<p><b>${esc(e.final.state)}</b> · ${e.final.prompts}问题 / ${e.final.decode_predictions}decode / 零排除</p><div class="table-scroll"><table><thead><tr><th>锁点</th><th>decode错选/漏选</th><th>decode一致率</th><th>整体与各类门槛</th></tr></thead><tbody>`+e.final.results.map(r=>`<tr><td>${esc(r.id)}</td><td>${r.quality.decode.misses}/${r.quality.decode.steps}</td><td>${(r.quality.decode.recall*100).toFixed(4)}%</td><td>${r.quality_gate?'通过':'失败，不重调'}</td></tr>`).join('')+'</tbody></table></div><p class="section-note">固定dense轨迹的条件一致性；不是闭环生成/任务正确率或实板验收。</p>';}
 if(e.final){out+='<div class="table-scroll"><table><thead><tr><th>锁点</th><th>中文错选/漏选</th><th>英文</th><th>代码</th><th>数学</th><th>首输出错选</th><th>整题decode全一致</th></tr></thead><tbody>'+e.final.results.map(r=>`<tr><td>${esc(r.id)}</td>${['chinese','english','code','math'].map(c=>{const q=r.quality.decode.by_category[c];return `<td>${q.misses}/${q.steps}</td>`;}).join('')}<td>${r.quality.prefill.misses}/${r.quality.prefill.steps}</td><td>${r.quality.complete_prompt_decode_match.all_steps_match_prompts}/${r.quality.prompt_groups}</td></tr>`).join('')+'</tbody></table></div>';}
 out+='<div class="filelinks">'+(e.evidence||[]).map(f=>`<a href="../../module_14_lm_head_v4b/reports/quantization_20261023_r1/${esc(f)}">${esc(f)}</a>`).join('')+'</div>';
 return out;
}
'''
    helper+=Path(__file__).with_name('gpu_timing_charts.js').read_text(encoding='utf-8')
    helper+=Path(__file__).with_name('quality_charts.js').read_text(encoding='utf-8')
    if bench:helper+='\n$("gpu-timing-charts").innerHTML=gpuTimingCharts(d.gpu_benchmark);\n'
    if bench and final:helper+='\n$("calibration-quality-chart").innerHTML=calibrationQualityChart(d.calibration_quality);\n'
    if bench and final:helper+='\n$("final-quality-chart").innerHTML=finalQualityChart(d.final_quality);\n'
    template=template.replace('function render(){',helper+'\nfunction render(){')
    PAGE.write_text(template.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')),encoding='utf-8')
    top=read(M/'PROGRESS.json');top.update(status='OFFLINE_EXPERIMENTS_RUNNING' if state['active'] else 'OFFLINE_STAGE_COMPLETE',updated=state['updated'],
      numerical=state['baseline'],gpu='PASS_PACKED_GPU_REFERENCE' if bench else 'NOT_RUN',final_quality=state['final_quality'],
      rtn_points=len(rtn),methods_points=len(methods),current_report='reports/quantization_20261023_r1',stage=state['stage'],
      next='Assess qualified candidates for separate hardware development; no automatic EDA/board stage or retuning' if final else 'Continue according to frozen plan; no board access')
    (M/'PROGRESS.json').write_text(json.dumps(top,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    import importlib.util
    check_spec=importlib.util.spec_from_file_location('v4b_page_validation',Path(__file__).with_name('validate_execution_page.py'))
    check=importlib.util.module_from_spec(check_spec);check_spec.loader.exec_module(check);check.main()
    print(json.dumps(state,ensure_ascii=False))
if __name__=='__main__':main()
