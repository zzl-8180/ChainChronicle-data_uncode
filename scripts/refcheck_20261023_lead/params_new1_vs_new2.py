# -*- coding: utf-8 -*-
"""params_new1_vs_new2.py — 两个 2026-10-23 目录的快照差异（只读）。

new1 = `claude_cc_site_pages 20261023/`（本机 01:25–02:46 生成）
new2 = `claude_cc_site_pages_给GPT_20261023/claude_cc_site_pages/`（04:34–10:41，含 GPT 批次的后续改动）
"""
import difflib
import json
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")


def main():
    for f in ("infer_params.py", "numbers.py", "unpack_text.py"):
        a = (P.NEW1 / "scripts" / f).read_text(encoding="utf-8").splitlines()
        b = (P.NEW2 / "scripts" / f).read_text(encoding="utf-8").splitlines()
        print(f"##### {f}  lines new1={len(a)} new2={len(b)}  identical={a == b}")
        d = list(difflib.unified_diff(a, b, "new1", "new2", lineterm="", n=0))
        print("\n".join(d) if d else "(no diff)")
        print()
    a = json.loads((P.NEW1 / "param_table.json").read_text(encoding="utf-8"))
    b = json.loads((P.NEW2 / "param_table.json").read_text(encoding="utf-8"))
    ka = {P.key(r): r for r in a["rows"]}
    kb = {P.key(r): r for r in b["rows"]}
    diff = [k for k in ka if k in kb and ka[k] != kb[k]]
    print(f"param_table: rows {len(a['rows'])} vs {len(b['rows'])}; 键集合相同={set(ka) == set(kb)}; 值不同的行={len(diff)}")
    for k in diff:
        print(" ", k, {f: (ka[k][f], kb[k][f]) for f in ka[k] if ka[k][f] != kb[k].get(f)})


if __name__ == "__main__":
    main()
