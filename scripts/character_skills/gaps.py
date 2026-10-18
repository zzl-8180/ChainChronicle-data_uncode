"""Item 4 - gap / candidate queue.

Aggregates every description or effect that has no confirmed rule yet across the
characters already processed, ranks it by the number of characters and
descriptions actually affected, and annotates each gap with the ready-made lead
(from the Claude reference cross-check) when one exists.

Leads are ordering hints only. Nothing here is marked as confirmed.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common as C  # noqa: E402
import rules as R  # noqa: E402

OUT = C.ROOT / "output" / "character_skills" / "gaps"
PROFILES = C.ROOT / "output" / "character_skills" / "profiles"
CROSSCHECK = C.REFERENCE_ANALYSIS / "crosscheck_summary.json"


def load_leads() -> dict:
    """(table, type, slot) -> reference candidate row; leads only."""
    if not CROSSCHECK.exists():
        return {}
    doc = json.loads(CROSSCHECK.read_text(encoding="utf-8"))
    out = {}
    for row in doc.get("值得本项目验证的未研究类型候选(decisive>=10)", []):
        slot = row.get("slot") or ""
        out[(row.get("table"), row.get("type"), "/" + slot.lstrip("/"))] = {
            "reference_inference": row.get("对方推断"),
            "hits": row.get("hits"),
            "decisive": row.get("decisive"),
            "examples": row.get("例证"),
            "status": "线索（对方统计推断，本项目未确认）",
        }
    return out


def main():
    C.enable_utf8_console()
    leads = load_leads()
    profiles = [json.loads(l) for l in (PROFILES / "profiles.jsonl").open(encoding="utf-8")]
    records = {r["rec_key"]: r for r in (PROFILES / "records.jsonl").open(encoding="utf-8") and
               [json.loads(l) for l in (PROFILES / "records.jsonl").open(encoding="utf-8")]}

    field_chars = collections.defaultdict(set)
    field_records = collections.defaultdict(set)
    field_groups = collections.defaultdict(collections.Counter)
    block_chars = collections.defaultdict(set)
    block_records = collections.defaultdict(set)
    block_frags = collections.Counter()
    block_frags_unexpl = collections.Counter()
    block_unexpl_fields = collections.Counter()
    char_examples = collections.defaultdict(list)
    lead_keys = collections.defaultdict(set)
    field_nonzero_chars = collections.defaultdict(set)
    broken = collections.Counter()
    broken_chars = collections.defaultdict(set)

    for p in profiles:
        cid = p["cid"]
        seen_field = set()
        seen_block = set()
        for g in p["groups"]:
            for ref in g["records"]:
                r = records.get(ref["rec_key"])
                if not r:
                    continue
                t, et = r["table"], r["effect_type"]
                hint = (r.get("type_hint") or {}).get("value")
                et_lead = et if et is not None else hint
                block = (t, et)
                if block not in seen_block:
                    seen_block.add(block)
                    block_chars[block].add(cid)
                block_records[block].add(ref["rec_key"])
                frags = r["fragments"]
                if frags:
                    block_frags[block] += len(frags)
                    block_frags_unexpl[block] += sum(1 for f in frags if f["status"] == "UNEXPLAINED_FRAGMENT")
                for u in r["unexplained"]:
                    key = (t, et, u["f"])
                    block_unexpl_fields[block] += 1
                    field_records[key].add(ref["rec_key"])
                    field_groups[key][g["label"]] += 1
                    if key not in seen_field:
                        seen_field.add(key)
                        field_chars[key].add(cid)
                        if len(char_examples[key]) < 5:
                            char_examples[key].append(f"{cid} {p['name']}")
                    if u.get("raw") not in (0, 0.0) and u.get("reason") != "NON_FINITE_VALUE":
                        field_nonzero_chars[key].add(cid)
                    if et_lead is not None:
                        lead_keys.setdefault(key, set()).add((t, et_lead, u["f"]))
                for ch in r["children"]:
                    # children belong to the same (table, type) block, so the type-level
                    # counters must include them or they would disagree with the field level
                    cb = (ch["table"], ch.get("effect_type"))
                    if cb not in seen_block:
                        seen_block.add(cb)
                        block_chars[cb].add(cid)
                    block_records[cb].add(ref["rec_key"] + "|" + str(ch["record_id"]))
                    for u in ch["unexplained"]:
                        key = (ch["table"], ch["effect_type"], u["f"])
                        block_unexpl_fields[cb] += 1
                        field_records[key].add(ref["rec_key"] + "|" + str(ch["record_id"]))
                        field_groups[key][g["label"]] += 1
                        if key not in seen_field:
                            seen_field.add(key)
                            field_chars[key].add(cid)
                            if len(char_examples[key]) < 5:
                                char_examples[key].append(f"{cid} {p['name']}")
                        if u.get("raw") not in (0, 0.0) and u.get("reason") != "NON_FINITE_VALUE":
                            field_nonzero_chars[key].add(cid)
        for u in p["unresolved"]:
            broken[(u.get("expected_table"), (u.get("reference_field") or "").split("[")[0])] += 1
            broken_chars[(u.get("expected_table"), (u.get("reference_field") or "").split("[")[0])].add(cid)

    field_rows = []
    for key, chars in field_chars.items():
        t, et, f = key
        lead = None
        for lk in (lead_keys.get(key) or [(t, et, f)]):
            cands = [lk]
            # the reference table names the bossskill / charainfo slots without the
            # leading "skill" prefix; try both spellings, never merge values
            if lk[2].startswith("/skillparam") or lk[2].startswith("/skillflag"):
                cands.append((lk[0], lk[1], lk[2].replace("/skill", "/", 1)))
            for c in cands:
                lead = leads.get(c)
                if lead:
                    break
            if lead:
                break
        field_rows.append({
            "gap_kind": "UNEXPLAINED_FIELD",
            "table": t,
            "effect_type": et,
            "field_path": f,
            "affected_characters": len(chars),
            "affected_characters_nonzero": len(field_nonzero_chars.get(key, ())),
            "affected_records": len(field_records[key]),
            "skill_groups": dict(field_groups[key]),
            "example_cids": char_examples[key],
            "candidate_lead": lead,
        })
    field_rows.sort(key=lambda r: (-r["affected_characters_nonzero"], -r["affected_characters"],
                                   -r["affected_records"], str(r["effect_type"])))

    block_rows = []
    for key, chars in block_chars.items():
        # a "gap" block is one that still has unexplained fields or unattributed
        # fragments; blocks that are fully answered are not gaps and are dropped
        if not block_unexpl_fields.get(key) and not block_frags_unexpl.get(key):
            continue
        t, et = key
        cands = [dict(leads[k], field_path=k[2]) for k in leads if k[0] == t and k[1] == et]
        cands.sort(key=lambda x: -(x.get("hits") or 0))
        block_rows.append({
            "gap_kind": "TYPE_WITHOUT_RULES_OR_PARTIAL",
            "table": t,
            "effect_type": et,
            "affected_characters": len(chars),
            "affected_records": len(block_records[key]),
            "descriptions": block_frags[key],
            "descriptions_unexplained": block_frags_unexpl[key],
            "unexplained_fields": block_unexpl_fields.get(key, 0),
            "candidate_leads": cands,
            "candidate_lead_count": len(cands),
        })
    # types that have some confirmed rules still carry unexplained fields
    block_rows.sort(key=lambda r: (-r["affected_characters"], -r["descriptions_unexplained"]))

    broken_rows = [{
        "gap_kind": "BROKEN_LINK",
        "expected_table": k[0],
        "reference_field": k[1],
        "occurrences": v,
        "affected_characters": len(broken_chars[k]),
        "candidate_lead": None,
        "note": ("缓存无此 ID 且 APK 主表未导出该表，回退不可用；保留断链。"
                 if k[0] in ("denju",) else
                 "缓存与 APK 同命名空间均无此 ID；保留断链。"),
    } for k, v in broken.items()]
    broken_rows.sort(key=lambda r: -r["affected_characters"])
    # note the charainfo grouping used only for lead matching
    for r in field_rows:
        if r["table"] == "charainfo" and r["candidate_lead"]:
            r["lead_grouping"] = "按 charainfo.skillid[0] 与参考候选对齐（仅线索分组，非本项目确认的类型字段）"

    summary = {
        "generated_by": "scripts/character_skills/gaps.py",
        "inputs": {
            "profiles": "output/character_skills/profiles/profiles.jsonl",
            "records": "output/character_skills/profiles/records.jsonl",
            "reference_candidates": "output/reference_analysis/claude_cc_site_pages/crosscheck_summary.json（只读）",
        },
        "policy": ("候选只是排序线索，不是已确认。任何字段在规则字典出现前都保持未解释；"
                   "本队列不改变任何角色答案，只描述缺口规模。"),
        "counts": {
            "unexplained_field_gaps": len(field_rows),
            "type_level_gaps": len(block_rows),
            "broken_link_gaps": len(broken_rows),
            "gaps_with_reference_lead": sum(1 for r in field_rows if r["candidate_lead"]),
        },
        "field_gaps": field_rows,
        "type_gaps": block_rows,
        "broken_links": broken_rows,
    }
    C.write_json(OUT / "gap_queue.json", summary)

    header = ["rank", "gap_kind", "table", "effect_type", "field_path", "affected_characters",
              "affected_characters_nonzero", "affected_records", "skill_groups",
              "has_reference_lead", "reference_inference",
              "lead_hits", "lead_decisive", "lead_examples", "example_cids"]
    rows = []
    for i, r in enumerate(field_rows, start=1):
        lead = r["candidate_lead"] or {}
        rows.append([i, r["gap_kind"], r["table"], r["effect_type"], r["field_path"],
                     r["affected_characters"], r["affected_characters_nonzero"], r["affected_records"],
                     json.dumps(r["skill_groups"], ensure_ascii=False), bool(lead),
                     lead.get("reference_inference"), lead.get("hits"), lead.get("decisive"),
                     lead.get("examples"), " | ".join(r["example_cids"])])
    C.write_csv(OUT / "gap_queue.csv", header, rows)

    header2 = ["rank", "table", "effect_type", "affected_characters", "affected_records",
               "descriptions", "descriptions_unexplained", "unexplained_fields",
               "candidate_lead_count", "top_lead"]
    rows2 = []
    for i, r in enumerate(block_rows, start=1):
        top = (r["candidate_leads"] or [{}])[0]
        rows2.append([i, r["table"], r["effect_type"], r["affected_characters"], r["affected_records"],
                      r["descriptions"], r["descriptions_unexplained"], r["unexplained_fields"],
                      r["candidate_lead_count"],
                      f"{top.get('field_path')} {top.get('reference_inference')} "
                      f"(hits={top.get('hits')}, decisive={top.get('decisive')})" if top else ""])
    C.write_csv(OUT / "type_gaps.csv", header2, rows2)

    header3 = ["expected_table", "reference_field", "occurrences", "affected_characters", "note"]
    C.write_csv(OUT / "broken_links.csv", header3,
                [[r.get(h) for h in header3] for r in broken_rows])

    print(json.dumps(summary["counts"], ensure_ascii=False, indent=2))
    print("\nTop field gaps (by affected characters):")
    for r in field_rows[:20]:
        lead = r["candidate_lead"]
        lead_s = (f" ←线索 {lead['reference_inference']} hits={lead['hits']} dec={lead['decisive']}"
                  if lead else " ←无线索")
        print(f"  {r['table']:11s} type={str(r['effect_type']):5s} {r['field_path']:14s} "
              f"chars={r['affected_characters']:5d} nonzero={r['affected_characters_nonzero']:5d} "
              f"records={r['affected_records']:5d}{lead_s}")
    print("\nType-level gaps:")
    for r in block_rows[:15]:
        print(f"  {r['table']:11s} type={str(r['effect_type']):5s} chars={r['affected_characters']:5d} "
              f"records={r['affected_records']:5d} desc={r['descriptions']} "
              f"unexpl={r['descriptions_unexplained']} leads={r['candidate_lead_count']}")
    print("\nBroken links:")
    for r in broken_rows:
        print("  ", r)


if __name__ == "__main__":
    main()
