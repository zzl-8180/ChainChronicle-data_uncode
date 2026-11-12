# -*- coding: utf-8 -*-
"""通常回复间隔的两段乘数结构（type19 param2／type1033 param3，2026-10-28 批 3）。

任务书：``docs/tasks/20261028-type19-1033-batch.md``。规则引用：``docs/角色技能完整解读实施方案.md``
（2026-10-24 修订，含 §1.3）。协作者对照：``output/reference_analysis/cc_20261027/``
（merge_recommendations A7、conflicts C5/C6）。枚举：``skilllist_types/dispatch_map.json``
的 ``ability_type_enum``：19=StrengthHealer、1033=HeroOneHeal。

范围（逐行门控，任一不满足即拒答并记原因码；不出数）
----------------------------------------------------
G1  零触碰：cid∈{30236,30239} 不进入（30236 基线整卡、30239 同守；30239 的 19.p2=0.275
    与 Class 0.5 口径争议正是本批不写秒数的原因，整卡不改一个字节）。
G2  载体：行属 ``table=skilllist``、``layer∈{APK,CACHE}``，记录可由**该层**原始主表按 skillid
    唯一解析（``output/base_master/_mdSkill.json`` / ``skilllist.data5.json.raw``）；sub 递归
    同层解析，缺件即拒。**CACHE/APK 同 skillid 不跨层取值**——载体层内解析，另层原值只披露
    （写入 ``binding.heal_interval_binding.other_layer_raw``），不参与换算。
G3  句形：行片段含「回復速度」（速度断言）。本批不覆盖「回復量」「回復範囲」句族，
    也不覆盖不含速度词的行。点名的能力由原始记录决定（不在句面猜槽位）。
G4  基础段：本行记录链内 ability=19 记录**恰一条**且 param2 数值有限 >0；0 条 → NO_CARRIER，
    >1 条 → CARRIER_NOT_UNIQUE（不合并多个值）。
G5  条件段：链内 ability=1033 记录 0 条或若干条；多条时按 param3 去重，去重后 ≠1 →
    CARRIER_NOT_UNIQUE（不猜哪条生效）；0 条＝只有基础段。
G6  形状：两段各自有限 >0；**两段同时＝1.0 与句面「上がる」矛盾** → NEUTRAL_SENTENCE_CONFLICT
    （留 hint 不出数）。中性段（=1.0）不作为答案输出，只在 note 披露。
G7  无既有答案：行内已有同一 ``rule_key`` 的答案则跳过（不覆盖旧值）。

数值语义（本批只登记结构，不写秒数）
------------------------------------
* 段1＝``skilllist|19|/param2``（基础段，恒常）；段2＝``skilllist|1033|/param3``（条件段，
  条件成立时另乘）。**结构形式：通常回复间隔 = 基础间隔 × param2 × param3(条件成立时)**。
* **不写秒数**：「基础 4 秒」是用户工作值且协作者自身两例口径不一致（30239 乘了 Class 0.5、
  1213 没乘，至少一例错），故本模块不产出任何秒数、不把 Class 0.5 当统一乘数
  （Class 记录 65000004/65000006/65000009 的 19.p2=0.5 只作旁证披露，不参与换算）。
* 证据：1213 日文「…通常回復の回復量と**回復速度**が上がり…」↔ 19.p2=0.95、1033.p3=0.95；
  11217 日文不提速度（「回復量が上がり、回復後の攻撃までの硬直時間が短縮」）↔ 两段均 1.0。
  11217 的 1033 两条（戦士在 p1=5.0／弓使い在 p1=3.5）p3 都是 1.0，反证 p3 是速度位而不是
  「効果」泛槽。
* **type1033 param1 的「回复范围」只保留为推断，不升级、不出数**：11217 强正例
  （戦士在 →5.0、弓使い在 →3.5 不变）与 1213 反例（19.p0=6.0 → 1033.p1=4.0 变成缩小）并存，
  「绝对值/增量」两种解释都解释不了全部样本。本模块只在 1033 段答案 note 里作推断+反例披露。

来源限定：``profiles/rules.json`` 自 2026-10-28 规则登记批起**已有** ``skilllist|19|/param2``
与 ``skilllist|1033|/param3`` 两个键（正文源自本模块批前 ``RULE_SPECS``，逐字迁入
``scripts/character_skills/rules.py::_registration_20261028_specs``）。模块不再持有副本，改为
``rules.rule_for`` 读取规则、``rules.answer_for``（显式传 ``source_layer``）读取换算文案；
答案 ``rule_registry``/``rule_status``/``numeric_source`` 如实记已登记，数值零变化。
**仍不写秒数、1033.p1 范围仍仅推断、96 攻击未证边界与本批无关。**

答案（每段 1 条，中性段不出）
----------------------------
* 段值＝原始 param（倍率，无量纲）；本段相对变化＝(1−param)×100%（间隔缩短）。
* 关联证据＝推断（句面↔记录槽位绑定，样本 2 张）；数值＝确认（原值逐值相等）。
* 合成值只在 note 披露（两段相乘），不单独成答案：基础间隔秒数未确认，合成后的秒数不写。
"""
from __future__ import annotations

import json
import math

import rules as R

MODULE_VERSION = 'heal_interval_20261028'
SCOPE = 'HEAL_INTERVAL_20261028'
TAG = '推断（模板批 回复间隔两段乘数）'
FAMILY = 'heal_interval_two_segment（type19 p2 基础段／type1033 p3 条件段）'

TABLE = 'skilllist'
LAYERS = ('APK', 'CACHE')
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

SPEED_MARK = '回復速度'
BASE_ABILITY = 19
COND_ABILITY = 1033
RULE_KEYS = {19: 'skilllist|19|/param2', 1033: 'skilllist|1033|/param3'}
FIELD_PATHS = {19: '/param2', 1033: '/param3'}
ENUM = {19: 'StrengthHealer', 1033: 'HeroOneHeal'}
SEGMENT = {19: 1, 1033: 2}
SEGMENT_LABEL = {19: '基础段', 1033: '条件段'}
MAX_SUB_DEPTH = 3

# Class 记录旁证（只披露，不参与换算）：本批不把 0.5 当统一乘数。
CLASS_19_P2_NOTE = ('Class 记录 65000004/65000006/65000009 的 ability19 param2=0.5 只作旁证；'
                    '30239（乘了 Class 0.5）与 1213（没乘）口径不一致，至少一例错，'
                    '本批不把 Class 0.5 当统一乘数、不写秒数。')

# 规则正文自 2026-10-28 规则登记批起只存在于规则层（本模块不再持有 RULE_SPECS 副本）。
def _rule(ability):
    """规则层规则行（登记批后为唯一事实源；缺键即拒答，不退回未登记口径）。"""
    rule = R.rule_for(TABLE, ability, FIELD_PATHS[ability])
    if not rule:
        raise RuntimeError(f'规则登记批：rules 层缺键 {RULE_KEYS[ability]}，拒绝在未登记状态下出数')
    return rule


def answer_core(ability, raw, layer):
    """规则层换算结果（value_text／quantity_kind／unit）。

    ``source_layer`` 是登记的来源限定门：只有显式声明载体层的消费者才可取到答案，
    无层证据的旧调用方（页面 record_evidence 逐字段外推）返回 None，不会产生树答案。
    """
    field = FIELD_PATHS[ability]
    record = {'ability': ability, field.lstrip('/'): raw}
    ans = R.answer_for(TABLE, ability, field, raw, record, source_layer=layer)
    if not ans:
        raise RuntimeError(f'规则登记批：answer_for 未返回 {RULE_KEYS[ability]}'
                           f'（layer={layer} raw={raw!r}）')
    return ans


def registration_assertions():
    """模块侧等价断言（scratch 调用）：登记后的规则行与出数文案一致、状态记已登记。"""
    out = []
    for ability, sample, want_text in (
            (19, 0.95, '通常回复间隔 ×0.95（第1段：基础段；间隔缩短 5%）'),
            (1033, 0.95, '通常回复间隔 ×0.95（第2段：条件段，条件成立时；间隔缩短 5%）')):
        rule = _rule(ability)
        core = answer_core(ability, sample, 'APK')
        status = rule.get('status') or ''
        out.append(dict(
            rule_key=RULE_KEYS[ability], present=True,
            registered=('已登记' in status and '未登记' not in status),
            unit_ok=(rule.get('unit') == core.get('unit') == '无量纲倍率（时间间隔乘数）'),
            conversion_ok=('(1−param' in (rule.get('conversion') or '')
                           and '不写秒数' in (rule.get('limits') or '')),
            value_text=core['value_text'],
            value_text_ok=(core['value_text'] == want_text),
            quantity_kind_ok=(core.get('quantity_kind') == '通常回復間隔乘數（時間倍率）'),
            no_seconds=('秒' not in core['value_text']),
            conditions_present=bool(rule.get('conditions') or rule.get('applicability')),
            limits_present=bool(rule.get('limits')),
            target_present=bool(rule.get('target')),
            evidence_present=bool(rule.get('evidence')),
            base_definition_present=bool(rule.get('base_definition')),
        ))
    return out

REJECT_ORDER = ('ZERO_TOUCH_CID', 'NOT_SKILLLIST_LAYER', 'SENTENCE_MISMATCH',
                'SUB_UNRESOLVED', 'NO_CARRIER', 'CARRIER_NOT_UNIQUE', 'SHAPE_INVALID',
                'NEUTRAL_SENTENCE_CONFLICT', 'ALREADY_ANSWERED')


def _is_num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _neutral(value) -> bool:
    return _is_num(value) and abs(float(value) - 1.0) < 1e-12


def skill_lookup(data, layer):
    """原始主表的 skillid → (index, record)。CACHE/APK 分源，不跨层。"""
    table = getattr(data, 'cache_skill' if layer == 'CACHE' else 'apk_skill', None)
    return table or {}


def resolve_chain(data, layer, record):
    """记录 + sub 递归展开（同层）；返回 (chain, unresolved)。"""
    lookup = skill_lookup(data, layer)
    chain, missing, seen = [record], [], {record.get('skillid')}
    frontier = [(record, 0)]
    while frontier:
        head, depth = frontier.pop(0)
        subs = head.get('sub') or []
        if depth >= MAX_SUB_DEPTH:
            if subs:
                missing.append(dict(parent=head.get('skillid'), reason='DEPTH_LIMIT', sub=list(subs)))
            continue
        for child in subs:
            if child in seen:
                continue
            hit = lookup.get(child)
            if hit is None:
                missing.append(dict(parent=head.get('skillid'), reason='MISSING_IN_LAYER', sub=child))
                continue
            seen.add(child)
            chain.append(hit[1])
            frontier.append((hit[1], depth + 1))
    return chain, missing


def _resolve_record(data, layer, skillid):
    hit = (skill_lookup(data, layer) or {}).get(skillid)
    return hit[1] if hit else None


def _record_index(data, layer, skillid):
    hit = (skill_lookup(data, layer) or {}).get(skillid)
    return hit[0] if hit else None


def segments_of_chain(chain):
    """链内 ability19（基础段）与 ability1033（条件段）记录。"""
    base = [c for c in chain if c.get('ability') == BASE_ABILITY]
    cond = [c for c in chain if c.get('ability') == COND_ABILITY]
    return base, cond


def other_layer_raw(data, ability, skillid, layer):
    """同 skillid 在另一层的对应槽原值（只披露，不参与换算）。"""
    other = 'APK' if layer == 'CACHE' else 'CACHE'
    rec = _resolve_record(data, other, skillid)
    if not isinstance(rec, dict) or rec.get('ability') != ability:
        return None
    return rec.get(FIELD_PATHS[ability].lstrip('/'))


def _fmt_num(value) -> str:
    return f'{float(value):.6g}'


def _source(data, layer, record, ability):
    index = _record_index(data, layer, record.get('skillid'))
    source_key = f'{layer}/_mdSkill.json' if layer == 'APK' else f'{layer}/skilllist.data5.json.raw'
    original = ('output/base_master/_mdSkill.json' if layer == 'APK'
                else 'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')
    field = FIELD_PATHS[ability]
    return dict(table=TABLE, record_id=record.get('skillid'), layer=layer,
                source_key=source_key,
                record_key=(f'{layer}/_mdSkill.json#/skilllist/{index}' if layer == 'APK'
                            else f'{layer}/skilllist.data5.json.raw#/skilllist/{index}'),
                json_pointer=(f'/skilllist/{index}' if index is not None else None),
                original_file=original, field=field, field_path=field,
                raw_value=record.get(field.lstrip('/')), namespace=TABLE, ability_type=ability)


def _combined_note(base_raw, cond_raw):
    if cond_raw is None:
        return f'本能力只有基础段：通常回复间隔 = 基础间隔 × {_fmt_num(base_raw)}'
    if _neutral(base_raw):
        return (f'两段结构：基础段 19.p2=1.0（中性，不改变间隔）× 条件段 1033.p3='
                f'{_fmt_num(cond_raw)}（条件成立时）')
    if _neutral(cond_raw):
        return (f'两段结构：基础段 19.p2={_fmt_num(base_raw)} × 条件段 1033.p3=1.0'
                f'（中性，不改变间隔）')
    return (f'两段相乘：基础间隔 × {_fmt_num(base_raw)} × {_fmt_num(cond_raw)} = '
            f'× {_fmt_num(float(base_raw) * float(cond_raw))}（条件成立时）')


def evaluate(cid, layer, table, record, row, *, data=None, groups=()):
    """单行门控。返回 dict(status, reject, gates, answers, segments)。"""
    row = row or {}
    frag = str(row.get('japanese') or '')
    gates = {}
    if cid in ZERO_TOUCH_CIDS:
        return dict(status='REJECT', reject='ZERO_TOUCH_CID',
                    gates={'G1_not_zero_touch': False}, answers=[], segments={})
    gates['G1_not_zero_touch'] = True
    if not (table == TABLE and layer in LAYERS and isinstance(record, dict)):
        return dict(status='REJECT', reject='NOT_SKILLLIST_LAYER',
                    gates={**gates, 'G2_carrier': False}, answers=[], segments={})
    gates['G2_carrier'] = True
    if SPEED_MARK not in frag:
        return dict(status='REJECT', reject='SENTENCE_MISMATCH',
                    gates={**gates, 'G3_sentence': False}, answers=[], segments={})
    gates['G3_sentence'] = True
    chain, missing = resolve_chain(data, layer, record)
    if missing:
        return dict(status='REJECT', reject='SUB_UNRESOLVED',
                    gates={**gates, 'G2_sub_resolved': False}, answers=[], segments={},
                    missing=missing)
    gates['G2_sub_resolved'] = True
    base, cond = segments_of_chain(chain)
    if not base:
        return dict(status='REJECT', reject='NO_CARRIER',
                    gates={**gates, 'G4_base': False}, answers=[], segments={})
    if len(base) != 1:
        return dict(status='REJECT', reject='CARRIER_NOT_UNIQUE',
                    gates={**gates, 'G4_base': False}, answers=[], segments={},
                    base_candidates=[c.get('skillid') for c in base])
    gates['G4_base'] = True
    base_rec = base[0]
    base_raw = base_rec.get('param2')
    if not _is_num(base_raw) or float(base_raw) <= 0:
        return dict(status='REJECT', reject='SHAPE_INVALID',
                    gates={**gates, 'G6_shape': False}, answers=[], segments={},
                    detail='BASE_P2_INVALID', base=dict(record=base_rec.get('skillid'),
                                                        param2=base_raw))
    cond_raw, cond_recs = None, []
    if cond:
        by_raw = {}
        for rec in cond:
            raw = rec.get('param3')
            if not _is_num(raw) or float(raw) <= 0:
                return dict(status='REJECT', reject='SHAPE_INVALID',
                            gates={**gates, 'G6_shape': False}, answers=[], segments={},
                            detail='COND_P3_INVALID',
                            cond=dict(record=rec.get('skillid'), param3=raw))
            by_raw.setdefault(float(raw), []).append(rec)
        if len(by_raw) != 1:
            return dict(status='REJECT', reject='CARRIER_NOT_UNIQUE',
                        gates={**gates, 'G5_cond': False}, answers=[], segments={},
                        cond_candidates=[dict(record=r.get('skillid'), param3=r.get('param3'))
                                         for r in cond])
        cond_raw = next(iter(by_raw))
        cond_recs = by_raw[cond_raw]
    gates['G5_cond'] = True
    if _neutral(base_raw) and (cond_raw is None or _neutral(cond_raw)):
        return dict(status='REJECT', reject='NEUTRAL_SENTENCE_CONFLICT',
                    gates={**gates, 'G6_shape': False}, answers=[], segments={},
                    segments_detail=dict(base=base_rec.get('skillid'), base_param2=base_raw,
                                         cond=[r.get('skillid') for r in cond_recs],
                                         cond_param3=cond_raw))
    gates['G6_shape'] = True

    out = []
    seg_info = {}
    for ability, raw, rec in ((BASE_ABILITY, base_raw, base_rec),
                              (COND_ABILITY, cond_raw, (cond_recs[0] if cond_recs else None))):
        if rec is None or _neutral(raw):
            seg_info[str(ability)] = dict(present=rec is not None, neutral=True, raw=raw)
            continue
        if any(str(a.get('rule_key')) == RULE_KEYS[ability] for a in row.get('answers') or []):
            seg_info[str(ability)] = dict(present=True, neutral=False, raw=raw,
                                          skipped='ALREADY_ANSWERED')
            continue
        out.append(build_answer(cid, row, layer, rec, ability, data, base_raw, cond_raw,
                                cond_recs))
        seg_info[str(ability)] = dict(present=True, neutral=False, raw=raw)
    if not out:
        reasons = [v.get('skipped') for v in seg_info.values() if v.get('skipped')]
        return dict(status='REJECT',
                    reject='ALREADY_ANSWERED' if reasons else 'NEUTRAL_SENTENCE_CONFLICT',
                    gates=gates, answers=[], segments=seg_info)
    return dict(status='ACCEPT', reject=None, gates=gates, answers=out, segments=seg_info)


def build_answer(cid, row, layer, carrier, ability, data, base_raw, cond_raw, cond_recs):
    rule = _rule(ability)
    field = FIELD_PATHS[ability]
    raw = carrier.get(field.lstrip('/'))
    core = answer_core(ability, raw, layer)
    other = other_layer_raw(data, ability, carrier.get('skillid'), layer)
    notes = [_combined_note(base_raw, cond_raw)]
    notes.append('基础间隔秒数未确认，本批不写秒数（不把 Class 0.5 当统一乘数）')
    notes.append(CLASS_19_P2_NOTE)
    if other is not None and _is_num(other) and abs(float(other) - float(raw)) > 1e-9:
        notes.append(f'同 skillid {carrier.get("skillid")} 在另一层 {field}={_fmt_num(other)}，'
                     f'按载体层 {layer} 取值（不跨层混用）')
    if ability == COND_ABILITY:
        notes.append('条件内容（flag 位图）未解码；同能力多条 1033 记录按 param3 去重'
                     if len(cond_recs or []) > 1 else '条件内容（flag 位图）未解码')
        notes.append('type1033 param1 的「回复范围」只是推断：1213 反例（19.p0=6.0 → p1=4.0 '
                     '缩小）、11217 强正例（戦士在 5.0／弓使い在 3.5）——本批不作范围答案')
    return dict(
        value=core['value_text'],
        quantity_kind=core['quantity_kind'],
        unit=core['unit'],
        raw_value=raw,
        field_path=field,
        numeric_source=('规则（rules.json#' + RULE_KEYS[ability] + '，规则登记批 2026-10-28 已登记；'
                        'dispatch_map 枚举＋1213/11217 句面↔记录）'),
        numeric_evidence='确认',
        association_evidence='推断',
        evidence_scope=SCOPE,
        rule_key=RULE_KEYS[ability],
        rule_registry=('output/character_skills/profiles/rules.json#' + RULE_KEYS[ability]
                       + '（规则登记批 2026-10-28 已登记；正文与批前模块声明逐字相同）'),
        rule_body_status=rule.get('status'),
        rule_status=rule.get('status'),
        conversion=rule.get('conversion'),
        base_definition=rule.get('base_definition'),
        conditions=rule.get('applicability') or rule.get('conditions'),
        rule_limits=rule.get('limits'),
        target=rule.get('target'),
        evidence=list(rule.get('evidence') or []),
        source=_source(data, layer, carrier, ability),
        table=TABLE, record_id=carrier.get('skillid'), layer=layer,
        binding={'heal_interval_binding': dict(
            scope=SCOPE, family='heal_interval_two_segment', ability=ability,
            enum=ENUM[ability], segment=SEGMENT[ability], slot=field.lstrip('/'),
            row_id=row.get('row_id'), rule_key=RULE_KEYS[ability],
            carrier_record_id=carrier.get('skillid'), carrier_layer=layer,
            raw=raw, base_param2=base_raw, cond_param3=cond_raw,
            cond_records=[r.get('skillid') for r in (cond_recs or [])] or None,
            other_layer_raw=other,
            range_inference=('type1033 p1「回复范围」仅推断（1213 反例/11217 正例），本批不出范围答案'
                             if ability == COND_ABILITY else None))},
        note='；'.join(notes),
        quantitative=True)


def _append(row, answer):
    def key(a):
        return (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    if any(key(a) == key(answer) for a in row.get('answers') or []):
        return False
    row.setdefault('answers', []).append(answer)
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = TAG
    row['partial'] = True
    row['evidence_scope'] = list(dict.fromkeys(list(row.get('evidence_scope') or []) + [SCOPE]))
    marker = row.setdefault('inference_heal_interval', dict(scope=SCOPE, claims=[]))
    marker['claims'].append(dict(family='heal_interval_two_segment',
                                 ability=answer['binding']['heal_interval_binding']['ability'],
                                 segment=answer['binding']['heal_interval_binding']['segment'],
                                 rule_key=answer['rule_key'], record_id=answer['record_id'],
                                 value=answer['raw_value']))
    return True


def _hint(row, reason, detail=None):
    text = f'{TAG}：{reason}'
    if detail:
        text += f'（{detail}）'
    row['inference_heal_interval_hint'] = text
    row.setdefault('inference_heal_interval_meta', dict(scope=SCOPE, reason=reason, detail=detail))
    return text


def apply_to_groups(data, cid, groups):
    """正式页消费：为「回復速度」句绑定本批两段乘数答案（不覆盖/不删除既有答案）。"""
    report = dict(scope=SCOPE, cid=cid, answers_added=0, additions=[], rejections=[],
                  hints=0, skipped_existing=0, evaluated=0)
    if cid in ZERO_TOUCH_CIDS:
        report['zero_touch'] = True
        return report
    for group in groups or []:
        for skill in group.get('skills') or []:
            if skill.get('table') != TABLE:
                continue
            rows = [r for r in skill.get('rows') or []
                    if SPEED_MARK in str(r.get('japanese') or '')]
            if not rows:
                continue
            layer = skill.get('layer')
            record = _resolve_record(data, layer, skill.get('record_id'))
            for row in rows:
                report['evaluated'] += 1
                res = evaluate(cid, layer, skill.get('table'), record, row, data=data, groups=groups)
                if res['status'] != 'ACCEPT':
                    if res['reject'] == 'ALREADY_ANSWERED':
                        report['skipped_existing'] += 1
                        continue
                    # hint 只写本批句族（skilllist 载体 + 回復速度）且该槽无既有答案；
                    # 其它表的同句式（job_ability/charainfo 等）不立本批句族注记。
                    if not any(str(a.get('rule_key') or '').startswith(('skilllist|19|',
                                                                       'skilllist|1033|'))
                               for a in row.get('answers') or []):
                        _hint(row, res['reject'], None)
                        report['hints'] += 1
                    report['rejections'].append(dict(row_id=row.get('row_id'),
                                                     reason=res['reject'],
                                                     segments=res.get('segments')))
                    continue
                added = 0
                for ans in res['answers']:
                    if _append(row, ans):
                        added += 1
                        b = ans['binding']['heal_interval_binding']
                        report['additions'].append(dict(
                            row_id=row.get('row_id'), ability=b['ability'], segment=b['segment'],
                            rule_key=ans['rule_key'], value=ans['value'], raw_value=ans['raw_value'],
                            carrier=ans['record_id'], carrier_layer=ans['layer']))
                report['answers_added'] += added
                row.setdefault('heal_interval_gate', dict(res['gates']))
    return report


# ---------------------------------------------------------------------------
# 只读探针：原始记录 → 两段结构（不进页面）
# ---------------------------------------------------------------------------
def probe(data, cid, row_id=None):
    """按页面找「回復速度」行，输出两段原值与合成值（不写页面）。"""
    from pathlib import Path
    page = json.loads((R.read_path(Path('output/character_skills/pages')) / str(cid) / 'card.json')
                      .read_text(encoding='utf-8'))
    out = dict(cid=cid, rows=[])
    for group in page.get('groups') or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                if row_id and row.get('row_id') != row_id:
                    continue
                if SPEED_MARK not in str(row.get('japanese') or ''):
                    continue
                layer = skill.get('layer')
                rec = _resolve_record(data, layer, skill.get('record_id'))
                chain, missing = resolve_chain(data, layer, rec) if rec else ([], ['NO_RECORD'])
                base, cond = segments_of_chain(chain)
                base_raw = base[0].get('param2') if len(base) == 1 else None
                cond_raws = [c.get('param3') for c in cond]
                prod = (float(base_raw) * float(cond_raws[0])
                        if _is_num(base_raw) and cond_raws and _is_num(cond_raws[0]) else base_raw)
                out['rows'].append(dict(
                    row_id=row.get('row_id'), table=skill.get('table'), layer=layer,
                    carrier=skill.get('record_id'), japanese=row.get('japanese'),
                    missing=missing,
                    base=dict(records=[c.get('skillid') for c in base], param2=base_raw),
                    cond=dict(records=[c.get('skillid') for c in cond], param3=cond_raws,
                              param1=[c.get('param1') for c in cond]),
                    combined=prod,
                    has_answer=any(str(a.get('rule_key') or '').startswith(('skilllist|19|',
                                                                            'skilllist|1033|'))
                                   for a in row.get('answers') or [])))
    return out


def probe_skill(data, layer, skillid):
    """按 skillid 直读原始链 → 两段原值与合成值（不依赖页面、不写页面）。"""
    rec = _resolve_record(data, layer, skillid)
    if not isinstance(rec, dict):
        return dict(layer=layer, skillid=skillid, missing=['NO_RECORD'], base=None, cond=None)
    chain, missing = resolve_chain(data, layer, rec)
    base, cond = segments_of_chain(chain)
    base_raw = base[0].get('param2') if len(base) == 1 else None
    cond_raws = [c.get('param3') for c in cond]
    combined = base_raw
    if _is_num(base_raw) and cond_raws and _is_num(cond_raws[0]):
        combined = float(base_raw) * float(cond_raws[0])
    return dict(layer=layer, skillid=skillid, missing=missing,
                chain=[c.get('skillid') for c in chain],
                base=dict(records=[c.get('skillid') for c in base], param2=base_raw,
                          param0=base[0].get('param0') if base else None),
                cond=dict(records=[c.get('skillid') for c in cond], param3=cond_raws,
                          param1=[c.get('param1') for c in cond]),
                combined=combined)


def _main(argv=None):
    import argparse
    import sys
    from pathlib import Path
    ap = argparse.ArgumentParser(description='回复间隔两段乘数批：只读探针')
    ap.add_argument('--cid', type=int, action='append', help='卡号（可多次）')
    ap.add_argument('--row-id', help='限定单行')
    args = ap.parse_args(argv)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    if not args.cid:
        ap.print_help()
        return 2
    root = Path('.')

    class Data:
        def __init__(self, rootp):
            self.apk_skill = {r['skillid']: (i, r) for i, r in enumerate(
                json.loads((rootp / 'output/base_master/_mdSkill.json')
                           .read_text(encoding='utf-8'))['skilllist'])}
            self.cache_skill = {r['skillid']: (i, r) for i, r in enumerate(
                json.loads((rootp / 'output/cache_full_20261015_v3/decoded/'
                            'skilllist.data5.json.raw').read_text(encoding='utf-8'))['skilllist'])}
    data = Data(root)
    print(json.dumps([probe(data, cid, args.row_id) for cid in args.cid],
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
