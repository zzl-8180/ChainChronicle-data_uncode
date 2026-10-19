"""P3B6 controlled structural correspondences on an explicitly frozen queue.

The queue pins reviewed inputs/contexts; membership alone never proves a sentence.
The recognisers also check grammar, source, local field identity, actual child
consumers, native controls and all role reference contexts. Numeric scopes stay
untouched. This module does not generalise to all type26/type5 records.
"""
from __future__ import annotations
import collections,functools,hashlib,json,math,re
from pathlib import Path
import common as C
import equivalence as EQ
import description_bindings as DB

OUT=C.ROOT/'output/character_skills/description_bindings/p3b6_batch'
SCOPE=Path(__file__).with_name('p3b6_binding_scope.json')
STRENGTH='受控结构规则审定＋原值与原生效果规则支持；限冻结候选及APK快照，不是机器码解析日文'
LINE='直線範囲上にいる全ての敵に小ダメージを与える'

def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()

@functools.lru_cache(maxsize=1)
def scope():return C.load_json(SCOPE)

@functools.lru_cache(maxsize=1)
def contexts():
 result=collections.defaultdict(list)
 def walk(x,path,p):
  if isinstance(x,dict):
   if x.get('resolved') and x.get('record') and 'table'in x:
    key=f"{x['table']}|{x.get('reference_id')}"
    result[key].append(dict(cid=p['cid'],link_path=path,reference_field=x.get('reference_field'),layer=x.get('layer'),character_source=p['charainfo_source']))
   for k,v in x.items():
    if k not in ['record','source','charainfo_source']:walk(v,path+'/'+k,p)
  elif isinstance(x,list):
   for i,v in enumerate(x):walk(v,path+'/'+str(i),p)
 for p in map(json.loads,(C.ROOT/'output/character_skills/links/character_skills.jsonl').open(encoding='utf-8')):walk(p,'',p)
 return result

def guard(entry,actual_contexts=None):
 key=f"{entry.get('table')}|{entry.get('reference_id')}";spec=scope()['records'].get(key)
 if not spec:return None,'OUTSIDE_P3B6_FROZEN_QUEUE'
 if C.SNAPSHOT_ID!=scope()['snapshot']or entry.get('layer')!='APK':return None,'SNAPSHOT_OR_LAYER_CHANGED'
 if entry.get('source')!=spec['source']or digest(entry.get('record'))!=spec['entry_sha256']:return None,'FROZEN_RECORD_OR_SOURCE_CHANGED'
 cc=contexts().get(key,[])if actual_contexts is None else actual_contexts
 if cc!=spec['contexts']:return None,'ALL_REFERENCE_CONTEXTS_CHANGED'
 if not cc or any(not re.fullmatch(r'/groups/\d+/records/\d+',c['link_path'])for c in cc):return None,'NON_DIRECT_REFERENCE'
 return spec,None

def field_copy(a,entry,semantic,native_path):
 return dict(f=a['f'],raw=a['raw'],value=a['value'],kind=a['kind'],unit=a['unit'],status=a['status'],evidence_scope=a['scope'],rule_key=a['rule_key'],table=entry['table'],record_id=entry['reference_id'],semantic_effect=semantic,native_path=native_path)

def bind(entry,fragment,answers,children,actual_contexts=None):
 spec,reason=guard(entry,actual_contexts)
 if reason:return None,reason
 rec=entry['record'];family=spec['family']
 if family=='type26_start_mana':
  match=re.fullmatch(r'マナを([１２３123])つ持った状態で戦闘を開始する',fragment)
  if not match or rec.get('ability')!=26:return None,'WHOLE_SENTENCE_GRAMMAR_CHANGED'
  if any(c['reference_field']not in ['skillid[1]','skillid[2]']for c in spec['contexts']):return None,'ABILITY_REFERENCE_CONDITION_CHANGED'
  if any(k not in rec or rec[k]is None or rec[k]!=0 for k in ['param1','param2','param3','param4','param5','param6','param7','iParam0','iParam1']):return None,'OTHER_MANA_LINE_OR_GATE_CHANGED'
  declared=rec.get('sub')
  if not isinstance(declared,list)or len(set(declared))!=len(declared):return None,'SUB_DECLARATION_INVALID'
  if len(children)!=len(declared)or collections.Counter(c.get('record_id')for c in children)!=collections.Counter(declared):return None,'MISSING_OR_DUPLICATE_CHILD'
  tab=C.Tables();sources=[]
  for ch in children:
   if ch.get('link_kind')!='sub_effect'or ch.get('table')!='skilllist'or ch.get('effect_type')!=9:return None,'CHILD_CONSUMER_NOT_APPROVED'
   sr,sl=tab('skilllist').get(ch['record_id'])
   if not sr or sr.get('ability')!=9 or sr.get('sub'):return None,'CHILD_TREE_CHANGED'
   src=C.location('skilllist',ch['record_id'],sl,sr)
   if ch.get('source')!=src:return None,'CHILD_SOURCE_CHANGED'
   sources.append(src)
  if sources!=spec['sub_sources']:return None,'FROZEN_CHILD_SOURCE_CHANGED'
  from type26_mana import KIND,CONDITION,LIMITS,published_native
  ev=published_native()
  if ev['native_sha256']!=scope()['native_sha256']or ev['passed']!=ev['total']:return None,'NATIVE_EVIDENCE_CHANGED'
  if children:
   bullet_ev=C.load_json(C.ROOT/'output/character_skills/type9_crit/native_evidence.json')
   if bullet_ev['native_sha256']!=scope()['native_sha256']or bullet_ev['passed']!=bullet_ev['total']:return None,'BULLET_NATIVE_EVIDENCE_CHANGED'
  hits=[a for a in answers if a['f']=='/param0'and a['kind']==KIND and a['status']=='CONFIRMED_NUMERIC']
  if len(hits)!=1 or rec.get('param0')!=hits[0]['raw']or hits[0]['raw']!=int(match[1]):return None,'LOCAL_VALUE_OR_TEXT_NUMBER_MISMATCH'
  a=hits[0]
  if a!=spec['local_answer']:return None,'FROZEN_LOCAL_ANSWER_CHANGED'
  return dict(template_id='p3b6_type26_start_mana_digit',strength=STRENGTH,status='已确认（冻结队列的结构规则对应）',
   target='传入PanelManaGage；颜色由能力持有者职业决定',condition=CONDITION+'；本记录param6=0，须_isActive非0',duration='开局一次基础授予；不是持续时间或每WAVE',
   rationale='完整单效果玛那句＋唯一param0原生消费者；其他已识别产线显式零，实际sub为空或仅已核Bullet type9叶子，技能子弹消费者不构成ManaGet开局产线；旁句及未知槽不据零猜含义。',
   source=entry['source'],fields=[field_copy(a,entry,'开局基础玛那','ManaGet.param0')],siblings=[dict(record_id=c['record_id'],effect_type=c['effect_type'],consumer='Bullet，非type26 ManaGet开局消费者')for c in children],
   native_evidence='output/character_skills/type26_mana/native_evidence.json',eligibility_evidence='output/character_skills/type9_crit/native_evidence.json',limits=LIMITS,
   frozen_contexts=spec['contexts'],snapshot=scope()['snapshot']),None
 if family=='type5_line_damage':
  if fragment!=LINE or rec.get('skilltext')!=LINE+'。'or rec.get('skillid0')!=5:return None,'WHOLE_SENTENCE_GRAMMAR_CHANGED'
  if children:return None,'EXTRA_EXECUTED_EFFECT'
  if any(c['reference_field']!='skilltext'or c['cid']!=entry['reference_id']for c in spec['contexts']):return None,'SPECIAL_MOVE_REFERENCE_CHANGED'
  # Full raw source is checked as well as the projected link record. Its F0
  # execution carries this exact vector into BattleBossSkill (no pattern copy).
  raw,layer=C.Tables()('charainfo').get(entry['reference_id'])
  if C.location('charainfo',entry['reference_id'],layer,raw)!=spec['source']:return None,'RAW_SOURCE_CHANGED'
  eq=EQ.classify(entry['reference_id'],raw,layer)
  if eq['class']!=EQ.NO_PATTERN_FALLBACK or any(raw.get(f'pattern{i}')!=0 for i in range(9)):return None,'EXECUTION_SIDE_CHANGED'
  if any(raw.get(k)!=v or rec.get(k)!=v for k,v in dict(skillflag0_0=1025,skillflag0_1=0,skillflag1_0=0,skillflag1_1=0,iparam0=0,iparam1=0).items()):return None,'TYPE5_CONTROL_VECTOR_CHANGED'
  if any(raw.get(f'skillparam{i}')!=0 or rec.get(f'skillparam{i}')!=0 for i in [0,2,3,4,5,6,7,8,9]):return None,'TYPE5_CONTROL_VECTOR_CHANGED'
  ev=C.load_json(OUT/'type5_native_evidence.json')
  if ev['native_sha256']!=scope()['native_sha256']or ev['passed']!=ev['total']:return None,'NATIVE_EVIDENCE_CHANGED'
  hits=[a for a in answers if a['f']=='/skillparam1'and a['kind']=='技能基值倍率'and a['status']=='CONFIRMED_FORMULA_ONLY']
  if len(hits)!=1 or hits[0]['raw']!=rec.get('skillparam1')or raw['skillparam1']!=hits[0]['raw']or not isinstance(hits[0]['raw'],(int,float))or not math.isfinite(hits[0]['raw'])or hits[0]['raw']<=0:return None,'LOCAL_FORMULA_NOT_UNIQUE_OR_VALUE_CHANGED'
  a=hits[0]
  if a!=spec['local_answer']:return None,'FROZEN_LOCAL_ANSWER_CHANGED'
  return dict(template_id='p3b6_type5_intrinsic_line_damage',strength=STRENGTH,status='已确认（冻结队列的结构规则对应；伤害为公式）',
   target='本条固有技能子弹：玩家侧取敌方列表；进入直线轨迹矩形碰撞的合格目标，MULTIHIT逐目标请求',
   condition='F0角色本体必杀执行路径；原生攻击请求或动作结束触发一次发射；本条固有flag=1025（MULTIHIT＋ISMAGIC）。候选活动、非行为态11/12、场内、未命中过；技能dmgtype=1可纳入不可见目标，跳跃高度及碰撞范围仍筛选',
   duration='一次发射；子弹随速度沿x轴移动并逐次检测；不是持续秒数或保证命中数',
   rationale='完整片段仅包含直线范围/全敌目标资格/单次伤害三部分；type5技能子弹、对立阵营列表与矩形几何、MULTIHIT循环和唯一skillparam1公式均有原生消费支持。小不定义为固定倍率；sp3=0是明确推力输入，sp4=0经真实映射为横向半径0.1，未把零当无范围或未知槽中性。',
   source=entry['source'],fields=[field_copy(a,entry,'本条技能子弹的单次伤害输入公式','Exec_SHOOT_NORMAL.skillparam1')],siblings=[],
   native_evidence='output/character_skills/description_bindings/p3b6_batch/type5_native_evidence.json',eligibility_evidence=EQ.PATTERN_EVIDENCE,
   limits='仅本条固有基础效果；B含运行时技能基值与Chain，系数不是面板倍率或最终扣血。AttackSkill_AttackFlag可受运行时能力覆盖/追加，武器flag另OR；不保证实际命中所有敌人，不含外部修改/传授替换，不是实机验证。所有未解释字段照留，不据零推未知槽含义。',
   frozen_contexts=spec['contexts'],snapshot=scope()['snapshot']),None
 return None,'FAMILY_NOT_SUPPORTED'
