"""Derive limited terrain/use-stage selection labels from actual source order.
Writes one new report. No mainline writes.
"""
import argparse,json,hashlib,re,sys
from pathlib import Path
from rerun_output import read_path, require_new_files, review_output, write_new_text
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
REPORT=review_output('selection-order', args.output)/'audit/selection_order_20261107/selection_receipt.json'
require_new_files(REPORT)
hashes={};cache={}
def read(rel):
 data=read_path(ROOT/rel, root=ROOT).read_bytes();hashes[rel]=hashlib.sha256(data).hexdigest()
 if rel not in cache:cache[rel]=json.loads(data.decode('utf-8-sig'))
 return cache[rel]
def filehash(rel):hashes[rel]=hashlib.sha256(read_path(ROOT/rel, root=ROOT).read_bytes()).hexdigest()
def locate(ref):
 rel=ref.get('file') or ref.get('original_file');ptr=ref.get('pointer') or ref.get('json_pointer')
 if ref.get('source_key')=='CACHE/charainfo.data5.json.raw':rel='output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw'
 value=read(rel)
 for k in ptr.split('/')[1:]:value=value[int(k)] if isinstance(value,list) else value[k]
 return rel,ptr,value
def choose(records,counts,stageflag=0,draw=0,mana=None):
 eligible=[p for p in records if (not p.get('limit',0) or counts[p['patternid']]<p['limit']) and (not p.get('bgf',0) or p['bgf']&stageflag) and (mana is None or p.get('mns',0)==p.get('mne',0)==0 or p.get('mns',0)<=mana<=p.get('mne',0))]
 if not eligible:return None
 total=sum(p.get('priority',0) for p in eligible);acc=0
 for p in eligible:
  prev=acc;acc+=p.get('priority',0)
  if prev<=draw<acc:return p['patternid']
 return eligible[0]['patternid']
# Counterexamples: weights are not max-priority; zero total preserves order.
assert choose([{'patternid':1,'priority':100},{'patternid':2,'priority':50}],{1:0,2:0},draw=125)==2
assert choose([{'patternid':2},{'patternid':1}],{1:0,2:0})==2
inp='output/character_skills/reader_full_20261106/audit/trigger_evidence_20261107/branch_invariance_receipt.json'
items=[x for x in read(inp)['items'] if x['branchInvariant'] is False];assert len(items)==45
proof=read('output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/native_selection_proof.json');assert proof['randomRangeInt']['native_rva']=='0x190732c';assert [x['name'] for x in proof['randomRangeInt']['parameters']]==['minInclusive','maxExclusive']
mana_proof=read('output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/mana_timing_receipt.json')
for rel,digest in {**mana_proof['sourceHashes'],**mana_proof['methodExcerptHashes']}.items():
 filehash(rel);assert hashes[rel]==digest,rel
mana_labels={(p['layer'],p['patternId']):p for p in mana_proof['parentLabels']}
for rel,expected in [('work/protection/il2cpp_loader_seed1.bin',proof['nativeSHA256']),('work/protection/metadata_aei_decoded.bin',proof['metadataSHA256'])]:filehash(rel);assert hashes[rel]==expected
terrain=read('output/ordinary_effects/ability7/trace.json');assert terrain['native_sha256']==proof['nativeSHA256']
for rel in ['output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/4928_think_attack.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/4927_getPatternAttackList.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/4090_makeExAttackPatternList.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/5174_CreateExecSkillList.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/5176_FindPatternCtrl.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/9116_GetExecSkillInfo.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/setListPattern.txt']:filehash(rel)
tables={}
for layer,rel in [('APK','output/base_master/_mdBossInfo.json'),('CACHE','output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw')]:
 data=read(rel);data=data if layer=='APK' else data['bossinfo'];tables[layer]=(rel,'' if layer=='APK' else '/bossinfo',{p['patternid']:(i,p) for i,p in enumerate(data['bosspattern'])})
results=[]
for old in items:
 s=old['source'];cid=old['cid'];layer=s['layer'];rel,prefix,table=tables[layer];pid=s['branchId'];parent=table[pid][1]
 cardrel=f'output/character_skills/pages/{cid}/card.json';card=read(cardrel);ref=next(f['source'] for f in card['basic']['fields'] if f.get('source',{}).get('json_pointer','').startswith('/charainfo/'));cf,cp,chara=locate(ref)
 refs=sorted([(int(k[7:]),k,v) for k,v in chara.items() if re.fullmatch(r'pattern\d+',k) and isinstance(v,int) and v],key=lambda x:x[0]);referenceids=[v for _,_,v in refs]
 records=[table[v][1] for _,_,v in refs if v in table and table[v][1].get('sname','')==parent.get('sname','') and table[v][1].get('flag',0)==parent.get('flag',0)]
 same_flag_other_names=[v for _,_,v in refs if v in table and table[v][1].get('flag',0)==parent.get('flag',0) and table[v][1].get('sname','')!=parent.get('sname','')]
 pageids={sk['record_id'] for g in card['groups'] if g['group']=='special_move' for sk in g['skills'] if sk.get('table')=='bosspattern'}
 valid=set(referenceids)==pageids and all(v in table for v in referenceids) and len(referenceids)==len(set(referenceids)) and len(records)>=2 and not same_flag_other_names
 # Known mode context only; no unknown flags, HP/chain/mana/position gates.
 valid=valid and parent.get('flag',0) in (0,4,256,8192,8448,32768)
 valid=valid and all(p.get('hpstart',0)==0 and p.get('hpend',0)==100 and all(p.get(k,0)==0 for k in ('chs','che','posp','pose','tid')) and p.get('priority',0)>=0 for p in records)
 no_mana=all(p.get(k,0)==0 for p in records for k in ('mns','mne'))
 kind=None;label=None;probes=[];reason='Not an admitted deterministic terrain/use-stage cohort'
 if valid and no_mana and all(p.get('bgf',0)==0 for p in records):
  # Exact linear chain: earlier controllers used once; final controller unlimited.
  n=len(records);limits=[p.get('limit',0) for p in records];weights=[p.get('priority',0) for p in records]
  prose=''.join(p.get('sinfo','') for p in records)
  if limits==[1]*(n-1)+[0] and weights[0]>0 and all(w==0 for w in weights[1:]):
   counts={p['patternid']:0 for p in records};sequence=[]
   for cast in range(n+2):
    total=sum(p.get('priority',0) for p in records if not p.get('limit',0) or counts[p['patternid']]<p['limit']);draws=range(total) if total else [0]
    selected={choose(records,counts,draw=d) for d in draws};assert len(selected)==1
    picked=selected.pop();sequence.append(picked);probes.append({'cast':cast+1,'countsBefore':dict(counts),'eligibleWeightTotal':total,'selected':picked});counts[picked]+=1
   assert sequence==[p['patternid'] for p in records]+[records[-1]['patternid']]*2
   index=[p['patternid'] for p in records].index(pid);kind='linear_per_mode_controller_lifetime'
   if set(map(int,re.findall(r'最大(\d+)回',prose)))=={n-1} and re.search(r'使用.*(?:上が|変動)',prose):
    label='初始' if index==0 else f'使用后强化{index}次'+('（最大）' if index==n-1 else '')
   else:label='初次施放' if index==0 else ('初次施放后' if n==2 else f'当前技能状态已施放{index}次'+('及以后' if index==n-1 else ''))
   reason='Deterministic after fresh controller-list construction; explicit-ID execution increments selected controller once.'
 if valid and no_mana and len(records)==2 and all(p.get('limit',0)==0 for p in records):
  bases=[p for p in records if p.get('bgf',0)==0 and p.get('priority',0)==0];strength=[p for p in records if p.get('bgf',0) in (8192,1114112) and p.get('priority',0)>0]
  if len(bases)==len(strength)==1:
   mask=strength[0]['bgf'];matches=[x['raw'] for x in terrain['background_source_records'] if x['raw']['flag']&mask]
   names={x['bg_name'] for x in matches};safe=(mask==8192 and all('夜' in x for x in names)) or (mask==1114112 and all(x.replace('夜','') in ('砂浜','船上','海中') for x in names))
   if safe:
    counts={p['patternid']:0 for p in records}
    for background in terrain['background_source_records']:
     bg=background['raw'];total=sum(p.get('priority',0) for p in records if not p.get('bgf',0) or p['bgf']&bg['flag']);draws=range(total) if total else [0]
     picks={choose(records,counts,bg['flag'],d) for d in draws};assert picks=={strength[0]['patternid'] if bg['flag']&mask else bases[0]['patternid']}
     probes.append({'backgroundId':bg['id'],'backgroundFlag':bg['flag'],'backgroundName':bg['bg_name'],'selected':next(iter(picks))})
    kind='deterministic_terrain_weight_pair';name='夜间' if mask==8192 else '沙滩／船上／海中（含夜间）'
    label=f'地形：{name}' if pid==strength[0]['patternid'] else ('其他地形（非夜间）' if mask==8192 else '其他地形（非沙滩／船上／海中）')
    reason='Complement follows full two-record weighted-selection proof, not bgf0 alone.'
 if valid and not no_mana and len(records)==2 and all(p.get('limit',0)==0 and p.get('bgf',0)==0 for p in records):
  known=[mana_labels.get((layer,p['patternid'])) for p in records]
  if all(known) and all(k['raw']==p for k,p in zip(known,records)):
   intervals=sorted((p.get('mns',0),p.get('mne',0)) for p in records)
   if intervals[0][0]==0 and intervals[0][1]+1==intervals[1][0] and intervals[1][1]==12:
    for count in range(13):
     eligible=[p for p in records if p.get('mns',0)<=count<=p.get('mne',0)];assert len(eligible)==1
     total=sum(p.get('priority',0) for p in eligible)
     picks={choose(records,{p['patternid']:0 for p in records},draw=d,mana=count) for d in (range(total) if total else [0])}
     assert picks=={eligible[0]['patternid']};probes.append({'selectorCounter':count,'selected':next(iter(picks))})
    info=mana_labels[(layer,pid)];low,high=info['runtimeRangeInclusive']
    kind='disjoint_preview_counter_ranges';label=(f'选档时废料{low}–{high}个' if info['counter']=='scrap' else f'预测扣费后职业法珠{low}–{high}颗')
    reason='Exact preview counter ranges; ordinary UI executes cached selected ID. No fresh selection after payment or universal before-cost threshold claimed.'
 results.append({'cid':cid,'layer':layer,'branchId':pid,'rowId':old['rowId'],'source':s,'parentRaw':parent,'parentSource':{'file':rel,'pointer':f'{prefix}/bosspattern/{table[pid][0]}'},'selectionResolved':kind is not None,'selectionKind':kind,'conditionLabel':label,'selectionLabel':label,'reason':reason,'scope':'本段技能已具备共同模式资格，当前同一控制器列表/选档预测快照；不是整场战斗永不重置或点击瞬间重新选档。','evidence':[{'file':'output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/native_selection_proof.json','fact':reason},{'file':'output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/mana_timing_receipt.json','fact':'Manual UI predicts with subMana/nextChain, caches selected ID, pays then explicitly executes cached ID; auto overload is separate.'}],'limits':proof['limitations'],'mainlineCard':{'file':cardrel,'sha256':hashes[cardrel]},'characterSource':{'file':cf,'pointer':cp,'patternReferencesInNativeOrder':[{k:v} for _,k,v in refs]},'cohort':{'sameLayer':layer,'sameName':parent.get('sname',''),'sameFlag':parent.get('flag',0),'orderedParents':[{'parentId':p['patternid'],'source':{'file':rel,'pointer':f"{prefix}/bosspattern/{table[p['patternid']][0]}"},'raw':p} for p in records]},'probes':probes,'inheritedBlockers':old['reasonCodes']})
receipt={'schema':1,'inputs':hashes,'nativeEvidence':'output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/native_selection_proof.json','stats':{'denominator':len(results),'selectionResolved':sum(x['selectionResolved'] for x in results),'terrain':sum(x['selectionKind']=='deterministic_terrain_weight_pair' for x in results),'useStages':sum(x['selectionKind']=='linear_per_mode_controller_lifetime' for x in results)},'items':results,'counterexamples':['priority100 vs50 can select50: not max selection','all-zero weights select first eligible: list order matters','auto-think fallback does not itself count use; restricted to explicit-ID manual execution','limit0 does not mean stage2 without full ordered prefix/exhaustion proof','normal/super modes use distinct controllers; not one shared global skill-use count']}
parents={}
for result in results:
 if not result['selectionResolved']:continue
 cohort=result['cohort']['orderedParents'];kind=result['selectionKind'];prose=''.join(p['raw'].get('sinfo','') for p in cohort);n=len(cohort)
 for index,record in enumerate(cohort):
  raw=record['raw'];pid=record['parentId']
  if kind=='linear_per_mode_controller_lifetime':
   if set(map(int,re.findall(r'最大(\d+)回',prose)))=={n-1} and re.search(r'使用.*(?:上が|変動)',prose):label='初始' if index==0 else f'使用后强化{index}次'+('（最大）' if index==n-1 else '')
   else:label='初次施放' if index==0 else ('初次施放后' if n==2 else f'当前技能状态已施放{index}次'+('及以后' if index==n-1 else ''))
  elif kind=='deterministic_terrain_weight_pair':
   mask=next(p['raw']['bgf'] for p in cohort if p['raw'].get('bgf',0));name='夜间' if mask==8192 else '沙滩／船上／海中（含夜间）'
   label=name if raw.get('bgf',0) else ('非夜间' if mask==8192 else '其他地形（非沙滩／船上／海中）')
  else:
   info=mana_labels[(result['layer'],pid)];low,high=info['runtimeRangeInclusive'];label=(f'选档时废料{low}–{high}个' if info['counter']=='scrap' else f'预测扣费后职业法珠{low}–{high}颗')
  item={**result,'branchId':pid,'parentRaw':raw,'parentSource':record['source'],'conditionLabel':label,'selectionLabel':label,'selectionOrder':index}
  item['triggerSource']=item.pop('source');item['triggerRowId']=item.pop('rowId')
  parents[f"{result['layer']}:{pid}"]=item
receipt['parents']=parents;receipt['stats']['mana']=sum(x['selectionKind']=='disjoint_preview_counter_ranges' for x in results);receipt['stats']['resolvedParents']=len(parents)
for rel,h in hashes.items():assert hashlib.sha256(read_path(ROOT/rel, root=ROOT).read_bytes()).hexdigest()==h,rel
write_new_text(REPORT, json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt['stats']));print([(x['cid'],x['source']['branchId'],x['selectionLabel']) for x in results if x['selectionResolved']])
