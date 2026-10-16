"""Refresh source-separated dictionary, coverage and candidate links for acquired cache."""
import argparse
import csv
import json
import re
from collections import Counter,defaultdict
from pathlib import Path

from build_field_guide import build_dictionary,csv_view,descendants,HIGHHP,meaning
from export_master import strict_load,lookup,write_json,write_lines,sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True)
    args=parser.parse_args();out=args.input/'analysis';out.mkdir(exist_ok=True)
    report=strict_load((args.input/'decode_report.json').read_bytes())
    records=[strict_load(line) for line in (args.input/'records.jsonl').open(encoding='utf-8')]
    by_key={r['record_key']:r for r in records};assert len(by_key)==len(records)
    active=strict_load(Path('output/sample/active_skill_trace.json').read_bytes())
    build_dictionary(out,records,active)
    # Scalar array members have a stable JSON pointer too; retain an explicit
    # unknown dictionary entry rather than omitting them for lacking field names.
    dictionary=strict_load((out/'field_dictionary.json').read_bytes())
    scalar_groups=defaultdict(list)
    for r in records:
        if not isinstance(r['raw'],(dict,list)):scalar_groups[(r['source_key'],r['table'])].append(r)
    for (_,table),group in scalar_groups.items():
        first=group[0]
        dictionary.append({'source_file':first['original_file'],'source':'CACHE','table':table,'record_type':table,
                           'field_path':'','meaning_zh':'无字段名的数组成员原值；含义未知，路径指向该成员自身',
                           'examples':[r['raw'] for r in group[:2]],'observed_types':dict(Counter(type(r['raw']).__name__ for r in group)),
                           'unit':None,'unit_status':'未知','conversion':None,'applicability':'仅本数组位置','status':'未知',
                           'evidence':['原始JSON数组边界及成员位置'],'records_with_field':len(group),'records_without_path':0,
                           'example_locations':[{'record_key':r['record_key'],'pointer':r['location']['json_pointer']} for r in group[:2]],
                           'path_is_analysis_name':False,'path_convention':'空相对路径表示记录原值本身；完整pointer见示例'})
    if scalar_groups:
        with (out/'field_dictionary.csv').open(encoding='utf-8-sig',newline='') as stream:headers=next(csv.reader(stream))
        keys=['source_file','source','table','record_type','field_path','meaning_zh','examples','observed_types','unit','unit_status','conversion','applicability','status','evidence','records_with_field','records_without_path','example_locations']
        assert len(keys)==len(headers)
        write_json(out/'field_dictionary.json',dictionary);csv_view(out/'field_dictionary.csv',dictionary,list(zip(keys,headers)))
    with (out/'field_dictionary.csv').open(encoding='utf-8-sig',newline='') as stream:headers=next(csv.reader(stream))
    keys=['source_file','source','table','record_type','field_path','meaning_zh','examples','observed_types','unit','unit_status','conversion','applicability','status','evidence','records_with_field','records_without_path','example_locations']
    headers[keys.index('examples')]='原始值示例JSON（长值为有标识预览）'
    csv_dictionary=[]
    for index,item in enumerate(dictionary):
        row=dict(item);example=json.dumps(item['examples'],ensure_ascii=False)
        if len(example)>2000:
            row['examples']={'preview':example[:2000],'truncated_for_csv':True,'full_value':f'field_dictionary.json#/{index}/examples'}
        csv_dictionary.append(row)
    csv_view(out/'field_dictionary.csv',csv_dictionary,list(zip(keys,headers)))
    selected=strict_load(Path('output/export/latest.json').read_bytes());base=Path(selected['directory'])
    manifest=strict_load((base/'manifest.json').read_bytes())
    # APK candidates remain separately sourced. Only daSkill uses the established
    # conditional per-ID lookup; no fields or other namespaces are merged.
    apk_source=next(s for s in manifest['sources'] if s['source_key']=='APK/_mdSkill.json')
    apk_raw=(base/apk_source['copied_file']).read_bytes();assert sha(apk_raw)==apk_source['sha256']
    from export_master import parse_records
    _,located=parse_records(apk_raw,'skilllist')
    apk=[{'record_key':'APK/_mdSkill.json#'+loc['json_pointer'],'raw':raw,'location':loc,'source_key':'APK/_mdSkill.json','layer':'APK','table':'skilllist'} for raw,loc in located]
    skills=[r for r in records if r['source_key']=='CACHE/skilllist.data5.json.raw']
    indexes={layer:defaultdict(list) for layer in ('CACHE','APK')}
    for r in skills+apk:indexes[r['layer']][r['raw']['skillid']].append(r)
    domains={table:defaultdict(list) for table in ('bosspattern','bossskill')}
    for r in records:
        if r['table'] in domains:
            key='patternid' if r['table']=='bosspattern' else 'skillid'
            domains[r['table']][r['raw'].get(key)].append(r)
    apk_domains={table:defaultdict(list) for table in domains}
    boss_source=next(s for s in manifest['sources'] if s['source_key']=='APK/_mdBossInfo.json')
    boss_raw=(base/boss_source['copied_file']).read_bytes();assert sha(boss_raw)==boss_source['sha256']
    apk_boss=[]
    for table in domains:
        _,located_boss=parse_records(boss_raw,table)
        for raw,loc in located_boss:
            entry={'record_key':'APK/_mdBossInfo.json#'+loc['json_pointer'],'raw':raw,'location':loc,
                   'source_key':'APK/_mdBossInfo.json','layer':'APK','table':table,'original_file':str(base/boss_source['copied_file'])}
            apk_domains[table][raw.get('patternid' if table=='bosspattern' else 'skillid')].append(entry);apk_boss.append(entry)
    write_lines(out/'apk_boss_records.jsonl',apk_boss)
    refs=[]
    def edge(parent,path,sid,domain,status):
        if type(sid) is not int:resolution={'status':'INVALID_OR_UNKNOWN_ID','candidates':[]}
        elif sid==0:resolution={'status':'ZERO_SENTINEL_PRESERVED','candidates':[]}
        elif domain=='daSkill':resolution=lookup(sid,'JSON_SNAPSHOT_WITH_APK_FALLBACK',indexes)
        else:resolution={'status':'CANDIDATE_FOUND' if domains[domain].get(sid) or apk_domains[domain].get(sid) else 'MISSING_CANDIDATE',
                         'candidates':[r['record_key'] for r in domains[domain].get(sid,[])+apk_domains[domain].get(sid,[])],
                         'cache_candidates':[r['record_key'] for r in domains[domain].get(sid,[])],
                         'apk_candidates':[r['record_key'] for r in apk_domains[domain].get(sid,[])],
                         'scope':'Candidates listed separately from both sources; loader priority/fallback UNKNOWN'}
        refs.append({'parent_record_key':parent['record_key'],'field_path':path,'id_raw':sid,'domain':domain,
                     'association_status':status,'resolution':resolution,'runtime_activation':'UNKNOWN'})
    for r in records:
        raw=r['raw'];table=r['table']
        if not isinstance(raw,dict):continue
        if r['source_key']=='CACHE/skilllist.data5.json.raw':
            for i,sid in enumerate(raw.get('sub',[])):edge(r,f'/sub/{i}',sid,'daSkill','已确认定义引用；仅一层，不证明实例安装')
        if table=='charainfo':
            slots=raw.get('skillid',[])
            if len(slots)==4:
                for i,sid in enumerate(slots[1:],1):edge(r,f'/skillid/{i}',sid,'daSkill','已确认四槽定义；开放状态未知')
        if table in ('charainfo','denju'):
            for field,sid in raw.items():
                if re.fullmatch(r'pattern\d+|patternid\d+',field):edge(r,'/'+field,sid,'bosspattern','推断：显式ID候选，加载入口待核对')
        if table=='bosspattern':
            for field,sid in raw.items():
                if re.fullmatch(r'skillid\d+',field):edge(r,'/'+field,sid,'bossskill','推断：Boss独立命名空间的有序槽位')
        for path,sid in descendants(raw):
            if re.search(r'/(?:skill_ids|sympathy_skill_ids)/\d+$',path):edge(r,path,sid,'daSkill','推断：辅助定义声明ID，运行入口未知')
        if table in ('supporterskill','sympathy_skill_info'):
            for field,sid in raw.items():
                if re.fullmatch(r'abi\d+' if table=='supporterskill' else r'ability\d+',field):edge(r,'/'+field,sid,'daSkill','推断：已有辅助字段候选')
    write_lines(out/'references.jsonl',refs)
    missing=[r for r in refs if r['resolution']['status'] in ('MISSING_ID','MISSING_CANDIDATE','INVALID_OR_UNKNOWN_ID')]
    write_lines(out/'unresolved_references.jsonl',missing)
    csv_view(out/'unresolved_references.csv',missing,[('parent_record_key','父记录'),('field_path','字段'),('id_raw','原ID'),('domain','命名空间'),('association_status','确认状态'),('resolution','查询结果')])
    card=next(r for r in records if r['table']=='charainfo' and r['raw']['cid']==2327)
    patterns=[r for r in records if r['table']=='bosspattern' and r['raw']['patternid'] in (40232700,40232701,40232702)]
    sample_skills=[r for r in records if r['table']=='bossskill' and r['raw']['skillid'] in range(40232700,40232706)]
    sample={'card':card,'patterns':patterns,'boss_skills':sample_skills,
            'links':[r for r in refs if r['parent_record_key'] in {card['record_key'],*(p['record_key'] for p in patterns)}],
            'status':'原值与显式ID候选链已补齐；Boss读取入口、执行先后/条件、type27/13参数语义仍未知',
            'namespace_warning':'Boss skill40232705与普通daSkill40232705不同记录，禁止混用',
            'current_player_unlock':'UNKNOWN','final_battle_multiplier':'UNKNOWN'}
    write_json(out/'cid2327_patterns.json',sample)
    sample_rows=[]
    for p in patterns:
        for key,sid in p['raw'].items():
            if not re.fullmatch(r'skillid\d+',key):continue
            for effect in domains['bossskill'].get(sid,[]):
                for field,value in effect['raw'].items():
                    if not re.fullmatch(r'skillparam\d+',field):continue
                    sample_rows.append({'cid':2327,'name_ja':card['raw'].get('name'),'title_ja':card['raw'].get('title'),
                                       'pattern_id':p['raw']['patternid'],'name':p['raw'].get('sname'),'description_ja':p['raw'].get('sinfo'),
                                       'translation_zh':None,'effect_fragment_ja':None,'pattern_slot':key,'boss_skill_id':sid,'active_type':effect['raw'].get('skillid0'),
                                       'record_key':effect['record_key'],'field_path':field,'pointer':effect['location']['json_pointer']+'/'+field,
                                       'raw_value':value,'interpretation':None,'unit':None,'condition':None,'duration':None,'status':'未知',
                                       'basis':'同一pattern显式skillid槽→Boss技能ID候选；未用描述顺序推出数值语义'})
    write_json(out/'cid2327_pattern_fields.json',sample_rows)
    csv_view(out/'cid2327_pattern_fields.csv',sample_rows,[(k,k) for k in sample_rows[0]])
    highhp=[]
    for effect in skills:
        if effect['raw'].get('ability')!=1105:continue
        for field in HIGHHP:
            if field in effect['raw']:
                highhp.append({'record_key':effect['record_key'],'skill_id':effect['raw']['skillid'],'name_ja':effect['raw'].get('name'),
                               'description_ja':effect['raw'].get('text'),'field':field,'raw':effect['raw'][field],**meaning(effect,'/'+field,active),
                               'scope':'原APK已有局部规则；不证明当前实例或全局最终值'})
    write_json(out/'highhp_fields.json',highhp)
    csv_view(out/'highhp_fields.csv',highhp,[('skill_id','技能ID'),('name_ja','日文名'),('description_ja','原文'),('field','字段'),('raw','原值'),('meaning_zh','含义'),('unit','单位'),('conversion','局部换算'),('status','状态'),('evidence','依据'),('record_key','记录定位')])
    previous_ids=[40035430,40035431,40035432,40035330,40035331,40035332,40035130,40035131,40035132]
    previous=[{'id':sid,'resolution':lookup(sid,'JSON_SNAPSHOT_WITH_APK_FALLBACK',indexes)} for sid in previous_ids]
    conflict={layer:[r for r in indexes[layer].get(36000358,[])] for layer in ('CACHE','APK')}
    write_json(out/'skill36000358_sources.json',{'sources':conflict,'rule':'Only per-ID conditional fallback; no field merge; live loaded layer unknown'})
    coverage=[{'category':row['filename'],'expected_files':1,'acquired_files':1,'decoded_files':int(row['status']=='DECODED'),
               'parsed_record_views':row.get('exported_record_views',0),'exported_record_views':row.get('exported_record_views',0),
               'failed':row['status']!='DECODED','error':row.get('error'),'meaning':'逐字段字典；未知保留',
               'expected_basis':'本次外部目录清单；记录依据已解码JSON数组/文档边界','source':row['source'],'sha256':row['source_sha256'],
               'needs_phone':False} for row in report['files']]
    extraction=strict_load(Path('output/phone_full_20261015/extraction/extraction.json').read_bytes())
    inventory=[strict_load(line) for line in Path('output/phone_full_20261015/inventory.jsonl').open(encoding='utf-8')]
    bundles=sum(r['path'].endswith('.bdl') for r in inventory)
    coverage.append({'category':'bdl容器','expected_files':bundles,'acquired_files':bundles,'decoded_files':0,'parsed_record_views':None,
                     'exported_record_views':None,'failed':None,'meaning':'原封装与路径已保存；头部不直接识别为UnityFS，目标比例未知',
                     'expected_basis':'本次目录清单及tar逐文件核对','needs_phone':False})
    other=len(inventory)-bundles-report['input_files']
    coverage.append({'category':'其他后缀/无后缀文件','expected_files':other,'acquired_files':other,'decoded_files':None,
                     'parsed_record_views':None,'exported_record_views':None,'failed':None,
                     'meaning':'全部原件已采；元数据/版本和广告缓存等混合，目标性质及其结构解析范围尚未穷尽',
                     'expected_basis':'完整目录清单扣除bdl与data5；未凭名称全部排除','needs_phone':False})
    write_json(out/'coverage_audit.json',coverage)
    csv_view(out/'coverage_audit.csv',coverage,[(key,key) for key in coverage[0]])
    summary={'snapshot':args.input.name,'acquisition':extraction,'data5_files':report['input_files'],'decoded_data5':report['decoded_files'],
             'record_views':len(records),'table_views':len(report['tables']),'reference_count':len(refs),
             'reference_results':dict(Counter(r['resolution']['status'] for r in refs)),
             'reference_scope':'当前缓存sub/四槽、Boss候选及已列辅助字段；八槽角色及其他命名空间未声明完整图',
             'previous_nine_missing_ids':previous,'highhp_records':len({r['skill_id'] for r in highhp}),
             'old_E_build':str(base),'old_E_manifest_sha256':sha((base/'manifest.json').read_bytes()),
             'limits':['全游戏覆盖未知','未验证私有目录或服务端完整性','当前加载版本/玩家状态未知','全部bdl已采但尚未解码','无入边不等于失效；全部记录保留'],
             'producer_sha256':sha(Path(__file__).read_bytes())}
    write_json(out/'summary.json',summary)
    print(json.dumps({'status':'EXPORTED','records':len(records),'references':len(refs),'missing':len(missing),'sample_patterns':len(patterns),'sample_boss_skills':len(sample_skills)}),flush=True)


if __name__=='__main__':main()
