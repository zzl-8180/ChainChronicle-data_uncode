# -*- coding: utf-8 -*-
"""C12-P3 ``charainfo.skilltext`` **同卡同文档位同文镜像**（buff 5/3 槽＋敌 debuff 3 槽）：候选实现。

任务卡 ``docs/tasks/20261031-c12-p3-skilltext-mirror.md``；选题预检
``output/character_skills/c12_p3_selection_20261031/selection_report.md``（PASS；冻结 88 卡
123 行／459 答案／459 效果）；同族先例 ``card_page_inference_c10_p1_mirror.py``
（t27/t64 单键镜像）、``card_page_inference_c11_p1_t114.py``（t114 镜像）。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；正式 pages、
``rules.json``、``effect_ledger.py`` 的映射表均未改动；本阶段不运行正式全库生成。

本批做什么、不做什么
--------------------
本批**不是**新数值发现：123 条 skilltext 行的句面与**同卡同标签档位行**（``patternN``，
块首标签同为「【共鳴必殺…】」）逐字相同，档位行**已经**有 8 个规则键里对应槽位的答案。
本批只把这些 skilltext 行上**尚缺**的槽位按「同卡同档位行同键同字段同原值」归位：

* buff 段（句面「味方全体の⟨属性⟩が一定時間上がる」）：``bossskill|13|/skillparam1``
  （攻撃力）、``/skillparam2``（防御力）、``/skillparam6``（移動速度）、
  ``skilllist|2012|/param4``（クリティカル発生率）、``/param5``（クリティカル威力）。
* debuff 段（句面「同時に攻撃した敵の⟨属性⟩が（一定時間）下がる」）：
  ``skilllist|2003|/param7``（攻撃力）、``/param8``（移動速度）、``/param9``（防御力）。

**只出句面点名的槽**：句面属性表逐字解析（``と`` 连接），任何不在上表的属性
（回復／攻撃速度／状態異常 等）→ 整行拒绝，不做「答一半、留一半」。**时长永不重答**：
buff 行已有的 ``13|/skillparam3``、debuff 行已有的 ``2003|/param0`` 是 B18 批的时长单项
部分答案，本模块只核其记录/字段/原值身份，不新增、不改写；句面无「一定時間」的行
（30108 debuff）**不得**补时长。

为什么不是「同记录重复答题」
--------------------------
镜像来源是**同卡另一条记录**（档位行的 bosspattern→bossskill／s_ability 链），不是本行
已消费的记录；本行这些槽位批前没有任何答案，账本效果仍为 ``unresolved``（D10 逐行断言
「未解类型集合 == 本批镜像键类型集合」）。

档位标签与 super 兄弟（为什么不能只按文本选值）
--------------------------------------------
本行文本块的块首标签决定它属【共鳴必殺】还是【超共鳴必殺】；同卡**同文**的另一档位行原值
必然不同（例：base 0.6/0.3/0.3 对 super 0.75/0.375/0.375；debuff base p7 −0.3 对
super −0.375）。故 D5 要求同文 super 档位行**存在**且镜像键上**至少一个原值不同**——
「按句面文本选值」不足以定值，必须按块标签＋同卡唯一同标签同文行归属。

**仍不宣称**已解析 Boss 模式下哪个 pattern 被选中（这正是账本 ``S7_same_cond_alt_t13``
至今未决的原因）：本批保留 S7、保留 b6/b8/b10 hint、不写实际装载、不写行完整。

原记录链（逐位核，不按数字跨表判记录）
------------------------------------
* 档位行 ``record_id`` = CACHE ``bosspattern.patternid``（唯一命中）；``skillid0..N`` 从 0
  连续、每个子记录在 ``bossskill`` 全表唯一命中。
* 13／2012 侧（buff）：恰 1 条 ``skillid0 == 13`` 子记录，其 ``skillparam1/2/6`` 与本批
  原值逐位相等、``skillparam3 > 0``（时长旁证）；句面主张クリティカル 的行再要求该 13
  记录的 ``s_ability`` 指向 ``skilllist`` 且 ``ability == 2012``，``param4/param5`` 逐位相等。
* 2003 侧（debuff）：档位行**全部** ``skillidN`` 子记录中 ``s_ability`` 指向 ``skilllist``
  且 ``ability == 2003`` 的记录恰 1 条，``param7/8/9`` 逐位相等。**实测校正（与任务卡措辞
  的差异，明确披露）**：这 39 行的 2003 记录**不是**都挂在 ``skillid0 == 13`` 子记录下——
  其父子记录类型实测为 105／110／116／22／55／76（13 只有 2012 中继那一路）。故本模块对
  2003 采用「档位行任一子记录的 ``s_ability``」判据（与预检 §5.1 第 4 条的实核口径一致），
  不虚构一条 13→2003 的边；3 行（4316／30105／30111 debuff）档位行根本没有 13 子记录。
* 只读 CACHE 层；不读 APK 同名表，不合并命名空间（2012 两域值分歧仅在 CACHE 域取值）。

一行一槽一答案
-------------
D10 用账本 ``effect_ledger.analyze_row``（纯函数、只读）断言：句面未解效果类型集合
**恰等于**本批镜像键效果类型集合，且每个主张类型在该行只出现一次 → 一条答案恰关闭一个
``unresolved``，不产生「同主张双值行」S4。若句面出现本批不承载的未解主张（例：クリティ
カル但无 2012 载体），整行拒绝而不是少答。

接口
----
``tables(data)`` / ``clone_tables(tab)``                CACHE 主表只读索引（可注入/深拷贝）。
``tier_label(text)`` / ``parse_clause(text)``           块首标签与句面属性表（逐字）。
``evaluate(data, cid, row, *, groups=None, tab=None, ledger=True)``   单行判定（不写入）。
``build_answers(data, cid, row, res, tab=None)``        本行答案对象（数量＝句面槽数）。
``apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None)``  正式页消费（候选未接线）。

批次边界由调用方**显式声明**：``scope_cids`` 缺省 ``None`` → 一行都不处理
（``NO_SCOPE_DECLARED``）；不在声明集合内的卡 → ``CID_NOT_IN_DECLARED_SCOPE``（零写入）。
保护／禁推卡 20234／30102／30236／30239 在模块内硬拒绝。
"""
from __future__ import annotations

import json
import math
import re
import struct
import unicodedata
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path

MODULE_VERSION = 'c12_p3_skilltext_mirror_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 本批证据 scope（写进答案 ``evidence_scope`` 与行级 scope 列表）。
SCOPE = 'TEMPLATE_BATCH12_P3_SKILLTEXT_MIRROR'
#: 结构判定自身 scope（只出现在 answer binding 里，供逐行溯源）。
STRUCTURE_SCOPE = 'C12_P3_SKILLTEXT_MIRROR_STRUCTURE_20261031'
#: 答案内 binding 的键名（**不**写行级 ``inference_*`` 顶层键：那会变成账本 promotion_key）。
BINDING_KEY = 'c12_p3_skilltext_mirror_binding'

#: 行所在层与表（本批只认 CACHE ``charainfo.skilltext``）。
TABLE = 'charainfo'
LAYER = 'CACHE'
REF_FIELD = 'skilltext'
SOURCE_KEY = 'CACHE/charainfo.data5.json.raw'
BOSS_TABLE = 'bossskill'
BOSS_SOURCE_KEY = 'CACHE/bossinfo.data5.json.raw'
SKILLLIST_SOURCE_KEY = 'CACHE/skilllist.data5.json.raw'
PATTERN_TABLE = 'bosspattern'
#: CACHE 解码主表目录（与预检、C11／C12-P1／P2 同源快照）。
CACHE_DIR = 'output/cache_full_20261015_v3/decoded'
SNAPSHOT_ID = 'cache_full_20261015_v3'

#: 保护／禁推卡：判定前硬拒绝（30102 禁推卡；30236／30239 保护卡；20234 既有边界）。
ZERO_TOUCH_CIDS = frozenset({20234, 30102, 30236, 30239})

BASE_LABEL = '【共鳴必殺'
SUPER_LABEL = '【超共鳴必殺'
BUFF_PREFIX = '味方全体の'
BUFF_SUFFIX = 'が一定時間上がる。'
DEBUFF_PREFIX = '同時に攻撃した敵の'
DEBUFF_SUFFIX = 'が一定時間下がる。'
DEBUFF_NODUR_SUFFIX = 'が下がる。'
#: 同块其它句子里的状态异常条款：句面一旦含该词即拒绝（本批不得顺带回答）。
ABNORMAL_WORD = '状態異常'

_BUFF_RE = re.compile(r'^.*?' + re.escape(BUFF_PREFIX) + r'(.+?)' + re.escape(BUFF_SUFFIX) + r'$')
_DEBUFF_RE = re.compile(r'^.*?' + re.escape(DEBUFF_PREFIX) + r'(.+?)'
                        + re.escape(DEBUFF_SUFFIX) + r'$')
_DEBUFF_NODUR_RE = re.compile(r'^.*?' + re.escape(DEBUFF_PREFIX) + r'(.+?)'
                              + re.escape(DEBUFF_NODUR_SUFFIX) + r'$')

#: 槽位表：句面属性名 → 规则键／记录表／能力号／字段／账本效果类型／值文关键词。
#: 8 个键全部是 ``rules.json`` 已确认规则；本模块不新增任何规则键。
SLOT = {
    '攻撃力': dict(name='攻撃力', rule_key='bossskill|13|/skillparam1', table='bossskill',
                   ability=13, field='/skillparam1', param='skillparam1',
                   effect_type='攻撃力', keyword='局部攻击增益', direction=1),
    '防御力': dict(name='防御力', rule_key='bossskill|13|/skillparam2', table='bossskill',
                   ability=13, field='/skillparam2', param='skillparam2',
                   effect_type='防御力', keyword='guard', direction=1),
    '移動速度': dict(name='移動速度', rule_key='bossskill|13|/skillparam6', table='bossskill',
                     ability=13, field='/skillparam6', param='skillparam6',
                     effect_type='移動速度', keyword='moveRate', direction=1),
    'クリティカル発生率': dict(name='クリティカル発生率', rule_key='skilllist|2012|/param4',
                              table='skilllist', ability=2012, field='/param4', param='param4',
                              effect_type='クリティカル発生率', keyword='暴击率', direction=1),
    'クリティカル威力': dict(name='クリティカル威力', rule_key='skilllist|2012|/param5',
                             table='skilllist', ability=2012, field='/param5', param='param5',
                             effect_type='クリティカル威力', keyword='暴击伤害系数', direction=1),
    '敵攻撃力': dict(name='攻撃力', rule_key='skilllist|2003|/param7', table='skilllist',
                     ability=2003, field='/param7', param='param7',
                     effect_type='攻撃力', keyword='受击目标本项攻击项', direction=-1),
    '敵移動速度': dict(name='移動速度', rule_key='skilllist|2003|/param8', table='skilllist',
                       ability=2003, field='/param8', param='param8',
                       effect_type='移動速度', keyword='移动因子', direction=-1),
    '敵防御力': dict(name='防御力', rule_key='skilllist|2003|/param9', table='skilllist',
                     ability=2003, field='/param9', param='param9',
                     effect_type='防御力', keyword='受伤量项', direction=1),
}
#: buff 段句面属性 → 槽（顺序即句面顺序）；属性表里出现其它名字即整行拒绝。
BUFF_SLOTS = {
    '攻撃力': SLOT['攻撃力'], '防御力': SLOT['防御力'], '移動速度': SLOT['移動速度'],
    'クリティカル発生率': SLOT['クリティカル発生率'], 'クリティカル威力': SLOT['クリティカル威力'],
}
#: debuff 段句面属性 → 槽。
DEBUFF_SLOTS = {
    '攻撃力': SLOT['敵攻撃力'], '防御力': SLOT['敵防御力'], '移動速度': SLOT['敵移動速度'],
}
#: 时长槽（**只作既有答案身份核对，永不新增**）。
DURATION_SLOT = {
    'buff': dict(rule_key='bossskill|13|/skillparam3', table='bossskill', ability=13,
                 field='/skillparam3', param='skillparam3'),
    'debuff': dict(rule_key='skilllist|2003|/param0', table='skilllist', ability=2003,
                   field='/param0', param='param0'),
}
#: 8 个镜像键（与规则族一一对应；用于静态自检与跨批零重叠）。
MIRROR_KEYS = tuple(s['rule_key'] for s in SLOT.values())
#: 值文禁写项（预检 §4 语义纪律）。
FORBIDDEN_WORDS = ('面板', '×1.1', '攻击力+10%', '最终伤害', '最终HP')
EVIDENCE = [
    'output/character_skills/c12_p3_selection_20261031/selection_report.md',
    'output/character_skills/c12_p3_selection_20261031/validate.py',
    'output/character_skills/profiles/rules.json',
    'output/boss_heal/field_dictionary.json',
    'output/ordinary_effects/ability2012/README.md',
    'output/ordinary_effects/ability2003/README.md',
]
LIMIT = ('原值为既有已确认规则下的输入系数／加算增量，不是面板值、最终伤害、固定防御实际量或'
         '最终移动速度；「本行 skilltext 句面 ↔ 同卡档位行记录」为结构证据（同卡同文＋同块'
         '标签＋唯一同标签同文档位行＋super 同文异值），关联＝推断；Boss 模式下的 pattern '
         '选取维度未解析（S7_same_cond_alt_t13 保留）；不写实际装载、不写行完整；2003 触发'
         '口径照规则：仅 Skill 型着弹（Normal/Critical 不触发）。')

_TABLES = {}


# ---------------------------------------------------------------- 基础工具
def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def canon(text):
    """NFKC＋去空白（句面/块文本比较口径；与预检 ``nrm`` 一致）。"""
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def tier_label(text):
    """文本块的档位标签：只认块首词形，不从值大小或句面内容推断。"""
    core = canon(text)
    if core.startswith(canon(SUPER_LABEL)):
        return 'SUPER'
    if core.startswith(canon(BASE_LABEL)):
        return 'BASE'
    return None


def num_state(value, present=True):
    """缺失／null／布尔／非有限／有限 分开标注（不把任何一档补成 0；不在此判符号）。"""
    if not present:
        return 'MISSING'
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'NON_FINITE'
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 'NON_FINITE'
    if not math.isfinite(f):
        return 'NON_FINITE'
    return 'FINITE'


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def _num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return ('%.6f' % f).rstrip('0').rstrip('.')


def parse_clause(text):
    """逐字解析句面属性表；返回 dict(kind, attrs, duration_claim) 或 None。

    只认三种逐字模板（前缀／后缀固定，属性以 ``と`` 连接）：
      * ``…味方全体の⟨A⟩と⟨B⟩…が一定時間上がる。``（buff）
      * ``…同時に攻撃した敵の⟨A⟩と⟨B⟩…が一定時間下がる。``（debuff）
      * ``…同時に攻撃した敵の⟨A⟩と⟨B⟩…が下がる。``（debuff，**无时长主张**）
    前缀在全句只允许出现 1 次（防止跨子句误取属性表）。
    """
    t = canon(text)
    if not t:
        return None
    m = _BUFF_RE.match(t)
    if m:
        if t.count(canon(BUFF_PREFIX)) != 1:
            return None
        return dict(kind='buff', attrs=[a for a in m.group(1).split('と') if a],
                    duration_claim=True, slotmap=BUFF_SLOTS)
    m = _DEBUFF_RE.match(t)
    if m:
        if t.count(canon(DEBUFF_PREFIX)) != 1:
            return None
        return dict(kind='debuff', attrs=[a for a in m.group(1).split('と') if a],
                    duration_claim=True, slotmap=DEBUFF_SLOTS)
    m = _DEBUFF_NODUR_RE.match(t)
    if m:
        if t.count(canon(DEBUFF_PREFIX)) != 1:
            return None
        return dict(kind='debuff', attrs=[a for a in m.group(1).split('と') if a],
                    duration_claim=False, slotmap=DEBUFF_SLOTS)
    return None


# ---------------------------------------------------------------- 只读主表
def tables(data):
    """CACHE 解码主表（按 root 缓存；只读）。索引均为 ``id -> [(array_index, record)]``。"""
    root = Path(getattr(data, 'root', Path('.'))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = read_path(root / CACHE_DIR, root=root)
        need = [base / 'bossinfo.data5.json.raw', base / 'skilllist.data5.json.raw',
                base / 'charainfo.data5.json.raw']
        missing = [str(p) for p in need if not p.exists()]
        if missing:
            raise FileNotFoundError('CACHE 解码主表缺失: %s' % missing)
        boss = _read(need[0])['bossinfo']
        patterns, boss_skills = {}, {}
        for i, rec in enumerate(boss.get('bosspattern') or []):
            patterns.setdefault(rec.get('patternid'), []).append((i, rec))
        for i, rec in enumerate(boss.get('bossskill') or []):
            boss_skills.setdefault(rec.get('skillid'), []).append((i, rec))
        skilllist = {}
        for i, rec in enumerate(_read(need[1])['skilllist']):
            skilllist.setdefault(rec.get('skillid'), []).append((i, rec))
        chara = {}
        chara_all = _read(need[2])['charainfo']
        for i, rec in enumerate(chara_all):
            chara.setdefault(rec.get('cid'), []).append((i, rec))
        _TABLES[key] = dict(patterns=patterns, boss_skills=boss_skills,
                            skilllist=skilllist, chara=chara, chara_all=chara_all,
                            root=root)
    return _TABLES[key]


def clone_tables(tab):
    """深拷贝主表索引（反例用例在副本上篡改，不动只读缓存）。"""
    return {k: (v if k in ('root',) else json.loads(json.dumps(v, ensure_ascii=False)))
            for k, v in tab.items()}


def unique_hit(index, record_id):
    hits = index.get(record_id) or []
    if len(hits) != 1:
        return None, 'NOT_UNIQUE(%d)' % len(hits)
    return hits[0], None


def card_entries(groups):
    """``[(group_name, skill, row)]``（顺序即页面顺序；同 row_id 重复由调用方判）。"""
    out = []
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                out.append((group.get('group'), skill, row))
    return out


# ---------------------------------------------------------------- 记录链
def pattern_chain(tab, pattern_id):
    """档位行 bosspattern→skillidN→bossskill 链（唯一命中＋槽位从 0 连续）。"""
    hit, err = unique_hit(tab['patterns'], pattern_id)
    if err:
        return None, 'PATTERN_RECORD_%s' % err
    index, pattern = hit
    slots = [(i, pattern.get('skillid%d' % i)) for i in range(7)
             if pattern.get('skillid%d' % i) is not None]
    if [i for i, _ in slots] != list(range(len(slots))):
        return None, 'PATTERN_SLOT_NOT_CONTIGUOUS'
    children = []
    for slot_index, skill_id in slots:
        child_hit, child_err = unique_hit(tab['boss_skills'], skill_id)
        if child_err:
            return None, 'BOSSSKILL_%s_%s' % (skill_id, child_err)
        child_index, child = child_hit
        children.append(dict(slot='skillid%d' % slot_index, skillid=skill_id,
                             index=child_index, type=child.get('skillid0'), record=child))
    return dict(pattern_id=pattern_id, pattern=pattern, index=index, children=children), None


def skilllist_record(tab, skill_id):
    if not isinstance(skill_id, int) or isinstance(skill_id, bool):
        return None, 'SKILLLIST_ID_INVALID'
    hit, err = unique_hit(tab['skilllist'], skill_id)
    if err:
        return None, 'SKILLLIST_%s_%s' % (skill_id, err)
    return hit, None


def sign_ok(slot, raw):
    """句面方向守卫：buff/crit 为「上がる」需原值 >0；debuff p7/p8 为下降贡献（<0），
    p9 为受伤量项上升（>0，规则口径：「正值＝受伤量因子上升——正文写作防御力下がる」）。"""
    f = float(raw)
    if slot['rule_key'] == 'skilllist|2003|/param9':
        return f > 0
    if slot['direction'] < 0:
        return f < 0
    return f > 0


# ---------------------------------------------------------------- 单行判定
def _reject(code, gates, detail=None):
    return {'accepted': False, 'rejection': code, 'detail': detail, 'gates': gates}


def evaluate(data, cid, row, *, groups=None, tab=None, ledger=True):
    """单行判定（不写入）。``groups`` 为该卡页面 ``groups``（同文档位行/同文 super 兄弟来源）。

    判定顺序（任一不符即拒，不猜、不跨卡取行）：
      D0 零触碰卡；D1 行身份＋CACHE 层＋charainfo 文本链；D2 句面属性表；
      D3 块标签；D4 同标签唯一同文档位行；D5 同文 super 兄弟存在；
      D6 档位行镜像键答案（同键同字段同原值、「推断/推断」）；D7 super 原值至少一处不同；
      D8 档位行原记录链（13／2012／2003 逐位）；D9 批前未答＋时长答案身份；
      D10 账本效果 1:1（未解类型集合 == 镜像键类型集合，一类型一次）。
    """
    gates = {'cid': cid, 'row_id': (row or {}).get('row_id') if isinstance(row, dict) else None}
    if isinstance(cid, bool) or not isinstance(cid, int):
        return _reject('CID_INVALID', gates)
    if cid in ZERO_TOUCH_CIDS:
        return _reject('ZERO_TOUCH_CID', gates)
    if not isinstance(row, dict) or not row.get('row_id'):
        return _reject('ROW_INVALID', gates)
    tab = tab or tables(data)
    entries = card_entries(groups)
    if not entries:
        return _reject('GROUPS_REQUIRED', gates)
    mine = [e for e in entries if e[2] is row]
    if len(mine) != 1:
        same_id = [e for e in entries if e[2].get('row_id') == row.get('row_id')]
        if len(same_id) > 1:
            return _reject('ROW_ID_DUPLICATE', gates)
        if not same_id:
            return _reject('ROW_NOT_IN_GROUPS', gates)
        mine = same_id
    group_name, skill, row = mine[0]

    # ---- D1 行身份＋层＋charainfo 文本链
    if group_name != 'special_move' or row.get('group') != 'special_move':
        return _reject('GROUP_MISMATCH', gates)
    if row.get('cid') != cid:
        return _reject('CID_MISMATCH', gates)
    if str(row.get('reference_field') or '') != REF_FIELD:
        return _reject('ROW_REFERENCE_FIELD_DRIFT', gates)
    if str(skill.get('reference_field') or '') != REF_FIELD:
        return _reject('SKILL_REFERENCE_FIELD_DRIFT', gates)
    if skill.get('table') != TABLE or skill.get('layer') != LAYER:
        return _reject('SKILL_TABLE_LAYER_DRIFT', gates)
    if skill.get('record_id') != cid:
        return _reject('SKILL_RECORD_ID_DRIFT', gates)
    src = skill.get('source') or {}
    if src.get('layer') != LAYER or src.get('source_key') != SOURCE_KEY:
        return _reject('SKILL_SOURCE_DRIFT', gates)
    rsrc = row.get('source') or {}
    if rsrc.get('layer') != LAYER or rsrc.get('source_key') != SOURCE_KEY:
        return _reject('ROW_SOURCE_DRIFT', gates)
    if str(rsrc.get('field') or '') != '/skilltext':
        return _reject('ROW_SOURCE_FIELD_DRIFT', gates)
    pointer = re.fullmatch(r'/charainfo/(\d+)', str(rsrc.get('json_pointer') or ''))
    if not pointer:
        return _reject('CHARAINFO_POINTER_MISSING', gates)
    chara_hit, chara_err = unique_hit(tab['chara'], cid)
    if chara_err:
        return _reject('CHARAINFO_RECORD_%s' % chara_err, gates)
    chara_index, chara = chara_hit
    gates['charainfo'] = {'index': chara_index, 'cid': chara.get('cid')}
    if chara_index != int(pointer.group(1)):
        return _reject('CHARAINFO_POINTER_DRIFT', gates,
                       {'pointer': int(pointer.group(1)), 'index': chara_index})
    full = chara.get('skilltext') or ''
    if not canon(full):
        return _reject('CHARAINFO_TEXT_MISSING', gates)
    if canon(full) != canon(skill.get('original_text')):
        return _reject('CHARAINFO_TEXT_DRIFT', gates)
    if canon(row.get('japanese')) not in canon(full):
        return _reject('ROW_TEXT_NOT_IN_CHARAINFO', gates)
    if canon(row.get('context_text')) != canon(full):
        return _reject('CONTEXT_TEXT_DRIFT', gates)

    # ---- D2 句面属性表（只认逐字模板；状态异常条款整行拒绝）
    if ABNORMAL_WORD in canon(row.get('japanese')):
        return _reject('ABNORMAL_CLAUSE', gates)
    clause = parse_clause(row.get('japanese'))
    if clause is None:
        return _reject('CLAUSE_UNSUPPORTED', gates)
    attrs = clause['attrs']
    gates['sentence'] = {'kind': clause['kind'], 'attrs': list(attrs),
                         'duration_claim': clause['duration_claim']}
    if not attrs:
        return _reject('CLAUSE_NO_ATTRIBUTE', gates)
    if len(set(attrs)) != len(attrs):
        return _reject('CLAUSE_ATTRIBUTE_DUPLICATE', gates, {'attrs': attrs})
    unmapped = [a for a in attrs if a not in clause['slotmap']]
    if unmapped:
        return _reject('ATTRIBUTE_UNSUPPORTED', gates, {'attrs': unmapped})
    claim = [clause['slotmap'][a] for a in attrs]
    gates['claim_keys'] = [s['rule_key'] for s in claim]

    # ---- D3 块标签（本行／本 skill 块首都必须是【共鳴必殺】而非【超共鳴必殺】）
    if tier_label(skill.get('original_text')) != 'BASE':
        return _reject('TIER_NOT_BASE', gates,
                       {'skill_label': tier_label(skill.get('original_text'))})
    if tier_label(row.get('context_text')) != 'BASE':
        return _reject('ROW_TIER_NOT_BASE', gates,
                       {'row_label': tier_label(row.get('context_text'))})

    # ---- D4 同卡同标签唯一同文档位行
    text = canon(row.get('japanese'))
    same_text = [(g, s, r) for g, s, r in entries
                 if g == 'special_move'
                 and str(s.get('reference_field') or '').startswith('pattern')
                 and canon(r.get('japanese')) == text]
    gates['same_text_pattern_rows'] = [
        {'row_id': r.get('row_id'), 'reference_field': s.get('reference_field'),
         'label': tier_label(s.get('original_text')),
         'record_id': s.get('record_id')} for _, s, r in same_text]
    peers = [x for x in same_text
             if tier_label(x[1].get('original_text')) == 'BASE'
             and tier_label(x[2].get('context_text')) == 'BASE']
    if not peers:
        return _reject('PEER_MISSING', gates)
    if len(peers) != 1:
        return _reject('PEER_NOT_UNIQUE(%d)' % len(peers), gates)
    _, peer_skill, peer_row = peers[0]
    if peer_skill.get('table') != PATTERN_TABLE or peer_skill.get('layer') != LAYER:
        return _reject('PEER_TABLE_LAYER_DRIFT', gates,
                       {'table': peer_skill.get('table'), 'layer': peer_skill.get('layer')})
    pattern_id = peer_skill.get('record_id')
    if isinstance(pattern_id, bool) or not isinstance(pattern_id, int):
        return _reject('PEER_RECORD_ID_INVALID', gates, {'record_id': pattern_id})
    gates['peer'] = {'row_id': peer_row.get('row_id'),
                     'reference_field': peer_skill.get('reference_field'),
                     'stage': peer_row.get('stage'), 'pattern_id': pattern_id}

    # ---- D5 同文 super 兄弟必须存在（同卡同句、异块标签）
    supers = [x for x in same_text
              if tier_label(x[1].get('original_text')) == 'SUPER'
              and tier_label(x[2].get('context_text')) == 'SUPER']
    gates['super_rows'] = [{'row_id': r.get('row_id'),
                            'reference_field': s.get('reference_field'),
                            'record_id': s.get('record_id')} for _, s, r in supers]
    if not supers:
        return _reject('SUPER_SIBLING_MISSING', gates)

    # ---- D6 档位行镜像键答案（同键同字段同原值，且证据档不得升格）
    plan = []
    for slot in claim:
        hits = [a for a in (peer_row.get('answers') or [])
                if isinstance(a, dict) and a.get('rule_key') == slot['rule_key']]
        if not hits:
            return _reject('PEER_MIRROR_MISSING', gates,
                           {'rule_key': slot['rule_key'], 'peer': peer_row.get('row_id')})
        if len(hits) != 1:
            return _reject('PEER_MIRROR_AMBIGUOUS(%d)' % len(hits), gates,
                           {'rule_key': slot['rule_key']})
        answer = hits[0]
        if str(answer.get('field_path') or '') != slot['field']:
            return _reject('PEER_FIELD_DRIFT', gates,
                           {'rule_key': slot['rule_key'],
                            'field_path': answer.get('field_path')})
        # 注意：既有批 6/8/9/15 的档位行答案把表/记录来源放在 ``source`` 子对象里
        # （顶层无 table/layer/record_id）。这里只核 rule_key／field_path／原值／证据档，
        # 记录级一致性在 D8 之后用 CACHE 链逐一复核（PEER_SOURCE_*）。
        raw = answer.get('raw_value')
        state = num_state(raw)
        if state != 'FINITE':
            return _reject('PEER_RAW_%s' % state, gates,
                           {'rule_key': slot['rule_key'], 'raw_value': raw})
        if not sign_ok(slot, raw):
            return _reject('PEER_RAW_SIGN_MISMATCH', gates,
                           {'rule_key': slot['rule_key'], 'raw_value': raw})
        if (str(answer.get('numeric_evidence') or '') != '推断'
                or str(answer.get('association_evidence') or '') != '推断'):
            return _reject('PEER_EVIDENCE_UPGRADE', gates,
                           {'rule_key': slot['rule_key'],
                            'numeric_evidence': answer.get('numeric_evidence'),
                            'association_evidence': answer.get('association_evidence')})
        plan.append(dict(slot=slot, raw=raw, peer_answer=answer))
    gates['peer_mirror_values'] = {p['slot']['rule_key']: p['raw'] for p in plan}

    # ---- D7 super 同文兄弟在原值上至少一处不同（证明块标签是判别依据）
    differ = []
    gates['super_values'] = {}
    for _, sup_skill, sup_row in supers:
        values = {}
        for answer in sup_row.get('answers') or []:
            if not isinstance(answer, dict):
                continue
            key = answer.get('rule_key')
            if key in MIRROR_KEYS:
                values[key] = answer.get('raw_value')
        gates['super_values'][sup_row.get('row_id')] = values
        for item in plan:
            sup_raw = values.get(item['slot']['rule_key'])
            if sup_raw is None:
                continue
            if num_state(sup_raw) != 'FINITE':
                continue
            if float(sup_raw) != float(item['raw']):
                differ.append({'rule_key': item['slot']['rule_key'],
                               'peer_raw': item['raw'], 'super_raw': sup_raw,
                               'super_row': sup_row.get('row_id')})
    gates['super_differences'] = differ
    if not differ:
        return _reject('SUPER_VALUES_NOT_DIFFERENT', gates)

    # ---- D8 原记录链（13／2012／2003 逐位）
    chain, chain_err = pattern_chain(tab, pattern_id)
    if chain_err:
        return _reject('CHAIN_%s' % chain_err, gates)
    gates['chain'] = {'pattern_id': chain['pattern_id'],
                      'child_ids': [c['skillid'] for c in chain['children']],
                      'child_types': [c['type'] for c in chain['children']]}
    keys13 = [p for p in plan if p['slot']['table'] == BOSS_TABLE]
    keys2012 = [p for p in plan if p['slot']['ability'] == 2012]
    keys2003 = [p for p in plan if p['slot']['ability'] == 2003]
    b13 = None
    if keys13 or keys2012 or (clause['kind'] == 'buff' and clause['duration_claim']):
        children13 = [c for c in chain['children'] if c['type'] == 13]
        if len(children13) != 1:
            return _reject('CHAIN_TYPE13_NOT_UNIQUE(%d)' % len(children13), gates)
        b13 = children13[0]
        gates['chain']['type13'] = {'skillid': b13['skillid'], 'slot': b13['slot'],
                                    'index': b13['index'],
                                    'params': {k: v for k, v in b13['record'].items()
                                               if k.startswith('skillparam')}}
        for item in keys13:
            param = item['slot']['param']
            present = param in b13['record']
            state = num_state(b13['record'].get(param), present=present)
            if state != 'FINITE':
                return _reject('CHAIN_13_PARAM_%s_%s' % (param.upper(), state), gates)
            if float(b13['record'][param]) != float(item['raw']):
                return _reject('CHAIN_13_PARAM_DRIFT', gates,
                               {'param': param, 'record': b13['record'][param],
                                'peer': item['raw']})
            if not sign_ok(item['slot'], b13['record'][param]):
                return _reject('CHAIN_13_PARAM_SIGN_MISMATCH', gates,
                               {'param': param, 'record': b13['record'][param]})
        p3_state = num_state(b13['record'].get('skillparam3'),
                            present='skillparam3' in b13['record'])
        gates['chain']['type13_duration'] = {'raw': b13['record'].get('skillparam3'),
                                             'state': p3_state}
        if clause['duration_claim'] and not (p3_state == 'FINITE'
                                            and float(b13['record']['skillparam3']) > 0):
            return _reject('CHAIN_13_DURATION_INVALID', gates,
                           {'skillparam3': b13['record'].get('skillparam3')})
    if keys2012:
        if b13 is None:
            return _reject('CHAIN_TYPE13_REQUIRED_FOR_2012', gates)
        relay_id = b13['record'].get('s_ability')
        gates['chain']['s_ability_of_13'] = relay_id
        hit, err = skilllist_record(tab, relay_id)
        if err:
            return _reject('CHAIN_2012_%s' % err, gates)
        relay_index, relay = hit
        if relay.get('ability') != 2012:
            return _reject('CHAIN_2012_ABILITY_DRIFT', gates, {'ability': relay.get('ability')})
        relay_info = {'skillid': relay.get('skillid'), 'index': relay_index,
                      'ability': relay.get('ability'), 'record': relay}
        gates['chain']['type2012'] = {'skillid': relay.get('skillid'), 'index': relay_index,
                                      'ability': relay.get('ability'),
                                      'params': {k: v for k, v in relay.items()
                                                 if k.startswith('param')}}
        for item in keys2012:
            param = item['slot']['param']
            present = param in relay
            state = num_state(relay.get(param), present=present)
            if state != 'FINITE':
                return _reject('CHAIN_2012_PARAM_%s_%s' % (param.upper(), state), gates)
            if float(relay[param]) != float(item['raw']):
                return _reject('CHAIN_2012_PARAM_DRIFT', gates,
                               {'param': param, 'record': relay[param], 'peer': item['raw']})
            if not sign_ok(item['slot'], relay[param]):
                return _reject('CHAIN_2012_PARAM_SIGN_MISMATCH', gates,
                               {'param': param, 'record': relay[param]})
    rec2003 = None
    if keys2003 or (clause['kind'] == 'debuff' and clause['duration_claim']):
        candidates = []
        for child in chain['children']:
            hit, err = skilllist_record(tab, child['record'].get('s_ability'))
            if err:
                continue
            candidate_index, candidate = hit
            if candidate.get('ability') == 2003:
                candidates.append(dict(child=child, index=candidate_index, record=candidate))
        if len(candidates) != 1:
            return _reject('CHAIN_TYPE2003_NOT_UNIQUE(%d)' % len(candidates), gates)
        chosen = candidates[0]
        rec2003 = chosen['record']
        gates['chain']['type2003'] = {
            'skillid': rec2003.get('skillid'), 'index': chosen['index'],
            'ability': rec2003.get('ability'),
            'parent_child_type': chosen['child']['type'],
            'parent_child_slot': chosen['child']['slot'],
            'params': {k: v for k, v in rec2003.items() if k.startswith('param')}}
        for item in keys2003:
            param = item['slot']['param']
            present = param in rec2003
            state = num_state(rec2003.get(param), present=present)
            if state != 'FINITE':
                return _reject('CHAIN_2003_PARAM_%s_%s' % (param.upper(), state), gates)
            if float(rec2003[param]) != float(item['raw']):
                return _reject('CHAIN_2003_PARAM_DRIFT', gates,
                               {'param': param, 'record': rec2003[param],
                                'peer': item['raw']})
            if not sign_ok(item['slot'], rec2003[param]):
                return _reject('CHAIN_2003_PARAM_SIGN_MISMATCH', gates,
                               {'param': param, 'record': rec2003[param]})
        p0_state = num_state(rec2003.get('param0'), present='param0' in rec2003)
        gates['chain']['type2003_duration'] = {'raw': rec2003.get('param0'),
                                               'state': p0_state}
        if clause['duration_claim'] and not (p0_state == 'FINITE'
                                            and float(rec2003['param0']) > 0):
            return _reject('CHAIN_2003_DURATION_INVALID', gates,
                           {'param0': rec2003.get('param0')})

    # ---- D8b 档位行答案的 source 记录号必须与 CACHE 链定源一致（原记录链逐位核）
    resolved_ids = {}
    if b13 is not None:
        resolved_ids['boss13'] = b13['skillid']
    if keys2012:
        resolved_ids['skilllist2012'] = relay_info['skillid']
    if rec2003 is not None:
        resolved_ids['skilllist2003'] = rec2003.get('skillid')
    for item in plan:
        slot = item['slot']
        expected_id = (resolved_ids.get('boss13') if slot['table'] == BOSS_TABLE
                       else resolved_ids.get('skilllist2012') if slot['ability'] == 2012
                       else resolved_ids.get('skilllist2003'))
        source = item['peer_answer'].get('source')
        gates.setdefault('peer_sources', {})[slot['rule_key']] = (
            source if isinstance(source, dict) else None)
        if not isinstance(source, dict):
            continue
        if source.get('table') is not None and source.get('table') != slot['table']:
            return _reject('PEER_SOURCE_TABLE_DRIFT', gates,
                           {'rule_key': slot['rule_key'], 'table': source.get('table')})
        if source.get('layer') is not None and source.get('layer') != LAYER:
            return _reject('PEER_SOURCE_LAYER_DRIFT', gates,
                           {'rule_key': slot['rule_key'], 'layer': source.get('layer')})
        if source.get('record_id') is not None and source.get('record_id') != expected_id:
            return _reject('PEER_SOURCE_RECORD_DRIFT', gates,
                           {'rule_key': slot['rule_key'],
                            'source_record_id': source.get('record_id'),
                            'chain_record_id': expected_id})

    # ---- D9 批前未答＋时长保护＋幂等
    existing = [a for a in (row.get('answers') or []) if isinstance(a, dict)]
    claim_keys = {p['slot']['rule_key'] for p in plan}
    by_key = {}
    for answer in existing:
        by_key.setdefault(answer.get('rule_key'), []).append(answer)
    mirrored = [a for a in existing if a.get('rule_key') in claim_keys]
    if mirrored:
        same = []
        conflict = []
        chain_ids = {}
        for item in plan:
            key = item['slot']['rule_key']
            target_id = (b13['skillid'] if item['slot']['table'] == BOSS_TABLE
                         else (rec2003 or {}).get('skillid') if item['slot']['ability'] == 2003
                         else None)
            if item['slot']['ability'] == 2012:
                hit, _err = skilllist_record(tab, (b13 or {}).get('record', {}).get('s_ability'))
                target_id = None if hit is None else hit[1].get('skillid')
            chain_ids[key] = target_id
            for answer in by_key.get(key, []):
                if (answer.get('record_id') == target_id
                        and num_state(answer.get('raw_value')) == 'FINITE'
                        and float(answer['raw_value']) == float(item['raw'])):
                    same.append(key)
                else:
                    conflict.append({'rule_key': key, 'record_id': answer.get('record_id'),
                                     'raw_value': answer.get('raw_value')})
        gates['existing_mirror'] = {'same': sorted(set(same)), 'conflict': conflict,
                                    'chain_ids': chain_ids}
        if not conflict and len(set(same)) == len(claim_keys):
            return _reject('ALREADY_PRESENT_SAME', gates)
        return _reject('ALREADY_ANSWERED', gates,
                       {'disclosure': '本行已有同 rule_key 答案；不新增、不改写',
                        'same': sorted(set(same)), 'conflict': conflict})
    duration_slot = DURATION_SLOT[clause['kind']]
    if clause['duration_claim']:
        dur = by_key.get(duration_slot['rule_key']) or []
        if len(dur) != 1:
            return _reject('DURATION_ANSWER_MISSING(%d)' % len(dur), gates)
        answer = dur[0]
        record = b13['record'] if clause['kind'] == 'buff' else (rec2003 or {})
        record_id = (b13 or {}).get('skillid') if clause['kind'] == 'buff' \
            else (rec2003 or {}).get('skillid')
        gates['duration_answer'] = {'rule_key': duration_slot['rule_key'],
                                    'record_id': answer.get('record_id'),
                                    'raw_value': answer.get('raw_value'),
                                    'chain_record_id': record_id}
        if answer.get('table') != duration_slot['table'] or answer.get('layer') != LAYER:
            return _reject('DURATION_TABLE_LAYER_DRIFT', gates)
        if str(answer.get('field_path') or '') != duration_slot['field']:
            return _reject('DURATION_FIELD_DRIFT', gates)
        if answer.get('record_id') != record_id:
            return _reject('DURATION_RECORD_DRIFT', gates)
        param = duration_slot['param']
        if num_state(record.get(param), present=param in record) != 'FINITE' \
                or num_state(answer.get('raw_value')) != 'FINITE' \
                or float(record[param]) != float(answer['raw_value']):
            return _reject('DURATION_RAW_DRIFT', gates,
                           {'record': record.get(param), 'answer': answer.get('raw_value')})
    else:
        if by_key.get(duration_slot['rule_key']):
            return _reject('DURATION_NOT_CLAIMED', gates,
                           {'rule_key': duration_slot['rule_key'],
                            'note': '句面无「一定時間」，本批不得补时长'})
    allowed_keys = {duration_slot['rule_key']} if clause['duration_claim'] else set()
    extras = [a.get('rule_key') for a in existing if a.get('rule_key') not in allowed_keys]
    if extras:
        return _reject('EXTRA_ANSWER', gates, {'rule_keys': sorted(set(map(str, extras)))})

    # ---- D10 账本效果 1:1（一行一槽一答案；不产生同主张双值行）
    if ledger:
        try:
            import effect_ledger as ledger_mod
        except Exception as exc:  # pragma: no cover - 环境缺模块时显式失败
            return _reject('LEDGER_UNAVAILABLE', gates, {'error': repr(exc)})
        probe = dict(row)
        probe['answers'] = [a for a in existing if a.get('rule_key') not in claim_keys]
        analyzed = ledger_mod.analyze_row(probe, TABLE)
        all_types = [e['effect_type'] for e in analyzed['effects']]
        unresolved = sorted(e['effect_type'] for e in analyzed['effects']
                            if e.get('status') == 'unresolved')
        want = sorted(item['slot']['effect_type'] for item in plan)
        gates['effects'] = {'unresolved': unresolved, 'expected': want,
                            'all_types': all_types}
        dup_types = sorted({t for t in want if all_types.count(t) != 1})
        if dup_types:
            return _reject('CLAIM_TYPE_NOT_UNIQUE', gates, {'types': dup_types})
        if unresolved != want:
            return _reject('EFFECT_SET_MISMATCH', gates)

    duration_answer = None
    if clause['duration_claim']:
        duration_answer = (by_key.get(duration_slot['rule_key']) or [None])[0]
    return {'accepted': True, 'rejection': None, 'gates': gates, 'claim': claim,
            'clause': clause, 'peer_skill': peer_skill, 'peer_row': peer_row,
            'pattern_id': pattern_id, 'chain': chain, 'plan': plan,
            'supers': [r.get('row_id') for _, _, r in supers],
            'type13': b13, 'type2012': relay_info if keys2012 else None,
            'type2003': rec2003,
            'duration_slot': duration_slot, 'duration_answer': duration_answer,
            'existing': existing, 'detail': None}


# ---------------------------------------------------------------- 答案构造
def _slot_source(slot, resolved, peer_row):
    if slot['table'] == BOSS_TABLE:
        record = resolved['type13']
        pointer = '/bossinfo/bossskill/%d' % record['index']
        source_key = BOSS_SOURCE_KEY
        original = 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw'
        table = BOSS_TABLE
    else:
        if slot['ability'] == 2012:
            record = resolved['type2012']
        else:
            record = dict(skillid=resolved['type2003'].get('skillid'),
                          index=resolved['gates']['chain']['type2003']['index'],
                          record=resolved['type2003'])
        pointer = '/skilllist/%d' % record['index']
        source_key = SKILLLIST_SOURCE_KEY
        original = 'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw'
        table = 'skilllist'
    if table == BOSS_TABLE:
        hop = 'bossskill 唯一命中（type13 子记录）'
    elif slot['ability'] == 2012:
        hop = 'skilllist 唯一命中（经 type13 记录的 s_ability 中继，ability=2012）'
    else:
        hop = ('skilllist 唯一命中（经档位行子记录的 s_ability 指向，ability=2003；'
               '该子记录类型实测可为 105/110/116/22/55/76，不经 type13）')
    return {
        'table': table, 'record_id': record['record'].get('skillid'), 'layer': LAYER,
        'field_path': slot['field'], 'source_key': source_key, 'original_file': original,
        'json_pointer': pointer, 'field': slot['field'],
        'field_json_pointer': pointer + slot['field'],
        'record_key': '%s#%s' % (source_key, pointer),
        'source_resolution': 'RESOLVED_EXACT_DECODED_RECORD',
        'snapshot_id': SNAPSHOT_ID,
        'note': ('按解码 JSON 的 %s 记录号唯一命中：%s；经同卡档位行 %s（%s / pattern %s）'
                 '定源；本行 skilltext 只作同卡同档位镜像，无独立执行链'
                 % ('bossinfo.bossskill' if table == BOSS_TABLE else 'skilllist', hop,
                    peer_row.get('row_id'),
                    resolved['gates']['peer'].get('reference_field'),
                    resolved['pattern_id'])),
    }


def _slot_chains(resolved):
    chain = {'pattern_id': resolved['pattern_id'],
             'base_child_ids': resolved['gates']['chain']['child_ids'],
             'base_child_types': resolved['gates']['chain']['child_types']}
    if resolved.get('type13'):
        chain['type13'] = {'skillid': resolved['type13']['skillid'],
                           'slot': resolved['type13']['slot'],
                           'params': {k: v for k, v in resolved['type13']['record'].items()
                                      if k.startswith('skillparam')}}
        if resolved['type13']['record'].get('s_ability') is not None:
            chain['type13']['s_ability'] = resolved['type13']['record'].get('s_ability')
    if resolved.get('type2012'):
        chain['type2012'] = {'skillid': resolved['type2012'].get('skillid'),
                             'ability': resolved['type2012'].get('ability'),
                             'params': {k: v for k, v in resolved['type2012']['record'].items()
                                        if k.startswith('param')}}
    if resolved.get('type2003'):
        chain['type2003'] = {'skillid': resolved['type2003'].get('skillid'),
                             'ability': resolved['type2003'].get('ability'),
                             'params': {k: v for k, v in resolved['type2003'].items()
                                        if k.startswith('param')}}
        chain['type2003']['parent_child_type'] = \
            resolved['gates']['chain']['type2003'].get('parent_child_type')
        chain['type2003']['parent_child_slot'] = \
            resolved['gates']['chain']['type2003'].get('parent_child_slot')
    return chain


def _slot_value(slot, converted, raw, resolved, peer_row):
    """值文：逐字沿用既有值文＋镜像来源与「未证明项」披露（关键词必须落在文内）。"""
    base = (converted or {}).get('value_text') or (
        '%s %s' % (slot['keyword'], _num(raw)))
    clause = resolved['clause']
    subject = '味方全体' if clause['kind'] == 'buff' else '同時に攻撃した敵'
    duration_note = '句面含「一定時間」；时长沿用既有 B18 答案，本批不重答' \
        if clause['duration_claim'] else \
        '句面无「一定時間」，本批不写时长（档位行 2003 的 param0 仅披露，不当 −1 秒或永久）'
    tail = ('；本项为镜像行（0 新增唯一数值）：同卡档位行 %s（%s / pattern %s）已交付同规则键'
            '同字段同原值；句面对象＝%s；%s；Boss 模式下 pattern 选取维度未解析'
            '（S7_same_cond_alt_t13 保留）；不声明实际装载、不写展示层最终数值（关联推断）'
            % (peer_row.get('row_id'),
               resolved['gates']['peer'].get('reference_field'), resolved['pattern_id'],
               subject, duration_note))
    return base + tail


def build_answers(data, cid, row, res, tab=None):
    """为本行构造答案（数量＝句面槽数）；任何规则缺失即返回 None（不静默沿用）。"""
    import rules as R
    if not res.get('accepted'):
        return None
    tab = tab or tables(data)
    peer_row = res['peer_row']
    answers = []
    for item in res['plan']:
        slot = item['slot']
        raw = item['raw']
        if slot['table'] == BOSS_TABLE:
            record = res['type13']['record']
        elif slot['ability'] == 2012:
            record = res['type2012']['record']
        else:
            record = res['type2003']
        converted = R.answer_for(slot['table'], slot['ability'], slot['field'], raw, record,
                                 source_layer=LAYER)
        if converted is None:
            return None
        rule = R.rule_for(slot['table'], slot['ability'], slot['field']) or {}
        if not rule or '已确认' not in str(rule.get('status') or ''):
            return None
        value = _slot_value(slot, converted, raw, res, peer_row)
        if any(word in value for word in FORBIDDEN_WORDS):
            return None
        marker = {
            'scope': SCOPE, 'structure_scope': STRUCTURE_SCOPE, 'module': MODULE_VERSION,
            'cid': cid, 'row_id': row.get('row_id'), 'attribute': slot['name'],
            'rule_key': slot['rule_key'], 'field_path': slot['field'],
            'table': slot['table'], 'record_id': record.get('skillid'), 'layer': LAYER,
            'raw_value': raw,
            'peer_row_id': peer_row.get('row_id'),
            'peer_reference_field': res['gates']['peer'].get('reference_field'),
            'peer_stage': res['gates']['peer'].get('stage'),
            'pattern_id': res['pattern_id'],
            'sentence': dict(res['gates']['sentence']),
            'chain': _slot_chains(res),
            'super_rows': res['supers'],
            'super_differences': [d for d in res['gates']['super_differences']
                                  if d['rule_key'] == slot['rule_key']],
            'duration_answer': None if res['duration_answer'] is None else {
                'rule_key': res['duration_answer'].get('rule_key'),
                'record_id': res['duration_answer'].get('record_id'),
                'raw_value': res['duration_answer'].get('raw_value')},
            'not_written': ('不写面板值/最终伤害/固定防御实际量/最终移动速度/叠加上限/Chain 实际'
                            '系数；不写 Boss 模式 pattern 选取；不写镜像行参与战斗；'
                            '不重答时长（13|p3 / 2003|p0）'),
            'admission': ('SAME_CARD_SAME_TEXT_SAME_TIER_LABEL_UNIQUE_PEER_MIRROR'
                          '（同卡同文＋同块【共鳴必殺】标签＋唯一同标签同文档位行＋'
                          'super 同文异值＋原记录链逐位相等＋批前未答＋效果 1:1）'),
            'association': '推断',
            'limits': LIMIT,
        }
        answers.append({
            'value': value,
            'quantity_kind': converted.get('quantity_kind'),
            'unit': converted.get('unit'),
            'value_text': converted.get('value_text'),
            'raw_value': raw,
            'effective_float32': _f32(raw),
            'quantitative': True,
            'numeric_source': ('复用既有已确认规则＋同卡档位行同键同字段同原值；'
                               '本行归属为推断'),
            'numeric_evidence': '推断',
            'association_evidence': '推断',
            'evidence_scope': SCOPE,
            'answer_status': 'INFERRED_MIRROR_OF_SAME_CARD_PEER_ROW',
            'rule_key': slot['rule_key'],
            'table': slot['table'],
            'record_id': record.get('skillid'),
            'layer': LAYER,
            'field_path': slot['field'],
            'source': _slot_source(slot, res, peer_row),
            'rule_status': rule.get('status'),
            'conversion': rule.get('conversion'),
            'base_definition': rule.get('base_definition'),
            'conditions': rule.get('applicability'),
            'rule_limits': rule.get('limits'),
            'condition_label': ('本行 skilltext 属【共鳴必殺】档；同卡档位行 %s（%s / '
                                'pattern %s）链内唯一 %s 记录生效时（pattern 选取未解析）'
                                % (peer_row.get('row_id'),
                                   res['gates']['peer'].get('reference_field'),
                                   res['pattern_id'],
                                   'bossskill 13' if slot['table'] == BOSS_TABLE
                                   else 'skilllist %d' % slot['ability'])),
            'target': ('味方全体（句面给出；rules.target 为空，受方选择未复查）'
                       if res['clause']['kind'] == 'buff' else
                       ('同時に攻撃した敵（句面给出；2003 写的是受击目标，触发仅 Skill 型着弹、'
                        'Normal/Critical 不触发）')),
            'binding': {BINDING_KEY: marker},
            'context': 'skilltext 同卡同档位镜像行（%s / %s）'
                       % (res['clause']['kind'], slot['name']),
            'note': ('同卡同文同标签唯一档位行的同键同字段同原值镜像；关联推断、'
                     '0 新增唯一数值；不写最终值、不写行完整、不声明 pattern 选取。' + LIMIT),
            'evidence': EVIDENCE[:],
        })
    return answers


# ---------------------------------------------------------------- 行级写入
_NOTE_PREFIX = 'C12-P3：'


def apply_answers(row, answers, res):
    """把本行答案写入行（只追加，不覆盖；不删 S7/hint 文本；不改 row_class/partial）。"""
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    existing = {key(a) for a in row.get('answers') or [] if isinstance(a, dict)}
    added = 0
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault('answers', []).append(answer)
        existing.add(key(answer))
        added += 1
    if not added:
        return 0
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = list(dict.fromkeys([str(s) for s in scopes] + [SCOPE]))
    row['evidence'] = '推断'
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    note = (_NOTE_PREFIX + 'skilltext 同卡同档位镜像——档位行 %s（%s / pattern %s）已交付同规则键'
            '同字段同原值；本行按同卡同文＋同块【共鳴必殺】标签＋唯一同标签同文档位行＋'
            'super 同文异值归位（0 新增唯一数值）；S7_same_cond_alt_t13 与 b6/b8/b10 hint '
            '原样保留，Boss 模式 pattern 选取维度未解析；不重答时长；不写行完整。'
            % (res['peer_row'].get('row_id'),
               res['gates']['peer'].get('reference_field'), res['pattern_id']))
    reasons = [r for r in (row.get('unknown_reasons') or []) if isinstance(r, str)]
    if note not in reasons:
        reasons.append(note)
    row['unknown_reasons'] = reasons
    return added


# ---------------------------------------------------------------- 正式页消费
def apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None):
    """正式页消费（候选未接线）：只为声明范围内卡片的匹配 skilltext 行写镜像答案。

    返回报告（``answers_added`` / ``rows_changed`` / ``additions`` / ``rejections`` /
    ``disclosures``）。``scope_cids`` 缺省 ``None`` → 一行都不处理。
    """
    report = {'scope': SCOPE, 'module': MODULE_VERSION, 'cid': cid,
              'out_of_scope': True, 'evaluated': 0, 'in_scope_rows': [],
              'answers_added': 0, 'rows_changed': 0, 'additions': [], 'rejections': [],
              'disclosures': [], 'skipped_existing': 0}
    if scope_cids is None:
        report['rejections'].append({'reason': 'NO_SCOPE_DECLARED'})
        return report
    scope = set()
    for item in scope_cids:
        if isinstance(item, bool) or not isinstance(item, int):
            report['rejections'].append({'reason': 'SCOPE_INVALID', 'value': item})
            return report
        scope.add(item)
    if cid not in scope:
        report['rejections'].append({'reason': 'CID_NOT_IN_DECLARED_SCOPE'})
        return report
    report['out_of_scope'] = False
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append({'reason': 'ZERO_TOUCH_CID'})
        return report
    tab = tab or tables(data)
    entries = card_entries(groups)
    for group_name, skill, row in entries:
        if group_name != 'special_move':
            continue
        if str(skill.get('reference_field') or '') != REF_FIELD:
            continue
        report['evaluated'] += 1
        report['in_scope_rows'].append(row.get('row_id'))
        res = evaluate(data, cid, row, groups=groups, tab=tab)
        if not res['accepted']:
            code = res['rejection']
            if code == 'ALREADY_PRESENT_SAME':
                report['skipped_existing'] += 1
            elif code == 'ALREADY_ANSWERED':
                report['disclosures'].append({'row_id': row.get('row_id'), 'reason': code,
                                              'detail': res.get('detail')})
            else:
                report['rejections'].append({'row_id': row.get('row_id'), 'reason': code,
                                             'detail': res.get('detail')})
            continue
        answers = build_answers(data, cid, row, res, tab=tab)
        if answers is None:
            report['rejections'].append({'row_id': row.get('row_id'),
                                         'reason': 'RULE_UNAVAILABLE'})
            continue
        added = apply_answers(row, answers, res)
        if added:
            report['answers_added'] += added
            report['rows_changed'] += 1
            for answer in answers:
                report['additions'].append({'row_id': row.get('row_id'),
                                            'rule_key': answer['rule_key'],
                                            'record_id': answer['record_id'],
                                            'field_path': answer['field_path'],
                                            'raw_value': answer['raw_value']})
        else:
            report['skipped_existing'] += 1
    return report


if __name__ == '__main__':
    raise SystemExit('候选模块不提供写入口；只读探针请用 run_checks.py（本批不运行正式生成）')
