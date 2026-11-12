"""Read-only source checks; writes only our lead_comparison/evidence.json."""
import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from project_layout_paths import read_path
from versioned_outputs import fresh_output

ROOT = Path(__file__).resolve().parent.parent
CACHE = read_path(ROOT / 'output/cache_full_20261015_v3/decoded', root=ROOT)
APK = read_path(ROOT / 'output/base_master', root=ROOT)
REF = read_path(ROOT / '其他人的参考', root=ROOT)
OLD = REF / 'claude_cc_site_pages'
FIRST = REF / 'claude_cc_site_pages 20261023'
LATE = REF / 'claude_cc_site_pages_给GPT_20261023/claude_cc_site_pages'
inputs = {}


def input_key(path):
    # Keep historical logical hash keys; physical data roots may be outside code ROOT.
    roots = ((CACHE, Path('output/cache_full_20261015_v3/decoded')),
             (APK, Path('output/base_master')),
             (REF, Path('其他人的参考')),
             (read_path(ROOT / 'output/character_skills', root=ROOT), Path('output/character_skills')))
    for physical, logical in roots:
        try:
            return (logical / path.relative_to(physical)).as_posix()
        except ValueError:
            pass
    return path.relative_to(ROOT).as_posix()


def read(path):
    raw = path.read_bytes()
    inputs[input_key(path)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw.decode('utf-8-sig'))


def index(rows, key):
    return {r[key]: r for r in rows}


def correlate(rows, keyword, slot):
    result = {}
    for label, subset in [('with', [r for r in rows if keyword in (r.get('text') or '')]),
                          ('without', [r for r in rows if keyword not in (r.get('text') or '')])]:
        result[label] = dict(total=len(subset), present=sum(slot in r for r in subset),
                            null=sum(slot in r and r[slot] is None for r in subset),
                            zero=sum(slot in r and r[slot] == 0 for r in subset),
                            nonzero=sum(isinstance(r.get(slot), (int, float)) and abs(r[slot]) > 1e-9 for r in subset))
    return result


def main():
    result = {}
    tables = {name: {(r['table'], r['type'], r['slot']): r for r in read(p / 'param_table.json')['rows']}
              for name, p in [('old', OLD), ('first', FIRST), ('late', LATE)]}
    result['deltas'] = {}
    for a, b in [('old', 'first'), ('old', 'late'), ('first', 'late')]:
        x, y = tables[a], tables[b]
        common = x.keys() & y.keys()
        changed = [k for k in common if any(x[k].get(f) != y[k].get(f) for f in ('status', 'label', 'conversion', 'unit'))]
        result['deltas'][a + '_to_' + b] = {'added': len(y.keys() - x.keys()), 'semantic_changed': len(changed), 'keys': sorted(changed)}
    rules = read(read_path(ROOT / 'output/character_skills/profiles/rules.json', root=ROOT))
    result['current_rules'] = {k: v for k, v in rules.items() if k in ['skilllist|1017|/param2', 'skilllist|67|/param2']}
    keys = [('skilllist', 99, 'param8'), ('skilllist', 99, 'param9'), ('skilllist', 28, 'param3'),
            ('skilllist', 2012, 'param7'), ('skilllist', 2012, 'param8'), ('skilllist', 2003, 'param5'),
            ('skilllist', 2003, 'param6'), ('skilllist', 9, 'param0'), ('skilllist', 96, 'param1')]
    result['late_selected_rules'] = [tables['late'].get(k) for k in keys]
    result['late_over_one_hits'] = [r for r in tables['late'].values() if r['hits'] > r['cards_with_value']]

    chars = {r['cid']: ('APK', r) for r in read(APK / '_mdCharacter.json')['charainfo']}
    chars.update({r['cid']: ('CACHE', r) for r in read(CACHE / 'charainfo.data5.json.raw')['charainfo']})
    support = {'CACHE': index(read(CACHE / 'supporterskill.data5.json.raw')['supporterskill'], 'ability_id'),
               'APK': index(read(APK / '_mdSAbirity.json')['supporterskill'], 'ability_id')}
    linkpath = read_path(ROOT / 'output/character_skills/links/character_skills.jsonl', root=ROOT)
    raw = linkpath.read_bytes()
    inputs[input_key(linkpath)] = hashlib.sha256(raw).hexdigest()
    links = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line]
    roster = {r['cid'] for r in links}
    existing = {r['cid'] for r in links if any(g['group'] == 'bond' and g['records'] for g in r['groups'])}
    result['bond'] = {'merged_charainfo': len(chars), 'roster': len(roster), 'current_bond_cards': len(existing)}
    for scope, ids in [('all_charainfo', set(chars)), ('current_roster', roster)]:
        nonzero = {cid for cid in ids if chars.get(cid, ('', {}))[1].get('sup1')}
        apk_join = {cid for cid in nonzero if chars[cid][1]['sup1'] in support['APK']}
        joined = {cid for cid in nonzero if any(chars[cid][1]['sup1'] in s for s in support.values())}
        result['bond'][scope] = dict(sup1_nonzero=len(nonzero), apk_only_lookup=len(apk_join),
            layered_lookup=len(joined), added_vs_existing=len(joined-existing), lost_vs_existing=sorted(existing-joined),
            unresolved=sorted(nonzero-joined), sup2_nonzero=sum(bool(chars.get(cid, ('', {}))[1].get('sup2')) for cid in ids))
    result['bond']['sup2_values_roster'] = dict(Counter(str(chars.get(cid, ('', {}))[1].get('sup2', '<missing>')) for cid in roster))
    result['bond']['sup1_differs_cid_roster'] = [[cid, chars[cid][1]['sup1']] for cid in sorted(roster) if chars.get(cid, ('', {}))[1].get('sup1') and chars[cid][1]['sup1'] != cid]
    result['bond']['samples'] = {cid: {'charainfo_layer': chars[cid][0], 'charainfo_fields': {k: chars[cid][1].get(k) for k in ('sup1', 'sup2', 'sup_cost')}, 'support': {layer: tab.get(chars[cid][1].get('sup1')) for layer, tab in support.items()}} for cid in (10001, 351, 201, 30236)}
    layered_support = {**support['APK'], **support['CACHE']}
    sup2_ids = {chars[cid][1]['sup2'] for cid in roster if chars.get(cid, ('', {}))[1].get('sup2')}
    result['bond']['sup2_lookup'] = {'unique_ids': len(sup2_ids), 'matched_ids': len(sup2_ids & layered_support.keys()),
        'records': [layered_support[i] for i in sorted(sup2_ids) if i in layered_support]}
    result['bond']['abi2_abi3_current_cards'] = [cid for cid in sorted(existing) if any(support['CACHE'][cid].get(k) for k in ('abi2', 'abi3'))]

    skill = {'CACHE': read(CACHE / 'skilllist.data5.json.raw')['skilllist'], 'APK': read(APK / '_mdSkill.json')['skilllist']}
    boss = {'CACHE': read(CACHE / 'bossinfo.data5.json.raw')['bossinfo']['bossskill'], 'APK': read(APK / '_mdBossInfo.json')['bossskill']}
    skill_keys = {layer: {r['skillid'] for r in rows} for layer, rows in skill.items()}
    result['bond']['abi2_abi3_sample30236'] = {k: {'id': layered_support[30236].get(k), 'found_layers': [layer for layer, ids in skill_keys.items() if layered_support[30236].get(k) in ids]} for k in ('abi2', 'abi3')}
    result['type58'] = {}
    result['type3000'] = {}
    result['equal_values'] = {}
    for layer in ('CACHE', 'APK'):
        r58 = [r for r in skill[layer] if r.get('ability') == 58]
        result['type58'][layer] = {'records': len(r58), 'p4_dist': dict(Counter(str(r.get('param4', '<missing>')) for r in r58)),
                                  'samples': [r for r in r58 if r['skillid'] in (65000005, 40839903, 42010505, 42030608, 40035108)]}
        r3000 = [r for r in skill[layer] if r.get('ability') == 3000]
        filtered = [r for r in r3000 if len(r.get('text') or '') > 25 and 'サブアビリティ' not in (r.get('text') or '')]
        result['type3000'][layer] = {scope: {'n': len(rows), 'correlation': {slot: correlate(rows, kw, slot) for kw, slot in [('移動速度', 'param3'), ('防御力', 'param4'), ('回復', 'param5'), ('クリティカル', 'param7'), ('クリティカル威力', 'param8')]}} for scope, rows in [('all', r3000), ('meaningful_text', filtered)]}
        result['equal_values'][layer] = {}
        for name, rows, a, b in [('type13_p2_p6', [r for r in boss[layer] if r.get('skillid0') == 13], 'skillparam2', 'skillparam6'),
                                  ('type2012_p4_p5', [r for r in skill[layer] if r.get('ability') == 2012], 'param4', 'param5')]:
            present = [r for r in rows if a in r and b in r and r[a] is not None and r[b] is not None]
            result['equal_values'][layer][name] = {'total': len(rows), 'both_present': len(present), 'equal': sum(r[a] == r[b] for r in present)}
    report = read_path(ROOT / 'work/refcheck_20261023_lead/params/REPORT.md', root=ROOT).read_text(encoding='utf-8-sig')
    section = report.split('### 6.4', 1)[1].split('\n---', 1)[0]
    report_rows = re.findall(r'^\| (skilllist|bossskill) \| (\d+) \| (param\d+) \|', section, re.M)
    tree = ast.parse((ROOT / 'scripts/refcheck_20261023_lead/params_ours_sitecheck.py').read_text(encoding='utf-8-sig'))
    selected = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'OURS' for t in n.targets))
    result['lead_slot_counts'] = dict(report_rows=len(report_rows), unique_report_keys=len(set(report_rows)),
        script_selected=len(selected), script_found=sum((t, ty, slot) in tables['first'] for t, ty, slot, _ in selected))
    result['inputs_sha256'] = inputs
    OUT = fresh_output("projects/reference-analysis/reports", "lead-reconcile")
    (OUT / 'evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'deltas': {k: {f: v[f] for f in ('added', 'semantic_changed')} for k, v in result['deltas'].items()},
                      'lead_slot_counts': result['lead_slot_counts'], 'bond': result['bond']['current_roster'],
                      'bond_abi2_abi3_current_cards': len(result['bond']['abi2_abi3_current_cards']),
                      'sup2_unique_ids': len(sup2_ids), 'sup2_matched_ids': len(sup2_ids & layered_support.keys()),
                      'equal_values': result['equal_values']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
