"""P3B6 ledgers, boundary checks and exact old-object regression accounting."""
from __future__ import annotations
import collections,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
import common as C
import batch_bindings as BB
BASE=C.ROOT/'output/character_skills';OUT=BB.OUT;BEFORE=C.ROOT/'work/character_skills_p3b6/before'
def rows(p):return [json.loads(s)for s in Path(p).open(encoding='utf-8')]
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def main():
 C.enable_utf8_console();checks=[]
 def ck(name,passed,**kw):checks.append(dict(name=name,passed=bool(passed),**kw))
 old=rows(BEFORE/'records.jsonl');now=rows(BASE/'profiles/records.jsonl');oldp=rows(BEFORE/'profiles.jsonl');newp=rows(BASE/'profiles/profiles.jsonl')
 by={r['rec_key']:r for r in now};oldby={r['rec_key']:r for r in old}
 def answers(rr):return collections.Counter((r['rec_key'],h['table'],h['record_id'],canon(a))for r in rr for h in [r]+r['children']for a in h['answers'])
 ca,cb=answers(old),answers(now)
 ck('82013_full_answer_objects_and_duplicate_counts_exact',ca==cb,before=sum(ca.values()),after=sum(cb.values()))
 ck('277_old_used_rules_exact_and_source287_retained',C.load_json(BEFORE/'rules.json')==C.load_json(BASE/'profiles/rules.json')and len(C.load_json(BASE/'profiles/rules.json'))==277 and C.load_json(BASE/'profiles/summary.json')['rule_source']['rule_count']==287)
 new=[];unchanged=True;oldbindingcount=0
 for r in old:
  n=by[r['rec_key']]
  if len(r['fragments'])!=len(n['fragments'])or r['baseline_answers']!=n['baseline_answers']:unchanged=False
  for a,b in zip(r['fragments'],n['fragments']):
   if a.get('binding'):oldbindingcount+=1
   if a==b:continue
   if a.get('binding')or a['t']!=b['t']or b.get('binding',{}).get('strength')!=BB.STRENGTH:unchanged=False
   else:new.append(dict(rec_key=r['rec_key'],source=r['source'],before=a,after=b,record_id=r['record_id'],table=r['table']))
  for k in set(r)-{'fragments'}:
   if r[k]!=n[k]:unchanged=False
 ck('old_all_bindings_fragments_baseline101_31_and_nonfragment_objects_preserved',unchanged and len(new)==9,old_bindings=oldbindingcount,new_bindings=len(new))
 uses=collections.defaultdict(list)
 for p in newp:
  for g in p['groups']:
   for ref in g['records']:uses[ref['rec_key']].append(dict(cid=p['cid'],name=p['name'],group=g['group'],reference_field=ref['reference_field'],character_source=p['charainfo_source']))
 # Independently load original JSON bytes/pointers; no C.Table source selection
 # or new binding function supplies the expected values in this audit.
 docs={};rawchecks=[];ledger=[]
 for item in new:
  src=item['source'];path=C.ROOT/src['original_file']
  if path not in docs:docs[path]=json.loads(path.read_bytes())
  raw=docs[path]
  for part in src['json_pointer'].strip('/').split('/'):raw=raw[int(part)]if isinstance(raw,list)else raw[part]
  sha=hashlib.sha256(canon(raw).encode('utf-8')).hexdigest()
  b=item['after']['binding'];expected_field='/param0'if item['table']=='skilllist'else '/skillparam1'
  a=b['fields'][0];local=next(a for a in by[item['rec_key']]['answers']if a['f']==expected_field)
  base={k:local[k]for k in ['f','raw','value','kind','unit','status','rule_key']};actual={k:a[k]for k in base}
  good=sha==src['raw_record_sha256']and raw[expected_field[1:]]==a['raw']and base==actual and a['evidence_scope']==local['scope']=='BY_TYPE_EXTRAPOLATED'
  if item['table']=='charainfo':good=good and raw['skilltext']==BB.LINE+'。'and raw['skillid'][0]==5 and raw['skillflag0_0']==1025 and not any(raw[f'pattern{i}']for i in range(9))and local['status']=='CONFIRMED_FORMULA_ONLY'
  rawchecks.append(dict(table=item['table'],record_id=item['record_id'],source=src,canonical_sha256=sha,field=expected_field,raw=a['raw'],formula_status=a['status'],passed=good))
  ledger.append(dict(item,raw_record=raw,all_role_contexts=BB.contexts()[f"{item['table']}|{item['record_id']}"],page_uses=uses[item['rec_key']]))
 ck('nine_original_json_hash_value_and_existing_formula_scope_crosschecks',all(r['passed']for r in rawchecks),rows=len(rawchecks))
 entries={}
 def walk(x):
  if isinstance(x,dict):
   key=f"{x.get('table')}|{x.get('reference_id')}"
   if key in BB.scope()['records']and x.get('resolved'):entries[key]=x
   for k,v in x.items():
    if k not in ['record','source','charainfo_source']:walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 for p in rows(BASE/'links/character_skills.jsonl'):walk(p)
 boundaries=[]
 def test(label,e,f,a,ch,ok=False,ctx=None):
  result,reason=BB.bind(e,f,a,ch,ctx)
  boundaries.append(dict(name=label,passed=bool(result)==ok,rejection=reason))
 for item in ledger:
  key=f"{item['table']}|{item['record_id']}";r=by[item['rec_key']];e=entries[key];f=item['after']['t'];a=r['answers'];ch=r['children']
  test(key+' positive',e,f,a,ch,True)
  test(key+' whole_sentence_change',e,f+'さらに攻撃力が上がる',a,ch)
  e2=copy.deepcopy(e);e2['layer']='CACHE';test(key+' source_layer_change',e2,f,a,ch)
  e2=copy.deepcopy(e);e2['record']['skillparam1'if item['table']=='charainfo'else'param0']=99;test(key+' raw_record_change',e2,f,a,ch)
  a2=copy.deepcopy(a);next(x for x in a2 if x['f']==('/skillparam1'if item['table']=='charainfo'else'/param0'))['raw']=99;test(key+' numeric_source_mismatch',e,f,a2,ch)
  a2=copy.deepcopy(a);next(x for x in a2 if x['f']==('/skillparam1'if item['table']=='charainfo'else'/param0'))['value']='999';test(key+' computed_value_changed_without_raw_change',e,f,a2,ch)
  ctx=copy.deepcopy(BB.scope()['records'][key]['contexts']);ctx[0]['reference_field']='job_ability.conditional';test(key+' all_reference_condition_change',e,f,a,ch,ctx=ctx)
  test(key+' duplicate_same_path_child',e,f,a,ch+[copy.deepcopy(ch[0])if ch else dict(table='skilllist',record_id=999,effect_type=26,link_kind='sub_effect')])
  if ch:test(key+' missing_child',e,f,a,[])
  a2=copy.deepcopy(a);a2.append(copy.deepcopy(next(x for x in a2 if x['f']==('/skillparam1'if item['table']=='charainfo'else'/param0'))));test(key+' duplicate_local_answer',e,f,a2,ch)
  a2=copy.deepcopy(a);next(x for x in a2 if x['f']==('/skillparam1'if item['table']=='charainfo'else'/param0'))['raw']=0;test(key+' wrong_direction_or_zero',e,f,a2,ch)
 ck('frozen_structural_boundary_suite',all(r['passed']for r in boundaries),passed_cases=sum(r['passed']for r in boundaries),total=len(boundaries))
 # Status is recomputed from each unchanged fragment denominator and actual real
 # binding, never from an expected number of complete characters.
 derived={}
 for p in newp:
  fs=[f for g in p['groups']for ref in g['records']for f in by[ref['rec_key']]['fragments']]
  real=sum(f['status']in ['BASELINE_DESCRIPTION_ANSWER','REVIEWED_DESCRIPTION_BINDING']for f in fs)
  answer_count=len(p.get('baseline',[]))+sum(len(h['answers'])for g in p['groups']for ref in g['records']for h in [by[ref['rec_key']]]+by[ref['rec_key']]['children'])
  derived[p['cid']]='仅未知'if not answer_count else ('完整'if len(fs)==real and not p['unresolved']else'部分')
 ck('all_2236_statuses_independently_derived_from_original_standard',all(derived[p['cid']]==p['status']for p in newp))
 op={p['cid']:p for p in oldp};trans=[dict(cid=p['cid'],name=p['name'],before=op[p['cid']]['status'],after=p['status'],before_coverage=op[p['cid']]['coverage'],after_coverage=p['coverage'])for p in newp if op[p['cid']]['status']!=p['status']]
 ck('every_denominator_unknown_field_and_field_scope_unchanged',all(all(p['coverage'][k]==op[p['cid']]['coverage'][k]for k in ['descriptions','descriptions_unique','descriptions_internal_label','unexplained_fields','answers','answers_in_reviewed_view','answers_by_type_extrapolated','broken_links'])for p in newp))
 s0=C.load_json(BEFORE/'summary.json');s1=C.load_json(BASE/'profiles/summary.json')
 inc=dict(independent_review_status='P3B6_PENDING_INDEPENDENT_D',field_answers_added_pages=s1['totals']['rule_answers']-s0['totals']['rule_answers'],field_answers_added_normalized_rows=s1['totals']['rule_answers_unique_records']-s0['totals']['rule_answers_unique_records'],field_answers_added_parent_holder_keys=s1['totals']['rule_answers_parent_holder_keys']-s0['totals']['rule_answers_parent_holder_keys'],fragments_added_unique_records=len(new),fragments_added_page_references=sum(len(r['page_uses'])for r in ledger),effect_slots_added_unique_records=sum(len(r['after']['binding']['fields'])for r in ledger),effect_slots_added_page_references=sum(len(r['page_uses'])*len(r['after']['binding']['fields'])for r in ledger),families=dict(collections.Counter(r['after']['binding']['template_id']for r in ledger)),status_transitions=trans,before_status=s0['status_counts'],after_status=s1['status_counts'],before_totals=s0['totals'],after_totals=s1['totals'])
 ck('nine_binding_page_and_effect_slot_increment_with_zero_fields',inc['field_answers_added_pages']==inc['field_answers_added_normalized_rows']==inc['field_answers_added_parent_holder_keys']==0 and inc['fragments_added_unique_records']==inc['fragments_added_page_references']==inc['effect_slots_added_unique_records']==inc['effect_slots_added_page_references']==9)
 cli=[];env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936')
 for cid in [29,1233,10032,30236]:
  for mode in ['json','text']:
   args=[sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),'--cid',str(cid)]+(['--json']if mode=='json'else[])
   run=subprocess.run(args,cwd=C.ROOT,env=env,capture_output=True);(OUT/f'cli_{cid}_{mode}.log').write_bytes(run.stdout+run.stderr)
   ok=run.returncode==0 and not run.stderr
   if mode=='json':ok=ok and json.loads(run.stdout.decode('utf-8'))['characters'][0]['cid']==cid
   else:ok=ok and f'cid {cid}'in run.stdout.decode('utf-8')
   cli.append(dict(cid=cid,mode=mode,passed=ok,returncode=run.returncode))
 ck('representative_default_gbk_cli_json_and_text',all(r['passed']for r in cli),samples=cli)
 C.write_jsonl(OUT/'bindings.jsonl',ledger);C.write_json(OUT/'increment.json',inc);C.write_json(OUT/'raw_crosscheck.json',dict(rows=len(rawchecks),passed=sum(r['passed']for r in rawchecks),checks=rawchecks))
 C.write_json(OUT/'boundary_validation.json',dict(checks=boundaries,passed=sum(r['passed']for r in boundaries),total=len(boundaries)))
 C.write_json(OUT/'validation.json',dict(checks=checks,passed=sum(r['passed']for r in checks),total=len(checks)))
 C.write_csv(OUT/'bindings.csv',['table','record_id','fragment','raw','unit','status','cids'],[[r['table'],r['record_id'],r['after']['t'],r['after']['binding']['fields'][0]['raw'],r['after']['binding']['fields'][0]['unit'],r['after']['binding']['fields'][0]['status'],','.join(str(p['cid'])for p in r['page_uses'])]for r in ledger])
 print(json.dumps(dict(checks=f"{sum(r['passed']for r in checks)}/{len(checks)}",boundaries=len(boundaries),new_fragments=len(new),status=s1['status_counts'],transitions=[dict(cid=t['cid'],after=t['after'])for t in trans]),ensure_ascii=False))
 if not all(r['passed']for r in checks):raise SystemExit(1)

def freeze():
 files=[C.ROOT/'scripts/character_skills'/name for name in ['batch_bindings.py','p3b6_binding_scope.json','p3b6_native.py','p3b6_batch.py','p3b6_dom.js','profiles.py']]
 files += [C.ROOT/p for p in ['HANDOFF.md','STATUS.md','docs/tasks/20261019-character-skills-p3b6-batch-bindings.md','output/character_skills/README.md','output/character_skills/P3B6_HANDOFF.md','output/character_skills/validation/crosscheck_raw.json']]
 files += [p for d in [OUT,BASE/'profiles',BASE/'gaps']for p in d.rglob('*')if p.is_file()and p.name!='frozen_manifest.json']
 readonly=[BEFORE/name for name in ['records.jsonl','profiles.jsonl','rules.json','summary.json']]
 readonly += [C.ROOT/'scripts/character_skills'/name for name in ['description_bindings.py','type26_mana.py','type9_bullet.py','equivalence.py','rules.py','verify_p1.py','crosscheck_raw.py']]
 readonly += [C.ROOT/'work/character_skills_p3b1/before'/name for name in ['rules.json','records.jsonl','profiles.jsonl']]
 readonly += [BASE/p for p in ['description_bindings/type8/accepted.jsonl','description_bindings/type8/excluded.jsonl','description_bindings/type8/summary.json','type26_mana/bindings.jsonl','type26_mana/native_evidence.json','type9_crit/native_evidence.json','boss_attack_types/type_rules.json','cp_paths/path_evidence.json']]
 def row(p):return dict(path=str(p.relative_to(C.ROOT)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 C.write_json(OUT/'frozen_manifest.json',dict(status='P3B6_PENDING_INDEPENDENT_D_REVIEW',files=[row(p)for p in sorted(set(files))],readonly_dependencies=[row(p)for p in sorted(set(readonly))]))
 print(json.dumps(dict(frozen_files=len(set(files)),readonly_dependencies=len(set(readonly)))))

if __name__=='__main__':
 if '--freeze'in sys.argv:freeze()
 else:main()
