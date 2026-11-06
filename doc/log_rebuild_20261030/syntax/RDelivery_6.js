
'use strict';
(()=>{
const data=JSON.parse(document.getElementById('design-data').textContent),r=data.route,d=data.design,$=id=>document.getElementById(id),ns='http://www.w3.org/2000/svg';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safe=v=>{const s=String(v||'').trim();return s&&!/[\u0000-\u001f\u007f]/.test(s)&&!s.startsWith('//')&&(!/^[a-z][a-z0-9+.-]*:/i.test(s)||/^(https?:|file:)/i.test(s))?s:'';};
const states={verified:'✓ 已验证',active:'● 进行中',waiting:'⏸ 等待条件',planned:'○ 未开始',failed:'× 未通过',na:'— 不适用',unknown:'? 未确认'};
$('back').href=safe(data.back)||'#';$('title').textContent=r.id+' · '+r.title;document.title=r.title+' · 路线设计';$('scope').textContent=r.scope;$('goal').textContent=r.goal;
$('snapshot').textContent='路线快照 '+data.updated;$('boundary').textContent=d.status_note||'验证范围见下方阶段；未完成的阶段仍待验证。';
$('outcome').textContent=r.outcome;$('next').textContent='下一步：'+(r.next||'未记录');$('overview').textContent=d.overview||'设计说明尚待补充';
$('stages').innerHTML=data.stages.map(s=>`<div class="stage-item ${esc(r.cells[s.id].state)}"><b>${esc(s.title)}</b><span>${esc(states[r.cells[s.id].state])}</span>${esc(r.cells[s.id].note)}</div>`).join('');
for(const id of ['contracts','tradeoffs'])$(''+id).innerHTML=(d[id]||[]).map(s=>`<li>${esc(s)}</li>`).join('')||'<li>尚未记录</li>';
const relative=h=>/^(?:[a-z][a-z0-9+.-]*:|\/|#)/i.test(h)?h:'../../'+h;
$('evidence').innerHTML=[...(r.evidence||[]),...(d.evidence||[])].filter(e=>safe(e.href)).map(e=>`<a href="${esc(relative(e.href))}">${esc(e.label)}</a>`).join('')||'尚无附件证据';
const svg=$('diagram'),nodes=new Map(d.nodes.map(n=>[n.id,n]));
const width=(Math.max(...d.nodes.map(n=>n.col))+1)*260+20,height=(Math.max(...d.nodes.map(n=>n.row))+1)*160+20;
svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
function el(tag,attrs={}){const e=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;}
for(const edge of d.edges||[]){const a=nodes.get(edge.source),b=nodes.get(edge.target),vertical=a.col===b.col,forward=vertical?b.row>a.row:b.col>a.col;
const x1=a.col*260+(vertical?125:forward?230:20),y1=a.row*160+(vertical?(forward?120:20):70),x2=b.col*260+(vertical?125:forward?20:230),y2=b.row*160+(vertical?(forward?20:120):70);
const path=vertical?`M${x1} ${y1} L${x2} ${y2}`:`M${x1} ${y1} C${(x1+x2)/2} ${y1},${(x1+x2)/2} ${y2},${x2} ${y2}`;
const line=el('path',{d:path,class:'edge'});svg.append(line);const title=el('title');title.textContent=edge.label||'';line.append(title);
const arrow=el('path',{d:vertical?`M${x2-5} ${y2+(forward?-7:7)} L${x2} ${y2} L${x2+5} ${y2+(forward?-7:7)}`:`M${x2+(forward?-7:7)} ${y2-5} L${x2} ${y2} L${x2+(forward?-7:7)} ${y2+5}`,class:'edge'});svg.append(arrow);}
for(const n of d.nodes){const x=n.col*260+20,y=n.row*160+20,g=el('g',{class:'node',tabindex:'0',role:'button','data-node':n.id,'aria-label':n.title});g.append(el('rect',{x,y,width:210,height:100,rx:9}));
const fo=el('foreignObject',{x,y,width:210,height:100}),box=document.createElementNS('http://www.w3.org/1999/xhtml','div');box.setAttribute('class','node-label');box.textContent=n.title;const small=document.createElementNS('http://www.w3.org/1999/xhtml','small');small.textContent=n.caption||'';box.append(small);fo.append(box);g.append(fo);svg.append(g);}
function select(id){const n=nodes.get(id);if(!n)return;svg.querySelectorAll('[data-node]').forEach(g=>g.classList.toggle('selected',g.dataset.node===id));$('node-title').textContent=n.title;$('node-detail').textContent=n.detail||n.caption||'未记录';}
svg.addEventListener('click',e=>{const g=e.target.closest('[data-node]');if(g)select(g.dataset.node);});
svg.addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){const g=e.target.closest('[data-node]');if(g){e.preventDefault();select(g.dataset.node);}}});
$('steps').innerHTML=(d.steps||[]).map((s,i)=>`<button type="button" data-step="${i}" aria-pressed="false">${esc(s.title)}</button>`).join('');
$('steps').addEventListener('click',e=>{const b=e.target.closest('[data-step]');if(!b)return;const s=d.steps[Number(b.dataset.step)];$('steps').querySelectorAll('button').forEach(v=>v.setAttribute('aria-pressed',String(v===b)));svg.querySelectorAll('[data-node]').forEach(g=>{g.classList.toggle('muted',!s.nodes.includes(g.dataset.node));g.classList.toggle('step-active',s.nodes.includes(g.dataset.node));});$('step-description').textContent=s.description||'';select(s.nodes[0]);});
$('reset').addEventListener('click',()=>{svg.querySelectorAll('[data-node]').forEach(g=>g.classList.remove('muted','step-active'));$('steps').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed','false'));$('step-description').textContent='';});
let zoom=1;$('zoom-in').addEventListener('click',()=>{zoom=Math.min(2,zoom+.2);svg.style.width=zoom*100+'%';});$('zoom-fit').addEventListener('click',()=>{zoom=1;svg.style.width='100%';svg.style.minWidth='0';});select(d.nodes[0].id);
})();
