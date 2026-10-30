"""G2 bulk continuous recycle executor: batch IFileOperation + parallel precheck.

Recycles the remaining approved candidates in batches of <=100 files / <=256 MiB
using ONE IFileOperation round-trip per batch (the backend `_shell_recycle_paths`
already queues multiple DeleteItem and performs once). Precheck (source SHA/bytes
recompute + manifest whitelist + archive survival copy) is parallelized with a
ThreadPoolExecutor. Per-item journal, per-item self-entry locating, and per-batch
restore sampling keep the exact same safety semantics as the proven micro/second
batch executors; only the loop shape changes.

Safety contract (identical to g2_batch2.py, never relaxed):
  - guard = approved-manifest path whitelist + live source SHA-256 recompute +
    archive survival copy (volume+member in index_resumed.jsonl matching sha/bytes).
  - IFileOperation recycle + ProgressSink permanent-delete protection imported
    verbatim from recycle_shell_backend.
  - No os.remove/os.unlink/shutil.rmtree/Remove-Item/cmd del anywhere.
  - FOF_NOCONFIRMATION/FOF_SILENT never set.
  - Per-item journal with recycle_identity_own_item_only; only "source gone +
    self entry located + recoverable hash matches" is RECYCLED_VERIFIED.

Stop discipline: on any permanent-delete risk, source change, missing archive copy,
recycle-bin unavailable, failed self-entry locate, or recovered-hash mismatch, the
item is recorded and the whole run stops (no further items, no whole-batch retry).
"""
from __future__ import annotations

import argparse
import csv
import gzip
import gc
import hashlib
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from recycle_fixture import (
    Blocked, now, error_code, hresult, extended, no_reparse, file_digest,
    write_json_new, PROJECT, SCHEMA,
)
from recycle_shell_backend import (
    _shell_recycle_paths,
    recycle_bin_dir, snapshot_i_names, parse_i_original_path,
    query_recycle_bin, _norm_win_path,
    OPERATION_FLAGS, FOF_NOCONFIRMATION, FOF_SILENT, TSF_DELETE_RECYCLE_IF_POSSIBLE,
)

FOLLOWUP = PROJECT / "output/storage_retention/recycle_g1_20261027/followup_after_review"
APPROVAL = FOLLOWUP / "approval_record.json"
MANIFEST_GZ = FOLLOWUP / "gap7_final_g2_candidate_manifest.csv.gz"
INDEX = PROJECT / "output/storage_retention/vault_g1_checkpoint_20261027/index_resumed.jsonl"
PRIOR_JOURNALS = [
    FOLLOWUP / "g2_micro_batch_journal.jsonl",
    FOLLOWUP / "g2_batch2_journal.jsonl",
]
JOURNAL = FOLLOWUP / "g2_bulk_journal.jsonl"
PROGRESS = FOLLOWUP / "g2_bulk_progress.json"
REPORT_JSON = FOLLOWUP / "g2_bulk_report.json"
REPORT_MD = FOLLOWUP / "g2_bulk_report.md"
VERIFY_BASE = PROJECT / "work/storage_recycle_g1_20261027/g2_bulk_verify"

APPROVAL_STAGE = "G2_APPROVED_FOR_MICRO_BATCH"
EXPECTED_MANIFEST_SHA = "2040fd35f19469f5350f7ac724700608034ccf64489e1011fbc08409e6d6cc2c"

BATCH_MAX_FILES = 100
BATCH_MAX_BYTES = 256 * 1024 * 1024
PATH_MAX = 260


def _forbidden_flag_assert_local():
    if OPERATION_FLAGS & FOF_NOCONFIRMATION or OPERATION_FLAGS & FOF_SILENT:
        raise Blocked("FORBIDDEN_FLAG_PRESENT")
    if TSF_DELETE_RECYCLE_IF_POSSIBLE != 0x80:
        raise Blocked("UNEXPECTED_TSF_CONSTANT")


def _sha256_bytes(path):
    digest = hashlib.sha256()
    size = 0
    with open(extended(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def load_approval():
    data = json.loads(APPROVAL.read_text(encoding="utf-8"))
    if data.get("stage") != APPROVAL_STAGE:
        raise Blocked("APPROVAL_STAGE_NOT_MICRO_BATCH")
    if data.get("manifest", {}).get("sha256") != EXPECTED_MANIFEST_SHA:
        raise Blocked("APPROVAL_MANIFEST_SHA_UNEXPECTED")
    actual, _ = _sha256_bytes(MANIFEST_GZ)
    if actual != EXPECTED_MANIFEST_SHA:
        raise Blocked("APPROVED_MANIFEST_GZ_SHA_MISMATCH")
    return data


def load_manifest_eligible():
    eligible = {}
    with gzip.open(MANIFEST_GZ, "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("classification") != "ELIGIBLE_A":
                continue
            eligible[row["path"]] = {"bytes": int(row["bytes"]), "sha256": row["sha256"]}
    return eligible


def load_index():
    idx = {}
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            idx[r["path"]] = r
    return idx


def load_prior_processed():
    done = set()
    for jp in PRIOR_JOURNALS:
        if not jp.exists():
            continue
        with open(jp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                done.add(json.loads(line)["path"])
    # Also this run's own journal (resume support).
    if JOURNAL.exists():
        with open(JOURNAL, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                done.add(json.loads(line)["path"])
    return done


def remaining_items(eligible, done):
    rem = []
    for path, meta in eligible.items():
        if path in done:
            continue
        rem.append({"path": path, "bytes": meta["bytes"], "sha256": meta["sha256"]})
    rem.sort(key=lambda it: it["path"])
    return rem


def chunk_items(items):
    """Yield batches of <=100 files and <=256 MiB; >260-char paths hard-excluded.

    Also prevents two files with identical sha256 (same content, multiple paths)
    from landing in the SAME batch: the Recycle Bin can return ERROR_FILE_EXISTS
    (0x80070050) for a same-content collision within one PerformOperations call.
    Splitting them across batches avoids that whole-batch failure mode.
    """
    cur, cur_bytes, cur_sha = [], 0, set()
    for it in items:
        if len(it["path"]) >= PATH_MAX:
            continue  # hard exclude; candidate count is 0 but keep the guard
        if (cur and (len(cur) >= BATCH_MAX_FILES or cur_bytes + it["bytes"] > BATCH_MAX_BYTES
                     or it["sha256"] in cur_sha)):
            yield cur
            cur, cur_bytes, cur_sha = [], 0, set()
        cur.append(it)
        cur_bytes += it["bytes"]
        cur_sha.add(it["sha256"])
    if cur:
        yield cur


def precheck_one(item, eligible, idx):
    """Return (item, abs_path, archive_record). Raise Blocked on any guard failure."""
    p = item["path"]
    e = eligible.get(p)
    if e is None:
        raise Blocked("NOT_IN_ELIGIBLE_MANIFEST")
    if e["bytes"] != item["bytes"] or e["sha256"] != item["sha256"]:
        raise Blocked("MANIFEST_MISMATCH")
    abs_path = PROJECT / p
    no_reparse(abs_path)
    try:
        st = os.lstat(extended(abs_path))
    except FileNotFoundError:
        raise Blocked("SOURCE_MISSING")
    if not os.path.isfile(extended(abs_path)):
        raise Blocked("SOURCE_NOT_REGULAR_FILE")
    src_sha, src_size = _sha256_bytes(abs_path)
    if src_size != item["bytes"]:
        raise Blocked("SOURCE_BYTES_MISMATCH")
    if src_sha != item["sha256"]:
        raise Blocked("SOURCE_SHA_MISMATCH")
    rec = idx.get(p)
    if rec is None:
        raise Blocked("NO_ARCHIVE_RECORD")
    if not rec.get("volume") or not rec.get("member"):
        raise Blocked("NO_ARCHIVE_VOLUME_MEMBER")
    if rec["bytes"] != item["bytes"] or rec["sha256"] != item["sha256"]:
        raise Blocked("ARCHIVE_RECORD_MISMATCH")
    return item, abs_path, rec


def precheck_batch(batch, eligible, idx, workers):
    """Parallel precheck; returns (ok_rows, failed). ok_rows = [(item, abs_path, rec), ...]."""
    ok, failed = [], []
    if workers <= 1 or len(batch) <= 1:
        for it in batch:
            try:
                ok.append(precheck_one(it, eligible, idx))
            except Blocked as exc:
                failed.append((it, str(exc)))
        return ok, failed
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(precheck_one, it, eligible, idx): it for it in batch}
        for fut in as_completed(futs):
            it = futs[fut]
            try:
                ok.append(fut.result())
            except Blocked as exc:
                failed.append((it, str(exc)))
    # restore deterministic order by path
    ok.sort(key=lambda r: r[0]["path"])
    failed.sort(key=lambda r: r[0]["path"])
    return ok, failed


def locate_self_entry(new_i_names, abs_path, item):
    target = _norm_win_path(str(abs_path.absolute())).casefold()
    for i_name in new_i_names:
        try:
            info = parse_i_original_path(recycle_bin_dir() / i_name)
        except Blocked:
            continue
        if _norm_win_path(info["original_path"]).casefold() != target:
            continue
        r_name = "$R" + i_name[2:]
        r_path = recycle_bin_dir() / r_name
        if not os.path.isfile(extended(r_path)):
            return {"entry_i_name": i_name, "entry_r_name": r_name,
                    "original_path": item["path"], "expected_sha256": item["sha256"],
                    "expected_bytes": item["bytes"], "actual_sha256": None,
                    "actual_bytes": None, "hash_match": False, "error": "R_FILE_MISSING"}
        digest, size = _sha256_bytes(r_path)
        return {"entry_i_name": i_name, "entry_r_name": r_name,
                "original_path": item["path"], "expected_sha256": item["sha256"],
                "expected_bytes": item["bytes"], "actual_sha256": digest,
                "actual_bytes": size, "hash_match": (digest == item["sha256"] and size == item["bytes"])}
    return None


def restore_sample(entry, item, batch_id, item_index):
    if entry is None or not entry.get("hash_match"):
        return {"result": "NO_ENTRY_OR_MISMATCH", "recoverable_content_sha256": None,
                "recoverable_content_bytes": None, "restored_to": None}
    r_path = recycle_bin_dir() / entry["entry_r_name"]
    with open(extended(r_path), "rb") as src:
        data = src.read()
    if len(data) != item["bytes"]:
        return {"result": "SIZE_MISMATCH", "recoverable_content_sha256": None,
                "recoverable_content_bytes": len(data), "restored_to": None}
    digest = hashlib.sha256(data).hexdigest()
    if digest != item["sha256"]:
        return {"result": "HASH_MISMATCH", "recoverable_content_sha256": digest,
                "recoverable_content_bytes": len(data), "restored_to": None}
    target_dir = VERIFY_BASE / batch_id / ("item_%03d" % item_index)
    no_reparse(VERIFY_BASE)
    target_dir.mkdir(parents=True, exist_ok=False)
    no_reparse(target_dir)
    target = target_dir / Path(item["path"]).name
    no_reparse(target)
    with open(extended(target), "xb") as dst:
        dst.write(data)
    return {"result": "RESTORED", "recoverable_content_sha256": digest,
            "recoverable_content_bytes": len(data), "restored_to": str(target)}


def _journal_line(item, rec, shell_result, abort_state, identity, recov_sha,
                  recov_bytes, source_present_after, result, timestamp):
    return {
        "path": item["path"],
        "sha256": item["sha256"],
        "bytes": item["bytes"],
        "approval_id": APPROVAL_STAGE,
        "archive_volume": rec.get("volume") if rec else None,
        "archive_member": rec.get("member") if rec else None,
        "shell_result": shell_result,
        "abort_state": abort_state,
        "recycle_identity_own_item_only": identity,
        "recoverable_content_sha256": recov_sha,
        "recoverable_content_bytes": recov_bytes,
        "source_present_after": source_present_after,
        "result": result,
        "timestamp": timestamp,
    }


def write_progress(batch_no, processed, recycled, stopped, remaining_count):
    # Progress is our own mutable pointer, not a frozen artifact; overwrite is fine.
    PROGRESS.write_text(json.dumps(
        {"batch_no": batch_no, "processed": processed, "recycled": recycled,
         "stopped": stopped, "remaining_count": remaining_count,
         "updated_utc": now()}, ensure_ascii=False, indent=2), encoding="utf-8")


def run_bulk(execute, workers=8, max_batches=None):
    _forbidden_flag_assert_local()
    load_approval()
    eligible = load_manifest_eligible()
    idx = load_index()
    done = load_prior_processed()
    items = remaining_items(eligible, done)

    before_q = query_recycle_bin()
    if before_q.get("hresult") != "0x00000000":
        raise Blocked("RECYCLE_BIN_UNAVAILABLE")

    processed = 0
    recycled = 0
    stopped = 0
    stop_reason = None
    # Dry-run must not touch the journal (would corrupt resume dedup). Use a
    # separate smoke file instead.
    journal_fh = open(JOURNAL, "a", encoding="utf-8") if execute else None
    smoke_rows = []
    try:
        for batch_no, batch in enumerate(chunk_items(items), start=1):
            if max_batches is not None and batch_no > max_batches:
                break
            ok_rows, failed = precheck_batch(batch, eligible, idx, workers)

            if failed:
                stop_reason = "PRECHECK_FAILED_" + failed[0][1]
                if execute:
                    for it, reason in failed:
                        line = _journal_line(it, None, None, "STOP_SOURCE_PRESERVED", None,
                                             None, None, os.path.lexists(extended(PROJECT / it["path"])),
                                             "SKIPPED", now())
                        journal_fh.write(json.dumps(line, ensure_ascii=False) + "\n")
                        stopped += 1
                    journal_fh.flush()
                else:
                    smoke_rows.append({"batch": batch_no, "failed": len(failed),
                                       "first_reason": failed[0][1]})
                break

            if not execute:
                smoke_rows.append({"batch": batch_no, "precheck_ok": len(ok_rows),
                                   "batch_bytes": sum(it["bytes"] for it, _, _ in ok_rows)})
                processed += len(ok_rows)
                continue

            if not ok_rows:
                continue

            batch_id = uuid.uuid4().hex
            before_i = snapshot_i_names()
            # ONE bulk recycle round-trip for the whole batch.
            op = _shell_recycle_paths([extended(abs_path) for (_, abs_path, _) in ok_rows])
            after_i = snapshot_i_names()
            new_i = sorted(after_i - before_i)
            shell_result = op.get("perform_hr")

            # Deterministic restore sampling: 2 items per batch (first and middle).
            sample_idx = {0, len(ok_rows) // 2}

            for j, (it, abs_path, rec) in enumerate(ok_rows):
                source_present_after = os.path.lexists(extended(abs_path))
                entry = None
                rv = {"result": "NO_ENTRY", "recoverable_content_sha256": None,
                      "recoverable_content_bytes": None, "restored_to": None}
                identity = None
                abort_state = "NONE"

                if op.get("permanent_delete_risk"):
                    abort_state = "PERMANENT_DELETE_RISK"
                    result = "SKIPPED" if source_present_after else "UNCERTAIN"
                elif shell_result != "0x00000000":
                    abort_state = "PERFORM_HR_NOT_S_OK"
                    result = "SKIPPED" if source_present_after else "UNCERTAIN"
                elif source_present_after:
                    abort_state = "SOURCE_STILL_PRESENT_AFTER_RECYCLE"
                    result = "SKIPPED"
                else:
                    entry = locate_self_entry(new_i, abs_path, it)
                    if entry is None:
                        abort_state = "SELF_ENTRY_NOT_LOCATED"
                        result = "UNKNOWN_LOCATION"
                    else:
                        identity = {"i_name": entry["entry_i_name"],
                                    "r_name": entry["entry_r_name"],
                                    "original_path": entry.get("original_path"),
                                    "hash_match": entry.get("hash_match")}
                        if entry.get("hash_match"):
                            if j in sample_idx:
                                rv = restore_sample(entry, it, batch_id, j)
                            else:
                                rv = {"result": "HASH_MATCH_ONLY",
                                      "recoverable_content_sha256": entry["actual_sha256"],
                                      "recoverable_content_bytes": entry["actual_bytes"],
                                      "restored_to": None}
                            if rv["result"] in ("RESTORED", "HASH_MATCH_ONLY"):
                                result = "RECYCLED_VERIFIED"
                            else:
                                result = "UNCERTAIN"
                                abort_state = "RESTORE_SAMPLE_FAILED"
                        else:
                            result = "UNCERTAIN"
                            abort_state = "RECOVERED_HASH_MISMATCH"

                line = _journal_line(it, rec, shell_result, abort_state, identity,
                                     rv.get("recoverable_content_sha256"),
                                     rv.get("recoverable_content_bytes"),
                                     source_present_after, result, now())
                journal_fh.write(json.dumps(line, ensure_ascii=False) + "\n")
                if result == "RECYCLED_VERIFIED":
                    recycled += 1
                elif result == "SKIPPED":
                    stopped += 1
                processed += 1

                # Stop on any non-verified outcome (uncertain/unknown/skipped).
                if result != "RECYCLED_VERIFIED":
                    stop_reason = abort_state or result
                    journal_fh.flush()
                    write_progress(batch_no, processed, recycled, stopped,
                                   len(items) - processed)
                    return _summarize(processed, recycled, stopped, stop_reason,
                                      before_q, query_recycle_bin())

            journal_fh.flush()
            write_progress(batch_no, processed, recycled, stopped,
                           len(items) - processed)
            print(json.dumps({"batch": batch_no, "batch_size": len(ok_rows),
                              "recycled": recycled, "processed": processed,
                              "remaining": len(items) - processed}, ensure_ascii=False),
                  flush=True)
            # Release COM sink / threadpool / file-buffer allocations before the
            # next batch so a multi-hour run does not accumulate memory.
            gc.collect()

        write_progress(processed, processed, recycled, stopped, len(items) - processed)
        return _summarize(processed, recycled, stopped, stop_reason, before_q,
                          query_recycle_bin(), smoke_rows)
    finally:
        if journal_fh is not None:
            journal_fh.close()


def _summarize(processed, recycled, stopped, stop_reason, before_q, after_q, smoke_rows=None):
    res = {"processed": processed, "recycled": recycled, "stopped": stopped,
           "stop_reason": stop_reason, "recycle_bin_before": before_q,
           "recycle_bin_after": after_q}
    if smoke_rows:
        res["smoke"] = smoke_rows
    return res


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true", help="perform real recycle (default: dry-run)")
    p.add_argument("--workers", type=int, default=8, help="parallel precheck threads")
    p.add_argument("--max-batches", type=int, default=None, help="limit batches (smoke test)")
    args = p.parse_args()
    try:
        res = run_bulk(execute=args.execute, workers=args.workers, max_batches=args.max_batches)
        print(json.dumps({**res, "real_recycle_attempted": args.execute}, ensure_ascii=False))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print(json.dumps({"overall": "BLOCKED", "error": error_code(exc),
                          "reason": str(exc) if isinstance(exc, Blocked) else "FAIL_CLOSED",
                          "real_recycle_attempted": args.execute}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
