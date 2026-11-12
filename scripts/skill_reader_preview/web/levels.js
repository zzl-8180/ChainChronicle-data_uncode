/* Presentation only: preserve every level's original rows and evidence. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.CC_LEVELS = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const numberPattern = /[0-9０-９]+(?:[.．][0-9０-９]+)?/g;
  function tokens(text) {
    const fixed = [], numbers = [];
    let end = 0;
    for (const match of text.matchAll(numberPattern)) {
      fixed.push(text.slice(end, match.index));
      numbers.push(match[0]);
      end = match.index + match[0].length;
    }
    fixed.push(text.slice(end));
    return { fixed, numbers };
  }
  function signature(skill) {
    if (!/^(?:等级\s+[0-9]+|最高等级)$/.test(skill.stage || '') ||
        typeof skill.name !== 'string' || !Array.isArray(skill.rows) || !skill.rows.length) return null;
    if (skill.rows.some(row => typeof row.textZh !== 'string' || typeof row.original !== 'string')) return null;
    return JSON.stringify([skill.name, skill.rows.map(row => [tokens(row.textZh).fixed, tokens(row.original).fixed])]);
  }
  function textParts(levelRows) {
    const parsed = levelRows.map(item => tokens(item.row.textZh));
    const parts = [];
    function addText(text) {
      if (!text) return;
      const previous = parts[parts.length - 1];
      if (previous && Object.prototype.hasOwnProperty.call(previous, 'text')) previous.text += text;
      else parts.push({ text });
    }
    parsed[0].fixed.forEach((fixed, index) => {
      addText(fixed);
      if (index === parsed[0].numbers.length) return;
      const values = parsed.map((item, level) => ({ stage: levelRows[level].stage, value: item.numbers[index] }));
      if (values.every(item => item.value === values[0].value)) addText(values[0].value);
      else parts.push({ values });
    });
    return parts.length ? parts : [{ text: '' }];
  }
  function merge(skills) {
    if (skills.length === 1) return {...skills[0], rows: skills[0].rows.map(row=>({...row,extraLevelStage:skills[0].stage}))};
    return Object.assign({}, skills[0], {
      levelStages: skills.map(skill => skill.stage),
      rows: skills[0].rows.map((base, index) => {
        const levelRows = skills.map(skill => ({ stage: skill.stage, row: skill.rows[index] }));
        return Object.assign({}, base, {
          extraLevelStage: skills[0].stage,
          levelRows,
          aliasIds: levelRows.slice(1).map(item => item.row.id),
          sourceRows: levelRows.map(item => item.row),
          levelTextParts: textParts(levelRows),
        });
      }),
    });
  }
  function groupSkills(group) {
    if (group.id !== 'extra') return group.skills;
    const result = [];
    let run = [], key = null;
    function flush() {
      if (run.length) result.push(merge(run));
      run = [];
    }
    // Contiguous runs preserve the original ordering, including structural changes.
    for (const skill of group.skills) {
      const nextKey = signature(skill);
      if (nextKey === null || key !== nextKey || run.some(item => item.stage === skill.stage)) flush();
      run.push(skill);
      key = nextKey;
      if (nextKey === null) flush();
    }
    flush();
    return result;
  }
  function displayRow(row, answerKey) {
    if (!row.levelRows) return row;
    const effects=[];
    const labels=[...new Set(row.levelRows.flatMap(x=>x.row.effects.map(e=>e.label)))];
    labels.forEach(label=>{
      const byLevel=row.levelRows.map(x=>({stage:x.stage,effects:x.row.effects.filter(e=>e.label===label)}));
      const records=byLevel.flatMap(x=>x.effects.flatMap(e=>e.answers.map(a=>({stage:x.stage,a,status:e.status}))));
      const grouped=new Map();
      records.forEach(x=>{const k=answerKey(x.a);if(!grouped.has(k))grouped.set(k,{a:x.a,stages:[]});if(!grouped.get(k).stages.includes(x.stage))grouped.get(k).stages.push(x.stage);});
      const answers=[...grouped.values()].map(x=>({...x.a,levelLabel:x.stages.length===row.levelRows.length ? '各等级' : x.stages.join(' / ')}));
      effects.push({...(byLevel.find(x=>x.effects.length)?.effects[0] || {}),label,answers,status:records.some(x=>x.status==='has_answer')?'has_answer':byLevel.every(x=>x.effects.every(e=>e.status==='justified_na'))?'justified_na':'unresolved'});
    });
    const unbound=new Map();
    row.levelRows.forEach(x=>x.row.unboundAnswers.forEach(a=>{const k=answerKey(a);if(!unbound.has(k))unbound.set(k,{...a,readerOrigin:x.stage});}));
    return {...row,effects,unboundAnswers:[...unbound.values()]};
  }
  function literal(answer) {
    return !answer.source?.rule && /^原文数字，字段关联未证(?:；|$)/.test(answer.source?.limitations || '');
  }
  function normalized(value) {
    return String(value).replace(/[０-９]/g,x=>String(x.charCodeAt(0)-0xff10)).replace(/．/g,'.');
  }
  function declaredPosition(source, effect, answer) {
    if ((source.effects || []).filter(item=>item.label===effect.label).length!==1) return -1;
    let pattern;
    // These are the currently represented field-backed extra-ability shapes.
    // A unique equal number elsewhere in a sentence is insufficient.
    if (effect.label==='开局法珠' && /开始战斗/.test(source.textZh) && /戦闘を開始する/.test(source.original))
      pattern=/持有([0-9０-９]+(?:[.．][0-9０-９]+)?)颗[^。]*法珠的状态下开始战斗/g;
    else if (effect.label==='攻击力' && (source.textZh.match(/攻击力/g) || []).length===1)
      pattern=/攻击力提高\s*([0-9０-９]+(?:[.．][0-9０-９]+)?)%/g;
    if(!pattern)return -1;
    const matches=[...source.textZh.matchAll(pattern)], values=tokens(answer.text || '').numbers;
    if(matches.length!==1 || values.length!==1 || normalized(matches[0][1])!==normalized(values[0]))return -1;
    const numberStart=matches[0].index+matches[0][0].indexOf(matches[0][1]);
    return [...source.textZh.matchAll(numberPattern)].findIndex(match=>match.index===numberStart);
  }
  function presentation(row, inline) {
    const levels=row.levelRows || [{stage:row.extraLevelStage,row}];
    const parsed=levels.map(({row:source})=>tokens(source.textZh || ''));
    const numeric=parsed.map((part,index)=>part.numbers.map(value=>({stage:levels[index].stage,value,color:'literal',answers:[]})));
    const records=[], represented=[];
    levels.forEach(({stage,row:source},level)=>{
      (source.effects || []).forEach(effect=>(effect.answers || []).forEach(answer=>{
        const numbers=tokens(answer.text || '').numbers;
        let position=-1;
        // Only colour a declared value when its one numeric token has one
        // exact position in this row. Numeric resemblance alone never binds
        // a multi-value answer or an unknown field to an effect.
        if (source.translationStatus!=='pending' && !literal(answer) && !inline.candidate(answer) && numbers.length===1 &&
            ['confirmed','inferred'].includes(answer.confidence) && !inline.semanticUnclear(answer)) {
          position=declaredPosition(source,effect,answer);
        }
        if (position>=0) {
          const value=numeric[level][position];
          // Distinct confidence classes are not silently collapsed.
          if (!value.answers.length || value.color===answer.confidence) {
            value.color=answer.confidence;value.answers.push(answer);
          } else position=-1;
        }
        const literalPresent=source.translationStatus!=='pending' && literal(answer) && numbers.length && numbers.every(number=>
          parsed[level].numbers.some(value=>normalized(value)===normalized(number)) && tokens(source.original || '').numbers.some(value=>normalized(value)===normalized(number)));
        if (position>=0 || literalPresent) represented.push({stage,answer,effectId:effect.id,position});
        else records.push({stage,answer,effect});
      }));
    });
    const textParts=[];
    parsed[0].fixed.forEach((fixed,index)=>{
      if(fixed)textParts.push({text:fixed});
      if(index<parsed[0].numbers.length) {
        const values=numeric.map(part=>part[index]);
        textParts.push({values,constant:values.every(value=>value.value===values[0].value && value.color===values[0].color)});
      }
    });
    const groups=new Map();
    records.forEach(record=>{
      const {answer,effect}=record;
      const parsedAnswer=tokens(answer.text || '');
      const key=JSON.stringify([effect.label,parsedAnswer.fixed,answer.confidence,answer.condition || '',answer.branchLabel || '',inline.candidate(answer),inline.semanticUnclear(answer)]);
      if(!groups.has(key))groups.set(key,[]);
      groups.get(key).push(record);
    });
    const visible=[];
    groups.forEach(entries=>{
      const first=entries[0], byStage=new Map();
      // Keep genuine multiple answers within a level separate. A repeated
      // source may be shared, but never invent a level or numeric order.
      if(entries.some(entry=>byStage.has(entry.stage) ? true : (byStage.set(entry.stage,entry),false))) {
        entries.forEach(entry=>visible.push({effect:{...entry.effect,answers:[{...entry.answer,levelLabel:entry.stage,levelAnswers:[entry]}]}}));
        return;
      }
      const answers=entries.map(entry=>tokens(entry.answer.text || ''));
      const text=answers[0].fixed.map((fixed,index)=>{
        if(index>=answers[0].numbers.length)return fixed;
        const values=answers.map(part=>part.numbers[index]);
        return fixed+(values.every(value=>value===values[0]) ? values[0] : values.join(' / '));
      }).join('');
      visible.push({effect:{...first.effect,answers:[{...first.answer,text,levelLabel:entries.length===levels.length?'各等级':entries.map(entry=>entry.stage).join(' / '),levelAnswers:entries}]}});
    });
    return {inserts:[],visible,held:[],branchLabel:'',strengthUnsolved:false,textParts,represented};
  }
  return { groupSkills, displayRow, presentation };
}));
