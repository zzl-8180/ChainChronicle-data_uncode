# -*- coding: utf-8 -*-
"""params_diff.py — 新版 1673 行 vs 旧版 1610 行 的规范化与逐条比对。

输出（work/refcheck_20261023_lead/params/）：
  param_rows_new1673.json   规范化后的全部行（含派生字段）
  new_rows_since_1017.json  63 条新增 + 33 条改判
只读「其他人的参考」，不写入。
"""
import collections
import json
import sys

import params_common as P

OUT = P.OUT
OUT.mkdir(parents=True, exist_ok=True)


def sg(r):
    """status 归组：'待定（与paramN同标签）' -> '待定'"""
    s = str(r.get("status", ""))
    return "待定" if s.startswith("待定") else s


def norm(r, src, old_row=None):
    d = {k: r.get(k) for k in P.ROW_KEYS}
    d["evidence_grade"] = P.grade(r["status"])
    d["status_group"] = sg(r)
    d["source_file"] = src
    if old_row is not None:
        d["prev_1017"] = {k: old_row.get(k) for k in ("status", "label", "conversion", "unit", "hits", "decisive_hits")}
    return d


def main():
    new = P.load(P.NEW1 / "param_table.json")
    old = P.load(P.OLD / "param_table.json")
    nk = {P.key(r): r for r in new["rows"]}
    ok = {P.key(r): r for r in old["rows"]}

    added = [nk[k] for k in nk if k not in ok]
    removed = [ok[k] for k in ok if k not in nk]
    common = [k for k in nk if k in ok]
    changed = []          # status / label / conversion / unit 任一变化 —— 真正的「改判」
    recount = []          # 仅 hits / decisive 等统计量变化（不算改判）
    for k in common:
        o, n = ok[k], nk[k]
        core = {f: (o.get(f), n.get(f)) for f in
                ("status", "label", "conversion", "unit") if o.get(f) != n.get(f)}
        cnt = {f: (o.get(f), n.get(f)) for f in
               ("hits", "decisive_hits") if o.get(f) != n.get(f)}
        if core:
            changed.append((o, n, {**core, **cnt}))
        elif cnt:
            recount.append((o, n, cnt))

    stat = {
        "new_rows": len(new["rows"]), "old_rows": len(old["rows"]),
        "new_paired_cards": new["paired_cards"], "old_paired_cards": old["paired_cards"],
        "added": len(added), "removed": len(removed), "changed": len(changed),
        "recount_only": len(recount),
        "changed_status_only": sum(1 for o, n, f in changed if set(f) == {"status"}),
        "changed_label": sum(1 for o, n, f in changed if "label" in f),
        "status_new": dict(collections.Counter(sg(r) for r in new["rows"]).most_common()),
        "status_old": dict(collections.Counter(sg(r) for r in old["rows"]).most_common()),
        "status_new_raw": dict(collections.Counter(r["status"] for r in new["rows"]).most_common()),
        "status_old_raw": dict(collections.Counter(r["status"] for r in old["rows"]).most_common()),
        "table_new": dict(collections.Counter(r["table"] for r in new["rows"]).most_common()),
        "table_old": dict(collections.Counter(r["table"] for r in old["rows"]).most_common()),
        "table_type_new": {"%s|%s" % (t, ty): c for t, ty in []},
    }
    tt = collections.Counter((r["table"], r["type"]) for r in new["rows"])
    stat["table_type_new"] = [{"table": t, "type": ty, "rows": c} for (t, ty), c in tt.most_common()]
    tt_old = collections.Counter((r["table"], r["type"]) for r in old["rows"])
    for e in stat["table_type_new"]:
        e["rows_old"] = tt_old.get((e["table"], e["type"]), 0)
        e["delta"] = e["rows"] - e["rows_old"]

    # 全量规范化
    allrows = []
    for r in sorted(new["rows"], key=lambda r: (P.grade(r["status"]), -r["decisive_hits"], -r["hits"], r["table"], r["type"], r["slot"])):
        src = "20261023"
        allrows.append(norm(r, src, ok.get(P.key(r))))
    payload = {
        "generated_from": {"new": str(P.NEW1 / "param_table.json"), "old": str(P.OLD / "param_table.json")},
        "note": "rows 按（证据等级, decisive_hits, hits）降序排列；prev_1017 为 2026-10-17 副本的同键行快照（仅既有行有）",
        "paired_cards": new["paired_cards"],
        "rows": allrows,
    }
    (OUT / "param_rows_new1673.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    # 新增 + 改判
    add_out = []
    for r in sorted(added, key=lambda r: (P.grade(r["status"]), -r["decisive_hits"], r["table"], r["type"], r["slot"])):
        add_out.append(norm(r, "20261023", None))
    chg_out = []
    for o, n, fields in changed:
        d = norm(n, "20261023", o)
        d["changed_fields"] = {k: {"from": v[0], "to": v[1]} for k, v in fields.items()}
        chg_out.append(d)
    chg_out.sort(key=lambda d: (P.grade(d["status"]), d["table"], d["type"], d["slot"]))
    recount_out = [dict(norm(n, "20261023", o),
                        changed_fields={k: {"from": v[0], "to": v[1]} for k, v in f.items()})
                   for o, n, f in recount]
    (OUT / "new_rows_since_1017.json").write_text(json.dumps({
        "note": ("added = 新版 1673 里有、旧版 1610 里没有的行；changed = 同键但 status/label/conversion/unit "
                 "有变化（改判）的既有行；recount_only = 只有命中数/决定性数变化、结论未变的既有行"),
        "added_count": len(added), "changed_count": len(changed), "removed_count": len(removed),
        "recount_only_count": len(recount),
        "added": add_out, "changed": chg_out, "recount_only": recount_out, "removed": removed,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    (OUT / "_stats.json").write_text(json.dumps(stat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: stat[k] for k in ("new_rows", "old_rows", "added", "removed", "changed", "recount_only",
                                           "changed_status_only", "changed_label",
                                           "status_new", "status_old", "table_new", "table_old")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
