"""Explain existing branch associations without promoting runtime certainty.

Evidence: yg1_batch1_20261024/REVIEW_SOURCE.md sections 3–4; each
current answer's binding and note. Pattern order is never a game level.
"""
import re
import unicodedata


def condition_title(jp):
    """Classify an explicit condition in this sentence, never a pattern index."""
    jp=unicodedata.normalize('NFKC',jp)
    if re.search(r'(?:\d+(?:st|nd|rd|th)\s*Chain|Chain数).{0,12}(?:以上|以下|応じ|ほど|につき)', jp, re.I):
        return '连携强化条件'
    if re.search(r'地形.{0,24}(?:時|場合|中|応じ)', jp):
        if '夜' in jp:return '夜间强化条件'
        if '砂漠' in jp:return '沙漠强化条件'
        return '地形强化条件'
    if re.search(r'HP.{0,30}(?:以上|以下|少な|多い|低い|高い|満タン|応じ|割合)', jp, re.I):return '生命强化条件'
    if re.search(r'(?:止まっている|停止している).{0,20}(?:と|ほど|間)', jp):return '停止不动强化条件'
    if re.search(r'(?:所属|所属の|<[^>]+>).{0,60}(?:いると|いる場合|いる時|ほど|につき)', jp):return '所属与队伍强化条件'
    if re.search(r'自身(?:の場合|に対して|が.{0,24}(?:時|場合|いると))', jp):return '自身强化条件'
    if re.search(r'マナ.{0,24}(?:所持|以上|以下|多いほど|少ないほど|持っている|所持している)', jp):return '法珠强化条件'
    if re.search(r'(?:いると|いる場合|いる時|なると|するたび|した時|の時|の場合|ほど|に応じて)', jp):return '效果强化条件'
    return ''


def explain(view, answer, row, skill, copies):
    binding = answer.get('binding') or {}
    pid = binding.get('pattern_id')
    original_condition = str(answer.get('condition_label') or '')
    if pid is None or not re.search(r'pattern(?:id)?\d+\s*/\s*pattern', original_condition):
        return view
    raw = binding.get('conditions_raw') or {}
    context = row.get('context_text') or skill.get('original_text') or ''
    source = view['source']
    source.update({'originalBinding': binding, 'originalEffectBinding': answer.get('effect_binding'),
                   'originalContext': context})
    own_text = raw.get('sinfo') or (context if pid == skill.get('record_id') else '')
    view['condition'] = '触发条件待核实'
    title = condition_title(own_text)
    if title:
        view['branchLabel'] = title + ' · 对应待核对'
        view['mappingNote'] = '该分支原文含此条件；具体分支与强化效果的对应仍需核对。'
    elif '超共鳴必殺' in own_text:
        view['branchLabel'] = '超共鸣必杀'
        view['mappingNote'] = ''
    elif own_text:
        view['branchLabel'] = '有独立原文 · 条件待核对'
        view['mappingNote'] = '原文没有明确说明此分支的实际选用条件。'
    else:
        view['branchLabel'] = '另一分支 · 条件待确认'
        view['mappingNote'] = '该分支没有独立描述；它与本句的对应仍是推断。'

    # These two existing mainline answers explicitly disclose the inferred
    # same-skill/Chain association. Guard values; do not decode chs/che here.
    cid = row.get('cid')
    chain_ids = {350: (40035000, 40035001), 30337: (43033700, 43033701)}
    pair = chain_ids.get(cid)
    if pair and '1stChain以上' in context and pid in pair:
        enhanced = pid == pair[1]
        expected = {'chs': 2, 'che': 5, 'scost': 1} if enhanced else {'che': 1, 'scost': 2}
        if any(raw.get(k) != v for k, v in expected.items()):
            raise ValueError(f'连携分支条件已变化，需重核阅读标签：{cid}/{pid}')
        view['branchLabel'] = '1stChain强化（推测）' if enhanced else '通常伤害'
        if enhanced:
            view['mappingNote'] = '推测对应技能的Chain强化条件；此分支无独立正文。'
            related = next((r for r in skill['rows'] if '1stChain以上' in r['japanese']), None)
            if related:
                copy = copies.get(related['row_id'], '')
                text = copy.get('textZh') if isinstance(copy, dict) else copy
                view['relatedDescription'] = {'rowId': related['row_id'], 'text': text or '达到1st Chain或以上时的强化条件'}
        else:
            view['mappingNote'] = '对应首次范围伤害。'
    return view


def skill_label(skill):
    original = skill.get('original_text') or ''
    if '超共鳴必殺' in original:return '超共鸣必杀'
    if '共鳴必殺' in original:return '共鸣必杀'
    return '触发条件待核对'


def condition_context(skill):
    """Promote an explicit cross-effect sentence, not an inferred selector.

    Scope below comes from words in that sentence. It does not establish
    numerical multipliers or bind an absent branch to all preceding effects.
    """
    matches=[]
    for row in skill.get('rows', []):
        jp=row.get('japanese') or ''
        # These describe the *next* skill, not a modifier of preceding effects
        # in this skill. Keep them in their original row instead of promoting.
        if re.search(r'次に.{0,20}(?:使用|発動)|次の必殺',jp):continue
        if not re.search(r'(?:効果|(?<!クリティカル)威力|回復量).{0,18}が(?:一定時間)?(?:上が[るり]|高くな[るり]|強くな[るり]|増え[るり])', jp):continue
        title=condition_title(jp)
        if not title:continue
        scope=[label for token,label in [
            ('必要なマナ','法珠消耗'),('必殺技の威力','必杀威力'),
            ('反響の威力','反响威力'),('回復量','回复量'),
            ('味方にかかる効果','我方增益'),('敵と味方にかかる効果','敌方减益与我方增益')
        ] if token in jp]
        if '敌方减益与我方增益' in scope:
            scope=[s for s in scope if s!='我方增益']
        # "This effect becomes stronger" needs its preceding paragraph. Moving
        # it over every ◆ paragraph makes e.g. standing-still amplification look
        # as though it modifies starting mana as well. Keep such sentences in
        # their original position; only explicit cross-effect scope is promoted.
        if not scope or set(scope)=={'法珠消耗'}:continue
        matches.append({'conditionRowId':row['row_id'],'conditionTitle':title,
                        'conditionScopeText':('原文说明影响：'+'、'.join(scope)+'。各项强化数值分别核对，不共用一个倍率。') if scope else '作用范围见本条描述；具体数值分别核对',
                        'conditionScope':scope,'conditionScopeEvidence':'explicit_original_text'})
    return {'conditions': matches} if matches else {}
