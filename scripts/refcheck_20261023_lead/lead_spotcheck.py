# -*- coding: utf-8 -*-
"""Lead 抽检：type58 p4（复活HP）取值分布 + type3000 p3/p4 与正文关键词的相关性。
只读。输出 work/refcheck_20261023_lead/lead_spotcheck.json
"""
import json
import os
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead")
CACHE = os.path.join(ROOT, "output", "cache_full_20261015_v3", "decoded")
APK = os.path.join(ROOT, "output", "base_master")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def rows(p, key):
    obj = load(p)
    return obj.get(key) or []


def main():
    res = {}
    # ---- type58 (skilllist) ----
    recs = []
    for src, p in (("CACHE", os.path.join(CACHE, "skilllist.data5.json.raw")),
                   ("APK", os.path.join(APK, "_mdSkill.json"))):
        for r in rows(p, "skilllist"):
            if isinstance(r, dict) and int(r.get("ability") or 0) == 58:
                r = dict(r)
                r["_src"] = src
                recs.append(r)
    res["type58_records"] = len(recs)
    p4 = collections.Counter(round(float(r.get("param4") or 0), 3) for r in recs)
    res["type58_param4_dist"] = dict(p4)
    res["type58_param0_dist"] = dict(collections.Counter(round(float(r.get("param0") or 0), 3) for r in recs))
    res["type58_param5_dist"] = dict(collections.Counter(round(float(r.get("param5") or 0), 3) for r in recs))
    # 只看 p4 特殊值样例（非 100000）
    special = [{"skillid": r.get("skillid"), "src": r["_src"], "name": r.get("name"),
                "param4": r.get("param4"), "param5": r.get("param5"), "param7": r.get("param7"),
                "text": (r.get("text") or "")[:100]}
               for r in recs if abs(float(r.get("param4") or 0) - 100000) > 1]
    res["type58_param4_not_100000"] = special[:12]
    res["type58_param4_not_100000_count"] = len(special)
    # ---- type3000 p3/p4 vs text keywords ----
    r3000 = []
    for src, p in (("CACHE", os.path.join(CACHE, "skilllist.data5.json.raw")),
                   ("APK", os.path.join(APK, "_mdSkill.json"))):
        for r in rows(p, "skilllist"):
            if isinstance(r, dict) and int(r.get("ability") or 0) == 3000:
                r = dict(r)
                r["_src"] = src
                r3000.append(r)
    res["type3000_records"] = len(r3000)
    def corr(kw, param):
        has_kw = [r for r in r3000 if kw in (r.get("text") or "")]
        no_kw = [r for r in r3000 if kw not in (r.get("text") or "")]
        return {
            "kw": kw, "param": param,
            "records_with_kw": len(has_kw),
            "with_kw_nonzero": sum(1 for r in has_kw if abs(float(r.get(param) or 0)) > 1e-9),
            "records_without_kw": len(no_kw),
            "without_kw_nonzero": sum(1 for r in no_kw if abs(float(r.get(param) or 0)) > 1e-9),
            "with_kw_samples": [{"skillid": r.get("skillid"), "text": (r.get("text") or "")[:80],
                                 "param1": r.get("param1"), "param2": r.get("param2"),
                                 "param3": r.get("param3"), "param4": r.get("param4"),
                                 "param5": r.get("param5"), "param7": r.get("param7"),
                                 "param8": r.get("param8")} for r in has_kw[:3]],
        }
    res["type3000_text_corr"] = [
        corr("移動速度", "param3"),
        corr("防御力", "param4"),
        corr("回復", "param5"),
        corr("クリティカル", "param7"),
    ]
    # keep-size guard
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "lead_spotcheck.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main()
