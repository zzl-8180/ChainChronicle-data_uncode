"""Item 1 - roster vs. reference card-set ID difference list (machine readable).

Compares this project's playable roster (output/char_roster/, 2236 cids) with the
Claude downstream reference card set (2233 cids). Quantities are not forced to
match: every difference is classified with the concrete filter that produced it.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common as C  # noqa: E402

OUT = C.ROOT / "output" / "character_skills" / "scope_diff"
REF_MATCH = Path(C.ROOT) / "其他人的参考" / "claude_cc_site_pages" / "match_result.json"


def load_reference():
    with REF_MATCH.open(encoding="utf-8") as fh:
        return json.load(fh)


def main():
    C.enable_utf8_console()
    roster = C.roster()
    by_cid = {r["cid"]: r for r in roster}
    ref = load_reference()
    ref_ids = {int(k) for k in ref}
    our_ids = set(by_cid)

    only_us = sorted(our_ids - ref_ids)
    only_ref = sorted(ref_ids - our_ids)

    # playable pools on each side (recomputed here from the raw masters so the
    # classification is not inherited from prose)
    cache_chara = {r["cid"]: r for r in C.cache_rows("charainfo")}
    apk_chara = {r["cid"]: r for r in C.apk_rows("charainfo")}
    cache_playable = {c: r for c, r in cache_chara.items() if r.get("is_enemy") != 1 and (r.get("rarity") or 0) >= 1}
    apk_playable = {c: r for c, r in apk_chara.items() if r.get("is_enemy") != 1 and (r.get("rarity") or 0) >= 1}
    overlap = set(cache_playable) & set(apk_playable)

    # the reference's own filter (its build_cards.py playable()): illustrator AND
    # skillname AND rarity all truthy, with cache records admitted when "rarity" is present.
    def ref_playable(r):
        return bool(r.get("illustrator")) and bool(r.get("skillname")) and bool(r.get("rarity"))

    def ref_pool_reason(cid):
        r = apk_chara.get(cid)
        if r is None:
            return "REF_POOL_APK_RECORD_ABSENT"
        missing = [k for k in ("illustrator", "skillname", "rarity") if not r.get(k)]
        if missing:
            return "REF_POOL_FILTER_EXCLUDED:" + "+".join(missing)
        return "REF_POOL_INCLUDED"

    diff_rows = []
    for cid in only_us:
        r = by_cid[cid]
        reason = ref_pool_reason(cid)
        if cid == 99999:
            cls = "PLACEHOLDER_DUMMY_CID"
            note = "cid 99999 为占位编号（ダミィ，rarity2/cost4），名册按 is_enemy≠1 且 rarity≥1 纳入；参考侧同时被 illustrator 为空排除。"
        elif reason.startswith("REF_POOL_FILTER_EXCLUDED:illustrator"):
            cls = "REF_EXCLUDED_ILLUSTRATOR_EMPTY"
            note = "APK 记录 illustrator 为空，参考 build_cards.playable() 要求 illustrator 为真而排除；本项目名册口径（is_enemy≠1 且 rarity≥1）纳入。"
        else:
            cls = "REF_POOL_OTHER"
            note = f"参考侧可玩池判定为 {reason}。"
        apk_rec = apk_chara.get(cid) or {}
        diff_rows.append({
            "cid": cid,
            "name": r.get("name"),
            "title": r.get("title"),
            "our_source": r.get("data_source"),
            "our_rarity": r.get("rarity"),
            "in_our_roster": True,
            "in_reference": False,
            "direction": "ONLY_OURS",
            "reason_class": cls,
            "reference_pool_reason": reason,
            "has_cache_record": cid in cache_chara,
            "apk_is_enemy": apk_rec.get("is_enemy"),
            "apk_illustrator": apk_rec.get("illustrator"),
            "apk_skillname": apk_rec.get("skillname"),
            "apk_skilltext": apk_rec.get("skilltext"),
            "note": note,
        })

    for cid in only_ref:
        diff_rows.append({
            "cid": cid, "in_our_roster": False, "in_reference": True,
            "direction": "ONLY_REFERENCE", "reason_class": "UNEXPLAINED",
            "note": "参考侧存在但不在本项目名册；需单独追查。",
        })

    # cards that are present on both sides but carry a reference-side marker
    marked = []
    for cid in sorted(our_ids & ref_ids):
        st = ref[str(cid)].get("status")
        if st in ("排除", "网站上没有"):
            marked.append({
                "cid": cid,
                "name": by_cid[cid].get("name"),
                "reference_status": st,
                "reference_match_ids": ref[str(cid)].get("site_ids"),
                "in_our_roster": True,
                "note": ("参考侧标记「排除」：它自建卡但未用于网站对照（如 7107 ユグド）。本项目名册保留该 cid。"
                         if st == "排除" else
                         "参考侧标记「网站上没有」：属其新建卡（网站无对应条目）。"),
            })

    # candidates that the reference excluded on purpose, for cross-checking
    ref_status_counter = collections.Counter(v.get("status") for v in ref.values())

    # the reference's own pool, recomputed from its declared filter
    # (build_cards.playable(): illustrator AND skillname AND rarity on the APK side;
    #  "rarity" in record on the cache side)
    ref_pool = {c for c, r in apk_chara.items() if ref_playable(r)}
    ref_pool |= {c for c, r in cache_chara.items() if "rarity" in r}

    summary = {
        "our_roster_playable": len(our_ids),
        "reference_cards": len(ref_ids),
        "only_ours": len(only_us),
        "only_reference": len(only_ref),
        "net_difference": len(our_ids) - len(ref_ids),
        "apk_playable_pool_ours": len(apk_playable),
        "reference_recomputed_pool": len(ref_pool),
        "reference_recomputed_pool_matches_cards": len(ref_pool) == len(ref_ids),
        "apk_playable_pool_reference": len({c for c in ref_pool if c not in cache_chara}),
        "cache_playable_pool_both": len(cache_playable),
        "apk_cache_overlap": len(overlap),
        "ours_union_check": len(cache_playable) + len(apk_playable) - len(overlap),
        "reference_status_counts": dict(ref_status_counter),
        "quantities_forced_equal": False,
        "reason_class_counts": dict(collections.Counter(r["reason_class"] for r in diff_rows)),
        "method": ("仅我方 = 名册 playable cid 减去参考 match_result.json 键；仅对方 = 反向。"
                   "原因分类由两侧实际过滤条件复算：本项目口径 is_enemy≠1 且 rarity≥1；"
                   "参考 build_cards.playable() = illustrator 且 skillname 且 rarity 均为真。"),
        "boundary": ("本项目名册口径与参考口径不同，不追求数量相同。名册完成不等于参考侧遗漏即为错误；"
                     "差异仅作范围透明化，不改变任何角色处理。"),
    }

    diff = {
        "generated_by": "scripts/character_skills/scope_diff.py",
        "our_input": "output/char_roster/data/playable_characters.json",
        "reference_input": "其他人的参考/claude_cc_site_pages/match_result.json（只读）",
        "summary": summary,
        "only_ours": [r for r in diff_rows if r["direction"] == "ONLY_OURS"],
        "only_reference": [r for r in diff_rows if r["direction"] == "ONLY_REFERENCE"],
        "reference_marked_cards": marked,
        "reference_excluded_by_design": [r for r in marked if r["reference_status"] == "排除"],
    }
    C.write_json(OUT / "scope_diff.json", diff)

    header = ["cid", "name", "title", "direction", "reason_class", "our_source", "our_rarity",
              "in_our_roster", "in_reference", "has_cache_record", "apk_illustrator",
              "apk_skillname", "reference_pool_reason", "note"]
    rows = []
    for r in sorted(diff_rows, key=lambda x: (x["direction"], x["cid"])):
        rows.append([r.get(k) for k in header])
    C.write_csv(OUT / "scope_diff.csv", header, rows)

    # full side-by-side table, all roster rows (for auditing, not only diffs)
    ref_rows = []
    for cid in sorted(our_ids):
        st = ref.get(str(cid), {})
        ref_rows.append({
            "cid": cid,
            "name": by_cid[cid].get("name"),
            "our_source": by_cid[cid].get("data_source"),
            "in_reference": str(cid) in ref,
            "reference_status": st.get("status"),
            "reference_site_ids": json.dumps(st.get("site_ids"), ensure_ascii=False) if st.get("site_ids") else "",
        })
    C.write_json(OUT / "roster_side_by_side.json", {"rows": ref_rows, "count": len(ref_rows)})

    C.write_json(OUT / "summary.json", summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for r in diff["only_ours"]:
        print("ONLY_OURS", r["cid"], r["name"], r["reason_class"])
    print("ONLY_REFERENCE", [r["cid"] for r in diff["only_reference"]])
    print("REFERENCE_MARKED", [(m["cid"], m["name"], m["reference_status"]) for m in marked])


if __name__ == "__main__":
    main()
