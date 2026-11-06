/* Embedded by render_v4_gpu_summary.py; no network or experiment execution. */
(() => {
  'use strict';
  const names = {all:'全部',chinese:'中文',english:'英文',code:'代码',math:'数学'};
  const escape = v => String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function metrics(point,category='all') {
    const q = category === 'all' ? point.quality : point.quality.by_category[category];
    const rate = category === 'all' ? point.rate : 1000/point.cases[category].mean_ms;
    return {recall:q.recall*100,rate,misses:q.misses,steps:q.steps};
  }
  function filterPoints(points,state) {
    return points.filter(p => (!state.common||state.commonIds.includes(p.id)) && (state.mode === 'all'||p.mode===state.mode) && (state.experiment==='all'||p.experiments.includes(Number(state.experiment))) && (!state.search||`${p.config} ${p.mode} ${JSON.stringify(p.parameters)}`.toLowerCase().includes(state.search.toLowerCase())) && metrics(p,state.category).recall+1e-10>=state.min);
  }
  function frontier(points,category='all') {
    const all=points.map(p=>({p,...metrics(p,category)}));
    return all.filter(a=>!all.some(b=>b.recall>=a.recall && b.rate>=a.rate && (b.recall>a.recall || b.rate>a.rate))).sort((a,b)=>a.recall-b.recall).map(x=>x.p);
  }
  // Pure functions are also exercised by the offline interaction test.
  if (typeof module!=='undefined' && module.exports) {module.exports={metrics,filterPoints,frontier};return;}
  const $=id=>document.getElementById(id);
  let data=JSON.parse($('gpu-summary-data').textContent);
  const cohortNode=$('gpu-cohort-datasets');
  const cohorts=cohortNode?JSON.parse(cohortNode.textContent):null;
  const commonNode=cohorts?$('gpu-common-only'):null;
  let cohortKey=cohorts?.default;
  let cohortInitialized=false;
  if(cohorts)data=cohorts[cohorts.default];
  let state={mode:'all',experiment:'all',category:'all',min:99,search:''};
  let selected=data.default_selected||'cluster_C256_R4_L16384';
  let current=[];let project=null;
  let pointMap=new Map(data.points.map(p=>[p.id,p]));
  const links=p=>`<a href="../../${escape(p.raw)}">本配置120次原始记录</a>${p.quality_source==='definition_control'?'':` · <a href="../../${escape(p.quality_source)}">校准质量来源</a>`}`;
  function inspect(id) {
    const p=pointMap.get(id);if(!p)return;selected=id;
    const m=metrics(p,state.category);
    const minimum=Math.min(...Object.values(p.quality.by_category).map(q=>q.recall*100));
    const kv = rows => `<div class="gpu-detail-kv">${rows.map(([k,v])=>`<b>${escape(k)}</b><span>${escape(v)}</span>`).join('')}</div>`;
    const independent = p.independent.length ? p.independent.map(s=>`<p><b>${escape(s.cohort)}</b><br>召回 ${(s.quality.recall*100).toFixed(5)}%；漏 ${s.quality.misses}/${s.quality.steps}。</p>`).join('') : '<p>此配置没有新独立问题质量结果，当前横轴只有校准召回。</p>';
    $('gpu-inspector').innerHTML=`<div class="eyebrow">${escape(data.names[p.mode])} · 实验 ${p.experiments.join(' / ')}</div><h3>${escape(p.config)}</h3><strong class="gpu-number">${m.rate.toFixed(2)} 次/s</strong><p>${names[state.category]} GPU lm_head 等效输出率</p>${kv([['校准召回',m.recall.toFixed(5)+'%'],['漏选',`${m.misses} / ${m.steps} decode`],['最低类别',minimum.toFixed(5)+'%'],['dense回退',String(p.fallback_decode||0)+'个校准decode步'],['参数',Object.entries(p.parameters).map(([k,v])=>`${k==='r'?'rank':k}=${v}`).join('，')||'V=151936，全词表'],['K均值 / P95',p.k.mean.toFixed(2)+' / '+p.k.p95],['计时次数',`${p.calls}（每类30次）`],['均值 / median',`${p.mean_ms.toFixed(4)} / ${p.median_ms.toFixed(4)} ms`],['固定输入P95',p.p95_ms.toFixed(4)+' ms']])}<p class="table-note">K均值/P95来自全部4,775个校准decode步；耗时摘要来自4固定输入。类别切换只改变大字速率与该类校准质量。</p><details><summary>4类校准召回与固定输入速度</summary>${Object.entries(p.cases).map(([c,x])=>`<p>${names[c]}：校准 ${(p.quality.by_category[c].recall*100).toFixed(5)}%，漏${p.quality.by_category[c].misses}/${p.quality.by_category[c].steps}；测速输入K=${x.k}，${x.mean_ms.toFixed(4)} ms，${(1000/x.mean_ms).toFixed(2)}次/s</p>`).join('')}</details><details open><summary>历史独立质量（不用于本图横轴）</summary>${independent}</details><p class="table-note">${p.estimated_arena_bytes ? `原公式arena估算 ${(p.estimated_arena_bytes/1048576).toFixed(2)}MiB；不是本配置均已硬件化。` : p.factor_logical_bytes ? `因子逻辑容量 ${(p.factor_logical_bytes/1048576).toFixed(2)}MiB；另需全量BF16权重259.66MiB及缓冲。` : `GPU结果不代表已具备匹配硬件布局。`}</p>${p.cost?`<details open><summary>计算量与FPGA布局预算</summary><p>乘法项：${(p.cost.total_multiplication_terms/1e6).toFixed(2)}M，dense的${p.cost.ratio_to_dense_multiplications.toFixed(3)}倍；主逻辑读取${(p.cost.logical_main_read_bytes/1048576).toFixed(2)}MiB。</p><p>权重＋索引最低预算${(p.cost.stored_weight_and_index_lower_bound_bytes/1048576).toFixed(2)}MiB（未含共同缓冲）。${p.cost.exceeds320MiB_before_common_buffers?"已超过旧320MiB arena，需新布局。":"尚需计入缓冲和对齐，不能据此判为布局通过。"}</p><p>${escape(p.cost.layout)}</p><p class="table-note">逻辑模型，非实际AXI或FPGA时延。<a href="V4SparseMethods.html#costs">查看公式与适配性分析</a></p></details>`:""}<p class="table-note">${links(p)}</p>`;
    if(data.fresh_quality||data.quality_label==='新独立'){
      const node=$('gpu-inspector');
      const label=data.quality_label||'新组';
      node.innerHTML=node.innerHTML.replace(/校准/g,label).replace(/此配置没有新独立问题质量结果，当前横轴只有[^。]+。/,'本轮'+label+'质量已作为横轴展示；该配置按99%整体及各类门槛：'+p.gate99+'。');
      node.innerHTML=node.innerHTML.replace('K均值/P95来自全部4,775个'+label+'decode步；耗时摘要来自4固定输入。',escape(data.k_note));
      if(p.validation_identity)node.innerHTML+='<p>'+escape(p.validation_identity)+'</p>';
      if(p.full_vocabulary_observed)node.innerHTML+='<p><b>本组候选始终为全词表；100%不代表稀疏收益。</b></p>';
    }
    const svg=$('gpu-overview-svg');svg.querySelectorAll('.gpu-selection').forEach(n=>n.remove());
    if(project&&current.some(v=>v.id===p.id)){
      const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');dot.setAttribute('cx',project.x(m.recall));dot.setAttribute('cy',project.y(m.rate));dot.setAttribute('r','10');dot.setAttribute('fill','none');dot.setAttribute('stroke','#15271c');dot.setAttribute('stroke-width','2');dot.setAttribute('pointer-events','none');dot.setAttribute('class','gpu-selection');svg.appendChild(dot);
    }
  }
  function draw() {
    current=filterPoints(data.points,state);
    const allMatching=filterPoints(data.points,{...state,min:0});
    const scalePoints=cohorts?.all557?[...filterPoints(cohorts.old.points,state),...filterPoints(cohorts.fresh.points,state)]:current;
    const max=Math.max(1,...scalePoints.map(p=>metrics(p,state.category).rate));
    const ymax=Math.ceil(max/25)*25;
    project={x:r=>85+(r-state.min)/(100-state.min)*865,y:v=>450-v/ymax*385};
    const {x,y}=project;let svg='';
    for(let i=0;i<=5;i++) {
      const r=state.min+(100-state.min)*i/5,v=ymax*i/5;
      svg+=`<line x1="85" x2="950" y1="${y(v)}" y2="${y(v)}" stroke="#dde5de"/><text x="74" y="${y(v)+5}" text-anchor="end">${v.toFixed(0)}</text><text x="${x(r)}" y="475" text-anchor="middle">${r.toFixed(state.min>=99.9?2:state.min>=95?1:0)}%</text>`;
    }
    if(state.min<99)svg+=`<line x1="${x(99)}" x2="${x(99)}" y1="65" y2="450" stroke="#aa4539" stroke-dasharray="4 4"/><text x="${x(99)+5}" y="82" fill="#aa4539">99%门槛</text>`;
    const dense=data.points.find(p=>p.mode==='dense'),dr=metrics(dense,state.category).rate;
    if(dr<=ymax) svg+=`<line x1="85" x2="950" y1="${y(dr)}" y2="${y(dr)}" stroke="#5b695e" stroke-dasharray="6 5"/><text x="88" y="${y(dr)-8}" fill="#526456">同轮dense ${dr.toFixed(2)}次/s</text>`;
    if($('gpu-frontier').checked && current.length)svg+=`<polyline points="${frontier(current,state.category).map(p=>{const m=metrics(p,state.category);return `${x(m.recall)},${y(m.rate)}`;}).join(' ')}" fill="none" stroke="#797f66" stroke-width="1.8" stroke-dasharray="4 4"/>`;
    for (const p of [...current].sort((a,b)=>Number(a.experiments.includes(1))-Number(b.experiments.includes(1)))) {
      const m=metrics(p,state.category),r=p.experiments.includes(1)?7:3.8;
      const title=`${data.names[p.mode]} ${p.config}；校准召回 ${m.recall.toFixed(5)}%；漏 ${m.misses}/${m.steps}；GPU ${m.rate.toFixed(2)}次/s；实验${p.experiments.join('/')}`;
      svg+=`<g class="gpu-dot" data-gpu-point="${escape(p.id)}" tabindex="0" role="button" aria-label="${escape(title)}"><title>${escape(title)}</title><circle cx="${x(m.recall)}" cy="${y(m.rate)}" r="${r}" fill="${data.colors[p.mode]}" fill-opacity="${p.experiments.includes(1)?.95:.65}" stroke="${p.experiments.includes(1)?'#fff':'none'}" stroke-width="1.4"/>${p.id===data.old_selected?`<circle cx="${x(m.recall)}" cy="${y(m.rate)}" r="8" fill="none" stroke="#992c26" stroke-width="2"/>`:''}</g>`;
    }
    svg+=`<text x="515" y="515" text-anchor="middle">${names[state.category]} decode 赢家召回率 / %（越右越好）</text><text transform="translate(22 257) rotate(-90)" text-anchor="middle">GPU lm_head 等效输出率 / 次·s⁻¹（越高越好）</text>`;
    if(!current.length)svg+='<text x="515" y="250" text-anchor="middle">当前筛选没有数据，请扩大召回范围或重置筛选</text>';
    $('gpu-overview-svg').innerHTML=svg;
    const counts=Object.keys(data.names).map(k=>`${data.names[k]} ${current.filter(p=>p.mode===k).length}`).join(' · ');
    $('gpu-overview-status').textContent=`显示 ${current.length} / ${data.points.length} 个配置（${counts}）；当前方案/搜索另有 ${allMatching.length-current.length} 点在召回轴范围之外。质量：${names[state.category]}${data.quality_label||'校准'}；速度：对应${state.category==='all'?'4输入均衡120':'类别30'}次实测。`;
    if(data.fresh_quality||data.quality_label==='新独立')$('gpu-overview-svg').innerHTML=$('gpu-overview-svg').innerHTML.replace(/校准召回/g,data.quality_label+'召回');
    $('gpu-overview-rows').innerHTML=[...current].sort((a,b)=>metrics(b,state.category).rate-metrics(a,state.category).rate).map(p=>{
      const m=metrics(p,state.category);return `<tr><td>${escape(data.names[p.mode])}</td><th><button type="button" data-gpu-point="${escape(p.id)}">${escape(p.config)}</button></th><td>${p.experiments.join(' / ')}</td><td>${m.recall.toFixed(5)}%</td><td>${m.misses} / ${m.steps}</td><td>${m.rate.toFixed(2)}</td><td>${(1000/m.rate).toFixed(4)}</td><td>${p.k.mean.toFixed(2)}</td></tr>`;
    }).join('');
    if(current.length){if(!current.some(p=>p.id===selected))selected=current.find(p=>p.mode!=='dense')?.id||current[0].id;inspect(selected);}
    else $('gpu-inspector').innerHTML='<h3>暂无匹配配置</h3><p>请扩大横轴范围或清除搜索。</p>';
  }
  function controls() {
    if(cohorts){
      data=cohortKey==='old'&&commonNode.checked?cohorts.paired_old:cohorts[cohortKey];
      pointMap=new Map(data.points.map(p=>[p.id,p]));
      $('gpu-cohort-description').textContent=data.caption;$('gpu-cohort-notice').textContent=data.notice;$('gpu-cohort-sources').innerHTML=data.source_html;
      $('gpu-legacy-methods').hidden=cohortKey==='fresh'||commonNode.checked;
    }
    state={mode:$('gpu-mode').value,experiment:$('gpu-experiment').value,category:$('gpu-category').value,min:Number($('gpu-range').value),search:$('gpu-search').value.trim(),common:!!commonNode?.checked,commonIds:cohorts?(cohorts.comparison_ids||cohorts.fresh.points.map(p=>p.id)):[]};draw();
  }
  ['gpu-mode','gpu-experiment','gpu-category','gpu-range','gpu-frontier'].forEach(id=>$(id).addEventListener('change',controls));
  $('gpu-search').addEventListener('input',controls);
  if(commonNode)commonNode.addEventListener('change',controls);
  function resetControls(){$('gpu-mode').value='all';$('gpu-experiment').value='all';$('gpu-category').value='all';$('gpu-range').value=String(data.default_min||99);$('gpu-search').value='';$('gpu-frontier').checked=true;selected=data.default_selected||'cluster_C256_R4_L16384';controls();}
  $('gpu-reset').addEventListener('click',resetControls);
  function activate(e){const target=e.target.closest('[data-gpu-point]');if(target)inspect(target.dataset.gpuPoint);}
  $('gpu-summary').addEventListener('click',activate);
  $('gpu-overview-svg').addEventListener('focusin',activate);
  $('gpu-overview-svg').addEventListener('mouseover',activate);
  $('gpu-overview-svg').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate(e);}});
  function switchCohort(key) {
    const previousSelected=selected;
    cohortKey=key;
    data=cohorts[key];pointMap=new Map(data.points.map(p=>[p.id,p]));selected=data.default_selected;
    $('gpu-cohort-old').setAttribute('aria-selected',String(key==='old'));
    $('gpu-cohort-fresh').setAttribute('aria-selected',String(key==='fresh'));
    $('gpu-cohort-description').textContent=data.caption;
    $('gpu-cohort-notice').textContent=data.notice;
    $('gpu-cohort-sources').innerHTML=data.source_html;
    $('gpu-legacy-caption').hidden=true;$('gpu-legacy-notice').hidden=true;
    $('gpu-legacy-methods').hidden=key==='fresh';
    if(cohorts.all557&&cohortInitialized){selected=previousSelected;controls();}else resetControls();
    cohortInitialized=true;
  }
  if(cohorts){
    $('gpu-cohort-old').addEventListener('click',()=>switchCohort('old'));
    $('gpu-cohort-fresh').addEventListener('click',()=>switchCohort('fresh'));
    switchCohort(cohorts.default);
  }else draw();
})();
