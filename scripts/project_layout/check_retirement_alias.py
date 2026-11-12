"""Read-only, per-entry C14-C18 retirement junction/content checks.

Select --cycle C14 (formal), --alias-path ABSOLUTE_APPROVED_ALIAS, or --all.
New target requires --expected-target new --new-target ABSOLUTE_APPROVED_ROOT.
Only previous aliases accept --identity-only: this is NOT a content pass.
JSON goes to stdout. No mutation, historical verifier, business import or fallback.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys

OLD = 'output/share_bundle'
NEW = 'operations/history/retired-packaging/20261108/share_bundle'
HANDOFF = '20261104-mechanism-first-handoff-r1'
P_REL = '20261025-character-tools/isolated 中文 space/scripts/release/build_explicit_bundle.py'
P_IDENTITY = {'bytes': 12340, 'sha256': 'b74e4681d492fbf0f7258e138669abf91bba23c27e091f865deae428ec4e9ee2'}
MANIFEST_IDENTITY = {'bytes': 45882, 'sha256': 'ae3a591d1dd35be221294a6418ca7455c9ec1184f247192cfee6c0f80bdef051'}
CYCLES = {'C14': '20261103', 'C15': '20261103', 'C16': '20261104',
          'C17': '20261106', 'C18': '20261106'}
BASENAMES = {'formal': 'share_bundle', 'next': 'share_bundle.retirement-next-20261108',
             'previous': 'share_bundle.retirement-previous-20261108'}
# Pinned from the original read-only current-junction-check.json. Recreating an
# old junction invalidates this identity and requires a separate reviewed baseline.
OLD_IDS = {'C14': (1926460150158795819, 2251799816698096),
           'C15': (1926460150158795819, 844424933172226),
           'C16': (1926460150158795819, 1125899909957636),
           'C17': (1926460150158795819, 562949956553455),
           'C18': (1926460150158795819, 562949956583989)}
# These five identities are copied unchanged from retained-identity-baseline.json.
BASELINE = {
    HANDOFF + '/README.md': {'bytes': 448, 'sha256': '146074111d23e14f2e6febaa12d7c8239ea44e2df8afe6bb052d0d73c5588af9'},
    HANDOFF + '/release_manifest.json': {'bytes': 1538, 'sha256': '924082bb4dd319f55d6605ba05b372308a21a44d11bf1e4aea06c90149964e70'},
    HANDOFF + '/isolation_receipt.json': {'bytes': 985, 'sha256': '0c3d07cc34bc5ae69eff5adcf3d85c8b847530bdf8a2c026476a5b56db96eb7a'},
    'cc_skill_values_20261021/manifest.json': {'bytes': 1957351, 'sha256': '9492d8c53935fe395aca80f741a04e3c740f4c270e022dd70c474622cb4b4045'},
    'cc_skill_values_20261022/manifest.json': {'bytes': 1960840, 'sha256': '424aaf23bd3ccc9c37f8c802243436872a8be2eed1d537d3a170fdffe84d67b2'},
}
FROZEN = {
    'P_preservation.json': '10e5b3d71d990b22fa8c53c595cc0be439707fb1dc4a36c589e537034724998f',
    'protection_manifest_v7.json': '2db5e6fd3b277884e4de47603760c22deb8db5ccdf6b8bbb8b235c1326b1de17',
}
SCOPE = ('Read-only approved alias identity and scoped retained content; no owner inactivity, '
         'relocation, NTFS rename/exchange, ZIP replay, complete historical postcheck, '
         'production or deletion authorization assertion. Check/open races require the owner window.')


def normalized(path):
    value = os.fspath(path)
    if value.startswith('\\\\?\\'):
        value = value[4:]
    return os.path.normcase(os.path.abspath(value))


def file_identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def ordinary(path, directory):
    info = os.lstat(path)
    if getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError('Unapproved reparse point: ' + str(path))
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ValueError('Unexpected file type: ' + str(path))
    return info


def ordinary_ancestors(path):
    # Top down: never lstat a descendant through an unchecked parent reparse.
    identities = []
    for current in reversed((path, *path.parents)):
        info = ordinary(current, directory=True)
        identities.append((str(current), info.st_dev, info.st_ino))
    return identities


def formal_path(repo, cycle):
    return repo / f'work/{cycle.lower()}_delivery_{CYCLES[cycle]}/impl/isolation_input/output/share_bundle'


def selected_aliases(repo, cycle=None, alias_path=None, all_entries=False):
    if all_entries and (cycle is not None or alias_path is not None):
        raise ValueError('--all cannot be combined with --cycle/--alias-path')
    if cycle is not None and cycle not in CYCLES:
        raise ValueError('Unknown cycle')
    if alias_path is None:
        return [(c, 'formal', formal_path(repo, c)) for c in ([cycle] if cycle else CYCLES)]
    if not alias_path.is_absolute():
        raise ValueError('--alias-path must be absolute')
    for candidate_cycle in CYCLES:
        for role, basename in BASENAMES.items():
            approved = formal_path(repo, candidate_cycle).with_name(basename)
            if normalized(alias_path) == normalized(approved):
                if cycle is not None and cycle != candidate_cycle:
                    raise ValueError('Alias directory does not match --cycle')
                return [(candidate_cycle, role, approved)]
    raise ValueError('Alias is not one of the five cycles / three approved same-parent basenames')


def approved_target(repo, mode, explicit_new, identity_only):
    if mode == 'old':
        if explicit_new is not None:
            raise ValueError('--new-target is only valid with --expected-target new')
        target = repo / OLD
    else:
        if explicit_new is None or not explicit_new.is_absolute():
            raise ValueError('new mode requires --new-target ABSOLUTE_APPROVED_ROOT')
        target = repo / NEW
        if normalized(explicit_new) != normalized(target):
            raise ValueError('New target differs from approved full-scope archive mapping')
    if not identity_only:
        ordinary_ancestors(target)
        if normalized(target.resolve(strict=True)) != normalized(target):
            raise ValueError('Target escaped approved physical root')
    return target


def inspect_alias(repo, cycle, role, alias, target, identity_only=False):
    parents = ordinary_ancestors(alias.parent)
    observed = os.lstat(alias)
    tag = getattr(observed, 'st_reparse_tag', 0)
    if (not getattr(observed, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            or tag != 0xA0000003 or not stat.S_ISDIR(observed.st_mode)):
        raise ValueError('Alias is not a directory mount-point reparse: ' + str(alias))
    link = os.readlink(alias)
    if normalized(link) != normalized(target):
        raise ValueError('Unexpected exact target at ' + str(alias) + ': ' + link)
    old_identity = (observed.st_dev, observed.st_ino) == OLD_IDS[cycle]
    if (identity_only or normalized(target) == normalized(repo / OLD)) and not old_identity:
        raise ValueError('Original old junction file ID changed: ' + str(alias))
    return {'cycle': cycle, 'role': role, 'path': str(alias), 'observed_target_exact': link,
            'expected_target': str(target), 'reparse_tag': hex(tag),
            'lstat_dev': observed.st_dev, 'lstat_ino': observed.st_ino,
            'parent_identity_sha256': hashlib.sha256(json.dumps(parents).encode()).hexdigest(),
            'original_old_file_id_matches': old_identity}


def safe_relative(rel):
    path = PurePosixPath(rel)
    if (not rel or path.is_absolute() or '..' in path.parts or '\\' in rel
            or ':' in rel or path.as_posix() != rel):
        raise ValueError('Unsafe retained relative path: ' + rel)
    return path


def retained_path(alias, target, rel, directory=False):
    relative = safe_relative(rel)
    current = alias
    for index, part in enumerate(relative.parts):
        current = current / part
        ordinary(current, directory=index < len(relative.parts) - 1 or directory)
    # The one approved consumer junction is the only allowed indirection.
    if normalized(current.resolve(strict=True)) != normalized(target / Path(rel)):
        raise ValueError('Retained path escaped exact target or returned to old root: ' + str(current))
    return current


def strict_tree_files(alias, target, rel):
    directory = retained_path(alias, target, rel, directory=True)
    files = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            child = rel + '/' + entry.name
            # lstat at this level is safe: every ancestor was checked above.
            info = os.lstat(alias / child)
            if getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError('Nested retained reparse: ' + str(alias / child))
            if stat.S_ISDIR(info.st_mode):
                files.update(strict_tree_files(alias, target, child))
            elif stat.S_ISREG(info.st_mode):
                retained_path(alias, target, child)
                files.add(child)
            else:
                raise ValueError('Unexpected retained file type: ' + str(alias / child))
    return files


def validate_content(alias, target, mode):
    # All 142 distinct content reads retain the lexical alias spelling.
    # Never resolve a candidate before read_bytes: that would bypass the alias.
    reads = []

    def read(rel, expected):
        path = retained_path(alias, target, rel)
        raw = path.read_bytes()
        actual = file_identity(raw)
        if actual != expected:
            raise ValueError('Content identity mismatch through alias: ' + str(path))
        reads.append({'relative_path': rel, **actual})
        return raw

    manifest_rel = HANDOFF + '/payload/manifest.json'
    manifest = json.loads(read(manifest_rel, MANIFEST_IDENTITY))
    members = manifest['files']
    if len(members) != 135 or len({r.casefold() for r in members}) != 135:
        raise ValueError('Frozen payload must have 135 distinct members')
    expected_tree = {HANDOFF + '/payload/' + str(safe_relative(rel)) for rel in members}
    expected_tree |= {manifest_rel} | {rel for rel in BASELINE if rel.startswith(HANDOFF + '/')}
    actual_tree = strict_tree_files(alias, target, HANDOFF)
    permitted_extra = {HANDOFF + '/mechanism_first_handoff_r1.zip'} if mode == 'old' else set()
    if not expected_tree <= actual_tree or actual_tree - expected_tree - permitted_extra:
        raise ValueError('Research retained-file set mismatch through alias')
    for rel, expected in members.items():
        read(HANDOFF + '/payload/' + rel, expected)
    for rel, expected in BASELINE.items():
        raw = read(rel, expected)
        if not rel.startswith(HANDOFF + '/'):
            json.loads(raw)  # Historical manifest identity evidence, not ZIP recovery.
    read(P_REL, P_IDENTITY)
    if len(reads) != 142 or len({r['relative_path'] for r in reads}) != 142:
        raise ValueError('Incomplete per-alias content read coverage')
    return {'status': 'CONTENT_PASS', 'content_read_via_alias': str(alias),
            'payload_members_hashed': len(members), 'research_retained_files': len(expected_tree),
            'outer_research_files_hashed': 3, 'recovery_manifests_hashed': 2,
            'p_source': P_IDENTITY, 'distinct_files_hashed': len(reads),
            'logical_bytes_hashed': sum(row['bytes'] for row in reads),
            'read_set_sha256': hashlib.sha256(json.dumps(sorted(reads, key=lambda r: r['relative_path']),
                    ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}


def check(repo, mode='old', explicit_new=None, cycle=None, alias_path=None,
          all_entries=False, identity_only=False):
    repo = repo.absolute()
    selected = selected_aliases(repo, cycle, alias_path, all_entries)
    if identity_only:
        if len(selected) != 1 or selected[0][1] != 'previous' or mode != 'old':
            raise ValueError('--identity-only is limited to one approved previous alias in old mode')
    elif any(role == 'previous' for _, role, _ in selected):
        raise ValueError('previous is disabled evidence: use --identity-only; never claim CONTENT_PASS')
    if any(role == 'next' for _, role, _ in selected) and mode != 'new':
        raise ValueError('next alias must point to approved new target')
    target = approved_target(repo, mode, explicit_new, identity_only)
    frozen = []
    if not identity_only:
        frozen_root = repo / 'output/storage_retention/recycle_g1_20261027'
        ordinary_ancestors(frozen_root)
        for rel, digest in FROZEN.items():
            ordinary(frozen_root / rel, directory=False)
            actual = file_identity((frozen_root / rel).read_bytes())
            if actual['sha256'] != digest:
                raise ValueError('Frozen P/v7 manifest changed: ' + rel)
            frozen.append({'relative_path': rel, **actual})
    aliases = []
    for selected_cycle, role, alias in selected:
        row = inspect_alias(repo, selected_cycle, role, alias, target, identity_only)
        if identity_only:
            try:
                os.lstat(formal_path(repo, selected_cycle))
            except FileNotFoundError:
                pass
            else:
                raise ValueError('previous identity-only is for the first-rename gap; formal must be absent')
        if identity_only:
            row.update(status='IDENTITY_PASS', content_checked=False,
                       distinct_files_hashed=0, target_content_read=False)
        else:
            row.update(validate_content(alias, target, mode), content_checked=True)
        after = inspect_alias(repo, selected_cycle, role, alias, target, identity_only)
        if any(row[key] != value for key, value in after.items()):
            raise ValueError('Alias or parent identity changed during verification: ' + str(alias))
        row['alias_and_parent_identity_rechecked_after_reads'] = True
        aliases.append(row)
    return {'status': 'IDENTITY_PASS' if identity_only else 'CONTENT_PASS',
            'expected_target_mode': mode, 'target': str(target), 'aliases_checked': len(aliases),
            'aliases': aliases, 'frozen_storage_manifests': frozen, 'scope': SCOPE,
            'deleted': 0, 'moved': 0, 'junctions_changed': 0}


def readonly(event, values):
    if event == 'open' and len(values) > 2 and isinstance(values[2], int):
        if values[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise RuntimeError('Read-only checker refused write')
    if event in {'os.remove', 'os.rmdir', 'os.rename', 'os.symlink', 'os.link', 'os.mkdir',
                 'os.chmod', 'os.chown', 'os.truncate', 'os.utime', 'os.system',
                 'os.startfile', 'subprocess.Popen'}:
        raise RuntimeError('Read-only checker refused mutation/process: ' + event)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--cycle', choices=list(CYCLES))
    parser.add_argument('--alias-path', type=Path)
    parser.add_argument('--all', action='store_true', dest='all_entries')
    parser.add_argument('--expected-target', choices=['old', 'new'], default='old')
    parser.add_argument('--new-target', type=Path)
    parser.add_argument('--identity-only', action='store_true')
    args = parser.parse_args()
    sys.addaudithook(readonly)
    try:
        result = check(args.repo, args.expected_target, args.new_target, args.cycle,
                       args.alias_path, args.all_entries, args.identity_only)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        result = {'status': 'FAIL_ALIAS_CHECK', 'error': str(error), 'scope': SCOPE,
                  'deleted': 0, 'moved': 0, 'junctions_changed': 0}
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
