# -*- coding: utf-8 -*-
"""金币（type100）／经验值（type102）倍率＋超上限位表核对（2026-10-28 批 2）。

任务书：``docs/tasks/20261028-type100-102-batch.md``。规则引用：``docs/角色技能完整解读实施方案.md``
（2026-10-24 修订，含 §1.3）。协作者对照：``output/reference_analysis/cc_20261027/``
（merge_recommendations A5/A6/A11、rule_candidates R09/R10/R21、conflicts C3/C7）。

范围（逐行门控，任一不满足即拒答并记原因码；不出数）
----------------------------------------------------
G1  零触碰：cid∈{30236,30239} 不进入（30236 基线整卡、30239 同守）。
G2  载体：行属 ``table=skilllist``、``layer∈{APK,CACHE}``，记录可由**该层**原始主表按 skillid
    唯一解析（``output/base_master/_mdSkill.json`` / ``skilllist.data5.json.raw``）；sub 递归
    同层解析，缺件即拒。**CACHE/APK 同 skillid 不跨层取值**——同号两层的 param0 可以不同
    （实测 40839907：CACHE 1.35 / APK 1.30；40839908：CACHE 1.85 / APK 1.75），按载体所在层取，
    另层原值只作披露（写入答案 note 与 binding.other_layer_raw），不参与换算。
G3  句形：行片段含「ゴールド」或「経験値」；点名的能力决定要答的槽
    （ゴールド→ability 100、経験値→ability 102；两者都点名就两槽都要）。「ゴールドは減る」
    仍然是 ability 100（值为负向），不因方向换槽。
G4  载体选择（同一行、同一层）：先看本行自身记录链内 ability=100/102 的记录；链内没有时才
    允许「同卡其它 skilllist 记录链」取值（协作者 C11 口径：同卡、同层、**必须唯一**）。
    去重后 ≠1 ⇒ 拒（NO_CARRIER / CARRIER_NOT_UNIQUE），不猜、不合并多个值。
G5  形状：``param0`` 存在、有限、>0 且 ≠1（=1 与本句「増える／減る」矛盾，拒）。
G6  无既有答案：同一行已有同一 ``rule_key`` 的答案则跳过（不覆盖旧值；行内其它子句的既有
    答案保持不动）。
G7  语义源：``skilllist_types/dispatch_map.json#ability_type_enum`` 的 ``100=Gold``、
    ``102=Experience`` ＋ APK/CACHE 正文「戦闘で獲得するゴールド／経験値が増える」。
    **2026-10-28 规则登记批起，两键已正式登记进 ``profiles/rules.json``**
    （``scripts/character_skills/rules.py::_registration_20261028_specs``），本模块不再持有
    ``RULE_SPECS`` 文本，改为 ``rules.rule_for`` 读取规则、``rules.answer_for``（显式传
    ``source_layer``）读取换算文案——单一事实源在规则层，避免双写漂移。登记只改登记状态
    字段，数值零变化；答案 ``rule_registry``/``rule_status``/``numeric_source`` 如实记已登记。

答案（每槽 1 条）
-----------------
* 倍率＝``param0``；增加百分比＝``(p0−1)×100%``（A5/A6 口径）。
* 基线：战斗结算的金币／经验基准（未含其他加成）；不承诺入账实际数额。
* 关联证据＝推断（句面↔记录绑定，跨链时更弱）；数值换算＝确认（枚举＋明文＋单值记录）。
* 多条同类记录是否连乘**未证**——门控要求唯一载体，故不产生合成值。

超上限位表核对（只核对，不写页面答案）
--------------------------------------
* 位表来源：``boss_heal_types/type_rules.json#heal_family.over_heal_bits/over_heal_ratios``
  与 ``output/boss_heal/constants.json#bits/values``，复用 ``rules._SUPER_LIMIT_BITS``/
  ``_SUPER_LIMIT_VALUES``/``decode_super_limit``（只读，不改 rules.py）。
* 映射：flag0_1 左移 32 位 → 命中完整 bit；bit 40→1.2（上限 20%）、bit 41→1.4（40%）、
  bit 42→1.6（60%）、bit 43→1.8（80%）、bit 44→2.0（100%）、bit 35→1.3（30%）。
  即 flag0_1 值 256→20%、512→40%、1024→60%、2048→80%、4096→100%、8→30%。
  多个位同时置位时按 ``s_flagList`` 反序取首个（最高位）。
* **flag1_1 没有已确认映射**：现存确认键只有 ``skilllist|21|/flag0_1`` 与
  ``bossskill|27|/skillflag0_1``；``skilllist|1059|/flag1_0`` 是受益对象武器位图（另一语义），
  证明 flag1_* 不等于超上限掩码。本模块对 flag1_1 只登记「未知/未解码」，不填零不猜。
* 本批**不新增**超上限页面答案（现存 53 条 ``skilllist|21|/flag0_1`` 答案族不受影响）；
  任务书 §1 对该项要求「核对」，核对结论见 ``verify_super_limit`` 与交付目录探针。
"""
from __future__ import annotations

import json
import math

import rules as R

MODULE_VERSION = 'gold_exp_20261028'
SCOPE = 'GOLD_EXP_BATCH_20261028'
TAG = '推断（模板批 金币/经验倍率）'
FAMILY = 'gold_exp_multiplier（type100 金币／type102 经验倍率）'

TABLE = 'skilllist'
LAYERS = ('APK', 'CACHE')
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

# 句面词 → ability。两者都出现时两槽都要答。
ABILITY_MARK = {100: 'ゴールド', 102: '経験値'}
ABILITY_LABEL = {100: '金币', 102: '经验值'}
ABILITY_ENUM = {100: 'Gold', 102: 'Experience'}
RULE_KEYS = {100: 'skilllist|100|/param0', 102: 'skilllist|102|/param0'}

MAX_SUB_DEPTH = 3

# 规则键与字段（规则正文自 2026-10-28 规则登记批起只存在于规则层；本模块不再持有副本）。
FIELD_PATH = '/param0'


def _rule(ability):
    """规则层规则行（登记批后为唯一事实源；缺键即拒答，不退回未登记口径）。"""
    rule = R.rule_for(TABLE, ability, FIELD_PATH)
    if not rule:
        raise RuntimeError(f'规则登记批：rules 层缺键 {RULE_KEYS[ability]}，拒绝在未登记状态下出数')
    return rule


def answer_core(ability, raw, layer):
    """规则层换算结果（value_text／quantity_kind／unit）。

    ``source_layer`` 是登记的来源限定门：只有显式声明载体层的消费者才可取到答案，
    无层证据的旧调用方（页面 record_evidence 逐字段外推）返回 None，不会产生树答案。
    """
    record = {'ability': ability, FIELD_PATH.lstrip('/'): raw}
    ans = R.answer_for(TABLE, ability, FIELD_PATH, raw, record, source_layer=layer)
    if not ans:
        raise RuntimeError(f'规则登记批：answer_for 未返回 {RULE_KEYS[ability]}'
                           f'（layer={layer} raw={raw!r}）')
    return ans


def registration_assertions():
    """模块侧等价断言（scratch 调用）：登记后的规则行与出数文案一致、状态记已登记。"""
    out = []
    for ability in (100, 102):
        rule = _rule(ability)
        core = answer_core(ability, 2.5, 'CACHE')
        label = ABILITY_LABEL[ability]
        out.append(dict(
            rule_key=RULE_KEYS[ability], present=True,
            registered=('已登记' in (rule.get('status') or '')
                        and '未登记' not in (rule.get('status') or '')),
            unit_ok=rule.get('unit') == core.get('unit') == '倍率（相对战斗结算基准）',
            conversion_ok=('(param0−1)×100%' in (rule.get('conversion') or '')
                           and '基准 × param0' in (rule.get('conversion') or '')),
            value_text=core['value_text'],
            value_text_ok=(core['value_text'] == f'{label}获得 ×2.5（本项 +150%）'),
            quantity_kind_ok=(core.get('quantity_kind') == f'{label}获得倍率'),
            conditions_present=bool(rule.get('conditions') or rule.get('applicability')),
            limits_present=bool(rule.get('limits')),
            target_present=bool(rule.get('target')),
            evidence_present=bool(rule.get('evidence')),
            base_definition_present=bool(rule.get('base_definition')),
            no_pct_zero=('+150%' in core['value_text'] and '±0%' not in core['value_text']),
        ))
    return out

REJECT_ORDER = ('ZERO_TOUCH_CID', 'NOT_SKILLLIST_LAYER', 'SENTENCE_MISMATCH',
                'SUB_UNRESOLVED', 'NO_CARRIER', 'CARRIER_NOT_UNIQUE', 'SHAPE_INVALID',
                'ALREADY_ANSWERED')

# 超上限：期望映射（任务书交叉验证点）。key＝flag0_1 原值。
SUPER_LIMIT_EXPECT = {
    256: dict(bit=40, cap=1.2, pct=20),
    512: dict(bit=41, cap=1.4, pct=40),
    1024: dict(bit=42, cap=1.6, pct=60),
    2048: dict(bit=43, cap=1.8, pct=80),
    4096: dict(bit=44, cap=2.0, pct=100),
    8: dict(bit=35, cap=1.3, pct=30),
}


def _norm(text: str) -> str:
    import unicodedata
    return unicodedata.normalize('NFKC', str(text or ''))


def _is_num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


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
                missing.append(dict(parent=head.get('skillid'), reason='DEPTH_LIMIT',
                                    sub=list(subs)))
            continue
        for child in subs:
            if child in seen:
                continue
            hit = lookup.get(child)
            if hit is None:
                missing.append(dict(parent=head.get('skillid'), reason='MISSING_IN_LAYER',
                                    sub=child))
                continue
            seen.add(child)
            chain.append(hit[1])
            frontier.append((hit[1], depth + 1))
    return chain, missing


def ability_records(chain, ability):
    return [c for c in chain if c.get('ability') == ability]


def _resolve_record(data, layer, skillid):
    hit = (skill_lookup(data, layer) or {}).get(skillid)
    return hit[1] if hit else None


def card_candidates(data, groups, layer, ability):
    """同卡、同层、全部 skilllist 记录链里的 ability 记录（按 skillid 去重）。"""
    out = {}
    for group in groups or []:
        for skill in group.get('skills') or []:
            if skill.get('table') != TABLE or skill.get('layer') != layer:
                continue
            rec = _resolve_record(data, layer, skill.get('record_id'))
            if not isinstance(rec, dict):
                continue
            chain, _missing = resolve_chain(data, layer, rec)
            for cand in ability_records(chain, ability):
                out.setdefault(cand.get('skillid'), cand)
    return list(out.values())


def carriers(data, layer, record, groups, ability):
    """返回 (candidates, source)。source∈{'own_chain','same_card_cross_chain'}。"""
    own = ability_records(resolve_chain(data, layer, record)[0], ability)
    if own:
        uniq = {}
        for cand in own:
            uniq.setdefault(cand.get('skillid'), cand)
        return list(uniq.values()), 'own_chain'
    return card_candidates(data, groups, layer, ability), 'same_card_cross_chain'


def other_layer_raw(data, ability, skillid, layer):
    """同 skillid 在另一层的 param0（只披露，不参与换算）。"""
    other = 'APK' if layer == 'CACHE' else 'CACHE'
    rec = _resolve_record(data, other, skillid)
    if not isinstance(rec, dict) or rec.get('ability') != ability:
        return None
    return rec.get('param0')


def _fmt_num(value) -> str:
    text = f'{float(value):.6g}'
    return text


def _record_key(layer, index):
    return (f'{layer}/_mdSkill.json#/skilllist/{index}' if layer == 'APK'
            else f'{layer}/skilllist.data5.json.raw#/skilllist/{index}')


def _source(data, layer, record, ability):
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
                original_file=original, field='/param0', field_path='/param0',
                raw_value=record.get('param0'), namespace=TABLE, ability_type=ability)


def shape_ok(carrier):
    p0 = carrier.get('param0')
    if not _is_num(p0):
        return False, 'P0_MISSING_OR_NOT_NUMERIC'
    if p0 <= 0:
        return False, 'P0_NOT_POSITIVE'
    if abs(float(p0) - 1.0) < 1e-12:
        return False, 'P0_NEUTRAL_CONTRADICTS_SENTENCE'
    return True, None


def evaluate(cid, layer, table, record, row, *, data=None, groups=()):
    """单行门控。返回 dict(status, reject, gates, answers, per_ability)。"""
    row = row or {}
    frag = str(row.get('japanese') or '')
    gates = {}
    if cid in ZERO_TOUCH_CIDS:
        return dict(status='REJECT', reject='ZERO_TOUCH_CID', gates={'G1_not_zero_touch': False},
                    answers=[], per_ability={})
    gates['G1_not_zero_touch'] = True
    if not (table == TABLE and layer in LAYERS and isinstance(record, dict)):
        return dict(status='REJECT', reject='NOT_SKILLLIST_LAYER',
                    gates={**gates, 'G2_carrier': False}, answers=[], per_ability={})
    gates['G2_carrier'] = True
    need = [ab for ab in (100, 102) if ABILITY_MARK[ab] in frag]
    if not need:
        return dict(status='REJECT', reject='SENTENCE_MISMATCH',
                    gates={**gates, 'G3_sentence': False}, answers=[], per_ability={})
    gates['G3_sentence'] = True
    _chain, missing = resolve_chain(data, layer, record)
    if missing:
        return dict(status='REJECT', reject='SUB_UNRESOLVED',
                    gates={**gates, 'G2_sub_resolved': False}, answers=[], per_ability={},
                    missing=missing)
    gates['G2_sub_resolved'] = True

    per, answers = {}, []
    for ability in need:
        cands, source = carriers(data, layer, record, groups, ability)
        key = str(ability)
        if not cands:
            per[key] = dict(status='REJECT', reason='NO_CARRIER', source=source)
            continue
        if len(cands) != 1:
            per[key] = dict(status='REJECT', reason='CARRIER_NOT_UNIQUE', source=source,
                            candidates=[c.get('skillid') for c in cands],
                            params=[c.get('param0') for c in cands])
            continue
        carrier = cands[0]
        ok, why = shape_ok(carrier)
        if not ok:
            per[key] = dict(status='REJECT', reason='SHAPE_INVALID', source=source,
                            carrier=carrier.get('skillid'), detail=why,
                            param0=carrier.get('param0'))
            continue
        if any(str(a.get('rule_key')) == RULE_KEYS[ability] for a in row.get('answers') or []):
            per[key] = dict(status='REJECT', reason='ALREADY_ANSWERED', source=source,
                            carrier=carrier.get('skillid'))
            continue
        answers.append(build_answer(cid, row, layer, carrier, ability, source, data))
        per[key] = dict(status='ACCEPT', source=source, carrier=carrier.get('skillid'),
                        param0=carrier.get('param0'),
                        other_layer_raw=other_layer_raw(data, ability, carrier.get('skillid'),
                                                        layer))
    if answers:
        return dict(status='ACCEPT', reject=None, gates=gates, answers=answers,
                    per_ability=per)
    reasons = [v['reason'] for v in per.values()]
    reject = next((r for r in REJECT_ORDER if r in reasons), reasons[0] if reasons else 'NO_CARRIER')
    return dict(status='REJECT', reject=reject, gates=gates, answers=[], per_ability=per)


def build_answer(cid, row, layer, carrier, ability, source_kind, data):
    rule = _rule(ability)
    core = answer_core(ability, carrier.get('param0'), layer)
    raw = carrier.get('param0')
    other = other_layer_raw(data, ability, carrier.get('skillid'), layer)
    layer_note = ''
    if other is not None and _is_num(other) and abs(float(other) - float(raw)) > 1e-9:
        layer_note = (f'；同 skillid {carrier.get("skillid")} 在另一层 param0={_fmt_num(other)}，'
                      f'按载体层 {layer} 取值（不跨层混用）')
    bind_note = ('；载体为本行记录自身链' if source_kind == 'own_chain'
                 else '；本行记录链内无该能力记录，按同卡同层唯一记录取值')
    return dict(
        value=core['value_text'],
        quantity_kind=core['quantity_kind'],
        unit=core['unit'],
        raw_value=raw,
        field_path='/param0',
        numeric_source=('规则（rules.json#' + RULE_KEYS[ability] + '，规则登记批 2026-10-28 已登记；'
                        'dispatch_map 枚举＋APK/CACHE 正文）'),
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
        binding={'gold_exp_binding': dict(
            scope=SCOPE, family='gold_exp_multiplier', ability=ability,
            enum=ABILITY_ENUM[ability], row_id=row.get('row_id'), slot='param0',
            rule_key=RULE_KEYS[ability],
            carrier_record_id=carrier.get('skillid'), carrier_layer=layer,
            carrier_source=source_kind, raw=raw, other_layer_raw=other)},
        note=('倍率=param0；增减百分比=(param0−1)×100%；基线为战斗结算的'
              + ABILITY_LABEL[ability] +
              '基准，不承诺入账实际数额；多条同类记录是否连乘未证（本句唯一载体）' +
              bind_note + layer_note),
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
    marker = row.setdefault('inference_gold_exp', dict(scope=SCOPE, claims=[]))
    marker['claims'].append(dict(family='gold_exp_multiplier',
                                 ability=answer['binding']['gold_exp_binding']['ability'],
                                 rule_key=answer['rule_key'], record_id=answer['record_id'],
                                 value=answer['raw_value']))
    return True


def _hint(row, reason, detail=None):
    text = f'{TAG}：{reason}'
    if detail:
        text += f'（{detail}）'
    row['inference_gold_exp_hint'] = text
    row.setdefault('inference_gold_exp_meta', dict(scope=SCOPE, reason=reason, detail=detail))
    return text


def apply_to_groups(data, cid, groups):
    """正式页消费：为金币/经验句绑定本批答案（不覆盖/不删除既有答案）。"""
    report = dict(scope=SCOPE, cid=cid, answers_added=0, additions=[], rejections=[],
                  hints=0, skipped_existing=0, evaluated=0, cross_chain=0)
    if cid in ZERO_TOUCH_CIDS:
        report['zero_touch'] = True
        return report
    for group in groups or []:
        for skill in group.get('skills') or []:
            if skill.get('table') != TABLE:
                continue
            rows = [r for r in skill.get('rows') or []
                    if any(mark in str(r.get('japanese') or '') for mark in ABILITY_MARK.values())]
            if not rows:
                continue
            layer = skill.get('layer')
            record = _resolve_record(data, layer, skill.get('record_id'))
            for row in rows:
                report['evaluated'] += 1
                res = evaluate(cid, layer, skill.get('table'), record, row,
                               data=data, groups=groups)
                if res['status'] != 'ACCEPT':
                    if res['reject'] == 'ALREADY_ANSWERED':
                        report['skipped_existing'] += 1
                        continue
                    # hint 只写本批句族（skilllist 载体、句面点名金币/经验）且该槽无既有答案；
                    # 其它表的同句式（leader_ability/supporterskill 等）不立本批句族注记。
                    if not any(str(a.get('rule_key') or '').startswith(('skilllist|100|',
                                                                       'skilllist|102|'))
                               for a in row.get('answers') or []):
                        detail = '；'.join(f'{k}:{v.get("reason")}'
                                          for k, v in sorted((res.get('per_ability') or {}).items()))
                        _hint(row, res['reject'], detail or None)
                        report['hints'] += 1
                    report['rejections'].append(dict(row_id=row.get('row_id'),
                                                     reason=res['reject'],
                                                     per_ability=res.get('per_ability')))
                    continue
                added = 0
                for ans in res['answers']:
                    if _append(row, ans):
                        added += 1
                        report['additions'].append(dict(
                            row_id=row.get('row_id'), ability=ans['binding']['gold_exp_binding']['ability'],
                            rule_key=ans['rule_key'], value=ans['value'],
                            raw_value=ans['raw_value'],
                            carrier=ans['record_id'], carrier_layer=ans['layer'],
                            carrier_source=ans['binding']['gold_exp_binding']['carrier_source']))
                        if ans['binding']['gold_exp_binding']['carrier_source'] == \
                                'same_card_cross_chain':
                            report['cross_chain'] += 1
                report['answers_added'] += added
                rejected = {k: v for k, v in (res.get('per_ability') or {}).items()
                            if v.get('status') != 'ACCEPT'}
                if rejected:
                    report['rejections'].append(dict(row_id=row.get('row_id'),
                                                     reason='PARTIAL',
                                                     per_ability=rejected))
                row.setdefault('gold_exp_gate', dict(res['gates']))
    return report


# ---------------------------------------------------------------------------
# 超上限位表核对（不写页面答案）
# ---------------------------------------------------------------------------
def super_limit_sources(root=None):
    """读取三处位表（只读）：type_rules.json、boss_heal/constants.json、rules 常量。"""
    from pathlib import Path
    root = Path(root or '.')
    tr = json.loads((root / 'output/character_skills/boss_heal_types/type_rules.json')
                    .read_text(encoding='utf-8'))['heal_family']
    const = json.loads((root / 'output/boss_heal/constants.json').read_text(encoding='utf-8'))
    return dict(type_rules_bits=list(tr['over_heal_bits']),
                type_rules_ratios=list(tr['over_heal_ratios']),
                constants_bits=list(const['bits']['values']),
                constants_values=list(const['values']['values']),
                rules_bits=list(R._SUPER_LIMIT_BITS),
                rules_values=list(R._SUPER_LIMIT_VALUES))


def decode_flag0_1(value):
    """复用 rules.decode_super_limit（左移 32 位 + 反序取首个置位）。"""
    return R.decode_super_limit(value, 32)


def verify_super_limit(root=None, *, pages=None):
    """位表一致性 + 期望映射 + 交叉验证卡 + flag1_1 未解码披露。

    ``pages``：{cid: card.json} 可选；用于核对现存 ``skilllist|21|/flag0_1`` 答案与本表一致。
    """
    src = super_limit_sources(root)
    checks = []

    def check(name, ok, detail):
        checks.append(dict(name=name, ok=bool(ok), detail=detail))
        return ok

    check('table_type_rules_equals_constants',
          src['type_rules_bits'] == src['constants_bits']
          and len(src['type_rules_ratios']) == len(src['constants_values'])
          and all(abs(a - b) < 1e-6 for a, b in
                  zip(src['type_rules_ratios'], src['constants_values'])),
          dict(type_rules=src['type_rules_bits'], constants=src['constants_bits']))
    check('table_equals_rules_constants',
          src['type_rules_bits'] == src['rules_bits']
          and all(abs(a - b) < 1e-6 for a, b in
                  zip(src['type_rules_ratios'], src['rules_values'])),
          dict(rules_bits=src['rules_bits']))
    mapping = {}
    for value, expect in sorted(SUPER_LIMIT_EXPECT.items()):
        dec = decode_flag0_1(value)
        # float32 存储：1.2000000476837158 → 20.000005%，按 3 位小数归一后比较
        got = dict(bit=dec['selected_bit'], cap=round(dec['cap_ratio'], 6),
                   pct=round((dec['cap_ratio'] - 1) * 100, 3))
        mapping[str(value)] = dict(expected=expect, got=got, ok=(got['bit'] == expect['bit']
                                                                 and abs(got['cap'] - expect['cap']) < 1e-6))
    check('expected_flag_mapping', all(v['ok'] for v in mapping.values()), mapping)
    check('zero_flag_is_neutral', decode_flag0_1(0)['cap_ratio'] == 1.0
          and decode_flag0_1(0)['selected_bit'] is None, decode_flag0_1(0))
    check('highest_bit_wins',
          abs(decode_flag0_1(256 + 512)['cap_ratio'] - 1.4) < 1e-6,
          dict(flag0_1=768, selected=decode_flag0_1(768)))
    check('flag1_1_not_decoded',
          True, 'flag1_1 无已确认映射（确认键仅 skilllist|21|/flag0_1、'
                'bossskill|27|/skillflag0_1）；本模块不解码、不填零')

    # 交叉验证卡（原始记录独立给出，不读页面）
    cross = {}
    if pages is not None:
        cache = json.loads((__import__('pathlib').Path(root or '.') /
                            'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')
                           .read_text(encoding='utf-8'))['skilllist']
        by_id = {r.get('skillid'): r for r in cache}
        # 第三项标签修正（2026-10-28 批4 落修，第三方向审查范围限制②）：记录 40129210
        # 实属 cid 1292（其超上限位在 flag1_1）；原占位标签 11234 是创建时误写。
        # 同一 cid 有两张交叉验证卡（40129204 有数值断言、40129210 无），故键改为
        # ``cid#skillid`` 以免后者覆盖前者——expect_pct 与全部数值断言均不变
        # （30246→40%、1292#40129204→20%、1292#40129210→None）。
        for cid, skillid, expect_pct in ((30246, 43024601, 40), (1292, 40129204, 20),
                                         (1292, 40129210, None)):
            rec = by_id.get(skillid) or {}
            flag = rec.get('flag0_1')
            dec = decode_flag0_1(flag) if isinstance(flag, int) else None
            row = dict(skillid=skillid, ability=rec.get('ability'), flag0_1=flag,
                       decoded=dec,
                       pct=None if not dec else round((dec['cap_ratio'] - 1) * 100, 3))
            if expect_pct is not None:
                row['expected_pct'] = expect_pct
                row['ok'] = bool(dec and abs(row['pct'] - expect_pct) < 1e-3)
            cross[f'{cid}#{skillid}'] = row
        # 现存 type21 超上限答案族（53 条）与本表一致
        found, bad = 0, []
        for cid, page in (pages or {}).items():
            for group in page.get('groups') or []:
                for skill in group.get('skills') or []:
                    for row in skill.get('rows') or []:
                        for ans in row.get('answers') or []:
                            if ans.get('rule_key') != 'skilllist|21|/flag0_1':
                                continue
                            found += 1
                            raw = ans.get('raw_value')
                            dec = decode_flag0_1(raw) if isinstance(raw, int) else None
                            text = str(ans.get('value') or '')
                            if not dec or f'上限 {dec["cap_ratio"]:.6g}' not in text:
                                bad.append(dict(cid=cid, row_id=row.get('row_id'),
                                                raw=raw, value=text[:80]))
        check('existing_type21_answers_match_table', found > 0 and not bad,
              dict(found=found, mismatches=bad[:5]))
        for value in sorted({v.get('flag0_1') for v in cross.values() if v.get('flag0_1')}):
            pass
    check('cross_validation_cards',
          all(v.get('ok', True) for v in cross.values()), cross)
    return dict(scope=SCOPE, module=MODULE_VERSION, sources=src, checks=checks,
                cross_validation=cross,
                all_ok=all(c['ok'] for c in checks),
                boundary='只核对位表与交叉验证卡；本批不新增超上限页面答案，'
                         '现存 skilllist|21|/flag0_1 答案族原样保留。')


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='金币/经验倍率批：句形/载体只读探针')
    ap.add_argument('--text', help='单句测试（点名了哪些能力）')
    ap.add_argument('--flag', type=int, help='flag0_1 原值 → 超上限档位')
    ap.add_argument('--super-limit', action='store_true', help='位表核对（无页面输入）')
    args = ap.parse_args(argv)
    if args.text:
        frag = args.text
        print(json.dumps(dict(
            needs=[dict(ability=ab, mark=ABILITY_MARK[ab]) for ab in (100, 102)
                   if ABILITY_MARK[ab] in frag],
            gold=ABILITY_MARK[100] in frag, exp=ABILITY_MARK[102] in frag),
            ensure_ascii=False, indent=1))
        return 0
    if args.flag is not None:
        print(json.dumps(decode_flag0_1(args.flag), ensure_ascii=False, indent=1))
        return 0
    if args.super_limit:
        print(json.dumps(verify_super_limit(), ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == '__main__':
    raise SystemExit(_main())
