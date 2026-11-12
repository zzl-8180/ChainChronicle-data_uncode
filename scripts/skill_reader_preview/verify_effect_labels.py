"""Recompute local recovery-label proof; never trust a receipt's PASS as proof."""
import argparse
from collections import Counter
import json
import re
from hashlib import sha256
from pathlib import Path
from rerun_output import require_new_files, write_new_text

ROOT = Path(__file__).resolve().parents[2]
R01_BATCH = 'reader_c19_r01_20261107'
# Explicit batch contract, not the expected size of every future repair.
BATCHES = {R01_BATCH: {'effects': 118, 'rows': 106, 'cards': 55}}
SCHEMA = 'reader-effect-label-review-v2'
PENDING = {'回复': '数值尚未解出', '解除异常状态': '效果已见于描述，机制细节待确认'}


def require(ok, code, context=''):
    if not ok:
        raise ValueError(f'{code}: {context}')


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def same(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(b, sort_keys=True, ensure_ascii=False, allow_nan=False)


def card(p):
    return json.loads(p.read_text('utf-8-sig').split(']=', 1)[1].strip().removesuffix(';'))


def rows(c):
    values = [r for g in c['groups'] for s in g['skills'] for r in s['rows']]
    result = {r['id']: r for r in values}
    require(len(result) == len(values), 'label_proof_duplicate_row')
    return result


def check_containers(row, counts):
    """All bound answers have an actual effect container; unbound views do not."""
    counts['rows'] += 1
    counts['unboundAnswers'] += len(row['unboundAnswers'])
    for effect in row['effects']:
        counts['effects'] += 1
        for answer in effect['answers']:
            counts['boundAnswers'] += 1
            require(answer.get('source', {}).get('effectId') == effect['id'],
                    'label_proof_answer_container', effect['id'])
        if effect['label'] == '解除异常状态':
            counts['statusRemovalEffects'] += 1
            require(not effect['answers'], 'label_proof_status_removal_has_answer', effect['id'])


def audit_labels(reader, baseline, ledger, batch=R01_BATCH):
    """Pure proof from actual before/after cards and trusted ledger; no writes."""
    require(batch in BATCHES, 'label_proof_unknown_batch', batch)
    effects, descriptions = {}, {}
    for line in ledger.open(encoding='utf-8'):
        item = json.loads(line)
        if item['record_type'] == 'effect':
            require(item['effect_id'] not in effects, 'label_proof_duplicate_ledger_effect', item['effect_id'])
            effects[item['effect_id']] = item
        elif item['record_type'] == 'description':
            require(item['row_id'] not in descriptions, 'label_proof_duplicate_ledger_row', item['row_id'])
            descriptions[item['row_id']] = item
    paths = sorted((reader/'data/cards').glob('*.js'))
    require({p.name for p in paths} == {p.name for p in (baseline/'data/cards').glob('*.js')}, 'label_proof_card_set')
    changes, inputs, consistency = [], {}, Counter()
    for p in paths:
        old_path = baseline/'data/cards'/p.name
        before, after = rows(card(old_path)), rows(card(p))
        consistency['cards'] += 1
        require(list(before) == list(after), 'label_proof_row_identity', p.name)
        for rid, row in after.items():
            check_containers(row, consistency)
            previous = before[rid]
            require(same({k:v for k,v in previous.items() if k != 'effects'},
                         {k:v for k,v in row.items() if k != 'effects'}), 'label_proof_row_fields', rid)
            old = {e['id']: e for e in previous['effects']}
            require(len(old) == len(previous['effects']) and list(old) == [e['id'] for e in row['effects']],
                    'label_proof_effect_identity', rid)
            for e in row['effects']:
                b = old[e['id']]
                require(same({k:v for k,v in b.items() if k not in ('label', 'pendingText')},
                             {k:v for k,v in e.items() if k not in ('label', 'pendingText')}),
                        'label_proof_effect_other_fields', e['id'])
                if b['label'] == e['label']:
                    require(b.get('pendingText') == e.get('pendingText'), 'label_proof_unregistered_pending', e['id'])
                    continue
                require(e['id'] in effects and rid in descriptions, 'label_proof_ledger_identity', e['id'])
                source = effects[e['id']]
                require(source['effect_id'] == e['id'] and source['description_ref'] == rid
                        and e['id'] in descriptions[rid]['effect_ids'], 'label_proof_ledger_row_effect', e['id'])
                start, end = source['span']
                jp = row['original']
                require(jp == descriptions[rid]['japanese'], 'label_proof_original_japanese', rid)
                require(0 <= start < end <= len(jp) and jp[start:end] == source['snippet'] == '回復',
                        'label_proof_span_snippet', e['id'])
                require(source['effect_type'] == '回復（词表外）', 'label_proof_effect_type', e['id'])
                status_recovery = bool(re.search(r'状態異常[をも]$', jp[:start]) or jp[end:].startswith('した状態異常'))
                expected = '解除异常状态' if status_recovery else '回复'
                require(e['label'] == expected, 'label_proof_local_semantics', e['id'])
                require((b['label'], expected) in {('解除异常状态', '回复'), ('回复', '解除异常状态')}
                        and '状態異常' in jp, 'label_proof_allowed_old_new', e['id'])
                require(b.get('pendingText') == PENDING[b['label']] and e.get('pendingText') == PENDING[e['label']],
                        'label_proof_pending_text', e['id'])
                changes.append(dict(rowId=rid, effectId=e['id'], old=b['label'], new=e['label'],
                                    oldPendingText=b['pendingText'], newPendingText=e['pendingText'],
                                    effect_type=source['effect_type'], span=source['span'], snippet=source['snippet'],
                                    original=jp, answerCount=len(e['answers'])))
                inputs[p.name] = {'before': digest(old_path), 'after': digest(p)}
    counts = {'effects':len(changes), 'rows':len({x['rowId'] for x in changes}), 'cards':len(inputs)}
    require(same(counts, BATCHES[batch]), 'label_proof_batch_counts', {'batch':batch, 'actual':counts, 'expected':BATCHES[batch]})
    consistency['answerViews'] = consistency['boundAnswers'] + consistency['unboundAnswers']
    consistency['answerContainerMismatches'] = 0
    consistency['statusRemovalEffectsWithAnswers'] = 0
    return {'schema':SCHEMA, 'batch':batch, 'pass':True, 'counts':counts, 'consistency':dict(consistency),
            'ledgerSHA256':digest(ledger), 'cards':inputs, 'changes':changes,
            'scope':'Full raw-card bound-answer container check and independently recomputed span-local label repairs; no production writes'}


def validate_review(reader, baseline, ledger, receipt_path, batch=R01_BATCH):
    """Compare the external receipt to proof computed here, not to itself."""
    reviewed = read(receipt_path)
    require(reviewed.get('schema') == SCHEMA and reviewed.get('pass') is True, 'label_review_schema')
    require(reviewed.get('batch') == batch and batch in BATCHES, 'label_review_batch')
    fixes_path = receipt_path.parent/'effect_label_fixes.json'
    require(fixes_path.is_file(), 'label_review_missing_fixes')
    require(reviewed.get('fixesSHA256') == digest(fixes_path), 'label_review_fixes_hash')
    fixes = read(fixes_path)
    require(isinstance(fixes, list) and isinstance(reviewed.get('changes'), list), 'label_review_changes_type')
    require(all(isinstance(f, dict) and isinstance(f.get('effectId'), str) for f in fixes), 'label_review_effect_id')
    require(len({f['effectId'] for f in fixes}) == len(fixes), 'label_review_duplicate_fix')
    require(same(fixes, reviewed['changes']), 'label_review_fixes_receipt_mismatch')
    proof = audit_labels(reader, baseline, ledger, batch)
    for field in ('counts', 'ledgerSHA256', 'cards', 'changes', 'consistency'):
        require(same(reviewed.get(field), proof[field]), 'label_review_'+field+'_mismatch')
    proof['fixesSHA256'] = digest(fixes_path)
    return proof


def verify(reader, baseline, output, batch=R01_BATCH):
    fixes = output/'effect_label_fixes.json'
    report = output/'effect_label_validation.json'
    require_new_files(fixes, report)
    result = audit_labels(reader, baseline, ROOT/'output/character_skills/effect_ledger/ledger.jsonl', batch)
    write_new_text(fixes, json.dumps(result['changes'], ensure_ascii=False, indent=2))
    result['fixesSHA256'] = digest(fixes)
    write_new_text(report, json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({'pass':True, 'counts':result['counts'], 'consistency':result['consistency']}, ensure_ascii=False))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--batch', choices=BATCHES, default=R01_BATCH)
    a = p.parse_args()
    verify(a.reader.resolve(), a.baseline.resolve(), a.output.absolute(), a.batch)
