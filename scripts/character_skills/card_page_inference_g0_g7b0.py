# -*- coding: utf-8 -*-
"""G0-B1（必殺技威力アップ・supporterskill bond 行）＋G7-B0（30110 地形句）合并小批。

任务书：``docs/tasks/20261028-g0-g7b0-batch.md``；只读预检：``docs/tasks/20261026-g0-g1-g7-precheck.md``
＋交付 ``output/character_skills/inference_inventory/g0_g1_g7_precheck_20261026/``；规则引用：
``docs/角色技能完整解读实施方案.md``（含 §1.3）。

本模块**只**处理预检冻结并获批的 32 个效果项（30 行 G0 ＋ 1 行 G7）：

G0-B1（30 项／30 行／30 卡）
    ``skilllist|29|/param0``（ExtraChainRate，必杀请求系数乘数）。载体是 supporterskill
    记录 ``abi0..abi3`` 中的 **106001**（APK：必殺威力UP・特大，ability 29，
    param0=1.149999976158142）。规则 ``conditions`` 声明域＝**{43023615（缓存）, 106001
    （缓存缺失时逐 ID 回退 APK）}**；域门**必须**在本模块内置——``rules.answer_for`` 对
    域外记录（如 43011002）同样返回 ``CONFIRMED_NUMERIC``，不能只靠它拦。

G7-B0（2 项／1 行／1 卡）
    ``skilllist|1008|/param1``（攻击×1.1）、``/param2``（移动×1.1），载体 **43011008**
    （CACHE，ability 1008，param0=20 → 地形 砂浜/船上/海中；p1=p2=1.1、p3=0.9）。
    规则声明域＝当前 v3 CACHE 普通 ability1008 的 37 条记录；APK 侧 1008（30239/30242
    的 102061、30002/30255 的 1017 等）**不扩域**，只登记拒答。

范围判定用预检冻结的**行级注册表**（``G0_ITEMS``／``G7B0_ITEMS``，含逐项 span/clause），
不是泛句式：全库另有 24 行「地形…味方全体…」句带 CACHE 1008 载体（4313/5264/6340/
20115/20523/20829 等），它们不属 G7 候选池（非 YG 族），本批**零触碰**，既不写答案也
不写 hint。同类「必殺技の威力が上がる」句若不在注册表内同样零触碰。

门控（任一不满足即拒答；行内注册表外直接跳过＝零触碰）
--------------------------------------------------------
G1  零触碰：cid 30236（冻结基线卡）整卡不动；30239 按主持 2026-10-28 裁定纳入本批出数，
    但其改动限白名单（本模块只写 f3 行的答案与行级状态字段）。
G2  范围：row_id ∈ 冻结注册表（30 G0 ＋ 1 G7）；不在表内不评价、不写字段。
G3  载体层/表：G0 行 ``table=supporterskill``、layer CACHE，supporterskill 原始主表按
    ``ability_id`` 唯一解析；G7 行 ``table=skilllist``、layer **CACHE**（APK 域外拒答）。
G4  句形点名槽位：G0 行正文含「必殺技の威力」，其「威力」span/子句号须与冻结 span **逐值
    相等**（因此 30334 的「遠距離通常攻撃の威力」不会被误配）；G7 行正文须同时点名
    「攻撃力」「移動速度」，且 span/子句号与冻结值逐值相等。
G5  唯一同层载体与域门：
    * G0：``abi0..abi3`` 中 ability 29 且 skillid ∈ {106001, 43023615} 的候选**恰一个**；
      载体在哪一层就从哪一层取 param0（106001 仅在 APK、43023615 仅在 CACHE），不跨层；
      出现第二候选/双层同 ID/域外 ability29 → 拒答并登记。
    * G7：行记录同层 sub 链内 ability 1008 记录**恰一条**；其 param0 解码地形名须与句面
      地形词**逐词相交**；载体记录须为冻结载体 43011008（ID 级锚定，杜绝 24 行泛匹配）。
G6  形状：载体 param 有限且 >0；G0 param0 ≠ 1（中性不写「上がる」）；G7 p1/p2 ≠ 1。
G7  无既有答案：行内已有同 ``rule_key`` 答案则跳过（不覆盖旧值）。

不映射（主持 2026-10-26 裁决，本批遵守）
----------------------------------------
* 1008 ``param3``（=0.9，受伤量）→ **不出防御力答案**；30110 行的「防御力」效果保持
  unresolved，行级标记 ``defense_slot_pending``。
* 1008/1017/3 的 **APK** 载体不扩域：30239/30242 的「地形が夜の時、味方全体の攻撃力が
  上がる」等只登记（``domain_refusals``），不写页面字段。
* G0 ability 容器（skilllist 侧 1110/1017/27/1086/1059）的必殺威力槽不做。

证据分档：数值换算＝**确认**（规则 status 已确认＋原生点）；「本句↔载体」归属＝**推断**。
答案措辞保持「必杀请求系数×1.15（本项威力 +15%）」，不写成最终伤害 +15%。
"""
from __future__ import annotations

import json
import math
import unicodedata
from pathlib import Path

import rules as R

MODULE_VERSION = 'g0_g7b0_20261028'
SCOPE = 'G0_G7B0_20261028'
TAG = '推断（模板批 G0 必殺威力／G7-B0 地形味方强化）'

# ---------------------------------------------------------------------------
# 冻结范围注册表（预检 frozen_candidates.json 的 32 个 ADMITTED_EVIDENCE_READY 项）
# ---------------------------------------------------------------------------
# G0：row_id → (cid, 冻结 span, 冻结 clause_index, abiN 中的载体 ID)
# span/clause 取自预检冻结项；module 运行时按同法重算并逐值比对。
G0_CARRIER_ID = 106001
G0_CARRIER_IDS = frozenset({106001, 43023615})   # 规则 conditions 声明域（逐条断言）
G0_TABLE = 'supporterskill'
G0_RULE_KEY = 'skilllist|29|/param0'
G0_EFFECT = '威力（词表外）'
G0_PHRASE = '必殺技の威力'
G0_ABI_FIELDS = ('abi0', 'abi1', 'abi2', 'abi3')
G0_ITEMS = {
    '349-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (349, (20, 22), 2),
    '351-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (351, (16, 18), 2),
    '352-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (352, (4, 6), 0),
    '353-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (353, (16, 18), 2),
    '1303-bond-bond-supporterskill_ability_id____cid-lvorder0-f2': (1303, (4, 6), 0),
    '4315-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (4315, (25, 27), 2),
    '7250-bond-bond-supporterskill_ability_id____cid-lvorder0-f2': (7250, (4, 6), 0),
    '30104-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30104, (16, 18), 2),
    '30105-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30105, (25, 27), 2),
    '30110-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30110, (16, 18), 2),
    '30112-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30112, (25, 27), 2),
    '30113-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30113, (4, 6), 0),
    '30207-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30207, (16, 18), 2),
    '30210-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30210, (21, 23), 2),
    '30218-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30218, (20, 22), 2),
    '30223-bond-bond-supporterskill_ability_id____cid-lvorder0-f2': (30223, (4, 6), 0),
    '30239-bond-bond-supporterskill_ability_id____cid-lvorder0-f3': (30239, (4, 6), 0),
    '30248-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30248, (4, 6), 0),
    '30255-bond-bond-supporterskill_ability_id____cid-lvorder0-f0': (30255, (4, 6), 0),
    '30256-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30256, (4, 6), 0),
    '30304-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30304, (16, 18), 2),
    '30308-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30308, (16, 18), 2),
    '30314-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30314, (16, 18), 2),
    '30323-bond-bond-supporterskill_ability_id____cid-lvorder0-f2': (30323, (4, 6), 0),
    '30324-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30324, (4, 6), 0),
    '30329-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30329, (16, 18), 2),
    '30330-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30330, (4, 6), 0),
    '30332-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30332, (4, 6), 0),
    '30334-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30334, (12, 14), 1),
    '30336-bond-bond-supporterskill_ability_id____cid-lvorder0-f1': (30336, (16, 18), 2),
}

G7_TABLE = 'skilllist'
G7_LAYER = 'CACHE'
G7_ABILITY = 1008
G7_CARRIER_ID = 43011008
G7_TERRAIN_SLOT = '/param0'
G7_RULE_KEYS = {'攻撃力': 'skilllist|1008|/param1', '移動速度': 'skilllist|1008|/param2'}
G7_SLOTS = {'攻撃力': '/param1', '移動速度': '/param2'}
G7_PENDING_ATTR = '防御力'          # p3=0.9 是受伤量，主持裁定本批不映射
G7B0_ITEMS = {
    '30110-ability-ability-skillid_2_-lvorder1-f4': dict(
        cid=30110, clause_index=1,
        claims={'攻撃力': (21, 24), '移動速度': (29, 33)}),
}

ZERO_TOUCH_CIDS = frozenset({30236})   # 30239 按主持 2026-10-28 裁定纳批（限白名单字段）

# 域外拒答登记（只登记，不写页面）：G7 ally 载体在 APK 的 1008/1017 记录、G0 ability 侧
# 6 条域外 ability29。均为预检已冻结的拒答集合，本批复核其仍被拒。
DOMAIN_REFUSAL_REGISTRY = dict(
    g7_apk_1008=dict(records=[102061], note='30239/30242 的地形味方句载体 102061 在 APK，'
                                           '规则声明域仅 CACHE 37 条 → 不扩域'),
    g0_ability29_out_of_domain=dict(
        records=[43011002, 43021803, 43025502, 43025703, 43032603, 43032903],
        note='ability29 param0=1.05 但不在 {106001, 43023615} 声明域 → 拒答'),
)

MAX_SUB_DEPTH = 3


# ---------------------------------------------------------------------------
# 规则层
# ---------------------------------------------------------------------------
def _rule(table, ability, field):
    rule = R.rule_for(table, ability, field)
    if not rule:
        raise RuntimeError(f'rules.json 缺键 {table}|{ability}|{field}（本批不改 rules，'
                           f'缺键即拒答，不退回未登记口径）')
    return rule


def answer_core(kind, raw, layer):
    """经规则层换算（显式声明载体层；answer_for 自身不执行域门，域门在本模块）。"""
    if kind == 'g0':
        ans = R.answer_for('skilllist', 29, '/param0', raw, {'ability': 29, 'param0': raw},
                           source_layer=layer)
    else:
        slot = G7_SLOTS[kind]
        ans = R.answer_for('skilllist', G7_ABILITY, slot, raw,
                           {'ability': G7_ABILITY, slot.lstrip('/'): raw}, source_layer=layer)
    if not ans:
        raise RuntimeError(f'answer_for 未返回 {kind} 答案（layer={layer} raw={raw!r}）')
    return ans


# ---------------------------------------------------------------------------
# 原始记录解析（同层，不跨层）
# ---------------------------------------------------------------------------
def _decoded(data):
    return Path(getattr(data, 'decoded', 'output/cache_full_20261015_v3/decoded'))


def support_lookup(data):
    """CACHE supporterskill：ability_id → (index, record)；重复 ability_id 记入 duplicates。"""
    cached = getattr(data, '_g0g7_support', None)
    if cached is not None:
        return cached
    doc = json.loads((_decoded(data) / 'supporterskill.data5.json.raw').read_text(encoding='utf-8'))
    rows = doc['supporterskill']
    by_id, dup = {}, set()
    for i, rec in enumerate(rows):
        aid = rec.get('ability_id')
        if aid in by_id:
            dup.add(aid)
        by_id[aid] = (i, rec)
    cached = dict(by_id=by_id, duplicates=dup)
    setattr(data, '_g0g7_support', cached)
    return cached


def support_record_of_skill(skill):
    """构建路径：supporterskill 原始记录取自 ``skill.record_evidence``（profiles 派生，
    已在 ``card_page_dependencies.data_paths`` 声明），不新增未声明输入文件。"""
    for entry in skill.get('record_evidence') or []:
        if (entry.get('table') == G0_TABLE
                and entry.get('record_id') == skill.get('record_id')
                and isinstance(entry.get('raw_record'), dict)):
            return entry['raw_record'], (entry.get('source') or {})
    return None, {}


def skill_lookup(data, layer):
    table = getattr(data, 'cache_skill' if layer == 'CACHE' else 'apk_skill', None)
    return table or {}


def _resolve_record(data, layer, skillid):
    hit = (skill_lookup(data, layer) or {}).get(skillid)
    return hit[1] if hit else None


def _record_index(data, layer, skillid):
    hit = (skill_lookup(data, layer) or {}).get(skillid)
    return hit[0] if hit else None


def resolve_chain(data, layer, record):
    """同层 sub 递归展开；返回 (chain, missing)。"""
    lookup = skill_lookup(data, layer)
    chain, missing, seen = [record], [], {record.get('skillid')}
    frontier = [(record, 0)]
    while frontier:
        head, depth = frontier.pop(0)
        if depth >= MAX_SUB_DEPTH:
            if head.get('sub'):
                missing.append(dict(parent=head.get('skillid'), reason='DEPTH_LIMIT'))
            continue
        for child in head.get('sub') or []:
            if child in seen:
                continue
            hit = lookup.get(child)
            if hit is None:
                missing.append(dict(parent=head.get('skillid'), reason='MISSING_IN_LAYER',
                                    sub=child))
                continue
            seen.add(child)
            chain.append(hit[1])
            frontier.append((hit[1], depth + 1))
    return chain, missing


def carrier_layers(data, skillid):
    """同一 skillid 在两层是否存在（G0 域门要求「按载体层取值不跨层」的可证性）。"""
    return {layer: _resolve_record(data, layer, skillid) is not None
            for layer in ('APK', 'CACHE')}


# ---------------------------------------------------------------------------
# 句面定位（NFKC，与 effect_ledger 的 span 同口径）
# ---------------------------------------------------------------------------
def nfkc(text):
    return unicodedata.normalize('NFKC', text or '')


def find_power_span(text):
    """「必殺技の威力」中的「威力」span 列表（NFKC 文本坐标）。"""
    t = nfkc(text)
    out, i = [], t.find(G0_PHRASE)
    while i >= 0:
        start = i + len('必殺技の')
        out.append((start, start + 2))
        i = t.find(G0_PHRASE, i + 1)
    return out, t


def clause_index_of(text, span, clauses):
    for i, (_clause, cspan) in enumerate(clauses):
        if cspan[0] <= span[0] and span[1] <= cspan[1]:
            return i
    return None


def find_attr_spans(text, attr):
    t = nfkc(text)
    out, i = [], t.find(attr)
    while i >= 0:
        out.append((i, i + len(attr)))
        i = t.find(attr, i + 1)
    return out


# ---------------------------------------------------------------------------
# 单行门控
# ---------------------------------------------------------------------------
REJECT_ORDER = ('ZERO_TOUCH_CID', 'NOT_IN_SCOPE', 'NOT_SUPPORTER_LAYER', 'SENTENCE_MISMATCH',
                'SPAN_MISMATCH', 'SUPPORT_UNRESOLVED', 'NO_CARRIER', 'CARRIER_NOT_UNIQUE',
                'CARRIER_OUT_OF_DECLARED_DOMAIN', 'CARRIER_LAYER_AMBIGUOUS', 'SHAPE_INVALID',
                'SUB_UNRESOLVED', 'TERRAIN_NOT_INTERSECTING', 'ALREADY_ANSWERED')


def _is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _neutral(value):
    return _is_num(value) and abs(float(value) - 1.0) < 1e-12


def _fmt_num(value):
    return f'{float(value):.6g}'


def _g0_carriers(record):
    """supporterskill abiN 的 (abi 字段名, skillid) 序列（按 abi0..abi3 位置序）。"""
    out = []
    for name in G0_ABI_FIELDS:
        sid = (record or {}).get(name)
        if not isinstance(sid, int):
            continue
        out.append((name, sid))
    return out


def evaluate_g0(cid, table, layer, support_record, row, *, data=None):
    """G0-B1 单行门控。support_record 为 supporterskill 原始记录。"""
    row = row or {}
    frag = row.get('japanese') or ''
    row_id = row.get('row_id')
    gates = {}
    if cid in ZERO_TOUCH_CIDS:
        return dict(status='REJECT', reject='ZERO_TOUCH_CID', gates={'G1': False},
                    answers=[], family='g0')
    gates['G1'] = True
    reg = G0_ITEMS.get(row_id)
    if reg is None or reg[0] != cid:
        return dict(status='REJECT', reject='NOT_IN_SCOPE', gates={'G2': False},
                    answers=[], family='g0')
    gates['G2'] = True
    if not (table == G0_TABLE and layer == 'CACHE' and isinstance(support_record, dict)):
        return dict(status='REJECT', reject='NOT_SUPPORTER_LAYER', gates={'G3': False},
                    answers=[], family='g0')
    gates['G3'] = True
    spans, _t = find_power_span(frag)
    if not spans:
        return dict(status='REJECT', reject='SENTENCE_MISMATCH', gates={'G4': False},
                    answers=[], family='g0')
    exp_span, exp_clause = reg[1], reg[2]
    if len(spans) != 1 or tuple(spans[0]) != tuple(exp_span):
        return dict(status='REJECT', reject='SPAN_MISMATCH', gates={'G4': False},
                    answers=[], family='g0', spans=[list(s) for s in spans],
                    expected=list(exp_span))
    power_span = spans[0]
    gates['G4'] = True
    # 同层载体：记录 abiN 中 ability29 且域内的记录
    cands = []
    for name, sid in _g0_carriers(support_record):
        layers = carrier_layers(data, sid)
        rec = None
        used_layer = None
        for probe in ('CACHE', 'APK'):
            if layers[probe]:
                rec = _resolve_record(data, probe, sid)
                used_layer = probe
                break
        ability = (rec or {}).get('ability')
        if ability != 29:
            cands.append(dict(abi=name, skillid=sid, ability=ability, layers=layers,
                              in_domain=sid in G0_CARRIER_IDS, chosen=None))
            continue
        cands.append(dict(abi=name, skillid=sid, ability=ability, layers=layers,
                          in_domain=sid in G0_CARRIER_IDS, chosen=used_layer))
    in_domain = [c for c in cands if c['in_domain'] and c['chosen']]
    out_of_domain = [c for c in cands if c['ability'] == 29 and not c['in_domain']]
    if out_of_domain:
        return dict(status='REJECT', reject='CARRIER_OUT_OF_DECLARED_DOMAIN', gates={'G5': False},
                    answers=[], family='g0', candidates=cands,
                    domain=sorted(G0_CARRIER_IDS))
    if not in_domain:
        return dict(status='REJECT', reject='NO_CARRIER', gates={'G5': False},
                    answers=[], family='g0', candidates=cands)
    if len(in_domain) != 1:
        return dict(status='REJECT', reject='CARRIER_NOT_UNIQUE', gates={'G5': False},
                    answers=[], family='g0', candidates=cands)
    chosen = in_domain[0]
    layer_of = chosen['chosen']
    if sum(1 for v in chosen['layers'].values() if v) != 1:
        return dict(status='REJECT', reject='CARRIER_LAYER_AMBIGUOUS', gates={'G5': False},
                    answers=[], family='g0', candidates=cands)
    carrier = _resolve_record(data, layer_of, chosen['skillid'])
    raw = (carrier or {}).get('param0')
    if not _is_num(raw) or float(raw) <= 0 or _neutral(raw):
        return dict(status='REJECT', reject='SHAPE_INVALID', gates={'G6': False},
                    answers=[], family='g0', carrier=chosen['skillid'], param0=raw)
    gates['G5'] = gates['G6'] = True
    if any(str(a.get('rule_key')) == G0_RULE_KEY for a in row.get('answers') or []):
        return dict(status='REJECT', reject='ALREADY_ANSWERED', gates={'G7': False},
                    answers=[], family='g0', carrier=chosen['skillid'])
    gates['G7'] = True
    ans = build_answer_g0(cid, row, carrier, layer_of, power_span, exp_clause, data)
    return dict(status='ACCEPT', reject=None, gates=gates, answers=[ans], family='g0',
                carrier=dict(skillid=chosen['skillid'], layer=layer_of, abi=chosen['abi'],
                             param0=raw))


def evaluate_g7(cid, table, layer, record, row, *, data=None):
    """G7-B0 单行门控（skilllist CACHE + 同层唯一 1008 + 地形逐词相交）。"""
    row = row or {}
    frag = row.get('japanese') or ''
    row_id = row.get('row_id')
    gates = {}
    if cid in ZERO_TOUCH_CIDS:
        return dict(status='REJECT', reject='ZERO_TOUCH_CID', gates={'G1': False},
                    answers=[], family='g7')
    gates['G1'] = True
    reg = G7B0_ITEMS.get(row_id)
    if reg is None or reg['cid'] != cid:
        return dict(status='REJECT', reject='NOT_IN_SCOPE', gates={'G2': False},
                    answers=[], family='g7')
    gates['G2'] = True
    if not (table == G7_TABLE and layer == G7_LAYER and isinstance(record, dict)):
        return dict(status='REJECT', reject='CARRIER_OUT_OF_DECLARED_DOMAIN',
                    gates={'G3': False}, answers=[], family='g7', layer=layer)
    gates['G3'] = True
    spans = {attr: find_attr_spans(frag, attr) for attr in G7_SLOTS}
    want = reg['claims']
    for attr, exp in want.items():
        if [tuple(s) for s in spans.get(attr) or []] != [tuple(exp)]:
            return dict(status='REJECT', reject='SPAN_MISMATCH', gates={'G4': False},
                        answers=[], family='g7',
                        spans={k: [list(x) for x in v] for k, v in spans.items()},
                        expected={k: list(v) for k, v in want.items()})
    if '地形' not in frag or '味方全体' not in frag:
        return dict(status='REJECT', reject='SENTENCE_MISMATCH', gates={'G4': False},
                    answers=[], family='g7')
    gates['G4'] = True
    chain, missing = resolve_chain(data, layer, record)
    if missing:
        return dict(status='REJECT', reject='SUB_UNRESOLVED', gates={'G5': False},
                    answers=[], family='g7', missing=missing)
    cands = [c for c in chain if c.get('ability') == G7_ABILITY]
    if not cands:
        return dict(status='REJECT', reject='NO_CARRIER', gates={'G5': False},
                    answers=[], family='g7')
    if len(cands) != 1:
        return dict(status='REJECT', reject='CARRIER_NOT_UNIQUE', gates={'G5': False},
                    answers=[], family='g7', candidates=[c.get('skillid') for c in cands])
    carrier = cands[0]
    if carrier.get('skillid') != G7_CARRIER_ID:
        return dict(status='REJECT', reject='CARRIER_NOT_UNIQUE', gates={'G5': False},
                    answers=[], family='g7', candidates=[carrier.get('skillid')],
                    detail='冻结载体锚定 43011008')
    gates['G5'] = True
    terrain = G7_TERRAIN_SLOT.lstrip('/')
    p0 = carrier.get(terrain)
    if not _is_num(p0):
        return dict(status='REJECT', reject='SHAPE_INVALID', gates={'G6': False},
                    answers=[], family='g7', detail='PARAM0_INVALID', param0=p0)
    decoded = R.decode_terrain(p0)
    names = list(decoded.get('terrain_names_ja') or [])
    tail = nfkc(frag).split('地形', 1)[-1].split('の時')[0].lstrip('がをは：: 　')
    words = [w.strip() for w in tail.split('/') if w.strip()]
    inter = [w for w in words if w in names]
    if not inter:
        return dict(status='REJECT', reject='TERRAIN_NOT_INTERSECTING', gates={'G6': False},
                    answers=[], family='g7', terrain_names=names, sentence_words=words)
    gates['G6'] = True
    values = {attr: carrier.get(G7_SLOTS[attr].lstrip('/')) for attr in G7_SLOTS}
    bad = {k: v for k, v in values.items() if not _is_num(v) or float(v) <= 0 or _neutral(v)}
    if bad:
        return dict(status='REJECT', reject='SHAPE_INVALID', gates={'G6': False},
                    answers=[], family='g7', detail='SLOT_INVALID', values=values)
    answers, skipped = [], []
    for attr in ('攻撃力', '移動速度'):
        rk = G7_RULE_KEYS[attr]
        if any(str(a.get('rule_key')) == rk for a in row.get('answers') or []):
            skipped.append(rk)
            continue
        answers.append(build_answer_g7(cid, row, carrier, layer, attr,
                                      want[attr], reg['clause_index'], data,
                                      terrain=dict(code=decoded.get('code'), names=names,
                                                   sentence_words=words, intersection=inter)))
    if not answers:
        return dict(status='REJECT', reject='ALREADY_ANSWERED', gates={'G7': False},
                    answers=[], family='g7', skipped=skipped)
    gates['G7'] = True
    return dict(status='ACCEPT', reject=None, gates=gates, answers=answers, family='g7',
                carrier=dict(skillid=carrier.get('skillid'), layer=layer,
                             terrain_intersection=inter),
                skipped=skipped or None)


# ---------------------------------------------------------------------------
# 答案构造
# ---------------------------------------------------------------------------
def _source(data, layer, carrier, field):
    index = _record_index(data, layer, carrier.get('skillid'))
    if layer == 'APK':
        source_key, original = 'APK/_mdSkill.json', 'output/base_master/_mdSkill.json'
        record_key = f'APK/_mdSkill.json#/skilllist/{index}'
    else:
        source_key = 'CACHE/skilllist.data5.json.raw'
        original = 'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw'
        record_key = f'CACHE/skilllist.data5.json.raw#/skilllist/{index}'
    return dict(table='skilllist', record_id=carrier.get('skillid'), layer=layer,
                source_key=source_key, record_key=record_key,
                json_pointer=(f'/skilllist/{index}' if index is not None else None),
                original_file=original, field=field, field_path=field,
                raw_value=carrier.get(field.lstrip('/')), namespace='skilllist')


def build_answer_g0(cid, row, carrier, layer, power_span, clause_index, data):
    rule = _rule('skilllist', 29, '/param0')
    raw = carrier.get('param0')
    core = answer_core('g0', raw, layer)
    pct = (float(raw) - 1) * 100
    notes = [
        f'必杀请求系数×{_fmt_num(raw)}：RequestSkill 当前技能请求系数乘本值后进入技能基值；'
        f'≈+{pct:.1f}%（APK 原值 {raw!r} 为 float32，15% 为显示舍入）',
        '本值是**请求系数乘数**，不是最终伤害倍率；玩家装载与完整叠加未证（规则 limits）',
        f'载体 supporterskill abi 位置 106001＝必殺威力UP・特大（ability 29），'
        f'按载体所在层 {layer} 取 param0（CACHE/APK 不跨层）',
        '句面「必殺技の威力」↔ abi 载体＝推断（位置序同 b5 口径）',
    ]
    return dict(
        value=core['value_text'],
        quantity_kind=core.get('quantity_kind'),
        unit=core.get('unit'),
        raw_value=raw,
        field_path='/param0',
        numeric_source=('规则（rules.json#' + G0_RULE_KEY + '，已登记；载体 APK 106001 '
                        'ability29 param0 原生值 1.149999976158142）'),
        numeric_evidence='确认',
        association_evidence='推断',
        evidence_scope=SCOPE,
        rule_key=G0_RULE_KEY,
        rule_registry='output/character_skills/profiles/rules.json#' + G0_RULE_KEY,
        rule_body_status=rule.get('status'),
        rule_status=rule.get('status'),
        conversion=rule.get('conversion'),
        base_definition=rule.get('base_definition'),
        conditions=rule.get('conditions') or rule.get('applicability'),
        rule_limits=rule.get('limits'),
        target=rule.get('target'),
        evidence=list(rule.get('evidence') or []),
        source=_source(data, layer, carrier, '/param0'),
        table='skilllist', record_id=carrier.get('skillid'), layer=layer,
        binding={'g0g7_binding': dict(
            scope=SCOPE, family='g0_bond_power', ability=29, row_id=row.get('row_id'),
            slot='param0', rule_key=G0_RULE_KEY,
            carrier_record_id=carrier.get('skillid'), carrier_layer=layer,
            raw=raw, effect_span=list(power_span), clause_index=clause_index,
            effect_type=G0_EFFECT, domain_declared=sorted(G0_CARRIER_IDS),
            domain_hit=carrier.get('skillid'))},
        note='；'.join(notes),
        quantitative=True)


def build_answer_g7(cid, row, carrier, layer, attr, span, clause_index, data, *, terrain):
    slot = G7_SLOTS[attr]
    rk = G7_RULE_KEYS[attr]
    rule = _rule('skilllist', G7_ABILITY, slot)
    raw = carrier.get(slot.lstrip('/'))
    core = answer_core(attr, raw, layer)
    pct = (float(raw) - 1) * 100
    attr_label = '接受者本项攻击' if attr == '攻撃力' else '移动速度'
    notes = [
        f'地形条件〔编号 {terrain["code"]} → {"/".join(terrain["names"])}〕与句面地形词'
        f'（{"/".join(terrain["sentence_words"])}）逐词相交：{"/".join(terrain["intersection"])}',
        f'{attr_label}×{_fmt_num(raw)}（≈+{pct:.1f}%）；本段不乘 Chain，非最终攻防/移动值',
        ('param2 规则 conditions 仅点名已核 ID 43023606（occurrences=1）；本批按同族 '
         'CACHE ability1008 的 37 条字段存在性与通用乘数路径取 43011008，ID 级外推标推断'
         if attr == '移動速度' else
         'param1 规则声明域＝当前 v3 CACHE ability1008 的 37 条记录，43011008 在域内'),
        '「味方全体」↔ 全体强化接受者＝按规则 target 文本的推断，非逐条实机验证',
    ]
    return dict(
        value=core['value_text'],
        quantity_kind=core.get('quantity_kind'),
        unit=core.get('unit'),
        raw_value=raw,
        field_path=slot,
        numeric_source=('规则（rules.json#' + rk + '，已登记；载体 CACHE 43011008 ability1008 '
                        + slot + ' 原生值 ' + repr(raw) + '）'),
        numeric_evidence='确认',
        association_evidence='推断',
        evidence_scope=SCOPE,
        rule_key=rk,
        rule_registry='output/character_skills/profiles/rules.json#' + rk,
        rule_body_status=rule.get('status'),
        rule_status=rule.get('status'),
        conversion=rule.get('conversion'),
        base_definition=rule.get('base_definition'),
        conditions=rule.get('conditions') or rule.get('applicability'),
        rule_limits=rule.get('limits'),
        target=rule.get('target'),
        evidence=list(rule.get('evidence') or []),
        source=_source(data, layer, carrier, slot),
        table='skilllist', record_id=carrier.get('skillid'), layer=layer,
        binding={'g0g7_binding': dict(
            scope=SCOPE, family='g7b0_terrain', ability=G7_ABILITY, row_id=row.get('row_id'),
            slot=slot.lstrip('/'), rule_key=rk,
            carrier_record_id=carrier.get('skillid'), carrier_layer=layer,
            raw=raw, effect_span=list(span), clause_index=clause_index,
            effect_type=attr, terrain=terrain)},
        note='；'.join(notes),
        quantitative=True)


def _append(row, answer):
    def key(a):
        return (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    if any(key(a) == key(answer) for a in row.get('answers') or []):
        return False
    row.setdefault('answers', []).append(answer)
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = TAG
    row['partial'] = True
    row['evidence_scope'] = list(dict.fromkeys(list(row.get('evidence_scope') or []) + [SCOPE]))
    marker = row.setdefault('inference_g0g7b0', dict(scope=SCOPE, claims=[]))
    b = answer['binding']['g0g7_binding']
    marker['claims'].append(dict(family=b['family'], rule_key=answer['rule_key'],
                                 record_id=answer['record_id'], layer=answer['layer'],
                                 raw_value=answer['raw_value'], effect_span=b['effect_span']))
    return True


def _hint(row, reason, detail=None):
    text = f'{TAG}：{reason}'
    if detail:
        text += f'（{detail}）'
    row['inference_g0g7b0_hint'] = text
    row.setdefault('inference_g0g7b0_meta', dict(scope=SCOPE, reason=reason, detail=detail))
    return text


# ---------------------------------------------------------------------------
# 页面消费
# ---------------------------------------------------------------------------
def apply_to_groups(data, cid, groups):
    """正式页消费：只对冻结注册表的 31 行出数（不覆盖/不删除既有答案）。"""
    report = dict(scope=SCOPE, cid=cid, answers_added=0, additions=[], rejections=[],
                  hints=0, skipped_existing=0, evaluated=0, g0=0, g7b0=0)
    if cid in ZERO_TOUCH_CIDS:
        report['zero_touch'] = True
        return report
    for group in groups or []:
        for skill in group.get('skills') or []:
            table, layer = skill.get('table'), skill.get('layer')
            rows = skill.get('rows') or []
            if not rows:
                continue
            if table == G0_TABLE and layer == 'CACHE':
                support_record, _support_source = support_record_of_skill(skill)
                for row in rows:
                    if row.get('row_id') not in G0_ITEMS:
                        continue
                    report['evaluated'] += 1
                    if support_record is None:
                        report['rejections'].append(dict(
                            row_id=row.get('row_id'), reason='SUPPORT_UNRESOLVED',
                            family='g0', detail='record_evidence 无 supporterskill 原始记录'))
                        continue
                    res = evaluate_g0(cid, table, layer, support_record, row, data=data)
                    _consume(row, res, report, 'g0')
            elif table == G7_TABLE and layer in ('APK', 'CACHE'):
                record = _resolve_record(data, layer, skill.get('record_id'))
                for row in rows:
                    if row.get('row_id') not in G7B0_ITEMS:
                        continue
                    report['evaluated'] += 1
                    res = evaluate_g7(cid, table, layer, record, row, data=data)
                    _consume(row, res, report, 'g7')
    return report


def _consume(row, res, report, family):
    if res['status'] == 'ACCEPT':
        added = 0
        for ans in res['answers']:
            if _append(row, ans):
                added += 1
                b = ans['binding']['g0g7_binding']
                report['additions'].append(dict(
                    row_id=row.get('row_id'), family=b['family'], rule_key=ans['rule_key'],
                    value=ans['value'], raw_value=ans['raw_value'],
                    carrier=ans['record_id'], carrier_layer=ans['layer'],
                    effect_span=b['effect_span']))
        report['answers_added'] += added
        report['g0' if family == 'g0' else 'g7b0'] += added
        row.setdefault('g0g7_gate', dict(res['gates']))
        if res.get('skipped'):
            report['rejections'].append(dict(row_id=row.get('row_id'), reason='PARTIAL',
                                             skipped=res['skipped']))
        return
    if res['reject'] == 'ALREADY_ANSWERED':
        report['skipped_existing'] += 1
        return
    _hint(row, res['reject'], res.get('detail'))
    report['hints'] += 1
    report['rejections'].append(dict(row_id=row.get('row_id'), reason=res['reject'],
                                     family=res.get('family'), detail=res.get('detail')))


# ---------------------------------------------------------------------------
# 只读探针与范围自检
# ---------------------------------------------------------------------------
def probe(data, cid, row_id=None):
    """按页面找本批注册表行，输出原始载体与门控结果（不写页面）。"""
    page = json.loads((Path('output/character_skills/pages') / str(cid) / 'card.json')
                      .read_text(encoding='utf-8'))
    out = dict(cid=cid, rows=[])
    for group in page.get('groups') or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                rid = row.get('row_id')
                if row_id and rid != row_id:
                    continue
                if rid not in G0_ITEMS and rid not in G7B0_ITEMS:
                    continue
                table, layer = skill.get('table'), skill.get('layer')
                entry = dict(row_id=rid, table=table, layer=layer,
                             record_id=skill.get('record_id'), japanese=row.get('japanese'),
                             answers=[a.get('rule_key') for a in row.get('answers') or []])
                if table == G0_TABLE:
                    sup = support_lookup(data)['by_id'].get(skill.get('record_id'))
                    rec = sup[1] if sup else None
                    entry['support'] = {k: (rec or {}).get(k) for k in
                                        ('ability_id', 'ability') + G0_ABI_FIELDS}
                    entry['evidence'] = probe_g0_carrier(data, rec)
                    entry['gate'] = evaluate_g0(cid, table, layer, rec, row, data=data)
                else:
                    rec = _resolve_record(data, layer, skill.get('record_id'))
                    chain, _missing = resolve_chain(data, layer, rec) if rec else ([], [])
                    entry['chain'] = [c.get('skillid') for c in chain]
                    entry['carrier_1008'] = [{k: c.get(k) for k in
                                              ('skillid', 'param0', 'param1', 'param2', 'param3')}
                                             for c in chain if c.get('ability') == G7_ABILITY]
                    entry['gate'] = evaluate_g7(cid, table, layer, rec, row, data=data)
                out['rows'].append(entry)
    return out


def probe_g0_carrier(data, support_record):
    """G0 载体证据：域内候选逐层原值（不读页面、不写页面）。"""
    rows = []
    for name, sid in _g0_carriers(support_record or {}):
        layers = carrier_layers(data, sid)
        recs = {}
        for layer, present in layers.items():
            if present:
                rec = _resolve_record(data, layer, sid)
                recs[layer] = dict(ability=rec.get('ability'), param0=rec.get('param0'),
                                   text=rec.get('text'))
        rows.append(dict(abi=name, skillid=sid, in_domain=sid in G0_CARRIER_IDS,
                         layers=layers, records=recs))
    return rows


def scope_registry():
    return dict(
        scope=SCOPE, module=MODULE_VERSION,
        g0_items={k: dict(cid=v[0], span=list(v[1]), clause_index=v[2]) for k, v in G0_ITEMS.items()},
        g7b0_items={k: dict(cid=v['cid'], clause_index=v['clause_index'],
                            claims={a: list(s) for a, s in v['claims'].items()})
                    for k, v in G7B0_ITEMS.items()},
        counts=dict(g0_rows=len(G0_ITEMS), g7b0_rows=len(G7B0_ITEMS),
                    g0_values=len(G0_ITEMS), g7b0_values=2, total_items=len(G0_ITEMS) + 2),
        domain=dict(g0=sorted(G0_CARRIER_IDS), g7_layer=[G7_LAYER], g7_carrier=[G7_CARRIER_ID],
                    g7_ability=[G7_ABILITY]),
        pending=dict(g7_param3='1008 p3=受伤量（0.9），主持 2026-10-26 裁定本批不映射',
                     g0_ability_side='ability 容器必殺威力槽不做'),
        domain_refusals=DOMAIN_REFUSAL_REGISTRY)


def domain_gate_assertions():
    """域门逐条断言（scratch 调用）：域内出数、域外拒答。"""
    out = []

    class Data:
        def __init__(self):
            self.decoded = Path('output/cache_full_20261015_v3/decoded')
            self.cache_skill = {r['skillid']: (i, r) for i, r in enumerate(
                json.loads((self.decoded / 'skilllist.data5.json.raw')
                           .read_text(encoding='utf-8'))['skilllist'])}
            self.apk_skill = {r['skillid']: (i, r) for i, r in enumerate(
                json.loads(Path('output/base_master/_mdSkill.json')
                           .read_text(encoding='utf-8'))['skilllist'])}

    data = Data()
    for sid, expect_layer, expect_domain in ((106001, 'APK', True), (43023615, 'CACHE', True),
                                             (43011002, 'CACHE', False),
                                             (43021803, None, False)):
        layers = carrier_layers(data, sid)
        rec = _resolve_record(data, expect_layer or 'CACHE', sid)
        ans = None
        if rec is not None:
            try:
                ans = R.answer_for('skilllist', 29, '/param0', rec.get('param0'), rec,
                                   source_layer=expect_layer or 'CACHE')
            except Exception:                                   # noqa: BLE001
                ans = None
        out.append(dict(check='g0_domain', skillid=sid, layers=layers,
                        in_declared_domain=sid in G0_CARRIER_IDS,
                        expect_in_domain=expect_domain,
                        answer_for_returns=(ans or {}).get('answer_status'),
                        module_accepts=(sid in G0_CARRIER_IDS and any(layers.values())),
                        ok=((sid in G0_CARRIER_IDS) == expect_domain)))
    # G7：CACHE 1008 记录在域，APK 1008 记录域外
    for layer, sid, expect_domain in (('CACHE', G7_CARRIER_ID, True),
                                      ('APK', 102061, False)):
        rec = _resolve_record(data, layer, sid)
        out.append(dict(check='g7_domain', layer=layer, skillid=sid,
                        ability=(rec or {}).get('ability'),
                        expect_in_domain=expect_domain,
                        module_accepts=(layer == G7_LAYER and sid == G7_CARRIER_ID),
                        ok=((layer == G7_LAYER and sid == G7_CARRIER_ID) == expect_domain)))
    return out


def _main(argv=None):
    import argparse
    import sys
    ap = argparse.ArgumentParser(description='G0-B1／G7-B0 合并小批：只读探针')
    ap.add_argument('--cid', type=int, action='append', help='卡号（可多次）')
    ap.add_argument('--row-id', help='限定单行')
    ap.add_argument('--scope', action='store_true', help='输出冻结范围注册表')
    ap.add_argument('--domains', action='store_true', help='域门逐条断言')
    args = ap.parse_args(argv)
    if args.scope:
        print(json.dumps(scope_registry(), ensure_ascii=False, indent=1))
        return 0
    if args.domains:
        print(json.dumps(domain_gate_assertions(), ensure_ascii=False, indent=1))
        return 0
    if not args.cid:
        ap.print_help()
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    class Data:
        def __init__(self):
            self.decoded = Path('output/cache_full_20261015_v3/decoded')
            self.cache_skill = {r['skillid']: (i, r) for i, r in enumerate(
                json.loads((self.decoded / 'skilllist.data5.json.raw')
                           .read_text(encoding='utf-8'))['skilllist'])}
            self.apk_skill = {r['skillid']: (i, r) for i, r in enumerate(
                json.loads(Path('output/base_master/_mdSkill.json')
                           .read_text(encoding='utf-8'))['skilllist'])}

    data = Data()
    print(json.dumps([probe(data, cid, args.row_id) for cid in args.cid],
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
