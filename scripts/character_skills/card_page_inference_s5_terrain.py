# -*- coding: utf-8 -*-
"""S5 地形段（type28 击杀マナ：地形附加概率阈值）推断模块。

范围（``docs/tasks/20261026-s5-terrain-batch.md`` §1；
预检 ``output/character_skills/inference_inventory/chain_precheck_20261026/precheck_report.md`` §8/§9.2；
前批 ``output/character_skills/s5_nonterrain_20261026/``）
----------------------------------------------------------------------------
S5 地形段 = 预检/批1 重筛排除的 **15 行 / 15 项**（句面含 ``地形が…`` 或 ``戦場が…``）。
值源 = ``skilllist`` ability 28 记录：

* ``param0/param1/param2`` = DamageType0/2/1 的**基础**阈值（批1 已交付口径，本批只披露）；
* **地形命中时**：DamageType2 另取 ``param4``、type0/1 另取 ``param5`` 作为**附加**阈值，
  与基础相加后与 ``Random.Range(0,1)`` 比较（``output/card_comparison_cid30236/
  mana_chance/README.md`` 与 rules.json 六个 28 键 conversion 同文）；
* ``param6`` = 地形附加概率的**位索引**，掩码 ``1<<param6``；
* ``param3``／``param9`` 语义未登记 → 只登记原值并写未知注记，不解释。

证据档（主持三裁决，沿用批1）
-----------------------------
1. 原文只写「マナを獲得しやすくなる／必ずマナを獲得する」时允许出示字段阈值
   （param4/param5 附加 × param6 掩码位）；**单来源（occurrences=1）、类型级外推、
   不升确认**，答案 ``numeric_evidence=推断``、``answer_status=INFERRED_SINGLE_SOURCE``、
   ``evidence_scope=BY_TYPE_EXTRAPOLATED``；规则证据层为 **CACHE**（记录 43023602 的受控
   原生检查），逐行同时披露本行载体层（CACHE/APK）。
2. ``param6≠4`` **只写掩码位 ``1<<param6``，不写地形名**，不由位索引反推地形名。
   全段只有 30236 的 param6=4（掩码 16＝砂漠，原生已核），而该卡零触碰 → 本批不出现
   任何「掩码＝地形名」断言。句面原文条件按原文引用（``binding.s5_binding.condition_text``），
   不是掩码推导结果。
3. ``param3``／``param9`` 语义未知 → 就地未知注记，不填零、不按参数对称性补解释。

逐行门控（拒绝即不出该行；原因码落盘可数）
--------------------------------------------
T1  零触碰：30236/30239 → ZERO_TOUCH_CID（30236 本段已有基线答案，不覆盖）。
T2  表边界：仅 ``skilllist``；其它表 fail-closed（CHARAINFO_EQUIVALENCE_FAIL_CLOSED）。
T3  句式：必须有地形/战场条件子句（``地形が…の場合/の時``、``戦場が…の場合/の時``）且条件
    **之后**有本行玛那获得主张（しやすくなる／必ず…する／…する）。无地形条件 → NOT_TERRAIN_S5_CLAIM；
    条件后无玛那主张 → NOT_TERRAIN_MANA_CLAIM；一行多地形条件 → MULTI_TERRAIN_CLAIM。
T4  载体串：own → sub（1082 转发）→ 容器；断裂 → CARRIER_CHAIN_BROKEN；
    无 ability28 → NO_TYPE28_CARRIER；≥2 条不同 ability28 → MULTI_CARRIER_AMBIGUOUS
    （不求和、不取最大，同批1 G4）。
T5  掩码：param6 必须存在且为正整数 → 缺失 MASK_MISSING、=0 MASK_ZERO（按批1既有口径
    param6<=0 视为无地形附加掩码，不写 1<<0）、非整数 MASK_NOT_INTEGER、
    越界 MASK_OUT_OF_RANGE（不猜位、不填零）。
T6  附加阈值：param4/param5 必须存在且 >0 → 缺失 ADDON_MISSING、非正 ADDON_OUT_OF_RANGE
    （「获得更容易」与 0 附加矛盾，拒答而不是写 0）。
T7  基础槽：param0/param1/param2 必须都存在 → BASE_SLOT_MISSING（不填零）。
T8  同值时机：「必ず」句要求三伤害类型 基础+附加 **==1.0**；「しやすくなる」句要求
    0 < 基础+附加 ≤ 1.0。不符 → VALUE_TRIGGER_MISMATCH / THRESHOLD_OUT_OF_RANGE。
T9  无既有答案：同 rule_key＋record_id＋field_path 已存在 → ALREADY_ANSWERED（不改旧值）。
T10 单来源不外推：``apply_to_groups`` 只处理 ``TERRAIN_ROWS``（15 行）内的行，范围外不消费。

答案粒度：一句地形条件＋一个玛那获得主张＝一条答案；``binding.fields`` 列
``/param4``、``/param5`` 两处地形附加原值；``field_path`` 取 ``/param4``
（规则 conversion 中「type2取param4」先列；两槽都在 fields 内，不丢值）。
"""
from __future__ import annotations

import json
import math
import re

import card_page_inference_mana_b as MB
import card_page_inference_s5 as BASE

MODULE_VERSION = "s5_terrain_20261026"
SCOPE = "S5_TERRAIN_20261026"
RULE_ID_PREFIX = "skilllist|28|/"
ADMITTED_TABLES = ("skilllist",)
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

# 预检/批1 重筛实测的 15 行（批1 `rescreen_summary.json`.terrain_excluded；本目录 rescreen 复算）
TERRAIN_ROWS = frozenset({
    "20236-ability-ability-skillid_1_-lvorder0-f3",
    "20503-ability-ability-skillid_2_-lvorder1-f9",
    "20523-ability-ability-skillid_2_-lvorder1-f4",
    "20638-ability-ability-skillid_1_-lvorder0-f6",
    "20644-ability-ability-skillid_1_-lvorder0-f2",
    "20702-ability-ability-skillid_1_-lvorder0-f5",
    "20706-ability-ability-skillid_1_-lvorder0-f4",
    "30236-ability-ability-skillid_1_-lvorder0-f4",
    "30242-ability-ability-skillid_1_-lvorder0-f2",
    "5048-ability-ability-skillid_2_-lvorder1-f2",
    "5092-ability-ability-skillid_1_-lvorder0-f1",
    "5300-ability-ability-skillid_1_-lvorder0-f3",
    "6334-ability-ability-skillid_1_-lvorder0-f4",
    "7248-ability-ability-skillid_2_-lvorder1-f5",
    "7546-ability-ability-skillid_2_-lvorder1-f2",
})

ADDON_SLOTS = ("param4", "param5")
BASE_SLOTS = ("param0", "param1", "param2")
# slot → death damageType（rules.json conversion：damageType0/2/1 读取 param0/1/2；
# 即 param0=type0、param1=type2、param2=type1）
ADDON_DAMAGE_TYPE = {"param4": "2", "param5": "0/1"}
BASE_DAMAGE_TYPE = {"param0": "0", "param1": "2", "param2": "1"}
# 附加槽 → 受影响的基础槽（规则 conversion 逐字：type2取param4、type0/1取param5）
#   type2 = param1 → 附加 param4；type0 = param0 / type1 = param2 → 附加 param5
# 独审残留①（2026-10-26）：原实现误写为 param4→param2、param5→param0+param1（type1/type2 互换）；
# 本批 14 行 param4==param5 故数值无影响，但 param4≠param5 的记录会算错，已按 conversion 修正。
ADDON_TARGETS = {"param4": ("param1",), "param5": ("param0", "param2")}

FLAT = str.maketrans("０１２３４５６７８９", "0123456789")
COND_RX = re.compile(r"(?:地形|戦場)が[^、。]{1,40}?(?:の場合|の時|のとき)")
COND_SPLIT_RX = re.compile(r"^(?:地形|戦場)が(.+?)(?:の場合|の時|のとき)$")
MANA_RX = re.compile(r"(さらに)?(必ず)?マナを獲得(しやすくなる|しやすく|する)")
BASE_PROB_RX = re.compile(r"一定確率で[^、。]{0,30}?マナを獲得")
PHRASE_ZH = {"always": "必ず", "relative": "しやすくなる", "plain": "獲得する"}
TOTAL_TOL = 1e-9

PARAM6_UNKNOWN = "param6≠4：只写掩码位 1<<param6，地形名未核（不写地形名、不由位索引反推）"
UNKNOWN_TAIL = [
    "多来源叠加/取最大值未模拟；本答案只给单记录附加阈值",
    "实际击杀资格、装载、地形标志获取（GetBgFlag）与玛那生成未模拟（未做实机验证）",
    "同串其它子句（攻撃力/HP/状態異常/回転速度/クリティカル発生率 等）不在本答案范围",
]
EVIDENCE_BASE = [
    "output/character_skills/profiles/rules.json",
    "output/card_comparison_cid30236/mana_chance/README.md",
    "output/card_comparison_cid30236/mana_chance/native_checks.json",
    "output/card_comparison_cid30236/mana_chance/trace.json",
]


# ---------------------------------------------------------------------------
# 基础工具（复用批1 规范化/数值格式，保持同一口径）
# ---------------------------------------------------------------------------
_norm = BASE._norm
_finite = BASE._finite
_pct = BASE._pct
_raw_txt = BASE._raw_txt


def _int_slot(v):
    """整数化位索引；非有限或非整数返回 None（不猜）。"""
    if not _finite(v):
        return None
    f = float(v)
    if f != math.floor(f):
        return None
    return int(f)


def _mask_text(p6):
    """param6 → 地形掩码（只写位，不写地形名）。"""
    code = _int_slot(p6)
    if code is None:
        return None
    return "%d（1<<%d）" % (1 << code, code)


def totals_by_type(rec):
    """「基础 + 地形附加」逐伤害类型总阈值（纯函数，按 rules.json conversion）。

    conversion 逐字：``damageType0/2/1分别读取param0/1/2`` → type0=param0、type2=param1、
    type1=param2；``type2取param4、type0/1取param5`` → 上述映射由 ``ADDON_TARGETS`` 承载。
    返回 {基础槽: 总和}；任一槽非有限则不产出该项（缺失不填零）。
    """
    out = {}
    for addon in ADDON_SLOTS:
        if not _finite(rec.get(addon)):
            continue
        for b in ADDON_TARGETS[addon]:
            if _finite(rec.get(b)):
                out[b] = float(rec[b]) + float(rec[addon])
    return out


def _totals_in(rec, order):
    """按指定键序输出 totals（仅序列化顺序；字典语义相同）。

    兼容性：页面 `s5_terrain_gate.totals` 与答案内 totals 在修正前均按 BASE_SLOTS
    （param0/param1/param2）序列化；保持该键序可让本批 14 行的页面字节不变。
    """
    t = totals_by_type(rec)
    return {b: t[b] for b in order if b in t}


# ---------------------------------------------------------------------------
# 句式解析
# ---------------------------------------------------------------------------
def classify_terrain(text):
    """解析「地形条件＋玛那获得」句；返回条件/主张/拒答原因。"""
    t = _norm(text)
    out = {"condition": None, "condition_pos": None, "mana_phrase": None, "phrase": None,
           "additive": False, "terrain_list_text": None, "terrain_count": None,
           "base_probability_clause": None, "claims": 0, "rejection": None, "detail": None}
    if not t:
        out["rejection"] = "EMPTY_TEXT"
        return out
    conds = list(COND_RX.finditer(t))
    if not conds:
        out["rejection"] = "NOT_TERRAIN_S5_CLAIM"
        out["detail"] = {"has_mana": "マナ" in t}
        return out
    if len(conds) > 1:
        out["rejection"] = "MULTI_TERRAIN_CLAIM"
        out["detail"] = [m.group(0) for m in conds]
        return out
    cond = conds[0]
    tail = t[cond.end():]
    m = MANA_RX.search(tail)
    if not m:
        out["rejection"] = "NOT_TERRAIN_MANA_CLAIM"
        out["detail"] = {"tail": tail[:60]}
        return out
    # 条件之后只允许一条本行玛那主张（第二条 → 句式超出本批单句口径）
    second = MANA_RX.search(tail[m.end():])
    if second:
        out["rejection"] = "MULTI_TERRAIN_MANA_CLAIM"
        out["detail"] = {"tail": tail[:80]}
        return out
    phrase = "always" if m.group(2) else ("relative" if m.group(3).startswith("しやすく")
                                          else "plain")
    sm = COND_SPLIT_RX.match(cond.group(0))
    list_text = sm.group(1) if sm else None
    terrains = [x for x in (list_text or "").split("/") if x]
    out.update({"condition": cond.group(0), "condition_pos": cond.start(),
                "mana_phrase": m.group(0), "phrase": phrase,
                "additive": bool(m.group(1)),
                "terrain_list_text": list_text, "terrain_count": len(terrains),
                "claims": 1})
    bp = BASE_PROB_RX.search(t[:cond.start()])
    if bp:
        out["base_probability_clause"] = bp.group(0)
    return out


# ---------------------------------------------------------------------------
# 答案
# ---------------------------------------------------------------------------
def _result(table, reference_field, text):
    return {"scope": SCOPE, "table": table, "reference_field": reference_field,
            "text": text, "gates": {}, "accepted": False, "rejection": None,
            "detail": None, "phrase": None, "answers": []}


def _reject(res, code, detail=None):
    res["rejection"] = code
    if detail is not None:
        res["detail"] = detail
    return res


def build_answer(data, table, reference_field, record, text, carrier, cls, cid=None):
    rec = carrier["record"]
    primary = "param4"
    rule_key = RULE_ID_PREFIX + primary
    p6 = _int_slot(rec.get("param6"))
    mask = _mask_text(rec.get("param6"))
    totals = _totals_in(rec, BASE_SLOTS)

    def _total(b):
        return "%s→%s" % (BASE_DAMAGE_TYPE[b], _pct(totals[b]))

    addon_txt = "；".join(
        "伤害类型%s(%s)→%s" % (ADDON_DAMAGE_TYPE[a], a, _pct(rec.get(a)))
        for a in ADDON_SLOTS)
    base_txt = "；".join("伤害类型%s(%s)→%s" % (BASE_DAMAGE_TYPE[b], b, _pct(rec.get(b)))
                         for b in BASE_SLOTS)
    value = ("地形掩码 1<<%d=%d 命中时，击杀玛那判定阈值附加：%s；基础阈值：%s；"
             "命中时总阈值：%s"
             % (p6, 1 << p6, addon_txt, base_txt,
                "、".join(_total(b) for b in BASE_SLOTS)))
    if cls["phrase"] == "always":
        value += "（三伤害类型均为 100%，与原文「必ず」一致）"

    cond = ("地形条件（原文）：「%s」；句面玛那表述（原文）：「%s」；记录掩码位 param6=%d"
            "（1<<%d=%d；地形名未核，不由位索引反推）；命中时把 param4/param5 附加到基础阈值，"
            "判定 Random.Range(0,1) ≤ 基础+附加"
            % (cls["condition"], cls["mana_phrase"], p6, p6, 1 << p6))
    if cls.get("base_probability_clause"):
        cond += "；本行另有击杀基础概率子句（原文「%s」），不在本答案范围" % (
            cls["base_probability_clause"])
    if cls.get("additive"):
        cond += "；原文「さらに」为叠加表述（叠加基准见同记录基础阈值）"

    unknowns = [
        "单来源证据（occurrences=1，规则证据记录 43023602/CACHE）；类型级外推，"
        "未逐卡原生核实，不升确认",
        PARAM6_UNKNOWN,
        "param3=%s 语义未知（规则未登记；原值保留，不解释）" % _raw_txt(rec.get("param3")),
        "param9=%s 语义未知（规则未登记；原值保留，不解释）" % _raw_txt(rec.get("param9")),
    ]
    if (cls.get("terrain_count") or 0) > 1:
        unknowns.append("原文地形句列 %d 个地形，记录仅按 param6 写 1 个位索引；"
                        "多地形↔位索引对应未核（不拆分、不映射、不按位补名）"
                        % cls["terrain_count"])
    for extra in ("param7", "param8"):
        if rec.get(extra) not in (None, 0, 0.0):
            unknowns.append("%s=%s 语义未知（规则未登记；仅登记原值，不并入掩码、不解释）"
                            % (extra, _raw_txt(rec.get(extra))))
    if cls.get("base_probability_clause"):
        unknowns.append("本行同时含击杀基础概率子句（一定確率でマナを獲得）；该子句不在本批"
                        "地形答案范围（本批只答地形附加），仍留未解")
    if cls.get("additive"):
        unknowns.append("原文「さらに」为叠加表述；叠加基准/上限未建模")
    if cls["phrase"] == "relative":
        unknowns.append("原文「マナを獲得しやすくなる」为相对表述；记录给绝对附加阈值，"
                        "相对基准未登记，不按差值解释")
    unknowns.extend(UNKNOWN_TAIL)

    fields = []
    for s in ADDON_SLOTS:
        v = float(rec.get(s))
        fields.append({
            "f": "/" + s,
            "raw": v,
            "value": ("地形命中时伤害类型%s 附加概率阈值 %s（原值 %s；param6=%d，掩码 %s）"
                      % (ADDON_DAMAGE_TYPE[s], _pct(v), _raw_txt(v), p6, mask)),
            "kind": "概率阈值增加量",
            "unit": "概率阈值增加量；派生百分点",
            "status": "INFERRED_SINGLE_SOURCE",
            "evidence_scope": "BY_TYPE_EXTRAPOLATED",
            "rule_key": RULE_ID_PREFIX + s,
            "table": "skilllist",
            "record_id": carrier["record_id"],
            "damage_type": ADDON_DAMAGE_TYPE[s],
            "mask_bit": p6,
        })

    src = MB._carrier_source(data, dict(carrier, slot=primary))
    note_parts = ["单来源类型级外推（occurrences=1，证据层 CACHE；本行载体层 %s）；不升确认"
                  % carrier["layer"],
                  "掩码位 param6=%d（1<<%d=%d），地形名未核（不写地形名）" % (p6, p6, 1 << p6)]
    if cls.get("terrain_count") and cls["terrain_count"] > 1:
        note_parts.append("原文列 %d 个地形，仅按 param6 写 1 个位索引" % cls["terrain_count"])
    note_parts.append("句面表述：" + PHRASE_ZH[cls["phrase"]])
    if cls.get("base_probability_clause"):
        note_parts.append("本行另有击杀基础概率子句，不在本答案范围")

    binding = {
        "template_id": "type28_terrain_%s" % cls["phrase"],
        "strength": ("规则键数值换算已确认（静态＋受控原生局部规则）；句面→载体类型级外推，"
                     "occurrences=1，不升确认"),
        "status": "推断（单来源类型级外推；不升确认）",
        "target": "持有者；击杀事件对应的玛那获得判定（地形掩码命中时的附加阈值）",
        "condition": cond,
        "duration": "地形满足时逐次击杀判定；常时被动（不是持续时间/每WAVE）",
        "rationale": ("原文只写「%s」，无逐字数值；载体 type28 记录 %s 的地形附加阈值"
                      "param4（type2）/param5（type0/1）、位索引 param6 为地形掩码；"
                      "基础 param0/param1/param2 只披露，不在本条答案范围"
                      % (cls["condition"], carrier["record_id"])),
        "source": src,
        "rule_status": "已确认（静态及受控原生局部规则）",
        "claim": {"table": table,
                  "record_id": MB._claim_record_id(record, table, cid),
                  "reference_field": reference_field, "text": text},
        "fields": fields,
        "registered_not_answered": {
            "param0": rec.get("param0"), "param1": rec.get("param1"),
            "param2": rec.get("param2"), "param6": rec.get("param6"),
            "param7": rec.get("param7"), "param8": rec.get("param8"),
            "note": ("param0/1/2 为基础阈值（披露用于计算命中时总阈值，本条只答地形附加）；"
                     "param6 为位索引（掩码 1<<param6）；param7/param8 语义未登记，"
                     "只登记原值；不写地形名"),
        },
        "unknowns": unknowns,
        "s5_binding": {
            "scope": SCOPE, "phrase": cls["phrase"], "phrase_zh": PHRASE_ZH[cls["phrase"]],
            "slots": list(ADDON_SLOTS), "base_slots": list(BASE_SLOTS),
            "record_id": carrier["record_id"], "carrier_layer": carrier["layer"],
            "carrier_role": carrier.get("role"),
            "evidence_layer": "CACHE", "rule_occurrences": 1,
            "mask_bit": p6, "mask": mask,
            "condition_text": cls["condition"],
            "terrain_count": cls.get("terrain_count"),
            "additive": bool(cls.get("additive")),
            "damage_types": {s: ADDON_DAMAGE_TYPE[s] for s in ADDON_SLOTS},
            "totals": {b: totals[b] for b in BASE_SLOTS},
            "base_values": {b: rec.get(b) for b in BASE_SLOTS},
            "base_probability_clause": cls.get("base_probability_clause"),
        },
    }
    return {
        "value": value,
        "quantity_kind": "击杀玛那概率阈值（地形附加）",
        "unit": "概率阈值增加量",
        "raw_value": float(rec.get(primary)),
        "field_path": "/" + primary,
        "rule_key": rule_key,
        "table": "skilllist",
        "record_id": carrier["record_id"],
        "layer": carrier["layer"],
        "source": src,
        "context": text,
        "numeric_source": "规则",
        "numeric_evidence": "推断",
        "association_evidence": "推断",
        "answer_status": "INFERRED_SINGLE_SOURCE",
        "evidence_scope": "BY_TYPE_EXTRAPOLATED",
        "quantitative": True,
        "condition_label": "地形掩码命中（param6=%d，1<<%d）+ 击杀时" % (p6, p6),
        "conditions": cond,
        "target": binding["target"],
        "note": "；".join(note_parts),
        "conversion": value,
        "binding": binding,
        "evidence": list(EVIDENCE_BASE),
    }


# ---------------------------------------------------------------------------
# 逐行评估
# ---------------------------------------------------------------------------
def gate_values(rec, phrase):
    """T5–T8 数值门（纯函数：只读 record dict＋句面表述），返回 (code, detail) 或 (None, None)。

    独立可测：反例用例可传入原始记录的副本并改值，不依赖载体解析/页面。
    """
    p6 = rec.get("param6")
    if p6 is None:
        return "MASK_MISSING", {"param6": p6}
    p6i = _int_slot(p6)
    if p6i is None:
        return "MASK_NOT_INTEGER", {"param6": p6}
    if p6i < 0 or p6i > 62:
        return "MASK_OUT_OF_RANGE", {"param6": p6i}
    if p6i == 0:
        return "MASK_ZERO", {"param6": p6i,
                             "why": "param6<=0 按批1既有口径视为无地形附加掩码"}
    for s in ADDON_SLOTS:
        v = rec.get(s)
        if not _finite(v):
            return "ADDON_MISSING", {"slot": s, "raw": v}
        if float(v) <= 0.0:
            return "ADDON_OUT_OF_RANGE", {"slot": s, "raw": v}
    missing_base = [b for b in BASE_SLOTS if not _finite(rec.get(b))]
    if missing_base:
        return "BASE_SLOT_MISSING", missing_base
    totals = _totals_in(rec, BASE_SLOTS)
    if phrase == "always":
        bad = {b: v for b, v in totals.items() if abs(v - 1.0) > TOTAL_TOL}
        if bad:
            return "VALUE_TRIGGER_MISMATCH", {"totals": totals,
                                              "expected": "必ず: 基础+附加==1.0",
                                              "bad": bad}
    else:
        bad = {b: v for b, v in totals.items() if not (0.0 < v <= 1.0 + TOTAL_TOL)}
        if bad:
            return "THRESHOLD_OUT_OF_RANGE", {"totals": totals, "bad": bad}
    return None, None


def _already(existing, rule_key, record_id, field_path):
    for a in existing or []:
        if (a.get("rule_key") == rule_key and a.get("record_id") == record_id
                and a.get("field_path") == field_path):
            return True
    return False


def evaluate(data, table, reference_field, record, text, existing_answers=None,
             layer=None, cid=None):
    existing_answers = existing_answers or []
    res = _result(table, reference_field, text)
    if cid in ZERO_TOUCH_CIDS:
        return _reject(res, "ZERO_TOUCH_CID", cid)
    if table not in ADMITTED_TABLES:
        return _reject(res, "CHARAINFO_EQUIVALENCE_FAIL_CLOSED",
                       "仅 skilllist；展示复制行（%s）需记录级等价门，本批 fail-closed" % table)
    t = _norm(text)
    if not t:
        return _reject(res, "EMPTY_TEXT")
    cls = classify_terrain(text)
    res["gates"]["classify"] = {k: v for k, v in cls.items() if k != "rejection"}
    res["phrase"] = cls.get("phrase")
    if cls.get("rejection"):
        return _reject(res, cls["rejection"], cls.get("detail"))

    carriers, issues = MB.resolve_carriers(data, table, record, layer=layer)
    res["gates"]["carrier_issues"] = issues
    if issues:
        return _reject(res, "CARRIER_CHAIN_BROKEN", issues)
    c28 = MB._dedupe([c for c in carriers if (c.get("record") or {}).get("ability") == 28])
    ids = sorted({c["record_id"] for c in c28})
    res["gates"]["carriers"] = [{"record_id": c["record_id"], "layer": c["layer"],
                                 "role": c["role"]} for c in c28]
    res["gates"]["sibling_abilities"] = sorted(
        {(c.get("record") or {}).get("ability") for c in carriers
         if _finite((c.get("record") or {}).get("ability"))})
    if not c28:
        return _reject(res, "NO_TYPE28_CARRIER")
    if len(ids) != 1:
        return _reject(res, "MULTI_CARRIER_AMBIGUOUS", ids)
    carrier = c28[0]
    rec = carrier["record"]
    res["gates"]["record_id"] = carrier["record_id"]
    res["gates"]["layer"] = carrier["layer"]
    res["gates"]["params"] = {k: rec.get(k) for k in
                              ("param0", "param1", "param2", "param3", "param4", "param5",
                               "param6", "param7", "param8", "param9", "iParam0")}
    res["gates"]["mask"] = _mask_text(rec.get("param6"))

    # T5–T8 数值门（掩码位/附加阈值/基础槽/必ず总阈值）
    p6i = _int_slot(rec.get("param6"))
    code, detail = gate_values(rec, cls["phrase"])
    if p6i is not None:
        res["gates"]["mask_bit"] = p6i
        res["gates"]["totals"] = _totals_in(rec, BASE_SLOTS)
    if code:
        return _reject(res, code, detail)
    # T9 既有答案
    ans = build_answer(data, table, reference_field, record, text, carrier, cls, cid)
    for _s in ADDON_SLOTS:
        _rk = RULE_ID_PREFIX + _s
        if _already(existing_answers, _rk, ans["record_id"], "/" + _s):
            return _reject(res, "ALREADY_ANSWERED",
                           {"rule_key": _rk, "record_id": ans["record_id"],
                            "field_path": "/" + _s})
    res["accepted"] = True
    res["answers"] = [ans]
    return res


# ---------------------------------------------------------------------------
# 正式页消费
# ---------------------------------------------------------------------------
def _record_index(data, cid):
    index = {}
    for g in ((data.links.get(cid) or {}).get("groups") or []):
        for rec in g.get("records") or []:
            index[(rec.get("table"), rec.get("reference_field"))] = rec
    return index


def _append(row, answer, report):
    def key(a):
        return (a.get("rule_key"), a.get("record_id"), a.get("field_path"))
    if any(key(a) == key(answer) for a in row.get("answers") or []):
        return False
    row.setdefault("answers", []).append(answer)
    row["row_class"] = "A"
    row["evidence"] = "推断"
    row["evidence_label"] = "推断（S5地形：type28 地形附加阈值单来源外推）"
    row["partial"] = True
    row["evidence_scope"] = list(dict.fromkeys(list(row.get("evidence_scope") or [])
                                              + ["BY_TYPE_EXTRAPOLATED"]))
    marker = row.setdefault("inference_s5_terrain", {"scope": SCOPE, "claims": []})
    marker["claims"].append({"phrase": answer["binding"]["s5_binding"]["phrase"],
                             "record_id": answer["record_id"],
                             "rule_key": answer["rule_key"],
                             "mask_bit": answer["binding"]["s5_binding"]["mask_bit"],
                             "slots": answer["binding"]["s5_binding"]["slots"]})
    report["answers_added"] += 1
    report["additions"].append({"row_id": row["row_id"],
                                "record_id": answer["record_id"],
                                "rule_key": answer["rule_key"],
                                "field_path": answer["field_path"],
                                "raw_value": answer["raw_value"]})
    return True


def apply_to_groups(data, cid, groups):
    """正式页消费：为 S5 地形段 15 行绑定 type28 地形附加阈值答案（不覆盖/不删除既有答案）。"""
    report = {"scope": SCOPE, "cid": cid, "answers_added": 0, "additions": [],
              "rejections": [], "skipped_existing": 0, "evaluated": 0}
    if cid in ZERO_TOUCH_CIDS:
        report["zero_touch"] = True
        report["rejections"].append({"reason": "ZERO_TOUCH_CID", "cid": cid})
        return report
    index = _record_index(data, cid)
    seen_rows = set()
    for group in groups:
        for skill in group.get("skills", []):
            table = skill.get("table")
            ref = skill.get("reference_field")
            lo = index.get((table, ref))
            if lo is None:
                continue
            record = lo.get("record") or {}
            for row in skill.get("rows", []):
                rid = row.get("row_id")
                if rid in seen_rows:
                    report["rejections"].append({"row_id": rid, "reason": "DUPLICATE_ROW_ID"})
                    continue
                seen_rows.add(rid)
                if rid not in TERRAIN_ROWS:
                    continue
                text = str(row.get("japanese") or "")
                if "地形" not in text and "戦場" not in text:
                    continue
                report["evaluated"] += 1
                res = evaluate(data, table, ref, record, text, row.get("answers") or [],
                               layer=lo.get("layer"), cid=cid)
                if not res["accepted"]:
                    if res["rejection"] == "ALREADY_ANSWERED":
                        report["skipped_existing"] += 1
                    else:
                        report["rejections"].append({"row_id": rid,
                                                     "reason": res["rejection"],
                                                     "detail": res.get("detail")})
                    continue
                added = 0
                for ans in res["answers"]:
                    if _append(row, ans, report):
                        added += 1
                if not added:
                    report["skipped_existing"] += 1
                row.setdefault("s5_terrain_gate", dict(res["gates"]))
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="S5 type28 地形附加：句式分类只读探针")
    ap.add_argument("--text", help="单句测试")
    args = ap.parse_args(argv)
    if args.text:
        print(json.dumps(classify_terrain(args.text), ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
