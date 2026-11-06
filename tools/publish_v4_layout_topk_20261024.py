"""Publish finite stage-B evidence; no experiment execution, GPU or EDA."""
from pathlib import Path
import hashlib,json,math,statistics,html
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/layout_topk_20261024_r1';A=M/'reports/sparse_quality_all557_20261024_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def mi(x):return x/2**20

def main():
    review=read(R/'INDEPENDENT_REVIEW.json');assert review['state'].startswith('PASS')
    plan=read(R/'PLAN.json');access=read(R/'ACCESS_MODEL.json')['records'];profiles=read(R/'PL_DDR_LAYOUTS.json')
    quality={c:{p['id']:p for p in read(A/f'cohorts/{c}/SUMMARY_DATA.json')['points']} for c in ['old','new']}
    summaries=[]
    for cohort in ['old','new']:
        for key in plan['configurations'][:2]:
            d,t=(64,4096) if 'd64_' in key else (128,1024)
            for tile in [128,1024]:
                rows=[x for x in access if x['id']==key and x['case'].startswith(cohort+'_') and x.get('tile_tokens')==tile]
                assert len(rows)==4
                dual=statistics.mean(x['preview']['payload_bytes']+x['dual_exact']['payload_bytes'] for x in rows)
                shared=statistics.mean(x['preview']['payload_bytes']+x['shared_exact']['payload_bytes'] for x in rows)
                terms=statistics.mean(151936*d+x['k']*896+896 for x in rows)
                # Capacity counts only, not synthesis mapping; FP32 tree slots,
                # two BF16 channel vectors, hidden/RMS/dims, histogram/bitmap/IDs.
                buffers=(d.bit_length()*tile*4)+(2*tile*2)+(896*8)+(128*4)+(256*4)+18992+(t+14)*4
                # Radix baseline keeps one32bit key per word in DDR: write once,
                # four histogram scans and one emit scan. Optional debug raw and
                # all control/history/candidate writes remain separate.
                radix_key_bytes=6*151936*4
                summaries.append(dict(cohort=cohort,id=key,tile=tile,fixture_count=4,
                    dual_weight_payload_bytes=dual,shared_weight_payload_bytes=shared,
                    shared_exact_amplification_min=min(x['shared_exact']['read_amplification'] for x in rows),
                    shared_exact_amplification_max=max(x['shared_exact']['read_amplification'] for x in rows),
                    preview_bursts_per_fixture=rows[0]['preview']['bursts'],
                    dual_exact_bursts_mean=statistics.mean(x['dual_exact']['bursts'] for x in rows),
                    shared_exact_bursts_mean=statistics.mean(x['shared_exact']['bursts'] for x in rows),
                    multiplication_terms_mean=terms,adjacent_preview_additions=151936*(d-1),
                    radix_key_read_write_bytes=radix_key_bytes,
                    dual_weight_plus_key_io_floor_cycles=math.ceil((dual+radix_key_bytes)/16),
                    ideal8mul_per_cycle_term_floor=math.ceil(terms/8),
                    onchip_capacity_model_bytes=buffers,ideal_bram18_capacity=math.ceil(buffers/2304),
                    cost_scope='Four fixed inputs only; proposed128bit payload schedule, no measured AXI or FPGA cycles'))
    write(R/'COST_SUMMARY.json',dict(state='OFFLINE_MODELS_NOT_MEASUREMENTS',rows=summaries,
        bus='128bit at nominal200MHz:16B/clock,3.2GB/s ideal aggregate at existing MIG128bit port; two masters do not double this port.',
        cycle_floor='Payload/16 and terms/8 are independent ideal lower bounds. Do not add overlapping stages blindly; no startup/policy/AR arbitration/DDR efficiency/actual FP II included.',
        bram='18K=2304B capacity division only; port replication, banking, alignment and control can increase actual HLS usage. No DSP estimate without floating-point IP configuration.'))
    payload=dict(access=access,profiles=profiles,summaries=summaries,
        quality={c:{key:{'recall':quality[c][key]['quality']['recall'],'minimum':min(x['recall'] for x in quality[c][key]['quality']['by_category'].values()),'rate':quality[c][key]['rate']} for key in plan['configurations']} for c in ['old','new']},
        top_cpu=read(R/'TOP_T_PROOF.json')['records'],streamed=review['streamed_preview'])
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>lm_head v4 · 布局与 Top-T 可行性评审</title>
<style>body{font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif;color:#233e3b;background:#f3f5f0;margin:0}main{max-width:1200px;margin:auto;padding:28px}section{background:white;border:1px solid #d7e1d9;border-radius:16px;padding:26px;margin:22px 0}h1,h2,h3{line-height:1.4}a{color:#287767}small,.muted{color:#60756f}.note{background:#fff4d8;border-left:5px solid #947034;padding:14px}.ok{background:#e9f3ec;padding:14px}label{display:inline-block;margin:8px 20px 8px 0}select{padding:9px;border-radius:6px;border:1px solid #c3d3cb;font:inherit}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid #d8e1dc;padding:10px;text-align:left}th{background:#f0f5f1}code{overflow-wrap:anywhere}.scroll{overflow:auto}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.card{background:#edf5ef;padding:16px;border-radius:12px}.card strong{display:block;font-size:27px}.flow{display:flex;flex-wrap:wrap;gap:10px}.flow span{background:#edf4f0;padding:14px;border-radius:8px}.barrow{display:grid;grid-template-columns:150px 1fr 110px;align-items:center;gap:10px;margin:12px 0}.track{background:#eef1ec;height:30px}.bar{background:#4d8570;height:100%}.bar.shared{background:#b47e4e}.bar.control{background:#7c8caa}summary{cursor:pointer;font-weight:bold}@media(max-width:720px){main{padding:12px}section{padding:16px}.cards{grid-template-columns:1fr}.barrow{grid-template-columns:100px 1fr 80px;font-size:13px}}</style>
<main><a href="V4Validation.html#gpu-summary">← GPU 汇总图</a><h1>lm_head v4：存储布局与稳定 Top-T 可行性评审</h1><p>2026-10-24 · 第一阶段完成：离线数值核对与访问模型。固定 d64/Top4096 为主候选，d128/Top1024 为质量余量备选，原聚类 C128/R4/L16384 为对照。</p>
<p class="note">本页给出软件证明和工程成本模型；没有运行新的 GPU 测速、HLS、RTL、200 MHz 实现或板卡测试。MiB/步为拟定访问调度的数据拍载荷，不能当作实测 DDR 流量或 decode 速度。</p>
<section><h2>当前结论</h2><p><b>建议先以“双份权重＋1024词分块预览＋稳定 radix 阈值选择”进入最小硬件原型评估。</b>双份布局的拟定 arena 为528.75 MiB；共享单份布局为269.00 MiB，但其候选精算读取放大更大。两者都处于现有2 GiB PL DDR映射窗口内；新布局尚未绑定descriptor、loader或ELF，不能直接上板。</p><p>128词分块作为对照保留。1024词分块使 d64 预览请求从每次75968个降至9536个，末块额外读取80 KiB，预览流式归约栈为28 KiB。该选择依据访存请求和缓冲模型，实际 II、资源及收益待 HLS 核验。</p><p>radix 与流式堆都已逐项正确；选择 radix 作为首个原型是因为它用顺序扫描和256个计数器完成阈值定位。CPU NumPy radix 耗时较低不能证明硬件更快；堆方案保留作有限备选。</p></section>
<section id="interactive"><h2>按输入检查布局代价</h2><p>原4＋新4固定输入，均与557配置同轮测速采用的8输入相同。这里不是对全部1000题做DDR访问统计。</p>
<label>候选方案 <select id="config"><option value="partial_dynamic_d64_T4096">主候选：d64 / Top4096</option><option value="partial_dynamic_d128_T1024">备选：d128 / Top1024</option></select></label>
<label>输入 <select id="case">__CASES__</select></label><label>分块词数 <select id="tile"><option>1024</option><option>128</option></select></label>
<div class="cards"><div class="card">实际候选 K<strong id="k"></strong><small>Top-T 并入14特殊ID后的去重集合</small></div><div class="card">共享布局精算读取放大<strong id="amp"></strong><small>128位拍按8个相邻词合并一次读取</small></div><div class="card">同组最低类别召回<strong id="quality"></strong><small>已有557质量报告，非本轮重新认证</small></div></div>
<h3>权重读取拍载荷 / MiB</h3><p class="muted">两种布局都包含预览和精算；聚类对照包含中心权重、有效列表及候选精算。控制和中间数组访问未混入权重条形图。</p><div id="bars"></div><div class="scroll"><table><thead><tr><th>路径</th><th>预览请求</th><th>精算请求</th><th>权重载荷</th></tr></thead><tbody id="access"></tbody></table></div>
<p id="key-cost"></p><p id="cpu-top"></p><p class="note">分块只改变物理存放。通道仍按 abs(hidden)×RMS 的稳定降序参与 FP32 相邻树；候选精算仍使用原 H8/interleave16 算术。不能为了地址连续而改变加法顺序。</p></section>
<section><h2>每一步怎样执行</h2><div class="flow"><span>①896通道打分<br>稳定选d通道</span><span>→②按分块/通道读取<br>FP32流式相邻树预览</span><span>→③history penalty<br>写每词32位排序键</span><span>→④4轮radix直方图<br>定位第T名分数阈值</span><span>→⑤全局ID顺序扫描<br>处理平局、并入特殊ID</span><span>→⑥canonical BF16精算<br>policy / token / score / CRC</span></div>
<p>预览每产生一个通道的乘积向量，就按二进制进位合并相邻子树。d64 用7层、d128用8层槽位，和一次性保存全部d个乘积的树逐位一致；1024词分块下栈分别28/32 KiB。</p><p>radix 每轮扫描全部151936个排序键，按高字节到低字节共4轮；再扫描1轮发出全部高于阈值的ID，并按较小ID优先补齐阈值平局。候选最后按全局ID顺序发出，硬件无需把Top-T再按分数完整排序。Python证明保留分数序列，是为了核对稳定排名。</p><p>排序键将正负零视为同分，原score bits保留；非有限分数或非法T显式拒绝。输出candidate bitmap每次清空，重复ID采用保留旧位的OR写入；bank冲突和写后读转发仍须在后续RTL验证。</p></section>
<section><h2>拟定 PL DDR 区域表</h2><p>沿用源文件确认的高地址窗口0x400000000–0x47FFFFFFF。该表是新实验的离线分区提案，未修改旧320 MiB运行配置。</p><label>布局 <select id="layout"><option value="dual">双份权重</option><option value="shared">共享单份权重</option></select></label><p id="arena"></p><details><summary>展开当前布局的全部区域（含guard）</summary><div class="scroll"><table><thead><tr><th>区域</th><th>系统地址</th><th>字节数</th></tr></thead><tbody id="regions"></tbody></table></div></details></section>
<section><h2>证明范围与尚未完成的项目</h2><ul><li>两份完整分块权重逐字逆变换SHA等于canonical BF16，padding为零。</li><li>24组方案/输入与既有完整候选、raw bits、token/score/CRC证明一致；32组布局预览与精算逐位一致；额外32组流式归约预览逐位一致。</li><li>16组真实Top-T，以及16组平局/零/极值/边界测试，两种选择器都与稳定全排序相同；非法T与NaN/Inf拒绝。</li><li>独立脚本复核全部地址表、40条访问模型和保存数组；不是第三方审核。</li><li>逻辑乘法项数、BRAM容量除法和理想数据拍周期仅用于排除明显不可行方案；没有新的实测FPGA速度、II、BRAM/DSP利用率或TTFT。</li></ul><p>下一阶段先做一个主配置的Csim/HLS最小原型，核验浮点流水、访存突发和Top-T开销；通过后再完整RTL/200MHz系统。质量门槛仍为整体及各类≥99%，逐位数值正确性不放宽。不对已打开新1000题调参再认证。</p></section>
<section><h2>原始证据与来源</h2><p>质量和GPU速度来自<a href="V4Validation.html#gpu-summary">新旧557点汇总及语料来源链接</a>；本轮只读取其中8个固定状态，没有采集新题或重拟合。</p><ul>__LINKS__</ul><p>页面可离线file://打开，无远程脚本或依赖。浏览器视觉检查尚未运行；静态、链接与交互逻辑检查另列。</p></section></main>
<script id="layout-data" type="application/json">__DATA__</script><script>
const DATA=JSON.parse(document.getElementById('layout-data').textContent);
function buildView(id,caseName,tile,layout){const row=DATA.access.find(x=>x.id===id&&x.case===caseName&&x.tile_tokens===tile),control=DATA.access.find(x=>x.id==='cluster_C128_R4_L16384'&&x.case===caseName);const cohort=caseName.startsWith('old_')?'old':'new',q=DATA.quality[cohort][id];const values=[row.preview.payload_bytes+row.dual_exact.payload_bytes,row.preview.payload_bytes+row.shared_exact.payload_bytes,control.cluster_exact.payload_bytes+control.router_weight_bytes+control.list_id_bytes];return {row,control,q,values,profile:DATA.profiles[layout+'_B'+tile],top:DATA.top_cpu.find(x=>x.tag===caseName+(id.includes('d64_')?'_d64_T4096':'_d128_T1024'))};}
const el=id=>document.getElementById(id),fmt=n=>n.toLocaleString('zh-CN'),mib=n=>(n/1048576).toFixed(3);
function update(){const id=el('config').value,caseName=el('case').value,tile=Number(el('tile').value),v=buildView(id,caseName,tile,el('layout').value);el('k').textContent=fmt(v.row.k);el('amp').textContent=v.row.shared_exact.read_amplification.toFixed(2)+' 倍';el('quality').textContent=(v.q.minimum*100).toFixed(4)+'%';const max=Math.max(...v.values);el('bars').innerHTML=v.values.map((n,i)=>'<div class="barrow"><span>'+['双份权重','共享单份权重','原聚类对照'][i]+'</span><div class="track"><div class="bar '+['','shared','control'][i]+'" style="width:'+(100*n/max)+'%"></div></div><b>'+mib(n)+' MiB</b></div>').join('');el('access').innerHTML=[['双份权重',v.row.preview.bursts,v.row.dual_exact.bursts,v.values[0]],['共享单份',v.row.preview.bursts,v.row.shared_exact.bursts,v.values[1]],['聚类对照','另见来源',v.control.cluster_exact.bursts,v.values[2]]].map(a=>'<tr>'+a.map((x,i)=>'<td>'+(i===3?mib(x)+' MiB':typeof x==='number'?fmt(x):x)+'</td>').join('')+'</tr>').join('');el('key-cost').textContent='radix另计排序键DDR：写1次＋直方图读4次＋发出ID读1次，共 '+mib(6*151936*4)+' MiB；不含可选debug分数、控制和其他写回。';el('cpu-top').textContent='本输入CPU功能模型耗时：heap '+(v.top.methods.heap.cpu_elapsed_s*1000).toFixed(2)+' ms，radix '+(v.top.methods.radix.cpu_elapsed_s*1000).toFixed(2)+' ms。单次Python/NumPy观察，不能用于硬件速度排名。';el('arena').textContent='arena '+mib(v.profile.arena_bytes)+' MiB；窗口剩余 '+mib(v.profile.remaining_aperture_bytes)+' MiB。区域包含loader工作区、debug、radix键、精算暂存和guard。';el('regions').innerHTML=v.profile.regions.map(r=>'<tr><td>'+r.name+'</td><td><code>'+r.address+'</code></td><td>'+fmt(r.bytes)+'</td></tr>').join('');}
['config','case','tile','layout'].forEach(id=>el(id).addEventListener('change',update));update();
</script></html>'''
    cases=sorted({x['case'] for x in access});labels={'old':'原校准','new':'新题','chinese':'中文','english':'英文','code':'代码','math':'数学'}
    page=page.replace('__CASES__',''.join(f'<option value="{c}">{labels[c.split("_")[0]]} · {labels[c.split("_")[1]]}</option>' for c in cases))
    links=[(R/'PLAN.json','本轮冻结入口/源SHA'),(R/'LAYOUT_PROOF.json','完整布局逆变换证明'),(R/'PL_DDR_LAYOUTS.json','全部拟定DDR地址表'),(R/'NUMERIC_PROOF.json','完整数值证明'),(R/'TOP_T_PROOF.json','Top-T证明与CPU观察'),(R/'BOUNDARY_TESTS.json','边界/非法输入/突发拆分测试'),(R/'ACCESS_MODEL.json','8输入逐项访问模型'),(R/'COST_SUMMARY.json','容量、运算项和周期下界模型'),(R/'INDEPENDENT_REVIEW.json','独立脚本复核及流式预览证明'),(M/'experiments/board_v4_20261021/create_bd.tcl','已有系统地址/数据位宽源文件'),(ROOT/'module_14_lm_head_v3_1/standalone/src/pl_ddr_layout.h','已上板v3.1窗口说明')]
    page=page.replace('__LINKS__',''.join(f'<li><a href="../../{p.relative_to(ROOT).as_posix()}">{html.escape(label)}</a></li>' for p,label in links)).replace('__DATA__',json.dumps(payload,ensure_ascii=False,allow_nan=False).replace('<',r'\u003c'))
    path=ROOT/'doc/design/V4LayoutTopK.html';path.write_text(page,encoding='utf-8')
    md='''# v4 布局与稳定Top-T评审 · 2026-10-24

第一阶段离线研究完成；没有新的GPU、HLS、RTL、200MHz实现或板卡操作。

## 工程决策

主候选固定动态d64/Top4096，备选d128/Top1024，原C128/R4/L16384为对照。建议下一步以双份权重、B1024分块、流式相邻树、radix阈值选择做最小Csim/HLS原型。不是锁定发布，也未继承旧硬件资格。

- 两份权重本体519.31MiB，B1024 padding后520.41MiB；完整拟定arena528.75MiB，位于已有2GiB高地址窗口。共享B1024 arena269.00MiB，但本轮8输入精算128位读取放大4.73–7.16倍，且AR请求更多。旧320MiB运行profile不能直接使用双份布局。
- B128/B1024均完整逆变换canonical SHA通过。d64预览AR请求75968→9536；B1024额外80KiB/调用；其流式相邻树栈28KiB（d128为32KiB），完整预览逐位一致。只改变存储与调度，不改动态通道顺序。
- heap和radix均与稳定排序的完整Top-T一致。radix以4轮全量32位键扫描定位阈值，最后1轮按全局ID处理平局并生成候选；+0/-0同分，原score bits不改。NaN/Inf与非法T拒绝。CPU计时仅功能模型观察，不能判断硬件速度。
- 推荐radix作为第一实现是基于固定顺序扫描、256计数器和有限状态；堆的每次替换存在log2(T)比较/更新依赖，保留为备选。最终硬件选择须看HLS真实II、浮点IP、AR行为和资源，不能依据Python耗时确定。

## 本轮8固定输入的访问模型

原校准4输入和新题4输入与最新557轮相同；以下为每组4输入平均，不是全1000题平均。权重载荷包括预览/精算，尚不含控制、中间键和debug流量；radix键另计写1+读5=3.478MiB。

|输入组|配置|分块|双份权重MiB|共享权重MiB|共享精算AR均值|
|---|---|---:|---:|---:|---:|
'''
    for row in summaries:
        md+=f'|{row["cohort"]}|{row["id"]}|{row["tile"]}|{mi(row["dual_weight_payload_bytes"]):.3f}|{mi(row["shared_weight_payload_bytes"]):.3f}|{row["shared_exact_bursts_mean"]:,.0f}|\n'
    md+='''
## 模型边界

已有v4是64位地址/128位数据，MIG端128位、拟定200MHz；16B/拍、3.2GB/s只是理想接口上限，两master共享一个MIG口不能直接翻倍。地址模型将连续候选/8词组相邻请求合并，限制256拍且不跨4KiB；共享布局不假设跨调用缓存或预览到精算复用。实际HLS必须实现该合并调度，逐候选随机读会更差。DDR命令、refresh、控制器内部取数、仲裁和效率均未测。不能把本表称为实际AXI流量。

乘法项/8与载荷字节/16只是分别假设8路乘法吞吐与满拍时的数据下界；不是latency、II或FPGA加速比。BRAM只按2304B/BRAM18K计算理想容量，银行/端口复制及浮点IP由HLS决定，不估造DSP数。硬件可行性为PASS_TO_MINIMAL_PROTOTYPE，非实现通过。

## 验证与下一阶段

24个方案/输入完整候选、raw bits、token/score/CRC匹配既有557证明；32个布局预览/精算证明；额外32个流式预览逐位证明。16组真实Top-T及16组边界用例通过，非法参数/非有限分数拒绝；全地址表与40条访问模型独立脚本复核通过。

下一步只开发d64/Top4096一个主配置的最小内核，依次检查动态通道、预览、radix/候选合并和canonical精算的Csim/HLS。首次原型若II或资源不合格，保留失败，在有限工程替代间修正；不自动扩参数/重跑质量。新IP身份、DDR profile、loader、descriptor、BSP/ELF仍待新工程开发。

所有当前质量组已打开；保持现参数/算术的布局优化可做逐位回归，不重新声称独立质量认证。若更改参数/近似算术，则另锁点并使用新的未打开最终组。当前仍无板卡授权，不连接/探测/操作FPGA，不恢复wb/luyou/心跳，不改冻结/封存包或实验10失败结论。

交互报告：[V4LayoutTopK.html](../../../doc/design/V4LayoutTopK.html)。原始数据见同目录PLAN、LAYOUT_PROOF、PL_DDR_LAYOUTS、NUMERIC_PROOF、TOP_T_PROOF、ACCESS_MODEL、COST_SUMMARY、INDEPENDENT_REVIEW。
'''
    (R/'RESULT.md').write_text(md,encoding='utf-8')
    result=read(R/'RESULT.json');result.update(state='STAGE_B_COMPLETE_PASS_TO_MINIMAL_PROTOTYPE',
        recommendation=dict(primary='partial_dynamic_d64_T4096',backup='partial_dynamic_d128_T1024',layout='dual_B1024',top='radix_threshold_first_heap_backup',
            arena_bytes=profiles['dual_B1024']['arena_bytes'],not_a_release=True),
        evidence_sha256={name:sha(R/name) for name in ['PLAN.json','LAYOUT_PROOF.json','PL_DDR_LAYOUTS.json','NUMERIC_PROOF.json','TOP_T_PROOF.json','BOUNDARY_TESTS.json','ACCESS_MODEL.json','COST_SUMMARY.json','INDEPENDENT_REVIEW.json','RESULT.md']},
        page_sha256=sha(path),stage_C='NOT_RUN_NEXT_FINITE_TASK',visual_QA='NOT_RUN')
    write(R/'RESULT.json',result)
    print(json.dumps(dict(state=result['state'],page=str(path),arena_mib=mi(profiles['dual_B1024']['arena_bytes']))))

if __name__=='__main__':main()
