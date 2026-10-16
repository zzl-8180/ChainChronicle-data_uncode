"""Resolve MonoBehaviour script identities without inventing missing field layouts."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

import UnityPy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--output", type=Path, default=Path("output/unity"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    env = UnityPy.load(args.source)
    scripts, rows, selected, errors = {}, [], [], []
    counts = Counter()
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        row = {"asset_file": obj.assets_file.name, "path_id": obj.path_id,
               "byte_start": obj.byte_start, "byte_size": obj.byte_size}
        try:
            head = obj.parse_monobehaviour_head()
            ptr = head.m_Script
            script_reader = ptr.deref()
            key = (script_reader.assets_file.name, script_reader.path_id)
            if key not in scripts:
                scripts[key] = script_reader.parse_as_object().m_ClassName
            row.update(name=head.m_Name, script_class=scripts[key],
                       script_file=key[0], script_path_id=key[1])
            counts[scripts[key]] += 1
            if re.search(r"^(SkillParameter|bhSkill|daCharacter|CharaDetailSkill|ChroSkillParameterView|DataManager|BattleDataManager|AssetBundleManager|AssetBundleLoader|ResourcesDriver|ServerMasterEditor_DataPool|da.*Master)$", scripts[key]):
                raw = obj.get_raw_data()
                dest = args.output / "mono_candidates" / f"{Path(obj.assets_file.name).name}_{obj.path_id}_{scripts[key]}.bin"
                dest.parent.mkdir(exist_ok=True)
                dest.write_bytes(raw)
                row["raw_file"] = dest.as_posix()
                row["field_layout_status"] = "UNKNOWN"
                try:
                    obj.parse_as_dict(check_read=True)
                    row["full_read_status"] = "READABLE"
                except Exception as exc:
                    row["full_read_status"] = "FAILED"
                    row["full_read_error"] = f"{type(exc).__name__}: {exc}"
                selected.append(row.copy())
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            errors.append(row.copy())
        rows.append(row)
    for name, data in [("mono_headers", rows), ("mono_candidates", selected), ("mono_errors", errors)]:
        with (args.output / f"{name}.jsonl").open("w", encoding="utf-8") as out:
            for row in data:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
    result = {"headers": len(rows), "errors": len(errors), "candidates": len(selected), "classes": dict(counts)}
    (args.output / "mono_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "classes"}))
    print(json.dumps(selected[:25], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
