"""G2 micro-batch executor: real recycle of exactly the 10 approved candidates.

Purpose
-------
This is the FIRST real-candidate micro-batch recycle. It moves exactly the 10 files
listed in `gap7_micro_batch_draft.json` into the Windows Recycle Bin (temporary
isolation), never permanently deletes them, and journals each item independently.

Safety contract (never relaxed in this file)
--------------------------------------------
  - Guard = approved-manifest path whitelist + live source SHA-256 recompute +
    archive survival copy (volume+member in index_resumed.jsonl with matching
    sha256/bytes). The synthetic-fixture load_guard/fixtureguard are NOT used here.
  - IFileOperation recycle action, the IFileOperationProgressSink permanent-delete
    protection (PreDeleteItem rejects missing TSF_DELETE_RECYCLE_IF_POSSIBLE and
    returns E_ABORT), and the recycle-bin self-entry locating are imported verbatim
    from recycle_shell_backend (semantics unchanged).
  - No os.remove / os.unlink / shutil.rmtree / Remove-Item / cmd del anywhere here.
  - FOF_NOCONFIRMATION and FOF_SILENT are never set (asserted in the imported
    backend's _forbidden_flag_assert, and re-asserted here).
  - Recycle-bin self-entry locating only persists self-entry identity after a
    same-process before/after $I diff, matched by exact original path.

Stop discipline: on any of the following, the item is recorded and the batch stops
(no further items, no whole-batch retry):
  permanent delete risk; source SHA/bytes change vs manifest; missing archive copy;
  recycle-bin unavailable; failed to locate self entry after recycle; recovered
  content hash mismatch.
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
    Blocked, now, error_code, hresult, extended, no_reparse, file_digest,
    write_json_new, PROJECT, SCHEMA,
)
from recycle_shell_backend import (
    SinkState, _make_progress_sink, _shell_recycle_paths,
    recycle_bin_dir, snapshot_i_names, parse_i_original_path,
    query_recycle_bin, _norm_win_path,
    OPERATION_FLAGS, FOF_NOCONFIRMATION, FOF_SILENT, TSF_DELETE_RECYCLE_IF_POSSIBLE,
)

FOLLOWUP = PROJECT / "output/storage_retention/recycle_g1_20261027/followup_after_review"
APPROVAL = FOLLOWUP / "approval_record.json"
MICRO_BATCH = FOLLOWUP / "gap7_micro_batch_draft.json"
MANIFEST_GZ = FOLLOWUP / "gap7_final_g2_candidate_manifest.csv.gz"
INDEX = PROJECT / "output/storage_retention/vault_g1_checkpoint_20261027/index_resumed.jsonl"
JOURNAL = FOLLOWUP / "g2_micro_batch_journal.jsonl"
REPORT_JSON = FOLLOWUP / "g2_micro_batch_report.json"
REPORT_MD = FOLLOWUP / "g2_micro_batch_report.md"
VERIFY_BASE = PROJECT / "work/storage_recycle_g1_20261027/g2_verify"

APPROVAL_STAGE = "G2_APPROVED_FOR_MICRO_BATCH"
# The approval record pins the manifest gz by SHA-256. This is the gate that says
# "this exact manifest was approved". Verify it, don't trust the path.
EXPECTED_MANIFEST_SHA = "2040fd35f19469f5350f7ac724700608034ccf64489e1011fbc08409e6d6cc2c"


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


def load_micro_batch():
    data = json.loads(MICRO_BATCH.read_text(encoding="utf-8"))
    items = data.get("items", [])
    if len(items) != 10:
        raise Blocked("MICRO_BATCH_NOT_10_ITEMS")
    if data.get("status") != "DRAFT_NOT_AUTHORIZED":
        raise Blocked("MICRO_BATCH_STATUS_UNEXPECTED")
    return data, items


def load_manifest_eligible():
    """path -> {bytes, sha256} for every ELIGIBLE_A row in the approved manifest."""
    eligible = {}
    with gzip.open(MANIFEST_GZ, "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("classification") != "ELIGIBLE_A":
                continue
            eligible[row["path"]] = {"bytes": int(row["bytes"]), "sha256": row["sha256"]}
    return eligible


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
    # 1a. must be in draft items (guaranteed by iteration) AND in ELIGIBLE_A manifest.
    e = eligible.get(p)
    if e is None:
        raise Blocked("NOT_IN_ELIGIBLE_MANIFEST")
    if e["bytes"] != item["bytes"] or e["sha256"] != item["sha256"]:
        raise Blocked("MANIFEST_MISMATCH")
    # 2. source recompute.
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


def restore_verify(entry, item, batch_id, item_index):
    """Copy the $R content to a fresh directory and verify sha256/bytes.

    This is a verification copy (read $R -> write fresh dir); it does NOT move the
    item out of the recycle bin. Returns a dict with recoverable content hash.
    """
    if entry is None:
        return {"result": "NO_ENTRY", "recoverable_content_sha256": None,
                "recoverable_content_bytes": None, "restored_to": None}
    if not entry.get("hash_match"):
        return {"result": "HASH_MISMATCH", "recoverable_content_sha256": None,
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
    target_dir = VERIFY_BASE / batch_id / ("item_%02d" % item_index)
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


def run_batch(execute):
    """Run the micro batch. execute=False => guard check only (no recycle)."""
    _forbidden_flag_assert_local()
    approval = load_approval()
    draft, items = load_micro_batch()
    eligible = load_manifest_eligible()
    idx = load_index()

    # Recycle-bin availability check (stop trigger before any action).
    before_q = query_recycle_bin()
    if before_q.get("hresult") != "0x00000000":
        raise Blocked("RECYCLE_BIN_UNAVAILABLE")

    if execute and JOURNAL.exists() and JOURNAL.stat().st_size > 0:
        raise Blocked("JOURNAL_ALREADY_EXISTS_NO_DOUBLE_RECYCLE")

    batch_id = uuid.uuid4().hex
    journal_records = []
    stop_reason = None

    for i, item in enumerate(items):
        abs_path = None
        rec = None
        # ---- guards (steps 1-3) ----
        try:
            abs_path, rec = verify_item_guards(item, eligible, idx)
        except Blocked as exc:
            # skip this item, preserve source, STOP the batch.
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

        if not execute:
            journal_records.append(_journal_line(
                item, rec, None, None, {"result": "CHECK_ONLY",
                                        "recoverable_content_sha256": None,
                                        "recoverable_content_bytes": None},
                "CHECK_ONLY", "CHECK_ONLY_NO_RECYCLE",
                True, None, now()))
            continue

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

        # ---- step 5b: restore-verify (copy $R to fresh dir, hash check) ----
        rv = restore_verify(entry, item, batch_id, i)

        if (shell_result == "0x00000000" and entry.get("hash_match")
                and rv.get("result") == "RESTORED"):
            result = "RECYCLED_VERIFIED"
            abort_state = "NONE"
        else:
            # Entry located but recovered content hash mismatch or non-S_OK HRESULT.
            result = "UNCERTAIN"
            if shell_result != "0x00000000":
                abort_state = "PERFORM_HR_NOT_S_OK"
            elif not entry.get("hash_match"):
                abort_state = "RECOVERED_HASH_MISMATCH"
            else:
                abort_state = "RESTORE_HASH_MISMATCH"
            stop_reason = abort_state

        entry_line = _journal_line(
            item, rec, op, entry, rv, result, abort_state,
            source_present_after, shell_result, now())
        journal_records.append(entry_line)

        if result != "RECYCLED_VERIFIED":
            break

    after_q = query_recycle_bin()

    # Append journal lines.
    if execute:
        no_reparse(JOURNAL.parent)
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        with open(extended(JOURNAL), "a", encoding="utf-8", newline="\n") as f:
            for line in journal_records:
                f.write(json.dumps(line, ensure_ascii=False, allow_nan=False) + "\n")

    return {
        "batch_id": batch_id,
        "execute": execute,
        "stop_reason": stop_reason,
        "items_total": len(items),
        "items_processed": len(journal_records),
        "items_not_processed": len(items) - len(journal_records),
        "recycle_bin_before": before_q,
        "recycle_bin_after": after_q,
        "journal_records": journal_records,
        "approval_manifest_sha_verified": EXPECTED_MANIFEST_SHA,
        "operation_flags": "0x%08X" % OPERATION_FLAGS,
        "forbidden_not_set": {"FOF_NOCONFIRMATION": True, "FOF_SILENT": True},
    }


def _summarize(result):
    records = result["journal_records"]
    counts = {"RECYCLED_VERIFIED": 0, "STOP_SOURCE_PRESERVED": 0,
              "UNCERTAIN": 0, "UNKNOWN_LOCATION": 0, "CHECK_ONLY": 0}
    for r in records:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    return counts


def build_report(result):
    counts = _summarize(result)
    report = {
        "schema": "cc-storage-recycle-g2-micro-batch-v1",
        "created_utc": now(),
        "stage": APPROVAL_STAGE,
        "execute": result["execute"],
        "batch_id": result["batch_id"],
        "overall": "G2_MICRO_BATCH_EXECUTED" if result["execute"] else "G2_MICRO_BATCH_CHECK_ONLY",
        "stop_reason": result["stop_reason"],
        "counts": counts,
        "items_total": result["items_total"],
        "items_processed": result["items_processed"],
        "items_not_processed": result["items_not_processed"],
        "recycle_bin_before": result["recycle_bin_before"],
        "recycle_bin_after": result["recycle_bin_after"],
        "per_item_results": [{"path": r["path"], "result": r["result"],
                              "sha256": r["sha256"], "bytes": r["bytes"],
                              "abort_state": r["abort_state"]}
                             for r in result["journal_records"]],
        "declarations": {
            "no_final_release_or_empty": True,
            "no_global_settings_changed": True,
            "no_retention_state_json_changed": True,
            "no_git": True,
            "no_other_dialogues_contacted": True,
            "no_w_m_implemented": True,
            "no_list_expanded": True,
            "only_approved_10_files_touched": True,
            "no_generic_delete_functions_used": True,
            "recycle_bin_not_emptied": True,
        },
        "tool_sha256": file_digest(Path(__file__).absolute()),
    }
    return report


def _render_md(report):
    c = report["counts"]
    rb_b = report["recycle_bin_before"]
    rb_a = report["recycle_bin_after"]
    lines = ["# G2 首批微批回收（10 件真实候选 → 回收站）", "",
             "结论：" + report["overall"] + ("（仅自检，未回收）" if not report["execute"] else ""), "",
             f'- 执行：{"是（真实回收 10 件）" if report["execute"] else "否（check 自检）"}',
             f'- 处理/总数：{report["items_processed"]}/{report["items_total"]}；'
             f'未处理：{report["items_not_processed"]}',
             f'- 停机原因：{report["stop_reason"] or "无（全部按序完成）"}',
             "", "## 结果计数", "",
             f'- RECYCLED_VERIFIED={c["RECYCLED_VERIFIED"]}，'
             f'STOP_SOURCE_PRESERVED={c["STOP_SOURCE_PRESERVED"]}，'
             f'UNCERTAIN={c["UNCERTAIN"]}，UNKNOWN_LOCATION={c["UNKNOWN_LOCATION"]}，'
             f'CHECK_ONLY={c["CHECK_ONLY"]}',
             "", "## 回收站前后计量（SHQueryRecycleBinW E:\\）", "",
             f'- 入站前：HRESULT={rb_b["hresult"]}, bytes={rb_b["bytes"]}, items={rb_b["items"]}',
             f'- 入站后：HRESULT={rb_a["hresult"]}, bytes={rb_a["bytes"]}, items={rb_a["items"]}',
             "", "## 逐件结果", "",
             "| 结果 | 字节 | 停机/异常 | 路径 |", "|---|---|---|---|"]
    for r in report["per_item_results"]:
        lines.append(f'| {r["result"]} | {r["bytes"]} | {r["abort_state"]} | {r["path"]} |')
    lines += ["", "## 声明", ""]
    for k, v in report["declarations"].items():
        lines.append(f'- {k} = {v}')
    lines += ["", "本批次只处理批准的 10 件真实候选；未做最终释放/清空回收站；未改全局设置；",
              "未改 retention/state.json；未 Git；未联系其他对话；未实施 W/M；未扩大清单；",
              "未使用通用删除函数（unlink/os.remove/shutil.rmtree/Remove-Item/cmd del）。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="check",
                        choices=["check", "execute"])
    args = parser.parse_args()
    try:
        execute = (args.command == "execute")
        result = run_batch(execute)
        if execute:
            report = build_report(result)
            if REPORT_JSON.exists() or REPORT_MD.exists():
                raise Blocked("REPORT_EXISTS_NOT_OVERWRITING")
            write_json_new(REPORT_JSON, report)
            with open(extended(REPORT_MD), "x", encoding="utf-8", newline="\n") as f:
                f.write(_render_md(report))
            print(json.dumps({"overall": report["overall"], "counts": report["counts"],
                              "stop_reason": report["stop_reason"],
                              "journal": str(JOURNAL), "report": str(REPORT_JSON)},
                             ensure_ascii=False))
        else:
            report = build_report(result)
            print(json.dumps({"overall": report["overall"], "counts": report["counts"],
                              "recycle_bin_before": report["recycle_bin_before"],
                              "items_total": report["items_total"],
                              "per_item": report["per_item_results"]},
                             ensure_ascii=False))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        diagnostic = {"overall": "BLOCKED", "error": error_code(exc),
                      "reason": str(exc) if isinstance(exc, Blocked) else "FAIL_CLOSED_SEE_ERROR_CODE",
                      "real_recycle_attempted": (args.command == "execute")}
        print(json.dumps(diagnostic, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
