"""P2 candidate: initial entry only; later slot configuration never closes effects.

Reuse rules and existing CheckEntry evidence; association remains inferred.
No report/manifest from this batch is a runtime input. No native extraction.
"""
from copy import deepcopy
from collections import Counter
import hashlib
import json
import re

import rules as R
from card_page_positions import fragment_positions, position_identity

SCOPE = 'YG1_P2_MULTISTAGE_INITIAL_ENTRY_INFERRED'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'
PARENTS = {
    4316: {'pattern0': 40431600, 'pattern1': 40431601},
    30105: {'pattern0': 43010500, 'pattern1': 43010501},
    30111: {'pattern0': 43011100, 'pattern1': 43011101, 'pattern2': 43011102},
}
ATTRS = (
    ('攻撃力', 'bossskill', 13, 'skillparam1'),
    ('防御力', 'bossskill', 13, 'skillparam2'),
    ('移動速度', 'bossskill', 13, 'skillparam6'),
    ('クリティカル発生率', 'skilllist', 2012, 'param4'),
    ('クリティカル威力', 'skilllist', 2012, 'param5'),
    ('継続時間', 'bossskill', 13, 'skillparam3'),
)
CLAUSE = '味方全体の攻撃力と防御力と移動速度とクリティカル発生率とクリティカル威力が一定時間上がる。'
UPGRADE = '一定時間が経過すると効果が上がる。'
EVIDENCE = [
    'output/character_skills/cp_paths/path_evidence.json',
    'output/boss_chain/34549.txt', 'output/boss_chain/5177.txt',
    'output/boss_chain/5179.txt', 'output/boss_chain/5351.txt',
    'output/boss_chain/trace.json', 'output/boss_heal/trace.json',
    'output/boss_chain/type13_basis/trace.json',
    'output/ordinary_effects/ability2012/trace.json',
]
LIMIT = ('后续增强的触发时点、支持覆盖/叠加与共同到期尚未闭合；'
         '后段配置不是已绑定增强效果，不能用两个支持时长相减求延时。')


def _exact(data, entry):
    """Compare full record to decoded JSON, including claimed identity/pointer."""
    if entry.get('layer') != 'CACHE':
        return None
    table = entry.get('table')
    if table not in ('charainfo', 'bosspattern', 'bossskill', 'skilllist'):
        return None
    stem = 'bossinfo' if table in ('bosspattern', 'bossskill') else table
    if stem not in data.raw_docs:
        data.raw_docs[stem] = json.loads((data.decoded / (stem+'.data5.json.raw')).read_text(encoding='utf-8'))
    doc = data.raw_docs[stem]
    rows = doc['bossinfo'][table] if stem == 'bossinfo' else doc[table]
    key = {'charainfo':'cid', 'bosspattern':'patternid'}.get(table, 'skillid')
    matches = [(i, r) for i, r in enumerate(rows)
               if r.get(key) == entry.get('reference_id') and r == entry.get('record')]
    if len(matches) != 1:
        return None
    pointer = ('/bossinfo' if stem == 'bossinfo' else '') + f'/{table}/{matches[0][0]}'
    source = data.precise_source(entry)
    # Boss precise_source corrects historical coarse links; others must already match.
    if source.get('source_key') != f'CACHE/{stem}.data5.json.raw' or source.get('json_pointer') != pointer:
        return None
    return {**deepcopy(source), 'source_resolution':EXACT,
            'original_file':f'output/cache_full_20261015_v3/decoded/{stem}.data5.json.raw',
            'record_key':f'CACHE/{stem}.data5.json.raw#{pointer}'}


def _graph(data, cid):
    errors = []
    groups = [g for g in data.links.get(cid, {}).get('groups', []) if g.get('group') == 'special_move']
    if len(groups) != 1:
        return [], ['SPECIAL_MOVE_GROUP_NOT_UNIQUE']
    entries = groups[0]['records']
    charas = [e for e in entries if e.get('table') == 'charainfo' and e.get('reference_id') == cid]
    chara = data.cache_chara.get(cid)
    if len(charas) != 1 or not chara or not _exact(data,{**charas[0],'record':chara}):
        return [], ['CHARA_SOURCE_MISMATCH']
    projection=charas[0]['record']
    # links stores a projection with absent slots materialized as None. Validate that
    # projection but perform all missing/null-sensitive checks on decoded raw chara.
    for key,value in projection.items():
        expected = chara.get('skillid',[None])[0] if key=='skillid0' else 'charainfo.skillid[0]' if key=='skillid0_ref' else chara.get(key)
        if value != expected:
            return [], ['CHARA_PROJECTION_MISMATCH']
    actual = {k:v for k,v in chara.items() if k.startswith('pattern') and k[7:].isdigit() and v}
    if actual != PARENTS[cid]:
        return [], ['CHARA_PARENT_MAP_CHANGED']
    branches = []
    for ref, pid in PARENTS[cid].items():
        found = [e for e in entries if e.get('table') == 'bosspattern'
                 and e.get('reference_field') == ref and e.get('reference_id') == pid]
        if len(found) != 1 or not _exact(data, found[0]):
            errors.append(f'{ref}:PARENT_SOURCE_OR_REFERENCE_MISMATCH')
            continue
        parent = found[0]
        rec = parent['record']
        if chara.get(ref) != pid or rec.get('patternid') != pid:
            errors.append(f'{ref}:CHARA_PARENT_EDGE_MISMATCH')
            continue
        # Three complete nonzero slots; missing/extra/duplicate edges are refused.
        slots = [(f'skillid{i}', rec.get(f'skillid{i}')) for i in range(7) if rec.get(f'skillid{i}')]
        children = parent.get('boss_skill_refs', [])
        if [s for s,_ in slots] != ['skillid0', 'skillid1', 'skillid2'] or len(children) != 3:
            errors.append(f'{ref}:THREE_SLOT_SHAPE_CHANGED')
            continue
        edges = []
        for slot, sid in slots:
            picks = [c for c in children if c.get('table') == 'bossskill'
                     and c.get('reference_id') == sid and c.get('reference_field') == f'bosspattern[{pid}].{slot}']
            if len(picks) != 1 or not _exact(data, picks[0]):
                break
            child = picks[0]
            support = data.skill(child['record'].get('s_ability'))
            if not support or not _exact(data, support):
                break
            edges.append(dict(slot=slot, child=child, source=_exact(data, child),
                              support=support, support_source=_exact(data, support)))
        if len(edges) != 3:
            errors.append(f'{ref}:CHILD_OR_SUPPORT_SOURCE_MISMATCH')
            continue
        first, middle, later = edges
        # Initial slot means CheckEntry item(0), not first type13 found by search.
        if [e['child']['record'].get('skillid0') for e in edges] != [13, 110 if cid == 30105 else 116, 13]:
            errors.append(f'{ref}:EXECUTION_ENTRY_TYPE_SHAPE_CHANGED')
            continue
        if any(e['support']['record'].get('ability') != t for e,t in zip(edges, (2012,2003,2012))):
            errors.append(f'{ref}:SUPPORT_TYPES_CHANGED')
            continue
        # Bind each carrier to its own direct s_ability, never pair by equal values.
        good = True
        for edge in (first, later):
            b = edge['child']['record']; s = edge['support']['record']
            active = {k for k,v in b.items() if k.startswith('skillparam') and v != 0}
            if active != {'skillparam1','skillparam2','skillparam3','skillparam6'}:
                good = False
            if s.get('param8') != 31 or s.get('param7') != 20 or s.get('sub') != [] or s.get('param0',0) <= 0:
                good = False
            if any(k in s for k in ('iParam0','iparam0')):
                good = False
            if b.get('s_ability') != edge['support']['reference_id']:
                good = False
        if not good:
            errors.append(f'{ref}:CARRIER_SHAPE_OR_TARGET_CHANGED')
            continue
        branches.append(dict(parent=parent, source=_exact(data,parent), reference_field=ref,
                             pattern_id=pid, edges=edges, chara=chara))
    return branches, errors


def _same_slots(chara, child):
    return (chara.get('skillid', [None])[0] == child.get('skillid0')
            and all((k in chara, chara.get(k)) == (k in child, child.get(k))
                    for k in [f'skillparam{i}' for i in range(10)]))


def _config(branch):
    return dict(pattern_id=branch['pattern_id'], reference_field=branch['reference_field'],
        conditions_raw=deepcopy(branch['parent']['record']),
        parent_binding_status='CONFIG_ONLY_NO_INDEPENDENT_PROSE' if not branch['parent']['record'].get('sinfo') else 'PROSE_PARENT',
        entries=[dict(slot=e['slot'], child_id=e['child']['reference_id'],
                      raw_record=deepcopy(e['child']['record']), source=deepcopy(e['source']),
                      support_id=e['support']['reference_id'],
                      support_raw_record=deepcopy(e['support']['record']),
                      support_source=deepcopy(e['support_source'])) for e in branch['edges']],
        later_stage_status='CONFIG_ONLY_NOT_BOUND_TO_UPGRADE', limit=LIMIT)


def _expected_row_id(data, cid, entry, fragment_index):
    """Replay build_card's special_move display ordinal from actual linked entries."""
    linked=[g for g in data.links[cid]['groups'] if g.get('group')=='special_move']
    if len(linked)!=1:return None
    slots={};target=None
    for item in linked[0]['records']:
        source=data.precise_source(item)
        key=json.dumps(['special_move',item.get('reference_field'),item.get('table'),
                        item.get('reference_id'),item.get('record'),source.get('source_key'),
                        source.get('json_pointer')],sort_keys=True,ensure_ascii=False)
        ordinal=slots.setdefault(key,len(slots))
        if item is entry:
            target=ordinal
    if target is None:return None
    level=entry['record'].get('lv','order'+str(target))
    ident=f"{cid}-special_move-special_move-{entry['reference_field']}-lv{level}-f{fragment_index}"
    return re.sub(r'[^\w\-]','_',ident)


def _row_position_matches(data, cid, skill, row, branch, source):
    """Bind the displayed fragment to its exact decoded field and generator identity."""
    table=skill['table']
    field='sinfo' if table=='bosspattern' else 'skilltext'
    if table=='bosspattern':
        entry=branch['parent'];raw=entry['record']
    else:
        entries=[e for g in data.links[cid]['groups'] if g.get('group')=='special_move'
                 for e in g['records'] if e.get('table')=='charainfo'
                 and e.get('reference_id')==cid and e.get('reference_field')=='skilltext']
        if len(entries)!=1:return False
        entry=entries[0];raw=branch['chara']
    projected=entry['record']
    ident=entry['reference_id'];ref=entry['reference_field']
    level=projected.get('lv')
    level_state=('missing' if 'lv' not in projected else 'null' if level is None
                 else 'zero' if level==0 else 'present')
    if (skill.get('layer')!='CACHE' or skill.get('record_id')!=ident
            or skill.get('reference_field')!=ref or skill.get('text_field')!=field
            or skill.get('original_group')!='special_move'
            or skill.get('level_state')!=level_state or skill.get('level')!=level):
        return False
    for candidate in (skill.get('source') or {},row.get('source') or {}):
        if any(source.get(k) is None or candidate.get(k)!=source[k]
               for k in ('layer','record_key','source_key','json_pointer')):
            return False
    pointer=source['json_pointer']+'/'+field
    row_source=row.get('source') or {}
    if row_source.get('field')!='/'+field or row_source.get('field_json_pointer')!=pointer:
        return False
    raw_text=raw.get(field)
    if not isinstance(raw_text,str):return False
    clean_text=raw_text.replace('\\n','\n')
    if skill.get('original_text')!=clean_text or row.get('context_text')!=clean_text:
        return False
    index=row.get('fragment_index');positions=fragment_positions(raw_text)
    if not isinstance(index,int) or isinstance(index,bool) or not 0<=index<len(positions):
        return False
    if row.get('row_id')!=_expected_row_id(data,cid,entry,index):
        return False
    span=positions[index]
    expected_position={**span,'field_pointer':pointer,'source_key':source['source_key']}
    position=row.get('source_position') or {}
    if not isinstance(position,dict):return False
    for key in ('raw_span','clean_span'):
        limits=position.get(key)
        if (not isinstance(limits,list) or len(limits)!=2 or
                any(not isinstance(v,int) or isinstance(v,bool) for v in limits)):
            return False
    if row.get('source_position')!=expected_position or row.get('japanese')!=span['japanese']:
        return False
    if (row.get('cid')!=cid or row.get('group')!='special_move'
            or row.get('reference_field')!=ref or row.get('level')!=level
            or row.get('stage')!=skill.get('stage')
            or row.get('source_evidence_ref')!=skill.get('skill_id')):
        return False
    execution=dict(reference_slot=ref,parent_record_sha256=hashlib.sha256(
        json.dumps(projected,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest())
    identity=position_identity(cid,'special_move',{'source_key':source['source_key'],
        'field_json_pointer':pointer},table,ident,level_state,level,span,'special_move',execution)
    encoded=json.dumps(identity,ensure_ascii=False,separators=(',',':'))
    return (row.get('merge_key')==identity and row.get('source_span_id')==
            'span-'+hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:20])


def _answers(row, branch, mirror):
    answers = []
    edge = branch['edges'][0]
    mode='超共鸣必杀' if branch['parent']['record'].get('sinfo','').startswith('【超共鳴必殺/') else '共鸣必杀'
    label=mode+'的初始支援阶段，本页档位生效时'
    source_label=f"{branch['reference_field']} / pattern {branch['pattern_id']} 被选中时的初始支持阶段"
    for attr, table, typ, field in ATTRS:
        entry = edge['child'] if table == 'bossskill' else edge['support']
        source = edge['source'] if table == 'bossskill' else edge['support_source']
        raw = entry['record'].get(field)
        converted = R.answer_for(table, typ, '/'+field, raw, entry['record'])
        if converted is None:
            return []
        rule = R.rule_for(table,typ,'/'+field) or {}
        human = {
            '攻撃力': f'技能连锁系数为1时，攻击提升{raw*100:g}%；实际提升受连锁系数影响',
            '防御力': f'获得固定防御加成；在已核玩家构造缩放条件、技能连锁系数为1时，名义原始攻击力系数约为{raw*10:g}%，实际固定量取决于当前攻击基数和连锁系数',
            '移動速度': f'技能连锁系数为1时，移动速度提升{raw*100:g}%；实际提升受连锁系数影响',
            'クリティカル発生率': f'暴击概率加算贡献为+{raw*100:g}个百分点',
            'クリティカル威力': f'暴伤系数加算贡献为+{raw:g}',
            '継続時間': f'这组攻击、固定防御与移速加成的支持计时为{raw:g}游戏秒',
        }[attr]
        note = ('CheckEntry在0x12954b0取执行列表item(0)，0x12954c0调用SetExecSkill；'
                '本值取该slot0的真实字段。归属为推断，规则复用；不保证所有实际接受者与最终战斗结果。'
                't13对象来自句面味方全体及target=1成员列表；2012自身目标输入param8=31、param7=20，'
                '二者实际名单不主张完全相同。2012时间/暴击两项不乘Chain。'+LIMIT)
        if mirror:
            note += 'charainfo完整正文及十参数槽逐值/缺失状态等价；数值仍取本父链真实子记录。'
        answers.append(dict(value=human+'（归属推断）',
            quantity_kind=converted['quantity_kind'], unit=converted['unit'], raw_value=raw,
            quantitative=True, numeric_source='复用既有局部规则；初始入口结构归属推断',
            numeric_evidence='推断', association_evidence='推断', evidence_scope=SCOPE,
            answer_status=converted['answer_status'], rule_key=f'{table}|{typ}|/{field}',
            table=table, record_id=entry['reference_id'], layer='CACHE', field_path='/'+field,
            source={**deepcopy(source),'table':table,'record_id':entry['reference_id'],
                    'field_path':'/'+field,'field_json_pointer':source['json_pointer']+'/'+field},
            rule_status=rule.get('status'), conversion=rule.get('conversion'),
            base_definition=rule.get('base_definition'), conditions=rule.get('applicability'),
            rule_limits=rule.get('limits'), condition_label=label,
            target='味方全体（实际接受者受各处理器成员列表筛选）',
            binding=dict(pattern_id=branch['pattern_id'],slot='skillid0',
                         reference_field=branch['reference_field'],source_condition_label=source_label,
                         child_id=edge['child']['reference_id'], support_id=edge['support']['reference_id'],
                         phase='INITIAL_ENTRY_ONLY', conditions_raw=deepcopy(branch['parent']['record']),
                         pattern_source=deepcopy(branch['source'])),
            evidence=EVIDENCE[:], note=note))
        if attr=='防御力':
            answers[-1]['exact_formula']='trunc(float32(float32(normalAtk)×float32(p2×Chain)))'
            answers[-1]['note']+=('固定防御精确式：trunc(float32(float32(normalAtk)×float32(p2×Chain)))；'
                'p2和Chain为单精度输入，先将normalAtk转换为float32，系数乘法和最终乘积各作float32舍入，再向零截断。'
                'normalAtk=20、p2=.35、Chain=1时，原生单精度乘积为7；省略最终乘积舍入会误得6。')
    return answers


def apply_to_groups(data, cid, groups):
    report = dict(cid=cid, added_answers=0, initial_rows=[], blocked_upgrade_rows=[], rejections=[])
    if cid not in PARENTS:
        return report
    ids=[row.get('row_id') for group in groups for skill in group.get('skills',[])
         for row in skill.get('rows',[])]
    if any(not isinstance(ident,str) or not ident for ident in ids):
        report['rejections']=['MALFORMED_ROW_ID']
        return report
    duplicates=[ident for ident,count in Counter(ids).items() if count>1]
    if duplicates:
        report['rejections']=['DUPLICATE_ROW_ID:'+ident for ident in duplicates]
        return report
    branches, errors = _graph(data,cid)
    if errors or len(branches) != len(PARENTS[cid]):
        report['rejections'] = errors or ['PARENT_SET_INCOMPLETE']
        return report
    for group in groups:
        if group.get('group') != 'special_move':
            continue
        for skill in group.get('skills', []):
            table = skill.get('table')
            if table not in ('bosspattern','charainfo'):
                continue
            selected = []
            body = skill.get('original_text')
            if table == 'bosspattern':
                selected = [b for b in branches if b['pattern_id'] == skill.get('record_id')
                            and b['reference_field'] == skill.get('reference_field')
                            and b['parent']['record'].get('sinfo') == body]
            elif skill.get('record_id') == cid and skill.get('reference_field') == 'skilltext':
                matches = [b for b in branches if b['parent']['record'].get('sinfo') == body
                           and _same_slots(b['chara'], b['edges'][0]['child']['record'])]
                if len(matches) == 1:
                    selected = matches[:]
                    normal = matches[0]
                    # Blank-text companion is preserved only with identical complete three-slot chain.
                    selected += [b for b in branches if not b['parent']['record'].get('sinfo')
                                 and [e['child']['record'] for e in b['edges']] ==
                                     [e['child']['record'] for e in normal['edges']]
                                 and [e['support']['record'] for e in b['edges']] ==
                                     [e['support']['record'] for e in normal['edges']]]
            if not selected:
                continue
            expected_source = selected[0]['source'] if table=='bosspattern' else _exact(data,dict(
                table='charainfo',layer='CACHE',reference_id=cid,record=selected[0]['chara'],source=skill.get('source')))
            if not expected_source or any(skill.get('source',{}).get(k)!=expected_source.get(k)
                                          for k in ('source_key','json_pointer')):
                report['rejections'].append(f"{skill.get('skill_id')}:PROJECTED_SOURCE_MISMATCH")
                continue
            # Exact full prose/fragment reconstruction refuses competing body added in UI projection.
            if ''.join(r.get('japanese','') for r in skill.get('rows',[])) != body:
                report['rejections'].append(f"{skill.get('skill_id')}:PROJECTED_BODY_MISMATCH")
                continue
            for row in skill.get('rows', []):
                text = row.get('japanese','')
                if any(row.get('source',{}).get(k)!=expected_source.get(k) for k in ('source_key','json_pointer')):
                    report['rejections'].append(row.get('row_id','')+':ROW_SOURCE_MISMATCH')
                    continue
                if not _row_position_matches(data,cid,skill,row,selected[0],expected_source):
                    report['rejections'].append(row.get('row_id','')+':ROW_FIELD_OR_POSITION_MISMATCH')
                    continue
                if text == UPGRADE:
                    row['yg1_multistage_config'] = [_config(b) for b in selected]
                    row['unknown_reasons'] = list(dict.fromkeys(row.get('unknown_reasons',[])+[LIMIT]))
                    report['blocked_upgrade_rows'].append(row['row_id'])
                    continue
                if text not in ('【共鳴必殺/連撃】'+CLAUSE,'【超共鳴必殺/連撃】'+CLAUSE):
                    continue
                if any(a.get('evidence_scope') == SCOPE for a in row.get('answers',[])):
                    continue
                # A preexisting answer for any of these claims is not overwritten or reinterpreted.
                keys = {f'{t}|{typ}|/{f}' for _,t,typ,f in ATTRS}
                if any(a.get('rule_key') in keys for a in row.get('answers',[])):
                    report['rejections'].append(row['row_id']+':EXISTING_CLAIM_ANSWER_PRESERVED')
                    continue
                # Blank prose companion keeps its separate conditions in configuration;
                # do not manufacture an effect binding or duplicate 2012 answers for it.
                additions = _answers(row,selected[0],table=='charainfo')
                if len(additions) != 6:
                    report['rejections'].append(row['row_id']+':RULE_UNAVAILABLE')
                    continue
                row.setdefault('answers',[]).extend(additions)
                row.update(inference_yg1_multistage=True, row_class='A',partial=True,
                           evidence_label='推断（YG1初始执行入口归属；后段阶段仍未解）',
                           evidence='推断', numeric_evidence='推断', association_evidence='推断')
                scopes=row.get('evidence_scope',[])
                if isinstance(scopes,str): scopes=[scopes]
                row['evidence_scope']=list(dict.fromkeys(scopes+[SCOPE]))
                row['yg1_multistage_config'] = [_config(b) for b in selected]
                row['unknown_reasons'] = list(dict.fromkeys(row.get('unknown_reasons',[])+[LIMIT]))
                if len(selected)>1:
                    row['unknown_reasons'].append('无正文Chain伴随档仅按独立父条件保留配置；没有独立描述绑定或额外2012答案。')
                report['initial_rows'].append(row['row_id'])
                report['added_answers'] += len(additions)
    return report
