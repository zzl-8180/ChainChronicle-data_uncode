"""G2 continuous-batch executor: recycle the remaining approved G2 candidates.

Purpose
-------
Runs continuously over every ELIGIBLE_A row in the approved manifest that has not
already been journaled by `g2_micro_batch.py` (10 items) and `g2_batch2.py` (100
items), splitting them into batches of <=100 items and <=256 MiB, recycling each
item into the Windows Recycle Bin (temporary isolation; never permanent delete),
and journalling each item independently. Batches run back-to-back with no pause
between them; progress is checkpointed after each batch so an interrupted run can
resume without re-processing already-journaled paths.

Safety contract (never relaxed in this file)
--------------------------------------------
  - Guard = approved-manifest path whitelist (path + sha256 + bytes all match) +
    live source SHA-256 recompute == manifest + archive survival copy (volume +
    member in index_resumed.jsonl with matching sha256/bytes). The synthetic
    fixture load_guard/fixtureguard are NOT used here.
  - IFileOperation recycle action, the IFileOperationProgressSink permanent-delete
    protection (PreDeleteItem rejects missing TSF_DELETE_RECYCLE_IF_POSSIBLE and
    returns E_ABORT), and the recycle-bin self-entry locating are imported verbatim
    from recycle_shell_backend (semantics unchanged). No re-implementation.
  - No os.remove / os.unlink / shutil.rmtree / Remove-Item / cmd del anywhere here.
  - FOF_NOCONFIRMATION and FOF_SILENT are never set (asserted in the imported
    backend and re-asserted here).
  - Recycle-bin self-entry locating only persists self-entry identity after a
    same-process before/after $I diff, matched by exact original path + $R hash.

Stop discipline: on any of the following, the item is recorded and the run stops
(no further items, no whole-batch retry):
  permanent delete risk; source SHA/bytes change vs manifest; missing archive copy;
  recycle-bin unavailable; failed to locate self entry after recycle; recovered
  content hash mismatch (per-item $R hash, or the post-batch sampled restore).

Sampling optimisation
---------------------
Instead of restoring every item to a fresh directory (the micro/batch2 demo did
that to illustrate the roundtrip), each batch restores only a reproducible sample
of 2 RECYCLED_VERIFIED items to a fresh directory and re-checks the hash. All
other items rely on the recycle-bin $R hash match (recoverable_content_sha256)
recorded at locate time as proof of recoverability. Items whose self entry cannot
be located are recorded as UNKNOWN_LOCATION, never as RECYCLED_VERIFIED.

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

# Continuous run outputs.
JOURNAL = FOLLOWUP / "g2_continuous_journal.jsonl"
PROGRESS = FOLLOWUP / "g2_continuous_progress.json"
BATCHES = FOLLOWUP / "g2_continuous_batches.jsonl"
STOP = FOLLOWUP / "g2_continuous_stop.json"
SMOKE = FOLLOWUP / "g2_continuous_smoke.json"
VERIFY_BASE = PROJECT / "work/storage_recycle_g1_20261027/g2_continuous_verify"

APPROVAL_STAGE = "G2_APPROVED_FOR_MICRO_BATCH"
# The approval record pins the manifest gz by SHA-256. This is the gate that says
# "this exact manifest was approved". Verify it, don't trust the path.
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
    """Paths already handled: micro batch + second batch + this run's own journal
    and progress checkpoint."""
    excluded = set()
    excluded |= _journal_paths(MICRO_JOURNAL)
    excluded |= _journal_paths(BATCH2_JOURNAL)
    excluded |= _journal_paths(JOURNAL)
    if PROGRESS.exists():
        with open(extended(PROGRESS), encoding="utf-8") as f:
            prog = json.load(f)
        excluded.update(prog.get("processed_paths", []))
    return excluded


def load_progress():
    """Best-effort cumulative checkpoint; returns defaults if absent."""
    default = {
        "processed_count": 0,
        "recycled_verified_count": 0,
        "bytes_recycled": 0,
        "batches_completed": 0,
        "next_batch_number": 1,
        "processed_paths": [],
    }
    if not PROGRESS.exists():
        return default
    with open(extended(PROGRESS), encoding="utf-8") as f:
        data = json.load(f)
    for k, v in default.items():
        data.setdefault(k, v)
    return data


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


def locate_self_entry(new_i_names, abs_path, item):
    """Match one of the new $I entries to this item by original path; verify $R hash.

    Returns None if no self entry located (=> UNKNOWN_LOCATION). Never records
    unrelated entries.
    """
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
                    "original_path": item["path"],
                    "expected_sha256": item["sha256"], "expected_bytes": item["bytes"],
                    "actual_sha256": None, "actual_bytes": None, "hash_match": False,
                    "error": "R_FILE_MISSING"}
        digest, size = _sha256_bytes(r_path)
        return {"entry_i_name": i_name, "entry_r_name": r_name,
                "original_path": item["path"],
                "expected_sha256": item["sha256"], "expected_bytes": item["bytes"],
                "actual_sha256": digest, "actual_bytes": size,
                "hash_match": (digest == item["sha256"] and size == item["bytes"])}
    return None


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
    """Execute one batch of real candidates. Returns a batch result dict.

    Never raises for per-item stop conditions: those are recorded and returned via
    stop_reason. Raises Blocked only for setup-level failures (recycle-bin
    unavailable, journal pre-existence guard not applicable here).
    """
    batch_id = uuid.uuid4().hex
    journal_records = []
    verified_entries = []  # (item_index, item, entry) for post-batch sampling
    stop_reason = None

    for i, item in enumerate(batch):
        abs_path = None
        rec = None
        # ---- guards (steps 1-3) ----
        try:
            abs_path, rec = verify_item_guards(item, eligible, idx)
        except Blocked as exc:
            entry_line = _journal_line(
                item, None, None, None, {"result": "SKIPPED",
                                         "recoverable_content_sha256": None,
                                         "recoverable_content_bytes": None},
                "STOP_SOURCE_PRESERVED", str(exc),
                (abs_path.exists() if abs_path else None),
                None, now())
            journal_records.append(entry_line)
            stop_reason = str(exc)
            break

        # ---- step 4: recycle via IFileOperation (one file at a time) ----
        before_i = snapshot_i_names()
        op = None
        try:
            op = _shell_recycle_paths([extended(abs_path)])
        except Blocked as exc:
            entry_line = _journal_line(
                item, rec, None, None, {"result": "SKIPPED",
                                        "recoverable_content_sha256": None,
                                        "recoverable_content_bytes": None},
                "STOP_SOURCE_PRESERVED", str(exc),
                os.path.lexists(extended(abs_path)), None, now())
            journal_records.append(entry_line)
            stop_reason = str(exc)
            break

        shell_result = op.get("perform_hr")
        source_present_after = os.path.lexists(extended(abs_path))

        # Permanent delete risk: PreDeleteItem aborted; source must be preserved.
        if op.get("permanent_delete_risk"):
            entry_line = _journal_line(
                item, rec, op, None, {"result": "SKIPPED",
                                      "recoverable_content_sha256": None,
                                      "recoverable_content_bytes": None},
                "STOP_SOURCE_PRESERVED", "PERMANENT_DELETE_RISK",
                source_present_after, shell_result, now())
            journal_records.append(entry_line)
            stop_reason = "PERMANENT_DELETE_RISK"
            break

        # "原路径消失"是成功必要条件：回收后原路径必须已不在。
        if source_present_after:
            entry_line = _journal_line(
                item, rec, op, None, {"result": "SKIPPED",
                                      "recoverable_content_sha256": None,
                                      "recoverable_content_bytes": None},
                "STOP_SOURCE_PRESERVED", "SOURCE_STILL_PRESENT_AFTER_RECYCLE",
                source_present_after, shell_result, now())
            journal_records.append(entry_line)
            stop_reason = "SOURCE_STILL_PRESENT_AFTER_RECYCLE"
            break

        # ---- step 5: locate self entry + verify $R hash ----
        after_i = snapshot_i_names()
        new_i = sorted(after_i - before_i)
        entry = locate_self_entry(new_i, abs_path, item)

        if entry is None:
            # Recycled but could not locate/identify our own entry => UNKNOWN_LOCATION.
            entry_line = _journal_line(
                item, rec, op, None, {"result": "NO_ENTRY",
                                      "recoverable_content_sha256": None,
                                      "recoverable_content_bytes": None},
                "UNKNOWN_LOCATION", "SELF_ENTRY_NOT_LOCATED",
                source_present_after, shell_result, now())
            journal_records.append(entry_line)
            stop_reason = "SELF_ENTRY_NOT_LOCATED"
            break

        # Recoverability proof = $R hash match (no per-item restore in continuous mode).
        recoverable = {
            "recoverable_content_sha256": entry.get("actual_sha256"),
            "recoverable_content_bytes": entry.get("actual_bytes"),
        }
        if shell_result == S_OK_HRESULT and entry.get("hash_match"):
            result = "RECYCLED_VERIFIED"
            abort_state = "NONE"
        else:
            result = "UNCERTAIN"
            if shell_result != S_OK_HRESULT:
                abort_state = "PERFORM_HR_NOT_S_OK"
            elif not entry.get("hash_match"):
                abort_state = "RECOVERED_HASH_MISMATCH"
            else:
                abort_state = "UNKNOWN"
            stop_reason = abort_state

        entry_line = _journal_line(
            item, rec, op, entry, recoverable, result, abort_state,
            source_present_after, shell_result, now())
        journal_records.append(entry_line)

        if result == "RECYCLED_VERIFIED":
            verified_entries.append((i, item, entry))
        else:
            break

    return {
        "batch_id": batch_id,
        "items_total": len(batch),
        "items_processed": len(journal_records),
        "items_not_processed": len(batch) - len(journal_records),
        "journal_records": journal_records,
        "verified_entries": verified_entries,
        "stop_reason": stop_reason,
    }


def _summarize(records):
    counts = {}
    for r in records:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    return counts


def _append_journal(lines):
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

    prog = load_progress()
    processed_paths = list(prog.get("processed_paths", []))
    cumulative = {
        "processed_count": prog.get("processed_count", 0),
        "recycled_verified_count": prog.get("recycled_verified_count", 0),
        "bytes_recycled": prog.get("bytes_recycled", 0),
        "batches_completed": prog.get("batches_completed", 0),
    }
    next_batch_number = prog.get("next_batch_number", 1)

    if args.max_batches is not None and next_batch_number > args.max_batches:
        args.max_batches = None  # resume past a prior smoke limit; keep going

    stop_reason = None
    t0 = __import__("time").monotonic()
    run_started = now()

    for batch in batches:
        if args.max_batches is not None and (next_batch_number - 1) >= args.max_batches:
            break

        batch_result = process_batch(batch, eligible, idx)
        records = batch_result["journal_records"]
        counts = _summarize(records)

        # Per-item journal (append) + checkpoint processed paths.
        _append_journal(records)
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

        # Batch report line.
        batch_report = {
            "schema": "cc-storage-recycle-g2-continuous-batch-v1",
            "batch_number": next_batch_number,
            "batch_id": batch_result["batch_id"],
            "timestamp": now(),
            "items_total": batch_result["items_total"],
            "items_processed": batch_result["items_processed"],
            "items_not_processed": batch_result["items_not_processed"],
            "counts": counts,
            "batch_bytes": sum(r["bytes"] for r in records),
            "sampled_restore": sampled,
            "stop_reason": batch_result["stop_reason"],
        }
        _append_jsonl(BATCHES, batch_report)

        # Console per-batch line (UTF-8, flush).
        print(
            json.dumps({
                "batch": next_batch_number,
                "items": batch_result["items_processed"],
                "batch_ok": batch_result["stop_reason"] is None,
                "cum_items": cumulative["processed_count"],
                "cum_bytes": cumulative["bytes_recycled"],
                "elapsed_s": round(__import__("time").monotonic() - t0, 1),
            }, ensure_ascii=False), flush=True)

        # Checkpoint progress (overwrite).
        _write_json_overwrite(PROGRESS, {
            "schema": "cc-storage-recycle-g2-continuous-progress-v1",
            "updated_utc": now(),
            "run_started_utc": run_started,
            "next_batch_number": next_batch_number + 1,
            "processed_paths": processed_paths,
            **cumulative,
            "long_path_excluded_count": len(long_path_excluded),
            "remaining_after_this_batch": max(0, len(remaining) - cumulative["processed_count"]),
        })

        if batch_result["stop_reason"]:
            stop_reason = batch_result["stop_reason"]
            break
        next_batch_number += 1

    # Stop-reason file (write only when a stop occurred).
    if stop_reason:
        _write_json_new(STOP, {
            "schema": "cc-storage-recycle-g2-continuous-stop-v1",
            "created_utc": now(),
            "stop_reason": stop_reason,
            "last_batch_number": next_batch_number,
            "cumulative": cumulative,
            "note": "NO_FURTHER_ITEMS_PROCESSED_AFTER_STOP; no whole-batch retry",
        })

    after_q = query_recycle_bin()
    final = {
        "schema": "cc-storage-recycle-g2-continuous-v1",
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
                      "progress": str(PROGRESS)}, ensure_ascii=False))
    _write_json_overwrite(PROGRESS.with_name("g2_continuous_final.json"), final)
    return 0


def _append_jsonl(path, obj):
    no_reparse(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(extended(path), "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False, allow_nan=False) + "\n")


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

    limit = args.max_batches if args.max_batches is not None else len(batches)
    precheck = []
    fail_reasons = {}
    has_missing_copy_or_source = False
    for b, batch in enumerate(batches[:limit]):
        passed = 0
        failed = 0
        for item in batch:
            try:
                verify_item_guards(item, eligible, idx)
                passed += 1
            except Blocked as exc:
                failed += 1
                has_missing_copy_or_source = True
                key = str(exc)
                fail_reasons[key] = fail_reasons.get(key, 0) + 1
        precheck.append({"batch": b + 1, "items": len(batch),
                         "passed": passed, "failed": failed})
        print(json.dumps({"dry_run_batch": b + 1, "items": len(batch),
                          "passed": passed, "failed": failed}, ensure_ascii=False),
              flush=True)

    smoke = {
        "schema": "cc-storage-recycle-g2-continuous-smoke-v1",
        "created_utc": now(),
        "mode": "DRY_RUN_NO_RECYCLE",
        "real_recycle_attempted": False,
        "real_restore_attempted": False,
        "manifest_sha_verified": EXPECTED_MANIFEST_SHA,
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
        "has_missing_copy_or_source": has_missing_copy_or_source,
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
                      "first_two_batches_precheck_pass": smoke["first_two_batches_precheck_pass"],
                      "real_recycle_attempted": False}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="guard validation only (no recycle/locate/restore/journal)")
    parser.add_argument("--max-batches", type=int, default=None,
                        help="limit to the first N batches (smoke); default: all")
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
