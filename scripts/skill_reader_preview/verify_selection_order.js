const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const inline=require('./web/inline'),branches=require('./web/branches');
const out=path.resolve(__dirname,'../../output/character_skills/reader_full_20261106'),audit=path.join(out,'audit/selection_order_20261107');
const json=f=>JSON.parse(fs.readFileSync(f,'utf8'));
const receipt=json(path.join(audit,'selection_receipt.json')),inv=json(path.join(audit,'inventory.json'));
assert.equal(receipt.stats.denominator,45);assert.equal(receipt.stats.selectionResolved,40);
for(const item of receipt.items){
 const found=inv.items.find(v=>v.rowId===item.rowId && v.source.branchId===item.source.branchId && v.source.rule===item.source.rule);
 assert(found);assert.equal(found.review.status,item.selectionResolved?'inferred':'purple');
 if(item.selectionResolved)assert(found.review.conditionKnown && found.review.selectionResolved);
}
for(const [key,item] of Object.entries(receipt.parents)){
 assert.equal(item.conditionLabel,item.selectionLabel);assert(!item.source && item.triggerSource,'parent selection identity does not reuse another numeric source');
 assert.equal(String(item.parentRaw.patternid),key.split(':')[1]);
 assert(item.probes.length && item.characterSource.patternReferencesInNativeOrder.length>=item.cohort.orderedParents.length);
}
const context={window:{}};for(const n of ['branch_candidates','branch_conditions','branch_assessments'])vm.runInNewContext(fs.readFileSync(path.join(out,`data/${n}.js`),'utf8'),context);
const data=JSON.parse(JSON.stringify(context.window));let outputs={};
for(const cid of [2046,20716,12226,7654]){
 const card=JSON.parse(fs.readFileSync(path.join(out,`data/cards/${cid}.js`),'utf8').split(']=')[1].trim().slice(0,-1));
 const skill=inline.prepareSkill(inline.mergeGroups(branches.apply(card,data.CC_BRANCH_CANDIDATES.cards[cid]).groups)[0].skills[0],data.CC_BRANCH_CONDITIONS.records,data.CC_BRANCH_ASSESSMENTS.records);
 outputs[cid]=skill.rows.flatMap(row=>inline.plan(row).inserts.flatMap(i=>(i.segments||[]).map(s=>({text:s.text,condition:s.conditionLabel,color:s.color}))));
 assert(outputs[cid].some(s=>s.color==='inferred' && s.condition));
}
assert(outputs[2046].some(s=>s.condition==='初始'));assert(outputs[2046].some(s=>s.condition==='使用后强化2次（最大）'));
assert(outputs[20716].some(s=>s.condition==='夜间'));assert(outputs[20716].some(s=>s.condition==='非夜间'));
assert(outputs[12226].some(s=>s.condition==='选档时废料3–12个'));
assert(outputs[7654].some(s=>s.condition==='预测扣费后职业法珠0–2颗'));assert(!outputs[7654].some(s=>/发动前/.test(s.condition)));
const report={pass:true,scope:'40 of 45 selector conditions, actual complete cohorts and inline display; no live game validation',stats:receipt.stats,outputs};
const {freshReviewDirectory}=require('./review_output.cjs');
fs.writeFileSync(path.join(freshReviewDirectory('selection-order'),'selection_validation.json'),JSON.stringify(report,null,2));
console.log('PASS: 40/45 selection conditions; full parent identities, use stages, terrain, preview resource ranges; 5 retained');
