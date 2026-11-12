# -*- coding: utf-8 -*-
"""Lead 独立核对 2：羁绊 join 语义与覆盖 —— charainfo.sup1/sup2 与 supporterskill.ability_id。
CACHE charainfo(1488 行) + APK _mdCharacter.charainfo(9169 行) 两源，按项目「缓存优先、缺才回退 APK」口径。
只读。输出 work/refcheck_20261023_lead/bond_join_check.json
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


def card_recs(obj, key_candidates=("charainfo",)):
    for k in key_candidates:
        if isinstance(obj.get(k), list):
            return obj[k]
    for k, v in obj.items():
        if isinstance(v, list) and v and isinstance(v[0], dict) and "cid" in v[0]:
            return v
    return []


def main():
    res = {}
    cs = load(os.path.join(CACHE, "supporterskill.data5.json.raw"))
    cache_sup = cs.get("supporterskill") or []
    res["cache_supporterskill"] = len(cache_sup)
    res["cache_supporterskill_keys"] = list(cache_sup[0]) if cache_sup else []

    sa = load(os.path.join(APK, "_mdSAbirity.json"))
    apk_sup = sa.get("supporterskill") or []
    res["apk_supporterskill"] = len(apk_sup)
    apk_by_id = {r.get("ability_id"): r for r in apk_sup}

    def sup_ids(r):
        return [int(r.get("sup1") or 0), int(r.get("sup2") or 0),
                int(r.get("sup_cost") or 0)]

    # CACHE charainfo
    ci_cache = card_recs(load(os.path.join(CACHE, "charainfo.data5.json.raw")))
    res["cache_charainfo"] = len(ci_cache)
    # APK charainfo
    apk_char = load(os.path.join(APK, "_mdCharacter.json"))
    ci_apk = card_recs(apk_char)
    res["apk_character_top"] = {k: (len(v) if isinstance(v, list) else type(v).__name__)
                                for k, v in apk_char.items() if not k.startswith("_")}
    res["apk_charainfo"] = len(ci_apk)

    # 项目口径：按 ID 缓存优先，缺才 APK
    byid = {}
    for r in ci_apk:
        cid = r.get("cid")
        if cid is not None:
            byid[cid] = ("APK", r)
    for r in ci_cache:
        cid = r.get("cid")
        if cid is not None:
            byid[cid] = ("CACHE", r)
    res["merged_cards"] = len(byid)

    src_count = collections.Counter()
    sup1_nonzero = []
    joined_sup1 = []
    for cid, (src, r) in byid.items():
        s1 = int(r.get("sup1") or 0)
        s2 = int(r.get("sup2") or 0)
        if s1:
            src_count[src] += 1
            sup1_nonzero.append((cid, src, s1, s2))
            if s1 in apk_by_id:
                joined_sup1.append((cid, src, s1, apk_by_id[s1]))
    res["cards_with_sup1_nonzero"] = len(sup1_nonzero)
    res["sup1_source_split"] = dict(src_count)
    res["sup1_join_apk_supporterskill"] = len(joined_sup1)
    res["sup2_nonzero"] = sum(1 for cid, (s, r) in byid.items() if int(r.get("sup2") or 0))
    # sup1 值域
    vals = [x[2] for x in sup1_nonzero]
    res["sup1_value_range"] = [min(vals), max(vals)] if vals else None
    res["sup1_first20"] = sorted([(c, v) for c, s, v, s2 in sup1_nonzero])[:20]
    # cid10001 明细
    detail = {}
    for cid in (10001, 351, 201, 30236):
        ent = byid.get(cid)
        if not ent:
            continue
        src, r = ent
        s1, s2 = int(r.get("sup1") or 0), int(r.get("sup2") or 0)
        d = {"source": src, "sup1": s1, "sup2": s2}
        if s1 in apk_by_id:
            rr = apk_by_id[s1]
            d["apk_sup"] = {"ability_id": rr.get("ability_id"), "name": rr.get("name"),
                            "text": (rr.get("text") or "")[:160], "ability": rr.get("ability"),
                            "param0_6": [rr.get("param%d" % i) for i in range(7)]}
        detail[cid] = d
    res["detail"] = detail

    with open(os.path.join(OUT, "bond_join_check.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1)[:5000])


if __name__ == "__main__":
    main()
