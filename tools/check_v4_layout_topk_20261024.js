// Offline DOM substitute, numerical bindings and every selectable combination.
const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..'),page=fs.readFileSync(path.join(root,'doc/design/V4LayoutTopK.html'),'utf8');
const data=JSON.parse(page.match(/<script id="layout-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const code=[...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
const elements={};
for(const id of ['config','case','tile','layout','k','amp','quality','bars','access','key-cost','cpu-top','arena','regions'])elements[id]={value:'',textContent:'',innerHTML:'',addEventListener(){}};
elements['layout-data']={textContent:JSON.stringify(data)};
elements.config.value='partial_dynamic_d64_T4096';elements.case.value='new_chinese';elements.tile.value='1024';elements.layout.value='dual';
const ctx={document:{getElementById:id=>{assert(elements[id],id);return elements[id];}}};vm.createContext(ctx);new vm.Script(code).runInContext(ctx);
let renders=0;
for(const id of ['partial_dynamic_d64_T4096','partial_dynamic_d128_T1024'])for(const c of [...new Set(data.access.map(x=>x.case))])for(const tile of [128,1024])for(const layout of ['dual','shared']){
  elements.config.value=id;elements.case.value=c;elements.tile.value=String(tile);elements.layout.value=layout;vm.runInContext('update()',ctx);renders++;
  const v=vm.runInContext(`buildView(${JSON.stringify(id)},${JSON.stringify(c)},${tile},${JSON.stringify(layout)})`,ctx);
  assert(v.row.k>=1024&&v.q.minimum>=.99);assert(v.values[1]>v.values[0]);assert(v.profile.arena_bytes<2**31);assert(elements.bars.innerHTML.includes('MiB'));assert(elements.regions.innerHTML.includes('candidate_bitmap'));
  assert(elements['cpu-top'].textContent.includes('不能用于硬件速度排名'));assert(elements['key-cost'].textContent.includes('3.478'));
}
assert.strictEqual(renders,64);assert(!page.includes('__DATA__'));assert(!page.includes('__CASES__'));assert(!page.includes('__LINKS__'));
console.log(JSON.stringify({state:'PASS',renders,methodCount:2,caseCount:8,tiles:[128,1024],layouts:['dual','shared'],scope:'DOM substitute; browser visual NOT_RUN'}));
