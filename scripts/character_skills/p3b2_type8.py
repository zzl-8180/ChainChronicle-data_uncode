"""Generate P3B2's fixed 15-record editorial decision ledger, not new rules."""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import common as C
import description_bindings as DB

BASE = C.ROOT/'output/character_skills'
OUT = BASE/'description_bindings/p3b2_type8'
IDS = [302,309,312,317,318,322,345,347,353,357,368,372,376,424,30124100]
MOVE = '戦闘時、移動速度が上昇する'
FRAGMENTS = {i:MOVE for i in IDS}
FRAGMENTS.update({353:'戦闘時、移動速度が大きく上昇する',368:'戦闘時、攻撃力が増加する',
                  372:'戦闘時、攻撃力が増加する',376:'戦闘時、攻撃力と移動速度が上昇する',
                  424:'攻撃力が上がる',30124100:'攻撃力が上がる'})
REASONS = {
    302:'完整原文为自身常时移动；背景及专用说明没有数值条件；无sub，param2唯一移动消费者。',
    309:'完整原文的舞步背景没有目标/计时门槛；自身常时移动，无sub，param2唯一。',
    312:'完整原文身体能力背景和专用说明没有新条件；自身常时移动，无sub，param2唯一。',
    317:'前句明说自身加速，目标片段限定移动；无sub，不把行动速度背景另答为攻速。',
    318:'盗剑士步法是背景说明；无sub，自身常时移动由param2唯一承载。',
    322:'主君/足运背景不是对象筛选；无sub，自身常时移动由param2唯一承载。',
    353:'完整原文将移动与战后金币分句；sub354/type100(Gold)的移动派发直接中性；不解释金币量。',
    357:'完整原文将移动与暴击率分句；sub358/type51(CriticalRate)移动路径中性由P3B1 D已核；不解释暴击句。',
    368:'完整原文将常时攻击与每WAVE回复分句；sub369/type16(WaveHeal)攻击路径直接中性；不把WAVE条件套到前句。',
    372:'完整原文攻击/移动分句，均在同一本体；目标攻击句param1唯一，无sub；后续非本次同句目标的移动句保留原提示。',
    376:'完整原文的攻移同句分别对应param1/param2；sub377/type46(Concentration)两路径直接中性，另句玛那槽保持未知。',
    345:DB.EXCLUSION_NOTES[345],347:DB.EXCLUSION_NOTES[347],424:DB.EXCLUSION_NOTES[424],
    30124100:DB.EXCLUSION_NOTES[30124100],
}

def lines(path):
    return [json.loads(x) for x in Path(path).open(encoding='utf-8')]

def main():
    C.enable_utf8_console()
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before',type=Path,default=C.ROOT/'work/character_skills_p3b2/before',
                    help='Explicit pre-batch snapshot directory; never overwritten')
    args=ap.parse_args()
    previous={r['rec_key']:r for r in lines(args.before/'records.jsonl')}
    records={r['rec_key']:r for r in lines(BASE/'profiles/records.jsonl')}
    profiles=lines(BASE/'profiles/profiles.jsonl')
    old_profiles=lines(args.before/'profiles.jsonl')
    tab=C.Tables()
    uses=collections.defaultdict(list)
    for p in profiles:
        for g in p['groups']:
            for ref in g['records']:
                cr,cl=tab('charainfo').get(p['cid'])
                if ref['rec_key'].startswith('skilllist|') and int(ref['rec_key'].split('|')[1]) in IDS:
                    idx=int(ref['reference_field'].split('[')[1].split(']')[0])
                    assert cr['skillid'][idx]==int(ref['rec_key'].split('|')[1])
                    assert C.location('charainfo',p['cid'],cl,cr)==p['charainfo_source']
                    uses[ref['rec_key']].append({'cid':p['cid'],'name':p['name'],'group':g['group'],
                        'reference_field':ref['reference_field'],'character_source':p['charainfo_source'],
                        'character_record':cr})
    ledger=[]
    for ident in IDS:
        key=f'skilllist|{ident}|APK|ability=8'
        now=records[key]
        raw,layer=tab('skilllist').get(ident)
        assert layer=='APK' and raw['ability']==8
        assert C.location('skilllist',ident,layer,raw)==now['source']
        target=next(f for f in now['fragments'] if f['t']==FRAGMENTS[ident])
        old=next(f for f in previous[key]['fragments'] if f['t']==FRAGMENTS[ident])
        included=ident in DB.P3B2_REVIEWED
        assert bool(target.get('binding'))==included
        subs=[]
        for sid in raw.get('sub') or []:
            sr,sl=tab('skilllist').get(sid)
            assert sr is not None and sl=='APK' and not sr.get('sub')
            subs.append({'record':sr,'source':C.location('skilllist',sid,sl,sr)})
        ledger.append({'record_id':ident,'rec_key':key,'decision':'INCLUDED_PENDING_INDEPENDENT_REVIEW' if included else 'EXCLUDED_RETAINED',
            'reason':REASONS[ident],'target_fragment':FRAGMENTS[ident],'source':now['source'],'raw_record':raw,
            'all_actual_subeffects':subs,'characters':uses[key],
            'fragment_before':old,'fragment_after':target,
            'other_fragments_retained':[f for f in now['fragments'] if f['t']!=FRAGMENTS[ident]],
            'native_evidence':['output/character_skills/skilllist_types/dispatch_map.json',
                'output/character_skills/skilllist_types/native_checks.json',
                'output/character_skills/review/p3b1_20261019_type8/REPORT.md#4',
                'output/character_skills/description_bindings/p3b2_type8/native_evidence.json'],
            'limits':'人工逐记录语义裁决；原值与原生规则支持局部贡献；不证明机器码解析日文、账号装载、最终战斗结果或旁句机制。'})
    accepted=[x for x in ledger if x['decision'].startswith('INCLUDED')]
    old_accepted=lines(args.before/'accepted_p3b1.jsonl')
    cids={p['cid'] for x in accepted for p in x['characters']}
    old_cids={p['cid'] for x in old_accepted for p in x['characters']}
    s0=C.load_json(args.before/'summary.json')
    s1=C.load_json(BASE/'profiles/summary.json')
    increment={'candidate_records':len(ledger),'included_records':len(accepted),'excluded_records':len(ledger)-len(accepted),
        'numeric_field_answers_added_pages':s1['totals']['rule_answers']-s0['totals']['rule_answers'],
        'numeric_field_answers_added_normalized_rows':s1['totals']['rule_answers_unique_records']-s0['totals']['rule_answers_unique_records'],
        'numeric_field_answers_added_parent_holder_keys':s1['totals']['rule_answers_parent_holder_keys']-s0['totals']['rule_answers_parent_holder_keys'],
        'fragments_unique_records_added':len(accepted),'fragments_page_references_added':sum(len(x['characters']) for x in accepted),
        'effect_slots_unique_records_added':sum(len(x['fragment_after']['binding']['fields']) for x in accepted),
        'effect_slots_page_references_added':sum(len(x['characters'])*len(x['fragment_after']['binding']['fields']) for x in accepted),
        'affected_cids':sorted(cids),'overlap_cids_with_p3b1':sorted(cids&old_cids),'new_cids_since_p3b1':sorted(cids-old_cids),
        'status_transitions':[{'cid':a['cid'],'before':a['status'],'after':b['status']} for a,b in zip(old_profiles,profiles) if a['status']!=b['status']],
        'before_totals':s0['totals'],'after_totals':s1['totals'],
        'strength':DB.STRENGTH,'independent_review_status':'P3B2_PENDING; P3B1 approved only its historical ten records'}
    C.write_jsonl(OUT/'candidate_decisions.jsonl',ledger)
    C.write_json(OUT/'increment.json',increment)
    C.write_csv(OUT/'candidate_decisions.csv',
        ['record_id','decision','reason','json_pointer','raw_sha256','fragment','bound_fields','cids'],
        [[x['record_id'],x['decision'],x['reason'],x['source']['json_pointer'],x['source']['raw_record_sha256'],
          x['target_fragment'],json.dumps(x['fragment_after'].get('binding',{}).get('fields',[]),ensure_ascii=False),
          ','.join(str(y['cid']) for y in x['characters'])] for x in ledger])
    print(json.dumps({k:v for k,v in increment.items() if k not in ['before_totals','after_totals']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
