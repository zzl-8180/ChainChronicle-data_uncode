"""YG1 ordered 105/110 damage and uniquely ordered 3/22 finishers.
Host integration of the unaccepted implementation draft; legacy producer is read-only.
"""
from copy import deepcopy
import math
import re
import struct
import card_page_inference_yg1 as Y

SCOPE = 'YG1_BATCH3_MULTIHIT_FORMULA_ONLY'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'
PRIMARY = (105, 110)
SUPPORTED = PRIMARY + (3, 22)
REPORT = 'output/character_skills/yg1_batch3_20261024/独立报告/REVIEW_SOURCE.md'


def f32(value):
    return struct.unpack('>f', struct.pack('>f', float(value)))[0]


def value_issue(record):
    if 'skillparam1' not in record:
        return 'P1_MISSING'
    value = record['skillparam1']
    if value is None:
        return 'P1_NULL'
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 'P1_NOT_NUMERIC'
    try:
        value = f32(value)
    except (ValueError, OverflowError, struct.error):
        return 'P1_NOT_FINITE_FLOAT32'
    return None if math.isfinite(value) and value >= 0 else 'P1_OUTSIDE_NONNEGATIVE_FINITE_DOMAIN'


def ordered(data, parent):
    record = parent['record']; pid = parent['reference_id']
    edges = []; issues = []
    for i in range(10):
        slot = f'skillid{i}'
        if not record.get(slot):
            continue
        if i > 6:
            issues.append('NONZERO_SLOT_7_TO_9_UNPROVEN_EXECUTION')
        matches = [c for c in parent.get('boss_skill_refs', [])
                   if c.get('table') == 'bossskill' and c.get('layer') == 'CACHE'
                   and c.get('reference_id') == record[slot]
                   and c.get('reference_field') == f'bosspattern[{pid}].{slot}']
        if len(matches) != 1:
            issues.append(f'CHILD_EDGE_NOT_UNIQUE:{slot}')
            continue
        child = matches[0]; raw = child.get('record') or {}
        source = data.precise_source(child)
        if raw.get('skillid') != record[slot] or source.get('source_resolution') != EXACT:
            issues.append(f'CHILD_ID_OR_SOURCE_INVALID:{slot}')
        edges.append(dict(slot=slot, child_id=record[slot], type=raw.get('skillid0'),
                          record=raw, source=source))
    return edges, issues


def scan(skill):
    rows = skill.get('rows', [])
    text = ''.join(str(r.get('japanese') or '') for r in rows)
    headers = list(Y.HEADER_RE.finditer(text))
    if len(headers) != 1:
        return [], ['RESONANCE_HEADER_NOT_UNIQUE']
    positions = []; offset = 0
    for row in rows:
        positions.append((offset, offset + len(row['japanese']), row))
        offset += len(row['japanese'])
    claims = []
    for match in re.finditer(r'ダメージを与え', text):
        start = max(text.rfind('。', 0, match.start()), text.rfind('その後、', 0, match.start()))
        start = 0 if start < 0 else start
        clause = text[start:match.end()]
        if '敵' not in clause or headers[0].start() > match.start():
            continue
        owning = [(a, r) for a, b, r in positions if a <= match.start() and match.start()+4 <= b]
        if len(owning) != 1:
            return [], ['DAMAGE_SPAN_NOT_ONE_ROW']
        a, row = owning[0]
        count = re.search(r'([0-9]+)回(?:連続で)?(?:大|中|小)?ダメージを与え$', clause)
        claims.append(dict(row=row, span=[match.start()-a, match.start()-a+4],
                           count=int(count.group(1)) if count else None,
                           after='その後' in clause, text=clause, position=match.start()))
    return claims, [] if claims else ['ENEMY_DAMAGE_PHRASE_MISSING']


def shape(edges, claims):
    targets = [e for e in edges if e['type'] in SUPPORTED]
    if not targets or not any(e['type'] in PRIMARY for e in targets):
        return [], ['PRIMARY_DAMAGE_CHILD_MISSING']
    if [id(e) for e in targets] != [id(e) for e in edges[:len(targets)]]:
        return [], ['UNSUPPORTED_MIDDLE_CARRIER']
    # Multiple supported segments require the complete one-to-one ordered list.
    # A single leading repeat segment can be independently answered while later
    # placement/echo damage remains unsupported, provided its N-hit phrase is unique.
    if len(targets) != len(claims):
        if len(targets) == 1 and len(claims) > 1 and claims[0]['count'] is not None:
            targets = targets[:1]; claims = claims[:1]
        else:
            return [], ['ORDERED_DAMAGE_BIJECTION_NOT_PROVEN']
    bindings = []
    for index, (edge, claim) in enumerate(zip(targets, claims)):
        if edge['type'] in PRIMARY:
            if claim['count'] is None:
                return [], ['REPEAT_COUNT_PHRASE_MISSING']
            cap = edge['record'].get('skillparam6')
            if cap is not None:
                try:
                    valid_cap = not isinstance(cap, bool) and isinstance(cap, (int,float)) and math.isfinite(f32(cap))
                    cap_int = math.trunc(f32(cap)) if valid_cap else None
                except (OverflowError, ValueError, struct.error):
                    cap_int = None
                if cap_int != claim['count']:
                    return [], ['REPEAT_COUNT_SLOT_CONFLICT']
        elif (index > 0 and not claim['after']) or claim['count'] is not None:
            return [], ['FINISHER_ORDER_NOT_EXPLICIT']
        bindings.append((edge, claim))
    return bindings, []


def answer(parent, edge, claim, mirror):
    row = claim['row']; pid = parent['reference_id']; typ = edge['type']
    condition = f"{parent['reference_field']} / pattern {pid} 被选中时"
    source = deepcopy(edge['source'])
    source.update(table='bossskill', record_id=edge['child_id'], field_path='/skillparam1')
    raw = edge['record']['skillparam1']
    return dict(value=condition + f'：floor/clamp(float32(B × {raw:g}))',
        quantity_kind='单次对敌伤害输入倍率', unit='倍率（相对B）', raw_value=raw,
        effective_float32=f32(raw), quantitative=True,
        numeric_source='原生静态及受控局部规则＋实际父子边', numeric_evidence='确认',
        association_evidence='推断', answer_status='CONFIRMED_FORMULA_ONLY',
        evidence_scope='BY_TYPE_EXTRAPOLATED', rule_key=f'bossskill|{typ}|/skillparam1',
        field_path='/skillparam1', table='bossskill', record_id=edge['child_id'], layer='CACHE',
        source=source, context=row['japanese'].split('、')[0], condition_label=condition,
        binding=dict(scope=SCOPE, type=typ, pattern_id=pid, slot=edge['slot'], child_id=edge['child_id'],
                     condition=condition, conditions_raw=deepcopy(parent['record']),
                     pattern_source=deepcopy(parent['_source']), mirror=mirror),
        effect_binding=dict(row_id=row['row_id'], effect_type='ダメージ（词表外）',
                            span=claim['span'], variant_group=row['row_id']+'|'+SCOPE+str(claim['span']),
                            pattern_id=pid, child_id=edge['child_id'], field_path='/skillparam1'),
        target='敌', note='B=getBasicSkillAttack(true)，已含Chain，不再乘Chain；float32乘积后floor/clamp。'
            '仅局部输入公式，最终HP、保证命中与运行时选档未验证。'
            + ('charainfo十参数存在性及原值与首段载体匹配，完整正文唯一回绑至此执行父；其余段沿该父的有序实际槽。' if mirror else '')
            + '父条件完整原值见binding.conditions_raw；无正文伴随档不强绑。', evidence=[REPORT])


def key(a):
    b = a.get('binding') or {}
    return b.get('scope'), b.get('pattern_id'), b.get('slot'), a.get('field_path')


def apply_to_groups(data, cid, groups, include_non_yg=False):
    report = dict(scope=SCOPE, answers_added=0, changed_row_ids=[], rejections=[], companions=[])
    if not include_non_yg and 'Y.G.' not in str((data.profiles.get(cid) or {}).get('title') or ''):
        return report
    entries = next((g for g in data.links[cid]['groups'] if g['group']=='special_move'), {}).get('records', [])
    chara = data.cache_chara.get(cid, {})
    skills = [s for g in groups if g['group']=='special_move' for s in g['skills']]
    parents = []
    for entry in entries:
        if entry.get('table') != 'bosspattern' or entry.get('layer') != 'CACHE':
            continue
        issues = Y._parent_issues(data, chara, entries, entry)
        edges, child_issues = ordered(data, entry)
        if not any(e['type'] in PRIMARY for e in edges):
            continue
        if issues or child_issues:
            report['rejections'].append(dict(pattern_id=entry['reference_id'], reasons=issues+child_issues)); continue
        parent = {**entry, '_source':data.precise_source(entry), '_edges':edges}
        if not entry['record'].get('sinfo'):
            report['companions'].append(dict(pattern_id=entry['reference_id'], conditions_raw=deepcopy(entry['record']),
                                            source=parent['_source'], status='NO_BODY_NOT_BOUND'))
            continue
        parents.append(parent)
    for skill in skills:
        mirror = skill.get('table') == 'charainfo'
        if skill.get('source',{}).get('layer') != 'CACHE' or skill.get('table') not in ('bosspattern','charainfo'):
            continue
        if mirror:
            selected = [p for p in parents if Y._canonical_text(p['record'].get('sinfo')) == Y._skill_body(skill)
                        and Y._same_slots(chara,p['_edges'][0]['record'])]
            if len(selected) != 1:
                continue
        else:
            selected = [p for p in parents if p['reference_id'] == skill.get('record_id')]
        for parent in selected:
            claims, issues = scan(skill)
            bindings, shape_issues = shape(parent['_edges'], claims) if not issues else ([], [])
            if issues or shape_issues:
                report['rejections'].append(dict(pattern_id=parent['reference_id'], mirror=mirror, reasons=issues+shape_issues)); continue
            for edge, claim in bindings:
                issue = value_issue(edge['record'])
                if issue:
                    report['rejections'].append(dict(pattern_id=parent['reference_id'], slot=edge['slot'], reasons=[issue])); continue
                row = claim['row']; item = answer(parent,edge,claim,mirror)
                if key(item) in {key(a) for a in row.get('answers',[])}:
                    continue
                row['answers'].append(item)
                row.update(row_class='A', evidence='推断', numeric_evidence='确认', association_evidence='推断',
                           partial=True, evidence_label='推断（YG1有序本体归属；局部公式类型外推）')
                row['evidence_scope'] = list(dict.fromkeys(row.get('evidence_scope',[]) + ['BY_TYPE_EXTRAPOLATED']))
                marker = row.setdefault('inference_yg1_multihit', dict(scope=SCOPE, pattern_ids=[], branches=[]))
                if parent['reference_id'] not in marker['pattern_ids']:
                    marker['pattern_ids'].append(parent['reference_id'])
                marker['branches'].append(dict(pattern_id=parent['reference_id'], slot=edge['slot'], child_id=edge['child_id'], type=edge['type'], mirror=mirror))
                reason='已补此段局部伤害输入；同句其余机制、保证命中及运行时选档仍待核查，无正文伴随档保留独立配置。'
                if reason not in row['unknown_reasons']:
                    row['unknown_reasons'].append(reason)
                report['answers_added'] += 1
                if row['row_id'] not in report['changed_row_ids']:
                    report['changed_row_ids'].append(row['row_id'])
    return report
