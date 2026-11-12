# -*- coding: utf-8 -*-
"""C7-B3 传授（denju）伤害镜像首段补齐：G1 族结构规则，28 行 / 28 卡（全 Y.G.）。

任务卡 ``docs/tasks/20261030-c7-p3-throughput-package.md``；预检
``output/character_skills/c7_p3_20261030/precheck/``（``precheck_report.md`` §3、
``batch_plan.json``、``candidates_all.jsonl``、``boundary_cases.json``、
``evidence_boundaries.md``）。

为什么是这一族
--------------
C7-P1 的 G1 结构族（``card_page_inference_g1_structure.py``）用 **逐字同文** 做 R8 交叉核；
传授（denju）行的句面是 ``【連撃】…``，同卡基础档行的句面是
``【共鳴必殺/連撃】…``——**句首展示标签不同、句身逐字相同**，因此 G1 的 ``canon`` 全等
永远不成立，这些行一律落到 ``FIELD_VALUE_ONLY``（零写入）。本模块把同一族的结构判定
限定到 **denju 行**，并把交叉核换成主持已裁定的**枚举前缀**口径：

    同卡基档行句面 == 「共鳴必殺/」 + 本行句首标签 + 本行句身（逐字，canon 后）

主持裁定（任务卡 §（本批））明示：该句面关系**只能作辅助交叉核，不能作 G1 R8 主证**，
归属仍标 ``推断``。本模块据此把主证放在 **denju 原始链**（R1–R7 结构/类型/槽位），
枚举前缀交叉核只用于确认「同记录同原值已在同卡基档行披露」（0 新增唯一数值）。

与既有模块的关系（本模块不修改它们）
----------------------------------
* ``card_page_inference_g1_structure.py``：本模块是它的 **denju 限定 + 枚举前缀交叉核**
  版本。两者作用集不相交：G1 只在逐字同文成立时写答案（这些行本模块会因「已有同键
  答案」幂等跳过）；G1 判 ``FIELD_VALUE_ONLY`` 的行本模块才可能写。
* ``card_page_inference_c7_p2_denju.py``：C7-P2 是 2 行冻结准入表（t13/t64 增益与回复），
  本模块是 denju 行的**伤害镜像**结构族（t3/22/55/74/105/110 六键），不重叠。
* 账本沿用既有 ``binding.g1_b1_binding``（scope＝``G1_B1_MIRROR_20261029``）与
  ``effect_ledger.G1B1_RULE_EFFECT`` 的 6 个既有确认规则键；**不改**
  ``rules.json``／``rules.py``／``effect_ledger.py``／其他推断模块。

判据（逐行硬门，任一不符即拒绝，不猜）
------------------------------------
R1 **行身份**：``group == denju`` 且 ``reference_field`` 以 ``denju.`` 开头；行日语片段
   与 ``denju.stext`` **首句**逐字相同；``context_text`` 与 ``denju.stext`` 逐字相同。
R2 **同层**：行 ``source.layer == CACHE`` 且 ``source_key == CACHE/denju.data5.json.raw``；
   子记录只从 CACHE ``bossinfo`` 取，**本模块不读 APK 表**（``_mdBossInfo`` 同号记录不入）。
R3 **链可达且唯一**：``denju.patternid0`` 非空、在该层 ``bosspattern`` 唯一命中；
   ``pattern.sinfo`` 与 ``denju.stext`` 逐字相同；槽位从 0 连续、子记录 ``skillid``
   在本层 ``bossskill`` 唯一命中。
R4 **形态选型唯一**：``N回ダメージ`` → 多段型 type105/110 且 ``skillparam6 == N`` 恰 1 条；
   大/中/一定間隔ダメージ → 单发型 type3/22/55/74 恰 1 条；其余形态（PLAIN、受击、
   增益/减益）拒绝。
R5 **槽位与空值分档**：类型 → 已确认伤害槽（``DAMAGE_SLOT``）；缺失/null/非有限/负值/
   真零各自独立拒绝；命中值必须 FINITE 且 > 0。
R6 **同卡基础档序列**：``charainfo.pattern0`` 指向的 ``bosspattern`` 槽序列与本行链序列
   **逐位相同**；``charainfo`` 记录对应 ``skillparam`` 与选中记录逐位相等。任一不同即
   拒绝（本批 30336 即在此门：``skillid1`` 漂移，任务卡已先行排除、不补证不扩大）。
R7 **枚举前缀辅助交叉核**：同卡（CACHE）存在句面 **逐字等于**
   ``【共鳴必殺/<本行句首标签>】 + 本行句身`` 的行，且该行已有
   **(rule_key, 选中记录 id, 原值)** 三重相等的答案；同 rule_key 同记录 id 但异值 → 拒绝
   （``ENUM_PREFIX_VALUE_CONFLICT``）；缺 → 拒绝（``NO_ENUM_PREFIX_CORROBORATION``）。
   剥掉句首【…】的宽松匹配**只作敏感性披露**，不作准入判据。
R8 **排除分支**：``charainfo.pattern1..4`` 中 ``sinfo`` 含「超共鳴」的另一条
   ``bosspattern``，其 slot0 同类型记录必须存在且原值与本行**不同**（不同值才登记为
   排除分支；本批逐行登记）。链内其余槽只登记不绑定。
R9 **幂等与去重**：本行已有同 rule_key 答案时——同记录同值 → 幂等跳过（零写入）；
   同值异记录 → 只写行级披露，不重复新增；同键异值 → 不新增、不改写，只披露。
   保护卡 30236／30239 零触碰。

证据分档（不得升格）
--------------------
R1–R3、R5 的槽位、R6 是**结构/类型证据**；R4 的「N回 ↔ param6」「大/中/一定間隔 ↔
单发型」是**类型语义＋一致性推断**；R7 是**同卡枚举前缀辅助交叉核**（主持裁定不作主证）。
故答案 ``association_evidence = 推断``、``evidence_scope = BY_TYPE_EXTRAPOLATED``，
``numeric_evidence = 确认``（原值与已确认规则键），不写最终扣血、不做秒数换算、不做实机验证。

数值来源
--------
答案 ``raw_value`` 逐字取自本行原始链选中的 bossskill 记录槽位；每个值在该卡此前已由
同卡基档行以同一规则键同一记录披露（0 新增唯一数值）。
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

MODULE_VERSION = 'c7_p3_denju_damage_20261030'
#: 账本消费用 scope：沿用既有 G1-B1 来源限定映射（effect_ledger.G1B1_SCOPE）。
SCOPE = 'G1_B1_MIRROR_20261029'
#: 结构判定自身的 marker scope（行级 ``inference_c7_p3_denju`` 与答案 binding 附带）。
STRUCTURE_SCOPE = 'C7_P3_DENJU_DAMAGE_20261030'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'

#: 类型 → 已确认规则键的伤害槽（逐键取自 profiles/rules.json，本批不新增键）。
DAMAGE_SLOT = {3: 'skillparam1', 22: 'skillparam1', 55: 'skillparam1',
               74: 'skillparam5', 105: 'skillparam1', 110: 'skillparam1'}
SINGLE_TYPES = (3, 22, 55, 74)
MULTI_TYPES = (105, 110)

#: effect_ledger.G1B1_RULE_EFFECT 覆盖的 6 键（其余类型不出值）。
LEDGER_MAPPED_RULE_KEYS = frozenset('bossskill|%d|/%s' % (t, s)
                                    for t, s in DAMAGE_SLOT.items())

#: 保护卡：30236 / 30239 G0 豁免不扩大（任务卡 §2 保护项）。
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

MULTIHIT_RX = re.compile(r'(\d+)回ダメージ')
BIGMID_RX = re.compile(r'(?:大|中)ダメージ')
INTERVAL_RX = re.compile(r'一定間隔でダメージ')
RECEIVE_MARKS = ('受ける', '受け', '味方')
MODIFIER_MARKS = ('ダメージが上がる', 'ダメージが下がる', 'ダメージが増', 'ダメージが減')
TAG_RX = re.compile(r'^(?:【[^】]*】)+')
FIRST_TAG_RX = re.compile(r'^【([^】]*)】')

#: 行级 marker 键（不覆盖其他批次键）。
MARKER_KEY = 'inference_c7_p3_denju'

#: 与 G1 结构族同一处「未知原因」清理口径（本模块覆盖伤害子句后这些理由失效）。
_STALE_REASONS = {
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应',
}

_BOSSINFO_CACHE = {}


# ---------------------------------------------------------------- 纯函数（结构判定）

def canon(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def canon_no_tag(text):
    """剥离句首【…】展示标签后的规范文本（只用于 R7b 敏感性披露，不作准入判据）。"""
    return TAG_RX.sub('', canon(text))


def first_tag(japanese):
    m = FIRST_TAG_RX.match(str(japanese or ''))
    return m.group(1) if m else None


def prefix_of(japanese):
    m = TAG_RX.search(str(japanese or ''))
    return m.group(0) if m else ''


def classify_clause(japanese):
    """片段 → 伤害子句形态。返回 ``(form, detail)``；form∈{MULTIHIT,BIGMID,INTERVAL,PLAIN,None}。"""
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
        path = read_path(Path(root) / 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw', root=Path(root))
        doc = json.loads(path.read_text(encoding='utf-8-sig'))['bossinfo']
        _BOSSINFO_CACHE[key] = dict(
            patterns={p['patternid']: (i, p) for i, p in enumerate(doc.get('bosspattern') or [])},
            skills={s['skillid']: (i, s) for i, s in enumerate(doc.get('bossskill') or [])},
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
    """R1/R3：denju 父记录 + pattern 指针（都在本行层）。"""
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


def children_of(root, layer, pattern_id):
    """R3：pattern.skillid0..6 → bossskill（同层）。"""
    raw = _bossinfo(root)
    hit = raw['patterns'].get(pattern_id)
    if hit is None:
        return None, None, None
    index, pattern = hit
    children = []
    for slot in range(7):
        sid = pattern.get('skillid%d' % slot)
        if not sid:
            continue
        sh = raw['skills'].get(sid)
        if sh is None:
            children.append({'slot': slot, 'skillid': sid, 'missing': True})
            continue
        k_index, record = sh
        children.append({'slot': slot, 'skillid': sid, 'index': k_index, 'record': record,
                         'type': record.get('skillid0'),
                         'params': {k: v for k, v in record.items()
                                    if k.startswith('skillparam')}})
    return index, pattern, children


def select_child(children, form, detail):
    """R4：片段形态 → 子记录（必须唯一）。"""
    if form == 'MULTIHIT':
        n = detail['n']
        typed = [c for c in children if c.get('type') in MULTI_TYPES]
        hits = [c for c in typed if c['params'].get('skillparam6') == n]
        if not hits:
            return None, {'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed),
                          'rejection': 'NO_MULTIHIT_PARAM6_MATCH'}
        if len(hits) > 1:
            # 本批口径：形态选型必须唯一（同链多条 param6==N 的多段记录＝记录选取不唯一，
            # 不按值相同就任取一条）。7251 即此门（slot0/slot2 同为 15回）。
            return None, {'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed),
                          'records': sorted(c['skillid'] for c in hits),
                          'rejection': 'MULTI_MULTIHIT_NOT_UNIQUE'}
        return hits[0], {
            'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed), 'param6': n,
            'records': [c['skillid'] for c in hits],
            'record_note': 'RECORD_UNIQUE',
            'basis': '句面 N回ダメージ ↔ 多段型 type105/110 且 skillparam6==N'}
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
    """同签名（全部 skillparam* 键值）的其他记录数（同值异记录披露；不按值配对）。"""
    bound_type = record.get('skillid0')
    sig = {k: v for k, v in record.items() if k.startswith('skillparam')}
    return sum(1 for rec in tab['skills_all']
               if rec.get('skillid0') == bound_type
               and {k: v for k, v in rec.items() if k.startswith('skillparam')} == sig)


def super_tiers_of(root, cid, charainfo, bound_type):
    """R8：``charainfo.pattern1..4`` 中含「超共鳴」的 pattern 的 slot0（同类型）。"""
    out = []
    raw = _bossinfo(root)
    for i in range(1, 5):
        pid = charainfo.get('pattern%d' % i)
        if not pid:
            continue
        hit = raw['patterns'].get(pid)
        if hit is None:
            continue
        pattern = hit[1]
        sinfo = str(pattern.get('sinfo') or '')
        if '超共鳴' not in sinfo:
            continue
        sid = pattern.get('skillid0')
        sh = raw['skills'].get(sid)
        if sh is None:
            continue
        rec = sh[1]
        if rec.get('skillid0') != bound_type:
            continue
        out.append({'pointer': 'charainfo.pattern%d' % i, 'pattern_id': pid,
                    'record_id': sid, 'type': rec.get('skillid0'),
                    'params': {k: v for k, v in rec.items() if k.startswith('skillparam')},
                    'clause': sinfo[:120]})
    return out


def base_sequence_of(root, charainfo, chain_len):
    pid = charainfo.get('pattern0')
    raw = _bossinfo(root)
    hit = raw['patterns'].get(pid) if pid else None
    if hit is None:
        return None, None
    pattern = hit[1]
    return pid, [pattern.get('skillid%d' % s) for s in range(chain_len)]


# ---------------------------------------------------------------- 单行判定

def evaluate(data, cid, row, *, rows=None, tab=None):
    """单行判定（不写入）。``rows`` 为同卡全部行（R7 交叉核）。"""
    out = {'cid': cid, 'row_id': row.get('row_id'), 'kind': 'DENJU', 'rules': {},
           'rejection': None, 'selected': None, 'gates': {}}
    if cid in ZERO_TOUCH_CIDS:
        out['rejection'] = 'ZERO_TOUCH_CID'
        return out
    if not is_denju_row(row.get('_group'), row.get('reference_field')):
        out['rejection'] = 'NOT_A_DENJU_ROW'
        return out
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
    p_index, pattern, children = children_of(data.root, 'CACHE', parent['pattern_id'])
    if pattern is None:
        out['rejection'] = 'BOSSPATTERN_MISSING'
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
    if chosen is None:
        out['rejection'] = sel.get('rejection')
        return out
    # R5 槽位与空值分档
    slot = DAMAGE_SLOT.get(chosen.get('type'))
    present = slot is not None and slot in chosen['params']
    raw = chosen['params'].get(slot) if slot else None
    state = raw_state(raw, present)
    out['rules']['R5_slot'] = {'type': chosen.get('type'), 'slot': slot, 'raw': raw,
                               'present': present, 'raw_state': state}
    if slot is None:
        out['rejection'] = 'TYPE_WITHOUT_DAMAGE_RULE'
        return out
    if state == 'MISSING':
        out['rejection'] = 'RAW_VALUE_MISSING'
        return out
    if state == 'NULL':
        out['rejection'] = 'RAW_VALUE_NULL'
        return out
    if state == 'NON_FINITE':
        out['rejection'] = 'RAW_VALUE_NON_FINITE'
        return out
    if state == 'NEGATIVE':
        out['rejection'] = 'RAW_VALUE_NEGATIVE'
        return out
    if state == 'ZERO':
        out['rejection'] = 'RAW_VALUE_ZERO'
        return out
    if float(raw) <= 0:
        out['rejection'] = 'RAW_VALUE_NON_POSITIVE'
        return out
    rule_key = 'bossskill|%d|/%s' % (chosen['type'], slot)
    if rule_key not in LEDGER_MAPPED_RULE_KEYS:
        out['rejection'] = 'RULE_KEY_NOT_IN_LEDGER_SCOPE'
        return out
    out['selected'] = {'skillid': chosen['skillid'], 'type': chosen['type'],
                       'slot': '/' + slot, 'raw': raw, 'raw_state': state,
                       'rule_key': rule_key, 'record_index': chosen['index'],
                       'selection': sel}
    # R6 同卡基础档序列
    charainfo = (getattr(data, 'cache_chara', None) or {}).get(cid) or {}
    base_pid, base_ids = base_sequence_of(data.root, charainfo, len(children))
    same_seq = base_ids == [c['skillid'] for c in children] if base_ids else False
    ten_equal = charainfo.get(slot) == raw
    out['rules']['R6_base_tier'] = {'pattern0': base_pid, 'base_ids': base_ids,
                                    'chain_ids': [c['skillid'] for c in children],
                                    'same_sequence': same_seq, 'chara_slot_equal': ten_equal}
    if base_pid is None:
        out['rejection'] = 'BASE_TIER_MISSING'
        return out
    if not same_seq:
        out['rejection'] = 'BASE_TIER_SEQUENCE_MISMATCH'
        return out
    if not ten_equal:
        out['rejection'] = 'CHARAINFO_SLOT_MISMATCH'
        return out
    # R7 枚举前缀辅助交叉核（同卡、CACHE、逐字句面）
    dtag = first_tag(row.get('japanese'))
    if dtag is None:
        out['rejection'] = 'ROW_TAG_MISSING'
        return out
    target = canon('【共鳴必殺/%s】' % dtag) + canon_no_tag(row.get('japanese'))
    enum_rows, super_rows, relaxed_rows = [], [], []
    body = canon_no_tag(row.get('japanese'))
    for other in rows or []:
        if other.get('row_id') == row.get('row_id'):
            continue
        ja = canon(other.get('japanese'))
        pref = prefix_of(other.get('japanese'))
        if canon_no_tag(other.get('japanese')) == body:
            relaxed_rows.append(other.get('row_id'))
        if ja == target:
            enum_rows.append(other)
        elif pref == canon('【超共鳴必殺/%s】' % dtag):
            super_rows.append(other)
    def _ans(other):
        src2 = other.get('source') or {}
        return (src2.get('layer') == 'CACHE', [
            {'rule_key': a.get('rule_key'), 'record_id': a.get('record_id'),
             'raw_value': a.get('raw_value')} for a in other.get('answers') or []])
    enum_items, enum_cache_rows, enum_off_layer = [], [], []
    for other in enum_rows:
        cache_ok, items = _ans(other)
        if cache_ok:
            enum_items.extend(dict(a, peer=other.get('row_id')) for a in items)
            enum_cache_rows.append(other.get('row_id'))
        else:
            enum_off_layer.append(other.get('row_id'))
    corrobor = [a for a in enum_items
                if a['rule_key'] == rule_key and a['record_id'] == chosen['skillid']
                and a['raw_value'] == raw]
    conflicts = [a for a in enum_items
                 if a['rule_key'] == rule_key and a['record_id'] == chosen['skillid']
                 and a['raw_value'] != raw]
    # 同 rule_key、不同记录（基档行重复键）：只披露，不认领；绑定只认选中记录 id。
    same_key_other_records = [a for a in enum_items
                              if a['rule_key'] == rule_key
                              and a['record_id'] != chosen['skillid']]
    out['rules']['R7_enum_cross'] = {
        'enum_prefix': '【共鳴必殺/%s】' % dtag,
        'enum_peers': enum_cache_rows,
        'enum_peers_off_layer': enum_off_layer,
        'record_and_value_matches': corrobor,
        'conflicts': conflicts,
        'same_key_other_records': same_key_other_records,
        'role': 'AUXILIARY_CORROBORATION_NOT_PRIMARY（主持裁定：不作 G1 R8 主证）',
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
    # R8 排除分支（超共鳴档）
    supers = super_tiers_of(data.root, cid, charainfo, chosen['type'])
    out['rules']['R8_super_tier'] = supers
    if not supers:
        out['rejection'] = 'SUPER_TIER_NOT_FOUND'
        return out
    distinct = [s for s in supers if s['params'].get(slot) != raw]
    if not distinct:
        out['rejection'] = 'SEGMENTS_INDISTINCT'
        return out
    out['gates']['excluded_values'] = [[s['record_id'], s['params'].get(slot)]
                                       for s in distinct]
    out['gates']['excluded_rows'] = [s['pointer'] for s in supers]
    out['parent'] = {'table': parent['table'], 'pointer': parent['pointer'],
                     'pattern_id': parent['pattern_id'], 'entry': parent['entry'],
                     'record': parent['record']}
    out['pattern_record'] = pattern
    out['chosen_record'] = chosen['record']
    out['verdict'] = 'VALUE_AND_BINDING'
    return out


# ---------------------------------------------------------------- 答案与 marker

def _source_of(data, chosen, slot, pattern_pointer):
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
        'note': ('按解码 JSON 的 bossskill.skillid 唯一命中；本行原始链（%s）定源，不是同文复制'
                 % pattern_pointer),
    }


def _answer(data, res, base_row_ids, excluded, same_value_existing):
    selected = res['selected']
    slot, raw, rid = selected['slot'], selected['raw'], selected['skillid']
    rule_key = selected['rule_key']
    chosen = {'skillid': rid, 'index': selected['record_index'], 'type': selected['type'],
              'record': res['chosen_record']}
    source = _source_of(data, chosen, slot[1:], res['parent']['pointer'])
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
        note_unique = '；同值异记录：%s 均为 %s（记录选取不唯一，值唯一）' % (
            '/'.join(str(c) for c in selected['selection'].get('records') or []), num)
    value = ('%s：%s（相对B；对象：敌方；镜像行按 denju 原始链定源到 bossskill %s type%s %s；'
             '同规则键同记录同原值已在同卡基档行 %s 披露；%s%s）'
             % (qk, num, rid, selected['type'], slot, base_ids, exc_tail, note_unique))
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
        'same_value_existing_answers': same_value_existing,
        'enum_prefix_cross_check': res['rules'].get('R7_enum_cross'),
        'same_key_base_answers': (res['rules'].get('R7_enum_cross') or {})
        .get('same_key_other_records'),
        'same_value_other_records': {
            'signature': {k: v for k, v in res['chosen_record'].items()
                          if k.startswith('skillparam')},
            'count': _same_signature_count(_bossinfo(data.root), res['chosen_record']),
            'note': '同值异记录：按记录 id 绑定，不按值配对',
        },
        'r8b_tag_normalized': res['rules'].get('R7b_tag_normalized'),
        'association': '推断',
        'cross_check_role': 'AUXILIARY_CORROBORATION_NOT_PRIMARY',
        'native_evidence': ('none（本批不新增原生点；片段判别为类型语义＋一致性推断；'
                            '枚举前缀交叉核只作辅助核，不作 G1 R8 主证）'),
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
        'binding': {'g1_b1_binding': marker,
                    'c7_p3_denju_binding': {'scope': STRUCTURE_SCOPE,
                                            'module': MODULE_VERSION,
                                            'verdict': res['verdict'],
                                            'dedup': 'NEW_ANSWER_NO_EXISTING_RULE_KEY'}},
        'target': '敌',
        'note': ('仅局部伤害输入公式（B=getBasicSkillAttack(true) 等沿用原规则定义），未验证'
                 '最终扣血、保证命中与运行时选档；抽取自本行 denju 原始链记录，非最终伤害。'
                 '同卡基档句面＝共鳴必殺/＋本行标签的枚举前缀只作辅助交叉核（不作 R8 主证），'
                 '超共鳴档位值已登记排除。结构判定规则见 '
                 'card_page_inference_c7_p3_denju.py 模块头注 R1–R9。'),
        'evidence': ['docs/tasks/20261030-c7-p3-throughput-package.md',
                     'output/character_skills/c7_p3_20261030/precheck/precheck_report.md',
                     'output/character_skills/c7_p1_20261029/build_report.md'],
    }


def _append(row, answer, res, dedup):
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    if any(key(a) == key(answer) for a in row.get('answers') or []):
        return False
    row.setdefault('answers', []).append(answer)
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = ('推断（C7-B3 传授伤害镜像首行绑定：denju 原始链定源；'
                             '倍率见同卡基档位行，不新增唯一数值）')
    row['partial'] = True
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    row['evidence_scope'] = list(dict.fromkeys(list(row.get('evidence_scope') or [])
                                              + ['BY_TYPE_EXTRAPOLATED']))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    reasons.append('C7-B3：本行伤害子句已按 denju 原始链首段绑定倍率（同卡基档行同值、'
                   '超共鳴档位值已排除）；同句其余机制仍按原状登记，账本行仍为拆分待核查。')
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
        'pattern_id': (res.get('parent') or {}).get('pattern_id'),
        'structure': {k: v for k, v in (res.get('rules') or {}).items()
                      if k in ('R4_clause', 'R4b_select', 'R5_slot', 'R6_base_tier')},
        'enum_prefix_cross_check': res.get('rules', {}).get('R7_enum_cross'),
        'r8b_tag_normalized': res.get('rules', {}).get('R7b_tag_normalized'),
        'super_tier': res.get('rules', {}).get('R8_super_tier'),
        'excluded_values': (res.get('gates') or {}).get('excluded_values'),
        'note': ('结构判定 marker：不新增/不改写答案时也保留判定与披露；'
                 '枚举前缀交叉核只作辅助核（不作 R8 主证）；归属仍为推断。'),
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
    """正式页消费：为 denju 伤害镜像首段行写入绑定答案或行级 marker（不覆盖既有答案）。"""
    report = {'scope': STRUCTURE_SCOPE, 'cid': cid, 'evaluated': 0, 'answers_added': 0,
              'marker_only': 0, 'skipped_existing': 0, 'field_value_only': 0,
              'additions': [], 'markers': [], 'rejections': [], 'out_of_scope': True}
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append({'reason': 'ZERO_TOUCH_CID', 'cid': cid})
        return report
    rows = [(g.get('group'), s, r) for g in groups or [] for s in g.get('skills') or []
            for r in s.get('rows') or []]
    mirrors = [(gn, s, r) for gn, s, r in rows
               if is_denju_row(gn, r.get('reference_field'))]
    if not mirrors:
        return report
    report['out_of_scope'] = False
    all_rows = [r for _gn, _s, r in rows]
    for gn, s, r in mirrors:
        layer = s.get('layer')
        if layer != 'CACHE':
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
        existing_disclosure = [{'record_id': a.get('record_id'),
                                'raw_value': a.get('raw_value'),
                                'rule_key': a.get('rule_key')} for a in same_key]
        if same_rec_value:
            report['skipped_existing'] += 1
            report['markers'].append({'row_id': r.get('row_id'),
                                      'dedup': 'ALREADY_PRESENT_SAME'})
            continue
        if same_key:
            dedup = ('SAME_VALUE_DIFF_RECORD_EXISTING' if same_value
                     else 'CONFLICT_EXISTING_VALUE')
            shown = '、'.join('%s=%s' % (a.get('record_id'), a.get('raw_value'))
                              for a in same_key)
            if same_value:
                text = ('本行已有同 rule_key 答案（%s）；结构判定选中 %s=%s（同值异记录）。'
                        '不得再新增同值答案，也不得改写为唯一来源已确认。'
                        % (shown, selected['skillid'], selected['raw']))
            else:
                text = ('本行已有同 rule_key 异值答案（%s）；结构判定选中 %s=%s 与既有值冲突，'
                        '不新增、不改值，保留待人工核实。'
                        % (shown, selected['skillid'], selected['raw']))
            _merge_marker(r, _row_marker(res, dedup, {'existing_answers': existing_disclosure,
                                                      'disclosure': text}))
            report['marker_only'] += 1
            report['markers'].append({'row_id': r.get('row_id'), 'dedup': dedup,
                                      'record_id': selected['skillid'],
                                      'raw_value': selected['raw']})
            continue
        base_row_ids = sorted({a.get('peer') for a in
                               (res['rules'].get('R7_enum_cross') or {})
                               .get('record_and_value_matches') or [] if a.get('peer')})
        answer = _answer(data, res, base_row_ids, excluded, existing_disclosure)
        if _append(r, answer, res, 'NEW_ANSWER_NO_EXISTING_RULE_KEY'):
            report['answers_added'] += 1
            report['additions'].append({'row_id': r.get('row_id'),
                                        'record_id': selected['skillid'],
                                        'rule_key': rule_key,
                                        'field_path': selected['slot'],
                                        'raw_value': selected['raw'],
                                        'base_row_ids': base_row_ids})
    return report


# ---------------------------------------------------------------- 只读探针（wrapper）

def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='C7-B3 传授伤害镜像首段判定：只读探针（单卡/单行/全库）')
    ap.add_argument('--cid', type=int, help='单卡重算（读当前正式页，不写入）')
    ap.add_argument('--row-id', help='单行检测')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    root = Path('.').resolve()
    import card_page_data as D
    pages = root / 'output/character_skills/pages'
    if args.cid or args.row_id:
        cid = args.cid or int(str(args.row_id).split('-', 1)[0])
        cids = [cid]
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
            if args.row_id and r.get('row_id') != args.row_id:
                continue
            row = dict(r)
            row['_group'] = gn
            res = evaluate(data, cid, row, rows=all_rows)
            out.append({'cid': cid, 'row_id': r.get('row_id'),
                        'accepted': res['rejection'] is None,
                        'rejection': res['rejection'],
                        'selected': res.get('selected'),
                        'enum_peers': (res.get('rules', {}).get('R7_enum_cross') or {})
                        .get('enum_peers'),
                        'base_row_ids': sorted({a.get('peer') for a in
                                                (res.get('rules', {}).get('R7_enum_cross') or {})
                                                .get('record_and_value_matches') or []}),
                        'excluded_values': (res.get('gates') or {}).get('excluded_values'),
                        'rules': res.get('rules')})
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
