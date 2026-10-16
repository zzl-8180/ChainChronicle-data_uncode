"""One description effect per row; card-specific inventory, not a global interpreter."""
import html
import json
import unicodedata
from pathlib import Path
from chica_remaining_effects import add_remaining_effects, critical_overlay, movement_overlay, lifesteal_overlay, field_time_overlay, mana_chance_overlay, chain_mana_overlay, leader_condition_overlay, super_counter_overlay, wedge_time_overlay


EFFECT_UNITS={
    '技能基值倍率':'倍（相对B或B_set）','攻击增加比例':'百分比（另受请求系数影响）',
    '固定防御量（系数已知）':'固定防御数值；系数相对当前normalAtk','攻击倍率':'倍；派生增加百分比',
    '屏障固定防御量系数':'接受者当前normalAtk的倍数，另乘请求系数','必杀请求系数乘数（ExtraChainRate）':'倍；派生威力增加百分比',
    '攻击加算增量':'倍率增量；派生百分比','受伤量加算增量':'倍率增量；派生减伤百分点','受伤量倍率':'倍；派生本项减伤百分比',
    '原文Chain威力提升量数值':'百分比（原文明示）','次数上限':'次（尝试/爆发范围见对象与条件）',
    '时间间隔':'游戏秒','层数':'层/位置','位置数量':'位置/段','移动因子增加量':'倍率增量，另乘请求系数',
    '暴击概率加算贡献':'概率增量；派生百分点','暴击伤害系数加算贡献':'暴击伤害倍率增量；派生百分点',
    '持续时间':'游戏秒','玛那数量配置':'个玛那','玛那数量差':'个玛那','原文耗玛那数量':'个玛那',
    '原文获得数量':'个玛那','超共鸣共用计数门槛':'次合格计数事件（队伍共用）',
    '暴击伤害系数加算贡献（先减1.5基准）':'暴击伤害倍率增量；派生百分点','初始数量':'个时楔',
    '普通时楔释放的停止时长输入':'游戏秒','击杀玛那基础概率':'概率百分比','原文条件与已核地形阈值':'概率百分比/0至1阈值',
    '地形变化的正持续时间':'游戏秒','保护次数':'次（完整消耗资格另论）','移动速度因子加算增量':'速度倍率增量；派生百分比',
    '原文攻击次数':'次暴击攻击','移动速度乘数':'倍；派生速度增加百分比','攻击间隔乘数':'间隔倍率；名义时间为游戏秒',
    '原文Chain门槛':'Chain档（原文）','Chain档位获珠概率阈值':'概率百分比/0至1阈值','Chain获珠数量':'个玛那',
    '原文同Chain上限':'个玛那/同Chain','暴击回复比例':'百分比（伤害处理返回整数的比例）','暴击回复HP上限档位':'倍最大HP',
    '原文初始数量':'个玛那','Leader职业人数资格':'名（职业条件命中者）','原文发动次数':'次/同Chain',
}


def fallback_records():
    proof=json.loads(Path('output/card_comparison_cid30236/skill_power/trace.json').read_text(encoding='utf-8'))
    return [r for r in proof['source_records'] if r['layer']=='APK_AB']


def difference_source_overlay(records,rules,views):
    """Annotate existing scoped rules/views; older records never become game inputs."""
    proof=json.loads(Path('output/card_comparison_cid30236/difference_sources/trace.json').read_text(encoding='utf-8'))
    ev=['difference_sources/README.md','difference_sources/trace.json','difference_sources/reference_observations.json']
    for case in proof['cases']:
        assert case['current_record'] in records and all(f['exact_match'] for f in case['fields'])
        paths={f['field_path'] for f in case['fields']}
        for view in views:
            if view['table']==case['table'] and view['record_id']==case['record_id'] and view['field_path'] in paths:
                view['evidence']=list(dict.fromkeys(view['evidence']+ev))
                view['limits']+='；'+case['finding']
        for rule in rules:
            if rule['table']==case['table'] and rule['effect_type']==case['effect_type'] and rule['field_path'] in paths:
                rule['evidence']=list(dict.fromkeys(rule['evidence']+ev))
                rule['limits']+='；以下旧来源备注仅限'+case['table']+'/'+str(case['record_id'])+'：'+case['finding']


def barrier_overlay(records):
    root=Path('output/card_comparison_cid30236/barrier')
    trace=json.loads((root/'trace.json').read_text(encoding='utf-8'));checks=json.loads((root/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    r=trace['source_records'][0];assert r in records
    request_root=Path('output/card_comparison_cid30236/barrier_request')
    request_trace=json.loads((request_root/'trace.json').read_text(encoding='utf-8'))
    request_checks=json.loads((request_root/'native_checks.json').read_text(encoding='utf-8'))
    assert request_trace['native_sha256']==request_checks['native_sha256']==trace['native_sha256']
    assert all(c['passed'] for c in request_checks['checks']) and all(s in records for s in request_trace['source_records'])
    ev=['barrier/README.md','barrier/trace.json','barrier/native_checks.json','barrier_request/README.md','barrier_request/trace.json','barrier_request/native_checks.json']
    conversion='固定防御量=trunc(接受者当前normalAtk×float32(skillparam1×请求系数))'
    limits='ability1080为AutoSkill；入场/每WAVE队列调用RequestSkillAtId。玩家请求系数读战斗规则extra_chain_rate，无规则时1；原生新建规则的未覆盖值也为1。1064条缓存关卡摘要均仅有rule=0，不能据此给出实际战斗系数或解释rule枚举。未发现自动.25、固定防御汇总或扣除除4。已核玩家构造名义基数.1，不代表完整玩家修正或最终减伤；截图5%的版本/来源仍未解释。'
    rule=dict(source='CACHE',table='bossskill',record_type='skillid0=16',effect_type=16,field_path='/skillparam1',meaning_zh='屏障固定防御量系数',unit='接受者normalAtk的倍数，另乘请求系数',conversion=conversion,base_definition='接受者当前normalAtk；已核玩家路径名义原始ATK缩放.1',status='已确认（局部系数；截图差异保留）',applicability='仅Boss43023614 /type16 SetShield分支；不泛化其他类型',evidence=ev,limits=limits,target='屏障接受者自身normalAtk',occurrences=1,unit_status='已确认（固定量）')
    view=dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='Boss skill',record_id=43023614,effect_type=16,field_path='/skillparam1',raw_value=r['raw']['skillparam1'],original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/skillparam1',meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=conversion,converted_value=None,display_value='固定量=trunc(当前normalAtk×2×战斗规则请求系数)；无规则时系数1，玩家路径名义原始ATK20%（截图5%）',raw_value_status='RAW_FOUND',correspondence_status='TYPE16_AUTOMATIC_REQUEST_SOURCE_AND_DEFAULT_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=rule['applicability'],evidence=ev,limits=limits)
    return [rule],[view]


def timed_overlay(records):
    proof=Path('output/card_comparison_cid30236/timed_support')
    trace=json.loads((proof/'trace.json').read_text(encoding='utf-8'))
    checks=json.loads((proof/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    rules,views=[],[]
    for r in trace['source_records']:
        assert r in records
        sid=r['raw']['skillid'];ability=r['raw']['ability'];enemy=ability==99;sympathy=ability==3000
        target='被攻击敌人' if enemy else '职业掩码1：job0（原文战士）' if ability==64 else '战场味方'
        for field in (('param1','param2','param6') if sympathy else ('param7','param9','param0') if enemy else ('param1','param3','param0')):
            value=r['raw'][field];attack=field in ('param1','param2','param7');duration=field in ('param0','param6')
            kind='持续时间' if duration else '攻击加算增量' if attack else '受伤量加算增量'
            converted=value if duration else value*100
            display=f'{value:g}游戏秒' if duration else f'敌方攻击降低{-converted:g}%（本项攻击因子1{value:+g}）' if enemy and attack else f'敌方受伤量+{converted:g}%（本项×{1+value:g}）' if enemy else f'攻击+{converted:g}%（同类支持加算）' if attack else f'本项减伤{-converted:g}个百分点（单独受伤量×{1+value:g}；同类支持加算）'
            conversion='正持续时间由游戏delta逐次扣减，单位游戏秒' if duration else 'Support2攻击因子=clamp(1+sum(_attack+_attackNormal/Skill))；本字段写_attack' if attack else 'Support2受伤量因子=clamp(1+sum(_defense))；负值减伤、正值增伤，非固定量'
            ev=['timed_support/README.md','timed_support/trace.json','timed_support/native_checks.json']
            if sympathy and attack:conversion='Support3复用同一聚合器；param1写_attackNormal、param2写_attackSkill，各为对1的加算增量'
            scope=f'仅已核本卡普通{sid} /ability{ability}，不推广其他效果；安装/触发资格满足时'
            limits='只确认本项配置及Support2局部加算；默认夹紧[.5,2]和其他同类效果会影响汇总，不计算最终HP。'
            rules.append(dict(source='CACHE',table='skilllist',record_type=f'ability={ability}',effect_type=ability,field_path='/'+field,meaning_zh=kind,unit='游戏秒' if duration else '对倍率1的加算增量；派生百分比/百分点',conversion=conversion,base_definition='所属Support2/3类别临时效果聚合的倍率1',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target=target,occurrences=1,unit_status='已确认（限定Support2路径）'))
            views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=sid,effect_type=ability,field_path='/'+field,raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=kind,unit=rules[-1]['unit'],target=target,conversion=conversion,converted_value=converted,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='ORDINARY_HANDLER_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    return rules,views


def ordinary_overlay(records):
    """Only fields exercised by the bounded twelve-record ordinary-rule probe."""
    proof=Path('output/card_comparison_cid30236/ordinary_rules')
    trace=json.loads((proof/'trace.json').read_text(encoding='utf-8'))
    checks=json.loads((proof/'native_checks.json').read_text(encoding='utf-8'))
    assert trace['native_sha256']==checks['native_sha256'] and all(c['passed'] for c in checks['checks'])
    byid={r['raw']['skillid']:r for r in records if r['table']=='skilllist'}
    rules,views=[],[]
    for ability in (1095,7,1008,1017):
        for field in ('param1','param3'):
            samples=[c for c in checks['checks'] if c.get('ability')==ability and c['field']==field and c['qualifier']]
            ev=['ordinary_rules/README.md','ordinary_rules/trace.json','ordinary_rules/native_checks.json']
            scope='只推广到本次逐字段检查的ID：'+','.join(str(c['skill_id']) for c in samples)+'；配置已安装且资格满足时'
            kind='攻击倍率' if field=='param1' else '受伤量倍率'
            conversion='攻击因子乘原值；相对本项基数的增加比例=(原值-1)×100%' if field=='param1' else '受伤量乘原值；本项减伤比例=(1-原值)×100%；不是固定防御量'
            target='自身' if ability in (1095,7) else '全体能力接受者；1017还受param0及iParam0职业掩码筛选'
            limits='资格/地形判定在片段中显式供给；1017实际执行param0/self和职业掩码门槛。未验证完整叠加、实际玩家装载或最终HP变化。'
            rules.append(dict(source='CACHE',table='skilllist',record_type=f'ability={ability}',effect_type=ability,field_path='/'+field,meaning_zh=kind,unit='无量纲倍率；派生百分比为本项局部贡献',conversion=conversion,base_definition='进入该项前的攻击因子或受伤量；不等同面板ATK/最终HP损失',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target=target,occurrences=len(samples),unit_status='已确认（本次限定普通能力分支）'))
            for c in samples:
                r=byid[c['skill_id']];assert r in trace['source_records'] and c['raw']==r['raw'][field]
                value=r['raw'][field];percent=(value-1)*100 if field=='param1' else (1-value)*100
                display=f'攻击+{percent:g}%（×{value:g}）' if field=='param1' else f'本项减伤{percent:g}%（受伤量×{value:g}）'
                views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=r['raw']['skillid'],effect_type=ability,field_path='/'+field,raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,meaning_zh=kind,unit=rules[-1]['unit'],target=target,conversion=conversion,converted_value=percent,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='ORDINARY_HANDLER_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    power=json.loads(Path('output/card_comparison_cid30236/skill_power/trace.json').read_text(encoding='utf-8'))
    power_checks=json.loads(Path('output/card_comparison_cid30236/skill_power/native_checks.json').read_text(encoding='utf-8'))
    assert power['native_sha256']==power_checks['native_sha256']==trace['native_sha256'] and all(c['passed'] for c in power_checks['checks'])
    ev=['skill_power/README.md','skill_power/trace.json','skill_power/native_checks.json']
    conversion='RequestSkill当前技能请求系数×param0；正值复制到Boss util.skillChainRate后进入技能基值。不是给Chain增加param0-1个百分点'
    scope='仅43023615（缓存）和106001（缓存该ID缺失时逐ID回退APK）；配置已安装且资格满足时'
    limits='玩家装载与完整叠加未知；APK的float32近似原值保持不变，可读15%为显示舍入。'
    rules.append(dict(source='CACHE / APK_AB（逐ID）',table='skilllist',record_type='ability=29',effect_type=29,field_path='/param0',meaning_zh='必杀请求系数乘数（ExtraChainRate）',unit='无量纲倍率；派生为本项威力增加比例',conversion=conversion,base_definition='传入RequestSkill的技能/Chain请求系数',status='已确认（静态及受控原生局部规则）',applicability=scope,evidence=ev,limits=limits,target='持有此普通能力的施法者技能请求',occurrences=2,unit_status='已确认（限定ability29路径）'))
    for r in power['source_records']:
        sid=r['raw']['skillid'];assert byid[sid]==r
        value=r['raw']['param0'];percent=(value-1)*100
        display=f'必杀威力+{percent:g}%（请求系数×{value:g}'+('；15%为float32显示舍入' if r['layer']=='APK_AB' else '')+'）'
        views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='ordinary skilllist',record_id=sid,effect_type=29,field_path='/param0',raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/param0',meaning_zh=rules[-1]['meaning_zh'],unit=rules[-1]['unit'],target=rules[-1]['target'],conversion=conversion,converted_value=percent,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='ORDINARY_HANDLER_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=scope,evidence=ev,limits=limits))
    timed_rules,timed_views=timed_overlay(records)
    return rules+timed_rules,views+timed_views


def build_effects(records):
    rows=[]
    def one(table,field,value):
        found=[r for r in records if r['table']==table and isinstance(r['raw'],dict) and r['raw'].get(field)==value]
        assert len(found)==1,(table,field,value,len(found))
        return found[0]
    def skill(sid):return one('skilllist','skillid',sid)
    def boss(sid):return one('bossskill','skillid',sid)
    def pattern(pid):return one('bosspattern','patternid',pid)
    def ref(r,field):
        present=field in r['raw']
        return dict(record_key=r['record_key'],table=r['table'],record_id=r['raw'].get('skillid',r['raw'].get('patternid',r['raw'].get('cid'))),namespace='Boss' if r['table'] in ('bossskill','bosspattern') else r['table'],ability_type=r['raw'].get('ability'),field_path='/'+field,present=present,raw_value=r['raw'].get(field),original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/'+field,location_scope=r.get('location_scope','原解码JSON字节定位'),layer=r['layer'])
    def add(key,group,effect,desc,fragment,bindings,target,condition='',duration='',answer=None,kind='未知',basis='',gap='',shot='',desc_field='text',desc_note=''):
        text=desc['raw'].get(desc_field)
        assert not fragment or isinstance(text,str) and fragment in text,(key,fragment)
        rows.append(dict(effect_id=key,cid=30236,group=group,effect_zh=effect,description_ja=text,description_fragment_ja=fragment,description_record_key=desc['record_key'],description_field='/'+desc_field,description_note=desc_note,field_refs=[ref(r,f) for r,fs in bindings for f in fs],readable_value=answer,quantity_kind=kind,target=target,condition=condition,duration=duration,answer_status='CONFIRMED_NUMERIC' if answer is not None else 'VALUE_UNEXPLAINED',raw_value_status='FOUND' if bindings else 'NOT_YET_LINKED',calculation_status='CONFIRMED_LOCAL_RULE' if answer is not None else 'NEEDS_LOCAL_MAPPING',evidence=basis,remaining_gap=gap,screenshot_value=shot,comparison_note='截图仅对照，原值不改写'))
        parent=desc['raw']
        rows[-1].update(card_name_ja=card['raw']['title']+' '+card['raw']['name'],description_table=desc['table'],description_record_id=parent.get('skillid',parent.get('patternid',parent.get('cid',parent.get('ability_id')))),skill_name_ja=parent.get('sname',parent.get('name')))
    card=one('charainfo','cid',30236)
    pnormal,psuper=pattern(43023601),pattern(43023602)
    for mode,pid,front,traps,support in [('普通',43023601,43023600,(43023602,43023603),43023604),('沙漠',43023600,43023605,(43023606,43023607),43023608),('超共鸣',43023602,43023609,(43023610,43023611),43023612)]:
        desc=psuper if mode=='超共鸣' else pnormal
        note='普通pattern原文包含砂漠分支；本砂漠pattern自身sinfo缺失' if mode=='沙漠' else ''
        r,b=boss(front),boss(support);v=r['raw']['skillparam1'];atk=b['raw']['skillparam1'];guard=b['raw']['skillparam2']
        cond=f'选中{mode}档pattern{pid}并执行该效果；当前玩家开放状态另论'
        add(f'sp_{pid}_front','必杀',mode+'·前方单次伤害',desc,'前方範囲内の全ての敵に5回ダメージを与え',[(r,['skillparam1'])],'前方范围敌人',cond,answer=f'每次{v:g}×技能基值B（Chain已在B中）',kind='技能基值倍率',basis='../boss_chain/type105/README.md',desc_field='sinfo',desc_note=note)
        t=boss(traps[0]);v=t['raw']['skillparam1']
        add(f'sp_{pid}_trap','必杀',mode+'·陷阱单次伤害',desc,'5回まで小ダメージを与え',[(boss(s),['skillparam1']) for s in traps],'陷阱范围目标',cond,answer=f'每次{v:g}×设置时技能基值B_set',kind='技能基值倍率',basis='../boss_chain/type112/README.md',desc_field='sinfo',desc_note=note)
        add(f'sp_{pid}_atk','必杀',mode+'·全体攻击提升',desc,'味方全体の攻撃力と防御力',[(b,['skillparam1','skillparam3'])],'味方全体（原文）',cond,'30游戏秒',f'+{atk*100:g}%（局部倍率1+{atk:g}×Chain）','攻击增加比例','../boss_chain/field_dictionary.json；../boss_heal/field_dictionary.json',desc_field='sinfo',desc_note=note)
        add(f'sp_{pid}_guard','必杀',mode+'·全体固定防御提升',desc,'味方全体の攻撃力と防御力',[(b,['skillparam2','skillparam3'])],'各接受者自身基数',cond,'30游戏秒',f'固定量=trunc(接受者当前normalAtk×{guard:g}×Chain)；已核玩家分支名义原始ATK{guard*10:g}%','固定防御量（系数已知）','../boss_chain/type13_basis/README.md',desc_field='sinfo',desc_note=note)
    a1,a2=skill(43023600),skill(43023605)
    add('a1_self_atk','能力一','自身攻击提升',a1,'攻撃力とクリティカル威力が上がる',[(skill(43023601),['param1'])],'自身',gap='ability1095.param1是否直接乘攻击分支；不可只凭1.375减1',shot='+37.5%')
    add('a1_barrier_guard','能力一','屏障防御量',a1,'10回まで防御力を上げ',[(boss(43023614),['skillparam1','skillparam2','skillparam5'])],'味方全体；每人防御基数待核','战斗/WAVE开始触发',gap='type16防御输入的基数与单位，原值2不能当2%或截图5%',shot='自身ATK5%')
    add('a1_skill_power','能力一','必杀威力提升',a1,'必殺技の威力が上がる',[(skill(43023615),['param0']),(skill(43023630),['str0'])],'自身','Extra附加入口，实例开放另论',gap='ability29.param0=1.05到技能/Chain分支的乘算位置',shot='+5%')
    for name in ('攻击力','防御力'):
        add('a1_enemy_'+('atk' if name=='攻击力' else 'def'),'能力一','敌方'+name+'降低',a1,'攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる',[(skill(43023616),['param0','param7','param8','param9'])],'被攻击敌人','攻击时','候选原值30；单位/作用字段待核',gap='ability99三个候选参数的属性映射、减益方向及时间；不预填-30%',shot='30%；截图时间45秒')
    for sid,mode,cond,shot in ((43023605,'常驻全体','战场味方',15),(43023606,'沙漠全体','沙漠',12.5),(43023607,'沙漠自身','自身且沙漠；资格细节另论',5)):
        r=skill(sid)
        for field,name in (('param1','攻击提升'),('param3','防御提升')):
            add(f'a2_{sid}_{field}','能力二',mode+'·'+name,a2,'戦場にいる味方の攻撃力と防御力と移動速度が上がる',[(r,[field,'param0'])],'自身' if sid==43023607 else '战场味方',cond,gap=f'ability{r["raw"]["ability"]}.{field}的乘算/减伤语义及对象资格',shot=f'{shot}%')
    for sid,mode,shot in ((43023608,'WAVE全体档',15),(43023609,'WAVE战士额外档',10)):
        r=skill(sid)
        for field,name in (('param1','攻击提升'),('param3','防御提升')):
            add(f'wave_{sid}_{field}','能力二',mode+'·'+name,a2,'WAVEが進むたび、味方全体の攻撃力と防御力',[(r,[field,'param0','iParam0'])],'味方全体' if sid==43023608 else '职业掩码1：job0（原文战士）','WAVE推进','120游戏秒',shot=f'{shot}%')
    job=next(r for r in records if r['table']=='job_ability' and 30236 in r['raw'].get('cids',[]))
    for sid,mode,shots in ((65000001,'Class自身',(1150,50)),(65000002,'Class全体',(50,15))):
        r=skill(sid)
        for (field,name),shot in zip((('param1','攻击提升'),('param3','防御提升')),shots):
            add(f'class_{sid}_{field}','Class',mode+'·'+name,job,'攻撃力と防御力と移動速度',[(r,[field])],'自身' if sid==65000001 else '战场味方','job_ability.cids明确包含30236',gap=f'ability{r["raw"]["ability"]}局部参数规则；当前Class开放不是配置值验收前提',shot=f'{shot}%')
    extra=one('extra_ability_info','cid',30236)
    add('extra_chain','Extra','同Chain下次必杀的Chain威力提升量',extra,'',[],'同Chain下一次使用必杀的味方','味方按必杀按钮发动；后备有效',answer='Lv1/2/3/4/MAX：32/34/36/38/40%（原文明确）',kind='原文Chain威力提升量数值',basis='extra_ability_info.extra_abilities[].text 原文',gap='参数计算结构/叠加可后续解释，数值文案已有答案')
    rows[-1].update(description_ja=[x['text'] for x in extra['raw']['extra_abilities']],description_field='/extra_abilities/*/text',calculation_status='ORIGINAL_TEXT_NUMBER_CONFIRMED',raw_value_status='FOUND',field_refs=[ref(extra,'extra_abilities')])
    leader=one('leader_ability','cid',30236)
    for key,effect,sid,value,cond,field in [('leader_atk','Leader全体攻击',75000012,60,'Leader原文条件','text'),('leader_desert','Leader沙漠攻击',75015002,10,'沙漠','text'),('leader_symp_atk','Leader共鸣全体攻击',75000102,3,'其他队员发动Leader时','sympathy_text'),('leader_symp_desert','Leader共鸣沙漠攻击',75015102,2,'其他队员发动Leader时且沙漠','sympathy_text')]:
        add(key,'Leader',effect,leader,'',[(skill(sid),['param1'])],'味方全体',cond,answer=f'+{value}%（游戏原文明确）',kind='原文攻击增加比例',basis='leader_ability.'+field,desc_field=field)
        rows[-1]['calculation_status']='ORIGINAL_TEXT_NUMBER_CONFIRMED'
    symp=skill(43023610)
    add('symp_atk','共鸣','常规共鸣攻击提升',symp,'戦場にいる<味方>の攻撃力とクリティカル威力',[(skill(43023611),['param1','param2','param6','param8'])],'战场味方','含自身味方发动共鸣必杀；后备有效（原文）','候选45；单位待核',gap='ability3000攻击分支与加算基准、持续时间',shot='攻击10%加算，45秒')
    bond=one('supporterskill','ability_id',30236)
    for sid,name,shot in ((102070,'羁绊沙漠全体攻击',5),(102071,'羁绊沙漠自身攻击',25)):
        add('bond_'+str(sid),'羁绊',name,bond,'地形が砂漠の時、味方全体の攻撃力が上がる',[(skill(sid),['param0','param1'])],'自身' if sid==102071 else '味方全体','父文案砂漠；102071自身text写森林，原文矛盾保留',gap='ability7/1008攻击乘算与地形枚举；不因文本矛盾停其他项',shot=f'+{shot}%')
    add('bond_skill_power','羁绊','羁绊必杀威力提升',bond,'必殺技の威力が上がる',[(skill(106001),['param0'])],'装备此羁绊的角色','缓存缺ID时按既有逐ID回退APK',shot='+15%')
    add_remaining_effects(add,one,skill,boss,pattern,records,rows)
    _,ordinary=ordinary_overlay(records)
    confirmed={(v['record_id'],v['field_path']):v for v in ordinary}
    for row in rows:
        if row.get('effect_scope')=='other_numeric':continue
        matches=[confirmed[(f['record_id'],f['field_path'])] for f in row['field_refs'] if f['table']=='skilllist' and (f['record_id'],f['field_path']) in confirmed]
        if row['effect_id'].startswith('wave_'):matches=[v for v in matches if row['effect_id'].endswith(v['field_path'][1:])]
        if row['effect_id'] in ('a1_enemy_atk','a1_enemy_def'):matches=[v for v in matches if v['field_path']==('/param7' if row['effect_id']=='a1_enemy_atk' else '/param9')]
        if row['effect_id']=='symp_atk':matches=[v for v in matches if v['field_path']=='/param1']
        if len(matches)!=1:continue
        v=matches[0]
        row.update(readable_value=v['display_value'],quantity_kind=v['meaning_zh'],answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap='本项配置值已确认；当前装载、全局叠加和最终HP另论',comparison_note='本项配置百分比与截图一致；原值不改写')
        if row['effect_id']=='bond_102071':row['remaining_gap']+='；父文案/名称为砂漠，自身text为森林，源内矛盾保留'
        if row['effect_id'].startswith('wave_'):row['target']=v['target'];row['remaining_gap']='本项数值及120游戏秒已确认；两项在Support2同类加算，整体战斗叠加另论'
        if row['effect_id'] in ('a1_enemy_atk','a1_enemy_def'):
            row.update(duration='30游戏秒（截图45秒）',comparison_note='减益幅度对应；游戏30秒与截图45秒存在差异，两者保留')
        if row['effect_id']=='symp_atk':row.update(readable_value='通常攻击/必杀攻击各+10%（Support3同类加算）',duration='45游戏秒',remaining_gap='本项两类攻击及时间已确认；完整共鸣触发资格和全局叠加另论')
    _,barrier=barrier_overlay(records);v=barrier[0]
    barrier_row=next(r for r in rows if r['effect_id']=='a1_barrier_guard')
    barrier_row.update(readable_value=v['display_value'],quantity_kind=v['meaning_zh'],answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),target='各屏障接受者自身当前normalAtk',remaining_gap=v['limits'],comparison_note='自动请求来源及默认1已确认；默认上下文名义20%仍与截图5%不同。实际关卡规则/截图版本未知，不把.25敏感性夹具当结论')
    barrier_row['field_refs'] += [ref(skill(43023603),f) for f in ('ability','param0','param1','param5','str0')]+[ref(pattern(43023603),'skillid1')]
    _,critical=critical_overlay(records)
    critical_values={(v['record_id'],v['field_path']):v for v in critical}
    effect_bindings=[('other_a1_critical_damage',43023601,'param6'),('other_class_param6',65000001,'param6'),('other_class_param5',65000001,'param5'),('other_symp_critical_damage',43023611,'param8')]
    effect_bindings.extend((f'other_sp_{pid}_{field}',sid,field) for pid,sid in ((43023601,43023612),(43023600,43023613),(43023602,43023614)) for field in ('param4','param5'))
    effect_bindings.extend((f'other_a2_{sid}_{field}',sid,field) for sid,fields in ((43023606,('param4','param5')),(43023607,('param5','param6'))) for field in fields)
    effect_bindings.extend((f'other_wave_{sid}_{field}',sid,field) for sid,fields in ((43023608,('param4','param6')),(43023609,('param4','param8'))) for field in fields)
    for key,record,field in effect_bindings:
        row=next(r for r in rows if r['effect_id']==key);v=critical_values[(record,'/'+field)]
        row.update(readable_value=v['display_value'],quantity_kind=v['meaning_zh'],answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap='本项配置贡献已确认；完整来源叠加与实际暴击另论',comparison_note='与截图数值可对应；这里按暴击系数增量/百分点解释')
        if record==65000001 and field=='param5':row.update(comparison_note='当前解包/代码为+40个百分点；截图20%，存在差异，原值不改写',remaining_gap='局部直接加算.4已确认；截图20%的版本/来源差异尚未解释')
        if v['effect_type']==2012:row['duration']='30游戏秒（2012.param0进入同一支持定时路径）'
    _,movement=movement_overlay(records);movement_values={(v['record_id'],v['field_path']):v for v in movement}
    speed_bindings=[('other_class_param2',65000001,'param2'),('other_class_party_move',65000002,'param2'),('other_a1_enemy_move',43023616,'param8'),('other_a2_attack_interval',43023607,'param7')]
    speed_bindings.extend((f'other_a2_{sid}_move',sid,'param2') for sid in (43023605,43023606,43023607))
    speed_bindings.extend((f'other_wave_{sid}_param2',sid,'param2') for sid in (43023608,43023609))
    for key,record,field in speed_bindings:
        row=next(r for r in rows if r['effect_id']==key);v=movement_values[(record,'/'+field)]
        row.update(readable_value=v['display_value'],quantity_kind=v['meaning_zh'],answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap='本项配置贡献已确认；所有速度/时序来源汇总另论',comparison_note='本项配置数值已有依据；截图列值与原值分别保留')
        if key=='other_a1_enemy_move':row['comparison_note']='移动降低30%对应；持续30游戏秒与截图45秒的差异保留'
        if key=='other_a2_attack_interval':row['comparison_note']='1.125游戏秒为中性上下文名义值，显示约1.1；不是从1.5秒减掉1.1秒'
    _,lifesteal=lifesteal_overlay(records)
    for key,v in zip(('other_class_heal_ratio','other_class_overheal'),lifesteal):
        row=next(r for r in rows if r['effect_id']==key)
        row.update(readable_value=v['display_value'],quantity_kind=v['meaning_zh'],answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap=v['limits'],comparison_note='最大HP1.4倍档位与截图超出40%对应')
        if key=='other_class_heal_ratio':row.update(comparison_note='当前配置/代码为25%，截图20%；差异保留，原值不改写',remaining_gap=v['limits']+'；截图20%的版本/来源差异尚未解释')
    _,field_time=field_time_overlay(records);v=field_time[0]
    for key in ('other_a1_desert_duration','other_symp_desert_duration'):
        next(r for r in rows if r['effect_id']==key).update(readable_value=v['display_value'],quantity_kind=v['meaning_zh'],duration='300游戏秒',answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap=v['limits'],comparison_note='300秒配置与截图对应；完整触发及提前结束条件另论')
    _,mana_chance=mana_chance_overlay(records);v=mana_chance[0]
    next(r for r in rows if r['effect_id']=='other_a1_mana_chance').update(readable_value='基础概率20%（通常/技能/暴击三类输入均为.2）',quantity_kind='击杀玛那基础概率',answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap=v['limits'],comparison_note='截图仅写一定几率；20%为本次代码补出的基础配置概率，实际生成事件与完整击杀资格另论')
    next(r for r in rows if r['effect_id']=='other_a1_desert_mana_chance').update(readable_value='原文沙漠必得；当前地形标志16时，基础.2+附加.8=1（100%阈值）',quantity_kind='原文条件与已核地形阈值',calculation_status='CONFIRMED_LOCAL_RULE_TERRAIN_ENUM_SCOPE_LIMIT',evidence='；'.join(v['evidence']),remaining_gap=v['limits'],comparison_note='100%阈值与必得文案相符；地形枚举的完整转换仍另论')
    _,chain_mana=chain_mana_overlay(records);v=chain_mana[1]
    next(r for r in rows if r['effect_id']=='other_a2_chain_probability').update(readable_value='每次有效按钮事件阈值10%（单一未锁存work；链列表数量2/3/4/≥5对应param1/2/3/4）；数量0/1不判定',quantity_kind=v['meaning_zh'],answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap=v['limits'],comparison_note='当前每次阈值10%，截图20%；未见固定双判定，失败可在后续事件重试；不当作整Chain累计概率')
    next(r for r in rows if r['effect_id']=='other_a2_chain_count').update(readable_value=chain_mana[0]['display_value'],quantity_kind=chain_mana[0]['meaning_zh'],calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap='param0=1的数量输入已确认；实际生成和当前装载另论')
    next(r for r in rows if r['effect_id']=='other_a2_chain_limit').update(calculation_status='CONFIRMED_LOCAL_CHAIN_LATCH',evidence='；'.join(v['evidence']),remaining_gap='成功后_isGottenMana置1并跳过后续判定；内部计数≤1时复位。完整Chain生命周期另论')
    _,leader_condition=leader_condition_overlay(records);v=leader_condition[0]
    next(r for r in rows if r['effect_id']=='other_leader_threshold').update(readable_value=v['display_value']+'；职业=战士（JOB_TYPE=0）',quantity_kind='Leader职业人数资格',answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',evidence='；'.join(v['evidence']),remaining_gap=v['limits'],comparison_note='至少4名战士的配置资格与截图对应；不证明当前玩家编成已满足')
    _,super_counter=super_counter_overlay(records);v=super_counter[0]
    code=json.loads(Path('output/card_comparison_cid30236/super_counter/trace.json').read_text(encoding='utf-8'))['code_constants'][0]
    next(r for r in rows if r['effect_id']=='other_sp_super_counter').update(readable_value=v['display_value'],quantity_kind=v['meaning_zh'],raw_value_status=v['raw_value_status'],answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',code_refs=[code],evidence='；'.join(v['evidence']),remaining_gap=v['limits'],comparison_note='原生常量10与截图10次对应；不是角色主表字段值')
    _,wedge_time=wedge_time_overlay(records);v=wedge_time[0]
    code=json.loads(Path('output/card_comparison_cid30236/wedge_time/trace.json').read_text(encoding='utf-8'))['code_constants'][0]
    next(r for r in rows if r['effect_id']=='other_a1_wedge_stop').update(readable_value=v['display_value'],quantity_kind=v['meaning_zh'],raw_value_status=v['raw_value_status'],answer_status='CONFIRMED_NUMERIC',calculation_status='CONFIRMED_LOCAL_RULE',condition='释放普通时楔；clockUpFlag=0；合格目标',duration='本项输入5游戏秒；已有时停可累加',code_refs=[code],evidence='；'.join(v['evidence']),remaining_gap=v['limits'],comparison_note='普通模式5秒与截图对应；ClockUp模式另为8秒，当前队伍模式未知')
    next(r for r in rows if r['effect_id']=='other_sp_normal_cost')['calculation_status']='RAW_CONFIGURATION_VALUE_CONFIRMED'
    next(r for r in rows if r['effect_id']=='other_a1_barrier_count')['calculation_status']='ORIGINAL_TEXT_AND_FIELD_NUMBER_CONFIRMED'
    differences=json.loads(Path('output/card_comparison_cid30236/difference_sources/trace.json').read_text(encoding='utf-8'))
    case_by_effect={key:case for case in differences['cases'] for key in case['effect_ids']}
    for row in rows:
        row.setdefault('effect_scope','attack_defence')
        row.setdefault('code_refs',[])
        row['unit']=EFFECT_UNITS[row['quantity_kind']]
        row['correspondence_status']='CONFIRMED_DESCRIPTION_TO_VALUE' if row['readable_value'] is not None else 'RECORD_LINK_CONFIRMED_VALUE_MAPPING_PENDING' if row['field_refs'] else 'NOT_YET_LINKED'
        row['screenshot_difference']=None
        if row['effect_id'] in case_by_effect:
            case=case_by_effect[row['effect_id']]
            row['screenshot_difference']={k:case[k] for k in ('case_id','source_comparison_status','discrepancy_status','fields','older_record','finding')}
            row['evidence']+='；difference_sources/README.md；difference_sources/trace.json'
            row['remaining_gap']+='；较早技能快照同值，不能直接归因于两快照之间的更新；截图来源/具体上下文仍待核'
        elif row['effect_id']=='a1_barrier_guard':
            row['screenshot_difference']=dict(case_id='barrier_guard',source_comparison_status='AUTOMATIC_REQUEST_SOURCE_AND_DEFAULT_CONFIRMED',discrepancy_status='OPEN_SCREENSHOT_SOURCE_OR_CONTEXT',finding='请求来源及默认1已确认，默认上下文名义20%与截图5%不同；实际关卡规则和截图版本未知')
        if row['screenshot_difference']:
            tokens={'barrier_guard':'5%','class_critical':'20%','class_lifesteal':'20%','chain_mana':'20%','enemy_duration':'45秒'}
            token=tokens[row['screenshot_difference']['case_id']]
            assert token not in unicodedata.normalize('NFKC',row['description_ja'])
            row['screenshot_difference']['number_origin']='EXTERNAL_REFERENCE_NUMBER_NOT_LITERAL_GAME_DESCRIPTION'
            row['screenshot_difference']['game_description_check']=dict(record_key=row['description_record_key'],field_path=row['description_field'],screenshot_numeric_token=token,literal_present=False)
            external=differences['external_observations']['content']
            row['screenshot_difference']['external_reference_checks']=[dict(source_id=s['source_id'],url=s['url'],page_updated=s['displayed_updated_date'],status='NO_RELEVANT_NUMERIC_ANNOTATION',finding_zh=f['finding_zh'])
                for s in external['sources'] for f in s['findings'] if f['case_id']==row['screenshot_difference']['case_id']]
            row['evidence']+='；difference_sources/reference_observations.json（外部说明未给争议数字，不能裁决）'
    for row in rows:
        stage_all_ids={f['record_id'] for f in row['field_refs'] if f.get('ability_type')==1008}
        if stage_all_ids:
            for sid in sorted(stage_all_ids):
                field_ref=ref(skill(sid),'param0')
                if field_ref not in row['field_refs']:row['field_refs'].append(field_ref)
            row['condition']+='；1008由玩家候选列表的存活活动提供者贡献给当前接受者，可含自身、无本类型职业/距离筛选；param0按两位十进制拆分匹配当前背景flag，非活动提供者的独立后备路径另论'
            row['evidence']+='；../ordinary_effects/ability1008/README.md；../ordinary_effects/ability1008/trace.json'
        stage_ids={f['record_id'] for f in row['field_refs'] if f.get('ability_type')==7}
        if stage_ids:
            for sid in sorted(stage_ids):
                field_ref=ref(skill(sid),'param0')
                if field_ref not in row['field_refs']:row['field_refs'].append(field_ref)
            row['condition']+='；7的param0按两位十进制分组，转位后与当前背景flag匹配，条件通过才乘本项；非队伍全体规则'
            row['evidence']+='；../ordinary_effects/ability7/README.md；../ordinary_effects/ability7/trace.json'
            if 102071 in stage_ids:
                row['condition']+='；102071的代码param0=4为沙漠（背景flag16），自身text写森林的源内矛盾保留'
        drain_ids={f['record_id'] for f in row['field_refs'] if f.get('ability_type')==99 and f['field_path'] in ('/param0','/param7','/param8','/param9')}
        if drain_ids:
            for sid in sorted(drain_ids):
                for field in ('param0','param1','param2','param3'):
                    if field in skill(sid)['raw']:
                        field_ref=ref(skill(sid),field)
                        if field_ref not in row['field_refs']:row['field_refs'].append(field_ref)
            row['condition']+='；99在Attack的Attacked返回≥1且能力筛选通过后施加；Normal/Skill/Critical分别看param1/3/2，本记录均1；弱化作用于本次受击目标的Support2'
            row['evidence']+='；../ordinary_effects/ability99/README.md；../ordinary_effects/ability99/trace.json'
        sympathy_ids={f['record_id'] for f in row['field_refs'] if f.get('ability_type')==3000 and f['field_path'] in ('/param1','/param2','/param6','/param8')}
        if sympathy_ids:
            for sid in sorted(sympathy_ids):
                for field in ('param0','iParam0','param9'):
                    if field in skill(sid)['raw']:
                        field_ref=ref(skill(sid),field)
                        if field_ref not in row['field_refs']:row['field_refs'].append(field_ref)
            row['condition']+='；3000共鸣技能开始事件及资格通过后施加Support3；iParam0/param9筛选发动者，param0控制接受者；本批武器flag交集全0绕过限制，实际名单另论'
            row['evidence']+='；../ordinary_effects/ability3000/README.md；../ordinary_effects/ability3000/trace.json'
        support_ids={f['record_id'] for f in row['field_refs'] if f.get('ability_type')==2012 and f['field_path'] in ('/param4','/param5')}
        if support_ids:
            for sid in sorted(support_ids):
                for field in ('param0','param7','param8'):
                    field_ref=ref(skill(sid),field)
                    if field_ref not in row['field_refs']:row['field_refs'].append(field_ref)
            row['condition']+='；2012在技能动作OnAction未处理的首轮选中目标时施加；param8为TARGET_TYPE，非1017职业位图'
            row['evidence']+='；../ordinary_effects/ability2012/README.md；../ordinary_effects/ability2012/trace.json'
        ids={f['record_id'] for f in row['field_refs'] if f.get('ability_type')==1017 and f['field_path'] in ('/param1','/param3')}
        if ids:
            for sid in sorted(ids):
                for field in ('param0','iParam0'):
                    field_ref=ref(skill(sid),field)
                    if field_ref not in row['field_refs']:row['field_refs'].append(field_ref)
            row['condition']+='；1017的param0=1允许提供者自身，iParam0=31仅匹配接受者职业0..4，完整候选名单/活动资格另论'
            row['evidence']+='；../ordinary_effects/ability1017/README.md；../ordinary_effects/ability1017/trace.json'
    assert len({r['effect_id'] for r in rows})==len(rows)
    return rows


def render_effects(rows):
    esc=html.escape
    answered=sum(r['readable_value'] is not None for r in rows)
    primary=[r for r in rows if r['effect_scope']=='attack_defence']
    other=[r for r in rows if r['effect_scope']=='other_numeric']
    out=f'<section id="attack-defense"><h2>整卡技能描述数值对照</h2><p>本表按描述效果拆行：共{len(rows)}项，{answered}项已有数值/公式答案，{len(rows)-answered}项仍缺局部解释。首批攻防{sum(r["readable_value"] is not None for r in primary)}/{len(primary)}；其余数值{sum(r["readable_value"] is not None for r in other)}/{len(other)}。原文数值、代码计算与截图差异分开标注；已确认配置不以玩家解锁或完整战斗汇总作为单项交付前提。</p><p><a href="description_effects.csv">下载逐效果CSV</a> · <a href="description_effects.json">逐效果JSON及来源</a></p>'
    focus=[r for r in rows if r['effect_id'] in ('a1_barrier_guard','other_class_param5','other_class_heal_ratio','other_a2_chain_probability','a1_enemy_atk')]
    out+='<div class="notice" style="margin:16px 0"><b>5组数值取值已裁决：采用解包与代码</b><p>按用户2026-10-16指示，冲突以解包原值和已确认代码规则为准；5组取值均已裁决。截图不同值并列保留，其注数成因仍未知；不再等待原网站恢复。屏障采用动态固定量公式，20%仅为请求系数1及已核玩家构造路径的名义换算。此裁决不补充完整战斗、实际装载或最终HP结论。</p><ul>'
    for r in focus:
        out+='<li><a href="#'+esc(r['effect_id'])+'">'+esc(r['group']+' · '+r['effect_zh'])+'</a>：'+esc(r['screenshot_difference']['adopted_display'])+'；截图 '+esc(r['screenshot_value'])+'</li>'
    out+='</ul><p><a href="difference_sources/adoption_policy.json">用户取值政策与五组裁决配置</a> · <a href="barrier_request/README.md">屏障请求证据</a> · <a href="difference_sources/README.md">四项旧新快照核对</a> · <a href="difference_sources/reference_observations.json">外部来源核对（未给争议数字）</a></p></div>'
    out+='<div style="overflow-x:auto"><table style="min-width:1050px"><thead><tr><th>技能组</th><th>单项效果</th><th>数值答案 / 性质</th><th>对象 / 条件</th><th>持续</th><th>确认与缺口</th><th>原文与来源</th></tr></thead><tbody>'
    for r in rows:
        answer=r['readable_value'] if r['readable_value'] is not None else '待解释；候选原值见下方来源'
        desc=r['description_ja'];desc='\n'.join(desc) if isinstance(desc,list) else desc or '描述文本尚未定位'
        identity_html='<p>'+esc(r['card_name_ja'])+' / '+esc(r['description_table'])+' / '+esc(str(r['description_record_id']) if r['description_record_id'] is not None else r['description_record_key'])+'</p>'
        if r['skill_name_ja']:identity_html+='<p>'+esc(r['skill_name_ja'])+'</p>'
        code_html='<p>代码常量（独立于原始表字段）</p><pre>'+esc(json.dumps(r['code_refs'],ensure_ascii=False,indent=2))+'</pre>' if r['code_refs'] else ''
        difference_html='<p>截图差异、采用结果及旧来源（独立于当前游戏输入）</p><pre>'+esc(json.dumps(r['screenshot_difference'],ensure_ascii=False,indent=2))+'</pre>' if r['screenshot_difference'] else ''
        out+='<tr id="'+esc(r['effect_id'])+'" data-effect-answer="'+('yes' if r['readable_value'] is not None else 'no')+'" data-effect-id="'+esc(r['effect_id'])+'"><td>'+esc(r['group'])+'</td><td>'+esc(r['effect_zh'])+'</td><td><b>'+esc(answer)+'</b><p>'+esc(r['quantity_kind'])+'</p><p>单位：'+esc(r['unit'])+'</p><p>截图：'+esc(r['screenshot_value'] or '见左侧原图')+'；'+esc(r['comparison_note'])+'</p></td><td>'+esc(r['target'])+'<p>'+esc(r['condition'])+'</p></td><td>'+esc(r['duration'] or '本项未另确认独立时长')+'</td><td>'+esc(r['answer_status'])+'<p>原值：'+esc(r['raw_value_status'])+'</p><p>对应：'+esc(r['correspondence_status'])+'</p><p>计算：'+esc(r['calculation_status'])+'</p><p>'+esc(r['remaining_gap'])+'</p></td><td><details><summary>原文 / 原值 / 定位</summary>'+identity_html+'<pre>'+esc(desc)+'</pre><pre>'+esc(json.dumps(r['field_refs'],ensure_ascii=False,indent=2))+'</pre>'+code_html+difference_html+'<p>依据：'+esc(r['evidence'])+'</p></details></td></tr>'
    return out+'</tbody></table></div></section>'
