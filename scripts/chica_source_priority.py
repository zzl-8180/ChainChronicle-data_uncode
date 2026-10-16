"""Apply the user's comparison policy after proven values have been generated.

This changes adoption decisions, never raw values or native verification states.
The policy is card/record/field scoped; screenshot equality and cause stay separate.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path('output/card_comparison_cid30236')
POLICY_PATH = ROOT/'difference_sources/adoption_policy.json'


def apply_source_priority(rules, views, effects, overview):
    policy = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    binding = dict(policy_id=policy['policy_id'], policy_path='difference_sources/adoption_policy.json',
                   policy_sha256=hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest(),
                   provenance=policy['provenance'], instruction_quote=policy['instruction_quote'],
                   discrepancy_status=policy['resolution_status'], screenshot_relation=policy['screenshot_relation'],
                   cause_status=policy['cause_status'], reason_zh=policy['reason_zh'])
    for row in rules+views+overview:
        row['screenshot_resolutions'] = []
    by_effect = {r['effect_id']: r for r in effects}
    for case in policy['cases']:
        adopted_fields = []
        matched_views = []
        matched_rules = []
        for field in case['fields']:
            found = [v for v in views if (v['table'], v['record_id'], v['effect_type'], v['field_path']) ==
                     (case['table'], case['record_id'], case['effect_type'], field['field_path'])]
            assert len(found) == 1, (case['case_id'], field['field_path'])
            view = found[0]
            assert view['raw_value'] == field['raw_value'] and view['converted_value'] == field['converted_value']
            matched_views.append(view)
            adopted_fields.append({k: copy.deepcopy(view[k]) for k in (
                'record_key', 'table', 'namespace', 'record_id', 'effect_type', 'field_path', 'raw_value',
                'converted_value', 'display_value', 'unit', 'conversion', 'conditions', 'raw_value_status',
                'correspondence_status', 'calculation_status', 'original_file', 'source_sha256', 'location', 'json_pointer')})
            found_rules = [r for r in rules if (r['table'], r['effect_type'], r['field_path']) ==
                           (case['table'], case['effect_type'], field['field_path'])]
            assert len(found_rules) == 1
            matched_rules.extend(found_rules)
        resolution = dict(binding, case_id=case['case_id'], effect_ids=case['effect_ids'],
                          adopted_display=case['adopted_display'], adopted_numeric_value=case['adopted_numeric_value'],
                          adopted_unit=case['adopted_unit'], screenshot_numeric_value=case['screenshot_numeric_value'],
                          screenshot_unit=case['screenshot_unit'], limits_zh=case['limits_zh'],
                          adopted_fields=adopted_fields, evidence=case['evidence'])
        if 'conditional_nominal_value' in case:
            resolution['conditional_nominal_value'] = case['conditional_nominal_value']
        for row in matched_views+matched_rules:
            # Rules may cover several IDs; adoption remains explicitly record scoped.
            row['screenshot_resolutions'].append(copy.deepcopy(resolution))
            row['evidence'] = list(dict.fromkeys(row['evidence']+case['evidence']+[binding['policy_path']]))
            row['limits'] += '；本卡截图取值已按用户优先级裁决，详见screenshot_resolutions；截图成因未知不再阻塞取值。'
        for key in case['effect_ids']:
            row = by_effect[key]
            assert row['screenshot_difference']['case_id'] == case['case_id']
            row['screenshot_difference'].update(copy.deepcopy(resolution))
            row['comparison_note'] = '已按解包/代码裁决：'+case['adopted_display']+'。截图数值不同，保留作外部参考。'
            row['remaining_gap'] = case['limits_zh']
            row['evidence'] += '；'+binding['policy_path']+'（用户指定取值优先级，非代码证明）'
            if case['case_id'] == 'barrier_guard':
                row['readable_value'] = case['adopted_display']
            elif case['case_id'] == 'enemy_duration':
                row['duration'] = '30游戏秒（采用解包/代码；截图45秒保留）'
            elif case['case_id'] == 'chain_mana':
                row['condition'] = '原文1stChain及以上；代码链列表数量≥2且未锁存时判定，显示计数映射另论'
        group = next(r for r in overview if r['title'] == case['overview_title'])
        group['screenshot_resolutions'].append(copy.deepcopy(resolution))
        group['conclusion'] += ' 本组截图取值已裁决：'+case['adopted_display']+'；按用户指示采用解包/代码，截图不同值及未知成因保留。'
        if group['status'] == 'diff':
            group.update(status='resolved', status_zh='截图数值已裁决 · 采用解包/代码')
    # Some proof builders share evidence lists; avoid repeated links in CSV/JSON.
    for row in rules+views:
        row['evidence'] = list(dict.fromkeys(row['evidence']))
    return policy
