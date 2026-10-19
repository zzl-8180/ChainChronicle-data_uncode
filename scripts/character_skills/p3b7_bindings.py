"""Finite P3B7 startup ManaGet sentence family; preserves earlier decisions."""
import collections,functools,hashlib,json,re
from pathlib import Path
import common as C
import batch_bindings as B6
from type26_mana import KIND,CONDITION,LIMITS,published_native

OUT=C.ROOT/'output/character_skills/description_bindings/p3b7_batch'
SCOPE=Path(__file__).with_name('p3b7_binding_scope.json')
STRENGTH='受控结构规则审定＋原值与原生效果规则支持；限P3B7冻结队列，不是机器码解析日文'
FORBIDDEN=frozenset([26,1073,1077])
ZERO_FIELDS=['param1','param2','param3','param4','param5','param6','param7','iParam0','iParam1']

@functools.lru_cache(maxsize=1)
def scope():return C.load_json(SCOPE)
@functools.lru_cache(maxsize=1)
def tables():return C.Tables()
@functools.lru_cache(maxsize=1)
def reference_membership():
 """Current output scope comes from real roster/links/profiles, not enemy flags."""
 playable={r['cid']:r for r in C.load_json(C.ROSTER_JSON)}
 other={r['cid']:r for r in C.load_json(C.ROSTER_OTHER_JSON)}
 def ids(path):return frozenset(json.loads(s)['cid']for s in path.open(encoding='utf-8'))
 profiles=ids(C.ROOT/'output/character_skills/profiles/profiles.jsonl')
 links=ids(C.ROOT/'output/character_skills/links/character_skills.jsonl')
 identity=dict(playable_count=len(playable),playable_cids_sha256=B6.digest(sorted(playable)),profiles_cids_sha256=B6.digest(sorted(profiles)),links_cids_sha256=B6.digest(sorted(links)),playable_roster_sha256=B6.digest(list(playable.values())),other_roster_sha256=B6.digest(list(other.values())))
 return dict(playable=playable,other=other,profiles=profiles,links=links,identity=identity)

@functools.lru_cache(maxsize=4)
def raw_charainfo_references(table_set):
 """Every selected raw skillid[1+] reference, including non-roster objects.

 Cached per table provider, so an independent Table overlay triggers a fresh
 scan even if the ordinary generation snapshot was already read.
 """
 result=collections.defaultdict(list);tab=table_set('charainfo');members=reference_membership()
 for cid in sorted(tab.ids()):
  raw,layer=tab.get(cid)
  for slot,target in enumerate(raw.get('skillid')or []):
   if slot<1 or f'skilllist|{target}'not in scope()['records']:continue
   playable=members['playable'].get(cid);other=members['other'].get(cid)
   included=cid in members['playable']and cid in members['profiles']and cid in members['links']
   source=dict(C.location('charainfo',cid,layer,raw),canonical_record_sha256=B6.digest(raw))
   decoded='output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw'if layer=='CACHE'else'output/base_master/_mdCharacter.json'
   result[target].append(dict(cid=cid,slot=f'skillid[{slot}]',layer=layer,decoded_json_file=decoded,source=source,in_playable_roster=playable is not None,in_profiles=cid in members['profiles'],in_links=cid in members['links'],roster_category=playable.get('category')if playable else None,other_category=other.get('category')if other else None,roster_record_sha256=B6.digest(playable)if playable else None,other_record_sha256=B6.digest(other)if other else None,raw_is_enemy=raw.get('is_enemy'),raw_rarity=raw.get('rarity'),included_in_player_output=included,exclusion_reason=None if included else 'OUTSIDE_CURRENT_2236_PLAYER_ROSTER_LINKS_PROFILES; raw slot fact only, no enemy execution or player-slot semantics inferred'))
 return result
@functools.lru_cache(maxsize=1)
def reverse_subs():
 """All selected same-namespace raw parents, including parents absent in links."""
 result=collections.defaultdict(list);tab=tables()('skilllist')
 for ident in sorted(tab.ids()):
  raw,layer=tab.get(ident)
  for i,sub in enumerate(raw.get('sub')or []):
   if f'skilllist|{sub}'in scope()['records']:
    result[sub].append(dict(parent_id=ident,sub_index=i,source=C.location('skilllist',ident,layer,raw)))
 return result

def bind(entry,fragment,answers,children,actual_contexts=None,actual_parents=None):
 key=f"{entry.get('table')}|{entry.get('reference_id')}";spec=scope()['records'].get(key)
 if not spec:return None,'OUTSIDE_P3B7_FROZEN_QUEUE'
 rec=entry.get('record')or {}
 match=re.fullmatch(r'マナを([１２３123])つ持った状態で戦闘を開始する',fragment)
 if not match or rec.get('ability')!=26:return None,'WHOLE_SENTENCE_OR_TYPE_CHANGED'
 if any(k not in rec or rec[k]is None or rec[k]!=0 for k in ZERO_FIELDS):return None,'OTHER_MANA_LINE_OR_GATE_NOT_EXPLICIT_ZERO'
 cc=B6.contexts().get(key,[])if actual_contexts is None else actual_contexts
 if not cc or any(c['reference_field']not in ['skillid[1]','skillid[2]']or not re.fullmatch(r'/groups/\d+/records/\d+',c['link_path'])for c in cc):return None,'NON_ORDINARY_DIRECT_REFERENCE'
 if cc!=spec['contexts']:return None,'ALL_REFERENCE_CONTEXTS_CHANGED'
 if reference_membership()['identity']!=scope()['reference_scope_identity']:return None,'RAW_REFERENCE_OUTPUT_SCOPE_CHANGED'
 if raw_charainfo_references(tables()).get(entry['reference_id'],[])!=spec['raw_charainfo_references']:return None,'RAW_CHARAINFO_DIRECT_REFERENCES_CHANGED'
 parents=reverse_subs().get(entry['reference_id'],[])if actual_parents is None else actual_parents
 if parents!=spec['reverse_subs'] or parents:return None,'NEW_REVERSE_SUB_REFERENCE'
 declared=rec.get('sub')
 if not isinstance(declared,list)or len(set(declared))!=len(declared):return None,'INVALID_OR_DUPLICATE_DECLARED_SUB'
 if len(children)!=len(declared)or collections.Counter(c.get('record_id')for c in children)!=collections.Counter(declared):return None,'MISSING_OR_DUPLICATE_CHILD'
 if [c['record_id']for c in children]!=declared:return None,'CHILD_ORDER_CHANGED'
 if len(spec['children'])!=len(children):return None,'FROZEN_CHILD_COUNT_CHANGED'
 for ch,expected in zip(children,spec['children']):
  if ch.get('table')!='skilllist'or ch.get('link_kind')!='sub_effect':return None,'CHILD_NAMESPACE_OR_LINK_CHANGED'
  raw,layer=tables()('skilllist').get(ch['record_id'])
  if not raw:return None,'UNRESOLVED_CHILD'
  if ch.get('effect_type')in FORBIDDEN or raw.get('ability')in FORBIDDEN:return None,'ADDITIONAL_START_MANA_CONSUMER'
  if 'sub'not in raw or raw['sub']!=[]:return None,'NON_LEAF_OR_MISSING_CHILD_SUB'
  if 'children'in ch and ch['children']:return None,'NESTED_PROFILE_CHILD'
  source=C.location('skilllist',ch['record_id'],layer,raw)
  if ch.get('source')!=source or source!=expected['source']or raw.get('ability')!=expected['effect_type']or ch.get('effect_type')!=expected['effect_type']:return None,'CHILD_SOURCE_OR_TYPE_CHANGED'
 if C.SNAPSHOT_ID!=scope()['snapshot']or entry.get('layer')!='APK':return None,'SNAPSHOT_OR_LAYER_CHANGED'
 if entry.get('source')!=spec['source']or B6.digest(rec)!=spec['entry_sha256']:return None,'FROZEN_ROOT_OR_SOURCE_CHANGED'
 raw,layer=tables()('skilllist').get(entry['reference_id'])
 if not raw or C.location('skilllist',entry['reference_id'],layer,raw)!=spec['source']or B6.digest(raw)!=spec['source']['raw_record_sha256']:return None,'CURRENT_RAW_SOURCE_CHANGED'
 hits=[a for a in answers if a['f']=='/param0']
 if len(hits)!=1 or hits[0]['kind']!=KIND or hits[0]['status']!='CONFIRMED_NUMERIC'or hits[0]['raw']!=rec.get('param0')or hits[0]['raw']!=int(match[1]):return None,'LOCAL_PARAM0_OR_TEXT_NUMBER_MISMATCH'
 a=hits[0]
 if a!=spec['local_answer']:return None,'FROZEN_LOCAL_ANSWER_CHANGED'
 ev=C.load_json(OUT/'native_evidence.json');old=published_native()
 if ev['passed']!=ev['total']or ev['total']!=8 or ev['native_sha256']!=scope()['native_sha256']or hashlib.sha256((OUT/'native_evidence.json').read_bytes()).hexdigest()!=scope()['native_evidence_sha256']or old['passed']!=old['total']or old['native_sha256']!=scope()['native_sha256']:return None,'NATIVE_EVIDENCE_CHANGED'
 return dict(template_id='p3b7_type26_start_mana_exact_digit',strength=STRENGTH,status='已确认（冻结队列的结构规则对应）',
  target='传入PanelManaGage；颜色由本条能力持有者职业决定',condition=CONDITION+'；本记录param6=0，须_isActive非0',duration='开局一次基础授予；不是持续时间或每WAVE',
  rationale='完整开局基础玛那句与唯一param0数值一致。其他已识别产线和门控显式零；实际sub均为有来源的叶子且无26/1073/1077。PartyAbilityInit的ManaGet/TenmaMana/MajinMana各按真实缓存映射和精确类型筛选，其他sub不进入这三条直接能力产线；未知槽不猜中性，旁句不升级。',
  source=entry['source'],fields=[B6.field_copy(a,entry,'本记录开局基础玛那','ManaGet.param0')],
  siblings=[dict(record_id=c['record_id'],effect_type=c['effect_type'],source=c['source'],consumer='精确类型筛选排除于26/1073/1077三条直接能力开局产线；其他效果未由此确认')for c in children],
  native_evidence='output/character_skills/type26_mana/native_evidence.json',eligibility_evidence='output/character_skills/description_bindings/p3b7_batch/native_evidence.json',
  limits=LIMITS+'；继续战斗、w5系统授予、Tenma/Majin及ManaGet其他产线确实存在；本对应仅本记录param0基础调用，不合计其他系统/成员/能力或外部加成。原生使用明确运行时对象/枚举/泛型接口夹具及保护值解码stub，不是实机。',
  frozen_contexts=spec['contexts'],snapshot=scope()['snapshot']),None
