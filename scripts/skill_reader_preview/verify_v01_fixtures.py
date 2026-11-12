"""Execute independent V01 receipt attacks against the real verify_c19 CLI.

Writes only --work (default work/reader_v01_fixtures_20261107). The reader,
both baselines, ledger and validators are read-only inputs. A physical copy2
scratch is reused, restoring changed card bytes before each case.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def card(p):
    return json.loads(p.read_text(encoding='utf-8-sig').split(']=', 1)[1].strip().removesuffix(';'))


def rows(c):
    return {r['id']: r for g in c['groups'] for s in g['skills'] for r in s['rows']}


def run(args):
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    scratch = work/'scratch_reader'
    if scratch.exists():
        raise FileExistsError(f'Use a new --work directory; scratch already exists: {scratch}')
    # copytree uses copy2, never os.link: mutations cannot affect the input reader.
    shutil.copytree(args.reader, scratch, copy_function=shutil.copy2)
    source_receipt = read(args.receipt)
    assert source_receipt.get('schema') == 'reader-effect-label-review-v2', 'Need a real legal v2 receipt'
    assert source_receipt['counts'] == {'effects': 118, 'rows': 106, 'cards': 55}
    assert len(source_receipt['changes']) == 118
    validator = ROOT/'scripts/skill_reader_preview/verify_c19.py'
    source_hashes = {'verify_c19.py': digest(validator),
                     'verify_effect_labels.py': digest(ROOT/'scripts/skill_reader_preview/verify_effect_labels.py'),
                     'fixtureScript': digest(Path(__file__)), 'receipt': digest(args.receipt)}
    changed_files = set()
    cases = []

    def execute(name, mutate=None):
        if args.only_case and name != args.only_case:
            return
        for rel in changed_files:
            shutil.copy2(args.reader/rel, scratch/rel)
        changed_files.clear()
        case_dir = work/'cases'/name
        case_dir.mkdir(parents=True)
        receipt = deepcopy(source_receipt)
        explicit_bad_fixes_hash = False
        card_documents = {}

        def edit(change):
            cid = change['rowId'].split('-', 1)[0]
            rel = Path('data/cards')/f'{cid}.js'
            if rel not in card_documents:
                card_documents[rel] = card(scratch/rel)
            row = rows(card_documents[rel])[change['rowId']]
            effect = next(e for e in row['effects'] if e['id'] == change['effectId'])
            return row, effect

        if mutate:
            explicit_bad_fixes_hash = mutate(receipt, edit) == 'bad-fixes-hash'
        for rel, document in card_documents.items():
            cid = rel.stem
            (scratch/rel).write_text(f'window.CC_DETAILS=window.CC_DETAILS||{{}};window.CC_DETAILS[{cid}]='+json.dumps(document, ensure_ascii=False, separators=(',', ':'))+';\n', encoding='utf-8')
            changed_files.add(rel)
            # Attacks that change cards also update the after hash and fixes
            # hash. They must reach semantic checks, not merely hash/shape gates.
            if rel.name in receipt.get('cards', {}):
                receipt['cards'][rel.name]['after'] = digest(scratch/rel)
            dest = case_dir/'mutated_files'/rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(scratch/rel, dest)
        fixes_path = case_dir/'effect_label_fixes.json'
        write(fixes_path, receipt.get('changes', []))
        if not explicit_bad_fixes_hash and 'changes' in receipt:
            receipt['fixesSHA256'] = digest(fixes_path)
        receipt_path = case_dir/'effect_label_validation.json'
        write(receipt_path, receipt)
        audit_dir = f'audit/v01_fixture_{name}'
        cmd = [sys.executable, '-B', str(validator), '--root', str(ROOT), '--output', str(scratch),
               '--baseline', str(args.baseline), '--audit-dir', audit_dir,
               '--label-review', str(receipt_path), '--label-baseline', str(args.label_baseline),
               '--label-batch', args.batch]
        process = subprocess.run(cmd, cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace')
        (case_dir/'stdout.txt').write_text(process.stdout, encoding='utf-8')
        (case_dir/'stderr.txt').write_text(process.stderr, encoding='utf-8')
        validation_path = scratch/audit_dir/'c19_validation.json'
        validation = read(validation_path) if validation_path.exists() else None
        if validation:
            shutil.copy2(validation_path, case_dir/'c19_validation.json')
        reasons = validation.get('failures', []) if validation else []
        if not reasons:
            reasons = [line for line in (process.stderr+'\n'+process.stdout).splitlines() if line.strip()]
        expected_success = mutate is None
        # A failure in the harness (missing file/CLI, unhandled interpreter
        # exception) is not accepted as proof of semantic rejection.
        cli_failure = any(token in process.stderr for token in ('unrecognized arguments:', 'FileNotFoundError', 'ModuleNotFoundError'))
        proof_rejection = any(token in json.dumps(reasons, ensure_ascii=False) for token in ('label_proof_', 'label_review_'))
        accepted = process.returncode == 0 if expected_success else process.returncode != 0 and proof_rejection and not cli_failure
        required_reason = {'original_V01_30310_answered_heal_to_damage':'label_proof_local_semantics',
                           'semantic_damage_fake_label_full118':'label_proof_span_snippet',
                           'semantic_answer_moved_container':'label_proof_answer_container',
                           'semantic_anomaly_contains_answer':'label_proof_status_removal_has_answer',
                           'semantic_card_pending_and_receipt':'label_proof_pending_text',
                           'semantic_actual117_fully_resynchronized':'label_proof_batch_counts'}.get(name)
        if required_reason:
            accepted = accepted and required_reason in json.dumps(reasons, ensure_ascii=False)
        result = {'case': name, 'expected': 'PASS' if expected_success else 'REJECT', 'accepted': accepted,
                  'exitCode': process.returncode, 'command': cmd, 'rejectionReasons': [] if expected_success else reasons,
                  'validatorStatus': validation.get('status') if validation else None, 'labelProofRejected': proof_rejection,
                  'requiredRejectionReason': required_reason,
                  'counts': validation.get('counts') if validation else None,
                  'receiptSHA256': digest(receipt_path), 'fixesSHA256': digest(fixes_path),
                  'mutatedCards': {str(rel): digest(scratch/rel) for rel in card_documents},
                  'logs': {'stdout': str(case_dir/'stdout.txt'), 'stderr': str(case_dir/'stderr.txt')},
                  'mutationUsesLegalV2Base': True, 'afterHashResynchronized': bool(card_documents),
                  'fixesHashResynchronized': not explicit_bad_fixes_hash and 'changes' in receipt}
        write(case_dir/'result.json', result)
        cases.append(result)
        print(json.dumps({'case': name, 'exit': process.returncode, 'accepted': accepted}, ensure_ascii=True), flush=True)

    execute('positive_118')

    def field_attack(field, value):
        def mutate(receipt, edit):
            receipt['changes'][0][field] = value
        return mutate

    for field, value in [('span', [0, 2]), ('snippet', '傷害'), ('effect_type', 'ダメージ'),
                         ('old', '伤害'), ('new', '伤害'), ('oldPendingText', '伪造旧提示'),
                         ('newPendingText', '伪造新提示'), ('original', '伪造原文'), ('answerCount', 999)]:
        execute('receipt_'+field, field_attack(field, value))

    def damage_label(receipt, edit):
        # Replace a legal repair in the same row/card, retaining all 118 entries,
        # row/card denominators and the untouched 117 semantic repairs.
        for index, change in enumerate(receipt['changes']):
            row, effect = edit(change)
            damage = next((e for e in row['effects'] if e['label'] == '伤害'), None)
            if damage:
                oldrow = rows(card(args.label_baseline/'data/cards'/f"{change['rowId'].split('-')[0]}.js"))[change['rowId']]
                oldeffect = next(e for e in oldrow['effects'] if e['id'] == effect['id'])
                effect['label'], effect['pendingText'] = oldeffect['label'], oldeffect['pendingText']
                before_damage = deepcopy(damage)
                damage['label'], damage['pendingText'] = '回复', '数值尚未解出'
                replacement = deepcopy(change)
                replacement.update(effectId=damage['id'], old=before_damage['label'], new='回复',
                                   oldPendingText=before_damage['pendingText'], newPendingText='数值尚未解出',
                                   answerCount=len(damage['answers']))
                receipt['changes'][index] = replacement
                return
        raise AssertionError('No repair row with damage effect for semantic attack')
    execute('semantic_damage_fake_label_full118', damage_label)

    def original_v01_counterexample(receipt, edit):
        eid = '30310-denju-denju-denju_denju_id____cid-lvorder0-f0#e01'
        change = next(c for c in receipt['changes'] if c['effectId'] == eid)
        _, effect = edit(change)
        assert effect['label'] == '回复' and effect['answers'], 'Exact V01 counterexample must start at answered healing effect'
        effect['label'] = '伤害'
        change['new'] = '伤害'
        assert len(receipt['changes']) == 118
    execute('original_V01_30310_answered_heal_to_damage', original_v01_counterexample)

    def answer_container(receipt, edit):
        eid = '30310-denju-denju-denju_denju_id____cid-lvorder0-f0#e01'
        change = next(c for c in receipt['changes'] if c['effectId'] == eid)
        row, effect = edit(change)
        answer = effect['answers'].pop()
        other = next(e for e in row['effects'] if e['id'] == eid.removesuffix('e01')+'e02')
        assert answer['source']['effectId'] == eid, 'Keep real source identity while moving its container'
        other['answers'].append(answer)
        change['answerCount'] = len(effect['answers'])
        if any(c['effectId'] == other['id'] for c in receipt['changes']):
            next(c for c in receipt['changes'] if c['effectId'] == other['id'])['answerCount'] = len(other['answers'])
    execute('semantic_answer_moved_container', answer_container)

    def anomaly_answer(receipt, edit):
        donor = None
        for change in receipt['changes']:
            row, effect = edit(change)
            if effect['answers']:
                donor = deepcopy(effect['answers'][0])
                break
        assert donor
        target = next(c for c in receipt['changes'] if c['new'] == '解除异常状态')
        _, effect = edit(target)
        donor['source']['effectId'] = effect['id']
        effect['answers'].append(donor)
        target['answerCount'] = len(effect['answers'])
    execute('semantic_anomaly_contains_answer', anomaly_answer)

    def actual_pending(receipt, edit):
        change = receipt['changes'][0]
        _, effect = edit(change)
        effect['pendingText'] = '伪造已解答状态'
        change['newPendingText'] = effect['pendingText']
    execute('semantic_card_pending_and_receipt', actual_pending)

    def missing(receipt, edit):
        receipt['changes'].pop()
    execute('missing_change_full_counts', missing)

    def duplicate(receipt, edit):
        receipt['changes'][-1] = deepcopy(receipt['changes'][0])
    execute('duplicate_change_still118', duplicate)

    def unconsumed(receipt, edit):
        receipt['changes'][0]['effectId'] += '-nonexistent'
    execute('unconsumed_change_still118', unconsumed)

    def missing_card_field(field):
        def mutate(receipt, edit):
            next(iter(receipt['cards'].values())).pop(field)
        return mutate
    execute('missing_before_card_hash', missing_card_field('before'))
    execute('missing_after_card_hash', missing_card_field('after'))

    def missing_card(receipt, edit):
        receipt['cards'].pop(next(iter(receipt['cards'])))
    execute('missing_card_hash_entry', missing_card)

    def wrong_card_hash(field):
        def mutate(receipt, edit):
            next(iter(receipt['cards'].values()))[field] = '0'*64
        return mutate
    execute('wrong_before_hash', wrong_card_hash('before'))
    execute('wrong_after_hash', wrong_card_hash('after'))

    def wrong_fixes(receipt, edit):
        receipt['fixesSHA256'] = '0'*64
        return 'bad-fixes-hash'
    execute('wrong_fixes_hash', wrong_fixes)

    def wrong_ledger(receipt, edit):
        receipt['ledgerSHA256'] = '0'*64
    execute('wrong_ledger_hash', wrong_ledger)

    def pass_only(receipt, edit):
        receipt.clear()
        receipt['pass'] = True
    execute('pass_only_no_evidence', pass_only)

    def incomplete(receipt, edit):
        receipt['changes'] = receipt['changes'][:117]
        receipt['counts']['effects'] = 117
    execute('incomplete117_self_consistent_count', incomplete)

    def actual117(receipt, edit):
        target = next(c for c in receipt['changes'] if c['old'] == '回复' and c['new'] == '解除异常状态' and c['answerCount'] == 0)
        row, effect = edit(target)
        cid = target['rowId'].split('-', 1)[0]
        oldrow = rows(card(args.label_baseline/'data/cards'/f'{cid}.js'))[target['rowId']]
        oldeffect = next(e for e in oldrow['effects'] if e['id'] == target['effectId'])
        assert not effect['answers'] and not oldeffect['answers']
        effect['label'], effect['pendingText'] = oldeffect['label'], oldeffect['pendingText']
        receipt['changes'].remove(target)
        affected_cards = {c['rowId'].split('-', 1)[0]+'.js' for c in receipt['changes']}
        receipt['cards'] = {name: hashes for name, hashes in receipt['cards'].items() if name in affected_cards}
        receipt['counts'] = {'effects': len(receipt['changes']), 'rows': len({c['rowId'] for c in receipt['changes']}), 'cards': len(affected_cards)}
        assert receipt['counts']['effects'] == 117
    execute('semantic_actual117_fully_resynchronized', actual117)

    def wrong_batch(receipt, edit):
        receipt['batch'] = 'other-batch'
    execute('wrong_batch', wrong_batch)

    summary = {'pass': all(c['accepted'] for c in cases), 'sourceHashes': source_hashes,
               'inputs': {'reader': str(args.reader), 'baselineC18': str(args.baseline),
                          'labelBaselineC19': str(args.label_baseline), 'receipt': str(args.receipt), 'batch': args.batch},
               'copyMethod': 'shutil.copytree(copy_function=shutil.copy2); no hard links',
               'caseCount': len(cases), 'onlyCase': args.only_case, 'cases': cases,
               'limits': ['Negative outcomes validate this exact CLI/source/receipt; no browser or game-runtime claim.']}
    write(work/'fixture_results.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reader', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--label-baseline', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--batch', default='reader_c19_r01_20261107')
    parser.add_argument('--work', type=Path, default=ROOT/'work/reader_v01_fixtures_20261107')
    parser.add_argument('--only-case', help='Execute one named case in a new independent --work directory')
    args = parser.parse_args()
    for name in ('reader', 'baseline', 'label_baseline', 'receipt'):
        setattr(args, name, getattr(args, name).resolve())
    result = run(args)
    raise SystemExit(0 if result['pass'] else 1)
