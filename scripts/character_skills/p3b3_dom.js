// Execute the generated page in a DOM fixture; not browser visual acceptance.
const fs=require('fs'),vm=require('vm');
const base='output/character_skills/',out=base+'type26_mana/';
const html=fs.readFileSync(base+'profiles/index.html','utf8');
const src=html.match(/<script>([\s\S]*)<\/script>/)[1],store={};
const el=id=>({id,value:'',innerHTML:'',textContent:'',children:[],addEventListener(){},appendChild(c){this.children.push(c);}});
const box={document:{getElementById(id){return store[id]||(store[id]=el(id));},createElement:el},location:{hash:''},window:{addEventListener(){}},console,JSON,Math,String,Array,Map,Object,RegExp};
vm.createContext(box);vm.runInContext(src,box,{timeout:120000});
const checks=[];
function check(name,passed){checks.push({name,passed});}
function render(cid){store.q.value=String(cid);box.go();return store.view.innerHTML;}
function rows(path){return fs.readFileSync(path,'utf8').trim().split('\n').map(JSON.parse);}
const ledger=rows(out+'bindings.jsonl');
let n=0,ok=true;
for(const r of ledger)for(const c of r.characters){
 const h=render(c.cid),b=r.fragment_after.binding;n++;
 ok&&=h.includes('已审定描述对应（原值／原生效果规则支持）')&&h.includes(b.template_id)&&
 h.includes('param0产线')&&h.includes('非继续战斗')&&h.includes('isHero=false')&&
 h.includes('_isActive非0')&&h.includes('开局一次授予')&&h.includes('按类型套用')&&
 b.fields.every(a=>h.includes(a.value));
}
check('all22 page references render values and native preconditions',n===22&&ok);
check('3101 and3102 preserve distinct raw-derived1and2 counts',ledger[0].fragment_after.binding.fields[0].value.includes('授予 1 个')&&ledger[1].fragment_after.binding.fields[0].value.includes('授予 2 个'));
const h=render(ledger[0].characters[0].cid);
check('param4 zero answer remains separate from positive param0',h.includes('param4 这条产线不产出追加玛那')&&h.includes('param0产线'));
const recs=Object.fromEntries(rows(base+'profiles/records.jsonl').map(r=>[r.rec_key,r]));
check('HTML embedded records equal JSON',vm.runInContext('JSON.stringify(RECS)',box)===JSON.stringify(recs));
check('type26 only two pinned records gain bindings',Object.values(recs).filter(r=>r.table==='skilllist'&&r.effect_type===26&&r.fragments.some(f=>f.binding)).length===2);
check('old101 baseline rendered',render(30236).includes('已有逐描述答案 101'));
check('type8 direction and old reviewed template rendered',render(5070).includes('移动速度×1.6（+60%）')&&render(5070).includes('battle_move_up'));
const cli=JSON.parse(fs.readFileSync(out+'cli_'+ledger[0].characters[0].cid+'_json.log','utf8'));
const cliRecord=cli.characters[0].materialised_records['skilllist|3101|APK|ability=26'];
check('CLI andDOM share binding and answer',JSON.stringify(cliRecord)===JSON.stringify(recs['skilllist|3101|APK|ability=26']));
const result={kind:'DOM fixture; browser connection to host local port timed out, no real browser visual claim',passed:checks.filter(x=>x.passed).length,total:checks.length,checks};
fs.writeFileSync(out+'dom_validation.json',JSON.stringify(result,null,1)+'\n');
console.log(JSON.stringify(result));process.exit(result.passed===result.total?0:1);
