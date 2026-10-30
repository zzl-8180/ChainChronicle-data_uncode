# -*- coding: utf-8 -*-
"""C8—C10 cycle closeout: archive-backed run cleanup and bounded B cleanup."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/character_skills"))
import run_retention  # noqa: E402

PAGES = ROOT / "output/character_skills/pages"
STATE = PAGES / "_batch/retention/state.json"
OUT = ROOT / "output/storage_retention/cycle_closeout_c8_c10_20261031"
VAULT = OUT / "vault"
WORK = ROOT / "work/cycle_closeout_c8_c10_20261031"
RESTORE = WORK / "restore_sample"
PLAN = OUT / "plan.json"
BINDING = OUT / "plan_binding.json"
MANIFEST = OUT / "run_archive_manifest.csv.gz"
RESTORE_REQUEST = OUT / "restore_request.json"
JOURNAL = OUT / "delete_journal.jsonl"
DISPOSITION = OUT / "run_disposition.json"
ACCOUNTING = OUT / "capacity_release_accounting.json"
POSTCHECK = OUT / "postcheck.json"
METADATA = ("before.json", "receipt.json")
PAYLOAD = ("card.json", "index.html")
DERIVED_NAMES = ("ledger.jsonl", "backlog.json", "metrics.json")
G1 = ROOT / "output/storage_retention/vault_g1_checkpoint_20261027"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def record(path: Path) -> dict:
    return {"bytes": path.stat().st_size, "sha256": sha(path)}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def state_summary() -> dict:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    active = {k: v for k, v in state["reservations"].items() if v["status"] == "RETAINED"}
    return {
        "max_runs": state["max_runs"],
        "max_bytes": state["max_bytes"],
        "active_runs": len(active),
        "active_bytes": sum(v["reserved_bytes"] for v in active.values()),
        "active_keys": sorted(active),
    }


def g1_baseline() -> dict:
    files = [p for p in G1.rglob("*") if p.is_file()]
    result = {"files": len(files), "bytes": sum(p.stat().st_size for p in files)}
    for name in ("catalog.json", "index_resumed.jsonl"):
        result[name] = record(G1 / name)
    return result


def derived_specs() -> list[dict]:
    base = "output/character_skills/c10_p1_20261030"
    generator = f"{base}/scratch/s3_ledger_precheck.py"
    evidence = f"{base}/ledger_precheck.json"
    inputs = ["work/c10_p1_20261030/subset_ge60", "work/c10_p1_20261030/subset_40to59"]
    for required in [generator, evidence, *inputs]:
        if not (ROOT / required).exists():
            raise ValueError(f"B_REBUILD_INPUT_MISSING:{required}")
    groups = []
    for name in ("ledger_oldpages", "ledger_sim"):
        groups.append({
            "root": f"{base}/scratch/{name}",
            "generator": generator,
            "generator_record": record(ROOT / generator),
            "evidence": evidence,
            "evidence_record": record(ROOT / evidence),
            "rebuild_command": f"./.venv/Scripts/python.exe -X utf8 -B {generator}",
            "declared_inputs": inputs,
            "input_file_counts": {p: sum(1 for x in (ROOT / p).rglob("*") if x.is_file()) for p in inputs},
        })
    return groups


def make_plan() -> None:
    if OUT.exists():
        raise ValueError(f"OUTPUT_ALREADY_EXISTS:{OUT}")
    OUT.mkdir(parents=True)
    before = state_summary()
    if before["active_runs"] != 12:
        raise ValueError(f"UNEXPECTED_RETAINED_RUN_COUNT:{before['active_runs']}")
    live_cache: dict[str, dict] = {}
    items = []
    metadata = []
    archive_rows = []
    for key in before["active_keys"]:
        run = PAGES / key
        for path in sorted(run.rglob("*")):
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                raise ValueError(f"REPARSE_NOT_ALLOWED:{path}")
            if not path.is_file():
                continue
            parts = path.relative_to(run).parts
            if not parts or parts[0] != "transactions":
                metadata.append({"run": key, "path": rel(path), **record(path), "kind": "run_level"})
                continue
            if len(parts) != 4 or parts[2] != "backup":
                raise ValueError(f"UNEXPECTED_TRANSACTION_FILE:{path}")
            cid, name = parts[1], parts[3]
            rec = record(path)
            if name in METADATA and rec["bytes"] <= 65536:
                metadata.append({"run": key, "path": rel(path), **rec})
                continue
            if name not in PAYLOAD:
                raise ValueError(f"UNEXPECTED_TRANSACTION_PAYLOAD:{path}")
            live = PAGES / cid / name
            live_key = rel(live)
            if live_key not in live_cache:
                if not live.is_file():
                    raise ValueError(f"CURRENT_PAGE_MISSING:{live}")
                live_cache[live_key] = record(live)
            same_as_live = live_cache[live_key] == rec
            item = {"run": key, "path": rel(path), "cid": cid, "name": name, **rec,
                    "class": "A", "survivor_kind": "live" if same_as_live else "archive"}
            if same_as_live:
                item["survivor"] = live_key
            else:
                archive_rows.append({"path": item["path"], "bytes": str(item["bytes"]),
                                     "sha256": item["sha256"], "classification": "ELIGIBLE_A"})
            items.append(item)
    with gzip.open(MANIFEST, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("path", "bytes", "sha256", "classification"))
        writer.writeheader()
        writer.writerows(archive_rows)
    restore_candidates = sorted(archive_rows, key=lambda x: (int(x["bytes"]), x["path"]))[:8]
    RESTORE_REQUEST.write_text(json.dumps([x["path"] for x in restore_candidates], indent=1), encoding="utf-8")
    derived = []
    for group in derived_specs():
        for name in DERIVED_NAMES:
            path = ROOT / group["root"] / name
            derived.append({"path": rel(path), "class": "B", **record(path), **group})
    protected_paths = [
        "output/character_skills/pages/_batch/campaign_latest.json",
        "output/character_skills/profiles/rules.json",
        "output/character_skills/effect_ledger/metrics.json",
        "output/character_skills/effect_ledger/ledger.jsonl",
        "output/character_skills/effect_ledger/backlog.json",
        "output/character_skills/review/direction_c8_c10_20261030_independent/REPORT.md",
    ]
    c8_root = ROOT / "output/character_skills/c8_p1_20261030/scratch"
    c8_files = [p for name in ("ledger_oldpages", "ledger_sim") for p in (c8_root / name).glob("*")
                if p.is_file() and p.name in DERIVED_NAMES]
    plan = {
        "schema": "cycle-closeout-20261031-v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "disk_free_before": shutil.disk_usage(ROOT).free,
        "state_before": before,
        "runs": before["active_keys"],
        "items": items,
        "metadata": metadata,
        "derived": derived,
        "live_baseline": live_cache,
        "protected_files": {p: record(ROOT / p) for p in protected_paths},
        "g1_baseline": g1_baseline(),
        "c_class": [{
            "paths": [rel(p) for p in c8_files],
            "files": len(c8_files),
            "bytes": sum(p.stat().st_size for p in c8_files),
            "reason": "C8 formal pages advanced to C9/C10; exact current-input rebuild is not proven",
        }],
        "archive": {"manifest": rel(MANIFEST), "vault": rel(VAULT),
                    "restore_request": rel(RESTORE_REQUEST), "restore_root": rel(RESTORE)},
    }
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    binding = {"plan_sha256": sha(PLAN), "manifest_sha256": sha(MANIFEST),
               "run_items": len(items), "run_bytes": sum(x["bytes"] for x in items),
               "archive_required_files": len(archive_rows),
               "archive_required_bytes": sum(int(x["bytes"]) for x in archive_rows),
               "derived_files": len(derived), "derived_bytes": sum(x["bytes"] for x in derived)}
    BINDING.write_text(json.dumps(binding, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(binding, ensure_ascii=False, indent=1))


def load_plan() -> tuple[dict, dict]:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    if sha(PLAN) != binding["plan_sha256"] or sha(MANIFEST) != binding["manifest_sha256"]:
        raise ValueError("PLAN_OR_MANIFEST_HASH_MISMATCH")
    return plan, binding


def archive_index(plan: dict) -> dict[str, dict]:
    required = [x for x in plan["items"] if x["survivor_kind"] == "archive"]
    if not required:
        return {}
    build = json.loads((VAULT / "build_report.json").read_text(encoding="utf-8"))
    catalog = json.loads((VAULT / "catalog.json").read_text(encoding="utf-8"))
    if build.get("status") != "PASS":
        raise ValueError("ARCHIVE_BUILD_NOT_PASS")
    reports = sorted(VAULT.glob("verify_report-*.json"), key=lambda p: p.stat().st_mtime)
    if not reports:
        raise ValueError("ARCHIVE_VERIFY_MISSING")
    verify = json.loads(reports[-1].read_text(encoding="utf-8"))
    if verify.get("status") != "PASS" or verify.get("catalog_sha256") != sha(VAULT / "catalog.json"):
        raise ValueError("ARCHIVE_VERIFY_NOT_PASS")
    if verify.get("index_sha256") != sha(VAULT / "index.jsonl"):
        raise ValueError("ARCHIVE_INDEX_HASH_MISMATCH")
    if verify.get("input_manifest_sha256") != sha(MANIFEST):
        raise ValueError("ARCHIVE_INPUT_MANIFEST_MISMATCH")
    index = {}
    with (VAULT / "index.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                index[row["path"]] = row
    for item in required:
        row = index.get(item["path"])
        if not row or row.get("sha256") != item["sha256"] or row.get("bytes") != item["bytes"]:
            raise ValueError(f"ARCHIVE_COPY_MISSING:{item['path']}")
        if not row.get("volume") or not row.get("member"):
            raise ValueError(f"ARCHIVE_LOCATION_MISSING:{item['path']}")
    request = json.loads(RESTORE_REQUEST.read_text(encoding="utf-8"))
    for path in request:
        restored = RESTORE / path
        expected = index[path]
        if not restored.is_file() or record(restored) != {"bytes": expected["bytes"], "sha256": expected["sha256"]}:
            raise ValueError(f"RESTORE_SAMPLE_MISMATCH:{path}")
    return index


def load_journal() -> dict[str, dict]:
    rows = {}
    if JOURNAL.exists():
        with JOURNAL.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    rows[row["path"]] = row
    return rows


def survivor_ok(item: dict, archives: dict[str, dict]) -> bool:
    if item["survivor_kind"] == "live":
        live = ROOT / item["survivor"]
        return live.is_file() and record(live) == {"bytes": item["bytes"], "sha256": item["sha256"]}
    row = archives.get(item["path"])
    return bool(row and row.get("sha256") == item["sha256"] and row.get("bytes") == item["bytes"]
                and row.get("volume") and row.get("member"))


def precheck() -> None:
    plan, binding = load_plan()
    archives = archive_index(plan)
    journaled = load_journal()
    checked = 0
    for item in plan["items"]:
        source = ROOT / item["path"]
        if item["path"] in journaled and not source.exists():
            if not survivor_ok(item, archives):
                raise ValueError(f"SURVIVOR_MISSING_FOR_JOURNALED:{item['path']}")
            continue
        if not source.is_file() or record(source) != {"bytes": item["bytes"], "sha256": item["sha256"]}:
            raise ValueError(f"SOURCE_MISMATCH:{item['path']}")
        if not survivor_ok(item, archives):
            raise ValueError(f"SURVIVOR_MISMATCH:{item['path']}")
        checked += 1
    for item in plan["derived"]:
        source = ROOT / item["path"]
        if item["path"] in journaled and not source.exists():
            continue
        if not source.is_file() or record(source) != {"bytes": item["bytes"], "sha256": item["sha256"]}:
            raise ValueError(f"B_SOURCE_MISMATCH:{item['path']}")
        if record(ROOT / item["generator"]) != item["generator_record"]:
            raise ValueError(f"B_GENERATOR_CHANGED:{item['generator']}")
        if record(ROOT / item["evidence"]) != item["evidence_record"]:
            raise ValueError(f"B_EVIDENCE_CHANGED:{item['evidence']}")
        for input_root in item["declared_inputs"]:
            if not (ROOT / input_root).is_dir():
                raise ValueError(f"B_INPUT_MISSING:{input_root}")
    result = {"status": "PASS", "run_sources_checked": checked,
              "journaled_already_deleted": len(journaled), **binding}
    (OUT / "precheck.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))


def protection_checks(plan: dict) -> dict:
    checks = {}
    checks["live_pages_unchanged"] = all(
        (ROOT / path).is_file() and record(ROOT / path) == rec
        for path, rec in plan["live_baseline"].items())
    checks["protected_files_unchanged"] = all(
        (ROOT / path).is_file() and record(ROOT / path) == rec
        for path, rec in plan["protected_files"].items())
    checks["g1_archive_unchanged"] = g1_baseline() == plan["g1_baseline"]
    checks["metadata_unchanged"] = all(
        (ROOT / item["path"]).is_file() and record(ROOT / item["path"]) == {
            "bytes": item["bytes"], "sha256": item["sha256"]}
        for item in plan["metadata"])
    return checks


def execute(max_items: int | None) -> None:
    plan, binding = load_plan()
    archives = archive_index(plan)
    journaled = load_journal()
    processed = 0
    failures = []
    with JOURNAL.open("a", encoding="utf-8") as journal:
        for item in plan["items"]:
            if max_items is not None and processed >= max_items:
                break
            path = item["path"]
            source = ROOT / path
            prior = journaled.get(path)
            try:
                if prior and not source.exists():
                    if not survivor_ok(item, archives):
                        raise ValueError("SURVIVOR_MISSING_FOR_PRIOR_DELETE")
                    continue
                if not source.is_file() or record(source) != {"bytes": item["bytes"], "sha256": item["sha256"]}:
                    raise ValueError("SOURCE_HASH_MISMATCH")
                if not survivor_ok(item, archives):
                    raise ValueError("SURVIVOR_HASH_MISMATCH")
                os.remove(source)
                if source.exists():
                    raise ValueError("SOURCE_STILL_PRESENT")
                row = {**item, "result": "DELETED", "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
                journal.write(json.dumps(row, ensure_ascii=False) + "\n")
                journal.flush()
                journaled[path] = row
                processed += 1
            except Exception as exc:
                row = {"path": path, "result": "STOP_SOURCE_PRESERVED", "error": repr(exc)}
                journal.write(json.dumps(row, ensure_ascii=False) + "\n")
                journal.flush()
                failures.append(row)
                break
        if max_items is not None:
            result = {"status": "PARTIAL" if not failures else "FAIL", "deleted_this_run": processed,
                      "journal_entries": len(journaled), "failures": failures}
            (OUT / "micro_batch_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
            print(json.dumps(result, ensure_ascii=False, indent=1))
            if failures:
                raise RuntimeError(failures[0])
            return
        for item in plan["derived"]:
            path = item["path"]
            source = ROOT / path
            prior = journaled.get(path)
            try:
                if prior and not source.exists():
                    continue
                if not source.is_file() or record(source) != {"bytes": item["bytes"], "sha256": item["sha256"]}:
                    raise ValueError("B_SOURCE_HASH_MISMATCH")
                if record(ROOT / item["generator"]) != item["generator_record"]:
                    raise ValueError("B_GENERATOR_CHANGED")
                if record(ROOT / item["evidence"]) != item["evidence_record"]:
                    raise ValueError("B_EVIDENCE_CHANGED")
                for input_root in item["declared_inputs"]:
                    if not (ROOT / input_root).is_dir():
                        raise ValueError(f"B_INPUT_MISSING:{input_root}")
                os.remove(source)
                row = {**item, "result": "DELETED", "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
                journal.write(json.dumps(row, ensure_ascii=False) + "\n")
                journal.flush()
                journaled[path] = row
            except Exception as exc:
                row = {"path": path, "result": "STOP_SOURCE_PRESERVED", "error": repr(exc)}
                journal.write(json.dumps(row, ensure_ascii=False) + "\n")
                journal.flush()
                failures.append(row)
                break
    if failures:
        raise RuntimeError(failures[0])
    for key in plan["runs"]:
        transactions = PAGES / key / "transactions"
        if transactions.exists():
            for directory in sorted((p for p in transactions.rglob("*") if p.is_dir()),
                                    key=lambda p: len(p.parts), reverse=True):
                if not any(directory.iterdir()):
                    directory.rmdir()
    checks = protection_checks(plan)
    checks["all_run_sources_deleted"] = all(not (ROOT / x["path"]).exists() for x in plan["items"])
    checks["all_derived_sources_deleted"] = all(not (ROOT / x["path"]).exists() for x in plan["derived"])
    if not all(checks.values()):
        raise ValueError(f"PRE_RELEASE_CHECKS_FAILED:{checks}")
    evidence = {
        "status": "PASS", "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "authorization": "docs/角色技能完整解读实施方案.md#62-周期收尾ab-清理与-git-推送2026-10-31-用户确认",
        "plan": rel(PLAN), "plan_sha256": sha(PLAN), "journal": rel(JOURNAL),
        "journal_sha256": sha(JOURNAL), "archive_vault": rel(VAULT),
        "archive_catalog_sha256": sha(VAULT / "catalog.json") if (VAULT / "catalog.json").exists() else None,
        "restore_sample_root": rel(RESTORE), "counts": {
            "run_deleted_files": len(plan["items"]), "run_deleted_bytes": sum(x["bytes"] for x in plan["items"]),
            "derived_deleted_files": len(plan["derived"]),
            "derived_deleted_bytes": sum(x["bytes"] for x in plan["derived"]),
            "metadata_kept_files": len(plan["metadata"]),
        }, "checks": checks, "state_before": plan["state_before"],
    }
    DISPOSITION.write_text(json.dumps(evidence, ensure_ascii=False, indent=1), encoding="utf-8")
    released = []
    for key in plan["runs"]:
        rec = run_retention.release_reservation(PAGES, key, DISPOSITION)
        released.append({"run": key, "status": rec["status"],
                         "retained_metadata_bytes": rec.get("retained_metadata_bytes")})
    after = state_summary()
    accounting = {
        "status": "PASS" if after["active_runs"] == 0 and after["max_runs"] == 12
                           and after["max_bytes"] == 8 * 1024 ** 3 else "FAIL",
        "evidence": rel(DISPOSITION), "evidence_sha256": sha(DISPOSITION),
        "released": released, "state_before": plan["state_before"], "state_after": after,
        "disk_free_before": plan["disk_free_before"], "disk_free_after_execute": shutil.disk_usage(ROOT).free,
    }
    ACCOUNTING.write_text(json.dumps(accounting, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(accounting, ensure_ascii=False, indent=1))
    if accounting["status"] != "PASS":
        raise ValueError("CAPACITY_ACCOUNTING_FAILED")


def postcheck() -> None:
    plan, binding = load_plan()
    checks = protection_checks(plan)
    checks["all_run_sources_deleted"] = all(not (ROOT / x["path"]).exists() for x in plan["items"])
    checks["all_derived_sources_deleted"] = all(not (ROOT / x["path"]).exists() for x in plan["derived"])
    checks["c8_c_class_preserved"] = all((ROOT / p).is_file() for p in plan["c_class"][0]["paths"])
    after = state_summary()
    checks["all_12_reservations_released"] = after["active_runs"] == 0
    checks["limits_unchanged"] = after["max_runs"] == 12 and after["max_bytes"] == 8 * 1024 ** 3
    journal = load_journal()
    expected = {x["path"] for x in plan["items"]} | {x["path"] for x in plan["derived"]}
    checks["journal_covers_exact_whitelist"] = set(journal) == expected and all(
        row.get("result") == "DELETED" for row in journal.values())
    free_after = shutil.disk_usage(ROOT).free
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
        "journal_entries": len(journal), "run_deleted_bytes": sum(x["bytes"] for x in plan["items"]),
        "derived_deleted_bytes": sum(x["bytes"] for x in plan["derived"]),
        "archive_bytes": sum(p.stat().st_size for p in VAULT.rglob("*") if p.is_file()) if VAULT.exists() else 0,
        "c_class_preserved_bytes": plan["c_class"][0]["bytes"],
        "disk_free_before": plan["disk_free_before"], "disk_free_after": free_after,
        "disk_free_delta": free_after - plan["disk_free_before"], "state_after": after,
    }
    POSTCHECK.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))
    if result["status"] != "PASS":
        raise ValueError("POSTCHECK_FAILED")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    sub.add_parser("precheck")
    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--max-items", type=int)
    sub.add_parser("postcheck")
    args = parser.parse_args()
    if args.command == "plan":
        make_plan()
    elif args.command == "precheck":
        precheck()
    elif args.command == "execute":
        execute(args.max_items)
    else:
        postcheck()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
