"""YG1 batch 2: bounded type-55/74 formulas from resolved CACHE patterns.

Formula evidence comes from the native type interpreters.  A formula branch is
selected only through a real Y.G. charainfo -> bosspattern -> bossskill edge; the
actual skill body must contain one resonance header and one type-specific enemy
damage phrase.  Header and phrase may live in different description fragments.
No interval, hit-count, final-HP, or resonance-resolution claim is made here.
"""
import copy
import math
import re
import struct

SCOPE = 'YG1_BATCH2_FORMULA_ONLY'
BATCH1_SCOPE = 'YG1_BATCH1_FORMULA_ONLY'
BATCH1_TARGETS = {
    349: dict(type=55, field='skillparam1', quantity='激光伤害输入倍率'),
    350: dict(type=74, field='skillparam5', quantity='直接范围伤害输入倍率'),
}
FORMULAS = {
    55: dict(field='skillparam1', quantity='激光伤害输入倍率'),
    74: dict(field='skillparam5', quantity='直接范围伤害输入倍率'),
}
TEXT_PHRASES = {
    55: ('直線範囲上にいる全ての敵に一定間隔でダメージを与え',),
    74: ('前方範囲内の全ての敵に大ダメージを与え',
         '自身中心範囲内の全ての敵に大ダメージを与え'),
}
CONDITION_KEYS = ('flag', 'chs', 'che', 'hpstart', 'hpend', 'bgf', 'priority', 'scost')
PATTERN_REF = re.compile(r'^pattern\d+$')
HEADER_RE = re.compile(r'【(?:超)?共鳴必殺[^】]*】')
DAMAGE = 'ダメージ'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'
FLOAT_MIN_NORMAL = struct.unpack('>f', bytes.fromhex('00800000'))[0]


def _same_slots(chara, record):
    types = chara.get('skillid')
    return (isinstance(types, list) and bool(types)
            and types[0] == record.get('skillid0')
            and all((k in chara, chara.get(k)) == (k in record, record.get(k))
                    for k in (f'skillparam{i}' for i in range(10))))


def _domain_source(data, cid, include_non_yg):
    title = str((data.profiles.get(cid) or {}).get('title') or '')
    is_yg = 'Y.G.' in title
    if is_yg:
        return 'YG_TITLE_CONTAINS_YG', is_yg
    if include_non_yg:
        return 'NON_YG_TEST_CONTROL', is_yg
    return 'NON_YG_NOT_SELECTED', is_yg


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _parent_issues(data, chara, entries, entry):
    ref = entry.get('reference_field')
    reference_id = entry.get('reference_id')
    if (entry.get('table') != 'bosspattern' or entry.get('layer') != 'CACHE'
            or not isinstance(ref, str) or not PATTERN_REF.fullmatch(ref)):
        return ['PARENT_NAMESPACE_OR_FIELD']
    issues = []
    if not _is_int(reference_id):
        issues.append('PARENT_REFERENCE_ID_INVALID')
    if sum(e.get('reference_field') == ref for e in entries) != 1:
        issues.append('PARENT_FIELD_NOT_UNIQUE')
    pattern_refs = [k for k in chara if isinstance(k, str) and PATTERN_REF.fullmatch(k)]
    if ref not in chara or chara.get(ref) != reference_id:
        issues.append('PARENT_RAW_REFERENCE_MISMATCH')
    if sum(chara.get(k) == reference_id for k in pattern_refs) != 1:
        issues.append('PARENT_REFERENCE_ID_NOT_UNIQUE')
    record = entry.get('record')
    if (not isinstance(record, dict) or record.get('patternid') != reference_id):
        issues.append('PARENT_RECORD_ID_MISMATCH')
    try:
        source = data.precise_source(entry)
    except (KeyError, TypeError, ValueError):
        source = {}
    if source.get('source_resolution') != EXACT:
        issues.append('PARENT_SOURCE_NOT_EXACT_CACHE')
    return issues


def _float32(value):
    return struct.unpack('>f', struct.pack('>f', float(value)))[0]


def _formula_value_issues(typ, value):
    if value is None:
        return ['FORMULA_VALUE_NULL']
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ['FORMULA_VALUE_NOT_NUMERIC']
    try:
        fv = _float32(value)
    except (OverflowError, struct.error, ValueError, TypeError):
        return ['FORMULA_VALUE_NOT_FLOAT32_FINITE']
    if not math.isfinite(fv):
        return ['FORMULA_VALUE_NOT_FLOAT32_FINITE']
    if typ == 55:
        return [] if fv >= 0 else ['FORMULA_VALUE_NEGATIVE']
    if fv <= 0:
        return ['FORMULA_VALUE_NOT_POSITIVE']
    if fv <= FLOAT_MIN_NORMAL:
        return ['FORMULA_VALUE_TINY_POSITIVE_BELOW_FLOAT_MIN_NORMAL']
    return []


def _child_issues(data, entry, child, typ):
    formula = FORMULAS[typ]
    pattern = entry.get('record') or {}
    reference_id = entry.get('reference_id')
    prefix = f'bosspattern[{reference_id}].skillid'
    field = child.get('reference_field')
    child_id = child.get('reference_id')
    record = child.get('record') or {}
    issues = []
    if child.get('table') != 'bossskill' or child.get('layer') != 'CACHE':
        issues.append('CHILD_NAMESPACE')
    if not _is_int(child_id):
        issues.append('CHILD_REFERENCE_ID_INVALID')
    refs = entry.get('boss_skill_refs') or []
    edge_key = (child.get('table'), child.get('layer'), field, child_id)
    if sum((e.get('table'), e.get('layer'), e.get('reference_field'), e.get('reference_id')) == edge_key
           for e in refs) != 1:
        issues.append('CHILD_PARENT_EDGE_NOT_UNIQUE')
    if (not isinstance(field, str) or not field.startswith(prefix)
            or not field[len(prefix):].isdigit()):
        return issues + ['CHILD_PARENT_EDGE']
    slot_text = field[len(prefix):]
    slot = int(slot_text)
    if slot_text != str(slot) or slot not in range(10):
        issues.append('CHILD_PARENT_EDGE')
    if slot not in range(10) or pattern.get(f'skillid{slot}') != child_id:
        issues.append('CHILD_PARENT_SLOT_MISMATCH')
    if record.get('skillid') != child_id:
        issues.append('CHILD_RECORD_ID_MISMATCH')
    if record.get('skillid0') != typ:
        issues.append('CHILD_TYPE_MISMATCH')
    try:
        source = data.precise_source(child)
    except (KeyError, TypeError, ValueError):
        source = {}
    if source.get('source_resolution') != EXACT:
        issues.append('CHILD_SOURCE_NOT_EXACT_CACHE')
    if formula['field'] not in record:
        issues.append('FORMULA_VALUE_MISSING')
    else:
        issues.extend(_formula_value_issues(typ, record.get(formula['field'])))
    return list(dict.fromkeys(issues))


def _branch_key(branch):
    return (branch['pattern_id'], branch['child_id'], branch['type'],
            branch['slot'], branch['field'])


def _collect(data, cid, include_non_yg=False):
    domain_source, is_yg = _domain_source(data, cid, include_non_yg)
    report = dict(domain=is_yg or include_non_yg, domain_source=domain_source,
                  branches=[], rejections=[], types=[])
    if not report['domain']:
        report['rejections'].append(dict(reasons=['NON_YG_DOMAIN_NOT_ENABLED']))
        return report
    linked = next((g for g in data.links[cid]['groups']
                   if g.get('group') == 'special_move'), {})
    entries = linked.get('records', [])
    chara = data.cache_chara.get(cid, {})
    for entry in entries:
        if entry.get('table') != 'bosspattern':
            continue
        ref = entry.get('reference_field')
        parent_issues = _parent_issues(data, chara, entries, entry)
        if parent_issues:
            report['rejections'].append(dict(
                pattern_ref=ref, pattern_id=entry.get('reference_id'),
                reasons=parent_issues))
            continue
        typed_children = []
        for child in entry.get('boss_skill_refs', []):
            record = child.get('record') or {}
            typ = record.get('skillid0')
            if typ in FORMULAS:
                typed_children.append((child, typ))
        if not typed_children:
            report['rejections'].append(dict(
                pattern_ref=ref, pattern_id=entry.get('reference_id'),
                reasons=['NO_FORMULA_TYPED_CHILD']))
            continue
        for child, typ in typed_children:
            issues = _child_issues(data, entry, child, typ)
            if issues:
                report['rejections'].append(dict(
                    pattern_ref=ref, pattern_id=entry.get('reference_id'),
                    child_id=child.get('reference_id'), type=typ, reasons=issues))
                continue
            pattern = entry['record']
            record = child['record']
            formula = FORMULAS[typ]
            prefix = f"bosspattern[{entry['reference_id']}].skillid"
            child_source = copy.deepcopy(data.precise_source(child))
            child_source.update(table='bossskill', record_id=child['reference_id'],
                                layer='CACHE', field_path='/' + formula['field'])
            branch = dict(
                type=typ, field=formula['field'], quantity=formula['quantity'],
                slot=int(child['reference_field'][len(prefix):]),
                reference_field=ref, pattern_id=entry['reference_id'],
                child_id=child['reference_id'], record=record, pattern=pattern,
                source=child_source,
                pattern_source=copy.deepcopy(data.precise_source(entry)),
                conditions_raw=copy.deepcopy(pattern),
                raw_value=record.get(formula['field']))
            report['branches'].append(branch)
    report['branches'].sort(key=lambda b: (
        int(str(b['reference_field'])[7:]) if str(b['reference_field'])[7:].isdigit() else 999,
        b['type'], b['slot'], b['pattern_id']))
    report['types'] = sorted({b['type'] for b in report['branches']})
    return report


def _scan_skill_body(skill, typ):
    rows = [r for r in (skill.get('rows') or []) if isinstance(r, dict)]
    if not rows:
        return None, ['TEXT_CARRIER_NO_ROWS']
    texts = [str(r.get('japanese') or '') for r in rows]
    body = '\n'.join(texts)
    headers = list(HEADER_RE.finditer(body))
    if not headers:
        return None, ['RESONANCE_HEADER_MISSING']
    if len(headers) != 1:
        return None, ['RESONANCE_HEADER_NOT_UNIQUE']
    occurrences = []
    phrase_text = None
    for phrase in TEXT_PHRASES[typ]:
        start = 0
        while True:
            at = body.find(phrase, start)
            if at < 0:
                break
            occurrences.append((at, phrase))
            start = at + len(phrase)
    if not occurrences:
        return None, ['DAMAGE_PHRASE_MISSING']
    if len(occurrences) != 1:
        return None, ['DAMAGE_PHRASE_NOT_UNIQUE']
    phrase_at, phrase_text = occurrences[0]
    if headers[0].start() > phrase_at:
        return None, ['HEADER_AFTER_DAMAGE_PHRASE']
    carriers = []
    for index, text in enumerate(texts):
        local = text.find(phrase_text)
        if local >= 0:
            carriers.append((index, local))
    if len(carriers) != 1:
        return None, ['DAMAGE_PHRASE_NOT_SINGLE_ROW_CARRIER']
    row_index, local = carriers[0]
    damage_local = local + phrase_text.index(DAMAGE)
    return dict(row=rows[row_index], row_index=row_index,
                span=(damage_local, damage_local + len(DAMAGE)),
                phrase=phrase_text, header=headers[0].group(0),
                joined_text=''.join(texts)), None


def _companion_for(normal, branches):
    candidates = [b for b in branches
                  if b['reference_field'] == 'pattern1'
                  and b['type'] == normal['type']]
    if not candidates:
        return None
    np = normal['pattern']
    if not np.get('sinfo'):
        return None
    valid = []
    for candidate in candidates:
        cp = candidate['pattern']
        if cp.get('sinfo') or cp.get('flag') != np.get('flag') or cp.get('flag') != 8192:
            continue
        normal_che = np.get('che')
        companion_chs = cp.get('chs')
        if normal_che is not None or companion_chs is not None:
            if (not _is_int(normal_che) or not _is_int(companion_chs)
                    or companion_chs != normal_che + 1):
                continue
        if cp.get('che') is not None and cp.get('che') != 5:
            continue
        valid.append(candidate)
    return valid[0] if len(valid) == 1 else None


def _all_companions(branches):
    result = {}
    for normal in branches:
        if normal['reference_field'] != 'pattern0':
            continue
        companion = _companion_for(normal, branches)
        if companion is not None:
            result[_branch_key(normal)] = companion
    return result


def _canonical_text(value):
    return re.sub(r'\s+', '', str(value or ''))


def _skill_body(skill):
    return _canonical_text(''.join(str(r.get('japanese') or '') for r in skill.get('rows', [])))


def _mirror_selection(data, cid, groups, branches, companions, report):
    chara = data.cache_chara.get(cid, {})
    result = []
    for group in groups:
        if group.get('group') != 'special_move':
            continue
        for skill in group.get('skills', []):
            if skill.get('table') != 'charainfo':
                continue
            body = _skill_body(skill)
            slot_matches = [b for b in branches if _same_slots(chara, b['record'])]
            if not slot_matches:
                report.setdefault('mirror_rejections', []).append(dict(
                    record_id=skill.get('record_id'), reasons=['MIRROR_TEN_SLOT_MISMATCH']))
                continue
            body_matches = [b for b in slot_matches
                            if _canonical_text(b['pattern'].get('sinfo')) == body]
            if not body_matches:
                report.setdefault('mirror_rejections', []).append(dict(
                    record_id=skill.get('record_id'), reasons=['MIRROR_PATTERN_BODY_NOT_UNIQUE']))
                continue
            carriers = {b['child_id'] for b in body_matches}
            if len(carriers) != 1:
                report.setdefault('mirror_rejections', []).append(dict(
                    record_id=skill.get('record_id'), reasons=['MIRROR_RAW_CARRIER_NOT_UNIQUE']))
                continue
            selected = list(body_matches)
            for branch in body_matches:
                companion = companions.get(_branch_key(branch))
                if companion is not None:
                    selected.append(companion)
            unique = {_branch_key(b): b for b in selected}
            for branch in unique.values():
                branch['mirror'] = True
                result.append(branch)
    return list({_branch_key(b): b for b in result}.values())


def _existing_branch_keys(row):
    keys = set()
    for answer in row.get('answers', []):
        binding = answer.get('effect_binding') or {}
        keys.add((binding.get('pattern_id'), answer.get('record_id'),
                  answer.get('field_path'), (answer.get('binding') or {}).get('slot')))
    return keys


def _new_branch_key(branch):
    return (branch['pattern_id'], branch['child_id'],
            '/' + branch['field'], f"skillid{branch['slot']}")


def _answer(row, branch, evidence, mirror=False, companion=False,
            scope=SCOPE, variant_group=None):
    raw = branch['raw_value']
    record = branch['record']
    conditions = copy.deepcopy(branch['conditions_raw'])
    condition = f"{branch['reference_field']} / pattern {branch['pattern_id']} 被选中时"
    note = ('B=getBasicSkillAttack(true)，已含Chain，不再乘Chain；float32乘积后floor/clamp至int32。'
            '仅局部伤害输入公式，未验证最终扣血、命中次数及运行时选档。'
            '55间隔、段上限/次数、反响结算及同句其他机制仍未解析。'
            '条件为父 pattern 完整原记录；缺失字段不补零。')
    if mirror:
        note += 'charainfo正文与十参数槽唯一等价，实际取值源仍为该bossskill子记录。'
    if companion:
        note += '该文本载体分支sinfo缺失；按同角色pattern1及可用Chain条件保留独立父边与条件。'
    answer = dict(
        value=f'{condition}：floor/clamp(float32(B × {raw:g}))',
        quantity_kind=branch['quantity'], unit='倍率（相对B）', raw_value=raw,
        quantitative=True, numeric_source='已有原生静态局部公式＋源记录',
        numeric_evidence='确认', association_evidence='推断',
        answer_status='CONFIRMED_FORMULA_ONLY', evidence_scope='BY_TYPE_EXTRAPOLATED',
        rule_key=f"bossskill|{branch['type']}|/{branch['field']}",
        field_path='/' + branch['field'], table='bossskill',
        record_id=record['skillid'], layer='CACHE', source=copy.deepcopy(branch['source']),
        context=str(evidence['row'].get('japanese') or '').split('、')[0],
        condition_label=condition,
        binding=dict(pattern_id=branch['pattern_id'], slot=f"skillid{branch['slot']}",
                     child_id=branch['child_id'], condition=condition,
                     conditions_raw=conditions,
                     pattern_source=copy.deepcopy(branch['pattern_source'])),
        target='敌', note=note,
        evidence=['output/character_skills/yg1_batch2_20261024/独立报告/REVIEW_SOURCE.md',
                  'output/character_skills/boss_heal_types/native_checks.json'],
    )
    answer['effect_binding'] = dict(
        row_id=row['row_id'], effect_type='ダメージ（词表外）',
        span=list(evidence['span']),
        variant_group=variant_group or row['row_id'] + '|' + scope,
        pattern_id=branch['pattern_id'], child_id=branch['child_id'],
        field_path='/' + branch['field'])
    return answer


def _existing_variant_group(row, typ):
    quantity = FORMULAS[typ]['quantity']
    for answer in row.get('answers', []):
        binding = answer.get('effect_binding') or {}
        if (answer.get('quantity_kind') == quantity
                and binding.get('row_id') == row.get('row_id')
                and binding.get('variant_group')):
            return binding['variant_group']
    return None


def _append_scopes(row, labels):
    current = row.get('binding_conditions', [])
    if not isinstance(current, list):
        current = [current]
    row['binding_conditions'] = list(dict.fromkeys(current + labels))
    scopes = row.get('evidence_scope', [])
    if not isinstance(scopes, list):
        scopes = [scopes] if scopes else []
    row['evidence_scope'] = list(dict.fromkeys(scopes + ['BY_TYPE_EXTRAPOLATED']))


def _apply_formula_scope(groups, report, branches, companions, mirror_branches):
    by_record = {}
    for branch in branches:
        by_record.setdefault(branch['pattern_id'], []).append(branch)
    changed = answers_added = mirror_rows = 0
    changed_ids = set()
    for group in groups:
        if group.get('group') != 'special_move':
            continue
        for skill in group.get('skills', []):
            mirror = skill.get('table') == 'charainfo'
            if mirror:
                if skill.get('source', {}).get('layer') != 'CACHE':
                    continue
                selected = [b for b in mirror_branches if b['type'] in FORMULAS]
            elif skill.get('table') == 'bosspattern':
                own = by_record.get(skill.get('record_id'), [])
                selected = list(own)
                for branch in own:
                    companion = companions.get(_branch_key(branch))
                    if companion is not None and companion not in selected:
                        selected.append(companion)
            else:
                continue
            if not selected:
                continue
            evidence_by_type = {}
            for typ in sorted({b['type'] for b in selected}):
                evidence, reasons = _scan_skill_body(skill, typ)
                if reasons:
                    report.setdefault('text_rejections', []).append(dict(
                        table=skill.get('table'), record_id=skill.get('record_id'),
                        fragment_rows=len(skill.get('rows') or []), type=typ,
                        reasons=reasons))
                    continue
                evidence_by_type[typ] = evidence
            if not evidence_by_type:
                continue
            carriers = {}
            for branch in selected:
                evidence = evidence_by_type.get(branch['type'])
                if evidence is not None:
                    carriers.setdefault(branch['type'], evidence['row'])['_batch2_evidence_' + str(branch['type'])] = evidence
            for typ, row in carriers.items():
                evidence = row['_batch2_evidence_' + str(typ)]
                existing = row.get('inference_yg1') or {}
                if existing and existing.get('scope') not in (BATCH1_SCOPE, SCOPE):
                    continue
                old_keys = _existing_branch_keys(row)
                candidates = [b for b in selected if b['type'] == typ]
                additions = [b for b in candidates if _new_branch_key(b) not in old_keys]
                if not additions:
                    continue
                variant_group = _existing_variant_group(row, typ)
                labels = []
                records = []
                adopted = []
                for branch in additions:
                    companion = companions.get(_branch_key(branch)) is not None
                    is_companion = any(companions.get(_branch_key(b)) == branch for b in branches)
                    label = f"{branch['reference_field']} / pattern {branch['pattern_id']} 被选中时"
                    labels.append(label)
                    records.append(dict(
                        pattern_id=branch['pattern_id'], pattern_ref=branch['reference_field'],
                        child_id=branch['child_id'], slot=f"skillid{branch['slot']}",
                        type=branch['type'], field=branch['field'], raw_value=branch['raw_value'],
                        conditions_raw=copy.deepcopy(branch['conditions_raw'])))
                    row['answers'].append(_answer(
                        row, branch, evidence, mirror=mirror,
                        companion=is_companion, scope=SCOPE,
                        variant_group=variant_group))
                    adopted.append(branch)
                    answers_added += 1
                if not adopted:
                    continue
                if existing:
                    existing.setdefault('domain_source', report['domain_source'])
                    existing['batch2_scope'] = SCOPE
                    existing['batch2_types'] = list(dict.fromkeys(
                        (existing.get('batch2_types') or []) + [b['type'] for b in adopted]))
                    existing['batch2_pattern_records'] = (
                        (existing.get('batch2_pattern_records') or []) + records)
                    ids = list(existing.get('pattern_ids') or [])
                    ids.extend(b['pattern_id'] for b in adopted if b['pattern_id'] not in ids)
                    existing['pattern_ids'] = ids
                else:
                    row.update(
                        row_class='A', evidence='推断', numeric_evidence='确认',
                        association_evidence='推断', partial=True,
                        evidence_label='推断（YG1本体归属；局部公式类型外推）',
                        inference_yg1=dict(
                            scope=SCOPE, mirror=mirror,
                            pattern_ids=list(dict.fromkeys(b['pattern_id'] for b in adopted)),
                            domain_source=report['domain_source'],
                            formula_types=list(dict.fromkeys(b['type'] for b in adopted)),
                            pattern_records=records),
                        unknown_reasons=['已补本体伤害输入；55间隔/段上限与次数、击退/状态、反响结算及运行时选档等未覆盖内容保留待办。'])
                _append_scopes(row, labels)
                changed_ids.add(row['row_id'])
                mirror_rows += int(mirror)
            for row in carriers.values():
                for key in tuple(row):
                    if key.startswith('_batch2_evidence_'):
                        row.pop(key, None)
    return dict(changed_rows=len(changed_ids), answers_added=answers_added,
                mirror_rows=mirror_rows)


def _legacy_batch1_companion(normal, branches):
    companion = _companion_for(normal, branches)
    if not companion:
        return None
    if normal['pattern'].get('che') != 1 or companion['pattern'].get('chs') != 2:
        return None
    return companion


def _legacy_branch_view(branch):
    return dict(
        pattern_id=branch['pattern_id'], reference_field=branch['reference_field'],
        record=branch['record'], pattern=branch['pattern'],
        source={k: v for k, v in branch['source'].items()
                if k not in ('table', 'record_id', 'field_path')},
        pattern_source=branch['pattern_source'],
        conditions_raw=copy.deepcopy({
            k: branch['pattern'][k] for k in CONDITION_KEYS if k in branch['pattern']}),
        field=branch['field'], raw_value=branch['raw_value'])


def _legacy_answer(row, branch, text, mirror, companion, type_code, quantity):
    raw = branch['raw_value']; rec = branch['record']; conditions = branch['conditions_raw']
    condition = f"{branch['reference_field']} / pattern {branch['pattern_id']} 被选中时"
    note = ('B=getBasicSkillAttack(true)，已含Chain，不再乘Chain；float32乘积后floor/clamp至int32。'
            '仅局部伤害输入公式，未验证最终扣血、命中次数及运行时选档。'
            '间隔/次数/反响结算/同句其他机制仍未解析。'
            '条件原值=' + repr(conditions) + '；hpstart缺失不补零。')
    if mirror:
        note += 'charainfo十参数槽及存在性与该载体等价，仅普通档副本展示，实际取值源为bossskill。'
    if companion:
        note += '本分支sinfo缺失；按同角色共鸣分支及Chain条件作同一本体描述归属推断，保留独立载体。'
    answer = dict(
        value=f'{condition}：floor/clamp(float32(B × {raw:g}))',
        quantity_kind=quantity, unit='倍率（相对B）', raw_value=raw,
        quantitative=True, numeric_source='已有原生静态局部公式＋源记录',
        numeric_evidence='确认', association_evidence='推断',
        answer_status='CONFIRMED_FORMULA_ONLY', evidence_scope='BY_TYPE_EXTRAPOLATED',
        rule_key=f'bossskill|{type_code}|/{branch["field"]}', field_path='/' + branch['field'],
        table='bossskill', record_id=rec['skillid'], layer='CACHE',
        source={**branch['source'], 'table': 'bossskill', 'record_id': rec['skillid'],
                'field_path': '/' + branch['field']},
        context=text.split('、')[0], condition_label=condition,
        binding=dict(pattern_id=branch['pattern_id'], slot='skillid0',
                     condition=condition, conditions_raw=conditions,
                     pattern_source=branch['pattern_source']),
        target='敌', note=note,
        evidence=['output/character_skills/boss_heal_types/native_checks.json',
                  'output/character_skills/yg1_batch1_20261024/REVIEW_SOURCE.md'],
    )
    start = text.index('ダメージ')
    answer['effect_binding'] = dict(
        row_id=row['row_id'], effect_type='ダメージ（词表外）',
        span=[start, start + len('ダメージ')],
        variant_group=row['row_id'] + '|' + BATCH1_SCOPE,
        pattern_id=branch['pattern_id'])
    return answer


def _legacy_mirror(branches):
    for branch in branches:
        if (branch['reference_field'] == 'pattern0'
                and branch['pattern'].get('sinfo')):
            return branch
    return None


def _apply_legacy_batch1(data, cid, groups, by_id, normal, legacy_companion, legacy_mirror):
    spec = BATCH1_TARGETS[cid]
    changed_ids = set()
    answers_added = mirror_rows = 0
    for group in groups:
        if group.get('group') != 'special_move':
            continue
        for skill in group.get('skills', []):
            mirror = skill.get('table') == 'charainfo'
            if mirror:
                chara = data.cache_chara.get(cid, {})
                if (skill.get('source', {}).get('layer') != 'CACHE'
                        or legacy_mirror is None
                        or not _same_slots(chara, legacy_mirror['record'])):
                    continue
                selected = [legacy_mirror]
            elif skill.get('table') == 'bosspattern':
                own = by_id.get(skill.get('record_id'))
                selected = [own] if own else []
                if own is normal and legacy_companion is not None:
                    selected.append(legacy_companion)
            else:
                continue
            evidence, reasons = _scan_skill_body(skill, spec['type'])
            if reasons:
                continue
            row = evidence['row']
            if row.get('inference_yg1'):
                continue
            labels = []
            for raw_branch in selected:
                if raw_branch['type'] != spec['type']:
                    continue
                branch = _legacy_branch_view(raw_branch)
                row['answers'].append(_legacy_answer(
                    row, branch, str(row.get('japanese') or ''), mirror,
                    raw_branch is legacy_companion, spec['type'], spec['quantity']))
                labels.append(f"{branch['reference_field']} / pattern {branch['pattern_id']} 被选中时")
                answers_added += 1
            if not labels:
                continue
            row.update(
                row_class='A', evidence='推断', numeric_evidence='确认',
                association_evidence='推断', partial=True,
                evidence_label='推断（YG1本体归属；局部公式类型外推）',
                inference_yg1=dict(
                    scope=BATCH1_SCOPE, mirror=mirror,
                    pattern_ids=list(dict.fromkeys(b['pattern_id'] for b in selected))),
                unknown_reasons=['已补本体伤害输入；间隔/次数、击退/状态、反响结算及运行时选档等未覆盖内容保留待办。'])
            row['binding_conditions'] = list(dict.fromkeys(
                row.get('binding_conditions', []) + labels))
            row['evidence_scope'] = list(dict.fromkeys(
                row.get('evidence_scope', []) + ['BY_TYPE_EXTRAPOLATED']))
            changed_ids.add(row['row_id'])
            mirror_rows += int(mirror)
    return dict(changed_rows=len(changed_ids), answers_added=answers_added,
                mirror_rows=mirror_rows)


def evaluate_domain(data, cid, groups=None, include_non_yg=False):
    report = _collect(data, cid, include_non_yg)
    report.update(changed_rows=0, answers_added=0, mirror_rows=0)
    return report


def apply_to_groups(data, cid, groups, include_non_yg=False):
    report = _collect(data, cid, include_non_yg)
    report.update(changed_rows=0, answers_added=0, mirror_rows=0)
    if not report['branches']:
        return report
    branches = report['branches']
    by_id = {b['pattern_id']: b for b in branches}
    normal_branches = [b for b in branches if b['reference_field'] == 'pattern0']
    companions = _all_companions(branches)
    mirror_branches = _mirror_selection(
        data, cid, groups, branches, companions, report)
    legacy = dict(changed_rows=0, answers_added=0, mirror_rows=0)
    if cid in BATCH1_TARGETS:
        normal = next((b for b in normal_branches if b['type'] == BATCH1_TARGETS[cid]['type']), None)
        legacy_companion = (_legacy_batch1_companion(normal, branches)
                            if normal is not None else None)
        legacy_mirror = _legacy_mirror(
            [b for b in branches if b['type'] == BATCH1_TARGETS[cid]['type']])
        legacy = _apply_legacy_batch1(
            data, cid, groups, by_id, normal, legacy_companion, legacy_mirror)
    added = _apply_formula_scope(
        groups, report, branches, companions, mirror_branches)
    report.update(
        changed_rows=legacy['changed_rows'] + added['changed_rows'],
        answers_added=legacy['answers_added'] + added['answers_added'],
        mirror_rows=legacy['mirror_rows'] + added['mirror_rows'])
    return report
