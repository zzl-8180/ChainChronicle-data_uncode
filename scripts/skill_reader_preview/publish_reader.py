"""Publish a sealed sibling reader directory; never generate mainline data."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path

from seal_reader import AUDIT, audit_path, check_sources, digest, verify_seal
from revalidate_sidecars import verify_adaptation

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'output/character_skills'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def publish(stage, live, backup, guard, audit_dir=AUDIT, base=None):
    base = write_path(base or BASE, root=ROOT).resolve()
    stage, live, backup = (write_path(p, root=ROOT).resolve() for p in (stage, live, backup))
    guard = read_path(guard, root=ROOT).resolve()
    # Both rename targets must be verified absolute direct children of our output.
    for p in (stage, live, backup):
        if p.parent != base or not p.name.startswith('reader_'):
            raise ValueError(f'Not an allowed reader output directory: {p}')
    if len({stage, live, backup}) != 3 or backup.exists():
        raise ValueError('Use three distinct directories and a new backup name')
    if not stage.is_dir() or not live.is_dir():
        raise ValueError('Both staged and live readers must exist')
    audit = audit_path(audit_dir)
    switched, saved_live = False, False
    try:
        if (stage / audit / 'publish_receipt.json').exists():
            raise ValueError('Stage already has a publication receipt; use a new audit directory')
        seal = verify_seal(stage, guard, audit_dir)
        formal = check_sources(ROOT, stage, guard)
        verify_adaptation(stage, stage / audit / 'sidecar_adaptation.json', ROOT)
        if seal['snapshot'] != formal:
            raise ValueError('Stage seal snapshot differs from current mainline')
        seal_hash = digest(stage / audit / 'stage_seal.json')
        live.rename(backup)
        saved_live = True
        stage.rename(live)
        switched = True
        # Catch mutations during the switch; success is written only afterwards.
        live_guard = live / guard.relative_to(stage) if guard.is_relative_to(stage) else guard
        verify_seal(live, live_guard, audit_dir)
        check_sources(ROOT, live, live_guard)
        verify_adaptation(live, live / audit / 'sidecar_adaptation.json', ROOT)
        journal = {'status': 'PUBLISHED', 'publishedAt': datetime.now(timezone.utc).isoformat(),
                   'stage': str(stage), 'live': str(live), 'backup': str(backup),
                   'snapshot': formal, 'mainlineUnchanged': True,
                   'stageSealSHA256': seal_hash, 'sealedFiles': len(seal['files']),
                   'checks': {rel: seal['files'][rel] for rel in seal['validations']},
                   'scope': 'Sealed reader switch; success recorded after switch and post-switch verification'}
        with (live / audit / 'publish_receipt.json').open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(journal, ensure_ascii=False, indent=2) + '\n')
        return journal
    except BaseException as error:
        rollback_errors = []
        if switched:
            try:
                live.rename(stage)
            except BaseException as rollback_error:
                rollback_errors.append(type(rollback_error).__name__ + ': ' + str(rollback_error))
            if stage.is_dir():
                try:
                    (stage / audit / 'publish_receipt.json').unlink(missing_ok=True)
                except BaseException as rollback_error:
                    rollback_errors.append(type(rollback_error).__name__ + ': ' + str(rollback_error))
        if saved_live:
            try:
                backup.rename(live)
            except BaseException as rollback_error:
                rollback_errors.append(type(rollback_error).__name__ + ': ' + str(rollback_error))
        failure = {'status': 'FAILED', 'failedAt': datetime.now(timezone.utc).isoformat(),
                   'stage': str(stage), 'live': str(live), 'backup': str(backup),
                   'error': type(error).__name__ + ': ' + str(error),
                   'rollbackErrors': rollback_errors,
                   'oldLiveRestored': saved_live and live.exists() and not backup.exists()}
        failure_path = write_path(base / (stage.name + '_publish_failure_' + uuid.uuid4().hex + '.json'), root=ROOT)
        failure_path.write_text(json.dumps(failure, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if rollback_errors:
            raise RuntimeError('Publication failed and rollback needs recovery; see ' + str(failure_path)) from error
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--live', type=Path, default=BASE / 'reader_full_20261106')
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--mainline-guard', type=Path, required=True)
    parser.add_argument('--audit-dir', default=AUDIT)
    parser.add_argument('--base', type=Path, help='explicit isolated reader output parent for a staged publication')
    args = parser.parse_args()
    print(json.dumps(publish(args.stage, args.live, args.backup, args.mainline_guard, args.audit_dir, args.base), ensure_ascii=False, indent=2))
