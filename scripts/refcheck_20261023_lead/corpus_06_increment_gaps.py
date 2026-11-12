# -*- coding: utf-8 -*-
"""增量缺口量化：bond(APK)、Leader 发动条件、基础字段、mtime 分簇。

输出: work/refcheck_20261023_lead/corpus/increment_gaps.json
用法: .venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/corpus_06_increment_gaps.py
"""
import os, sys, json, collections, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_cards as cc

ROOT = r"E:\代码项目\锁链战记数据解包"
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead", "corpus")
CACHE = os.path.join(ROOT, "output", "cache_full_20261015_v3", "decoded")
APK = os.path.join(ROOT, "output", "base_master")
PAGES = os.path.join(ROOT, "output", "character_skills", "pages")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def bond_gap():
    """我方 bond 只查 CACHE supporterskill；对方并入 APK _mdSAbirity.supporterskill。"""
    cache = load(os.path.join(CACHE, "supporterskill.data5.json.raw"))["supporterskill"]
    apk = load(os.path.join(APK, "_mdSAbirity.json"))["supporterskill"]
    c_ids = {r["ability_id"] for r in cache}
    a_ids = {r["ability_id"] for r in apk}
    # charainfo sup1（我方主表：CACHE decoded + APK）
    char_cache = load(os.path.join(CACHE, "charainfo.data5.json.raw"))["charainfo"]
    char_apk = load(os.path.join(APK, "_mdCharacter.json"))["charainfo"]
    cid2sup1 = {}
    for rec in char_apk:
        cid = rec.get("cid")
        if cid is not None:
            cid2sup1[str(cid)] = rec.get("sup1")
    for rec in char_cache:
        cid = rec.get("cid")
        if cid is not None:
            cid2sup1[str(cid)] = rec.get("sup1")  # CACHE 优先
    n_nonzero = sum(1 for v in cid2sup1.values() if v)
    in_cache = sum(1 for v in cid2sup1.values() if v in c_ids)
    in_either = sum(1 for v in cid2sup1.values() if v in c_ids or v in a_ids)
    # APK 记录的 abi0..abi3 引用
    apk_with_refs = sum(1 for r in apk if any(r.get(k) for k in ("abi0", "abi1", "abi2", "abi3")))
    return {
        "cache_supporterskill_records": len(cache),
        "apk_supporterskill_records": len(apk),
        "cache_distinct_ability_id": len(c_ids),
        "apk_distinct_ability_id": len(a_ids),
        "union_distinct_ability_id": len(c_ids | a_ids),
        "overlap_ability_id": len(c_ids & a_ids),
        "charainfo_total": len(cid2sup1),
        "charainfo_sup1_nonzero": n_nonzero,
        "resolvable_via_cache_only": in_cache,
        "resolvable_via_union": in_either,
        "apk_records_with_abi_refs": apk_with_refs,
        "our_links_bond_cards": 311,
    }


def leader_condition():
    p = os.path.join(cc.BASES["new2"], "leader_condition_map.json")
    d = load(p)
    cards = sum(v2.get("cards", 0) for v1 in d.values() for v2 in v1.values())
    cats = {k: {"options": len(v), "cards": sum(x.get("cards", 0) for x in v.values())}
            for k, v in d.items()}
    # 我方 leader 组覆盖
    led = 0
    with open(os.path.join(ROOT, "output", "character_skills", "links", "character_skills.jsonl"),
              encoding="utf-8") as f:
        for line in f:
            j = json.loads(line)
            for g in j["groups"]:
                if g["group"] == "leader" and g.get("records"):
                    led += 1
    return {"category_groups": list(cats.keys()), "per_category": cats,
            "card_entries_summed": cards, "our_leader_group_cards": led,
            "note": "对方 map 是按 category 统计的标签表（不是逐卡条件），我们的 leader 组只登记效果记录，无条件字段"}


def basic_field_gap():
    j = load(os.path.join(PAGES, "351", "card.json"))
    ours = [f["key"] for f in j["basic"]["fields"]]
    # 对方 basic 键（全量并集）
    idx = cc.index_by_cid(cc.BASES["new2"])
    keys = collections.Counter()
    for cid in idx:
        d, p = idx[cid][0]
        cj = load(os.path.join(cc.data_path(p), "card.json"))
        for k in (cj.get("basic") or {}).keys():
            keys[k] += 1
    return {"our_page_basic_fields": ours, "their_basic_keys": dict(keys),
            "on_our_page": sorted(set(ours) & set(keys)),
            "not_on_our_page": sorted(set(keys) - set(ours))}


def mtime_clusters():
    """各快照 cards/ 内部文件的 mtime 按文件名分簇（判断哪些是何时重生成的）。"""
    res = {}
    for k in ("old", "new1", "new2"):
        base = cc.BASES[k]
        idx = cc.index_by_cid(base)
        buckets = collections.defaultdict(collections.Counter)
        seen = set()
        for cid in idx:
            for dname, dpath in idx[cid]:
                for root in (cc.data_path(dpath), dpath):
                    if not os.path.isdir(root):
                        continue
                    for fn in os.listdir(root):
                        fp = os.path.join(root, fn)
                        if not os.path.isfile(fp):
                            continue
                        key = os.path.normcase(os.path.abspath(fp))
                        if key in seen:
                            continue
                        seen.add(key)
                        day = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(fp)))
                        buckets[fn][day] += 1
        res[k] = {fn: dict(c) for fn, c in buckets.items()}
    return res


def main():
    res = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bond_gap": bond_gap(),
        "leader_condition": leader_condition(),
        "basic_field_gap": basic_field_gap(),
        "mtime_clusters": mtime_clusters(),
    }
    with open(os.path.join(OUT, "increment_gaps.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("bond:", json.dumps(res["bond_gap"], ensure_ascii=False))
    print("leader:", json.dumps(res["leader_condition"], ensure_ascii=False))
    print("basic.not_on_our_page:", res["basic_field_gap"]["not_on_our_page"])
    print("mtime clusters:")
    for k, v in res["mtime_clusters"].items():
        print(" ", k)
        for fn, c in sorted(v.items()):
            print("   ", fn, c)


if __name__ == "__main__":
    main()
