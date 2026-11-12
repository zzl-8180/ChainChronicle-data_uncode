"""Independent source reconciliation and adversarial regression for reader candidates."""
import copy
import json
from hashlib import sha256
from pathlib import Path

from branch_candidates import ROOT, reader, read, parent, graph_pairs, compatible, semantic_damage_targets
from versioned_outputs import fresh_output

OUT=ROOT/'output/character_skills/reader_full_20261106'
A=OUT/'audit/branch_candidates_20261107'
overlay=json.loads((OUT/'data/branch_candidates.js').read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
inventory=read(A/'inventory.json')
masters={}


def resolve(source):
    key=source['source_key']
    if key not in masters:
        file=(ROOT/'output/cache_full_20261015_v3/decoded'/key.split('/',1)[1]) if key.startswith('CACHE/') else ROOT/'output/base_master'/key.split('/',1)[1]
        masters[key]=read(file)
    value=masters[key]
    for part in source['json_pointer'].lstrip('/').split('/'):
        part=part.replace('~1','/').replace('~0','~')
        value=value[int(part)] if isinstance(value,list) else value[part]
    return value


frozen=read(OUT/'audit/presentation_release_20261107/input_snapshot.json')
for path,digest in frozen['dataHashes'].items():
    assert sha256((OUT/path).read_bytes()).hexdigest()==digest,path
checks=0
for cid,entry in overlay['cards'].items():
    formal=read(ROOT/f'output/character_skills/pages/{cid}/card.json')
    assert sha256((ROOT/f'output/character_skills/pages/{cid}/card.json').read_bytes()).hexdigest()==inventory['sourceHashes'][cid]
    skills={s['record_id']:s for g in formal['groups'] if g['group']=='special_move' for s in g['skills'] if parent(s)}
    for rid,patch in entry['rows'].items():
        for addition in patch.get('additions',[]):
            ans=addition['answer'];s=ans['source'];skill=skills[s['branchId']]
            rec=next(r for r in skill['record_evidence'] if r['record_id']==s['recordId'] and r['layer']==s['layer'] and r['table']==s['rule'].split('|')[0])
            actual=resolve(rec['source'])
            field=s['field'].lstrip('/')
            assert field in actual and actual[field]==s['raw'],(cid,rid,s)
            assert s['recordRaw']==actual,(cid,s['recordId'])
            p=resolve(parent(skill)['source']);slot=s['parentSlot'].split('/')[0]
            if '/' in s['parentSlot']:
                boss=next(r for r in skill['record_evidence'] if r['table']=='bossskill' and r['record_id']==p[slot])
                assert resolve(boss['source'])['s_ability']==s['recordId']
            else:assert p[slot]==s['recordId']
            assert ans['branchCandidate'] and ans['confidence']=='inferred'
            assert '待确认' in ans['condition']
            checks+=1

assert checks==overlay['summary']['additions']
assert len(inventory['branches'])==1012
assert len(inventory['sameConditionRows'])==1336
assert all(b['state']!='无可核对父记录，不绑定' for r in inventory['sameConditionRows'] for b in r['branches'])

def additions(cid):
    return [a['answer'] for p in overlay['cards'].get(str(cid),{}).get('rows',{}).values() for a in p.get('additions',[])]

for rule,raw in [('skilllist|2003|/param7',-.325),('skilllist|2003|/param8',-.325),
                 ('skilllist|2003|/param9',.325),('bossskill|13|/skillparam1',.65),
                 ('skilllist|2012|/param4',.325),('skilllist|2012|/param5',.325)]:
    assert any(a['source']['rule']==rule and a['source']['raw']==raw for a in additions(1303)),rule
assert all(a['source']['layer']=='APK' for a in additions(1214))
assert all(a['source']['rule']!='bossskill|64|/skillparam1' for a in additions(10214))
assert all(a['source']['rule']!='bossskill|51|/skillparam0' for a in additions(7576))
assert all(not(a['source']['branchId']==41021501 and a['source']['parentSlot']=='skillid2/s_ability') for a in additions(10215))
assert all(not(a['source']['branchId'] in (42062201,42062202,42062203,42062204) and a['source']['rule'].startswith('skilllist|2003|')) for a in additions(20622))

# Raw missing/null/zero must not silently acquire equivalence in compatibility.
b={'table':'bossskill','raw_record':{'skillid0':13,'iParam0':None}}
o=copy.deepcopy(b);del o['raw_record']['iParam0'];assert 'iParam0' in compatible(b,o)
o['raw_record']['iParam0']=0;assert 'iParam0' in compatible(b,o)

report={'pass':True,'primarySourceValuesVerified':checks,'frozenDataFilesUnchanged':len(frozen['dataHashes']),
    'allNoRowPatternsAccounted':1012,'sameConditionRowsAccounted':1336,
    'regressions':['1303 enemy/buff/crit candidate values','1214 APK and reverse order','10214 unknown heal consumer remains unbound',
                   '7576 field damage cannot become frontal hit','10215/20622 parent restrictions propagate','missing/null/zero distinct'],
    'limits':'Static numeric inputs and provisional sentence correspondence; no runtime selector or final battle outcome claim.'}
report_dir=fresh_output('projects/reader/reports/review','branch-source')
(report_dir/'validation_source.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
