# -*- coding: utf-8 -*-
"""复核 1-12：参数槽语义与取值分布（skilllist / bossskill）。

只读 output/cache_full_20261015_v3/decoded 与 output/base_master，
结果写 work/refcheck_20261023_lead/verify/params_claims.json。
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_common import Db, cache_table, out, pstr, val_counter, write_json  # noqa: E402


def real_text(r):
    """记录自带的日文效果描述（排除 'xxxのサブアビリティ' 这类元数据占位）。"""
    t = r.get("text") or ""
    return t if len(t) > 25 and "サブアビリティ" not in t else ""


def sel(db, table, ty):
    src = db.skilllist if table == "skilllist" else db.bossskill
    key = "ability" if table == "skilllist" else "skillid0"
    return [r for r in src if r.get(key) == ty]


def cid_from_skillid(sid):
    """40000000 + cid*100 + n 命名规则（用于定位 2012/sub 能力的持有 cid）。"""
    idx = sid - 40000000
    if idx <= 0:
        return None
    return idx // 100


def claim1_1009(db):
    recs = sel(db, "skilllist", 1009)
    names = []
    for r in recs:
        nm = re.sub(r"\s+", " ", (r.get("name") or "").replace("\n", " "))
        names.append([r["skillid"], nm, {k: v for k, v in r.items() if k.startswith("param")}])
    # 技能名自带显式倍率范围的两条（dev 命名），用 k*m_k 公式回算比对
    checks = []
    for sid, base, p6, p7, lo, hi in (
        (137002, 0.04, 0.75, 0.6, 1.04, 1.072),
        (137003, 0.125, 0.75, 0.6, 1.125, 1.225),
    ):
        k1 = 1 + base * 1
        k2 = 1 + base * 2 * p6
        k3 = 1 + base * 3 * p7
        checks.append({
            "skillid": sid, "name_range": [lo, hi],
            "k1": round(k1, 6), "k2": round(k2, 6), "k3": round(k3, 6),
            "k1_matches_min": abs(k1 - lo) < 1e-9, "k3_matches_max": abs(k3 - hi) < 1e-9,
            "k3_over_k1": round((k3 - 1) / (k1 - 1), 6),
        })
    return {
        "table": "skilllist", "type": 1009, "n": len(recs),
        "slots": val_counter(recs),
        "records": names,
        "name_range_checks": checks,
        "p0_distinct": dict(Counter(r.get("param0") for r in recs)),
        "note": "p0∈{1,2} 与属性无关；m_k 存 p6(k=2)/p7(k=3)，无字段承载 k=1（m_1 恒 1）。",
    }


def claim2_116(db):
    recs = sel(db, "bossskill", 116)
    p1 = Counter(r.get("skillparam1") for r in recs if "skillparam1" in r)
    lt1 = sum(n for v, n in p1.items() if v is not None and v < 1)
    return {
        "table": "bossskill", "type": 116, "n": len(recs),
        "slots": val_counter(recs, "skillparam"),
        "p1_present": sum(p1.values()), "p1_missing": len(recs) - sum(p1.values()),
        "p1_lt_1": lt1, "p1_lt_1_ratio": round(lt1 / len(recs), 4),
        "p1_dist": sorted([[v, n] for v, n in p1.items()], key=lambda x: -(x[1] or 0)),
        "p6_15": sum(1 for r in recs if r.get("skillparam6") == 1.5),
        "p8_05": sum(1 for r in recs if r.get("skillparam8") == 0.5),
        "p2_dist": sorted([[v, n] for v, n in Counter(
            r.get("skillparam2") for r in recs if "skillparam2" in r).items()],
            key=lambda x: -(x[1] or 0)),
        "samples": [[r["skillid"], pstr(r, "skillparam")] for r in recs[:8]],
    }


def claim3_1074(db):
    recs = sel(db, "skilllist", 1074)
    return {
        "table": "skilllist", "type": 1074, "n": len(recs),
        "slots": val_counter(recs),
        "records": [{"skillid": r["skillid"], "name": r.get("name"),
                     "cid": cid_from_skillid(r["skillid"]),
                     "char": (db.cid_index.get(cid_from_skillid(r["skillid"])) or {}).get("name"),
                     "params": {k: v for k, v in r.items() if k.startswith("param")}}
                    for r in recs],
        "identical_values": len({tuple(sorted((k, v) for k, v in r.items() if k.startswith("param")))
                                 for r in recs}) == 1,
    }


def claim4_1051(db):
    recs = sel(db, "skilllist", 1051)
    p6 = [r for r in recs if r.get("param6") == 1]
    nop6 = [r for r in recs if "param6" not in r]
    paired = []
    for r in p6:
        paired.append([r["skillid"], r.get("name"),
                       {k: v for k, v in r.items() if k.startswith("param")}])
    return {
        "table": "skilllist", "type": 1051, "n": len(recs),
        "slots": val_counter(recs),
        "p6_eq_1": len(p6), "p6_other": sum(1 for r in recs if "param6" in r and r["param6"] != 1),
        "p6_1_all_p1_negative": sum(1 for r in p6 if r.get("param1", 0) < 0),
        "p6_1_p3_positive": sum(1 for r in p6 if r.get("param3", 0) > 0),
        "no_p6_all_p1_positive": sum(1 for r in nop6 if r.get("param1", 0) > 0),
        "no_p6_p3_negative": sum(1 for r in nop6 if r.get("param3", 0) < 0),
        "no_p6": len(nop6),
        "enemy_records": paired,
        "p0_dist": dict(Counter(r.get("param0") for r in recs)),
    }


def claim5_58(db):
    recs = sel(db, "skilllist", 58)
    rows = []
    for r in recs:
        cid = cid_from_skillid(r["skillid"])
        c = db.cid_index.get(cid) or {}
        rows.append({
            "skillid": r["skillid"], "name": r.get("name"),
            "params": {k: v for k, v in r.items() if k.startswith("param")},
            "cid": cid, "char_name": c.get("name"), "jobtype": c.get("jobtype"),
            "rarity": c.get("rarity"),
        })
    return {
        "table": "skilllist", "type": 58, "n": len(recs),
        "p0_all_1": all(r.get("param0") == 1 for r in recs),
        "p4_dist": dict(Counter(r.get("param4") for r in recs)),
        "p5_dist": dict(Counter(r.get("param5") for r in recs)),
        "p6_values": [r.get("param6") for r in recs if "param6" in r],
        "p7_values": [r.get("param7") for r in recs if "param7" in r],
        "records": rows,
    }


def claim6_2012(db):
    recs = sel(db, "skilllist", 2012)
    both = [r for r in recs if "param4" in r and "param5" in r]
    p6 = [r for r in recs if "param6" in r]
    prod = []
    for r in p6:
        cid = cid_from_skillid(r["skillid"])
        c = db.cid_index.get(cid) or {}
        at = c.get("atkspeed")
        prod.append({
            "skillid": r["skillid"], "p6": r["param6"], "cid": cid,
            "char": c.get("name"), "atkspeed": at,
            "interval": round(at * (1 + r["param6"]), 6) if at else None,
            "p7": r.get("param7"), "p8": r.get("param8"),
        })
    intervals = Counter(str(p["interval"]) for p in prod if p["interval"] is not None)
    # 持有卡正文关键词核对（p4/p5 与 p6 各自）
    p45 = [r for r in recs if "param4" in r]
    owner_cr = owner_cd = 0
    for r in p45:
        cid = cid_from_skillid(r["skillid"])
        t = (db.cid_index.get(cid) or {}).get("skilltext") or ""
        owner_cr += 1 if "クリティカル発生率" in t else 0
        owner_cd += 1 if "クリティカル威力" in t else 0
    p6_owner_spd = 0
    for r in p6:
        cid = cid_from_skillid(r["skillid"])
        t = (db.cid_index.get(cid) or {}).get("skilltext") or ""
        p6_owner_spd += 1 if "攻撃速度" in t else 0
    return {
        "table": "skilllist", "type": 2012, "n": len(recs),
        "slots": val_counter(recs),
        "p4_present": sum(1 for r in recs if "param4" in r),
        "p5_present": sum(1 for r in recs if "param5" in r),
        "both_p4_p5_equal": sum(1 for r in both if r["param4"] == r["param5"]),
        "both_p4_p5": len(both),
        "p45_owner_text": {"n": len(p45), "mentions_crit_rate": owner_cr,
                           "mentions_crit_dmg": owner_cd},
        "p6_owner_text": {"n": len(p6), "mentions_attack_speed": p6_owner_spd},
        "p6_present": len(p6), "p6_dist": dict(Counter(r["param6"] for r in p6)),
        "p6_interval_products": prod,
        "interval_dist": dict(intervals),
        "claimed_examples": {"1.0125": intervals.get("1.0125", 0),
                             "1.05": intervals.get("1.05", 0),
                             "1.505": intervals.get("1.505", 0),
                             "1.575": intervals.get("1.575", 0),
                             "0.9": intervals.get("0.9", 0)},
    }


def claim7_3000(db):
    recs = sel(db, "skilllist", 3000)
    p4 = [r for r in recs if "param4" in r]
    ratio_ok = sum(1 for r in p4 if "param1" in r and abs(r["param4"] + r["param1"] / 4) < 1e-12)
    ratio_checked = sum(1 for r in p4 if "param1" in r)
    withtext = [(r, real_text(r)) for r in recs if real_text(r)]

    def stat(kw):
        hit = [r for r, t in withtext if kw in t]
        nohit = [r for r, t in withtext if kw not in t]
        return {
            "text_with": len(hit),
            "text_with_slot": sum(1 for r in hit if kw_slot[kw] in r),
            "text_without": len(nohit),
            "text_without_slot": sum(1 for r in nohit if kw_slot[kw] in r),
        }

    kw_slot = {"防御力": "param4", "移動速度": "param3", "クリティカル威力": "param8",
               "攻撃力": "param1", "上限を超えて": "flag1_1"}
    corr = {kw: stat(kw) for kw in kw_slot}
    ex = []
    for r, t in withtext:
        if "防御力" in t and "攻撃力" not in t:
            ex.append([r["skillid"], {k: v for k, v in r.items() if k.startswith("param")},
                       t[:110].replace("\n", " ")])
    return {
        "table": "skilllist", "type": 3000, "n": len(recs),
        "slots": val_counter(recs),
        "p4_present": len(p4), "p4_dist": dict(Counter(r["param4"] for r in p4)),
        "p4_equals_negative_p1_over_4": [ratio_ok, ratio_checked],
        "text_param_correlation": corr,
        "defence_only_examples": ex[:6],
        "records_with_real_text": len(withtext),
    }


def claim8_99(db):
    recs = sel(db, "skilllist", 99)
    dev = []
    for r in recs:
        nm = r.get("name") or ""
        if "DOWN" in nm.upper() or "デバフ" in nm:
            dev.append([r["skillid"], nm, {k: v for k, v in r.items() if k.startswith("param")}])
    p7 = [r.get("param7") for r in recs if "param7" in r]
    p8 = [r.get("param8") for r in recs if "param8" in r]
    p9 = [r.get("param9") for r in recs if "param9" in r]
    return {
        "table": "skilllist", "type": 99, "n": len(recs),
        "slots": val_counter(recs),
        "p7_all_negative": all(v < 0 for v in p7), "p7_n": len(p7),
        "p8_all_negative": all(v < 0 for v in p8), "p8_n": len(p8),
        "p9_all_positive": all(v > 0 for v in p9), "p9_n": len(p9),
        "p8_outliers": [[r["skillid"], r["param8"]] for r in recs
                        if r.get("param8") is not None and abs(r["param8"]) > 1],
        "dev_named": dev,
    }


def claim9_13(db):
    recs = sel(db, "bossskill", 13)
    eq_p2_half = sum(1 for r in recs
                     if abs(r.get("skillparam2", 9) * 2 - r.get("skillparam1", 8)) < 1e-12)
    eq_p6_p2 = sum(1 for r in recs if r.get("skillparam6") == r.get("skillparam2"))
    return {
        "table": "bossskill", "type": 13, "n": len(recs),
        "slots": val_counter(recs, "skillparam"),
        "p2_equals_p1_half": [eq_p2_half, len(recs)],
        "p6_equals_p2": [eq_p6_p2, sum(1 for r in recs if "skillparam6" in r)],
        "p6_missing": sum(1 for r in recs if "skillparam6" not in r),
        "p0_p4_p5_absent": {k: sum(1 for r in recs if "skillparam" + k in r)
                            for k in ("0", "4", "5", "7", "8", "9")},
    }


def claim10_28(db):
    recs = sel(db, "skilllist", 28)
    with345 = [r for r in recs if "param3" in r or "param4" in r or "param5" in r]
    equal345 = sum(1 for r in with345
                   if r.get("param3") == r.get("param4") == r.get("param5"))
    return {
        "table": "skilllist", "type": 28, "n": len(recs),
        "slots": val_counter(recs),
        "p0_to_p2_range": {
            "p0": [min(r[k] for r in recs if k in r), max(r[k] for r in recs if k in r)]
            for k in ("param0", "param1", "param2")},
        "terrain_records": len(with345), "terrain_p345_equal": equal345,
        "p6_dist": dict(Counter(r.get("param6") for r in recs if "param6" in r)),
        "p9_dist": dict(Counter(r.get("param9") for r in recs if "param9" in r)),
        "p6_4_records": [[r["skillid"], r.get("name")] for r in recs if r.get("param6") == 4],
    }


def claim11_6(db):
    recs = sel(db, "skilllist", 6)
    return {
        "table": "skilllist", "type": 6, "n": len(recs),
        "slots": val_counter(recs),
        "p0_dev_named": [[r["skillid"], r.get("name"), r.get("param0")] for r in recs],
        "p3_all_one": all(r.get("param3") == 1 for r in recs),
        "p1_gt1": sum(1 for r in recs if r.get("param1", 0) > 1),
        "p1_dist": dict(Counter(r.get("param1") for r in recs)),
    }


def claim12_1029(db):
    recs = sel(db, "skilllist", 1029)
    # 只取「像倍率」的数字：带小数点、或带 ％/% 的百分数；排除 sub1 / _1 这类序号
    num = re.compile(r"(\d+(?:\.\d+)?)(\s*[%％])?")
    matches = []
    for r in recs:
        nm = (r.get("name") or "").replace("\n", " ")
        p0 = r.get("param0")
        found = []
        for m in num.finditer(nm):
            txt, pct = m.group(1), m.group(2)
            if "." not in txt and not pct:
                continue  # 纯整数且无百分号：多为序号，不算倍率证据
            val = float(txt)
            if pct:
                val = val / 100.0
            found.append((txt + (pct or ""), val))
        hit = [f for f in found if p0 is not None and abs(f[1] - p0) < 1e-12]
        if found:
            matches.append({"skillid": r["skillid"], "name": nm, "p0": p0,
                            "numbers": found, "matched": bool(hit)})
    named = [m for m in matches if m["matched"]]
    fam = Counter("追撃" if "追撃" in (m["name"] or "") else
                  ("EnchantWeapon/付与" if ("EnchantWeapon" in (m["name"] or "") or "付与" in (m["name"] or ""))
                   else "其他") for m in matches)
    return {
        "table": "skilllist", "type": 1029, "n": len(recs),
        "slots": val_counter(recs),
        "p0_dist": dict(Counter(r.get("param0") for r in recs)),
        "records_with_multiplier_like_number_in_name": len(matches),
        "name_number_matches_p0": len(named),
        "matched_samples": named[:12],
        "families": dict(fam),
        "family_all": dict(Counter(
            "追撃" if "追撃" in (r.get("name") or "") else
            ("EnchantWeapon/付与" if ("EnchantWeapon" in (r.get("name") or "") or "付与" in (r.get("name") or ""))
             else "其他") for r in recs)),
        "enchant_p0_dist": dict(Counter(r.get("param0") for r in recs
                                        if "EnchantWeapon" in (r.get("name") or ""))),
        "chase_p0_dist": dict(Counter(r.get("param0") for r in recs
                                      if "追撃" in (r.get("name") or ""))),
    }


def main():
    db = Db()
    res = {
        "generated_by": "scripts/refcheck_20261023_lead/verify_01_params.py",
        "input": "output/cache_full_20261015_v3/decoded/{skilllist,bossinfo,charainfo}.data5.json.raw",
        "claim1_type1009": claim1_1009(db),
        "claim2_type116": claim2_116(db),
        "claim3_type1074": claim3_1074(db),
        "claim4_type1051": claim4_1051(db),
        "claim5_type58": claim5_58(db),
        "claim6_type2012": claim6_2012(db),
        "claim7_type3000": claim7_3000(db),
        "claim8_type99": claim8_99(db),
        "claim9_bossskill13": claim9_13(db),
        "claim10_type28": claim10_28(db),
        "claim11_type6": claim11_6(db),
        "claim12_type1029": claim12_1029(db),
    }
    p = write_json(out("params_claims.json"), res)
    print("wrote", p)
    for k, v in res.items():
        if isinstance(v, dict) and "n" in v:
            print("  %-24s n=%s" % (k, v["n"]))


if __name__ == "__main__":
    main()
