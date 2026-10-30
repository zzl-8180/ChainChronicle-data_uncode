# -*- coding: utf-8 -*-
"""マナ批 A 档推断模块：开局/获得玛那句式 → skilllist|26 已确认槽位。

范围（docs/tasks/20261025-character-skills-mana-batch.md §1，初裁②③）
--------------------------------------------------------------------
只消费已确认链：
* ``skilllist|26|/param0``（9/9 原生；持有者职业基础玛那）
* ``skilllist|26|/param4`` ＋ ``/iParam1``（原生成对；iParam1=31＝全职业位图）
* ``skilllist|26|/param7``（万象玛那，属性标志 8，不受职业限定）
* 二级链 ``extra_ability_info.extra_abilities[N].skill_ids[]`` 与
  ``supporterskill.abi0/abi1`` 经 **1082 包装 str0 转发** 到上述 26 记录。

不消费（本模块一律不回答）：
* ``skilllist|28`` 六键（单来源 43023602，不得外推）；
* ``26 /param1 ＋ /iParam0``（第三套槽位，规则未覆盖）与 ``param0×param5(isBoost)``；
* Chain/WAVE/撃破/地形/コスト句（``gain_number``/``cost_reduce``/``cost_statement`` 等）；
* ``80/96/1106/1110/1111`` 类型（只作为同串 sibling 登记，不取值）；
* charainfo/denju 展示复制行：记录级等价门 fail-closed（本批范围无此类行）。

门控（逐行，拒绝即不出答案）
------------------------------
1. 句式必须精确匹配三类开局句（含台词前缀/「また・さらに」接续；复合句只绑定主句）；
2. 载体槽位值＝原文数字（整数化后），否则 VALUE_MISMATCH；
3. 同一 26 记录/同一链串中若有两个同槽位载体 → MULTI_CARRIER_AMBIGUOUS；
4. 其它 26 槽位（param1+iParam0 / 另一开局产线）只登记不消费；若与主句冲突 → 拒答；
5. 时机：26 是开戦产线；主句之前出现 Chain/WAVE/発動時/地形/撃破/スロット/所持/消費/
   必要マナ 等触发词 → TIMING_MISMATCH；
6. charainfo/denju（记录级等价未证）→ CHARAINFO_EQUIVALENCE_FAIL_CLOSED；
7. 28/80/96/1106/1110/1111 载体不作值源；缺 26 载体 → NO_TYPE26_CARRIER；
8. 1082 转发断裂（str0 非数字/目标缺失）→ FORWARD_BROKEN；
9. param6 生效码：0 需装载期 ``_isActive`` 非 0、1 恒生效、2 需标志为 0；其它码 → PARAM6_INACTIVE；
10. 已有同 rule_key＋record_id 答案 → 跳过（不改旧值，不重复登记）。

答案证据档：数值换算「确认」、句面→记录归属「推断」、``BY_TYPE_EXTRAPOLATED``；
``answer_status=CONFIRMED_NUMERIC``，不冒充实机/最终数值。
"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

MODULE_VERSION = "mana_batch_20261025"

SCOPE = "MANA_BATCH_20261025_A"
ADMITTED_TABLES = ("skilllist", "extra_ability_info", "supporterskill")
# 主持 preservation 约束「30236/30239 零触碰」：这两张基线卡即使是万象 A 档也不新增答案
# （12 行保留拆分，本批范围 1,209 行 / 1,104 条新增）。
ZERO_TOUCH_CIDS = frozenset({30236, 30239})
MANA_TYPES = {26: "start_mana", 28: "kill_mana_chance", 80: "hold_mana",
              96: "mana_count_up", 1106: "chain_mana_get",
              1110: "aggregate_container_1110", 1111: "wedge_holder_scale"}

FAMILIES = {
    "start_manso": {
        "slot": "param7", "rule_key": "skilllist|26|/param7",
        "quantity_kind": "开局万象玛那数量",
        "value_template": "战斗开始时获得 {n} 个万象玛那（param7 产线；不受职业限定，属性标志 8）",
        "target": "持有者；开戦时授予有效 PanelManaGage（万象玛那）",
    },
    "start_alljob": {
        "slot": "param4", "rule_key": "skilllist|26|/param4",
        "quantity_kind": "开局全职业玛那数量",
        "value_template": "战斗开始时获得 {n} 个所有职业可用的玛那（param4 产线；职业位图 iParam1=31）",
        "target": "持有者；按 iParam1 位图展开为全职业旗标",
    },
    "start_plain": {
        "slot": "param0", "rule_key": "skilllist|26|/param0",
        "quantity_kind": "开局基础玛那数量（持有者职业）",
        "value_template": "战斗开始时按持有者职业获得 {n} 个基础玛那（param0 产线）",
        "target": "持有者职业；颜色由能力持有者 _jobType 决定",
    },
}

MANSO_RX = re.compile(r"^万象マナを([0-9]+)つ持った状態で戦闘を開始する。?$")
ALLJOB_RX = re.compile(r"^全ての職業で使用できるマナを([0-9]+)つ持った状態で戦闘を開始する。?$")
PLAIN_RX = re.compile(r"^(?:自身の職業の)?マナを([0-9]+)つ持った状態で戦闘を開始(?:する。|し、)(.*)$")
BARE_PLAIN_RX = re.compile(r"^(?:自身の職業の)?マナを[0-9]+つ持った状態で戦闘を開始する。?$")
CLAIM_PHRASE_RX = re.compile(r"(?:自身の職業の)?マナを[0-9]+つ持った状態で戦闘を開始(?:する。|し、)")
FLAVOR_RX = re.compile(r"^[^！？♪]*[！？♪]")
CONNECTIVES = ("また、", "また", "さらに")
FLAT = str.maketrans("０１２３４５６７８９", "0123456789")

# 主句之前出现即判时机不符的词（26 是开戦产线；这些属别族）
PREFIX_TRIGGERS = ("Chain", "チェイン", "WAVE", "発動時", "使用すると", "倒した時", "倒すたび",
                   "止めを刺す", "地形", "マナスロット", "所持していると", "保持している",
                   "マナを獲得", "マナを消費", "必要なマナ", "マナで発動", "限界突破", "ピリカ")
# 明确属别族/未确认的句式（即使含「マナをNつ持った状態で戦闘を開始」也不回答）
REJECT_PATTERNS = (
    ("START_BOOST_UNCONFIRMED", "全ての必殺技が使えるマナ"),
    ("START_BOOST_UNCONFIRMED", "全ての必殺技が使用できるマナ"),
    ("WEDGE_START_UNCONFIRMED", "時の楔"),
)
JOB_WORDS = ("戦士", "騎士", "弓使い", "僧侶", "魔法使い", "魔神所属", "天魔")
PARAM6_TEXT = {
    0: "param6=0：仅当装载期 CharaBehavior._isActive 非 0 时生效（装载流程未在逐卡证据中确认）",
    1: "param6=1：恒生效分支",
    2: "param6=2：仅当装载期 _isActive 为 0 时生效",
}
# 未知项按族拆分（2026-10-26 マナ账本映射批 §1.3）：万象专属的「属性标志 8」未知项不再挂到
# 全職業/素マナ答案上（マナ批独审 REPORT §6/§9 非阻塞项①）。纯文案：答案值/状态/证据档不变；
# 万象族清单逐项同原值同序（模块级旧名 UNKNOWNS 保留为万象族清单，兼容既有引用）。
UNKNOWNS_COMMON = [
    "实机装载/开局流程是否逐卡满足 param6 条件（本批不验证实机）",
    "最终战斗数值（本答案只给开局授予数量）",
]
UNKNOWNS_MANSO = [
    UNKNOWNS_COMMON[0],
    "万象玛那属性标志 8 在战斗中的具体颜色/用途（仅登记原生标志）",
    UNKNOWNS_COMMON[1],
]
UNKNOWNS = UNKNOWNS_MANSO
UNKNOWNS_BY_FAMILY = {
    "start_manso": UNKNOWNS_MANSO,
    "start_alljob": UNKNOWNS_COMMON,
    "start_plain": UNKNOWNS_COMMON,
}


def _norm(text):
    s = (text or "").replace("◆", "").replace("\\n", "").replace("\n", "")
    return re.sub(r"\s+", "", s.translate(FLAT))


def _strip_flavor(text):
    """剥掉连续台词段（以！？♪结尾且不含主张），返回 (前缀, 余文)。"""
    pref = ""
    t = text
    while True:
        m = FLAVOR_RX.match(t)
        if not m:
            break
        seg, rest = t[:m.end()], t[m.end():]
        if ((rest.startswith("マナを") or rest.startswith("自身の職業のマナを")
             or any(rest.startswith(c) for c in CONNECTIVES))):
            return pref + seg, rest
        if "マナを" in seg:
            break
        pref, t = pref + seg, rest
    return pref, t


def classify_claim(text):
    """返回 dict(family, number, residual, prefix) 或 dict(rejection=code, detail=...)。"""
    raw = str(text or "").strip()
    if not raw:
        return {"rejection": "EMPTY_TEXT"}
    for code, needle in REJECT_PATTERNS:
        if needle in raw:
            return {"rejection": code, "detail": needle}
    t = raw.translate(FLAT)
    pref, t = _strip_flavor(t)
    conn = ""
    for c in CONNECTIVES:
        if t.startswith(c):
            conn, t = c, t[len(c):]
            break
    if MANSO_RX.match(t):
        return {"family": "start_manso", "number": int(MANSO_RX.match(t).group(1)),
                "residual": None, "prefix": pref + conn, "sentence_kind": "bare"}
    if ALLJOB_RX.match(t):
        return {"family": "start_alljob", "number": int(ALLJOB_RX.match(t).group(1)),
                "residual": None, "prefix": pref + conn, "sentence_kind": "bare"}
    m = PLAIN_RX.match(t)
    if m:
        num = int(m.group(1))
        tail = (m.group(2) or "").strip()
        if not tail:
            kind = "flavor" if pref else ("connective" if conn else "bare")
            return {"family": "start_plain", "number": num, "residual": None,
                    "prefix": pref + conn, "sentence_kind": kind}
        # 复合句：主句＝mana 开局，余文另句（本批只绑定主句，行拆分保留）
        residual = re.sub(r"^(?:また、|また|さらに)", "", tail).strip("、。 ")
        if not residual:
            kind = "flavor" if pref else ("connective" if conn else "bare")
            return {"family": "start_plain", "number": num, "residual": None,
                    "prefix": pref + conn, "sentence_kind": kind}
        return {"family": "start_plain", "number": num, "residual": residual,
                "prefix": pref + conn, "sentence_kind": "residual"}
    # 句中前置子句（「スロウとダウンにならず、」「経験値が増え、さらに」）：
    # 仅当 mana 主张短语存在、且前置子句不含职业限定/使用限定时才绑定主句。
    m2 = CLAIM_PHRASE_RX.search(t)
    if m2:
        pre = t[:m2.start()]
        post = t[m2.end():]
        num_m = re.search(r"マナを([0-9]+)つ", m2.group(0))
        if num_m:
            jobs = [j for j in JOB_WORDS if j in pre]
            if jobs or "戦場に" in pre or "使用できる" in pre:
                return {"rejection": "JOB_LIMITED_START_UNCONFIRMED",
                        "detail": "/".join(jobs) or "使用限定/戦場条件"}
            residual = (pre + post).strip("、。 ")
            if not residual:
                kind = "flavor" if pref else ("connective" if conn else "bare")
                return {"family": "start_plain", "number": int(num_m.group(1)),
                        "residual": None, "prefix": pref + conn, "sentence_kind": kind}
            return {"family": "start_plain", "number": int(num_m.group(1)),
                    "residual": residual, "prefix": pref + conn,
                    "sentence_kind": "residual"}
    # 其它含 mana 主张的句子：明确不是本族，交给其它批
    return {"rejection": "NOT_MANA_START_CLAIM"}


def _pack_record(rec, layer, record_id, role, wrapper_chain=None):
    if rec is None:
        return None
    return {"record_id": record_id, "layer": layer, "ability_type": rec.get("ability"),
            "role": role, "record": rec, "wrapper_chain": wrapper_chain or []}


def _skill_entry(data, sid, layer=None):
    """层感知 skilllist 记录读取；兼容 data.skill（card_page_data.Inputs）。"""
    try:
        sid = int(sid)
    except (TypeError, ValueError):
        return None
    for want, table, path in (("CACHE", getattr(data, "cache_skill", None),
                               "skilllist.data5.json.raw"),
                              ("APK", getattr(data, "apk_skill", None), "_mdSkill.json")):
        if table is None or (layer and layer != want):
            continue
        hit = table.get(sid)
        if hit is None:
            continue
        idx, row = hit
        return dict(resolved=True, table="skilllist", reference_id=sid, record=row,
                    layer=want, source=dict(
                        source_key="%s/%s" % (want, path),
                        json_pointer="/skilllist/%d" % idx, layer=want,
                        record_key="%s/%s#/skilllist/%d" % (want, path, idx)))
    try:
        return data.skill(sid)
    except (AttributeError, TypeError, ValueError):
        return None


def _expand(data, sid, maxhop=3):
    """1082 包装按 str0 转发；返回 (entry, chain, broken_reason)。"""
    entry = _skill_entry(data, sid)
    chain = []
    for _ in range(maxhop):
        if entry is None:
            return None, chain, "TARGET_MISSING"
        rec = entry.get("record") or {}
        if rec.get("ability") != 1082:
            return entry, chain, None
        s0 = str(rec.get("str0") or "").strip()
        chain.append({"wrapper": rec.get("skillid"), "str0": s0})
        if not s0.lstrip("-").isdigit() or int(s0) < 1:
            return None, chain, "STR0_INVALID"
        entry = _skill_entry(data, int(s0))
    return None, chain, "WRAPPER_DEPTH"


def resolve_carriers(data, table, record, layer=None):
    """展开一行所属载体串，返回 (carriers, issues)。

    carriers: 26/28/80/96/1106/1110/1111 记录（含 role / wrapper chain）。
    issues: 转发断裂、容器缺失等。
    """
    out, issues = [], []
    rec = record or {}
    if table == "skilllist":
        entry = _skill_entry(data, rec.get("skillid"), layer)
        # data.skill 的 record 必须与页面行记录一致（防错位）
        if entry is None or entry.get("record") != rec:
            issues.append("OWN_RECORD_MISMATCH")
            return out, issues
        out.append(_pack_record(rec, entry.get("layer"), entry.get("reference_id"),
                                "own_record"))
        for sid in rec.get("sub") or []:
            sub, chain, broken = _expand(data, sid)
            if sub is None:
                issues.append("SUB_FORWARD_BROKEN:%s:%s" % (sid, broken))
                continue
            out.append(_pack_record(sub["record"], sub.get("layer"), sub.get("reference_id"),
                                    "sub", chain))
    elif table == "extra_ability_info":
        for sid in rec.get("skill_ids") or []:
            target, chain, broken = _expand(data, sid)
            if target is None:
                issues.append("CONTAINER_FORWARD_BROKEN:%s:%s" % (sid, broken))
                continue
            out.append(_pack_record(target["record"], target.get("layer"),
                                    target.get("reference_id"), "container", chain))
    elif table == "supporterskill":
        for sid in (rec.get("abi0"), rec.get("abi1")):
            if sid in (None, 0, "0"):
                continue
            target, chain, broken = _expand(data, sid)
            if target is None:
                issues.append("SUPPORT_FORWARD_BROKEN:%s:%s" % (sid, broken))
                continue
            out.append(_pack_record(target["record"], target.get("layer"),
                                    target.get("reference_id"), "container", chain))
    return out, issues


def _slot_value(carrier, slot):
    """26 槽位整数化（rules: float32→有符号 int32 向零截断）。"""
    v = (carrier.get("record") or {}).get(slot)
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
        return None
    return int(v), v


def _start_slots(record):
    """该 26 记录里带正值的三条开局产线槽位：param0/param4/param7。"""
    out = {}
    for slot in ("param0", "param4", "param7"):
        v = (record or {}).get(slot)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0:
            out[slot] = v
    return out


def _param6_state(record):
    v = (record or {}).get("param6")
    if v in (None, ""):
        code = 0
    else:
        try:
            code = int(float(v))
        except (TypeError, ValueError):
            return None, "PARAM6_UNREADABLE"
    if code not in PARAM6_TEXT:
        return code, "PARAM6_INACTIVE"
    return code, None


def evaluate(data, table, reference_field, record, text, existing_answers=None,
             layer=None, cid=None):
    """对一行做分类＋载体＋门控；返回 dict（accepted / rejection / gates / answer）。"""
    existing_answers = existing_answers or []
    result = {"scope": SCOPE, "table": table, "reference_field": reference_field,
              "text": text, "gates": {}, "accepted": False, "rejection": None,
              "answer": None, "carrier": None}
    if cid in ZERO_TOUCH_CIDS:
        result["rejection"] = "ZERO_TOUCH_CID"
        result["detail"] = cid
        return result
    cls = classify_claim(text)
    if cls.get("rejection"):
        result["rejection"] = cls["rejection"]
        result["detail"] = cls.get("detail")
        return result
    fam, num = cls["family"], cls["number"]
    spec = FAMILIES[fam]
    result["family"] = fam
    result["gates"].update({"claim_number": num, "sentence_kind": cls["sentence_kind"],
                            "residual_clause": cls["residual"],
                            "flavor_prefix": cls["prefix"]})
    # 主句之前的时机词
    m = CLAIM_PHRASE_RX.search(text.translate(FLAT))
    prefix = text.translate(FLAT)[:m.start()] if m else ""
    hit = [w for w in PREFIX_TRIGGERS if w in prefix]
    result["gates"]["prefix_triggers"] = hit
    if hit:
        result["rejection"] = "TIMING_MISMATCH"
        result["detail"] = "/".join(hit)
        return result
    if table not in ADMITTED_TABLES:
        result["rejection"] = "CHARAINFO_EQUIVALENCE_FAIL_CLOSED"
        result["detail"] = "展示复制行（%s）需记录级等价门；本批 fail-closed" % table
        return result
    carriers, issues = resolve_carriers(data, table, record, layer)
    result["gates"]["carrier_issues"] = issues
    result["gates"]["sibling_types"] = sorted({c["ability_type"] for c in carriers
                                               if c.get("ability_type") in MANA_TYPES})
    c26 = [c for c in carriers if c.get("ability_type") == 26]
    if not c26:
        result["rejection"] = "NO_TYPE26_CARRIER"
        return result
    slot = spec["slot"]
    exact = []
    for c in c26:
        got = _slot_value(c, slot)
        if got and got[0] >= 1 and got[0] == num:
            exact.append((c, got))
    if not exact:
        # 有 26 但槽位值不符/缺失
        observed = [(c["record_id"], _slot_value(c, slot)) for c in c26]
        result["rejection"] = "VALUE_MISMATCH"
        result["detail"] = observed
        return result
    if len({c["record_id"] for c, _ in exact}) > 1:
        result["rejection"] = "MULTI_CARRIER_AMBIGUOUS"
        result["detail"] = [c["record_id"] for c, _ in exact]
        return result
    carrier, (iv, raw) = exact[0]
    rec = carrier["record"]
    result["carrier"] = {"record_id": carrier["record_id"], "layer": carrier["layer"],
                         "role": carrier["role"], "wrapper_chain": carrier["wrapper_chain"],
                         "params": {k: v for k, v in rec.items() if k.startswith(("param", "iParam", "flag"))
                                    and v not in (0, 0.0, None)}}
    # 同一 26 记录的其它开局槽位（只登记）
    other_start = {s: v for s, v in _start_slots(rec).items() if s != slot}
    result["gates"]["other_start_slots"] = other_start
    # 其它 26 载体的起始槽位冲突：同槽位不同值或另一开局线值>0
    conflicts = []
    for c in c26:
        if c["record_id"] == carrier["record_id"]:
            continue
        p = c.get("record") or {}
        same = _slot_value(c, slot)
        if same and same[0] >= 1:
            conflicts.append({"record_id": c["record_id"], "slot": slot, "value": same[0]})
        for s, v in _start_slots(p).items():
            if s != slot:
                conflicts.append({"record_id": c["record_id"], "slot": s, "value": v})
    result["gates"]["competing_26"] = conflicts
    if any(x["slot"] == slot for x in conflicts):
        result["rejection"] = "MULTI_CARRIER_AMBIGUOUS"
        result["detail"] = conflicts
        return result
    # 同记录内另一开局槽位若为正且不属第三套 param1/iParam0 → 不拒绝但登记；此处两者都登记。
    third = [c for c in c26 if c["record_id"] == carrier["record_id"] and "param1" in (rec or {})
             and (rec.get("iParam0") or 0)]
    result["gates"]["third_slot_param1_iparam0"] = bool(third)
    # 全職業：iParam1 必须为 31（全职业位图）
    if fam == "start_alljob":
        mask = rec.get("iParam1")
        result["gates"]["iparam1"] = mask
        if mask != 31:
            result["rejection"] = "JOB_MASK_NOT_ALL"
            result["detail"] = mask
            return result
    # 万象：只接受 CACHE（审计实测 param7 仅 CACHE>0）
    if fam == "start_manso" and carrier["layer"] != "CACHE":
        result["rejection"] = "PARAM7_APK_UNEXPECTED"
        result["detail"] = carrier["layer"]
        return result
    # param6 生效码
    code, p6err = _param6_state(rec)
    result["gates"]["param6"] = code
    result["gates"]["param6_text"] = PARAM6_TEXT.get(code)
    if p6err:
        result["rejection"] = p6err
        result["detail"] = rec.get("param6")
        return result
    # 文本核验：容器句或记录句须包含本行文本
    text_ok = False
    if table in ("extra_ability_info", "supporterskill"):
        text_ok = bool(_norm(text) and _norm(text) in _norm(record.get("text")))
        where = "container_text_contains_row" if text_ok else "container_text_no_substring"
    else:
        # 行所属记录（own）或 26 载体记录（sub/直载）任一句面含本行文本即可
        own_ok = bool(_norm(text) and _norm(text) in _norm((record or {}).get("text")))
        car_ok = bool(_norm(text) and _norm(text) in _norm(rec.get("text")))
        text_ok = own_ok or car_ok
        where = ("own_record_text_contains_row" if own_ok else
                 "carrier_record_text_contains_row" if car_ok else
                 "record_text_no_sentence")
    result["gates"]["text_verified"] = where
    if not text_ok:
        result["rejection"] = "TEXT_UNVERIFIED"
        return result
    # 去重：同 rule_key（+ 可得的 record_id/field_path/数值）已有答案 → 跳过，不改旧值
    for a in existing_answers:
        if a.get("rule_key") != spec["rule_key"]:
            continue
        rid = a.get("record_id")
        fp = a.get("field_path")
        if rid is not None and rid != carrier["record_id"]:
            continue
        if fp is not None and fp != "/" + slot:
            continue
        if rid is None and fp is None:
            try:
                if float(a.get("raw_value")) != float(raw):
                    continue
            except (TypeError, ValueError):
                pass
        result["rejection"] = "ALREADY_ANSWERED"
        result["detail"] = {"rule_key": spec["rule_key"], "record_id": carrier["record_id"]}
        return result
    result["accepted"] = True
    result["answer"] = build_answer(data, table, reference_field, record, text, carrier,
                                    fam, num, cls, iv, raw, code, cid)
    return result


def build_answer(data, table, reference_field, record, text, carrier, fam, num, cls,
                 iv, raw, code, cid=None):
    spec = FAMILIES[fam]
    rec = carrier["record"]
    entry = _skill_entry(data, carrier["record_id"], carrier.get("layer")) or {}
    source = copy.deepcopy(entry.get("source") or {})
    condition = "战斗开始时；type26 %s 分支" % spec["slot"]
    if fam == "start_alljob":
        condition += "；职业旗标 iParam1=31（全职业）"
    elif fam == "start_plain":
        condition += "；职业取持有者 _jobType"
    else:
        condition += "；属性标志 transELEMENT_TYPE_FLAG(8)，不受职业限定"
    condition += "；" + PARAM6_TEXT.get(code, "param6=未知")
    note_parts = []
    if fam == "start_manso":
        note_parts.append("5 个等级行同值、按卡×主张只登记一次；本行引用本档容器载体 %s"
                          % carrier["record_id"])
    if fam == "start_alljob":
        note_parts.append("param4 的生效仍受装载/开局流程影响（rules 现状），本答案只给槽位值")
    comp = [x for x in _start_slots(rec).items() if x[0] != spec["slot"]]
    if comp:
        note_parts.append("同记录另有槽位 %s（不同句/不同主张，未在本答案中消费）"
                          % "、".join("%s=%s" % (k, v) for k, v in comp))
    if "param1" in rec and (rec.get("iParam0") or 0):
        note_parts.append("同记录 param1+iParam0=%s（第三套槽位，规则未覆盖，B；本批不消费）"
                          % rec.get("iParam0"))
    if cls.get("residual"):
        note_parts.append("同句另有未被本批覆盖的子句「%s」，行拆分标志保留" % cls["residual"])
    if cls.get("flavor_prefix"):
        note_parts.append("前置为角色台词/接续词，不构成效果子句")
    binding = {
        "template_id": "type26_%s_%s" % (spec["slot"].lstrip("/"), fam),
        "strength": "原生槽位与规则已确认；句面→记录归属为逐行结构门控＋原文数字一致，证据档推断；不是机器码解析日文",
        "status": "推断（句面→载体槽位；数值换算已确认）",
        "target": spec["target"],
        "condition": condition,
        "duration": "开局一次授予；不是持续时间或每WAVE",
        "rationale": "原文只有开局玛那主张；载体 %s 的 %s 原值整数化＝原文数字；"
                     "其它产线/类型载体不参与本值" % (carrier["record_id"], spec["slot"]),
        "source": source,
        "claim": {"table": table, "record_id": _claim_record_id(record, table, reference_field, cid),
                  "reference_field": reference_field, "text": text},
        "fields": [{
            "f": "/" + spec["slot"], "raw": raw, "value": spec["value_template"].format(n=num),
            "kind": spec["quantity_kind"], "unit": "个",
            "status": "CONFIRMED_NUMERIC", "evidence_scope": "BY_TYPE_EXTRAPOLATED",
            "rule_key": spec["rule_key"], "table": "skilllist",
            "record_id": carrier["record_id"], "semantic_effect": "开局玛那",
            "native_path": "ManaGet.%s" % spec["slot"],
        }],
        "unknowns": list(UNKNOWNS_BY_FAMILY[fam]),
        "mana_batch": {"scope": SCOPE, "family": fam, "slot": spec["slot"],
                       "sentence_kind": cls["sentence_kind"],
                       "residual_clause": cls.get("residual")},
    }
    return {
        "value": spec["value_template"].format(n=num),
        "quantity_kind": spec["quantity_kind"],
        "unit": "个",
        "raw_value": (float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool)
                      else raw),
        "field_path": "/" + spec["slot"],
        "rule_key": spec["rule_key"],
        "table": "skilllist",
        "record_id": carrier["record_id"],
        "layer": carrier["layer"],
        "source": source,
        "context": text,
        "numeric_source": "规则",
        "numeric_evidence": "确认",
        "association_evidence": "推断",
        "answer_status": "CONFIRMED_NUMERIC",
        "evidence_scope": "BY_TYPE_EXTRAPOLATED",
        "quantitative": True,
        "condition_label": "战斗开始时 / %s" % spec["slot"],
        "conditions": condition,
        "target": spec["target"],
        "note": "；".join(note_parts) if note_parts else None,
        "conversion": spec["value_template"].format(n=num),
        "binding": binding,
        "evidence": ["output/character_skills/profiles/rules.json",
                     "output/character_skills/type26_mana/native_evidence.json",
                     "output/character_skills/skilllist_types/native_checks.json"],
    }


def _claim_record_id(record, table, reference_field, cid=None):
    if table in ("supporterskill", "extra_ability_info"):
        return cid
    return (record or {}).get("skillid")


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
    row["evidence_label"] = "推断（マナ开局句→type26 已确认槽位）"
    row["partial"] = True
    row["evidence_scope"] = list(dict.fromkeys(list(row.get("evidence_scope") or [])
                                              + ["BY_TYPE_EXTRAPOLATED"]))
    marker = row.setdefault("inference_mana", {"scope": SCOPE, "claims": []})
    marker["claims"].append({"family": answer["binding"]["mana_batch"]["family"],
                             "slot": answer["binding"]["mana_batch"]["slot"],
                             "record_id": answer["record_id"],
                             "value": answer["raw_value"]})
    report["answers_added"] += 1
    report["additions"].append({"row_id": row["row_id"],
                                "family": answer["binding"]["mana_batch"]["family"],
                                "slot": answer["binding"]["mana_batch"]["slot"],
                                "record_id": answer["record_id"],
                                "value": answer["raw_value"]})
    return True


def apply_to_groups(data, cid, groups):
    """正式页消费：为マナ A 档行绑定 type26 已确认槽位答案（不覆盖/不删除既有答案）。"""
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
                text = str(row.get("japanese") or "")
                if "マナ" not in text:
                    continue
                report["evaluated"] += 1
                res = evaluate(data, table, ref, record, text, row.get("answers") or [],
                                layer=lo.get("layer"), cid=cid)
                if not res["accepted"]:
                    if res["rejection"] == "ALREADY_ANSWERED":
                        report["skipped_existing"] += 1
                    elif res["rejection"] not in ("NOT_MANA_START_CLAIM",):
                        report["rejections"].append({"row_id": rid,
                                                     "reason": res["rejection"],
                                                     "detail": res.get("detail")})
                    continue
                if res["gates"].get("sentence_kind") == "residual":
                    report["rejections"].append({"row_id": rid,
                                                 "reason": "CLAUSE_PARTIAL_BOUND",
                                                 "detail": res["gates"].get("residual_clause")})
                _append(row, res["answer"], report)
                row.setdefault("mana_batch_gate", dict(res["gates"]))
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="マナ批 A 档：句面分类/载体/门控只读探针")
    ap.add_argument("--text", help="单句测试")
    ap.add_argument("--scope", help="scope_rows.jsonl（逐行 evaluate 只读复核）")
    args = ap.parse_args(argv)
    if args.text:
        print(json.dumps(classify_claim(args.text), ensure_ascii=False, indent=1))
        return 0
    if args.scope:
        rows = [json.loads(l) for l in Path(args.scope).read_text(encoding="utf-8").splitlines() if l.strip()]
        bad = [r for r in rows if classify_claim(r["japanese"]).get("rejection")]
        print(json.dumps({"rows": len(rows), "classification_rejections": len(bad),
                          "samples": bad[:5]}, ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
