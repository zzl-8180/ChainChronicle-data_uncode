"""Generate the isolated C20 reader from reviewed C19 presentation and C20 evidence."""
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from html import escape
from pathlib import Path
import json
import re
import shutil

from build import dump, js, read, rows
from presentation import answer, num

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'output/character_skills'
LIVE = BASE / 'reader_full_20261106'
C20 = BASE / 'cycle_reports/C20_r02_20261109'
REVIEW = BASE / 'review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_r02_v01'
NAME = 'c20-sync-pilot-20261111'
SITE = ROOT / 'projects/reader/site' / NAME
REPORTS = ROOT / 'projects/reader/reports' / NAME
RUNTIME = ('index.html', 'app.js', 'branches.js', 'inline.js', 'levels.js', 'style.css')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def payload(path):
    delimiter = ']=' if path.parent.name == 'cards' else '='
    return json.loads(path.read_text(encoding='utf-8').split(delimiter, 1)[1].strip().removesuffix(';'))


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def selected_identity(addition, effect_id, selection):
    """Match a specific executor under a specific parent, including its selectors."""
    s = addition['answer']['source']
    t = selection['source']
    return (addition['effectId'] == effect_id
            and (s['layer'], s['branchId'], s['recordId'], s['rule'], s['field'], s['raw'], s['parentSlot'])
            == (t['layer'], selection['pattern_id'], selection['record_id'],
                selection['rule_key'], '/' + selection['field'], selection['raw_value'],
                'skillid' + str(selection['child_slot']))
            and s['allSources']['record_key'] == t['record_key']
            and s['parentSource']['source_key'] == t['source_key']
            and s['parentSource']['json_pointer'] == selection['pattern_json_pointer']
            and all(s['conditionsRaw'].get(k) == v for k, v in selection['parent_conditions_raw'].items())
            and s['conditionsRaw'][s['parentSlot']] == selection['record_id']
            and sha256(json.dumps(s['recordRaw'], ensure_ascii=False, sort_keys=True,
                                  separators=(',', ':')).encode()).hexdigest() == t['raw_record_sha256'])


def condition_label(a, proof):
    """Shorten C20's already established conditions for the sentence."""
    p = proof['selected']['parent_conditions_raw']
    model = proof['model']
    if model == 'HP_CHAIN':
        return f"HP {p['hpstart']}–{p['hpend']}%"
    if model == 'JOB_AFTER_COST':
        return f"预测扣费后职业法珠 {p['mns']}–{p['mne']} 颗"
    if model == 'SCRAP_BASE_SAME_VALUE':
        return '选档时废料 0–12 个'
    if model == 'SCRAP_TWO_TIER':
        return f"选档时废料 {p.get('mns', 0)}–{p['mne']} 个"
    if model == 'TERRAIN_SHARED':
        return '基础档／森林（含夜间，限本控制器前3次）'
    if model == 'USE_ONCE_NORMAL':
        return a['condition_label'].split('；')[0].replace('当前同一控制器', '本控制器')
    if model == 'CURRENT_SUPER_UI':
        return '超共鸣当前选档'
    assert model == 'DIRECT', model
    if '未设置Chain区间条件' in a['condition_label']:
        return '当前基础档'
    return a['condition_label'].split('；')[0].removeprefix('仅').removesuffix('被选中时').replace('（通常）', '').replace('当前档', '档')


def split_notes(flags):
    detail = '、'.join(d.get('word') or d.get('text', '') for f in flags for d in f['detail'])
    return [cn for jp, cn in [('弾き飛ば', '击飞'), ('転倒', '击倒'), ('ダウン', '眩晕'),
                             ('暗闇', '暗盲'), ('スロウ', '缓速')] if jp in detail]


def build_pilot():
    assert not SITE.exists() and not REPORTS.exists(), 'Use a fresh pilot destination'
    formal_snapshot = read(BASE/'effect_ledger/metrics.json')['snapshot']
    m = read(C20/'final_manifest.json')
    v = read(REVIEW/'verdict.json')
    assert v['f01_status'] == 'CLOSED' and v['verdict'] == 'PASS_WITH_EXPLICIT_SCOPE_LIMITS'
    assert v['submitted_manifest_sha256'] == digest(C20/'final_manifest.json')
    assert (formal_snapshot['snapshot_id'], formal_snapshot['campaign_signature']) == (m['snapshot'], m['campaign'])
    for name in ('report_data.json', 'answer_ledger.json'):
        assert digest(C20/name) == m['files'][name]['sha256'], name
    assert digest(BASE/'profiles/rules.json')[:16] == formal_snapshot['rules_json_sha256_16']
    accepted = {r['row_id']: r for batch in read(C20/'report_data.json')['batch_results'] for r in batch['rows']}
    identities = Counter((x['row_id'], x['answer_branch_pattern_id'], x['answer_record_id'], x['raw_value'])
                         for x in read(C20/'answer_ledger.json')['items'])
    assert len(accepted) == 18 and sum(identities.values()) == 25
    cids = {str(r['cid']) for r in accepted.values()}
    assert len(cids) == 16
    web = read(LIVE/'build_receipt.json')
    assert web['snapshot']['snapshot_id'] == '99bee2a1-cf9451c6ff47fcfb'
    cards = {cid: payload(LIVE/'data/cards'/f'{cid}.js') for cid in cids}
    web_rows = {r['id']: r for card in cards.values() for r in rows(card)}
    upstream = {}
    source_hashes = {}
    for cid, old_hash in web['sourceHashes'].items():
        path = BASE/'pages'/cid/'card.json'
        raw = path.read_bytes()
        source_hashes[cid] = sha256(raw).hexdigest()
        if cid in cids:
            upstream.update({r['row_id']: r for r in rows(json.loads(raw))})
    assert {cid for cid in source_hashes if source_hashes[cid] != web['sourceHashes'][cid]} == cids
    old_cards = deepcopy(cards)

    desc, effects, counts = {}, {}, defaultdict(Counter)
    with (BASE/'effect_ledger/ledger.jsonl').open(encoding='utf-8') as ledger:
        for line in ledger:
            e = json.loads(line)
            assert (e.get('snapshot_id') or e.get('input_snapshot', {}).get('snapshot_id')) == m['snapshot']
            cid = str(e['cid'])
            if e['record_type'] == 'description':
                counts[cid][{'完整':'complete', '部分':'partial', '未解析':'unparsed',
                             '拆分待核查':'review'}[e['ledger_row_status']]] += 1
                if e['row_id'] in accepted:
                    desc[e['row_id']] = e
            elif e['record_type'] == 'effect':
                if e['status'] in ('has_answer', 'unresolved'):
                    counts[cid]['answer' if e['status'] == 'has_answer' else 'unresolved'] += 1
                if e['description_ref'] in accepted:
                    effects[e['effect_id']] = e

    overlay = payload(LIVE/'data/branch_candidates.js')
    old_overlay = deepcopy(overlay)
    adopted, decisions, ambiguities, unknowns = [], [], [], []
    expected_additions = defaultdict(list)
    for rid, item in accepted.items():
        cid = str(item['cid'])
        before, after = item['before'], item['after']
        row = web_rows[rid]
        assert after == upstream[rid] and row['original'] == after['japanese'] == desc[rid]['japanese']
        state_fields = {'answers', 'association_evidence', 'numeric_evidence', 'unknown_reasons',
                        'evidence_scope', 'row_class', 'partial', 'inference_yg1',
                        'inference_c20_p1_yg_direct_damage', 'inference_c20_p2_nonyg_direct_damage'}
        assert {k:v for k,v in before.items() if k not in state_fields} == \
            {k:v for k,v in after.items() if k not in state_fields}, rid
        assert after['answers'][:len(before['answers'])] == before['answers']
        assert sorted(a['source']['answerIndex'] for e in row['effects'] for a in e['answers']) + \
            sorted(a['source']['answerIndex'] for a in row['unboundAnswers']) == list(range(len(before['answers'])))
        patch = overlay['cards'].get(cid, {}).get('rows', {}).get(rid, {})
        remaining = list(patch.get('additions', []))
        flag_records = item['row_split_flags']
        assert flag_records == desc[rid]['split_flags']
        notes = split_notes(flag_records)
        assert not flag_records or notes
        if notes:
            row['review'] = True
            row['c20FormalSplit'] = True
            row['c20SplitFlags'] = flag_records
            row['reviewMessage'] = '同句待核对：' + '、'.join(notes)
        if cid == '20332':
            row['c20ScopeGap'] = '自身受到的伤害数值尚未解出'
            ambiguities.append({'cid':cid, 'rowId':rid, 'issue':row['c20ScopeGap'],
                                'decision':'仅将正式系数标在对敌伤害；同句自伤和后续周期伤害不套用'})
        unknowns.append({'cid':cid, 'rowId':rid, 'splitFlags':flag_records,
                         'unresolvedEffects':item['unresolved_effects'], 'scopeGap':row.get('c20ScopeGap')})
        for idx, a in enumerate(after['answers'][len(before['answers']):], len(before['answers'])):
            proof = next(value for key, value in a['binding'].items() if key.startswith('c20_'))
            eid = proof['effect_id']
            ledger_effect = effects[eid]
            e = next(e for e in row['effects'] if e['id'] == eid)
            assert (proof['row_id'], proof['runtime_verified'], ledger_effect['status'], e['label']) == (rid, False, 'has_answer', '伤害')
            assert ledger_effect['span'] == a['effect_binding']['span']
            start, end = ledger_effect['span']
            assert row['original'][start:end] == ledger_effect['snippet'] == 'ダメージ'
            assert [(r['rule_key'], r['field_path'], r['raw_value'], r['condition_label'])
                    for r in ledger_effect['answer_refs'] if r['answer_index'] == idx] == [
                (a['rule_key'], a['field_path'], a['raw_value'], a['condition_label'])]
            selected = proof['selected']
            identity = (rid, selected['pattern_id'], a['record_id'], a['raw_value'])
            assert identities[identity] == 1
            identities[identity] -= 1
            assert selected['source'] == a['source'] and a['binding']['pattern_id'] == selected['pattern_id']
            view = answer(a, cid=int(cid), original=row['original'])
            assert view['confidence'] == 'inferred' and view['text'] == f"伤害系数 {num(a['raw_value'])}倍"
            view.update(condition=a['condition_label'], c20Formal=True, readerOrigin='C20 正式答案')
            view['source'].update(rowId=rid, effectId=eid, answerIndex=idx, playerScope=a['player_scope'],
                                  originalPlayerText=a['player_text'], notIncluded=a.get('not_included'))
            view['displayBranch'] = {'key':f"C20:{a['layer']}:{selected['pattern_id']}",
                                     'conditionKnown':True, 'conditionLabel':condition_label(a, proof),
                                     'order':idx}
            branches = []
            for kind, selection, reason in [
                ('same_parent', selected, '同一效果、父分支、执行槽、规则、来源与原值'),
                *[('merged_parent', x['selection'], x['reason']) for x in proof['merged_disclosures']],
                *[('excluded_parent', x['selection'], x['reason']) for x in proof['excluded_branch_values']],
            ]:
                same = [x for x in remaining if selected_identity(x, eid, selection)]
                assert len(same) <= 1
                if same:
                    old = same[0]
                    remaining.remove(old)
                    decision = {'cid':cid, 'rowId':rid, 'effectId':eid, 'kind':kind,
                                'branchId':selection['pattern_id'], 'recordId':selection['record_id'],
                                'raw':selection['raw_value'], 'reason':reason, 'oldCandidate':deepcopy(old)}
                    # Prepare the original branch table first. Then hide only
                    # the superseded candidate values in the sentence.
                    old['answer']['c20Disposition'] = kind
                    decisions.append(decision)
                    branches.append(decision)
                    if kind == 'excluded_parent':
                        row['c20Excluded'] = f"旧候选 {num(selection['raw_value'])}倍：当前常规界面不选用"
                        ambiguities.append({**{k:v for k,v in decision.items() if k != 'oldCandidate'},
                                            'decision':'保留旧候选及来源，单独显示为当前模式未选用'})
            view['source']['c20PreviousCandidates'] = branches
            e['answers'].append(view)
            e['status'] = 'has_answer'
            expected_additions[(rid,eid)].append(view)
            adopted.append({'cid':cid, 'rowId':rid, 'effectId':eid, 'answerIndex':idx,
                            'branchId':selected['pattern_id'], 'source':a['source'],
                            'raw':a['raw_value'], 'confidence':view['confidence'], 'condition':a['condition_label']})
        for other in remaining:
            ambiguities.append({'cid':cid, 'rowId':rid, 'issue':'旧候选未通过精确等价检查',
                                'decision':'保留原候选', 'candidate':other})
    hp_rows = next(s['rows'] for g in cards['20332']['groups'] for s in g['skills']
                   if any(r.get('c20ScopeGap') for r in s['rows']))
    hp_row = next(r for r in hp_rows if r.get('c20ScopeGap'))
    qualifier = hp_rows[hp_rows.index(hp_row)+1]
    assert qualifier['original'] == 'ダメージ量は自身の残りHP量に応じて変化する。'
    qualifier['c20HpQualifier'] = hp_row['id']
    assert not +identities and len(adopted) == 25 and len(expected_additions) == 18
    assert Counter(x['kind'] for x in decisions) == {'same_parent':15, 'merged_parent':6, 'excluded_parent':1}
    assert sum(len(x['splitFlags']) for x in unknowns) == 21
    assert sum(bool(x['splitFlags']) for x in unknowns) == 15
    for cid, old in old_cards.items():
        new = deepcopy(cards[cid])
        for r in rows(new):
            old_row = next(o for o in rows(old) if o['id'] == r['id'])
            for e, old_effect in zip(r['effects'], old_row['effects'], strict=True):
                additions = expected_additions.get((r['id'],e['id']), [])
                assert e['answers'] == old_effect['answers'] + additions
                if additions:
                    e['answers'] = old_effect['answers']
                    e['status'] = old_effect['status']
            for key in ('review', 'reviewMessage', 'c20FormalSplit', 'c20SplitFlags',
                        'c20ScopeGap', 'c20Excluded', 'c20HpQualifier'):
                if key in old_row:
                    r[key] = old_row[key]
                else:
                    r.pop(key, None)
        assert old == new, cid
    check_overlay = deepcopy(overlay)
    annotated = 0
    for card in check_overlay['cards'].values():
        for patch in card['rows'].values():
            for item in patch.get('additions', []):
                annotated += item['answer'].pop('c20Disposition', None) is not None
    assert annotated == len(decisions) and old_overlay == check_overlay

    catalog = payload(LIVE/'data/catalog.js')
    metrics = read(BASE/'effect_ledger/metrics.json')
    assert metrics['snapshot'] == formal_snapshot
    assert set(counts) == {str(card['cid']) for card in catalog['cards']}
    for card in catalog['cards']:
        n = counts[str(card['cid'])]
        new = {k:n[k] for k in card['counts'] if k != 'descriptions'}
        new['descriptions'] = sum(n[k] for k in ('complete','partial','unparsed','review'))
        if str(card['cid']) not in cids:
            assert new == card['counts']
        card['counts'] = new
        card['status'] = ('全部描述完整' if new['complete'] == new['descriptions'] else
                          '已有部分答案' if new['answer'] else '暂无效果答案')
    for key, status in [('answer','has_answer'), ('unresolved','unresolved')]:
        assert sum(c['counts'][key] for c in catalog['cards']) == metrics['effects']['by_status'][status]['all']
    catalog['summary'].update(withAnswer=sum(bool(c['counts']['answer']) for c in catalog['cards']),
                              noAnswer=sum(not c['counts']['answer'] for c in catalog['cards']),
                              complete=sum(c['counts']['complete']==c['counts']['descriptions'] for c in catalog['cards']))
    catalog['meta'].update(snapshot=m['snapshot'], acceptedCycle='C20 隔离试点', updated=metrics['generated_at'])

    SITE.mkdir()
    REPORTS.mkdir(parents=True)
    shutil.copytree(LIVE/'data', SITE/'data', copy_function=shutil.copy2)
    for name in RUNTIME:
        shutil.copy2(LIVE/name, SITE/name)
    for cid, card in cards.items():
        content = json.dumps(card, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('</','<\\/')
        (SITE/'data/cards'/f'{cid}.js').write_text(f'window.CC_DETAILS=window.CC_DETAILS||{{}};window.CC_DETAILS["{cid}"]={content};\n', encoding='utf-8')
    js(SITE/'data/catalog.js','CC_CATALOG',catalog)
    js(SITE/'data/branch_candidates.js','CC_BRANCH_CANDIDATES',overlay)
    build_frontend()
    for cid,h in source_hashes.items():
        assert digest(BASE/'pages'/cid/'card.json') == h, cid
        if cid not in cids:
            assert digest(SITE/'data/cards'/f'{cid}.js') == digest(LIVE/'data/cards'/f'{cid}.js'), cid
    assert read(BASE/'effect_ledger/metrics.json')['snapshot'] == formal_snapshot
    result = {'pass':True, 'baseSnapshot':web['snapshot']['snapshot_id'], 'snapshot':m['snapshot'],
              'cards':len(cids), 'rows':len(accepted), 'answers':adopted, 'candidateDecisions':decisions,
              'ambiguities':ambiguities, 'sameSentenceUnknowns':unknowns,
              'scope':'C20 delta applied to C19 R01 presentation; existing C19 sidecar assessments keep original provenance',
              'inputs':{str(p.relative_to(ROOT)):digest(p) for p in
                        (C20/'final_manifest.json', C20/'answer_ledger.json', C20/'report_data.json',
                         REVIEW/'verdict.json', LIVE/'build_receipt.json', LIVE/'data/branch_candidates.js')}}
    dump(REPORTS/'reconciliation.json', result)
    return result


def build_frontend():
    for name in ('index.html', 'app.js', 'inline.js'):
        shutil.copy2(LIVE/name, SITE/name)
    index = SITE/'index.html'
    text = index.read_text(encoding='utf-8')
    text = replace_once(text, '角色技能 · 数值阅读版', 'C20 隔离试点')
    index.write_text(text, encoding='utf-8')
    app = SITE/'app.js'
    text = app.read_text(encoding='utf-8')
    text = replace_once(text, '  function image(src, alt, className = \'portrait\') {',
                        "  function image(src, alt, className = 'portrait') {\n"
                        "    if (src?.startsWith('../pages/art/')) src = '../../../../output/character_skills/' + src.slice(3);")
    text = replace_once(text, "reviewLink.href = 'audit/semantic_review.html';",
                        "reviewLink.href = 'pilot-report.html'; reviewLink.textContent = '查看 C20 试点对账与变动角色';")
    text = replace_once(text, 'map(skill=>window.CC_INLINE.prepareSkill(skill,window.CC_BRANCH_CONDITIONS?.records,window.CC_BRANCH_ASSESSMENTS?.records,window.CC_BRANCH_ASSESSMENTS?.resolvedParents))',
                        'map(skill=>window.CC_INLINE.hideC20Replaced(window.CC_INLINE.prepareSkill(skill,window.CC_BRANCH_CONDITIONS?.records,window.CC_BRANCH_ASSESSMENTS?.records,window.CC_BRANCH_ASSESSMENTS?.resolvedParents)))')
    text = replace_once(text, 'row.translationStatus === \'pending\' || list(row.effects).some(isPending)',
                        "row.translationStatus === 'pending' || row.c20ScopeGap || list(row.effects).some(isPending)")
    text = replace_once(text, '    if (pending.length) item.append', """    if (row.c20HpQualifier) {
      const link=button('对敌伤害的 HP 档位见上一句',event=>{
        event.currentTarget.dispatchEvent(new CustomEvent('reveal-description',{bubbles:true,detail:{rowId:row.c20HpQualifier}}));
      },'related-description');
      item.append(link);
    }
    if (pending.length && !row.c20HpQualifier) item.append""")
    text = replace_once(text, '    if (row.review) wrap.append', """    if (row.c20SplitFlags?.length) wrap.append(disclosure('同句待核对依据（JSON）',
      node('pre','source-json',JSON.stringify(row.c20SplitFlags,null,2))));
    if (row.review) wrap.append""")
    text = replace_once(text, '    if(scopeGaps.length)item.append', """    if (row.c20ScopeGap) scopeGaps.push(row.c20ScopeGap);
    if (row.c20Excluded) item.append(node('p','inline-missing',row.c20Excluded));
    if (row.c20FormalSplit) item.append(node('p','inline-missing',row.reviewMessage));
    if(scopeGaps.length)item.append""")
    app.write_text(text, encoding='utf-8')
    inline = SITE/'inline.js'
    text = inline.read_text(encoding='utf-8')
    text = replace_once(text, '      effect.answers.forEach((answer,index)=>{',
                        '      effect.answers.forEach((answer,index)=>{\n        if(answer.c20Formal)return;')
    text = replace_once(text, '      if(assignments.has(answer))return;',
                        '      if(answer.c20Formal || assignments.has(answer))return;')
    text = replace_once(text, 'const known = new Set(matches.flatMap(e=>e.answers.map(answerKey)));',
                        'const known = new Set(matches.flatMap(e=>e.answers.filter(a=>!a.c20Formal).map(answerKey)));')
    text = replace_once(text, '      const damageVariants =', """      const c20Inline = effect.label === '伤害' && effect.status === 'has_answer'
        && answers.every(a=>a.c20Formal && a.displayBranch?.conditionKnown && a.confidence==='inferred')
        && row.translationStatus !== 'pending' && !row.translationNote && damageMatches.length === 1
        && effects.filter(e=>e.label==='伤害').length === 1
        && spans.every(span=>Array.isArray(span) && /ダメージ/.test((row.original || '').slice(span[0],span[1])));
      if (c20Inline) {
        const segments=parallelValues(answers,'伤害');
        if (row.c20ScopeGap) segments[0].text=segments[0].text.replace(/^系数/,'对敌系数');
        inserts.push({end:damageMatches[0].index+2,effect,answer,answers,text:segments.map(s=>s.text).join(' / '),segments});
        return;
      }
      const damageVariants =""")
    text = replace_once(text, '  const api = { plan,', """  function hideC20Replaced(skill) {
    if (!skill.rows.some(row=>row.effects.some(e=>e.answers.some(a=>a.c20Disposition || a.c20Formal)))) return skill;
    const hide = row=>({...row,effects:row.effects.map(effect=>{
      const formal=effect.answers.filter(a=>a.c20Formal);
      const mirrors=a=>a.readerOrigin==='角色资料' && formal.some(b=>answerKey(a)===answerKey(b)
        && a.source.pointer===b.source.pointer && a.source.file===b.source.file);
      return {...effect,answers:effect.answers.filter(a=>!a.c20Disposition && !mirrors(a))};
    })});
    const excluded=new Set(skill.rows.flatMap(row=>row.effects.flatMap(e=>e.answers))
      .filter(a=>a.c20Disposition==='excluded_parent').map(a=>a.source.layer+':'+a.source.branchId));
    return {...skill,rows:skill.rows.map(row=>({...hide(row),
      ...(row.sourceRows ? {sourceRows:row.sourceRows.map(hide)} : {})})),
      ...(skill.branchTable ? {branchTable:skill.branchTable.map(branch=>excluded.has(branch.key)
        ? {...branch,conditionKnown:true,conditionLabel:'当前常规界面不选用'} : branch)} : {})};
  }
  const api = { hideC20Replaced, plan,""")
    inline.write_text(text, encoding='utf-8')
    text = index.read_text(encoding='utf-8')
    text = re.sub(r'((?:src|href)=")([^"?]+\.(?:js|css))(?:\?v=[^"]+)?(")',
                  lambda match: f'{match[1]}{match[2]}?v={digest(SITE/match[2])[:12]}{match[3]}', text)
    index.write_text(text, encoding='utf-8')


def report_page(result):
    cards = list(dict.fromkeys(a['cid'] for a in result['answers']))
    links = ' '.join(f'<a href="index.html#card={cid}">{cid}</a>' for cid in cards)
    lines = ''.join(f"<li>CID {x['cid']}：{escape(x.get('decision',''))}</li>" for x in result['ambiguities'])
    (SITE/'pilot-report.html').write_text(f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>C20 试点对账</title>
<link rel="stylesheet" href="style.css"><main id="main"><p><a href="index.html">返回试点首页</a></p>
<h1>C20 试点对账</h1><p>16 张角色卡，18 条描述，25 条正式答案。</p>
<p>15 条同父候选由正式答案接替。6 个不同父分支按 C20 证据合记并保留来源。
1 个旧候选保留为当前模式未选用。</p><p>变动角色：{links}</p>
<h2>单独保留的范围</h2><ul>{lines}</ul></main></html>""", encoding='utf-8')


if __name__ == '__main__':
    result = build_pilot()
    report_page(result)
    print(json.dumps({'site':str(SITE), 'report':str(REPORTS/'reconciliation.json'),
                      'formalAnswers':len(result['answers']),
                      'decisions':dict(Counter(x['kind'] for x in result['candidateDecisions']))}, ensure_ascii=False))
