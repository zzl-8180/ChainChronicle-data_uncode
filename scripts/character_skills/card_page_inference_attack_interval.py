"""YG cadence contributions: exact configuration paths, conservative text binding.

Field formulas are confirmed locally; installation and description association
remain inferred. Base atkspeed, damage ticks and actual animation cadence differ.
"""
import copy
import math
import re
import unicodedata

import rules as R
from card_page_attack_interval_grants import DefaultRecordStore, GrantResolver

SCOPE = 'ATTACK_INTERVAL_BATCH1_LOCAL_FORMULA_ONLY'
REPORT = 'output/character_skills/attack_interval_batch1_20261024/review/source_audit.md'
TYPE7_IDS = {43011009, 43023407, 43023607, 43025107, 43025707}
WORD = re.compile('攻撃速度|攻撃間隔')


def finite(v):
    return isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v)


def node(data, table, ident):
    if not hasattr(data, '_attack_interval_store'):
        data._attack_interval_store = DefaultRecordStore()
        data._attack_interval_nodes = {}
    key = (table, ident)
    if key not in data._attack_interval_nodes:
        found = data._attack_interval_store.lookup(table, ident)
        value = found.records[0] if not found.reason_codes and len(found.records) == 1 else None
        if value and value['source'].get('layer') != 'CACHE':
            value = None
        data._attack_interval_nodes[key] = value
    return data._attack_interval_nodes[key]


def ordinary_tree(data, ident, stack=()):
    if ident in stack:
        return None
    item = node(data, 'skilllist', ident)
    if item is None:
        return None
    out = [(item, list(stack) + [ident])]
    for child in item['raw'].get('sub') or []:
        if not isinstance(child, int) or isinstance(child, bool):
            return None
        branch = ordinary_tree(data, child, stack + (ident,))
        if branch is None:
            return None
        out.extend(branch)
    return out


def pattern_carriers(data, entry):
    if entry.get('table') != 'bosspattern' or entry.get('layer') != 'CACHE':
        return []
    pid = entry['reference_id'];parent = node(data, 'bosspattern', pid)
    if parent is None or parent['raw'] != entry.get('record'):
        return []
    results = []
    for i in range(10):
        sid = parent['raw'].get(f'skillid{i}')
        if not sid:
            continue
        if i > 6:
            return []  # No claim about execution of the unused tail slots.
        boss = node(data, 'bossskill', sid)
        if boss is None:
            return []
        aid = boss['raw'].get('s_ability')
        if aid in (None, 0):
            continue
        if not isinstance(aid, int) or isinstance(aid, bool):
            return []
        tree = ordinary_tree(data, aid)
        if tree is None:
            return []
        for item, path in tree:
            raw = item['raw']
            if raw.get('ability') == 2012 and 'param6' in raw:
                results.append({'item':item, 'path':{'pattern_id':pid, 'slot':f'skillid{i}',
                    'boss_id':sid, 'ordinary_sub_path':path}, 'parent':parent})
    return results


def _binding(row, index, answer, source, scope=SCOPE):
    text = unicodedata.normalize('NFKC', row['japanese'])
    matches = list(WORD.finditer(text))
    if len(matches) != 1:
        return
    m = matches[0]
    binding = {k:source[k] for k in ('layer', 'table', 'record_id', 'field_path', 'record_key')}
    binding.update(answer_index=index, row_id=row['row_id'], effect_type=m.group()+'（词表外）',
                   span=[m.start(),m.end()], rule_key=answer.get('rule_key') or 'skilllist|7|/param7')
    row['attack_interval'] = {'scope':scope, 'bindings':[binding]}


def _attach(row, item, field, path, conditions, duration=None, *, scope=SCOPE, target=None, report=REPORT):
    raw = item['raw'];ability = raw['ability'];value = raw[field]
    answer = R.answer_for('skilllist', ability, '/'+field, value, raw, source_layer='CACHE')
    if answer is None:
        return
    source = {**copy.deepcopy(item['source']), 'table':'skilllist', 'record_id':raw['skillid'],
              'field_path':'/'+field}
    text = answer['value_text']
    if duration is not None:
        text += f'；本项支持持续{duration:g}游戏秒'
    answer.update(value=text, rule_key=f'skilllist|{ability}|/{field}', table='skilllist',
        record_id=raw['skillid'], layer='CACHE', source=source, conditions=conditions,
        target=target or ('自身' if raw.get('param8') == 64 or ability == 7 else '原目标选择范围'),
        numeric_evidence='推断', association_evidence='推断', evidence_scope=scope,
        rule_body_status='已确认（字段与局部公式）', rule_status='本条描述归属为推断',
        numeric_source='真实CACHE记录及有界原生局部公式', evidence=[report],
        binding={'scope':scope, 'path':path},
        note='规则本体已确认；句→载体为数据结构归属推断。实际装载、summary刷新/过期和动画每击周期未验证；'
             '固有atkspeed不作为该技能贡献。'+conditions)
    index = len(row['answers']);row['answers'].append(answer)
    _binding(row,index,answer,source,scope)
    row['attack_interval']['path'] = path
    row['attack_interval']['duration_raw'] = duration
    if row['row_class'] == 'C':
        row['row_class'] = 'A'
        row['evidence'] = '推断'
        row['evidence_label'] = '推断（攻击间隔局部贡献）'
    row['numeric_evidence'] = '推断' if row.get('numeric_evidence') != '确认' else row['numeric_evidence']
    row['association_evidence'] = '推断' if row.get('association_evidence') != '确认' else row['association_evidence']
    row['evidence_scope'] = list(dict.fromkeys(row.get('evidence_scope',[])+[scope]))
    row['partial'] = True
    row['unknown_reasons'] = list(dict.fromkeys(row.get('unknown_reasons',[]) +
        ['本项局部间隔贡献见附加答案；其他未解机制和实际动作周期保持待办。']))


def apply_to_groups(data, cid, groups):
    if 'Y.G.' not in str((data.profiles.get(cid) or {}).get('title') or ''):
        return
    linked = {g['group']:g for g in data.links[cid]['groups']}
    for group in groups:
        kind = group.get('group')
        if kind not in ('ability','special_move','sympathy'):
            continue
        for skill in group.get('skills',[]):
            rows = [r for r in skill.get('rows',[]) if len(WORD.findall(r['japanese'])) == 1]
            if not rows:
                continue
            entries = [e for e in linked.get(kind,{}).get('records',[])
                       if e.get('reference_field') == skill.get('reference_field')
                       and e.get('table') == skill.get('table') and e.get('layer') == 'CACHE']
            if len(entries) != 1:
                continue
            entry = entries[0]
            if kind == 'ability' and entry.get('table') == 'skilllist' and len(rows) == 1:
                slot = re.fullmatch(r'skillid\[(\d+)\]', entry.get('reference_field', ''))
                actual = data.cache_chara.get(cid, {}).get('skillid')
                if (slot is None or not isinstance(actual, list) or int(slot[1]) >= len(actual)
                        or actual[int(slot[1])] != entry['reference_id']):
                    continue
                root = node(data, 'skilllist', entry['reference_id'])
                if root is None or root['raw'] != entry.get('record'):
                    continue
                tree = ordinary_tree(data,entry['reference_id'])
                if tree is None:
                    continue
                carriers = [(it,path) for it,path in tree if it['raw'].get('ability') == 7
                            and it['raw'].get('skillid') in TYPE7_IDS and finite(it['raw'].get('param7'))
                            and it['raw']['param7'] > 0]
                if len(carriers) != 1:
                    continue
                item,path = carriers[0];row = rows[0];raw = item['raw']
                old = [(i,a) for i,a in enumerate(row['answers']) if a.get('effect_id') == 'other_a2_attack_interval']
                if old:
                    if len(old) == 1:
                        i,a = old[0];proofs=[s for s in a.get('source',[]) if s.get('field_path')=='/param7'
                            and s.get('record_id')==raw['skillid'] and s.get('raw_value')==raw['param7']]
                        if len(proofs)==1:_binding(row,i,a,proofs[0])
                    continue
                ground = R.decode_terrain(raw.get('param0'))
                if ground.get('unknown_group_indices') or ground.get('error'):
                    continue
                conditions = ('持有者自身；地形资格param0='+str(raw.get('param0'))+'，背景位任一匹配才乘；'
                    '地形原生解码='+str(ground)+'；原句上下文='+row.get('context_text',''))
                _attach(row,item,'param7',{'ordinary_sub_path':path},conditions)
            elif kind == 'special_move' and entry.get('table') == 'bosspattern':
                if data.cache_chara.get(cid,{}).get(entry.get('reference_field')) != entry.get('reference_id'):
                    continue
                carriers = pattern_carriers(data,entry)
                eligible = [x for x in carriers if finite(x['item']['raw'].get('param6'))
                            and x['item']['raw']['param6'] < 0]
                if len(eligible) != 1:
                    continue
                candidate = eligible[0]
                _apply_2012(rows, candidate['item'], candidate['path'], entry['record'].get('sinfo',''))
            elif kind == 'sympathy' and entry.get('record',{}).get('ability') == 3005:
                slot = re.fullmatch(r'sympathy_skill_info\[_id=(\d+)\]\.ability(\d+)',
                                    entry.get('reference_field', ''))
                if slot is None or int(slot[1]) != cid:
                    continue
                info = node(data, 'sympathy_skilllist', cid)
                root = node(data, 'skilllist', entry['reference_id'])
                if (info is None or info['raw'].get('ability'+slot[2]) != entry['reference_id']
                        or root is None or root['raw'] != entry.get('record')):
                    continue
                if not hasattr(data,'_attack_interval_grants'):
                    if not hasattr(data,'_attack_interval_store'):node(data,'skilllist',entry['reference_id'])
                    data._attack_interval_grants = GrantResolver(data._attack_interval_store)
                result = data._attack_interval_grants.resolve_ordinary(entry['reference_id'])
                found = result.get('consumer_payload',{}).get('attack_interval_2012',[])
                if result.get('status') != 'resolved_candidate' or len(found) != 1:
                    continue
                grant = found[0]
                _apply_2012(rows, {'raw':grant['raw'],'source':grant['source']},
                            {'grant_path':grant['path_node_ids']}, entry['record'].get('text',''))


def _apply_2012(rows, item, path, parent_text):
    raw = item['raw']
    if (raw.get('ability') != 2012 or not finite(raw.get('param6')) or raw['param6'] >= 0
            or not finite(raw.get('param0')) or raw['param0'] <= 0 or raw.get('flag') != 0
            or raw.get('iParam0',0) != 0 or raw.get('param8') != 64
            or not finite(raw.get('param7')) or int(raw['param7']) != 1):
        return
    # A single explicit self cadence phrase is the supported object/word shape.
    eligible = [r for r in rows if re.search(r'自身の攻撃(?:速度|間隔)',r['japanese'])
                and re.search(r'上が|早く|速く',r['japanese'])
                and parent_text.count(r['japanese']) == 1]
    if len(eligible) != 1:
        return
    row = eligible[0]
    conditions = ('句面对象自身；2012目标param8=64(MYSELF)，param7=1；职业筛选缺失/0；'
        'OnAction附加能力阶段（不等于整场仅一次）；原句触发='+row.get('context_text','')+
        '；源路径='+str(path))
    _attach(row,item,'param6',path,conditions,raw['param0'])
