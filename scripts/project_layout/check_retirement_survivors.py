"""R01 read-only, fresh content gate. No move/delete/junction/business writes.

Only --report is written, exclusively (never overwritten). A receipt is an
observation, not authorization or an OS lock on a future deletion operation.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys

BASE = 'docs/project-layout/20261108-packaging-full-retirement-v1/'
LOCKS = {
    'full-disposition.jsonl': '274c6cd5602b591047ce2b2c907b4e5d9bb33ff55b190b0bb8678ec586e82ef1',
    'repro/verified-source-pairs.json': '3c06b68412c705090a70fefe03715a9508582ee0614f5be902079b6c747b91d5',
    'terminal-survivors.json': '031e0a84a4795c3ec7f99baa1481647c846947da8e0af1f4d9fc8986a354db9e',
    'retained/extra-disposition.jsonl': 'c9f7614614c69f025b4eebcbee239da3393bcc28529597c5dc7192a4181456bb',
}
REPORT_ROOT = 'docs/project-layout/20261108-packaging-execution-v1/r01'
CHUNK = 1024 * 1024


def relative(value):
    p = PurePosixPath(value)
    if (not value or '\\' in value or ':' in value or p.is_absolute()
            or any(x in ('', '.', '..') for x in value.split('/'))):
        raise ValueError('unsafe relative path: ' + value)
    return p.as_posix()


def common(s):
    # Windows path.stat ctime and fstat ctime can use different semantics.
    # Compare ctime only within the SAME API before/after (see stamp).
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)


def stamp(s):
    return common(s) + (s.st_ctime_ns, s.st_mode,
                        getattr(s, 'st_file_attributes', 0))


def inspect(root, rel):
    p = root / relative(rel)
    ancestors = list(reversed(p.parents)) + [p]
    seen = []
    for item in ancestors:
        s = item.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 1024:
            raise ValueError('reparse: ' + str(item))
        if item == p:
            if not stat.S_ISREG(s.st_mode):
                raise ValueError('not regular file: ' + rel)
        elif not stat.S_ISDIR(s.st_mode):
            raise ValueError('not directory ancestor: ' + str(item))
        seen.append((str(item), s.st_dev, s.st_ino))
    return p, s, seen


def identity(s):
    return dict(zip(('dev', 'ino', 'bytes', 'mtime_ns', 'nlink', 'ctime_ns'),
                    common(s) + (s.st_ctime_ns,)))


class Reader:
    def __init__(self, root):
        self.root = root
        self.cache = {}
        self.bytes_read = 0

    def digest(self, rel, maximum):
        p, before, parents = inspect(self.root, rel)
        if before.st_size > maximum:
            raise ValueError('file exceeds recorded byte bound: ' + rel)
        # Cache only this run's freshly hashed physical file and full identity.
        # Every use still opens and checks the requested path and parent IDs.
        key = stamp(before)
        with p.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            if common(opened) != common(before):
                raise ValueError('path/handle identity changed: ' + rel)
            if key in self.cache:
                result = self.cache[key]
            else:
                h = hashlib.sha256()
                count = 0
                while True:
                    block = stream.read(min(CHUNK, maximum - count + 1))
                    if not block:
                        break
                    count += len(block)
                    self.bytes_read += len(block)
                    if count > maximum:
                        raise ValueError('file grew beyond recorded bound: ' + rel)
                    h.update(block)
                result = (count, h.hexdigest())
            closed = os.fstat(stream.fileno())
            if stamp(opened) != stamp(closed):
                raise ValueError('handle changed during read: ' + rel)
        _, after, parents_after = inspect(self.root, rel)
        if (stamp(before) != stamp(after) or common(closed) != common(after)
                or parents != parents_after):
            raise ValueError('path or ancestor identity changed during read: ' + rel)
        self.cache[key] = result
        return result, identity(after), parents_after


def group_for(source):
    return '/'.join(source.split('/')[:3 if source.startswith('output/') else 2])


def build_pairs(full, proofs, terminal, extras):
    by_path = {relative(x['path']): x for x in full}
    if len(by_path) != len(full):
        raise ValueError('duplicate full-table paths')
    folded_delete = {x['path'].casefold() for x in full if x['disposition'] == 'DELETE'}
    term = {relative(x['deleted_copy']): x for x in terminal}
    if len(term) != len(terminal):
        raise ValueError('duplicate terminal chain')
    proof = {relative(x['source']): x for x in proofs}
    readback = {relative(x['path']): x for x in extras if x['disposition'] == 'DELETE'}
    if (len(proof) != len(proofs) or len(proofs) != 1270 or len(readback) != 136
            or len(term) != 1406 or set(proof) & set(readback)
            or set(term) != set(proof) | set(readback)):
        raise ValueError('expected exact 1270 + 136 = 1406 pair coverage')
    pairs = []
    for source, chain in term.items():
        row = by_path[source]
        evidence = proof.get(source, readback.get(source))
        survivor = relative(chain['surviving_current_path'])
        target = relative(chain['survivor_final_target'])
        kind = 'external' if source in proof else 'readback'
        if row['disposition'] != 'DELETE':
            raise ValueError('source not declared DELETE: ' + source)
        expected_survivor = evidence['survivor']
        if (survivor != expected_survivor or row.get('survivor') != survivor
                or row.get('survivor_final_target') != target
                or evidence['bytes'] != row['bytes']
                or evidence['sha256'] != row['sha256']):
            raise ValueError('proof/full/terminal mismatch: ' + source)
        if survivor.casefold() in folded_delete or target.casefold() in folded_delete:
            raise ValueError('survivor is DELETE: ' + source)
        if kind == 'external':
            if survivor in by_path or target != survivor:
                raise ValueError('external survivor is not outside frozen scope: ' + source)
            if evidence.get('basis') != 'fresh_streaming_SHA256_both_files':
                raise ValueError('undeclared hash proof basis: ' + source)
        else:
            retained = by_path.get(survivor)
            if (not retained or retained['disposition'] != 'REHOME_BUSINESS'
                    or retained['target'] != target
                    or evidence['survivor_target'] != target
                    or retained['bytes'] != evidence['bytes']):
                raise ValueError('undeclared retained payload mapping: ' + source)
        pairs.append({'source': source, 'current': survivor, 'archive': target,
                      'kind': kind, 'group': group_for(source),
                      'bytes': evidence['bytes'], 'sha256': evidence['sha256'],
                      'source_identity': row['current_identity']})
    return pairs


def check_pair(reader, pair, mode):
    result = {k: pair[k] for k in ('source', 'kind', 'group')}
    result.update(survivor=pair[mode], match=False, source_should_keep=True,
                  fail_reason=[])
    snapshots = {}
    for side, rel in (('source', pair['source']), ('survivor', pair[mode])):
        try:
            (size, sha), seen, parents = reader.digest(rel, pair['bytes'])
            snapshots[side] = (seen, parents)
            result[side + '_observed'] = seen
            if side == 'source' and any(seen[k] != v for k, v in pair['source_identity'].items()):
                result['fail_reason'].append('source_frozen_identity_drift')
            if size != pair['bytes'] or sha != pair['sha256']:
                result['fail_reason'].append(side + '_content_drift')
        except (OSError, ValueError) as exc:
            result['fail_reason'].append(side + ': ' + str(exc))
    # The first side must remain stable across the OTHER side's entire read,
    # including cached physical-file reads. Compare path stat to path stat;
    # ctime is deliberately never compared between path and handle APIs.
    for side, rel in (('source', pair['source']), ('survivor', pair[mode])):
        if side in snapshots:
            try:
                _, after, parents = inspect(reader.root, rel)
                if (identity(after), parents) != snapshots[side]:
                    result['fail_reason'].append(side + '_changed_across_pair')
            except (OSError, ValueError) as exc:
                result['fail_reason'].append(side + '_pair_end: ' + str(exc))
    a, b = result.get('source_observed'), result.get('survivor_observed')
    if a and b and (a['dev'], a['ino']) == (b['dev'], b['ino']):
        result['fail_reason'].append('source_and_survivor_same_file_id')
    result['match'] = not result['fail_reason']
    return result


def run(root, mode, selected):
    reader = Reader(root)
    loaded = {}
    for name, expected in LOCKS.items():
        (size, sha), _, _ = reader.digest(BASE + name, 16 * CHUNK)
        if sha != expected:
            raise ValueError('frozen evidence SHA mismatch: ' + name)
        # Bounded read; digest above checked regular file, parents, identity.
        p, before, parents = inspect(root, BASE + name)
        with p.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            data = stream.read(size + 1)
            closed = os.fstat(stream.fileno())
        _, after, after_parents = inspect(root, BASE + name)
        if (len(data) != size or hashlib.sha256(data).hexdigest() != expected
                or common(before) != common(opened) or stamp(opened) != stamp(closed)
                or stamp(before) != stamp(after) or parents != after_parents):
            raise ValueError('evidence changed during parse: ' + name)
        text = data.decode('utf-8')
        loaded[name] = ([json.loads(line) for line in text.splitlines()]
                        if name.endswith('.jsonl') else json.loads(text))
    pairs = build_pairs(loaded['full-disposition.jsonl'],
                        loaded['repro/verified-source-pairs.json'],
                        loaded['terminal-survivors.json'],
                        loaded['retained/extra-disposition.jsonl'])
    groups = sorted({p['group'] for p in pairs})
    if selected and not set(selected) <= set(groups):
        raise ValueError('unknown group; available: ' + ', '.join(groups))
    chosen = set(selected or groups)
    results = []
    summaries = []
    for group in groups:
        if group not in chosen:
            continue
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        subset = [check_pair(reader, p, mode) for p in pairs if p['group'] == group]
        failures = sum(not x['match'] for x in subset)
        for item in subset:
            item['source_should_keep'] = bool(failures)
            item['group_stopped'] = bool(failures)
        results.extend(subset)
        summaries.append({'group': group, 'started_utc': started,
                          'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          'pairs': len(subset), 'failed': failures, 'stopped': bool(failures)})
    failed = sum(not x['match'] for x in results)
    return {'schema_version': 1, 'mode': mode, 'evidence_sha256': LOCKS,
            'scope': 'full1406' if len(results) == 1406 else 'selected_groups',
            'pairs': len(results), 'matched': len(results) - failed, 'failed': failed,
            'full1406_content_gate_pass': len(results) == 1406 and failed == 0,
            'deletion_authorized': False, 'groups': summaries,
            'payload_bytes_read_including_evidence': reader.bytes_read,
            'external_multilink_pairs': sum(x['kind'] == 'external' and
                x.get('survivor_observed', {}).get('nlink', 0) > 1 for x in results),
            'results': results}


def report_target(root, value, explicit):
    target = Path(os.path.abspath(value))
    allowed = root / REPORT_ROOT
    if not explicit and not target.is_relative_to(allowed):
        raise ValueError('report must be inside ' + str(allowed) +
                         '; use --independent-report for an explicit independent destination')
    # Report parent must already exist and have no reparse anywhere.
    for p in list(reversed(target.parent.parents)) + [target.parent]:
        s = p.lstat()
        if (not stat.S_ISDIR(s.st_mode) or stat.S_ISLNK(s.st_mode)
                or getattr(s, 'st_file_attributes', 0) & 1024):
            raise ValueError('unsafe report parent: ' + str(p))
    if target.exists() or target.is_symlink():
        raise ValueError('report already exists: ' + str(target))
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).absolute().parents[2])
    parser.add_argument('--mode', choices=('current', 'archive'), default='current',
                        help='archive reads exact final targets; never falls back to current')
    parser.add_argument('--group', action='append', help='source root; partial runs never pass full1406 gate')
    parser.add_argument('--report', required=True, help='new JSON receipt, parent must exist')
    parser.add_argument('--independent-report', action='store_true',
                        help='explicitly authorize a new receipt outside the new r01 directory')
    args = parser.parse_args(argv)
    try:
        root = Path(os.path.abspath(args.repo))
        report = report_target(root, args.report, args.independent_report)
        try:
            result = run(root, args.mode, args.group)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result = {'full1406_content_gate_pass': False, 'deletion_authorized': False,
                      'fatal_error': str(exc), 'source_should_keep': True}
        with report.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, separators=(',', ':'))
            stream.write('\n')
        print(json.dumps({k: v for k, v in result.items() if k not in
                          ('results', 'groups', 'evidence_sha256')}, ensure_ascii=False))
        return 0 if result.get('full1406_content_gate_pass') else 2
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
