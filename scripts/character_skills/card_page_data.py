"""Conservative sample-page data projection over existing unpacked artifacts."""
from __future__ import annotations
import collections
import copy
import hashlib
import json
import math
import os
import re
import unicodedata
from pathlib import Path

import common as C
import rules as R
from card_page_policy import metrics,INFERENCE_STATUS
from card_page_basic import apply_basic_display
from card_page_positions import fragment_positions,position_identity

SAMPLES = (30236,7229,29,2020,5023,4009,8151,30004,10001,13001,30338)
GROUPS = [('special_move','必杀技'),('ability','能力'),('sa','SA'),('sympathy','共鸣'),
          ('leader','Leader'),('class','Class'),('extra','Extra'),('passive','PASSIVE'),
          ('bond','羁绊'),('heroic','英雄技'),('denju','传授'),('crossworld','CrossWorld'),('slot0','必杀效果类型')]
TEXT = {'charainfo':('skilltext','skillname'),'bosspattern':('sinfo','sname'),
        'denju':('stext','sname'),'denju_limit_break_info':('stext','sname')}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def lines(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line in stream:
            yield json.loads(line)


def clean(text):
    return str(text or '').replace('\\n','\n')


def fragments(text):
    """Sentence units preserve repeated occurrences and all skill prose; flavor stays separate."""
    text=clean(text)
    cut=text.find('[i][c]')
    body=text[:cut] if cut>=0 else text
    return [s.strip(' ◆\r\t') for s in re.split(r'(?<=。)|\n|◆',body) if s.strip(' ◆\r\t')]


def canonical(text):
    return clean(text).strip().rstrip('。').strip()


def raw_state(rec, key):
    return 'missing' if key not in rec else 'null' if rec[key] is None else 'zero' if rec[key]==0 else 'present'


NUMBER = r'(?<![\d.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
NUM_UNITS = re.compile('('+NUMBER+r')\s*(%|秒間|秒|回|発|つ|個|枚|体|倍|人|マナ)(?![a-zA-Z])')


def original_numbers(text):
    """Extract only explicit quantities; ordinal 1st/IDs/level names do not qualify."""
    normalized=unicodedata.normalize('NFKC',text)
    out=[]
    for match in NUM_UNITS.finditer(normalized):
        value,unit=match.group(1),match.group(2)
        left=normalized[max(0,match.start()-14):match.start()]
        right=normalized[match.end():match.end()+14]
        role=('条件阈值' if re.match(r'(以上|以下|未満|を超え)',right) else
              '时长' if unit.startswith('秒') else '次数' if unit in ('回','発') else
              '效果量百分比' if unit=='%' else '倍数' if unit=='倍' else '数量')
        if right.startswith('まで') and unit in ('回','発','人'):role=('人数上限' if unit=='人' else '次数上限')
        if unit=='%' and re.search(r'HP(?:が|の)?$',left) and re.match(r'(以上|以下|未満|より)',right):
            role='HP条件阈值'
        out.append(dict(value=value,unit=unit,role=role,literal=match.group(),
                        context=normalized[max(0,match.start()-20):match.end()+24],
                        normalized_span=[match.start(),match.end()]))
    # Fixed HP/ATK amounts often have no unit suffix (HPが1000上がり).
    for match in re.finditer(r'(HP|ATK)(?:が|を|の)?('+NUMBER+r')(?=上|増|回復|減)',normalized):
        if any(a['normalized_span'][0]<=match.start(2)<a['normalized_span'][1] for a in out): continue
        out.append(dict(value=match.group(2),unit=match.group(1)+'原文固定量',role='效果固定量',
                        literal=match.group(),context=normalized[max(0,match.start()-15):match.end()+20],
                        normalized_span=[match.start(),match.end()]))
    return out


def quantitative(value):
    value=re.sub(r'0x[0-9a-fA-F]+','',str(value))
    return bool(re.search(r'[0-9０-９]|×|\bB(?:_set)?\b',value))


def walk_entries(entry):
    yield entry
    for key in ('skill_refs','sympathy_skill_refs','boss_skill_refs','sa_ability_refs','sub_effects'):
        for child in entry.get(key,[]):
            if isinstance(child,dict): yield from walk_entries(child)


class Inputs:
    def __init__(self,root:Path,cids):
        self.root=root.resolve(); self.base=self.root/'output/character_skills'; self.cids=set(cids)
        self.links={r['cid']:r for r in lines(self.base/'links/character_skills.jsonl') if r['cid'] in self.cids}
        self.profiles={r['cid']:r for r in lines(self.base/'profiles/profiles.jsonl') if r['cid'] in self.cids}
        if set(self.links)!=self.cids or set(self.profiles)!=self.cids:
            raise ValueError('Requested cid missing from declared links/profiles inputs')
        keys={e['rec_key'] for p in self.profiles.values() for g in p['groups'] for e in g['records']}
        self.old={r['rec_key']:r for r in lines(self.base/'profiles/records.jsonl') if r['rec_key'] in keys}
        self.rule_metadata=read(self.base/'profiles/rules.json')
        self.decoded=self.root/'output/cache_full_20261015_v3/decoded'
        self.apk=self.root/'output/base_master'
        self.cache_chara={r['cid']:r for r in read(self.decoded/'charainfo.data5.json.raw')['charainfo']}
        self.apk_chara={r['cid']:r for r in read(self.apk/'_mdCharacter.json')['charainfo']}
        self.cache_skill={r['skillid']:(i,r) for i,r in enumerate(read(self.decoded/'skilllist.data5.json.raw')['skilllist'])}
        self.apk_skill={r['skillid']:(i,r) for i,r in enumerate(read(self.apk/'_mdSkill.json')['skilllist'])}
        self.baseline=read(self.root/'output/card_comparison_cid30236/description_effects.json') if 30236 in self.cids else []
        self.forward=read(self.base/'type1082/native_checks.json')['verdict']
        if self.forward!='FORWARD': raise ValueError('This sample implementation requires the frozen FORWARD verdict')
        self.raw_docs={}
        # Existing converters use root-relative source files: declare/rebind that root explicitly.
        C.ROOT=self.root; C.DECODED=self.decoded; C.BASE_MASTER=self.apk; C.CARD_COMPARISON=self.root/'output/card_comparison_cid30236'
        R.DECODED=self.decoded; R.CARD_COMPARISON=C.CARD_COMPARISON
        os.chdir(self.root)
        self.old_answers={}
        for r in self.old.values():
            self.old_answers[(r['table'],r['record_id'],r['layer'])]=r.get('answers',[])
            for ch in r.get('children',[]):
                self.old_answers.setdefault((ch['table'],ch['record_id'],ch.get('layer',r['layer'])),ch.get('answers',[]))

    def skill(self,sid):
        if sid in self.cache_skill:
            i,row=self.cache_skill[sid]; layer='CACHE'; path='skilllist.data5.json.raw'; pointer=f'/skilllist/{i}'
        elif sid in self.apk_skill:
            i,row=self.apk_skill[sid]; layer='APK'; path='_mdSkill.json'; pointer=f'/skilllist/{i}'
        else: return None
        return dict(resolved=True,table='skilllist',reference_id=sid,record=row,layer=layer,
                    source=dict(source_key=f'{layer}/{path}',json_pointer=pointer,layer=layer,
                                record_key=f'{layer}/{path}#{pointer}'))

    def precise_source(self,entry):
        source=copy.deepcopy(entry.get('source') or {})
        ref=entry.get('reference_field','')
        table=entry.get('table')
        if entry.get('layer')=='CACHE' and table in ('bosspattern','bossskill','job_ability'):
            stem='jobabilityinfo' if table=='job_ability' else 'bossinfo'
            path=self.decoded/(stem+'.data5.json.raw')
            if not path.is_file():
                source.update(json_pointer=None,source_resolution='UNKNOWN_MISSING_DECODED_FILE',
                              note='声明的真实解码文件缺失，未伪造记录指针')
                return source
            if stem not in self.raw_docs:self.raw_docs[stem]=read(path)
            doc=self.raw_docs[stem]
            rows=doc['job_ability'] if table=='job_ability' else doc['bossinfo'][table]
            ident=entry.get('reference_id');record=entry.get('record')
            candidates=[(i,r) for i,r in enumerate(rows) if
                        (ident in (r.get('cids') or []) if table=='job_ability' else r.get('patternid' if table=='bosspattern' else 'skillid')==ident)
                        and (record is None or r==record)]
            if len(candidates)!=1:
                source.update(json_pointer=None,source_resolution='UNKNOWN_NON_UNIQUE_OR_MISMATCHED_RECORD',
                              note='按引用ID及完整原始record无法唯一匹配；未选择首条候选')
                return source
            index,_=candidates[0]
            pointer=f'/job_ability/{index}' if table=='job_ability' else f'/bossinfo/{table}/{index}'
            source.update(source_key=f'CACHE/{stem}.data5.json.raw',
                          record_key=f'CACHE/{stem}.data5.json.raw#{pointer}',json_pointer=pointer,
                          original_file=path.relative_to(self.root).as_posix(),
                          source_resolution='RESOLVED_EXACT_DECODED_RECORD',
                          note='按实际解码JSON的引用ID及完整原始record唯一核对；只修复定位，不升级数值或关联证据')
        if table in ('extra_ability_info','passive_info','denju_limit_break_info'):
            stem={'extra_ability_info':'extraabilitylist','passive_info':'passivelist','denju_limit_break_info':'denju_lblist'}[table]
            if stem not in self.raw_docs: self.raw_docs[stem]=read(self.decoded/(stem+'.data5.json.raw'))
            roots=self.raw_docs[stem][table]
            cid=int(str(entry['reference_id']).split('#')[0])
            parent_index,parent=next((i,r) for i,r in enumerate(roots) if r['cid']==cid)
            key={'extra_ability_info':'extra_abilities','passive_info':'passives','denju_limit_break_info':'denju_limit_break'}[table]
            ordinal=int(re.search(r'\[(\d+)\]',ref).group(1))
            if key not in parent:
                # Preserve actual nested-array name for denju data rather than guessing.
                key=next(k for k,v in parent.items() if isinstance(v,list) and ordinal<len(v) and v[ordinal]==entry['record'])
            assert parent[key][ordinal]==entry['record'],f'Nested source mismatch {cid}:{ref}'
            source.update(parent_json_pointer=f'/{table}/{parent_index}',
                          json_pointer=f'/{table}/{parent_index}/{key}/{ordinal}',
                          nested_reference_field=ref,
                          location_scope='字节范围和原始hash属于父记录；嵌套字段按完整JSON指针定位')
            if source.get('raw_record_sha256'):
                source['parent_raw_record_sha256']=source.pop('raw_record_sha256')
        return source

    def field_answers(self,entry):
        table,ident,layer=entry.get('table'),entry.get('reference_id'),entry.get('layer')
        rec=entry.get('record',{})
        existing=copy.deepcopy(self.old_answers.get((table,ident,layer),[]))
        if table=='charainfo':
            # Preserve the prior record-specific execution/equivalence gate.
            return existing
        etype=rec.get('ability') if table in ('skilllist','heroicskilllist','supporterskill') else rec.get('skillid0') if table=='bossskill' else None
        if etype is None: return existing
        seen={a['f'] for a in existing}
        for name,value in rec.items():
            field='/'+name
            if field in seen or not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value): continue
            answer=R.answer_for(table,etype,field,value,rec)
            if answer:
                existing.append(dict(f=field,raw=value,value=answer['value_text'],kind=answer['quantity_kind'],
                                     unit=answer['unit'],status=answer['answer_status'],scope='BY_TYPE_EXTRAPOLATED',
                                     rule_key=f'{table}|{etype}|{field}',details=answer))
        for answer in existing:
            rule=self.rule_metadata.get(answer.get('rule_key'),{})
            answer.setdefault('conversion',rule.get('conversion'))
            answer.setdefault('base_definition',rule.get('base_definition'))
            answer.setdefault('conditions',rule.get('conditions'))
            answer.setdefault('rule_limits',rule.get('limits'))
        return existing

    def evidence_tree(self,entry,seen=None):
        seen=set() if seen is None else seen
        key=(entry.get('table'),entry.get('reference_id'),entry.get('layer'))
        if key in seen: return []
        seen.add(key)
        out=[]
        if entry.get('resolved',True):
            out.append(dict(table=entry.get('table'),record_id=entry.get('reference_id'),layer=entry.get('layer'),
                            source=self.precise_source(entry),answers=self.field_answers(entry),
                            raw_record=entry.get('record'),association_evidence='确认·记录引用（不代表句内归属）'))
        for e in list(walk_entries(entry))[1:]:
            childkey=(e.get('table'),e.get('reference_id'),e.get('layer'))
            if childkey not in seen:
                seen.add(childkey)
                out.append(dict(table=e.get('table'),record_id=e.get('reference_id'),layer=e.get('layer'),
                                source=self.precise_source(e),answers=self.field_answers(e),raw_record=e.get('record'),
                                association_evidence='确认·记录引用（不代表句内归属）'))
        return out

    def forward_links(self,entry):
        if entry.get('table')!='extra_ability_info': return []
        out=[]
        for index,sid in enumerate(entry.get('record',{}).get('skill_ids',[])):
            wrapper=self.skill(sid)
            if not wrapper or wrapper['record'].get('ability')!=1082: continue
            raw=wrapper['record'].get('str0')
            try: target=self.skill(int(raw))
            except (ValueError,TypeError): target=None
            out.append(dict(wrapper_id=sid,wrapper=wrapper,target_id=target['reference_id'] if target else None,
                            raw_str0=raw,raw_str0_state=raw_state(wrapper['record'],'str0'),target=target,
                            reference_field=f"{entry['reference_field']}.skill_ids[{index}]",
                            evidence='确认·链上复用（str0转发已证）',
                            runtime_evidence='output/character_skills/type1082/native_checks.json',
                            field_answers=self.field_answers(target) if target else [],
                            limits='父limit_break档位及目标资格有门控；缺param0默认值和句内数值归属不随链升级'))
        return out


def basic(data, cid):
    rec=data.cache_chara.get(cid,data.apk_chara.get(cid))
    layer='CACHE' if cid in data.cache_chara else 'APK'
    source=data.links[cid]['charainfo_source']
    spec=[('name','姓名'),('title','称号'),('rarity','星级'),('cost','COST'),('jobtype','职业'),
          ('home','所属'),('battle_home','战斗所属'),('weaponid','武器ID'),('iniap','主表初始ATK'),('inihp','主表初始HP'),
          ('critical','暴击几率原值'),('atkspeed','攻击速度原值'),('growth','成长原值'),('profile','介绍')]
    fields=[]
    for key,label in spec:
        state=raw_state(rec,key)
        note=('缓存整条记录缺失职业，未知；未逐字段回退APK' if key=='jobtype' and state=='missing' and layer=='CACHE' else
              '主表缺失；外部/网站维护' if state=='missing' else '原值null；外部/网站维护' if state=='null' else
              '原值；单位或枚举语义未在此推定' if key in ('atkspeed','growth','battle_home','home','critical') else '主表原值')
        fields.append(dict(key=key,label=label,raw_value=rec.get(key),raw_state=state,note=note,
                           source={**source,'field':f'/{key}'},evidence='确认' if state not in ('missing','null') else '未知'))
    external=[dict(label=label,value='外部/网站维护',raw_state='missing') for label in ('标签/外部资料','日期','等级成长表')]
    for key,label in [('illustrator','画师'),('voice_artist','声优')]:
        external.append(dict(label=label,value=rec.get(key) if key in rec else '外部/网站维护',raw_state=raw_state(rec,key),
                             note='主表原值' if key in rec else '外部/网站维护',source={**source,'field':'/'+key}))
    return apply_basic_display(data,dict(fields=fields,external=external,layer=layer,card_art=dict(status='NO_VERIFIED_BINDING',
                    note='本样本未找到本项目已证绑定卡面；不借用参考页图片'),raw_record=rec))


def source_answer(answer,table,ident,source,numeric_source='规则',association='确认'):
    value=answer.get('value',answer.get('readable_value',''))
    return dict(value=value,quantity_kind=answer.get('kind',answer.get('quantity_kind')),
                raw_value=answer.get('raw',answer.get('raw_value')),field_path=answer.get('f',answer.get('field_path')),
                unit=answer.get('unit'),conversion=answer.get('conversion'),base_definition=answer.get('base_definition'),
                target=answer.get('target'),conditions=answer.get('conditions',answer.get('condition')),
                duration=answer.get('duration'),rule_limits=answer.get('rule_limits'),note=answer.get('note'),
                numeric_source=numeric_source,numeric_evidence='确认',association_evidence=association,
                evidence_scope=answer.get('scope',answer.get('evidence_scope')),
                table=table,record_id=ident,source=source,rule_key=answer.get('rule_key'),
                evidence=answer.get('evidence'),quantitative=quantitative(value))


def baseline_target(b):
    ids=re.findall(r'pattern(\d+)',b.get('condition',''))
    if b.get('description_table')=='bosspattern' and len(set(ids))==1: return int(ids[0])
    return b.get('description_record_id')


def build_card(data:Inputs,cid):
    profile=data.profiles[cid]; links=data.links[cid]
    oldgroups={g['group']:g for g in profile['groups']}
    linkgroups={g['group']:g for g in links['groups']}
    groups=[]; allrows=[]; mapping=[]; position_rows={};registry={b['effect_id']:dict(answer=b,mapped_row_ids=[],mapped_skill_ids=[]) for b in data.baseline} if cid==30236 else {}
    stage_targets={}
    patterns=[e for g in links['groups'] if g['group']=='special_move' for e in g['records'] if e.get('table')=='bosspattern']
    for effect_id,item in registry.items():
        b=item['answer'];target=baseline_target(b)
        if b.get('description_table')=='bosspattern':
            required={(f.get('table'),f.get('record_id')) for f in b.get('field_refs',[])}
            candidates=[e['reference_id'] for e in patterns if required and required <=
                        {(n.get('table'),n.get('reference_id')) for n in walk_entries(e)}]
            if len(candidates)==1:target=candidates[0]
        stage_targets[effect_id]=target
        item['execution_description_id']=target
    for group_id,label in GROUPS:
        group=dict(group=group_id,label=label,skills=[],status='无配置',unresolved=[],annotations=[])
        source_groups=[group_id,'denju_lb'] if group_id=='denju' else [group_id]
        for original_group in source_groups:
            lg=linkgroups.get(original_group,{})
            group['unresolved']+=lg.get('unresolved',[]); group['annotations']+=lg.get('annotations',[])
            oldrefs=oldgroups.get(original_group,{}).get('records',[])
            display_slots={}
            expanded=[]
            for source_ordinal,e in enumerate(lg.get('records',[])):
                expanded.append({**e,'_origin_ordinal':source_ordinal})
                if e.get('table')=='leader_ability' and e.get('record',{}).get('sympathy_text'):
                    expanded.append({**e,'reference_field':e['reference_field']+'.sympathy_text',
                                     '_text_field_override':'sympathy_text','_origin_ordinal':source_ordinal})
            for ordinal,entry in enumerate(expanded):
                record=entry.get('record',{}); table=entry.get('table'); ref=entry.get('reference_field',str(ordinal))
                source=data.precise_source(entry)
                display_key=json.dumps([original_group,ref,table,entry.get('reference_id'),record,source.get('source_key'),source.get('json_pointer')],sort_keys=True,ensure_ascii=False)
                # Equal aliases do not shift the display/row IDs of later real slots.
                ordinal=display_slots.setdefault(display_key,len(display_slots))
                tf,nf=TEXT.get(table,('text','name'));tf=entry.get('_text_field_override',tf); text=clean(record.get(tf,''))
                name=clean(record.get(nf,'')) if nf else ''
                original_ref=ref.removesuffix('.sympathy_text') if entry.get('_text_field_override') else ref
                matching_old=[r for r in oldrefs if r.get('reference_field')==original_ref]
                if len(matching_old)>1:
                    matching_old=[r for r in matching_old if (data.old.get(r.get('rec_key'),{}).get('table'),
                                  str(data.old.get(r.get('rec_key'),{}).get('record_id')),data.old.get(r.get('rec_key'),{}).get('layer'))
                                  ==(table,str(entry.get('reference_id')).split('#')[0],entry.get('layer'))]
                oldref=matching_old[0] if len(matching_old)==1 else {}
                old=data.old.get(oldref.get('rec_key'),{})
                oldfrags=old.get('fragments',[]) if table not in ('extra_ability_info','passive_info','denju_limit_break_info') else []
                stage=('传授突破' if original_group=='denju_lb' else '原表顺序档' if group_id=='passive' else '档位')+f' {ordinal+1}'
                if 'lv' in record and record['lv'] not in (None,''): stage='Lv '+str(record['lv'])
                if tf=='sympathy_text':stage='Leader共鸣（原字段sympathy_text）'
                skill_id=f'{cid}/{group_id}/{original_group}/{ref}'
                skill=dict(skill_id=skill_id,name=name,stage=stage,level=record.get('lv'),level_state=raw_state(record,'lv'),
                           reference_field=ref,original_group=original_group,record_id=entry.get('reference_id'),table=table,
                           layer=entry.get('layer'),source=source,text_field=tf,original_text=text,
                           cost=record.get('scost',record.get('skill_cost')),cost_state=raw_state(record,'scost') if table!='charainfo' else raw_state(record,'skill_cost'),
                           rows=[],record_evidence=data.evidence_tree(entry),forward_links=data.forward_links(entry),
                           old_rec_key=oldref.get('rec_key'),link_status=entry.get('link_status'),
                           baseline_metadata_answers=[],
                           association_evidence='推断' if entry.get('ambiguous') or 'INFERRED' in str(entry.get('link_status','')) else '确认')
                skill['level_note']='原表无等级字段，序号不代表解锁等级' if group_id=='passive' and 'lv' not in record else '按原始引用独立保留档位；实际装载另有门控'
                for effect_id,item in registry.items():
                    b=item['answer']
                    # A conditional variant without independent effect prose stays a header annotation.
                    variant=(not text and table=='bosspattern' and b.get('description_table')==table and stage_targets[effect_id]==entry.get('reference_id'))
                    metadata=(not b.get('description_fragment_ja') and table=='bosspattern' and
                              b.get('description_table')==table and b.get('description_record_id')==entry.get('reference_id'))
                    if variant or metadata:
                        a=source_answer(b,table,entry.get('reference_id'),b.get('field_refs'),'既有逐描述证据')
                        a.update(effect_id=effect_id,conditions=b.get('condition'),
                                 baseline_declared_description_id=b.get('description_record_id'),
                                 mapping_note='执行档位及真实子记录引用；本档无独立正文，不新增描述行' if variant else '技能配置/就绪门槛，未虚造描述行')
                        skill['baseline_metadata_answers'].append(a);item['mapped_skill_ids'].append(skill_id)
                internal=text and not any(c in text for c in ('。','◆','\n')) and (bool(re.match(r'^(?:■)?(?:エクストラ_|パッシブ_|職業_|内部)',text)) or 'SA_' in text)
                if internal:
                    skill['internal_label']=text
                    mapping.append(dict(cid=cid,old_rec_key=oldref.get('rec_key'),old_reference_field=ref,
                                        old_fragment_text=text,new_row_id=None,new_source=source,new_text=text,
                                        correction='内部标签保留配置，不计N_all/N_num；非E排除'))
                for fragment_index,span in enumerate([] if internal else fragment_positions(record.get(tf,''))):
                    frag=span['japanese']
                    row_id=f'{cid}-{group_id}-{original_group}-{ref}-lv{record.get("lv","order"+str(ordinal))}-f{fragment_index}'
                    row_id=re.sub(r'[^\w\-]','_',row_id)
                    originals=original_numbers(frag)
                    answers=[dict(value=f"{n['role']}：{n['literal']}",quantity_kind=n['role'],unit=n['unit'],
                                  raw_value=n['value'],numeric_source='原文',numeric_evidence='确认',association_evidence='未知',
                                  note='原文数字，字段关联未证',source={**source,'field':'/'+tf},context=n['context'],
                                  quantitative=True) for n in originals]
                    matched_old=next((f for f in oldfrags if canonical(f['t'])==canonical(frag)),None)
                    if matched_old and matched_old.get('binding') and matched_old.get('status')=='REVIEWED_DESCRIPTION_BINDING':
                        for answer in matched_old['binding'].get('fields',[]):
                            converted=source_answer(answer,answer.get('table',table),answer.get('record_id',entry.get('reference_id')),source)
                            converted['binding']=matched_old['binding']
                            answers.append(converted)
                    # Baseline attaches only at an explicit fragment, table and actual stage.
                    for effect_id,item in registry.items():
                        b=item['answer']; snippet=b.get('description_fragment_ja')
                        if b.get('description_table')!=table or stage_targets[effect_id] not in (None,entry.get('reference_id')): continue
                        if table=='job_ability':
                            # The baseline itself distinguishes self and battlefield targets;
                            # its shortened snippet is not a license to match both sentences.
                            target=b.get('target','')
                            ref_ids={f.get('record_id') for f in b.get('field_refs',[])}
                            if 65000002 in ref_ids and target=='战场味方' and not frag.startswith('戦場にいる味方'):continue
                            if 65000001 in ref_ids and target=='自身' and not frag.startswith('攻撃力と防御力'):continue
                        if snippet:
                            if canonical(snippet) not in canonical(frag):continue
                        else:
                            description=b.get('description_ja')
                            exact_text=(text in description if isinstance(description,list) else clean(description)==text)
                            if not exact_text:continue
                            if table=='leader_ability':
                                if len(fragments(text))!=1:continue
                            elif table=='extra_ability_info':
                                if effect_id=='extra_chain' and 'Chainによる威力の上昇量' not in frag:continue
                                elif effect_id=='other_extra_initial_mana' and '万象マナを1つ持った状態' not in frag:continue
                                elif effect_id not in ('extra_chain','other_extra_initial_mana'):continue
                            else:continue
                        a=source_answer(b,table,entry.get('reference_id'),b.get('field_refs'),numeric_source='既有逐描述证据')
                        a.update(effect_id=effect_id,baseline_declared_description_id=b.get('description_record_id'),
                                 target=b.get('target'),conditions=b.get('condition'),evidence=b.get('evidence'),
                                 evidence_scope='REVIEWED_RECORD',conversion='原101项基线的既有换算；不再次乘Chain')
                        if effect_id=='extra_chain':
                            amount=next(n['literal'] for n in originals if n['unit']=='%')
                            a['value']=f'本档Chain威力提升量 {amount}（原文；原101项基线支持分档）'
                        answers.append(a); item['mapped_row_ids'].append(row_id)
                    numerical=[a for a in answers if a['quantitative']]
                    # Existing baseline mechanisms may be useful, but only count B with an explicit added claim.
                    mechanisms=[a for a in answers if not a['quantitative'] and a.get('numeric_source')=='既有逐描述证据']
                    cls='A' if numerical else 'B' if mechanisms else 'C'
                    association='确认' if any(a['association_evidence']=='确认' for a in answers) else '未知'
                    if skill['association_evidence']=='推断' and association=='确认': association='推断'
                    reasons=[]
                    if association!='确认': reasons.append('尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应' if originals else '原文未提供该效果数值，尚无已审定的句内字段归属')
                    if not answers: reasons.append('此描述尚无可适用的已确认数值或新增机制证据')
                    if matched_old and matched_old.get('cands') and not matched_old.get('binding'):
                        reasons.append('旧关键词候选未作为答案；不能排除对象或效果错配')
                    if group_id=='heroic': reasons.append('英雄技引用沿用既有ID模式关联，未证明运行时装载和等级条件')
                    if skill['forward_links']: reasons.append('str0目标规则已在来源层复用；具体句内归属、对象资格及缺参默认值另列未知')
                    partial=cls=='A' and not (matched_old and matched_old.get('binding') and skill['association_evidence']=='确认')
                    state_keys=([f'param{i}' for i in range(10)] if table in ('skilllist','heroicskilllist','supporterskill') else
                                [f'skillparam{i}' for i in range(10)] if table in ('charainfo','bossskill') else [])
                    states={k:raw_state(record,k) for k in sorted(set(state_keys)|{k for k in record if re.match(r'(param|iParam|skillparam|str)\d',k)})}
                    state_counts=collections.Counter(states.values())
                    state_summary=('原值状态：'+ ' / '.join(f'{label}{state_counts[state]}' for state,label in
                                  [('present','有值'),('zero','真实零'),('null','null'),('missing','缺失')])) if states else '父记录无直接参数槽；已关联子记录原值保留在来源层'
                    row=dict(row_id=row_id,cid=cid,group=group_id,stage=stage,level=record.get('lv'),reference_field=ref,
                             fragment_index=fragment_index,japanese=frag,context_text=text,row_class=cls,answers=answers,
                             original_numeric_items=originals,original_A=bool(originals),evidence='确认' if association=='确认' else '推断' if association=='推断' else '未知',
                             numeric_evidence='确认' if numerical else '未知',association_evidence=association,
                             partial=partial,unknown_reasons=reasons,source={**source,'field':'/'+tf,
                                'field_json_pointer':source.get('json_pointer','')+'/'+tf if source.get('json_pointer') else None},
                             raw_value_states=states,raw_state_summary=state_summary,
                             source_evidence_ref=skill_id,old_fragment_status=matched_old.get('status') if matched_old else None,
                             old_candidates_reused=False,mechanism_added=mechanisms,
                             evidence_scope=sorted({str(a['evidence_scope']) for a in answers if a.get('evidence_scope')}))
                    # The display ordinal is not an execution identity. Reference slots
                    # and the actual parent record (including level/conditions) are.
                    execution_context=dict(reference_slot=ref,parent_record_sha256=hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest())
                    identity=position_identity(cid,group_id,row['source'],table,entry.get('reference_id'),skill['level_state'],record.get('lv'),span,original_group,execution_context)
                    encoded_identity=json.dumps(identity,ensure_ascii=False,separators=(',',':'))
                    row['source_position']={**span,'field_pointer':row['source']['field_json_pointer'],'source_key':source.get('source_key')}
                    row['source_span_id']='span-'+hashlib.sha256(encoded_identity.encode('utf-8')).hexdigest()[:20]
                    row['merge_key']=identity;row['alias_references']=[]
                    if encoded_identity in position_rows:
                        original=position_rows[encoded_identity]
                        for item in registry.values():
                            item['mapped_row_ids']=[original['row_id'] if rid==row_id else rid for rid in item['mapped_row_ids']]
                        original['alias_references'].append(dict(row_id=row_id,reference_field=ref,source=source,stage=stage,origin_list_ordinal=entry['_origin_ordinal']))
                        skill.setdefault('alias_row_ids',[]).append(original['row_id'])
                        row_id=original['row_id']
                    else:
                        position_rows[encoded_identity]=row
                        skill['rows'].append(row);allrows.append(row)
                    old_fragment=next((f['t'] for f in old.get('fragments',[]) if canonical(f['t'])==canonical(frag)),None)
                    if table in ('extra_ability_info','passive_info','denju_limit_break_info') and fragment_index<len(old.get('fragments',[])):
                        old_fragment=old['fragments'][fragment_index]['t']
                    mapping.append(dict(cid=cid,old_rec_key=oldref.get('rec_key'),old_reference_field=ref,
                                        old_occurrence_key=f'{cid}/{original_group}/{ref}/f{fragment_index}',old_fragment_text=old_fragment,
                                        new_row_id=row_id,new_source=row['source'],new_text=frag,
                                        correction='按links逐档原文纠正复用rec_key' if table in ('extra_ability_info','passive_info','denju_limit_break_info') else '保持原始引用/句子边界'))
                if not skill['rows']: skill['empty_reason']='同源位置及同执行档/父条件的别名引用，描述已合并；见alias_row_ids' if skill.get('alias_row_ids') else '内部标签，不计描述分母' if internal else '关联缺失' if not entry.get('resolved',True) else '无描述正文；保留配置原值'
                group['skills'].append(skill)
        if group['skills'] or group['annotations']: group['status']='已配置'
        if group['unresolved']: group['status']='关联缺失'
        groups.append(group)
    counts=collections.Counter(r['row_class'] for r in allrows); cross={c:{e:0 for e in ('确认','推断','未知')} for c in ('A','B','C')}
    for r in allrows: cross[r['row_class']][r['evidence']]+=1
    total=len(allrows); chains=[f for g in groups for s in g['skills'] for f in s['forward_links']]
    coverage=dict(N_all=total,E=0,N_num=total,A=counts['A'],B=counts['B'],C=counts['C'],
                  A_rate=counts['A']/total if total else 0,B_rate=counts['B']/total if total else 0,C_rate=counts['C']/total if total else 0,
                  evidence_cross=cross,partial_A=sum(r['partial'] for r in allrows),original_A=sum(r['original_A'] for r in allrows),
                  chain_target_associations=len(chains),chain_targets_with_rules=sum(bool(f['field_answers']) for f in chains),
                  chain_new_A_rows=0,chain_new_value_items_in_rows=0,
                  chain_parent_original_A_rows=sum(r['original_A'] for g in groups for s in g['skills'] if s['forward_links'] for r in s['rows']),
                  old_descriptions=profile['coverage']['descriptions'],old_confirmed=profile['coverage']['fragments_attributed_confirmed'],
                  old_hint=profile['coverage']['fragments_attributed_hint_only'])
    coverage['internal_labels_excluded']=sum(bool(s.get('internal_label')) for g in groups for s in g['skills'])
    coverage['leader_sympathy_rows_added']=sum(len(s['rows']) for g in groups for s in g['skills'] if s['text_field']=='sympathy_text')
    coverage['repeated_actual_occurrences_retained']=sum(len(s['rows'])-len({canonical(r['japanese']) for r in s['rows']}) for g in groups for s in g['skills'])
    coverage['same_position_aliases_merged']=sum(len(r['alias_references']) for r in allrows)
    return dict(schema_version='card-page-pilot-1',cid=cid,basic=basic(data,cid),groups=groups,coverage=coverage,
                summary=metrics(coverage),implementation_status=INFERENCE_STATUS,
                sources=dict(input_root='声明的 --input-root',snapshot='cache_full_20261015_v3 + APK5.6.2',
                             task0_verdict=data.forward,baseline_registry=registry,old_to_new=mapping),
                reference_comparison=dict(local_layout='仅参考结构；不读取参考数值或图片作为数据',website_status='待主持/独立R1实际浏览对照',
                                          external_difference_note='网站一致/差异独立于证据等级；外部值不覆盖游戏原值'))
