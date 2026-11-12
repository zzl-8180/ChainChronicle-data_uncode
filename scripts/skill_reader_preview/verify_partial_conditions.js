const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const inline=require('./web/inline'),branches=require('./web/branches');
const out=path.resolve(__dirname,'../../output/character_skills/reader_full_20261106'),audit=path.join(out,'audit/trigger45_evidence_20261107');
const json=f=>JSON.parse(fs.readFileSync(f,'utf8'));
const current=path.join(out,'audit/selection_order_20261107/inventory.json');
const receipt=json(path.join(audit,'partial_conditions_receipt.json')),inv=json(fs.existsSync(current)?current:path.join(audit,'inventory.json'));
assert.equal(receipt.items.length,45);assert.equal(receipt.stats.partialItems,20);
const context={window:{}};for(const n of ['branch_candidates','branch_conditions','branch_assessments'])vm.runInNewContext(fs.readFileSync(path.join(out,`data/${n}.js`),'utf8'),context);
const data=JSON.parse(JSON.stringify(context.window));let labels=0;
for(const item of receipt.items){
 const found=inv.items.find(v=>v.rowId===item.rowId && v.source.branchId===item.source.branchId && v.source.rule===item.source.rule);
 assert(found);
 if(found.review.selectionResolved){assert(found.review.conditionKnown);if(item.partialCondition)labels++;continue;}
 assert.equal(found.review.status,'purple');assert.equal(found.review.conditionKnown,false,'necessary condition alone never claims complete selection');
 if(!item.partialCondition)continue;
 assert.equal(found.review.partialCondition,item.partialCondition);
 const card=JSON.parse(fs.readFileSync(path.join(out,`data/cards/${item.cid}.js`),'utf8').split(']=')[1].trim().slice(0,-1));
 const skills=inline.mergeGroups(branches.apply(card,data.CC_BRANCH_CANDIDATES.cards[item.cid]).groups).flatMap(g=>g.skills).map(s=>inline.prepareSkill(s,data.CC_BRANCH_CONDITIONS.records,data.CC_BRANCH_ASSESSMENTS.records));
 const row=skills.flatMap(s=>s.rows).find(r=>r.id===item.rowId);
 const segment=inline.plan(row).inserts.flatMap(i=>i.segments||[]).find(s=>s.answers.some(a=>a.source.branchId===item.source.branchId && a.source.rule===item.source.rule));
 assert(segment?.conditionPartial && !segment.conditionKnown && segment.color==='branch-candidate','known necessary condition is visible while value remains purple');labels++;
 if(item.necessaryConditions.includes('PER_PATTERN_USE_COUNT_UPPER_BOUND'))assert(!/第[123一二三]次|以后/.test(segment.conditionLabel));
 if(item.parentRaw.bgf===8192)assert(segment.conditionLabel.includes('夜间'));
 if(item.parentRaw.bgf===1114112)assert(segment.conditionLabel.includes('沙滩'));
}
assert.equal(labels,20);console.log('PASS: 45 covered; necessary gates retain purple unless superseded by full selection proof');
