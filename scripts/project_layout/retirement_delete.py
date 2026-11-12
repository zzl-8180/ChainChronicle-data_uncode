"""Exact retirement deletion preparation and separately authorized future apply.

No implicit authorization. prepare is read-only outside a new evidence directory.
apply is never invoked by prepare and has no recursive deletion or resume mode.
"""
import argparse
import ctypes
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).absolute().parent


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


p = module('retirement_preservation_helpers', 'run_retirement_preservation.py')
r01 = module('retirement_r01_helpers', 'check_retirement_survivors.py')
alias = module('retirement_alias_helpers', 'check_retirement_alias.py')
BASE = 'docs/project-layout/20261108-packaging-final-ready-v1'
PHYSICAL = 'docs/project-layout/20261108-packaging-physical-v1/run-immediate-bound/'
PHYSICAL_LOCKS = {
    'source-hashes.json': 'b37141ce19ba36958e555d30da4f3e744ae6fcf9dd51a316c8bb5b09c28e33f0',
    'verify.json': '54770b9c50ed8ab88f215adf10feab07f7dee0428f1dd35c384b424404b219a3',
    'move-journal.jsonl': '2f46150f2069d369088d50d25b7109b5b37f1dd30d47afd4dff85d64d90eea76',
    'junction-summary.json': 'f573abf1437f2ad7d758c0d3aa13e280cd150d11233ac2a8bf27e0a8322643fa',
}
INHERITED_REVIEWS = {
    'docs/project-layout/20261108-packaging-physical-v1/archive-independent-review.json':
        'c40355d276685003072f1b0793186e277dbb064b590a789d4d05b22932fe0a7c',
    'docs/project-layout/20261108-packaging-physical-v1/physical-independent-review.json':
        '4324a59e52229a5682af6b4be55e018118135a30a8d65129a96475ba48c2bf80',
}
EXCLUDES = ['previous_junctions', 'directories', 'unknown_files', 'preserved_5317', 'retain_in_place_11']
DELETE_COUNT = 1607
DELETE_BYTES = 4979429886
MAINLINE = {'output/character_skills/profiles/rules.json',
            'output/character_skills/pages/_batch/campaign_latest.json'}


def require(ok, message):
    p.require(ok, message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc)


def read_bound(path, expected):
    p.no_reparse(path)
    before = p.file_meta(path)
    raw = path.read_bytes()
    require(p.file_meta(path) == before and sha(raw) == expected, 'Bound file changed/wrong SHA: ' + str(path))
    return json.loads(raw)


def dependencies():
    return {name: p.digest(HERE / name) for name in (
        'retirement_delete.py', 'run_retirement_preservation.py', 'check_retirement_survivors.py', 'check_retirement_alias.py')}


LOADED_CODE = dependencies()


def check_loaded():
    require(dependencies() == LOADED_CODE, 'Code changed after process import; start a fresh process')


def fresh_directory(repo, run_dir, kind):
    value = p.no_reparse(Path(os.path.abspath(run_dir)))
    base = p.under(repo, BASE)
    require(value.parent == base and value.name.startswith(kind + '-'), 'Use direct ' + BASE + '/' + kind + '-<unique>')
    require(base.is_dir(), 'Evidence parent must already exist')
    value.mkdir(exist_ok=False)
    return value


def physical(repo):
    for logical, expected in INHERITED_REVIEWS.items():
        read_bound(p.under(repo, logical), expected)
    loaded = {name: read_bound(p.under(repo, PHYSICAL + name), expected)
              for name, expected in PHYSICAL_LOCKS.items() if name != 'move-journal.jsonl'}
    journal = p.under(repo, PHYSICAL + 'move-journal.jsonl')
    require(p.digest(journal) == PHYSICAL_LOCKS['move-journal.jsonl'], 'Physical journal changed')
    before = loaded['source-hashes.json']
    verification = loaded['verify.json']
    require(before['full_sha256'] == p.FULL_SHA and before['overlay_sha256'] == p.OVERLAY_SHA
            and verification['status'] == 'MOVE_VERIFIED' and verification['verified'] == 5317,
            'Physical handover incomplete')
    return before


def contract(repo):
    # Exact frozen bytes establish all 6935 mappings; do not lstat the 5317
    # already-accepted targets through preservation.load_contract.
    raw = p.under(repo, p.FULL).read_bytes()
    overlay = p.under(repo, p.OVERLAY).read_bytes()
    require(sha(raw) == p.FULL_SHA and sha(overlay) == p.OVERLAY_SHA, 'Full/overlay SHA mismatch')
    return [json.loads(line) for line in raw.decode('utf-8').splitlines()]


def structure(repo, rows, before, deleted=False):
    remaining = {r['path'] for r in rows if r['disposition'] not in p.MOVE
                 and (not deleted or r['disposition'] == 'RETAIN_IN_PLACE')}
    actual = p.walk_files(repo, p.CORE + p.EXTRA_TREES) | set(p.EXTRA_FILES)
    require(len(remaining) == (11 if deleted else 1618) and actual == remaining, 'Old-tree exact remaining file set drift')
    # Inherit the bound physical/Astra 5317 acceptance, not a second full audit.
    for suffix in ('share_bundle', 'distribution', 'history-work'):
        root = p.under(repo, p.HISTORY + '/' + suffix)
        require(root.is_dir(), 'Approved archive root missing/not ordinary directory')
    summary = read_bound(p.under(repo, PHYSICAL + 'junction-summary.json'), PHYSICAL_LOCKS['junction-summary.json'])
    by_cycle = {x['cycle']: x for x in summary['entries']}
    for cycle in alias.CYCLES:
        formal = alias.formal_path(repo, cycle)
        item = alias.inspect_alias(repo, cycle, 'formal', formal, repo / alias.NEW)
        require([item['lstat_dev'], item['lstat_ino']] == by_cycle[cycle]['new_file_id'], 'Formal alias identity drift')
        previous = formal.with_name(alias.BASENAMES['previous'])
        alias.inspect_alias(repo, cycle, 'previous', previous, repo / alias.OLD, identity_only=True)
        try:
            formal.with_name(alias.BASENAMES['next']).lstat()
        except FileNotFoundError:
            pass
        else:
            raise ValueError('Unexpected next alias exists')
    for rel, expected in {**alias.BASELINE, alias.P_REL: alias.P_IDENTITY,
                          alias.HANDOFF + '/payload/manifest.json': alias.MANIFEST_IDENTITY}.items():
        path = p.under(repo, alias.NEW + '/' + rel)
        observed = p.stable_hash(path)
        require(observed['metadata']['bytes'] == expected['bytes'] and observed['sha256'] == expected['sha256'],
                'Key archive identity drift: ' + rel)
    for r in rows:
        if r['disposition'] == 'RETAIN_IN_PLACE':
            require(p.file_meta(p.under(repo, r['path'])) == before['untouched'][r['path']],
                    'RETAIN_IN_PLACE changed: ' + r['path'])


def load_pairs(repo, rows):
    proof = read_bound(p.under(repo, r01.BASE + 'repro/verified-source-pairs.json'),
                       r01.LOCKS['repro/verified-source-pairs.json'])
    term = read_bound(p.under(repo, r01.BASE + 'terminal-survivors.json'),
                      r01.LOCKS['terminal-survivors.json'])
    extra_path = p.under(repo, r01.BASE + 'retained/extra-disposition.jsonl')
    raw = extra_path.read_bytes()
    require(sha(raw) == r01.LOCKS['retained/extra-disposition.jsonl'], 'Extra evidence changed')
    extras = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
    return r01.build_pairs(rows, proof, term, extras)


def validate_gate(repo, gate, pairs, max_age_minutes=60, clock=utc):
    require(gate.get('mode') == 'archive' and gate.get('scope') == 'full1406'
            and gate.get('pairs') == gate.get('matched') == 1406 and gate.get('failed') == 0
            and gate.get('full1406_content_gate_pass') is True
            and gate.get('deletion_authorized') is False and gate.get('evidence_sha256') == r01.LOCKS,
            'Requires complete genuine archive1406 content-gate receipt')
    by_source = {x['source']: x for x in gate['results']}
    require(len(by_source) == 1406 and set(by_source) == {x['source'] for x in pairs}, 'Gate exact pair scope mismatch')
    now = clock()
    require(bool(gate.get('groups')), 'Gate has no group timestamps')
    for group in gate['groups']:
        end = dt.datetime.fromisoformat(group['finished_utc'])
        require(end.tzinfo is not None and dt.timedelta(0) <= now - end <= dt.timedelta(minutes=max_age_minutes)
                and group['failed'] == 0 and not group['stopped'], 'Gate stale, future-dated or group stopped')
    for pair in pairs:
        item = by_source[pair['source']]
        require(item['match'] and not item['source_should_keep'] and not item['fail_reason']
                and item['survivor'] == pair['archive'] and item['group'] == pair['group'],
                'Gate pair does not match exact archive mapping')
        for side, logical in (('source', pair['source']), ('survivor', pair['archive'])):
            _, observed, _ = r01.inspect(repo, logical)
            require(r01.identity(observed) == item[side + '_observed'],
                    'Content gate identity drift: ' + logical)
    return by_source


def source_record(repo, row, before, reader):
    logical = row['path']
    path = p.under(repo, logical)
    initial = p.file_meta(path)
    require(initial['nlink'] == 1 and p.identity(initial) == row['current_identity']
            and initial == before['untouched'][logical], 'DELETE source identity/single-link drift: ' + logical)
    (size, digest), observed, _ = reader.digest(logical, row['current_identity']['bytes'])
    require(size == initial['bytes'] and p.file_meta(path) == initial, 'DELETE source changed while hashing: ' + logical)
    require(not row.get('sha256') or digest == row['sha256'], 'Frozen DELETE source SHA mismatch: ' + logical)
    return dict(source=logical, metadata=initial, sha256=digest, group=r01.group_for(logical),
                reason=row['reason'], original_gate=row.get('gate', row.get('original_gate')),
                frozen_sha256=row.get('sha256'))


def compare_protection(current, expected):
    # rules/current pointer are live observations, not a global research freeze.
    require({k: v for k, v in current.items() if k not in MAINLINE}
            == {k: v for k, v in expected.items() if k not in MAINLINE}, 'Frozen/navigation protection drift')


def immutable_history(current, before):
    rebased = MAINLINE | {'AGENTS.md', 'HANDOFF.md', 'STATUS.md', 'README.md'}
    require(all(current.get(k) == value for k, value in before['protected'].items() if k not in rebased),
            'Historical P/v7/plan/binding/root-ignore protection changed')


def prepare(repo, run_dir, gate_path, gate_sha, clock=utc):
    check_loaded()
    run_dir = fresh_directory(repo, run_dir, 'prepare')
    try:
        rows = contract(repo)
        before = physical(repo)
        pairs = load_pairs(repo, rows)
        gate_path = p.no_reparse(Path(os.path.abspath(gate_path)))
        require(gate_path.is_relative_to(p.under(repo, BASE)), 'Gate must be in this final-ready evidence package')
        gate = read_bound(gate_path, gate_sha)
        gate_by_source = validate_gate(repo, gate, pairs, clock=clock)
        structure(repo, rows, before)
        protected = p.protection(repo)
        immutable_history(protected, before)
        reader = r01.Reader(repo)
        records = [source_record(repo, row, before, reader) for row in rows if row['disposition'] == 'DELETE']
        require(len(records) == DELETE_COUNT and sum(r['metadata']['bytes'] for r in records) == DELETE_BYTES,
                'Wrong DELETE count/bytes')
        for record in records:
            if record['source'] in gate_by_source:
                record['survivor'] = gate_by_source[record['source']]['survivor']
                record['survivor_observed'] = gate_by_source[record['source']]['survivor_observed']
        validate_gate(repo, gate, pairs, clock=clock)
        for record in records:
            require(p.file_meta(p.under(repo, record['source'])) == record['metadata'], 'Source changed after hashing')
        after = p.protection(repo)
        compare_protection(after, protected)
        check_loaded()
        manifest = dict(schema='retirement-delete-manifest-v1', repo=str(repo), count=DELETE_COUNT,
                        logical_bytes=DELETE_BYTES, full_sha256=p.FULL_SHA, overlay_sha256=p.OVERLAY_SHA,
                        physical_sha256=PHYSICAL_LOCKS, inherited_review_sha256=INHERITED_REVIEWS,
                        excludes=EXCLUDES, files=records)
        manifest_path = run_dir / 'delete-manifest.json'
        p.write_new(manifest_path, manifest)
        result = dict(status='PREPARED_PENDING_FINAL_USER_AUTHORIZATION', deletion_authorized=False,
                      utc=clock().isoformat(), repo=str(repo), count=DELETE_COUNT, logical_bytes=DELETE_BYTES,
                      manifest_path=str(manifest_path), manifest_sha256=p.digest(manifest_path),
                      gate_report=str(gate_path), gate_report_sha256=gate_sha,
                      physical_sha256=PHYSICAL_LOCKS, inherited_review_sha256=INHERITED_REVIEWS,
                      archive5317_content='Inherited bound physical/Astra acceptance; no full rehash/stat/scan this run',
                      code_sha256=LOADED_CODE,
                      protected=protected, mainline_after={k: v for k, v in after.items() if k in MAINLINE},
                      excludes=EXCLUDES, deleted=0,
                      limitation='Snapshot only. Future apply requires separate user authorization and a new full1406 gate plus locked per-group checks.')
        p.write_new(run_dir / 'preparation.json', result)
        return dict(status=result['status'], deleted=0, manifest_sha256=result['manifest_sha256'],
                    preparation_sha256=p.digest(run_dir / 'preparation.json'), run_dir=str(run_dir))
    except BaseException as exc:
        p.write_new(run_dir / 'prepare-failure.json', dict(status='PREPARATION_FAILED', error=repr(exc), deleted=0))
        raise


def timestamp(value):
    result = dt.datetime.fromisoformat(value)
    require(result.tzinfo is not None and result.utcoffset() == dt.timedelta(0), 'Authorization requires explicit UTC timestamps')
    return result


def authorize(repo, auth, manifest_sha, preparation_sha, preparation, run_dir, clock=utc):
    require(auth.get('authorized') is True and auth.get('action') == 'DELETE_EXACT_1607'
            and auth.get('count') == DELETE_COUNT and auth.get('repo') == str(repo), 'Missing explicit user DELETE1607 authorization')
    require(auth.get('manifest_sha256') == manifest_sha
            and auth.get('preparation_sha256') == preparation_sha
            and auth.get('gate_report_sha256') == preparation['gate_report_sha256']
            and auth.get('code_sha256') == LOADED_CODE
            and auth.get('excludes') == EXCLUDES, 'Authorization scope/bindings mismatch')
    require(isinstance(auth.get('user_confirmation_reference'), str)
            and bool(auth['user_confirmation_reference'].strip()), 'User confirmation reference required')
    run_id = auth.get('run_id', '')
    require(re.fullmatch(r'apply-[A-Za-z0-9_-]{1,80}', run_id) is not None
            and Path(os.path.abspath(run_dir)) == p.under(repo, BASE) / run_id,
            'Authorization run_id must bind the unique apply evidence directory')
    start, end = timestamp(auth['not_before_utc']), timestamp(auth['not_after_utc'])
    require(dt.timedelta(0) < end - start <= dt.timedelta(hours=2), 'Authorization window must be positive and <=2h')
    require(start <= clock() < end, 'Outside separate final deletion authorization window')
    return start, end


def auth_window(bounds, clock=utc):
    require(bounds[0] <= clock() < bounds[1], 'Deletion authorization window expired/not open')


class LockedFile:
    """Windows file handle: deny writes/deletes; source unlinks by this exact handle.

    Only used on the current approved DELETE source. External/mainline survivors
    are never locked, so their writers remain free to run.
    """
    def __init__(self, repo, logical, expected_sha, maximum, delete=False):
        require(os.name == 'nt', 'Apply requires Windows native file locking')
        import msvcrt
        from ctypes import wintypes
        self.repo, self.logical = repo, logical
        self.path = p.under(repo, logical)
        _, _, self.parents = r01.inspect(repo, logical)
        self.initial = p.file_meta(self.path)
        require(self.initial['bytes'] == maximum and (not delete or self.initial['nlink'] == 1),
                'Locked file size/link drift: ' + logical)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = self.kernel.CreateFileW
        create.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                           wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
        create.restype = wintypes.HANDLE
        handle = create(str(self.path), 0x80000000 | (0x10000 if delete else 0), 1, None,
                        3, 0x00200000 | 0x08000000, None)
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        self.kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            self.kernel.CloseHandle(handle)
            raise
        self.stream = os.fdopen(fd, 'rb')
        self.handle = handle
        self.delete_access = delete
        try:
            opened = os.fstat(self.stream.fileno())
            require(r01.common(opened) == tuple(self.initial[k] for k in ('dev', 'ino', 'bytes', 'mtime_ns', 'nlink')),
                    'Locked handle/path identity mismatch')
            h, total = hashlib.sha256(), 0
            for block in iter(lambda: self.stream.read(1024 * 1024), b''):
                total += len(block)
                require(total <= maximum, 'Locked file grew beyond bound')
                h.update(block)
            require(total == maximum and h.hexdigest() == expected_sha, 'Locked file content mismatch: ' + logical)
            require(r01.stamp(opened) == r01.stamp(os.fstat(self.stream.fileno())), 'Locked handle changed while read')
            self.sha256 = h.hexdigest()
            self.check()
        except BaseException:
            self.close()
            raise

    def check(self):
        require(p.file_meta(self.path) == self.initial, 'Locked path drift: ' + str(self.path))
        _, _, parents = r01.inspect(self.repo, self.logical)
        require(parents == self.parents, 'Locked source ancestor identity drift')
        require(r01.common(os.fstat(self.stream.fileno())) == tuple(
            self.initial[k] for k in ('dev', 'ino', 'bytes', 'mtime_ns', 'nlink')), 'Locked file ID drift')

    def unlink(self, authorize_now):
        require(self.delete_access, 'Not a delete-access source handle')
        self.check()
        from ctypes import wintypes
        disposition = ctypes.c_ubyte(1)  # FILE_DISPOSITION_INFO.DeleteFile is BOOLEAN.
        fn = self.kernel.SetFileInformationByHandle
        fn.argtypes = (wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD)
        fn.restype = wintypes.BOOL
        authorize_now()  # Last possible check immediately before the destructive API.
        if not fn(self.handle, 4, ctypes.byref(disposition), ctypes.sizeof(disposition)):
            raise ctypes.WinError(ctypes.get_last_error())
        self.close()  # Exact-handle single-file unlink completes on close.

    def close(self):
        if not self.stream.closed:
            self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def apply(repo, run_dir, manifest_path, manifest_sha, preparation_path, preparation_sha,
          authorization_path, authorization_sha, clock=utc, locker=LockedFile, fresh_gate=None):
    """Separately authorized future action. Never called in preparation work."""
    check_loaded()
    require(bool(authorization_path) and bool(authorization_sha), 'Independent final user authorization file and CLI SHA required')
    manifest = read_bound(manifest_path, manifest_sha)
    preparation = read_bound(preparation_path, preparation_sha)
    auth = read_bound(authorization_path, authorization_sha)
    require(preparation['manifest_sha256'] == manifest_sha and preparation['repo'] == str(repo)
            and preparation['code_sha256'] == LOADED_CODE and preparation['deletion_authorized'] is False,
            'Preparation binding mismatch')
    bounds = authorize(repo, auth, manifest_sha, preparation_sha, preparation, run_dir, clock)
    run_dir = fresh_directory(repo, run_dir, 'apply')  # Replay consumes this unique run ID even on failure.
    done, active = 0, None
    with (run_dir / 'delete-journal.jsonl').open('x', encoding='utf-8', newline='\n') as log:
        try:
            p.event(log, dict(status='AUTHORIZED_RUN_START', authorization_sha256=authorization_sha,
                              manifest_sha256=manifest_sha, preparation_sha256=preparation_sha))
            rows = contract(repo)
            before = physical(repo)
            structure(repo, rows, before)
            compare_protection(p.protection(repo), preparation['protected'])
            immutable_history(p.protection(repo), before)
            require(manifest['schema'] == 'retirement-delete-manifest-v1' and manifest['repo'] == str(repo)
                    and manifest['full_sha256'] == p.FULL_SHA and manifest['overlay_sha256'] == p.OVERLAY_SHA
                    and manifest['physical_sha256'] == PHYSICAL_LOCKS
                    and manifest['inherited_review_sha256'] == INHERITED_REVIEWS and manifest['excludes'] == EXCLUDES,
                    'Manifest contract mismatch')
            by_source = {x['source']: x for x in manifest['files']}
            deleted_rows = {x['path']: x for x in rows if x['disposition'] == 'DELETE'}
            require(len(by_source) == manifest['count'] == DELETE_COUNT and set(by_source) == set(deleted_rows)
                    and manifest['logical_bytes'] == DELETE_BYTES
                    and sum(x['metadata']['bytes'] for x in by_source.values()) == DELETE_BYTES,
                    'Manifest is not exact frozen1607 DELETE set')
            pairs = load_pairs(repo, rows)
            auth_window(bounds, clock)
            gate = fresh_gate(repo) if fresh_gate else r01.run(repo, 'archive', None)
            p.write_new(run_dir / 'fresh-archive1406.json', gate)
            gate_by_source = validate_gate(repo, gate, pairs, clock=clock)
            reader = r01.Reader(repo)
            for logical, row in deleted_rows.items():
                observed = source_record(repo, row, before, reader)
                require(observed['metadata'] == by_source[logical]['metadata']
                        and observed['sha256'] == by_source[logical]['sha256'], 'Prepared source drift: ' + logical)
            auth_window(bounds, clock)
            require(all(x['group'] == r01.group_for(x['source']) for x in by_source.values()), 'Forged group mapping')
            pair_by_source = {x['source']: x for x in pairs}
            for group in sorted({x['group'] for x in by_source.values()}):
                check_loaded()
                auth_window(bounds, clock)
                group_sources = [x for x in by_source.values() if x['group'] == group]
                group_pairs = [x for x in pairs if x['group'] == group]
                group_reader = r01.Reader(repo)  # New cache per group, never reused for per-item checks.
                group_results = [r01.check_pair(group_reader, pair, 'archive') for pair in group_pairs]
                require(all(x['match'] and x['survivor_observed'] == gate_by_source[x['source']]['survivor_observed']
                            for x in group_results), 'Group source/survivor drift; affected group kept')
                group_survivors = {}
                for pair in group_pairs:
                    _, state, parents = r01.inspect(repo, pair['archive'])
                    require(r01.identity(state) == gate_by_source[pair['source']]['survivor_observed'],
                            'Group survivor drift after read')
                    group_survivors[pair['archive']] = (r01.identity(state), parents)
                p.event(log, dict(status='GROUP_VERIFIED_OBSERVATION', group=group, pairs=len(group_pairs),
                                  source_files=len(group_sources), results=group_results))
                for record in group_sources:
                    active = record['source']
                    auth_window(bounds, clock)
                    with locker(repo, active, record['sha256'], record['metadata']['bytes'], delete=True) as source:
                        require(source.initial == record['metadata'], 'Source metadata drift before unlink')
                        pair = pair_by_source.get(active)
                        snapshot = None
                        if pair:
                            # Source SHA comes from its locked DELETE-access handle;
                            # reopening it via Python can violate Windows sharing.
                            reader = r01.Reader(repo)
                            (size, content), seen, parents = reader.digest(pair['archive'], pair['bytes'])
                            require(size == pair['bytes'] and content == pair['sha256']
                                    and source.sha256 == pair['sha256']
                                    and seen == gate_by_source[active]['survivor_observed'], 'Immediate pair content/identity drift')
                            snapshot = (pair['archive'], seen, parents)
                        source.check()
                        if snapshot:
                            _, state, parents = r01.inspect(repo, snapshot[0])
                            require((r01.identity(state), parents) == snapshot[1:], 'Survivor changed across final pair')
                        auth_window(bounds, clock)
                        p.event(log, dict(status='INTENT', source=active, group=group,
                                          metadata=source.initial, sha256=source.sha256,
                                          survivor_snapshot=snapshot,
                                          method='Windows FILE_DISPOSITION_INFO exact locked file handle'))
                        auth_window(bounds, clock)
                        source.check()
                        if snapshot:
                            _, state, parents = r01.inspect(repo, snapshot[0])
                            require((r01.identity(state), parents) == snapshot[1:], 'Survivor drift after WAL; source kept')
                        source.unlink(lambda: auth_window(bounds, clock))
                    try:
                        p.under(repo, active).lstat()
                    except FileNotFoundError:
                        pass
                    else:
                        raise ValueError('Source still present after handle unlink')
                    done += 1
                    p.event(log, dict(status='DONE', source=active, sha256=record['sha256'], deleted=done))
                for logical, expected in group_survivors.items():
                    _, state, parents = r01.inspect(repo, logical)
                    require((r01.identity(state), parents) == expected, 'Group-end survivor drift; remaining kept')
                compare_protection(p.protection(repo), preparation['protected'])
            check_loaded()
            structure(repo, rows, before, deleted=True)
            compare_protection(p.protection(repo), preparation['protected'])
            p.event(log, dict(status='DELETE_COMPLETE', deleted=done, directories_deleted=0, junctions_changed=0))
            result = dict(status='DELETE_COMPLETE', deleted=done, directories_deleted=0, junctions_changed=0)
            p.write_new(run_dir / 'result.json', result)
            return result
        except BaseException as exc:
            observed = None
            if active:
                try:
                    path = p.under(repo, active)
                    observed = dict(path=active, exists=os.path.lexists(path),
                                    metadata=p.file_meta(path) if os.path.lexists(path) else None)
                except Exception as observation_error:
                    observed = dict(path=active, error=repr(observation_error))
            p.event(log, dict(status='PAUSED', confirmed_deleted=done, current_source=active,
                              observed=observed, error=repr(exc), resume_allowed=False))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', default='prepare', choices=('prepare', 'apply'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--gate-report', type=Path)
    parser.add_argument('--gate-report-sha256')
    for name in ('manifest', 'preparation', 'authorization'):
        parser.add_argument('--' + name, type=Path)
        parser.add_argument('--' + name + '-sha256')
    args = parser.parse_args()
    repo = p.no_reparse(args.repo)
    if args.mode == 'prepare':
        require(args.gate_report is not None and bool(args.gate_report_sha256), 'Explicit current archive1406 report and SHA required')
        result = prepare(repo, args.run_dir, args.gate_report, args.gate_report_sha256)
    else:
        require(all(getattr(args, name) for name in ('manifest', 'manifest_sha256', 'preparation',
                    'preparation_sha256', 'authorization', 'authorization_sha256')), 'Apply requires all explicit bound files and hashes')
        result = apply(repo, args.run_dir, args.manifest, args.manifest_sha256,
                       args.preparation, args.preparation_sha256, args.authorization, args.authorization_sha256)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps(dict(status='REFUSED_OR_PAUSED', error=str(error)), ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
