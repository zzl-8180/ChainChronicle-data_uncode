/* Audit player-facing condition labels against frozen cards and parent records.
 * Writes only audit/player_conditions_20261107/validation.json.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const inline=require('./web/inline'),branches=require('./web/branches');
const root=path.resolve(process.argv[2] || path.join(__dirname,'../../output/character_skills/reader_full_20261106'));
const context={window:{}};
for(const name of ['branch_candidates','branch_conditions'])vm.runInNewContext(fs.readFileSync(path.join(root,`data/${name}.js`),'utf8'),context);
const overlay=context.window.CC_BRANCH_CANDIDATES.cards,records=context.window.CC_BRANCH_CONDITIONS.records;
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const plain=value=>JSON.parse(JSON.stringify(value));
const answerCore=answer=>{const copy={...answer};delete copy.displayBranch;return copy;};
const stats={cards:0,conditionSkills:0,conditionCards:0,branchRecords:0,knownBranches:0,unknownBranches:0,varyingFlagSkills:0,sourceAnswers:0,inlineGroups:0,sharedOrderRows:0,mergedAnswers:0};
const failures=[],samples=[];
const check=(label,fn)=>{try{fn();}catch(error){failures.push({label,message:error.message});}};
const overlayBefore=JSON.stringify(overlay),recordsBefore=JSON.stringify(records);
for(const file of fs.readdirSync(path.join(root,'data/cards')).filter(f=>f.endsWith('.js'))){
 const card=JSON.parse(fs.readFileSync(path.join(root,'data/cards',file),'utf8').split(']=')[1].trim().replace(/;$/,''));
 const frozenBefore=JSON.stringify(card),applied=branches.apply(card,overlay[card.cid]);
 const appliedBefore=JSON.stringify(applied);let hasConditions=false;
 stats.cards++;
 for(const group of inline.mergeGroups(applied.groups))for(const old of group.skills){
  const before=JSON.stringify(old),skill=inline.prepareSkill(old,records);
  check(`${card.cid}: input skill immutable`,()=>assert.equal(JSON.stringify(old),before));
  if(!skill.branchTable)continue;
  hasConditions=true;stats.conditionSkills++;
  const branchByKey=new Map(skill.branchTable.map(b=>[b.key,b]));
  const flagValues=new Set(skill.branchTable.map(b=>b.raw?.flag ?? 0));
  if(flagValues.size>1){stats.varyingFlagSkills++;check(`${card.cid}: varying flags cannot be fully labelled`,()=>assert(skill.branchTable.every(b=>!b.conditionKnown)));}
  stats.branchRecords+=skill.branchTable.length;
  const reversed=inline.prepareSkill({...old,rows:old.rows.map(r=>({...r,effects:r.effects.map(e=>({...e,answers:[...e.answers].reverse()}))}))},records);
  check(`${card.cid}: identity order survives per-effect reversal`,()=>assert.deepEqual(reversed.branchTable.map(b=>[b.key,b.order,b.conditionLabel,b.conditionKnown]),skill.branchTable.map(b=>[b.key,b.order,b.conditionLabel,b.conditionKnown])));
  for(const entry of skill.branchTable){
   stats[entry.conditionKnown?'knownBranches':'unknownBranches']++;
   check(`${card.cid}:${entry.key}: primary parent retained`,()=>{
    assert(records[entry.key],'parent must resolve in exact layer');
    assert.equal(JSON.stringify(entry.raw),JSON.stringify(records[entry.key].raw));
    assert.equal(JSON.stringify(entry.conditionSource),JSON.stringify(records[entry.key].source));
   });
  }
  const outputs=[];
  skill.rows.forEach((row,ri)=>{
   const oldRow=old.rows[ri];
   row.effects.forEach((effect,ei)=>{
    const previous=oldRow.effects[ei];stats.sourceAnswers+=effect.answers.length;
    check(`${card.cid}:${row.id}:${effect.label}: sources/confidence unchanged`,()=>{
     assert.equal(effect.answers.length,previous.answers.length);
     effect.answers.forEach((answer,ai)=>{
      assert.deepEqual(answerCore(answer),answerCore(previous.answers[ai]));
      assert.equal(inline.candidate(answer),inline.candidate(previous.answers[ai]),'condition knowledge never promotes candidate color');
      if(answer.displayBranch)assert.equal(answer.displayBranch,branchByKey.get(answer.displayBranch.key));
     });
    });
   });
   const plan=inline.plan(row);
   if(plan.valueOrder){
    stats.sharedOrderRows++;
    check(`${card.cid}:${row.id}: one shared condition order describes every inline effect`,()=>{
     for(const insertion of plan.inserts.filter(i=>i.segments))assert.deepEqual(insertion.segments.map(s=>s.conditionLabel),plan.valueOrder);
    });
   }
   for(const insertion of plan.inserts){
    if(!insertion.segments)continue;
    stats.inlineGroups++;
    const sourceAnswers=insertion.answers || [insertion.answer],flattened=insertion.segments.flatMap(s=>s.answers);
    check(`${card.cid}:${row.id}: equal-value grouping conserves every answer`,()=>{
     assert.equal(flattened.length,sourceAnswers.length);
     assert.deepEqual(flattened.map(a=>JSON.stringify(answerCore(a))).sort(),sourceAnswers.map(a=>JSON.stringify(answerCore(a))).sort());
     let previousOrder=-1;
     for(const segment of insertion.segments){
      const colors=new Set(segment.answers.map(a=>inline.candidate(a)?'branch-candidate':a.confidence));
      assert.equal(colors.size,1,'different evidence colors cannot merge');
      assert.equal(segment.color,[...colors][0]);
      assert.equal(new Set(segment.answers.map(a=>inline.compact(a,insertion.effect.label))).size,1,'different values/units cannot merge');
      const order=segment.branches.length?Math.min(...segment.branches.map(b=>b.order)):-1;
      assert(order>=previousOrder,'effect order follows shared branch identity');previousOrder=order;
      for(const answer of segment.answers)if(answer.displayBranch)assert(segment.branches.some(b=>b.key===answer.displayBranch.key));
      if(segment.conditionKnown)assert(segment.answers.every(a=>a.displayBranch?.conditionKnown));
     }
    });
    stats.mergedAnswers+=sourceAnswers.length-insertion.segments.length;
    outputs.push({rowId:row.id,label:insertion.effect.label,values:insertion.segments.map(s=>({text:s.text,color:s.color,known:s.conditionKnown,condition:s.conditionLabel,branches:s.branches.map(b=>b.key)}))});
   }
  });
  if([20622,20332,30207,20437,10213].includes(card.cid))samples.push({cid:card.cid,name:skill.name,stage:skill.stage,branches:skill.branchTable.map(b=>({key:b.key,condition:b.conditionLabel,known:b.conditionKnown,raw:b.raw})),outputs});
 }
 if(hasConditions)stats.conditionCards++;
 check(`${card.cid}: card and overlay input immutable`,()=>{assert.equal(JSON.stringify(card),frozenBefore);assert.equal(JSON.stringify(applied),appliedBefore);});
}
check('all 2236 frozen cards',()=>assert.equal(stats.cards,2236));
check('parent and overlay objects remain immutable',()=>{assert.equal(JSON.stringify(records),recordsBefore);assert.equal(JSON.stringify(overlay),overlayBefore);});
const sample=cid=>samples.find(s=>s.cid===cid),output=(cid,label)=>sample(cid)?.outputs.find(o=>o.label===label);
check('20622: shared 0th/1st/2nd/3rd/Max across attack/defence/movement',()=>{
 const labels=['0thChain','1stChain','2ndChain','3rdChain','MaxChain'];
 for(const label of ['攻击力','防御','移动速度']){
  assert.deepEqual(output(20622,label).values.map(v=>v.condition),labels);
  assert(output(20622,label).values.every(v=>v.known));
 }
 assert.deepEqual(output(20622,'攻击力').values.map(v=>v.text),['+45% ×C','+46% ×C','+47% ×C','+48% ×C','+50% ×C']);
 assert.deepEqual(output(20622,'攻击力').values.map(v=>v.color),['inferred',...Array(4).fill('branch-candidate')]);
 assert(!Object.hasOwn(sample(20622).branches[0].raw,'chs'),'missing source chs remains missing despite runtime default');
});
check('20332: eight HP × Chain records merge into four HP values',()=>{
 const damage=output(20332,'伤害');assert.equal(sample(20332).branches.length,8);
 assert.deepEqual(damage.values.map(v=>v.condition),['HP 76–100%','HP 51–75%','HP 26–50%','HP 0–25%']);
 assert(damage.values.every(v=>v.known && v.branches.length===2));
 assert.deepEqual(damage.values.map(v=>v.text),['系数 20倍','19倍','18倍','17倍']);
});
for(const cid of [30207,20437])check(`${cid}: additional/indistinguishable gates retain unknown`,()=>{
 assert(sample(cid).branches.every(b=>!b.known));
 assert(sample(cid).outputs.flatMap(o=>o.values).every(v=>!v.known));
});
check('30207: absent mana field remains distinct from zero',()=>assert(sample(30207).branches.some(b=>!Object.hasOwn(b.raw,'mns'))));
check('20437: six equal damage records retain all sources once',()=>{const values=output(20437,'伤害').values;assert.equal(values.length,1);assert.equal(values[0].branches.length,6);});
// Missing fields use documented native defaults, not convenience JS defaults.
const synthetic=raws=>({name:'boundary',rows:[{id:'boundary',effects:[{label:'攻击力',answers:raws.map((raw,i)=>({text:`攻击力提高 ${i+1}%`,confidence:'inferred',branchCandidate:true,source:{layer:'CACHE',branchId:900+i,conditionsRaw:raw}}))}]}]});
check('missing hpend defaults to zero and cannot invent 100%',()=>{
 const prepared=inline.prepareSkill(synthetic([{hpstart:51,che:1},{hpstart:0,hpend:100,chs:2,che:2}]));
 const entry=prepared.branchTable.find(b=>b.id===900);assert.equal(entry.conditionKnown,false);assert(!/100%/.test(entry.hpLabel || ''));
});
check('explicit/missing zero chain endpoint never invents unbounded range',()=>{
 const prepared=inline.prepareSkill(synthetic([{hpend:100,chs:2},{hpend:100,chs:3,che:3}]));
 assert.equal(prepared.branchTable.find(b=>b.id===900).conditionKnown,false);
});
check('varying flag bits retain unknown despite clear Chain labels',()=>{
 const prepared=inline.prepareSkill(synthetic([{hpend:100,che:1,flag:0},{hpend:100,chs:2,che:2,flag:4}]));
 assert(prepared.branchTable.every(b=>!b.conditionKnown));
});
check('identical full behavior with different voice keeps its known Chain',()=>{
 const prepared=inline.prepareSkill(synthetic([{hpend:100,chs:2,che:5,skillid0:123,voice:1},{hpend:100,chs:2,che:5,skillid0:123,voice:2}]));
 assert(prepared.branchTable.every(b=>b.conditionKnown && b.conditionLabel==='1stChain以上'));
});
check('same threshold with different or extra executor remains uncertain',()=>{
 for(const changed of [{skillid0:124},{skillid0:123,skillid1:456},{skillid0:123,unknownGate:1}]){
  const prepared=inline.prepareSkill(synthetic([{hpend:100,chs:2,che:5,skillid0:123},{hpend:100,chs:2,che:5,...changed}]));
  assert(prepared.branchTable.every(b=>!b.conditionKnown));
 }
});
const report={pass:failures.length===0,stats,failures,samples,inputHashes:{inline:sha(path.join(__dirname,'web/inline.js')),branchCandidates:sha(path.join(root,'data/branch_candidates.js')),branchConditions:sha(path.join(root,'data/branch_conditions.js'))},scope:'Presentation-only exhaustive structural audit of frozen cards + overlay. Native evidence is static APK code, not a full runtime or device validation.'};
const {freshReviewDirectory}=require('./review_output.cjs');
const destination=path.join(freshReviewDirectory('player-conditions'),'validation.json');
fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({pass:report.pass,stats,failures},null,2));
if(failures.length)process.exitCode=1;
