// Actual generated HTML script in controlled DOM interfaces; no browser visual claim.
const fs=require('fs'),vm=require('vm'),base='output/character_skills/',out=base+'description_bindings/p3b10_batch/';
const rows=p=>fs.readFileSync(p,'utf8').trim().split('\n').map(JSON.parse),store={};
const html=fs.readFileSync(base+'profiles/index.html','utf8'),src=html.match(/<script>([\s\S]*)<\/script>/)[1];
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
 check('cid '+cid+' whole sentence all target values and complete visible condition',h.includes(esc(item.after.t))&&b.fields.every(f=>h.includes(esc(f.value))&&h.includes(esc(f.unit)))&&h.includes(esc(b.condition))&&h.includes(esc(b.strength))&&h.includes(esc(b.limits))&&h.includes(esc(b.source.record_key))&&h.includes('按类型套用'));
 if(item.subgroup==='DECLARED_WEAPON_TYPE_MISSING_3'){
  const wid=b.declared_weapon_evidence[0].weapons[0].value;
  check('cid '+cid+' missing weapon type visible with native threshold2 and no unconditional other>=1',h.includes('主weaponid='+wid)&&h.includes('weaponlist行缺type')&&h.includes('无法从声明数据确认自身能否计入N')&&h.includes('N&gt;=int(param0)=2')&&h.includes('不无条件换述其他&gt;=1')&&h.includes('不据名称/外观/缺失默认0推武器类型'));
 }
 if(cid===214)check('cid214 bow declaration never assumed sword/self eligible',b.declared_weapon_evidence[0].weapons[0].rows[0].type_value===3&&h.includes('0x400000')&&h.includes('不保证声明武器一定匹配筛选'));
 snapshots.push({cid,record_id:item.record_id,subgroup:item.subgroup,visible_condition:b.condition,fields:b.fields});
}
check('old missing-holder-job 6203 stays excluded',Object.values(recs).find(r=>r.table==='skilllist'&&r.record_id===30620310).fragments.every(f=>!f.binding));
for(const cid of [29,2020,5023]){store.q.value=String(cid);box.go();check('old complete '+cid+' still complete',store.view.innerHTML.includes('状态 完整'));}
store.q.value='30236';box.go();check('101 baseline answers retained',store.view.innerHTML.includes('已有逐描述答案 101'));
store.q.value='not-a-real-cid';box.go();store.q.value='8294';box.go();check('search recovers after no result',store.view.innerHTML.includes('p3b10_type67_weapon_or_job_self_stats'));
const result={kind:'C actual generated HTML script VM/DOM interfaces, not D or real-browser visual acceptance',passed:checks.filter(x=>x.passed).length,total:checks.length,checks};
fs.writeFileSync(out+'dom_validation.json',JSON.stringify(result,null,1)+'\n');fs.writeFileSync(out+'dom_snapshots.json',JSON.stringify(snapshots,null,1)+'\n');console.log(JSON.stringify({passed:result.passed,total:result.total,failed:checks.filter(x=>!x.passed).map(x=>x.name)}));process.exit(result.passed===result.total?0:1);
