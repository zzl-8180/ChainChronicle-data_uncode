'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { groupSkills, displayRow } = require('./web/levels.js');
const { answerKey } = require('./web/inline.js');
const {readPath}=require('./project_layout_paths.cjs');
const {freshReviewDirectory}=require('./review_output.cjs');
const logicalCardsDir = path.resolve(__dirname, '../../output/character_skills/reader_full_20261106/data/cards');
const cardsDir = readPath(logicalCardsDir);
function freeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.freeze(value);
    Object.values(value).forEach(freeze);
  }
  return value;
}
function skill(stage, zh, original = zh, name = '同名技能') {
  return { name, stage, rows: [{ id: stage, textZh: zh, original, effects: [{ answers: [{ confidence: 'inferred' }] }] }] };
}
function grouped(skills, id = 'extra') { return groupSkills({ id, skills }); }
const sample = [skill('等级 1', '攻击提高10.5%，持续20秒。'), skill('最高等级', '攻击提高12.5%，持续20秒。')];
const merged = grouped(freeze(sample));
assert.equal(merged.length, 1);
assert.deepEqual(merged[0].rows[0].levelTextParts, [
  { text: '攻击提高' }, { values: [{ stage: '等级 1', value: '10.5' }, { stage: '最高等级', value: '12.5' }] }, { text: '%，持续20秒。' },
]);
assert.equal(grouped(sample, 'ability'), sample);
for (const pair of [
  [skill('等级 1', '攻击10%'), skill('等级 2', '防御20%')],
  [skill('等级 1', '攻击10%', '攻撃10%'), skill('等级 2', '攻击20%', '防御20%')],
  [skill('等级 1', '夜间攻击10%'), skill('等级 2', '攻击20%')],
  [skill('等级 1', '攻击10%'), skill('等级 1', '攻击20%')],
  [skill('普通', '攻击10%'), skill('等级 2', '攻击20%')],
  [skill('等级 1', '攻击10%'), skill('等级 2', '攻击20%', '攻击20%', '异名')],
  [skill('等级 1', '攻击10%'), { ...skill('等级 2', '攻击20%'), rows: [] }],
  [skill('等级 1', '攻击10%'), skill('等级 2', '攻击20秒')],
]) assert.equal(grouped(pair).length, 2);
assert.equal(grouped([sample[0], skill('等级 2', '条件变化'), sample[1]]).length, 3);
const stats = { cards: 0, originalSkills: 0, displayedSkills: 0, mergedGroups: 0, originalRows: 0, groupedRows: 0, tracedRows: 0, varyingNumberPositions: 0 };
const examples = {};
for (const file of fs.readdirSync(cardsDir).filter(name => name.endsWith('.js'))) {
  const context = { window: {} };
  vm.runInNewContext(fs.readFileSync(path.join(cardsDir, file), 'utf8'), context);
  const card = Object.values(context.window.CC_DETAILS)[0];
  const before = JSON.stringify(card);
  freeze(card);
  stats.cards++;
  for (const group of card.groups) {
    const output = groupSkills(group);
    if (group.id !== 'extra') { assert.equal(output, group.skills); continue; }
    stats.originalSkills += group.skills.length;
    stats.displayedSkills += output.length;
    const expectedRows = group.skills.flatMap(item => item.rows);
    const seen = [];
    for (const item of output) {
      if (!item.levelStages) { seen.push(...item.rows); continue; }
      stats.mergedGroups++;
      for (const row of item.rows) {
        stats.groupedRows++;
        const display=displayRow(row,answerKey);
        for(const source of row.sourceRows){
          for(const effect of source.effects)for(const answer of effect.answers)assert(display.effects.some(e=>e.label===effect.label && e.answers.some(a=>answerKey(a)===answerKey(answer))), 'all levels bound answers displayed');
          for(const answer of source.unboundAnswers)assert(display.unboundAnswers.some(a=>answerKey(a)===answerKey(answer)), 'all levels unbound answers preserved');
        }
        assert.equal(row.effects, row.sourceRows[0].effects);
        assert.equal(row.unboundAnswers, row.sourceRows[0].unboundAnswers);
        assert.equal(row.sourceRows.length, item.levelStages.length);
        assert.equal(JSON.stringify(row.aliasIds), JSON.stringify(row.sourceRows.slice(1).map(source => source.id)));
        stats.varyingNumberPositions += row.levelTextParts.filter(part => part.values).length;
        row.levelRows.forEach(({ stage, row: source }, index) => {
          assert.equal(source, row.sourceRows[index]);
          assert.equal(stage, item.levelStages[index]);
          const reconstructed = row.levelTextParts.map(part => part.values ? part.values[index].value : part.text).join('');
          assert.equal(reconstructed, source.textZh);
        });
      }
      // Return to skill-major order for exact provenance/order comparison.
      item.levelStages.forEach((_, level) => item.rows.forEach(row => seen.push(row.sourceRows[level])));
    }
    assert.equal(seen.length, expectedRows.length);
    seen.forEach((row, index) => {
      if(row.extraLevelStage) {
        const {extraLevelStage,...original}=row;
        assert.equal(JSON.stringify(original),JSON.stringify(expectedRows[index]));
      } else assert.equal(row, expectedRows[index]);
    });
    stats.originalRows += expectedRows.length;
    stats.tracedRows += seen.length;
    if (['350', '30315'].includes(String(card.cid))) {
      examples[card.cid] = { before: group.skills.length, after: output.length, stages: output.map(item => item.levelStages || [item.stage]), values: output.flatMap(item => item.rows.flatMap(row => (row.levelTextParts || []).filter(part => part.values))) };
      assert.equal(group.skills.length, 5);
      assert.equal(output.length, 1);
    }
  }
  assert.equal(JSON.stringify(card), before);
}
assert.ok(examples['350'] && examples['30315']);
const result={status:'PASS',stats,examples};
fs.writeFileSync(path.join(freshReviewDirectory('levels'),'levels_validation.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({status:'PASS',stats}));
