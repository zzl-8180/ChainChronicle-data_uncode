# -*- coding: utf-8 -*-
"""G1-B1 必殺ダメージ镜像行绑定（25 行 / 21 卡，全部 Y.G.）。

任务书 ``docs/tasks/20261029-g1-b1-mirror-batch.md``；预检
``output/character_skills/inference_inventory/next_cycle_precheck_20261029/``
（``precheck_report.md`` §3、``g1_b1_admission_final.jsonl``、``g1_b1_o02_admission.jsonl``）。

问题
----
`その後、前方範囲内の全ての敵に大ダメージを与え、弾き飛ばし、ダウンにする。` 这类
必殺技「第二段」片段在每张卡的 **传授（denju）行** 与 **skilltext（charainfo）行** 上
都是 0 答案 / 仅原文次数，而同一段在同一卡的 **special_move pattern 档位行** 上已有
已确认规则的伤害倍率答案。贸然按同文复制会把 **另一档位** 的值抄过来（O02 反例：
351 pattern0=30 与 pattern2=34.5 同文异值），因此本批只做**行级绑定**：按本行自己的
原始链定源到唯一的 bossskill 记录，并用同卡基础档位行做同值核对。

定源（任务书 §1；CACHE 行只在 CACHE 层解析，不跨层）
----------------------------------------------------
* 19 行 ``DENJU_CHAIN``：``denju[denju_id=cid].patternid0`` → ``bossinfo.bosspattern``
  → ``skillid0..3`` → ``bossinfo.bossskill``（传送技自身带 patternid0，不是同文复制）。
* 6 行 ``CHARAINFO_PATTERN0``：``charainfo[cid].pattern0`` → bosspattern → skillids
  → bossskill（charainfo 记录自带 pattern0，同样不是同文复制）。
* 链内若有多条伤害型子记录，按**本行日语句面片段**判别（类型语义＋25 项一致性推断，
  **不是原生证据**）：
    - 句面 ``N回ダメージ`` → 多段型 type 105/110，且 ``skillparam6 == N``，恰 1 条；
    - 句面 大/中ダメージ 或 一定間隔 → 单发型 type 3/22/55/74，恰 1 条。
    - 7251 例外：两条 type105 记录 param6 都是 15、倍率都是 0.83——记录选取不唯一但
      **值唯一**，按 skillid 升序取首个并在答案里写明两记录同值。

槽位（rules.json 294 键内，本批**不改 rules.json / rules.py**）
--------------------------------------------------------------
``bossskill|3|/skillparam1``、``|22|/skillparam1``、``|55|/skillparam1``、
``|105|/skillparam1``、``|110|/skillparam1``、``|74|/skillparam5``。
另 4 个（76/112/51/47）不被这 25 行消费，不预登记。

不新增唯一数值
--------------
每个答案的 raw_value 必须与同卡基础档位行（同文 special_move pattern* 行）同 rule_key
答案**逐值相等**；链外其他档位值逐行登记为排除值（``binding.excluded_values``），
不并入本行。答案文本写「镜像行按原始链定源到 bossskill 记录与档位，倍率见同卡基础
档位行；链外档位值排除」，**不写同文复制、不写最终伤害、不写秒数**。

账本侧：只补 6 个既有确认规则键的**来源限定**映射（答案带 ``binding.g1_b1_binding``
且 scope/槽/record/layer 全部一致才消费），其他行映射行为零变化。
"""
from __future__ import annotations

import json
import math
import re
import struct
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path

MODULE_VERSION = "g1_b1_mirror_20261029"
SCOPE = "G1_B1_MIRROR_20261029"
EFFECT_TYPE = "ダメージ（词表外）"
ZERO_TOUCH_CIDS = frozenset({30236, 30239})
SINGLE_TYPES = (3, 22, 55, 74)
MULTI_TYPES = (105, 110)
SLOT = {3: "skillparam1", 22: "skillparam1", 55: "skillparam1",
        105: "skillparam1", 110: "skillparam1", 74: "skillparam5"}
MULTIHIT_RX = re.compile(r"(\d+)回ダメージ")

# 冻结准入表（25 行；由预检 g1_b1_admission_final.jsonl 经 rescreen.py 独立重导一致后固化）。
# base_records＝同卡基础档位行同值答案覆盖的记录；excluded＝链外档位值（record_id, raw）。
_ADMITTED_LIST = [
    dict(cid=351, row_id="351-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=40035103, skillid=40035101, type=3, rule_key="bossskill|3|/skillparam1",
         field_path="/skillparam1", raw_value=30, record_note=None, base_records=[40035101],
         excluded=[[40035108, 34.5]]),
    dict(cid=352, row_id="352-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=40035203, skillid=40035201, type=22, rule_key="bossskill|22|/skillparam1",
         field_path="/skillparam1", raw_value=15, record_note=None, base_records=[40035201],
         excluded=[[40035207, 19.5]]),
    dict(cid=2331, row_id="2331-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=40233103, skillid=40233101, type=110, rule_key="bossskill|110|/skillparam1",
         field_path="/skillparam1", raw_value=3, record_note=None, base_records=[40233101],
         excluded=[[40233107, 3.5]]),
    dict(cid=4315, row_id="4315-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=40431503, skillid=40431501, type=3, rule_key="bossskill|3|/skillparam1",
         field_path="/skillparam1", raw_value=17.5, record_note=None, base_records=[40431501],
         excluded=[[40431508, 20.5]]),
    dict(cid=7251, row_id="7251-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=40725103, skillid=40725100, type=105, rule_key="bossskill|105|/skillparam1",
         field_path="/skillparam1", raw_value=0.83,
         record_note="VALUE_UNIQUE_RECORD_NOT_UNIQUE", base_records=[40725101],
         excluded=[[40725107, 1.083]], same_value_records=[40725100, 40725101]),
    dict(cid=30108, row_id="30108-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=43010803, skillid=43010801, type=3, rule_key="bossskill|3|/skillparam1",
         field_path="/skillparam1", raw_value=30, record_note=None, base_records=[43010801],
         excluded=[[43010804, 32.5]]),
    dict(cid=30109, row_id="30109-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=43010903, skillid=43010901, type=22, rule_key="bossskill|22|/skillparam1",
         field_path="/skillparam1", raw_value=30, record_note=None, base_records=[43010901],
         excluded=[[43010905, 32.5]]),
    dict(cid=30110, row_id="30110-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=43011003, skillid=43011001, type=3, rule_key="bossskill|3|/skillparam1",
         field_path="/skillparam1", raw_value=30, record_note=None, base_records=[43011001],
         excluded=[[43011005, 32.5]]),
    dict(cid=30232, row_id="30232-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=43023203, skillid=43023202, type=74, rule_key="bossskill|74|/skillparam5",
         field_path="/skillparam5", raw_value=40, record_note=None, base_records=[43023202],
         excluded=[[43023205, 42.5], [43023208, 47.5]]),
    dict(cid=30232, row_id="30232-special_move-special_move-skilltext-lvorder3-f2",
         gate="CHARAINFO_PATTERN0", pattern_id=43023200, skillid=43023202, type=74,
         rule_key="bossskill|74|/skillparam5", field_path="/skillparam5", raw_value=40,
         record_note=None, base_records=[43023202],
         excluded=[[43023205, 42.5], [43023208, 47.5]]),
    dict(cid=30247, row_id="30247-special_move-special_move-skilltext-lvorder3-f1",
         gate="CHARAINFO_PATTERN0", pattern_id=43024700, skillid=43024701, type=3,
         rule_key="bossskill|3|/skillparam1", field_path="/skillparam1", raw_value=13.75,
         record_note=None, base_records=[43024701], excluded=[[43024707, 17.5]]),
    dict(cid=30258, row_id="30258-special_move-special_move-skilltext-lvorder3-f1",
         gate="CHARAINFO_PATTERN0", pattern_id=43025800, skillid=43025801, type=3,
         rule_key="bossskill|3|/skillparam1", field_path="/skillparam1", raw_value=17.5,
         record_note=None, base_records=[43025801], excluded=[[43025809, 20.5]]),
    dict(cid=30303, row_id="30303-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=43030302, skillid=43030301, type=22, rule_key="bossskill|22|/skillparam1",
         field_path="/skillparam1", raw_value=10, record_note=None, base_records=[43030301],
         excluded=[[43030305, 12.5]]),
    dict(cid=30309, row_id="30309-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=43030902, skillid=43030901, type=22, rule_key="bossskill|22|/skillparam1",
         field_path="/skillparam1", raw_value=31.25, record_note=None, base_records=[43030901],
         excluded=[[43030905, 34.5]]),
    dict(cid=30310, row_id="30310-denju-denju-denju_denju_id____cid-lvorder0-f3", gate="DENJU_CHAIN",
         pattern_id=43031002, skillid=43031002, type=74, rule_key="bossskill|74|/skillparam5",
         field_path="/skillparam5", raw_value=15, record_note=None, base_records=[43031002],
         excluded=[[43031005, 20]]),
    dict(cid=30310, row_id="30310-special_move-special_move-skilltext-lvorder2-f3",
         gate="CHARAINFO_PATTERN0", pattern_id=43031000, skillid=43031002, type=74,
         rule_key="bossskill|74|/skillparam5", field_path="/skillparam5", raw_value=15,
         record_note=None, base_records=[43031002], excluded=[[43031005, 20]]),
    dict(cid=30317, row_id="30317-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=43031703, skillid=43031701, type=22, rule_key="bossskill|22|/skillparam1",
         field_path="/skillparam1", raw_value=17.5, record_note=None, base_records=[43031701],
         excluded=[[43031705, 21]]),
    dict(cid=30323, row_id="30323-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=43032303, skillid=43032302, type=55, rule_key="bossskill|55|/skillparam1",
         field_path="/skillparam1", raw_value=1.6, record_note=None, base_records=[43032302],
         excluded=[[43032305, 1.8]]),
    dict(cid=30323, row_id="30323-special_move-special_move-skilltext-lvorder3-f2",
         gate="CHARAINFO_PATTERN0", pattern_id=43032300, skillid=43032302, type=55,
         rule_key="bossskill|55|/skillparam1", field_path="/skillparam1", raw_value=1.6,
         record_note=None, base_records=[43032302], excluded=[[43032305, 1.8]]),
    dict(cid=30324, row_id="30324-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=43032403, skillid=43032401, type=3, rule_key="bossskill|3|/skillparam1",
         field_path="/skillparam1", raw_value=20, record_note=None, base_records=[43032401],
         excluded=[[43032405, 22.5]]),
    dict(cid=30325, row_id="30325-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=43032503, skillid=43032501, type=55, rule_key="bossskill|55|/skillparam1",
         field_path="/skillparam1", raw_value=1, record_note=None, base_records=[43032501],
         excluded=[]),
    dict(cid=30325, row_id="30325-special_move-special_move-skilltext-lvorder3-f1",
         gate="CHARAINFO_PATTERN0", pattern_id=43032500, skillid=43032501, type=55,
         rule_key="bossskill|55|/skillparam1", field_path="/skillparam1", raw_value=1,
         record_note=None, base_records=[43032501], excluded=[]),
    dict(cid=30326, row_id="30326-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=43032606, skillid=43032601, type=3, rule_key="bossskill|3|/skillparam1",
         field_path="/skillparam1", raw_value=25, record_note=None, base_records=[43032601],
         excluded=[[43032605, 28.5]]),
    dict(cid=30327, row_id="30327-denju-denju-denju_denju_id____cid-lvorder0-f1", gate="DENJU_CHAIN",
         pattern_id=43032703, skillid=43032701, type=110, rule_key="bossskill|110|/skillparam1",
         field_path="/skillparam1", raw_value=5, record_note=None, base_records=[43032701],
         excluded=[[43032704, 5.5]]),
    dict(cid=30330, row_id="30330-denju-denju-denju_denju_id____cid-lvorder0-f2", gate="DENJU_CHAIN",
         pattern_id=43033003, skillid=43033001, type=3, rule_key="bossskill|3|/skillparam1",
         field_path="/skillparam1", raw_value=16, record_note=None, base_records=[43033001],
         excluded=[[43033009, 19]]),
]
ADMITTED = {item["row_id"]: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item["cid"] for item in _ADMITTED_LIST)
RULE_KEYS = frozenset(item["rule_key"] for item in _ADMITTED_LIST)

_BOSSINFO_CACHE = {}


def _bossinfo(root):
    key = str(Path(root).resolve())
    if key not in _BOSSINFO_CACHE:
        path = read_path(Path(root) / "output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw", root=Path(root))
        doc = json.loads(path.read_text(encoding="utf-8-sig"))["bossinfo"]
        _BOSSINFO_CACHE[key] = dict(
            patterns={p["patternid"]: (i, p) for i, p in enumerate(doc["bosspattern"])},
            skills={s["skillid"]: (i, s) for i, s in enumerate(doc["bossskill"])})
    return _BOSSINFO_CACHE[key]


def _denju_pattern(data, cid):
    """传授行自身的 patternid0（来自 links 的 denju_pattern_refs；CACHE）。"""
    for group in (data.links.get(cid) or {}).get("groups") or []:
        for entry in group.get("records") or []:
            if entry.get("table") == "denju":
                refs = entry.get("denju_pattern_refs") or []
                if refs:
                    return refs[0].get("reference_id"), refs[0].get("layer"), entry
    return None, None, None


def chain_of(data, cid, gate):
    """原始链 → (chain dict, rejection|None)。"""
    if gate == "DENJU_CHAIN":
        pid, layer, entry = _denju_pattern(data, cid)
        origin = {"kind": "denju.patternid0", "patternid0": pid,
                  "denju_pointer": (entry or {}).get("source", {}).get("json_pointer")}
        if pid is None:
            return None, "DENJU_PATTERNID0_MISSING"
    elif gate == "CHARAINFO_PATTERN0":
        rec = (getattr(data, "cache_chara", None) or {}).get(cid)
        if rec is None:
            return None, "CHARAINFO_RECORD_MISSING"
        pid = rec.get("pattern0")
        layer = "CACHE"
        origin = {"kind": "charainfo.pattern0", "pattern0": pid,
                  "charainfo_layer": "CACHE"}
        if pid is None:
            return None, "CHARAINFO_PATTERN0_MISSING"
    else:
        return None, "UNKNOWN_GATE"
    if layer != "CACHE":
        return None, "LAYER_MISMATCH"
    raw = _bossinfo(data.root)
    hit = raw["patterns"].get(pid)
    if hit is None:
        return None, "BOSSPATTERN_MISSING"
    pidx, pattern = hit
    children = []
    for slot in range(4):
        sid = pattern.get(f"skillid{slot}")
        if not sid:
            continue
        sh = raw["skills"].get(sid)
        if sh is None:
            children.append({"slot": slot, "skillid": sid, "missing": True})
            continue
        cidx, srec = sh
        children.append({"slot": slot, "skillid": sid, "index": cidx,
                         "type": srec.get("skillid0"),
                         "params": {k: v for k, v in srec.items()
                                    if k.startswith("skillparam")}})
    return {"pattern_id": pid, "pattern_index": pidx, "pattern": pattern,
            "children": children, "origin": origin, "layer": layer}, None


def select(chain, text):
    """片段判别 → (chosen|None, selection dict)。"""
    children = chain["children"]
    m = MULTIHIT_RX.search(text or "")
    if m:
        n = int(m.group(1))
        typed = [c for c in children if c.get("type") in MULTI_TYPES]
        hits = [c for c in typed if c.get("params", {}).get("skillparam6") == n]
        if not hits:
            return None, {"mode": "MULTIHIT", "n": n, "n_typed": len(typed),
                          "rejection": "NO_MULTIHIT_PARAM6_MATCH"}
        if len(hits) > 1 and len({c["params"].get(SLOT[c["type"]]) for c in hits}) > 1:
            return None, {"mode": "MULTIHIT", "n": n, "n_typed": len(typed),
                          "rejection": "MULTI_MULTIHIT_DIFF_VALUES"}
        hits = sorted(hits, key=lambda c: c["skillid"])
        return hits[0], {"mode": "MULTIHIT", "n": n, "n_typed": len(typed),
                         "param6": n, "records": [c["skillid"] for c in hits],
                         "record_note": ("VALUE_UNIQUE_RECORD_NOT_UNIQUE"
                                         if len(hits) > 1 else None),
                         "basis": "句面 N回ダメージ ↔ 多段型 type105/110 且 skillparam6==N"}
    typed = [c for c in children if c.get("type") in SINGLE_TYPES]
    if len(typed) != 1:
        return None, {"mode": "SINGLE", "n_typed": len(typed),
                      "rejection": ("NO_SINGLE_TYPE_CARRIER" if not typed
                                    else "MULTI_SINGLE_TYPE_AMBIGUOUS")}
    return typed[0], {"mode": "SINGLE", "n_typed": len(typed), "records": [typed[0]["skillid"]],
                      "basis": "句面 大/中ダメージ・一定間隔 ↔ 单发型 type3/22/55/74 恰 1 条"}


def _f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    text = ("%.6f" % f).rstrip("0").rstrip(".")
    return text


def _rows(groups):
    return {r["row_id"]: r for g in groups or [] for s in g.get("skills") or []
            for r in s.get("rows") or []}


def _canon(text):
    import unicodedata
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(text or "")))


def base_and_excluded(rows, row, rule_key, chosen_skillid, raw):
    """同文行 → (base rows, base answers, excluded, same_value_records)。"""
    target = _canon(row.get("japanese"))
    same = [r for r in rows.values() if _canon(r.get("japanese")) == target]
    base = [r for r in same if str(r.get("reference_field") or "").startswith("pattern")
            and r["row_id"] != row["row_id"]]
    base_answers = [{"row_id": r["row_id"], "record_id": a.get("record_id"),
                     "raw_value": a.get("raw_value"),
                     "quantity_kind": a.get("quantity_kind"), "unit": a.get("unit"),
                     "numeric_source": a.get("numeric_source")}
                    for r in base for a in (r.get("answers") or [])
                    if a.get("rule_key") == rule_key]
    excluded, same_value = [], []
    for r in same:
        if r["row_id"] == row["row_id"]:
            continue
        for a in r.get("answers") or []:
            if a.get("rule_key") != rule_key:
                continue
            item = {"row_id": r["row_id"], "reference_field": r.get("reference_field"),
                    "record_id": a.get("record_id"), "raw_value": a.get("raw_value"),
                    "condition_label": a.get("condition_label")}
            if a.get("raw_value") == raw:
                same_value.append(item)
            else:
                excluded.append(item)
    return base, base_answers, excluded, same_value


def evaluate(data, cid, row, rows=None):
    """单行判定（不写入）。返回 dict(accepted, rejection, answer, gates, detail)。"""
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
    chain, err = chain_of(data, cid, adm["gate"])
    if err:
        return {"accepted": False, "rejection": err}
    gates = {"chain": adm["gate"], "pattern_id": chain["pattern_id"],
             "pattern_layer": chain["layer"], "origin": chain["origin"]}
    # 冻结 chain 与实时 chain 一致
    if chain["pattern_id"] != adm["pattern_id"]:
        return {"accepted": False, "rejection": "PATTERN_ID_DRIFT",
                "detail": {"expected": adm["pattern_id"], "actual": chain["pattern_id"]},
                "gates": gates}
    chosen, sel = select(chain, row.get("japanese"))
    gates["selection"] = sel
    if chosen is None:
        return {"accepted": False, "rejection": sel.get("rejection"), "gates": gates}
    if chosen["skillid"] != adm["skillid"] or chosen.get("type") != adm["type"]:
        return {"accepted": False, "rejection": "CHAINTARGET_DRIFT",
                "detail": {"expected": [adm["skillid"], adm["type"]],
                           "actual": [chosen["skillid"], chosen.get("type")]},
                "gates": gates}
    slot = "/" + SLOT[chosen["type"]]
    raw = chosen["params"].get(SLOT[chosen["type"]])
    if raw is None or isinstance(raw, bool) or not isinstance(raw, (int, float)) \
            or not math.isfinite(float(raw)):
        return {"accepted": False, "rejection": "RAW_VALUE_MISSING_OR_NONFINITE",
                "detail": raw, "gates": gates}
    if raw != adm["raw_value"] or slot != adm["field_path"]:
        return {"accepted": False, "rejection": "RAW_VALUE_DRIFT",
                "detail": {"expected": [adm["raw_value"], adm["field_path"]],
                           "actual": [raw, slot]}, "gates": gates}
    gates.update({"skillid": chosen["skillid"], "type": chosen["type"], "raw_value": raw})
    # 同卡基础档位行：同文 pattern* 行同 rule_key 同值
    base, base_answers, excluded, same_value = base_and_excluded(
        rows, row, adm["rule_key"], chosen["skillid"], raw)
    gates["base_rows"] = sorted(r["row_id"] for r in base)
    gates["base_value_match"] = any(a["raw_value"] == raw for a in base_answers)
    gates["base_record_match"] = any(a["record_id"] == chosen["skillid"]
                                     and a["raw_value"] == raw for a in base_answers)
    gates["same_value_records"] = sorted({a["record_id"] for a in same_value
                                          if a["raw_value"] == raw})
    # 卡内同 rule_key 同值的全部记录（含不同文的其他片段行）——7251 同值异记录的核对基准
    gates["card_same_value_records"] = sorted({
        a.get("record_id") for r in rows.values() for a in (r.get("answers") or [])
        if a.get("rule_key") == adm["rule_key"] and a.get("raw_value") == raw})
    if not gates["base_value_match"]:
        return {"accepted": False, "rejection": "BASE_ROW_VALUE_MISMATCH",
                "detail": {"base_answers": base_answers, "raw": raw}, "gates": gates}
    if not gates["base_record_match"]:
        # 同值异记录（7251）：要求冻结表登记，且卡内同值记录集合与登记一致
        if adm.get("record_note") != "VALUE_UNIQUE_RECORD_NOT_UNIQUE" \
                or sorted(adm.get("same_value_records") or []) \
                != gates["card_same_value_records"]:
            return {"accepted": False, "rejection": "BASE_ROW_RECORD_MISMATCH",
                    "detail": {"base_answers": base_answers, "raw": raw,
                               "card_same_value_records": gates["card_same_value_records"]},
                    "gates": gates}
    # 链外档位值必须与冻结表逐项相等（不新增、不遗漏）
    got_exc = sorted((e["record_id"], e["raw_value"]) for e in excluded)
    want_exc = sorted((r, v) for r, v in adm["excluded"])
    gates["excluded_values"] = [{"row_id": e["row_id"], "reference_field": e["reference_field"],
                                 "record_id": e["record_id"], "raw_value": e["raw_value"]}
                                for e in excluded]
    if got_exc != want_exc:
        return {"accepted": False, "rejection": "EXCLUDED_SET_MISMATCH",
                "detail": {"expected": want_exc, "actual": got_exc}, "gates": gates}
    # 既有同键答案不覆盖（幂等）
    for a in row.get("answers") or []:
        if (a.get("rule_key") == adm["rule_key"]
                and a.get("record_id") == chosen["skillid"]
                and a.get("field_path") == slot):
            return {"accepted": False, "rejection": "ALREADY_ANSWERED", "gates": gates}
    # 继承同值基础答案的表述字段（同 rule_key / 同值；记录可异）
    ref = next((a for a in base_answers if a["record_id"] == chosen["skillid"]), None) \
        or next((a for a in base_answers if a["raw_value"] == raw), None)
    qk = (ref or {}).get("quantity_kind")
    unit = (ref or {}).get("unit") or "倍率（相对B）"
    numeric_source = (ref or {}).get("numeric_source") or "原生静态及受控局部规则＋实际父子边"
    num = _num(raw)
    # 只列「与选中值同值」的基础档位行（异值档位行走 excluded，不写成基础行）
    value_base_rows = sorted({a["row_id"] for a in base_answers if a["raw_value"] == raw})
    gates["value_base_rows"] = value_base_rows
    base_ids = "、".join(value_base_rows) or "（无）"
    if gates["excluded_values"]:
        exc_txt = "、".join("%s（%s）" % (_num(e["raw_value"]), e["record_id"])
                           for e in gates["excluded_values"])
        exc_tail = "链外档位值 %s已排除、不计入本行" % exc_txt
    else:
        exc_tail = "本档为唯一档位（无链外档位值）"
    note_unique = ""
    if adm.get("record_note") == "VALUE_UNIQUE_RECORD_NOT_UNIQUE":
        note_unique = "；同值异记录：%s 均为 %s（记录选取不唯一，值唯一）" % (
            "/".join(str(x) for x in adm["same_value_records"]), num)
    value = ("%s：%s（相对B；对象：敌方；镜像行按原始链定源到 bossskill %s type%s %s，"
             "倍率见同卡基础档位行 %s；%s%s）"
             % (qk or "单次对敌伤害输入倍率", num, chosen["skillid"], chosen["type"], slot,
                base_ids, exc_tail, note_unique))
    conditions_raw = {k: chain["pattern"].get(k) for k in
                      ("flag", "hpend", "priority", "scost", "sname",
                       "skillid0", "skillid1", "skillid2", "skillid3")
                      if chain["pattern"].get(k) is not None}
    conditions_raw["sinfo"] = chain["pattern"].get("sinfo")
    marker = {
        "scope": SCOPE,
        "gate": adm["gate"],
        "row_id": rid,
        "rule_key": adm["rule_key"],
        "record_id": chosen["skillid"],
        "layer": "CACHE",
        "field_path": slot,
        "pattern_id": chain["pattern_id"],
        "pattern_slot": ("patternid0" if adm["gate"] == "DENJU_CHAIN" else "pattern0"),
        "origin": chain["origin"],
        "selection": sel,
        "base_row_ids": value_base_rows,
        "same_text_base_row_ids": gates["base_rows"],
        "base_record_ids": sorted({a["record_id"] for a in base_answers}),
        "record_selection": adm.get("record_note") or "RECORD_UNIQUE",
        "excluded_values": [[e["record_id"], e["raw_value"]] for e in gates["excluded_values"]],
        "value_basis": ("同值已在同卡基础档位行同 rule_key 答案中披露；本行只做行级绑定，"
                        "不新增唯一数值"),
        "association": "推断",
        "native_evidence": "none（本批不新增原生点；片段判别为类型语义＋25 项一致性推断）",
        "conditions_raw": conditions_raw,
    }
    binding = {"g1_b1_binding": marker,
               "fields": [{"f": slot, "raw": raw}]}
    answer = {
        "value": value,
        "quantity_kind": qk or ("单次对敌伤害输入倍率"
                                if chosen["type"] in (3, 22, 105, 110) else
                                "直接范围伤害输入倍率" if chosen["type"] == 74 else
                                "激光伤害输入倍率"),
        "unit": unit,
        "raw_value": raw,
        "effective_float32": _f32(raw),
        "quantitative": True,
        "numeric_source": numeric_source,
        "numeric_evidence": "确认",
        "association_evidence": "推断",
        "answer_status": "CONFIRMED_FORMULA_ONLY",
        "evidence_scope": "BY_TYPE_EXTRAPOLATED",
        "rule_key": adm["rule_key"],
        "field_path": slot,
        "table": "bossskill",
        "record_id": chosen["skillid"],
        "layer": "CACHE",
        "source": {
            "table": "bossskill",
            "record_id": chosen["skillid"],
            "layer": "CACHE",
            "field_path": slot,
            "source_key": "CACHE/bossinfo.data5.json.raw",
            "original_file": "output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw",
            "json_pointer": f"/bossinfo/bossskill/{chosen['index']}",
            "field": slot,
            "field_json_pointer": f"/bossinfo/bossskill/{chosen['index']}{slot}",
            "record_key": f"CACHE/bossinfo.data5.json.raw#/bossinfo/bossskill/{chosen['index']}",
            "source_resolution": "RESOLVED_EXACT_DECODED_RECORD",
            "note": ("按解码 JSON 的 bossskill.skillid 唯一命中；本行原始链"
                     "（%s）定源，不是同文复制" % ("denju.patternid0" if adm["gate"] == "DENJU_CHAIN"
                                                else "charainfo.pattern0")),
        },
        "context": "镜像段（传授/skilltext 行）",
        "condition_label": "pattern%s / pattern %s 被选中时" % (
            "id0" if adm["gate"] == "DENJU_CHAIN" else "0", chain["pattern_id"]),
        "binding": binding,
        "target": "敌",
        "note": ("仅局部伤害输入公式（B=getBasicSkillAttack(true) 等沿用原规则定义），未验证"
                 "最终扣血、保证命中与运行时选档；抽取自本行原始链记录，非最终伤害。父条件"
                 "原值见 binding.conditions_raw；缺失字段不补零；链外档位值已登记排除。"),
        "evidence": ["docs/tasks/20261029-g1-b1-mirror-batch.md",
                     "output/character_skills/g1_b1_20261029/README.md"],
    }
    return {"accepted": True, "rejection": None, "answer": answer, "gates": gates,
            "detail": None}


def _append(row, answer):
    key = lambda a: (a.get("rule_key"), a.get("record_id"), a.get("field_path"))
    if any(key(a) == key(answer) for a in row.get("answers") or []):
        return False
    row.setdefault("answers", []).append(answer)
    row["row_class"] = "A"
    row["evidence"] = "推断"
    row["evidence_label"] = ("推断（G1-B1 镜像行绑定：原始链定源；倍率见同卡基础档位行，"
                             "不新增唯一数值）")
    row["partial"] = True
    row["evidence_scope"] = list(dict.fromkeys(list(row.get("evidence_scope") or [])
                                              + ["BY_TYPE_EXTRAPOLATED"]))
    # 未知原因：删掉本批已不成立的通用行（原文无值/无可用数值/仅原文数字），
    # 换成本批准确口径；其余既有原因（如 charainfo 同 HP 组 t13 分支披露）原样保留。
    stale = {"原文未提供该效果数值，尚无已审定的句内字段归属",
             "此描述尚无可适用的已确认数值或新增机制证据",
             "尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应"}
    reasons = [r for r in (row.get("unknown_reasons") or []) if r not in stale]
    try:
        import effect_ledger as _L
        residual = [w for w in _L._RESIDUAL_MECHANISM_WORDS
                    if w in str(row.get("japanese") or "")]
    except Exception:  # noqa: BLE001 - 反向依赖不可用时只写通用口径
        residual = []
    reasons.append("镜像行按原始链定源写入伤害倍率（同卡基础档位行同值、链外档位值已排除）；"
                   "同句其余机制%s仍未解析，账本行仍为拆分待核查。"
                   % (("（登记残差词：%s）" % "、".join(residual)) if residual
                      else "（未被主张覆盖的子句，如 弾き飛ばす）"))
    row["unknown_reasons"] = reasons
    marker = row.setdefault("inference_g1_b1", {"scope": SCOPE, "bindings": []})
    b = answer["binding"]["g1_b1_binding"]
    marker["bindings"].append({
        "gate": b["gate"], "pattern_id": b["pattern_id"], "record_id": b["record_id"],
        "rule_key": b["rule_key"], "field_path": b["field_path"],
        "base_row_ids": b["base_row_ids"], "record_selection": b["record_selection"],
        "excluded_values": b["excluded_values"]})
    return True


def apply_to_groups(data, cid, groups):
    """正式页消费：为 25 行冻结准入表写入镜像行绑定答案（不覆盖/不删除既有答案）。"""
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
    for rid, adm in ADMITTED.items():
        if adm["cid"] != cid:
            continue
        row = rows.get(rid)
        if row is None:
            report["rejections"].append({"row_id": rid, "reason": "ROW_NOT_FOUND"})
            continue
        report["evaluated"] += 1
        res = evaluate(data, cid, row, rows=rows)
        if not res["accepted"]:
            if res["rejection"] == "ALREADY_ANSWERED":
                report["skipped_existing"] += 1
            else:
                report["rejections"].append({"row_id": rid, "reason": res["rejection"],
                                             "detail": res.get("detail")})
            continue
        if _append(row, res["answer"]):
            report["answers_added"] += 1
            report["additions"].append({
                "row_id": rid, "record_id": res["answer"]["record_id"],
                "rule_key": res["answer"]["rule_key"],
                "field_path": res["answer"]["field_path"],
                "raw_value": res["answer"]["raw_value"]})
        else:
            report["skipped_existing"] += 1
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="G1-B1 镜像行绑定：只读探针（单行/单卡）")
    ap.add_argument("--cid", type=int, help="单卡重算（读当前正式页，不写入）")
    ap.add_argument("--row-id", help="单行检测")
    ap.add_argument("--all", action="store_true", help="重算冻结准入表全部 25 行")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)
    root = Path(".").resolve()
    import card_page_data as D
    if args.row_id:
        cids = [int(str(args.row_id).split("-", 1)[0])]
    elif args.cid:
        cids = [args.cid]
    else:
        cids = sorted(ADMITTED_CIDS)
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
            out.append({"row_id": adm["row_id"], "accepted": res["accepted"],
                        "rejection": res["rejection"],
                        "record_id": (res.get("answer") or {}).get("record_id"),
                        "raw_value": (res.get("answer") or {}).get("raw_value"),
                        "value": (res.get("answer") or {}).get("value"),
                        "page_answers": len(row.get("answers") or []),
                        "page_row_class": row.get("row_class"),
                        "gates": res.get("gates")})
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for item in out:
            print(("OK  " if item["accepted"] else "REJ "), item["row_id"],
                  item.get("record_id"), item.get("raw_value"), item.get("rejection") or "")
    return 0 if all(i["accepted"] for i in out) else 1


if __name__ == "__main__":
    raise SystemExit(_main())
