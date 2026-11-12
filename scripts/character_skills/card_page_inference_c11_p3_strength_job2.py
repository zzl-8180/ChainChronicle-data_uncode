# -*- coding: utf-8 -*-
"""C11-P3 ``skilllist|1017|``（StrengthJob2）**第二段** サブパーティ条件句：候选实现。

任务卡 ``docs/tasks/20261031-c11-p3-strength-job2.md``；选题预检
``output/character_skills/c11_p3_selection_20261031/selection_report.md``；周期计划
``docs/tasks/20261031-c11-c13-three-cycle-plan.md``。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；正式页面、
``rules.json``、``effect_ledger`` 均未改动；正式全库生成与全库检查不在本阶段。账本所需
**0 条新映射**——``scripts/character_skills/effect_ledger.py:467-468`` 已有 1017 的
``/param1``→攻撃力、``/param2``→移動速度、``/param3``→防御力 三条键精确映射，本批直接复用。

句子与范围
----------
只处理记录正文**第二段**（``\\n`` 分隔后的 0 基下标 1）里的那一句，两种逐字形态：

    またサブパーティにいると、メインパーティの攻撃力と防御力と移動速度が上がる。
    サブパーティにいると、メインパーティの攻撃力と防御力と移動速度が上がる。

（30229 无句首「また」，其余 12 行有。）**首段**「戦場にいる味方の攻撃力と防御力と移動速度が
上がる。」已由既有 1017 试点出过 3 条答案，本批零触碰；**同段竞争子句**「<所属>の場合、
効果が上がり、さらにクリティカル発生率とクリティカル威力が上がる」不归本句，也不被本批
消费（句面不匹配即拒绝）。

0 新公式、0 新规则键、0 新原生、0 新账本映射
--------------------------------------------
三条换算全部复用 ``profiles/rules.json`` 已确认的 ``skilllist|1017|/param1../param3``；
本模块通过 ``rules.answer_for('skilllist', 1017, '/paramN', raw, record, source_layer='CACHE')``
取 ``conversion/unit/quantity_kind/conditions/rule_status/rule_limits/value_text/answer_status``，
**不在本批重写公式**，也不写 ``_RULE_KEY_EFFECT``。

S3 条件子句**保留**（不升级为原生确认）
---------------------------------------
「サブパーティにいる」「メインパーティ」的放置／前后备判定**未被规则编码**。规则只确认
「接受者职业位命中 + 提供者自身开关」。因此本模块：

* **不写** ``row['binding_conditions']``（不清 S3），不写任何清除 split 标记的字段；
* 答案与行注记显式声明条件未确认、账本行仍「拆分待核查」、不宣称整行完整；
* 不把句面条件改写成「已确认仅对主队生效」，也不写最终伤害/HP/面板/叠加上限/Chain 影响。

准入是**结构规则**，不是 row_id / 记录 / 原值白名单
---------------------------------------------------
模块内没有任何 row_id、卡号、记录号或「原值 == 字面量」常量（``candidate/run_checks.py``
的静态扫描用例断言这一点）。判定顺序：

    D1 行身份：``group == 'ability'``、``reference_field == 'skillid[2]'``、
       ``fragment_index >= 1``（首段行不处理），且日语逐字等于两种形态之一。
    D2 同层来源：``layer == 'CACHE'``、``source_key == CACHE/skilllist.data5.json.raw``、
       ``field == '/text'``、``json_pointer`` 匹配 ``/skilllist/<n>``；不读 APK 表。
    D3 父链一致：``charainfo[cid].skillid[2]`` → 该下标记录 ``skillid`` 全表唯一命中，
       下标就是 D2 的 ``<n>``；记录 ``ability`` ＝ 1017；页面载体表/层/记录一致。
    D4 槽位：``param1/param2/param3`` 必须有限正数（缺失/null/非数值/非有限/真零/负值
       逐档独立拒绝，不补 0）；``param0`` 必须整型且落在规则文档域 0..1（不入值行）；
       ``param4/param5`` 非零拒绝（句面无暴击主张，1017 亦无 p4/p5 规则）；
       ``param6..param9``、``flag1_0``、``iParam1`` 非零拒绝；``flag`` 非零拒绝；
       ``iParam0`` 必须非零、位图解码全部落在 ``filter_dictionary`` 的 job enum 内，
       且**不含 ALMIGHTY(bit5)**——`31` 只含 JobType 0..4，不写成「全职业」。
    D5 段落与唯一性：句子在记录正文恰出现 1 次、所在段为第二段（下标 1）、不在首段；
       同卡 ``reference_field`` 内恰 1 行匹配本句式（不抢子句、不只处理半句）。
    D6 规则语义：三条槽的 ``answer_for`` 必须返回非空，``meaning_zh`` 含对应属性关键词
       （攻击倍率／移动速度乘数／受伤量倍率）。规则语义漂移即拒绝。
    D7 幂等：本行已有同 ``rule_key`` 答案——同记录同字段同原值同层 → ``ALREADY_PRESENT_SAME``
       （零写入）；其余 → ``ALREADY_ANSWERED``（只写披露 marker，不改写既有答案）。

**批次边界由调用方显式声明**：``apply_to_groups(data, cid, groups, scope_cids=...)``，缺省
``None`` → 一行都不处理（``NO_SCOPE_DECLARED``），避免将来接线时按结构规则无声扩面。
保护卡 30236／30239 在模块内硬拒绝（30239 同族但豁免不扩大）。

证据分档（不得升格）
--------------------
* 原值与规则：``numeric_evidence = 确认``（rules.json 已确认静态换算＋受控原生片段）。
* 「本行句面 → 本记录三槽」：``association_evidence = 推断``（句面不写数值；归属由句面属性
  顺序＋记录唯一＋职业位筛选给出，未做实机）。``answer_status`` 沿用规则／页面既有口径
  ``CONFIRMED_NUMERIC``（数值确认、关联推断），不新增状态词。
* ``param2`` 证据面窄（已核 ID 仅 2 个）：``evidence_scope = BY_TYPE_EXTRAPOLATED``，
  逐行在答案文本里保留同类型外推注记；``param1/param3`` 为 ``BY_TYPE_CONFIRMED``。
* 防御口径：p3=0.85 是**受伤量倍率**（减伤 15%），不是固定防御量、不是「防御 −15%」。

接口
----
``evaluate(data, cid, row, rows=None, skill=None, tab=None)``  单行判定（不写入）。
``build_answers(data, cid, row, res, tab=None)``                 三条答案对象（复用 rules）。
``apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None)`` 正式页消费（候选未接线）。
``tables(data)`` / ``clone_tables(tab)``                         CACHE 主表只读索引（可注入，反例用）。
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path

MODULE_VERSION = 'c11_p3_strength_job2_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 本批证据 scope（写进答案 binding，供账本/页面按 scope 精确消费时对账）。
SCOPE = 'C11_P3_STRENGTH_JOB2_20261031'
#: 结构判定自身 scope（行级 marker）。
STRUCTURE_SCOPE = 'C11_P3_STRENGTH_JOB2_CHAIN_20261031'
#: 行级 marker 键（每行至多一个本批键，不覆盖其他批的 marker）。
MARKER_KEY = 'inference_c11_p3_strength_job2'

#: 本族载体：skilllist 的 ability 1017（元数据 StrengthJob2）。
TABLE = 'skilllist'
ABILITY = 1017
REF_FIELD = 'skillid[2]'
TEXT_FIELD = '/text'
SOURCE_KEY = 'CACHE/skilllist.data5.json.raw'
#: CACHE 解码主表目录（与预检、C11-P1/P2 同源快照）。
BASE = 'output/cache_full_20261015_v3/decoded'
FILTER_DICT = 'output/character_skills/skilllist_types/filter_dictionary.json'

#: 保护卡：30236（G0）／30239（豁免不扩大）零触碰。
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

#: 记录正文用**字面**反斜线＋n 分段（不是控制字符）；此常量避免源码里写转义序列。
_TEXT_SEP = chr(92) + 'n'
#: 本批句面所在段（0 基）：第二段。首段（下标 0）由既有答案承载，本批零触碰。
TARGET_SEGMENT_INDEX = 1
#: 两种逐字形态（12 行带「また」，30229 无）。
SENTENCE_FORMS = (
    'またサブパーティにいると、メインパーティの攻撃力と防御力と移動速度が上がる。',
    'サブパーティにいると、メインパーティの攻撃力と防御力と移動速度が上がる。',
)
#: 首段句（只为 disclosure / 反例锚点使用，不参与判定）。
FIRST_SEGMENT_SENTENCE = '戦場にいる味方の攻撃力と防御力と移動速度が上がる。'
#: 同段竞争子句的固定片段（只作披露与反例锚点，不被本批消费）。
COMPETING_CLAUSE_MARK = 'クリティカル発生率とクリティカル威力が上がる'

#: 值槽 → (字段, 句面属性, 规则 meaning_zh 关键词, 证据 scope)。
#: 关键词是 D6 语义守卫：规则文本一变即拒绝，不静默沿用本表。
VALUE_SLOTS = (
    ('param1', '/param1', '攻撃力', ('攻击倍率',), 'BY_TYPE_CONFIRMED'),
    ('param2', '/param2', '移動速度', ('移动速度乘数',), 'BY_TYPE_EXTRAPOLATED'),
    ('param3', '/param3', '防御力', ('受伤量倍率',), 'BY_TYPE_CONFIRMED'),
)
#: 必读数值槽（param0 只是自身参与开关，不产出值行）。
NUMERIC_SLOTS = ('param0', 'param1', 'param2', 'param3')
#: 句面未主张的槽：暴击两槽（1017 无规则）、周期回复、绝壁/受益侧筛选。
UNCLAIMED_SLOTS = ('param4', 'param5', 'param6', 'param7', 'param8', 'param9',
                   'flag1_0', 'iParam1')
#: param0 的规则文档域：截断后 0（排除提供者自身）／1（允许自身）。
PARAM0_MAX_DOMAIN = 1
#: ALMIGHTY 的 JobType 位：iParam0=31 不含它，故不写「全职业」。
ALMIGHTY_JOB_BIT = 5

#: 页面既有答案里本批上线前应被本批替换为「已解」的通用未知原因（逐字）。
_STALE_REASONS = (
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '旧关键词候选未作为答案；不能排除对象或效果错配',
)
RESIDUAL_NOTE = ('C11-P3：第二段 1017 记录 p1/p2/p3 按已确认换算给值、句面归属为推断；'
                 '放置条件（サブパーティ／メインパーティ）未被规则编码，账本 S3 条件子句保留'
                 '（行仍「拆分待核查」）；同段暴击子句不归本句；未做实机验证')
RESIDUAL_LABEL = '推断（C11-P3：1017 第二段 p1/p2/p3 槽位归属；放置条件未编码，S3 保留）'

_TABLES = {}


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


def pct_text(value, base=0.0):
    """把倍率/增量转成百分数文本：round 到 6 位后去尾零（符号由调用方文本给出）。"""
    return '%g' % round((float(value) - base) * 100.0, 6)


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


def _read(path):
    return json.loads(read_path(Path(path)).read_text(encoding='utf-8-sig'))


# ---------------------------------------------------------------- CACHE 主表

def tables(data):
    """CACHE 解码主表（按 root 缓存，只读）。``tab`` 可由调用方注入（反例用）。

    ``skills`` 保留**数组下标**（行来源 ``/skilllist/<n>`` 按下标解析）；``by_id`` 是按
    skillid 的索引视图，二者须指向同一条记录才放行。
    """
    root = Path(getattr(data, 'root', Path('.'))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = read_path(root / BASE, root=root)
        skilllist = _read(base / 'skilllist.data5.json.raw')['skilllist']
        skills = {}
        for index, record in enumerate(skilllist):
            if record.get('skillid') is not None:
                skills.setdefault(record['skillid'], []).append((index, record))
        chara_list = _read(base / 'charainfo.data5.json.raw')['charainfo']
        chara = {record['cid']: record for record in chara_list}
        fdict = _read(root / FILTER_DICT)
        _TABLES[key] = dict(skills=skills, chara=chara, chara_list=chara_list,
                            filter=fdict, root=root)
    return _TABLES[key]


def clone_tables(tab):
    """反例用：深拷贝只读索引（不改动全局缓存）。"""
    return {k: (copy.deepcopy(v) if k in ('skills', 'chara', 'chara_list', 'filter') else v)
            for k, v in tab.items()}


# ---------------------------------------------------------------- 句面

def parse_sentence(japanese):
    """逐字匹配本族两种形态；返回 ``(form, detail)``，不匹配返回 ``(None, detail)``。

    form ∈ {'with_mata','plain'}。缺字、换序、改成「下がる」、追加尾句、首段句、
    同段暴击子句一律不匹配（不走正则近似，避免半句被消费）。
    """
    text = str(japanese or '')
    if not text:
        return None, {'reason': 'ROW_TEXT_EMPTY'}
    for form, known in zip(('with_mata', 'plain'), SENTENCE_FORMS):
        if text == known:
            return form, {'reason': None, 'form': form, 'length': len(text)}
    detail = {'reason': 'SENTENCE_NOT_STRENGTH_JOB2', 'text': text,
              'is_first_segment_sentence': text == FIRST_SEGMENT_SENTENCE,
              'has_competing_crit_clause': COMPETING_CLAUSE_MARK in text}
    return None, detail


def segment_view(record_text, body):
    """记录正文分段视图：``(segments, hit_indices, in_first)``。

    分段按字面反斜线＋n 切（解码 JSON 的存储形式），不是控制字符。
    """
    segments = str(record_text or '').split(_TEXT_SEP)
    hits = [i for i, seg in enumerate(segments) if body and body in seg]
    return segments, hits, (0 in hits)


# ---------------------------------------------------------------- 职业位

def decode_jobs(record, fdict):
    """解码 ``iParam0`` 职业位图；返回 ``(bits, names, fails, detail)``。"""
    fails = []
    value, state = _int_or_zero(record, 'iParam0')
    detail = {'slot': 'iParam0', 'raw': record.get('iParam0'), 'state': state,
              'value': value}
    if value is None:
        return [], [], ['IPARAM0_NOT_INTEGRAL'], detail
    if not value:
        return [], [], ['IPARAM0_EMPTY'], detail
    enum = fdict['job']['enum']
    names_zh = fdict['job']['names_zh']
    by_bit = {bit: key for key, bit in enum.items()}
    bits = [bit for bit in range(32) if value >> bit & 1]
    names = []
    for bit in bits:
        key = by_bit.get(bit)
        if key is None or key not in names_zh:
            fails.append('IPARAM0_UNKNOWN_JOB_BIT')
            break
        names.append(names_zh[key])
    if ALMIGHTY_JOB_BIT in bits:
        fails.append('IPARAM0_CONTAINS_ALMIGHTY')
    detail.update(bits=bits, decoded=names)
    return bits, names, fails, detail


# ---------------------------------------------------------------- 单行判定

def _param_view(record, name):
    return {'present': name in record,
            'raw_state': raw_state(record.get(name), name in record), 'raw': record.get(name)}


def evaluate(data, cid, row, rows=None, skill=None, tab=None):
    """单行判定（不写入）。``rows`` 为同卡页面全部行（D5 句面唯一性）。"""
    rid = row.get('row_id')
    out = {'row_id': rid, 'cid': cid, 'module': MODULE_VERSION, 'accepted': False,
           'rejection': None, 'rejection_detail': None, 'gates': {}, 'slots': []}
    if cid in ZERO_TOUCH_CIDS:
        out['rejection'] = 'ZERO_TOUCH_CID'
        return out
    # D1 行身份
    if row.get('group') != 'ability':
        out['rejection'] = 'NOT_ABILITY_GROUP'
        return out
    if str(row.get('reference_field') or '') != REF_FIELD:
        out['rejection'] = 'NOT_SKILLID2_ROW'
        out['rejection_detail'] = {'reference_field': row.get('reference_field')}
        return out
    fragment = row.get('fragment_index')
    if not isinstance(fragment, int) or fragment < 1:
        out['rejection'] = 'FIRST_SEGMENT_ROW'
        out['rejection_detail'] = {'fragment_index': fragment}
        return out
    form, detail = parse_sentence(row.get('japanese'))
    out['gates']['clause'] = dict(detail)
    if form is None:
        out['rejection'] = detail.get('reason') or 'SENTENCE_NOT_STRENGTH_JOB2'
        return out
    # D2 同层来源
    src = row.get('source') or {}
    out['gates']['row_source'] = {k: src.get(k) for k in
                                  ('source_key', 'layer', 'field', 'json_pointer', 'record_key')}
    if src.get('layer') != 'CACHE' or src.get('source_key') != SOURCE_KEY:
        out['rejection'] = 'ROW_LAYER_NOT_CACHE'
        return out
    if str(src.get('field') or '') != TEXT_FIELD:
        out['rejection'] = 'ROW_FIELD_NOT_TEXT'
        return out
    pointer = str(src.get('json_pointer') or '')
    if not pointer.startswith('/skilllist/'):
        out['rejection'] = 'ROW_POINTER_NOT_SKILLLIST'
        return out
    tail = pointer[len('/skilllist/'):]
    if not tail.isdigit():
        out['rejection'] = 'ROW_POINTER_NOT_SKILLLIST'
        out['rejection_detail'] = {'json_pointer': pointer}
        return out
    index = int(tail)
    out['gates']['record_index'] = index
    tab = tab or tables(data)
    chara = tab['chara'].get(cid)
    if chara is None:
        out['rejection'] = 'CHARAINFO_RECORD_MISSING'
        return out
    skillids = chara.get('skillid') or []
    if len(skillids) < 3 or skillids[2] is None:
        out['rejection'] = 'CHARAINFO_POINTER_MISSING'
        return out
    parent_id = skillids[2]
    out['gates']['charainfo'] = {'cid': cid, 'pointer': 'charainfo.skillid[2]',
                                 'record_id': parent_id}
    if skill is not None:
        if skill.get('table') != TABLE or skill.get('layer') != 'CACHE':
            out['rejection'] = 'SKILL_CARRIER_NOT_CACHE_SKILLLIST'
            return out
        if skill.get('record_id') != parent_id:
            out['rejection'] = 'SKILL_RECORD_MISMATCH'
            out['rejection_detail'] = {'skill_record_id': skill.get('record_id'),
                                       'charainfo': parent_id}
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
                              'sub': list(record.get('sub') or ())}
    if rec_index != index:
        out['rejection'] = 'PARENT_POINTER_MISMATCH'
        out['rejection_detail'] = {'pointer_index': index, 'record_index': rec_index}
        return out
    if record.get('ability') != ABILITY:
        out['rejection'] = 'ABILITY_NOT_1017'
        out['rejection_detail'] = {'ability': record.get('ability')}
        return out
    # D4a 数值槽：逐档独立拒绝，不补 0
    params = {}
    for name in NUMERIC_SLOTS:
        view = _param_view(record, name)
        params[name] = view
        state = view['raw_state']
        if state != 'FINITE':
            out['rejection'] = 'PARAM_%s_%s' % (name.upper(), state)
            out['rejection_detail'] = {'slot': name, 'state': state, 'raw': view['raw']}
            return out
    out['gates']['params'] = params
    p0 = float(params['param0']['raw'])
    if p0 != int(p0):
        out['rejection'] = 'PARAM0_NOT_INTEGRAL'
        return out
    first = int(p0)
    if first > PARAM0_MAX_DOMAIN:
        out['rejection'] = 'PARAM0_OUT_OF_DOMAIN'
        out['rejection_detail'] = {'param0': record.get('param0'),
                                   'documented_max': PARAM0_MAX_DOMAIN}
        return out
    # D4b 方向守卫：句面「上がる」⇒ p1/p2 增幅、p3 减伤（受伤量 <1）。
    p1 = float(params['param1']['raw'])
    p2 = float(params['param2']['raw'])
    p3 = float(params['param3']['raw'])
    if not (p1 > 1 and p2 > 1):
        out['rejection'] = 'PARAM12_DIRECTION_CONTRADICTS_SENTENCE'
        return out
    if not (0 < p3 < 1):
        out['rejection'] = 'PARAM3_RANGE_CONTRADICTS_SENTENCE'
        return out
    # D4c 句面未主张的槽必须缺省/null/零（暴击两项、周期回复、筛选位、受益位）
    for name in UNCLAIMED_SLOTS:
        value, state = _int_or_zero(record, name)
        if state in ('invalid', 'non_integral') or value:
            out['rejection'] = 'UNCLAIMED_SLOT_NONZERO'
            out['rejection_detail'] = {'slot': name, 'raw': record.get(name), 'state': state}
            return out
    flag, flag_state = _int_or_zero(record, 'flag')
    if flag_state in ('invalid', 'non_integral') or flag:
        out['rejection'] = 'FLAG_UNSUPPORTED'
        out['rejection_detail'] = {'flag': record.get('flag'), 'state': flag_state}
        return out
    # D4d 职业位：非零、解码全部落在 enum、不含 ALMIGHTY
    bits, job_names, fails, jdetail = decode_jobs(record, tab['filter'])
    out['gates']['job_filter'] = jdetail
    if fails:
        out['rejection'] = fails[0]
        out['rejection_detail'] = jdetail
        return out
    # D5 段落与唯一性
    record_text = str(record.get('text') or '')
    body = str(row.get('japanese') or '')
    segments, seg_hits, in_first = segment_view(record_text, body)
    occurrences = record_text.count(body)
    out['gates']['segment'] = {
        'segments': len(segments),
        'nonempty_segments': len([s for s in segments if s.strip()]),
        'hit_segment_indices': seg_hits,
        'target_segment_index': TARGET_SEGMENT_INDEX,
        'occurrences_in_record': occurrences,
        'in_first_segment': in_first,
        'competing_clause_in_same_segment': (
            bool(seg_hits) and COMPETING_CLAUSE_MARK in segments[seg_hits[0]]),
        'sub_consumed': False,
    }
    if not seg_hits:
        out['rejection'] = 'SENTENCE_NOT_IN_RECORD'
        return out
    if in_first:
        out['rejection'] = 'SENTENCE_IN_FIRST_SEGMENT'
        return out
    if seg_hits != [TARGET_SEGMENT_INDEX]:
        out['rejection'] = 'SENTENCE_NOT_IN_SECOND_SEGMENT'
        out['rejection_detail'] = {'hit_segment_indices': seg_hits,
                                   'target': TARGET_SEGMENT_INDEX}
        return out
    if occurrences != 1:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_RECORD'
        out['rejection_detail'] = {'occurrences': occurrences}
        return out
    holders = [sid for sid in skillids
               if isinstance(sid, int) and sid in tab['skills']
               and body in (tab['skills'][sid][0][1].get('text') or '')]
    out['gates']['card_holders'] = holders
    if holders != [parent_id]:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_CARD'
        out['rejection_detail'] = {'holders': holders}
        return out
    siblings = []
    if isinstance(rows, dict):
        for other in rows.values():
            if str(other.get('reference_field') or '') != REF_FIELD:
                continue
            oform, _od = parse_sentence(other.get('japanese'))
            if oform is not None:
                siblings.append(other.get('row_id'))
    out['gates']['sentence_rows'] = siblings
    if len(siblings) != 1 or siblings[0] != rid:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_SCOPE'
        out['rejection_detail'] = {'siblings': siblings}
        return out
    # D6 规则语义（三槽 answer_for 非空 + meaning 关键词）
    import rules as R
    slots = []
    for name, field, attr, keywords, scope in VALUE_SLOTS:
        answer = None
        try:
            answer = R.answer_for(TABLE, ABILITY, field, record.get(name), record,
                                  source_layer='CACHE')
        except Exception as exc:  # pragma: no cover - 规则导入失败即拒绝，不静默
            out['rejection'] = 'RULE_LOOKUP_ERROR'
            out['rejection_detail'] = {'slot': name, 'error': repr(exc)}
            return out
        if not answer:
            out['rejection'] = 'RULE_SLOT_UNCONFIRMED'
            out['rejection_detail'] = {'slot': name}
            return out
        meaning = str(answer.get('meaning_zh') or '')
        if not all(word in meaning for word in keywords):
            out['rejection'] = 'RULE_SEMANTICS_CHANGED'
            out['rejection_detail'] = {'slot': name, 'meaning_zh': meaning,
                                       'expected_keywords': list(keywords)}
            return out
        slots.append({'slot': name, 'field': field, 'attr': attr,
                      'evidence_scope': scope, 'raw': record.get(name), 'rule': answer})
    out['gates']['rule_slots'] = [
        {'slot': s['slot'], 'meaning_zh': s['rule'].get('meaning_zh'),
         'rule_key': '%s|%d|%s' % (TABLE, ABILITY, s['field']),
         'raw': s['raw'], 'evidence_scope': s['evidence_scope']} for s in slots]
    out['accepted'] = True
    out['record'] = {'skillid': parent_id, 'index': rec_index,
                     'ability': record.get('ability'), 'layer': 'CACHE',
                     'sub': list(record.get('sub') or ()),
                     'param0': record.get('param0'), 'iParam0': record.get('iParam0'),
                     'flag': record.get('flag')}
    out['sentence'] = {'form': form, 'text': body,
                       'segment_index': seg_hits[0]}
    out['jobs'] = {'bits': bits, 'decoded': job_names}
    out['slots'] = slots
    return out


# ---------------------------------------------------------------- 答案对象

def _answer_key(field):
    return '%s|%d|%s' % (TABLE, ABILITY, field)


def _common_text(res, record):
    """条件／对象／段落／未知／S3 的公共表述（数值全部来自记录与规则，不硬编码）。"""
    job_names = '、'.join(res['jobs']['decoded'])
    bits = ','.join(str(b) for b in res['jobs']['bits'])
    p0 = record.get('param0')
    cond = ('原文条件：「%s」；「サブパーティにいる」「メインパーティ」的放置与前后备判定'
            '未被规则编码，本批未确认该条件，不得写成「已确认仅对主队生效」'
            % res['sentence']['text'])
    obj = ('对象＝接收该 1017 能力的队友：iParam0=%s → 职业位 %s（%s；不含 ALMIGHTY bit%d，'
           '不写成「全职业」），param0=%s 允许提供者自身；对象与关联仍为推断'
           % (record.get('iParam0'), bits, job_names, ALMIGHTY_JOB_BIT, p0))
    same = ('数值非新发现：同记录首段「%s」已用同一组 p1/p2/p3 出过 3 条答案，'
            '本批是第二段句面的归属' % FIRST_SEGMENT_SENTENCE)
    crit = ('同段竞争子句「<所属>の場合、効果が上がり、さらにクリティカル発生率と'
            'クリティカル威力が上がる」不归本句；1017 无 p4/p5 规则，暴击两项保持未知')
    s3 = ('账本 S3：本句「サブパーティにいると」条件子句仍为未覆盖子句，保留 split 标记，'
          '行状态仍「拆分待核查」，不宣称整行完整')
    limits = '不写最终伤害/最终HP/面板ATK/叠加上限/Chain 影响；未做实机验证'
    return '；'.join((cond, obj, same, crit, s3, limits))


def _slot_value_text(name, raw, rule):
    """值文本：复用规则的 ``value_text``（已含倍率与百分比），再补本槽的口径守卫。

    不在本批重写换算，也不重复数字：p3 只补「受伤量倍率≠固定防御量」的语义守卫，
    p1/p2 沿用规则文本（攻击因子乘算 / 移动因子乘算，+15% 为本项局部贡献）。
    """
    head = str(rule.get('value_text') or '').rstrip('。')
    if name == 'param3':
        reduction = '%g' % round((1.0 - float(raw)) * 100.0, 6)
        return ('%s；口径：这是受伤量倍率（减伤 %s%%），不是固定防御量，'
                '也不是「防御力 −%s%%」' % (head, reduction, reduction))
    if name == 'param2':
        return ('%s；口径：移动因子乘算（乘数，不是加算，也不写实际每击动作周期）' % head)
    return '%s；口径：攻击因子乘算（本项局部贡献，不等同面板 ATK）' % head


def _slot_note(name, rule):
    """逐槽证据面注记；param2 必须保留同类型外推披露（已核 ID 仅 2 个）。"""
    if name == 'param2':
        return ('param2 证据面窄：已核 ID 仅 %d 个（见 conditions：「%s」），'
                '属同类型外推（BY_TYPE_EXTRAPOLATED）'
                % (int(rule.get('occurrences') or 0), rule.get('conditions')))
    return None


def build_answers(data, cid, row, res, tab=None):
    """构造三条答案对象（复用 ``rules.answer_for`` 的换算与证据字段，不重写公式）。"""
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
        note = _slot_note(name, rule)
        if note:
            value = '%s。%s' % (value, note)
        answers.append({
            'value': value,
            'quantity_kind': rule.get('quantity_kind'),
            'unit': rule.get('unit'),
            'raw_value': raw,
            'field_path': field,
            'rule_key': _answer_key(field),
            'table': TABLE,
            'record_id': parent_id,
            'layer': 'CACHE',
            'effect_attribute': attr,
            'source': {
                'source_key': SOURCE_KEY,
                'json_pointer': pointer,
                'layer': 'CACHE',
                'record_key': '%s#%s' % (SOURCE_KEY, pointer),
                'table': TABLE,
                'record_id': parent_id,
                'field_path': field,
                'field': field,
                'field_json_pointer': '%s%s' % (pointer, field),
            },
            'numeric_source': '规则',
            'numeric_evidence': '确认',
            'association_evidence': '推断',
            'answer_status': rule.get('answer_status') or 'CONFIRMED_NUMERIC',
            'evidence_scope': slot['evidence_scope'],
            'quantitative': True,
            'conversion': rule.get('conversion'),
            'value_text': rule.get('value_text'),
            'conditions': rule.get('conditions'),
            'base_definition': rule.get('base_definition'),
            'rule_status': rule.get('rule_status'),
            'rule_limits': rule.get('rule_limits'),
            'evidence': list(rule.get('evidence') or ()),
            'context': row.get('japanese'),
            'binding': {MARKER_KEY: {
                'scope': SCOPE,
                'structure_scope': STRUCTURE_SCOPE,
                'module': MODULE_VERSION,
                'candidate_only': True,
                'cid': cid,
                'row_id': row_id,
                'reference_field': REF_FIELD,
                'rule_key': _answer_key(field),
                'table': TABLE,
                'record_id': parent_id,
                'layer': 'CACHE',
                'record_index': index,
                'field_path': field,
                'slot': name,
                'effect_attribute': attr,
                'raw_value': raw,
                'sentence_form': res['sentence']['form'],
                'segment_index': res['sentence']['segment_index'],
                'first_segment_not_consumed': True,
                'competing_crit_clause_not_attributed': True,
                'sub_records_not_consumed': list(record.get('sub') or ()),
                'job_filter': {'iParam0': record.get('iParam0'),
                               'bits': list(res['jobs']['bits']),
                               'decoded': list(res['jobs']['decoded']),
                               'almighty_excluded': True},
                'condition': {'param0': record.get('param0'),
                              'param0_self_switch': True,
                              'placement_condition': 'UNCODED（サブパーティ／メインパーティ 未被规则编码）'},
                'split_flag_policy': 'S3_KEPT（条件子句不被本批覆盖，不清 split 标记）',
                'association': '推断',
                'disclosure': {
                    'placement_condition': 'UNCONFIRMED（未编码；不得写成仅对主队生效）',
                    'same_record_first_segment_answers': '同记录首段 3 条已存在；本批为第二句归属',
                    'competing_crit_clause': 'NOT_ATTRIBUTED（1017 无 p4/p5）',
                    'defense_semantics': ('受伤量倍率（减伤），不是固定防御量、'
                                          '不是防御力 −百分数'),
                    'param2_scope': 'BY_TYPE_EXTRAPOLATED（已核 ID 仅 2 个）',
                    'rights': '不写最终伤害/HP/面板/叠加上限/Chain；未做实机',
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
              'marker_only': 0, 'out_of_domain_rows': 0, 'bindings_written': 0}
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
    rows_map = {r['row_id']: r for g in groups for s in g.get('skills') or []
                for r in s.get('rows') or []}
    for group in groups:
        if group.get('group') != 'ability':
            continue
        for skill in group.get('skills') or []:
            if str(skill.get('reference_field') or '') != REF_FIELD:
                continue
            for row in skill.get('rows') or []:
                fragment = row.get('fragment_index')
                if not isinstance(fragment, int) or fragment < 1:
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
                                            'attributes': [a['effect_attribute'] for a in answers]})
    return report


def _stamp_row(row, res, cid):
    """行级标注：证据档、scope、残余未知原因与本批 marker（不改 row_class／partial）。

    **不写** ``binding_conditions``：S3 条件子句保留，本批不清 split 标记。
    """
    row['evidence'] = '推断'
    row['evidence_scope'] = sorted({scope for _n, _f, _a, _k, scope in VALUE_SLOTS})
    row['evidence_label'] = RESIDUAL_LABEL
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    if RESIDUAL_NOTE not in reasons:
        reasons.append(RESIDUAL_NOTE)
    row['unknown_reasons'] = reasons
    _write_marker(row, res, cid, state='ANSWERS_ADDED')


def _write_marker(row, res, cid, state):
    row[MARKER_KEY] = {
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'module': MODULE_VERSION,
        'candidate_only': True,
        'state': state,
        'cid': cid,
        'row_id': row.get('row_id'),
        'record_id': res['record']['skillid'],
        'record_index': res['record']['index'],
        'ability': res['record']['ability'],
        'layer': 'CACHE',
        'sentence_form': res['sentence']['form'],
        'segment_index': res['sentence']['segment_index'],
        'first_segment_not_consumed': True,
        'competing_crit_clause_not_attributed': True,
        'sub_records_not_consumed': res['record'].get('sub'),
        'job_filter': {'iParam0': res['record'].get('iParam0'),
                       'bits': list(res['jobs']['bits']),
                       'decoded': list(res['jobs']['decoded']),
                       'almighty_excluded': True},
        'condition': {'param0': res['record'].get('param0'),
                      'placement_condition': 'UNCODED'},
        'split_flag_policy': 'S3_KEPT',
        'binding_conditions_written': False,
        'rule_keys': [('skilllist|%d|%s' % (ABILITY, slot[1])) for slot in VALUE_SLOTS],
        'association': '推断',
        'unknowns': ['放置条件（サブパーティ／メインパーティ）未编码',
                     '同段暴击两项（1017 无 p4/p5）', '叠加上限', 'Chain 影响', '实机'],
    }
