# -*- coding: utf-8 -*-
"""复核 17：(表, ID) 数值归属 / skilllist 与 bossskill 同号串值 / SA(2012) 承载必杀增益暴击。

结果写 work/refcheck_20261023_lead/verify/namespace_claim.json。
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_common import Db, out, pstr, write_json  # noqa: E402


def main():
    db = Db()
    sl = {r["skillid"]: r for r in db.skilllist}
    bs = db.skill_by_id
    overlap = sorted(set(sl) & set(bs))

    # 同号两表记录对照（取若干代表性 id）
    examples = []
    for sid in overlap:
        a, b = sl[sid], bs[sid]
        if a.get("ability") == b.get("skillid0"):
            continue  # 同类型的不算「串值」典型
        examples.append({
            "skillid": sid,
            "skilllist": {"ability": a.get("ability"), "name": (a.get("name") or "")[:50],
                          "params": {k: v for k, v in a.items() if k.startswith("param")}},
            "bossskill": {"type": b.get("skillid0"),
                          "params": {k: v for k, v in b.items() if k.startswith("skillparam")},
                          "s_ability": b.get("s_ability")},
        })
        if len(examples) >= 12:
            break

    # s_ability 指向 skilllist 的能力类型分布（bossskill 侧与 charainfo 侧）
    def sa_stats(records, key="s_ability"):
        dist = Counter()
        hits = 0
        for r in records:
            sa = r.get(key)
            if not sa:
                continue
            rec = sl.get(sa)
            if rec is None:
                dist["(不在 skilllist)"] += 1
                continue
            hits += 1
            dist[rec.get("ability")] += 1
        return {"records_with_sa": hits, "target_ability_types": dist.most_common(20)}

    sa_boss = sa_stats(db.bossskill)
    sa_char = sa_stats([r for r in db.charainfo if r.get("s_ability")])

    # s_ability -> 2012 且带 p4/p5 的数量
    def sa_2012(records, key="s_ability"):
        n = 0
        with_p4 = with_p5 = 0
        for r in records:
            sa = r.get(key)
            if not sa:
                continue
            rec = sl.get(sa)
            if rec is None or rec.get("ability") != 2012:
                continue
            n += 1
            with_p4 += 1 if "param4" in rec else 0
            with_p5 += 1 if "param5" in rec else 0
        return {"n": n, "with_p4": with_p4, "with_p5": with_p5}

    # 2012 p4/p5 数值同一性（数据本身无法区分两槽）
    t12 = [r for r in db.skilllist if r.get("ability") == 2012]
    both = [r for r in t12 if "param4" in r and "param5" in r]

    # bossskill type13 的 p6 与 skilllist 2012 的 p4：同号串值的典型后果示例
    conflict = []
    for r in db.bossskill:
        if r.get("skillid0") == 13 and r.get("skillparam6") is not None:
            sid = r["skillid"]
            a = sl.get(sid)
            if a is not None and a.get("ability") == 2012:
                conflict.append({"skillid": sid,
                                 "bossskill_type13_p6": r["skillparam6"],
                                 "skilllist_2012": {k: v for k, v in a.items()
                                                    if k.startswith("param")}})
    if not conflict:
        # 退一步：只要是同号但类型不同，就记录一条示例
        for r in db.bossskill[:0]:
            pass
    return_doc = {
        "generated_by": "scripts/refcheck_20261023_lead/verify_03_namespace.py",
        "id_overlap": {
            "skilllist_ids": len(sl), "bossskill_ids": len(bs),
            "numeric_overlap": len(overlap),
            "overlap_ratio_of_bossskill": round(len(overlap) / len(bs), 4),
        },
        "same_id_different_semantics_examples": examples,
        "sa_ability_targets": {
            "bossskill_s_ability": sa_boss,
            "charainfo_s_ability": sa_char,
            "bossskill_sa_2012": sa_2012(db.bossskill),
            "charainfo_sa_2012": sa_2012(db.charainfo),
        },
        "sa2012_p4_p5_identity": {
            "records": len(t12), "both_present": len(both),
            "equal": sum(1 for r in both if r["param4"] == r["param5"]),
            "only_p5": sum(1 for r in t12 if "param5" in r and "param4" not in r),
            "only_p4": sum(1 for r in t12 if "param4" in r and "param5" not in r),
        },
        "type13_vs_2012_same_id_conflict": conflict[:5],
        "our_evidence": [
            "output/character_skills/effect_ledger/README.md（namespace=layer/table/record_id/source_key，同号跨源不合并）",
            "output/character_skills/charainfo_types/README.md（charainfo.skillid[0] 与 bossskill.skillid0 同域，普通/Boss 分开）",
            "AGENTS.md §5（APK／缓存快照／普通／Boss 技能命名空间分开，同号 ID 不自动合并）",
            "output/character_skills/profiles/rules.json（规则键一律以 skilllist|<type>|/field 或 bossskill|<type>|/field 命名）",
        ],
    }
    p = write_json(out("namespace_claim.json"), return_doc)
    print("wrote", p)
    print("overlap", len(overlap), "of", len(bs), "bossskill ids")
    print("sa boss:", sa_boss)
    print("sa char:", sa_char)
    print("boss sa->2012:", return_doc["sa_ability_targets"]["bossskill_sa_2012"])
    print("2012 p4/p5 identity:", return_doc["sa2012_p4_p5_identity"])


if __name__ == "__main__":
    main()
