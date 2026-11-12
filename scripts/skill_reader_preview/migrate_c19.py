"""Approve unchanged Chinese against the exact, reversible C18 -> C19 delta.

Only writes a new migration receipt. Never changes semantic_sentences.json,
formal pages, the frozen review, or reader files. Unknown differences fail.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = 'output/character_skills/cycle_reports/C19_r01_20261107/report_data.json'
FROZEN = 'output/character_skills/reader_full_20261106'
OLD = '01c05f78-cf9451c6ff47fcfb'
NEW = '99bee2a1-cf9451c6ff47fcfb'
DRIFT_CIDS = {7250,30105,30107,30220,30223,30225,30301,30329,30334}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def card_rows(card):
    return {r['row_id']: r for g in card['groups'] for s in g['skills'] for r in s['rows']}


def frozen_fingerprints(root, cids):
    result = {}
    for cid in cids:
        text = (root/FROZEN/f'data/cards/{cid}.js').read_text(encoding='utf-8')
        card = json.loads(text.split(']=', 1)[1].strip().removesuffix(';'))
        for g in card['groups']:
            for s in g['skills']:
                for r in s['rows']:
                    for a in [a for e in r['effects'] for a in e['answers']] + r['unboundAnswers']:
                        source = a['source']
                        binding = (source.get('originalBinding') or {}).get('g1_b1_binding')
                        if binding and 'page_sha256' in binding:
                            result[f"{r['id']}:{source['answerIndex']}"] = binding['page_sha256']
    return result


def inspect(root, semantic, fingerprints):
    """Invert only the audited answer append and known fingerprint fields.

    Matching the reconstructed *whole card bytes* to the old reviewed hash
    protects wording, context, sentence boundaries, references and sources.
    """
    report = read(root/REPORT)
    metrics = read(root/'output/character_skills/effect_ledger/metrics.json')
    if report['snapshot'] != NEW or metrics['snapshot']['snapshot_id'] != NEW:
        raise ValueError('C19 migration requires the accepted C19 snapshot')
    targets = {r['row_id']: r for b in report['batch_results'] for r in b['rows']}
    if len(targets) != 133:
        raise ValueError('C19 target denominator changed')
    hashes, changes, added, unknown = {}, [], 0, 0
    for cid, old_hash in semantic['sourceHashes'].items():
        path = root/f'output/character_skills/pages/{cid}/card.json'
        raw = path.read_bytes()
        hashes[cid] = sha256(raw).hexdigest()
        if hashes[cid] == old_hash:
            continue
        card = json.loads(raw)
        before = deepcopy(card)
        target_count, fingerprint_count = 0, 0
        for rid, row in card_rows(before).items():
            if rid in targets:
                target = targets[rid]
                if canonical(row) != canonical(target['after']):
                    raise ValueError('C19 current row differs from accepted after: '+rid)
                old = target['before']
                if canonical({k:v for k,v in old.items() if k!='answers'}) != canonical({k:v for k,v in row.items() if k!='answers'}):
                    raise ValueError('C19 changed a non-answer field: '+rid)
                if row['answers'][:len(old['answers'])] != old['answers']:
                    raise ValueError('C19 changed an existing answer: '+rid)
                increment = len(row['answers'])-len(old['answers'])
                if increment <= 0:
                    raise ValueError('C19 target is not an answer append: '+rid)
                added += increment
                unknown += len(target['unresolved_effects'])
                row['answers'] = deepcopy(old['answers'])
                target_count += 1
            for index, answer in enumerate(row['answers']):
                key = f'{rid}:{index}'
                if key in fingerprints:
                    binding = (answer.get('binding') or {}).get('g1_b1_binding')
                    if not binding:
                        raise ValueError('Fingerprint binding disappeared: '+key)
                    if binding['page_sha256'] != fingerprints[key]:
                        fingerprint_count += 1
                        binding['page_sha256'] = fingerprints[key]
        # Formal pages were serialized as indent=2, UTF-8, CRLF, final newline.
        reconstructed = (json.dumps(before, ensure_ascii=False, indent=2, allow_nan=False)+'\n').replace('\n', '\r\n').encode('utf-8')
        if sha256(reconstructed).hexdigest() != old_hash:
            raise ValueError('Unapproved full-card difference, Chinese cannot be reused: '+cid)
        changes.append({'cid':int(cid), 'beforeSHA256':old_hash, 'afterSHA256':hashes[cid],
                        'answerRows':target_count, 'fingerprintFields':fingerprint_count,
                        'validation':'EXACT_OLD_WHOLE_CARD_RECONSTRUCTION'})
    if len(changes)!=139 or added!=407 or unknown!=45 or sum(c['answerRows'] for c in changes)!=133:
        raise ValueError('C19 migration denominator mismatch')
    if {c['cid'] for c in changes if c['fingerprintFields']} != DRIFT_CIDS or sum(c['fingerprintFields'] for c in changes)!=16:
        raise ValueError('C19 fingerprint drift differs from the accepted nine-card scope')
    return {'acceptedCycle':'C19', 'beforeSnapshot':OLD, 'afterSnapshot':NEW,
            'sourceHashes':hashes, 'changes':changes,
            'counts':{'cards':len(hashes),'changedCards':len(changes),'targetRows':133,
                      'addedAnswers':added,'sameSentenceUnknownEffects':unknown},
            'validation':'PASSED_EXACT_C19_SEMANTIC_REUSE'}


def validate_receipt(root, path, semantic):
    receipt = read(path)
    if receipt.get('semanticSHA256') != digest(HERE/'semantic_sentences.json'):
        raise ValueError('Migration semantic-review hash mismatch')
    if receipt.get('reportSHA256') != digest(root/REPORT):
        raise ValueError('Accepted C19 report changed after migration')
    actual = inspect(root, semantic, receipt['oldFingerprints'])
    for key, value in actual.items():
        if canonical(receipt.get(key)) != canonical(value):
            raise ValueError('Migration receipt no longer matches current source: '+key)
    return receipt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=HERE.parents[1])
    ap.add_argument('--output',type=Path,required=True,help='New receipt path; existing files are never overwritten')
    args = ap.parse_args()
    root = args.root.resolve()
    if args.output.exists():
        raise FileExistsError('Keep prior migration receipts; choose a new output path')
    semantic = read(HERE/'semantic_sentences.json')
    frozen = read(root/FROZEN/'build_receipt.json')
    if frozen['snapshot']['snapshot_id'] != OLD or frozen['sourceHashes'] != semantic['sourceHashes']:
        raise ValueError('Frozen C18 reader does not match reviewed source hashes')
    changed = [cid for cid,h in semantic['sourceHashes'].items()
               if digest(root/f'output/character_skills/pages/{cid}/card.json')!=h]
    fingerprints = frozen_fingerprints(root,changed)
    result = inspect(root,semantic,fingerprints)
    result.update({'schema':'reader-c19-semantic-migration-v1', 'createdAt':datetime.now(timezone.utc).isoformat(),
                   'semanticSHA256':digest(HERE/'semantic_sentences.json'),
                   'reportPath':REPORT, 'reportSHA256':digest(root/REPORT),
                   'frozenBuildReceiptSHA256':digest(root/FROZEN/'build_receipt.json'),
                   'oldFingerprints':fingerprints,
                   'scope':'Original Chinese review is reused only after exact old-card reconstruction; new answers remain inferred and same-sentence unknown effects remain visible.'})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result['counts'],ensure_ascii=False))


if __name__=='__main__':
    main()
