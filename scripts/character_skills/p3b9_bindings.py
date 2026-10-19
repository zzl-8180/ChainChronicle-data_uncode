"""Finite type67 pure conditional sentences; existing numeric answers unchanged."""
import collections,functools,hashlib,json,re
from pathlib import Path
import common as C
import batch_bindings as B6
import p3b7_bindings as B7
OUT=C.ROOT/'output/character_skills/description_bindings/p3b9_batch'
SCOPE=Path(__file__).with_name('p3b9_binding_scope.json')
STRENGTH='受控结构规则审定＋原值与原生效果规则支持；限P3B9冻结type67队列，不是机器码解析日文'
PATTERN=r'戦場に(?P<exclude>自身以外の)?<(?P<target>[^<>]+)>(?P<home>所属)?の味方がいると自身の(?P<effects>(?:攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力)(?:と(?:攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力))*)が上がる'
TERMS={'攻撃力':('/param1','attack'),'防御力':('/param3','defence'),'移動速度':('/param2','move'),'クリティカル発生率':('/param6','crit_rate'),'クリティカル威力':('/param7','crit_dmg')}
JOBS={'戦士':1,'弓使い':2,'魔法使い':4,'僧侶':8,'騎士':16}
ZERO=['param4','param5','param9','iParam1','flag0_0','flag0_1','flag1_0','flag1_1']
ALL=[*(f'param{i}'for i in range(10)),'iParam0','iParam1','flag0_0','flag0_1','flag1_0','flag1_1']
@functools.lru_cache(maxsize=1)
def scope():return C.load_json(SCOPE)
@functools.lru_cache(maxsize=1)
def tables():return C.Tables()
@functools.lru_cache(maxsize=1)
def membership():return B7.reference_membership()
def original_rows(tab,ident):
 return [dict(layer=layer,raw_sha256=B6.digest(r))for layer,idx in [('CACHE',tab.cache),('APK',tab.apk)]for r in idx.get(ident,[])]
@functools.lru_cache(maxsize=4)
def raw_audit(provider):
 """Selected raw references, out-of-roster owners and reverse parents included."""
 targets={int(k.split('|')[1])for k in scope()['records']};mm=membership();ct=provider('charainfo');st=provider('skilllist');refs=collections.defaultdict(list);parents=collections.defaultdict(list)
 for cid in sorted(ct.ids()):
  raw,layer=ct.get(cid)
  for i,sid in enumerate(raw.get('skillid')or []):
   if i<1 or sid not in targets:continue
   playable=mm['playable'].get(cid);other=mm['other'].get(cid)
   included=cid in mm['playable']and cid in mm['profiles']and cid in mm['links']
   refs[sid].append(dict(cid=cid,slot=f'skillid[{i}]',source=C.location('charainfo',cid,layer,raw),raw_sha256=B6.digest(raw),original_rows=original_rows(ct,cid),in_playable_roster=cid in mm['playable'],in_profiles=cid in mm['profiles'],in_links=cid in mm['links'],roster_record_sha256=B6.digest(playable)if playable else None,other_record_sha256=B6.digest(other)if other else None,included=included,exclusion_reason=None if included else'OUTSIDE_CURRENT_PLAYER_SCOPE_RAW_REFERENCE_ONLY',declared_identity={k:dict(present=k in raw,value=raw.get(k))for k in ['jobtype','home','battle_home','is_enemy','rarity']}))
 for ident in sorted(st.ids()):
  raw,layer=st.get(ident)
  for i,sid in enumerate(raw.get('sub')or []):
   if sid in targets:parents[sid].append(dict(parent_id=ident,sub_index=i,source=C.location('skilllist',ident,layer,raw),raw_sha256=B6.digest(raw),original_rows=original_rows(st,ident)))
 result={}
 for sid in sorted(targets):
  raw,layer=st.get(sid)
  result[sid]=dict(root_source=C.location('skilllist',sid,layer,raw)if raw else None,root_sha256=B6.digest(raw),root_original_rows=original_rows(st,sid),raw_charainfo_references=refs[sid],reverse_sub_references=parents[sid])
 return result
@functools.lru_cache(maxsize=1)
def native_ready():
 ev=C.load_json(OUT/'native_evidence.json')
 return ev['passed']==ev['total']==9 and C.sha256_file(OUT/'native_evidence.json')==scope()['native_evidence_sha256'] and all(ev[k]==scope()[k]for k in ['native_sha256','metadata_sha256'])and all(C.sha256_file(C.ROOT/x['path'])==x['sha256']for x in ev['reused_evidence'])

def bind(entry,fragment,answers,children,actual_contexts=None,actual_audit=None,actual_membership=None):
 key=f"{entry.get('table')}|{entry.get('reference_id')}";spec=scope()['records'].get(key)
 if not spec:return None,'OUTSIDE_P3B9_FROZEN_QUEUE'
 rec=entry.get('record')or {};match=re.fullmatch(PATTERN,fragment)
 if not match or rec.get('ability')!=67:return None,'WHOLE_SENTENCE_OR_TYPE_CHANGED'
 if fragment!=spec['fragment']or rec.get('text')not in [fragment,fragment+'。','◆'+fragment,'◆'+fragment+'。']:return None,'WHOLE_SOURCE_TEXT_CHANGED'
 if any(k not in rec or rec[k]is None or isinstance(rec[k],bool)for k in ALL):return None,'MISSING_NULL_BOOL_CONTROL'
 # Reject changed input before interpreting any selector (e.g. int(param8)).
 if C.SNAPSHOT_ID!=scope()['snapshot']or entry.get('layer')!='APK':return None,'SNAPSHOT_OR_LAYER_CHANGED'
 if entry.get('source')!=spec['source']or B6.digest(rec)!=spec['entry_sha256']:return None,'FROZEN_ROOT_OR_SOURCE_CHANGED'
 if any(rec[k]!=0 for k in ZERO):return None,'CONTROL_NOT_EXPLICIT_ZERO'
 if rec.get('sub')!=[]or children:return None,'ACTUAL_SUB_OR_CHILD_CHANGED'
 terms=match['effects'].split('と');wanted=[TERMS[t][0]for t in terms]
 if len(set(wanted))!=len(wanted):return None,'DUPLICATE_SEMANTIC_TERM'
 if match['home']:
  homes=C.load_json(C.ROOT/'output/character_skills/skilllist_types/filter_dictionary.json')['home']['table']['ids']
  # Dictionary structure is frozen by native_ready; source labels never invent codes.
  if rec['iParam0']!=0 or homes.get(str(int(rec['param8'])))!=match['target']:return None,'HOME_FILTER_LABEL_MISMATCH'
 elif rec['param8']!=0 or rec['iParam0']!=JOBS.get(match['target']):return None,'JOB_FILTER_LABEL_MISMATCH'
 if rec['param0']not in [1.,2.]:return None,'COUNT_THRESHOLD_CHANGED'
 raw,layer=tables()('skilllist').get(entry['reference_id'])
 if not raw or layer!='APK'or C.location('skilllist',entry['reference_id'],layer,raw)!=spec['source']or B6.digest(raw)!=spec['source']['raw_record_sha256']:return None,'CURRENT_RAW_SOURCE_CHANGED'
 cc=B6.contexts().get(key,[])if actual_contexts is None else actual_contexts
 if cc!=spec['contexts']:return None,'ALL_REFERENCE_CONTEXTS_CHANGED'
 if not cc or any(not re.fullmatch(r'/groups/\d+/records/\d+',c['link_path'])or not re.fullmatch(r'skillid\[[1-9]\d*\]',c['reference_field'])for c in cc):return None,'NON_ORDINARY_DIRECT_REFERENCE'
 mm=membership()['identity']if actual_membership is None else actual_membership
 if mm!=scope()['reference_scope_identity']:return None,'PLAYER_SCOPE_IDENTITY_CHANGED'
 audit=raw_audit(tables()).get(entry['reference_id'])if actual_audit is None else actual_audit
 if audit!=spec['raw_audit']:return None,'RAW_IDENTITY_REFERENCES_OR_PARENTS_CHANGED'
 if audit['reverse_sub_references']:return None,'REVERSE_SUB_CONTEXT_NOT_APPROVED'
 # Freeze every local object, including condition/neutral fields, with strict JSON
 # type identity. A duplicate answer or bool-for-number is not equal evidence.
 if B6.digest(answers)!=spec['local_answers_sha256']:return None,'LOCAL_ANSWER_OBJECT_ORDER_OR_DUPLICATE_CHANGED'
 bound=[];condition_fields=[]
 for term in terms:
  f,path=TERMS[term];hits=[a for a in answers if a['f']==f]
  if len(hits)!=1 or hits[0]['raw']!=rec[f[1:]]or hits[0]['status']!='CONFIRMED_NUMERIC'or hits[0]['scope']not in ['IN_REVIEWED_VIEW','BY_TYPE_EXTRAPOLATED']:return None,'LOCAL_TARGET_VALUE_STATUS_SCOPE_CHANGED'
  bound.append(B6.field_copy(hits[0],entry,term,'BattleParam type67 '+path))
 for f in ['/param0','/iParam0','/flag0_0','/param8']:
  a=next(a for a in answers if a['f']==f);condition_fields.append(B6.field_copy(a,entry,'原生计数条件','CalcCharaNum'))
 if not native_ready():return None,'NATIVE_EVIDENCE_CHANGED'
 selector=f"所属 param8={rec['param8']}（{match['target']}；比较home或battle_home）"if match['home']else f"职业位图 iParam0={rec['iParam0']}（{match['target']}）"
 threshold=int(rec['param0'])
 condition=f'本记录由冻结普通skillid[3]引用且实际装载到持有者BattleParam；页面引用不证明解锁/装载。五路径按同阵营GetMemberList(onlyActive=0, onlyAlive=1, onlyInGround=0)取列表，真实IsAlive为HP>=1且state!=12；该重载不按可见、场内、出场/hero筛选。CalcCharaNum随后要求_isActive!=0；{selector}，武器筛选flag0_0=0为不筛武器。职业位图非0时还须阵营聚合职业位图与iParam0相交。N为通过实际列表/快速门槛及各筛选的原生计数，要求N>=int(param0)={threshold}（有限值向零截断，比较含等于）。'
 if match['exclude']:
  relation='原文写自身以外；原生不直接移除持有者。仅当持有者当前也满足全部筛选且实际被计入N时，N>=2等价其余合格成员>=1；否则仍按N>=2。冻结原表身份命中不保证动态运行时身份永远命中。'
 elif threshold==2:
  relation='原文仅写有该类味方，未写原生所需合格计数>=2；本条保留阈值2并明示文本差异，不改为1，也不伪称原文明确排除自己。持有者合格且计入时才可将其余计数理解为>=1。'
 else:relation='原文未排除持有者；N>=1即可，持有者若当前合格且实际计入，也可提供该计数。'
 return dict(template_id='p3b9_type67_conditional_self_stats',strength=STRENGTH,status='已确认（冻结队列的结构规则对应；原生计数条件明示）',target='本记录实际装载者自身的原生单项贡献',condition=condition+relation,duration='每次读取按当时列表和筛选判定本项贡献；没有计时秒数，不补0秒',rationale='完整纯句所有目标项分别对应67五路径唯一现成消费者；本体无sub且所有反向sub/原表引用已冻结。数值、目标筛选与计数门槛分别有原值和原生规则；不是关键词命中。未写的五路径项仅依已证消费者确认本项中性，未知槽仍未知。',source=entry['source'],fields=bound,condition_fields=condition_fields,siblings=[],text_condition_relation=relation,frozen_declared_owner_identity=spec['declared_owners'],native_evidence='output/character_skills/description_bindings/p3b9_batch/native_evidence.json',eligibility_evidence='output/character_skills/skilllist_types/composite_chains.json',limits='仅这条type67记录条件成立时的乘数/加算贡献，不是所有技能叠加后的角色总属性、最终伤害或暴击总概率；防御为受伤量倍率，非固定防御；暴击率为百分点加算、暴伤为系数加算。实际同阵营列表、聚合职业位图和动态职业/所属/装载为运行时前提。原生含明确列表/单例/保护值getter夹具，不是实机或完整战斗引擎；其他未知字段保留。',frozen_contexts=spec['contexts'],snapshot=scope()['snapshot']),None
