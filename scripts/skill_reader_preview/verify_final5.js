const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const inline=require('./web/inline'),branches=require('./web/branches');
const out=path.resolve(__dirname,'../../output/character_skills/reader_full_20261106'),audit=path.join(out,'audit/final5_evidence_20261107');
const json=f=>JSON.parse(fs.readFileSync(f,'utf8'));
const prior=json(path.join(out,'audit/selection_order_20261107/selection_receipt.json'));
const inv=json(path.join(audit,'inventory.json')),sparse=json(path.join(audit,'sparse_receipt.json')),random=json(path.join(audit,'random_pool_receipt.json'));
const oldFive=prior.items.filter(i=>!i.selectionResolved);assert.equal(oldFive.length,5);let resolved=0;
for(const item of oldFive){
 const value=inv.items.find(x=>x.rowId===item.rowId && x.source.branchId===item.branchId && x.source.rule===item.source.rule);assert(value);
 if(item.cid===278){assert.equal(value.review.status,'purple');assert(value.review.randomPoolKnown && !value.review.cardFaceMappingKnown);}
 else{assert.equal(value.review.status,'inferred');assert(value.review.selectionResolved && value.review.conditionKnown);resolved++;}
}
assert.equal(resolved,3);assert.equal(Object.keys(sparse.parents).length,4);
assert(sparse.parents['CACHE:41223602'].selectionUnavailable);
assert(!sparse.parents['CACHE:41223605'].selectionUnavailable);
assert(sparse.items[0].sourceParents.every(p=>p.raw.hpend===100),'both actual bounds exist; do not revive the old missing-hpend diagnosis');
assert(sparse.negativeTests.some(t=>t.includes('Missing hpend')));
assert.equal(random.completeParents.length,4);assert.equal(random.randomIntervals.length,3);
assert.equal(random.integerIntervalCheck.rollsChecked,300);assert.equal(random.items.length,2);
assert.deepEqual(random.randomIntervals.map(x=>x.minInclusive),[0,100,200]);
assert(random.openGaps.some(g=>g.topic==='Parent to visible card-face mapping'));
const ctx={window:{}};for(const n of ['branch_candidates','branch_conditions','branch_assessments'])vm.runInNewContext(fs.readFileSync(path.join(out,`data/${n}.js`),'utf8'),ctx);
const data=JSON.parse(JSON.stringify(ctx.window)),samples={};
for(const cid of [278,12236,5300]){
 const card=JSON.parse(fs.readFileSync(path.join(out,`data/cards/${cid}.js`),'utf8').split(']=')[1].trim().slice(0,-1));
 samples[cid]=inline.mergeGroups(branches.apply(card,data.CC_BRANCH_CANDIDATES.cards[cid]).groups).flatMap(g=>g.skills).map(s=>inline.prepareSkill(s,data.CC_BRANCH_CONDITIONS.records,data.CC_BRANCH_ASSESSMENTS.records)).flatMap(s=>s.rows.flatMap(r=>inline.plan(r).inserts.flatMap(i=>i.segments||[])));
}
assert(samples[278].some(s=>s.color==='branch-candidate'));
assert(samples[12236].some(s=>s.conditionLabel.includes('当前选档') && s.color==='inferred'));
assert(samples[12236].some(s=>s.answers.some(a=>a.displayAssessment?.selectionUnavailable)),'unused old source is retained');
assert(samples[5300].some(s=>s.conditionLabel.includes('森林') && s.color==='inferred'));
const report={pass:true,targets:5,resolved:3,retained:2,stats:inv.stats,checks:['complete four-parent random pool, not two-number probability','no invented card face or DOWN-bit mapping','fresh primary JSON and whole-record AB fallback scope','hpend100 is explicit, not inferred default','joint forest/count history and controller lifetime','unused old selection explicitly retained']};
const {freshReviewDirectory}=require('./review_output.cjs');
fs.writeFileSync(path.join(freshReviewDirectory('final5'),'final5_validation.json'),JSON.stringify(report,null,2));
console.log('PASS: final five: three selector conclusions, two card-face gaps retained, source identities and visible labels');
