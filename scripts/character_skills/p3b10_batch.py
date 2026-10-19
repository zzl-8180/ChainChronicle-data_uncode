"""P3B10 exact-object, stdlib source, refusal-boundary and interface C checks."""
import collections,copy,json,os,subprocess,sys
from pathlib import Path
from unittest.mock import patch
import common as C
import p3b10_bindings as B
BASE=C.ROOT/'output/character_skills';OUT=B.OUT;BEFORE=C.ROOT/'work/character_skills_p3b10/before'
def rows(p):return [json.loads(s)for s in Path(p).open(encoding='utf-8')]
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def main():
 C.enable_utf8_console();checks=[];boundaries=[]
 def ck(name,ok,**kw):checks.append(dict(name=name,passed=bool(ok),**kw))
 old=rows(BEFORE/'records.jsonl');now=rows(BASE/'profiles/records.jsonl');oldp=rows(BEFORE/'profiles.jsonl');newp=rows(BASE/'profiles/profiles.jsonl');after={r['rec_key']:r for r in now}
 def ans(rr):return collections.Counter((r['rec_key'],h['table'],h['record_id'],canon(a))for r in rr for h in [r]+r['children']for a in h['answers'])
 ck('all82013_complete_answers_objects_and_duplicates',ans(old)==ans(now)and sum(ans(now).values())==82013)
 ck('all277_used_287_source_rules_unchanged',C.load_json(BEFORE/'rules.json')==C.load_json(BASE/'profiles/rules.json')and len(C.load_json(BASE/'profiles/rules.json'))==277 and C.load_json(BASE/'profiles/summary.json')['rule_source']['rule_count']==287)
 good=[r['rec_key']for r in old]==[r['rec_key']for r in now];new=[];oldbindings=0;ba=0;bf=0
 for r in old:
  nr=after[r['rec_key']];good=good and {k:v for k,v in r.items()if k!='fragments'}=={k:v for k,v in nr.items()if k!='fragments'}and len(r['fragments'])==len(nr['fragments']);ba+=len(r['baseline_answers']);bf+=sum(f['status']=='BASELINE_DESCRIPTION_ANSWER'for f in r['fragments'])
  for a,b in zip(r['fragments'],nr['fragments']):
   oldbindings+=bool(a.get('binding'))
   if a==b:continue
   key=f"{r['table']}|{r['record_id']}"
   good=good and not a.get('binding')and a['t']==b['t']and key in B.scope()['records']and b.get('binding',{}).get('strength')==B.STRENGTH
   new.append(dict(rec_key=r['rec_key'],record_id=r['record_id'],source=r['source'],before=a,after=b))
 ck('311_old_bindings_101_baseline_31_fragments_every_non_target_object',good and oldbindings==311 and ba==101 and bf==31,old_bindings=oldbindings,baseline_answers=ba,baseline_fragments=bf,new_fragments=len(new))
 oldpd={p['cid']:p for p in oldp};ck('three_old_complete_profiles_entire_objects_unchanged',all(p==oldpd[p['cid']]for p in newp if p['cid']in [29,2020,5023]))
 ck('all_profile_noncoverage_objects_unchanged',all({k:v for k,v in p.items()if k not in ['coverage','status']}=={k:v for k,v in oldpd[p['cid']].items()if k not in ['coverage','status']}for p in newp))
 uses=collections.defaultdict(list)
 for p in newp:
  for g in p['groups']:
   for ref in g['records']:uses[ref['rec_key']].append(dict(cid=p['cid'],name=p['name'],group=g['group'],reference_field=ref['reference_field'],character_source=p['charainfo_source']))
 # Standard JSON + source pointers; independent of Table.get and B.raw_audit.
 apk=json.loads((C.BASE_MASTER/'_mdCharacter.json').read_bytes())['charainfo'];cache=json.loads((C.DECODED/'charainfo.data5.json.raw').read_bytes())['charainfo'];selected={}
 for layer,rr in [('CACHE',cache),('APK',apk)]:
  for idx,r in enumerate(rr):selected.setdefault(r['cid'],(r,layer,idx))
 st=json.loads((C.BASE_MASTER/'_mdSkill.json').read_bytes())['skilllist'];cache_skills=json.loads((C.DECODED/'skilllist.data5.json.raw').read_bytes())['skilllist'];selected_st={}
 for layer,rr in [('CACHE',cache_skills),('APK',st)]:
  for idx,r in enumerate(rr):selected_st.setdefault(r['skillid'],(r,layer,idx))
 targets={s['record_id']for s in B.scope()['records'].values()};rawrefs=[];rawparents=[]
 for cid,(r,layer,i)in sorted(selected.items()):
  for slot,sid in enumerate(r.get('skillid')or []):
   if slot>0 and sid in targets:rawrefs.append(dict(target=sid,cid=cid,slot=f'skillid[{slot}]',layer=layer,pointer=f'/charainfo/{i}',raw_sha256=B.B6.digest(r)))
 for sid,(r,layer,i)in sorted(selected_st.items()):
  for subidx,sub in enumerate(r.get('sub')or []):
   if sub in targets:rawparents.append(dict(target=sub,parent=sid,index=subidx,layer=layer,raw_sha256=B.B6.digest(r)))
 declared=rows(OUT/'raw_charainfo_references.jsonl')
 expected=[dict(target=r['target'],cid=r['cid'],slot=r['slot'],layer=r['source']['layer'],pointer=r['source']['json_pointer'],raw_sha256=r['raw_sha256'])for r in declared]
 order=lambda rr:sorted(rr,key=lambda r:(r['target'],r['cid'],r['slot']))
 ck('stdlib_all_selected_charainfo_and_reverse_sub_census',order(rawrefs)==order(expected)and len(rawrefs)==28 and not rawparents,selected_charainfo=len(selected),selected_skills=len(selected_st),references=len(rawrefs),outside_player=[r for r in declared if not r['included']],reverse_subs=rawparents)
 ledger=[];rawchecks=[];entries={}
 for p in rows(BASE/'links/character_skills.jsonl'):
  for g in p['groups']:
   for e in g['records']:
    key=f"{e.get('table')}|{e.get('reference_id')}"
    if key in B.scope()['records']:entries[key]=e
 for item in new:
  key=f"skilllist|{item['record_id']}";s=B.scope()['records'][key];source=item['source'];raw=st[int(source['json_pointer'].split('/')[-1])];r=after[item['rec_key']]
  ok=B.B6.digest(raw)==source['raw_record_sha256']==s['entry_sha256']and raw['skillid']==item['record_id']and not raw['sub']
  for f in item['after']['binding']['fields']+item['after']['binding']['condition_fields']:
   aa=next(a for a in r['answers']if a['f']==f['f']);ok=ok and f['raw']==raw[f['f'][1:]]and all(f[k]==aa[k]for k in ['raw','value','kind','unit','status','rule_key'])and f['evidence_scope']==aa['scope']
  rawchecks.append(dict(record_id=item['record_id'],source=source,passed=ok));ledger.append(dict(item,raw_record=raw,page_uses=uses[item['rec_key']],all_contexts=s['contexts'],raw_audit=s['raw_audit'],subgroup=s['subgroup']))
 ck('stdlib_exact_source_target_and_condition_values_units_scopes',len(rawchecks)==28 and all(x['passed']for x in rawchecks),records=len(rawchecks))
 def test(label,e,f,a,ch,accept=False,**kw):
  binding,reason=B.bind(e,f,a,ch,**kw);passed=binding is not None if accept else binding is None
  if accept:passed=passed and binding==after[B.scope()['records'][f"skilllist|{e['reference_id']}"]['rec_key']]['fragments'][0]['binding']
  boundaries.append(dict(name=label,passed=passed,reason=reason))
 for key,s in B.scope()['records'].items():
  e=entries[key];r=after[s['rec_key']];f=s['fragment'];a=r['answers'];ch=r['children'];sid=s['record_id']
  test(f'{sid} positive_exact_full_binding',e,f,a,ch,True)
  if sid not in [30021410,30624410,30829410]:continue
  test(f'{sid} added_clause',e,f+'さらにHPが回復する',a,ch)
  test(f'{sid} wrong_beneficiary',e,f.replace('自身の','敵の'),a,ch)
  for val in ['MISSING',None,0.,1. if e['record']['param0']==2 else 2.]:
   z=copy.deepcopy(e)
   if val=='MISSING':z['record'].pop('param0')
   else:z['record']['param0']=val
   test(f'{sid} threshold_{val}',z,f,a,ch)
  z=copy.deepcopy(a);z.append(copy.deepcopy(z[0]));test(f'{sid} local_duplicate',e,f,z,ch)
  z=copy.deepcopy(a);z[0]['scope']='IN_REVIEWED_VIEW'if z[0]['scope']!='IN_REVIEWED_VIEW'else'BY_TYPE_EXTRAPOLATED';test(f'{sid} scope_change',e,f,z,ch)
  z=copy.deepcopy(e);z['source']['raw_record_sha256']='0'*64;test(f'{sid} source_hash',z,f,a,ch)
  z=copy.deepcopy(e);z['layer']='CACHE';test(f'{sid} layer_change',z,f,a,ch)
  test(f'{sid} unexpected_child',e,f,a,[dict(table='skilllist',record_id=999)])
  test(f'{sid} missing_context',e,f,a,ch,actual_contexts=[])
 # Actual provider overlays: root/local/links remain untouched.
 sample=next(iter(B.scope()['records']));s=B.scope()['records'][sample];e=entries[sample];r=after[s['rec_key']];f=s['fragment'];a=r['answers'];sid=s['record_id'];base=B.tables()
 def overlay(label,changes=None,removed=(),duplicate_table=None,duplicate_id=None):
  changes=changes or {}
  class Provider:
   def __call__(self,table):
    original=base(table)
    class T:
     def __init__(self):
      self.cache=copy.copy(original.cache);self.apk=copy.copy(original.apk)
      if table==duplicate_table:
       which=self.cache if duplicate_id in self.cache else self.apk;which[duplicate_id]=list(which[duplicate_id])+[which[duplicate_id][0]]
     def ids(self):return (original.ids()|{i for t,i in changes if t==table})-{i for t,i in removed if t==table}
     def get(self,i):return changes.get((table,i),original.get(i))
    return T()
  with patch.object(B,'tables',return_value=Provider()):test(label,e,f,a,r['children'])
 raw,ly=base('skilllist').get(sid);changed=copy.deepcopy(raw);changed['param1']+=.1;overlay('real_raw_root_numeric_change',{('skilllist',sid):(changed,ly)})
 overlay('real_raw_root_source_layer_change',{('skilllist',sid):(raw,'CACHE')})
 overlay('duplicate_original_root_row',duplicate_table='skilllist',duplicate_id=sid)
 owner=s['raw_audit']['raw_charainfo_references'][0]['cid'];cr,cl=base('charainfo').get(owner);changed=copy.deepcopy(cr);changed['skillid'][2]=sid;changed['skillid'][3]=0;overlay('real_raw_owner_slot_moves',{('charainfo',owner):(changed,cl)})
 changed=copy.deepcopy(cr);changed['cid']=990001;overlay('new_outside_roster_raw_reference',{('charainfo',990001):(changed,cl)})
 overlay('removed_raw_owner',removed=[('charainfo',owner)])
 changed=copy.deepcopy(cr);changed['home']=99;overlay('real_owner_identity_source_change',{('charainfo',owner):(changed,cl)})
 overlay('duplicate_original_owner_row',duplicate_table='charainfo',duplicate_id=owner)
 changed=copy.deepcopy(raw);changed['skillid']=990002;changed['sub']=[sid];overlay('new_reverse_sub_parent_not_in_links',{('skilllist',990002):(changed,ly)})
 test('changed_roster_identity',e,f,a,r['children'],actual_membership={})
 with patch.object(B,'native_ready',return_value=False):test('native_evidence_not_ready',e,f,a,r['children'])
 ck('all_positive_and_material_refusal_boundaries',all(x['passed']for x in boundaries),passed_cases=sum(x['passed']for x in boundaries),total_cases=len(boundaries))
 ss0=C.load_json(BEFORE/'summary.json');ss1=C.load_json(BASE/'profiles/summary.json');trans=[dict(cid=p['cid'],before=oldpd[p['cid']]['status'],after=p['status'])for p in newp if p['status']!=oldpd[p['cid']]['status']]
 inc=dict(independent_review_status='P3B10_PENDING_INDEPENDENT_D',field_answers_added_pages=ss1['totals']['rule_answers']-ss0['totals']['rule_answers'],field_answers_added_normalized_rows=ss1['totals']['rule_answers_unique_records']-ss0['totals']['rule_answers_unique_records'],field_answers_added_parent_holder_keys=ss1['totals']['rule_answers_parent_holder_keys']-ss0['totals']['rule_answers_parent_holder_keys'],fragments_added_unique_records=len(ledger),fragments_added_page_references=sum(len(x['page_uses'])for x in ledger),effect_slots_added_unique_records=sum(len(x['after']['binding']['fields'])for x in ledger),effect_slots_added_page_references=sum(len(x['page_uses'])*len(x['after']['binding']['fields'])for x in ledger),affected_cids=sorted({p['cid']for x in ledger for p in x['page_uses']}),subgroups=dict(collections.Counter(x['subgroup']for x in ledger)),before_totals=ss0['totals'],after_totals=ss1['totals'],before_status=ss0['status_counts'],after_status=ss1['status_counts'],status_transitions=trans)
 ck('actual28_increment_zero_fields_original_denominators_unknowns',len(ledger)==28 and len(inc['affected_cids'])==28 and all(inc[k]==0 for k in ['field_answers_added_pages','field_answers_added_normalized_rows','field_answers_added_parent_holder_keys'])and ss1['totals']['fragments_attributed_confirmed']-ss0['totals']['fragments_attributed_confirmed']==28 and all(ss0['totals'][k]==ss1['totals'][k]for k in ['descriptions','unexplained_fields','broken_links','descriptions_internal_label']))
 ck('all2236_original_status_algorithm',all(p['status']==('仅未知'if not(p['coverage']['answers']+p['coverage']['baseline_answers'])else'完整'if p['coverage']['descriptions']==p['coverage']['fragments_attributed_confirmed']and p['coverage']['broken_links']==0 else'部分')for p in newp)and len(newp)==2236)
 # Independently read current weaponlist bytes and locate complete declared rows.
 wd=json.loads(B.WEAPONS.read_bytes());weapon_checks=[]
 for key,spec in B.scope()['records'].items():
  for d in spec['declared_weapons']:
   owner,layer,idx=selected[d['cid']]
   for w in d['weapons']:
    matches=[dict(pointer=f'/weaponlist/{i}',raw_record=z,raw_sha256=B.B6.digest(z),type_present='type'in z,type_value=z.get('type'))for i,z in enumerate(wd['weaponlist'])if type(z.get('id'))is type(owner.get(w['character_field']))and z.get('id')==owner.get(w['character_field'])]
    weapon_checks.append(dict(record_id=spec['record_id'],cid=d['cid'],field=w['character_field'],passed=w['present']==(w['character_field']in owner)and w['value']==owner.get(w['character_field'])and matches==w['rows']))
 ck('stdlib_all_declared_weapon_pointers_complete_rows_missing_types',len(weapon_checks)==56 and all(x['passed']for x in weapon_checks))
 C.write_json(OUT/'weapon_raw_crosscheck.json',dict(weapon_source_sha256=C.sha256_file(B.WEAPONS),checks=weapon_checks))
 # Distinct source/missing/null/zero/bool and exact-object refusal samples.
 key='skilllist|30829410';spec=B.scope()['records'][key];e=entries[key];r=after[spec['rec_key']];f=spec['fragment'];a=r['answers'];ch=r['children'];wid=spec['declared_weapons'][0]['weapons'][0]['value']
 for label,value in [('added_zero',0),('added_null',None),('added_bool',True),('added_type',1)]:
  changed=copy.deepcopy(wd)
  next(z for z in changed['weaponlist']if z.get('id')==wid)['type']=value
  test('missing_type_'+label,e,f,a,ch,actual_weapon_document=changed)
 changed=copy.deepcopy(wd);changed['weaponlist']=[z for z in changed['weaponlist']if z.get('id')!=wid];test('declared_weapon_row_removed',e,f,a,ch,actual_weapon_document=changed)
 changed=copy.deepcopy(wd);changed['weaponlist'].append(copy.deepcopy(next(z for z in changed['weaponlist']if z.get('id')==wid)));test('declared_weapon_row_duplicate',e,f,a,ch,actual_weapon_document=changed)
 normal=copy.deepcopy(wd);key='skilllist|30021410';spec=B.scope()['records'][key];e=entries[key];r=after[spec['rec_key']];f=spec['fragment'];a=r['answers'];ch=r['children'];wid=spec['declared_weapons'][0]['weapons'][0]['value']
 for label,op in [('delete_type','delete'),('type_null',None),('type_zero',0),('type_bool',True)]:
  changed=copy.deepcopy(wd);w=next(z for z in changed['weaponlist']if z.get('id')==wid)
  if op=='delete':w.pop('type')
  else:w['type']=op
  test('known_weapon_'+label,e,f,a,ch,actual_weapon_document=changed)
 for label,value in [('str','bad'),('inf',float('inf')),('nan',float('nan')),('bool',True),('null',None),('zero',0)]:
  changed=copy.deepcopy(e);changed['record']['flag0_0']=value;test('weapon_selector_'+label,changed,f,a,ch)
 changed=copy.deepcopy(e);changed['table']='bossskill';test('ordinary_boss_same_numeric_id_not_transferred',changed,f,a,ch)
 z=copy.deepcopy(a);z[0]['unit']='WRONG';test('complete_local_unit_changed',e,f,z,ch)
 z=list(reversed(a));test('complete_local_order_changed',e,f,z,ch)
 # Update the boundary aggregate after the weapon-specific samples.
 checks[next(i for i,x in enumerate(checks)if x['name']=='all_positive_and_material_refusal_boundaries')].update(passed=all(x['passed']for x in boundaries),passed_cases=sum(x['passed']for x in boundaries),total_cases=len(boundaries))
 cli=[];env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936')
 for cid in [214,8294,8296,13211]:
  for mode in ['json','text']:
   run=subprocess.run([sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),'--cid',str(cid)]+(['--json']if mode=='json'else[]),cwd=C.ROOT,env=env,capture_output=True);(OUT/f'cli_{cid}_{mode}.log').write_bytes(run.stdout+run.stderr)
   ok=run.returncode==0 and not run.stderr
   if mode=='json':ok=ok and json.loads(run.stdout.decode('utf-8'))['characters'][0]['cid']==cid
   cli.append(dict(cid=cid,mode=mode,passed=ok))
 ck('representative_real_GBK_json_and_text',all(x['passed']for x in cli),samples=cli)
 C.write_jsonl(OUT/'bindings.jsonl',ledger);C.write_json(OUT/'increment.json',inc);C.write_json(OUT/'raw_crosscheck.json',dict(roots=rawchecks,all_raw_references=rawrefs,reverse_subs=rawparents));C.write_json(OUT/'boundary_validation.json',dict(checks=boundaries,passed=sum(x['passed']for x in boundaries),total=len(boundaries)));C.write_json(OUT/'validation.json',dict(status='C_SELF_CHECK_NOT_INDEPENDENT_D',checks=checks,passed=sum(x['passed']for x in checks),total=len(checks)));C.write_json(OUT/'source_manifest.json',dict(snapshot=C.SNAPSHOT_ID,records=[dict(record_id=x['record_id'],source=x['source'],page_uses=x['page_uses'],contexts=x['all_contexts'],raw_audit=x['raw_audit'])for x in ledger],native_evidence='reused_native_evidence.json'))
 C.write_csv(OUT/'bindings.csv',['record_id','cids','fragment','field_raw_values','condition','text_relation','subgroup'],[[x['record_id'],','.join(str(u['cid'])for u in x['page_uses']),x['after']['t'],canon([dict(field=f['f'],raw=f['raw'],unit=f['unit'])for f in x['after']['binding']['fields']]),x['after']['binding']['condition'],x['after']['binding']['text_condition_relation'],x['subgroup']]for x in ledger])
 print(json.dumps(dict(passed=sum(x['passed']for x in checks),total=len(checks),boundaries=f"{sum(x['passed']for x in boundaries)}/{len(boundaries)}",fragments=len(ledger),effectslots=inc['effect_slots_added_unique_records'],failed=[x['name']for x in checks if not x['passed']]),ensure_ascii=False))
 if not all(x['passed']for x in checks):raise SystemExit(1)
if __name__=='__main__':main()
