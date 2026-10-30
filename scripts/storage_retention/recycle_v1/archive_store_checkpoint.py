"""G1 archive/verify/restore only. Never removes, renames or overwrites files.

Source events are flushed for visibility, but are NOT durable completion markers.
Checkpoint fsync runs after 256 completed sources or 1 second, at source boundaries.
A slow single source can exceed that interval. Without a final PASS build report
the entire vault remains unqualified. Final full sync and 100% readback are required.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import ctypes
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import time
import uuid
import zipfile

CHUNK = 1024 * 1024
GIB = 1024 ** 3
VOLUME_TARGET = 512 * 1024 ** 2
VOLUME_HARD = 640 * 1024 ** 2
DIAGNOSTIC_RESERVE = 64 * 1024
FORMAT = "g1-archive-v1"
CHECKPOINT_SOURCES = 256
CHECKPOINT_SECONDS = 1.0
REPARSE = 0x400
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
VOLUME_RE = re.compile(r"volume-[0-9]{6}\.zip\Z")
A_PATH_RE = re.compile(
    r"output/character_skills/pages/_batch/(?:ge60|40to59|20to39|remaining)/runs/"
    r"[0-9]{8}T[0-9]{12}Z-[0-9a-f]{8}/transactions/[0-9]+/backup/(?:card\.json|index\.html)\Z")
RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?\Z", re.I)


class ArchiveError(Exception):
    pass


def relpath(value):
    """Deliberately use Windows-safe POSIX names even when running on Linux."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise ArchiveError(f"invalid relative POSIX path: {value!r}")
    parts = value.split("/")
    if any(p in ("", ".", "..") or p[-1:] in (" ", ".") or
           RESERVED.fullmatch(p) or any(ord(c) < 32 or c in '<>:"|?*' for c in p)
           for p in parts):
        raise ArchiveError(f"unsafe path: {value!r}")
    return value


def check_stat(s, *, directory=False):
    if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & REPARSE:
        raise ArchiveError("reparse/symlink is forbidden")
    if directory:
        if not stat.S_ISDIR(s.st_mode):
            raise ArchiveError("expected ordinary directory")
    elif not stat.S_ISREG(s.st_mode):
        raise ArchiveError("expected ordinary file")
    elif s.st_nlink != 1:
        raise ArchiveError(f"hardlink HOLD: nlink={s.st_nlink}; no physical-release estimate")


def checked_path(path, *, directory=False, missing=False):
    """lstat every component, including ancestors of the supplied root."""
    p = Path(os.path.abspath(path))
    chain = list(reversed(p.parents)) + [p]
    for n, part in enumerate(chain):
        try:
            s = part.lstat()
        except FileNotFoundError:
            if missing and n == len(chain) - 1:
                return p
            raise
        check_stat(s, directory=n < len(chain) - 1 or directory)
    return p


@contextlib.contextmanager
def locked_parents(path):
    """On Windows keep ancestors from being renamed/replaced during file I/O."""
    handles = []
    if os.name != "nt":
        yield
        return
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    create = k.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    info = k.GetFileInformationByHandleEx
    info.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    info.restype = wintypes.BOOL
    close = k.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    try:
        for parent in reversed(Path(os.path.abspath(path)).parents):
            # READ_ATTRIBUTES; share READ|WRITE, deliberately deny DELETE.
            h = create(str(parent), 0x80, 3, None, 3, 0x02200000, None)
            if h == ctypes.c_void_p(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            handles.append(h)
            attrs = (wintypes.DWORD * 2)()
            if not info(h, 9, ctypes.byref(attrs), ctypes.sizeof(attrs)):
                raise ctypes.WinError(ctypes.get_last_error())
            if attrs[0] & REPARSE or not attrs[0] & 0x10:
                raise ArchiveError("reparse/non-directory ancestor is forbidden")
        yield
    finally:
        for h in reversed(handles):
            close(h)


def new_directory(path):
    with locked_parents(path):
        checked_path(path, missing=True)
        path.mkdir()


def under(root, name):
    relpath(name)
    return root.joinpath(*name.split("/"))


def identity(s):
    # CPython on Windows may expose creation time in stat().st_ctime but
    # last-change time in fstat().st_ctime. birthtime is consistent there.
    change_time = getattr(s, "st_birthtime_ns", None) if os.name == "nt" else s.st_ctime_ns
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, change_time,
            s.st_nlink, getattr(s, "st_file_attributes", 0))


def reject_ads(path):
    if os.name != "nt":
        return
    from ctypes import wintypes

    class StreamData(ctypes.Structure):
        _fields_ = [("size", ctypes.c_longlong), ("name", wintypes.WCHAR * 296)]

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    first = k.FindFirstStreamW
    first.argtypes = [wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(StreamData), wintypes.DWORD]
    first.restype = wintypes.HANDLE
    nxt = k.FindNextStreamW
    nxt.argtypes = [wintypes.HANDLE, ctypes.POINTER(StreamData)]
    nxt.restype = wintypes.BOOL
    close = k.FindClose
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    data = StreamData()
    handle = first(str(path), 0, ctypes.byref(data), 0)
    if handle == ctypes.c_void_p(-1).value:
        if ctypes.get_last_error() == 38:  # ERROR_HANDLE_EOF: no streams (e.g. empty file)
            return
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        while True:
            if data.name != "::$DATA":
                raise ArchiveError(f"alternate data stream HOLD: {path}: {data.name}")
            if not nxt(handle, ctypes.byref(data)):
                if ctypes.get_last_error() != 38:
                    raise ctypes.WinError(ctypes.get_last_error())
                break
    finally:
        close(handle)


@contextlib.contextmanager
def read_file(path):
    with locked_parents(path):
        with _read_file(path) as opened:
            yield opened


@contextlib.contextmanager
def _read_file(path):
    """Windows handles deny concurrent writes/replacement for the open file."""
    path = checked_path(path)
    before = path.lstat()
    if os.name == "nt":
        import msvcrt
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        create = k.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        handle = create(str(path), 0x80000000, 1, None, 3, 0x00200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            k.CloseHandle.argtypes = [wintypes.HANDLE]
            k.CloseHandle(handle)
            raise
    else:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        current = os.fstat(stream.fileno())
        check_stat(current)
        if identity(before) != identity(current):
            raise ArchiveError(f"source changed before open: {path}")
        reject_ads(path)
        yield stream, before
        after = os.fstat(stream.fileno())
        checked_path(path)
        if identity(current) != identity(after) or identity(after) != identity(path.lstat()):
            raise ArchiveError(f"source changed while reading: {path}")


def digest_stream(stream, sink=None, expected_size=None):
    h = hashlib.sha256()
    size = 0
    while True:
        block = stream.read(CHUNK)
        if not block:
            break
        size += len(block)
        if expected_size is not None and size > expected_size:
            raise ArchiveError("content exceeds expected length")
        h.update(block)
        if sink is not None:
            sink.write(block)
    return h.hexdigest(), size


def hash_file(path):
    with read_file(path) as (f, _):
        return digest_stream(f)


def encode_json(obj):
    return (json.dumps(obj, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")


class Budget:
    def __init__(self, vault, reserve, maximum):
        if not all(math.isfinite(x) and x >= 0 for x in (reserve, maximum)):
            raise ArchiveError("budgets must be finite and nonnegative")
        self.vault = vault
        self.reserve = int(reserve * GIB)
        self.maximum = int(maximum * GIB)
        self.added = 0

    def check(self, increase=0, diagnostic=False):
        allowance = 0 if diagnostic else DIAGNOSTIC_RESERVE
        if self.added + increase + allowance > self.maximum:
            raise ArchiveError(f"max-added budget exceeded: {self.added}+{increase}+{allowance}>{self.maximum}")
        if shutil.disk_usage(self.vault).free - increase < self.reserve + allowance:
            raise ArchiveError("reserve-free budget exceeded")


class NewFile:
    """Exclusive creation; enforce actual high-water bytes, including ZIP rewrites."""
    def __init__(self, path, budget=None, hard=None, diagnostic=False):
        self.parents = locked_parents(path)
        self.parents.__enter__()
        try:
            checked_path(path, missing=True)
            self.f = open(path, "xb+")
        except BaseException:
            self.parents.__exit__(*sys.exc_info())
            raise
        self.budget, self.hard, self.diagnostic = budget, hard, diagnostic
        self.high = 0

    def write(self, block):
        end = self.f.tell() + len(block)
        increase = max(0, end - self.high)
        if self.hard is not None and end > self.hard:
            raise ArchiveError("volume hard limit exceeded; partial volume retained")
        if self.budget:
            self.budget.check(increase, self.diagnostic)
        result = self.f.write(block)
        self.high = max(self.high, self.f.tell())
        if self.budget:
            self.budget.added += increase
        return result

    def tell(self):
        return self.f.tell()

    def seek(self, *args):
        return self.f.seek(*args)

    def flush(self):
        self.f.flush()

    def sync(self):
        self.f.flush()
        os.fsync(self.f.fileno())

    def close(self):
        try:
            self.f.close()
        finally:
            self.parents.__exit__(None, None, None)

    def set_mtime(self, ns):
        if os.name == "nt":
            import msvcrt
            from ctypes import wintypes
            ticks = ns // 100 + 116444736000000000
            ft = wintypes.FILETIME(ticks & 0xffffffff, ticks >> 32)
            k = ctypes.WinDLL("kernel32", use_last_error=True)
            fn = k.SetFileTime
            fn.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(wintypes.FILETIME)]
            fn.restype = wintypes.BOOL
            if not fn(msvcrt.get_osfhandle(self.f.fileno()), None, None, ctypes.byref(ft)):
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            os.utime(self.f.fileno(), ns=(ns, ns))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def write_json(path, data, budget=None, diagnostic=False):
    with NewFile(path, budget, diagnostic=diagnostic) as f:
        f.write(encode_json(data))
        f.sync()


def manifest_rows(path):
    with read_file(path) as (raw, _):
        with gzip.GzipFile(fileobj=raw, mode="rb") as gz:
            with io.TextIOWrapper(gz, encoding="utf-8-sig", newline="") as text:
                reader = csv.DictReader(text)
                required = {"path", "bytes", "sha256", "classification"}
                if not reader.fieldnames or not required <= set(reader.fieldnames):
                    raise ArchiveError("manifest requires path,bytes,sha256,classification")
                seen = set()
                for row in reader:
                    if row.get("classification") != "ELIGIBLE_A":
                        yield None
                        continue
                    name = relpath(row["path"])
                    if name.casefold() in seen:
                        raise ArchiveError(f"duplicate/case-colliding manifest path: {name}")
                    seen.add(name.casefold())
                    if not A_PATH_RE.fullmatch(name):
                        raise ArchiveError(f"ELIGIBLE_A path is outside the real A payload shape: {name}")
                    if not re.fullmatch(r"[0-9]+", row.get("bytes", "")) or not SHA_RE.fullmatch(row.get("sha256", "")):
                        raise ArchiveError(f"invalid bytes/sha256 for {name}")
                    yield {"path": name, "bytes": int(row["bytes"]), "sha256": row["sha256"]}


def member_name(sha, size):
    return f"sha256/{sha}-{size}"


def snapshot(s):
    return {"ctime_ns": s.st_ctime_ns, "mtime_ns": s.st_mtime_ns,
            "attrs": getattr(s, "st_file_attributes", 0), "linkcount": s.st_nlink,
            "mode": s.st_mode, "device": s.st_dev, "inode": s.st_ino}


def read_json(path):
    with read_file(path) as (f, _):
        return json.load(f)


def verify_core(vault, catalog):
    """No source tree reads. Every member and every source mapping is checked."""
    if catalog.get("format") != FORMAT:
        raise ArchiveError("unsupported vault format")
    if hash_file(vault / "plan_manifest.csv.gz")[0] != catalog["input_manifest_sha256"]:
        raise ArchiveError("input manifest snapshot hash mismatch")
    if hash_file(vault / "index.jsonl")[0] != catalog["index_sha256"]:
        raise ArchiveError("index hash mismatch")
    expected = {r["path"]: r for r in manifest_rows(vault / "plan_manifest.csv.gz") if r is not None}
    if not expected:
        raise ArchiveError("empty ELIGIBLE_A set")
    mappings, contents, folded = {}, {}, set()
    volume_names = set()
    for v in catalog["volumes"]:
        name = v["name"]
        if not VOLUME_RE.fullmatch(name) or name in volume_names:
            raise ArchiveError("invalid/duplicate volume name")
        volume_names.add(name)
    actual_volumes = {p.name for p in vault.iterdir() if p.name.startswith("volume-")}
    if actual_volumes != volume_names:
        raise ArchiveError("unlisted/missing volume files")
    with read_file(vault / "index.jsonl") as (f, _):
        for line in f:
            r = json.loads(line)
            name = relpath(r["path"])
            if name.casefold() in folded or name not in expected:
                raise ArchiveError("extra/duplicate/case-colliding index path")
            folded.add(name.casefold())
            if any(r[k] != expected[name][k] for k in ("bytes", "sha256")):
                raise ArchiveError(f"index disagrees with manifest: {name}")
            meta = r["metadata"]
            if meta["linkcount"] != 1 or meta["attrs"] & REPARSE or r["mtime_ns"] != meta["mtime_ns"]:
                raise ArchiveError("unsafe/inconsistent source metadata")
            if r["volume"] not in volume_names or r["member"] != member_name(r["sha256"], r["bytes"]):
                raise ArchiveError("unsafe volume/member mapping")
            key = (r["sha256"], r["bytes"])
            loc = (r["volume"], r["member"])
            if key in contents and contents[key] != loc:
                raise ArchiveError("content has conflicting locations")
            contents[key] = loc
            mappings[name] = r
    if mappings.keys() != expected.keys():
        raise ArchiveError("incomplete source mapping")
    wanted = {loc: key for key, loc in contents.items()}
    checked = set()
    for v in catalog["volumes"]:
        with read_file(vault / v["name"]) as (raw, _):
            if digest_stream(raw) != (v["sha256"], v["bytes"]):
                raise ArchiveError(f"volume hash/length mismatch: {v['name']}")
            raw.seek(0)
            with zipfile.ZipFile(raw, "r") as z:
                infos = z.infolist()
                if not infos:
                    raise ArchiveError("empty volume")
                for info in infos:
                    loc = (v["name"], info.filename)
                    if loc in checked or loc not in wanted:
                        raise ArchiveError("extra/duplicate/unsafe ZIP member")
                    sha, size = wanted[loc]
                    mode = info.external_attr >> 16
                    if info.is_dir() or stat.S_ISLNK(mode) or info.flag_bits & 1 or info.compress_type != zipfile.ZIP_DEFLATED or info.file_size != size:
                        raise ArchiveError("unsupported ZIP member attributes")
                    with z.open(info) as data:
                        if digest_stream(data, expected_size=size) != (sha, size):
                            raise ArchiveError("readback SHA/length mismatch")
                    checked.add(loc)
    if checked != set(wanted):
        raise ArchiveError("missing volume members")
    stats = {"source_paths": len(mappings), "unique_contents": len(contents),
             "source_logical_bytes": sum(r["bytes"] for r in mappings.values()),
             "unique_logical_bytes": sum(k[1] for k in contents),
             "volume_count": len(volume_names), "volume_bytes": sum(v["bytes"] for v in catalog["volumes"]),
             "readback_members": len(checked), "physical_released_bytes": 0}
    if stats != catalog["statistics"]:
        raise ArchiveError("catalog statistics mismatch")
    return stats, mappings


def build(root, manifest, vault, reserve_free_gib=15, max_added_gib=10):
    root = checked_path(root, directory=True)
    manifest = checked_path(manifest)
    vault = checked_path(vault, directory=True, missing=True)
    if vault.exists():
        raise ArchiveError("vault must be a new directory")
    # Validate the numeric configuration before creating anything.
    budget = Budget(vault, reserve_free_gib, max_added_gib)
    input_hash = hash_file(manifest)[0]
    new_directory(vault)
    report = {"format": FORMAT, "operation": "build", "status": "RUNNING",
              "started_ns": time.time_ns(), "input_manifest_sha256": input_hash,
              "limits": {"reserve_free_bytes": budget.reserve, "max_added_bytes": budget.maximum,
                         "volume_target_bytes": VOLUME_TARGET, "volume_hard_bytes": VOLUME_HARD},
              "source_policy": "unchanged; nlink!=1/reparse/ADS rejected", "physical_released_bytes": 0}
    log = None
    z = None
    volume_file = None
    volumes = []
    source_count = logical = skipped = 0
    contents = {}
    checkpoint_count = 0
    checkpoint_time = time.monotonic()

    def event(kind, **detail):
        log.write(encode_json({"time_ns": time.time_ns(), "event": kind, **detail}))
        if kind in ("source_started", "source_verified"):
            # Visibility only. These events do not certify durable ZIP/index data.
            log.flush()
        else:
            log.sync()

    def checkpoint(index, force=False):
        nonlocal checkpoint_count, checkpoint_time
        now = time.monotonic()
        if not force and source_count - checkpoint_count < CHECKPOINT_SOURCES and now - checkpoint_time < CHECKPOINT_SECONDS:
            return
        # Commit buffered payload before its mappings and source events. ZIP is
        # still incomplete until close + full readback + the final PASS report.
        if volume_file is not None:
            volume_file.sync()
        index.sync()
        log.sync()
        checkpoint_count = source_count
        checkpoint_time = time.monotonic()

    def finish_volume():
        nonlocal z, volume_file
        if z is None:
            return
        z.close()
        z = None
        volume_file.sync()
        volume_file.close()
        volume_file = None
        name = f"volume-{len(volumes) + 1:06d}.zip"
        sha, size = hash_file(vault / name)
        volumes.append({"name": name, "sha256": sha, "bytes": size})
        event("volume_closed_pending_readback", **volumes[-1])

    try:
        log = NewFile(vault / "build_events.jsonl", budget)
        event("started", root=str(root), manifest=str(manifest))
        with read_file(manifest) as (src, _):
            with NewFile(vault / "plan_manifest.csv.gz", budget) as dst:
                sha, _ = digest_stream(src, dst)
                dst.sync()
        if sha != input_hash:
            raise ArchiveError("input manifest changed since preflight hash")
        event("manifest_snapshotted", sha256=sha)
        with NewFile(vault / "index.jsonl", budget) as index:
            for row in manifest_rows(vault / "plan_manifest.csv.gz"):
                if row is None:
                    skipped += 1
                    continue
                name, size, sha = row["path"], row["bytes"], row["sha256"]
                source = under(root, name)
                # Do not let a supplied manifest archive the new vault itself.
                if source == vault or vault in source.parents:
                    raise ArchiveError("source intersects vault")
                event("source_started", path=name, expected_sha256=sha, bytes=size)
                key = (sha, size)
                with read_file(source) as (src, s):
                    if s.st_size != size:
                        raise ArchiveError(f"source length mismatch: {name}")
                    if key not in contents:
                        if z is not None and volume_file.tell() >= VOLUME_TARGET:
                            finish_volume()
                        if z is None:
                            vname = f"volume-{len(volumes) + 1:06d}.zip"
                            volume_file = NewFile(vault / vname, budget, hard=VOLUME_HARD)
                            z = zipfile.ZipFile(volume_file, "w", compression=zipfile.ZIP_DEFLATED,
                                                compresslevel=6, allowZip64=True)
                        member = member_name(sha, size)
                        with z.open(member, "w", force_zip64=True) as out:
                            actual = digest_stream(src, out, expected_size=size)
                        contents[key] = (vname, member)
                    else:
                        actual = digest_stream(src, expected_size=size)
                    if actual != key:
                        raise ArchiveError(f"source SHA/length mismatch: {name}; expected={key}, got={actual}")
                    meta = snapshot(s)
                loc = contents[key]
                index.write(encode_json({**row, "volume": loc[0], "member": loc[1],
                                         "mtime_ns": meta["mtime_ns"], "metadata": meta}))
                index.flush()
                source_count += 1
                logical += size
                event("source_verified", path=name, sha256=sha, bytes=size,
                      volume=loc[0], member=loc[1])
                checkpoint(index)
            if not source_count:
                raise ArchiveError("no ELIGIBLE_A sources")
            checkpoint(index, force=True)
        finish_volume()
        stats = {"source_paths": source_count, "unique_contents": len(contents),
                 "source_logical_bytes": logical, "unique_logical_bytes": sum(k[1] for k in contents),
                 "volume_count": len(volumes), "volume_bytes": sum(v["bytes"] for v in volumes),
                 "readback_members": len(contents), "physical_released_bytes": 0}
        catalog = {"format": FORMAT, "input_manifest_sha256": report["input_manifest_sha256"],
                   "index_sha256": hash_file(vault / "index.jsonl")[0],
                   "volumes": volumes, "statistics": stats}
        verified, _ = verify_core(vault, catalog)
        event("full_readback_verified", statistics=verified)
        # No rename: a failed/incomplete vault never gets a successful build report.
        write_json(vault / "catalog.json", catalog, budget)
        event("completed", statistics=stats)
        budget.check()
        report.update(status="PASS", statistics=stats, skipped_manifest_rows=skipped,
                      catalog_sha256=hash_file(vault / "catalog.json")[0])
    except BaseException as exc:
        report.update(status="FAIL", error=f"{type(exc).__name__}: {exc}",
                      completed_source_paths=source_count, completed_source_logical_bytes=logical)
        # Failed output is deliberately retained. Best-effort close cannot mask the error.
        for obj in (z, volume_file):
            if obj is not None:
                try:
                    obj.close()
                except BaseException as close_error:
                    report.setdefault("close_errors", []).append(str(close_error))
        raise
    finally:
        if log is not None:
            log.close()
        report["ended_ns"] = time.time_ns()
        report["accounted_bytes_before_report"] = budget.added
        # Emergency report consumes the explicitly held diagnostic reserve.
        write_json(vault / "build_report.json", report, budget, diagnostic=True)
    return report


def load_verified(vault):
    vault = checked_path(vault, directory=True)
    build_report = read_json(vault / "build_report.json")
    if build_report.get("status") != "PASS" or build_report.get("format") != FORMAT:
        raise ArchiveError("vault has no completed PASS build")
    if hash_file(vault / "catalog.json")[0] != build_report["catalog_sha256"]:
        raise ArchiveError("catalog hash mismatch")
    catalog = read_json(vault / "catalog.json")
    if catalog["input_manifest_sha256"] != build_report["input_manifest_sha256"]:
        raise ArchiveError("build/catalog manifest identity mismatch")
    stats, mappings = verify_core(vault, catalog)
    if stats != build_report["statistics"]:
        raise ArchiveError("build/catalog statistics mismatch")
    return vault, catalog, stats, mappings


def verify(vault):
    vault = checked_path(vault, directory=True)
    report = {"format": FORMAT, "operation": "verify", "status": "FAIL", "started_ns": time.time_ns()}
    try:
        previous = read_json(vault / "build_report.json")
        report["input_manifest_sha256"] = previous.get("input_manifest_sha256")
        _, catalog, stats, _ = load_verified(vault)
        report.update(status="PASS", statistics=stats, volumes=catalog["volumes"],
                      catalog_sha256=hash_file(vault / "catalog.json")[0],
                      index_sha256=catalog["index_sha256"])
        return report
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["ended_ns"] = time.time_ns()
        write_json(vault / f"verify_report-{uuid.uuid4().hex}.json", report)


def restore(vault, request, dest):
    vault = checked_path(vault, directory=True)
    report = {"format": FORMAT, "operation": "restore", "status": "FAIL", "started_ns": time.time_ns(),
              "restored_paths": [], "physical_released_bytes": 0}
    try:
        with read_file(request) as (f, _):
            report["request_sha256"] = digest_stream(f)[0]
            f.seek(0)
            names = json.load(f)
        if not isinstance(names, list) or not names:
            raise ArchiveError("request must be a nonempty JSON array of exact paths")
        folded = set()
        for name in names:
            relpath(name)
            if name.casefold() in folded:
                raise ArchiveError("duplicate/case-colliding restore request")
            folded.add(name.casefold())
        dest = checked_path(dest, directory=True, missing=True)
        if dest.exists() or dest == vault or vault in dest.parents or dest in vault.parents:
            raise ArchiveError("restore destination must be an independent new directory")
        previous = read_json(vault / "build_report.json")
        report["input_manifest_sha256"] = previous.get("input_manifest_sha256")
        _, catalog, stats, mappings = load_verified(vault)
        missing = [n for n in names if n not in mappings]
        if missing:
            raise ArchiveError(f"missing requested paths: {missing}")
        # File-vs-directory collisions must be rejected before creating the destination.
        requested = {n.casefold() for n in names}
        for name in names:
            parts = name.split("/")
            if any("/".join(parts[:i]).casefold() in requested for i in range(1, len(parts))):
                raise ArchiveError("restore file/directory collision")
        new_directory(dest)
        volume_info = {v["name"]: v for v in catalog["volumes"]}
        by_volume = {}
        for name in names:
            by_volume.setdefault(mappings[name]["volume"], []).append(name)
        for volume, volume_paths in by_volume.items():
            # Keep one locked volume open for its whole restore group, avoiding
            # a full-volume rehash for every small output in the same ZIP.
            with read_file(vault / volume) as (raw, _):
                v = volume_info[volume]
                if digest_stream(raw) != (v["sha256"], v["bytes"]):
                    raise ArchiveError("volume changed since verify")
                raw.seek(0)
                with zipfile.ZipFile(raw) as z:
                    for name in volume_paths:
                        row = mappings[name]
                        out = under(dest, name)
                        parent = dest
                        for part in name.split("/")[:-1]:
                            parent = parent / part
                            if not parent.exists():
                                new_directory(parent)
                            checked_path(parent, directory=True)
                        # Read and validate before creating each new output.
                        with z.open(row["member"]) as data:
                            if digest_stream(data, expected_size=row["bytes"]) != (row["sha256"], row["bytes"]):
                                raise ArchiveError("restore member failed pre-write SHA/length check")
                        with z.open(row["member"]) as data, NewFile(out) as dst:
                            if digest_stream(data, dst, expected_size=row["bytes"]) != (row["sha256"], row["bytes"]):
                                raise ArchiveError("restore write SHA/length mismatch")
                            dst.sync()
                            dst.set_mtime(row["mtime_ns"])
                        report["restored_paths"].append(name)
        report.update(status="PASS", verified_statistics=stats,
                      restored_bytes=sum(mappings[n]["bytes"] for n in names))
        return report
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["ended_ns"] = time.time_ns()
        write_json(vault / f"restore_report-{uuid.uuid4().hex}.json", report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("build")
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--vault", required=True, type=Path)
    p.add_argument("--reserve-free-gib", type=float, default=15)
    p.add_argument("--max-added-gib", type=float, default=10)
    p = commands.add_parser("verify")
    p.add_argument("--vault", required=True, type=Path)
    p = commands.add_parser("restore")
    p.add_argument("--vault", required=True, type=Path)
    p.add_argument("--request", required=True, type=Path)
    p.add_argument("--dest", required=True, type=Path)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    try:
        result = {"build": build, "verify": verify, "restore": restore}[command](**args)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "operation": command,
                          "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
