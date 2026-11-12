# -*- coding: utf-8 -*-
"""params_rows.py — 打印指定 table/type 的全部行（只读）。用法：python params_rows.py skilllist 7 99 1095 ..."""
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
new = P.load(P.NEW1 / "param_table.json")
old = P.load(P.OLD / "param_table.json")
ok = {P.key(r): r for r in old["rows"]}
table = sys.argv[1]
types = [int(x) for x in sys.argv[2:]] or sorted({r["type"] for r in new["rows"] if r["table"] == table})
for typ in types:
    rows = [r for r in new["rows"] if r["table"] == table and r["type"] == typ]
    print(f"### {table} type {typ}  ({len(rows)} 行)")
    for r in rows:
        o = ok.get(P.key(r))
        prev = f"  <-旧 {o['status']}/{o['label'] or '-'}/{o['conversion'] or '-'}" if o and (
            o["status"] != r["status"] or o["label"] != r["label"] or o["conversion"] != r["conversion"]) else ""
        print(f"   {r['slot']:8s} {r['status']:18s} {r['label'] or '-':12s} {r['conversion'] or '-':15s} "
              f"{r['unit'] or '-':6s} hits {r['hits']:4d} dec {r['decisive_hits']:3d}{prev}")
