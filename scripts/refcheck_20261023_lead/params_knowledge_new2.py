# -*- coding: utf-8 -*-
"""params_knowledge_new2.py — new2（给GPT包）脚本里的知识表条目数，并与 new1 对照。"""
import importlib
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(P.NEW2 / "scripts"))
ip = importlib.import_module("infer_params")
print("new2 infer_params:")
for d in ("CONFIRMED", "USER_CONFIRMED", "REVIEWED", "REFERENCE"):
    print(f"  {d}: {len(getattr(ip, d))}")
print("  REVIEWED 明细:")
for k, v in ip.REVIEWED.items():
    print(f"    {k} -> {v}")
ut = importlib.import_module("unpack_text")
print(f"new2 unpack_text.NAMED: {len(ut.NAMED)}")
print("new2 unpack_text 新增函数:", [n for n in ("per_member", "fill_variants", "fill_atk", "fix_tiers", "norm_n")
                                    if hasattr(ut, n)])
nb = importlib.import_module("numbers")
print("new2 numbers.CONV:", list(nb.CONV))
print("new2 numbers.USABLE:", list(nb.USABLE))
