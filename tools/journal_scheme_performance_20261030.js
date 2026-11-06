(()=>{'use strict';
const $=id=>document.getElementById(id),d=JSON.parse($('dev-log-data').textContent).performance,c=d.scheme_comparison;
if(!c)return;const esc=x=>String(x??'').replace(/[&<>"']/g,a=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[a]));
const num=x=>x==null?'未测':Number(x).toLocaleString('zh-CN',{maximumFractionDigits:3});
const safe=x=>typeof x==='string'&&!/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(x)?esc(x):null;
let evaluation=c.default_evaluation,chosen=c.schemes.find(s=>s.variant_ids.aggregate===d.default_variant)?.id||c.schemes[0].id;
const legacy=d.variants.filter(v=>!v.scheme_id),select=$('perf-variant');
select.innerHTML='<optgroup label="实板稀疏化方案">'+c.schemes.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')+'</optgroup><optgroup label="历史完整词表与离线版本（计时口径另列）">'+legacy.map(v=>`<option value="${esc(v.id)}">${esc(v.label)}</option>`).join('')+'</optgroup>';select.value=chosen;
$('perf-title').textContent='真实方案与M14性能对比';$('perf-candidate').textContent=d.candidate_note;
function render(){
 const scheme=c.schemes.find(s=>s.id===chosen),v=scheme?d.variants.find(v=>v.id===scheme.variant_ids[evaluation]):d.variants.find(v=>v.id===chosen);
 const isAggregate=!!scheme&&evaluation==='aggregate',rate=v.values?.decode;
 $('perf-current').textContent=[v.label,v.scope,v.measured_at].filter(Boolean).join(' · ');
 const specification=(v.specification||[]).map(s=>`<div class="perf-spec-row"><dt>${esc(s.label)}</dt><dd>${s.priority?'<b>':''}${esc(s.value)}${s.priority?'</b>':''}</dd></div>`).join('');
 const additional=scheme?`${isAggregate?'平均耗时':'30次Median'}：<b>${num(v.values[isAggregate?'mean_ms':'a53_median'])} ms</b>；${isAggregate?'120次合并P95':'P95'}：<b>${num(v.values.a53_p95)} ms</b>；整网TTFT：未测`:'历史IP计数口径；与本轮A53完整调用另列。整网TTFT：未测';
 $('perf-cards').classList.remove('perf-single');
 $('perf-cards').innerHTML=`<article class="perf-card primary"><div class="scheme-name">${esc(scheme?.name||v.label)}</div>${scheme?`<div class="scheme-method"><b>稀疏化方法</b>${esc(scheme.explanation)}</div>`:''}<div class="perf-label">M14等效输出率 · ${esc(scheme?c.evaluations[evaluation]:'历史测量')}</div><div class="perf-value"><strong>${num(rate)}</strong>${rate==null?'':'<span>次/s</span>'}</div><small>${esc(isAggregate?'四类各30次，共120次原始调用；120 / 总调用秒数。':'单输入30次测量的Median换算：1000 / Median_ms。历史版本沿用其原始计时边界。')}</small><div class="perf-meta"><dl class="perf-specs">${specification}</dl><p>${esc(v.conditions)}</p></div><div class="perf-resources">${additional}</div></article><section class="perf-chart"><div class="perf-chart-heading"><h3>不同方案的M14等效输出率</h3></div><div class="scheme-chart-toolbar"><label for="perf-evaluation">评价输入 <select id="perf-evaluation">${Object.entries(c.evaluations).map(([k,label])=>`<option value="${k}">${esc(label)}</option>`).join('')}</select></label></div><p class="scheme-scope">同一板卡、200MHz配置、PL DDR、相同A53完整调用边界。横坐标为真实方案；颜色区分方案。</p><div class="scheme-plot" id="scheme-comparison-plot"></div><div id="scheme-comparison-table"></div><p class="scheme-chart-note">${esc(c.formula)}<br>综合覆盖四个冻结校准输入，不代表全语料或整网decode。历史完整词表的IP计时不混入本图。${safe(c.source)?` <a href="${safe(c.source)}">综合计算与原始计时来源</a>`:''}</p></section>`;
 $('perf-meta').textContent='';$('perf-meta').hidden=true;
 const field=$('perf-evaluation');field.value=evaluation;field.addEventListener('change',()=>{evaluation=field.value;render();});
 $('perf-method').textContent=d.method;$('perf-proof').innerHTML=(d.evidence||[]).filter(e=>safe(e.href)).map(e=>`<a href="${safe(e.href)}">${esc(e.label)}</a>`).join(' · ');
 $('perf-comparison-head').innerHTML='<tr><th>真实方案 / 输入</th><th>M14输出率 / 次/s</th><th>平均耗时 / ms</th><th>Median / ms</th><th>P95 / ms</th><th>测量范围</th></tr>';
 $('perf-comparison-body').innerHTML=d.variants.map(v=>`<tr><th>${esc(v.label)}</th><td>${num(v.values.decode)}</td><td>${num(v.values.mean_ms)}</td><td>${num(v.values.a53_median??v.values.ip_median)}</td><td>${num(v.values.a53_p95??v.values.ip_p95)}</td><td>${esc(v.scope)}</td></tr>`).join('');
 draw();
}
function draw(){
 const items=c.schemes.map((s,i)=>({s,v:d.variants.find(v=>v.id===s.variant_ids[evaluation]),color:['#367d6b','#c2773c'][i]}));
 const W=720,H=300,left=58,right=22,top=35,bottom=65,max=Math.max(1,...items.map(x=>x.v.values.decode))*1.18;
 const y=value=>H-bottom-value/max*(H-bottom-top);let svg=`<svg viewBox="0 0 ${W} ${H}" role="group" aria-label="不同稀疏化方案的${esc(c.evaluations[evaluation])}输出率比较"><text x="8" y="18">次/s</text>`;
 for(let i=0;i<=4;i++){const v=max*i/4;svg+=`<line x1="${left}" x2="${W-right}" y1="${y(v)}" y2="${y(v)}" stroke="#dde7e1"/><text x="${left-8}" y="${y(v)+5}" text-anchor="end">${num(v)}</text>`;}
 items.forEach(({s,v,color},i)=>{const x=left+(i+.5)*(W-left-right)/2,rate=v.values.decode;svg+=`<rect class="bar" data-scheme="${s.id}" x="${x-66}" y="${y(rate)}" width="132" height="${H-bottom-y(rate)}" rx="5" fill="${color}" role="button" tabindex="0" aria-label="${esc(s.name)}，${num(rate)}次每秒，选择方案"><title>${esc(s.name)} · ${num(rate)}次/s</title></rect><text x="${x}" y="${y(rate)-12}" text-anchor="middle" font-weight="700">${num(rate)}</text><text x="${x}" y="${H-bottom+23}" text-anchor="middle">L2聚类${s.short.split('中心')[0]}中心</text><text x="${x}" y="${H-bottom+46}" text-anchor="middle">rank${s.short.split('rank')[1]}低秩＋BF16精算</text>`;});
 $('scheme-comparison-plot').innerHTML=svg+'</svg>';
 const before=items[0].v.values.decode,after=items[1].v.values.decode;
 $('scheme-comparison-table').innerHTML=`<div class="table-wrap"><table class="scheme-chart-table"><thead><tr><th>方法</th><th>${esc(c.evaluations[evaluation])} / 次/s</th><th>相对128中心＋rank128</th></tr></thead><tbody>${items.map(({s,v},i)=>`<tr class="${s.id===chosen?'scheme-selected':''}"><th>${esc(s.name)}</th><td>${num(v.values.decode)}</td><td>${i?`+${num((after/before-1)*100)}%`:'对照'}</td></tr>`).join('')}</tbody></table></div>`;
 for(const bar of $('scheme-comparison-plot').querySelectorAll('[data-scheme]')){const choose=()=>{chosen=bar.dataset.scheme;select.value=chosen;render();};bar.addEventListener('click',choose);bar.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});}
}
select.addEventListener('change',()=>{chosen=select.value;render();});window.addEventListener('resize',draw);render();
})();
