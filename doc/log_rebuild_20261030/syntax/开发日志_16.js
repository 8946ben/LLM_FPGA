
'use strict';
(() => {
 const $ = id => document.getElementById(id);
 const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const cls = {'已验证':'verified','待验证':'pending','阻塞':'blocked','进行中':'active','未确认':''};
 const badge = status => `<span class="badge ${cls[status] || ''}">${esc(status || '未确认')}</span>`;
 const link = value => {
  const v = String(value || '').trim();
  if (!v || /[\u0000-\u0020\u007f]/.test(v.replace(/ /g,''))) return '';
  if (/^[a-z][a-z0-9+.-]*:/i.test(v) && !/^(https?:|file:)/i.test(v)) return '';
  return esc(v);
 };
 let data;
 try {
  data = JSON.parse($('dev-log-data').textContent);
  if (!data.project || !Array.isArray(data.todos) || !Array.isArray(data.entries)) throw new Error('缺少 project / todos / entries');
  const ids = new Set();
  for (const e of data.entries) {
   const date = /^\d{4}-\d{2}-\d{2}$/.test(e.date) ? new Date(e.date + 'T00:00:00Z') : null;
   if (!e.importance) e.importance='过程记录';
   if (!['关键突破','重要成果','过程记录'].includes(e.importance)) throw new Error('重要程度无效');
   if (!e.id || ids.has(e.id) || !date || isNaN(date) || date.toISOString().slice(0,10) !== e.date || !e.title || !e.summary || !Object.hasOwn(cls,e.status)) throw new Error('条目 ID、日期、标题、摘要或状态无效');
   ids.add(e.id);
  }
  for (const e of data.entries) if ((e.related || []).some(id => !ids.has(id))) throw new Error('关联记录不存在');
 } catch (err) {
  $('timeline').textContent = '日志数据无法读取：' + err.message;
  $('timeline').className = 'error';
  return;
 }
 const entries = data.entries.slice().sort((a,b) => b.date.localeCompare(a.date));
 /* journal-lessons */
 let timelineScope='all';
 const isLesson=e=>e.category==='经验与教训'||(e.tags||[]).includes('经验与教训');
 $('lesson-count').textContent=String(entries.filter(isLesson).length);
 for(const button of document.querySelectorAll('[data-timeline-scope]'))button.addEventListener('click',()=>{timelineScope=button.dataset.timelineScope;render();});
 function openLessons(){
  timelineScope='lessons';selectedDate=null;calendarMonth=newestDate.slice(0,7);
  $('search').value='';$('status').value='';$('importance').value='';render();
  $('timeline-heading').scrollIntoView({block:'start',behavior:'auto'});
 }
 function renderPhaseTasks(){
  const container=$('phase'),routes=data.exploration?.routes||[];
  let current=routes.filter(r=>r.lifecycle==='active'),uncertain=false;
  if(!current.length){const selected=routes.find(r=>r.id===data.exploration?.selected);if(selected?.cells?.[selected.currentStage]?.state==='unknown'){current=[selected];uncertain=true;}}
  container.replaceChildren();
  if(!current.length){container.textContent='当前无执行中的任务';return;}
  for(const route of current){
   const refs=route.task_refs?.length?route.task_refs:[{label:route.id+' '+route.title}];
   for(const task of refs){const a=document.createElement('a');a.href='#route-'+route.id;a.dataset.routeJump=route.id;a.textContent=task.label;a.setAttribute('aria-label','定位探索路线：'+task.label);container.append(a);}
  }
  if(uncertain){const note=document.createElement('small');note.textContent='状态未确认，以最后采集快照为准';container.append(note);}
 }
 function renderJournalUpdate(){
  const value=data.project.log_updated_at,date=value?new Date(value):null,zone=data.project.timezone||'Asia/Shanghai';
  const text=date&&!Number.isNaN(date.getTime())?new Intl.DateTimeFormat('sv-SE',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(date)+'（'+(zone==='Asia/Shanghai'?'北京时间':zone)+'）':(data.project.updated||'未记录')+'（具体时刻未记录）';
  $('updated').textContent='最后更新 '+text;$('updated').title='日志内容更新时间；任务状态以各自快照的采集时间为准。';
 }
 $('results-nav').addEventListener('click',event=>{
  if(event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  event.preventDefault();timelineScope='all';selectedDate=null;calendarMonth=newestDate.slice(0,7);
  $('search').value='';$('status').value='';$('importance').value='';render();
  $('results-experience').scrollIntoView({block:'start',behavior:'auto'});
  if(location.hash!=='#results-experience')history.pushState(null,'','#results-experience');
 });
 /* journal-lessons:end */

 $('project-name').textContent = data.project.name || '开发日志';
 document.title = (data.project.name || '项目') + ' · 开发日志';
 $('project-intro').textContent = data.project.intro || '';
 renderPhaseTasks();
 renderJournalUpdate();
 $('source').textContent = data.project.source || '';
 const kindClass = e => e.importance==='关键突破'?'breakthrough':e.importance==='重要成果'?'achievement':'process';
 const kind = e => `<span class="kind ${kindClass(e)}">${esc(e.importance)}</span>`;
 $('stats').innerHTML = ['关键突破','重要成果','过程记录'].map(label=>`<div class="stat"><strong>${entries.filter(e=>e.importance===label).length}</strong><span>${label} · 日志条目</span></div>`).join('');
 $('presentation-checks').textContent = (data.presentation?.checks || '');
 $('highlights').innerHTML = entries.filter(e=>e.spotlight).sort((a,b)=>a.spotlight.order-b.spotlight.order).map(e=>{
  const s=e.spotlight;
  return `<article class="highlight ${s.order===1?'primary':''}"><div>${kind(e)}${badge(e.status)}<h3>${esc(s.title)}</h3>${s.comparison?`<div class="comparison">${esc(s.comparison)}</div>`:''}<p class="note">${esc(s.note)}</p></div><div class="metric"><div class="value">${esc(s.value)}</div><div class="metric-label">${esc(s.label)}</div></div><div class="proof"><a href="#${esc(e.id)}" data-related="${esc(e.id)}">查看记录与证据</a></div></article>`;
 }).join('');
 $('todos').innerHTML = data.todos.length ? data.todos.map(t=>`<li>${badge(t.status)}<span>${esc(t.text)}</span></li>`).join('') : '<li>无已记录的未完成事项</li>';
 const table = (headers,rows) => `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(c=>`<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
 function card(e) {
  const fields = (isLesson(e)?[['适用场景',e.context],['遇到的问题',e.problem],['原因',e.cause],['处理办法',e.solution],['已验证范围',e.verification],['使用边界',e.next]]:[['尝试',e.attempt],['问题',e.problem],['解决',e.solution],['验证',e.verification],['下一步',e.next]]).filter(([,v])=>v);
  let detail = `${e.impact?`<p class="section-label">当时记录</p><p>${esc(e.summary)}</p>`:''}<dl class="fields">${fields.map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`;
  if (e.experiments?.length) detail += `<p class="section-label">实验过程</p><ol class="experiments">${e.experiments.map(x=>`<li><b>${esc(x.action)}</b><p>观察：${esc(x.observation)}</p><p>结论：${esc(x.conclusion)}</p></li>`).join('')}</ol>`;
  if (e.hypotheses?.length) detail += '<p class="section-label">原因假设与证据</p>' + table(['假设','证据','判断'],e.hypotheses.map(h=>[h.idea,h.evidence,h.verdict]));
  if (e.metrics?.length) detail += '<p class="section-label">实测指标对照</p>' + table(['指标','之前','之后','单位','测量口径 / 来源'],e.metrics.map(m=>[m.name,m.before ?? '未测',m.after ?? '未测',m.unit,m.context]));
  if (e.evidence?.length) detail += `<p class="section-label">复现与证据</p>${e.evidence.map(x=>`<div class="evidence"><b>${link(x.href)?`<a href="${link(x.href)}">${esc(x.label)}</a>`:esc(x.label)}</b>${x.text?`<pre>${esc(x.text)}</pre>`:''}</div>`).join('')}`;
  if (e.raw) detail += `<details><summary>迁移原文</summary><pre>${esc(e.raw)}</pre></details>`;
  const chain = e.chain?.length ? `<ol class="chain" aria-label="调试链路">${e.chain.map(n=>`<li><b>${esc(n.label)}</b><p>${esc(n.text)}</p></li>`).join('')}</ol>` : '';
  const related = e.related?.length ? `<div class="related">关联记录：${e.related.map(id=>`<a href="#${esc(encodeURIComponent(id))}" data-related="${esc(id)}">${esc(id)}</a>`).join(' · ')}</div>` : '';
  if (isLesson(e)) return `<article class="panel entry lesson-entry" id="${esc(encodeURIComponent(e.id))}"><div class="entry-head"><div><span class="kind lesson">经验与教训</span><h3>${esc(e.title)}</h3></div>${badge(e.status)}</div><p class="summary">${esc(e.summary)}</p><div class="tags">${(e.tags||[]).filter(t=>t!=='经验与教训').map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div><details><summary>查看问题、做法与适用边界</summary>${detail}${related}</details></article>`;
  if (e.importance==='过程记录') return `<details class="process-entry entry" id="${esc(encodeURIComponent(e.id))}"><summary>${esc(e.title)} ${badge(e.status)}</summary><div class="entry-id">${esc(e.id)}</div><p class="summary">${esc(e.summary)}</p>${chain}${detail}${related}</details>`;
  return `<article class="panel entry ${kindClass(e)}" id="${esc(encodeURIComponent(e.id))}"><div class="entry-head"><div>${kind(e)}<h3>${esc(e.title)}</h3></div>${badge(e.status)}</div><p class="summary">${esc(e.impact || e.summary)}</p><details><summary>查看过程与验证证据</summary><div class="entry-id">${esc(e.id)}</div><div class="tags">${(e.tags || []).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>${chain}${detail}${related}</details></article>`;
 }
 // Calendar availability is based on all log dates, independent of filters.
 const dateCounts=new Map();
 entries.forEach(e=>dateCounts.set(e.date,(dateCounts.get(e.date)||0)+1));
 const newestDate=entries[0]?.date||new Intl.DateTimeFormat('sv-SE',{timeZone:(data.project.timezone || 'Asia/Shanghai')}).format(new Date());
 const todayParts=new Intl.DateTimeFormat('en',{timeZone:(data.project.timezone || 'Asia/Shanghai'),year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const todayDate=['year','month','day'].map(k=>todayParts.find(p=>p.type===k).value).join('-');
 let selectedDate=null,calendarMonth=newestDate.slice(0,7);
 function utcDate(y,m,day){const date=new Date(0);date.setUTCHours(0,0,0,0);date.setUTCFullYear(y,m-1,day);return date;}
 function renderCalendar(matching){
  const [year,month]=calendarMonth.split('-').map(Number);
  const first=utcDate(year,month,1),offset=(first.getUTCDay()+6)%7;
  const matches=new Map();matching.forEach(e=>matches.set(e.date,(matches.get(e.date)||0)+1));
  $('calendar-month').value=calendarMonth;
  $('calendar-latest').disabled=!entries.length;
  $('calendar-prev').disabled=calendarMonth==='0001-01';$('calendar-next').disabled=calendarMonth==='9999-12';
  const cells=[];
  for(let i=0;i<42;i++){
   const date=utcDate(year,month,1-offset+i),key=date.toISOString().slice(0,10);
   const total=dateCounts.get(key)||0,count=matches.get(key)||0,selected=key===selectedDate;
   const label=key+'，'+(total?`${total}条日志，${count}条符合当前筛选`:'无日志');
   cells.push(`<button type="button" class="calendar-day ${key.slice(0,7)!==calendarMonth?'other-month':''} ${key===todayDate?'today':''} ${selected?'selected':''} ${total&&!count?'no-match':''}" data-day="${esc(key)}" aria-label="${esc(label)}" title="${esc(label)}" aria-pressed="${selected}" ${key===todayDate?'aria-current="date"':''} ${total?'':'disabled'}>${date.getUTCDate()}${total?'<span class="calendar-dot" aria-hidden="true"></span>':''}</button>`);
  }
  $('calendar-grid').innerHTML=cells.join('');
  const monthDays=[...dateCounts].filter(([day])=>day.startsWith(calendarMonth));
  const monthTotal=monthDays.reduce((sum,[,count])=>sum+count,0);
  $('calendar-status').textContent=(selectedDate?`已选 ${selectedDate} · ${matches.get(selectedDate)||0}/${dateCounts.get(selectedDate)} 条符合筛选。`:'全部日期 · 点击有标记的日期查看。')+' '+(monthDays.length?`本月 ${monthDays.length} 天，${monthTotal} 条日志。`:'本月暂无日志。');
  $('calendar-all').setAttribute('aria-pressed',String(selectedDate===null));
 }
 function shiftCalendar(delta){
  const [year,month]=calendarMonth.split('-').map(Number),date=utcDate(year,month+delta,1);
  if(date.getUTCFullYear()<1||date.getUTCFullYear()>9999)return;
  calendarMonth=date.toISOString().slice(0,7);render();
 }
 function selectDate(day,{scroll=true,hash=true}={}){
  if(!dateCounts.has(day))return;
  selectedDate=day;calendarMonth=day.slice(0,7);render();
  if(hash)history.replaceState(null,'','#day-'+day);
  if(scroll)($('day-'+day)||$('timeline')).scrollIntoView({behavior:'smooth',block:'start'});
 }
 function removeDateHash(){if(/^#day-\d{4}-\d{2}-\d{2}$/.test(location.hash)||location.hash==='#lessons')history.replaceState(null,'',location.pathname+location.search);}
 $('calendar-prev').addEventListener('click',()=>shiftCalendar(-1));
 $('calendar-next').addEventListener('click',()=>shiftCalendar(1));
 $('calendar-month').addEventListener('change',()=>{
  const value=$('calendar-month').value;
  if(/^\d{4}-(0[1-9]|1[0-2])$/.test(value)&&Number(value.slice(0,4))>=1){calendarMonth=value;render();}
  else $('calendar-month').value=calendarMonth;
 });
 $('calendar-grid').addEventListener('click',event=>{const b=event.target.closest('button[data-day]');if(b&&!b.disabled)selectDate(b.dataset.day);});
 $('calendar-all').addEventListener('click',()=>{selectedDate=null;removeDateHash();render();});
 $('calendar-latest').addEventListener('click',()=>selectDate(newestDate));

 function render() {
  const query = $('search').value.trim().toLocaleLowerCase();
  const status = $('status').value;
  const importance = $('importance').value;
  const matching = entries.filter(e => (timelineScope!=='lessons'||isLesson(e)) && (!status || e.status===status) && (!importance || (importance==='highlights'?e.importance!=='过程记录':e.importance===importance)) && (!query || JSON.stringify(e).toLocaleLowerCase().includes(query)));
  const filtered=matching.filter(e=>!selectedDate||e.date===selectedDate);
  const days = [...new Set(filtered.map(e=>e.date))];
  $('result').textContent = `${timelineScope==='lessons'?'经验与教训 · ':''}${selectedDate?'日期 '+selectedDate:'全部日期'} · 显示 ${filtered.length} / ${entries.length} 条记录；过程记录默认折叠，搜索或筛选过程时展开记录列表。`;
  renderCalendar(matching);
  for(const b of document.querySelectorAll('[data-timeline-scope]'))b.setAttribute('aria-pressed',String(b.dataset.timelineScope===timelineScope));
  $('timeline').innerHTML = days.length ? days.map(day=>{
   const dayEntries=filtered.filter(e=>e.date===day).slice().reverse();
   const major=['关键突破','重要成果'].map(label=>{
    const list=dayEntries.filter(e=>e.importance===label&&!isLesson(e));
    return list.length?`<h3 class="group-title">${esc(label)} <small>· ${list.length} 条</small></h3>${list.map(card).join('')}`:'';
   }).join('');
   const lessons=dayEntries.filter(isLesson);
   const lessonCards=lessons.length?`<h3 class="group-title">经验与教训 <small>· ${lessons.length} 条</small></h3>${lessons.map(card).join('')}`:'';
   const routine=dayEntries.filter(e=>e.importance==='过程记录'&&!isLesson(e));
   const process=routine.length?`<details class="process-group" ${query || importance==='过程记录' || status?'open':''}><summary>过程记录 · ${routine.length} 条 <small>中间实验 / 环境与排错 · 展开回溯</small></summary>${routine.map(card).join('')}</details>`:'';
   return `<section class="day" id="day-${day}"><h2 class="day-title">${day}</h2>${major}${lessonCards}${process}</section>`;
  }).join('') : '<div class="empty">没有匹配记录，请清除筛选后重试。</div>';
 }
 const reset = () => { timelineScope='all';selectedDate=null;calendarMonth=newestDate.slice(0,7);removeDateHash();$('search').value=''; $('status').value=''; $('importance').value=''; render(); };
 const reveal = id => {
  const target = $(id);
  if (!target) return;
  if (target.matches('details')) target.open=true;
  let parent=target.parentElement;
  while(parent){if(parent.matches('details'))parent.open=true;parent=parent.parentElement;}
  document.querySelectorAll('.jump-target').forEach(e=>e.classList.remove('jump-target'));
  target.classList.add('jump-target');
  target.scrollIntoView({behavior:'smooth'});
 };
 $('search').addEventListener('input',render);
 $('status').addEventListener('change',render);
 $('importance').addEventListener('change',render);
 $('clear').addEventListener('click',reset);
 document.addEventListener('click',event=>{
  const anchor = event.target.closest('a[data-related]');
  if (!anchor) return;
  event.preventDefault();
  const id = encodeURIComponent(anchor.dataset.related);
  reset();
  reveal(id);
  if ($(id)) history.replaceState(null,'','#'+id);
 });
 function handleHash(){
  if(location.hash==='#lessons'){openLessons();return;}
  const id=location.hash.slice(1),day=/^day-(\d{4}-\d{2}-\d{2})$/.exec(id);
  if(day&&dateCounts.has(day[1])){selectDate(day[1],{hash:false});return;}
  if(!$(id)&&entries.some(e=>encodeURIComponent(e.id)===id))reset();
  if(id)reveal(id);
 }
 window.addEventListener('hashchange',handleHash);
 render();
 if(location.hash)handleHash();
})();
