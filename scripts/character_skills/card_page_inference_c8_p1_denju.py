# -*- coding: utf-8 -*-
"""C8-B1 传授（denju）首句伤害镜像**余量**：3 行 / 3 效果（全 Y.G.）。

任务卡 ``docs/tasks/20261030-c8-p1-throughput-package.md``；预检
``output/character_skills/c8_p1_20261030/precheck/``（``precheck_report.md`` §2.4、
``batch_plan.json``、``boundary_cases.json``、``evidence_boundaries.md``）。

为什么是这三行
--------------
C7-P3（``card_page_inference_c7_p3_denju.py``）已交付 denju 首句伤害镜像 28 行；本模块只补
其**余量**。三行都是传授（denju）原始链的**首句**、对象=敵、档位 1，且同卡基础档行
（``special_move`` 的 ``pattern0``）以**枚举前缀同文**（``【共鳴必殺/<本行标签>】+ 本行句身``）
披露了它们绑定的**同一记录同一原值**：

* 30104 ``t51 /skillparam0`` = 0.5（记录 43010400）：句面「範囲内の全ての敵に小ダメージを
  一定間隔ごとに与え…」不是 G7 形态分类里的多段/大中/一定間隔形态（现有分类器判 PLAIN），
  准入依据是**基档先例**——同卡 ``pattern0`` 的同文行已用 ``bossskill|51|/skillparam0``
  同记录同值出过 0.5（``card_page_inference_yg1_remaining_ab`` 交付，页上现存）。本模块
  因此把 t51 的准入显式记成 ``BASE_TIER_PRECEDENT_NOT_FORM_CLASSIFICATION``，不冒充形态分类。
* 30336 ``t110 /skillparam1`` = 5（记录 43033600）：句面 8回ダメージ → 多段型 105/110 且
  ``skillparam6==8`` 恰 1 条。**只绑 slot0**；同卡基档 ``slot1`` 的 t13 记录与 denju 链不同
  （43033601 vs 43033607，参数逐值相同、记录 id 不同），序列不匹配逐行披露，不据此绑增益。
* 7251 ``t105 /skillparam1`` = 0.83（记录 40725100）：句面 15回ダメージ → 链内两条 t105
  都是 ``param6==15`` 且 ``skillparam1`` 同为 0.83（记录不唯一、值唯一）。本模块**不把
  记录选取升级为唯一来源确认**：只按同卡基档首句行已有的同记录同值（40725100）取首段，
  并把「同卡 f2 既有答案用同一记录 40725100、基档 f2 用 40725101」登记为披露，不改写既有行。

与既有模块的关系（本模块不修改它们）
----------------------------------
* ``card_page_inference_c7_p3_denju``：本模块的结构域是它 28 行的**超集**（逐卡全库扫描
  实测：结构上接受 31 行 = C7-P3 已交付 28 行 + 本批 3 行）。那 28 行页上已有同 rule_key
  同记录同值答案，本模块在 R9 幂等门零写入跳过；所以**本批实际新增恰 3 行**，不会重复
  认领已交付行。
* ``card_page_inference_g1_structure``：逐字同文 R8 对 denju 行永不成立（句首标签不同），
  本模块沿用主持已裁定的**枚举前缀**口径，且明示该交叉核**只作辅助**、不作 G1 R8 主证。
* 账本沿用既有 ``binding.g1_b1_binding``（scope＝``G1_B1_MIRROR_20261029``）与
  ``effect_ledger.G1B1_RULE_EFFECT`` 的 6 个既有确认规则键；**不改**
  ``rules.json``／``rules.py``／``effect_ledger.py``。
  t51 不在那 6 键内，按同卡基档行的既有消费路径（``quantity_kind`` 词面「伤害」→
  ``ダメージ（词表外）``）被账本消费，本模块**不新增** t51 的 rule_key 映射。

判据（逐行硬门，任一不符即拒绝，不猜）
------------------------------------
R1 **行身份**：``group == denju`` 且 ``reference_field`` 以 ``denju.`` 开头；行日语片段与
   ``denju.stext`` **首句**逐字相同；``context_text`` 与 ``denju.stext`` 逐字相同。
R2 **同层**：行 ``source.layer == CACHE`` 且 ``source_key == CACHE/denju.data5.json.raw``；
   子记录只从 CACHE ``bossinfo`` 取，**本模块不读 APK 表**（``_mdBossInfo`` 同号记录不入）。
R3 **链可达且唯一**：``denju.patternid0`` 非空、在该层 ``bosspattern`` 唯一命中；
   ``pattern.sinfo`` 与 ``denju.stext`` 逐字相同；槽位从 0 连续、子记录 ``skillid``
   在本层 ``bossskill`` 唯一命中。
R4 **形态选型**：``N回ダメージ`` → 多段型 type105/110 且 ``skillparam6==N``；大/中/一定間隔
   ダメージ → 单发型 type3/22/55/74 恰 1 条；**t51 先例形态**（``小ダメージを一定間隔ごとに
   与え``）→ 链内 type51 恰 1 条，且必须过 R7 基档先例门（否则拒绝，不按形态分类放行）。
   多段命中 >1 条时：值必须唯一且同卡基档同文行已用其中**恰一条**记录出值；否则拒绝。
R5 **槽位与空值分档**：类型 → 已确认槽位（``DAMAGE_SLOT``，t51 为 ``/skillparam0``）；
   缺失/null/非有限/负值/真零各自独立拒绝。
R6 **同卡基础档**：``charainfo.pattern0`` 的 slot0 记录与本行链 slot0 **同记录**、绑定槽
   原值逐位相等；完整序列不同时只披露分歧槽（本批 30336 的 slot1 t13 记录分歧），
   **不**把分歧槽并入本行。
R7 **枚举前缀辅助交叉核**：同卡（CACHE）存在句面逐字等于
   ``【共鳴必殺/<本行句首标签>】 + 本行句身`` 的行，且该行已有
   **(rule_key, 选中记录 id, 原值)** 三重相等的答案（缺 → ``NO_ENUM_PREFIX_CORROBORATION``，
   同键同记录异值 → ``ENUM_PREFIX_VALUE_CONFLICT``）。剥句首【…】的宽松匹配只作敏感性披露
   （R7b），不作准入——30102 即在此门拒绝（基档标签多一个「無敵」）。
R8 **排除分支**：``charainfo.pattern1..4`` 中含「超共鳴」的 pattern，其 slot0 同类型记录必须
   存在且原值与本行不同（不同值才登记为排除分支）。
R9 **幂等与去重**：本行已有同 rule_key 答案时——同记录同值 → 幂等跳过（零写入）；
   同值异记录 → 只写行级披露；同键异值 → 不新增、不改写，只披露。30236／30239 零触碰。

证据分档（不得升格）
--------------------
R1–R3、R5 的槽位、R6 是结构/类型证据；R4 的「N回 ↔ param6」「大/中/一定間隔 ↔ 单发型」是
类型语义＋一致性推断；t51 的准入是**基档先例**（同卡已披露的同记录同值），不是形态分类；
R7 是**同卡枚举前缀辅助交叉核**（主持裁定不作主证）。故答案
``association_evidence = 推断``、``evidence_scope = BY_TYPE_EXTRAPOLATED``、不写最终扣血。
"""
from __future__ import annotations

import json
import math
import re
import struct
import unicodedata
from pathlib import Path

MODULE_VERSION = 'c8_p1_denju_mirror_20261030'
#: 账本消费用 scope：沿用既有 G1-B1 来源限定映射（effect_ledger.G1B1_SCOPE）。
SCOPE = 'G1_B1_MIRROR_20261029'
#: 本批结构判定自身的 marker scope。
STRUCTURE_SCOPE = 'C8_P1_DENJU_MIRROR_20261030'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'

#: 类型 → 已确认规则键的伤害槽（逐键取自 profiles/rules.json，本批不新增键）。
#: t51 的 /skillparam0 来自 rules.json 既有键（rules 294 键之一），槽位见该键 base_definition。
DAMAGE_SLOT = {3: 'skillparam1', 22: 'skillparam1', 51: 'skillparam0',
               55: 'skillparam1', 74: 'skillparam5', 105: 'skillparam1',
               110: 'skillparam1'}
SINGLE_TYPES = (3, 22, 55, 74)
MULTI_TYPES = (105, 110)
PRECEDENT_TYPE = 51

#: effect_ledger.G1B1_RULE_EFFECT 覆盖的 6 键（t51 不在内：按既有 quantity_kind 词面消费）。
LEDGER_MAPPED_RULE_KEYS = frozenset({
    'bossskill|3|/skillparam1', 'bossskill|22|/skillparam1',
    'bossskill|55|/skillparam1', 'bossskill|74|/skillparam5',
    'bossskill|105|/skillparam1', 'bossskill|110|/skillparam1'})

#: 保护卡：30236 / 30239 G0 豁免不扩大（任务卡 §2 保护项）。
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

MULTIHIT_RX = re.compile(r'(\d+)回ダメージ')
BIGMID_RX = re.compile(r'(?:大|中)ダメージ')
INTERVAL_RX = re.compile(r'一定間隔でダメージ')
#: t51 先例形态：句面点名的周期小伤害（不是 G7 形态分类的类目）。
T51_PRECEDENT_RX = re.compile(r'小ダメージを一定間隔ごとに与え')
RECEIVE_MARKS = ('受ける', '受け', '味方')
MODIFIER_MARKS = ('ダメージが上がる', 'ダメージが下がる', 'ダメージが増', 'ダメージが減')
TAG_RX = re.compile(r'^(?:【[^】]*】)+')
FIRST_TAG_RX = re.compile(r'^【([^】]*)】')

#: 行级 marker 键（不覆盖其他批次键）。
MARKER_KEY = 'inference_c8_p1_denju'

#: 与 G1/C7-P3 同一处「未知原因」清理口径（本模块覆盖伤害子句后这些理由失效）。
_STALE_REASONS = {
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应',
}

_BOSSINFO_CACHE = {}


# ---------------------------------------------------------------- 纯函数

def canon(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def canon_no_tag(text):
    """剥离句首【…】后的规范文本（只用于 R7b 敏感性披露，不作准入判据）。"""
    return TAG_RX.sub('', canon(text))


def first_tag(japanese):
    m = FIRST_TAG_RX.match(str(japanese or ''))
    return m.group(1) if m else None


def classify_clause(japanese):
    """片段 → 伤害子句形态 ∈ {MULTIHIT, BIGMID, INTERVAL, T51_PRECEDENT, PLAIN, None}。"""
    text = str(japanese or '')
    if 'ダメージ' not in text:
        return None, {'reason': 'NO_DAMAGE_WORD'}
    for mark in MODIFIER_MARKS:
        if mark in text:
            return None, {'reason': 'DAMAGE_MODIFIER_NOT_INSTANCE', 'mark': mark}
    for mark in RECEIVE_MARKS:
        if mark in text:
            return None, {'reason': 'DAMAGE_RECEIVER_NOT_ENEMY', 'mark': mark}
    if '敵' not in text:
        return None, {'reason': 'NO_ENEMY_TARGET'}
    m = MULTIHIT_RX.search(text)
    if m:
        return 'MULTIHIT', {'n': int(m.group(1)), 'clause': m.group(0)}
    m = BIGMID_RX.search(text)
    if m:
        return 'BIGMID', {'clause': m.group(0)}
    m = INTERVAL_RX.search(text)
    if m:
        return 'INTERVAL', {'clause': m.group(0)}
    m = T51_PRECEDENT_RX.search(text)
    if m:
        return 'T51_PRECEDENT', {'clause': m.group(0),
                                 'note': 't51 的准入依据是基档先例，不是 G7 形态分类'}
    return 'PLAIN', {'reason': 'DAMAGE_WITHOUT_QUALIFIER'}


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


def f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def _num_text(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return ('%.6f' % f).rstrip('0').rstrip('.')


def is_denju_row(group, reference_field):
    return group == 'denju' and str(reference_field or '').startswith('denju.')


# ---------------------------------------------------------------- 记录读取（层显式）

def _bossinfo(root):
    """CACHE bossinfo 的 pattern/skill 索引（只读；本模块不读 APK 表）。"""
    key = str(Path(root).resolve())
    if key not in _BOSSINFO_CACHE:
        path = Path(root) / 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw'
        doc = json.loads(path.read_text(encoding='utf-8-sig'))['bossinfo']
        patterns, skills = {}, {}
        for i, rec in enumerate(doc.get('bosspattern') or []):
            patterns.setdefault(rec.get('patternid'), []).append((i, rec))
        for i, rec in enumerate(doc.get('bossskill') or []):
            skills.setdefault(rec.get('skillid'), []).append((i, rec))
        _BOSSINFO_CACHE[key] = dict(patterns=patterns, skills=skills,
                                    skills_all=doc.get('bossskill') or [])
    return _BOSSINFO_CACHE[key]


def _records(data, cid, group, table):
    for g in (data.links.get(cid) or {}).get('groups') or []:
        if g.get('group') != group:
            continue
        for entry in g.get('records') or []:
            if entry.get('table') == table:
                yield entry


def resolve_parent(data, cid):
    """R1/R2：denju 父记录 + pattern 指针（都在本行层）。"""
    rec = next(iter(_records(data, cid, 'denju', 'denju')), None)
    if rec is None:
        return None, 'DENJU_RECORD_MISSING'
    record = rec.get('record') or {}
    pid, text = record.get('patternid0'), record.get('stext')
    if pid is None:
        return None, 'PATTERN_POINTER_MISSING'
    if not text:
        return None, 'PARENT_TEXT_MISSING'
    return {'record': record, 'table': 'denju', 'pointer': 'denju.patternid0',
            'pattern_id': pid, 'text': text, 'layer': 'CACHE', 'entry': rec}, None


def children_of(root, pattern_id):
    """R3：pattern.skillid0..6 → bossskill（同层）。"""
    raw = _bossinfo(root)
    hit = raw['patterns'].get(pattern_id) or []
    if len(hit) != 1:
        return None, None, None, len(hit)
    index, pattern = hit[0]
    children = []
    for slot in range(7):
        sid = pattern.get('skillid%d' % slot)
        if not sid:
            continue
        sh = raw['skills'].get(sid) or []
        if len(sh) != 1:
            children.append({'slot': slot, 'skillid': sid, 'missing': True,
                             'hits': len(sh)})
            continue
        k_index, record = sh[0]
        children.append({'slot': slot, 'skillid': sid, 'index': k_index, 'record': record,
                         'type': record.get('skillid0'),
                         'params': {k: v for k, v in record.items()
                                    if k.startswith('skillparam')}})
    return index, pattern, children, 1


def select_child(children, form, detail):
    """R4：形态 → 子记录（唯一）；t51 先例形态留给 R7 再判。"""
    if form == 'MULTIHIT':
        n = detail['n']
        typed = [c for c in children if c.get('type') in MULTI_TYPES]
        hits = [c for c in typed if c['params'].get('skillparam6') == n]
        if not hits:
            return None, {'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed),
                          'rejection': 'NO_MULTIHIT_PARAM6_MATCH'}
        if len(hits) > 1:
            values = {c['params'].get('skillparam1') for c in hits}
            if len(values) > 1:
                return None, {'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed),
                              'records': sorted(c['skillid'] for c in hits),
                              'rejection': 'MULTI_MULTIHIT_DIFF_VALUES'}
            return None, {'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed),
                          'records': sorted(c['skillid'] for c in hits),
                          'candidates': hits,
                          'rejection': 'MULTI_MULTIHIT_NOT_UNIQUE'}
        return hits[0], {
            'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed), 'param6': n,
            'records': [c['skillid'] for c in hits],
            'record_note': 'RECORD_UNIQUE',
            'basis': '句面 N回ダメージ ↔ 多段型 type105/110 且 skillparam6==N'}
    if form == 'T51_PRECEDENT':
        typed = [c for c in children if c.get('type') == PRECEDENT_TYPE]
        if len(typed) != 1:
            return None, {'mode': 'T51_PRECEDENT', 'n_typed': len(typed),
                          'records': [c['skillid'] for c in typed],
                          'rejection': ('NO_T51_CARRIER' if not typed
                                        else 'MULTI_T51_AMBIGUOUS')}
        return typed[0], {'mode': 'T51_PRECEDENT', 'n_typed': 1,
                          'records': [typed[0]['skillid']],
                          'record_note': 'RECORD_UNIQUE',
                          'basis': ('句面「小ダメージを一定間隔ごとに与え」＋链内 type51 恰 1 条；'
                                    '准入另需 R7 基档先例（不作形态分类放行）')}
    typed = [c for c in children if c.get('type') in SINGLE_TYPES]
    if not typed:
        return None, {'mode': 'SINGLE', 'n_typed': 0, 'rejection': 'NO_SINGLE_TYPE_CARRIER'}
    if len(typed) > 1:
        return None, {'mode': 'SINGLE', 'n_typed': len(typed),
                      'records': [c['skillid'] for c in typed],
                      'rejection': 'MULTI_SINGLE_TYPE_AMBIGUOUS'}
    return typed[0], {'mode': 'SINGLE', 'n_typed': 1, 'records': [typed[0]['skillid']],
                      'record_note': 'RECORD_UNIQUE',
                      'basis': '句面 大/中ダメージ・一定間隔でダメージ ↔ 单发型 type3/22/55/74 恰 1 条'}


def _same_signature_count(tab, record):
    """同签名（全部 skillparam* 键值）的同类型记录数（同值异记录披露；不按值配对）。"""
    bound_type = record.get('skillid0')
    sig = {k: v for k, v in record.items() if k.startswith('skillparam')}
    return sum(1 for rec in tab['skills_all']
               if rec.get('skillid0') == bound_type
               and {k: v for k, v in rec.items() if k.startswith('skillparam')} == sig)


def base_tier_of(root, charainfo, chain):
    """R6：charainfo.pattern0 的槽序列与本行链逐位对照（只读）。"""
    out = {'chara_present': charainfo is not None}
    if charainfo is None:
        return out
    pid = charainfo.get('pattern0')
    out['pattern0'] = pid
    raw = _bossinfo(root)
    hit = raw['patterns'].get(pid) if pid else None
    if not hit or len(hit) != 1:
        out['unique'] = False
        return out
    out['unique'] = True
    pattern = hit[0][1]
    ids = [pattern.get('skillid%d' % s) for s in range(len(chain['children']))]
    out['ids'] = ids
    out['same_sequence'] = ids == [c['skillid'] for c in chain['children']]
    out['same_slot0'] = bool(ids) and ids[0] == chain['children'][0]['skillid']
    out['divergent_slots'] = [
        {'slot': 'skillid%d' % i, 'chain': chain['children'][i]['skillid'],
         'base_tier': ids[i],
         'chain_params': chain['children'][i]['params'],
         'base_tier_params': {k: v for k, v in
                              (next((r for idx, r in raw['skills'].get(ids[i]) or []), {}) or {}).items()
                              if k.startswith('skillparam')}}
        for i in range(min(len(ids), len(chain['children'])))
        if ids[i] != chain['children'][i]['skillid']]
    out['chara_params'] = {k: v for k, v in charainfo.items() if k.startswith('skillparam')}
    out['sinfo'] = pattern.get('sinfo')
    return out


def super_tiers_of(root, charainfo, bound_type):
    """R8：``charainfo.pattern1..4`` 中含「超共鳴」的 pattern 的 slot0（同类型）。"""
    out = []
    raw = _bossinfo(root)
    for i in range(1, 5):
        pid = (charainfo or {}).get('pattern%d' % i)
        if not pid:
            continue
        hit = raw['patterns'].get(pid) or []
        if len(hit) != 1:
            continue
        pattern = hit[0][1]
        sinfo = str(pattern.get('sinfo') or '')
        if '超共鳴' not in sinfo:
            continue
        sid = pattern.get('skillid0')
        sh = raw['skills'].get(sid) or []
        if len(sh) != 1:
            continue
        rec = sh[0][1]
        if rec.get('skillid0') != bound_type:
            continue
        out.append({'pointer': 'charainfo.pattern%d' % i, 'pattern_id': pid,
                    'record_id': sid, 'type': rec.get('skillid0'),
                    'params': {k: v for k, v in rec.items() if k.startswith('skillparam')},
                    'clause': sinfo[:120]})
    return out


# ---------------------------------------------------------------- 单行判定

def evaluate(data, cid, row, rows=None, tab=None):
    """单行判定（不写入）。``rows`` 为同卡全部行（R7 交叉核）。"""
    out = {'cid': cid, 'row_id': row.get('row_id'), 'kind': 'DENJU', 'rules': {},
           'rejection': None, 'selected': None, 'gates': {}}
    if cid in ZERO_TOUCH_CIDS:
        out['rejection'] = 'ZERO_TOUCH_CID'
        return out
    if not is_denju_row(row.get('_group'), row.get('reference_field')):
        out['rejection'] = 'NOT_A_DENJU_ROW'
        return out
    # R2 同层
    src = row.get('source') or {}
    out['rules']['R2_layer'] = {'layer': src.get('layer'), 'source_key': src.get('source_key')}
    if src.get('layer') != 'CACHE' or src.get('source_key') != 'CACHE/denju.data5.json.raw':
        out['rejection'] = 'LAYER_NOT_ESTABLISHED_APK'
        return out
    # R1 行身份
    parent, err = resolve_parent(data, cid)
    if err:
        out['rejection'] = err
        return out
    stext = str(parent['text'])
    first = stext.split('。')[0] + '。'
    first_ok = canon(first) == canon(row.get('japanese'))
    ctx_ok = canon(row.get('context_text')) == canon(stext)
    out['rules']['R1_identity'] = {'first_sentence': first_ok, 'context_text_eq_stext': ctx_ok,
                                   'pointer': parent['pointer'],
                                   'pattern_id': parent['pattern_id']}
    if not ctx_ok or not first_ok:
        out['rejection'] = 'ROW_TEXT_NOT_FIRST_SENTENCE' if not first_ok else 'CONTEXT_TEXT_MISMATCH'
        return out
    # R3 链
    p_index, pattern, children, pattern_hits = children_of(data.root, parent['pattern_id'])
    if pattern is None:
        out['rejection'] = 'BOSSPATTERN_NOT_UNIQUE(%d)' % pattern_hits
        return out
    sinfo = pattern.get('sinfo')
    out['rules']['R3_text'] = {'pattern_index': p_index, 'sinfo_present': bool(sinfo),
                               'sinfo_equals_parent_text': canon(sinfo) == canon(stext)}
    if not sinfo:
        out['rejection'] = 'PATTERN_SINFO_MISSING'
        return out
    if canon(sinfo) != canon(stext):
        out['rejection'] = 'PARENT_TEXT_NOT_PATTERN_SINFO'
        return out
    if any(c.get('missing') for c in children):
        out['rejection'] = 'CHILD_RECORD_MISSING'
        return out
    if [c['slot'] for c in children] != list(range(len(children))):
        out['rejection'] = 'SLOT_NOT_CONTIGUOUS'
        return out
    out['gates']['children'] = [{'skillid': c['skillid'], 'type': c.get('type')}
                                for c in children]
    # R4 形态选型
    form, detail = classify_clause(row.get('japanese'))
    out['rules']['R4_clause'] = {'form': form, **detail}
    if form is None:
        out['rejection'] = detail.get('reason') or 'NO_DAMAGE_CLAUSE'
        return out
    if form == 'PLAIN':
        out['rejection'] = 'DAMAGE_WITHOUT_QUALIFIER'
        return out
    chosen, sel = select_child(children, form, detail)
    out['rules']['R4b_select'] = sel
    hits = []
    if chosen is None:
        hits = sel.get('candidates') or []
        if sel.get('rejection') != 'MULTI_MULTIHIT_NOT_UNIQUE' or not hits:
            out['rejection'] = sel.get('rejection')
            return out
        # 多段命中不唯一：留给 R7 用同卡基档同文行的已用记录定首段（只在该记录恰一条时放行）。
    # R5 槽位与空值分档（多条候选时要求全部同槽同值，否则不按值任取）
    probe = chosen if chosen is not None else hits[0]
    slot = DAMAGE_SLOT.get(probe.get('type'))
    present = slot is not None and slot in probe['params']
    raw = probe['params'].get(slot) if slot else None
    state = raw_state(raw, present)
    if hits and any(slot not in c['params'] or c['params'].get(slot) != raw for c in hits):
        out['rejection'] = 'MULTI_MULTIHIT_SLOT_NOT_IDENTICAL'
        return out
    out['rules']['R5_slot'] = {'type': probe.get('type'), 'slot': slot, 'raw': raw,
                               'present': present, 'raw_state': state}
    if slot is None:
        out['rejection'] = 'TYPE_WITHOUT_DAMAGE_RULE'
        return out
    for verdict, code in (('MISSING', 'RAW_VALUE_MISSING'), ('NULL', 'RAW_VALUE_NULL'),
                          ('NON_FINITE', 'RAW_VALUE_NON_FINITE'),
                          ('NEGATIVE', 'RAW_VALUE_NEGATIVE'), ('ZERO', 'RAW_VALUE_ZERO')):
        if state == verdict:
            out['rejection'] = code
            return out
    rule_key = 'bossskill|%d|/%s' % (probe['type'], slot)
    # R6 同卡基础档
    charainfo = (getattr(data, 'cache_chara', None) or {}).get(cid) or {}
    base_tier = base_tier_of(data.root, charainfo, {'children': children})
    out['rules']['R6_base_tier'] = {k: v for k, v in base_tier.items() if k != 'chara_params'}
    if not base_tier.get('chara_present') or not base_tier.get('unique'):
        out['rejection'] = 'BASE_TIER_MISSING'
        return out
    if not base_tier.get('same_slot0'):
        out['rejection'] = 'BASE_TIER_SLOT0_RECORD_MISMATCH'
        return out
    if charainfo.get(slot) != raw:
        out['rejection'] = 'CHARAINFO_SLOT_MISMATCH'
        return out
    divergent = base_tier.get('divergent_slots') or []
    if divergent and any(d['slot'] == 'skillid0' for d in divergent):
        out['rejection'] = 'BASE_TIER_SEQUENCE_MISMATCH'
        return out
    # R7 枚举前缀辅助交叉核（同卡、CACHE、逐字句面）
    dtag = first_tag(row.get('japanese'))
    if dtag is None:
        out['rejection'] = 'ROW_TAG_MISSING'
        return out
    target = canon('【共鳴必殺/%s】' % dtag) + canon_no_tag(row.get('japanese'))
    body = canon_no_tag(row.get('japanese'))
    enum_rows, super_rows, relaxed_rows = [], [], []
    for other in rows or []:
        if other.get('row_id') == row.get('row_id'):
            continue
        ja = canon(other.get('japanese'))
        if canon_no_tag(other.get('japanese')) == body:
            relaxed_rows.append(other.get('row_id'))
        if ja == target:
            enum_rows.append(other)
        elif ja.startswith(canon('【超共鳴必殺/%s】' % dtag)):
            super_rows.append(other)
    enum_items, enum_cache_rows, enum_off_layer = [], [], []
    for other in enum_rows:
        s2 = other.get('source') or {}
        items = [{'rule_key': a.get('rule_key'), 'record_id': a.get('record_id'),
                  'raw_value': a.get('raw_value'), 'peer': other.get('row_id')}
                 for a in other.get('answers') or []]
        if s2.get('layer') == 'CACHE':
            enum_items.extend(items)
            enum_cache_rows.append(other.get('row_id'))
        else:
            enum_off_layer.append(other.get('row_id'))
    hits = hits if hits else [chosen]
    corrobor = [a for a in enum_items
                if a['rule_key'] == rule_key and a['raw_value'] == raw
                and any(a['record_id'] == c['skillid'] for c in hits)]
    conflicts = [a for a in enum_items
                 if a['rule_key'] == rule_key and a['raw_value'] != raw
                 and any(a['record_id'] == c['skillid'] for c in hits)]
    same_key_other_records = [a for a in enum_items
                              if a['rule_key'] == rule_key
                              and not any(a['record_id'] == c['skillid'] for c in hits)]
    out['rules']['R7_enum_cross'] = {
        'enum_prefix': '【共鳴必殺/%s】' % dtag,
        'enum_peers': enum_cache_rows,
        'enum_peers_off_layer': enum_off_layer,
        'record_and_value_matches': corrobor,
        'conflicts': conflicts,
        'same_key_other_records': same_key_other_records,
        'role': 'AUXILIARY_CORROBORATION（t51 时同时是准入先例；不作 G1 R8 主证）',
    }
    out['rules']['R7b_tag_normalized'] = {
        'rows': sorted(set(relaxed_rows)),
        'note': '剥离句首【…】后的同文匹配只作敏感性披露，未作为准入判据',
    }
    if conflicts:
        out['rejection'] = 'ENUM_PREFIX_VALUE_CONFLICT'
        return out
    if not corrobor:
        out['rejection'] = 'NO_ENUM_PREFIX_CORROBORATION'
        return out
    if chosen is None:
        # 多段命中不唯一：只按先例命中的那一条记录放行，且不升级为唯一来源确认。
        got = {a['record_id'] for a in corrobor}
        if len(got) != 1:
            out['rejection'] = 'MULTI_MULTIHIT_PRECEDENT_NOT_SINGLE'
            return out
        chosen = next(c for c in hits if c['skillid'] in got)
        sel = dict(sel, record_note='VALUE_UNIQUE_RECORD_NOT_UNIQUE',
                   record_resolution='BASE_TIER_SENTENCE_ORDER_PRECEDENT',
                   record_resolution_note=('链内多条同 param6 记录且值相同；记录选取不唯一，'
                                           '按同卡基档同文行已用记录定首段；不升级为唯一来源确认'))
        out['rules']['R4b_select'] = sel
    out['selected'] = {'skillid': chosen['skillid'], 'type': chosen['type'],
                       'slot': '/' + slot, 'raw': raw, 'raw_state': state,
                       'rule_key': rule_key, 'record_index': chosen['index'],
                       'selection': sel,
                       'admission_basis': ('BASE_TIER_PRECEDENT_NOT_FORM_CLASSIFICATION'
                                           if chosen['type'] == PRECEDENT_TYPE
                                           else 'FORM_CLASSIFICATION')}
    # R8 排除分支
    supers = super_tiers_of(data.root, charainfo, chosen['type'])
    out['rules']['R8_super_tier'] = supers
    if not supers:
        out['rejection'] = 'SUPER_TIER_NOT_FOUND'
        return out
    distinct = [s for s in supers if s['params'].get(slot) != raw]
    if not distinct:
        out['rejection'] = 'SEGMENTS_INDISTINCT'
        return out
    out['gates']['excluded_values'] = [[s['record_id'], s['params'].get(slot)] for s in distinct]
    out['gates']['excluded_rows'] = [s['pointer'] for s in supers]
    out['parent'] = {'table': parent['table'], 'pointer': parent['pointer'],
                     'pattern_id': parent['pattern_id'], 'entry': parent['entry'],
                     'record': parent['record']}
    out['pattern_record'] = pattern
    out['chosen_record'] = chosen['record']
    out['verdict'] = 'VALUE_AND_BINDING'
    return out


# ---------------------------------------------------------------- 答案与 marker

def _source_of(chosen, slot, pattern_pointer):
    record_key = 'CACHE/bossinfo.data5.json.raw#/bossinfo/bossskill/%d' % chosen['index']
    return {
        'table': 'bossskill', 'record_id': chosen['skillid'], 'layer': 'CACHE',
        'field_path': '/' + slot,
        'source_key': 'CACHE/bossinfo.data5.json.raw',
        'original_file': 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw',
        'json_pointer': '/bossinfo/bossskill/%d' % chosen['index'],
        'field': '/' + slot,
        'field_json_pointer': '/bossinfo/bossskill/%d/%s' % (chosen['index'], slot),
        'record_key': record_key,
        'source_resolution': EXACT,
        'note': ('按解码 JSON 的 bossskill.skillid 唯一命中；本行原始链（%s）定源，'
                 '不是同文复制' % pattern_pointer),
    }


def _answer(res, base_row_ids, excluded, same_value_existing):
    selected = res['selected']
    slot, raw, rid = selected['slot'], selected['raw'], selected['skillid']
    rule_key = selected['rule_key']
    chosen = {'skillid': rid, 'index': selected['record_index'], 'type': selected['type'],
              'record': res['chosen_record']}
    source = _source_of(chosen, slot[1:], res['parent']['pointer'])
    pattern = res['pattern_record']
    num = _num_text(raw)
    qk = ('直接范围伤害输入倍率' if selected['type'] == 74
          else '激光伤害输入倍率' if selected['type'] == 55
          else '单次对敌伤害输入倍率')
    base_ids = '、'.join(base_row_ids) or '（无）'
    if excluded:
        exc_txt = '、'.join('%s（%s）' % (_num_text(v), r) for r, v in excluded)
        exc_tail = '超共鳴档位值 %s已排除、不计入本行' % exc_txt
    else:
        exc_tail = '本档无链外档位值'
    note_unique = ''
    if (selected.get('selection') or {}).get('record_note') == 'VALUE_UNIQUE_RECORD_NOT_UNIQUE':
        note_unique = '；同值异记录：%s 均为 %s（记录选取不唯一，按同卡基档句序定首段；' \
                      '不升级为唯一来源确认）' % (
                          '/'.join(str(c) for c in (selected.get('selection') or {}).get('records') or []),
                          num)
    admission = selected.get('admission_basis')
    adm_txt = ('；准入依据＝基档先例（同卡同文基档行已用同记录同值），非 G7 形态分类'
               if admission == 'BASE_TIER_PRECEDENT_NOT_FORM_CLASSIFICATION' else '')
    value = ('%s：%s（相对B；对象：敌方；镜像行按 denju 原始链定源到 bossskill %s type%s %s；'
             '同规则键同记录同原值已在同卡基档行 %s 披露；%s%s%s）'
             % (qk, num, rid, selected['type'], slot, base_ids, exc_tail, note_unique, adm_txt))
    conditions_raw = {k: pattern.get(k) for k in
                      ('flag', 'hpend', 'priority', 'scost', 'sname',
                       'skillid0', 'skillid1', 'skillid2', 'skillid3')
                      if pattern.get(k) is not None}
    conditions_raw['sinfo'] = pattern.get('sinfo')
    marker = {
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'gate': 'denju.patternid0',
        'row_id': res['row_id'],
        'rule_key': rule_key,
        'record_id': rid,
        'layer': 'CACHE',
        'field_path': slot,
        'pattern_id': res['parent']['pattern_id'],
        'pattern_slot': res['parent']['pointer'],
        'origin': {'kind': 'DENJU', 'record_table': 'denju',
                   'patternid0': res['parent']['pattern_id'],
                   'denju_pointer': (res['parent']['entry'].get('source') or {}).get('json_pointer')},
        'selection': selected.get('selection'),
        'base_row_ids': base_row_ids,
        'record_selection': (selected.get('selection') or {}).get('record_note') or 'RECORD_UNIQUE',
        'excluded_values': [[r, v] for r, v in excluded],
        'excluded_rows': res['gates'].get('excluded_rows'),
        'value_basis': ('同值已在同卡基档行同 rule_key 答案中披露；本行只做行级绑定，'
                        '不新增唯一数值'),
        'admission_basis': admission,
        'same_value_existing_answers': same_value_existing,
        'enum_prefix_cross_check': res['rules'].get('R7_enum_cross'),
        'same_key_base_answers': (res['rules'].get('R7_enum_cross') or {})
        .get('same_key_other_records'),
        'same_value_other_records': {
            'signature': {k: v for k, v in res['chosen_record'].items()
                          if k.startswith('skillparam')},
            'count': _same_signature_count(_bossinfo(res['_root']), res['chosen_record']),
            'note': '同值异记录：按记录 id 绑定，不按值配对',
        },
        'r8b_tag_normalized': res['rules'].get('R7b_tag_normalized'),
        'association': '推断',
        'cross_check_role': 'AUXILIARY_CORROBORATION_NOT_PRIMARY',
        'native_evidence': ('none（本批不新增原生点；片段判别为类型语义＋一致性推断；'
                            't51 准入为基档先例；枚举前缀交叉核只作辅助核）'),
        'conditions_raw': conditions_raw,
    }
    return {
        'value': value,
        'quantity_kind': qk,
        'unit': '倍率（相对B）',
        'raw_value': raw,
        'effective_float32': f32(raw),
        'quantitative': True,
        'numeric_source': '原生静态及受控局部规则＋实际父子边',
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'answer_status': 'CONFIRMED_FORMULA_ONLY',
        'evidence_scope': 'BY_TYPE_EXTRAPOLATED',
        'rule_key': rule_key,
        'field_path': slot,
        'table': 'bossskill',
        'record_id': rid,
        'layer': 'CACHE',
        'source': source,
        'context': '镜像段（传授行）',
        'condition_label': 'patternid0 / pattern %s 被选中时' % res['parent']['pattern_id'],
        'binding': {
            'g1_b1_binding': marker,
            'c8_p1_denju_binding': {
                'scope': STRUCTURE_SCOPE,
                'module': MODULE_VERSION,
                'verdict': res['verdict'],
                'dedup': 'NEW_ANSWER_NO_EXISTING_RULE_KEY',
                'admission_basis': admission,
                'base_tier_sequence_equal': res['rules'].get('R6_base_tier', {})
                .get('same_sequence'),
                'base_tier_divergent_slots': res['rules'].get('R6_base_tier', {})
                .get('divergent_slots'),
                'record_selection': (selected.get('selection') or {}).get('record_note'),
            },
        },
        'target': '敌',
        'note': ('仅局部伤害输入公式（B=getBasicSkillAttack(true) 等沿用原规则定义），未验证'
                 '最终扣血、保证命中与运行时选档；抽取自本行 denju 原始链记录，非最终伤害。'
                 '同卡基档句面＝共鳴必殺/＋本行标签的枚举前缀只作辅助交叉核（t51 时同时是准入'
                 '先例，不作 G1 R8 主证），超共鳴档位值已登记排除。结构判定规则见 '
                 'card_page_inference_c8_p1_denju.py 模块头注 R1–R9。'),
        'evidence': ['docs/tasks/20261030-c8-p1-throughput-package.md',
                     'output/character_skills/c8_p1_20261030/precheck/precheck_report.md',
                     'output/character_skills/c7_p3_20261030/precheck/precheck_report.md'],
    }


def _append(row, answer, res, dedup):
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    if any(key(a) == key(answer) for a in row.get('answers') or []):
        return False
    row.setdefault('answers', []).append(answer)
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = ('推断（C8-B1 传授伤害镜像余量绑定：denju 原始链定源；'
                             '倍率见同卡基档位行，不新增唯一数值）')
    row['partial'] = True
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    row['evidence_scope'] = list(dict.fromkeys(list(row.get('evidence_scope') or [])
                                              + ['BY_TYPE_EXTRAPOLATED']))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    reasons.append('C8-B1：本行首句伤害子句已按 denju 原始链首段绑定倍率（同卡基档行同记录'
                   '同值、超共鳴档位值已排除%s）；同句其余机制仍按原状登记，账本行仍为拆分待核查。'
                   % ('；t51 准入为基档先例' if res['selected']['type'] == PRECEDENT_TYPE else ''))
    row['unknown_reasons'] = reasons
    row[MARKER_KEY] = _row_marker(res, dedup)
    return True


def _row_marker(res, dedup, extra=None):
    selected = res.get('selected') or {}
    marker = {
        'scope': STRUCTURE_SCOPE,
        'ledger_scope': SCOPE,
        'module': MODULE_VERSION,
        'row_id': res['row_id'],
        'kind': res['kind'],
        'layer': 'CACHE',
        'verdict': res.get('verdict'),
        'dedup': dedup,
        'rule_key': selected.get('rule_key'),
        'record_id': selected.get('skillid'),
        'field_path': selected.get('slot'),
        'raw_value': selected.get('raw'),
        'raw_state': selected.get('raw_state'),
        'admission_basis': selected.get('admission_basis'),
        'pattern_id': (res.get('parent') or {}).get('pattern_id'),
        'structure': {k: v for k, v in (res.get('rules') or {}).items()
                      if k in ('R4_clause', 'R4b_select', 'R5_slot', 'R6_base_tier')},
        'enum_prefix_cross_check': res.get('rules', {}).get('R7_enum_cross'),
        'r8b_tag_normalized': res.get('rules', {}).get('R7b_tag_normalized'),
        'super_tier': res.get('rules', {}).get('R8_super_tier'),
        'excluded_values': (res.get('gates') or {}).get('excluded_values'),
        'note': ('结构判定 marker：不新增/不改写答案时也保留判定与披露；'
                 '枚举前缀交叉核只作辅助核（t51 时同时是准入先例）；归属仍为推断。'),
    }
    if extra:
        marker.update(extra)
    return marker


def _merge_marker(row, marker):
    existing = row.get(MARKER_KEY)
    if isinstance(existing, dict):
        for k, v in marker.items():
            if k in ('structure', 'enum_prefix_cross_check', 'r8b_tag_normalized',
                     'super_tier') and isinstance(existing.get(k), dict):
                continue
            existing.setdefault(k, v)
        existing['dedup'] = marker.get('dedup')
        for k in ('existing_answers', 'disclosure'):
            if k in marker:
                existing[k] = marker[k]
        return existing
    row[MARKER_KEY] = marker
    return marker


# ---------------------------------------------------------------- 正式页消费

def apply_to_groups(data, cid, groups):
    """正式页消费：为 denju 伤害镜像余量行写入绑定答案或行级 marker（不覆盖既有答案）。"""
    report = {'scope': STRUCTURE_SCOPE, 'cid': cid, 'evaluated': 0, 'answers_added': 0,
              'marker_only': 0, 'skipped_existing': 0,
              'additions': [], 'markers': [], 'rejections': [], 'out_of_scope': True}
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append({'reason': 'ZERO_TOUCH_CID', 'cid': cid})
        return report
    rows = [(g.get('group'), s, r) for g in groups or [] for s in g.get('skills') or []
            for r in s.get('rows') or []]
    mirrors = [(gn, s, r) for gn, s, r in rows if is_denju_row(gn, r.get('reference_field'))]
    if not mirrors:
        return report
    report['out_of_scope'] = False
    all_rows = [r for _gn, _s, r in rows]
    for gn, s, r in mirrors:
        if s.get('layer') != 'CACHE':
            report['rejections'].append({'row_id': r.get('row_id'),
                                         'reason': 'LAYER_NOT_ESTABLISHED_APK'})
            continue
        row = dict(r)
        row['_group'] = gn
        res = evaluate(data, cid, row, rows=all_rows)
        report['evaluated'] += 1
        if res['rejection']:
            report['rejections'].append({'row_id': r.get('row_id'), 'reason': res['rejection']})
            continue
        if res.get('selected') is None:
            continue
        selected = res['selected']
        rule_key = selected['rule_key']
        same_key = [a for a in r.get('answers') or [] if a.get('rule_key') == rule_key]
        same_rec_value = [a for a in same_key
                          if a.get('record_id') == selected['skillid']
                          and a.get('raw_value') == selected['raw']]
        same_value = [a for a in same_key if a.get('raw_value') == selected['raw']]
        excluded = sorted({(e[0], e[1]) for e in res['gates'].get('excluded_values') or []})
        existing = [{'record_id': a.get('record_id'), 'raw_value': a.get('raw_value'),
                     'rule_key': a.get('rule_key')} for a in same_key]
        if same_rec_value:
            report['skipped_existing'] += 1
            report['markers'].append({'row_id': r.get('row_id'),
                                      'dedup': 'ALREADY_PRESENT_SAME'})
            continue
        if same_key:
            dedup = ('SAME_VALUE_DIFF_RECORD_EXISTING' if same_value
                     else 'CONFLICT_EXISTING_VALUE')
            shown = '、'.join('%s=%s' % (a.get('record_id'), a.get('raw_value')) for a in same_key)
            text = (('本行已有同 rule_key 答案（%s）；结构判定选中 %s=%s（同值异记录）。'
                     '不得再新增同值答案，也不得改写为唯一来源已确认。'
                     if same_value else
                     '本行已有同 rule_key 异值答案（%s）；结构判定选中 %s=%s 与既有值冲突，'
                     '不新增、不改值，保留待人工核实。')
                    % (shown, selected['skillid'], selected['raw']))
            _merge_marker(r, _row_marker(res, dedup, {'existing_answers': existing,
                                                      'disclosure': text}))
            report['marker_only'] += 1
            report['markers'].append({'row_id': r.get('row_id'), 'dedup': dedup,
                                      'record_id': selected['skillid'],
                                      'raw_value': selected['raw']})
            continue
        base_row_ids = sorted({a.get('peer') for a in
                               (res['rules'].get('R7_enum_cross') or {})
                               .get('record_and_value_matches') or [] if a.get('peer')})
        res['_root'] = data.root
        answer = _answer(res, base_row_ids, excluded, existing)
        if _append(r, answer, res, 'NEW_ANSWER_NO_EXISTING_RULE_KEY'):
            report['answers_added'] += 1
            report['additions'].append({'row_id': r.get('row_id'),
                                        'record_id': selected['skillid'],
                                        'rule_key': rule_key,
                                        'field_path': selected['slot'],
                                        'raw_value': selected['raw'],
                                        'admission_basis': selected.get('admission_basis'),
                                        'record_selection': (selected.get('selection') or {})
                                        .get('record_note'),
                                        'base_row_ids': base_row_ids})
    return report


# ---------------------------------------------------------------- 只读探针

def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='C8-B1 denju 伤害镜像余量判定：只读探针')
    ap.add_argument('--cid', type=int)
    ap.add_argument('--row-id')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    root = Path('.').resolve()
    import card_page_data as D
    pages = root / 'output/character_skills/pages'
    if args.cid or args.row_id:
        cids = [args.cid or int(str(args.row_id).split('-', 1)[0])]
    else:
        cids = sorted(int(p.name) for p in pages.iterdir()
                      if p.is_dir() and p.name.isdigit())
    data = D.Inputs(root, cids)
    out = []
    for cid in cids:
        card = json.loads((pages / str(cid) / 'card.json').read_text(encoding='utf-8'))
        rows = [(g.get('group'), r) for g in card.get('groups') or []
                for s in g.get('skills') or [] for r in s.get('rows') or []]
        all_rows = [r for _gn, r in rows]
        for gn, r in rows:
            if not is_denju_row(gn, r.get('reference_field')):
                continue
            if args.row_id and args.row_id != r.get('row_id'):
                continue
            row = dict(r)
            row['_group'] = gn
            res = evaluate(data, cid, row, rows=all_rows)
            out.append({'cid': cid, 'row_id': r.get('row_id'),
                        'accepted': res['rejection'] is None,
                        'rejection': res['rejection'],
                        'selected': {k: v for k, v in (res.get('selected') or {}).items()
                                     if k in ('skillid', 'type', 'slot', 'raw', 'rule_key',
                                              'admission_basis', 'selection')}})
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for item in out:
            print(('OK  ' if item['accepted'] else 'REJ '), item['row_id'],
                  (item.get('selected') or {}).get('rule_key'),
                  (item.get('selected') or {}).get('raw'),
                  item.get('rejection') or '')
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
