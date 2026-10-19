"""P3B8 finite own-F0 Boss sentence correspondence; no cross-table transfer."""
import functools,hashlib,math,re
from pathlib import Path
import common as C
import equivalence as EQ
import batch_bindings as B6
import p3b7_bindings as B7

OUT=C.ROOT/'output/character_skills/description_bindings/p3b8_boss'
SCOPE=Path(__file__).with_name('p3b8_binding_scope.json')
STRENGTH='受控结构规则审定＋原值与原生效果规则支持；限P3B8冻结队列，不是机器码解析日文'
CONTROL_ZERO=[*(f'skillparam{i}'for i in [0,2,3,4,5,6,7,8,9]),'skillflag0_1','skillflag1_0','skillflag1_1','iparam0','iparam1']

@functools.lru_cache(maxsize=1)
def scope():return C.load_json(SCOPE)
@functools.lru_cache(maxsize=1)
def tables():return C.Tables()
@functools.lru_cache(maxsize=1)
def membership():return B7.reference_membership()
@functools.lru_cache(maxsize=1)
def contexts():
 import json
 result={}
 def own(x,path,cid,out):
  if isinstance(x,dict):
   if x.get('resolved')and x.get('table')=='charainfo':out.append(dict(cid=cid,path=path,reference_field=x.get('reference_field'),reference_id=x.get('reference_id'),layer=x.get('layer'),source=x.get('source'),record_sha256=B6.digest(x.get('record'))))
   for k,v in x.items():
    if k not in ['record','source','charainfo_source']:own(v,path+'/'+k,cid,out)
  elif isinstance(x,list):
   for i,v in enumerate(x):own(v,path+'/'+str(i),cid,out)
 for p in map(json.loads,(C.ROOT/'output/character_skills/links/character_skills.jsonl').open(encoding='utf-8')):
  cc=[];own(p,'',p['cid'],cc)
  result[p['cid']]=dict(own_charainfo=cc,related_groups=[g for g in p['groups']if g['group']in ['denju','denju_lb','heroic']])
 return result

@functools.lru_cache(maxsize=6)
def raw_audit(provider):
 """CID identities and related namespaces, never ordinary skillid numeric aliases."""
 tab=provider('charainfo');result={};owners={}
 for cid in sorted(tab.ids()):
  raw,layer=tab.get(cid)
  for i in range(9):
   pat=raw.get(f'pattern{i}')
   if pat:owners.setdefault(pat,set()).add(cid)
 heroes={}
 for ident in sorted(provider('heroicskilllist').ids()):
  h,hl=provider('heroicskilllist').get(ident);pats=[h.get(k)for k in ['boss_pattern','boss_pattern2','boss_pattern3']if h.get(k)]
  confirmed={cid for p in pats for cid in owners.get(p,[])}
  # Derived ownership is only a related-context guard, never a formula reference.
  related=confirmed or {(p//100)%100000 for p in pats}
  for cid in related:heroes.setdefault(cid,[]).append(dict(table='heroicskilllist',record_id=ident,relation='OWN_PATTERN'if confirmed else'INFERRED_PATTERN_CID_ONLY',layer=hl,source=C.location('heroicskilllist',ident,hl,h),raw_sha256=B6.digest(h)))
 for key in scope()['records']:
  cid=int(key.split('|')[1]);raw,layer=tab.get(cid)
  original=[]
  for ll,idx in [('CACHE',tab.cache),('APK',tab.apk)]:
   original.extend(dict(layer=ll,selected=ll==layer,raw_sha256=B6.digest(r))for r in idx.get(cid,[]))
  related=[]
  for table in ['denju','denju_lblist']:
   rec,rl=provider(table).get(cid)
   if rec is not None:related.append(dict(table=table,record_id=cid,relation='denju.denju_id==cid'if table=='denju'else'denju_limit_break_info.cid==cid',layer=rl,source=C.location(table,cid,rl,rec),raw_sha256=B6.digest(rec)))
  result[cid]=dict(selected_source=C.location('charainfo',cid,layer,raw)if raw else None,selected_raw_sha256=B6.digest(raw),all_original_rows=original,related_records=related+heroes.get(cid,[]))
 return result

@functools.lru_cache(maxsize=1)
def native_ready():
 path=OUT/'native_evidence.json';ev=C.load_json(path)
 return ev['passed']==ev['total']==9 and ev['native_sha256']==scope()['native_sha256']and ev['metadata_sha256']==scope()['metadata_sha256']and C.sha256_file(path)==scope()['native_evidence_sha256']and all(C.sha256_file(C.ROOT/x['path'])==x['sha256']for x in ev['reused_evidence'])

def bind(entry,fragment,answers,children,actual_contexts=None,actual_raw_audit=None,actual_membership=None):
 key=f"{entry.get('table')}|{entry.get('reference_id')}";spec=scope()['records'].get(key)
 if not spec:return None,'OUTSIDE_P3B8_FROZEN_QUEUE'
 cid=entry['reference_id'];rec=entry.get('record')or {};family=spec['family'];typ=5 if family=='type5_line'else 11
 pattern=r'直線範囲上にいる(全ての敵|敵[１1]体)に(小|中|大)ダメージを与える'if typ==5 else r'味方全体の(HP|ＨＰ)を(小|中)回復する'
 match=re.fullmatch(pattern,fragment)
 if not match or rec.get('skillid0')!=typ:return None,'WHOLE_SENTENCE_OR_TYPE_CHANGED'
 if rec.get('skilltext')not in [fragment,fragment+'。']:return None,'WHOLE_SOURCE_TEXT_CHANGED'
 if any(k not in rec or rec[k]is None or isinstance(rec[k],bool)or rec[k]!=0 for k in CONTROL_ZERO):return None,'CONTROL_NOT_EXPLICIT_ZERO'
 flag=rec.get('skillflag0_0')
 if isinstance(flag,bool)or flag is None or flag not in ([0,1,1024,1025]if typ==5 else[0]):return None,'FLAG_CONTROL_CHANGED'
 if typ==5 and bool(flag&1)!=bool(match[1]=='全ての敵'):return None,'FLAG_SENTENCE_TARGET_MISMATCH'
 if children:return None,'EXTRA_EXECUTION_CHILD'
 if C.SNAPSHOT_ID!=scope()['snapshot']or entry.get('layer')!='APK':return None,'SNAPSHOT_OR_LAYER_CHANGED'
 if entry.get('source')!=spec['source']or B6.digest(rec)!=spec['entry_sha256']:return None,'FROZEN_ROOT_OR_SOURCE_CHANGED'
 raw,layer=tables()('charainfo').get(cid)
 if not raw or layer!='APK'or C.location('charainfo',cid,layer,raw)!=spec['source']or B6.digest(raw)!=spec['raw_sha256']:return None,'CURRENT_RAW_SOURCE_CHANGED'
 if any(k not in raw or raw[k]is None or raw[k]!=0 for k in [f'pattern{i}'for i in range(9)])or EQ.classify(cid,raw,layer)['class']!=EQ.NO_PATTERN_FALLBACK:return None,'OWN_F0_EXECUTION_CHANGED'
 cc=contexts().get(cid)if actual_contexts is None else actual_contexts
 if cc!=spec['contexts']:return None,'OWN_OR_RELATED_CONTEXT_CHANGED'
 if len(cc['own_charainfo'])!=1 or cc['own_charainfo'][0]['reference_id']!=cid or cc['own_charainfo'][0]['reference_field']!='skilltext':return None,'NOT_OWN_SKILLTEXT_REFERENCE'
 mm=membership()['identity']if actual_membership is None else actual_membership
 if mm!=scope()['reference_scope_identity']:return None,'PLAYER_SCOPE_IDENTITY_CHANGED'
 rr=raw_audit(tables()).get(cid)if actual_raw_audit is None else actual_raw_audit
 if rr!=spec['raw_audit']:return None,'RAW_IDENTITY_OR_RELATED_REFERENCE_CHANGED'
 hits=[a for a in answers if a['f']=='/skillparam1']
 if len(hits)!=1:return None,'LOCAL_FORMULA_NOT_UNIQUE'
 a=hits[0];value=a['raw']
 if isinstance(value,bool)or not isinstance(value,(int,float))or not math.isfinite(value)or value<=0 or value!=rec.get('skillparam1')or value!=raw.get('skillparam1')or a['status']!='CONFIRMED_FORMULA_ONLY'or a['scope']!='BY_TYPE_EXTRAPOLATED':return None,'LOCAL_FORMULA_VALUE_STATUS_SCOPE_CHANGED'
 if a!=spec['local_answer']:return None,'FROZEN_LOCAL_FORMULA_CHANGED'
 if not native_ready():return None,'NATIVE_EVIDENCE_CHANGED'
 if typ==5:
  multi=bool(flag&1)
  target='本条固有技能子弹：玩家侧取敌方列表；进入直线轨迹矩形碰撞的合格目标；'+('MULTIHIT逐目标请求'if multi else'单目标分支仅取碰撞结果首项，至多一次Attack请求')
  condition=f'F0角色本体必杀；攻击request或motion_end触发一次发射；固有flag={flag}（MULTIHIT={int(multi)}，ISMAGIC={int(bool(flag&1024))}）。候选活动、非行为态11/12、场内、未命中过；技能dmgtype=1可纳入不可见对象，跳跃/碰撞仍筛选'
  duration='一次发射；子弹随x向速度检测直线轨迹；不是持续秒数或保证命中数'
  rationale='完整纯直线单次伤害句、四flag实际单/多目标分支与既有几何/资格/一次发射证据对应。小/中/大不定义固定倍率；sp3=0为推力输入，sp4=0经真实映射为横向半径0.1。'
  semantic='本条技能子弹的伤害输入公式';path='Exec_SHOOT_NORMAL.skillparam1'
  limits='仅固有基础效果；B含运行时技能基值和Chain，系数不是面板倍率或最终扣血。运行时能力可覆盖/追加攻击flag，武器flag另OR；不保证命中全部敌人或最近目标，不含传授/英雄替换。'
 else:
  target='施法者同阵营的合格成员，可含自身；iParam0=0保留全部职业；逐目标发出Heal请求'
  condition='F0角色本体必杀，request或motion_end且尚未执行；mode1/act0。GetMemberList同阵营、onlyActive=1、onlyAlive=1；活动且（_isEnableAppearAnim字节为0或本分支读取的_heroWork字节非0），IsAlive要求HP>=1且state!=12。onlyVisible=0、onlyInGround=0，不附加可见/场内筛选'
  duration='一次执行、每个合格成员一次回复请求；不是周期回复或持续时间'
  rationale='完整全体HP回复句与type11真实mode1同阵营列表、活动/出场/hero及存活过滤、零职业掩码和共同Heal消费者对应；小/中及HP字形不产生数值。sp1原公式、sp2/flag的原上限规则原样保留。'
  semantic='本条技能的回复输入公式';path='Exec_HEAL(mode1,act0).skillparam1'
  limits='回复输入为floor/clamp(float32(B×skillparam1))，B=getBasicSkillAttack(true)仍是运行时基数；不是具体HP或最终回血量。HealSkill_HealFlag可有运行时增强；sp2=0不代表最终HP上限为0。只覆盖本记录固有执行，不含外部效果/传授/英雄替换。'
 return dict(template_id='p3b8_'+family+'_intrinsic',strength=STRENGTH,status='已确认（冻结队列的结构规则对应；数值为公式）',target=target,condition=condition,duration=duration,rationale=rationale,source=entry['source'],fields=[B6.field_copy(a,entry,semantic,path)],siblings=[],native_evidence='output/character_skills/description_bindings/p3b8_boss/native_evidence.json',eligibility_evidence=EQ.PATTERN_EVIDENCE,limits=limits+'未解释字段和另域denju原文仍保留；有界对象/分配/容器/保护值getter夹具及请求拦截，不是实机/完整引擎。',frozen_contexts=spec['contexts'],snapshot=scope()['snapshot']),None
