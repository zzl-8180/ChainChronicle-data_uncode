"""Extract APK-owned tabular/story records with provenance and unresolved semantics."""
import csv
import hashlib
import json
from pathlib import Path


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    out = Path("output/structured")
    out.mkdir(parents=True, exist_ok=True)
    assets = [json.loads(line) for line in Path("output/unity/textassets.jsonl").read_text(encoding="utf-8").splitlines()]
    identity = json.loads(Path("output/apk/baseline.json").read_text(encoding="utf-8"))["identity"]

    def provenance(row, locator):
        return {"apk_entry": "assets/bin/Data/data.unity3d", "asset_file": row["asset_file"],
                "path_id": row["path_id"], "textasset_name": row["name"],
                "textasset_sha256": row["text_sha256"], "locator": locator}

    casts, commands, table = [], [], []
    for row in assets:
        raw = Path(row["text_path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["text_sha256"]:
            raise ValueError("TextAsset no longer matches scan")
        try:
            encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
            text = raw.decode(encoding)
        except UnicodeError:
            continue
        if row["name"] == "character_parameter":
            for line_number, line in enumerate(text.splitlines(), 1):
                fields = next(csv.reader([line]))
                table.append({"source": provenance(row, f"line:{line_number}"), "encoding": encoding,
                              "raw_columns": fields,
                              "column_semantics": "UNKNOWN (no header); DUMMY first line retained",
                              "scope": "test/default-looking character rows; active card master not established"})
        cast_section = False
        section = None
        for line_number, line in enumerate(text.splitlines(), 1):
            if line.startswith("<"):
                section = line
                cast_section = line == "<CharacterData>"
                continue
            if not line.strip():
                continue
            if cast_section:
                casts.append({"source": provenance(row, f"line:{line_number}"),
                              "raw_columns": next(csv.reader([line])),
                              "id_namespace": "UNKNOWN (story speaker/portrait reference; card id mapping unverified)"})
            if "CID:" in line or "必殺技" in line:
                commands.append({"source": provenance(row, f"line:{line_number}"), "section": section,
                                 "raw_columns": next(csv.reader([line]))})
    enemy_row = next(r for r in assets if r["name"] == "EnemyTableDefault")
    enemy = json.loads(Path(enemy_row["text_path"]).read_bytes())
    helpers = [{"source": provenance(enemy_row, f"/battleInfo/helper/{i}/card"), "raw_record": r["card"],
                "scope": "APK default battle fixture; active master/runtime use unknown"}
               for i, r in enumerate(enemy["battleInfo"]["helper"])]
    write(out / "test_character_rows.json", table)
    write(out / "story_casts.json", casts)
    write(out / "tutorial_skill_context.json", commands)
    write(out / "default_battle_cards.json", helpers)
    kain = next(c for c in casts if c["raw_columns"][:2] == ["カイン", "40"])
    pointers = [c for c in commands if any("TargetCID:40" in f for f in c["raw_columns"])]
    sample = {"identity": identity, "status": "INCOMPLETE_CHAIN", "candidate_name_original": "カイン",
              "candidate_id_raw": "40", "card_identity_status": "INFERRED",
              "identity_basis": "Local story cast ID 40 and tutorial TargetCID:40 alongside カイン text; master record not obtained",
              "evidence": [kain, *pointers], "card_master_record": None, "skill_id": None,
              "effect_record": None, "raw_skill_parameters": None, "interpretation_status": "UNKNOWN",
              "missing": ["card master record", "card to skill reference", "skill effect record and raw parameters"],
              "parser": "structured_candidates.py/1"}
    write(out / "sample_candidate.json", sample)
    summary = {"test_character_lines": len(table), "test_character_data_rows": len(table)-1,
               "story_cast_records": len(casts), "tutorial_context_rows": len(commands),
               "default_battle_card_records": len(helpers), "complete_skill_chains": 0}
    write(out / "summary.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
