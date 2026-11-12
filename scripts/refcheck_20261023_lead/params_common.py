# -*- coding: utf-8 -*-
"""公共加载器：新版/旧版 param_table 与对方脚本里的知识表。

只读：本模块不写任何「其他人的参考」下的文件。
"""
import ast
import json
from pathlib import Path

ROOT = Path(r"E:\代码项目\锁链战记数据解包")
REF = ROOT / "其他人的参考"
NEW1 = REF / "claude_cc_site_pages 20261023"
NEW2 = REF / "claude_cc_site_pages_给GPT_20261023" / "claude_cc_site_pages"
OLD = REF / "claude_cc_site_pages"

OUT = ROOT / "work" / "refcheck_20261023_lead" / "params"

ROW_KEYS = ["table", "type", "slot", "status", "site_statistics", "label", "conversion",
            "unit", "hits", "cards_with_value", "hit_rate", "decisive_hits",
            "decisive_cases", "examples", "alternatives"]

# 证据等级排序（数字越小越强）
GRADE = {"解包确认": 1, "用户确认": 2, "统计推断": 3, "参考推断": 4, "弱证据": 5, "待定": 6, "未知": 7}


def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = d["rows"]
    for r in rows:
        r["_key"] = (r["table"], r["type"], r["slot"])
    return {"paired_cards": d.get("paired_cards"), "rows": rows, "path": str(path)}


def key(r):
    return (r["table"], r["type"], r["slot"])


def grade(status):
    return GRADE.get(status, 99)


def load_knowledge(script_path):
    """用 ast 提取模块级大写字典字面量（{ (table, type, slot): (label, conv, unit[, note]) }），
    返回 [(name, table, type, slot, label, conv, unit, note, lineno)]。"""
    src = Path(script_path).read_text(encoding="utf-8")
    tree = ast.parse(src)
    out = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if node.value.__class__.__name__ not in ("Dict", "List"):
            continue
        try:
            val = ast.literal_eval(node.value)
        except Exception:
            continue
        if not isinstance(val, dict):
            continue
        for k, v in val.items():
            if not (isinstance(k, tuple) and len(k) == 3 and isinstance(v, tuple)):
                continue
            note = v[3] if len(v) > 3 else ""
            out.append({
                "dict": name,
                "table": k[0], "type": k[1], "slot": k[2],
                "label": v[0], "conversion": v[1], "unit": v[2], "note": note,
                "line": node.lineno,
            })
    return out


def knowledge_comments(script_path):
    """返回 [(lineno, text)] 的全部注释行，便于摘录依据注释。"""
    out = []
    for i, line in enumerate(Path(script_path).read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if s.startswith("#"):
            out.append((i, s))
    return out
