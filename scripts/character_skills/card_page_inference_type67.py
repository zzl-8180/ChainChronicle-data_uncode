# -*- coding: utf-8 -*-
"""type67「…が多いほど」阶梯推断模块（2026-10-28 批 1）。

任务书：``docs/tasks/20261028-type67-batch.md``。规则引用：``docs/角色技能完整解读实施方案.md``
（2026-10-24 修订，含 §1.3）。协作者对照：``output/reference_analysis/cc_20261027/`` 与
``其他人的参考/CC解包数据_给GPT_20261027/claude_cc_site_pages/真实算法.md`` §1。

范围（逐行门控，任一不满足即拒答并记原因码；不出数）
----------------------------------------------------
G1  零触碰：cid∈{30236,30239} 不进入（30236 基线整卡、30239 同守）。
G2  载体：行属 ``table=skilllist``、``layer∈{APK,CACHE}``，记录可由该层原始主表按 skillid
    唯一解析（``_mdSkill.json`` / ``skilllist.data5.json.raw``）；子记录**同层**解析，
    缺件即拒（不跨层取值）。
G3  句形：行片段含「多いほど」。
G4  计数域：句面必须落在原生计数域（CalcCharaNum 的成员列表＋职业/武器/出身筛选）——即
    「（自身を含む）…味方が多いほど」。命中「マナ／敵の数／職業の種類／状態異常」的句子
    **不是**该计数域（法珠数/敌数/职业种类/状态异常均无原生计数证据），留 hint 不出数。
G5  形状：载体链（记录 + ``sub`` 递归展开，深度≤3，环路保护）内 ability=67 的记录
    ① ≥2 条；② param0 全为整数；③ 升序且恰为 1,2,…,M（重号或跳号＝形状不符：13207 的
    p0 全 1／iParam0 分职业、11232 的 p0 仅 2 均在此拒）；④ 筛选签名（iParam0, flag0_0,
    int(param8)）逐条一致（同一计数域）。
G6  无既有答案：行 ``answers`` 为空才新增（不改旧值）。
G7  规则可用：``rules.answer_for('skilllist',67,field,…)`` 返回 CONFIRMED_NUMERIC 且
    ``rule_for`` 状态含「已确认」——规则键 ``skilllist|67|/param1,/param2,/param3,/param6,
    /param7`` **已存在**，本模块不改 rules.json / rules.py。
G8  槽位：槽位对应属性必须在句面点名（攻撃力/防御力/移動速度/クリティカル発生率/
    クリティカル威力），且该槽在阶梯内非中性（倍率≠1 / 加算≠0）。

答案（每个槽位 1 条，逐行产出）
--------------------------------
* ``/param1`` 攻击倍率：**连乘** 倍率(N)=Π{p0≤N}.param1（原生累乘点 0x1107af4 ``fmul s8,s8,s0``）。
* ``/param2`` 移动速度乘数、``/param3`` 受伤量乘数：同连乘结构（0x1118bbc / 0x110838c）。
* ``/param6`` 暴击率 / ``/param7`` 暴伤系数：**逐条加算** 增量(N)=Σ{p0≤N}.param（原生累加点
  0x11195b0 / 0x1119dc0 ``fadd s9,s9,s0``）。任务书 §1 把 p6/p7 写成「同连乘结构」；本项目
  rules.json、skilllist_types/composite_chains.json 与协作者 R03 均为加算，本模块按原始
  累加点出数并在答案 note 明示该差异（连乘 0.2×0.05⁴≈1.25e-6 与记录/正文不符）。

原文加算写法与真实算法分列披露：页面「120%+5n%」这类加算只是阅读简化，不是算法；
答案的 ``conversion`` 写真实算式，``note`` 写页面写法与差值。

关联证据=推断（句面↔67 记录组属同一句式/同一 sub 链）；数值换算=确认（规则 + 原生累乘/
累加点）。不承诺最终伤害/扣血；不含 Chain 与等级成长。

未并入：同一张卡其它档位里存在「同筛选签名、p0 更高」的 67 记录（1271/6329/8345 的
p0=4/5 落在别的档位 sub 里）时，是否与本句同一阶梯未证——只在 note 披露记录号与原值，
不并入本数值。
"""
from __future__ import annotations

import json

import rules as R

MODULE_VERSION = 'type67_20261028'
SCOPE = 'TYPE67_BATCH_20261028'
TAG = '推断（模板批 type67 阶梯）'
FAMILY = 'type67 阶梯（…が多いほど：人数计数×逐记录累乘/累加）'

SENTENCE_KEY = '多いほど'
TABLE = 'skilllist'
LAYERS = ('APK', 'CACHE')

ZERO_TOUCH_CIDS = frozenset({30236, 30239})

# G4：非法计数域（无原生计数证据）。命中即 hint，不出数。
FOREIGN_DOMAIN_MARKS = ('マナ', '敵の数', '職業の種類', '状態異常')
# G4：合法计数域（原生 CalcCharaNum 的成员列表＋三项筛选）。
MEMBER_DOMAIN_MARK = '味方'

# 槽位 → 句面属性词（G8）。句子没点名该属性就不为该槽出数。
SLOT_STAT = {
    'param1': '攻撃力',
    'param2': '移動速度',
    'param3': '防御力',
    'param6': 'クリティカル発生率',
    'param7': 'クリティカル威力',
}
# 槽位 → 效果类型（账本窄映射用；见 effect_ledger 本批块）。
SLOT_EFFECT = {
    'param1': '攻撃力',
    'param2': '移動速度',
    'param3': '防御力',
    'param6': 'クリティカル発生率',
    'param7': 'クリティカル威力',
}
MULTIPLICATIVE = ('param1', 'param2', 'param3')
ADDITIVE = ('param6', 'param7')

RULE_KEYS = tuple(f'skilllist|67|/{slot}' for slot in SLOT_STAT)

MAX_SUB_DEPTH = 3

REJECT_ORDER = ('ZERO_TOUCH_CID', 'NOT_SKILLLIST_LAYER', 'SENTENCE_MISMATCH',
                'FOREIGN_COUNT_DOMAIN', 'SUB_UNRESOLVED', 'SHAPE_NOT_LADDER',
                'FILTER_SIGNATURE_MIXED', 'ALREADY_ANSWERED', 'RULE_UNAVAILABLE',
                'NO_NAMED_SLOT')


def _norm(text: str) -> str:
    import unicodedata
    return unicodedata.normalize('NFKC', str(text or ''))


def _is_num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def skill_lookup(data, layer):
    """原始主表的 skillid → (index, record)。CACHE/APK 分源，不跨层。"""
    table = getattr(data, 'cache_skill' if layer == 'CACHE' else 'apk_skill', None)
    return table or {}


def resolve_chain(data, layer, record):
    """记录 + sub 递归展开（同层）；返回 (chain, unresolved_ids)。"""
    lookup = skill_lookup(data, layer)
    chain, missing, seen = [record], [], {record.get('skillid')}
    frontier = [(record.get('skillid'), 0)]
    while frontier:
        sid, depth = frontier.pop(0)
        head = next((c for c in chain if c.get('skillid') == sid), None) or record
        subs = head.get('sub') or []
        if depth >= MAX_SUB_DEPTH:
            if subs:
                missing.append(dict(parent=sid, reason='DEPTH_LIMIT', sub=list(subs)))
            continue
        for child in subs:
            if child in seen:
                continue
            hit = lookup.get(child)
            if hit is None:
                missing.append(dict(parent=sid, reason='MISSING_IN_LAYER', sub=child))
                continue
            seen.add(child)
            chain.append(hit[1])
            frontier.append((child, depth + 1))
    return chain, missing


def ladder_records(chain):
    return [c for c in chain if c.get('ability') == 67]


def filter_signature(record):
    p8 = record.get('param8')
    return (record.get('iParam0'), record.get('flag0_0'),
            int(p8) if _is_num(p8) else p8)


def shape_gate(recs):
    """G5 形状门：返回 (ok, reason, p0s)。"""
    if len(recs) < 2:
        return False, 'NEED_AT_LEAST_TWO_RECORDS', []
    p0s = []
    for rec in recs:
        value = rec.get('param0')
        if not _is_num(value) or float(value) != int(float(value)):
            return False, 'NON_INTEGER_P0', p0s
        p0s.append(int(float(value)))
    ordered = sorted(p0s)
    if ordered != list(range(1, len(p0s) + 1)):
        return False, 'P0_NOT_CONTIGUOUS_FROM_ONE', p0s
    return True, None, p0s


def ordered_ladder(recs):
    return sorted(recs, key=lambda r: int(float(r.get('param0'))))


def neutral(slot, record):
    value = record.get(slot)
    if not _is_num(value):
        return True
    return abs(float(value) - (1.0 if slot in MULTIPLICATIVE else 0.0)) < 1e-12


def _cascade(slot, ladder):
    """逐人累计值：返回 [(p0, 累计值)]；倍率连乘、加算累加。"""
    out = []
    acc = 1.0 if slot in MULTIPLICATIVE else 0.0
    for rec in ladder:
        value = float(rec.get(slot) or 0.0)
        acc = acc * value if slot in MULTIPLICATIVE else acc + value
        out.append((int(float(rec.get('param0'))), acc))
    return out


def _fmt(value: float, digits: int = 4) -> str:
    text = f'{value:.{digits}f}'.rstrip('0').rstrip('.')
    return text or '0'


def _pct(value: float) -> str:
    """百分比：带符号、一位小数（项目既有页面文案口径用 ASCII '-'）。"""
    if abs(value) < 5e-5:
        return '±0.0%'
    return f'{"+" if value > 0 else "-"}{abs(value):.1f}%'


def value_text(slot, steps):
    parts = []
    for p0, acc in steps:
        if slot == 'param1':
            text = f'{p0}人 ×{_fmt(acc)}（攻击 {_pct((acc - 1.0) * 100)}）'
        elif slot == 'param2':
            text = f'{p0}人 ×{_fmt(acc)}（移速 {_pct((acc - 1.0) * 100)}）'
        elif slot == 'param3':
            text = f'{p0}人 ×{_fmt(acc)}（受伤 {_pct((acc - 1.0) * 100)}）'
        elif slot == 'param6':
            text = f'{p0}人 +{acc * 100:.1f}pp'
        else:
            text = f'{p0}人 +{_fmt(acc)}（{_pct(acc * 100)}）'
        parts.append(text)
    return '；'.join(parts)


def _slot_unit_text(slot, steps):
    if slot in MULTIPLICATIVE:
        return f'每多一名符合条件的味方乘一次（连乘）：{value_text(slot, steps)}'
    return f'每多一名符合条件的味方加一次（逐条累加）：{value_text(slot, steps)}'


def evaluate(cid, layer, table, record, row, *, data=None, extra_domain=()):
    """单行门控。返回 dict(status=ACCEPT|REJECT, reject, gates, answers, ladder)。"""
    row = row or {}
    frag = str(row.get('japanese') or '')
    gates = {}
    if cid in ZERO_TOUCH_CIDS:
        return dict(status='REJECT', reject='ZERO_TOUCH_CID', gates={'G1_not_zero_touch': False},
                    answers=[], ladder=None)
    gates['G1_not_zero_touch'] = True
    if not (table == TABLE and layer in LAYERS and isinstance(record, dict)):
        return dict(status='REJECT', reject='NOT_SKILLLIST_LAYER',
                    gates={**gates, 'G2_carrier': False}, answers=[], ladder=None)
    chain, missing = resolve_chain(data, layer, record)
    gates['G2_carrier'] = True
    if SENTENCE_KEY not in frag:
        return dict(status='REJECT', reject='SENTENCE_MISMATCH',
                    gates={**gates, 'G3_sentence': False}, answers=[], ladder=None)
    gates['G3_sentence'] = True
    if any(mark in frag for mark in FOREIGN_DOMAIN_MARKS) or MEMBER_DOMAIN_MARK not in frag:
        return dict(status='REJECT', reject='FOREIGN_COUNT_DOMAIN',
                    gates={**gates, 'G4_member_domain': False}, answers=[], ladder=None)
    gates['G4_member_domain'] = True
    if missing:
        return dict(status='REJECT', reject='SUB_UNRESOLVED',
                    gates={**gates, 'G2_sub_resolved': False}, answers=[], ladder=None,
                    missing=missing)
    gates['G2_sub_resolved'] = True
    recs = ladder_records(chain)
    ok, reason, p0s = shape_gate(recs)
    gates['G5_shape'] = ok
    if not ok:
        return dict(status='REJECT', reject='SHAPE_NOT_LADDER',
                    gates=gates, answers=[], ladder=dict(p0s=p0s, reason=reason))
    signatures = {filter_signature(rec) for rec in recs}
    gates['G5b_single_filter'] = len(signatures) == 1
    if len(signatures) != 1:
        return dict(status='REJECT', reject='FILTER_SIGNATURE_MIXED', gates=gates,
                    answers=[], ladder=dict(p0s=p0s, reason='MIXED'))
    if row.get('answers'):
        return dict(status='REJECT', reject='ALREADY_ANSWERED',
                    gates={**gates, 'G6_no_existing_answer': False}, answers=[], ladder=None)
    gates['G6_no_existing_answer'] = True
    ladder = ordered_ladder(recs)
    named = [slot for slot, stat in SLOT_STAT.items() if stat in frag]
    active = [slot for slot in named
              if any(not neutral(slot, rec) for rec in ladder)]
    gates['G8_named_slot'] = bool(active)
    if not active:
        return dict(status='REJECT', reject='NO_NAMED_SLOT',
                    gates={**gates, 'G8_named_slot': False}, answers=[], ladder=None)
    rules_gate = {}
    for slot in active:
        field = '/' + slot
        probe = R.answer_for(TABLE, 67, field, ladder[0].get(slot), ladder[0],
                             source_layer=layer)
        rule = R.rule_for(TABLE, 67, field) or {}
        rules_gate[slot] = bool(probe and probe.get('answer_status') == 'CONFIRMED_NUMERIC'
                                and '已确认' in str(rule.get('status') or ''))
    gates.update({f'G7_rule_{slot}': ok for slot, ok in rules_gate.items()})
    if not all(rules_gate.values()):
        return dict(status='REJECT', reject='RULE_UNAVAILABLE', gates=gates, answers=[],
                    ladder=None)
    answers = build_answers(cid, row, layer, ladder, active, data,
                            extra_domain=extra_domain)
    return dict(status='ACCEPT', reject=None, gates=gates, answers=answers,
                ladder=dict(p0s=p0s, records=[r.get('skillid') for r in ladder],
                            signature=filter_signature(ladder[0])))


def _record_key(layer, index):
    return (f'{layer}/_mdSkill.json#/skilllist/{index}' if layer == 'APK'
            else f'{layer}/skilllist.data5.json.raw#/skilllist/{index}')


def _source(data, layer, record, field):
    lookup = skill_lookup(data, layer)
    hit = lookup.get(record.get('skillid'))
    index = hit[0] if hit else None
    source_key = f'{layer}/_mdSkill.json' if layer == 'APK' else f'{layer}/skilllist.data5.json.raw'
    original = ('output/base_master/_mdSkill.json' if layer == 'APK'
                else 'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')
    return dict(table=TABLE, record_id=record.get('skillid'), layer=layer,
                source_key=source_key,
                record_key=_record_key(layer, index) if index is not None else None,
                json_pointer=(f'/skilllist/{index}' if index is not None else None),
                original_file=original,
                field=field, field_path=field, raw_value=record.get(field[1:]),
                namespace=TABLE, ability_type=67)


_NOTE_COMMON = ('每多一名符合条件的味方，本项再累计一次（倍率连乘/暴击类逐条加算）；'
                '页面的「120%+5n%」式加算只是阅读简化，不是算法')


def build_answers(cid, row, layer, ladder, slots, data, extra_domain=()):
    out = []
    for slot in slots:
        steps = _cascade(slot, ladder)
        main = ladder[0]
        raw = main.get(slot)
        probe = R.answer_for(TABLE, 67, '/' + slot, raw, main, source_layer=layer) or {}
        rule = R.rule_for(TABLE, 67, '/' + slot) or {}
        extra = [e for e in extra_domain if e.get('slot') == slot] if extra_domain else []
        extra_note = ''
        if extra:
            extra_note = ('；另有同计数域（同 iParam0/flag0_0/param8）的 p0='
                          + '/'.join(str(e['p0']) for e in extra)
                          + ' 记录（' + '、'.join(str(e['skillid']) for e in extra)
                          + '）位于其它档位；是否与本句同一阶梯未证，未并入本数值')
        out.append(dict(
            value=_slot_unit_text(slot, steps),
            quantity_kind=probe.get('quantity_kind'),
            unit=probe.get('unit'),
            raw_value=raw,
            field_path='/' + slot,
            numeric_source='规则',
            numeric_evidence='确认',
            association_evidence='推断',
            evidence_scope=SCOPE,
            rule_key=f'skilllist|67|{"/" + slot}',
            rule_body_status=rule.get('status'),
            rule_status=rule.get('status'),
            conversion=(rule.get('conversion') or '') +
                       ('' if slot in MULTIPLICATIVE else '；阶梯内逐条累加（原生 fadd 累加点）'),
            base_definition=probe.get('base_definition'),
            conditions=rule.get('conditions'),
            rule_limits=rule.get('limits'),
            target=rule.get('target'),
            evidence=['output/character_skills/profiles/rules.json#skilllist|67|' + '/' + slot,
                      'output/character_skills/skilllist_types/composite_chains.json#' +
                      ('attack/67' if slot == 'param1' else
                       'move/67' if slot == 'param2' else
                       'defence/67' if slot == 'param3' else
                       'crit_rate/67' if slot == 'param6' else 'crit_dmg/67'),
                      '其他人的参考/CC解包数据_给GPT_20261027/claude_cc_site_pages/真实算法.md#§1'],
            source=_source(data, layer, main, '/' + slot),
            table=TABLE, record_id=main.get('skillid'), layer=layer,
            binding={'type67_binding': dict(
                scope=SCOPE, family='type67_ladder', row_id=row.get('row_id'), slot=slot,
                effect_type=SLOT_EFFECT[slot], rule_key=f'skilllist|67|/{slot}',
                carrier_record_id=main.get('skillid'), carrier_layer=layer,
                p0_domain='人数', filter_signature=list(filter_signature(main)),
                ladder=[dict(skillid=rec.get('skillid'), p0=int(float(rec.get('param0'))),
                             raw=rec.get(slot),
                             cumulative=(steps[i][1]))
                        for i, rec in enumerate(ladder)],
                combination=('multiply' if slot in MULTIPLICATIVE else 'add'))},
            note=(_NOTE_COMMON +
                  ('；暴击类按原生逐条加算（fadd 0x11195b0/0x1119dc0），不是连乘'
                   '（任务书 §1 的「同连乘结构」按原始累加点订正）' if slot in ADDITIVE else '') +
                  '；目标对象＝本记录实际装载者自身；以能力被装载并进入玩家侧 apply 路径为前提' +
                  extra_note),
            quantitative=True))
    return out


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
    marker = row.setdefault('inference_type67', dict(scope=SCOPE, claims=[]))
    marker['claims'].append(dict(family='type67_ladder', slot=answer['field_path'],
                                 record_id=answer['record_id'], rule_key=answer['rule_key'],
                                 value=answer['raw_value']))
    return True


def _hint(row, reason, detail=None):
    text = f'{TAG}：{reason}'
    if detail:
        text += f'（{detail}）'
    row['inference_type67_hint'] = text
    row.setdefault('inference_type67_meta', dict(scope=SCOPE, reason=reason, detail=detail))
    return text


def _domain_extra(data, layer, cid, signature, own_ids, groups):
    """同卡其它档位内同筛选签名的 67 记录（只披露，不并入）。"""
    out = []
    for group in groups:
        for skill in group.get('skills') or []:
            if skill.get('table') != TABLE or skill.get('layer') != layer:
                continue
            rec = _resolve_record(data, layer, skill.get('record_id'))
            if not isinstance(rec, dict):
                continue
            chain, _missing = resolve_chain(data, layer, rec)
            for cand in ladder_records(chain):
                if cand.get('skillid') in own_ids:
                    continue
                if filter_signature(cand) != signature:
                    continue
                out.append(dict(skillid=cand.get('skillid'),
                                p0=int(float(cand.get('param0') or 0)),
                                parent=rec.get('skillid')))
    return out


def _resolve_record(data, layer, skillid):
    hit = skill_lookup(data, layer).get(skillid)
    return hit[1] if hit else None


def apply_to_groups(data, cid, groups):
    """正式页消费：为「…が多いほど」阶梯行绑定本批答案（不覆盖/不删除既有答案）。"""
    report = dict(scope=SCOPE, cid=cid, answers_added=0, additions=[], rejections=[],
                  hints=0, skipped_existing=0, evaluated=0)
    if cid in ZERO_TOUCH_CIDS:
        report['zero_touch'] = True
        return report
    for group in groups:
        for skill in group.get('skills') or []:
            if skill.get('table') != TABLE:
                continue
            rows = [r for r in skill.get('rows') or [] if SENTENCE_KEY in str(r.get('japanese') or '')]
            if not rows:
                continue
            layer = skill.get('layer')
            record = _resolve_record(data, layer, skill.get('record_id'))
            for row in rows:
                report['evaluated'] += 1
                extra = []
                if isinstance(record, dict) and layer in LAYERS:
                    chain, _missing = resolve_chain(data, layer, record)
                    recs = ladder_records(chain)
                    ok, _reason, _p0s = shape_gate(recs)
                    if ok and len({filter_signature(r) for r in recs}) == 1:
                        extra = _domain_extra(data, layer, cid, filter_signature(recs[0]),
                                             {r.get('skillid') for r in recs}, groups)
                res = evaluate(cid, layer, skill.get('table'), record, row,
                               data=data, extra_domain=extra)
                if res['status'] != 'ACCEPT':
                    if res['reject'] == 'ALREADY_ANSWERED':
                        report['skipped_existing'] += 1
                        continue
                    # hint 只写本批句族（skilllist 载体）且无既有答案的行：不改其他族的答案行，
                    # 也不对非 skilllist 载体（supporterskill/charainfo 等）另立句族注记。
                    if row.get('answers'):
                        report['hint_skipped_existing'] = report.get('hint_skipped_existing', 0) + 1
                        report['rejections'].append(dict(row_id=row.get('row_id'),
                                                         reason=res['reject'],
                                                         note='ROW_ALREADY_ANSWERED_NO_HINT'))
                        continue
                    _hint(row, res['reject'],
                          '；'.join(f'{k}={v}' for k, v in sorted(res['gates'].items())
                                   if not v) or None)
                    report['hints'] += 1
                    report['rejections'].append(dict(row_id=row.get('row_id'),
                                                     reason=res['reject']))
                    continue
                added = 0
                for ans in res['answers']:
                    if _append(row, ans):
                        added += 1
                        report['additions'].append(dict(
                            row_id=row.get('row_id'), slot=ans['field_path'],
                            rule_key=ans['rule_key'], value=ans['value'],
                            raw_value=ans['raw_value'],
                            ladder=[(e['p0'], e['cumulative']) for e in
                                    ans['binding']['type67_binding']['ladder']]))
                report['answers_added'] += added
                row.setdefault('type67_gate', dict(res['gates']))
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='type67 阶梯批：句形/形状只读探针')
    ap.add_argument('--text', help='单句测试（是否属人数计数域）')
    args = ap.parse_args(argv)
    if args.text:
        frag = args.text
        print(json.dumps(dict(
            has_key=SENTENCE_KEY in frag,
            foreign=[m for m in FOREIGN_DOMAIN_MARKS if m in frag],
            member=MEMBER_DOMAIN_MARK in frag,
            named=[stat for stat in SLOT_STAT.values() if stat in frag]),
            ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == '__main__':
    raise SystemExit(_main())
