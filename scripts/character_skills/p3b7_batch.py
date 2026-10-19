"""C self-check: actual increments, full old-object accounting and boundaries."""
import collections,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
from unittest.mock import patch
import common as C
import p3b7_bindings as B

BASE=C.ROOT/'output/character_skills';OUT=B.OUT;BEFORE=C.ROOT/'work/character_skills_p3b7/before'
def rows(p):return [json.loads(s)for s in Path(p).open(encoding='utf-8')]
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def main():
 C.enable_utf8_console();checks=[]
 def ck(name,ok,**kw):checks.append(dict(name=name,passed=bool(ok),**kw))
 old=rows(BEFORE/'records.jsonl');now=rows(BASE/'profiles/records.jsonl');oldp=rows(BEFORE/'profiles.jsonl');newp=rows(BASE/'profiles/profiles.jsonl')
 before={r['rec_key']:r for r in old};after={r['rec_key']:r for r in now}
 def allanswers(rr):return collections.Counter((r['rec_key'],h['table'],h['record_id'],canon(a))for r in rr for h in [r]+r['children']for a in h['answers'])
 aa,ab=allanswers(old),allanswers(now)
 ck('82013_complete_answer_objects_holder_keys_and_duplicates_preserved',aa==ab,before=sum(aa.values()),after=sum(ab.values()))
 ck('277_used_rules_287_source_rules_exact',C.load_json(BEFORE/'rules.json')==C.load_json(BASE/'profiles/rules.json')and len(C.load_json(BASE/'profiles/rules.json'))==277 and C.load_json(BASE/'profiles/summary.json')['rule_source']['rule_count']==287)
 ck('all_record_keys_order_and_duplicate_counts_preserved',[r['rec_key']for r in old]==[r['rec_key']for r in now])
 new=[];good=True;oldbindings=0;baseanswers=0;basefrags=0
 for r in old:
  n=after[r['rec_key']];baseanswers+=len(r['baseline_answers']);basefrags+=sum(f['status']=='BASELINE_DESCRIPTION_ANSWER'for f in r['fragments'])
  if len(r['fragments'])!=len(n['fragments']):good=False
  for a,b in zip(r['fragments'],n['fragments']):
   if a.get('binding'):oldbindings+=1
   if a==b:continue
   if a.get('binding')or a['t']!=b['t']or b.get('binding',{}).get('strength')!=B.STRENGTH or f"{r['table']}|{r['record_id']}"not in B.scope()['records']:good=False
   else:new.append(dict(rec_key=r['rec_key'],table=r['table'],record_id=r['record_id'],source=r['source'],before=a,after=b))
  if any(r[k]!=n[k]for k in set(r)-{'fragments'}):good=False
 ck('old32_bindings_101_baseline_answers_31_fragments_and_all_non_targets_exact',good and oldbindings==32 and baseanswers==101 and basefrags==31,old_bindings=oldbindings,baseline_answers=baseanswers,baseline_fragments=basefrags,actual_new_fragments=len(new))
 uses=collections.defaultdict(list)
 for p in newp:
  for g in p['groups']:
   for ref in g['records']:uses[ref['rec_key']].append(dict(cid=p['cid'],name=p['name'],group=g['group'],reference_field=ref['reference_field'],character_source=p['charainfo_source']))
 docs={};rawchecks=[];sources=[];ledger=[]
 def direct(source):
  path=C.ROOT/source['original_file']
  if path not in docs:docs[path]=json.loads(path.read_bytes())
  raw=docs[path]
  for x in source['json_pointer'].strip('/').split('/'):raw=raw[int(x)]if isinstance(raw,list)else raw[x]
  sha=hashlib.sha256(canon(raw).encode()).hexdigest()
  return raw,sha
 for item in new:
  raw,sha=direct(item['source']);a=item['after']['binding']['fields'][0];r=after[item['rec_key']];local=next(a for a in r['answers']if a['f']=='/param0')
  same=sha==item['source']['raw_record_sha256']and raw['param0']==a['raw']and all(a[k]==local[k]for k in ['f','raw','value','kind','unit','status','rule_key'])and a['evidence_scope']==local['scope']=='BY_TYPE_EXTRAPOLATED'and local['status']=='CONFIRMED_NUMERIC'
  rawchecks.append(dict(record_id=item['record_id'],source=item['source'],canonical_sha256=sha,param0=raw['param0'],unit=a['unit'],passed=same))
  spec=B.scope()['records'][f"skilllist|{item['record_id']}"]
  for child in spec['children']:
   cr,csha=direct(child['source']);sources.append(dict(parent_id=item['record_id'],record_id=child['record_id'],source=child['source'],effect_type=cr['ability'],leaf=cr.get('sub')==[],passed=csha==child['source']['raw_record_sha256']and cr['ability']==child['effect_type']and cr['ability']not in B.FORBIDDEN and cr.get('sub')==[]))
  ledger.append(dict(item,raw_record=raw,all_role_contexts=spec['contexts'],reverse_subs=spec['reverse_subs'],children=spec['children'],page_uses=uses[item['rec_key']]))
 ck('source_raw_numeric_unit_scope_and_all_actual_leaf_sources',all(x['passed']for x in rawchecks+sources),roots=len(rawchecks),child_instances=len(sources),unique_child_sources=len({x['source']['record_key']for x in sources}),child_types=len({x['effect_type']for x in sources}))
 entries={}
 def walk(x):
  if isinstance(x,dict):
   key=f"{x.get('table')}|{x.get('reference_id')}"
   if x.get('resolved')and key in B.scope()['records']:entries[key]=x
   for k,v in x.items():
    if k not in ['record','source','charainfo_source']:walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 for p in rows(BASE/'links/character_skills.jsonl'):walk(p)
 boundaries=[]
 def test(name,e,f,a,ch,expect=None,**kw):
  binding,reason=B.bind(e,f,a,ch,**kw)
  ok=bool(binding)if expect=='ACCEPT'else binding is None and (expect is None or reason==expect)
  boundaries.append(dict(name=name,passed=ok,expected=expect,actual=reason))
 for item in ledger:
  key=f"skilllist|{item['record_id']}";e=entries[key];r=after[item['rec_key']];f=item['after']['t'];a=r['answers'];ch=r['children']
  test(key+' positive',e,f,a,ch,'ACCEPT')
  test(key+' added_clause',e,f+'攻撃力が上がる',a,ch,'WHOLE_SENTENCE_OR_TYPE_CHANGED')
  test(key+' direction',e,f.replace('持った','失った'),a,ch,'WHOLE_SENTENCE_OR_TYPE_CHANGED')
  wrong=f.replace('1','2').replace('１','２')if e['record']['param0']==1 else f.replace('2','1').replace('２','１')
  test(key+' wrong_number',e,wrong,a,ch,'LOCAL_PARAM0_OR_TEXT_NUMBER_MISMATCH')
  bad=copy.deepcopy(e);bad['layer']='CACHE';test(key+' source_layer',bad,f,a,ch,'SNAPSHOT_OR_LAYER_CHANGED')
  bad=copy.deepcopy(e);bad['source']['raw_record_sha256']='0'*64;test(key+' source_stamp',bad,f,a,ch,'FROZEN_ROOT_OR_SOURCE_CHANGED')
  bad=copy.deepcopy(e);bad['record']['text']+='別の説明';test(key+' whole_text',bad,f,a,ch,'FROZEN_ROOT_OR_SOURCE_CHANGED')
  test(key+' missing_child',e,f,a,ch[:-1],'MISSING_OR_DUPLICATE_CHILD')
  test(key+' duplicate_child',e,f,a,ch+[copy.deepcopy(ch[0])],'MISSING_OR_DUPLICATE_CHILD')
  ctx=copy.deepcopy(B.scope()['records'][key]['contexts']);ctx.append(copy.deepcopy(ctx[0]));test(key+' added_direct_reference',e,f,a,ch,'ALL_REFERENCE_CONTEXTS_CHANGED',actual_contexts=ctx)
  test(key+' new_parent_sub_reference',e,f,a,ch,'NEW_REVERSE_SUB_REFERENCE',actual_parents=[dict(parent_id=999,sub_index=0)])
  bad=copy.deepcopy(a);bad.append(copy.deepcopy(next(x for x in bad if x['f']=='/param0')));test(key+' duplicate_local_answer',e,f,bad,ch,'LOCAL_PARAM0_OR_TEXT_NUMBER_MISMATCH')
 # The varied four sources cover one/many sub and half/full-width text. These
 # semantic guards run before whole-source pin checks, avoiding a hash-only suite.
 for ident in [30000303,30221300,30832700,35901503]:
  item=next(x for x in ledger if x['record_id']==ident);key=f'skilllist|{ident}';e=entries[key];r=after[item['rec_key']];f=item['after']['t'];a=r['answers'];ch=r['children']
  for field in B.ZERO_FIELDS:
   for value in [1,None,'MISSING']:
    bad=copy.deepcopy(e)
    if value=='MISSING':bad['record'].pop(field)
    else:bad['record'][field]=value
    test(key+f' {field}={value}',bad,f,a,ch,'OTHER_MANA_LINE_OR_GATE_NOT_EXPLICIT_ZERO')
  bad=copy.deepcopy(e);bad['record']['sub'].append(bad['record']['sub'][0]);test(key+' duplicate_declared',bad,f,a,ch,'INVALID_OR_DUPLICATE_DECLARED_SUB')
  bad=copy.deepcopy(ch);bad[0]['table']='bossskill';test(key+' wrong_namespace',e,f,a,bad,'CHILD_NAMESPACE_OR_LINK_CHANGED')
  for typ in [26,1073,1077]:
   bad=copy.deepcopy(ch);bad[0]['effect_type']=typ;test(key+f' forbidden_profile_type{typ}',e,f,a,bad,'ADDITIONAL_START_MANA_CONSUMER')
  for field,value in [('raw',9),('value','999'),('unit','%'),('scope','IN_REVIEWED_VIEW'),('kind','other'),('status','UNKNOWN'),('rule_key','skilllist|9|/param0')]:
   bad=copy.deepcopy(a);next(x for x in bad if x['f']=='/param0')[field]=value;test(key+' local_'+field,e,f,bad,ch)
  # Raw child mutations use a temporary Table overlay, not a re-pinned source
  # digest supplied as the expected answer. Source/type/leaf checks reject them.
  original=B.tables();sid=ch[0]['record_id'];raw,layer=original('skilllist').get(sid)
  for label,mutation,expected in [('nested',dict(sub=[999]),'NON_LEAF_OR_MISSING_CHILD_SUB'),('missing_sub',dict(sub='MISSING'),'NON_LEAF_OR_MISSING_CHILD_SUB'),('changed_raw',dict(param0=999),'CHILD_SOURCE_OR_TYPE_CHANGED')]+[(f'raw_forbidden{t}',dict(ability=t),'ADDITIONAL_START_MANA_CONSUMER')for t in [26,1073,1077]]:
   altered=copy.deepcopy(raw)
   for k,v in mutation.items():
    if v=='MISSING':altered.pop(k)
    else:altered[k]=v
   class Overlay:
    def __call__(self,table):
     outer=self
     class T:
      def get(self,ident):return (altered,layer)if table=='skilllist'and ident==sid else original(table).get(ident)
     return T()
   with patch.object(B,'tables',return_value=Overlay()):test(key+' '+label,e,f,a,ch,expected)
 ck('exact_structural_and_source_boundary_suite',all(x['passed']for x in boundaries),passed_cases=sum(x['passed']for x in boundaries),total=len(boundaries))
 op={p['cid']:p for p in oldp};derived={}
 for p in newp:
  fs=[f for g in p['groups']for ref in g['records']for f in after[ref['rec_key']]['fragments']]
  real=sum(f['status']in ['BASELINE_DESCRIPTION_ANSWER','REVIEWED_DESCRIPTION_BINDING']for f in fs)
  answercount=len(p.get('baseline',[]))+sum(len(h['answers'])for g in p['groups']for ref in g['records']for h in [after[ref['rec_key']]]+after[ref['rec_key']]['children'])
  derived[p['cid']]='仅未知'if not answercount else ('完整'if real==len(fs)and not p['unresolved']else'部分')
 ck('all2236_statuses_naturally_recomputed_and_complete29_preserved',len(newp)==2236 and all(derived[p['cid']]==p['status']for p in newp)and next(p for p in newp if p['cid']==29)==op[29])
 fixed=['descriptions','descriptions_unique','descriptions_internal_label','unexplained_fields','answers','answers_in_reviewed_view','answers_by_type_extrapolated','broken_links']
 ck('all_original_denominators_field_scope_unknowns_and_other_profile_objects_preserved',all(all(p['coverage'][k]==op[p['cid']]['coverage'][k]for k in fixed)and all(p[k]==op[p['cid']][k]for k in set(p)-{'coverage','status'})for p in newp))
 s0=C.load_json(BEFORE/'summary.json');s1=C.load_json(BASE/'profiles/summary.json');trans=[dict(cid=p['cid'],name=p['name'],before=op[p['cid']]['status'],after=p['status'],coverage=p['coverage'])for p in newp if p['status']!=op[p['cid']]['status']]
 inc=dict(independent_review_status='P3B7_PENDING_INDEPENDENT_D',field_answers_added_pages=s1['totals']['rule_answers']-s0['totals']['rule_answers'],field_answers_added_normalized_rows=s1['totals']['rule_answers_unique_records']-s0['totals']['rule_answers_unique_records'],field_answers_added_parent_holder_keys=s1['totals']['rule_answers_parent_holder_keys']-s0['totals']['rule_answers_parent_holder_keys'],fragments_added_unique_records=len(new),fragments_added_page_references=sum(len(x['page_uses'])for x in ledger),effect_slots_added_unique_records=sum(len(x['after']['binding']['fields'])for x in ledger),effect_slots_added_page_references=sum(len(x['page_uses'])*len(x['after']['binding']['fields'])for x in ledger),affected_cids=sorted({p['cid']for x in ledger for p in x['page_uses']}),old_target_status_counts=dict(collections.Counter(x['before']['status']for x in ledger)),before_totals=s0['totals'],after_totals=s1['totals'],before_status=s0['status_counts'],after_status=s1['status_counts'],status_transitions=trans)
 ck('actual_increment_reconciles_without_new_fields',not any(inc[k]for k in ['field_answers_added_pages','field_answers_added_normalized_rows','field_answers_added_parent_holder_keys'])and s1['totals']['fragments_attributed_confirmed']-s0['totals']['fragments_attributed_confirmed']==inc['fragments_added_page_references']and len(inc['affected_cids'])==len(new),actual_unique=len(new),actual_pages=inc['fragments_added_page_references'],actual_cids=len(inc['affected_cids']))
 cli=[];env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936')
 for cid in [3,2213,8327,59015,29,30236]:
  for mode in ['json','text']:
   run=subprocess.run([sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),'--cid',str(cid)]+(['--json']if mode=='json'else[]),cwd=C.ROOT,env=env,capture_output=True)
   (OUT/f'cli_{cid}_{mode}.log').write_bytes(run.stdout+run.stderr)
   ok=run.returncode==0 and not run.stderr
   if mode=='json':ok=ok and json.loads(run.stdout.decode('utf-8'))['characters'][0]['cid']==cid
   else:ok=ok and f'cid {cid}'in run.stdout.decode('utf-8')
   cli.append(dict(cid=cid,mode=mode,returncode=run.returncode,passed=ok))
 ck('representative_gbk_json_text_and_old_complete_baseline_queries',all(x['passed']for x in cli),samples=cli)
 C.write_jsonl(OUT/'bindings.jsonl',ledger);C.write_json(OUT/'increment.json',inc);C.write_json(OUT/'raw_crosscheck.json',dict(roots=rawchecks,children=sources,passed=all(x['passed']for x in rawchecks+sources)))
 C.write_json(OUT/'boundary_validation.json',dict(checks=boundaries,passed=sum(x['passed']for x in boundaries),total=len(boundaries)))
 C.write_json(OUT/'validation.json',dict(status='C_SELF_CHECK_NOT_INDEPENDENT_D',checks=checks,passed=sum(x['passed']for x in checks),total=len(checks)))
 C.write_json(OUT/'source_manifest.json',dict(snapshot=C.SNAPSHOT_ID,roots=[dict(record_id=x['record_id'],source=x['source'],pages=x['page_uses'],all_contexts=x['all_role_contexts'])for x in ledger],child_instances=sources,native_evidence='native_evidence.json'))
 C.write_csv(OUT/'bindings.csv',['record_id','fragment','raw_param0','unit','status','cids'],[[x['record_id'],x['after']['t'],x['after']['binding']['fields'][0]['raw'],x['after']['binding']['fields'][0]['unit'],x['after']['binding']['fields'][0]['status'],','.join(str(p['cid'])for p in x['page_uses'])]for x in ledger])
 print(json.dumps(dict(passed=sum(x['passed']for x in checks),total=len(checks),boundaries=f"{sum(x['passed']for x in boundaries)}/{len(boundaries)}",new_fragments=len(new),new_pages=inc['fragments_added_page_references'],status_transitions=trans),ensure_ascii=False))
 if not all(x['passed']for x in checks):raise SystemExit(1)

def freeze():
 files=[C.ROOT/'scripts/character_skills'/n for n in ['p3b7_native.py','p3b7_bindings.py','p3b7_binding_scope.json','p3b7_batch.py','p3b7_dom.js','profiles.py']]
 files += [C.ROOT/p for p in ['HANDOFF.md','STATUS.md','docs/tasks/20261019-character-skills-p3b7-batch-bindings.md','output/character_skills/README.md','output/character_skills/P3B7_HANDOFF.md','output/character_skills/validation/crosscheck_raw.json']]
 files += [p for d in [OUT,BASE/'profiles',BASE/'gaps']for p in d.rglob('*')if p.is_file()and p.name!='frozen_manifest.json']
 readonly=[p for p in BEFORE.iterdir()if p.is_file()]
 readonly += [C.ROOT/'scripts/character_skills'/n for n in ['batch_bindings.py','p3b6_binding_scope.json','description_bindings.py','type26_mana.py','equivalence.py','rules.py','verify_p1.py','crosscheck_raw.py']]
 readonly += [BASE/p for p in ['description_bindings/type8/accepted.jsonl','type26_mana/bindings.jsonl','type26_mana/native_evidence.json','description_bindings/p3b6_batch/bindings.jsonl','description_bindings/p3b6_batch/type5_native_evidence.json','review/p3b6_20261019_batch_bindings/REPORT.md']]
 files += [C.ROOT/'work/character_skills_p3b7'/p for p in ['phase_a_inventory.py','start_consumer_outline.py','freeze_scope.py','stability.py']]
 def row(p):return dict(path=str(p.relative_to(C.ROOT)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 C.write_json(OUT/'frozen_manifest.json',dict(status='P3B7_PENDING_INDEPENDENT_D',files=[row(p)for p in sorted(set(files))],readonly_dependencies=[row(p)for p in sorted(set(readonly))]))
 print(json.dumps(dict(frozen_files=len(set(files)),readonly_dependencies=len(set(readonly)))))

if __name__=='__main__':
 if '--freeze'in sys.argv:freeze()
 else:main()
