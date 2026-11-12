"""Bounded read-only CID278 random-pool audit. Writes this work directory only."""
import json,hashlib,re,collections,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/character_skills/reader_full_20261106/audit/final5_evidence_20261107';hashes={}
def read(rel):
 b=(ROOT/rel).read_bytes();hashes[rel]=hashlib.sha256(b).hexdigest();return json.loads(b.decode('utf-8-sig'))
def pin(rel):hashes[rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
pin(Path(__file__).relative_to(ROOT).as_posix())
card=read('output/character_skills/pages/278/card.json');chars=read('output/base_master/_mdCharacter.json')['charainfo'];boss=read('output/base_master/_mdBossInfo.json');chara=chars[119];assert chara['cid']==278
refs=sorted([(int(k[7:]),k,v) for k,v in chara.items() if re.fullmatch(r'pattern\d+',k) and v],key=lambda r:r[0]);assert [v for _,_,v in refs]==[30027800,30027801,30027802,30027803]
patterns={p['patternid']:(i,p) for i,p in enumerate(boss['bosspattern'])};children={p['skillid']:(i,p) for i,p in enumerate(boss['bossskill'])}
pageids={s['record_id'] for g in card['groups'] if g['group']=='special_move' for s in g['skills'] if s.get('table')=='bosspattern'};assert pageids=={v for _,_,v in refs}
allparents=[]
for _,ref,pid in refs:
 i,p=patterns[pid];slots=[(k,v) for k,v in p.items() if re.fullmatch(r'skillid\d+',k) and v];assert slots==[('skillid0',p['skillid0'])]
 bi,b=children[p['skillid0']];allparents.append({'reference':ref,'parentId':pid,'parentRaw':p,'parentSource':{'file':'output/base_master/_mdBossInfo.json','pointer':f'/bosspattern/{i}'},'childId':b['skillid'],'childType':b['skillid0'],'childRaw':b,'childSource':{'file':'output/base_master/_mdBossInfo.json','pointer':f'/bossskill/{bi}'}})
normal=[p for p in allparents if p['parentRaw']['flag']==8];sup=[p for p in allparents if p['parentRaw']['flag']==4]
assert len(normal)==3 and len(sup)==1 and len(normal)+len(sup)==len(allparents)
for p in normal:
 r=p['parentRaw'];assert all(r[k]==0 for k in ('limit','bgf','mns','mne','chs','che','hpstart','posp','pose','tid')) and r['hpend']==100 and r['priority']==100
 assert p['childType']==3 and p['childRaw']['s_ability']==0
rules=read('output/character_skills/profiles/rules.json');rule=rules['bossskill|3|/skillparam1'];assert rule['status'].startswith('已确认')
proof=read('output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/native_selection_proof.json');assert proof['randomRangeInt']['native_rva']=='0x190732c'
for rel,expected in [('work/protection/il2cpp_loader_seed1.bin',proof['nativeSHA256']),('work/protection/metadata_aei_decoded.bin',proof['metadataSHA256'])]:pin(rel);assert hashes[rel]==expected
cache=read('output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/mana_timing_receipt.json');bridge=[x for x in cache['facts'] if x['id'] in ('M4','M5','M6')];assert len(bridge)==3
down_enum=read('output/character_skills/reader_full_20261106/audit/final5_evidence_20261107/native/random/down_enum_metadata.json');assert down_enum['default']['value']==4
for rel in ['output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/4927_getPatternAttackList.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/4928_think_attack.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/8179_PanelCharaInfo_UpdateCharaInfo.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/8166_PanelCharaInfo_GetPatternId.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/7894_InterfaceManager_OnClickSpSkill.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/6377_CharaBehavior_CreateExecSkillList.txt','output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/5174_CreateExecSkillList.txt','output/character_skills/reader_full_20261106/audit/final5_evidence_20261107/native/random/motion_method_entries.json']:pin(rel)
# Enumerate only integer selector intervals, not game/runtime state.
intervals=[];start=0
for p in normal:
 end=start+p['parentRaw']['priority'];intervals.append({'parentId':p['parentId'],'minInclusive':start,'maxExclusive':end,'rawDamageInputCoefficient':p['childRaw']['skillparam1'],'motion':p['childRaw']['spmotname']});start=end
counts=collections.Counter()
for roll in range(start):
 hit=[x['parentId'] for x in intervals if x['minInclusive']<=roll<x['maxExclusive']];assert len(hit)==1;counts[hit[0]]+=1
assert list(counts.values())==[100,100,100]
items=[{'cid':278,'layer':'APK','branchId':x['parentId'],'parentRaw':next(p['parentRaw'] for p in normal if p['parentId']==x['parentId']),'parentSource':next(p['parentSource'] for p in normal if p['parentId']==x['parentId']),'conditionLabel':'普通必杀随机池成员（卡牌图案对应未确认）','randomPoolKnown':True,'selectorMembershipResolved':True,'cardFaceMappingKnown':False,'selectionResolved':False,'coefficient':x['rawDamageInputCoefficient'],'drawInterval':{'minInclusive':x['minInclusive'],'maxExclusive':x['maxExclusive']},'motionName':x['motion']} for x in intervals if x['parentId'] in (30027800,30027801)]
report={'schema':1,'scope':'Normal skill-pool membership and numeric source are resolved; named card-face trigger mapping remains unknown. Do not present per-cast 1/3 empirical probability.','inputs':hashes,'cardSource':{'file':'output/base_master/_mdCharacter.json','pointer':'/charainfo/119'},'mainlineCardSHA256':hashes['output/character_skills/pages/278/card.json'],'completeParents':allparents,'modeGate':{'normal':'flag8 requires !BattleParam.isSSkillGaugeFull','super':'flag4 requires BattleParam.isSSkillGaugeFull','evidence':{'file':'output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/4927_getPatternAttackList.txt','rva':'0x100a7b4..0x100a7d8'}},'randomIntervals':intervals,'integerIntervalCheck':{'rollsChecked':start,'selectedCounts':dict(counts),'meaning':'Per invocation, given uniform integer Range and ordinary preview caller. Not empirical click/cast frequency.'},'cacheExecutionBridge':bridge,'items':items,'openGaps':[{'topic':'Parent to visible card-face mapping','known':'raw boss skills use sp_komodia03 / sp_komodia02 / sp_komodia01; no extracted animation/texture evidence here identifies their actual cards. Numeric suffix is not a card enum.','entryMethods':['BattleBossSkill.get_spmotname @0x1a6ea74','BattleParam.get_SPMotionName @0x10f298c','BattleParam.set_SPMotionName @0x10f29e8','CharaInfoCharaModel.PlaySpMotion @0xda3ea4','CharaInfoModelCtrl.PlaySpMotion @0xdad4b8'],'requiredInputs':['The actual animation/Animator/effect/material/texture references used by sp_komodia01..03 and their source bundle/object identities.'],'neededProof':'Follow each selected boss skill motion to the actual rendered playing-card asset; visually inspect named faces before assigning Joker or suit names.'},{'topic':'Joker status inference','known':'Only 30027802 has skillflag0_0=16 among the normal pool; original prose says Joker adds Down.','missing':'No card-art binding is established by this difference alone; do not use it to assign identities to the other two motions.'},{'topic':'Click frequency','known':'UI caches predicted pattern ID and explicit-ID execution consumes it.','missing':'Prediction refresh schedule and user timing effects are unmeasured; equal weights establish draw intervals only.'}]}
OUT.mkdir(parents=True,exist_ok=True);(OUT/'random_pool_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for rel,h in hashes.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
print(json.dumps({'allParents':len(allparents),'normalPool':len(normal),'superExcluded':len(sup),'drawsChecked':start,'cardFaceMappingKnown':False,'items':len(items)},ensure_ascii=False))
