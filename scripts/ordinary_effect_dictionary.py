"""Reusable ordinary effects, merged into the existing dictionary and page."""
import html
import json
from pathlib import Path

PROOF=Path('output/ordinary_effects/ability1095')


def context_1008(record,trace):
    # Reuse only the proved terrain representation, never the type7 self scope.
    terrain=context_7(record,trace)
    code=record['raw']['param0'];condition=terrain['terrain_condition']
    return dict(trigger_zh=f'玩家侧计算当前接受者的攻防；候选提供者来自_aChara_Player，存活且活动，已安装数组筛出1008并通过资格；param0={code}拆为{condition["base100_groups_low_to_high"]}，当前背景flag满足编号{condition["terrain_indices_low_to_high"]}的或条件才乘本项；可含提供者自身，无接受者职业筛选',
        trigger_status='NATIVE_PLAYER_CANDIDATE_GUARD_TYPE_FILTER_CURRENT_TERRAIN_AND_MULTIPLY_CONFIRMED',
        terrain_condition=condition,current_stage=terrain['current_stage'],source_field_refs=terrain['source_field_refs'],missing_requested_fields=[],
        target=dict(subject='玩家侧正在计算的接受者；可为提供者自身或其他队友',status='PLAYER_MANAGER_RECIPIENT_AND_NO_SELF_OR_JOB_EXCLUSION_CONFIRMED',
            provider_candidate_list='_aChara_Player（BattleManager.GetAllCharaList(0)）',provider_gate='Unity对象非空、IsAlive通过、_isActive为真；再按已装数组/类型筛选1008',
            self_included=True,recipient_job_filter=False,distance_filter=False,
            limits_zh='候选列表内容、实际安装/解锁是夹具输入。非活动成员走独立后备路径，本轮未证明该路径提供1008；敌用同表记录保留，不据此声称玩家管理器会实际装入它。'),
        evidence=['../ordinary_effects/ability1008/'+f for f in ('README.md','trace.json','native_checks.json')]+['../ordinary_effects/ability7/trace.json'],
        limits_zh='仅当前37条的param0/1/3；玩家侧活动提供者的本项贡献，不代表完整叠加或最终HP。原文提及后备生效时保留原文，后备路径另核；param2/4/5不随本轮推广。背景名为表行标签，不是唯一正式枚举。')


def extend_1008(records,rules,views):
    proof=Path('output/ordinary_effects/ability1008');trace=json.loads((proof/'trace.json').read_text(encoding='utf-8'));checks=json.loads((proof/'native_checks.json').read_text(encoding='utf-8'))
    selected=[r for r in records if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==1008]
    assert selected==trace['source_records'] and trace['native_sha256']==checks['native_sha256']
    assert len(checks['checks'])==trace['native_check_count'] and all(c['passed'] for c in checks['checks'])
    template=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',1008,'/param1'))
    rules.append(dict(template,field_path='/param0'))
    paths=('/param0','/param1','/param3');target_rules={r['field_path']:r for r in rules if r['table']=='skilllist' and r['effect_type']==1008 and r['field_path'] in paths}
    assert len(target_rules)==3
    defs={
        '/param0':('全体强化的当前地形条件编码','十进制组合编号；转换为背景flag位集合','先向零截断，按两位十进制拆最多三组，各编号转位求或，与当前背景flag相交并去bit0，非零通过；不是接受者职业或自身排除开关'),
        '/param1':('地形条件通过时接受者本项攻击乘数','本项攻击倍率；派生增加百分比','接受者本项攻击因子乘param1；增加=(raw-1)×100%；本段不乘Chain'),
        '/param3':('地形条件通过时接受者本项受伤量乘数','本项受伤量倍率；派生减伤百分比','接受者本项受伤量因子乘param3；减伤=(1-raw)×100%；本段不乘Chain；1为中性，保留原值'),
    }
    for path,rule in target_rules.items():
        meaning,unit,conversion=defs[path];rule.update(meaning_zh=meaning,unit=unit,conversion=conversion,
            base_definition='当前背景battle_bg.flag；玩家侧正在计算的接受者本项攻防因子',
            applicability='仅当前v3 CACHE普通ability1008的37条、9种地形编码及存在的param0/param1/param3共111字段；不推广其他类型或字段',
            occurrences=37,unit_status='已确认（限定玩家侧对象、当前地形与局部乘算）',target='当前接受者，可含提供者自身；活动提供者来自_aChara_Player，无本类型职业/距离筛选',
            limits='原生类型/资格筛选执行，候选列表和安装数组为夹具；非活动成员转独立后备路径，未证明该路径提供1008。敌用同表数据保留但玩家侧实际装入另论。其他字段保持原范围，最终战斗另论。',
            evidence=list(dict.fromkeys(rule['evidence']+['../ordinary_effects/ability1008/'+f for f in ('README.md','trace.json','native_checks.json')]+['../ordinary_effects/ability7/trace.json'])))
    views[:]=[v for v in views if not (v['table']=='skilllist' and v['effect_type']==1008 and v['field_path'] in paths)]
    for r in selected:
        ctx=context_1008(r,trace)
        for path,rule in target_rules.items():
            field=path[1:];value=r['raw'][field]
            if field=='param0':
                converted=ctx['terrain_condition']['terrain_indices_low_to_high']
                display='地形编号'+str(converted)+'的或条件；匹配背景：'+'／'.join(ctx['terrain_condition']['matching_background_names_ja'])
            elif field=='param1':converted=(value-1)*100;display=f'接受者本项攻击{converted:+g}%（×{value:g}）'
            else:converted=(1-value)*100;display=f'接受者本项减伤{converted:g}%（受伤量×{value:g}）' if value!=1 else '接受者本项受伤量×1（中性原值）'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=r['raw']['skillid'],effect_type=1008,
                field_path=path,raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+path,
                meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=rule['conversion'],converted_value=converted,display_value=display,
                raw_value_status='RAW_FOUND',correspondence_status='SCOPED_TARGETSTAGEALL_PLAYER_RECIPIENT_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',
                conditions=ctx['trigger_zh'],evidence=rule['evidence'],limits=rule['limits'],trigger_context=ctx))


def context_7(record,trace):
    raw=record['raw'];code=raw['param0'];parts=[code%100,(code//100)%100,(code//10000)%100];indices=[i for i in parts if i]
    bg_by_id={r['raw']['id']:r for r in trace['background_source_records']}
    matched=[bg_by_id[i] for i in trace['code_background_matches'][str(code)]]
    names=list(dict.fromkeys(r['raw']['bg_name'] for r in matched))
    refs={f:dict(record_key=record['record_key'],field_path='/'+f,present=True,raw_value=raw[f],
                 json_pointer=record['location']['json_pointer']+'/'+f,source_sha256=record['source_sha256']) for f in ('param0','param1','param3')}
    condition=f'持有者自身的已选中ability7；param0={code}按两位十进制分组为{parts}；非零编号{indices}转成位并作或；与当前背景flag交集去掉bit0后非零才生效'
    conflict=dict(status='SOURCE_NAME_TEXT_CONFLICT_CODE_MATCHES_DESERT',code_condition_zh='param0=4命中沙漠flag16、拒绝森林flag4',
                  raw_name=raw.get('name'),raw_text=raw.get('text'),raw_preserved=True) if raw['skillid']==102071 else None
    return dict(trigger_zh=condition,trigger_status='NATIVE_ISENABLE7_CURRENT_STAGE_BG_FLAG_MATCH_CONFIRMED',
        terrain_condition=dict(field='/param0',raw_value=code,base100_groups_low_to_high=parts,terrain_indices_low_to_high=indices,
            mask_without_bit0=sum(1<<i for i in set(indices)),comparison='(编码掩码 & 当前battle_bg.flag & 0xfffffffe) != 0',
            status='ENCODING_AND_CURRENT_BG_FLAG_NATIVE_MATCH_CONFIRMED',matching_background_names_ja=names,
            matching_backgrounds=[dict(record_key=r['record_key'],id=r['raw']['id'],flag=r['raw']['flag'],bg_name_ja=r['raw']['bg_name'],
                original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location']) for r in matched]),
        target=dict(subject='持有该已选中能力的自身',status='SELF_EFFECT_PATH_CONFIRMED_INSTALLED_LIST_SUPPLIED'),
        current_stage=dict(source='GroundManager.GetStageNo -> daBattleInfo.GetBgFlag -> battle_bg.flag',
            status='NATIVE_CURRENT_STAGE_AND_ACTIVE_BG_OVERRIDE_PATH_CONFIRMED',limits_zh='数据查找返回实际源背景行；当前实例、地形变更时刻及完整查找装载是外部上下文'),
        source_field_refs=refs,missing_requested_fields=[],description_conflict=conflict,
        evidence=['../ordinary_effects/ability7/'+f for f in ('README.md','trace.json','native_checks.json')],
        limits_zh='仅本轮64条/三字段；其他TargetStage类型、sub效果资格、安装/解锁及完整战斗另论。背景名属于表行标签，位13/20等可跨多个背景名，不编造唯一正式中文枚举。param3>1为本项增伤，原值不钳到1。')


def extend_7(records,rules,views):
    proof=Path('output/ordinary_effects/ability7');trace=json.loads((proof/'trace.json').read_text(encoding='utf-8'));checks=json.loads((proof/'native_checks.json').read_text(encoding='utf-8'))
    selected=[r for r in records if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==7]
    assert selected==trace['source_records'] and trace['native_sha256']==checks['native_sha256']
    assert len(checks['checks'])==1390 and all(c['passed'] for c in checks['checks'])
    assert trace['background_source_records']==[r for r in records if r['table']=='battle_bg']
    template=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',7,'/param1'))
    rules.append(dict(template,field_path='/param0'))
    paths=('/param0','/param1','/param3');target_rules={r['field_path']:r for r in rules if r['table']=='skilllist' and r['effect_type']==7 and r['field_path'] in paths}
    assert len(target_rules)==3
    defs={
        '/param0':('地形条件编码（按两位十进制分组）','十进制组合编号；转换为背景flag位集合','先向零截断为整数，按%100、/100后%100、/10000后%100取最多三组；各组转1<<编号求或，与当前背景flag交集去掉bit0后非零才通过；当前源只用前两组'),
        '/param1':('地形条件通过时自身攻击乘数','本项攻击倍率；派生增加百分比','本项攻击因子乘param1；相对本项基准的增加=(param1-1)×100%；不乘Chain'),
        '/param3':('地形条件通过时自身受伤量乘数','本项受伤量倍率；派生减伤百分比（负值表示增伤）','本项受伤量因子乘param3；本项减伤=(1-param3)×100%；2/250表示本项增伤，不修成减伤或钳为1；不乘Chain'),
    }
    for path,rule in target_rules.items():
        meaning,unit,conversion=defs[path];rule.update(meaning_zh=meaning,unit=unit,conversion=conversion,
            base_definition='当前背景battle_bg.flag；已选中能力持有者自身的本项攻击/受伤量因子',
            applicability='仅当前v3 CACHE普通ability7的64条及13种param0编码，存在的param0/param1/param3共192字段；不推广1008等其他地形类型',
            occurrences=64,unit_status='已确认（地形编码/当前背景及局部乘算）',target='能力持有者自身；已装数组/实际解锁另论',
            limits='当前源param0均正整数，0/第三组只为代码对照；背景名不是唯一枚举，保留实际匹配背景记录。param3可为2/250，负减伤表示本项增伤，不能改原值。102071代码沙漠与源text森林冲突并列保留；其他字段、sub资格、最终叠加/HP未知。',
            evidence=list(dict.fromkeys(rule['evidence']+['../ordinary_effects/ability7/'+f for f in ('README.md','trace.json','native_checks.json')])))
    views[:]=[v for v in views if not (v['table']=='skilllist' and v['effect_type']==7 and v['field_path'] in paths)]
    for r in selected:
        ctx=context_7(r,trace)
        for path,rule in target_rules.items():
            field=path[1:];value=r['raw'][field]
            if field=='param0':
                converted=ctx['terrain_condition']['terrain_indices_low_to_high'];names=ctx['terrain_condition']['matching_background_names_ja']
                display='地形编号'+str(converted)+'的或条件；匹配背景：'+'／'.join(names)
            elif field=='param1':converted=(value-1)*100;display=f'本项攻击{converted:+g}%（×{value:g}）'
            else:
                converted=(1-value)*100
                display=f'本项减伤{converted:g}%（受伤量×{value:g}）' if value<1 else '本项受伤量×1（中性原值）' if value==1 else f'本项受伤量增加{-converted:g}%（×{value:g}；最终另论）'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=r['raw']['skillid'],effect_type=7,
                field_path=path,raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+path,
                meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=rule['conversion'],converted_value=converted,display_value=display,
                raw_value_status='RAW_FOUND',correspondence_status='SCOPED_TARGETSTAGE_SELF_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',
                conditions=ctx['trigger_zh'],evidence=rule['evidence'],limits=rule['limits'],trigger_context=ctx))


def context_99(record):
    raw=record['raw'];fields=('param0','param1','param2','param3','param7','param9','flag')
    refs={f:dict(record_key=record['record_key'],field_path='/'+f,present=f in raw,raw_value=raw.get(f),
                 json_pointer=record['location']['json_pointer']+'/'+f,source_sha256=record['source_sha256']) for f in fields}
    routes=[dict(damage_type=kind,enum_name=name,field='/'+field,present=field in raw,raw_value=raw.get(field),
                 status='SOURCE_ONE_NATIVE_THRESHOLD_ALLOWS_ROUTE' if field in raw else 'SOURCE_ABSENT_NATIVE_ZERO_SKIPS_BEFORE_RANDOM')
            for kind,name,field in ((0,'Normal','param1'),(1,'Skill','param3'),(2,'Critical','param2'))]
    enabled='／'.join({'Normal':'普通攻击','Skill':'技能','Critical':'暴击'}[r['enum_name']] for r in routes if r['present'])
    condition='本次Attack的Attacked返回值≥1，攻击附加能力标记通过；已安装列表筛出99且IsEnableAbility99默认分支通过；'
    condition+='本记录允许'+enabled+'（对应存在的触发参数均为1）；缺触发字段原生默认0跳过，不填源值；'
    condition+='param7/9施加到本次Attack传入的目标，Support2独立类别；不是战场全敌方遍历'
    return dict(trigger_zh=condition,trigger_status='NATIVE_ATTACK_DAMAGE_GATE_TYPE_FILTER_99_ELIGIBILITY_AND_PROBABILITY_ROUTES_CONFIRMED',
        positive_damage_gate=dict(source='CharaBehavior.Attacked return -> Attack.w24',minimum=1,status='BOUNDED_CALLER_GATE_CONFIRMED_RETURNED_DAMAGE_SUPPLIED'),
        probability_routes=routes,probability_comparison='先要求阈值≥Single.Epsilon，再以Random.Range(0,1)≤阈值通过；当前存在值全1，缺失默认0跳过',
        target=dict(subject='本次Attack传入的单个目标',status='NATIVE_TARGET_ARGUMENT_AND_SUPPORT2_CONTROLLER_CONFIRMED',
                    limits_zh='处理器不另选阵营；普通skilllist含敌用能力，可由敌方对玩家施加。实际攻击目标选择与最终HP另论。'),
        support_category=dict(name='Support2',field='CharaStatus._support2CtrlData',offset='0x230',multi_check=True,
                              default_normal_skill_incoming_bounds=[.5,2],status='NATIVE_ROUTE_AND_DEFAULT_CATEGORY_BOUNDS_CONFIRMED_REPEAT_MATCHING_PENDING'),
        duration=dict(field='/param0',raw_value=raw['param0'],status='POSITIVE_GAME_SECONDS' if raw['param0']>0 else 'SOURCE_MINUS_ONE_NO_POSITIVE_COUNTDOWN',
                      meaning_zh='正计时按游戏delta扣减' if raw['param0']>0 else '-1保留原值；此更新路径不扣正时间，在无其他移除条件夹具中保留；不承诺跨死亡/换波/覆盖永久'),
        self_support_branch='同次事件还向攻击者提交param4/5/6支持，目标分支使用param7/8/9；本轮不推广自身分支或其他移动记录',
        source_field_refs=refs,missing_requested_fields=[f for f in ('param7','param9','param0') if f not in raw],
        evidence=['../ordinary_effects/ability99/'+f for f in ('README.md','trace.json','native_checks.json')],
        limits_zh='真实安装/上游攻击目标、实际Attacked返回值及完整战斗另论；重复施加匹配/覆盖和其他移除路径未模拟。当前133条flag均0。其他参数保留原值，不补缺失。')


def extend_99(records,rules,views):
    proof=Path('output/ordinary_effects/ability99')
    trace=json.loads((proof/'trace.json').read_text(encoding='utf-8'));checks=json.loads((proof/'native_checks.json').read_text(encoding='utf-8'))
    selected=[r for r in records if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==99]
    assert selected==trace['source_records'] and trace['native_sha256']==checks['native_sha256']
    assert len(checks['checks'])==192 and all(c['passed'] for c in checks['checks'])
    paths=('/param7','/param9','/param0');ev=['../ordinary_effects/ability99/'+f for f in ('README.md','trace.json','native_checks.json')]
    target_rules={r['field_path']:r for r in rules if r['table']=='skilllist' and r['effect_type']==99 and r['field_path'] in paths}
    assert len(target_rules)==3
    definitions={
        '/param7':('受击目标攻击倍率的加算贡献','Support2攻击倍率增量；显示百分点','param7直接写目标_attack；普通/技能攻击同类汇总=clamp(1+Σ(_attack+_attackNormal/Skill))；单项-.3形成本类别因子.7，不乘Chain'),
        '/param9':('受击目标受伤量倍率的加算贡献','Support2受伤量倍率增量；显示百分点','param9直接写目标_defense；同类受伤量汇总=clamp(1+Σ_defense)；单项+.3形成本类别因子1.3，不是固定防御减少30%，不乘Chain'),
        '/param0':('PowerDrain支持计时输入（正秒数或-1标记）','正值为游戏秒；-1为无正计时标记','正10/20/30/60原样存入Support2支持时间及完整时间，按游戏delta扣减；源-1保存-1并跳过正时间扣减，其他移除条件另论；不乘Chain'),
    }
    for path,rule in target_rules.items():
        meaning,unit,conversion=definitions[path]
        rule.update(meaning_zh=meaning,unit=unit,conversion=conversion,
            applicability='仅当前v3 CACHE普通ability99的133条记录中存在的param7/param9/param0（126/123/133）；已进入Attack正返回伤害附加阶段并选出本能力时',
            occurrences=trace['field_counts'][path[1:]],base_definition='目标Support2普通/技能攻击或受伤量倍率基准1；param0是两次支持提交共用的计时输入',
            unit_status='已确认（限定Support2加算/正计时及源-1路径）',target='param7/9为本次受击目标；param0同时用于攻击者和目标两次提交',
            limits='只推广本类型存在字段；缺param7的7条、缺param9的10条不填0，其他参数不推广。默认类别倍率夹紧[.5,2]；重复施加匹配/覆盖、跨类别叠加/实际HP及死亡/换波等清除未知。源-1不当-1秒或无条件永久。普通表中的敌用能力仍保留，不能限制为玩家施加。',
            evidence=list(dict.fromkeys(rule['evidence']+ev)))
    views[:]=[v for v in views if not (v['table']=='skilllist' and v['effect_type']==99 and v['field_path'] in paths)]
    for r in selected:
        ctx=context_99(r)
        for path,rule in target_rules.items():
            field=path[1:]
            if field not in r['raw']:continue
            value=r['raw'][field];converted=value if field=='param0' else value*100
            display=(f'{value:g}游戏秒（正支持计时）' if value>0 else '-1：无正时间倒计时；其他清除/覆盖另论') if field=='param0' else f'目标攻击倍率{value:+g}（{converted:+g}个百分点；单项因子{1+value:g}）' if field=='param7' else f'目标受伤量倍率{value:+g}（{converted:+g}个百分点；单项因子{1+value:g}）'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=r['raw']['skillid'],effect_type=99,
                field_path=path,raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+path,
                meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=rule['conversion'],converted_value=converted,display_value=display,
                raw_value_status='RAW_FOUND',correspondence_status='SCOPED_POWERDRAIN_TARGET_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',
                conditions=ctx['trigger_zh'],evidence=rule['evidence'],limits=rule['limits'],trigger_context=ctx))


def context_3000(record):
    """Shared source-only context, including records with no requested fields."""
    raw=record['raw'];fields=('param0','iParam0','param9','param1','param2','param6','param8','flag','flag0_0','flag0_1')
    refs={f:dict(record_key=record['record_key'],field_path='/'+f,present=f in raw,raw_value=raw.get(f),
                 json_pointer=record['location']['json_pointer']+'/'+f,source_sha256=record['source_sha256']) for f in fields}
    mask=raw.get('iParam0');mode=raw.get('param0');home=raw.get('param9')
    job_names=('战士','弓手','法师','僧侣','骑士','ALMIGHTY')
    jobs=[job_names[i] for i in range(6) if mask and mask&(1<<i)]
    selector='param0=1遍历本次候选列表；回调只接受存活且_isActive的成员' if mode==1 else '源param0缺失；运行时构造默认0走能力持有者自身，且须存活/活动；不导出源值0'
    condition='共鸣标记的技能开始事件；队伍共鸣标记开启、发动者为存活玩家；持有者存活/有共鸣能力/非Hero；'
    condition+=('发动者职业命中iParam0='+str(mask)+'（'+'／'.join(jobs)+'）；') if mask else '源iParam0缺失，原生getter0绕过此职业筛选；'
    condition+=f'param9={home}交给IsTargetHome筛选发动者所属（枚举名称未推广）；' if home is not None else '源param9缺失，原生getter0绕过此所属筛选；'
    condition+=selector+'；本批flag与已核武器掩码交集全0，绕过武器限制；候选列表/实际安装另论'
    return dict(trigger_zh=condition,trigger_status='SCOPED_NATIVE_SYMPATHY_GATES_CONFIRMED_RUNTIME_INPUTS_PENDING',
        support_category=dict(name='Support3',field='CharaStatus._support3CtrlData',offset='0x238',shared_aggregator_class='SupportType2CtrlData',
                              default_normal_skill_bounds=[.5,2],default_critical_damage_delta_bounds=[-1.5,1],status='NATIVE_ROUTE_AND_DEFAULT_CONSTRUCTOR_CONFIRMED_OVERRIDES_PENDING'),
        triggering_job_filter=dict(field='/iParam0',present='iParam0' in raw,raw_value=mask,job_names_zh=jobs,
                                   subject='发动共鸣的角色；不是支持接受者',status='BITMASK_GATE_CONFIRMED' if mask is not None else 'SOURCE_ABSENT_NATIVE_ZERO_BYPASS'),
        triggering_home_filter=dict(field='/param9',present='param9' in raw,raw_value=home,subject='发动共鸣的角色；不是支持接受者',
                                    status='NATIVE_ISTARGETHOME_INPUT_AND_GATE_CONFIRMED_ENUM_NAMES_PENDING' if home is not None else 'SOURCE_ABSENT_NATIVE_ZERO_BYPASS'),
        recipient_selector=dict(field='/param0',present='param0' in raw,raw_value=mode,meaning_zh=selector),
        weapon_filter=dict(source_fields={f:raw[f] for f in ('flag','flag0_0','flag0_1') if f in raw},
                           mask=0x7fc00000,source_intersection=0,
                           status='NATIVE_INITIALIZED_MASK_CONFIRMED_ALL382_SOURCE_FLAGS_BYPASS_WEAPON_GATE'),
        source_field_refs=refs,missing_requested_fields=[f for f in ('param1','param2','param6','param8') if f not in raw],
        evidence=['../ordinary_effects/ability3000/'+f for f in ('README.md','trace.json','native_checks.json')],
        limits_zh='候选列表/真实后备范围、安装/共鸣标记设置、武器条件完整映射、重施加/到期移除及最终战斗结果另论。缺param6不推定永久或0秒；其他参数不随四字段推广。')


def extend_3000(records,rules,views):
    proof=Path('output/ordinary_effects/ability3000')
    trace=json.loads((proof/'trace.json').read_text(encoding='utf-8'));checks=json.loads((proof/'native_checks.json').read_text(encoding='utf-8'))
    selected=[r for r in records if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==3000]
    assert selected==trace['source_records'] and trace['native_sha256']==checks['native_sha256']
    assert len(checks['checks'])==86 and all(c['passed'] for c in checks['checks'])
    fields=('/param1','/param2','/param6','/param8')
    target_rules={r['field_path']:r for r in rules if r['table']=='skilllist' and r['effect_type']==3000 and r['field_path'] in fields}
    assert len(target_rules)==4
    definitions={
        '/param1':('普通攻击的加算贡献','Support3普通攻击倍率1的加算增量；显示百分点','param1写TimePowerUpData._attackNormal；本类别普通攻击汇总为1+各项(_attack+_attackNormal)，再按类别边界夹紧；不乘Chain'),
        '/param2':('技能攻击的加算贡献','Support3技能攻击倍率1的加算增量；显示百分点','param2写TimePowerUpData._attackSkill；本类别技能攻击汇总为1+各项(_attack+_attackSkill)，再按类别边界夹紧；不乘Chain'),
        '/param6':('共鸣临时支持的正持续时间输入','游戏秒','存在的正param6原样传setSupport3，再进入共用时间存储；正计时扣游戏delta；不乘Chain'),
        '/param8':('共鸣临时支持的暴击伤害系数加算贡献','暴伤系数增量；显示百分点','param8直接写_criticalDmgRate，同Support3类别加算；不减1.5，不乘Chain；不是相对现有暴击伤害再乘百分比'),
    }
    for path,rule in target_rules.items():
        meaning,unit,conversion=definitions[path]
        rule.update(meaning_zh=meaning,unit=unit,conversion=conversion,
            applicability='仅当前v3 CACHE普通ability3000的382条记录中实际存在的param1/param2/正param6/param8，共348条有本轮字段；不推广其他共鸣类型',
            occurrences=trace['field_counts'][path[1:]],unit_status='已确认（限定Support3读取/提交及正时间路径）',
            base_definition='本项Support3配置贡献；普通/技能攻击以1为基准，暴伤增量以0为基准，时间独立',
            target='param0控制的候选支持接受者；iParam0/param9检查共鸣发动者，不能当接受者筛选',
            limits='缺字段不补0，34条没有本轮四字段；缺时间不推定永久。Support3独立控制器默认普通/技能倍率[.5,2]、暴伤增量[-1.5,1]；覆盖设置/全战斗叠加/最终HP未知。资格配置与实际安装分开；已核本批全部绕过武器限制，完整武器名称映射及实际候选名单另论。',
            evidence=list(dict.fromkeys(rule['evidence']+['../ordinary_effects/ability3000/'+f for f in ('README.md','trace.json','native_checks.json')])))
    views[:]=[v for v in views if not (v['table']=='skilllist' and v['effect_type']==3000 and v['field_path'] in fields)]
    for r in selected:
        context=context_3000(r)
        for path,rule in target_rules.items():
            field=path[1:]
            if field not in r['raw']:continue
            value=r['raw'][field];converted=value if field=='param6' else value*100
            display=f'{value:g}游戏秒（正支持计时输入）' if field=='param6' else f'暴击伤害系数+{value:g}（+{converted:g}个百分点；Support3贡献）' if field=='param8' else f'{"普通攻击" if field=="param1" else "技能攻击"}倍率+{value:g}（+{converted:g}个百分点；Support3贡献）'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=r['raw']['skillid'],effect_type=3000,
                field_path=path,raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+path,
                meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=rule['conversion'],converted_value=converted,display_value=display,
                raw_value_status='RAW_FOUND',correspondence_status='SCOPED_SUPPORT3000_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',
                conditions=context['trigger_zh'],evidence=rule['evidence'],limits=rule['limits'],trigger_context=context))


def extend_2012(records,rules,views):
    proof=Path('output/ordinary_effects/ability2012')
    trace=json.loads((proof/'trace.json').read_text(encoding='utf-8'))
    checks=json.loads((proof/'native_checks.json').read_text(encoding='utf-8'))
    selected=[r for r in records if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==2012]
    assert selected==trace['source_records'] and trace['native_sha256']==checks['native_sha256']
    assert len(checks['checks'])==49 and all(c['passed'] for c in checks['checks'])
    ev=['../ordinary_effects/ability2012/README.md','../ordinary_effects/ability2012/trace.json','../ordinary_effects/ability2012/native_checks.json']
    scope='仅当前v3 CACHE普通ability2012的406条记录：存在的正param0及有限param4/param5；已进入技能动作OnAction附加能力列表且目标选中时'
    limits='只解释本项计时/暴击贡献；不是暴击命中触发或按param4概率施加支持。完整目标名单/实际安装/动作时刻/重施加及最终HP另论。param4/5缺失保持缺失，不导出默认0；当前iParam0均缺失，原生getter读0免额外职业过滤，不能当源字段0。2012的param8=31是TARGET_TYPE.pGROUP_ALL，不是1017职业位图。'
    template=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',2012,'/param4'))
    rules.append(dict(template,field_path='/param0',meaning_zh='临时支持的正持续时间输入',unit='游戏秒',
                      conversion='正param0原样传setSupport2支持时间，Support2正计时按游戏delta扣减；不乘Chain系数',
                      base_definition='本项Support2计时；精确结束/重施加另论'))
    target_rules={r['field_path']:r for r in rules if r['table']=='skilllist' and r['effect_type']==2012 and r['field_path'] in ('/param0','/param4','/param5')}
    assert len(target_rules)==3
    for path,rule in target_rules.items():
        rule.update(applicability=scope,occurrences=trace['field_counts'][path[1:]],limits=limits,
                    target='GetMemberList及后续筛选选出的支持接受者；完整名单另论',evidence=list(dict.fromkeys(rule['evidence']+ev)))
    views[:]=[v for v in views if not (v['table']=='skilllist' and v['effect_type']==2012 and v['field_path'] in target_rules)]
    selector_names={e['default']['value']:e['name'] for e in trace['target_selector_enum']}
    for r in selected:
        raw=r['raw'];selector=raw['param8'];limit=raw.get('param7')
        refs={field:dict(record_key=r['record_key'],field_path='/'+field,present=field in raw,raw_value=raw.get(field),
                         json_pointer=r['location']['json_pointer']+'/'+field,source_sha256=r['source_sha256'])
              for field in ('param0','param4','param5','param7','param8','iParam0')}
        context=dict(trigger_zh='技能动作OnAction附加能力阶段；_isSkillAbilityAction尚为false；该轮列表处理完置true，后续调用跳过2012',
                     trigger_status='NATIVE_ACTION_DISPATCH_AND_PROCESSED_GATE_CONFIRMED',
                     target_selector=dict(field='/param8',raw_value=selector,enum_name=selector_names[selector],
                                          status='ENUM_AND_CALL_INPUT_CONFIRMED_TARGET_POPULATION_PENDING'),
                     target_limit=dict(field='/param7',present='param7' in raw,raw_value=limit,
                                       status='POSITIVE_NATIVE_LOOP_LIMIT_CONFIRMED' if limit is not None else 'SOURCE_ABSENT_NO_LIMIT_FILLED'),
                     additional_job_filter=dict(field='/iParam0',present=False,raw_value=None,
                                                status='SOURCE_ABSENT_NATIVE_ZERO_GETTER_BYPASS_CONFIRMED'),
                     source_field_refs=refs,missing_requested_fields=[f for f in ('param0','param4','param5') if f not in raw],evidence=ev,
                     limits_zh='GetMemberList目标列表和bAll由夹具提供；未验证实际全体/后备/搭档范围或动作事件外部重置。缺失param7不补1或20。')
        conditions=context['trigger_zh']+f'；param8={selector}（{selector_names[selector]}）'
        conditions+=f'，正param7={limit}限制应用数量' if limit is not None else '，param7缺失，完整目标数量另论'
        conditions+='；当前iParam0缺失，getter免额外职业筛选；实际安装及目标名单另论'
        for path,rule in target_rules.items():
            field=path[1:]
            if field not in raw:continue
            value=raw[field];converted=value if field=='param0' else value*100
            display=f'{value:g}游戏秒（正支持计时输入）' if field=='param0' else f'暴击率+{converted:g}个百分点（Support2加算贡献）' if field=='param4' else f'暴击伤害系数+{value:g}（+{converted:g}个百分点；Support2加算）'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=raw['skillid'],effect_type=2012,
                              field_path=path,raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+path,
                              meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=rule['conversion'],converted_value=converted,display_value=display,
                              raw_value_status='RAW_FOUND',correspondence_status='SCOPED_SUPPORT2012_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',
                              conditions=conditions,evidence=list(rule['evidence']),limits=limits,trigger_context=context))


def extend_1017(records,rules,views):
    proof=Path('output/ordinary_effects/ability1017')
    trace=json.loads((proof/'trace.json').read_text(encoding='utf-8'))
    checks=json.loads((proof/'native_checks.json').read_text(encoding='utf-8'))
    selected=[r for r in records if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==1017]
    assert selected==trace['source_records'] and trace['native_sha256']==checks['native_sha256']
    assert len(checks['checks'])==236 and all(c['passed'] for c in checks['checks'])
    ev=['../ordinary_effects/ability1017/README.md','../ordinary_effects/ability1017/trace.json','../ordinary_effects/ability1017/native_checks.json']
    scope='仅当前v3 CACHE普通ability1017的321条记录及param0/iParam0/param1/param3；候选提供者及已安装1017列表已选定时'
    limits='实际候选成员/后备范围、活动条件和完整安装仍另论。所有源param0均为1，0/.5等仅为对照夹具；param0先向零截断，非零允许提供者自身，仍须职业匹配。iParam0按接受者职业位筛选，31只含0..4，不含ALMIGHTY5。仅本项乘算，不给出最终攻击/总减伤/HP；其他参数及类型不推广。'
    template=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',1017,'/param1'))
    for path,meaning,unit,conversion,base in (
        ('/param0','提供者自身参与开关（先截断）','对象筛选配置；不是人数或百分比','当前源值1允许提供者自身；有限值trunc(param0)=0时仅排除提供者自身，其他接受者仍须职业匹配','提供者BattleParam与接受者BattleParam是否相同'),
        ('/iParam0','接受者职业位图','位图；bit=1<<JobType','(iParam0 & (1 << 接受者._jobType)) != 0；多个职业位是或关系','JobType元数据枚举；0战士/1弓手/2法师/3僧侣/4骑士/5 ALMIGHTY'),
    ):
        rules.append(dict(template,field_path=path,meaning_zh=meaning,unit=unit,conversion=conversion,base_definition=base))
    target_rules={r['field_path']:r for r in rules if r['table']=='skilllist' and r['effect_type']==1017 and r['field_path'] in ('/param0','/iParam0','/param1','/param3')}
    assert len(target_rules)==4
    for rule in target_rules.values():
        rule.update(applicability=scope,occurrences=len(selected),limits=limits,target='候选能力接受者；param0允许自身时仍需接受者职业命中iParam0',evidence=list(dict.fromkeys(rule['evidence']+ev)))
    views[:]=[v for v in views if not (v['table']=='skilllist' and v['effect_type']==1017 and v['field_path'] in target_rules)]
    for r in selected:
        raw=r['raw'];mask=raw['iParam0']
        jobs=[j for j in trace['job_enum'] if mask&j['bit']]
        labels='／'.join(j['meaning_zh'] for j in jobs)
        conditions=f'候选提供者的1017能力已进入列表；param0={raw["param0"]}允许自身及其他接受者，仍需iParam0={mask}命中接受者职业（{labels}）；完整名单/活动资格另论'
        for path,rule in target_rules.items():
            value=raw[path[1:]]
            if path=='/param0':
                converted=int(value);display='允许提供者自身参与（非仅自身）；仍须职业掩码命中'
            elif path=='/iParam0':
                converted=[j['default']['value'] for j in jobs];display=f'职业位图{mask}：{labels}；按接受者职业匹配'
            elif path=='/param1':
                converted=(value-1)*100;display=f'攻击+{converted:g}%（本项×{value:g}）'
            else:
                converted=(1-value)*100;display=f'本项减伤{converted:g}%（受伤量×{value:g}）'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=raw['skillid'],effect_type=1017,
                              field_path=path,raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+path,
                              meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=f'接受者职业：{labels}；提供者自身也须匹配',conversion=rule['conversion'],
                              converted_value=converted,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='ORDINARY_HANDLER_MAPPING_CONFIRMED',
                              calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=conditions,evidence=list(rule['evidence']),limits=limits))


def extend_1095(records,rules,views):
    trace=json.loads((PROOF/'trace.json').read_text(encoding='utf-8'))
    checks=json.loads((PROOF/'native_checks.json').read_text(encoding='utf-8'))
    selected=[r for r in records if r['layer']=='CACHE' and r['table']=='skilllist' and r['raw'].get('ability')==1095]
    assert selected==trace['source_records'] and trace['native_sha256']==checks['native_sha256']
    assert len(checks['checks'])==32 and all(c['passed'] for c in checks['checks'])
    ev=['../ordinary_effects/ability1095/README.md','../ordinary_effects/ability1095/trace.json','../ordinary_effects/ability1095/native_checks.json']
    scope='当前v3 CACHE/skilllist中ability=1095的407条记录，仅存在的有限数值param1/param3；接受者已装有本能力且IsEnableAbility资格通过时'
    limits='按类型读取当前记录，未见数值按技能ID分叉；8个代表ID/两字段/资格真假的32项片段检查通过。资格由夹具供给，实际安装、Leader/Extra来源触发与完整叠加未知；不计算最终攻击或最终HP。其他字段/类型/命名空间不随本轮推广，缺失字段不补零。'
    views[:]=[v for v in views if not (v['table']=='skilllist' and v['effect_type']==1095 and v['field_path'] in ('/param1','/param3'))]
    for field in ('param1','param3'):
        rule=next(r for r in rules if (r['table'],r['effect_type'],r['field_path'])==('skilllist',1095,'/'+field))
        rule.update(applicability=scope,occurrences=len(selected),limits=limits,
                    target='装有此能力的接受者自身；安装来源/资格另论',evidence=rule['evidence']+ev)
        for r in selected:
            value=r['raw'][field]
            percent=(value-1)*100 if field=='param1' else (1-value)*100
            display=f'攻击+{percent:g}%（本项×{value:g}）' if field=='param1' else f'本项减伤{percent:g}%（受伤量×{value:g}）'
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',
                              record_id=r['raw']['skillid'],effect_type=1095,field_path='/'+field,raw_value=value,
                              original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],
                              json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=rule['meaning_zh'],unit=rule['unit'],
                              target=rule['target'],conversion=rule['conversion'],converted_value=percent,display_value=display,
                              raw_value_status='RAW_FOUND',correspondence_status='ORDINARY_HANDLER_MAPPING_CONFIRMED',
                              calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=list(rule['evidence']),limits=limits))
    bykey={r['record_key']:r for r in records}
    for view in views:
        raw=bykey.get(view['record_key'],{}).get('raw',{})
        view['skill_name_ja']=raw.get('name',raw.get('sname'))
        view['skill_text_ja']=raw.get('text',raw.get('sinfo'))
        view.setdefault('trigger_context',None)


def render_reusable_effects(views,effect_type=1095,records=None):
    esc=html.escape
    assert effect_type in (7,99,1008,1095,1017,2012,3000)
    paths=('/param0','/param1','/param3') if effect_type in (7,1008) else ('/param7','/param9','/param0') if effect_type==99 else ('/param1','/param2','/param6','/param8') if effect_type==3000 else ('/param0','/param4','/param5') if effect_type==2012 else ('/param0','/iParam0','/param1','/param3')
    selected=[v for v in views if v['table']=='skilllist' and v['effect_type']==effect_type and v['field_path'] in paths]
    grouped={}
    for view in selected:grouped.setdefault(view['record_id'],{})[view['field_path']]=view
    source3000={r['raw']['skillid']:r for r in records or [] if r['table']=='skilllist' and r['raw'].get('ability')==3000}
    if effect_type==3000:
        assert len(source3000)==382
        for sid in source3000:grouped.setdefault(sid,{})
    count=len(grouped);title={1008:'TargetStageAll地形条件全体强化',7:'TargetStage地形条件自身强化',99:'PowerDrain受击目标弱化（Support2）',1095:'自身常驻强化',1017:'全体／职业攻防强化',2012:'临时支持的时间／暴击字段',3000:'共鸣临时支持（Support3）'}[effect_type]
    section_id='reusable-dictionary' if effect_type==1095 else 'reusable-dictionary-'+str(effect_type)
    gate_note={1008:'param0按两位十进制分组匹配当前背景flag，607为7或6。存活活动提供者来自玩家列表，贡献给当前接受者，可含自身且无本类型职业/距离筛选；非活动提供者走独立后备路径，不能据文本推定1008直接生效。param1乘攻击、param3乘受伤量，1为中性；其他字段保持旧范围。',7:'param0按两位十进制分组转背景flag位条件；4是沙漠编号，对应flag16。1320是20或13，325是25或3。param1乘攻击、param3乘受伤量；2/250为本项增伤。字段均存在，源内文本冲突保留。',99:'param7为目标攻击增量，param9为目标受伤量增量；-.3/+.3分别形成独立单项因子.7/1.3。param0正值10/20/30/60为游戏秒，源-1无正倒计时，其他清除另论。Normal/Skill/Critical触发分别看param1/3/2，本次Attack返回伤害≥1后施加到传入目标；缺字段不补0。',1095:'param1是攻击乘数；param3是受伤量乘数。',1017:'param1是攻击乘数；param3是受伤量乘数。param0源值均为1，允许自身但不免除职业条件；iParam0=31含0..4，不含ALMIGHTY5。',2012:'param0为正持续时间，param4加暴击概率，param5加暴伤系数；两暴击量不乘Chain。仅308条有param4、311条有param5，缺失不补0。技能动作OnAction首轮选中目标时施加，不是暴击命中时触发。param8=31是目标选择器pGROUP_ALL。',3000:'param1/2分别为普通/技能攻击加算，param6为存在的45/60游戏秒，param8为暴伤系数加算，四项不乘Chain。iParam0/param9筛选共鸣发动者，param0控制支持接受者。仅348条有本轮字段，另34条四项全缺失，明确保留；不推定0或永久。'}[effect_type]
    value_columns=(('/param0','param0 / 地形编码'),('/param1','param1 / 攻击倍率'),('/param3','param3 / 受伤量倍率')) if effect_type in (7,1008) else (('/param7','param7 / 目标攻击加算'),('/param9','param9 / 目标受伤量加算'),('/param0','param0 / 计时输入')) if effect_type==99 else (('/param1','param1 / 普攻加算'),('/param2','param2 / 技能攻击加算'),('/param6','param6 / 游戏秒'),('/param8','param8 / 暴伤加算')) if effect_type==3000 else (('/param0','param0 / 游戏秒'),('/param4','param4 / 暴击率加算'),('/param5','param5 / 暴伤系数加算')) if effect_type==2012 else (('/param1','param1 / 攻击'),('/param3','param3 / 受伤量'))
    headings=''.join('<th>'+label+'</th>' for path,label in value_columns)
    out=f'<section id="{section_id}"><h2>可复用字段字典 · ability{effect_type} {title}</h2><p>当前缓存{count}条普通技能记录，{len(selected)}个已解释字段。{gate_note}只解释本项配置贡献，实际安装/资格及其他字段另论。记录条数不等于角色数。</p><p><a href="verified_parameter_views.csv">带名称的原值/解释CSV</a> · <a href="field_dictionary.json">限定规则字典</a> · <a href="../ordinary_effects/ability{effect_type}/README.md">适用范围与检查依据</a></p><details><summary>展开并按技能名称、技能ID或原文检索{count}条记录</summary><input id="type{effect_type}-search" placeholder="技能ID、日文名或原文片段"><p id="type{effect_type}-count">{count}条记录</p><div style="max-height:600px;overflow:auto"><table><thead><tr><th>普通技能身份</th><th>游戏原文</th>{headings}<th>条件与来源</th></tr></thead><tbody>'
    for sid,fields in grouped.items():
        if effect_type==3000 and not fields:
            r=source3000[sid];context=context_3000(r)
            a=dict(record_key=r['record_key'],table=r['table'],namespace='ordinary skilllist',record_id=sid,effect_type=3000,
                original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],evidence=context['evidence'],limits=context['limits_zh'],
                skill_name_ja=r['raw'].get('name'),skill_text_ja=r['raw'].get('text'),conditions=context['trigger_zh'],trigger_context=context,
                raw_value_status='REQUESTED_SOURCE_FIELDS_ABSENT',correspondence_status='NO_PRESENT_REQUESTED_FIELD',calculation_status='NO_VALUE_FILLED')
        else:a=next(iter(fields.values())) if effect_type==3000 else fields['/param0'] if effect_type in (7,99,1008,2012) else fields['/param1']
        source={k:a[k] for k in ('record_key','table','namespace','record_id','effect_type','original_file','source_sha256','location','evidence','limits')}
        out+='<tr data-reusable-type="'+str(effect_type)+'" data-reusable-id="'+str(sid)+'"><td>'+str(sid)+'<br>'+esc(a['skill_name_ja'] or '')+'</td><td>'+esc(a['skill_text_ja'] or '本记录未带text；不补写原文')+'</td>'
        for path,label in value_columns:
            if path not in fields:
                out+='<td data-missing-field="'+esc(path)+'">源记录缺失该字段（不补0）</td>'
            else:
                v=fields[path]
                out+='<td>原值 '+esc(str(v['raw_value']))+'<br><b>'+esc(v['display_value'])+'</b><br>'+esc(v['json_pointer'])+'</td>'
        gate_fields=[{k:fields[path][k] for k in ('field_path','raw_value','display_value','json_pointer')} for path in ('/param0','/iParam0') if path in fields and effect_type==1017]
        gate_html=''.join('<p>'+esc(g['field_path'])+'='+esc(str(g['raw_value']))+'；'+esc(g['display_value'])+'</p>' for g in gate_fields)
        out+='<td>'+gate_html+esc(a['conditions'])+'<details><summary>完整定位、确认状态及边界</summary><pre>'+esc(json.dumps(dict(source,gate_fields=gate_fields,trigger_context=a['trigger_context'],raw_value_status=a['raw_value_status'],correspondence_status=a['correspondence_status'],calculation_status=a['calculation_status']),ensure_ascii=False,indent=2))+'</pre></details></td></tr>'
    return out+'</tbody></table></div></details><script>document.querySelector("#type'+str(effect_type)+'-search").oninput=function(){let q=this.value.toLowerCase(),n=0;document.querySelectorAll(\'tr[data-reusable-type="'+str(effect_type)+'"]\').forEach(r=>{r.hidden=!r.textContent.toLowerCase().includes(q);if(!r.hidden)n++});document.querySelector("#type'+str(effect_type)+'-count").textContent=n+"条记录";};</script></section>'
