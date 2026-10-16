"""Verify the current card and type105/112 overlays, without replaying A-E."""
import csv
import hashlib
import json
import re
import struct
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from chica_description_effects import fallback_records

OUT = Path('output/card_comparison_cid30236')
SOURCE = Path('output/cache_full_20261015_v3/records.jsonl')

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

records = {r['record_key']: r for r in map(json.loads, SOURCE.open(encoding='utf-8'))}
assert not any(r['table']=='skilllist' and r['raw'].get('skillid')==106001 for r in records.values())
records.update({r['record_key']:r for r in fallback_records()})
comparison, evidence = load(OUT/'comparison.json'), load(OUT/'evidence.json')
views, rules = load(OUT/'verified_parameter_views.json'), load(OUT/'field_dictionary.json')
manifest = load(OUT/'manifest.json')
effects=load(OUT/'description_effects.json')
checks = []

def check(name, passed, **details):
    assert passed, name
    checks.append(dict(name=name, passed=True, **details))

check('manifest_inputs_and_generated_payloads',
      manifest['source_sha256'] == sha(SOURCE)
      and manifest['generator_sha256'] == sha('scripts/build_chica_comparison.py')
      and manifest['screenshot_sha256'] == sha(OUT/'reference.png')
      and all(sha(p) == h for group in ('semantic_inputs', 'analysis_scripts') for p,h in manifest[group].items())
      and all(sha(OUT/p) == h for p,h in manifest['payloads'].items()))
check('54_evidence_records_equal_v3', len(evidence) == 54 and all(r == records[r['record_key']] for r in evidence))
check('33_rows_all_record_links_resolve', len(comparison) == 33 and all(k in records for r in comparison for k in r['record_keys']))

samples = next(r for r in comparison if r['title'] == '前方 5 连击倍率')
check('six_sample_fields_and_explicit_progress_states', len(samples['field_comparisons']) == 6
      and samples['raw_value_status'] == 'RAW_FOUND'
      and samples['correspondence_status'] == 'CONFIRMED_PATTERN_CODE_AND_SCREENSHOT_VALUES'
      and samples['calculation_status'] == 'CONFIRMED_LOCAL_INPUT_RULE_NOT_FINAL_DAMAGE')
expected = {43023601: (43023600, 3.5), 43023600: (43023605, 3.75), 43023602: (43023609, 4.25)}
boss_bytes = Path('output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw').read_bytes()
for v in samples['field_comparisons']:
    sid, p1 = expected[v['pattern_id']]
    source = records[v['record_key']]
    pattern = records[v['pattern_record_key']]
    assert source['table'] == 'bossskill' and pattern['table'] == 'bosspattern'
    assert pattern['raw']['skillid0'] == sid == source['raw']['skillid']
    assert source['raw']['skillid0'] == 105
    assert source['raw']['skillparam1'] == p1 and source['raw']['skillparam6'] == 5
    assert v['description_ja'] == pattern['raw'].get('sinfo')
    for r in (source, pattern):
        loc = r['location']; blob = boss_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
        assert json.loads(blob) == r['raw']
        assert hashlib.sha256(blob).hexdigest() == loc['raw_record_sha256']
check('three_pattern_boss_namespaces_and_source_bytes', True)

traps = next(r for r in comparison if r['title']=='陷阱、次数与倍率')
assert len(traps['field_comparisons']) == 42 and traps['status']=='raw'
assert traps['calculation_status']=='CONFIRMED_LOCAL_TRAP_RULES_FINAL_STATE_AND_DAMAGE_UNKNOWN'
expected_traps={43023601: ((43023602,43023603),.75),43023600: ((43023606,43023607),.875),43023602: ((43023610,43023611),1.125)}
for v in traps['field_comparisons']:
    sids,p1=expected_traps[v['pattern_id']]
    source,pattern=records[v['record_key']],records[v['pattern_record_key']]
    assert source['table']=='bossskill' and source['raw']['skillid0']==112
    assert v['record_id']==sids[v['pattern_slot']-2]==pattern['raw'][f'skillid{v["pattern_slot"]}']
    expected_value={'/skillparam1':p1,'/skillparam0':1,'/skillparam4':.25,'/skillparam5':5,'/skillparam7':.001,'/skillparam8':88725,'/skillparam9':1}[v['field_path']]
    assert v['raw_value']==expected_value==source['raw'][v['field_path'][1:]]
    assert v['description_ja']==pattern['raw'].get('sinfo')
    for r in (source,pattern):
        loc=r['location'];blob=boss_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
        assert json.loads(blob)==r['raw'] and hashlib.sha256(blob).hexdigest()==loc['raw_record_sha256']
check('42_type112_sample_fields_pattern_slots_bytes_and_partial_status',True)
guard=next(r for r in comparison if r['title']=='防御提升的单位')
assert guard['status']=='yes' and len(guard['field_comparisons'])==3
assert guard['calculation_status']=='CONFIRMED_PLAYER_BASIS_WITH_MODIFIERS_AND_TRUNCATION'
for v in guard['field_comparisons']:
    r,p=records[v['record_key']],records[v['pattern_record_key']]
    assert r['table']=='bossskill' and r['raw']['skillid0']==13 and p['raw']['skillid4']==v['record_id']
    assert v['field_path']=='/skillparam2' and v['raw_value']==r['raw']['skillparam2']
    assert v['calculation_status']=='CONDITIONAL_PLAYER_NORMAL_ATK_BASIS'
    assert v['converted_value']==v['raw_value']*.1
check('three_type13_guard_samples_conditional_player_basis',True)

expected_keys = {(r['record_key'], '/' + f) for r in records.values()
                 if r['table'] == 'bossskill' and r['raw'].get('skillid0') in (105,112,13)
                 for f in ({105:('skillparam1','skillparam6'),112:('skillparam0','skillparam1','skillparam4','skillparam5','skillparam7','skillparam8','skillparam9'),13:('skillparam2',)}[r['raw']['skillid0']]) if f in r['raw']}
boss_views=[v for v in views if v['table']=='bossskill' and v['effect_type'] in (105,112,13)]
ordinary_views=[v for v in views if v['table']=='skilllist']
actual_keys = {(v['record_key'], v['field_path']) for v in boss_views}
assert len(boss_views) == len(actual_keys) == len(expected_keys) == 1659
assert len({v['record_key'] for v in boss_views}) == 956 and actual_keys == expected_keys
assert Counter(v['effect_type'] for v in boss_views)=={105:284,112:657,13:718}
for v in boss_views:
    r = records[v['record_key']]; f = v['field_path'][1:]
    assert v['effect_type'] == r['raw']['skillid0']
    assert type(v['raw_value']) is type(r['raw'][f]) and v['raw_value'] == r['raw'][f]
    assert v['location'] == r['location'] and v['source_sha256'] == r['source_sha256']
    assert v['original_file'] == r['original_file']
    assert v['json_pointer'] == r['location']['json_pointer'] + '/' + f
    converted=(r['raw'][f]*.1 if f=='skillparam2' else int(r['raw'][f]) if f in ('skillparam5','skillparam6') else float(r['raw'][f]) if f in ('skillparam4','skillparam7') else int(r['raw'][f]).bit_count() if f=='skillparam8' else int(r['raw'][f])!=0 if f=='skillparam9' else 1 if f=='skillparam0' and r['raw'][f]==1 else 0 if f=='skillparam0' else None)
    assert v['converted_value'] == converted
    if f=='skillparam7':assert v['correspondence_status']=='INFERRED_DESCRIPTION_TO_DAMAGEL_ACTION'
    if v['effect_type']==13:assert v['calculation_status']=='CONDITIONAL_PLAYER_NORMAL_ATK_BASIS'
check('1659_present_fields_exact_and_scoped', True)
boss_rules=[r for r in rules if r['table']=='bossskill' and r['effect_type'] in (105,112,13)]
check('ten_separately_boss_type_scoped_rules', len(boss_rules) == 10
      and Counter((r['effect_type'],r['occurrences']) for r in boss_rules)=={(105,142):2,(112,96):3,(112,93):2,(112,91):1,(112,92):1,(13,718):1})
ordinary_trace=load(OUT/'ordinary_rules/trace.json')
ordinary_checks=load(OUT/'ordinary_rules/native_checks.json')
expected_ordinary={(c['skill_id'],'/'+c['field']) for c in ordinary_checks['checks'] if c.get('qualifier')}
power_trace=load(OUT/'skill_power/trace.json')
power_checks=load(OUT/'skill_power/native_checks.json')
expected_ordinary.update((c['skill_id'],'/'+c['field']) for c in power_checks['checks'])
timed_trace=load(OUT/'timed_support/trace.json')
timed_checks=load(OUT/'timed_support/native_checks.json')
expected_ordinary.update((r['raw']['skillid'],'/'+f) for r in timed_trace['source_records'] for f in (('param1','param2','param6') if r['raw']['ability']==3000 else ('param7','param9','param0') if r['raw']['ability']==99 else ('param1','param3','param0')))
critical_trace=load(OUT/'critical/trace.json');critical_checks=load(OUT/'critical/native_checks.json')
expected_critical={(43023601,'/param6'),(65000001,'/param6'),(65000001,'/param5'),(43023607,'/param5'),(43023607,'/param6'),(43023606,'/param4'),(43023606,'/param5'),(43023608,'/param4'),(43023608,'/param6'),(43023609,'/param4'),(43023609,'/param8'),(43023611,'/param8')}
expected_critical.update((sid,'/'+field) for sid in (43023612,43023613,43023614) for field in ('param4','param5'))
expected_ordinary.update(expected_critical)
movement_trace=load(OUT/'movement/trace.json');movement_checks=load(OUT/'movement/native_checks.json')
expected_movement={(sid,'/param2') for sid in (43023605,43023606,43023607,65000001,65000002,43023608,43023609)}|{(43023616,'/param8'),(43023607,'/param7')}
expected_ordinary.update(expected_movement)
lifesteal_trace=load(OUT/'lifesteal/trace.json');lifesteal_checks=load(OUT/'lifesteal/native_checks.json')
expected_lifesteal={(65000003,'/param1'),(65000003,'/flag0_1')}
expected_ordinary.update(expected_lifesteal)
mana_chance_trace=load(OUT/'mana_chance/trace.json');mana_chance_checks=load(OUT/'mana_chance/native_checks.json')
expected_mana_chance={(43023602,'/'+f) for f in ('param0','param1','param2','param4','param5','param6')}
expected_ordinary.update(expected_mana_chance)
chain_mana_trace=load(OUT/'chain_mana/trace.json');chain_mana_checks=load(OUT/'chain_mana/native_checks.json')
expected_chain_mana={(43023617,'/param'+str(i)) for i in range(5)}
expected_ordinary.update(expected_chain_mana)
reusable_trace=load('output/ordinary_effects/ability1095/trace.json')
reusable_checks=load('output/ordinary_effects/ability1095/native_checks.json')
reusable_records=[r for r in records.values() if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==1095]
expected_ordinary.update((r['raw']['skillid'],'/'+field) for r in reusable_records for field in ('param1','param3'))
job_trace=load('output/ordinary_effects/ability1017/trace.json')
job_checks=load('output/ordinary_effects/ability1017/native_checks.json')
job_records=[r for r in records.values() if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==1017]
expected_ordinary.update((r['raw']['skillid'],'/'+field) for r in job_records for field in ('param0','iParam0','param1','param3'))
support_trace=load('output/ordinary_effects/ability2012/trace.json')
support_checks=load('output/ordinary_effects/ability2012/native_checks.json')
support_records=[r for r in records.values() if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==2012]
expected_ordinary.update((r['raw']['skillid'],'/'+field) for r in support_records for field in ('param0','param4','param5') if field in r['raw'])
sympathy_trace=load('output/ordinary_effects/ability3000/trace.json')
sympathy_checks=load('output/ordinary_effects/ability3000/native_checks.json')
sympathy_records=[r for r in records.values() if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==3000]
expected_ordinary.update((r['raw']['skillid'],'/'+field) for r in sympathy_records for field in ('param1','param2','param6','param8') if field in r['raw'])
drain_trace=load('output/ordinary_effects/ability99/trace.json')
drain_checks=load('output/ordinary_effects/ability99/native_checks.json')
drain_records=[r for r in records.values() if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==99]
expected_ordinary.update((r['raw']['skillid'],'/'+field) for r in drain_records for field in ('param7','param9','param0') if field in r['raw'])
stage_trace=load('output/ordinary_effects/ability7/trace.json')
stage_checks=load('output/ordinary_effects/ability7/native_checks.json')
stage_records=[r for r in records.values() if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==7]
expected_ordinary.update((r['raw']['skillid'],'/'+field) for r in stage_records for field in ('param0','param1','param3'))
stage_all_trace=load('output/ordinary_effects/ability1008/trace.json')
stage_all_checks=load('output/ordinary_effects/ability1008/native_checks.json')
stage_all_records=[r for r in records.values() if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==1008]
expected_ordinary.update((r['raw']['skillid'],'/'+field) for r in stage_all_records for field in ('param0','param1','param3'))
assert len(expected_critical)==18
assert len(expected_ordinary)==len(ordinary_views)==4947
assert {(v['record_id'],v['field_path']) for v in ordinary_views}==expected_ordinary
assert len({v['record_key'] for v in ordinary_views})==1723
assert len([r for r in rules if r['table']=='skilllist'])==60
for v in ordinary_views:
    r=records[v['record_key']];f=v['field_path'][1:];raw=r['raw'][f]
    assert r in ordinary_trace['source_records']+power_trace['source_records']+timed_trace['source_records']+critical_trace['source_records']+movement_trace['source_records']+lifesteal_trace['source_records']+mana_chance_trace['source_records']+chain_mana_trace['source_records']+reusable_trace['source_records']+job_trace['source_records']+support_trace['source_records']+sympathy_trace['source_records']+drain_trace['source_records']+stage_trace['source_records']+stage_all_trace['source_records'] and v['raw_value']==raw and type(v['raw_value']) is type(raw)
    assert v['effect_type']==r['raw']['ability'] and v['location']==r['location']
    assert v['source_sha256']==r['source_sha256'] and v['json_pointer']==r['location']['json_pointer']+'/'+f
    if v['effect_type'] in (7,1008) and f=='param0':
        expected_converted=[x for x in (raw%100,(raw//100)%100,(raw//10000)%100) if x]
    elif v['effect_type']==2012:
        expected_converted=raw if f=='param0' else raw*100
    elif v['effect_type']==1017 and f in ('param0','iParam0'):
        expected_converted=int(raw) if f=='param0' else [i for i in range(6) if raw&(1<<i)]
    elif (v['record_id'],v['field_path']) in expected_chain_mana:
        expected_converted=int(raw) if f=='param0' else raw*100
    elif (v['record_id'],v['field_path']) in expected_mana_chance:
        expected_converted=1<<int(raw) if f=='param6' else raw*100
    elif (v['record_id'],v['field_path']) in expected_lifesteal:
        expected_converted=raw*100 if f=='param1' else 1.4
    elif (v['record_id'],v['field_path']) in expected_movement:
        expected_converted=raw if f=='param7' else raw*100 if v['effect_type'] in (64,65,99) else (raw-1)*100
    elif (v['record_id'],v['field_path']) in expected_critical:
        expected_converted=(raw-1.5)*100 if v['effect_type']==1095 and f=='param6' else raw*100
    elif v['effect_type'] in (64,65,99,3000):expected_converted=raw if f in ('param0','param6') else raw*100
    else:expected_converted=(raw-1)*100 if f in ('param0','param1') else (1-raw)*100
    assert v['converted_value']==expected_converted
check('4947_ordinary_fields_60_rules_and_1723_exact_source_records',True)
assert reusable_trace['source_records']==reusable_records and len(reusable_records)==407
assert reusable_trace['source_sha256']==sha(SOURCE) and reusable_trace['script_sha256']==sha('scripts/ordinary_1095_probe.py')
assert reusable_trace['native_sha256']==reusable_checks['native_sha256']==ordinary_trace['native_sha256']
assert reusable_trace['metadata_sha256']==ordinary_trace['metadata_sha256']
assert reusable_trace['ability_enum']['default']['value']==1095 and reusable_trace['ability_enum']['name']=='Always3'
assert reusable_trace['reused_proof']['sha256']==sha(reusable_trace['reused_proof']['path'])
assert len(reusable_checks['checks'])==32 and all(c['passed'] and c['result']==c['expected_float32'] for c in reusable_checks['checks'])
assert len(reusable_trace['sample_ids'])==8 and {c['skill_id'] for c in reusable_checks['checks']}==set(reusable_trace['sample_ids'])
for field in ('param1','param3'):
    assert {min(r['raw'][field] for r in reusable_records),max(r['raw'][field] for r in reusable_records)} <= {
        c['raw_value'] for c in reusable_checks['checks'] if c['field']==field}
for c in reusable_checks['checks']:
    r=next(r for r in reusable_records if r['raw']['skillid']==c['skill_id'])
    assert c['raw_value']==r['raw'][c['field']] and c['initial_factor']==1.2
    assert c['reads']==([dict(source_id=c['skill_id'],field=c['field'],raw=c['raw_value'],origin='SOURCE')] if c['qualifier'] else [])
check('32_native_samples_bound_to_1095_type_branch_current_inputs_and_observed_numeric_extremes',True)

skill_bytes=Path('output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw').read_bytes()
for r in reusable_records:
    loc=r['location'];fragment=skill_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert json.loads(fragment)==r['raw'] and hashlib.sha256(fragment).hexdigest()==loc['raw_record_sha256']
reusable_views=[v for v in ordinary_views if v['effect_type']==1095 and v['field_path'] in ('/param1','/param3')]
assert len(reusable_views)==814
for v in views:
    source=records.get(v['record_key'],{}).get('raw',{})
    assert v['skill_name_ja']==source.get('name',source.get('sname'))
    assert v['skill_text_ja']==source.get('text',source.get('sinfo'))
for field in ('/param1','/param3'):
    rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',1095,field))
    assert rule['occurrences']==407 and '407' in rule['applicability']
    assert '../ordinary_effects/ability1095/trace.json' in rule['evidence']
assert all(v['raw_value_status']=='RAW_FOUND' and v['calculation_status']=='CONFIRMED_LOCAL_INPUT_RULE' for v in reusable_views)
assert len(views)==6613 and len({v['record_key'] for v in views})==2684
check('407_1095_records_814_fields_source_bytes_names_and_scoped_rules_no_duplicate_keys',len({(v['record_key'],v['field_path']) for v in views})==len(views))

assert job_trace['source_records']==job_records and len(job_records)==321
assert job_trace['source_sha256']==sha(SOURCE) and job_trace['script_sha256']==sha('scripts/ordinary_1017_probe.py')
assert all(sha(p)==h for p,h in job_trace['fixture_scripts'].items())
assert job_trace['native_sha256']==job_checks['native_sha256']==ordinary_trace['native_sha256']
assert job_trace['metadata_sha256']==ordinary_trace['metadata_sha256']
assert job_trace['ability_enum']['name']=='StrengthJob2' and job_trace['ability_enum']['default']['value']==1017
assert job_trace['reused_proof']['sha256']==sha(job_trace['reused_proof']['path'])
assert [(j['name'],j['default']['value'],j['bit']) for j in job_trace['job_enum']]==[
    ('WARRIOR',0,1),('ARCHERY',1,2),('WIZARD',2,4),('HEALER',3,8),('SHIELD',4,16),('ALMIGHTY',5,32)]
assert {r['raw']['param0'] for r in job_records}=={1}
assert {r['raw']['iParam0'] for r in job_records}==set(job_trace['source_job_masks']) and len(job_trace['source_job_masks'])==15
assert len(job_checks['checks'])==236 and all(c['passed'] for c in job_checks['checks'])
matrix=job_checks['checks'][:180]
assert {(c['source_job_mask'],c['receiver_job'],c['field']) for c in matrix}=={
    (mask,job,field) for mask in job_trace['source_job_masks'] for job in range(6) for field in ('param1','param3')}
controls=[c for c in job_checks['checks'] if c['fixture_param0_override'] is not None]
assert len(controls)==48 and {c['fixture_param0_override'] for c in controls}=={0,1,.5,-.5,-1,2}
assert all(c['fixture_kind']=='CONTROL_ONLY_NOT_GAME_DATA' for c in controls)
for c in job_checks['checks']:
    r=next(r for r in job_records if r['raw']['skillid']==c['skill_id'])
    assert c['source_param0']==r['raw']['param0']==1 and c['source_job_mask']==r['raw']['iParam0']
    assert c['raw_value']==r['raw'][c['field']] and c['receiver_job_bit']==1<<c['receiver_job']
    value=c['source_param0'] if c['fixture_param0_override'] is None else c['fixture_param0_override']
    allowed=int(value)!=0 or not c['provider_is_receiver']
    qualified=allowed and bool(c['source_job_mask']&c['receiver_job_bit'])
    assert c['self_allowed']==allowed and c['qualified']==qualified and c['result']==c['expected_float32']
    assert c['float_fields_read']==['param0']+([c['field']] if qualified else [])
assert all(not c['qualified'] for c in matrix if c['receiver_job']==5)
assert [f['name'] for f in job_trace['receiver_fields']]==['_jobType','_listSkill']
assert job_trace['provider_field']['name']=='_param' and job_trace['provider_field']['offset']=='0x28'
check('236_1017_native_checks_all_15_masks_receiver_jobs_self_gate_and_control_values_separate_from_source',True)

job_views=[v for v in ordinary_views if v['effect_type']==1017 and v['field_path'] in ('/param0','/iParam0','/param1','/param3')]
assert len(job_views)==1284
for r in job_records:
    loc=r['location'];fragment=skill_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert json.loads(fragment)==r['raw'] and hashlib.sha256(fragment).hexdigest()==loc['raw_record_sha256']
for path in ('/param0','/iParam0','/param1','/param3'):
    rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',1017,path))
    assert rule['occurrences']==321 and '321' in rule['applicability']
    assert '../ordinary_effects/ability1017/trace.json' in rule['evidence']
assert len(rules)==77 and all('接受者职业' in v['conditions'] for v in job_views)
check('321_1017_records_1284_present_fields_exact_source_bytes_formulas_and_four_scoped_rules',True)

assert support_trace['source_records']==support_records and len(support_records)==406
assert support_trace['source_sha256']==sha(SOURCE) and support_trace['script_sha256']==sha('scripts/ordinary_2012_probe.py')
assert support_trace['native_sha256']==support_checks['native_sha256']==ordinary_trace['native_sha256']
assert support_trace['metadata_sha256']==ordinary_trace['metadata_sha256']
assert all(sha(p)==h for p,h in support_trace['fixture_scripts'].items())
assert all(sha(p['path'])==p['sha256'] for p in support_trace['reused_proofs'])
assert support_trace['ability_enum']['name']=='SA_SupportTarget' and support_trace['ability_enum']['default']['value']==2012
assert support_trace['jump_table']['target']=='0x11a4014'
assert support_trace['action_gate_field']['name']=='_isSkillAbilityAction' and support_trace['action_gate_field']['offset']=='0x160'
assert [(s['name'],s['default']['value']) for s in support_trace['target_selector_enum']]==[('pGROUP_ALL',31),('MYSELF',64)]
assert len(support_checks['checks'])==49 and all(c['passed'] for c in support_checks['checks'])
actions=[c for c in support_checks['checks'] if c['name'].startswith('action_')]
assert len(actions)==34 and {c['chain_rate_fixture'] for c in actions}=={.5,1,2}
by_support_id={r['raw']['skillid']:r for r in support_records}
for c in actions:
    raw=by_support_id[c['skill_id']]['raw']
    for field,source_field in c['source_fields'].items():
        assert source_field['present']==(field in raw) and source_field['raw_value']==raw.get(field)
    assert c['handler_calls']==int(not c['already_processed']) and c['repeated_action_additional_calls']==0
    assert c['application_count']==len(c['applications'])
    assert c['application_count']==(0 if c['already_processed'] else min(c['target_count_fixture'],int(raw.get('param7',0)) or 1))
    for applied in c['applications']:
        def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]
        assert applied['ability_id']==raw['skillid'] and applied['ability_type']==2012
        assert applied['support_time']==f32(raw['param0'])
        assert applied['stored_chance']==f32(raw.get('param4',0)) and applied['stored_damage']==f32(raw.get('param5',0))
for field in ('param0','param4','param5'):
    assert {r['raw'][field] for r in support_records if field in r['raw']} <= {
        c['source_fields'][field]['raw_value'] for c in actions if c['source_fields'][field]['present']}
times=[c for c in support_checks['checks'] if c['name'].startswith('time_')]
assert len(times)==12 and all(c['remaining']==c['expected_float32'] for c in times)
assert {c['source_time'] for c in times}=={r['raw']['param0'] for r in support_records}
assert len([c for c in support_checks['checks'] if c['name'].startswith('support2_sum_')])==3
check('49_2012_native_checks_action_gate_chain_independent_contributions_defaults_and_game_time',True)

support_views=[v for v in ordinary_views if v['effect_type']==2012]
assert len(support_views)==1025 and Counter(v['field_path'] for v in support_views)=={'/param0':406,'/param4':308,'/param5':311}
for r in support_records:
    loc=r['location'];fragment=skill_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert json.loads(fragment)==r['raw'] and hashlib.sha256(fragment).hexdigest()==loc['raw_record_sha256']
    present={v['field_path'] for v in support_views if v['record_key']==r['record_key']}
    assert present=={'/'+f for f in ('param0','param4','param5') if f in r['raw']}
for v in views:
    if v['effect_type'] not in (7,99,1008,2012,3000):assert v['trigger_context'] is None
for v in support_views:
    r=records[v['record_key']];ctx=v['trigger_context']
    assert ctx['trigger_status']=='NATIVE_ACTION_DISPATCH_AND_PROCESSED_GATE_CONFIRMED' and 'OnAction' in v['conditions']
    assert ctx['missing_requested_fields']==[f for f in ('param0','param4','param5') if f not in r['raw']]
    assert ctx['target_selector']['raw_value']==r['raw']['param8']
    for field,source_field in ctx['source_field_refs'].items():
        assert source_field['record_key']==r['record_key'] and source_field['present']==(field in r['raw'])
        assert source_field['raw_value']==r['raw'].get(field) and source_field['source_sha256']==r['source_sha256']
        assert source_field['json_pointer']==r['location']['json_pointer']+'/'+field
    assert not ctx['additional_job_filter']['present'] and ctx['additional_job_filter']['raw_value'] is None
for path,count in (('/param0',406),('/param4',308),('/param5',311)):
    rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',2012,path))
    assert rule['occurrences']==count and '../ordinary_effects/ability2012/trace.json' in rule['evidence']
check('406_2012_records_1025_present_fields_exact_source_bytes_context_and_no_filled_missing_values',True)

assert sympathy_trace['source_records']==sympathy_records and len(sympathy_records)==382
assert sympathy_trace['source_sha256']==sha(SOURCE) and sympathy_trace['script_sha256']==sha('scripts/ordinary_3000_probe.py')
assert sympathy_trace['native_sha256']==sympathy_checks['native_sha256']==ordinary_trace['native_sha256']
assert sympathy_trace['metadata_sha256']==ordinary_trace['metadata_sha256']
assert all(sha(p)==h for p,h in sympathy_trace['fixture_scripts'].items())
assert all(sha(p['path'])==p['sha256'] for p in sympathy_trace['reused_proofs'])
assert sympathy_trace['ability_enum']['name']=='SAutoMotion' and sympathy_trace['ability_enum']['default']['value']==3000
assert sympathy_trace['support3_field']['offset']=='0x238'
assert len(sympathy_checks['checks'])==sympathy_trace['native_check_count']==86 and all(c['passed'] for c in sympathy_checks['checks'])
sympathy_applications=[c for c in sympathy_checks['checks'] if c['name'].startswith('apply_')]
assert len(sympathy_applications)==24 and {c['chain_fixture'] for c in sympathy_applications}=={.5,1,2}
by_sympathy_id={r['raw']['skillid']:r for r in sympathy_records}
for c in sympathy_applications:
    raw=by_sympathy_id[c['skill_id']]['raw']
    assert c['support_category']=='Support3' and c['application_count']==len(c['submissions'])
    for field,ref in c['source_fields'].items():assert ref['present']==(field in raw) and ref['raw_value']==raw.get(field)
    for applied in c['submissions']:
        assert applied['ability_id']==raw['skillid'] and applied['ability_type']==3000
        for f,k in (('param1','normal_delta'),('param2','skill_delta'),('param6','support_time'),('param8','critical_damage_delta')):
            assert applied[k]==struct.unpack('<f',struct.pack('<f',raw.get(f,0)))[0]
for f in ('param1','param2','param6','param8'):
    assert {r['raw'][f] for r in sympathy_records if f in r['raw']} <= {c['source_fields'][f]['raw_value'] for c in sympathy_applications if c['source_fields'][f]['present']}
flag_cases=[c for c in sympathy_checks['checks'] if c['name'].startswith('skill_start_sympathy_flags_')]
assert len(flag_cases)==8 and all(c['dispatch_count']==int(c['sympathy'] or c['k_sympathy'] or c['s_sympathy']) for c in flag_cases)
assert sympathy_trace['default_support3_bounds']=={'normal':[.5,2],'skill':[.5,2],'critical_damage':[-1.5,1]}
assert len([c for c in sympathy_checks['checks'] if c['name'].startswith('qualification_')])==30
assert {c['remaining'] for c in sympathy_checks['checks'] if c['name'].startswith('time_')}=={44.75,59.75,0}
assert sympathy_trace['weapon_mask']['value']==0x7fc00000 and sympathy_trace['weapon_mask']['source_intersection_count']==0
assert sympathy_trace['weapon_mask']['field']['name']=='sAttackFlagWeaponMask' and sympathy_trace['weapon_mask']['field']['offset']=='0x20'
assert bytes.fromhex(sympathy_trace['weapon_mask']['literal_hex'])==struct.pack('<Q',0x7fc00000)
assert all(((r['raw'].get('flag0_0',r['raw'].get('flag',0))|(r['raw'].get('flag0_1',0)<<32))&0x7fc00000)==0 for r in sympathy_records)
check('86_3000_native_checks_sympathy_flags_qualification_weapon_mask_recipient_route_category_and_time',True)

sympathy_views=[v for v in ordinary_views if v['effect_type']==3000]
assert len(sympathy_views)==1098 and Counter(v['field_path'] for v in sympathy_views)=={'/param1':303,'/param2':303,'/param6':348,'/param8':144}
assert len({v['record_key'] for v in sympathy_views})==348
for r in sympathy_records:
    loc=r['location'];fragment=skill_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert json.loads(fragment)==r['raw'] and hashlib.sha256(fragment).hexdigest()==loc['raw_record_sha256']
    present={v['field_path'] for v in sympathy_views if v['record_key']==r['record_key']}
    assert present=={'/'+f for f in ('param1','param2','param6','param8') if f in r['raw']}
for v in sympathy_views:
    r=records[v['record_key']];raw=r['raw'];ctx=v['trigger_context']
    assert ctx['support_category']['name']=='Support3' and ctx['support_category']['offset']=='0x238'
    assert ctx['triggering_job_filter']['raw_value']==raw.get('iParam0') and '发动' in ctx['triggering_job_filter']['subject']
    assert ctx['triggering_home_filter']['raw_value']==raw.get('param9') and '发动' in ctx['triggering_home_filter']['subject']
    assert ctx['recipient_selector']['raw_value']==raw.get('param0')
    assert ctx['weapon_filter']['mask']==0x7fc00000 and ctx['weapon_filter']['source_intersection']==0
    assert ctx['missing_requested_fields']==[f for f in ('param1','param2','param6','param8') if f not in raw]
    for f,ref in ctx['source_field_refs'].items():
        assert ref['record_key']==r['record_key'] and ref['present']==(f in raw) and ref['raw_value']==raw.get(f)
        assert ref['source_sha256']==r['source_sha256'] and ref['json_pointer']==r['location']['json_pointer']+'/'+f
    assert v['correspondence_status']=='SCOPED_SUPPORT3000_MAPPING_CONFIRMED' and v['raw_value_status']=='RAW_FOUND'
for path,count in (('/param1',303),('/param2',303),('/param6',348),('/param8',144)):
    rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',3000,path))
    assert rule['occurrences']==count and '../ordinary_effects/ability3000/trace.json' in rule['evidence']
check('382_3000_source_records_1098_present_fields_four_rules_context_and_no_zero_filling',True)

assert drain_trace['source_records']==drain_records and len(drain_records)==133
assert drain_trace['source_sha256']==sha(SOURCE) and drain_trace['script_sha256']==sha('scripts/ordinary_99_probe.py')
assert drain_trace['native_sha256']==drain_checks['native_sha256']==ordinary_trace['native_sha256']
assert drain_trace['metadata_sha256']==ordinary_trace['metadata_sha256']
assert all(sha(p)==h for p,h in drain_trace['fixture_scripts'].items())
assert all(sha(p['path'])==p['sha256'] for p in drain_trace['reused_proofs'])
assert drain_trace['ability_enum']['name']=='PowerDrain' and drain_trace['ability_enum']['default']['value']==99
assert [(e['name'],e['default']['value']) for e in drain_trace['damage_type_enum']]==[('Normal',0),('Skill',1),('Critical',2)]
assert drain_trace['cached_type_field']['name']=='_PowerDrain' and drain_trace['cached_type_field']['offset']=='0xa6'
assert Counter(r['raw']['param0'] for r in drain_records)=={-1:2,10:6,20:3,30:103,60:19}
assert drain_trace['probability_field_presence']=={'param1':100,'param2':130,'param3':100}
assert len(drain_checks['checks'])==drain_trace['native_check_count']==192 and all(c['passed'] for c in drain_checks['checks'])
by_drain_id={r['raw']['skillid']:r for r in drain_records}
drain_handlers=[c for c in drain_checks['checks'] if c['name'].startswith('handler_')]
assert len(drain_handlers)==169 and len(drain_trace['sample_ids'])==27
assert {c['skill_id'] for c in drain_handlers}==set(drain_trace['sample_ids'])
assert {c['chain_fixture'] for c in drain_handlers}=={.5,1,2}
for c in drain_handlers:
    raw=by_drain_id[c['skill_id']]['raw'];field={0:'param1',1:'param3',2:'param2'}.get(c['damage_type'])
    threshold=c['threshold_fixture_override'] if c['threshold_fixture_override'] is not None else raw.get(field,0)
    want=c['installed_fixture'] and threshold>0 and c['random_fixture']<=threshold
    assert c['trigger_source_field']==field and c['source_threshold']==raw.get(field)
    assert len(c['submissions'])==2*int(want) and c['target_recipient_count']==int(want)
    assert c['draw_count']==int(c['installed_fixture'] and threshold>0)
    for f,ref in c['source_fields'].items():assert ref['present']==(f in raw) and ref['raw_value']==raw.get(f)
    for applied,attack_field,incoming_field in zip(c['submissions'],('param4','param7'),('param6','param9')):
        assert applied['ability_id']==raw['skillid'] and applied['ability_type']==99 and applied['multi_check']
        assert applied['support_time']==struct.unpack('<f',struct.pack('<f',raw['param0']))[0]
        assert applied['attack_delta']==struct.unpack('<f',struct.pack('<f',raw.get(attack_field,0)))[0]
        assert applied['incoming_delta']==struct.unpack('<f',struct.pack('<f',raw.get(incoming_field,0)))[0]
for f in ('param0','param7','param9'):
    assert {r['raw'][f] for r in drain_records if f in r['raw']} <= {c['source_fields'][f]['raw_value'] for c in drain_handlers if c['source_fields'][f]['present']}
time_stores=[c for c in drain_checks['checks'] if c['name'].startswith('time_store_')]
time_updates=[c for c in drain_checks['checks'] if c['name'].startswith('time_update_')]
assert len(time_stores)==5 and all(c['source_time']==c['support_time']==c['support_full_time'] for c in time_stores)
assert len(time_updates)==10
assert all(c['remaining']==-1 and not c['removed'] for c in time_updates if c['source_time']==-1)
assert all(c['removed']==(c['game_delta_fixture']>=c['source_time']) for c in time_updates if c['source_time']>0)
assert len([c for c in drain_checks['checks'] if c['name'].startswith('outer_returned_damage')])==4
assert drain_trace['default_support2_bounds']=={'normal':[.5,2],'skill':[.5,2],'incoming':[.5,2]}
check('192_99_native_checks_damage_gate_type_eligibility_trigger_routes_target_support_and_minus_one_timer',True)

drain_views=[v for v in ordinary_views if v['effect_type']==99 and v['field_path'] in ('/param7','/param9','/param0')]
assert len(drain_views)==382 and Counter(v['field_path'] for v in drain_views)=={'/param7':126,'/param9':123,'/param0':133}
assert len({v['record_key'] for v in drain_views})==133
for r in drain_records:
    loc=r['location'];fragment=skill_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert json.loads(fragment)==r['raw'] and hashlib.sha256(fragment).hexdigest()==loc['raw_record_sha256']
    assert {v['field_path'] for v in drain_views if v['record_key']==r['record_key']}=={'/'+f for f in ('param7','param9','param0') if f in r['raw']}
for v in drain_views:
    r=records[v['record_key']];raw=r['raw'];ctx=v['trigger_context']
    assert ctx['support_category']['name']=='Support2' and ctx['support_category']['offset']=='0x230' and ctx['support_category']['multi_check']
    assert ctx['positive_damage_gate']['minimum']==1 and ctx['target']['subject']=='本次Attack传入的单个目标'
    assert [(p['damage_type'],p['field']) for p in ctx['probability_routes']]==[(0,'/param1'),(1,'/param3'),(2,'/param2')]
    for route in ctx['probability_routes']:
        f=route['field'][1:];assert route['present']==(f in raw) and route['raw_value']==raw.get(f)
    assert ctx['missing_requested_fields']==[f for f in ('param7','param9','param0') if f not in raw]
    assert ctx['duration']['raw_value']==raw['param0'] and ctx['duration']['status']==('POSITIVE_GAME_SECONDS' if raw['param0']>0 else 'SOURCE_MINUS_ONE_NO_POSITIVE_COUNTDOWN')
    for f,ref in ctx['source_field_refs'].items():
        assert ref['present']==(f in raw) and ref['raw_value']==raw.get(f) and ref['record_key']==r['record_key']
        assert ref['source_sha256']==r['source_sha256'] and ref['json_pointer']==r['location']['json_pointer']+'/'+f
    assert v['raw_value_status']=='RAW_FOUND' and v['correspondence_status']=='SCOPED_POWERDRAIN_TARGET_MAPPING_CONFIRMED'
for path,count in (('/param7',126),('/param9',123),('/param0',133)):
    rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',99,path))
    assert rule['occurrences']==count and '../ordinary_effects/ability99/trace.json' in rule['evidence']
    if path=='/param0':assert '以下旧来源备注仅限skilllist/43023616' in rule['limits']
assert len([v for v in ordinary_views if v['effect_type']==99 and v['field_path']=='/param8'])==1
check('133_99_source_records_382_present_fields_three_rules_source_bytes_context_and_existing_move_scope',True)

assert stage_trace['source_records']==stage_records and len(stage_records)==64
assert stage_trace['source_sha256']==sha(SOURCE) and stage_trace['script_sha256']==sha('scripts/ordinary_7_probe.py')
assert stage_trace['native_sha256']==stage_checks['native_sha256']==ordinary_trace['native_sha256']
assert stage_trace['metadata_sha256']==ordinary_trace['metadata_sha256']
assert all(sha(p)==h for p,h in stage_trace['fixture_scripts'].items())
assert stage_trace['reused_proof']['sha256']==sha(stage_trace['reused_proof']['path'])
assert stage_trace['ability_enum']['name']=='TargetStage' and stage_trace['ability_enum']['default']['value']==7
assert stage_trace['eligibility_jump']['target']=='0x1112fd8'
assert len(stage_checks['checks'])==stage_trace['native_check_count']==1390 and all(c['passed'] for c in stage_checks['checks'])
background_records=[r for r in records.values() if r['table']=='battle_bg']
assert stage_trace['background_source_records']==background_records and len(background_records)==99
by_bg_id={r['raw']['id']:r for r in background_records}
stage_conditions=[c for c in stage_checks['checks'] if c['name'].startswith('condition_')]
assert len(stage_conditions)==13*99
for c in stage_conditions:
    code=c['param0'];raw=by_bg_id[c['background_id']]['raw'];mask=sum(1<<i for i in set((code%100,(code//100)%100,(code//10000)%100)))
    assert c['background_flag']==raw['flag'] and c['matches']==bool(mask&raw['flag']&0xfffffffe)
for code,ids in stage_trace['code_background_matches'].items():
    assert ids==[c['background_id'] for c in stage_conditions if c['param0']==int(code) and c['matches']]
stage_effect_checks=[c for c in stage_checks['checks'] if c['name'].startswith('effect_')]
assert len(stage_effect_checks)==92 and len(stage_trace['sample_ids'])==23
by_stage_id={r['raw']['skillid']:r for r in stage_records}
for c in stage_effect_checks:
    raw=by_stage_id[c['skill_id']]['raw'];assert c['raw_value']==raw[c['field']] and c['param0']==raw['param0']
    assert c['result']==c['expected_float32']
    expected=struct.unpack('<f',struct.pack('<f',struct.unpack('<f',struct.pack('<f',1.2))[0]*struct.unpack('<f',struct.pack('<f',raw[c['field']] if c['qualifies'] else 1))[0]))[0]
    assert c['result']==expected
for field in ('param0','param1','param3'):
    assert {r['raw'][field] for r in stage_records} <= {by_stage_id[sid]['raw'][field] for sid in stage_trace['sample_ids']}
assert {c['background_id']:c['code_matches'] for c in stage_checks['checks'] if c['name'].startswith('102071_')}=={4:True,2:False}
assert len([c for c in stage_checks['checks'] if c['name'].startswith('current_stage_')])==2
assert any(c.get('synthetic_background_flag')==1 and not c['matches'] for c in stage_checks['checks'])
check('1390_7_native_checks_current_bg_encoding_eligibility_self_multiply_extremes_and_text_conflict',True)

stage_views=[v for v in ordinary_views if v['effect_type']==7 and v['field_path'] in ('/param0','/param1','/param3')]
assert len(stage_views)==192 and Counter(v['field_path'] for v in stage_views)=={'/param0':64,'/param1':64,'/param3':64}
for r in stage_records+background_records:
    loc=r['location'];source_bytes=skill_bytes if r['table']=='skilllist' else Path('output/cache_full_20261015_v3/decoded/battleinfo.data5.json.raw').read_bytes()
    fragment=source_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert json.loads(fragment)==r['raw'] and hashlib.sha256(fragment).hexdigest()==loc['raw_record_sha256']
for v in stage_views:
    r=records[v['record_key']];raw=r['raw'];ctx=v['trigger_context'];condition=ctx['terrain_condition'];code=raw['param0']
    assert ctx['target']['subject']=='持有该已选中能力的自身'
    assert condition['raw_value']==code and condition['base100_groups_low_to_high']==[code%100,(code//100)%100,(code//10000)%100]
    assert condition['terrain_indices_low_to_high']==[x for x in condition['base100_groups_low_to_high'] if x]
    assert condition['mask_without_bit0']==sum(1<<x for x in set(condition['terrain_indices_low_to_high']))
    assert [b['id'] for b in condition['matching_backgrounds']]==stage_trace['code_background_matches'][str(code)]
    for b in condition['matching_backgrounds']:
        bg=by_bg_id[b['id']];assert b['flag']==bg['raw']['flag'] and b['bg_name_ja']==bg['raw']['bg_name']
        assert all(b[f]==bg[f] for f in ('record_key','source_sha256','original_file','location'))
    assert condition['matching_background_names_ja']==list(dict.fromkeys(b['bg_name_ja'] for b in condition['matching_backgrounds']))
    assert v['raw_value_status']=='RAW_FOUND' and v['correspondence_status']=='SCOPED_TARGETSTAGE_SELF_MAPPING_CONFIRMED'
    for field,ref in ctx['source_field_refs'].items():
        assert ref['present'] and ref['raw_value']==raw[field] and ref['record_key']==r['record_key']
        assert ref['source_sha256']==r['source_sha256'] and ref['json_pointer']==r['location']['json_pointer']+'/'+field
for path in ('/param0','/param1','/param3'):
    rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',7,path))
    assert rule['occurrences']==64 and '../ordinary_effects/ability7/trace.json' in rule['evidence']
check('64_7_records_192_present_fields_99_bg_sources_three_rules_current_terrain_and_unclamped_source_values',True)

assert stage_all_trace['source_records']==stage_all_records and len(stage_all_records)==37
assert stage_all_trace['source_sha256']==sha(SOURCE) and stage_all_trace['script_sha256']==sha('scripts/ordinary_1008_probe.py')
assert stage_all_trace['native_sha256']==stage_all_checks['native_sha256']==stage_trace['native_sha256']
assert stage_all_trace['metadata_sha256']==stage_trace['metadata_sha256']
assert all(sha(p)==h for p,h in stage_all_trace['fixture_scripts'].items())
assert stage_all_trace['reused_proof']['sha256']==sha(stage_all_trace['reused_proof']['path'])
assert stage_all_trace['ability_enum']['name']=='TargetStageAll' and stage_all_trace['ability_enum']['default']['value']==1008
assert stage_all_trace['background_source_records']==background_records
assert stage_all_trace['player_candidate_field']['name']=='_aChara_Player' and stage_all_trace['player_candidate_field']['offset']=='0x70'
assert len(stage_all_checks['checks'])==stage_all_trace['native_check_count']==389 and all(c['passed'] for c in stage_all_checks['checks'])
assert stage_all_trace['new_param0_codes']==[3,607]
all_stage_codes={r['raw']['param0'] for r in stage_all_records}
assert set(stage_all_trace['param0_values'])==all_stage_codes and len(all_stage_codes)==9
new_conditions=[c for c in stage_all_checks['checks'] if c['name'].startswith('new_condition_')]
assert len(new_conditions)==198
for c in new_conditions:
    raw=by_bg_id[c['background_id']]['raw'];code=c['param0']
    assert c['background_flag']==raw['flag']
    assert c['matches']==bool(sum(1<<i for i in set((code%100,(code//100)%100,(code//10000)%100)))&raw['flag']&0xfffffffe)
for code,ids in stage_all_trace['code_background_matches'].items():
    expected=[r['raw']['id'] for r in background_records if sum(1<<i for i in set((int(code)%100,(int(code)//100)%100,(int(code)//10000)%100)))&r['raw']['flag']&0xfffffffe]
    assert ids==expected
    if int(code) not in (3,607):assert ids==stage_trace['code_background_matches'][code]
by_stage_all_id={r['raw']['skillid']:r for r in stage_all_records}
all_effect_checks=[c for c in stage_all_checks['checks'] if c['name'].startswith('effect_')]
assert len(all_effect_checks)==180 and {c['skill_id'] for c in all_effect_checks}==set(by_stage_all_id)
for c in all_effect_checks:
    raw=by_stage_all_id[c['skill_id']]['raw'];assert c['raw_value']==raw[c['field']] and c['param0']==raw['param0']
    assert c['result']==c['expected_float32']
    expected=struct.unpack('<f',struct.pack('<f',struct.unpack('<f',struct.pack('<f',1.2))[0]*struct.unpack('<f',struct.pack('<f',raw[c['field']] if c['qualifies'] else 1))[0]))[0]
    assert c['result']==expected and c['real_eligibility_calls']==int(c['installed_fixture'])
    assert any(r['field']==c['field'] for r in c['reads'])==c['qualifies']
assert {(c['provider_is_receiver'],c['receiver_job_fixture']) for c in all_effect_checks if c['skill_id']==43023606 and c['qualifies']} >= {(same,job) for same in (True,False) for job in range(6)}
assert len([c for c in stage_all_checks['checks'] if c['name'].startswith('provider_')])==8
assert {(c['hp_fixture'],c['active_fixture']):c['route'] for c in stage_all_checks['checks'] if c['name'].startswith('provider_')}=={(100,1):'ACTIVE',(0,1):'DEAD',(100,0):'BACKUP',(0,0):'DEAD'}
assert {c['kind']:c['selected_offset'] for c in stage_all_checks['checks'] if c['name'].startswith('candidate_list_')}=={0:'0x70',1:'0x78',2:'0x68'}
check('389_1008_native_checks_type_filter_eligibility_all_source_values_self_other_job_terrain_and_provider_routes',True)
stage_all_views=[v for v in ordinary_views if v['effect_type']==1008 and v['field_path'] in ('/param0','/param1','/param3')]
assert len(stage_all_views)==111 and Counter(v['field_path'] for v in stage_all_views)=={'/param0':37,'/param1':37,'/param3':37}
for r in stage_all_records:
    loc=r['location'];fragment=skill_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert json.loads(fragment)==r['raw'] and hashlib.sha256(fragment).hexdigest()==loc['raw_record_sha256']
for v in stage_all_views:
    r=records[v['record_key']];raw=r['raw'];ctx=v['trigger_context'];condition=ctx['terrain_condition'];code=raw['param0']
    assert ctx['target']['self_included'] and not ctx['target']['recipient_job_filter'] and not ctx['target']['distance_filter']
    assert ctx['target']['subject']!='持有该已选中能力的自身' and '_aChara_Player' in ctx['target']['provider_candidate_list']
    assert condition['raw_value']==code and condition['base100_groups_low_to_high']==[code%100,(code//100)%100,(code//10000)%100]
    assert [b['id'] for b in condition['matching_backgrounds']]==stage_all_trace['code_background_matches'][str(code)]
    for b in condition['matching_backgrounds']:
        bg=by_bg_id[b['id']];assert b['flag']==bg['raw']['flag'] and b['bg_name_ja']==bg['raw']['bg_name']
        assert all(b[f]==bg[f] for f in ('record_key','source_sha256','original_file','location'))
    assert v['raw_value_status']=='RAW_FOUND' and v['correspondence_status']=='SCOPED_TARGETSTAGEALL_PLAYER_RECIPIENT_MAPPING_CONFIRMED'
    for field,ref in ctx['source_field_refs'].items():
        assert ref['present'] and ref['raw_value']==raw[field] and ref['record_key']==r['record_key']
        assert ref['source_sha256']==r['source_sha256'] and ref['json_pointer']==r['location']['json_pointer']+'/'+field
for path in ('/param0','/param1','/param3'):
    rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',1008,path))
    assert rule['occurrences']==37 and '../ordinary_effects/ability1008/trace.json' in rule['evidence']
check('37_1008_records_111_present_fields_source_bytes_scoped_party_context_and_three_rules',True)

from query_effect_dictionary import lookup
for sid,code,attack,guard in ((43023606,4,12.5,12.5),(102070,4,5,0),(42011507,607,10,10),(42052306,1320,15,15)):
    result=lookup('skilllist',sid)['results'][0]
    assert result['target_conditions']['/param0']['raw_value']==code
    assert result['trigger_context']['target']['self_included']
    explained={v['field_path']:v for v in result['explained_fields']}
    assert abs(explained['/param1']['converted_value']-attack)<1e-10 and abs(explained['/param3']['converted_value']-guard)<1e-10
    assert '/param2' not in explained or sid==43023606
assert lookup('bossskill',43023606)['results'][0]['record']['raw'].get('ability')!=1008
check('1008_lookup_same_terrain_distinct_scope_neutral_defence_composite_codes_and_boss_namespace',True)
attack_lookup=lookup('skilllist',40129301)
assert attack_lookup['matches']==1 and next(v for v in attack_lookup['results'][0]['explained_fields'] if v['field_path']=='/param1')['converted_value']==1750
defence_lookup=lookup('skilllist',41223601)
assert next(v for v in defence_lookup['results'][0]['explained_fields'] if v['field_path']=='/param3')['converted_value']==60
name_lookup=lookup('skilllist',name='祝福を受けし者')
assert name_lookup['matches']>1 and len({r['record']['record_key'] for r in name_lookup['results']})==name_lookup['matches']
ordinary_lookup=lookup('skilllist',43023614);boss_lookup=lookup('bossskill',43023614)
assert ordinary_lookup['results'][0]['record']['raw']['ability']==2012 and boss_lookup['results'][0]['record']['raw']['skillid0']==16
assert all(v['table']=='skilllist' and v['effect_type']!=1095 for v in ordinary_lookup['results'][0]['explained_fields'])
unknown_lookup=lookup('skilllist',43023603)
assert unknown_lookup['results'][0]['unexplained_present_fields']['str0']=='43023603'
assert unknown_lookup['results'][0]['status']=='RAW_FOUND_NO_SCOPED_EXPLANATION'
check('lookup_ID_name_multiple_records_Boss_namespace_and_unknown_fields_preserved',True)
job_lookup=lookup('skilllist',40768606)['results'][0]
assert job_lookup['target_conditions']['/param0']['raw_value']==1
assert job_lookup['target_conditions']['/iParam0']['raw_value']==1 and job_lookup['target_conditions']['/iParam0']['converted_value']==[0]
assert set(job_lookup['target_conditions'])=={'/param0','/iParam0'}
assert 'param0' not in job_lookup['unexplained_present_fields'] and 'iParam0' not in job_lookup['unexplained_present_fields']
assert 'param2' in job_lookup['unexplained_present_fields'] and 'flag' in job_lookup['unexplained_present_fields']
all_job_lookup=lookup('skilllist',43023605)['results'][0]
assert all_job_lookup['target_conditions']['/iParam0']['converted_value']==[0,1,2,3,4]
assert not attack_lookup['results'][0]['target_conditions'] and not boss_lookup['results'][0]['target_conditions']
check('query_1017_target_conditions_visible_warrior_mask_all_five_mask_and_unknowns_remain',True)
fraction_lookup=lookup('skilllist',40431614)['results'][0]
assert {v['field_path']:v['converted_value'] for v in fraction_lookup['explained_fields']}=={'/param0':22.5,'/param4':5,'/param5':5}
assert fraction_lookup['trigger_context']['target_selector']['enum_name']=='pGROUP_ALL'
assert not fraction_lookup['target_conditions']
damage_only=lookup('skilllist',40126713)['results'][0]
assert {v['field_path'] for v in damage_only['explained_fields']}=={'/param0','/param5'}
assert damage_only['trigger_context']['missing_requested_fields']==['param4']
assert damage_only['trigger_context']['source_field_refs']['param4']['raw_value'] is None
assert damage_only['trigger_context']['target_selector']['enum_name']=='MYSELF'
assert 'param1' in damage_only['unexplained_present_fields'] and 'param4' not in damage_only['record']['raw']
assert not job_lookup['trigger_context'] and not boss_lookup['results'][0]['trigger_context']
check('query_2012_duration_deltas_action_context_missing_probability_and_other_namespaces_preserved',True)
sympathy_lookup=lookup('skilllist',43023611)['results'][0]
assert {v['field_path']:v['converted_value'] for v in sympathy_lookup['explained_fields']}=={'/param1':10,'/param2':10,'/param6':45,'/param8':10}
assert sympathy_lookup['trigger_context']['support_category']['name']=='Support3' and not sympathy_lookup['target_conditions']
sympathy_raw_only=lookup('skilllist',40121710)['results'][0]
assert sympathy_raw_only['status']=='RAW_FOUND_CONTEXT_ONLY' and not sympathy_raw_only['explained_fields']
assert sympathy_raw_only['trigger_context']['missing_requested_fields']==['param1','param2','param6','param8']
assert 'param5' in sympathy_raw_only['unexplained_present_fields']
sympathy_job=lookup('skilllist',40124411)['results'][0]['trigger_context']
assert sympathy_job['triggering_job_filter']['raw_value']==16 and sympathy_job['triggering_job_filter']['job_names_zh']==['骑士']
assert 'param0' in sympathy_job['source_field_refs']
sympathy_boss=lookup('bossskill',43023611)['results'][0]
assert sympathy_boss['record']['raw']['skillid0']==112 and not sympathy_boss['trigger_context']
check('query_3000_four_values_context_only_absent_record_trigger_job_and_Boss_namespace',True)
drain_lookup=lookup('skilllist',43023616)['results'][0]
assert {v['field_path']:v['converted_value'] for v in drain_lookup['explained_fields'] if v['field_path'] in ('/param7','/param9','/param0')}=={'/param7':-30,'/param9':30,'/param0':30}
assert drain_lookup['trigger_context']['support_category']['name']=='Support2' and not drain_lookup['target_conditions']
minus_one=lookup('skilllist',42080504)['results'][0]
assert minus_one['trigger_context']['duration']['status']=='SOURCE_MINUS_ONE_NO_POSITIVE_COUNTDOWN'
assert next(v for v in minus_one['explained_fields'] if v['field_path']=='/param0')['converted_value']==-1
assert [p['enum_name'] for p in minus_one['trigger_context']['probability_routes'] if p['present']]==['Critical']
no_attack_defence=lookup('skilllist',127008)['results'][0]
assert {v['field_path'] for v in no_attack_defence['explained_fields']}=={'/param0'}
assert no_attack_defence['trigger_context']['missing_requested_fields']==['param7','param9']
assert 'param8' in no_attack_defence['unexplained_present_fields'] and 'param7' not in no_attack_defence['record']['raw']
enemy_use=lookup('skilllist',47000715)['results'][0]
assert 'エネミー用' in enemy_use['record']['raw']['name'] and enemy_use['record']['table']=='skilllist'
assert [p['enum_name'] for p in enemy_use['trigger_context']['probability_routes'] if p['present']]==['Critical']
drain_boss=lookup('bossskill',40008903)['results'][0]
assert drain_boss['record']['raw']['skillid0']==74 and not drain_boss['trigger_context']
assert lookup('skilllist',40008903)['results'][0]['record']['raw']['ability']==99
check('query_99_attack_incoming_time_minus_one_missing_fields_enemy_use_and_Boss_namespaces',True)
stage_lookup=lookup('skilllist',43023607)['results'][0]
assert stage_lookup['target_conditions']['/param0']['raw_value']==4 and stage_lookup['target_conditions']['/param0']['converted_value']==[4]
assert stage_lookup['trigger_context']['terrain_condition']['mask_without_bit0']==16
assert '砂漠' in stage_lookup['trigger_context']['terrain_condition']['matching_background_names_ja']
assert abs(next(v for v in stage_lookup['explained_fields'] if v['field_path']=='/param1')['converted_value']-5)<1e-10
stage_conflict=lookup('skilllist',102071)['results'][0]
assert '森林' in stage_conflict['record']['raw']['text'] and stage_conflict['trigger_context']['description_conflict']['raw_preserved']
assert stage_conflict['trigger_context']['description_conflict']['status']=='SOURCE_NAME_TEXT_CONFLICT_CODE_MATCHES_DESERT'
extreme_stage=lookup('skilllist',47000707)['results'][0]
extreme=next(v for v in extreme_stage['explained_fields'] if v['field_path']=='/param3')
assert extreme['raw_value']==250 and extreme['converted_value']==-24900 and '增加24900%' in extreme['display_value']
multi_stage=lookup('skilllist',47000830)['results'][0]
assert multi_stage['target_conditions']['/param0']['raw_value']==1320 and multi_stage['target_conditions']['/param0']['converted_value']==[20,13]
stage_boss=lookup('bossskill',43023607)['results'][0]
assert stage_boss['record']['raw']['skillid0']==112 and not stage_boss['trigger_context']
check('query_7_desert_id_vs_flag_102071_source_conflict_250_multiplier_OR_encoding_and_Boss_namespace',True)
apk=next(r for r in power_trace['source_records'] if r['layer']=='APK_AB')
blob=Path(apk['original_file']).read_bytes();loc=apk['location'];record_bytes=blob[loc['byte_begin']:loc['byte_end_exclusive']]
check('APK106001_per_ID_fallback_raw_bytes_and_source_preserved',sha(apk['original_file'])==apk['source_sha256'] and json.loads(record_bytes)==apk['raw'] and hashlib.sha256(record_bytes).hexdigest()==loc['raw_record_sha256'] and apk['raw']['param0']==1.149999976158142)

for stem in ('comparison', 'field_dictionary', 'verified_parameter_views','description_effects'):
    js = load(OUT/(stem+'.json'))
    with (OUT/(stem+'.csv')).open(encoding='utf-8-sig', newline='') as f:
        cs = list(csv.DictReader(f))
    assert len(js) == len(cs)
    for jr, cr in zip(js, cs):
        for key, value in jr.items():
            expected_value = json.dumps(value, ensure_ascii=False) if isinstance(value,(dict,list)) else '' if value is None else str(value)
            assert cr[key] == expected_value, (stem, key)
check('four_csv_json_pairs_exact_including_nested_sources', True)
assert len(effects)==101 and len({r['effect_id'] for r in effects})==101
assert {r['group'] for r in effects}=={'必杀','能力一','能力二','Class','Extra','Leader','共鸣','羁绊'}
for effect in effects:
    desc=records[effect['description_record_key']]['raw']
    if effect['description_field']=='/extra_abilities/*/text':assert effect['description_ja']==[x['text'] for x in desc['extra_abilities']]
    else:assert effect['description_ja']==desc[effect['description_field'][1:]]
    assert (effect['answer_status']=='CONFIRMED_NUMERIC')==(effect['readable_value'] is not None)
    for ref in effect['field_refs']:
        r=records[ref['record_key']];field=ref['field_path'][1:]
        assert ref['present']==(field in r['raw']) and ref['raw_value']==r['raw'].get(field)
        assert ref['table']==r['table'] and ref['location']==r['location'] and ref['source_sha256']==r['source_sha256']
primary=[r for r in effects if r['effect_scope']=='attack_defence'];other=[r for r in effects if r['effect_scope']=='other_numeric']
assert len(primary)==40 and all(r['readable_value'] is not None for r in primary) and len(other)==61
check('101_atomic_effects_all_eight_groups_sources_and_separate_progress',True,answered=sum(r['readable_value'] is not None for r in effects),primary_answered=40,other_answered=sum(r['readable_value'] is not None for r in other))
assert all(r['readable_value'] is not None and r['unit'] and r['card_name_ja']=='《Y.G.1009》竜の眷属 チーカ' for r in effects)
assert all(r['description_table']==records[r['description_record_key']]['table'] for r in effects)
assert next(r for r in effects if r['effect_id']=='other_sp_normal_cost')['calculation_status']=='RAW_CONFIGURATION_VALUE_CONFIRMED'
assert next(r for r in effects if r['effect_id']=='other_a1_barrier_count')['calculation_status']=='ORIGINAL_TEXT_AND_FIELD_NUMBER_CONFIRMED'
assert sum(r['calculation_status']=='ORIGINAL_TEXT_NUMBER_CONFIRMED' for r in effects)==10
check('101_effects_units_identity_and_explicit_number_basis',True)
by_effect={r['effect_id']:r for r in effects}
assert '+0.875' in by_effect['other_a1_critical_damage']['readable_value']
assert '+2' in by_effect['other_class_param6']['readable_value']
assert '+40' in by_effect['other_class_param5']['readable_value'] and by_effect['other_class_param5']['screenshot_value']=='20%'
assert '10%' in by_effect['other_a2_chain_probability']['readable_value'] and by_effect['other_a2_chain_probability']['screenshot_value']=='20%'
assert any(f['record_id']==43023617 for f in by_effect['other_a2_chain_probability']['field_refs'])
check('critical_baselines_Class_probability_difference_and_correct_Chain_candidate',True)
source_diff=load(OUT/'difference_sources/trace.json')
assert source_diff['source_sha256']==sha(SOURCE) and source_diff['script_sha256']==sha('scripts/chica_difference_sources.py')
old_source=source_diff['older_source'];old_bytes=Path(old_source['path']).read_bytes()
assert sha(old_source['path'])==old_source['sha256']
assert sha(old_source['export_manifest'])==old_source['export_manifest_sha256']
assert next(s for s in load(old_source['export_manifest'])['sources'] if s['input_file']==old_source['path'])['sha256']==old_source['sha256']
assert len(source_diff['checks'])==4 and all(c['passed'] for c in source_diff['checks'])
assert source_diff['apk_source']['sha256']==sha(source_diff['apk_source']['path'])
old_rows=json.loads(old_bytes)['skilllist'];apk_rows=load(source_diff['apk_source']['path'])['skilllist']
for case in source_diff['cases']:
    assert case['current_record']==records[case['current_record']['record_key']]
    old=case['older_record'];loc=old['location'];fragment=old_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert old['source_sha256']==old_source['sha256'] and json.loads(fragment)==old['raw']==old_rows[loc['ordinal_zero_based']]
    assert hashlib.sha256(fragment).hexdigest()==loc['raw_record_sha256']
    assert loc['json_pointer']=='/skilllist/'+str(loc['ordinal_zero_based'])
    assert [r for r in apk_rows if r.get('skillid')==case['record_id']]==[]
    for field in case['fields']:
        key=field['field_path'][1:]
        assert field['current_raw_value']==case['current_record']['raw'][key]==field['older_raw_value']==old['raw'][key]
    for key in case['effect_ids']:
        assert by_effect[key]['screenshot_difference']['older_record']==old
        assert by_effect[key]['screenshot_difference']['discrepancy_status']=='RESOLVED_BY_SOURCE_PRIORITY'
    for field in case['fields']:
        view=next(v for v in views if v['table']==case['table'] and v['record_id']==case['record_id'] and v['field_path']==field['field_path'])
        assert 'difference_sources/trace.json' in view['evidence']
assert len({r['screenshot_difference']['case_id'] for r in effects if r['screenshot_difference']})==5
observations=source_diff['external_observations']
assert observations['sha256']==sha(observations['path']) and observations['content']==load(observations['path'])
assert observations['content']['conclusion']=='NO_NUMERIC_ARBITRATION_FOR_FIVE_SCREENSHOT_DIFFERENCES'
assert {f['case_id'] for s in observations['content']['sources'] for f in s['findings']}=={'barrier_guard','class_critical','class_lifesteal','chain_mana','enemy_duration'}
assert all(f['annotated_numeric_value'] is None for s in observations['content']['sources'] for f in s['findings'])
assert all(len(r['screenshot_difference']['external_reference_checks'])==1 for r in effects if r['screenshot_difference'])
assert all(r['screenshot_difference']['number_origin']=='EXTERNAL_REFERENCE_NUMBER_NOT_LITERAL_GAME_DESCRIPTION'
           and r['screenshot_difference']['game_description_check']['literal_present'] is False
           and r['screenshot_difference']['game_description_check']['record_key']==r['description_record_key']
           for r in effects if r['screenshot_difference'])
check('four_discrepancies_seven_fields_same_older_snapshot_bytes_and_original_annotations_preserved',True)

# Adoption is a user decision over existing proven rules, not a new native result.
policy=load(OUT/'difference_sources/adoption_policy.json')
assert policy['provenance']=='USER_INSTRUCTION' and policy['instruction_quote']=='如果有冲突，以解包数据和代码数据为准。'
expected_adoptions={
    'barrier_guard':('bossskill',43023614,16,{'/skillparam1':(2,None)},None,5),
    'class_critical':('skilllist',65000001,1095,{'/param5':(.4,40)},40,20),
    'class_lifesteal':('skilllist',65000003,21,{'/param1':(.25,25)},25,20),
    'chain_mana':('skilllist',43023617,1106,{f'/param{i}':(.1,10) for i in range(1,5)},10,20),
    'enemy_duration':('skilllist',43023616,99,{'/param0':(30,30)},30,45),
}
assert len(policy['cases'])==5 and {c['case_id'] for c in policy['cases']}==set(expected_adoptions)
resolved_effects=[r for r in effects if r['screenshot_difference']]
assert len(resolved_effects)==7
for case in policy['cases']:
    table,sid,kind,expected_fields,adopted,shot=expected_adoptions[case['case_id']]
    assert (case['table'],case['record_id'],case['effect_type'])==(table,sid,kind)
    assert {f['field_path']:(f['raw_value'],f['converted_value']) for f in case['fields']}==expected_fields
    for key in case['effect_ids']:
        row=by_effect[key];resolution=row['screenshot_difference']
        assert resolution['discrepancy_status']=='RESOLVED_BY_SOURCE_PRIORITY'
        assert resolution['screenshot_relation']=='DIFFERS' and resolution['cause_status']=='UNKNOWN_NOT_REQUIRED_FOR_ADOPTION'
        assert resolution['adopted_numeric_value']==adopted and resolution['screenshot_numeric_value']==shot
        assert resolution['policy_sha256']==sha(OUT/resolution['policy_path'])
        assert resolution['provenance']=='USER_INSTRUCTION' and row['calculation_status']=='CONFIRMED_LOCAL_RULE'
        assert resolution['adopted_display']==case['adopted_display'] and resolution['adopted_unit']==case['adopted_unit']
        for field in resolution['adopted_fields']:
            source=records[field['record_key']]
            assert field['raw_value']==source['raw'][field['field_path'][1:]]
            assert (field['table'],field['record_id'],field['effect_type'])==(table,sid,kind)
            view=next(v for v in views if v['record_key']==field['record_key'] and v['field_path']==field['field_path'])
            assert all(view[k]==v for k,v in field.items())
            assert len(view['screenshot_resolutions'])==1
            scoped_resolution=view['screenshot_resolutions'][0]
            assert all(resolution[k]==value for k,value in scoped_resolution.items())
            rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==(table,kind,field['field_path']))
            assert rule['screenshot_resolutions']==[scoped_resolution]
            assert resolution['policy_path'] in view['evidence'] and resolution['policy_path'] in rule['evidence']
            assert all((OUT/p).is_file() for p in resolution['evidence'])
    assert len(next(r for r in resolved_effects if r['screenshot_difference']['case_id']==case['case_id'])['screenshot_difference']['adopted_fields'])==len(expected_fields)
assert sum(bool(v['screenshot_resolutions']) for v in views)==8
assert sum(bool(r['screenshot_resolutions']) for r in rules)==8
check('five_user_policy_adoptions_seven_effects_eight_fields_traceable_and_different_values_preserved',True)

barrier_resolution=by_effect['a1_barrier_guard']['screenshot_difference']
assert barrier_resolution['adopted_numeric_value'] is None
assert barrier_resolution['conditional_nominal_value']['value']==20
assert '请求系数1' in barrier_resolution['conditional_nominal_value']['condition']
assert 'float32(2×请求系数)' in by_effect['a1_barrier_guard']['readable_value']
assert '无条件20%' in barrier_resolution['limits_zh'] and '截图5%反推' in barrier_resolution['limits_zh']
assert 'Attacked' in by_effect['other_class_heal_ratio']['screenshot_difference']['adopted_display']
assert '每次有效' in by_effect['other_a2_chain_probability']['screenshot_difference']['adopted_unit']
assert '不是整条Chain累计概率' in by_effect['other_a2_chain_probability']['remaining_gap']
assert all(by_effect[key]['duration'].startswith('30游戏秒') for key in ('a1_enemy_atk','a1_enemy_def','other_a1_enemy_move'))
check('adopted_barrier_is_conditional_formula_and_critical_lifesteal_chain_duration_units_remain_scoped',True)

overview_resolutions=[r for r in comparison if r['screenshot_resolutions']]
assert len(overview_resolutions)==5 and sum(r['status']=='resolved' for r in overview_resolutions)==3
assert {r['screenshot_resolutions'][0]['case_id'] for r in overview_resolutions}==set(expected_adoptions)
assert {r['title'] for r in comparison if r['status']=='diff'}=={'攻击类型与初始武器','初始玛那、沙漠强化、必杀强化'}
assert next(r for r in comparison if r['title']=='地形变化与屏障')['status']=='raw'
check('legacy_overview_numeric_adoptions_visible_other_text_conflicts_not_erased',True)

# Prior completion belongs to its frozen numerical-scope snapshot, not this Goal.
audit=load(OUT/'completion_audit.json')
for file,key in (('manifest.json','manifest_sha256'),('validation.json','validation_sha256'),('description_effects.json','description_effects_sha256')):
    assert sha(OUT/'prior_numeric_completion'/file)==audit['binding'][key]
prior_effects={r['effect_id']:r for r in load(OUT/'prior_numeric_completion/description_effects.json')}
assert set(prior_effects)==set(by_effect)
for effect in effects:
    prior=prior_effects[effect['effect_id']]
    for key in ('raw_value_status','calculation_status','description_record_key','description_field','description_ja','screenshot_value'):
        assert effect[key]==prior[key], (effect['effect_id'],key)
    assert all(ref in effect['field_refs'] for ref in prior['field_refs'])
prior_manifest=load(OUT/'prior_numeric_completion/manifest.json')
assert all(manifest[key]==prior_manifest[key] for key in ('source_sha256','screenshot_sha256'))
check('prior_audit_frozen_and_101_original_refs_descriptions_screenshot_and_calculation_states_preserved',True)

class Page(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.articles=[]; self.table_rows=0;self.effect_rows=[];self.ids=[];self.reusable_ids=[];self.missing_fields=[]
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag == 'a' and 'href' in a: self.links.append(a['href'])
        if tag == 'article': self.articles.append(a.get('data-status'))
        if tag == 'tr': self.table_rows += 1
        if tag=='tr' and 'data-effect-id' in a:self.effect_rows.append(a['data-effect-id'])
        if tag=='tr' and 'data-reusable-id' in a:self.reusable_ids.append((int(a['data-reusable-type']),int(a['data-reusable-id'])))
        if tag=='td' and 'data-missing-field' in a:self.missing_fields.append(a['data-missing-field'])

page = Page(); html = (OUT/'index.html').read_text(encoding='utf-8'); page.feed(html)
check('html_33_overview_articles_101_atomic_effects_1750_reusable_records_and_links', len(page.articles) == 33 and page.table_rows == 54+len(effects)+1+408+322+407+383+134+65+38
      and page.effect_rows==[r['effect_id'] for r in effects]
      and Counter(page.articles) == Counter(r['status'] for r in comparison)
      and all((OUT/link).is_file() for link in page.links if ':' not in link and not link.startswith('#')))
check('HTML_1095_search_keeps_407_records_and_proof_link',sum(kind==1095 for kind,sid in page.reusable_ids)==407
      and {sid for kind,sid in page.reusable_ids if kind==1095}=={r['raw']['skillid'] for r in reusable_records}
      and 'type1095-search' in page.ids and '../ordinary_effects/ability1095/README.md' in page.links)
check('HTML_1017_search_has_321_records_gate_fields_proof_and_separate_search_target',sum(kind==1017 for kind,sid in page.reusable_ids)==321
      and {sid for kind,sid in page.reusable_ids if kind==1017}=={r['raw']['skillid'] for r in job_records}
      and 'type1017-search' in page.ids and '../ordinary_effects/ability1017/README.md' in page.links
      and 'param0源值均为1' in html and 'ALMIGHTY5' in html)
check('HTML_2012_search_has_406_records_three_columns_193_missing_cells_and_separate_target',sum(kind==2012 for kind,sid in page.reusable_ids)==406
      and {sid for kind,sid in page.reusable_ids if kind==2012}==set(by_support_id)
      and Counter(page.missing_fields)=={'/param4':98,'/param5':95,'/param1':79,'/param2':79,'/param6':34,'/param8':238,'/param7':7,'/param9':10}
      and 'type2012-search' in page.ids and '../ordinary_effects/ability2012/README.md' in page.links)
check('HTML_3000_has_all_382_records_including_34_without_requested_fields_and_missing_cells',sum(kind==3000 for kind,sid in page.reusable_ids)==382
      and {sid for kind,sid in page.reusable_ids if kind==3000}==set(by_sympathy_id)
      and 'type3000-search' in page.ids and '../ordinary_effects/ability3000/README.md' in page.links
      and 'REQUESTED_SOURCE_FIELDS_ABSENT' in html and '34条四项全缺失' in html)
check('HTML_99_has_133_records_three_columns_17_missing_cells_minus_one_and_separate_search',sum(kind==99 for kind,sid in page.reusable_ids)==133
      and {sid for kind,sid in page.reusable_ids if kind==99}==set(by_drain_id)
      and 'type99-search' in page.ids and '../ordinary_effects/ability99/README.md' in page.links
      and 'SOURCE_MINUS_ONE_NO_POSITIVE_COUNTDOWN' in html and 'param1/3/2' in html)
check('HTML_7_has_64_records_terrain_attack_incoming_columns_original_conflict_and_separate_search',sum(kind==7 for kind,sid in page.reusable_ids)==64
      and {sid for kind,sid in page.reusable_ids if kind==7}==set(by_stage_id)
      and 'type7-search' in page.ids and '../ordinary_effects/ability7/README.md' in page.links
      and 'SOURCE_NAME_TEXT_CONFLICT_CODE_MATCHES_DESERT' in html and '增加24900%' in html)
check('HTML_1008_has_37_records_terrain_recipient_attack_incoming_columns_and_separate_search',sum(kind==1008 for kind,sid in page.reusable_ids)==37
      and {sid for kind,sid in page.reusable_ids if kind==1008}==set(by_stage_all_id)
      and 'type1008-search' in page.ids and '../ordinary_effects/ability1008/README.md' in page.links
      and 'TargetStageAll地形条件全体强化' in html and '非活动提供者走独立后备路径' in html)
check('five_adjudicated_difference_groups_have_unique_html_targets_and_policy_link',len(page.ids)==len(set(page.ids))
      and all(link[1:] in page.ids for link in page.links if link.startswith('#'))
      and sum(link in ('#a1_barrier_guard','#other_class_param5','#other_class_heal_ratio','#other_a2_chain_probability','#a1_enemy_atk') for link in page.links)==5
      and '5组取值均已裁决' in html and '5组差异仍开放' not in html
      and 'difference_sources/adoption_policy.json' in page.links)
native = load('output/boss_chain/type105/native_checks.json')
trace = load('output/boss_chain/type105/trace.json')
check('eleven_native_fragment_checks_bound_to_trace', len(native['checks']) == 11
      and all(c['passed'] for c in native['checks']) and native['native_sha256'] == trace['native_sha256'])
native112=load('output/boss_chain/type112/native_checks.json')
trace112=load('output/boss_chain/type112/trace.json')
check('23_type112_checks_bound_to_same_native_version',len(native112['checks'])==23
      and all(c['passed'] for c in native112['checks'])
      and native112['native_sha256']==trace112['native_sha256']==trace['native_sha256'])
check('initial_grid_6x3_and_native_nine_mask_cells',trace112['ground_initializer']['values'][:2]==[6,3]
      and all(len(r['cells'])==9 for r in next(c for c in native112['checks'] if c['name']=='88725_nine_cells_native_mask_and_edge_clamp')['layouts']))
guard_native=load('output/boss_chain/type13_basis/native_checks.json')
guard_trace=load('output/boss_chain/type13_basis/trace.json')
check('seven_guard_basis_checks_scale_and_double_truncation',len(guard_native['checks'])==7 and all(c['passed'] for c in guard_native['checks'])
      and guard_native['native_sha256']==guard_trace['native_sha256']==trace['native_sha256']
      and abs(guard_trace['player_scale']['float32']-.1)<1e-8
      and guard_native['checks'][-1]['normal_atk']==13 and guard_native['checks'][-1]['stored_guard']==4)
check('39_ordinary_native_checks_current_script_and_version',len(ordinary_checks['checks'])==39
      and all(c['passed'] for c in ordinary_checks['checks'])
      and ordinary_checks['native_sha256']==ordinary_trace['native_sha256']==trace['native_sha256']
      and ordinary_trace['source_sha256']==sha(SOURCE)
      and ordinary_trace['script_sha256']==sha('scripts/chica_ordinary_rules.py'))
check('six_skill_power_native_checks_bound_to_current_script',len(power_checks['checks'])==6 and all(c['passed'] for c in power_checks['checks']) and power_checks['native_sha256']==power_trace['native_sha256']==trace['native_sha256'] and power_trace['script_sha256']==sha('scripts/chica_skill_power.py'))
check('15_timed_support_checks_and_wave_scope_correction',len(timed_checks['checks'])==15 and all(c['passed'] for c in timed_checks['checks']) and timed_checks['native_sha256']==timed_trace['native_sha256']==trace['native_sha256'] and timed_trace['script_sha256']==sha('scripts/chica_timed_support.py') and next(r for r in effects if r['effect_id']=='wave_43023609_param1')['target'].startswith('职业掩码1'))
barrier_trace=load(OUT/'barrier/trace.json');barrier_checks=load(OUT/'barrier/native_checks.json')
barrier_views=[v for v in views if v['effect_type']==16 and v['table']=='bossskill']
check('four_barrier_checks_fixed_guard_coefficient_and_source',len(barrier_checks['checks'])==4 and all(c['passed'] for c in barrier_checks['checks']) and barrier_checks['native_sha256']==barrier_trace['native_sha256']==trace['native_sha256'] and barrier_trace['script_sha256']==sha('scripts/chica_barrier_rule.py') and len(barrier_views)==1 and barrier_views[0]['raw_value']==2 and barrier_trace['source_records'][0]==records[barrier_views[0]['record_key']])
request_trace=load(OUT/'barrier_request/trace.json');request_checks=load(OUT/'barrier_request/native_checks.json')
assert len(request_trace['source_records'])==3 and all(r==records[r['record_key']] for r in request_trace['source_records'])
assert request_trace['ability_enum']['name']=='AutoSkill' and request_trace['ability_enum']['default']['value']==1080
assert request_trace['setup_dispatch']['branch_rva']=='0x10f5dec'
assert len(request_checks['checks'])==29 and all(c['passed'] for c in request_checks['checks'])
assert request_trace['native_sha256']==request_checks['native_sha256']==trace['native_sha256']
assert request_trace['metadata_sha256']==barrier_trace['metadata_sha256']
assert request_trace['source_sha256']==sha(SOURCE) and request_trace['script_sha256']==sha('scripts/chica_barrier_request.py')
assert [c['result'] for c in request_checks['checks'] if c['name'].endswith('_default_extra_chain_rate')]==[1,1,1,1]
assert all(c['request_factor']==c['boss_skill_chain_rate'] for c in request_checks['checks'] if c['name'].startswith('auto_'))
for lookup in request_trace['apk_coverage']:
    assert lookup['sha256']==sha(lookup['path'])
    assert [r for r in load(lookup['path'])[lookup['table']] if r.get(lookup['id_field'])==lookup['record_id']]==lookup['matches']==[]
assert '无规则或新建未覆盖规则时系数1' in by_effect['a1_barrier_guard']['readable_value']
assert by_effect['a1_barrier_guard']['screenshot_value']=='自身ATK5%'
assert any(f['table']=='skilllist' and f['record_id']==43023603 and f['field_path']=='/str0' for f in by_effect['a1_barrier_guard']['field_refs'])
assert [c['damage_after_this_step'] for c in request_checks['checks'] if c['name'].startswith('fixed_guard_damage_step_')]==[5000,8750,1]
check('29_auto_barrier_request_and_guard_subtraction_checks_default1_actual_rule_unknown_APK_ID_absence',True)
coverage=request_trace['cached_rule_coverage'];digest_bytes=Path(coverage['path']).read_bytes();digest=json.loads(digest_bytes)
assert coverage['sha256']==sha(coverage['path']) and coverage['count']==len(coverage['views'])==1064
for view in coverage['views']:
    parts=view['json_pointer'].strip('/').split('/');quest=digest[parts[0]][int(parts[1])][int(parts[2])]
    assert quest['quest_id']==view['record_id'] and quest[parts[3]]==view['raw_value']=={'rule':0}
    assert view['record_key'] in records
for parent in coverage['parent_locations']:
    r=records[parent['record_key']]
    assert all(parent[k]==r[k] for k in parent)
    loc=parent['location'];part=digest_bytes[loc['byte_begin']:loc['byte_end_exclusive']]
    assert json.loads(part)==r['raw'] and hashlib.sha256(part).hexdigest()==loc['raw_record_sha256']
assert request_trace['rule_extra_field']['name']=='_debuff_extra_chain_rate' and request_trace['rule_extra_field']['offset']=='0xd0'
assert request_trace['local_load_probe']['filename_literal']['text']=='/helper.data5'
check('1064_cached_quest_rule_summaries_have_no_explicit_extra_chain_rate_and_constructor_defaults1',True)
check('33_scoped_critical_native_checks_current_script_and_inputs',len(critical_checks['checks'])==33
      and all(c['passed'] for c in critical_checks['checks'])
      and critical_checks['native_sha256']==critical_trace['native_sha256']==trace['native_sha256']
      and critical_trace['script_sha256']==sha('scripts/chica_critical_rules.py')
      and critical_trace['source_sha256']==sha(SOURCE))
check('19_movement_checks_and_nominal_interval_current_sources',len(movement_checks['checks'])==19
      and all(c['passed'] for c in movement_checks['checks'])
      and movement_checks['native_sha256']==movement_trace['native_sha256']==trace['native_sha256']
      and movement_trace['script_sha256']==sha('scripts/chica_move_rules.py')
      and movement_trace['card_record']==next(r for r in records.values() if r['table']=='charainfo' and r['raw'].get('cid')==30236)
      and movement_checks['checks'][-1]['nominal_interval']==1.125
      and '1.125' in by_effect['other_a2_attack_interval']['readable_value'])
check('13_ability21_checks_amount_flag_cap_and_screenshot_difference',len(lifesteal_checks['checks'])==13
      and all(c['passed'] for c in lifesteal_checks['checks'])
      and lifesteal_checks['native_sha256']==lifesteal_trace['native_sha256']==trace['native_sha256']
      and lifesteal_trace['script_sha256']==sha('scripts/chica_lifesteal.py')
      and lifesteal_trace['source_sha256']==sha(SOURCE)
      and lifesteal_trace['constants_sha256']==sha('output/boss_heal/constants.json')
      and lifesteal_trace['high_word_literal']['text']=='flag0_1'
      and lifesteal_checks['checks'][1]['heal_amount']==250
      and lifesteal_checks['checks'][6]['retained']==1<<41
      and abs(lifesteal_checks['checks'][7]['rate']-1.4)<1e-6
      and [c['hp_after'] for c in lifesteal_checks['checks'][8:]]==[1250,1400,1400,1500,1401]
      and '25%' in by_effect['other_class_heal_ratio']['readable_value']
      and by_effect['other_class_heal_ratio']['screenshot_value']=='20%'
      and '1.4' in by_effect['other_class_overheal']['readable_value'])
field_time_trace=load(OUT/'field_time/trace.json');field_time_checks=load(OUT/'field_time/native_checks.json')
field_time_view=next(v for v in views if v['table']=='bossskill' and v['effect_type']==66)
check('seven_type66_duration_checks_and_two_description_bindings',len(field_time_checks['checks'])==7
      and all(c['passed'] for c in field_time_checks['checks'])
      and field_time_checks['native_sha256']==field_time_trace['native_sha256']==trace['native_sha256']
      and field_time_trace['script_sha256']==sha('scripts/chica_field_time.py')
      and field_time_trace['source_sha256']==sha(SOURCE)
      and field_time_trace['delta_icall']['text']=='UnityEngine.Time::get_deltaTime()'
      and len(field_time_trace['source_records'])==5
      and all(r==records[r['record_key']] for r in field_time_trace['source_records'])
      and field_time_view['raw_value']==field_time_view['converted_value']==300
      and field_time_view['record_id']==43023613 and field_time_view['field_path']=='/skillparam5'
      and field_time_view['location']==records[field_time_view['record_key']]['location']
      and [(c['after'],c['expiry_branch']) for c in field_time_checks['checks'][3:]]==[(0,False),(299.5,False),(300,True),(300.5,True)]
      and all(by_effect[k]['duration']=='300游戏秒' and by_effect[k]['readable_value'] is not None for k in ('other_a1_desert_duration','other_symp_desert_duration')))
check('14_ability28_threshold_checks_scoped_fields_and_original_unknown_preserved',len(mana_chance_checks['checks'])==14
      and all(c['passed'] for c in mana_chance_checks['checks'])
      and mana_chance_checks['native_sha256']==mana_chance_trace['native_sha256']==trace['native_sha256']
      and mana_chance_trace['script_sha256']==sha('scripts/chica_mana_chance.py')
      and mana_chance_trace['source_sha256']==sha(SOURCE)
      and mana_chance_trace['rng_icall']['text']=='UnityEngine.Random::Range(System.Single,System.Single)'
      and all(r==records[r['record_key']] for r in mana_chance_trace['source_records'])
      and len([c for c in mana_chance_checks['checks'] if 'fields' in c])==6
      and '20%' in by_effect['other_a1_mana_chance']['readable_value']
      and by_effect['other_a1_mana_chance']['screenshot_value']=='一定几率（截图未标数字）'
      and not any(v['record_id']==43023602 and v['field_path']=='/param3' for v in ordinary_views)
      and mana_chance_trace['source_records'][0]['raw']['param3']==.8)
check('14_ability1106_checks_rate_quantity_latch_and_difference',len(chain_mana_checks['checks'])==14
      and all(c['passed'] for c in chain_mana_checks['checks'])
      and chain_mana_checks['native_sha256']==chain_mana_trace['native_sha256']==trace['native_sha256']
      and chain_mana_trace['script_sha256']==sha('scripts/chica_chain_mana.py')
      and chain_mana_trace['source_sha256']==sha(SOURCE)
      and all(r==records[r['record_key']] for r in chain_mana_trace['source_records'])
      and [c['rate'] for c in chain_mana_checks['checks'][:2]]==[0,0]
      and all(abs(c['rate']-.1)<1e-7 for c in chain_mana_checks['checks'][2:7])
      and chain_mana_checks['checks'][6]['amount']==1
      and [c['success'] for c in chain_mana_checks['checks'][7:11]]==[True,True,False,False]
      and chain_mana_checks['checks'][-1]['latched'] is False
      and '生成数量输入' in by_effect['other_a2_chain_count']['readable_value'])
dispatch_trace=load(OUT/'chain_dispatch/trace.json');dispatch_checks=load(OUT/'chain_dispatch/native_checks.json')
assert dispatch_trace['script_sha256']==sha('scripts/chica_chain_dispatch.py') and dispatch_trace['source_sha256']==sha(SOURCE)
assert dispatch_trace['native_sha256']==dispatch_checks['native_sha256']==trace['native_sha256']
assert dispatch_trace['metadata_sha256']==chain_mana_trace['metadata_sha256']
assert all(r==records[r['record_key']] for r in dispatch_trace['source_records'])
assert dispatch_trace['reused_rate_proof']['sha256']==sha(dispatch_trace['reused_rate_proof']['path'])
assert len(dispatch_checks['checks'])==17 and all(c['passed'] for c in dispatch_checks['checks'])
button_checks=[c for c in dispatch_checks['checks'] if c['name'].startswith('button_one_work_')]
assert len(button_checks)==7 and [c['random_calls'] for c in button_checks]==[0,0,1,1,1,1,1]
assert [c['dispatched_chain_num'] for c in button_checks]==[0,1,2,3,4,5,5]
assert all(c['work_calls']==1 and c['award_count']==0 for c in button_checks)
assert [c['random_calls'] for c in dispatch_checks['checks'] if c['name'].startswith('sequence_')]==[4,2,2]
assert '每次有效按钮事件阈值10%' in by_effect['other_a2_chain_probability']['readable_value']
assert all('chain_dispatch/trace.json' in v['evidence'] for v in views if v['table']=='skilllist' and v['record_id']==43023617)
check('17_chain_button_dispatch_checks_one_threshold_per_work_retries_and_latch',True)
leader_condition_trace=load(OUT/'leader_condition/trace.json');leader_condition_checks=load(OUT/'leader_condition/native_checks.json')
leader_views=[v for v in views if v['table']=='leader_ability']
assert len(leader_views)==3 and {v['field_path'] for v in leader_views}=={'/border','/category','/conditions'}
for v in leader_views:
    r=records[v['record_key']];f=v['field_path'][1:]
    assert v['record_id']==30236 and r==leader_condition_trace['source_records'][0]
    assert v['raw_value']==r['raw'][f] and v['source_sha256']==r['source_sha256'] and v['location']==r['location']
    assert v['json_pointer']==r['location']['json_pointer']+'/'+f
check('eight_leader_job_minimum_count_checks_and_exact_auxiliary_source',len(leader_condition_checks['checks'])==8
      and all(c['passed'] for c in leader_condition_checks['checks'])
      and leader_condition_checks['native_sha256']==leader_condition_trace['native_sha256']==trace['native_sha256']
      and leader_condition_trace['script_sha256']==sha('scripts/chica_leader_condition.py')
      and leader_condition_trace['source_sha256']==sha(SOURCE)
      and leader_condition_trace['job0_enum']['value']==0 and leader_condition_trace['job0_label']['text']=='戦士'
      and [h['method']['name'] for h in leader_condition_trace['generic_helpers']]==['Intersect','Any']
      and [c['qualified'] for c in leader_condition_checks['checks'][2:]]==[False,False,False,True,True,True]
      and '至少4名' in by_effect['other_leader_threshold']['readable_value']
      and 'target0仅确认' in by_effect['other_leader_threshold']['remaining_gap'])
super_counter_trace=load(OUT/'super_counter/trace.json');super_counter_checks=load(OUT/'super_counter/native_checks.json')
code_constant=super_counter_trace['code_constants'][0]
blob=Path(code_constant['original_file']).read_bytes();loc=code_constant['location'];raw_code=blob[loc['byte_begin']:loc['byte_end_exclusive']]
native_view=next(v for v in views if v['table']=='NATIVE_METHOD')
assert native_view['record_key']==code_constant['record_key'] and native_view['raw_value']==native_view['converted_value']==10
assert native_view['source_sha256']==code_constant['source_sha256'] and native_view['location']==loc and native_view['json_pointer'] is None
assert all(isinstance(r['code_refs'],list) for r in effects)
check('eight_shared_super_counter_checks_and_native_constant_bytes',len(super_counter_checks['checks'])==8
      and all(c['passed'] for c in super_counter_checks['checks'])
      and super_counter_checks['native_sha256']==super_counter_trace['native_sha256']==trace['native_sha256']==hashlib.sha256(blob).hexdigest()
      and super_counter_trace['script_sha256']==sha('scripts/chica_super_counter.py')
      and super_counter_trace['source_sha256']==sha(SOURCE)
      and all(r==records[r['record_key']] for r in super_counter_trace['source_records'])
      and raw_code.hex()==loc['raw_hex'] and len(raw_code)==4 and (int.from_bytes(raw_code,'little')>>10)&4095==10
      and by_effect['other_sp_super_counter']['code_refs']==[code_constant]
      and by_effect['other_sp_super_counter']['raw_value_status']=='RAW_CODE_CONSTANT_FOUND'
      and [c['threshold_reached'] for c in super_counter_checks['checks'][:3]]==[False,False,True])
wedge_time_trace=load(OUT/'wedge_time/trace.json');wedge_time_checks=load(OUT/'wedge_time/native_checks.json')
wedge_constant=wedge_time_trace['code_constants'][0];loc=wedge_constant['location'];raw_code=blob[loc['byte_begin']:loc['byte_end_exclusive']]
word=int.from_bytes(raw_code,'little');imm8=(word>>13)&255
exponent=(0 if imm8&64 else 128)|(124 if imm8&64 else 0)|((imm8>>4)&3)
bits=((imm8>>7)<<31)|(exponent<<23)|((imm8&15)<<19)
native_view=next(v for v in views if v['table']=='NATIVE_METHOD' and v['record_id']==9093)
assert native_view['record_key']==wedge_constant['record_key'] and type(native_view['raw_value']) is float
assert native_view['raw_value']==native_view['converted_value']==5.0 and native_view['location']==loc
assert native_view['source_sha256']==wedge_constant['source_sha256'] and native_view['json_pointer'] is None
assert len([v for v in views if v['table']=='NATIVE_METHOD'])==2
check('nine_wedge_mode_and_game_timer_checks_and_float_instruction',len(wedge_time_checks['checks'])==9
      and all(c['passed'] for c in wedge_time_checks['checks'])
      and wedge_time_checks['native_sha256']==wedge_time_trace['native_sha256']==trace['native_sha256']
      and wedge_time_trace['script_sha256']==sha('scripts/chica_wedge_time.py')
      and wedge_time_trace['source_sha256']==sha(SOURCE)
      and all(r==records[r['record_key']] for r in wedge_time_trace['source_records'])
      and raw_code.hex()==loc['raw_hex'] and word&0xffe01fe0==0x1e201000
      and struct.unpack('<f',bits.to_bytes(4,'little'))[0]==5.0
      and [c['timer_after'] for c in wedge_time_checks['checks']]==[5,8,7,0,0,4.75,0,0,0]
      and by_effect['other_a1_wedge_stop']['code_refs']==[wedge_constant]
      and 'clockUpFlag=0' in by_effect['other_a1_wedge_stop']['condition'])
check('handoff_local_links_exist', all((Path('HANDOFF.md').parent/p).exists()
      for p in re.findall(r'\]\(([^)]+)\)', Path('HANDOFF.md').read_text(encoding='utf-8')) if '://' not in p))
result = dict(status='PASS_DATA_AND_STRUCTURE', checks=checks,
              screenshot_adjudication=dict(status='COMPLETE_BY_USER_SOURCE_PRIORITY', policy_path='difference_sources/adoption_policy.json',
                  policy_sha256=sha(OUT/'difference_sources/adoption_policy.json'), cases_resolved=5, effects=7, fields=8,
                  screenshot_values_preserved=True, screenshot_numeric_equality=False, historical_causes='UNKNOWN',
                  barrier_actual_context='UNKNOWN_FORMULA_ADOPTED', validation_kind='GENERATOR_OUTPUT_CHECK_NOT_INDEPENDENT_REVIEW',
                  manifest_sha256=sha(OUT/'manifest.json')),
              comparison_rows=len(comparison), exact_source_records_verified=len(evidence),
              type105_records=142, type105_fields=284, type112_records=96,type112_fields=657,
              native_checks_type105=11,native_checks_type112=23,
              type13_basis_records=718,type13_basis_fields=718,native_checks_type13_basis=7,
              ordinary_records=1723,ordinary_fields=4947,ordinary_rules=60,reusable_1008_records=37,reusable_1008_fields=111,native_checks_reusable_1008=389,reusable_7_records=64,reusable_7_fields=192,native_checks_reusable_7=1390,reusable_99_records=133,reusable_99_fields=382,native_checks_reusable_99=192,reusable_3000_records=382,reusable_3000_records_with_fields=348,reusable_3000_fields=1098,native_checks_reusable_3000=86,reusable_2012_records=406,reusable_2012_fields=1025,native_checks_reusable_2012=49,reusable_1017_records=321,reusable_1017_fields=1284,native_checks_reusable_1017=236,reusable_1095_records=407,reusable_1095_fields=814,native_checks_reusable_1095=32,native_checks_ordinary=39,native_checks_skill_power=6,native_checks_timed_support=15,native_checks_barrier=4,native_checks_barrier_request=29,native_checks_critical=33,native_checks_movement=19,native_checks_lifesteal=13,native_checks_field_time=7,native_checks_mana_chance=14,native_checks_chain_mana=14,native_checks_chain_dispatch=17,native_checks_leader_condition=8,native_checks_super_counter=8,native_checks_wedge_time=9,
              description_effects=len(effects),description_effects_answered=sum(r['readable_value'] is not None for r in effects),
              visual_browser_check='NOT_COMPLETED: browser security policy rejects file:// URLs; no workaround attempted')
(OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=len(checks),status=result['status'])))
