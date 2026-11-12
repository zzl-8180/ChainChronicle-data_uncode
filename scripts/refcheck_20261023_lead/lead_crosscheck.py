# -*- coding: utf-8 -*-
"""Lead 独立核对：对方 param_table（2026-10-23 版） vs 我方 rules.json 覆盖。

只读输入，不修改任何既有产物。输出：
  work/refcheck_20261023_lead/crosscheck_param_vs_our_rules.json
"""
import json
import collections
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead")
NEW_TABLE = os.path.join(ROOT, "其他人的参考", "claude_cc_site_pages_给GPT_20261023",
                         "claude_cc_site_pages", "param_table.json")
NEW_TABLE1 = os.path.join(ROOT, "其他人的参考", "claude_cc_site_pages 20261023", "param_table.json")
OLD_TABLE = os.path.join(ROOT, "其他人的参考", "claude_cc_site_pages", "param_table.json")
OUR_RULES = os.path.join(ROOT, "output", "character_skills", "profiles", "rules.json")

os.makedirs(OUT, exist_ok=True)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def our_key(table, etype, slot):
    """对方 slot 命名 paramN / skillparamN / iParamN / flagN 等 → 我方 field_path 风格。"""
    if table == "bossskill":
        if slot.startswith("param"):
            return "bossskill|%d|/skill%s" % (etype, slot)
        return "bossskill|%d|/%s" % (etype, slot)
    if slot.startswith("param"):
        return "%s|%d|/%s" % (table, etype, slot)
    return "%s|%d|/%s" % (table, etype, slot)


def main():
    new = load(NEW_TABLE)
    new1 = load(NEW_TABLE1)
    old = load(OLD_TABLE)
    rules = load(OUR_RULES)
    rows = new["rows"]
    rows1 = new1["rows"]
    oldrows = old["rows"]

    # 我方 key 归一化（bossskill 的 /skillparamN 与我方 rules 一致；skilllist 用 /paramN）
    our_keys = set(rules)

    def key_of(r):
        return our_key(r["table"], int(r["type"]), r["slot"])

    status_cnt = collections.Counter(r["status"] for r in rows)
    overlap = collections.Counter()
    absent = collections.Counter()
    for r in rows:
        k = key_of(r)
        if k in our_keys:
            overlap[r["status"]] += 1
        else:
            absent[r["status"]] += 1

    # 两版是否一致（给 GPT 包 vs 用户工作副本）
    sig = lambda rs: collections.Counter(
        (r["table"], int(r["type"]), r["slot"], r["status"], r["label"], r["conversion"])
        for r in rs)
    same_1_2 = sig(rows) == sig(rows1)

    # 旧版 1610 → 新版 1673 差异
    def rowkey(r):
        return (r["table"], int(r["type"]), r["slot"])

    oldmap = {rowkey(r): r for r in oldrows}
    newmap = {rowkey(r): r for r in rows}
    added = [newmap[k] for k in newmap if k not in oldmap]
    removed = [oldmap[k] for k in oldmap if k not in newmap]
    changed = []
    for k in newmap:
        if k in oldmap:
            a, b = oldmap[k], newmap[k]
            diff = {f: (a.get(f), b.get(f)) for f in ("status", "label", "conversion", "unit")
                    if a.get(f) != b.get(f)}
            if diff:
                changed.append({"key": k, "old": a, "new": b, "diff": diff})

    # 我方尚未覆盖、对方给了非「未知/待定」标签的行
    interesting = []
    for r in rows:
        if key_of(r) in our_keys:
            continue
        if r["status"] in ("未知", "待定", "弱证据"):
            continue
        interesting.append({
            "key": key_of(r),
            "status": r["status"],
            "label": r["label"],
            "conversion": r["conversion"],
            "unit": r["unit"],
            "hits": r["hits"],
            "decisive": r["decisive_hits"],
            "decisive_cases": r["decisive_cases"],
            "cards_with_value": r["cards_with_value"],
            "examples": r.get("examples", ""),
            "alternatives": r.get("alternatives", ""),
        })
    interesting.sort(key=lambda x: (-x["decisive"], -x["hits"]))

    # 我方 rules.json 有、对方表里没有的（对方覆盖缺口，供「我方更强」判断）
    their_keys = {key_of(r) for r in rows}
    ours_only = sorted(k for k in our_keys if k not in their_keys)

    # 关注槽位明细
    focus = [
        ("skilllist", 3000), ("skilllist", 1110), ("skilllist", 1059), ("bossskill", 13),
        ("skilllist", 2012), ("bossskill", 116), ("skilllist", 58), ("skilllist", 1051),
        ("skilllist", 1074), ("skilllist", 1009), ("bossskill", 51), ("skilllist", 1029),
        ("skilllist", 99), ("skilllist", 6), ("skilllist", 28), ("bossskill", 27),
        ("skilllist", 1095), ("skilllist", 1017), ("skilllist", 1106), ("skilllist", 1071),
        ("skilllist", 1086), ("skilllist", 70), ("skilllist", 1111), ("ability", 2003),
        ("ability", 3000), ("ability", 1095), ("ability", 99),
    ]
    focus_rows = {}
    for t, et in focus:
        rs = [r for r in rows if r["table"] == t and int(r["type"]) == et]
        focus_rows["%s|%d" % (t, et)] = [{
            "slot": r["slot"], "status": r["status"], "label": r["label"],
            "conversion": r["conversion"], "unit": r["unit"],
            "hits": r["hits"], "decisive": r["decisive_hits"],
            "decisive_cases": r["decisive_cases"],
            "in_our_rules": key_of(r) in our_keys,
            "our_meaning": rules.get(key_of(r), {}).get("meaning_zh"),
            "our_evidence": rules.get(key_of(r), {}).get("evidence") or rules.get(key_of(r), {}).get("status"),
        } for r in rs]

    summary = {
        "meta": {"generated_by": "scripts/refcheck_20261023_lead/lead_crosscheck.py",
                 "our_rules_keys": len(our_keys),
                 "new_rows": len(rows), "new1_rows": len(rows1), "old_rows": len(oldrows),
                 "new1_vs_new2_identical_rows": same_1_2},
        "status_distribution": dict(status_cnt),
        "overlap_with_our_rules": dict(overlap),
        "not_in_our_rules": dict(absent),
        "added_rows_since_1017": [{
            "key": rowkey(r), "status": r["status"], "label": r["label"],
            "conversion": r["conversion"], "unit": r["unit"], "hits": r["hits"],
            "decisive": r["decisive_hits"], "decisive_cases": r["decisive_cases"],
            "in_our_rules": key_of(r) in our_keys,
            "examples": r.get("examples", "")[:300],
        } for r in added],
        "removed_rows": [rowkey(r) for r in removed],
        "changed_rows": [{"key": list(c["key"]), "diff": c["diff"]} for c in changed],
        "ours_only_keys": ours_only,
        "interesting_not_in_our_rules": interesting,
        "focus_rows": focus_rows,
    }
    outp = os.path.join(OUT, "crosscheck_param_vs_our_rules.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    print("rows new=%d new1=%d old=%d  new1==new2:%s" % (len(rows), len(rows1), len(oldrows), same_1_2))
    print("status:", dict(status_cnt))
    print("overlap:", dict(overlap))
    print("not in ours:", dict(absent))
    print("added=%d removed=%d changed=%d" % (len(added), len(removed), len(changed)))
    print("interesting(not ours, status>=ref/stat) =", len(interesting))
    for r in interesting[:25]:
        print("  %-28s %-6s %-10s %-14s hits=%3d dec=%2d/%2d" % (
            r["key"], r["status"], r["label"], r["conversion"], r["hits"], r["decisive"], r["decisive_cases"]))
    print("ours_only_keys =", len(ours_only))
    print("saved", outp)


if __name__ == "__main__":
    main()
