"""Derive the isolated reader UI from the verified formal presentation template."""
from hashlib import sha256
import re
import shutil


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Reader template no longer matches: ' + old)
    return text.replace(old, new)


def build_frontend(SITE, LIVE, label):
    for name in ('index.html', 'app.js', 'inline.js'):
        shutil.copy2(LIVE/name, SITE/name)
    index = SITE/'index.html'
    text = index.read_text(encoding='utf-8')
    text = replace_once(text, '角色技能 · 数值阅读版', label)
    index.write_text(text, encoding='utf-8')
    app = SITE/'app.js'
    text = app.read_text(encoding='utf-8')
    text = replace_once(text, '  function image(src, alt, className = \'portrait\') {',
                        "  function image(src, alt, className = 'portrait') {\n"
                        "    if (src?.startsWith('../pages/art/')) src = '../../../../output/character_skills/' + src.slice(3);")
    text = replace_once(text, "reviewLink.href = 'audit/semantic_review.html';",
                        "reviewLink.href = 'pilot-report.html'; reviewLink.textContent = '查看同步对账与变动角色';")
    text = replace_once(text, 'map(skill=>window.CC_INLINE.prepareSkill(skill,window.CC_BRANCH_CONDITIONS?.records,window.CC_BRANCH_ASSESSMENTS?.records,window.CC_BRANCH_ASSESSMENTS?.resolvedParents))',
                        'map(skill=>window.CC_INLINE.hideSyncReplaced(window.CC_INLINE.prepareSkill(skill,window.CC_BRANCH_CONDITIONS?.records,window.CC_BRANCH_ASSESSMENTS?.records,window.CC_BRANCH_ASSESSMENTS?.resolvedParents)))')
    text = replace_once(text, 'row.translationStatus === \'pending\' || list(row.effects).some(isPending)',
                        "row.translationStatus === 'pending' || row.syncScopeGap || list(row.effects).some(isPending)")
    text = replace_once(text, '    if (pending.length) item.append', """    if (row.syncHpQualifier) {
      const link=button('对敌伤害的 HP 档位见上一句',event=>{
        event.currentTarget.dispatchEvent(new CustomEvent('reveal-description',{bubbles:true,detail:{rowId:row.syncHpQualifier}}));
      },'related-description');
      item.append(link);
    }
    if (pending.length && !row.syncHpQualifier) item.append""")
    text = replace_once(text, '    if (row.review) wrap.append', """    if (row.syncSplitFlags?.length) wrap.append(disclosure('同句待核对依据（JSON）',
      node('pre','source-json',JSON.stringify(row.syncSplitFlags,null,2))));
    if (row.review) wrap.append""")
    text = replace_once(text, '    if(scopeGaps.length)item.append', """    if (row.syncScopeGap) scopeGaps.push(row.syncScopeGap);
    if (row.syncExcluded) item.append(node('p','inline-missing',row.syncExcluded));
    if (row.syncFormalSplit) item.append(node('p','inline-missing',row.reviewMessage));
    if(scopeGaps.length)item.append""")
    app.write_text(text, encoding='utf-8')
    inline = SITE/'inline.js'
    text = inline.read_text(encoding='utf-8')
    text = replace_once(text, '      effect.answers.forEach((answer,index)=>{',
                        '      effect.answers.forEach((answer,index)=>{\n        if(answer.syncFormal)return;')
    text = replace_once(text, '      if(assignments.has(answer))return;',
                        '      if(answer.syncFormal || assignments.has(answer))return;')
    text = replace_once(text, 'const known = new Set(matches.flatMap(e=>e.answers.map(answerKey)));',
                        'const known = new Set(matches.flatMap(e=>e.answers.filter(a=>!a.syncFormal).map(answerKey)));')
    text = replace_once(text, '      const damageVariants =', """      const syncInline = effect.label === '伤害' && effect.status === 'has_answer'
        && answers.every(a=>a.syncFormal && a.displayBranch?.conditionKnown && ['inferred','confirmed'].includes(a.confidence))
        && row.translationStatus !== 'pending' && !row.translationNote && damageMatches.length === 1
        && effects.filter(e=>e.label==='伤害').length === 1
        && spans.every(span=>Array.isArray(span) && /ダメージ/.test((row.original || '').slice(span[0],span[1])));
      if (syncInline) {
        const segments=parallelValues(answers,'伤害');
        if (row.syncScopeGap) segments[0].text=segments[0].text.replace(/^系数/,'对敌系数');
        inserts.push({end:damageMatches[0].index+2,effect,answer,answers,text:segments.map(s=>s.text).join(' / '),segments});
        return;
      }
      const damageVariants =""")
    text = replace_once(text, '  const api = { plan,', """  function hideSyncReplaced(skill) {
    if (!skill.rows.some(row=>row.effects.some(e=>e.answers.some(a=>a.syncDisposition || a.syncFormal)))) return skill;
    const hide = row=>({...row,effects:row.effects.map(effect=>{
      const formal=effect.answers.filter(a=>a.syncFormal);
      const mirrors=a=>a.readerOrigin==='角色资料' && formal.some(b=>answerKey(a)===answerKey(b)
        && a.source.pointer===b.source.pointer && a.source.file===b.source.file);
      return {...effect,answers:effect.answers.filter(a=>!a.syncDisposition && !mirrors(a))};
    })});
    const excluded=new Set(skill.rows.flatMap(row=>row.effects.flatMap(e=>e.answers))
      .filter(a=>a.syncDisposition==='excluded_parent').map(a=>a.source.layer+':'+a.source.branchId));
    return {...skill,rows:skill.rows.map(row=>({...hide(row),
      ...(row.sourceRows ? {sourceRows:row.sourceRows.map(hide)} : {})})),
      ...(skill.branchTable ? {branchTable:skill.branchTable.map(branch=>excluded.has(branch.key)
        ? {...branch,conditionKnown:true,conditionLabel:'当前常规界面不选用'} : branch)} : {})};
  }
  const api = { hideSyncReplaced, plan,""")
    inline.write_text(text, encoding='utf-8')
    text = index.read_text(encoding='utf-8')
    text = re.sub(r'((?:src|href)=")([^"?]+\.(?:js|css))(?:\?v=[^"]+)?(")',
                  lambda match: f'{match[1]}{match[2]}?v={digest(SITE/match[2])[:12]}{match[3]}', text)
    index.write_text(text, encoding='utf-8')

