"""Read-only lookup of four retained packaging identities; never replays old jobs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

FULL_TABLE = 'docs/project-layout/20261108-packaging-full-retirement-v1/full-disposition.jsonl'
FULL_SHA256 = '274c6cd5602b591047ce2b2c907b4e5d9bb33ff55b190b0bb8678ec586e82ef1'
ARCHIVE = 'operations/history/retired-packaging/20261108/'
P_PLAN = 'output/storage_retention/recycle_g1_20261027/P_preservation.json'
DEFAULT_MAPPING = 'docs/project-layout/20261108-packaging-runtime-ready-v1/runtime/locations.json'
PAYLOAD = 'output/share_bundle/20261104-mechanism-first-handoff-r1/payload/manifest.json'
P_PAYLOAD = 'output/share_bundle/20261025-character-tools/isolated 中文 space/scripts/release/build_explicit_bundle.py'
SKILLS = {date: 'output/share_bundle/cc_skill_values_' + date + '/manifest.json'
          for date in ('20261021', '20261022')}
ALLOWED = {PAYLOAD, P_PAYLOAD, *SKILLS.values()}


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def relative(value):
    p = PurePosixPath(value)
    if not value or '\\' in value or ':' in value or p.is_absolute() or '..' in p.parts or p.as_posix() != value:
        raise ValueError('Not a canonical repository-relative path: ' + value)
    return value


def under(repo, value):
    p = (repo / relative(value)).resolve()
    if not p.is_relative_to(repo):
        raise ValueError('Path escapes repository: ' + value)
    return p


def load_locations(repo, mapping):
    """Validate selected external locations against the unchanged full disposition."""
    raw = under(repo, FULL_TABLE).read_bytes()
    if identity(raw)['sha256'] != FULL_SHA256:
        raise ValueError('Wrong disposition source/version')
    source = {r['path']: r for r in map(json.loads, raw.decode('utf-8').splitlines())}
    config = json.loads(mapping.read_bytes())
    if config['source'] != {'path': FULL_TABLE, 'sha256': FULL_SHA256, 'rows': 6935}:
        raise ValueError('Wrong mapping source')
    entries = config['entries']
    if set(entries) != ALLOWED:
        raise ValueError('Mapping must contain only the four selected retained identities')
    for logical, entry in entries.items():
        row = source[logical]
        if row['disposition'] == 'DELETE' or not row.get('target'):
            raise ValueError('Deleted/unretained identity: ' + logical)
        if entry['disposition'] != row['disposition']:
            raise ValueError('Disposition disagrees with frozen table: ' + logical)
        if entry['archive'] != row['target'] or not relative(entry['archive']).startswith(ARCHIVE):
            raise ValueError('Archive location disagrees with frozen table: ' + logical)
        if entry['identity']['bytes'] != row['bytes']:
            raise ValueError('Size disagrees with frozen table: ' + logical)
        relative(logical)
    return entries


def resolve(repo, entries, logical, location):
    if location not in ('current', 'archive'):
        raise ValueError('location must be current or archive')
    relative(logical)
    if logical not in entries:
        raise ValueError('Undeclared or DELETE identity: ' + logical)
    physical = logical if location == 'current' else entries[logical]['archive']
    p = under(repo, physical)
    if location == 'archive' and p.is_relative_to((repo / 'output/share_bundle').resolve()):
        raise ValueError('Archive cannot access old share_bundle root')
    return p


def read_retained(repo, entries, logical, location):
    p = resolve(repo, entries, logical, location)
    raw = p.read_bytes()  # Missing new object raises; there is no current-path fallback.
    if identity(raw) != entries[logical]['identity']:
        raise ValueError('Retained identity mismatch: ' + logical)
    return p, raw


def check_preserved(repo, entries, location):
    frozen = json.loads(under(repo, P_PLAN).read_bytes())
    row = frozen['files'][221]
    if row.get('source_existing_protected') != P_PAYLOAD:
        raise ValueError('Wrong P_preservation logical identity')
    expected = {k: row[k] for k in ('bytes', 'sha256')}
    if expected != entries[P_PAYLOAD]['identity']:
        raise ValueError('Mapping does not match frozen P_preservation #222')
    p, raw = read_retained(repo, entries, P_PAYLOAD, location)
    return {'logical_identity': P_PAYLOAD, 'physical_path': str(p),
            'frozen_reference': P_PLAN, 'entry_one_based': 222, 'identity': identity(raw),
            'matches_frozen_preservation': True, 'location': location}


def skill_manifest(repo, entries, location, date, member=None, sha256=None):
    p, raw = read_retained(repo, entries, SKILLS[date], location)
    data = json.loads(raw)
    if data['bundle_id'] != 'cc_skill_values_' + date:
        raise ValueError('Wrong skill manifest bundle identity')
    matches = [r for r in data['files'] if (member is None or r['path'] == member)
               and (sha256 is None or r['sha256'] == sha256)]
    return {'bundle_id': data['bundle_id'], 'physical_path': str(p), 'manifest_identity': identity(raw),
            'campaign_run_id': data['campaign']['run_id'],
            'campaign_signature': data['campaign']['signature'],
            'declared_entries': len(data['files']), 'matching_entries': len(matches),
            'entries': matches if member or sha256 else [],
            'entry_list_omitted': not (member or sha256),
            'archive_status': 'ZIP_ALREADY_MISSING_NOT_RECOVERED',
            'scope': 'Manifest identity clues only. Does not read or restore card/HTML/media or ZIP.',
            'location': location}


def commands(repo, entries, location, output):
    payload = resolve(repo, entries, PAYLOAD, location).parent
    checker = repo / 'docs/project-layout/20261108-packaging-full-retirement-v1/retained/check_relocated_payload.py'
    reconcile = repo / 'scripts/character_skills/reconcile_mechanism_first_handoff_20261104.py'
    python = str(repo / '.venv/Scripts/python.exe')
    jobs = {'reconcile': [python, '-B', str(reconcile), '--bundle', str(payload), '--output', str(output.resolve())],
            'payload_checker': [python, '-B', str(checker), '--repo', str(repo), '--payload-root', str(payload), '--run-frozen-verifier']}
    return {'location': location, 'executed': False, 'argv': jobs,
            'powershell': {k: '& ' + ' '.join("'" + x.replace("'", "''") + "'" for x in v) for k, v in jobs.items()},
            'notes': ['Reconcile writes output and reads the current production baseline. Command only; not run.',
                      'Archive commands require actual verified relocation first.',
                      'Payload checker refuses current old share_bundle root; use archive or independent readback.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--location', choices=('current', 'archive'), required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('preservation')
    look = sub.add_parser('skill-manifest')
    look.add_argument('date', choices=SKILLS)
    look.add_argument('--member')
    look.add_argument('--sha256')
    get = sub.add_parser('resolve')
    get.add_argument('logical')
    cmd = sub.add_parser('commands')
    cmd.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        entries = load_locations(repo, args.mapping.resolve())
        if args.action == 'preservation':
            result = check_preserved(repo, entries, args.location)
        elif args.action == 'skill-manifest':
            result = skill_manifest(repo, entries, args.location, args.date, args.member, args.sha256)
        elif args.action == 'commands':
            result = commands(repo, entries, args.location, args.output)
        else:
            result = {'logical_identity': args.logical, 'physical_path': str(resolve(repo, entries, args.logical, args.location)),
                      'existence_checked': False, 'location': args.location}
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
