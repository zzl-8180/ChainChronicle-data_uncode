"""Verify phase E lossless roundtrip, accounting and bounded structural regressions."""
import argparse
import contextlib
import csv
import io
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from export_master import (SCENARIOS, annotate, build_index, compact, expand_roots,
                           lookup, parse_records, sha, strict_load, typed_value, write_json)
from phase_d_source_rule import PriorityGuest
import export_master


def read_lines(path):
    with path.open(encoding='utf-8') as stream:
        return [strict_load(line) for line in stream]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory',type=Path)
    args = parser.parse_args()
    directory = args.directory or Path(strict_load(Path('output/export/latest.json').read_bytes())['directory'])
    manifest = strict_load((directory/'manifest.json').read_bytes())
    checks = []
    for relative,digest in manifest['output_sha256'].items():
        assert sha((directory/relative).read_bytes())==digest,relative
    checks.append('All exported payload files match manifest SHA-256')
    records = [r for file in manifest['record_files'] for r in read_lines(directory/file)]
    references = read_lines(directory/'references.jsonl')
    expansions = read_lines(directory/'one_level_expansions.jsonl')
    anomalies = read_lines(directory/'anomalies.jsonl')
    conflicts = read_lines(directory/'source_conflicts.jsonl')
    by_key = {r['record_key']:r for r in records}
    assert len(by_key)==len(records)==manifest['record_count']
    grouped = defaultdict(list)
    for r in records:
        grouped[r['source_key']].append(r)
        assert r['snapshot_id']==manifest['snapshot_id'] and r['parser_version']==manifest['parser_version']
    for file in manifest['record_files']:
        assert len({r['source_key'] for r in read_lines(directory/file)})<=1,'JSONL sources must remain separate'
    for source in manifest['sources']:
        copied = (directory/source['copied_file']).read_bytes()
        assert sha(copied)==source['sha256']
        # Current source compared too: confirms export did not alter decoder results.
        assert Path(source['input_file']).read_bytes()==copied
        if 'main_table' not in source or source['status']!='PARSED_AND_PRESERVED':
            continue
        original = strict_load(copied)
        actual = grouped[source['source_key']]
        assert len(actual)==len(original[source['main_table']])==source['record_count']
        for ordinal,r in enumerate(actual):
            loc = r['location']
            assert loc['ordinal_zero_based']==ordinal
            assert loc['json_pointer']==f"/{source['main_table']}/{ordinal}"
            slice_bytes = copied[loc['byte_begin']:loc['byte_end_exclusive']]
            assert sha(slice_bytes)==loc['raw_record_sha256']
            assert typed_value(strict_load(slice_bytes))==typed_value(r['raw'])==typed_value(original[source['main_table']][ordinal])
        # Restore whole document including non-core arrays/wrapper fields.
        rebuilt = dict(source['other_top_level_fields'])
        rebuilt[source['main_table']] = [r['raw'] for r in actual]
        assert typed_value(rebuilt)==typed_value(original)
    checks.append('Every core record and complete JSON document roundtrips: types, nested arrays, absent/null/zero and UTF8 byte spans')
    counts = {layer:{table:sum(r['layer']==layer and r['table']==table for r in records) for table in ('charainfo','skilllist')} for layer in ('APK','CACHE')}
    assert counts==manifest['record_counts']=={'APK':{'charainfo':7800,'skilllist':21008},'CACHE':{'charainfo':1482,'skilllist':8559}}
    expected_refs = []
    for r in records:
        if not isinstance(r['raw'],dict):
            continue
        field = 'sub' if r['table']=='skilllist' else 'skillid'
        values = r['raw'].get(field, [])
        if isinstance(values,list):
            expected_refs.extend((r['record_key'],field,i,typed_value(sid)) for i,sid in enumerate(values))
    actual_refs = [(r['parent_record_key'],r['field'],r['ordinal'],typed_value(r['id_raw'])) for r in references]
    assert actual_refs==expected_refs
    assert len({r['reference_key'] for r in references})==len(references)==manifest['reference_count']
    assert len(anomalies)==manifest['anomaly_count']
    reference_counts = {layer:{field:sum(r['parent_layer']==layer and r['field']==field for r in references) for field in ('skillid','sub')} for layer in ('APK','CACHE')}
    assert reference_counts==manifest['reference_counts']=={'APK':{'skillid':54692,'sub':7863},'CACHE':{'skillid':10232,'sub':3203}}
    indexes = {layer:build_index([r for r in records if r['layer']==layer and r['table']=='skilllist'],'skillid') for layer in ('APK','CACHE')}
    for r in references:
        for scenario in SCENARIOS:
            found = r['resolution'][scenario]
            if found['status'] in ('RESOLVED','MISSING_ID','AMBIGUOUS_ID','INVALID_REFERENCE_ID'):
                assert found==lookup(r['id_raw'],scenario,indexes)
            for candidate in found['candidates']:
                assert candidate in by_key
    for scenario in SCENARIOS:
        counted = dict(Counter(r['resolution'][scenario]['status'] for r in references))
        assert counted==manifest['resolution_counts'][scenario]
        assert sum(counted.values())==len(references)
    for layer in ('APK','CACHE'):
        for scenario in SCENARIOS:
            assert dict(Counter(r['resolution'][scenario]['status'] for r in references if r['parent_layer']==layer and r['field']=='sub'))==manifest['sub_resolution_counts'][layer][scenario]
    cache_sub = [r for r in references if r['parent_layer']=='CACHE' and r['field']=='sub']
    fallback = [r for r in cache_sub if r['resolution'][SCENARIOS[1]].get('layer')=='APK']
    assert len(fallback)==104
    assert all(r['resolution'][SCENARIOS[1]]['status']=='RESOLVED' for r in cache_sub)
    checks.append('Record/reference accounting reconciles, including all3203 cache sub edges and104 APK fallbacks')
    slot_counts = {layer:dict(Counter(str(len(r['raw']['skillid'])) for r in records if r['layer']==layer and r['table']=='charainfo' and isinstance(r['raw'].get('skillid'),list))) for layer in ('APK','CACHE')}
    assert slot_counts==manifest['slot_array_lengths']=={'APK':{'4':1927,'8':5873},'CACHE':{'4':406,'8':1076}}
    assert all(r['resolution'][s]['status']=='SLOT_ROLE_UNKNOWN' for r in references if r['field']=='skillid' and len(by_key[r['parent_record_key']]['raw']['skillid'])==8 for s in SCENARIOS)
    checks.append('Four-slot and eight-slot arrays preserved in full; eight-slot role not invented')
    card = next(r for r in records if r['layer']=='CACHE' and r['table']=='charainfo' and r['id_raw']==2327)
    assert card['raw']['skillid']==[116,40232700,40232705,0]
    root = indexes['CACHE'][40232705][0]
    child = indexes['CACHE'][40232706][0]
    assert root['raw']['sub']==[40232706,40232707,40232708,40232709]
    assert 'param4' not in root['raw'] and 'param4' not in child['raw'] and 'skillparam9' not in card['raw']
    selected = lookup(36000358,SCENARIOS[1],indexes)
    assert by_key[selected['candidates'][0]]['raw']['param1']==400
    assert by_key[lookup(36000358,SCENARIOS[0],indexes)['candidates'][0]]['raw']['param1']==300.0
    conflict = next(r for r in conflicts if r['table']=='skilllist' and r['id_raw']==36000358)
    assert not conflict['merge_performed']
    parameter = next(d for d in conflict['differences'] if d['field']=='param1')
    assert parameter['APK']['raw']==300.0 and parameter['CACHE']['raw']==400
    for table,expected in [('charainfo',119),('skilllist',568)]:
        assert sum(r['table']==table for r in conflicts)==expected
    checks.append('cid2327 namespace/source/absent fields and skill36000358 300-vs400 remain separate')
    # Compare all emitted expansions against the original raw lists, not recursion.
    assert len(expansions)==manifest['one_level_expansion_count']==2*sum(r['table']=='skilllist' for r in records)
    for e in expansions:
        assert e['requested_from'] in by_key
        expected = expand_roots([e['root_id_raw']],e['scenario'],indexes,by_key)
        assert all(e[k]==v for k,v in expected.items())
        assert all(i['depth'] in (0,1) for i in e['installed'])
    cases = [([42011300],SCENARIOS[1]),([602],SCENARIOS[0]),([36000376],SCENARIOS[0]),([40034712,40034714],SCENARIOS[1])]
    regressions = []
    for ids,scenario in cases:
        expansion = expand_roots(ids,scenario,indexes,by_key)
        actual = [x['id_raw'] for x in expansion['installed']]
        if ids==[602]: assert actual==[602,607]
        if ids==[36000376]: assert actual==[36000376,36000376]
        if ids==[40034712,40034714]: assert actual==[40034712,40034713,40034714,40034713]
        regressions.append({'roots':ids,'scenario':scenario,'installed':expansion['installed'],'status':'PASS'})
    checks.append('Cycle/self-loop remain graph edges; shared children retain repeated installation and original order')
    # Reuse the existing native model, adding only a non-query fallback for flag setup.
    class FlagRows(dict):
        def __missing__(self,key):
            return apk_rows[key]
    apk_rows = {sid:rows[0]['raw'] for sid,rows in indexes['APK'].items() if len(rows)==1}
    cache_rows = {sid:rows[0]['raw'] for sid,rows in indexes['CACHE'].items() if len(rows)==1}
    native = Path('work/protection/il2cpp_loader_seed1.bin').read_bytes()
    sample = strict_load((directory/'provenance/output/sample/sample.json').read_bytes())
    assert sha(native)==sample['native_code_provenance']['native_image_sha256']
    for regression in regressions:
        rows = cache_rows if regression['scenario']==SCENARIOS[1] else {}
        guest = PriorityGuest(native,FlagRows(rows),apk_rows)
        installed = guest.install(regression['roots'])
        assert installed==[r['id_raw'] for r in regression['installed']],(regression,installed)
        regression['existing_native_install_model'] = 'PASS'
        regression['lookup_log'] = guest.lookups
    checks.append('Four structural cases match recovered native install/addSubAbility using existing declared models; not game runtime')
    shapes = Counter()
    for r in records:
        if r['table']=='skilllist' and r['layer']=='CACHE' and r['raw'].get('ability')==1105:
            shape = tuple(k for k in [f'param{i}' for i in range(6)] if k in r['raw'])
            shapes[shape]+=1
            for key,item in r['interpretation']['parameters'].items():
                assert typed_value(item['raw'])==typed_value(r['raw'][key])
                if key=='param4': assert item['status']=='UNKNOWN'
            assert r['interpretation']['final_battle_multiplier'] is None
    assert shapes==Counter({('param0','param1','param2','param3'):27,('param0','param1','param2','param3','param5'):4,('param0','param1','param2','param3','param4','param5'):3})
    checks.append('All34 cache HighHPAll records cover three field-presence profiles; no defaults/evaluator introduced')
    # Adverse fixtures check real export hazards, without changing actual source files.
    synthetic = b'{"skilllist":[{"skillid":1,"ability":1105,"param1":null,"param2":0,"param3":1.0,"sub":[1,1]}],"extra":{"future":[null,0,{"x":"y"}]}}'
    doc,spans = parse_records(synthetic,'skilllist')
    r=spans[0][0]
    assert 'param0' not in r and r['param1'] is None and type(r['param2']) is int and type(r['param3']) is float
    assert typed_value(strict_load(synthetic))==typed_value(doc)
    assert annotate(r,True)['parameters']['param1']['value_usable'] is False
    for bad in (synthetic[:-1], b'{"skilllist":[{"skillid":1,"skillid":2}]}',b'{"skilllist":[],}',b'{"skilllist":[NaN]}'):
        try:
            parse_records(bad,'skilllist')
        except (ValueError,IndexError):
            pass
        else:
            raise AssertionError('Invalid/truncated/duplicate-key JSON accepted')
    a={'record_key':'a','raw':{'skillid':1,'ability':1105}}
    b={'record_key':'b','raw':{'skillid':1,'ability':1105,'param1':400}}
    base={'record_key':'base','raw':{'skillid':1,'ability':1105,'param0':0.5,'param1':300}}
    dupe={'CACHE':build_index([a,b],'skillid'),'APK':build_index([base],'skillid')}
    assert lookup(1,SCENARIOS[1],dupe)['status']=='AMBIGUOUS_ID' and len(dupe['CACHE'][1])==2
    unique={'CACHE':build_index([a],'skillid'),'APK':dupe['APK']}
    picked=lookup(1,SCENARIOS[1],unique)
    assert picked['candidates']==['a'] and 'param0' not in a['raw'] and 'param1' not in a['raw']
    assert lookup(2,SCENARIOS[1],unique)['status']=='MISSING_ID'
    assert lookup(1,SCENARIOS[1],unique,unavailable=['CACHE'])['status']=='LAYER_UNAVAILABLE'
    checks.append('Negative fixtures reject corrupt JSON; duplicate IDs/missing references/layer errors remain explicit; missing fields never merge')
    # Fault-injected export in a disposable workspace subdirectory: never alter inputs.
    work = Path('work').resolve()
    read_source = export_master.read_source
    original_argv = sys.argv[:]
    def faulty_read(path):
        name = Path(path).name
        if name=='charainfo.data5.json.raw':
            return {'raw':b'{'}
        if name=='_mdSkill.json':
            return {'raw':None,'read_error':'INJECTED_TEST_SOURCE_UNAVAILABLE'}
        return read_source(path)
    try:
        with tempfile.TemporaryDirectory(prefix='phase_e_fault_',dir=work) as temporary:
            target=Path(temporary).resolve()
            assert target.is_relative_to(work) and target!=work
            export_master.read_source=faulty_read
            sys.argv=['export_master.py','--output-root',str(target)]
            with contextlib.redirect_stdout(io.StringIO()):
                export_master.main()
            faulty_dir=Path(strict_load((target/'latest.json').read_bytes())['directory'])
            bad_manifest=strict_load((faulty_dir/'manifest.json').read_bytes())
            bad_errors=read_lines(faulty_dir/'anomalies.jsonl')
            assert len(bad_errors)==2 and bad_manifest['status']=='EXPORTED_WITH_PRESERVED_ANOMALIES'
            assert bad_manifest['record_counts']=={'APK':{'charainfo':7800,'skilllist':0},'CACHE':{'charainfo':0,'skilllist':8559}}
            broken=next(s for s in bad_manifest['sources'] if s['source_key']=='CACHE/charainfo.data5.json.raw')
            assert (faulty_dir/broken['copied_file']).read_bytes()==b'{'
            missing=next(s for s in bad_manifest['sources'] if s['source_key']=='APK/_mdSkill.json')
            assert missing['copied_file'] is None and 'INJECTED_TEST' in missing['error']
            assert bad_manifest['resolution_counts'][SCENARIOS[1]]['LAYER_UNAVAILABLE']>0
    finally:
        export_master.read_source=read_source
        sys.argv=original_argv
    checks.append('Fault-injected full export retains corrupt bytes/unavailable-source errors and still exports both unaffected tables')
    with (directory/'records_view.csv').open(encoding='utf-8-sig',newline='') as stream:
        view=list(csv.DictReader(stream))
    assert len(view)==len(records)
    assert [r['record_key'] for r in view]==[r['record_key'] for r in records]
    root_view=next(r for r in view if r['record_key']==root['record_key'])
    assert strict_load(root_view['param0_to5_presence_json'])['param4']=='MISSING'
    assert strict_load(root_view['parameters_json'])['param1']==1.15
    checks.append('CSV filter view row count, source keys and missing parameter state trace to JSONL')
    for path,digest in manifest['evidence_sha256'].items():
        assert sha((directory/'provenance'/path).read_bytes())==digest
    for path,digest in manifest['support_script_sha256'].items():
        assert sha((directory/'provenance'/path).read_bytes())==sha(Path(path).read_bytes())==digest
    assert sha(Path(__file__).read_bytes())==manifest['verifier_sha256']
    review='output/审查报告/阶段D独立审查报告_2026-10-15.md'
    assert sha(Path(review).read_bytes())==manifest['evidence_sha256'][review]
    checks.append('Evidence/parser copies pinned; independent D review remains byte-identical')
    report={'status':'PASS','snapshot_id':manifest['snapshot_id'],'build_id':manifest['build_id'],
            'manifest_sha256':sha((directory/'manifest.json').read_bytes()),
            'verifier_version':'phase-e-verify-1.0','verifier_sha256':sha(Path(__file__).read_bytes()),
            'checks':checks,'structural_native_regressions':regressions,'record_counts':counts,
            'reference_counts':reference_counts,'cache_sub_APK_fallbacks':len(fallback),
            'HighHPAll_presence_profiles':[{'fields':list(k),'count':v} for k,v in sorted(shapes.items())],
            'prior_D_evidence':'Reused pinned32 HP checks,11+1 chain cases,4 source branch checks; not rerun or represented as new device evidence',
            'limits':['No current player unlock/loaded-version/final-battle evaluation','Eight-slot meanings and other effect parameters remain unknown']}
    output=directory/'validation.json'
    if output.exists():
        assert strict_load(output.read_bytes())==report,'Existing validation differs; retained without overwrite'
    else:
        write_json(output,report)
    print(compact({'status':'PASS','output':str(output),'checks':len(checks),'records':len(records),'references':len(references),'native_cases':len(regressions)}))


if __name__=='__main__':
    main()
