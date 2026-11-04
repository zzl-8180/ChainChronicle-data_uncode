"""Check immutable sources and collect observed research times, without running arms."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'output/skill_mechanism_scale/20261104'

def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def save(name,data): (BASE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def stamp(value):
    if value.endswith(' UTC'):
        return datetime.fromisoformat(value[:-4]).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace('Z','+00:00'))
def pointer(obj,path):
    for key in path.strip('/').split('/'):
        key=key.replace('~1','/').replace('~0','~')
        obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--freeze',action='store_true'); args=parser.parse_args()
    protocol=load(BASE/'protocol.json'); manifest=load(BASE/'input/manifest.json')
    targets={x['task_id']:x for x in load(BASE/'input/targets.json')}
    rules=load(BASE/'input/output/character_skills/profiles/rules.json')
    input_errors=[p for p,h in manifest['files'].items() if digest(BASE/'input'/p)!=h['sha256']]
    assert not input_errors,input_errors
    arms={}; checks=[]; cached={}
    for name,ids in protocol['arms'].items():
        result=load(BASE/name/'task_results.json'); timing=load(BASE/name/'timing.json')
        # An arm may finalize its data JSON before packaging/checks finish.
        # Full timing.json bounds consistently include that tail for every arm.
        started=timing.get('started_at') or timing.get('started_at_utc') or result['started_at']
        finished=timing.get('finished_at') or timing.get('finished_at_utc') or result['finished_at']
        reported_finish=finished
        validation=load(BASE/name/'validation.json')
        verification_times=[validation[k] for k in ['finished_at','finished_at_utc','validated_at_utc','checked_at'] if isinstance(validation.get(k),str)]
        if verification_times:
            finished=max([finished,*verification_times],key=stamp)
        assert stamp(finished)>=stamp(started)>=stamp(protocol['frozen_at'])
        tasks=result['tasks']; assert {t['task_id'] for t in tasks}==set(ids)
        submitted=0
        for task in tasks:
            target=targets[task['task_id']]
            assert task['cid']==target['cid'] and task['row_id']==target['row_id']
            effect_ids={e['effect_id'] for e in target['baseline_effects']}
            for answer in task.get('answers',[]):
                source=answer['source']; path=source['input_relative_path']; ptr=source['json_pointer']
                if path not in cached: cached[path]=load(BASE/'input'/path)
                obj=pointer(cached[path],ptr)
                field=answer['field_path'].lstrip('/')
                if isinstance(obj,dict): record=obj; raw=obj.get(field)
                else: raw=obj; record=pointer(cached[path],ptr.rsplit('/',1)[0])
                rule=rules.get(answer.get('rule_key'))
                check={'arm':name,'task_id':task['task_id'],'effect_id':answer['effect_id'],
                       'field':answer['field_path'],'checks':{
                           'effect':answer['effect_id'] in effect_ids,
                           'raw':raw==answer['raw_value'],
                           'record':record.get('skillid')==source['record_id'],
                           'layer':source['layer']=='CACHE',
                           'rule_exists':bool(rule),
                           'rule_type':bool(rule and rule.get('effect_type')==record.get('ability',record.get('skillid0'))),
                           'rule_field':bool(rule and rule.get('field_path')==answer['field_path']),
                           'rule_table':bool(rule and rule.get('table')==source['table']),
                       }}
                check['passed']=all(check['checks'].values()); checks.append(check); submitted+=1
        arms[name]={'started_at':started,'finished_at':finished,'reported_research_finished_at':reported_finish,
                    'completion_adjustment_seconds':(stamp(finished)-stamp(reported_finish)).total_seconds(),
                    'elapsed_seconds':(stamp(finished)-stamp(started)).total_seconds(),
                    'targets':len(tasks),'submitted_answers':submitted,'timing_reference':f'{name}/timing.json'}
    pnames=['parallel_attack','parallel_heal']
    parallel=(max(stamp(arms[n]['finished_at']) for n in pnames)-min(stamp(arms[n]['started_at']) for n in pnames)).total_seconds()
    serial=arms['card_serial']['elapsed_seconds']; grouped=arms['family_serial']['elapsed_seconds']
    totals={'card_serial_seconds':serial,'family_serial_seconds':grouped,'family_parallel_span_seconds':parallel,
            'family_parallel_sum_seconds':sum(arms[n]['elapsed_seconds'] for n in pnames),
            'grouping_difference_seconds':serial-grouped,'grouping_saving_percent':100*(serial-grouped)/serial,
            'parallel_difference_seconds':grouped-parallel,'parallel_saving_percent':100*(grouped-parallel)/grouped,
            'combined_saving_percent':100*(serial-parallel)/serial}
    save('collection.json',{'collected_at':datetime.now(timezone.utc).isoformat(),'snapshot':manifest['snapshot'],
         'input_hashes_checked':len(manifest['files']),'arms':arms,'observed_timing':totals,
         'source_checks':checks,'all_source_checks_passed':all(x['passed'] for x in checks),
         'caution':'Source/arithmetic collection is not semantic approval. Time comparisons require reviewed equal outcome sets. Completion uses max(full timing finish, final validation timestamp); reported research finish is retained separately.'})
    if args.freeze:
        dest=BASE/'arm_freeze_manifest.json'
        assert not dest.exists(),'Never overwrite arm freeze'
        save(dest.name,{'frozen_at':datetime.now(timezone.utc).isoformat(),'arms':{
            name:{p.relative_to(BASE).as_posix():digest(p) for p in sorted((BASE/name).rglob('*')) if p.is_file()}
            for name in protocol['arms']}})
    print(json.dumps({'times':totals,'source_checks':len(checks),'passed':all(x['passed'] for x in checks)}))

if __name__=='__main__': main()
