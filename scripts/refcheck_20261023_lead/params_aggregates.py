# -*- coding: utf-8 -*-
"""params_aggregates.py — REPORT 需要的几个汇总数。"""
import collections
import json
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
d = json.loads((P.OUT / "new_rows_since_1017.json").read_text(encoding="utf-8"))
new = P.load(P.NEW1 / "param_table.json")

print("== 63 条新增 ==")
print(" status:", dict(collections.Counter(r["status"] for r in d["added"]).most_common()))
print(" 高于统计推断的:", [(r["table"], r["type"], r["slot"], r["status"]) for r in d["added"]
                          if r["status"] in ("解包确认", "用户确认", "参考推断")])
print(" decisive>=10:", sum(1 for r in d["added"] if r["decisive_hits"] >= 10),
      "| decisive>=20:", sum(1 for r in d["added"] if r["decisive_hits"] >= 20),
      "| hits>=50:", sum(1 for r in d["added"] if r["hits"] >= 50))
print(" 空标签(未知且无 label):", sum(1 for r in d["added"] if not r["label"]))
print(" 有 examples 的:", sum(1 for r in d["added"] if r["examples"]))
print(" 新增涉及 type 数:", len({r["type"] for r in d["added"]}))

print("\n== 33 条改判 ==")
print(" 现在的 status:", dict(collections.Counter(r["status"] for r in d["changed"]).most_common()))
print(" 升级方向：")
for r in d["changed"]:
    cf = r["changed_fields"]
    if "status" in cf:
        print(f"   {r['table']} t{r['type']} {r['slot']}: {cf['status']['from']} -> {cf['status']['to']}"
              f" | {cf.get('label', {}).get('from', r['label'])} -> {cf.get('label', {}).get('to', r['label'])}")
print(" 仅换换算/单位（status 不变）:")
for r in d["changed"]:
    cf = r["changed_fields"]
    if "status" not in cf:
        print(f"   {r['table']} t{r['type']} {r['slot']}: conv {cf.get('conversion', {}).get('from')} -> "
              f"{cf.get('conversion', {}).get('to')} | unit {cf.get('unit', {}).get('from')} -> {cf.get('unit', {}).get('to')}"
              f" | label {cf.get('label', {}).get('from')} -> {cf.get('label', {}).get('to')}")

print("\n== 全表候选量级 ==")
rows = new["rows"]
print(" 统计推断+decisive>=20:", sum(1 for r in rows if r["status"] == "统计推断" and r["decisive_hits"] >= 20))
print(" 统计推断+decisive>=50:", sum(1 for r in rows if r["status"] == "统计推断" and r["decisive_hits"] >= 50))
print(" 解包确认/用户确认/参考推断 合计:", sum(1 for r in rows if r["status"] in ("解包确认", "用户确认", "参考推断")))
print(" 统计推断但 decisive<3（旧分析点的 11 行高风险同类）:", sum(1 for r in rows if r["status"] == "统计推断" and r["decisive_hits"] < 3))
print(" 待定行数:", sum(1 for r in rows if str(r["status"]).startswith("待定")))
print(" 弱证据+未知 合计:", sum(1 for r in rows if r["status"] in ("弱证据", "未知")))
