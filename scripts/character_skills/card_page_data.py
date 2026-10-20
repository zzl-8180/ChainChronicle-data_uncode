"""Conservative sample-page data projection over existing unpacked artifacts."""
from __future__ import annotations
import collections
import copy
import hashlib
import json
import math
import os
import re
import unicodedata
from pathlib import Path

import common as C
import rules as R
from card_page_policy import metrics,INFERENCE_STATUS
from card_page_basic import apply_basic_display
from card_page_positions import fragment_positions,position_identity

SAMPLES = (30236,7229,29,2020,5023,4009,8151,30004,10001,13001,30338)
GROUPS = [('special_move','必杀技'),('ability','能力'),('sa','SA'),('sympathy','共鸣'),
          ('leader','Leader'),('class','Class'),('extra','Extra'),('passive','PASSIVE'),
          ('bond','羁绊'),('heroic','英雄技'),('denju','传授'),('crossworld','CrossWorld'),('slot0','必杀效果类型')]
TEXT = {'charainfo':('skilltext','skillname'),'bosspattern':('sinfo','sname'),
        'denju':('stext','sname'),'denju_limit_break_info':('stext','sname')}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def lines(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line in stream:
            yield json.loads(line)


def clean(text):
    return str(text or '').replace('\\n','\n')


def fragments(text):
    """Sentence units preserve repeated occurrences and all skill prose; flavor stays separate."""
    text=clean(text)
    cut=text.find('[i][c]')
    body=text[:cut] if cut>=0 else text
    return [s.strip(' ◆\r\t') for s in re.split(r'(?<=。)|\n|◆',body) if s.strip(' ◆\r\t')]


def canonical(text):
    return clean(text).strip().rstrip('。').strip()


def raw_state(rec, key):
    return 'missing' if key not in rec else 'null' if rec[key] is None else 'zero' if rec[key]==0 else 'present'


# NUMBER 的双重 lookbehind：排除整数相邻与小数位（“1.5”不得再匹配“5”）；
# 但允许省略号（NFKC 归一为“...”）后的数字（L-11：8424「…3つの効果」此前被误当作小数位跳过）。
NUMBER = r'(?<!\d)(?<!\d\.)(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
UNIT_CLASS = r'%|秒間|秒|回|発|つ|個|枚|体|匹|倍|人|マナ|羽|台|本'
NUM_UNITS = re.compile('('+NUMBER+r')\s*('+UNIT_CLASS+r')(?![a-zA-Z])')
UNIT_DISPLAY = {'秒間':'秒'}  # 显示单位统一；unit_raw 保留原文后缀（G-08/G-09）
SENTENCE_DELIMS = ('。','、','，','\n','◆')


def _raw_map(text):
    """Per-character NFKC with a normalized→raw index map, so literal/context stay verbatim (G-09)."""
    parts=[];index=[]
    for i,ch in enumerate(text):
        for nch in unicodedata.normalize('NFKC',ch):
            parts.append(nch);index.append(i)
    return ''.join(parts),index


def _raw_slice(text,index,start,end):
    if not index or start>=len(index): return text,min(start,len(text)),min(end,len(text))
    rs=index[start]
    re_=index[end-1]+1 if end>start else rs
    return text[rs:re_],rs,re_


def _context(text,start,end,span=40):
    """Evidence context aligned to sentence/clause delimiters; never cuts a number or word (G-06/G-13)."""
    lo=max(0,start-span);hi=min(len(text),end+span)
    s=lo;e=hi
    for d in SENTENCE_DELIMS:
        p=text.rfind(d,lo,start)
        if p>=0 and p+1>s:s=p+1
        p=text.find(d,end,hi)
        if p>=0 and p<e:e=p
    return text[s:e],[s,e]


def original_numbers(text):
    """Extract only explicit quantities; ordinal 1st/IDs/level names do not qualify.
    literal/context are verbatim raw text; normalized_literal/value follow NFKC (G-09)."""
    normalized,index=_raw_map(text)
    out=[]
    def item(value,unit,role,ms,me,display,qualifier=None,unit_raw=None):
        raw_literal,rs,re_=_raw_slice(text,index,ms,me)
        normalized_literal=normalized[ms:me]
        context,cspan=_context(text,rs,re_)
        entry=dict(value=value,unit=unit,role=role,literal=raw_literal,normalized_literal=normalized_literal,
                   display=display,raw_span=[rs,re_],normalized_span=[ms,me],context=context,context_span=cspan)
        if qualifier: entry['qualifier']=qualifier
        if unit_raw and unit_raw!=unit:
            entry['unit_raw']=unit_raw
            # N-01（DeepSeek 20to39复验）：「回」是「回復」的首字，不是次数单位/量词；措辞修正，值与标签不变。
            entry['display_note']=('原文单位后缀「'+unit_raw+'」；本页时长单位显示统一为“秒”，literal保留原文' if unit_raw=='秒間' else
                                   '原文后缀「回」是「回復」的首字（不是次数单位），本项为HP回复量，literal保留原文' if unit=='HP' else
                                   '显示单位与原文单位后缀不同，literal保留原文')
        if normalized_literal!=raw_literal:
            entry['normalization_note']='literal为逐字原文；normalized_literal/display为NFKC归一化，值不变'
        out.append(entry)
    # “N～M回”等范围：保持为单一范围值项，不再拆成两个独立次数（L-13；DeepSeek 20to39审查）。
    # NFKC 把全角“～”归一为“~”；波浪省略号“〜”保持原形，两者都识别。
    # N-02（DeepSeek 20to39复验）：literal/raw_span 取完整范围 token（含第二个单位后缀，如「1回～6回」），
    # 不再截断为「1回～6」；raw_value 仍为字符串范围，显示值不变。前后单位必须一致才按范围合并。
    range_spans=[]
    for match in re.finditer(r'('+NUMBER+r')('+UNIT_CLASS+r')[~〜]('+NUMBER+r')('+UNIT_CLASS+r')(?![a-zA-Z])',normalized):
        if match.group(4)!=match.group(2):continue
        n1,n2,unit=match.group(1),match.group(3),match.group(2)
        role={'回':'次数','発':'次数','%':'效果量百分比','秒':'时长','秒間':'时长'}.get(unit,'数量')
        unit_raw=unit;unit=UNIT_DISPLAY.get(unit,unit)
        range_spans.append((match.start(),match.end()))
        item(n1+'～'+n2,unit,role,match.start(1),match.end(4),n1+'～'+n2+unit+'（范围）',unit_raw=unit_raw)
    for match in NUM_UNITS.finditer(normalized):
        if any(s<=match.start() and match.end()<=e for s,e in range_spans):continue
        value,unit=match.group(1),match.group(2)
        left=normalized[max(0,match.start()-14):match.start()]
        right=normalized[match.end():match.end()+14]
        role=('条件阈值' if re.match(r'(以上|以下|未満|を超え)',right) else
              '时长' if unit.startswith('秒') else '次数' if unit in ('回','発') else
              '效果量百分比' if unit=='%' else '倍数' if unit=='倍' else '数量')
        if right.startswith('まで') and unit in ('回','発','人','体','羽','台','本'):
            role=('人数上限' if unit=='人' else '次数上限' if unit in ('回','発') else '数量上限')
        # “N回ダメージを受けるまで”是受击耐久上限，不是攻击次数（G-03）。
        if unit=='回' and re.match(r'ダメージを受けるまで',right):role='受击次数上限'
        # RM-03（DeepSeek remaining审查）：「N秒先/秒後」是叙述性时间（视界/时点），不是效果持续时间。
        if unit.startswith('秒') and re.match(r'(?:先|後)',right):role='叙述数字'
        if unit=='%' and re.search(r'HP(?:が|の)?$',left) and re.match(r'(以上|以下|未満|より)',right):
            role='HP条件阈值'
        # RM-01（DeepSeek remaining审查）：「(残り)HPが N% の時/の場合/ならば/だと」限定的是HP条件
        # 而非效果量（如「HPが100%の時、攻撃力が上がる」），同标HP条件阈值。
        elif unit=='%' and role=='效果量百分比' and re.search(r'(?:残り)?HPが$',left) \
                and re.match(r'(の時|のとき|の場合|ならば|なら|だと)',right):
            role='HP条件阈值'
        # 承前省略主语的「N%の時/の場合/ならば/だと」（如7581「残りHPが50％以上の場合、…、100％の場合」
        # 的第二个数）：同句前文已有「(残り)HPが N%（以上等）（時/場合等）」条件锚点时同标。
        elif unit=='%' and role=='效果量百分比' and re.match(r'(の時|のとき|の場合|ならば|なら|だと)',right):
            head=normalized[sentence_start(normalized,match.start()):match.start()]
            if re.search(r'(?:残り)?HPが'+NUMBER+r'%(?:以上|以下|未満|より)?(?:の時|のとき|の場合|ならば|なら|だと)',head):
                role='HP条件阈值'
        # “0マナで発動”是发动费用，不是获得数量（G-04）。
        if unit=='マナ' and re.match(r'で発動',right):role='发动费用'
        # “この効果で0マナにはならない”是否定表述：费用下限，不是数量（R-04；R2审查）。
        if unit=='マナ' and re.match(r'にはならない',right):role='费用下限'
        # “Nつ獲得”是获得数量（G-04）。
        if unit in ('つ','個') and re.match(r'獲得',right):role='获得数量'
        # “必要なマナがNつ減る”是所需玛那减少量，不是获得（G-05）。
        # L-08（DeepSeek 20to39/remaining审查，终版polish）：「(必要な)マナ(の数|数)が/を」同样逐字
        # 写在同分句内（12004/2003/2042/5098/8106/8146 等「マナ数がNつ減る」变体，原14字符窗口未覆盖），
        # 按同法标所需玛那减少；这是同句逐字依据，不是跨片段推断。
        reduce_note=None
        if unit=='つ' and re.search(r'(?:必要な)?マナ(?:の数|数)?[がを]$',left) and re.match(r'減',right):
            role='所需玛那减少'
        # 「2ndChainを達成した時、さらに1つ減る」承接前片段的マナ语义，片段内无逐字对象：
        # 不跨片段推断，标签保持数量，值行注记指向同技能前文（L-08保留口径）。
        elif unit=='つ' and re.match(r'減',right):
            reduce_note='减少对象见同技能前文（片段内无逐字依据）'
        # “N回復”是HP固定回复量，不是次数（M-01；DeepSeek 20to39审查）；“N回復活/復帰”仍是次数。
        heal_fixed=False
        if unit=='回' and re.match(r'復(?!活|帰)',right):heal_fixed=True;role='回复量'
        # “戦闘不能になった際にN回耐え”是耐久次数（L-08；DeepSeek 20to39审查）。
        elif unit=='回' and re.match(r'耐え',right):role='耐久次数'
        # “N回受けるまで”是受击次数上限（G-03 同族），“N回受けると/たび”是受击触发次数（L-08）。
        elif unit=='回' and re.match(r'受け(?!止|身)',right):
            role='受击次数上限' if re.match(r'受け(?:る)?まで',right) else '受击触发次数'
        if unit=='%' and role=='效果量百分比' and match.start()==0:
            # RM-05（DeepSeek remaining审查）：片段开头即「N%」、后接叙述性文本（5037
            # 「１００％あーしの葡萄酒…」）是叙述性数字，不是效果量；与8022「N秒先」同法。
            # 全库段首%（无任何前文）的行实测仅此1行，其他段首数字均为条件/固定量等既有角色。
            role='叙述数字'
        elif unit=='%' and role=='效果量百分比':
            # “N%回復”／“与えたダメージのN%、HPが回復”是回复量百分比（M-05；DeepSeek 20to39审查）。
            if re.match(r'回復',right):role='回复量效果量百分比'
            elif re.search(r'与えたダメージ(?:量)?の$',left) and re.match(r'[、,]?[^、。]{0,10}?HPが回復',right):
                role='回复量效果量百分比'
            # “(自身/敵)の最大HP N%のダメージ”是对敌伤害及其基数，不是自身增益（M-04）。
            # RM-02（DeepSeek remaining审查）：扩展到省略领属的「最大HP N%のダメージ」
            # （与える→对敌、受ける→自身）、「(自身/自分)も最大HP N%のダメージを受ける」自伤、
            # 「N％ダメージを受ける」无の变体及「炎属性ダメージ」类；基数按 left 窗口逐字判定，数值不变。
            maxhp=re.search(r'(?:(自身|自分|敵)(?:も)?の?)?最大[ＨH][ＰP]の?$',left)
            if maxhp and re.match(r'の?(?:[炎氷闇光]属性)?ダメージ',right):
                who=maxhp.group(1)
                take=bool(re.match(r'の?(?:[炎氷闇光]属性)?ダメージ(?:を)?受け',right))
                if who in ('自身','自分'):
                    role='自身受到伤害（基数：自身最大HP）效果量百分比' if take else '对敌伤害（基数：自身最大HP）效果量百分比'
                elif who=='敵':role='对敌伤害（基数：敌方最大HP）效果量百分比'
                else:
                    role='自身受到伤害（基数：最大HP）效果量百分比' if take else '对敌伤害（基数：最大HP）效果量百分比'
        # “マナを1つも所持していない”是否定条件（未持有玛那），不是持有1个（R-05；R2审查）。
        negated=False
        if unit=='つ' and re.search(r'マナを$',left) and re.match(r'も所持していない',right):
            role='条件阈值';negated=True
        unit_raw=unit;unit=UNIT_DISPLAY.get(unit,unit)
        if heal_fixed:unit='HP'
        display=value+unit
        # “3つの効果のうちランダムで1つ”的“3つ”是随机效果数，不是效果量（L-11）。
        if unit=='つ' and re.search(r'の効果のうち',right):display+='（随机效果数，非效果量）'
        if role=='叙述数字':display+='（叙述性时间，非效果时长）' if unit.startswith('秒') else '（叙述性数字，非效果量）'
        if role=='费用下限':display+='（不会降至0マナ）'
        elif negated:display+='（未持有玛那）'
        item(value,unit,role,match.start(),match.end(),display,unit_raw=unit_raw)
        if reduce_note:out[-1]['reduce_note']=reduce_note
    # “所持できるマナの数がNに増えた”：可持有玛那上限，原文无单位后缀（G-02）。
    for match in re.finditer(r'所持できるマナの数が('+NUMBER+r')に増え',normalized):
        if any(a['normalized_span'][0]<=match.start(1)<a['normalized_span'][1] for a in out): continue
        item(match.group(1),'マナ','数量',match.start(1),match.end(1),match.group(1)+'（可持有玛那上限）',
             qualifier='可持有玛那上限')
    # Fixed HP/ATK amounts often have no unit suffix (HPが1000上がり).
    for match in re.finditer(r'(HP|ATK)(?:が|を|の)?('+NUMBER+r')(?=上|増|回復|減)',normalized):
        if any(a['normalized_span'][0]<=match.start(2)<a['normalized_span'][1] for a in out): continue
        unit=match.group(1)+'原文固定量'
        item(match.group(2),unit,'效果固定量',match.start(),match.end(),match.group(1)+'が'+match.group(2))
    # “ダメージをN減少させる”：防御無視攻撃等伤害的固定减少量，原文无单位后缀（R-02；R2审查）。
    # 值行显示用纯中文标签＋数值，不再夹整句日文（L-05）；原文短语见 literal/context。
    for match in re.finditer(r'ダメージを('+NUMBER+r')減少',normalized):
        if any(a['normalized_span'][0]<=match.start(1)<a['normalized_span'][1] for a in out): continue
        item(match.group(1),'ダメージ固定量','固定减少量',match.start(1),match.end(1),match.group(1))
    # “1000ダメージ”等直接接在数字后的固定伤害量（RM-04；DeepSeek remaining审查，
    # 6215「呪い付与_5回1000ダメージ」，正文「呪いは5回までの追加固定ダメージを与える」佐证）。
    # 与「ダメージをN減少」同法：单位以角色名表达，值行不夹日文（L-05）。
    for match in re.finditer(r'('+NUMBER+r')ダメージ',normalized):
        if any(a['normalized_span'][0]<=match.start(1)<a['normalized_span'][1] for a in out): continue
        item(match.group(1),'ダメージ固定量','固定伤害量',match.start(1),match.end(1),match.group(1))
    out.sort(key=lambda a:(a['normalized_span'][0],a['normalized_span'][1]))
    return out


# 多值行的“效果量百分比”按同分句前文补属性/对象；仅当一行内有≥2个百分数时启用（G-07）。
# R-06：具体短语（如「味方の必殺技の威力」）排在泛化短语（「必殺技の威力」）之前并遮蔽之；
# 「天魔/状態異常の敵/遠距離通常攻撃/経験値/ゴールド」为同句逐字短语补全（R2审查 R-06）。
ATTR_KEYWORDS=(('味方の必殺技の威力','味方必杀技威力'),('必殺技の威力','必杀技威力'),('クリティカル発生率','暴击发生率'),('クリティカル威力','暴击威力'),
               ('人間に与えるダメージ','对人间伤害'),('天魔に与えるダメージ','对天魔伤害'),('状態異常の敵に与えるダメージ','对异常状态敌人伤害'),
               ('遠距離通常攻撃のダメージ','远程通常攻击伤害'),('経験値','经验值'),('ゴールド','金币'),
               ('移動速度','移动速度'),('攻撃力','攻击力'),('防御力','防御力'),
               ('回復量','回复量'),('与ダメージ','造成伤害'))
ATTR_TARGETS=(('1stキャラクター','1st角色'),('1stキャラ','1st角色'),('味方全体','味方全体'),('自身','自身'),('敵','敌方'))
# R-03（R2审查）：下述条件短语中的「敵」是条件/受击对象的一部分，不是效果对象；
# 在对象搜索前遮蔽，同时经 CONDITION_PATTERNS 登记为同句条件标签。
# R-03（R2审查）：下述条件短语中的「敵」是条件/受击对象的一部分，不是效果对象；
# 在对象搜索前遮蔽，同时经 CONDITION_PATTERNS 登记为同句条件标签。
# 「敵陣の奥に行く程」「状態異常の敵がいると」同类（M-02/M-03B；DeepSeek 20to39审查）。
CONDITION_EXCLUDES=('敵陣にいると','同じ敵を攻撃すると','敵陣の奥に行く程','状態異常の敵がいると')


def attribute_role(text,pos,window_start=None):
    start=0
    for d in SENTENCE_DELIMS:
        p=text.rfind(d,0,pos)
        if p>=0 and p+1>start:start=p+1
    # R-06：多值行各数值只看自己与前一个数字之间的前文，避免同标签重复粘贴到每个数值。
    if window_start is not None and window_start>start:start=window_start
    clause=text[start:pos]
    if not clause:return None
    # R-03：条件短语中的「敵」不是效果对象，搜索前遮蔽（遮蔽用等长占位，不改字序）。
    clause=mask_conditions(clause)
    attrs=[];matched=[]
    for pat,label in ATTR_KEYWORDS:
        # 具体短语命中后遮蔽其包含的泛化短语（如「味方の必殺技の威力」遮蔽「必殺技の威力」）。
        if pat in clause and label not in attrs and not any(pat in m for m in matched):
            attrs.append(label);matched.append(pat)
    targets=[]
    for pat,label in ATTR_TARGETS:
        # 对象短语若只是已命中的属性短语的一部分（如「状態異常の敵に与えるダメージ」中的「敵」），不再单列对象。
        if pat in clause and label not in targets and not any(pat in m for m in matched):
            targets.append(label)
    if not attrs:return None
    return '/'.join(targets+attrs) if targets else '/'.join(attrs)


# R-01：条件/所属/目标标签。仅当同句原文逐字写出下列短语、且短语出现在数字之前时才附加；
# 目标取数字之前最近的主体短语，其他主体（味方全体/自身/敵/1stキャラ）就近覆盖，
# 不跨句推断、不补“自身”这类日文默认省略的对象；无据行保持原样。
SENTENCE_BREAKS=('。','\n','◆')
# L-04（终版polish；DeepSeek 20to39/40to59/ge60/remaining审查）：多值行重复标签（同一行内同一
# 数量/次数类角色≥2个数值）的逐值就近对象标注。仅当数值在同一分句（R-06窗口）内紧邻逐字对象
# 短语时，以括注原样引用；无逐字依据的行保持原样并另行计数，不跨句、不翻译、不按位置猜测对象。
L04_COUNT_ROLES=('数量','次数','获得数量')
L04_DELIMS=re.compile(r'[、。・【】（）「」『』〈〉／/！？!?…\n◆ 　]+')
L04_PARTICLES='をがのにへとはでも'
L04_NOUN_ENDS=('敵','味方','自身','マナ')


def l04_object(text,window_start,num_start):
    """同一分句内紧邻数值之前的逐字原文（截到最后一个句读分隔符，去掉一个尾随助词）。
    就近依据收紧为两种形态：「名詞＋を/が＋数值」（被数名词直接受を/が支配）或
    「敵/味方/自身/マナ＋数值」（对象名词紧邻数值）；纯承接/上限词（最大/さらに）、
    以助词开头的跨数值残留尾巴、时间副词（効果時間中に）与接续语（自身に対して）等
    无对象名词收尾的情况一律视为无逐字依据，返回None并保持原样。
    L-04微修（20261020终版复验）：对象名词收尾的尾巴不得跨入以「を」结尾的前一修饰链——
    该「を」是前一分句的对象而非被数名词的修饰，故截到最后一个「を」之后，只保留紧邻
    数值的最小名词短语（如「…宝石を自身から最も遠い味方」→「自身から最も遠い味方」）。"""
    window=text[window_start:num_start]
    tail=L04_DELIMS.split(window)[-1] if window else ''
    if not tail or tail in ('最大','さらに'):return None
    phrase=tail[:-1] if tail[-1] in L04_PARTICLES else tail
    if tail[-1] not in 'をが' and tail[-1] not in L04_PARTICLES:
        # 对象名词收尾：括注不得跨入以「を」结尾的前一修饰链——该「を」是前一
        # 分句的对象标记，不是被数名词的修饰，故截到最后一个「を」之后取最小名词短语。
        cut=tail.rfind('を')
        phrase=tail[cut+1:] if cut>=0 else tail
    if not phrase or phrase in ('最大','さらに') or phrase[0] in L04_PARTICLES:return None
    if not (tail[-1] in 'をが' or phrase.endswith(L04_NOUN_ENDS)):return None
    return phrase
# M-01/M-05：HP回复量（固定/百分比）同样参与同句对象/所属/条件标注。
TARGET_SENTENCE_ROLES={'效果量百分比','效果固定量','倍数','回复量','回复量效果量百分比'}
CONDITION_SENTENCE_ROLES=TARGET_SENTENCE_ROLES|{'所需玛那减少','发动费用','获得数量','数量'}
TARGET_SUBJECT=re.compile(r'戦場にいる味方(?!以外)|味方全体|1stキャラクター|1stキャラ|(?<![無宿])敵|自身')
# R-06：dimension_labels 只附加下列同句逐字写出的对象短语；「敵」不在此列（R-03，
# 敵方对象仅由 attribute_role 在真实敌方分句中给出，且条件短语已遮蔽）。
TARGET_ATTACH={'戦場にいる味方','味方全体','自身','1stキャラクター','1stキャラ'}
TARGET_CANON={'1stキャラクター':'1st角色','1stキャラ':'1st角色'}
SCOPE_PATTERN=re.compile(r'(?:戦場にいる|メインパーティの)(<[^<>]{1,30}>所属)')
CONDITION_PATTERNS=(re.compile(r'地形が砂浜[/／]船上[/／]海中の時'),re.compile(r'ボスWAVE時'),
                    re.compile(r'年代記の力を発動した時'),re.compile(r'敵陣にいると'),re.compile(r'敵陣の奥に行く程'),
                    re.compile(r'状態異常の敵がいると'),
                    re.compile(r'[0-9０-９]+人以上で同じ敵を攻撃すると'),
                    re.compile(r'自身がヒロイックスキルに設定されていると'))


def mask_conditions(text):
    """Mask all registered condition phrases (incl. the two R-03「敵」条件) for object/subject search only;
    condition detection in dimension_labels still runs on the unmasked window."""
    for pat in CONDITION_PATTERNS:
        text=pat.sub(lambda m:'■'*len(m.group(0)),text)
    for phrase in CONDITION_EXCLUDES:
        text=text.replace(phrase,'■'*len(phrase))
    return text


def sentence_start(text,pos):
    start=0
    for d in SENTENCE_BREAKS:
        p=text.rfind(d,0,pos)
        if p>=0 and p+1>start:start=p+1
    return start


def dimension_labels(text,pos,role,subject_start=None,pos_end=None):
    """Same-sentence verbatim condition/affiliation-scope/battlefield-ally labels before the number."""
    labels={};sent=sentence_start(text,pos);window=text[sent:pos]
    recip=None;recip_end=None
    if role in TARGET_SENTENCE_ROLES or role in CONDITION_SENTENCE_ROLES:
        for m in re.finditer(r'(1stキャラクター|1stキャラ)に',window):
            recip,recip_end=m.group(1),m.end()
    if role in TARGET_SENTENCE_ROLES:
        # 条件短语切点：句内最后一个条件短语结束处；之后的对象/所属不继承条件之前的（R-03：30336
        # 「2人以上で…」不得继承「味方全体」）。
        cut=0
        for pat in CONDITION_PATTERNS+tuple(re.compile(re.escape(p)) for p in CONDITION_EXCLUDES):
            for m in pat.finditer(window):
                if m.end()>cut:cut=m.end()
        # R-06：对象搜索窗口为同句数字之前全部前文（句首主题可被后句承前省略继承）；
        # 全程先遮蔽条件短语中的「敵」（R-03）。
        masked=mask_conditions(window)
        subject=None;subject_end=None
        for m in TARGET_SUBJECT.finditer(masked[cut:]):
            subject,subject_end=m.group(0),cut+m.end()
        if subject in TARGET_ATTACH:labels['target']=TARGET_CANON.get(subject,subject)
        # M-03（DeepSeek 20to39审查）：「1stキャラクターに…効果を付与」且效果对象是「攻撃した敵」时，
        # 1st 是授与者不是效果对象；效果对象「敵」由 attribute_role 给出，这里只登记付与注记。
        elif recip is not None and not (subject=='敵' and subject_end is not None and subject_end>recip_end):
            labels['target']=TARGET_CANON.get(recip,recip)
        elif recip is not None and subject=='敵' and subject_end is not None and subject_end>recip_end:
            labels['grant_note']=recip+'に付与'
        # R-06：所属继承整个同句前文，但止于付与对象标记「1stキャラクターに」之后的新述语
        # （20521第二数值不得继承第一述语的所属）；同句后段新所属就近覆盖（last match wins）。
        # L-02：メインパーティの限定是逐字主队限定，scope 保留完整短语。
        cut_scope=0
        for m in re.finditer(r'(1stキャラクター|1stキャラ)に',window):
            cut_scope=m.end()
        scope=None
        for m in SCOPE_PATTERN.finditer(window[cut_scope:]):scope=m
        if scope:labels['scope']=scope.group(0) if scope.group(0).startswith('メインパーティの') else scope.group(1)
    # M-05：「与えたダメージのN%、自身のHPが回復」的回复对象「自身」在数字之后，逐字就近补。
    if role=='回复量效果量百分比' and 'target' not in labels:
        m=re.match(r'[、,]?\s*(自身|味方全体|戦場にいる味方|1stキャラクター|1stキャラ)のHPが回復',
                   text[pos_end if pos_end is not None else pos:])
        if m:labels['target']=TARGET_CANON.get(m.group(1),m.group(1))
    # M-03/L-03：「効果を付与/与え」句中「1stキャラクターに」是授与对象；效果对象不是 1st 时补付与注记。
    if (recip is not None and (role in TARGET_SENTENCE_ROLES or role in CONDITION_SENTENCE_ROLES)
            and re.search(r'効果を(?:付与|与え)',text[sent:])
            and labels.get('target')!=TARGET_CANON.get(recip,recip)):
        labels.setdefault('grant_note',recip+'に付与')
    if role in CONDITION_SENTENCE_ROLES:
        hits=[]
        for pat in CONDITION_PATTERNS:
            hit=None
            for hit in pat.finditer(window):pass
            if hit and hit.group(0) not in hits:hits.append(hit.group(0))
        if hits:labels['conditions']=hits
    return labels


def quantitative(value):
    value=re.sub(r'0x[0-9a-fA-F]+','',str(value))
    return bool(re.search(r'[0-9０-９]|×|\bB(?:_set)?\b',value))


def walk_entries(entry):
    yield entry
    for key in ('skill_refs','sympathy_skill_refs','boss_skill_refs','sa_ability_refs','sub_effects'):
        for child in entry.get(key,[]):
            if isinstance(child,dict): yield from walk_entries(child)


class Inputs:
    def __init__(self,root:Path,cids):
        self.root=root.resolve(); self.base=self.root/'output/character_skills'; self.cids=set(cids)
        self.links={r['cid']:r for r in lines(self.base/'links/character_skills.jsonl') if r['cid'] in self.cids}
        self.profiles={r['cid']:r for r in lines(self.base/'profiles/profiles.jsonl') if r['cid'] in self.cids}
        if set(self.links)!=self.cids or set(self.profiles)!=self.cids:
            raise ValueError('Requested cid missing from declared links/profiles inputs')
        keys={e['rec_key'] for p in self.profiles.values() for g in p['groups'] for e in g['records']}
        self.old={r['rec_key']:r for r in lines(self.base/'profiles/records.jsonl') if r['rec_key'] in keys}
        self.rule_metadata=read(self.base/'profiles/rules.json')
        self.decoded=self.root/'output/cache_full_20261015_v3/decoded'
        self.apk=self.root/'output/base_master'
        self.cache_chara={r['cid']:r for r in read(self.decoded/'charainfo.data5.json.raw')['charainfo']}
        self.apk_chara={r['cid']:r for r in read(self.apk/'_mdCharacter.json')['charainfo']}
        self.cache_skill={r['skillid']:(i,r) for i,r in enumerate(read(self.decoded/'skilllist.data5.json.raw')['skilllist'])}
        self.apk_skill={r['skillid']:(i,r) for i,r in enumerate(read(self.apk/'_mdSkill.json')['skilllist'])}
        self.baseline=read(self.root/'output/card_comparison_cid30236/description_effects.json') if 30236 in self.cids else []
        self.forward=read(self.base/'type1082/native_checks.json')['verdict']
        if self.forward!='FORWARD': raise ValueError('This sample implementation requires the frozen FORWARD verdict')
        self.raw_docs={}
        # Existing converters use root-relative source files: declare/rebind that root explicitly.
        C.ROOT=self.root; C.DECODED=self.decoded; C.BASE_MASTER=self.apk; C.CARD_COMPARISON=self.root/'output/card_comparison_cid30236'
        R.DECODED=self.decoded; R.CARD_COMPARISON=C.CARD_COMPARISON
        os.chdir(self.root)
        self.old_answers={}
        for r in self.old.values():
            self.old_answers[(r['table'],r['record_id'],r['layer'])]=r.get('answers',[])
            for ch in r.get('children',[]):
                self.old_answers.setdefault((ch['table'],ch['record_id'],ch.get('layer',r['layer'])),ch.get('answers',[]))

    def skill(self,sid):
        if sid in self.cache_skill:
            i,row=self.cache_skill[sid]; layer='CACHE'; path='skilllist.data5.json.raw'; pointer=f'/skilllist/{i}'
        elif sid in self.apk_skill:
            i,row=self.apk_skill[sid]; layer='APK'; path='_mdSkill.json'; pointer=f'/skilllist/{i}'
        else: return None
        return dict(resolved=True,table='skilllist',reference_id=sid,record=row,layer=layer,
                    source=dict(source_key=f'{layer}/{path}',json_pointer=pointer,layer=layer,
                                record_key=f'{layer}/{path}#{pointer}'))

    def precise_source(self,entry):
        source=copy.deepcopy(entry.get('source') or {})
        ref=entry.get('reference_field','')
        table=entry.get('table')
        if entry.get('layer')=='CACHE' and table in ('bosspattern','bossskill','job_ability'):
            stem='jobabilityinfo' if table=='job_ability' else 'bossinfo'
            path=self.decoded/(stem+'.data5.json.raw')
            if not path.is_file():
                source.update(json_pointer=None,source_resolution='UNKNOWN_MISSING_DECODED_FILE',
                              note='声明的真实解码文件缺失，未伪造记录指针')
                return source
            if stem not in self.raw_docs:self.raw_docs[stem]=read(path)
            doc=self.raw_docs[stem]
            rows=doc['job_ability'] if table=='job_ability' else doc['bossinfo'][table]
            ident=entry.get('reference_id');record=entry.get('record')
            candidates=[(i,r) for i,r in enumerate(rows) if
                        (ident in (r.get('cids') or []) if table=='job_ability' else r.get('patternid' if table=='bosspattern' else 'skillid')==ident)
                        and (record is None or r==record)]
            if len(candidates)!=1:
                source.update(json_pointer=None,source_resolution='UNKNOWN_NON_UNIQUE_OR_MISMATCHED_RECORD',
                              note='按引用ID及完整原始record无法唯一匹配；未选择首条候选')
                return source
            index,_=candidates[0]
            pointer=f'/job_ability/{index}' if table=='job_ability' else f'/bossinfo/{table}/{index}'
            source.update(source_key=f'CACHE/{stem}.data5.json.raw',
                          record_key=f'CACHE/{stem}.data5.json.raw#{pointer}',json_pointer=pointer,
                          original_file=path.relative_to(self.root).as_posix(),
                          source_resolution='RESOLVED_EXACT_DECODED_RECORD',
                          note='按实际解码JSON的引用ID及完整原始record唯一核对；只修复定位，不升级数值或关联证据')
        if table in ('extra_ability_info','passive_info','denju_limit_break_info'):
            stem={'extra_ability_info':'extraabilitylist','passive_info':'passivelist','denju_limit_break_info':'denju_lblist'}[table]
            if stem not in self.raw_docs: self.raw_docs[stem]=read(self.decoded/(stem+'.data5.json.raw'))
            roots=self.raw_docs[stem][table]
            cid=int(str(entry['reference_id']).split('#')[0])
            parent_index,parent=next((i,r) for i,r in enumerate(roots) if r['cid']==cid)
            key={'extra_ability_info':'extra_abilities','passive_info':'passives','denju_limit_break_info':'denju_limit_break'}[table]
            ordinal=int(re.search(r'\[(\d+)\]',ref).group(1))
            if key not in parent:
                # Preserve actual nested-array name for denju data rather than guessing.
                key=next(k for k,v in parent.items() if isinstance(v,list) and ordinal<len(v) and v[ordinal]==entry['record'])
            assert parent[key][ordinal]==entry['record'],f'Nested source mismatch {cid}:{ref}'
            source.update(parent_json_pointer=f'/{table}/{parent_index}',
                          json_pointer=f'/{table}/{parent_index}/{key}/{ordinal}',
                          nested_reference_field=ref,
                          location_scope='字节范围和原始hash属于父记录；嵌套字段按完整JSON指针定位')
            if source.get('raw_record_sha256'):
                source['parent_raw_record_sha256']=source.pop('raw_record_sha256')
        return source

    def field_answers(self,entry):
        table,ident,layer=entry.get('table'),entry.get('reference_id'),entry.get('layer')
        rec=entry.get('record',{})
        existing=copy.deepcopy(self.old_answers.get((table,ident,layer),[]))
        if table=='charainfo':
            # Preserve the prior record-specific execution/equivalence gate.
            return existing
        etype=rec.get('ability') if table in ('skilllist','heroicskilllist','supporterskill') else rec.get('skillid0') if table=='bossskill' else None
        if etype is None: return existing
        seen={a['f'] for a in existing}
        for name,value in rec.items():
            field='/'+name
            if field in seen or not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value): continue
            answer=R.answer_for(table,etype,field,value,rec)
            if answer:
                existing.append(dict(f=field,raw=value,value=answer['value_text'],kind=answer['quantity_kind'],
                                     unit=answer['unit'],status=answer['answer_status'],scope='BY_TYPE_EXTRAPOLATED',
                                     rule_key=f'{table}|{etype}|{field}',details=answer))
        for answer in existing:
            rule=self.rule_metadata.get(answer.get('rule_key'),{})
            answer.setdefault('conversion',rule.get('conversion'))
            answer.setdefault('base_definition',rule.get('base_definition'))
            answer.setdefault('conditions',rule.get('conditions'))
            answer.setdefault('rule_limits',rule.get('limits'))
        return existing

    def evidence_tree(self,entry,seen=None):
        seen=set() if seen is None else seen
        key=(entry.get('table'),entry.get('reference_id'),entry.get('layer'))
        if key in seen: return []
        seen.add(key)
        out=[]
        if entry.get('resolved',True):
            out.append(dict(table=entry.get('table'),record_id=entry.get('reference_id'),layer=entry.get('layer'),
                            source=self.precise_source(entry),answers=self.field_answers(entry),
                            raw_record=entry.get('record'),association_evidence='确认·记录引用（不代表句内归属）'))
        for e in list(walk_entries(entry))[1:]:
            childkey=(e.get('table'),e.get('reference_id'),e.get('layer'))
            if childkey not in seen:
                seen.add(childkey)
                out.append(dict(table=e.get('table'),record_id=e.get('reference_id'),layer=e.get('layer'),
                                source=self.precise_source(e),answers=self.field_answers(e),raw_record=e.get('record'),
                                association_evidence='确认·记录引用（不代表句内归属）'))
        return out

    def forward_links(self,entry):
        if entry.get('table')!='extra_ability_info': return []
        out=[]
        for index,sid in enumerate(entry.get('record',{}).get('skill_ids',[])):
            wrapper=self.skill(sid)
            if not wrapper or wrapper['record'].get('ability')!=1082: continue
            raw=wrapper['record'].get('str0')
            try: target=self.skill(int(raw))
            except (ValueError,TypeError): target=None
            out.append(dict(wrapper_id=sid,wrapper=wrapper,target_id=target['reference_id'] if target else None,
                            raw_str0=raw,raw_str0_state=raw_state(wrapper['record'],'str0'),target=target,
                            reference_field=f"{entry['reference_field']}.skill_ids[{index}]",
                            evidence='确认·链上复用（str0转发已证）',
                            runtime_evidence='output/character_skills/type1082/native_checks.json',
                            field_answers=self.field_answers(target) if target else [],
                            limits='父limit_break档位及目标资格有门控；缺param0默认值和句内数值归属不随链升级'))
        return out


def basic(data, cid):
    rec=data.cache_chara.get(cid,data.apk_chara.get(cid))
    layer='CACHE' if cid in data.cache_chara else 'APK'
    source=data.links[cid]['charainfo_source']
    spec=[('name','姓名'),('title','称号'),('rarity','星级'),('cost','COST'),('jobtype','职业'),
          ('home','所属'),('battle_home','战斗所属'),('weaponid','武器ID'),('iniap','主表初始ATK'),('inihp','主表初始HP'),
          ('critical','暴击几率原值'),('atkspeed','攻击速度原值'),('growth','成长原值'),('profile','介绍')]
    fields=[]
    for key,label in spec:
        state=raw_state(rec,key)
        note=('缓存整条记录缺失职业，未知；未逐字段回退APK' if key=='jobtype' and state=='missing' and layer=='CACHE' else
              '主表缺失；外部/网站维护' if state=='missing' else '原值null；外部/网站维护' if state=='null' else
              '原值；单位或枚举语义未在此推定' if key in ('atkspeed','growth','battle_home','home','critical') else '主表原值')
        fields.append(dict(key=key,label=label,raw_value=rec.get(key),raw_state=state,note=note,
                           source={**source,'field':f'/{key}'},evidence='确认' if state not in ('missing','null') else '未知'))
    external=[dict(label=label,value='外部/网站维护',raw_state='missing') for label in ('标签/外部资料','日期','等级成长表')]
    for key,label in [('illustrator','画师'),('voice_artist','声优')]:
        external.append(dict(label=label,value=rec.get(key) if key in rec else '外部/网站维护',raw_state=raw_state(rec,key),
                             note='主表原值' if key in rec else '外部/网站维护',source={**source,'field':'/'+key}))
    return apply_basic_display(data,dict(fields=fields,external=external,layer=layer,card_art=dict(status='NO_VERIFIED_BINDING',
                    note='本样本未找到本项目已证绑定卡面；不借用参考页图片'),raw_record=rec))


def source_answer(answer,table,ident,source,numeric_source='规则',association='确认'):
    value=answer.get('value',answer.get('readable_value',''))
    return dict(value=value,quantity_kind=answer.get('kind',answer.get('quantity_kind')),
                raw_value=answer.get('raw',answer.get('raw_value')),field_path=answer.get('f',answer.get('field_path')),
                unit=answer.get('unit'),conversion=answer.get('conversion'),base_definition=answer.get('base_definition'),
                target=answer.get('target'),conditions=answer.get('conditions',answer.get('condition')),
                duration=answer.get('duration'),rule_limits=answer.get('rule_limits'),note=answer.get('note'),
                numeric_source=numeric_source,numeric_evidence='确认',association_evidence=association,
                evidence_scope=answer.get('scope',answer.get('evidence_scope')),
                table=table,record_id=ident,source=source,rule_key=answer.get('rule_key'),
                evidence=answer.get('evidence'),quantitative=quantitative(value))


# 源数据异常登记：原文疑似笔误，页面忠实保留，不修改游戏原值（G-10）。
SOURCE_ANOMALIES={204:[('ダッシュ範囲上にいるに','源数据疑似笔误“ダッシュ範囲上にいるに”（来源sinfo原文如此）；页面忠实保留原文，未修正，不当作页面错误。')]}

# 分母口径登记（R2审查R-12）：计入N_all但非效果正文的行在此说明；不改行集合，只登记。
DENOMINATOR_NOTES={20438:[('神仙セリーヌ_神仙の力',
    'SA标题行（对应技能名「神仙セリーヌ用SA_ArtsFlag」的页内标题，非效果正文）按现状计入N_all/C。'
    '内部标签排除规则为整技能文本单行且匹配内部前缀（エクストラ_/パッシブ_/職業_/内部）或含SA_（cid89据此整技能排除）；'
    '本技能文本含句读正文行「《玲瓏璧》のサブアビリティ。」，不满足整技能排除条件，标题行本身无独立排除依据，故保留计数。')],
 6215:[('呪い付与_5回1000ダメージ',
    'SA内部标签行（整技能文本即「呪い付与_5回1000ダメージ」单一行，下划线连接的内部标识，非效果正文）'
    '按L-07保留口径计入N_all/A（「5回」为原文数字项；RM-04，DeepSeek remaining审查）。'
    '内部标签排除规则为整技能文本单行且匹配内部前缀（エクストラ_/パッシブ_/職業_/内部）或含SA_（cid89据此整技能排除）；'
    '本文本不含上述前缀与SA_，无逐字排除依据，故保留计数并在此登记。'
    '「1000ダメージ」按同轮RM-04补提为固定伤害量（special_move正文「呪いは5回までの追加固定ダメージを与える」佐证语义）。')],
 6327:[('アマツVer3用_ManaHunter',
    'SA内部标签行（整技能文本即「アマツVer3用_ManaHunter」单一行，内部用途标识，非效果正文）'
    '按L-07保留口径计入N_all/C（RM-04，DeepSeek remaining审查）。'
    '内部标签排除规则为整技能文本单行且匹配内部前缀（エクストラ_/パッシブ_/職業_/内部）或含SA_；'
    '本文本不含上述前缀与SA_，无逐字排除依据，故保留计数并在此登记。')]}


def baseline_target(b):
    ids=re.findall(r'pattern(\d+)',b.get('condition',''))
    if b.get('description_table')=='bosspattern' and len(set(ids))==1: return int(ids[0])
    return b.get('description_record_id')


def build_card(data:Inputs,cid):
    profile=data.profiles[cid]; links=data.links[cid]
    oldgroups={g['group']:g for g in profile['groups']}
    linkgroups={g['group']:g for g in links['groups']}
    groups=[]; allrows=[]; mapping=[]; position_rows={};registry={b['effect_id']:dict(answer=b,mapped_row_ids=[],mapped_skill_ids=[]) for b in data.baseline} if cid==30236 else {}
    stage_targets={}
    patterns=[e for g in links['groups'] if g['group']=='special_move' for e in g['records'] if e.get('table')=='bosspattern']
    for effect_id,item in registry.items():
        b=item['answer'];target=baseline_target(b)
        if b.get('description_table')=='bosspattern':
            required={(f.get('table'),f.get('record_id')) for f in b.get('field_refs',[])}
            candidates=[e['reference_id'] for e in patterns if required and required <=
                        {(n.get('table'),n.get('reference_id')) for n in walk_entries(e)}]
            if len(candidates)==1:target=candidates[0]
        stage_targets[effect_id]=target
        item['execution_description_id']=target
    for group_id,label in GROUPS:
        group=dict(group=group_id,label=label,skills=[],status='无配置',unresolved=[],annotations=[])
        source_groups=[group_id,'denju_lb'] if group_id=='denju' else [group_id]
        for original_group in source_groups:
            lg=linkgroups.get(original_group,{})
            group['unresolved']+=lg.get('unresolved',[]); group['annotations']+=lg.get('annotations',[])
            oldrefs=oldgroups.get(original_group,{}).get('records',[])
            display_slots={}
            expanded=[]
            for source_ordinal,e in enumerate(lg.get('records',[])):
                expanded.append({**e,'_origin_ordinal':source_ordinal})
                if e.get('table')=='leader_ability' and e.get('record',{}).get('sympathy_text'):
                    expanded.append({**e,'reference_field':e['reference_field']+'.sympathy_text',
                                     '_text_field_override':'sympathy_text','_origin_ordinal':source_ordinal})
            for ordinal,entry in enumerate(expanded):
                record=entry.get('record',{}); table=entry.get('table'); ref=entry.get('reference_field',str(ordinal))
                source=data.precise_source(entry)
                display_key=json.dumps([original_group,ref,table,entry.get('reference_id'),record,source.get('source_key'),source.get('json_pointer')],sort_keys=True,ensure_ascii=False)
                # Equal aliases do not shift the display/row IDs of later real slots.
                ordinal=display_slots.setdefault(display_key,len(display_slots))
                tf,nf=TEXT.get(table,('text','name'));tf=entry.get('_text_field_override',tf); text=clean(record.get(tf,''))
                name=clean(record.get(nf,'')) if nf else ''
                original_ref=ref.removesuffix('.sympathy_text') if entry.get('_text_field_override') else ref
                matching_old=[r for r in oldrefs if r.get('reference_field')==original_ref]
                if len(matching_old)>1:
                    matching_old=[r for r in matching_old if (data.old.get(r.get('rec_key'),{}).get('table'),
                                  str(data.old.get(r.get('rec_key'),{}).get('record_id')),data.old.get(r.get('rec_key'),{}).get('layer'))
                                  ==(table,str(entry.get('reference_id')).split('#')[0],entry.get('layer'))]
                oldref=matching_old[0] if len(matching_old)==1 else {}
                old=data.old.get(oldref.get('rec_key'),{})
                oldfrags=old.get('fragments',[]) if table not in ('extra_ability_info','passive_info','denju_limit_break_info') else []
                stage=('传授突破' if original_group=='denju_lb' else '原表顺序档' if group_id=='passive' else '档位')+f' {ordinal+1}'
                if 'lv' in record and record['lv'] not in (None,''): stage='Lv '+str(record['lv'])
                if tf=='sympathy_text':stage='Leader共鸣（原字段sympathy_text）'
                skill_id=f'{cid}/{group_id}/{original_group}/{ref}'
                skill=dict(skill_id=skill_id,name=name,stage=stage,level=record.get('lv'),level_state=raw_state(record,'lv'),
                           reference_field=ref,original_group=original_group,record_id=entry.get('reference_id'),table=table,
                           layer=entry.get('layer'),source=source,text_field=tf,original_text=text,
                           cost=record.get('scost',record.get('skill_cost')),cost_state=raw_state(record,'scost') if table!='charainfo' else raw_state(record,'skill_cost'),
                           rows=[],record_evidence=data.evidence_tree(entry),forward_links=data.forward_links(entry),
                           old_rec_key=oldref.get('rec_key'),link_status=entry.get('link_status'),
                           baseline_metadata_answers=[],
                           association_evidence='推断' if entry.get('ambiguous') or 'INFERRED' in str(entry.get('link_status','')) else '确认·记录引用（不代表句内归属）')
                skill['level_note']='原表无等级字段，序号不代表解锁等级' if group_id=='passive' and 'lv' not in record else '按原始引用独立保留档位；实际装载另有门控'
                for effect_id,item in registry.items():
                    b=item['answer']
                    # A conditional variant without independent effect prose stays a header annotation.
                    variant=(not text and table=='bosspattern' and b.get('description_table')==table and stage_targets[effect_id]==entry.get('reference_id'))
                    metadata=(not b.get('description_fragment_ja') and table=='bosspattern' and
                              b.get('description_table')==table and b.get('description_record_id')==entry.get('reference_id'))
                    if variant or metadata:
                        a=source_answer(b,table,entry.get('reference_id'),b.get('field_refs'),'既有逐描述证据')
                        a.update(effect_id=effect_id,conditions=b.get('condition'),
                                 baseline_declared_description_id=b.get('description_record_id'),
                                 mapping_note='执行档位及真实子记录引用；本档无独立正文，不新增描述行' if variant else '技能配置/就绪门槛，未虚造描述行')
                        skill['baseline_metadata_answers'].append(a);item['mapped_skill_ids'].append(skill_id)
                internal=text and not any(c in text for c in ('。','◆','\n')) and (bool(re.match(r'^(?:■)?(?:エクストラ_|パッシブ_|職業_|内部)',text)) or 'SA_' in text)
                if internal:
                    skill['internal_label']=text
                    mapping.append(dict(cid=cid,old_rec_key=oldref.get('rec_key'),old_reference_field=ref,
                                        old_fragment_text=text,new_row_id=None,new_source=source,new_text=text,
                                        correction='内部标签保留配置，不计N_all/N_num；非E排除'))
                for fragment_index,span in enumerate([] if internal else fragment_positions(record.get(tf,''))):
                    frag=span['japanese']
                    row_id=f'{cid}-{group_id}-{original_group}-{ref}-lv{record.get("lv","order"+str(ordinal))}-f{fragment_index}'
                    row_id=re.sub(r'[^\w\-]','_',row_id)
                    originals=original_numbers(frag)
                    # 效果量百分比分句补属性/对象标签（G-07；单值泛标签行同样适用，阈值/上限角色不覆盖）；
                    # 条件/所属/目标只取同句原文逐字写出的短语并附加到其后的效果数值，无据不补（R-01）。
                    # R-06：多值行各数值的对象/属性窗口不跨前一个数字；R-03：条件短语中的「敵」先遮蔽。
                    prev_end=None;prev_sent=None;prev_role=None;l04_windows=[]
                    for n in originals:
                        sent=sentence_start(frag,n['raw_span'][0])
                        window_start=prev_end if (prev_end is not None and prev_sent==sent) else None
                        l04_windows.append(window_start if window_start is not None else sent)
                        dims=dimension_labels(frag,n['raw_span'][0],n['role'],window_start,pos_end=n['raw_span'][1])
                        if n['unit']=='%' and n['role']=='效果量百分比':
                            enriched=attribute_role(frag,n['raw_span'][0],window_start)
                            if enriched:n['role']=enriched+'效果量百分比'
                        if dims.get('target') or dims.get('scope'):
                            # 同义对象前缀去重（如 attribute_role 的「1st角色」与 dims 的「1stキャラクター」）。
                            have={TARGET_CANON.get(p,p) for p in n['role'].split('/')[:-1]}
                            add=[t for t in (dims.get('target'),dims.get('scope'))
                                 if t and TARGET_CANON.get(t,t) not in have]
                            if add:
                                n['role']='/'.join(add+[n['role']])
                                if dims.get('target') in add:n['target']=dims['target']
                                if dims.get('scope') in add:n['scope']=dims['scope']
                        if dims.get('conditions'):n['condition']='、'.join(dims['conditions'])
                        # L-01（DeepSeek 20to39审查）：同一敌方减益句（「攻撃した敵の…下がる」）中，
                        # 后续同向值逐字继承「敌方/」前缀；句中出现新主体、方向转上升时不继承。
                        if (prev_sent==sent and prev_end is not None and prev_role and prev_role.startswith('敌方/')
                                and '/' not in n['role'] and n['unit']=='%'):
                            between=frag[prev_end:n['raw_span'][0]]
                            sent_end=min([p for p in (frag.find(b,prev_end) for b in SENTENCE_BREAKS) if p>=0]+[len(frag)])
                            tail=frag[prev_end:sent_end]
                            if (not TARGET_SUBJECT.search(mask_conditions(between))
                                    and '下が' in tail and not re.search(r'上が|アップ',tail)):
                                n['role']='敌方/'+n['role']
                        if dims.get('grant_note'):
                            n['condition']=(n['condition']+'、' if n.get('condition') else '')+dims['grant_note']
                        prev_end=n['raw_span'][1];prev_sent=sent;prev_role=n['role']
                    # L-04（终版polish）：多值重复标签行的逐值就近对象——仅同一行内同一数量/次数类
                    # 角色≥2个数值、且该数值同分句内紧邻逐字对象短语时，display 以括注原样引用；
                    # 无逐字依据的行保持原样（不为清零债务按位置猜测）。
                    l04_counts=collections.Counter(n['role'] for n in originals if n['role'] in L04_COUNT_ROLES)
                    for n,ws in zip(originals,l04_windows):
                        if n['role'] in L04_COUNT_ROLES and l04_counts[n['role']]>=2 and 'qualifier' not in n and '（' not in n['display']:
                            phrase=l04_object(frag,ws,n['raw_span'][0])
                            if phrase:
                                n['l04_object']=phrase;n['display']+='（'+phrase+'）'
                                n['l04_note']='括注为该数值同分句紧邻的逐字原文（L-04逐值标注）'
                    answers=[dict(value=f"{n['role']}：{n['display']}"+(f"（条件：{n['condition']}）" if n.get('condition') else ''),
                                  quantity_kind=n['role'],unit=n['unit'],
                                  raw_value=n['value'],numeric_source='原文',numeric_evidence='确认',association_evidence='未知',
                                  note='；'.join(['原文数字，字段关联未证']+[n[key] for key in ('display_note','normalization_note','reduce_note','l04_note') if n.get(key)]),
                                  source={**source,'field':'/'+tf},context=n['context'],
                                  **({'condition':n['condition']} if n.get('condition') else {}),
                                  quantitative=True) for n in originals]
                    matched_old=next((f for f in oldfrags if canonical(f['t'])==canonical(frag)),None)
                    if matched_old and matched_old.get('binding') and matched_old.get('status')=='REVIEWED_DESCRIPTION_BINDING':
                        for answer in matched_old['binding'].get('fields',[]):
                            converted=source_answer(answer,answer.get('table',table),answer.get('record_id',entry.get('reference_id')),source)
                            converted['binding']=matched_old['binding']
                            answers.append(converted)
                    # Baseline attaches only at an explicit fragment, table and actual stage.
                    for effect_id,item in registry.items():
                        b=item['answer']; snippet=b.get('description_fragment_ja')
                        if b.get('description_table')!=table or stage_targets[effect_id] not in (None,entry.get('reference_id')): continue
                        if table=='job_ability':
                            # The baseline itself distinguishes self and battlefield targets;
                            # its shortened snippet is not a license to match both sentences.
                            target=b.get('target','')
                            ref_ids={f.get('record_id') for f in b.get('field_refs',[])}
                            if 65000002 in ref_ids and target=='战场味方' and not frag.startswith('戦場にいる味方'):continue
                            if 65000001 in ref_ids and target=='自身' and not frag.startswith('攻撃力と防御力'):continue
                        if snippet:
                            if canonical(snippet) not in canonical(frag):continue
                        else:
                            description=b.get('description_ja')
                            exact_text=(text in description if isinstance(description,list) else clean(description)==text)
                            if not exact_text:continue
                            if table=='leader_ability':
                                if len(fragments(text))!=1:continue
                            elif table=='extra_ability_info':
                                if effect_id=='extra_chain' and 'Chainによる威力の上昇量' not in frag:continue
                                elif effect_id=='other_extra_initial_mana' and '万象マナを1つ持った状態' not in frag:continue
                                elif effect_id not in ('extra_chain','other_extra_initial_mana'):continue
                            else:continue
                        a=source_answer(b,table,entry.get('reference_id'),b.get('field_refs'),numeric_source='既有逐描述证据')
                        a.update(effect_id=effect_id,baseline_declared_description_id=b.get('description_record_id'),
                                 target=b.get('target'),conditions=b.get('condition'),evidence=b.get('evidence'),
                                 evidence_scope='REVIEWED_RECORD',conversion='原101项基线的既有换算；不再次乘Chain')
                        if effect_id=='extra_chain':
                            amount=next(n['literal'] for n in originals if n['unit']=='%')
                            a['value']=f'本档Chain威力提升量 {amount}（原文；原101项基线支持分档）'
                        answers.append(a); item['mapped_row_ids'].append(row_id)
                    # L-09（DeepSeek 20to39审查）：同一数值同时存在原文（关联未知）与规则（确认）答案时，
                    # 在原文答案注记覆盖关系；不改 R-01 整行判定，数值与口径不变。
                    rule_values=[float(a['raw_value']) for a in answers
                                 if a.get('numeric_source')=='规则' and isinstance(a.get('raw_value'),(int,float))
                                 and not isinstance(a.get('raw_value'),bool)]
                    for a in answers:
                        if a.get('numeric_source')!='原文' or '同值规则答案' in (a.get('note') or ''):continue
                        try: v=float(a.get('raw_value'))
                        except (TypeError,ValueError): continue
                        if any(abs(v-r)<=1e-9 for r in rule_values):
                            a['note']=(a.get('note') or '')+'；同值已有一条规则答案（见本行「规则」来源值行）；原文数字的字段关联仍未知，整行按R-01口径维持未知'
                    numerical=[a for a in answers if a['quantitative']]
                    # Existing baseline mechanisms may be useful, but only count B with an explicit added claim.
                    mechanisms=[a for a in answers if not a['quantitative'] and a.get('numeric_source')=='既有逐描述证据']
                    cls='A' if numerical else 'B' if mechanisms else 'C'
                    # R-01（40to59审查）：整行字段关联确认当且仅当该行全部答案的关联均为确认；
                    # 任一答案「关联未知」（含原文数字答案）即整行为未知，不再用 any() 虚增整行确认。
                    association='确认' if answers and all(a['association_evidence']=='确认' for a in answers) else '未知'
                    if skill['association_evidence']=='推断' and association=='确认': association='推断'
                    reasons=[]
                    if association!='确认':
                        reasons.append('尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应' if originals else
                                       '原文未提供该效果数值，尚无已审定的句内字段归属'+
                                       ('；原文含范围几何数字（N直線），不作为效果量提取' if re.search(r'[0-9０-９]+直線',frag) else ''))
                    if not answers: reasons.append('此描述尚无可适用的已确认数值或新增机制证据')
                    if matched_old and matched_old.get('cands') and not matched_old.get('binding'):
                        reasons.append('旧关键词候选未作为答案；不能排除对象或效果错配')
                    if group_id=='heroic': reasons.append('英雄技引用沿用既有ID模式关联，未证明运行时装载和等级条件')
                    if skill['forward_links']: reasons.append('str0目标规则已在来源层复用；具体句内归属、对象资格及缺参默认值另列未知')
                    partial=cls=='A' and not (matched_old and matched_old.get('binding') and skill['association_evidence'].startswith('确认'))
                    state_keys=([f'param{i}' for i in range(10)] if table in ('skilllist','heroicskilllist','supporterskill') else
                                [f'skillparam{i}' for i in range(10)] if table in ('charainfo','bossskill') else [])
                    states={k:raw_state(record,k) for k in sorted(set(state_keys)|{k for k in record if re.match(r'(param|iParam|skillparam|str)\d',k)})}
                    state_counts=collections.Counter(states.values())
                    state_summary=('原值状态：'+ ' / '.join(f'{label}{state_counts[state]}' for state,label in
                                  [('present','有值'),('zero','真实零'),('null','null'),('missing','缺失')])) if states else '父记录无直接参数槽；已关联子记录原值保留在来源层'
                    row=dict(row_id=row_id,cid=cid,group=group_id,stage=stage,level=record.get('lv'),reference_field=ref,
                             fragment_index=fragment_index,japanese=frag,context_text=text,row_class=cls,answers=answers,
                             original_numeric_items=originals,original_A=bool(originals),evidence='确认' if association=='确认' else '推断' if association=='推断' else '未知',
                             numeric_evidence='确认' if numerical else '未知',association_evidence=association,
                             partial=partial,unknown_reasons=reasons,source={**source,'field':'/'+tf,
                                'field_json_pointer':source.get('json_pointer','')+'/'+tf if source.get('json_pointer') else None},
                             raw_value_states=states,raw_state_summary=state_summary,
                             source_evidence_ref=skill_id,old_fragment_status=matched_old.get('status') if matched_old else None,
                             old_candidates_reused=False,mechanism_added=mechanisms,
                             evidence_scope=sorted({str(a['evidence_scope']) for a in answers if a.get('evidence_scope')}))
                    # L-12（DeepSeek 20to39审查）：冻结绑定条件（N>=2/职业/所属/武器等）提到行级可见层，
                    # 不再只在折叠JSON；条件文本逐字来自冻结binding，不改数值与判定。
                    row['binding_conditions']=[]
                    for a in answers:
                        binding=a.get('binding')
                        if binding and binding.get('condition') and binding['condition'] not in row['binding_conditions']:
                            row['binding_conditions'].append(binding['condition'])
                    # The display ordinal is not an execution identity. Reference slots
                    # and the actual parent record (including level/conditions) are.
                    execution_context=dict(reference_slot=ref,parent_record_sha256=hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest())
                    identity=position_identity(cid,group_id,row['source'],table,entry.get('reference_id'),skill['level_state'],record.get('lv'),span,original_group,execution_context)
                    encoded_identity=json.dumps(identity,ensure_ascii=False,separators=(',',':'))
                    row['source_position']={**span,'field_pointer':row['source']['field_json_pointer'],'source_key':source.get('source_key')}
                    row['source_span_id']='span-'+hashlib.sha256(encoded_identity.encode('utf-8')).hexdigest()[:20]
                    row['merge_key']=identity;row['alias_references']=[]
                    if encoded_identity in position_rows:
                        original=position_rows[encoded_identity]
                        for item in registry.values():
                            item['mapped_row_ids']=[original['row_id'] if rid==row_id else rid for rid in item['mapped_row_ids']]
                        original['alias_references'].append(dict(row_id=row_id,reference_field=ref,source=source,stage=stage,origin_list_ordinal=entry['_origin_ordinal']))
                        skill.setdefault('alias_row_ids',[]).append(original['row_id'])
                        row_id=original['row_id']
                    else:
                        position_rows[encoded_identity]=row
                        skill['rows'].append(row);allrows.append(row)
                    old_fragment=next((f['t'] for f in old.get('fragments',[]) if canonical(f['t'])==canonical(frag)),None)
                    if table in ('extra_ability_info','passive_info','denju_limit_break_info') and fragment_index<len(old.get('fragments',[])):
                        old_fragment=old['fragments'][fragment_index]['t']
                    mapping.append(dict(cid=cid,old_rec_key=oldref.get('rec_key'),old_reference_field=ref,
                                        old_occurrence_key=f'{cid}/{original_group}/{ref}/f{fragment_index}',old_fragment_text=old_fragment,
                                        new_row_id=row_id,new_source=row['source'],new_text=frag,
                                        correction='按links逐档原文纠正复用rec_key' if table in ('extra_ability_info','passive_info','denju_limit_break_info') else '保持原始引用/句子边界'))
                if not skill['rows']: skill['empty_reason']='同源位置及同执行档/父条件的别名引用，描述已合并；见alias_row_ids' if skill.get('alias_row_ids') else '内部标签，不计描述分母' if internal else '关联缺失' if not entry.get('resolved',True) else '无描述正文；保留配置原值'
                group['skills'].append(skill)
        if group['skills'] or group['annotations']: group['status']='已配置'
        if group['unresolved']: group['status']='关联缺失'
        groups.append(group)
    counts=collections.Counter(r['row_class'] for r in allrows); cross={c:{e:0 for e in ('确认','推断','未知')} for c in ('A','B','C')}
    for r in allrows: cross[r['row_class']][r['evidence']]+=1
    total=len(allrows); chains=[f for g in groups for s in g['skills'] for f in s['forward_links']]
    coverage=dict(N_all=total,E=0,N_num=total,A=counts['A'],B=counts['B'],C=counts['C'],
                  A_rate=counts['A']/total if total else 0,B_rate=counts['B']/total if total else 0,C_rate=counts['C']/total if total else 0,
                  evidence_cross=cross,partial_A=sum(r['partial'] for r in allrows),original_A=sum(r['original_A'] for r in allrows),
                  chain_target_associations=len(chains),chain_targets_with_rules=sum(bool(f['field_answers']) for f in chains),
                  chain_new_A_rows=0,chain_new_value_items_in_rows=0,
                  chain_parent_original_A_rows=sum(r['original_A'] for g in groups for s in g['skills'] if s['forward_links'] for r in s['rows']),
                  old_descriptions=profile['coverage']['descriptions'],old_confirmed=profile['coverage']['fragments_attributed_confirmed'],
                  old_hint=profile['coverage']['fragments_attributed_hint_only'])
    # H-01（DeepSeek 20to39审查）：整行确认分两类口径——记录级 REVIEWED_RECORD（30236基线）
    # 与类型外推 BY_TYPE_EXTRAPOLATED（冻结P3B9/P3B10模板行）；只拆分呈现与统计，不降级判定。
    confirmed_scopes={}
    for r in allrows:
        if r['evidence']!='确认':continue
        scopes=set(r['evidence_scope'])
        key=next(iter(scopes)) if len(scopes)==1 else 'MIXED' if scopes else '无scope标注'
        confirmed_scopes[key]=confirmed_scopes.get(key,0)+1
    coverage['confirmed_rows_by_scope']=confirmed_scopes
    coverage['internal_labels_excluded']=sum(bool(s.get('internal_label')) for g in groups for s in g['skills'])
    coverage['leader_sympathy_rows_added']=sum(len(s['rows']) for g in groups for s in g['skills'] if s['text_field']=='sympathy_text')
    coverage['repeated_actual_occurrences_retained']=sum(len(s['rows'])-len({canonical(r['japanese']) for r in s['rows']}) for g in groups for s in g['skills'])
    coverage['same_position_aliases_merged']=sum(len(r['alias_references']) for r in allrows)
    source_anomalies=[dict(cid=cid,row_id=r['row_id'],note=note) for r in allrows
                      for pattern,note in SOURCE_ANOMALIES.get(cid,()) if pattern in r['japanese']]
    denominator_notes=[dict(cid=cid,row_id=r['row_id'],note=note) for r in allrows
                       for pattern,note in DENOMINATOR_NOTES.get(cid,()) if pattern in r['japanese']]
    return dict(schema_version='card-page-pilot-1',cid=cid,basic=basic(data,cid),groups=groups,coverage=coverage,
                summary=metrics(coverage),implementation_status=INFERENCE_STATUS,
                sources=dict(input_root='声明的 --input-root',snapshot='cache_full_20261015_v3 + APK5.6.2',
                             task0_verdict=data.forward,baseline_registry=registry,old_to_new=mapping,
                             source_anomalies=source_anomalies,denominator_notes=denominator_notes,
                             baseline_evidence_roots=dict(
                                 root='output/card_comparison_cid30236/',
                                 note='30236基线answers[].evidence中的相对路径（含以../引用output/同层其他任务目录，'
                                      '如「barrier/README.md」「../boss_chain/type105/README.md」）均以上述目录为解析根；'
                                      '「skill43023600.text」「extra_ability_info.extra_abilities[].text」等非路径文本为说明性引用，不是文件指针')),
                reference_comparison=dict(local_layout='仅参考结构；不读取参考数值或图片作为数据',website_status='待主持/独立R1实际浏览对照',
                                          external_difference_note='网站一致/差异独立于证据等级；外部值不覆盖游戏原值'))
