"""Review the 59 condition-only cases against complete current character refs."""
import argparse, json, hashlib, re
from pathlib import Path
from rerun_output import read_path, require_new_files, review_output, write_new_text
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
REPORT=review_output('branch-invariance', args.output)/'audit/trigger_evidence_20261107/branch_invariance_receipt.json'
require_new_files(REPORT)
hashes={}; loaded={}
def read(rel):
 p=read_path(ROOT/rel, root=ROOT); content=p.read_bytes(); hashes[rel]=hashlib.sha256(content).hexdigest()
 if rel not in loaded:loaded[rel]=json.loads(content.decode('utf-8-sig'))
 return loaded[rel]
def locate(ref):
 rel=ref.get('file') or ref.get('original_file'); ptr=ref.get('pointer') or ref.get('json_pointer')
 if ref.get('source_key')=='CACHE/charainfo.data5.json.raw':rel='output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw'
 x=read(rel)
 for k in ptr.split('/')[1:]:x=x[int(k)] if isinstance(x,list) else x[k]
 return rel,ptr,x
changes_rel='output/character_skills/reader_full_20261106/audit/remaining_evidence_20261107/changes.json'
items=[x for x in read(changes_rel)['changes'] if x['after']['status']=='purple' and x['after']['bindingKnown']]
tables={}
for layer,rel in [('APK','output/base_master/_mdBossInfo.json'),('CACHE','output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw')]:
 d=read(rel);d=d if layer=='APK' else d['bossinfo']; prefix='' if layer=='APK' else '/bossinfo'
 skillrel='output/base_master/_mdSkill.json' if layer=='APK' else 'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw'
 tables[layer]={'file':rel,'prefix':prefix,'parents':{x['patternid']:(i,x) for i,x in enumerate(d['bosspattern'])},'boss':{x['skillid']:(i,x) for i,x in enumerate(d['bossskill'])},'abilities':{x['skillid']:(i,x) for i,x in enumerate(read(skillrel)['skilllist'])},'skillFile':skillrel}
results=[]
for old in items:
 s=old['source']; cid=old['cid']; layer=s['layer']; meta=tables[layer]; cardrel=f'output/character_skills/pages/{cid}/card.json';card=read(cardrel)
 pid=s['branchId']; raw=meta['parents'][pid][1]
 cref=next(f['source'] for f in card['basic']['fields'] if f.get('source',{}).get('json_pointer','').startswith('/charainfo/'))
 cf,cp,chara=locate(cref); charrefs={k:v for k,v in chara.items() if re.fullmatch(r'pattern\d+',k) and isinstance(v,int) and v!=0}
 page_refs={sk['record_id'] for g in card['groups'] if g['group']=='special_move' for sk in g['skills'] if sk.get('table')=='bosspattern'}
 reasons=[]
 if set(charrefs.values())!=page_refs:reasons.append('DENOMINATOR_CHARA_PAGE_REFERENCE_MISMATCH')
 if not set(charrefs.values())<=set(meta['parents']):reasons.append('DENOMINATOR_NOT_ALL_RESOLVED_IN_SAME_LAYER')
 cohort=[(ident,meta['parents'][ident]) for ident in dict.fromkeys(charrefs.values()) if ident in meta['parents'] and meta['parents'][ident][1].get('sname','')==raw.get('sname','') and meta['parents'][ident][1].get('flag',0)==raw.get('flag',0)]
 if not cohort:reasons.append('EMPTY_COHORT')
 typ=int(s['rule'].split('|')[1]); slot=s['parentSlot']; field=s['field'][1:]; carriers=[]; target_records=[]; attachment_ids=[]
 for ident,(pi,parent) in cohort:
  chain=[]
  for key,value in parent.items():
   if re.fullmatch(r'skillid\d+',key) and value!=0:
    got=meta['boss'].get(value)
    chain.append({'slot':key,'recordId':value,'type':got[1].get('skillid0') if got else None,'recordPointer':f"{meta['prefix']}/bossskill/{got[0]}" if got else None})
    if got is None:reasons.append('MISSING_CHILD_IN_DENOMINATOR')
    elif got[1].get('skillid0') not in (typ,13):reasons.append('OTHER_EXECUTOR_REQUIRES_ASSOCIATION_REVIEW')
  matches=[e for e in chain if e['type']==typ]
  if len(matches)!=1 or matches[0]['slot']!=slot:reasons.append('NON_UNIQUE_TARGET_CARRIER')
  target=meta['boss'].get(parent.get(slot))
  if not target:continue
  bi,record=target;target_records.append(record);attachment_ids.append(record.get('s_ability',0))
  if record.get('skillid0')!=typ or record.get(field)!=s['raw']:reasons.append('TARGET_AMOUNT_DIFFERS')
  carriers.append({'parentId':ident,'parentSource':{'file':meta['file'],'pointer':f"{meta['prefix']}/bosspattern/{pi}"},'referenceFields':[k for k,v in charrefs.items() if v==ident],'slot':slot,'recordId':record['skillid'],'recordSource':{'file':meta['file'],'pointer':f"{meta['prefix']}/bossskill/{bi}"},'rule':s['rule'],'field':s['field'],'raw':record.get(field),'rawRecord':record,'executors':chain})
 # Identity and animation cue may differ; numeric/geometry/flags/attachments may not.
 ignored={'skillid','name','sname','spmotname'}
 if target_records:
  baseline={k:v for k,v in target_records[0].items() if k not in ignored}
  if any({k:v for k,v in r.items() if k not in ignored}!=baseline for r in target_records[1:]):reasons.append('FULL_TARGET_RECORD_DIFFERS_EXCEPT_ID_OR_ANIMATION')
 if len(set(attachment_ids))>1:reasons.append('ATTACHED_ABILITY_DIFFERS')
 attachments=[]
 for aid in dict.fromkeys(attachment_ids):
  if not aid:continue
  got=meta['abilities'].get(aid)
  if not got:reasons.append('ATTACHED_ABILITY_NOT_RESOLVED');continue
  ai,ability=got;attachments.append({'recordId':aid,'type':ability.get('ability'),'rawRecord':ability,'source':{'file':meta['skillFile'],'pointer':f'/skilllist/{ai}'}})
  # 2003 is an existing confirmed PowerDrain consumer. Other SA families are
  # kept for further review rather than assuming unchanged raw means no extra scaling.
  if ability.get('ability')!=2003:reasons.append('ATTACHED_ABILITY_ADDITIONAL_SCALING_OR_UNKNOWN_CONSUMER')
 if field!='skillparam1' or typ not in (3,55,110,112):reasons.append('OUTSIDE_REVIEWED_DAMAGE_INPUT_RULES')
 accepted=not reasons
 results.append({'cid':cid,'rowId':old['rowId'],'text':old['text'],'source':s,'bindingKnown':old['after']['bindingKnown'],'numericKnown':old['after']['numericKnown'],'branchInvariant':accepted,'conditionKnown':False,'scope':'仅已解出的局部单次伤害输入系数，不是命中次数、总伤害或最终扣血；不解除分支触发条件疑问','reasonCodes':sorted(set(reasons)),'mainlineCard':{'file':cardrel,'sha256':hashes[cardrel]},'characterSource':{'file':cf,'pointer':cp,'allPatternReferences':charrefs},'cohortCriterion':{'sameLayer':layer,'sameName':raw.get('sname',''),'sameFlag':raw.get('flag',0)},'allCohortParents':[p for p,_ in cohort],'carriers':carriers,'attachments':attachments})
receipt={'schema':1,'inputs':hashes,'stats':{'reviewed':len(results),'accepted':sum(x['branchInvariant'] for x in results)},'items':results}
for rel,h in hashes.items():assert hashlib.sha256(read_path(ROOT/rel, root=ROOT).read_bytes()).hexdigest()==h,rel
write_new_text(REPORT, json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'stats':receipt['stats'],'acceptedByCard':dict(__import__('collections').Counter(x['cid'] for x in results if x['branchInvariant']))},ensure_ascii=False))
