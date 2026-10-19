// Generated-page DOM fixture; this is not browser or visual acceptance.
const fs=require('fs'),vm=require('vm'),base='output/character_skills/',out=base+'description_bindings/p3b7_batch/';
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
 const cid=item.page_uses[0].cid,b=item.after.binding;store.q.value=String(cid);box.go();const h=store.view.innerHTML;
 check('cid '+cid+' whole sentence numeric scope source conditions and limits',h.includes(esc(item.after.t))&&h.includes(esc(b.fields[0].value))&&h.includes(esc(b.strength))&&h.includes(esc(b.condition))&&h.includes(esc(b.limits))&&h.includes(esc(b.source.record_key))&&h.includes('按类型套用'));
 const unknown=recs[item.rec_key].fragments.filter(f=>!f.binding&&f.status!=='BASELINE_DESCRIPTION_ANSWER');
 check('cid '+cid+' all other original fragments remain visible',unknown.every(f=>h.includes(esc(f.t))));
 snapshots.push({cid,record_id:item.record_id,binding:b.template_id,other_fragments:unknown.length});
}
store.q.value='29';box.go();check('old complete29 and raw unknown gaps preserved',store.view.innerHTML.includes('状态 完整')&&store.view.innerHTML.includes('未解释字段 24')&&store.view.innerHTML.includes('type26_start_mana_3101'));
store.q.value='30236';box.go();check('baseline101 preserved',store.view.innerHTML.includes('已有逐描述答案 101'));
store.q.value='8031';box.go();check('old B6 lore still unknown and partial',store.view.innerHTML.includes('装備者の最大ＭＰを増やす効果がある')&&store.view.innerHTML.includes('状态 部分'));
check('old type8 and B6 template strengths retained',html.includes('battle_move_up')&&html.includes('p3b6_type26_start_mana_digit')&&html.includes('逐记录人工语义对应'));
const result={kind:'DOM fixture; not browser visual acceptance',passed:checks.filter(c=>c.passed).length,total:checks.length,checks};
fs.writeFileSync(out+'dom_validation.json',JSON.stringify(result,null,1)+'\n');fs.writeFileSync(out+'dom_snapshots.json',JSON.stringify(snapshots,null,1)+'\n');console.log(JSON.stringify({passed:result.passed,total:result.total}));process.exit(result.passed===result.total?0:1);
