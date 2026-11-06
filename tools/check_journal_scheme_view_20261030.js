// Offline data/DOM-substitute interaction audit. Not a real browser/layout test.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'开发日志.html'),'utf8');
const data=JSON.parse(html.match(/<script id="dev-log-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const src=html.match(/<script id="dev-log-performance-js">([\s\S]*?)<\/script>/)[1];
const elements=new Map();
class E{
 constructor(id){this.id=id;this.textContent='';this._html='';this.value='';this.events={};this.hidden=false;this.classList={remove(){},add(){},toggle(){}};this.nodes=[];}
 set innerHTML(s){this._html=s;for(const [,id]of s.matchAll(/\bid="([^"]+)"/g))elements.set(id,new E(id));this.nodes=[...s.matchAll(/data-scheme="([^"]+)"/g)].map(m=>{const e=new E('bar');e.dataset={scheme:m[1]};return e;});}
 get innerHTML(){return this._html;}
 addEventListener(name,f){this.events[name]=f;}
 querySelectorAll(){return this.nodes;}
 fire(name,event={}){assert(this.events[name],this.id+' event '+name);this.events[name](event);}
}
const ids=['dev-log-data','perf-variant','perf-title','perf-candidate','perf-current','perf-cards','perf-meta','perf-method','perf-proof','perf-comparison-head','perf-comparison-body'];for(const id of ids)elements.set(id,new E(id));elements.get('dev-log-data').textContent=JSON.stringify(data);
const document={getElementById:id=>{assert(elements.has(id),'Missing element '+id);return elements.get(id);}};
const win={events:{},addEventListener(k,f){this.events[k]=f;}};
vm.runInNewContext(src,{document,window:win,console,Number,Object,Math,String});
const get=id=>elements.get(id),p=data.performance,c=p.scheme_comparison;
assert.equal(get('perf-variant').value,'hybrid256');assert.equal(get('perf-evaluation').value,'aggregate');
assert(get('perf-cards').innerHTML.includes('27.437'));assert(get('perf-cards').innerHTML.includes('L2聚类256中心＋rank64低秩预筛＋BF16候选精算'));
assert(!get('perf-variant').innerHTML.includes('早期v4混合')&&!get('perf-variant').innerHTML.includes('实验10融合'));
for(const evaluation of Object.keys(c.evaluations)){
 const f=get('perf-evaluation');f.value=evaluation;f.fire('change');
 assert.equal(get('scheme-comparison-plot').querySelectorAll().length,2);
 assert(!get('scheme-comparison-plot').innerHTML.includes('实验记录（按时间）'));
 assert(get('scheme-comparison-table').innerHTML.includes(c.evaluations[evaluation]));
 for(const scheme of c.schemes){
  const v=p.variants.find(v=>v.id===scheme.variant_ids[evaluation]);assert(get('scheme-comparison-table').innerHTML.includes(v.values.decode.toLocaleString('zh-CN',{maximumFractionDigits:3})));
 }
 get('scheme-comparison-plot').nodes[0].fire('click');assert.equal(get('perf-variant').value,'hybrid128');
 get('scheme-comparison-plot').nodes[1].fire('keydown',{key:'Enter',preventDefault(){}});assert.equal(get('perf-variant').value,'hybrid256');
}
get('perf-variant').value='lm-head-v31-pl-ddr';get('perf-variant').fire('change');assert(get('perf-cards').innerHTML.includes('历史IP计数口径'));
get('perf-variant').value='hybrid128';get('perf-variant').fire('change');win.events.resize();assert.equal(get('scheme-comparison-plot').nodes.length,2);
const proof=JSON.parse(fs.readFileSync(path.join(root,c.source),'utf8'));
for(const method of proof.methods){
 let totalSeconds=0,totalCount=0;
 for(const source of method.sources){
  const folder=path.join(root,source.path),h=fs.readFileSync(path.join(folder,'header.bin')),r=fs.readFileSync(path.join(folder,'records.bin'));const hz=Number(h.readBigUInt64LE(64));let n=0;
  for(let i=0;i<r.length;i+=128)if(r.readUInt32LE(i+4)===1){totalSeconds+=Number(r.readBigUInt64LE(i+72)-r.readBigUInt64LE(i+64))/hz;totalCount++;n++;}
  assert.equal(n,30);
 }
 assert.equal(totalCount,120);assert(Math.abs(totalCount/totalSeconds-method.rate)<1e-10);
 const s=c.schemes.find(s=>s.id===method.scheme_id),v=p.variants.find(v=>v.id===s.variant_ids.aggregate);assert.equal(v.values.decode,method.rate);assert.equal(v.values.mean_ms,method.mean_ms);
}
const result={state:'PASS_METHOD_NAMES_RAW_TIMING_AGGREGATES_AND_OFFLINE_INTERACTION_MODEL',schemes:2,evaluations:5,bars_per_evaluation:2,measurement_records:240,default:'four_class_equal_weight_aggregate',checks:['real method names','primary method description','five evaluation switches','two method bars','bar click/keyboard selects method','historical timing boundary','resize handler','independent Node raw tick recomputation'],real_browser_visual:'NOT_RUN_FILE_POLICY',real_touch:'NOT_RUN'};
fs.writeFileSync(path.join(root,'doc/log_rebuild_20261030/SCHEME_VIEW_REVIEW.json'),JSON.stringify(result,null,2)+'\n');console.log(result);
