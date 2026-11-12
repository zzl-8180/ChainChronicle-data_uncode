const fs=require('fs'),path=require('path'),assert=require('assert');
const m=require('./web/inline.js');
const root=path.resolve(__dirname,'../../output/character_skills/reader_full_20261106');
const inline=[],left=[],unclear=[];
for(const file of fs.readdirSync(path.join(root,'data/cards'))){
 const text=fs.readFileSync(path.join(root,'data/cards',file),'utf8');
 const card=JSON.parse(text.split(']=')[1].trim().replace(/;$/,''));
 for(const group of m.mergeGroups(card.groups))for(const skill of group.skills)for(const row of skill.rows){
  const p=m.plan(row);
  for(const e of p.inserts)if(e.branchCandidate)for(const a of e.answers||[e.answer]){
   assert(!m.semanticUnclear(a),'semantic ambiguity must not be presented as a branch candidate');
   inline.push({cid:card.cid,row:row.id,label:e.effect.label,value:a.text,condition:a.condition,anchorEnd:e.end});
  }
  for(const e of p.visible)for(const a of e.effect.answers){
   const entry={cid:card.cid,row:row.id,label:e.effect.label,value:a.text,condition:a.condition};
   if(m.candidate(a))left.push(entry);
   if(m.semanticUnclear(a))unclear.push(entry);
  }
 }
}
assert.equal(left.length,0,'all purple candidates should have a unique sentence position');
assert(unclear.some(x=>x.cid===30236 && x.condition.includes('沙漠')));
assert(unclear.some(x=>x.value.includes('用途待确认')));
const result={pass:true,purpleInline:inline.length,purpleOutside:left.length,semanticUnclear:unclear.length,left,unclear,inline};
const {freshReviewDirectory}=require('./review_output.cjs');
fs.writeFileSync(path.join(freshReviewDirectory('purple'),'purple_audit.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({pass:true,purpleInline:inline.length,purpleOutside:left.length,semanticUnclear:unclear.length}));
