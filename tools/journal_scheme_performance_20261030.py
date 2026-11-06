"""Project performance view: explicit methods and raw-timing aggregate.
Keeps the current dev-log renderer for the rest of the page.
"""
from pathlib import Path
import json,struct,statistics,hashlib,math,re
CASES={'aggregate':'综合（四类等权）','chinese':'中文','english':'英文','code':'代码','math':'数学'}
METHODS=[('baseline_hybrid','hybrid128','board-early',128,16384,128),('exp10','hybrid256','board-exp10',256,8192,64)]
def prepare(d,root):
    p=d['performance'];by_id={v['id']:v for v in p['variants']};schemes=[];proof=[]
    if not any(m['id']=='mean_ms' for m in p['metrics']):p['metrics'].append(dict(id='mean_ms',label='平均调用耗时',unit='ms',definition='综合为四类各30次原始计时的等权平均；其倒数用于综合输出率。'))
    for variant,key,prefix,C,L,rank in METHODS:
        name=f'L2聚类{C}中心＋rank{rank}低秩预筛＋BF16候选精算'
        params=f'聚类：{C}个L2中心，取最近4簇，每簇最多{L}个ID；低秩：rank{rank}，稳定Top16384；两路升序去重并入14个特殊ID，读取原始BF16权重，按固定FP32合同精算候选行。'
        base=root/'module_14_lm_head_v4'
        if variant=='exp10':base=base/'experiments/fusion_exp10_20261023'
        seconds=[];sources=[];case_ids={};counts=[];per_case={}
        for case in list(CASES)[1:]:
            folder=base/'reports/board_acceptance_20261030_r3'/case
            h=struct.unpack('<16I4Q8I',(folder/'header.bin').read_bytes());raw=list(struct.iter_unpack('<16I8Q',(folder/'records.bin').read_bytes()))
            sample=[(r[17]-r[16])/h[16] for r in raw if r[1]==1];assert len(sample)==30 and all(t>0 for t in sample)
            seconds.extend(sample);counts.append(raw[0][7]);per_case[case]=dict(measurements=30,sum_seconds=sum(sample),mean_ms=statistics.mean(sample)*1000)
            id=prefix+'-'+case;v=by_id[id];case_ids[case]=id
            v.update(label=name+' · '+CASES[case],scheme_id=key,scheme_name=name,scheme_explanation=params,evaluation=case)
            v['specification']=[dict(label='稀疏化方法',value='L2聚类路由与低秩预筛取并集，再做BF16候选精算',priority=True),dict(label='聚类参数',value=f'{C}中心 / 最近4簇 / 每簇上限{L} ID'),dict(label='低秩参数',value=f'rank{rank} / Top16384'),dict(label='精算与输出',value=f'canonical BF16；固定输入候选K={raw[0][7]} → 1 token'),dict(label='输入维度',value='H=896 / 完整词表V=151936')]
            v['specification']=[s for s in v['specification'] if s['label'] not in ['稀疏化方法','聚类参数','低秩参数']]
            v['values']['mean_ms']=statistics.mean(sample)*1000
            sources.append(dict(case=case,path=str(folder.relative_to(root)).replace('\\','/'),header_sha256=hashlib.sha256((folder/'header.bin').read_bytes()).hexdigest(),records_sha256=hashlib.sha256((folder/'records.bin').read_bytes()).hexdigest(),counter_hz=h[16],measurements=30))
        rate=120/sum(seconds);mean=statistics.mean(seconds)*1000;median=statistics.median(seconds)*1000;p95=sorted(seconds)[math.ceil(.95*120)-1]*1000
        id=prefix+'-aggregate';values={m['id']:None for m in p['metrics']};values.update(decode=rate,mean_ms=mean,a53_median=median,a53_p95=p95)
        latest=max(by_id[x]['measured_at'] for x in case_ids.values())
        aggregate=dict(id=id,label=name+' · '+CASES['aggregate'],scheme_id=key,scheme_name=name,scheme_explanation=params,evaluation='aggregate',scope='实板四固定输入等权综合 · A53完整调用',measured_at=latest,values=values,specification=[dict(label='稀疏化方法',value='L2聚类路由＋低秩预筛并集＋canonical BF16精算',priority=True),dict(label='聚类参数',value=f'{C}中心 / 最近4簇 / 每簇上限{L} ID'),dict(label='低秩参数',value=f'rank{rank} / Top16384'),dict(label='综合规模',value=f'中文/英文/代码/数学各30次，共120次；每类权重25%；K范围{min(counts)}–{max(counts)}'),dict(label='输入/输出',value='H=896 / V=151936；四个冻结hidden/history，每次输出1 token')],conditions='200MHz配置 / PL DDR。综合输出率=120 ÷ 120次实际调用耗时之和（秒）=1000/平均耗时_ms；只使用measurement记录，排除每类3预热和1000稳定调用。四固定输入等权汇总，不外推为整批语料或真实LLM生成。')
        aggregate['specification']=[s for s in aggregate['specification'] if s['label'] not in ['稀疏化方法','聚类参数','低秩参数']]
        p['variants']=[v for v in p['variants'] if v['id']!=id]+[aggregate]
        schemes.append(dict(id=key,name=name,explanation=params,short=f'{C}中心＋rank{rank}',variant_ids=dict(aggregate=id,**case_ids),historical_alias='早期v4混合' if variant=='baseline_hybrid' else '实验10融合'))
        proof.append(dict(scheme_id=key,name=name,formula='120 / sum((end_ticks-start_ticks)/counter_hz), only kind=1 measurement records',class_weights={c:.25 for c in case_ids},measurements=120,rate=rate,mean_ms=mean,pooled_median_ms=median,pooled_p95_ms=p95,per_case=per_case,sources=sources))
    legacy_names={'m14-100mhz':'BF16完整词表精算 · 100MHz / PS DDR（历史）','m14-200mhz-candidate':'BF16完整词表精算 · 200MHz原源码（历史未达标）','lm-head-v2-100mhz-20261019':'BF16完整词表精算 · 100MHz / PS DDR（同板复测）','lm-head-v3-200mhz':'分层规约BF16完整词表精算 · 200MHz / PS DDR','lm-head-v3-v31-task-baseline':'分层规约BF16完整词表精算 · PS DDR迁移对照','lm-head-v31-pl-ddr':'分层规约BF16完整词表精算 · 200MHz / PL DDR','lm-head-v4-sparse-offline':'L2聚类128中心＋rank128低秩＋BF16精算（历史离线候选）'}
    for v in p['variants']:
        if v['id'] in legacy_names:v['label']=legacy_names[v['id']]
    p['default_variant']='board-exp10-aggregate';p['candidate_note']='默认比较两种实板稀疏化方案的四类等权综合结果；可切换单类。历史完整词表版本保留单独口径，未测项保持未测。'
    p['metrics'][next(i for i,m in enumerate(p['metrics']) if m['id']=='decode')]['definition']='单输入：1000/30次调用Median_ms；四类综合：120/120次实际调用耗时之和（秒）。'
    p['scheme_comparison']=dict(schemes=schemes,evaluations=CASES,default_evaluation='aggregate',formula='四类各30次、各占25%；综合输出率=120/Σ实际调用秒数。先汇总耗时再求输出率，不直接平均四个次/s，也不把Median当平均值。',source='doc/log_rebuild_20261030/BOARD_SCHEME_AGGREGATES.json')
    p['history']['points']=[] # No time-series: categorical method comparison replaces it.
    for route in d['exploration']['routes']:
        if route['id'] in ['R4Sparse','R4Exp10']:
            method=schemes[0 if route['id']=='R4Sparse' else 1];route['title']=method['name'];route['design']['overview']=method['explanation']+' '+route['design']['status_note']
    out=root/'doc/log_rebuild_20261030/BOARD_SCHEME_AGGREGATES.json';out.write_text(json.dumps(dict(state='DERIVED_FROM_240_SAVED_RAW_MEASUREMENTS_NO_NEW_TESTS',methods=proof),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def apply(page):
    source=Path(__file__).with_name('journal_scheme_performance_20261030.js').read_text(encoding='utf-8')
    html=page.read_text(encoding='utf-8')
    html,n=re.subn(r'(<script id="dev-log-performance-js">).*?(</script>)',lambda m:m[1]+'\n'+source+'\n'+m[2],html,flags=re.S);assert n==1
    css='''<style id="project-scheme-performance-css">
.scheme-name{font-size:20px;line-height:1.55;font-weight:750;color:#24574f;margin:4px 0 10px;overflow-wrap:anywhere}.scheme-method{background:#edf5f1;padding:12px;border-radius:9px;line-height:1.8;margin:0 0 15px}.scheme-method b{display:block}.scheme-chart-toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.scheme-chart-toolbar select{max-width:100%;padding:8px}.perf-heading{flex-wrap:wrap}.perf-select{max-width:100%}.perf-select select{max-width:100%;width:min(650px,100%)}.scheme-chart-table{margin-top:14px}.scheme-chart-table th,.scheme-chart-table td{padding:8px}.scheme-selected{background:#eaf4ee}.scheme-plot svg{min-width:0!important;width:100%;height:auto!important}.scheme-plot text{font:14px system-ui,sans-serif}.scheme-plot .bar{cursor:pointer;outline-offset:4px}.scheme-plot .bar:focus{stroke:#172d28;stroke-width:3px}.scheme-chart-note{font-size:12px;color:#536977;line-height:1.8}.scheme-scope{margin:10px 0;font-size:13px}
@media(max-width:800px){.scheme-name{font-size:17px}.scheme-method{font-size:13px}.scheme-chart-table{font-size:12px}.scheme-chart-table th,.scheme-chart-table td{padding:5px}.perf-heading .perf-select{width:100%}}
</style>'''
    html=html.replace('</head>',css+'\n</head>');page.write_text(html,encoding='utf-8')
