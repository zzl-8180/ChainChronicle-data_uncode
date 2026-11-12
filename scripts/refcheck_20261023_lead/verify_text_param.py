# -*- coding: utf-8 -*-
"""文本 × 参数槽 相关性检查（探索用）：对 2012 / 3000 / 1051 / 1009 等，
按记录自带日文描述的关键词分组，统计各槽位出现率，验证属性归属。"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from verify_common import Db  # noqa: E402

KEYS = [
    ("attack", ["攻撃力"]),
    ("defence", ["防御力"]),
    ("move", ["移動速度"]),
    ("crit_rate", ["クリティカル発生率", "クリ率"]),
    ("crit_dmg", ["クリティカル威力"]),
    ("atkspeed", ["攻撃速度"]),
    ("interval", ["攻撃間隔"]),
]


def real_text(r):
    t = r.get("text") or ""
    return t if len(t) > 25 and "サブアビリティ" not in t else ""


def main(argv):
    db = Db()
    types = [int(x) for x in argv[0].split(",")] if argv else [2012, 3000]
    for ty in types:
        recs = [r for r in db.skilllist if r.get("ability") == ty]
        withtext = [(r, real_text(r)) for r in recs if real_text(r)]
        print("=" * 100)
        print("type", ty, "records", len(recs), "with real text", len(withtext))
        # 槽位存在率（按关键词组合分组）
        groups = defaultdict(list)
        for r, t in withtext:
            sig = tuple(k for k, kws in KEYS if any(w in t for w in kws))
            groups[sig].append(r)
        for sig, rs in sorted(groups.items(), key=lambda x: -len(x[1])):
            present = Counter()
            for r in rs:
                for i in range(0, 10):
                    if "param%d" % i in r:
                        present[i] += 1
            top = "%d" % len(rs)
            print("  n=%-4s keywords=%-40s slots=%s" %
                  (top, ",".join(sig) or "(none)",
                   {i: present[i] for i in sorted(present)}))
        print("  -- 记录级样例（含 防御力 或 攻撃速度） --")
        n = 0
        for r, t in withtext:
            if ("防御力" in t or "攻撃速度" in t or "攻撃間隔" in t) and n < 10:
                n += 1
                ps = {k: v for k, v in r.items() if k.startswith("param")}
                print("   ", r["skillid"], ps)
                print("      ", t[:150].replace("\n", " "))


if __name__ == "__main__":
    main(sys.argv[1:])
