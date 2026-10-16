"""Read-only, curated screenshot comparison. Run from project root; stdlib only."""
import base64, csv, hashlib, html, json
from collections import Counter
from pathlib import Path
from chica_remaining_effects import critical_overlay, movement_overlay, lifesteal_overlay, field_time_overlay, mana_chance_overlay, chain_mana_overlay, leader_condition_overlay, super_counter_overlay, wedge_time_overlay
from chica_description_effects import build_effects, render_effects, ordinary_overlay, fallback_records, barrier_overlay, difference_source_overlay

from chica_source_priority import apply_source_priority, POLICY_PATH
from ordinary_effect_dictionary import extend_1095, extend_1017, extend_2012, extend_3000, extend_99, extend_7, extend_1008, render_reusable_effects

OUT = Path('output/card_comparison_cid30236')
SOURCE = Path('output/cache_full_20261015_v3/records.jsonl')
TYPE105 = Path('output/boss_chain/type105')
TYPE112 = Path('output/boss_chain/type112')
GUARD_BASIS = Path('output/boss_chain/type13_basis')
OUT.mkdir(parents=True, exist_ok=True)
records = [json.loads(s) for s in SOURCE.open(encoding='utf-8')]
assert not any(r['table']=='skilllist' and r['raw'].get('skillid')==106001 for r in records)
records.extend(fallback_records())
rows = []
evidence = {}
labels = {'yes':'已对应 · 文本或局部规则', 'resolved':'截图数值已裁决 · 采用解包/代码', 'raw':'原值已找到 · 尚未闭合', 'gap':'尚未建立对应', 'diff':'其他差异 · 待核对', 'out':'网站添加 · 排除'}
def select(table, field, value):
    return [r for r in records if r['table']==table and isinstance(r['raw'],dict) and (value in r['raw'].get(field,[]) if isinstance(r['raw'].get(field),list) else r['raw'].get(field)==value)]
def one(table, field, value):
    found=select(table,field,value)
    assert len(found)==1,(table,field,value,len(found))
    r=found[0];evidence[r['record_key']]=r
    return r
card=one('charainfo','cid',30236)
def c(): return [card]
def sk(*ids): return [one('skilllist','skillid',x) for x in ids]
def bs(*ids): return [one('bossskill','skillid',x) for x in ids]
def bp(*ids): return [one('bosspattern','patternid',x) for x in ids]
def aux(table,field='cid',value=30236):return [one(table,field,value)]
def add(group,title,status,shot,raw,note,refs):
    for r in refs:evidence[r['record_key']]=r
    rows.append(dict(number=len(rows)+1,group=group,title=title,status=status,status_zh=labels[status],screenshot=shot,extracted=raw,conclusion=note,record_keys=[r['record_key'] for r in refs],raw_value_status=None,correspondence_status=None,calculation_status=None,field_comparisons=[]))

add('基本资料','日文名、稀有度与 COST','yes','《Y.G.1009》竜の眷属 チーカ；五星 SSR；28','title/name 原文相同；rarity=5；cost=28','身份与原始星级数字可对应；SSR 为截图显示标签。',c())
add('基本资料','画师、声优、介绍','yes','NPA；今井麻美；页面底部日文人物介绍','illustrator=NPA；voice_artist=今井麻美；profile 已完整保存','可展开原始记录查看完整日文介绍。',c())
add('基本资料','所属与战斗所属','yes','湖都；限战时追加未来所属','home=8 → homelist 湖都；battle_home=32 → 未来','所属名称可明确关联；限战触发逻辑未在本卡重新验证。',c()+aux('homelist','home_id',8)+aux('homelist','home_id',32))
add('基本资料','职业、成长类型','raw','战士；普通(?)','本记录没有 jobtype；growth=1；Class 关联表已找到','未把缺失职业字段补成默认值；职业及成长枚举、成长公式仍需核对。',c())
add('基本资料','暴击率、攻击速度','raw','40%；1.5 秒/下','critical=0.4；atkspeed=1.5','数值可对照，尚未核实这两个字段到最终面板的完整计算与时间单位路径。',c())
add('基本资料','攻击类型与初始武器','diff','突 [C] 突刺剑','weaponid=86856 → 波導戟・槍；type=2；rank=2','武器关联确定，但名称与截图不同；type/rank 的显示枚举尚未确认，不能直接认定截图或当前记录错误。',c()+aux('weaponlist','id',86856))
add('排除项','获得来源、登场日期','out','「竜の眷属」登場フェス；2026/10/02','用户于2026-10-16补充：这两项为网站自行添加','按用户补充排除，不计入游戏数据提取缺口；未据此证明所有游戏资源中都不存在相关信息。',c())
add('基本资料','卡面与头像','gap','截图中有卡面与头像','资源包已采集；本次未建立 cid30236 到图片资产的独立绑定','左栏只是用户提供的截图，不冒充从游戏资源包导出的卡图。',c())
add('等级属性','LV60—80 ATK / HP','gap','60:25000/24900；65:25500/25400；70:26000/25900；75:26500/26400；80:27000/26900','iniap=18200；inihp=18100；maxlv=60；limit_break=4；growth=1；Aparam=33554440','成长相关原值已取得，但尚未闭合等级/突破到属性的公式；不能据截图倒推后冒充解包。',c())
add('必杀技','名称、原文与两种必杀','yes','ドラゴニックドライブ／ドラゴニックスマッシュ','card.pattern0/1/2 → 43023600/01/02；pattern.sname / sinfo 保存日文原文','通过卡牌显式 pattern 引用定位，不按文案顺序猜关联。超共鸣原文明确写 0 玛那、获得 1 万象玛那。',c()+bp(43023600,43023601,43023602))
add('必杀技','耗珠、沙漠切换与共鸣次数','raw','普通 2；沙漠少 1；累积 10 次后超共鸣 0','pattern43023601.scost=2；43023600.scost=1,bgf=16；43023602.scost 缺失','2/1 数字与描述对应；bgf条件选择另论；10次共用计数门槛已由原生常量及边界确认。缺失 scost 不擅自填 0；0 来自原文。',bp(43023600,43023601,43023602))
add('必杀技','前方 5 连击倍率','yes','普通每击3.5倍；沙漠3.75倍；超共鸣4.25倍；5连击','Boss type105：43023601→43023600(3.5)，43023600→43023605(3.75)，43023602→43023609(4.25)；三条skillparam6均为5','已确认局部规则：单次攻击输入=floor/clamp(float32(技能基值B×skillparam1))，B=getBasicSkillAttack(true)，Chain已在B内参与一次。5是每目标尝试上限，在范围判断前计数；持续在范围内的受控样例产生5次Attack调用。系数与截图一致；不是直接面板ATK倍率，也未验证最终扣血。',bs(43023600,43023605,43023609)+bp(43023600,43023601,43023602))
type105_row = rows[-1]
add('必杀技','陷阱、次数与倍率','raw','9 个二重陷阱；最多 5 次；0.75/0.875/1.125 倍','Boss type112：普通02/03=.75，沙漠06/07=.875，超共鸣10/11=1.125（均430236前缀）；param0=1、4=.25、5=5、7=.001、8=88725、9=1','设置时单次基值含Chain。每陷阱共用5次爆发，有敌门控、.25游戏秒间隔，单次update最多一次。88725选6×3交错九格；两段均执行且保留旧对象时，9格各2层，与截图数量/系数对应。.001推力传到Attack并在允许条件下请求DamageL强受击状态；与原文転倒动作对应仍标推断，最终扣血未知。',bs(43023602,43023603,43023606,43023607,43023610,43023611)+bp(43023600,43023601,43023602))
type112_row = rows[-1]
add('必杀技','全体攻击提升与持续时间','yes','攻击 +60% / +65% / +75%；30 秒','type13：43023604/08/12，skillparam1=.6/.65/.75；skillparam3=30','已有静态/受控证据支持：攻击输入先乘 skillChainRate，再形成 1+输入；30 为游戏秒。这是局部支持效果规则，不是最终全战斗倍率。',bs(43023604,43023608,43023612))
add('必杀技','防御提升的单位','yes','自身 ATK ×3% /3.25% /3.75%','同三条type13的skillparam2=.3/.325/.375；已核玩家构建片段含CardInfo.ATK×.1缩放','名义系数对应已确认：.3/.325/.375乘玩家构建的.1缩放，即原始卡牌ATK的3/3.25/3.75%。实际固定量=接受者当前_normalAtk×(param2×Chain)再向零截断；构建缩放先截断，后续初始化/常驻能力还可改_normalAtk。属于有条件基数换算，实际叠加/扣血另行处理，原值不改。',bs(43023604,43023608,43023612))
guard_row=rows[-1]
add('必杀技','移动、暴击率与暴击威力','raw','移速增加；暴击率增加；暴击威力 +30/32.5/37.5%','type13.skillparam6=.3/.325/.375；s_ability=43023612/13/14 → 普通 skilllist ability2012，param4/5=.3/.325/.375，param0=30','移动局部规则已有证据；附加能力原值存在，暴击两项及其施加对象未完整验证。Boss 与普通 skilllist 同号是不同记录。',bs(43023604,43023608,43023612)+sk(43023612,43023613,43023614))
add('能力一','能力名称、说明与子效果','yes','并行未来の系譜《竜の眷属》','card.skillid 含 43023600；其 sub=[43023601,43023602,43023603,43023604]','完整日文能力说明已取得；这里只认主表定义与一层引用，不代表玩家已解锁。',c()+sk(43023600))
add('能力一','时之楔、击杀玛那','raw','初始 1 楔；解放敌人 5 秒不能行动；击杀概率获得，沙漠必得','根 ability1110,param0=1；子43023602 ability28 多项 .2/.8、param6=4；说明包含时之楔与沙漠必得','初始数量有原文对应；击杀玛那基础20%阈值已确认，地形标志16时另加80个百分点。普通时楔模式已确认5游戏秒输入，ClockUp模式另为8秒；完整队伍模式、地形资格/触发入口另论。',sk(43023600,43023602))
add('能力一','攻击与暴击威力','yes','攻击 +37.5%；暴击威力 +87.5%','43023601 ability1095：param1=1.375；param6=2.375','攻击+37.5%已确认；1095.param6在代码中先减1.5，故暴击伤害系数贡献+.875（87.5个百分点）。两项见上方逐效果表，完整叠加另论。',sk(43023601))
add('能力一','地形变化与屏障','raw','战斗/WAVE开始：沙漠300秒；10层，防御自身ATK5%，防异常/无视防御/火冰','43023603 ability1080,str0=43023603；同号 Boss pattern 指向43023613/14；type66 参数含300；type16 含10与标志194806','Boss66地形计时300游戏秒已确认。1080为AutoSkill，自动请求读取战斗规则extra_chain_rate，无规则时1；默认上下文屏障名义原始ATK20%，截图5%。未发现自动.25或汇总除4，具体关卡规则/截图版本仍未知；取值已按用户政策采用动态固定量公式，详见逐项表。',sk(43023603)+bp(43023603)+bs(43023613,43023614))
add('能力一','必杀增伤、攻击减益与范围暴击','diff','必杀 +5%；攻击减益30%，45秒；暴击6连范围','43023615 ability29,param0=1.05；43023616 ability99,param0=30,param7/8=-.3,param9=.3；卡牌 CRInumber=6；43023604 ability1079,param8=6','Extra 表经43023630/31/32关联这些附加技能。必杀+5%已确认；减益攻击降低30%、受伤量增加30%，持续30游戏秒，与截图45秒并列保留，见上方逐项表。',c()+sk(43023604,43023615,43023616,43023630,43023631,43023632))
add('能力二','全体/沙漠/自身强化','yes','全体攻击/防御15%与12.5%；沙漠自身另5%，攻击间隔约1.1秒','43023605 ability1017：1.15/1.15/.85；43023606 ability1008：1.125/1.125/.875；43023607 ability7：1.05/1.05/.95，param7=.75','攻防/移动/暴击各档及间隔×.75已分别确认，见上方逐项表；间隔中性名义1.5×.75=1.125游戏秒，约1.1秒。完整叠加/动画周期另论。',sk(43023605,43023606,43023607))
add('能力二','WAVE 增强与 Chain 玛那','raw','120秒；攻击/防御15%与10%；战士更高；1stChain20%获得一次','43023608 ability65:param0=120,param1/2=.15；43023609 ability64:param0=120,param1/2=.1,param6=20','全体攻击/本项减伤15%、战士额外10%及120游戏秒已确认并逐项交付；64/65为同类加算。64.param6=20在该路径用于目标数量；Chain玛那已核ordinary1106/43023617有效四档为10%，截图20%；两份本地技能快照同值。不能将64.param6=20当概率，见上方逐项差异。',sk(43023605,43023608,43023609))
job=aux('job_ability','cids',30236)
add('Class','Class 能力与常驻/全体强化','diff','自身攻击1150%、防御50%、暴击率20%、暴击威力200%；全体攻击50%、防御15%','job_ability.cids 包含30236 → skill_ids=[65000001,65000002,65000003]；65000001 参数12.5/2/.5/1/.4/3.5；65000002 参数1.5/1.15/.85','自身及全体攻防已逐项确认；Class暴击伤害系数+2.0（200个百分点）。当前1095.param5=.4在代码直接加概率，即+40个百分点，与截图20%有差异；保留两者。自身/全体移动分别+100%/+15%已确认。',job+sk(65000001,65000002))
add('Class','暴击吸血与超上限','diff','按伤害20%回复，超上限40%','65000003 ability21：param1=.25；flag0_1=512','暴击回复输入=floor(本次伤害处理返回整数×25%)，与截图20%有差异。flag0_1左移32位后bit41经Heal掩码选择1.4倍最大HP档位，与截图超出40%对应；完整回复资格/实际装载另论。',job+sk(65000003))
bond=aux('supporterskill','ability_id',30236)
add('羁绊','羁绊名称、文案与四槽','yes','《竜の眷属》の献身','supporterskill ability_id=30236；abi0/1/2/3=115010/102070/102071/106001','名称、完整日文文案与四槽完整保留；从卡牌sup1关联。',c()+bond)
add('羁绊','初始玛那、沙漠强化、必杀强化','diff','1万象；沙漠全体5%/自身25%；必杀15%','115010.param7=1；102070.param1=1.05；102071.param0=4、param1=1.25。102071名称写砂漠，但 text 写森林','已核102071.param0=4通过当前背景flag16匹配沙漠，与名称相符；自身text写森林的源内矛盾保留。106001缓存缺ID，已按既有逐ID规则在APK找到param0=1.149999976158142；本项约+15%为显示舍入，未改原值。',bond+sk(115010,102070,102071))
extra=aux('extra_ability_info')
add('Extra','等级与32/34/36/38/40%','yes','紡がれた絆の力；初始万象；同Chain下次必杀32/34/36/38/40%；后备有效','extra_abilities 保存五档 lv、text 与 skill_ids','这些百分数直接出现在游戏原始文案，可确认“文案数值已取得”；执行叠加与玩家开放等级尚未验证。',extra)
leader=aux('leader_ability')
add('Leader','强化与 Leader 共鸣数值','yes','全体60%、沙漠10%；Leader共鸣3%、沙漠2%','leader_ability.text / sympathy_text 直接含60%/10%/3%/2%；各有技能ID数组','可确认原文数值与关联入口已取得，不等于已经验证实际战斗累积。',leader)
add('Leader','发动条件','raw','战士4人以上；其他队员发动Leader时共鸣','border=4；category=2；conditions=[0]；target=0','category2为职业列表、0为战士，border4要求候选职业命中累计至少4；已由局部代码/边界确认。完整候选队伍及共鸣资格另论，target0只确认装入_rule。',leader)
add('共鸣','常规共鸣增强','raw','含自身触发共鸣必杀：45秒攻击10%加算、暴击威力10%；后备有效','sympathy_skill_info._id=30236 → ability0=43023610 → sub43023611；param1=.1,param2=.1,param6=45,param8=.1','已确认通常/必杀攻击各+10%，Support3同类加算，45游戏秒；见上方单项表。完整后备/触发资格另论。',aux('sympathy_skill_info','_id')+sk(43023610,43023611))
add('共鸣','MaxChain 沙漠300秒','raw','MaxChain触发；自身必杀发动期间除外；同Chain一次','43023610 ability3005：str0=43023604；同号Boss pattern →43023613(type66)，参数含300','文字与引用链已找到，type66时间配置确认300游戏秒；完整MaxChain资格、字符串调用入口另论。',sk(43023610)+bp(43023604)+bs(43023613))
add('排除项','中文名、标签、外部资料','out','网站中文译名、页面标签、外链','按用户说明不作为游戏提取缺口','页面对照说明为中文分析文本，与游戏日文原文分开保存。',[])

def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

# Curated type-scoped semantic overlay; the historical v3 observations stay unchanged.
trace = json.loads((TYPE105/'trace.json').read_text(encoding='utf-8'))
probe = json.loads((TYPE105/'native_checks.json').read_text(encoding='utf-8'))
assert trace['native_sha256'] == probe['native_sha256']
assert all(c['passed'] for c in probe['checks'])
conditions = 'Boss命名空间；APK 5.6.2/56021 type105处理器；需选中pattern并执行到该段；当前装载、玩家状态未知'
base_rule = 'B=getBasicSkillAttack(true)：含初始化时从BattleParam._skillAtk取得的技能攻击输入、_statusAtk、skillChainRate、技能增伤、武器及局部支持等因子；并非直接面板ATK。Chain在B内相乘，type105不再次乘Chain。'
rules = [
    dict(source='CACHE',table='bossskill',record_type='skillid0=105',effect_type=105,field_path='/skillparam1',meaning_zh='单次前方攻击的技能基值倍率',unit='倍（相对B）',conversion='damage_input=floor/clamp(float32(B × skillparam1))；有限正常范围向下取整',base_definition=base_rule,status='已确认（静态及受控原生局部规则）',applicability=conditions,evidence=['../boss_chain/type105/5351.txt:1181a34–1181a54/1181a80–1181a8c','../boss_chain/type105/5360.txt:1182f90–1182fe0/1183168–1183174','../boss_chain/type105/5409.txt:118a2e8–118a314/118a740–118a774','../boss_chain/type105/trace.json conversion_fragment','../boss_chain/type105/native_checks.json'],limits='Attack之前的整数伤害输入；目标防御、元素、标志及实际HP变化另行处理；面板ATK到BattleParam._skillAtk关系未验证'),
    dict(source='CACHE',table='bossskill',record_type='skillid0=105',effect_type=105,field_path='/skillparam6',meaning_zh='每目标前方连击尝试次数上限',unit='次/目标',conversion='有限正数向零截断为整数；每目标计数先加1，再判范围并决定是否调用Attack',base_definition=None,status='已确认（静态及受控原生局部规则）',applicability=conditions,evidence=['../boss_chain/type105/5351.txt:1181ad0–1181adc','../boss_chain/type105/5409.txt:118a5bc–118a5d8/118a63c–118a68c/118a6f8–118a774','../boss_chain/type105/native_checks.json'],limits='持续在范围内且更新足够时可调用相应次数；范围外也消耗次数，不能保证实际命中数；一次update每目标至多一次尝试')]
type105_skills=[r for r in records if r['table']=='bossskill' and r['raw'].get('skillid0')==105]
for rule in rules:
    rule['target']='处理器选择的前方范围目标；每目标独立计数；成员列表的完整筛选未在受控夹具中执行'
field_views=[]
for r in type105_skills:
    for rule in rules:
        field=rule['field_path'][1:]
        if field not in r['raw']: continue
        value=r['raw'][field]
        assert isinstance(value,(int,float)) and not isinstance(value,bool)
        field_views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='Boss skill',record_id=r['raw']['skillid'],effect_type=105,field_path=rule['field_path'],raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+rule['field_path'],meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=rule['conversion'],converted_value=int(value) if field=='skillparam6' else None,display_value=f'{value:g}倍B（每次）' if field=='skillparam1' else f'{int(value)}次/目标（尝试上限）',raw_value_status='RAW_FOUND',correspondence_status='TYPE105_HANDLER_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=conditions,evidence=rule['evidence'],limits=rule['limits']))
for rule in rules:
    rule['occurrences']=sum(v['field_path']==rule['field_path'] for v in field_views)
    rule['unit_status']='已确认（限定type105）'
for pid,sid,mode in ((43023601,43023600,'普通'),(43023600,43023605,'沙漠档'),(43023602,43023609,'超共鸣')):
    p=one('bosspattern','patternid',pid)
    assert p['raw']['skillid0']==sid
    for v in field_views:
        if v['record_id']!=sid: continue
        type105_row['field_comparisons'].append(dict(v,cid=30236,card_name_ja=card['raw']['title']+' '+card['raw']['name'],mode=mode,pattern_id=pid,pattern_record_key=p['record_key'],skill_name_ja=p['raw'].get('sname'),description_ja=p['raw'].get('sinfo'),description_note='本pattern缺失sinfo，不补写' if 'sinfo' not in p['raw'] else '本pattern原文',screenshot_item=type105_row['screenshot'],comparison_result='局部系数和尝试次数与截图一致；实际扣血/实际命中未知'))
type105_row.update(raw_value_status='RAW_FOUND',correspondence_status='CONFIRMED_PATTERN_CODE_AND_SCREENSHOT_VALUES',calculation_status='CONFIRMED_LOCAL_INPUT_RULE_NOT_FINAL_DAMAGE')

# Type112 has its own creation/storage path; do not infer it from type105's handler.
trace112=json.loads((TYPE112/'trace.json').read_text(encoding='utf-8'))
probe112=json.loads((TYPE112/'native_checks.json').read_text(encoding='utf-8'))
assert trace112['native_sha256']==probe112['native_sha256']==trace['native_sha256']
assert all(c['passed'] for c in probe112['checks'])
conditions112='Boss命名空间；APK 5.6.2/56021 type112设置陷阱处理器；需执行到设置/触发段；当前装载及玩家状态未知'
rule112=dict(source='CACHE',table='bossskill',record_type='skillid0=112',effect_type=112,field_path='/skillparam1',meaning_zh='单次陷阱攻击的设置时技能基值系数',unit='倍（相对设置时B_set）',conversion='stored_damage=floor/clamp(float32(B_set × skillparam1))；经CoveringFirePoint→BulletDelay保存，随后原样传给Attack入口',base_definition='B_set=getBasicSkillAttack(true)，在type112设置阶段计算，含skillChainRate、BattleParam._skillAtk及状态/技能等因子；此伤害值的传递链未再次求基值或乘Chain，非直接面板ATK。',status='已确认（静态及受控原生局部规则）',applicability=conditions112,evidence=['../boss_chain/type112/5466.txt:1198ce8–1198d04/11991c4–1199230','../boss_chain/type112/7401.txt:1579608–157961c','../boss_chain/type112/7406.txt:1579d90–1579e20','../boss_chain/type112/5846.txt:15ac564–15ac5a4','../boss_chain/type112/5850.txt:15acca0–15acce8/15acd08–15acd20','../boss_chain/type105/5360.txt','../boss_chain/type112/native_checks.json'],limits='只确认单次攻击输入及其保存/传递；未验证布置数量、触发次数、间隔、击倒、面板ATK换算和实际HP变化',occurrences=0,unit_status='已确认（限定type112）',target='一次陷阱爆发中由延迟攻击对象选出的目标；目标选择及触发循环未完整模拟')
time_trace=json.loads(Path('output/boss_heal/trace.json').read_text(encoding='utf-8'))
assert time_trace['native_sha256']==trace112['native_sha256']
type112_rules=[rule112]
for field,meaning,unit,conversion,target,ev,limits in [
    ('skillparam0','陷阱爆发的有敌门控模式','枚举：1有敌门控，2定时模式','原值有限且等于1时fireType=1，否则0；模式1仅IsInEnemy=true时爆发，模式0不检查有敌','陷阱对象的爆发门控','5466.txt:1198e5c–1198e80/1199108–1199110;7403.txt:1579a68–1579a90','仅按本缓存观察的1/2解释；有敌检测仍包含成员筛选/位置/半径条件，不代表任意敌人都可触发'),
    ('skillparam4','每陷阱爆发间隔','游戏秒（fixedDeltaTime累计）','原值→CoveringFirePoint._interval；_passTime累积delta，到间隔且门控通过后爆发并归零；一次update最多一次','每个陷阱对象，非每目标','5466.txt:1198d70/1199228;7401.txt:1579668–1579684;7403.txt:1579a44–1579a90;../boss_heal/3622.txt','无敌时计时仍累积；不以次数×间隔承诺精确总时长；fixedDeltaTime链复用boss_heal同native证据'),
    ('skillparam5','每陷阱对象最大爆发次数','次/陷阱对象','有限正数向零截断→_maxFireCount；每次ShootDelayBullet前_fireCount加1，随后比较达到上限则移除','同一陷阱对象共享，多个目标不分别扣次数','5466.txt:1198d18–1198d60/11991d0–1199230;7401.txt:1579678;7403.txt:1579a80–1579a9c/1579b3c','本缓存存在值均为正整数1—10；零值为爆发后检查边界，不当作无限；缺失字段不补0'),
    ('skillparam8','6×3陷阱设置位置位图','位图（bit i→列i%6、行i//6）','先向零截断；MakeFieldBitArea按6列3行映射，原点为anchor−(3,1)，bEdge=true时整体夹在场地边界内；88725置位9格','位置模板；默认初始化战场6×3时为整盘交错九格','5466.txt:1198f58/11990a0–11990d4/1199114–11992a4;9180.txt;7698.txt:156e8d4–156e8fc;trace.json ground_initializer','只解释18位非负模板；实际场地尺寸可由运行时改变，不冒充固定世界坐标；初始化常量为6×3'),
    ('skillparam9','设置前保留旧陷阱的开关','整数化后非0保留；0调用清理','有限值向零截断；结果非0跳过deleteFirePointTransform，0先调用清理；本卡相同掩码两段均为1','施法者已有的陷阱对象；具体清理函数内部筛选本规则不展开','5466.txt:1198c04–1198c88','本缓存92项存在值均为1，缺失不补默认；两段都执行时九位置各两次initialize，未模拟完整pattern资格'),
    ('skillparam7','推力及强受击输入（原文転倒对应为推断）','推力输入，非伤害倍率','经CoveringFirePoint._PushPower→BulletDelay→Attack.pushPower；正值在未锁定/未免推等条件下请求eCharaState.DamageL(10)','被攻击目标的受击状态；资格/抵抗可阻止','5466.txt:1198d74/11991f0;7401.txt:1579650;7406.txt:1579dd8;5846.txt:15ac5a8;5850.txt:15accb4–15acce8;6986.txt:1772b50–1772ca4;trace.json damage_reaction_state','推力传值和状态门控已确认；实际动画、目标完整抵抗及与原文転倒的视觉对应未验证')]:
    type112_rules.append(dict(rule112,field_path='/'+field,meaning_zh=meaning,unit=unit,conversion=conversion,base_definition=None,target=target,evidence=[part if part.startswith('../boss_heal/') else '../boss_chain/type112/'+part for part in ev.split(';')]+['../boss_chain/type112/native_checks.json'],limits=limits,occurrences=0))
    if field=='skillparam7':type112_rules[-1]['status']='已确认（推力/状态请求）；推断（原文転倒动作对应）'
type112_skills=[r for r in records if r['table']=='bossskill' and r['raw'].get('skillid0')==112]
for rule in type112_rules:
    field=rule['field_path'][1:]
    for r in type112_skills:
        if field not in r['raw']:continue
        value=r['raw'][field]
        assert isinstance(value,(int,float)) and not isinstance(value,bool)
        converted={'skillparam0':1 if value==1 else 0,'skillparam4':float(value),'skillparam5':int(value),'skillparam8':int(value).bit_count(),'skillparam9':int(value)!=0,'skillparam7':float(value)}.get(field)
        display={'skillparam0':'有敌才爆发' if value==1 else '定时爆发','skillparam1':f'{value:g}倍B_set（每次陷阱攻击）','skillparam4':f'{value:g}游戏秒/次','skillparam5':f'{int(value)}次/陷阱（共用额度）','skillparam8':f'{int(value)}→{int(value).bit_count()}置位格（6×3模板）','skillparam9':'保留旧陷阱' if int(value)!=0 else '先调用旧陷阱清理','skillparam7':f'{value:g}推力；转倒动作对应为推断'}[field]
        field_views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='Boss skill',record_id=r['raw']['skillid'],effect_type=112,field_path=rule['field_path'],raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+rule['field_path'],meaning_zh=rule['meaning_zh'],unit=rule['unit'],target=rule['target'],conversion=rule['conversion'],converted_value=converted,display_value=display,raw_value_status='RAW_FOUND',correspondence_status='TYPE112_HANDLER_MAPPING_CONFIRMED',calculation_status='CONFIRMED_LOCAL_INPUT_RULE',conditions=conditions112,evidence=rule['evidence'],limits=rule['limits']))
        if field=='skillparam7':field_views[-1].update(correspondence_status='INFERRED_DESCRIPTION_TO_DAMAGEL_ACTION',calculation_status='CONFIRMED_LOCAL_PUSH_INPUT_AND_STATE_GATE')
    rule['occurrences']=sum(v['effect_type']==112 and v['field_path']==rule['field_path'] for v in field_views)
rules.extend(type112_rules)
for pid,sids,mode in ((43023601,(43023602,43023603),'普通'),(43023600,(43023606,43023607),'沙漠档'),(43023602,(43023610,43023611),'超共鸣')):
    p=one('bosspattern','patternid',pid)
    for slot,sid in enumerate(sids,2):
        assert p['raw'][f'skillid{slot}']==sid
        for v in (v for v in field_views if v['effect_type']==112 and v['record_id']==sid):
            type112_row['field_comparisons'].append(dict(v,cid=30236,card_name_ja=card['raw']['title']+' '+card['raw']['name'],mode=mode,pattern_id=pid,pattern_slot=slot,pattern_record_key=p['record_key'],skill_name_ja=p['raw'].get('sname'),description_ja=p['raw'].get('sinfo'),description_note='本pattern缺失sinfo，不补写' if 'sinfo' not in p['raw'] else '本pattern原文',screenshot_item=type112_row['screenshot'],comparison_result='系数/5次/9格两层有局部代码对应；转倒动作对应为推断，最终扣血未知'))
type112_row.update(raw_value_status='RAW_FOUND',correspondence_status='CONFIRMED_VALUES_AND_LAYOUT_PUSH_DESCRIPTION_INFERRED',calculation_status='CONFIRMED_LOCAL_TRAP_RULES_FINAL_STATE_AND_DAMAGE_UNKNOWN')

guard_trace=json.loads((GUARD_BASIS/'trace.json').read_text(encoding='utf-8'))
guard_checks=json.loads((GUARD_BASIS/'native_checks.json').read_text(encoding='utf-8'))
assert guard_trace['native_sha256']==guard_checks['native_sha256']==trace['native_sha256']
assert all(c['passed'] for c in guard_checks['checks'])
guard_rule=dict(source='CACHE',table='bossskill',record_type='skillid0=13',effect_type=13,field_path='/skillparam2',meaning_zh='固定防御值系数；玩家接受者的名义原始ATK换算',unit='相对_normalAtk的系数；已核玩家分支名义CardInfo.ATK系数=原值×.1',conversion='guard=trunc(float32(当前_normalAtk×float32(param2×Chain)))；已核构建片段先缩放并截断((CardInfo.ATK+belovedAtk)×.1×给定初始化因子)，后续设置仍可改_normalAtk',base_definition='接受者为已核BattleParam.CreatePlayer构建分支时成立；.1来自native常量0x2015cf4；不推广到未核NPC/怪物构建路径',status='已确认（限定玩家构造分支的有条件基数换算）',applicability='Boss type13进入既有支持分支；接受者按已核CreatePlayer路径构建；初始化修正、Chain及整数化保留，当前玩家状态未知',evidence=['../boss_chain/type13_basis/player_card_atk.txt','../boss_chain/type13_basis/player_atk_scale.txt','../boss_chain/type13_basis/support_guard.txt','../boss_chain/type13_basis/integer_truncation.txt','../boss_chain/type13_basis/trace.json','../boss_chain/type13_basis/native_checks.json'],limits='派生值只为名义原始ATK系数，不是实际固定防御量或最终减伤；双重截断可能使小数边界不同；后续常驻/传授/变身等修改未模拟；未核其他构造分支',occurrences=0,unit_status='已确认（限定玩家构造路径）',target='支持接受者自身_normalAtk，非施法者面板ATK')
guard_skills=[r for r in records if r['table']=='bossskill' and r['raw'].get('skillid0')==13 and 'skillparam2' in r['raw']]
for r in guard_skills:
    value=r['raw']['skillparam2']
    field_views.append(dict(record_key=r['record_key'],source=r['layer'],table=r['table'],namespace='Boss skill',record_id=r['raw']['skillid'],effect_type=13,field_path='/skillparam2',raw_value=value,original_file=r['original_file'],source_sha256=r['source_sha256'],location=r['location'],json_pointer=r['location']['json_pointer']+'/skillparam2',meaning_zh=guard_rule['meaning_zh'],unit=guard_rule['unit'],target=guard_rule['target'],conversion=guard_rule['conversion'],converted_value=value*.1,display_value=f'名义原始ATK×{value*10:g}%（玩家分支，含修正/截断条件）',raw_value_status='RAW_FOUND',correspondence_status='CONFIRMED_TYPE13_FIXED_GUARD_MAPPING',calculation_status='CONDITIONAL_PLAYER_NORMAL_ATK_BASIS',conditions=guard_rule['applicability'],evidence=guard_rule['evidence'],limits=guard_rule['limits']))
guard_rule['occurrences']=len(guard_skills);rules.append(guard_rule)
for pid,sid,mode in ((43023601,43023604,'普通'),(43023600,43023608,'沙漠档'),(43023602,43023612,'超共鸣')):
    p=one('bosspattern','patternid',pid);assert p['raw']['skillid4']==sid
    v=next(v for v in field_views if v['effect_type']==13 and v['record_id']==sid)
    guard_row['field_comparisons'].append(dict(v,cid=30236,card_name_ja=card['raw']['title']+' '+card['raw']['name'],mode=mode,pattern_id=pid,pattern_slot=4,pattern_record_key=p['record_key'],skill_name_ja=p['raw'].get('sname'),description_ja=p['raw'].get('sinfo'),description_note='本pattern缺失sinfo，不补写' if 'sinfo' not in p['raw'] else '本pattern原文',screenshot_item=guard_row['screenshot'],comparison_result='名义3/3.25/3.75%基数关系已对应；实际固定量含初始化修正及两次截断，不宣称最终伤害一致'))
guard_row.update(raw_value_status='RAW_FOUND',correspondence_status='CONFIRMED_NOMINAL_SCREENSHOT_PERCENT_BASIS',calculation_status='CONFIRMED_PLAYER_BASIS_WITH_MODIFIERS_AND_TRUNCATION')

ordinary_rules,ordinary_views=ordinary_overlay(records)
rules.extend(ordinary_rules);field_views.extend(ordinary_views)
barrier_rules,barrier_views=barrier_overlay(records)
rules.extend(barrier_rules);field_views.extend(barrier_views)
critical_rules,critical_views=critical_overlay(records)
rules.extend(critical_rules);field_views.extend(critical_views)
movement_rules,movement_views=movement_overlay(records)
rules.extend(movement_rules);field_views.extend(movement_views)
lifesteal_rules,lifesteal_views=lifesteal_overlay(records)
rules.extend(lifesteal_rules);field_views.extend(lifesteal_views)
field_time_rules,field_time_views=field_time_overlay(records)
rules.extend(field_time_rules);field_views.extend(field_time_views)
mana_chance_rules,mana_chance_views=mana_chance_overlay(records)
rules.extend(mana_chance_rules);field_views.extend(mana_chance_views)
chain_mana_rules,chain_mana_views=chain_mana_overlay(records)
rules.extend(chain_mana_rules);field_views.extend(chain_mana_views)
leader_condition_rules,leader_condition_views=leader_condition_overlay(records)
rules.extend(leader_condition_rules);field_views.extend(leader_condition_views)
super_counter_rules,super_counter_views=super_counter_overlay(records)
rules.extend(super_counter_rules);field_views.extend(super_counter_views)
wedge_time_rules,wedge_time_views=wedge_time_overlay(records)
rules.extend(wedge_time_rules);field_views.extend(wedge_time_views)

extend_1008(records,rules,field_views)
extend_7(records,rules,field_views)
extend_99(records,rules,field_views)
extend_3000(records,rules,field_views)
extend_2012(records,rules,field_views)
extend_1017(records,rules,field_views)
extend_1095(records,rules,field_views)
difference_source_overlay(records,rules,field_views)

def save_table(stem,data):
    save(stem+'.json',data)
    with (OUT/(stem+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader()
        for r in data:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
description_effects=build_effects(records)
adoption_policy=apply_source_priority(rules,field_views,description_effects,rows)
save_table('field_dictionary',rules)
save_table('verified_parameter_views',field_views)
save_table('description_effects',description_effects)
save('comparison.json',rows);save('evidence.json',list(evidence.values()))
with (OUT/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
    for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
image_path=OUT/'reference.png'
assert image_path.exists(), 'Provide the original screenshot as output/card_comparison_cid30236/reference.png'
esc=html.escape
counts=Counter(r['status'] for r in rows)
cards=[]
for r in rows:
    details=''.join('<details><summary>'+esc(k)+'</summary><pre>'+esc(json.dumps(evidence[k],ensure_ascii=False,indent=2))+'</pre></details>' for k in r['record_keys'])
    field_detail=''
    if r['field_comparisons']:
        lines=''.join('<tr>'+''.join('<td>'+esc(str(v[k]))+'</td>' for k in ('mode','record_id','field_path','raw_value','display_value'))+'</tr>' for v in r['field_comparisons'])
        effect_type=r['field_comparisons'][0]['effect_type']
        checks_count={105:len(probe['checks']),112:len(probe112['checks']),13:len(guard_checks['checks'])}[effect_type]
        scope_note={105:'最终扣血未知。',112:'次数/间隔/九格已确认；转倒动作对应为推断，最终扣血未知。',13:'名义玩家基数已确认；保留初始化修正、逐步整数化和最终叠加条件。'}[effect_type]
        proof_dir='type13_basis' if effect_type==13 else 'type'+str(effect_type)
        field_detail='<p>原值已找到：已确认 · 局部计算规则：'+scope_note+'</p><div style="overflow-x:auto"><table><thead><tr><th>档位</th><th>Boss ID</th><th>字段</th><th>原值</th><th>解释</th></tr></thead><tbody>'+lines+'</tbody></table></div><p><a href="field_dictionary.json">字段字典（规则按效果类型分开）</a> · <a href="verified_parameter_views.csv">原值与局部解释 CSV</a> · <a href="../boss_chain/'+proof_dir+'/native_checks.json">'+str(checks_count)+'项受控检查与边界</a></p>'
    cards.append(f'<article data-status="{r["status"]}"><div class="eyebrow">{esc(r["group"])} · {r["number"]:02}</div><h3>{esc(r["title"])}</h3><span class="badge {r["status"]}">{labels[r["status"]]}</span><div class="pair"><section><label>截图中的信息</label><p>{esc(r["screenshot"])}</p></section><section><label>本地提取记录</label><p>{esc(r["extracted"])}</p></section></div><p class="conclusion">{esc(r["conclusion"])}</p>{field_detail}<details><summary>查看来源与完整原始记录（{len(r["record_keys"])}）</summary>{details}</details></article>')
buttons='<button class="active" data-filter="all">全部 '+str(len(rows))+'</button>'+''.join(f'<button data-filter="{k}">{v} {counts[k]}</button>' for k,v in labels.items())
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>チーカ · 截图与解包数据对照</title><style>
:root{color-scheme:light;--ink:#192b36;--muted:#586b76}*{box-sizing:border-box}body{margin:0;background:#edf2f5;color:var(--ink);font:15px/1.7 "Microsoft YaHei",sans-serif}header{background:#123343;color:white;padding:38px max(26px,4vw)}h1{margin:5px 0 12px;font-size:30px}header p{max-width:1100px;color:#d9e6ec;margin:8px 0}.eyebrow{font-size:12px;letter-spacing:1px;color:#6b7d87}header .eyebrow{color:#a3d7d6}.notice{margin:20px 4vw;padding:18px 22px;background:#fff;border-left:4px solid #218282}.layout{display:grid;grid-template-columns:minmax(290px,34%) minmax(0,1fr);gap:24px;margin:24px 4vw}.reference{position:sticky;top:20px;align-self:start;background:white;border-radius:12px;padding:16px}.reference img{width:100%;display:block}.image-scroll{max-height:72vh;overflow:auto;margin-top:12px}.reference p{font-size:13px;color:var(--muted)}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}button,input{font:inherit;border:1px solid #b9cad3;border-radius:7px;background:white;padding:8px 11px}button{cursor:pointer;font-size:12px}button.active{background:#123343;color:white}input{width:100%}article{padding:23px;margin-bottom:16px;background:white;border:1px solid #d8e2e8;border-radius:12px;box-shadow:0 3px 12px #12334306}h3{margin:4px 0 10px;font-size:20px}.badge{display:inline-block;font-size:12px;border-radius:5px;padding:3px 9px}.yes,.resolved{color:#11664e;background:#dff4ea}.raw{color:#79560a;background:#fff0c9}.gap{color:#9b3636;background:#fce4e4}.diff{color:#743f8b;background:#f0e4f8}.out{color:#52616c;background:#e7edf0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}.pair section{background:#f5f8fa;border-radius:8px;padding:14px}label{font-size:12px;color:#617581}p{margin:7px 0}.conclusion{border-left:3px solid #bdced7;padding-left:13px;margin:17px 0}details{margin-top:8px;font-size:12px}summary{cursor:pointer;overflow-wrap:anywhere;color:#34637a}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:480px;overflow:auto;background:#eef3f6;padding:14px}a{color:#167684}header a{color:#ade4e6}.foot{margin:30px 4vw 50px;color:#586b76}#visible{font-size:13px;color:#586b76;margin-bottom:12px}@media(max-width:950px){.layout{grid-template-columns:1fr}.reference{position:static}.image-scroll{max-height:400px}.pair{grid-template-columns:1fr}h1{font-size:25px}}@media print{.reference,.toolbar{display:none}.layout{display:block}article{break-inside:avoid;box-shadow:none}details{display:none}}
</style><header><div class="eyebrow">本地快照证据对照 / CID 30236 / 2026-10-15</div><h1>这张チーカ，哪些已经解出来了？</h1><p>整卡技能数值已按描述拆行，具体答案、单位、证据及剩余缺口见下表。截图差异并列保留；等级面板、实际装载与完整战斗汇总另论。</p><p>绿色表示文本、字段或限定局部规则已对应，黄色表示原值存在但解释未完成，绿色的“已裁决”另指采用解包/代码，截图不同值仍保留；紫色为其余待核差异，红色表示尚未建立对应。条目数是本页整理项数，不是完成百分比。</p><a href="comparison.csv">下载 CSV</a> · <a href="comparison.json">对照 JSON</a> · <a href="evidence.json">完整记录与定位</a></header>
<div class="notice"><b>两份证据分开看：</b>左边是用户提供的数据库截图，右边是手机缓存实际提取记录。不会用截图补写原始字段。绿色的“文案里有百分比”也不等于代码已经验证该倍率。该卡主表 revision=1，当前游戏实际装载版本与玩家解锁状态未知。</div>
<main class="layout"><aside class="reference"><b>用户截图 · 原图参照</b><p>可在这里滚动；点击图片在新窗口放大。中文名、标签、外部资料、获得来源和登场日期按用户说明排除。</p><div class="image-scroll"><a href="reference.png" target="_blank"><img src="data:image/png;base64,IMAGE_DATA" alt="用户提供的チーカ数据库全页截图"></a></div></aside><div><div class="toolbar">BUTTONS<input id="search" placeholder="筛选：如 45秒、Class、43023601、沙漠"></div><div id="visible"></div>CARDS</div></main>
<div class="foot"><b>来源与解释边界</b><p>表字段原值来自 cache_full_20261015_v3/records.jsonl；共用10次等代码常量另列原生镜像路径、指令字节和RVA，不冒充表字段。后续 refresh_20261015 的77个data5与该快照一致；新增165个bdl不代表新增主表记录。每条证据附原文件、SHA256、JSON指针和记录字节定位。羁绊106001缓存缺ID后按既有逐ID回退本地APK；原浮点值与组件/导出JSON定位见skill_power/trace.json。APK不与缓存逐字段混合。</p><p>type13 局部解释复用 ../boss_chain/field_dictionary.json 与 ../boss_heal/field_dictionary.json；其他类型若无处理器证据只列原值。普通 skilllist 与 Boss skill 的同号ID分属不同表。保留缺失、原文矛盾与尚未关联项。</p><p>此页可用于找到这张卡的原文、记录入口和候选数值；不能用于计算完整战斗倍率、证明全游戏覆盖、判定玩家解锁状态；五组截图冲突的采用值按用户政策另列，不证明网站注数成因。</p></div><script>
let mode='all';function filter(){let n=0,q=document.querySelector('#search').value.toLowerCase();document.querySelectorAll('article').forEach(a=>{let show=(mode==='all'||a.dataset.status===mode)&&a.textContent.toLowerCase().includes(q);a.hidden=!show;if(show)n++});document.querySelector('#visible').textContent='当前显示 '+n+' 项；展开每项可查看未改写的原始证据。'}document.querySelectorAll('button[data-filter]').forEach(b=>b.onclick=()=>{mode=b.dataset.filter;document.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));filter()});document.querySelector('#search').oninput=filter;filter();</script></html>'''
page=page.replace('IMAGE_DATA',base64.b64encode(image_path.read_bytes()).decode()).replace('BUTTONS',buttons).replace('CARDS',''.join(cards))
page=page.replace('<div class="toolbar">',render_reusable_effects(field_views)+render_reusable_effects(field_views,1017)+render_reusable_effects(field_views,2012)+render_reusable_effects(field_views,3000,records)+render_reusable_effects(field_views,99)+render_reusable_effects(field_views,7)+render_reusable_effects(field_views,1008)+render_effects(description_effects)+'<div class="toolbar">')
page=page.replace("querySelectorAll('article')","querySelectorAll('article[data-status]')")
page=page.replace('其他类型若无处理器证据只列原值。','type105/112 局部解释见本页字段字典及 ../boss_chain/type105、type112；其余类型若无处理器证据只列原值。')
page=page.replace('</style>','table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;padding:8px;border:1px solid #d8e2e8;overflow-wrap:anywhere}</style>')
(OUT/'index.html').write_text(page,encoding='utf-8')
semantic_paths=list((OUT/'wedge_time').glob('*.txt'))+[OUT/'wedge_time'/'trace.json',OUT/'wedge_time'/'native_checks.json',OUT/'wedge_time'/'README.md']+list((OUT/'super_counter').glob('*.txt'))+[OUT/'super_counter'/'trace.json',OUT/'super_counter'/'native_checks.json',OUT/'super_counter'/'README.md',Path('work/protection/il2cpp_loader_seed1.bin')]+list((OUT/'leader_condition').glob('*.txt'))+[OUT/'leader_condition'/'trace.json',OUT/'leader_condition'/'native_checks.json',OUT/'leader_condition'/'README.md']+list((OUT/'chain_mana').glob('*.txt'))+[OUT/'chain_mana'/'trace.json',OUT/'chain_mana'/'native_checks.json',OUT/'chain_mana'/'README.md']+list((OUT/'mana_chance').glob('*.txt'))+[OUT/'mana_chance'/'trace.json',OUT/'mana_chance'/'native_checks.json',OUT/'mana_chance'/'README.md']+list((OUT/'field_time').glob('*.txt'))+[OUT/'field_time'/'trace.json',OUT/'field_time'/'native_checks.json',OUT/'field_time'/'README.md']+list((OUT/'lifesteal').glob('*.txt'))+[OUT/'lifesteal'/'trace.json',OUT/'lifesteal'/'native_checks.json',OUT/'lifesteal'/'README.md']+list((OUT/'movement').glob('*.txt'))+[OUT/'movement'/'trace.json',OUT/'movement'/'native_checks.json',OUT/'movement'/'README.md']+list((OUT/'critical').glob('*.txt'))+[OUT/'critical'/'trace.json',OUT/'critical'/'native_checks.json',OUT/'critical'/'README.md']+list((OUT/'barrier').glob('*.txt'))+[OUT/'barrier'/'trace.json',OUT/'barrier'/'native_checks.json',OUT/'barrier'/'README.md']+list((OUT/'timed_support').glob('*.txt'))+[OUT/'timed_support'/'trace.json',OUT/'timed_support'/'native_checks.json',OUT/'timed_support'/'README.md']+list((OUT/'skill_power').glob('*.txt'))+[OUT/'skill_power'/'trace.json',OUT/'skill_power'/'native_checks.json',OUT/'skill_power'/'README.md',Path('output/base_master/_mdSkill.json'),Path('output/base_master/report.json')]+list((OUT/'ordinary_rules').glob('*.txt'))+[OUT/'ordinary_rules'/'trace.json',OUT/'ordinary_rules'/'native_checks.json',OUT/'ordinary_rules'/'README.md']+[p for root in (TYPE105,TYPE112,GUARD_BASIS) for p in (root/'trace.json',root/'native_checks.json')]+list(TYPE112.glob('*.txt'))+list(GUARD_BASIS.glob('*.txt'))+[TYPE105/'5351.txt',TYPE105/'5360.txt',Path('output/boss_heal/trace.json'),Path('output/boss_heal/3622.txt'),Path('output/boss_heal/constants.json')]
semantic_paths += [Path('output/ordinary_effects/ability1095')/name for name in ('trace.json','native_checks.json','README.md','attack_dispatch.txt','attack_getter.txt','attack_multiply.txt','defence_dispatch.txt','defence_getter_multiply.txt')]
semantic_paths += list(Path('output/ordinary_effects/ability1017').glob('*.txt'))+[Path('output/ordinary_effects/ability1017')/name for name in ('trace.json','native_checks.json','README.md')]
semantic_paths += list(Path('output/ordinary_effects/ability2012').glob('*.txt'))+[Path('output/ordinary_effects/ability2012')/name for name in ('trace.json','native_checks.json','README.md')]
semantic_paths += list(Path('output/ordinary_effects/ability3000').glob('*.txt'))+[Path('output/ordinary_effects/ability3000')/name for name in ('trace.json','native_checks.json','README.md')]
semantic_paths += list(Path('output/ordinary_effects/ability99').glob('*.txt'))+[Path('output/ordinary_effects/ability99')/name for name in ('trace.json','native_checks.json','README.md')]
semantic_paths += list(Path('output/ordinary_effects/ability7').glob('*.txt'))+[Path('output/ordinary_effects/ability7')/name for name in ('trace.json','native_checks.json','README.md')]
semantic_paths += list(Path('output/ordinary_effects/ability1008').glob('*.txt'))+[Path('output/ordinary_effects/ability1008')/name for name in ('trace.json','native_checks.json','README.md')]
semantic_paths += [POLICY_PATH]
semantic_paths += list((OUT/'chain_dispatch').glob('*.txt')) + [OUT/'chain_dispatch'/name for name in ('trace.json','native_checks.json','README.md')]
semantic_paths += [OUT/'difference_sources'/'reference_observations.json',OUT/'difference_sources'/'trace.json',OUT/'difference_sources'/'README.md',Path('output/decoded/skilllist.data5.json.raw'),Path('output/export/snapshot_223183400c1c62013338/build_261ac189c316abba/manifest.json')]
semantic_paths += [Path('output/cache_full_20261015_v3/decoded/questdigest.data5.json.raw')]
semantic_paths += list((OUT/'barrier_request').glob('*.txt')) + [OUT/'barrier_request'/name for name in ('trace.json','native_checks.json','README.md')] + [Path('output/base_master/_mdBossInfo.json')]
save('manifest.json',dict(card_id=30236,source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),screenshot_sha256=hashlib.sha256(image_path.read_bytes()).hexdigest(),generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),semantic_inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in semantic_paths},analysis_scripts={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in map(Path,('scripts/boss_type105_trace.py','scripts/boss_type105_probe.py','scripts/boss_type112_probe.py','scripts/boss_guard_basis.py','scripts/chica_description_effects.py','scripts/chica_source_priority.py','scripts/ordinary_1095_probe.py','scripts/ordinary_1017_probe.py','scripts/ordinary_2012_probe.py','scripts/ordinary_3000_probe.py','scripts/ordinary_99_probe.py','scripts/ordinary_7_probe.py','scripts/ordinary_1008_probe.py','scripts/ordinary_effect_dictionary.py','scripts/query_effect_dictionary.py','scripts/chica_ordinary_rules.py','scripts/chica_skill_power.py','scripts/chica_timed_support.py','scripts/chica_barrier_rule.py','scripts/chica_barrier_request.py','scripts/chica_difference_sources.py','scripts/chica_critical_rules.py','scripts/chica_move_rules.py','scripts/chica_lifesteal.py','scripts/chica_field_time.py','scripts/chica_mana_chance.py','scripts/chica_chain_mana.py','scripts/chica_chain_dispatch.py','scripts/chica_leader_condition.py','scripts/chica_super_counter.py','scripts/chica_wedge_time.py','scripts/chica_remaining_effects.py','scripts/verify_chica_comparison.py'))},description_effect_count=len(description_effects),description_effects_answered=sum(r['readable_value'] is not None for r in description_effects),row_count=len(rows),evidence_record_count=len(evidence),status_counts=counts,type105_rules=2,type105_records=len(type105_skills),type105_present_fields=sum(v['effect_type']==105 for v in field_views),type13_basis_rules=1,type13_basis_records=len(guard_skills),type13_basis_present_fields=len(guard_skills),type112_rules=len(type112_rules),type112_records=len(type112_skills),type112_present_fields=sum(r['occurrences'] for r in type112_rules),payloads={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ('comparison.json','comparison.csv','evidence.json','field_dictionary.json','field_dictionary.csv','verified_parameter_views.json','verified_parameter_views.csv','description_effects.json','description_effects.csv','index.html')},reusable_1095_records=407,reusable_1095_fields=814,reusable_1017_records=321,reusable_1017_fields=1284,reusable_2012_records=406,reusable_2012_fields=1025,reusable_3000_records=382,reusable_3000_records_with_fields=348,reusable_3000_fields=1098,reusable_99_records=133,reusable_99_fields=382,reusable_7_records=64,reusable_7_fields=192,reusable_1008_records=37,reusable_1008_fields=111,scope='one card atomic effects plus CACHE1095 attack/defence, CACHE1017 recipient/job/attack/defence, CACHE2012 positive time/present critical deltas, CACHE3000 present normal/skill/time/critical damage, CACHE99 present target attack/incoming/time, CACHE7 terrain/self attack/incoming, CACHE1008 terrain/player recipient attack/incoming; not whole-game coverage'))
print(json.dumps(dict(output=str(OUT),rows=len(rows),evidence_records=len(evidence),counts=counts),ensure_ascii=False))
