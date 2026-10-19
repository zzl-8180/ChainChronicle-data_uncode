"""R2 disclosure and pilot preparation; never generates a full roster."""
import argparse
import collections
import copy
import hashlib
import json
import time
from pathlib import Path

from card_page_data import Inputs,SAMPLES,canonical
from card_page_positions import fragment_positions
from card_page import build_card,page,validate,report
from card_page_basic import format_critical,format_interval,apply_basic_display
from card_page_cohorts import freeze


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def disclose(data,out):
    oldpages=data.base/'pages'
    cards={cid:json.loads((oldpages/str(cid)/'card.json').read_text(encoding='utf-8')) for cid in SAMPLES}
    specs=[(30338,'30338-special_move-special_move-pattern0-lvorder0-f2','INTENTIONAL_FALSE_POSITIVE_REJECTION',
            '原候选把我方攻击/固定防御/移动增益挂到敌方减益句；对象与方向不一致，拒绝假阳性，不能以数字吻合晋级'),
           (7229,'7229-ability-ability-skillid_1_-lvorder0-f0','CANDIDATE_PROMOTION_NOT_IMPLEMENTED',
            '已有param1/2/3字段规则候选，但未实现按原文条件及对象审核后导入推断层；不能把未实现说成全库没有hint'),
           (4009,'4009-special_move-special_move-skilltext-lvorder0-f0','GENERAL_MECHANISM_LAYER_NOT_IMPLEMENTED',
            '已有施法结束阈值caster._behaviorTime+30游戏秒规则；若列30这个数值应归A，不是B。可能的无数字B是“施法结束请求依赖行为时钟、与异常到期不同”；一般机制择句层未实现，所以当前仍C'),
           (7229,'7229-heroic-heroic-heroicskilllist_boss_pattern___cid-lvorder0-f0','ASSOCIATION_BOUNDARY_PRESERVED',
            '20秒为原文A；英雄技角色关联来自既有ID模式推断，未证明运行时装载/实际等级，字段关联仍未知'),
           (30338,'30338-sympathy-sympathy-sympathy_skill_info__id_30338__ability0-lvorder0-f0','CANDIDATE_PROMOTION_NOT_IMPLEMENTED',
            '原候选列出普通/技能攻击贡献+10%、45游戏秒等字段规则，但未审核其是否对应本句，候选集合也未覆盖原文所有攻防项；不是此句已适用答案。不能因30236同文有基线就跨记录升级')]
    boundaries=[]
    for cid,row_id,kind,reason in specs:
        found=[(s,r) for g in cards[cid]['groups'] for s in g['skills'] for r in s['rows'] if r['row_id']==row_id]
        if not found and cid==7229 and kind=='ASSOCIATION_BOUNDARY_PRESERVED':
            found=[(s,r) for g in cards[cid]['groups'] if g['group']=='heroic' for s in g['skills'][:1] for r in s['rows'][:1]]
        assert len(found)==1,(cid,row_id)
        skill,row=found[0];record=data.old.get(skill['old_rec_key'],{})
        oldf=next((f for f in record.get('fragments',[]) if canonical(f['t'])==canonical(row['japanese'])),{})
        boundaries.append(dict(cid=cid,row_id=row['row_id'],japanese=row['japanese'],row_class=row['row_class'],
                               numeric_evidence=row['numeric_evidence'],association_evidence=row['association_evidence'],
                               boundary_kind=kind,reason=reason,old_candidates=oldf.get('cands',[]),
                               existing_field_rules=[dict(table=e['table'],record_id=e['record_id'],answers=e['answers'],source=e['source'])
                                                     for e in skill['record_evidence'] if e['answers']],source=row['source']))
    duplicate_groups=[]
    for g in cards[30004]['groups']:
        for s in g['skills']:
            raw=s['record_evidence'][0]['raw_record'].get(s['text_field'],'')
            spans=fragment_positions(raw);assert [p['japanese'] for p in spans]==[r['japanese'] for r in s['rows']] or not s['rows']
            buckets=collections.defaultdict(list)
            for row,span in zip(s['rows'],spans):
                buckets[row['japanese']].append(dict(row_id=row['row_id'],
                       field_pointer=row['source']['field_json_pointer'],source_key=row['source']['source_key'],
                       **span,raw_field_sha256=hashlib.sha256(str(raw).encode('utf-8')).hexdigest()))
            for text,occurrences in buckets.items():
                if len(occurrences)>1:duplicate_groups.append(dict(cid=30004,group=g['group'],occurrence_count=len(occurrences),occurrences=occurrences))
    basic_conflict=dict(cid=7229,chosen_layer='CACHE',cache_critical_state='missing' if 'critical' not in data.cache_chara[7229] else 'present',
                        cache_critical=data.cache_chara[7229].get('critical'),apk_critical=data.apk_chara[7229].get('critical'),
                        action='保持CACHE缺失，主显示外部/网站维护；不回填APK0.0，更不补用户示例0.4',
                        formatting_example_0_4_cid=30236,example_actual_raw=data.cache_chara[30236].get('critical'))
    basic_conflict['source_records']=[]
    for layer,path in [('CACHE',data.decoded/'charainfo.data5.json.raw'),('APK',data.apk/'_mdCharacter.json')]:
        records=json.loads(path.read_text(encoding='utf-8'))['charainfo']
        index,record=next((i,r) for i,r in enumerate(records) if r['cid']==7229)
        basic_conflict['source_records'].append(dict(layer=layer,path=path.relative_to(data.root).as_posix(),json_pointer=f'/charainfo/{index}',
              fields={key:dict(state='missing' if key not in record else 'null' if record[key] is None else 'zero' if record[key]==0 else 'present',raw_value=record.get(key))
                      for key in ('critical','atkspeed','jobtype','home','place','growth','battle_home')}))
    result=dict(status='R2_PREPARATION_DISCLOSURE_NOT_REVIEW_APPROVAL',
                implementation_status=dict(skill_candidate_promotion_enabled=False,general_mechanism_layer_enabled=False,
                    message='推断层暂不启用（候选晋级未实现；有意保守的实际边界）',
                    B_zero_reason='无经实现入页的新增机制；不代表原数据没有机制，也不代表全库没有hint',
                    existing_baseline_mechanism_slot='仅既有逐描述基线可携非数值项；没有一般机制关联实现',
                    basic_job_name_mapping='职业枚举复用名册动作相关推断，独立于技能候选推断层'),
                boundaries=boundaries,critical_conflict=basic_conflict,duplicate_groups=duplicate_groups,
                dedup_method=dict(coordinates='原始decoded JSON字段字符串Unicode code point起止，不是文件字节；同时留clean span',
                    merge_key='cid+group+original_group+source_key+field_pointer+table+record_id+actual_level_state/value+actual_reference_slot+parent_record_hash+raw_span (never traversal ordinal)',
                    aliases='同一源位置、同一执行上下文的引用别名合并并保留alias引用；不同位置/档位/等级不合并',
                    proposed_impact='两个重复点各有两个不同raw span，应保留+2；预计旧384→387不变，实际11卡合并后另核'),
                no_skill_answer_or_evidence_upgrade=True)
    dump(out/'boundary_disclosure.json',result)
    text=['# R2前实际边界与位置方法披露','','推断层暂不启用（候选晋级未实现；有意保守的实际边界）。B0说明无经实现入页的新增机制，不代表全库无hint。','','7229：CACHE无critical；APK为0.0，均不支持0.4。按整条记录优先继续缺失，展示“外部/网站维护”，不跨源补值。30236 CACHE实际0.4可验证40%的展示约定。','', '## 可核边界','']
    for b in boundaries:text+=['- '+str(b['cid'])+' / '+b['row_id']+' / '+b['boundary_kind'],'  - '+b['japanese'],'  - '+b['reason']]
    text+=['','## 30004重复源位置','']
    for d in duplicate_groups:
        for p in d['occurrences']:text+=['- '+p['row_id']+'：'+p['field_pointer']+'，raw span '+str(p['raw_span'])+'；'+p['japanese']]
    text+=['','方法：以原始字段字符span定位；同源位置且同执行上下文别名合并，保留所有引用。此两处各两次位于不同源位置，保留+2；不同等级/执行档不按同文去重。旧384→387预计保持，等待实施验证。']
    (out/'boundary_disclosure.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--disclose-only',action='store_true')
    a=p.parse_args();root=a.input_root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    data=Inputs(root,SAMPLES);result=disclose(data,out)
    if a.disclose_only:
        print(json.dumps(dict(boundaries=len(result['boundaries']),duplicate_groups=len(result['duplicate_groups']),critical_conflict=result['critical_conflict']),ensure_ascii=True));return
    start=time.perf_counter();cards=[];checks=[]
    for cid in SAMPLES:
        card=build_card(data,cid);html=page(card);checks.append(validate(card,html))
        old=json.loads((data.base/'pages'/str(cid)/'card.json').read_text(encoding='utf-8'))
        def rows(c):return [r for g in c['groups'] for s in g['skills'] for r in s['rows']]
        oldrows=rows(old);newrows=rows(card);assert len(oldrows)==len(newrows)
        for before,after in zip(oldrows,newrows):
            assert before=={k:v for k,v in after.items() if k in before},(cid,before['row_id'],'semantic drift')
        for group in card['groups']:
            for skill in group['skills']:
                raw=skill['record_evidence'][0]['raw_record'].get(skill['text_field'],'')
                for row in skill['rows']:
                    lo,hi=row['source_position']['raw_span'];assert raw[lo:hi].replace('\\n','\n')==row['japanese']
        dump(out/'pages'/str(cid)/'card.json',card);(out/'pages'/str(cid)/'index.html').write_text(html,encoding='utf-8');cards.append(card)
    rep=report(cards,checks,time.perf_counter()-start,out/'pages')
    s=rep['summary'];assert [s[k]['count'] for k in ('A','whole_row_confirmed','original_A','C')]==[185,47,165,202]
    assert s['N_all']==387 and s['A_whole_row_unknown']['count']==138 and s['whole_row_inferred']['count']==0
    fields={c['cid']:{f['key']:f for f in c['basic']['fields']} for c in cards}
    assert fields[30236]['critical']['display_value']=='40%'
    assert fields[7229]['critical']['raw_state']=='missing' and fields[7229]['critical']['display_value']=='外部/网站维护'
    assert fields[7229]['atkspeed']['display_value']=='2.0秒/下'
    assert data.apk_chara[7229]['atkspeed']==2.0 and data.apk_chara[7229]['critical']==0.0
    assert fields[7229]['jobtype']['mapping_evidence'].startswith('推断')
    assert fields[7229]['home']['display_value']=='義勇軍' and fields[30236]['home']['display_value']=='湖都'
    assert fields[7229]['home']['mapping_source']['json_pointer']=='/homelist/0'
    for raw,expected in [({'home':4},'副都'),({'home':5},'聖都'),({'home':0},'未知／外部/网站维护'),({'place':4},'未知／外部/网站维护'),({'home':None,'place':5},'未知／外部/网站维护')]:
        probe=copy.deepcopy(cards[0]['basic']);probe['raw_record']=raw
        field=next(f for f in apply_basic_display(data,probe)['fields'] if f['key']=='home')
        assert field['display_value']==expected and field['raw_value']==raw.get('home')
    dump(out/'home_mapping_correction.json',dict(reason='旧roster worldinfo.chara_place是地理命名空间，不能据此确认home所属；仅新card_page基础映射改为已有homelist/IsTargetHome证据',
         examples=[dict(cid=cid,home=fields[cid]['home']) for cid in SAMPLES],skill_rows_and_metrics_unchanged=True,
         screenshot_comparison='7229本输入home1→義勇軍，不借截图改副都；旧worldinfo join1部聖都只留差异详情'))
    assert fields[7229]['battle_home']['raw_value']==0 and fields[7229]['battle_home']['display_value']=='外部/网站维护'
    assert fields[7229]['growth']['raw_value']==1 and fields[7229]['growth']['display_value']=='外部/网站维护'
    assert format_critical(0)=='0%' and format_critical(.4)=='40%' and format_interval(0)=='0.0秒/下'
    assert not sum(c['coverage']['same_position_aliases_merged'] for c in cards)
    manifest=freeze(root,out)
    dump(out/'validation.json',dict(status='IMPLEMENTATION_SELF_CHECK_NOT_INDEPENDENT_REVIEW',checks=checks,
         semantic_rows_unchanged=387,raw_span_roundtrips=387,alias_merge_count=0,distinct_repeat_groups_30004=2,
         dedup_identity_boundaries='Actual build_card alias/different slot/parent condition/level checks are in f1_f5_fixes/checks.json; no key==key substitute',
         critical_7229_same_record_missing=True,critical_zero_and_0_4_formats=True,interval_nominal_not_reciprocal=True,
         home_homelist_confirmed_and_not_geographic_place=True,home_missing_null_zero_boundaries=True,
         summary=rep['summary'],cohort_counts={k:len(v) for k,v in manifest['cohorts'].items()}))
    print(json.dumps(dict(output=str(out),summary=rep['summary'],cohorts={k:len(v) for k,v in manifest['cohorts'].items()},seconds=time.perf_counter()-start),ensure_ascii=True))


if __name__=='__main__':main()
