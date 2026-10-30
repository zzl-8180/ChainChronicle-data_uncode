"""G1 fixture capability audit. No deletion backend, no G2/G3 implementation.

Default: read-only Windows probes + an append-only diagnostic report. `exercise`
creates bounded synthetic files and tests guards/models; it never recycles files.
"""
from __future__ import annotations

import argparse
import copy
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
import uuid


PROJECT = Path(__file__).absolute().parents[3]
FIXTURES = PROJECT / "work/storage_recycle_g1_20261027/recycle_fixtures"
RECORDS = PROJECT / "output/storage_retention/recycle_g1_20261027/recycle_tests"
SCHEMA = "cc-storage-recycle-g1-fixture-v1"
RESERVE = 64 * 1024 * 1024
MAX_FIXTURE_BYTES = 16 * 1024 * 1024
# This is a requirements contract, NOT a validated/installed action backend.
SHELL_FLAG_CONTRACT = {
    "FOF_ALLOWUNDO": 0x0040,
    "FOF_NO_CONNECTED_ELEMENTS": 0x2000,
    "FOF_WANTNUKEWARNING": 0x4000,
    "FOF_NOERRORUI": 0x0400,
    "FOFX_RECYCLEONDELETE": 0x00080000,
    "FOFX_EARLYFAILURE": 0x00100000,
}


class Blocked(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def error_code(exc):
    # Do not log exception strings: Windows exceptions may contain private names.
    return {"type": type(exc).__name__, "winerror": getattr(exc, "winerror", None),
            "errno": getattr(exc, "errno", None)}


def hresult(value):
    return f"0x{value & 0xffffffff:08X}"


def extended(path):
    text = str(path.absolute())
    return "\\\\?\\" + text if os.name == "nt" and not text.startswith("\\\\?\\") else text


def no_reparse(path):
    """Check lexical ancestors without following a junction/symlink first.

    Not a race-free delete authorization: no mutation backend consumes this guard.
    """
    for part in reversed((path, *path.parents)):
        try:
            s = os.lstat(extended(part))
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
            raise Blocked("REPARSE_POINT")


def new_directory(parent, name):
    no_reparse(parent)
    parent.mkdir(parents=True, exist_ok=True)
    no_reparse(parent)
    target = parent / name
    target.mkdir(exist_ok=False)
    return target


def write_json_new(path, data):
    no_reparse(path.parent)
    with open(extended(path), "x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def specs():
    long_name = "/".join(["长路径_" + "x" * 76] * 4) + "/末端 空格.txt"
    return [
        {"path": "中文 空格/夹具 数据.txt", "size": 4096, "queued": True},
        {"path": "同名甲/same.txt", "size": 1024, "queued": True},
        {"path": "同名乙/same.txt", "size": 2048, "queued": True},
        {"path": "连接资源/page.html", "size": 4096, "queued": True},
        {"path": "连接资源/page_files/resource.txt", "size": 1024, "queued": False},
        {"path": long_name, "size": 8192, "queued": True},
        {"path": "较大夹具/8 MiB.bin", "size": 8 * 1024 * 1024, "queued": True},
    ]


def validate_id(run_id):
    if not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise Blocked("INVALID_RUN_ID")
    return run_id


def synthetic_chunks(run_id, spec):
    # Full contents are deterministic synthetic bytes, not caller-supplied files.
    seed = (SCHEMA + "\n" + run_id + "\n" + spec["path"] + "\n").encode("utf-8")
    chunk = (seed * (65536 // len(seed) + 1))[:65536]
    remaining = spec["size"]
    while remaining:
        part = chunk[:remaining]
        yield part
        remaining -= len(part)


def expected_manifest(run_id):
    rows = []
    for spec in specs():
        digest = hashlib.sha256()
        for chunk in synthetic_chunks(run_id, spec):
            digest.update(chunk)
        rows.append({**spec, "sha256": digest.hexdigest()})
    return {"schema": SCHEMA, "run_id": run_id, "files": rows}


def file_digest(path):
    digest = hashlib.sha256()
    with open(extended(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_guard(run_id):
    root = FIXTURES / validate_id(run_id)
    no_reparse(root)
    marker = root / "fixtureguard.json"
    no_reparse(marker)
    s = os.lstat(extended(marker))
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_size > 65536:
        raise Blocked("INVALID_MARKER")
    with open(extended(marker), encoding="utf-8") as f:
        manifest = json.load(f)
    if manifest != expected_manifest(run_id):
        raise Blocked("MANIFEST_NOT_SYNTHETIC_RECIPE")
    return root, manifest


def fixtureguard(run_id, relative, *, queued_only=True):
    root, manifest = load_guard(run_id)
    if (not relative or "\\" in relative or ":" in relative
            or PurePosixPath(relative).is_absolute()
            or any(x in ("", ".", "..") or x.endswith((".", " "))
                   for x in relative.split("/"))):
        raise Blocked("INVALID_RELATIVE_PATH")
    spec = next((r for r in manifest["files"] if r["path"] == relative), None)
    if spec is None or (queued_only and not spec["queued"]):
        raise Blocked("NOT_A_QUEUED_SYNTHETIC_SOURCE")
    path = root.joinpath(*relative.split("/"))
    no_reparse(path)
    s = os.lstat(extended(path))
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
        raise Blocked("NOT_SINGLE_LINK_REGULAR_FILE")
    if s.st_size != spec["size"] or file_digest(path) != spec["sha256"]:
        raise Blocked("SYNTHETIC_CONTENT_MISMATCH")
    return {"path": relative, "bytes": s.st_size, "sha256": spec["sha256"],
            "device": s.st_dev, "file_id": s.st_ino, "links": s.st_nlink,
            "path_characters": len(str(path))}


def create_fixtures():
    run_id = uuid.uuid4().hex
    total = sum(s["size"] for s in specs())
    if total > MAX_FIXTURE_BYTES or shutil.disk_usage(PROJECT).free < total + 256 * 1024 * 1024:
        raise Blocked("FIXTURE_CREATION_SPACE_GUARD")
    root = new_directory(FIXTURES, run_id)
    manifest = expected_manifest(run_id)
    for spec in specs():
        path = root.joinpath(*spec["path"].split("/"))
        os.makedirs(extended(path.parent), exist_ok=True)
        no_reparse(path)
        with open(extended(path), "xb") as f:
            for chunk in synthetic_chunks(run_id, spec):
                f.write(chunk)
    # Unlisted, synthetic negative case; never changes an already accepted file.
    with open(extended(root / "unlisted-synthetic.txt"), "xb") as f:
        f.write(b"G1 unlisted synthetic guard-negative case\n")
    write_json_new(root / "fixtureguard.json", manifest)
    return run_id


def registry_values(hive, path, names):
    import winreg
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            values = {}
            for name in names:
                try:
                    value, kind = winreg.QueryValueEx(key, name)
                    values[name] = {"value": value, "type": kind}
                except FileNotFoundError:
                    values[name] = {"state": "ABSENT"}
            return {"state": "READ", "values": values}
    except OSError as exc:
        return {"state": "UNAVAILABLE", **error_code(exc)}


def windows_probe():
    result = {"timestamp_utc": now(), "os": os.name,
              "python": sys.version.split()[0], "pointer_bits": C.sizeof(C.c_void_p) * 8,
              "effective_quota_bytes": None, "ui_control_verified": False,
              "action_backend_validated": False,
              "privacy": "aggregate only; no recycle entry enumeration or names"}
    if os.name != "nt":
        result["platform_blocked"] = True
        return result
    import winreg
    kernel = C.WinDLL("kernel32", use_last_error=True)
    volume_root = "E:\\"
    kernel.GetVolumeNameForVolumeMountPointW.argtypes = [W.LPCWSTR, W.LPWSTR, W.DWORD]
    volume = C.create_unicode_buffer(128)
    ok = kernel.GetVolumeNameForVolumeMountPointW(volume_root, volume, len(volume))
    result["volume"] = {"root": volume_root, "guid_path": volume.value if ok else None,
                        "error": None if ok else C.get_last_error()}
    kernel.GetDriveTypeW.argtypes = [W.LPCWSTR]
    result["drive_type"] = kernel.GetDriveTypeW(volume_root)
    try:
        result["disk"] = dict(zip(("total", "used", "free"), shutil.disk_usage(volume_root)))
    except OSError as exc:
        result["disk"] = {"error": error_code(exc)}
    guid = re.search(r"\{[0-9a-fA-F-]+\}", volume.value) if ok else None
    base = r"Software\Microsoft\Windows\CurrentVersion\Explorer\BitBucket"
    paths = [("global", base, ["NukeOnDelete", "UseGlobalSettings", "Percent", "MaxCapacity"])]
    if guid:
        paths.append(("volume", base + "\\Volume\\" + guid.group(), ["NukeOnDelete", "MaxCapacity"]))
    paths += [("policy", r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
               ["NoRecycleFiles", "RecycleBinSize", "ConfirmFileDelete"])]
    result["registry"] = {}
    for hive_name, hive in [("HKCU", winreg.HKEY_CURRENT_USER), ("HKLM", winreg.HKEY_LOCAL_MACHINE)]:
        for label, path, names in paths:
            result["registry"][hive_name + "/" + label] = {
                "path": path, **registry_values(hive, path, names)}
    result["quota_note"] = ("Raw registry configuration is not proof of effective capacity. "
                            "No default, percent, unit conversion or policy precedence assumed.")

    # shellapi SHQUERYRBINFO uses normal 8-byte alignment in this 64-bit host.
    class Query(C.Structure):
        _fields_ = [("cbSize", W.DWORD), ("i64Size", C.c_int64), ("i64NumItems", C.c_int64)]
    q = Query()
    q.cbSize = C.sizeof(q)
    shell = C.WinDLL("shell32", use_last_error=True)
    shell.SHQueryRecycleBinW.argtypes = [W.LPCWSTR, C.POINTER(Query)]
    shell.SHQueryRecycleBinW.restype = C.c_int32
    hr = shell.SHQueryRecycleBinW(volume_root, C.byref(q))
    result["recycle_aggregate"] = {
        "api": "SHQueryRecycleBinW", "hresult": hresult(hr), "struct_bytes": C.sizeof(q),
        "scope": "E: Shell query for calling security context; not an all-user disk scan",
        "bytes": q.i64Size if hr == 0 else None,
        "items": q.i64NumItems if hr == 0 else None,
    }
    user = C.WinDLL("user32", use_last_error=True)
    user.OpenInputDesktop.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    user.OpenInputDesktop.restype = W.HANDLE
    user.CloseDesktop.argtypes = [W.HANDLE]
    desktop = user.OpenInputDesktop(0, False, 0x100)  # DESKTOP_SWITCHDESKTOP, read-only open
    result["input_desktop"] = {"accessible": bool(desktop),
                               "winerror": None if desktop else C.get_last_error()}
    if desktop:
        user.CloseDesktop(desktop)
    session = W.DWORD()
    kernel.ProcessIdToSessionId.argtypes = [W.DWORD, C.POINTER(W.DWORD)]
    if kernel.ProcessIdToSessionId(os.getpid(), C.byref(session)):
        result["session_id"] = session.value
    # Numeric token context only; never persist user/account names or SID.
    advapi = C.WinDLL("advapi32", use_last_error=True)
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    advapi.OpenProcessToken.argtypes = [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)]
    advapi.GetTokenInformation.argtypes = [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)]
    advapi.IsTokenRestricted.argtypes = [W.HANDLE]
    token = W.HANDLE()
    if advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, C.byref(token)):
        try:
            context = {"restricted": bool(advapi.IsTokenRestricted(token))}
            for label, information_class in [("elevated", 20), ("app_container", 29)]:
                value, returned = W.DWORD(), W.DWORD()
                if advapi.GetTokenInformation(token, information_class, C.byref(value), C.sizeof(value), C.byref(returned)):
                    context[label] = bool(value.value)
                else:
                    context[label] = {"winerror": C.get_last_error()}
            result["token_context"] = context
        finally:
            kernel.CloseHandle(token)
    else:
        result["token_context"] = {"winerror": C.get_last_error()}

    # Test COM activation only. NO SetOperationFlags/DeleteItem/PerformOperations.
    ole = C.WinDLL("ole32", use_last_error=True)
    ole.CoInitializeEx.argtypes = [C.c_void_p, W.DWORD]
    ole.CoInitializeEx.restype = C.c_int32
    init_hr = ole.CoInitializeEx(None, 2)  # STA required by IFileOperation
    result["com"] = {"sta_hresult": hresult(init_hr)}
    if init_hr >= 0:
        try:
            clsid = (C.c_ubyte * 16).from_buffer_copy(uuid.UUID("3ad05575-8857-4850-9277-11b85bdb8e09").bytes_le)
            iid = (C.c_ubyte * 16).from_buffer_copy(uuid.UUID("947aab5f-0a5c-4c13-b4d6-4bf7836fc9f8").bytes_le)
            ptr = C.c_void_p()
            ole.CoCreateInstance.argtypes = [C.c_void_p, C.c_void_p, W.DWORD, C.c_void_p, C.POINTER(C.c_void_p)]
            ole.CoCreateInstance.restype = C.c_int32
            com_hr = ole.CoCreateInstance(C.byref(clsid), None, 1, C.byref(iid), C.byref(ptr))
            result["com"]["IFileOperation_activation_hresult"] = hresult(com_hr)
            if com_hr >= 0 and ptr:
                vtable = C.cast(ptr, C.POINTER(C.POINTER(C.c_void_p))).contents
                C.WINFUNCTYPE(W.ULONG, C.c_void_p)(vtable[2])(ptr)  # IUnknown.Release
        finally:
            ole.CoUninitialize()
    return result


def preflight(env, planned_bytes):
    reasons = []
    if env.get("os") != "nt" or env.get("drive_type") != 3:
        reasons.append("WINDOWS_FIXED_E_DRIVE_NOT_PROVEN")
    query = env.get("recycle_aggregate", {})
    if query.get("hresult") != "0x00000000" or not isinstance(query.get("bytes"), int):
        reasons.append("RECYCLE_EXISTING_USAGE_UNKNOWN")
    quota = env.get("effective_quota_bytes")
    if not isinstance(quota, int) or isinstance(quota, bool) or quota <= 0:
        reasons.append("EFFECTIVE_RECYCLE_QUOTA_UNKNOWN")
    elif isinstance(query.get("bytes"), int) and query["bytes"] + planned_bytes + RESERVE > quota:
        reasons.append("RECYCLE_QUOTA_INSUFFICIENT")
    if env.get("recycle_enabled_verified") is not True:
        reasons.append("RECYCLE_ENABLED_NOT_VERIFIED")
    if env.get("input_desktop", {}).get("accessible") is not True:
        reasons.append("INPUT_DESKTOP_UNAVAILABLE")
    if env.get("ui_control_verified") is not True:
        reasons.append("PERMANENT_DELETE_UI_CANNOT_BE_SAFELY_CONTROLLED")
    if env.get("action_backend_validated") is not True:
        reasons.append("NO_VALIDATED_IFILEOPERATION_BACKEND")
    disk = env.get("disk", {})
    if not isinstance(disk.get("free"), int) or disk["free"] < planned_bytes + RESERVE:
        reasons.append("DISK_HEADROOM_NOT_PROVEN")
    com = env.get("com", {})
    if com.get("IFileOperation_activation_hresult") != "0x00000000":
        reasons.append("IFILEOPERATION_ACTIVATION_NOT_PROVEN")
    return reasons


def receipt_state(source_exists, expected, entry=None, restored_hash=None):
    """Pure simulation contract: disappearance alone cannot prove recycling."""
    if source_exists:
        return "SOURCE_RETAINED"
    if (not entry or entry.get("original") != expected["path"]
            or entry.get("bytes") != expected["size"]
            or entry.get("sha256") != expected["sha256"]
            or not entry.get("entry_id")):
        return "UNCERTAIN_STOP_NO_RETRY"
    if restored_hash != expected["sha256"]:
        return "RECOVERABLE_MODEL_ONLY"
    return "ROUNDTRIP_MODEL_ONLY"


def simulations(run_id):
    """Injected dictionaries/in-memory receipts only, no OS fault injection."""
    env = {"os": "nt", "drive_type": 3, "effective_quota_bytes": 1024**3,
           "recycle_enabled_verified": True,
           "recycle_aggregate": {"hresult": "0x00000000", "bytes": 0},
           "input_desktop": {"accessible": True}, "ui_control_verified": True,
           "action_backend_validated": True, "disk": {"free": 1024**3},
           "com": {"IFileOperation_activation_hresult": "0x00000000"}}
    tests = []

    def check(name, good, detail):
        tests.append({"test": name, "mode": "SIMULATED", "result": "PASS" if good else "FAIL",
                      "real_shell_verified": False, "detail": detail})

    check("preflight_model_nominal", not preflight(env, 4096), "model only; cannot enable a real backend")
    for name, changes, reason in [
        ("unavailable", {"recycle_aggregate": {"hresult": "0x80070005", "bytes": None}}, "RECYCLE_EXISTING_USAGE_UNKNOWN"),
        ("quota_unknown", {"effective_quota_bytes": None}, "EFFECTIVE_RECYCLE_QUOTA_UNKNOWN"),
        ("over_quota", {"effective_quota_bytes": RESERVE}, "RECYCLE_QUOTA_INSUFFICIENT"),
        ("permanent_delete_risk", {"recycle_enabled_verified": False}, "RECYCLE_ENABLED_NOT_VERIFIED"),
        ("uncontrolled_UI", {"ui_control_verified": False}, "PERMANENT_DELETE_UI_CANNOT_BE_SAFELY_CONTROLLED"),
        ("disk_full_risk", {"disk": {"free": 4095}}, "DISK_HEADROOM_NOT_PROVEN"),
    ]:
        injected = copy.deepcopy(env)
        injected.update(changes)
        check(name, reason in preflight(injected, 4096), reason + "; action not called, source retained")
    expected = expected_manifest(run_id)["files"][0]
    entry = {"original": expected["path"], "bytes": expected["size"],
             "sha256": expected["sha256"], "entry_id": "simulated-entry-not-a-shell-item"}
    check("roundtrip_receipt", receipt_state(False, expected, entry, expected["sha256"]) == "ROUNDTRIP_MODEL_ONLY",
          "synthetic identity and matching hash in memory; no actual recycling or restore")
    check("source_disappearance_not_success", receipt_state(False, expected) == "UNCERTAIN_STOP_NO_RETRY",
          "missing source with no matching entry stops without retry")
    for field, bad in [("original", "other"), ("bytes", 1), ("sha256", "bad"), ("entry_id", "")]:
        wrong = {**entry, field: bad}
        check("entry_mismatch_" + field, receipt_state(False, expected, wrong) == "UNCERTAIN_STOP_NO_RETRY",
              "reject mismatched identity/bytes/hash/entry receipt")
    check("restore_hash_mismatch", receipt_state(False, expected, entry, "bad") == "RECOVERABLE_MODEL_ONLY",
          "bad restored hash cannot be classified as roundtrip")
    for name in ["access_denied", "cancelled_before_item"]:
        check(name, receipt_state(True, expected) == "SOURCE_RETAINED", "injected failure; no ACL/UI changes")
    states = [receipt_state(False, expected, entry), receipt_state(True, expected), receipt_state(False, expected)]
    check("partial_success", states == ["RECOVERABLE_MODEL_ONLY", "SOURCE_RETAINED", "UNCERTAIN_STOP_NO_RETRY"],
          "per-item model, never all-success; stop and reconcile, no retry")
    recovered = json.loads(json.dumps(entry))
    check("restart_receipt_model", receipt_state(False, expected, recovered, expected["sha256"]) == "ROUNDTRIP_MODEL_ONLY",
          "JSON receipt survives serialization; not an OS reboot test")
    return tests


def inspect_run(run_id):
    root, manifest = load_guard(run_id)
    rows = [fixtureguard(run_id, row["path"], queued_only=False) for row in manifest["files"]]
    return {"run_id": run_id, "root": str(root), "files": rows,
            "all_sources_present_same_hash": True, "real_recycle_attempted": False,
            "real_restore_attempted": False}


def actual_tests(run_id):
    inspected = inspect_run(run_id)
    tests = [{"test": "fixture_bytes_and_guard", "mode": "ACTUAL_LOCAL", "result": "PASS",
              "detail": "all deterministic synthetic contents and single-link checks passed; no Shell action"}]
    rows = inspected["files"]
    for name, ok, detail in [
        ("chinese_spaces_file", rows[0]["bytes"] == 4096, "created and hashed; Shell roundtrip blocked"),
        ("same_name_different_directories", rows[1]["sha256"] != rows[2]["sha256"],
         "same basename, distinct synthetic bytes and file ids; Shell identity test blocked"),
        ("long_path_file", rows[5]["path_characters"] > 260,
         "extended-length file API, no global setting change; Shell roundtrip blocked"),
        ("larger_fixture_file", rows[6]["bytes"] == 8 * 1024 * 1024,
         "8 MiB bounded synthetic bytes; not quota stress or maximum-file validation"),
    ]:
        tests.append({"test": name, "mode": "ACTUAL_LOCAL", "result": "PASS" if ok else "FAIL", "detail": detail})
    for name, rel in [("reject_project_candidate", "output/real-candidate.zip"),
                      ("reject_traversal", "../HANDOFF.md"),
                      ("reject_absolute", "E:/candidate.zip"),
                      ("reject_ADS", "foo:stream"),
                      ("reject_unlisted", "unlisted-synthetic.txt"),
                      ("reject_connected_resource_queue", "连接资源/page_files/resource.txt")]:
        try:
            fixtureguard(run_id, rel)
            result = "FAIL"
        except Blocked:
            result = "PASS"
        tests.append({"test": name, "mode": "ACTUAL_LOCAL", "result": result,
                      "detail": "guard rejects request before reading non-fixture content"})
    # Independently generated malformed cases; retain all bytes and markers.
    # Never rewrite a valid run or alter another task's input/ACLs.
    for name in ["forged_manifest", "content_mismatch"]:
        negative_id = uuid.uuid4().hex
        negative_root = new_directory(FIXTURES, negative_id)
        negative_manifest = expected_manifest(negative_id)
        first = negative_manifest["files"][0]
        if name == "forged_manifest":
            first["sha256"] = "0" * 64
        else:
            path = negative_root.joinpath(*first["path"].split("/"))
            path.parent.mkdir(parents=True, exist_ok=False)
            with open(extended(path), "xb") as f:
                f.write(b"X" * first["size"])
        write_json_new(negative_root / "fixtureguard.json", negative_manifest)
        try:
            fixtureguard(negative_id, first["path"])
            outcome = "FAIL"
        except Blocked:
            outcome = "PASS"
        tests.append({"test": "reject_" + name, "mode": "ACTUAL_LOCAL", "result": outcome,
                      "detail": "fresh synthetic negative directory retained; no valid fixture modified",
                      "negative_run_id": negative_id})
    command = [sys.executable, "-X", "utf8", "-B", str(Path(__file__).absolute()),
               "inspect", "--run-id", run_id]
    proc = subprocess.run(command, capture_output=True, timeout=60, check=False)
    child = None
    if proc.returncode == 0:
        child = json.loads(proc.stdout.decode("utf-8"))
    tests.append({"test": "new_python_process_reloads_guard", "mode": "ACTUAL_LOCAL",
                  "result": "PASS" if child and child == inspected else "FAIL",
                  "detail": "new Python process validates every source hash; not OS/Shell restart",
                  "returncode": proc.returncode})
    return tests, inspected


def build_report(mode, env, run_id=None):
    report = {"schema": SCHEMA, "created_utc": now(), "mode": mode,
              "overall": "BLOCKED_G1_NOT_PASSED", "environment": env,
              "run_id": run_id, "shell_flag_contract_not_executed": SHELL_FLAG_CONTRACT,
              "real_recycle_attempted": False, "real_restore_attempted": False,
              "action_backend": "NOT_IMPLEMENTED_UNSAFE_ENVIRONMENT",
              "privacy": "no unrelated recycle item names read or logged",
              "tests": [], "blocked_real_cases": [],
              "preservation": "all fixtures/reports retained; no cleanup or settings changes"}
    report["tool_sha256"] = file_digest(Path(__file__).absolute())
    planned = sum(s["size"] for s in specs() if s["queued"])
    report["planned_synthetic_bytes"] = planned
    report["blockers"] = preflight(env, planned)
    if run_id and mode == "exercise":
        tests, inspection = actual_tests(run_id)
        report["tests"] += tests
        report["fixture_inspection"] = inspection
        report["tests"] += simulations(run_id)
        unchanged = inspect_run(run_id) == inspection
        report["tests"].append({"test": "sources_and_connected_resource_retained", "mode": "ACTUAL_LOCAL",
                                "result": "PASS" if unchanged else "FAIL",
                                "detail": "all seven synthetic file identities and hashes unchanged after blocked/model checks"})
    elif run_id:
        report["fixture_inspection"] = inspect_run(run_id)
        report["tests"].append({"test": "existing_fixture_reconciled_without_retry", "mode": "ACTUAL_LOCAL",
                                "result": "PASS", "detail": "persisted synthetic manifest and all source hashes revalidated; no action/retry"})
    for case in ["中文空格入站及恢复", "同名异目录身份及恢复", "HTML无连接资源连带",
                 "长路径入站及恢复", "8MiB夹具入站及恢复", "真实拒绝访问保源",
                 "真实中途取消保源", "真实部分成功逐项对账", "操作系统重启后恢复",
                 "识别真实可恢复条目", "真实恢复到新目录同SHA256", "有效配额覆盖现有占用及余量"]:
        report["blocked_real_cases"].append({"test": case, "mode": "ACTUAL_SHELL",
                                              "result": "BLOCKED", "action_called": False})
    report["test_failures"] = sum(t["result"] == "FAIL" for t in report["tests"])
    if report["test_failures"]:
        report["overall"] = "FAIL_LOCAL_TESTS_AND_BLOCKED_G1"
    return report


def save_report(report):
    folder = new_directory(RECORDS, datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:12])
    write_json_new(folder / "report.json", report)
    lines = ["# G1 回收夹具能力核查", "", "结论：" + report["overall"], "",
             "真实回收调用：0；真实恢复调用：0。缺能力不能视为通过。", "",
             "## 阻塞", ""]
    lines += ["- " + reason for reason in report["blockers"]]
    lines += ["", "## 实测与模拟矩阵", "", "| 项目 | 类型 | 结果 | 说明 |", "|---|---|---|---|"]
    for t in report["tests"]:
        lines.append(f'| {t["test"]} | {t["mode"]} | {t["result"]} | {t["detail"]} |')
    for t in report["blocked_real_cases"]:
        lines.append(f'| {t["test"]} | {t["mode"]} | {t["result"]} | 未调用动作 |')
    lines += ["", "ACTUAL_LOCAL 只证明本地夹具/guard，不证明回收；SIMULATED 不证明 Windows 行为。",
              "没有安装依赖、改ACL/配额/全局设置、枚举私人物件、清理夹具或清空回收站。",
              "无G2生产执行器、无G3最终释放功能。原始API/注册表诊断见同目录report.json。", ""]
    with open(folder / "REPORT.md", "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="dryrun",
                        choices=["dryrun", "probe", "exercise", "inspect", "resume", "attempt-fixture"])
    parser.add_argument("--run-id", help="existing tool-created 32-character fixture id; no arbitrary source paths")
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            if not args.run_id:
                raise Blocked("RUN_ID_REQUIRED")
            print(json.dumps(inspect_run(args.run_id), ensure_ascii=False, allow_nan=False))
            return 0
        env = windows_probe()
        run_id = args.run_id
        if args.command == "exercise":
            if run_id:
                raise Blocked("EXERCISE_MUST_CREATE_FRESH_FIXTURES")
            run_id = create_fixtures()
        elif args.command in ("resume", "attempt-fixture"):
            if not run_id:
                raise Blocked("RUN_ID_REQUIRED")
            inspect_run(run_id)
        elif run_id:
            raise Blocked("RUN_ID_NOT_ACCEPTED_FOR_READONLY_PROBE")
        report = build_report(args.command, env, run_id)
        # Deliberately unconditional: no CLI argument/environment JSON enables actions.
        # A successful COM activation is not an action/undo/recovery capability test.
        folder = save_report(report)
        print(json.dumps({"overall": report["overall"], "report_directory": str(folder),
                          "run_id": run_id, "blockers": report["blockers"],
                          "test_failures": report["test_failures"],
                          "real_recycle_attempted": False}, ensure_ascii=False))
        return 1 if report["test_failures"] else 2  # 2 = capability BLOCKED, never success
    except (Blocked, OSError, ValueError, subprocess.SubprocessError) as exc:
        diagnostic = {"overall": "BLOCKED", "error": error_code(exc),
                      "reason": str(exc) if isinstance(exc, Blocked) else "FAIL_CLOSED_SEE_ERROR_CODE",
                      "real_recycle_attempted": False, "real_restore_attempted": False}
        folder = new_directory(RECORDS, "diagnostic_" + uuid.uuid4().hex)
        write_json_new(folder / "diagnostic.json", diagnostic)
        print(json.dumps({**diagnostic, "report_directory": str(folder)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
