# -*- coding: utf-8 -*-
"""params_summary.py — 打印分布统计（供 REPORT 引用）。"""
import json
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
st = json.loads((P.OUT / "_stats.json").read_text(encoding="utf-8"))
for k in ("new_rows", "old_rows", "new_paired_cards", "old_paired_cards", "added", "removed",
          "changed", "recount_only", "changed_status_only", "changed_label"):
    print(f"{k}: {st[k]}")
print("status_new:", json.dumps(st["status_new"], ensure_ascii=False))
print("status_old:", json.dumps(st["status_old"], ensure_ascii=False))
print("status_new_raw:", json.dumps(st["status_new_raw"], ensure_ascii=False))
print("status_old_raw:", json.dumps(st["status_old_raw"], ensure_ascii=False))
print("table_new:", json.dumps(st["table_new"], ensure_ascii=False))
print("table_old:", json.dumps(st["table_old"], ensure_ascii=False))
print()
print("table×type（按 20261023 行数降序，含旧版行数与增量）：")
tt = sorted(st["table_type_new"], key=lambda e: -e["rows"])
print(f"{'table':10s} {'type':6s} {'new':>5s} {'old':>5s} {'delta':>6s}")
for e in tt:
    print(f"{e['table']:10s} {str(e['type']):6s} {e['rows']:5d} {e['rows_old']:5d} {e['delta']:+6d}")
print()
print("有增量的类型：")
for e in tt:
    if e["delta"]:
        print(f"  {e['table']} type{e['type']}: {e['rows_old']} -> {e['rows']} ({e['delta']:+d})")
