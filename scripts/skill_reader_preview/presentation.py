"""Player-facing wording for the preview; the original answer stays in source."""
import re
import unicodedata
from wording import terms

EFFECT_LABELS = {
    'ダメージ（词表外）': '伤害', '開局マナ': '开局法珠', '回復（词表外）': '回复',
    '攻撃力': '攻击力', '防御力': '防御', '移動速度': '移动速度',
    'クリティカル発生率': '暴击率', 'クリティカル威力': '暴击威力',
    '与えるダメージ（词表外）': '造成的伤害', '受けるダメージ（词表外）': '受到的伤害',
    '威力（词表外）': '技能威力', 'HP回復': '生命回复', '継続時間': '持续时间',
    '効果（词表外）': '附加效果', '確率マナ獲得': '获得法珠的概率',
    'クリティカル攻撃机制（非暴击率/暴伤）': '暴击攻击方式',
    '攻撃速度（词表外）': '攻击速度', '攻撃間隔（词表外）': '攻击间隔',
    '定性机制': '特殊效果', 'クリティカル（発生率/威力未区分）': '暴击效果',
}

def num(x):
    return f'{float(x):.6g}'


TECHNICAL = re.compile(r'float32|floor\s*\(|clamp\s*\(|trunc\s*\(|min\s*\(|param\d*|iParam|skilllist\||bossskill\||normalAtk|0x[0-9a-f]+|OnAction|Support|ClockUp|delta|CACHE|Random\.|getBasic|reactive|frintm|fcvtms|Σ|s_flag|JOB_TYPE|TARGET_TYPE|atkspeed', re.I)


def change(label, delta, unit='%'):
    direction = '提高' if delta >= 0 else '降低'
    return f'{label}{direction} {num(abs(delta))}{unit}'


def effect_label(effect, original):
    label=EFFECT_LABELS.get(effect['effect_type'],effect['effect_type'].replace('（词表外）',''))
    span=effect.get('span')
    if not isinstance(span,list) or len(span)!=2:return label
    start,end=span
    if original[start:end]!=effect.get('snippet'):return label
    prefix=original[:start]
    if label=='技能威力':
        if prefix.endswith('必殺技の'):return '必杀威力'
        if prefix.endswith('反響の'):return '反响威力'
    if label=='回复' and original[start:end+1]=='回復量':return '回复量'
    # Classify this exact occurrence, not every recovery in the same sentence.
    if label=='回复' and (re.search(r'状態異常[をも]$', prefix) or original[end:].startswith('した状態異常')):
        return '解除异常状态'
    if label=='附加效果':
        if prefix.endswith('敵と味方にかかる'):return '敌方减益与我方增益'
        if prefix.endswith('味方にかかる'):return '我方增益'
    return label

def confidence(a):
    n, b = str(a.get('numeric_evidence', '')), str(a.get('association_evidence', ''))
    if '未知' in n or '未知' in b or not n or not b:
        return 'unknown'
    if '推断' in n or '推断' in b or a.get('evidence_scope') == 'BY_TYPE_EXTRAPOLATED':
        return 'inferred'
    return 'confirmed' if '确认' in n and '确认' in b else 'unknown'

def condition(a):
    """Keep runtime restrictions legible; full original conditions remain available."""
    c = str(a.get('condition_label') or '')
    if not c:
        c = str(a.get('conditions') or '')
    c=unicodedata.normalize('NFKC',c).replace(';','；').replace('(','（').replace(')','）').replace(':','：')
    rule=a.get('rule_key') or ''
    if c.startswith('hold_mana'):
        return '满足本句说明的法珠职业与数量条件时'
    if c.startswith('mana_count_up') or c.startswith('计数对象由'):
        return '按当前符合本句条件的法珠数量计算'
    if rule.startswith('skilllist|1059|'):
        return '满足本句的队伍条件时；人数递增效果仍待确认'
    if c=='状態異常の敵がいると':return '存在处于异常状态的敌人时'
    if c.endswith('の味方の場合'):
        jobs={'戦士':'战士','騎士':'骑士','弓使い':'弓手','魔法使い':'法师','僧侶':'僧侣'}
        parts=c[:-len('の味方の場合')].split('と')
        if all(p in jobs for p in parts):return '对我方'+('或'.join(jobs[p] for p in parts))+'生效时'
    m=re.fullmatch(r'HPが([\d.]+)%(以上|以下)の時',c)
    if m:return f'HP为{m[1]}%或{m[2]}时'
    m=re.fullmatch(r'(.*?)マナを所持していると',c)
    if m:
        job={'':'','騎士':'骑士','戦士':'战士','弓使い':'弓手','魔法使い':'法师','僧侶':'僧侣'}.get(m[1])
        if job is not None:return f'持有{job}法珠时'
    m=re.fullmatch(r'戦場に自身以外の(.*?)味方がいる(?:と|場合)',c)
    if m:
        role={'':'','魔法使いの':'法师','<副都>所属の':'〈副都〉所属'}.get(m[1])
        if role is not None:return f'战场上有自身以外的{role}我方角色时'
    if c.startswith('父文案砂漠'):return '地形条件的原文存在矛盾（沙漠／森林），对应仍待核实'
    if c.startswith('句面条件「戦闘時」'):return '战斗时'
    if c.startswith('句面自身对象'):return '作用对象为自身；与强化条件的对应仍需核实'
    if c.startswith('句面对象自身'):return '此项加速作用于自身'
    if c.startswith('传授（denju）首段'):return '传授必杀的首段生效时'
    if c.startswith('传授（denju）发动期间'):return '传授必杀发动期间，共鸣必杀基础档生效时'
    if c.startswith('击杀时'):return '击倒敌人时；各攻击方式的数值分别列出'
    if c.startswith('地形掩码命中'):return '满足本句地形条件并击倒敌人时（地形对应见来源）'
    if c.startswith('持有者自身；地形资格'):return '自身满足本句地形条件时（对应为推断）'
    if c.startswith(('本卡 pattern','本卡卡面 skilltext','charainfo.pattern','denju.patternid')):
        return '本条必杀对应的分支生效时；实际选用条件仍待核实'
    if c.startswith(('job_ability.cids','Class配置')):return '本角色的职业能力生效时'
    if c.startswith('D1：'):return '仅确认共同持续时间，具体触发条件仍待核实'
    if c.startswith(('只复用已完成','缓存缺ID','对应Boss','仅ordinary','本能力装载','同上（IsEnable','接受者自身已装载')):
        return '本能力生效时；具体适用条件见本句'
    if c=='有敌门控':return '存在符合条件的敌人时'
    m = re.search(r'pattern(?:id)?(\d+)\s*/\s*pattern', c)
    if m:
        return '触发条件待核实'
    if c.startswith(('仅当前', '样本域', '以Boss', 'Boss type', '仅普通', '仅430')):
        return ''
    if c.startswith('仅回答停止'):
        return '停止不动时逐档增强；移动后复位。每档需要多久尚未确认'
    if c.startswith('战斗开始时 /'):
        return '战斗开始时'
    if '有正文 pattern' in c:return '各已列出的档位共用这项持续时间'
    if c.startswith('选中普通档'):return '普通必杀档生效时；实际开放状态待核实'
    if c.startswith('选中超共鸣档'):return '超共鸣必杀档生效时；实际开放状态待核实'
    if c.startswith('一次update'):return '每次状态更新最多触发一次'
    # Keep later gameplay restrictions (backline applicability, once per Chain,
    # exclusions). A semicolon is not a boundary between prose and research.
    clauses=[]
    for part in c.split('；'):
        if re.search(r'param|pattern|skillid|\b(?:CACHE|APK|Boss|type|ability|flag|OnAction|Support|ClockUp|update)\b|代码链|资格细节|候选|本批|规则|原生|载体|逐ID',part,re.I):continue
        if part.strip():clauses.append(part)
    c='；'.join(clauses)
    c = re.sub(r'选中普通档.*并执行该效果', '普通档生效时', c)
    c = re.sub(r'选中沙漠档.*并执行该效果', '沙漠档生效时', c)
    c = c.replace('战场味方', '战场上的我方').replace('Leader资格', '队长条件').replace('一次update至多一次', '每次状态更新最多触发一次')
    c = c.replace('（原文）','').replace('原文', '').replace('配置已安装且资格满足时', '满足发动条件时')
    c=c.replace('味方','我方').replace('Leader','队长能力').replace('砂漠','沙漠')
    c = c.replace('Extra附加入口，实例开放另论', '额外能力生效时')
    if any(w in c for w in ('OnAction', 'Support', 'ClockUp', 'param', 'CACHE', 'type', '载体', '候选名单')):
        return '适用条件见技能描述；细节可展开查看'
    return c.strip(' /；，')

def _readable_value(a, cid=None, original=''):
    k, v, r = a.get('quantity_kind', ''), str(a.get('value', '')), a.get('raw_value')
    rule = a.get('rule_key') or ''
    note = ''
    from literal_presentation import literal_value
    literal=literal_value(a,original)
    if literal:return literal
    if rule.startswith('bossskill|') and ('伤害输入倍率' in k or k in ('技能基值倍率','单次伤害的技能基值倍率','单次前方攻击的技能基值倍率')) and isinstance(r, (int, float)):
        return f'伤害系数 {num(r)}倍', '以已含Chain修正的技能伤害基值计算，不等于面板ATK或最终扣血'
    if rule.startswith('skilllist|96|'):
        # raw_value is a per-mana contribution here, not a total multiplier.
        cap = re.search(r'min\([^,，]+[,，]\s*(\d+)\)', v)
        if not cap:return '换算说明待整理', ''
        slot = rule.rsplit('/',1)[-1]
        label = {'param2':'非必杀攻击力','param3':'必杀攻击力','param4':'移动速度','param5':'受到的伤害','param6':'暴击率','param7':'暴击威力'}.get(slot)
        if not label:return '换算说明待整理', ''
        resource = '斯库拉普法珠' if '斯库拉普' in v else '符合条件的法珠'
        if slot == 'param7': amount=change(label,r,'（系数）')
        elif slot == 'param6': amount=change(label,r*100,' 个百分点')
        else: amount=change(label,r*100)
        return f'每颗{resource}：{amount}，最多计入{cap[1]}颗', '按当前持有数量计算；适用法珠条件见技能描述'
    if rule.startswith('skilllist|67|') and '连乘' in v:
        tiers = re.findall(r'(\d+)人\s*[×x]\s*([\d.]+)',v)
        if not tiers:return '换算说明待整理', ''
        label={'param1':'攻击力','param2':'移动速度','param3':'受到的伤害'}.get(rule.rsplit('/',1)[-1])
        if not label:return '换算说明待整理', ''
        return label+'：'+'；'.join(f'{n}名符合条件的角色 ×{factor}' for n,factor in tiers), '各人数档位分别列出，按同类规则连乘'
    if rule.startswith('skilllist|67|') and '逐条累加' in v:
        slot=rule.rsplit('/',1)[-1]
        tiers=re.findall(r'(\d+)人\s*([+-][\d.]+)(pp)?',v)
        if slot not in ('param6','param7') or not tiers:return '换算说明待整理',''
        label='暴击率' if slot=='param6' else '暴击威力系数'
        suffix=' 个百分点' if slot=='param6' else ''
        return label+'：'+'；'.join(f'{n}名符合条件的角色 {amount}{suffix}' for n,amount,_ in tiers),'按符合条件的人数取对应一档，不把各档再相加'
    if re.match(r'skilllist\|(?:99|2003)\|',rule):
        slot=rule.rsplit('/',1)[-1]
        label={'param7':'受击目标攻击力','param8':'受击目标移动速度','param9':'受击目标受到的伤害'}.get(slot)
        if label:return change(label,r*100), '本项与同类增幅相加，不乘Chain修正'
    if rule.startswith('skilllist|21|'):
        if k=='暴击回复比例':return f'回复量为本次伤害处理结果的 {num(r*100)}%', '按整数计算，向下取整'
        if k=='暴击回复HP上限档位':
            limit=re.search(r'上限\s*([\d.]+)\s*[×x]\s*最大HP',v)
            if limit:return f'最多回复至最大生命值的{num(float(limit[1])*100)}%', '原本更高的生命值不会因本次回复降低'
    if rule.startswith('skilllist|28|'):
        fields=(a.get('binding') or {}).get('fields') or []
        labels={'0':'通常攻击（推测）','2':'暴击（推测）','1':'必杀技','0/1':'通常攻击／必杀技（推测）'}
        parts=[]
        for field in fields:
            if not str(field.get('rule_key','')).startswith('skilllist|28|') or field.get('damage_type') not in labels:continue
            raw=field.get('raw')
            if not isinstance(raw,(int,float)):continue
            amount=f'+{num(raw*100)}个百分点' if '地形附加' in k else f'{num(raw*100)}%'
            parts.append(labels[field['damage_type']]+' '+amount)
        if parts:
            if '地形附加' in k:return '地形满足时获珠判定值：'+'；'.join(parts),'在基础判定值上增加；地形对应仍为推断'
            return '击倒获珠判定值：'+'；'.join(parts),'按攻击方式分别判定；这是各档数值，不是提升幅度。0%仍保留随机值相等时的边界'
        if '地形附加' in k:return change('本项击倒获珠阈值',r*100,' 个百分点'), '仅地形条件满足时附加；各攻击方式分别判定，不是额外获得概率'
        return f'本项击倒获珠判定阈值 {num(r*100)}%', '各攻击方式分别判定，完整阈值及适用方式见来源；阈值0也保留相等时的判定边界'
    if rule.startswith('bossskill|') and k in ('技能基值倍率(回复)','单次回复量的技能基值系数','回复量输入（reactive heal 基值）','技能基值输入（消费点未定）'):
        label='回复输入系数' if '消费点未定' not in k else '技能输入系数（用途待确认）'
        return f'{label} {num(r)}倍', '以技能计算基值为基础；不代表最终生命回复量'
    if k=='激光段启用上限（含首段）' and rule.startswith('bossskill|55|'):
        return f'最多启用{int(r)}段激光（含首段）', '启用上限，不保证全部命中'
    if k=='激光段生成调度阈值' and rule.startswith('bossskill|55|'):
        return f'激光分段启用的计时阈值 {num(r)} 秒', '每次固定更新最多启用一段，不等于实际命中间隔'
    if k=='Boss攻击间隔因子加算增量':
        return change('攻击间隔',r*100), '仅此项单独生效时；实际叠加结果与结束时机仍待确认'
    if k in ('通常回復間隔乘數（時間倍率）','攻击间隔乘数') and rule:
        label='普通回复间隔' if '回復' in k else '攻击间隔'
        return f'{label} ×{num(r)}', '仅此项生效时的间隔因子；不代表最终动作周期'
    if rule.startswith('bossskill|13|'):
        slot = rule.rsplit('/', 1)[-1]
        if slot in ('skillparam1', 'skillparam6'):
            label = '攻击力' if slot == 'skillparam1' else '移动速度'
            return change(label,r*100)+' × 连携修正', '显示本项增幅；还会受连携修正影响'
        if slot == 'skillparam2':
            return f'固定防御：接受者的攻击计算基值 ×{num(r)} × 连携修正', '减少固定伤害量，并非百分比减伤；攻击计算基值的定义见来源'
        if slot == 'skillparam3':
            return f'持续 {num(r)} 秒', '按游戏内时间计时'
    if rule == 'skilllist|1016|/param6':
        tiers = re.findall(r'第\d+档[：:]\s*([\d.]+)倍', v)
        return '攻击间隔依次 ×' + ' → ×'.join(tiers), '仅为停止不动带来的额外变化；移动后复位。每档所需时间及最终攻击间隔尚未确认'
    if rule == 'skilllist|2012|/param6':
        m = re.search(r'默认限幅时因子\s*([\d.]+)', v)
        return f'攻击间隔 ×{m[1] if m else num(1+r)}', '其他同类加速不生效时；不是最终攻击动作周期'
    if rule and k in ('持续时间',):
        return f'持续 {num(r)} 秒', '按游戏内时间计时'
    if rule and k == '每目标尝试预算':
        return f'每个目标最多尝试 {num(r)} 次攻击', '攻击次数上限，不保证每次命中'
    if rule and k == '连击调度重置值':
        return f'连击等待设定 {num(r)} 秒', '这是连续攻击的等待设定，实际命中间隔仍未确认'
    if rule.startswith('skilllist|26|'):
        slot=rule.rsplit('/',1)[-1]
        if '全ての必殺技が使える' in v:label='可用于所有必杀技的法珠'
        elif slot=='param7': label='万象法珠'
        elif slot=='param0': label='自身职业的法珠'
        elif slot=='param4' and ('全职业' in v or '所有职业' in v or re.search(r'iParam1\s*=\s*31\b',v)):
            label='全职业万能法珠'
        else: label='指定职业的法珠'
        return f'开局获得 {num(r)} 颗{label}', ''
    if rule and k in ('攻击倍率', '攻击力'):
        return change('攻击力',(r-1)*100), ''
    if rule and k in ('受伤量倍率','防御力'):
        return change('受到的伤害',(r-1)*100), ''
    if rule and k in ('移动速度乘数','移动速度'):
        return change('移动速度',(r-1)*100), ''
    if rule and k in ('暴击概率加算贡献', '暴击发生率'):
        return change('暴击率',r*100,' 个百分点'), ''
    if rule and ('暴击伤害系数' in k or k == '暴击威力'):
        m = re.search(r'系数\s*(?:\+=\s*)?([+-]?[\d.]+)', v)
        return change('暴击威力',float(m[1]) if m else r,'（系数）'), ''
    if rule.startswith('skilllist|3000|') and k == '攻击加算增量':
        label = '普通攻击' if rule.endswith('/param1') else '必杀攻击'
        return change(label+'倍率',r*100,' 个百分点'), '与同类增幅相加'
    if rule == 'skilllist|29|/param0':
        return change('必杀威力',(r-1)*100), ''
    if rule and k in ('金币获得倍率','经验值获得倍率'):
        return change(k.replace('倍率',''),(r-1)*100), ''
    if not rule and r is not None:
        unit = {'つ': '个', '回': '次', 'マナ': '颗法珠', '体': '名'}.get(a.get('unit'), a.get('unit', ''))
        if k == '所需玛那减少': return f'消耗减少 {r} 颗法珠', '日文描述直接写出的数量'
        if k == '发动费用': return f'消耗 {r} 颗法珠', '日文描述直接写出的数量'
        if k == '次数上限': return f'最多 {r} {unit}', '日文描述直接写出的数量'
        if k in ('次数', '数量', '获得数量'): return f'{r} {unit}', '日文描述直接写出的数量'
        if k == '味方全体/攻击力效果量百分比':return f'我方全体攻击力提高 {r}%', '日文描述明示'
        if k == '效果量百分比':return f'{r}%', '日文描述明示；适用效果见上方正文'
    # Older cid30236 conclusions have no rule_key. Read their explicit value,
    # never assume null raw_value means zero or apply a generic percentage rule.
    if not rule and r is None and str(cid)!='30236':
        return '换算说明待整理', ''
    if not rule and str(cid)=='30236':
        if k=='受伤量加算增量':
            m=re.search(r'减伤([\d.]+)个百分点',v)
            if m:return f'受到的伤害降低{m[1]}%（单独生效时）','与同类变化相加'
        if k=='必杀请求系数乘数（ExtraChainRate）':
            m=re.search(r'必杀威力\+([\d.]+)%',v)
            if m:return f'必杀威力提高 {m[1]}%',''
        if k=='击杀玛那基础概率':return '击倒敌人获珠判定值：通常攻击、暴击与必杀技均为20%','三种攻击方式分别判定'
        if k=='攻击加算增量' and '通常攻击/必杀攻击各' in v:
            m=re.search(r'各\+([\d.]+)%',v)
            if m:return f'普通攻击与必杀攻击倍率各增加 {m[1]} 个百分点', '与同类增幅相加'
        if k == '攻击增加比例':
            m = re.search(r'\+([\d.]+)%', v)
            if m:return f'攻击力提高 {m[1]}% × 连携修正', '显示本项增幅；还会受连携修正影响'
        if k == '技能基值倍率':
            m = re.search(r'每次([\d.]+)×', v)
            if m:return f'每次伤害计算基础值 ×{m[1]}', '基础值已含连携修正；不是最终扣血'
        if k == '固定防御量（系数已知）':
            m = re.search(r'normalAtk×([\d.]+)', v)
            if m:return f'固定防御：接受者的攻击计算基值 ×{m[1]} × 连携修正', '减少固定伤害量，并非百分比减伤'
        if k == '屏障固定防御量系数':
            return '护盾固定防御：接受者的攻击计算基值 ×2 × 技能修正', '无适用修正规则时，技能修正为1；减少固定伤害量，并非百分比减伤'
        if k == '移动因子增加量':
            m = re.search(r'1\+([\d.]+)', v)
            if m:return f'移动速度提高 {num(float(m[1])*100)}% × 技能修正', '具体修正条件见来源'
        if k == '暴击回复比例':return '回复量为本次伤害处理结果的 25%', '按整数计算，向下取整'
        if k == '普通时楔释放的停止时长输入':return '普通时之楔：停止时间增加 5 秒', '特殊加速模式为8秒；可累加到已有停止时间'
        if k == '原文条件与已核地形阈值':return '沙漠中击倒敌人时，获得法珠的概率为 100%', ''
        if k == 'Chain档位获珠概率阈值':return '每次符合条件的必杀按钮事件，有 10% 概率获得法珠', '须达到连携条件，且本轮尚未触发；同一连携内不重复获得'
        if k == 'Leader职业人数资格':return '队长条件：至少4名战士', ''
        if k == '玛那数量差':return '消耗从2颗降至1颗法珠', ''
        if k == '攻击间隔乘数':return '攻击间隔缩短25%（×0.75）', '基础间隔1.5秒且没有其他修正时，名义间隔为1.125秒'
        if k == '原文Chain威力提升量数值':
            m = re.search(r'提升量\s*([\d.]+)%', v)
            if m:return f'本档连携威力提升量 {m[1]}%', '日文描述明示'
        if k == '原文耗玛那数量':return '消耗0颗法珠', '日文描述明示'
        if k in ('原文获得数量','Chain获珠数量','原文初始数量'):return '1颗法珠', '日文描述明示或已有数量结论'
        if k == '初始数量':return '开局持有1个时之楔', ''
        if k == '原文同Chain上限':return '每次连携最多获得1颗', ''
        if k == '原文发动次数':return '同一次连携最多发动1次', ''
        if k == '原文Chain门槛':return '达到1st Chain或以上', ''
        if k == '保护次数':return '保护次数设定：10次', '完整消耗条件仍需核对'
        if k == '原文攻击次数':return '暴击连续攻击6次', '原文次数，不保证全部命中'
        if k == '位置数量':return '每段9个位置', '完整作用机制仍需核对'
        if k == '层数':return '每个位置2层', '需两段都执行并保留原有对象'
        if k == '地形变化的正持续时间':return '地形持续300秒（5分钟）', ''
        if k == '暴击回复HP上限档位':return '最多回复至最大生命值的140%', '原本更高的生命值不会因本次回复降低'
    # Remaining older answers already use readable numeric phrases.
    clean = v.split('；')[0]
    clean = re.sub(r'（(?:原文|本项|局部|请求系数|×|受伤量|对 0).*?）', '', clean)
    clean = clean.replace('游戏秒','秒').replace('暴击伤害系数', '暴击伤害倍率')
    clean = clean.replace('攻击+', '攻击力提高 ').replace('移动速度+', '移动速度提高 ')
    clean = clean.replace('敌方受伤量+', '敌人受到的伤害增加 ').replace('本项', '')
    clean = clean.replace('基础概率', '基础概率为 ').replace('普通时楔', '普通时之楔')
    return clean, note

def readable_value(a, cid=None, original=''):
    text,note=_readable_value(a,cid,original)
    # Unknown formula families stay available verbatim in source.originalAnswer.
    # Do not mistake their stored contribution for a finished effect amount.
    if not text or text=='None' or TECHNICAL.search(text):text='换算说明待整理'
    return text,note


def answer(a, cid=None, original=''):
    text, note = readable_value(a,cid,original)
    rule=a.get('rule_key') or ''
    c19 = str(a.get('evidence_scope','')).startswith(('C19_P1_1095_', 'C19_P2_TYPE8_'))
    if c19:
        text = '自身'+text
        note = '仅本句、本项单独生效时的贡献；同段其他效果与条件强化另论。' + note
    if rule.startswith('skilllist|1059|'):
        note='这是满足队伍条件时的一项加成；每增加一人会增强多少，尚未确认'
    if rule.startswith('skilllist|80|'):
        note='满足本句持珠条件时生效，不按法珠颗数重复叠加'
    detail_note=''
    if text.startswith('伤害系数 ') or TECHNICAL.search(note):note,detail_note='',note
    source = a.get('source') or {}
    first = source[0] if isinstance(source, list) and source else source
    if not isinstance(first, dict): first = {}
    return {
        'text': terms(text), 'confidence': confidence(a), 'condition': terms(condition(a)) if not TECHNICAL.search(condition(a)) else '适用条件见技能描述；细节可展开查看', 'note': terms(note), 'detailNote': terms(detail_note),
        'source': {'file': first.get('original_file'), 'pointer': first.get('json_pointer'),
                   'field': a.get('field_path'), 'raw': a.get('raw_value'), 'rule': a.get('rule_key'),
                   'originalAnswer': a.get('value'), 'originalConditions': a.get('conditions'),
                   'originalBinding': a.get('binding'), 'originalEffectBinding': a.get('effect_binding'),
                   'originalConditionLabel': a.get('condition_label'), 'limitations': a.get('note'),
                   'numericEvidence': a.get('numeric_evidence'), 'associationEvidence': a.get('association_evidence'),
                   'evidenceScope': a.get('evidence_scope'), 'allSources': source,
                   **({'playerScope':a.get('player_scope'), 'originalPlayerText':a.get('player_text'),
                       'notIncluded':a.get('not_included'), 'excludedCarrierFields':a.get('excluded_carrier_fields')} if c19 else {})},
    }
