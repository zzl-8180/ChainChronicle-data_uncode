# -*- coding: utf-8 -*-
"""探索用 dump：打印指定类型的记录、参数存在性与取值分布。只读。"""
from __future__ import annotations

import sys
from collections import Counter

sys.path.insert(0, __import__("os").path.dirname(__file__))
from verify_common import Db, params, pstr, type_of, val_counter  # noqa: E402


def main(argv):
    db = Db()
    table = argv[0]
    types = [int(x) for x in argv[1].split(",")]
    mode = argv[2] if len(argv) > 2 else "list"
    src = db.skilllist if table == "skilllist" else db.bossskill
    for t in types:
        recs = [r for r in src if type_of(r, table) == t]
        print("=" * 100)
        print("TABLE=%s TYPE=%s n=%d" % (table, t, len(recs)))
        print("-- 取值分布 --")
        vc = val_counter(recs, "skillparam" if table == "bossskill" else "param")
        for i, d in vc.items():
            print("  p%-2d present=%-4d missing=%-4d distinct=%-3d top=%s"
                  % (i, d["present"], d["missing"], d["distinct"], d["top"][:8]))
        if mode == "list":
            pre = "skillparam" if table == "bossskill" else "param"
            for r in recs:
                nm = r.get("name") or r.get("spmotname") or ""
                print("  %-10s | %-60s | %s" % (r.get("skillid"), str(nm).replace("\n", " ")[:60], pstr(r, pre)))
        elif mode == "full":
            import json
            for r in recs[:8]:
                print(json.dumps(r, ensure_ascii=False))
        elif mode == "text":
            for r in recs[:20]:
                print("  --", r.get("skillid"), "|", (r.get("text") or r.get("sinfo") or "")[:200].replace("\n", " / "))
                print("     ", pstr(r, "param" if table == "skilllist" else "skillparam"))


if __name__ == "__main__":
    main(sys.argv[1:])
