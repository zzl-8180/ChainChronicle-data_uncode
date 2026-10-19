// Generated HTML's actual script in a DOM fixture; not visual acceptance.
const fs=require('fs'),vm=require('vm'),base='output/character_skills/',out=base+'description_bindings/p3b9_batch/';
const rows=p=>fs.readFileSync(p,'utf8').trim().split('\n').map(JSON.parse);
const html=fs.readFileSync(base+'profiles/index.html','utf8'),src=html.match(/<script>([\s\S]*)<\/script>/)[1],store={};
const el=id=>({id,value:'',innerHTML:'',textContent:'',children:[],addEventListener(){},appendChild(c){this.children.push(c);}});
const box={document:{getElementById(id){return store[id]||(store[id]=el(id));},createElement:el},location:{hash:''},window:{addEventListener(){}},console,JSON,Math,String,Array,Map,Object,RegExp};
vm.createContext(box);vm.runInContext(src,box,{timeout:120000});
const checks=[],check=(name,passed)=>checks.push({name,passed});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const recs=Object.fromEntries(rows(base+'profiles/records.jsonl').map(r=>[r.rec_key,r]));
check('all embedded records exactly equal JSONL',vm.runInContext('JSON.stringify(RECS)',box)===JSON.stringify(recs));
const snapshots=[];
for(const item of rows(out+'bindings.jsonl')){
 const cid=item.page_uses[0].cid,b=item.after.binding;store.q.value=String(cid);box.go();const h=store.view.innerHTML;
 check('cid '+cid+' exact sentence all values units raw condition scope and source',h.includes(esc(item.after.t))&&b.fields.every(f=>h.includes(esc(f.value))&&h.includes(esc(f.unit)))&&h.includes(esc(b.condition))&&h.includes(esc(b.strength))&&h.includes(esc(b.limits))&&h.includes(esc(b.source.record_key))&&h.includes('按类型套用'));
 check('cid '+cid+' loaded-slot3 and real predicate visible',h.includes('skillid[3]')&&h.includes('_isActive')&&h.includes('聚合职业位图')&&h.includes('int(param0)'));
 if(item.subgroup==='TEXT_NO_SELF_EXCLUSION_NATIVE_THRESHOLD2')check('cid '+cid+' threshold2 prose discrepancy visible',h.includes('未写原生所需合格计数&gt;=2')&&h.includes('不改为1'));
 snapshots.push({cid,record_id:item.record_id,subgroup:item.subgroup,fields:b.fields.length});
}
const missing=Object.values(recs).find(r=>r.table==='skilllist'&&r.record_id===30620310);
check('missing-holder-job root remains unbound',missing.fragments.every(f=>!f.binding));
for(const cid of [29,2020,5023]){store.q.value=String(cid);box.go();check('old complete '+cid+' remains complete',store.view.innerHTML.includes('状态 完整'));}
store.q.value='30236';box.go();check('101 baseline descriptions retained',store.view.innerHTML.includes('已有逐描述答案 101'));
check('all earlier template strengths retained',html.includes('p3b8_type11')&&html.includes('p3b7_type26_start_mana_exact_digit')&&html.includes('逐记录人工语义对应'));
store.q.value='not-a-real-cid';box.go();store.q.value='328';box.go();check('search recovers after missing query',store.view.innerHTML.includes('p3b9_type67_conditional_self_stats'));
const result={kind:'C actual HTML script VM/DOM fixture, not independent D or browser visual acceptance',passed:checks.filter(x=>x.passed).length,total:checks.length,checks};
fs.writeFileSync(out+'dom_validation.json',JSON.stringify(result,null,1)+'\n');fs.writeFileSync(out+'dom_snapshots.json',JSON.stringify(snapshots,null,1)+'\n');console.log(JSON.stringify({passed:result.passed,total:result.total,failed:checks.filter(x=>!x.passed).map(x=>x.name)}));process.exit(result.passed===result.total?0:1);
