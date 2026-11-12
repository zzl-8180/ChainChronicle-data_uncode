"""Read-only upstream preflight. Exit 0=same, 2=review/update needed, 3=blocked.

This inspects a completed local snapshot; it never builds pages or starts mainline.
The result is a point-in-time preflight, not a lock or a publication approval.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

from seal_reader import AUDIT, audit_path, inventory
from revalidate_sidecars import payload, verify_adaptation

HERE = Path(__file__).resolve().parent


def inspect(root, output, audit_dir=AUDIT):
    base = root / 'output/character_skills'
    pages = base / 'pages'
    observed = {}
    errors = []

    def data(path):
        raw = path.read_bytes()
        value = sha256(raw).hexdigest()
        if path in observed and observed[path] != value:
            errors.append('input changed between reads: ' + str(path))
        observed.setdefault(path, value)
        return json.loads(raw.decode('utf-8-sig'))

    def digest(path):
        value = sha256(path.read_bytes()).hexdigest()
        observed[path] = value
        return value

    def require(condition, message):
        if not condition:
            errors.append(message)

    def inside(relative):
        path = (pages / relative).resolve()
        if not path.is_relative_to(pages.resolve()):
            raise ValueError('campaign report path escapes pages root')
        return path

    result = {'status': 'blocked', 'exitCode': 3, 'changedCards': [],
              'reasons': errors, 'readOnly': True, 'automaticUpdate': False,
              'scope': 'point-in-time local snapshot preflight; formal review still required',
              'statusScope': 'base snapshot alignment and observed Web integrity; not complete semantic equivalence',
              'baseStatus': 'blocked', 'fullSemanticConsistency': 'not_established_by_this_check',
              'webIntegrity': {'status': 'not_checked', 'missingFiles': [], 'hashMismatches': []},
              'sidecarStatus': {'status': 'not_checked'},
              'requiredValidation': [
                  '主线 card_page_verify_full.py 与账本正式验证',
                  '变化卡语义迁移审定（保留原句、分支条件与未知状态）',
                  '分支/条件/法珠旁注重建及来源哈希验证',
                  'verify_full.py、verify_regressions.py 与展示专项验证'],
              'nextSteps': []}
    try:
        pointer = data(pages / '_batch/campaign_latest.json')
        campaign = data(inside(pointer['report']))
        metrics = data(base / 'effect_ledger/metrics.json')
        snapshot = metrics['snapshot']
        signature = campaign['signature']
        result['upstreamSnapshot'] = snapshot
        require(campaign['campaign_complete'] is True and
                campaign['completed'] == campaign['expected'] > 0, 'campaign is incomplete')
        require(not campaign['unresolved_latest_failures'], 'campaign has unresolved latest failures')
        require(signature == snapshot['campaign_signature'], 'campaign and ledger signatures differ')
        require(digest(base / 'profiles/rules.json')[:16] == snapshot['rules_json_sha256_16'],
                'rules and ledger hashes differ')
        card_ids = set()
        require(bool(campaign['cohort_snapshots']), 'campaign has no cohort snapshots')
        for cohort in campaign['cohort_snapshots']:
            report_path = inside(cohort['report'])
            report = data(report_path)
            require(cohort['status'] == 'MATCHING_SIGNATURE_SNAPSHOT' and
                    cohort['completed'] == cohort['expected'], 'cohort snapshot incomplete: ' + cohort['cohort'])
            require(report['signature'] == signature and report['cohort_complete'] is True and
                    report['completed'] == report['expected'], 'cohort report inconsistent: ' + cohort['cohort'])
            require(not report['failed'] and not report['unresolved_latest_failures'] and
                    not report['pending_cids'] and not report['stale_or_invalid_cids'],
                    'cohort has failed/pending/invalid cards: ' + cohort['cohort'])
            latest = data(pages / '_batch' / cohort['cohort'] / 'latest.json')
            require(inside(latest['report']) == report_path, 'cohort latest has advanced: ' + cohort['cohort'])
            for stat in report['statistics']:
                cid = str(stat['cid'])
                require(cid not in card_ids, 'duplicate cohort card: ' + cid)
                card_ids.add(cid)
        disk_ids = {p.parent.name for p in pages.glob('*/card.json') if p.parent.name.isdigit()}
        require(card_ids == disk_ids, 'campaign card set differs from pages card set')
        require(len(card_ids) == campaign['expected'] == metrics['rows']['cards'], 'card counts differ')
        hashes = {}
        descriptions = 0
        for cid in sorted(card_ids, key=int):
            folder = pages / cid
            require(not (folder / 'reuse_blocked.json').exists(), 'card update/reuse blocked: ' + cid)
            receipt = data(folder / 'receipt.json')
            require(receipt['status'] == 'SUCCESS' and receipt['signature'] == signature,
                    'card receipt is not successful/current: ' + cid)
            require(set(receipt['files']) == {'card.json', 'index.html'}, 'invalid artifact set: ' + cid)
            for name in ('card.json', 'index.html'):
                require(digest(folder / name) == receipt['files'].get(name), 'card artifact hash differs: ' + cid + '/' + name)
            hashes[cid] = observed[folder / 'card.json']
            card = data(folder / 'card.json')
            require(str(card['cid']) == cid, 'card identity differs: ' + cid)
            descriptions += sum(len(s['rows']) for g in card['groups'] for s in g['skills'])
            # A failure after the frozen cohort report must also block reuse.
            for cohort in campaign['cohort_snapshots']:
                attempt = pages / '_batch' / cohort['cohort'] / 'card_latest' / (cid + '.json')
                if attempt.is_file():
                    a = data(attempt)
                    require(a.get('status') != 'FAILED', 'latest card attempt failed: ' + cid)
        require(descriptions == metrics['rows']['descriptions'], 'page description count differs from ledger metrics')
        row_counts, effect_counts = Counter(), Counter()
        ledger_ids = set()
        ledger = base / 'effect_ledger/ledger.jsonl'
        # Hash before and after streaming to reject a changing ledger.
        digest(ledger)
        with ledger.open(encoding='utf-8-sig') as stream:
            for line in stream:
                entry = json.loads(line)
                require((entry.get('snapshot_id') or entry.get('input_snapshot', {}).get('snapshot_id')) ==
                        snapshot['snapshot_id'], 'ledger contains a different snapshot')
                ledger_ids.add(str(entry['cid']))
                if entry['record_type'] == 'description':
                    row_counts[entry['ledger_row_status']] += 1
                else:
                    effect_counts[entry['status']] += 1
        require(ledger_ids == card_ids, 'ledger card set differs from campaign')
        require(dict(row_counts) == metrics['descriptions']['by_ledger_status'], 'ledger description counts differ')
        require(dict(effect_counts) == {k: v['all'] for k, v in metrics['effects']['by_status'].items()},
                'ledger effect counts differ')
        web = data(output / 'build_receipt.json')
        require(web.get('validation') == 'PASSED_DATA_ALIGNMENT', 'Web build receipt has no passed data alignment')
        old_hashes = web['sourceHashes']
        require(bool(old_hashes), 'Web receipt has no source hashes')
        result['webSnapshot'] = web['snapshot']
        changed = sorted((cid for cid in hashes.keys() | old_hashes.keys()
                          if hashes.get(cid) != old_hashes.get(cid)), key=int)
        result['changedCards'] = [int(cid) for cid in changed]
        result['addedCards'] = [int(cid) for cid in sorted(hashes.keys() - old_hashes.keys(), key=int)]
        result['removedCards'] = [int(cid) for cid in sorted(old_hashes.keys() - hashes.keys(), key=int)]
        result['checkedCards'] = len(hashes)
        result['versionChanged'] = any(web['snapshot'].get(k) != snapshot[k] for k in
                                       ('campaign_signature', 'rules_json_sha256_16', 'snapshot_id'))
        result['baseStatus'] = 'blocked' if errors else ('upstream_changed' if changed or result['versionChanged'] else 'same')
        # A build receipt proves inputs, not that the served files still exist.
        integrity = result['webIntegrity']
        required = ['index.html', 'app.js', 'branches.js', 'inline.js', 'levels.js', 'style.css',
                    'frontend_receipt.json', 'data/catalog.js']
        required += ['data/' + n + '.js' for n in ('branch_candidates', 'branch_conditions', 'mana_costs', 'branch_assessments')]
        required += ['data/cards/' + cid + '.js' for cid in old_hashes]
        integrity['missingFiles'] = [rel for rel in required if not (output / rel).is_file()]
        for rel in integrity['missingFiles']:
            require(False, 'Web file missing: ' + rel)
        if not integrity['missingFiles']:
            frontend = data(output / 'frontend_receipt.json')
            require(frontend['snapshot'] == web['snapshot'], 'frontend and Web base snapshots differ')
            require(bool(frontend.get('webHashes')), 'frontend receipt has no output hashes')
            for rel, expected in frontend.get('webHashes', {}).items():
                path = (output / rel).resolve()
                require(path.is_relative_to(output.resolve()), 'frontend hash path escapes Web output: ' + rel)
                if not path.is_relative_to(output.resolve()):
                    continue
                if not path.is_file() or digest(path) != expected:
                    integrity['hashMismatches'].append(rel)
                    require(False, 'Web output hash differs: ' + rel)
            # Explicitly inspect HTML dependencies rather than trust receipts alone.
            for rel in re.findall(r'(?:src|href)="([^"?#]+\.(?:js|css))(?:\?[^"#]*)?"', (output / 'index.html').read_text(encoding='utf-8')):
                path = (output / rel).resolve()
                require(path.is_relative_to(output.resolve()) and path.is_file(), 'Web dependency missing/escaping: ' + rel)
            candidates = payload(output / 'data/branch_candidates.js')
            sidecar = result['sidecarStatus']
            sidecar['originalSnapshot'] = candidates.get('readerSnapshot')
            sidecar['baseSnapshot'] = web['snapshot']
            sidecar['regeneratedByBaseBuild'] = web.get('sidecarsRegenerated')
            adaptation_path = output / audit_path(audit_dir) / 'sidecar_adaptation.json'
            if adaptation_path.is_file():
                try:
                    adapted = verify_adaptation(output, adaptation_path, root)
                    sidecar['status'] = 'revalidated_for_current_base'
                    sidecar['receipt'] = adaptation_path.relative_to(output).as_posix()
                    sidecar['counts'] = adapted['counts']
                    integrity['runtimeFilesHashChecked'] = len(adapted['runtimeHashes'])
                except (OSError, ValueError, KeyError, TypeError) as error:
                    sidecar['status'] = 'adaptation_invalid'
                    require(False, 'Sidecar adaptation invalid: ' + str(error))
            else:
                sidecar['status'] = 'adaptation_missing'
                require(False, 'Sidecar adaptation receipt missing; base alignment does not prove reused sidecar compatibility')
            assessments = payload(output / 'data/branch_assessments.js')
            for name, expected in assessments.get('inputHashes', {}).items():
                path = (output / 'data' / (name + '.js')).resolve()
                require(path.is_relative_to((output / 'data').resolve()), 'sidecar input hash path escapes Web data')
                if path.is_relative_to((output / 'data').resolve()):
                    require(path.is_file() and digest(path) == expected, 'Sidecar input hash differs: ' + name)
            seal_path = output / audit_path(audit_dir) / 'stage_seal.json'
            if seal_path.is_file():
                seal = data(seal_path)
                require(inventory(output, audit_dir) == seal.get('files'), 'Web full-stage sealed content differs')
                integrity['sealStatus'] = 'checked'
            else:
                integrity['sealStatus'] = 'not_sealed'
        integrity['status'] = 'passed' if not errors else 'blocked'
        # Detect concurrent mutations of every observed source, including latest pointers.
        for path, value in observed.items():
            require(path.is_file() and sha256(path.read_bytes()).hexdigest() == value,
                    'input changed during preflight: ' + str(path.relative_to(root)))
        require({p.parent.name for p in pages.glob('*/card.json') if p.parent.name.isdigit()} == disk_ids,
                'card set changed during preflight')
        require(not any((pages / cid / 'reuse_blocked.json').exists() for cid in card_ids),
                'card update/reuse blocker appeared during preflight')
        if not errors:
            result['status'] = 'upstream_changed' if changed or result['versionChanged'] else 'same'
            result['exitCode'] = 2 if result['status'] == 'upstream_changed' else 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(type(error).__name__ + ': ' + str(error))
    # Multiple ledger rows can share a failure; keep diagnostics readable.
    result['reasons'] = list(dict.fromkeys(errors))
    if result['status'] == 'blocked':
        result['nextSteps'] = ['由主线负责人完成失败恢复及正式页面/账本一致性验证后，重新运行本 --check；保留当前Web。']
    elif result['status'] == 'upstream_changed':
        result['nextSteps'] = ['对 changedCards 做语义迁移审定；在独立输出目录重建并验证，通过后再切换Web入口。',
                               'python -B scripts/skill_reader_preview/build.py --help',
                               'python -B scripts/skill_reader_preview/verify_full.py --help']
    else:
        result['nextSteps'] = ['基础数据已对应本次主线快照且所检Web文件哈希有效；完整语义仍以专项审定为准。此检查不启动后台同步。']
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', required=True, help='inspect only; do not update Web')
    parser.add_argument('--root', type=Path, default=HERE.parents[1])
    parser.add_argument('--output', type=Path, help='existing Web directory to compare')
    parser.add_argument('--report', type=Path, help='optional independent JSON report (must not exist)')
    parser.add_argument('--audit-dir', default=AUDIT, help='relative current audit directory; historical receipts are not rewritten')
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / 'output/character_skills/reader_full_20261106').resolve()
    result = inspect(root, output, args.audit_dir)
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.report:
        # Exclusive creation prevents accidental overwrite of formal data/receipts.
        with args.report.open('x', encoding='utf-8') as stream:
            stream.write(text)
    print(text, end='')
    return result['exitCode']


if __name__ == '__main__':
    sys.exit(main())
