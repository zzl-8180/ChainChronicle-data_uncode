"""Bound, fail-closed preservation moves. No deletion, junction changes or fallback."""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys

FULL = 'docs/project-layout/20261108-packaging-full-retirement-v1/full-disposition.jsonl'
FULL_SHA = '274c6cd5602b591047ce2b2c907b4e5d9bb33ff55b190b0bb8678ec586e82ef1'
OVERLAY = 'docs/project-layout/20261108-packaging-runtime-ready-v1/execution-overlay.json'
OVERLAY_SHA = '6f8d35eb2be4551807148921c4eb7372309f21544ad0498b90a31e634e44225f'
HISTORY = 'operations/history/retired-packaging/20261108'
EVIDENCE = 'docs/project-layout/20261108-packaging-physical-v1'
CORE = ['output/share_bundle', 'projects/distribution', 'scripts/release'] + [
    'work/' + x for x in ('delivery_20261016', 'repro_20261016', 'review2_20261016',
                         'review_20261016', 'review_20261017', 'review_20261017_r1')]
EXTRA_TREES = ['output/20261016-reproducibility-audit',
               'output/character_skills/share_manifest_20261021',
               'work/mechanism_first_handoff_20261104']
EXTRA_FILES = ['docs/tasks/' + x + '.md' for x in (
    '20261016-reproducibility-audit', '20261025-clean-release-reproduction',
    '20261104-mechanism-first-handoff')]
MOVE = {'ARCHIVE_HISTORY', 'REHOME_BUSINESS'}
IDENTITY = ('bytes', 'mtime_ns', 'dev', 'ino', 'nlink')
# User amended the start to immediately after inventory completion; observed UTC.
OPEN = dt.datetime(2026, 11, 8, 4, 47, 51, tzinfo=dt.timezone.utc)
CLOSE = dt.datetime(2026, 11, 8, 6, tzinfo=dt.timezone.utc)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def utc():
    return dt.datetime.now(dt.timezone.utc)


def window(clock=utc):
    now = clock()
    require(OPEN <= now < CLOSE, 'Outside authorized UTC window: ' + now.isoformat())


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def metadata(s):
    return dict(bytes=s.st_size, mtime_ns=s.st_mtime_ns, dev=s.st_dev,
                ino=s.st_ino, nlink=s.st_nlink, mode=s.st_mode,
                attributes=getattr(s, 'st_file_attributes', 0), ctime_ns=s.st_ctime_ns)


def identity(m):
    return {k: m[k] for k in IDENTITY}


def no_reparse(path):
    """Check lexical absolute ancestors before any resolve/open; missing suffix is allowed."""
    path = Path(os.path.abspath(path))
    for p in reversed((path, *path.parents)):
        try:
            s = p.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(s.st_mode) and not (
            getattr(s, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT),
            'Reparse/symlink refused: ' + str(p))
        if p != path:
            require(stat.S_ISDIR(s.st_mode), 'Non-directory ancestor: ' + str(p))
    return path


def under(repo, relative):
    p = PurePosixPath(relative)
    require(bool(relative) and p.as_posix() == relative and not p.is_absolute()
            and '..' not in p.parts and '\\' not in relative and ':' not in relative,
            'Noncanonical relative path: ' + str(relative))
    result = no_reparse(repo / relative)
    require(result.is_relative_to(repo), 'Path outside repository: ' + str(result))
    return result


def file_meta(path):
    no_reparse(path)
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode), 'Not ordinary file: ' + str(path))
    return metadata(s)


def stable_hash(path):
    before = file_meta(path)
    with path.open('rb') as f:
        first = metadata(os.fstat(f.fileno()))
        require(identity(first) == identity(before), 'Open identity changed: ' + str(path))
        h = hashlib.sha256()
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
        last = metadata(os.fstat(f.fileno()))
    after = file_meta(path)
    require(first == last and before == after, 'Changed while hashing: ' + str(path))
    return {'metadata': before, 'sha256': h.hexdigest()}


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        f.flush()
        os.fsync(f.fileno())


def event(f, value):
    value['utc'] = utc().isoformat()
    f.write(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n')
    f.flush()
    os.fsync(f.fileno())


def load_contract(repo):
    full = under(repo, FULL)
    overlay = under(repo, OVERLAY)
    full_raw, overlay_raw = full.read_bytes(), overlay.read_bytes()
    require(hashlib.sha256(full_raw).hexdigest() == FULL_SHA, 'Frozen full table SHA mismatch')
    require(hashlib.sha256(overlay_raw).hexdigest() == OVERLAY_SHA, 'Approved overlay SHA mismatch')
    rows = [json.loads(line) for line in full_raw.decode('utf-8').splitlines()]
    require(len(rows) == 6935 and len({r['path'] for r in rows}) == 6935, 'Wrong full scope')
    counts = collections.Counter(r['disposition'] for r in rows)
    require(counts == {'ARCHIVE_HISTORY': 5171, 'REHOME_BUSINESS': 146,
                       'DELETE': 1607, 'RETAIN_IN_PLACE': 11}, 'Wrong dispositions')
    override = json.loads(overlay_raw)['identity_changes']
    require(len(override) == 1 and override[0]['path'] == 'projects/distribution/README.md',
            'Unexpected overlay')
    for r in rows:
        under(repo, r['path'])
        if r['path'] == override[0]['path']:
            r['current_identity'] = override[0]['execution_identity']
            r['overlay_sha256'] = override[0]['sha256']
        require(any(r['path'].startswith(x + '/') for x in CORE + EXTRA_TREES)
                or r['path'] in EXTRA_FILES, 'Unapproved source root: ' + r['path'])
        if r['disposition'] in MOVE:
            require(r['target'].startswith(HISTORY + '/'), 'Unapproved target root')
            under(repo, r['target'])
    targets = [r['target'] for r in rows if r['disposition'] in MOVE]
    require(len(set(x.casefold() for x in targets)) == 5317, 'Target collision')
    return rows


def walk_files(repo, roots):
    found = set()
    for rel in roots:
        root = under(repo, rel)
        require(root.is_dir(), 'Missing approved directory: ' + rel)
        stack = [root]
        while stack:
            parent = stack.pop()
            no_reparse(parent)
            with os.scandir(parent) as entries:
                for entry in entries:
                    p = no_reparse(Path(entry.path))
                    s = p.lstat()
                    if stat.S_ISDIR(s.st_mode):
                        stack.append(p)
                    else:
                        require(stat.S_ISREG(s.st_mode), 'Unexpected object: ' + str(p))
                        found.add(p.relative_to(repo).as_posix())
    return found


def inventory(repo, rows):
    core = walk_files(repo, CORE)
    extra = walk_files(repo, EXTRA_TREES) | set(EXTRA_FILES)
    expected = {r['path'] for r in rows}
    require(len(core) == 6788 and len(extra) == 147 and core | extra == expected,
            'Enumeration drift: missing=' + repr(sorted(expected - (core | extra)))
            + ' added=' + repr(sorted((core | extra) - expected)))


def current_check(repo, rows):
    inventory(repo, rows)
    for r in rows:
        m = file_meta(under(repo, r['path']))
        require(identity(m) == r['current_identity'], 'Frozen identity drift: ' + r['path'])
        if r['disposition'] in MOVE:
            target = under(repo, r['target'])
            require(not os.path.lexists(target), 'Target already exists: ' + str(target))
            parent = target.parent
            while not parent.exists():
                parent = parent.parent
            require(parent.stat().st_dev == m['dev'] == repo.stat().st_dev,
                    'Not same repository volume: ' + r['path'])


def protection(repo):
    files = ['AGENTS.md', 'HANDOFF.md', 'STATUS.md', 'README.md', '.gitignore',
             'output/character_skills/profiles/rules.json',
             'output/character_skills/pages/_batch/campaign_latest.json',
             'output/storage_retention/recycle_g1_20261027/P_preservation.json',
             'output/storage_retention/recycle_g1_20261027/protection_manifest_v7.json']
    fixed = ['10e5b3d71d990b22fa8c53c595cc0be439707fb1dc4a36c589e537034724998f',
             '2db5e6fd3b277884e4de47603760c22deb8db5ccdf6b8bbb8b235c1326b1de17']
    for name, sha in zip(files[-2:], fixed):
        require(stable_hash(under(repo, name))['sha256'] == sha, 'P/v7 changed: ' + name)
    for cycle in ('c14_c15_20261104', 'c16_20261106', 'c17_c18_20261106', 'c19_20261107'):
        base = 'output/storage_retention/cycle_closeout_' + cycle
        plan, binding = base + '/plan.json', base + '/plan_binding.json'
        declared = json.loads(under(repo, binding).read_bytes())
        require(stable_hash(under(repo, plan))['sha256'] == declared['plan_sha256'],
                'Plan binding mismatch: ' + plan)
        files += [plan, binding]
    return {name: stable_hash(under(repo, name)) for name in files}


def evidence_dir(repo, run_dir, create=False):
    run_dir = no_reparse(Path(os.path.abspath(run_dir)))
    base = under(repo, EVIDENCE)
    require(run_dir.is_relative_to(base), 'Run directory outside physical evidence root')
    parts = run_dir.relative_to(base).parts
    require(len(parts) == 1 and parts[0].startswith('run'), 'Use a fresh physical-v1/run* directory')
    if create:
        run_dir.mkdir(exist_ok=False)
    require(run_dir.is_dir(), 'Run directory missing')
    return run_dir


def preflight(repo, run_dir):
    rows = load_contract(repo)
    current_check(repo, rows)
    require(not os.path.lexists(under(repo, HISTORY)), 'History root already exists')
    protected = protection(repo)
    hashes = {}
    held = {}
    for r in rows:
        path = under(repo, r['path'])
        if r['disposition'] in MOVE:
            value = stable_hash(path)
            require(identity(value['metadata']) == r['current_identity'], 'Hash source drift: ' + r['path'])
            if 'overlay_sha256' in r:
                require(value['sha256'] == r['overlay_sha256'], 'Overlay content drift')
            hashes[r['path']] = dict(target=r['target'], **value)
        else:
            held[r['path']] = file_meta(path)
    current_check(repo, rows)
    require(protected == protection(repo), 'Protection changed during preflight')
    result = dict(status='PREFLIGHT_READY', utc=utc().isoformat(), repo=str(repo),
                  full_sha256=FULL_SHA, overlay_sha256=OVERLAY_SHA,
                  tool_sha256=digest(Path(__file__)), preserved=hashes, untouched=held,
                  protected=protected, counts=dict(preserved=len(hashes), untouched=len(held)),
                  limitation='No deletion or alias authorization; parent owns activity/time approval.')
    run_dir = evidence_dir(repo, run_dir, create=True)
    path = run_dir / 'source-hashes.json'
    write_new(path, result)
    return dict(status='PREFLIGHT_READY', source_hashes=str(path), sha256=digest(path))


def load_baseline(repo, run_dir, expected_sha):
    run_dir = evidence_dir(repo, run_dir)
    path = no_reparse(run_dir / 'source-hashes.json')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_sha, 'Preflight receipt SHA mismatch')
    data = json.loads(raw)
    require(data['status'] == 'PREFLIGHT_READY' and data['repo'] == str(repo)
            and data['full_sha256'] == FULL_SHA and data['overlay_sha256'] == OVERLAY_SHA
            and data['tool_sha256'] == digest(Path(__file__)), 'Preflight binding mismatch')
    rows = load_contract(repo)
    moving = {r['path']: r['target'] for r in rows if r['disposition'] in MOVE}
    require({k: v['target'] for k, v in data['preserved'].items()} == moving,
            'Preflight preserved mapping mismatch')
    require(set(data['untouched']) == {r['path'] for r in rows if r['disposition'] not in MOVE},
            'Preflight untouched scope mismatch')
    return run_dir, data, rows


def check_untouched(repo, data):
    for rel, expected in data['untouched'].items():
        require(file_meta(under(repo, rel)) == expected, 'Untouched identity drift: ' + rel)
    require(protection(repo) == data['protected'], 'Protected files changed')


def make_parents(repo, path, clock=utc):
    require(path.is_relative_to(repo / HISTORY), 'Creation outside history')
    missing = []
    p = path
    while not p.exists():
        missing.append(p)
        p = p.parent
    no_reparse(p)
    for p in reversed(missing):
        no_reparse(p.parent)
        window(clock)
        p.mkdir(exist_ok=False)
        no_reparse(p)


def post_match(actual, expected):
    # Rename can alter change-time; mtime, file ID, attributes and mode must survive.
    keys = (*IDENTITY, 'mode', 'attributes')
    return (actual['sha256'] == expected['sha256'] and
            all(actual['metadata'][k] == expected['metadata'][k] for k in keys))


def move(repo, run_dir, expected_sha, clock=utc, rename=os.rename):
    require(os.name == 'nt', 'Real moves require Windows non-overwriting os.rename')
    window(clock)
    run_dir, data, rows = load_baseline(repo, run_dir, expected_sha)
    journal = run_dir / 'move-journal.jsonl'
    require(not os.path.lexists(journal), 'Move already attempted; manual journal-based takeover required')
    moved = 0
    with journal.open('x', encoding='utf-8', newline='\n') as log:
        active = None
        try:
            require(not os.path.lexists(under(repo, HISTORY)), 'History root appeared after preflight')
            current_check(repo, rows)
            check_untouched(repo, data)
            for rel, expected in data['preserved'].items():
                require(stable_hash(under(repo, rel)) == {k: expected[k] for k in ('metadata', 'sha256')},
                        'Preflight source content/metadata drift: ' + rel)
            event(log, dict(status='MOVE_START', preflight_sha256=expected_sha, files=len(data['preserved'])))
            for rel, expected in data['preserved'].items():
                window(clock)
                active = dict(source=rel, target=expected['target'])
                source = under(repo, rel)
                target = under(repo, expected['target'])
                require(not os.path.lexists(target), 'Target appeared: ' + str(target))
                before = stable_hash(source)
                require(before == {k: expected[k] for k in ('metadata', 'sha256')}, 'Source drift: ' + rel)
                make_parents(repo, target.parent, clock)
                source = under(repo, rel)
                target = under(repo, expected['target'])
                require(source.stat().st_dev == target.parent.stat().st_dev, 'Cross-device move refused')
                require(not os.path.lexists(target), 'Target collision at final check')
                require(file_meta(source) == before['metadata'], 'Source changed after hashing')
                window(clock)
                event(log, dict(status='INTENT', source=rel, target=expected['target'], before=before))
                window(clock)
                rename(source, target)  # Windows refuses existing target; never copy/delete.
                after = stable_hash(target)
                require(not os.path.lexists(source) and post_match(after, expected), 'Post-move identity/content mismatch')
                moved += 1
                event(log, dict(status='DONE', source=rel, target=expected['target'], before=before, after=after))
            check_untouched(repo, data)
            event(log, dict(status='MOVE_COMPLETE', moved=moved, aliases_changed=0, deleted=0))
            return dict(status='MOVE_COMPLETE', moved=moved, verification_required=True)
        except BaseException as exc:
            observed = {}
            if active:
                for side, rel in active.items():
                    try:
                        p = under(repo, rel)
                        observed[side] = dict(path=rel, exists=os.path.lexists(p),
                                              metadata=file_meta(p) if os.path.lexists(p) else None)
                    except Exception as observation_error:
                        observed[side] = dict(path=rel, error=repr(observation_error))
            event(log, dict(status='PAUSED', confirmed_done=moved, error=repr(exc),
                            current_item=active, observed=observed,
                            instruction='No automatic rollback/resume; inspect INTENT and actual paths.'))
            raise


def verify(repo, run_dir, expected_sha):
    run_dir, data, rows = load_baseline(repo, run_dir, expected_sha)
    report = run_dir / 'verify.json'
    require(not os.path.lexists(report), 'Verify report exists; do not overwrite evidence')
    checked = []
    try:
        for rel, expected in data['preserved'].items():
            source, target = under(repo, rel), under(repo, expected['target'])
            require(not os.path.lexists(source), 'Old source still exists: ' + rel)
            actual = stable_hash(target)  # Never reads/falls back to old source.
            require(post_match(actual, expected), 'Archive content/metadata mismatch: ' + str(target))
            checked.append(dict(source=rel, target=expected['target'], expected_sha256=expected['sha256'], **actual))
        check_untouched(repo, data)
        actual_archive = walk_files(repo, [HISTORY])
        require(actual_archive == {v['target'] for v in data['preserved'].values()},
                'Unexpected/missing archive files')
        expected_remaining = set(data['untouched'])
        actual_remaining = walk_files(repo, CORE + EXTRA_TREES) | set(EXTRA_FILES)
        require(actual_remaining == expected_remaining, 'Unexpected/missing objects in old roots after move')
        result = dict(status='MOVE_VERIFIED', verified=len(checked), files=checked,
                      untouched=len(data['untouched']), deleted=0, aliases_changed=0,
                      protected=data['protected'], preflight_sha256=expected_sha,
                      limitation='Preservation transfer only; branch not retired, aliases not switched.')
    except BaseException as exc:
        write_new(report, dict(status='VERIFY_FAILED', verified=len(checked), error=repr(exc), files=checked))
        raise
    write_new(report, result)
    return {k: v for k, v in result.items() if k not in ('files', 'protected')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preflight', 'move', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--preflight-sha256')
    args = parser.parse_args()
    repo = no_reparse(args.repo)
    require(repo.is_dir(), 'Repository missing')
    if args.mode == 'preflight':
        require(not args.preflight_sha256, 'Preflight does not consume earlier receipts')
        result = preflight(repo, args.run_dir)
    else:
        require(bool(args.preflight_sha256), 'Explicit --preflight-sha256 required')
        result = globals()[args.mode](repo, args.run_dir, args.preflight_sha256)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps(dict(status='REFUSED_OR_PAUSED', error=str(error)), ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
