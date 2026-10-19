"""Targeted pilot source/level/quantity checks and optional immutable source receipt."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path

from card_page_data import SAMPLES,original_numbers,raw_state
from card_page import validate


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--snapshot',type=Path)
    args=p.parse_args();root=args.input_root.resolve();out=args.output.resolve();checks=[]
    def ck(name,condition,**detail):
        checks.append(dict(name=name,passed=bool(condition),**detail))
        if not condition:raise AssertionError(name)
    def read(path):return json.loads(path.read_text(encoding='utf-8'))
    cards={cid:read(out/str(cid)/'card.json') for cid in SAMPLES}
    ck('exactly_eleven_card_directories',{int(q.name) for q in out.iterdir() if q.is_dir() and q.name.isdigit()}==set(SAMPLES))
    for cid,c in cards.items():validate(c,(out/str(cid)/'index.html').read_text(encoding='utf-8'))
    ck('all_11_html_json_groups_rows_sources_consistent',True)
    links={}
    with (root/'output/character_skills/links/character_skills.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if row['cid'] in SAMPLES:links[row['cid']]=row
    for cid,group in [(10001,'extra'),(30236,'extra'),(30004,'passive')]:
        original=next(g for g in links[cid]['groups'] if g['group']==group)['records']
        projected=next(g for g in cards[cid]['groups'] if g['group']==group)['skills']
        ck(f'{cid}_{group}_every_reference_text_and_level',len(original)==len(projected) and
           all(a['record']['text'].replace('\\n','\n')==b['original_text'] and a['record'].get('lv')==b['level'] and
               a['reference_field']==b['reference_field'] and b['source'].get('parent_json_pointer') for a,b in zip(original,projected)),
           references=len(original))
    extra10001=next(g for g in cards[10001]['groups'] if g['group']=='extra')['skills']
    ck('10001_extra_1000_2_to_2000_10_not_folded','1000' in extra10001[0]['original_text'] and
       '1250' in extra10001[1]['original_text'] and '2000' in extra10001[-1]['original_text'] and
       any(n['value']=='2' for r in extra10001[0]['rows'] for n in r['original_numeric_items']) and
       any(n['value']=='10' for r in extra10001[-1]['rows'] for n in r['original_numeric_items']))
    passives=next(g for g in cards[30004]['groups'] if g['group']=='passive')['skills']
    ck('30004_passive_uses_order_not_invented_level',all(s['level_state']=='missing' and s['stage'].startswith('原表顺序档') for s in passives))
    ck('30004_passive_distinct_recovery_and_abnormal_text_preserved',len({s['original_text'] for s in passives})>1)
    denju=next(g for g in cards[10001]['groups'] if g['group']=='denju')['skills']
    ck('10001_all_five_denju_lb_kept_inside_teaching',sum(s['original_group']=='denju_lb' for s in denju)==5)
    fields={f['key']:f for f in cards[30236]['basic']['fields']}
    ck('30236_cache_missing_job_no_field_backfill',fields['jobtype']['raw_state']=='missing' and cards[30236]['basic']['layer']=='CACHE')
    ck('six_required_basic_locations_and_distinct_home',all(k in fields for k in ['critical','atkspeed','growth','profile','battle_home']) and
       fields['home']['raw_value']==8 and fields['battle_home']['raw_value']==32 and any(x['label']=='标签/外部资料' for x in cards[30236]['basic']['external']))
    ck('missing_null_real_zero_distinct',[raw_state({},'x'),raw_state({'x':None},'x'),raw_state({'x':0},'x')]==['missing','null','zero'])
    ck('HP50_is_threshold_not_attack_gain',original_numbers('HPが50%以上の時、攻撃力が上がる')[0]['role']=='HP条件阈值')
    ck('six_shots_original_quantity_retained',original_numbers('6発までの砲撃が可能')[0]['value']=='6')
    ck('ordinal_1st_not_effect_quantity',not original_numbers('1stChain以上を達成した時'))
    registry=cards[30236]['sources']['baseline_registry']
    ck('all_101_baseline_items_retained_and_located',len(registry)==101 and all(x['mapped_row_ids'] or x['mapped_skill_ids'] for x in registry.values()),
       row_mapped=sum(bool(x['mapped_row_ids']) for x in registry.values()),header_mapped=sum(bool(x['mapped_skill_ids']) for x in registry.values()))
    class_rows=next(g for g in cards[30236]['groups'] if g['group']=='class')['skills'][0]['rows']
    ck('class_self_party_short_snippet_disambiguated',not any(a.get('effect_id','').startswith('class_65000002') for a in class_rows[0]['answers']) and
       all(not a.get('effect_id','').startswith('class_65000001') for a in class_rows[1]['answers']))
    special=next(g for g in cards[30236]['groups'] if g['group']=='special_move')['skills']
    sand=next(s for s in special if s['record_id']==43023600)
    normal=next(s for s in special if s['record_id']==43023601)
    ck('sand_actual_child_references_and_condition_kept',not sand['rows'] and len(sand['baseline_metadata_answers'])==7 and
       all('沙漠档' in a['conditions'] and a['baseline_declared_description_id']==43023601 for a in sand['baseline_metadata_answers']) and
       not any('sp_43023600' in a.get('effect_id','') for r in normal['rows'] for a in r['answers']))
    allrows=[r for c in cards.values() for g in c['groups'] for s in g['skills'] for r in s['rows']]
    guard=[a for r in allrows for a in r['answers'] if 'guard' in a.get('effect_id','') and '固定' in a.get('value','')]
    ck('fixed_defence_keeps_formula_and_target_attack_base',bool(guard) and any('normalAtk' in a['value'] or 'ATK' in a['value'] for a in guard))
    ck('29_and_5023_existing_damage_heal_formula_reused',all(any('B ×' in a['value'] for g in cards[cid]['groups'] for s in g['skills'] for r in s['rows'] for a in r['answers']) for cid in (29,5023)))
    ck('internal_SA_labels_not_description_rows',all(not s['rows'] and s.get('internal_label') for cid in (30004,30338) for g in cards[cid]['groups'] if g['group']=='sa' for s in g['skills']))
    ck('original_A_not_credited_to_forward',all(c['coverage']['chain_new_A_rows']==0 and c['coverage']['chain_new_value_items_in_rows']==0 for c in cards.values()))
    ck('7229_all_A_explicit_original_B_zero',cards[7229]['coverage']['A']==cards[7229]['coverage']['original_A'] and cards[7229]['coverage']['B']==0)
    report=read(out/'pilot_report.json')
    ck('72_distinct_actual_samples_no_padding',len(report['samples'])==72 and len({r['row_id'] for r in report['samples']})==72)
    ck('denominator_changes_accounted',sum(c['coverage']['N_all'] for c in cards.values())==387 and
       sum(c['coverage']['leader_sympathy_rows_added']+c['coverage']['repeated_actual_occurrences_retained']-c['coverage']['internal_labels_excluded'] for c in cards.values())==3)
    result=dict(kind='IMPLEMENTATION_SELF_CHECK_NOT_INDEPENDENT_REVIEW',checks=checks,passed=len(checks),total=len(checks),
                scope='11 pilot pages only; no native rerun, historical regression suite or browser acceptance claim')
    (out/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.snapshot:
        snap=args.snapshot.resolve();snap.mkdir(parents=True,exist_ok=False)
        paths=sorted((root/'scripts/character_skills').glob('card_page*.py'))+[root/'docs/tasks/20261019-character-skills-card-pages.md']
        rows=[]
        for path in paths:
            rel=path.relative_to(root);target=snap/'files'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
            digest=hashlib.sha256(path.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
            rows.append(dict(path=rel.as_posix(),sha256=digest,size=path.stat().st_size))
        manifest=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),files=rows,
                      dependencies='Existing character_skills/common.py and rules.py plus declared unpacked artifact tree and converter helper modules; preserved by pre-pivot/type1082 snapshots.',
                      excluded='No game input, generated bulk results, environment or clean-environment reproduction claim')
        manifest['frozen_outputs']=[dict(path=q.relative_to(root).as_posix(),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),size=q.stat().st_size) for q in sorted(out.rglob('*')) if q.is_file()]
        (snap/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),total=len(checks),samples=len(report['samples']),N_all=sum(c['coverage']['N_all'] for c in cards.values())),ensure_ascii=True))


if __name__=='__main__':main()
