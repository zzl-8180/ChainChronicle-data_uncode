"""Compare only the existing cid30236 discrepancy IDs across local snapshots."""
import hashlib
import json
from pathlib import Path
from sample_trace import locate_record

OUT = Path('output/card_comparison_cid30236/difference_sources')
SOURCE = Path('output/cache_full_20261015_v3/records.jsonl')
OLDER = Path('output/decoded/skilllist.data5.json.raw')
EXPORT = Path('output/export/snapshot_223183400c1c62013338/build_261ac189c316abba/manifest.json')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = [json.loads(s) for s in SOURCE.read_text(encoding='utf-8').splitlines()]
    raw = OLDER.read_bytes()
    old = json.loads(raw)['skilllist']
    export = json.loads(EXPORT.read_text(encoding='utf-8'))
    binding = next(r for r in export['sources'] if r['input_file'] == OLDER.as_posix())
    assert binding['sha256'] == hashlib.sha256(raw).hexdigest()
    apk_path = Path('output/base_master/_mdSkill.json')
    apk = json.loads(apk_path.read_bytes())['skilllist']
    cases = []
    specs = [('class_critical', 65000001, ['param5'], ['other_class_param5'], '20%', '40个百分点'),
             ('class_lifesteal', 65000003, ['param1'], ['other_class_heal_ratio'], '20%', '25%'),
             ('chain_mana', 43023617, ['param1', 'param2', 'param3', 'param4'], ['other_a2_chain_probability'], '20%', '四档10%'),
             ('enemy_duration', 43023616, ['param0'], ['a1_enemy_atk', 'a1_enemy_def', 'other_a1_enemy_move'], '45秒', '30游戏秒')]
    for key, sid, fields, effect_ids, shot, answer in specs:
        current = next(r for r in records if r['table'] == 'skilllist' and r['raw'].get('skillid') == sid)
        hits = [i for i, r in enumerate(old) if r.get('skillid') == sid]
        assert len(hits) == 1
        row, location = locate_record(raw, 'skilllist', hits[0])
        older_record = dict(record_key='OLDER_CACHE/skilllist.data5.json.raw#' + location['json_pointer'],
                            layer='OLDER_CACHE', table='skilllist', snapshot_id=export['snapshot_id'], raw=row,
                            original_file=OLDER.as_posix(), source_sha256=binding['sha256'], location=location)
        comparisons = [dict(field_path='/' + f, current_raw_value=current['raw'][f], older_raw_value=row[f],
                            exact_match=current['raw'][f] == row[f]) for f in fields]
        assert all(c['exact_match'] for c in comparisons)
        apk_hits = [r for r in apk if r.get('skillid') == sid]
        assert apk_hits == []
        cases.append(dict(case_id=key, effect_ids=effect_ids, table='skilllist', record_id=sid,
                          effect_type=current['raw']['ability'], current_record=current, older_record=older_record,
                          fields=comparisons, apk_matches=apk_hits, screenshot_value=shot, current_readable_value=answer,
                          source_comparison_status='TWO_LOCAL_SNAPSHOTS_SAME_VALUES',
                          discrepancy_status='OPEN_SCREENSHOT_SOURCE_OR_CONTEXT',
                          finding='较早已审查输入与v3的本项参数相同；不能把差异直接归因于这两快照之间的更新。截图数字来源及更早版本仍未知。'))
    # Barrier's earlier ordinary trigger is available; earlier Boss source is absent.
    trigger = next(r for r in records if r['table'] == 'skilllist' and r['raw'].get('skillid') == 43023603)
    old_trigger = next(r for r in old if r.get('skillid') == 43023603)
    assert all(old_trigger.get(f) == trigger['raw'].get(f) for f in ('ability', 'param0', 'param1', 'param5', 'str0'))
    assert not Path('output/decoded/bossinfo.data5.json.raw').exists()
    proof = dict(kind='TARGETED_LOCAL_SOURCE_COMPARISON_NOT_RUNTIME_TEST',
                 script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                 older_source=dict(path=OLDER.as_posix(), sha256=binding['sha256'], export_manifest=EXPORT.as_posix(),
                                   export_manifest_sha256=hashlib.sha256(EXPORT.read_bytes()).hexdigest(), snapshot_id=export['snapshot_id']),
                 apk_source=dict(path=apk_path.as_posix(), sha256=hashlib.sha256(apk_path.read_bytes()).hexdigest()),
                 cases=cases,
                 barrier_limit='较早ordinary43023603自动触发参数相同；较早Boss输入不存在，未据普通同号ID猜旧屏障值。',
                 checks=[dict(case_id=c['case_id'], passed=True, fields_exact_match=len(c['fields']), apk_id_absent=True) for c in cases],
                 limits=['Only four existing numeric discrepancies; no other character or whole-game comparison.',
                         'Native semantic experiments are reused; this script only checks source identity, exact fields and byte locations.',
                         'Record timestamp values are preserved, not interpreted as per-record modification dates.',
                         'No screenshot version, actual battle settings or older matching numeric source is inferred.'])
    external_path=OUT/'reference_observations.json'
    external=json.loads(external_path.read_text(encoding='utf-8'))
    assert external['kind']=='CURATED_EXTERNAL_REFERENCE_OBSERVATIONS_NOT_GAME_INPUT'
    proof['external_observations']=dict(path=external_path.as_posix(),sha256=hashlib.sha256(external_path.read_bytes()).hexdigest(),
                                        content=external)
    (OUT / 'trace.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=len(cases), matching_fields=sum(len(c['fields']) for c in cases))))


if __name__ == '__main__':
    main()
