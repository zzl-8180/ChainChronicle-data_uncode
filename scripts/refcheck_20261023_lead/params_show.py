# -*- coding: utf-8 -*-
"""params_show.py — 打印指定行的完整字段。用法：python params_show.py skilllist:67:param2 ..."""
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
new = P.load(P.NEW1 / "param_table.json")
old = P.load(P.OLD / "param_table.json")
nk = {P.key(r): r for r in new["rows"]}
ok = {P.key(r): r for r in old["rows"]}
for spec in sys.argv[1:]:
    t, ty, slot = spec.split(":")
    k = (t, int(ty), slot)
    r = nk.get(k)
    o = ok.get(k)
    print(f"===== {spec}")
    if not r:
        print("  新版无此行")
        continue
    for f in P.ROW_KEYS:
        print(f"   {f}: {r.get(f)!r}")
    print(f"   [旧版] status={o['status']!r} label={o['label']!r} conv={o['conversion']!r} hits={o['hits']} dec={o['decisive_hits']}" if o else "   [旧版] 无")
