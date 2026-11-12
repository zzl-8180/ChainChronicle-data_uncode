const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const inline=require('./web/inline'),branches=require('./web/branches'),levels=require('./web/levels');
const root=path.resolve(process.argv[2] || path.join(__dirname,'../../output/character_skills/reader_full_20261106')),ctx={window:{}};
const explicitReport=process.argv[3]&&path.resolve(root,process.argv[3]);
if(explicitReport&&fs.lstatSync(explicitReport,{throwIfNoEntry:false}))throw new Error('Choose a new validation receipt: '+explicitReport);
for(const name of ['branch_candidates','branch_conditions','branch_assessments'])vm.runInNewContext(fs.readFileSync(path.join(root,`data/${name}.js`),'utf8'),ctx);
const data=JSON.parse(JSON.stringify(ctx.window));
const reviews=data.CC_BRANCH_ASSESSMENTS,seen=new Set(),stats={cards:0,reviewed:0,inferred:0,purple:0},samples={};
for(const [name,digest] of Object.entries(reviews.inputHashes))assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(root,`data/${name}.js`))).digest('hex'),digest);
for(const file of fs.readdirSync(path.join(root,'data/cards')).filter(f=>f.endsWith('.js'))){
 const card=JSON.parse(fs.readFileSync(path.join(root,'data/cards',file),'utf8').split(']=')[1].trim().replace(/;$/,''));
 const before=JSON.stringify(card),applied=branches.apply(card,data.CC_BRANCH_CANDIDATES.cards[card.cid]);stats.cards++;
 for(const group of inline.mergeGroups(applied.groups))for(const raw of levels.groupSkills(group)){
  const old=inline.prepareSkill(raw,data.CC_BRANCH_CONDITIONS.records),reviewed=inline.prepareSkill(raw,data.CC_BRANCH_CONDITIONS.records,reviews.records,reviews.resolvedParents);
  for(const entry of reviewed.branchTable || []){
   const selector=reviews.resolvedParents?.[entry.key];
   if(!selector)continue;
   assert.deepEqual(entry.raw,selector.parentRaw,'condition overlay uses the exact full parent');
   assert(entry.conditionKnown,'known condition also reaches original values');
   assert.equal(entry.conditionLabel,selector.selectionUnavailable?'本模式常规选档不选用':selector.conditionLabel);
  }
  if(card.cid===10213 && reviewed.branchTable?.some(e=>e.key==='CACHE:41021301')){
   const entry=reviewed.branchTable.find(e=>e.key==='CACHE:41021301');
   assert.equal(entry.conditionLabel,'使用后强化1次（最大）');
   assert(!inline.plan(reviewed.rows.find(r=>r.effects.some(e=>e.label==='攻击力'))).inserts.some(i=>i.segments?.some(s=>!s.conditionKnown)),'no stale letter on known usage branch');
  }
  for(let r=0;r<old.rows.length;r++){
   const previous=old.rows[r],row=reviewed.rows[r],plan=inline.plan(row);
   for(let e=0;e<previous.effects.length;e++)for(let a=0;a<previous.effects[e].answers.length;a++){
    const original=previous.effects[e].answers[a],answer=row.effects[e].answers[a];
    assert.equal(answer.text,original.text);assert.equal(answer.confidence,original.confidence);assert.deepEqual(answer.source,original.source,'underlying evidence never rewritten');
    if(!inline.candidate(original))continue;
    const key=inline.reviewKey(previous,previous.effects[e],original),review=reviews.records[key];assert(review,'every displayed purple answer assessed');seen.add(key);stats.reviewed++;
    assert.equal(inline.candidate(answer),review.status!=='inferred');stats[review.status==='inferred'?'inferred':'purple']++;
    if(review.status==='inferred'){
     assert(review.numericKnown && review.bindingKnown && (review.conditionKnown || review.branchInvariant),'effect and value proven, with known condition or complete invariant branch coverage');
     const insert=plan.inserts.find(i=>(i.answers || [i.answer]).includes(answer));
     assert(insert,'reclassified value remains inside description');
     const segment=insert.segments?.find(s=>s.answers.includes(answer));
     assert(!segment || segment.color===answer.confidence,'resolved uses existing confidence color');
    }else assert(review.shortReason,'uncertainty has a specific reason');
    (samples[card.cid] ||= []).push({label:previous.effects[e].label,text:answer.text,review});
   }
  }
 }
 assert.equal(JSON.stringify(card),before,'original card stays immutable');
}
assert.equal(seen.size,Object.keys(reviews.records).length,'no unused or missing assessment entries');assert.equal(stats.cards,2236);
assert.equal(stats.inferred,reviews.stats.inferred);assert.equal(stats.purple,reviews.stats.purple);
assert(samples[350].filter(v=>['伤害系数 25倍','伤害系数 27.5倍'].includes(v.text)).every(v=>v.review.status==='inferred'));
assert(samples[20622].filter(v=>['攻击力','防御','移动速度'].includes(v.label)).every(v=>v.review.status==='inferred'));
const hpDamage=samples[20332].filter(v=>v.label==='伤害');
assert.equal(hpDamage.length,8);
assert(hpDamage.every(v=>v.review.status==='inferred' && v.review.bindingKind==='hp_first_enemy_area' && v.review.valuePrefix==='对敌系数' && v.review.unresolvedScope.includes('自身')));
for(const cid of [10215,30314])assert(samples[cid].filter(v=>v.review.bindingKind==='explicit_heal_binding').every(v=>v.review.bindingKnown));
assert(samples[7251].some(v=>v.review.bindingKind==='unique_record_binding' && !v.review.bindingKnown && v.review.status==='purple'));
assert(samples[1303].filter(v=>v.review.bindingKind==='count_scaling').every(v=>v.review.status==='purple' && v.review.shortReason==='逐人增长方式待确认'));
assert(samples[30310].filter(v=>v.text.startsWith('回复输入系数')).every(v=>v.review.status==='purple' && v.review.shortReason.includes('回复数值')));
assert.equal(Object.values(samples).flat().filter(v=>v.review.bindingKind==='own_record_duration' && v.review.status==='inferred').length,45);
const report={pass:true,stats,checks:['all frozen cards and displayed candidates','three separate evidence axes','no promotion to green','no source/number mutations','resolved candidates stay inline','fallback/count/record-ambiguity counterexamples','actual executor and prose despite absent old donor','self damage kept separate from enemy area coefficient','legacy denju parent lookup'],samples:Object.fromEntries([350,20622,20332,7251,1303,30310,30236,30255,10215,30314,12238].map(cid=>[cid,samples[cid]]))};
const {freshReviewDirectory}=require('./review_output.cjs');
const output=explicitReport || path.join(freshReviewDirectory('confidence'),'validation.json');
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(report,null,2),{flag:'wx'});console.log(JSON.stringify({pass:true,stats},null,2));
