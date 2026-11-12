# -*- coding: utf-8 -*-
"""params_knowledge.py — 提取对方三个脚本里的「知识表」并与 param_table 对账。

输出 work/refcheck_20261023_lead/params/knowledge_tables.json

做法：把对方 scripts 目录加到 sys.path 后真实 import 模块（这些模块在 import 时只定义常量、
不读写文件），从而拿到 ast 字面量提取拿不到的内容（REFERENCE 里含变量拼接、unpack_text.NAMED
里含 rf-string 正则）。同时用 ast 记录每个表在源文件中的起始行号。
"""
import ast
import json
import re
import sys
import importlib

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
OUT = P.OUT
SCRIPTS = P.NEW1 / "scripts"


def block_lines(path, name):
    """返回该模块级赋值语句的 (起始行, 结束行)。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == name:
            return node.lineno, node.end_lineno
    return None, None


def main():
    new = P.load(P.NEW1 / "param_table.json")
    rows = {P.key(r): r for r in new["rows"]}
    sys.path.insert(0, str(SCRIPTS))
    ip = importlib.import_module("infer_params")
    ut = importlib.import_module("unpack_text")
    nb = importlib.import_module("numbers")
    res = {"scripts": str(SCRIPTS), "tables": {}}

    def rowview(k):
        r = rows.get(k)
        if not r:
            return {"in_param_table": False}
        return {"in_param_table": True, "pt_status": r["status"], "pt_label": r["label"],
                "pt_conversion": r["conversion"], "pt_unit": r["unit"],
                "pt_hits": r["hits"], "pt_decisive": r["decisive_hits"]}

    for dname in ("CONFIRMED", "USER_CONFIRMED", "REVIEWED", "REFERENCE"):
        d = getattr(ip, dname)
        s, e = block_lines(SCRIPTS / "infer_params.py", dname)
        items = []
        for k, v in d.items():
            note = v[3] if len(v) > 3 else ""
            items.append({"table": k[0], "type": k[1], "slot": k[2], "label": v[0], "conversion": v[1],
                          "unit": v[2], "note": note,
                          "agree_label": rows.get(k, {}).get("label") == v[0],
                          "agree_conv": rows.get(k, {}).get("conversion") == v[1],
                          **rowview(k)})
        res["tables"][dname] = {"count": len(items), "src_line_from": s, "src_line_to": e, "entries": items}

    # charainfo 镜像（infer_params.py 143-145 行在 import 后已经写入 CONFIRMED）
    res["tables"]["CONFIRMED"]["count_after_mirror"] = len(ip.CONFIRMED)
    res["tables"]["CONFIRMED"]["mirror_note"] = "源文件只写 25 条 bossskill/skilllist；143-145 行的循环把它们镜像到 charainfo，运行时 37 条"

    # unpack_text.NAMED
    s, e = block_lines(SCRIPTS / "unpack_text.py", "NAMED")
    named = [{"label": v[0], "pattern": v[1], "types": list(v[2]) if len(v) > 2 else None}
             for v in ut.NAMED]
    res["tables"]["unpack_text.NAMED"] = {"count": len(named), "src_line_from": s, "src_line_to": e,
                                          "entries": named}
    res["tables"]["numbers.CONV"] = {"count": len(nb.CONV), "entries": list(nb.CONV)}
    res["tables"]["numbers.USABLE"] = {"count": len(nb.USABLE), "entries": list(nb.USABLE)}

    (OUT / "knowledge_tables.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, t in res["tables"].items():
        print(f"{name}: count={t['count']} src_line={t.get('src_line_from')}-{t.get('src_line_to')}")
    print()
    print("--- REFERENCE ---")
    for e in res["tables"]["REFERENCE"]["entries"]:
        print(f"  {e['table']} t{e['type']} {e['slot']} -> {e['label']} {e['conversion']} {e['unit']} | note={e['note']} | "
              f"pt={e.get('pt_status')}/{e.get('pt_label')} hits={e.get('pt_hits')} dec={e.get('pt_decisive')}")
    print("--- unpack_text.NAMED ---")
    for e in res["tables"]["unpack_text.NAMED"]["entries"]:
        print(f"  {e['label']} types={e['types']} :: {e['pattern']}")
    print("--- numbers.CONV ---")
    print(" ", res["tables"]["numbers.CONV"]["entries"])
    print("--- numbers.USABLE ---")
    print(" ", res["tables"]["numbers.USABLE"]["entries"])


if __name__ == "__main__":
    main()
