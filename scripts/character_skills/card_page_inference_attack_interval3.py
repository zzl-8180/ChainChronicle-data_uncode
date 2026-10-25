"""Source-limited Position and ManaCycle cadence, never a base-speed substitute."""
import copy
import re
import rules as R
import card_page_inference_attack_interval as A
import card_page_inference_attack_interval2 as B
import card_page_inference_yg1 as Y

SCOPE='ATTACK_INTERVAL_BATCH3_LOCAL_FORMULA_ONLY'
REPORT='output/character_skills/attack_interval_batch3_20261025/native/native_checks.json'
POSITION={30220:(1,43022000,43022002),30307:(2,43030705,43030707)}
SYMPATHY={7251:40725110,30315:43031510,30338:43033808}


def _unique_target(groups,skill,row):
    rows=[(s,r) for g in groups for s in g.get('skills',[]) for r in s.get('rows',[])]
    if sum(r.get('row_id')==row.get('row_id') for s,r in rows)!=1:return False
    return sum(s.get('table')==skill.get('table') and s.get('record_id')==skill.get('record_id')
        and s.get('reference_field')==skill.get('reference_field')
        and r.get('source_position')==row.get('source_position') for s,r in rows)==1


def _attach(row,item,table,typ,field,path,conditions,partial=False):
    if row.get('attack_interval'):return
    raw=item['raw'];a=R.answer_for(table,typ,'/'+field,raw[field],raw,source_layer='CACHE')
    if a is None:return
    source={**copy.deepcopy(item['source']),'table':table,'record_id':raw['skillid'],'field_path':'/'+field}
    a.update(value=a['value_text'],rule_key=f'{table}|{typ}|/{field}',table=table,
        record_id=raw['skillid'],layer='CACHE',source=source,target='自身',conditions=conditions,
        numeric_evidence='推断',association_evidence='推断',evidence_scope=SCOPE,
        rule_body_status='已确认（字段与局部计算）',rule_status='描述对应关系为推断',
        numeric_source='真实CACHE记录和有界原生局部公式',evidence=[REPORT],
        binding={'scope':SCOPE,'path':path},
        note='字段与局部计算有代码依据；描述和条件对应关系为推断，实际装载与最终每击周期未验证。'+conditions)
    if partial:a['value']='仅敌阵额外加成：'+a['value']+'基础攻击间隔仍未确定。'
    index=len(row['answers']);row['answers'].append(a);A._binding(row,index,a,source,SCOPE)
    row['attack_interval']['path']=path
    if partial:
        row['attack_interval'].update(contribution_only=True,remaining_claim='基础攻击间隔仍未确定，敌阵额外加成不代替基础值')
    if row['row_class']=='C':
        row.update(row_class='A',evidence='推断',evidence_label='推断（条件攻击间隔）')
    for key in ('numeric_evidence','association_evidence'):
        if row.get(key)!='确认':row[key]='推断'
    row['evidence_scope']=list(dict.fromkeys(row.get('evidence_scope',[])+[SCOPE]));row['partial']=True
    row['unknown_reasons']=list(dict.fromkeys(row.get('unknown_reasons',[])+['已列出的间隔加成以外，尚未确定的效果和最终每击周期继续保留。']))


def _position(data,cid,groups):
    if cid not in POSITION:return
    slot,rid,sid=POSITION[cid];ch=A.node(data,'charainfo',cid);root=A.node(data,'skilllist',rid)
    if ch is None or root is None or ch['raw']!=data.cache_chara.get(cid):return
    slots=ch['raw'].get('skillid')
    if not isinstance(slots,list) or len(slots)<=slot or slots[slot]!=rid:return
    entries=[e for g in data.links[cid]['groups'] if g['group']=='ability' for e in g.get('records',[])
        if e.get('reference_field')==f'skillid[{slot}]' and e.get('table')=='skilllist' and e.get('layer')=='CACHE']
    if len(entries)!=1 or entries[0].get('reference_id')!=rid or entries[0].get('record')!=root['raw']:return
    tree=A.ordinary_tree(data,rid)
    if tree is None:return
    found=[(n,p) for n,p in tree if n['raw'].get('ability')==56 and 'param9' in n['raw']]
    if len(found)!=1 or found[0][0]['raw'].get('skillid')!=sid:return
    item,path=found[0]
    for g in groups:
        if g.get('group')!='ability':continue
        for skill in g['skills']:
            if skill.get('table')!='skilllist' or skill.get('record_id')!=rid or skill.get('reference_field')!=f'skillid[{slot}]':continue
            for row in skill['rows']:
                if not B._row_on_root(skill,row,root) or not _unique_target(groups,skill,row):continue
                start,end=row['source_position']['raw_span'];text=root['raw']['text']
                if cid==30307:
                    if row['japanese']!='自身の場合、さらに攻撃間隔が早くなる。':continue
                    if not re.search(r'敵陣にいる味方[^。]*。$',text[:start]):continue
                else:
                    if row['japanese']!='攻撃間隔が早くなる。' or not text[end:].startswith('敵陣にいると効果が上がる。'):continue
                _attach(row,item,'skilllist',56,'param9',{'ordinary_sub_path':path,'root':rid,'position_param0':item['raw'].get('param0')},
                    '自身在敌阵时的额外加速。原文与位置条件记录的对应关系为推断，尚未实机确认位置资格和实际生效。',partial=cid==30220)


def _boss_carrier(data,parent):
    found=[]
    for i in range(10):
        ident=parent['raw'].get('skillid'+str(i))
        if not ident:continue
        if i>6:return None
        node=A.node(data,'bossskill',ident)
        if node is None:return None
        raw=node['raw'];typ=raw.get('skillid0')
        if typ in (68,118) and 'skillparam9' in raw:
            found.append((node,{'pattern_id':parent['raw']['patternid'],'slot':'skillid'+str(i),'boss_id':ident}))
    return found[0] if len(found)==1 else None


def _boss_answer(row,carrier,path):
    if row.get('attack_interval'):return
    item,carrier_path=carrier;raw=item['raw']
    chain=re.search(r'(\d+)(?:st|nd|rd)Chain以上',row['japanese'])
    trigger=(f'Chain达到{chain[1]}以上时追加的自身加速。' if chain else '必杀后续阶段的自身加速。')
    if 'sympathy_id' in path:
        trigger=(f'Chain达到{chain[1]}以上，任一友方（含自身）发动共鸣必杀时触发的自身加速。' if chain else '原文触发事件对应的自身加速，触发档位待确认。')
        trigger+='本人正在释放必杀时不触发；同一Chain最多触发一次。'
    refund=('原文所述命中50次后的返还效果仍未解析。' if '50回' in row['japanese'] else '原文所述返还效果仍未解析。')
    _attach(row,item,'bossskill',raw['skillid0'],'skillparam9',{**path,'carrier_path':carrier_path},
        trigger+'条件与分支对应关系为推断，尚未验证实际选档和生效。计时阈值为30游戏秒，是否等同完整加速时长尚未确认。'+refund)
    if row.get('attack_interval',{}).get('scope')==SCOPE:
        row['answers'][-1]['supporting_fields']=[{**copy.deepcopy(item['source']),'table':'bossskill',
            'record_id':raw['skillid'],'field_path':'/skillparam4','raw_value':raw.get('skillparam4')}]


def _boss(data,cid,groups):
    if cid==30301:
        graph=B._patterns(data,cid)
        if graph is None:return
        chara,patterns=graph
        for g in groups:
            if g.get('group')!='special_move':continue
            for skill in g['skills']:
                bases=[]
                if skill.get('table')=='bosspattern':
                    base=patterns.get(skill.get('reference_field'))
                    if base is not None:bases=[base]
                elif skill.get('table')=='charainfo' and skill.get('reference_field')=='skilltext':
                    if B._canonical(skill.get('original_text'))!=B._canonical(chara['raw'].get('skilltext')):continue
                    for base in patterns.values():
                        if B._canonical(base[1]['raw'].get('sinfo'))!=B._canonical(chara['raw'].get('skilltext')):continue
                        head=A.node(data,'bossskill',base[1]['raw'].get('skillid0'))
                        if head and Y._same_slots(chara['raw'],head['raw']):bases.append(base)
                if len(bases)!=1:continue
                base=bases[0]
                for row in skill['rows']:
                    if not B._self_phrase(row.get('japanese','')) or not _unique_target(groups,skill,row):continue
                    if skill['table']=='bosspattern':
                        ds=data.precise_source(base[0])
                        if ds.get('source_resolution')!=Y.EXACT or not B._row_on_root(skill,row,base[1],'sinfo',base[0]['reference_id'],ds):continue
                    elif not B._row_on_root(skill,row,chara,'skilltext',cid):continue
                    selected=base
                    if re.search(r'\d+(?:st|nd|rd)Chain以上',row['japanese']):
                        selected=B._companion(patterns,base,row['japanese'])
                        if selected is None:continue
                    carrier=_boss_carrier(data,selected[1])
                    if carrier is not None:_boss_answer(row,carrier,{'description_pattern':base[0]['reference_id'],
                        'configured_pattern':selected[0]['reference_id'],'conditions':{k:selected[1]['raw'].get(k) for k in Y.CONDITION_KEYS}})
    elif cid in SYMPATHY:
        info=A.node(data,'sympathy_skilllist',cid)
        if info is None:return
        entries=[e for g in data.links[cid]['groups'] if g['group']=='sympathy' for e in g.get('records',[])
            if e.get('table')=='skilllist' and e.get('layer')=='CACHE' and e.get('reference_field')==f'sympathy_skill_info[_id={cid}].ability0']
        if len(entries)!=1:return
        entry=entries[0];rid=entry['reference_id'];root=A.node(data,'skilllist',rid)
        if info['raw'].get('ability0')!=rid or root is None or root['raw']!=entry.get('record') or root['raw'].get('ability')!=3005:return
        if not all(t in root['raw'].get('text','') for t in ('自身が必殺技発動中に条件を満たした場合は発動しない','同じChain内で1回しか発動しない')):return
        pointer=root['raw'].get('str0')
        if not isinstance(pointer,str) or not re.fullmatch(r'\d+',pointer):return
        parent=A.node(data,'bosspattern',int(pointer))
        if parent is None:return
        carrier=_boss_carrier(data,parent)
        if carrier is None or carrier[0]['raw']['skillid']!=SYMPATHY[cid]:return
        for g in groups:
            if g.get('group')!='sympathy':continue
            for skill in g['skills']:
                if skill.get('table')!='skilllist' or skill.get('reference_field')!=entry['reference_field']:continue
                for row in skill['rows']:
                    if B._self_phrase(row.get('japanese','')) and B._row_on_root(skill,row,root) and _unique_target(groups,skill,row):
                        _boss_answer(row,carrier,{'sympathy_id':cid,'ordinary_root':rid,'str0_pattern':int(pointer),
                            'trigger_raw':copy.deepcopy(root['raw'])})


def apply_to_groups(data,cid,groups):
    if 'Y.G.' not in str((data.profiles.get(cid) or {}).get('title') or ''):return
    _position(data,cid,groups);_boss(data,cid,groups)
