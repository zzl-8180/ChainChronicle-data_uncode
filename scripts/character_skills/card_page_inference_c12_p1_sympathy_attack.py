# -*- coding: utf-8 -*-
"""C12-P1 ``skilllist|3000|``（共鳴アビリティ／Sympathy Support3）**首段**
攻撃力・クリティカル威力 段：候选实现。

任务卡 ``docs/tasks/20261031-c12-p1-sympathy-attack.md``；选题预检
``output/character_skills/c12_p1_selection_20261031/selection_report.md``（10/10 PASS）；
周期计划 ``docs/tasks/20261031-c11-c13-three-cycle-plan.md``。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；正式页面、
``rules.json``、``effect_ledger`` 均未改动；正式全库生成与全库检查不在本阶段。账本所需
**0 条新映射**——``scripts/character_skills/effect_ledger.py:469-470`` 已有 3000 的
``/param1``→攻撃力、``/param2``→攻撃力、``/param8``→クリティカル威力、``/param6``→継続時間
四条键精确映射，本批直接复用其中三条值槽。

句子与范围
----------
只有一条句式（记录正文**首段**，页面 ``fragment_index == 0``，row_id 尾部 ``-f0``）::

    【共鳴アビリティ】自身を含む<味方>が≪共鳴必殺≫を発動するたび、
    戦場にいる<味方>の<属性A>と<属性B>[と<属性C>]が一定時間上がる。
    （回復形态尾句：…が一定時間上がり、HPが上限を超えて回復する。）

属性取自「攻撃力／防御力／移動速度／クリティカル発生率／クリティカル威力／回復」，
顺序与记录活性槽 1:1。本批只对**已确认槽**出值：

* 攻撃力 → ``/param1``（普通攻击加算增量）＋ ``/param2``（技能攻击加算增量）＝**2 条**
* クリティカル威力 → ``/param8``（暴伤系数加算）＝**1 条**
* 其余属性（防御力→p4、移動速度→p3、クリティカル発生率→p7、回復→p5）**无规则**，
  本批**不出值**，也不按相关性猜槽位（p4 原值为负、与「上がる」句向矛盾，批 7 已登记）。
* ``/param6``（45 游戏秒）**已有答案**：本批不重复、不改写，并以其一致性作为准入条件。

首段之后的 ``この効果は、サブパーティでも発動する。`` 是**同记录的第二片段行**（``-f1``），
本批零触碰，也不归属其条件语义。

0 新公式、0 新规则键、0 新原生、0 新账本映射
--------------------------------------------
三条换算全部复用 ``profiles/rules.json`` 已确认的 ``skilllist|3000|/param1../param8``；
本模块通过 ``rules.answer_for('skilllist', 3000, '/paramN', raw, record, source_layer='CACHE')``
取 ``unit/quantity_kind/conversion/conditions/rule_status/rule_limits/value_text``，
**不在本批重写公式**，也不写 ``_RULE_KEY_EFFECT``。

证据档（按预检保守口径，不得升格）
----------------------------------
* 规则体状态 ``已确认（静态及受控原生局部规则）``（rules.json 原文）——本模块照抄披露。
* **本批不做逐记录执行确认**，因此答案 ``numeric_evidence`` 与 ``association_evidence``
  一律为 ``推断``，``evidence_scope`` 用本批独立 scope
  ``TEMPLATE_BATCH12_P1_SYMPATHY_ATTACK``（预检 §6.4 建议值），不沿用批 7 的 scope。
* ``answer_status`` 沿用规则／页面既有口径 ``CONFIRMED_NUMERIC``，不新增状态词。

b7 hint 与 S3 **保留**（不拆半晋级、不宣称整行完整）
----------------------------------------------------
* **不写** ``row['binding_conditions']``，不清任何 split 标记，不改 ``partial``／``row_class``；
* 不删 ``inference_b7_hint``，也不从 ``unknown_reasons`` 移除该 G4 hint 文本；
* 行仍「拆分待核查」：触发子句（``【共鳴アビリティ】…発動するたび``）不在本批答案覆盖内，
  账本 S3 原样保留；完整行增量 0。

准入是**结构规则 + 显式批次边界**，不是 row_id／记录／原值白名单
--------------------------------------------------------------
模块内没有任何 row_id、卡号、记录号或「原值 == 字面量」常量（``candidate/run_checks.py``
的静态扫描用例断言这一点）。判定顺序：

    D1 行身份：``group == 'sympathy'``、``reference_field ==
       'sympathy_skill_info[_id=<cid>].ability0'``、``fragment_index == 0``，
       且日语按结构解析出属性序列（前缀／两种尾句逐字，属性必须来自六属性表、无重复、含攻撃力）。
    D2 同层来源：``layer == 'CACHE'``、``source_key == CACHE/skilllist.data5.json.raw``、
       ``field == '/text'``、``json_pointer`` 匹配 ``/skilllist/<n>``；不读 APK 表。
    D3 父链一致：``sympathy_skillinfo[_id=<cid>].ability0`` = 页面载体记录号；
       ``skilllist`` 中该 ``skillid`` 全表唯一命中，下标就是 D2 的 ``<n>``；记录 ``ability``
       ＝ 3000；页面载体表/层/记录一致。
    D4 槽位（**只消费已确认槽，且与句面主张严格 1:1**）：
       ``param0`` 整型且让提供者自身参与（句面「自身を含む」）；``param1``/``param2`` 有限正、
       落在加算增量域 (0,1]；``param6`` 有限正（时长已有答案）；``param8`` 仅在句面主张
       クリティカル威力时存在且落在 (0,1]；**防御力/移動速度/クリ発生率/回復 四项槽
       有值 ⇔ 句面点名该属性**，任一方向不符即拒绝（不猜槽位、不静默忽略）；
       ``flag1_1``（512，与「HPが上限を超えて回復する」1:1）只作机制披露、不消费；
       ``param9/iParam0/iParam1/flag0_x/flag1_0`` 非零拒绝；``flag`` 非零拒绝；``sub`` 非空拒绝。
    D5 段落与唯一性：句面是记录正文的**第 1 个句子单位**、在记录内唯一出现；
       记录其余句子单位只能是 ``この効果は、サブパーティでも発動する。``；同卡该
       ``reference_field`` 内恰 1 行可解析（不抢子句）；该 ``-f1`` 行必须存在且不可被本批解析。
    D6 规则语义：p1/p2(/p8) 的 ``answer_for`` 必须返回非空，``meaning_zh`` 含对应属性关键词
       （普通攻击／技能攻击／暴击伤害）。规则语义漂移即拒绝。
    D7 幂等：本行 ``/param6`` 答案必须存在、唯一、与本记录原值一致（保护 p6）；
       本批值槽同键已有答案——同记录同字段同原值同层 → ``ALREADY_PRESENT_SAME``（零写入）；
       其余 → ``ALREADY_ANSWERED``（只写披露 marker，不改写既有答案）。

**批次边界由调用方显式声明**：``apply_to_groups(data, cid, groups, *, scope_cids=...)``，缺省
``None`` → 一行都不处理（``NO_SCOPE_DECLARED``）。保护卡 20234／30102／30236／30239 在模块内
硬拒绝（30102 为禁推卡；30236／30239 为保护卡，豁免不扩大）。

接口
----
``evaluate(data, cid, row, rows=None, skill=None, tab=None)``  单行判定（不写入）。
``build_answers(data, cid, row, res, tab=None)``                 2/3 条答案对象（复用 rules）。
``apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None)`` 正式页消费（候选未接线）。
``tables(data)`` / ``clone_tables(tab)``                         CACHE 主表只读索引（可注入，反例用）。
"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

MODULE_VERSION = 'c12_p1_sympathy_attack_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 本批证据 scope（写进答案 binding，供账本/页面按 scope 精确消费时对账）。
SCOPE = 'TEMPLATE_BATCH12_P1_SYMPATHY_ATTACK'
#: 结构判定自身 scope（行级 marker）。
STRUCTURE_SCOPE = 'C12_P1_SYMPATHY_ATTACK_STRUCTURE_20261031'
#: 行级 marker 键（每行至多一个本批键，不覆盖其他批的 marker）。
MARKER_KEY = 'inference_c12_p1_sympathy_attack'

#: 本族载体：skilllist 的 ability 3000（元数据 Sympathy／Support3）。
TABLE = 'skilllist'
ABILITY = 3000
LAYER = 'CACHE'
REF_TEMPLATE = 'sympathy_skill_info[_id=%d].ability0'
TEXT_FIELD = '/text'
SOURCE_KEY = 'CACHE/skilllist.data5.json.raw'
#: CACHE 解码主表目录（与预检、C11 各批同源快照）。
BASE = 'output/cache_full_20261015_v3/decoded'
#: 共鸣索引表：``sympathy_skill_info[_id=<cid>].ability0`` → skilllist 记录号。
SYMPATHY_TABLE = 'sympathy_skilllist.data5.json.raw'
SYMPATHY_KEY = 'sympathy_skill_info'
SYMPATHY_ID = '_id'
SYMPATHY_FIELD = 'ability0'

#: 保护／禁推卡：本批零触碰（判定前硬拒绝）。30102 禁推卡；30236／30239 保护卡；
#: 20234 为既有边界（本批不涉及，保留硬拒绝以防误扩）。
ZERO_TOUCH_CIDS = frozenset({20234, 30102, 30236, 30239})

#: 记录正文用**字面**反斜线＋n 分段（不是控制字符）；此常量避免源码里写转义序列。
_TEXT_SEP = chr(92) + 'n'
#: 本批句面所在片段（0 基）：首段。
TARGET_FRAGMENT_INDEX = 0
#: 句面前缀（逐字）：共鳴アビリティ 的触发子句 + 对象 + 「の」。
SENTENCE_PREFIX = ('【共鳴アビリティ】自身を含む<味方>が≪共鳴必殺≫を発動するたび、'
                   '戦場にいる<味方>の')
#: 两种逐字尾句（无回復／HP上限超回復）。
SUFFIX_PLAIN = 'が一定時間上がる。'
SUFFIX_HEAL = 'が一定時間上がり、HPが上限を超えて回復する。'
#: 同记录第二片段的逐字句（不归属、零触碰；D5 用于形状守卫）。
TRAILING_CLAUSE = 'この効果は、サブパーティでも発動する。'
#: 句面点名的属性全集（顺序即槽位顺序证据）。
ATTR_ORDER = ('攻撃力', '防御力', '移動速度', 'クリティカル発生率', 'クリティカル威力', '回復')
#: 已确认槽：属性 → (字段, 证据 scope, 规则 meaning_zh 关键词)。
#: 关键词是 D6 语义守卫：规则文本一变即拒绝，不静默沿用本表。
CONFIRMED_SLOTS = {
    '攻撃力': (('/param1', '普通攻击'), ('/param2', '技能攻击')),
    'クリティカル威力': (('/param8', '暴击伤害'),),
}
#: 未确认槽：属性 → 字段。skilllist|3000 **没有** p3/p4/p5/p7 规则，本批不得出值。
UNCONFIRMED_SLOTS = {
    '防御力': '/param4',
    '移動速度': '/param3',
    'クリティカル発生率': '/param7',
    '回復': '/param5',
}
#: 加算增量域：p1/p2/p8 只接受 (0,1]（大于 1 会被误读成乘数，拒绝）。
INCREMENT_MAX = 1.0
#: 「自身を含む」⇒ param0 必须让提供者自身参与。
PARAM0_SELF_INCLUSIVE = 1
#: 句面未主张的辅助筛位：必须缺省/零（不隐藏未知机制）。
AUX_SLOTS = ('param9', 'iParam0', 'iParam1', 'flag0_0', 'flag0_1', 'flag1_0')
#: 与「HPが上限を超えて回復する」1:1 的机制标记：只披露、不消费。
HEAL_FLAG_SLOT = 'flag1_1'
#: p6 规则键（已有答案，本批只保护、不重复）。
P6_RULE_KEY = '%s|%d|/param6' % (TABLE, ABILITY)

#: 页面既有答案里本批上线前应被本批替换为「已解」的通用未知原因（逐字）。
_STALE_REASONS = (
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '旧关键词候选未作为答案；不能排除对象或效果错配',
)
RESIDUAL_NOTE = ('C12-P1：首段 3000 记录 p1/p2(/p8) 按已确认换算给值（原值与关联证据档均为推断，'
                 '未做逐记录执行确认）；防御力/移動速度/クリ発生率/回復 仍未知，p3/p4/p5/p7 不消费；'
                 'p6 已有 45 游戏秒答案不改；b7 hint 与 S3 保留，行仍「拆分待核查」')
RESIDUAL_LABEL = ('推断（C12-P1：3000 首段 p1/p2(/p8) 加算增量；防御/移速/クリ発生率/回復 未确认，'
                  'S3 与 b7 hint 保留）')

_TABLES = {}

_SENTENCE_UNIT_SPLIT = re.compile(r'(?<=。)|[\r\n]')


# ---------------------------------------------------------------- 基础工具

def num_text(value):
    """有限数值的稳定文本（不引入千分位、不用科学计数法）。"""
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
    """缺失 / null / 非有限 / 非数值 / 负值 / 真零 / 有限分开标注（不把任何一档补成 0）。"""
    if not present:
        return 'MISSING'
    if raw is None:
        return 'NULL'
    if isinstance(raw, bool):
        return 'NON_FINITE'
    if not isinstance(raw, (int, float)):
        return 'NOT_NUMERIC'
    try:
        f = float(raw)
    except (TypeError, ValueError):
        return 'NOT_NUMERIC'
    if not math.isfinite(f):
        return 'NON_FINITE'
    if f < 0:
        return 'NEGATIVE'
    if f == 0:
        return 'ZERO'
    return 'FINITE'


def _int_or_zero(record, name):
    """整型筛位读取：缺失/显式 null 按 0（原生 get_* 缺省口径），非整型/非有限单独标注。"""
    if name not in record:
        return 0, 'missing'
    value = record.get(name)
    if value is None:
        return 0, 'null'
    if isinstance(value, bool):
        return None, 'invalid'
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None, 'invalid'
    if not math.isfinite(f):
        return None, 'invalid'
    if f != int(f):
        return None, 'non_integral'
    return int(f), 'present'


def _slot_value(record, name):
    """槽位数值视图：缺省/显式 null → 0.0；非数值/非有限 → None（单独拒绝）。"""
    if name not in record or record[name] is None:
        return 0.0
    value = record[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(float(value)):
        return None
    return float(value)


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


# ---------------------------------------------------------------- CACHE 主表

def tables(data):
    """CACHE 解码主表（按 root 缓存，只读）。``tab`` 可由调用方注入（反例用）。

    ``skills`` 保留**数组下标**（行来源 ``/skilllist/<n>`` 按下标解析）；``by_id`` 是按
    skillid 的索引视图，二者须指向同一条记录才放行。``sympathy`` 是
    ``sympathy_skill_info[_id=<cid>].ability0`` 的索引。
    """
    root = Path(getattr(data, 'root', Path('.'))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = root / BASE
        skilllist = _read(base / 'skilllist.data5.json.raw')['skilllist']
        skills = {}
        for index, record in enumerate(skilllist):
            if record.get('skillid') is not None:
                skills.setdefault(record['skillid'], []).append((index, record))
        sympathy = {entry[SYMPATHY_ID]: entry
                    for entry in _read(base / SYMPATHY_TABLE)[SYMPATHY_KEY]}
        _TABLES[key] = dict(skills=skills, sympathy=sympathy, root=root)
    return _TABLES[key]


def clone_tables(tab):
    """反例用：深拷贝只读索引（不改动全局缓存）。"""
    return {k: (copy.deepcopy(v) if k in ('skills', 'sympathy') else v) for k, v in tab.items()}


# ---------------------------------------------------------------- 句面

def parse_sentence(japanese):
    """结构解析本族首段句；返回 ``(attrs, detail)``，不匹配返回 ``(None, detail)``。

    attrs 是句面点名的属性序列（回復形态在末尾补 ``回復``）。缺前缀、尾句不符、
    属性不在六属性表、属性重复、缺攻撃力、把回復写进「と」链、追加尾句、
    「全状態異常を回復する」等越界句一律不匹配（不走正则近似，避免半句被消费）。
    """
    text = str(japanese or '')
    if not text:
        return None, {'reason': 'ROW_TEXT_EMPTY'}
    if not text.startswith(SENTENCE_PREFIX):
        return None, {'reason': 'SENTENCE_NOT_SYMPATHY',
                      'has_prefix': False,
                      'has_trailing_clause': text == TRAILING_CLAUSE}
    rest = text[len(SENTENCE_PREFIX):]
    if rest.endswith(SUFFIX_HEAL):
        body, heal = rest[:-len(SUFFIX_HEAL)], True
    elif rest.endswith(SUFFIX_PLAIN):
        body, heal = rest[:-len(SUFFIX_PLAIN)], False
    else:
        return None, {'reason': 'SENTENCE_SUFFIX_NOT_SYMPATHY', 'tail': rest[-40:]}
    parts = tuple(body.split('と'))
    detail = {'reason': None, 'attrs': parts, 'heal_suffix': heal, 'length': len(text)}
    if not parts or any(not p for p in parts):
        return None, dict(detail, reason='SENTENCE_ATTR_EMPTY')
    unknown = [p for p in parts if p not in ATTR_ORDER]
    if unknown:
        return None, dict(detail, reason='SENTENCE_ATTR_UNKNOWN', unknown=unknown)
    if len(set(parts)) != len(parts):
        return None, dict(detail, reason='SENTENCE_ATTR_DUPLICATED')
    if '回復' in parts:
        return None, dict(detail, reason='SENTENCE_HEAL_IN_ATTR_CHAIN')
    if '攻撃力' not in parts:
        return None, dict(detail, reason='SENTENCE_ATTACK_NOT_CLAIMED')
    attrs = parts + (('回復',) if heal else ())
    return attrs, dict(detail, attrs=attrs, form='+'.join(attrs))


def sentence_units(record_text):
    """记录正文的句子单位（与页面 fragment 切分同口径：句末「。」／换行）。"""
    cleaned = str(record_text or '').replace(_TEXT_SEP, '\n')
    return [unit for unit in _SENTENCE_UNIT_SPLIT.split(cleaned) if unit.strip()]


def claims_view(attrs):
    """属性序列 → (已确认属性, 未确认属性, 预期值槽)。"""
    confirmed = [a for a in attrs if a in CONFIRMED_SLOTS]
    unconfirmed = [a for a in attrs if a in UNCONFIRMED_SLOTS]
    slots = []
    for attr in confirmed:
        for field, _needle in CONFIRMED_SLOTS[attr]:
            slots.append((field, attr))
    return confirmed, unconfirmed, slots


# ---------------------------------------------------------------- 单行判定

def _param_view(record, name):
    return {'present': name in record,
            'raw_state': raw_state(record.get(name), name in record), 'raw': record.get(name)}


def evaluate(data, cid, row, rows=None, skill=None, tab=None):
    """单行判定（不写入）。``rows`` 为同卡页面全部行（D5 句面唯一性）。"""
    rid = row.get('row_id')
    out = {'row_id': rid, 'cid': cid, 'module': MODULE_VERSION, 'accepted': False,
           'rejection': None, 'rejection_detail': None, 'gates': {}, 'slots': [],
           'claims': [], 'unconfirmed': []}
    if cid in ZERO_TOUCH_CIDS:
        out['rejection'] = 'ZERO_TOUCH_CID'
        return out
    # D1 行身份
    if row.get('group') != 'sympathy':
        out['rejection'] = 'NOT_SYMPATHY_GROUP'
        out['rejection_detail'] = {'group': row.get('group')}
        return out
    ref = str(row.get('reference_field') or '')
    if ref != REF_TEMPLATE % cid:
        out['rejection'] = 'NOT_SYMPATHY_ABILITY0_ROW'
        out['rejection_detail'] = {'reference_field': ref,
                                   'expected': REF_TEMPLATE % cid}
        return out
    fragment = row.get('fragment_index')
    if not isinstance(fragment, int) or fragment != TARGET_FRAGMENT_INDEX:
        out['rejection'] = 'NOT_FIRST_FRAGMENT'
        out['rejection_detail'] = {'fragment_index': fragment,
                                   'target': TARGET_FRAGMENT_INDEX}
        return out
    attrs, detail = parse_sentence(row.get('japanese'))
    out['gates']['clause'] = dict(detail)
    if attrs is None:
        out['rejection'] = detail.get('reason') or 'SENTENCE_NOT_SYMPATHY'
        return out
    confirmed, unconfirmed, value_slots = claims_view(attrs)
    out['claims'] = list(attrs)
    out['unconfirmed'] = list(unconfirmed)
    # D2 同层来源
    src = row.get('source') or {}
    out['gates']['row_source'] = {k: src.get(k) for k in
                                  ('source_key', 'layer', 'field', 'json_pointer', 'record_key')}
    if src.get('layer') != LAYER or src.get('source_key') != SOURCE_KEY:
        out['rejection'] = 'ROW_LAYER_NOT_CACHE'
        return out
    if str(src.get('field') or '') != TEXT_FIELD:
        out['rejection'] = 'ROW_FIELD_NOT_TEXT'
        return out
    pointer = str(src.get('json_pointer') or '')
    if not pointer.startswith('/skilllist/'):
        out['rejection'] = 'ROW_POINTER_NOT_SKILLLIST'
        out['rejection_detail'] = {'json_pointer': pointer}
        return out
    tail = pointer[len('/skilllist/'):]
    if not tail.isdigit():
        out['rejection'] = 'ROW_POINTER_NOT_SKILLLIST'
        out['rejection_detail'] = {'json_pointer': pointer}
        return out
    index = int(tail)
    out['gates']['record_index'] = index
    tab = tab or tables(data)
    entry = tab['sympathy'].get(cid)
    if entry is None:
        out['rejection'] = 'SYMPATHY_ENTRY_MISSING'
        return out
    parent_id = entry.get(SYMPATHY_FIELD)
    out['gates']['sympathy'] = {'cid': cid, SYMPATHY_ID: entry.get(SYMPATHY_ID),
                                SYMPATHY_FIELD: parent_id}
    if isinstance(parent_id, bool) or not isinstance(parent_id, int):
        out['rejection'] = 'SYMPATHY_POINTER_NOT_INTEGER'
        out['rejection_detail'] = {'ability0': parent_id}
        return out
    if skill is not None:
        if skill.get('table') != TABLE or skill.get('layer') != LAYER:
            out['rejection'] = 'SKILL_CARRIER_NOT_CACHE_SKILLLIST'
            return out
        if skill.get('record_id') != parent_id:
            out['rejection'] = 'SKILL_RECORD_MISMATCH'
            out['rejection_detail'] = {'skill_record_id': skill.get('record_id'),
                                       'sympathy': parent_id}
            return out
    # D3 父链一致
    hits = tab['skills'].get(parent_id) or []
    if len(hits) != 1:
        out['rejection'] = 'SKILL_NOT_UNIQUE(%d)' % len(hits)
        return out
    rec_index, record = hits[0]
    out['gates']['record'] = {'skillid': parent_id, 'index': rec_index,
                              'pointer_index': index, 'index_matches_pointer': rec_index == index,
                              'ability': record.get('ability'),
                              'sub': list(record.get('sub') or ()),
                              'name': record.get('name')}
    if rec_index != index:
        out['rejection'] = 'PARENT_POINTER_MISMATCH'
        out['rejection_detail'] = {'pointer_index': index, 'record_index': rec_index}
        return out
    if record.get('ability') != ABILITY:
        out['rejection'] = 'ABILITY_NOT_3000'
        out['rejection_detail'] = {'ability': record.get('ability')}
        return out
    if record.get('sub'):
        out['rejection'] = 'SUB_RECORDS_PRESENT'
        out['rejection_detail'] = {'sub': record.get('sub')}
        return out
    # D4a 已确认槽逐档独立拒绝，不补 0
    params = {}
    for name in ('param0', 'param1', 'param2', 'param6', 'param8'):
        params[name] = _param_view(record, name)
    out['gates']['params'] = params
    for name in ('param0', 'param1', 'param2', 'param6'):
        state = params[name]['raw_state']
        if state != 'FINITE':
            out['rejection'] = 'PARAM_%s_%s' % (name.upper(), state)
            out['rejection_detail'] = {'slot': name, 'state': state, 'raw': params[name]['raw']}
            return out
    p0 = float(params['param0']['raw'])
    if p0 != int(p0):
        out['rejection'] = 'PARAM0_NOT_INTEGRAL'
        return out
    first = int(p0)
    if first > PARAM0_SELF_INCLUSIVE:
        out['rejection'] = 'PARAM0_OUT_OF_DOMAIN'
        out['rejection_detail'] = {'param0': record.get('param0'),
                                   'documented_max': PARAM0_SELF_INCLUSIVE}
        return out
    if first != PARAM0_SELF_INCLUSIVE:
        out['rejection'] = 'PARAM0_NOT_SELF_INCLUSIVE'
        out['rejection_detail'] = {'param0': record.get('param0'),
                                   'sentence': '自身を含む<味方>'}
        return out
    p1 = float(params['param1']['raw'])
    p2 = float(params['param2']['raw'])
    if not (0 < p1 <= INCREMENT_MAX and 0 < p2 <= INCREMENT_MAX):
        out['rejection'] = 'PARAM12_NOT_INCREMENT_RANGE'
        out['rejection_detail'] = {'param1': p1, 'param2': p2, 'domain': [0, INCREMENT_MAX]}
        return out
    # D4b 句面 ↔ 槽位 1:1（含未确认四槽与 p8）
    slot_values = {}
    for attr, field in UNCONFIRMED_SLOTS.items():
        name = field.lstrip('/')
        value = _slot_value(record, name)
        if value is None:
            out['rejection'] = 'SLOT_NOT_NUMERIC'
            out['rejection_detail'] = {'slot': name, 'raw': record.get(name)}
            return out
        slot_values[name] = value
        if attr in attrs and value == 0:
            out['rejection'] = 'CLAIM_WITHOUT_SLOT'
            out['rejection_detail'] = {'attr': attr, 'slot': name, 'raw': record.get(name)}
            return out
        if attr not in attrs and value != 0:
            out['rejection'] = 'SLOT_WITHOUT_CLAIM'
            out['rejection_detail'] = {'attr': attr, 'slot': name, 'raw': record.get(name)}
            return out
    p8 = _slot_value(record, 'param8')
    if p8 is None:
        out['rejection'] = 'SLOT_NOT_NUMERIC'
        out['rejection_detail'] = {'slot': 'param8', 'raw': record.get('param8')}
        return out
    slot_values['param8'] = p8
    crit_claimed = 'クリティカル威力' in attrs
    if crit_claimed:
        state = params['param8']['raw_state']
        if state != 'FINITE' or not (0 < p8 <= INCREMENT_MAX):
            out['rejection'] = 'PARAM_PARAM8_%s' % state
            out['rejection_detail'] = {'slot': 'param8', 'state': state,
                                       'raw': record.get('param8'),
                                       'domain': [0, INCREMENT_MAX]}
            return out
    elif p8 != 0:
        out['rejection'] = 'SLOT_WITHOUT_CLAIM'
        out['rejection_detail'] = {'attr': 'クリティカル威力', 'slot': 'param8',
                                   'raw': record.get('param8')}
        return out
    # D4c 辅助筛位／机制标记
    for name in AUX_SLOTS:
        value, state = _int_or_zero(record, name)
        if state in ('invalid', 'non_integral') or value:
            out['rejection'] = 'AUX_SLOT_NONZERO'
            out['rejection_detail'] = {'slot': name, 'raw': record.get(name), 'state': state}
            return out
    flag, flag_state = _int_or_zero(record, 'flag')
    if flag_state in ('invalid', 'non_integral') or flag:
        out['rejection'] = 'FLAG_UNSUPPORTED'
        out['rejection_detail'] = {'flag': record.get('flag'), 'state': flag_state}
        return out
    heal_flag, heal_state = _int_or_zero(record, HEAL_FLAG_SLOT)
    if heal_state in ('invalid', 'non_integral'):
        out['rejection'] = 'FLAG1_1_NOT_INTEGRAL'
        out['rejection_detail'] = {'slot': HEAL_FLAG_SLOT, 'raw': record.get(HEAL_FLAG_SLOT)}
        return out
    if bool(heal_flag) != ('回復' in attrs):
        out['rejection'] = 'FLAG1_1_CLAIM_MISMATCH'
        out['rejection_detail'] = {'slot': HEAL_FLAG_SLOT, 'raw': record.get(HEAL_FLAG_SLOT),
                                   'heal_claimed': '回復' in attrs}
        return out
    out['gates']['slot_values'] = {'param1': p1, 'param2': p2, 'param6': float(
        params['param6']['raw']), 'param8': p8,
        'unconfirmed': {k: slot_values[k] for k in
                        (f.lstrip('/') for f in UNCONFIRMED_SLOTS.values())},
        'heal_flag1_1': heal_flag}
    # D5 段落与唯一性
    record_text = str(record.get('text') or '')
    body = str(row.get('japanese') or '')
    units = sentence_units(record_text)
    occurrences = record_text.count(body)
    trailing = units[1:]
    out['gates']['segment'] = {
        'units': len(units),
        'sentence_is_first_unit': bool(units) and units[0] == body,
        'occurrences_in_record': occurrences,
        'trailing_units': trailing,
        'trailing_clause_only': trailing in ([], [TRAILING_CLAUSE]),
        'target_fragment_index': TARGET_FRAGMENT_INDEX,
        'sub_consumed': False,
    }
    if not units or body not in record_text:
        out['rejection'] = 'SENTENCE_NOT_IN_RECORD'
        return out
    if occurrences != 1:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_RECORD'
        out['rejection_detail'] = {'occurrences': occurrences}
        return out
    if units[0] != body:
        out['rejection'] = 'SENTENCE_NOT_FIRST_UNIT'
        out['rejection_detail'] = {'units': units[:2]}
        return out
    if trailing not in ([], [TRAILING_CLAUSE]):
        out['rejection'] = 'TRAILING_CLAUSE_UNEXPECTED'
        out['rejection_detail'] = {'trailing_units': trailing}
        return out
    siblings = []
    trailing_rows = []
    if isinstance(rows, dict):
        for other in rows.values():
            if str(other.get('reference_field') or '') != ref:
                continue
            if other.get('row_id') == rid:
                continue
            other_attrs, _od = parse_sentence(other.get('japanese'))
            if other_attrs is not None:
                siblings.append(other.get('row_id'))
            if other.get('japanese') == TRAILING_CLAUSE:
                trailing_rows.append((other.get('row_id'), other.get('fragment_index')))
    out['gates']['sentence_rows'] = siblings
    out['gates']['trailing_rows'] = trailing_rows
    if siblings:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_SCOPE'
        out['rejection_detail'] = {'siblings': siblings}
        return out
    if trailing and len(trailing_rows) != 1:
        out['rejection'] = 'TRAILING_ROW_MISSING'
        out['rejection_detail'] = {'trailing_rows': trailing_rows}
        return out
    # D6 规则语义（已确认槽 answer_for 非空 + meaning 关键词）
    import rules as R
    slots = []
    for field, attr in value_slots:
        name = field.lstrip('/')
        needle = next(n for f, n in CONFIRMED_SLOTS[attr] if f == field)
        answer = None
        try:
            answer = R.answer_for(TABLE, ABILITY, field, record.get(name), record,
                                  source_layer=LAYER)
        except Exception as exc:  # pragma: no cover - 规则导入失败即拒绝，不静默
            out['rejection'] = 'RULE_LOOKUP_ERROR'
            out['rejection_detail'] = {'slot': name, 'error': repr(exc)}
            return out
        if not answer:
            out['rejection'] = 'RULE_SLOT_UNCONFIRMED'
            out['rejection_detail'] = {'slot': name}
            return out
        meaning = str(answer.get('meaning_zh') or '')
        if needle not in meaning:
            out['rejection'] = 'RULE_SEMANTICS_CHANGED'
            out['rejection_detail'] = {'slot': name, 'meaning_zh': meaning,
                                       'expected_keyword': needle}
            return out
        if answer.get('answer_status') != 'CONFIRMED_NUMERIC':
            out['rejection'] = 'RULE_ANSWER_STATUS_UNEXPECTED'
            out['rejection_detail'] = {'slot': name,
                                       'answer_status': answer.get('answer_status')}
            return out
        slots.append({'slot': name, 'field': field, 'attr': attr,
                      'evidence_scope': SCOPE, 'raw': record.get(name), 'rule': answer})
    out['gates']['rule_slots'] = [
        {'slot': s['slot'], 'meaning_zh': s['rule'].get('meaning_zh'),
         'rule_key': '%s|%d|%s' % (TABLE, ABILITY, s['field']),
         'raw': s['raw'], 'evidence_scope': s['evidence_scope']} for s in slots]
    # D7 幂等 / p6 保护
    existing = [a for a in (row.get('answers') or [])
                if str(a.get('rule_key') or '') == P6_RULE_KEY]
    out['gates']['p6_answers'] = [{'raw_value': a.get('raw_value'),
                                   'record_id': a.get('record_id'),
                                   'field_path': a.get('field_path'),
                                   'layer': a.get('layer')} for a in existing]
    if len(existing) != 1:
        out['rejection'] = 'P6_ANSWER_MISSING' if not existing else 'P6_ANSWER_DUPLICATED'
        return out
    p6 = existing[0]
    p6_raw = p6.get('raw_value')
    p6_ok = (p6.get('record_id') == parent_id and p6.get('field_path') == '/param6'
             and p6.get('layer') == LAYER
             and not isinstance(p6_raw, bool)
             and isinstance(p6_raw, (int, float))
             and math.isfinite(float(p6_raw))
             and float(p6_raw) == float(params['param6']['raw']))
    if not p6_ok:
        out['rejection'] = 'P6_ANSWER_INCONSISTENT'
        out['rejection_detail'] = {'answer': {k: p6.get(k) for k in
                                              ('record_id', 'field_path', 'layer', 'raw_value')},
                                   'record_param6': params['param6']['raw']}
        return out
    out['accepted'] = True
    out['record'] = {'skillid': parent_id, 'index': rec_index,
                     'ability': record.get('ability'), 'layer': LAYER,
                     'sub': list(record.get('sub') or ()),
                     'name': record.get('name'),
                     'param0': record.get('param0'),
                     'param1': record.get('param1'),
                     'param2': record.get('param2'),
                     'param6': record.get('param6'),
                     'param8': record.get('param8'),
                     'param3': record.get('param3'),
                     'param4': record.get('param4'),
                     'param5': record.get('param5'),
                     'param7': record.get('param7'),
                     'flag1_1': record.get(HEAL_FLAG_SLOT),
                     'flag': record.get('flag')}
    out['sentence'] = {'text': body, 'attrs': list(attrs),
                       'form': '+'.join(attrs),
                       'fragment_index': TARGET_FRAGMENT_INDEX,
                       'trailing_clause': TRAILING_CLAUSE if trailing else None,
                       'units': len(units)}
    out['slots'] = slots
    return out


# ---------------------------------------------------------------- 答案对象

def _answer_key(field):
    return '%s|%d|%s' % (TABLE, ABILITY, field)


def _common_text(res, record):
    """条件／对象／未知／S3 的公共表述（数值全部来自记录与规则，不硬编码）。"""
    attrs = res['sentence']['attrs']
    unconfirmed = res['unconfirmed']
    p4 = record.get('param4')
    if unconfirmed:
        unknown = ('句面另含无规则属性：%s —— skilllist|3000 没有 p3/p4/p5/p7 规则，'
                   '本批不出值、不按相关性猜槽位' % '、'.join(unconfirmed))
        if '防御力' in unconfirmed:
            unknown += ('（p4 原值 %s 为负，与「上がる」方向矛盾，仍未知、不消费）' % num_text(p4))
        if '回復' in unconfirmed:
            unknown += ('；「HPが上限を超えて回復する」对应的回復量（p5）无规则，本批不出值'
                        '（flag1_1 只作机制披露）')
    else:
        unknown = ('句面未点名防御力／移動速度／クリティカル発生率／回復，'
                   '本批不为这四项出值')
    cond = ('原文条件：「%s」；触发子句「【共鳴アビリティ】自身を含む<味方>が'
            '≪共鳴必殺≫を発動するたび」逐字保留，对象为句面「戦場にいる<味方>」；'
            'param0=%s 只控制候选接受者是否含提供者自身，iParam0/param9 属发动者筛选'
            '（本记录未设置），两者不得混写'
            % (res['sentence']['text'], record.get('param0')))
    semantics = ('口径：攻撃力只落成 /param1（普通攻击加算增量，写 _attackNormal）与'
                 '/param2（技能攻击加算增量，写 _attackSkill）两条，以 1 为基准汇总，'
                 '不是把攻击面板按倍率放大；クリティカル威力只落成 /param8 暴伤系数加算'
                 '（_criticalDmgRate），不减 1.5、不是暴击伤害再乘百分比')
    p6 = ('同记录 /param6=%s 已有 45 游戏秒答案，本批不重复、不改写'
          % num_text(record.get('param6')))
    s3 = ('账本 S3：触发子句仍为未覆盖子句，split 标记保留、行状态仍「拆分待核查」，'
          'b7 hint 保留，不宣称整行完整')
    grade = ('规则体状态为「已确认（静态及受控原生局部规则）」，但本批未做逐记录执行确认，'
             '故原值与关联证据档均为「推断」')
    limits = '不写最终面板／最终伤害／最终HP／叠加上限／Chain 影响／账号解锁；未做实机验证'
    return '；'.join((cond, semantics, unknown, p6, s3, grade, limits))


def _slot_value_text(name, raw, rule):
    """值文本：复用规则的 ``value_text``（已含换算与百分点），再补本槽口径守卫。

    不在本批重写换算，也不重复数字：p1/p2 补「加算增量≠乘数」，p8 补「系数加算≠乘数」。
    """
    head = str(rule.get('value_text') or '').rstrip('。')
    if name == 'param1':
        return '%s；口径：这是 Support3 普通攻击的加算增量（本项贡献 +%s 个百分点），' \
               '以 1 为基准与其他项汇总，不是把攻击面板按倍率放大' % (head, num_text(
                   round(float(raw) * 100.0, 6)))
    if name == 'param2':
        return '%s；口径：这是 Support3 技能攻击的加算增量（本项贡献 +%s 个百分点），' \
               '以 1 为基准与其他项汇总，不是把攻击面板按倍率放大' % (head, num_text(
                   round(float(raw) * 100.0, 6)))
    return '%s；口径：这是暴击伤害系数的加算贡献（直接写 _criticalDmgRate），' \
           '不减 1.5、不乘 Chain、不是暴击伤害再乘百分比' % head


def _slot_note(ctx, record, slot):
    """逐槽 note：载体、映射、方向、对象、触发、样本域、未确认项、证据档（不升格）。"""
    name, attr, raw = slot['slot'], slot['attr'], slot['raw']
    rule = slot['rule']
    if name == 'param1':
        mapping = '句中「攻撃力」→ /param1（攻撃力＝param1+param2 两条值行；本条为普通攻击侧）'
        direction = '方向审核：原值 %s>0，普通攻击加算贡献与「上がる」句向一致' % num_text(raw)
    elif name == 'param2':
        mapping = '句中「攻撃力」→ /param2（攻撃力＝param1+param2 两条值行；本条为技能攻击侧）'
        direction = '方向审核：原值 %s>0，技能攻击加算贡献与「上がる」句向一致' % num_text(raw)
    else:
        mapping = '句中「クリティカル威力」→ /param8 1:1（暴伤系数加算，不减 1.5、不乘 Chain）'
        direction = ('方向审核：原值 %s>0，暴伤系数加算贡献（_criticalDmgRate）与「上がる」'
                     '句向一致' % num_text(raw))
    unconfirmed = ctx['unconfirmed']
    unknown = ('句面未确认属性：%s（p3/p4/p5/p7 无规则，本批不出值）'
               % '、'.join(unconfirmed) if unconfirmed else
               '句面未点名防御力/移動速度/クリ発生率/回復')
    heal_flag = record.get(HEAL_FLAG_SLOT)
    heal = ('；句面「HPが上限を超えて回復する」对应 flag1_1=%s 只作机制披露，'
            '回復量（p5）无规则、不出值' % heal_flag) if heal_flag else ''
    return ('；'.join((
        'C12-P1 候选值行（来源载体＝**本行自身记录** skilllist|%d|CACHE，'
        '非相邻 sub1、非跨记录推断）' % ctx['record_id'],
        mapping,
        '规则键 %s；原值 %s' % ('%s|%d|%s' % (TABLE, ABILITY, slot['field']), num_text(raw)),
        direction,
        '对象披露（双源）：句面依据「戦場にいる<味方>の」逐字在句；记录侧 param0=%s '
        '控制候选支持接受者（1→遍历候选、含提供者自身；缺→持有者自身），'
        'iParam0/param9 筛选发动者（职业位图/所属），本记录均未设置，不得混写'
        % num_text(record.get('param0')),
        '触发条件逐字：「【共鳴アビリティ】自身を含む<味方>が≪共鳴必殺≫を発動するたび」',
        '样本域：%s' % (rule.get('conditions') or ''),
        unknown + heal,
        '证据档：规则体已确认，但本行未做逐记录执行确认，原值/关联均记「推断」'
        '（scope=%s）' % SCOPE,
        'S3 与 b7 hint 保留：触发子句不被本批答案覆盖，行仍「拆分待核查」，不宣称完整',
    )) + '。')


def build_answers(data, cid, row, res, tab=None):
    """构造 2/3 条答案对象（复用 ``rules.answer_for`` 的换算与证据字段，不重写公式）。"""
    if not res.get('accepted'):
        return []
    tab = tab or tables(data)
    index = res['record']['index']
    parent_id = res['record']['skillid']
    pointer = '/skilllist/%d' % index
    record = tab['skills'][parent_id][0][1]
    common = _common_text(res, record)
    row_id = row.get('row_id')
    answers = []
    for slot in res['slots']:
        name, field, attr, rule = slot['slot'], slot['field'], slot['attr'], slot['rule']
        raw = slot['raw']
        value = '%s。%s' % (_slot_value_text(name, raw, rule), common)
        answers.append({
            'value': value,
            'quantity_kind': rule.get('quantity_kind'),
            'unit': rule.get('unit'),
            'raw_value': raw,
            'field_path': field,
            'rule_key': _answer_key(field),
            'table': TABLE,
            'record_id': parent_id,
            'layer': LAYER,
            'effect_attribute': attr,
            'source': {
                'source_key': SOURCE_KEY,
                'json_pointer': pointer,
                'layer': LAYER,
                'record_key': '%s#%s' % (SOURCE_KEY, pointer),
                'table': TABLE,
                'record_id': parent_id,
                'field_path': field,
                'field': field,
                'field_json_pointer': '%s%s' % (pointer, field),
            },
            'numeric_source': '规则（%s，本批按记录取值）' % _answer_key(field),
            'numeric_evidence': '推断',
            'association_evidence': '推断',
            'answer_status': rule.get('answer_status') or 'CONFIRMED_NUMERIC',
            'evidence_scope': SCOPE,
            'quantitative': True,
            'conversion': rule.get('conversion'),
            'value_text': rule.get('value_text'),
            'conditions': rule.get('conditions'),
            'base_definition': rule.get('base_definition'),
            'rule_status': rule.get('rule_status') or rule.get('status'),
            'rule_body_status': rule.get('rule_status'),
            'rule_limits': rule.get('rule_limits') or rule.get('limits'),
            'evidence': list(rule.get('evidence') or ()),
            'context': row.get('japanese'),
            'note': _slot_note({'record_id': parent_id,
                               'unconfirmed': list(res['unconfirmed'])}, record, slot),
            'binding': {MARKER_KEY: {
                'scope': SCOPE,
                'structure_scope': STRUCTURE_SCOPE,
                'module': MODULE_VERSION,
                'candidate_only': True,
                'cid': cid,
                'row_id': row_id,
                'reference_field': REF_TEMPLATE % cid,
                'rule_key': _answer_key(field),
                'table': TABLE,
                'ability': ABILITY,
                'record_id': parent_id,
                'record_index': index,
                'layer': LAYER,
                'field_path': field,
                'slot': name,
                'effect_attribute': attr,
                'raw_value': raw,
                'sentence_form': res['sentence']['form'],
                'sentence_attrs': list(res['sentence']['attrs']),
                'fragment_index': TARGET_FRAGMENT_INDEX,
                'trailing_clause_not_consumed': True,
                'sub_records_not_consumed': list(record.get('sub') or ()),
                'carrier': 'OWN_RECORD（本行自身记录，非相邻 sub1）',
                'unconfirmed_attrs': list(res['unconfirmed']),
                'unconfirmed_slots_not_consumed': [UNCONFIRMED_SLOTS[a]
                                                   for a in res['unconfirmed']],
                'condition': {'param0': record.get('param0'),
                              'param0_self_inclusive': True,
                              'iParam0': record.get('iParam0'),
                              'param9': record.get('param9')},
                'p6_existing_answer_kept': True,
                'p6_rule_key': P6_RULE_KEY,
                'split_flag_policy': 'S3_KEPT（触发子句未被本批覆盖，不清 split 标记）',
                'b7_hint_kept': True,
                'numeric_evidence': '推断',
                'association': '推断',
                'disclosure': {
                    'carrier': 'OWN_RECORD（不借相邻 sub1、不跨记录）',
                    'unconfirmed_attributes': (
                        'NOT_CONSUMED（p3/p4/p5/p7 无规则；p4 负值不猜）'
                        if res['unconfirmed'] else 'NONE_CLAIMED'),
                    'p6': 'EXISTING_KEPT（不重复、不改写）',
                    's3': 'S3_KEPT（行仍「拆分待核查」）',
                    'b7_hint': 'KEPT（inference_b7_hint 未删、G4 文本保留）',
                    'evidence_grade': '推断（规则体已确认，逐记录未核实）',
                    'rights': '不写最终伤害/HP/面板/叠加上限/Chain/账号解锁；未做实机',
                },
            }},
        })
    return answers


# ---------------------------------------------------------------- 页面消费（候选）

def _existing_same(row, answers):
    """已有同键答案：全部同记录/同字段/同原值/同层 → SAME；否则 CONFLICT。"""
    keys = {a['rule_key'] for a in answers}
    existing = {}
    for answer in row.get('answers') or []:
        key = answer.get('rule_key')
        if key in keys:
            existing[key] = answer
    if not existing:
        return 'ABSENT', {}
    same = True
    for answer in answers:
        hit = existing.get(answer['rule_key'])
        if hit is None:
            same = False
            continue
        if not (hit.get('record_id') == answer['record_id']
                and hit.get('field_path') == answer['field_path']
                and hit.get('layer') == answer['layer']
                and hit.get('raw_value') == answer['raw_value']):
            same = False
    if same and len(existing) == len(answers):
        return 'SAME', existing
    return 'CONFLICT', existing


def apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None):
    """在页面 ``groups`` 上消费本批规则；返回报告（不写文件、不碰共享接线）。

    批次边界必须由调用方显式声明：``scope_cids is None`` → 一行都不处理。
    """
    report = {'cid': cid, 'scope': SCOPE, 'module': MODULE_VERSION,
              'scope_declared': scope_cids is not None,
              'out_of_scope': False, 'processed': 0, 'answers_added': 0,
              'additions': [], 'rejections': [], 'skipped_existing': 0,
              'marker_only': 0, 'out_of_domain_rows': 0}
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append({'row_id': None, 'reason': 'ZERO_TOUCH_CID'})
        return report
    if scope_cids is None:
        report['rejections'].append({'row_id': None, 'reason': 'NO_SCOPE_DECLARED'})
        return report
    if cid not in scope_cids:
        report['out_of_scope'] = True
        report['rejections'].append({'row_id': None, 'reason': 'CID_NOT_IN_DECLARED_SCOPE'})
        return report
    tab = tab or tables(data)
    ref = REF_TEMPLATE % cid
    rows_map = {r['row_id']: r for g in groups for s in g.get('skills') or []
                for r in s.get('rows') or []}
    for group in groups:
        if group.get('group') != 'sympathy':
            continue
        for skill in group.get('skills') or []:
            if str(skill.get('reference_field') or '') != ref:
                continue
            for row in skill.get('rows') or []:
                fragment = row.get('fragment_index')
                if not isinstance(fragment, int) or fragment != TARGET_FRAGMENT_INDEX:
                    report['out_of_domain_rows'] += 1
                    continue
                report['processed'] += 1
                res = evaluate(data, cid, row, rows=rows_map, skill=skill, tab=tab)
                if not res['accepted']:
                    report['rejections'].append({'row_id': row.get('row_id'),
                                                 'reason': res['rejection'],
                                                 'detail': res.get('rejection_detail')})
                    continue
                answers = build_answers(data, cid, row, res, tab=tab)
                state, existing = _existing_same(row, answers)
                if state == 'SAME':
                    report['skipped_existing'] += 1
                    report['rejections'].append({'row_id': row.get('row_id'),
                                                 'reason': 'ALREADY_PRESENT_SAME'})
                    continue
                if state == 'CONFLICT':
                    _write_marker(row, res, cid, state='ALREADY_ANSWERED')
                    report['marker_only'] += 1
                    report['rejections'].append({'row_id': row.get('row_id'),
                                                 'reason': 'ALREADY_ANSWERED',
                                                 'existing_rule_keys': sorted(existing)})
                    continue
                row.setdefault('answers', [])
                row['answers'].extend(answers)
                _stamp_row(row, res, cid)
                report['answers_added'] += len(answers)
                report['additions'].append({'row_id': row.get('row_id'),
                                            'rule_keys': [a['rule_key'] for a in answers],
                                            'attributes': [a['effect_attribute']
                                                           for a in answers]})
    return report


def _stamp_row(row, res, cid):
    """行级标注：证据档、scope、残余未知原因与本批 marker（不改 row_class／partial）。

    **不写** ``binding_conditions``：S3 条件子句保留，本批不清 split 标记；也不删
    ``inference_b7_hint``。
    """
    row['evidence'] = '推断'
    row['evidence_scope'] = sorted({s['evidence_scope'] for s in res['slots']})
    row['evidence_label'] = RESIDUAL_LABEL
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    if RESIDUAL_NOTE not in reasons:
        reasons.append(RESIDUAL_NOTE)
    row['unknown_reasons'] = reasons
    _write_marker(row, res, cid, state='ANSWERS_ADDED')


def _write_marker(row, res, cid, state):
    record = res['record']
    row[MARKER_KEY] = {
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'module': MODULE_VERSION,
        'candidate_only': True,
        'state': state,
        'cid': cid,
        'row_id': row.get('row_id'),
        'reference_field': REF_TEMPLATE % cid,
        'record_id': record['skillid'],
        'record_index': record['index'],
        'ability': record['ability'],
        'layer': LAYER,
        'carrier': 'OWN_RECORD',
        'sentence_form': res['sentence']['form'],
        'sentence_attrs': list(res['sentence']['attrs']),
        'fragment_index': TARGET_FRAGMENT_INDEX,
        'trailing_clause_not_consumed': True,
        'sub_records_not_consumed': record.get('sub'),
        'unconfirmed_attrs': list(res['unconfirmed']),
        'unconfirmed_slots_not_consumed': [UNCONFIRMED_SLOTS[a] for a in res['unconfirmed']],
        'condition': {'param0': record.get('param0'), 'self_inclusive': True},
        'p6_existing_answer_kept': True,
        'split_flag_policy': 'S3_KEPT',
        'b7_hint_kept': True,
        'binding_conditions_written': False,
        'rule_keys': [('skilllist|%d|%s' % (ABILITY, s['field'])) for s in res['slots']],
        'numeric_evidence': '推断',
        'association': '推断',
        'unknowns': ['防御力（p4 负值，方向与「上がる」矛盾）',
                     '移動速度（p3）', 'クリティカル発生率（p7）', '回復（p5）',
                     '叠加上限', 'Chain 影响', '实机'],
    }
