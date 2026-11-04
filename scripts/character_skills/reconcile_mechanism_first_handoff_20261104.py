#!/usr/bin/env python3
"""Reconcile the frozen mechanism-first 49/4 handoff against current formal products.

Reads the handoff, current card pages, decoded CACHE records, rules and effect ledger.
Writes only a new reconciliation report directory; never imports or modifies producers.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = ROOT / "output/share_bundle/20261104-mechanism-first-handoff-r1/payload"
DEFAULT_OUTPUT = ROOT / "output/character_skills/mechanism_first_reconciliation_20261104"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer(document, path: str):
    value = document
    for part in path.strip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def row_map(card: dict) -> dict:
    return {
        row["row_id"]: row
        for group in card.get("groups", [])
        for skill in group.get("skills", [])
        for row in skill.get("rows", [])
    }


def identity(answer: dict) -> str:
    source = answer["source"]
    return "|".join(map(str, [
        answer["effect_id"], source["layer"], source["table"],
        source["record_id"], answer["field_path"],
    ]))


def answer_identity(answer: dict) -> tuple:
    source = answer.get("source") or {}
    record_id = answer.get("record_id")
    if record_id is None:
        record_id = source.get("record_id")
    return (
        answer.get("rule_key"),
        answer.get("field_path") or source.get("field_path"),
        answer.get("table") or source.get("table"),
        record_id,
        answer.get("layer") or source.get("layer"),
        answer.get("raw_value"),
    )


def normalized_check(answer: dict) -> bool:
    raw = Decimal(str(answer["raw_value"]))
    field = answer["field_path"][1:]
    expected = {
        "param1": (raw - 1) * 100,
        "param2": (raw - 1) * 100,
        "param3": (1 - raw) * 100,
        "param5": raw * 100,
        "param6": raw - Decimal("1.5"),
    }[field]
    return Decimal(str(answer["review_normalized"]["value"])) == expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expect-snapshot")
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    accepted = load(bundle / "data/accepted49.json")["items"]
    pending = load(bundle / "data/pending4.json")["items"]
    dispositions61 = load(bundle / "data/effect_disposition61.json")["items"]
    assert len(accepted) == 49 and len(pending) == 4 and len(dispositions61) == 61
    assert len({identity(item["answer"]) for item in accepted}) == 49
    base_by_effect = {item["effect_id"]: item for item in dispositions61}
    assert len(base_by_effect) == 61

    metrics = load(ROOT / "output/character_skills/effect_ledger/metrics.json")
    snapshot = metrics["snapshot"]
    current_snapshot = snapshot["snapshot_id"]
    current_campaign = snapshot["campaign_signature"]
    current_rules_path = ROOT / "output/character_skills/profiles/rules.json"
    current_rules = load(current_rules_path)
    current_rules_sha = sha(current_rules_path)
    frozen_rules = load(bundle / "evidence/experiment/input/output/character_skills/profiles/rules.json")

    current_skills_path = ROOT / "output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw"
    current_chars_path = ROOT / "output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw"
    frozen_skills_path = bundle / "evidence/experiment/input/output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw"
    frozen_chars_path = bundle / "evidence/experiment/input/output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw"
    current_skills_doc = load(current_skills_path)
    current_chars_doc = load(current_chars_path)
    frozen_skills_doc = load(frozen_skills_path)
    frozen_chars_doc = load(frozen_chars_path)
    current_skills = {record["skillid"]: record for record in current_skills_doc["skilllist"]}
    frozen_skills = {record["skillid"]: record for record in frozen_skills_doc["skilllist"]}
    current_chars = {record["cid"]: record for record in current_chars_doc["charainfo"]}
    frozen_chars = {record["cid"]: record for record in frozen_chars_doc["charainfo"]}

    wanted_effects = set(base_by_effect)
    current_effects = {}
    ledger_path = ROOT / "output/character_skills/effect_ledger/ledger.jsonl"
    with ledger_path.open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("record_type") == "effect" and record.get("effect_id") in wanted_effects:
                current_effects[record["effect_id"]] = record

    page_cache = {}
    frozen_page_cache = {}
    for item in dispositions61:
        cid = item["cid"]
        if cid not in page_cache:
            page_cache[cid] = load(ROOT / f"output/character_skills/pages/{cid}/card.json")
            frozen_page = bundle / f"evidence/experiment/input/output/character_skills/pages/{cid}/card.json"
            frozen_page_cache[cid] = load(frozen_page) if frozen_page.is_file() else None

    results = []
    for item in accepted + pending:
        is_pending = item in pending
        answer = item["answer"]
        source = answer["source"]
        effect_id = answer["effect_id"]
        base = base_by_effect[effect_id]
        cid = item["cid"]
        current_row = row_map(page_cache[cid]).get(item["row_id"])
        frozen_card = frozen_page_cache[cid]
        frozen_row = row_map(frozen_card).get(item["row_id"]) if frozen_card else None
        effect = current_effects.get(effect_id)
        parent_id = base["source_skill"]["record_id"]
        parent = current_skills.get(parent_id)
        frozen_parent = frozen_skills.get(parent_id)
        carrier = current_skills.get(source["record_id"])
        frozen_carrier = frozen_skills.get(source["record_id"])
        char = current_chars.get(cid)
        frozen_char = frozen_chars.get(cid)
        current_rule = current_rules.get(answer["rule_key"])
        frozen_rule = frozen_rules.get(answer["rule_key"])

        direct_conflicts = []
        version_differences = []
        if current_row is None:
            direct_conflicts.append("CURRENT_ROW_MISSING")
        elif current_row.get("japanese") != item["japanese"]:
            direct_conflicts.append("CURRENT_JAPANESE_DIFFERS")
        if effect is None:
            direct_conflicts.append("CURRENT_LEDGER_EFFECT_MISSING")
        else:
            if effect.get("effect_type") != base["baseline_effect"]["effect_type"]:
                direct_conflicts.append("CURRENT_EFFECT_TYPE_DIFFERS")
            if effect.get("snapshot_id") != current_snapshot:
                direct_conflicts.append("EFFECT_SNAPSHOT_NOT_CURRENT")
        if current_rule is None:
            direct_conflicts.append("CURRENT_RULE_MISSING")
        elif current_rule.get("field_path") != answer["field_path"]:
            direct_conflicts.append("CURRENT_RULE_FIELD_DIFFERS")
        if parent is None:
            direct_conflicts.append("CURRENT_PARENT_MISSING")
        if carrier is None:
            direct_conflicts.append("CURRENT_CARRIER_MISSING")
        else:
            if carrier.get("ability") != 1095:
                direct_conflicts.append("CURRENT_CARRIER_NOT_1095")
            if carrier.get(answer["field_path"][1:]) != answer["raw_value"]:
                direct_conflicts.append("CURRENT_RAW_VALUE_DIFFERS")
        if parent is not None and carrier is not None:
            try:
                if source["record_id"] not in parent.get("sub", []):
                    direct_conflicts.append("CURRENT_PARENT_SUB_LINK_MISSING")
                if item["japanese"] not in parent.get("text", ""):
                    direct_conflicts.append("CURRENT_PARENT_TEXT_MISSING_SENTENCE")
                if sum(current_skills[sid].get("ability") == 1095 for sid in parent.get("sub", [])) != 1:
                    direct_conflicts.append("CURRENT_1095_CARRIER_NOT_UNIQUE")
            except (KeyError, TypeError):
                direct_conflicts.append("CURRENT_PARENT_SUB_RECORD_MISSING")
        if not is_pending:
            try:
                if char is None or char["skillid"][1] != parent_id:
                    direct_conflicts.append("CURRENT_CHARACTER_PARENT_LINK_MISSING")
            except (KeyError, IndexError, TypeError):
                direct_conflicts.append("CURRENT_CHARACTER_PARENT_LINK_INVALID")

        if current_row is not None and current_row != frozen_row:
            version_differences.append("TARGET_ROW_DIFFERS_FROM_FROZEN")
        if parent is not None and parent != frozen_parent:
            version_differences.append("PARENT_RECORD_DIFFERS_FROM_FROZEN")
        if carrier is not None and carrier != frozen_carrier:
            version_differences.append("CARRIER_RECORD_DIFFERS_FROM_FROZEN")
        if not is_pending and char is not None and char != frozen_char:
            version_differences.append("CHARACTER_RECORD_DIFFERS_FROM_FROZEN")
        if current_rule is not None and current_rule != frozen_rule:
            version_differences.append("RELEVANT_RULE_OBJECT_DIFFERS_FROM_FROZEN")

        exact_answer = {
            "rule_key": answer["rule_key"], "field_path": answer["field_path"],
            "table": source["table"], "record_id": source["record_id"],
            "layer": source["layer"], "raw_value": answer["raw_value"],
        }
        matching_answers = []
        if current_row is not None:
            matching_answers = [
                old for old in current_row.get("answers") or []
                if answer_identity(old) == tuple(exact_answer[key] for key in (
                    "rule_key", "field_path", "table", "record_id", "layer", "raw_value"))
            ]
        current_status = effect.get("status") if effect else "missing"
        if matching_answers and current_status == "unresolved":
            direct_conflicts.append("CANDIDATE_ANSWER_EXISTS_BUT_EFFECT_UNRESOLVED")

        if direct_conflicts:
            disposition = "SOURCE_OR_SEMANTIC_CONFLICT"
        elif current_status == "has_answer":
            disposition = "ALREADY_PRESENT_NO_NEW"
        elif is_pending:
            disposition = "PENDING_RAW_UPSTREAM"
        elif current_status != "unresolved":
            disposition = "SOURCE_OR_SEMANTIC_CONFLICT"
            direct_conflicts.append("CURRENT_EFFECT_NOT_UNRESOLVED_OR_ANSWERED")
        elif version_differences:
            disposition = "VERSION_PENDING_REVIEW"
        else:
            disposition = "ADOPTABLE_CURRENT_UNRESOLVED"

        results.append({
            "task_id": item["task_id"], "cid": cid, "yg": base["yg"],
            "row_id": item["row_id"], "effect_id": effect_id,
            "japanese": item["japanese"],
            "handoff_group": "PENDING4" if is_pending else "ACCEPTED49",
            "handoff_status": item["status"],
            "identity": identity(answer),
            "rule_key": answer["rule_key"], "field_path": answer["field_path"],
            "raw_value": answer["raw_value"], "normalized": answer["review_normalized"],
            "normalized_value_recheck": normalized_check(answer),
            "source": source, "parent_record_id": parent_id,
            "current_effect_status": current_status,
            "current_answer_refs": (effect or {}).get("answer_refs") or [],
            "current_row_answer_count": len((current_row or {}).get("answers") or []),
            "exact_candidate_answers_present": len(matching_answers),
            "current_page_sha256": sha(ROOT / f"output/character_skills/pages/{cid}/card.json"),
            "frozen_page_sha256": sha(bundle / f"evidence/experiment/input/output/character_skills/pages/{cid}/card.json") if frozen_card else None,
            "target_row_matches_frozen": current_row == frozen_row,
            "parent_matches_frozen": parent == frozen_parent,
            "carrier_matches_frozen": carrier == frozen_carrier,
            "character_matches_frozen": (char == frozen_char) if not is_pending else None,
            "relevant_rule_matches_frozen": current_rule == frozen_rule,
            "disposition": disposition,
            "direct_conflicts": direct_conflicts,
            "version_differences": version_differences,
            "remaining_gap": base["remaining_gap"],
        })

    for base in dispositions61:
        if base["handoff_status"] != "UNKNOWN":
            continue
        effect = current_effects.get(base["effect_id"])
        status = effect.get("status") if effect else "missing"
        if status == "has_answer":
            disposition = "ALREADY_PRESENT_NO_NEW"
        elif status == "unresolved":
            disposition = "UNKNOWN_RETAINED"
        else:
            disposition = "SOURCE_OR_SEMANTIC_CONFLICT"
        results.append({
            "task_id": base["task_id"], "cid": base["cid"], "yg": base["yg"],
            "row_id": base["row_id"], "effect_id": base["effect_id"],
            "japanese": base["japanese"], "handoff_group": "UNKNOWN8",
            "handoff_status": base["handoff_status"],
            "identity": None, "rule_key": None, "field_path": None,
            "raw_value": None, "normalized": None, "normalized_value_recheck": None,
            "source": None, "parent_record_id": base["source_skill"]["record_id"],
            "current_effect_status": status,
            "current_answer_refs": (effect or {}).get("answer_refs") or [],
            "disposition": disposition, "direct_conflicts": [] if effect else ["CURRENT_LEDGER_EFFECT_MISSING"],
            "version_differences": [], "remaining_gap": base["remaining_gap"],
        })

    assert len(results) == 61 and len({item["effect_id"] for item in results}) == 61
    accepted_results = [item for item in results if item["handoff_group"] == "ACCEPTED49"]
    pending_results = [item for item in results if item["handoff_group"] == "PENDING4"]
    unknown_results = [item for item in results if item["handoff_group"] == "UNKNOWN8"]
    counts = Counter(item["disposition"] for item in results)
    accepted_counts = Counter(item["disposition"] for item in accepted_results)
    pending_counts = Counter(item["disposition"] for item in pending_results)
    unknown_counts = Counter(item["disposition"] for item in unknown_results)
    yg_next = [item for item in accepted_results if item["disposition"] == "ADOPTABLE_CURRENT_UNRESOLVED" and item["yg"]]
    non_yg_next = [item for item in accepted_results if item["disposition"] == "ADOPTABLE_CURRENT_UNRESOLVED" and not item["yg"]]

    checks = {
        "handoff_49_4_61": len(accepted_results) == 49 and len(pending_results) == 4 and len(unknown_results) == 8,
        "all_61_effects_classified_exactly_once": len(results) == 61,
        "expected_snapshot": current_snapshot == args.expect_snapshot if args.expect_snapshot else True,
        "campaign_matches_snapshot": current_snapshot.startswith(current_campaign[:8] + "-"),
        "rules_hash_matches_ledger": current_rules_sha[:16] == snapshot["rules_json_sha256_16"],
        "all_normalized_values_rechecked": all(item["normalized_value_recheck"] for item in accepted_results + pending_results),
        "pending4_not_mixed_into_accepted": all(item["disposition"] != "ADOPTABLE_CURRENT_UNRESOLVED" for item in pending_results),
        "adoptable_are_currently_unresolved": all(item["current_effect_status"] == "unresolved" for item in accepted_results if item["disposition"] == "ADOPTABLE_CURRENT_UNRESOLVED"),
        "no_production_promotion": True,
    }
    summary = {
        "status": "RECONCILED_NO_PRODUCTION_CHANGES" if all(checks.values()) else "RECONCILIATION_CHECK_FAILED",
        "handoff_snapshot": "8d96f313-cf9451c6ff47fcfb",
        "current": {
            "campaign": current_campaign, "snapshot": current_snapshot,
            "rules_sha256": current_rules_sha, "rules_keys": len(current_rules),
            "metrics_sha256": sha(ROOT / "output/character_skills/effect_ledger/metrics.json"),
            "ledger_sha256": sha(ledger_path),
            "skilllist_sha256": sha(current_skills_path), "charainfo_sha256": sha(current_chars_path),
            "frozen_skilllist_sha256": sha(frozen_skills_path), "frozen_charainfo_sha256": sha(frozen_chars_path),
            "skilllist_file_matches_frozen": sha(current_skills_path) == sha(frozen_skills_path),
            "charainfo_file_matches_frozen": sha(current_chars_path) == sha(frozen_chars_path),
        },
        "checks": checks,
        "counts_all61": dict(sorted(counts.items())),
        "accepted49": {
            "counts": dict(sorted(accepted_counts.items())),
            "yg": dict(sorted(Counter(item["disposition"] for item in accepted_results if item["yg"]).items())),
            "non_yg": dict(sorted(Counter(item["disposition"] for item in accepted_results if not item["yg"]).items())),
            "cards": len({item["cid"] for item in accepted_results}),
        },
        "pending4": {"counts": dict(sorted(pending_counts.items())), "cids": sorted({item["cid"] for item in pending_results})},
        "unknown8": {"counts": dict(sorted(unknown_counts.items()))},
        "next_yg_mature_subset": {
            "answers": len(yg_next), "cards": len({item["cid"] for item in yg_next}),
            "effect_ids": [item["effect_id"] for item in yg_next],
        },
        "next_non_yg_same_domain": {
            "answers": len(non_yg_next), "cards": len({item["cid"] for item in non_yg_next}),
            "effect_ids": [item["effect_id"] for item in non_yg_next],
        },
        "production_changes": {"pages": 0, "ledger": 0, "rules": 0, "formal_generations": 0, "c16_started": False},
    }
    report = {
        "summary": summary,
        "bundle": str(bundle), "ledger": str(ledger_path),
        "items": results,
    }
    (output / "reconciliation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = [
        "task_id", "cid", "yg", "row_id", "effect_id", "handoff_group", "rule_key",
        "field_path", "raw_value", "parent_record_id", "current_effect_status",
        "disposition", "direct_conflicts", "version_differences", "remaining_gap",
    ]
    with (output / "reconciliation.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in results:
            row = dict(item)
            row["direct_conflicts"] = "|".join(item["direct_conflicts"])
            row["version_differences"] = "|".join(item["version_differences"])
            writer.writerow(row)
    print(json.dumps({
        "status": summary["status"], "checks": checks,
        "accepted49": summary["accepted49"], "pending4": summary["pending4"], "unknown8": summary["unknown8"],
        "next_yg": {key: value for key, value in summary["next_yg_mature_subset"].items() if key != "effect_ids"},
        "next_non_yg": {key: value for key, value in summary["next_non_yg_same_domain"].items() if key != "effect_ids"},
        "output": str(output),
    }, ensure_ascii=False))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
