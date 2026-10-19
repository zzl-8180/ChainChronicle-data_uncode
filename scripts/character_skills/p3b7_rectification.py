"""F1 only: raw-reference guards and exact R1-object preservation; no old rewrites."""
import collections,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
from unittest.mock import patch
import common as C
import p3b7_bindings as B
BASE=C.ROOT/'output/character_skills';OUT=B.OUT
BEFORE=C.ROOT/'work/character_skills_p3b7/rectification_f1_before'
def rows(p):return [json.loads(s)for s in p.open(encoding='utf-8')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 C.enable_utf8_console();checks=[];boundaries=[]
 def ck(name,ok,**kw):checks.append(dict(name=name,passed=bool(ok),**kw))
 # Original JSON is read independently of the new scan/helper for the census.
 cache=json.loads((C.DECODED/'charainfo.data5.json.raw').read_bytes())['charainfo']
 apk=json.loads((C.BASE_MASTER/'_mdCharacter.json').read_bytes())['charainfo']
 cache_sources={r['raw']['cid']:r for r in rows(C.RECORDS_JSONL)if r.get('table')=='charainfo'}
 selected={}
 for layer,doc,path in [('CACHE',cache,'output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw'),('APK',apk,'output/base_master/_mdCharacter.json')]:
  for i,r in enumerate(doc):selected.setdefault(r['cid'],(r,layer,path,f'/charainfo/{i}'))
 playable={r['cid']:r for r in json.loads(C.ROSTER_JSON.read_bytes())}
 other={r['cid']:r for r in json.loads(C.ROSTER_OTHER_JSON.read_bytes())}
 profiles=rows(BASE/'profiles/profiles.jsonl');links=rows(BASE/'links/character_skills.jsonl')
 pids={p['cid']for p in profiles};lids={p['cid']for p in links};targets={s['record_id']for s in B.scope()['records'].values()}
 direct=[]
 for cid,(r,layer,path,pointer)in sorted(selected.items()):
  for slot,target in enumerate(r.get('skillid')or []):
   if slot<1 or target not in targets:continue
   source=dict(original_file=path,json_pointer=pointer,raw_record_sha256=B.B6.digest(r),canonical_record_sha256=B.B6.digest(r))
   if layer=='CACHE':
    source['original_file']=cache_sources[cid]['original_file'];source['raw_record_sha256']=cache_sources[cid]['location']['raw_record_sha256']
   direct.append(dict(target=target,cid=cid,slot=f'skillid[{slot}]',layer=layer,decoded_json_file=path,source=source,in_playable_roster=cid in playable,in_profiles=cid in pids,in_links=cid in lids,roster_category=playable.get(cid,{}).get('category'),other_category=other.get(cid,{}).get('category'),raw_is_enemy=r.get('is_enemy'),raw_rarity=r.get('rarity'),included_in_player_output=cid in playable and cid in pids and cid in lids))
 actual=rows(OUT/'raw_charainfo_references.jsonl')
 def small(r):return dict(**{k:r[k]for k in ['target','cid','slot','layer','decoded_json_file','in_playable_roster','in_profiles','in_links','roster_category','other_category','raw_is_enemy','raw_rarity','included_in_player_output']},source={k:r['source'][k]for k in ['original_file','json_pointer','raw_record_sha256','canonical_record_sha256']})
 sort=lambda xs:sorted(xs,key=lambda x:(x['target'],x['cid'],x['slot']))
 excluded=[r for r in direct if not r['included_in_player_output']]
 ck('independent_whole_record_selection_census_82_equals80plus2',sort(direct)==sort([small(r)for r in actual])and len(direct)==82 and sum(r['included_in_player_output']for r in direct)==80 and set(playable)==pids==lids and len(pids)==2236,raw_references=len(direct),included=80,excluded=excluded,selected_raw_charainfo=len(selected))
 entries={}
 def walk(x):
  if isinstance(x,dict):
   key=f"{x.get('table')}|{x.get('reference_id')}"
   if x.get('resolved')and key in B.scope()['records']:entries[key]=x
   for k,v in x.items():
    if k not in ['record','source','charainfo_source']:walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 for p in links:walk(p)
 records={r['rec_key']:r for r in rows(BASE/'profiles/records.jsonl')}
 ledger=rows(OUT/'bindings.jsonl')
 for item in ledger:
  e=entries[f"skilllist|{item['record_id']}"];r=records[item['rec_key']]
  binding,reason=B.bind(e,item['after']['t'],r['answers'],r['children'])
  boundaries.append(dict(name=f"positive_preserve_full_binding_{item['record_id']}",passed=binding==item['after']['binding'],actual=reason))
 e=entries['skilllist|3233'];r=next(r for r in records.values()if r['table']=='skilllist'and r['record_id']==3233)
 f=next(f['t']for f in r['fragments']if f.get('binding',{}).get('template_id')=='p3b7_type26_start_mana_exact_digit')
 root_pin=B.B6.digest(e);link_pin=B.B6.digest(B.B6.contexts()['skilllist|3233']);original=B.tables()
 def test_overlay(label,changed=None,removed=()):
  changed=changed or {}
  class Overlay:
   def __call__(self,table):
    base=original(table)
    if table!='charainfo':return base
    class T:
     def ids(self):return (base.ids()|set(changed))-set(removed)
     def get(self,cid):return changed[cid]if cid in changed else base.get(cid)
    return T()
  with patch.object(B,'tables',return_value=Overlay()):
   binding,reason=B.bind(e,f,r['answers'],r['children'])
  boundaries.append(dict(name=label,passed=binding is None and reason=='RAW_CHARAINFO_DIRECT_REFERENCES_CHANGED'and B.B6.digest(e)==root_pin and B.B6.digest(B.B6.contexts()['skilllist|3233'])==link_pin,actual=reason,root_and_links_unchanged=True))
 raw,layer=original('charainfo').get(75370)
 added=copy.deepcopy(raw);added['cid']=990001
 test_overlay('new_raw_non_roster_reference_not_in_links',{990001:(added,layer)})
 raw75528,layer75528=original('charainfo').get(75528)
 changed=copy.deepcopy(raw75528);changed['skillid'][2]=3233;changed['skillid'][3]=0
 test_overlay('existing_other_raw_reference_slot_moves_3_to_2',{75528:(changed,layer75528)})
 test_overlay('remove_existing_outside_roster_charainfo',removed=[75370])
 changed=copy.deepcopy(raw);changed['skillid'][2]=0
 test_overlay('remove_target_from_raw_skill_array',{75370:(changed,layer)})
 changed=copy.deepcopy(raw);changed['title']='F1 source-only fixture'
 test_overlay('raw_reference_source_hash_changes_with_same_cid_and_slot',{75370:(changed,layer)})
 test_overlay('raw_reference_selected_source_layer_changes',{75370:(copy.deepcopy(raw),'CACHE')})
 player,playerlayer=original('charainfo').get(8054);changed=copy.deepcopy(player);changed['skillid'].append(3233)
 test_overlay('extra_slot_in_existing_player_while_links_unchanged',{8054:(changed,playerlayer)})
 loader=C.load_json
 for name,path in [('roster_membership',C.ROSTER_JSON),('other_category',C.ROSTER_OTHER_JSON)]:
  altered=copy.deepcopy(loader(path))
  if name=='roster_membership':altered.append(dict(copy.deepcopy(other[75370]),category='playable'))
  else:next(x for x in altered if x['cid']==75370)['category']='F1 changed category'
  def replacement(p):return altered if Path(p)==path else loader(p)
  B.reference_membership.cache_clear()
  with patch.object(C,'load_json',side_effect=replacement):binding,reason=B.bind(e,f,r['answers'],r['children'])
  B.reference_membership.cache_clear()
  boundaries.append(dict(name=name+'_identity_change',passed=binding is None and reason=='RAW_REFERENCE_OUTPUT_SCOPE_CHANGED',actual=reason,root_and_links_unchanged=True))
 ck('raw_reference_guard_80_positive_and9_real_table_scope_changes',all(x['passed']for x in boundaries),passed_cases=sum(x['passed']for x in boundaries),total=len(boundaries))
 snapshot=C.load_json(BEFORE/'snapshot_manifest.json');product_rows=[x for x in snapshot['files']if x['path'].replace('\\','/').startswith(('output/character_skills/profiles/','output/character_skills/gaps/'))]
 identical=[dict(path=x['path'],unchanged=sha(C.ROOT/x['path'])==x['sha256'])for x in product_rows]
 ck('all12_formal_products_byte_identical_to_R1_including_every_binding_and_unknown',len(identical)==12 and all(x['unchanged']for x in identical),products=identical)
 oldrecords=rows(BEFORE/'output/character_skills/profiles/records.jsonl');newrecords=list(records.values())
 def answers(rr):return collections.Counter((row['rec_key'],h['table'],h['record_id'],json.dumps(a,ensure_ascii=False,sort_keys=True))for row in rr for h in [row]+row['children']for a in h['answers'])
 oldbindings=[f['binding']for row in oldrecords for f in row['fragments']if f.get('binding')];newbindings=[f['binding']for row in newrecords for f in row['fragments']if f.get('binding')]
 ck('complete82013_answers_duplicates_112_bindings_and_all_original_profile_state_objects',answers(oldrecords)==answers(newrecords)and sum(answers(newrecords).values())==82013 and oldbindings==newbindings and len(oldbindings)==112 and rows(BEFORE/'output/character_skills/profiles/profiles.jsonl')==profiles and C.load_json(BEFORE/'output/character_skills/profiles/rules.json')==C.load_json(BASE/'profiles/rules.json')and C.load_json(BEFORE/'output/character_skills/profiles/summary.json')==C.load_json(BASE/'profiles/summary.json'),full_binding_objects=len(newbindings))
 frozen=C.load_json(OUT/'frozen_manifest.json');allowed={'scripts/character_skills/p3b7_bindings.py','scripts/character_skills/p3b7_binding_scope.json','HANDOFF.md','STATUS.md','docs/tasks/20261019-character-skills-p3b7-batch-bindings.md','output/character_skills/README.md','output/character_skills/description_bindings/p3b7_batch/README.md'}
 protected=[x for x in frozen['files']+frozen['readonly_dependencies']if x['path'].replace('\\','/')not in allowed]
 changed=[x['path']for x in protected if sha(C.ROOT/x['path'])!=x['sha256']]
 ck('all_R1_native_validation_boundary_ledgers_and_other_protected_files_preserved',not changed,protected_files=len(protected),changed=changed)
 cli=[];env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936')
 for mode in ['json','text']:
  run=subprocess.run([sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),'--cid','8054']+(['--json']if mode=='json'else[]),cwd=C.ROOT,env=env,capture_output=True)
  (OUT/f'rectification_cli_8054_{mode}.log').write_bytes(run.stdout+run.stderr)
  cli.append(dict(mode=mode,returncode=run.returncode,passed=run.returncode==0 and not run.stderr))
 ck('affected8054_real_gbk_json_text',all(x['passed']for x in cli),samples=cli)
 C.write_json(OUT/'rectification_validation.json',dict(status='C_F1_SELF_CHECK_NOT_D_R2',checks=checks,passed=sum(x['passed']for x in checks),total=len(checks),boundaries=boundaries,independent_raw_reference_census=direct))
 print(json.dumps(dict(passed=sum(x['passed']for x in checks),total=len(checks),boundary_passed=sum(x['passed']for x in boundaries),boundary_total=len(boundaries)),ensure_ascii=False))
 if not all(x['passed']for x in checks):raise SystemExit(1)

if __name__=='__main__':main()
