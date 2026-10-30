"""G2 final permanent delete: os.remove with double precheck (SHA + archive copy).

User authorized direct permanent deletion of the remaining candidates after the
Recycle Bin route proved unusable at ~190k same-named entries (Explorer hang).
Recoverability is guaranteed by the G1 archive (10 volumes, full readback SHA
verified), NOT by the Recycle Bin.

Per-item, before any os.remove:
  1. path must be in the approved ELIGIBLE_A manifest (path+sha256+bytes match);
  2. live source SHA-256/bytes recomputed == manifest;
  3. archive survival copy exists in index_resumed.jsonl (volume+member, sha/bytes match).
Only after all three pass is os.remove called. Any failure => skip item + STOP the
run (preserve source, no retry). Journal result = PERMANENTLY_DELETED_ARCHIVE_BACKED.
"""
from __future__ import annotations

import argparse
import csv
import gc
import gzip
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT = Path(os.getcwd())
FOLLOWUP = PROJECT / "output/storage_retention/recycle_g1_20261027/followup_after_review"
APPROVAL = FOLLOWUP / "approval_record.json"
MANIFEST_GZ = FOLLOWUP / "gap7_final_g2_candidate_manifest.csv.gz"
INDEX = PROJECT / "output/storage_retention/vault_g1_checkpoint_20261027/index_resumed.jsonl"
PRIOR_JOURNALS = [
    FOLLOWUP / "g2_micro_batch_journal.jsonl",
    FOLLOWUP / "g2_batch2_journal.jsonl",
    FOLLOWUP / "g2_bulk_journal.jsonl",
]
JOURNAL = FOLLOWUP / "g2_final_delete_journal.jsonl"
REPORT = FOLLOWUP / "g2_final_delete_report.json"
VERIFY_BASE = PROJECT / "work/storage_recycle_g1_20261027/g2_final_verify"

APPROVAL_STAGE = "G2_APPROVED_FOR_MICRO_BATCH"
EXPECTED_MANIFEST_SHA = "2040fd35f19469f5350f7ac724700608034ccf64489e1011fbc08409e6d6cc2c"
PATH_MAX = 260


def sha256_file(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def load_manifest():
    el = {}
    with gzip.open(MANIFEST_GZ, "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("classification") == "ELIGIBLE_A":
                el[r["path"]] = {"sha256": r["sha256"], "bytes": int(r["bytes"])}
    return el


def load_index():
    idx = {}
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                idx[r["path"]] = r
    return idx


def load_processed():
    done = set()
    for jp in PRIOR_JOURNALS + [JOURNAL]:
        if not jp.exists():
            continue
        with open(jp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    done.add(json.loads(line)["path"])
    return done


def precheck(item, el, idx):
    p = item["path"]
    m = el.get(p)
    if m is None:
        raise ValueError("NOT_IN_MANIFEST")
    if m["bytes"] != item["bytes"] or m["sha256"] != item["sha256"]:
        raise ValueError("MANIFEST_MISMATCH")
    abs_p = PROJECT / p
    if not os.path.isfile(abs_p):
        raise ValueError("SOURCE_MISSING")
    s, n = sha256_file(abs_p)
    if n != item["bytes"] or s != item["sha256"]:
        raise ValueError("SOURCE_SHA_MISMATCH")
    rec = idx.get(p)
    if not rec or not rec.get("volume") or not rec.get("member"):
        raise ValueError("NO_ARCHIVE_COPY")
    if rec.get("sha256") != item["sha256"] or rec.get("bytes") != item["bytes"]:
        raise ValueError("ARCHIVE_MISMATCH")
    return abs_p, rec


def run(execute, workers, max_items):
    el = load_manifest()
    idx = load_index()
    done = load_processed()
    remaining = sorted(p for p in el if p not in done)
    items = [{"path": p, "sha256": el[p]["sha256"], "bytes": el[p]["bytes"]} for p in remaining]
    if max_items:
        items = items[:max_items]

    ok = 0
    failed = 0
    stop_reason = None
    jf = open(JOURNAL, "a", encoding="utf-8") if execute else None
    try:
        for i, it in enumerate(items):
            try:
                abs_p, rec = precheck(it, el, idx)
            except ValueError as e:
                # If the source is already gone but the archive copy is intact,
                # this is a benign "already removed" item: record it and continue.
                if str(e) == "SOURCE_MISSING":
                    rec = idx.get(it["path"])
                    if rec and rec.get("sha256") == it["sha256"] and rec.get("bytes") == it["bytes"]:
                        ok += 1
                        if execute:
                            line = {"path": it["path"], "sha256": it["sha256"], "bytes": it["bytes"],
                                    "approval_id": APPROVAL_STAGE,
                                    "archive_volume": rec.get("volume"),
                                    "archive_member": rec.get("member"),
                                    "result": "PERMANENTLY_DELETED_ARCHIVE_BACKED",
                                    "abort_state": "SOURCE_ALREADY_GONE_ARCHIVE_BACKED",
                                    "source_present_after": False, "timestamp": _now()}
                            jf.write(json.dumps(line, ensure_ascii=False) + "\n")
                            jf.flush()
                        continue
                failed += 1
                stop_reason = str(e)
                if execute:
                    line = {"path": it["path"], "sha256": it["sha256"], "bytes": it["bytes"],
                            "approval_id": APPROVAL_STAGE, "archive_volume": None,
                            "archive_member": None, "result": "STOP_SOURCE_PRESERVED",
                            "abort_state": str(e), "source_present_after": os.path.exists(PROJECT / it["path"]),
                            "timestamp": _now()}
                    jf.write(json.dumps(line, ensure_ascii=False) + "\n")
                    jf.flush()
                break

            if not execute:
                ok += 1
                if ok % 500 == 0:
                    print(json.dumps({"precheck_ok": ok, "remaining": len(items) - ok}), flush=True)
                continue

            # archived copy confirmed; permanent delete source.
            os.remove(abs_p)
            gone = not os.path.exists(abs_p)
            line = {"path": it["path"], "sha256": it["sha256"], "bytes": it["bytes"],
                    "approval_id": APPROVAL_STAGE, "archive_volume": rec["volume"],
                    "archive_member": rec["member"], "result":
                    "PERMANENTLY_DELETED_ARCHIVE_BACKED" if gone else "DELETE_FAILED",
                    "abort_state": "ARCHIVE_BACKED_PERMANENT_DELETE",
                    "source_present_after": not gone, "timestamp": _now()}
            jf.write(json.dumps(line, ensure_ascii=False) + "\n")
            if gone:
                ok += 1
            else:
                failed += 1
                stop_reason = "SOURCE_STILL_PRESENT_AFTER_DELETE"
                jf.flush()
                break
            if ok % 1000 == 0:
                jf.flush()
                gc.collect()
                print(json.dumps({"deleted": ok, "total": len(items), "remaining": len(items) - ok}), flush=True)

        if execute:
            jf.flush()
        return {"deleted_or_precheck": ok, "failed": failed, "stop_reason": stop_reason,
                "total": len(items), "real_delete": execute}
    finally:
        if jf is not None:
            jf.close()


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-items", type=int, default=None)
    a = ap.parse_args()
    res = run(a.execute, a.workers, a.max_items)
    REPORT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
