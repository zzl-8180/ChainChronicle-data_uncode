"""Additive, source-checked candidates for remaining YG1 P1/P3.

Install next to the existing consumers; host wires apply_to_groups after cadence.
No candidate manifest, report, ledger file, or per-CID numeric answer is read.
CID sets are admission boundaries, not numeric lookup tables.
"""
from copy import deepcopy
from pathlib import Path
import json
import json
import re
import unicodedata

import rules as R
import card_page_inference_attack_interval as A
import card_page_inference_attack_interval2 as B
import card_page_inference_yg1 as Y
import card_page_inference_yg1_multihit as M
from card_page_positions import fragment_positions

SCOPE = 'YG1_REMAINING_AB_P1_P3_SOURCE_ONLY'
DURATION_CIDS = {30002,30101,30108,30112,30202,30218,30221,30228,30229,
                 30238,30239,30241,30243,30245,30254,30312,30318,30324,30325,30336}
MIRROR_CIDS = {30002,30229,30255,30306}
BUFF_CIDS = {7250,30219,30220}
DAMAGE_CIDS = {30201,30207,30210,30222,30247,30251,30258,30262,30304,30308,30321,30335}
HEAL_CIDS = {10215,30228,30314}
TAIL_CIDS = {30104,30205,30252,30255,30306}
ADMITTED_CIDS = DURATION_CIDS | MIRROR_CIDS | BUFF_CIDS | DAMAGE_CIDS | HEAL_CIDS | TAIL_CIDS | {30301}
SELF_SPEED = re.compile(r'^(?:その後、|また|さらに)自身の攻撃速度が一定時間上がる。$')
ALLY_BUFF = re.compile(r'^【(?:超)?共鳴必殺[^】]*】味方全体の攻撃力と防御力と移動速度が一定時間上が(?:る。|り、)')
HEAL = re.compile(r'^【(?:超)?共鳴必殺/連撃】味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。$')


def _graph(data, cid):
    graph = B._patterns(data, cid)
    if graph is None:
        return None
    chara, patterns = graph
    entries = [e for g in data.links[cid]['groups'] if g['group']=='special_move'
               for e in g.get('records', [])]
    result = {}
    for ref, (entry, item) in patterns.items():
        if Y._parent_issues(data, chara['raw'], entries, entry):
            return None
        edges, issues = M.ordered(data, entry)
        if issues:
            return None
        for edge in edges:
            child = A.node(data, 'bossskill', edge['child_id'])
            if child is None or child['raw'] != edge['record']:
                return None
            edge['item'] = child
        result[ref] = dict(entry=entry, item=item, edges=edges)
    return chara, result


def _row_identity_ok(data, cid, skill, row, raw):
    """Reproduce build_card's display ordinal/ID from actual links, not display claims.

    This consumer only admits special_move; that namespace has no leader text expansion.
    Identical link aliases share a display ordinal exactly as in build_card.
    """
    original_group='special_move'
    links=[g for g in data.links[cid]['groups'] if g.get('group')==original_group]
    if (len(links)!=1 or row.get('cid')!=cid or row.get('group')!='special_move'
            or skill.get('original_group')!=original_group):
        return False
    display_slots={};matches=set()
    for origin_ordinal, entry in enumerate(links[0].get('records',[])):
        record=entry.get('record',{});table=entry.get('table')
        ref=entry.get('reference_field',str(origin_ordinal))
        exact=data.precise_source(entry)
        display_key=json.dumps([original_group,ref,table,entry.get('reference_id'),record,
                                exact.get('source_key'),exact.get('json_pointer')],
                               sort_keys=True,ensure_ascii=False)
        ordinal=display_slots.setdefault(display_key,len(display_slots))
        if (table!=skill.get('table') or ref!=skill.get('reference_field')
                or entry.get('reference_id')!=skill.get('record_id')
                or entry.get('layer')!=skill.get('layer')
                # charainfo links are the producer's skill projection, not the full raw character.
                # Its identity uses that projection's lv/ordinal; full raw/source/ten-slot gates follow.
                or (table!='charainfo' and record!=raw)):
            continue
        expected=f'{cid}-special_move-{original_group}-{ref}-lv{record.get("lv","order"+str(ordinal))}-f{row.get("fragment_index")}'
        matches.add(re.sub(r'[^\w\-]','_',expected))
    return len(matches)==1 and row.get('row_id') in matches


def _row_ok(data, cid, skill, row, root, ident, field, source=None):
    if not _row_identity_ok(data,cid,skill,row,root['raw']):
        return False
    body = root['raw'].get(field, '')
    if (skill.get('original_text') != body
            or row.get('context_text') != str(body).replace('\\n', '\n')):
        return False
    positions=fragment_positions(body)
    ordinal=row.get('fragment_index')
    position=row.get('source_position') or {}
    return (isinstance(ordinal,int) and not isinstance(ordinal,bool) and 0<=ordinal<len(positions)
            and all(position.get(k)==positions[ordinal].get(k) for k in ('japanese','raw_span','clean_span'))
            and row.get('reference_field')==skill.get('reference_field')
            and B._row_on_root(skill, row, root, field, ident, source))


def _selected(data, cid, skill, row, chara, patterns, *, interior_mirror=False):
    if skill.get('table') == 'bosspattern':
        parent = patterns.get(skill.get('reference_field'))
        if parent is None or parent['entry']['reference_id'] != skill.get('record_id'):
            return []
        if not _row_ok(data,cid,skill,row,parent['item'],skill['record_id'],'sinfo',data.precise_source(parent['entry'])):
            return []
        return [parent]
    if (skill.get('table') != 'charainfo' or skill.get('reference_field') != 'skilltext'
            or not _row_ok(data,cid,skill,row,chara,cid,'skilltext')):
        return []
    body = chara['raw'].get('skilltext')
    parents = []
    for parent in patterns.values():
        # Whole body and type + presence/value of all ten parameters are independent gates.
        if parent['item']['raw'].get('sinfo') != body:
            continue
        candidates = parent['edges'] if interior_mirror else parent['edges'][:1]
        matches = [e for e in candidates if Y._same_slots(chara['raw'],e['record'])]
        if len(matches)==1:
            parents.append(parent)
    return parents if len(parents)==1 else []


def _binding(parent, edge=None):
    entry = parent['entry']
    out = dict(scope=SCOPE, pattern_id=entry['reference_id'],
               reference_field=entry['reference_field'],
               conditions_raw=deepcopy(entry['record']),
               pattern_source=deepcopy(parent['item']['source']),
               ordered_children=[dict(slot=e['slot'], child_id=e['child_id'], type=e['type'],
                                      source=deepcopy(e['item']['source'])) for e in parent['edges']])
    if edge:
        out.update(slot=edge['slot'], child_id=edge['child_id'])
    return out


def _append(row, answer, report, kind):
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'),
                     a.get('remaining_ab_binding',{}).get('pattern_id'))
    if any(key(a)==key(answer) for a in row.get('answers', [])):
        return
    # This candidate has one selected real parent per row; technical identity stays in details.
    answer['condition_label']='本页这一档必杀生效时'
    row['answers'].append(answer)
    if row.get('row_class')=='C':
        row.update(row_class='A',evidence='推断',evidence_label='推断（剩余YG1精确来源绑定）')
    for k in ('numeric_evidence','association_evidence'):
        if row.get(k) not in ('确认','推断'):
            row[k]='推断'
    row['partial'] = True
    row['evidence_scope'] = list(dict.fromkeys(row.get('evidence_scope',[])+[SCOPE]))
    # Existing answers, notes and hints are never removed or rewritten.
    report['answers_added'] += 1
    report['additions'].append(dict(row_id=row['row_id'],kind=kind,answer_index=len(row['answers'])-1,
                                    rule_key=answer['rule_key'],record_id=answer['record_id']))


def _source_answer(item, table, typ, field, parent, target):
    raw = item['raw']
    if field not in raw or not A.finite(raw[field]):
        return None
    answer = R.answer_for(table,typ,'/'+field,raw[field],raw,source_layer='CACHE')
    if not answer or not answer.get('quantity_kind'):
        return None
    # Rule evidence may use Python tuples; the delivered answer is standard JSON.
    answer = json.loads(json.dumps(answer, ensure_ascii=False, allow_nan=False))
    ident = raw['skillid']
    answer.update(value=answer['value_text'], rule_key=f'{table}|{typ}|/{field}',
                  table=table,record_id=ident,layer='CACHE',target=target,
                  source={**deepcopy(item['source']),'table':table,'record_id':ident,'field_path':'/'+field},
                  numeric_evidence='推断',association_evidence='推断',evidence_scope=SCOPE,
                  quantitative=True,remaining_ab_binding=_binding(parent),
                  condition_label=f"{parent['entry']['reference_field']} / pattern {parent['entry']['reference_id']} 被选中时",
                  conditions='仅该完整父分支被选择时适用；完整条件原值和有序子边见remaining_ab_binding。',
                  rule_body_status='复用既有字段局部规则，句内归属为推断')
    return answer


def _duration_source_note(data, carrier):
    raw = carrier['item']['raw']
    parents = [A.node(data, 'skilllist', ident)['raw']
               for ident in carrier['path']['ordinary_sub_path'][:-1]]
    if not parents:
        return f"直接引用支持记录{raw['skillid']}；param0与param6在同一记录，不经sub。"
    parent_ids = '→'.join(str(p['skillid']) for p in parents)
    parent_times = '、'.join(f"{p['skillid']}.param0={p.get('param0', '缺失')}" for p in parents)
    same_time = all('param0' in p and p['param0'] == raw['param0'] for p in parents)
    location = 'param6只在sub' if all('param6' not in p for p in parents) else '父记录也含param6，不视作仅sub字段'
    return (f"本档支持父记录{parent_ids}→sub记录{raw['skillid']}；{location}；"
            f"父记录{parent_times}，sub.param0={raw['param0']}，"
            f"当前父子param0{'同值' if same_time else '不全同值，须另行复核'}。"
            '本答案仍引用sub的param0；不得以当前同值替代未来快照的父档核对。')


def _speed(data,cid,skill,row,chara,patterns,report):
    if not SELF_SPEED.fullmatch(row.get('japanese','')):
        return
    mirror = skill.get('table')=='charainfo'
    # New non-head mirror admission is restricted to the four reviewed setup/dash families.
    interior = mirror and cid in MIRROR_CIDS
    parents = _selected(data,cid,skill,row,chara,patterns,interior_mirror=interior)
    if len(parents)!=1:
        report['rejections'].append(dict(row_id=row['row_id'],reason='SPEED_BODY_SOURCE_OR_TEN_SLOT_GATE'))
        return
    parent = parents[0]
    if parent['item']['raw'].get('sinfo','').count(row['japanese']) != 1:
        return
    carriers = A.pattern_carriers(data,parent['entry'])
    selected = []
    for c in carriers:
        r=c['item']['raw']
        if (r.get('ability')==2012 and A.finite(r.get('param6')) and r['param6']<0
                and A.finite(r.get('param0')) and r['param0']>0 and r.get('flag')==0
                and r.get('iParam0',0)==0 and r.get('param8')==64
                and A.finite(r.get('param7')) and int(r['param7'])==1):
            selected.append(c)
    if len(selected)!=1:
        report['rejections'].append(dict(row_id=row['row_id'],reason='SELF_2012_CARRIER_NOT_UNIQUE'))
        return
    c=selected[0];raw=c['item']['raw']
    cadence=[a for a in row.get('answers',[]) if a.get('rule_key')=='skilllist|2012|/param6']
    if not cadence and interior:
        # Reuse the established cadence answer/binding producer after the stronger full graph gate.
        A._apply_2012([row],c['item'],c['path'],parent['item']['raw']['sinfo'])
        cadence=[a for a in row.get('answers',[]) if a.get('rule_key')=='skilllist|2012|/param6']
        if cadence:
            # These four are newly created here. Never rewrite an earlier producer's answer.
            cadence[0].update(value=(f"自身这项加速使攻击间隔因子减少{-raw['param6']:g}；其他同类加成中性、无自定义限制对象且采用默认上下界时，"
                f"间隔因子为{max(.5,min(2.,1+raw['param6'])):g}（推断）。这项支持持续{raw['param0']:g}游戏秒。"
                '在此默认条件下，同类加成汇总后限于0.5至2；实际动作周期还受其他因素影响。'),
                base_definition='2012支持汇总层：无自定义限制对象、采用默认上下界时，clamp(1+Σparam6,0.5,2)；不是最终每击周期。',
                condition_label='本页这一档必杀生效时',
                description_binding_scope=SCOPE,remaining_ab_binding=_binding(parent))
            report['answers_added']+=1
            report['additions'].append(dict(row_id=row['row_id'],kind='speed_mirror',
                answer_index=len(row['answers'])-1,rule_key=cadence[0]['rule_key'],record_id=cadence[0]['record_id']))
    if len(cadence)!=1:
        return
    old=cadence[0];source=old.get('source') or {}
    if (old.get('record_id')!=raw['skillid'] or old.get('raw_value')!=raw['param6']
            or any(source.get(k)!=c['item']['source'].get(k) for k in
                   ('record_key','source_key','json_pointer','raw_record_sha256'))):
        return
    old_path=(old.get('binding') or {}).get('path') or {}
    if 'all_matching_pattern_branches' in old_path:
        branches=old_path['all_matching_pattern_branches']
        if (old_path.get('branch_count')!=1 or len(branches)!=1
                or branches[0].get('configured_pattern')!=parent['entry']['reference_id']
                or branches[0].get('description_pattern')!=parent['entry']['reference_id']):
            return
        old_path=branches[0].get('carrier_path')
    if old_path!=c['path']:
        return
    # The old trusted cadence binding is necessary but is rechecked against current actual edges.
    index=row['answers'].index(old)
    binding=[b for b in (row.get('attack_interval') or {}).get('bindings',[]) if b.get('answer_index')==index]
    word=re.search('攻撃速度',unicodedata.normalize('NFKC',row['japanese']))
    if (len(binding)!=1 or binding[0].get('row_id')!=row['row_id']
            or binding[0].get('span')!=[word.start(),word.end()]
            or binding[0].get('record_id')!=raw['skillid']):
        return
    answer=_source_answer(c['item'],'skilllist',2012,'param0',parent,'自身')
    if answer is None:
        return
    answer.update(quantity_kind='持续时间',value=f"这项自身加速持续{raw['param0']:g}游戏秒（推断）。",
        unit='游戏秒',note='来自同一自身加速支持记录的正param0；不从旧value字符串取数，不借全体增益或敌方减益时间。实际装载和选档仍未实机验证。'+_duration_source_note(data,c),
        supporting_fields=[dict(field_path='/param6',raw_value=raw['param6'])])
    answer['remaining_ab_binding'].update(carrier_path=deepcopy(c['path']),
        text_row_id=row['row_id'],source_position=deepcopy(row['source_position']),
        mirror_interior_equivalence=interior)
    _append(row,answer,report,'known_duration_binding' if cid in DURATION_CIDS else 'mirror_duration')


def _buff(data,cid,skill,row,chara,patterns,report):
    text=row.get('japanese','')
    if not ALLY_BUFF.match(text):
        return
    selected=_selected(data,cid,skill,row,chara,patterns)
    if len(selected)!=1:
        report['rejections'].append(dict(row_id=row['row_id'],reason='ALLY_FULL_SOURCE_GATE'))
        return
    parent=selected[0];body=parent['item']['raw']['sinfo']
    carriers=[e for e in parent['edges'] if e['type']==13]
    # A second gain clause would compete for the same t13, regardless of its position.
    gains=list(re.finditer(r'(?:味方全体|範囲内の味方|自身)の[^。]*?一定時間上が',body))
    if len(carriers)!=1 or len(gains)!=1 or body.count(text)!=1:
        report['rejections'].append(dict(row_id=row['row_id'],reason='ALLY_COMPETING_GAIN_OR_T13'))
        return
    edge=carriers[0];raw=edge['record']
    fields=('skillparam1','skillparam2','skillparam6','skillparam3')
    # Exact union shape; every claimed slot is present, positive, finite. No crit bypass.
    if (any(not A.finite(raw.get(f)) or raw[f]<=0 for f in fields)
            or any(raw.get(f) not in (None,0) for f in ('skillparam0','skillparam4','skillparam5','skillparam7','skillparam8','skillparam9'))):
        return
    for field in fields:
        a=_source_answer(edge['item'],'bossskill',13,field,parent,'味方全体（原文对象；记录选择未实机核实）')
        if a is None:continue
        raw_value=raw[field]
        values={
            'skillparam1':f'全体友方这项攻击加成输入{raw_value:g}，随Chain变化（推断）。',
            'skillparam2':f'全体友方这项固定防御按各接受者当前普通攻击基值的{raw_value:g}倍、再乘Chain系数计算（推断）；不是固定比例减伤。',
            'skillparam6':f'全体友方这项移动速度加成输入{raw_value:g}，随Chain变化（推断）。',
            'skillparam3':f'这组全体友方加成持续{raw_value:g}游戏秒（推断）。'}
        a.update(value=values[field],
            note='完整正文只有一组该对象的限时增益；实际父链只有一个type13，攻/防/移/时间槽与主张并集相等。敌方减益来自不同对象，不分配到本答案。对象与句内归属为推断，运行时选档未验证。')
        a['remaining_ab_binding'].update(slot=edge['slot'],child_id=edge['child_id'],
            text_row_id=row['row_id'],source_position=deepcopy(row['source_position']),
            object_ja='味方全体',claimed_fields=list(fields))
        _append(row,a,report,'ally_t13')


def _damage(data,cid,skill,row,chara,patterns,report,tail=False):
    text=row.get('japanese','')
    if tail and cid in {30252,30255,30306} and skill.get('table')!='charainfo':
        return
    # Only the first, header-bearing enemy attack is admitted in this batch.
    if (row.get('fragment_index')!=0 or not Y.HEADER_RE.match(text)
            or '敵' not in text.split('ダメージ')[0] or 'ダメージ' not in text):
        return
    selected=_selected(data,cid,skill,row,chara,patterns,
                       interior_mirror=tail and cid in {30252,30255,30306})
    if len(selected)!=1:
        report['rejections'].append(dict(row_id=row['row_id'],reason='DAMAGE_FULL_BODY_TEN_SLOT_MISMATCH'))
        return
    parent=selected[0];edges=parent['edges'];body=parent['item']['raw']['sinfo']
    if tail:
        typ=51 if cid==30104 else 114 if cid in {30252,30255,30306} else 103
        carriers=[e for e in edges if e['type']==typ]
        if typ==103:
            report['rejections'].append(dict(row_id=row['row_id'],reason='TYPE103_AIRAREASTRIKE_UPDATE_DAMAGE_SLOT_UNRESOLVED'))
            return
        # Do not use a neighbouring familiar attack type for a periodic/dash clause.
        if (len(carriers)!=1 or (typ==51 and '小ダメージを一定間隔ごとに与え' not in text)
                or (typ==114 and not re.search(r'ダッシュ範囲上.*\d+回ダメージを与え',text))):
            return
        edge=carriers[0];field='skillparam0' if typ==51 else 'skillparam1'
        evidence=_tail_evidence(data,typ,field)
        if evidence is None:
            report['rejections'].append(dict(row_id=row['row_id'],reason='TAIL_CONCRETE_LOCAL_EVIDENCE_MISSING'))
            return
    else:
        carriers=[e for e in edges if e['type'] in (3,22)]
        if not carriers or carriers[0] is not edges[0]:
            return
        if len(carriers)>1:
            # Complete ordered pair, not a first-match numeric guess (30321).
            phrases=re.findall(r'[^。]*ダメージを与え[^。]*。',body)
            if (len(carriers)!=2 or carriers!=edges[:2] or len(phrases)!=2
                    or 'その後、' not in phrases[1] or not phrases[0].endswith(text)
                    or any(re.search(r'\d+回',p) or '敵' not in p for p in phrases)):
                report['rejections'].append(dict(row_id=row['row_id'],reason='DAMAGE_ORDERED_PAIR_NOT_PROVEN'))
                return
        edge=carriers[0];field='skillparam1';typ=edge['type']
    raw=edge['record']
    if not A.finite(raw.get(field)) or raw[field]<0:
        return
    a=_source_answer(edge['item'],'bossskill',typ,field,parent,'敌')
    if a is None:
        report['rejections'].append(dict(row_id=row['row_id'],reason='DAMAGE_LOCAL_RULE_MISSING',type=typ,field=field))
        return
    if any(v.get('rule_key')==a['rule_key'] and v.get('record_id')==a['record_id'] for v in row['answers']):
        return
    a.update(quantity_kind='单次对敌伤害输入倍率',
        value=f"这段攻击按技能基础攻击力的{raw[field]:g}倍计算（推断）；该基础已含Chain，不是面板攻击力，实际扣血仍待核实。",
        base_definition='B=getBasicSkillAttack(true)，已含Chain；不再次乘Chain。',
        note='仅局部伤害输入；最终扣血、保证命中次数及实际选档未验证。'
             '描述归属由本角色实际父边、完整正文和有序对象句核对；不能借同数值或同句跨父拼接。')
    a['remaining_ab_binding'].update(slot=edge['slot'],child_id=edge['child_id'],
        text_row_id=row['row_id'],source_position=deepcopy(row['source_position']),object_ja='敵')
    if tail:
        a['reused_local_formula_evidence']=evidence
    _append(row,a,report,'tail_damage' if tail else 'known_damage')


def _tail_evidence(data,typ,field):
    """Only reuse concrete P2-10 results, never infer proof from a shell's status."""
    if not hasattr(data,'_remaining_ab_tail_evidence'):
        data._remaining_ab_tail_evidence={}
    cache=data._remaining_ab_tail_evidence
    if typ in cache:return deepcopy(cache[typ])
    base=Path(data.root)/'output/character_skills/boss_heal_types'
    if not all((base/name).is_file() for name in ('type_rules.json','native_checks.json')):
        return None
    rules=R.load_json(base/'type_rules.json');checks=R.load_json(base/'native_checks.json')
    local=rules.get('types',{}).get(str(typ),{})
    names=('damage_function_found','basic_skill_attack_times_slot_then_integerise',
           'slot_resolved','slot_matches_the_hand_read_expectation',
           'getBasicSkillAttack_argument_is_the_expected_variant','consumer_located')
    df=local.get('damage_function') or {};slot=(local.get('slots') or {}).get('atk_rate') or {}
    checks_key='checks' if 'checks' in checks else 'results'
    controlled=checks.get(checks_key,[])
    valid=(slot.get('slot')==int(field.removeprefix('skillparam'))
           and slot.get('load_rva')==df.get('fmul_rva') and df.get('trunc_rva')
           and df.get('w1_to_getBasicSkillAttack')==1 and df.get('consumers')
           and all(any(c.get('name')==name and c.get('ok') is True for c in local.get('checks',[])) for name in names)
           and all(any(c.get('name')==f'g{typ}.{name}' and c.get('ok') is True for c in controlled) for name in names))
    if not valid:return None
    cache[typ]=dict(type=typ,field='/'+field,
        type_rules='output/character_skills/boss_heal_types/type_rules.json',
        native_checks='output/character_skills/boss_heal_types/native_checks.json',
        json_pointer=f'/types/{typ}/damage_function',damage_function=deepcopy(df),
        controlled_checks=[f'g{typ}.{name}' for name in names],
        original_rule_status=None,proof='既有局部乘法/整数化/消费者检查；没有新原生调用')
    return deepcopy(cache[typ])


def _heal(data,cid,skill,row,chara,patterns,report):
    if not HEAL.fullmatch(row.get('japanese','')):
        return
    selected=_selected(data,cid,skill,row,chara,patterns)
    if len(selected)!=1:
        report['rejections'].append(dict(row_id=row['row_id'],reason='HEAL_FULL_SOURCE_GATE'))
        return
    parent=selected[0];carriers=[e for e in parent['edges'] if e['type']==27]
    if len(carriers)!=1 or carriers[0] is not parent['edges'][0]:
        return
    edge=carriers[0];raw=edge['record']
    if any(not A.finite(raw.get(f)) or raw[f]<=0 for f in ('skillparam1','skillparam2','skillparam3')):
        return
    a=_source_answer(edge['item'],'bossskill',27,'skillparam1',parent,'味方全体（原文）')
    if a is None:return
    a.update(quantity_kind='单次回复输入倍率',
        value=f"全体友方每次回复按技能基础攻击力的{raw['skillparam1']:g}倍计算（推断）；该基础已含Chain，不是面板攻击力或最大HP百分比。",
        base_definition='B=getBasicSkillAttack(true)，已含Chain；不是最大HP百分比。',
        note=f"回复间隔配置{raw['skillparam2']:g}游戏秒，次数配置{int(raw['skillparam3'])}次（向零截断）；初始化计时为0，更新可立即触发，一次更新最多一次。"
             '不把间隔当总时长，不乘次数伪造总回复。原文对象和超上限陈述保留，实际选择与最终HP未验证。',
        supporting_fields=[dict(field_path='/'+f,raw_value=raw[f]) for f in ('skillparam2','skillparam3')])
    a['remaining_ab_binding'].update(slot=edge['slot'],child_id=edge['child_id'],
        text_row_id=row['row_id'],source_position=deepcopy(row['source_position']),object_ja='味方全体')
    word=re.search('回復',unicodedata.normalize('NFKC',row['japanese']))
    a['yg1_heal_claim']=dict(scope=SCOPE,row_id=row['row_id'],effect_type='回復（词表外）',
                            span=[word.start(),word.end()],pattern_id=parent['entry']['reference_id'])
    # Held for host/user decision. The unchanged ledger does not consume this claim.
    # Default application leaves these nine rows byte-for-byte unchanged.
    report['pending_heal_answers'].append(dict(row_id=row['row_id'],answer=a,
        reason='现有账本HP回復与本句回復（词表外）不匹配；仅提案，不默认写入行'))


def apply_to_groups(data,cid,groups):
    report=dict(scope=SCOPE,cid=cid,answers_added=0,additions=[],rejections=[],pending_heal_answers=[])
    if cid not in ADMITTED_CIDS or 'Y.G.' not in str((data.profiles.get(cid) or {}).get('title') or ''):
        return report
    graph=_graph(data,cid)
    if graph is None:
        report['rejections'].append(dict(reason='CURRENT_GRAPH_SOURCE_MISMATCH'))
        return report
    chara,patterns=graph
    row_ids=[r['row_id'] for g in groups for s in g.get('skills',[]) for r in s.get('rows',[])]
    if len(set(row_ids))!=len(row_ids):
        report['rejections'].append(dict(reason='DUPLICATE_ROW_ID'))
        return report
    for group in groups:
        if group.get('group')!='special_move':
            continue
        for skill in group.get('skills',[]):
            for row in skill.get('rows',[]):
                if cid in DURATION_CIDS or (cid in MIRROR_CIDS and skill.get('table')=='charainfo'):
                    _speed(data,cid,skill,row,chara,patterns,report)
                if cid in BUFF_CIDS:
                    _buff(data,cid,skill,row,chara,patterns,report)
                if cid in DAMAGE_CIDS:
                    _damage(data,cid,skill,row,chara,patterns,report)
                if cid in TAIL_CIDS:
                    _damage(data,cid,skill,row,chara,patterns,report,tail=True)
                if cid in HEAL_CIDS:
                    _heal(data,cid,skill,row,chara,patterns,report)
    return report
