"""G2 batch-continuous executor: recycle remaining approved G2 candidates in bulk.

Purpose
-------
Runs continuously over every ELIGIBLE_A row in the approved manifest that has not
already been journaled by `g2_micro_batch.py` (10 items), `g2_batch2.py` (100
items) or this run's own journal, splitting them into batches of <=100 items and
<=256 MiB, recycling each batch into the Windows Recycle Bin (temporary isolation;
never permanent delete), and journalling each item independently.

KEY DIFFERENCE vs `g2_batch2.py` / `g2_continuous.py`
----------------------------------------------------
Those two scripts recycle ONE file per IFileOperation: for each item they call
DeleteItem once and PerformOperations once. This script recycles a WHOLE BATCH with
a single IFileOperation: it queues one DeleteItem per item (N DeleteItem calls, the
global progress sink passed as NULL third argument, exactly as `_shell_recycle_paths`
already does) and then calls PerformOperations ONCE. The imported backend
`_shell_recycle_paths(list_of_paths)` already implements "queue all DeleteItem then
one PerformOperations" verbatim; this file just feeds it the whole batch instead of
a one-element list. PreDeleteItem is still invoked once per item, so the
permanent-delete protection (TSF_DELETE_RECYCLE_IF_POSSIBLE == 0x80) applies to
every item in the batch.

Safety contract (never relaxed in this file)
--------------------------------------------
  - Guard = approved-manifest path whitelist (path + sha256 + bytes all match) +
    live source SHA-256 recompute == manifest + archive survival copy (volume +
    member in index_resumed.jsonl with matching sha256/bytes). The synthetic
    fixture load_guard/fixtureguard are NOT used here.
  - IFileOperation recycle action, the IFileOperationProgressSink permanent-delete
    protection (PreDeleteItem rejects missing TSF_DELETE_RECYCLE_IF_POSSIBLE and
    returns E_ABORT), and the recycle-bin self-entry locating (parse_i_original_path
    + $R hash compare) are imported/derived from recycle_shell_backend semantics.
  - No os.remove / os.unlink / shutil.rmtree / Remove-Item / cmd del anywhere here.
  - FOF_NOCONFIRMATION and FOF_SILENT are never set (asserted in the imported
    backend and re-asserted here).
  - Recycle-bin self-entry locating only persists self-entry identity after a
    same-process before/after $I diff, matched by exact original path + $R hash.
    Unrelated entries are never recorded.

Stop discipline (per item; never relaxed by batching)
-----------------------------------------------------
On any of the following the item is recorded and the run stops (no further items,
no further batches, no whole-batch retry): permanent delete risk; source SHA/bytes
change vs manifest; missing archive copy; recycle-bin unavailable; failed to locate
self entry after recycle; recovered content hash mismatch (per-item $R hash, or the
post-batch sampled restore).

Sampling optimisation
---------------------
Each batch restores only a reproducible sample of 2 RECYCLED_VERIFIED items to a
fresh directory and re-checks the hash. All other items rely on the recycle-bin $R
hash match (recoverable_content_sha256) recorded at locate time as proof of
recoverability. Items whose self entry cannot be located are recorded as
UNKNOWN_LOCATION, never as RECYCLED_VERIFIED.

Batch-abort accounting
----------------------
IFileOperation processes queued items one at a time; with FOFX_EARLYFAILURE it stops
at the first failure. So if some mid-batch item triggers a PreDeleteItem abort
(permanent-delete risk), items queued BEFORE it may already be in the recycle bin
while that item and the rest are preserved. This file therefore does NOT assume the
whole batch shares one fate: after PerformOperations it classifies EACH item from
its own ground truth (source still present? self entry located? $R hash matches?).
Items already in the bin with a matching $R hash are RECYCLED_VERIFIED; the aborted
item and everything after it are STOP_SOURCE_PRESERVED.

--dry-run performs guard validation only (no recycle, no locate, no restore, no
journal/progress writes); it is used for the read-only smoke test.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import time
import uuid
from pathlib import Path

from recycle_fixture import (
    Blocked, now, error_code, extended, no_reparse, file_digest,
    PROJECT, SCHEMA,
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

MICRO_JOURNAL = FOLLOWUP / "g2_micro_batch_journal.jsonl"
BATCH2_JOURNAL = FOLLOWUP / "g2_batch2_journal.jsonl"

# This run's outputs.
JOURNAL = FOLLOWUP / "g2_batch_continuous_journal.jsonl"   # journal AND progress
BATCHES = FOLLOWUP / "g2_batch_continuous_batches.jsonl"   # per-batch reports
STOP = FOLLOWUP / "g2_batch_continuous_stop.json"          # written only on a stop
SMOKE = FOLLOWUP / "g2_batch_continuous_smoke.json"
VERIFY_BASE = PROJECT / "work/storage_recycle_g1_20261027/g2_batch_continuous_verify"

APPROVAL_STAGE = "G2_APPROVED_FOR_MICRO_BATCH"
# The approval record pins the manifest gz by SHA-256. Verify it, don't trust the path.
EXPECTED_MANIFEST_SHA = "2040fd35f19469f5350f7ac724700608034ccf64489e1011fbc08409e6d6cc2c"

MAX_ITEMS_PER_BATCH = 100
MAX_BYTES_PER_BATCH = 256 * 1024 * 1024  # 268435456
LONG_PATH_HARD_LIMIT = 260
SAMPLE_PER_BATCH = 2

S_OK_HRESULT = "0x00000000"


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
    pinned = data.get("manifest", {}).get("sha256")
    if pinned != EXPECTED_MANIFEST_SHA:
        raise Blocked("APPROVAL_MANIFEST_SHA_UNEXPECTED")
    # The approved manifest is the gz file; verify its content hash matches the pin.
    actual, _ = _sha256_bytes(MANIFEST_GZ)
    if actual != EXPECTED_MANIFEST_SHA:
        raise Blocked("APPROVED_MANIFEST_GZ_SHA_MISMATCH")
    return data


def load_manifest_eligible():
    """Return (eligible, order).

    eligible: path -> {"bytes": int, "sha256": str} for every ELIGIBLE_A row.
    order:    list of paths in manifest order (deterministic batch composition).
    """
    eligible = {}
    order = []
    with gzip.open(MANIFEST_GZ, "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("classification") != "ELIGIBLE_A":
                continue
            p = row["path"]
            if p in eligible:
                raise Blocked("DUPLICATE_PATH_IN_MANIFEST")
            eligible[p] = {"bytes": int(row["bytes"]), "sha256": row["sha256"]}
            order.append(p)
    return eligible, order


def load_index():
    """path -> archive record (volume/member/sha256/bytes) from index_resumed.jsonl."""
    idx = {}
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            idx[r["path"]] = r
    return idx


def _journal_paths(journal_path):
    """Set of paths recorded in a JSONL journal file (empty if missing)."""
    out = set()
    if not journal_path.exists():
        return out
    with open(extended(journal_path), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.add(json.loads(line)["path"])
    return out


def load_excluded_paths():
    """Paths already handled: micro batch + second batch + this run's own journal."""
    excluded = set()
    excluded |= _journal_paths(MICRO_JOURNAL)
    excluded |= _journal_paths(BATCH2_JOURNAL)
    excluded |= _journal_paths(JOURNAL)
    return excluded


def _abs_path_characters(path):
    return len(str((PROJECT / path).absolute()))


def compute_remaining(eligible, order, excluded):
    """Remaining candidates in manifest order: not yet journaled, not over 260 chars.

    Returns (remaining, long_path_excluded). remaining is a list of item dicts.
    """
    remaining = []
    long_path_excluded = []
    for p in order:
        if p in excluded:
            continue
        if _abs_path_characters(p) > LONG_PATH_HARD_LIMIT:
            long_path_excluded.append(p)
            continue
        remaining.append({"path": p, "bytes": eligible[p]["bytes"],
                          "sha256": eligible[p]["sha256"]})
    return remaining, long_path_excluded


def split_batches(items):
    """Deterministic batch split: <=100 items and <=256 MiB each (hard cap)."""
    batches = []
    cur = []
    cur_bytes = 0
    for item in items:
        b = item["bytes"]
        if b > MAX_BYTES_PER_BATCH:
            raise Blocked("SINGLE_ITEM_EXCEEDS_BATCH_BYTE_CAP")
        if cur and (len(cur) >= MAX_ITEMS_PER_BATCH
                    or cur_bytes + b > MAX_BYTES_PER_BATCH):
            batches.append(cur)
            cur = []
            cur_bytes = 0
        cur.append(item)
        cur_bytes += b
    if cur:
        batches.append(cur)
    return batches


def verify_item_guards(item, eligible, idx):
    """Return (abs_path, archive_record). Raise Blocked (=> skip item + STOP) otherwise.

    Guard chain, in order:
      1. path whitelist: exact path present in the approved ELIGIBLE_A manifest with
         matching bytes + sha256;
      2. live source SHA-256 + bytes recompute == manifest;
      3. archive survival: index has volume + member mapping with matching
         sha256/bytes.
    """
    p = item["path"]
    e = eligible.get(p)
    if e is None:
        raise Blocked("NOT_IN_ELIGIBLE_MANIFEST")
    if e["bytes"] != item["bytes"] or e["sha256"] != item["sha256"]:
        raise Blocked("MANIFEST_MISMATCH")
    # 2. source recompute.
    abs_path = PROJECT / p
    no_reparse(abs_path)
    try:
        os.lstat(extended(abs_path))
    except FileNotFoundError:
        raise Blocked("SOURCE_MISSING")
    if not os.path.isfile(extended(abs_path)):
        raise Blocked("SOURCE_NOT_REGULAR_FILE")
    src_sha, src_size = _sha256_bytes(abs_path)
    if src_size != item["bytes"]:
        raise Blocked("SOURCE_BYTES_MISMATCH")
    if src_sha != item["sha256"]:
        raise Blocked("SOURCE_SHA_MISMATCH")
    # 3. archive survival copy.
    rec = idx.get(p)
    if rec is None:
        raise Blocked("NO_ARCHIVE_RECORD")
    if not rec.get("volume") or not rec.get("member"):
        raise Blocked("NO_ARCHIVE_VOLUME_MEMBER")
    if rec["bytes"] != item["bytes"] or rec["sha256"] != item["sha256"]:
        raise Blocked("ARCHIVE_RECORD_MISMATCH")
    return abs_path, rec


def _locate_batch_entries(new_i_names, passed_items):
    """Parse new $I entries once, map normalized original path -> $I names, match.

    For each passed item, find candidate $I entries whose parsed original path
    (case-folded, normalized) equals the item's absolute source path, then verify
    the $R file hash. Prefers the first candidate whose $R hash matches; otherwise
    returns the first non-matching candidate (hash_match=False). Returns a list of
    entry dicts aligned with passed_items, or None per slot. Never records unrelated
    entries. Reuses parse_i_original_path + _norm_win_path + $R hash semantics.
    """
    path_to_i = {}
    for i_name in new_i_names:
        try:
            info = parse_i_original_path(recycle_bin_dir() / i_name)
        except Blocked:
            continue
        key = _norm_win_path(info["original_path"]).casefold()
        path_to_i.setdefault(key, []).append(i_name)

    entries = []
    for (_, item, abs_path, _rec) in passed_items:
        target = _norm_win_path(str(abs_path.absolute())).casefold()
        candidates = path_to_i.get(target, [])
        entry = None
        for i_name in candidates:
            r_name = "$R" + i_name[2:]
            r_path = recycle_bin_dir() / r_name
            if not os.path.isfile(extended(r_path)):
                candidate = {"entry_i_name": i_name, "entry_r_name": r_name,
                             "original_path": item["path"],
                             "expected_sha256": item["sha256"],
                             "expected_bytes": item["bytes"],
                             "actual_sha256": None, "actual_bytes": None,
                             "hash_match": False, "error": "R_FILE_MISSING"}
            else:
                digest, size = _sha256_bytes(r_path)
                candidate = {"entry_i_name": i_name, "entry_r_name": r_name,
                             "original_path": item["path"],
                             "expected_sha256": item["sha256"],
                             "expected_bytes": item["bytes"],
                             "actual_sha256": digest, "actual_bytes": size,
                             "hash_match": (digest == item["sha256"]
                                            and size == item["bytes"])}
            if candidate["hash_match"]:
                entry = candidate
                break
            if entry is None:
                entry = candidate
        entries.append(entry)
    return entries


def restore_verify_sample(entry, item, batch_id, item_index):
    """Copy the $R content to a fresh directory and verify sha256/bytes (sampled).

    This is a verification copy (read $R -> write fresh dir); it does NOT move the
    item out of the recycle bin. Re-reads the $R file fresh so a post-locate change
    is detected. Returns a dict with the result and recoverable content hash.
    """
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
    target_dir = VERIFY_BASE / batch_id / ("item_%04d" % item_index)
    no_reparse(VERIFY_BASE)
    target_dir.mkdir(parents=True, exist_ok=False)
    no_reparse(target_dir)
    base = Path(item["path"]).name
    target = target_dir / base
    no_reparse(target)
    with open(extended(target), "xb") as dst:
        dst.write(data)
    return {"result": "RESTORED", "recoverable_content_sha256": digest,
            "recoverable_content_bytes": len(data), "restored_to": str(target)}


def _pick_sample_indices(n):
    """Reproducible selection of up to SAMPLE_PER_BATCH indices from a list sorted
    by path: index 0 and the middle index (n-1)//2. Deterministic regardless of
    batch_id. Returns sorted ascending indices."""
    if n <= 0:
        return []
    picks = {0}
    if n >= 2:
        picks.add((n - 1) // 2)
    return sorted(picks)


def _journal_line(item, rec, op, entry, rv, result, abort_state, source_present_after,
                  shell_result, timestamp):
    recov_sha = rv.get("recoverable_content_sha256")
    recov_bytes = rv.get("recoverable_content_bytes")
    identity = None
    if entry is not None:
        identity = {"i_name": entry["entry_i_name"], "r_name": entry["entry_r_name"],
                    "original_path": entry.get("original_path"),
                    "hash_match": entry.get("hash_match")}
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


def process_batch(batch, eligible, idx):
    """Pre-check all items; submit the whole batch via ONE PerformOperations; then
    locate/classify/journal each item independently.

    Returns a batch result dict. Never raises for per-item stop conditions: those
    are recorded and returned via stop_reason. Raises Blocked only for setup-level
    failures (recycle-bin enumeration).
    """
    batch_id = uuid.uuid4().hex
    journal_records = []
    stop_reason = None
    passed = []  # (item_index, item, abs_path, rec)

    # ---- Phase 1: pre-check every item (no recycle yet). ----
    for i, item in enumerate(batch):
        try:
            abs_path, rec = verify_item_guards(item, eligible, idx)
            passed.append((i, item, abs_path, rec))
        except Blocked as exc:
            journal_records.append(_journal_line(
                item, None, None, None,
                {"result": "SKIPPED", "recoverable_content_sha256": None,
                 "recoverable_content_bytes": None},
                "STOP_SOURCE_PRESERVED", str(exc),
                None, None, now()))
            stop_reason = str(exc)
            break

    if stop_reason:
        # A pre-check item failed: do NOT submit anything in this batch.
        return {
            "batch_id": batch_id,
            "items_total": len(batch),
            "items_processed": len(journal_records),
            "items_not_processed": len(batch) - len(journal_records),
            "journal_records": journal_records,
            "verified_entries": [],
            "stop_reason": stop_reason,
            "submitted": False,
            "operation": None,
        }

    # ---- Phase 2: submit the WHOLE batch (multiple DeleteItem + ONE Perform). ----
    before_i = snapshot_i_names()
    op = None
    try:
        op = _shell_recycle_paths([extended(a) for (_, _, a, _) in passed])
    except Blocked as exc:
        # Failed before/during queue (SHCreateItem/DeleteItem/STA). PerformOperations
        # did not run; treat every item as preserved.
        for (i, item, abs_path, rec) in passed:
            journal_records.append(_journal_line(
                item, rec, None, None,
                {"result": "SKIPPED", "recoverable_content_sha256": None,
                 "recoverable_content_bytes": None},
                "STOP_SOURCE_PRESERVED", str(exc),
                os.path.lexists(extended(abs_path)), None, now()))
        stop_reason = str(exc)
        return {
            "batch_id": batch_id,
            "items_total": len(batch),
            "items_processed": len(journal_records),
            "items_not_processed": 0,
            "journal_records": journal_records,
            "verified_entries": [],
            "stop_reason": stop_reason,
            "submitted": True,
            "operation": op,
        }

    after_i = snapshot_i_names()
    new_i = sorted(after_i - before_i)
    shell_result = op.get("perform_hr")

    # ---- Phase 3: locate each item's self entry and classify independently. ----
    entries = _locate_batch_entries(new_i, passed)
    verified_entries = []

    for k, (i, item, abs_path, rec) in enumerate(passed):
        source_present_after = os.path.lexists(extended(abs_path))
        entry = entries[k]

        if op.get("permanent_delete_risk"):
            # Whole operation aborted due to a permanent-delete risk on some item.
            # Items queued before the abort may already be in the bin; classify each
            # item from its own ground truth.
            if source_present_after:
                result = "STOP_SOURCE_PRESERVED"
                abort_state = "PERMANENT_DELETE_RISK"
            elif entry is not None and entry.get("hash_match"):
                result = "RECYCLED_VERIFIED"
                abort_state = "NONE"
                verified_entries.append((i, item, entry))
            elif entry is None:
                result = "UNKNOWN_LOCATION"
                abort_state = "SELF_ENTRY_NOT_LOCATED"
            else:
                result = "UNCERTAIN"
                abort_state = "RECOVERED_HASH_MISMATCH"
            stop_reason = "PERMANENT_DELETE_RISK"
        elif source_present_after:
            result = "STOP_SOURCE_PRESERVED"
            abort_state = "SOURCE_STILL_PRESENT_AFTER_RECYCLE"
            stop_reason = "SOURCE_STILL_PRESENT_AFTER_RECYCLE"
        elif entry is None:
            result = "UNKNOWN_LOCATION"
            abort_state = "SELF_ENTRY_NOT_LOCATED"
            stop_reason = "SELF_ENTRY_NOT_LOCATED"
        elif shell_result != S_OK_HRESULT or not entry.get("hash_match"):
            result = "UNCERTAIN"
            if shell_result != S_OK_HRESULT:
                abort_state = "PERFORM_HR_NOT_S_OK"
            else:
                abort_state = "RECOVERED_HASH_MISMATCH"
            stop_reason = abort_state
        else:
            result = "RECYCLED_VERIFIED"
            abort_state = "NONE"
            verified_entries.append((i, item, entry))

        recoverable = {
            "recoverable_content_sha256": entry.get("actual_sha256") if entry else None,
            "recoverable_content_bytes": entry.get("actual_bytes") if entry else None,
        }
        journal_records.append(_journal_line(
            item, rec, op, entry, recoverable, result, abort_state,
            source_present_after, shell_result, now()))

    return {
        "batch_id": batch_id,
        "items_total": len(batch),
        "items_processed": len(journal_records),
        "items_not_processed": 0,
        "journal_records": journal_records,
        "verified_entries": verified_entries,
        "stop_reason": stop_reason,
        "submitted": True,
        "operation": op,
    }


def _summarize(records):
    counts = {}
    for r in records:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    return counts


def _append_jsonl(path, obj):
    no_reparse(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(extended(path), "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False, allow_nan=False) + "\n")


def _append_journal_lines(lines):
    """Append one batch's journal lines to the journal in a single open (progress)."""
    no_reparse(JOURNAL.parent)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with open(extended(JOURNAL), "a", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(json.dumps(line, ensure_ascii=False, allow_nan=False) + "\n")


def _write_json_overwrite(path, data):
    no_reparse(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(extended(tmp), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, allow_nan=False, indent=2)
        f.write("\n")
    os.replace(str(tmp), str(path))


def _write_json_new(path, data):
    no_reparse(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(extended(path), "x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, allow_nan=False, indent=2)
        f.write("\n")


def run_execute(args):
    """Continuous real recycle loop. Not run in this delivery (dry-run only)."""
    _forbidden_flag_assert_local()
    load_approval()
    eligible, order = load_manifest_eligible()
    idx = load_index()
    excluded = load_excluded_paths()
    remaining, long_path_excluded = compute_remaining(eligible, order, excluded)
    batches = split_batches(remaining)
    if not batches:
        print(json.dumps({"overall": "NOTHING_REMAINING",
                          "remaining": 0,
                          "real_recycle_attempted": False}, ensure_ascii=False))
        return 0

    # Recycle-bin availability check (stop trigger before any action).
    before_q = query_recycle_bin()
    if before_q.get("hresult") != S_OK_HRESULT:
        raise Blocked("RECYCLE_BIN_UNAVAILABLE")
    snapshot_i_names()  # confirm enumerable; raises Blocked if not

    stop_reason = None
    t0 = time.monotonic()
    run_started = now()
    processed_paths = []
    cumulative = {
        "processed_count": 0,
        "recycled_verified_count": 0,
        "bytes_recycled": 0,
        "batches_completed": 0,
    }
    next_batch_number = 1

    for batch in batches:
        if args.max_batches is not None and (next_batch_number - 1) >= args.max_batches:
            break

        batch_result = process_batch(batch, eligible, idx)
        records = batch_result["journal_records"]
        counts = _summarize(records)

        # Per-item journal (append) == progress checkpoint for resume.
        _append_journal_lines(records)
        for r in records:
            processed_paths.append(r["path"])
        cumulative["processed_count"] += batch_result["items_processed"]
        cumulative["recycled_verified_count"] += counts.get("RECYCLED_VERIFIED", 0)
        cumulative["bytes_recycled"] += sum(
            r["bytes"] for r in records if r["result"] == "RECYCLED_VERIFIED")
        cumulative["batches_completed"] += 1

        # ---- post-batch sampled restore (optimisation) ----
        verified = batch_result["verified_entries"]
        sampled = []
        sample_fail = None
        verified_sorted = sorted(verified, key=lambda t: t[1]["path"])
        for j in _pick_sample_indices(len(verified_sorted)):
            item_index, item, entry = verified_sorted[j]
            rv = restore_verify_sample(entry, item, batch_result["batch_id"], item_index)
            sampled.append({"path": item["path"], "result": rv["result"],
                            "restored_to": rv.get("restored_to"),
                            "recoverable_content_sha256": rv.get("recoverable_content_sha256"),
                            "recoverable_content_bytes": rv.get("recoverable_content_bytes")})
            if rv["result"] != "RESTORED":
                sample_fail = "SAMPLED_RESTORE_" + rv["result"]
        if sample_fail and batch_result["stop_reason"] is None:
            batch_result["stop_reason"] = sample_fail

        batch_report = {
            "schema": "cc-storage-recycle-g2-batch-continuous-batch-v1",
            "batch_number": next_batch_number,
            "batch_id": batch_result["batch_id"],
            "timestamp": now(),
            "items_total": batch_result["items_total"],
            "items_processed": batch_result["items_processed"],
            "items_not_processed": batch_result["items_not_processed"],
            "counts": counts,
            "batch_bytes": sum(r["bytes"] for r in records),
            "sampled_restore": sampled,
            "submitted_once": batch_result["submitted"],
            "stop_reason": batch_result["stop_reason"],
        }
        _append_jsonl(BATCHES, batch_report)

        # Console per-batch line (UTF-8, flush).
        print(
            json.dumps({
                "batch": next_batch_number,
                "items": batch_result["items_processed"],
                "recycled_verified": counts.get("RECYCLED_VERIFIED", 0),
                "batch_ok": batch_result["stop_reason"] is None,
                "cum_items": cumulative["processed_count"],
                "cum_bytes": cumulative["bytes_recycled"],
                "elapsed_s": round(time.monotonic() - t0, 1),
            }, ensure_ascii=False), flush=True)

        if batch_result["stop_reason"]:
            stop_reason = batch_result["stop_reason"]
            break
        next_batch_number += 1

    # Stop-reason file (write only when a stop occurred).
    if stop_reason:
        _write_json_new(STOP, {
            "schema": "cc-storage-recycle-g2-batch-continuous-stop-v1",
            "created_utc": now(),
            "stop_reason": stop_reason,
            "last_batch_number": next_batch_number,
            "cumulative": cumulative,
            "note": "NO_FURTHER_ITEMS_PROCESSED_AFTER_STOP; no whole-batch retry",
        })

    after_q = query_recycle_bin()
    final = {
        "schema": "cc-storage-recycle-g2-batch-continuous-v1",
        "overall": "STOPPED_" + stop_reason if stop_reason else "ALL_REMAINING_PROCESSED",
        "created_utc": now(),
        "stop_reason": stop_reason,
        "remaining_initial": len(remaining),
        "cumulative": cumulative,
        "batches_total_planned": len(batches),
        "recycle_bin_before": before_q,
        "recycle_bin_after": after_q,
        "long_path_excluded_count": len(long_path_excluded),
        "tool_sha256": file_digest(Path(__file__).absolute()),
    }
    print(json.dumps({"overall": final["overall"],
                      "stop_reason": stop_reason,
                      "cumulative": cumulative,
                      "journal": str(JOURNAL)}, ensure_ascii=False))
    _write_json_overwrite(JOURNAL.with_name("g2_batch_continuous_final.json"), final)
    return 0


def _cheap_integrity_scan(remaining, idx):
    """Cheap full-set scan: source existence (lstat) + archive record presence.

    No SHA recompute here (that is scoped to the pre-checked batches). Returns
    (missing_source, missing_copy) lists of paths.
    """
    missing_source = []
    missing_copy = []
    for item in remaining:
        abs_path = PROJECT / item["path"]
        try:
            os.lstat(extended(abs_path))
        except OSError:
            missing_source.append(item["path"])
            continue
        rec = idx.get(item["path"])
        if (rec is None or not rec.get("volume") or not rec.get("member")
                or rec.get("bytes") != item["bytes"] or rec.get("sha256") != item["sha256"]):
            missing_copy.append(item["path"])
    return missing_source, missing_copy


def run_dry_run(args):
    """Read-only smoke: guards only (whitelist + source recompute + archive copy),
    no recycle/locate/restore/journal/progress writes."""
    _forbidden_flag_assert_local()
    load_approval()
    eligible, order = load_manifest_eligible()
    idx = load_index()
    excluded = load_excluded_paths()
    remaining, long_path_excluded = compute_remaining(eligible, order, excluded)
    batches = split_batches(remaining)

    # Full-set cheap integrity scan (source existence + archive record) for the
    # remaining candidates — answers "是否有缺源/缺副本" over the whole set.
    missing_source, missing_copy = _cheap_integrity_scan(remaining, idx)

    limit = args.max_batches if args.max_batches is not None else len(batches)
    precheck = []
    fail_reasons = {}
    has_missing_copy_or_source_scoped = False
    for b, batch in enumerate(batches[:limit]):
        passed = 0
        failed = 0
        for item in batch:
            try:
                verify_item_guards(item, eligible, idx)
                passed += 1
            except Blocked as exc:
                failed += 1
                has_missing_copy_or_source_scoped = True
                key = str(exc)
                fail_reasons[key] = fail_reasons.get(key, 0) + 1
        precheck.append({"batch": b + 1, "items": len(batch),
                         "passed": passed, "failed": failed})
        print(json.dumps({"dry_run_batch": b + 1, "items": len(batch),
                          "passed": passed, "failed": failed}, ensure_ascii=False),
              flush=True)

    smoke = {
        "schema": "cc-storage-recycle-g2-batch-continuous-smoke-v1",
        "created_utc": now(),
        "mode": "DRY_RUN_NO_RECYCLE",
        "real_recycle_attempted": False,
        "real_restore_attempted": False,
        "manifest_sha_verified": EXPECTED_MANIFEST_SHA,
        "batch_submission_mode": "MULTI_DELETEITEM_SINGLE_PERFORMOPERATIONS",
        "eligible_total": len(order),
        "excluded_already_journaled": len(excluded & set(order)),
        "remaining_total": len(remaining),
        "long_path_over_260_count": len(long_path_excluded),
        "has_long_path": len(long_path_excluded) > 0,
        "batch_count_planned": len(batches),
        "batches_prechecked": limit,
        "precheck_batches": precheck,
        "first_two_batches_precheck_pass": sum(
            p["passed"] for p in precheck[:2]),
        "first_two_batches_precheck_fail": sum(
            p["failed"] for p in precheck[:2]),
        "full_scan_missing_source_count": len(missing_source),
        "full_scan_missing_copy_count": len(missing_copy),
        "has_missing_source_or_copy": bool(missing_source or missing_copy),
        "scoped_precheck_missing_source_or_copy": has_missing_copy_or_source_scoped,
        "fail_reasons": fail_reasons,
        "batch_parameters": {
            "max_items": MAX_ITEMS_PER_BATCH,
            "max_bytes": MAX_BYTES_PER_BATCH,
            "sample_per_batch": SAMPLE_PER_BATCH,
            "long_path_hard_limit": LONG_PATH_HARD_LIMIT,
        },
        "tool_sha256": file_digest(Path(__file__).absolute()),
    }
    _write_json_overwrite(SMOKE, smoke)
    print(json.dumps({"smoke": str(SMOKE),
                      "remaining_total": len(remaining),
                      "batch_count_planned": len(batches),
                      "long_path_over_260_count": len(long_path_excluded),
                      "full_scan_missing_source_count": len(missing_source),
                      "full_scan_missing_copy_count": len(missing_copy),
                      "first_two_batches_precheck_pass": smoke["first_two_batches_precheck_pass"],
                      "real_recycle_attempted": False}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="guard validation only (no recycle/locate/restore/journal)")
    parser.add_argument("--max-batches", type=int, default=None,
                        help="limit to the first N batches (smoke/staged run); default: all")
    args = parser.parse_args()
    try:
        if args.dry_run:
            return run_dry_run(args)
        return run_execute(args)
    except (Blocked, OSError, ValueError) as exc:
        diagnostic = {"overall": "BLOCKED", "error": error_code(exc),
                      "reason": str(exc) if isinstance(exc, Blocked) else "FAIL_CLOSED_SEE_ERROR_CODE",
                      "real_recycle_attempted": not args.dry_run}
        print(json.dumps(diagnostic, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
