"""Bound future transaction backups without deleting any run or evidence.

Reservations are conservative and shared by serial/parallel cohort runners.
Old runs are grandfathered, not removed. See scripts/storage_retention/README.md.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

DEFAULT_MAX_BYTES = 8 * 1024 ** 3
DEFAULT_MAX_RUNS = 12
ARTIFACTS = ('card.json', 'index.html', 'receipt.json', 'reuse_blocked.json')


class RetentionLimitError(RuntimeError):
    pass


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _save(path, value):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


@contextmanager
def _locked(pages, timeout=30):
    folder = pages.resolve() / '_batch' / 'retention'
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / 'reservation.lock'
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RetentionLimitError(f'Retention lock busy: {lock}. Check the owner; never auto-remove a stale lock.')
            time.sleep(0.05)
    try:
        os.write(fd, json.dumps(dict(pid=os.getpid(), created_at=_now())).encode())
        os.close(fd)
        yield folder / 'state.json'
    finally:
        lock.unlink()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _state(path):
    if not path.exists():
        return dict(schema_version=1, created_at=_now(), max_bytes=DEFAULT_MAX_BYTES,
                    max_runs=DEFAULT_MAX_RUNS, reservations={},
                    legacy_policy='Existing unregistered runs are protected; inventory only, no automatic deletion.')
    state = _read(path)
    if state.get('schema_version') != 1 or state.get('max_bytes', 0) <= 0 or state.get('max_runs', 0) <= 0:
        raise RetentionLimitError(f'Invalid retention state: {path}')
    if not isinstance(state.get('reservations'), dict):
        raise RetentionLimitError(f'Invalid reservations: {path}')
    return state


def _run_key(pages, run_dir):
    relative = run_dir.resolve().relative_to(pages.resolve())
    parts = relative.parts
    if (len(parts) != 4 or parts[0] != '_batch' or parts[1] not in
            ('ge60', '40to59', '20to39', 'remaining') or parts[2] != 'runs'):
        raise ValueError('Expected pages/_batch/<cohort>/runs/<run_id>')
    return relative.as_posix()


def reserve_run(pages, run_dir, cids):
    """Reserve existing bytes before any replacement. Never infer review success.

    Each caller supplies exactly the cards it will rebuild; unchanged --resume
    cards need no reservation. A failure/crash keeps its entire reservation.
    """
    pages = Path(pages).resolve()
    key = _run_key(pages, Path(run_dir))
    cids = list(cids)
    if not cids:
        return dict(status='NO_REBUILD', reserved_bytes=0)
    # before.json and other tiny transaction metadata fit within 4 KiB/card.
    total = 4096 * len(cids)
    for cid in cids:
        if not str(cid).isdigit():
            raise ValueError('Non-numeric card ID')
        folder = pages / str(cid)
        if folder.resolve().parent != pages:
            raise ValueError(f'Card folder escapes output: {folder}')
        for name in ARTIFACTS:
            file = folder / name
            if file.is_symlink():
                raise ValueError(f'Symlink artifact is not supported: {file}')
            if file.exists():
                total += file.stat().st_size
    with _locked(pages) as path:
        state = _state(path)
        if key in state['reservations']:
            raise RetentionLimitError(f'Run already reserved: {key}')
        active = [r for r in state['reservations'].values() if r['status'] == 'RETAINED']
        used = sum(r['reserved_bytes'] for r in active)
        if len(active) >= state['max_runs'] or used + total > state['max_bytes']:
            raise RetentionLimitError(
                f'Backup retention limit reached BEFORE page writes: retained_runs={len(active)}/{state["max_runs"]}, '
                f'reserved_bytes={used}, requested_bytes={total}, limit_bytes={state["max_bytes"]}. '
                'Review/archive retained backups and explicitly release reservations; nothing was deleted. '
                f'State: {path}')
        record = dict(status='RETAINED', created_at=_now(), reserved_bytes=total,
                      cards=len(cids), review_status='NOT_INFERRED', run=key)
        state['reservations'][key] = record
        _save(path, state)
    return record


def release_reservation(pages, key, evidence):
    """Accounting only, after a separately authorized cleanup. Does not delete.

    Require a retained disposition file and no large transaction payload.
    Small before/receipt manifests may stay. Build success is not review success.
    """
    pages = Path(pages).resolve()
    run = pages / key
    key = _run_key(pages, run)
    evidence = Path(evidence).resolve()
    if not evidence.is_file():
        raise ValueError('A review/archive disposition file is required')
    payload = run / 'transactions'
    if evidence.is_relative_to(payload.resolve()):
        raise ValueError('Evidence must live outside the disposable transaction tree')
    metadata_bytes = 0
    if payload.exists():
        for file in payload.rglob('*'):
            if file.is_symlink() or not file.resolve().is_relative_to(payload.resolve()):
                raise RetentionLimitError('Transaction tree contains a link or escaping path')
            if file.is_file():
                if file.parent.name != 'backup' or file.name not in ('before.json', 'receipt.json') or file.stat().st_size > 65536:
                    raise RetentionLimitError('Transaction payload still present; reservation stays protected')
                metadata_bytes += file.stat().st_size
    with _locked(pages) as path:
        state = _state(path)
        record = state['reservations'][key]
        if record['status'] != 'RETAINED':
            raise RetentionLimitError('Reservation is not retained')
        record.update(status='RELEASED', released_at=_now(), disposition=str(evidence),
                      disposition_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
                      retained_metadata_bytes=metadata_bytes)
        _save(path, state)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pages', type=Path, required=True)
    parser.add_argument('--release-run', help='Accounting only; never deletes files')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    if args.release_run:
        if not args.evidence:
            parser.error('--release-run requires --evidence')
        result = release_reservation(args.pages, args.release_run, args.evidence)
    else:
        path = args.pages / '_batch/retention/state.json'
        result = _read(path) if path.exists() else dict(status='NOT_INITIALIZED', max_bytes=DEFAULT_MAX_BYTES,
                                                      max_runs=DEFAULT_MAX_RUNS, note='Initialized on first rebuilding run')
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
