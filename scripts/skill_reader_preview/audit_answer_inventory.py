"""Read-only inventory of current card answers and preview conversion risks."""
from __future__ import annotations

import collections
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "output" / "character_skills" / "pages"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from presentation import readable_value  # noqa: E402
from review_output import parse_review_id, review_directory, write_new_text  # noqa: E402


def walk_row_answers(card):
    """Match the production builder: only answers attached to displayed rows."""
    for group in card.get("groups", []):
        for skill in group.get("skills", []):
            for row in skill.get("rows", []):
                row_id = row.get("row_id")
                for answer_index, answer in enumerate(row.get("answers", [])):
                    if isinstance(answer, dict):
                        yield row_id, answer_index, answer


def finite_tree(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_tree(v) for v in value)
    return True


def main(review_id=None):
    out = review_directory(ROOT, review_id) / 'answer_inventory.json'
    combos = collections.defaultdict(lambda: {"count": 0, "examples": []})
    errors, nonfinite, suspicious = [], [], []
    totals = collections.Counter()
    for path in sorted(PAGES.iterdir(), key=lambda p: p.name):
        if not path.is_dir() or not path.name.isdigit():
            continue
        card_path = path / "card.json"
        if not card_path.is_file():
            continue
        totals["cards"] += 1
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append({"cid": path.name, "error": f"card JSON: {type(exc).__name__}: {exc}"})
            continue
        for row_id, answer_index, a in walk_row_answers(card):
            totals["answers"] += 1
            kind = str(a.get("quantity_kind") or "(missing)")
            rule = str(a.get("rule_key") or "(no rule_key)")
            group = combos[(kind, rule)]
            group["count"] += 1
            if len(group["examples"]) < 4:
                group["examples"].append({"cid": path.name, "row_id": row_id, "answer_index": answer_index,
                                          "value": a.get("value"), "raw_value": a.get("raw_value")})
            if rule == "(no rule_key)":
                totals["no_rule"] += 1
            try:
                shown, note = readable_value(a)
                totals["converted"] += 1
            except Exception as exc:
                errors.append({"cid": path.name, "row_id": row_id, "answer_index": answer_index, "rule_key": rule,
                               "quantity_kind": kind, "error": f"{type(exc).__name__}: {exc}"})
                continue
            if not finite_tree((shown, note)) or re.search(r"\bNaN\b|\bInfinity\b", str((shown, note)), re.I):
                nonfinite.append({"cid": path.name, "row_id": row_id, "answer_index": answer_index, "rule_key": rule,
                                  "quantity_kind": kind, "shown": shown, "note": note})
            tiers = re.findall(r"第\d+档[：:]\s*([\d.]+)倍", str(a.get("value") or ""))
            if "skilllist|1016|/param6" == rule and (not tiers or any(not x for x in tiers)):
                suspicious.append({"cid": path.name, "row_id": row_id, "answer_index": answer_index, "issue": "empty/unparsed tier list",
                                   "value": a.get("value"), "rendered": shown})
            # These labels have explicit CID30236-only legacy renderers. Their
            # numeric values came from that card's reviewed conclusions, not a
            # portable conversion rule.
            if path.name != "30236" and rule == "(no rule_key)" and kind in {
                "暴击回复比例", "普通时楔释放的停止时长输入", "Chain档位获珠概率阈值",
                "攻击间隔乘数", "保护次数", "原文攻击次数", "位置数量", "层数",
                "地形变化的正持续时间", "暴击回复HP上限档位",
            }:
                suspicious.append({"cid": path.name, "row_id": row_id, "answer_index": answer_index, "issue": "legacy hardcoded quantity kind outside CID30236 (needs value/source review)",
                                   "quantity_kind": kind, "value": a.get("value"), "raw_value": a.get("raw_value"),
                                   "shown": shown})
    result = {
        "schema_version": 1,
        "scope": "only groups[].skills[].rows[].answers[] in numeric card.json files, matching the production builder; candidates outside rows are excluded",
        "totals": dict(totals),
        "quantity_kind_rule_key": [
            {"quantity_kind": k, "rule_key": r, **v}
            for (k, r), v in sorted(combos.items(), key=lambda item: (-item[1]["count"], item[0]))
        ],
        "readable_value_audit": {"call_errors": errors, "nonfinite_outputs": nonfinite,
                                  "suspicious_hardcodes_or_tiers": suspicious},
    }
    write_new_text(out, json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({"cards": totals["cards"], "answers": totals["answers"],
                      "combinations": len(combos), "converted": totals["converted"],
                      "errors": len(errors), "nonfinite": len(nonfinite),
                      "suspicious": len(suspicious), "output": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main(parse_review_id(__doc__))
