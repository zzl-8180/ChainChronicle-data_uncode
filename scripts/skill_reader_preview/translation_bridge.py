"""Traceable sentence-level Chinese without importing reference game numbers."""
from collections import Counter, defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
import json
import re
import unicodedata
from hashlib import sha256

from wording import description, terms, EXACT

def canonical(s):
    s=re.sub(r'^\s*【[^】]*】', '', s.strip(' ◆\n\r\t'))
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC',s)).rstrip('。')

def numbers(s):
    return Counter(re.findall(r'\d+(?:\.\d+)?',unicodedata.normalize('NFKC',s)))

# This gate is a documented lexical check, not a claim of human review.
TOKENS=(
    ('クリティカル発生率',('暴击率',)),('クリティカル威力',('暴击威力',)),
    ('攻撃力',('攻击力',)),('防御力',('防御力','防御')),('移動速度',('移动速度',)),
    ('攻撃間隔',('攻击间隔',)),('攻撃速度',('攻击速度',)),
    ('遠距離',('远距离','远程')),('近接',('近战','近身','近距离')),
    ('サブパーティ',('后备队伍',)),('メインパーティ',('主要队伍',)),
    ('敵',('敌',)),('味方',('我方','队员','队友','己方','敌我')),('自身',('自身','自己','含自身')),
    ('ダメージ',('伤害',)),('回復',('回复','恢复','治疗','解除')),
    ('マナ',('法珠',)),('万象',('万象',)),('時の楔',('时之楔',)),
    ('暗闇',('暗盲',)),('スロウ',('缓速',)),('ダウン',('眩晕',)),
    ('弾き飛ば',('弹飞',)),('転倒',('击倒','倒地')),('毒',('毒',)),
    ('封印',('封印',)),('凍結',('冻结','冰冻')),('衰弱',('衰弱',)),
    ('一定時間',('一定时间','暂时','持续时间','一段时间')),('一定間隔',('固定间隔','一定间隔','每隔','周期性')),
    ('上限を超え',('超过HP上限','超上限','超过上限','超出上限')),
    ('地形',('地形',)),('砂漠',('沙漠',)),('夜',('夜',)),
    ('通常攻撃',('通常攻击',)),('通常回復',('通常回复','通常恢复')),
    ('範囲',('范围',)),('貫通',('贯穿','贯通','穿透')),
    ('前方',('前方',)),('後方',('后方',)),('直線',('直线',)),
    ('バリア',('防护罩',)),('スクラップ',('废料','废铁','废品')),
    ('炎',('火','炎')),('氷',('冰',)),('Chain',('Chain',)),('WAVE',('WAVE',)),
    ('必殺',('必杀',)),('共鳴',('共鸣',)),('反響',('反响',)),('戦場',('战场',)),
    ('自身以外',('自身以外','除自身','自己以外','自身之外','不含自身')),
    ('自身を含む',('含自身','包含自身','包括自身','自身在内','自身和','自身及')),
    ('一定確率',('概率','几率')),('敵陣',('敌方阵地','敌阵')),('自陣',('我方阵地','己方阵地','自阵','己阵')),
    ('徐々に',('逐渐','缓缓','缓慢')),('のみ',('仅','只','限','最多')),
)

def issues(jp,zh):
    out=[]
    if not zh:out.append('missing_translation');return out
    if re.search('[ぁ-ゖァ-ヺ]',zh):out.append('untranslated_kana')
    if numbers(jp)!=numbers(zh):out.append('literal_numbers_differ')
    # Matching digits alone cannot distinguish "survive once" from "1 HP".
    jpn=unicodedata.normalize('NFKC',jp)
    zhn=unicodedata.normalize('NFKC',zh)
    for value in re.findall(r'(\d+)回(?!復)',jpn):
        if not re.search(re.escape(value)+r'\s*(?:次|回|连击|連擊|段)',zhn):out.append('count_unit_missing:'+value+'回')
    for value in re.findall(r'(\d+)人',jpn):
        if not re.search(re.escape(value)+r'\s*(?:名|人)',zhn):out.append('person_unit_missing:'+value+'人')
    for value,kind in re.findall(r'(\d+(?:st|nd|rd|th)\s*Chain)(以上|以下)',jpn):
        value=re.sub(r'\s+','',value)
        if value+kind not in re.sub(r'\s+|或','',zhn):out.append('chain_bound_missing:'+value+kind)
    # Skill-kind headers are displayed separately and may be omitted in prose.
    jp=re.sub(r'^\s*【[^】]*】','',jp)
    for token,options in TOKENS:
        if token in jp and not any(x in zh for x in options):out.append('missing_semantic:'+token)
    for token,options in TOKENS[:6]:
        if token=='防御力':options=('防御力',)
        if token not in jp and any(x in zh for x in options):out.append('added_effect:'+token)
    if '解除' in zh and not re.search('解除|回復|治[すし]',jp):out.append('added_status_cure')
    for size,word in [('大','大伤害'),('中','中伤害'),('小','小伤害')]:
        if size+'ダメージ' in jp and word not in zh and size+'额伤害' not in zh:out.append('missing_damage_size:'+size)
    negative = '不|无法|不能|免疫|无效|无'
    if 'しか' in jp:negative += '|只|最多|至多'
    if ('できない' in jp or '発動しない' in jp or 'ならない' in jp) and not re.search(negative,zh):out.append('missing_negation')
    if '一定時間' not in jp and '永久' in zh:out.append('added_permanence')
    if '大ダメージ' in jp and '大范围伤害' in zh:out.append('damage_vs_area')
    if '原地' in zh and not re.search('その場|現在位置|自分の位置',jp):out.append('invented_position')
    return out

def equivalent_wording(zh):
    """Collapse only stylistic synonyms; keep amounts, order and conditions."""
    for old,new in [('随后','之后'),('此外','另外'),('全体','全部'),('所有','全部'),
                    ('几率','概率'),('提升','增加'),('上升','增加'),('提高','增加'),
                    ('回复','恢复'),('缓缓','逐渐'),('只需消耗','仅需'),
                    ('所需要','所需'),('所需要的','所需'),('所需的','所需'),
                    ('下次','下一次'),('自身处于','自身在'),('时可以','时可'),
                    ('给予','对'),('受到的伤害','所受伤害')]:zh=zh.replace(old,new)
    zh=zh.replace('造成','').replace('的','')
    return re.sub(r'[\s。；，、,;◆<>≪≫《》]+','',zh)

def body_copy(zh):
    return re.sub(r'^\s*【[^】]*】','',terms(zh).strip()).lstrip('◆ ')

HEADER_TERMS={'共鳴アビリティ':'共鸣能力','共鳴必殺':'共鸣必杀','超共鳴必殺':'超共鸣必杀',
 '絆共鳴必殺':'羁绊共鸣必杀','連撃':'连击','領域':'领域','英雄技':'英雄技','超必殺':'超必杀',
 '超必殺技':'超必杀技','返還':'返还','反響':'反响','付加':'附加','設置':'设置','無敵':'无敌',
 '地形変化':'地形变化','地形':'地形','搭乗':'搭乘','搭乗中':'搭乘中','変身':'变身','変身中':'变身中',
 '変身後':'变身后','多重詠唱':'多重咏唱','決戦必殺':'决战必杀','決戦号令':'决战号令','敵陣':'敌方阵地',
 '自陣':'我方阵地','自陣最後列以外':'我方阵地最后排以外','自陣最後列':'我方阵地最后排',
 '最後列':'最后排','溜め':'蓄力','歌':'歌唱','舞':'舞蹈','覚醒':'觉醒','超過':'超额',
 'ランダム':'随机','砲撃':'炮击','異神解放':'异神解放','強化中':'强化中','強化':'强化',
 '連舞':'连舞','斬撃':'斩击','おじゃまぷよ':'干扰噗哟'}

def header_text(tag):
    result=[]
    for part in tag.split('/'):
        if part in HEADER_TERMS:result.append(HEADER_TERMS[part]);continue
        m=re.fullmatch(r'(\d+)回のみ',part)
        if m:result.append(f'仅{m[1]}次');continue
        m=re.fullmatch(r'(\d+(?:st|nd|rd|th)Chain)(以上|以下)',part)
        if m:result.append(m[1]+('或以上' if m[2]=='以上' else '或以下'));continue
        m=re.fullmatch(r'マナ(\d+)(以上|以下)',part)
        if m:result.append(('至少' if m[2]=='以上' else '至多')+m[1]+'颗法珠');continue
        return None
    return '/'.join(result)

class Translator:
    def __init__(self,root):
        self.root=Path(root)
        self.audit=[]
        self.cache={}
        self.refs=defaultdict(list)
        self.reviewed={}
        self.reviewed_sources={}
        reviewed_path=Path(__file__).parent/'semantic_sentences.json'
        self.semantic=json.loads(reviewed_path.read_text(encoding='utf8')) if reviewed_path.exists() else None
        for filename in ('reviewed_sentences.json','extra_reviewed_sentences.json','audited_sentence_fixes.json'):
            path=Path(__file__).parent/filename
            if path.exists():
                for jp,zh in json.loads(path.read_text(encoding='utf-8')).items():
                    self.reviewed[canonical(jp)]=zh
                    self.reviewed_sources[canonical(jp)]=filename
        self.reviewed_templates={}
        for jp,zh in self.reviewed.items():
            zh=body_copy(zh)
            ns=re.findall(r'\d+(?:\.\d+)?',jp)
            if ns and ns==re.findall(r'\d+(?:\.\d+)?',zh) and not issues(jp,zh):
                self.reviewed_templates[re.sub(r'\d+(?:\.\d+)?','{n}',jp)]=(re.sub(r'\d+(?:\.\d+)?','{n}',zh),self.reviewed_sources[jp])
        auditpath=read_path(self.root/'output/character_skills/reader_full_20261106/audit/reference_pairs.json', root=self.root)
        ref=json.loads(auditpath.read_text(encoding='utf-8'))
        for jp,p in ref['pairs'].items():self.refs[canonical(jp)].append(p)
        for conflict in ref['conflicts']:
            for p in conflict['candidates']:self.refs[canonical(conflict['japanese'])].append(p)
        self.templates=defaultdict(list)
        for jp,ps in self.refs.items():
            for p in ps:
                zh=body_copy(p['textZh'])
                if issues(jp,zh):continue
                ns=re.findall(r'\d+(?:\.\d+)?',jp)
                zs=re.findall(r'\d+(?:\.\d+)?',zh)
                if ns and ns==zs:
                    self.templates[re.sub(r'\d+(?:\.\d+)?','{n}',jp)].append((re.sub(r'\d+(?:\.\d+)?','{n}',zh),p['source']))

    def translate(self,jp):
        tag=re.match(r'^\s*【([^】]+)】',jp)
        body=jp[tag.end():] if tag else jp
        # The frozen unit strips exactly one leading header. Passing the
        # already-stripped body would discard a second adjacent header.
        result=self._translate_body(jp if self.semantic else body)
        if result['translationStatus']=='pending':return result
        if tag:
            header=header_text(tag[1])
            if header is None:return {'textZh':'中文待核对','translationStatus':'pending','translationSource':None,'translationChecks':['untranslated_skill_header']}
            result['textZh']='【'+header+'】'+result['textZh']
        problems=issues(jp,result['textZh'])
        if result.get('semanticReview'):
            # A lexical heuristic may flag approved proper names, synonyms or
            # reordered fractions. Retain its diagnostics; compare to the exact
            # reviewed sentence in verify_full instead of treating it as review.
            if numbers(jp)!=numbers(result['textZh']):raise ValueError('Reviewed translation changed literal numbers: '+jp)
            result['translationChecks']=problems
            return result
        if problems:return {'textZh':'中文待核对','translationStatus':'pending','translationSource':None,'translationChecks':problems}
        return result

    def _translate_body(self,jp):
        key=canonical(jp)
        if key in self.cache:return dict(self.cache[key])
        if self.semantic:
            values=[]
            def slot(m):
                values.append(m[0]);return '{n'+str(len(values)-1)+'}'
            pattern=re.sub(r'\d+(?:\.\d+)?',slot,key)
            uid=sha256(pattern.encode()).hexdigest()[:16]
            record=self.semantic['units'].get(uid)
            if record and record['jpPattern']==pattern:
                zh=re.sub(r'\{n(\d+)\}',lambda m:values[int(m[1])],record['zhPattern'])
                result={'textZh':zh,'translationStatus':'reviewed',
                        'translationSource':'semantic_review/'+record['packet'],
                        'translationNote':record.get('displayNote',''),
                        'semanticReview':{'unitId':uid,'packet':record['packet'],'verdict':record['verdict'],
                                          'inputHash':record['inputHash'],'resultHash':record['resultHash']},
                        'translationChecks':[]}
                self.cache[key]=result;return dict(result)
            raise ValueError('Description absent from completed review: '+jp)
        from common_grammar import translate
        options=[]
        if key in self.reviewed:options.append((self.reviewed[key],'reviewed',self.reviewed_sources[key]))
        direct=description(jp,'')
        if direct:options.append((direct,'reviewed','wording.py'))
        grammar=translate(unicodedata.normalize('NFKC',jp))
        reference_options=[]
        for p in self.refs.get(key,[]):reference_options.append((body_copy(p['textZh']),'template',p['source']))
        ns=iter(re.findall(r'\d+(?:\.\d+)?',key))
        sk=re.sub(r'\d+(?:\.\d+)?','{n}',key)
        if sk in self.reviewed_templates:
            pattern,source=self.reviewed_templates[sk]
            ns=iter(re.findall(r'\d+(?:\.\d+)?',key))
            options.append((re.sub(r'\{n\}',lambda m:next(ns),pattern),'template',source+' (literal-number template)'))
        if grammar:options.append((grammar,'template','common_grammar.py'))
        for pattern,source in self.templates.get(sk,[]):
            ns=iter(re.findall(r'\d+(?:\.\d+)?',key))
            reference_options.append((re.sub(r'\{n\}',lambda m:next(ns),pattern),'template',source+' (literal-number template)'))
        viable={equivalent_wording(zh):(zh,status,source) for zh,status,source in reference_options if not issues(jp,zh)}
        # Conflicting wording is not resolved by picking the first file found.
        if len(viable)==1:options.extend(viable.values())
        rejected=[]
        for zh,status,source in options:
            zh=body_copy(zh)
            if not zh.endswith(('。','！','？')):zh+='。'
            problems=issues(jp,zh)
            if not problems:
                result={'textZh':zh,'translationStatus':status,'translationSource':source,'translationChecks':'literal_numbers_and_semantic_terms'}
                self.cache[key]=result;return dict(result)
            rejected.append({'source':source,'issues':problems})
        if len(viable)>1:rejected.append({'source':'reference candidates','issues':['conflicting_translations'],'candidateCount':len(viable)})
        result={'textZh':'中文待核对','translationStatus':'pending','translationSource':None,'translationChecks':rejected or ['no_exact_sentence_candidate']}
        self.cache[key]=result
        return dict(result)

    def record(self,row,translated):
        self.audit.append({'rowId':row['row_id'],'cid':row['cid'],'original':row['japanese'],**translated})

    def write_audit(self,out):
        out.mkdir(parents=True,exist_ok=True)
        with (out/'translation_rows.jsonl').open('w',encoding='utf-8') as f:
            for r in self.audit:f.write(json.dumps(r,ensure_ascii=False)+'\n')
        summary={'rows':len(self.audit),'byStatus':dict(Counter(r['translationStatus'] for r in self.audit)),
                 'uniqueSentences':len({r['original'] for r in self.audit}),'uniquePending':len({r['original'] for r in self.audit if r['translationStatus']=='pending'})}
        pending={}
        for row in self.audit:
            if row['translationStatus']!='pending':continue
            jp=row['original']
            if jp not in pending:pending[jp]={'original':jp,'count':0,'checks':row['translationChecks']}
            pending[jp]['count']+=1
        (out/'translation_pending_sentences.json').write_text(json.dumps(sorted(pending.values(),key=lambda r:-r['count']),ensure_ascii=False,indent=2),encoding='utf-8')
        (out/'translation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        return summary
