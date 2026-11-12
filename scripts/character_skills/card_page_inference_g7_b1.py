# -*- coding: utf-8 -*-
"""G7-B1 首段味方全体增益（3 行 / 12 效果，全 Y.G.）。

任务书 ``docs/tasks/20261029-g7-b1-first-segment-batch.md``；预检
``output/character_skills/inference_inventory/next_cycle_precheck_20261029/``
（``precheck_report.md`` §4.1、``g7_yield.jsonl``）；本批重筛与首/次段证据清单
``output/character_skills/g7_b1_20261029/``（``rescreen.json``、
``first_second_segment_evidence.md``）。

问题
----
4316／30105／30111 的 **传授（denju）首句行**
``【連撃】味方全体の攻撃力と防御力と移動速度とクリティカル発生率とクリティカル威力が一定時間上がる。``
当前 0 答案、账本「未解析」、各 6 条 unresolved。句中紧随的
``一定時間が経過すると効果が上がる。`` 是**同一加成的升级段**，同一原始链里因此有
**两条 type13**。若不分首/次段，就会把升级后的值（.7/.35/.35）当成初始值。

首段归属（顺序证据＋原生证据，**不按同文或数值大小猜选**）
----------------------------------------------------------
1. ``denju[denju_id=cid].patternid0`` 指向的 ``bosspattern`` 其 ``sinfo`` 与
   ``denju.stext`` **逐字符相等**——该 pattern 就是本技能自己的正文载体；
2. 该 pattern 恰 3 个非零槽 ``skillid0..2``，类型 ``[13, mid, 13]``（mid 实测为
   116／110／116），即链内 **type13 恰 2 条**；
3. 执行列表按 ``skillidN`` 顺序组装，``CheckEntry(0x1295360)`` 在 ``0x12954B0``
   取列表 ``get_Item(0)`` → ``SetExecSkill(0x1295e70)`` → ``initialize_ExAttack``
   把该记录的 ``skillparamN`` 复制进 util（``scripts/character_skills/cp_paths.py:192-207``；
   同旨 ``equivalence.py:45-46``）——**slot0＝最先执行的那条**；
4. 因此 slot0 的 type13 对应首句（初始加成），slot2 的 type13 对应升级句（次段）。
   同卡 ``special_move pattern0`` 首句行已用**同一批子记录**出过值且恰好绑定 slot0
   的 type13（本模块把它作为**同卡既有已审定答案的逐值对照门**，不是复制来源）。

出数范围（12 效果 = 3 行 × 4 槽）
--------------------------------
``bossskill|13|/skillparam1``（攻击增益输入）、``/skillparam2``（固定防御量系数）、
``/skillparam3``（持续游戏秒）、``/skillparam6``（移动速度乘数）——rules 294 键内，
**不改 rules.json／rules.py**。

暴击两项保持未知
----------------
``クリティカル発生率``／``クリティカル威力`` 的候选载体 ``bossskill|116`` 在 rules 中
**0 键**；另一条会被借用的路（链内两个 type13 各自的 s_ability＝ability2012）本轮实测为
**两条载体**（首段 param4/5＝.3、次段＝.05），天然 multi-carrier 归属歧义，与行上既有
``inference_b8_hint`` 一致。故本批**不出数、不填零、不借 type13 或 2012 其他链补**
（3 行 × 2 项＝6 项）。

次段（排除分支）
----------------
slot2 的 type13（4316 ``40431602`` .7/.35/22.5/.35；30105 ``43010502``
.7/.35/24.15/.35；30111 ``43011102`` .7/.35/24.15/.35）**逐行披露为排除值**
（``binding.g7_b1_binding.second_segment``），不并入首段数值。沿用既有
``CONFIG_ONLY_NOT_BOUND_TO_UPGRADE`` 口径（``card_page_inference_yg1_multistage.py``）。

层
--
行 source＝``CACHE/denju.data5.json.raw``，载体全部在 CACHE ``bossinfo``；APK 主表
无 bossskill 侧记录，故无跨层取值。``CACHE/APK`` 同 skillid 不混层。

不新增唯一数值
--------------
三行 4 槽的值与同卡 ``special_move pattern0`` 首句行同 rule_key 同记录同值
（逐值门 ``base_pattern0_matches_first``）；本批是**行级出清 + 首段归属定源**，
不产生该卡此前未出现的数值。答案文本不写最终伤害、不写秒数换算、不做实机验证。

账本侧：**不改 effect_ledger 映射逻辑**——t13 四键已在 ``_RULE_KEY_EFFECT``，答案带
标准 ``rule_key``/``table``/``record_id``/``layer``/``field_path`` 即被既有映射消费。
"""
from __future__ import annotations

import math
import re
import struct
import unicodedata
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path

MODULE_VERSION = "g7_b1_first_segment_20261029"
SCOPE = "G7_B1_T13_FIRST_SEGMENT_20261029"
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

CLAUSE = ("味方全体の攻撃力と防御力と移動速度とクリティカル発生率とクリティカル威力が"
          "一定時間上がる。")
DENJU_TEXT = "【連撃】" + CLAUSE
ESCALATION_TEXT = "一定時間が経過すると効果が上がる。"
BASE_PREFIXES = ("【共鳴必殺/連撃】", "【超共鳴必殺/連撃】")

# (句面效果, 槽字段, human 模板键)
SLOTS = (("攻撃力", "skillparam1", "attack"),
         ("防御力", "skillparam2", "defense"),
         ("移動速度", "skillparam6", "move"),
         ("継続時間", "skillparam3", "duration"))
RULE_KEYS = tuple(f"bossskill|13|/{field}" for _a, field, _k in SLOTS)
EVIDENCE = [
    "output/character_skills/g7_b1_20261029/rescreen.json",
    "output/character_skills/g7_b1_20261029/first_second_segment_evidence.md",
    "scripts/character_skills/cp_paths.py",
    "scripts/character_skills/equivalence.py",
    "docs/tasks/20261018-character-skills-p9.md",
]
LIMIT = ("首段为执行列表第 0 项的归属推断；次段（升级段）配置未绑定、不入本行数值；"
         "暴击两项（t116 在 rules 中 0 键）保持未知；不写最终伤害、不写秒数换算。")

# 冻结准入表（2026-10-29 由 rescreen.py 从原始 CACHE 记录独立重导一致后固化）。
# first＝slot0 type13（首段）；mid＝slot1（116/110，无映射键或非本句）；later＝slot2 type13（次段/排除）。
_ADMITTED_LIST = [
    dict(cid=4316, row_id="4316-denju-denju-denju_denju_id____cid-lvorder0-f0",
         denju_index=386, pattern_id=40431602,
         first_id=40431600, mid_id=40431601, mid_type=116, later_id=40431602,
         first_vals={"skillparam1": 0.6, "skillparam2": 0.3,
                     "skillparam3": 30, "skillparam6": 0.3},
         later_vals={"skillparam1": 0.7, "skillparam2": 0.35,
                     "skillparam3": 22.5, "skillparam6": 0.35}),
    dict(cid=30105, row_id="30105-denju-denju-denju_denju_id____cid-lvorder0-f0",
         denju_index=1452, pattern_id=43010502,
         first_id=43010500, mid_id=43010501, mid_type=110, later_id=43010502,
         first_vals={"skillparam1": 0.6, "skillparam2": 0.3,
                     "skillparam3": 30, "skillparam6": 0.3},
         later_vals={"skillparam1": 0.7, "skillparam2": 0.35,
                     "skillparam3": 24.15, "skillparam6": 0.35}),
    dict(cid=30111, row_id="30111-denju-denju-denju_denju_id____cid-lvorder0-f0",
         denju_index=1456, pattern_id=43011103,
         first_id=43011100, mid_id=43011101, mid_type=116, later_id=43011102,
         first_vals={"skillparam1": 0.6, "skillparam2": 0.3,
                     "skillparam3": 30, "skillparam6": 0.3},
         later_vals={"skillparam1": 0.7, "skillparam2": 0.35,
                     "skillparam3": 24.15, "skillparam6": 0.35}),
]
ADMITTED = {item["row_id"]: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item["cid"] for item in _ADMITTED_LIST)

HUMAN = {
    "attack": ("技能连锁系数为1时，攻击提升{s}%；实际提升受连锁系数影响"
               "（首段／初始加成；归属推断）"),
    "defense": ("获得固定防御加成；在已核玩家构造缩放条件、技能连锁系数为1时，"
                "名义原始攻击力系数约为{s}%，实际固定量取决于当前攻击基数和连锁系数"
                "（首段／初始加成；归属推断）"),
    "move": ("技能连锁系数为1时，移动速度提升{s}%；实际提升受连锁系数影响"
             "（首段／初始加成；归属推断）"),
    "duration": ("这组攻击、固定防御与移速加成的支持计时为{s}游戏秒"
                 "（首段／初始加成；归属推断）"),
}
_STALE_REASONS = {
    "原文未提供该效果数值，尚无已审定的句内字段归属",
    "此描述尚无可适用的已确认数值或新增机制证据",
}

_TABLES = {}


def _read(path: Path):
    import json
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def tables(data):
    """CACHE 解码主表（按 root 缓存；只读）。"""
    root = Path(getattr(data, "root", Path("."))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = read_path(root / "output/cache_full_20261015_v3/decoded", root=root)
        boss = _read(base / "bossinfo.data5.json.raw")["bossinfo"]
        patterns, skills = {}, {}
        for i, rec in enumerate(boss["bosspattern"]):
            patterns.setdefault(rec.get("patternid"), []).append((i, rec))
        for i, rec in enumerate(boss["bossskill"]):
            skills.setdefault(rec.get("skillid"), []).append((i, rec))
        denju = {rec["denju_id"]: (i, rec)
                 for i, rec in enumerate(_read(base / "denju.data5.json.raw")["denju"])}
        chara = {rec["cid"]: rec
                 for rec in _read(base / "charainfo.data5.json.raw")["charainfo"]}
        _TABLES[key] = dict(patterns=patterns, skills=skills, denju=denju, chara=chara,
                            root=root)
    return _TABLES[key]


def canon(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(text or "")))


def chain_of(tab, cid):
    """denju 原始链 → (chain|None, rejection)。"""
    hit = tab["denju"].get(cid)
    if hit is None:
        return None, "DENJU_RECORD_MISSING"
    didx, denju = hit
    pid = denju.get("patternid0")
    pats = tab["patterns"].get(pid) or []
    if not pid or len(pats) != 1:
        return None, "BOSSPATTERN_NOT_UNIQUE"
    pidx, pattern = pats[0]
    if pattern.get("sinfo") != denju.get("stext"):
        return None, "PATTERN_TEXT_MISMATCH"
    slots = [(slot, pattern.get(f"skillid{slot}")) for slot in range(7)
             if pattern.get(f"skillid{slot}")]
    if [s for s, _ in slots] != [0, 1, 2]:
        return None, "SLOT_SHAPE_NOT_THREE"
    children = []
    for slot, sid in slots:
        hits = tab["skills"].get(sid) or []
        if len(hits) != 1:
            return None, f"SKILL_NOT_UNIQUE({sid})"
        sidx, rec = hits[0]
        children.append(dict(slot=f"skillid{slot}", skillid=sid, index=sidx,
                             type=rec.get("skillid0"), record=rec,
                             params={k: v for k, v in rec.items()
                                     if k.startswith("skillparam")}))
    if [c["type"] for c in children].count(13) != 2:
        return None, "EXACTLY_TWO_TYPE13_REQUIRED"
    return dict(denju_index=didx, denju_record=denju, pattern_id=pid,
                pattern_index=pidx, pattern=pattern, children=children,
                layer="CACHE"), None


def _rows(groups):
    return {r["row_id"]: r for g in groups or [] for s in g.get("skills") or []
            for r in s.get("rows") or []}


def _num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return ("%.6f" % f).rstrip("0").rstrip(".")


def _f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _base_corroboration(rows, rid, first_id, first_vals):
    """同卡 special_move pattern0 首句行的同 rule_key 同值答案（逐值对照门）。"""
    out = []
    for other in rows.values():
        if other["row_id"] == rid:
            continue
        if canon(other.get("japanese")) not in [canon(p + CLAUSE) for p in BASE_PREFIXES]:
            continue
        if other.get("reference_field") != "pattern0":
            continue
        for ans in other.get("answers") or []:
            rk = str(ans.get("rule_key") or "")
            if not rk.startswith("bossskill|13|/"):
                continue
            out.append(dict(row_id=other["row_id"], rule_key=rk,
                            record_id=ans.get("record_id"),
                            raw_value=ans.get("raw_value"),
                            field_path=ans.get("field_path"),
                            quantity_kind=ans.get("quantity_kind"),
                            unit=ans.get("unit"),
                            numeric_source=ans.get("numeric_source")))
    pairs = sorted((a["rule_key"], a["raw_value"]) for a in out
                   if a.get("record_id") == first_id)
    want = sorted((f"bossskill|13|/{field}", first_vals[field]) for _a, field, _k in SLOTS)
    return out, pairs == want


def evaluate(data, cid, row, rows=None, tab=None, chain=None):
    """单行判定（不写入）。返回 dict(accepted, rejection, answers, gates, detail)。"""
    rid = row.get("row_id")
    if cid in ZERO_TOUCH_CIDS:
        return {"accepted": False, "rejection": "ZERO_TOUCH_CID"}
    adm = ADMITTED.get(rid)
    if adm is None:
        return {"accepted": False, "rejection": "NOT_IN_BATCH_SCOPE"}
    if adm["cid"] != cid:
        return {"accepted": False, "rejection": "CID_MISMATCH"}
    if rows is None:
        rows = {rid: row}
    gates = {"row_id": rid, "cid": cid}
    if canon(row.get("japanese")) != canon(DENJU_TEXT):
        return {"accepted": False, "rejection": "ROW_TEXT_NOT_FIRST_CLAUSE", "gates": gates}
    if canon(row.get("context_text")) != canon(
            (tab or tables(data))["denju"][cid][1].get("stext")):
        return {"accepted": False, "rejection": "CONTEXT_TEXT_MISMATCH", "gates": gates}
    src = row.get("source") or {}
    gates["row_source"] = {k: src.get(k) for k in ("record_key", "source_key", "layer",
                                                   "json_pointer")}
    if src.get("layer") != "CACHE" or src.get("source_key") != "CACHE/denju.data5.json.raw":
        return {"accepted": False, "rejection": "ROW_LAYER_NOT_CACHE", "gates": gates}
    if chain is None:
        chain, err = chain_of(tab or tables(data), cid)
        if err:
            return {"accepted": False, "rejection": err, "gates": gates}
    if chain["pattern_id"] != adm["pattern_id"]:
        return {"accepted": False, "rejection": "PATTERN_ID_DRIFT",
                "detail": {"expected": adm["pattern_id"], "actual": chain["pattern_id"]},
                "gates": gates}
    first, mid, later = chain["children"]
    gates.update({
        "pattern_id": chain["pattern_id"], "layer": chain["layer"],
        "slots": [c["slot"] for c in chain["children"]],
        "child_ids": [c["skillid"] for c in chain["children"]],
        "child_types": [c["type"] for c in chain["children"]],
        "type13_count": [c["type"] for c in chain["children"]].count(13),
    })
    if first["type"] != 13 or later["type"] != 13 or mid["type"] == 13:
        return {"accepted": False, "rejection": "TYPE_SHAPE_DRIFT", "gates": gates}
    if (first["skillid"], mid["skillid"], later["skillid"],
            mid["type"]) != (adm["first_id"], adm["mid_id"], adm["later_id"],
                             adm["mid_type"]):
        return {"accepted": False, "rejection": "CHAINTARGET_DRIFT",
                "detail": {"expected": [adm["first_id"], adm["mid_id"], adm["later_id"],
                                        adm["mid_type"]],
                           "actual": [first["skillid"], mid["skillid"], later["skillid"],
                                      mid["type"]]}, "gates": gates}
    active = sorted(k for k, v in first["params"].items() if v not in (0, None))
    gates["first_active_params"] = active
    if active != ["skillparam1", "skillparam2", "skillparam3", "skillparam6"]:
        return {"accepted": False, "rejection": "FIRST_ACTIVE_SHAPE_DRIFT", "gates": gates}
    got_first = {k: first["params"].get(k) for k in
                 ("skillparam1", "skillparam2", "skillparam3", "skillparam6")}
    got_later = {k: later["params"].get(k) for k in
                 ("skillparam1", "skillparam2", "skillparam3", "skillparam6")}
    gates["first_values"] = got_first
    gates["later_values"] = got_later
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in list(got_first.values()) + list(got_later.values())):
        return {"accepted": False, "rejection": "VALUE_MISSING_OR_NONFINITE", "gates": gates}
    if got_first != adm["first_vals"]:
        return {"accepted": False, "rejection": "FIRST_VALUE_DRIFT",
                "detail": {"expected": adm["first_vals"], "actual": got_first},
                "gates": gates}
    if got_later != adm["later_vals"]:
        return {"accepted": False, "rejection": "LATER_VALUE_DRIFT",
                "detail": {"expected": adm["later_vals"], "actual": got_later},
                "gates": gates}
    if got_first == got_later:
        return {"accepted": False, "rejection": "SEGMENTS_INDISTINCT", "gates": gates}
    # 同卡既有已审定答案逐值对照（首段记录必须已在同卡 pattern0 首句行披露同值）
    base, base_ok = _base_corroboration(rows, rid, adm["first_id"], adm["first_vals"])
    gates["base_answers"] = base
    gates["base_value_match"] = base_ok
    if not base_ok:
        return {"accepted": False, "rejection": "NO_SAME_CARD_CORROBORATION",
                "detail": {"base_answers": base}, "gates": gates}
    # 无既有答案覆盖 / 冲突
    for ans in row.get("answers") or []:
        if ans.get("rule_key") in RULE_KEYS:
            return {"accepted": False, "rejection": "ALREADY_ANSWERED",
                    "detail": {"rule_key": ans.get("rule_key"),
                               "record_id": ans.get("record_id")}, "gates": gates}
    # 出 4 条答案
    ref_by_field = {}
    for item in base:
        if item.get("record_id") == adm["first_id"]:
            ref_by_field.setdefault(item["rule_key"], item)
    answers = []
    for attr, field, kind in SLOTS:
        raw = first["params"].get(field)
        rule_key = f"bossskill|13|/{field}"
        ref = ref_by_field.get(rule_key) or {}
        converted = _answer_for(raw, field, first["record"])
        if converted is None:
            return {"accepted": False, "rejection": "RULE_UNAVAILABLE",
                    "detail": field, "gates": gates}
        s = _num(raw * (100 if kind in ("attack", "move") else 10
                        if kind == "defense" else 1))
        value = HUMAN[kind].format(s=s)
        note = ("首段（初始加成）取执行列表第 0 项（pattern %s 的 skillid0，type13）的真实字段；"
                "顺序依据 CheckEntry 取执行列表 item(0) → SetExecSkill（本批不新增原生点）。"
                "次段（升级段）为排除分支：slot skillid2 的 type13 %s，原值 %s，不并入本行。"
                "暴击発生率／威力两项载体 type116 在 rules 中 0 键，保持未知。"
                "同值已在同卡 special_move pattern0 首句行同 rule_key 披露（不新增唯一数值）。%s"
                % (chain["pattern_id"], later["skillid"],
                   "/".join(_num(got_later[k]) for k in ("skillparam1", "skillparam2",
                                                        "skillparam3", "skillparam6")),
                   LIMIT))
        answer = {
            "value": value,
            "quantity_kind": converted.get("quantity_kind"),
            "unit": converted.get("unit"),
            "raw_value": raw,
            "effective_float32": _f32(raw),
            "quantitative": True,
            "numeric_source": "复用既有局部规则；首段（执行列表第 0 项）归属推断",
            "numeric_evidence": "推断",
            "association_evidence": "推断",
            "evidence_scope": SCOPE,
            "answer_status": converted.get("answer_status"),
            "rule_key": rule_key,
            "table": "bossskill",
            "record_id": first["skillid"],
            "layer": "CACHE",
            "field_path": "/" + field,
            "source": _source(first, chain, field),
            "rule_status": converted.get("rule_status"),
            "conversion": converted.get("conversion"),
            "base_definition": converted.get("base_definition"),
            "conditions": converted.get("conditions"),
            "rule_limits": converted.get("rule_limits"),
            "condition_label": "传授（denju）首段生效时（pattern %s 的执行列表第 0 项）"
                               % chain["pattern_id"],
            "target": "味方全体（实际接受者受各处理器成员列表筛选）",
            "binding": {"g7_b1_binding": _marker(cid, rid, chain, first, mid, later,
                                                got_first, got_later, field, rule_key)},
            "evidence": EVIDENCE[:],
            "note": note,
        }
        if kind == "defense":
            answer["exact_formula"] = ("trunc(float32(float32(normalAtk)×float32(p2×Chain)))")
        answers.append(answer)
    return {"accepted": True, "rejection": None, "answers": answers, "gates": gates,
            "detail": None}


def _answer_for(raw, field, record):
    import rules as R
    converted = R.answer_for("bossskill", 13, "/" + field, raw, record,
                             source_layer="CACHE")
    if converted is None:
        return None
    rule = R.rule_for("bossskill", 13, "/" + field) or {}
    out = dict(converted)
    out.update(rule_status=rule.get("status"), conversion=rule.get("conversion"),
               base_definition=rule.get("base_definition"),
               conditions=rule.get("applicability"), rule_limits=rule.get("limits"))
    return out


def _source(first, chain, field):
    pointer = f"/bossinfo/bossskill/{first['index']}"
    return {
        "table": "bossskill", "record_id": first["skillid"], "layer": "CACHE",
        "field_path": "/" + field,
        "source_key": "CACHE/bossinfo.data5.json.raw",
        "original_file": "output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw",
        "json_pointer": pointer,
        "field": "/" + field,
        "field_json_pointer": pointer + "/" + field,
        "record_key": f"CACHE/bossinfo.data5.json.raw#{pointer}",
        "source_resolution": "RESOLVED_EXACT_DECODED_RECORD",
        "note": ("按解码 JSON 的 bossskill.skillid 唯一命中；经本行 denju.patternid0 原始链"
                 "（pattern %s 的 skillid0）定源，不是同文复制" % chain["pattern_id"]),
    }


def _marker(cid, rid, chain, first, mid, later, got_first, got_later, field, rule_key):
    return {
        "scope": SCOPE,
        "cid": cid,
        "row_id": rid,
        "segment": "FIRST",
        "slot": "skillid0",
        "rule_key": rule_key,
        "field_path": "/" + field,
        "record_id": first["skillid"],
        "layer": "CACHE",
        "pattern_id": chain["pattern_id"],
        "pattern_slot": "patternid0",
        "denju_record": {"json_pointer": f"/denju/{chain['denju_index']}"},
        "first_segment": {"slot": "skillid0", "record_id": first["skillid"], "type": 13,
                          "values": dict(got_first)},
        "mid_slot": {"slot": "skillid1", "record_id": mid["skillid"], "type": mid["type"],
                     "rule_keys": []},
        "second_segment": {
            "slot": "skillid2", "record_id": later["skillid"], "type": 13,
            "values": dict(got_later),
            "disposition": "EXCLUDED_BRANCH_NOT_BOUND",
            "basis": ("次段＝升级句「一定時間が経過すると効果が上がる。」；沿用既有 "
                      "CONFIG_ONLY_NOT_BOUND_TO_UPGRADE 口径，只披露为排除值，不并入首段"),
            "clause": ESCALATION_TEXT,
        },
        "crit_unknown": {"type116_rule_keys": 0,
                         "claims": ["クリティカル発生率", "クリティカル威力"],
                         "note": "t116 在 rules 中 0 键；不出数、不填零、不借 type13/2012 其他链"},
        "order_evidence": {
            "execution_list": "pattern.skillid0..N 顺序即执行列表顺序",
            "item0": ("bhSkill.CheckEntry 0x12954B0 get_Item(0) → 0x12954C0 SetExecSkill "
                      "→ initialize_ExAttack 复制该记录 skillparamN"),
            "citations": ["scripts/character_skills/cp_paths.py:192-207",
                          "scripts/character_skills/equivalence.py:45-46",
                          "docs/tasks/20261018-character-skills-p9.md:46"],
            "not_value_magnitude": "不以同文或数值大小选段",
        },
        "value_basis": ("同卡 special_move pattern0 首句行同 rule_key 同记录同值已披露；"
                        "本批为行级出清＋首段归属定源，不新增该卡唯一数值"),
        "association": "推断",
        "native_evidence": "none（本批不新增原生点；沿用既有 CheckEntry item(0) 检查）",
    }


def _append(row, answers):
    """写入 4 条答案与行级标记（幂等）。返回新增条数。"""
    key = lambda a: (a.get("rule_key"), a.get("record_id"), a.get("field_path"))
    existing = {key(a) for a in row.get("answers") or []}
    added = 0
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault("answers", []).append(answer)
        existing.add(key(answer))
        added += 1
    if not added:
        return 0
    row["row_class"] = "A"
    row["evidence"] = "推断"
    row["evidence_label"] = ("推断（G7-B1 首段味方全体增益：执行列表第 0 项归属；"
                            "次段为排除分支；暴击两项未知）")
    row["partial"] = True
    row["numeric_evidence"] = "推断"
    row["association_evidence"] = "推断"
    scopes = row.get("evidence_scope") or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row["evidence_scope"] = list(dict.fromkeys(list(scopes) + [SCOPE]))
    reasons = [r for r in (row.get("unknown_reasons") or []) if r not in _STALE_REASONS]
    reasons.append("G7-B1：4 项（攻击力／固定防御系数／移动速度／持续游戏秒）已按执行列表"
                   "第 0 项（首段）出值；次段（升级段）为排除分支；暴击発生率／威力"
                   "（t116 在 rules 中 0 键）保持未知。")
    row["unknown_reasons"] = list(dict.fromkeys(reasons))
    binding = answers[0]["binding"]["g7_b1_binding"]
    marker = row.setdefault("inference_g7_b1", {"scope": SCOPE, "segment": "FIRST",
                                                "bindings": []})
    marker["pattern_id"] = binding["pattern_id"]
    marker["pattern_slot"] = binding["pattern_slot"]
    marker["second_segment"] = binding["second_segment"]
    marker["crit_unknown"] = binding["crit_unknown"]
    marker["order_evidence"] = binding["order_evidence"]
    marker["bindings"].append({
        "slot": "skillid0", "record_id": binding["record_id"],
        "rule_key": binding["rule_key"], "field_path": binding["field_path"],
        "values": binding["first_segment"]["values"]})
    marker["bindings"] = list({(b["rule_key"], b["field_path"]): b
                               for b in marker["bindings"]}.values())
    return added


def apply_to_groups(data, cid, groups):
    """正式页消费：为 3 行冻结准入表写首段 4 槽答案（不覆盖/不删除既有答案）。"""
    report = {"scope": SCOPE, "cid": cid, "evaluated": 0, "answers_added": 0,
              "additions": [], "rejections": [], "skipped_existing": 0,
              "out_of_scope": True}
    if cid not in ADMITTED_CIDS:
        return report
    report["out_of_scope"] = False
    if cid in ZERO_TOUCH_CIDS:
        report["zero_touch"] = True
        report["rejections"].append({"reason": "ZERO_TOUCH_CID", "cid": cid})
        return report
    rows = _rows(groups)
    tab = tables(data)
    for rid, adm in ADMITTED.items():
        if adm["cid"] != cid:
            continue
        row = rows.get(rid)
        if row is None:
            report["rejections"].append({"row_id": rid, "reason": "ROW_NOT_FOUND"})
            continue
        report["evaluated"] += 1
        res = evaluate(data, cid, row, rows=rows, tab=tab)
        if not res["accepted"]:
            if res["rejection"] == "ALREADY_ANSWERED":
                report["skipped_existing"] += 1
            else:
                report["rejections"].append({"row_id": rid, "reason": res["rejection"],
                                             "detail": res.get("detail")})
            continue
        added = _append(row, res["answers"])
        if added:
            report["answers_added"] += added
            for answer in res["answers"]:
                report["additions"].append({
                    "row_id": rid, "record_id": answer["record_id"],
                    "rule_key": answer["rule_key"],
                    "field_path": answer["field_path"],
                    "raw_value": answer["raw_value"]})
        else:
            report["skipped_existing"] += 1
    return report


def _main(argv=None):
    import argparse
    import json
    ap = argparse.ArgumentParser(description="G7-B1 首段味方全体增益：只读探针（单行/单卡）")
    ap.add_argument("--cid", type=int)
    ap.add_argument("--row-id")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(".").resolve()
    import card_page_data as D
    cids = ([int(str(args.row_id).split("-", 1)[0])] if args.row_id
            else [args.cid] if args.cid else sorted(ADMITTED_CIDS))
    data = D.Inputs(root, cids)
    out = []
    for cid in cids:
        card = json.loads((root / "output/character_skills/pages" / str(cid) / "card.json")
                          .read_text(encoding="utf-8"))
        rows = _rows(card.get("groups") or [])
        targets = [r for r in ADMITTED.values() if r["cid"] == cid]
        if args.row_id:
            targets = [r for r in targets if r["row_id"] == args.row_id]
        for adm in targets:
            row = rows.get(adm["row_id"]) or {"row_id": adm["row_id"]}
            res = evaluate(data, cid, row, rows=rows)
            out.append({
                "row_id": adm["row_id"], "accepted": res["accepted"],
                "rejection": res["rejection"],
                "records": sorted({a["record_id"] for a in res.get("answers") or []}),
                "values": [{"rule_key": a["rule_key"], "raw_value": a["raw_value"]}
                           for a in res.get("answers") or []],
                "second_segment": [b.get("second_segment")
                                   for b in [a["binding"]["g7_b1_binding"]
                                             for a in res.get("answers") or []]][:1],
                "page_answers": len(row.get("answers") or []),
                "page_row_class": row.get("row_class"),
                "gates": res.get("gates")})
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for item in out:
            print(("OK  " if item["accepted"] else "REJ "), item["row_id"],
                  item.get("records"),
                  [v["raw_value"] for v in item.get("values") or []],
                  item.get("rejection") or "")
    return 0 if all(i["accepted"] for i in out) else 1


if __name__ == "__main__":
    raise SystemExit(_main())
