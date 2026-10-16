"""Phase E: lossless source snapshots, conditional daSkill links, no live evaluation.

Uses existing decoded files only. JSON is authoritative; CSV is a derived index.
No decryption, device access, recursive execution, field merging or ID deduplication.
"""
import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

PARSER_VERSION = 'phase-e-1.0'
RULE_VERSION = 'highhp1105-local-fields-1.0;daskill-id-fallback-1.0;one-level-sub-1.0'
SCENARIOS = ('APK_ONLY', 'JSON_SNAPSHOT_WITH_APK_FALLBACK')
MEANINGS = {
    'param0': ('recipient_hp_ratio_lower_bound_inclusive', 'compare'),
    'param1': ('local_attack_contribution', 'multiply'),
    'param2': ('local_movement_contribution', 'multiply'),
    'param3': ('local_defence_contribution', 'multiply'),
    'param5': ('local_critical_damage_contribution', 'add'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def typed_value(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON object key: {key!r}')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f'Non-JSON numeric constant: {value}')


def strict_load(raw):
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def read_source(path):
    try:
        return {'raw':Path(path).read_bytes()}
    except OSError as error:
        return {'raw':None,'read_error':str(error)}


def pointer_part(value):
    return str(value).replace('~', '~0').replace('/', '~1')


def parse_records(raw, table):
    """Single forward scan; exact UTF8 record spans without quadratic prefix encoding."""
    text = raw.decode('utf-8')
    decoder = json.JSONDecoder(object_pairs_hook=unique_object, parse_constant=invalid_constant)

    def ws(pos):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        return pos

    doc, records = {}, []
    pos = ws(0)
    if pos >= len(text) or text[pos] != '{':
        raise ValueError('Expected top-level JSON object')
    pos = ws(pos+1)
    char_cursor = byte_cursor = 0
    while pos < len(text) and text[pos] != '}':
        key, pos = decoder.raw_decode(text, pos)
        if not isinstance(key, str) or key in doc:
            raise ValueError('Invalid or duplicate top-level key')
        pos = ws(pos)
        if text[pos:pos+1] != ':':
            raise ValueError('Missing object colon')
        pos = ws(pos+1)
        if key != table:
            value, pos = decoder.raw_decode(text, pos)
            doc[key] = value
        else:
            if text[pos:pos+1] != '[':
                raise ValueError(f'{table} is not an array')
            pos = ws(pos+1)
            values = []
            while text[pos:pos+1] != ']':
                begin = pos
                value, pos = decoder.raw_decode(text, pos)
                byte_cursor += len(text[char_cursor:begin].encode('utf-8'))
                byte_begin = byte_cursor
                byte_cursor += len(text[begin:pos].encode('utf-8'))
                char_cursor = pos
                location = {'json_pointer':f'/{pointer_part(table)}/{len(values)}',
                            'ordinal_zero_based':len(values), 'byte_begin':byte_begin,
                            'byte_end_exclusive':byte_cursor,
                            'raw_record_sha256':sha(raw[byte_begin:byte_cursor])}
                values.append(value)
                records.append((value, location))
                pos = ws(pos)
                if text[pos:pos+1] == ']':
                    break
                if text[pos:pos+1] != ',':
                    raise ValueError('Missing array separator or truncated array')
                pos = ws(pos+1)
                if text[pos:pos+1] == ']':
                    raise ValueError('Trailing array comma')
            doc[key] = values
            pos += 1
        pos = ws(pos)
        if text[pos:pos+1] == '}':
            break
        if text[pos:pos+1] != ',':
            raise ValueError('Missing object separator')
        pos = ws(pos+1)
        if text[pos:pos+1] == '}':
            raise ValueError('Trailing object comma')
    if text[pos:pos+1] != '}' or ws(pos+1) != len(text) or table not in doc:
        raise ValueError('Truncated/trailing document or missing table')
    return doc, records


def valid_id(value):
    return type(value) is int


def build_index(records, key):
    index = defaultdict(list)
    for record in records:
        raw = record['raw']
        if isinstance(raw, dict) and valid_id(raw.get(key)):
            index[raw[key]].append(record)
    return dict(index)


def lookup(sid, scenario, indexes, unavailable=()):
    """Presence in an ambiguous primary layer cannot justify APK fallback."""
    if not valid_id(sid):
        return {'status':'INVALID_REFERENCE_ID','candidates':[]}
    layers = ['APK'] if scenario == 'APK_ONLY' else ['CACHE','APK']
    for layer in layers:
        if layer in unavailable:
            return {'status':'LAYER_UNAVAILABLE','layer':layer,'candidates':[]}
        candidates = indexes[layer].get(sid, [])
        if candidates:
            return {'status':'RESOLVED' if len(candidates)==1 else 'AMBIGUOUS_ID',
                    'layer':layer,'candidates':[r['record_key'] for r in candidates]}
    return {'status':'MISSING_ID','candidates':[]}


def expand_roots(root_ids, scenario, indexes, by_key, unavailable=()):
    """Append each selected original root then its immediate sub, retaining duplicates."""
    installed, issues = [], []
    for root_ordinal, sid in enumerate(root_ids):
        if sid == 0 and valid_id(sid):
            continue
        result = lookup(sid, scenario, indexes, unavailable)
        if result['status'] != 'RESOLVED':
            issues.append({'root_ordinal':root_ordinal,'id_raw':sid,**result})
            continue
        root = by_key[result['candidates'][0]]
        ability = root['raw'].get('ability')
        if not valid_id(ability):
            issues.append({'root_ordinal':root_ordinal,'status':'UNKNOWN_ABILITY_VALUE','record_key':root['record_key']})
            continue
        if ability == 0:
            continue
        installed.append({'record_key':root['record_key'],'id_raw':sid,'root_ordinal':root_ordinal,'depth':0})
        sub = root['raw'].get('sub', [])
        if not isinstance(sub, list):
            issues.append({'root_ordinal':root_ordinal,'status':'INVALID_SUB_ARRAY','record_key':root['record_key']})
            continue
        for sub_ordinal, child_id in enumerate(sub):
            found = lookup(child_id, scenario, indexes, unavailable)
            if found['status'] != 'RESOLVED':
                issues.append({'root_ordinal':root_ordinal,'sub_ordinal':sub_ordinal,'id_raw':child_id,**found})
                continue
            child = by_key[found['candidates'][0]]
            child_ability = child['raw'].get('ability')
            if not valid_id(child_ability):
                issues.append({'root_ordinal':root_ordinal,'sub_ordinal':sub_ordinal,'status':'UNKNOWN_ABILITY_VALUE','record_key':child['record_key']})
            elif child_ability != 0:
                installed.append({'record_key':child['record_key'],'id_raw':child_id,
                                  'root_ordinal':root_ordinal,'sub_ordinal':sub_ordinal,'depth':1})
    return {'installed':installed,'issues':issues,'execution_scope':'ORIGINAL_ROOTS_AND_IMMEDIATE_SUB_ONLY; no eligibility/HP/final evaluation'}


def annotate(raw, enabled):
    if not isinstance(raw, dict):
        return {'status':'UNKNOWN_NON_OBJECT','parameters':{}}
    parameters = {}
    for key, value in raw.items():
        if key.startswith(('param','skillparam','iParam')):
            item = {'raw':value,'status':'UNKNOWN'}
            if enabled and raw.get('ability') == 1105 and key in MEANINGS:
                meaning, operation = MEANINGS[key]
                item.update(status='CONFIRMED_STATIC_LOCAL_MEANING', meaning=meaning, operation=operation,
                            value_usable=type(value) in (int,float))
            parameters[key] = item
    return {'status':'LOCAL_FIELDS_ONLY' if any(p['status']!='UNKNOWN' for p in parameters.values()) else 'UNKNOWN',
            'parameters':parameters,'unlisted_field_semantics':'UNKNOWN',
            'runtime_activation':'UNKNOWN','final_battle_multiplier':None}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def write_lines(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        for row in rows:
            stream.write(compact(row)+'\n')


def csv_text(value):
    # Filter view only; explicit apostrophe protects text interpreted as formulas.
    if isinstance(value, str) and value.lstrip().startswith(('=','+','-','@')):
        return "'"+value
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-root', type=Path, default=Path('output/export'))
    args = parser.parse_args()
    baseline = strict_load(Path('output/apk/baseline.json').read_bytes())
    decoded = strict_load(Path('output/decoded/report.json').read_bytes())
    archive = strict_load(Path('output/base_master/report.json').read_bytes())
    collected = strict_load(Path('output/phone/collected_files.json').read_bytes())
    evidence_paths = ['output/sample/sample.json','output/il2cpp/sample_code.json',
                      'output/phase_d/chain_probe.json','output/phase_d/source_rule_36000358.json',
                      'output/validation/high_hp_sample.json',
                      'output/审查报告/阶段D独立审查报告_2026-10-15.md',
                      'output/phase_d/external_reference/cid2327_database_20261015.json']
    evidence, evidence_errors, parsed_evidence = {}, {}, {}
    for p in evidence_paths:
        try:
            evidence[p] = sha(Path(p).read_bytes())
            if p.endswith('.json'):
                parsed_evidence[p] = strict_load(Path(p).read_bytes())
        except (OSError,ValueError) as error:
            evidence_errors[p] = str(error)
    metadata = parsed_evidence.get('output/il2cpp/sample_code.json',{})
    sample = parsed_evidence.get('output/sample/sample.json',{})
    native_hash = metadata.get('native_image_sha256')
    rules_enabled = bool(native_hash) and all(p in parsed_evidence for p in evidence_paths[:5])
    rules_enabled = rules_enabled and all(parsed_evidence[p].get('native_image_sha256',native_hash)==native_hash for p in evidence_paths[1:5])
    rules_enabled = rules_enabled and sample.get('phase_d',{}).get('status')=='CONDITIONAL_ASSOCIATION_CONFIRMED'
    rules_enabled = rules_enabled and parsed_evidence.get('output/validation/high_hp_sample.json',{}).get('status')=='PASS'
    documents = []
    for row in decoded['files']:
        p = Path('output/decoded')/(row['filename']+'.json.raw')
        originals = [c for c in collected if Path(c.get('local','')).name==row['filename'] and c.get('sha256_local')==row['source_sha256']]
        documents.append({'layer':'CACHE','path':p.as_posix(),**read_source(p),
                          'expected_sha256':row['json_raw_sha256'], 'origin':{'kind':'COLLECTED_DATA5',
                          'work_input':row['source'],'encrypted_source_sha256':row['source_sha256'],
                          'original_collections':originals,'decoder_report':'output/decoded/report.json'}})
    for filename in ('_mdBossInfo.json','_mdCharacter.json','_mdSAbirity.json','_mdSkill.json'):
        p = Path('output/base_master')/filename
        documents.append({'layer':'APK','path':p.as_posix(),**read_source(p),
                          'origin':{'kind':'APK_UNITY_COMPONENT_EXPORT','apk':baseline['apk'],
                          'apk_sha256':baseline['sha256'],'asset':archive['source'],'asset_sha256':archive['source_sha256'],
                          'serialized_file':archive['serialized_file'],'object_path_id':archive['object_path_id'],
                          'object_sha256':archive['object_sha256'],'component_field':p.stem,
                          'component_binary_file':'output/base_master/ChronicleArchiveData.bin',
                          'object_byte_start_in_serialized_file':archive['object_byte_start_in_serialized_file'],
                          'object_byte_size':archive['object_byte_size'],
                          'decoder_report':'output/base_master/report.json'}})
    identity = [{'layer':d['layer'],'path':d['path'],'sha256':sha(d['raw']) if d['raw'] is not None else None,
                 'origin':d['origin'],**({'read_error':d['read_error']} if 'read_error' in d else {})} for d in documents]
    snapshot = 'snapshot_'+sha(compact(identity).encode())[:20]
    parser_hash = sha(Path(__file__).read_bytes())
    verifier_hash = sha(Path('scripts/verify_export.py').read_bytes())
    support_paths = ['scripts/phase_d_chain_probe.py','scripts/phase_d_source_rule.py','scripts/sample_trace.py']
    support_hashes = {p:sha(Path(p).read_bytes()) for p in support_paths}
    build = 'build_'+sha(compact({'parser':parser_hash,'verifier':verifier_hash,'support':support_hashes,'rules':RULE_VERSION,'evidence':evidence,'evidence_errors':evidence_errors}).encode())[:16]
    destination = args.output_root/snapshot/build
    if destination.exists():
        old = strict_load((destination/'manifest.json').read_bytes())
        for name, expected in old['output_sha256'].items():
            if sha((destination/name).read_bytes()) != expected:
                raise ValueError(f'Existing immutable export differs: {name}')
        # Select only after every payload has passed; never touch the old payload.
        write_json(args.output_root/'latest.json',{'snapshot_id':snapshot,'build_id':build,'directory':destination.as_posix()})
        print(compact({'status':'EXISTING_SNAPSHOT_VERIFIED','output':destination.as_posix()}))
        return
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging = destination.with_name(destination.name+'.partial')
    if staging.exists():
        raise ValueError(f'Partial build retained for diagnosis: {staging}; use another output root or inspect it')
    staging.mkdir()
    for p in list(evidence)+support_paths+['scripts/export_master.py','scripts/verify_export.py','requirements-lock.txt']:
        copied = staging/'provenance'/p
        copied.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,copied)
    anomalies, records, sources = [], [], []
    core = {('CACHE','charainfo.data5.json.raw'):('charainfo','cid'),
            ('CACHE','skilllist.data5.json.raw'):('skilllist','skillid'),
            ('APK','_mdCharacter.json'):('charainfo','cid'),('APK','_mdSkill.json'):('skilllist','skillid')}
    unavailable = set()
    for d in documents:
        source_key = d['layer']+'/'+Path(d['path']).name
        copy = Path('sources')/source_key
        (staging/copy).parent.mkdir(parents=True,exist_ok=True)
        if d['raw'] is not None:
            (staging/copy).write_bytes(d['raw'])
        source = {'source_key':source_key,'layer':d['layer'],'input_file':d['path'],
                  'copied_file':copy.as_posix() if d['raw'] is not None else None,
                  'sha256':sha(d['raw']) if d['raw'] is not None else None,'origin':d['origin'],
                  'snapshot_id':snapshot,'input_bytes':len(d['raw']) if d['raw'] is not None else None,
                  'location_scope':'ORIGINAL_DECOMPRESSED_UTF8_JSON' if d['layer']=='CACHE' else 'EXPORTED_TYPEDTREE_UTF8_JSON_NOT_UNITY_BINARY_OFFSETS'}
        sources.append(source)
        selected = core.get((d['layer'],Path(d['path']).name))
        if selected:
            source.update(main_table=selected[0],id_key=selected[1],record_count=None)
        try:
            if 'read_error' in d:
                raise ValueError('Source unavailable: '+d['read_error'])
            if d.get('expected_sha256') and source['sha256'] != d['expected_sha256']:
                raise ValueError('Decoded bytes differ from decoder report')
            if selected:
                table, id_key = selected
                document, located = parse_records(d['raw'],table)
                source.update(main_table=table,id_key=id_key,record_count=len(located),
                              other_top_level_fields={k:v for k,v in document.items() if k!=table})
                for raw, location in located:
                    key = source_key+'#'+location['json_pointer']
                    status = 'PRESERVED'
                    if not isinstance(raw,dict) or not valid_id(raw.get(id_key)):
                        status = 'INVALID_OR_MISSING_ID_PRESERVED'
                        anomalies.append({'status':status,'record_key':key,'raw':raw})
                    records.append({'snapshot_id':snapshot,'parser_version':PARSER_VERSION,'rule_version':RULE_VERSION,
                                    'source_key':source_key,'record_key':key,'layer':d['layer'],'table':table,
                                    'id_field':id_key,'id_raw':raw.get(id_key) if isinstance(raw,dict) else None,
                                    'location':location,'preservation_status':status,'raw':raw,
                                    'interpretation':annotate(raw,rules_enabled and table=='skilllist')})
            else:
                strict_load(d['raw'])
                source['export_scope'] = 'COMPLETE_JSON_DOCUMENT; auxiliary schema not normalized to core JSONL'
            source['status'] = 'PARSED_AND_PRESERVED'
        except (ValueError,IndexError,UnicodeError) as error:
            source.update(status='ERROR_RAW_BYTES_PRESERVED',error=str(error))
            anomalies.append({'status':'SOURCE_PARSE_OR_INTEGRITY_ERROR','source_key':source_key,
                              'error':str(error),'raw_file':source['copied_file']})
            if selected and selected[0]=='skilllist':
                unavailable.add(d['layer'])
    by_key = {r['record_key']:r for r in records}
    indexes = {layer:build_index([r for r in records if r['layer']==layer and r['table']=='skilllist'],'skillid') for layer in ('APK','CACHE')}
    for record in records:
        if record['table']=='skilllist':
            raw = record['raw'] if isinstance(record['raw'],dict) else {}
            names = [name for name,value in metadata.get('enums',{}).get('ABILITY_TYPE',{}).items() if value['value']==raw.get('ability')]
            record['effect_type'] = {'code_raw':raw.get('ability'),'enum_candidates':names,
                                    'status':'STATIC_ENUM_MATCH' if len(names)==1 else 'UNKNOWN_OR_AMBIGUOUS_ENUM'}
    for layer in ('APK','CACHE'):
        for table,id_key in (('charainfo','cid'),('skilllist','skillid')):
            idx = build_index([r for r in records if r['layer']==layer and r['table']==table],id_key)
            for sid, candidates in idx.items():
                if len(candidates)>1:
                    anomalies.append({'status':'DUPLICATE_ID_ALL_RECORDS_PRESERVED','layer':layer,'table':table,
                                      'id_raw':sid,'record_keys':[r['record_key'] for r in candidates]})
    references = []
    for parent in records:
        raw = parent['raw']
        if not isinstance(raw,dict):
            continue
        field = 'sub' if parent['table']=='skilllist' else 'skillid'
        if field not in raw:
            continue
        values = raw[field]
        if not isinstance(values,list):
            anomalies.append({'status':'INVALID_REFERENCE_ARRAY_PRESERVED','record_key':parent['record_key'],'field':field,'raw':values})
            continue
        for ordinal, sid in enumerate(values):
            resolutions = {}
            for scenario in SCENARIOS:
                if field=='skillid' and len(values)!=4:
                    found = {'status':'SLOT_ROLE_UNKNOWN','candidates':[]}
                elif field=='skillid' and ordinal==0:
                    found = {'status':'SLOT0_SEPARATE_TYPE_NAMESPACE','candidates':[]}
                elif field=='skillid' and valid_id(sid) and sid==0:
                    found = {'status':'EMPTY_SLOT','candidates':[]}
                else:
                    found = lookup(sid,scenario,indexes,unavailable)
                resolutions[scenario] = found
            references.append({'snapshot_id':snapshot,'parent_record_key':parent['record_key'],
                               'reference_key':parent['record_key']+'/'+field+'/'+str(ordinal),
                               'parent_layer':parent['layer'],'field':field,'ordinal':ordinal,'id_raw':sid,
                               'declaration_only':True,'resolution':resolutions,
                               'execution_scope':'ONE_LEVEL_SUB_ONLY' if field=='sub' else 'MASTER_DEFINITION_NOT_PLAYER_UNLOCK_STATE'})
    record_files = []
    for source in sources:
        if 'main_table' in source:
            relative = f"tables/{source['layer']}/{source['main_table']}.jsonl"
            source['records_file'] = relative
            record_files.append(relative)
            write_lines(staging/relative,(r for r in records if r['source_key']==source['source_key']))
    write_lines(staging/'references.jsonl',references)
    write_lines(staging/'anomalies.jsonl',anomalies)
    conflicts = []
    for table,id_field in (('charainfo','cid'),('skilllist','skillid')):
        by_layer = {layer:build_index([r for r in records if r['layer']==layer and r['table']==table],id_field) for layer in ('APK','CACHE')}
        for sid in sorted(by_layer['APK'].keys() & by_layer['CACHE'].keys()):
            a,c = by_layer['APK'][sid],by_layer['CACHE'][sid]
            if len(a)!=1 or len(c)!=1:
                conflicts.append({'table':table,'id_raw':sid,'status':'AMBIGUOUS_SOURCE_ID',
                                  'APK_record_keys':[r['record_key'] for r in a],'CACHE_record_keys':[r['record_key'] for r in c]})
                continue
            av,cv = a[0]['raw'],c[0]['raw']
            fields = []
            for field in sorted(av.keys() | cv.keys()):
                if field not in av or field not in cv or typed_value(av[field])!=typed_value(cv[field]):
                    fields.append({'field':field,'APK':{'present':field in av,**({'raw':av[field]} if field in av else {})},
                                   'CACHE':{'present':field in cv,**({'raw':cv[field]} if field in cv else {})}})
            conflicts.append({'table':table,'id_raw':sid,'status':'DIFFERENT_FIELDS_OR_TYPES' if fields else 'IDENTICAL_RECORDS',
                              'APK_record_key':a[0]['record_key'],'CACHE_record_key':c[0]['record_key'],
                              'differences':fields,'merge_performed':False})
    write_lines(staging/'source_conflicts.jsonl',conflicts)
    expansions = []
    for parent in records:
        if parent['table']=='skilllist' and valid_id(parent['id_raw']):
            for scenario in SCENARIOS:
                expansions.append({'requested_from':parent['record_key'],'root_id_raw':parent['id_raw'],
                                   'scenario':scenario,**expand_roots([parent['id_raw']],scenario,indexes,by_key,unavailable)})
    write_lines(staging/'one_level_expansions.jsonl',expansions)
    with (staging/'records_view.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields = ['snapshot_id','source_key','record_key','table','id_raw','name','title','ability_raw',
                  'skill_slots_json','sub_json','parameters_json','param0_to5_presence_json','interpretation_status']
        writer = csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        for record in records:
            raw = record['raw'] if isinstance(record['raw'],dict) else {}
            row = {k:record[k] for k in ('snapshot_id','source_key','record_key','table','id_raw')}
            row.update(name=raw.get('name'),title=raw.get('title'),ability_raw=raw.get('ability'),
                       skill_slots_json=compact(raw['skillid']) if 'skillid' in raw and isinstance(raw['skillid'],list) else '',
                       sub_json=compact(raw['sub']) if 'sub' in raw else '',
                       parameters_json=compact({k:v['raw'] for k,v in record['interpretation']['parameters'].items()}),
                       param0_to5_presence_json=compact({f'param{i}':('MISSING' if f'param{i}' not in raw else 'NULL' if raw[f'param{i}'] is None else 'PRESENT') for i in range(6)}),
                       interpretation_status=record['interpretation']['status'])
            writer.writerow({k:csv_text(v) for k,v in row.items()})
    counts = {layer:{table:sum(r['layer']==layer and r['table']==table for r in records) for table in ('charainfo','skilllist')} for layer in ('APK','CACHE')}
    reference_counts = {layer:{field:sum(r['parent_layer']==layer and r['field']==field for r in references) for field in ('skillid','sub')} for layer in ('APK','CACHE')}
    resolution_counts = {scenario:dict(Counter(r['resolution'][scenario]['status'] for r in references)) for scenario in SCENARIOS}
    sub_resolution_counts = {layer:{scenario:dict(Counter(r['resolution'][scenario]['status'] for r in references if r['parent_layer']==layer and r['field']=='sub')) for scenario in SCENARIOS} for layer in ('APK','CACHE')}
    slot_counts = {layer:dict(Counter(str(len(r['raw']['skillid'])) for r in records if r['layer']==layer and r['table']=='charainfo' and isinstance(r['raw'],dict) and isinstance(r['raw'].get('skillid'),list))) for layer in ('APK','CACHE')}
    manifest = {'status':'EXPORTED_WITH_PRESERVED_ANOMALIES' if anomalies else 'EXPORTED',
                'snapshot_id':snapshot,'build_id':build,'parser_version':PARSER_VERSION,'parser_sha256':parser_hash,
                'verifier_sha256':verifier_hash,
                'support_script_sha256':support_hashes,
                'rule_version':RULE_VERSION,'APK_identity':baseline['identity'],'APK_baseline_sha256':baseline['sha256'],
                'runtime':{'python':sys.version,'added_dependencies':[],'requirements_lock_sha256':sha(Path('requirements-lock.txt').read_bytes())},
                'rules_enabled':rules_enabled,'evidence_sha256':evidence,'sources':sources,'record_counts':counts,
                'evidence_errors':evidence_errors,'rules_disabled_scope':None if rules_enabled else 'Local parameter interpretation only; raw export unaffected',
                'reference_counts':reference_counts,'resolution_counts':resolution_counts,'slot_array_lengths':slot_counts,
                'sub_resolution_counts':sub_resolution_counts,
                'source_conflict_counts':{table:dict(Counter(r['status'] for r in conflicts if r['table']==table)) for table in ('charainfo','skilllist')},
                'interpretation_counts':{layer:{'HighHPAll_records':sum(r['layer']==layer and r['table']=='skilllist' and isinstance(r['raw'],dict) and r['raw'].get('ability')==1105 for r in records),
                                              'skill_records_without_parameter_rules':sum(r['layer']==layer and r['table']=='skilllist' and r['interpretation']['status']=='UNKNOWN' for r in records),
                                              'unrecognized_effect_enum_records':sum(r['layer']==layer and r['table']=='skilllist' and r.get('effect_type',{}).get('status')!='STATIC_ENUM_MATCH' for r in records)} for layer in ('APK','CACHE')},
                'record_count':len(records),'reference_count':len(references),'anomaly_count':len(anomalies),
                'record_files':record_files,
                'one_level_expansion_count':len(expansions),'scenarios':{
                    'APK_ONLY':'Assume only exported APK daSkill table loaded',
                    'JSON_SNAPSHOT_WITH_APK_FALLBACK':'Assume exported cache snapshot populates JSON daSkill and APK base is loaded; not current device observation'},
                'semantics_limits':['Rules restricted to reviewed APK ability1105 present param0/1/2/3/5; no param4 default fill or evaluator',
                                    'Four-slot first value is separate type namespace; eight-slot roles remain unknown, all values retained',
                                    'Every source record preserved independently; no field merge; no claim of current player activation/final multiplier',
                                    'CSV is derived filter view; apostrophe may prefix formula-like text; full raw/type/missing values are in JSONL and copied JSON',
                                    'Counts describe records including NPCs and snapshots, not playable cards or whole-game coverage'],
                'output_sha256':{}}
    for p in sorted(staging.rglob('*')):
        if p.is_file():
            manifest['output_sha256'][p.relative_to(staging).as_posix()] = sha(p.read_bytes())
    write_json(staging/'manifest.json',manifest)
    staging.rename(destination)
    write_json(args.output_root/'latest.json',{'snapshot_id':snapshot,'build_id':build,'directory':destination.as_posix()})
    print(compact({'status':manifest['status'],'output':destination.as_posix(),'records':counts,
                   'references':reference_counts,'anomalies':len(anomalies),'rules_enabled':rules_enabled}))


if __name__=='__main__':
    main()
