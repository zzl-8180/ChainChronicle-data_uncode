// Generated-page DOM fixture; no actual browser visual acceptance claim.
const fs=require('fs'),vm=require('vm'),base='output/character_skills/',out=base+'remaining_five/';
const html=fs.readFileSync(base+'profiles/index.html','utf8'),src=html.match(/<script>([\s\S]*)<\/script>/)[1],store={};
const el=id=>({id,value:'',innerHTML:'',textContent:'',children:[],addEventListener(){},appendChild(c){this.children.push(c);}});
const box={document:{getElementById(id){return store[id]||(store[id]=el(id));},createElement:el},location:{hash:''},window:{addEventListener(){}},console,JSON,Math,String,Array,Map,Object,RegExp};
vm.createContext(box);vm.runInContext(src,box,{timeout:120000});
const rows=p=>fs.readFileSync(p,'utf8').trim().split('\n').map(JSON.parse),checks=[];
const check=(name,passed)=>checks.push({name,passed});
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const recs=Object.fromEntries(rows(base+'profiles/records.jsonl').map(r=>[r.rec_key,r]));
check('embedded records exactly equal generated records',vm.runInContext('JSON.stringify(RECS)',box)===JSON.stringify(recs));
for(const cid of [4009,4049,8116,10018,8151]){
 store.q.value=String(cid);box.go();const h=store.view.innerHTML;
 const cli=JSON.parse(fs.readFileSync(out+'cli_'+cid+'_json.log','utf8')).characters[0];
 const newa=Object.values(cli.materialised_records).flatMap(r=>[r,...r.children]).flatMap(r=>r.answers).filter(a=>/^bossskill\|(24|56|68|73)\|/.test(a.rule_key));
 check('cid '+cid+' renders new values conditions and type scope',newa.length>0&&newa.every(a=>h.includes(esc(a.value))&&h.includes(esc(a.note)))&&h.includes('按类型套用'));
}
store.q.value='30236';box.go();check('101 baseline still renders',store.view.innerHTML.includes('已有逐描述答案 101'));
store.q.value='8151';box.go();check('F1 entry threshold and same-loop cooldown boundary render',store.view.innerHTML.includes('候选遍历入口正次数门槛')&&store.view.innerHTML.includes('非正冷却同轮可越过')&&store.view.innerHTML.includes('正值停止本轮继续遍历'));
check('old type8 and type26 binding templates remain',html.includes('battle_move_up')&&html.includes('type26_start_mana_3101'));
const result={kind:'DOM fixture; no browser visual acceptance',passed:checks.filter(r=>r.passed).length,total:checks.length,checks};
fs.writeFileSync(out+'dom_validation.json',JSON.stringify(result,null,1)+'\n');console.log(JSON.stringify(result));process.exit(result.passed===result.total?0:1);
