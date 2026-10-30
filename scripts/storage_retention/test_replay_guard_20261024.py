"""Targeted fail-closed tests. Fixtures are retained; no file is removed."""
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage_retention.replay_guard import Replay, ReplayInputError, digest, inspect_old, inspect_new, validate_comparison

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/storage_retention/replay_safety_20261024'
FIX = OUT / 'test_fixtures' / uuid.uuid4().hex
FIX.mkdir(parents=True)
results = []
SIG = 'a' * 64


def put(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding='utf-8')


def run(name, func):
    func()
    results.append(dict(test=name, status='PASS'))


def old_run(name, missing=(), corrupt=(), cids=('1', '2')):
    p = FIX / name
    put(p / 'plan.json', {'cids': list(cids)})
    (p / 'transactions').mkdir()
    for cid in cids:
        base = p / 'transactions' / cid / 'backup'
        base.mkdir(parents=True)
        if cid not in missing:
            put(base / 'card.json', {'cid': int(cid), 'groups': []})
        sha = digest(base / 'card.json') if cid not in missing else 'f' * 64
        if cid in corrupt:
            sha = 'f' * 64
        put(base / 'receipt.json', {'files': {'card.json': sha}})
        put(base / 'before.json', {'card.json': sha})
    return p


def expect_blocked(p, count):
    d = inspect_old([p], 2)
    assert d['status'] == 'BLOCKED' and d['missing_count'] == count, d


def expect_error(func):
    try:
        func()
    except (ReplayInputError, SystemExit, FileExistsError):
        return
    raise AssertionError('failure was accepted')


complete = old_run('complete')
missing = old_run('missing', missing=('1',))
empty = old_run('empty', cids=())
corrupt = old_run('corrupt', corrupt=('1',))
run('empty baseline cannot pass', lambda: expect_blocked(empty, 0))
run('one missing backup cannot pass', lambda: expect_blocked(missing, 1))
run('wrong backup hash cannot pass', lambda: expect_blocked(corrupt, 0))
run('complete baseline accepted', lambda: (
    None if inspect_old([complete], 2)['status'] == 'INPUTS_COMPLETE' else (_ for _ in ()).throw(AssertionError())))


def overlap():
    d = inspect_old([missing, complete], 2)
    assert d['missing_count'] == 1 and d['status'] == 'BLOCKED'
    assert d['paths']['1'] == str((missing / 'transactions/1/backup/card.json').resolve())


run('later duplicate cannot hide earlier missing backup', overlap)
pages = FIX / 'frozen_pages'
for cid in ('1', '2'):
    put(pages / cid / 'card.json', {'cid': int(cid), 'groups': []})
    put(pages / cid / 'receipt.json', {'status': 'SUCCESS', 'signature': SIG,
                                     'files': {'card.json': digest(pages / cid / 'card.json')}})
run('wrong new signature blocked', lambda: expect_error(lambda: inspect_new(pages, ('1', '2'), 'b' * 64)))
run('incomplete new card set blocked', lambda: expect_error(lambda: inspect_new(pages, ('1', '2', '3'), SIG)))
script = FIX / 'work/task/legacy.py'
put(script, {})


def args(out):
    return ['--new-pages', str(pages), '--expected-new-signature', SIG, '--out-dir', str(out)]


def fresh_output():
    p = FIX / 'output/independent'
    r = Replay(script, [complete], args(p), 2)
    r.finish(True)
    assert json.loads((p / 'run_record.json').read_text(encoding='utf-8'))['status'] == 'PASS'
    expect_error(lambda: Replay(script, [complete], args(p), 2))


run('fresh output succeeds; existing output cannot be overwritten', fresh_output)
run('original work output blocked', lambda: expect_error(
    lambda: Replay(script, [complete], args(FIX / 'work/task/new'), 2)))
run('original review output blocked', lambda: expect_error(
    lambda: Replay(script, [complete], args(FIX / 'output/character_skills/review/new'), 2)))
run('explicit historical new side required', lambda: expect_error(
    lambda: Replay(script, [complete], [], 2)))


def failure_record():
    r = Replay(script, [complete], args(FIX / 'output/failure'), 2)
    expect_error(lambda: r.finish(False, violations=1))
    assert json.loads((r.out / 'run_record.json').read_text(encoding='utf-8'))['status'] == 'FAIL'


run('comparison violation exits nonzero and records FAIL', failure_record)
run('stale unbound comparison result rejected', lambda: expect_error(
    lambda: validate_comparison({'stats': {'cards': 2236}}, 'binding', 2236)))
comparison = dict(_replay_guard=dict(status='PASS', script_name='compare_zero_change.py',
                                    expected_cards=2236, binding='correct'), stats=dict(cards=2236))
run('comparison from other historical input rejected', lambda: expect_error(
    lambda: validate_comparison(comparison, 'other', 2236)))
run('matching complete comparison accepted', lambda: validate_comparison(comparison, 'correct', 2236))


def default_missing():
    target = FIX / 'output/missing_must_not_write'
    expect_error(lambda: Replay(script, [missing], args(target), 2))
    assert not target.exists()


run('normal invocation with missing old input fails before output creation', default_missing)
import subprocess
optimized = subprocess.run([sys.executable, '-B', '-O', str(ROOT / 'work/20261020-pilot1017/compare_full_rows.py'),
                            '--check-inputs'], capture_output=True)
run('optimized Python cannot bypass assertions', lambda: (
    None if optimized.returncode == 2 else (_ for _ in ()).throw(AssertionError(optimized.returncode))))
payload = dict(status='PASS', tests=results, fixtures=str(FIX), deletions=0)
with (OUT / ('guard_tests_' + FIX.name + '.json')).open('x', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print(json.dumps(payload, ensure_ascii=False))
