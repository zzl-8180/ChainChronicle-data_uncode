"""Verify collected game candidates and test only directly identifiable formats."""
import collections
import hashlib
import json
import math
import shutil
from pathlib import Path


def main():
    output = Path("output/phone")
    output.mkdir(parents=True, exist_ok=True)
    acquired = {}
    failures = []
    for report in sorted(Path("raw").glob("phone_20261014_*/acquisition.json")):
        data = json.loads(report.read_text(encoding="utf-8"))
        for row in data["items"]:
            if row["status"] != "COPIED":
                failures.append({"report": report.as_posix(), "remote": row["remote"], "error": row["stderr"]})
                continue
            path = Path(row["local"])
            raw = path.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            if sha != row["sha256_local"] or len(raw) != row["bytes"]:
                raise ValueError(f"Collected file changed: {path}")
            acquired[row["remote"]] = dict(row, report=report.as_posix())
    records = []
    work = Path("work/phone_candidates")
    work.mkdir(parents=True, exist_ok=True)
    for row in acquired.values():
        source = Path(row["local"])
        if source.suffix != ".data5":
            continue
        dest = work / source.name
        shutil.copyfile(source, dest)
        raw = dest.read_bytes()
        counter = collections.Counter(raw)
        entropy = -sum((n/len(raw))*math.log2(n/len(raw)) for n in counter.values())
        record = {"name": source.name, "source_file": source.as_posix(), "source_sha256": row["sha256_local"],
                  "work_file": dest.as_posix(), "size": len(raw), "head_hex": raw[:32].hex(),
                  "size_multiple_of_16": len(raw) % 16 == 0, "entropy_bits_per_byte": entropy,
                  "record_decode_status": "UNKNOWN", "algorithm": None, "records": None}
        try:
            parsed = json.loads(raw)
            record["format"] = "JSON"
            record["record_decode_status"] = "CONFIRMED"
            record["records"] = parsed
        except (ValueError, UnicodeError) as exc:
            record["json_parse_error"] = f"{type(exc).__name__}: {exc}"
            record["format"] = "UNKNOWN_BINARY"
        record["sqlite_header"] = raw.startswith(b"SQLite format 3\0")
        record["unity_header"] = raw.startswith((b"UnityFS\0", b"UnityRaw\0", b"UnityWeb\0"))
        record["known_compression_header"] = ("gzip" if raw.startswith(b"\x1f\x8b") else
                                               "zip" if raw.startswith(b"PK\x03\x04") else None)
        records.append(record)
    baseline = json.loads(Path("output/apk/baseline.json").read_text(encoding="utf-8"))
    apk = next(r for r in acquired.values() if Path(r["local"]).name == "base.apk")
    meta = next(r for r in acquired.values() if Path(r["local"]).name == "global-metadata.dat")
    expected_meta = next(r for r in baseline["extracted"] if r["apk_entry"].endswith("global-metadata.dat"))
    summary = {"verified_copied_files": len(acquired), "verified_copied_bytes": sum(r["bytes"] for r in acquired.values()),
               "data5_candidates": len(records), "data5_bytes": sum(r["size"] for r in records),
               "apk_exact_match": apk["sha256_local"] == baseline["sha256"],
               "external_metadata_exact_match": meta["sha256_local"] == expected_meta["sha256"],
               "previous_copy_failures": failures, "outstanding_failed_files": [f["remote"] for f in failures if f["remote"] not in acquired],
               "scope": "14 explicitly selected files; not full cache; copy times differ",
               "decoded_card_skill_chains": 0}
    (output / "collected_files.json").write_text(json.dumps(list(acquired.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "cache_formats.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "acquisition_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "previous_copy_failures"}, ensure_ascii=False, indent=2))
    print("Candidate formats:", [(r["name"], r["format"]) for r in records])


if __name__ == "__main__":
    main()
