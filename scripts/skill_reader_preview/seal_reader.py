"""Seal a fully validated reader; subsequent edits require validation and resealing.

The seal covers every file in the directory, including audit evidence. Only this
manifest and the successful post-switch publish receipt are excluded. This binds
the final reviewed stage, not an independent semantic review of its contents.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path

AUDIT = 'audit/c19_closeout_20261107'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def audit_path(audit_dir):
    path = Path(audit_dir)
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'audit':
        raise ValueError('audit-dir must be a relative path inside audit/')
    return path


def validation_paths(audit_dir=AUDIT):
    a = audit_path(audit_dir).as_posix()
    return ['validation.json', *(a + '/' + name for name in (
        'c19_validation.json', 'confidence_validation.json',
        'condition_validation.json', 'browser_validation.json',
        'sidecar_adaptation.json'))]


def check_validations(stage, paths):
    for rel in paths:
        path = stage / rel
        if not path.resolve().is_relative_to(stage.resolve()):
            raise ValueError('Validation path escapes stage: ' + rel)
        result = load(path)
        if not (result.get('pass') is True or result.get('passed') is True or result.get('status') == 'PASS'):
            raise ValueError('Validation not passed: ' + rel)


def exclusions(audit_dir):
    a = audit_path(audit_dir).as_posix()
    return [a + '/stage_seal.json', a + '/publish_receipt.json']


def inventory(stage, audit_dir):
    excluded = exclusions(audit_dir)
    files = {}
    for path in sorted(stage.rglob('*')):
        # Avoid directory links and files resolving outside the sealed tree.
        if path.is_symlink() or not path.resolve().is_relative_to(stage.resolve()):
            raise ValueError('Linked/escaping stage entry cannot be sealed: ' + str(path))
        if path.is_file():
            rel = path.relative_to(stage).as_posix()
            if rel not in excluded:
                files[rel] = digest(path)
    return files


def check_sources(root, stage, guard):
    base = read_path(root / 'output/character_skills', root=root)
    build = load(stage / 'build_receipt.json')
    formal = load(base / 'effect_ledger/metrics.json')['snapshot']
    if build['snapshot'] != formal:
        raise ValueError('Staged reader is not the current formal snapshot')
    sources = build['sourceHashes']
    disk = {p.parent.name for p in (base / 'pages').glob('*/card.json') if p.parent.name.isdigit()}
    if not sources or set(sources) != disk:
        raise ValueError('Reader source set differs from current mainline')
    for cid, expected in sources.items():
        if not str(cid).isdigit() or digest(base / 'pages' / str(cid) / 'card.json') != expected:
            raise ValueError('Reader source hash differs: ' + str(cid))
    guards = load(guard)
    required = {'output/character_skills/effect_ledger/metrics.json',
                'output/character_skills/effect_ledger/ledger.jsonl',
                'output/character_skills/profiles/rules.json'}
    if not required.issubset(guards):
        raise ValueError('Mainline guard must include metrics, ledger and rules')
    for rel, expected in guards.items():
        logical = (root / rel).resolve()
        if not logical.is_relative_to(root.resolve()):
            raise ValueError('Mainline guard path escapes character data')
        path = read_path(logical, root=root).resolve()
        if not path.is_relative_to(base.resolve()):
            raise ValueError('Mainline guard path escapes character data')
        if digest(path) != expected:
            raise ValueError('Mainline changed before publication: ' + rel)
    return formal


def seal(root, stage, guard, audit_dir=AUDIT, extra_validations=()):
    root, stage = root.resolve(), stage.resolve()
    paths = validation_paths(audit_dir) + list(extra_validations)
    check_validations(stage, paths)
    snapshot = check_sources(root, stage, guard)
    # Validate the independently rechecked sidecar/runtime binding as well.
    from revalidate_sidecars import verify_adaptation
    verify_adaptation(stage, stage / audit_path(audit_dir) / 'sidecar_adaptation.json', root)
    files = inventory(stage, audit_dir)
    result = {'schema': 1, 'pass': True, 'sealedAt': datetime.now(timezone.utc).isoformat(),
              'snapshot': snapshot, 'auditDir': audit_path(audit_dir).as_posix(),
              'excludedPaths': exclusions(audit_dir), 'files': files,
              'validations': paths, 'mainlineGuardSHA256': digest(guard),
              'scope': 'All stage files after required validation; seal and successful post-switch receipt excluded'}
    target = stage / audit_path(audit_dir) / 'stage_seal.json'
    write_path(target, root=root).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def verify_seal(stage, guard, audit_dir=AUDIT):
    result = load(stage / audit_path(audit_dir) / 'stage_seal.json')
    if result.get('schema') != 1 or result.get('pass') is not True or result.get('auditDir') != audit_path(audit_dir).as_posix():
        raise ValueError('Missing or invalid stage seal')
    if result.get('excludedPaths') != exclusions(audit_dir):
        raise ValueError('Unapproved seal exclusions')
    if not set(validation_paths(audit_dir)).issubset(result.get('validations', [])):
        raise ValueError('Stage seal lacks mandatory validations')
    if result.get('mainlineGuardSHA256') != digest(guard):
        raise ValueError('Mainline guard differs from stage seal')
    actual = inventory(stage, audit_dir)
    if actual != result.get('files'):
        expected = result.get('files', {})
        changes = sorted(k for k in actual.keys() | expected.keys() if actual.get(k) != expected.get(k))
        raise ValueError('Stage contents differ from seal: ' + ', '.join(changes[:20]))
    check_validations(stage, result['validations'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mainline-guard', type=Path, required=True)
    parser.add_argument('--audit-dir', default=AUDIT)
    parser.add_argument('--validation', action='append', default=[], help='additional required PASS receipt, relative to output')
    args = parser.parse_args()
    result = seal(args.root, args.output, args.mainline_guard, args.audit_dir, args.validation)
    print(json.dumps({'pass': True, 'sealedFiles': len(result['files']), 'auditDir': result['auditDir']}, ensure_ascii=False))
