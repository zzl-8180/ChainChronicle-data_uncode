# -*- coding: utf-8 -*-
"""C20 两批候选的真实 Inputs／analyze_row 独立机器检查。

由 P1/P2 候选目录中的 check_candidate.py 调用。期望值只存在于本检查脚本，生产模块
不保存预筛 raw 或记录 ID。这里直接重读 CACHE/APK JSON，不复用生产 RawView 来验证来源。
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import json
import math
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/character_skills'))
_SCRIPTS = ROOT / 'scripts'
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from project_layout_paths import read_path, write_path

import card_page_data as D
import effect_ledger as L
import rules as R
import card_page_inference_c20_direct_damage_common as C20

CD_SHA = 'c1334ca6b621fe282d69a3c6793e356ee06f768fec08db7133e97e0fbc50d252'
RULES_SHA = 'cf9451c6ff47fcfb2707a845a799839b352acc10180c1ebc559f852a93affe67'
EXPECTED = {}


def expect(row, pattern, record, raw):
    EXPECTED[(row, pattern, record)] = raw


# P1 回归值；仅用于检查后计算，不进入生产模块。
expect('7250-special_move-special_move-pattern0-lvorder0-f1', 40725000, 40725002, 1)
expect('7250-special_move-special_move-pattern0-lvorder0-f2', 40725000, 40725003, 15)
expect('30105-special_move-special_move-pattern0-lvorder0-f2', 43010500, 43010501, 8)
expect('30107-special_move-special_move-pattern0-lvorder0-f3', 43010700, 43010702, 4)
expect('30220-special_move-special_move-pattern0-lvorder0-f1', 43022000, 43022001, 12.5)
expect('30223-special_move-special_move-pattern0-lvorder0-f3', 43022300, 43022302, 15)
expect('30225-special_move-special_move-pattern0-lvorder0-f1', 43022500, 43022502, 5)
expect('30301-special_move-special_move-pattern0-lvorder0-f1', 43030100, 43030102, 8)
expect('30329-special_move-special_move-pattern0-lvorder0-f1', 43032900, 43032901, 5)
expect('30334-special_move-special_move-pattern0-lvorder0-f2', 43033400, 43033402, 4)
# P2 回归值。
for pattern, record, raw in ((42033200, 42033200, 20.0), (42033201, 42033201, 19.0),
                             (42033202, 42033202, 18.0), (42033203, 42033203, 17.0)):
    expect('20332-special_move-special_move-pattern0-lvorder0-f0', pattern, record, raw)
expect('12236-special_move-special_move-pattern1-lvorder1-f0', 41223600, 41223600, 1.25)
expect('12236-special_move-special_move-pattern1-lvorder1-f0', 41223601, 41223602, 1.5)
expect('12236-special_move-special_move-pattern3-lvorder3-f0', 41223605, 41223605, 2)
expect('5300-special_move-special_move-pattern1-lvorder1-f0', 40530001, 40530000, 1.75)
expect('7654-special_move-special_move-pattern0-lvorder0-f0', 30765400, 30765400, 4.5)
expect('7654-special_move-special_move-pattern0-lvorder0-f0', 30765401, 30765401, 6.0)
expect('12032-special_move-special_move-pattern0-lvorder0-f0', 31203200, 31203200, 4.5)
expect('12226-special_move-special_move-pattern0-lvorder0-f0', 31222600, 31222600, 0.75)
expect('12226-special_move-special_move-pattern0-lvorder0-f0', 31222601, 31222601,
       1.100000023841858)
expect('20619-special_move-special_move-pattern0-lvorder0-f0', 42061900, 42061900, 35)
expect('20619-special_move-special_move-pattern0-lvorder0-f0', 42061901, 42061902, 37.5)

EXPECTED_SELECTED = {
    '20332-special_move-special_move-pattern0-lvorder0-f0': [42033200, 42033201, 42033202, 42033203],
    '12236-special_move-special_move-pattern1-lvorder1-f0': [41223600, 41223601],
    '12236-special_move-special_move-pattern3-lvorder3-f0': [41223605],
    '5300-special_move-special_move-pattern1-lvorder1-f0': [40530001],
    '7654-special_move-special_move-pattern0-lvorder0-f0': [30765400, 30765401],
    '12032-special_move-special_move-pattern0-lvorder0-f0': [31203200],
    '12226-special_move-special_move-pattern0-lvorder0-f0': [31222600, 31222601],
    '20619-special_move-special_move-pattern0-lvorder0-f0': [42061900, 42061901],
}
EXPECTED_CURRENT = {
    '20332-special_move-special_move-pattern0-lvorder0-f0': 42033200,
    '12236-special_move-special_move-pattern1-lvorder1-f0': 41223601,
    '12236-special_move-special_move-pattern3-lvorder3-f0': 41223605,
    '5300-special_move-special_move-pattern1-lvorder1-f0': 40530001,
    '7654-special_move-special_move-pattern0-lvorder0-f0': 30765400,
    '12032-special_move-special_move-pattern0-lvorder0-f0': 31203200,
    '12226-special_move-special_move-pattern0-lvorder0-f0': 31222600,
    '20619-special_move-special_move-pattern0-lvorder0-f0': 42061900,
}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(read_path(Path(path), root=ROOT).read_text(encoding='utf-8-sig'))


def watched_sha(path):
    # Keep source-code hashes on the candidate code root; resolve data reads only.
    logical = Path(path).relative_to(ROOT)
    return sha(path if logical.parts[0] == 'scripts' else read_path(path, root=ROOT))


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def record_hash(record):
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def rows_of(card_or_groups):
    groups = card_or_groups.get('groups') if isinstance(card_or_groups, dict) else card_or_groups
    return {row['row_id']: (skill, row) for group in groups or []
            for skill in group.get('skills') or [] for row in skill.get('rows') or []}


def main(M, out_dir):
    out_dir = write_path(Path(out_dir), root=ROOT).resolve()
    started = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    checks = []
    state = {}
    expected_answers = 10 if M.SCOPE == 'C20_P1_YG_DIRECT_DAMAGE_20261108' else 15
    expected_rows = len(M.TARGETS)
    expected_cids = len(M.TARGET_CIDS)
    target_cids = sorted(M.TARGET_CIDS)
    extra_cids = sorted(set(M.NEGATIVE_CIDS) | set(M.PROTECTED_CIDS) | {220})
    all_cids = sorted(set(target_cids) | set(extra_cids))

    def run(check_id, fn):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, {'error': '%s: %s' % (type(exc).__name__, exc),
                                 'traceback': traceback.format_exc()[-5000:]}
        checks.append({'check_id': check_id, 'ok': bool(ok), 'detail': detail})
        print(('PASS' if ok else 'FAIL'), check_id, '—',
              (json.dumps(detail, ensure_ascii=False, default=str)[:500]))
        return ok

    module_path = ROOT / 'scripts/character_skills' / (M.__name__ + '.py')
    common_path = ROOT / 'scripts/character_skills/card_page_inference_c20_direct_damage_common.py'
    cand_path, exc_path = out_dir / 'candidates.json', out_dir / 'exclusions.json'
    run_record_path = out_dir / 'run_record.json'
    shared_paths = [ROOT / 'scripts/character_skills/card_page_data.py',
                    ROOT / 'scripts/character_skills/effect_ledger.py',
                    ROOT / 'scripts/character_skills/rules.py',
                    ROOT / 'output/character_skills/profiles/rules.json',
                    ROOT / 'output/character_skills/effect_ledger/ledger.jsonl',
                    ROOT / 'output/character_skills/effect_ledger/backlog.json']
    shared_paths += [ROOT / 'output/character_skills/pages' / str(cid) / 'card.json'
                     for cid in all_cids]
    watch_before = {str(path.relative_to(ROOT)): watched_sha(path) for path in shared_paths}
    state['watch_before'] = watch_before

    def c01():
        keys = {'cid', 'row_id', 'effect_id', 'layer', 'reference_field', 'model'}
        bad = [t for t in M.TARGETS if set(t) != keys]
        ids = [t['effect_id'] for t in M.TARGETS]
        ok = (not bad and len(set(ids)) == len(ids) == expected_rows
              and all(t['effect_id'] == t['row_id'] + '#e00' for t in M.TARGETS)
              and not any(token in dump(M.TARGETS)
                          for token in ('raw_value', 'skillparam1', 'bossskill/')))
        return ok, {'targets': len(ids), 'unique_effects': len(set(ids)),
                    'identity_keys': sorted(keys), 'bad': bad}
    run('C01_frozen_identity_only', c01)

    def c02():
        c1, e1 = M.build_candidates(ROOT)
        c2, e2 = M.build_candidates(ROOT)
        rr = load(run_record_path)
        ok = (dump(c1) == dump(c2) and dump(e1) == dump(e2)
              and dump(c1) == dump(load(cand_path)) and dump(e1) == dump(load(exc_path))
              and c1['counts']['answers'] == expected_answers
              and c1['counts']['resolved_rows'] == expected_rows
              and c1['counts']['cids'] == expected_cids
              and rr['outputs']['candidates_sha256'] == sha(cand_path)
              and rr['outputs']['exclusions_sha256'] == sha(exc_path))
        state['candidate'] = c1
        state['exclusions'] = e1
        return ok, {'counts': c1['counts'], 'deterministic': dump(c1) == dump(c2),
                    'disk_matches': dump(c1) == dump(load(cand_path))}
    run('C02_candidate_determinism_and_counts', c02)

    def c03():
        candidate = state['candidate']
        rules = load(ROOT / 'output/character_skills/profiles/rules.json')
        ok = (sha(ROOT / 'scripts/character_skills/card_page_data.py') == CD_SHA
              and watched_sha(ROOT / 'output/character_skills/profiles/rules.json') == RULES_SHA
              and len(rules) == 294 and candidate['baseline']['campaign']
              == '99bee2a166e5ec5f9c03ac97b555d4ada2f6f30d1535258add16bc64c7227c66'
              and candidate['baseline']['snapshot'] == '99bee2a1-cf9451c6ff47fcfb')
        return ok, {'baseline': candidate['baseline'], 'rules': len(rules),
                    'card_page_data': CD_SHA[:16]}
    run('C03_baseline_versions_and_rules', c03)

    data = D.Inputs(ROOT, set(all_cids))
    built = {cid: D.build_card(data, cid) for cid in target_cids}
    extra_built = {cid: D.build_card(data, cid) for cid in extra_cids}
    baseline_groups = {cid: copy.deepcopy(built[cid]['groups']) for cid in target_cids}
    baseline_analysis = {}
    for cid in target_cids:
        for row_id, (_skill, row) in rows_of(built[cid]).items():
            if row_id in M.TARGET_ROW_IDS[cid]:
                baseline_analysis[row_id] = L.analyze_row(row, table='bosspattern')
    state.update(data=data, built=built, baseline_groups=baseline_groups,
                 baseline_analysis=baseline_analysis,
                 inputs_attrs=set(vars(data)), inputs_dir=set(dir(D.Inputs)))

    def c04():
        details, bad = [], []
        for target in M.TARGETS:
            row_id = target['row_id']
            analysis = baseline_analysis[row_id]
            effects = [e for e in analysis['effects']
                       if e.get('record_type') == 'effect'
                       and e.get('effect_id') == target['effect_id']]
            row = rows_of(built[target['cid']])[row_id][1]
            ok = (len(effects) == 1 and effects[0]['effect_type'] == 'ダメージ（词表外）'
                  and effects[0]['status'] == 'unresolved' and not row.get('inference_yg1'))
            if not ok:
                bad.append(row_id)
            details.append({'row_id': row_id, 'effect_status': effects[0]['status'] if effects else None,
                            'old_answers': len(row.get('answers') or [])})
        return not bad, {'targets': len(details), 'bad': bad, 'rows': details}
    run('C04_real_inputs_and_baseline_unresolved', c04)

    raw = {
        'CACHE': {
            'chara': load(ROOT / 'output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw')['charainfo'],
            'boss': load(ROOT / 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw')['bossinfo'],
        },
        'APK': {
            'chara': load(ROOT / 'output/base_master/_mdCharacter.json')['charainfo'],
            'boss': load(ROOT / 'output/base_master/_mdBossInfo.json'),
        },
    }
    raw_index = {}
    for layer, docs in raw.items():
        raw_index[layer] = {
            'chara': {},
            'pattern': {},
            'skill': {},
            'pattern_rows': docs['boss']['bosspattern'] if layer == 'CACHE' else docs['boss']['bosspattern'],
            'skill_rows': docs['boss']['bossskill'],
        }
        for i, rec in enumerate(docs['chara']):
            raw_index[layer]['chara'].setdefault(rec.get('cid'), []).append(i)
        for i, rec in enumerate(raw_index[layer]['pattern_rows']):
            raw_index[layer]['pattern'].setdefault(rec.get('patternid'), []).append(i)
        for i, rec in enumerate(raw_index[layer]['skill_rows']):
            raw_index[layer]['skill'].setdefault(rec.get('skillid'), []).append(i)
    state['raw_index'] = raw_index

    def c05():
        actual, failures = {}, []
        for item in state['candidate']['items']:
            for answer in item['answers']:
                layer = answer['layer']
                source = answer['source']
                idx = source['record_index']
                rec = raw_index[layer]['skill_rows'][idx]
                field = answer['field_path'].lstrip('/')
                pattern_id = answer['effect_binding']['pattern_id']
                key = (item['row_id'], pattern_id, answer['record_id'])
                actual[key] = answer['raw_value']
                checks_one = {
                    'record_id': rec.get('skillid') == answer['record_id'],
                    'raw': rec.get(field) == answer['raw_value'],
                    'pointer': source['json_pointer'] ==
                               (('/bossinfo/bossskill/' if layer == 'CACHE' else '/bossskill/') + str(idx)),
                    'field_pointer': source['field_json_pointer'] == source['json_pointer'] + '/' + field,
                    'raw_hash': source['raw_record_sha256'] == record_hash(rec),
                    'finite': isinstance(answer['raw_value'], (int, float))
                              and not isinstance(answer['raw_value'], bool)
                              and math.isfinite(answer['raw_value']) and answer['raw_value'] > 0,
                    'float32': answer['effective_float32'] == C20.f32(answer['raw_value']),
                }
                if not all(checks_one.values()):
                    failures.append({'key': key, 'failed': [k for k, v in checks_one.items() if not v]})
        scoped = {key: value for key, value in actual.items()
                  if key[0] in {t['row_id'] for t in M.TARGETS}}
        expected_scoped = {key: value for key, value in EXPECTED.items()
                           if key[0] in {t['row_id'] for t in M.TARGETS}}
        missing = set(expected_scoped) - set(scoped)
        unexpected = set(scoped) - set(expected_scoped)
        unequal = [key for key in set(scoped) & set(expected_scoped)
                   if scoped[key] != expected_scoped[key]]
        ok = not failures and scoped == expected_scoped and len(actual) == expected_answers
        return ok, {'answers': len(actual), 'failures': failures,
                    'missing': sorted(missing), 'unexpected': sorted(unexpected), 'unequal': unequal}
    run('C05_independent_raw_source_and_expected_values', c05)

    def c06():
        failures = []
        for item in state['candidate']['items']:
            layer = item['layer']
            cid = item['cid']
            chits = raw_index[layer]['chara'].get(cid) or []
            if len(chits) != 1:
                failures.append({'row': item['row_id'], 'why': 'charainfo', 'hits': len(chits)})
                continue
            chara = raw[layer]['chara'][chits[0]]
            actual_parents = [(key, chara[key]) for key in sorted(
                [key for key in chara if key.startswith('pattern') and chara[key]],
                key=lambda key: int(key[7:]))]
            candidate_parents = [(p['reference_field'], p['pattern_id'])
                                 for p in item['complete_parent_set']]
            if actual_parents != candidate_parents:
                failures.append({'row': item['row_id'], 'why': 'complete_parent_set',
                                 'actual': actual_parents, 'candidate': candidate_parents})
            answers = item['answers']
            current = answers[0]['binding'][M.BLOCKING_KEY]['current_parent']['pattern_id']
            if chara.get(item['reference_field']) != current:
                failures.append({'row': item['row_id'], 'why': 'current_parent',
                                 'chara': chara.get(item['reference_field']), 'answer': current})
            if item['model'] != 'DIRECT':
                selected = [a['effect_binding']['pattern_id'] for a in answers]
                if selected != EXPECTED_SELECTED[item['row_id']] or current != EXPECTED_CURRENT[item['row_id']]:
                    failures.append({'row': item['row_id'], 'why': 'selected_or_current',
                                     'selected': selected, 'current': current})
            for answer in answers:
                selected = answer['binding'][M.BLOCKING_KEY]['selected']
                pidx = selected['pattern_index']
                prec = raw_index[layer]['pattern_rows'][pidx]
                if prec.get('patternid') != selected['pattern_id']:
                    failures.append({'row': item['row_id'], 'why': 'pattern_index'})
                if prec.get('skillid%d' % selected['child_slot']) != answer['record_id']:
                    failures.append({'row': item['row_id'], 'why': 'child_link'})
        return not failures, {'rows': len(state['candidate']['items']), 'failures': failures}
    run('C06_complete_parent_sets_and_child_links', c06)

    def c07():
        failures = []
        for item in state['candidate']['items']:
            for answer in item['answers']:
                rec = raw_index[answer['layer']]['skill_rows'][answer['source']['record_index']]
                rule = R.answer_for('bossskill', answer['binding']['g1_b1_binding'].get('type', rec['skillid0']),
                                    answer['field_path'], answer['raw_value'], rec,
                                    source_layer=answer['layer'])
                nested = answer['binding'][M.BLOCKING_KEY]
                eb = answer['effect_binding']
                expected_span = item['baseline_effect']['span']
                checks_one = {
                    'numeric': answer['numeric_evidence'] == '确认',
                    'association': answer['association_evidence'] == '推断',
                    'status': answer['answer_status'] == (rule.get('answer_status')
                                                             or rule.get('rule_status')
                                                             or 'CONFIRMED_FORMULA_ONLY'),
                    'scope': answer['evidence_scope'] == M.SCOPE,
                    'inferred': nested['binding'] == 'inferred' and nested['runtime_verified'] is False,
                    'g1': answer['binding']['g1_b1_binding']['scope'] == 'G1_B1_MIRROR_20261029',
                    'effect_span': eb['span'] == expected_span,
                    'effect_type': eb['effect_type'] == 'ダメージ（词表外）',
                    'pattern_binding': answer['binding']['pattern_id'] == eb['pattern_id'],
                    'rule_value': bool(rule) and answer['value'].startswith(rule['value_text']),
                    'not_included': bool(answer['not_included']),
                    'no_page_sha': 'page_sha256' not in answer,
                }
                if not all(checks_one.values()):
                    failures.append({'row': item['row_id'], 'record': answer['record_id'],
                                     'failed': [k for k, v in checks_one.items() if not v]})
        return not failures, {'answers': expected_answers, 'failures': failures}
    run('C07_rule_recompute_evidence_and_effect_bindings', c07)

    first_reports = {}
    for cid in target_cids:
        first_reports[cid] = M.apply_to_groups(data, cid, built[cid]['groups'], scope=M.SCOPE)
    state['first_reports'] = first_reports

    def c08():
        total = sum(rep['added'] for rep in first_reports.values())
        bad = {cid: rep for cid, rep in first_reports.items()
               if rep['conflicts'] or rep['rejected'] or rep['status'] != 'APPLIED'}
        return total == expected_answers and not bad, {
            'added': total, 'expected': expected_answers, 'bad': bad,
            'per_cid': {cid: rep['added'] for cid, rep in first_reports.items()}}
    run('C08_first_apply_expected_additions', c08)

    def c09():
        failures, remaining = [], 0
        for target in M.TARGETS:
            row = rows_of(built[target['cid']])[target['row_id']][1]
            old_row = rows_of(baseline_groups[target['cid']])[target['row_id']][1]
            before = baseline_analysis[target['row_id']]
            after = L.analyze_row(row, table='bosspattern')
            effect = next(e for e in after['effects'] if e.get('effect_id') == target['effect_id'])
            old_count = len(old_row.get('answers') or [])
            new_refs = [ref for ref in after['answer_refs'] if ref['answer_index'] >= old_count]
            expected_row_answers = len(next(item for item in state['candidate']['items']
                                            if item['row_id'] == target['row_id'])['answers'])
            old_unmatched = sum(ref['matched_effect_id'] is None for ref in before['answer_refs'])
            new_unmatched = sum(ref['matched_effect_id'] is None for ref in new_refs)
            checks_one = {
                'effect_has_answer': effect['status'] == 'has_answer',
                'effect_ref_count': len(effect['answer_refs']) == expected_row_answers,
                'new_ref_count': len(new_refs) == expected_row_answers,
                'new_unmatched': new_unmatched == 0,
                'new_refs_to_target': all(ref['matched_effect_id'] == target['effect_id'] for ref in new_refs),
                'old_unmatched_unchanged': sum(ref['matched_effect_id'] is None
                                               for ref in after['answer_refs']) == old_unmatched,
                'split_unchanged': dump(after['split_flags']) == dump(before['split_flags']),
            }
            remaining += sum(e.get('status') == 'unresolved' for e in after['effects']
                             if e.get('record_type') == 'effect')
            if not all(checks_one.values()):
                failures.append({'row': target['row_id'],
                                 'failed': [k for k, v in checks_one.items() if not v]})
        return not failures, {'effects': expected_rows, 'answers': expected_answers,
                              'remaining_unresolved_effects': remaining, 'failures': failures}
    run('C09_ledger_consumption_no_new_unmatched_or_split', c09)

    snapshots = {cid: dump(built[cid]['groups']) for cid in target_cids}
    second_reports = {cid: M.apply_to_groups(data, cid, built[cid]['groups'], scope=M.SCOPE)
                      for cid in target_cids}
    state['second_reports'] = second_reports

    def c10():
        added = sum(rep['added'] for rep in second_reports.values())
        skipped = sum(rep['skipped'] for rep in second_reports.values())
        changed = [cid for cid in target_cids if dump(built[cid]['groups']) != snapshots[cid]]
        return added == 0 and skipped == expected_answers and not changed, {
            'added': added, 'skipped': skipped, 'changed': changed}
    run('C10_second_apply_zero_and_byte_identical', c10)

    def c11():
        target = M.TARGETS[0]
        row = rows_of(built[target['cid']])[target['row_id']][1]
        before = dump(row)
        attempts = []

        def reject(label, fn):
            try:
                fn()
            except M.ScopeError as exc:
                attempts.append({'call': label, 'ok': True, 'error': str(exc)})
                return True
            attempts.append({'call': label, 'ok': False})
            return False
        ok = True
        ok &= reject('evaluate_default', lambda: M.evaluate(data, target['cid'], row))
        ok &= reject('evaluate_wrong', lambda: M.evaluate(data, target['cid'], row, scope='WRONG'))
        ok &= reject('evaluate_empty', lambda: M.evaluate(data, target['cid'], row, scope=''))
        ok &= reject('apply_default', lambda: M.apply_to_groups(data, target['cid'], built[target['cid']]['groups']))
        ok &= reject('apply_wrong', lambda: M.apply_to_groups(data, target['cid'], built[target['cid']]['groups'], scope='WRONG'))
        ok &= reject('apply_empty', lambda: M.apply_to_groups(data, target['cid'], built[target['cid']]['groups'], scope=''))
        return ok and dump(row) == before, {'attempts': attempts, 'row_unchanged': dump(row) == before}
    run('C11_scope_hard_reject', c11)

    def c12():
        target = M.TARGETS[0]
        alternatives = [(skill, row) for cid in target_cids for skill, row in rows_of(built[cid]).values()
                        if row.get('group') == 'special_move'
                        and row['row_id'] not in {t['row_id'] for t in M.TARGETS}]
        if not alternatives:
            return False, {'why': 'no non-target special_move row'}
        skill, row = alternatives[0]
        result = M.evaluate(data, row['cid'], row, scope=M.SCOPE, skill=skill)
        return result['status'] == 'REJECTED' and result['reason'] == 'ROW_NOT_IN_FROZEN_SCOPE' \
               and not result['answers'], {'row_id': row['row_id'], 'result': result}
    run('C12_nonfrozen_row_rejected', c12)

    def c13():
        details, ok = [], True
        for cid in extra_cids:
            card = extra_built[cid]
            before = dump(card['groups'])
            rep = M.apply_to_groups(data, cid, card['groups'], scope=M.SCOPE)
            row_ok = rep['status'] == 'OUT_OF_SCOPE' and rep['added'] == 0 and dump(card['groups']) == before
            ok &= row_ok
            details.append({'cid': cid, 'status': rep['status'], 'added': rep['added'], 'ok': row_ok})
        return ok, {'cards': details}
    run('C13_negative_protected_and_other_cards_zero', c13)

    def c14():
        failures = []
        target_rows = {t['row_id'] for t in M.TARGETS}
        for cid in target_cids:
            before_rows = rows_of(baseline_groups[cid])
            after_rows = rows_of(built[cid]['groups'])
            for row_id, (_skill, old_row) in before_rows.items():
                new_row = after_rows[row_id][1]
                old_answers = old_row.get('answers') or []
                new_answers = new_row.get('answers') or []
                if new_answers[:len(old_answers)] != old_answers:
                    failures.append({'row': row_id, 'why': 'old_answer_prefix'})
                if row_id not in target_rows and dump(new_row) != dump(old_row):
                    failures.append({'row': row_id, 'why': 'non_target_row_changed'})
        return not failures, {'failures': failures}
    run('C14_old_answers_prefix_and_non_target_rows', c14)

    def c15():
        failures = []
        for item in state['candidate']['items']:
            row = rows_of(built[item['cid']])[item['row_id']][1]
            marker = row.get('inference_yg1') or {}
            answers = [a for a in row['answers'] if (a.get('binding') or {}).get(M.BLOCKING_KEY)]
            pids = [a['effect_binding']['pattern_id'] for a in answers]
            groups = {a['effect_binding']['variant_group'] for a in answers}
            checks_one = {
                'scope': marker.get('scope') == M.SCOPE,
                'pattern_ids': marker.get('pattern_ids') == list(dict.fromkeys(pids)),
                'variant_group': len(groups) == 1,
                'effect_span': all(a['effect_binding']['span'] == item['baseline_effect']['span'] for a in answers),
                'source_identity': all(a['source']['table'] == 'bossskill'
                                       and a['source']['record_id'] == a['record_id']
                                       and a['source']['layer'] == a['layer']
                                       and a['source']['field_path'] == a['field_path'] for a in answers),
            }
            if not all(checks_one.values()):
                failures.append({'row': item['row_id'],
                                 'failed': [k for k, v in checks_one.items() if not v]})
        return not failures, {'rows': expected_rows, 'failures': failures}
    run('C15_variant_marker_identity_and_source', c15)

    def c16():
        target = M.TARGETS[0]
        skill, original = rows_of(baseline_groups[target['cid']])[target['row_id']]
        row = copy.deepcopy(original)
        row['source'] = dict(row.get('source') or {})
        row['source']['json_pointer'] = '/invalid/0'
        result = M.evaluate(data, target['cid'], row, scope=M.SCOPE, skill=skill)
        return result['status'] == 'REJECTED' and result['reason'] == 'ROW_SOURCE_POINTER_MISMATCH', result
    run('C16_source_pointer_tamper_rejected', c16)

    def c17():
        target = M.TARGETS[0]
        cid = target['cid']
        groups = copy.deepcopy(baseline_groups[cid])
        answer = next(item for item in state['candidate']['items']
                      if item['row_id'] == target['row_id'])['answers'][0]
        row = rows_of(groups)[target['row_id']][1]
        row.setdefault('answers', []).append({'rule_key': answer['rule_key'], 'raw_value': -999,
                                              'record_id': -1, 'field_path': answer['field_path']})
        before = dump(row)
        rep = M.apply_to_groups(data, cid, groups, scope=M.SCOPE)
        same_rule_atomic = (dump(rows_of(groups)[target['row_id']][1]) == before
                            and all(entry['added'] == 0 for entry in rep['rows']
                                    if entry['row_id'] == target['row_id']))
        groups2 = copy.deepcopy(baseline_groups[cid])
        row2 = rows_of(groups2)[target['row_id']][1]
        row2['inference_yg1'] = {'scope': 'OTHER_SCOPE'}
        before2 = dump(row2)
        rep2 = M.apply_to_groups(data, cid, groups2, scope=M.SCOPE)
        scope_atomic = (dump(rows_of(groups2)[target['row_id']][1]) == before2
                        and all(entry['added'] == 0 for entry in rep2['rows']
                                if entry['row_id'] == target['row_id']))
        return same_rule_atomic and scope_atomic and rep['conflicts'] > 0 and rep2['conflicts'] > 0, {
            'same_rule': {'card_added': rep['added'], 'conflicts': rep['conflicts'], 'target_row_atomic': same_rule_atomic},
            'scope': {'card_added': rep2['added'], 'conflicts': rep2['conflicts'], 'target_row_atomic': scope_atomic},
            'note': '原子性按目标行验收；同卡其它独立目标行允许正常新增'}
    run('C17_existing_answer_and_scope_conflicts_atomic', c17)

    def c18():
        view = C20.RawView(ROOT)
        target = M.TARGETS[0]
        skill, row = next((skill, row) for skill, row in rows_of(view.card(target['cid'])).values()
                           if row['row_id'] == target['row_id'])
        good = M.evaluate(view, target['cid'], row, scope=M.SCOPE, skill=skill)
        source = good['answers'][0]['source']
        record = view.layers[source['layer']]['skill_docs'][source['record_index']]
        field = good['answers'][0]['field_path'].lstrip('/')
        old = record[field]
        record[field] = 0
        bad = M.evaluate(view, target['cid'], row, scope=M.SCOPE, skill=skill)
        record[field] = old
        restored = M.evaluate(view, target['cid'], row, scope=M.SCOPE, skill=skill)
        return (bad['status'] == 'REJECTED' and 'RAW_NOT_FINITE_POSITIVE' in dump(bad)
                and restored['status'] == 'RESOLVED'), {
            'good': good['status'], 'mutated': bad, 'restored': restored['status']}
    run('C18_raw_zero_rejected_and_restored', c18)

    def c19():
        texts = [module_path.read_text(encoding='utf-8'), common_path.read_text(encoding='utf-8')]
        joined = '\n'.join(texts)
        banned = ['scripts/skill_reader_preview', 'work/c20_web_absorption_assessment',
                  'import card_page_data']
        hits = [token for token in banned if token in joined]
        return not hits and set(vars(data)) == state['inputs_attrs'] \
               and set(dir(D.Inputs)) == state['inputs_dir'], {
            'banned_hits': hits, 'inputs_attrs_unchanged': set(vars(data)) == state['inputs_attrs'],
            'inputs_class_unchanged': set(dir(D.Inputs)) == state['inputs_dir']}
    run('C19_production_dependencies_and_inputs_not_mutated', c19)

    def c20():
        failures = []
        banned = ('skillparam', 'bossskill', '/bossinfo', 'floor/', 'param6', 'priority=', 'bosspattern')
        for item in state['candidate']['items']:
            for answer in item['answers']:
                text = answer['player_text']
                failed = [token for token in banned if token in text]
                if failed or '条件：' not in text or '未验证' not in text \
                        or not answer['player_scope']['conditions'] or not answer['player_scope']['unknowns']:
                    failures.append({'row': item['row_id'], 'record': answer['record_id'],
                                     'tokens': failed, 'text': text})
                if item['cid'] == 20332 and '自身受伤' not in text:
                    failures.append({'row': item['row_id'], 'why': 'self_damage_boundary_missing'})
                label = answer['condition_label']
                if item['cid'] == 20332 and (
                        '0thChain（通常）与1stChain以上（含MaxChain）' not in label
                        or '2ndChain以上' in label or '通常／1stChain' in label):
                    failures.append({'row': item['row_id'], 'why': 'CHAIN_LABEL_MISMATCH',
                                     'condition': label})
                if item['row_id'] == '12236-special_move-special_move-pattern1-lvorder1-f0' \
                        and answer['record_id'] == 41223602 \
                        and ('强化1次档' not in label or '回到基础分支' in label):
                    failures.append({'row': item['row_id'], 'why': 'USE_ONCE_NOT_STRENGTHENED',
                                     'condition': label})
                if item['cid'] == 5300 and ('常规基础分支' not in label or '亦使用这一来源' not in label):
                    failures.append({'row': item['row_id'], 'why': 'TERRAIN_CONDITION_NOT_SPLIT'})
                if item['row_id'] == '7250-special_move-special_move-pattern0-lvorder0-f1' \
                        and answer['answer_status'] != 'CONFIRMED_NUMERIC':
                    failures.append({'row': item['row_id'], 'why': 'TYPE105_STATUS',
                                     'got': answer['answer_status']})
                if item['model'] == 'DIRECT':
                    selected = answer['binding'][M.BLOCKING_KEY]['selected']
                    prec = raw_index[item['layer']]['pattern_rows'][selected['pattern_index']]
                    chs, che = prec.get('chs', 0) or 0, prec.get('che', 0) or 0
                    expected_scope = {
                        (0, 0): '当前基础档（未设置Chain区间条件）',
                        (0, 1): '0thChain（通常）当前档',
                        (0, 2): '0th／1stChain当前档',
                        (2, 5): '1stChain以上（含MaxChain）当前档',
                    }.get((chs, che), 'Chain计数%d–%d当前档' % (chs, che))
                    if expected_scope not in label:
                        failures.append({'row': item['row_id'], 'why': 'DIRECT_CHAIN_SCOPE',
                                         'chs': chs, 'che': che, 'want': expected_scope,
                                         'got': label})
                if item['row_id'] == '20619-special_move-special_move-pattern0-lvorder0-f0' \
                        and answer['record_id'] == 42061900:
                    excluded = answer['binding'][M.BLOCKING_KEY]['excluded_branch_values']
                    if not any(x['selection']['pattern_id'] == 42061902 for x in excluded):
                        failures.append({'row': item['row_id'], 'why': 'SUPER_PARENT_NOT_DISCLOSED'})
        return not failures, {'answers': expected_answers, 'failures': failures}
    run('C20_player_text_conditions_and_boundaries', c20)

    def c21():
        after = {str(path.relative_to(ROOT)): watched_sha(path) for path in shared_paths}
        changed = [key for path, key in ((path, str(path.relative_to(ROOT))) for path in shared_paths)
                   if after[key] != watch_before[key]]
        return not changed, {'watched': len(after), 'changed': changed}
    run('C21_shared_files_and_pages_unmodified', c21)

    def c22():
        candidate = state['candidate']
        item_answers = [answer for item in candidate['items'] for answer in item['answers']]
        pids = [(answer['effect_binding']['row_id'], answer['effect_binding']['pattern_id'],
                 answer['record_id']) for answer in item_answers]
        ok = (len(item_answers) == expected_answers and len(candidate['items']) == expected_rows
              and len({item['cid'] for item in candidate['items']}) == expected_cids
              and len(pids) == expected_answers
              and all(t['row_id'] in baseline_analysis for t in M.TARGETS)
              and all(c['ok'] for c in checks))
        return ok, {'rows': expected_rows, 'cids': expected_cids, 'answers': len(item_answers),
                    'checks_before_final': len(checks)}
    run('C22_final_accounting', c22)

    passed = sum(c['ok'] for c in checks)
    result = {
        'schema': 'c20-candidate-check-result-1', 'scope': M.SCOPE,
        'module': M.MODULE_VERSION, 'module_sha256': sha(module_path),
        'common_module_sha256': sha(common_path),
        'card_page_data_sha256': sha(ROOT / 'scripts/character_skills/card_page_data.py'),
        'baseline': state['candidate']['baseline'],
        'candidates_sha256': sha(cand_path), 'exclusions_sha256': sha(exc_path),
        'check_summary': {'total': len(checks), 'passed': passed,
                          'failed': len(checks) - passed, 'all_passed': passed == len(checks)},
        'checks': checks,
        'started_at_utc': started,
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        'command': './.venv/Scripts/python.exe -X utf8 -I -B %s/check_candidate.py'
                   % (out_dir.relative_to(ROOT).as_posix() if out_dir.is_relative_to(ROOT)
                      else out_dir.as_posix()),
        'limits': ['候选内存自检，不是独立语义审查；未运行正式全库生成、原生执行或实机。',
                   '固定16卡与命名反例，不称任意分组复现；正式pages/rules/ledger未写。'],
    }
    path = out_dir / 'check_result.json'
    path.write_bytes((json.dumps(result, ensure_ascii=False, indent=1, allow_nan=False) + '\n').encode('utf-8'))
    print('RESULT', path, json.dumps(result['check_summary'], ensure_ascii=False))
    return 0 if result['check_summary']['all_passed'] else 1
