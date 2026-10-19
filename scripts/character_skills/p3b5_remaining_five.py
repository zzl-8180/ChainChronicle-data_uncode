"""P3B5 independent raw JSON audit, delta ledger and zero-breakage accounting."""
from __future__ import annotations
import collections,csv,hashlib,json,os,subprocess,sys
from pathlib import Path
import common as C
BASE=C.ROOT/'output/character_skills';OUT=BASE/'remaining_five';BEFORE=C.ROOT/'work/character_skills_p3b5/before'
def rows(p):return [json.loads(x) for x in Path(p).open(encoding='utf8')]
def canon(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def holders(rr):
 for r in rr:
  for h in [r]+r['children']:yield r['rec_key'],h
def main():
 C.enable_utf8_console();checks=[]
 def check(name,ok,**detail):checks.append(dict(name=name,passed=bool(ok),**detail))
 old,now=rows(BEFORE/'profiles/records.jsonl'),rows(BASE/'profiles/records.jsonl')
 oldp,newp=rows(BEFORE/'profiles/profiles.jsonl'),rows(BASE/'profiles/profiles.jsonl')
 def mult(rr):return collections.Counter((parent,r['table'],r['record_id'],canon(a)) for parent,r in holders(rr) for a in r['answers'])
 ca,cb=mult(old),mult(now);added=cb-ca
 check('old_complete_answer_objects_and_multiplicity_preserved',not ca-cb,before=sum(ca.values()),lost=sum((ca-cb).values()))
 ra,rb=C.load_json(BEFORE/'profiles/rules.json'),C.load_json(BASE/'profiles/rules.json');newkeys=set(rb)-set(ra)
 expected_keys={'bossskill|24|/skillparam3','bossskill|56|/skillparam2','bossskill|68|/skillparam4',*[f'bossskill|73|/skillparam{s}' for s in [5,6,7]]}
 check('all_old_rule_objects_preserved_and_only_six_new_rules',all(rb[k]==v for k,v in ra.items()) and newkeys==expected_keys,before=len(ra),after=len(rb))
 check('only_six_fields_added',all(json.loads(k[3])['rule_key'] in newkeys for k in added),rows=sum(added.values()))
 curr={r['rec_key']:r for r in now}
 check('baseline101_31_type8_type26_and_all_fragments_unchanged',all(r['baseline_answers']==curr[r['rec_key']]['baseline_answers'] and r['fragments']==curr[r['rec_key']]['fragments'] for r in old))
 binding=[p for folder in ['description_bindings/type8','type26_mana'] for p in (BEFORE/folder).glob('*.json*') if 'bindings' in p.name or 'type8' in str(p.parent)]
 check('all_old_binding_bytes_preserved',all(p.read_bytes()==(BASE/p.relative_to(BEFORE)).read_bytes() for p in binding),files=len(binding))
 uses=collections.defaultdict(list)
 for p in newp:
  for g in p['groups']:
   for ref in g['records']:uses[ref['rec_key']].append(dict(cid=p['cid'],name=p['name'],group=g['group'],reference_field=ref['reference_field']))
 ledger=[]
 for parent,r in holders(now):
  for a in r['answers']:
   if a['rule_key'] in newkeys:ledger.append(dict(parent_rec_key=parent,table=r['table'],record_id=r['record_id'],effect_type=r['effect_type'],source=r['source'],answer=a,page_references=uses[parent]))
 # Original documents are read directly with stdlib. Missing old source pointers
 # are resolved by the actual layer/table/ID, retaining all duplicate candidates.
 docs={};source_maps={};source_paths={}
 for layer,table,path,pointer in [('APK','charainfo',C.ROOT/'output/base_master/_mdCharacter.json','/charainfo'),('APK','bossskill',C.ROOT/'output/base_master/_mdBossInfo.json','/bossskill'),('CACHE','charainfo',C.ROOT/'output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw','/charainfo'),('CACHE','bossskill',C.ROOT/'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw','/bossinfo/bossskill')]:
  payload=path.read_bytes();doc=json.loads(payload);rr=doc
  for part in pointer.strip('/').split('/'):rr=rr[part]
  byid=collections.defaultdict(list)
  for i,r in enumerate(rr):byid[r['cid'] if table=='charainfo' else r['skillid']].append((pointer+'/'+str(i),r))
  source_maps[layer,table]=byid;source_paths[layer,table]=path
  docs[path]=(payload,hashlib.sha256(payload).hexdigest())
 results=[];sources={};null_pointer=0
 for entry in ledger:
  a=entry['answer'];s=entry['source'];layer=s['layer'];table=entry['table'];rid=entry['record_id'];p=source_paths[layer,table]
  choices=source_maps[layer,table][rid]
  if s.get('json_pointer'):choices=[q for q in choices if q[0]==s['json_pointer']]
  elif s.get('raw_record_sha256'):choices=[q for q in choices if hashlib.sha256(canon(q[1]).encode()).hexdigest()==s['raw_record_sha256']]
  else:null_pointer+=1
  if len(choices)!=1:raise ValueError(f'ambiguous original source {table} {rid}: {len(choices)}')
  pointer,raw=choices[0];field=a['f'][1:];v=raw[field];t=raw['skillid'][0] if table=='charainfo' else raw['skillid0'];text=f'{v:.7g}'
  if t==24:expected=f'施法结束阈值：caster._behaviorTime + {text} 游戏秒（非目标异常时长）'
  elif t==56:
   if raw['skillflag0_0']==32:expected=f'默认异常时长系数 ×{text}；仅bit5 SetStop分支请求10×{text} 游戏秒（非实际持续保证）'
   elif raw['skillflag0_0']==128:expected=f'默认异常时长系数 ×{text}；仅bit7 SetSlow分支请求60×{text} 游戏秒，速度输入0.5（非实际持续保证）'
   else:raise ValueError('unreviewed type56 flag')
  elif t==68:expected=f'ManaCycle计时阈值 {text} 游戏秒（仅正阈值计时路径；返还仍有门控）'
  elif field=='skillparam5':expected=f'玩家炮击候选遍历入口时间阈值 {text} 游戏秒' if v>0 else '本项非正：不启用正时间入口阈值'
  elif field=='skillparam6':expected=f'玩家炮击候选遍历入口正次数门槛 {int(v)} 次（向零整数化；非正冷却同轮可越过）' if int(v)>=1 else f'整数化为 {int(v)}：不启用正次数入口门槛'
  else:expected=f'每次发射后冷却重置 {text} 游戏秒（正值停止本轮继续遍历；第一发不预等）'
  digest=hashlib.sha256(canon(raw).encode()).hexdigest()
  original_blob=(docs[p][0][s['byte_begin']:s['byte_end_exclusive']]
                 if layer=='CACHE' and s.get('byte_begin') is not None else canon(raw).encode())
  original_digest=hashlib.sha256(original_blob).hexdigest()
  ok=(t==entry['effect_type'] and a['raw']==v and a['value']==expected and a['scope']=='BY_TYPE_EXTRAPOLATED' and
      json.loads(original_blob)==raw and (not s.get('raw_record_sha256') or original_digest==s['raw_record_sha256']) and 'E/F0' in a['note'])
  results.append(dict(parent_rec_key=entry['parent_rec_key'],table=table,record_id=rid,field=a['f'],layer=layer,original_file=str(p.relative_to(C.ROOT)),
     json_pointer=pointer,file_sha256=docs[p][1],canonical_record_sha256=digest,raw=v,expected=expected,passed=ok,
     original_pointer_was_null=not bool(s.get('json_pointer'))))
  sources[layer,table,pointer]=dict(layer=layer,table=table,record_id=rid,file=str(p.relative_to(C.ROOT)),json_pointer=pointer,
                                 file_sha256=docs[p][1],canonical_record_sha256=digest,record=raw)
 check('every_new_row_independent_original_json_value_type_pointer_hash',all(r['passed'] for r in results) and len(results)==sum(added.values()),rows=len(results),sources=len(sources),old_null_pointer_rows=null_pointer)
 # CACHE source preference checked against the original whole table, with no
 # per-field borrowing. APK rows must not replace any cache row of the same ID.
 check('cache_whole_record_precedence_and_no_field_fallback',all(r['layer']!='APK' or r['table']!='bossskill' or r['record_id'] not in source_maps['CACHE','bossskill'] for r in results))
 s0,s1=C.load_json(BEFORE/'profiles/summary.json'),C.load_json(BASE/'profiles/summary.json');t0,t1=s0['totals'],s1['totals']
 page=sum(len(r['page_references']) for r in ledger);keys={(r['parent_rec_key'],r['table'],r['record_id'],r['answer']['rule_key'],r['answer']['f']) for r in ledger}
 desc=['descriptions','descriptions_attributed','descriptions_with_hint','descriptions_from_baseline','descriptions_reviewed_bindings','descriptions_unexplained','fragments_attributed_confirmed']
 check('three_calibers_and_unknown_field_delta',page==t1['rule_answers']-t0['rule_answers']==t0['unexplained_fields']-t1['unexplained_fields'] and len(ledger)==t1['rule_answers_unique_records']-t0['rule_answers_unique_records'] and len(keys)==t1['rule_answers_parent_holder_keys']-t0['rule_answers_parent_holder_keys'])
 check('baseline_scope_description_broken_link_invariants',t1['baseline_answers']==101 and t1['broken_links']==3 and t1['rule_answers_in_reviewed_view']==t0['rule_answers_in_reviewed_view'] and all(t1[k]==t0[k] for k in desc))
 oldby={p['cid']:p for p in oldp};trans=[dict(cid=p['cid'],name=p['name'],before=oldby[p['cid']]['status'],after=p['status']) for p in newp if p['status']!=oldby[p['cid']]['status']]
 check('five_state_transitions_independently_recomputed',{p['cid'] for p in trans}=={4009,4049,8116,8151,10018} and all(p['before']=='仅未知' and p['after']=='部分' for p in trans) and all((p['coverage']['answers']>0)==(p['status']!='仅未知') for p in newp))
 target=[]
 for cid in [4009,4049,8116,8151,10018]:
  hit=[r for r in ledger if any(x['cid']==cid for x in r['page_references'])]
  target.append(dict(cid=cid,rows=[dict(parent=r['parent_rec_key'],table=r['table'],record_id=r['record_id'],source=r['source'],answer=r['answer']) for r in hit]))
 imuka=next(r for r in target if r['cid']==8151)
 import equivalence as EQ
 gate=EQ.classify(8151)
 chara_raw=source_maps['APK','charainfo'][8151][0][1]
 boss_raw=source_maps['APK','bossskill'][30815100][0][1]
 all_ten=all(chara_raw[f'skillparam{s}']==boss_raw[f'skillparam{s}'] for s in range(10))
 gate_trace=dict(classification=gate,field_gates=[dict(field=f'/skillparam{s}',allowed=EQ.field_allowed(8151,f'/skillparam{s}')[0],
     reason=EQ.field_allowed(8151,f'/skillparam{s}')[1],charainfo_value=chara_raw[f'skillparam{s}'],boss_record_id=30815100,boss_value=boss_raw[f'skillparam{s}']) for s in [5,6,7]],
     independent_direct_original_ten_slots_equal=all_ten,eq_source='scripts/character_skills/equivalence.py',eq_not_modified=True)
 C.write_json(OUT/'imuka_gate_trace.json',gate_trace)
 boss_imuka=[r for r in imuka['rows'] if r['table']=='bossskill' and r['parent'].startswith('bosspattern|')]
 denju_imuka=[r for r in imuka['rows'] if r['table']=='bossskill' and r['parent'].startswith('denju|')]
 chara_imuka=[r for r in imuka['rows'] if r['table']=='charainfo']
 check('imuka_boss_source_two_patterns_plus_existing_equal_value_E0_alias',len(boss_imuka)==6 and
       all(r['record_id']==30815100 for r in boss_imuka) and {r['parent'].split('|')[1] for r in boss_imuka}=={'30815100','30815101'} and
       len(chara_imuka)==3 and len(denju_imuka)==3 and all(r['record_id']==81510 for r in denju_imuka) and
       all(any(q['answer']['f']==r['answer']['f'] and q['answer']['raw']==r['answer']['raw'] for q in boss_imuka) for r in chara_imuka) and
       all_ten and gate['all_ten_slots_equal'] and 7 in gate['applicable_slots'] and all(r['allowed'] and r['reason']=='E0' for r in gate_trace['field_gates']),
       field_gates=gate_trace['field_gates'],all_ten_slots_equal=all_ten)
 cli=[];env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936')
 for cid in [4009,4049,8116,10018,8151,30236]:
  run=subprocess.run([sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),'--cid',str(cid),'--json'],cwd=C.ROOT,env=env,capture_output=True)
  (OUT/f'cli_{cid}_json.log').write_bytes(run.stdout+run.stderr)
  ok=run.returncode==0 and not run.stderr and json.loads(run.stdout.decode('utf8'))['characters'][0]['cid']==cid
  cli.append(dict(cid=cid,passed=ok,returncode=run.returncode))
 check('six_default_gbk_json_queries',all(r['passed'] for r in cli),samples=cli)
 affected={u['cid'] for r in ledger for u in r['page_references']}
 inc=dict(field_answers_added_pages=page,field_answers_added_normalized_rows=len(ledger),field_answers_added_parent_holder_keys=len(keys),
          field_source_records=len(sources),field_source_layers=dict(collections.Counter(r['layer'] for r in sources.values())),field_affected_characters=len(affected),field_affected_cids=sorted(affected),
          fields_by_rule=dict(collections.Counter(r['answer']['rule_key'] for r in ledger)),fragments_added_unique_records=0,fragments_added_page_references=0,
          effect_slots_added_unique_records=0,effect_slots_added_page_references=0,status_transitions=trans,before_status=s0['status_counts'],after_status=s1['status_counts'],
          before_totals=t0,after_totals=t1,independent_review_status='P3B5_PENDING')
 C.write_jsonl(OUT/'field_answers.jsonl',ledger);C.write_jsonl(OUT/'source_records.jsonl',list(sources.values()));C.write_json(OUT/'raw_crosscheck.json',dict(rows=len(results),passed=sum(r['passed'] for r in results),distinct_sources=len(sources),results=results))
 C.write_json(OUT/'increment.json',inc);C.write_json(OUT/'target_five.json',target)
 C.write_json(OUT/'validation.json',dict(checks=checks,passed=sum(r['passed'] for r in checks),total=len(checks)))
 print(json.dumps(dict(new_pages=page,new_rows=len(ledger),new_keys=len(keys),affected=len(affected),sources=len(sources),checks=f"{sum(r['passed'] for r in checks)}/{len(checks)}"),ensure_ascii=False))
 if not all(r['passed'] for r in checks):raise SystemExit(1)
def freeze():
 files=[C.ROOT/'scripts/character_skills'/x for x in ['remaining_five.py','p3b5_remaining_five.py','p3b5_dom.js','rules.py','profiles.py','verify_p1.py','crosscheck_raw.py']]
 files += [BASE/x for x in ['README.md','P3B5_HANDOFF.md']]
 for folder in ['remaining_five','profiles','gaps','charainfo_params']:
  files += [p for p in (BASE/folder).rglob('*') if p.is_file() and p.name not in ['frozen_manifest.json']]
 files += [BASE/'denju_skills/p7_increment.json',BASE/'boss_attack_types/p8_increment.json',BASE/'validation/crosscheck_raw.json']
 files += [C.ROOT/'docs/tasks/20261019-character-skills-p3b5-remaining-five.md']
 files += [C.ROOT/'HANDOFF.md',C.ROOT/'STATUS.md']
 historical=[C.ROOT/'work/character_skills_p3b1/before'/x for x in ['rules.json','records.jsonl','profiles.jsonl']]
 rows=[dict(path=str(p.relative_to(C.ROOT)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(set(files))]
 C.write_json(OUT/'frozen_manifest.json',dict(status='P3B5_PENDING_INDEPENDENT_D_REVIEW',files=rows,
  readonly_historical_scope=[dict(path=str(p.relative_to(C.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in historical]))
 print(f'frozen {len(rows)} files')
if __name__=='__main__':
 if '--freeze' in sys.argv:freeze()
 else:main()
