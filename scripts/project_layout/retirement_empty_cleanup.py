"""Remove only five pinned disabled junctions and pinned empty old directories."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat

HERE = Path(__file__).absolute().parent
def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

p = module('preserve', 'run_retirement_preservation.py')
a = module('aliases', 'check_retirement_alias.py')
BASE = 'docs/project-layout/20261108-packaging-empty-cleanup-v1'
OLD = 'docs/project-layout/20261108-packaging-final-ready-v1/'
SNAP = OLD + 'deletion-20261108-v1/directories-before.json'
SNAP_SHA = '26213ce1341f2ed47f2693cd7e10467efba28ce3e760e43e73bc062a933b64e0'
PHYSICAL = 'docs/project-layout/20261108-packaging-physical-v1/run-immediate-bound/'
BEFORE_SHA = 'b37141ce19ba36958e555d30da4f3e744ae6fcf9dd51a316c8bb5b09c28e33f0'
SUMMARY_SHA = 'f573abf1437f2ad7d758c0d3aa13e280cd150d11233ac2a8bf27e0a8322643fa'

def bound(repo, name, expected):
    raw = p.under(repo, name).read_bytes()
    p.require(hashlib.sha256(raw).hexdigest() == expected, 'Bound evidence changed: ' + name)
    return json.loads(raw)

def load(repo):
    raw = p.under(repo, p.FULL).read_bytes()
    p.require(hashlib.sha256(raw).hexdigest() == p.FULL_SHA, 'Frozen scope changed')
    rows = [json.loads(x) for x in raw.decode('utf-8').splitlines()]
    snapshot = bound(repo, SNAP, SNAP_SHA)['directories']
    before = bound(repo, PHYSICAL + 'source-hashes.json', BEFORE_SHA)
    summary = bound(repo, PHYSICAL + 'junction-summary.json', SUMMARY_SHA)
    dirs = {x['path']: x for x in snapshot}
    p.require(len(dirs) == len(snapshot) == 9476, 'Wrong directory snapshot')
    roots = p.CORE + p.EXTRA_TREES
    for name in dirs:
        p.require(any(name == r or name.startswith(r + '/') for r in roots), 'Directory outside old roots')
    retained = {x['path'] for x in rows if x['disposition'] == 'RETAIN_IN_PLACE'}
    protected_dirs = {name for name in dirs if any(f.startswith(name + '/') for f in retained)}
    candidates = set(dirs) - protected_dirs
    p.require(len(retained) == 11 and len(protected_dirs) == 9 and len(candidates) == 9467,
              'Retained ancestor boundary changed')
    return rows, dirs, retained, protected_dirs, candidates, before, summary

def directory(repo, rel, expected):
    path = p.under(repo, rel)
    s = path.lstat()
    p.require(stat.S_ISDIR(s.st_mode) and (s.st_dev, s.st_ino) == (expected['dev'], expected['ino']),
              'Directory identity/type changed: ' + rel)
    return path

def protection(repo, retained, before, summary, previous):
    for rel in retained:
        p.require(p.file_meta(p.under(repo, rel)) == before['untouched'][rel], 'Retained file drift: ' + rel)
    for suffix in ('share_bundle', 'distribution', 'history-work'):
        p.require(p.under(repo, p.HISTORY + '/' + suffix).is_dir(), 'Archive root missing')
    ids = {x['cycle']: x['new_file_id'] for x in summary['entries']}
    for cycle in a.CYCLES:
        formal = a.formal_path(repo, cycle)
        item = a.inspect_alias(repo, cycle, 'formal', formal, repo / a.NEW)
        p.require([item['lstat_dev'], item['lstat_ino']] == ids[cycle], 'Formal alias changed')
        if previous:
            a.inspect_alias(repo, cycle, 'previous', formal.with_name(a.BASENAMES['previous']), repo / a.OLD, True)
        else:
            absent(formal.with_name(a.BASENAMES['previous']))
        absent(formal.with_name(a.BASENAMES['next']))
    return p.protection(repo)

def absent(path):
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError('Object still present: ' + str(path))

def check(repo):
    rows, dirs, retained, keep, candidates, before, summary = load(repo)
    for rel, expected in dirs.items():
        directory(repo, rel, expected)
    actual_files = p.walk_files(repo, p.CORE + p.EXTRA_TREES) | set(p.EXTRA_FILES)
    p.require(actual_files == retained, 'Unknown/missing file in old trees; no cleanup')
    actual_dirs = set()
    stack = [p.under(repo, r) for r in p.CORE + p.EXTRA_TREES]
    while stack:
        path = stack.pop()
        p.no_reparse(path)
        actual_dirs.add(path.relative_to(repo).as_posix())
        for child in path.iterdir():
            s = child.lstat()
            p.require(not s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, 'Unexpected reparse')
            if stat.S_ISDIR(s.st_mode):
                stack.append(child)
    p.require(actual_dirs == set(dirs), 'Unknown/missing old directory; no cleanup')
    protected = protection(repo, retained, before, summary, True)
    return dict(status='CHECK_PASS', directories=9476, empty_tree_candidates=9467,
                retained_ancestor_directories=9, previous_candidates=5, retained_files=11,
                protected=protected, code_sha256=p.digest(Path(__file__)))

def remove_directory(path):
    """RemoveDirectoryW never recursively removes files; a junction target survives."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = kernel.RemoveDirectoryW
    fn.argtypes = (wintypes.LPCWSTR,)
    fn.restype = wintypes.BOOL
    value = str(path)
    if not value.startswith('\\\\?\\'):
        value = '\\\\?\\' + value
    if not fn(value):
        raise ctypes.WinError(ctypes.get_last_error())
    absent(path)

def apply(repo, plan_sha):
    base = p.under(repo, BASE)
    plan = bound(repo, BASE + '/check.json', plan_sha)
    p.require(plan['status'] == 'CHECK_PASS' and plan['code_sha256'] == p.digest(Path(__file__)), 'Plan/code mismatch')
    current = check(repo)
    p.require(current == plan, 'Check/protection drift; no cleanup')
    _, dirs, retained, keep, candidates, before, summary = load(repo)
    removed_dirs, removed_previous = 0, 0
    active = None
    with (base / 'cleanup-journal.jsonl').open('x', encoding='utf-8', newline='\n') as log:
        try:
            for cycle in a.CYCLES:
                path = a.formal_path(repo, cycle).with_name(a.BASENAMES['previous'])
                active = path.relative_to(repo).as_posix()
                info = a.inspect_alias(repo, cycle, 'previous', path, repo / a.OLD, True)
                p.event(log, dict(status='INTENT', kind='previous_junction_only', path=active, identity=info))
                p.require(a.inspect_alias(repo, cycle, 'previous', path, repo / a.OLD, True) == info, 'Previous drift')
                remove_directory(path)
                removed_previous += 1
                p.event(log, dict(status='DONE', kind='previous_junction_only', path=active))
            for rel in sorted(candidates, key=lambda s: (-len(Path(s).parts), s)):
                active = rel
                path = directory(repo, rel, dirs[rel])
                p.require(not list(path.iterdir()), 'Directory became nonempty; keep and pause: ' + rel)
                p.event(log, dict(status='INTENT', kind='empty_directory', path=rel, identity=dirs[rel]))
                directory(repo, rel, dirs[rel])
                p.require(not list(path.iterdir()), 'Directory became nonempty after WAL: ' + rel)
                remove_directory(path)
                removed_dirs += 1
                p.event(log, dict(status='DONE', kind='empty_directory', path=rel))
            for rel in keep:
                directory(repo, rel, dirs[rel])
            after = protection(repo, retained, before, summary, False)
            p.require(after == plan['protected'], 'Protected state changed during cleanup')
            result = dict(status='CLEANUP_COMPLETE', previous_removed=removed_previous,
                          empty_directories_removed=removed_dirs, files_deleted=0,
                          retained_ancestor_directories=9, retained_files=11, formal_junctions=5)
            p.event(log, result.copy())
            p.write_new(base / 'result.json', result)
            return result
        except BaseException as exc:
            p.event(log, dict(status='PAUSED', current_path=active, previous_removed=removed_previous,
                              empty_directories_removed=removed_dirs, error=repr(exc), automatic_resume=False))
            raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('check', 'apply'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    repo = p.no_reparse(args.repo)
    base = p.under(repo, BASE)
    if args.mode == 'check':
        result = check(repo)
        p.write_new(base / 'check.json', result)
        print(json.dumps(dict(status=result['status'], empty_tree_candidates=9467,
                              previous_candidates=5, plan_sha256=p.digest(base / 'check.json'))))
    else:
        p.require(bool(args.plan_sha256), 'Explicit reviewed plan SHA required')
        print(json.dumps(apply(repo, args.plan_sha256)))

if __name__ == '__main__':
    main()
