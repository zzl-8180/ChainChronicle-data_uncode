# -*- coding: utf-8 -*-
"""C11-P1 t114 冲刺重复攻击伤害：**直接行**候选（4 行 / 4 效果，全 Y.G.）。

任务卡 ``docs/tasks/20261031-c11-p1-t114-direct.md``；规则入口
``docs/角色技能完整解读实施方案.md``（2026-10-24 修订）；周期计划
``docs/tasks/20261031-c11-c13-three-cycle-plan.md``。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块，
正式页面、rules.json、effect_ledger 均未改动；正式全库生成与全库检查不在本阶段。

为什么是这四行（范围）
----------------------
30002 pattern0 f2／pattern1 f2 与 30229 pattern0 f2／pattern1 f2 四条**直接描述行**，
句面同为「さらにダッシュ範囲上にいる全ての敵に25回ダメージを与え、弾き飛ばした後、
元の位置に戻る。」本行原始链（CACHE ``/bossinfo/bosspattern`` → ``/bossinfo/bossskill``）
各恰有 1 条 type114，``skillparam1`` 为有限正值（1／1.2／0.6／0.8）。

**0 新增规则键、0 新公式、0 新原生点**：``bossskill|114|/skillparam1`` 已在
``profiles/rules.json`` 确认为局部公式 ``floor/clamp(float32(B × p1))``，
``B=getBasicSkillAttack(true)`` 已含 Chain；账本已有全局映射
``bossskill|114|/skillparam1 → ダメージ（词表外）``（``effect_ledger._RULE_KEY_EFFECT``），
本批不新增映射、不改 ``_RULE_KEY_EFFECT``／rules.json／rules.py。

准入是**结构规则**，不是 row_id / 原值白名单
--------------------------------------------
模块内**没有任何** row_id、卡号、记录号或原值常量（见 ``D1``–``D5`` 与
``output/character_skills/c11_p1_t114_20261031/candidate/run_checks.py`` 的静态扫描用例）。
判定顺序：

    D1 行身份：``group == 'special_move'``；``reference_field`` 匹配 ``^pattern\\d$``
       （**直接行**）——skilltext 镜像行、denju 行、pattern 以外的族一律不在本规则族内。
    D2 同层来源：``row.source.layer == 'CACHE'``、``source_key ==
       CACHE/bossinfo.data5.json.raw``、``source.field == '/sinfo'``、
       ``json_pointer`` 匹配 ``/bossinfo/bosspattern/<n>``。不读 APK 表，跨层在结构上不可达。
    D3 父链一致：``charainfo[cid][patternN]`` → ``bosspattern.patternid`` 唯一命中，
       且该命中的数组下标**等于** D2 的 ``<n>``（行的父记录就是本卡该档位的执行链）。
    D4 句面机制：本行日语必须是该 pattern ``sinfo`` 的**逐字唯一子串**；且同时含
       「ダッシュ範囲上」（冲刺位移）与「N回ダメージを与え」（重复命中）两个机制词。
       同一档位内（同一 reference_field）**恰 1 行**满足该机制 → 否则拒绝（不抢子句）。
    D5 载体唯一（伤害族内）：链内子记录槽位从 0 连续、``skillid`` 在 bossskill 全表唯一；
       以 ``rules.json`` 已确认的**伤害族键**（``unit`` 含「倍」且 ``meaning_zh`` 含「伤害」、
       不含「非伤害」）为竞争域：链内伤害族子记录**恰 1 条**且其类型为 114；
       type52（无已确认规则键）与 type13（已确认键是攻撃力等保单，非伤害）因此**结构上
       不与该冲刺伤害槽竞争**——若链内另有一条伤害族子记录（例如 type51/55/74/105/110），
       一律拒绝，不猜哪条才是本句子的载体。
    D6 槽位与取值：``skillparam1`` 缺失/null/非有限/负值/真零**逐档独立拒绝**，不补 0；
       规则键由 ``rules.rule_for('bossskill', 114, '/skillparam1')`` 提供，规则语义需含
       「冲刺」「重复」两词（机制词与规则族语义对上，属文本级机制守卫，不是原生证明）。
    D7 幂等：本行已有同 rule_key 答案时——同记录同值 → ``ALREADY_PRESENT_SAME``（零写入）；
       其余 → ``ALREADY_ANSWERED``（只披露，不新增、不改写既有值）。

**批次边界由调用方显式声明**：``apply_to_groups(data, cid, groups, scope_cids=None)``。
``scope_cids`` 缺省为 ``None`` → 一行都不处理（``NO_SCOPE_DECLARED``），避免将来接入时
按结构规则无声扩面。任务卡只授权 30002／30229 四条直接行，故本阶段只以
``scope_cids={30002, 30229}`` 运行。

skilltext 镜像两行（同卡同记录同值，opt-in）
------------------------------------------
30002／30229 各有一条 ``reference_field == 'skilltext'`` 的**卡面文本行**（来源
``CACHE/charainfo.data5.json.raw`` 的 ``/charainfo/<i>`` 字段 ``/skilltext``，即
``charainfo`` 索引 309／345）；其正文与本卡 ``pattern0`` 直接行逐字相同。这类行**没有
自己的执行链**（不指向 bosspattern／bossskill），因此不重新推导数值，只复用**同卡、同
记录、同 rule_key、同 raw_value、同 CACHE 层**的直接基档答案：

    M1 行身份：``group == 'special_move'`` 且 ``reference_field == 'skilltext'``、
       来源 ``field == '/skilltext'``；其他族、直接行、denju 行在结构上不可达。
    M2 同层父记录：``layer == 'CACHE'``、``source_key ==
       CACHE/charainfo.data5.json.raw``、``json_pointer == /charainfo/<i>``；该下标记录
       存在、其 ``cid`` 与本卡相同，且与 ``charainfo[cid]`` 是同一记录（父链一致）。
       不读 APK 表，跨层在结构上不可达。
    M3 正文：本行日语是该卡面 ``skilltext`` 的**逐字唯一子串**，同时含「ダッシュ範囲上」
       与「N回ダメージを与え」两机制；同一 ``reference_field`` 内**恰 1 行**满足该机制。
    M4 同卡基档：本卡 ``pattern0`` 直接行与 skilltext 行**正文逐字相同**，且该基档经上面
       D1–D6 完整结构判定通过（判定基档时忽略其自身既有答案，写入状态不影响结构判定）；
       该下标记录的 ``pattern0`` 必须就是基档命中的 patternid。于是镜像只可能绑定**同卡
       pattern0 链内唯一的 type114 载体**：不得使用 pattern1 的 1.2／0.8，不得借跨卡先例，
       同文但异记录／异值／异层一律拒绝。
    M5 幂等：镜像行已有同 rule_key 答案时——同记录同值同层 → ``ALREADY_PRESENT_SAME``
       （零写入）；其余 → ``ALREADY_ANSWERED``（只披露，不改写既有值）。

镜像同样**必须由调用方显式声明**：``apply_to_groups(..., mirror_cids=...)``，缺省
``None`` → 镜像行一行不触碰（直接阶段的「镜像新增 0」保持在位）。``mirror_cids`` 内的卡片
还必须同时在 ``scope_cids`` 内（镜像只复用同卡直接行答案），否则
``MIRROR_REQUIRES_DIRECT_SCOPE``。

**结构规则的潜在扩面（本阶段不纳入，只披露）**：全库另有同样满足 D4/D5 的
``bosspattern`` 30 个（13 卡，其中 Y.G. 5 卡／非 Y.G. 8 卡）与 8 条 denju 引用；
载体槽位在这些 pattern 中 slot1 有 23 个、slot2 有 7 个，另有 2 个 pattern 同时含
type51 伤害族（按 D5 会被拒绝）。因此**不**把 slot2 写成准入条件。扩面属后续批次，
不以本批结构规则声称已完成。

证据分档（不得升格）
--------------------
* 原值与规则：``numeric_evidence = 确认``（rules.json 已确认静态局部公式）。
* 「本行句面 → 本行链内 type114.skillparam1」：``association_evidence = 推断``
  （句面不写倍率；归属由句面机制＋本行执行链载体唯一给出，未做实机）。
* 原文「25回」只作原文披露；**不用** ``skillparam4=24`` 反推次数，不写总伤害、
  最终 HP、实际命中次数与间隔；「弾き飛ばす／元の位置に戻る」等子句仍未解析。
* 不写最终扣血，不做实机验证；不跨 CACHE/APK 取值。

接口
----
``evaluate(data, cid, row, rows=None, tab=None)``  直接行单行判定（不写入）。
``evaluate_mirror(data, cid, row, rows=None, tab=None)``  skilltext 镜像行判定（不写入）。
``build_answers(data, cid, row, res)``             答案对象（复用 rules.answer_for 的换算）。
``build_mirror_answer(data, cid, row, res)``      镜像答案（复用同卡直接基档答案）。
``apply_to_groups(data, cid, groups, *, scope_cids=None, mirror_cids=None, tab=None)``
                                                   正式页消费（候选未接线；镜像 opt-in）。
``tables(data)``                                   CACHE 主表只读索引（可注入，供反例使用）。
"""
from __future__ import annotations

import copy
import json
import math
import re
import struct
from pathlib import Path
from project_layout_paths import read_path

#: 批标识：保持直接阶段字符串，便于与 ``candidate/`` 产物对账；镜像阶段用 MIRROR_SCOPE
#: 与 MIRROR_STRUCTURE_SCOPE 区分（模块哈希随镜像分支更新，直接四行由 candidate_mirror 的
#: check 5 与直接检查器回归副本核对未变）。
MODULE_VERSION = 'c11_p1_t114_direct_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 本批证据 scope（写进答案 binding，供账本/页面按 scope 精确消费时对账）。
SCOPE = 'C11_P1_T114_DIRECT_20261031'
#: 结构判定自身 scope（行级 marker）。
STRUCTURE_SCOPE = 'C11_P1_T114_DIRECT_CHAIN_20261031'
#: 镜像批 scope（两行 skilltext 同卡同记录同值镜像）。
MIRROR_SCOPE = 'C11_P1_T114_SKILLTEXT_MIRROR_20261031'
MIRROR_STRUCTURE_SCOPE = 'C11_P1_T114_SKILLTEXT_MIRROR_CHAIN_20261031'

CARRIER_TYPE = 114
FIELD = '/skillparam1'
PARAM = 'skillparam1'
TABLE = 'bossskill'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'
#: 保护卡：30236（G0）／30239（豁免不扩大）零触碰。
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

MARKER_KEY = 'inference_c11_p1_t114'
BASE = 'output/cache_full_20261015_v3/decoded'

#: 直接行判定：reference_field 只能是 patternN（skilltext／denju／其他族一律不在本规则族内）。
DIRECT_ROW_RX = re.compile(r'^pattern\d$')
#: 行来源必须是 bosspattern.sinfo（D2）。
POINTER_RX = re.compile(r'^/bossinfo/bosspattern/(\d+)$')
#: 句面机制：冲刺位移 + N回重复命中（D4）。数字只作披露，不参与载体判定。
DASH_RX = re.compile(r'ダッシュ範囲上')
REPEAT_RX = re.compile(r'(\d+)回ダメージを与え')
#: 规则族语义机制词（D6 机制守卫：规则 meaning_zh 必须同时含这两词）。
RULE_MECH_WORDS = ('冲刺', '重复')

#: 镜像行族：卡面 skilltext 文本行（M1）。
MIRROR_REF = 'skilltext'
MIRROR_FIELD = '/skilltext'
MIRROR_SOURCE_KEY = 'CACHE/charainfo.data5.json.raw'
MIRROR_POINTER_RX = re.compile(r'^/charainfo/(\d+)$')
#: 镜像基档：charainfo 的 primary 指针（卡面必杀文本描述的基础档），不是按数值挑选的档位。
MIRROR_BASELINE_REF = 'pattern0'

_STALE_REASONS = {
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应',
}

_TABLES = {}
_DAMAGE_FAMILY = None


# ---------------------------------------------------------------- 基础工具

def f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def num_text(value):
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


def damage_family():
    """rules.json 已确认的**伤害族**规则键集合：返回 ``{(table, type, field_path)}``。

    判据只用已确认规则自己的字段：``unit`` 含「倍」且 ``meaning_zh`` 含「伤害」、
    不含「非伤害」（type103 落点偏移因此被排除）。不在此表内的类型没有已确认的
    伤害数值语义，结构上不能与本槽竞争。
    """
    global _DAMAGE_FAMILY
    if _DAMAGE_FAMILY is None:
        import rules as R
        fam = set()
        for rule in R.rules():
            meaning = str(rule.get('meaning_zh') or '')
            unit = str(rule.get('unit') or '')
            etype = rule.get('effect_type')
            if (rule.get('table') != TABLE or etype is None
                    or '倍' not in unit or '伤害' not in meaning or '非伤害' in meaning):
                continue
            fam.add((rule.get('table'), etype, rule.get('field_path')))
        if not fam:
            raise RuntimeError('rules.json 伤害族为空，规则输入异常，拒绝适配')
        _DAMAGE_FAMILY = frozenset(fam)
    return _DAMAGE_FAMILY


def table_damage_types(table=TABLE):
    return frozenset(t for (tb, t, _f) in damage_family() if tb == table)


# ---------------------------------------------------------------- CACHE 主表

def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def tables(data):
    """CACHE 解码主表（按 root 缓存，只读）。``tab`` 可被调用方注入（反例用）。

    ``chara_list`` 保留 charainfo 的**数组顺序**（镜像行的 ``/charainfo/<i>`` 指针按下标
    解析；``chara`` 是按 cid 的索引视图，二者须一致才放行镜像）。
    """
    root = Path(getattr(data, 'root', Path('.'))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = read_path(root / BASE, root=root)
        boss = _read(base / 'bossinfo.data5.json.raw')['bossinfo']
        patterns, skills = {}, {}
        for i, rec in enumerate(boss.get('bosspattern') or []):
            patterns.setdefault(rec.get('patternid'), []).append((i, rec))
        for i, rec in enumerate(boss.get('bossskill') or []):
            skills.setdefault(rec.get('skillid'), []).append((i, rec))
        chara_list = _read(base / 'charainfo.data5.json.raw')['charainfo']
        chara = {rec['cid']: rec for rec in chara_list}
        _TABLES[key] = dict(patterns=patterns, skills=skills, chara=chara,
                            chara_list=chara_list, root=root)
    return _TABLES[key]


def clone_tables(tab):
    """反例用：深拷贝只读索引（不改动全局缓存；整型键保持整型）。"""
    return {k: (copy.deepcopy(v) if k in ('patterns', 'skills', 'chara', 'chara_list') else v)
            for k, v in tab.items()}


# ---------------------------------------------------------------- 纯函数判定

def classify_clause(japanese):
    """句面机制（D4）：返回 ``(form, detail)``。数字只作披露。"""
    text = str(japanese or '')
    if not text:
        return None, {'reason': 'ROW_TEXT_EMPTY'}
    if not DASH_RX.search(text):
        return None, {'reason': 'NO_DASH_RANGE_CLAUSE'}
    m = REPEAT_RX.search(text)
    if not m:
        return None, {'reason': 'NO_REPEAT_HIT_CLAUSE'}
    return 'DASH_REPEAT', {'clause': m.group(0), 'literal_hits': int(m.group(1)),
                           'note': '原文回数只作披露，不用于载体判定、不写总伤害'}


def _param_view(record, name):
    return {'present': name in record, 'raw': record.get(name),
            'state': raw_state(record.get(name), name in record)}


# ---------------------------------------------------------------- 单行判定

def evaluate(data, cid, row, rows=None, tab=None):
    """单行判定（不写入）。``rows`` 为同一 ``reference_field`` 下的全部行（D4 唯一性）。"""
    rid = row.get('row_id')
    out = {'row_id': rid, 'cid': cid, 'module': MODULE_VERSION,
           'accepted': False, 'rejection': None, 'gates': {}, 'detail': None}
    if cid in ZERO_TOUCH_CIDS:
        out['rejection'] = 'ZERO_TOUCH_CID'
        return out
    # D1 行身份
    ref = str(row.get('reference_field') or '')
    if row.get('group') != 'special_move':
        out['rejection'] = 'NOT_SPECIAL_MOVE_ROW'
        return out
    if not DIRECT_ROW_RX.match(ref):
        out['rejection'] = 'NOT_DIRECT_PATTERN_ROW'
        out['detail'] = {'reference_field': ref,
                         'note': 'skilltext 镜像行、denju 行与其他族不在本规则族内'}
        return out
    tab = tab or tables(data)
    gates = out['gates']
    gates['row'] = {'row_id': rid, 'cid': cid, 'group': row.get('group'),
                    'reference_field': ref,
                    'japanese': row.get('japanese'),
                    'layer': (row.get('source') or {}).get('layer')}
    # D2 同层来源
    src = row.get('source') or {}
    gates['row_source'] = {k: src.get(k) for k in
                           ('source_key', 'layer', 'field', 'json_pointer', 'record_key')}
    if src.get('layer') != 'CACHE' or src.get('source_key') != 'CACHE/bossinfo.data5.json.raw':
        out['rejection'] = 'ROW_LAYER_NOT_CACHE'
        return out
    if str(src.get('field') or '') != '/sinfo':
        out['rejection'] = 'ROW_FIELD_NOT_SINFO'
        return out
    m = POINTER_RX.match(str(src.get('json_pointer') or ''))
    if not m:
        out['rejection'] = 'ROW_POINTER_NOT_BOSSPATTERN'
        return out
    p_index = int(m.group(1))
    gates['parent_pattern_index'] = p_index
    # D4a 句面机制
    form, det = classify_clause(row.get('japanese'))
    gates['clause'] = {'form': form, **det}
    if form is None:
        out['rejection'] = det.get('reason') or 'MECHANISM_NOT_MATCHED'
        return out
    # D3 父链一致（charainfo 指针 ↔ 行来源下标）
    chara = tab['chara'].get(cid)
    if chara is None:
        out['rejection'] = 'CHARAINFO_RECORD_MISSING'
        return out
    pid = chara.get(ref)
    gates['charainfo'] = {'cid': cid, 'pointer': 'charainfo.' + ref, 'pattern_id': pid}
    if not pid:
        out['rejection'] = 'PATTERN_POINTER_MISSING'
        return out
    hits = tab['patterns'].get(pid) or []
    if len(hits) != 1:
        out['rejection'] = 'BOSSPATTERN_NOT_UNIQUE(%d)' % len(hits)
        return out
    pat_index, pattern = hits[0]
    gates['pattern'] = {'pattern_id': pid, 'index': pat_index,
                        'index_matches_row_pointer': pat_index == p_index,
                        'pointer': '/bossinfo/bosspattern/%d' % pat_index}
    if pat_index != p_index:
        out['rejection'] = 'PARENT_POINTER_MISMATCH'
        out['detail'] = {'row_pointer_index': p_index, 'charainfo_pattern_index': pat_index}
        return out
    sinfo = str(pattern.get('sinfo') or '')
    if not sinfo:
        out['rejection'] = 'PATTERN_SINFO_MISSING'
        return out
    body = str(row.get('japanese') or '')
    occurrences = sinfo.count(body)
    gates['span'] = {'occurrences': occurrences,
                     'span': [sinfo.find(body), sinfo.find(body) + len(body)]
                     if occurrences == 1 else None,
                     'sinfo': sinfo}
    if occurrences != 1:
        out['rejection'] = ('ROW_BODY_NOT_IN_PATTERN' if occurrences == 0
                            else 'ROW_BODY_NOT_UNIQUE_IN_PATTERN')
        return out
    # D4b 档位内机制唯一：同一 reference_field 恰 1 行满足冲刺重复机制
    siblings = []
    if isinstance(rows, dict):
        for other in rows.values():
            if str(other.get('reference_field') or '') != ref:
                continue
            oform, _o = classify_clause(other.get('japanese'))
            if oform == 'DASH_REPEAT':
                siblings.append(other.get('row_id'))
    gates['mechanism_rows_in_pattern'] = siblings
    if len(siblings) != 1 or siblings[0] != rid:
        out['rejection'] = 'MECHANISM_CLAUSE_NOT_UNIQUE'
        return out
    # 链
    slots = []
    for slot in range(7):
        sid = pattern.get('skillid%d' % slot)
        if sid:
            slots.append((slot, sid))
    if [s for s, _ in slots] != list(range(len(slots))):
        out['rejection'] = 'SLOT_NOT_CONTIGUOUS'
        return out
    children = []
    for slot, sid in slots:
        sh = tab['skills'].get(sid) or []
        if len(sh) != 1:
            out['rejection'] = 'SKILL_NOT_UNIQUE(%s)' % sid
            return out
        k_index, rec = sh[0]
        children.append({'slot': slot, 'slot_name': 'skillid%d' % slot, 'skillid': sid,
                         'index': k_index, 'type': rec.get('skillid0'), 'record': rec,
                         'params': {k: v for k, v in rec.items()
                                    if k.startswith('skillparam')}})
    gates['chain'] = [{'slot': c['slot'], 'slot_name': c['slot_name'],
                       'skillid': c['skillid'], 'index': c['index'], 'type': c['type'],
                       'params': c['params']} for c in children]
    # D5 伤害族内载体唯一
    family = table_damage_types()
    competitors = [c for c in children if c.get('type') in family]
    gates['damage_family_types'] = sorted(family)
    gates['damage_family_carriers'] = [{'skillid': c['skillid'], 'type': c['type'],
                                        'slot': c['slot']} for c in competitors]
    non_competitors = []
    import rules as R
    for c in children:
        if c.get('type') in family:
            continue
        rule = R.rule_for(TABLE, c.get('type'), FIELD)
        non_competitors.append({
            'slot': c['slot'], 'slot_name': c['slot_name'], 'record_id': c['skillid'],
            'type': c.get('type'),
            'same_field_rule_key': None if rule is None else
            'bossskill|%s|%s' % (c.get('type'), FIELD),
            'reason': ('NO_CONFIRMED_RULE_KEY' if rule is None
                       else 'CONFIRMED_RULE_OUTSIDE_DAMAGE_FAMILY')})
    gates['non_competitors'] = non_competitors
    if not competitors:
        out['rejection'] = 'NO_DAMAGE_FAMILY_CARRIER'
        return out
    if len(competitors) != 1:
        out['rejection'] = 'MULTIPLE_DAMAGE_CARRIERS'
        out['detail'] = {'carriers': gates['damage_family_carriers']}
        return out
    carrier = competitors[0]
    if carrier.get('type') != CARRIER_TYPE:
        out['rejection'] = 'DAMAGE_CARRIER_NOT_%d' % CARRIER_TYPE
        out['detail'] = {'type': carrier.get('type'), 'record_id': carrier['skillid']}
        return out
    # D6 槽位与取值
    view = _param_view(carrier['record'], PARAM)
    gates['param'] = {PARAM: view}
    if view['state'] != 'FINITE':
        out['rejection'] = 'PARAM_%s_%s' % (PARAM.upper(), view['state'])
        out['detail'] = {PARAM: view['raw']}
        return out
    raw = view['raw']
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        # 数字字符串等「可 float 化但非数值类型」的原值不得当成数值写入答案
        out['rejection'] = 'PARAM_%s_NOT_NUMERIC' % PARAM.upper()
        out['detail'] = {PARAM: raw, 'type': type(raw).__name__}
        return out
    if float(raw) <= 0:
        out['rejection'] = 'PARAM_%s_NON_POSITIVE' % PARAM.upper()
        out['detail'] = {PARAM: raw}
        return out
    rule = R.rule_for(TABLE, CARRIER_TYPE, FIELD)
    if rule is None:
        out['rejection'] = 'RULE_MISSING'
        return out
    meaning = str(rule.get('meaning_zh') or '')
    missing_mech = [w for w in RULE_MECH_WORDS if w not in meaning]
    gates['rule'] = {'rule_key': 'bossskill|%d|%s' % (CARRIER_TYPE, FIELD),
                     'meaning_zh': meaning, 'status': rule.get('status'),
                     'conversion': rule.get('conversion'),
                     'mechanism_words_missing': missing_mech}
    if missing_mech:
        out['rejection'] = 'RULE_MECHANISM_MISMATCH'
        out['detail'] = {'missing': missing_mech}
        return out
    if not str(rule.get('status') or '').startswith('已确认'):
        out['rejection'] = 'RULE_NOT_CONFIRMED'
        out['detail'] = {'status': rule.get('status')}
        return out
    # D7 幂等
    rule_key = 'bossskill|%d|%s' % (CARRIER_TYPE, FIELD)
    existing = [a for a in row.get('answers') or [] if a.get('rule_key') == rule_key]
    gates['existing_same_rule_key'] = [
        {'rule_key': a.get('rule_key'), 'record_id': a.get('record_id'),
         'raw_value': a.get('raw_value'), 'field_path': a.get('field_path'),
         'table': a.get('table'), 'layer': a.get('layer')} for a in existing]
    same = [a for a in existing
            if a.get('record_id') == carrier['skillid'] and a.get('raw_value') == raw]
    if same:
        out['rejection'] = 'ALREADY_PRESENT_SAME'
        return out
    if existing:
        out['rejection'] = 'ALREADY_ANSWERED'
        out['detail'] = {'dedup': ('SAME_VALUE_DIFF_RECORD_EXISTING'
                                   if [a for a in existing if a.get('raw_value') == raw]
                                   else 'CONFLICT_EXISTING_VALUE'),
                         'existing': gates['existing_same_rule_key'],
                         'selected': {'record_id': carrier['skillid'], 'raw_value': raw}}
        return out
    # 披露：原文回数与链内其余槽位原值（只登记，不换算）
    gates['disclosure'] = {
        'literal_hits_in_text': det.get('literal_hits'),
        'skillparam4': carrier['params'].get('skillparam4'),
        'skillparam4_present': 'skillparam4' in carrier['params'],
        'policy': ('原文「N回」只作原文披露；不用 skillparam4 反推次数；'
                   '不写总伤害、最终 HP、实际命中次数与间隔'),
        'other_params': {k: v for k, v in carrier['params'].items() if k != PARAM},
    }
    out.update(accepted=True, rejection=None, pattern=pattern, pattern_index=pat_index,
               pattern_id=pid, carrier=carrier, children=children, params={PARAM: raw},
               rule_key=rule_key, rule=rule, clause=det)
    return out


# ---------------------------------------------------------------- 镜像行判定

def evaluate_mirror(data, cid, row, rows=None, tab=None):
    """skilltext 镜像行判定（不写入）：只复用同卡 pattern0 直接基档的答案。

    守卫 M1–M4 见模块头注：行身份／同层父记录／正文唯一机制／同卡同文基档（基档须经
    D1–D6 完整结构判定通过）。返回结构与 :func:`evaluate` 兼容，另加
    ``kind='MIRROR'``、``baseline``（基档判定结果）与 ``mirror_binding``。
    """
    rid = row.get('row_id')
    out = {'row_id': rid, 'cid': cid, 'module': MODULE_VERSION, 'kind': 'MIRROR',
           'accepted': False, 'rejection': None, 'gates': {}, 'detail': None}
    if cid in ZERO_TOUCH_CIDS:
        out['rejection'] = 'ZERO_TOUCH_CID'
        return out
    # M1 行身份
    ref = str(row.get('reference_field') or '')
    if row.get('group') != 'special_move':
        out['rejection'] = 'NOT_SPECIAL_MOVE_ROW'
        return out
    if ref != MIRROR_REF:
        out['rejection'] = 'NOT_SKILLTEXT_MIRROR_ROW'
        out['detail'] = {'reference_field': ref,
                         'note': '只有卡面 skilltext 文本行可走镜像；直接行走 evaluate'}
        return out
    tab = tab or tables(data)
    gates = out['gates']
    gates['row'] = {'row_id': rid, 'cid': cid, 'group': row.get('group'),
                    'reference_field': ref, 'japanese': row.get('japanese'),
                    'layer': (row.get('source') or {}).get('layer')}
    # M2 同层父记录（charainfo 卡面文本）
    src = row.get('source') or {}
    gates['row_source'] = {k: src.get(k) for k in
                           ('source_key', 'layer', 'field', 'json_pointer', 'record_key')}
    if src.get('layer') != 'CACHE' or src.get('source_key') != MIRROR_SOURCE_KEY:
        out['rejection'] = 'MIRROR_ROW_LAYER_NOT_CACHE'
        return out
    if str(src.get('field') or '') != MIRROR_FIELD:
        out['rejection'] = 'MIRROR_ROW_FIELD_NOT_SKILLTEXT'
        return out
    m = MIRROR_POINTER_RX.match(str(src.get('json_pointer') or ''))
    if not m:
        out['rejection'] = 'MIRROR_ROW_POINTER_NOT_CHARAINFO'
        return out
    c_index = int(m.group(1))
    chara_list = tab.get('chara_list') or []
    if not 0 <= c_index < len(chara_list):
        out['rejection'] = 'MIRROR_CHARAINFO_INDEX_OUT_OF_RANGE'
        out['detail'] = {'index': c_index, 'len': len(chara_list)}
        return out
    crec = chara_list[c_index]
    gates['charainfo'] = {'pointer': '/charainfo/%d' % c_index, 'index': c_index,
                          'record_cid': crec.get('cid'),
                          'field': MIRROR_FIELD}
    if crec.get('cid') != cid:
        out['rejection'] = 'MIRROR_PARENT_CID_MISMATCH'
        out['detail'] = {'pointer': '/charainfo/%d' % c_index,
                         'record_cid': crec.get('cid'), 'cid': cid,
                         'note': '镜像行父记录必须是本卡自己的 charainfo 记录，不借跨卡卡面文本'}
        return out
    if tab['chara'].get(cid) != crec:
        # 同一 cid 的 charainfo 记录不唯一（或下标与 cid 索引不一致）→ 父链不唯一
        out['rejection'] = 'MIRROR_CHARAINFO_RECORD_MISMATCH'
        return out
    # M3 正文：卡面 skilltext 内逐字唯一 + 机制词
    body = str(row.get('japanese') or '')
    if not body:
        out['rejection'] = 'MIRROR_TEXT_EMPTY'
        return out
    skilltext = str(crec.get('skilltext') or '')
    if not skilltext:
        out['rejection'] = 'MIRROR_SKILLTEXT_MISSING'
        return out
    occurrences = skilltext.count(body)
    gates['span'] = {'occurrences': occurrences,
                     'span': [skilltext.find(body), skilltext.find(body) + len(body)]
                     if occurrences == 1 else None}
    if occurrences != 1:
        out['rejection'] = ('MIRROR_TEXT_NOT_IN_CHARAINFO' if occurrences == 0
                            else 'MIRROR_TEXT_NOT_UNIQUE_IN_CHARAINFO')
        return out
    form, det = classify_clause(body)
    gates['clause'] = {'form': form, **det}
    if form is None:
        out['rejection'] = det.get('reason') or 'MECHANISM_NOT_MATCHED'
        return out
    # 同族镜像唯一：同一 reference_field 内恰 1 行满足冲刺重复机制
    siblings = []
    for other in (rows or {}).values():
        if str(other.get('reference_field') or '') != ref:
            continue
        oform, _o = classify_clause(other.get('japanese'))
        if oform == 'DASH_REPEAT':
            siblings.append(other.get('row_id'))
    gates['mechanism_rows_in_skilltext'] = siblings
    if len(siblings) != 1 or siblings[0] != rid:
        out['rejection'] = 'MIRROR_MECHANISM_CLAUSE_NOT_UNIQUE'
        return out
    # M4 同卡基档：本卡 pattern0 直接行中**正文逐字相同**的那一行（同档按子句拆成多行，
    # 只有命中同一句的行才是基档），且该基档结构判定通过（忽略其既有答案）
    base_rows = [r for r in (rows or {}).values()
                 if str(r.get('reference_field') or '') == MIRROR_BASELINE_REF]
    gates['baseline_candidates'] = [r.get('row_id') for r in base_rows]
    if not base_rows:
        out['rejection'] = 'MIRROR_NO_SAME_CARD_BASELINE'
        return out
    same_text_rows = [r for r in base_rows
                      if str(r.get('japanese') or '') == body]
    gates['baseline_same_text'] = [r.get('row_id') for r in same_text_rows]
    if not same_text_rows:
        out['rejection'] = 'MIRROR_TEXT_DIFFERS_FROM_BASELINE'
        out['detail'] = {'mirror_text': body,
                         'baseline_texts': sorted({str(r.get('japanese') or '')
                                                   for r in base_rows})}
        return out
    if len(same_text_rows) != 1:
        out['rejection'] = 'MIRROR_BASELINE_NOT_UNIQUE(%d)' % len(same_text_rows)
        out['detail'] = {'baseline_rows': gates['baseline_same_text']}
        return out
    base_row = same_text_rows[0]
    gates['baseline'] = {'row_id': base_row.get('row_id'),
                         'reference_field': MIRROR_BASELINE_REF,
                         'same_text': True}
    base_probe = copy.deepcopy(base_row)
    base_probe['answers'] = []          # 基档写入状态不影响结构判定（幂等）
    res_b = evaluate(data, cid, base_probe, rows=rows, tab=tab)
    gates['baseline_result'] = {'accepted': res_b['accepted'],
                                'rejection': res_b['rejection'],
                                'detail': res_b.get('detail')}
    if not res_b['accepted']:
        out['rejection'] = 'MIRROR_BASELINE_NOT_ACCEPTED'
        out['detail'] = {'baseline_row_id': base_row.get('row_id'),
                         'baseline_rejection': res_b['rejection'],
                         'note': ('镜像只复用同卡 pattern0 直接基档已成立的答案；'
                                  '基档结构不成立时不用其他档位或跨卡数值替代')}
        return out
    carrier, raw = res_b['carrier'], res_b['params'][PARAM]
    binding = {'rule_key': res_b['rule_key'], 'table': TABLE,
               'record_id': carrier['skillid'], 'record_index': carrier['index'],
               'raw_value': raw, 'effective_float32': f32(raw),
               'layer': 'CACHE', 'field_path': FIELD,
               'carrier_slot': carrier['slot'], 'carrier_type': carrier['type'],
               'pattern_id': res_b['pattern_id'],
               'pattern_pointer': '/bossinfo/bosspattern/%d' % res_b['pattern_index'],
               'baseline_row_id': base_row.get('row_id')}
    gates['mirror_binding'] = binding
    # M5 幂等（同记录同值同层才算已存在）
    rule_key = res_b['rule_key']
    existing = [a for a in row.get('answers') or [] if a.get('rule_key') == rule_key]
    gates['existing_same_rule_key'] = [
        {'rule_key': a.get('rule_key'), 'record_id': a.get('record_id'),
         'raw_value': a.get('raw_value'), 'field_path': a.get('field_path'),
         'table': a.get('table'), 'layer': a.get('layer')} for a in existing]
    same = [a for a in existing
            if a.get('record_id') == carrier['skillid'] and a.get('raw_value') == raw
            and (a.get('layer') or 'CACHE') == 'CACHE'
            and (a.get('field_path') or FIELD) == FIELD]
    if same:
        out['rejection'] = 'ALREADY_PRESENT_SAME'
        return out
    if existing:
        out['rejection'] = 'ALREADY_ANSWERED'
        out['detail'] = {'dedup': ('SAME_VALUE_DIFF_RECORD_EXISTING'
                                   if [a for a in existing if a.get('raw_value') == raw]
                                   else 'CONFLICT_EXISTING_VALUE'),
                         'existing': gates['existing_same_rule_key'],
                         'selected': {'record_id': carrier['skillid'], 'raw_value': raw}}
        return out
    out.update(accepted=True, rejection=None,
               baseline_row=base_row, baseline=res_b,
               baseline_row_id=base_row.get('row_id'),
               carrier=carrier, params={PARAM: raw}, rule_key=rule_key,
               rule=res_b['rule'], clause=det,
               mirror_index=c_index, mirror_charainfo=crec,
               mirror_span=gates['span']['span'],
               mirror_binding=binding)
    return out


# ---------------------------------------------------------------- 答案与 marker

def _source(carrier, pattern_index, cid):
    pointer = '/bossinfo/bossskill/%d' % carrier['index']
    return {
        'table': TABLE, 'record_id': carrier['skillid'], 'layer': 'CACHE',
        'field_path': FIELD,
        'source_key': 'CACHE/bossinfo.data5.json.raw',
        'original_file': BASE + '/bossinfo.data5.json.raw',
        'json_pointer': pointer,
        'field': FIELD,
        'field_json_pointer': pointer + FIELD,
        'record_key': 'CACHE/bossinfo.data5.json.raw#%s' % pointer,
        'source_resolution': EXACT,
        'note': ('按解码 JSON 的 bossskill.skillid 全表唯一命中；经本行父记录 '
                 '/bossinfo/bosspattern/%d（charainfo.%s → patternid）链内唯一伤害族载体 type%d 定源'
                 % (pattern_index, 'patternN', CARRIER_TYPE)),
    }


def _marker(res, cid):
    carrier = res['carrier']
    gates = res['gates']
    return {
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'module': MODULE_VERSION,
        'candidate_only': CANDIDATE_ONLY,
        'cid': cid,
        'row_id': res['row_id'],
        'reference_field': (gates.get('row') or {}).get('reference_field'),
        'rule_key': res['rule_key'],
        'table': TABLE,
        'record_id': carrier['skillid'],
        'record_index': carrier['index'],
        'layer': 'CACHE',
        'field_path': FIELD,
        'raw_value': res['params'][PARAM],
        'effective_float32': f32(res['params'][PARAM]),
        'parent_chain': {
            'pattern_pointer': '/bossinfo/bosspattern/%d' % res['pattern_index'],
            'pattern_id': res['pattern_id'],
            'chain': gates.get('chain'),
            'carrier_slot': carrier['slot'],
            'carrier_slot_name': carrier['slot_name'],
            'carrier_type': carrier['type'],
            'field': FIELD,
        },
        'non_competitors': gates.get('non_competitors'),
        'damage_family_carriers': gates.get('damage_family_carriers'),
        'clause': gates.get('clause'),
        'disclosure': gates.get('disclosure'),
        'admission': ('DIRECT_ROW_DASH_REPEAT（本行＝patternN 直接行；本行父记录链内'
                      '伤害族载体恰 1 条且为 type114；skillparam1 有限正值；'
                      '规则族语义含「冲刺」「重复」）'),
        'association': '推断',
        'not_written': ('总伤害、最终 HP、实际命中次数与间隔；原文「N回」不换算；'
                        '「弾き飛ばす／元の位置に戻る」等子句未解析'),
    }


def build_answers(data, cid, row, res):
    """答案对象（复用 rules.answer_for 的换算与规则字段；不新增公式）。"""
    import rules as R
    carrier, raw = res['carrier'], res['params'][PARAM]
    converted = R.answer_for(TABLE, CARRIER_TYPE, FIELD, raw,
                             carrier['record'], source_layer='CACHE')
    if converted is None:
        return None
    rule = res['rule'] or {}
    num = num_text(raw)
    eff = f32(raw)
    hits = (res['gates'].get('clause') or {}).get('literal_hits')
    p4 = (res['gates'].get('disclosure') or {}).get('skillparam4')
    value = (
        '冲刺重复攻击的单次伤害输入倍率：技能基础攻击 B 的 %s 倍（原值 %s，float32 %r）。'
        '伤害输入 = floor/clamp(float32(B × %s))，B = getBasicSkillAttack(true) 已含 Chain，'
        '不再重复乘 Chain。对象：对敌（句面「ダッシュ範囲上にいる全ての敵」，敌方目标由处理器选出，'
        '选择规则未复查）。原文的「%s回」只作原文披露，不用 skillparam4（本记录原值 %s）反推次数；'
        '不写总伤害、最终 HP、实际命中次数与间隔；「弾き飛ばす／元の位置に戻る」等子句仍未解析。'
        % (num, num, eff, num, hits, p4))
    marker = _marker(res, cid)
    answer = {
        'value': value,
        'quantity_kind': converted.get('quantity_kind'),
        'unit': converted.get('unit'),
        'value_text': converted.get('value_text'),
        'raw_value': raw,
        'effective_float32': eff,
        'quantitative': True,
        'numeric_source': 'rules.json 已确认局部公式（type114 skillparam1→伤害输入）＋本行执行链实际记录',
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'evidence_scope': 'BY_TYPE_EXTRAPOLATED',
        'answer_status': converted.get('answer_status') or 'CONFIRMED_FORMULA_ONLY',
        'rule_key': res['rule_key'],
        'table': TABLE,
        'record_id': carrier['skillid'],
        'layer': 'CACHE',
        'field_path': FIELD,
        'source': _source(carrier, res['pattern_index'], cid),
        'rule_status': rule.get('status'),
        'conversion': rule.get('conversion'),
        'base_definition': rule.get('base_definition'),
        'conditions': rule.get('applicability') or rule.get('conditions'),
        'rule_limits': rule.get('limits'),
        'condition_label': ('本卡 %s 档（pattern %s）生效时'
                            % (marker.get('reference_field'), res['pattern_id'])),
        'target': '敌（句面「ダッシュ範囲上にいる全ての敵」；rules.target 为处理器选出目标）',
        'binding': {'c11_p1_t114_binding': marker},
        'context': '直接描述行（冲刺重复攻击段）',
        'note': ('规则已确认的局部伤害公式，绑定到本行父记录链内唯一 type114 载体；'
                 '句面→槽位归属为推断；非最终扣血，不做实机验证。'),
        'evidence': [
            'docs/tasks/20261031-c11-p1-t114-direct.md',
            'output/character_skills/profiles/rules.json#bossskill|114|/skillparam1',
            'output/character_skills/c11_p1_t114_20261031/candidate/README.md',
        ],
    }
    return [answer]


def _mirror_marker(res_m):
    """镜像 marker：父链与不竞争披露取自**同卡 pattern0 直接基档**，并显式登记同值关系。"""
    res_b = res_m['baseline']
    base = _marker(res_b, res_m['cid'])
    binding = res_m['mirror_binding']
    return {
        'scope': MIRROR_SCOPE,
        'structure_scope': MIRROR_STRUCTURE_SCOPE,
        'module': MODULE_VERSION,
        'candidate_only': CANDIDATE_ONLY,
        'kind': 'SKILLTEXT_SAME_CARD_MIRROR',
        'cid': res_m['cid'],
        'row_id': res_m['row_id'],
        'reference_field': MIRROR_REF,
        'rule_key': res_m['rule_key'],
        'table': TABLE,
        'record_id': binding['record_id'],
        'record_index': binding['record_index'],
        'layer': 'CACHE',
        'field_path': FIELD,
        'raw_value': binding['raw_value'],
        'effective_float32': binding['effective_float32'],
        'mirror_basis': {
            'kind': 'SAME_CARD_SAME_RECORD_SAME_RAW_SAME_LAYER',
            'baseline_row_id': res_m.get('baseline_row_id'),
            'baseline_reference_field': MIRROR_BASELINE_REF,
            'baseline_rule_key': binding['rule_key'],
            'baseline_record_id': binding['record_id'],
            'baseline_raw_value': binding['raw_value'],
            'baseline_layer': 'CACHE',
            'same_card': True,
            'same_text': True,
            'same_record': True,
            'same_raw_value': True,
            'same_rule_key': True,
            'same_layer': True,
            'not_used': ['其他档位数值（本卡 pattern1 的 1.2／0.8）', '跨卡先例',
                         '原文「N回」换算次数', 'skillparam4 反推次数'],
        },
        'charainfo': {
            'pointer': '/charainfo/%d' % res_m['mirror_index'],
            'index': res_m['mirror_index'],
            'cid': res_m['cid'],
            'field': MIRROR_FIELD,
            'text_span': res_m.get('mirror_span'),
            'occurrences': 1,
            'skilltext_len': len(str(res_m['mirror_charainfo'].get('skilltext') or '')),
        },
        'parent_chain': base.get('parent_chain'),
        'parent_chain_of': '同卡 pattern0 直接基档（skilltext 行自身无执行链）',
        'non_competitors': base.get('non_competitors'),
        'damage_family_carriers': base.get('damage_family_carriers'),
        'clause': res_m['gates'].get('clause'),
        'disclosure': base.get('disclosure'),
        'admission': ('SKILLTEXT_SAME_CARD_MIRROR（本行＝charainfo 卡面 skilltext 文本行；'
                      '正文与同卡 pattern0 直接行逐字相同、在该 skilltext 内唯一；'
                      'charainfo 父记录 cid 一致；基档经 D1–D6 结构判定通过；'
                      '只复用同记录／同原值／同 rule_key／同 CACHE 层）'),
        'association': '推断',
        'not_written': ('总伤害、最终 HP、实际命中次数与间隔；原文「N回」不换算；'
                        '「弾き飛ばす／元の位置に戻る」等子句未解析'),
    }


def build_mirror_answer(data, cid, row, res_m):
    """镜像答案：数值与来源完全复用同卡基档答案，只换 marker／说明与证据档。

    复用 :func:`build_answers`（即 ``rules.answer_for`` 的换算），不新增公式；镜像行自身
    没有执行链，故 ``source.note`` 明确写成「经同卡 pattern0 基档链定源」。
    """
    built = build_answers(data, cid, res_m['baseline_row'], res_m['baseline'])
    if not built:
        return None
    marker = _mirror_marker(res_m)
    out = []
    for answer in built:
        answer = copy.deepcopy(answer)
        source = dict(answer.get('source') or {})
        source['note'] = ('按解码 JSON 的 bossskill.skillid 全表唯一命中；经**同卡 pattern0 '
                          '直接基档**父记录 /bossinfo/bosspattern/%d（charainfo.%s → patternid）'
                          '链内唯一伤害族载体 type%d 定源；本 skilltext 行自身无执行链，'
                          '只复用同卡同文基档的同记录／同原值'
                          % (res_m['baseline']['pattern_index'], MIRROR_BASELINE_REF,
                             CARRIER_TYPE))
        answer['source'] = source
        answer['binding'] = {'c11_p1_t114_binding': marker}
        answer['mirror_basis'] = {
            'kind': 'SAME_CARD_SAME_RECORD_SAME_RAW_SAME_LAYER',
            'baseline_row_id': res_m.get('baseline_row_id'),
            'baseline_reference_field': MIRROR_BASELINE_REF,
            'record_id': answer['record_id'],
            'raw_value': answer['raw_value'],
            'layer': 'CACHE',
            'field_path': FIELD,
        }
        answer['condition_label'] = ('本卡卡面 skilltext（与 %s 档同文）生效时'
                                    % res_m['baseline']['pattern_id'])
        answer['context'] = 'skilltext 卡面文本行（同卡 pattern0 直接行的同文镜像）'
        answer['numeric_source'] = ('rules.json 已确认局部公式（type114 skillparam1→伤害输入）'
                                    '＋同卡 pattern0 基档执行链实际记录')
        answer['note'] = ('与同卡 pattern0 直接行同文、同记录、同原值、同 CACHE 层的 skilltext '
                          '镜像；不新增公式、不借其他档位或跨卡数值；非最终扣血，不做实机验证。')
        answer['evidence'] = [
            'docs/tasks/20261031-c11-p1-t114-mirror.md',
            'docs/tasks/20261031-c11-p1-t114-direct.md',
            'output/character_skills/profiles/rules.json#bossskill|114|/skillparam1',
            'output/character_skills/c11_p1_t114_20261031/candidate_mirror/README.md',
        ]
        out.append(answer)
    return out


def _append(row, answers, res):
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    existing = {key(a) for a in row.get('answers') or []}
    added = []
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault('answers', []).append(answer)
        existing.add(key(answer))
        added.append(answer)
    if not added:
        return 0
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = ('推断（C11-P1 t114 直接行：本行执行链唯一伤害族载体 type114，'
                            '复用已确认局部伤害公式；归属推断）')
    row['partial'] = True
    row['association_evidence'] = '推断'
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = list(dict.fromkeys(list(scopes) + ['BY_TYPE_EXTRAPOLATED']))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    num = num_text(res['params'][PARAM])
    reasons.append('C11-P1：命中段已按本行执行链 type114 skillparam1=%s 给出单次伤害输入倍率'
                   '（B 的倍数）；原文「N回」次数、实际命中次数与间隔、'
                   '「弾き飛ばす／元の位置に戻る」等子句仍未解析。' % num)
    row['unknown_reasons'] = list(dict.fromkeys(reasons))
    marker = row.setdefault(MARKER_KEY, dict(_marker(res, res['cid'])))
    marker.setdefault('bindings', [])
    marker['bindings'] = list({(b['rule_key'], b['field_path']): b
                               for b in marker['bindings'] + [
                                   {'rule_key': a['rule_key'], 'field_path': a['field_path'],
                                    'record_id': a['record_id'], 'raw_value': a['raw_value']}
                                   for a in added]}.values())
    return len(added)


def _merge_disclosure(row, detail, res):
    marker = row.setdefault(MARKER_KEY, {
        'scope': SCOPE, 'structure_scope': STRUCTURE_SCOPE, 'module': MODULE_VERSION,
        'candidate_only': CANDIDATE_ONLY, 'row_id': row.get('row_id'), 'bindings': []})
    marker.setdefault('disclosures', []).append({
        'dedup': detail.get('dedup'),
        'existing': detail.get('existing'),
        'selected': detail.get('selected'),
        'chain': (res.get('gates') or {}).get('chain'),
        'disclosure': ('本行已有同 rule_key 答案；本批按结构规则选中的记录与原值如 selected，'
                       '不新增答案、不改写既有值，只披露。'),
    })


def _append_mirror(row, answers, res_m):
    """镜像写入（只在结构判定通过后调用）；理由与直接行相同，marker 换成镜像口径。"""
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    existing = {key(a) for a in row.get('answers') or []}
    added = []
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault('answers', []).append(answer)
        existing.add(key(answer))
        added.append(answer)
    if not added:
        return 0
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = ('推断（C11-P1 t114 skilltext 镜像：与同卡 pattern0 直接行同文、'
                            '同记录、同原值、同 CACHE 层，复用已确认局部伤害公式；归属推断）')
    row['partial'] = True
    row['association_evidence'] = '推断'
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = list(dict.fromkeys(list(scopes) + ['BY_TYPE_EXTRAPOLATED']))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    num = num_text(res_m['params'][PARAM])
    reasons.append('C11-P1：本行为卡面 skilltext 的镜像文本，数值引用同卡 pattern0 直接行'
                   '（同记录 %s、原值 %s、CACHE 层）；原文「N回」次数、实际命中次数与间隔、'
                   '「弾き飛ばす／元の位置に戻る」等子句仍未解析。'
                   % (res_m['mirror_binding']['record_id'], num))
    row['unknown_reasons'] = list(dict.fromkeys(reasons))
    marker = row.setdefault(MARKER_KEY, dict(_mirror_marker(res_m)))
    marker.setdefault('bindings', [])
    marker['bindings'] = list({(b['rule_key'], b['field_path']): b
                               for b in marker['bindings'] + [
                                   {'rule_key': a['rule_key'], 'field_path': a['field_path'],
                                    'record_id': a['record_id'], 'raw_value': a['raw_value']}
                                   for a in added]}.values())
    return len(added)


def _merge_mirror_disclosure(row, detail, res_m):
    marker = row.setdefault(MARKER_KEY, {
        'scope': MIRROR_SCOPE, 'structure_scope': MIRROR_STRUCTURE_SCOPE,
        'module': MODULE_VERSION, 'candidate_only': CANDIDATE_ONLY,
        'row_id': row.get('row_id'), 'bindings': []})
    marker.setdefault('disclosures', []).append({
        'dedup': detail.get('dedup'),
        'existing': detail.get('existing'),
        'selected': detail.get('selected'),
        'baseline_row_id': res_m.get('baseline_row_id'),
        'mirror_binding': (res_m.get('gates') or {}).get('mirror_binding'),
        'disclosure': ('本镜像行已有同 rule_key 答案；同卡 pattern0 基档选中的记录与原值如 '
                       'selected，不新增答案、不改写既有值，只披露。'),
    })


# ---------------------------------------------------------------- 正式页消费

def apply_to_groups(data, cid, groups, *, scope_cids=None, mirror_cids=None, tab=None):
    """候选消费入口：为 ``scope_cids`` 内卡片的直接行写 t114 答案（不覆盖既有答案）。

    ``scope_cids`` 缺省 ``None`` → 一行不处理（``NO_SCOPE_DECLARED``）。批次边界必须由
    调用方显式声明；本模块不内置任何卡号/行号/原值常量，避免按结构规则无声扩面。

    ``mirror_cids`` 另行声明 skilltext 镜像批次：缺省 ``None`` → 镜像行一行不触碰（直接
    阶段「镜像新增 0」保持）；声明了的卡片还必须在 ``scope_cids`` 内，否则
    ``MIRROR_REQUIRES_DIRECT_SCOPE``（镜像只复用同卡直接行答案）。
    """
    report = {'scope': SCOPE, 'mirror_scope': MIRROR_SCOPE, 'module': MODULE_VERSION,
              'candidate_only': CANDIDATE_ONLY,
              'cid': cid, 'evaluated': 0, 'answers_added': 0, 'additions': [],
              'markers': [], 'rejections': [], 'skipped_existing': 0, 'marker_only': 0,
              'mirror_evaluated': 0, 'mirror_answers_added': 0, 'mirror_additions': [],
              'mirror_markers': [], 'mirror_rejections': [], 'mirror_skipped_existing': 0,
              'mirror_marker_only': 0,
              'out_of_scope': True}
    if scope_cids is None:
        report['rejections'].append({'reason': 'NO_SCOPE_DECLARED', 'cid': cid})
        return report
    if cid not in set(scope_cids):
        report['rejections'].append({'reason': 'CID_NOT_IN_DECLARED_SCOPE', 'cid': cid})
        return report
    report['out_of_scope'] = False
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append({'reason': 'ZERO_TOUCH_CID', 'cid': cid})
        return report
    mirror_on = (mirror_cids is not None) and (cid in set(mirror_cids))
    rows = {r['row_id']: r for g in groups or [] for s in g.get('skills') or []
            for r in s.get('rows') or []}
    tab = tab or tables(data)
    for rid in sorted(rows):
        row = rows[rid]
        ref = str(row.get('reference_field') or '')
        # 镜像行：只有显式声明 mirror_cids 才处理；缺省跳过，保持直接阶段零新增。
        if row.get('group') == 'special_move' and ref == MIRROR_REF:
            if not mirror_on:
                continue
            report['mirror_evaluated'] += 1
            res_m = evaluate_mirror(data, cid, row, rows=rows, tab=tab)
            if not res_m['accepted']:
                if res_m['rejection'] == 'ALREADY_ANSWERED':
                    _merge_mirror_disclosure(row, res_m.get('detail') or {}, res_m)
                    report['mirror_marker_only'] += 1
                    report['mirror_markers'].append(
                        {'row_id': rid,
                         'dedup': (res_m.get('detail') or {}).get('dedup')})
                elif res_m['rejection'] == 'ALREADY_PRESENT_SAME':
                    report['mirror_skipped_existing'] += 1
                    report['mirror_markers'].append(
                        {'row_id': rid, 'dedup': 'ALREADY_PRESENT_SAME'})
                else:
                    report['mirror_rejections'].append(
                        {'row_id': rid, 'reason': res_m['rejection'],
                         'detail': res_m.get('detail')})
                continue
            answers = build_mirror_answer(data, cid, row, res_m)
            if answers is None:
                report['mirror_rejections'].append({'row_id': rid,
                                                    'reason': 'RULE_UNAVAILABLE'})
                continue
            res_m['cid'] = cid
            added = _append_mirror(row, answers, res_m)
            if added:
                report['mirror_answers_added'] += added
                for answer in answers:
                    report['mirror_additions'].append({
                        'row_id': rid, 'record_id': answer['record_id'],
                        'rule_key': answer['rule_key'], 'field_path': answer['field_path'],
                        'raw_value': answer['raw_value'],
                        'effective_float32': answer['effective_float32'],
                        'baseline_row_id': res_m.get('baseline_row_id')})
            else:
                report['mirror_skipped_existing'] += 1
            continue
        # 规则族外的行（非必杀技组、denju／其他族）直接跳过：范围外零触碰。
        if (row.get('group') != 'special_move'
                or not DIRECT_ROW_RX.match(ref)):
            continue
        report['evaluated'] += 1
        res = evaluate(data, cid, row, rows=rows, tab=tab)
        if not res['accepted']:
            if res['rejection'] == 'ALREADY_ANSWERED':
                _merge_disclosure(row, res.get('detail') or {}, res)
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
        res['cid'] = cid
        added = _append(row, answers, res)
        if added:
            report['answers_added'] += added
            for answer in answers:
                report['additions'].append({
                    'row_id': rid, 'record_id': answer['record_id'],
                    'rule_key': answer['rule_key'], 'field_path': answer['field_path'],
                    'raw_value': answer['raw_value'],
                    'effective_float32': answer['effective_float32']})
        else:
            report['skipped_existing'] += 1
    return report


if __name__ == '__main__':
    raise SystemExit('候选模块只提供 evaluate/evaluate_mirror/build_answers/build_mirror_answer/'
                     'apply_to_groups；自检入口见 '
                     'output/character_skills/c11_p1_t114_20261031/candidate/run_checks.py 与 '
                     'output/character_skills/c11_p1_t114_20261031/candidate_mirror/run_checks.py')
