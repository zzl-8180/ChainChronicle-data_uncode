/* Presentation-only annotations. Never infer a new effect or a branch condition. */
(function (root) {
  'use strict';
  const anchors = {
    '攻击力': /攻击力/g, '防御': /防御力/g, '移动速度': /移动速度/g,
    '暴击率': /暴击率/g, '暴击威力': /暴击威力/g,
    '持续时间': /一定时间|一段时间/g, '伤害': /伤害/g, '回复': /回复/g, '生命回复': /回复/g,
  };
  function compact(answer, label) {
    let text = answer.text.replace(/\s*×\s*Chain修正/g, ' ×C').trim();
    if (/^C19_P[12]_/.test(answer.source?.evidenceScope || '')) text=text.replace(/^自身/, '');
    if (label === '攻击力' && /^受击目标攻击力降低/.test(text)) return text.replace(/^受击目标攻击力降低\s*/, '降低 ');
    if (label === '移动速度' && /^受击目标移动速度降低/.test(text)) return text.replace(/^受击目标移动速度降低\s*/, '降低 ');
    if (label === '防御' && /^受击目标受到的伤害提高/.test(text)) return text.replace(/^受击目标受到的伤害提高\s*/, '受伤 +');
    if (label === '伤害') return text.replace(/^伤害系数\s*/, `${answer.displayAssessment?.valuePrefix || '系数'} `);
    if (label === '持续时间') return text.replace(/^持续\s*/, '');
    if (label === '防御') return text.replace(/^受到的伤害降低\s*/, '减伤 ').replace(/^固定防御：接受者的攻击计算基值\s*×\s*/, '固定减伤系数 ');
    return text.replace(new RegExp('^' + label + '提高\\s*'), '+').replace(new RegExp('^' + label), '').trim();
  }
  function parallelValues(answers, label) {
    const values = [];
    const ordered = [...answers].sort((a,b)=>(a.displayBranch?.order ?? -1)-(b.displayBranch?.order ?? -1));
    ordered.forEach(answer=>{
      const text=compact(answer,label), color=candidate(answer) ? 'branch-candidate' : answer.confidence;
      // Equal values are shared only within one confidence class. Keep every
      // source and branch identity, including different triggers with equal values.
      const existing=values.find(v=>v.text===text && v.color===color);
      if (existing) existing.answers.push(answer);
      else values.push({answer,answers:[answer],text,color});
    });
    values.forEach(value=>{
      value.branches=[...new Map(value.answers.flatMap(a=>a.displayBranches || (a.displayBranch?[a.displayBranch]:[])).map(branch=>[branch.key,branch])).values()].sort((a,b)=>a.order-b.order);
      const branches=value.branches;
      value.conditionKnown=branches.length>0 && value.answers.every(a=>a.displayBranch?.conditionKnown);
      const hp=[...new Set(branches.map(b=>b.hpLabel))];
      const covered=new Set(branches.flatMap(b=>b.chainRange ? Array.from({length:b.chainRange[1]-b.chainRange[0]+1},(_,i)=>b.chainRange[0]+i) : []));
      // Equal damage in every Chain state need not repeat Chain beside its HP range.
      value.conditionLabel=value.conditionKnown && hp.length===1 && hp[0] && [0,1,2,3,4].every(n=>covered.has(n))
        ? hp[0] : [...new Set(branches.map(b=>b.conditionLabel).filter(Boolean))].join(' / ');
      if(value.answers.every(a=>a.displayAssessment?.branchInvariant)) {
        value.conditionKnown=true;
        value.conditionLabel='各分支相同';
      }
      const partials=value.answers.filter(a=>a.displayAssessment?.partialCondition);
      if(!value.conditionKnown && partials.length) {
        value.conditionPartial=true;
        value.conditionLabel=(partials.length<value.answers.length?'部分分支：':'')+[...new Set(partials.map(a=>a.displayAssessment.partialCondition.replace(/^地形：/,'')))].join(' / ');
      }
    });
    const prefix = values[0]?.text.match(/^[^\d+\-−]+/)?.[0] || '';
    if (prefix && values.every(value=>value.text.startsWith(prefix))) {
      values.forEach((value,index)=>{ if (index) value.text=value.text.slice(prefix.length); });
    }
    return values;
  }
  const chainNames=['0thChain','1stChain','2ndChain','3rdChain','MaxChain'];
  function describeBranches(table) {
    // Static consumer proof: audit/player_conditions_20261107/native_conditions.*.
    // Missing chs/che getters and ctor hpstart/hpend values are 0. Preserve
    // original JSON untouched. These labels do not promote effect bindings.
    table.forEach(entry=>{
      const raw=entry.raw;if(!raw)return;
      const hpStart=raw.hpstart ?? 0,hpEnd=raw.hpend ?? 0;
      entry.hpLabel=Number.isInteger(hpStart) && Number.isInteger(hpEnd) && hpStart>=0 && hpEnd<=100 && hpStart<=hpEnd && (hpStart>0 || hpEnd<100) ? `HP ${hpStart}–${hpEnd}%` : '';
      const start=raw.chs ?? 0,end=raw.che ?? 0;
      const chainValid=Number.isInteger(start) && Number.isInteger(end) && start>=0 && end<=5 && start<=end;
      if(chainValid && (start!==0 || end!==0)) {
        const low=Math.max(0,start-1),high=Math.max(0,end-1);
        entry.chainRange=[low,high];
        entry.chainLabel=low===high ? chainNames[low] : high===4 ? `${chainNames[low]}以上` : `${chainNames[low]}–${chainNames[high]}`;
      }
      entry.conditionLabel=[entry.hpLabel,entry.chainLabel].filter(Boolean).join(' · ');
      const otherGate=['limit','bgf','mns','mne','posp','pose','tid'].some(key=>raw[key]!=null && raw[key]!==0);
      const invalidHp=![hpStart,hpEnd].every(Number.isInteger) || hpStart<0 || hpEnd>100 || hpStart>hpEnd;
      entry.conditionKnown=Boolean(entry.conditionLabel || entry.proseContext && table.length===1) && !otherGate && !invalidHp && chainValid;
      if(entry.conditionKnown && !entry.conditionLabel)entry.conditionLabel='本段技能';
    });
    // The same visible threshold cannot distinguish a random/use-count branch.
    const differentFlags=new Set(table.map(entry=>entry.raw?.flag ?? 0)).size>1;
    const signature=entry=>JSON.stringify(Object.entries(entry.raw || {}).filter(([k])=>!['patternid','sname','stext','sinfo','voice'].includes(k)).sort(([a],[b])=>a.localeCompare(b)));
    table.forEach(entry=>{
      if(differentFlags || table.some(other=>other!==entry && other.conditionLabel===entry.conditionLabel && signature(other)!==signature(entry)))entry.conditionKnown=false;
    });
  }
  function bindingFor(answer) {
    const original=answer.source?.originalBinding || {};
    const binding=original.g1_b1_binding || original.c12_p3_skilltext_mirror_binding || original.c8_p1_t27_binding || original.c11_p1_t114_binding || original.c7_p2_denju_binding || original;
    return binding.parent_chain ? {...binding,pattern_id:binding.parent_chain.pattern_id} : binding;
  }
  const sameRaw=(left,right)=>Boolean(left && right) && Object.keys(left).length===Object.keys(right).length && Object.keys(left).every(key=>JSON.stringify(left[key])===JSON.stringify(right[key]));
  const executionSlots=raw=>Object.fromEntries(Object.entries(raw || {}).filter(([key])=>/^skillid\d+$/.test(key)).sort(([a],[b])=>a.localeCompare(b,undefined,{numeric:true})));
  function prepareSkill(skill, conditionRecords, assessments, resolvedParents) {
    const effects=(skill.rows || []).flatMap(row=>(row.effects || []).map(effect=>({row,effect})));
    if (!effects.some(({effect})=>effect.answers.some(candidate))) return skill;
    const entries=new Map(), assignments=new Map();
    effects.forEach(({row,effect})=>{
      if (!effect.answers.some(candidate)) return;
      const bases=[...new Set(effect.answers.filter(a=>a.source?.baseBranchId!=null).map(a=>`${a.source.layer}:${a.source.baseBranchId}`))];
      effect.answers.forEach((answer,index)=>{
        const source=answer.source || {}, binding=bindingFor(answer);
        let id=source.branchId ?? binding.pattern_id;
        let layer=source.layer || source.allSources?.layer || binding.layer || '';
        const review=assessments?.[reviewKey(row,effect,answer)], selected=resolvedParents?.[review?.selectionKey];
        // The assessment records an exact, source-checked parent. Recover old
        // answer shapes without guessing from row indices, prose or values.
        if(review?.selectionResolved && selected && sameRaw(conditionRecords?.[review.selectionKey]?.raw,selected.parentRaw)) {
          if(id==null)id=selected.branchId;
          if(!layer)layer=review.selectionKey.split(':')[0];
        }
        // A missing ID is associated with the donor only when the effect has
        // one exact record/field match or documented donor. Never assign by
        // numeric magnitude, array position, or pattern index.
        if (id==null) {
          const matches=effect.answers.filter(a=>a.source?.branchId!=null && a.source.layer===layer && a.source.recordId===source.allSources?.record_id && a.source.field===source.field && a.source.raw===source.raw);
          const ids=[...new Set(matches.map(a=>a.source.branchId))];
          if(ids.length===1)id=ids[0];
        }
        if (id==null) {
          const matches=effect.answers.filter(a=>a.source?.baseBranchId!=null && a.source.layer===layer && a.source.donorRule===source.rule && a.source.donorRaw===source.raw && [row.id,...(row.aliasIds || [])].includes(a.source.donorRowId));
          const ids=[...new Set(matches.map(a=>a.source.baseBranchId))];
          if(ids.length===1)id=ids[0];
        }
        if(id==null)return; // Keep the value, but do not invent a branch identity.
        const key=`${layer}:${id}`,isOriginal=bases.includes(key);
        const raw=source.conditionsRaw || binding.conditions_raw || null;
        if(!raw && !conditionRecords?.[key]?.raw)return;
        if (!entries.has(key)) entries.set(key,{key,id,layer,original:isOriginal,raw,rawRecords:[],values:[]});
        const entry=entries.get(key);
        entry.original ||= isOriginal;
        entry.raw ||= raw;
        if(raw && !entry.rawRecords.some(r=>JSON.stringify(r)===JSON.stringify(raw)))entry.rawRecords.push(raw);
        entry.values.push({rowId:row.id,label:effect.label,text:compact(answer,effect.label)});
        assignments.set(answer,[key]);
      });
    });
    if (!entries.size) return applyAssessments(skill,assessments);
    entries.forEach(entry=>{
      const primary=conditionRecords?.[entry.key];
      if(primary) {
        entry.raw=primary.raw;entry.conditionSource=primary.source;
        if(!entry.rawRecords.some(r=>JSON.stringify(r)===JSON.stringify(primary.raw)))entry.rawRecords.push(primary.raw);
      }
    });
    // Ordinary values such as the buff duration can have no branch annotation.
    // Recover only a unique direct bossskill owner already present in this
    // skill, with its original record identity (not an equal numeric value).
    effects.forEach(({row,effect})=>effect.answers.forEach(answer=>{
      if(assignments.has(answer))return;
      const source=answer.source || {},record=source.allSources;
      if(record?.table!=='bossskill' || !source.rule?.startsWith('bossskill|') || record.record_id==null)return;
      const matches=[...entries.values()].filter(entry=>entry.layer===record.layer && Object.values(executionSlots(entry.raw)).includes(record.record_id));
      if(matches.length!==1)return;
      const entry=matches[0];
      entry.values.push({rowId:row.id,label:effect.label,text:compact(answer,effect.label)});
      assignments.set(answer,[entry.key]);
    }));
    // Full resolved cohorts include ordinary parents with no separate answer.
    // Share an existing effect binding only for the exact same layer, cohort
    // and complete executor-slot identities. Equal values are not evidence.
    const donors=[...entries.values()];
    const cohorts=new Set(donors.map(entry=>resolvedParents?.[entry.key]?.cohortKey).filter(Boolean));
    Object.entries(resolvedParents || {}).forEach(([key,parent])=>{
      if(entries.has(key) || !cohorts.has(parent.cohortKey))return;
      const layer=key.split(':')[0], slots=executionSlots(parent.parentRaw);
      const source=donors.find(entry=>entry.layer===layer && resolvedParents?.[entry.key]?.cohortKey===parent.cohortKey && Object.keys(slots).length && sameRaw(slots,executionSlots(entry.raw)));
      const entry={key,id:parent.branchId,layer,original:false,raw:parent.parentRaw,rawRecords:[parent.parentRaw],conditionSource:parent.parentSource,values:[]};
      if(source) {
        entry.displayAliasOf=source.key;entry.executionSlots=slots;
        entry.values=source.values.map(value=>({...value,displayAliasOf:source.key}));
        assignments.forEach(keys=>{if(keys.includes(source.key))keys.push(key);});
      } else entry.displayExclusionReason='本父已完成选档复核；当前展示无同执行链的已绑定效果，未从其他数值推造答案。';
      entries.set(key,entry);
    });
    const tableId=`${skill.rows[0].id}-branches`;
    const table=[...entries.values()].sort((a,b)=>Number(b.original)-Number(a.original) || a.key.localeCompare(b.key,undefined,{numeric:true}));
    table.forEach(entry=>{
      const prose=(entry.raw?.sinfo || '').replace(/\s/g,'');
      entry.proseContext=Boolean(prose && skill.rows.some(row=>(row.original || '').length>8 && prose.includes(row.original.replace(/\s/g,''))));
    });
    describeBranches(table);
    // A verified selector belongs to the exact parent, including original values.
    // This labels conditions only; numeric/effect confidence still uses per-answer review.
    table.forEach(entry=>{
      const resolved=resolvedParents?.[entry.key], raw=entry.raw;
      if(!resolved || !sameRaw(raw,resolved.parentRaw))return;
      entry.conditionKnown=true;
      entry.conditionLabel=resolved.selectionUnavailable?'本模式常规选档不选用':resolved.conditionLabel;
      entry.selectionOrder=resolved.selectionOrder;
    });
    // Use player condition order only when every branch has a known condition.
    if(table.every(b=>b.conditionKnown))table.sort((a,b)=>(a.selectionOrder ?? a.chainRange?.[0] ?? 0)-(b.selectionOrder ?? b.chainRange?.[0] ?? 0) || (b.raw?.hpstart ?? 0)-(a.raw?.hpstart ?? 0));
    const codes=index=>index<26 ? String.fromCharCode(65+index) : `B${index+1}`;
    table.forEach((entry,index)=>Object.assign(entry,{code:codes(index),order:index,tableId}));
    const byKey=new Map(table.map(entry=>[entry.key,entry]));
    const rows=skill.rows.map(row=>({...row,effects:row.effects.map(effect=>({...effect,answers:effect.answers.map(answer=>assignments.has(answer) ? {...answer,displayBranch:byKey.get(assignments.get(answer)[0]),displayBranches:assignments.get(answer).map(key=>byKey.get(key))} : answer)}))}));
    rows.forEach((row,index)=>{
      // This sentence qualifies the immediately preceding damage, rather than
      // introducing another unknown damage amount. Keep selection provisional.
      if (!/^ダメージ量は自身の残りHP量に応じて変化する。$/.test(row.original || '') || !index) return;
      const previous=rows[index-1];
      const damage=previous.effects.filter(e=>e.label==='伤害' && e.answers.some(candidate));
      if (damage.length!==1 || !damage[0].answers.some(a=>a.source?.conditionsRaw?.hpstart!=null)) return;
      row.knownCandidateScopes=[...new Set([...(row.knownCandidateScopes || []),'伤害'])];
      row.candidateLinks=[...(row.candidateLinks || []),{targetRowId:previous.id,labels:['伤害']}];
    });
    rows.forEach(row=>{
      const links=row.candidateLinks || [];
      row.linkedConditionsKnown=links.length>0 && links.every(link=>{
        const target=rows.find(r=>r.id===link.targetRowId || r.aliasIds?.includes(link.targetRowId));
        const answers=(target?.effects || []).flatMap(e=>e.answers).filter(candidate);
        return answers.length>0 && answers.every(a=>a.displayBranch?.conditionKnown);
      });
    });
    return applyAssessments({...skill,branchTable:table,rows},assessments);
  }
  function reviewKey(row,effect,answer) { return JSON.stringify([row.id,effect.id,answerKey(answer)]); }
  function applyAssessments(skill,records) {
    if(!records)return skill;
    const rows=skill.rows.map(row=>({...row,effects:row.effects.map(effect=>({...effect,answers:effect.answers.map(answer=>{
      const review=records[reviewKey(row,effect,answer)];
      return review ? {...answer,displayAssessment:review,...(review.selectionResolved && answer.displayBranch ? {displayBranch:{...answer.displayBranch,conditionKnown:true,conditionLabel:review.condition,order:review.selectionOrder}} : {})} : answer;
    })}))}));
    rows.forEach(row=>{
      row.linkedReviewReasons=[...new Set((row.candidateLinks || []).flatMap(link=>{
        const target=rows.find(r=>r.id===link.targetRowId || r.aliasIds?.includes(link.targetRowId));
        return (target?.effects || []).flatMap(e=>e.answers).filter(candidate).map(a=>a.displayAssessment?.shortReason || '条件待确认');
      }))];
    });
    const resolved=new Map(rows.flatMap(r=>r.effects.flatMap(e=>e.answers)).filter(a=>a.displayAssessment?.selectionResolved && a.displayBranch).map(a=>[a.displayBranch.key,a.displayBranch]));
    rows.forEach(row=>row.effects.forEach(effect=>{
      effect.answers=effect.answers.map(answer=>({...answer,...(resolved.has(answer.displayBranch?.key)?{displayBranch:resolved.get(answer.displayBranch.key)}:{}),...(answer.displayBranches?{displayBranches:answer.displayBranches.map(branch=>resolved.get(branch.key)||branch)}:{})}));
    }));
    return {...skill,rows,...(skill.branchTable?{branchTable:skill.branchTable.map(b=>resolved.get(b.key)||b)}:{})};
  }
  function orderedAnswers(answers) {
    const hp=answer=>(answer.displayBranch?.conditionLabel || answer.condition || '').match(/^HP\s+(\d+)–(\d+)%$/);
    // Apply the same high-to-low HP order to visible denju values. Leave mixed
    // or non-HP conditions in their evidence order and retain every answer.
    return answers.length && answers.every(answer=>hp(answer)) ? [...answers].sort((a,b)=>Number(hp(b)[1])-Number(hp(a)[1]) || Number(hp(b)[2])-Number(hp(a)[2])) : answers;
  }
  function orderGroups(groups) {
    const result=[...groups], inherited=result.findIndex(g=>g.label==='传授');
    if (inherited<0) return result;
    const [group]=result.splice(inherited,1), special=result.findIndex(g=>g.label==='必杀技');
    result.splice(special<0 ? 0 : special+1,0,group);
    return result;
  }
  function plan(row) {
    const text = row.textZh || '';
    const inserts = [], held = [], visible = [];
    const effects = row.effects || [];
    effects.forEach(effect => {
      const answers = effect.answers || [];
      if (!answers.length) return;
      const answer = answers[0], pattern = anchors[effect.label];
      // Multiple candidates can share a sentence position without confirming
      // which trigger selects them. Require the same explicit Japanese span,
      // a unique Chinese damage anchor, and meaningful variant labels.
      const damageMatches = [...text.matchAll(/伤害/g)];
      const spans = answers.map(a => a.source?.originalEffectBinding?.span);
      const damageVariants = effect.status === 'has_answer' && effect.label === '伤害' && answers.length > 1
        && row.translationStatus !== 'pending' && !row.translationNote && damageMatches.length === 1
        && effects.filter(e => e.label === '伤害').length === 1
        && answers.every(a => ['confirmed','inferred'].includes(a.confidence) && a.branchLabel && !/待核|待确认|有独立原文/.test(a.branchLabel)
          && (!a.condition || /^(?:触发条件待核实|触发条件待核对|实际触发条件仍需核对)$/.test(a.condition)))
        && spans.every(span => Array.isArray(span) && span.length === 2 && JSON.stringify(span) === JSON.stringify(spans[0])
          && /ダメージ/.test((row.original || '').slice(span[0],span[1])));
      if (damageVariants) {
        const segments=parallelValues(answers,'伤害');
        inserts.push({end:damageMatches[0].index+2, effect, answer, answers, branchCandidate:answers.some(candidate), text:segments.map(s=>s.text).join(' / '),segments});
        return;
      }
      // Purple means the numeric effect is bound but its activation branch is
      // still provisional. Keep that distinction in the sentence, not outside.
      const isHealing = ['回复','生命回复'].includes(effect.label) && answers.every(a=>/^回复输入系数/.test(a.text)) && /小幅回复|小回复/.test(text);
      const candidatePattern = isHealing ? /小幅回复|小回复/g : pattern;
      const candidateMatches = candidatePattern ? [...text.matchAll(candidatePattern)] : [];
      const uncertain = answers.some(candidate);
      const safeCandidate = (uncertain || answers.some(a=>a.displayAssessment)) && effect.status === 'has_answer'
        && row.translationStatus !== 'pending' && !row.translationNote
        && candidateMatches.length === 1 && (isHealing || effects.filter(e=>e.label===effect.label).length===1)
        && answers.every(a=>['confirmed','inferred'].includes(a.confidence) && !semanticUnclear(a))
        && (effect.label!=='伤害' || spans.filter(Array.isArray).every(span=>/ダメージ/.test((row.original||'').slice(span[0],span[1])) && JSON.stringify(span)===JSON.stringify(spans.filter(Array.isArray)[0])))
        && !(effect.label==='伤害' && /(?:反响|暴击)(?:造成的)?伤害|受到|承受|减伤|伤害降低|伤害减少/.test(text))
        && !(effect.label==='持续时间' && /每隔一定时间|每过一定时间/.test(text));
      if (safeCandidate) {
        const segments=parallelValues(answers,effect.label);
        inserts.push({end:candidateMatches[0].index+candidateMatches[0][0].length,effect,answer,answers,branchCandidate:uncertain,text:segments.map(s=>s.text).join(' / '),segments});
        return;
      }
      // C19's local self-ability scope is already expressed by this exact
      // sentence. Keep full runtime qualifications in source disclosure rather
      // than treating the generic scope note as a separate selectable branch.
      const binding=answer.source?.originalBinding?.c19_p1_1095_attack_families_binding || answer.source?.originalBinding?.c19_p2_type8_basic_attack_binding;
      const localBound=Boolean(binding && ['C19_P1_1095_ATTACK_FAMILIES_20261107','C19_P2_TYPE8_BASIC_ATTACK_20261107'].includes(binding.scope)
        && binding.scope===answer.source.evidenceScope && binding.row_id===row.id && binding.effect_id===effect.id
        && binding.rule_key===answer.source.rule && '/'+binding.slot===answer.source.field && binding.raw_value===answer.source.raw
        && answer.source.allSources?.row_fragment?.row_id===row.id && answer.source.allSources.row_fragment.japanese===row.original
        && /^自身/.test(answer.source.playerScope?.object || '') && answer.condition==='本能力生效时；具体适用条件见本句');
      let reason = '';
      if (effect.status !== 'has_answer') reason = '效果对应待核对';
      else if (answers.length !== 1) reason = '多个数值或分支仍需区分';
      else if (!['confirmed', 'inferred'].includes(answer.confidence)) reason = '数值或对应仍未确认';
      else if (answer.condition && !localBound || answer.branchLabel || answer.relatedDescription || /待核|待确认|推测|不明确/.test(answer.mappingNote || '')) reason = '另有适用条件或分支说明';
      else if (!pattern || row.translationStatus === 'pending' || row.translationNote) reason = '尚无可靠的句内位置';
      else if (effects.filter(e => e.label === effect.label).length !== 1) reason = '本句包含多个同类效果';
      const matches = reason ? [] : [...text.matchAll(pattern)];
      if (!reason && matches.length !== 1) reason = '中文位置不唯一';
      // Durations may refer to an attack interval instead of a buff. Damage
      // coefficients may belong to damage taken, echoes, or critical damage.
      if (!reason && effect.label === '持续时间' && /间隔|每隔|每过|每经过/.test(text)) reason = '持续时间与触发间隔需要区分';
      if (!reason && effect.label === '伤害' && /反响|暴击|受到|承受|减伤|伤害降低|伤害减少/.test(text)) reason = '伤害种类需进一步区分';
      if (reason) {
        // An effect-bound answer remains visible even when a branch or extra
        // condition prevents safe insertion into the sentence.
        (effect.status === 'has_answer' ? visible : held).push({ effect, reason }); return;
      }
      inserts.push({ end: matches[0].index + matches[0][0].length, effect, answer, text: compact(answer, effect.label) });
    });
    inserts.sort((a, b) => a.end - b.end);
    const answers = effects.flatMap(e => e.answers || []).concat(row.unboundAnswers || []);
    const hasStrengthBranch = answers.some(a => candidate(a) && (a.relatedDescription || /强化（推测）|Chain强化/.test(a.branchLabel || '')));
    const hasUncertainBranch = answers.some(candidate);
    const hasOtherBranch = answers.some(a => !a.displayAssessment && (a.branchLabel || a.relatedDescription));
    const strengthUnsolved = !(row.candidateLinks?.length || row.unmappedBranches?.length || answers.some(a=>a.branchCandidate)) && /效果(?:会)?(?:提高|上升|增加)|进一步|强化/.test(text) && effects.some(e => e.status === 'unresolved');
    const parallel=inserts.filter(entry=>entry.segments);
    const orders=parallel.map(entry=>entry.segments.map(segment=>segment.conditionLabel));
    const commonOrder=parallel.length && parallel.every(entry=>entry.segments.length>1 && entry.segments.every(segment=>segment.conditionKnown)) && orders.every(order=>JSON.stringify(order)===JSON.stringify(orders[0])) ? orders[0] : null;
    const knownCandidateConditions=row.linkedConditionsKnown || answers.filter(candidate).length>0 && answers.filter(candidate).every(answer=>answer.displayBranch?.conditionKnown);
    return { inserts, visible, held, valueOrder:commonOrder, knownCandidateConditions, branchLabel: hasStrengthBranch ? '强化分支待确认' : hasUncertainBranch ? '分支条件待确认' : hasOtherBranch ? '分支数值' : '', strengthUnsolved };
  }
  function semanticUnclear(answer) {
    return /用途待|原文存在矛盾|沙漠.*森林|无法确定.*效果/.test([answer.text,answer.condition,answer.mappingNote].join(' '));
  }
  function candidate(answer) {
    if(answer.displayAssessment?.status==='inferred')return false;
    return !semanticUnclear(answer) && Boolean(answer.branchCandidate || answer.relatedDescription || /待核|待确认|待核实|推测/.test([answer.branchLabel, answer.condition, answer.mappingNote].join(' ')));
  }
  function variantLabel(answer) {
    if (answer.branchCandidate) return answer.candidateLabel || '强化候选';
    if (answer.branchLabel === '通常伤害' && candidate(answer)) return '通常候选';
    if (answer.branchLabel === '1stChain强化（推测）') return '1stChain强化候选';
    if (/待核|待确认|有独立原文/.test(answer.branchLabel || '')) return '候选值';
    return answer.branchLabel || '';
  }
  const isProfile = skill => skill.sourceKind === 'character_profile' || ['共用描述','角色资料中的必杀说明'].includes(skill.stage);
  function skillIdentity(skill, skills) {
    if (!isProfile(skill)) {
      const resolved=skill.stage==='触发条件待核对' && skill.branchTable?.length && skill.branchTable.every(b=>b.conditionKnown) && skill.rows.some(r=>r.effects.some(e=>e.answers.some(a=>a.displayAssessment?.selectionResolved)));
      return {stage:resolved?'必杀技':skill.stage || '', note:''};
    }
    const original = (skill.rows || []).map(r => r.original).join('');
    const matches = skills.filter(s => s !== skill && !isProfile(s) && (s.rows || []).map(r=>r.original).join('') === original);
    const labels = [...new Set(matches.map(s=>s.stage).filter(Boolean))];
    return {stage:labels.length === 1 ? `${labels[0]} · 角色资料` : '角色资料中的必杀说明',
      note:labels.length ? `与「${labels.join(' / ')}」原文相同；此处保留角色资料中的数值对应记录。` : '来自角色资料；与各分支描述的对应关系仍需核对。'};
  }
  // Deduplicate presentation, not evidence. The original rows remain intact
  // in sourceRows and in the frozen data files. Conditions are NOT inferred
  // from equal prose or equal numbers.
  function answerKey(answer) {
    return JSON.stringify([answer.text, answer.confidence, answer.source?.field, answer.source?.raw, Boolean(answer.branchCandidate), answer.candidateLabel,
      answer.source?.branchId,answer.source?.branchId!=null ? answer.source?.layer : null,answer.source?.originalBinding?.pattern_id ?? answer.source?.originalBinding?.g1_b1_binding?.pattern_id]);
  }
  function mergeRow(base, incoming) {
    const sourceRows = base.sourceRows || [base];
    const effects = base.effects.map(e=>({...e, answers:[...e.answers]}));
    for (const other of incoming.effects) {
      const matches = effects.filter(e=>e.label === other.label);
      const incomingCount = incoming.effects.filter(e=>e.label === other.label).length;
      const known = new Set(matches.flatMap(e=>e.answers.map(answerKey)));
      const extra = other.answers.filter(a=>!known.has(answerKey(a))).map(a=>({...a, readerOrigin:'角色资料'}));
      if (matches.length === 1 && incomingCount === 1) {
        matches[0].answers.push(...extra);
        if (other.status === 'has_answer') matches[0].status = 'has_answer';
      } else if (extra.length || !matches.length) effects.push({...other, answers:extra});
    }
    const unboundAnswers = [...base.unboundAnswers];
    const unboundKeys = new Set(unboundAnswers.map(answerKey));
    for (const answer of incoming.unboundAnswers) {
      if (!unboundKeys.has(answerKey(answer))) { unboundAnswers.push({...answer,readerOrigin:'角色资料'}); unboundKeys.add(answerKey(answer)); }
    }
    return {...base, effects, unboundAnswers, sourceRows:[...sourceRows,incoming],
      aliasIds:[...(base.aliasIds || []),incoming.id], review:base.review || incoming.review,
      candidateLinks:[...(base.candidateLinks || []),...(incoming.candidateLinks || [])],
      knownCandidateScopes:[...(base.knownCandidateScopes || []),...(incoming.knownCandidateScopes || [])],
      candidateStatusText:base.candidateStatusText || incoming.candidateStatusText || '',
      unmappedBranches:[...(base.unmappedBranches || []),...(incoming.unmappedBranches || [])]};
  }
  function mergeGroups(groups) {
    return groups.map(group=>{
      const sourceSkills = group.skills;
      const replacements = new Map(), removed = new Set();
      for (const incoming of sourceSkills) {
        if (!isProfile(incoming) || !incoming.rows.length) continue;
        const originals = JSON.stringify(incoming.rows.map(r=>r.original));
        const matches = sourceSkills.filter(s=>!isProfile(s) && JSON.stringify(s.rows.map(r=>r.original)) === originals);
        if (matches.length !== 1) continue;
        const target = matches[0], base = replacements.get(target) || target;
        const rows = base.rows.map((row,i)=>mergeRow(row,incoming.rows[i]));
        const alias = new Map(incoming.rows.map((r,i)=>[r.id,rows[i].id]));
        const conditions = [...(base.conditions || (base.conditionRowId ? [base] : []))];
        for (const condition of incoming.conditions || (incoming.conditionRowId ? [incoming] : [])) {
          const id = alias.get(condition.conditionRowId);
          if (id && !conditions.some(c=>c.conditionRowId === id)) conditions.push({...condition,conditionRowId:id});
        }
        replacements.set(target,{...base,rows,conditions,mergedSourceCount:(base.mergedSourceCount || 0)+1});
        removed.add(incoming);
      }
      return {...group,skills:sourceSkills.filter(s=>!removed.has(s)).map(s=>replacements.get(s) || s)};
    });
  }
  const api = { plan, compact, semanticUnclear, candidate, variantLabel, skillIdentity, answerKey, reviewKey, mergeGroups, prepareSkill, orderGroups, describeBranches, orderedAnswers };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.CC_INLINE = api;
})(typeof window === 'object' ? window : globalThis);
