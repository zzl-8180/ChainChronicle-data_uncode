# -*- coding: utf-8 -*-
"""C9-B1 t99 敵デバフ余量（4 行 / 16 值行，全 Y.G.）：**冻结 4 行准入 + 复用既有 b9.evaluate**。

任务卡 ``docs/tasks/20261030-c9-p1-throughput-package.md``；预检
``output/character_skills/c9_p1_20261030/precheck/``（``precheck_report.md`` §3.3、
``batch_plan.json`` 的 ``primary``、``boundary_cases.json``）。

为什么是这 4 行
---------------
这 4 行（30101 f2 / 30302 f4 / 30305 f3 / 30333 f5）本来就是批 9（
``card_page_inference_b9_debuff``）的同形行：句面固定为「…攻撃した敵の攻撃力と防御力と
移動速度が一定時間下がる」，行记录是 skilllist 能力容器，own ``sub_effect`` 链上恰 1 条
ability99（SA_PowerDrain）载体。它们**不是**语义被否决，而是被页面构建的
``card_page_data.py`` 里 ``table in B9.TABLES and not answers`` 守卫挡住的——每行已有一条
原文数字答案（``クリティカル攻撃が5回`` 的「5」），``answers`` 非空 → b9 从未被调用。
预检用既有 live gate（``B9.evaluate`` 单函数）实跑这 4 行，**4/4 返回 promote**，
载体分别 43010103 / 43030204 / 43030504 / 43033303，p7=-0.3、p9=+0.3、p8=-0.3、p0=30。

为什么必须冻结准入
------------------
**本模块不改 ``not answers`` 守卫、不全局放宽 b9 调用条件。** 放宽会让全库最多另有 37 个
非 Y.G. A 行同形命中（未逐行跑 gate）。本模块只对冻结的 4 个 ``row_id`` 生效，逐行重新
调用 ``B9.evaluate`` 并要求 promote；任何输入漂移（句面/容器记录/载体/参数/原值）在
``evaluate`` 内拒绝，不静默重绑。非 Y.G. 连带 0。

口径（与批 9 已交付的 11 个同句 Y.G. 兄弟行完全一致）
---------------------------------------------------
* 值行直接复用 ``B9.evaluate`` 返回的答案对象（rule_key / note / 证据 scope
  ``TEMPLATE_BATCH9_DEBUFF`` / evidence 路径全部由批 9 生成，本模块**不重写**）。
* p9 表述：「受伤量倍率 +0.3（受伤量因子 1.3；不是固定防御减少 30%）」——正面值是
  受伤量倍率的表现层，**不写成固定防御 −30%**。批 9 note 已逐字如此，本模块不新增
  另一种写法。
* p8 限制保留：``skilllist|99|/param8`` 已核样本域只有 43023616 单条（occ=1），其余为
  存在数口径；本行载体为规则适用域内外推，批 9 note 逐行披露，本模块原样保留。
* 规则本体已确认（``profiles/rules.json`` 四键），本条数值归属＝推断；不升「确认」。
* 账本沿用 ``effect_ledger._RULE_KEY_EFFECT`` 的 4 个既有全局映射
  （``skilllist|99|/param7|/param8|/param9|/param0``）与 ``_RULE_KEY_DIRECTION`` 的 p9
  down 口径；**不改 rules.json／rules.py／effect_ledger.py，不新增映射。**

判据（逐行硬门，任一不符即拒绝，不猜）
------------------------------------
1. ``row_id`` 在冻结表内、cid 一致、``group == 'ability'``。
2. 行技能层：``table == 'skilllist'``、``layer == 'CACHE'``、容器 ``record_id`` 与
   ``reference_field`` 等于冻结值、``source_key == CACHE/skilllist.data5.json.raw``。
3. ``japanese`` 与冻结句面逐字（NFKC＋空白归一）相同。
4. 容器记录 ability 等于冻结值（1110），且冻结载体记录 ability == 99、p7/p8/p9/p0
   与冻结原值逐位相等（MISSING/NULL/NON_FINITE/ZERO 独立拒绝，不补零）。
5. 本行**必须**仍有至少一条原文数字答案（rule_key 为空的定量答案）——这是本批存在的
   前提（守卫来源）；该答案消失即拒绝（``ORIGINAL_NUMERIC_MISSING``），不静默写入。
6. 幂等/去重：本行已有同 rule_key 答案时——同记录同值 → ``ALREADY_PRESENT_SAME``；
   其余 → ``ALREADY_ANSWERED``（只披露，不新增、不改写）。
7. ``B9.evaluate`` 必须返回 ``kind == 'promote'``，且 carrier_record_id / carrier_layer /
   subject / attrs / claims / 4 条值行（rule_key + raw_value）与冻结值逐项相等。
8. 保护卡 30236／30239 零触碰。

证据分档（不得升格）
--------------------
规则键与「哪条 ability99 对应本句」都沿用批 9 的已确认口径；本模块只补「被守卫挡住的
4 行」。答案 ``numeric_evidence = 推断``、``association_evidence = 推断``、不写最终扣血、
不写实机时长与叠加/覆盖。
"""
from __future__ import annotations

import unicodedata

import card_page_inference_b9_debuff as B9

MODULE_VERSION = 'c9_p1_t99_debuff_gap_20261030'
#: 行级 marker scope（不新增账本映射；账本消费走既有 skilllist|99| 全局表）。
SCOPE = 'C9_P1_T99_DEBUFF_GAP_20261030'
MARKER_KEY = 'inference_c9_p1_t99'
RULE_KEYS = ('skilllist|99|/param7', 'skilllist|99|/param9',
             'skilllist|99|/param8', 'skilllist|99|/param0')
ATTRS = ('攻撃力', '防御力', '移動速度')
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

#: 冻结准入表（2026-10-30 由原始 CACHE 记录、当前正式页与既有 B9.evaluate 实跑独立重导
#: 一致后固化；任何漂移即拒绝，不静默重绑）。
_ADMITTED_LIST = [
    dict(cid=30101, group='ability',
         row_id='30101-ability-ability-skillid_1_-lvorder0-f2',
         container_record=43010100, container_ability=1110,
         reference_field='skillid[1]', carrier_record=43010103,
         subject='攻撃した敵',
         japanese='クリティカル攻撃時、クリティカル攻撃が5回になり、クリティカル威力が上がり、'
                  '範囲攻撃になり、範囲が広がり、範囲が前方に移動し、攻撃した敵の攻撃力と'
                  '防御力と移動速度が一定時間下がる。',
         params={'param7': -0.3, 'param8': -0.3, 'param9': 0.3, 'param0': 30}),
    dict(cid=30302, group='ability',
         row_id='30302-ability-ability-skillid_1_-lvorder0-f4',
         container_record=43030200, container_ability=1110,
         reference_field='skillid[1]', carrier_record=43030204,
         subject='攻撃した敵',
         japanese='またクリティカル攻撃時、クリティカル攻撃が5回になり、クリティカル威力が上がり、'
                  '範囲攻撃になり、攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         params={'param7': -0.3, 'param8': -0.3, 'param9': 0.3, 'param0': 30}),
    dict(cid=30305, group='ability',
         row_id='30305-ability-ability-skillid_1_-lvorder0-f3',
         container_record=43030500, container_ability=1110,
         reference_field='skillid[1]', carrier_record=43030504,
         subject='攻撃した敵',
         japanese='さらにクリティカル攻撃時、クリティカル攻撃が5回になり、クリティカル威力が上がり、'
                  '範囲攻撃になり、攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         params={'param7': -0.3, 'param8': -0.3, 'param9': 0.3, 'param0': 30}),
    dict(cid=30333, group='ability',
         row_id='30333-ability-ability-skillid_1_-lvorder0-f5',
         container_record=43033300, container_ability=1110,
         reference_field='skillid[1]', carrier_record=43033303,
         subject='攻撃した敵',
         japanese='さらに攻撃時、攻撃した敵の攻撃力と防御力と移動速度が一定時間下がり、'
                  'クリティカル攻撃時、クリティカル攻撃が5回になり、クリティカル威力が上がる。',
         params={'param7': -0.3, 'param8': -0.3, 'param9': 0.3, 'param0': 30}),
]
ADMITTED = {item['row_id']: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item['cid'] for item in _ADMITTED_LIST)

EVIDENCE = [
    'output/character_skills/c9_p1_20261030/precheck/precheck_report.md',
    'output/character_skills/c9_p1_20261030/precheck/batch_plan.json',
    'output/character_skills/c9_p1_20261030/precheck/boundary_cases.json',
    'output/character_skills/inference_inventory/b9_debuff_scope.md',
]
LIMIT = ('规则键与载体归属沿用批 9 已确认口径（规则本体已确认；本条数值归属＝推断）；'
         'p9 为受伤量倍率表现层（+0.3→受伤量因子 1.3），不是固定防御 −30%；p8 已核样本域'
         '仅 43023616 单条，本行载体为域内外推；不写最终扣血、不写实机时长/叠加/覆盖。')


def canon(text):
    return ''.join(unicodedata.normalize('NFKC', str(text or '')).split())


def raw_state(value, present=True):
    """缺失 / null / 非有限 / 负值 / 真零 / 有限分开标注（不把任何一档补成 0）。"""
    import math
    if not present:
        return 'MISSING'
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'NON_FINITE'
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 'NON_FINITE'
    if not math.isfinite(f):
        return 'NON_FINITE'
    if f < 0:
        return 'NEGATIVE'
    if f == 0:
        return 'ZERO'
    return 'FINITE'


def _original_numeric(row):
    return [a for a in row.get('answers') or []
            if a.get('rule_key') is None and a.get('quantitative')]


def evaluate(data, cid, row, skill, b9=None):
    """单行判定（不写入）。``skill`` 为页面 skill 节点；``b9`` 可注入替代评估器（只读测试）。"""
    if cid in ZERO_TOUCH_CIDS:
        return {'accepted': False, 'rejection': 'ZERO_TOUCH_CID'}
    rid = row.get('row_id')
    adm = ADMITTED.get(rid)
    if adm is None:
        return {'accepted': False, 'rejection': 'NOT_IN_BATCH_SCOPE'}
    if adm['cid'] != cid:
        return {'accepted': False, 'rejection': 'CID_MISMATCH'}
    if row.get('group') != adm['group']:
        return {'accepted': False, 'rejection': 'GROUP_MISMATCH'}
    gates = {'row_id': rid, 'cid': cid}
    if canon(row.get('japanese')) != canon(adm['japanese']):
        return {'accepted': False, 'rejection': 'ROW_TEXT_NOT_ADMITTED', 'gates': gates}
    if str(row.get('reference_field') or '') != adm['reference_field']:
        return {'accepted': False, 'rejection': 'REFERENCE_FIELD_DRIFT', 'gates': gates}
    if skill is None or skill.get('table') != 'skilllist':
        return {'accepted': False, 'rejection': 'ROW_NOT_SKILLLIST', 'gates': gates}
    src = skill.get('source') or {}
    gates['skill'] = {k: skill.get(k) for k in ('table', 'record_id', 'layer')}
    if (skill.get('layer') != 'CACHE' or skill.get('record_id') != adm['container_record']
            or src.get('source_key') != 'CACHE/skilllist.data5.json.raw'):
        return {'accepted': False, 'rejection': 'ROW_LAYER_OR_CONTAINER_MISMATCH', 'gates': gates}
    entry = data.skill(adm['container_record'])
    if entry is None or entry.get('resolved') is not True:
        return {'accepted': False, 'rejection': 'CONTAINER_RECORD_MISSING', 'gates': gates}
    record = entry.get('record') or {}
    gates['container_ability'] = record.get('ability')
    if record.get('ability') != adm['container_ability']:
        return {'accepted': False, 'rejection': 'CONTAINER_ABILITY_DRIFT',
                'detail': {'expected': adm['container_ability'],
                           'actual': record.get('ability')}, 'gates': gates}
    hit = data.cache_skill.get(adm['carrier_record'])
    if hit is None:
        return {'accepted': False, 'rejection': 'CARRIER_RECORD_MISSING', 'gates': gates}
    carrier = hit[1] or {}
    gates['carrier_ability'] = carrier.get('ability')
    if carrier.get('ability') != 99:
        return {'accepted': False, 'rejection': 'CARRIER_NOT_ABILITY_99',
                'detail': {'carrier': adm['carrier_record'],
                           'ability': carrier.get('ability')}, 'gates': gates}
    states = {f: raw_state(carrier.get(f), present=f in carrier)
              for f in ('param7', 'param8', 'param9', 'param0')}
    if carrier.get('param0') == -1:
        # 哨兵：-1＝无正计时标记（不是 -1 秒/永久）；与缺失/真零分开标注，一律不补零。
        states['param0'] = 'SENTINEL'
    gates['carrier_params'] = {f: carrier.get(f) for f in states}
    gates['carrier_param_states'] = states
    # p7/p8 的负值是本规则的方向语义（加算下降），不是异常；缺失/null/非有限/真零各自独立
    # 拒绝（不补零），随后再与原值逐位比对（MISSING/NULL/NON_FINITE/ZERO 不会被当作数值）。
    if any(s in ('MISSING', 'NULL', 'NON_FINITE', 'ZERO', 'SENTINEL') for s in states.values()):
        return {'accepted': False, 'rejection': 'CARRIER_PARAM_STATE',
                'detail': states, 'gates': gates}
    if {f: float(carrier.get(f)) for f in states} != {f: float(v) for f, v in adm['params'].items()}:
        return {'accepted': False, 'rejection': 'CARRIER_PARAM_DRIFT',
                'detail': {'expected': adm['params'], 'actual': gates['carrier_params']},
                'gates': gates}
    originals = _original_numeric(row)
    gates['preexisting_original_numeric'] = [a.get('value') for a in originals]
    if not originals:
        # 本批存在的唯一理由就是「已有原文数字答案 → 全局守卫跳过 b9」；答案消失说明输入
        # 已漂移，不得把本批当成通用放宽使用。
        return {'accepted': False, 'rejection': 'ORIGINAL_NUMERIC_MISSING', 'gates': gates}
    existing = [a for a in row.get('answers') or [] if a.get('rule_key') in RULE_KEYS]
    gates['existing_same_rule_keys'] = [
        {'rule_key': a.get('rule_key'), 'raw_value': a.get('raw_value'),
         'record_id': a.get('record_id')} for a in existing]
    if existing:
        same = (len(existing) == len(RULE_KEYS)
                and {a.get('rule_key') for a in existing} == set(RULE_KEYS)
                and all(a.get('record_id') in (None, adm['carrier_record'])
                        and a.get('raw_value') is not None
                        and float(a.get('raw_value')) == float(adm['params'][a['rule_key'].rsplit('/', 1)[-1]])
                        for a in existing))
        return {'accepted': False,
                'rejection': 'ALREADY_PRESENT_SAME' if same else 'ALREADY_ANSWERED',
                'detail': None if same else {'existing': gates['existing_same_rule_keys']},
                'gates': gates}
    if b9 is None:
        b9 = B9.evaluate
    res = b9(record, row.get('japanese'), table='skilllist', layer=entry.get('layer'),
             record_id=entry.get('reference_id'), text=record.get('text'),
             data=data, cid=cid)
    if not isinstance(res, dict):
        return {'accepted': False, 'rejection': 'B9_RETURNED_NONE', 'gates': gates}
    gates['b9_kind'] = res.get('kind')
    if res.get('kind') != 'promote':
        return {'accepted': False, 'rejection': 'B9_NOT_PROMOTED',
                'detail': res.get('reasons'), 'gates': gates}
    gates['b9_carrier'] = [res.get('carrier_record_id'), res.get('carrier_layer')]
    if (res.get('carrier_record_id') != adm['carrier_record']
            or res.get('carrier_layer') != 'CACHE'):
        return {'accepted': False, 'rejection': 'B9_CARRIER_DRIFT',
                'detail': gates['b9_carrier'], 'gates': gates}
    if res.get('subject') != adm['subject'] or list(res.get('attrs') or []) != list(ATTRS):
        return {'accepted': False, 'rejection': 'B9_SUBJECT_OR_ATTRS_DRIFT',
                'detail': {'subject': res.get('subject'), 'attrs': res.get('attrs')},
                'gates': gates}
    got = [{'rule_key': a.get('rule_key'), 'raw_value': a.get('raw_value'),
            'field_path': a.get('field_path'), 'record_id': a.get('record_id')}
           for a in res.get('answers') or []]
    gates['b9_value_rows'] = got
    want = [{'rule_key': k, 'raw_value': adm['params'][k.rsplit('/', 1)[-1]],
             'field_path': '/' + k.rsplit('/', 1)[-1], 'record_id': None}
            for k in RULE_KEYS]
    if len(got) != 4 or [g['rule_key'] for g in got] != [w['rule_key'] for w in want] \
            or any(float(g['raw_value']) != float(w['raw_value']) or g['field_path'] != w['field_path']
                   for g, w in zip(got, want)):
        return {'accepted': False, 'rejection': 'B9_VALUE_ROWS_DRIFT',
                'detail': {'expected': want, 'actual': got}, 'gates': gates}
    return {'accepted': True, 'rejection': None, 'gates': gates, 'b9': res,
            'detail': None}


def _merge_reasons(row, res, originals):
    """晋级行未知原因：批 9 summary＋extra_reasons，并显式保留原文数字未归属的披露。"""
    reasons = [res['summary_reason']]
    reasons += list(res.get('extra_reasons') or [])
    if originals:
        reasons.append('本行既有原文数字答案（%s）保持不变，其字段关联仍未知；本批只补'
                       ' skilllist|99| 值行，不改写原文数字答案。'
                       % '、'.join(str(a.get('value')) for a in originals))
    row['unknown_reasons'] = list(dict.fromkeys(reasons))


def _append(row, answers):
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    existing = {key(a) for a in row.get('answers') or []}
    added = []
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault('answers', []).append(answer)
        existing.add(key(answer))
        added.append(answer)
    return added


def _row_provenance(row, adm, res, gts):
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = B9.B9_TAG
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    row['partial'] = True
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = sorted(set(scopes) | {'TEMPLATE_BATCH9_DEBUFF'})
    row['inference_b9'] = dict(
        batch='20261021 批9', family=B9.B9_FAMILY,
        table='skilllist', record_id=adm['container_record'], layer='CACHE',
        carrier_record_id=res['carrier_record_id'], carrier_layer=res['carrier_layer'],
        carrier_name=res.get('carrier_name'), via=res['via'], subject=res['subject'],
        attrs=res['attrs'], claims=res['claims'], sent_no=res['sent_no'],
        sent_total=res['sent_total'])
    row[MARKER_KEY] = dict(
        scope=SCOPE, module=MODULE_VERSION, batch='C9-B1',
        row_id=adm['row_id'], cid=adm['cid'],
        admission='FROZEN_4_ROW_TABLE_REUSING_EXISTING_B9_GATE',
        global_guard='card_page_data.py 的 `not answers` b9 调用守卫未改动（未全局放宽）',
        container=dict(table='skilllist', record_id=adm['container_record'], layer='CACHE',
                       ability=adm['container_ability'], reference_field=adm['reference_field']),
        carrier=dict(record_id=res['carrier_record_id'], layer=res['carrier_layer'],
                     ability=99, params=adm['params']),
        subject=res['subject'], attrs=res['attrs'], claims=res['claims'],
        sent_no=res['sent_no'], sent_total=res['sent_total'],
        preexisting_original_numeric=gts.get('preexisting_original_numeric'),
        non_yg_collateral='0（冻结准入；未放宽全局守卫）',
        limits=LIMIT)


# ---------------------------------------------------------------- 正式页消费

def apply_to_groups(data, cid, groups):
    """正式页消费：为冻结 4 行补 b9 值行（不改写既有原文数字答案，不放宽全局守卫）。"""
    report = {'scope': SCOPE, 'cid': cid, 'evaluated': 0, 'answers_added': 0,
              'additions': [], 'markers': [], 'rejections': [],
              'skipped_existing': 0, 'marker_only': 0, 'out_of_scope': True}
    if cid not in ADMITTED_CIDS:
        return report
    report['out_of_scope'] = False
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append({'reason': 'ZERO_TOUCH_CID', 'cid': cid})
        return report
    index = {}
    for g in groups or []:
        for s in g.get('skills') or []:
            for r in s.get('rows') or []:
                index[r.get('row_id')] = (s, r)
    for rid, adm in sorted(ADMITTED.items(), key=lambda kv: kv[0]):
        if adm['cid'] != cid:
            continue
        pair = index.get(rid)
        if pair is None:
            report['rejections'].append({'row_id': rid, 'reason': 'ROW_NOT_FOUND'})
            continue
        skill, row = pair
        report['evaluated'] += 1
        res = evaluate(data, cid, row, skill)
        if not res['accepted']:
            if res['rejection'] == 'ALREADY_ANSWERED':
                disclosure = dict(
                    scope=SCOPE, module=MODULE_VERSION, batch='C9-B1', row_id=rid, cid=cid,
                    admission='FROZEN_4_ROW_TABLE_REUSING_EXISTING_B9_GATE',
                    dedup=res['rejection'], existing=res['gates'].get('existing_same_rule_keys'),
                    disclosure='本行已有同 rule_key 答案；不新增、不改写，只披露。')
                marker = row.get(MARKER_KEY)
                if marker != disclosure:
                    row[MARKER_KEY] = disclosure
                    report['marker_only'] += 1
                    report['markers'].append({'row_id': rid, 'dedup': res['rejection']})
            elif res['rejection'] == 'ALREADY_PRESENT_SAME':
                # 同记录同值：幂等跳过，**零写入**（不重写 marker，重复应用页 JSON 不变）。
                report['skipped_existing'] += 1
                report['markers'].append({'row_id': rid, 'dedup': 'ALREADY_PRESENT_SAME'})
            else:
                report['rejections'].append({'row_id': rid, 'reason': res['rejection'],
                                             'detail': res.get('detail')})
            continue
        b9 = res['b9']
        added = _append(row, b9['answers'])
        if not added:
            report['skipped_existing'] += 1
            continue
        _merge_reasons(row, b9, _original_numeric(row))
        _row_provenance(row, adm, b9, res['gates'])
        report['answers_added'] += len(added)
        for a in added:
            report['additions'].append({'row_id': rid, 'rule_key': a.get('rule_key'),
                                        'field_path': a.get('field_path'),
                                        'raw_value': a.get('raw_value')})
    return report


if __name__ == '__main__':
    raise SystemExit('只读探针请用 scratch 用例；本模块不提供写入口')
