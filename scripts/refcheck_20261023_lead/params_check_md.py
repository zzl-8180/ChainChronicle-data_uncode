# -*- coding: utf-8 -*-
"""params_check_md.py — 检查 REPORT.md 的 markdown 表格是否列数一致（`\\|` 视为转义）。

用法：python params_check_md.py [文件路径]
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1] if len(sys.argv) > 1 else r"work\refcheck_20261023_lead\params\REPORT.md"
lines = open(path, encoding="utf-8").read().splitlines()


def cells(line):
    """去掉转义竖线后数单元格。"""
    s = re.sub(r"\\\|", "\x00", line)
    return s.count("|") - 1


SEP = re.compile(r"^\|[\-| ]+\|$")
tables = bad = 0
i = 0
while i < len(lines):
    if lines[i].startswith("|") and i + 1 < len(lines) and SEP.match(lines[i + 1].strip()):
        n = cells(lines[i])
        j = i + 1
        while j < len(lines) and lines[j].startswith("|"):
            if cells(lines[j]) != n:
                bad += 1
                print(f"  列数不符 L{j + 1}: 期望 {n} 实际 {cells(lines[j])}: {lines[j][:120]}")
            j += 1
        tables += 1
        print(f"table@L{i + 1} 列数={n} 数据行={j - i - 2}")
        i = j
    else:
        i += 1
print(f"\n共 {tables} 张表，列数不符 {bad} 行")
