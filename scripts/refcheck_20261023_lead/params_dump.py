# -*- coding: utf-8 -*-
"""params_dump.py — 把新增/改判行打印成便于贴进 REPORT.md 的紧凑文本（只读）。"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
P = r"work\refcheck_20261023_lead\params\new_rows_since_1017.json"


def line(i, r):
    return (f"{i:2d}. {r['table']} type{r['type']} {r['slot']} | {r['status']} | "
            f"{r['label'] or '(空)'} {r['conversion'] or '(空)'} {r['unit'] or '(空)'} | "
            f"hits {r['hits']}/{r['cards_with_value']} dec {r['decisive_hits']}/{r['decisive_cases']} | "
            f"stat={(r['site_statistics'] or '')[:95]} | ex={(r['examples'] or '')[:120]}")


d = json.load(open(P, encoding="utf-8"))
print(f"ADDED {d['added_count']} / CHANGED {d['changed_count']} / RECOUNT_ONLY {d['recount_only_count']}")
print("\n===== ADDED =====")
for i, r in enumerate(d["added"], 1):
    print(line(i, r))
print("\n===== CHANGED (改判) =====")
for i, r in enumerate(d["changed"], 1):
    cf = r.get("changed_fields", {})
    print(f"{i:2d}. {r['table']} type{r['type']} {r['slot']} | {' ; '.join(f'{k}: {v['from']} -> {v['to']}' for k, v in cf.items())}")
    print(f"     now: {r['status']} | {r['label'] or '(空)'} {r['conversion'] or '(空)'} {r['unit'] or '(空)'} | "
          f"hits {r['hits']} dec {r['decisive_hits']} | stat={(r['site_statistics'] or '')[:100]}")
