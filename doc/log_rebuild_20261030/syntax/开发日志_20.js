
(()=>{'use strict';
 const shell=document.querySelector('.shell'),body=document.getElementById('rail-body'),toggle=document.getElementById('sidebar-toggle');
 const key='dev-log-sidebar-collapsed:'+location.pathname,media=matchMedia('(max-width:800px)');
 let preference=null;try{preference=localStorage.getItem(key);}catch{}
 function apply(collapsed){
  shell.classList.toggle('rail-collapsed',collapsed);body.hidden=collapsed;
  toggle.setAttribute('aria-expanded',String(!collapsed));toggle.setAttribute('aria-label',collapsed?'展开侧栏':'收起侧栏');
  toggle.querySelector('.rail-toggle-label').textContent=collapsed?'展开侧栏':'收起侧栏';
  toggle.querySelector('.rail-toggle-icon').textContent=collapsed?'☰':'‹';
  requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));
 }
 toggle.addEventListener('click',()=>{preference=String(!shell.classList.contains('rail-collapsed'));try{localStorage.setItem(key,preference);}catch{}apply(preference==='true');});
 media.addEventListener('change',()=>{if(preference===null)apply(media.matches);});
 apply(preference===null?media.matches:preference==='true');
})();

