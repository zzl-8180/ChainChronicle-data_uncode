"""Extend the same card table to all remaining described numeric effects."""
import json
from pathlib import Path


def wedge_time_overlay(records):
    root=Path('output/card_comparison_cid30236/wedge_time')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    assert all(r in records for r in trace['source_records'])
    c=trace['code_constants'][0];ev=['wedge_time/README.md','wedge_time/trace.json','wedge_time/native_checks.json']
    scope='TimeWedgeSkill.SetTimeStop的普通模式clockUpFlag=0；cid30236有初始时楔，具体当前队伍模式另论'
    limits='普通模式5游戏秒，ClockUp模式为8；正输入加到已有停止计时。完整队伍/目标资格和时楔消耗/动画时序另论。'
    conversion='原生fmov常量5.0，clockUpFlag=0时选择；传入CharaStatus.SetTimeStop并累加至_timeStop计时，按BattleManager游戏delta扣减至0'
    rule=dict(source='NATIVE_CODE',table='NATIVE_METHOD',record_type='TimeWedgeSkill.SetTimeStop',effect_type='TimeWedgeStop',field_path=c['field_path'],meaning_zh='普通时楔释放的停止时长输入',unit='游戏秒',conversion=conversion,base_definition='目标CharaStatus的停止计时；已有计时为0时，本项输入为5',status='已确认（原生常量及受控局部规则）',applicability=scope,evidence=ev,limits=limits,target='时楔目标列表中的合格敌人',occurrences=1,unit_status='已确认（限定普通时楔模式）')
    view=dict(record_key=c['record_key'],source='NATIVE_CODE',table=c['table'],namespace='Native code constant',record_id=c['record_id'],effect_type=rule['effect_type'],field_path=c['field_path'],raw_value=c['raw_value'],original_file=c['original_file'],source_sha256=c['source_sha256'],location=c['location'],json_pointer=None,meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=conversion,converted_value=5.0,display_value='普通时楔停止时长输入5游戏秒（ClockUp模式为8秒）；正输入累加到已有停止计时',raw_value_status='RAW_CODE_CONSTANT_FOUND',correspondence_status='NORMAL_TIMEWEDGE_STOP_INPUT_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits)
    return [rule],[view]


def super_counter_overlay(records):
    root=Path('output/card_comparison_cid30236/super_counter')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    assert all(r in records for r in trace['source_records'])
    c=trace['code_constants'][0];ev=['super_counter/README.md','super_counter/trace.json','super_counter/native_checks.json']
    scope='PlayerManager.incSympathySkillCount的共用K/SSympathy计数；本卡pattern2=43023602，资格/实际装载另论'
    limits='数值来自原生指令常量，角色主表没有对应数字字段；完整事件资格、队伍派发与pattern选择另论。'
    conversion='合格共鸣事件使共用计数加1；达到10则清零并派发；符合SSympathy资格时置就绪标志，使用后消耗'
    rule=dict(source='NATIVE_CODE',table='NATIVE_METHOD',record_type='PlayerManager.incSympathySkillCount',effect_type='K/SSympathyCounter',field_path=c['field_path'],meaning_zh='超共鸣共用计数门槛',unit='次合格共鸣计数事件',conversion=conversion,base_definition='PlayerManager的共用计数，不是cid独立计数',status='已确认（原生常量及受控局部规则）',applicability=scope,evidence=ev,limits=limits,target='符合超共鸣派发资格的角色',occurrences=1,unit_status='已确认（共用计数常量）')
    view=dict(record_key=c['record_key'],source='NATIVE_CODE',table=c['table'],namespace='Native code constant',record_id=c['record_id'],effect_type=rule['effect_type'],field_path=c['field_path'],raw_value=c['raw_value'],original_file=c['original_file'],source_sha256=c['source_sha256'],location=c['location'],json_pointer=None,meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=conversion,converted_value=10,display_value='累计10次合格共鸣计数事件（队伍共用）；达到后计数清零并派发就绪',raw_value_status='RAW_CODE_CONSTANT_FOUND',correspondence_status='SHARED_SUPER_COUNTER_THRESHOLD_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits)
    return [rule],[view]


def leader_condition_overlay(records):
    root=Path('output/card_comparison_cid30236/leader_condition')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    r=trace['source_records'][0];assert r in records
    ev=['leader_condition/README.md','leader_condition/trace.json','leader_condition/native_checks.json']
    scope='仅leader_ability cid30236的category2、conditions=[0]、border4组合'
    limits='配置资格：候选角色的职业条件命中累计至少4；完整候选队伍/后备/搭档范围和当前激活另论。target0仅确认装入_rule，本规则不赋予额外语义。'
    specs=(('border','资格命中成员的最小累计人数','名',4,'原值→_targetNum；累计人数小于border则继续，否则通过','至少4名满足职业条件的候选成员'),
        ('category','Leader条件类别','类别枚举','职业','category2的跳表分支将conditions装入_target_job','category2：职业条件'),
        ('conditions','Leader要求的职业列表','职业枚举列表',['战士'],'JOB_TYPE.WARRIOR原始枚举0；Intersect(条件列表,候选成员jobtype列表).Any()','conditions=[0]：战士'))
    rules,views=[],[]
    for field,meaning,unit,value,conversion,display in specs:
        rules.append(dict(source='CACHE',table='leader_ability',record_type='category=2',effect_type='LeaderCondition',field_path='/'+field,meaning_zh=meaning,unit=unit,conversion=conversion,base_definition='每个传入候选角色的jobtype与配置职业列表的交集命中结果',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target='Leader资格计数中的候选成员',occurrences=1,unit_status='已确认（限定当前职业人数条件）'))
        views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='Leader ability',record_id=30236,effect_type='LeaderCondition',field_path='/'+field,raw_value=r['raw'][field],original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=meaning,unit=unit,target=rules[-1]['target'],conversion=conversion,converted_value=value,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='LEADER_CATEGORY_JOB_MINIMUM_COUNT_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    return rules,views


def chain_mana_overlay(records):
    root=Path('output/card_comparison_cid30236/chain_mana')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    assert all(r in records for r in trace['source_records'])
    dispatch_root=Path('output/card_comparison_cid30236/chain_dispatch')
    dispatch=json.loads((dispatch_root/'trace.json').read_text(encoding='utf-8'))
    dispatch_checks=json.loads((dispatch_root/'native_checks.json').read_text(encoding='utf-8'))
    assert dispatch['native_sha256']==dispatch_checks['native_sha256']==trace['native_sha256']
    assert all(c['passed'] for c in dispatch_checks['checks']) and all(r in records for r in dispatch['source_records'])
    r=next(r for r in trace['source_records'] if r['raw']['skillid']==43023617)
    ev=['chain_mana/README.md','chain_mana/trace.json','chain_mana/native_checks.json','chain_dispatch/README.md','chain_dispatch/trace.json','chain_dispatch/native_checks.json']
    scope='仅ordinary43023617 /ability1106已核Chain获珠路径；Extra43023632.str0引用此ID，实际解锁/安装另论'
    limits='唯一活成员/单一已装work的有效按钮事件最多一次随机；失败可在后续事件重试、成功锁存。10%为每次阈值，不是整条Chain累计概率；未发现固定双判定。完整名单/装载/显示计数换算和实际生成另论。当前四档10%与截图20%差异保留。'
    rules,views=[],[]
    for i in range(5):
        field=f'param{i}';quantity=i==0;meaning='Chain获珠数量' if quantity else 'Chain档位获珠概率阈值'
        conversion='param0向零截断为生成数量，本卡1；param5=-1跳过累计总数上限分支' if quantity else f'内部计数{str(i+1) if i<4 else ">=5"}读取{field}；计数0/1返回0；Random.Range(0,1)≤阈值时通过'
        raw=r['raw'][field];value=int(raw) if quantity else raw*100;unit='个（生成输入）' if quantity else '概率阈值；派生百分比'
        display=f'{value}个（生成数量输入）' if quantity else f'每次有效按钮事件的获珠阈值{value:g}%（未锁存时；非整Chain累计概率）'
        rules.append(dict(source='CACHE',table='skilllist',record_type='ability=1106',effect_type=1106,field_path='/'+field,meaning_zh=meaning,unit=unit,conversion=conversion,base_definition='cAbilityCharaManaGetWork.GetRate选择与OnExecSkillAbilityChainManaGet生成输入',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target='施法方获珠事件',occurrences=1,unit_status='已确认（限定当前1106路径）'))
        views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=43023617,effect_type=1106,field_path='/'+field,raw_value=raw,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=meaning,unit=unit,target=rules[-1]['target'],conversion=conversion,converted_value=value,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='ABILITY1106_SCOPED_RATE_AND_COUNT_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    return rules,views


def mana_chance_overlay(records):
    root=Path('output/card_comparison_cid30236/mana_chance')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    r=trace['source_records'][0];assert r in records and r['raw']['ability']==28
    ev=['mana_chance/README.md','mana_chance/trace.json','mana_chance/native_checks.json']
    scope='仅普通43023602 /ability28的subManaHunter已核三个伤害类型；资格和来源列表满足时'
    limits='单来源配置阈值；完整击杀/装载及实际玛那生成未模拟。地形标志16的沙漠含义按本卡文案对照，完整地形枚举链另论；param3保留未知。'
    rules,views=[],[]
    for field in ('param0','param1','param2','param4','param5','param6'):
        mask=field=='param6';base=field in ('param0','param1','param2')
        meaning='地形附加概率的位索引' if mask else '击杀玛那基础概率阈值' if base else '匹配地形时的附加概率阈值'
        conversion='正整数4→1<<4=16；与当前地形标志按位与' if mask else 'damageType0/2/1分别读取param0/1/2，取为基础阈值；Random.Range(0,1)≤基础+附加时通过' if base else '地形掩码匹配时读取；type2取param4、type0/1取param5，附加到基础阈值'
        raw=r['raw'][field];value=1<<int(raw) if mask else raw*100
        unit='位索引；派生地形掩码' if mask else '概率阈值；派生百分比' if base else '概率阈值增加量；派生百分点'
        display='地形位索引4→掩码16' if mask else f'基础概率{value:g}%' if base else f'匹配地形时概率+{value:g}个百分点'
        rules.append(dict(source='CACHE',table='skilllist',record_type='ability=28',effect_type=28,field_path='/'+field,meaning_zh=meaning,unit=unit,conversion=conversion,base_definition='Random.Range浮点0..1；基础与地形附加相加',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target='原文击杀事件对应的玛那获得判定',occurrences=1,unit_status='已确认（限定当前普通28概率路径）'))
        views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=43023602,effect_type=28,field_path='/'+field,raw_value=raw,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=meaning,unit=unit,target=rules[-1]['target'],conversion=conversion,converted_value=value,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='ABILITY28_SCOPED_RANDOM_THRESHOLD_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    return rules,views


def field_time_overlay(records):
    root=Path('output/card_comparison_cid30236/field_time')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    assert all(r in records for r in trace['source_records'])
    r=next(r for r in trace['source_records'] if r['table']=='bossskill')
    ev=['field_time/README.md','field_time/trace.json','field_time/native_checks.json']
    conversion='skillparam5原样→bhSkillUtil.param5→startChangeField(change_time)→cFieldChangeData._changeTime；_changeTimeCount累计Unity deltaTime，达到时进入恢复分支'
    scope='仅Boss43023613 /type66，原值300为正；能力一1080/共鸣3005的候选pattern分别43023603/04共用本记录'
    limits='配置计时300游戏秒；完整触发/安装、地形切换动画、提前死亡恢复、其他地形覆盖另论，不承诺墙钟300秒。'
    rule=dict(source='CACHE',table='bossskill',record_type='skillid0=66',effect_type=66,field_path='/skillparam5',meaning_zh='地形变化的正持续时间',unit='游戏秒（Unity deltaTime累计）',conversion=conversion,base_definition='GroundManager处于更新地形的战斗状态时累计的deltaTime',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target='战场地形',occurrences=1,unit_status='已确认（限定Boss66正持续时间路径）')
    view=dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='Boss skill',record_id=43023613,effect_type=66,field_path='/skillparam5',raw_value=r['raw']['skillparam5'],original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/skillparam5',meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=conversion,converted_value=300,display_value='300游戏秒（5游戏分钟；地形计时配置）',raw_value_status='RAW_FOUND',correspondence_status='TYPE66_CHANGE_TIME_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits)
    return [rule],[view]


def lifesteal_overlay(records):
    root=Path('output/card_comparison_cid30236/lifesteal')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    r=trace['source_records'][0];assert r in records and r['raw']['ability']==21
    ev=['lifesteal/README.md','lifesteal/trace.json','lifesteal/native_checks.json']
    scope='仅普通65000003 /ability21已核暴击回复分支；进入回复路径且安装/资格满足时'
    limits='伤害基数为目标Attacked返回整数，不承诺等于实际HP减少；完整Heal入口资格、其他回复/上限来源及当前玩家装载另论。'
    specs=(('param1','暴击回复比例','伤害处理返回整数的比例',25,'回复输入=floor(本次伤害处理返回整数×param1)','暴击回复输入=floor(伤害处理返回整数×25%)'),
        ('flag0_1','暴击回复HP上限档位','最大HP的倍数',1.4,'flag0_1左移32位；512→bit41，经Heal掩码保留，由上限表选择float32(1.4)','可回复至最大HP的1.4倍（超出40%）；已有更高HP不因本次回复降低'))
    rules,views=[],[]
    for field,meaning,unit,value,conversion,display in specs:
        rules.append(dict(source='CACHE',table='skilllist',record_type='ability=21',effect_type=21,field_path='/'+field,meaning_zh=meaning,unit=unit,conversion=conversion,base_definition='目标Attacked伤害处理返回整数' if field=='param1' else '接受者最大HP；配置表1.399999976158142的可读档位1.4',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target='暴击攻击者自身',occurrences=1,unit_status='已确认（限定普通21回复路径）'))
        views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=65000003,effect_type=21,field_path='/'+field,raw_value=r['raw'][field],original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=meaning,unit=unit,target='暴击攻击者自身',conversion=conversion,converted_value=value,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='ABILITY21_AMOUNT_AND_HEAL_CAP_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    return rules,views


def movement_overlay(records):
    root=Path('output/card_comparison_cid30236/movement')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    specs=((1095,'param2',(65000001,),'multiply'),(7,'param2',(43023607,),'multiply'),(1008,'param2',(43023606,),'multiply'),(1017,'param2',(43023605,65000002),'multiply'),
        (65,'param2',(43023608,),'add'),(64,'param2',(43023609,),'add'),(99,'param8',(43023616,),'add'),(7,'param7',(43023607,),'interval'))
    rules,views=[],[]
    for ability,field,ids,mode in specs:
        ev=['movement/README.md','movement/trace.json','movement/native_checks.json']
        meaning='攻击间隔乘数' if mode=='interval' else '移动速度乘数' if mode=='multiply' else '移动速度因子加算增量'
        conversion='间隔因子乘param7；原始atkspeed1.5且其他因子1/偏移0时，名义间隔1.125' if mode=='interval' else '移动因子乘param2' if mode=='multiply' else 'Support2移动因子=clamp(1+sum(_move))；本字段直接写_move'
        scope=f'仅普通ability{ability}已核ID：'+','.join(map(str,ids))+'；安装/资格满足时'
        limits='局部配置贡献；地形资格/实际装载和全部速度来源另论。1.125为中性上下文名义间隔，非实际每击动作周期。'
        target='被攻击敌人' if ability==99 else '自身' if ability in (1095,7) else '对应全体/职业接受者'
        rules.append(dict(source='CACHE',table='skilllist',record_type=f'ability={ability}',effect_type=ability,field_path='/'+field,meaning_zh=meaning,unit='间隔倍率；名义时间游戏秒' if mode=='interval' else '速度倍率/加算增量；派生为百分比',conversion=conversion,base_definition='进入本项前的移动因子或攻击间隔；临时移动从1加算',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target=target,occurrences=len(ids),unit_status='已确认（限定对应速度分支）'))
        for sid in ids:
            r=next(r for r in trace['source_records'] if r['raw']['skillid']==sid);assert r in records
            raw=r['raw'][field];converted=raw if mode=='interval' else (raw-1)*100 if mode=='multiply' else raw*100
            display='攻击间隔×0.75（缩短25%；原始1.5且其他因子中性时名义1.125游戏秒，约1.1秒）' if mode=='interval' else f'移动速度降低{-converted:g}%（本项因子{1+raw:g}）' if converted<0 else f'移动速度+{converted:g}%（'+(f'×{raw:g}' if mode=='multiply' else '同类临时支持加算')+'）'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=sid,effect_type=ability,field_path='/'+field,raw_value=raw,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=meaning,unit=rules[-1]['unit'],target=target,conversion=conversion,converted_value=converted,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='SCOPED_SPEED_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    return rules,views


def critical_overlay(records):
    root=Path('output/card_comparison_cid30236/critical')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    rules,views=[],[]
    specs=((1095,'param6',(43023601,65000001),'damage',1.5),(1095,'param5',(65000001,),'chance',0),
        (7,'param5',(43023607,),'chance',0),(7,'param6',(43023607,),'damage',0),
        (1008,'param4',(43023606,),'chance',0),(1008,'param5',(43023606,),'damage',0),
        (65,'param4',(43023608,),'chance',0),(65,'param6',(43023608,),'damage',0),
        (64,'param4',(43023609,),'chance',0),(64,'param8',(43023609,),'damage',0),
        (2012,'param4',(43023612,43023613,43023614),'chance',0),(2012,'param5',(43023612,43023613,43023614),'damage',0),
        (3000,'param8',(43023611,),'damage',0))
    for ability,field,ids,kind,baseline in specs:
        ev=['critical/README.md','critical/trace.json','critical/native_checks.json']
        meaning=('暴击伤害系数加算贡献（先减1.5基准）' if baseline else '暴击伤害系数加算贡献') if kind=='damage' else '暴击概率加算贡献'
        conversion='delta=param6-1.5；攻击时在1.5基础暴击系数上加delta及其他来源' if baseline else f'本能力分支直接将{field}作为'+('暴击概率' if kind=='chance' else '暴击伤害系数')+'增量加算；不套用Always3的减1.5规则'
        if ability==2012:conversion+='；本段暴击量直接写入，不乘请求系数'
        scope=f'仅ordinary ability{ability}，已核ID：'+','.join(map(str,ids))+'；安装与资格满足时'
        limits='单项配置贡献；不等于所有来源后的最终概率、倍率或HP变化。概率使用百分点；暴击伤害使用倍率增量/百分点，不能当相对现有伤害的百分比。'
        target='自身' if ability in (1095,7) else '对应支持接受者（对象资格按原文/字段条件）'
        rules.append(dict(source='CACHE',table='skilllist',record_type=f'ability={ability}',effect_type=ability,field_path='/'+field,meaning_zh=meaning,unit='倍率增量；可显示百分点' if kind=='damage' else '概率增量；可显示百分点',conversion=conversion,base_definition='暴击伤害基准1.5由原生显式减去并加回' if baseline else '本项对0的加算增量；同类支持的上限/其他类别另论',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target=target,occurrences=len(ids),unit_status='已确认（限定对应能力分支）'))
        for sid in ids:
            r=next(r for r in trace['source_records'] if r['raw']['skillid']==sid);assert r in records
            raw=r['raw'][field];delta=raw-baseline
            display=f'暴击伤害系数+{delta:g}（+{delta*100:g}个百分点）' if kind=='damage' else f'暴击率+{delta*100:g}个百分点'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=sid,effect_type=ability,field_path='/'+field,raw_value=raw,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=meaning,unit=rules[-1]['unit'],target=rules[-1]['target'],conversion=conversion,converted_value=delta*100,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='SCOPED_CRITICAL_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    return rules,views


def add_remaining_effects(add,one,skill,boss,pattern,records,rows):
    def put(*args,text_number=False,**kwargs):
        add(*args,**kwargs)
        rows[-1]['effect_scope']='other_numeric'
        if text_number:rows[-1]['calculation_status']='ORIGINAL_TEXT_NUMBER_CONFIRMED'
    normal,superp=pattern(43023601),pattern(43023602)
    a1,a2=skill(43023600),skill(43023605)
    job=next(r for r in records if r['table']=='job_ability' and 30236 in r['raw'].get('cids',[]))
    front=[boss(s) for s in (43023600,43023605,43023609)]
    traps=[boss(s) for s in (43023602,43023603,43023606,43023607,43023610,43023611)]
    put('other_sp_front_count','必杀','前方连击次数（三档共通）',normal,'5回ダメージを与え',[(r,['skillparam6']) for r in front],'每个前方目标','需持续在有效范围内',answer='每目标最多5次尝试；范围外也消耗预算',kind='次数上限',basis='../boss_chain/type105/README.md',shot='5次',desc_field='sinfo')
    put('other_sp_trap_count','必杀','每陷阱爆发次数（三档共通）',normal,'5回まで小ダメージを与え',[(r,['skillparam5']) for r in traps],'每个陷阱对象','有敌门控',answer='每个对象最多5次爆发',kind='次数上限',basis='../boss_chain/type112/README.md',shot='最多5次',desc_field='sinfo')
    put('other_sp_trap_interval','必杀','陷阱爆发间隔（三档共通）',normal,'一定間隔ごとに',[(r,['skillparam4']) for r in traps],'每个陷阱对象','一次update至多一次',answer='0.25游戏秒',kind='时间间隔',basis='../boss_chain/type112/README.md',desc_field='sinfo')
    put('other_sp_trap_layers','必杀','陷阱重叠层数（三档共通）',normal,'攻撃範囲を2つ重ねて複数設置',[(r,['skillparam9']) for r in traps],'设置位置','两段都执行且保留旧对象',answer='每位置2层；原文2重，既有局部设置路径已对应',kind='层数',basis='../boss_chain/type112/README.md',shot='二重',desc_field='sinfo')
    put('other_sp_trap_positions','必杀','陷阱位置数量（三档共通）',normal,'複数設置',[(r,['skillparam8']) for r in traps],'设置位置','只复用已完成数量规则，完整机制暂缓',answer='每段9个位置',kind='位置数量',basis='../boss_chain/type112/README.md',shot='9个',desc_field='sinfo')
    for mode,pid,sid,extraid in (('普通',43023601,43023604,43023612),('沙漠',43023600,43023608,43023613),('超共鸣',43023602,43023612,43023614)):
        desc=superp if mode=='超共鸣' else normal
        b=boss(sid)
        put(f'other_sp_{pid}_move','必杀',mode+'·全体移动提升',desc,'移動速度とクリティカル',[(b,['skillparam6'])],'味方全体',mode+'档','30游戏秒',answer=f'移动因子1+{b["raw"]["skillparam6"]:g}×请求系数',kind='移动因子增加量',basis='../boss_chain/field_dictionary.json',desc_field='sinfo')
        for field,name in (('param4','暴击率提升'),('param5','暴击伤害提升')):
            put(f'other_sp_{pid}_{field}','必杀',mode+'·全体'+name,desc,'クリティカル発生率とクリティカル威力',[(skill(extraid),[field,'param0'])],'附加能力的接受者；原文全体',mode+'档','原始30；单位待该路径核实',gap='ability2012到TimePowerUpData的属性/增量映射；不从其他类型套同名参数',shot=f'{skill(extraid)["raw"][field]*100:g}%',desc_field='sinfo')
    put('other_sp_support_duration','必杀','全体支持持续时间（三档共通）',normal,'一定時間上がる',[(boss(s),['skillparam3']) for s in (43023604,43023608,43023612)],'各支持接受者','对应Boss13支持段',answer='30游戏秒',kind='持续时间',basis='../boss_heal/field_dictionary.json',shot='30秒',desc_field='sinfo')
    put('other_sp_normal_cost','必杀','普通档耗玛那',normal,'',[(normal,['scost'])],'施法者','普通档',answer='2（pattern.scost原值）',kind='玛那数量配置',basis='bosspattern.scost原值与截图；完整扣除流程未验',shot='2',desc_field='sinfo')
    put('other_sp_desert_cost_reduction','必杀','沙漠档耗玛那减少量',normal,'必要なマナが1つ減り',[(normal,['scost']),(pattern(43023600),['scost'])],'施法者','沙漠档',answer='减少1：两档scost分别2→1，原文明确',kind='玛那数量差',basis='bosspattern原文及两档scost',shot='少1',text_number=True,desc_field='sinfo')
    put('other_sp_super_cost','必杀','超共鸣耗玛那',superp,'0マナで発動',[(superp,['scost'])],'施法者','超共鸣档',answer='0（原文明确；scost字段缺失仍保留缺失）',kind='原文耗玛那数量',basis='bosspattern.sinfo',shot='0',text_number=True,desc_field='sinfo')
    put('other_sp_super_mana','必杀','超共鸣获得万象玛那',superp,'万象マナを1つ獲得',[],'施法方','发动超共鸣时',answer='1个（原文明确）',kind='原文获得数量',basis='bosspattern.sinfo',shot='1',text_number=True,desc_field='sinfo',gap='具体获得记录/字段的执行对应未建立；文案数值已交付')
    put('other_sp_super_counter','必杀','超共鸣累计触发次数门槛',normal,'',[],'自身','截图列共鸣10次后切换',gap='游戏条件配置记录尚未定位；不把其他同值字段当计数门槛',shot='10次',desc_field='sinfo',desc_note='本sinfo未写10；这是截图待对应项')
    put('other_a1_critical_damage','能力一','自身暴击伤害提升',a1,'攻撃力とクリティカル威力が上がる',[(skill(43023601),['param6'])],'自身',gap='Always3暴击伤害基准',shot='+87.5%')
    put('other_a1_wedge_count','能力一','初始时之楔数量',a1,'時の楔を1つ持った状態',[(a1,['param0'])],'自身','战斗开始；后备有效（原文）',answer='1个（原文明确）',kind='初始数量',basis='skill43023600.text',shot='1',text_number=True)
    put('other_a1_wedge_stop','能力一','时之楔解放后的敌方停止时间',a1,'時の楔',[],'被解放时之楔命中的敌人','解放时之楔',gap='截图5秒尚未定位到本地具体配置/常量；不将楔数量param0当时间',shot='5秒',desc_note='本卡原文只写初始楔数量；此项来自截图')
    put('other_a1_mana_chance','能力一','击杀获得玛那概率（通常）',a1,'一定確率で全ての必殺技が使えるマナ',[(skill(43023602),['param0','param1','param2','param3','param4','param5','param6'])],'施法方','敌方被自身击倒',gap='ability28各param的职业/地形与概率映射，不能将.2/.8直接当已确认概率',shot='一定几率（截图未标数字）')
    put('other_a1_desert_mana_chance','能力一','沙漠击杀获得玛那概率',a1,'地形が砂漠の場合、必ずマナを獲得',[(skill(43023602),['param3','param4','param5','param6'])],'施法方','沙漠且击杀敌人',answer='必定获得（原文；概率文案100%）',kind='原文必定条件',basis='skill43023600.text',text_number=True,gap='具体.2/.8组合和运行判断另行解释；不改写原值')
    put('other_a1_desert_duration','能力一','战斗/WAVE开始的沙漠持续时间',a1,'地形を砂漠に一定時間変更',[(skill(43023603),['str0']),(pattern(43023603),['skillid0']),(boss(43023613),['skillparam5'])],'战场地形','战斗/WAVE开始',gap='Boss66.skillparam5=300的定时路径与时间单位；触发资格另论',shot='300秒')
    put('other_a1_barrier_count','能力一','屏障保护次数',a1,'10回まで防御力を上げ',[(boss(43023614),['skillparam2'])],'每个屏障接受者','原文仅必杀攻击消耗次数',answer='10次计数配置；完整消耗资格另论',kind='保护次数',basis='barrier/native_checks.json；skill43023600.text',shot='10')
    put('other_a1_enemy_move','能力一','被攻击敌方移动降低',a1,'移動速度が一定時間下がる',[(skill(43023616),['param8','param0'])],'被攻击敌人','攻击时','30游戏秒',gap='已见param8写移动成员；仍需核移动聚合量纲',shot='30%')
    put('other_a1_critical_count','能力一','暴击攻击次数',a1,'クリティカル攻撃が6回になり',[(one('charainfo','cid',30236),['CRInumber']),(skill(43023604),['param8'])],'自身暴击','暴击时',answer='6次（原文明确；两个来源字段均为6）',kind='原文攻击次数',basis='skill43023600.text；Card.CRInumber /1079.param8',shot='6',text_number=True,gap='动作/实际命中计数的完整机制另论')
    for sid,mode in ((43023605,'常驻全体'),(43023606,'沙漠全体'),(43023607,'沙漠自身')):
        put(f'other_a2_{sid}_move','能力二',mode+'·移动提升',a2,'味方の攻撃力と防御力と移動速度',[(skill(sid),['param2','param0'])],'自身' if sid==43023607 else '战场味方',mode,gap='本能力类型param2的移动乘算映射')
    for sid,mode,rate,damage in ((43023606,'沙漠全体','param4','param5'),(43023607,'沙漠自身','param5','param6')):
        for field,name in ((rate,'暴击率'),(damage,'暴击伤害')):
            put(f'other_a2_{sid}_{field}','能力二',mode+'·'+name+'提升',a2,'クリティカル発生率とクリティカル威力が上がる',[(skill(sid),[field,'param0'])],'自身' if sid==43023607 else '战场味方',mode,gap=f'ability{skill(sid)["raw"]["ability"]}.{field}的属性与基准；不套Always3')
    put('other_a2_attack_interval','能力二','沙漠自身攻击间隔缩短',a2,'攻撃間隔が早くなる',[(skill(43023607),['param7']),(one('charainfo','cid',30236),['atkspeed'])],'自身','沙漠',gap='param7=.75到攻击间隔的乘算/单位，及截图1.1的舍入方式',shot='约1.1秒（表述待核）')
    for sid,mode,dmg in ((43023608,'WAVE全体','param6'),(43023609,'WAVE战士额外','param8')):
        for field,name in (('param2','移动'),('param4','暴击率'),(dmg,'暴击伤害')):
            put(f'other_wave_{sid}_{field}','能力二',mode+'·'+name+'提升',a2,'移動速度とクリティカル発生率とクリティカル威力が一定時間上がる',[(skill(sid),[field])],'战场味方' if sid==43023608 else '职业掩码1（原文战士）','WAVE推进','120游戏秒',gap='本项属性已见TimePowerUpData赋值；聚合基准/量纲待核')
    put('other_wave_duration','能力二','WAVE增强持续时间',a2,'一定時間上がる',[(skill(s),['param0']) for s in (43023608,43023609)],'对应WAVE接受者','WAVE推进',answer='120游戏秒',kind='持续时间',basis='timed_support/README.md',shot='120秒')
    chain=skill(43023617)
    put('other_a2_chain_threshold','能力二','获得万象玛那的Chain门槛',a2,'1stChain以上を達成した時',[(chain,['param1','param2','param3','param4']),(skill(43023632),['str0'])],'施法方','达到Chain门槛',answer='1stChain及以上（原文）',kind='原文Chain门槛',basis='skill43023605.text',text_number=True,gap='内部计数0/1概率为0，2起选param1..4；显示计数换算完整链另论；param0已确认为数量，不当门槛')
    put('other_a2_chain_probability','能力二','Chain获得万象玛那概率',a2,'一定確率で万象マナを1つ獲得',[(chain,['param1','param2','param3','param4','param6'])],'施法方','1stChain及以上',gap='实际候选是Extra附加1106记录43023617的.1参数；WaveSupport64.param6=20另用于目标数量，不能当此概率',shot='20%')
    put('other_a2_chain_count','能力二','Chain获得万象玛那数量',a2,'万象マナを1つ獲得',[(chain,['param0'])],'施法方','触发获得事件',answer='1个（原文明确）',kind='原文获得数量',basis='skill43023605.text',text_number=True,gap='具体数量字段对应尚未确认；不强行将param0当数量')
    put('other_a2_chain_limit','能力二','同一Chain获取次数上限',a2,'同じChain内で1つしか獲得できない',[],'施法方','同一个Chain',answer='最多1个（原文）',kind='原文同Chain上限',basis='skill43023605.text',text_number=True,gap='执行计数路径尚未核实')
    for field,name in (('param2','移动提升'),('param5','暴击率提升'),('param6','暴击伤害提升')):
        put('other_class_'+field,'Class','Class自身·'+name,job,'移動速度とクリティカル発生率とクリティカル威力',[(skill(65000001),[field])],'自身','Class配置包含cid30236',gap='Always3对应字段局部基准',shot={'param2':'100%','param5':'20%','param6':'200%'}[field])
    put('other_class_party_move','Class','Class全体·移动提升',job,'戦場にいる味方の攻撃力と防御力と移動速度',[(skill(65000002),['param2'])],'战场味方','Class配置包含cid30236',gap='1017.param2的移动乘算语义',shot='15%')
    put('other_class_heal_ratio','Class','暴击按伤害回复比例',job,'与えたダメージ量に応じて',[(skill(65000003),['param1'])],'自身','暴击攻击时',gap='ability21.param1=.25的伤害基数与回复路径；不从其他治疗类型套规则',shot='20%')
    put('other_class_overheal','Class','暴击回复的HP上限',job,'HPが上限を超えて回復',[(skill(65000003),['flag0_1'])],'自身','暴击回复时',gap='21的旗标装配到通用Heal上限；512不直接当40%',shot='超出40%（1.4倍上限）')
    extra=one('extra_ability_info','cid',30236)
    put('other_extra_initial_mana','Extra','Extra初始万象玛那数量',extra,'',[(skill(56000002),['str0']),(skill(56000001),['param7'])],'施法方','战斗开始；各Extra等级均同文案',answer='1个（五档原文相同）',kind='原文初始数量',basis='extra_ability_info.extra_abilities[].text',text_number=True)
    rows[-1].update(description_ja=[x['text'] for x in extra['raw']['extra_abilities']],description_field='/extra_abilities/*/text')
    leader=one('leader_ability','cid',30236)
    put('other_leader_threshold','Leader','Leader发动所需职业人数',leader,'',[(leader,['border','category','conditions'])],'队伍','Leader资格',gap='border=4的数量与category=2/conditions=[0]的职业/条件枚举处理尚待核实',shot='战士4人以上',desc_note='此text只写增益；资格数值来自配置/截图')
    symp=skill(43023610)
    put('other_symp_critical_damage','共鸣','常规共鸣暴击伤害提升',symp,'クリティカル威力が一定時間上がる',[(skill(43023611),['param8','param6'])],'战场味方','味方发动共鸣必杀；后备有效（原文）','45游戏秒',gap='Support3的暴击伤害聚合以0还是1为基准，不能当相对伤害乘1.1',shot='10%加算')
    put('other_symp_duration','共鸣','常规共鸣增强持续时间',symp,'一定時間上がる',[(skill(43023611),['param6'])],'战场味方','共鸣必杀触发',answer='45游戏秒',kind='持续时间',basis='timed_support/README.md',shot='45秒')
    put('other_symp_desert_duration','共鸣','MAXChain沙漠持续时间',symp,'地形を砂漠に一定時間変更',[(symp,['str0']),(pattern(43023604),['skillid0']),(boss(43023613),['skillparam5'])],'战场地形','MAXChain触发；自身必杀期间除外（原文）',gap='Boss66定时单位；条件资格另论',shot='300秒')
    put('other_symp_chain_limit','共鸣','MAXChain沙漠同Chain发动上限',symp,'同じChain内で1回しか発動しない',[],'本触发效果','同一Chain',answer='最多1次（原文明确）',kind='原文发动次数',basis='skill43023610.text',text_number=True,gap='触发计数的实际状态另论')
    bond=one('supporterskill','ability_id',30236)
    put('other_bond_initial_mana','羁绊','羁绊初始万象玛那数量',bond,'万象マナを1つ持った状態',[(skill(115010),['param7'])],'装备该羁绊的一方','战斗开始',answer='1个（原文明确）',kind='原文初始数量',basis='supporterskill.text及115010.text',shot='1',text_number=True)
