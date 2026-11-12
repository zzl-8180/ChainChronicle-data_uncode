const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const inline=require('./web/inline'),branches=require('./web/branches');
const out=path.resolve(__dirname,'../../output/character_skills/reader_full_20261106'),audit=path.join(out,'audit/trigger_evidence_20261107');
const receipt=JSON.parse(fs.readFileSync(path.join(audit,'branch_invariance_receipt.json'))),review=JSON.parse(fs.readFileSync(path.join(audit,'inventory.json')));
assert.equal(receipt.items.length,59);assert.equal(receipt.stats.accepted,14);
for(const i of receipt.items){
 const match=review.items.find(v=>v.rowId===i.rowId && v.source.branchId===i.source.branchId && v.source.rule===i.source.rule);
 assert(match);
 if(i.branchInvariant){assert.equal(match.review.status,'inferred');assert.equal(match.review.conditionKnown,false);assert.equal(match.review.branchInvariant,true);assert.equal(i.carriers.length,i.allCohortParents.length);}
 else assert.equal(match.review.status,'purple','excluded attachment or changing value must retain uncertainty');
}
assert(receipt.items.some(i=>i.cid===1300 && !i.branchInvariant && i.reasonCodes.includes('OTHER_EXECUTOR_REQUIRES_ASSOCIATION_REVIEW')));
const context={window:{}};
for(const name of ['branch_candidates','branch_conditions','branch_assessments'])vm.runInNewContext(fs.readFileSync(path.join(out,`data/${name}.js`),'utf8'),context);
const data=JSON.parse(JSON.stringify(context.window));
for(const cid of [11228,20612]){
 const card=JSON.parse(fs.readFileSync(path.join(out,`data/cards/${cid}.js`),'utf8').split(']=')[1].trim().slice(0,-1));
 const skill=inline.prepareSkill(inline.mergeGroups(branches.apply(card,data.CC_BRANCH_CANDIDATES.cards[cid]).groups)[0].skills[0],data.CC_BRANCH_CONDITIONS.records,data.CC_BRANCH_ASSESSMENTS.records);
 const segments=skill.rows.flatMap(r=>inline.plan(r).inserts.flatMap(i=>i.segments||[]));
 if(cid===11228)assert(segments.some(v=>v.conditionLabel==='各分支相同' && v.color==='inferred' && v.conditionKnown));
 else assert(segments.some(v=>v.conditionLabel==='1stChain以上' && v.color==='inferred'));
}
console.log('PASS: 59 cases, 14 constant inputs vs 45 exclusions; known-equivalent Chain and invariant wording');
