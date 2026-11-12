# -*- coding: utf-8 -*-
"""C9-B2 t64 受击回复（7 行 / 7 效果，全 Y.G.）：t27 同级标准的冻结准入。

任务卡 ``docs/tasks/20261030-c9-p1-throughput-package.md``；预检
``output/character_skills/c9_p1_20261030/precheck/``（``precheck_report.md`` §2、
``batch_plan.json`` 的 ``host_ruling_required[0]``、``boundary_cases.json``）。

为什么是这 7 行
---------------
句面固定为「（さらに/その後、）味方全体にダメージを受けるたびに上限を超えて小回復し、
全状態異常を回復する効果を与える。」。每行在**本行自己的执行链**（``special_move`` 的
``patternN`` 或 ``denju.patternid0``）里**恰有一条 type64**，其 ``skillparam1`` 与冻结值
逐位相等（1.5 / 1.75 / 1.5 / 1.5 / 2 / 1.5 / 1.75）；句面正文在该 pattern ``sinfo`` 里
出现恰 1 次、且「ダメージを受けるたびに上限を超えて」恰 1 次，因此「本行句 ↔ 链内唯一
t64」不是按句序猜的。

准入标准（与 C8-B2 t27 同级）
----------------------------
1. **规则已确认**：``profiles/rules.json`` ``bossskill|64|/skillparam1``
   （origin＝``output/character_skills/boss_heal_types/type_rules.json`` 的 ``types.64``，
   ``native_checks.json`` 的 ``g64.*`` 六项 True；原生 ``bhSkillUtil.Exec_REACTIVE_HEAL``
   0x1196988 ``fmul`` → 0x119698c 整数化 → ``CharaStatus.setReactiveHeal``）。
2. **链内载体唯一**：本行链内 type64 恰 1 条，记录 id 与冻结值相等。
3. **句面机制唯一**：本行句身与机制短语在 pattern 正文各恰 1 次。
4. **同卡 0 披露显式登记**：三张卡在本批之前 t64 键答案数均为 0（全库只有 30310 的
   4 条）。准入**不依赖**同卡交叉核；跨卡 30310 先例只在披露中引用，不构成本批放行
   依据（30310 是 ``card_page_inference_kyoumei_ab`` 四卡窄批 + C7-P2 单行）。

不写的东西（与 30310 已交付口径相同）
------------------------------------
最终 HP 回复量、超上限保留比例、单场触发次数、实机间隔、「全状態異常を回復」子句。
原生 ``target_selection`` 为空：受疗对象只由句面「味方全体」给出，答案 ``target``
逐字写明，不把对象选择当原生证据。

账本侧
------
``effect_ledger._RULE_KEY_EFFECT`` 已含 ``bossskill|64|/skillparam1`` →
``回復（词表外）``（共鳴必殺A/B 批登记，30310 的答案就是走这条全局表消费的）。
本模块**不新增映射、不改 effect_ledger.py／rules.json／rules.py**；答案带
``binding.c9_p1_t64_binding`` 仅作逐行溯源，不改变映射路径。

判据（逐行硬门，任一不符即拒绝，不猜）
------------------------------------
1. ``row_id`` 在冻结表内、cid 一致、``group`` 一致。
2. ``japanese`` 与冻结句面逐字（NFKC＋空白归一）相同；``reference_field`` 等于冻结值。
3. 行 ``source.layer == CACHE``；``special_move`` 行 ``source_key == CACHE/bossinfo.data5.json.raw``
   且 ``source.record_key`` 指向该 pattern；``denju`` 行 ``source_key ==
   CACHE/denju.data5.json.raw``。
4. 链可达且唯一：``charainfo.patternN`` 或 ``denju.patternid0`` 在该层 ``bosspattern``
   唯一命中；槽位从 0 连续；子记录 ``skillid`` 在本层 ``bossskill`` 唯一命中；链 id /
   类型序列等于冻结值。
5. 载体唯一：链内 type64 **恰 1 条**，``skillid`` 等于冻结记录；``skillparam1``
   FINITE 且 >0（MISSING/NULL/NON_FINITE/ZERO/NEGATIVE 独立拒绝，不补零），逐位等于
   冻结值。
6. 句面唯一：pattern ``sinfo`` 含本行句身恰 1 次、含机制短语恰 1 次。
7. 同卡 t64 披露：登记本批之前同卡已有的同键答案（只披露/去重，不作准入）。
8. 幂等与去重：本行已有同 rule_key 答案时——同记录同值 → ``ALREADY_PRESENT_SAME``；
   其余 → ``ALREADY_ANSWERED``（只披露，不新增、不改写）。
9. 保护卡 30236／30239 零触碰。

证据分档（不得升格）
--------------------
``skillparam1`` 的语义是 ``rules.json`` 已确认的静态规则；「哪一条 t64 对应本行句面」是
结构/唯一性证据；对象/触发只由句面给出。故答案 ``numeric_evidence = 确认``（原值＋已确认
规则键）、``association_evidence = 推断``，不写最终 HP、不写实机间隔/次数，不做实机验证。
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

MODULE_VERSION = 'c9_p1_t64_reactive_heal_20261030'
SCOPE = 'C9_P1_T64_REACTIVE_HEAL_20261030'
RULE_KEY = 'bossskill|64|/skillparam1'
HEAL_FIELD = 'skillparam1'
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

MARKER_KEY = 'inference_c9_p1_t64'
MECH_RX = re.compile(r'ダメージを受けるたびに上限を超えて')

_STALE_REASONS = {
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应',
}

J_30110 = 'さらに味方全体にダメージを受けるたびに上限を超えて小回復し、全状態異常を回復する効果を与える。'
J_30203 = 'その後、味方全体にダメージを受けるたびに上限を超えて小回復し、全状態異常を回復する効果を与える。'
J_30223 = J_30203

#: 冻结准入表（2026-10-30 由原始 CACHE 记录与当前正式页独立重导一致后固化）。
_ADMITTED_LIST = [
    dict(cid=30110, group='special_move', ref='pattern1',
         row_id='30110-special_move-special_move-pattern1-lvorder1-f2',
         pattern_id=43011001, chain_ids=[43011000, 43011001, 43011002, 43011003],
         chain_types=[110, 3, 64, 13], record_id=43011002,
         params={HEAL_FIELD: 1.5}, japanese=J_30110),
    dict(cid=30110, group='special_move', ref='pattern2',
         row_id='30110-special_move-special_move-pattern2-lvorder2-f2',
         pattern_id=43011002, chain_ids=[43011004, 43011005, 43011006, 43011007],
         chain_types=[110, 3, 64, 13], record_id=43011006,
         params={HEAL_FIELD: 1.75}, japanese=J_30110),
    dict(cid=30110, group='denju', ref='denju.denju_id == cid',
         row_id='30110-denju-denju-denju_denju_id____cid-lvorder0-f2',
         pattern_id=43011003, chain_ids=[43011000, 43011001, 43011002, 43011003],
         chain_types=[110, 3, 64, 13], record_id=43011002,
         params={HEAL_FIELD: 1.5}, japanese=J_30110),
    dict(cid=30203, group='special_move', ref='pattern0',
         row_id='30203-special_move-special_move-pattern0-lvorder0-f1',
         pattern_id=43020300, chain_ids=[43020300, 43020301, 43020302],
         chain_types=[112, 64, 13], record_id=43020301,
         params={HEAL_FIELD: 1.5}, japanese=J_30203),
    dict(cid=30203, group='special_move', ref='pattern2',
         row_id='30203-special_move-special_move-pattern2-lvorder2-f1',
         pattern_id=43020302, chain_ids=[43020304, 43020305, 43020306],
         chain_types=[112, 64, 13], record_id=43020305,
         params={HEAL_FIELD: 2}, japanese=J_30203),
    dict(cid=30223, group='special_move', ref='pattern0',
         row_id='30223-special_move-special_move-pattern0-lvorder0-f1',
         pattern_id=43022300, chain_ids=[43022300, 43022301, 43022302],
         chain_types=[13, 64, 3], record_id=43022301,
         params={HEAL_FIELD: 1.5}, japanese=J_30223),
    dict(cid=30223, group='special_move', ref='pattern1',
         row_id='30223-special_move-special_move-pattern1-lvorder1-f1',
         pattern_id=43022301, chain_ids=[43022303, 43022304, 43022305],
         chain_types=[13, 64, 3], record_id=43022304,
         params={HEAL_FIELD: 1.75}, japanese=J_30223),
]
ADMITTED = {item['row_id']: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item['cid'] for item in _ADMITTED_LIST)

EVIDENCE = [
    'output/character_skills/c9_p1_20261030/precheck/precheck_report.md',
    'output/character_skills/c9_p1_20261030/precheck/batch_plan.json',
    'output/character_skills/c9_p1_20261030/precheck/boundary_cases.json',
    'output/character_skills/boss_heal_types/type_rules.json',
    'output/character_skills/boss_heal_types/native_checks.json',
]
LIMIT = ('skillparam1 为已确认静态规则（reactive heal 基值，非最终 HP）；「哪条 t64 对应'
         '本行句面」为结构/唯一性证据，关联＝推断；对象/触发只由句面「味方全体／ダメージを'
         '受けるたび」给出（原生 target_selection 为空，受疗对象选择未复查）；不写最终 HP '
         '回复量、超上限保留比例、实际触发次数与间隔，不做实机验证。')

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
    """单行判定（不写入）。``rows`` 为同卡全部行（同卡 64 键答案披露/去重）。"""
    rid = row.get('row_id')
    if cid in ZERO_TOUCH_CIDS:
        return {'accepted': False, 'rejection': 'ZERO_TOUCH_CID'}
    adm = ADMITTED.get(rid)
    if adm is None:
        return {'accepted': False, 'rejection': 'NOT_IN_BATCH_SCOPE'}
    if adm['cid'] != cid:
        return {'accepted': False, 'rejection': 'CID_MISMATCH'}
    if row.get('group') != adm['group']:
        return {'accepted': False, 'rejection': 'GROUP_MISMATCH'}
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
    t64 = [c for c in chain['children'] if c['type'] == 64]
    gates['t64_records'] = [c['skillid'] for c in t64]
    if len(t64) != 1:
        return {'accepted': False, 'rejection': 'T64_CARRIER_NOT_UNIQUE', 'gates': gates}
    bound = t64[0]
    if bound['skillid'] != adm['record_id']:
        return {'accepted': False, 'rejection': 'T64_RECORD_DRIFT',
                'detail': {'expected': adm['record_id'], 'actual': bound['skillid']},
                'gates': gates}
    raw = bound['params'].get(HEAL_FIELD)
    state = raw_state(raw, present=HEAL_FIELD in bound['params'])
    gates['params'] = {HEAL_FIELD: raw}
    gates['param_states'] = {HEAL_FIELD: state}
    if state != 'FINITE':
        return {'accepted': False, 'rejection': 'PARAM_%s_%s' % (HEAL_FIELD.upper(), state),
                'detail': {HEAL_FIELD: raw}, 'gates': gates}
    if float(raw) <= 0:
        return {'accepted': False, 'rejection': 'PARAM_%s_NON_POSITIVE' % HEAL_FIELD.upper(),
                'detail': {HEAL_FIELD: raw}, 'gates': gates}
    if float(raw) != float(adm['params'][HEAL_FIELD]):
        return {'accepted': False, 'rejection': 'PARAM_VALUE_DRIFT',
                'detail': {'expected': adm['params'], 'actual': gates['params']},
                'gates': gates}
    # 5 句面唯一（pattern 正文）
    sinfo = str(chain['pattern'].get('sinfo') or '')
    if not sinfo:
        return {'accepted': False, 'rejection': 'PATTERN_SINFO_MISSING', 'gates': gates}
    body = canon(row.get('japanese'))
    n_body = canon(sinfo).count(body)
    n_mech = len(MECH_RX.findall(canon(sinfo)))
    gates['sentence'] = {'body_occurrences': n_body, 'mechanism_occurrences': n_mech}
    if n_body != 1:
        return {'accepted': False, 'rejection': 'ROW_BODY_NOT_UNIQUE_IN_PATTERN',
                'gates': gates}
    if n_mech != 1:
        return {'accepted': False, 'rejection': 'HEAL_MECHANISM_NOT_UNIQUE_IN_PATTERN',
                'gates': gates}
    # 6 同卡已有的 64 键答案（只披露/去重，不作准入）
    same_card = []
    for other in (rows or {}).values() if isinstance(rows, dict) else []:
        for a in other.get('answers') or []:
            if a.get('rule_key') == RULE_KEY:
                same_card.append({'row_id': other.get('row_id'),
                                  'record_id': a.get('record_id'),
                                  'raw_value': a.get('raw_value')})
    gates['same_card_t64_answers_at_eval'] = same_card
    # 7 去重
    existing = [a for a in row.get('answers') or [] if a.get('rule_key') == RULE_KEY]
    gates['existing_same_rule_key'] = [{'record_id': a.get('record_id'),
                                        'raw_value': a.get('raw_value')} for a in existing]
    same_rec_value = [a for a in existing
                      if a.get('record_id') == bound['skillid']
                      and a.get('raw_value') == raw]
    if same_rec_value:
        return {'accepted': False, 'rejection': 'ALREADY_PRESENT_SAME', 'gates': gates}
    if existing:
        return {'accepted': False, 'rejection': 'ALREADY_ANSWERED',
                'detail': {'dedup': 'CONFLICT_EXISTING_VALUE',
                           'existing': gates['existing_same_rule_key'],
                           'selected': {'record_id': bound['skillid'], 'raw_value': raw}},
                'gates': gates}
    return {'accepted': True, 'rejection': None, 'gates': gates, 'chain': chain,
            'bound': bound, 'params': {HEAL_FIELD: raw}, 'detail': None}


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
        'source_resolution': 'RESOLVED_EXACT_DECODED_RECORD',
        'note': ('按解码 JSON 的 bossskill.skillid 唯一命中；经本行原始链（%s，pattern %s）'
                 '链内唯一 type64 定源' % (chain['pattern_pointer'], chain['pattern_id'])),
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
        'bound_type': 64,
        'params': params,
        'native_target_selection': None,
        'target_from_sentence_only': True,
        'not_written': ('最终 HP 回复量、超上限保留比例、单场触发次数、实机间隔、'
                        '「全状態異常も回復」子句均不写'),
        'same_card_t64_answers_at_eval': same_card,
        'admission': ('RULE_CONFIRMED_AND_CHAIN_CARRIER_UNIQUE_AND_MECHANISM_UNIQUE'
                      '（同卡 0 披露显式登记，准入不依赖同卡交叉核；跨卡 30310 先例不作放行依据）'),
        'association': '推断',
        'limits': LIMIT,
    }


def build_answers(data, cid, row, res):
    import rules as R
    adm = ADMITTED[row['row_id']]
    chain, bound, params = res['chain'], res['bound'], res['params']
    raw = params[HEAL_FIELD]
    converted = R.answer_for('bossskill', 64, '/' + HEAL_FIELD, raw,
                             bound['record'], source_layer='CACHE')
    if converted is None:
        return None
    rule = R.rule_for('bossskill', 64, '/' + HEAL_FIELD) or {}
    num = _num(raw)
    value = ('reactive heal 输入：floor/clamp(float32(B × %s))（B=getBasicSkillAttack(true)，'
             '已含 Chain；原生 0x1196988 fmul → 0x119698c 整数化 → '
             'CharaStatus.setReactiveHeal）；对象：味方全体（句面）；触发：ダメージを受ける'
             'たび（句面）；不证明最终 HP 回复量、超上限保留比例、实际触发次数与间隔（关联推断）'
             % num)
    marker = _marker(adm, chain, bound, params,
                     res['gates'].get('same_card_t64_answers_at_eval'))
    answer = {
        'value': value,
        'quantity_kind': converted.get('quantity_kind'),
        'unit': converted.get('unit'),
        'value_text': converted.get('value_text'),
        'raw_value': raw,
        'effective_float32': _f32(raw),
        'quantitative': True,
        'numeric_source': '复用既有已确认局部规则；记录归属为推断',
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'evidence_scope': SCOPE,
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
        'condition_label': ('%s / pattern %s 被选中且链内唯一 type64 生效时'
                            % (chain['pattern_pointer'], chain['pattern_id'])),
        'target': '味方全体（由句面给出；原生 target_selection 为空，受疗对象选择未复查）',
        'binding': {'c9_p1_t64_binding': marker},
        'context': '受击回复（t64）句',
        'note': ('仅已确认静态规则下 reactive heal 基值系数的输入实例；描述归属为推断'
                 '（规则已确认＋链内唯一 type64＋句面机制唯一，同卡 0 披露）。' + LIMIT),
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
    row['evidence_label'] = ('推断（C9-B2 t64 受击回复：规则确认＋链内载体唯一＋句面机制唯一；'
                            '同卡 0 披露）')
    row['partial'] = True
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = list(dict.fromkeys(list(scopes) + [SCOPE]))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    binding = answers[0]['binding']['c9_p1_t64_binding']
    reasons.append('C9-B2：受击回复子句已按链内唯一 type64（记录 %s）的 skillparam1 绑定'
                   'reactive heal 基值系数 %s；同句「全状態異常も回復」等其余机制未覆盖；'
                   '最终 HP、超上限保留比例、实际触发次数与间隔未验证。'
                   % (binding['record_id'], _num(binding['params'][HEAL_FIELD])))
    row['unknown_reasons'] = list(dict.fromkeys(reasons))
    marker = row.setdefault(MARKER_KEY, dict(binding))
    marker.setdefault('bindings', [])
    for answer in answers:
        m = answer['binding']['c9_p1_t64_binding']
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
        'same_card_t64_answers_at_eval': same_card,
        'disclosure': ('本行已有同 rule_key 答案；本批选中的记录与原值如 selected，'
                       '不新增答案、不改写既有值，只披露。'),
    })


# ---------------------------------------------------------------- 正式页消费

def apply_to_groups(data, cid, groups):
    """正式页消费：为 7 行冻结准入表写 t64 受击回复绑定答案（不覆盖既有答案）。"""
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
                                  res['gates'].get('same_card_t64_answers_at_eval'))
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
