/* Presentation audit: frozen data + provisional overlay, no mainline writes. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const inline=require('./web/inline'),branches=require('./web/branches');
const root=path.resolve(__dirname,'../../output/character_skills/reader_full_20261106');
const context={window:{}};
vm.runInNewContext(fs.readFileSync(path.join(root,'data/branch_candidates.js'),'utf8'),context);
const overlay=context.window.CC_BRANCH_CANDIDATES.cards;
const stats={cards:0,multiCards:0,multiSkills:0,multiEffects:0,mergedRepeatedValues:0};
const samples=[],inventory=[];
for(const file of fs.readdirSync(path.join(root,'data/cards')).filter(f=>f.endsWith('.js'))){
 const card=JSON.parse(fs.readFileSync(path.join(root,'data/cards',file),'utf8').split(']=')[1].trim().replace(/;$/,''));
 const applied=branches.apply(card,overlay[card.cid]);
 const original=JSON.stringify(applied);
 const groups=inline.orderGroups(inline.mergeGroups(applied.groups));
 const special=groups.findIndex(g=>g.label==='必杀技'),inherited=groups.findIndex(g=>g.label==='传授');
 if(special>=0 && inherited>=0)assert.equal(inherited,special+1,'传授 immediately follows 必杀技');
 stats.cards++;let multi=false;
 for(const group of groups)for(const old of group.skills){
  const skill=inline.prepareSkill(old);
  if(!skill.branchTable)continue;
  multi=true;stats.multiSkills++;
  const codes=new Map(skill.branchTable.map(b=>[b.key,b.code]));
  if(card.cid===20622){
   const reversed=inline.prepareSkill({...old,rows:old.rows.map(r=>({...r,effects:r.effects.map(e=>({...e,answers:[...e.answers].reverse()}))}))});
   assert.deepEqual(reversed.branchTable.map(b=>[b.key,b.code]),skill.branchTable.map(b=>[b.key,b.code]),'source identity ordering survives different per-effect answer order');
  }
  if(card.cid===20332)assert(skill.rows[1].knownCandidateScopes.includes('伤害'),'HP qualification links existing values instead of reporting missing damage');
  const outputs=[];
  for(const row of skill.rows){
   for(const insertion of inline.plan(row).inserts){
    if(!insertion.segments)continue;
    const sourceAnswers=insertion.answers || [insertion.answer];
    if(sourceAnswers.length>2)stats.multiEffects++;
    assert.equal(insertion.segments.flatMap(s=>s.answers).length,sourceAnswers.length,'grouped display retains all source answers');
    const unique=new Set();let last=-1;
    for(const segment of insertion.segments){
     const colors=new Set(segment.answers.map(a=>inline.candidate(a) ? 'branch-candidate' : a.confidence));
     assert.equal(colors.size,1,'never merge purple with gold or green');
     const texts=new Set(segment.answers.map(a=>inline.compact(a,insertion.effect.label)));
     assert.equal(texts.size,1,'never merge different values or units');
     const key=[...colors][0]+[...texts][0];assert(!unique.has(key),'same-value same-color displayed once');unique.add(key);
     const order=segment.branches.length ? Math.min(...segment.branches.map(b=>b.order)) : -1;
     assert(order>=last,'consistent branch order across every effect');last=order;
     for(const answer of segment.answers){
      if(!answer.displayBranch)continue;
      assert.equal(answer.displayBranch.code,codes.get(answer.displayBranch.key),'letter follows identity, not array position');
      assert(segment.branches.some(b=>b.key===answer.displayBranch.key),'all equal-value branch markers retained');
      const raw=answer.source?.conditionsRaw;
      if(raw)assert(answer.displayBranch.rawRecords.some(r=>JSON.stringify(r)===JSON.stringify(raw)),'full condition object remains unchanged');
     }
    }
    stats.mergedRepeatedValues+=sourceAnswers.length-insertion.segments.length;
    outputs.push({rowId:row.id,label:insertion.effect.label,values:insertion.segments.map(s=>({text:s.text,color:s.color,codes:s.branches.map(b=>b.code)}))});
   }
  }
  inventory.push({cid:card.cid,skill:skill.name,stage:skill.stage,branches:skill.branchTable.map(b=>({code:b.code,key:b.key,conditions:b.raw})),outputs});
  if([20332,20437,20622,30207].includes(card.cid))samples.push(inventory.at(-1));
 }
 if(multi)stats.multiCards++;
 assert.equal(JSON.stringify(applied),original,'preparation never changes input data');
 if(card.cid===10213){
  const attacks=groups[0].skills.map(s=>s.rows.flatMap(r=>r.effects.filter(e=>e.label==='攻击力' && e.answers.length>1).map(e=>e.answers.map(a=>inline.compact(a,e.label)))));
  assert(attacks.flat().some(values=>values[0].startsWith('+60%') && values[1].startsWith('+50%')),'lower-valued other branch is not reordered as stronger');
 }
}
assert.equal(stats.cards,2236);
const hp=samples.find(s=>s.cid===20332).outputs.find(o=>o.label==='伤害');
assert.equal(hp.values.length,4,'HP x Chain eight records share four displayed values');
assert(hp.values.every(v=>v.codes.length===2),'each HP value retains both Chain records');
assert.equal(samples.find(s=>s.cid===20437).outputs.find(o=>o.label==='伤害').values.length,1,'random barrier branches do not duplicate damage six times');
const mana=samples.find(s=>s.cid===30207);
assert(mana.branches.some(b=>b.conditions && !Object.hasOwn(b.conditions,'mns')),'absent mana threshold remains absent');
const report={pass:true,stats,samples,inventory};
const {freshReviewDirectory}=require('./review_output.cjs');
fs.writeFileSync(path.join(freshReviewDirectory('multi-branch'),'multi_branch_validation.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({pass:true,stats},null,2));
