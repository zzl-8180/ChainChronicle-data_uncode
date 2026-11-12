"""Read-only mana annotations for frozen reader skills; no runtime simulation."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from rerun_output import read_path, require_new_files, review_output, write_new_text

ROOT = Path(__file__).resolve().parents[2]
ZERO = re.compile(r'この技は[0０]マナで発動でき')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_card_js(path):
    return json.loads(path.read_text(encoding='utf-8').split(']=', 1)[1].strip().removesuffix(';'))


def cost_info(skill):
    """Missing scost never becomes zero; explicit prose is a separate basis."""
    text = skill.get('original_text') or ''
    literal_zero = ZERO.search(text)
    raw_cost = skill.get('cost')
    state = skill.get('cost_state')
    source = dict(skill['source'])
    source.update(table=skill['table'], recordId=skill['record_id'], layer=skill['layer'])
    field = 'skill_cost' if skill['table'] == 'charainfo' else 'scost'
    result = {'cost': None, 'costState': state, 'rawCost': raw_cost,
              'basis': 'unknown', 'source': {**source, 'field': '/' + field}}
    if state in ('present', 'zero') and isinstance(raw_cost, int) and not isinstance(raw_cost, bool) and raw_cost >= 0:
        result.update(cost=raw_cost, basis='raw_field')
    elif literal_zero:
        result.update(cost=0, basis='explicit_zero_text')
        result['source'] = {**source, 'field': '/' + skill['text_field'],
                            'quote': literal_zero.group(0)}
    if literal_zero and raw_cost not in (None, 0):
        raise ValueError(f"Conflicting cost and explicit zero: {skill['skill_id']}")
    result['explicitZeroText'] = bool(literal_zero)
    result['conditions'] = [
        {'rowId': row['row_id'], 'original': row['japanese']}
        for row in skill['rows']
        if 'マナ' in row['japanese'] and re.search(r'減[るりら]|消費せず|消費しない', row['japanese'])
    ]
    return result


def raw_branch(skill):
    evidence = [item for item in skill.get('record_evidence', [])
                if item['table'] == 'bosspattern' and item['record_id'] == skill['record_id']]
    if len(evidence) != 1:
        raise ValueError(f"Non-unique branch evidence: {skill['skill_id']}")
    raw = evidence[0]['raw_record']
    return {**cost_info(skill), 'recordId': skill['record_id'], 'name': skill['name'],
            'raw': raw, 'hasIndependentText': bool(skill.get('original_text')),
            'association': 'same_exact_name_only; runtime selector not interpreted'}


def build_costs(root, out, destination=None):
    destination = destination or out
    sidecar = destination/'data/mana_costs.js'
    inventory = destination/'audit/mana_costs_20261107/inventory.json'
    require_new_files(sidecar, inventory)
    records, unmatched, sources = {}, [], {}
    totals, all_costs = Counter(), Counter()
    for file in sorted((out/'data/cards').glob('*.js')):
        frozen = read_card_js(file)
        cid = frozen['cid']
        formal_path = root/f'output/character_skills/pages/{cid}/card.json'
        formal = read(formal_path)
        sources[str(cid)] = {'formalSha256': sha256(formal_path.read_bytes()).hexdigest(),
                             'readerSha256': sha256(file.read_bytes()).hexdigest()}
        groups = {group['group']: group for group in formal['groups']}
        for group in formal['groups']:
            if group['group'] in ('special_move', 'denju'):
                for skill in group['skills']:
                    all_costs[(group['group'], skill['table'], skill.get('cost_state'), skill.get('cost'))] += 1
        for group in frozen['groups']:
            if group['id'] not in ('special_move', 'denju'):
                continue
            formal_skills = groups[group['id']]['skills']
            for skill in group['skills']:
                if not skill['rows']:
                    continue
                anchor = skill['rows'][0]['id']
                # Verify every sentence as well as its stable row identity. Do
                # not parse an ordinal from the row ID to invent a pattern ID.
                wanted = [(row['id'], row['original']) for row in skill['rows']]
                matches = [candidate for candidate in formal_skills
                           if [(row['row_id'], row['japanese']) for row in candidate['rows']] == wanted]
                if len(matches) != 1:
                    unmatched.append({'cid': cid, 'rowId': anchor, 'matches': len(matches)})
                    continue
                original = matches[0]
                info = cost_info(original)
                info.update(cid=cid, group=group['id'], rowId=anchor, name=skill['name'],
                            skillId=original['skill_id'])
                # Same-name siblings are a raw comparison inventory, not a
                # claim about which selector realizes a prose condition.
                info['branches'] = [raw_branch(candidate) for candidate in formal_skills
                                    if candidate['table'] == 'bosspattern' and
                                    candidate['name'] == original['name'] and original['name']]
                if anchor in records:
                    raise ValueError(f'Duplicate reader anchor: {anchor}')
                records[anchor] = info
                totals[info['basis']] += 1
    if unmatched:
        raise ValueError(f'Reader/formal sentence mismatch: {unmatched[:5]}')
    result = {'schema': 1, 'records': records,
              'scope': 'Original configured consumption only. Missing is not zero. Explicit zero prose has a separate basis. No runtime ability reductions, job colors, selector decoding, or subtraction applied.'}
    write_new_text(sidecar, 'window.CC_MANA_COSTS='+json.dumps(result, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')+';\n')
    report = {'readerSkills': len(records), 'basisCounts': dict(totals), 'unmatched': unmatched,
              'formalCosts': [dict(group=k[0], table=k[1], costState=k[2], cost=k[3], count=v)
                              for k, v in sorted(all_costs.items(), key=lambda item: str(item[0]))],
              'sources': sources}
    write_new_text(inventory, json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('readerSkills', 'basisCounts', 'unmatched')}, ensure_ascii=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, help='Use an explicit stage for both input and new sidecars')
    args = parser.parse_args()
    destination = review_output('mana-costs', args.output)
    source = destination if args.output else read_path(args.root/'output/character_skills/reader_full_20261106', root=args.root)
    build_costs(args.root.resolve(), source, destination)
