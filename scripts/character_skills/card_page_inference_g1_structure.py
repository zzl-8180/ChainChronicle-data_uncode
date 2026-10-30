# -*- coding: utf-8 -*-
"""G1 必殺ダメージ镜像族**结构推广**（C7-B1，正式生产接入）。

任务书：``docs/tasks/20261029-c7-p1-throughput-package.md`` §1（C7-B1）、
``docs/tasks/20261029-mainline-throughput-plan.md`` §2.4（首个推广试点）。
候选与独审：``output/character_skills/c7_p1_20261029/g1_structure/``、
``output/character_skills/review/c7_p1_g1_structure_20261029_deepseek/REPORT.md``
（PASS_WITH_EXPLICIT_SCOPE_LIMITS）。

与 ``card_page_inference_g1_b1.py`` 的关系（本模块是它的**结构推广**，不是替代）
--------------------------------------------------------------------------
G1-B1 把 25 行写死在 ``_ADMITTED_LIST``（row_id / pattern / skillid / raw / excluded）。
本模块保留同一判定语义，但把「哪一行可以出」换成可核对的**结构规则**，因此同族新记录
不再需要手加 row_id：

    R1 记录身份：行的父记录必须在本行所在层解析（DENJU / CHARAINFO，均 CACHE）
    R2 引用链：父记录只交出 pattern 指针（denju.patternid0 / charainfo.pattern0）
    R3 文本同一：该 pattern 的 sinfo 必须与父记录自己的文本逐字相同
    R4 子句：本行日语片段必须含一条「对敌造成伤害」的子句（对象/方向门）
    R5 选中：片段形态 → 子记录类型类；N回 → 多段型 type105/110 且 skillparam6==N；
             单发型（大/中/一定間隔）恰 1 条 type3/22/55/74
    R6 注入性：同一 (pattern, 父文本) 内，不同片段不得落到同一条**单发型**子记录
    R7 槽位：类型 → 已确认规则键的伤害槽；缺失/null/非有限/负值拒绝；type74 的 ≤0 拒绝
    R8 交叉核：同卡**逐字**同文 pattern 行上已有同 rule_key / 同记录 / 同原值的答案
              （剥离句首【…】的放宽匹配只作敏感性披露 R8b，不作准入判据）
    R9 幂等：本行若已有同键答案则不重复写（见下「去重」）

证据分档（不得升格）
--------------------
R1–R3、R5 的 param6、R6、R7 是**结构/类型证据**；R4 的「N回 ↔ param6」「大/中/一定間隔 ↔
单发型」是**类型语义＋一致性推断**；R8 是**同卡交叉核对**，只作确认。故答案
``association_evidence = 推断``、``evidence_scope = BY_TYPE_EXTRAPOLATED``，
与 C6 批2 同档，不写最终扣血/秒数。

去重（C7-P1 硬性要求）
----------------------
* 账本映射沿用既有 ``binding.g1_b1_binding``（scope＝``G1_B1_MIRROR_20261029``）与
  6 个既有确认规则键，**不新增规则键、不改 rules.json/rules.py/effect_ledger.py**。
* 本行已有同 rule_key 答案时**一律不再新增答案**：
    - 同记录同值 → ``ALREADY_PRESENT_SAME``（幂等，无写入）；
    - 同值异记录 → ``SAME_VALUE_DIFF_RECORD_EXISTING``：**只写行级 marker 披露**
      （7251 skilltext f2：既有 40725101=0.83，结构选中 40725100=0.83），不新增同值答案；
    - 同键异值 → ``CONFLICT_EXISTING_VALUE``：不新增，只写 marker（不覆盖、不改值）。
* 只有「本行无同 rule_key 答案」且 R8 同记录同值成立时才写答案。
* 30236／30239（G0 豁免）零触碰；APK 层镜像行一律范围外（本族已证载体只有 CACHE
  bossskill，本模块**不读 APK 表**，跨层在结构上不可达）。
"""
from __future__ import annotations

import json
import math
import re
import struct
import unicodedata
from pathlib import Path

MODULE_VERSION = 'g1_structure_c7b1_20261029'
#: 账本消费用 scope：沿用既有 G1-B1 来源限定映射（effect_ledger.G1B1_SCOPE）。
SCOPE = 'G1_B1_MIRROR_20261029'
#: 结构判定自身的 marker scope（行级 ``inference_g1_structure`` 与答案 binding 附带）。
STRUCTURE_SCOPE = 'G1_STRUCTURE_C7B1_20261029'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'

#: 类型 → 已确认规则键的伤害槽（逐键取自 profiles/rules.json，本批不新增键）。
DAMAGE_SLOT = {
    3: 'skillparam1',
    22: 'skillparam1',
    55: 'skillparam1',
    74: 'skillparam5',
    105: 'skillparam1',
    110: 'skillparam1',
}
SINGLE_TYPES = (3, 22, 55, 74)
MULTI_TYPES = (105, 110)

#: effect_ledger.G1B1_RULE_EFFECT 覆盖的 6 键（其余类型只能出字段值，不影响账本主张）。
LEDGER_MAPPED_RULE_KEYS = frozenset({
    'bossskill|3|/skillparam1', 'bossskill|22|/skillparam1',
    'bossskill|55|/skillparam1', 'bossskill|74|/skillparam5',
    'bossskill|105|/skillparam1', 'bossskill|110|/skillparam1',
})

#: 保护卡：30236 / 30239 G0 豁免不扩大（任务书 §2 保护项）。
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

MULTIHIT_RX = re.compile(r'(\d+)回ダメージ')
BIGMID_RX = re.compile(r'(?:大|中)ダメージ')
INTERVAL_RX = re.compile(r'一定間隔でダメージ')
RECEIVE_MARKS = ('受ける', '受け', '味方')
MODIFIER_MARKS = ('ダメージが上がる', 'ダメージが下がる', 'ダメージが増', 'ダメージが減')
TAG_RX = re.compile(r'^(?:【[^】]*】)+')

#: 行级 marker 键（不覆盖其他批次键，不写答案时也留判定与披露）。
MARKER_KEY = 'inference_g1_structure'

#: g1_b1 追加答案沿用同一处「未知原因」清理口径（见 card_page_inference_g1_b1._append）。
_STALE_REASONS = {'原文未提供该效果数值，尚无已审定的句内字段归属',
                  '此描述尚无可适用的已确认数值或新增机制证据',
                  '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应'}

_BOSSINFO_CACHE = {}


# ---------------------------------------------------------------- 纯函数（结构判定）

def canon(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def canon_no_tag(text):
    """剥离句首【…】展示标签后的规范文本（只用于 R8b 敏感性披露，不作准入判据）。"""
    return TAG_RX.sub('', canon(text))


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


def row_kind(group, reference_field):
    """行的族内身份：只有 denju 父记录行与 charainfo(skilltext) 行是镜像行。"""
    if group == 'denju' and str(reference_field or '').startswith('denju.'):
        return 'DENJU'
    if group == 'special_move' and reference_field == 'skilltext':
        return 'CHARAINFO'
    return None


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


def ten_slot_diff(parent_record, child_record):
    """charainfo 记录 skillparam0..9 与起始子记录逐槽对照（只作披露）。"""
    diffs = []
    for i in range(10):
        key = 'skillparam%d' % i
        a = (key in parent_record, parent_record.get(key))
        b = (key in child_record, child_record.get(key))
        if a != b:
            diffs.append({'slot': key, 'parent': a[1], 'child': b[1],
                          'parent_present': a[0], 'child_present': b[0]})
    return diffs


# ---------------------------------------------------------------- 记录读取（层显式）

def _bossinfo(root):
    """CACHE bossinfo 的 pattern/skill 索引（只读；本模块不读 APK 表）。"""
    key = str(Path(root).resolve())
    if key not in _BOSSINFO_CACHE:
        path = Path(root) / 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw'
        doc = json.loads(path.read_text(encoding='utf-8-sig'))['bossinfo']
        _BOSSINFO_CACHE[key] = dict(
            patterns={p['patternid']: (i, p) for i, p in enumerate(doc.get('bosspattern') or [])},
            skills={s['skillid']: (i, s) for i, s in enumerate(doc.get('bossskill') or [])})
    return _BOSSINFO_CACHE[key]


def _records(data, cid, group, table):
    for g in (data.links.get(cid) or {}).get('groups') or []:
        if g.get('group') != group:
            continue
        for entry in g.get('records') or []:
            if entry.get('table') == table:
                yield entry


def resolve_parent(data, cid, kind, layer):
    """R1/R2：父记录 + pattern 指针（都在本行层）。返回 (parent|None, rejection|None)。"""
    if layer != 'CACHE':
        return None, 'LAYER_NOT_ESTABLISHED_APK'
    if kind == 'DENJU':
        rec = next(iter(_records(data, cid, 'denju', 'denju')), None)
        if rec is None:
            return None, 'DENJU_RECORD_MISSING'
        record = rec.get('record') or {}
        pid, text = record.get('patternid0'), record.get('stext')
        pointer, table, entry = 'denju.patternid0', 'denju', rec
    elif kind == 'CHARAINFO':
        # links 的 charainfo record 是裁剪视图（不含 pattern0），必须取 CACHE 解码原记录。
        record = (getattr(data, 'cache_chara', None) or {}).get(cid)
        if record is None:
            return None, 'CHARAINFO_RECORD_MISSING'
        pid, text = record.get('pattern0'), record.get('skilltext')
        pointer, table = 'charainfo.pattern0', 'charainfo'
        entry = next(iter(_records(data, cid, 'special_move', 'charainfo')), None) or {}
    else:
        return None, 'UNKNOWN_KIND'
    if pid is None:
        return None, 'PATTERN_POINTER_MISSING'
    if not text:
        return None, 'PARENT_TEXT_MISSING'
    return {'record': record, 'table': table, 'pointer': pointer, 'pattern_id': pid,
            'text': text, 'layer': layer, 'entry': entry}, None


def children_of(data, layer, pattern_id):
    """R5 候选集合：pattern.skillid0..3 → bossskill（同层）。返回 (pattern_index, pattern, children)。"""
    raw = _bossinfo(data.root)
    hit = raw['patterns'].get(pattern_id)
    if hit is None:
        return None, None, None
    index, pattern = hit
    children = []
    for slot in range(4):
        sid = pattern.get('skillid%d' % slot)
        if not sid:
            continue
        sh = raw['skills'].get(sid)
        if sh is None:
            children.append({'slot': slot, 'skillid': sid, 'missing': True})
            continue
        k_index, record = sh
        children.append({
            'slot': slot, 'skillid': sid, 'index': k_index, 'record': record,
            'type': record.get('skillid0'),
            'params': {k: v for k, v in record.items() if k.startswith('skillparam')},
        })
    return index, pattern, children


def select_child(children, form, detail):
    """R5：片段形态 → 子记录。返回 (chosen|None, selection dict)。"""
    if form == 'MULTIHIT':
        n = detail['n']
        typed = [c for c in children if c.get('type') in MULTI_TYPES]
        hits = [c for c in typed if c['params'].get('skillparam6') == n]
        if not hits:
            return None, {'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed),
                          'rejection': 'NO_MULTIHIT_PARAM6_MATCH'}
        values = {c['params'].get('skillparam1') for c in hits}
        if len(values) > 1:
            return None, {'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed),
                          'records': [c['skillid'] for c in hits],
                          'rejection': 'MULTI_MULTIHIT_DIFF_VALUES'}
        hits = sorted(hits, key=lambda c: c['skillid'])
        return hits[0], {
            'mode': 'MULTIHIT', 'n': n, 'n_typed': len(typed), 'param6': n,
            'records': [c['skillid'] for c in hits],
            'record_note': ('VALUE_UNIQUE_RECORD_NOT_UNIQUE' if len(hits) > 1 else 'RECORD_UNIQUE'),
            'basis': '句面 N回ダメージ ↔ 多段型 type105/110 且 skillparam6==N',
        }
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


# ---------------------------------------------------------------- 单行判定

def evaluate(data, cid, row, layer, *, injective=None, base_answers=None,
             base_answers_tag=None):
    """单行判定（不写入）。``injective``/``base_answers`` 由 apply_to_groups 同一卡内预计算。"""
    out = {'cid': cid, 'row_id': row.get('row_id'), 'layer': layer,
           'kind': row_kind(row.get('_group'), row.get('reference_field')),
           'rules': {}, 'rejection': None, 'selected': None, 'gates': {}}
    if out['kind'] is None:
        out['rejection'] = 'NOT_A_MIRROR_ROW'
        return out
    if cid in ZERO_TOUCH_CIDS:
        out['rejection'] = 'ZERO_TOUCH_CID'
        return out
    form, detail = classify_clause(row.get('japanese'))
    out['rules']['R4_clause'] = {'form': form, **detail}
    if form is None:
        out['rejection'] = detail.get('reason') or 'NO_DAMAGE_CLAUSE'
        return out
    if form == 'PLAIN':
        out['rejection'] = 'DAMAGE_WITHOUT_QUALIFIER'
        return out
    parent, err = resolve_parent(data, cid, out['kind'], layer)
    if err:
        out['rejection'] = err
        return out
    out['rules']['R1_parent'] = {'table': parent['table'], 'pointer': parent['pointer'],
                                 'pattern_id': parent['pattern_id'], 'layer': layer}
    p_index, pattern, children = children_of(data, layer, parent['pattern_id'])
    if pattern is None:
        out['rejection'] = 'BOSSPATTERN_MISSING'
        return out
    sinfo = pattern.get('sinfo')
    out['rules']['R3_text'] = {'pattern_index': p_index, 'sinfo_present': bool(sinfo),
                               'sinfo_equals_parent_text': canon(sinfo) == canon(parent['text'])}
    if not sinfo:
        out['rejection'] = 'PATTERN_SINFO_MISSING'
        return out
    if canon(sinfo) != canon(parent['text']):
        out['rejection'] = 'PARENT_TEXT_NOT_PATTERN_SINFO'
        return out
    chosen, sel = select_child(children, form, detail)
    out['rules']['R5_select'] = sel
    if chosen is None:
        out['rejection'] = sel.get('rejection')
        return out
    out['gates']['children'] = [{'skillid': c['skillid'], 'type': c.get('type')} for c in children]
    if injective is not None and form != 'MULTIHIT':
        same = injective.get(chosen['skillid']) or []
        out['rules']['R6_injective'] = {'record_id': chosen['skillid'], 'rows': same}
        if len(same) > 1:
            out['rejection'] = 'FRAGMENT_RECORD_NOT_INJECTIVE'
            return out
    slot = DAMAGE_SLOT.get(chosen.get('type'))
    present = slot is not None and slot in chosen['params']
    raw = chosen['params'].get(slot) if slot else None
    state = raw_state(raw, present)
    out['rules']['R7_slot'] = {'type': chosen.get('type'), 'slot': slot, 'raw': raw,
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
    if chosen['type'] == 74 and float(raw) <= 0:
        out['rejection'] = 'TYPE74_THRESHOLD_NOT_MET'
        return out
    rule_key = 'bossskill|%d|/%s' % (chosen['type'], slot)
    out['selected'] = {'skillid': chosen['skillid'], 'type': chosen['type'],
                       'slot': '/' + slot, 'raw': raw, 'raw_state': state,
                       'rule_key': rule_key, 'record_index': chosen['index'],
                       'selection': sel}
    base = base_answers or []
    rec_hits = [a for a in base if a.get('rule_key') == rule_key
                and a.get('record_id') == chosen['skillid'] and a.get('raw_value') == raw]
    val_hits = [a for a in base if a.get('rule_key') == rule_key
                and a.get('raw_value') == raw]
    conflicts = [a for a in base if a.get('rule_key') == rule_key
                 and a.get('raw_value') != raw]
    out['rules']['R8_cross'] = {'base_record_and_value_matches': rec_hits,
                                'base_value_only_matches': val_hits,
                                'base_conflicts': conflicts}
    if rec_hits:
        out['verdict'] = 'VALUE_AND_BINDING'
    elif val_hits:
        out['verdict'] = 'VALUE_ONLY_SAME_VALUE_DIFF_RECORD'
    else:
        out['verdict'] = 'FIELD_VALUE_ONLY'
    out['gates']['excluded_values'] = [{'record_id': a.get('record_id'),
                                        'raw_value': a.get('raw_value'),
                                        'row_id': a.get('row_id')} for a in conflicts]
    tag = base_answers_tag or []
    out['rules']['R8b_tag_normalized'] = {
        'record_and_value_matches': [a for a in tag if a.get('rule_key') == rule_key
                                     and a.get('record_id') == chosen['skillid']
                                     and a.get('raw_value') == raw],
        'conflicts': [a for a in tag if a.get('rule_key') == rule_key
                      and a.get('raw_value') != raw],
        'note': '敏感性披露：句首【…】展示标签不同但其余逐字相同；未作为准入判据',
    }
    if out['kind'] == 'CHARAINFO':
        first = next((c for c in children if c.get('slot') == 0), None)
        if first is not None:
            out['rules']['R8c_ten_slot'] = {
                'start_child': first['skillid'],
                'diff_vs_start_child': ten_slot_diff(parent['record'], first['record']),
                'damage_slot_equal': parent['record'].get(slot) == raw,
            }
    out['parent'] = {'table': parent['table'], 'pointer': parent['pointer'],
                     'pattern_id': parent['pattern_id'], 'entry': parent['entry'],
                     'record': parent['record']}
    out['pattern_record'] = pattern
    out['chosen_record'] = chosen['record']
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


def _answer(data, res, base_value_rows, excluded, same_value_existing, selection):
    selected = res['selected']
    slot, raw, rid = selected['slot'], selected['raw'], selected['skillid']
    rule_key = selected['rule_key']
    chosen = {'skillid': rid, 'index': selected['record_index'], 'type': selected['type'],
              'record': res['chosen_record']}
    source = _source_of(data, chosen, selected['slot'][1:], res['parent']['pointer'])
    pattern = res['pattern_record']
    num = _num_text(raw)
    condition = 'pattern%s / pattern %s 被选中时' % (
        'id0' if res['parent']['pointer'] == 'denju.patternid0' else '0',
        res['parent']['pattern_id'])
    base_ids = '、'.join(base_value_rows) or '（无）'
    if excluded:
        exc_txt = '、'.join('%s（%s）' % (_num_text(e[1]), e[0]) for e in excluded)
        exc_tail = '链外档位值 %s已排除、不计入本行' % exc_txt
    else:
        exc_tail = '本档为唯一档位（无链外档位值）'
    note_unique = ''
    if selection.get('record_note') == 'VALUE_UNIQUE_RECORD_NOT_UNIQUE':
        note_unique = '；同值异记录：%s 均为 %s（记录选取不唯一，值唯一）' % (
            '/'.join(str(c) for c in selection.get('records') or []), num)
    qk = ('直接范围伤害输入倍率' if selected['type'] == 74
          else '激光伤害输入倍率' if selected['type'] == 55
          else '单次对敌伤害输入倍率')
    value = ('%s：%s（相对B；对象：敌方；镜像行按原始链定源到 bossskill %s type%s %s，'
             '倍率见同卡基础档位行 %s；%s%s）'
             % (qk, num, rid, selected['type'], slot, base_ids, exc_tail, note_unique))
    conditions_raw = {k: pattern.get(k) for k in
                      ('flag', 'hpend', 'priority', 'scost', 'sname',
                       'skillid0', 'skillid1', 'skillid2', 'skillid3')
                      if pattern.get(k) is not None}
    conditions_raw['sinfo'] = pattern.get('sinfo')
    marker = {
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'gate': res['parent']['pointer'],
        'row_id': res['row_id'],
        'rule_key': rule_key,
        'record_id': rid,
        'layer': 'CACHE',
        'field_path': slot,
        'pattern_id': res['parent']['pattern_id'],
        'pattern_slot': res['parent']['pointer'],
        'origin': {'kind': res['parent']['pointer'],
                   'record_table': res['parent']['table'],
                   'patternid0' if res['parent']['pointer'] == 'denju.patternid0'
                   else 'pattern0': res['parent']['pattern_id'],
                   'denju_pointer': (res['parent']['entry'].get('source') or {}).get('json_pointer')
                   if res['parent']['pointer'] == 'denju.patternid0'
                   else (res['parent']['entry'].get('source') or {}).get('json_pointer')},
        'selection': selection,
        'base_row_ids': base_value_rows,
        'record_selection': selection.get('record_note') or 'RECORD_UNIQUE',
        'excluded_values': [[rid_, raw_] for rid_, raw_ in excluded],
        'value_basis': '同值已在同卡基础档位行同 rule_key 答案中披露；本行只做行级绑定，不新增唯一数值',
        'same_value_existing_answers': same_value_existing,
        'association': '推断',
        'native_evidence': 'none（本批不新增原生点；片段判别为类型语义＋一致性推断）',
        'conditions_raw': conditions_raw,
    }
    answer = {
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
        'context': '镜像段（传授/skilltext 行）',
        'condition_label': condition,
        'binding': {'g1_b1_binding': marker,
                    'g1_structure_binding': {'scope': STRUCTURE_SCOPE,
                                             'module': MODULE_VERSION,
                                             'verdict': res['verdict'],
                                             'dedup': 'NEW_ANSWER_NO_EXISTING_RULE_KEY'},
                    'fields': [{'f': slot, 'raw': raw}]},
        'target': '敌',
        'note': ('仅局部伤害输入公式（B=getBasicSkillAttack(true) 等沿用原规则定义），未验证'
                 '最终扣血、保证命中与运行时选档；抽取自本行原始链记录，非最终伤害。父条件'
                 '原值见 binding.g1_b1_binding.conditions_raw；缺失字段不补零；链外档位值已登记排除。'
                 '结构判定规则见 card_page_inference_g1_structure.py 模块头注 R1–R9。'),
        'evidence': ['docs/tasks/20261029-c7-p1-throughput-package.md',
                     'output/character_skills/c7_p1_20261029/build_report.md'],
    }
    return answer


def _append(row, answer, res, dedup):
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    if any(key(a) == key(answer) for a in row.get('answers') or []):
        return False
    row.setdefault('answers', []).append(answer)
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = ('推断（G1 结构族镜像行绑定：原始链定源；倍率见同卡基础档位行，'
                             '不新增唯一数值）')
    row['partial'] = True
    row['evidence_scope'] = list(dict.fromkeys(list(row.get('evidence_scope') or [])
                                              + ['BY_TYPE_EXTRAPOLATED']))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    try:
        import effect_ledger as _L
        residual = [w for w in _L._RESIDUAL_MECHANISM_WORDS
                    if w in str(row.get('japanese') or '')]
    except Exception:  # noqa: BLE001 - 反向依赖不可用时只写通用口径
        residual = []
    reasons.append('镜像行按原始链定源写入伤害倍率（同卡基础档位行同值、链外档位值已排除）；'
                   '同句其余机制%s仍未解析，账本行仍为拆分待核查。'
                   % (('（登记残差词：%s）' % '、'.join(residual)) if residual else
                      '（未被主张覆盖的子句）'))
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
        'layer': res['layer'],
        'verdict': res.get('verdict'),
        'dedup': dedup,
        'rule_key': selected.get('rule_key'),
        'record_id': selected.get('skillid'),
        'field_path': selected.get('slot'),
        'raw_value': selected.get('raw'),
        'raw_state': selected.get('raw_state'),
        'pattern_id': (res.get('parent') or {}).get('pattern_id'),
        'structure': {k: v for k, v in (res.get('rules') or {}).items()
                      if k in ('R4_clause', 'R5_select', 'R7_slot')},
        'R8_cross': res.get('rules', {}).get('R8_cross'),
        'excluded_values': (res.get('gates') or {}).get('excluded_values'),
        'note': ('结构判定 marker：不新增/不改写答案时也保留判定与披露；'
                 '同值异记录不升级为唯一来源已确认，不计账本新主张。'),
    }
    if extra:
        marker.update(extra)
    return marker


# ---------------------------------------------------------------- 正式页消费

def apply_to_groups(data, cid, groups):
    """正式页消费：按结构规则为镜像行写入绑定答案或行级 marker（不覆盖既有答案）。"""
    report = {'scope': STRUCTURE_SCOPE, 'cid': cid, 'evaluated': 0, 'answers_added': 0,
              'marker_only': 0, 'skipped_existing': 0, 'additions': [], 'markers': [],
              'rejections': [], 'out_of_scope': True}
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append({'reason': 'ZERO_TOUCH_CID', 'cid': cid})
        return report
    rows = [(g.get('group'), s, r) for g in groups or [] for s in g.get('skills') or []
            for r in s.get('rows') or []]
    mirrors = [(gn, s, r) for gn, s, r in rows
               if row_kind(gn, r.get('reference_field')) is not None]
    if not mirrors:
        return report
    report['out_of_scope'] = False
    # R8 交叉核来源：同卡 pattern* 行的全部答案（逐字同文 / 剥离句首标签两种口径）
    pattern_rows = [(gn, s, r) for gn, s, r in rows
                    if str(r.get('reference_field') or '').startswith('pattern')]
    # R6 注入性：同卡内 (pattern, 父文本) → 子记录 → 行
    injective = {}
    for gn, s, r in mirrors:
        if s.get('layer') != 'CACHE':
            continue
        form, detail = classify_clause(r.get('japanese'))
        if form is None or form == 'PLAIN':
            continue
        parent, err = resolve_parent(data, cid, row_kind(gn, r.get('reference_field')), 'CACHE')
        if err:
            continue
        _, pattern, children = children_of(data, 'CACHE', parent['pattern_id'])
        if pattern is None or not pattern.get('sinfo'):
            continue
        if canon(pattern.get('sinfo')) != canon(parent['text']):
            continue
        chosen, _sel = select_child(children, form, detail)
        if chosen is None:
            continue
        key = (parent['pattern_id'], canon(parent['text']))
        injective.setdefault(key, {}).setdefault(chosen['skillid'], []).append(r.get('row_id'))
    for gn, s, r in mirrors:
        layer = s.get('layer')
        row = dict(r)
        row['_group'] = gn
        parent, err = resolve_parent(data, cid, row_kind(gn, r.get('reference_field')), layer)
        inj = None
        base = base_tag = None
        if not err:
            inj = injective.get((parent['pattern_id'], canon(parent['text'])))
            base, base_tag = _base_answers(pattern_rows, r.get('japanese'))
        res = evaluate(data, cid, row, layer, injective=inj, base_answers=base,
                       base_answers_tag=base_tag)
        report['evaluated'] += 1
        if res['rejection']:
            if res['rejection'] not in ('NOT_A_MIRROR_ROW',):
                report['rejections'].append({'row_id': r.get('row_id'),
                                             'reason': res['rejection']})
            continue
        if res.get('verdict') is None or res.get('selected') is None:
            continue
        selected = res['selected']
        rule_key = selected['rule_key']
        same_key = [a for a in r.get('answers') or [] if a.get('rule_key') == rule_key]
        same_rec_value = [a for a in same_key
                          if a.get('record_id') == selected['skillid']
                          and a.get('raw_value') == selected['raw']]
        same_value = [a for a in same_key if a.get('raw_value') == selected['raw']]
        excluded = sorted({(e['record_id'], e['raw_value'])
                           for e in res['gates'].get('excluded_values') or []})
        existing_disclosure = [{'record_id': a.get('record_id'),
                                'raw_value': a.get('raw_value'),
                                'rule_key': a.get('rule_key')} for a in same_key]
        if same_rec_value:
            # R9 幂等：同记录同值答案已在行上 → 零写入（不写 marker，避免改动无关页面）。
            report['skipped_existing'] += 1
            report['markers'].append({'row_id': r.get('row_id'),
                                      'dedup': 'ALREADY_PRESENT_SAME'})
            continue
        if res['verdict'] != 'VALUE_AND_BINDING' and not same_key:
            # 未获同卡基础档位行「同记录同值」确认（VALUE_ONLY 记录不唯一 / FIELD_VALUE_ONLY
            # 无基础行）：只出字段值、不作描述绑定，**不写答案、不写 marker**（零写入）。
            report['field_value_only'] = report.get('field_value_only', 0) + 1
            report['markers'].append({'row_id': r.get('row_id'),
                                      'dedup': 'FIELD_VALUE_ONLY_NO_WRITE',
                                      'verdict': res['verdict'],
                                      'record_id': selected['skillid'],
                                      'raw_value': selected['raw']})
            continue
        if same_key and res['verdict'] != 'VALUE_AND_BINDING':
            # 未准入但本行已有同 rule_key 答案：只写 marker 披露同值异记录 / 异值冲突。
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
            _merge_marker(r, _row_marker(res, dedup,
                                         {'existing_answers': existing_disclosure,
                                          'disclosure': text}))
            report['marker_only'] += 1
            report['markers'].append({'row_id': r.get('row_id'), 'dedup': dedup,
                                      'verdict': res['verdict'],
                                      'record_id': selected['skillid'],
                                      'raw_value': selected['raw']})
            continue
        if same_key:
            dedup = ('SAME_VALUE_DIFF_RECORD_EXISTING' if same_value
                     else 'CONFLICT_EXISTING_VALUE')
            shown = '、'.join('%s=%s' % (d['record_id'], d['raw_value'])
                              for d in [{'record_id': a.get('record_id'),
                                         'raw_value': a.get('raw_value')} for a in same_key])
            if same_value:
                text = ('本行已有同 rule_key 答案（%s）；结构判定选中 %s=%s。'
                        '同值异记录：不得再新增同值答案，也不得改写为唯一来源已确认。'
                        % (shown, selected['skillid'], selected['raw']))
            else:
                text = ('本行已有同 rule_key 异值答案（%s）；结构判定选中 %s=%s 与既有值冲突，'
                        '不新增、不改值，保留待人工核实。'
                        % (shown, selected['skillid'], selected['raw']))
            extra = {'existing_answers': existing_disclosure, 'disclosure': text}
            _merge_marker(r, _row_marker(res, dedup, extra))
            report['marker_only'] += 1
            report['markers'].append({'row_id': r.get('row_id'), 'dedup': dedup,
                                      'record_id': selected['skillid'],
                                      'raw_value': selected['raw']})
            continue
        res['row_id'] = r.get('row_id')
        base_value_rows = sorted({a.get('row_id') for a in
                                  (res['rules'].get('R8_cross') or {}).get('base_record_and_value_matches')
                                  or []})
        answer = _answer(data, res, base_value_rows, excluded, existing_disclosure,
                         selected['selection'])
        if _append(r, answer, res, 'NEW_ANSWER_NO_EXISTING_RULE_KEY'):
            report['answers_added'] += 1
            report['additions'].append({'row_id': r.get('row_id'),
                                        'record_id': selected['skillid'],
                                        'rule_key': rule_key,
                                        'field_path': selected['slot'],
                                        'raw_value': selected['raw'],
                                        'verdict': res['verdict']})
    return report


def _merge_marker(row, marker):
    """写行级 marker；已有同键 marker 时只补披露字段，不重复添加答案。"""
    existing = row.get(MARKER_KEY)
    if isinstance(existing, dict):
        for k, v in marker.items():
            if k in ('structure', 'R8_cross') and isinstance(existing.get(k), dict):
                continue
            existing.setdefault(k, v)
        existing['dedup'] = marker.get('dedup')
        for k in ('existing_answers', 'disclosure'):
            if k in marker:
                existing[k] = marker[k]
        return existing
    row[MARKER_KEY] = marker
    return marker


def _base_answers(pattern_rows, japanese):
    """同卡同文 pattern 行上的全部答案 → (逐字同文, 剥离句首标签后同文)。"""
    target = canon(japanese)
    target_nt = canon_no_tag(japanese)
    exact, relaxed = [], []
    for gn, s, r in pattern_rows:
        ja = r.get('japanese')
        is_exact = canon(ja) == target
        is_relaxed = canon_no_tag(ja) == target_nt
        if not (is_exact or is_relaxed):
            continue
        for a in r.get('answers') or []:
            item = {'row_id': r.get('row_id'), 'rule_key': a.get('rule_key'),
                    'record_id': a.get('record_id'), 'raw_value': a.get('raw_value')}
            if is_exact:
                exact.append(item)
            if is_relaxed:
                relaxed.append(item)
    return exact, relaxed


# ---------------------------------------------------------------- 只读探针（wrapper）

def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='G1 结构族镜像行判定：只读探针（单行/单卡/全库）')
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
        cids = sorted(int(p.name) for p in pages.iterdir() if p.is_dir() and p.name.isdigit())
    data = D.Inputs(root, cids)
    out = []
    for cid in cids:
        card = json.loads((pages / str(cid) / 'card.json').read_text(encoding='utf-8'))
        rows = [(g.get('group'), s, r) for g in card.get('groups') or []
                for s in g.get('skills') or [] for r in s.get('rows') or []]
        mirrors = [(gn, s, r) for gn, s, r in rows
                   if row_kind(gn, r.get('reference_field')) is not None]
        pattern_rows = [(gn, s, r) for gn, s, r in rows
                        if str(r.get('reference_field') or '').startswith('pattern')]
        injective = {}
        for gn, s, r in mirrors:
            if s.get('layer') != 'CACHE':
                continue
            form, detail = classify_clause(r.get('japanese'))
            if form is None or form == 'PLAIN':
                continue
            parent, err = resolve_parent(data, cid, row_kind(gn, r.get('reference_field')), 'CACHE')
            if err:
                continue
            _, pattern, children = children_of(data, 'CACHE', parent['pattern_id'])
            if pattern is None or not pattern.get('sinfo'):
                continue
            if canon(pattern.get('sinfo')) != canon(parent['text']):
                continue
            chosen, _sel = select_child(children, form, detail)
            if chosen is None:
                continue
            injective.setdefault((parent['pattern_id'], canon(parent['text'])), {}) \
                .setdefault(chosen['skillid'], []).append(r.get('row_id'))
        for gn, s, r in mirrors:
            if args.row_id and r.get('row_id') != args.row_id:
                continue
            row = dict(r)
            row['_group'] = gn
            parent, err = resolve_parent(data, cid, row_kind(gn, r.get('reference_field')),
                                         s.get('layer'))
            inj = base = base_tag = None
            if not err:
                inj = injective.get((parent['pattern_id'], canon(parent['text'])))
                base, base_tag = _base_answers(pattern_rows, r.get('japanese'))
            res = evaluate(data, cid, row, s.get('layer'), injective=inj,
                           base_answers=base, base_answers_tag=base_tag)
            same_key = [a for a in r.get('answers') or []
                        if a.get('rule_key') == (res.get('selected') or {}).get('rule_key')]
            out.append({'cid': cid, 'row_id': r.get('row_id'),
                        'rejection': res['rejection'], 'verdict': res.get('verdict'),
                        'selected': {k: v for k, v in (res.get('selected') or {}).items()
                                     if k in ('skillid', 'type', 'slot', 'raw', 'rule_key')},
                        'existing_same_rule_key': [{'record_id': a.get('record_id'),
                                                    'raw_value': a.get('raw_value')}
                                                   for a in same_key],
                        'rules': {k: res['rules'].get(k) for k in
                                  ('R4_clause', 'R5_select', 'R7_slot')}})
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for item in out:
            print(item['cid'], item['row_id'], item.get('verdict') or item['rejection'],
                  (item.get('selected') or {}).get('skillid'),
                  (item.get('selected') or {}).get('raw'))
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
