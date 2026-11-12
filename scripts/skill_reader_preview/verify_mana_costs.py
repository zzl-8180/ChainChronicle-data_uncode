"""Verify reader mana annotations against formal records and representative cases."""
import argparse
import json
from pathlib import Path

from mana_costs import ROOT, cost_info, read, read_card_js
from versioned_outputs import fresh_output


def verify(root, out):
    content = (out/'data/mana_costs.js').read_text(encoding='utf-8')
    data = json.loads(content.split('=', 1)[1].strip().removesuffix(';'))
    records, checks = data['records'], []

    def check(ok, label):
        if not ok:
            raise AssertionError(label)
        checks.append(label)

    count = 0
    for path in sorted((out/'data/cards').glob('*.js')):
        card = read_card_js(path)
        formal = read(root/f"output/character_skills/pages/{card['cid']}/card.json")
        by_anchor = {skill['rows'][0]['row_id']: skill for group in formal['groups']
                     if group['group'] in ('special_move', 'denju')
                     for skill in group['skills'] if skill['rows']}
        for group in card['groups']:
            if group['id'] not in ('special_move', 'denju'):
                continue
            for skill in group['skills']:
                anchor = skill['rows'][0]['id']
                annotated = records[anchor]
                source = by_anchor[anchor]
                assert annotated['costState'] == source['cost_state'], anchor
                assert annotated['rawCost'] == source['cost'], anchor
                assert annotated['source']['json_pointer'] == source['source']['json_pointer'], anchor
                assert [(r['id'], r['original']) for r in skill['rows']] == [(r['row_id'], r['japanese']) for r in source['rows']], anchor
                if annotated['basis'] == 'explicit_zero_text':
                    assert source['cost'] is None and 'この技は0マナで発動でき' in source['original_text'], anchor
                    assert annotated['cost'] == 0 and annotated['source']['field'] == '/sinfo', anchor
                else:
                    assert annotated['basis'] == 'raw_field' and annotated['cost'] == source['cost'], anchor
                for branch in annotated['branches']:
                    raw = branch['raw']
                    assert raw['patternid'] == branch['recordId'], anchor
                    assert ('scost' in raw) == (branch['costState'] != 'missing'), anchor
                    if 'scost' in raw:
                        assert raw['scost'] == branch['cost'] == branch['rawCost'], anchor
                count += 1
    check(count == len(records), 'all frozen special/denju skills have one sentence-verified annotation')

    def find(cid, group, record):
        found = [item for item in records.values() if item['cid'] == cid and item['group'] == group and item['source']['recordId'] == record]
        check(len(found) == 1, f'unique sample {cid}/{group}/{record}')
        return found[0]

    for cid, normal, zero in [(20622, 42062200, 42062205), (350, 40035000, 40035002), (1303, 40130300, 40130302)]:
        check(find(cid, 'special_move', normal)['cost'] == 2, f'{cid} configured ordinary consumption is 2')
        item = find(cid, 'special_move', zero)
        check(item['cost'] == 0 and item['rawCost'] is None and item['costState'] == 'missing' and item['basis'] == 'explicit_zero_text', f'{cid} zero prose does not overwrite missing raw field')
        check(find(cid, 'denju', cid)['cost'] == 2, f'{cid} denju retains its own 2 consumption')
    for cid, normal in [(350, 40035000), (1303, 40130300), (20332, 42033200)]:
        item = find(cid, 'special_move', normal)
        check(item['cost'] == 2 and {branch['cost'] for branch in item['branches']} == {1, 2}, f'{cid} branch costs preserved without subtracting twice')
        check(bool(item['conditions']), f'{cid} literal reduction context retained')
    check(find(2239, 'special_move', 2239)['cost'] == 0, 'CID2239 explicit charainfo skill_cost 0 retained')
    # Eight empty-text patterns with absent scost are excluded from rendered
    # skills, but any future consumer of their metadata must keep them unknown.
    missing = read(root/'output/character_skills/pages/10213/card.json')
    skill = next(s for g in missing['groups'] for s in g['skills'] if s['table'] == 'bosspattern' and s['record_id'] == 41021302)
    item = cost_info(skill)
    check(item['cost'] is None and item['costState'] == 'missing' and item['basis'] == 'unknown', 'empty prose + missing scost stays unknown')
    report = {'status': 'PASS', 'skillsChecked': count, 'checks': checks,
              'limits': 'Original configured costs and explicit prose only; runtime reductions and mana colors not verified.'}
    report_dir=fresh_output('projects/reader/reports/review','mana-costs')
    (report_dir/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'skillsChecked': count, 'checks': len(checks)}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT/'output/character_skills/reader_full_20261106')
    args = parser.parse_args()
    verify(args.root.resolve(), args.output.resolve())
