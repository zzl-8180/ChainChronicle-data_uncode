"""Regression checks on actual APK data, including byte preservation and bad input."""
import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
from project_layout_paths import read_path, write_path
from versioned_outputs import fresh_output

import UnityPy


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unity_index(path):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    for row in rows:
        if "text_path" in row:
            source = read_path(Path(row["text_path"]))
            row["text_path"] = source.relative_to(path.parent).as_posix()
            assert sha(source) == row["text_sha256"], source
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Fresh directory for independent verification")
    args = parser.parse_args()
    rerun = fresh_output("projects/unpack/reports/validation", "phase-a", args.output)
    out = rerun if args.output is not None else write_path(Path("output/validation"))
    baseline = json.loads(read_path(Path("output/apk/baseline.json")).read_text(encoding="utf-8"))
    assert sha(read_path(Path(baseline["apk"]))) == baseline["sha256"], "APK no longer matches initial input"
    for row in baseline["extracted"]:
        assert sha(read_path(Path(row["work_path"]))) == row["sha256"], row["work_path"]
    source = read_path(Path("work/apk/assets/bin/Data/data.unity3d"))
    env = UnityPy.load(str(source))
    texts = [json.loads(line) for line in read_path(Path("output/unity/textassets.jsonl")).read_text(encoding="utf-8").splitlines()]
    lookup = {(r["asset_file"], r["path_id"]): r for r in texts}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        raw = obj.get_raw_data()
        endian = obj.reader.endian
        name_len = struct.unpack_from(endian + "I", raw)[0]
        script_offset = (4 + name_len + 3) & ~3
        script_len = struct.unpack_from(endian + "I", raw, script_offset)[0]
        exact_bytes = raw[script_offset+4:script_offset+4+script_len]
        row = lookup[(obj.assets_file.name, obj.path_id)]
        assert exact_bytes == read_path(Path(row["text_path"])).read_bytes(), row["name"]
    paths = [read_path(Path(p)) for p in ["output/unity/objects.jsonl", "output/unity/textassets.jsonl",
                              "output/native/recovered_symbols.json", "output/native/loader_calls.json",
                              "output/native/debug_recovery.json", "output/structured/sample_candidate.json",
                              "output/structured/test_character_rows.json"]]
    before = {str(p): sha(p) for p in paths}
    scripts = Path(__file__).resolve().parent
    unity, native, structured = (rerun / name for name in ("unity", "native", "structured"))
    for argv in [
        [scripts / "unity_scan.py", source, "--output", unity],
        [scripts / "native_debug.py", read_path(Path("work/apk/lib/arm64-v8a/libChronicleNUtils.so")),
         "--output", native],
        [scripts / "structured_candidates.py", "--textassets", unity / "textassets.jsonl", "--output", structured],
    ]:
        proc = subprocess.run([sys.executable, "-B", *map(str, argv)], capture_output=True)
        assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    rerun_roots = [unity, unity, native, native, native, structured, structured]
    for original, directory in zip(paths, rerun_roots):
        candidate = directory / original.name
        if directory == unity:
            assert unity_index(original) == unity_index(candidate), original.name
        else:
            assert before[str(original)] == sha(candidate), original.name
    assert before == {str(p): sha(p) for p in paths}, "Original output changed"
    invalid = rerun / "truncated.unity3d"
    invalid.write_bytes(source.read_bytes()[:128])
    proc = subprocess.run([sys.executable, "-B", str(scripts / "unity_scan.py"), str(invalid),
                           "--output", str(rerun / "invalid_unity")], capture_output=True)
    assert proc.returncode != 0, "Truncated bundle was accepted"
    error = json.loads((rerun / "invalid_unity/load_error.json").read_text())
    sample = json.loads(read_path(Path("output/structured/sample_candidate.json")).read_text(encoding="utf-8"))
    assert sample["status"] == "INCOMPLETE_CHAIN"
    assert all(sample[k] is None for k in ["skill_id", "effect_record", "raw_skill_parameters"])
    rows = json.loads(read_path(Path("output/structured/test_character_rows.json")).read_text(encoding="utf-8"))
    assert len(rows) == 21 and all(len(r["raw_columns"]) == 21 for r in rows[1:])
    result = {"status": "PASS", "apk_unchanged": True, "work_files_verified": len(baseline["extracted"]),
              "textasset_raw_bytes_verified": len(texts), "deterministic_outputs": before,
              "truncated_bundle_rejected": error, "unknown_skill_values_remain_null": True,
              "csv_columns_preserved": True, "device_acquisition_tested": False,
              "skill_semantics_tested": False}
    out.mkdir(parents=True, exist_ok=True)
    (out / "checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "deterministic_outputs"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
