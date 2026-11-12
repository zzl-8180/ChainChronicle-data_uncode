# -*- coding: utf-8 -*-
"""复核 13-16：范围格数、攻击间隔显示、超上限标志位、缓存省略 0 字段。

结果写 work/refcheck_20261023_lead/verify/flags_units_claims.json。
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_common import Db, apk_table, cache_table, out, write_json  # noqa: E402


def claim13_grid(db):
    """1 格 = 1.5 游戏单位：检查我方已知的几何槽取值是否为 1.5 / 0.75 的整数倍。"""
    pairs = [
        ("bossskill", 3, "skillparam2", "范围长度"),
        ("bossskill", 22, "skillparam2", "前方到达延长"),
        ("bossskill", 22, "skillparam3", "横向宽度"),
        ("bossskill", 110, "skillparam2", "范围长度"),
        ("bossskill", 112, "skillparam2", "爆炸半径"),
        ("bossskill", 112, "skillparam3", "爆炸半径"),
        ("bossskill", 47, "skillparam2", "爆炸半径"),
        ("bossskill", 47, "skillparam3", "爆炸半径"),
        ("bossskill", 105, "skillparam2", "范围长度"),
        ("bossskill", 105, "skillparam3", "范围宽度"),
    ]
    res = []
    for table, ty, field, label in pairs:
        src = db.bossskill if table == "bossskill" else db.skilllist
        key = "skillid0" if table == "bossskill" else "ability"
        vals = [r[field] for r in src if r.get(key) == ty and field in r]
        if not vals:
            res.append({"table": table, "type": ty, "field": field, "label": label, "n": 0})
            continue
        m15 = sum(1 for v in vals if abs(v / 1.5 - round(v / 1.5)) < 1e-9)
        m075 = sum(1 for v in vals if abs(v / 0.75 - round(v / 0.75)) < 1e-9)
        res.append({
            "table": table, "type": ty, "field": field, "label": label,
            "n": len(vals), "multiples_of_1.5": m15,
            "ratio_1.5": round(m15 / len(vals), 4),
            "multiples_of_0.75": m075, "ratio_0.75": round(m075 / len(vals), 4),
            "top": Counter(vals).most_common(8),
            "distinct": len(set(vals)),
        })
    return {
        "slots_checked": res,
        "note": "我方 rules.json / 全部 character_skills 文档内均无「格」单位规则；"
                "本检查只能说明几何槽取值是否与 1.5/0.75 整除相容，不能证明 1 格 = 1.5 单位。",
    }


def claim14_interval(db):
    ca = db.charainfo
    atk_cache = Counter(r.get("atkspeed") for r in ca if "atkspeed" in r)
    apk = apk_table("_mdCharacter.json")["charainfo"]
    atk_apk = Counter(round(r.get("atkspeed"), 4) for r in apk if r.get("atkspeed") is not None)
    # 2012 p6 → 攻击间隔
    recs = [r for r in db.skilllist if r.get("ability") == 2012 and "param6" in r]
    rows = []
    for r in recs:
        cid = (r["skillid"] - 40000000) // 100
        c = db.cid_index.get(cid) or {}
        at = c.get("atkspeed")
        rows.append({"skillid": r["skillid"], "p6": r["param6"], "cid": cid,
                     "char": c.get("name"), "atkspeed": at,
                     "interval": None if at is None else at * (1 + r["param6"]),
                     "p7": r.get("param7"), "p8": r.get("param8")})
    prod = Counter(round(r["interval"], 6) for r in rows if r["interval"] is not None)
    # 1.505 / 1.575 复现搜索：atkspeed(缓存+APK) × 间隔倍率（2012 p6／type57 p4／type7 p7）
    multipliers = {round(1 + r["param6"], 6) for r in recs}
    for ty, field in ((57, "param4"), (7, "param7")):
        multipliers |= {round(r[field], 6) for r in db.skilllist
                        if r.get("ability") == ty and field in r}
    multipliers = sorted(multipliers)
    atkvals = sorted({round(r.get("atkspeed"), 4) for r in apk if r.get("atkspeed")} |
                     {round(v, 4) for v in atk_cache if v})
    repro = {}
    for target in (1.0125, 1.05, 1.505, 1.575, 0.9):
        hits = []
        for at in atkvals:
            for m in multipliers:
                if abs(at * m - target) < 1e-6:
                    hits.append({"atkspeed": at, "multiplier": m})
        repro[str(target)] = hits
    # 数据里是否本来就存在 1.505/1.575 这样的值（作为其它类型的原始参数）
    raw_1505 = []
    for r in db.skilllist:
        for k, v in r.items():
            if k.startswith("param") and isinstance(v, (int, float)) and abs(v - 1.505) < 1e-9:
                raw_1505.append([r["skillid"], r.get("ability"), k, v])
    raw_1575 = []
    for r in db.skilllist:
        for k, v in r.items():
            if k.startswith("param") and isinstance(v, (int, float)) and abs(v - 1.575) < 1e-9:
                raw_1575.append([r["skillid"], r.get("ability"), k, v])
    return {
        "atkspeed_cache": {"present": sum(atk_cache.values()), "distinct": len(atk_cache),
                           "values": sorted([v, n] for v, n in atk_cache.items())},
        "atkspeed_apk": {"present": sum(atk_apk.values()), "distinct": len(atk_apk),
                         "values": sorted([[v, n] for v, n in atk_apk.items()])},
        "sa2012_p6_records": len(rows),
        "sa2012_interval_dist": dict(prod),
        "sa2012_rows": rows,
        "reproduce_targets": repro,
        "reproduce_scope": {"atkspeed_values": atkvals, "multipliers": multipliers,
                            "note": "atkspeed 取缓存+APK 两源；倍率取 SA2012 (1+p6)、type57 p4、type7 p7 的全部出现值。"},
        "raw_1.505_occurrences": raw_1505,
        "raw_1.575_occurrences": raw_1575,
        "truncation_check": {
            "1.0125_floor_0.1": 1.0, "1.05_floor_0.1": 1.0,
            "1.505_floor_0.1": 1.5, "1.575_floor_0.1": 1.5, "0.9_floor_0.1": 0.9,
            "note": "所声称的 5 个显示值全部等于 floor(x/0.1)*0.1；round 会把 1.575 变成 1.6，"
                    "故声称的口径是「截断」而非「四舍五入」。",
        },
    }


HEAL_BITS = {256: 20, 512: 40, 1024: 60, 2048: 80, 4096: 100}


def claim15_flags(db):
    bs = db.bossskill
    sl = db.skilllist
    out_ = {}

    def flags_of(src, key):
        d = {}
        for suf in ("0_0", "0_1", "1_0", "1_1"):
            field = key + suf
            c = Counter(r[field] for r in src if field in r)
            d[field] = {"present": sum(c.values()), "distinct": len(c),
                        "top": c.most_common(10)}
        return d

    out_["bossskill_flags"] = flags_of(bs, "skillflag")
    out_["skilllist_flags"] = flags_of(sl, "flag")
    # 逐类型：哪些类型用 skillflag1_1 / skillflag0_1
    out_["bossskill_types_with_flag1_1"] = Counter(
        r.get("skillid0") for r in bs if "skillflag1_1" in r).most_common()
    out_["bossskill_types_with_flag0_1"] = Counter(
        r.get("skillid0") for r in bs if "skillflag0_1" in r).most_common()
    out_["skilllist_types_with_flag1_1"] = Counter(
        r.get("ability") for r in sl if "flag1_1" in r).most_common()
    out_["skilllist_types_with_flag0_1"] = Counter(
        r.get("ability") for r in sl if "flag0_1" in r).most_common()
    # type27 / type64 / ability21
    for name, ty, table, field in (
        ("type27", 27, "bossskill", "skillflag0_1"),
        ("type64", 64, "bossskill", "skillflag1_1"),
        ("ability21", 21, "skilllist", "flag0_1"),
    ):
        src = bs if table == "bossskill" else sl
        key = "skillid0" if table == "bossskill" else "ability"
        recs = [r for r in src if r.get(key) == ty]
        out_[name] = {
            "n": len(recs), "field": field,
            "present": sum(1 for r in recs if field in r),
            "values": dict(Counter(r[field] for r in recs if field in r)),
            "other_flag_fields": {f: sum(1 for r in recs if f in r)
                                  for f in ("skillflag0_1", "skillflag1_1",
                                            "flag0_1", "flag1_1")},
        }
    # 超上限文本 vs 标志（skilllist）
    def real(r):
        t = r.get("text") or ""
        return t if len(t) > 25 and "サブアビリティ" not in t else ""
    has = [r for r in sl if "上限を超えて" in real(r)]
    out_["skilllist_overheal_text"] = {
        "records": len(has),
        "by_type": Counter(r["ability"] for r in has).most_common(),
        "flag0_1_present": sum(1 for r in has if "flag0_1" in r),
        "flag0_1_values": dict(Counter(r["flag0_1"] for r in has if "flag0_1" in r)),
        "flag1_1_present": sum(1 for r in has if "flag1_1" in r),
        "flag1_1_values": dict(Counter(r["flag1_1"] for r in has if "flag1_1" in r)),
        "neither": sum(1 for r in has if "flag0_1" not in r and "flag1_1" not in r),
    }
    # 3000 专项：文本「上限を超えて」 vs flag1_1
    t3 = [r for r in sl if r.get("ability") == 3000 and real(r)]
    with_kw = [r for r in t3 if "上限を超えて" in real(r)]
    without = [r for r in t3 if "上限を超えて" not in real(r)]
    out_["type3000_overheal"] = {
        "records_with_text": len(t3),
        "with_kw": len(with_kw), "with_kw_flag1_1": sum(1 for r in with_kw if "flag1_1" in r),
        "without_kw": len(without), "without_kw_flag1_1": sum(1 for r in without if "flag1_1" in r),
        "with_kw_values": dict(Counter(r["flag1_1"] for r in with_kw if "flag1_1" in r)),
    }
    # 反例：非超上限位的位值
    counter = []
    for src, key, field, table in (
        (bs, "skillid0", "skillflag0_1", "bossskill"),
        (sl, "ability", "flag0_1", "skilllist"),
    ):
        for v, n in Counter(r[field] for r in src if field in r).items():
            if v not in HEAL_BITS:
                counter.append({"table": table, "field": field, "value": v, "n": n})
    out_["non_overheal_bits"] = counter
    out_["bit_mapping_claim"] = HEAL_BITS
    return out_


def claim16_zero(db):
    ca = db.charainfo
    missing = [r for r in ca if "jobtype" not in r]
    apk = {r["cid"]: r for r in apk_table("_mdCharacter.json")["charainfo"]}
    match0 = 0
    notfound = 0
    other = []
    for r in missing:
        a = apk.get(r["cid"])
        if a is None:
            notfound += 1
            continue
        jt = a.get("jobtype")
        if jt == 0:
            match0 += 1
        else:
            other.append([r["cid"], r.get("name"), jt])
    wl = cache_table("weaponlist")["weaponlist"]
    wt = Counter(r.get("type") for r in wl if "type" in r)
    miss_w = [r for r in wl if "type" not in r]
    # 缺失 type 的武器名是否都是「斩」类（刀剑）
    sword_markers = ("剣", "ソード", "ブレード", "セイバー", "ダガー", "カタナ", "刀", "レイピア")
    swordish = sum(1 for r in miss_w if any(m in (r.get("name") or "") for m in sword_markers))
    return {
        "jobtype_cache": {"records": len(ca), "present": len(ca) - len(missing),
                          "missing": len(missing),
                          "values": dict(Counter(r.get("jobtype") for r in ca if "jobtype" in r))},
        "jobtype_missing_vs_apk": {"missing": len(missing), "apk_found": len(missing) - notfound,
                                   "apk_jobtype_0": match0, "apk_jobtype_nonzero": other,
                                   "apk_notfound": notfound},
        "jobtype_present_vs_apk": {
            "same": sum(1 for r in ca if "jobtype" in r and r["cid"] in apk
                        and apk[r["cid"]].get("jobtype") == r["jobtype"]),
            "diff": sum(1 for r in ca if "jobtype" in r and r["cid"] in apk
                        and apk[r["cid"]].get("jobtype") != r["jobtype"]),
        },
        "weaponlist_type": {"records": len(wl), "present": sum(wt.values()),
                            "missing": len(miss_w), "values": dict(wt),
                            "has_zero": 0 in wt,
                            "missing_sword_name_like": swordish,
                            "missing_samples": [r.get("name") for r in miss_w[:12]]},
        "apk_jobtype_values": dict(Counter(r.get("jobtype") for r in apk.values())),
    }


def main():
    db = Db()
    res = {
        "generated_by": "scripts/refcheck_20261023_lead/verify_02_flags_units.py",
        "claim13_grid_unit": claim13_grid(db),
        "claim14_attack_interval": claim14_interval(db),
        "claim15_overheal_flags": claim15_flags(db),
        "claim16_zero_omission": claim16_zero(db),
    }
    p = write_json(out("flags_units_claims.json"), res)
    print("wrote", p)
    print("grid slots:", len(res["claim13_grid_unit"]["slots_checked"]))
    print("interval repro:", {k: len(v) for k, v in
                              res["claim14_attack_interval"]["reproduce_targets"].items()})
    print("jobtype missing vs apk:",
          res["claim16_zero_omission"]["jobtype_missing_vs_apk"]["apk_jobtype_0"],
          "of", res["claim16_zero_omission"]["jobtype_missing_vs_apk"]["missing"])


if __name__ == "__main__":
    main()
