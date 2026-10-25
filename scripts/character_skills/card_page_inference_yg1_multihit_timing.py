"""110/105 configuration, consumed only after a separately reviewed p1 binding."""
from copy import deepcopy
import math
import struct

SCOPE = 'YG1_BATCH3_MULTIHIT_FORMULA_ONLY'
REPORT = 'output/character_skills/yg1_batch3_20261024/独立报告/REVIEW_SOURCE.md'


def config(field, raw):
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    try:
        value = struct.unpack('>f', struct.pack('>f', float(raw)))[0]
    except (OverflowError, ValueError, struct.error):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    if field == 'skillparam5':
        return dict(value=f'连击调度重置值 {value:.9g} 游戏秒',
                    quantity_kind='连击调度重置值', unit='游戏秒（逐帧更新）',
                    effective_float32=value)
    if field == 'skillparam6' and 1 <= math.trunc(value) <= 2147483647:
        return dict(value=f'每目标最多 {math.trunc(value)} 次尝试（配置上限）',
                    quantity_kind='每目标尝试预算', unit='次/目标（配置上限）',
                    effective_float32=value, effective_int=math.trunc(value))
    return None


def apply_to_groups(data, cid, groups):
    if 'Y.G.' not in str((data.profiles.get(cid) or {}).get('title') or ''):
        return
    linked = next((g for g in data.links[cid]['groups'] if g['group'] == 'special_move'), {})
    for group in groups:
        if group.get('group') != 'special_move':
            continue
        for skill in group.get('skills', []):
            for row in skill.get('rows', []):
                if not row.get('inference_yg1_multihit'):
                    continue
                seen = {(a.get('binding', {}).get('pattern_id'), a.get('binding', {}).get('slot'),
                         a.get('record_id'), a.get('field_path')) for a in row.get('answers', [])}
                states = []
                for formula in list(row.get('answers', [])):
                    binding = formula.get('binding') or {}
                    typ = binding.get('type')
                    if (binding.get('scope') != SCOPE or typ not in (105, 110)
                            or formula.get('rule_key') != f'bossskill|{typ}|/skillparam1'):
                        continue
                    parents = [p for p in linked.get('records', [])
                               if p.get('table') == 'bosspattern' and p.get('layer') == 'CACHE'
                               and p.get('reference_id') == binding.get('pattern_id')]
                    if len(parents) != 1:
                        continue
                    parent = parents[0]
                    slot = binding.get('slot')
                    children = [c for c in parent.get('boss_skill_refs', [])
                                if c.get('table') == 'bossskill' and c.get('layer') == 'CACHE'
                                and c.get('reference_id') == formula.get('record_id')
                                and c.get('reference_field') == f"bosspattern[{binding['pattern_id']}].{slot}"
                                and parent['record'].get(slot) == c.get('reference_id')]
                    if len(children) != 1 or children[0]['record'].get('skillid0') != typ:
                        continue
                    child = children[0]
                    exact = data.precise_source(child)
                    if exact.get('source_resolution') != 'RESOLVED_EXACT_DECODED_RECORD':
                        continue
                    record = child['record']
                    for field in ('skillparam5', 'skillparam6'):
                        key = (binding['pattern_id'], slot, formula['record_id'], '/' + field)
                        raw = record.get(field)
                        result = config(field, raw)
                        states.append(dict(pattern_id=binding['pattern_id'], slot=slot,
                                           child_id=formula['record_id'], field=field,
                                           present=field in record, raw_value=raw,
                                           status='CONFIRMED_CONFIG' if result else 'OUTSIDE_CONFIRMED_DOMAIN'))
                        if key in seen or result is None:
                            continue
                        item = deepcopy(formula)
                        item.pop('effect_binding', None)
                        item.update(value=f"pattern {binding['pattern_id']} / {slot}：" + result['value'],
                                    quantity_kind=result['quantity_kind'], unit=result['unit'],
                                    raw_value=raw, rule_key=f'bossskill|{typ}|/' + field,
                                    field_path='/' + field,
                                    source={**exact, 'table':'bossskill', 'record_id':formula['record_id'],
                                            'field':'/' + field, 'field_path':'/' + field},
                                    answer_status='CONFIRMED_NUMERIC', target='连击调度配置',
                                    numeric_source='已有原生局部计时/计数读取链＋源记录',
                                    evidence=[REPORT], config_effective=deepcopy(result),
                                    note='float32参数。每次update每目标至多一次尝试；不是保证命中间隔、命中次数或总时长。'
                                         + ('105计数先递增再判范围，范围外仍消耗预算。' if typ == 105
                                            else '110在建立目标清单后不再做范围重判。')
                                         + '完整父条件见binding.conditions_raw；运行时选档仍未验证。')
                        row['answers'].append(item)
                        seen.add(key)
                if states:
                    row['yg1_multihit_config'] = states
