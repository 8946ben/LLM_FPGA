/* Two real-data tabs and cross-cohort metric isolation. DOM double, not visual QA. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..'),out=path.join(root,'module_14_lm_head_v4/reports/sparse_quality_20261024_r1');
const page=fs.readFileSync(path.join(root,'doc/design/V4Validation.html'),'utf8');
const data=JSON.parse(page.match(/<script id="gpu-summary-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const cohorts=JSON.parse(page.match(/<script id="gpu-cohort-datasets" type="application\/json">([\s\S]*?)<\/script>/)[1]);
if(cohorts.all557){require('./check_v4_all557_cohorts_20261024.js');process.exit(0);}
assert.equal(cohorts.default,'fresh');assert.equal(cohorts.old.points.length,557);assert.equal(cohorts.fresh.points.length,6);
const elements={};class Element{constructor(id){this.id=id;this.value='';this.checked=false;this.events={};this.innerHTML='';this.textContent='';this.children=[];}addEventListener(t,f){(this.events[t]??=[]).push(f);}setAttribute(k,v){this[k]=v;}querySelectorAll(){return [];}appendChild(n){this.children.push(n);}fire(t,e={}){for(const f of this.events[t]||[])f(e);}}
for(const id of ['gpu-summary-data','gpu-mode','gpu-experiment','gpu-range','gpu-category','gpu-search','gpu-frontier','gpu-reset','gpu-overview-svg','gpu-overview-rows','gpu-inspector','gpu-summary','gpu-overview-status','gpu-cohort-datasets','gpu-cohort-old','gpu-cohort-fresh','gpu-cohort-description','gpu-cohort-notice','gpu-cohort-sources','gpu-legacy-caption','gpu-legacy-notice','gpu-legacy-methods','gpu-common-only']){assert(page.includes(`id="${id}"`));elements[id]=new Element(id);}
elements['gpu-summary-data'].textContent=JSON.stringify(data);elements['gpu-cohort-datasets'].textContent=JSON.stringify(cohorts);
const document={getElementById:id=>{assert(elements[id],id);return elements[id];},createElementNS:()=>new Element('new')};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'v4_gpu_summary.js'),'utf8'),{document});
function set(id,value,event='change'){elements[id].value=value;elements[id].fire(event);}
function count(){return (elements['gpu-overview-rows'].innerHTML.match(/<tr>/g)||[]).length;}
assert.equal(elements['gpu-cohort-fresh']['aria-selected'],'true');assert(elements['gpu-cohort-description'].textContent.includes('1000题'));assert(elements['gpu-legacy-methods'].hidden);
set('gpu-range','0');assert.equal(count(),6);
for(const p of cohorts.fresh.points){
 elements['gpu-summary'].fire('click',{target:{closest:()=>({dataset:{gpuPoint:p.id}})}});
 assert(elements['gpu-inspector'].innerHTML.includes(`${p.quality.misses} / ${p.quality.steps}`));
 assert(elements['gpu-inspector'].innerHTML.includes(p.rate.toFixed(2)));assert(!elements['gpu-inspector'].innerHTML.includes('4,775'));
 assert(elements['gpu-inspector'].innerHTML.includes(p.gate99));
}
for(const cat of ['chinese','english','code','math']){set('gpu-category',cat);assert.equal(count(),6);assert(!elements['gpu-overview-svg'].innerHTML.includes('NaN'));}
const freshHTML=elements['gpu-cohort-sources'].innerHTML;
for(const url of ['github.com/haonan-li/CMMLU','github.com/databrickslabs/dolly','github.com/xlang-ai/DS-1000','github.com/openai/grade-school-math'])assert(freshHTML.includes(url));
assert(freshHTML.includes('9份历史'));assert(freshHTML.includes('代码分布变化'));
elements['gpu-cohort-old'].fire('click');assert.equal(elements['gpu-cohort-old']['aria-selected'],'true');assert.equal(elements['gpu-range'].value,'99');assert(!elements['gpu-legacy-methods'].hidden);
set('gpu-range','0');assert.equal(count(),557);assert(elements['gpu-cohort-sources'].innerHTML.includes('google-research/google-research/tree/master/mbpp'));
elements['gpu-common-only'].checked=true;elements['gpu-common-only'].fire('change');assert.equal(count(),6);
for(const p of cohorts.paired_old.points){
 elements['gpu-summary'].fire('click',{target:{closest:()=>({dataset:{gpuPoint:p.id}})}});
 assert(elements['gpu-inspector'].innerHTML.includes(p.rate.toFixed(2)));
 const q=cohorts.old.points.find(x=>x.id===p.id);assert.deepStrictEqual(p.quality,q.quality);
}
elements['gpu-common-only'].checked=false;elements['gpu-common-only'].fire('change');assert.equal(count(),557);
const id='partial_dynamic_d64_T4096';elements['gpu-summary'].fire('click',{target:{closest:()=>({dataset:{gpuPoint:id}})}});const old=cohorts.old.points.find(p=>p.id===id);assert(elements['gpu-inspector'].innerHTML.includes(`${old.quality.misses} / ${old.quality.steps}`));
elements['gpu-cohort-fresh'].fire('click');set('gpu-range','0');assert.equal(count(),6);assert(elements['gpu-cohort-notice'].textContent.includes('每类≥99%'));
assert.deepStrictEqual(cohorts.old.points,data.points);
const result={state:'PASS_BOTH_DATA_TABS_AND_METRIC_ISOLATION',old_points:557,new_points:6,source_links:'official four sources per cohort, pinned revisions and local evidence',checks:['fresh default','old/fresh roundtrip','reset filters on switching','separate recall/K/rates/case timings','all six result details and99% gate','source links and code-distribution change','full-range excludes no tested point','historical557 unchanged'],browser_visual:'NOT_RUN'};
fs.writeFileSync(path.join(out,'COHORT_UI_REVIEW.json'),JSON.stringify(result,null,2)+'\n');console.log(result);
