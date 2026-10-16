"""Field/description guide and layered coverage audit of existing master data.

Adds normalized auxiliary records; never edits the accepted E build or invents
units, player state, cross-table loader priority or unavailable device resources.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from export_master import compact, lookup, parse_records, strict_load, typed_value, write_json, write_lines

VERSION = 'field-guide-1.0'
CONFIRMED, INFERRED, UNKNOWN = '已确认', '推断', '未知'
HIGHHP = {
    'param0':('接受效果角色的HP比率下限，含等号','比率','原值×100得到百分比；判断接受者HP比例≥原值'),
    'param1':('攻击分支局部乘算贡献','无量纲乘数','乘以原值；(原值−1)×100仅为该局部乘数的名义变化'),
    'param2':('移动分支局部乘算贡献','无量纲乘数','乘以原值；不是所有移动修正后的最终速度'),
    'param3':('防御分支局部乘算贡献','无量纲乘数','乘以原值；不直接改称最终减伤百分比'),
    'param5':('暴击伤害分支局部加算贡献','局部系数','加原值；不直接改称最终伤害百分比'),
}
BASIC = {
    'cid':('角色定义ID','标识',CONFIRMED), 'name':('日文原名/记录名称','文本',CONFIRMED),
    'title':('日文称号','文本',CONFIRMED), 'text':('原始日文描述（含控制标记）','文本',CONFIRMED),
    'skillname':('必杀原名','文本',CONFIRMED), 'skilltext':('必杀原文描述','文本',CONFIRMED),
    'profile':('角色介绍原文','文本',CONFIRMED), 'illustrator':('画师字段','文本',INFERRED),
    'voice_artist':('声优字段','文本',INFERRED), 'cost':('编成Cost定义','Cost，显示含义待读取入口复核',INFERRED),
    'jobtype':('职业类型原始编码','枚举编码，中文标签未统一确认',INFERRED),
    'home':('所属原始编码','枚举编码，具体标签待确认',INFERRED),
    'rarity':('稀有度原始编码','枚举编码，星级换算未在此规则确认',INFERRED),
    'growth':('成长类型原始编码','编码，成长公式未知',INFERRED),
    'maxlv':('等级上限定义，非玩家当前等级','级，实际开放条件未知',INFERRED),
    'limit_break':('突破相关定义，非玩家当前突破','具体上限/规则待确认',INFERRED),
    'inihp':('HP基础配置候选，不是页面各等级HP','数值单位/成长组合未知',INFERRED),
    'iniap':('攻击基础配置候选，不是页面各等级ATK','数值单位/成长组合未知',INFERRED),
    'skill_cost':('必杀耗珠定义候选','珠数及修正待读取链确认',INFERRED),
    'lv':('嵌套定义的等级/档位标签，非玩家当前等级','原始字符串或数字；不自动换算MAX',INFERRED),
}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def csv_view(path, rows, columns):
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow([label for key,label in columns])
        for row in rows:
            values=[]
            for key,label in columns:
                value=row.get(key)
                if isinstance(value,(dict,list,tuple)): value=compact(value)
                elif value is None: value=''
                if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):value="'"+value
                values.append(value)
            writer.writerow(values)


def descendants(value,path=''):
    if isinstance(value,dict):
        for key,child in value.items():
            escaped=key.replace('~','~0').replace('/','~1')
            here=path+'/'+escaped
            yield here,child
            yield from descendants(child,here)
    elif isinstance(value,list):
        for index,child in enumerate(value):
            here=path+'/'+str(index)
            yield here,child
            yield from descendants(child,here)


def get_path(raw,path):
    result=raw
    for part in path.strip('/').split('/') if path else []:
        part=part.replace('~1','/').replace('~0','~')
        result=result[int(part)] if isinstance(result,list) else result[part]
    return result


def field_context(record,path):
    raw=record['raw'];first=path.split('/')[1] if '/' in path else ''
    regular=record['source_key'] in ('CACHE/skilllist.data5.json.raw','APK/_mdSkill.json')
    if regular:return f"daSkill/ability={raw.get('ability','MISSING')}"
    if record['table']=='charainfo':
        slots=raw.get('skillid',[])
        if first.startswith('skillparam'):
            return f"角色必杀/四槽类型={slots[0]}" if len(slots)==4 else '角色必杀/八槽角色未知'
        return f'角色定义/{len(slots)}槽'
    if record['table']=='bossskill' and first.startswith('skillparam'):
        return f"Boss技能/skillid0={raw.get('skillid0','MISSING')}（与普通技能ID分域）"
    return record['table']


def normalize_field_path(record,path):
    # Only the proven four-slot namespace is position-specific; all eight stay raw.
    if re.fullmatch('/skillid/[0-9]+',path) and record['table']=='charainfo': return path
    return re.sub(r'/\d+(?=/|$)','/*',path)


def meaning(record,path,active):
    field=path.rsplit('/',1)[-1]
    raw=record['raw'];context=field_context(record,path)
    result={'meaning_zh':'尚未确认；保留原始字段/位置','unit':None,'conversion':None,
            'status':UNKNOWN,'applicability':context,'evidence':['原记录字段及观察结构；字段名不单独证明机制']}
    regular=record['source_key'] in ('CACHE/skilllist.data5.json.raw','APK/_mdSkill.json')
    if regular and raw.get('ability')==1105 and field in HIGHHP and path=='/'+field:
        zh,unit,conversion=HIGHHP[field]
        result.update(meaning_zh=zh,unit=unit,conversion=conversion,status=CONFIRMED,
                      applicability='本APK ability1105；记录进入对应处理器后。资格/当前玩家状态另论',
                      evidence=['output/il2cpp/sample_code/PlayerManager_subAbilityApply_HighHPAll.txt@0x159321c',
                                'output/validation/high_hp_sample.json（既有32项局部实验）',
                                'output/phase_d/chain_probe.json（既有有模型安装/资格链）'])
    elif regular and field=='param4' and raw.get('ability')==1105:
        result['meaning_zh']='原始param4；本规则未确认其数值解释，不补缺失默认值'
    elif record['table']=='charainfo' and field.startswith('skillparam') and context=='角色必杀/四槽类型=116':
        binding=next((b for b in active['parameter_bindings'] if b['field']==field),None)
        if binding:
            labels={'skillparam0':'持续控制入参','skillparam1':'攻击触发间隔入参','skillparam2':'成功触发计数上限入参',
                    'skillparam3':'目标类型入参','skillparam4':'主攻击强度系数入参','skillparam5':'推力入参',
                    'skillparam6':'扩散范围入参','skillparam7':'扩散攻击强度系数入参','skillparam8':'命中延迟入参'}
            result.update(meaning_zh=labels[field],status=CONFIRMED,unit='次（Attack成功返回才递减）' if field=='skillparam2' else '枚举编码' if field=='skillparam3' else '函数入参；完整单位未确认',
                          conversion='fcvtzs转计数；不保证实际命中次数' if field=='skillparam2' else '32=TARGET_TYPE.oRANDOM' if field=='skillparam3' else '按原值传入；不推断世界单位/最终伤害',
                          applicability='本APK SKILL_TYPE.INTERVAL_FALL2=116攻击段；未推广其他必杀类型',
                          evidence=['output/sample/active_skill_trace.json',binding['code_path'],binding['meaning_limit']])
    elif regular and field=='skillid':
        result.update(meaning_zh='daSkill记录ID，与必杀类型编码分域',unit='标识，不换算',status=CONFIRMED,evidence=['daSkill.get@0x181be68；原记录唯一性/显式引用'])
    elif regular and field=='ability':
        result.update(meaning_zh='ABILITY_TYPE效果代码；枚举名不等于参数语义',unit='枚举编码',status=CONFIRMED,evidence=['output/il2cpp/sample_code.json/enums/ABILITY_TYPE'])
    elif regular and (path=='/sub' or path.startswith('/sub/')):
        result.update(meaning_zh='直接子效果ID的有序定义；保留重复，只展开原根一层',unit='ID数组或成员',status=CONFIRMED,evidence=['BattleParam.addSubAbility@0x10f8368；既有循环/共享项原生结构回归'])
    elif record['table']=='charainfo' and path=='/skillid/0' and len(raw.get('skillid',[]))==4:
        result.update(meaning_zh='四槽定义的必杀类型码，不能查同号被动技能',unit='类型编码',status=CONFIRMED,evidence=['output/sample/active_skill_trace.json；BattleParam.SetSkillList从索引1读能力定义'])
    elif record['table']=='charainfo' and path.startswith('/skillid/'):
        if len(raw.get('skillid',[]))==4:
            result.update(meaning_zh='四槽主表能力ID定义；不证明玩家已开放',unit='ID，0保留为空槽定义',status=CONFIRMED,evidence=['BattleParam.SetSkillList@0x11032fc；普通队员另读CardInfo.skillid'])
        else:result['meaning_zh']='八槽原始成员，槽位角色未知，完整保留'
    elif field in BASIC:
        zh,unit,status=BASIC[field]
        # A generic name is original text; context decides which entity it names.
        result.update(meaning_zh=zh,unit=unit,status=status,evidence=['实际表结构、原文及对应记录；编码显示/运行条件未自动确认'])
    elif field in ('skill_ids','sympathy_skill_ids') or '/skill_ids/' in path:
        result.update(meaning_zh='该辅助定义声明的技能ID列表/成员；加载入口未复核',unit='ID，保留顺序/重复',status=INFERRED,evidence=['辅助表字段及与daSkill记录ID匹配；不宣称运行时加载规则'])
    result['unit_status']=UNKNOWN if result['unit'] is None or any(word in result['unit'] for word in ('未知','未确认','待')) else result['status']
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-root',type=Path,default=Path('output/field_guide'))
    args=parser.parse_args()
    selected=strict_load(Path('output/export/latest.json').read_bytes());base=Path(selected['directory'])
    manifest=strict_load((base/'manifest.json').read_bytes());active=strict_load(Path('output/sample/active_skill_trace.json').read_bytes())
    inventory_path=Path('output/phone/inventory.jsonl')
    inventory=[strict_load(line) for line in inventory_path.open(encoding='utf-8')]
    collected=strict_load(Path('output/phone/collected_files.json').read_bytes())
    inputs={'formal_manifest':sha((base/'manifest.json').read_bytes()),'device_inventory':sha(inventory_path.read_bytes()),
            'active_trace':sha(Path('output/sample/active_skill_trace.json').read_bytes()),
            'collection_list':sha(Path('output/phone/collected_files.json').read_bytes()),
            'APK_component_JSON':sha(Path('output/base_master/ChronicleArchiveData.json').read_bytes()),
            'producer':sha(Path(__file__).read_bytes())}
    for file in ('output/unity/summary.json','output/unity/mono_summary.json',
                 'output/unity/mono_candidates.jsonl','output/unity/mono_errors.jsonl',
                 'output/field_guide/unity_header_gap_audit.json'):
        inputs[file]=sha(Path(file).read_bytes())
    output=args.output_root/('guide_'+sha(compact(inputs).encode())[:16])
    if output.exists():
        previous=strict_load((output/'manifest.json').read_bytes())
        for path,digest in previous['output_sha256'].items():assert sha((output/path).read_bytes())==digest,path
        write_json(args.output_root/'latest.json',{'directory':str(output),'manifest':str(output/'manifest.json')})
        write_root_readme(args.output_root,output)
        print(compact({'status':'EXISTING_GUIDE_VERIFIED','output':str(output)}));return
    output.mkdir(parents=True)
    (output/'unity_header_gap_audit.json').write_bytes(Path('output/field_guide/unity_header_gap_audit.json').read_bytes())
    all_records=[];supplemental=[];tables=[];sources={s['source_key']:s for s in manifest['sources']}
    for source in manifest['sources']:
        path=base/source['copied_file'];raw=path.read_bytes()
        assert sha(raw)==source['sha256']
        doc=strict_load(raw)
        arrays=[k for k,v in doc.items() if isinstance(v,list)]
        if source['source_key']=='CACHE/const.data5.json.raw':arrays=['@document']
        for table in arrays:
            if table=='@document':located=[(doc,{'json_pointer':'','ordinal_zero_based':0,'byte_begin':0,'byte_end_exclusive':len(raw),'raw_record_sha256':sha(raw)})]
            else:_,located=parse_records(raw,table)
            core=source.get('main_table')==table
            for value,location in located:
                record={'record_key':source['source_key']+'#'+location['json_pointer'],'source_key':source['source_key'],
                        'layer':source['layer'],'table':table,'location':location,'raw':value,
                        'snapshot_id':manifest['snapshot_id'],'original_file':source['input_file'],
                        'analysis_named_table':table=='@document','export_location':source.get('records_file') if core else 'supplemental_records.jsonl'}
                all_records.append(record)
                if not core:supplemental.append(record)
            tables.append({'source_key':source['source_key'],'source_file':source['input_file'],'layer':source['layer'],'table':table,
                           'expected_count':len(located),'expected_basis':'本已解码JSON数组边界' if table!='@document' else 'JSON根文档；@document为分析命名，不是游戏实体数',
                           'acquired_files':1,'decoded_files':1,'parsed_records':len(located),'exported_records':len(located),
                           'export_scope':'正式E逐记录JSONL' if core else '本轮补齐逐记录JSONL（原先已有完整JSON）',
                           'unparsed_records':0,'filtered_records':0,'failed_records':0,'unassociated_scope':'另见关联审计；结构解析不等于运行关联',
                           'meaning_scope':'按字典逐字段记录；未知不阻塞导出','gap_reason':None,'next_action':None,'needs_phone':False})
    by_key={r['record_key']:r for r in all_records}
    assert len(by_key)==len(all_records)
    write_lines(output/'supplemental_records.jsonl',supplemental)
    def row(layer,table,key,value,source_contains=None):
        matches=[r for r in all_records if r['layer']==layer and r['table']==table and isinstance(r['raw'],dict) and r['raw'].get(key)==value and (not source_contains or source_contains in r['source_key'])]
        if len(matches)!=1:raise ValueError((layer,table,key,value,len(matches)))
        return matches[0]
    cards=[r for r in all_records if r['table']=='charainfo'];skills=[r for r in all_records if r['source_key'] in ('CACHE/skilllist.data5.json.raw','APK/_mdSkill.json') and r['table']=='skilllist']
    indexes={layer:defaultdict(list) for layer in ('CACHE','APK')}
    for r in skills:indexes[r['layer']][r['raw']['skillid']].append(r)
    # First author actual examples, with raw text and translation stored separately.
    examples=[]
    card=row('CACHE','charainfo','cid',2327);root=row('CACHE','skilllist','skillid',40232705,'/skilllist.');child=row('CACHE','skilllist','skillid',40232706,'/skilllist.')
    contexts=defaultdict(list)
    for c in cards:
        slots=c['raw'].get('skillid',[])
        if len(slots)!=4:continue
        for ordinal,sid in enumerate(slots[1:],1):
            target=lookup(sid,'JSON_SNAPSHOT_WITH_APK_FALLBACK',indexes)
            if target['status']!='RESOLVED':continue
            key=target['candidates'][0]
            context={'cid':c['raw']['cid'],'name_ja':c['raw'].get('name'),'title_ja':c['raw'].get('title'),
                     'source':c['source_key'],'master_slot':ordinal,'status':'定义引用，不是玩家解锁/运行实例'}
            contexts[key].append(context)
            for sub in by_key[key]['raw'].get('sub',[]):
                found=lookup(sub,'JSON_SNAPSHOT_WITH_APK_FALLBACK',indexes)
                if found['status']=='RESOLVED':contexts[found['candidates'][0]].append({**context,'via_root':sid})
    def compare(effect,path,description=None,fragment=None,translation=None,kind='HighHPAll',card_contexts=None):
        description=description or effect
        value=get_path(effect['raw'],path);rule=meaning(effect,path,active)
        numeric=None;unit=rule['unit']
        if kind=='HighHPAll' and path=='/param0':numeric=value*100;unit='% HP（含等号）'
        elif kind=='HighHPAll' and path in ('/param1','/param2','/param3'):numeric=value;unit='局部乘数'
        elif kind=='HighHPAll' and path=='/param5':numeric=value;unit='局部加算系数'
        elif kind=='必杀116代码绑定':numeric=value
        entry={'example_kind':kind,'card_contexts':card_contexts if card_contexts is not None else contexts.get(effect['record_key'],[]),
               'client_version':manifest['APK_identity'],'snapshot_id':manifest['snapshot_id'],'source_layer':effect['layer'],
               'skill_id':effect['raw'].get('skillid') if effect['table']=='skilllist' else None,
               'active_type':116 if kind=='必杀116代码绑定' else None,
               'skill_name_ja':effect['raw'].get('skillname') if effect['table']=='charainfo' else effect['raw'].get('name'),
               'description_skill_id':description['raw'].get('skillid') if description['table']=='skilllist' else None,
               'description_skill_name_ja':description['raw'].get('skillname') if description['table']=='charainfo' else description['raw'].get('name'),
               'description_field_path':'/text' if 'text' in description['raw'] else '/skilltext' if 'skilltext' in description['raw'] else None,
               'effect_own_description_ja':effect['raw'].get('text',effect['raw'].get('skilltext')),
               'description_ja':description['raw'].get('text',description['raw'].get('skilltext')),
               'translation_zh':translation,'translation_scope':'仅所选效果片段人工释义；非游戏原始字段' if translation else '未翻译，保留原文',
               'effect_fragment_ja':fragment,'description_record_key':description['record_key'],
               'effect_record_key':effect['record_key'],'field_path':path,'field_pointer':effect['location']['json_pointer']+path,
               'raw_value':value,'interpretation_zh':rule['meaning_zh'],'interpreted_number':numeric,'unit':unit,'unit_status':rule['unit_status'],
               'conversion':rule['conversion'],'conditions':{'HighHPAll':'接受者HP达param0，双方存活；外层PLAYER/active为静态依据；当前实例未知'}.get(kind,'见具体记录/代码入参，未推定实际开放'),
               'target':'接受效果的角色；非被攻击目标' if kind=='HighHPAll' else None,'duration':None,
               'duration_status':'无已确认持续时间解释，不补值','status':rule['status'],
               'card_association_status':'已保留定义关联/明确样例上下文；非玩家实例' if (card_contexts if card_contexts is not None else contexts.get(effect['record_key'],[])) else '未建立可信卡牌关联，不能按名称猜测',
               'evidence':rule['evidence'],'description_link_status':'代码与显式记录关联支持；不靠描述顺序' if fragment else '未指定文案片段/文案未显示；字段解释来自代码',
               'not_final_battle_value':True}
        return entry
    selected_context=[{'cid':2327,'name_ja':card['raw']['name'],'title_ja':card['raw']['title'],'source':card['source_key'],'status':'主表定义，非玩家实例'}]
    for effect in (root,child):
        for key in HIGHHP:
            if key not in effect['raw']:continue
            fragment='HPが25%以上' if key=='param0' and effect is root else 'HPが50%以上' if key=='param0' else '攻撃力と移動速度とクリティカル威力が上がる' if key in ('param1','param2','param5') else None
            examples.append(compare(effect,'/'+key,root,fragment,'HP满足条件的友方获得攻击、移动和暴击威力提升；50%以上进一步增强。',card_contexts=selected_context))
    simple=row('CACHE','skilllist','skillid',143001,'/skilllist.')
    for key in ('param0','param1','param2','param3'):
        examples.append(compare(simple,'/'+key,fragment='HPが25%以上' if key=='param0' else '攻撃力(5%)が上がる' if key=='param1' else None,translation='战场上HP在25%以上的友方攻击力提高5%。'))
    for binding in active['parameter_bindings']:
        field=binding['field'];fragment='攻撃は15回まで継続する' if field=='skillparam2' else '一定間隔ごとにランダムで敵1体とその周囲' if field in ('skillparam1','skillparam3','skillparam4','skillparam6','skillparam7') else None
        examples.append(compare(card,'/'+field,card,fragment,'间隔性攻击随机敌人及其周围，攻击持续至15次计数；后续治疗/增益尚未追通。',kind='必杀116代码绑定',card_contexts=selected_context))
    extra=row('CACHE','extra_ability_info','cid',2327)
    for ordinal,tier in enumerate(extra['raw']['extra_abilities']):
        entry=compare(extra,f'/extra_abilities/{ordinal}/skill_ids',kind='Extra嵌套分档（只确认原始结构）',card_contexts=selected_context)
        entry.update(skill_name_ja=tier['name'],description_ja=tier['text'],effect_fragment_ja=tier['text'],
                     description_skill_name_ja=tier['name'],effect_own_description_ja=tier['text'],
                     description_field_path=f'/extra_abilities/{ordinal}/text',
                     tier_raw=tier['lv'],translation_zh='开战持有万象珠；同Chain下一次必杀的Chain威力提升量增加（具体百分比见原文）。',
                     translation_scope='同档原文人工释义；非游戏原始字段',
                     interpretation_zh='按cid及嵌套lv结构对应本档skill_ids；未确认每个数值参数与文案百分比的读取链',
                     interpreted_number=None,unit=None,unit_status=UNKNOWN,status=INFERRED,description_link_status='同一嵌套对象直接保存name/text/lv/skill_ids，不靠文案顺序',
                     evidence=[extra['record_key']+f'/extra_abilities/{ordinal}','数值说明为原文字段，不作倍率参数证明'])
        examples.append(entry)
    for layer in ('CACHE','APK'):
        conflict=row(layer,'skilllist','skillid',36000358,'/skilllist.' if layer=='CACHE' else None)
        examples.append(compare(conflict,'/param1',kind='来源冲突（参数单位未知）'))
    write_json(output/'record_comparisons_examples.json',examples)
    # Expand only the already verified ability1105 local field meanings.
    highhp=[]
    for effect in skills:
        if effect['raw'].get('ability')!=1105:continue
        description=effect
        if effect['record_key']==child['record_key']:description=root
        for field in HIGHHP:
            if field in effect['raw']:highhp.append(compare(effect,'/'+field,description))
    write_json(output/'record_comparisons_highhp.json',highhp)
    build_dictionary(output,all_records,active)
    build_references_and_audit(output,all_records,skills,cards,by_key,indexes,tables,inventory,collected,base,manifest)
    columns=[('example_kind','样例结构'),('card_contexts','卡牌ID日文名及定义来源JSON'),('client_version','客户端版本JSON'),
             ('skill_id','技能ID'),('active_type','必杀类型（不是技能ID）'),('skill_name_ja','效果记录日文名'),('effect_own_description_ja','效果记录自身原文'),
             ('description_skill_id','引用文案的技能ID'),('description_skill_name_ja','引用文案的技能名'),('description_ja','用于对照的原文描述'),
             ('translation_zh','中文释义'),('effect_fragment_ja','具体效果片段'),('effect_record_key','效果记录'),('field_pointer','原始字段位置'),
             ('raw_value','原始值JSON'),('interpretation_zh','数值解释'),('interpreted_number','解释数值'),('unit','单位'),('unit_status','单位确认状态'),('conversion','换算规则及限制'),
             ('conditions','条件'),('target','对象'),('duration','持续时间（空即未知）'),('status','确认状态'),('evidence','依据JSON')]
    csv_view(output/'record_comparisons_examples.csv',examples,columns)
    csv_view(output/'record_comparisons_highhp.csv',highhp,columns)
    guide={'version':VERSION,'formal_E_build':str(base),'formal_E_manifest_sha256':inputs['formal_manifest'],'inputs':inputs,
           'producer_sha256':inputs['producer'],'all_record_views':len(all_records),'supplemental_record_views':len(supplemental),
           'example_rows':len(examples),'highhp_rule_rows':len(highhp),'source_tables':tables,
           'limits':['未连接手机；77个旧清单data5中仅11个已取得，其他目标覆盖未证实',
                     '辅助表关联有推断层级；不将其升级为实际运行规则',
                     '不改正式E构建、原值、玩家状态或全局倍率；不把嵌套视图数当独立实体总数']}
    write_json(output/'manifest.json',guide)
    verify_guide(output,all_records,examples,highhp,base,manifest)
    make_readme(output,guide)
    guide['output_sha256']={p.relative_to(output).as_posix():sha(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='manifest.json'}
    write_json(output/'manifest.json',guide)
    write_json(args.output_root/'latest.json',{'directory':str(output),'manifest':str(output/'manifest.json')})
    write_root_readme(args.output_root,output)
    print(compact({'status':'PASS','output':str(output),'examples':len(examples),'HighHPAll_rows':len(highhp),'supplemental_records':len(supplemental)}))


def write_root_readme(root,output):
    (root/'README.md').write_text('# 字段对照与覆盖审计\n\n当前离线交付：['+output.name+'/README.md]('+output.name+'/README.md)。\n\n正式E构建保持不变；手机全量采集等待用户连接。\n',encoding='utf-8')


def build_dictionary(output,records,active):
    dictionary={};scope=defaultdict(set)
    for record in records:
        for path,value in descendants(record['raw']):
            context=field_context(record,path);normalized=normalize_field_path(record,path)
            identity=(record['source_key'],record['table'],context,normalized)
            scope[(record['source_key'],record['table'],context)].add(record['record_key'])
            if identity not in dictionary:
                dictionary[identity]={'source_file':record['original_file'],'source':record['layer'],'table':record['table'],
                                      'record_type':context,'field_path':normalized,'path_is_analysis_name':normalized!=path or record['analysis_named_table'],
                                      **meaning(record,path,active),'observed_types':Counter(),'occurrences':0,
                                      'examples':[],'example_locations':[],'record_keys':set()}
            item=dictionary[identity];item['occurrences']+=1;item['record_keys'].add(record['record_key'])
            item['observed_types'][type(value).__name__]+=1
            if len(item['examples'])<2 and all(typed_value(value)!=typed_value(v) for v in item['examples']):
                item['examples'].append(value);item['example_locations'].append({'record_key':record['record_key'],'pointer':record['location']['json_pointer']+path,'source_file':record['original_file']})
    rows=[]
    for identity,item in dictionary.items():
        item['records_with_field']=len(item.pop('record_keys'));item['records_in_context']=len(scope[identity[:3]])
        item['records_without_path']=item['records_in_context']-item['records_with_field']
        item['observed_types']=dict(item['observed_types'])
        item['path_convention']='JSON-pointer式路径，*为分析加入的数组成员通配；八槽仍保留原位置'
        rows.append(item)
    write_json(output/'field_dictionary.json',rows)
    csv_view(output/'field_dictionary.csv',rows,[('source_file','所属文件'),('source','来源'),('table','表'),('record_type','记录类型/效果条件'),
        ('field_path','原字段路径（*为分析通配）'),('meaning_zh','中文含义'),('examples','原始值示例JSON'),('observed_types','观察类型JSON'),
        ('unit','单位'),('unit_status','单位确认状态'),('conversion','换算规则'),('applicability','适用条件'),('status','含义确认状态'),('evidence','证据JSON'),
        ('records_with_field','含字段记录数'),('records_without_path','上下文内缺字段记录数'),('example_locations','示例定位JSON')])


def build_references_and_audit(output,records,skills,cards,by_key,indexes,tables,inventory,collected,base,manifest):
    refs=[];nested=[]
    domains={'character':('charainfo','cid'),'boss_pattern':('bosspattern','patternid'),
             'boss_skill':('bossskill','skillid'),'supporter':('supporterskill','ability_id')}
    domain_indexes={}
    for domain,(table,key) in domains.items():
        idx=defaultdict(list)
        for record in records:
            if record['table']==table and isinstance(record['raw'],dict) and type(record['raw'].get(key)) is int:
                idx[record['raw'][key]].append(record['record_key'])
        domain_indexes[domain]=idx
    def edge(parent,path,value,domain,confidence,reason):
        if type(value) is not int:
            result={'status':'INVALID_OR_UNCONFIRMED_ID_FORMAT','candidates':[]}
        elif value==0:
            result={'status':'ZERO_SENTINEL_PRESERVED','candidates':[]}
        elif domain=='skill':
            result=lookup(value,'JSON_SNAPSHOT_WITH_APK_FALLBACK',indexes)
        else:
            candidates=domain_indexes[domain].get(value,[])
            result={'status':'CANDIDATE_FOUND' if candidates else 'MISSING_CANDIDATE',
                    'candidates':candidates,'priority':'未知；不跨其他表推广daSkill优先级'}
        refs.append({'reference_key':parent['record_key']+path,'parent_record_key':parent['record_key'],
                     'source_layer':parent['layer'],'parent_table':parent['table'],'field_path':path,
                     'target_domain':domain,'id_raw':value,'association_status':confidence,
                     'basis':reason,'resolution':result,'runtime_activation':'UNKNOWN',
                     'scenario':'仅skill域使用假定JSON快照已装载的逐ID回退；其他域仅列候选、不选唯一值'})
    for parent in records:
        raw=parent['raw']
        if not isinstance(raw,dict):continue
        table=parent['table']
        if table in ('extra_ability_info','passive_info','leader_ability') and type(raw.get('cid')) is int:
            edge(parent,'/cid',raw['cid'],'character',INFERRED,'辅助定义显式cid与角色cid匹配；未验证加载入口')
        if table=='job_ability':
            for i,cid in enumerate(raw.get('cids',[])):edge(parent,f'/cids/{i}',cid,'character',INFERRED,'显式cids成员，保留序号')
        if table=='charainfo':
            for field in ('sup1','sup2'):
                if field in raw:edge(parent,'/'+field,raw[field],'supporter',INFERRED,'sup字段到supporterskill是待代码复核候选；不按同名拼接')
        if table in ('charainfo','denju'):
            for field,value in raw.items():
                if re.fullmatch(r'pattern\d+|patternid\d+',field):
                    edge(parent,'/'+field,value,'boss_pattern',INFERRED,'pattern字段与patternid候选关联；运行读取/优先级未证实')
        if table=='bosspattern':
            for field,value in raw.items():
                if re.fullmatch(r'skillid\d+',field):edge(parent,'/'+field,value,'boss_skill',INFERRED,'Boss pattern槽与Boss skill ID候选，分离普通技能命名空间')
        # Explicit skill ID declarations in auxiliary schemas; do not cast str0.
        is_aux=parent['source_key'] not in ('CACHE/skilllist.data5.json.raw','APK/_mdSkill.json') and table!='charainfo'
        if is_aux:
            for path,value in descendants(raw):
                if re.search(r'/(?:skill_ids|sympathy_skill_ids)/\d+$',path):
                    edge(parent,path,value,'skill',INFERRED,'辅助表声明的skill_ids；ID查询条件已知，加载语义仍待复核')
            if table=='supporterskill':
                for field,value in raw.items():
                    if re.fullmatch(r'abi\d+',field):edge(parent,'/'+field,value,'skill',INFERRED,'supporterskill.abi字段候选技能ID')
            if table=='sympathy_skill_info':
                for field,value in raw.items():
                    if re.fullmatch(r'ability\d+',field):edge(parent,'/'+field,value,'skill',INFERRED,'共鸣定义ability字段候选技能ID；不当成效果代码')
        for field in ('extra_abilities','passives'):
            if isinstance(raw.get(field),list):
                for i,value in enumerate(raw[field]):
                    nested.append({'analysis_record_key':parent['record_key']+f'/{field}/{i}',
                                   'analysis_naming':True,'parent_record_key':parent['record_key'],
                                   'source_key':parent['source_key'],'table':table+'.'+field,'ordinal':i,
                                   'relative_pointer':f'/{field}/{i}','parent_location':parent['location'],
                                   'location_scope':'父记录原始字节区间＋子项JSON pointer；未伪造独立字节偏移','raw':value})
    write_lines(output/'supplemental_references.jsonl',refs)
    write_lines(output/'supplemental_nested_records.jsonl',nested)
    incoming_confirmed=set();incoming_candidates=set()
    existing_counts=defaultdict(Counter)
    for line in (base/'references.jsonl').open(encoding='utf-8'):
        ref=strict_load(line)
        parent=by_key[ref['parent_record_key']]
        for scenario,resolution in ref['resolution'].items():
            incoming_confirmed.update(resolution['candidates'])
            existing_counts[(parent['source_key'],parent['table'],scenario)][resolution['status']]+=1
    for ref in refs:incoming_candidates.update(ref['resolution']['candidates'])
    unlinked=[]
    for record in skills:
        if record['record_key'] not in incoming_confirmed:
            unlinked.append({'record_key':record['record_key'],'layer':record['layer'],'skill_id':record['raw']['skillid'],
                             'name_ja':record['raw'].get('name'),'has_auxiliary_candidate_incoming':record['record_key'] in incoming_candidates,
                             'reason':'未在已验证四槽/sub图的任一场景找到入边；不等于废弃/未生效；辅助候选入边另列',
                             'raw_preserved_in':'正式E对应来源skilllist.jsonl'})
    write_lines(output/'unlinked_skill_records.jsonl',unlinked)
    for t in tables:
        selected_refs=[r for r in refs if by_key[r['parent_record_key']]['source_key']==t['source_key'] and r['parent_table']==t['table']]
        t['supplemental_reference_count']=len(selected_refs)
        t['reference_outcomes']=dict(Counter(r['resolution']['status'] for r in selected_refs))
        t['verified_E_reference_outcomes']={scenario:dict(existing_counts[(t['source_key'],t['table'],scenario)]) for scenario in ('APK_ONLY','JSON_SNAPSHOT_WITH_APK_FALLBACK')}
        t['unassociated_scope']='完整保留；候选关联与已验证图分别计数，不证明当前生效'
    for table in sorted({r['table'] for r in nested}):
        count=sum(r['table']==table for r in nested)
        tables.append({'source_file':'见parent_record_key','layer':'CACHE','table':table,'expected_count':count,
                       'expected_basis':'已解码父数组内嵌套项总数；不是独立文件/实体总数','parsed_records':count,'exported_records':count,
                       'unparsed_records':0,'filtered_records':0,'failed_records':0,'export_scope':'本轮嵌套视图；与父记录重叠，不与顶层相加',
                       'unassociated_scope':'见辅助引用图','gap_reason':'运行语义仍有未知','next_action':'按加载入口及对应处理器定向验证','needs_phone':False})
    acquired_by_remote={c['remote']:c for c in collected if c.get('status')=='COPIED'}
    data5=[r for r in inventory if PurePosixPath(r['path']).suffix.lower()=='.data5']
    other_files=[r for r in inventory if PurePosixPath(r['path']).suffix.lower() not in ('.data5','.bdl')]
    other_acquired=sum(r['path'] in acquired_by_remote and Path(acquired_by_remote[r['path']]['local']).is_file() for r in other_files)
    related={'denju_lblist.data5','crossworldabilitylist.data5','weaponlist.data5','runelist.data5','buffinfo.data5',
             'battleinfo.data5','various.data5','homelist.data5','motionlist.data5','enemyinfo.data5','beloved_item.data5'}
    resources=[]
    for item in data5:
        name=PurePosixPath(item['path']).name;acquisition=acquired_by_remote.get(item['path'])
        local=Path(acquisition['local']) if acquisition else None
        acquired=bool(local and local.is_file())
        matching=[s for s in manifest['sources'] if s['source_key']=='CACHE/'+name+'.json.raw']
        count=sum(t['parsed_records'] for t in tables if t.get('source_key')=='CACHE/'+name+'.json.raw') if matching else 0
        target_class='已取得的目标主数据' if acquired else '高优先目标缺件：必杀pattern候选' if name=='bossinfo.data5' else '相关候选（依文件名/已有字段推断）' if name in related else '未解码候选；不能仅凭名称排除或认定为目标'
        resources.append({'category':target_class,'source':'旧手机外部文件清单','file':name,'remote_path':item['path'],
                          'inventory_size':item['size'],'expected_files':1,'expected_record_count':None,
                          'expected_basis':'2026-10-14实际文件清单，只证明当时文件存在，不证明全游戏/当前版本记录总数',
                          'acquired_files':int(acquired),'decoded_files':int(bool(matching)),'parsed_records':count,'exported_records':count,
                          'local_source':str(local) if local else None,'unparsed_scope':None if matching else '尚未取得/解码，结构与记录数未知',
                          'gap_reason':None if acquired else '电脑无本地采集件；不是字段语义未知造成',
                          'next_action':None if acquired else '用户连接后全量只读采集files/cache到新快照，再逐文件解码、保留失败并按目标分类',
                          'needs_phone':not acquired})
    write_json(output/'phone_resource_inventory_audit.json',resources)
    csv_view(output/'phone_resource_inventory_audit.csv',resources,[('category','目标分类'),('file','文件'),('remote_path','旧清单路径'),('inventory_size','旧清单字节'),
        ('expected_files','清单预期文件数'),('expected_record_count','预期记录数（空=未知）'),('acquired_files','已取得文件数'),('decoded_files','已解码文件数'),
        ('parsed_records','已解析记录视图数'),('exported_records','已导出记录视图数'),('unparsed_scope','未解析范围'),('gap_reason','缺口原因'),('next_action','补齐动作'),('needs_phone','需要手机')])
    coverage=list(tables)
    unity=strict_load(Path('output/unity/summary.json').read_bytes())
    mono=strict_load(Path('output/unity/mono_summary.json').read_bytes())
    gaps=strict_load(Path('output/field_guide/unity_header_gap_audit.json').read_bytes())
    candidates=[strict_load(line) for line in Path('output/unity/mono_candidates.jsonl').open(encoding='utf-8')]
    assert gaps['count']==mono['errors'] and gaps['all_null_script'] and gaps['sizes']==[32]
    coverage.extend([
        {'source_file':'output/unity/summary.json; output/unity/objects.jsonl','layer':'APK','table':'Unity对象元信息（不是目标实体数）',
         'expected_count':unity['objects'],'expected_basis':'已有容器扫描的对象目录边界；复用A阶段结果，未重新批量提取',
         'acquired_files':1,'parsed_records':unity['objects'],'exported_records':unity['objects'],
         'filtered_records':0,'failed_records':unity['errors'],
         'gap_reason':'元信息成功不等于对象字段均已解析或目标分类完备','next_action':'按加载依赖及下面的错误保留记录定向检查','needs_phone':False},
        {'source_file':'output/unity/textassets.jsonl','layer':'APK','table':'TextAsset已提取对象',
         'expected_count':unity['textassets'],'expected_basis':'已有Unity目录TextAsset对象计数',
         'parsed_records':unity['textassets'],'exported_records':unity['textassets'],'filtered_records':0,'failed_records':0,
         'gap_reason':'不是全部结构化目标；其他MonoBehaviour和外部主表分别审计','needs_phone':False},
        {'source_file':'output/unity/mono_summary.json; output/field_guide/unity_header_gap_audit.json','layer':'APK','table':'MonoBehaviour头及脚本类识别',
         'expected_count':mono['headers'],'expected_basis':'已有MonoBehaviour目录边界；本轮只针对原19个异常对象读取',
         'parsed_records':mono['headers']-mono['errors'],'exported_records':mono['headers'],'filtered_records':0,'failed_records':mono['errors'],
         'unparsed_records':mono['errors'],'gap_reason':'19项都是32字节且脚本指针为空；保留原错误及608字节原始内容，不计成功解析的游戏记录',
         'next_action':'已补齐错误分类与原值；没有证据表明是目标缺件，不为此重采手机','needs_phone':False},
        {'source_file':'output/unity/mono_candidates.jsonl','layer':'APK','table':'按类名选出的MonoBehaviour候选（目标性质未确认）',
         'expected_count':len(candidates),'expected_basis':'原脚本类名筛选结果，非可信全量目标索引',
         'parsed_records':sum(r['full_read_status']=='READABLE' for r in candidates),
         'exported_records':len(candidates),'filtered_records':0,'failed_records':sum(r['full_read_status']=='FAILED' for r in candidates),
         'gap_reason':'6个AssetBundleLoader可完整读取；2个ChroSkillParameterView及1个CharaDetailSkill字段读取失败，已有原二进制保留，尚未证实含目标主记录',
         'next_action':'有加载依赖证据再定向解析这3项；不把界面对象当主表或要求先还原全部字段','needs_phone':False},
        {'source_file':'output/phone/inventory.jsonl','layer':'PHONE_OLD_INVENTORY','table':'全部data5候选文件','expected_count':len(data5),'expected_basis':'旧手机清单，不是目标主表/全游戏索引',
         'acquired_files':sum(r['acquired_files'] for r in resources),'decoded_files':sum(r['decoded_files'] for r in resources),
         'unparsed_records':None,'failed_records':None,'unassociated_scope':'未采文件结构及ID覆盖未知',
         'gap_reason':f"{len(data5)-sum(r['acquired_files'] for r in resources)}个data5尚未取得；不能称手机目标资源已全部取得",
         'next_action':'用户连接后全量采集files/cache，旧批次不覆盖','needs_phone':True},
        {'source_file':'output/phone/inventory.jsonl','layer':'PHONE_OLD_INVENTORY','table':'bdl容器（目标比例未知）',
         'expected_count':sum(PurePosixPath(r['path']).suffix.lower()=='.bdl' for r in inventory),'expected_basis':'旧目录文件计数；不能把所有bdl都当媒体或都当目标',
         'acquired_files':0,'decoded_files':0,'unparsed_records':None,'exported_records':0,
         'gap_reason':'未批量采集或识别容器内容；本项目不以图片音频为必须目标，但尚不能排除容器内结构化目标',
         'next_action':'全量采集后优先索引/加载依赖/结构化对象，不批量导出无关媒体','needs_phone':True},
        {'source_file':'output/phone/inventory.jsonl','layer':'PHONE_OLD_INVENTORY','table':'其他后缀/无后缀文件（目标性质未穷尽）',
         'expected_count':len(other_files),'expected_basis':'旧完整文件清单排除data5与bdl后的剩余边界，含元数据、版本及广告缓存候选，不凭名称全部排除',
         'acquired_files':other_acquired,'decoded_files':None,'parsed_records':None,'exported_records':None,'failed_records':None,
         'gap_reason':'已取元数据/版本文件用于技术分析；其余未取得，记录数与目标意义未知，不将技术文件数当游戏记录数',
         'next_action':'外部files/cache全量采集后按实际格式/加载证据分类；完整原路径仍在旧inventory.jsonl','needs_phone':True},
        {'source_file':'work/apk/assets/chronicle.dat','layer':'APK','table':'ChronicleArchiveData主表字段','expected_count':4,
         'expected_basis':'已解码组件实际_mdCharacter/_mdSkill/_mdBossInfo/_mdSAbirity四字段，检查无遗漏',
         'acquired_files':1,'decoded_files':1,'parsed_records':4,'exported_records':4,'filtered_records':0,'failed_records':0,
         'gap_reason':None,'next_action':None,'needs_phone':False},
        {'source_file':'output/unity/objects.jsonl','layer':'APK','table':'其他Unity对象的目标分类','expected_count':None,
         'expected_basis':'对象元信息不是全目标语义索引；已提取23个TextAsset，不证明所有MonoBehaviour目标均识别',
         'gap_reason':'未取得证明全游戏角色/技能完整覆盖的可信索引；教程/测试数据不自动当生产主表',
         'next_action':'按实际加载依赖定向检查现有对象；无需重新从APK扫描开始','needs_phone':False},
        {'source_file':None,'layer':'PHONE_PRIVATE_OR_SERVER','table':'私有目录/未下载/服务端独有目标','expected_count':None,
         'expected_basis':'无可信全量依据；没有文件不能证明服务端独有','gap_reason':'未采私有目录，权限能力未证实；当前手机不可用',
         'next_action':'先做已授权的外部files/cache全量采集；实际缺件再说明最小操作，不自动Root','needs_phone':True},
    ])
    write_json(output/'coverage_audit.json',coverage)
    csv_view(output/'coverage_audit.csv',coverage,[('layer','来源'),('source_file','文件/依据'),('table','数据类别/表'),('expected_count','预期数量（空=未知）'),
        ('expected_basis','预期依据'),('acquired_files','已取得文件数'),('decoded_files','已解码文件数'),('parsed_records','已解析记录/视图数'),
        ('exported_records','已导出记录/视图数'),('unparsed_records','未解析数（空=未知）'),('filtered_records','过滤数'),('failed_records','失败数（空=未知）'),
        ('unassociated_scope','未关联范围'),('reference_outcomes','辅助候选关联结果JSON'),('verified_E_reference_outcomes','原E已验证图结果JSON'),
        ('gap_reason','缺口原因'),('next_action','补齐动作'),('needs_phone','需要手机')])
    unresolved=[r for r in refs if r['resolution']['status'] in ('MISSING_ID','MISSING_CANDIDATE','INVALID_OR_UNCONFIRMED_ID_FORMAT')]
    write_lines(output/'unresolved_auxiliary_references.jsonl',unresolved)
    csv_view(output/'unresolved_auxiliary_references.csv',unresolved,[('parent_record_key','父记录'),('field_path','原字段位置'),('target_domain','候选目标命名空间'),
        ('id_raw','原ID'),('association_status','关联确认状态'),('resolution','候选查询结果JSON'),('basis','依据')])
    aux=[r for r in records if r['export_location']=='supplemental_records.jsonl']
    index_rows=[{'record_key':r['record_key'],'source':r['source_key'],'table':r['table'],'cid':r['raw'].get('cid'),
                 'id_raw':r['raw'].get('denju_id',r['raw'].get('ability_id',r['raw'].get('skillid',r['raw'].get('patternid',r['raw'].get('_id'))))),
                 'name_ja':r['raw'].get('name',r['raw'].get('sname')),'description_ja':r['raw'].get('text',r['raw'].get('stext')),
                 'pointer':r['location']['json_pointer']} for r in aux]
    csv_view(output/'supplemental_record_index.csv',index_rows,[('source','来源文件'),('table','表'),('record_key','记录键'),('cid','显式cid'),('id_raw','原标识（按表分域）'),
        ('name_ja','原名称'),('description_ja','原文'),('pointer','JSON pointer')])
    nested_index=[{'key':r['analysis_record_key'],'parent':r['parent_record_key'],'cid':by_key[r['parent_record_key']]['raw'].get('cid'),
                   'lv':r['raw'].get('lv'),'name':r['raw'].get('name'),'text':r['raw'].get('text'),'skill_ids':r['raw'].get('skill_ids')} for r in nested]
    csv_view(output/'nested_definition_view.csv',nested_index,[('cid','定义cid'),('lv','原档位'),('name','原名称'),('text','原文'),('skill_ids','原skill_ids JSON'),('parent','父记录'),('key','分析命名位置键')])
    patterns=[r for r in refs if r['target_domain']=='boss_pattern' and r['id_raw'] in (40232700,40232701,40232702)]
    summary={'formal_E_counts':manifest['record_counts'],'formal_E_reference_counts':manifest['reference_counts'],
             'top_level_table_views':sum(not t['table'].startswith(('extra_ability_info.','passive_info.')) for t in tables),
             'nested_table_views':2,'supplemental_reference_count':len(refs),
             'supplemental_reference_outcomes':dict(Counter(r['resolution']['status'] for r in refs)),
             'skill_no_confirmed_incoming':dict(Counter(r['layer'] for r in unlinked)),
             'skill_no_confirmed_or_candidate_incoming':dict(Counter(r['layer'] for r in unlinked if not r['has_auxiliary_candidate_incoming'])),
             'nested_views':len(nested),'phone_data5_in_old_inventory':len(data5),'phone_data5_collected':sum(r['acquired_files'] for r in resources),
             'phone_inventory_files':len(inventory),'phone_other_files':len(other_files),'phone_other_acquired':other_acquired,
             'phone_suffix_counts':dict(Counter(PurePosixPath(r['path']).suffix.lower() or '(无后缀)' for r in inventory)),
             'phone_data5_uncollected':len(data5)-sum(r['acquired_files'] for r in resources),
             'sample_active_pattern_candidates':patterns,'phone_next_step':'用户已要求连接后全量导出可访问的外部files/cache，而非只补bossinfo；当前等待连接',
             'missing_skill_candidate_ids':sorted({r['id_raw'] for r in unresolved if r['resolution']['status']=='MISSING_ID'}),
             'missing_skill_candidate_reason':'候选关联45次不等于45个缺件；需先核实辅助加载命名空间/快照一致性。资源缺失、版本不同步均为待验证解释',
             'whole_game_coverage':'UNKNOWN; do not compute a percentage',
             'duplicate_historical_placeholder_policy':'不默认删除；每来源每位置保留。无入边不证明无效/历史/占位；不按同名合并',
             'semantic_policy':'未知字段仍完整导出；补充图有推断状态，原始E已验证图保持不变'}
    write_json(output/'audit_summary.json',summary)


def verify_guide(output,records,examples,highhp,base,manifest):
    checks=[]
    sources={s['source_key']:s for s in manifest['sources']}
    grouped=defaultdict(list)
    for record in records:grouped[record['source_key']].append(record)
    for source_key,rows in grouped.items():
        source=sources[source_key];raw=(base/source['copied_file']).read_bytes();doc=strict_load(raw)
        for record in rows:
            loc=record['location'];sliced=raw[loc['byte_begin']:loc['byte_end_exclusive']]
            assert sha(sliced)==loc['raw_record_sha256']
            assert typed_value(strict_load(sliced))==typed_value(record['raw'])
            assert typed_value(get_path(doc,loc['json_pointer']))==typed_value(record['raw'])
    checks.append('All normalized main/aux records match original decoded UTF8 slices and JSON pointers')
    component=strict_load(Path('output/base_master/ChronicleArchiveData.json').read_bytes())
    fields=[k for k in component if k.startswith('_md')]
    assert set(fields)=={'_mdCharacter','_mdSkill','_mdBossInfo','_mdSAbirity'}
    for field in fields:
        exported=next(s for s in manifest['sources'] if s['source_key']=='APK/'+field+'.json')
        assert typed_value(component[field])==typed_value(strict_load((base/exported['copied_file']).read_bytes()))
    checks.append('All four component master fields fully match exported APK documents; not a whole-APK/global-game claim')
    by_key={r['record_key']:r for r in records}
    for row in examples+highhp:
        record=by_key[row['effect_record_key']]
        assert typed_value(get_path(record['raw'],row['field_path']))==typed_value(row['raw_value'])
        if row['description_field_path']:
            assert get_path(by_key[row['description_record_key']]['raw'],row['description_field_path'])==row['description_ja']
        if row['effect_fragment_ja']:assert row['effect_fragment_ja'] in row['description_ja']
        if row['example_kind']=='HighHPAll':assert record['raw']['ability']==1105 and row['field_path'][1:] in HIGHHP
        if row['example_kind']=='来源冲突（参数单位未知）':assert row['status']==UNKNOWN and row['interpreted_number'] is None
    checks.append('Example fragments are exact source substrings; field meanings bound to type/code evidence, not text order')
    assert len({r['effect_record_key'] for r in highhp})==34
    assert all(r['field_path']!='/param4' for r in highhp)
    for line in (output/'supplemental_nested_records.jsonl').open(encoding='utf-8'):
        r=strict_load(line);assert typed_value(get_path(by_key[r['parent_record_key']]['raw'],r['relative_pointer']))==typed_value(r['raw'])
    checks.append('Only34 existing HighHPAll records receive expanded local mappings; nested tier views match parents without defaults')
    dictionary=strict_load((output/'field_dictionary.json').read_bytes())
    for item in dictionary:
        if item['field_path']=='/param1' and item['record_type']!='daSkill/ability=1105':assert item['status']==UNKNOWN
        assert item['status'] in (CONFIRMED,INFERRED,UNKNOWN)
    checks.append('Same parameter names separated by table/type; other effect param1 remains unknown')
    supplemental=[strict_load(l) for l in (output/'supplemental_records.jsonl').open(encoding='utf-8')]
    core_count=manifest['record_count'];assert len(records)==core_count+len(supplemental)
    for file,expected in [('record_comparisons_examples.csv',len(examples)),('record_comparisons_highhp.csv',len(highhp)),('field_dictionary.csv',len(dictionary))]:
        with (output/file).open(encoding='utf-8-sig',newline='') as stream:assert sum(1 for _ in csv.DictReader(stream))==expected
    for file,data in [('coverage_audit.csv','coverage_audit.json'),('phone_resource_inventory_audit.csv','phone_resource_inventory_audit.json')]:
        with (output/file).open(encoding='utf-8-sig',newline='') as stream:assert sum(1 for _ in csv.DictReader(stream))==len(strict_load((output/data).read_bytes()))
    for file,data in [('supplemental_record_index.csv','supplemental_records.jsonl'),('nested_definition_view.csv','supplemental_nested_records.jsonl'),('unresolved_auxiliary_references.csv','unresolved_auxiliary_references.jsonl')]:
        with (output/file).open(encoding='utf-8-sig',newline='') as stream:assert sum(1 for _ in csv.DictReader(stream))==sum(1 for _ in (output/data).open(encoding='utf-8'))
    checks.append('Every parsed top-level record has E or supplemental output; CSV/JSON row counts reconcile')
    auxiliary=[strict_load(l) for l in (output/'supplemental_references.jsonl').open(encoding='utf-8')]
    assert len({r['reference_key'] for r in auxiliary})==len(auxiliary)
    for ref in auxiliary:
        assert get_path(by_key[ref['parent_record_key']]['raw'],ref['field_path'])==ref['id_raw']
        assert all(key in by_key for key in ref['resolution']['candidates'])
        assert ref['association_status']==INFERRED
    audit=strict_load((output/'audit_summary.json').read_bytes())
    assert sum(audit['supplemental_reference_outcomes'].values())==len(auxiliary)
    assert audit['phone_data5_collected']+audit['phone_data5_uncollected']==audit['phone_data5_in_old_inventory']
    assert audit['phone_data5_in_old_inventory']==77 and audit['phone_data5_collected']==11
    assert sum(audit['phone_suffix_counts'].values())==audit['phone_inventory_files']
    assert audit['phone_data5_in_old_inventory']+audit['phone_suffix_counts']['.bdl']+audit['phone_other_files']==audit['phone_inventory_files']
    for source in manifest['sources']:
        assert sha((base/source['copied_file']).read_bytes())==source['sha256']
    checks.append('Auxiliary references preserve exact paths/counts and inferred status; phone77/11/66 are file counts, not game coverage')
    gaps=strict_load((output/'unity_header_gap_audit.json').read_bytes())
    old_errors=[strict_load(line) for line in Path('output/unity/mono_errors.jsonl').open(encoding='utf-8')]
    assert {(r['asset_file'],r['path_id']) for r in gaps['rows']}=={(r['asset_file'],r['path_id']) for r in old_errors}
    assert gaps['source_sha256']==strict_load(Path('output/unity/summary.json').read_bytes())['sha256']
    for item in gaps['rows']:
        raw=bytes.fromhex(item['raw_hex'])
        assert len(raw)==item['byte_size']==32 and sha(raw)==item['sha256']
        assert item['script_path_id']==0 and item['original_error']
    checks.append('All19 prior Unity header failures retain exact object identities,608 raw bytes and original errors; not counted as typed gameplay success')
    write_json(output/'checks.json',{'status':'PASS','checks':checks,'main_records_unchanged':core_count,
                                   'normalized_record_views':len(records),'supplemental_record_views':len(supplemental),
                                   'example_rows':len(examples),'HighHPAll_rows':len(highhp),'dictionary_rows':len(dictionary),
                                   'phone_connected':False,'formal_E_build_unchanged':True})


def make_readme(output,guide):
    audit=strict_load((output/'audit_summary.json').read_bytes())
    checks=strict_load((output/'checks.json').read_bytes())
    dictionary=strict_load((output/'field_dictionary.json').read_bytes())
    states=dict(Counter(r['status'] for r in dictionary))
    text=f'''# 字段、原文与覆盖审计：离线交付

2026-10-15。依据正式E构建`build_261ac189c316abba`及现有代码证据。未改正式E构建或独立审查报告。手机当前无法连接；用户已要求连接后全量采集可访问的游戏外部files/cache，本次没有把待采资源写成已取得。

## 文件入口

- 字段字典：[CSV](field_dictionary.csv) / [JSON](field_dictionary.json)，{checks['dictionary_rows']}项，按来源、表、效果/类型、字段路径区分。状态计数{compact(states)}，不是全游戏字段解释率。`*`是数组成员的分析通配；示例另保留真实JSON pointer。
- 实际样例：[CSV](record_comparisons_examples.csv) / [JSON](record_comparisons_examples.json)，{guide['example_rows']}行，含根/子效果、单条HighHP、必杀116、Extra嵌套分档和来源冲突。
- 已验证规则扩展：[CSV](record_comparisons_highhp.csv) / [JSON](record_comparisons_highhp.json)，34条HighHPAll、{guide['highhp_rule_rows']}行存在字段；不补param4、不执行统一战斗求值。
- 覆盖审计：[CSV](coverage_audit.csv) / [JSON](coverage_audit.json)。手机候选逐文件清单：[CSV](phone_resource_inventory_audit.csv) / [JSON](phone_resource_inventory_audit.json)。
- 本轮补齐数据：[辅助逐记录JSONL](supplemental_records.jsonl)、[筛选索引CSV](supplemental_record_index.csv)，{guide['supplemental_record_views']}个顶层记录/文档视图；包含APK Boss pattern/skill、传授、Class/Extra/Leader、羁绊/共鸣等。
- [嵌套定义JSONL](supplemental_nested_records.jsonl) / [嵌套阅读CSV](nested_definition_view.csv)，{audit['nested_views']}项Extra/被动分档视图。与父记录重叠，不相加作为实体数。
- [辅助候选引用](supplemental_references.jsonl)、[未解析候选CSV](unresolved_auxiliary_references.csv) / [JSONL](unresolved_auxiliary_references.jsonl)、[无已验证入边技能](unlinked_skill_records.jsonl)。关联状态与查询结果分开，不代表生效。
- [数量汇总](audit_summary.json)、[结构核对](checks.json)、[来源及版本清单](manifest.json)。
- [APK原19项头部异常的定向原值核对](unity_header_gap_audit.json)：19项均为32字节空脚本指针；保留错误与608字节，不计入成功解析主记录。既有9个类名候选中6项可完整读取，另3项字段读取失败，原二进制仍在原Unity提取目录；不能将元信息扫描成功等同于所有对象目标均识别。

## 先读这几种样例

|记录与文案|原字段|可确认解释|
|---|---|---|
|cid2327根40232705：HPが25%以上|param0=0.25|接受者HP≥25%，含等号；由处理器比较证明|
|同根：攻撃力…が上がる|param1=1.15|局部攻击分支乘×1.15，名义+15%；文案没给倍率，证据来自代码|
|sub40232706，对应根文案HPが50%以上|param0=0.5、param1=1.05|靠根sub[0]及同处理器关联；子项自身调试文案与引用的父文案分别保存|
|143001原文攻击(5%)|param1=1.05|有文案数值，也有ability1105代码支持；不是仅凭文字推公式|
|cid2327必杀116：攻撃は15回まで継続する|skillparam2=15|成功Attack返回后递减的计数控制，不保证15次命中；116不是被动skilllist ID|
|Extra的lv=1/2/3/4/MAX|同嵌套对象name/text/lv/skill_ids|分档原文32/34/36/38/40%可读取；对应参数的执行链仍未知，不强行把str0数字串当ID|
|36000358两来源|APK param1=300.0；缓存400|保留冲突；参数单位未知，不补成300%/400%，不选当前唯一生效值|

原文、效果片段、中文释义、字段数值解释分列；中文只译选定片段，不伪装游戏原始字段。没有可靠卡牌关联时明确留空/未知，不按名称拼接。持续时间/单位未确认时保留空值及限制。

CSV使用UTF-8 BOM；复杂列是JSON文本，空单元格表示无已确认值，请回JSON区分缺失/null/空串。以公式控制字符开头的字符串在CSV前加单引号防止表格执行，JSON保留原始类型和值；CSV仅作追溯阅读视图。

## 审计结论分六层

1. **资源取得**：旧手机清单共{audit['phone_inventory_files']}个文件：77个data5，已取得11个，另66个没有本地采集件。77是旧清单文件数，不是77张目标表；未解码文件的目标性质/记录数不能凭名字确定。另有68451个bdl未逐件取得/识别，不能全当媒体或全当目标；其余{audit['phone_other_files']}个其他后缀/无后缀文件已取{audit['phone_other_acquired']}个技术文件，未采部分也未默认为非目标。三组计数与原清单总数核对。私有/未下载/服务端范围未知。
2. **识别解码**：已取得11个data5均有完整解码证据；APK ChronicleArchiveData四个主字段与分表完整比对。没有重新从APK开始分析。所有APK其他对象是否还含目标，尚无完整语义索引证明。
3. **解析**：本离线范围内共有{guide['all_record_views']}个顶层记录/文档视图，包含原E的38849条核心记录及新增辅助视图。const根文档属于分析视图，非游戏实体。
4. **导出**：这些已解码视图全部有正式E或本轮JSONL出口；原字段、类型、嵌套、位置、顺序、重复及缺失/null/0保留，过滤/失败为0。完整来源JSON也仍在正式E内。
5. **关联**：原E已验证四槽/sub图保持不变；本轮{audit['supplemental_reference_count']}条辅助候选关系均按原字段位置保存，结果{compact(audit['supplemental_reference_outcomes'])}。45条缺候选技能引用来自3条Extra定义，只有9个不同ID；加载命名空间和快照一致性未完全证实，不能直接认定为45个资源缺件。未在已验证图中有入边的技能计数{compact(audit['skill_no_confirmed_incoming'])}；计入辅助候选后仍无已知入边计数{compact(audit['skill_no_confirmed_or_candidate_incoming'])}。都保留，不推断废弃或删除。
6. **解释**：已确认规则只在对应结构启用；其他效果、八槽角色、成长计算、完整治疗/增益、单位、玩家解锁/当前版本/最终倍率仍有未知。字段未知不等于未提取。

样本2327的pattern0=40232700、pattern1=40232701及传授候选patternid0=40232702，在当前APK pattern表均无候选。旧手机清单明确有尚未取得的bossinfo.data5（134000字节），需要后续资源核对。不能用普通skilllist里的同号记录冒充Boss pattern。

没有可证明全游戏角色/技能范围的可信索引，因此全游戏覆盖仍UNKNOWN，不计算百分比。手机清单、主表内数组边界、全游戏目录完整性是不同依据。

## 可做的查询及不能做的判断

可按来源/表/记录路径/效果代码筛字段；查同一参数在不同效果的不同状态；查角色2327原文与字段证据；查34条HighHP存在参数；查Extra等级文案和ID声明；查辅助表完整记录、候选失配及来源冲突。

不能据此判定玩家已解锁哪项能力、当前唯一生效版本、全游戏已取齐、全部技能倍率、完整成长表或最终伤害。数值相同、名称相同、文案顺序相同都不足以新增规则。

## 重跑

从项目根目录使用现有环境：

```powershell
Set-Location 'E:\\代码项目\\锁链战记数据解包'
$env:PYTHONIOENCODING='utf-8'
& .\\.venv\\Scripts\\python.exe -B scripts/build_field_guide.py
```

只读正式E的manifest及15份来源JSON，复用已有手机清单、采集清单、主表组件JSON、必杀追踪证据及Unity扫描/定向核对记录；新增文件仅在output/field_guide，STATUS单独维护。依赖为Python3.12.14标准库及本项目export_master辅助函数；不连接手机、不重新解密、不需要新增包。此脚本是当前输入的字段/覆盖交付器，不是新快照通用语义验收器。{len(checks['checks'])}项结构核对通过，不冒充独立审查或实机验证。

若需重新产生19项定向头部证据，先运行`& .\\.venv\\Scripts\\python.exe -B scripts/audit_unity_headers.py`，需要已有UnityPy1.25.4、`work/apk/assets/bin/Data/data.unity3d`及`output/unity/mono_errors.jsonl`。只读原容器，写入`output/field_guide/unity_header_gap_audit.json`；随后再次运行字段交付器生成/选定新目录。未实现全缓存采集或未来快照的自动兼容：手机连接后会另存完整可访问外部files/cache采集件，先分类解码，再核对本审计缺口；图片音频不列为必须逐对象导出目标。
'''
    (output/'README.md').write_text(text,encoding='utf-8')


if __name__=='__main__':
    main()
