#!/usr/bin/env python3
"""Build an explicit-file ZIP bundle from a JSON specification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

CHUNK_SIZE = 1024 * 1024
SPEC_KEYS = {"packages"}
PACKAGE_KEYS = {"name", "files"}
FILE_KEYS = {"source", "target", "sha256"}
SHA256_RE = re.compile(r"[0-9a-fA-F]{64}\Z")
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]}


class BundleError(Exception):
    """Expected validation or build failure."""


def die(message: str) -> None:
    raise BundleError(message)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stat_key(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def within(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def check_keys(value: dict[str, Any], allowed: set[str], where: str, required: set[str] | None = None) -> None:
    extra = sorted(set(value) - allowed)
    missing = sorted((allowed if required is None else required) - set(value))
    if extra:
        die(f"{where}: unknown keys: {', '.join(extra)}")
    if missing:
        die(f"{where}: missing keys: {', '.join(missing)}")


def safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        die(f"{label} must be a non-empty string")
    if "\\" in value or "\x00" in value or any(ord(char) < 32 for char in value):
        die(f"{label} must use safe forward-slash relative syntax")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts) or PurePosixPath(value).is_absolute():
        die(f"{label} must be a normalized relative path without . or ..")
    return PurePosixPath(*parts).as_posix()


def safe_package_name(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        die(f"{where}.name must be a valid basename ending in .zip")
    if "\\" in value or "/" in value or len(value) <= 4 or not value.lower().endswith(".zip"):
        die(f"{where}.name must be a basename ending in .zip")
    if value.endswith((" ", ".")) or any(char in '<>:"|?*' or ord(char) < 32 for char in value):
        die(f"{where}.name contains a non-portable filename character")
    if value[:-4].upper() in WINDOWS_RESERVED:
        die(f"{where}.name is a reserved filename")
    return value


def source_item(root: Path, value: Any, expected: Any, where: str) -> dict[str, Any]:
    source = safe_relative(value, f"{where}.source")
    candidate = root.joinpath(*source.split("/"))
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        die(f"{where}.source does not resolve: {source}: {exc}")
    if not within(root, resolved):
        die(f"{where}.source resolves outside --root: {source}")
    info = resolved.stat()
    if not stat.S_ISREG(info.st_mode):
        die(f"{where}.source is not a regular file: {source}")
    if expected is not None and (not isinstance(expected, str) or not SHA256_RE.fullmatch(expected)):
        die(f"{where}.sha256 must be exactly 64 hexadecimal characters")
    return {
        "source": source,
        "candidate": candidate,
        "resolved": resolved,
        "snapshot": stat_key(info),
        "expected_sha256": expected.lower() if expected else None,
    }


def load_spec(spec_path: Path, root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        raw = spec_path.read_bytes()
    except OSError as exc:
        die(f"cannot read --spec: {spec_path}: {exc}")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        die(f"--spec is not valid UTF-8 JSON: {exc}")
    if not isinstance(data, dict):
        die("--spec top level must be an object")
    check_keys(data, SPEC_KEYS, "spec")
    if not isinstance(data["packages"], list) or not data["packages"]:
        die("spec.packages must be a non-empty array")

    packages: list[dict[str, Any]] = []
    names: set[str] = set()
    root_resolved = root.resolve(strict=True)
    for pindex, raw_package in enumerate(data["packages"]):
        where = f"packages[{pindex}]"
        if not isinstance(raw_package, dict):
            die(f"{where} must be an object")
        check_keys(raw_package, PACKAGE_KEYS, where)
        name = safe_package_name(raw_package["name"], where)
        if name.casefold() in names:
            die(f"duplicate package name: {name}")
        names.add(name.casefold())
        raw_files = raw_package["files"]
        if not isinstance(raw_files, list) or not raw_files:
            die(f"{where}.files must be a non-empty array")
        targets: set[str] = set()
        files: list[dict[str, Any]] = []
        for findex, raw_file in enumerate(raw_files):
            fwhere = f"{where}.files[{findex}]"
            if not isinstance(raw_file, dict):
                die(f"{fwhere} must be an object")
            check_keys(raw_file, FILE_KEYS, fwhere, {"source", "target"})
            target = safe_relative(raw_file["target"], f"{fwhere}.target")
            if target.casefold() in targets:
                die(f"{where}: duplicate target: {target}")
            targets.add(target.casefold())
            item = source_item(root_resolved, raw_file["source"], raw_file.get("sha256"), fwhere)
            item["target"] = target
            files.append(item)
        packages.append({"name": name, "files": files})
    return packages, {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def check_source_current(item: dict[str, Any], root: Path, where: str) -> tuple[Path, os.stat_result]:
    try:
        current = item["candidate"].resolve(strict=True)
    except OSError as exc:
        die(f"{where}: source disappeared or cannot be resolved: {exc}")
    if current != item["resolved"] or not within(root, current) or not stat.S_ISREG(current.stat().st_mode):
        die(f"{where}: source path or target changed during build")
    info = current.stat()
    if stat_key(info) != item["snapshot"]:
        die(f"{where}: source changed during build")
    return current, info


def copy_and_zip(item: dict[str, Any], root: Path, archive: zipfile.ZipFile, where: str) -> dict[str, Any]:
    source_path, _ = check_source_current(item, root, where)
    digest = hashlib.sha256()
    size = 0
    try:
        with source_path.open("rb") as source, archive.open(item["target"], "w") as target:
            opened = os.fstat(source.fileno())
            # Windows stat/fstat can report different ctime semantics. Compare
            # identity/size/mtime across APIs; retain full keys within each API.
            if stat_key(opened)[:4] != item["snapshot"][:4]:
                die(f"{where}: source changed before copy")
            for chunk in iter(lambda: source.read(CHUNK_SIZE), b""):
                target.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            closed_stat = os.fstat(source.fileno())
    except (OSError, zipfile.BadZipFile) as exc:
        die(f"{where}: copy failed: {exc}")
    _, current = check_source_current(item, root, where)
    if stat_key(closed_stat) != stat_key(opened) or stat_key(current) != item["snapshot"] or size != opened.st_size:
        die(f"{where}: source changed while copying")
    actual = digest.hexdigest()
    if item["expected_sha256"] and actual != item["expected_sha256"]:
        die(f"{where}: SHA-256 mismatch: expected {item['expected_sha256']}, got {actual}")
    return {"source": item["source"], "target": item["target"], "size": size, "sha256": actual}


def verify_archive(path: Path, records: list[dict[str, Any]], package_name: str) -> None:
    expected = {record["target"]: record for record in records}
    seen: set[str] = set()
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            if len(infos) != len(records):
                die(f"{package_name}: ZIP count mismatch after readback")
            for info in infos:
                if info.is_dir() or info.filename in seen or info.filename not in expected:
                    die(f"{package_name}: unexpected or duplicate ZIP entry: {info.filename}")
                seen.add(info.filename)
                record = expected[info.filename]
                digest = hashlib.sha256()
                with archive.open(info, "r") as stream:
                    for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
                        digest.update(chunk)
                if info.file_size != record["size"] or digest.hexdigest() != record["sha256"]:
                    die(f"{package_name}: ZIP entry verification failed: {info.filename}")
    except (OSError, zipfile.BadZipFile) as exc:
        die(f"{package_name}: ZIP readback failed: {exc}")
    if seen != set(expected):
        die(f"{package_name}: ZIP entry set mismatch after readback")


def build(root: Path, spec_path: Path, out: Path) -> dict[str, Any]:
    if not root.exists() or not root.is_dir():
        die(f"--root is not an existing directory: {root}")
    if out.exists():
        die(f"--out must not exist: {out}")
    if not out.parent.exists() or not out.parent.is_dir():
        die(f"--out parent must be an existing directory: {out.parent}")
    packages, spec_record = load_spec(spec_path, root)
    try:
        out.mkdir()
    except FileExistsError:
        die(f"--out must not exist: {out}")
    except OSError as exc:
        die(f"cannot create --out: {exc}")

    package_records: list[dict[str, Any]] = []
    for package in packages:
        package_path = out / package["name"]
        records: list[dict[str, Any]] = []
        try:
            with zipfile.ZipFile(package_path, "x", compression=zipfile.ZIP_DEFLATED, allowZip64=True, strict_timestamps=False) as archive:
                for findex, item in enumerate(package["files"]):
                    records.append(copy_and_zip(item, root.resolve(strict=True), archive, f"{package['name']}.files[{findex}]"))
        except (OSError, zipfile.BadZipFile) as exc:
            die(f"{package['name']}: cannot create ZIP: {exc}")
        verify_archive(package_path, records, package["name"])
        package_records.append({
            "name": package["name"],
            "size": package_path.stat().st_size,
            "sha256": sha256_path(package_path),
            "file_count": len(records),
            "files": records,
        })

    manifest_path = out / "manifest.json"
    manifest = {
        "schema": "explicit-bundle-manifest-v1",
        "spec": {"name": spec_path.name, **spec_record},
        "packages": package_records,
    }
    payload = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with manifest_path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        die(f"cannot write manifest.json: {exc}")
    return {"manifest": str(manifest_path), "sha256": hashlib.sha256(payload).hexdigest(), "packages": package_records}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="project root containing source files")
    parser.add_argument("--spec", required=True, type=Path, help="explicit JSON bundle specification")
    parser.add_argument("--out", required=True, type=Path, help="new output directory (must not exist)")
    args = parser.parse_args(argv)
    try:
        result = build(args.root, args.spec, args.out)
    except BundleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"error: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
