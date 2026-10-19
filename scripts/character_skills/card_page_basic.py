"""Same-record basic-field presentation using the existing roster mappings."""
import importlib.util
import math
from pathlib import Path


def format_critical(value):return f'{float(value)*100:.6g}%'


def format_interval(value):
    number=f'{float(value):.6g}'
    if '.' not in number and 'e' not in number:number+='.0'
    return number+'秒/下'


def apply_basic_display(data,basic):
    path=Path(__file__).resolve().parents[1]/'build_char_roster.py'
    spec=importlib.util.spec_from_file_location('card_page_roster_mapping',path);roster=importlib.util.module_from_spec(spec);spec.loader.exec_module(roster)
    if not hasattr(data,'world_places'):
        import json
        source=data.decoded/'worldinfo.data5.json.raw'
        rows=json.loads(source.read_text(encoding='utf-8'))['chara_place'] if source.is_file() else []
        data.world_places={int(r['id']):(i,r['name']) for i,r in enumerate(rows)}
        home_source=data.decoded/'homelist.data5.json.raw'
        homes=json.loads(home_source.read_text(encoding='utf-8'))['homelist'] if home_source.is_file() else []
        data.home_names={int(r['home_id']):(i,r['name']) for i,r in enumerate(homes)}
        filter_path=data.base/'skilllist_types/filter_dictionary.json'
        data.home_filter=json.loads(filter_path.read_text(encoding='utf-8')).get('home',{}) if filter_path.is_file() else {}
    rec=basic['raw_record']
    for f in basic['fields']:
        key=f['key'];raw=f['raw_value'];present=f['raw_state'] not in ('missing','null')
        f['display_value']=raw if present else '外部/网站维护'
        f['formatting_basis']='同源原值，未跨CACHE/APK逐字段拼接'
        if key=='jobtype':
            f['display_value']=roster.JOB_NAMES.get(raw,'未知／外部/网站维护') if present else '未知／外部/网站维护'
            f['mapping_evidence']='推断（复用名册spmotname动作相关映射）' if present and raw in roster.JOB_NAMES else '未知'
            f['mapping_source']='scripts/build_char_roster.py:JOB_NAMES；output/char_roster/README.md'
            f['note']='职业名称：'+f['mapping_evidence']+'；原jobtype保留详情'
            if not present:f['note']='所选整条记录缺jobtype；未知，未从另一源补值'
        elif key=='home':
            chosen='home'
            raw=rec.get(chosen);f['raw_value']=raw;f['selected_field']=chosen
            f['selection_evidence']=dict(home_present='home' in rec,home=rec.get('home'),place_present='place' in rec,place=rec.get('place'))
            f['raw_state']='missing' if chosen not in rec else 'null' if raw is None else 'zero' if raw==0 else 'present'
            f['source']={**f['source'],'field':'/'+chosen}
            old_join_raw=raw if raw is not None else rec.get('place')
            old_match=data.world_places.get(old_join_raw)
            f['roster_geography_comparison']=dict(source_key='CACHE/worldinfo.data5.json.raw',json_pointer=f'/chara_place/{old_match[0]}' if old_match else None,
                                                 raw_join_value=old_join_raw,name=old_match[1] if old_match else None,meaning='旧名册地理join，仅作差异记录；不可作为home所属证据')
            match=data.home_names.get(raw)
            reviewed_name=data.home_filter.get('table',{}).get('ids',{}).get(str(raw))
            valid=bool(match and reviewed_name==match[1])
            f['display_value']=match[1] if valid else '未知／外部/网站维护'
            f['mapping_evidence']='确认（同源home原值＋homelist＋既有IsTargetHome证据）' if valid else '未知（缺字典或字典不一致）'
            f['mapping_source']=dict(source_key='CACHE/homelist.data5.json.raw',json_pointer=f'/homelist/{match[0]}' if match else None,
                                     original_file=(data.decoded/'homelist.data5.json.raw').relative_to(data.root).as_posix())
            f['mapping_review_evidence']=dict(path='output/character_skills/skilllist_types/filter_dictionary.json',json_pointer='/home',native_evidence=data.home_filter.get('native_evidence'),
                                             known_boundary=data.home_filter.get('known_boundary'),new_native_run=False)
            f['formatting_basis']='home按homelist.home_id/name查表；已有IsTargetHome读取home/battle_home的证据，不使用worldinfo地理ID拼接'
            f['note']='同源home='+str(raw)+'；'+f['mapping_evidence']+'；与旧名册地理表不是同一命名空间' if raw is not None else '所属home缺失或null；未知／外部/网站维护，不以place地理字段代替'
        elif key=='critical' and present and isinstance(raw,(int,float)) and not isinstance(raw,bool) and math.isfinite(raw):
            f['label']='暴击几率';f['display_value']=format_critical(raw);f['formatting_basis']='比例原值×100展示为百分比（展示约定）';f['note']='原值'+str(raw)+'；按比例×100展示'
        elif key=='atkspeed' and present and isinstance(raw,(int,float)) and not isinstance(raw,bool) and math.isfinite(raw):
            f['display_value']=format_interval(raw);f['label']='攻击基础名义间隔'
            f['raw_value_evidence']=f['evidence']
            f['unit_evidence']='推断（名义间隔展示约定）'
            f['formatting_evidence_level']='推断'
            f['formatting_basis']='按名义间隔展示约定标秒/下；原atkspeed数值确认与单位推断分列，不取倒数'
            f['formatting_evidence']=['scripts/chica_move_rules.py','output/card_comparison_cid30236/movement/README.md','output/card_comparison_cid30236/movement/trace.json']
            f['formatting_limits']=['既有局部检查手工将原卡atkspeed放入s0后执行乘算；未完整证明charainfo→BattleParam赋值链',
                                    '基础名义间隔，未含技能/动作修正，不代表实机命中节奏；本轮没有新native检查']
            f['note']='原值：确认；秒/下单位：推断（名义间隔展示约定）。既有夹具手工s0=原卡atkspeed，未全证charainfo→BattleParam赋值链；未含技能/动作修正，非实机命中节奏'
        elif key in ('growth','battle_home'):
            f['display_value']='外部/网站维护';f['note']='没有可靠成长枚举映射；原值保留详情' if key=='growth' else '本轮未启用战斗所属名称映射；原值保留详情'
        elif key in ('critical','atkspeed') and not present:
            f['note']='所选'+basic['layer']+'记录'+('缺失' if f['raw_state']=='missing' else '为null')+'；外部/网站维护，不跨源回填'
    return basic
