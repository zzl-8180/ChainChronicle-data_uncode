// Actual generated-page script in a DOM fixture; no browser visual acceptance.
const fs=require('fs'),vm=require('vm'),base='output/character_skills/',out=base+'description_bindings/p3b8_boss/';
const rows=p=>fs.readFileSync(p,'utf8').trim().split('\n').map(JSON.parse);
const html=fs.readFileSync(base+'profiles/index.html','utf8'),src=html.match(/<script>([\s\S]*)<\/script>/)[1],store={};
const el=id=>({id,value:'',innerHTML:'',textContent:'',children:[],addEventListener(){},appendChild(c){this.children.push(c);}});
const box={document:{getElementById(id){return store[id]||(store[id]=el(id));},createElement:el},location:{hash:''},window:{addEventListener(){}},console,JSON,Math,String,Array,Map,Object,RegExp};
vm.createContext(box);vm.runInContext(src,box,{timeout:120000});
const checks=[],check=(name,passed)=>checks.push({name,passed});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const recs=Object.fromEntries(rows(base+'profiles/records.jsonl').map(r=>[r.rec_key,r]));
check('embedded all records equal JSONL',vm.runInContext('JSON.stringify(RECS)',box)===JSON.stringify(recs));
const ledger=rows(out+'bindings.jsonl'),snapshots=[];
for(const item of ledger){
 const cid=item.record_id,b=item.after.binding;store.q.value=String(cid);box.go();const h=store.view.innerHTML;
 check('cid '+cid+' whole sentence formula source scope conditions and limits',h.includes(esc(item.after.t))&&h.includes(esc(b.fields[0].value))&&h.includes(esc(b.strength))&&h.includes(esc(b.condition))&&h.includes(esc(b.limits))&&h.includes(esc(b.source.record_key))&&h.includes('按类型套用'));
 const separate=item.all_contexts.related_groups.flatMap(g=>g.records).filter(r=>r.table==='denju');
 check('cid '+cid+' separate denju text never borrows own formula',separate.every(e=>Object.values(recs).filter(r=>r.table==='denju'&&r.record_id===e.reference_id).every(r=>r.fragments.every(f=>!f.binding)&&r.fragments.every(f=>h.includes(esc(f.t))))));
 snapshots.push({cid,template:b.template_id,related_denju:separate.length});
}
store.q.value='29';box.go();check('old complete29 and 24 unknown fields',store.view.innerHTML.includes('状态 完整')&&store.view.innerHTML.includes('未解释字段 24')&&store.view.innerHTML.includes('type26_start_mana_3101'));
store.q.value='30236';box.go();check('101 baseline answers',store.view.innerHTML.includes('已有逐描述答案 101'));
store.q.value='34';box.go();check('heal is runtime formula with explicit HP limitation',store.view.innerHTML.includes('不是具体HP或最终回血量')&&store.view.innerHTML.includes('onlyVisible=0'));
store.q.value='5';box.go();check('single target has no nearest or guaranteed-hit promise',store.view.innerHTML.includes('至多一次Attack请求')&&store.view.innerHTML.includes('不保证命中全部敌人或最近目标'));
check('old B6 B7 and type8 template strengths retained',html.includes('p3b6_type5_intrinsic_line_damage')&&html.includes('p3b7_type26_start_mana_exact_digit')&&html.includes('逐记录人工语义对应'));
const result={kind:'C DOM fixture, not independent D/browser visual acceptance',passed:checks.filter(c=>c.passed).length,total:checks.length,checks};
fs.writeFileSync(out+'dom_validation.json',JSON.stringify(result,null,1)+'\n');fs.writeFileSync(out+'dom_snapshots.json',JSON.stringify(snapshots,null,1)+'\n');console.log(JSON.stringify({passed:result.passed,total:result.total}));process.exit(result.passed===result.total?0:1);
