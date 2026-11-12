"""Reconcile a reused candidate overlay against current rows and primary sources.

Keep the original sidecar stamp. The separate receipt records what was checked,
which historical carrier rows were reused and which current runtime bytes passed.
This does not promote candidates or re-decide their semantic association.
"""
import argparse
import copy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path
from rerun_output import require_new_files, write_new_text

from seal_reader import AUDIT, audit_path, digest, load

SIDECARS = ('branch_candidates', 'branch_conditions', 'mana_costs', 'branch_assessments')


def payload(path, detail=False):
    text = path.read_text(encoding='utf-8-sig')
    value = text.split(']=', 1)[1] if detail else text.split('=', 1)[1]
    return json.loads(value.strip().removesuffix(';'))


def rows(card):
    return {r['id']: r for g in card['groups'] for s in g['skills'] for r in s['rows']}


def same(left, right):
    # JSON distinguishes missing/null, booleans and numeric zero.
    return json.dumps(left, ensure_ascii=False, sort_keys=True, allow_nan=False) == json.dumps(right, ensure_ascii=False, sort_keys=True, allow_nan=False)


def canonical_hash(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def runtime_hashes(output):
    required = ['build_receipt.json', 'frontend_receipt.json', 'index.html', 'app.js',
                'branches.js', 'inline.js', 'levels.js', 'style.css', 'data/catalog.js']
    required += ['data/' + name + '.js' for name in SIDECARS]
    receipt = load(output / 'build_receipt.json')
    required += ['data/cards/' + cid + '.js' for cid in receipt['sourceHashes']]
    return {rel: digest(output / rel) for rel in sorted(required)}


def verify_adaptation(output, receipt_path, root=None):
    receipt = load(receipt_path)
    if receipt.get('schema') != 1 or receipt.get('pass') is not True:
        raise ValueError('Invalid sidecar adaptation receipt')
    if receipt.get('targetSnapshot') != load(output / 'build_receipt.json')['snapshot']:
        raise ValueError('Sidecar adaptation targets a different base snapshot')
    if receipt.get('runtimeHashes') != runtime_hashes(output):
        raise ValueError('Runtime content differs from sidecar adaptation receipt')
    if root is not None:
        for rel, expected in receipt.get('sourceFiles', {}).items():
            logical = (root / rel).resolve()
            if not logical.is_relative_to(root.resolve()) or digest(read_path(logical, root=root)) != expected:
                raise ValueError('Sidecar primary source hash differs: ' + rel)
    return receipt


def revalidate(root, output, baseline, audit_dir=AUDIT, label_fixes=None):
    root, output, baseline = (p.resolve() for p in (root, output, baseline))
    target = write_path(output / audit_path(audit_dir) / 'sidecar_adaptation.json', root=root)
    require_new_files(target)
    build_receipt = load(output / 'build_receipt.json')
    overlay = payload(output / 'data/branch_candidates.js')
    if digest(output / 'data/branch_candidates.js') != digest(baseline / 'data/branch_candidates.js'):
        raise ValueError('Reused overlay differs from baseline; regenerate and review instead')
    fixes = load(label_fixes) if label_fixes else []
    if not isinstance(fixes, list):
        raise ValueError('label-fixes must be an explicit list of {rowId,effectId,old,new}')
    allowed = {(f['rowId'], f['effectId']): f for f in fixes}
    if len(allowed) != len(fixes):
        raise ValueError('Duplicate reviewed label fixes')
    used_fixes, source_files = {}, {}

    def resolve(source):
        key = source['source_key']
        if key.startswith('CACHE/'):
            path = root / 'output/cache_full_20261015_v3/decoded' / key.split('/', 1)[1]
        elif key.startswith('APK/'):
            path = root / 'output/base_master' / key.split('/', 1)[1]
        else:
            raise ValueError('Unsupported primary source namespace: ' + key)
        path = path.resolve()
        if not path.is_relative_to(root):
            raise ValueError('Source path escapes root')
        if path not in source_files:
            physical = read_path(path, root=root)
            source_files[path] = (physical, load(physical), digest(physical))
        result = source_files[path][1]
        for part in source['json_pointer'].lstrip('/').split('/'):
            part = part.replace('~1', '/').replace('~0', '~')
            result = result[int(part)] if isinstance(result, list) else result[part]
        return result

    carriers, items, target_hashes = [], [], {}
    for cid, entry in overlay['cards'].items():
        if not cid.isdigit():
            raise ValueError('Invalid candidate card id')
        active = {rid: p for rid, p in entry['rows'].items() if p.get('additions')}
        if not active:
            continue
        current_path = output / 'data/cards' / (cid + '.js')
        old_path = baseline / 'data/cards' / (cid + '.js')
        current, old = rows(payload(current_path, True)), rows(payload(old_path, True))
        formal_path = read_path(root / 'output/character_skills/pages' / cid / 'card.json', root=root)
        formal = load(formal_path)
        target_hashes[cid] = digest(formal_path)
        if build_receipt['sourceHashes'].get(cid) != target_hashes[cid]:
            raise ValueError('Reader source hash is stale: ' + cid)
        skills = { (s.get('layer'), s.get('record_id')): s for g in formal['groups']
                   if g['group'] == 'special_move' for s in g['skills'] }
        for rid, patch in active.items():
            left, right = copy.deepcopy(old[rid]), copy.deepcopy(current[rid])
            old_effects = {e['id']: e for e in left['effects']}
            for effect in right['effects']:
                before = old_effects.get(effect['id'])
                if before and (before['label'] != effect['label'] or before.get('pendingText') != effect.get('pendingText')):
                    fix = allowed.get((rid, effect['id']))
                    if not fix or fix['old'] != before['label'] or fix['new'] != effect['label']:
                        raise ValueError('Unreviewed carrier label change: ' + effect['id'])
                    used_fixes[(rid, effect['id'])] = fix
                    before['label'] = effect['label']
                    if before.get('pendingText') != effect.get('pendingText'):
                        if ('oldPendingText' not in fix or 'newPendingText' not in fix or
                            fix['oldPendingText'] != before.get('pendingText') or
                            fix['newPendingText'] != effect.get('pendingText')):
                            raise ValueError('Unreviewed carrier pendingText change: ' + effect['id'])
                        if 'pendingText' in effect:
                            before['pendingText'] = effect['pendingText']
                        else:
                            before.pop('pendingText', None)
            if not same(left, right):
                raise ValueError('Carrier row semantics differ from baseline: ' + rid)
            carriers.append({'cid': int(cid), 'rowId': rid,
                             'baselineRowSHA256': canonical_hash(old[rid]),
                             'targetRowSHA256': canonical_hash(current[rid]),
                             'relation': 'same_except_reviewed_labels' if not same(old[rid], current[rid]) else 'identical'})
            effects = {e['id']: e for e in current[rid]['effects']}
            for addition in patch['additions']:
                if addition['effectId'] not in effects:
                    raise ValueError('Candidate effect missing: ' + addition['effectId'])
                answer = addition['answer']
                source = answer['source']
                skill = skills[(source['layer'], source['branchId'])]
                record = next(r for r in skill['record_evidence']
                              if r['record_id'] == source['recordId'] and r['layer'] == source['layer']
                              and r['table'] == source['rule'].split('|')[0])
                actual = resolve(record['source'])
                if not same(actual, source['recordRaw']) or not same(actual[source['field'].lstrip('/')], source['raw']):
                    raise ValueError('Candidate raw/source differs: ' + rid)
                if not same(record['source'], source['allSources']):
                    raise ValueError('Candidate source locator differs: ' + rid)
                parent = next(r for r in skill['record_evidence'] if r['table'] == 'bosspattern'
                              and r['record_id'] == source['branchId'] and r['layer'] == source['layer'])
                parent_raw = resolve(parent['source'])
                if not same(parent['source'], source['parentSource']) or not same(parent_raw, source['conditionsRaw']):
                    raise ValueError('Candidate parent source differs: ' + rid)
                slot = source['parentSlot'].split('/')[0]
                if '/' in source['parentSlot']:
                    boss = next(r for r in skill['record_evidence'] if r['table'] == 'bossskill'
                                and r['record_id'] == parent_raw[slot] and r['layer'] == source['layer'])
                    linked_id = resolve(boss['source'])['s_ability']
                else:
                    linked_id = parent_raw[slot]
                if linked_id != source['recordId']:
                    raise ValueError('Candidate no longer belongs to parent slot: ' + rid)
                items.append({'cid': int(cid), 'rowId': rid, 'effectId': addition['effectId'],
                              'branchId': source['branchId'], 'recordId': source['recordId'],
                              'rule': source['rule'], 'source': record['source'],
                              'parentSource': parent['source'], 'additionSHA256': canonical_hash(addition)})
    if len(items) != overlay['summary']['additions']:
        raise ValueError('Candidate addition count differs from declared denominator')
    # An allowed label repair may concern rows outside the overlay. Its use is
    # audited by the build regression, so only relevant carrier changes are here.
    for path, (physical, _, expected) in source_files.items():
        if digest(physical) != expected:
            raise ValueError('Primary source changed during reconciliation: ' + str(path))
    result = {'schema': 1, 'pass': True, 'adaptedAt': datetime.now(timezone.utc).isoformat(),
              'targetSnapshot': load(output / 'build_receipt.json')['snapshot'],
              'sidecarOriginalSnapshot': overlay['readerSnapshot'],
              'baseline': str(baseline), 'baselineBuildReceiptSHA256': digest(baseline / 'build_receipt.json'),
              'candidateSHA256': digest(output / 'data/branch_candidates.js'),
              'counts': {'additions': len(items), 'carrierRows': len(carriers), 'cards': len(target_hashes)},
              'sourceHashes': target_hashes, 'sourceFiles': {str(p.relative_to(root)).replace('\\', '/'): h for p, (_, _, h) in source_files.items()},
              'reviewedLabelChanges': list(used_fixes.values()), 'carriers': carriers, 'additions': items,
              'runtimeHashes': runtime_hashes(output),
              'scope': 'Current row/effect/primary-source and parent-slot reconciliation of reused additions; original stamp retained; no new semantic promotion or runtime validation'}
    if label_fixes:
        result['labelFixesSHA256'] = digest(label_fixes)
    write_new_text(target, json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--audit-dir', default=AUDIT)
    parser.add_argument('--label-fixes', type=Path)
    args = parser.parse_args()
    result = revalidate(args.root, args.output, args.baseline, args.audit_dir, args.label_fixes)
    print(json.dumps({'pass': True, **result['counts']}, ensure_ascii=False))
