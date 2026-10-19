// Generated-page DOM fixture; no browser visual claim.
const fs=require('fs'),vm=require('vm'),base='output/character_skills/',out=base+'type9_crit/';
const html=fs.readFileSync(base+'profiles/index.html','utf8'),src=html.match(/<script>([\s\S]*)<\/script>/)[1],store={};
const el=id=>({id,value:'',innerHTML:'',textContent:'',children:[],addEventListener(){},appendChild(c){this.children.push(c);}});
const box={document:{getElementById(id){return store[id]||(store[id]=el(id));},createElement:el},location:{hash:''},window:{addEventListener(){}},console,JSON,Math,String,Array,Map,Object,RegExp};
vm.createContext(box);vm.runInContext(src,box,{timeout:120000});
const rows=p=>fs.readFileSync(p,'utf8').trim().split('\n').map(JSON.parse),checks=[];
const check=(name,passed)=>checks.push({name,passed});
const recs=Object.fromEntries(rows(base+'profiles/records.jsonl').map(r=>[r.rec_key,r]));
const ledger=rows(out+'field_answers.jsonl');
check('HTML embedded records equal generated JSON',vm.runInContext('JSON.stringify(RECS)',box)===JSON.stringify(recs));
const samples=[];
for(const kind of ['zero','neutral','decrease','increase']){
 const r=ledger.find(r=>{const v=r.answers[0].raw;return kind==='zero'?v===0:kind==='neutral'?v===1:kind==='decrease'?v>0&&v<1:v>1;});
 const cid=r.page_references[0].cid;store.q.value=String(cid);box.go();const h=store.view.innerHTML;
 samples.push({kind,cid,passed:h.includes(r.answers[0].value)&&h.includes('首次命中先用当前伤害输入')&&h.includes('SHOT_THROUGH')&&h.includes('bCheckAbility=true')&&h.includes('按类型套用')});
}
check('zero neutral attenuation increase render distinct values and gates',samples.length===4&&samples.every(r=>r.passed));
check('new answers are coefficients without probability labels',ledger.every(r=>r.answers.every(a=>a.unit==='无量纲系数（非概率/百分点）'&&!a.value.includes('暴击')&&a.scope==='BY_TYPE_EXTRAPOLATED')));
store.q.value='30236';box.go();check('old101 baseline renders',store.view.innerHTML.includes('已有逐描述答案 101'));
const cli=JSON.parse(fs.readFileSync(out+'cli_'+ledger.reduce((s,r)=>Math.min(s,...r.page_references.map(p=>p.cid)),Infinity)+'_json.log','utf8'));
check('CLI records equal DOM shared records',Object.entries(cli.characters[0].materialised_records).every(([k,v])=>JSON.stringify(v)===JSON.stringify(recs[k])));
check('old type8 and type26 binding templates remain embedded',html.includes('battle_move_up')&&html.includes('type26_start_mana_3101'));
const result={kind:'DOM fixture; no actual browser visual acceptance',passed:checks.filter(r=>r.passed).length,total:checks.length,checks,samples};
fs.writeFileSync(out+'dom_validation.json',JSON.stringify(result,null,1)+'\n');console.log(JSON.stringify(result));process.exit(result.passed===result.total?0:1);
