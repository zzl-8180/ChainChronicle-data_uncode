# -*- coding: utf-8 -*-
"""params_candidates.py — 生成「可直接用于我方字段解释」的候选清单（最多 40 条）。

排序维度（依次）：证据等级（解包确认/用户确认 > 参考推断 > 统计推断）
                × 我方是否尚未覆盖该 effect type
                × decisive_hits 降序
另标 rec：「可直接用于填数」/「候选，需我方验证」/「与我方证据冲突，不要采用」。

我方已用代码/原生检查覆盖的 effect type（见 output/ordinary_effects、output/boss_chain、output/boss_heal）：
  skilllist 7 99 1008 1017 1095 2003 2012 3000；bossskill 13 27 105 112
"""
import json
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
OUT = P.OUT

OURS = {("skilllist", 7), ("skilllist", 99), ("skilllist", 1008), ("skilllist", 1017), ("skilllist", 1095),
        ("skilllist", 2003), ("skilllist", 2012), ("skilllist", 3000),
        ("bossskill", 13), ("bossskill", 27), ("bossskill", 105), ("bossskill", 112)}
TIER = {"解包确认": 4, "用户确认": 4, "参考推断": 3, "统计推断": 2}
# 与我方已确认语义直接冲突的（表, type, slot）→ 给出我方语义
CONFLICT = {
    ("skilllist", 2012, "param7"): "我方：param7 = 支持目标数量上限（1/20），不是伤害倍",
    ("skilllist", 2012, "param8"): "我方：param8 = TARGET_TYPE（31=pGROUP_ALL，64=MYSELF），不是伤害倍",
    ("skilllist", 2003, "param5"): "我方：param5 = 攻者自身 Support2 _move 增量（同 2003 布局 p4/p5/p6=_attack/_move/_defense）",
    ("skilllist", 2003, "param6"): "我方：param6 = 攻者自身 Support2 _defense 增量",
    ("skilllist", 99, "param1"): "我方：param1 = Normal 攻击触发阈值（源值全 1），不是几率",
    ("skilllist", 99, "param2"): "我方：param2 = Critical 攻击触发阈值",
}
SOURCE = {
    "解包确认": "对方 CONFIRMED（称原项目代码证实）",
    "用户确认": "用户口述确认（HANDOFF 2026-10-22/23；infer_params.USER_CONFIRMED）",
    "参考推断": "回收：我方交付包 cc_skill_values_20261021 / 原项目 30236 逐条审定",
    "统计推断": "对方网站统计（hits/decisive）",
}


def main():
    d = json.loads((OUT / "new_rows_since_1017.json").read_text(encoding="utf-8"))
    pool = []
    for tag, rows in (("新增", d["added"]), ("改判", d["changed"])):
        for r in rows:
            t = r["status"]
            if t not in TIER and (r["decisive_hits"] or 0) < 20:
                continue
            pool.append((tag, r))
    out = []
    for tag, r in pool:
        k = (r["table"], r["type"], r["slot"])
        ours = k[:2] in OURS
        tier = TIER.get(r["status"], 0)
        conflict = CONFLICT.get(k)
        if conflict:
            rec = "与我方证据冲突，不要采用"
        elif r["status"] in ("解包确认", "用户确认"):
            rec = "可直接采用（确认级）"
        else:
            rec = "候选，需我方验证"
        out.append({
            "tag": tag, "table": r["table"], "type": r["type"], "slot": r["slot"],
            "status": r["status"], "label": r["label"], "conversion": r["conversion"], "unit": r["unit"],
            "hits": r["hits"], "cards_with_value": r["cards_with_value"], "hit_rate": r["hit_rate"],
            "decisive_hits": r["decisive_hits"], "decisive_cases": r["decisive_cases"],
            "examples": r["examples"], "site_statistics": r["site_statistics"],
            "our_type_covered": ours, "recommend": rec, "conflict_note": conflict or "",
            "evidence_source": SOURCE.get(r["status"], r["status"]),
            "score": (tier, 1 if not ours else 0, r["decisive_hits"] or 0, r["hits"] or 0),
        })
    out.sort(key=lambda e: e["score"], reverse=True)
    top = out[:40]
    for i, e in enumerate(top, 1):
        e["rank"] = i
    (OUT / "candidate_list_40.json").write_text(json.dumps({
        "note": ("排序：证据等级(tier) → 我方未覆盖 → decisive_hits → hits。候选池 = 63 条新增 + 33 条改判里 "
                 "status 属 解包确认/用户确认/参考推断/统计推断，或 decisive_hits>=20 的行"),
        "pool_size": len(out), "shown": len(top),
        "our_covered_types": sorted("%s type%s" % k for k in OURS),
        "candidates": top, "rest": out[40:],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    for e in top:
        print(f"{e['rank']:2d}. [{e['tag']}] {e['table']} t{e['type']} {e['slot']} | {e['status']} | "
              f"{e['label']} {e['conversion']} {e['unit']} | hits {e['hits']}/{e['cards_with_value']} "
              f"dec {e['decisive_hits']}/{e['decisive_cases']} | ours={e['our_type_covered']} | {e['recommend']}")
        if e["conflict_note"]:
            print(f"      !! {e['conflict_note']}")
    print(f"\npool={len(out)} shown={len(top)}")


if __name__ == "__main__":
    main()
