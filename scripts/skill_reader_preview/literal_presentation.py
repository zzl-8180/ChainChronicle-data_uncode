"""Read literal Japanese quantities without pretending they are decoded fields."""
import re
import unicodedata

NOUNS={'1st角色':'1号位角色','味方全体':'我方全体','戦場にいる味方':'战场上的我方',
 'メインパーティの':'主要队伍中的','ケ者の大陸':'兽者之里','奈落の世界':'奈落世界',
 '年代記の大陸':'年代记大陆','幻獣の世界':'幻兽世界','幽夜の世界':'幽夜世界','時空軍':'时空军',
 '潜艦の世界':'潜艇世界','神仙の世界':'神仙世界','精霊島':'精灵岛','罪の大陸':'罪之大陆',
 '聖都':'圣都','薄命の大陸':'薄命大陆','謀略の世界':'谋略世界','賢者の塔':'贤者之塔',
 '迷宮山脈':'迷宫山脉','遊戯の世界':'游戏世界','鉄煙の大陸':'铁烟大陆','ifの世界':'if世界',
 '九領':'九领','味方':'我方','暴击发生率':'暴击率','回复量':'回复量','玛那':'法珠','人间':'人类'}

def noun(text):
    text=unicodedata.normalize('NFKC',text)
    for a,b in NOUNS.items():text=text.replace(a,b)
    return text.replace('/',' · ').replace('<','〈').replace('>','〉')

def literal_value(a,original=''):
    if a.get('rule_key') or a.get('numeric_source')!='原文' or a.get('raw_value') is None:return None
    k=a.get('quantity_kind','');r=unicodedata.normalize('NFKC',str(a['raw_value']))
    context=unicodedata.normalize('NFKC',str(a.get('context') or ''))
    note='原文明示；适用对象与条件见本句'
    if k.endswith('效果量百分比'):
        label=noun(k[:-len('效果量百分比')]).strip(' ·') or '效果幅度'
        after=re.search(re.escape(r)+r'%(?:ずつ)?(?:一定時間)?(上が|上げ|増加|増え|上昇|下が|下げ|減少)',context)
        direction=('提高' if after[1] in ('上が','上げ','増加','増え','上昇') else '降低') if after else '原文幅度'
        if not after and original and re.search(r'が'+re.escape(r)+r'%$',context):
            # Coordinated attributes share the final verb: 攻撃力が25%、防御力が25%、
            # 移動速度が25%一定時間下がる. Do not borrow a conflicting verb.
            jp=unicodedata.normalize('NFKC',original)
            verbs=set(re.findall(r'(上が|下が)',jp))
            if len(verbs)==1:direction='提高' if '上が' in verbs else '降低'
        if '貫通するたびに' in context and '威力を増す' in context:
            return f'每次贯穿后威力提高 {r}%',note
        if 'ずつ' in context and after:direction='每次'+direction
        if '基数:' in label:direction=''
        if '回复量' in label and not after:direction=''
        if '与えたダメージの' in context:return f'回复量为造成伤害的 {r}%',note
        if k in ('效果量百分比','味方全体/效果量百分比','戦場にいる味方/效果量百分比','自身/效果量百分比'):
            if 'Chainによる威力の上昇量' in context:label='下次必杀的Chain威力提升量'
            elif '遠距離通常攻撃の威力' in context:label='我方全体的远距离通常攻击威力'
            elif '最大HP' in context:label='战场上我方的最大HP'
            elif 'ダメージを受け' in context:return f'自身受到 {r}% 的伤害（计算基数见本句）',note
        return f'{label}{direction} {r}%',note
    if k.endswith('效果固定量'):
        target=noun(k[:-len('效果固定量')]).strip(' ·')
        if 'HPが' in context:
            m=re.search('HPが'+re.escape(r)+r'(上が|下が)',context)
            change=('提高' if m[1]=='上が' else '降低') if m else '原文数值'
            return f'{target+"：" if target else ""}生命值{change} {r}',note
    unit={'つ':'个','個':'个','人':'名','体':'个','回':'次','本':'个','羽':'只','発':'发','マナ':'颗法珠','秒':'秒','秒間':'秒','WAVE':'WAVE'}.get(a.get('unit'),a.get('unit',''))
    if a.get('unit')=='体' and re.search(r'敵'+re.escape(r)+'体',context):unit='名'
    if k in ('所需玛那减少','发动费用'):unit='颗法珠'
    if unit=='个' and re.search(r'マナ(?:を|が|も)?'+re.escape(r)+r'(?:つ|個)',context):unit='颗法珠'
    if unit=='个' and '超必殺技ゲージ' in context:unit='条超必杀技量表'
    if k.endswith('回复量'):return f'{noun(k)}：{r} HP',note
    if k=='叙述数字':return f'背景描述中的数字：{r}{unit}（不是技能效果量）',note
    if k=='人数上限':return f'最多按 {r} 人计算',note
    if k=='受击次数上限':return f'各对象受到 {r} 次伤害后结束',note
    if k=='受击触发次数':return f'每受到 {r} 次攻击伤害触发',note
    if k=='耐久次数':return f'可抵挡 {r} 次致命事件',note
    if k in ('时长','时间间隔'):return f'{"持续" if k=="时长" else "间隔"} {r} {unit}',note
    if k=='费用下限' and 'ならない' in context:return f'消耗不会降至 {r} 颗法珠',note
    if k in ('HP条件阈值','条件阈值'):
        if re.search(r'マナを1つも所持していない',context):return '不持有任何法珠时',note
        m=re.search(re.escape(r)+r'(?:%|個|つ|回|人|体|本|マナ)?(以上|以下|未満|より多|の場合)',context)
        bound={'以上':'至少','以下':'至多','未満':'低于','より多':'高于','の場合':'等于'}.get(m[1],'') if m else ''
        return f'{"HP条件" if k=="HP条件阈值" else "触发条件数值"}：{bound}{r} {unit}',note
    if k=='数量上限':return f'数量上限 {r} {unit}',note
    if k in ('数量','次数','获得数量','次数上限','发动费用','所需玛那减少'):
        label={'数量':'数量','次数':'次数','获得数量':'获得','次数上限':'最多','发动费用':'消耗','所需玛那减少':'消耗减少'}[k]
        return f'{label} {r} {unit}',note
    return None
