"""P3B8 C self-check and reproducible ledgers; never an independent D result."""
import collections,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
from unittest.mock import patch
import common as C
import p3b8_bindings as B

BASE=C.ROOT/'output/character_skills';OUT=B.OUT;BEFORE=C.ROOT/'work/character_skills_p3b8/before'
def rows(p):return [json.loads(s)for s in Path(p).open(encoding='utf-8')]
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def main():
 C.enable_utf8_console();checks=[]
 def ck(name,ok,**kw):checks.append(dict(name=name,passed=bool(ok),**kw))
 old=rows(BEFORE/'records.jsonl');now=rows(BASE/'profiles/records.jsonl');oldp=rows(BEFORE/'profiles.jsonl');newp=rows(BASE/'profiles/profiles.jsonl')
 before={r['rec_key']:r for r in old};after={r['rec_key']:r for r in now}
 def answers(rr):return collections.Counter((r['rec_key'],h['table'],h['record_id'],canon(a))for r in rr for h in [r]+r['children']for a in h['answers'])
 aa,ab=answers(old),answers(now)
 ck('all82013_complete_answers_and_duplicate_counts',aa==ab,before=sum(aa.values()),after=sum(ab.values()))
 ck('277_used_rules_287_source_rules_exact',C.load_json(BEFORE/'rules.json')==C.load_json(BASE/'profiles/rules.json')and len(C.load_json(BASE/'profiles/rules.json'))==277 and C.load_json(BASE/'profiles/summary.json')['rule_source']['rule_count']==287)
 ck('record_order_keys_and_duplicates_exact',[r['rec_key']for r in old]==[r['rec_key']for r in now])
 new=[];good=True;bindings=0;ba=0;bf=0
 for r in old:
  n=after[r['rec_key']];ba+=len(r['baseline_answers']);bf+=sum(f['status']=='BASELINE_DESCRIPTION_ANSWER'for f in r['fragments'])
  if len(r['fragments'])!=len(n['fragments']):good=False
  for a,b in zip(r['fragments'],n['fragments']):
   if a.get('binding'):bindings+=1
   if a==b:continue
   if a.get('binding')or a['t']!=b['t']or b.get('binding',{}).get('strength')!=B.STRENGTH or f"{r['table']}|{r['record_id']}"not in B.scope()['records']:good=False
   else:new.append(dict(rec_key=r['rec_key'],table=r['table'],record_id=r['record_id'],source=r['source'],before=a,after=b))
  if any(r[k]!=n[k]for k in set(r)-{'fragments'}):good=False
 ck('112_old_bindings_101_baseline_answers_31_fragments_non_targets_exact',good and bindings==112 and ba==101 and bf==31,old_bindings=bindings,baseline_answers=ba,baseline_fragments=bf,new_fragments=len(new))
 uses=collections.defaultdict(list)
 for p in newp:
  for g in p['groups']:
   for ref in g['records']:uses[ref['rec_key']].append(dict(cid=p['cid'],name=p['name'],group=g['group'],reference_field=ref['reference_field'],character_source=p['charainfo_source']))
 docs={}
 def direct(source,table):
  path=C.ROOT/source['original_file']if source['layer']=='APK'else C.DECODED/(C.CACHE_TABLES[table][3]+'.data5.json.raw')
  if path not in docs:docs[path]=json.loads(path.read_bytes())
  raw=docs[path]
  for x in source['json_pointer'].strip('/').split('/'):raw=raw[int(x)]if isinstance(raw,list)else raw[x]
  return raw,hashlib.sha256(canon(raw).encode()).hexdigest(),str(path.relative_to(C.ROOT)).replace('\\','/')
 ledger=[];rawchecks=[];related=[]
 for item in new:
  key=f"charainfo|{item['record_id']}";spec=B.scope()['records'][key];raw,sha,path=direct(item['source'],'charainfo');a=item['after']['binding']['fields'][0];local=next(a for a in after[item['rec_key']]['answers']if a['f']=='/skillparam1')
  ok=sha==spec['raw_sha256']==item['source']['raw_record_sha256']and raw['skillparam1']==a['raw']and all(a[k]==local[k]for k in ['f','raw','value','kind','unit','status','rule_key'])and a['evidence_scope']==local['scope']=='BY_TYPE_EXTRAPOLATED'and local['status']=='CONFIRMED_FORMULA_ONLY'
  rawchecks.append(dict(cid=item['record_id'],source=item['source'],decoded_json_file=path,canonical_sha256=sha,raw_skillparam1=raw['skillparam1'],passed=ok))
  for rr in spec['raw_audit']['related_records']:
   dr,ds,dp=direct(rr['source'],rr['table']);related.append(dict(cid=item['record_id'],relation=rr['relation'],table=rr['table'],source=rr['source'],decoded_json_file=dp,canonical_sha256=ds,raw_record=dr,passed=ds==rr['raw_sha256']))
  ledger.append(dict(item,family=spec['family'],raw_record=raw,all_contexts=spec['contexts'],raw_audit=spec['raw_audit'],page_uses=uses[item['rec_key']]))
 ck('stdlib_source_pointers_raw_formulas_scope_related_namespace_sources',all(x['passed']for x in rawchecks+related),roots=len(rawchecks),related_records=len(related))
 entries={}
 for p in rows(BASE/'links/character_skills.jsonl'):
  for g in p['groups']:
   for e in g['records']:
    if e.get('table')=='charainfo':entries[e['reference_id']]=e
 boundaries=[]
 def test(name,e,f,a,ch,expect=None,**kw):
  bound,reason=B.bind(e,f,a,ch,**kw);ok=(bound is not None)if expect=='ACCEPT'else bound is None and(expect is None or expect==reason)
  if expect=='ACCEPT':ok=ok and bound==after[next(x['rec_key']for x in ledger if x['record_id']==e['reference_id'])]['fragments'][0]['binding']
  boundaries.append(dict(name=name,passed=ok,expected=expect,actual=reason))
 for x in ledger:
  cid=x['record_id'];e=entries[cid];f=x['after']['t'];a=after[x['rec_key']]['answers'];ch=after[x['rec_key']]['children']
  test(str(cid)+' exact_positive',e,f,a,ch,'ACCEPT')
  test(str(cid)+' added_clause',e,f+'さらに攻撃力が上がる',a,ch,'WHOLE_SENTENCE_OR_TYPE_CHANGED')
  test(str(cid)+' wrong_target_direction',e,f.replace('敵','味方').replace('味方全体','敵全体'),a,ch,'WHOLE_SENTENCE_OR_TYPE_CHANGED')
  z=copy.deepcopy(e);z['layer']='CACHE';test(str(cid)+' source_layer',z,f,a,ch,'SNAPSHOT_OR_LAYER_CHANGED')
  z=copy.deepcopy(e);z['source']['raw_record_sha256']='0'*64;test(str(cid)+' source_stamp',z,f,a,ch,'FROZEN_ROOT_OR_SOURCE_CHANGED')
  z=copy.deepcopy(a);z.append(copy.deepcopy(next(v for v in a if v['f']=='/skillparam1')));test(str(cid)+' duplicate_formula',e,f,z,ch,'LOCAL_FORMULA_NOT_UNIQUE')
 for cid in [5,2020,6005,5028,34,5232]:
  x=next(x for x in ledger if x['record_id']==cid);e=entries[cid];f=x['after']['t'];a=after[x['rec_key']]['answers'];ch=after[x['rec_key']]['children']
  for field in B.CONTROL_ZERO:
   for value in [1,None,'MISSING']:
    z=copy.deepcopy(e)
    if value=='MISSING':z['record'].pop(field)
    else:z['record'][field]=value
    test(str(cid)+f' {field}={value}',z,f,a,ch,'CONTROL_NOT_EXPLICIT_ZERO')
  for field,value in [('raw',999),('value','999HP'),('kind','other'),('unit','%'),('status','CONFIRMED_NUMERIC'),('scope','IN_REVIEWED_VIEW'),('rule_key','skilllist|11|/param0')]:
   z=copy.deepcopy(a);next(v for v in z if v['f']=='/skillparam1')[field]=value;test(str(cid)+' local_'+field,e,f,z,ch)
  z=copy.deepcopy(e);z['record']['skillflag0_0']=1 if x['family']=='type11_heal'else(0 if e['record']['skillflag0_0']&1 else 1)
  test(str(cid)+' flag_target_mismatch',z,f,a,ch,'FLAG_CONTROL_CHANGED'if x['family']=='type11_heal'else'FLAG_SENTENCE_TARGET_MISMATCH')
  z=copy.deepcopy(e);z['record']['skilltext']+='別の説明。';test(str(cid)+' full_text',z,f,a,ch,'WHOLE_SOURCE_TEXT_CHANGED')
  test(str(cid)+' executed_child',e,f,a,[dict(table='bossskill',record_id=999)],'EXTRA_EXECUTION_CHILD')
  cc=copy.deepcopy(B.contexts()[cid]);cc['own_charainfo'].append(copy.deepcopy(cc['own_charainfo'][0]));test(str(cid)+' added_own_context',e,f,a,ch,'OWN_OR_RELATED_CONTEXT_CHANGED',actual_contexts=cc)
  cc=copy.deepcopy(B.contexts()[cid]);cc['related_groups'].append(dict(group='heroic',records=[]));test(str(cid)+' added_conditional_group',e,f,a,ch,'OWN_OR_RELATED_CONTEXT_CHANGED',actual_contexts=cc)
  cc=copy.deepcopy(B.contexts()[cid]);cc['own_charainfo']=[];test(str(cid)+' removed_own_context',e,f,a,ch,'OWN_OR_RELATED_CONTEXT_CHANGED',actual_contexts=cc)
  identity=copy.deepcopy(B.membership()['identity']);identity['playable_count']-=1;test(str(cid)+' changed_player_scope',e,f,a,ch,'PLAYER_SCOPE_IDENTITY_CHANGED',actual_membership=identity)
 # Real Table overlays: roots and links stay fixed for related-namespace changes.
 original=B.tables()
 class Overlay:
  def __init__(self,changes=None,duplicates=None):self.changes=changes or {};self.duplicates=duplicates or {};self.tabs={}
  def __call__(self,table):
   if table in self.tabs:return self.tabs[table]
   base=original(table);outer=self
   class T:
    cache=base.cache;apk=copy.deepcopy(base.apk)if table in outer.duplicates else base.apk
    if table in outer.duplicates:
     did=outer.duplicates[table];apk[did]=apk[did]+[copy.deepcopy(apk[did][0])]
    def get(self,ident):return outer.changes.get((table,ident),base.get(ident))
    def ids(self):return base.ids()|{i for t,i in outer.changes if t==table}
   self.tabs[table]=T();return self.tabs[table]
 overlays=[]
 raw,layer=original('charainfo').get(5)
 for label,mut in [('raw_value',dict(skillparam1=123)),('raw_pattern',dict(pattern0=12345))]:overlays.append((label,5,Overlay({('charainfo',5):(dict(raw,**mut),layer)}),'CURRENT_RAW_SOURCE_CHANGED'))
 overlays.append(('duplicate_original_identity',5,Overlay(duplicates={'charainfo':5}),'RAW_IDENTITY_OR_RELATED_REFERENCE_CHANGED'))
 overlays.append(('remove_denju',5,Overlay({('denju',5):(None,None)}),'RAW_IDENTITY_OR_RELATED_REFERENCE_CHANGED'))
 dr,dl=original('denju').get(39);overlays.append(('change_denju_raw',39,Overlay({('denju',39):(dict(dr,stext=dr['stext']+'改'),dl)}),'RAW_IDENTITY_OR_RELATED_REFERENCE_CHANGED'))
 overlays.append(('new_denju',21,Overlay({('denju',21):(dict(dr,denju_id=21),'CACHE')}),'RAW_IDENTITY_OR_RELATED_REFERENCE_CHANGED'))
 overlays.append(('new_hero_context',21,Overlay({('heroicskilllist',999000001):(dict(skillid=999000001,boss_pattern=10002100,boss_pattern2=0,boss_pattern3=0),'CACHE')}),'RAW_IDENTITY_OR_RELATED_REFERENCE_CHANGED'))
 for label,cid,provider,expected in overlays:
  x=next(x for x in ledger if x['record_id']==cid);e=entries[cid]
  with patch.object(B,'tables',return_value=provider):test(label,e,x['after']['t'],after[x['rec_key']]['answers'],after[x['rec_key']]['children'],expected)
 ck('semantic_source_and_real_raw_reference_boundaries',all(x['passed']for x in boundaries),passed_cases=sum(x['passed']for x in boundaries),total=len(boundaries))
 op={p['cid']:p for p in oldp};derived={}
 for p in newp:
  ff=[f for g in p['groups']for ref in g['records']for f in after[ref['rec_key']]['fragments']];real=sum(f['status']in ['BASELINE_DESCRIPTION_ANSWER','REVIEWED_DESCRIPTION_BINDING']for f in ff)
  answercount=len(p.get('baseline',[]))+sum(len(h['answers'])for g in p['groups']for ref in g['records']for h in [after[ref['rec_key']]]+after[ref['rec_key']]['children'])
  derived[p['cid']]='仅未知'if not answercount else('完整'if real==len(ff)and not p['unresolved']else'部分')
 ck('2236_statuses_naturally_recomputed_old_complete29_exact',len(newp)==2236 and all(derived[p['cid']]==p['status']for p in newp)and next(p for p in newp if p['cid']==29)==op[29])
 fixed=['descriptions','descriptions_unique','descriptions_internal_label','unexplained_fields','answers','answers_in_reviewed_view','answers_by_type_extrapolated','broken_links']
 ck('all_denominators_field_scopes_unknowns_noncoverage_profile_objects_exact',all(all(p['coverage'][k]==op[p['cid']]['coverage'][k]for k in fixed)and all(p[k]==op[p['cid']][k]for k in set(p)-{'coverage','status'})for p in newp))
 s0=C.load_json(BEFORE/'summary.json');s1=C.load_json(BASE/'profiles/summary.json');trans=[dict(cid=p['cid'],name=p['name'],before=op[p['cid']]['status'],after=p['status'],coverage=p['coverage'])for p in newp if p['status']!=op[p['cid']]['status']]
 inc=dict(independent_review_status='P3B8_PENDING_INDEPENDENT_D',field_answers_added_pages=s1['totals']['rule_answers']-s0['totals']['rule_answers'],field_answers_added_normalized_rows=s1['totals']['rule_answers_unique_records']-s0['totals']['rule_answers_unique_records'],field_answers_added_parent_holder_keys=s1['totals']['rule_answers_parent_holder_keys']-s0['totals']['rule_answers_parent_holder_keys'],fragments_added_unique_records=len(new),fragments_added_page_references=sum(len(x['page_uses'])for x in ledger),effect_slots_added_unique_records=sum(len(x['after']['binding']['fields'])for x in ledger),effect_slots_added_page_references=sum(len(x['page_uses'])*len(x['after']['binding']['fields'])for x in ledger),affected_cids=sorted({p['cid']for x in ledger for p in x['page_uses']}),family_counts=dict(collections.Counter(x['family']for x in ledger)),old_target_status_counts=dict(collections.Counter(x['before']['status']for x in ledger)),before_totals=s0['totals'],after_totals=s1['totals'],before_status=s0['status_counts'],after_status=s1['status_counts'],status_transitions=trans)
 ck('actual_increment_reconciles_no_new_fields',not any(inc[k]for k in ['field_answers_added_pages','field_answers_added_normalized_rows','field_answers_added_parent_holder_keys'])and s1['totals']['fragments_attributed_confirmed']-s0['totals']['fragments_attributed_confirmed']==inc['fragments_added_page_references']and len(new)==len(B.scope()['records'])and len(inc['affected_cids'])==len(new))
 cli=[];env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936')
 for cid in [5,6005,34,5232,29,30236]:
  for mode in ['json','text']:
   run=subprocess.run([sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),'--cid',str(cid)]+(['--json']if mode=='json'else[]),cwd=C.ROOT,env=env,capture_output=True);(OUT/f'cli_{cid}_{mode}.log').write_bytes(run.stdout+run.stderr)
   ok=run.returncode==0 and not run.stderr
   if mode=='json':ok=ok and json.loads(run.stdout.decode('utf-8'))['characters'][0]['cid']==cid
   else:ok=ok and f'cid {cid}'in run.stdout.decode('utf-8')
   cli.append(dict(cid=cid,mode=mode,returncode=run.returncode,passed=ok))
 ck('representative_GBK_JSON_text_old_complete_baseline_queries',all(x['passed']for x in cli),samples=cli)
 C.write_jsonl(OUT/'bindings.jsonl',ledger);C.write_json(OUT/'increment.json',inc);C.write_json(OUT/'raw_crosscheck.json',dict(roots=rawchecks,related_records=related,passed=all(x['passed']for x in rawchecks+related)))
 C.write_json(OUT/'boundary_validation.json',dict(checks=boundaries,passed=sum(x['passed']for x in boundaries),total=len(boundaries)))
 C.write_json(OUT/'validation.json',dict(status='C_SELF_CHECK_NOT_INDEPENDENT_D',checks=checks,passed=sum(x['passed']for x in checks),total=len(checks)))
 C.write_json(OUT/'source_manifest.json',dict(snapshot=C.SNAPSHOT_ID,roots=[dict(cid=x['record_id'],source=x['source'],pages=x['page_uses'],contexts=x['all_contexts'],raw_audit=x['raw_audit'])for x in ledger],related_namespace_records=related,native_evidence='native_evidence.json'))
 C.write_csv(OUT/'bindings.csv',['cid','family','fragment','raw_skillparam1','unit','status','cids'],[[x['record_id'],x['family'],x['after']['t'],x['after']['binding']['fields'][0]['raw'],x['after']['binding']['fields'][0]['unit'],x['after']['binding']['fields'][0]['status'],','.join(str(p['cid'])for p in x['page_uses'])]for x in ledger])
 print(json.dumps(dict(passed=sum(x['passed']for x in checks),total=len(checks),boundaries=f"{sum(x['passed']for x in boundaries)}/{len(boundaries)}",new_fragments=len(new),new_pages=inc['fragments_added_page_references'],transitions=trans,failed=[x['name']for x in checks if not x['passed']]),ensure_ascii=False))
 if not all(x['passed']for x in checks):raise SystemExit(1)

def freeze():
 files=[C.ROOT/'scripts/character_skills'/n for n in ['p3b8_native.py','p3b8_bindings.py','p3b8_binding_scope.json','p3b8_batch.py','p3b8_dom.js','profiles.py']]
 files+=[C.ROOT/p for p in ['HANDOFF.md','STATUS.md','docs/tasks/20261019-character-skills-p3b8-boss-bindings.md','output/character_skills/README.md','output/character_skills/P3B8_HANDOFF.md','output/character_skills/validation/crosscheck_raw.json']]
 files+=[p for directory in [OUT,BASE/'profiles',BASE/'gaps',C.ROOT/'work/character_skills_p3b8']for p in directory.rglob('*')if p.is_file()and p.name!='frozen_manifest.json'and BEFORE not in p.parents]
 readonly=[p for p in BEFORE.iterdir()if p.is_file()]+[C.ROOT/'scripts/character_skills'/n for n in ['batch_bindings.py','p3b6_binding_scope.json','p3b7_bindings.py','p3b7_binding_scope.json','description_bindings.py','equivalence.py','rules.py','verify_p1.py','crosscheck_raw.py','link_skills.py']]
 readonly+=[C.ROOT/x['path']for x in C.load_json(OUT/'native_evidence.json')['reused_evidence']]
 readonly+=[BASE/'review/p3b7_20261019_type26_batch/REPORT_R2.md',BASE/'description_bindings/p3b7_batch/bindings.jsonl']
 def item(p):return dict(path=str(p.relative_to(C.ROOT)).replace('\\','/'),size=p.stat().st_size,sha256=C.sha256_file(p))
 C.write_json(OUT/'frozen_manifest.json',dict(status='P3B8_PENDING_INDEPENDENT_D',files=[item(p)for p in sorted(set(files))],readonly_dependencies=[item(p)for p in sorted(set(readonly))]))
 print(json.dumps(dict(frozen_files=len(set(files)),readonly_dependencies=len(set(readonly)))))

if __name__=='__main__':
 if '--freeze'in sys.argv:freeze()
 else:main()
