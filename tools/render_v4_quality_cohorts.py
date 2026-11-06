"""Attach two offline data tabs; preserve historical 557-point fact source."""
from pathlib import Path
import collections,csv,hashlib,html,io,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';Q=M/'reports/sparse_quality_20261024_r1';D=M/'data/sparse_quality_20261024'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def e(v):return html.escape(str(v),quote=True)
def local(p,label):return f'<a href="../../{p.relative_to(ROOT).as_posix()}">{e(label)}</a>'
def sources(fresh):
    lock=read(M/'data/public_corpus_v1/sources.lock.json');revs=lock['revisions']
    rows=[('中文','CMMLU','400题' if fresh else '80题','https://github.com/haonan-li/CMMLU',revs['cmmlu'],'官方 test 中未用问题' if fresh else '原问题组哈希划分的 calibration'),('英文','Dolly-15k','250题' if fresh else '80题','https://github.com/databrickslabs/dolly',revs['dolly'],'未用 instruction＋可选 context' if fresh else 'instruction＋可选 context；原 calibration'),('代码','DS-1000' if fresh else 'MBPP','100题' if fresh else '80题','https://github.com/xlang-ai/DS-1000' if fresh else 'https://github.com/google-research/google-research/tree/master/mbpp','b39aab71da6d23ef8d3cac59a7c5f834516ab334' if fresh else revs['mbpp'],'按原题 family 排除历史与扰动变体；只给 prompt，不执行代码' if fresh else '只给任务文本；原 calibration，不执行测试代码'),('数学','GSM8K','250题' if fresh else '80题','https://github.com/openai/grade-school-math',revs['gsm8k'],'官方 train/test 中本项目未用问题；不提供答案' if fresh else '原问题组划分 calibration；不提供答案')]
    out='<div class="table-scroll"><table><thead><tr><th>类别</th><th>数据来源（官方链接）</th><th>问题数</th><th>冻结版本</th><th>本项目使用方式</th></tr></thead><tbody>'
    for cat,name,n,url,rev,note in rows:out+=f'<tr><td>{cat}</td><td><a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a></td><td>{n}</td><td><code>{rev}</code></td><td>{note}</td></tr>'
    out+='</tbody></table></div>'
    if fresh:
        manifest=read(D/'MANIFEST.json')
        quality=read(Q/'QUALITY.json')
        out+='<h3>冻结配置的独立质量结果 · 整体与每类均≥99%才通过</h3><div class="table-scroll"><table><thead><tr><th>配置</th><th>decode漏选</th><th>整体召回</th><th>最低类别</th><th>99%判定</th></tr></thead><tbody>'
        for row in quality['configurations']:
            q=row['report']['decode'];minimum=min(v['recall'] for v in q['by_category'].values())
            out+=f'<tr><th>{e(row["id"])}</th><td>{q["misses"]}/{q["steps"]}</td><td>{q["recall"]*100:.5f}%</td><td>{minimum*100:.5f}%</td><td>{"通过" if row["gate99"]=="PASS" else "未通过"}</td></tr>'
        out+='</tbody></table></div>'
        out+='<p>新1000题在配置/入口锁定后才采集标签；完整问题分组，排除9份历史训练、校准、快照及评估文件（含v4b最终组）。NFKC/casefold/空白归一化精确去重；代码按DS-1000 origin family分组，并做trigram Jaccard≥0.5排除。语义重复及模型预训练污染仍未知。</p>'
        out+='<p>中文/英文/数学沿用官方来源的新问题；代码从旧MBPP改为DS-1000，因此新旧差异同时包含问题抽样与代码分布变化。不能将两组召回差直接解释为同分布退化。</p>'
        prompts=[json.loads(s) for s in (D/'holdout.jsonl').read_text(encoding='utf-8').splitlines()]
        libraries=collections.Counter(p['library'] for p in prompts if p['category']=='code')
        math_splits=collections.Counter(p['source_id'].split(':')[0] for p in prompts if p['category']=='math')
        out+='<p>本轮实际代码库组成：'+e('、'.join(f'{k} {v}题' for k,v in sorted(libraries.items())))+'；数学官方split组成：'+e('、'.join(f'{k} {v}题' for k,v in sorted(math_splits.items())))+'。官方train表示上游数据集split，本项目已排除实际训练分组。</p>'
        out+='<p>先声明的6点分别按整体及每类decode召回≥99%判定。候选精算仍用canonical BF16权重和固定FP32算术；这是固定dense轨迹下的一致性，不是闭环生成或任务正确率。</p>'
        out+=f'<p>语料SHA256：<code>{manifest["corpus_sha256"]}</code></p><p>'+ ' · '.join([local(D/'MANIFEST.json','新组来源/划分与历史排除清单'),local(D/'holdout.jsonl','1000题prompt清单'),local(D/'EVALUATION_ENTRY_LOCK.json','标签前冻结入口'),local(M/'data/public_corpus_v1/sources.lock.json','原始公开源URL/许可/SHA'),local(ROOT/'module_14_lm_head_v4b/data/final_quality_20261023/raw/ds1000/SOURCE_LOCK.json','DS-1000下载URL/许可/SHA'),local(Q/'SELECTION_LOCK.json','6点配置及99%门槛'),local(Q/'INDEPENDENT_REVIEW.json','独立复核'),local(Q/'benchmark/RESULT.json','新输入GPU实测'),local(Q/'SUMMARY.csv','下载新6点CSV')])+'</p>'
    else:
        out+='<p>原320题：每类80题。训练1500题和calibration320按完整问题组划分，使用NFKC/casefold/空白归一化、SHA确定性采样；并非按相邻token切分。原分组仅做精确去重，语义重复与预训练污染未知。这批calibration用于调参，不能作为独立最终认证。</p>'
        out+='<p>原320题共5095预测/4775 decode：中文1200、英文1175、代码1200、数学1200。横轴=(decode步数−漏选次数)/decode步数。纵轴为原4固定输入、每类30次完整M14 Eager调用；120000/耗时毫秒总和，并非4775步逐步测速。</p>'
        out+='<p>'+ ' · '.join([local(M/'data/public_corpus_v1/sources.lock.json','原始公开数据URL/版本/许可/SHA'),local(M/'data/public_corpus_v1/MANIFEST.json','原分组与样本量'),local(M/'data/public_corpus_v1/calibration.jsonl','原320题prompt清单'),local(M/'reports/sparse_methods_20261024_r1/benchmark/PLAN.json','原557点测速条件')])+'</p>'
    out+='<p>模型为本地冻结Qwen2.5-0.5B-Instruct，使用相同system/user聊天模板；最多生成16个预测，首预测单列，其后才计decode；history包含输入及已生成ID，penalty=1.1。新旧组均不将公开数据集答案作为dense标签。</p>'
    return out

def attach(panel,old):
    full=M/'reports/sparse_quality_all557_20261024_r1'
    if (full/'INDEPENDENT_REVIEW.json').exists() and (full/'benchmark/RESULT.json').exists():
        from render_v4_all557_cohorts import attach as full_attach
        return full_attach(panel,old)
    if not (Q/'INDEPENDENT_REVIEW.json').exists() or not (Q/'benchmark/RESULT.json').exists():return panel
    review=read(Q/'INDEPENDENT_REVIEW.json');assert review['state'].startswith('PASS')
    result=read(Q/'benchmark/RESULT.json');quality=read(Q/'QUALITY.json');assert review['quality_sha256']==sha(Q/'QUALITY.json') and review['benchmark_sha256']==sha(Q/'benchmark/RESULT.json')
    fresh=dict(old);points=[]
    oldmap={p['id']:p for p in old['points']}
    for row in result['configurations']:
        p=dict(oldmap[row['id']]);p.update(quality=row['report']['decode'],k=row['candidate_decode'],rate=row['equivalent_m14_per_s'],mean_ms=row['wall_mean_ms'],median_ms=row['wall_median_ms'],p95_ms=row['wall_p95_ms'],cases=row['cases'],calls=row['calls'],raw=row['raw'],quality_source='module_14_lm_head_v4/reports/sparse_quality_20261024_r1/QUALITY.json',independent=[],fallback_decode=0,gate99=row['gate99'])
        # Old logical costs were averaged on calibration and cannot describe new K.
        p.pop('cost',None);points.append(p)
    fresh.update(points=points,completed=result['completed'],quality_label='新独立',quality_scope=f'新1000问题 / {quality["decode"]} decode；冻结6配置独立验证',timing_scope='新组4个预声明固定decode输入，每类3预热＋30实测；完整重算M14，非1000题总体测速',default_selected='partial_dynamic_d64_T4096',default_min=98.5,old_selected='',result_sha256=sha(Q/'QUALITY.json'),measurements=720)
    fresh['caption']=f'新独立1000题：中文400/英文250/代码100/数学250；{quality["predictions"]}预测 / {quality["decode"]} decode，零排除。仅验证标签前冻结的4候选＋2对照，共6点；未测的其他551点不补画。'
    fresh['source_html']=sources(True)
    timing_plan=read(Q/'benchmark/PLAN.json')
    fresh['source_html']+=f'<p>GPU测速条件：{e(timing_plan["device"])} / PyTorch {e(timing_plan["torch"])}，固定FP32算术Eager实现。每类按预声明规则取首个至少有2预测的问题之第1个decode输入；每配置每类3预热＋30计时，共720测量，另30 dense哨兵。完整重算筛选、排序、合并、gather、精算、penalty及主机输出；权重/参数常驻，排除初始加载、H2D、Transformer、prefill和TTFT。输出率=120000/120次耗时毫秒总和；median/P95仅为四输入重复计时。</p>'
    fresh['notice']='横轴是新1000题召回率，纵轴是新组4固定输入的GPU M14输出率，门槛为整体及每类≥99%。旧输入在本轮也明显变快，说明跨轮绝对速度不可直接归因于数据/算法；对比共同6配置请勾选下方选项，旧集将使用本轮对照测速。不是整网decode或FPGA速度。'
    old=dict(old,quality_label='校准',caption='原320校准题、557个配置：用于参数探索；保留此前同轮GPU实测。勾选共同6配置可改用本轮原输入重测速度，再与新集切换对比。',source_html=sources(False),notice='当前557点使用历史同轮测速。新旧轮次绝对速度存在明显差异，不能将纵轴变化直接归因为新数据或算法；勾选共同6配置可使用本轮六点对照。横轴为调参用校准召回，非独立认证。')
    fresh['k_note']=f'K均值/P95来自新组全部{quality["decode"]}个decode步；耗时来自新组4固定输入。'
    old['k_note']='K均值/P95来自原组全部4775个decode步；耗时来自原4固定输入。'
    for p in points:p['cohort']='new_independent_20261024'
    control=read(Q/'benchmark_calibration_control/RESULT.json')
    assert read(Q/'TIMING_COMPARABILITY_REVIEW.json')['control_sha256']==sha(Q/'benchmark_calibration_control/RESULT.json')
    paired=dict(old);paired_points=[]
    for row in control['configurations']:
        p=dict(oldmap[row['id']]);p.update(rate=row['equivalent_m14_per_s'],mean_ms=row['wall_mean_ms'],median_ms=row['wall_median_ms'],p95_ms=row['wall_p95_ms'],cases=row['cases'],calls=row['calls'],raw=row['raw']);paired_points.append(p)
    paired.update(points=paired_points,caption='原320校准召回 × 本轮共同6配置重测速度：输入hidden/history与原557轮完全相同，但采用与新组相同的六配置运行方式。',notice='已启用配对速度对照：旧集取本轮原4输入计时，新集取本轮新4输入计时；两组都测相同6配置。四固定输入测速仍不代表整批语料或整网decode。',default_selected='partial_dynamic_d64_T4096',old_selected='',source_html=sources(False)+'<p>当前纵轴改用本轮6配置对照，共720测量＋30dense哨兵；原557点历史速度未改。'+local(Q/'TIMING_COMPARABILITY_REVIEW.json','跨轮可比性审计')+' · '+local(Q/'benchmark_calibration_control/PLAN.json','原输入本轮重测条件')+'</p>')
    both=dict(default='fresh',old=old,fresh=fresh,paired_old=paired)
    (Q/'SUMMARY_DATA.json').write_text(json.dumps(fresh,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    buf=io.StringIO();w=csv.writer(buf);w.writerow(['id','decode_steps','misses','recall_percent','minimum_category_percent','gate99','gpu_m14_per_s','K_mean','quality_source','timing_source'])
    for p in points:w.writerow([p['id'],p['quality']['steps'],p['quality']['misses'],p['quality']['recall']*100,min(x['recall']*100 for x in p['quality']['by_category'].values()),p['gate99'],p['rate'],p['k']['mean'],p['quality_source'],p['raw']])
    (Q/'SUMMARY.csv').write_text('\ufeff'+buf.getvalue(),encoding='utf-8')
    tabs='<div class="gpu-dataset-tabs" role="tablist" aria-label="评估数据集"><button type="button" id="gpu-cohort-old" role="tab" aria-selected="false">原校准集 · 320题 / 557配置</button><button type="button" id="gpu-cohort-fresh" role="tab" aria-selected="true">新独立集 · 1000题 / 6配置</button></div><p id="gpu-cohort-description" class="gpu-caption"></p><p id="gpu-cohort-notice" class="notice"></p>'
    panel=panel.replace('<div class="gpu-controls">',tabs+'<div class="gpu-controls">',1)
    panel=panel.replace('<option value="99">99%–100%</option>','<option value="99">99%–100%</option><option value="98.5">98.5%–100%（含本轮失败点）</option>',1)
    panel=panel.replace('横轴默认截断为99%–100%，纵轴从0开始。','横轴范围可切换；新集默认98.5%–100%以显示失败点，旧集默认99%–100%。纵轴从0开始。',1)
    panel=panel.replace('<button type="button" id="gpu-reset">','<label><input type="checkbox" id="gpu-common-only">仅显示两组共同的6配置</label><button type="button" id="gpu-reset">',1)
    sourcebox='<details open id="gpu-cohort-source-box"><summary>当前数据集：数据来源链接、划分与指标口径</summary><div id="gpu-cohort-sources"></div></details>'
    panel=panel.replace('<details><summary>完整数据表',sourcebox+'<details><summary>完整数据表',1)
    panel=panel.replace('召回率 × GPU decode 效率：全部配置总览','召回率 × GPU lm_head 效率：按数据集对比',1)
    panel=panel.replace('<p class="gpu-caption">','<p class="gpu-caption" id="gpu-legacy-caption">',1).replace('<p class="notice">','<p class="notice" id="gpu-legacy-notice">',1)
    panel=panel.replace('<details><summary>数据来源、计算方法与测试条件</summary>','<details id="gpu-legacy-methods"><summary>原557点完整测速条件与证据</summary>',1)
    panel=panel.replace('<th>校准召回</th>','<th>当前组召回</th>')
    panel=panel.replace('</style>',' .gpu-dataset-tabs{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}.gpu-dataset-tabs [aria-selected="true"]{background:#235f52;color:white;border-color:#235f52}#gpu-cohort-source-box{margin:14px 0}#gpu-cohort-sources code{overflow-wrap:anywhere;font-size:11px}</style>',1)
    payload=json.dumps(both,ensure_ascii=False,allow_nan=False).replace('<',r'\u003c')
    panel=panel.replace('<script id="gpu-summary-data"',f'<script id="gpu-cohort-datasets" type="application/json">{payload}</script><script id="gpu-summary-data"',1)
    return panel
