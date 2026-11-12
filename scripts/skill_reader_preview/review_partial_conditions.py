"""Review necessary limit/terrain gates for the frozen 45-item denominator."""
import argparse,json,hashlib
from pathlib import Path
from rerun_output import read_path, require_new_files, review_output, write_new_text
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
REPORT=review_output('partial-conditions', args.output)/'audit/trigger45_evidence_20261107/partial_conditions_receipt.json'
require_new_files(REPORT)
hashes={}
def read(rel):
 content=read_path(ROOT/rel, root=ROOT).read_bytes();hashes[rel]=hashlib.sha256(content).hexdigest();return json.loads(content.decode('utf-8-sig'))
def pin(rel):hashes[rel]=hashlib.sha256(read_path(ROOT/rel, root=ROOT).read_bytes()).hexdigest()
inrel='output/character_skills/reader_full_20261106/audit/trigger_evidence_20261107/branch_invariance_receipt.json'
a=[x for x in read(inrel)['items'] if x['branchInvariant'] is False]
assert len(a)==45
terrain=read('output/ordinary_effects/ability7/trace.json');ctrl=read('output/character_skills/reader_full_20261106/audit/trigger45_evidence_20261107/controller_fields.json')
assert [(f['name'],f['offset']) for f in ctrl['fields']]==[('_pattern','0x10'),('_useNum','0x18')]
assert ctrl['native_sha256']==terrain['native_sha256'] and ctrl['metadata_sha256']==terrain['metadata_sha256']
for rel in ['output/character_skills/reader_full_20261106/audit/trigger45_evidence_20261107/native_context_excerpt.txt','output/character_skills/reader_full_20261106/audit/player_conditions_20261107/native_conditions.txt','output/boss_chain/5174.txt','output/ordinary_effects/ability7/README.md']:pin(rel)
tables={}
for layer,rel in [('APK','output/base_master/_mdBossInfo.json'),('CACHE','output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw')]:
 d=read(rel);d=d if layer=='APK' else d['bossinfo'];tables[layer]=(rel,'' if layer=='APK' else '/bossinfo',{r['patternid']:(i,r) for i,r in enumerate(d['bosspattern'])})
results=[]
for old in a:
 s=old['source'];rel,prefix,table=tables[s['layer']];i,p=table[s['branchId']];partial=[];evidence=[];known=[]
 cardrel=f"output/character_skills/pages/{old['cid']}/card.json";card=read(cardrel)
 context=[{'reference':sk['reference_field'],'parent':sk['record_id'],'layer':sk['layer'],'original':sk['original_text']} for g in card['groups'] if g['group']=='special_move' for sk in g['skills'] if sk.get('record_id') in old['allCohortParents']]
 limit=p.get('limit',0)
 if isinstance(limit,int) and limit>0:
  partial.append(f'本分支已使用次数＜{limit}次');known.append('PER_PATTERN_USE_COUNT_UPPER_BOUND')
  evidence.extend([{'file':'output/character_skills/reader_full_20261106/audit/trigger45_evidence_20261107/controller_fields.json','pointer':'/fields/1','fact':'BossPatternCtrl._useNum offset0x18'}, {'file':'output/character_skills/reader_full_20261106/audit/trigger45_evidence_20261107/native_context_excerpt.txt','rva':'0x100a5f8..0x100a5fc','fact':'x23=controller.pattern; x25=controller'}, {'file':'output/character_skills/reader_full_20261106/audit/player_conditions_20261107/native_conditions.txt','rva':'0x100a720..0x100a738','fact':'positive limit requires _useNum < limit'}, {'file':'output/boss_chain/5174.txt','lines':[45,51,111,117,142,148],'fact':'FindPatternCtrl then increments _useNum by1'}])
 bgf=p.get('bgf',0)
 if isinstance(bgf,int) and bgf>0:
  matches=[(j,r['raw']) for j,r in enumerate(terrain['background_source_records']) if r['raw']['flag'] & bgf]
  names=set(r['bg_name'] for _,r in matches)
  label=None
  if bgf==8192 and matches and all('夜' in n for n in names):label='地形：夜间'
  elif bgf==1114112 and matches and all(n.replace('夜','') in ('砂浜','船上','海中') for n in names):label='地形：沙滩／船上／海中（含夜间）'
  elif bgf==32768 and names=={'高地'}:label='地形：高地'
  if label:
   partial.append(label);known.append('CURRENT_TERRAIN_FLAG_INTERSECTION')
   evidence.extend([{'file':'output/character_skills/reader_full_20261106/audit/trigger45_evidence_20261107/native_context_excerpt.txt','rva':'0x100a2cc..0x100a300','fact':'GetStageNo -> GetBgFlag -> sp+0x24'}, {'file':'output/character_skills/reader_full_20261106/audit/player_conditions_20261107/native_conditions.txt','rva':'0x100a634..0x100a644','fact':'bgf nonzero requires (currentStageFlag & bgf)!=0'}, {'file':'output/ordinary_effects/ability7/trace.json','pointers':[f'/background_source_records/{j}/raw' for j,_ in matches],'fact':'Exact background source names and flags; never infer complement for bgf0'}])
 results.append({'cid':old['cid'],'rowId':old['rowId'],'source':s,'partialCondition':' · '.join(partial),'necessaryConditions':known,'conditionKnown':False,'displayStatus':'purple','remainingReason':'分支选取待确认' if partial else '本项尚无本次可接入的limit／地形必要条件','evidence':evidence,'parentSource':{'file':rel,'pointer':f'{prefix}/bosspattern/{i}'},'parentRaw':p,'mainlineCard':{'file':cardrel,'sha256':hashes[cardrel]},'fullCohortProse':context,'limits':['limit为每个pattern控制器自身计数，不能解成整个技能的第N次使用。','计数重置/完整priority选择和其他资格门未闭合，不解除紫色。','bgf0不代表非夜间/非水边；limit0不代表第二次以后。']})
report={'schema':1,'scope':'Partial necessary-condition receipt only. No upgrade to inferred or confirmed; no mainline writes.','inputs':hashes,'stats':{'denominator':len(results),'partialItems':sum(bool(x['partialCondition']) for x in results),'limitItems':sum('PER_PATTERN_USE_COUNT_UPPER_BOUND' in x['necessaryConditions'] for x in results),'terrainItems':sum('CURRENT_TERRAIN_FLAG_INTERSECTION' in x['necessaryConditions'] for x in results)},'items':results}
for rel,h in hashes.items():assert hashlib.sha256(read_path(ROOT/rel, root=ROOT).read_bytes()).hexdigest()==h,rel
write_new_text(REPORT, json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report['stats']))
