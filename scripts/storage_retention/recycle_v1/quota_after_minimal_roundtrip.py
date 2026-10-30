"""G1 缺口1：E 盘配额调大后合成夹具最小闭环验证（2026-10-27）。

只处理 work/storage_recycle_g1_20261027/recycle_fixtures/ 下由内置配方生成的合成文件，
逐字节可复算、过 guard。绝不回收真实候选；绝不用通用删除；恢复只复制 $R 到全新目录。

分支（全部真实入站→定位自身条目→同 hash 恢复，除取消/部分成功/新进程续跑按说明）：
  1. 中文/空格（4096）
  2. 长文件名（整条绝对路径 <=260，新 UUID 内置配方夹具）
  3. 8 MiB
  4. 取消（PreDeleteItem 拒绝）保源
  5. 部分成功（1 成功 + 1 取消）逐项对账
  6. 新进程续跑（入站后独立 Python 子进程 locate + restore）
  OS 重启：UNVERIFIED

安全：本脚本不实现任何回收逻辑，全部复用 recycle_shell_backend / recycle_fixture 的
guard 与真实动作原语；不对后端行为做任何放宽。出现永久删除风险/未预期错误 → 停机保源。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import uuid
from pathlib import Path

import recycle_fixture as rf
import recycle_shell_backend as b

FOLLOWUP = b.FOLLOWUP
RESTORE_BASE = b.RESTORE_BASE
REPORT_JSON = FOLLOWUP / "gap1_quota_after_minimal_roundtrip.json"
REPORT_MD = FOLLOWUP / "gap1_quota_after_minimal_roundtrip.md"


# ---------------------------------------------------------------------------
# 自定义长文件名（路径 <=260）内置配方夹具
# ---------------------------------------------------------------------------

def custom_expected_manifest(run_id, specs_list):
    """与 recycle_fixture.expected_manifest 完全同配方（synthetic_chunks 种子/分块），
    仅 spec 列表可自定义。逐字节可复算。"""
    rows = []
    for spec in specs_list:
        digest = hashlib.sha256()
        for chunk in rf.synthetic_chunks(run_id, spec):
            digest.update(chunk)
        rows.append({**spec, "sha256": digest.hexdigest()})
    return {"schema": rf.SCHEMA, "run_id": run_id, "files": rows}


def create_long_filename_fixture():
    """新 UUID 目录 + 单条"文件名很长、整条绝对路径 <=260"的合成文件。

    使用内置配方 synthetic_chunks 生成逐字节可复算内容，写 fixtureguard.json。
    """
    run_id = uuid.uuid4().hex
    root = rf.new_directory(rf.FIXTURES, run_id)
    prefix_len = len(str(root.absolute())) + 1  # +1 = 末尾分隔符
    name_len = 259 - prefix_len - 4  # 预留 ".bin"；目标总长 259 <= 260
    if name_len < 120:
        raise rf.Blocked("LONG_FILENAME_NOT_FEASIBLE_" + str(name_len))
    rel = ("n" * name_len) + ".bin"
    specs_list = [{"path": rel, "size": 8192, "queued": True}]
    manifest = custom_expected_manifest(run_id, specs_list)
    for spec in specs_list:
        path = root.joinpath(*spec["path"].split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        rf.no_reparse(path)
        with open(rf.extended(path), "xb") as f:
            for chunk in rf.synthetic_chunks(run_id, spec):
                f.write(chunk)
    rf.write_json_new(root / "fixtureguard.json", manifest)
    return run_id, root, manifest, specs_list[0]


def verify_custom_guard(root, manifest, rel):
    """对自定义夹具执行与 fixtureguard 等价的 guard 校验（标记文件 + 内容 hash + 单链接普通文件）。"""
    rf.no_reparse(root)
    marker = root / "fixtureguard.json"
    rf.no_reparse(marker)
    s = os.lstat(rf.extended(marker))
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_size > 65536:
        raise rf.Blocked("INVALID_MARKER")
    with open(rf.extended(marker), encoding="utf-8") as f:
        on_disk = json.load(f)
    if on_disk != manifest:
        raise rf.Blocked("MANIFEST_NOT_SYNTHETIC_RECIPE")
    spec = next((r for r in manifest["files"] if r["path"] == rel), None)
    if spec is None or not spec["queued"]:
        raise rf.Blocked("NOT_A_QUEUED_SYNTHETIC_SOURCE")
    p = root.joinpath(*rel.split("/"))
    rf.no_reparse(p)
    s2 = os.lstat(rf.extended(p))
    if not stat.S_ISREG(s2.st_mode) or s2.st_nlink != 1:
        raise rf.Blocked("NOT_SINGLE_LINK_REGULAR_FILE")
    if s2.st_size != spec["size"] or rf.file_digest(p) != spec["sha256"]:
        raise rf.Blocked("SYNTHETIC_CONTENT_MISMATCH")
    return True


def custom_restore(entries, run_id):
    """把自身条目 $R 内容复制到全新目录并校验 SHA-256（目标不存在才写，不覆盖）。"""
    target_dir = rf.new_directory(RESTORE_BASE, rf.validate_id(run_id))
    restored = []
    for e in entries:
        r_name = "$R" + e["entry_i_name"][2:]
        r_path = b.recycle_bin_dir() / r_name
        with open(rf.extended(r_path), "rb") as src:
            data = src.read()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != e["expected_bytes"] or digest != e["expected_sha256"]:
            restored.append({**e, "result": "SKIPPED_HASH_MISMATCH"})
            continue
        target = target_dir.joinpath(*e["original_path"].split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        rf.no_reparse(target)
        with open(rf.extended(target), "xb") as dst:
            dst.write(data)
        restored.append({**e, "result": "RESTORED", "restored_to": str(target),
                         "restored_sha256": digest})
    return restored, target_dir


# ---------------------------------------------------------------------------
# 只读探测
# ---------------------------------------------------------------------------

def probe():
    env = b.windows_probe()
    agg = env.get("recycle_aggregate", {})
    disk = env.get("disk", {})
    vol_reg = env.get("registry", {}).get("HKCU/volume", {})
    out = {
        "os": env.get("os"),
        "drive_type": env.get("drive_type"),
        "token_context": env.get("token_context", {}),
        "session_id": env.get("session_id"),
        "com_activation": env.get("com", {}).get("IFileOperation_activation_hresult"),
        "recycle_aggregate": agg,
        "disk_free": disk.get("free"),
        "volume_registry": vol_reg.get("values") or vol_reg,
        "ALLOW_REAL_RECYCLE": b.ALLOW_REAL_RECYCLE,
    }
    return out


# ---------------------------------------------------------------------------
# 分支执行
# ---------------------------------------------------------------------------

def _source_hash(run_id, rel):
    root, _manifest = b.load_guard(run_id)
    p = root.joinpath(*rel.split("/"))
    return rf.file_digest(p)


def _entry_summary(entries):
    return [{
        "entry_i_name": e.get("entry_i_name"),
        "original_path": e.get("original_path"),
        "expected_bytes": e.get("expected_bytes"),
        "actual_bytes": e.get("actual_bytes"),
        "hash_match": e.get("hash_match"),
        "actual_sha256": e.get("actual_sha256"),
    } for e in entries]


def _restore_summary(restore):
    if isinstance(restore, dict) and "restored" in restore:
        return [{
            "original_path": r.get("original_path"),
            "result": r.get("result"),
            "restored_sha256": r.get("restored_sha256"),
            "restored_to": r.get("restored_to"),
        } for r in restore["restored"]]
    return restore


def branch_chinese_spaces():
    run_id = b.create_fixtures()
    res = b.recycle_run(run_id, True, relative_paths=["中文 空格/夹具 数据.txt"])
    ok = (not res["operation"].get("permanent_delete_risk")
          and not res["operation"].get("cancelled")
          and len(res["self_entries"]) == 1
          and res["self_entries"][0]["hash_match"]
          and res["restore"].get("real_restore_attempted")
          and any(r["result"] == "RESTORED" for r in res["restore"]["restored"]))
    return {"branch": "chinese_spaces", "run_id": run_id, "ok": ok, "res": res,
            "detail": "中文 空格/夹具 数据.txt 入站→定位→同 hash 恢复"}


def branch_long_filename():
    run_id, root, manifest, spec = create_long_filename_fixture()
    rel = spec["path"]
    guard_ok = verify_custom_guard(root, manifest, rel)
    path = root.joinpath(*rel.split("/"))
    name_len = len(rel)
    total_len = len(str(path.absolute()))
    before_q = b.query_recycle_bin()
    before_i = b.snapshot_i_names()
    op = b._shell_recycle_paths([rf.extended(path)])
    after_q = b.query_recycle_bin()
    after_i = b.snapshot_i_names()
    new_i = sorted(after_i - before_i)
    entries = b.match_self_entries(new_i, manifest, root)
    restored, restore_dir = custom_restore(entries, run_id)
    ok = (guard_ok and not op.get("permanent_delete_risk") and not op.get("cancelled")
          and len(entries) == 1 and entries[0]["hash_match"]
          and entries[0]["original_path"] == rel
          and any(r["result"] == "RESTORED" and r["restored_sha256"] == r["expected_sha256"]
                  for r in restored))
    res = {
        "run_id": run_id, "operation": op,
        "recycle_bin_before": before_q, "recycle_bin_after": after_q,
        "i_before_count": len(before_i), "i_after_count": len(after_i),
        "i_diff_count": len(new_i),
        "self_entries": entries,
        "restore": {"real_restore_attempted": any(r["result"] == "RESTORED" for r in restored),
                    "restored": restored, "restore_root": str(restore_dir)},
        "long_filename_chars": name_len, "absolute_path_chars": total_len,
        "guard_ok": guard_ok,
    }
    return {"branch": "long_filename_le260", "run_id": run_id, "ok": ok, "res": res,
            "detail": f"长文件名 {name_len} 字符，整条绝对路径 {total_len} 字符(<=260)，入站→定位→同 hash 恢复"}


def branch_large_8mib():
    run_id = b.create_fixtures()
    res = b.recycle_run(run_id, True, relative_paths=["较大夹具/8 MiB.bin"])
    ok = (not res["operation"].get("permanent_delete_risk")
          and not res["operation"].get("cancelled")
          and len(res["self_entries"]) == 1
          and res["self_entries"][0]["hash_match"]
          and res["restore"].get("real_restore_attempted")
          and any(r["result"] == "RESTORED" for r in res["restore"]["restored"]))
    return {"branch": "large_8mib", "run_id": run_id, "ok": ok, "res": res,
            "detail": "较大夹具/8 MiB.bin 入站→定位→同 hash 恢复"}


def branch_cancel():
    run_id = b.create_fixtures()
    rel = "中文 空格/夹具 数据.txt"
    hash_before = _source_hash(run_id, rel)
    res = b.recycle_run(run_id, True, relative_paths=[rel], cancel_after=1)
    root, _m = b.load_guard(run_id)
    p = root.joinpath(*rel.split("/"))
    source_still_exists = p.exists()
    hash_after = rf.file_digest(p) if source_still_exists else None
    op = res["operation"]
    source_gone = any(x["source_gone"] for x in res["per_item"])
    ok = (op.get("cancelled") and not op.get("permanent_delete_risk")
          and not source_gone and source_still_exists and hash_after == hash_before
          and len(res["self_entries"]) == 0)
    return {"branch": "cancel_predelete", "run_id": run_id, "ok": ok, "res": res,
            "source_preserved": source_still_exists and hash_after == hash_before,
            "source_hash_before": hash_before, "source_hash_after": hash_after,
            "detail": "PreDeleteItem 拒绝入站，源文件保留且 hash 不变"}


def branch_partial():
    run_id = b.create_fixtures()
    item1 = "中文 空格/夹具 数据.txt"
    item2 = "同名乙/same.txt"
    hash2_before = _source_hash(run_id, item2)
    res = b.recycle_run(run_id, True, relative_paths=[item1, item2], cancel_after=2)
    root, _m = b.load_guard(run_id)
    p2 = root.joinpath(*item2.split("/"))
    item2_still_exists = p2.exists()
    hash2_after = rf.file_digest(p2) if item2_still_exists else None
    per = {x["path"]: x for x in res["per_item"]}
    i1 = per.get(item1, {})
    i2 = per.get(item2, {})
    op = res["operation"]
    ok = (op.get("cancelled") and not op.get("permanent_delete_risk")
          and i1.get("source_gone") and i1.get("self_entry_located")
          and not i2.get("source_gone") and not i2.get("self_entry_located")
          and item2_still_exists and hash2_after == hash2_before
          and len(res["self_entries"]) == 1
          and res["self_entries"][0]["hash_match"])
    return {"branch": "partial_success", "run_id": run_id, "ok": ok, "res": res,
            "item2_preserved": item2_still_exists and hash2_after == hash2_before,
            "item2_hash_before": hash2_before, "item2_hash_after": hash2_after,
            "detail": "item1 入站+定位+恢复；item2 PreDeleteItem 取消保源；逐项对账，不伪报整批、不重试"}


def branch_new_process():
    run_id = b.create_fixtures()
    rel = "中文 空格/夹具 数据.txt"
    res = b.recycle_run(run_id, True, relative_paths=[rel], do_restore=False)
    located = (len(res["self_entries"]) >= 1
               and all(e["hash_match"] for e in res["self_entries"]))
    script = str(Path(b.__file__).absolute())
    loc = subprocess.run([sys.executable, "-X", "utf8", "-B", script, "locate", "--run-id", run_id],
                         capture_output=True, timeout=120, check=False)
    rst = subprocess.run([sys.executable, "-X", "utf8", "-B", script, "restore", "--run-id", run_id],
                         capture_output=True, timeout=120, check=False)
    locate_data = json.loads(loc.stdout.decode("utf-8")) if loc.returncode == 0 else None
    restore_data = json.loads(rst.stdout.decode("utf-8")) if rst.returncode == 0 else None
    reverify_ok = bool(locate_data and all(e.get("reverify_ok")
                                           for e in locate_data.get("self_entries", [])))
    restored_ok = bool(restore_data and any(
        r.get("result") == "RESTORED" and r.get("restored_sha256") == r.get("expected_sha256")
        for r in restore_data.get("restored", [])))
    ok = (located and loc.returncode == 0 and rst.returncode == 0
          and reverify_ok and restored_ok)
    return {"branch": "new_process_resume", "run_id": run_id, "ok": ok, "res": res,
            "locate_returncode": loc.returncode, "locate_reverify_ok": reverify_ok,
            "restore_returncode": rst.returncode, "restore_ok": restored_ok,
            "detail": "入站后独立 Python 子进程重新 locate + restore + 同 hash"}


BRANCHES = [
    ("chinese_spaces", branch_chinese_spaces),
    ("long_filename_le260", branch_long_filename),
    ("large_8mib", branch_large_8mib),
    ("cancel_predelete", branch_cancel),
    ("partial_success", branch_partial),
    ("new_process_resume", branch_new_process),
]


def run_all():
    env_snapshot = probe()
    before_all = b.query_recycle_bin()
    results = []
    stopped = False
    for label, fn in BRANCHES:
        if stopped:
            results.append({"branch": label, "mode": "ACTUAL_SHELL", "result": "NOT_RUN",
                            "detail": "stopped after earlier safety stop"})
            continue
        try:
            r = fn()
            op = r["res"].get("operation", {})
            if op.get("permanent_delete_risk"):
                result = "BLOCKED"
                stopped = True
            elif not r["ok"]:
                result = "FAIL"
                stopped = True
            else:
                result = "PASS"
            rec = {
                "branch": r["branch"], "mode": "ACTUAL_SHELL", "result": result,
                "run_id": r["run_id"], "detail": r["detail"],
                "operation": {k: op.get(k) for k in
                              ("perform_hr", "any_aborted", "permanent_delete_risk", "cancelled")},
                "recycle_bin_before": r["res"].get("recycle_bin_before"),
                "recycle_bin_after": r["res"].get("recycle_bin_after"),
                "i_before_count": r["res"].get("i_before_count"),
                "i_after_count": r["res"].get("i_after_count"),
                "i_diff_count": r["res"].get("i_diff_count"),
                "self_entries": _entry_summary(r["res"].get("self_entries", [])),
                "restore": _restore_summary(r["res"].get("restore", {})),
                "per_item": r["res"].get("per_item"),
                "source_preserved": r.get("source_preserved"),
                "item2_preserved": r.get("item2_preserved"),
                "long_filename_chars": r["res"].get("long_filename_chars"),
                "absolute_path_chars": r["res"].get("absolute_path_chars"),
                "guard_ok": r["res"].get("guard_ok"),
                "locate_returncode": r.get("locate_returncode"),
                "locate_reverify_ok": r.get("locate_reverify_ok"),
                "restore_returncode": r.get("restore_returncode"),
                "restore_ok": r.get("restore_ok"),
            }
            # 去除 None 字段，保持报告干净
            rec = {k: v for k, v in rec.items() if v is not None}
            results.append(rec)
        except (rf.Blocked, OSError, ValueError, subprocess.SubprocessError) as exc:
            results.append({"branch": label, "mode": "ACTUAL_SHELL", "result": "FAIL",
                            "error": rf.error_code(exc), "detail": "branch raised: " + type(exc).__name__,
                            "real_recycle_attempted": True, "real_restore_attempted": False})
            stopped = True

    results.append({"branch": "os_restart", "mode": "ACTUAL_SHELL", "result": "UNVERIFIED",
                    "detail": "OS 重启未实测，明确不声称"})

    passed = [x for x in results if x.get("result") == "PASS"]
    failed = [x for x in results if x.get("result") == "FAIL"]
    blocked = [x for x in results if x.get("result") == "BLOCKED"]
    unverified = [x for x in results if x.get("result") == "UNVERIFIED"]
    not_run = [x for x in results if x.get("result") == "NOT_RUN"]
    overall = "PASS" if (not failed and not blocked) else "HAS_FAILURES_OR_BLOCKED"

    report = {
        "schema": "cc-storage-recycle-g1-quota-after-minimal-roundtrip-v1",
        "created_utc": rf.now(),
        "task": "gap1 E-drive quota-adjusted synthetic-fixture minimal roundtrip",
        "overall": overall,
        "environment_snapshot": env_snapshot,
        "recycle_bin_before_all": before_all,
        "pass_count": len(passed), "fail_count": len(failed),
        "blocked_count": len(blocked), "unverified_count": len(unverified),
        "not_run_count": len(not_run),
        "os_restart": "UNVERIFIED",
        "real_recycle_attempted": True, "real_restore_attempted": True,
        "branches": results,
        "declarations": {
            "only_synthetic_fixtures": True,
            "no_real_candidate_recycled": True,
            "no_final_release_or_empty_recycle_bin": True,
            "no_global_settings_or_registry_or_acl_changed": True,
            "no_generic_delete_used": True,
            "no_html_connected_resource_recycled_this_round": True,
            "restore_only_copies_R_to_fresh_dir_no_remove": True,
            "no_git_no_publish_no_cross_agent_contact": True,
        },
        "privacy": "no SID written to disk; no unrelated recycle entry names/content recorded",
    }
    return report


def render_md(report):
    lines = ["# G1 缺口1：E 盘配额调大后合成夹具最小闭环验证（2026-10-27）", "",
             "结论：" + report["overall"], "",
             f'- PASS {report["pass_count"]} / FAIL {report["fail_count"]} / BLOCKED {report["blocked_count"]} / '
             f'UNVERIFIED {report["unverified_count"]} / NOT_RUN {report["not_run_count"]}',
             f'- OS 重启={report["os_restart"]}',
             f'- real_recycle_attempted={report["real_recycle_attempted"]}, '
             f'real_restore_attempted={report["real_restore_attempted"]}',
             "", "## 只读环境快照", "",
             f'- ALLOW_REAL_RECYCLE={report["environment_snapshot"].get("ALLOW_REAL_RECYCLE")}',
             f'- SHQueryRecycleBinW(E:\\) 本轮开始前：'
             f'{report["recycle_bin_before_all"]}',
             f'- COM IFileOperation 激活 HRESULT：'
             f'{report["environment_snapshot"].get("com_activation")}',
             f'- E 盘磁盘空闲：{report["environment_snapshot"].get("disk_free")} 字节',
             f'- E 盘卷注册表（只读）：{report["environment_snapshot"].get("volume_registry")}',
             f'- token 上下文：{report["environment_snapshot"].get("token_context")}',
             "", "## 分支结果", "",
             "| 分支 | 类型 | 结果 | 说明 |", "|---|---|---|---|"]
    for br in report["branches"]:
        lines.append(f'| {br["branch"]} | {br.get("mode")} | {br.get("result")} | {br.get("detail")} |')
    lines += ["", "## 各分支前后计量与定位", ""]
    for br in report["branches"]:
        if br.get("result") in ("NOT_RUN", "UNVERIFIED"):
            continue
        lines.append(f'### {br["branch"]}（run_id={br.get("run_id")}）')
        lines.append("")
        rb_b = br.get("recycle_bin_before") or {}
        rb_a = br.get("recycle_bin_after") or {}
        lines.append(f'- 入站前 SHQueryRecycleBinW：bytes={rb_b.get("bytes")}, items={rb_b.get("items")}')
        lines.append(f'- 入站后 SHQueryRecycleBinW：bytes={rb_a.get("bytes")}, items={rb_a.get("items")}')
        lines.append(f'- $I 数量：入站前 {br.get("i_before_count")}，入站后 {br.get("i_after_count")}，'
                     f'diff={br.get("i_diff_count")}')
        if br.get("long_filename_chars"):
            lines.append(f'- 长文件名字符数={br.get("long_filename_chars")}，'
                         f'绝对路径字符数={br.get("absolute_path_chars")}，guard_ok={br.get("guard_ok")}')
        if br.get("source_preserved") is not None:
            lines.append(f'- 源文件保留且 hash 不变：{br.get("source_preserved")}')
        if br.get("item2_preserved") is not None:
            lines.append(f'- item2 源文件保留且 hash 不变：{br.get("item2_preserved")}')
        for e in br.get("self_entries", []):
            lines.append(f'- 定位条目：{e.get("original_path")}（$I={e.get("entry_i_name")}，'
                         f'hash_match={e.get("hash_match")}，{e.get("actual_bytes")} 字节）')
        for r in br.get("restore", []):
            if r.get("result") == "RESTORED":
                lines.append(f'- 恢复：{r.get("original_path")} -> {r.get("restored_to")}，'
                             f'sha256={r.get("restored_sha256")}')
    lines += ["", "## 声明", "",
              "本轮只入站由内置配方生成的合成夹具，未回收任何真实候选，未做最终释放/清空回收站，",
              "未改全局回收/清理设置/注册表/ACL，未用通用删除函数，未设 FOF_NOCONFIRMATION/FOF_SILENT，",
              "恢复只把 $R 复制到全新目录（目标不存在才写），未从回收站还原移除条目，",
              "未 Git、未发布、未联系其他对话。OS 重启未实测，明确标 UNVERIFIED。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--render-md-only", action="store_true",
                        help="render MD from existing JSON report without any recycle action")
    args = parser.parse_args()
    if args.probe_only:
        print(json.dumps(probe(), ensure_ascii=False, indent=2))
        return 0
    if args.render_md_only:
        if not REPORT_JSON.exists():
            raise rf.Blocked("REPORT_JSON_MISSING")
        if REPORT_MD.exists():
            raise rf.Blocked("REPORT_EXISTS_NOT_OVERWRITING")
        with open(rf.extended(REPORT_JSON), encoding="utf-8") as f:
            report = json.load(f)
        with open(rf.extended(REPORT_MD), "x", encoding="utf-8", newline="\n") as f:
            f.write(render_md(report))
        print(json.dumps({"rendered_md": str(REPORT_MD)}, ensure_ascii=False))
        return 0
    report = run_all()
    if REPORT_JSON.exists() or REPORT_MD.exists():
        raise rf.Blocked("REPORT_EXISTS_NOT_OVERWRITING")
    rf.write_json_new(REPORT_JSON, report)
    with open(rf.extended(REPORT_MD), "x", encoding="utf-8", newline="\n") as f:
        f.write(render_md(report))
    print(json.dumps({"overall": report["overall"],
                      "pass_count": report["pass_count"],
                      "fail_count": report["fail_count"],
                      "blocked_count": report["blocked_count"],
                      "unverified_count": report["unverified_count"],
                      "not_run_count": report["not_run_count"],
                      "report_json": str(REPORT_JSON),
                      "report_md": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if (report["fail_count"] == 0 and report["blocked_count"] == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
