"""Matched557 supplementary cohort plots, paired timings and unchanged first-six history."""
from pathlib import Path
import collections,csv,hashlib,html,io,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/sparse_quality_all557_20261024_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def e(v):return html.escape(str(v),quote=True)
def link(p,label):return f'<a href="../../{p.relative_to(ROOT).as_posix()}">{e(label)}</a>'
def attach(panel,historical):
    from render_v4_quality_cohorts import sources
    review=read(R/'INDEPENDENT_REVIEW.json');quality=read(R/'QUALITY.json');assert review['quality_sha256']==sha(R/'QUALITY.json')
    qmap={p['id']:p for p in quality['configurations']};base={p['id']:p for p in historical['points']}
    firstsix=read(M/'reports/sparse_quality_20261024_r1/SELECTION_LOCK.json')['configurations'];sixids=[p['id'] for p in firstsix]
    datasets={};csvoutputs={}
    for cohort in ['old','new']:
        timed=read(R/f'cohorts/{cohort}/TIMING_SUMMARY.json');assert len(timed['configurations'])==557
        points=[]
        for t in timed['configurations']:
            p=dict(base[t['id']]);p.update(rate=t['rate'],mean_ms=t['mean_ms'],median_ms=t['median_ms'],p95_ms=t['p95_ms'],cases=t['cases'],calls=120,raw=t['raw'])
            if cohort=='new':
                q=qmap[p['id']];p.update(quality=q['quality']['decode'],k=q['candidate_decode'],quality_source='module_14_lm_head_v4/reports/sparse_quality_all557_20261024_r1/QUALITY.json',independent=[],gate99=q['gate99'],fallback_decode=q['fallback_decode'],supplementary=True)
                p.pop('cost',None)
                if p['id'] in sixids:p['validation_identity']='首轮标签前冻结6点之一；本轮逐步hits/K与首轮一致'
                else:p['validation_identity']='打开标签后按用户要求追加；补充分析，不作新的独立认证'
            else:p['gate99']='PASS' if p['quality']['recall']>=.99 and all(v['recall']>=.99 for v in p['quality']['by_category'].values()) else 'FAIL'
            p['full_vocabulary_observed']=p['k'].get('min',0)==151936
            points.append(p)
        d=dict(historical,points=points,completed=read(R/'benchmark/RESULT.json')['completed'],default_selected='partial_dynamic_d64_T4096',old_selected=historical['old_selected'],measurements=66840,result_sha256=sha(R/'QUALITY.json'),benchmark_sha256=sha(R/'benchmark/RESULT.json'),review_sha256=sha(R/'INDEPENDENT_REVIEW.json'),timing_scope='本轮全部557配置、原4＋新4固定输入交错，当前组每配置120次完整M14 Eager计时')
        if cohort=='old':
            d.update(quality_label='校准',caption='原320校准题 × 557配置。本图速度改用本轮557配置/新旧8输入统一重测中的原4输入；配置与新组一一对应，历史557速度另存。',notice='横轴为调参用原320题/4775 decode召回；纵轴为本轮原4固定输入的120次完整GPU M14调用。与新组使用相同557配置驻留与同一计时轮次，仍不是整网decode或整批语料测速。',k_note='K均值/P95来自原组4775 decode步；速度来自本轮原4固定输入。',source_html=sources(False)+'<p>当前图的GPU速度为本轮配对重测，不采用旧557轮绝对速率。每配置旧4/新4输入分别各120次，共133680测量；两数据集单独计算120000/各自耗时毫秒总和。</p>')
            counts=collections.Counter(p['mode'] for p in points if p['gate99']=='PASS')
            d['source_html']+='<p>按当前整体及每类99%门槛回看原校准数据：'+e('；'.join(f'{historical["names"][k]} {v}点' for k,v in counts.items()))+'。这是描述性对照，包含全词表端点，不改变旧实验的原门槛/认证结论。</p>'
        else:
            counts=collections.Counter(p['mode'] for p in quality['configurations'] if p['gate99']=='PASS');names=historical['names']
            d.update(quality_label='新组补充',quality_scope='已打开新1000问题/14956decode，全部557配置补充分析；非新的独立认证',fresh_quality=True,default_min=98.5,caption='新1000题 × 全部557配置，与原校准图逐项对应；15956预测/14956 decode/零排除。首轮6点验证保留，本轮其余点为已打开数据上的补充分析，没有调参或重采集。',notice='横轴为新1000题召回；纵轴为本轮新4固定输入120次完整GPU M14实测，与原组同轮同557配置。整体及每类≥99%才记通过；全词表端点/dense回退须结合详情看，观察边界不等于独立认证或FPGA收益。',k_note='K均值/P95来自新组全部14956 decode步；速度来自本轮新4固定输入。',source_html='<p><b>本轮范围：557点全量补充分析。</b>新组先完成标签前冻结的六点验证，随后用户要求追加全部配置。以下六点表是历史首轮结果，所有557点本轮结果见图和完整表/CSV；不能将后追加配置称为新的独立认证。</p>'+sources(True)+'<h3>全部557点的99%门槛统计</h3><p>'+e('；'.join(f'{names[k]} {v}点' for k,v in counts.items()))+'。以上包含全词表端点及可能dense回退，不能直接当作有效稀疏方案数量。</p>')
        d['source_html']+='<p>本轮证据：'+ ' · '.join([link(R/'PLAN.json','冻结557清单与执行范围'),link(R/'QUALITY.json','全部新组质量/真实K'),link(R/'benchmark/PLAN.json','同轮8输入测速条件'),link(R/'INDEPENDENT_REVIEW.json','完整复核'),link(R/f'cohorts/{cohort}/SUMMARY.csv','当前组557点CSV'),link(M/'reports/sparse_methods_20261024_r1/benchmark/RESULT.json','保留的历史557速度'),'<a href="V4Validation_first6_20261024.html#gpu-summary">首轮6点页面存档</a>'])+'</p>'
        d['source_html']+='<p>GPU速度条件：RTX5060 Laptop / PyTorch2.13.0+cu130，FP32固定算术Eager；每输入3次预热＋30计时。每次完整重算路由/预览/稳定排序/候选并集/gather/精算/policy和token/score/CRC主机返回，缓存只用于未计时的质量分析。排除加载、H2D、Transformer、prefill和TTFT；包含4456组完整CPU/GPU候选/raw位证明，所有133680次输出核对通过。</p>'
        datasets['old' if cohort=='old' else 'fresh']=d
        path=R/f'cohorts/{cohort}/SUMMARY_DATA.json';path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        buf=io.StringIO();w=csv.writer(buf);w.writerow(['id','mode','recall_percent','misses','decode_steps','minimum_category_percent','gate99','fallback_decode','full_vocabulary_observed','gpu_m14_per_s','K_mean','quality_source','timing_source'])
        for p in points:w.writerow([p['id'],p['mode'],p['quality']['recall']*100,p['quality']['misses'],p['quality']['steps'],min(c['recall']*100 for c in p['quality']['by_category'].values()),p.get('gate99','calibration_only'),p.get('fallback_decode',0),p['full_vocabulary_observed'],p['rate'],p['k']['mean'],p['quality_source'],p['raw']])
        (R/f'cohorts/{cohort}/SUMMARY.csv').write_text('\ufeff'+buf.getvalue(),encoding='utf-8')
    datasets.update(default='fresh',paired_old=datasets['old'],comparison_ids=sixids,all557=True)
    payload=json.dumps(datasets,ensure_ascii=False,allow_nan=False).replace('<',r'\u003c')
    tabs='<div class="gpu-dataset-tabs" role="tablist" aria-label="评估数据集"><button type="button" id="gpu-cohort-old" role="tab" aria-selected="false">原校准集 · 320题 / 557配置</button><button type="button" id="gpu-cohort-fresh" role="tab" aria-selected="true">新1000题 · 557配置补充分析</button></div><p id="gpu-cohort-description" class="gpu-caption"></p><p id="gpu-cohort-notice" class="notice"></p>'
    panel=panel.replace('<div class="gpu-controls">',tabs+'<div class="gpu-controls">',1)
    panel=panel.replace('<option value="99">99%–100%</option>','<option value="99">99%–100%</option><option value="98.5">98.5%–100%</option>',1)
    panel=panel.replace('<button type="button" id="gpu-reset">','<label><input type="checkbox" id="gpu-common-only">仅显示首轮6配置</label><button type="button" id="gpu-reset">',1)
    panel=panel.replace('召回率 × GPU decode 效率：全部配置总览','召回率 × GPU lm_head 效率：557配置配对对比',1)
    panel=panel.replace('<p class="gpu-caption">','<p class="gpu-caption" id="gpu-legacy-caption">',1).replace('<p class="notice">','<p class="notice" id="gpu-legacy-notice">',1)
    panel=panel.replace('<details><summary>数据来源、计算方法与测试条件</summary>','<details id="gpu-legacy-methods"><summary>历史557轮完整测速条件与证据</summary>',1)
    panel=panel.replace('<details><summary>完整数据表','<details open id="gpu-cohort-source-box"><summary>当前数据集：来源链接、划分与本轮测试条件</summary><div id="gpu-cohort-sources"></div></details><details><summary>完整数据表',1)
    panel=panel.replace('<th>校准召回</th>','<th>当前组召回</th>')
    panel=panel.replace('横轴默认截断为99%–100%，纵轴从0开始。','新组默认98.5%–100%，可切换到0%–100%查看所有点；两组共用横纵轴范围，切换保留筛选和选中配置。纵轴从0开始。',1)
    panel=panel.replace('</style>',' .gpu-dataset-tabs{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}.gpu-dataset-tabs [aria-selected="true"]{background:#235f52;color:white;border-color:#235f52}#gpu-cohort-source-box{margin:14px 0}#gpu-cohort-sources code{overflow-wrap:anywhere;font-size:11px}</style>',1)
    panel=panel.replace('<script id="gpu-summary-data"',f'<script id="gpu-cohort-datasets" type="application/json">{payload}</script><script id="gpu-summary-data"',1)
    return panel
