# -*- coding: utf-8 -*-
"""C8-B2 t27 周期回复（15 行 / 15 效果，全 Y.G.）：来源限定窄映射的唯一生产者。

任务卡 ``docs/tasks/20261030-c8-p1-throughput-package.md``；预检
``output/character_skills/c8_p1_20261030/precheck/``（``precheck_report.md`` §2.5、
``batch_plan.json`` 的 ``host_ruling_required[1]``、``evidence_boundaries.md``）。

为什么是这 15 行
----------------
句面固定为 HP 回复句（不是状态异常解除句）：

* ``【共鳴必殺/連撃】/【超共鳴必殺/連撃】/【連撃】味方全体のHPを一定時間、一定間隔ごとに
  上限を超えて小回復する。``
* ``その後、味方全体のHPを…小回復する。``
* ``また/さらに味方全体のHPを…小回復し、同時に全状態異常も回復する。``

每行在**本行自己的执行链**（``special_move`` 的 ``patternN`` 或 ``denju.patternid0``）里
**恰有一条 type27**，参数 p1（单次回复量系数）/p2（回复间隔输入，游戏秒）/p3（回复次数）
与冻结值逐位相等；句面在 pattern 正文里只出现一次、且正文含「一定間隔ごとに上限を超えて」
恰一次，因此「本行句 ↔ 链内唯一 t27」不是按句子顺序猜的。

同卡 **0 披露**：这批行在本批之前没有任何同卡同键答案可用于交叉核（全库 pages 0 条答案
使用 27 键，本批实测）。因此本模块的准入靠「规则已确认（``output/boss_heal/field_dictionary.json``）
＋链内载体唯一＋句面机制名唯一」，**答案的关联仍标推断**，不写最终 HP、不写实机间隔。

账本侧
------
``effect_ledger`` 原本没有 27 键映射，句面主张是既有词表的「回復（词表外）」。本批经主持
裁决只增加**一条来源限定窄映射**（``effect_ledger.C8P1_T27_SCOPE``）：只消费本模块写入、
带 ``binding.c8_p1_t27_binding``（scope＝``C8_P1_T27_HEAL_20261030``）且 rule_key/槽/载体
记录/层逐项一致的答案；**不整族映射 type27**（p2/p3、``skillflag0_1`` 不映射），无标记行
（含全部旧页与其他族）映射行为零变化。JSON 的 ``rules.json`` 已含 27 p1/p2/p3 三键
（294 键内），本批**不新增规则键、不改 rules.json／rules.py**。

为什么用冻结准入表
----------------
同一句面在全库还有 58 条非 Y.G. CACHE 行与 6 条同卡 ``skilltext`` 行（跨多档、无单一链，
见 ``evidence_boundaries.md`` §2）。冻结准入表 + 链形状/参数漂移门保证：只写这 15 行、
非 Y.G. 连带 0 行、``skilltext`` 行不入。任何输入漂移（pattern id／链序列／参数值）即拒绝，
不静默重绑。

判据（逐行硬门，任一不符即拒绝，不猜）
------------------------------------
1. ``row_id`` 在冻结准入表内、cid 一致；``japanese`` 与冻结句面逐字相同。
2. 行 ``source.layer == CACHE``；``special_move`` 行 ``source_key == CACHE/bossinfo.data5.json.raw``
   且 ``reference_field`` 为 ``pattern0/1/2``；``denju`` 行 ``source_key ==
   CACHE/denju.data5.json.raw`` 且 ``reference_field`` 以 ``denju.`` 开头。
3. 链可达且唯一：``charainfo.patternN`` 或 ``denju.patternid0`` 在该层 ``bosspattern``
   唯一命中；槽位从 0 连续、子记录 ``skillid`` 在本层 ``bossskill`` 唯一命中；
   链 id 序列与类型序列等于冻结值。
4. 载体唯一：链内 type27 **恰 1 条**，其 ``skillid`` 等于冻结记录；p1/p2/p3 逐位等于冻结值，
   且各自 FINITE>0（缺失/null/非有限/负值/真零独立拒绝，不补零）。
5. 句面唯一：pattern 正文含本行句身恰 1 次，且含「一定間隔ごとに上限を超えて」恰 1 次。
6. 同卡披露状态：记录本卡在本批之前已有的 27 键答案（用于披露与去重，**不作准入**）。
7. 幂等与去重：本行已有同 rule_key 答案时——同记录同值 → 幂等跳过（零写入）；
   同值异记录 → 只写行级披露；同键异值 → 不新增、不改写，只披露。
8. 保护卡 30236／30239 零触碰。

证据分档（不得升格）
--------------------
p1/p2/p3 的语义是 ``rules.json`` 已确认的静态规则（origin ``output/boss_heal/field_dictionary.json``）；
「哪一条 t27 对应本行句面」是结构/唯一性证据；「味方全体」对象只来自句面（``rules.target``
为空）。故 ``association_evidence = 推断``、``numeric_evidence = 确认``（原值＋已确认规则键），
不写最终 HP 回复、不写实机间隔/次数，不做实机验证。
"""
from __future__ import annotations

import json
import math
import re
import struct
import unicodedata
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path

MODULE_VERSION = 'c8_p1_t27_periodic_heal_20261030'
#: 账本消费用 scope：effect_ledger.C8P1_T27_SCOPE（来源限定窄映射，唯一消费标记）。
SCOPE = 'C8_P1_T27_HEAL_20261030'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'
RULE_KEY = 'bossskill|27|/skillparam1'
HEAL_FIELD = 'skillparam1'
LIMIT_FIELD = 'skillparam2'
COUNT_FIELD = 'skillparam3'
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

#: 行级 marker 键（不覆盖其他批次键）。
MARKER_KEY = 'inference_c8_p1_t27'
HEAL_MECH_RX = re.compile(r'一定間隔ごとに上限を超えて')

_STALE_REASONS = {
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应',
}

S1 = '味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。'
S1_BASE = '【共鳴必殺/連撃】' + S1
S1_SUPER = '【超共鳴必殺/連撃】' + S1
S1_DENJU = '【連撃】' + S1
S2 = 'その後、味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。'
S3 = 'また味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復し、同時に全状態異常も回復する。'
S4 = 'さらに味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復し、同時に全状態異常も回復する。'

#: 冻结准入表（2026-10-30 由原始 CACHE 记录与当前正式页独立重导一致后固化；
#: 输入漂移即拒绝，不静默重绑）。
_ADMITTED_LIST = [
    dict(cid=353, group='special_move', ref='pattern0',
         row_id='353-special_move-special_move-pattern0-lvorder0-f3',
         pattern_id=40035300, chain_ids=[40035300, 40035301, 40035302, 40035303],
         chain_types=[110, 3, 13, 27], record_id=40035303,
         params={HEAL_FIELD: 1.25, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S3),
    dict(cid=353, group='special_move', ref='pattern2',
         row_id='353-special_move-special_move-pattern2-lvorder2-f3',
         pattern_id=40035302, chain_ids=[40035308, 40035309, 40035310, 40035311],
         chain_types=[110, 3, 13, 27], record_id=40035311,
         params={HEAL_FIELD: 2, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S3),
    dict(cid=10215, group='special_move', ref='pattern0',
         row_id='10215-special_move-special_move-pattern0-lvorder0-f0',
         pattern_id=41021500, chain_ids=[41021500, 41021501, 41021502],
         chain_types=[27, 13, 116], record_id=41021500,
         params={HEAL_FIELD: 1.25, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S1_BASE),
    dict(cid=10215, group='special_move', ref='pattern2',
         row_id='10215-special_move-special_move-pattern2-lvorder2-f0',
         pattern_id=41021502, chain_ids=[41021506, 41021507, 41021508],
         chain_types=[27, 13, 116], record_id=41021506,
         params={HEAL_FIELD: 2, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S1_SUPER),
    dict(cid=10215, group='denju', ref='denju.denju_id == cid',
         row_id='10215-denju-denju-denju_denju_id____cid-lvorder0-f0',
         pattern_id=41021503, chain_ids=[41021500, 41021501, 41021502],
         chain_types=[27, 13, 116], record_id=41021500,
         params={HEAL_FIELD: 1.25, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S1_DENJU),
    dict(cid=30104, group='special_move', ref='pattern0',
         row_id='30104-special_move-special_move-pattern0-lvorder0-f2',
         pattern_id=43010400, chain_ids=[43010400, 43010401, 43010402, 43010403],
         chain_types=[51, 27, 13, 16], record_id=43010401,
         params={HEAL_FIELD: 1.5, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S2),
    dict(cid=30104, group='special_move', ref='pattern1',
         row_id='30104-special_move-special_move-pattern1-lvorder1-f3',
         pattern_id=43010401, chain_ids=[43010404, 43010405, 43010406, 43010407],
         chain_types=[51, 27, 13, 16], record_id=43010405,
         params={HEAL_FIELD: 1.75, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S2),
    dict(cid=30104, group='denju', ref='denju.denju_id == cid',
         row_id='30104-denju-denju-denju_denju_id____cid-lvorder0-f2',
         pattern_id=43010402, chain_ids=[43010400, 43010401, 43010402, 43010403],
         chain_types=[51, 27, 13, 16], record_id=43010401,
         params={HEAL_FIELD: 1.5, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S2),
    dict(cid=30228, group='special_move', ref='pattern0',
         row_id='30228-special_move-special_move-pattern0-lvorder0-f0',
         pattern_id=43022800, chain_ids=[43022800, 43022801, 43022802],
         chain_types=[27, 13, 116], record_id=43022800,
         params={HEAL_FIELD: 1.25, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S1_BASE),
    dict(cid=30228, group='special_move', ref='pattern1',
         row_id='30228-special_move-special_move-pattern1-lvorder1-f0',
         pattern_id=43022801, chain_ids=[43022803, 43022804, 43022805],
         chain_types=[27, 13, 116], record_id=43022803,
         params={HEAL_FIELD: 1.5, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S1_SUPER),
    dict(cid=30257, group='special_move', ref='pattern1',
         row_id='30257-special_move-special_move-pattern1-lvorder1-f3',
         pattern_id=43025701, chain_ids=[43025700, 43025701, 43025702],
         chain_types=[55, 13, 27], record_id=43025702,
         params={HEAL_FIELD: 1.25, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S4),
    dict(cid=30257, group='special_move', ref='pattern2',
         row_id='30257-special_move-special_move-pattern2-lvorder2-f3',
         pattern_id=43025702, chain_ids=[43025706, 43025707, 43025708],
         chain_types=[55, 13, 27], record_id=43025708,
         params={HEAL_FIELD: 2, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S4),
    dict(cid=30314, group='special_move', ref='pattern0',
         row_id='30314-special_move-special_move-pattern0-lvorder0-f0',
         pattern_id=43031400, chain_ids=[43031400, 43031401, 43031402],
         chain_types=[27, 13, 116], record_id=43031400,
         params={HEAL_FIELD: 1.75, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S1_BASE),
    dict(cid=30314, group='special_move', ref='pattern1',
         row_id='30314-special_move-special_move-pattern1-lvorder1-f0',
         pattern_id=43031401, chain_ids=[43031403, 43031404, 43031405],
         chain_types=[27, 13, 116], record_id=43031403,
         params={HEAL_FIELD: 2, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S1_SUPER),
    dict(cid=30314, group='denju', ref='denju.denju_id == cid',
         row_id='30314-denju-denju-denju_denju_id____cid-lvorder0-f0',
         pattern_id=43031402, chain_ids=[43031400, 43031401, 43031402],
         chain_types=[27, 13, 116], record_id=43031400,
         params={HEAL_FIELD: 1.75, LIMIT_FIELD: 2, COUNT_FIELD: 15}, japanese=S1_DENJU),
]
ADMITTED = {item['row_id']: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item['cid'] for item in _ADMITTED_LIST)

EVIDENCE = [
    'output/character_skills/c8_p1_20261030/precheck/precheck_report.md',
    'output/character_skills/c8_p1_20261030/precheck/batch_plan.json',
    'output/character_skills/c8_p1_20261030/precheck/evidence_boundaries.md',
    'output/boss_heal/field_dictionary.json',
]
LIMIT = ('单次回复量系数为已确认静态规则；「哪条 t27 对应本行句面」为结构/唯一性证据；'
         '对象只由句面「味方全体」给出（rules.target 为空，受疗对象选择未复查）；'
         '不写最终 HP 回复量、超上限保留比例、实际触发间隔与次数，不做实机验证。')

_TABLES = {}


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def tables(data):
    """CACHE 解码主表（按 root 缓存；只读）。"""
    root = Path(getattr(data, 'root', Path('.'))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = read_path(root / 'output/cache_full_20261015_v3/decoded', root=root)
        boss = _read(base / 'bossinfo.data5.json.raw')['bossinfo']
        patterns, skills = {}, {}
        for i, rec in enumerate(boss.get('bosspattern') or []):
            patterns.setdefault(rec.get('patternid'), []).append((i, rec))
        for i, rec in enumerate(boss.get('bossskill') or []):
            skills.setdefault(rec.get('skillid'), []).append((i, rec))
        chara = {rec['cid']: rec for rec in _read(base / 'charainfo.data5.json.raw')['charainfo']}
        denju = {rec['denju_id']: (i, rec)
                 for i, rec in enumerate(_read(base / 'denju.data5.json.raw')['denju'])}
        _TABLES[key] = dict(patterns=patterns, skills=skills, chara=chara, denju=denju,
                            skills_all=boss.get('bossskill') or [], root=root)
    return _TABLES[key]


def canon(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def _num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return ('%.6f' % f).rstrip('0').rstrip('.')


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def raw_state(raw, present=True):
    """缺失 / null / 非有限 / 负值 / 真零 / 有限分开标注（不把任何一档补成 0）。"""
    if not present:
        return 'MISSING'
    if raw is None:
        return 'NULL'
    if isinstance(raw, bool):
        return 'NON_FINITE'
    try:
        f = float(raw)
    except (TypeError, ValueError):
        return 'NON_FINITE'
    if not math.isfinite(f):
        return 'NON_FINITE'
    if f < 0:
        return 'NEGATIVE'
    if f == 0:
        return 'ZERO'
    return 'FINITE'


# ---------------------------------------------------------------- 链

def pattern_pointer(tab, cid, adm):
    """(pattern_id, pointer, owner) 或 (None, rejection)。"""
    if adm['group'] == 'denju':
        hit = tab['denju'].get(cid)
        if hit is None:
            return None, 'DENJU_RECORD_MISSING'
        pid = hit[1].get('patternid0')
        return (pid, 'denju.patternid0', hit[1]) if pid else (None, 'PATTERN_POINTER_MISSING')
    chara = tab['chara'].get(cid)
    if chara is None:
        return None, 'CHARAINFO_RECORD_MISSING'
    pid = chara.get(adm['ref'])
    return (pid, 'charainfo.' + adm['ref'], chara) if pid else (None, 'PATTERN_POINTER_MISSING')


def chain_of(tab, cid, adm):
    pid, pointer, owner = pattern_pointer(tab, cid, adm)
    if pid is None:
        return None, pointer
    hits = tab['patterns'].get(pid) or []
    if len(hits) != 1:
        return None, 'BOSSPATTERN_NOT_UNIQUE(%d)' % len(hits)
    _, pattern = hits[0]
    slots = [(slot, pattern.get('skillid%d' % slot)) for slot in range(7)
             if pattern.get('skillid%d' % slot)]
    if [s for s, _ in slots] != list(range(len(slots))):
        return None, 'SLOT_NOT_CONTIGUOUS'
    children = []
    for slot, sid in slots:
        sh = tab['skills'].get(sid) or []
        if len(sh) != 1:
            return None, 'SKILL_NOT_UNIQUE(%s)' % sid
        k_index, rec = sh[0]
        children.append(dict(slot='skillid%d' % slot, skillid=sid, index=k_index,
                             type=rec.get('skillid0'), record=rec,
                             params={k: v for k, v in rec.items()
                                     if k.startswith('skillparam')}))
    return dict(pattern_id=pid, pattern=pattern, pattern_pointer=pointer,
                owner=owner, children=children, layer='CACHE'), None


# ---------------------------------------------------------------- 单行判定

def evaluate(data, cid, row, rows=None, tab=None):
    """单行判定（不写入）。``rows`` 为同卡全部行（同卡 27 键答案披露/去重）。"""
    rid = row.get('row_id')
    if cid in ZERO_TOUCH_CIDS:
        return {'accepted': False, 'rejection': 'ZERO_TOUCH_CID'}
    adm = ADMITTED.get(rid)
    if adm is None:
        return {'accepted': False, 'rejection': 'NOT_IN_BATCH_SCOPE'}
    if adm['cid'] != cid:
        return {'accepted': False, 'rejection': 'CID_MISMATCH'}
    tab = tab or tables(data)
    gates = {'row_id': rid, 'cid': cid}
    # 1 行身份
    if canon(row.get('japanese')) != canon(adm['japanese']):
        return {'accepted': False, 'rejection': 'ROW_TEXT_NOT_ADMITTED', 'gates': gates}
    if str(row.get('reference_field') or '') != adm['ref']:
        return {'accepted': False, 'rejection': 'REFERENCE_FIELD_DRIFT', 'gates': gates}
    # 2 同层
    src = row.get('source') or {}
    want_key = ('CACHE/denju.data5.json.raw' if adm['group'] == 'denju'
                else 'CACHE/bossinfo.data5.json.raw')
    gates['row_source'] = {k: src.get(k) for k in
                           ('record_key', 'source_key', 'layer', 'json_pointer')}
    if src.get('layer') != 'CACHE' or src.get('source_key') != want_key:
        return {'accepted': False, 'rejection': 'ROW_LAYER_NOT_CACHE', 'gates': gates}
    # 3 链
    chain, err = chain_of(tab, cid, adm)
    if err:
        return {'accepted': False, 'rejection': err, 'gates': gates}
    gates.update(pattern_id=chain['pattern_id'], pattern_pointer=chain['pattern_pointer'],
                 child_ids=[c['skillid'] for c in chain['children']],
                 child_types=[c['type'] for c in chain['children']])
    if chain['pattern_id'] != adm['pattern_id']:
        return {'accepted': False, 'rejection': 'PATTERN_ID_DRIFT',
                'detail': {'expected': adm['pattern_id'], 'actual': chain['pattern_id']},
                'gates': gates}
    if [c['skillid'] for c in chain['children']] != adm['chain_ids']:
        return {'accepted': False, 'rejection': 'CHAIN_IDS_DRIFT',
                'detail': {'expected': adm['chain_ids'],
                           'actual': [c['skillid'] for c in chain['children']]},
                'gates': gates}
    if [c['type'] for c in chain['children']] != adm['chain_types']:
        return {'accepted': False, 'rejection': 'CHAIN_TYPES_DRIFT',
                'detail': {'expected': adm['chain_types'],
                           'actual': [c['type'] for c in chain['children']]},
                'gates': gates}
    # 4 载体唯一 + 参数
    t27 = [c for c in chain['children'] if c['type'] == 27]
    gates['t27_records'] = [c['skillid'] for c in t27]
    if len(t27) != 1:
        return {'accepted': False, 'rejection': 'T27_CARRIER_NOT_UNIQUE', 'gates': gates}
    bound = t27[0]
    if bound['skillid'] != adm['record_id']:
        return {'accepted': False, 'rejection': 'T27_RECORD_DRIFT',
                'detail': {'expected': adm['record_id'], 'actual': bound['skillid']},
                'gates': gates}
    states, actual = {}, {}
    for f in (HEAL_FIELD, LIMIT_FIELD, COUNT_FIELD):
        raw = bound['params'].get(f)
        states[f] = raw_state(raw, present=f in bound['params'])
        actual[f] = raw
    gates['params'] = actual
    gates['param_states'] = states
    for f in (HEAL_FIELD, LIMIT_FIELD, COUNT_FIELD):
        if states[f] != 'FINITE':
            return {'accepted': False, 'rejection': 'PARAM_%s_%s' % (f.upper(), states[f]),
                    'detail': {f: actual[f]}, 'gates': gates}
        if float(actual[f]) <= 0:
            return {'accepted': False, 'rejection': 'PARAM_%s_NON_POSITIVE' % f.upper(),
                    'detail': {f: actual[f]}, 'gates': gates}
    if actual != adm['params']:
        return {'accepted': False, 'rejection': 'PARAM_VALUE_DRIFT',
                'detail': {'expected': adm['params'], 'actual': actual}, 'gates': gates}
    # 5 句面唯一（pattern 正文）
    sinfo = str(chain['pattern'].get('sinfo') or '')
    if not sinfo:
        return {'accepted': False, 'rejection': 'PATTERN_SINFO_MISSING', 'gates': gates}
    body = canon(row.get('japanese'))
    n_body = canon(sinfo).count(body)
    n_mech = len(HEAL_MECH_RX.findall(canon(sinfo)))
    gates['sentence'] = {'body_occurrences': n_body, 'heal_mechanism_occurrences': n_mech}
    if n_body != 1:
        return {'accepted': False, 'rejection': 'ROW_BODY_NOT_UNIQUE_IN_PATTERN',
                'gates': gates}
    if n_mech != 1:
        return {'accepted': False, 'rejection': 'HEAL_MECHANISM_NOT_UNIQUE_IN_PATTERN',
                'gates': gates}
    # 6 同卡已有的 27 键答案（只披露/去重，不作准入）
    same_card = []
    for other in (rows or {}).values() if isinstance(rows, dict) else []:
        for a in other.get('answers') or []:
            if a.get('rule_key') == RULE_KEY:
                same_card.append({'row_id': other.get('row_id'),
                                  'record_id': a.get('record_id'),
                                  'raw_value': a.get('raw_value')})
    gates['same_card_t27_answers_at_eval'] = same_card
    # 7 去重
    existing = [a for a in row.get('answers') or [] if a.get('rule_key') == RULE_KEY]
    gates['existing_same_rule_key'] = [{'record_id': a.get('record_id'),
                                        'raw_value': a.get('raw_value')} for a in existing]
    same_rec_value = [a for a in existing
                      if a.get('record_id') == bound['skillid']
                      and a.get('raw_value') == actual[HEAL_FIELD]]
    same_value = [a for a in existing if a.get('raw_value') == actual[HEAL_FIELD]]
    if same_rec_value:
        return {'accepted': False, 'rejection': 'ALREADY_PRESENT_SAME', 'gates': gates}
    if existing:
        dedup = ('SAME_VALUE_DIFF_RECORD_EXISTING' if same_value
                 else 'CONFLICT_EXISTING_VALUE')
        return {'accepted': False, 'rejection': 'ALREADY_ANSWERED',
                'detail': {'dedup': dedup,
                           'existing': gates['existing_same_rule_key'],
                           'selected': {'record_id': bound['skillid'],
                                        'raw_value': actual[HEAL_FIELD]}},
                'gates': gates}
    return {'accepted': True, 'rejection': None, 'gates': gates, 'chain': chain,
            'bound': bound, 'params': actual,
            'detail': None}


# ---------------------------------------------------------------- 答案与 marker

def _source(bound, chain, adm):
    pointer = '/bossinfo/bossskill/%d' % bound['index']
    return {
        'table': 'bossskill', 'record_id': bound['skillid'], 'layer': 'CACHE',
        'field_path': '/' + HEAL_FIELD,
        'source_key': 'CACHE/bossinfo.data5.json.raw',
        'original_file': 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw',
        'json_pointer': pointer,
        'field': '/' + HEAL_FIELD,
        'field_json_pointer': pointer + '/' + HEAL_FIELD,
        'record_key': 'CACHE/bossinfo.data5.json.raw#%s' % pointer,
        'source_resolution': EXACT,
        'note': ('按解码 JSON 的 bossskill.skillid 唯一命中；经本行原始链（%s，pattern %s）'
                 '链内唯一 type27 定源' % (chain['pattern_pointer'], chain['pattern_id'])),
    }


def _marker(adm, chain, bound, params, same_card):
    return {
        'scope': SCOPE,
        'module': MODULE_VERSION,
        'cid': adm['cid'],
        'row_id': adm['row_id'],
        'rule_key': RULE_KEY,
        'field_path': '/' + HEAL_FIELD,
        'table': 'bossskill',
        'record_id': bound['skillid'],
        'layer': 'CACHE',
        'pattern_id': chain['pattern_id'],
        'pattern_pointer': chain['pattern_pointer'],
        'chain_ids': [c['skillid'] for c in chain['children']],
        'chain_types': [c['type'] for c in chain['children']],
        'bound_slot': bound['slot'],
        'bound_type': 27,
        'params': params,
        'field_values_disclosed': {
            LIMIT_FIELD: {'raw': params[LIMIT_FIELD], 'unit': '游戏秒（fixedDeltaTime累计）',
                          'meaning_zh': '回复间隔输入（存入 _regenerationTimeMax）'},
            COUNT_FIELD: {'raw': params[COUNT_FIELD], 'unit': '次',
                          'meaning_zh': '回复次数（向零截断后存入 _regenerationNum）'},
        },
        'not_written': ('p2/p3 只作字段值披露，不写答案、不换算实机秒数；'
                        '「全状態異常も回復」子句不由本批覆盖'),
        'same_card_t27_answers_at_eval': same_card,
        'admission': 'RULE_CONFIRMED_AND_CHAIN_CARRIER_UNIQUE（同卡 0 披露：准入不依赖同卡交叉核）',
        'association': '推断',
        'limits': LIMIT,
    }


def build_answers(data, cid, row, res):
    import rules as R
    adm = ADMITTED[row['row_id']]
    chain, bound, params = res['chain'], res['bound'], res['params']
    converted = R.answer_for('bossskill', 27, '/' + HEAL_FIELD, params[HEAL_FIELD],
                             bound['record'], source_layer='CACHE')
    if converted is None:
        return None
    rule = R.rule_for('bossskill', 27, '/' + HEAL_FIELD) or {}
    num = _num(params[HEAL_FIELD])
    value = ('周期回复输入：floor/clamp(float32(B × %s))（B=getBasicSkillAttack(true)，'
             '已含 Chain；整数化 0x14374bc）；对象：味方全体（句面）；回复间隔字段 %s=%s 游戏秒、'
             '回复次数字段 %s=%s 次（已确认字段值，不换算实机间隔）；'
             '不证明最终 HP 回复量、超上限保留比例、实际触发间隔与次数（关联推断）'
             % (num, LIMIT_FIELD, _num(params[LIMIT_FIELD]),
                COUNT_FIELD, _num(params[COUNT_FIELD])))
    marker = _marker(adm, chain, bound, params, res['gates'].get('same_card_t27_answers_at_eval'))
    answer = {
        'value': value,
        'quantity_kind': converted.get('quantity_kind'),
        'unit': converted.get('unit'),
        'value_text': converted.get('value_text'),
        'raw_value': params[HEAL_FIELD],
        'effective_float32': _f32(params[HEAL_FIELD]),
        'quantitative': True,
        'numeric_source': '复用既有局部规则；记录归属为推断',
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'evidence_scope': 'T27_PERIODIC_HEAL_20261030',
        'answer_status': 'CONFIRMED_FORMULA_ONLY',
        'rule_key': RULE_KEY,
        'table': 'bossskill',
        'record_id': bound['skillid'],
        'layer': 'CACHE',
        'field_path': '/' + HEAL_FIELD,
        'source': _source(bound, chain, adm),
        'rule_status': rule.get('status'),
        'conversion': rule.get('conversion'),
        'base_definition': rule.get('base_definition'),
        'conditions': rule.get('applicability'),
        'rule_limits': rule.get('limits'),
        'condition_label': ('%s / pattern %s 被选中且链内唯一 type27 生效时'
                            % (chain['pattern_pointer'], chain['pattern_id'])),
        'target': '味方全体（由句面给出；rules.target 为空，受疗对象选择未复查）',
        'binding': {'c8_p1_t27_binding': marker},
        'context': '周期回复（t27）句',
        'note': ('仅已确认静态规则下单次回复量系数的输入实例；描述归属为推断（句面机制名与链内'
                 '唯一载体一致，同卡无既有披露可交叉核）。' + LIMIT),
        'evidence': EVIDENCE[:],
    }
    return [answer]


def _append(row, answers, res):
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    existing = {key(a) for a in row.get('answers') or []}
    added = 0
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault('answers', []).append(answer)
        existing.add(key(answer))
        added += 1
    if not added:
        return 0
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = ('推断（C8-B2 周期回复 t27：链内载体唯一＋规则已确认；'
                            '同卡无既有披露，关联仍推断）')
    row['partial'] = True
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = list(dict.fromkeys(list(scopes) + ['T27_PERIODIC_HEAL_20261030']))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    binding = answers[0]['binding']['c8_p1_t27_binding']
    reasons.append('C8-B2：HP 周期回复子句已按链内唯一 type27（记录 %s）的 skillparam1 绑定'
                   '单次回复量系数；skillparam2=%s 游戏秒／skillparam3=%s 次只作已确认字段值披露；'
                   '同句「全状態異常も回復」等其余机制未覆盖，账本行仍为拆分待核查；'
                   '最终 HP、实机间隔与次数未验证。'
                   % (binding['record_id'], _num(binding['params'][LIMIT_FIELD]),
                      _num(binding['params'][COUNT_FIELD])))
    row['unknown_reasons'] = list(dict.fromkeys(reasons))
    marker = row.setdefault(MARKER_KEY, dict(binding))
    marker.setdefault('bindings', [])
    for answer in answers:
        m = answer['binding']['c8_p1_t27_binding']
        marker['bindings'].append({'rule_key': m['rule_key'], 'field_path': m['field_path'],
                                   'record_id': m['record_id'], 'params': m['params']})
    marker['bindings'] = list({(b['rule_key'], b['field_path']): b
                               for b in marker['bindings']}.values())
    return added


def _merge_disclosure(row, detail, same_card):
    marker = row.setdefault(MARKER_KEY, {
        'scope': SCOPE, 'module': MODULE_VERSION, 'row_id': row.get('row_id'),
        'bindings': []})
    marker.setdefault('disclosures', []).append({
        'dedup': detail.get('dedup'), 'rule_key': RULE_KEY,
        'existing': detail.get('existing'), 'selected': detail.get('selected'),
        'same_card_t27_answers_at_eval': same_card,
        'disclosure': ('本行已有同 rule_key 答案；本批选中的记录与原值如 selected，'
                       '不新增答案、不改写既有值，只披露。'),
    })


# ---------------------------------------------------------------- 正式页消费

def apply_to_groups(data, cid, groups):
    """正式页消费：为 15 行冻结准入表写 t27 周期回复绑定答案（不覆盖既有答案）。"""
    report = {'scope': SCOPE, 'cid': cid, 'evaluated': 0, 'answers_added': 0,
              'additions': [], 'markers': [], 'rejections': [], 'skipped_existing': 0,
              'marker_only': 0, 'out_of_scope': True}
    if cid not in ADMITTED_CIDS:
        return report
    report['out_of_scope'] = False
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append({'reason': 'ZERO_TOUCH_CID', 'cid': cid})
        return report
    rows = {r['row_id']: r for g in groups or [] for s in g.get('skills') or []
            for r in s.get('rows') or []}
    tab = tables(data)
    for rid, adm in sorted(ADMITTED.items(), key=lambda kv: kv[0]):
        if adm['cid'] != cid:
            continue
        row = rows.get(rid)
        if row is None:
            report['rejections'].append({'row_id': rid, 'reason': 'ROW_NOT_FOUND'})
            continue
        report['evaluated'] += 1
        res = evaluate(data, cid, row, rows=rows, tab=tab)
        if not res['accepted']:
            if res['rejection'] == 'ALREADY_ANSWERED':
                _merge_disclosure(row, res.get('detail') or {},
                                  res['gates'].get('same_card_t27_answers_at_eval'))
                report['marker_only'] += 1
                report['markers'].append({'row_id': rid,
                                          'dedup': (res.get('detail') or {}).get('dedup')})
            elif res['rejection'] == 'ALREADY_PRESENT_SAME':
                report['skipped_existing'] += 1
                report['markers'].append({'row_id': rid, 'dedup': 'ALREADY_PRESENT_SAME'})
            else:
                report['rejections'].append({'row_id': rid, 'reason': res['rejection'],
                                             'detail': res.get('detail')})
            continue
        answers = build_answers(data, cid, row, res)
        if answers is None:
            report['rejections'].append({'row_id': rid, 'reason': 'RULE_UNAVAILABLE'})
            continue
        added = _append(row, answers, res)
        if added:
            report['answers_added'] += added
            for answer in answers:
                report['additions'].append({'row_id': rid,
                                            'record_id': answer['record_id'],
                                            'rule_key': answer['rule_key'],
                                            'field_path': answer['field_path'],
                                            'raw_value': answer['raw_value']})
        else:
            report['skipped_existing'] += 1
    return report


if __name__ == '__main__':
    raise SystemExit('只读探针请用 batch 构建/scratch 用例；本模块不提供写入口')
