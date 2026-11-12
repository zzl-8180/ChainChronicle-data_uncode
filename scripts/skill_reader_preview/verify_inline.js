const fs = require('fs'), path = require('path'), assert = require('assert');
const {plan, compact, skillIdentity} = require('./web/inline.js');
const root = path.resolve(__dirname, '../..');
const out = path.join(root, 'output/character_skills/reader_full_20261106');
const files = fs.readdirSync(path.join(out,'data/cards'));
const stats = {cards:0, rows:0, inlineAnswers:0, visibleAnswers:0, heldAnswers:0, unboundAnswers:0, branchMarkers:0, confidence:{}, labels:{}};
const samples = [], variantRows = [], identityAudit = [];
const data = new Map();
for(const file of files) {
  const text = fs.readFileSync(path.join(out,'data/cards',file),'utf8');
  const card = JSON.parse(text.split(']=')[1].trim().replace(/;$/,'')); data.set(card.cid,card); stats.cards++;
  for(const group of card.groups) for(const skill of group.skills) for(const row of skill.rows) {
    const before = JSON.stringify(row), p = plan(row); stats.rows++;
    assert.equal(JSON.stringify(row), before, 'planner must not change source');
    const bound = row.effects.reduce((n,e)=>n+e.answers.length,0);
    assert.equal(p.inserts.reduce((n,e)=>n+(e.answers || [e.answer]).length,0) + p.visible.concat(p.held).reduce((n,e)=>n+e.effect.answers.length,0),bound);
    for (const entry of p.visible) assert.equal(entry.effect.status,'has_answer');
    for (const effect of row.effects.filter(e=>e.status==='has_answer')) assert(p.inserts.some(i=>i.effect===effect)||p.visible.some(i=>i.effect===effect),'bound values must be visible');
    assert.equal(new Set(p.inserts.map(e=>e.end)).size,p.inserts.length);
    for(const entry of p.inserts) {
      assert(entry.end>0 && entry.end <= row.textZh.length);
      assert.equal(entry.effect.status,'has_answer');
      if (!entry.branchCandidate) assert(!entry.answer.condition && !entry.answer.branchLabel && !entry.answer.relatedDescription);
      else variantRows.push({cid:card.cid,row:row.id,text:entry.text,span:entry.answer.source.originalEffectBinding?.span});
      for (const answer of entry.answers || [entry.answer]) {
        assert.deepEqual(compact(answer,entry.effect.label).match(/[\d.]+/g),answer.text.match(/[\d.]+/g),'numeric tokens must survive');
        assert.equal(compact(answer,entry.effect.label).includes('×C'),answer.text.includes('× Chain修正'),'Chain multiplier preserved exactly once');
      }
      for (const a of entry.answers || [entry.answer]) stats.confidence[a.confidence]=(stats.confidence[a.confidence]||0)+1;
      stats.labels[entry.effect.label]=(stats.labels[entry.effect.label]||0)+1;
    }
    stats.inlineAnswers+=p.inserts.reduce((n,e)=>n+(e.answers || [e.answer]).length,0);
    stats.visibleAnswers+=p.visible.reduce((n,e)=>n+e.effect.answers.length,0);
    stats.heldAnswers+=p.held.reduce((n,e)=>n+e.effect.answers.length,0);
    stats.unboundAnswers+=row.unboundAnswers.length;
    if(p.branchLabel)stats.branchMarkers++;
    if(p.inserts.length && samples.length<24 && (stats.rows%53===0 || card.cid===30315)) {
      let reconstructed='',pos=0;
      for(const x of p.inserts){reconstructed+=row.textZh.slice(pos,x.end)+'（'+x.text+'）';pos=x.end;}
      samples.push({cid:card.cid,row:row.id,original:row.original,inline:reconstructed+row.textZh.slice(pos)});
    }
  }
}
function rows(cid){return data.get(cid).groups.flatMap(g=>g.skills.flatMap(s=>s.rows));}
const initial350=rows(350)[0];
assert.equal(plan(initial350).inserts.length,1);
assert(plan(initial350).inserts[0].branchCandidate);
assert(plan(initial350).inserts[0].text.includes('25倍') && plan(initial350).inserts[0].text.includes('27.5倍'));
assert.equal(plan(initial350).inserts[0].end, initial350.textZh.indexOf('伤害')+2);
assert.equal(plan(initial350).branchLabel,'强化分支待确认');
assert.equal(plan(initial350).visible.length,0);
assert(rows(350).some(r => /1stChain/.test(r.textZh) && plan(r).strengthUnsolved));
assert.equal(plan(rows(30315)[2]).inserts.length,6);
assert.equal(plan(rows(30315)[2]).inserts[0].text,'+60% ×C');
assert.equal(plan(rows(30315)[2]).inserts[1].text,'固定减伤系数 0.3 ×C');
assert.equal(plan(rows(29)[0]).inserts[0].text,'系数 4倍');
assert(rows(30236).some(r=>plan(r).inserts.some(e=>e.answer.confidence==='confirmed')));
const fixture=JSON.parse(JSON.stringify(rows(29)[0]));
fixture.textZh='受到的伤害降低，并对敌人造成伤害。';assert.equal(plan(fixture).inserts.length,0);
fixture.textZh='受到的伤害降低。';assert.equal(plan(fixture).inserts.length,0);
fixture.textZh='对敌人造成伤害。';fixture.effects[0].answers[0].condition='1stChain以上';assert.equal(plan(fixture).inserts.length,0);
for (const card of data.values()) for (const group of card.groups) for (const skill of group.skills) {
  if (skill.stage === '共用描述') identityAudit.push({cid:card.cid,name:skill.name,...skillIdentity(skill,group.skills)});
}
assert.equal(identityAudit.find(x=>x.cid===350).stage,'共鸣必杀 · 角色资料');
assert(identityAudit.every(x=>!x.stage.includes('共用描述')));
const invalidSpan=JSON.parse(JSON.stringify(initial350));
invalidSpan.effects[0].answers[1].source.originalEffectBinding.span=[0,2];
assert.equal(plan(invalidSpan).inserts.length,0);
const {freshReviewDirectory}=require('./review_output.cjs');
fs.writeFileSync(path.join(freshReviewDirectory('inline'),'inline_validation.json'),JSON.stringify({pass:true,stats,regressions:['350 candidates inside unique damage clause; distinct span rejected','30315 six buff values inline','29 single damage coefficient','30236 confirmed confidence retained','duplicate anchor rejected','damage taken rejected','extra condition excluded from sentence; bound value remains visible'],variantRows,identityAudit,samples},null,2));
console.log(JSON.stringify(stats));console.log(JSON.stringify({candidateRows:variantRows.length,identityChecks:identityAudit.length}));
