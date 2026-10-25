"""Second batch: source-qualified StopUp, with explicit runtime limits."""
import copy
import re
import card_page_inference_attack_interval as A
import card_page_inference_yg1 as Y

SCOPE='ATTACK_INTERVAL_BATCH2_LOCAL_FORMULA_ONLY'
REPORT='output/character_skills/attack_interval_batch2_20261025/native/native_checks.json'
ORDINARY={350:(40035000,40035003),4316:(40431600,40431604),
          30205:(43020500,43020503),30223:(43022300,43022303),
          30308:(43030800,43030803),30337:(43033700,43033703)}


def _row_on_root(skill,row,root,field='text',ident=None,display_source=None):
    source=root['source'];raw=root['raw']
    if ident is None:ident=raw['skillid']
    if (skill.get('layer')!='CACHE' or skill.get('record_id')!=ident
            or skill.get('text_field')!=field):
        return False
    for candidate in (skill.get('source') or {},row.get('source') or {}):
        expected=source if display_source is None else display_source
        keys=(('layer','record_key','source_key','source_sha256','json_pointer',
               'byte_begin','byte_end_exclusive','raw_record_sha256') if display_source is None
              else ('layer','record_key','source_key','json_pointer','original_file','source_resolution'))
        if any(expected.get(k) is None or candidate.get(k)!=expected[k] for k in keys):
            return False
    row_source=row['source'];position=row.get('source_position') or {}
    pointer=source['json_pointer']+'/'+field
    span=position.get('raw_span')
    return (row_source.get('field')=='/'+field and row_source.get('field_json_pointer')==pointer
            and position.get('field_pointer')==pointer and position.get('source_key')==source['source_key']
            and isinstance(span,list) and len(span)==2
            and all(isinstance(x,int) and not isinstance(x,bool) for x in span)
            and 0<=span[0]<span[1]<=len(raw.get(field,''))
            and raw[field][span[0]:span[1]]==row.get('japanese'))


def _ordinary(data,cid,groups):
    if 'Y.G.' not in str((data.profiles.get(cid) or {}).get('title') or ''):
        return
    if cid not in ORDINARY:
        return
    root_id,carrier_id=ORDINARY[cid]
    chara=A.node(data,'charainfo',cid)
    if chara is None or chara['raw'] != data.cache_chara.get(cid):
        return
    slots=chara['raw'].get('skillid')
    if not isinstance(slots,list) or len(slots)<2 or slots[1]!=root_id:
        return
    linked=[e for g in data.links[cid]['groups'] if g['group']=='ability'
            for e in g.get('records',[]) if e.get('reference_field')=='skillid[1]'
            and e.get('table')=='skilllist' and e.get('layer')=='CACHE']
    root=A.node(data,'skilllist',root_id)
    if len(linked)!=1 or root is None or linked[0].get('record')!=root['raw'] or linked[0].get('reference_id')!=root_id:
        return
    tree=A.ordinary_tree(data,root_id)
    if tree is None:
        return
    carriers=[(it,path) for it,path in tree if it['raw'].get('ability')==1016]
    if len(carriers)!=1 or carriers[0][0]['raw'].get('skillid')!=carrier_id:
        return
    item,path=carriers[0];raw=item['raw']
    eligible=[(s,r) for g in groups if g.get('group')=='ability'
              for s in g.get('skills',[]) if s.get('reference_field')=='skillid[1]'
              and s.get('table')=='skilllist' for r in s.get('rows',[])
              if r.get('japanese')=='攻撃間隔が早くなる。']
    if len(eligible)!=1:
        return
    skill,row=eligible[0]
    if not _row_on_root(skill,row,root) or root['raw'].get('text','').count(row['japanese'])!=1:
        return
    if row.get('attack_interval'):
        return
    conditions=('仅回答停止后的额外增强；原句无条件基础间隔仍未知。能力持有者自身；'
                '每param1=1.5传入delta累计单位一档（调用端时间单位尚未核实），'
                f'param0={raw.get("param0")}限制最大档数；移动超过原生位置容差时计时清零。'
                '根装载分派与实际解锁未验证，依据真实角色槽→普通sub及停止增强文本推断归属；'
                '其他能力中性，非最终动画周期。上下文='+row.get('context_text',''))
    A._attach(row,item,'param6',{'charainfo_slot':'skillid[1]','ordinary_sub_path':path},
              conditions,scope=SCOPE,target='自身',report=REPORT)
    if row.get('attack_interval',{}).get('scope')!=SCOPE:
        return
    answer=row['answers'][-1]
    row['attack_interval']['contribution_only']=True
    row['attack_interval']['remaining_claim']='无条件基础攻击间隔与描述绑定尚未解释；停止增强不是基础值'
    answer['value']='仅停止增强：'+answer['value']+'；无条件基础攻击间隔仍未解'
    answer['supporting_fields']=[{**copy.deepcopy(item['source']),'table':'skilllist',
        'record_id':carrier_id,'field_path':'/'+field,'raw_value':raw[field]}
        for field in ('param0','param1')]
    answer['stopup_configuration']={'max_count':raw['param0'],'interval_input_delta_units':raw['param1'],
        'per_count_interval_delta':raw['param6'],'installation':'INFERRED_NOT_EXECUTED'}


MIRRORS={30002,30101,30108,30112,30202,30218,30221,30228,30229,30238,
         30239,30241,30243,30245,30254,30255,30301,30306,30312,30318,30324,30325,30336}
CHAIN_CIDS={30108,30241,30312,30324,30325}


def _canonical(text):
    return re.sub(r'\s+','',str(text or '').replace('\\n','\n'))


def _patterns(data,cid):
    chara=A.node(data,'charainfo',cid)
    if chara is None or chara['raw']!=data.cache_chara.get(cid):return None
    entries=[e for g in data.links[cid]['groups'] if g['group']=='special_move'
             for e in g.get('records',[]) if e.get('table')=='bosspattern' and e.get('layer')=='CACHE']
    expected={k:v for k,v in chara['raw'].items() if re.fullmatch(r'pattern\d+',k) and v}
    if (any(not isinstance(v,int) or isinstance(v,bool) for v in expected.values())
            or len(set(expected.values()))!=len(expected)):
        return None
    if len(entries)!=len(expected):return None
    result={}
    for e in entries:
        ref=e.get('reference_field');pid=e.get('reference_id')
        node=A.node(data,'bosspattern',pid)
        if (ref in result or expected.get(ref)!=pid or node is None or node['raw']!=e.get('record')):return None
        result[ref]=(e,node)
    return chara,result


def _one_self_carrier(data,entry):
    carriers=A.pattern_carriers(data,entry)
    if len(carriers)!=1:return None
    c=carriers[0];r=c['item']['raw']
    if (not A.finite(r.get('param6')) or r['param6']>=0 or not A.finite(r.get('param0'))
            or r['param0']<=0 or r.get('flag')!=0 or r.get('iParam0',0)!=0
            or r.get('param8')!=64 or not A.finite(r.get('param7')) or int(r['param7'])!=1):return None
    return c


def _companion(patterns,base,text):
    if base[0].get('reference_field')!='pattern0' or 'pattern1' not in patterns:return None
    cp=patterns['pattern1'];n=base[1]['raw'];c=cp[1]['raw']
    threshold=re.search(r'(\d+)(?:st|nd|rd)Chain以上',text)
    if (threshold is None or n.get('che')!=int(threshold[1]) or c.get('sinfo')
            or n.get('flag')!=8192 or c.get('flag')!=8192
            or c.get('chs')!=n['che']+1 or c.get('che')!=5):return None
    return cp


def _self_phrase(text):
    return bool(re.search(r'自身の攻撃(?:力と攻撃)?(?:速度|間隔)',text)
                and re.search(r'上が|早く|速く',text) and len(A.WORD.findall(text))==1)


def _attach_temporary(row,candidates,path):
    # Same-value branches may share one displayed answer only with every source disclosed.
    signature=lambda c:tuple(c['item']['raw'].get(k) for k in ('param0','param6','param7','param8','flag','iParam0'))
    if not candidates or len({signature(c) for c in candidates})!=1:return
    c=candidates[0];raw=c['item']['raw']
    conditions=('句面自身对象（含攻撃力と攻撃速度的共用对象）；实际CACHE父边与各pattern条件见binding；'
                '2012 param8=64(MYSELF)、param7=1、flag=0、职业筛选缺失/0；'
                '仅该间隔贡献。Chain条件按正文和原始chs/che配置推断，未验证运行时选择；'
                '不补法力、命中数或其他效果。上下文='+row.get('context_text',''))
    A._attach(row,c['item'],'param6',path,conditions,raw['param0'],scope=SCOPE,target='自身',
              report='output/character_skills/attack_interval_batch2_20261025/review/REVIEW_CANDIDATE.md')
    if row.get('attack_interval',{}).get('scope')!=SCOPE:return
    row['answers'][-1]['all_pattern_sources']=[{'source':copy.deepcopy(x['item']['source']),
       'raw':copy.deepcopy(x['item']['raw']),'path':copy.deepcopy(x['path'])} for x in candidates]


def _temporary(data,cid,groups):
    if cid not in MIRRORS:return
    graph=_patterns(data,cid)
    if graph is None:return
    chara,patterns=graph
    skills=[s for g in groups if g.get('group')=='special_move' for s in g.get('skills',[])]
    if cid in CHAIN_CIDS:
        for skill in skills:
            base=patterns.get(skill.get('reference_field'))
            if skill.get('table')!='bosspattern' or base is None:continue
            for row in skill.get('rows',[]):
                if row.get('attack_interval') or not _self_phrase(row.get('japanese','')):continue
                display_source=data.precise_source(base[0])
                if display_source.get('source_resolution')!=Y.EXACT:continue
                if not _row_on_root(skill,row,base[1],'sinfo',base[0]['reference_id'],display_source):continue
                companion=_companion(patterns,base,row['japanese'])
                if companion is None:continue
                carrier=_one_self_carrier(data,companion[0])
                if carrier is None:continue
                _attach_temporary(row,[carrier],{'description_pattern':base[0]['reference_id'],
                    'configured_companion':companion[0]['reference_id'],'carrier_path':carrier['path'],
                    'conditions':{k:companion[1]['raw'].get(k) for k in Y.CONDITION_KEYS}})
    for skill in skills:
        if skill.get('table')!='charainfo' or skill.get('reference_field')!='skilltext':continue
        if _canonical(skill.get('original_text'))!=_canonical(chara['raw'].get('skilltext')):continue
        # Reuse the established full-body + head-slot equivalence gate, not a same-clause guess.
        bases=[]
        for ref,base in patterns.items():
            if _canonical(base[1]['raw'].get('sinfo'))!=_canonical(chara['raw'].get('skilltext')):continue
            first=A.node(data,'bossskill',base[1]['raw'].get('skillid0'))
            if first is not None and Y._same_slots(chara['raw'],first['raw']):bases.append(base)
        if not bases:continue
        for row in skill.get('rows',[]):
            if row.get('attack_interval') or not _self_phrase(row.get('japanese','')):continue
            if not _row_on_root(skill,row,chara,'skilltext',cid):continue
            candidates=[];paths=[];valid=True
            for base in bases:
                pattern=base[1]['raw'];selected=base
                if re.search(r'\d+(?:st|nd|rd)Chain以上',row['japanese']):
                    selected=_companion(patterns,base,row['japanese'])
                    if selected is None:valid=False;break
                carrier=_one_self_carrier(data,selected[0])
                if carrier is None:valid=False;break
                candidates.append(carrier);paths.append({'description_pattern':base[0]['reference_id'],
                    'configured_pattern':selected[0]['reference_id'],'carrier_path':carrier['path'],
                    'conditions':{k:selected[1]['raw'].get(k) for k in Y.CONDITION_KEYS}})
            if valid:_attach_temporary(row,candidates,{'mirror':'charainfo.skilltext full-body/head-slot equivalence',
                'all_matching_pattern_branches':paths,'branch_count':len(bases)})


def apply_to_groups(data,cid,groups):
    if 'Y.G.' not in str((data.profiles.get(cid) or {}).get('title') or ''):return
    _ordinary(data,cid,groups)
    _temporary(data,cid,groups)
