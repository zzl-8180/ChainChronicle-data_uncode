# -*- coding: utf-8 -*-
"""params_vs_1017.py — 用我方 2026-10-17 逐条核对结论（1610 行 CSV）回看新版 1673 行。

输出 work/refcheck_20261023_lead/params/vs_1017.json
"""
import csv
import json
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
OUT = P.OUT
CROSS = P.ROOT / "output" / "reference_analysis" / "claude_cc_site_pages" / "param_table_crosscheck.csv"


def main():
    new = P.load(P.NEW1 / "param_table.json")
    nk = {P.key(r): r for r in new["rows"]}
    rows = list(csv.DictReader(CROSS.open(encoding="utf-8-sig")))
    out = []
    for o in rows:
        k = (o["table"], int(o["type"]) if o["type"].isdigit() else o["type"], o["slot"])
        n = nk.get(k)
        out.append({
            "key": list(k),
            "verdict_1017": o["核对结论"],
            "note_1017": o["备注"],
            "old": {"status": o["对方状态"], "label": o["对方标签"], "conv": o["对方换算"], "unit": o["对方单位"],
                    "hits": o["hits"], "dec": o["decisive"]},
            "new": None if n is None else {"status": n["status"], "label": n["label"], "conv": n["conversion"],
                                           "unit": n["unit"], "hits": n["hits"], "dec": n["decisive_hits"]},
        })
    # 新增行里我方未核对过的
    oldkeys = {(o["table"], int(o["type"]) if o["type"].isdigit() else o["type"], o["slot"]) for o in rows}
    added_unchecked = [{"key": [r["table"], r["type"], r["slot"]], "status": r["status"], "label": r["label"],
                        "conv": r["conversion"], "unit": r["unit"], "hits": r["hits"], "dec": r["decisive_hits"]}
                       for r in new["rows"] if P.key(r) not in oldkeys]
    payload = {"rows": out, "added_not_in_1017": added_unchecked}
    (OUT / "vs_1017.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    # 只打印被点名的问题行
    focus = [r for r in out if not r["verdict_1017"].startswith("本项目未研究")]
    print(f"旧版 1610 行核对：非「未研究」结论 {len(focus)} 行")
    for r in focus:
        print(f"  {r['key']} | 1017: {r['verdict_1017']} | 旧={r['old']} | 新={r['new']}")
    print()
    print(f"新版新增且 1017 未核对的行 {len(added_unchecked)} 行")
    for r in added_unchecked:
        print(f"  {r['key']} {r['status']} {r['label']} {r['conv']} hits={r['hits']} dec={r['dec']}")


if __name__ == "__main__":
    main()
