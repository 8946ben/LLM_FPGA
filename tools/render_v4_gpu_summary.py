"""Build an embedded, offline GPU scatter census above the experiment reports."""
from pathlib import Path
import csv, hashlib, html, io, json, math
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/gpu_summary_20261024_r1'
BASE_R=R;RESEARCH=M/'reports/sparse_methods_20261024_r1'
COLORS=dict(cluster='#18705a',lowrank='#3768ad',hybrid='#b85f2a',dense='#28352e')
NAMES=dict(cluster='仅聚类',lowrank='仅低秩',hybrid='聚类＋低秩融合',dense='完整词表 dense')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def esc(x):return html.escape(str(x),quote=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build_data():
    result=read(R/'RESULT.json');review=read(R/'INDEPENDENT_REVIEW.json');plan=read(R/'PLAN.json')
    assert review['result_sha256']==sha(R/'RESULT.json') and review['configurations']==len(result['configurations'])
    fixed=read(M/'reports/fixed_quality_20261022/RESULT.json');fresh=read(M/'reports/fusion_exp10_20261023_r1/FINAL_QUALITY.json')
    old=read(M/'reports/fusion_exp10_20261023_r1/SELECTION_LOCK.json')['chosen']
    points=[];calibrations={}
    costs={r['id']:r for r in read(RESEARCH/'ANALYSIS.json')['rows']} if R!=BASE_R else {}
    for row in result['configurations']:
        p=dict(id=row['id'],config=row['config'],mode=row['mode'],parameters=row['parameters'],experiments=row['experiments'],quality=row['quality']['decode'],k=row['candidate_decode'],rate=row['equivalent_m14_per_s'],mean_ms=row['wall_mean_ms'],median_ms=row['wall_median_ms'],p95_ms=row['wall_p95_ms'],cases=row['cases'],calls=row['calls'],raw=(R/row['raw']).relative_to(ROOT).as_posix(),quality_source=row['calibration_source'],independent=[])
        if row['id'] in costs:p['cost']=costs[row['id']]
        if row['mode']!='dense':
            src=row['calibration_source']
            if src not in calibrations:calibrations[src]={r['id']:r for r in read(ROOT/src)['configurations']}
            origin=calibrations[src][row['config']]
            p['fallback_decode']=origin.get('fallback_decode',origin.get('dense_fallback_decode_calls',0))
            p['estimated_arena_bytes']=origin.get('estimated_arena_bytes')
            p['factor_logical_bytes']=origin.get('factor_logical_bytes')
        if row['mode']=='cluster' and row['parameters']==dict(C=128,R=4,L=16384):p['independent'].append(dict(cohort='实验1独立1000题 / 14958 decode',quality=fixed['route']['decode']))
        if row['mode']=='lowrank' and row['parameters']==dict(r=128,T=16384):p['independent'].append(dict(cohort='实验1独立1000题 / 14958 decode',quality=fixed['lowrank']['decode']))
        if row['mode']=='hybrid' and row['parameters']==dict(C=128,R=4,L=16384,r=128,T=16384):
            p['independent'].append(dict(cohort='实验1独立1000题 / 14958 decode',quality=fixed['hybrid']['decode']))
            p['independent'].append(dict(cohort='实验10新1000题 / 14986 decode',quality=fresh['frozen_baseline']['report']['decode']))
        if row['mode']=='hybrid' and row['config']==old:p['independent'].append(dict(cohort='实验10新1000题 / 14986 decode（原99.9%门槛失败）',quality=fresh['selected']['report']['decode']))
        points.append(p)
    return dict(completed=result['completed'],points=points,colors=COLORS,names=NAMES,device=plan['device'],torch=plan['torch'],plan_sha256=sha(R/'PLAN.json'),result_sha256=sha(R/'RESULT.json'),review_sha256=sha(R/'INDEPENDENT_REVIEW.json'),measurements=result['measurements'],new_research=R!=BASE_R,default_selected='partial_dynamic_d64_T4096' if R!=BASE_R else 'cluster_C256_R4_L16384',quality_scope='原320校准问题 / 4775 decode；不是独立最终质量认证',timing_scope='原校准集4固定hidden/history夹具：中文、英文、代码、数学；每配置每类3预热＋30测量，同轮随机交错；全部BF16权重和参数常驻GPU，FP32固定算术PyTorch Eager全M14调用',old_selected='hybrid_'+old)

def static_svg(data):
    pts=[p for p in data['points'] if p['quality']['recall']>=.99];ymax=math.ceil(max(p['rate'] for p in pts)/25)*25
    x=lambda r:85+(r-99)/1*865;y=lambda v:450-v/ymax*385
    parts=['<svg id="gpu-overview-svg" viewBox="0 0 1040 525" role="img" aria-label="全部配置召回率与GPU lm_head等效输出率散点图">']
    for i in range(6):
        xx=99+i/5;yy=ymax*i/5
        parts.append(f'<line x1="85" x2="950" y1="{y(yy)}" y2="{y(yy)}" stroke="#dde5de"/><text x="74" y="{y(yy)+5}" text-anchor="end">{yy:.0f}</text><text x="{x(xx)}" y="475" text-anchor="middle">{xx:.1f}%</text>')
    for p in pts:
        r=p['quality']['recall']*100;label=f'{NAMES[p["mode"]]} {p["config"]}；校准召回{r:.5f}%；GPU {p["rate"]:.2f}次/s'
        parts.append(f'<circle cx="{x(r):.3f}" cy="{y(p["rate"]):.3f}" r="4" fill="{COLORS[p["mode"]]}" opacity=".65"><title>{esc(label)}</title></circle>')
    parts.append('<text x="515" y="515" text-anchor="middle">decode 赢家召回率 / %（越右越好）</text><text transform="translate(22 257) rotate(-90)" text-anchor="middle">GPU lm_head 等效输出率 / 次·s⁻¹（越高越好）</text></svg>')
    return ''.join(parts)

def table_rows(points):
    return ''.join(f'<tr><td>{esc(NAMES[p["mode"]])}</td><th><button type="button" data-gpu-point="{esc(p["id"])}">{esc(p["config"])}</button></th><td>{" / ".join(map(str,p["experiments"]))}</td><td>{p["quality"]["recall"]*100:.5f}%</td><td>{p["quality"]["misses"]} / {p["quality"]["steps"]}</td><td>{p["rate"]:.2f}</td><td>{p["mean_ms"]:.4f}</td><td>{p["k"]["mean"]:.2f}</td></tr>' for p in sorted(points,key=lambda p:-p['rate']))

def render():
    global R
    if (RESEARCH/'benchmark/INDEPENDENT_REVIEW.json').is_file() and (RESEARCH/'ANALYSIS.json').is_file() and (RESEARCH/'STAGE_PROFILE.json').is_file() and (RESEARCH/'SELECTOR_REVIEW.json').is_file() and (RESEARCH/'RESULT.json').is_file() and (ROOT/'doc/design/V4SparseMethods.html').is_file():
        R=RESEARCH/'benchmark'
        COLORS.update(partial='#8647ac',affinity='#00849a',learned='#a64670',lsh='#7f7827')
        NAMES.update(partial='部分通道预筛',affinity='全词表倒排桶',learned='学习式桶路由',lsh='多表哈希检索')
    if not (R/'RESULT.json').is_file() or not (R/'INDEPENDENT_REVIEW.json').is_file():return ''
    d=build_data();points=d['points']
    # CSV is an exported scientific table, not a second fact source.
    csvfile=io.StringIO(newline='');writer=csv.writer(csvfile);writer.writerow(['id','mode','experiments','C','R','L','rank','TopT','calibration_decode_steps','misses','recall_percent','gpu_equivalent_m14_per_s','mean_ms','median_ms','p95_ms','K_mean','K_p95','calls','raw_observations'])
    for p in points:
        a=p['parameters'];q=p['quality'];writer.writerow([p['id'],p['mode'],'/'.join(map(str,p['experiments'])),*[a.get(k,'') for k in ['C','R','L','r','T']],q['steps'],q['misses'],q['recall']*100,p['rate'],p['mean_ms'],p['median_ms'],p['p95_ms'],p['k']['mean'],p['k']['p95'],p['calls'],p['raw']])
    (R/'SUMMARY.csv').write_text('\ufeff'+csvfile.getvalue(),encoding='utf-8')
    js=(ROOT/'tools/v4_gpu_summary.js').read_text(encoding='utf-8')
    panel='''<style>
    #gpu-summary{scroll-margin-top:15px}#gpu-summary .gpu-caption{max-width:1000px}#gpu-summary .gpu-layout{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:16px;align-items:start}#gpu-summary .gpu-chart{min-width:0;background:#fbfdf9;border:1px solid var(--line);border-radius:12px;padding:8px}#gpu-summary svg{display:block;width:100%;height:auto;font:13px "Microsoft YaHei",sans-serif}#gpu-summary .gpu-inspector{background:#f0f5ef;border:1px solid var(--line);border-radius:10px;padding:15px;font-size:13px;min-width:0}#gpu-summary .gpu-inspector h3{overflow-wrap:anywhere}#gpu-summary .gpu-inspector strong.gpu-number{font-size:24px;display:block;color:var(--accent)}#gpu-summary .gpu-controls{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0;align-items:center}#gpu-summary .gpu-controls label{display:flex;gap:6px;align-items:center;font-size:13px}#gpu-summary .gpu-controls input[type=search]{width:220px}#gpu-summary .gpu-controls input[type=number]{width:86px}#gpu-summary .gpu-legend{display:flex;gap:15px;flex-wrap:wrap;font-size:13px;margin:9px 0}#gpu-summary .gpu-key{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:5px}#gpu-summary .gpu-dot{cursor:pointer}#gpu-summary .gpu-dot:focus{outline:none;stroke:#0b1e13;stroke-width:3}#gpu-summary #gpu-overview-table button{font-size:12px;padding:2px 5px;text-align:left;overflow-wrap:anywhere}#gpu-summary #gpu-overview-table{max-height:470px;overflow:auto}#gpu-summary .gpu-scroll{min-width:620px}#gpu-summary .gpu-detail-kv{display:grid;grid-template-columns:75px 1fr;gap:5px;margin:12px 0}#gpu-summary .gpu-detail-kv b{font-weight:500;color:var(--muted)}#gpu-summary .gpu-inspector code{font-size:12px}#gpu-summary .gpu-links{display:flex;gap:12px;flex-wrap:wrap;font-size:13px}@media(max-width:950px){#gpu-summary .gpu-layout{grid-template-columns:1fr}#gpu-summary .gpu-inspector{min-height:0}}@media(max-width:620px){#gpu-summary .gpu-chart{overflow:auto}#gpu-summary svg{min-width:650px}#gpu-summary .gpu-controls{gap:8px}}
    </style><section class="panel" id="gpu-summary"><div class="eyebrow">EXPERIMENTS 1 / 8 / 9 / 10 · SAME-RUN GPU CENSUS</div><h2>召回率 × GPU decode 效率：全部配置总览</h2>
    <p class="gpu-caption">489 个去重配置：23 个仅聚类、33 个仅低秩（含12个联合点）、432 个融合配置、1 个 dense 对照。实验1的原始三方案已标为大点，并与实验8/9/10的相同配置合并。横轴越右、纵轴越高越好。</p>
    <p class="notice">纵轴为 <b>GPU lm_head（M14）等效输出率</b>，包含筛选和候选精算；不是整个 LLM 的 decode token/s。横轴统一使用<b>同一校准集</b>的赢家召回率；独立1000题结果在点的详情单列，不能将它们与校准召回混作同一质量认证。</p>
    <div class="gpu-controls"><label>方案<select id="gpu-mode"><option value="all">全部方案</option><option value="cluster">仅聚类</option><option value="lowrank">仅低秩</option><option value="hybrid">融合</option><option value="dense">dense</option></select></label><label>实验<select id="gpu-experiment"><option value="all">1 / 8 / 9 / 10 全部</option><option value="1">实验1：原始方案</option><option value="8">实验8：聚类超参</option><option value="9">实验9：低秩超参</option><option value="10">实验10：融合超参</option></select></label><label>召回轴<select id="gpu-range"><option value="99">99%–100%</option><option value="99.9">99.9%–100%</option><option value="95">95%–100%</option><option value="0">0%–100% 全部</option></select></label><label>质量类别<select id="gpu-category"><option value="all">全部 decode</option><option value="chinese">中文</option><option value="english">英文</option><option value="code">代码</option><option value="math">数学</option></select></label><label>配置<input id="gpu-search" type="search" placeholder="如 C256_R4_L16384、r64"></label><label><input type="checkbox" id="gpu-frontier" checked>显示观察边界</label><button type="button" id="gpu-reset">重置</button></div>
    <div class="gpu-legend">__LEGEND__<span>大点：实验1原始方案；空心环：实验10原锁定点</span></div><p class="statusline" id="gpu-overview-status">默认放大99%–100%；切换到全范围可查看全部489点。</p>
    <div class="gpu-layout"><div class="gpu-chart">__SVG__<p class="table-note">横轴默认截断为99%–100%，纵轴从0开始。悬停或点击点查看配置；键盘可聚焦数据点。同坐标不作抖动，重叠点可通过下方表格定位。虚线仅连接当前显示点中的非支配观察边界，未作新选型。</p></div><aside class="gpu-inspector" id="gpu-inspector" aria-live="polite"><h3>点击点查看完整结果</h3><p>包括 C / R / L / rank / Top-T、漏选次数、真实候选K、四输入耗时与历史独立质量。</p></aside></div>
    <details><summary>完整数据表（可筛选、点击配置查看详情）</summary><div class="table-scroll" id="gpu-overview-table"><table><thead><tr><th>方案</th><th>配置</th><th>实验</th><th>校准召回</th><th>漏选/步数</th><th>GPU 次/s</th><th>均值 ms</th><th>K均值</th></tr></thead><tbody id="gpu-overview-rows">__ROWS__</tbody></table></div></details>
    <details><summary>数据来源、计算方法与测试条件</summary><p>质量复用实验8/9/10已保存的原320校准题，共5095预测，其中4775个decode步；中文1200、英文1175、代码1200、数学1200。候选包含dense赢家即记命中，召回率=(decode步数−漏选次数)/decode步数。训练、问题来源与划分见下方各实验报告；本汇总没有新采集最终标签或调整超参数。dense的100%为定义对照。</p><p>速度是 __DEVICE__ / PyTorch __TORCH__ 的本轮统一补测：4个原校准固定hidden/history（中文、英文、代码、数学），每配置每类3次预热＋30次测量，共58680次；每轮随机交错全部配置，并另插入570次dense哨兵。常驻canonical BF16 W与参数，固定FP32乘加/归约，预览分块32768行，包含路由/低秩、稳定排序、候选并集、权重gather、精算、penalty及主机接收token/score/CRC；排除首次加载、H2D、CPU参考、Transformer、prefill、TTFT。CPU/GPU完整候选ID与raw位、输出共1956组逐位核验通过。</p><p>纵轴 = 120 ÷（该配置120次完整调用耗时之和/1000），单位次/s。点详情中的median/P95来自这4个固定输入的重复测量，不是全语料延迟分位。质量类别筛选同时使用对应类别的30次计时，保证同一图的纵轴含义一致。独立1000题与4固定测速输入不是同一统计总体；GPU参考速度不外推FPGA速度。所有配置采用同一新轮次，原报告中的历史速度保留。</p><p>同轮原始耗时、全部覆盖数组及SHA、数值证明已独立复核；本轮仅形成描述性总览，不改变实验10原99.9%质量失败结论、不发布新锁点。</p><p class="table-note">完成：__COMPLETED__（Asia/Shanghai）。页面内嵌全部绘图数据，无联网、fetch或板卡操作。<br>RESULT SHA256：__RESULT_SHA__</p><div class="gpu-links">__LINKS__</div></details>
    </section><script id="gpu-summary-data" type="application/json">__DATA__</script><script>__JS__</script>'''
    if R!=BASE_R:
        panel=panel.replace('489','557').replace('58680','66840').replace('570','660').replace('1956','2228')
        panel=panel.replace('EXPERIMENTS 1 / 8 / 9 / 10 · SAME-RUN GPU CENSUS','EXPERIMENTS 1 / 8 / 9 / 10 + NEW 11–14 · SAME-RUN GPU CENSUS')
        panel=panel.replace('557 个去重配置：23 个仅聚类、33 个仅低秩（含12个联合点）、432 个融合配置、1 个 dense 对照。','557 个去重配置：原489点与新增68点全部同轮重测。新增16部分通道、18全词表倒排桶、18学习式桶路由、16多表哈希配置。')
        panel=panel.replace('<option value="dense">dense</option></select>','<option value="dense">dense</option><option value="partial">部分通道预筛</option><option value="affinity">全词表倒排桶</option><option value="learned">学习式桶路由</option><option value="lsh">多表哈希检索</option></select>')
        panel=panel.replace('<option value="all">1 / 8 / 9 / 10 全部</option>','<option value="all">全部既有与新增研究</option>')
        panel=panel.replace('<option value="10">实验10：融合超参</option></select>','<option value="10">实验10：融合超参</option><option value="11">研究11：部分通道</option><option value="12">研究12：全词表倒排桶</option><option value="13">研究13：学习式桶路由</option><option value="14">研究14：多表哈希</option></select>')
        panel=panel.replace('质量复用实验8/9/10已保存的原320校准题','质量使用同一原320校准题；旧方案复用冻结数组，新68点在相同输入上重新评价')
        panel=panel.replace('原报告中的历史速度保留。','原报告中的历史速度保留。新增4类研究的原理、参数、分阶段耗时、逐点计算量和FPGA适配性见独立研究报告。')
        panel=panel.replace('<details><summary>完整数据表','<p><a href="V4SparseMethods.html">阅读新增4类方案：原理、GPU结果、计算量与FPGA适配性 →</a></p><details><summary>完整数据表',1)
    legend=''.join(f'<span><i class="gpu-key" style="background:{COLORS[k]}"></i>{NAMES[k]}</span>' for k in COLORS)
    links=''.join(f'<a href="../../{(R/file).relative_to(ROOT).as_posix()}">{esc(label)}</a>' for file,label in [('SUMMARY.csv',f'下载{len(points)}点CSV'),('PLAN.json','冻结补测方案'),('RESULT.json','本轮完整结果'),('GPU_NUMERIC_PROOF.json',f'{len(points)*4}组数值证明'),('INDEPENDENT_REVIEW.json','独立复核及dense哨兵')])
    values=dict(LEGEND=legend,SVG=static_svg(d),ROWS=table_rows(points),DEVICE=esc(d['device']),TORCH=esc(d['torch']),COMPLETED=esc(d['completed']),RESULT_SHA=d['result_sha256'],LINKS=links,DATA=json.dumps(d,ensure_ascii=False,allow_nan=False).replace('<',r'\u003c'),JS=js)
    for k,v in values.items():panel=panel.replace('__'+k+'__',v)
    (R/'SUMMARY_DATA.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from render_v4_quality_cohorts import attach
    panel=attach(panel,d)
    return panel
