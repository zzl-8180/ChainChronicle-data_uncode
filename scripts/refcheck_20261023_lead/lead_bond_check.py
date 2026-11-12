# -*- coding: utf-8 -*-
"""Lead 独立核对：羁绊(supporterskill) 缺口 —— CACHE 311 vs APK 1916，参考项目用 sup1 join 到 2205 卡。
只读。输出 work/refcheck_20261023_lead/bond_check.json
"""
import json
import os
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead")
CACHE = os.path.join(ROOT, "output", "cache_full_20261015_v3", "decoded")
APK = os.path.join(ROOT, "output", "base_master")
REF_CARD = os.path.join(ROOT, "其他人的参考", "claude_cc_site_pages_给GPT_20261023",
                        "claude_cc_site_pages", "cards")


def load_raw(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    res = {}
    # 1) CACHE supporterskill
    cs = load_raw(os.path.join(CACHE, "supporterskill.data5.json.raw"))
    top = {k: (len(v) if isinstance(v, list) else type(v).__name__) for k, v in cs.items()
           if not k.startswith("_")}
    res["cache_supporterskill_top"] = top
    # 2) APK _mdSAbirity supporterskill
    sa = load_raw(os.path.join(APK, "_mdSAbirity.json"))
    res["apk_sabirity_top"] = {k: (len(v) if isinstance(v, list) else type(v).__name__)
                               for k, v in sa.items() if not k.startswith("_")}
    apk_sup = sa.get("supporterskill") or []
    apk_ids = set()
    for r in apk_sup:
        if isinstance(r, dict):
            for key in ("skillid", "id", "abilityid", "ability_id"):
                if key in r:
                    apk_ids.add(r[key])
    res["apk_supporterskill_records"] = len(apk_sup)
    if apk_sup:
        res["apk_supporterskill_sample_keys"] = list(apk_sup[0])
        res["apk_supporterskill_sample"] = apk_sup[0]
    # 3) CACHE charainfo sup1
    ci = load_raw(os.path.join(CACHE, "charainfo.data5.json.raw"))
    ci_rows = ci.get("charainfo") or []
    res["cache_charainfo_rows"] = len(ci_rows)
    def is_card(r):
        return isinstance(r, dict) and r.get("cid") is not None and (
            r.get("skillname") or r.get("name") or r.get("rarity"))
    if ci_rows and not is_card(ci_rows[0]):
        res["cache_charainfo_note"] = "首行不是卡记录"
    cards = [r for r in ci_rows if is_card(r)]
    res["cache_card_records"] = len(cards)
    sup1_cards = [r for r in cards if int(r.get("sup1") or 0) != 0]
    res["cache_cards_with_sup1"] = len(sup1_cards)
    # join by ability id
    if apk_sup:
        id_field = next((k for k in ("skillid", "id", "abilityid", "ability_id") if k in apk_sup[0]), None)
        if id_field:
            amap = {r[id_field]: r for r in apk_sup}
            joined = [r for r in sup1_cards if r.get("sup1") in amap]
            res["sup1_join_apk_matched_cards"] = len(joined)
            sample = joined[:3]
            res["sup1_join_sample"] = [{
                "cid": r.get("cid"), "name": r.get("name"), "sup1": r.get("sup1"),
                "apk_record_name": amap[r["sup1"]].get("name") or amap[r["sup1"]].get("sname"),
                "apk_record_text_head": str(amap[r["sup1"]].get("text") or amap[r["sup1"]].get("stext") or "")[:120],
            } for r in sample]
    # 4) reference card.json bond for sample cids
    ref_samples = {}
    for d in sorted(os.listdir(REF_CARD))[:4000]:
        if not d.startswith("cid10001"):
            continue
        p = os.path.join(REF_CARD, d, "data", "card.json")
        if os.path.exists(p):
            cj = load_raw(p)
            ref_samples[d] = {
                "keys": list(cj),
                "bond": json.dumps(cj.get("bond"), ensure_ascii=False)[:500],
            }
    res["ref_10001"] = ref_samples
    # 5) our page 10001 bond status
    ourp = os.path.join(ROOT, "output", "character_skills", "pages", "10001", "card.json")
    cj = load_raw(ourp)
    gs = cj["groups"]
    if isinstance(gs, dict):
        gs = [dict(group=k, **v) for k, v in gs.items()]
    res["our_page_10001_bond"] = next(({"status": g.get("status"),
                                       "skills": len(g.get("skills") or [])}
                                      for g in gs if g.get("group") == "bond"), None)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "bond_check.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("ref_10001",)},
                     ensure_ascii=False, indent=1)[:4000])
    print("ref_10001:", json.dumps(res["ref_10001"], ensure_ascii=False)[:800])


if __name__ == "__main__":
    main()
