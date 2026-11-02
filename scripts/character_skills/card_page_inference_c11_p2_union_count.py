# -*- coding: utf-8 -*-
"""C11-P2 ``skilllist|1059|``（UnionCount）首段五属性：**候选**实现（14 行 / 70 答案，全 Y.G.）。

任务卡 ``docs/tasks/20261031-c11-p2-union-count.md``；选题预检
``output/character_skills/c11_p2_selection_20261031/selection_report.md``；周期计划
``docs/tasks/20261031-c11-c13-three-cycle-plan.md``。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；正式页面、
``rules.json``、``effect_ledger`` 均未改动；正式全库生成与全库检查不在本阶段。账本所需
**恰好 5 条键精确映射**以独立 patch/JSON 形式放在候选目录，本模块不写 ``_RULE_KEY_EFFECT``。

句子与范围
----------
只处理记录正文**首段 ◆** 的那一句：

    戦場に自身を含む<A/B/C>所属の味方が多いほど味方全体の攻撃力と防御力と移動速度と
    クリティカル発生率とクリティカル威力が上がる。

三种筛选形态各自绑定一个筛位（双向）：``<…>所属`` ↔ ``param8``（出身）、``<…>武器`` ↔
``flag0_0``（武器）、``A/B/C``（无尖括号、无后缀）↔ ``iParam0``（职业）。五个属性词按固定
顺序出现，缺一、换序、改成「下がる」都不在本族内。

**第二 ◆ 段不归属本句**：同一记录 ``text`` 的第二段（「自身を含む味方が必殺技を発動する
たび…」）与卡面页面的后续 fragment（f2 起）由 ``sub`` 链承载，本模块只消费父记录的
``param1..param5``，不读、不映射任何 sub 记录；答案里显式写明该披露。

0 新公式、0 新规则键、0 新原生
-----------------------------
五条换算全部复用 ``profiles/rules.json`` 已确认的 ``skilllist|1059|/param1../param5``；
本模块通过 ``rules.answer_for('skilllist', 1059, '/paramN', raw, record, source_layer='CACHE')``
取 ``conversion/unit/quantity_kind/conditions/evidence``，**不在本批重写公式**。受控原生证据
``output/character_skills/skilllist_types/union_count_chains.json``（``verified=true``）给出
门控 ``0x423``、装载 ``0x10f5830``、施加段 ``0x110bc28..0x110be64`` 与五个玩家侧消费点；
其 ``player_side_paramn_aggregation`` 明确聚合为**极值选择（EXTREMUM_SELECTION）**，
**不是按人叠乘**——答案按此写「单记录精确」，不写人数比例、不写 5 人上限。

准入是**结构规则**，不是 row_id / 记录 / 原值白名单
---------------------------------------------------
模块内没有任何 row_id、卡号、记录号或原值常量（``candidate/run_checks.py`` 的静态扫描用例
断言这一点）。判定顺序：

    D1 行身份：``group == 'ability'``、``reference_field == 'skillid[2]'``、
       ``fragment_index == 0``（首段），且句面逐字匹配本族句式（五属性顺序固定）。
    D2 同层来源：``layer == 'CACHE'``、``source_key == CACHE/skilllist.data5.json.raw``、
       ``field == '/text'``、``json_pointer`` 匹配 ``/skilllist/<n>``；不读 APK 表。
    D3 父链一致：``charainfo[cid].skillid[2]`` → 该下标记录 ``skillid`` 全表唯一命中，
       下标就是 D2 的 ``<n>``；记录 ``ability`` 为本族类型。
    D4 槽位与筛选：``param0..param5`` 缺失/null/非有限/非数值/真零/负值逐档独立拒绝
       （不补 0）；``param6/param7``（周期回复槽）非零拒绝（句面无回复主张）；
       ``param9/flag1_0``（受益侧筛选）非零拒绝（句面「味方全体」）；``iParam1`` 必须是
       全 5 职业位图；``param8/flag0_0/iParam0`` **恰一个**非零，解码集合与句面 token 集合
       逐项相等（武器位按 ``text_crosscheck`` 落位＋剩余 token 与剩余 bit 一一计数）。
    D5 首段唯一：本行日语是父记录 ``text`` 首段 ◆ 的开头且全记录恰出现 1 次、不出现在第二
       ◆ 段；该句在该卡 ``charainfo.skillid`` 全部记录中恰命中 1 条（就是父记录）；同一
       ``reference_field`` 内恰 1 行匹配本句式（不抢子句）。
    D6 规则语义：五槽的 ``answer_for`` 必须返回非空，且 ``meaning_zh`` 含对应属性关键词
       （攻击倍率／移动速度倍率／受伤量倍率／暴击率／暴击伤害）。规则语义漂移即拒绝，
       不静默沿用硬编码映射。
    D7 幂等：本行已有同 ``rule_key`` 答案——同记录同字段同原值同层 → ``ALREADY_PRESENT_SAME``
       （零写入）；其余 → ``ALREADY_ANSWERED``（只写披露 marker，不改写既有答案）。

**批次边界由调用方显式声明**：``apply_to_groups(data, cid, groups, scope_cids=...)``，缺省
``None`` → 一行都不处理（``NO_SCOPE_DECLARED``），避免将来接线时按结构规则无声扩面。
保护卡 30236／30239 在模块内硬拒绝。

证据分档（不得升格）
--------------------
* 原值与规则：``numeric_evidence = 确认``（rules.json 已确认静态换算＋受控原生片段）。
* 「本行句面 → 本记录五槽」：``association_evidence = 推断``（句面不写数值；归属由句面属性
  顺序＋筛选位双向＋记录唯一给出，未做实机）。``answer_status`` 沿用页面既有口径
  ``CONFIRMED_NUMERIC``（数值确认、关联推断），不新增状态词。
* 不写最终伤害、最终 HP、命中人数比例、5 人上限、叠加上限；不写固定防御量，也不写
  「防御力 −15%」；原文「5人」只作原文披露（由另一行承载，本模块零触碰）。
* 第二 ◆ 段（必殺技発動／Chain 增量／サブパーティ）机制不归属本句，不消费 sub 记录。

接口
----
``evaluate(data, cid, row, rows=None, skill=None, tab=None)``  单行判定（不写入）。
``build_answers(data, cid, row, res)``                          五条答案对象（复用 rules）。
``apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None)`` 正式页消费（候选未接线）。
``tables(data)`` / ``clone_tables(tab)``                        CACHE 主表只读索引（可注入，反例用）。
"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

MODULE_VERSION = 'c11_p2_union_count_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 本批证据 scope（写进答案 binding，供账本/页面按 scope 精确消费时对账）。
SCOPE = 'C11_P2_UNION_COUNT_20261031'
#: 结构判定自身 scope（行级 marker）。
STRUCTURE_SCOPE = 'C11_P2_UNION_COUNT_CHAIN_20261031'
#: 行级 marker 键（每行至多一个本批键，不覆盖其他批的 marker）。
MARKER_KEY = 'inference_c11_p2_union_count'

#: 本族载体：skilllist 的 ability 1059（UnionCount）。
TABLE = 'skilllist'
ABILITY = 1059
REF_FIELD = 'skillid[2]'
TEXT_FIELD = '/text'
SOURCE_KEY = 'CACHE/skilllist.data5.json.raw'
#: CACHE 解码主表目录（与预检、C11-P1 同源快照）。
BASE = 'output/cache_full_20261015_v3/decoded'
FILTER_DICT = 'output/character_skills/skilllist_types/filter_dictionary.json'

#: 保护卡：30236（G0）／30239（豁免不扩大）零触碰。
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

#: 句面固定部分：五个属性按此顺序；「上がる」不可换向。
_SENTENCE_RX = re.compile(
    r'^戦場に自身を含む'
    r'(?:<(?P<home>[^<>]+)>所属'
    r'|<(?P<weapon>[^<>]+)>武器'
    r'|(?P<job>[^<>の]+))'
    r'の味方が多いほど味方全体の攻撃力と防御力と移動速度と'
    r'クリティカル発生率とクリティカル威力が上がる。$')
_ATTRS = ('攻撃力', '防御力', '移動速度', 'クリティカル発生率', 'クリティカル威力')
#: 值槽 → (字段, 句面属性, 规则 meaning_zh 关键词)。关键词是 D6 语义守卫：
#: 规则文本一变即拒绝，不静默沿用本表。
VALUE_SLOTS = (
    ('param1', '/param1', '攻撃力', ('攻击倍率',)),
    ('param2', '/param2', '移動速度', ('移动速度倍率',)),
    ('param3', '/param3', '防御力', ('受伤量倍率',)),
    ('param4', '/param4', 'クリティカル発生率', ('暴击率',)),
    ('param5', '/param5', 'クリティカル威力', ('暴击伤害',)),
)
#: 按记录必读的六个数值槽（param0 只是人数阈值，不产出值行）。
NUMERIC_SLOTS = ('param0',) + tuple(s[0] for s in VALUE_SLOTS)
#: 周期回复槽（apply 段 heals）与受益侧筛选槽：句面「味方全体五属性」不支持它们非零。
RECOVERY_SLOTS = ('param6', 'param7')
BENEFIT_FILTER_SLOTS = ('param9', 'flag1_0')
#: 计数筛选三选一：home(param8)／weapon(flag0_0)／job(iParam0)。
FILTER_SLOTS = ('param8', 'flag0_0', 'iParam0')
#: iParam1 = bit0..4 全 5 职业 = 「味方全体」。
BENEFIT_JOBS = 31
_DIM_ZH = {'home': '出身', 'weapon': '武器', 'job': '职业'}
#: 页面既有答案里本批上线前应被本批替换为「已解」的通用未知原因（逐字）。
_STALE_REASONS = (
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '旧关键词候选未作为答案；不能排除对象或效果错配',
)
RESIDUAL_NOTE = ('C11-P2：首段 1059 记录五槽（param1..param5）按已确认换算给值、句面归属为推断；'
                 '「多いほど」人数递增比例与「5人まで」上限未在记录中符号化（保留未知）；'
                 '第二 ◆ 段（sub 链）机制不归属本句；未做实机验证')
RESIDUAL_LABEL = '推断（C11-P2：1059 UnionCount 首段五属性槽位归属；人数比例与 5 人上限未符号化）'

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
        # 数字字符串/其他类型一律拒绝（不 float() 隐式转换，避免 '1.15' 被当成有限值）
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
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


# ---------------------------------------------------------------- CACHE 主表

def tables(data):
    """CACHE 解码主表（按 root 缓存，只读）。``tab`` 可由调用方注入（反例用）。

    ``skills`` 保留**数组下标**（行来源 ``/skilllist/<n>`` 按下标解析；``by_id`` 是按
    skillid 的索引视图，二者须指向同一条记录才放行）。
    """
    root = Path(getattr(data, 'root', Path('.'))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = root / BASE
        skilllist = _read(base / 'skilllist.data5.json.raw')['skilllist']
        skills, by_id = {}, {}
        for index, record in enumerate(skilllist):
            if record.get('skillid') is not None:
                skills.setdefault(record['skillid'], []).append((index, record))
                by_id.setdefault(record['skillid'], []).append((index, record))
        chara_list = _read(base / 'charainfo.data5.json.raw')['charainfo']
        chara = {record['cid']: record for record in chara_list}
        fdict = _read(root / FILTER_DICT)
        _TABLES[key] = dict(skills=skills, by_id=by_id, chara=chara,
                            chara_list=chara_list, filter=fdict, root=root)
    return _TABLES[key]


def clone_tables(tab):
    """反例用：深拷贝只读索引（不改动全局缓存）。"""
    return {k: (copy.deepcopy(v) if k in ('skills', 'by_id', 'chara', 'chara_list', 'filter') else v)
            for k, v in tab.items()}


# ---------------------------------------------------------------- 句面与筛位

def parse_sentence(japanese):
    """解析本族句式；返回 ``(form, tokens, detail)``，不匹配返回 ``(None, None, detail)``。

    form ∈ {'home','weapon','job'}：尖括号＋「所属」＝出身、尖括号＋「武器」＝武器、
    无尖括号无后缀＝职业。五个属性词的顺序由正则固定，不接受缺项/换序/「下がる」。
    """
    text = str(japanese or '')
    if not text:
        return None, None, {'reason': 'ROW_TEXT_EMPTY'}
    match = _SENTENCE_RX.match(text)
    if not match:
        return None, None, {'reason': 'SENTENCE_NOT_UNION_COUNT', 'text': text}
    if match.group('home'):
        form, body = 'home', match.group('home')
    elif match.group('weapon'):
        form, body = 'weapon', match.group('weapon')
    else:
        form, body = 'job', match.group('job')
    tokens = [tok for tok in body.split('/') if tok]
    if not tokens or len(tokens) != len(set(tokens)):
        return None, None, {'reason': 'SENTENCE_TOKENS_INVALID', 'tokens': tokens}
    return form, tokens, {'reason': None, 'form': form, 'tokens': tokens,
                          'bracketed': form in ('home', 'weapon')}


def _sentence_attrs_present(text):
    """五属性词是否按固定顺序出现（正则已保证，此处给 evidence 用）。"""
    return [attr for attr in _ATTRS if attr in str(text or '')]


def decode_filter(record, fdict):
    """按 filter_dictionary 解码三个筛位；返回 ``(dimension, decoded, detail, fails)``。"""
    fails = []
    values, states = {}, {}
    for name in FILTER_SLOTS:
        value, state = _int_or_zero(record, name)
        values[name] = value
        states[name] = state
        if value is None:
            fails.append('FILTER_SLOT_NOT_INTEGRAL')
    nonzero = [name for name in FILTER_SLOTS if values.get(name)]
    if fails:
        return None, set(), {'values': values, 'states': states}, fails
    if len(nonzero) != 1:
        return None, set(), {'values': values, 'states': states, 'nonzero': nonzero}, [
            'FILTER_DIMENSION_NOT_UNIQUE']
    name = nonzero[0]
    dimension = {'param8': 'home', 'flag0_0': 'weapon', 'iParam0': 'job'}[name]
    detail = {'values': values, 'states': states, 'dimension': dimension, 'slot': name,
              'evidence': []}
    if dimension == 'home':
        raw = values['param8']
        groups = [raw % 100, (raw // 100) % 100, (raw // 10000) % 100]
        if raw // 1000000:
            fails.append('FILTER_UNKNOWN_GROUP')
        ids = fdict['home']['table']['ids']
        names = []
        for group in groups:
            if str(group) not in ids:
                fails.append('FILTER_UNKNOWN_GROUP')
                break
            names.append(ids[str(group)])
        detail.update(groups=groups, decoded=names,
                      evidence=['homelist.home_id（filter_dictionary home.table.ids）'])
        return dimension, set(names), detail, fails
    if dimension == 'job':
        raw = values['iParam0']
        enum = fdict['job']['enum']
        names_zh = fdict['job']['names_zh']
        known = {bit: key for key, bit in enum.items()}
        bits = [bit for bit in range(32) if raw >> bit & 1]
        names = []
        for bit in bits:
            key = known.get(bit)
            if key is None or key not in names_zh:
                fails.append('FILTER_UNKNOWN_JOB_BIT')
                break
            names.append(names_zh[key])
        detail.update(bits=bits, decoded=names,
                      evidence=['job iParam0 位图 + filter_dictionary job.names_zh'])
        return dimension, set(names), detail, fails
    raw = values['flag0_0']
    bits_table = fdict['weapon']['bits']
    set_bits = {int(spec['bit']) for spec in bits_table.values()}
    bits = [bit for bit in range(32) if raw >> bit & 1]
    unknown = [bit for bit in bits if bit not in set_bits]
    if unknown:
        fails.append('FILTER_UNKNOWN_WEAPON_BIT')
        return dimension, set(), dict(detail, bits=bits, unknown_bits=unknown), fails
    cross = {}
    for sample in fdict['weapon'].get('text_crosscheck', {}).get('samples', ()):
        cross[str(sample.get('text_word'))] = int(sample['bit'])
    detail.update(bits=bits, crosscheck=cross,
                  evidence=['weapon flag0_0 位图 + filter_dictionary weapon.text_crosscheck'])
    return dimension, set(), detail, fails


def compare_tokens(dimension, decoded, detail, tokens):
    """句面 token ↔ 筛位解码集合的双向核对（武器按落位＋剩余一一计数）。"""
    fails = []
    token_set = set(tokens)
    if dimension == 'weapon':
        cross = detail.get('crosscheck') or {}
        bits = set(detail.get('bits') or ())
        known = {tok: cross[tok] for tok in tokens if tok in cross}
        if any(bit not in bits for bit in known.values()):
            fails.append('FILTER_TEXT_MISMATCH')
        rest_tokens = [tok for tok in tokens if tok not in known]
        rest_bits = sorted(bits - set(known.values()))
        detail['bit_text'] = {tok: ('text_crosscheck' if tok in cross else 'count_only')
                              for tok in tokens}
        detail['unmatched_tokens'] = rest_tokens
        detail['unmatched_bits'] = rest_bits
        if len(bits) != len(tokens) or len(rest_tokens) != len(rest_bits):
            fails.append('FILTER_TEXT_MISMATCH')
        elif len(rest_tokens) > 1:
            # 两个以上无对照词的 token 只能计数、不能建立集合相等 → 不猜。
            fails.append('FILTER_TEXT_AMBIGUOUS')
    else:
        detail['decoded'] = sorted(decoded)
        if decoded != token_set:
            fails.append('FILTER_TEXT_MISMATCH')
    return fails


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
    if int(row.get('fragment_index')) != 0:
        out['rejection'] = 'NOT_FIRST_SEGMENT'
        out['rejection_detail'] = {'fragment_index': row.get('fragment_index')}
        return out
    form, tokens, detail = parse_sentence(row.get('japanese'))
    out['gates']['clause'] = dict(detail, attrs=_sentence_attrs_present(row.get('japanese')))
    if form is None:
        out['rejection'] = detail.get('reason') or 'SENTENCE_NOT_UNION_COUNT'
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
    match = re.match(r'^/skilllist/(\d+)$', str(src.get('json_pointer') or ''))
    if not match:
        out['rejection'] = 'ROW_POINTER_NOT_SKILLLIST'
        return out
    index = int(match.group(1))
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
    # D3 父链一致：指针下标记录 == charainfo.skillid[2]，且 skillid 全表唯一
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
        out['rejection'] = 'ABILITY_NOT_1059'
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
    if float(params['param0']['raw']) != int(float(params['param0']['raw'])):
        out['rejection'] = 'PARAM0_NOT_INTEGRAL'
        return out
    if int(params['param0']['raw']) < 1:
        out['rejection'] = 'PARAM0_BELOW_ONE'
        return out
    # D4b 方向守卫：句面「上がる」⇒ p1/p2 增幅、p3 减伤（受伤量<1）。p4/p5 的负值/零已由
    # D4a 的 NEGATIVE/ZERO 分档逐槽拒绝（不在此重复成不可达分支）。
    p1, p2 = float(params['param1']['raw']), float(params['param2']['raw'])
    p3 = float(params['param3']['raw'])
    if not (p1 > 1 and p2 > 1):
        out['rejection'] = 'PARAM12_DIRECTION_CONTRADICTS_SENTENCE'
        return out
    if not (0 < p3 < 1):
        out['rejection'] = 'PARAM3_RANGE_CONTRADICTS_SENTENCE'
        return out
    # D4c 句面未主张的槽：周期回复与受益侧筛选必须为缺省/null/零
    for name in RECOVERY_SLOTS:
        value, state = _int_or_zero(record, name)
        if state in ('invalid', 'non_integral') or value:
            out['rejection'] = 'PARAM_RECOVERY_NONZERO'
            out['rejection_detail'] = {'slot': name, 'raw': record.get(name), 'state': state}
            return out
    for name in BENEFIT_FILTER_SLOTS:
        value, state = _int_or_zero(record, name)
        if state in ('invalid', 'non_integral') or value:
            out['rejection'] = 'BENEFIT_FILTER_NONZERO'
            out['rejection_detail'] = {'slot': name, 'raw': record.get(name), 'state': state}
            return out
    benefit, state = _int_or_zero(record, 'iParam1')
    if benefit != BENEFIT_JOBS:
        out['rejection'] = 'BENEFIT_JOBS_NOT_ALL'
        out['rejection_detail'] = {'iParam1': record.get('iParam1'), 'state': state}
        return out
    # D4d 筛位：恰一维非零，解码集合 = 句面 token，形态与维度双向一致
    dimension, decoded, fdetail, fails = decode_filter(record, tab['filter'])
    out['gates']['filter'] = fdetail
    if fails:
        out['rejection'] = fails[0]
        return out
    if dimension != form:
        out['rejection'] = 'FILTER_FORM_MISMATCH'
        out['rejection_detail'] = {'dimension': dimension, 'sentence_form': form}
        return out
    fails = compare_tokens(dimension, decoded, fdetail, tokens)
    if fails:
        out['rejection'] = fails[0]
        return out
    # D5 首段唯一
    # 解码 JSON 的 text 用**字面** ``\n``（反斜线＋n）分段（不是控制字符），两种都归一后
    # 再切 ◆ 段，避免把整段当成首段而漏掉「第二 ◆ 段不归属」的核对。
    record_text = str(record.get('text') or '').replace('\\n', '\n')
    body = str(row.get('japanese') or '')
    segments = record_text.split('\n')
    first = segments[0] if segments else ''
    second = '\n'.join(segments[1:])
    occurrences = record_text.count(body)
    out['gates']['segment'] = {
        'occurrences_in_record': occurrences,
        'first_segment_prefix': first.startswith('◆' + body),
        'in_second_segment': body in second,
        'second_segment_chars': len(second),
        'sub_consumed': False,
    }
    if body not in first:
        out['rejection'] = 'SENTENCE_NOT_IN_FIRST_SEGMENT'
        return out
    if body in second:
        out['rejection'] = 'SENTENCE_IN_SECOND_SEGMENT'
        return out
    if occurrences != 1:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_RECORD'
        return out
    if not first.startswith('◆' + body):
        out['rejection'] = 'SENTENCE_NOT_FIRST_SENTENCE'
        return out
    holders = [sid for sid in skillids
               if isinstance(sid, int) and sid in tab['skills']
               and body in (tab['skills'][sid][0][1].get('text') or '')]
    out['gates']['card_holders'] = holders
    if holders != [parent_id]:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_CARD'
        return out
    siblings = []
    if isinstance(rows, dict):
        for other in rows.values():
            if str(other.get('reference_field') or '') != REF_FIELD:
                continue
            oform, _otok, _od = parse_sentence(other.get('japanese'))
            if oform is not None:
                siblings.append(other.get('row_id'))
    out['gates']['sentence_rows'] = siblings
    if len(siblings) != 1 or siblings[0] != rid:
        out['rejection'] = 'SENTENCE_NOT_UNIQUE_IN_SCOPE'
        return out
    # D6 规则语义（五槽 answer_for 非空 + meaning 关键词）
    import rules as R
    slots = []
    for name, field, attr, keywords in VALUE_SLOTS:
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
                      'raw': record.get(name), 'rule': answer})
    out['gates']['rule_slots'] = [{'slot': s['slot'], 'meaning_zh': s['rule'].get('meaning_zh'),
                                   'rule_key': '%s|%d|%s' % (TABLE, ABILITY, s['field']),
                                   'raw': s['raw']} for s in slots]
    out['accepted'] = True
    out['record'] = {'skillid': parent_id, 'index': rec_index,
                     'ability': record.get('ability'), 'layer': 'CACHE',
                     'sub': list(record.get('sub') or ())}
    out['sentence'] = {'form': form, 'tokens': tokens,
                       'filter_display': ('〈%s〉' % '/'.join(tokens)) if detail['bracketed']
                       else '/'.join(tokens)}
    out['slots'] = slots
    return out


# ---------------------------------------------------------------- 答案对象

def _answer_key(field):
    return '%s|%d|%s' % (TABLE, ABILITY, field)


def _common_text(res, record):
    """条件／对象／未知／段落边界的公共表述（数值全部来自记录与规则，不硬编码）。"""
    tokens = res['sentence']['tokens']
    dimension = res['gates']['filter'].get('dimension')
    dim_zh = _DIM_ZH.get(dimension, dimension)
    p0 = int(record.get('param0'))
    display = res['sentence']['filter_display']
    cond = ('条件：满足%s（%s）任一筛选的存活角色数 ≥ int(param0)=%d 时生效（含等于）；'
            'param0 只是人数阈值，不是效果量' % (display, dim_zh, p0))
    obj = ('对象＝玩家侧队伍范围（iParam1=全 5 职业位图、句面「味方全体」，'
           'PlayerManager.GetAbility* 施加），不是只作用于自身')
    unknown = ('「多いほど」的人数递增比例与「5人まで」上限未在记录中符号化，保留未知；'
               '聚合为极值选择（EXTREMUM_SELECTION），不是按人叠乘，单记录精确')
    scope = '本行只消费首段 ◆ 的 1059 记录五槽；第二 ◆ 段（sub 链）机制不归属本句'
    limits = '不写最终伤害/HP、不写叠加上限；句面→槽位归属为推断，未做实机'
    return '；'.join((cond, obj, unknown, scope, limits))


def build_answers(data, cid, row, res, tab=None):
    """构造五条答案对象（复用 ``rules.answer_for`` 的换算与证据字段，不重写公式）。"""
    if not res.get('accepted'):
        return []
    tab = tab or tables(data)
    index = res['record']['index']
    parent_id = res['record']['skillid']
    pointer = '/skilllist/%d' % index
    record = tab['skills'][parent_id][0][1]
    common = _common_text(res, record)
    row_id = row.get('row_id')
    tokens = res['sentence']['tokens']
    fdetail = res['gates']['filter']
    answers = []
    for slot in res['slots']:
        name, field, attr, rule = slot['slot'], slot['field'], slot['attr'], slot['rule']
        raw = slot['raw']
        value_text = num_text(raw)
        if name == 'param1':
            value = ('队伍攻击率 ×%s（本项 +%s%%）' % (value_text, pct_text(raw, 1.0)))
            qk = rule.get('quantity_kind')
        elif name == 'param2':
            value = ('移动速度 ×%s（本项 +%s%%）' % (value_text, pct_text(raw, 1.0)))
            qk = rule.get('quantity_kind')
        elif name == 'param3':
            # 减伤幅度 = (1 − 受伤量倍率) ×100；用绝对值文本，避免出现「减伤 -15%」这种双负号。
            reduction = ('%g' % round((1.0 - float(raw)) * 100.0, 6))
            value = ('受伤量 ×%s（本项减伤 %s%%；这是受伤量倍率，不是固定防御量，'
                     '也不是「防御力 −%s%%」）' % (value_text, reduction, reduction))
            qk = rule.get('quantity_kind')
        elif name == 'param4':
            value = ('暴击率 += +%s 个百分点（原值 %s ×100，对 0 的加算增量）'
                     % (pct_text(raw), value_text))
            qk = rule.get('quantity_kind')
        else:
            value = '暴击伤害系数 += %s（加算增量）' % value_text
            qk = rule.get('quantity_kind')
        answers.append({
            'value': '%s。%s。' % (value, common),
            'quantity_kind': qk,
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
            'evidence_scope': 'BY_TYPE_EXTRAPOLATED',
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
                'filter': {'dimension': fdetail.get('dimension'),
                           'tokens': list(tokens),
                           'decoded': fdetail.get('decoded'),
                           'bit_text': fdetail.get('bit_text'),
                           'values': fdetail.get('values')},
                'condition': {'param0': record.get('param0'), 'param0_is_threshold': True,
                              'iParam1': record.get('iParam1'),
                              'benefit_side': '味方全体（全 5 职业位图）'},
                'segment': 'first',
                'second_segment_not_attributed': True,
                'sub_records_not_consumed': list(record.get('sub') or ()),
                'aggregation': '极值选择（EXTREMUM_SELECTION）；不是按人叠乘；单记录精确',
                'association': '推断',
                'disclosure': {
                    'per_person_scaling': 'UNKNOWN（「多いほど」人数比例未符号化）',
                    'five_person_cap': 'UNKNOWN（「5人まで」上限未符号化；原文「5人」只作原文披露）',
                    'second_segment': 'NOT_ATTRIBUTED（第二 ◆ 段由 sub 链承载）',
                    'defense_semantics': ('受伤量倍率 0.85＝减伤，不是固定防御量、'
                                          '不是防御力 −15%'),
                    'rights': '不写最终伤害/HP/叠加上限；未做实机',
                },
            }},
        })
    return answers


# ---------------------------------------------------------------- 页面消费（候选）

def _existing_same(row, answers):
    """已有同键答案：全部同记录/同字段/同原值/同层 → SAME；否则 CONFLICT。"""
    existing = {}
    for answer in row.get('answers') or []:
        key = answer.get('rule_key')
        if key in {a['rule_key'] for a in answers}:
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
    rows_map = {r['row_id']: r for g in groups for s in g.get('skills') or []
                for r in s.get('rows') or []}
    for group in groups:
        if group.get('group') != 'ability':
            continue
        for skill in group.get('skills') or []:
            if str(skill.get('reference_field') or '') != REF_FIELD:
                continue
            for row in skill.get('rows') or []:
                if int(row.get('fragment_index') or 0) != 0:
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
    """行级标注：证据档、scope、残余未知原因与本批 marker（不改 row_class／partial）。"""
    row['evidence'] = '推断'
    row['evidence_scope'] = ['BY_TYPE_EXTRAPOLATED']
    row['evidence_label'] = RESIDUAL_LABEL
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    if RESIDUAL_NOTE not in reasons:
        reasons.append(RESIDUAL_NOTE)
    row['unknown_reasons'] = reasons
    _write_marker(row, res, cid, state='ANSWERS_ADDED')


def _write_marker(row, res, cid, state):
    fdetail = res['gates'].get('filter') or {}
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
        'filter': {'dimension': fdetail.get('dimension'),
                   'slot': fdetail.get('slot'),
                   'tokens': list(res['sentence']['tokens']),
                   'values': fdetail.get('values')},
        'condition': {'param0_is_threshold': True, 'iParam1': BENEFIT_JOBS},
        'rule_keys': [('skilllist|%d|%s' % (ABILITY, slot[1])) for slot in VALUE_SLOTS],
        'segment': 'first',
        'second_segment_not_attributed': True,
        'sub_records_not_consumed': res['record'].get('sub'),
        'association': '推断',
        'unknowns': ['多いほど人数比例', '5人まで上限', '第二 ◆ 段机制', '叠加上限', '实机'],
    }
