# -*- coding: utf-8 -*-
"""相对我方主线的增量对照：对方 card.json 的 13 组结构 vs 我方 links 台账。

输入（只读）:
  对方: 新版2 .../claude_cc_site_pages/cards/<dir>/data/card.json
  我方: output/character_skills/links/link_summary.json
        output/character_skills/links/character_skills.jsonl
输出: work/refcheck_20261023_lead/corpus/increment_vs_mainline.json
用法: .venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/corpus_03_increment_join.py
"""
import os, sys, json, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_cards as cc

ROOT = r"E:\代码项目\锁链战记数据解包"
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead", "corpus")

CATS = ["special_move", "ability", "sa", "sympathy", "leader", "class", "extra",
        "passive", "bond", "heroic", "denju", "denju_lb", "crossworld"]


def nonempty(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() not in ("", "null")
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def theirs_per_card():
    """对方 card.json -> {cid: {cat: 记录数}}，只统计直接可见的记录/技能。"""
    base = cc.BASES["new2"]
    idx = cc.index_by_cid(base)
    out = {}
    for cid in sorted(idx, key=lambda x: (len(x), x)):
        for dname, dpath in idx[cid]:
            f = os.path.join(cc.data_path(dpath), "card.json")
            if not os.path.exists(f):
                continue
            j = json.load(open(f, encoding="utf-8"))
            per = {}
            # special_move: skill.patterns
            per["special_move"] = len((j.get("skill") or {}).get("patterns") or [])
            per["ability"] = len(j.get("abilities") or [])
            per["sa"] = 1 if nonempty((j.get("skill") or {}).get("sa")) else 0
            per["sympathy"] = 1 if nonempty(j.get("sympathy")) else 0
            per["leader"] = 1 if nonempty(j.get("leader")) else 0
            per["class"] = 1 if nonempty(j.get("job_ability")) else 0
            per["extra"] = len(j.get("extra") or [])
            per["passive"] = 1 if nonempty(j.get("passive")) else 0
            per["bond"] = 1 if nonempty(j.get("bond")) else 0
            per["heroic"] = 1 if nonempty(j.get("heroic")) else 0
            dj = j.get("denju")
            per["denju"] = 1 if nonempty(dj) else 0
            per["denju_lb"] = len((dj or {}).get("limit_break") or []) if isinstance(dj, dict) else 0
            per["crossworld"] = 1 if nonempty(j.get("crossworld")) else 0
            # 额外事实
            per["_site_ids"] = [c.get("site_id") for c in ((j.get("site") or {}).get("candidates") or [])]
            per["_site_status"] = (j.get("site") or {}).get("status")
            per["_buddy_id"] = (j.get("basic") or {}).get("buddy_id")
            per["_buddy_of"] = (j.get("basic") or {}).get("buddy_of")
            per["_atknumber"] = (j.get("basic") or {}).get("atknumber")
            per["_shotspeed"] = (j.get("basic") or {}).get("shotspeed")
            per["_crinumber"] = (j.get("basic") or {}).get("crinumber")
            per["_source"] = j.get("source")
            per["_denju_weapon_change"] = (dj or {}).get("weapon_change") if isinstance(dj, dict) else None
            per["_dir_cid"] = cid
            # 以 card.json 的 cid 为准（目录名 'cid8150422部隊 No.13' 实际 cid=8150）
            real = j.get("cid")
            out[str(real if real is not None else cid)] = per
    return out


def ours_per_card():
    """我方 links/character_skills.jsonl -> {cid: {group: 记录数}}。"""
    p = os.path.join(ROOT, "output", "character_skills", "links", "character_skills.jsonl")
    out = {}
    with open(p, encoding="utf-8") as f:
        for line in f:
            j = json.loads(line)
            cid = str(j.get("cid"))
            g = {}
            for grp in j.get("groups") or []:
                g[grp.get("group")] = len(grp.get("records") or [])
            out[cid] = g
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    print("读对方 card.json ...")
    T = theirs_per_card()
    print("  卡数", len(T))
    print("读我方 links ...")
    O = ours_per_card()
    print("  卡数", len(O))

    # 按组：出现卡数（对方）/ 记录卡数（我方）
    summary = {}
    for cat in CATS:
        t_cards = sum(1 for v in T.values() if v.get(cat, 0) > 0)
        o_cards = sum(1 for v in O.values() if v.get(cat, 0) > 0)
        t_recs = sum(v.get(cat, 0) for v in T.values())
        o_recs = sum(v.get(cat, 0) for v in O.values())
        common = set(c for c in T if c in O)
        only_t = sorted(c for c in common if T[c].get(cat, 0) > 0 and O[c].get(cat, 0) == 0)
        only_o = sorted(c for c in common if O[c].get(cat, 0) > 0 and T[c].get(cat, 0) == 0)
        both = sorted(c for c in common if T[c].get(cat, 0) > 0 and O[c].get(cat, 0) > 0)
        # 记录数是否逐卡一致
        rec_mismatch = [c for c in both if T[c].get(cat, 0) != O[c].get(cat, 0)]
        summary[cat] = {
            "their_cards": t_cards, "our_cards": o_cards,
            "their_records": t_recs, "our_records": o_recs,
            "both_cards": len(both),
            "only_theirs": len(only_t), "only_theirs_sample": only_t[:12],
            "only_ours": len(only_o), "only_ours_sample": only_o[:12],
            "record_count_mismatch_cards": len(rec_mismatch),
            "record_count_mismatch_sample": rec_mismatch[:12],
        }

    # site 映射
    site_cards = sum(1 for v in T.values() if v.get("_site_ids"))
    site_ids = set()
    for v in T.values():
        for s in v.get("_site_ids") or []:
            site_ids.add(s)
    status = collections.Counter(v.get("_site_status") for v in T.values())
    buddy = sum(1 for v in T.values() if v.get("_buddy_id") or v.get("_buddy_of"))

    result = {
        "generated_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        "note": "their = 新版2 card.json 内可见记录数；our = output/character_skills/links/character_skills.jsonl 逐组记录数",
        "group_summary": summary,
        "site_mapping": {"cards_with_site_id": site_cards,
                         "distinct_site_ids": len(site_ids),
                         "status_distribution": dict(status)},
        "buddy_cards": buddy,
    }
    with open(os.path.join(OUT, "increment_vs_mainline.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("已写 increment_vs_mainline.json")
    print(f"{'group':14s}{'对方卡':>7s}{'我方卡':>7s}{'对方记录':>9s}{'我方记录':>9s}{'仅对方':>7s}{'仅我方':>7s}{'记录数不符':>10s}")
    for cat in CATS:
        s = summary[cat]
        print(f"{cat:14s}{s['their_cards']:7d}{s['our_cards']:7d}{s['their_records']:9d}{s['our_records']:9d}"
              f"{s['only_theirs']:7d}{s['only_ours']:7d}{s['record_count_mismatch_cards']:10d}")
    print("site:", site_cards, "张有 site_id,", len(site_ids), "个不同 site_id, status:", dict(status))
    print("buddy:", buddy)


if __name__ == "__main__":
    main()
