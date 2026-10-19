// DOM fixture of the generated script, without browser visual acceptance.
const fs=require('fs'),vm=require('vm'),base='output/character_skills/',out=base+'description_bindings/p3b6_batch/';
const html=fs.readFileSync(base+'profiles/index.html','utf8'),src=html.match(/<script>([\s\S]*)<\/script>/)[1],store={};
const el=id=>({id,value:'',innerHTML:'',textContent:'',children:[],addEventListener(){},appendChild(c){this.children.push(c);}});
const box={document:{getElementById(id){return store[id]||(store[id]=el(id));},createElement:el},location:{hash:''},window:{addEventListener(){}},console,JSON,Math,String,Array,Map,Object,RegExp};
vm.createContext(box);vm.runInContext(src,box,{timeout:120000});
const rows=p=>fs.readFileSync(p,'utf8').trim().split('\n').map(JSON.parse),checks=[];
const check=(name,passed)=>checks.push({name,passed});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const recs=Object.fromEntries(rows(base+'profiles/records.jsonl').map(r=>[r.rec_key,r]));
check('embedded records equal generated records',vm.runInContext('JSON.stringify(RECS)',box)===JSON.stringify(recs));
for(const cid of [29,1233,8031,10032,2045,2058,5052,10039,58001]){
 store.q.value=String(cid);box.go();const h=store.view.innerHTML;
 const cli=rows(out+'bindings.jsonl').filter(r=>r.page_uses.some(p=>p.cid===cid));
 check('cid '+cid+' renders structural strength full conditions and existing formula',cli.length===1&&cli.every(r=>h.includes(esc(r.after.binding.strength))&&h.includes(esc(r.after.binding.condition))&&h.includes(esc(r.after.binding.limits))&&h.includes(esc(r.after.binding.fields[0].value)))&&h.includes('按类型套用'));
 if(cid===29)check('cid29 complete follows two real bindings while raw gaps remain',h.includes('状态 完整')&&h.includes('未解释字段 24')&&h.includes('type26_start_mana_3101')&&h.includes('已确认公式'));
}
store.q.value='30236';box.go();check('101 baseline still renders',store.view.innerHTML.includes('已有逐描述答案 101'));
store.q.value='8031';box.go();check('MP lore remains unexplained and does not make full role',store.view.innerHTML.includes('装備者の最大ＭＰを増やす効果がある')&&store.view.innerHTML.includes('状态 部分'));
check('old type8 and two old type26 strengths and templates remain',html.includes('battle_move_up')&&html.includes('type26_start_mana_3101')&&html.includes('type26_start_mana_3102')&&html.includes('逐记录人工语义对应'));
const result={kind:'DOM fixture; no browser visual acceptance',passed:checks.filter(r=>r.passed).length,total:checks.length,checks};
fs.writeFileSync(out+'dom_validation.json',JSON.stringify(result,null,1)+'\n');console.log(JSON.stringify(result));process.exit(result.passed===result.total?0:1);
