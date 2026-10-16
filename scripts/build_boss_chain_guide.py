"""Add evidence-backed Boss parameter views without changing accepted exports."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path('output/cache_full_20261015_v3');OUT=Path('output/boss_chain')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):
 (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 if isinstance(data,list) and data:
  with (OUT/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader()
   for r in data:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
rows=[json.loads(s) for s in (ROOT/'records.jsonl').read_text(encoding='utf-8').splitlines()]
skills=[r for r in rows if r['table']=='bossskill'];patterns=[r for r in rows if r['table']=='bosspattern']
card=next(r for r in rows if r['table']=='charainfo' and r['raw'].get('cid')==2327)
# Statements are local handler semantics, not battle outcome formulas.
rules=[
 (27,'skillparam1','单次回复量的技能基值系数','getBasicSkillAttack(true) × 原值，再经0x14374bc转换；后续Heal另行处理','系数','5416.txt:118ba2c–118ba3c','一定間隔ごとに上限を超えて小回復する'),
 (27,'skillparam2','回复间隔输入','直接存入_regenerationTimeMax；更新时按传入delta倒计时','传入delta的时间单位；尚未在此链确认秒','5416.txt:118ba5c/118bac4;7077.txt;7078.txt','一定時間、一定間隔ごとに'),
 (27,'skillparam3','回复次数','float向零截断为整数，存入_regenerationNum；每次调用Heal后减1','次','5416.txt:118ba04–118ba28;7078.txt:176f790–176f7a0','一定時間、一定間隔ごとに'),
 (13,'skillparam1','局部攻击增益输入','attackRate=原值×skillChainRate；SupportData._attackUp=1+attackRate','系数；不是最终战斗倍率','5398.txt:1188444–1188474;7084.txt:1776788–177678c','攻撃力と防御力と移動速度が一定時間上がる'),
 (13,'skillparam2','局部固定防御值系数','guardRate=原值×skillChainRate；接受者BattleParam._normalAtk×guardRate经0x14376ec转换后存_guardUp','原值为系数；输出为整数防御值，非减伤百分比','5398.txt:1188454–1188468;7084.txt:1776790–17767cc','攻撃力と防御力と移動速度が一定時間上がる'),
 (13,'skillparam3','增益持续时间输入','直接作为supportTime；仅>0进入SetSupport_noCheckTime','内部时间输入；此链尚未确认秒','5398.txt:118845c;7083.txt;7084.txt:17767bc–17767e0','一定時間上がる'),
 (13,'skillparam6','局部移动速度增益输入','moveRate=原值×skillChainRate；SupportData._moveUp=1+moveRate','系数；不是最终移动速度','5398.txt:1188458–118846c;7084.txt:17767c4/17767dc','移動速度が一定時間上がる')]
dictionary=[{'file_table':'bossinfo.data5 / bossinfo.bossskill','effect_type':t,'field_path':f,'meaning_zh':zh,'rule':rule,'unit':unit,'status':'已确认（静态代码局部语义）','evidence':ev,'condition':'以Boss skill经initialize_ExAttack进入对应type处理器为前提','example':next(r['raw'][f] for r in skills if r['raw'].get('skillid0')==t and f in r['raw'])} for t,f,zh,rule,unit,ev,fragment in rules]
save('field_dictionary',dictionary)
lookup={(t,f):(zh,rule,unit,ev,frag) for t,f,zh,rule,unit,ev,frag in rules}
view=[]
for r in skills:
 raw=r['raw'];t=raw.get('skillid0')
 if t not in (13,27):continue
 for (rt,f),(zh,rule,unit,ev,frag) in lookup.items():
  if rt!=t or f not in raw:continue
  view.append({'record_key':r['record_key'],'source_sha256':r['source_sha256'],'location':r['location'],'skillid':raw['skillid'],'type':t,'field':f,'raw_value':raw[f],'meaning_zh':zh,'rule':rule,'unit':unit,'status':'CONFIRMED_STATIC_LOCAL','evidence':ev})
save('verified_parameter_views',view)
chosen=[p for p in patterns if p['raw'].get('patternid') in (40232700,40232701,40232702)]
assert len(chosen)==3
byid={r['raw']['skillid']:r for r in skills};sample=[];chains=[]
for p in chosen:
 pr=p['raw'];ordered=[]
 for slot in range(7):
  key=f'skillid{slot}'
  if key not in pr:continue
  sid=pr[key];ordered.append({'slot':slot,'id':sid,'record_key':byid[sid]['record_key'] if sid in byid else None})
  if sid not in byid:continue
  r=byid[sid];raw=r['raw'];t=raw.get('skillid0')
  for f,v in raw.items():
   if not f.startswith('skillparam') and not f.startswith(('flag','skillflag')):continue
   info=lookup.get((t,f));sample.append({'cid':2327,'card_name_ja':card['raw']['title']+' '+card['raw']['name'],'version':'APK code 5.6.2/56021; cache_full_20261015_v3 (current load unknown)','patternid':pr['patternid'],'skill_name_ja':pr.get('sname'),'description_ja':pr.get('sinfo'),'description_translation_zh':None,'description_fragment':info[4] if info else None,'slot':slot,'boss_skillid':sid,'type':t,'record_key':r['record_key'],'location':r['location'],'field':f,'raw_value':v,'meaning_zh':info[0] if info else None,'interpretation':info[1] if info else None,'unit':info[2] if info else None,'status':'CONFIRMED_STATIC_LOCAL' if info else 'UNKNOWN_IN_THIS_SUPPLEMENT','evidence':info[3] if info else None,'conditions':'需选中本pattern且执行到此段；当前装载/玩家状态未证实'})
 chains.append({'pattern_record':p,'ordered_present_slots':ordered,'selection_status':'NOT_OBSERVED_IN_GAME'})
save('cid2327_description_fields',sample)
save('cid2327_chain',{'card_record':card,'patterns':chains,'boss_records':[byid[i] for i in range(40232700,40232706)],'source_rule':'JSON table lookup per ID, null result falls back to AB table; no field merge; loaded snapshot unknown','limits':['pattern列出顺序不保证每段在任意场景执行','同号Boss技能与普通能力是不同命名空间','未对缺失字段填默认值','截图强化回复2倍不替换缓存原值1.75','首次update时计时器为0，会调用Heal；15次与间隔2不能直接证明30秒完整持续时间']})
checks={'rules':len(dictionary),'expanded_present_fields':len(view),'expanded_records':len({v['record_key'] for v in view}),'sample_fields':len(sample),'sample_patterns':len(chosen),'checks':[{'name':'sample_three_patterns_six_records','pass':set(s['boss_skillid'] for s in sample)==set(range(40232700,40232706))},{'name':'ordered_three_stage_types','pass':all([byid[x['id']]['raw']['skillid0'] for x in c['ordered_present_slots']]==[116,27,13] for c in chains)},{'name':'native_fragment_checks','pass':all(c['pass'] for c in json.loads((OUT/'native_checks.json').read_text())['checks'])}]}
assert all(c['pass'] for c in checks['checks']);save('guide_checks',checks)
inputs=[ROOT/'records.jsonl',Path('work/protection/il2cpp_loader_seed1.bin'),Path('work/protection/metadata_aei_decoded.bin')]
manifest={'inputs':{str(p):sha(p) for p in inputs},'scripts':{str(p):sha(p) for p in map(Path,['scripts/boss_chain_trace.py','scripts/boss_chain_probe.py','scripts/build_boss_chain_guide.py'])},'payloads':{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'},'status':'supplement; not independently reviewed; original outputs unchanged'}
save('manifest',manifest)
print(json.dumps(checks,ensure_ascii=False))
