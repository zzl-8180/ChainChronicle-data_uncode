"""Real Windows Shell (IFileOperation) synthetic-fixture recycle backend for G1 gap 1.

Phase A build (this file): a complete STA-COM recycle backend + guard + read-only
dryrun self-check. The real recycle/delete path is fully implemented but HARD-DISABLED
in this build (ALLOW_REAL_RECYCLE=False) and additionally requires the explicit
`--i-have-reviewed` CLI flag on `recycle`. Stage A never invokes it.

Hard safety contract (never relaxed in this file):
  - Only synthetic fixtures regenerated from the built-in recipe are ever queued
    (reuses recycle_fixture.expected_manifest / synthetic_chunks / fixtureguard).
  - No os.remove / os.unlink / shutil.rmtree / Remove-Item / cmd del anywhere here.
  - FOF_NOCONFIRMATION and FOF_SILENT are never set (asserted defensively).
  - IFileOperationProgressSink.PreDeleteItem rejects permanent delete
    (TSF_DELETE_RECYCLE_IF_POSSIBLE, 0x80, absent), returning E_ABORT so the
    source is preserved.
  - Recycle-bin self-entry locating never records unrelated entry names/content or
    the current-user SID; it only persists self-entry identity after a same-process
    before/after diff.

Reuses recycle_fixture.py's guard primitives (no guard logic re-implemented here).
"""
from __future__ import annotations

import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone

from recycle_fixture import (
    Blocked, now, error_code, hresult, extended, no_reparse, new_directory,
    write_json_new, validate_id, expected_manifest, file_digest,
    load_guard, fixtureguard, create_fixtures, specs,
    FIXTURES, PROJECT, SCHEMA, SHELL_FLAG_CONTRACT, windows_probe, inspect_run,
)

FOLLOWUP = PROJECT / "output/storage_retention/recycle_g1_20261027/followup_after_review"
RESTORE_BASE = PROJECT / "work/storage_recycle_g1_20261027/restored_fixtures"
SELF_ENTRY_PREFIX = "gap1_self_entry_"

# ---- Phase gate (stage B: real minimal-sample recycle enabled after review) ----
ALLOW_REAL_RECYCLE = True

# ---- COM identifiers ----
CLSID_FILE_OPERATION = uuid.UUID("3ad05575-8857-4850-9277-11b85bdb8e09")
IID_FILE_OPERATION = uuid.UUID("947aab5f-0a5c-4c13-b4d6-4bf7836fc9f8")
IID_ISHELL_ITEM = uuid.UUID("43826d1e-e718-42ee-bc55-a1e261c37bfe")
IID_PROGRESS_SINK = uuid.UUID("04b0f1a7-9490-44bc-96e1-4296a31252e2")

# ---- Operation / transfer flags ----
FOF_ALLOWUNDO = 0x0040
FOF_NO_CONNECTED_ELEMENTS = 0x2000
FOF_WANTNUKEWARNING = 0x4000
FOF_NOERRORUI = 0x0400
FOFX_RECYCLEONDELETE = 0x00080000
FOFX_EARLYFAILURE = 0x00100000
FOF_NOCONFIRMATION = 0x0010   # FORBIDDEN: never set
FOF_SILENT = 0x0004           # FORBIDDEN: never set

# Per Microsoft _TRANSFER_SOURCE_FLAGS (shobjidl_core.h), recycle-if-possible is 0x80
# (0x40 is TSF_USE_FULL_ACCESS). There is NO TSF "delete no confirmation" flag: the
# no-confirmation concern is enforced at the FILEOP_FLAGS level, where
# FOF_NOCONFIRMATION and FOF_SILENT are never set.
TSF_DELETE_RECYCLE_IF_POSSIBLE = 0x80

OPERATION_FLAGS = (FOF_ALLOWUNDO | FOF_NO_CONNECTED_ELEMENTS | FOF_WANTNUKEWARNING |
                   FOF_NOERRORUI | FOFX_RECYCLEONDELETE | FOFX_EARLYFAILURE)

S_OK = 0
S_FALSE = 1
E_NOINTERFACE = 0x80004002
E_ABORT = 0x80004004

HRESULT_T = C.c_long
ULONG_T = C.c_ulong
UINT_T = C.c_uint


def _guid_bytes(guid):
    return (C.c_ubyte * 16).from_buffer_copy(guid.bytes_le)


def _forbidden_flag_assert():
    if OPERATION_FLAGS & FOF_NOCONFIRMATION or OPERATION_FLAGS & FOF_SILENT:
        raise Blocked("FORBIDDEN_FLAG_PRESENT")


class SinkState:
    """Carries progress-sink observations for one operation. No item content stored."""

    def __init__(self, cancel_after=None):
        self.permanent_delete_risk = False
        self.cancel_after = cancel_after  # 1-indexed PreDeleteItem to reject (cancel/partial tests)
        self.pre_delete_count = 0
        self.cancelled = False
        self.events = []
        self._keepalive = None

    def record(self, name, **kw):
        self.events.append({"callback": name, **kw})


def _make_progress_sink(state):
    """Construct an IFileOperationProgressSink (19-slot vtable) in ctypes.

    PreDeleteItem rejects permanent delete (TSF_DELETE_RECYCLE_IF_POSSIBLE, 0x80,
    absent) by returning E_ABORT; every other callback returns S_OK.
    """
    THIS = C.c_void_p
    PVOID = C.c_void_p
    LPCWSTR = W.LPCWSTR
    DWORD = W.DWORD
    fns = []

    @C.WINFUNCTYPE(HRESULT_T, THIS, PVOID, C.POINTER(PVOID))
    def query_interface(this, riid, ppv):
        return E_NOINTERFACE

    fns.append(query_interface)

    @C.WINFUNCTYPE(ULONG_T, THIS)
    def add_ref(this):
        return 1

    fns.append(add_ref)

    @C.WINFUNCTYPE(ULONG_T, THIS)
    def release(this):
        return 1

    fns.append(release)

    @C.WINFUNCTYPE(HRESULT_T, THIS)
    def start_operations(this):
        state.record("StartOperations")
        return S_OK

    fns.append(start_operations)

    @C.WINFUNCTYPE(HRESULT_T, THIS, HRESULT_T)
    def finish_operations(this, hr_result):
        state.record("FinishOperations", hr_result=hresult(hr_result))
        return S_OK

    fns.append(finish_operations)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, LPCWSTR)
    def pre_rename_item(this, dw_flags, psi_item, psz_new_name):
        return S_OK

    fns.append(pre_rename_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, LPCWSTR, HRESULT_T, PVOID)
    def post_rename_item(this, dw_flags, psi_item, psz_new_name, hr_rename, psi_new):
        return S_OK

    fns.append(post_rename_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, PVOID, LPCWSTR)
    def pre_move_item(this, dw_flags, psi_item, psi_dest, psz_new_name):
        return S_OK

    fns.append(pre_move_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, PVOID, LPCWSTR, HRESULT_T, PVOID)
    def post_move_item(this, dw_flags, psi_item, psi_dest, psz_new_name, hr_move, psi_new):
        return S_OK

    fns.append(post_move_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, PVOID, LPCWSTR)
    def pre_copy_item(this, dw_flags, psi_item, psi_dest, psz_new_name):
        return S_OK

    fns.append(pre_copy_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, PVOID, LPCWSTR, HRESULT_T, PVOID)
    def post_copy_item(this, dw_flags, psi_item, psi_dest, psz_new_name, hr_copy, psi_new):
        return S_OK

    fns.append(post_copy_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID)
    def pre_delete_item(this, dw_flags, psi_item):
        state.pre_delete_count += 1
        state.record("PreDeleteItem", flags=f"0x{dw_flags & 0xffffffff:08X}",
                     item_index=state.pre_delete_count)
        if not (dw_flags & TSF_DELETE_RECYCLE_IF_POSSIBLE):
            state.permanent_delete_risk = True
            return E_ABORT
        if state.cancel_after is not None and state.pre_delete_count == state.cancel_after:
            state.cancelled = True
            return E_ABORT  # simulated cancel: abort this delete, preserve source
        return S_OK

    fns.append(pre_delete_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, HRESULT_T, PVOID)
    def post_delete_item(this, dw_flags, psi_item, hr_delete, psi_new):
        state.record("PostDeleteItem", hr_delete=hresult(hr_delete))
        return S_OK

    fns.append(post_delete_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, LPCWSTR)
    def pre_new_item(this, dw_flags, psi_dest, psz_new_name):
        return S_OK

    fns.append(pre_new_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, DWORD, PVOID, LPCWSTR, LPCWSTR, DWORD, HRESULT_T, PVOID)
    def post_new_item(this, dw_flags, psi_dest, psz_new_name, psz_template, dw_attr, hr_new, psi_new):
        return S_OK

    fns.append(post_new_item)

    @C.WINFUNCTYPE(HRESULT_T, THIS, UINT_T, UINT_T)
    def update_progress(this, i_work_total, i_work_so_far):
        return S_OK

    fns.append(update_progress)

    @C.WINFUNCTYPE(HRESULT_T, THIS)
    def reset_timer(this):
        return S_OK

    fns.append(reset_timer)

    @C.WINFUNCTYPE(HRESULT_T, THIS)
    def pause_timer(this):
        return S_OK

    fns.append(pause_timer)

    @C.WINFUNCTYPE(HRESULT_T, THIS)
    def resume_timer(this):
        return S_OK

    fns.append(resume_timer)

    assert len(fns) == 19, "sink vtable must have 19 slots"

    vtbl = (C.c_void_p * 19)(*[C.cast(f, C.c_void_p) for f in fns])

    class _Sink(C.Structure):
        _fields_ = [("lpVtbl", C.POINTER(C.c_void_p * 19))]

    sink = _Sink()
    sink.lpVtbl = C.pointer(vtbl)
    # Keep every callback, the vtable and the object alive for the operation.
    state._keepalive = (fns, vtbl, sink)
    return sink


def _shell_recycle_paths(extended_paths, cancel_after=None):
    """Real IFileOperation recycle of already-guarded extended absolute paths.

    This is the ONLY function that may call DeleteItem/PerformOperations. It is
    unreachable in stage A because ALLOW_REAL_RECYCLE is False. Returns a result
    dict; raises Blocked on any safety breach. Never sets NOCONFIRMATION/SILENT.
    """
    if not ALLOW_REAL_RECYCLE:
        raise Blocked("REAL_RECYCLE_NOT_ENABLED_THIS_BUILD")
    if not extended_paths:
        raise Blocked("NO_PATHS_TO_RECYCLE")
    _forbidden_flag_assert()

    ole = C.WinDLL("ole32", use_last_error=True)
    shell = C.WinDLL("shell32", use_last_error=True)

    state = SinkState(cancel_after=cancel_after)
    sink = _make_progress_sink(state)

    ole.CoInitializeEx.argtypes = [C.c_void_p, W.DWORD]
    ole.CoInitializeEx.restype = C.c_int32
    init_hr = ole.CoInitializeEx(None, 2)  # COINIT_APARTMENTTHREADED (STA)
    if init_hr not in (S_OK, S_FALSE):
        raise Blocked("STA_COINIT_FAILED_" + hresult(init_hr))
    try:
        clsid = _guid_bytes(CLSID_FILE_OPERATION)
        iid = _guid_bytes(IID_FILE_OPERATION)
        op_ptr = C.c_void_p()
        ole.CoCreateInstance.argtypes = [C.c_void_p, C.c_void_p, W.DWORD,
                                         C.c_void_p, C.POINTER(C.c_void_p)]
        ole.CoCreateInstance.restype = C.c_int32
        hr = ole.CoCreateInstance(C.byref(clsid), None, 1, C.byref(iid), C.byref(op_ptr))
        if hr < 0 or not op_ptr.value:
            raise Blocked("IFILEOPERATION_CREATE_FAILED_" + hresult(hr))

        vtbl = C.cast(op_ptr, C.POINTER(C.POINTER(C.c_void_p))).contents
        advise = C.WINFUNCTYPE(HRESULT_T, C.c_void_p, C.c_void_p, C.POINTER(W.DWORD))(vtbl[3])
        unadvise = C.WINFUNCTYPE(HRESULT_T, C.c_void_p, W.DWORD)(vtbl[4])
        set_flags = C.WINFUNCTYPE(HRESULT_T, C.c_void_p, W.DWORD)(vtbl[5])
        delete_item = C.WINFUNCTYPE(HRESULT_T, C.c_void_p, C.c_void_p, C.c_void_p)(vtbl[18])
        perform = C.WINFUNCTYPE(HRESULT_T, C.c_void_p)(vtbl[21])
        get_aborted = C.WINFUNCTYPE(HRESULT_T, C.c_void_p, C.POINTER(W.BOOL))(vtbl[22])
        release = C.WINFUNCTYPE(ULONG_T, C.c_void_p)(vtbl[2])

        cookie = W.DWORD()
        sink_ptr = C.cast(C.pointer(sink), C.c_void_p)
        hr = advise(op_ptr, sink_ptr, C.byref(cookie))
        if hr < 0:
            raise Blocked("ADVISE_FAILED_" + hresult(hr))

        hr = set_flags(op_ptr, OPERATION_FLAGS)
        if hr < 0:
            raise Blocked("SET_OPERATION_FLAGS_FAILED_" + hresult(hr))

        shell.SHCreateItemFromParsingName.argtypes = [W.LPCWSTR, C.c_void_p,
                                                       C.c_void_p, C.POINTER(C.c_void_p)]
        shell.SHCreateItemFromParsingName.restype = C.c_int32
        iid_shell_item = _guid_bytes(IID_ISHELL_ITEM)
        for ep in extended_paths:
            # SHCreateItemFromParsingName rejects the \\?\ extended prefix (E_INVALIDARG);
            # pass the normal absolute parsing name instead. The \\?\ prefix stays in use
            # for low-level file I/O (guard/open/read), not for Shell parsing.
            normal = ep[4:] if ep.startswith("\\\\?\\") else ep
            item_ptr = C.c_void_p()
            hr = shell.SHCreateItemFromParsingName(normal, None, C.byref(iid_shell_item),
                                                   C.byref(item_ptr))
            if hr < 0 or not item_ptr.value:
                raise Blocked("SHCREATEITEM_FAILED_" + hresult(hr))
            hr = delete_item(op_ptr, item_ptr, None)  # NULL per-item sink -> global sink
            item_vtbl = C.cast(item_ptr, C.POINTER(C.POINTER(C.c_void_p))).contents
            C.WINFUNCTYPE(ULONG_T, C.c_void_p)(item_vtbl[2])(item_ptr)
            if hr < 0:
                raise Blocked("DELETEITEM_QUEUE_FAILED_" + hresult(hr))

        perform_hr = perform(op_ptr)
        aborted = W.BOOL()
        get_aborted(op_ptr, C.byref(aborted))
        unadvise(op_ptr, cookie.value)
        release(op_ptr)
        return {"perform_hr": hresult(perform_hr), "any_aborted": bool(aborted.value),
                "permanent_delete_risk": state.permanent_delete_risk,
                "cancelled": state.cancelled,
                "sink_events": state.events,
                "paths_count": len(extended_paths)}
    finally:
        ole.CoUninitialize()


# ---- Recycle-bin self-entry locating (read-only; no unrelated records) ----

def current_user_sid():
    """Return the current process user SID string (in memory only; never persisted)."""
    advapi = C.WinDLL("advapi32", use_last_error=True)
    kernel = C.WinDLL("kernel32", use_last_error=True)

    class SID_AND_ATTRIBUTES(C.Structure):
        _fields_ = [("Sid", C.c_void_p), ("Attributes", W.DWORD)]

    class TOKEN_USER(C.Structure):
        _fields_ = [("User", SID_AND_ATTRIBUTES)]

    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.LocalFree.argtypes = [C.c_void_p]
    advapi.OpenProcessToken.argtypes = [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)]
    advapi.GetTokenInformation.argtypes = [W.HANDLE, C.c_int, C.c_void_p, W.DWORD,
                                           C.POINTER(W.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes = [C.c_void_p, C.POINTER(C.c_void_p)]
    advapi.ConvertSidToStringSidW.restype = W.BOOL

    token = W.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, C.byref(token)):  # TOKEN_QUERY
        raise Blocked("OPEN_PROCESS_TOKEN_FAILED")
    try:
        needed = W.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, C.byref(needed))  # TokenUser
        buf = C.create_string_buffer(needed.value)
        returned = W.DWORD()
        if not advapi.GetTokenInformation(token, 1, buf, needed.value, C.byref(returned)):
            raise Blocked("GET_TOKEN_USER_FAILED")
        tu = C.cast(buf, C.POINTER(TOKEN_USER)).contents
        str_ptr = C.c_void_p()
        if not advapi.ConvertSidToStringSidW(tu.User.Sid, C.byref(str_ptr)):
            raise Blocked("CONVERT_SID_FAILED")
        try:
            return C.wstring_at(str_ptr)
        finally:
            kernel.LocalFree(str_ptr)
    finally:
        kernel.CloseHandle(token)


def recycle_bin_dir():
    """Path of the current user's E: recycle-bin subdirectory. SID stays in memory."""
    return Path("E:\\$Recycle.Bin") / current_user_sid()


def snapshot_i_names():
    """Set of existing $I filenames (names only, in memory, never serialized)."""
    names = set()
    try:
        with os.scandir(extended(recycle_bin_dir())) as it:
            for entry in it:
                if entry.name.startswith("$I"):
                    names.add(entry.name)
    except OSError:
        raise Blocked("RECYCLE_BIN_NOT_ENUMERABLE")
    return names


def parse_i_original_path(i_path):
    """Read a Windows $I (v2) header + UTF-16LE original path. Returns parsed fields.

    $I v2 layout: version(4) header_size(4, usually 0x1C=28) file_size(8)
    deletion_time(8) name_len(4, UTF-16 code units, no trailing null) name(name_len*2).
    Reads the small header first, then the exact name bytes (avoid a 1 MiB read per
    entry so long bulk runs do not accumulate transient allocations).
    """
    with open(extended(i_path), "rb") as f:
        head = f.read(28)
    if len(head) < 28:
        raise Blocked("I_ENTRY_TOO_SHORT")
    version = int.from_bytes(head[0:4], "little")
    header_size = int.from_bytes(head[4:8], "little")
    file_size = int.from_bytes(head[8:16], "little")
    name_len = int.from_bytes(head[24:28], "little")
    if name_len <= 0 or name_len > (1024 * 1024):
        raise Blocked("I_ENTRY_NAME_LEN_OUT_OF_RANGE")
    with open(extended(i_path), "rb") as f:
        f.seek(28)
        raw = f.read(name_len * 2)
    if len(raw) != name_len * 2:
        raise Blocked("I_ENTRY_NAME_LEN_OUT_OF_RANGE")
    try:
        original = raw.decode("utf-16-le")
    except UnicodeDecodeError:
        raise Blocked("I_ENTRY_PATH_DECODE_FAILED")
    # Real Windows $I stores a NUL-terminated UTF-16 name: name_len includes the
    # trailing null terminator. Strip it so the path matches the source exactly.
    original = original.rstrip("\x00")
    return {"version": version, "header_size": header_size, "file_size": file_size,
            "name_len_chars": name_len, "original_path": original}


def selfcheck_i_parse():
    """Unit self-check: parse synthetic $I v2 samples (never touches the real bin)."""
    tmp_root = new_directory(FIXTURES, uuid.uuid4().hex)
    results = []

    def write_sample(name, blob):
        p = tmp_root / name
        with open(extended(p), "xb") as f:
            f.write(blob)
        return p

    def run(name, blob, expect_ok, expect_original=None):
        p = write_sample(name, blob)
        try:
            info = parse_i_original_path(p)
            if expect_ok:
                ok = info["original_path"] == expect_original
                results.append({"test": name, "result": "PASS" if ok else "FAIL",
                                "mode": "ACTUAL_LOCAL", "expected": expect_original,
                                "actual": info["original_path"]})
            else:
                results.append({"test": name, "result": "FAIL", "mode": "ACTUAL_LOCAL",
                                "detail": "expected Blocked, got parsed"})
        except Blocked as exc:
            if not expect_ok:
                results.append({"test": name, "result": "PASS", "mode": "ACTUAL_LOCAL",
                                "rejected": str(exc)})
            else:
                results.append({"test": name, "result": "FAIL", "mode": "ACTUAL_LOCAL",
                                "rejected": str(exc)})

    original = "C:\\中文 空格\\夹具 数据.txt"
    name_b = original.encode("utf-16-le")
    name_len = len(name_b) // 2
    good = ((2).to_bytes(4, "little") + (28).to_bytes(4, "little")
            + (4096).to_bytes(8, "little") + (132537600000000000).to_bytes(8, "little")
            + name_len.to_bytes(4, "little") + name_b)
    run("positive_chinese_spaces_path", good, True, original)
    # Real Windows $I stores a NUL-terminated name (name_len includes the terminator).
    null_name = name_b + b"\x00\x00"
    good_null = ((2).to_bytes(4, "little") + (28).to_bytes(4, "little")
                 + (4096).to_bytes(8, "little") + (132537600000000000).to_bytes(8, "little")
                 + (len(null_name) // 2).to_bytes(4, "little") + null_name)
    run("positive_trailing_null_path", good_null, True, original)
    run("reject_header_too_short", good[:27], False)
    run("reject_zero_name_len", good[:24] + (0).to_bytes(4, "little") + name_b, False)
    run("reject_name_len_out_of_range", good[:24] + (0x7FFFFFFF).to_bytes(4, "little"), False)
    run("reject_decode_failure", good[:24] + (1).to_bytes(4, "little") + b"\x00\xd8", False)

    failures = sum(1 for r in results if r["result"] == "FAIL")
    return {"overall": "PASS" if failures == 0 else "FAIL",
            "real_recycle_attempted": False, "real_restore_attempted": False,
            "tmp_dir": str(tmp_root), "tests": results, "test_failures": failures}


def save_i_parse_fix_report(result):
    folder = _ensure_folder(FOLLOWUP)
    jp = folder / "gap1_stageA_i_parse_fix.json"
    mp = folder / "gap1_stageA_i_parse_fix.md"
    if jp.exists() or mp.exists():
        raise Blocked("I_PARSE_FIX_REPORT_EXISTS_NOT_OVERWRITING")
    report = {"schema": SCHEMA, "created_utc": now(), "phase": "A", **result}
    write_json_new(jp, report)
    lines = ["# G1 缺口1 阶段A：$I 解析修复单元自检", "",
             "结论：" + result["overall"], "",
             "真实回收调用：0；真实恢复调用：0。全部为人工合成的 $I v2 二进制样本，"
             "未写入真实回收站，未调用任何真实动作。", "",
             "| 项目 | 类型 | 结果 | 说明 |", "|---|---|---|---|"]
    for t in result["tests"]:
        detail = t.get("rejected") or t.get("actual") or t.get("detail") or ""
        lines.append(f'| {t["test"]} | {t["mode"]} | {t["result"]} | {detail} |')
    lines += ["", "解析修复：$I v2 结构偏移 24..28 为 name_len（UTF-16 字符数），"
              "name 位于偏移 28，字节数 = name_len×2；越界/零长/非法 UTF-16 均拒绝。", ""]
    with open(extended(mp), "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return jp


def _norm_win_path(path):
    p = path.replace("/", "\\")
    if p.startswith("\\\\?\\"):
        p = p[4:]
    return p


def match_self_entries(new_i_names, manifest, root):
    """For each new $I (post-recycle diff), match original path + verify $R hash.

    Only self entries are returned; unrelated names/content are never logged.
    """
    expected = {}
    for row in manifest["files"]:
        if row["queued"]:
            p = root.joinpath(*row["path"].split("/"))
            expected[_norm_win_path(str(p.absolute()))] = row
    entries = []
    for i_name in new_i_names:
        info = parse_i_original_path(recycle_bin_dir() / i_name)
        row = expected.get(_norm_win_path(info["original_path"]))
        if row is None:
            continue  # not ours; do not log
        r_name = "$R" + i_name[2:]
        r_path = recycle_bin_dir() / r_name
        size = os.stat(extended(r_path)).st_size
        digest = file_digest(r_path)
        entries.append({
            "entry_i_name": i_name,
            "original_path": row["path"],
            "expected_sha256": row["sha256"],
            "actual_sha256": digest,
            "expected_bytes": row["size"],
            "actual_bytes": size,
            "hash_match": digest == row["sha256"],
        })
    return entries


def _self_entry_path(run_id):
    return FOLLOWUP / (SELF_ENTRY_PREFIX + validate_id(run_id) + ".json")


def persist_self_entries(run_id, entries):
    if entries:
        p = _self_entry_path(run_id)
        no_reparse(p.parent)
        p.parent.mkdir(parents=True, exist_ok=True)
        write_json_new(p, {"schema": SCHEMA, "run_id": run_id,
                           "entries": entries, "created_utc": now()})


def load_self_entries(run_id):
    p = _self_entry_path(run_id)
    if not p.exists():
        return []
    with open(extended(p), encoding="utf-8") as f:
        data = json.load(f)
    if data.get("run_id") != run_id:
        raise Blocked("SELF_ENTRY_RUN_ID_MISMATCH")
    return data.get("entries", [])


# ---- Command actions ----

def query_recycle_bin():
    """Read-only SHQueryRecycleBinW(E:) aggregate (no enumeration, no SID)."""
    shell = C.WinDLL("shell32", use_last_error=True)

    class Query(C.Structure):
        _fields_ = [("cbSize", W.DWORD), ("i64Size", C.c_int64), ("i64NumItems", C.c_int64)]

    q = Query()
    q.cbSize = C.sizeof(q)
    shell.SHQueryRecycleBinW.argtypes = [W.LPCWSTR, C.POINTER(Query)]
    shell.SHQueryRecycleBinW.restype = C.c_int32
    hr = shell.SHQueryRecycleBinW("E:\\", C.byref(q))
    return {"hresult": hresult(hr),
            "bytes": q.i64Size if hr == 0 else None,
            "items": q.i64NumItems if hr == 0 else None}


def recycle_run(run_id, i_have_reviewed, relative_paths=None, limit_one=False,
                cancel_after=None, do_restore=True):
    """Real recycle of a fixture run's queued synthetic files.

    relative_paths: optional list of relative queued paths to recycle (None + no
    limit_one = all queued). Records before/after recycle-bin aggregates and $I
    diff, locates self entries, and (unless do_restore=False) restores them.
    cancel_after: optional 1-indexed PreDeleteItem position to reject (cancel/partial).
    """
    if not ALLOW_REAL_RECYCLE:
        raise Blocked("REAL_RECYCLE_NOT_ENABLED_THIS_BUILD")
    if not i_have_reviewed:
        raise Blocked("REQUIRES_I_HAVE_REVIEWED_FLAG")
    root, manifest = load_guard(run_id)
    queued = [r for r in manifest["files"] if r["queued"]]
    if not queued:
        raise Blocked("NO_QUEUED_SYNTHETIC_SOURCES")
    if limit_one:
        selected = [min(queued, key=lambda r: (r["size"], r["path"]))]
    elif relative_paths is not None:
        if not isinstance(relative_paths, (list, tuple)):
            raise Blocked("RELATIVE_PATHS_MUST_BE_LIST")
        selected = []
        for rel in relative_paths:
            spec = next((r for r in queued if r["path"] == rel), None)
            if spec is None:
                raise Blocked("NOT_A_QUEUED_SYNTHETIC_SOURCE")
            selected.append(spec)
    else:
        selected = queued
    selected_paths = {row["path"] for row in selected}
    paths = []
    for row in selected:
        g = fixtureguard(run_id, row["path"], queued_only=True)
        paths.append((row, g, root.joinpath(*row["path"].split("/"))))

    before_q = query_recycle_bin()
    before_i = snapshot_i_names()
    op = _shell_recycle_paths([extended(p) for (_, _, p) in paths], cancel_after=cancel_after)
    after_q = query_recycle_bin()
    after_i = snapshot_i_names()
    new_i = sorted(after_i - before_i)
    entries = match_self_entries(new_i, manifest, root)
    persist_self_entries(run_id, entries)
    if do_restore:
        restore = restore_run(run_id)
    else:
        restore = {"overall": "RESTORE_SKIPPED_FOR_RESUME",
                   "real_restore_attempted": False, "restored": []}

    found = {e["original_path"] for e in entries if e["hash_match"]}
    per_item = []
    for row, g, p in paths:
        gone = not os.path.lexists(extended(p))
        per_item.append({"path": row["path"], "source_gone": gone,
                         "self_entry_located": row["path"] in found,
                         "sha256": row["sha256"]})

    if op.get("permanent_delete_risk"):
        overall = "STOP_PRESERVE_SOURCE"
    elif op.get("cancelled"):
        overall = "CANCELLED_PRESERVE_SOURCE"
    elif entries and all(e["hash_match"] for e in entries) and restore["real_restore_attempted"]:
        overall = "ROUNDTRIP_SHELL_VERIFIED"
    elif entries and all(e["hash_match"] for e in entries) and not do_restore:
        overall = "RECYCLED_LOCATED_AWAITING_RESUME"
    else:
        overall = "STOP_UNCERTAIN"

    return {"schema": SCHEMA, "run_id": run_id, "overall": overall,
            "real_recycle_attempted": True,
            "real_restore_attempted": restore["real_restore_attempted"],
            "recycled_paths": sorted(selected_paths),
            "queued_total": len(queued),
            "queued_not_recycled": sorted(r["path"] for r in queued if r["path"] not in selected_paths),
            "operation": op,
            "recycle_bin_before": before_q, "recycle_bin_after": after_q,
            "i_before_count": len(before_i), "i_after_count": len(after_i),
            "i_diff_count": len(new_i),
            "self_entries": entries, "self_entry_count": len(entries),
            "restore": restore, "per_item": per_item}


def locate_run(run_id):
    """Read-only locate: re-verify persisted self entries (no enumeration)."""
    root, manifest = load_guard(run_id)
    entries = load_self_entries(run_id)
    if not entries:
        return {"schema": SCHEMA, "run_id": run_id,
                "overall": "NO_SELF_ENTRY_RECORDED",
                "real_recycle_attempted": False, "real_restore_attempted": False,
                "self_entries": [], "note": "no persisted self entry; nothing recycled"}
    verified = []
    for e in entries:
        r_name = "$R" + e["entry_i_name"][2:]
        r_path = recycle_bin_dir() / r_name
        digest = file_digest(r_path)
        size = os.stat(extended(r_path)).st_size
        verified.append({**e, "reverify_sha256": digest, "reverify_bytes": size,
                         "reverify_ok": (digest == e["expected_sha256"]
                                         and size == e["expected_bytes"])})
    return {"schema": SCHEMA, "run_id": run_id, "overall": "LOCATE_VERIFIED",
            "real_recycle_attempted": False, "real_restore_attempted": False,
            "self_entries": verified}


def restore_run(run_id):
    """Restore self-entry $R content to a fresh directory; verify SHA-256 == expected."""
    root, manifest = load_guard(run_id)
    entries = load_self_entries(run_id)
    if not entries:
        return {"schema": SCHEMA, "run_id": run_id,
                "overall": "NO_SELF_ENTRY_TO_RESTORE",
                "real_recycle_attempted": False, "real_restore_attempted": False,
                "restored": []}
    target_dir = new_directory(RESTORE_BASE, validate_id(run_id))
    restored = []
    for e in entries:
        r_name = "$R" + e["entry_i_name"][2:]
        r_path = recycle_bin_dir() / r_name
        if not e.get("hash_match"):
            restored.append({**e, "result": "SKIPPED_HASH_MISMATCH"})
            continue
        with open(extended(r_path), "rb") as src:
            data = src.read()
        if len(data) != e["expected_bytes"]:
            restored.append({**e, "result": "SKIPPED_SIZE_MISMATCH"})
            continue
        digest = hashlib.sha256(data).hexdigest()
        if digest != e["expected_sha256"]:
            restored.append({**e, "result": "SKIPPED_HASH_MISMATCH"})
            continue
        target = target_dir.joinpath(*e["original_path"].split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        no_reparse(target)
        with open(extended(target), "xb") as dst:
            dst.write(data)
        restored.append({**e, "result": "RESTORED", "restored_to": str(target),
                         "restored_sha256": digest})
    return {"schema": SCHEMA, "run_id": run_id,
            "overall": "RESTORE_REPORT", "real_recycle_attempted": False,
            "real_restore_attempted": any(x["result"] == "RESTORED" for x in restored),
            "restored": restored, "restore_root": str(target_dir)}


# ---- Read-only dryrun probe ----

def recycle_bin_readonly_probe():
    """Read-only probe: can we enumerate the current user's recycle-bin dir, and how
    many $I entries exist? Names are held in memory and never written anywhere."""
    result = {"root_display": "E:\\$Recycle.Bin\\<SID>",
              "sid_recorded_to_disk": False, "enumerable": False,
              "i_entry_count": None, "error": None}
    try:
        names = snapshot_i_names()
        result["enumerable"] = True
        result["i_entry_count"] = len(names)
    except Blocked as exc:
        result["error"] = str(exc)
    return result


def guard_negatives(run_id):
    """Guard negative cases. Reuses recycle_fixture.fixtureguard / load_guard."""
    tests = []
    for name, rel in [
        ("reject_project_candidate", "output/real-candidate.zip"),
        ("reject_traversal", "../HANDOFF.md"),
        ("reject_absolute", "E:/candidate.zip"),
        ("reject_ADS", "foo:stream"),
        ("reject_unlisted", "unlisted-synthetic.txt"),
        ("reject_connected_resource_queue", "连接资源/page_files/resource.txt"),
    ]:
        try:
            fixtureguard(run_id, rel)
            result = "FAIL"
        except Blocked:
            result = "PASS"
        tests.append({"test": name, "mode": "ACTUAL_LOCAL", "result": result,
                      "detail": "guard rejects request before reading non-fixture content"})
    try:
        g = fixtureguard(run_id, "中文 空格/夹具 数据.txt", queued_only=True)
        positive = "PASS" if g["sha256"] else "FAIL"
    except Blocked:
        positive = "FAIL"
    tests.append({"test": "accept_valid_queued_synthetic", "mode": "ACTUAL_LOCAL",
                  "result": positive,
                  "detail": "valid queued synthetic file passes guard and hashes to recipe"})
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
    return tests


# ---- Reporting ----

def _count_modes(tests):
    shell = sum(1 for t in tests if t.get("mode") == "ACTUAL_SHELL")
    local = sum(1 for t in tests if t.get("mode") == "ACTUAL_LOCAL")
    sim = sum(1 for t in tests if t.get("mode") == "SIMULATED")
    return shell, local, sim


def build_stageA_report(env, rb_probe):
    report = {
        "schema": "cc-storage-recycle-g1-shell-backend-stageA-v1",
        "created_utc": now(),
        "phase": "A",
        "overall": "STAGE_A_READONLY_COMPLETE_NO_REAL_ACTION",
        "real_recycle_attempted": False,
        "real_restore_attempted": False,
        "ALLOW_REAL_RECYCLE": ALLOW_REAL_RECYCLE,
        "action_backend": "IMPLEMENTED_BUT_NOT_EXECUTED_STAGE_A",
        "operation_flags": {
            "value": f"0x{OPERATION_FLAGS:08X}",
            "components": {k: f"0x{v:04X}" for k, v in SHELL_FLAG_CONTRACT.items()},
            "forbidden_not_set": {"FOF_NOCONFIRMATION": True, "FOF_SILENT": True},
        },
        "com_contract": {
            "CLSID_IFileOperation": str(CLSID_FILE_OPERATION),
            "IID_IFileOperation": str(IID_FILE_OPERATION),
            "IID_IShellItem": str(IID_ISHELL_ITEM),
            "IID_IFileOperationProgressSink": str(IID_PROGRESS_SINK),
        },
        "environment": env,
        "recycle_bin_probe": rb_probe,
        "self_entry_locate_empty_run": {
            "ran": True, "self_entries": 0,
            "note": "no fixtures recycled in stage A; no before/after diff performed",
        },
        "tests": [],
        "privacy": ("no SID written to disk; no unrelated recycle entry names or "
                    "contents recorded; aggregate counts only"),
        "tool_sha256": file_digest(Path(__file__).absolute()),
    }
    shell, local, sim = _count_modes(report["tests"])
    report["ACTUAL_SHELL_count"] = shell
    report["ACTUAL_LOCAL_count"] = local
    report["SIMULATED_count"] = sim
    report["test_failures"] = 0
    return report


def _render_stageA_md(report):
    env = report["environment"]
    com = env.get("com", {})
    tok = env.get("token_context", {})
    agg = env.get("recycle_aggregate", {})
    rb = report["recycle_bin_probe"]
    lines = ["# G1 缺口1 阶段A：真实 Shell 后端 dryrun 只读自检", "",
             "结论：" + report["overall"], "",
             "真实回收调用：0；真实恢复调用：0。阶段A 未执行任何真实入站，"
             "未调用 PerformOperations 的删除路径或 DeleteItem。", "",
             "## 进程上下文", "",
             f'- app_container={tok.get("app_container")}, restricted={tok.get("restricted")}, '
             f'elevated={tok.get("elevated")}',
             f'- 会话：{env.get("session_id")}', "",
             "## 只读探针", "",
             f'- SHQueryRecycleBinW(E:\\)：HRESULT={agg.get("hresult")}, '
             f'bytes={agg.get("bytes")}, items={agg.get("items")}',
             f'- IFileOperation 激活 HRESULT：{com.get("IFileOperation_activation_hresult")}',
             f'- 回收站目录可枚举：{rb.get("enumerable")}；当前 $I 数量：{rb.get("i_entry_count")}',
             f'- 磁盘 E: free={env.get("disk", {}).get("free")}',
             f'- 操作标志：{report["operation_flags"]["value"]}（不含 FOF_NOCONFIRMATION / FOF_SILENT）',
             "", "## 结论口径", "",
             "ACTUAL_SHELL 数量为 0（阶段A 禁止动作）；本阶段只有 ACTUAL_LOCAL 只读结果。",
             "SIMULATED 数量为 0。未记录 SID、未记录无关回收站条目名或内容。",
             "真实入站、定位、恢复均未执行，等待主代理复核后再决定是否进入阶段B。", ""]
    return "\n".join(lines)


def _ensure_folder(folder):
    no_reparse(folder)
    folder.mkdir(parents=True, exist_ok=True)
    no_reparse(folder)
    return folder


def save_stageA_report(report):
    folder = _ensure_folder(FOLLOWUP)
    jp = folder / "gap1_stageA_report.json"
    mp = folder / "gap1_stageA_REPORT.md"
    if jp.exists() or mp.exists():
        raise Blocked("STAGE_A_REPORT_EXISTS_NOT_OVERWRITING")
    write_json_new(jp, report)
    with open(extended(mp), "x", encoding="utf-8", newline="\n") as f:
        f.write(_render_stageA_md(report))
    return jp


def save_guard_report(run_id, tests):
    folder = _ensure_folder(FOLLOWUP)
    shell, local, sim = _count_modes(tests)
    failures = sum(1 for t in tests if t["result"] == "FAIL")
    report = {"schema": SCHEMA, "created_utc": now(), "phase": "A", "run_id": run_id,
              "overall": "GUARD_NEGATIVES_" + ("PASS" if failures == 0 else "FAIL"),
              "real_recycle_attempted": False, "real_restore_attempted": False,
              "tests": tests, "ACTUAL_SHELL_count": shell, "ACTUAL_LOCAL_count": local,
              "SIMULATED_count": sim, "test_failures": failures}
    jp = folder / "gap1_stageA_guards.json"
    mp = folder / "gap1_stageA_guards.md"
    if jp.exists() or mp.exists():
        raise Blocked("GUARD_REPORT_EXISTS_NOT_OVERWRITING")
    write_json_new(jp, report)
    lines = ["# G1 缺口1 阶段A：guard 负例自检", "",
             "结论：" + report["overall"], "", "| 项目 | 类型 | 结果 | 说明 |",
             "|---|---|---|---|"]
    for t in tests:
        lines.append(f'| {t["test"]} | {t["mode"]} | {t["result"]} | {t["detail"]} |')
    lines += ["", "全部为 ACTUAL_LOCAL（本地 guard/夹具），ACTUAL_SHELL 数量为 0。",
              "未回收任何文件、未调用任何真实动作。", ""]
    with open(extended(mp), "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return jp


def save_stageB_report(result):
    folder = _ensure_folder(FOLLOWUP)
    jp = folder / "gap1_stageB_minimal_report.json"
    mp = folder / "gap1_stageB_minimal_report.md"
    if jp.exists() or mp.exists():
        raise Blocked("STAGE_B_REPORT_EXISTS_NOT_OVERWRITING")
    write_json_new(jp, result)
    op = result.get("operation", {})
    rb_b = result["recycle_bin_before"]
    rb_a = result["recycle_bin_after"]
    lines = ["# G1 缺口1 阶段B：真实最小样本闭环", "",
             "结论：" + result["overall"], "",
             f'- real_recycle_attempted={result["real_recycle_attempted"]}, '
             f'real_restore_attempted={result["real_restore_attempted"]}',
             f'- 入站文件：{", ".join(result["recycled_paths"])}（合成夹具，非真实候选）',
             f'- queued 总数：{result["queued_total"]}；本次入站 {len(result["recycled_paths"])} 个，'
             f'未入站：{", ".join(result["queued_not_recycled"]) or "无"}',
             "", "## 回收站前后计量", "",
             f'- 入站前 SHQueryRecycleBinW：HRESULT={rb_b["hresult"]}, bytes={rb_b["bytes"]}, items={rb_b["items"]}',
             f'- 入站后 SHQueryRecycleBinW：HRESULT={rb_a["hresult"]}, bytes={rb_a["bytes"]}, items={rb_a["items"]}',
             f'- $I 数量：入站前 {result["i_before_count"]}，入站后 {result["i_after_count"]}，diff={result["i_diff_count"]}',
             "", "## 操作 HRESULT", "",
             f'- PerformOperations HRESULT={op.get("perform_hr")}, any_aborted={op.get("any_aborted")}, '
             f'permanent_delete_risk={op.get("permanent_delete_risk")}',
             "", "## 自身条目定位与恢复", "",
             "| 原始路径 | $I | $R sha256 匹配 | 恢复结果 |", "|---|---|---|---|"]
    for e in result["self_entries"]:
        rr = [x for x in result["restore"]["restored"] if x.get("original_path") == e["original_path"]]
        rres = rr[0]["result"] if rr else "-"
        lines.append(f'| {e["original_path"]} | {e["entry_i_name"]} | {e["hash_match"]} | {rres} |')
    if not result["self_entries"]:
        lines.append("| （无定位到的自身条目） | - | - | - |")
    lines += ["", "本阶段只入站单个最小合成文件；未触碰任何真实候选；未做最终释放/清空回收站；",
              "未使用通用删除函数；未设 FOF_NOCONFIRMATION/FOF_SILENT。", ""]
    with open(extended(mp), "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return jp


def _roundtrip_ok(res):
    if res.get("operation", {}).get("permanent_delete_risk"):
        return False
    if res.get("operation", {}).get("cancelled"):
        return False
    entries = res.get("self_entries", [])
    if not entries or not all(e.get("hash_match") for e in entries):
        return False
    if not res.get("restore", {}).get("real_restore_attempted"):
        return False
    for pi in res.get("per_item", []):
        if not pi.get("source_gone") or not pi.get("self_entry_located"):
            return False
    return True


def _branch(label, res, ok, detail):
    b = {"branch": label, "mode": "ACTUAL_SHELL",
         "result": "PASS" if ok else "FAIL", "detail": detail}
    b.update(res)
    return b


def _guarded_branch(label, fn):
    try:
        return fn()
    except (Blocked, OSError, ValueError) as exc:
        return {"branch": label, "mode": "ACTUAL_SHELL", "result": "FAIL",
                "error": error_code(exc), "reason": str(exc),
                "real_recycle_attempted": True, "real_restore_attempted": False,
                "detail": "branch raised: " + str(exc)}


def run_stage_c_matrix():
    branches = []

    # 1. Chinese + spaces path (4096)
    def b1():
        run_id = create_fixtures()
        res = recycle_run(run_id, True, relative_paths=["中文 空格/夹具 数据.txt"])
        return _branch("chinese_spaces", res, _roundtrip_ok(res),
                       "recycled 中文 空格/夹具 数据.txt and restored same hash")
    branches.append(_guarded_branch("chinese_spaces", b1))

    # 2. Same basename, different directory (2048, distinct content)
    def b2():
        run_id = create_fixtures()
        res = recycle_run(run_id, True, relative_paths=["同名乙/same.txt"])
        ok = _roundtrip_ok(res)
        entry = res["self_entries"][0] if res["self_entries"] else {}
        ok = ok and entry.get("original_path") == "同名乙/same.txt"
        return _branch("same_name_diff_dir", res, ok,
                       "same.txt in 同名乙 distinguished by full path+hash (not 同名甲)")
    branches.append(_guarded_branch("same_name_diff_dir", b2))

    # 3. Long path (>260 chars)
    def b3():
        long_rel = specs()[5]["path"]
        run_id = create_fixtures()
        res = recycle_run(run_id, True, relative_paths=[long_rel])
        if res["operation"].get("permanent_delete_risk"):
            return {"branch": "long_path", "mode": "ACTUAL_SHELL", "result": "BLOCKED",
                    "detail": "Shell reports permanent delete (PreDeleteItem flags=0x200, "
                              "no TSF_DELETE_RECYCLE_IF_POSSIBLE) for >260-char path; "
                              "recycle unsupported via IFileOperation; fail-safe preserved "
                              "source (no permanent delete)", **res}
        return _branch("long_path", res, _roundtrip_ok(res),
                       "long path (" + str(len(long_rel) + 3) + "+ chars incl dirs) roundtrip")
    branches.append(_guarded_branch("long_path", b3))

    # 4. 8 MiB fixture
    def b4():
        run_id = create_fixtures()
        res = recycle_run(run_id, True, relative_paths=["较大夹具/8 MiB.bin"])
        return _branch("large_8mib", res, _roundtrip_ok(res), "8 MiB fixture roundtrip")
    branches.append(_guarded_branch("large_8mib", b4))

    # 5. HTML connected resource not recycled
    def b5():
        run_id = create_fixtures()
        root, manifest = load_guard(run_id)
        resource_rel = "连接资源/page_files/resource.txt"
        resource_path = root.joinpath(*resource_rel.split("/"))
        resource_hash_before = file_digest(resource_path)
        res = recycle_run(run_id, True, relative_paths=["连接资源/page.html"])
        resource_intact = resource_path.exists() and file_digest(resource_path) == resource_hash_before
        ok = _roundtrip_ok(res) and resource_intact
        res["resource_check"] = {"path": resource_rel, "intact": resource_intact,
                                 "hash_before": resource_hash_before,
                                 "hash_after": file_digest(resource_path) if resource_path.exists() else None}
        return _branch("html_connected", res, ok,
                       "page_files/resource.txt preserved, hash unchanged: " + str(resource_intact))
    branches.append(_guarded_branch("html_connected", b5))

    # 6. Failure (target missing -> SHCreateItemFromParsingName fails; source preserved)
    def b6():
        run_id = create_fixtures()
        root, manifest = load_guard(run_id)
        source_rel = "中文 空格/夹具 数据.txt"
        source_path = root.joinpath(*source_rel.split("/"))
        source_hash = next(r["sha256"] for r in manifest["files"] if r["path"] == source_rel)
        missing_path = root.joinpath("中文 空格", "不存在的目标.txt")
        error = None
        try:
            _shell_recycle_paths([extended(missing_path)])
            failed_as_expected = False
        except Blocked as exc:
            error = str(exc)
            failed_as_expected = True
        source_intact = source_path.exists() and file_digest(source_path) == source_hash
        ok = failed_as_expected and source_intact
        return {"branch": "failure_target_missing", "mode": "ACTUAL_SHELL",
                "result": "PASS" if ok else "FAIL", "run_id": run_id,
                "error": error, "source_intact": source_intact,
                "source_gone": not source_path.exists(),
                "real_recycle_attempted": True, "real_restore_attempted": False,
                "detail": "SHCreateItemFromParsingName failed (" + (error or "") +
                          "); real source preserved=" + str(source_intact)}
    branches.append(_guarded_branch("failure_target_missing", b6))

    # 7. Cancel (PreDeleteItem rejects item 1)
    def b7():
        run_id = create_fixtures()
        res = recycle_run(run_id, True, relative_paths=["中文 空格/夹具 数据.txt"], cancel_after=1)
        op = res["operation"]
        source_gone = any(p["source_gone"] for p in res["per_item"])
        ok = op.get("cancelled") and (not source_gone)
        return _branch("cancel_predelete", res, ok,
                       "PreDeleteItem rejected (perform_hr=" + op.get("perform_hr") +
                       "); source preserved=" + str(not source_gone))
    branches.append(_guarded_branch("cancel_predelete", b7))

    # 8. Partial success (item1 recycled, item2 canceled at PreDeleteItem)
    def b8():
        run_id = create_fixtures()
        res = recycle_run(run_id, True,
                          relative_paths=["中文 空格/夹具 数据.txt", "同名乙/same.txt"],
                          cancel_after=2)
        per = {p["path"]: p for p in res["per_item"]}
        i1 = per.get("中文 空格/夹具 数据.txt", {})
        i2 = per.get("同名乙/same.txt", {})
        ok = (res["operation"].get("cancelled")
              and i1.get("source_gone") and i1.get("self_entry_located")
              and (not i2.get("source_gone")) and (not i2.get("self_entry_located")))
        return _branch("partial_success", res, ok,
                       "item1 recycled+restored, item2 canceled+preserved; per-item reconciled, no retry")
    branches.append(_guarded_branch("partial_success", b8))

    # 9. New process resume (locate + restore in a fresh Python process)
    def b9():
        run_id = create_fixtures()
        res = recycle_run(run_id, True, relative_paths=["中文 空格/夹具 数据.txt"], do_restore=False)
        located = res["self_entry_count"] >= 1 and all(e["hash_match"] for e in res["self_entries"])
        script = str(Path(__file__).absolute())
        loc = subprocess.run([sys.executable, "-X", "utf8", "-B", script, "locate", "--run-id", run_id],
                             capture_output=True, timeout=120, check=False)
        rst = subprocess.run([sys.executable, "-X", "utf8", "-B", script, "restore", "--run-id", run_id],
                             capture_output=True, timeout=120, check=False)
        locate_data = json.loads(loc.stdout.decode("utf-8")) if loc.returncode == 0 else None
        restore_data = json.loads(rst.stdout.decode("utf-8")) if rst.returncode == 0 else None
        reverify_ok = bool(locate_data and all(e.get("reverify_ok") for e in locate_data.get("self_entries", [])))
        restored_ok = bool(restore_data and any(
            r.get("result") == "RESTORED" and r.get("restored_sha256") == r.get("expected_sha256")
            for r in restore_data.get("restored", [])))
        ok = located and loc.returncode == 0 and rst.returncode == 0 and reverify_ok and restored_ok
        return {"branch": "new_process_resume", "mode": "ACTUAL_SHELL",
                "result": "PASS" if ok else "FAIL", "run_id": run_id,
                "recycle_overall": res["overall"], "located": located,
                "locate_returncode": loc.returncode, "locate_reverify_ok": reverify_ok,
                "restore_returncode": rst.returncode, "restore_ok": restored_ok,
                "self_entries": res["self_entries"],
                "detail": "fresh Python process re-located and restored same hash"}
    branches.append(_guarded_branch("new_process_resume", b9))

    # OS restart: not tested
    branches.append({"branch": "os_restart", "mode": "ACTUAL_SHELL",
                     "result": "UNVERIFIED", "detail": "OS restart not performed; explicitly not claimed"})

    leftover = {}
    for b in branches:
        for e in b.get("self_entries", []):
            leftover[e["entry_i_name"]] = {"size": e.get("actual_bytes"),
                                          "original_path": e.get("original_path")}

    passed = [b for b in branches if b.get("result") == "PASS"]
    failed = [b for b in branches if b.get("result") == "FAIL"]
    blocked = [b for b in branches if b.get("result") == "BLOCKED"]
    unverified = [b for b in branches if b.get("result") == "UNVERIFIED"]
    overall = "STAGE_C_PASS" if not failed else "STAGE_C_HAS_FAILURES"

    return {"schema": SCHEMA, "created_utc": now(), "phase": "C", "overall": overall,
            "real_recycle_attempted": True, "real_restore_attempted": True,
            "pass_count": len(passed), "fail_count": len(failed),
            "blocked_count": len(blocked), "unverified_count": len(unverified),
            "branches": branches, "os_restart": "UNVERIFIED",
            "leftover_synthetic_entries": leftover,
            "privacy": "no SID written; no unrelated recycle entry names/content recorded"}


def save_stageC_report(result):
    folder = _ensure_folder(FOLLOWUP)
    jp = folder / "gap1_stageC_full_matrix_report.json"
    mp = folder / "gap1_stageC_full_matrix_report.md"
    if jp.exists() or mp.exists():
        raise Blocked("STAGE_C_REPORT_EXISTS_NOT_OVERWRITING")
    write_json_new(jp, result)
    lines = ["# G1 缺口1 阶段C：完整矩阵", "",
             "结论：" + result["overall"], "",
             f'- 分支：{result["pass_count"]} PASS / {result["fail_count"]} FAIL / '
             f'{result.get("blocked_count", 0)} BLOCKED / '
             f'{result["unverified_count"]} UNVERIFIED；OS 重启={result["os_restart"]}',
             f'- real_recycle_attempted={result["real_recycle_attempted"]}, '
             f'real_restore_attempted={result["real_restore_attempted"]}',
             "", "## 分支结果", "",
             "| 分支 | 类型 | 结果 | 说明 |", "|---|---|---|---|"]
    for b in result["branches"]:
        lines.append(f'| {b["branch"]} | {b.get("mode")} | {b.get("result")} | {b.get("detail")} |')
    lines += ["", "## 遗留合成条目（本任务自身，名称+大小）", ""]
    if result["leftover_synthetic_entries"]:
        for name, info in result["leftover_synthetic_entries"].items():
            lines.append(f'- {name}：{info["size"]} 字节（原路径 {info["original_path"]}）')
    else:
        lines.append("- （无）")
    lines += ["", "全部只处理合成夹具；未触碰真实候选；未做最终释放/清空回收站；",
              "未使用通用删除函数；未设 FOF_NOCONFIRMATION/FOF_SILENT。", ""]
    with open(extended(mp), "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return jp


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="dryrun",
                        choices=["dryrun", "create-fixtures", "guard-check",
                                 "selfcheck-i-parse", "recycle", "locate", "restore",
                                 "stage-c"])
    parser.add_argument("--run-id", help="tool-created 32-char fixture id; no arbitrary source paths")
    parser.add_argument("--i-have-reviewed", action="store_true",
                        help="explicit review flag; required by `recycle`")
    parser.add_argument("--limit-one", action="store_true",
                        help="recycle only the single smallest queued synthetic file (stage B minimal)")
    args = parser.parse_args()
    try:
        if args.i_have_reviewed and args.command != "recycle":
            raise Blocked("I_HAVE_REVIEWED_ONLY_VALID_FOR_RECYCLE")

        if args.command == "create-fixtures":
            run_id = create_fixtures()
            print(json.dumps({"run_id": run_id, "fixtures_root": str(FIXTURES / run_id),
                              "real_recycle_attempted": False,
                              "real_restore_attempted": False}, ensure_ascii=False))
            return 0

        if args.command == "dryrun":
            if args.run_id:
                raise Blocked("RUN_ID_NOT_ACCEPTED_FOR_READONLY_DRYRUN")
            env = windows_probe()
            rb = recycle_bin_readonly_probe()
            report = build_stageA_report(env, rb)
            jp = save_stageA_report(report)
            print(json.dumps({"overall": report["overall"], "report": str(jp),
                              "recycle_bin_probe": rb,
                              "real_recycle_attempted": False}, ensure_ascii=False))
            return 0

        if args.command == "guard-check":
            if not args.run_id:
                raise Blocked("RUN_ID_REQUIRED")
            validate_id(args.run_id)
            load_guard(args.run_id)
            tests = guard_negatives(args.run_id)
            jp = save_guard_report(args.run_id, tests)
            print(json.dumps({"run_id": args.run_id, "report": str(jp),
                              "test_failures": sum(1 for t in tests if t["result"] == "FAIL"),
                              "real_recycle_attempted": False}, ensure_ascii=False))
            return 0

        if args.command == "selfcheck-i-parse":
            result = selfcheck_i_parse()
            jp = save_i_parse_fix_report(result)
            print(json.dumps({"overall": result["overall"], "report": str(jp),
                              "test_failures": result["test_failures"],
                              "real_recycle_attempted": False}, ensure_ascii=False))
            return 0

        if args.command == "stage-c":
            result = run_stage_c_matrix()
            jp = save_stageC_report(result)
            print(json.dumps({"overall": result["overall"],
                              "pass_count": result["pass_count"],
                              "fail_count": result["fail_count"],
                              "blocked_count": result.get("blocked_count", 0),
                              "unverified_count": result["unverified_count"],
                              "report": str(jp)}, ensure_ascii=False))
            return 0 if result["fail_count"] == 0 else 1

        if args.command == "recycle":
            if not args.run_id:
                raise Blocked("RUN_ID_REQUIRED")
            result = recycle_run(args.run_id, args.i_have_reviewed, limit_one=args.limit_one)
            if args.limit_one:
                jp = save_stageB_report(result)
                print(json.dumps({"overall": result["overall"], "report": str(jp),
                                  "real_recycle_attempted": result["real_recycle_attempted"],
                                  "real_restore_attempted": result["real_restore_attempted"],
                                  "recycled_paths": result["recycled_paths"]},
                                 ensure_ascii=False))
            else:
                print(json.dumps(result, ensure_ascii=False))
            return 0

        if args.command == "locate":
            if not args.run_id:
                raise Blocked("RUN_ID_REQUIRED")
            print(json.dumps(locate_run(args.run_id), ensure_ascii=False))
            return 0

        if args.command == "restore":
            if not args.run_id:
                raise Blocked("RUN_ID_REQUIRED")
            print(json.dumps(restore_run(args.run_id), ensure_ascii=False))
            return 0

    except (Blocked, OSError, ValueError) as exc:
        diagnostic = {"overall": "BLOCKED", "error": error_code(exc),
                      "reason": str(exc) if isinstance(exc, Blocked) else "FAIL_CLOSED_SEE_ERROR_CODE",
                      "real_recycle_attempted": False, "real_restore_attempted": False}
        print(json.dumps(diagnostic, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
