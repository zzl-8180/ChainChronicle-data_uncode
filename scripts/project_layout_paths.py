"""Explicit, SHA-pinned data paths; no activation or filesystem mutation on import.

No configuration preserves Path(path), including its original relative semantics.
Active configuration is a per-process immutable snapshot. Callers keep their code
ROOT and pass it as root when a path is built from that namespace.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import NamedTuple

CONFIG_ENV = "CC_PROJECT_LAYOUT_CONFIG"
SHA_ENV = "CC_PROJECT_LAYOUT_SHA256"
_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_ACTIVATION_KEY = None


class LayoutPathError(ValueError):
    pass


class _Layout(NamedTuple):
    repository_root: Path
    reads: tuple
    writes: tuple
    strict_writes: tuple
    legacy_roots: tuple
    deny_unmapped_output_writes: bool


def _need(ok, message):
    if not ok:
        raise LayoutPathError(message)


def _absolute(path):
    return Path(os.path.abspath(os.fspath(path)))


def _physical(value, repository_root):
    _need(isinstance(value, str) and value and "\x00" not in value, "Invalid physical path")
    path = Path(value)
    _need(".." not in path.parts, "Parent traversal in configured path")
    _need(not path.drive or path.is_absolute(), "Drive-relative physical path")
    return _absolute(path if path.is_absolute() else repository_root / path)


def _real_ancestors(path):
    """Only inspect existing ancestors; permission/I/O errors are never absence."""
    for ancestor in reversed((path, *path.parents)):
        try:
            info = ancestor.lstat()
        except FileNotFoundError:
            continue
        _need(not getattr(info, "st_file_attributes", 0) & 0x400
              and not ancestor.is_symlink(), "Reparse in strict write boundary: " + str(ancestor))


def _table(value, repository_root):
    _need(isinstance(value, dict), "Path root table must be an object")
    rows = []
    seen = set()
    for key, destination in value.items():
        _need(isinstance(key, str) and key and "\x00" not in key, "Invalid logical root")
        key = key.replace("\\", "/").rstrip("/")
        parts = key.split("/")
        _need(not key.startswith("/") and ":" not in key
              and all(part not in ("", ".", "..") for part in parts), "Unsafe logical root")
        folded = tuple(part.casefold() for part in parts)
        _need(folded not in seen, "Duplicate logical root after case normalization")
        seen.add(folded)
        rows.append((folded, _physical(destination, repository_root)))
    return tuple(sorted(rows, key=lambda row: len(row[0]), reverse=True))


@lru_cache(maxsize=8)
def _load(config_name, expected_sha, raw):
    config_path = Path(config_name)
    _need(config_path.is_absolute(), "Layout configuration must have an absolute path")
    _need(len(expected_sha) == 64 and all(c in "0123456789abcdef" for c in expected_sha.lower()),
          "Invalid layout SHA-256")
    _need(hashlib.sha256(raw).hexdigest() == expected_sha.lower(), "Layout configuration SHA mismatch")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise LayoutPathError("Invalid layout JSON") from error
    _need(isinstance(data, dict) and type(data.get("schema_version")) is int
          and data["schema_version"] == 1, "Unsupported layout schema")
    allowed = {"schema_version", "repository_root", "read_roots", "write_roots", "strict_write_roots",
               "legacy_repository_roots", "deny_unmapped_output_writes", "description", "mode"}
    _need(not set(data) - allowed, "Unknown layout configuration field")
    _need({"repository_root", "read_roots", "write_roots"} <= set(data), "Missing required layout fields")
    _need(isinstance(data["repository_root"], str), "repository_root must be a path string")
    repository_root = Path(data["repository_root"])
    _need(".." not in repository_root.parts and (not repository_root.drive or repository_root.is_absolute()),
          "Unsafe repository_root")
    repository_root = _absolute(repository_root if repository_root.is_absolute() else _SOURCE_ROOT / repository_root)
    reads = _table(data["read_roots"], repository_root)
    writes = _table(data["write_roots"], repository_root)
    strict = data.get("strict_write_roots", [])
    legacy = data.get("legacy_repository_roots", [])
    _need(isinstance(strict, list) and isinstance(legacy, list), "Root allowlists must be arrays")
    strict = tuple(_physical(p, repository_root) for p in strict)
    legacy = tuple(_physical(p, repository_root) for p in legacy)
    for boundary in strict:
        _real_ancestors(boundary)
    deny = data.get("deny_unmapped_output_writes", False)
    _need(isinstance(deny, bool), "deny_unmapped_output_writes must be boolean")
    return _Layout(repository_root, reads, writes, strict, legacy, deny)


def _active():
    global _ACTIVATION_KEY
    name, digest = os.environ.get(CONFIG_ENV), os.environ.get(SHA_ENV)
    if name is None and digest is None:
        # This locator is installed only by the later explicitly authorized
        # cutover. Absence keeps legacy behavior; a broken installed locator
        # must not silently reactivate old output paths.
        selector = _SOURCE_ROOT / "scripts/project_layout_active.json"
        _real_ancestors(selector.parent)
        try:
            selector_info = selector.lstat()
        except FileNotFoundError:
            _need(_ACTIVATION_KEY in (None, ("legacy",)), "Layout activation removed; restart this process")
            _ACTIVATION_KEY = ("legacy",)
            return None
        _need(stat.S_ISREG(selector_info.st_mode)
              and not getattr(selector_info, "st_file_attributes", 0) & 0x400,
              "Active layout locator must be a real ordinary file")
        # An existing locator that vanishes or cannot be read is an error, not
        # proof of uninstalled legacy mode.
        selector_raw = selector.read_bytes()
        try:
            selected = json.loads(selector_raw)
        except (ValueError, UnicodeError) as error:
            raise LayoutPathError("Invalid active layout locator") from error
        _need(isinstance(selected, dict) and set(selected) == {"schema_version", "configuration", "sha256"}
              and type(selected["schema_version"]) is int and selected["schema_version"] == 1,
              "Invalid active layout locator schema")
        name = str(_physical(selected["configuration"], _SOURCE_ROOT))
        digest = selected["sha256"]
    _need(bool(name) and bool(digest), "Layout configuration and SHA must both be explicitly provided")
    _need(isinstance(name, str) and isinstance(digest, str), "Layout locator fields must be strings")
    config_path = Path(name)
    _need(config_path.is_absolute(), "Layout configuration must have an absolute path")
    # Always read and check current bytes, even when their parsed form is cached.
    # Parsing and hashing use this same buffer; changing a pinned file fails closed.
    raw = config_path.read_bytes()
    result = _load(name, digest, raw)
    key = (str(config_path), digest.lower())
    _need(_ACTIVATION_KEY is None or _ACTIVATION_KEY == key,
          "Layout changed after process initialization; restart to avoid mixed cached roots")
    _ACTIVATION_KEY = key
    return result


def _relative(path, namespaces):
    """Extract a logical path without resolving any data symlink."""
    value = os.fspath(path)
    _need("\x00" not in value, "NUL in input path")
    if value.startswith("\\\\?\\"):
        value = value[4:]
    value = value.replace("\\", "/")
    path = Path(value)
    _need(".." not in path.parts, "Parent traversal in logical path")
    _need(not path.drive or path.is_absolute(), "Drive-relative input path")
    if not path.is_absolute():
        return path, None
    absolute = _absolute(path)
    for namespace in sorted(set(namespaces), key=lambda p: len(p.parts), reverse=True):
        try:
            return absolute.relative_to(namespace), None
        except ValueError:
            pass
    return None, absolute


def _resolve(path, root, access):
    config = _active()
    original = Path(path)
    if config is None:
        return original
    namespace = _absolute(root) if root is not None else _SOURCE_ROOT
    logical, external = _relative(path, (namespace, _SOURCE_ROOT, config.repository_root, *config.legacy_roots))
    mapped = False
    if external is not None:
        result = external
    else:
        parts = logical.parts
        _need(not parts or parts[0].casefold() != "scripts",
              "Source-code paths must use the caller's code root, not the data resolver")
        folded = tuple(part.casefold() for part in parts)
        table = config.reads if access == "read" else config.writes
        for prefix, physical in table:
            if folded[:len(prefix)] == prefix:
                result = physical.joinpath(*parts[len(prefix):])
                mapped = True
                break
        else:
            result = config.repository_root / logical
        if access == "write" and config.deny_unmapped_output_writes:
            _need(mapped or not parts or parts[0].casefold() != "output", "Unmapped output write denied")
    if access == "write" and config.strict_writes:
        # Do not let a link below an approved scratch root lead into live data.
        for boundary in config.strict_writes:
            _real_ancestors(boundary)
        resolved = result.resolve(strict=False)
        _need(any(resolved.is_relative_to(boundary) for boundary in config.strict_writes),
              "Write outside declared roots: " + str(result))
    return result


def layout_active():
    """Validate and report the actual process mode, including installed locators."""
    return _active() is not None


def read_path(path, *, root=None):
    """Resolve declared input location; never mkdir, probe fallbacks or rewrite metadata."""
    return _resolve(path, root, "read")


def write_path(path, *, root=None):
    """Resolve a declared output location; strict candidate roots are fail-closed."""
    return _resolve(path, root, "write")


def path_reference(path, *, root=None):
    """Serialize a newly produced locator, never mutate historical metadata.

    Legacy mode preserves str(path). Active mode emits a repository-relative
    locator when possible; genuinely external locations remain absolute.
    Pass an already resolved physical read_path/write_path result. This function
    does not remap an old logical path. It is for data-locator fields, not
    source-code signature keys or logs.
    """
    config = _active()
    if config is None:
        return str(path)
    value = Path(path)
    _need(value.is_absolute(), "Resolve the physical data path before serializing its locator")
    value = _absolute(value)
    try:
        return value.relative_to(config.repository_root).as_posix()
    except ValueError:
        return value.as_posix()
