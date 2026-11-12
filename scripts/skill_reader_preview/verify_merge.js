const fs=require('fs'),path=require('path'),assert=require('assert');
const {mergeGroups,answerKey,plan}=require('./web/inline.js');
const {readPath}=require('./project_layout_paths.cjs');
const {freshReviewDirectory}=require('./review_output.cjs');
const logicalOut=path.resolve(__dirname,'../../output/character_skills/reader_full_20261106');
const out=readPath(logicalOut);
const stats={cards:0,originalRows:0,displayRows:0,mergedSkills:0,mergedRows:0,originalAnswers:0,displayAnswers:0};
const samples=[];
for(const file of fs.readdirSync(path.join(out,'data/cards'))){
 const text=fs.readFileSync(path.join(out,'data/cards',file),'utf8');
 const card=JSON.parse(text.split(']=')[1].trim().replace(/;$/,''));
 const before=JSON.stringify(card), groups=mergeGroups(card.groups);
 assert.equal(JSON.stringify(card),before,'input is immutable');
 const oldRows=card.groups.flatMap(g=>g.skills.flatMap(s=>s.rows));
 const rows=groups.flatMap(g=>g.skills.flatMap(s=>s.rows));
 const indexed=new Map(rows.flatMap(r=>[r.id,...(r.aliasIds||[])].map(id=>[id,r])));
 assert.equal(indexed.size,oldRows.length,'every original row still addressable');
 stats.cards++;stats.originalRows+=oldRows.length;stats.displayRows+=rows.length;
 stats.mergedRows+=oldRows.length-rows.length;
 stats.mergedSkills+=groups.reduce((n,g)=>n+g.skills.reduce((m,s)=>m+(s.mergedSourceCount||0),0),0);
 for(const row of oldRows){
  const merged=indexed.get(row.id); assert(merged);
  assert((merged.sourceRows||[merged]).some(r=>JSON.stringify(r)===JSON.stringify(row)),'complete evidence retained');
  for(const effect of row.effects) for(const answer of effect.answers){
   assert(merged.effects.some(e=>e.label===effect.label && e.answers.some(a=>answerKey(a)===answerKey(answer))),'bound numeric answer retained');
  }
  for(const answer of row.unboundAnswers)assert(merged.unboundAnswers.some(a=>answerKey(a)===answerKey(answer)),'unbound numeric answer retained');
  stats.originalAnswers+=row.effects.reduce((n,e)=>n+e.answers.length,0)+row.unboundAnswers.length;
 }
 for(const row of rows){
  const p=plan(row);
  const bound=row.effects.reduce((n,e)=>n+e.answers.length,0);
  assert.equal(bound,p.inserts.reduce((n,e)=>n+(e.answers||[e.answer]).length,0)+p.visible.concat(p.held).reduce((n,e)=>n+e.effect.answers.length,0));
  stats.displayAnswers+=bound+row.unboundAnswers.length;
 }
 if([350,30337,10210].includes(card.cid))samples.push({cid:card.cid,originalRows:oldRows.length,displayRows:rows.length,skills:groups[0].skills.map(s=>({name:s.name,stage:s.stage,rows:s.rows.length,merged:s.mergedSourceCount||0}))});
 if(card.cid===350){
  assert.equal(groups[0].skills.length,2);assert.equal(rows.length,59);
  const row=groups[0].skills[0].rows[2];
  assert.equal(row.effects.reduce((n,e)=>n+e.answers.length,0),4,'same values shown once');
  assert.equal(row.sourceRows[1].effects[0].answers[0].condition,'触发条件待核实','different condition is retained in source');
  assert.equal(plan(groups[0].skills[0].rows[0]).inserts[0].answers.length,2,'25 and 27.5 still inline');
  const skills=card.groups[0].skills;
  const ambiguous=[skills[0],{...skills[0],name:'另一个技能'},skills[2]];
  assert.equal(mergeGroups([{skills:ambiguous}])[0].skills.length,3,'ambiguous same-prose matches do not pick an arbitrary branch');
  assert.equal(groups[0].skills[0].rows[5].id.split('-').pop(),'f5','original condition order');
 }
}
const result={pass:true,stats,samples,checks:['input immutable','all original row IDs retained as aliases','all source records preserved byte-equivalent as objects','bound and unbound values retained by label/value/confidence/field/raw','inline and visible rendering conservation','350 two skills and one prose copy','350 independent conditions preserved','ambiguous source match not merged']};
fs.writeFileSync(path.join(freshReviewDirectory('presentation-merge'),'merge_validation.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
