"""Finite type67 weapon/job sentence binding; reuses independently reviewed B9 evidence."""
import collections,functools,json,re
from pathlib import Path
import common as C
import batch_bindings as B6
import p3b7_bindings as B7
import p3b9_bindings as B9

OUT=C.ROOT/'output/character_skills/description_bindings/p3b10_batch'
SCOPE=Path(__file__).with_name('p3b10_binding_scope.json')
WEAPONS=C.DECODED/'weaponlist.data5.json.raw'
STRENGTH='受控结构规则审定＋原值与原生效果规则支持；限P3B10冻结28条type67队列，不是机器码解析日文'
PATTERN=r'戦場に(?P<exclude>自身以外の)?<(?P<target>[^<>]+)>(?P<weapon>武器)?の味方がいると(?P<comma>、)?自身の(?P<effects>(?:攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力)(?:と(?:攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力))*)が上がる'
TERMS=B9.TERMS
ZERO=['param4','param5','param8','param9','iParam1','flag0_1','flag1_0','flag1_1']
ALL=B9.ALL

@functools.lru_cache(maxsize=1)
def scope():return C.load_json(SCOPE)
@functools.lru_cache(maxsize=1)
def tables():return C.Tables()
@functools.lru_cache(maxsize=1)
def membership():return B7.reference_membership()

def weapon_audit(character,document):
 """Exact declared pointers and complete rows, including missing fields; no defaults."""
 rows=document.get('weaponlist')
 if not isinstance(rows,list):return dict(invalid='WEAPONLIST_NOT_ARRAY')
 result=[]
 for field in ['weaponid','weaponid2']:
  present=field in character;wid=character.get(field)
  matches=[dict(pointer=f'/weaponlist/{i}',raw_record=r,raw_sha256=B6.digest(r),type_present='type'in r,type_value=r.get('type'))for i,r in enumerate(rows)if isinstance(r,dict)and type(r.get('id'))is type(wid)and r.get('id')==wid]
  result.append(dict(character_field=field,present=present,value=wid,source=dict(snapshot=C.SNAPSHOT_ID,layer='CACHE',path=str(WEAPONS.relative_to(C.ROOT)),table='weaponlist',selection='DECLARED_CACHE_WEAPONLIST_NO_APK_FALLBACK'),rows=matches))
 return result

@functools.lru_cache(maxsize=4)
def raw_audit(provider):
 """Full selected ordinary references, original rows, reverse parents and weapons."""
 targets={int(k.split('|')[1])for k in scope()['records']};mm=membership();ct=provider('charainfo');st=provider('skilllist');refs=collections.defaultdict(list);parents=collections.defaultdict(list)
 for cid in sorted(ct.ids()):
  raw,layer=ct.get(cid)
  for i,sid in enumerate(raw.get('skillid')or []):
   if i<1 or sid not in targets:continue
   playable=mm['playable'].get(cid);other=mm['other'].get(cid);included=cid in mm['playable']and cid in mm['profiles']and cid in mm['links']
   refs[sid].append(dict(cid=cid,slot=f'skillid[{i}]',source=C.location('charainfo',cid,layer,raw),raw_sha256=B6.digest(raw),original_rows=B9.original_rows(ct,cid),in_playable_roster=cid in mm['playable'],in_profiles=cid in mm['profiles'],in_links=cid in mm['links'],roster_record_sha256=B6.digest(playable)if playable else None,other_record_sha256=B6.digest(other)if other else None,included=included,exclusion_reason=None if included else'OUTSIDE_CURRENT_PLAYER_SCOPE_RAW_REFERENCE_ONLY',declared_identity={k:dict(present=k in raw,value=raw.get(k))for k in ['jobtype','home','battle_home','is_enemy','rarity','weaponid','weaponid2']}))
 for ident in sorted(st.ids()):
  raw,layer=st.get(ident)
  for i,sid in enumerate(raw.get('sub')or []):
   if sid in targets:parents[sid].append(dict(parent_id=ident,sub_index=i,source=C.location('skilllist',ident,layer,raw),raw_sha256=B6.digest(raw),original_rows=B9.original_rows(st,ident)))
 result={}
 for sid in sorted(targets):
  raw,layer=st.get(sid)
  result[sid]=dict(root_source=C.location('skilllist',sid,layer,raw)if raw else None,root_sha256=B6.digest(raw),root_original_rows=B9.original_rows(st,sid),raw_charainfo_references=refs[sid],reverse_sub_references=parents[sid])
 return result

def declared_weapons(audit,provider,document):
 return [dict(cid=x['cid'],weapons=weapon_audit(provider('charainfo').get(x['cid'])[0],document))for x in audit['raw_charainfo_references']]

@functools.lru_cache(maxsize=1)
def native_ready():
 ev=C.load_json(OUT/'reused_native_evidence.json')
 return C.sha256_file(OUT/'reused_native_evidence.json')==scope()['reused_native_sha256']and ev['new_native_execution']is False and all(C.sha256_file(C.ROOT/x['path'])==x['sha256']for x in ev['sources'])

def bind(entry,fragment,answers,children,actual_contexts=None,actual_audit=None,actual_membership=None,actual_weapon_document=None):
 key=f"{entry.get('table')}|{entry.get('reference_id')}";spec=scope()['records'].get(key)
 if not spec:return None,'OUTSIDE_P3B10_FROZEN_QUEUE'
 rec=entry.get('record')or {};match=re.fullmatch(PATTERN,fragment)
 if not match or type(rec.get('ability'))is not int or rec['ability']!=67:return None,'WHOLE_SENTENCE_OR_TYPE_CHANGED'
 if fragment!=spec['fragment']or rec.get('text')not in [fragment,fragment+'。','◆'+fragment,'◆'+fragment+'。']:return None,'WHOLE_SOURCE_TEXT_CHANGED'
 if any(k not in rec or rec[k]is None or isinstance(rec[k],bool)for k in ALL):return None,'MISSING_NULL_BOOL_CONTROL'
 # Full strict JSON identity precedes interpreting selectors or numbers.
 if C.SNAPSHOT_ID!=scope()['snapshot']or entry.get('layer')!='APK':return None,'SNAPSHOT_OR_LAYER_CHANGED'
 if entry.get('source')!=spec['source']or B6.digest(rec)!=spec['entry_sha256']:return None,'FROZEN_ROOT_OR_SOURCE_CHANGED'
 if any(rec[k]!=0 for k in ZERO):return None,'CONTROL_NOT_EXPLICIT_ZERO'
 if rec.get('sub')!=[]or children:return None,'ACTUAL_SUB_OR_CHILD_CHANGED'
 wanted=[TERMS[t][0]for t in match['effects'].split('と')]
 if wanted!=spec['target_fields']or len(set(wanted))!=len(wanted):return None,'SEMANTIC_TERMS_CHANGED'
 label=scope()['weapon_labels'].get(match['target'])
 if match['weapon']:
  if match['comma']or not label or rec['iParam0']!=0 or rec['flag0_0']!=label['flag']:return None,'WEAPON_LABEL_OR_FILTER_MISMATCH'
 elif match['target']!='戦士'or not match['comma']or rec['flag0_0']!=0 or rec['iParam0']!=1:return None,'FINITE_JOB_PUNCTUATION_CHANGED'
 if rec['param0']not in [1.,2.]:return None,'COUNT_THRESHOLD_CHANGED'
 raw,layer=tables()('skilllist').get(entry['reference_id'])
 if not raw or layer!='APK'or C.location('skilllist',entry['reference_id'],layer,raw)!=spec['source']or B6.digest(raw)!=spec['entry_sha256']:return None,'CURRENT_RAW_SOURCE_CHANGED'
 cc=B6.contexts().get(key,[])if actual_contexts is None else actual_contexts
 if cc!=spec['contexts']:return None,'ALL_REFERENCE_CONTEXTS_CHANGED'
 if not cc or any(not re.fullmatch(r'/groups/\d+/records/\d+',c['link_path'])or c['reference_field']!='skillid[3]'for c in cc):return None,'NON_ORDINARY_DIRECT_REFERENCE'
 if (membership()['identity']if actual_membership is None else actual_membership)!=scope()['reference_scope_identity']:return None,'PLAYER_SCOPE_IDENTITY_CHANGED'
 audit=raw_audit(tables()).get(entry['reference_id'])if actual_audit is None else actual_audit
 if audit!=spec['raw_audit']:return None,'RAW_IDENTITY_REFERENCES_OR_PARENTS_CHANGED'
 if audit['reverse_sub_references']:return None,'REVERSE_SUB_CONTEXT_NOT_APPROVED'
 if C.sha256_file(WEAPONS)!=scope()['weapon_source_sha256']:return None,'WEAPON_SOURCE_BYTES_CHANGED'
 document=json.loads(WEAPONS.read_bytes())if actual_weapon_document is None else actual_weapon_document
 if declared_weapons(audit,tables(),document)!=spec['declared_weapons']:return None,'DECLARED_WEAPON_ROW_POINTER_MISSING_TYPE_OR_SOURCE_CHANGED'
 if B6.digest(answers)!=spec['local_answers_sha256']:return None,'LOCAL_ANSWER_OBJECT_ORDER_OR_DUPLICATE_CHANGED'
 fields=[]
 for term in match['effects'].split('と'):
  f,path=TERMS[term];hits=[a for a in answers if a['f']==f]
  if len(hits)!=1 or hits[0]['raw']!=rec[f[1:]]or hits[0]['status']!='CONFIRMED_NUMERIC'or hits[0]['scope']not in ['IN_REVIEWED_VIEW','BY_TYPE_EXTRAPOLATED']:return None,'LOCAL_TARGET_VALUE_STATUS_SCOPE_CHANGED'
  fields.append(B6.field_copy(hits[0],entry,term,'BattleParam type67 '+path))
 condition_fields=[B6.field_copy(next(a for a in answers if a['f']==f),entry,'原生计数条件','CalcCharaNum')for f in ['/param0','/iParam0','/flag0_0','/param8']]
 if not native_ready():return None,'REUSED_NATIVE_EVIDENCE_CHANGED'
 selector=f"武器flag0_0={hex(rec['flag0_0'])}（{match['target']}；实际BattleParam._weaponTypeAttackFlag相交）"if match['weapon']else'职业iParam0=1（戦士）；非0职业筛选还须阵营聚合职业位图相交'
 condition=f"本记录由冻结普通skillid[3]引用且实际装载到持有者BattleParam；页面引用不证明装载/解锁。五路径按同阵营GetMemberList(onlyActive=0, onlyAlive=1, onlyInGround=0)取列表，真实IsAlive为HP>=1且state!=12；该重载不按可见、场内、出场/hero筛选。CalcCharaNum随后要求_isActive!=0；{selector}，职业/武器/所属同时筛选，本批param8=0不筛所属。N为通过实际列表、快速门槛及全部筛选的成员数，要求N>=int(param0)={int(rec['param0'])}（有限值向零截断，比较含等于）。"
 if match['exclude']:
  relation='原文写自身以外，但原生不直接移除持有者；仅当持有者运行时也满足全部筛选且确实计入N时，N>=2才等价其他合格成员>=1；否则仍按N>=2，不无条件换述其他>=1。'
 else:relation='原文未排除持有者，N>=1即可；持有者仅在运行时合格且实际计入时可贡献该计数，不保证声明武器一定匹配筛选。'
 if spec['subgroup']=='DECLARED_WEAPON_TYPE_MISSING_3':
  wid=spec['declared_weapons'][0]['weapons'][0]['value']
  relation+=f'当前持有者主weaponid={wid}对应当前CACHE weaponlist行缺type，无法从声明数据确认自身能否计入N；不据名称/外观/缺失默认0推武器类型。该声明身份缺口不把本项数值填0；保留真实N>=2条件。'
 else:relation+='冻结声明武器/职业身份不保证实际装载、装备或动态资格；声明身份不是自身必计入的证明。'
 return dict(template_id='p3b10_type67_weapon_or_job_self_stats',strength=STRENGTH,status='已确认（冻结队列结构对应；实际N条件及声明武器缺口明示）',target='本记录实际装载者自身的原生单项贡献',condition=condition+relation,duration='每次读取按当时列表和筛选判定本项贡献；没有计时秒数，不补0秒',rationale='完整纯句目标项对应67五路径唯一现成消费者，整源无sub；实际原表引用/反向sub及声明武器完整行冻结。武器标签由已审枚举/Constants位映射支持；未写五路径项中性依既有消费者和原值共同成立，不猜其他未知槽。',source=entry['source'],fields=fields,condition_fields=condition_fields,siblings=[],text_condition_relation=relation,declared_weapon_evidence=spec['declared_weapons'],subgroup=spec['subgroup'],native_evidence='output/character_skills/description_bindings/p3b10_batch/reused_native_evidence.json',eligibility_evidence='output/character_skills/description_bindings/p3b9_batch/native_evidence.json',limits='仅本记录条件成立时的乘数/加算贡献，不是所有技能叠加后的总属性、最终伤害或暴击总概率。防御是受伤量倍率，非固定防御。复用B9真实列表/计数/五worker及武器AND交集证据，未新增原生执行；列表/单例/保护值getter有明确夹具，不是实机或完整引擎。实际装备/动态武器资格/装载为运行时前提，全部未知字段保留。',frozen_contexts=spec['contexts'],snapshot=scope()['snapshot']),None
