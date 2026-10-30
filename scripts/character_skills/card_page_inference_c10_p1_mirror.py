# -*- coding: utf-8 -*-
"""C10-B1 同卡同记录同原值 skilltext 镜像整理（6 行 / 6 效果，全 Y.G.）。

任务卡 ``docs/tasks/20261030-c10-p1-throughput-package.md``；预检
``output/character_skills/c10_p1_20261030/precheck/``（``precheck_report.md`` §3.3、
``batch_plan.json`` 的 ``host_ruling_required[1]`` 与 §6.2 FAMILY_REPEAT_T27_T64 裁决、
``boundary_cases.json``、``evidence_boundaries.md``）。

为什么是这 6 行
---------------
它们都是 **skilltext 行**（``reference_field == 'skilltext'``，来源
``CACHE/charainfo.data5.json.raw``），句面与**同卡基础档位（【共鳴必殺】）pattern 行逐字相同**，
且该基础档位行**已经**有同 rule_key＋同 record_id＋同 raw_value 的答案：

| cid | 本行（skilltext） | 键 | 记录 | 原值 | 同卡基档行 |
|---|---|---|---:|---:|---|
| 353 | f3 | ``bossskill|27|/skillparam1`` | 40035303 | 1.25 | pattern0 f3 |
| 30104 | f2 | ``bossskill|27|/skillparam1`` | 43010401 | 1.5 | pattern0 f2 |
| 30257 | f3 | ``bossskill|27|/skillparam1`` | 43025702 | 1.25 | pattern1 f3 |
| 30110 | f2 | ``bossskill|64|/skillparam1`` | 43011002 | 1.5 | pattern1 f2 |
| 30203 | f1 | ``bossskill|64|/skillparam1`` | 43020301 | 1.5 | pattern0 f1 |
| 30223 | f1 | ``bossskill|64|/skillparam1`` | 43022301 | 1.5 | pattern0 f1 |

**0 新增唯一数值、0 新公式、0 新规则键**：6 个原值早已在同卡基档行交付；本批只把这 6 个
未答的 skilltext 行归位到同一记录/原值。

为什么基础档（而不是超共鳴）
--------------------------
6 张卡的 skilltext 文本块**自身首句标签**都是 ``【共鳴必殺…】``（不是
``【超共鳴必殺…】``，逐行核 ``context_text``）；同文的超共鳴行标签为 ``【超共鳴必殺…】``
且记录/原值不同，逐行列为**排除值**（``excluded``），不并入。这是「同文不同档」的判别依据，
不是「挑一个喜欢的值」。

注：30104（以及 30110／30223）的 denju 行与本行同文同记录同值（C8/C9 已交付），但它们不是
**档位行**（``reference_field`` 以 ``denju.`` 开头），不进入「同文档位集合」；本模块只把
``pattern0/1/2`` 行当档位行。这也保证「同文超共鳴行」的排除集合恰为 1 条而不是把 denju
复制行误当第三档。

判据（逐行硬门，任一不符即拒绝，不猜）
------------------------------------
1. ``row_id`` 在冻结表内、cid/group 一致；``japanese`` 与冻结句面逐字（NFKC＋空白归一）相同；
   ``reference_field == 'skilltext'``。
2. 行来源：``source.layer == 'CACHE'``、``source.source_key == CACHE/charainfo.data5.json.raw``、
   ``source.field == '/skilltext'``（不跨层，不读 APK 表）。
3. 档位标签：本行 ``context_text`` 以 ``【共鳴必殺`` 开头且不以 ``【超共鳴必殺`` 开头。
4. 同卡基档披露**恰 1 条**：同卡内与本行同文、``reference_field`` 为 ``pattern0/1/2``、且已有
   ``rule_key == 冻结键`` 的答案，其 ``record_id``/``raw_value`` 与冻结值逐位相等；该行
   ``row_id``/``reference_field`` 与冻结值相等，其档位标签同为 ``【共鳴必殺``。
5. 同文档位集合**恰等于**「基档 1 条＋排除 1 条」：任何未登记的第三档（含同值异记录）→ 拒绝。
   排除项逐条核存在、同文、记录/原值等于冻结排除值。
6. 基档行的原始链逐位复核（CACHE）：``charainfo[cid].patternN`` 在该层 ``bosspattern`` 唯一命中；
   槽位从 0 连续；子记录 ``skillid`` 在该层 ``bossskill`` 唯一命中；链 id/类型序列等于冻结值；
   链内目标类型（27/64）**恰 1 条**且 ``skillid`` 等于冻结记录；``skillparam1`` FINITE>0 且
   逐位等于冻结原值（MISSING/NULL/NON_FINITE/NEGATIVE/ZERO 独立拒绝，不补零）。
   t27 另核 ``skillparam2``/``skillparam3`` FINITE>0（C8 同级，只作字段值披露）；t64 只记录
   其原值状态。
7. 句面唯一：基档 pattern ``sinfo`` 含本行句身恰 1 次、含机制短语（t27「一定間隔ごとに
   上限を超えて」／t64「ダメージを受けるたびに上限を超えて」）恰 1 次。
8. 幂等与去重：本行已有同 rule_key 答案时——同记录同值 → ``ALREADY_PRESENT_SAME``（零写入）；
   其余 → ``ALREADY_ANSWERED``（只披露，不新增、不改写）。
9. 保护卡 30236／30239 零触碰。

证据分档（不得升格）
--------------------
* 原值＋规则键：``numeric_evidence = 确认``（rules.json 已确认的静态规则；
  t27 origin ``output/boss_heal/field_dictionary.json``、t64 origin
  ``output/character_skills/boss_heal_types/type_rules.json``）。
* 「本行 skilltext 句面对应哪条记录」：依赖**同卡同文＋基档披露同键同记录同原值＋档位标签**
  的结构证据，故 ``association_evidence = 推断``。
* 对象/触发只由句面给出（``rules.target`` 为空，原生 ``target_selection`` 为空）；不写最终 HP、
  超上限保留比例、实际触发次数/间隔，不做实机验证。

账本侧
------
* t27：``effect_ledger`` 另立**来源限定窄映射** ``C10P1_T27_SKILLTEXT_MIRROR_20261030``
  （答案带 ``binding.c10_p1_mirror_binding`` 且 scope/rule_key/槽/表/记录/层逐项一致才消费），
  只把 ``bossskill|27|/skillparam1`` 绑到句面已有的「回復（词表外）」主张；**不整族映射 type27**，
  不改 ``_RULE_KEY_EFFECT``／C8 的 scope／rules.json／rules.py。
* t64：走既有全局 ``bossskill|64|/skillparam1 → 回復（词表外）``，本批不新增映射。
"""
from __future__ import annotations

import json
import math
import re
import struct
import unicodedata
from pathlib import Path

MODULE_VERSION = 'c10_p1_skilltext_mirror_20261030'
#: 账本消费用的 t27 来源限定 scope（effect_ledger.C10P1_T27_SCOPE 精确匹配）。
T27_SCOPE = 'C10_P1_T27_SKILLTEXT_MIRROR_20261030'
#: t64 走既有全局映射；本 scope 只作逐行溯源标记，不参与账本分支。
T64_SCOPE = 'C10_P1_T64_SKILLTEXT_MIRROR_20261030'
RULE_KEY = {27: 'bossskill|27|/skillparam1', 64: 'bossskill|64|/skillparam1'}
FIELD = '/skillparam1'
PARAM = 'skillparam1'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

MARKER_KEY = 'inference_c10_p1_mirror'
MECH = {27: re.compile(r'一定間隔ごとに上限を超えて'),
        64: re.compile(r'ダメージを受けるたびに上限を超えて')}
BASE_LABEL = '【共鳴必殺'
SUPER_LABEL = '【超共鳴必殺'

_STALE_REASONS = {
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应',
}

T_353 = 'また味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復し、同時に全状態異常も回復する。'
T_30104 = 'その後、味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。'
T_30257 = 'さらに味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復し、同時に全状態異常も回復する。'
T_30110 = 'さらに味方全体にダメージを受けるたびに上限を超えて小回復し、全状態異常を回復する効果を与える。'
T_30203 = 'その後、味方全体にダメージを受けるたびに上限を超えて小回復し、全状態異常を回復する効果を与える。'

#: 冻结准入表（2026-10-30 由原始 CACHE 记录、当前正式页与预检逐行重导一致后固化；
#: 输入漂移即拒绝，不静默重绑）。
_ADMITTED_LIST = [
    dict(cid=353, carrier_type=27,
         row_id='353-special_move-special_move-skilltext-lvorder3-f3', text=T_353,
         record_id=40035303, raw_value=1.25,
         base_ref='pattern0',
         base_row_id='353-special_move-special_move-pattern0-lvorder0-f3',
         base_pattern_id=40035300,
         base_chain_ids=[40035300, 40035301, 40035302, 40035303],
         base_chain_types=[110, 3, 13, 27],
         excluded=[dict(row_id='353-special_move-special_move-pattern2-lvorder2-f3',
                        ref='pattern2', record_id=40035311, raw_value=2)]),
    dict(cid=30104, carrier_type=27,
         row_id='30104-special_move-special_move-skilltext-lvorder2-f2', text=T_30104,
         record_id=43010401, raw_value=1.5,
         base_ref='pattern0',
         base_row_id='30104-special_move-special_move-pattern0-lvorder0-f2',
         base_pattern_id=43010400,
         base_chain_ids=[43010400, 43010401, 43010402, 43010403],
         base_chain_types=[51, 27, 13, 16],
         excluded=[dict(row_id='30104-special_move-special_move-pattern1-lvorder1-f3',
                        ref='pattern1', record_id=43010405, raw_value=1.75)]),
    dict(cid=30257, carrier_type=27,
         row_id='30257-special_move-special_move-skilltext-lvorder3-f3', text=T_30257,
         record_id=43025702, raw_value=1.25,
         base_ref='pattern1',
         base_row_id='30257-special_move-special_move-pattern1-lvorder1-f3',
         base_pattern_id=43025701,
         base_chain_ids=[43025700, 43025701, 43025702],
         base_chain_types=[55, 13, 27],
         excluded=[dict(row_id='30257-special_move-special_move-pattern2-lvorder2-f3',
                        ref='pattern2', record_id=43025708, raw_value=2)]),
    dict(cid=30110, carrier_type=64,
         row_id='30110-special_move-special_move-skilltext-lvorder3-f2', text=T_30110,
         record_id=43011002, raw_value=1.5,
         base_ref='pattern1',
         base_row_id='30110-special_move-special_move-pattern1-lvorder1-f2',
         base_pattern_id=43011001,
         base_chain_ids=[43011000, 43011001, 43011002, 43011003],
         base_chain_types=[110, 3, 64, 13],
         excluded=[dict(row_id='30110-special_move-special_move-pattern2-lvorder2-f2',
                        ref='pattern2', record_id=43011006, raw_value=1.75)]),
    dict(cid=30203, carrier_type=64,
         row_id='30203-special_move-special_move-skilltext-lvorder3-f1', text=T_30203,
         record_id=43020301, raw_value=1.5,
         base_ref='pattern0',
         base_row_id='30203-special_move-special_move-pattern0-lvorder0-f1',
         base_pattern_id=43020300,
         base_chain_ids=[43020300, 43020301, 43020302],
         base_chain_types=[112, 64, 13],
         excluded=[dict(row_id='30203-special_move-special_move-pattern2-lvorder2-f1',
                        ref='pattern2', record_id=43020305, raw_value=2)]),
    dict(cid=30223, carrier_type=64,
         row_id='30223-special_move-special_move-skilltext-lvorder2-f1', text=T_30203,
         record_id=43022301, raw_value=1.5,
         base_ref='pattern0',
         base_row_id='30223-special_move-special_move-pattern0-lvorder0-f1',
         base_pattern_id=43022300,
         base_chain_ids=[43022300, 43022301, 43022302],
         base_chain_types=[13, 64, 3],
         excluded=[dict(row_id='30223-special_move-special_move-pattern1-lvorder1-f1',
                        ref='pattern1', record_id=43022304, raw_value=1.75)]),
]
for _item in _ADMITTED_LIST:
    _item['group'] = 'special_move'
    _item['ref'] = 'skilltext'
    _item['rule_key'] = RULE_KEY[_item['carrier_type']]
    _item['scope'] = T27_SCOPE if _item['carrier_type'] == 27 else T64_SCOPE
ADMITTED = {item['row_id']: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item['cid'] for item in _ADMITTED_LIST)

EVIDENCE = [
    'output/character_skills/c10_p1_20261030/precheck/precheck_report.md',
    'output/character_skills/c10_p1_20261030/precheck/batch_plan.json',
    'output/character_skills/c10_p1_20261030/precheck/boundary_cases.json',
    'output/boss_heal/field_dictionary.json',
    'output/character_skills/boss_heal_types/type_rules.json',
    'output/character_skills/boss_heal_types/native_checks.json',
]
LIMIT = ('原值为已确认静态规则（t27 单次回复量系数／t64 reactive heal 基值，非最终 HP）；'
         '「本行 skilltext 句面对应哪条记录」为结构证据（同卡同文＋基础档披露同键同记录同原值＋'
         '档位标签【共鳴必殺】），关联＝推断；同文超共鳴行记录/原值不同，逐行披露不并入；'
         '对象/触发只由句面给出（rules.target 为空、原生 target_selection 为空）；不写最终 HP '
         '回复量、超上限保留比例、实际触发次数与间隔，不做实机验证。')

_TABLES = {}


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def tables(data):
    """CACHE 解码主表（按 root 缓存；只读）。"""
    root = Path(getattr(data, 'root', Path('.'))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = root / 'output/cache_full_20261015_v3/decoded'
        boss = _read(base / 'bossinfo.data5.json.raw')['bossinfo']
        patterns, skills = {}, {}
        for i, rec in enumerate(boss.get('bosspattern') or []):
            patterns.setdefault(rec.get('patternid'), []).append((i, rec))
        for i, rec in enumerate(boss.get('bossskill') or []):
            skills.setdefault(rec.get('skillid'), []).append((i, rec))
        chara_all = _read(base / 'charainfo.data5.json.raw')['charainfo']
        chara = {rec['cid']: rec for rec in chara_all}
        denju = {rec['denju_id']: (i, rec)
                 for i, rec in enumerate(_read(base / 'denju.data5.json.raw')['denju'])}
        _TABLES[key] = dict(patterns=patterns, skills=skills, chara=chara,
                            chara_all=chara_all, denju=denju,
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


def tier_label(context_text):
    """skilltext/pattern 文本块的档位标签（只认开头词形，不从值大小推断）。"""
    core = canon(context_text)
    if core.startswith(canon(SUPER_LABEL)):
        return 'SUPER'
    if core.startswith(canon(BASE_LABEL)):
        return 'BASE'
    return 'UNKNOWN'


# ---------------------------------------------------------------- 基档链

def pattern_pointer(tab, cid, ref):
    chara = tab['chara'].get(cid)
    if chara is None:
        return None, 'CHARAINFO_RECORD_MISSING'
    pid = chara.get(ref)
    return (pid, 'charainfo.' + ref, chara) if pid else (None, 'PATTERN_POINTER_MISSING')


def chain_of(tab, cid, ref):
    pid, pointer, owner = pattern_pointer(tab, cid, ref)
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

def _answer_view(answer):
    return {'rule_key': answer.get('rule_key'), 'record_id': answer.get('record_id'),
            'raw_value': answer.get('raw_value'), 'field_path': answer.get('field_path'),
            'table': answer.get('table'), 'layer': answer.get('layer')}


def evaluate(data, cid, row, rows=None, tab=None):
    """单行判定（不写入）。``rows`` 为同卡全部行（基档披露/排除集/去重）。"""
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
    gates = {'row_id': rid, 'cid': cid, 'carrier_type': adm['carrier_type']}
    # 1 行身份
    if canon(row.get('japanese')) != canon(adm['text']):
        return {'accepted': False, 'rejection': 'ROW_TEXT_NOT_ADMITTED', 'gates': gates}
    if str(row.get('reference_field') or '') != adm['ref']:
        return {'accepted': False, 'rejection': 'REFERENCE_FIELD_DRIFT', 'gates': gates}
    # 2 同层
    src = row.get('source') or {}
    gates['row_source'] = {k: src.get(k) for k in
                           ('record_key', 'source_key', 'layer', 'field', 'json_pointer')}
    if (src.get('layer') != 'CACHE'
            or src.get('source_key') != 'CACHE/charainfo.data5.json.raw'):
        return {'accepted': False, 'rejection': 'ROW_LAYER_NOT_CACHE', 'gates': gates}
    if str(src.get('field') or '') != '/skilltext':
        return {'accepted': False, 'rejection': 'SKILLTEXT_FIELD_DRIFT', 'gates': gates}
    # 2b 来源记录自洽：json_pointer 指向本卡 charainfo，且其 skilltext 含本行句身
    m = re.fullmatch(r'/charainfo/(\d+)', str(src.get('json_pointer') or ''))
    if not m:
        return {'accepted': False, 'rejection': 'CHARAINFO_POINTER_MISSING', 'gates': gates}
    idx = int(m.group(1))
    all_chara = tab.get('chara_all') or []
    rec = all_chara[idx] if 0 <= idx < len(all_chara) else None
    gates['charainfo'] = {'index': idx,
                          'cid': None if rec is None else rec.get('cid')}
    if rec is None or rec.get('cid') != cid:
        return {'accepted': False, 'rejection': 'CHARAINFO_RECORD_MISMATCH', 'gates': gates}
    if canon(adm['text']) not in canon(rec.get('skilltext')):
        return {'accepted': False, 'rejection': 'CHARAINFO_TEXT_MISSING', 'gates': gates}
    # 3 档位标签（本行）
    label = tier_label(row.get('context_text'))
    gates['row_tier_label'] = label
    if label != 'BASE':
        return {'accepted': False, 'rejection': 'ROW_TIER_NOT_BASE', 'gates': gates}
    # 4 同卡基档披露（恰 1 条同键同记录同原值）
    rows = rows if isinstance(rows, dict) else {}
    text = canon(adm['text'])
    same_text = []
    for other in rows.values():
        if canon(other.get('japanese')) != text:
            continue
        ref = str(other.get('reference_field') or '')
        if not ref.startswith('pattern'):
            continue
        for answer in other.get('answers') or []:
            if answer.get('rule_key') == adm['rule_key']:
                same_text.append((other, answer))
    gates['same_text_pattern_answers'] = [
        {'row_id': r['row_id'], 'ref': r.get('reference_field'),
         'tier': tier_label(r.get('context_text')), **_answer_view(a)}
        for r, a in same_text]
    base_hits = [(r, a) for r, a in same_text
                 if a.get('record_id') == adm['record_id']
                 and a.get('raw_value') == adm['raw_value']
                 and a.get('field_path') == FIELD
                 and a.get('table') == 'bossskill'
                 and a.get('layer') == 'CACHE']
    if len(base_hits) != 1:
        return {'accepted': False,
                'rejection': ('BASE_DISCLOSURE_MISSING' if not base_hits
                              else 'BASE_DISCLOSURE_AMBIGUOUS(%d)' % len(base_hits)),
                'gates': gates}
    base_row, base_answer = base_hits[0]
    gates['base_row_id'] = base_row.get('row_id')
    gates['base_reference_field'] = base_row.get('reference_field')
    gates['base_tier_label'] = tier_label(base_row.get('context_text'))
    if base_row.get('row_id') != adm['base_row_id']:
        return {'accepted': False, 'rejection': 'BASE_ROW_DRIFT',
                'detail': {'expected': adm['base_row_id'],
                           'actual': base_row.get('row_id')}, 'gates': gates}
    if str(base_row.get('reference_field') or '') != adm['base_ref']:
        return {'accepted': False, 'rejection': 'BASE_REF_DRIFT',
                'detail': {'expected': adm['base_ref'],
                           'actual': base_row.get('reference_field')}, 'gates': gates}
    if gates['base_tier_label'] != 'BASE':
        return {'accepted': False, 'rejection': 'BASE_TIER_NOT_BASE', 'gates': gates}
    # 5 同文档位集合恰等于基档＋排除
    want = sorted([(adm['base_row_id'], adm['record_id'], adm['raw_value'])]
                  + [(e['row_id'], e['record_id'], e['raw_value']) for e in adm['excluded']])
    got = sorted((r['row_id'], a.get('record_id'), a.get('raw_value')) for r, a in same_text)
    gates['same_text_tier_set'] = {'expected': [list(x) for x in want],
                                   'actual': [list(x) for x in got]}
    if got != want:
        return {'accepted': False, 'rejection': 'SAME_TEXT_TIER_SET_DRIFT', 'gates': gates}
    # 6 基档原始链
    chain, err = chain_of(tab, cid, adm['base_ref'])
    if err:
        return {'accepted': False, 'rejection': err, 'gates': gates}
    gates.update(pattern_id=chain['pattern_id'], pattern_pointer=chain['pattern_pointer'],
                 child_ids=[c['skillid'] for c in chain['children']],
                 child_types=[c['type'] for c in chain['children']])
    if chain['pattern_id'] != adm['base_pattern_id']:
        return {'accepted': False, 'rejection': 'PATTERN_ID_DRIFT',
                'detail': {'expected': adm['base_pattern_id'],
                           'actual': chain['pattern_id']}, 'gates': gates}
    if [c['skillid'] for c in chain['children']] != adm['base_chain_ids']:
        return {'accepted': False, 'rejection': 'CHAIN_IDS_DRIFT',
                'detail': {'expected': adm['base_chain_ids'],
                           'actual': [c['skillid'] for c in chain['children']]},
                'gates': gates}
    if [c['type'] for c in chain['children']] != adm['base_chain_types']:
        return {'accepted': False, 'rejection': 'CHAIN_TYPES_DRIFT',
                'detail': {'expected': adm['base_chain_types'],
                           'actual': [c['type'] for c in chain['children']]},
                'gates': gates}
    carrier = [c for c in chain['children'] if c['type'] == adm['carrier_type']]
    gates['carrier_records'] = [c['skillid'] for c in carrier]
    if len(carrier) != 1:
        return {'accepted': False, 'rejection': 'CARRIER_NOT_UNIQUE', 'gates': gates}
    bound = carrier[0]
    if bound['skillid'] != adm['record_id']:
        return {'accepted': False, 'rejection': 'CARRIER_RECORD_DRIFT',
                'detail': {'expected': adm['record_id'], 'actual': bound['skillid']},
                'gates': gates}
    raw = bound['params'].get(PARAM)
    state = raw_state(raw, present=PARAM in bound['params'])
    extra_fields = ('skillparam2', 'skillparam3') if adm['carrier_type'] == 27 else ()
    extra = {f: {'raw': bound['params'].get(f),
                 'state': raw_state(bound['params'].get(f), present=f in bound['params'])}
             for f in extra_fields}
    gates['params'] = {PARAM: raw}
    gates['param_states'] = {PARAM: state,
                             **{f: v['state'] for f, v in extra.items()}}
    if state != 'FINITE':
        return {'accepted': False, 'rejection': 'PARAM_%s_%s' % (PARAM.upper(), state),
                'detail': {PARAM: raw}, 'gates': gates}
    if float(raw) <= 0:
        return {'accepted': False, 'rejection': 'PARAM_%s_NON_POSITIVE' % PARAM.upper(),
                'detail': {PARAM: raw}, 'gates': gates}
    if float(raw) != float(adm['raw_value']):
        return {'accepted': False, 'rejection': 'PARAM_VALUE_DRIFT',
                'detail': {'expected': adm['raw_value'], 'actual': raw}, 'gates': gates}
    for f, v in extra.items():
        if v['state'] != 'FINITE' or float(v['raw']) <= 0:
            return {'accepted': False, 'rejection': 'PARAM_%s_%s' % (f.upper(), v['state']),
                    'detail': {f: v['raw']}, 'gates': gates}
    # 7 句面唯一（基档 pattern 正文）
    sinfo = str(chain['pattern'].get('sinfo') or '')
    if not sinfo:
        return {'accepted': False, 'rejection': 'PATTERN_SINFO_MISSING', 'gates': gates}
    body = canon(row.get('japanese'))
    n_body = canon(sinfo).count(body)
    n_mech = len(MECH[adm['carrier_type']].findall(canon(sinfo)))
    gates['sentence'] = {'body_occurrences': n_body, 'mechanism_occurrences': n_mech}
    if n_body != 1:
        return {'accepted': False, 'rejection': 'ROW_BODY_NOT_UNIQUE_IN_PATTERN',
                'gates': gates}
    if n_mech != 1:
        return {'accepted': False, 'rejection': 'MECHANISM_NOT_UNIQUE_IN_PATTERN',
                'gates': gates}
    gates['excluded_values'] = [
        {'row_id': e['row_id'], 'record_id': e['record_id'], 'raw_value': e['raw_value']}
        for e in adm['excluded']]
    gates['same_card_base_disclosure'] = {
        'row_id': base_row['row_id'], 'reference_field': base_row.get('reference_field'),
        **_answer_view(base_answer)}
    # 8 去重
    existing = [a for a in row.get('answers') or [] if a.get('rule_key') == adm['rule_key']]
    gates['existing_same_rule_key'] = [_answer_view(a) for a in existing]
    same_rec_value = [a for a in existing
                      if a.get('record_id') == bound['skillid']
                      and a.get('raw_value') == raw]
    if same_rec_value:
        return {'accepted': False, 'rejection': 'ALREADY_PRESENT_SAME', 'gates': gates}
    if existing:
        same_value = [a for a in existing if a.get('raw_value') == raw]
        return {'accepted': False, 'rejection': 'ALREADY_ANSWERED',
                'detail': {'dedup': ('SAME_VALUE_DIFF_RECORD_EXISTING' if same_value
                                     else 'CONFLICT_EXISTING_VALUE'),
                           'existing': gates['existing_same_rule_key'],
                           'selected': {'record_id': bound['skillid'], 'raw_value': raw}},
                'gates': gates}
    return {'accepted': True, 'rejection': None, 'gates': gates, 'chain': chain,
            'bound': bound, 'params': {PARAM: raw},
            'extra_params': extra, 'base_row': base_row, 'base_answer': base_answer,
            'detail': None}


# ---------------------------------------------------------------- 答案与 marker

def _source(bound, chain, adm):
    pointer = '/bossinfo/bossskill/%d' % bound['index']
    return {
        'table': 'bossskill', 'record_id': bound['skillid'], 'layer': 'CACHE',
        'field_path': FIELD,
        'source_key': 'CACHE/bossinfo.data5.json.raw',
        'original_file': 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw',
        'json_pointer': pointer,
        'field': FIELD,
        'field_json_pointer': pointer + FIELD,
        'record_key': 'CACHE/bossinfo.data5.json.raw#%s' % pointer,
        'source_resolution': EXACT,
        'note': ('按解码 JSON 的 bossskill.skillid 唯一命中；经同卡基档行 %s（%s，pattern %s）'
                 '链内唯一 type%d 定源；本行 skilltext 只作同卡同文镜像，无独立执行链'
                 % (adm['base_row_id'], chain['pattern_pointer'], chain['pattern_id'],
                    adm['carrier_type'])),
    }


def _marker(adm, chain, bound, params, extra, gates):
    return {
        'scope': adm['scope'],
        'module': MODULE_VERSION,
        'cid': adm['cid'],
        'row_id': adm['row_id'],
        'rule_key': adm['rule_key'],
        'field_path': FIELD,
        'table': 'bossskill',
        'record_id': bound['skillid'],
        'layer': 'CACHE',
        'carrier_type': adm['carrier_type'],
        'row_tier_label': gates.get('row_tier_label'),
        'base_row_id': adm['base_row_id'],
        'base_reference_field': adm['base_ref'],
        'base_pattern_id': chain['pattern_id'],
        'base_pattern_pointer': chain['pattern_pointer'],
        'base_chain_ids': [c['skillid'] for c in chain['children']],
        'base_chain_types': [c['type'] for c in chain['children']],
        'bound_slot': bound['slot'],
        'params': params,
        'extra_params': extra,
        'same_card_base_disclosure': gates.get('same_card_base_disclosure'),
        'excluded_values': gates.get('excluded_values'),
        'same_text_tier_set': gates.get('same_text_tier_set'),
        'not_written': ('最终 HP 回复量、超上限保留比例、实际触发次数与间隔、'
                        '「全状態異常も回復」子句均不写；t27 的 p2/p3 只作字段值披露'),
        'admission': ('SAME_CARD_SAME_TEXT_BASE_TIER_DISCLOSURE_SAME_RULE_KEY_RECORD_VALUE'
                      '（同卡同文＋【共鳴必殺】档位标签＋基档行已披露同键同记录同原值；'
                      '超共鳴同文行逐行排除，不并入）'),
        'association': '推断',
        'limits': LIMIT,
    }


def build_answers(data, cid, row, res):
    import rules as R
    adm = ADMITTED[row['row_id']]
    chain, bound, params = res['chain'], res['bound'], res['params']
    ct = adm['carrier_type']
    raw = params[PARAM]
    converted = R.answer_for('bossskill', ct, FIELD, raw, bound['record'],
                             source_layer='CACHE')
    if converted is None:
        return None
    rule = R.rule_for('bossskill', ct, FIELD) or {}
    num = _num(raw)
    excluded = '；'.join('%s=%s（记录 %s）' % (e['row_id'], _num(e['raw_value']),
                                             e['record_id']) for e in adm['excluded'])
    if ct == 27:
        extra = res.get('extra_params') or {}
        p2 = extra.get('skillparam2') or {}
        p3 = extra.get('skillparam3') or {}
        value = ('镜像行（0 新增唯一数值）：同卡基档行 %s（%s / pattern %s）已披露同规则键同记录'
                 '同原值 %s；本行 skilltext 文本块标签为【共鳴必殺】（非超共鳴），按同卡同文'
                 '基础档镜像绑定到 bossskill 记录 %s 的 skillparam1=%s（周期回复输入系数）；'
                 '对象：味方全体（句面）；回复间隔字段 skillparam2=%s 游戏秒、回复次数字段 '
                 'skillparam3=%s 次（已确认字段值，不换算实机间隔）；不证明最终 HP 回复量、'
                 '超上限保留比例、实际触发间隔与次数；同文超共鳴行 %s披露、不并入（关联推断）'
                 % (adm['base_row_id'], chain['pattern_pointer'], chain['pattern_id'], num,
                    bound['skillid'], num, _num(p2.get('raw')), _num(p3.get('raw')), excluded))
    else:
        value = ('镜像行（0 新增唯一数值）：同卡基档行 %s（%s / pattern %s）已披露同规则键同记录'
                 '同原值 %s；本行 skilltext 文本块标签为【共鳴必殺】（非超共鳴），按同卡同文'
                 '基础档镜像绑定到 bossskill 记录 %s 的 skillparam1=%s（reactive heal 基值系数）；'
                 '对象：味方全体（句面）；触发：ダメージを受けるたび（句面）；不证明最终 HP '
                 '回复量、超上限保留比例、实际触发次数与间隔；同文超共鳴行 %s披露、不并入'
                 '（关联推断）'
                 % (adm['base_row_id'], chain['pattern_pointer'], chain['pattern_id'], num,
                    bound['skillid'], num, excluded))
    marker = _marker(adm, chain, bound, params, res.get('extra_params') or {}, res['gates'])
    answer = {
        'value': value,
        'quantity_kind': converted.get('quantity_kind'),
        'unit': converted.get('unit'),
        'value_text': converted.get('value_text'),
        'raw_value': raw,
        'effective_float32': _f32(raw),
        'quantitative': True,
        'numeric_source': '复用既有已确认局部规则；同卡镜像行归属为推断',
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'evidence_scope': adm['scope'],
        'answer_status': 'CONFIRMED_FORMULA_ONLY',
        'rule_key': adm['rule_key'],
        'table': 'bossskill',
        'record_id': bound['skillid'],
        'layer': 'CACHE',
        'field_path': FIELD,
        'source': _source(bound, chain, adm),
        'rule_status': rule.get('status'),
        'conversion': rule.get('conversion'),
        'base_definition': rule.get('base_definition'),
        'conditions': rule.get('applicability'),
        'rule_limits': rule.get('limits'),
        'condition_label': ('本行 skilltext 属【共鳴必殺】档；同卡基档行 %s（%s / pattern %s）'
                            '链内唯一 type%d 生效时'
                            % (adm['base_row_id'], chain['pattern_pointer'],
                               chain['pattern_id'], ct)),
        'target': '味方全体（由句面给出；rules.target 为空，受疗对象选择未复查）',
        'binding': {'c10_p1_mirror_binding': marker},
        'context': 'skilltext 基础档镜像行（t%d 回复）' % ct,
        'note': ('仅已确认静态规则下回复系数的同卡镜像实例；同卡同文＋基档披露同键同记录同原值＋'
                 '档位标签【共鳴必殺】，关联仍为推断；0 新增唯一数值。' + LIMIT),
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
    row['evidence_label'] = ('推断（C10-B1 skilltext 基础档镜像：同卡同文＋基档披露同键同记录'
                            '同原值＋【共鳴必殺】标签；0 新增唯一数值）')
    row['partial'] = True
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = list(dict.fromkeys(list(scopes) + [answers[0]['evidence_scope']]))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    binding = answers[0]['binding']['c10_p1_mirror_binding']
    reasons.append('C10-B1：skilltext 基础档镜像——同卡基档行 %s 已披露同规则键同记录同原值 '
                   'skillparam1=%s；本行按同卡同文绑定（0 新增唯一数值）；同文超共鳴行'
                   '逐行披露、不并入；同句其余机制（全状態異常も回復等）与最终 HP、'
                   '实机间隔/次数仍未验证。'
                   % (binding['base_row_id'], _num(binding['params'][PARAM])))
    row['unknown_reasons'] = list(dict.fromkeys(reasons))
    marker = row.setdefault(MARKER_KEY, dict(binding))
    marker.setdefault('bindings', [])
    for answer in answers:
        m = answer['binding']['c10_p1_mirror_binding']
        marker['bindings'].append({'rule_key': m['rule_key'], 'field_path': m['field_path'],
                                   'record_id': m['record_id'], 'params': m['params']})
    marker['bindings'] = list({(b['rule_key'], b['field_path']): b
                               for b in marker['bindings']}.values())
    return added


def _merge_disclosure(row, detail, gates):
    marker = row.setdefault(MARKER_KEY, {
        'scope': ADMITTED[row['row_id']]['scope'], 'module': MODULE_VERSION,
        'row_id': row.get('row_id'), 'bindings': []})
    marker.setdefault('disclosures', []).append({
        'dedup': detail.get('dedup'),
        'rule_key': ADMITTED[row['row_id']]['rule_key'],
        'existing': detail.get('existing'), 'selected': detail.get('selected'),
        'same_card_base_disclosure': (gates or {}).get('same_card_base_disclosure'),
        'disclosure': ('本行已有同 rule_key 答案；本批选中的记录与原值如 selected，'
                       '不新增答案、不改写既有值，只披露。'),
    })


# ---------------------------------------------------------------- 正式页消费

def apply_to_groups(data, cid, groups):
    """正式页消费：为 6 个冻结 skilltext 行写镜像绑定答案（不覆盖既有答案）。"""
    report = {'scope': 'C10_P1_SKILLTEXT_MIRROR_20261030', 'cid': cid, 'evaluated': 0,
              'answers_added': 0, 'additions': [], 'markers': [], 'rejections': [],
              'skipped_existing': 0, 'marker_only': 0, 'out_of_scope': True}
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
                _merge_disclosure(row, res.get('detail') or {}, res.get('gates'))
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
