"""Freeze a bounded, equal input packet for three research arms."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
from versioned_outputs import experiment_output

ROOT = Path(__file__).resolve().parents[2]
OUT = experiment_output('skill_mechanism_trial')
PACKET = OUT / 'input'
TARGETS = [
    ('A1', 'attack', 30110, '30110-ability-ability-skillid_1_-lvorder0-f0'),
    ('B1', 'heal', 30107, '30107-special_move-special_move-pattern0-lvorder0-f1'),
    ('A2', 'attack', 30333, '30333-ability-ability-skillid_1_-lvorder0-f2'),
    ('B2', 'heal', 30313, '30313-special_move-special_move-pattern0-lvorder0-f2'),
]


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def main():
    if (PACKET / 'manifest.json').exists():
        raise RuntimeError('Frozen packet already exists')
    manifest = {'started_at': datetime.now(timezone.utc).isoformat(), 'files': {}}

    def freeze(rel):
        p = ROOT / rel if rel.startswith('scripts/') else read_path(ROOT / rel,root=ROOT)
        before = p.stat()
        data = p.read_bytes()
        after = p.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), rel
        q = PACKET / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes(data)
        manifest['files'][rel] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
        return json.loads(data) if rel.endswith('.json') else None

    metrics = freeze('output/character_skills/effect_ledger/metrics.json')
    freeze('output/character_skills/profiles/rules.json')
    for name in ['skilllist', 'charainfo', 'bossinfo']:
        freeze('output/cache_full_20261015_v3/decoded/' + name + '.data5.json.raw')
    cards = {cid: freeze(f'output/character_skills/pages/{cid}/card.json') for _, _, cid, _ in TARGETS}
    for folder in ['output/ordinary_effects/ability1095', 'output/character_skills/boss_heal_types', 'output/boss_heal']:
        for p in read_path(ROOT / folder,root=ROOT).iterdir():
            if p.is_file() and p.suffix in ('.md', '.json', '.txt'):
                if p.stat().st_size > 4 * 1024**2:
                    raise RuntimeError('Unexpectedly large evidence: ' + str(p))
                freeze(folder+'/'+p.name)
    for name in ['card_page_inference_b11_sa1095.py', 'card_page_inference_b12_1095ext.py',
                 'card_page_inference_type8.py', 'skilllist_types.py', 'boss_heal_types.py', 'rules.py']:
        freeze('scripts/character_skills/' + name)
    row_ids = {row_id for _, _, _, row_id in TARGETS}
    descriptions, effects = {}, []
    digest = hashlib.sha256()
    ledger_path = read_path(ROOT / 'output/character_skills/effect_ledger/ledger.jsonl',root=ROOT)
    before = ledger_path.stat()
    with ledger_path.open('rb') as stream:
        for line in stream:
            digest.update(line)
            item = json.loads(line)
            if item['record_type'] == 'description' and item['row_id'] in row_ids:
                descriptions[item['row_id']] = item
            elif item['record_type'] == 'effect' and item['description_ref'] in row_ids:
                effects.append(item)
    after = ledger_path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    manifest['ledger_source'] = {'sha256': digest.hexdigest(), 'bytes': after.st_size}
    manifest['snapshot'] = metrics['snapshot']['snapshot_id']
    targets = []
    for task_id, family, cid, row_id in TARGETS:
        d = descriptions[row_id]
        assert d['input_snapshot']['snapshot_id'] == manifest['snapshot']
        skill = next(s for g in cards[cid]['groups'] for s in g['skills'] if any(r['row_id'] == row_id for r in s['rows']))
        row = next(r for r in skill['rows'] if r['row_id'] == row_id)
        assert not row['answers'], 'Target already has answers: ' + row_id
        ee = [e for e in effects if e['description_ref'] == row_id]
        assert ee and all(e['status'] == 'unresolved' for e in ee)
        targets.append({'task_id': task_id, 'family': family, 'cid': cid, 'row_id': row_id,
                        'japanese': row['japanese'], 'baseline_description': d, 'baseline_effects': ee,
                        'baseline_answers': row['answers'], 'source_skill': {k: skill[k] for k in ['table', 'record_id', 'layer', 'reference_field', 'source']}})
    save(PACKET / 'targets.json', targets)
    # Recheck originals only during preparation; subsequent research reads this packet only.
    drift = [rel for rel, entry in manifest['files'].items()
             if hashlib.sha256((ROOT / rel if rel.startswith('scripts/') else read_path(ROOT / rel, root=ROOT)).read_bytes()).hexdigest() != entry['sha256']]
    assert not drift, drift
    manifest['files']['targets.json'] = {'sha256': hashlib.sha256((PACKET / 'targets.json').read_bytes()).hexdigest(), 'bytes': (PACKET / 'targets.json').stat().st_size}
    manifest['source_freeze_check'] = 'UNCHANGED_DURING_FREEZE'
    manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
    manifest['total_bytes'] = sum(x['bytes'] for x in manifest['files'].values())
    assert manifest['total_bytes'] < 60 * 1024**2
    save(PACKET / 'manifest.json', manifest)
    for arm in ['card_serial', 'family_attack', 'family_heal', 'review']:
        (OUT / arm).mkdir(parents=True, exist_ok=True)
    save(OUT / 'experiment_start.json', {'preparation_end_utc': manifest['finished_at'], 'snapshot': manifest['snapshot'],
        'arms': {'card_serial': ['A1','B1','A2','B2'], 'family_attack': ['A1','A2'], 'family_heal': ['B1','B2']},
        'timing_unit': 'agent wall-clock seconds, not human work hours', 'common_experiment_start_utc': '2026-11-03T16:10:15+00:00'})
    print(json.dumps({'tasks': len(targets), 'snapshot': manifest['snapshot'], 'files': len(manifest['files']), 'bytes': manifest['total_bytes']}))


if __name__ == '__main__':
    main()
