/* Matching557 x two cohorts, correct metrics/timing sources and filters. DOM double only. */
const fs=require('fs'),path=require('path'),assert=require('assert'),vm=require('vm');
const root=path.resolve(__dirname,'..'),out=path.join(root,'module_14_lm_head_v4/reports/sparse_quality_all557_20261024_r1');
const page=fs.readFileSync(path.join(root,'doc/design/V4Validation.html'),'utf8');
const historical=JSON.parse(page.match(/<script id="gpu-summary-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const both=JSON.parse(page.match(/<script id="gpu-cohort-datasets" type="application\/json">([\s\S]*?)<\/script>/)[1]);
assert(both.all557);assert.equal(both.old.points.length,557);assert.equal(both.fresh.points.length,557);assert.equal(both.comparison_ids.length,6);
assert.deepStrictEqual(both.old.points.map(p=>p.id),both.fresh.points.map(p=>p.id));
const hm=new Map(historical.points.map(p=>[p.id,p]));
for(const p of both.old.points){assert.deepStrictEqual(p.parameters,hm.get(p.id).parameters);assert.deepStrictEqual(p.quality,hm.get(p.id).quality);assert.equal(p.quality.steps,4775);}
for(const p of both.fresh.points){assert.equal(p.quality.steps,14956);assert.equal(p.supplementary,true);assert.equal(p.calls,120);assert.equal(Object.keys(p.cases).length,4);assert(p.raw.includes('/cohorts/new/timing/'));}
const elements={};class Element{constructor(id){this.id=id;this.events={};this.value='';this.checked=false;this.innerHTML='';this.textContent='';this.children=[];}addEventListener(t,f){(this.events[t]??=[]).push(f);}setAttribute(k,v){this[k]=v;}querySelectorAll(){return [];}appendChild(v){this.children.push(v);}fire(t,e={}){for(const f of this.events[t]||[])f(e);}}
for(const id of ['gpu-summary-data','gpu-mode','gpu-experiment','gpu-range','gpu-category','gpu-search','gpu-frontier','gpu-reset','gpu-overview-svg','gpu-overview-rows','gpu-inspector','gpu-summary','gpu-overview-status','gpu-cohort-datasets','gpu-cohort-old','gpu-cohort-fresh','gpu-cohort-description','gpu-cohort-notice','gpu-cohort-sources','gpu-legacy-caption','gpu-legacy-notice','gpu-legacy-methods','gpu-common-only']){assert(page.includes(`id="${id}"`));elements[id]=new Element(id);}
elements['gpu-summary-data'].textContent=JSON.stringify(historical);elements['gpu-cohort-datasets'].textContent=JSON.stringify(both);
const document={getElementById:id=>{assert(elements[id],id);return elements[id];},createElementNS:()=>new Element('new')};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'v4_gpu_summary.js'),'utf8'),{document});
function set(id,value,type='change'){elements[id].value=value;elements[id].fire(type);}
function count(){return (elements['gpu-overview-rows'].innerHTML.match(/<tr>/g)||[]).length;}
assert.equal(elements['gpu-cohort-fresh']['aria-selected'],'true');assert(elements['gpu-cohort-description'].textContent.includes('557'));assert(elements['gpu-cohort-notice'].textContent.includes('整体及每类≥99%'));
const counts={cluster:23,lowrank:33,hybrid:432,dense:1,partial:16,affinity:18,learned:18,lsh:16};
for(const key of ['fresh','old']){
 elements['gpu-cohort-'+key].fire('click');set('gpu-range','0');assert.equal(count(),557);
 for(const [mode,n] of Object.entries(counts)){set('gpu-mode',mode);assert.equal(count(),n);}
 set('gpu-mode','all');
 for(const cat of ['chinese','english','code','math','all']){set('gpu-category',cat);assert.equal(count(),557);assert(!elements['gpu-overview-svg'].innerHTML.includes('NaN'));}
 for(const p of both[key].points.filter(p=>p.experiments.includes(1)||p.mode==='partial')){
   elements['gpu-summary'].fire('click',{target:{closest:()=>({dataset:{gpuPoint:p.id}})}});
   assert(elements['gpu-inspector'].innerHTML.includes(p.rate.toFixed(2)));assert(elements['gpu-inspector'].innerHTML.includes(`${p.quality.misses} / ${p.quality.steps}`));
 }
 elements['gpu-common-only'].checked=true;elements['gpu-common-only'].fire('change');assert.equal(count(),6);
 elements['gpu-common-only'].checked=false;elements['gpu-common-only'].fire('change');assert.equal(count(),557);
 set('gpu-search','nonexistent_testing','input');assert.equal(count(),0);elements['gpu-reset'].fire('click');
 assert(elements['gpu-cohort-sources'].innerHTML.includes('同轮')||elements['gpu-cohort-sources'].innerHTML.includes('配对重测'));
 for(const source of ['github.com/haonan-li/CMMLU','github.com/databrickslabs/dolly','github.com/openai/grade-school-math'])assert(elements['gpu-cohort-sources'].innerHTML.includes(source));
}
elements['gpu-cohort-fresh'].fire('click');set('gpu-range','0');
assert(elements['gpu-cohort-sources'].innerHTML.includes('github.com/xlang-ai/DS-1000'));assert(elements['gpu-cohort-sources'].innerHTML.includes('补充分析'));assert(elements['gpu-cohort-sources'].innerHTML.includes('133680'));
const freshTicks=[...elements['gpu-overview-svg'].innerHTML.matchAll(/<text x="74"[^>]*>([^<]+)<\/text>/g)].map(x=>x[1]);
elements['gpu-cohort-old'].fire('click');const oldTicks=[...elements['gpu-overview-svg'].innerHTML.matchAll(/<text x="74"[^>]*>([^<]+)<\/text>/g)].map(x=>x[1]);assert.deepStrictEqual(oldTicks,freshTicks);
set('gpu-category','code');set('gpu-search','C128_R4_L16384','input');
elements['gpu-summary'].fire('click',{target:{closest:()=>({dataset:{gpuPoint:'cluster_C128_R4_L16384'}})}});
elements['gpu-cohort-fresh'].fire('click');assert.equal(elements['gpu-category'].value,'code');assert.equal(elements['gpu-search'].value,'C128_R4_L16384');assert(elements['gpu-inspector'].innerHTML.includes('C128_R4_L16384'));
elements['gpu-reset'].fire('click');set('gpu-range','0');
const full=both.fresh.points.find(p=>p.mode==='affinity'&&p.parameters.R===p.parameters.C);elements['gpu-summary'].fire('click',{target:{closest:()=>({dataset:{gpuPoint:full.id}})}});assert(elements['gpu-inspector'].innerHTML.includes('全词表'));
const result={state:'PASS_MATCHED557_PAIRED_COHORTS_AND_SUPPLEMENTARY_SCOPE',old_points:557,new_points:557,mode_counts:counts,checks:['same557 IDs/parameters','old4775 vs new14956 quality','same-round cohort120 timings','eight mode filters','all category metric isolation','first-six subset checkbox','source links and supplemental identity','full vocabulary warning','common axes and retained filters/selection across tabs','reset/search/empty/roundtrip'],browser_visual:'NOT_RUN'};
fs.writeFileSync(path.join(out,'COHORT_UI_REVIEW.json'),JSON.stringify(result,null,2)+'\n');console.log(result);
