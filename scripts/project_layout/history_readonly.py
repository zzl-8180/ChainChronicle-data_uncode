"""Read-only route for six preserved historical review junctions after authorization.

No installation, fallback, directory mutation or old-verifier replay. The caller
must supply the exact SHA-256 of the manifest bytes and an exact alias key.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

MOUNT_POINT_TAG = 0xA0000003
REPARSE_ATTR = 0x400
ALIAS_PREFIX = 'work/review_p2b5_thirdparty/iso/output/'
PROPOSAL_KIND = 'SIX_FROZEN_HISTORY_READONLY_ROUTE_PROPOSAL_NOT_ACTIVE'
ACTIVE_KIND = 'SIX_FROZEN_HISTORY_READONLY_ROUTE_ACTIVE'


class RouteError(ValueError):
    pass


def _parts(value: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or '\x00' in value or '\\' in value or ':' in value or value.startswith('/'):
        raise RouteError('Unsafe relative path')
    parts = tuple(value.split('/'))
    if any(part in ('', '.', '..') for part in parts):
        raise RouteError('Unsafe relative path component')
    return parts


def _ordinary(path: Path, *, final_reparse=False):
    sequence = tuple(reversed((path, *path.parents)))
    info = None
    for index, item in enumerate(sequence):
        try:
            info = item.lstat()
        except OSError as error:
            raise RouteError('Missing or unreadable route component: ' + str(item)) from error
        if getattr(info, 'st_file_attributes', 0) & REPARSE_ATTR or item.is_symlink():
            if not (final_reparse and index == len(sequence)-1):
                raise RouteError('Reparse in route component: ' + str(item))
    return info


def load_manifest(path: Path, expected_sha256: str) -> dict:
    path = Path(path)
    if not path.is_absolute() or not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise RouteError('Absolute manifest and exact SHA-256 required')
    _ordinary(path)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256.lower():
        raise RouteError('Manifest SHA-256 mismatch')
    try:
        manifest = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise RouteError('Invalid route manifest') from error
    if manifest.get('schema_version') != 1 or manifest.get('kind') not in (PROPOSAL_KIND, ACTIVE_KIND):
        raise RouteError('Unexpected route manifest schema')
    root = Path(manifest.get('repository_root', ''))
    if not root.is_absolute() or '..' in root.parts:
        raise RouteError('Unsafe repository root')
    _ordinary(root)
    aliases = manifest.get('aliases')
    if not isinstance(aliases, list) or len(aliases) != 6:
        raise RouteError('Six exact aliases required')
    keys = []
    for row in aliases:
        if not isinstance(row, dict):
            raise RouteError('Invalid alias row')
        key = row.get('alias')
        _parts(key)
        if not key.startswith(ALIAS_PREFIX) or len(_parts(key)) != len(_parts(ALIAS_PREFIX[:-1])) + 1:
            raise RouteError('Alias outside frozen six namespace')
        target = row.get('new_target')
        if _parts(target)[0] != 'projects':
            raise RouteError('New target must be under projects')
        if row.get('old_tag') != MOUNT_POINT_TAG or not isinstance(row.get('old_target_raw'), str):
            raise RouteError('Missing frozen alias identity')
        if not (type(row.get('source_root_dev')) is int and type(row.get('source_root_ino')) is int):
            raise RouteError('Missing pre-move source root identity')
        if manifest['kind'] == ACTIVE_KIND and not (type(row.get('new_root_dev')) is int and
                                                    type(row.get('new_root_ino')) is int):
            raise RouteError('Active route requires post-move new root identity')
        if manifest['kind'] == ACTIVE_KIND and (row['new_root_dev'], row['new_root_ino']) != (
                row['source_root_dev'], row['source_root_ino']):
            raise RouteError('Relocated root must retain pre-move directory identity')
        keys.append(key.casefold())
    if len(set(keys)) != 6:
        raise RouteError('Duplicate frozen alias key')
    return manifest


def _verify_alias(manifest: dict, alias: str) -> dict:
    _parts(alias)
    matches = [row for row in manifest['aliases'] if row['alias'] == alias]
    if len(matches) != 1:
        raise RouteError('Alias is not in pinned frozen six')
    row = matches[0]
    physical = Path(manifest['repository_root']).joinpath(*_parts(alias))
    info = _ordinary(physical, final_reparse=True)
    if not (getattr(info, 'st_file_attributes', 0) & REPARSE_ATTR) or getattr(info, 'st_reparse_tag', None) != MOUNT_POINT_TAG:
        raise RouteError('Frozen alias is not the expected mount-point junction')
    if (info.st_dev, info.st_ino) != (row['old_dev'], row['old_ino']):
        raise RouteError('Frozen alias object identity changed')
    try:
        raw_target = os.readlink(physical)
    except OSError as error:
        raise RouteError('Frozen alias readlink failed') from error
    if raw_target != row['old_target_raw']:
        raise RouteError('Frozen alias target text changed')
    return row


def _open_ordinary_file(root: Path, relative: str):
    parts = _parts(relative)
    base = Path(root)
    _ordinary(base)
    target = base.joinpath(*parts)
    info = _ordinary(target)
    if not stat.S_ISREG(info.st_mode):
        raise RouteError('Selected material is not an ordinary file')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    try:
        descriptor = os.open(target, flags)
    except OSError as error:
        raise RouteError('Read-only open failed') from error
    actual = os.fstat(descriptor)
    if (actual.st_dev, actual.st_ino) != (info.st_dev, info.st_ino):
        os.close(descriptor)
        raise RouteError('File identity changed during open')
    return descriptor, info, target


def inspect_file(root: Path, relative: str, *, digest=False) -> dict:
    """Use only ordinary paths; never try the alias or old logical output root."""
    descriptor, info, target = _open_ordinary_file(root, relative)
    try:
        result = {'physical': str(target), 'dev': info.st_dev, 'ino': info.st_ino, 'bytes': info.st_size,
                  'mtime_ns': info.st_mtime_ns}
        if digest:
            value = hashlib.sha256()
            while block := os.read(descriptor, 1024 * 1024):
                value.update(block)
            after = os.fstat(descriptor)
            if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                    info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns):
                raise RouteError('Material changed during digest')
            result['sha256'] = value.hexdigest()
        return result
    finally:
        os.close(descriptor)


def _active_root(manifest: dict, alias: str) -> Path:
    if manifest.get('kind') != ACTIVE_KIND:
        raise RouteError('Proposal route is inactive until authorized post-move identity binding')
    row = _verify_alias(manifest, alias)
    target = Path(manifest['repository_root']).joinpath(*_parts(row['new_target']))
    root_info = _ordinary(target)
    if not stat.S_ISDIR(root_info.st_mode) or (root_info.st_dev, root_info.st_ino) != (
            row['new_root_dev'], row['new_root_ino']) or (root_info.st_dev, root_info.st_ino) != (
            row['source_root_dev'], row['source_root_ino']):
        raise RouteError('Relocated root identity mismatch')
    return target


def inspect_historical(manifest: dict, alias: str, relative: str, *, digest=False) -> dict:
    target = _active_root(manifest, alias)
    result = inspect_file(target, relative, digest=digest)
    result['alias'] = alias
    result['old_alias_identity_preserved'] = True
    result['route'] = 'NEW_PHYSICAL_TARGET_ONLY'
    return result


def inspect_logical(manifest: dict, old_target: str, relative: str, *, digest=False) -> dict:
    """Old logical target plus suffix routes through its pinned frozen alias."""
    _parts(old_target)
    matches = [row for row in manifest['aliases'] if
               '/'.join((row['source_root'], row['target_relative_suffix'])).rstrip('/') == old_target]
    if len(matches) != 1:
        raise RouteError('Old logical target is not uniquely pinned')
    return inspect_historical(manifest, matches[0]['alias'], relative, digest=digest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument('--alias')
    selector.add_argument('--old-target')
    parser.add_argument('--relative', required=True)
    parser.add_argument('--sha256', action='store_true', help='stream a read-only digest of the selected file')
    args = parser.parse_args()
    manifest = load_manifest(args.manifest, args.manifest_sha256)
    alias = args.alias
    if not alias:
        _parts(args.old_target)
        matches = [row for row in manifest['aliases'] if
                   '/'.join((row['source_root'], row['target_relative_suffix'])).rstrip('/') == args.old_target]
        if len(matches) != 1:
            raise RouteError('Old logical target is not uniquely pinned')
        alias = matches[0]['alias']
    result = inspect_historical(manifest, alias, args.relative, digest=args.sha256)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
