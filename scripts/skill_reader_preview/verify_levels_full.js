'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const levels=require('./web/levels.js'),inline=require('./web/inline.js');
const cardsDir=path.resolve(__dirname,'../../output/character_skills/reader_full_20261106/data/cards');

const shape=text=>text.replace(/[0-9０-９]+(?:[.．][0-9０-９]+)?/g,'#');
const stats={cards:0,extraCards:0,originalSkills:0,displayedSkills:0,mergedGroups:0,numberOnlyCards:0,japaneseStructureCards:0,chineseOnlyBoundaries:0,representedBoundAnswers:0,supplementalSourceAnswers:0,supplementalDisplayAnswers:0,inferredNumericPositions:0,confirmedNumericPositions:0,literalNumericPositions:0,sourceRows:0};
const inventory=[],examples={};
for(const file of fs.readdirSync(cardsDir).filter(name=>name.endsWith('.js'))) {
  const context={window:{}};
  vm.runInNewContext(fs.readFileSync(path.join(cardsDir,file),'utf8'),context);
  const card=Object.values(context.window.CC_DETAILS)[0],before=JSON.stringify(card);
  stats.cards++;
  for(const group of card.groups.filter(group=>group.id==='extra')) {
    stats.extraCards++;stats.originalSkills+=group.skills.length;
    const output=levels.groupSkills(group);
    stats.displayedSkills+=output.length;stats.mergedGroups+=output.filter(skill=>skill.levelStages).length;
    const originalShapes=group.skills.map(skill=>JSON.stringify(skill.rows.map(row=>shape(row.original))));
    const category=new Set(originalShapes).size===1?'number_only':'japanese_structure_change';
    stats[category==='number_only'?'numberOnlyCards':'japaneseStructureCards']++;
    for(let i=1;i<group.skills.length;i++) {
      const a=group.skills[i-1],b=group.skills[i];
      if(originalShapes[i-1]===originalShapes[i] && JSON.stringify(a.rows.map(row=>shape(row.textZh)))!==JSON.stringify(b.rows.map(row=>shape(row.textZh))))stats.chineseOnlyBoundaries++;
    }
    const report={cid:card.cid,name:group.skills[0].name,category,originalSkills:group.skills.length,displayedSkills:output.length,segments:[]};
    for(const skill of output) {
      const segment={stages:skill.levelStages || [skill.stage],rows:[]};
      for(const row of skill.rows) {
        const display=levels.displayRow(row,inline.answerKey),plan=levels.presentation(display,inline);
        const sources=row.levelRows || [{stage:row.extraLevelStage,row}];
        stats.sourceRows+=sources.length;
        const allBound=sources.flatMap(({stage,row:source})=>(source.effects || []).flatMap(effect=>(effect.answers || []).map(answer=>({stage,answer}))));
        const remaining=plan.visible.flatMap(entry=>entry.effect.answers.flatMap(answer=>answer.levelAnswers));
        const actual=[...plan.represented,...remaining];
        assert.equal(actual.length,allBound.length,`all bound sources accounted ${row.id}`);
        allBound.forEach(expected=>assert.equal(actual.filter(value=>value.stage===expected.stage && value.answer===expected.answer).length,1,`exact once ${row.id}`));
        stats.representedBoundAnswers+=plan.represented.length;
        stats.supplementalSourceAnswers+=remaining.length;
        stats.supplementalDisplayAnswers+=plan.visible.reduce((n,e)=>n+e.effect.answers.length,0);
        sources.forEach(({row:source},index)=>{
          const text=plan.textParts.map(part=>part.values ? part.values[index].value : part.text).join('');
          assert.equal(text,source.textZh,`exact numeric/text reconstruction ${source.id}`);
        });
        plan.textParts.filter(part=>part.values).forEach(part=>{
          part.values.forEach(value=>{
            stats[value.color==='inferred'?'inferredNumericPositions':value.color==='confirmed'?'confirmedNumericPositions':'literalNumericPositions']++;
            if(value.color!=='literal') {
              assert(value.answers.length,'field colour requires answer');
              value.answers.forEach(answer=>assert.equal(value.color,answer.confidence));
            }
          });
        });
        segment.rows.push({id:row.id,sourceIds:sources.map(source=>source.row.id),textParts:plan.textParts.map(part=>part.values ? {constant:part.constant,values:part.values.map(({stage,value,color})=>({stage,value,color}))} : part),supplemental:plan.visible.map(entry=>({label:entry.effect.label,answers:entry.effect.answers.map(answer=>({text:answer.text,confidence:answer.confidence,levelLabel:answer.levelLabel}))})),represented:plan.represented.length});
      }
      report.segments.push(segment);
    }
    inventory.push(report);
    if([20622,292,350,20115,20302,20916,7241,20001].includes(+card.cid))examples[card.cid]=report;
  }
  assert.equal(JSON.stringify(card),before,'frozen input unchanged');
}
assert.equal(stats.cards,2236);assert.equal(stats.extraCards,494);
assert.equal(stats.chineseOnlyBoundaries,0);
assert.equal(examples[20622].displayedSkills,1);
assert.equal(examples[20622].segments[0].rows[0].supplemental.length,0,'20622 explicit values not repeated');
assert.equal(examples[292].segments[0].rows[0].supplemental.length,2,'292 defence and level 3 attack retain exact calculated values');
assert.equal(examples[350].segments[0].rows[0].textParts.filter(part=>part.values)[0].values[0].color,'inferred','constant mana retains gold');
assert.equal(examples[7241].displayedSkills,5,'actual new effects stay separate');
assert.equal(examples[20115].displayedSkills,2,'different mana descriptions not assumed equivalent');
const semanticNegative={extraLevelStage:'等级 1',textZh:'自身攻击力提高2%，我方攻击力提高4%。',original:'攻撃力が2%上がり、味方の攻撃力が4%上がる。',effects:[{label:'攻击力',answers:[{text:'攻击力提高 2%',confidence:'inferred',source:{rule:'skilllist|80|/param1'}}]}]};
assert(levels.presentation(semanticNegative,inline).textParts.filter(part=>part.values).every(part=>part.values[0].color==='literal'),'two attack targets cannot be coloured by numeric equality');
const {freshReviewDirectory}=require('./review_output.cjs');
const out=freshReviewDirectory('levels-full');
fs.writeFileSync(path.join(out,'inventory.json'),JSON.stringify(inventory,null,2));
fs.writeFileSync(path.join(out,'full_validation.json'),JSON.stringify({status:'PASS',stats,examples},null,2));
console.log(JSON.stringify({status:'PASS',stats}));
