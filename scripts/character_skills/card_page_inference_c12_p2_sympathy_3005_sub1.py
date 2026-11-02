# -*- coding: utf-8 -*-
"""C12-P2 ``skilllist|3005|``（共鳴アビリティ主记录 M）→ 相邻 ``sub1`` 子记录
（``skillid = M + 1``、``ability = 3000``）**首段** 攻撃力・一定時間 段：候选实现。

任务卡 ``docs/tasks/20261031-c12-p2-sympathy-3005-sub1.md``；选题预检
``output/character_skills/c12_p2_selection_20261031/selection_report.md``（PASS，16 门）；
同族先例 ``scripts/character_skills/card_page_inference_b7_sympathy.py``（23 行已上线）。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；正式页面、
``rules.json``、``effect_ledger`` 均未改动；正式全库生成不在本阶段。账本所需 **0 条新映射**：
``scripts/character_skills/effect_ledger.py:469-470`` 已有 ``skilllist|3000|/param1``→攻撃力、
``/param2``→攻撃力、``/param8``→クリティカル威力、``/param6``→継続時間 四条既有映射，本批只用
其中三条（p1／p2／p6）。

本批与 C12-P1 的结构差别（**本文件的唯一新判断**）
------------------------------------------------
C12-P1 的 42 行是 ``skilllist|3000|`` 记录**自身**承载数值；本批 34 行的行记录是
``skilllist|3005|`` 的 **M**，M 自身只有 ``param1``／``param2``（实测 ∈{1,2}／∈{1,4} 的**整数**，
b7 口径：Chain 发动侧配置），**没有** ``param0``／``param6`` 及 p3..p9，数值在其 ``sub`` 唯一的
相邻子记录上（``ability=3000``）。因此：

* **M→sub1 是数据侧结构对应**（6 项结构证据逐行实核，见 ``evaluate`` 的 D3/D4），
  **不是已核实的装载路径**——``output/ordinary_effects/ability3000/dispatch.txt:10`` 与
  ``qualification.txt:26`` 的分派是 ``cmp w0,#0xbb8``（＝3000）后 ``b.ne`` 返回，3005 主记录
  的处理器入口未被既有原生证据覆盖（b7 同结论）。故答案 ``numeric_evidence``／
  ``association_evidence`` 一律「推断」，**不升「确认」**。
* **M 自身 param 零消费**：``M_ZERO_CONSUMED`` 记录 M 的 p1/p2 原值并声明不消费；模块从
  ``build_answers`` 起只读 **sub 记录**，且 D5b 要求 M 上不存在任何值槽（p0/p3..p9）、
  M 的 p1/p2 为整数 ≥1（若某天出现 0.1 这类增量值即拒绝，防止有人把 M 当载体）。
* **不建任何 ``skilllist|3005|`` 规则键**，也不写「3005 规则」；三条换算全部
  ``rules.answer_for('skilllist', 3000, ...)`` 套在**子记录自己的字段**上。

**本批不承载クリティカル系**：同族另有 23 行（b7，句面「攻撃力＋クリティカル威力」、sub 带
``param8``）已由批 7 以 4 条答案上线；它们的句面主张 クリティカル威力，而本批只携带
攻撃力／一定時間，因此对这些行整行拒绝（``CRIT_ATTRIBUTE_NOT_IN_BATCH``），不做「只答攻撃力、
把クリ威力悄悄留空」的半答。

句子与范围
----------
行句面是 M 正文 ``text`` 的**第 1 个句子单位**（页面 ``fragment_index == 0``，row_id 尾部 ``-f0``）::

    【共鳴アビリティ】自身を含む<味方>が≪共鳴必殺≫を発動するたび、
    戦場にいる<味方>の<属性A>と<属性B>[と<属性C>]が一定時間上がる。
    （回復形态尾句：…が一定時間上がり、HPが上限を超えて回復する。）

本批只对**已确认槽**出值，且与句面主张 1:1：

* 攻撃力 → sub ``/param1``（普通攻击加算增量）＋ ``/param2``（技能攻击加算增量）＝**2 条**
* 一定時間 → sub ``/param6``（45 游戏秒）＝**1 条**
* 防御力→p4（29 行，负值 −0.025）、移動速度→p3（4 行，0.1）、回復→p5（1 行，0.3＋flag1_1=512）
  **无规则，不出值**，也不按相关性猜槽位（p4 负值与「上がる」句向矛盾，b7 已登记）。
* ``/param7``／``/param8``：34 行**均无值**，若出现即拒绝（句面无クリティカル系主张）。

第二段竞争句（预检 §5.3b）
--------------------------
M 正文按字面 ``\\n`` 切**恰 2 段**：第 1 段含本行 buff 句（34/34 含「戦場にいる」），第 2 段是
Chain 必殺技描述（34/34 **不含**「戦場にいる」）。``一定時間上が`` 在正文出现 **1 次 19 行／
2 次 15 行**；第二处一律在第 2 段引号内、主语为「自身」，但属性组合并不统一（实测 6／7／2 三种
形态）。本模块的判据是**句面对象标记**（第 2 段不含「戦場にいる」且主语「自身」），
**不是**「第二处一定是攻撃速度」的猜想，也**不是**引擎侧装载确认；15 行形态逐行进
``res['competition']`` 供披露，第二段一条值都不出。

b7 hint 与 S3 **保留**（不拆半晋级、不宣称整行完整）
--------------------------------------------------
* **不写** ``row['binding_conditions']``，不清 split 标记，不改 ``partial``／``row_class``；
* 不删 ``inference_b7_hint``，不从 ``unknown_reasons`` 移除该 G4 hint 文本；
* 行仍「拆分待核查」：触发子句（``【共鳴アビリティ】…発動するたび``）不在本批覆盖内，
  账本 S3 原样保留；p2 与 p1 同属一条「攻撃力」主张 → 账本记 S4（与 ``10215`` 先例同形）；
  完整行增量 **0**。

准入是**结构规则 + 显式批次边界**，不是 row_id／记录／原值白名单
--------------------------------------------------------------
模块内没有 row_id、卡号、记录号或「原值 == 字面量」常量（``run_checks.py`` 静态用例断言）。
唯一的白名单是 **1 条已登记命名变体**（30335 的子记录名把角色词缩短，预检 §5.1#6 冻结），
按 **(M 名, sub 名)** 精确对登记，属披露而非 cid 白名单。

判定顺序：

    D1 行身份：``group == 'sympathy'``、``reference_field ==
       'sympathy_skill_info[_id=<cid>].ability0'``、``fragment_index == 0``，
       日语按结构解析出属性序列（前缀／两种尾句逐字，属性来自六属性表、无重复、含攻撃力）。
    D2 同层来源：``layer == 'CACHE'``、``source_key == CACHE/skilllist.data5.json.raw``、
       ``field == '/text'``、``json_pointer`` 匹配 ``/skilllist/<n>``。
    D3 父链：``sympathy_skill_info[_id=<cid>].ability0`` = 页面载体记录号 M；``skilllist`` 中
       该 ``skillid`` 全表唯一命中且下标 = 指针 ``<n>``；``M.ability == 3005``；
       ``M.sub`` 恰 1 个元素且 ``== M + 1``。
    D4 子记录（值载体）：``sub`` 全表唯一、``ability == 3000``、自身 ``sub`` 为空；
       全 8,634 条里被父引用**恰 1 次**且父即 M；无任何 ``str0`` 指向它；不在
       ``sympathy_skill_info`` 的任何字段值里；不在 ``charainfo`` 的任何标量值里；
       命名对应成立（``sub``／``sub1`` ＋ M 名去 ``■``，或命中 1 条登记变体）。
    D5a 子记录槽位（**只消费已确认槽，且与句面主张严格 1:1**）：``param0`` 整数且＝1
       （句面「自身を含む」）；``param1``／``param2`` 有限正、落在加算增量域 (0,1]；
       ``param6`` 有限正；防御力／移動速度／回復 三槽「有值 ⇔ 句面点名」双向一致；
       ``param7``／``param8`` 必须缺省；``flag1_1``（512）与「HPが上限を超えて回復する」1:1
       且只作机制披露；``param9／iParam0／iParam1／flag0_x／flag1_0`` 非零拒绝；``flag`` 非零拒绝。
    D5b **M 零消费**：M 上不得出现 ``param0``／``param3``..``param9``／``iParam0``／``iParam1``
       （出现即拒绝，避免把 Chain 配置或别处值当载体）；``M.param1``／``M.param2`` 必须是
       整数 ≥1（Chain 配置形态），一旦是 (0,1) 增量即拒绝并显式登记。
    D6 段落与竞争句：字面 ``\\n`` 切恰 2 段；段 0 含本行句面且含「戦場にいる」；段 1 **不含**
       「戦場にいる」；``一定時間上が`` 计数 ∈{1,2}；为 2 时第二处必须在段 1、且段 1 含
       「1stChain以上」与「自身」；形态归类（速度のみ／自身の攻撃力のみ／速度＋攻撃力言及）
       只登记不消费。另：行句面在记录内唯一、是第 1 个句子单位，记录其余单位只能含
       ``この効果は、サブパーティでも発動する。``；同卡该 ``reference_field`` 内恰 1 行可解析、
       且 ``-f1`` 尾句行必须存在。
    D7 规则语义：p1／p2／p6 的 ``answer_for`` 必须返回非空，``meaning_zh`` 含对应关键词
       （普通攻击／技能攻击／持续），``answer_status == CONFIRMED_NUMERIC``。漂移即拒绝。
    D8 幂等：本批值槽同键已有答案——同记录（sub）同字段同原值同层 → ``ALREADY_PRESENT_SAME``
       （零写入）；其余 → ``ALREADY_ANSWERED``（只写披露 marker，不改写既有答案）。

**批次边界由调用方显式声明**：``apply_to_groups(data, cid, groups, *, scope_cids=...)``，缺省
``None`` → 一行都不处理（``NO_SCOPE_DECLARED``）。保护／禁推卡 20234／30102／30236／30239 在
模块内硬拒绝；30314（句含「全状態異常を回復する」）交给 D1 句面门拒绝，并在 run_checks 里
单列其拒绝理由，不混入零触碰名单。

接口
----
``evaluate(data, cid, row, rows=None, skill=None, tab=None)``          单行判定（不写入）。
``build_answers(data, cid, row, res, tab=None)``                       3 条答案对象（复用 rules）。
``apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None)``   正式页消费（候选未接线）。
``tables(data)`` / ``clone_tables(tab)``                               CACHE 主表只读索引（可注入）。
"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

MODULE_VERSION = 'c12_p2_sympathy_3005_sub1_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 本批证据 scope（写进答案与行级 metadata，供账本/页面按 scope 精确消费时对账）。
SCOPE = 'TEMPLATE_BATCH12_P2_SYMPATHY_3005_SUB1'
#: 结构判定自身 scope（行级 marker）。
STRUCTURE_SCOPE = 'C12_P2_SYMPATHY_3005_SUB1_STRUCTURE_20261031'
#: 行级 marker 键（每行至多一个本批键，不覆盖其他批的 marker）。
MARKER_KEY = 'inference_c12_p2_sympathy_3005_sub1'

TABLE = 'skilllist'
#: 行记录（正文承载）能力号：共鳴アビリティ主记录。
M_ABILITY = 3005
#: 值载体（相邻子记录）能力号：与 b7／C12-P1 同一批已确认规则族。
SUB_ABILITY = 3000
LAYER = 'CACHE'
REF_TEMPLATE = 'sympathy_skill_info[_id=%d].ability0'
TEXT_FIELD = '/text'
SOURCE_KEY = 'CACHE/skilllist.data5.json.raw'
#: CACHE 解码主表目录（与预检、C11／C12-P1 各批同源快照）。
BASE = 'output/cache_full_20261015_v3/decoded'
#: 共鸣索引表：``sympathy_skill_info[_id=<cid>].ability0`` → M 记录号。
SYMPATHY_TABLE = 'sympathy_skilllist.data5.json.raw'
SYMPATHY_KEY = 'sympathy_skill_info'
SYMPATHY_ID = '_id'
SYMPATHY_FIELD = 'ability0'
#: 角色索引表（反查「子记录不是任何角色的字段值」）。
CHARA_TABLE = 'charainfo.data5.json.raw'

#: 保护／禁推卡：本批零触碰（判定前硬拒绝）。30102 禁推卡；30236／30239 保护卡；
#: 20234 为既有边界（本批不涉及，保留硬拒绝以防误扩）。
ZERO_TOUCH_CIDS = frozenset({20234, 30102, 30236, 30239})
#: 句面排除（不属零触碰名单，交给 D1 句面门）：30314 首段含「全状態異常を回復する」。
SENTENCE_EXCLUDED_CIDS = frozenset({30314})

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
#: 第 1 段之后的同记录片段句（不归属、零触碰；D6 用于形状守卫）。
TRAILING_CLAUSE = 'この効果は、サブパーティでも発動する。'
#: 句面点名的属性全集（顺序即槽位顺序证据）。
ATTR_ORDER = ('攻撃力', '防御力', '移動速度', 'クリティカル発生率', 'クリティカル威力', '回復')
#: 已确认值槽：属性 → ((字段, 规则 meaning_zh 关键词), ...)。三条换算全部来自 skilllist|3000。
CONFIRMED_SLOTS = {
    '攻撃力': (('/param1', '普通攻击'), ('/param2', '技能攻击')),
    # 「一定時間」不是属性名而是时长子句：每条本族句面都含，值在 sub /param6。
    '継続時間': (('/param6', '持续'),),
}
#: 未确认槽：属性 → 字段。skilllist|3000 **没有** p3/p4/p5/p7 规则，本批不得出值。
UNCONFIRMED_SLOTS = {
    '防御力': '/param4',
    '移動速度': '/param3',
    '回復': '/param5',
}
#: 句面未主张即必须缺省的槽（34 行实测全缺）：出现即拒绝（不猜槽位）。
UNCLAIMED_ABSENT_SLOTS = ('param7', 'param8')
#: 本批**不承载**的属性：句面一旦主张即整行拒绝（同族 b7 的 23 行属这一形态）。
CRIT_ATTRS = ('クリティカル発生率', 'クリティカル威力')
#: 加算增量域：p1／p2 只接受 (0,1]（大于 1 会被误读成乘数，拒绝）。
INCREMENT_MAX = 1.0
#: 「自身を含む」⇒ 子记录 param0 必须让提供者自身参与。
PARAM0_SELF_INCLUSIVE = 1
#: 句面未主张的辅助筛位：必须缺省/零（不隐藏未知机制）。
AUX_SLOTS = ('param9', 'iParam0', 'iParam1', 'flag0_0', 'flag0_1', 'flag1_0')
#: 与「HPが上限を超えて回復する」1:1 的机制标记：只披露、不消费。
HEAL_FLAG_SLOT = 'flag1_1'
#: M 上**不得出现**的字段：出现即说明「值不在 M 上」的前提失效，必须拒绝而不是猜。
M_FORBIDDEN_SLOTS = ('param0', 'param3', 'param4', 'param5', 'param6', 'param7', 'param8',
                     'param9', 'iParam0', 'iParam1')
#: M 的 Chain 侧配置槽（整数 ≥1；不得是 (0,1) 增量）。
M_CHAIN_SLOTS = ('param1', 'param2')
#: 统计「一定時間上が」出现次数的字面（第二段竞争句判据）。
DURATION_PHRASE = '一定時間上が'
#: 第二段（竞争句）所在段必须含的触发标记（与句面对象标记并用）。
COMPETITION_MARKS = ('1stChain以上', '自身')

#: **唯一的命名白名单**：1 条已登记变体（30335 子记录把角色词缩短，预检 §5.1#6 冻结）。
#: 键＝(M 名, 子记录名)，值＝登记理由。其余一律要求 ``sub``／``sub1`` ＋（M 名去 ``■``）。
FROZEN_NAMING_VARIANTS = {
    ('■シンパシー_時空軍ミズクン_0-1', 'subシンパシー_ミズクン_0-1'):
        '预检 §5.1#6 已登记变体：子记录名把角色词「時空軍ミズクン」缩为「ミズクン」',
}

#: 页面既有答案里本批上线前应被本批替换为「已解」的通用未知原因（逐字）。
_STALE_REASONS = (
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '旧关键词候选未作为答案；不能排除对象或效果错配',
)
RESIDUAL_NOTE = ('C12-P2：首段 3005 主记录 M 的相邻 sub1 子记录（ability 3000）p1/p2/p6 按已确认'
                 '换算给值（M→sub1 为数据侧结构对应，原值与关联证据档均为推断，未做逐记录执行'
                 '确认）；M 自身 param1/param2 为 Chain 配置，零消费；防御力/移動速度/回復 仍'
                 '未知，p3/p4/p5 不消费；正文第 2 段的自身侧一定時間句不消费；b7 hint 与 S3 保留，'
                 '行仍「拆分待核查」')
RESIDUAL_LABEL = ('推断（C12-P2：3005 主记录的 sub1 子记录 p1/p2/p6 加算增量＋游戏秒；'
                  'M→sub1 数据侧结构对应、未核引擎装载；防御/移速/回復 未确认，S3 与 b7 hint 保留）')

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

def _charainfo_tokens(path):
    """charainfo 全表的标量值文本集合（用于「子记录不是任何角色字段值」的反查）。"""
    obj = _read(path)
    tokens = set()
    for value in obj.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if not isinstance(record, dict):
                continue
            for item in record.values():
                if isinstance(item, bool) or item is None:
                    continue
                if isinstance(item, (int, str)):
                    tokens.add(str(item))
    return tokens


def tables(data):
    """CACHE 解码主表（按 root 缓存，只读）。``tab`` 可由调用方注入（反例用）。

    ``skills`` 保留**数组下标**（行来源 ``/skilllist/<n>`` 按下标解析）；``by_id`` 是按
    skillid 的索引视图，二者须指向同一条记录才放行。``sympathy`` 是
    ``sympathy_skill_info[_id=<cid>].ability0`` 的索引，``sympathy_values`` 是它所有标量值
    的文本集合，``charainfo_tokens`` 是角色表所有标量值的文本集合。
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
        sympathy_values = set()
        for entry in sympathy.values():
            for value in entry.values():
                if isinstance(value, bool) or value is None:
                    continue
                if isinstance(value, (int, str)):
                    sympathy_values.add(str(value))
        _TABLES[key] = dict(skills=skills, sympathy=sympathy,
                            sympathy_values=sympathy_values,
                            charainfo_tokens=_charainfo_tokens(base / CHARA_TABLE),
                            root=root)
    return _TABLES[key]


def clone_tables(tab):
    """反例用：深拷贝只读索引（不改动全局缓存）。"""
    keep = ('skills', 'sympathy', 'sympathy_values', 'charainfo_tokens', 'root')
    return {k: (copy.deepcopy(v) if k != 'root' else v) for k, v in tab.items() if k in keep}


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


def paragraphs(record_text):
    """记录正文的段落（按**字面**反斜线＋n 切；本族实测恰 2 段）。"""
    return [part for part in str(record_text or '').split(_TEXT_SEP) if part.strip()]


def paragraph_spans(record_text):
    """段落的 ``(start, end)`` 偏移（与 ``paragraphs`` 同序同内容；供竞争句定位）。"""
    text = str(record_text or '')
    spans = []
    cursor = 0
    for part in text.split(_TEXT_SEP):
        if part.strip():
            spans.append((cursor, cursor + len(part)))
        cursor += len(part) + len(_TEXT_SEP)
    return spans


def _quoted_around(text, index):
    """取 ``index`` 处所在的「…」引号片段（没有则返回整段尾部）。"""
    left = text.rfind('「', 0, index)
    right = text.find('」', index)
    if left != -1 and right != -1:
        return text[left:right + 1]
    return text[index:index + 80]


def competition_shape(quote):
    """第二段竞争句的形态归类（只登记不消费；三类合计＝预检 6／7／2）。"""
    if '攻撃速度' in quote and '攻撃力' not in quote:
        return '速度のみ'
    if '自身の攻撃力が一定時間上が' in quote and '攻撃速度' not in quote:
        return '自身の攻撃力のみ'
    return '速度＋攻撃力言及'


def competition_view(record_text, sentence):
    """第二段竞争句视图：段落切分、``一定時間上が`` 计数、第二处位置与形态。"""
    text = str(record_text or '')
    paras = paragraphs(text)
    spans = paragraph_spans(text)
    total = text.count(DURATION_PHRASE)
    first_para = paras[0] if paras else ''
    detail = {
        'paragraphs': len(paras),
        'duration_phrase_total': total,
        'paragraph0_has_battlefield': '戦場にいる' in first_para,
        'paragraph1_has_battlefield': ('戦場にいる' in paras[1]) if len(paras) > 1 else None,
        'sentence_in_paragraph0': sentence in first_para,
    }
    second = None
    if total >= 2:
        index = text.find(DURATION_PHRASE, text.find(DURATION_PHRASE) + 1)
        quote = _quoted_around(text, index)
        last = paras[-1] if paras else ''
        last_span = spans[-1] if spans else (0, 0)
        second = {
            'offset': index,
            'in_paragraph1': (len(paras) > 1 and index >= last_span[0]),
            'has_1stchain': COMPETITION_MARKS[0] in last,
            'has_self': COMPETITION_MARKS[1] in last,
            'has_battlefield': '戦場にいる' in quote,
            'mentions_attack': '攻撃力' in quote,
            'shape': competition_shape(quote),
            'quote': quote,
        }
    detail['second'] = second
    return detail


def claims_view(attrs):
    """属性序列 → (已确认值槽列表, 未确认属性列表)。「一定時間」恒为已确认 p6。"""
    unconfirmed = [a for a in attrs if a in UNCONFIRMED_SLOTS]
    slots = []
    for attr in attrs:
        for field, _needle in CONFIRMED_SLOTS.get(attr, ()):
            slots.append((field, attr))
    slots.append(('/param6', '継続時間'))
    return slots, unconfirmed


# ---------------------------------------------------------------- 单行判定

def _param_view(record, name):
    return {'present': name in record,
            'raw_state': raw_state(record.get(name), name in record), 'raw': record.get(name)}


def _m_zero_consumed_detail(m_record):
    """M 侧「零消费」证据：Chain 配置原值 + 缺失值槽 + str0 指向。"""
    return {
        'record_id': m_record.get('skillid'),
        'ability': m_record.get('ability'),
        'param1': m_record.get('param1'),
        'param2': m_record.get('param2'),
        'str0': m_record.get('str0'),
        'present_forbidden_slots': [name for name in M_FORBIDDEN_SLOTS if name in m_record],
        'policy': ('M 的 param1/param2 为 Chain 发动侧配置（b7 口径），本批零消费、不出值、'
                   '不建任何 skilllist|3005| 规则键；值只取 sub1 子记录'),
    }


def evaluate(data, cid, row, rows=None, skill=None, tab=None):
    """单行判定（不写入）。``rows`` 为同卡页面全部行（D6 句面唯一性）。"""
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
    value_slots, unconfirmed = claims_view(attrs)
    out['claims'] = list(attrs)
    out['unconfirmed'] = list(unconfirmed)
    # 句面主张クリティカル系 ⇒ 本批不承载该槽（同族 b7 的 23 行就是这一形态，已由批 7 结算）；
    # 整行拒绝而不是只答攻撃力/时长，避免「主张无答案」被悄悄留下。句面级判定，先于槽位门。
    crit_claimed = [a for a in attrs if a in CRIT_ATTRS]
    if crit_claimed:
        out['rejection'] = 'CRIT_ATTRIBUTE_NOT_IN_BATCH'
        out['rejection_detail'] = {'crit_attrs': crit_claimed,
                                   'policy': ('本批只携带 攻撃力／一定時間；句面含クリティカル系'
                                              '属性时整行不处理（同族 b7 行形态）')}
        return out
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
    # D3 父链：M 唯一、下标一致、ability 3005、sub 恰 = [M + 1]
    hits = tab['skills'].get(parent_id) or []
    if len(hits) != 1:
        out['rejection'] = 'M_NOT_UNIQUE(%d)' % len(hits)
        return out
    m_index, m_record = hits[0]
    subs = list(m_record.get('sub') or ())
    out['gates']['m_record'] = {'skillid': parent_id, 'index': m_index,
                                'pointer_index': index,
                                'index_matches_pointer': m_index == index,
                                'ability': m_record.get('ability'), 'sub': subs,
                                'name': m_record.get('name')}
    if m_index != index:
        out['rejection'] = 'PARENT_POINTER_MISMATCH'
        out['rejection_detail'] = {'pointer_index': index, 'm_index': m_index}
        return out
    if m_record.get('ability') != M_ABILITY:
        out['rejection'] = 'M_ABILITY_NOT_3005'
        out['rejection_detail'] = {'ability': m_record.get('ability')}
        return out
    if len(subs) != 1 or subs[0] != parent_id + 1:
        out['rejection'] = 'M_SUB_SHAPE_BAD'
        out['rejection_detail'] = {'sub': subs, 'expect': [parent_id + 1]}
        return out
    sub_id = subs[0]
    # D4 子记录（值载体）
    sub_hits = tab['skills'].get(sub_id) or []
    if len(sub_hits) != 1:
        out['rejection'] = 'SUB_NOT_UNIQUE(%d)' % len(sub_hits)
        return out
    sub_index, sub_record = sub_hits[0]
    out['gates']['sub_record'] = {
        'skillid': sub_id, 'index': sub_index, 'ability': sub_record.get('ability'),
        'sub': list(sub_record.get('sub') or ()), 'name': sub_record.get('name'),
        'has_text': 'text' in sub_record,
        'text': sub_record.get('text') if 'text' in sub_record else None,
    }
    if sub_record.get('ability') != SUB_ABILITY:
        out['rejection'] = 'SUB_ABILITY_NOT_3000'
        out['rejection_detail'] = {'ability': sub_record.get('ability')}
        return out
    if sub_record.get('sub'):
        out['rejection'] = 'SUB_HAS_SUB'
        out['rejection_detail'] = {'sub': sub_record.get('sub')}
        return out
    parents = [rid_ for _i, rec_ in _iter_records(tab) for rid_ in (rec_.get('sub') or [])
               if rid_ == sub_id]
    out['gates']['sub_parent_refs'] = len(parents)
    if len(parents) != 1:
        out['rejection'] = 'SUB_PARENT_REF_COUNT(%d)' % len(parents)
        return out
    str0_refs = [rec_.get('skillid') for _i, rec_ in _iter_records(tab)
                 if str(rec_.get('str0')) == str(sub_id)]
    out['gates']['sub_str0_refs'] = str0_refs
    if str0_refs:
        out['rejection'] = 'SUB_STR0_REFERENCED'
        out['rejection_detail'] = {'str0_refs': str0_refs}
        return out
    if str(sub_id) in (tab.get('sympathy_values') or set()):
        out['rejection'] = 'SUB_IN_SYMPATHY_INDEX'
        return out
    if str(sub_id) in (tab.get('charainfo_tokens') or set()):
        out['rejection'] = 'SUB_IN_CHARAINFO'
        return out
    naming = _naming_check(m_record.get('name'), sub_record.get('name'))
    out['gates']['naming'] = naming
    if not naming['ok']:
        out['rejection'] = 'NAMING_MISMATCH'
        out['rejection_detail'] = naming
        return out
    # D5a 子记录槽位
    params = {}
    for name in ('param0', 'param1', 'param2', 'param6'):
        params[name] = _param_view(sub_record, name)
    out['gates']['params'] = params
    for name in ('param0', 'param1', 'param2', 'param6'):
        state = params[name]['raw_state']
        if state != 'FINITE':
            out['rejection'] = 'PARAM_%s_%s' % (name.upper(), state)
            out['rejection_detail'] = {'slot': name, 'state': state,
                                       'raw': params[name]['raw']}
            return out
    p0 = float(params['param0']['raw'])
    if p0 != int(p0):
        out['rejection'] = 'PARAM0_NOT_INTEGRAL'
        return out
    first = int(p0)
    if first > PARAM0_SELF_INCLUSIVE:
        out['rejection'] = 'PARAM0_OUT_OF_DOMAIN'
        out['rejection_detail'] = {'param0': sub_record.get('param0'),
                                   'documented_max': PARAM0_SELF_INCLUSIVE}
        return out
    if first != PARAM0_SELF_INCLUSIVE:
        out['rejection'] = 'PARAM0_NOT_SELF_INCLUSIVE'
        out['rejection_detail'] = {'param0': sub_record.get('param0'),
                                   'sentence': '自身を含む<味方>'}
        return out
    p1 = float(params['param1']['raw'])
    p2 = float(params['param2']['raw'])
    if not (0 < p1 <= INCREMENT_MAX and 0 < p2 <= INCREMENT_MAX):
        out['rejection'] = 'PARAM12_NOT_INCREMENT_RANGE'
        out['rejection_detail'] = {'param1': p1, 'param2': p2,
                                   'domain': [0, INCREMENT_MAX]}
        return out
    # D5b 句面 ↔ 未确认槽 1:1（含 p3/p4/p5 双向、p7/p8 必须缺省）
    slot_values = {}
    for attr, field in UNCONFIRMED_SLOTS.items():
        name = field.lstrip('/')
        value = _slot_value(sub_record, name)
        if value is None:
            out['rejection'] = 'SLOT_NOT_NUMERIC'
            out['rejection_detail'] = {'slot': name, 'raw': sub_record.get(name)}
            return out
        slot_values[name] = value
        if attr in attrs and value == 0:
            out['rejection'] = 'CLAIM_WITHOUT_SLOT'
            out['rejection_detail'] = {'attr': attr, 'slot': name,
                                       'raw': sub_record.get(name)}
            return out
        if attr not in attrs and value != 0:
            out['rejection'] = 'SLOT_WITHOUT_CLAIM'
            out['rejection_detail'] = {'attr': attr, 'slot': name,
                                       'raw': sub_record.get(name)}
            return out
    for name in UNCLAIMED_ABSENT_SLOTS:
        if name in sub_record and sub_record.get(name) is not None:
            out['rejection'] = 'UNCLAIMED_SLOT_PRESENT'
            out['rejection_detail'] = {'slot': name, 'raw': sub_record.get(name),
                                       'sentence_claims_crit': False}
            return out
    # D5c 辅助筛位／机制标记
    for name in AUX_SLOTS:
        value, state = _int_or_zero(sub_record, name)
        if state in ('invalid', 'non_integral') or value:
            out['rejection'] = 'AUX_SLOT_NONZERO'
            out['rejection_detail'] = {'slot': name, 'raw': sub_record.get(name),
                                       'state': state}
            return out
    flag, flag_state = _int_or_zero(sub_record, 'flag')
    if flag_state in ('invalid', 'non_integral') or flag:
        out['rejection'] = 'FLAG_UNSUPPORTED'
        out['rejection_detail'] = {'flag': sub_record.get('flag'), 'state': flag_state}
        return out
    heal_flag, heal_state = _int_or_zero(sub_record, HEAL_FLAG_SLOT)
    if heal_state in ('invalid', 'non_integral'):
        out['rejection'] = 'FLAG1_1_NOT_INTEGRAL'
        out['rejection_detail'] = {'slot': HEAL_FLAG_SLOT,
                                   'raw': sub_record.get(HEAL_FLAG_SLOT)}
        return out
    if bool(heal_flag) != ('回復' in attrs):
        out['rejection'] = 'FLAG1_1_CLAIM_MISMATCH'
        out['rejection_detail'] = {'slot': HEAL_FLAG_SLOT,
                                   'raw': sub_record.get(HEAL_FLAG_SLOT),
                                   'heal_claimed': '回復' in attrs}
        return out
    # D5d M 零消费：M 不得携带任何值槽；Chain 配置必须是整数 ≥1
    forbidden = [name for name in M_FORBIDDEN_SLOTS if name in m_record]
    out['gates']['m_chain_config'] = _m_zero_consumed_detail(m_record)
    if forbidden:
        out['rejection'] = 'M_CARRIER_PARAM_PRESENT'
        out['rejection_detail'] = {'slots': forbidden,
                                   'policy': '值不在 M 上；M 出现值槽即前提失效，拒绝'}
        return out
    for name in M_CHAIN_SLOTS:
        raw = m_record.get(name)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            out['rejection'] = 'M_PARAM_%s_NOT_NUMERIC' % name.upper()
            out['rejection_detail'] = {'slot': name, 'raw': raw}
            return out
        value = float(raw)
        if not math.isfinite(value) or value != int(value):
            out['rejection'] = 'M_PARAM_NOT_INTEGRAL'
            out['rejection_detail'] = {'slot': name, 'raw': raw}
            return out
        if value < 1:
            out['rejection'] = 'M_PARAM_NOT_CHAIN_CONFIG'
            out['rejection_detail'] = {'slot': name, 'raw': raw,
                                       'policy': 'M 侧应为整数 ≥1 的 Chain 配置；'
                                                 '一旦是 (0,1) 增量值即拒绝'}
            return out
    out['gates']['slot_values'] = {
        'param0': first, 'param1': p1, 'param2': p2,
        'param6': float(params['param6']['raw']),
        'unconfirmed': {k: slot_values[k] for k in
                        (f.lstrip('/') for f in UNCONFIRMED_SLOTS.values())},
        'heal_flag1_1': heal_flag,
    }
    # D6 段落与竞争句
    record_text = str(m_record.get('text') or '')
    body = str(row.get('japanese') or '')
    units = sentence_units(record_text)
    paras = paragraphs(record_text)
    comp = competition_view(record_text, body)
    out['gates']['segment'] = dict(comp, units=len(units), target_fragment_index=0,
                                   sub_text_consumed=False)
    if not units or body not in record_text:
        out['rejection'] = 'SENTENCE_NOT_IN_RECORD'
        return out
    if record_text.count(body) != 1:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_RECORD'
        out['rejection_detail'] = {'occurrences': record_text.count(body)}
        return out
    if units[0] != body:
        out['rejection'] = 'SENTENCE_NOT_FIRST_UNIT'
        out['rejection_detail'] = {'units': units[:2]}
        return out
    # 3005 主记录正文形状：句 0＝本行 buff 句；句 1＝サブパーティ 尾句；句 2..＝第 2 段
    # （Chain 必殺技描述）。这些单位**都不被本批消费**，只作形状守卫与披露。
    if len(units) < 3 or units[1] != TRAILING_CLAUSE:
        out['rejection'] = 'TRAILING_CLAUSE_POSITION'
        out['rejection_detail'] = {'units': units[1:3], 'expected': TRAILING_CLAUSE}
        return out
    chain_units = units[2:]
    if any(unit not in (paras[1] if len(paras) > 1 else '') for unit in chain_units) \
            or '【共鳴アビリティ】' not in (paras[1] if len(paras) > 1 else ''):
        out['rejection'] = 'CHAIN_PARAGRAPH_MISMATCH'
        out['rejection_detail'] = {'chain_units': [u[:40] for u in chain_units[:3]]}
        return out
    if comp['paragraphs'] != 2:
        out['rejection'] = 'PARAGRAPH_SHAPE_UNEXPECTED'
        out['rejection_detail'] = {'paragraphs': comp['paragraphs']}
        return out
    if not comp['paragraph0_has_battlefield'] or not comp['sentence_in_paragraph0']:
        out['rejection'] = 'COMPETITION_OBJECT_MARK_MISSING'
        out['rejection_detail'] = {'paragraph0_has_battlefield':
                                   comp['paragraph0_has_battlefield'],
                                   'sentence_in_paragraph0': comp['sentence_in_paragraph0']}
        return out
    if comp['paragraph1_has_battlefield']:
        out['rejection'] = 'COMPETITION_SECOND_PARAGRAPH_HAS_OBJECT_MARK'
        return out
    if comp['duration_phrase_total'] not in (1, 2):
        out['rejection'] = 'COMPETITION_DURATION_COUNT'
        out['rejection_detail'] = {'total': comp['duration_phrase_total']}
        return out
    second = comp['second']
    if comp['duration_phrase_total'] == 2:
        if not second or not second['in_paragraph1']:
            out['rejection'] = 'COMPETITION_SECOND_NOT_IN_PARAGRAPH1'
            out['rejection_detail'] = second
            return out
        if not (second['has_1stchain'] and second['has_self']):
            out['rejection'] = 'COMPETITION_TRIGGER_MARKS_MISSING'
            out['rejection_detail'] = second
            return out
        if second['has_battlefield']:
            out['rejection'] = 'COMPETITION_SECOND_HAS_BATTLEFIELD'
            out['rejection_detail'] = second
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
    if len(trailing_rows) != 1:
        out['rejection'] = 'TRAILING_ROW_MISSING'
        out['rejection_detail'] = {'trailing_rows': trailing_rows}
        return out
    # D7 规则语义（套在**子记录自己的字段**上；不建 3005 规则）
    import rules as R
    slots = []
    for field, attr in value_slots:
        name = field.lstrip('/')
        needle = next((n for a, pairs in CONFIRMED_SLOTS.items() for f, n in pairs
                       if f == field), None)
        answer = None
        try:
            answer = R.answer_for(TABLE, SUB_ABILITY, field, sub_record.get(name),
                                  sub_record, source_layer=LAYER)
        except Exception as exc:  # pragma: no cover - 规则导入失败即拒绝，不静默
            out['rejection'] = 'RULE_LOOKUP_ERROR'
            out['rejection_detail'] = {'slot': name, 'error': repr(exc)}
            return out
        if not answer:
            out['rejection'] = 'RULE_SLOT_UNCONFIRMED'
            out['rejection_detail'] = {'slot': name}
            return out
        meaning = str(answer.get('meaning_zh') or '')
        if not needle or needle not in meaning:
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
                      'evidence_scope': SCOPE, 'raw': sub_record.get(name), 'rule': answer})
    out['gates']['rule_slots'] = [
        {'slot': s['slot'], 'meaning_zh': s['rule'].get('meaning_zh'),
         'rule_key': '%s|%d|%s' % (TABLE, SUB_ABILITY, s['field']),
         'raw': s['raw'], 'evidence_scope': s['evidence_scope']} for s in slots]
    out['accepted'] = True
    out['record'] = {
        'skillid': parent_id, 'index': m_index, 'ability': m_record.get('ability'),
        'layer': LAYER, 'sub': subs, 'name': m_record.get('name'),
        'param1': m_record.get('param1'), 'param2': m_record.get('param2'),
        'str0': m_record.get('str0'),
        'sub_id': sub_id, 'sub_index': sub_index, 'sub_ability': sub_record.get('ability'),
        'sub_name': sub_record.get('name'),
        'sub_param0': sub_record.get('param0'), 'sub_param1': sub_record.get('param1'),
        'sub_param2': sub_record.get('param2'), 'sub_param6': sub_record.get('param6'),
        'sub_param3': sub_record.get('param3'), 'sub_param4': sub_record.get('param4'),
        'sub_param5': sub_record.get('param5'), 'sub_param7': sub_record.get('param7'),
        'sub_param8': sub_record.get('param8'), 'flag1_1': sub_record.get(HEAL_FLAG_SLOT),
        'flag': sub_record.get('flag'),
    }
    out['sentence'] = {'text': body, 'attrs': list(attrs), 'form': '+'.join(attrs),
                       'fragment_index': TARGET_FRAGMENT_INDEX,
                       'trailing_clause': TRAILING_CLAUSE,
                       'units': len(units),
                       'paragraphs': comp['paragraphs'],
                       'chain_units': len(chain_units)}
    out['competition'] = comp
    out['slots'] = slots
    return out


def _iter_records(tab):
    for pair_list in tab['skills'].values():
        for pair in pair_list:
            yield pair[0], pair[1]


def _naming_check(m_name, sub_name):
    """命名对应：``sub``／``sub1`` ＋（M 名去 ``■``），或命中 1 条已登记变体。"""
    m_text = str(m_name or '')
    s_text = str(sub_name or '')
    core = m_text[1:] if m_text.startswith('■') else m_text
    expected = ['sub' + core, 'sub1' + core]
    frozen = FROZEN_NAMING_VARIANTS.get((m_text, s_text))
    return {'ok': bool(core) and (s_text in expected or frozen is not None),
            'm_name': m_text, 'sub_name': s_text, 'expected': expected,
            'matched': ('exact' if s_text in expected else
                        ('frozen_variant' if frozen is not None else 'none')),
            'frozen_reason': frozen}


# ---------------------------------------------------------------- 答案对象

def _answer_key(field):
    return '%s|%d|%s' % (TABLE, SUB_ABILITY, field)


def _common_text(res, sub_record, m_record):
    """条件／对象／未知／竞争段／证据档／S3 的公共表述（数值全部来自记录与规则）。"""
    attrs = res['sentence']['attrs']
    unconfirmed = res['unconfirmed']
    if unconfirmed:
        unknown = ('句面另含无规则属性：%s —— skilllist|3000 没有 p3/p4/p5/p7 规则，'
                   '本批不出值、不按相关性猜槽位' % '、'.join(unconfirmed))
        if '防御力' in unconfirmed:
            unknown += ('（p4 原值 %s 为负，与「上がる」方向矛盾，仍未知、不消费）'
                        % num_text(sub_record.get('param4')))
        if '回復' in unconfirmed:
            unknown += ('；「HPが上限を超えて回復する」对应的回復量（p5）无规则，本批不出值'
                        '（flag1_1 只作机制披露）')
    else:
        unknown = ('句面未点名防御力／移動速度／クリティカル系／回復，本批不为这些槽出值')
    cond = ('原文条件：「%s」；触发子句「【共鳴アビリティ】自身を含む<味方>が'
            '≪共鳴必殺≫を発動するたび」逐字保留，对象为句面「戦場にいる<味方>」；'
            '子记录 param0=%s 只控制候选接受者是否含提供者自身，iParam0/param9 属发动者筛选'
            '（本记录未设置），两者不得混写'
            % (res['sentence']['text'], sub_record.get('param0')))
    carrier = ('载体=M→sub1 数据侧结构对应：行记录 M=%s（ability 3005）的 sub 恰为子记录 %s'
               '（ability 3000），数值取自**子记录自身字段**；M 的 param1=%s/param2=%s 为 '
               'Chain 发动侧配置，本批零消费、不出值，也不建任何 skilllist|3005| 规则键；'
               '3005 主记录的处理器入口未被既有原生证据覆盖（dispatch.txt:10 为 cmp w0,#0xbb8 '
               '即 3000），因此这是结构对应、不是已核实的装载路径'
               % (res['record']['skillid'], res['record']['sub_id'],
                  num_text(m_record.get('param1')), num_text(m_record.get('param2'))))
    semantics = ('口径：攻撃力只落成 /param1（普通攻击加算增量，写 _attackNormal）与'
                 '/param2（技能攻击加算增量，写 _attackSkill）两条，以 1 为基准汇总，'
                 '不是把攻击面板按倍率放大；一定時間只落成 /param6 正时长（游戏秒），'
                 '缺时间不推定永久')
    comp = res.get('competition') or {}
    second = comp.get('second')
    if second:
        comp_text = ('竞争段披露：正文按字面换行恰 2 段，第 1 段含「戦場にいる」、第 2 段不含；'
                     '第 2 段另有 1 处「%s」（形态＝%s，主语「自身」、含「1stChain以上」），'
                     '本批按**句面对象标记**判为另一对象，未消费、不出值——这是句面判据，'
                     '不是引擎装载核实' % (DURATION_PHRASE, second['shape']))
    else:
        comp_text = ('竞争段披露：正文按字面换行恰 2 段，第 1 段含「戦場にいる」、第 2 段不含，'
                     '且正文仅 1 处「%s」，第 2 段无同名 buff 短语' % DURATION_PHRASE)
    s3 = ('账本 S3：触发子句仍为未覆盖子句，split 标记保留、行状态仍「拆分待核查」，'
          'b7 hint 保留，不宣称整行完整；p2 与 p1 同属一条「攻撃力」主张，账本按 S4 记'
          '「答案未对应到新效果」（与 10215 先例同形）')
    grade = ('证据档：规则体状态为「已确认（静态及受控原生局部规则）」，但本批未做逐记录执行'
             '确认、且 M→sub1 的引擎装载未核实，故原值与关联证据档均为「推断」')
    limits = ('不写最终面板／最终伤害／最终HP／叠加上限／Chain 影响／实际装载／账号解锁；'
              '未做实机验证')
    return '；'.join((cond, carrier, semantics, unknown, comp_text, s3, grade, limits))


def _slot_value_text(name, raw, rule):
    """值文本：复用规则的 ``value_text``（已含换算），再补本槽口径守卫（不重写公式）。"""
    head = str(rule.get('value_text') or '').rstrip('。')
    if name == 'param1':
        return ('%s；口径：这是 Support3 普通攻击的加算增量（本项贡献 +%s 个百分点），'
                '以 1 为基准与其他项汇总，不是把攻击面板按倍率放大'
                % (head, num_text(round(float(raw) * 100.0, 6))))
    if name == 'param2':
        return ('%s；口径：这是 Support3 技能攻击的加算增量（本项贡献 +%s 个百分点），'
                '以 1 为基准与其他项汇总，不是把攻击面板按倍率放大'
                % (head, num_text(round(float(raw) * 100.0, 6))))
    return ('%s；口径：正时长原样传入共用时间存储，按游戏 fixedDeltaTime 累计扣减，'
            '不是现实墙钟秒、也不是永久；不乘 Chain' % head)


def _slot_note(ctx, sub_record, m_record, slot):
    """逐槽 note：载体、M 零消费、映射、方向、对象、触发、样本域、未知、证据档。"""
    name, attr, raw = slot['slot'], slot['attr'], slot['raw']
    rule = slot['rule']
    if name == 'param1':
        mapping = ('句中「攻撃力」→ 子记录 /param1（攻撃力＝param1+param2 两条值行；'
                   '本条为普通攻击侧）')
        direction = ('方向审核：原值 %s>0，普通攻击加算贡献与「上がる」句向一致'
                     % num_text(raw))
    elif name == 'param2':
        mapping = ('句中「攻撃力」→ 子记录 /param2（攻撃力＝param1+param2 两条值行；'
                   '本条为技能攻击侧；同一「攻撃力」主张的第二值行，账本记 S4）')
        direction = ('方向审核：原值 %s>0，技能攻击加算贡献与「上がる」句向一致'
                     % num_text(raw))
    else:
        mapping = '句中「一定時間」→ 子记录 /param6 1:1（正时长，游戏秒）'
        direction = ('方向审核：原值 %s>0 为正时长；缺时间不推定永久，也不据相关性猜单位'
                     % num_text(raw))
    unconfirmed = ctx['unconfirmed']
    unknown = ('句面未确认属性：%s（p3/p4/p5 无规则，本批不出值）'
               % '、'.join(unconfirmed) if unconfirmed else
               '句面未点名防御力/移動速度/回復')
    heal_flag = sub_record.get(HEAL_FLAG_SLOT)
    heal = ('；句面「HPが上限を超えて回復する」对应 flag1_1=%s 只作机制披露，'
            '回復量（p5）无规则、不出值' % heal_flag) if heal_flag else ''
    return ('；'.join((
        'C12-P2 候选值行（来源载体＝M 的相邻 sub1 子记录 skilllist|%d|CACHE；'
        'M=%d 自身 param 零消费、不建 3005 规则）'
        % (ctx['record_id'], ctx['m_record_id']),
        mapping,
        '规则键 %s；原值 %s' % ('%s|%d|%s' % (TABLE, SUB_ABILITY, slot['field']),
                               num_text(raw)),
        direction,
        '对象披露（双源）：句面依据「戦場にいる<味方>の」逐字在句；记录侧＝子记录 param0=%s '
        '控制候选支持接受者（1→遍历候选、含提供者自身；缺→持有者自身），'
        'iParam0/param9 筛选发动者（职业位图/所属），本记录均未设置，不得混写'
        % num_text(sub_record.get('param0')),
        '触发条件逐字：「【共鳴アビリティ】自身を含む<味方>が≪共鳴必殺≫を発動するたび」',
        '样本域：%s' % (rule.get('conditions') or ''),
        unknown + heal,
        'M→sub1 归属：数据侧结构对应（M.sub 恰 1 个且＝M+1；子记录 ability 3000、全表唯一、'
        '父引用恰 1、无 str0/charainfo/sympathy 引用、命名对应）；引擎侧装载未核实'
        '（dispatch.txt:10 cmp w0,#0xbb8）',
        '证据档：规则体已确认，但本行未做逐记录执行确认，原值/关联均记「推断」（scope=%s）'
        % SCOPE,
        'S3 与 b7 hint 保留：触发子句与第 2 段自身侧 buff 不被本批答案覆盖，行仍「拆分待核查」，'
        '不宣称完整',
    )) + '。')


def build_answers(data, cid, row, res, tab=None):
    """构造 3 条答案对象（复用 ``rules.answer_for`` 的换算与证据字段，不重写公式）。

    **载体一律是子记录**：``answer['record_id']`` 与 ``answer['source']['record_id']`` 都是
    ``sub_id``，不是 M。M 的原值只进 ``binding`` 的披露字段。
    """
    if not res.get('accepted'):
        return []
    tab = tab or tables(data)
    sub_id = res['record']['sub_id']
    m_id = res['record']['skillid']
    sub_index = res['record']['sub_index']
    m_index = res['record']['index']
    sub_record = tab['skills'][sub_id][0][1]
    m_record = tab['skills'][m_id][0][1]
    common = _common_text(res, sub_record, m_record)
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
            'record_id': sub_id,
            'layer': LAYER,
            'effect_attribute': attr,
            'source': {
                'source_key': SOURCE_KEY,
                'json_pointer': '/skilllist/%d' % sub_index,
                'layer': LAYER,
                'record_key': '%s#%s' % (SOURCE_KEY, '/skilllist/%d' % sub_index),
                'table': TABLE,
                'record_id': sub_id,
                'field_path': field,
                'field': field,
                'field_json_pointer': '/skilllist/%d%s' % (sub_index, field),
            },
            'numeric_source': '规则（%s，本批按子记录取值）' % _answer_key(field),
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
            'note': _slot_note({'record_id': sub_id, 'm_record_id': m_id,
                               'unconfirmed': list(res['unconfirmed'])},
                              sub_record, m_record, slot),
            'binding': {MARKER_KEY: {
                'scope': SCOPE,
                'structure_scope': STRUCTURE_SCOPE,
                'module': MODULE_VERSION,
                'candidate_only': True,
                'cid': cid,
                'row_id': row_id,
                'reference_field': REF_TEMPLATE % cid,
                'rule_key': _answer_key(field),
                'rule_table': TABLE,
                'rule_ability': SUB_ABILITY,
                'carrier': 'M_SUB1（行记录 M 的相邻子记录；非行记录自身）',
                'm_record_id': m_id,
                'm_record_index': m_index,
                'm_ability': M_ABILITY,
                'm_chain_config': {'param1': m_record.get('param1'),
                                   'param2': m_record.get('param2'),
                                   'consumed': False},
                'record_id': sub_id,
                'record_index': sub_index,
                'record_ability': res['record']['sub_ability'],
                'layer': LAYER,
                'field_path': field,
                'slot': name,
                'effect_attribute': attr,
                'raw_value': raw,
                'sentence_form': res['sentence']['form'],
                'sentence_attrs': list(res['sentence']['attrs']),
                'fragment_index': TARGET_FRAGMENT_INDEX,
                'trailing_clause_not_consumed': True,
                'sub_text_not_consumed': True,
                'sub_records_not_consumed': list(m_record.get('sub') or []),
                'unconfirmed_attrs': list(res['unconfirmed']),
                'unconfirmed_slots_not_consumed': [UNCONFIRMED_SLOTS[a]
                                                   for a in res['unconfirmed']],
                'condition': {'param0': sub_record.get('param0'),
                              'param0_self_inclusive': True,
                              'iParam0': sub_record.get('iParam0'),
                              'param9': sub_record.get('param9')},
                'competition': None if not res.get('competition', {}).get('second') else {
                    'shape': res['competition']['second']['shape'],
                    'consumed': False,
                    'judgement': '句面对象标记（第 2 段不含「戦場にいる」、主语「自身」）',
                    'engine_load_confirmed': False,
                },
                'split_flag_policy': 'S3_KEPT（触发子句未被本批覆盖，不清 split 标记）',
                'b7_hint_kept': True,
                'numeric_evidence': '推断',
                'association': '推断（数据侧结构对应，引擎装载未核实）',
                'disclosure': {
                    'carrier': 'M_SUB1（不借行记录自身、不跨卡）',
                    'm_params': 'NOT_CONSUMED（Chain 配置；不建 3005 规则）',
                    'unconfirmed_attributes': (
                        'NOT_CONSUMED（p3/p4/p5 无规则；p4 负值不猜）'
                        if res['unconfirmed'] else 'NONE_CLAIMED'),
                    'competition_paragraph': ('NOT_CONSUMED（句面对象标记判据，非引擎核实）'
                                              if res.get('competition', {}).get('second')
                                              else 'NONE_PRESENT'),
                    's3': 'S3_KEPT（行仍「拆分待核查」）',
                    'b7_hint': 'KEPT（inference_b7_hint 未删、G4 文本保留）',
                    'evidence_grade': '推断（规则体已确认；逐记录未核实；M→sub1 仅数据侧）',
                    'rights': '不写最终伤害/HP/面板/叠加上限/Chain/账号解锁；未做实机',
                },
            }},
        })
    return answers


# ---------------------------------------------------------------- 页面消费（候选）

def _existing_same(row, answers):
    """已有同键答案：全部同记录（sub）/同字段/同原值/同层 → SAME；否则 CONFLICT。"""
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
                                                           for a in answers],
                                            'record_id': res['record']['sub_id']})
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
    competition = res.get('competition') or {}
    second = competition.get('second')
    row[MARKER_KEY] = {
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'module': MODULE_VERSION,
        'candidate_only': True,
        'state': state,
        'cid': cid,
        'row_id': row.get('row_id'),
        'reference_field': REF_TEMPLATE % cid,
        'm_record_id': record['skillid'],
        'm_record_index': record['index'],
        'm_ability': record['ability'],
        'm_chain_config': {'param1': record.get('param1'), 'param2': record.get('param2'),
                           'consumed': False},
        'record_id': record['sub_id'],
        'record_index': record['sub_index'],
        'record_ability': record['sub_ability'],
        'layer': LAYER,
        'carrier': 'M_SUB1',
        'naming': res['gates'].get('naming'),
        'sentence_form': res['sentence']['form'],
        'sentence_attrs': list(res['sentence']['attrs']),
        'fragment_index': TARGET_FRAGMENT_INDEX,
        'trailing_clause_not_consumed': True,
        'sub_text_not_consumed': True,
        'sub_records_not_consumed': list(record.get('sub') or []),
        'unconfirmed_attrs': list(res['unconfirmed']),
        'unconfirmed_slots_not_consumed': [UNCONFIRMED_SLOTS[a] for a in res['unconfirmed']],
        'condition': {'param0': record.get('sub_param0'), 'self_inclusive': True},
        'competition': {'paragraphs': competition.get('paragraphs'),
                        'duration_phrase_total': competition.get('duration_phrase_total'),
                        'second': None if not second else {
                            'shape': second['shape'],
                            'quote': second['quote'],
                            'consumed': False,
                            'judgement': '句面对象标记（第 2 段不含「戦場にいる」、主语「自身」）',
                            'engine_load_confirmed': False}},
        'split_flag_policy': 'S3_KEPT',
        'b7_hint_kept': True,
        'binding_conditions_written': False,
        'rule_keys': [('%s|%d|%s' % (TABLE, SUB_ABILITY, s['field'])) for s in res['slots']],
        'numeric_evidence': '推断',
        'association': '推断（数据侧结构对应，引擎装载未核实）',
        'unknowns': ['防御力（p4 负值，方向与「上がる」矛盾）', '移動速度（p3）', '回復（p5）',
                     '第 2 段自身侧一定会時間句（不消费）', '叠加上限', 'Chain 影响',
                     'M→sub1 引擎装载路径', '实机'],
    }
