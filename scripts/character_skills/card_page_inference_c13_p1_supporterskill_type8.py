# -*- coding: utf-8 -*-
"""C13-P1 supporterskill→abiN 的 type8「戦闘時」常时基础增益：候选实现。

任务卡 ``docs/tasks/20261031-c13-p1-supporterskill-type8.md``；周期卡
``docs/tasks/20261031-c13-cycle.md``；候选输入 ``work/c13_20261031/supporterskill_type8_strict.json``。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；正式
``pages/``、``rules.json``／``rules.py``、``effect_ledger.py``／账本均未改动；未运行正式全库
生成。运行 ``python -B <本文件>`` 只写本任务候选目录
``output/character_skills/c13_p1_supporterskill_type8_20261031/candidate_answers.json``。

句子族与范围
------------
只处理 Y.G. 卡的 bond 段、``reference_field == 'supporterskill.ability_id == cid'``、
句面以逐字「戦闘時、」开头的**常时自身基础增益**句，且句面点名的属性落在本批三个 scope 槽::

    戦闘時、<攻撃力|防御力|移動速度>[と<...>]が上がり、…          （句首属性链）
    戦闘時、<攻撃力|防御力|移動速度>[と<...>]が上がる。

属性→槽位（全部复用 ``rules.json`` 既有 ``skilllist|8|`` 三键，本批 0 新规则键）::

    攻撃力   → /param1  本项攻击乘数（乘进自身攻击因子）
    移動速度 → /param2  移动速度乘数
    防御力   → /param3  本项受伤量乘数（正文写作「防御」；乘受伤量因子，不是固定防御量）

条件句／对象句（「ボスWAVE時」「2人以上で同じ敵を攻撃すると」「WAVEが進むたび」
「戦場にいる<所属>所属の」「味方全体の」「自身がサブパーティにいると」等）**一律拒绝**：
type8 原生 ``IsEnableAbility`` 对该 type 无条件返回 true，乘的是自身因子，承载不了额外条件或
他人目标；把这些句子归到 type8 会把条件与对象丢掉。5 条上游候选因此被剔除（记录见
``candidate_answers.json#exclusions``），30302 的重复攻击主张同样不得重新纳入。

来源链（逐行重验，不采信上游筛选脚本）
--------------------------------------
1. 行身份：``row.cid == cid``、``group == 'bond'``、``reference_field`` 逐字、``source`` 为
   CACHE ``supporterskill.data5.json.raw`` 的 ``/text``、``json_pointer`` 形如
   ``/supporterskill/<n>``；``supporterskill[<n>].ability_id == cid``；页面载体
   ``record_evidence`` 内嵌 ``raw_record`` 与解码记录逐字段相等；``original_text``／
   ``context_text`` 等于记录正文（字面 ``\\n`` 转真实换行）；``japanese`` 是该正文的**唯一**
   句单位，且 ``fragment_index`` 等于它在句单位中的下标。
2. 引用解引用：只按原记录的 ``abiN`` 字段取值，逐 ID **CACHE 优先**；CACHE 缺该 ID 才回退
   APK ``_mdSkill.json``；两层都有时只用 CACHE，APK 只登记为 ``apk_shadow``（差异逐字段披露），
   **不合并**。任一 ``abiN`` 缺失／重复即整行拒绝（不静默跳过）。
3. 句面↔载体：目标属性必须是句首「戦闘時、」属性链的**独立成员**（``自身の攻撃力``／
   ``味方全体の攻撃力``／``<所属>所属の攻撃力`` 不算）；载体记录的正文必须以「戦闘時」开头，
   且正文点名属性集合 == 该记录非中性 scope 槽集合（条文与槽位 1:1）。
4. 唯一来源：每个目标效果恰一个未解 backlog 项、恰一个 ability 8 非中性来源；同记录出现第二个
   非中性 scope 槽而本行未主张 → 拒绝；来源 0 个／多个 → 拒绝。
5. 中性分档：``1.0`` 为中性（不出值、不补 0）；缺失／null／非数值／非有限分别登记；方向按代码
   语义（攻撃力 param1>1、移動速度 param2>1、防御力 0<param3<1），方向矛盾拒绝。
6. 幂等：同键同记录同原值已在页面上 → ``ALREADY_PRESENT_SAME``（零写入）；同键异值 →
   拒绝（永不覆盖）；本批不重复回答 ``skilllist|29`` 等既有特殊威力答案。
7. 句面归属：若同一 supporterskill 记录的**另一** abi 记录正文与本行句面逐字相同，则本句属于
   该记录（如 30243 f2→122067、30257 f2→123003、30261 f2→131002、30320 f2→107011、
   30336 f2→123003），type8 不得抢答。

证据档（分开披露，不升格）
--------------------------
* 规则体：``rules.json#skilllist|8|/paramN`` 原文状态逐字保留在 ``rule_status``／
  ``rule_body_status``（已确认数值换算；未乘 Chain，不承诺最终伤害）。
* 数值侧 ``numeric_evidence = 确认``：只复用已确认换算，原值与载体正文数字一致（如
  ``攻撃1.15`` ↔ param1=1.149999976158142），本批不重写公式。
* 关联侧 ``association_evidence = 推断``：句面→abi 载体、以及「装载后进入玩家侧 apply 路径」
  都是结构门控，**未做逐记录执行确认、未做实机**。
* 不写玩家解锁、最终面板、最终伤害／最终HP、叠加上限、Chain 影响。

接口
----
``tables(root=None)`` / ``clone_tables(tab)``      只读主表索引（可注入，反例用）
``parse_battle_chain(japanese)``                    句首「戦闘時、」属性链结构解析
``evaluate(cid, row, *, skill=None, tab=None, backlog=None, scope_cids=None)``
                                                     单行判定（不写入）
``build_answers(cid, row, res, tab=None)``           值行对象（复用 rules.answer_for）
``apply_to_skill(cid, skill, *, tab, backlog, scope_cids)``
                                                     页面消费（深拷贝、候选未接线）
``build_candidate(root=None, write=True)``           本任务候选 JSON（含剔除与对账）
"""
from __future__ import annotations

import collections
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path

MODULE_VERSION = 'c13_p1_supporterskill_type8_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 答案证据 scope（供账本/页面按 scope 精确消费时对账）。
SCOPE = 'C13_P1_SUPPORTERSKILL_TYPE8_20261031'
#: 结构判定自身 scope（行级 marker）。
STRUCTURE_SCOPE = 'C13_P1_SUPPORTERSKILL_TYPE8_STRUCTURE_20261031'
#: 行级 marker 键（每行至多一个本批键，不覆盖其他批的 marker）。
MARKER_KEY = 'inference_c13_p1_supporterskill_type8'

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = 'output/cache_full_20261015_v3/decoded'
SUPPORTER_FILE = 'supporterskill.data5.json.raw'
SKILLLIST_FILE = 'skilllist.data5.json.raw'
APK_SKILLLIST = 'output/base_master/_mdSkill.json'
RULES_FILE = 'output/character_skills/profiles/rules.json'
PAGES_DIR = 'output/character_skills/pages'
YG_ITEMS_FILE = 'work/character_skills_yg_priority/yg_candidates_items.json'
UPSTREAM_CANDIDATE_FILE = 'work/c13_20261031/supporterskill_type8_strict.json'
OUT_DIR = 'output/character_skills/c13_p1_supporterskill_type8_20261031'
CANDIDATE_FILE = OUT_DIR + '/candidate_answers.json'

TABLE = 'skilllist'
ABILITY = 8
SUPPORTER_TABLE = 'supporterskill'
REF_FIELD = 'supporterskill.ability_id == cid'
TEXT_FIELD = '/text'
SOURCE_KEY = 'CACHE/supporterskill.data5.json.raw'
SOURCE_KEY_SKILLLIST_CACHE = 'CACHE/skilllist.data5.json.raw'
SOURCE_KEY_SKILLLIST_APK = 'APK/_mdSkill.json'
POINTER_RE = re.compile(r'^/supporterskill/(\d+)$')
ABI_FIELD_RE = re.compile(r'^abi(\d+)$')

#: 句首逐字（常时＝戦闘時）。本批只处理这一族。
LEADING_CLAUSE = '戦闘時、'
#: 句首属性链的上升终止词（取最先出现者）。
UP_TERMINATORS = ('が上がり', 'が上がる')

#: 本批 scope 槽：属性 → 记录字段（顺序即输出顺序）。
ATTR_SLOTS = (('攻撃力', 'param1'), ('移動速度', 'param2'), ('防御力', 'param3'))
ATTR_FIELD = {attr: '/' + slot for attr, slot in ATTR_SLOTS}
SLOT_ATTR = {slot: attr for attr, slot in ATTR_SLOTS}
TARGET_ATTRS = tuple(attr for attr, _slot in ATTR_SLOTS)
#: 载体正文点名属性的判定词（必须原文明确支持该属性）。
ATTR_TEXT_NEEDLES = {
    '攻撃力': ('攻撃力',),
    '移動速度': ('移動速度',),
    '防御力': ('防御', 'ダメージ'),
}
#: 规则 meaning_zh 语义守卫：规则文本一变即拒绝，不静默沿用。
RULE_MEANING_NEEDLES = {
    '攻撃力': ('攻击',),
    '移動速度': ('移动速度',),
    '防御力': ('受伤量', '防御'),
}
#: 乘数中性值（原值恰 1 不出值；方向按代码语义）。
NEUTRAL_IDENTITY = 1.0
#: 无规则数值槽的中性登记值：0（未设置）或 1（乘数恒等）。
UNRULED_NEUTRAL_VALUES = (0.0, 1.0)
#: 无规则数值槽（rules.json 对 skilllist|8 只有 param1/param2/param3 三键）。
UNRULED_SLOTS = ('param0', 'param4', 'param5', 'param6', 'param7', 'param8', 'param9',
                 'iParam0', 'iParam1', 'flag0_0', 'flag0_1', 'flag1_0', 'flag1_1', 'flag')
#: 保护／禁推卡：判定前硬拒绝（30102 禁推卡；30236／30239 保护卡；20234 既有边界）。
ZERO_TOUCH_CIDS = frozenset({20234, 30102, 30236, 30239})
#: 记录正文用**字面**反斜线＋n 分段（不是控制字符）；避免源码写转义序列。
TEXT_SEP = chr(92) + 'n'
_SENTENCE_SPLIT = re.compile(r'(?<=。)|[\r\n]')

_TABLES = {}

LIMITS_TEXT = ('不写玩家解锁、最终面板、最终伤害／最终HP、叠加上限、Chain 影响；未做实机验证；'
               '本批未做逐记录执行确认（句面→载体与装载/生效关联为推断）；CACHE 与 APK 同号记录'
               '不合并；type18、type9 及其他能力类型不在本批范围。')


# ---------------------------------------------------------------- 基础工具

def read_json(path):
    return json.loads(read_path(Path(path)).read_text(encoding='utf-8'))


def sha256_file(path):
    return hashlib.sha256(read_path(Path(path)).read_bytes()).hexdigest()


def num_text(value):
    """有限数值的稳定文本：最短往返 repr（保留 float32 原值的十进制展开，不做 6 位截断）。"""
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    text = repr(f)
    if 'e' in text or 'E' in text:
        text = '%.17g' % f
    return text


def plain_text(value):
    """记录正文字面 ``\\n`` → 真实换行（与页面 ``original_text``／``context_text`` 同口径）。"""
    return str(value or '').replace(TEXT_SEP, '\n')


def norm_text(value):
    """去全部空白后的比较口径（载体正文里有「。 移動速度1.2」这类空格）。"""
    return re.sub(r'\s+', '', plain_text(value))


def sentence_units(value):
    """记录正文的句单位（句末「。」／换行切分，去行首◆）。与页面 fragment 同口径。"""
    units = []
    for unit in _SENTENCE_SPLIT.split(plain_text(value)):
        unit = unit.strip().lstrip('◆').strip()
        if unit:
            units.append(unit)
    return units


def raw_state(value, present=True):
    """缺失 / null / 非数值 / 非有限 / 负值 / 真零 / 有限分开标注（不把任何一档补成 0）。"""
    if not present:
        return 'MISSING'
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'NON_NUMERIC'
    if not isinstance(value, (int, float)):
        return 'NON_NUMERIC'
    f = float(value)
    if not math.isfinite(f):
        return 'NON_FINITE'
    if f < 0:
        return 'NEGATIVE'
    if f == 0:
        return 'ZERO'
    return 'FINITE'


def _int_or_zero(record, name):
    """整型筛位读取：缺失/显式 null 按 0；非整型/非有限单独标注。"""
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
    if not math.isfinite(f) or f != int(f):
        return None, 'invalid'
    return int(f), 'present'


def _rules_module():
    """惰性导入 rules（scripts/character_skills 下）；-I 运行时不依赖 cwd。"""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import rules  # noqa: WPS433 - 既有规则层，只读复用
    return rules


# ---------------------------------------------------------------- 只读主表

def _index(records):
    out = collections.defaultdict(list)
    for index, record in enumerate(records):
        sid = record.get('skillid')
        if isinstance(sid, int) and not isinstance(sid, bool):
            out[sid].append((index, record))
    return dict(out)


def tables(root=None):
    """只读主表索引（按 root 缓存）。``tab`` 可由调用方注入（反例用）。"""
    root = Path(root).resolve() if root is not None else ROOT
    key = str(root)
    if key not in _TABLES:
        base = read_path(root / CACHE_DIR, root=root)
        supporter = read_json(base / SUPPORTER_FILE)[SUPPORTER_TABLE]
        cache = read_json(base / SKILLLIST_FILE)[TABLE]
        apk = read_json(root / APK_SKILLLIST)[TABLE]
        rules = read_json(root / RULES_FILE)
        _TABLES[key] = {
            'root': root,
            'supporter': supporter,
            'cache': _index(cache),
            'apk': _index(apk),
            'cache_count': len(cache),
            'apk_count': len(apk),
            'rules': rules,
        }
    return _TABLES[key]


def clone_tables(tab):
    """反例用：深拷贝索引（不改动全局缓存）。"""
    return {
        'root': tab.get('root'),
        'supporter': copy.deepcopy(tab['supporter']),
        'cache': copy.deepcopy(tab['cache']),
        'apk': copy.deepcopy(tab['apk']),
        'cache_count': tab.get('cache_count'),
        'apk_count': tab.get('apk_count'),
        'rules': copy.deepcopy(tab['rules']),
    }


def resolve_record(tab, record_id):
    """逐 ID **CACHE 优先、CACHE 缺 ID 才回退 APK**；两层都有只用 CACHE（不合并）。"""
    if isinstance(record_id, bool) or not isinstance(record_id, int):
        return {'error': 'NON_INTEGER_ID', 'record_id': record_id}
    cache_hits = tab['cache'].get(record_id) or []
    apk_hits = tab['apk'].get(record_id) or []
    if len(cache_hits) > 1 or len(apk_hits) > 1:
        return {'error': 'DUPLICATE_ID', 'record_id': record_id,
                'cache_hits': len(cache_hits), 'apk_hits': len(apk_hits)}
    if cache_hits:
        index, record = cache_hits[0]
        out = {'record_id': record_id, 'layer': 'CACHE', 'index': index, 'record': record,
               'cache_present': True, 'apk_present': bool(apk_hits),
               'resolution': 'CACHE'}
        if apk_hits:
            apk_index, apk_record = apk_hits[0]
            divergent = [name for name in ('ability', 'param1', 'param2', 'param3', 'text')
                         if apk_record.get(name) != record.get(name)]
            out['apk_shadow'] = {'index': apk_index, 'skillid': apk_record.get('skillid'),
                                 'ability': apk_record.get('ability'),
                                 'divergent_fields': divergent,
                                 'params': {name: apk_record.get(name)
                                            for name in ('param1', 'param2', 'param3')}}
        return out
    if apk_hits:
        index, record = apk_hits[0]
        return {'record_id': record_id, 'layer': 'APK', 'index': index, 'record': record,
                'cache_present': False, 'apk_present': True,
                'resolution': 'CACHE_MISSING_APK_FALLBACK'}
    return {'error': 'MISSING', 'record_id': record_id,
            'cache_present': False, 'apk_present': False}


# ---------------------------------------------------------------- 句面结构

def parse_battle_chain(japanese):
    """解析「戦闘時、<属性>[と<属性>…]が上がり/が上がる…」的句首属性链。

    返回 ``(members, detail)``；不匹配返回 ``(None, detail)``。只做逐字结构切分，
    不做正则近似，避免半句被消费。``members`` 是「と」连接的独立成员——目标属性必须是
    其中的**完整成员**（``自身の攻撃力``／``味方全体の攻撃力`` 不算）。
    """
    text = str(japanese or '')
    if not text:
        return None, {'reason': 'ROW_TEXT_EMPTY'}
    if not text.startswith(LEADING_CLAUSE):
        return None, {'reason': 'NOT_BATTLE_SELF_CLAUSE', 'has_leading_clause': False}
    rest = text[len(LEADING_CLAUSE):]
    hits = [(rest.find(term), term) for term in UP_TERMINATORS if rest.find(term) >= 0]
    if not hits:
        return None, {'reason': 'NO_UP_TERMINATOR', 'rest': rest}
    pos, term = min(hits)
    chain = rest[:pos]
    members = tuple(chain.split('と'))
    detail = {'reason': None, 'members': members, 'terminator': term,
              'chain': chain, 'rest': rest}
    if not chain or any(not member for member in members):
        return None, dict(detail, reason='EMPTY_MEMBER')
    return members, detail


def direction_ok(attr, raw):
    """方向按代码语义：攻撃力/移動速度乘数 >1；防御力＝受伤量乘数 0<x<1（减伤）。"""
    if attr in ('攻撃力', '移動速度'):
        return float(raw) > 1.0
    if attr == '防御力':
        return 0.0 < float(raw) < 1.0
    return False


def direction_text(attr, raw):
    value = num_text(raw)
    if attr == '攻撃力':
        return 'param1=%s>1，攻击因子乘数>1 与「攻撃力が上がる」句向一致' % value
    if attr == '移動速度':
        return 'param2=%s>1，移动速度乘数>1 与「移動速度が上がる」句向一致' % value
    return ('param3=%s<1，受伤量乘数<1 即减伤，与「防御力が上がる」句向一致'
            '（方向按代码语义，不按名称「防御」改动）' % value)


def exact_text_owners(tab, record, japanese):
    """解析 ``record`` 的 abiN，列出正文与本句**逐字相同**的记录（句面归属证据）。"""
    owners = []
    want = norm_text(japanese)
    for name, value in record.items():
        if not ABI_FIELD_RE.match(name):
            continue
        hit = resolve_record(tab, value)
        if hit.get('error'):
            continue
        if norm_text(hit['record'].get('text')) == want:
            owners.append({'abi_field': name, 'record_id': value, 'layer': hit['layer'],
                           'ability': hit['record'].get('ability'),
                           'text': hit['record'].get('text')})
    return owners


def _row_owners(tab, row):
    """行载体记录 → 与本句逐字相同的 abi 记录列表（句面归属证据，容错版）。"""
    pointer = str((row.get('source') or {}).get('json_pointer') or '')
    match = POINTER_RE.match(pointer)
    if not match:
        return []
    index = int(match.group(1))
    if index >= len(tab['supporter']):
        return []
    return exact_text_owners(tab, tab['supporter'][index], row.get('japanese'))


def _record_view(record):
    """一条 abi 记录的只读视图：正文点名属性、scope 槽状态、无规则槽与结构位。"""
    text = norm_text(record.get('text'))
    supports = [attr for attr in TARGET_ATTRS
                if any(needle in text for needle in ATTR_TEXT_NEEDLES[attr])]
    slots = {}
    for attr, slot in ATTR_SLOTS:
        present = slot in record
        raw = record.get(slot)
        state = raw_state(raw, present)
        slots[attr] = {
            'slot': slot,
            'present': present,
            'raw': raw,
            'state': state,
            'neutral': state == 'FINITE' and float(raw) == NEUTRAL_IDENTITY,
        }
    nonneutral = [attr for attr in TARGET_ATTRS
                  if slots[attr]['state'] == 'FINITE' and not slots[attr]['neutral']]
    unruled = {}
    for name in UNRULED_SLOTS:
        value, state = _int_or_zero(record, name)
        unruled[name] = {'raw': record.get(name), 'state': state, 'value': value}
    return {
        'ability': record.get('ability'),
        'text': record.get('text'),
        'normalized_text': text,
        'starts_with_battle': text.startswith(LEADING_CLAUSE),
        'supports': supports,
        'slots': slots,
        'nonneutral': nonneutral,
        'unruled': unruled,
        'sub': list(record.get('sub') or ()),
    }


# ---------------------------------------------------------------- 单行判定

def evaluate(cid, row, *, skill=None, tab=None, backlog=None, scope_cids=None):
    """单行判定（不写入）。``backlog`` 为 row_id → 未解效果项列表（缺失即零出值）。"""
    rid = (row or {}).get('row_id')
    out = {
        'cid': cid,
        'row_id': rid,
        'module': MODULE_VERSION,
        'status': 'REJECTED',
        'reason': None,
        'detail': None,
        'gates': {},
        'sentence': None,
        'claims': [],
        'refs': [],
        'slots': [],
        'existing_answers': [],
        'already_present': [],
    }

    # D0 作用域（先于任何主表访问）
    if cid in ZERO_TOUCH_CIDS:
        out['reason'] = 'ZERO_TOUCH_CID'
        out['detail'] = {'cid': cid, 'protected': sorted(ZERO_TOUCH_CIDS)}
        return out
    if scope_cids is None:
        out['reason'] = 'NO_SCOPE_DECLARED'
        out['detail'] = {'scope': None}
        return out
    scope = {int(value) for value in scope_cids}
    if cid not in scope:
        out['reason'] = 'CID_OUT_OF_SCOPE'
        out['detail'] = {'cid': cid, 'scope_size': len(scope)}
        return out

    # D1 行身份
    if row is None:
        out['reason'] = 'ROW_MISSING'
        return out
    if row.get('cid') != cid:
        out['reason'] = 'ROW_CID_MISMATCH'
        out['detail'] = {'row_cid': row.get('cid'), 'cid': cid}
        return out
    if row.get('group') != 'bond':
        out['reason'] = 'NOT_BOND_GROUP'
        out['detail'] = {'group': row.get('group')}
        return out
    if str(row.get('reference_field') or '') != REF_FIELD:
        out['reason'] = 'NOT_SUPPORTERSKILL_ROW'
        out['detail'] = {'reference_field': row.get('reference_field')}
        return out

    src = row.get('source') or {}
    out['gates']['row_source'] = {name: src.get(name) for name in
                                  ('source_key', 'layer', 'field', 'json_pointer', 'record_key',
                                   'original_file', 'source_sha256', 'raw_record_sha256')}
    if src.get('layer') != 'CACHE' or src.get('source_key') != SOURCE_KEY:
        out['reason'] = 'ROW_SOURCE_NOT_CACHE_SUPPORTERSKILL'
        out['detail'] = {'layer': src.get('layer'), 'source_key': src.get('source_key')}
        return out
    if str(src.get('field') or '') != TEXT_FIELD:
        out['reason'] = 'ROW_FIELD_NOT_TEXT'
        out['detail'] = {'field': src.get('field')}
        return out
    pointer = str(src.get('json_pointer') or '')
    match = POINTER_RE.match(pointer)
    if not match:
        out['reason'] = 'ROW_POINTER_NOT_SUPPORTERSKILL'
        out['detail'] = {'json_pointer': pointer}
        return out
    index = int(match.group(1))
    tab = tables() if tab is None else tab
    supporter = tab['supporter']
    if index >= len(supporter):
        out['reason'] = 'ROW_POINTER_OUT_OF_RANGE'
        out['detail'] = {'index': index, 'records': len(supporter)}
        return out
    record = supporter[index]
    out['gates']['carrier'] = {'json_pointer': pointer, 'index': index,
                               'ability_id': record.get('ability_id'),
                               'ability': record.get('ability'), 'name': record.get('name')}
    if record.get('ability_id') != cid:
        out['reason'] = 'CARRIER_ABILITY_ID_MISMATCH'
        out['detail'] = {'ability_id': record.get('ability_id'), 'cid': cid}
        return out
    expected_key = '%s#%s' % (SOURCE_KEY, pointer)
    if src.get('record_key') not in (None, expected_key):
        out['reason'] = 'ROW_RECORD_KEY_MISMATCH'
        out['detail'] = {'record_key': src.get('record_key'), 'expected': expected_key}
        return out

    if skill is not None:
        if skill.get('table') != SUPPORTER_TABLE or skill.get('layer') != 'CACHE':
            out['reason'] = 'SKILL_CARRIER_NOT_CACHE_SUPPORTERSKILL'
            out['detail'] = {'table': skill.get('table'), 'layer': skill.get('layer')}
            return out
        if skill.get('record_id') != cid:
            out['reason'] = 'SKILL_RECORD_MISMATCH'
            out['detail'] = {'record_id': skill.get('record_id'), 'cid': cid}
            return out
        if str(skill.get('reference_field') or '') != REF_FIELD:
            out['reason'] = 'SKILL_REFERENCE_FIELD_MISMATCH'
            out['detail'] = {'reference_field': skill.get('reference_field')}
            return out
        if (skill.get('source') or {}).get('json_pointer') != pointer:
            out['reason'] = 'SKILL_POINTER_MISMATCH'
            out['detail'] = {'skill_pointer': (skill.get('source') or {}).get('json_pointer'),
                             'row_pointer': pointer}
            return out
        embedded = [entry for entry in (skill.get('record_evidence') or [])
                    if entry.get('table') == SUPPORTER_TABLE and entry.get('record_id') == cid]
        out['gates']['carrier_evidence'] = {'entries': len(embedded)}
        if len(embedded) != 1:
            out['reason'] = 'CARRIER_EVIDENCE_MISSING'
            return out
        if embedded[0].get('raw_record') != record:
            out['reason'] = 'PAGE_RAW_RECORD_MISMATCH'
            out['detail'] = {'record_id': cid, 'pointer': pointer}
            return out
        if skill.get('original_text') != plain_text(record.get('text')):
            out['reason'] = 'SKILL_ORIGINAL_TEXT_MISMATCH'
            return out

    # D1b 句面在记录正文中的位置
    japanese = str(row.get('japanese') or '')
    units = sentence_units(record.get('text'))
    out['gates']['record_text'] = {'units': len(units)}
    if not japanese:
        out['reason'] = 'ROW_TEXT_EMPTY'
        return out
    if units.count(japanese) != 1:
        out['reason'] = 'ROW_TEXT_NOT_UNIQUE_SENTENCE_UNIT'
        out['detail'] = {'occurrences': units.count(japanese), 'japanese': japanese}
        return out
    if row.get('context_text') not in (None, plain_text(record.get('text'))):
        out['reason'] = 'ROW_CONTEXT_TEXT_MISMATCH'
        return out
    fragment = row.get('fragment_index')
    unit_index = units.index(japanese)
    if fragment is not None and fragment != unit_index:
        out['reason'] = 'FRAGMENT_INDEX_MISMATCH'
        out['detail'] = {'fragment_index': fragment, 'unit_index': unit_index}
        return out
    out['gates']['sentence_position'] = {'unit_index': unit_index, 'units': len(units)}

    # D2 句首「戦闘時、」属性链
    members, detail = parse_battle_chain(japanese)
    out['gates']['sentence'] = dict(detail)
    if members is None:
        out['reason'] = detail.get('reason') or 'SENTENCE_NOT_BATTLE_SELF'
        out['detail'] = dict(detail)
        return out
    out['sentence'] = {'text': japanese, 'members': list(members),
                       'terminator': detail.get('terminator')}

    # D3 未解 backlog 效果项（每效果恰一条）
    claims_all = list((backlog or {}).get(rid) or ())
    target_claims = [claim for claim in claims_all
                     if claim.get('kind') in (None, 'effect')
                     and claim.get('effect_type') in ATTR_FIELD]
    out['gates']['backlog'] = {
        'items': len(claims_all),
        'target_items': len(target_claims),
        'other_effects': [claim.get('effect_type') for claim in claims_all
                          if claim.get('effect_type') not in ATTR_FIELD],
    }
    if not target_claims:
        out['reason'] = 'NO_TARGET_CLAIMS'
        return out
    counts = collections.Counter(claim.get('effect_type') for claim in target_claims)
    duplicated = sorted(attr for attr, number in counts.items() if number != 1)
    if duplicated:
        out['reason'] = 'DUPLICATE_EFFECT_CLAIM'
        out['detail'] = {'attributes': duplicated,
                         'items': [{'effect_type': claim.get('effect_type'),
                                    'backlog_id': claim.get('backlog_id')}
                                   for claim in target_claims]}
        return out
    for claim in target_claims:
        if claim.get('cid') != cid:
            out['reason'] = 'CLAIM_CID_MISMATCH'
            out['detail'] = {'claim': claim}
            return out
        if claim.get('row_id') != rid:
            out['reason'] = 'CLAIM_ROW_MISMATCH'
            out['detail'] = {'claim_row': claim.get('row_id'), 'row_id': rid}
            return out
        if claim.get('yg') is not True:
            out['reason'] = 'CLAIM_NOT_YG'
            out['detail'] = {'backlog_id': claim.get('backlog_id'), 'yg': claim.get('yg')}
            return out
        if claim.get('effect_type') not in members:
            out['reason'] = 'CLAIM_OUTSIDE_LEADING_CLAUSE'
            out['detail'] = {'effect_type': claim.get('effect_type'),
                             'members': list(members),
                             'backlog_id': claim.get('backlog_id')}
            return out
    out['claims'] = [{'effect_type': claim.get('effect_type'),
                      'backlog_id': claim.get('backlog_id')} for claim in target_claims]

    # D4 abiN → 记录（逐 ID CACHE 优先；缺失即拒绝）
    refs = []
    for name, value in record.items():
        match = ABI_FIELD_RE.match(name)
        if match:
            refs.append((int(match.group(1)), name, value))
    refs.sort(key=lambda item: item[0])
    out['gates']['abi_fields'] = [name for _rank, name, _value in refs]
    if not refs:
        out['reason'] = 'NO_ABI_REFS'
        return out
    resolved = []
    for _rank, name, record_id in refs:
        hit = resolve_record(tab, record_id)
        if hit.get('error'):
            out['reason'] = 'ABI_REF_UNRESOLVED'
            out['detail'] = {'abi_field': name, 'record_id': record_id,
                             'error': hit.get('error')}
            return out
        rec = hit['record']
        view = _record_view(rec)
        resolved.append({
            'abi_field': name,
            'record_id': record_id,
            'layer': hit['layer'],
            'index': hit['index'],
            'resolution': hit['resolution'],
            'cache_present': hit['cache_present'],
            'apk_present': hit['apk_present'],
            'apk_shadow': hit.get('apk_shadow'),
            'identity': (hit['layer'], hit['index'], record_id),
            'record': rec,
            'view': view,
        })
    out['refs'] = [{'abi_field': ref['abi_field'], 'record_id': ref['record_id'],
                    'layer': ref['layer'], 'index': ref['index'],
                    'resolution': ref['resolution'], 'cache_present': ref['cache_present'],
                    'apk_present': ref['apk_present'],
                    'ability': ref['view']['ability'],
                    'text': ref['view']['text'],
                    'supports': ref['view']['supports'],
                    'nonneutral': ref['view']['nonneutral'],
                    'apk_shadow': ref['apk_shadow']} for ref in resolved]

    # D5 每属性恰一个 ability 8 非中性来源
    chosen = {}
    for attr in counts:
        usable = []
        troubles = []
        for ref in resolved:
            view = ref['view']
            if view['ability'] != ABILITY:
                continue
            if attr not in view['supports']:
                continue
            slot_view = view['slots'][attr]
            if slot_view['state'] != 'FINITE':
                troubles.append({'abi_field': ref['abi_field'], 'record_id': ref['record_id'],
                                 'slot': slot_view['slot'], 'state': slot_view['state'],
                                 'raw': slot_view['raw']})
                continue
            if slot_view['neutral']:
                continue
            if not direction_ok(attr, slot_view['raw']):
                troubles.append({'abi_field': ref['abi_field'], 'record_id': ref['record_id'],
                                 'slot': slot_view['slot'], 'direction_conflict': True,
                                 'raw': slot_view['raw']})
                continue
            usable.append(ref)
        if troubles:
            out['reason'] = 'ATTR_SOURCE_INCONSISTENT'
            out['detail'] = {'effect_type': attr, 'troubles': troubles,
                             'candidates': [ref['record_id'] for ref in resolved]}
            return out
        if not usable:
            out['reason'] = 'ATTR_SOURCE_MISSING'
            out['detail'] = {'effect_type': attr, 'troubles': troubles,
                             'candidates': [ref['record_id'] for ref in resolved]}
            return out
        if len(usable) > 1:
            out['reason'] = 'ATTR_SOURCE_AMBIGUOUS'
            out['detail'] = {'effect_type': attr,
                             'sources': [{'abi_field': ref['abi_field'],
                                          'record_id': ref['record_id'],
                                          'layer': ref['layer']} for ref in usable]}
            return out
        chosen[attr] = usable[0]

    # D5b 载体记录自洽：正文点名属性集合 == 非中性 scope 槽集合 == 本行主张集
    by_record = collections.defaultdict(list)
    for attr, ref in chosen.items():
        by_record[ref['identity']].append(attr)
    for identity, attrs in by_record.items():
        ref = next(item for item in resolved if item['identity'] == identity)
        view = ref['view']
        if not view['starts_with_battle']:
            out['reason'] = 'CARRIER_TEXT_NOT_BATTLE_SELF'
            out['detail'] = {'record_id': ref['record_id'], 'text': view['text']}
            return out
        if set(view['supports']) != set(view['nonneutral']):
            out['reason'] = 'TEXT_SLOT_ATTR_MISMATCH'
            out['detail'] = {'record_id': ref['record_id'], 'text': view['text'],
                             'text_attrs': view['supports'],
                             'slot_attrs': view['nonneutral']}
            return out
        if set(view['nonneutral']) != set(attrs):
            out['reason'] = 'UNCLAIMED_NON_NEUTRAL_SLOT'
            out['detail'] = {'record_id': ref['record_id'],
                             'slot_attrs': view['nonneutral'],
                             'claimed_on_record': sorted(attrs)}
            return out
        if view['sub']:
            out['reason'] = 'SUB_RECORDS_PRESENT'
            out['detail'] = {'record_id': ref['record_id'], 'sub': view['sub']}
            return out
        for name, item in view['unruled'].items():
            if item['state'] in ('invalid',) or item['value'] is None:
                out['reason'] = 'UNRULED_SLOT_INVALID'
                out['detail'] = {'record_id': ref['record_id'], 'slot': name,
                                 'raw': item['raw'], 'state': item['state']}
                return out
            if float(item['value']) not in UNRULED_NEUTRAL_VALUES:
                out['reason'] = 'UNRULED_SLOT_NON_NEUTRAL'
                out['detail'] = {'record_id': ref['record_id'], 'slot': name,
                                 'raw': item['raw']}
                return out

    # D5c 句面归属：另一 abi 记录正文与本句逐字相同 → 本句属于它，type8 不抢答
    sentence_norm = norm_text(japanese)
    used = {ref['identity'] for ref in chosen.values()}
    foreign = [ref for ref in resolved
               if ref['identity'] not in used
               and ref['view']['normalized_text'] == sentence_norm]
    out['gates']['sentence_owner'] = {
        'exact_matches': [{'abi_field': ref['abi_field'], 'record_id': ref['record_id'],
                           'ability': ref['view']['ability'], 'own': ref['identity'] in used}
                          for ref in resolved
                          if ref['view']['normalized_text'] == sentence_norm],
        'foreign_owner': bool(foreign),
    }
    if foreign:
        out['reason'] = 'SENTENCE_OWNED_BY_SIBLING'
        out['detail'] = {'owners': [{'abi_field': ref['abi_field'],
                                     'record_id': ref['record_id'],
                                     'ability': ref['view']['ability'],
                                     'text': ref['view']['text']} for ref in foreign]}
        return out

    # D6 既有答案保护与幂等
    existing = list(row.get('answers') or [])
    out['existing_answers'] = [
        {'rule_key': answer.get('rule_key'), 'record_id': answer.get('record_id'),
         'layer': answer.get('layer'), 'field_path': answer.get('field_path'),
         'raw_value': answer.get('raw_value'), 'value': answer.get('value')}
        for answer in existing
    ]
    existing_by_key = collections.defaultdict(list)
    for answer in existing:
        key = answer.get('rule_key')
        if isinstance(key, str) and key:
            existing_by_key[key].append(answer)

    slots = []
    for attr in TARGET_ATTRS:
        if attr not in chosen:
            continue
        ref = chosen[attr]
        record_raw = ref['record'].get(ref['view']['slots'][attr]['slot'])
        rule_key = '%s|%d|%s' % (TABLE, ABILITY, ATTR_FIELD[attr])
        present = existing_by_key.get(rule_key) or []
        if present:
            if len(present) != 1:
                out['reason'] = 'EXISTING_ANSWER_DUPLICATED'
                out['detail'] = {'rule_key': rule_key, 'count': len(present)}
                return out
            answer = present[0]
            same = (answer.get('record_id') == ref['record_id']
                    and answer.get('layer') == ref['layer']
                    and str(answer.get('field_path') or '') == ATTR_FIELD[attr]
                    and isinstance(answer.get('raw_value'), (int, float))
                    and not isinstance(answer.get('raw_value'), bool)
                    and float(answer.get('raw_value')) == float(record_raw))
            if not same:
                out['reason'] = 'EXISTING_ANSWER_CONFLICT'
                out['detail'] = {'rule_key': rule_key,
                                 'existing': {'record_id': answer.get('record_id'),
                                              'layer': answer.get('layer'),
                                              'field_path': answer.get('field_path'),
                                              'raw_value': answer.get('raw_value')},
                                 'candidate': {'record_id': ref['record_id'],
                                               'layer': ref['layer'],
                                               'field_path': ATTR_FIELD[attr],
                                               'raw_value': record_raw}}
                return out
            out['already_present'].append({'effect_type': attr, 'rule_key': rule_key,
                                           'record_id': ref['record_id']})
            continue
        slots.append({'attr': attr, 'field': ATTR_FIELD[attr], 'rule_key': rule_key,
                      'record_id': ref['record_id'], 'layer': ref['layer'],
                      'index': ref['index'], 'resolution': ref['resolution'],
                      'cache_present': ref['cache_present'], 'apk_present': ref['apk_present'],
                      'apk_shadow': ref.get('apk_shadow'), 'raw': record_raw,
                      'abi_field': ref['abi_field'], 'abi_text': ref['view']['text'],
                      'record': ref['record'], 'view': ref['view'],
                      'backlog_id': next(claim.get('backlog_id') for claim in target_claims
                                         if claim.get('effect_type') == attr)})

    # D6b 规则语义守卫（复用既有换算，不新注册）
    rules = _rules_module()
    for slot in slots:
        answer = rules.answer_for(TABLE, ABILITY, slot['field'], slot['raw'], slot['record'],
                                  source_layer=slot['layer'])
        if not answer:
            out['reason'] = 'RULE_SLOT_UNCONFIRMED'
            out['detail'] = {'rule_key': slot['rule_key'], 'raw': slot['raw'],
                             'layer': slot['layer']}
            return out
        if answer.get('answer_status') != 'CONFIRMED_NUMERIC':
            out['reason'] = 'RULE_ANSWER_STATUS_UNEXPECTED'
            out['detail'] = {'rule_key': slot['rule_key'],
                             'answer_status': answer.get('answer_status')}
            return out
        meaning = str(answer.get('meaning_zh') or '')
        missing = [needle for needle in RULE_MEANING_NEEDLES[slot['attr']]
                   if needle not in meaning]
        if missing:
            out['reason'] = 'RULE_SEMANTICS_CHANGED'
            out['detail'] = {'rule_key': slot['rule_key'], 'meaning_zh': meaning,
                             'missing': missing}
            return out
        rule_row = tab['rules'].get(slot['rule_key'])
        if not rule_row:
            out['reason'] = 'RULE_KEY_NOT_REGISTERED'
            out['detail'] = {'rule_key': slot['rule_key']}
            return out
        if rule_row.get('field_path') != slot['field'] or rule_row.get('effect_type') != ABILITY:
            out['reason'] = 'RULE_KEY_SHAPE_MISMATCH'
            out['detail'] = {'rule_key': slot['rule_key'], 'rule': rule_row}
            return out
        if float(answer.get('raw_value')) != float(slot['raw']):
            out['reason'] = 'RULE_RAW_MISMATCH'
            out['detail'] = {'rule_key': slot['rule_key'],
                             'rule_raw': answer.get('raw_value'), 'slot_raw': slot['raw']}
            return out
        slot['rule'] = answer

    out['slots'] = slots
    out['status'] = 'ACCEPTED' if slots else 'ALREADY_PRESENT'
    if not slots:
        out['reason'] = 'ALREADY_PRESENT_SAME'
    return out


# ---------------------------------------------------------------- 答案对象

def _out_of_scope_members(members):
    return [member for member in members if member not in ATTR_FIELD]


def _other_slot_texts(attr, view, claimed_attrs):
    parts = []
    for other in TARGET_ATTRS:
        if other == attr:
            continue
        slot_view = view['slots'][other]
        if slot_view['neutral']:
            parts.append('%s=%s（中性）' % (slot_view['slot'], num_text(slot_view['raw'])))
        elif other in claimed_attrs:
            parts.append('%s=%s（非中性，已由本行「%s」答案消费，不重复）'
                         % (slot_view['slot'], num_text(slot_view['raw']), other))
        else:
            parts.append('%s=%s（非中性，未主张）'
                         % (slot_view['slot'], num_text(slot_view['raw'])))
    return '、'.join(parts)


def _unruled_text(view):
    parts = []
    for name in UNRULED_SLOTS:
        item = view['unruled'][name]
        if item['state'] == 'missing':
            parts.append('%s=缺失' % name)
        elif item['state'] == 'null':
            parts.append('%s=null' % name)
        elif item['value'] is None:
            parts.append('%s=%r(%s)' % (name, item['raw'], item['state']))
        else:
            parts.append('%s=%r' % (name, item['raw']))
    return '、'.join(parts)


def _value_text(attr, rule):
    head = str(rule.get('value_text') or '').rstrip('。')
    if attr == '攻撃力':
        tail = '口径：上面是乘进自身攻击因子的乘数，不是百分点的加算，也不是最终伤害倍率'
    elif attr == '移動速度':
        tail = '口径：上面是移动速度乘数，不是加算百分点，也不是最终移动值'
    else:
        tail = ('口径：上面是乘进受伤量因子的乘数（承伤比例），方向按代码语义，'
                '不按名称「防御」改写')
    return '%s；%s' % (head, tail)


def _conditions_text(cid, slot):
    return ('句面条件「戦闘時」；载体 supporterskill|%d 的 %s 字段引用本记录（abi 位置逐字取自'
            '原记录）；type=8 记录被装载即生效（IsEnableAbility 对该 type 无条件返回 true）；'
            '以该能力被装载并进入玩家侧 apply 路径为前提（规则 limits 原文）；不另加 Wave／'
            '地形／所属／サブパーティ／味方全体 限定'
            % (cid, slot['abi_field']))


def _target_text():
    return ('type=8 的原生 apply 路径把本项乘进「持有该能力者自身」的攻击／移动／受伤量因子；'
            '本批不推断装备该羁绊的角色名单与最终受取者资格')


def build_answers(cid, row, res, tab=None):
    """把 ``evaluate`` 的接受槽位渲染成值行对象（复用 rules 既有换算）。"""
    if res.get('status') not in ('ACCEPTED',):
        return []
    tab = tables() if tab is None else tab
    japanese = str(row.get('japanese') or '')
    members = res['sentence']['members']
    claimed_attrs = {slot['attr'] for slot in res['slots']}
    others_members = _out_of_scope_members(members)
    existing = res.get('existing_answers') or []
    existing_keys = [item['rule_key'] for item in existing if item.get('rule_key')]
    answers = []
    for slot in res['slots']:
        attr = slot['attr']
        rule = slot['rule']
        view = slot['view']
        source = {
            'table': TABLE,
            'record_id': slot['record_id'],
            'layer': slot['layer'],
            'source_key': SOURCE_KEY_SKILLLIST_CACHE if slot['layer'] == 'CACHE'
            else SOURCE_KEY_SKILLLIST_APK,
            'json_pointer': '/%s/%d' % (TABLE, slot['index']),
            'record_key': '%s#/%s/%d' % (
                SOURCE_KEY_SKILLLIST_CACHE if slot['layer'] == 'CACHE'
                else SOURCE_KEY_SKILLLIST_APK, TABLE, slot['index']),
            'field_path': slot['field'],
            'field': slot['field'],
            'field_json_pointer': '/%s/%d%s' % (TABLE, slot['index'], slot['field']),
        }
        carrier_source = row.get('source') or {}
        carrier = {
            'table': SUPPORTER_TABLE,
            'record_id': cid,
            'layer': 'CACHE',
            'reference_field': REF_FIELD,
            'source_key': SOURCE_KEY,
            'json_pointer': carrier_source.get('json_pointer'),
            'record_key': carrier_source.get('record_key'),
            'abi_field': slot['abi_field'],
            'raw_record_sha256': carrier_source.get('raw_record_sha256'),
            'source_sha256': carrier_source.get('source_sha256'),
        }
        disclosure = []
        disclosure.append(
            'C13-P1 候选值行：句面「戦闘時、…」中的「%s」→ supporterskill|%d 的 %s 字段'
            '（原记录 abi 引用）→ skilllist|%d（%s 层，ability %d）→ %s；规则键 %s；原值 %s'
            '（float32 原样保留，不做十进制改写）'
            % (attr, cid, slot['abi_field'], slot['record_id'], slot['layer'], ABILITY,
               slot['field'], slot['rule_key'], num_text(slot['raw'])))
        disclosure.append('方向审核：' + direction_text(attr, slot['raw']))
        disclosure.append('槽位 1:1：本记录非中性 scope 槽＝%s，与本行主张一致；同记录其他 scope 槽 %s'
                          % ('、'.join(view['nonneutral']),
                             _other_slot_texts(attr, view, claimed_attrs)))
        disclosure.append('无规则槽均为中性登记值：' + _unruled_text(view))
        if others_members:
            disclosure.append('句面同句其他效果（%s）不在本批：只走 supporterskill 原记录 '
                              'abiN→ability %d，不处理 type18／type9 及其他类型，也不猜其槽位'
                              % ('、'.join(others_members), ABILITY))
        if existing:
            disclosure.append('本行既有答案 %d 条（%s）原样保留，不重复、不改写'
                              % (len(existing), '、'.join(existing_keys) or '原文数字行'))
        disclosure.append(
            '证据档：数值侧复用 rules.json 已确认换算（规则体状态「%s」），载体正文同值；'
            '句面→载体归属与装载／生效关联为「推断」（结构门控，未做逐记录执行确认）'
            % rule.get('rule_status'))
        disclosure.append(LIMITS_TEXT)
        answer = {
            'cid': cid,
            'row_id': row.get('row_id'),
            'rule_key': slot['rule_key'],
            'effect_attribute': attr,
            'value': _value_text(attr, rule),
            'value_text': rule.get('value_text'),
            'quantity_kind': rule.get('quantity_kind'),
            'unit': rule.get('unit'),
            'raw_value': slot['raw'],
            'field_path': slot['field'],
            'table': TABLE,
            'effect_type': ABILITY,
            'record_id': slot['record_id'],
            'layer': slot['layer'],
            'source': source,
            'carrier': carrier,
            'abi_field': slot['abi_field'],
            'abi_text': slot['abi_text'],
            'abi_slots': {
                'nonneutral': view['nonneutral'],
                'slots': {name: {'raw': item['raw'], 'state': item['state'],
                                 'neutral': item['neutral']}
                          for name, item in ((a, view['slots'][a]) for a in TARGET_ATTRS)},
                'unruled': {name: {'raw': item['raw'], 'state': item['state']}
                            for name, item in view['unruled'].items()},
            },
            'numeric_source': '%s#%s（本批按记录原值取值，不重写公式）'
                              % (RULES_FILE, slot['rule_key']),
            'numeric_evidence': '确认',
            'association_evidence': '推断',
            'evidence_scope': SCOPE,
            'answer_status': rule.get('answer_status'),
            'quantitative': True,
            'conversion': rule.get('conversion'),
            'base_definition': rule.get('base_definition'),
            'target': _target_text(),
            'object_note': ('对象：句面「戦闘時、…が上がる」无「味方全体／所属／サブパーティ／'
                            '自身の」等限定语，按 type8 自身因子口径；载体原始引用只给 abiN→'
                            '记录号，不推断受取者名单'),
            'conditions': _conditions_text(cid, slot),
            'rule_status': rule.get('rule_status'),
            'rule_body_status': rule.get('rule_status'),
            'rule_limits': rule.get('rule_limits'),
            'evidence': rule.get('evidence') or [],
            'evidence_grade': {
                'rule_body': rule.get('rule_status'),
                'numeric_value': '确认（复用 rules.json 换算；载体正文数字与原值一致）',
                'sentence_to_carrier': ('推断（句首「戦闘時、」属性链＋载体正文属性＋唯一非中性'
                                        '槽位；未逐记录执行确认）'),
                'load_and_apply': '推断（未做玩家装载／实机验证）',
            },
            'context': japanese,
            'note': '；'.join(disclosure),
            'limitations': LIMITS_TEXT,
            'backlog_id': slot['backlog_id'],
            'backlog_effect_type': attr,
            'claim': {
                'backlog_id': slot['backlog_id'],
                'effect_type': attr,
                'sentence': japanese,
                'leading_members': list(members),
            },
            'binding': {
                MARKER_KEY: {
                    'scope': SCOPE,
                    'structure_scope': STRUCTURE_SCOPE,
                    'module': MODULE_VERSION,
                    'cid': cid,
                    'row_id': row.get('row_id'),
                    'carrier_pointer': carrier['json_pointer'],
                    'carrier_ability_id': cid,
                    'abi_field': slot['abi_field'],
                    'record_id': slot['record_id'],
                    'layer': slot['layer'],
                    'resolution': slot['resolution'],
                    'cache_present': slot['cache_present'],
                    'apk_present': slot['apk_present'],
                    'apk_shadow_divergent': bool((slot.get('apk_shadow') or {})
                                                 .get('divergent_fields')),
                    'rule_key': slot['rule_key'],
                    'raw': slot['raw'],
                    'effect_attribute': attr,
                    'sentence_member': attr,
                    'leading_members': list(members),
                    'text_attrs': view['supports'],
                    'slot_attrs': view['nonneutral'],
                    'direction_ok': direction_ok(attr, slot['raw']),
                    'backlog_id': slot['backlog_id'],
                    'evidence_grade': {
                        'numeric_value': '确认',
                        'sentence_to_carrier': '推断',
                        'load_and_apply': '推断',
                    },
                }
            },
        }
        answers.append(answer)
    return answers


# ---------------------------------------------------------------- 页面消费（候选未接线）

def apply_to_skill(cid, skill, *, tab=None, backlog=None, scope_cids=None):
    """深拷贝 skill 并给通过判定的行追加值行；**不改输入、不写盘**（候选未接线）。"""
    tab = tables() if tab is None else tab
    new_skill = copy.deepcopy(skill)
    reports = []
    new_answers = []
    for row in new_skill.get('rows') or []:
        if str(row.get('reference_field') or '') != REF_FIELD:
            continue
        res = evaluate(cid, row, skill=new_skill, tab=tab, backlog=backlog,
                       scope_cids=scope_cids)
        report = {'row_id': row.get('row_id'), 'status': res['status'],
                  'reason': res['reason'], 'answers': 0, 'already_present': []}
        if res['status'] == 'ACCEPTED':
            answers = build_answers(cid, row, res, tab=tab)
            if answers:
                row['answers'] = list(row.get('answers') or []) + answers
                row[MARKER_KEY] = {
                    'scope': SCOPE,
                    'structure_scope': STRUCTURE_SCOPE,
                    'module': MODULE_VERSION,
                    'candidate_only': True,
                    'carrier_pointer': (row.get('source') or {}).get('json_pointer'),
                    'abi_fields': sorted({answer['abi_field'] for answer in answers}),
                    'record_ids': sorted({answer['record_id'] for answer in answers}),
                    'rule_keys': [answer['rule_key'] for answer in answers],
                    'evidence_grade': {'numeric_value': '确认',
                                       'sentence_to_carrier': '推断',
                                       'load_and_apply': '推断'},
                }
                report['answers'] = len(answers)
                new_answers.extend(answers)
        elif res['status'] == 'ALREADY_PRESENT':
            report['already_present'] = res.get('already_present') or []
        reports.append(report)
    if new_answers:
        new_skill[MARKER_KEY] = {
            'scope': SCOPE,
            'module': MODULE_VERSION,
            'candidate_only': True,
            'record_id': new_skill.get('record_id'),
            'rows': [report['row_id'] for report in reports if report['answers']],
            'answers': len(new_answers),
        }
    return {'skill': new_skill, 'rows': reports, 'answers': new_answers}


# ---------------------------------------------------------------- 候选构建

def load_backlog(root=None):
    """加载 Y.G. 未解 backlog（kind=effect）→ row_id → 效果项列表；不存在即零出值。"""
    root = Path(root).resolve() if root is not None else ROOT
    payload = read_json(root / YG_ITEMS_FILE)
    backlog = collections.defaultdict(list)
    yg_cids = set()
    for item in payload.get('items') or []:
        if item.get('yg'):
            yg_cids.add(item.get('cid'))
        if item.get('kind') == 'effect':
            backlog[item.get('row_id')].append(item)
    return {'meta': payload.get('meta') or {}, 'backlog': dict(backlog),
            'yg_cids': yg_cids}


def _page_path(root, cid):
    return root / PAGES_DIR / str(cid) / 'card.json'


def iter_supporter_pages(root, tab):
    """按 cid 升序遍历有 supporterskill 载体的页面（缺页面即跳过并单列）。"""
    cids = sorted({record.get('ability_id') for record in tab['supporter']
                   if isinstance(record.get('ability_id'), int)
                   and not isinstance(record.get('ability_id'), bool)})
    for cid in cids:
        path = _page_path(root, cid)
        if path.exists():
            yield cid, path, read_json(path)
        else:
            yield cid, path, None


def build_candidate(root=None, write=True):
    """构建本任务候选 JSON（接受行＋剔除行＋上界对账＋来源/数量审计）。"""
    root = Path(root).resolve() if root is not None else ROOT
    tab = tables(root)
    backlog_info = load_backlog(root)
    backlog = backlog_info['backlog']
    yg_cids = backlog_info['yg_cids']

    accepted_rows = []
    row_verdicts = []
    rejections = collections.Counter()
    scope_audit = {
        'supporter_records': len(tab['supporter']),
        'supporter_cids': 0,
        'supporter_cids_with_page': 0,
        'supporter_cids_without_page': [],
        'yg_supporter_cids': 0,
        'non_yg_supporter_cids_skipped': 0,
        'yg_bond_rows': 0,
        'evaluated_rows': 0,
        'rows_with_target_claims': 0,
        'rows_without_target_claims': 0,
    }
    page_hashes = {}
    cid_seen = set()
    for cid, path, page in iter_supporter_pages(root, tab):
        if cid not in cid_seen:
            cid_seen.add(cid)
            scope_audit['supporter_cids'] += 1
        if page is None:
            scope_audit['supporter_cids_without_page'].append(cid)
            continue
        scope_audit['supporter_cids_with_page'] += 1
        page_hashes[str(cid)] = sha256_file(path)
        if cid not in yg_cids:
            scope_audit['non_yg_supporter_cids_skipped'] += 1
            continue
        scope_audit['yg_supporter_cids'] += 1
        for group in page.get('groups') or []:
            for skill in group.get('skills') or []:
                if str(skill.get('reference_field') or '') != REF_FIELD:
                    continue
                for row in skill.get('rows') or []:
                    scope_audit['yg_bond_rows'] += 1
                    scope_audit['evaluated_rows'] += 1
                    claims = [item for item in (backlog.get(row.get('row_id')) or [])
                              if item.get('kind') in (None, 'effect')
                              and item.get('effect_type') in ATTR_FIELD]
                    if claims:
                        scope_audit['rows_with_target_claims'] += 1
                    else:
                        scope_audit['rows_without_target_claims'] += 1
                    res = evaluate(cid, row, skill=skill, tab=tab, backlog=backlog,
                                   scope_cids=yg_cids)
                    verdict = {
                        'cid': cid,
                        'row_id': row.get('row_id'),
                        'japanese': row.get('japanese'),
                        'carrier_pointer': (row.get('source') or {}).get('json_pointer'),
                        'status': res['status'],
                        'reason': res['reason'],
                        'detail': res['detail'],
                        'has_target_claims': bool(claims),
                        'claims': [{'effect_type': item.get('effect_type'),
                                    'backlog_id': item.get('backlog_id')} for item in claims],
                        'exact_text_owners': [],
                        'answer_count': 0,
                    }
                    if res['status'] == 'REJECTED':
                        verdict['exact_text_owners'] = _row_owners(tab, row)
                        rejections[res['reason']] += 1
                        row_verdicts.append(verdict)
                        continue
                    # ACCEPTED / ALREADY_PRESENT
                    answers = build_answers(cid, row, res, tab=tab)
                    verdict['answer_count'] = len(answers)
                    row_verdicts.append(verdict)
                    accepted_rows.append({
                        'cid': cid,
                        'row_id': row.get('row_id'),
                        'japanese': row.get('japanese'),
                        'carrier': {
                            'table': SUPPORTER_TABLE,
                            'record_id': cid,
                            'layer': 'CACHE',
                            'json_pointer': (row.get('source') or {}).get('json_pointer'),
                            'record_key': (row.get('source') or {}).get('record_key'),
                            'raw_record_sha256': (row.get('source') or {}).get(
                                'raw_record_sha256'),
                        },
                        'claims': res['claims'],
                        'leading_members': res['sentence']['members'],
                        'out_of_scope_members': _out_of_scope_members(res['sentence']['members']),
                        'existing_answers': res['existing_answers'],
                        'already_present': res['already_present'],
                        'answers': answers,
                        'answer_count': len(answers),
                    })

    answers = [answer for row in accepted_rows for answer in row['answers']]
    answers.sort(key=lambda answer: (answer['cid'], TARGET_ATTRS.index(
        answer['effect_attribute']), answer['rule_key']))
    accepted_rows.sort(key=lambda row: row['cid'])

    by_attribute = collections.Counter(answer['effect_attribute'] for answer in answers)
    by_record = collections.Counter(str(answer['record_id']) for answer in answers)
    by_layer = collections.Counter(answer['layer'] for answer in answers)
    by_resolution = collections.Counter(
        answer['binding'][MARKER_KEY]['resolution'] for answer in answers)

    upstream = None
    upstream_path = root / UPSTREAM_CANDIDATE_FILE
    if upstream_path.exists():
        payload = read_json(upstream_path)
        upstream_effects = {(row['cid'], row['row_id'], item['effect_type'],
                            item['record_id'], item['layer'], item['raw_value'])
                           for row in payload.get('accepted') or []
                           for item in row.get('candidates') or []}
        candidate_effects = {(answer['cid'], answer['row_id'], answer['effect_attribute'],
                              answer['record_id'], answer['layer'], answer['raw_value'])
                             for answer in answers}
        removed = sorted(upstream_effects - candidate_effects)
        added = sorted(candidate_effects - upstream_effects)
        upstream = {
            'path': UPSTREAM_CANDIDATE_FILE,
            'sha256': sha256_file(upstream_path),
            'rows': payload.get('accepted_rows'),
            'cids': payload.get('accepted_cids'),
            'answers': payload.get('accepted_answers'),
            'effect_counts': payload.get('effect_counts'),
            'removed_effects': [
                {'cid': cid, 'row_id': row_id, 'effect_type': attr,
                 'record_id': record_id, 'layer': layer, 'raw_value': raw}
                for cid, row_id, attr, record_id, layer, raw in removed],
            'added_effects': [
                {'cid': cid, 'row_id': row_id, 'effect_type': attr,
                 'record_id': record_id, 'layer': layer, 'raw_value': raw}
                for cid, row_id, attr, record_id, layer, raw in added],
            'removed_count': len(removed),
            'added_count': len(added),
            'subset_of_upstream': not added,
        }
    else:
        upstream = {'path': UPSTREAM_CANDIDATE_FILE, 'missing': True}

    upstream_removed_rows = {item['row_id'] for item in upstream.get('removed_effects') or []}
    exclusions = []
    for verdict in row_verdicts:
        if verdict['status'] != 'REJECTED' or not verdict['has_target_claims']:
            continue
        if verdict['row_id'] not in upstream_removed_rows:
            continue
        exclusions.append({
            'cid': verdict['cid'],
            'row_id': verdict['row_id'],
            'japanese': verdict['japanese'],
            'carrier_pointer': verdict['carrier_pointer'],
            'reason': verdict['reason'],
            'detail': verdict['detail'],
            'upstream_effects': [item for item in verdict['claims']],
            'exact_text_owners': verdict['exact_text_owners'],
            'conclusion': ('候选剔除：上游候选上限内的效果，本批证据不足不出值'
                           '（条件句／对象句不归 type8，或同一效果重复主张）'),
        })
    exclusions.sort(key=lambda item: (item['cid'], item['row_id']))

    non_candidate_rows = [
        {'cid': verdict['cid'], 'row_id': verdict['row_id'],
         'japanese': verdict['japanese'], 'reason': verdict['reason'],
         'detail': verdict['detail'],
         'claims': verdict['claims'],
         'exact_text_owners': verdict['exact_text_owners']}
        for verdict in row_verdicts
        if verdict['status'] == 'REJECTED' and verdict['has_target_claims']
    ]
    non_candidate_rows.sort(key=lambda item: (item['cid'], item['row_id']))
    protected_rows = [
        {'cid': verdict['cid'], 'row_id': verdict['row_id'], 'reason': verdict['reason'],
         'japanese': verdict['japanese'], 'claims': verdict['claims']}
        for verdict in row_verdicts
        if verdict['cid'] in ZERO_TOUCH_CIDS and verdict['claims']
    ]
    protected_rows.sort(key=lambda item: (item['cid'], item['row_id']))
    rejected_upstream = []
    if upstream_path.exists():
        payload = read_json(upstream_path)
        ambiguous = {(item.get('cid'), item.get('row_id'), item.get('effect_type')): item
                     for item in payload.get('rejected_ambiguous') or []}
        for verdict in row_verdicts:
            keys = {(verdict['cid'], verdict['row_id'], claim['effect_type'])
                    for claim in verdict['claims']}
            hits = [(key, ambiguous[key]) for key in keys if key in ambiguous]
            if not hits:
                continue
            rejected_upstream.append({
                'cid': verdict['cid'],
                'row_id': verdict['row_id'],
                'japanese': verdict['japanese'],
                'reason': verdict['reason'],
                'detail': verdict['detail'],
                'claims': verdict['claims'],
                'exact_text_owners': verdict['exact_text_owners'],
                'upstream_reasons': sorted({item.get('reason') for _key, item in hits}),
                'upstream_effect_types': sorted({key[2] for key, _item in hits}),
                'conclusion': ('上游已按同一效果重复主张排除；本批复核仍为不出值，不得重新纳入'),
            })
    rejected_upstream.sort(key=lambda item: (item['cid'], item['row_id']))

    meta = backlog_info['meta']
    result = {
        'schema': 'c13_p1_supporterskill_type8_candidate/v1',
        'module': MODULE_VERSION,
        'candidate_only': CANDIDATE_ONLY,
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'task_card': 'docs/tasks/20261031-c13-p1-supporterskill-type8.md',
        'cycle_card': 'docs/tasks/20261031-c13-cycle.md',
        'inputs': {
            'supporter': {
                'path': '%s/%s' % (CACHE_DIR, SUPPORTER_FILE),
                'sha256': sha256_file(read_path(root / CACHE_DIR / SUPPORTER_FILE, root=root)),
                'records': len(tab['supporter']),
            },
            'skilllist_cache': {
                'path': '%s/%s' % (CACHE_DIR, SKILLLIST_FILE),
                'sha256': sha256_file(read_path(root / CACHE_DIR / SKILLLIST_FILE, root=root)),
                'records': tab['cache_count'],
            },
            'skilllist_apk': {
                'path': APK_SKILLLIST,
                'sha256': sha256_file(root / APK_SKILLLIST),
                'records': tab['apk_count'],
            },
            'rules': {
                'path': RULES_FILE,
                'sha256': sha256_file(root / RULES_FILE),
                'keys': len(tab['rules']),
                'type8_keys': sorted(key for key in tab['rules']
                                     if key.startswith('%s|%d|' % (TABLE, ABILITY))),
            },
            'yg_items': {
                'path': YG_ITEMS_FILE,
                'sha256': sha256_file(root / YG_ITEMS_FILE),
                'snapshot_id': meta.get('snapshot_id'),
                'campaign_signature': meta.get('campaign_signature'),
                'yg_items': meta.get('yg_items'),
            },
            'pages_dir': PAGES_DIR,
        },
        'scope_audit': scope_audit,
        'counts': {
            'rows': len(accepted_rows),
            'cids': len({row['cid'] for row in accepted_rows}),
            'answers': len(answers),
            'by_attribute': dict(by_attribute),
            'by_record': dict(by_record),
            'by_layer': dict(by_layer),
            'by_resolution': dict(by_resolution),
            'rows_with_existing_answers': sum(1 for row in accepted_rows
                                              if row['existing_answers']),
            'existing_answers_preserved': sum(len(row['existing_answers'])
                                              for row in accepted_rows),
            'rows_already_present': sum(1 for row in accepted_rows
                                        if row['answer_count'] == 0),
            'excluded_rows': len(exclusions),
            'non_candidate_rows_with_target_claims': len(non_candidate_rows),
            'protected_rows_total': sum(1 for verdict in row_verdicts
                                        if verdict['cid'] in ZERO_TOUCH_CIDS),
            'protected_rows_with_target_claims': len(protected_rows),
            'upstream_excluded_reverified': len(rejected_upstream),
            'rejections_by_reason': dict(rejections),
        },
        'upstream_comparison': upstream,
        'exclusions': exclusions,
        'non_candidate_rows': non_candidate_rows,
        'protected_rows': protected_rows,
        'upstream_excluded_reverified': rejected_upstream,
        'rows': accepted_rows,
        'answers': answers,
        'evidence': {
            'page_sha256': dict(sorted(page_hashes.items())),
            'rule_evidence': sorted({tuple(answer['evidence']) for answer in answers}),
        },
        'limits': [
            '候选实现，未接入 card_page_data.py；未改 rules.json／rules.py／effect_ledger.py／正式 pages／账本。',
            '未运行正式全库生成；候选独立审查通过前不得合并冻结。',
            'association_evidence 全为推断：句面→abi 载体、装载与生效未逐记录执行确认，未实机。',
            '不写玩家解锁、最终面板、最终伤害/最终HP、叠加上限、Chain 影响。',
            '仅 ability 8 的 param1/param2/param3；type18、type9、type29 及其他类型不在本批。',
            'CACHE 与 APK 同号记录不合并；本轮全部来源记录 CACHE 缺 ID、逐 ID 回退 APK。',
            '5 条上游候选因条件句／对象句归属另一 abi 记录被剔除；30302 重复攻击主张不重新纳入。',
        ],
    }
    if write:
        out_path = root / CANDIDATE_FILE
        out_path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(result, ensure_ascii=False, indent=1, sort_keys=False)
        out_path.write_text(text + '\n', encoding='utf-8')
    return result


def main():
    result = build_candidate()
    counts = result['counts']
    print(json.dumps({key: result[key] for key in
                      ('module', 'scope', 'counts', 'scope_audit')},
                     ensure_ascii=False, indent=1))
    print('candidate', CANDIDATE_FILE)
    print('rows %d cids %d answers %d' % (counts['rows'], counts['cids'],
                                          counts['answers']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
