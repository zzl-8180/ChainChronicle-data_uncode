# -*- coding: utf-8 -*-
"""クリティカル吸収（ability21 StealHP／skilllist 65000003｜CACHE）推断模块。

任务书：``docs/tasks/20261026-crit-absorb-batch.md``；预检
``output/character_skills/inference_inventory/yg_alternative_precheck_20261026/precheck_report.md``。

范围（逐行门控，任一不满足即拒答并记原因码）
--------------------------------------------
G1  行表/层/引用位：``table=job_ability`` ∧ ``layer=CACHE`` ∧
    ``reference_field='job_ability.cids contains cid'``。
G2  句式逐字句：行片段 ``japanese`` 与
    ``クリティカル攻撃時に与えたダメージ量に応じて、自身のHPが上限を超えて回復する。``
    逐字相等（NFKC 后亦相等）。
G3  段序：行记录正文恰 3 个◆段，第 3◆段（0 基段号 2）逐字等于本句，且
    ``fragment_index==2``。第 3◆段 ↔ ``skill_ids[2]`` 位置序（b5 批同法）。
G4  载体唯一：``skill_ids[2]`` 解析为 ``skilllist|65000003|CACHE``，记录字段
    ``ability==21`` ∧ ``skillid==65000003``。只认该位置引用，**不读 children/sub_effect**
    （b9 §5.1 B1 同法：sub_effect 同号碰撞伪影不参与归属）；同号记录不跨层取值
    （载体层必须 CACHE；APK 同号不取）。
G5  原值逐值相等：``param1==0.25`` ∧ ``flag0_1==512``（不取近似、不做整数化比较）；
    bool 视为不合格。
G6  无既有答案：行 ``answers`` 为空才新增（B5 同法 ``not answers`` 守卫），不改旧值。
G7  零触碰：cid∈{30236,30239} 不进入（30236 为基线整卡，30239 同守）。
G8  规则可用：``rules.answer_for('skilllist',21,'/param1'|'/flag0_1', …)`` 均返回
    ``CONFIRMED_NUMERIC``，且规则 conditions 含「仅普通65000003」（声明样本域；本载体
    恰在域内）。规则键 ``skilllist|21|/param1``、``skilllist|21|/flag0_1`` 均**已存在**
    ——本模块不改 rules.json / rules.py。

答案（每行 2 条，逐行产出、不按同文/同值折叠）
---------------------------------------------
* ``/param1``＝回復输入 ``floor(伤害处理返回整数 × 0.25)``（比例；不承诺等于实际 HP 减少）。
* ``/flag0_1``＝上限 ``1.4 × 最大HP``（flag0_1=512→bit41；s_flagList 反序取首个已置位）。

证据分档：数值换算＝确认（既有规则，且载体在规则声明域内）；句面◆段↔
``skill_ids[2]`` 位置对应、引擎侧装载路径＝推断。行级标签「推断（模板批
クリティカル吸収）」；不升整行/整卡确认。

每行仍有「クリティカル攻撃机制（非暴击率/暴伤）」与「ダメージ（词表外）」两项无答案型
效果——本批 **0 行关闭**，不得把整行写成完整。

明确不处理（任务书 §5）：8 行「HPが回復する」无上限变体（skilllist APK）、
8424/8425「回復するドル」方言、20907 supporterskill 复合句（载体 CACHE 缺失）、
P1/P3 各池、Chain/第三套槽位/新原生/cost_statement。
"""
from __future__ import annotations

import json

import rules as R

MODULE_VERSION = 'crit_absorb_20261026'
SCOPE = 'CRIT_ABSORB_BATCH_20261026'
TAG = '推断（模板批 クリティカル吸収）'
FAMILY = 'クリティカル吸収（job_ability 第 3◆段→skill_ids[2]→skilllist ability21 StealHP）'

EXACT_SENTENCE = 'クリティカル攻撃時に与えたダメージ量に応じて、自身のHPが上限を超えて回復する。'
TABLE = 'job_ability'
LAYER = 'CACHE'
REF_FIELD = 'job_ability.cids contains cid'
FRAGMENT_INDEX = 2
SEGMENT_INDEX = 2
SEGMENT_COUNT = 3

CARRIER_ID = 65000003
CARRIER_ABILITY = 21
CARRIER_LAYER = 'CACHE'
PARAM1 = 0.25
FLAG0_1 = 512
RULE_KEYS = ('skilllist|21|/param1', 'skilllist|21|/flag0_1')

ZERO_TOUCH_CIDS = frozenset({30236, 30239})
DIALECT_CIDS = frozenset({8424, 8425})
DIALECT_MARK = '回復するドル。'

# 本批准入行（cid），重筛实测；apply_to_groups 只写这些行，范围外零变化。
ADMITTED_CIDS = frozenset({
    351, 352, 353, 354, 2329, 2330, 3228, 3237, 4313, 4315, 6269, 6339, 6341, 6343,
    7611, 7612, 7687, 9242, 11234, 13226, 13229, 20237, 20333, 20838, 30001, 30002,
    30101, 30108, 30110, 30201, 30206, 30228, 30229, 30237, 30240, 30243, 30244,
    30249, 30252, 30256, 30263, 30305, 30306, 30307, 30320, 30321, 30324, 30325,
    30326, 30329, 30332, 30333, 30336,
})

EVIDENCE_RATIO = ('lifesteal/README.md', 'lifesteal/trace.json', 'lifesteal/native_checks.json',
                  'difference_sources/README.md', 'difference_sources/trace.json',
                  'difference_sources/reference_observations.json',
                  'difference_sources/adoption_policy.json')
EVIDENCE_CAP = ('lifesteal/README.md', 'lifesteal/trace.json', 'lifesteal/native_checks.json')


def _norm(text: str) -> str:
    import unicodedata
    return unicodedata.normalize('NFKC', str(text or ''))


def segments(text: str):
    """◆ 分段（去空段；保留原文，不做标点归一）。"""
    return [s.strip(' \r\t\n') for s in str(text or '').replace('\\n', '\n').split('◆') if s.strip(' \r\t\n')]


def _ref(entry: dict, index: int):
    for r in (entry or {}).get('skill_refs') or []:
        if r.get('reference_field') == f'{TABLE}.skill_ids[{index}]':
            return r
    return None


def _carrier_gates(entry):
    ref = _ref(entry, SEGMENT_INDEX)
    rec = (ref or {}).get('record') or {}
    g = {
        'G4a_skill_ids_2_present': bool(ref and ref.get('resolved')
                                        and ref.get('table') == 'skilllist'),
        'G4b_carrier_identity': bool(ref and ref.get('reference_id') == CARRIER_ID
                                     and ref.get('layer') == CARRIER_LAYER
                                     and rec.get('skillid') == CARRIER_ID),
        'G4c_carrier_ability21': rec.get('ability') == CARRIER_ABILITY,
        'G5a_param1_0_25': (not isinstance(rec.get('param1'), bool)) and rec.get('param1') == PARAM1,
        'G5b_flag0_1_512': (not isinstance(rec.get('flag0_1'), bool)) and rec.get('flag0_1') == FLAG0_1,
    }
    return g, ref, rec


def _rules_ok(rec):
    out = {}
    for key in RULE_KEYS:
        field = key.split('|')[-1]
        ans = R.answer_for('skilllist', CARRIER_ABILITY, field, rec.get(field[1:]), rec,
                           source_layer=CARRIER_LAYER)
        rule = R.rule_for('skilllist', CARRIER_ABILITY, field)
        out[key] = bool(
            ans and ans.get('answer_status') == 'CONFIRMED_NUMERIC'
            and '已确认' in str((rule or {}).get('status') or '')
            and '65000003' in str((rule or {}).get('applicability')
                                  or (rule or {}).get('conditions') or ''))
    return out


REJECT_ORDER = ('ZERO_TOUCH_CID', 'DIALECT_VARIANT', 'NOT_JOB_ABILITY_CACHE_REF',
                'SENTENCE_MISMATCH', 'SEGMENT_ORDER_MISMATCH', 'NO_SKILL_IDS_2',
                'CARRIER_MISMATCH', 'PARAM_MISMATCH', 'ALREADY_ANSWERED',
                'RULE_UNAVAILABLE')


def evaluate(cid, layer, reference_field, record, row, entry):
    """对一行做本批门控。返回 dict(status=ACCEPT|REJECT, reject, gates, answers, carrier)。

    ``entry``：link 层本行所属 job_ability 记录（含 ``skill_refs``）；
    ``record``：该 job_ability 记录本身；``row``：页面行（含 japanese/fragment_index/answers）。
    """
    record = record or {}
    row = row or {}
    frag = str(row.get('japanese') or '')
    segs = segments(record.get('text'))
    gates = {}
    # 零触碰与方言先行（原因码稳定）
    if cid in ZERO_TOUCH_CIDS:
        return dict(status='REJECT', reject='ZERO_TOUCH_CID',
                    gates={'G7_not_zero_touch': False}, answers=[], carrier=None)
    if cid in DIALECT_CIDS or (DIALECT_MARK in frag and frag != EXACT_SENTENCE):
        return dict(status='REJECT', reject='DIALECT_VARIANT',
                    gates={'G2_sentence_verbatim': False}, answers=[], carrier=None)
    if not (layer == LAYER and reference_field == REF_FIELD):
        return dict(status='REJECT', reject='NOT_JOB_ABILITY_CACHE_REF',
                    gates={'G1_table_layer_ref': False}, answers=[], carrier=None)
    gates['G1_table_layer_ref'] = True
    gates['G2_sentence_verbatim'] = (frag == EXACT_SENTENCE
                                     and _norm(frag) == _norm(EXACT_SENTENCE))
    if not gates['G2_sentence_verbatim']:
        return dict(status='REJECT', reject='SENTENCE_MISMATCH', gates=gates,
                    answers=[], carrier=None)
    gates['G3_segment_order'] = (len(segs) == SEGMENT_COUNT
                                 and segs[SEGMENT_INDEX] == EXACT_SENTENCE
                                 and row.get('fragment_index') == FRAGMENT_INDEX)
    if not gates['G3_segment_order']:
        return dict(status='REJECT', reject='SEGMENT_ORDER_MISMATCH', gates=gates,
                    answers=[], carrier=None)
    if not row.get('answers'):
        gates['G6_no_existing_answer'] = True
    else:
        return dict(status='REJECT', reject='ALREADY_ANSWERED',
                    gates={**gates, 'G6_no_existing_answer': False}, answers=[], carrier=None)
    cg, ref, rec = _carrier_gates(entry)
    gates.update(cg)
    if not cg['G4a_skill_ids_2_present']:
        return dict(status='REJECT', reject='NO_SKILL_IDS_2', gates=gates,
                    answers=[], carrier=None)
    if not (cg['G4b_carrier_identity'] and cg['G4c_carrier_ability21']):
        return dict(status='REJECT', reject='CARRIER_MISMATCH', gates=gates,
                    answers=[], carrier=None)
    if not (cg['G5a_param1_0_25'] and cg['G5b_flag0_1_512']):
        return dict(status='REJECT', reject='PARAM_MISMATCH', gates=gates, answers=[], carrier=None)
    rg = _rules_ok(rec)
    gates.update({'G8_rule_' + k.replace('|', '_').replace('/', '_'): v for k, v in rg.items()})
    if not all(rg.values()):
        return dict(status='REJECT', reject='RULE_UNAVAILABLE', gates=gates,
                    answers=[], carrier=rec)
    answers = build_answers(cid, row, rec, ref)
    return dict(status='ACCEPT', reject=None, gates=gates, answers=answers,
                carrier=rec, carrier_ref=ref)


def _carrier_source(rec, ref, field):
    """答案 source（B5 同法：table/record_id/layer/record_key 供 verify_full registry 解引用）。

    不复制原始二进制 original_file/work 指针（verify_full 只对 .json/.json.raw 采用
    original_file；指向 work/*.data5 的指针会解引用失败），也不写 field 键——字段由
    field_path 指认，registry 以 (skilllist, CACHE, skillid=65000003) 唯一定位记录。
    """
    return dict(table='skilllist', record_id=CARRIER_ID, layer=CARRIER_LAYER,
                namespace='skilllist', ability_type=CARRIER_ABILITY,
                field_path=field, raw_value=rec.get(field[1:]),
                record_key=f'skilllist|{CARRIER_ID}|{CARRIER_LAYER}|ability={CARRIER_ABILITY}',
                reference_field=f'{TABLE}.skill_ids[{SEGMENT_INDEX}]')


def _binding(row_id, field):
    return {'crit_absorb_binding': dict(
        scope=SCOPE, family='crit_absorb', row_id=row_id,
        table=TABLE, layer=LAYER, reference_field=REF_FIELD,
        fragment_index=FRAGMENT_INDEX, segment_index=SEGMENT_INDEX,
        carrier_table='skilllist', carrier_record_id=CARRIER_ID,
        carrier_layer=CARRIER_LAYER, carrier_ability=CARRIER_ABILITY,
        rule_key=f'skilllist|{CARRIER_ABILITY}|{field}',
        claim='回復（词表外）')}


_COMMON_CONDITION = ('暴击攻击时；仅普通65000003 /ability21 已核暴击回复分支'
                     '（本行载体 65000003 在规则声明样本域内）；进入回复路径且安装/资格满足时')


def build_answers(cid, row, rec, ref):
    row_id = row.get('row_id')
    out = []
    fields = (('/param1', '暴击回复比例', '比例（0~1）', EVIDENCE_RATIO,
               '回复量与伤害基数的关系（比例）：本条只给回复输入算式，不承诺最终 HP 结果'),
              ('/flag0_1', '暴击回复HP上限档位', '最大HP倍数', EVIDENCE_CAP,
               '回复上限：本条只给上限档位（1.4×最大HP），不承诺最终 HP 结果'))
    for field, kind, unit, evidence, limit_note in fields:
        key = f'skilllist|{CARRIER_ABILITY}|{field}'
        raw = rec.get(field[1:])
        converted = R.answer_for('skilllist', CARRIER_ABILITY, field, raw, rec,
                                 source_layer=CARRIER_LAYER) or {}
        rule = R.rule_for('skilllist', CARRIER_ABILITY, field) or {}
        out.append(dict(
            value=converted.get('value_text'),
            quantity_kind=kind, unit=converted.get('unit') or unit,
            raw_value=raw, field_path=field,
            numeric_source='规则',
            numeric_evidence='确认', association_evidence='推断',
            evidence_scope=SCOPE,
            rule_key=key,
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=converted.get('conversion') or rule.get('conversion'),
            base_definition=converted.get('base_definition'),
            conditions=_COMMON_CONDITION,
            rule_limits=rule.get('limits'),
            target=rule.get('target'),
            evidence=list(evidence),
            source=_carrier_source(rec, ref, field),
            table='skilllist', record_id=CARRIER_ID, layer=CARRIER_LAYER,
            binding=_binding(row_id, field),
            note=('クリティカル吸収批值行：载体 skilllist|65000003|CACHE（ability21 StealHP）；'
                  f'第 3◆段↔skill_ids[{SEGMENT_INDEX}] 位置序；规则键 {key}（已确认，'
                  'conditions 明写「仅普通65000003」，本载体在域内）；数值换算＝确认、'
                  '句面↔段位/链位置关联＝推断；' + limit_note +
                  '；同号记录不跨层取值（只取 skilllist CACHE），sub_effect 同号碰撞伪影不参与归属；'
                  '本行另有「クリティカル攻撃机制」「ダメージ」两项效果无答案（0 行关闭）'),
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
    row['evidence_scope'] = list(dict.fromkeys(
        list(row.get('evidence_scope') or []) + [SCOPE]))
    marker = row.setdefault('inference_crit_absorb', dict(scope=SCOPE, claims=[]))
    marker['claims'].append(dict(family='crit_absorb', slot=answer['field_path'],
                                 record_id=CARRIER_ID, rule_key=answer['rule_key'],
                                 value=answer['raw_value']))
    return True


def _record_index(data, cid):
    index = {}
    for g in ((data.links.get(cid) or {}).get('groups') or []):
        for rec in g.get('records') or []:
            index[(rec.get('table'), rec.get('reference_field'))] = rec
    return index


def apply_to_groups(data, cid, groups):
    """正式页消费：为クリティカル吸収行绑定两条来源限定答案（不覆盖/不删除既有答案）。"""
    report = dict(scope=SCOPE, cid=cid, answers_added=0, additions=[], rejections=[],
                  skipped_existing=0, evaluated=0)
    if cid in ZERO_TOUCH_CIDS:
        report['zero_touch'] = True
        report['rejections'].append(dict(reason='ZERO_TOUCH_CID', cid=cid))
        return report
    if cid not in ADMITTED_CIDS:
        return report
    index = _record_index(data, cid)
    for group in groups:
        for skill in group.get('skills', []):
            table = skill.get('table')
            if table != TABLE:
                continue
            ref = skill.get('reference_field')
            entry = index.get((table, ref))
            if entry is None:
                continue
            record = entry.get('record') or {}
            for row in skill.get('rows', []):
                if str(row.get('japanese') or '') not in (EXACT_SENTENCE,):
                    continue
                report['evaluated'] += 1
                res = evaluate(cid, skill.get('layer'), ref, record, row, entry)
                if res['status'] != 'ACCEPT':
                    if res['reject'] == 'ALREADY_ANSWERED':
                        report['skipped_existing'] += 1
                    else:
                        report['rejections'].append(dict(row_id=row.get('row_id'),
                                                         reason=res['reject']))
                    continue
                added = 0
                for ans in res['answers']:
                    if _append(row, ans):
                        added += 1
                        report['additions'].append(dict(row_id=row.get('row_id'),
                                                        slot=ans['field_path'],
                                                        rule_key=ans['rule_key'],
                                                        value=ans['raw_value']))
                report['answers_added'] += added
                row.setdefault('crit_absorb_gate', dict(res['gates']))
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='クリティカル吸収批：句式/门控只读探针')
    ap.add_argument('--text', help='单句测试')
    args = ap.parse_args(argv)
    if args.text:
        frag = args.text
        print(json.dumps(dict(
            exact=frag == EXACT_SENTENCE,
            nfkc_equal=_norm(frag) == _norm(EXACT_SENTENCE),
            dialect=DIALECT_MARK in frag,
            segments=segments(frag)), ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == '__main__':
    raise SystemExit(_main())
