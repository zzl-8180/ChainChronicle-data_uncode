"""Explicit, allowlisted source mapping for isolated reader preparation.

No map is activated on import. The supplied manifest must be the reviewed S5
JSONL; destination_root may point at a simulation or a later approved location.
"""
from pathlib import Path, PurePosixPath
import json
import hashlib
import os
import re
import stat

OLD_ROOT = '其他人的参考/CC解包数据_给GPT_20261027/claude_cc_site_pages/'
NEW_ROOT = 'projects/reader/data/reference_sources/cc_20261027/'
FROZEN_SOURCE_ROOT = r'E:\代码项目\锁链战记数据解包\其他人的参考\CC解包数据_给GPT_20261027\claude_cc_site_pages'
COUNT = 2234
MANIFEST_SHA256 = 'a133fd20fff003cfcb9e0a71ce15da0ecb0c442dc6b1bf8d98f062c45c3f14fd'


def _relative(value):
    if not isinstance(value, str) or not value or any(c in value for c in ('\\', '%', '\x00', '?', '#')):
        raise ValueError('ambiguous source path')
    if value.startswith('/') or re.match(r'^[A-Za-z]:', value):
        raise ValueError('absolute source path')
    parts = value.split('/')
    if any(p in ('', '.', '..') or ':' in p for p in parts):
        raise ValueError('invalid source path segment')
    if PurePosixPath(value).as_posix() != value:
        raise ValueError('noncanonical source path')
    return value


def _safe_file(path):
    # No resolve(): inspect every existing ancestor before opening the file.
    absolute = Path(os.path.abspath(path))
    for component in reversed((absolute, *absolute.parents)):
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('reparse point in destination path')
    if not stat.S_ISREG(absolute.lstat().st_mode):
        raise ValueError('source target is not a regular file')
    return absolute


class ReferenceSourceMap:
    def __init__(self, destination_root, members):
        self.destination_root = Path(os.path.abspath(destination_root))
        self.members = frozenset(members)

    @classmethod
    def from_manifest(cls, manifest_path, destination_root):
        members = set()
        raw = Path(manifest_path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
            raise ValueError('untrusted S5 manifest identity')
        for line in raw.decode('utf-8-sig').splitlines():
            row = json.loads(line)
            if row.get('action') != 'REHOME':
                continue
            source, target = row.get('path'), row.get('target')
            if not isinstance(source, str) or not source.startswith(OLD_ROOT):
                raise ValueError('unexpected source root')
            relative = _relative(source[len(OLD_ROOT):])
            if target != NEW_ROOT + relative:
                raise ValueError('source/target mapping differs')
            if relative != 'index_unpack.html' and not re.fullmatch(r'cards/[^/]+/unpack\.html', relative):
                raise ValueError('unexpected allowlist member')
            if relative in members:
                raise ValueError('duplicate allowlist member')
            members.add(relative)
        if len(members) != COUNT or 'index_unpack.html' not in members:
            raise ValueError('incomplete allowlist')
        return cls(destination_root, members)

    def resolve_from_root(self, source_root, reference):
        if not isinstance(source_root, str) or source_root != FROZEN_SOURCE_ROOT:
            raise ValueError('untrusted frozen source root')
        return self.resolve(reference)

    def resolve(self, reference):
        if not isinstance(reference, str) or reference.count('#') > 1:
            raise ValueError('ambiguous reference fragment')
        file_part, marker, fragment = reference.partition('#')
        relative = _relative(file_part)
        if marker and (not fragment or any(c in fragment for c in ('#', '\\', '%', '\x00', '?'))):
            raise ValueError('ambiguous reference fragment')
        if relative not in self.members:
            raise ValueError('source is not in allowlist')
        path = _safe_file(self.destination_root.joinpath(*relative.split('/')))
        return path, ('#' + fragment if marker else '')
