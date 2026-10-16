"""Compare master source coverage without assuming runtime overwrite priority."""
import json
import hashlib
import zipfile
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    tables = [('cards','_mdCharacter','charainfo','cid','charainfo'),
              ('skills','_mdSkill','skilllist','skillid','skilllist')]
    summaries = {}
    for label,field,table,key,cache in tables:
        base = read(f'output/base_master/{field}.json')[table]
        phone = read(f'output/decoded/{cache}.data5.json')[table]
        base_ids,phone_ids = {r[key] for r in base},{r[key] for r in phone}
        summaries[label] = {'APK_base_records':len(base),'phone_snapshot_records':len(phone),
                            'overlapping_ids':len(base_ids & phone_ids),'union_ids_for_coverage_only':len(base_ids | phone_ids),
                            'APK_only_ids':len(base_ids-phone_ids),'phone_only_ids':len(phone_ids-base_ids)}
    report = read('output/base_master/report.json')
    with zipfile.ZipFile('チェンクロ.apk') as apk:
        original = apk.read('assets/chronicle.dat')
    assert original==Path(report['source']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==report['source_sha256']
    current = Path('work/protection/chronicle_decoded.unityfs').read_bytes()
    assert hashlib.sha256(current).hexdigest()==report['converted_sha256']
    initial = Path('work/protection/chronicle_initialize_candidate.bin')
    repeat = 'NOT_RUN: independent initial probe not present'
    if initial.exists():
        assert initial.read_bytes()==current
        repeat = 'PASS: independent initial probe and reusable decoder identical'
    sample = read('output/sample/sample.json')
    base_skill_rows = read('output/base_master/_mdSkill.json')['skilllist']
    enums = read('output/il2cpp/sample_code.json')['enums']['ABILITY_TYPE']
    children = []
    for row in [sample['skill_raw']]+sample['subskills_raw']:
        names = [name for name,value in enums.items() if value['value']==row['ability']]
        if len(names)!=1:
            raise ValueError('Sample effect enum not uniquely resolved')
        children.append({'skill_id':row['skillid'],'ability_raw':row['ability'],'metadata_enum_name':names[0],
                         'meaning_scope':'Enum mapping confirmed; parameter semantics require corresponding handler'})
    collision = next(r for r in base_skill_rows if r['skillid']==116)
    result = {'status':'SOURCE_COVERAGE_PASS','original_APK_asset_equals_unchanged_work_input':True,
              'independent_repeat_transform':repeat,'chronicle_conversion_sha256':report['converted_sha256'],
              'tables':summaries,'sample_effect_enum_links':children,
              'identifier_role_example':{'card_active_type116':'SKILL_TYPE.INTERVAL_FALL2',
                                         'APK_skilllist_id116':{'name':collision['name'],'ability':collision['ability']},
                                         'rule':'Different fields/roles; do not join active-type116 to passive skilllist id116'},
              'limits':['Coverage unions only; sources are not merged and overwrite priority is unknown',
                        'Record counts include base master categories/NPCs; not a playable-card count',
                        'Same identifier across sources does not establish equal fields or current live applicability']}
    Path('output/base_master/source_comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
