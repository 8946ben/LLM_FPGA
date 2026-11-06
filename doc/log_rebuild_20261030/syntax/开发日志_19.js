
(()=>{'use strict';const data=JSON.parse(document.getElementById('dev-log-data').textContent),d=data.task_overview;
const routes=new Map((data.exploration?.routes||[]).map(r=>[r.id,r]));
const section=document.getElementById('task-overview-panel');if(!d?.rows?.length){section.hidden=true;document.getElementById('task-overview-nav').hidden=true;return;}
document.getElementById('task-overview-title').textContent=d.title||'任务进展总览';
document.getElementById('task-overview-note').textContent=d.note;
document.getElementById('task-overview-snapshot').textContent='结果快照：'+(d.snapshot_at||'未记录')+' · '+(data.project.timezone||'Asia/Shanghai');
document.getElementById('task-overview-count').textContent=d.rows.length+'项任务';
const body=document.getElementById('task-overview-body');body.replaceChildren();
for(const r of d.rows){const tr=document.createElement('tr');tr.dataset.task=r.id;tr.id='task-'+r.id;tr.tabIndex=-1;
 const task=document.createElement('td'),work=document.createElement('td'),scope=document.createElement('td');
 const name=document.createElement('strong');name.className='task-name';name.textContent=r.task_label||r.task;task.append(name);
 const state=document.createElement('span');state.className='task-state '+(['verified','active','pending','waiting','stopped'].includes(r.state)?r.state:'pending');state.textContent=r.status;task.append(state);
 const routeLinks=document.createElement('div');routeLinks.className='task-route-links';
 for(const id of r.route_ids||[]){const route=routes.get(id);if(!route)continue;const a=document.createElement('a');a.href='#route-'+id;a.dataset.routeJump=id;a.textContent=route.title;a.setAttribute('aria-label','定位路线：'+id+' '+route.title);routeLinks.append(a);}
 task.append(routeLinks);
 const spec=document.createElement('small');spec.className='task-spec';spec.textContent=r.spec;work.append(spec);
 const result=document.createElement('p');for(const x of r.work||[]){const node=document.createElement(x.strong?'strong':'span');node.textContent=x.text;result.append(node);}work.append(result);
 if(r.evidence?.href&&!/^[a-z][a-z0-9+.-]*:/i.test(r.evidence.href)&&!r.evidence.href.startsWith('//')){const proof=document.createElement('p');proof.className='task-evidence';const a=document.createElement('a');a.href=r.evidence.href;a.textContent=r.evidence.label||'查看证据';proof.append(a);work.append(proof);}
 scope.textContent=r.scope;tr.append(task,work,scope);body.append(tr);
}
})();
