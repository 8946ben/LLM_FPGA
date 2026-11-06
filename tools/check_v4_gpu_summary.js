/* Functional offline UI logic check using a DOM double; NOT browser visual QA. */
const fs=require('fs'),path=require('path'),assert=require('assert'),vm=require('vm');
const root=path.resolve(__dirname,'..'),folder=process.argv[2]?path.resolve(root,process.argv[2]):path.join(root,'module_14_lm_head_v4/reports/gpu_summary_20261024_r1');
const data=JSON.parse(fs.readFileSync(path.join(folder,'SUMMARY_DATA.json'),'utf8'));
const page=fs.readFileSync(path.join(root,'doc/design/V4Validation.html'),'utf8');
const source=fs.readFileSync(path.join(__dirname,'v4_gpu_summary.js'),'utf8');
const {metrics,filterPoints,frontier}=require('./v4_gpu_summary.js');
const total=data.new_research?557:489;assert.equal(data.points.length,total);
assert(page.indexOf('id="gpu-summary"')<page.indexOf('id="experiments"'));
const embedded=JSON.parse(page.match(/<script id="gpu-summary-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
assert.deepStrictEqual(data,embedded);
const elements={};
class Element {
  constructor(id){this.id=id;this.value='';this.checked=false;this.innerHTML='';this.textContent='';this.events={};this.children=[];}
  addEventListener(type,fn){(this.events[type]??=[]).push(fn);}
  querySelectorAll(){return [];}
  setAttribute(k,v){this[k]=v;}
  appendChild(n){this.children.push(n);}
  fire(type,event={}){for(const f of this.events[type]||[])f(event);}
}
for(const id of ['gpu-summary-data','gpu-mode','gpu-experiment','gpu-range','gpu-category','gpu-search','gpu-frontier','gpu-reset','gpu-overview-svg','gpu-overview-rows','gpu-inspector','gpu-summary','gpu-overview-status']){
  assert(page.includes(`id="${id}"`),id);elements[id]=new Element(id);
}
for(const id of ['gpu-cohort-datasets','gpu-cohort-old','gpu-cohort-fresh','gpu-cohort-description','gpu-cohort-notice','gpu-cohort-sources','gpu-legacy-caption','gpu-legacy-notice','gpu-legacy-methods','gpu-common-only']){
  if(page.includes(`id="${id}"`))elements[id]=new Element(id);
}
if(elements['gpu-cohort-datasets']){
  const both=JSON.parse(page.match(/<script id="gpu-cohort-datasets" type="application\/json">([\s\S]*?)<\/script>/)[1]);both.default='old';elements['gpu-cohort-datasets'].textContent=JSON.stringify(both);
}
elements['gpu-summary-data'].textContent=JSON.stringify(data);
for(const id of ['gpu-mode','gpu-experiment','gpu-category'])elements[id].value='all';
elements['gpu-range'].value='99';elements['gpu-frontier'].checked=true;
const document={getElementById:id=>{if(id==='gpu-cohort-datasets'&&!elements[id])return null;assert(elements[id],id);return elements[id];},createElementNS:()=>new Element('new')};
vm.runInNewContext(source,{document,console});
function displayed(){return (elements['gpu-overview-rows'].innerHTML.match(/<tr>/g)||[]).length;}
function set(id,value,event='change'){elements[id].value=value;elements[id].fire(event);}
const counts={};
const newModes=data.new_research?[['partial',16],['affinity',18],['learned',18],['lsh',16]]:[];
assert(displayed()>0 && displayed()<total);
set('gpu-range','0');assert.equal(displayed(),total);
for(const [mode,n] of [['cluster',23],['lowrank',33],['hybrid',432],['dense',1],...newModes]){
  set('gpu-mode',mode);assert.equal(displayed(),n);counts[mode]=n;
}
set('gpu-mode','all');set('gpu-experiment','1');assert.equal(displayed(),4);
set('gpu-experiment','8');assert.equal(displayed(),24);
set('gpu-experiment','9');assert.equal(displayed(),34);
set('gpu-experiment','10');assert.equal(displayed(),433);
if(data.new_research){for(const [exp,n] of [[11,17],[12,19],[13,19],[14,17]]){set('gpu-experiment',String(exp));assert.equal(displayed(),n);}}
set('gpu-experiment','all');set('gpu-search','C256_R4_L16384','input');assert.equal(displayed(),13);
set('gpu-search','does_not_exist_abc','input');assert.equal(displayed(),0);assert(elements['gpu-overview-svg'].innerHTML.includes('没有数据'));
set('gpu-search','','input');
for(const cat of ['chinese','english','code','math']){
  set('gpu-category',cat);assert.equal(displayed(),total);assert(!elements['gpu-overview-svg'].innerHTML.includes('NaN'));
  const p=data.points.find(p=>p.mode==='dense');assert.equal(metrics(p,cat).rate,1000/p.cases[cat].mean_ms);
}
set('gpu-category','all');set('gpu-range','99.9');assert(displayed()>0 && displayed()<total);
set('gpu-frontier','');elements['gpu-frontier'].checked=false;elements['gpu-frontier'].fire('change');
set('gpu-range','0');
const selected=data.old_selected;
elements['gpu-summary'].fire('click',{target:{closest:()=>({dataset:{gpuPoint:selected}})}});
assert(elements['gpu-inspector'].innerHTML.includes('19/14986'));
assert(elements['gpu-inspector'].innerHTML.includes('门槛失败'));
elements['gpu-reset'].fire('click');assert.equal(elements['gpu-mode'].value,'all');assert.equal(elements['gpu-range'].value,'99');assert.equal(elements['gpu-search'].value,'');assert(elements['gpu-frontier'].checked);
const points=filterPoints(data.points,{mode:'all',experiment:'all',category:'all',min:99,search:''});
for(const p of frontier(points)){
 const a=metrics(p);assert(!points.some(q=>{const b=metrics(q);return b.recall>=a.recall&&b.rate>=a.rate&&(b.recall>a.recall||b.rate>a.rate);}));
}
const result={state:'PASS_EMBEDDED_DATA_AND_FUNCTIONAL_UI_LOGIC_DOM_DOUBLE',configurations:total,mode_counts:counts,checks:['default99 axis and full configuration range','all mode and experiment filters with shared baselines','search/empty/reset','all four category quality and speed','point inspection retains independent E10 failure','finite SVG coordinates','nondominated observation boundary','embedded payload equality and panel placement'],browser_visual:'NOT_RUN: DOM double checks runtime/logic, not browser rendering',hardware_access:'NONE'};
fs.writeFileSync(path.join(folder,'UI_LOGIC_REVIEW.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
