
'use strict';
(() => {
 const data=JSON.parse(document.getElementById('dev-log-data').textContent);
 const x=data.exploration;
 if(!x?.routes?.length){document.getElementById('schedule-panel').hidden=true;document.getElementById('exploration-nav').hidden=true;return;}
 const p=x;
 const $=id=>document.getElementById(id);
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const safeLink=v=>{const s=String(v||'').trim();return s&&!/[\u0000-\u001f\u007f]/.test(s)&&!s.startsWith('//')&&(!/^[a-z][a-z0-9+.-]*:/i.test(s)||/^(https?:|file:)/i.test(s))?esc(s):'';};
 const routes=new Map(x.routes.map(r=>[r.id,r]));
 const stages=new Map(x.stages.map(s=>[s.id,s]));
 const labels={verified:'✓ 已验证',active:'● 进行中',waiting:'⏸ 等待',planned:'○ 未开始',failed:'× 未通过',na:'— 不适用',unknown:'? 未确认'};
 const lifecycle={active:'进行中',waiting:'等待条件',planned:'待启动',paused:'保留 / 暂缓',completed:'已完成',stopped:'已结束'};
 const closed=r=>['completed','stopped'].includes(r.lifecycle);
 let selected=x.selected;
 const openArchives=new Set();
 let allRoutesExpanded=false;
 $('schedule-title').textContent=x.title||'探索路线图';
 $('schedule-updated').textContent='路线状态快照 '+(x.updated||'未记录')+' · '+(data.project.timezone||'Asia/Shanghai');
 $('schedule-summary').textContent=x.summary||'每行一条探索路线，每列一个具体的实现或验证步骤。';
 $('schedule-snapshot').textContent=x.snapshot_note;
 $('schedule-assumptions').textContent=x.explanation||'横向为验证环节，并非工时坐标；进行中表示实际执行，等待条件和未开始单独标注。';
 $('schedule-cards').innerHTML=(x.current||[]).map(c=>`<div class="schedule-card"><b>${esc(c.value)}</b><small>${esc(c.label)}</small></div>`).join('');
 if(p.badge)$('schedule-badge').textContent=p.badge;
 $('schedule-proof').innerHTML=(p.evidence||[]).filter(e=>safeLink(e.href)).map(e=>`<a href="${safeLink(e.href)}">${esc(e.label)}</a>`).join('');
 /* task-route-links */
 function taskLinks(r,heading=false){const refs=(r.task_refs||[]).filter(t=>(data.task_overview?.rows||[]).some(task=>task.id===t.id)),cls='route-task-links'+(heading?' route-task-heading':'');return refs.length?`<div class="${cls}">${heading?'':'<span>所属任务：</span>'}${refs.map(t=>`<a href="#task-${esc(t.id)}" data-task-jump="${esc(t.id)}" title="返回任务总览：${esc(t.label)}">${esc(heading?(refs.length===1?r.id:r.id+' · '+t.label):t.label)}</a>`).join('')}</div>`:heading?`<div class="${cls}">${esc(r.id)}</div>`:'';}
 function taskSummary(r){return (r.task_refs||[]).length?`<span class="route-task-summary">所属任务：${esc(r.task_refs.map(t=>t.label).join(' / '))}</span>`:'';}
 function revealLinkedRoute(id){
  const r=routes.get(id);if(!r)return false;
  hideExecution();selected=id;
  if(closed(r))openArchives.add(id);
  const filter=$('schedule-scope').value;
  const included=filter==='all'||(filter==='working'&&['active','waiting','paused'].includes(r.lifecycle))||(filter==='planned'&&r.lifecycle==='planned')||(filter==='closed'&&closed(r));
  if(!included)$('schedule-scope').value='all';
  render();detail(id,r.currentStage);
  const target=$('route-'+id);if(!target)return false;
  const archive=target.closest('details');if(archive)archive.open=true;
  document.querySelectorAll('.route-linked-target,.task-linked-target').forEach(el=>el.classList.remove('route-linked-target','task-linked-target'));
  target.classList.add('route-linked-target');
  const scroll=target.closest('.route-scroll');if(scroll)scroll.scrollLeft=0;
  target.scrollIntoView({block:'center',behavior:'auto'});target.focus({preventScroll:true});
  return true;
 }
 function revealLinkedTask(id){
  const target=$('task-'+id);if(!target)return false;
  hideExecution();
  document.querySelectorAll('.route-linked-target,.task-linked-target').forEach(el=>el.classList.remove('route-linked-target','task-linked-target'));
  target.classList.add('task-linked-target');
  const scroll=target.closest('.task-overview-scroll');if(scroll)scroll.scrollLeft=0;
  target.scrollIntoView({block:'center',behavior:'auto'});target.focus({preventScroll:true});return true;
 }
 function handleRouteTaskHash(){
  const hash=location.hash.slice(1);
  if(hash.startsWith('route-'))revealLinkedRoute(hash.slice(6));
  else if(hash.startsWith('task-'))revealLinkedTask(hash.slice(5));
 }
 document.addEventListener('click',event=>{
  const a=event.target.closest('a[data-route-jump],a[data-task-jump]');
  if(!a||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  event.preventDefault();
  const route=a.dataset.routeJump,task=a.dataset.taskJump;
  if(route?revealLinkedRoute(route):revealLinkedTask(task)){
   if(location.hash!==a.getAttribute('href'))history.pushState(null,'',a.getAttribute('href'));
  }
 });
 window.addEventListener('hashchange',handleRouteTaskHash);
 /* task-route-links:end */

 function table(rows){
  return `<table class="route-table" style="min-width:${200+x.stages.length*120}px"><caption class="sr-only">优化探索路线与验证阶段；点击阶段查看证据</caption><colgroup><col>${x.stages.map(()=>'<col>').join('')}</colgroup><thead><tr><th scope="col">探索路线 / 验证范围</th>${x.stages.map((s,i)=>`<th scope="col" data-stage-header="${esc(s.id)}"><span class="stage-number">${String(i+1).padStart(2,'0')}</span>${esc(s.title)}</th>`).join('')}</tr></thead><tbody>${rows.map(row).join('')}</tbody></table>`;
 }
 function row(r){
  return `<tr class="route-row ${r.lifecycle==='active'?'route-running':''}" id="route-${esc(r.id)}" tabindex="-1" data-route-row="${esc(r.id)}"><th scope="row">${taskLinks(r,true)}<${safeLink(r.design_page)?'a':'button'} class="route-title route-design-link" ${safeLink(r.design_page)?`href="${safeLink(r.design_page)}"`:`type="button" data-route="${esc(r.id)}"`} data-design-route="${esc(r.id)}" aria-label="${esc('查看 '+r.id+' '+r.title+' 的HTML可视化设计')}"><strong>${esc(r.title)}</strong><small class="route-caption">${esc(lifecycle[r.lifecycle])}${r.parent?' · 延续 '+esc(r.parent):''}</small><span class="route-scope">${esc(r.scope)}</span><span class="route-design-hint">${safeLink(r.design_page)?'查看设计':'查看已知方案与状态'}</span></${safeLink(r.design_page)?'a':'button'}></th>${x.stages.map(stage=>{
   const c=r.cells[stage.id],frontier=r.currentStage===stage.id;
   return `<td><button type="button" class="route-cell ${esc(c.state)} ${frontier?'frontier':''}" data-route="${esc(r.id)}" data-stage="${esc(stage.id)}" aria-controls="execution-popover" aria-haspopup="dialog" aria-expanded="false" aria-pressed="false" ${(c.execution||c.state==='active')?'data-execution="true"':''} ${c.state==='active'?'aria-current="step"':''} aria-label="${esc(r.title+'，'+stage.title+'，'+labels[c.state]+'，'+c.note)}"><b>${esc(labels[c.state])}</b><small>${esc(c.note)}</small></button></td>`;
  }).join('')}</tr>`;
 }
 function detail(id,stageId){
  const r=routes.get(id);if(!r)return;
  const s=stages.get(stageId||r.currentStage)||x.stages[x.stages.length-1],c=r.cells[s.id];
  selected=id;
  document.querySelectorAll('.route-cell').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.route===id&&b.dataset.stage===s.id)));
  return {r,s,c};
 }
 function render(){
  const filter=$('schedule-scope').value;
  if(filter!=='all')allRoutesExpanded=false;
  const rows=x.routes.filter(r=>filter==='all'||(filter==='working'&&['active','waiting','paused'].includes(r.lifecycle))||(filter==='planned'&&r.lifecycle==='planned')||(filter==='closed'&&closed(r)));
  const working=rows.filter(r=>!closed(r)),archive=rows.filter(closed),visible=allRoutesExpanded?[...working,...archive]:working;
  $('plan-gantt').innerHTML=visible.length?`<div class="route-scroll" tabindex="0" role="region" aria-label="探索路线阶段表，可左右滚动">${table(visible)}</div>`:filter==='closed'?'':'<div class="route-empty">该筛选下没有展开的路线。</div>';
  $('closed-routes').hidden=allRoutesExpanded||!archive.length;
  $('closed-routes').innerHTML=!allRoutesExpanded&&archive.length?`<h3 class="route-closed-title">已完成 / 已结束路线 · ${archive.length} 条</h3>${archive.map(r=>`<details class="route-archive ${r.lifecycle==='stopped'?'stopped':''}" data-archive="${esc(r.id)}" ${openArchives.has(r.id)?'open':''}><summary>${esc(r.title)}${taskSummary(r)}<span class="route-outcome">${esc(lifecycle[r.lifecycle])} · ${esc(r.scope)}</span><small>${esc(r.outcome)} · 展开查看每个阶段</small></summary><div class="route-scroll" tabindex="0" role="region" aria-label="${esc(r.title+'的历史阶段')}">${table([r])}</div></details>`).join('')}`:'';
  const toggle=$('route-expand-all');toggle.setAttribute('aria-expanded',String(allRoutesExpanded));toggle.textContent=allRoutesExpanded?'收缩':'展开';toggle.setAttribute('aria-label',allRoutesExpanded?'收缩已完成和已结束路线':'展开全部路线并合并到同一张表');toggle.disabled=!x.routes.some(closed);
  $('schedule-count').textContent=`显示 ${rows.length} / ${x.routes.length} 条探索路线，${x.stages.length} 个验证阶段。${allRoutesExpanded?'已结束路线已全部接在未结束路线之后。':`${archive.length} 条已结束路线在下方折叠，可点击“展开”合并查看。`}整页纵向滚动；窄屏表格可左右滑动，路线名称固定在左侧。`;
  const first=rows.find(r=>r.id===selected)||working[0]||archive[0];
  if(first)detail(first.id);else selected=null;
  $('route-current').disabled=!x.routes.some(r=>r.lifecycle==='active');
 }
 // unified-route-panel:start
 const executionTip=$('execution-popover');
 let executionAnchor=null,executionHover=null,executionFocus=null,executionClick=null,executionTimer=null,restoringPanelFocus=false,touchFocusPending=false;
 function executionCell(target){return target?.closest?.('button.route-cell[data-route][data-stage]')||null;}
 function positionExecution(){
  if(!executionAnchor||executionTip.hidden)return;
  if(!executionAnchor.isConnected){hideExecution();return;}
  const a=executionAnchor.getBoundingClientRect(),clip=executionAnchor.closest('.route-scroll')?.getBoundingClientRect();
  if(a.bottom<0||a.top>innerHeight||clip&&(a.right<clip.left||a.left>clip.right||a.bottom<clip.top||a.top>clip.bottom)){hideExecution();return;}
  const w=executionTip.offsetWidth,h=executionTip.offsetHeight,pad=12,gap=10;
  let left=Math.max(pad,Math.min(a.left,innerWidth-w-pad)),top;
  if(innerWidth<=800)top=innerHeight-h-pad;
  else if(a.right+gap+w<=innerWidth-pad){left=a.right+gap;top=a.top;}
  else if(a.left-gap-w>=pad){left=a.left-gap-w;top=a.top;}
  else top=a.top>=h+gap+pad?a.top-h-gap:a.bottom+gap;
  executionTip.style.left=left+'px';executionTip.style.top=Math.max(pad,Math.min(top,innerHeight-h-pad))+'px';
 }
 function showExecution(b,mode){
  if(executionClick&&mode==='hover')return;
  clearTimeout(executionTimer);
  const result=detail(b.dataset.route,b.dataset.stage);if(!result)return;
  const {r,s,c}=result,e=c.execution,parent=routes.get(r.parent);
  const field=(label,value)=>value?`<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`:'';
  const normalized=v=>String(v||'').trim();
  const scope=normalized(r.scope),evidence=normalized(c.detail||c.note),executionScope=normalized(e?.scope);
  const facts=[field('验证范围',scope),evidence!==scope?field('当前证据 / 状态',evidence):'',field('该阶段做什么',s.description),normalized(r.outcome)!==normalized(e?.current_task)?field('路线结论',r.outcome):'',
   field('前序路线',parent?parent.id+' · '+parent.title:'独立路线或既有基线'),field('下一步 / 启动条件',r.next)].join('');
  const runtime=e?`<section class="route-runtime"><h5>执行快照</h5><dl class="route-panel-fields">${[
   field('执行位置',[e.host,e.location].filter(Boolean).join(' / ')||'未记录'),field(normalized(r.outcome)===normalized(e.current_task)?'当前执行 / 路线结论':'当前执行',e.current_task||'未记录'),
   field('进度',e.progress||'未记录'),field('已完成',e.completed),field('运行工具',e.tool||'未记录'),
   field('CPU范围',e.cpu||'未记录'),field('内存限制',e.memory_limit||'未记录'),field('时间范围',e.elapsed||'未记录'),
   executionScope&&executionScope!==scope&&executionScope!==evidence?field('执行验证范围',executionScope):'',
   e.next&&e.next!==r.next?field('执行下一步',e.next):''
  ].join('')}</dl><p class="execution-stamp">采集时间：${esc(e.snapshot_at||'未记录')} · ${esc(data.project.timezone||'Asia/Shanghai')}<br>离线快照，不自动轮询；不据此推断当前作业仍在运行。</p></section>`:'';
  const links=[...(c.evidence||[]),...(r.evidence||[]),...(e?.source?[{label:'执行快照来源',href:e.source}]:[])];
  const unique=links.filter((v,i,a)=>safeLink(v.href)&&a.findIndex(w=>w.href===v.href)===i);
  executionAnchor=b;executionClick=mode==='click'?b:null;
  document.querySelectorAll('.route-cell[aria-expanded="true"]').forEach(el=>el.setAttribute('aria-expanded','false'));
  b.setAttribute('aria-expanded','true');
  executionTip.innerHTML=`<div class="route-panel-top"><div><div class="execution-kicker">路线与阶段详情 · ${esc(labels[c.state])}</div><h3 id="route-panel-title">${esc(r.id+' · '+r.title)}</h3><p class="route-panel-stage">${esc(s.title)} · ${esc(labels[c.state])}</p></div><button type="button" data-route-panel-close aria-label="关闭路线详情">×</button></div><div class="route-panel-body">${taskLinks(r)}${r.goal&&r.goal!==r.title?`<p class="route-panel-goal">${esc(r.goal)}</p>`:''}${runtime}<dl class="route-panel-fields">${facts}</dl>${unique.length?`<div class="route-panel-proof"><h5>证据与来源</h5>${unique.map(v=>`<a href="${safeLink(v.href)}">${esc(v.label)}</a>`).join('')}</div>`:''}</div>`;
  executionTip.hidden=false;executionTip.querySelector('.route-panel-body').scrollTop=0;positionExecution();
  if(mode==='click')executionTip.querySelector('[data-route-panel-close]').focus({preventScroll:true});
 }
 function hideExecution(restoreFocus=false){
  clearTimeout(executionTimer);const anchor=executionAnchor;
  executionTip.hidden=true;if(anchor)anchor.setAttribute('aria-expanded','false');
  executionAnchor=null;executionClick=null;executionHover=null;executionFocus=null;
  if(restoreFocus&&anchor?.isConnected){restoringPanelFocus=true;anchor.focus({preventScroll:true});restoringPanelFocus=false;}
 }
 function queueExecutionHide(){
  clearTimeout(executionTimer);executionTimer=setTimeout(()=>{
   if(!executionClick&&!executionHover&&!executionFocus&&!executionTip.matches(':hover')&&!executionTip.contains(document.activeElement))hideExecution();
  },220);
 }
 document.addEventListener('pointerover',event=>{
  if(event.pointerType==='touch')return;
  const b=executionCell(event.target);if(!b||b.contains(event.relatedTarget))return;
  executionHover=b;showExecution(b,'hover');
 });
 document.addEventListener('pointerout',event=>{
  const b=executionCell(event.target);if(!b||b.contains(event.relatedTarget))return;
  executionHover=null;if(!executionTip.contains(event.relatedTarget))queueExecutionHide();
 });
 executionTip.addEventListener('pointerenter',()=>clearTimeout(executionTimer));
 executionTip.addEventListener('pointerleave',queueExecutionHide);
 document.addEventListener('pointerdown',event=>{touchFocusPending=event.pointerType==='touch';},true);
 document.addEventListener('pointercancel',()=>{touchFocusPending=false;},true);
 document.addEventListener('focusin',event=>{
  if(restoringPanelFocus||touchFocusPending)return;
  const b=executionCell(event.target);if(b){executionFocus=b;showExecution(b,'focus');}
  else if(executionTip.contains(event.target))clearTimeout(executionTimer);
 });
 document.addEventListener('focusout',event=>{
  if(executionCell(event.target))executionFocus=null;
  if(!executionTip.contains(event.relatedTarget))queueExecutionHide();
 });
 document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&!executionTip.hidden){event.preventDefault();hideExecution(true);}
 });
 document.addEventListener('click',event=>{
  touchFocusPending=false;
  if(event.target.closest('[data-route-panel-close]')){hideExecution(true);return;}
  const b=executionCell(event.target);
  if(b){if(executionClick===b&&!executionTip.hidden)hideExecution();else showExecution(b,'click');return;}
  if(!executionTip.contains(event.target))hideExecution();
 });
 window.addEventListener('resize',positionExecution);
 document.addEventListener('scroll',positionExecution,true);
 $('schedule-scope').addEventListener('change',()=>hideExecution());
 // unified-route-panel:end

 function click(event){const b=event.target.closest('button[data-route]');if(b&&!b.matches('.route-cell')){const row=b.closest('tr'),cell=row?.querySelector('.route-cell.frontier')||row?.querySelector('.route-cell');if(cell)showExecution(cell,'click');}}
 $('plan-gantt').addEventListener('click',click);$('closed-routes').addEventListener('click',click);
 $('closed-routes').addEventListener('toggle',event=>{const e=event.target;if(!e.matches('details[data-archive]'))return;e.open?openArchives.add(e.dataset.archive):openArchives.delete(e.dataset.archive);},true);
 $('schedule-scope').addEventListener('change',render);
 $('route-expand-all').addEventListener('click',()=>{hideExecution();allRoutesExpanded=!allRoutesExpanded;if(allRoutesExpanded)$('schedule-scope').value='all';else openArchives.clear();render();});
 $('route-current').addEventListener('click',()=>{
  const r=x.routes.find(r=>r.lifecycle==='active');if(!r)return;
  if(!document.querySelector(`#plan-gantt [data-route-row="${r.id}"]`)){$('schedule-scope').value='all';render();}
  detail(r.id,r.currentStage);
  const cell=document.querySelector(`#plan-gantt button[data-route="${r.id}"][data-stage="${r.currentStage}"]`);
  if(cell){const scroll=cell.closest('.route-scroll'),label=cell.closest('tr').querySelector('th');scroll.scrollLeft=cell.parentElement.offsetLeft-label.offsetWidth-8;cell.focus({preventScroll:true});}
 });
 render();
 requestAnimationFrame(handleRouteTaskHash);
})();
