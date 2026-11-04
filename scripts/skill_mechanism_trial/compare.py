"""Compare completed research arms without executing their implementations.

Raw-source checks here are distinct from semantic acceptance by the reviewer.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/skill_mechanism_trial/20261104'
INPUT = OUT / 'input'
ARMS = ['card_serial', 'family_attack', 'family_heal']


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def stamp(value):
    if value.endswith(' UTC'):
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def pointer(document, ptr):
    value = document
    for token in ptr.strip('/').split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def main():
    manifest = load(INPUT / 'manifest.json')
    targets = {t['task_id']: t for t in load(INPUT / 'targets.json')}
    rules = load(INPUT / 'output/character_skills/profiles/rules.json')
    changed = [rel for rel, meta in manifest['files'].items()
               if hashlib.sha256((INPUT / rel).read_bytes()).hexdigest() != meta['sha256']]
    assert not changed, changed
    arms, source_checks = {}, []
    for arm in ARMS:
        data = load(OUT / arm / 'task_results.json')
        start, end = stamp(data['started_at']), stamp(data['finished_at'])
        assert end >= start
        arms[arm] = {'started_at': data['started_at'], 'finished_at': data['finished_at'],
                     'elapsed_seconds': (end-start).total_seconds(), 'tasks': []}
        for task in data['tasks']:
            target = targets[task['task_id']]
            assert task['row_id'] == target['row_id'] and task['cid'] == target['cid']
            arms[arm]['tasks'].append({'task_id': task['task_id'], 'status': task['status'],
                'submitted_items': len(task.get('answers', [])),
                'descriptor_candidates': sum(a.get('novelty_category') == 'new_description_binding' for a in task.get('answers', [])),
                'field_observations_in_answers': sum(a.get('novelty_category') == 'field_value_only' for a in task.get('answers', []))})
            for answer in task.get('answers', []):
                check = {'arm': arm, 'task_id': task['task_id'], 'answer': answer, 'checks': {}}
                source = answer['source']
                rel = source['input_relative_path'].replace('\\', '/')
                path = (INPUT / rel).resolve()
                path.relative_to(INPUT.resolve())
                record = pointer(load(path), source['json_pointer'])
                field = answer['field_path'].lstrip('/')
                if not isinstance(record, dict):
                    # Source pointer may point to the field itself; retain both levels.
                    record = pointer(load(path), source['json_pointer'].rsplit('/', 1)[0])
                identity_field = {'skilllist': 'skillid', 'bossskill': 'skillid', 'bosspattern': 'patternid', 'charainfo': 'cid'}[source['table']]
                check['checks']['identity'] = record.get(identity_field) == source['record_id']
                check['checks']['raw_value'] = field in record and record[field] == answer['raw_value']
                check['checks']['layer'] = source['layer'] == 'CACHE'
                check['checks']['baseline_unresolved'] = any(e['effect_id'] == answer['effect_id'] and e['status'] == 'unresolved' for e in target['baseline_effects'])
                key = answer.get('rule_key')
                known = rules.get(key)
                if answer.get('novelty_category') != 'field_value_only':
                    check['checks']['known_rule'] = known is not None
                check['known_rule_exists'] = known is not None
                if known:
                    check['checks']['rule_field'] = known['field_path'] == answer['field_path']
                    check['checks']['rule_table'] = known['table'] == source['table']
                    check['checks']['rule_type'] = known['effect_type'] == record.get('ability' if source['table'] == 'skilllist' else 'skillid0')
                check['passed_source_checks'] = all(check['checks'].values())
                source_checks.append(check)
    assert {x['task_id'] for x in arms['card_serial']['tasks']} == set(targets)
    assert {x['task_id'] for arm in ['family_attack','family_heal'] for x in arms[arm]['tasks']} == set(targets)
    ps = min(stamp(arms[a]['started_at']) for a in ['family_attack','family_heal'])
    pe = max(stamp(arms[a]['finished_at']) for a in ['family_attack','family_heal'])
    serial = arms['card_serial']['elapsed_seconds']
    parallel = (pe-ps).total_seconds()
    summary = {'snapshot': manifest['snapshot'], 'input_files': len(manifest['files']), 'input_hash_mismatches': changed,
        'arms': arms, 'source_checks': source_checks,
        'source_checks_all_pass': all(x['passed_source_checks'] for x in source_checks),
        'timing': {'serial_seconds': serial, 'parallel_span_seconds': parallel,
                   'family_worker_seconds_sum': sum(arms[a]['elapsed_seconds'] for a in ['family_attack','family_heal']),
                   'raw_difference_seconds': serial-parallel,
                   'raw_difference_fraction': (serial-parallel)/serial,
                   'valid_as_savings_only_if_equal_reviewed_coverage': True,
                   'unit': 'agent wall-clock, not human work hours'},
        'limits': ['single nonrandomized pilot', 'grouping and worker count changed together',
                   'no causal speedup attribution', 'common preparation/review not included in arm elapsed',
                   'new candidates are not production promotion']}
    save('comparison.json', summary)
    print(json.dumps({'source_checks': len(source_checks), 'all_pass': summary['source_checks_all_pass'], 'timing': summary['timing']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
