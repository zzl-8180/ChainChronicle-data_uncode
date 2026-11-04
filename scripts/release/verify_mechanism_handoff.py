"""Read-only, standard-library verifier. Copied into the bundle as verify_bundle.py."""
import hashlib
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path


def main():
    base=Path(__file__).resolve().parent
    def read(rel): return json.loads((base/rel).read_text(encoding='utf-8-sig'))
    def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
    def ptr(obj,path):
        for key in path.strip('/').split('/'):
            key=key.replace('~1','/').replace('~0','~')
            obj=obj[int(key)] if isinstance(obj,list) else obj[key]
        return obj
    def identity(item):
        a=item['answer']; s=a['source']
        return '|'.join(map(str,[a['effect_id'],s['layer'],s['table'],s['record_id'],a['field_path']]))

    manifest=read('manifest.json')
    # Nested historical manifests are regular payload members, only the root is excluded.
    actual={p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file() and p!=base/'manifest.json'}
    assert actual==set(manifest['files']),'Payload inventory mismatch'
    for rel,info in manifest['files'].items():
        path=(base/rel).resolve()
        assert path.is_relative_to(base) and path.is_file(),rel
        assert path.stat().st_size==info['bytes'] and sha(path)==info['sha256'],rel
    experiment='evidence/experiment/'
    packet=experiment+'input/'
    frozen=read(packet+'manifest.json')
    for rel,info in frozen['files'].items():
        assert sha(base/packet/rel)==info['sha256'],rel
    arms=read(experiment+'arm_freeze_manifest.json')
    for files in arms['arms'].values():
        for rel,h in files.items(): assert sha(base/experiment/rel)==h,rel
    original=read(experiment+'accepted_candidates.json')
    strict=read('data/accepted49.json')['items']; pending=read('data/pending4.json')['items']
    assert strict==original['strict_inferred_answers']
    assert pending==original['pending_page_supported_candidates']
    assert len(strict)==49 and len(pending)==4
    assert len({identity(x) for x in strict})==49
    assert len({x['cid'] for x in strict})==23 and {x['cid'] for x in pending}=={20607}
    verdict=read(experiment+'review/verdict.json')
    assert {identity(x) for x in strict}==set(verdict['deduplicated_outcome']['accepted_keys'])
    targets={x['task_id']:x for x in read(packet+'targets.json')}
    skills_doc=read(packet+'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')
    skills={r['skillid']:r for r in skills_doc['skilllist']}
    chars={r['cid']:r for r in read(packet+'output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw')['charainfo']}
    rules=read(packet+'output/character_skills/profiles/rules.json')
    trace={r['raw']['skillid']:r['raw'] for r in read(packet+'output/ordinary_effects/ability1095/trace.json')['source_records']}
    fieldmap={'攻撃力':'/param1','防御力':'/param3','移動速度':'/param2','クリティカル発生率':'/param5','クリティカル威力':'/param6'}
    baseline={e['effect_id']:e for t in targets.values() for e in t['baseline_effects']}
    for group in [strict,pending]:
        for item in group:
            a=item['answer']; s=a['source']; t=targets[item['task_id']]
            raw_record=ptr(skills_doc,s['json_pointer'])
            if not isinstance(raw_record,dict): raw_record=ptr(skills_doc,s['json_pointer'].rsplit('/',1)[0])
            field=a['field_path'][1:]
            assert s['layer']=='CACHE' and s['table']=='skilllist'
            assert raw_record['skillid']==s['record_id'] and raw_record['ability']==1095
            assert raw_record[field]==a['raw_value'] and trace[s['record_id']]==raw_record
            assert rules[a['rule_key']]['field_path']==a['field_path']
            assert baseline[a['effect_id']]['status']=='unresolved'
            assert fieldmap[baseline[a['effect_id']]['effect_type']]==a['field_path']
            parent=skills[t['source_skill']['record_id']]
            assert raw_record['skillid'] in parent['sub'] and t['japanese'] in parent['text']
            assert sum(skills[sid].get('ability')==1095 for sid in parent['sub'])==1
            if group is strict:
                assert chars[item['cid']]['skillid'][1]==parent['skillid']
                assert a['review_grade']=='ACCEPT_INFERRED'
                assert a['review_tier']=='FULL_RAW_SOURCE_CHAIN_SCOPED_INFERENCE'
                raw=Decimal(str(a['raw_value']))
                expected={'param1':(raw-1)*100,'param2':(raw-1)*100,'param3':(1-raw)*100,'param5':raw*100,'param6':raw-Decimal('1.5')}[field]
                assert Decimal(str(a['review_normalized']['value']))==expected
                scope=a['review_normalized']['scope']
                assert scope['binding']=='inferred' and scope['runtime_verified'] is False
                assert scope['installed'] is True
            else:
                assert item['cid'] not in chars
                assert a['review_grade']=='UNRESOLVED'
    states=read('data/effect_disposition61.json')['items']
    assert len(states)==61 and {x['effect_id'] for x in states}==set(baseline)
    counts=Counter(x['handoff_status'] for x in states)
    assert counts=={'ACCEPTED_INFERRED_FULL_CHAIN':49,'PENDING_RAW_UPSTREAM':4,'UNKNOWN':8}
    assert manifest['counts']['confirmed_description_answers']==0 and manifest['counts']['production_promotions']==0
    assert manifest['counts']['yg_inferred_answers']==sum(targets[x['task_id']]['baseline_description']['yg'] for x in strict)==23
    print(json.dumps({'passed':True,'files_checked':len(manifest['files']),'input_files_checked':len(frozen['files']),
          'arm_files_checked':sum(map(len,arms['arms'].values())),'strict_inferred':49,'pending':4,
          'remaining_without_supported_numbers':8,'baseline_effects':61,'confirmed':0,'production_promotions':0,
          'scope':'Integrity, frozen baseline, source chains and arithmetic; reuses documented semantic review. No current production adoption or new native verification.',
          'bundle_root':str(base),'python_version':sys.version.split()[0]},ensure_ascii=True))


if __name__=='__main__': main()
