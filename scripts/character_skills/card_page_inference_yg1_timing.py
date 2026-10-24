"""Boss55 scheduling configuration attached only to already bound YG1 formulas."""
from copy import deepcopy

from rules import laser_config

REPORT = 'output/character_skills/yg1_batch2_20261024/独立报告/REVIEW_SOURCE.md'


def apply_to_groups(data, cid, groups):
    if 'Y.G.' not in str((data.profiles.get(cid) or {}).get('title') or ''):
        return
    linked = next((g for g in data.links[cid]['groups'] if g['group'] == 'special_move'), {})
    for group in groups:
        if group.get('group') != 'special_move':
            continue
        for skill in group.get('skills', []):
            for row in skill.get('rows', []):
                if not row.get('inference_yg1') or row.get('yg1_schedule_config'):
                    continue
                states = []
                for answer in list(row.get('answers', [])):
                    if answer.get('rule_key') != 'bossskill|55|/skillparam1':
                        continue
                    binding = answer.get('binding') or {}
                    parents = [e for e in linked.get('records', [])
                               if e.get('table') == 'bosspattern' and e.get('layer') == 'CACHE'
                               and e.get('reference_id') == binding.get('pattern_id')]
                    if len(parents) != 1:
                        continue
                    parent = parents[0]
                    children = [c for c in parent.get('boss_skill_refs', [])
                                if c.get('table') == 'bossskill' and c.get('layer') == 'CACHE'
                                and c.get('reference_id') == answer.get('record_id')
                                and c.get('reference_field') ==
                                f"bosspattern[{binding['pattern_id']}].{binding.get('slot')}"
                                and parent['record'].get(binding.get('slot')) == c.get('reference_id')]
                    if len(children) != 1 or children[0]['record'].get('skillid0') != 55:
                        continue
                    child = children[0]
                    exact = data.precise_source(child)
                    if exact.get('source_resolution') != 'RESOLVED_EXACT_DECODED_RECORD':
                        continue
                    for field in ('skillparam6', 'skillparam0'):
                        record = child['record']
                        value = record.get(field)
                        result = laser_config('/'+field, value)
                        states.append(dict(pattern_id=binding['pattern_id'], field=field,
                            present=field in record, raw_value=value,
                            status='CONFIRMED_CONFIG' if result else 'OUTSIDE_CONFIRMED_DOMAIN'))
                        if result is None:
                            continue
                        item = deepcopy(answer)
                        item.pop('effect_binding', None)
                        item.update(value=answer['condition_label']+'：'+result['value_text'],
                            quantity_kind=result['quantity_kind'], unit=result['unit'],
                            raw_value=value, rule_key='bossskill|55|/'+field, field_path='/'+field,
                            source={**exact, 'table':'bossskill', 'record_id':answer['record_id'],
                                    'field_path':'/'+field},
                            answer_status='CONFIRMED_NUMERIC', target='激光段调度配置',
                            numeric_source='有界原生调度读取链＋源记录',
                            evidence=[REPORT],
                            note='仅调度配置；首段启用不等于立即命中。固定更新离散调度，每步至多新增一段。'
                                 '不是严格受伤间隔、保证命中次数或总时长；运行时选档仍未验证。'
                                 '条件原值='+repr(binding.get('conditions_raw')))
                        row['answers'].append(item)
                if states:
                    row['yg1_schedule_config'] = states
                    row['unknown_reasons'] = list(dict.fromkeys(row.get('unknown_reasons', []) + [
                        '正常正值的激光调度配置见附加答案；缺失或域外配置保留原值且不出数值答案。'
                        '严格受伤间隔/命中次数、其他机制及运行时选档仍待解释。']))
