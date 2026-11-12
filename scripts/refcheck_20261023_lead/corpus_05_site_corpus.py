# -*- coding: utf-8 -*-
"""网站语料可用性评估：site_parsed.json / detail_parsed.json。

输出: work/refcheck_20261023_lead/corpus/site_corpus_stats.json
      work/refcheck_20261023_lead/corpus/site_vs_mainline_examples.json
用法: .venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/corpus_05_site_corpus.py
"""
import os, sys, json, re, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_cards as cc

ROOT = r"E:\代码项目\锁链战记数据解包"
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead", "corpus")
SITEDIR = os.path.join(cc.BASES["new2"], "..", "site_diff", "out")
PAGES = os.path.join(ROOT, "output", "character_skills", "pages")

NUM_RE = re.compile(r"(\d+(?:\.\d+)?)")
MULT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*倍")
PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def ne(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() not in ("", "null")
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def stats_of(records, fields):
    n = len(records)
    out = {}
    for f in fields:
        c = sum(1 for r in records if ne(r.get(f)))
        out[f] = {"nonempty": c, "rate": round(c / n, 4) if n else 0}
    return out


def site_map():
    """从对方 card.json 的 site.candidates 建 cid -> site_id。"""
    idx = cc.index_by_cid(cc.BASES["new2"])
    m = {}
    for cid in idx:
        d, p = idx[cid][0]
        f = os.path.join(cc.data_path(p), "card.json")
        j = json.load(open(f, encoding="utf-8"))
        cands = ((j.get("site") or {}).get("candidates") or [])
        if cands:
            m[str(cid)] = [c.get("site_id") for c in cands]
    return m


def our_row_answers(cid):
    """我方页面：返回 special_move/ability 组的行摘要（japanese + answers 的 quantity_kind）。"""
    p = os.path.join(PAGES, str(cid), "card.json")
    if not os.path.exists(p):
        return None
    j = json.load(open(p, encoding="utf-8"))
    rows = []
    for g in j.get("groups") or []:
        if g.get("group") not in ("special_move", "ability", "sa"):
            continue
        for s in g.get("skills") or []:
            for r in s.get("rows") or []:
                rows.append({
                    "group": g["group"],
                    "row_class": r.get("row_class"),
                    "japanese": r.get("japanese") or "",
                    "kinds": [a.get("quantity_kind") for a in (r.get("answers") or [])],
                    "values": [a.get("value") for a in (r.get("answers") or [])],
                })
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    site = json.load(open(os.path.join(SITEDIR, "site_parsed.json"), encoding="utf-8"))
    detail = json.load(open(os.path.join(SITEDIR, "detail_parsed.json"), encoding="utf-8"))
    print("site_parsed:", len(site), " detail_parsed:", len(detail))

    site_fields = ["site_id", "jp_name", "zh_name", "rarity", "job", "cost", "home",
                   "weapon_kind", "weapon_name", "exp", "atkspeed", "illustrator", "voice",
                   "skill_name", "skill_text", "abilities", "ability_texts", "bond_name",
                   "bond_text", "source", "levels"]
    detail_fields = ["site_id", "jp_name", "zh_name", "rarity", "COST", "职业", "所属",
                     "攻击类型", "成长", "暴击几率", "攻击速度", "获取来源", "画师", "声优",
                     "登场日期", "skill_name", "skill_parts", "羁绊", "军记", "PASSIVE",
                     "Extra能力", "CrossWorld能力", "Leader能力", "共鸣能力", "战斗所属",
                     "介绍", "标签", "levels"]

    s_stat = stats_of(site, site_fields)
    d_stat = stats_of(detail, detail_fields)

    # 数字存在性
    skill_text_num = sum(1 for r in site if isinstance(r.get("skill_text"), str) and NUM_RE.search(r["skill_text"]))
    skill_text_mult = sum(1 for r in site if isinstance(r.get("skill_text"), str) and MULT_RE.search(r["skill_text"]))
    skill_text_pct = sum(1 for r in site if isinstance(r.get("skill_text"), str) and PCT_RE.search(r["skill_text"]))
    detail_parts_num = sum(1 for r in detail
                           if any(NUM_RE.search(x) for x in (r.get("skill_parts") or []) if isinstance(x, str)))

    # 网站 id -> cid
    m = site_map()
    mapped_site_ids = set()
    for v in m.values():
        mapped_site_ids.update(v)
    site_by_id = {r["site_id"]: r for r in site if "site_id" in r}
    detail_by_id = {r["site_id"]: r for r in detail if "site_id" in r}
    print("映射卡数:", len(m), " 不同 site_id:", len(mapped_site_ids),
          " 其中在 site_parsed 中可查到:", len([s for s in mapped_site_ids if s in site_by_id]))

    # 5 张同卡对比（用我方进度文档已核实的 site_id→cid）
    known = {"30236": 2453, "7229": 1268, "29": 79, "2020": 18, "5023": 155}
    compare = []
    for cid, sid in known.items():
        web = site_by_id.get(sid) or {}
        det = detail_by_id.get(sid) or {}
        rows = our_row_answers(cid)
        if rows is None:
            continue
        a_cnt = sum(1 for r in rows if r["row_class"] == "A")
        c_cnt = sum(1 for r in rows if r["row_class"] == "C")
        compare.append({
            "cid": cid, "site_id": sid,
            "web_jp_name": web.get("jp_name"),
            "web_skill_text": web.get("skill_text"),
            "web_skill_mults": MULT_RE.findall(web.get("skill_text") or ""),
            "web_skill_pcts": PCT_RE.findall(web.get("skill_text") or ""),
            "web_levels": (web.get("levels") or {}) and list((web.get("levels") or {}).keys()),
            "web_detail_has": {k: bool(ne(det.get(k))) for k in
                               ("Leader能力", "PASSIVE", "军记", "CrossWorld能力", "羁绊", "战斗所属", "共鸣能力")},
            "detail_skill_parts": det.get("skill_parts"),
            "our_rows": len(rows), "our_A": a_cnt, "our_C": c_cnt,
            "our_kinds": sorted({k for r in rows for k in r["kinds"] if k}),
        })

    # 自动找"网站有倍率数字、我方该行无对应倍率答案"的样例
    examples = []
    for cid, sids in m.items():
        if len(examples) >= 40:
            break
        web = None
        for s in sids:
            if s in site_by_id:
                web = site_by_id[s]
                break
        if not web:
            continue
        st = web.get("skill_text") or ""
        mults = MULT_RE.findall(st)
        if not mults:
            continue
        rows = our_row_answers(cid)
        if not rows:
            continue
        sm = [r for r in rows if r["group"] == "special_move"]
        if not sm:
            continue
        has_mult_answer = any(any(k and ("倍率" in k or "攻击力" in k) for k in r["kinds"]) for r in sm)
        if not has_mult_answer:
            examples.append({
                "cid": cid, "site_id": web.get("site_id"),
                "web_jp_name": web.get("jp_name"),
                "web_skill_text": st,
                "web_mults": mults,
                "our_special_move_rows": [{"class": r["row_class"], "jp": r["japanese"][:90],
                                           "kinds": r["kinds"]} for r in sm],
            })
    print("自动样例（网站有倍率、我方必杀无倍率答案）:", len(examples))
    for e in examples[:3]:
        print("  cid", e["cid"], "site", e["site_id"], "网站倍率", e["web_mults"], "| 我方行",
              [(r["class"], r["jp"][:40]) for r in e["our_special_move_rows"]])

    res = {
        "generated_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        "inputs": {
            "site_parsed": os.path.join(SITEDIR, "site_parsed.json"),
            "detail_parsed": os.path.join(SITEDIR, "detail_parsed.json"),
            "size": {"site_parsed": os.path.getsize(os.path.join(SITEDIR, "site_parsed.json")),
                     "detail_parsed": os.path.getsize(os.path.join(SITEDIR, "detail_parsed.json"))},
        },
        "counts": {"site_parsed": len(site), "detail_parsed": len(detail),
                   "cards_with_site_id": len(m),
                   "distinct_site_ids_in_cards": len(mapped_site_ids),
                   "mapped_ids_found_in_site_parsed": len([s for s in mapped_site_ids if s in site_by_id])},
        "site_field_coverage": s_stat,
        "detail_field_coverage": d_stat,
        "numeric_presence": {"skill_text_has_any_number": skill_text_num,
                             "skill_text_has_multiplier_x_bei": skill_text_mult,
                             "skill_text_has_percent": skill_text_pct,
                             "detail_skill_parts_has_number": detail_parts_num,
                             "ratio": {"any_number": round(skill_text_num / len(site), 4),
                                       "multiplier": round(skill_text_mult / len(site), 4)}},
        "known_five_comparison": compare,
    }
    with open(os.path.join(OUT, "site_corpus_stats.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "site_vs_mainline_examples.json"), "w", encoding="utf-8") as f:
        json.dump({"auto_examples": examples, "known_five": compare}, f, ensure_ascii=False, indent=1)
    print("已写 site_corpus_stats.json / site_vs_mainline_examples.json")


if __name__ == "__main__":
    main()
