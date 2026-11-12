/* Read frozen cards and the branch overlay; write only this audit's report. */
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),vm=require('node:vm');
const branches=require('./web/branches.js'),inline=require('./web/inline.js');
const {readPath}=require('./project_layout_paths.cjs');
const {freshReviewDirectory}=require('./review_output.cjs');
const logicalRoot=path.resolve(process.argv[2] || path.join(__dirname,'../../output/character_skills/reader_full_20261106'));
const root=readPath(logicalRoot);
const context={window:{}};
vm.runInNewContext(fs.readFileSync(path.join(root,'data/branch_candidates.js'),'utf8'),context);
const overlay=context.window.CC_BRANCH_CANDIDATES;
assert(overlay?.cards,'branch overlay exists');
const list=value=>Array.isArray(value) ? value : [];
const rows=card=>list(card.groups).flatMap(g=>list(g.skills).flatMap(s=>list(s.rows)));
const answers=row=>list(row.effects).flatMap(e=>list(e.answers)).concat(list(row.unboundAnswers));
const sourceKey=answer=>JSON.stringify(answer.source);
const stats={cards:0,overlayCards:0,additions:0,inlineCandidates:0,conditionLinks:0,cardUnmapped:0};
const failures=[];
for(const file of fs.readdirSync(path.join(root,'data/cards')).filter(f=>f.endsWith('.js'))){
 const text=fs.readFileSync(path.join(root,'data/cards',file),'utf8');
 const card=JSON.parse(text.split(']=')[1].trim().replace(/;$/,''));
 const before=JSON.stringify(card),entry=overlay.cards[String(card.cid)];
 const applied=branches.apply(card,entry);
 assert.equal(JSON.stringify(card),before,'frozen card stays immutable');
 assert.equal(JSON.stringify(applied.counts),JSON.stringify(card.counts),'ledger counts unchanged');
 stats.cards++;
 if(!entry)continue;
 stats.overlayCards++;
 assert.equal(JSON.stringify(applied.unmappedBranches),JSON.stringify(entry.unmappedBranches || []));
 stats.cardUnmapped+=list(applied.unmappedBranches).length;
 const originalRows=new Map(rows(card).map(row=>[row.id,row]));
 const appliedRows=new Map(rows(applied).map(row=>[row.id,row]));
 const merged=rows({...applied,groups:inline.mergeGroups(applied.groups).map(g=>({...g,skills:g.skills.map(inline.prepareSkill)}))});
 const displayed=new Map(merged.flatMap(row=>[row.id,...list(row.aliasIds)].map(id=>[id,row])));
 for(const [rowId,patch] of Object.entries(entry.rows || {})){
  const row=appliedRows.get(rowId),mergedRow=displayed.get(rowId);
  try {
   assert(row && mergedRow,'overlay row exists before and after merging');
   for(const link of list(patch.candidateLinks)){
    assert(displayed.has(link.targetRowId),'condition link target exists');stats.conditionLinks++;
   }
   for(const addition of list(patch.additions)){
    stats.additions++;
    const effect=row.effects.find(e=>e.id===addition.effectId);
    assert(effect,'candidate effect exists');
    assert.equal(effect.sourceStatus,originalRows.get(rowId).effects.find(e=>e.id===addition.effectId).status);
    const candidate=effect.answers.find(a=>a.branchCandidate && a.text===addition.answer.text && sourceKey(a)===sourceKey(addition.answer));
    assert(candidate,'candidate and complete source retained');
    assert.equal(candidate.text,addition.answer.text,'raw numeric display text is unchanged');
    assert(inline.candidate(candidate),'overlay always takes the purple branch candidate style');
    const plan=inline.plan(mergedRow);
    const insertion=plan.inserts.find(e=>(e.answers || [e.answer]).some(a=>a.branchCandidate && a.text===candidate.text && sourceKey(a)===sourceKey(candidate)));
    assert(insertion,'every added candidate has a safe inline anchor after merge');
    assert(insertion.branchCandidate,'inline insertion has branch styling');
    const sourceRecords=answers(mergedRow).concat(list(mergedRow.sourceRows).flatMap(answers));
    assert(sourceRecords.some(a=>sourceKey(a)===sourceKey(candidate)),'sources include overlay after merge');
    const segment=list(insertion.segments).find(s=>(s.answers || [s.answer]).some(a=>a.branchCandidate && a.text===candidate.text && sourceKey(a)===sourceKey(candidate)));
    const printed=segment ? segment.text : insertion.text;
    const numeric=inline.compact(candidate,effect.label);
    assert(numeric.endsWith(printed),'only a shared leading explanation may be omitted');
    const shared=numeric.slice(0,numeric.length-printed.length);
    assert(!/[\d+\-−]/.test(shared),'numbers and signs cannot be shared away');
    if(shared)assert(insertion.segments[0].text.startsWith(shared),'shared meaning remains on the first value');
    assert.deepEqual(printed.match(/[\d.]+|×C|%|秒|倍|百分点/g),numeric.match(/[\d.]+|×C|%|秒|倍|百分点/g),'numeric tokens, units and Chain factor survive rendering');
    assert(!/候选/.test(printed),'no repeated candidate labels inside prose');
    assert.match(plan.branchLabel,/待确认/,'each candidate sentence exposes uncertain conditions');
    stats.inlineCandidates++;
   }
  }catch(error){failures.push({cid:card.cid,rowId,message:error.message});}
 }
}
assert.equal(stats.cards,2236,'all frozen cards inspected');
assert(stats.additions>0,'overlay has added candidates');
const output=path.join(freshReviewDirectory('branch-ui'),'validation_ui.json');
const report={pass:failures.length===0,stats,failures,checks:['2236 frozen cards','overlay does not mutate cards or counts','all additions inline after profile merging','complete candidate source retained','purple candidate style','numeric text and Chain factor unchanged','condition links resolve','card-level unmapped records preserved']};
fs.writeFileSync(output,JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
assert.equal(failures.length,0,'branch UI validation failures; see '+output);
