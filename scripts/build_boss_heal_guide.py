"""Merge verified Boss local rules with cap/time evidence; preserve raw/source fields."""
import json,csv,hashlib
from pathlib import Path
OLD=Path('output/boss_chain');OUT=Path('output/boss_heal')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):
 (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 if isinstance(data,list) and data:
  keys=list(dict.fromkeys(k for r in data for k in r))
  with (OUT/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
   for r in data:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
e=load(OUT/'constants.json');rules=load(OLD/'field_dictionary.json')
time_evidence='6979.txt:176c938/176c93c/176cca8/176d874;3622.txt;constants.json time_getter + Unity2021.3 API docs'
for r in rules:
 r['evidence']='../boss_chain/'+r['evidence']
 if (r['effect_type'],r['field_path']) in ((27,'skillparam2'),(13,'skillparam3')):
  r['unit']='游戏秒（fixedDeltaTime累计；非现实墙钟秒）';r['evidence']+=';'+time_evidence
rules.append({'file_table':'bossinfo.data5 / bossinfo.bossskill','effect_type':27,'field_path':'skillflag0_1','meaning_zh':'技能标志高32位中的超上限回复档位','rule':'高32位移位后按Constants.s_flagList反序选首个已设置位，对应s_valueList；只解释超上限掩码覆盖的位，其余位保持未知','unit':'HP上限比率；不是回复量倍数','status':'已确认（静态代码及受控原生片段）','evidence':'34609.txt:1a6f728–1a6f748;7355.txt;7358.txt;6370.txt:1541418–15414c8;constants.json;checks.json','condition':'type27进入Heal且未被更早条件中止；HealSkill_HealFlag还可能合入能力标志，所以原标志算出的档位不是最终实机承诺','example':1024})
save('field_dictionary',rules)
rulemap={(r['effect_type'],r['field_path']):r for r in rules}
def cap(high):
 flag=(high&0xffffffff)<<32
 for bit,rate in reversed(list(zip(e['bits']['values'],e['values']['values']))):
  if flag&(1<<bit):return {'bit':bit,'rate_float32':rate,'rate_display':round(rate,6),'hp_cap_rule':'truncate_toward_zero(hpMax * rate_float32); positive small-normal HP only tested'}
 return {'bit':None,'rate_float32':1.0,'rate_display':1.0,'hp_cap_rule':'no over-heal bit in this high word'}
records=[json.loads(l) for l in Path('output/cache_full_20261015_v3/records.jsonl').open(encoding='utf-8')]
skills={r['raw']['skillid']:r for r in records if r['table']=='bossskill'}
views=load(OLD/'verified_parameter_views.json')
for v in views:
 rule=rulemap[(v['type'],v['field'])];v['unit']=rule['unit'];v['evidence']=rule['evidence'];v['raw_flag_cap']=None
for r in skills.values():
 raw=r['raw']
 if raw.get('skillid0')!=27 or 'skillflag0_1' not in raw:continue
 rule=rulemap[(27,'skillflag0_1')]
 views.append({'record_key':r['record_key'],'source_sha256':r['source_sha256'],'location':r['location'],'skillid':raw['skillid'],'type':27,'field':'skillflag0_1','raw_value':raw['skillflag0_1'],'meaning_zh':rule['meaning_zh'],'rule':rule['rule'],'unit':rule['unit'],'status':'CONFIRMED_STATIC_LOCAL','evidence':rule['evidence'],'raw_flag_cap':cap(raw['skillflag0_1'])})
save('verified_parameter_views',views)
samples=load(OLD/'cid2327_description_fields.json')
for s in samples:
 s['raw_flag_cap']=None
 assert skills[s['boss_skillid']]['raw'][s['field']]==s['raw_value']
 rule=rulemap.get((s['type'],s['field']))
 if rule:
  s.update(unit=rule['unit'],evidence=rule['evidence'],meaning_zh=rule['meaning_zh'],interpretation=rule['rule'],status='CONFIRMED_STATIC_LOCAL')
 if s['type']==27 and s['field']=='skillflag0_1':
  s['description_fragment']='上限を超えて小回復する';s['raw_flag_cap']=cap(s['raw_value']);s['conditions']+=';'+rule['condition']
save('cid2327_description_fields',samples)
chain=load(OLD/'cid2327_chain.json')
expected=[]
for p in chain['patterns']:
 for slot in p['ordered_present_slots']:
  row=skills[slot['id']]['raw']
  expected += [(p['pattern_record']['raw']['patternid'],slot['slot'],slot['id'],f) for f in row if f.startswith(('skillparam','skillflag','flag'))]
assert [(s['patternid'],s['slot'],s['boss_skillid'],s['field']) for s in samples]==expected
native=load(OUT/'checks.json');assert len(native['checks'])==13 and all(r['pass'] for r in native['checks'])
# CSV must not silently lose a raw field or any relation/value from JSON.
with (OUT/'cid2327_description_fields.csv').open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f))
assert len(csvrows)==len(samples)==54
for c,j in zip(csvrows,samples):assert c['field']==j['field'] and json.loads(c['raw_flag_cap'] or 'null')==j['raw_flag_cap']
checks={'status':'PASS','rules':len(rules),'sample_rows':len(samples),'sample_flag_rows':sum(s['field'].startswith('skillflag') for s in samples),'expanded_fields':len(views),'expanded_records':len({v['record_key'] for v in views}),'native_checks':13,'checks':['all sample param and flag fields match source with order','CSV rows and complex cap values match JSON','13 native cap checks pass'],'limits':['No real game observation','Only raw flag cap, ability flags may alter result','All previous unresolved relations retained in v3 analysis']};save('guide_checks',checks)
inputs=[OLD/'field_dictionary.json',OLD/'verified_parameter_views.json',OLD/'cid2327_description_fields.json',Path('output/cache_full_20261015_v3/records.jsonl'),Path('work/protection/metadata_aei_decoded.bin'),Path('work/protection/il2cpp_loader_seed1.bin')]
save('manifest',{'inputs':{str(p):sha(p) for p in inputs},'scripts':{str(p):sha(p) for p in map(Path,['scripts/boss_heal_trace.py','scripts/boss_heal_probe.py','scripts/build_boss_heal_guide.py'])},'payloads':{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'},'review_status':'implementation self-check only; not independent review'})
print(json.dumps(checks,ensure_ascii=False))
