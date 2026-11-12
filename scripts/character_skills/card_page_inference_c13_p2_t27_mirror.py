# -*- coding: utf-8 -*-
"""C13-P2 ``charainfo.skilltext`` 同卡同档位同文 t27 周期回复镜像（3 行 / 3 答案，全 Y.G.）。

任务卡 ``docs/tasks/20261031-c13-p2-t27-skilltext-mirror.md``；C13 总卡
``docs/tasks/20261031-c13-cycle.md``；候选输入 ``work/c13_20261031/mirror_scan.json``。
同族先例：``card_page_inference_c10_p1_mirror.py``（同卡 skilltext 基础档 t27/t64 镜像 6 行）、
``card_page_inference_c8_p1_t27.py``（t27 周期回复单键生产）、
``card_page_inference_c12_p3_skilltext_mirror.py``（同卡同文档位 buff/debuff 镜像）。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；正式 pages、
``rules.json``／``rules.py``、``effect_ledger.py`` 的映射表均未改动；本阶段不运行正式全库生成。

本批做什么、不做什么
--------------------
三张卡（10215／30228／30314）的 ``special_move.skilltext`` 首句逐字相同：

    【共鳴必殺/連撃】味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。

同卡**同文基档行**（``pattern0``，块首标签同为「【共鳴必殺…】」）**已经**有 C8 交付的
``bossskill|27|/skillparam1`` 答案。本批只把这些 skilltext 行上**尚缺**的单次回复系数
（p1）按「同卡同文＋同档位标签＋唯一基档行＋原记录链逐位相等」归位：

* 10215：基档行 pattern0（记录 41021500）p1 = 1.25 → skilltext 行
  ``10215-special_move-special_move-skilltext-lvorder3-f0``
* 30228：基档行 pattern0（记录 43022800）p1 = 1.25 → skilltext 行
  ``30228-special_move-special_move-skilltext-lvorder2-f0``
* 30314：基档行 pattern0（记录 43031400）p1 = 1.75 → skilltext 行
  ``30314-special_move-special_move-skilltext-lvorder2-f0``

**0 新增唯一数值、0 新公式、0 新规则键**：三个原值早已在同卡基档行交付；本批只把三个未答
skilltext 行归位到同一记录／原值，不把 C8／C10 已交付项重复计入收益。

为什么是基档（而不是超共鳴），以及为什么不按数字选值
--------------------------------------------------
每张卡的 skilltext 文本块**自身首句标签**都是 ``【共鳴必殺…】``（逐行核 ``context_text``
前缀，不看值大小）；同文的超共鳴行标签为 ``【超共鳴必殺…】``，记录／原值不同，逐行列为
**排除值**（``excluded``）：10215 pattern2 = 2（41021506）、30228 pattern1 = 1.5（43022803）、
30314 pattern1 = 2（43031403）。超共鳴原值**必须与基档至少一处不同**（``SUPER_VALUES_NOT_
DIFFERENT`` 门），否则「按句面文本选值」无法解释，直接拒绝。

原记录链（逐位核，不按日文或数字跨表选值）
------------------------------------------
每个候选行都从**原始 CACHE** 独立重读三层，而不是只看页面答案：

1. ``charainfo[cid].pattern0`` → 在该层 ``bosspattern`` 唯一命中；
2. 该 pattern 的 ``skillid0..N`` 槽位从 0 连续，每个子记录在 ``bossskill`` 全表唯一命中；
3. 链内 type27 **恰 1 条**，且**必须位于 skillid0**（任务卡逐字要求
   ``charainfo.pattern0→bosspattern→skillid0→bossskill``），其 ``skillid``、
   ``skillparam1``（FINITE>0）与基档行已交付答案的 ``record_id``／``raw_value`` 逐位相等；
   链 id／类型序列同时等于冻结表。
4. 基档行答案的 ``source`` 指针必须指向同一 ``/bossinfo/bossskill/<index>`` 记录。

``skillparam2``（回复间隔输入＝2 游戏秒）与 ``skillparam3``（回复次数＝15 次）只在值文／
marker 里作**已确认字段值披露**，**不新增答案、不换算实机间隔与次数**。

一行一答案
----------
D9 用账本 ``effect_ledger.analyze_row``（纯函数、只读）断言：该行句面效果**恰 1 条**且
``status == 'unresolved'``、类型为既有词表外的「回復（词表外）」→ 本批一条答案恰对应一个
未解主张，不产生「同主张双值行」。

接口
----
``tables(data)`` / ``clone_tables(tab)``                  CACHE 主表只读索引（可注入／深拷贝）。
``tier_label(text)``                                      块首档位标签（逐字）。
``chain_of(tab, cid)``                                    ``charainfo.pattern0``→bosspattern→bossskill。
``evaluate(data, cid, row, *, groups=None, tab=None, ledger=True)``   单行判定（不写入）。
``build_answers(data, cid, row, res, tab=None)``          本行答案对象（恰 1 条）。
``apply_answers(row, answers, res)``                      行级写入（只追加，不覆盖）。
``apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None)``  正式页消费（候选未接线）。

批次边界由调用方**显式声明**：``scope_cids`` 缺省 ``None`` → 一行都不处理
（``NO_SCOPE_DECLARED``）；不在声明集合内的卡 → ``CID_NOT_IN_DECLARED_SCOPE``（零写入）。
保护／禁推卡 20234／30102／30236／30239 在模块内硬拒绝。

账本侧（合并时才需要，本阶段不做）
----------------------------------
``effect_ledger`` 目前只消费 C8 的 ``C8_P1_T27_SCOPE`` 与 C10 的 ``C10P1_T27_SCOPE``；
本批答案带 ``binding.c13_p2_t27_mirror_binding``（scope ``C13_P2_T27_MIRROR_20261031``），
合并冻结时必须另加**一条来源限定窄映射**才会被账本消费。**本阶段不新增映射、不改
``effect_ledger.py``**；候选检查只验证句面未解效果恰为 1 条（1:1），不宣称已关闭账本。
"""
from __future__ import annotations

import json
import math
import re
import struct
import unicodedata
from pathlib import Path
from project_layout_paths import read_path

MODULE_VERSION = 'c13_p2_t27_mirror_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 本批证据 scope（写进答案 ``evidence_scope`` 与行级 scope 列表）。
SCOPE = 'C13_P2_T27_MIRROR_20261031'
#: 结构判定自身 scope（只出现在 answer binding 里，供逐行溯源）。
STRUCTURE_SCOPE = 'C13_P2_T27_MIRROR_STRUCTURE_20261031'
#: 答案内 binding 的键名。
BINDING_KEY = 'c13_p2_t27_mirror_binding'
#: 行级 marker 键（与 C8／C10 同族；成为账本 promotion_key，保留可追溯性）。
MARKER_KEY = 'inference_c13_p2_t27_mirror'

#: 唯一新增规则键（既有已确认规则，不新增键）。
RULE_KEY = 'bossskill|27|/skillparam1'
FIELD = '/skillparam1'
PARAM = 'skillparam1'
LIMIT_FIELD = 'skillparam2'
COUNT_FIELD = 'skillparam3'
CARRIER_TYPE = 27

TABLE = 'charainfo'
LAYER = 'CACHE'
REF_FIELD = 'skilltext'
SOURCE_KEY = 'CACHE/charainfo.data5.json.raw'
BOSS_SOURCE_KEY = 'CACHE/bossinfo.data5.json.raw'
PATTERN_TABLE = 'bosspattern'
BOSS_TABLE = 'bossskill'
CACHE_DIR = 'output/cache_full_20261015_v3/decoded'
SNAPSHOT_ID = 'cache_full_20261015_v3'

#: 保护／禁推卡：判定前硬拒绝（30102 禁推卡；30236／30239 保护卡；20234 既有边界）。
ZERO_TOUCH_CIDS = frozenset({20234, 30102, 30236, 30239})

BASE_LABEL = '【共鳴必殺'
SUPER_LABEL = '【超共鳴必殺'
#: 本批唯一受理句面（逐字；NFKC＋去空白比较）。
SENTENCE = '【共鳴必殺/連撃】味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。'
MECH_RX = re.compile(r'一定間隔ごとに上限を超えて')
ABNORMAL_WORD = '状態異常'
#: 文本块标签（块首【…】）；句身比较时剥离，档位由 label 单独判定。
_LABEL_RX = re.compile(r'^【[^】]*】')

#: 冻结准入表（2026-10-31 由原始 CACHE 记录与当前正式页逐行重导一致后固化；输入漂移即拒绝）。
_ADMITTED_LIST = [
    dict(cid=10215,
         row_id='10215-special_move-special_move-skilltext-lvorder3-f0',
         text=SENTENCE, record_id=41021500, raw_value=1.25,
         peer_row_id='10215-special_move-special_move-pattern0-lvorder0-f0',
         peer_ref='pattern0', pattern_id=41021500,
         chain_ids=[41021500, 41021501, 41021502], chain_types=[27, 13, 116],
         super_row_id='10215-special_move-special_move-pattern2-lvorder2-f0',
         super_ref='pattern2', super_pattern_id=41021502,
         super_record_id=41021506, super_raw_value=2.0),
    dict(cid=30228,
         row_id='30228-special_move-special_move-skilltext-lvorder2-f0',
         text=SENTENCE, record_id=43022800, raw_value=1.25,
         peer_row_id='30228-special_move-special_move-pattern0-lvorder0-f0',
         peer_ref='pattern0', pattern_id=43022800,
         chain_ids=[43022800, 43022801, 43022802], chain_types=[27, 13, 116],
         super_row_id='30228-special_move-special_move-pattern1-lvorder1-f0',
         super_ref='pattern1', super_pattern_id=43022801,
         super_record_id=43022803, super_raw_value=1.5),
    dict(cid=30314,
         row_id='30314-special_move-special_move-skilltext-lvorder2-f0',
         text=SENTENCE, record_id=43031400, raw_value=1.75,
         peer_row_id='30314-special_move-special_move-pattern0-lvorder0-f0',
         peer_ref='pattern0', pattern_id=43031400,
         chain_ids=[43031400, 43031401, 43031402], chain_types=[27, 13, 116],
         super_row_id='30314-special_move-special_move-pattern1-lvorder1-f0',
         super_ref='pattern1', super_pattern_id=43031401,
         super_record_id=43031403, super_raw_value=2.0),
]
ADMITTED = {item['row_id']: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item['cid'] for item in _ADMITTED_LIST)
ADMITTED_PATTERN_IDS = frozenset(item['pattern_id'] for item in _ADMITTED_LIST)

EVIDENCE = [
    'docs/tasks/20261031-c13-p2-t27-skilltext-mirror.md',
    'docs/tasks/20261031-c13-cycle.md',
    'work/c13_20261031/mirror_scan.json',
    'output/character_skills/profiles/rules.json',
    'output/boss_heal/field_dictionary.json',
]
LIMIT = ('单次回复系数的原值与规则键为已确认静态规则（origin output/boss_heal/'
         'field_dictionary.json）；「本行 skilltext 句面对应同卡基档行记录」依赖同卡同文＋'
         '【共鳴必殺】档位标签＋唯一基档行已交付同键同记录同原值＋原记录链逐位相等，属结构证据，'
         '关联＝推断；对象只由句面「味方全体」给出（rules.target 为空，受疗对象选择未复查）；'
         '不写最终 HP 回复量、超上限保留比例、实际触发间隔与次数；不声明实际装载、不做实机验证；'
         'skillparam2／skillparam3 只作已确认字段值披露，不新增答案。')
FORBIDDEN_PHRASES = ('面板值', '最终伤害', '固定防御实际量', '实际间隔为', '实际次数为')

_TABLES = {}


# ---------------------------------------------------------------- 基础工具
def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def canon(text):
    """NFKC＋去空白（句面／块文本比较口径）。"""
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def tier_label(text):
    """文本块的档位标签：只认块首词形，不从值大小或句面内容推断。"""
    core = canon(text)
    if core.startswith(canon(SUPER_LABEL)):
        return 'SUPER'
    if core.startswith(canon(BASE_LABEL)):
        return 'BASE'
    return None


def body_of(text):
    """剥离块首【…】标签后的句身（NFKC＋去空白）；「同文」按句身比较，档位另判。"""
    core = canon(text)
    return _LABEL_RX.sub('', core)


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


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def raw_state(raw, present=True):
    """缺失 / null / 非有限 / 负值 / 真零 / 有限分开标注（不把任何一档补成 0）。"""
    if not present:
        return 'MISSING'
    if raw is None:
        return 'NULL'
    if isinstance(raw, bool):
        return 'NON_FINITE'
    try:
        f = float(raw)
    except (TypeError, ValueError):
        return 'NON_FINITE'
    if not math.isfinite(f):
        return 'NON_FINITE'
    if f < 0:
        return 'NEGATIVE'
    if f == 0:
        return 'ZERO'
    return 'FINITE'


# ---------------------------------------------------------------- 只读主表
def tables(data):
    """CACHE 解码主表（按 root 缓存；只读）。索引均为 ``id -> [(array_index, record)]``。"""
    root = Path(getattr(data, 'root', None) or Path('.')).resolve()
    key = str(root)
    if key not in _TABLES:
        base = read_path(root / CACHE_DIR, root=root)
        need = [base / 'bossinfo.data5.json.raw', base / 'charainfo.data5.json.raw']
        missing = [str(p) for p in need if not p.exists()]
        if missing:
            raise FileNotFoundError('CACHE 解码主表缺失: %s' % missing)
        boss = _read(need[0])['bossinfo']
        patterns, boss_skills = {}, {}
        for i, rec in enumerate(boss.get('bosspattern') or []):
            patterns.setdefault(rec.get('patternid'), []).append((i, rec))
        for i, rec in enumerate(boss.get('bossskill') or []):
            boss_skills.setdefault(rec.get('skillid'), []).append((i, rec))
        chara_all = _read(need[1])['charainfo']
        chara = {}
        for i, rec in enumerate(chara_all):
            chara.setdefault(rec.get('cid'), []).append((i, rec))
        _TABLES[key] = dict(patterns=patterns, boss_skills=boss_skills,
                            chara=chara, chara_all=chara_all, root=root)
    return _TABLES[key]


def clone_tables(tab):
    """深拷贝主表索引（反例用例在副本上篡改，不动只读缓存；保留整数键，不经 JSON）。"""
    import copy
    return {k: (v if k == 'root' else copy.deepcopy(v)) for k, v in tab.items()}


def unique_hit(index, record_id):
    hits = index.get(record_id) or []
    if len(hits) != 1:
        return None, 'NOT_UNIQUE(%d)' % len(hits)
    return hits[0], None


def card_rows(groups):
    """``[(group_name, skill, row)]``（顺序即页面顺序）。"""
    out = []
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                out.append((group.get('group'), skill, row))
    return out


# ---------------------------------------------------------------- 原记录链
def chain_of(tab, cid):
    """``charainfo[cid].pattern0`` → bosspattern → skillidN → bossskill（唯一命中）。"""
    chara_hit, chara_err = unique_hit(tab['chara'], cid)
    if chara_err:
        return None, 'CHARAINFO_RECORD_%s' % chara_err
    chara_index, chara = chara_hit
    pattern_id = chara.get('pattern0')
    if isinstance(pattern_id, bool) or not isinstance(pattern_id, int):
        return None, 'PATTERN_POINTER_MISSING'
    hit, err = unique_hit(tab['patterns'], pattern_id)
    if err:
        return None, 'BOSSPATTERN_%s' % err
    pattern_index, pattern = hit
    slots = [(i, pattern.get('skillid%d' % i)) for i in range(7)
             if pattern.get('skillid%d' % i) is not None]
    if [i for i, _ in slots] != list(range(len(slots))):
        return None, 'SLOT_NOT_CONTIGUOUS'
    children = []
    for slot_index, skill_id in slots:
        child_hit, child_err = unique_hit(tab['boss_skills'], skill_id)
        if child_err:
            return None, 'BOSSSKILL_%s_%s' % (skill_id, child_err)
        child_index, child = child_hit
        children.append(dict(slot='skillid%d' % slot_index, skillid=skill_id,
                             index=child_index, type=child.get('skillid0'), record=child,
                             params={k: v for k, v in child.items()
                                     if k.startswith('skillparam')}))
    return dict(pattern_id=pattern_id, pattern_index=pattern_index, pattern=pattern,
                charainfo_index=chara_index, charainfo=chara, children=children,
                layer=LAYER), None


# ---------------------------------------------------------------- 单行判定
def _reject(code, gates, detail=None):
    return {'accepted': False, 'rejection': code, 'detail': detail, 'gates': gates}


def _answer_view(answer):
    return {'rule_key': answer.get('rule_key'), 'record_id': answer.get('record_id'),
            'raw_value': answer.get('raw_value'), 'field_path': answer.get('field_path'),
            'table': answer.get('table'), 'layer': answer.get('layer')}


def evaluate(data, cid, row, *, groups=None, tab=None, ledger=True, admitted=None):
    """单行判定（不写入）。``groups`` 为该卡页面 ``groups``（同文基档行／超共鳴兄弟来源）。

    判定顺序（任一不符即拒，不猜、不跨卡取行）：
      D0 零触碰卡；D1 冻结行身份＋CACHE 层＋档位标签（块首须【共鳴必殺】）＋charainfo
      文本链；D2 句面逐字；D4 同文档位集合＝基档 1 条＋超共鳴 1 条；
      D5 基档行已交付同键同字段同记录同原值答案；D6 超共鳴同文行存在且原值不同；
      D7 原记录链（charainfo.pattern0→bosspattern→skillid0→bossskill，唯一 type27）；
      D8 基档答案 source 指针指向同一记录；D9 句面在 pattern 正文唯一；
      D10 批前未答／幂等；D11 账本效果 1:1。
    """
    gates = {'cid': cid, 'row_id': (row or {}).get('row_id') if isinstance(row, dict) else None}
    if isinstance(cid, bool) or not isinstance(cid, int):
        return _reject('CID_INVALID', gates)
    if cid in ZERO_TOUCH_CIDS:
        return _reject('ZERO_TOUCH_CID', gates)
    if not isinstance(row, dict) or not row.get('row_id'):
        return _reject('ROW_INVALID', gates)
    table_adm = ADMITTED if admitted is None else admitted
    adm = table_adm.get(row.get('row_id'))
    if adm is None:
        return _reject('NOT_IN_BATCH_SCOPE', gates)
    if adm['cid'] != cid:
        return _reject('CID_MISMATCH', gates)
    tab = tab or tables(data)
    entries = card_rows(groups)
    if not entries:
        return _reject('GROUPS_REQUIRED', gates)
    same_id = [e for e in entries if e[2].get('row_id') == row.get('row_id')]
    if len(same_id) > 1:
        return _reject('ROW_ID_DUPLICATE', gates)
    mine = [e for e in entries if e[2] is row]
    if not mine:
        if not same_id:
            return _reject('ROW_NOT_IN_GROUPS', gates)
        mine = same_id
    group_name, skill, row = mine[0]

    # ---- D1 行身份＋层＋charainfo 文本链
    if group_name != 'special_move' or row.get('group') != 'special_move':
        return _reject('GROUP_MISMATCH', gates)
    if row.get('cid') != cid:
        return _reject('ROW_CID_MISMATCH', gates)
    if str(row.get('reference_field') or '') != REF_FIELD:
        return _reject('ROW_REFERENCE_FIELD_DRIFT', gates)
    if str(skill.get('reference_field') or '') != REF_FIELD:
        return _reject('SKILL_REFERENCE_FIELD_DRIFT', gates)
    if skill.get('table') != TABLE or skill.get('layer') != LAYER:
        return _reject('SKILL_TABLE_LAYER_DRIFT', gates,
                       {'table': skill.get('table'), 'layer': skill.get('layer')})
    if skill.get('record_id') != cid:
        return _reject('SKILL_RECORD_ID_DRIFT', gates)
    src = skill.get('source') or {}
    if src.get('layer') != LAYER or src.get('source_key') != SOURCE_KEY:
        return _reject('SKILL_SOURCE_DRIFT', gates)
    rsrc = row.get('source') or {}
    gates['row_source'] = {k: rsrc.get(k) for k in
                           ('record_key', 'source_key', 'layer', 'field', 'json_pointer')}
    if rsrc.get('layer') != LAYER or rsrc.get('source_key') != SOURCE_KEY:
        return _reject('ROW_SOURCE_DRIFT', gates)
    if str(rsrc.get('field') or '') != '/skilltext':
        return _reject('ROW_SOURCE_FIELD_DRIFT', gates)
    # ---- 档位标签前置：块首标签必须【共鳴必殺】（不从值大小推断；先于文本内容比较）
    skill_label = tier_label(skill.get('original_text'))
    row_label = tier_label(row.get('context_text'))
    gates['tier'] = {'skill_label': skill_label, 'row_label': row_label}
    if skill_label != 'BASE' or row_label != 'BASE':
        return _reject('ROW_TIER_NOT_BASE', gates)
    pointer = re.fullmatch(r'/charainfo/(\d+)', str(rsrc.get('json_pointer') or ''))
    if not pointer:
        return _reject('CHARAINFO_POINTER_MISSING', gates)
    chara_hit, chara_err = unique_hit(tab['chara'], cid)
    if chara_err:
        return _reject('CHARAINFO_RECORD_%s' % chara_err, gates)
    chara_index, chara = chara_hit
    gates['charainfo'] = {'index': chara_index, 'cid': chara.get('cid'),
                          'pointer': int(pointer.group(1))}
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

    # ---- D2 句面逐字（不从日文片段或数字猜归属）
    if ABNORMAL_WORD in canon(row.get('japanese')):
        return _reject('ABNORMAL_CLAUSE', gates)
    if canon(row.get('japanese')) != canon(adm['text']):
        return _reject('ROW_TEXT_NOT_ADMITTED', gates)
    if body_of(row.get('japanese')) != body_of(adm['text']):
        return _reject('ROW_BODY_DRIFT', gates)
    if len(MECH_RX.findall(canon(row.get('japanese')))) != 1:
        return _reject('ROW_MECHANISM_NOT_UNIQUE', gates)

    # ---- D4 同文档位集合＝基档 1 条＋超共鳴 1 条（「同文」按剥离块标签的句身比较）
    text = canon(row.get('japanese'))
    body = body_of(row.get('japanese'))
    same_text = [(g, s, r) for g, s, r in entries
                 if g == 'special_move'
                 and str(s.get('reference_field') or '').startswith('pattern')
                 and body_of(r.get('japanese')) == body]
    gates['same_text_pattern_rows'] = [
        {'row_id': r.get('row_id'), 'reference_field': s.get('reference_field'),
         'skill_label': tier_label(s.get('original_text')),
         'row_label': tier_label(r.get('context_text')),
         'record_id': s.get('record_id')} for _, s, r in same_text]
    if len(same_text) != 2:
        return _reject('SAME_TEXT_TIER_SET_DRIFT', gates,
                       {'count': len(same_text),
                        'rows': gates['same_text_pattern_rows']})
    base = [x for x in same_text
            if tier_label(x[1].get('original_text')) == 'BASE'
            and tier_label(x[2].get('context_text')) == 'BASE']
    if len(base) != 1:
        return _reject('PEER_NOT_UNIQUE(%d)' % len(base), gates)
    peer_group, peer_skill, peer_row = base[0]
    if peer_row.get('row_id') != adm['peer_row_id']:
        return _reject('PEER_ROW_DRIFT', gates,
                       {'expected': adm['peer_row_id'], 'actual': peer_row.get('row_id')})
    if str(peer_skill.get('reference_field') or '') != adm['peer_ref']:
        return _reject('PEER_REF_DRIFT', gates)
    if peer_skill.get('table') != PATTERN_TABLE or peer_skill.get('layer') != LAYER:
        return _reject('PEER_TABLE_LAYER_DRIFT', gates,
                       {'table': peer_skill.get('table'), 'layer': peer_skill.get('layer')})
    if peer_skill.get('record_id') != adm['pattern_id']:
        return _reject('PEER_RECORD_ID_DRIFT', gates,
                       {'expected': adm['pattern_id'],
                        'actual': peer_skill.get('record_id')})
    if peer_row.get('cid') != cid:
        return _reject('PEER_CID_DRIFT', gates)
    gates['peer'] = {'row_id': peer_row.get('row_id'),
                     'reference_field': peer_skill.get('reference_field'),
                     'stage': peer_row.get('stage'), 'pattern_id': adm['pattern_id']}

    # ---- D5 基档行已交付同键同字段同记录同原值答案（不产生同主张双值行）
    hits = [a for a in (peer_row.get('answers') or [])
            if isinstance(a, dict) and a.get('rule_key') == RULE_KEY]
    if not hits:
        return _reject('PEER_MIRROR_MISSING', gates)
    if len(hits) != 1:
        return _reject('PEER_MIRROR_AMBIGUOUS(%d)' % len(hits), gates)
    peer_answer = hits[0]
    gates['peer_answer'] = _answer_view(peer_answer)
    if peer_answer.get('table') != BOSS_TABLE or peer_answer.get('layer') != LAYER:
        return _reject('PEER_ANSWER_TABLE_LAYER_DRIFT', gates)
    if str(peer_answer.get('field_path') or '') != FIELD:
        return _reject('PEER_ANSWER_FIELD_DRIFT', gates)
    if peer_answer.get('record_id') != adm['record_id']:
        return _reject('PEER_ANSWER_RECORD_DRIFT', gates,
                       {'expected': adm['record_id'],
                        'actual': peer_answer.get('record_id')})
    peer_raw_state = raw_state(peer_answer.get('raw_value'))
    if peer_raw_state != 'FINITE':
        return _reject('PEER_ANSWER_RAW_%s' % peer_raw_state, gates)
    if float(peer_answer['raw_value']) != float(adm['raw_value']):
        return _reject('PEER_MIRROR_VALUE_DRIFT', gates,
                       {'expected': adm['raw_value'],
                        'actual': peer_answer.get('raw_value')})
    if str(peer_answer.get('numeric_evidence') or '') != '确认' \
            or str(peer_answer.get('association_evidence') or '') != '推断':
        return _reject('PEER_EVIDENCE_DRIFT', gates,
                       {'numeric_evidence': peer_answer.get('numeric_evidence'),
                        'association_evidence': peer_answer.get('association_evidence')})
    if _num(adm['raw_value']) not in str(peer_answer.get('value') or ''):
        return _reject('PEER_VALUE_TEXT_DRIFT', gates)

    # ---- D6 超共鳴同文行存在且原值不同（档位标签是判别依据）
    supers = [x for x in same_text
              if tier_label(x[1].get('original_text')) == 'SUPER'
              and tier_label(x[2].get('context_text')) == 'SUPER']
    gates['super_rows'] = [{'row_id': r.get('row_id'),
                            'reference_field': s.get('reference_field'),
                            'record_id': s.get('record_id')} for _, s, r in supers]
    if len(supers) != 1:
        return _reject('SUPER_SIBLING_NOT_UNIQUE(%d)' % len(supers), gates)
    sup_skill, sup_row = supers[0][1], supers[0][2]
    if sup_row.get('row_id') != adm['super_row_id']:
        return _reject('SUPER_ROW_DRIFT', gates,
                       {'expected': adm['super_row_id'], 'actual': sup_row.get('row_id')})
    if sup_skill.get('record_id') != adm['super_pattern_id']:
        return _reject('SUPER_PATTERN_DRIFT', gates)
    sup_hits = [a for a in (sup_row.get('answers') or [])
                if isinstance(a, dict) and a.get('rule_key') == RULE_KEY]
    if len(sup_hits) != 1:
        return _reject('SUPER_ANSWER_NOT_UNIQUE(%d)' % len(sup_hits), gates)
    sup_answer = sup_hits[0]
    if sup_answer.get('record_id') != adm['super_record_id']:
        return _reject('SUPER_RECORD_DRIFT', gates,
                       {'expected': adm['super_record_id'],
                        'actual': sup_answer.get('record_id')})
    sup_state = raw_state(sup_answer.get('raw_value'))
    if sup_state != 'FINITE':
        return _reject('SUPER_RAW_%s' % sup_state, gates)
    if float(sup_answer['raw_value']) == float(adm['raw_value']):
        return _reject('SUPER_VALUES_NOT_DIFFERENT', gates,
                       {'base_raw_value': adm['raw_value'],
                        'super_raw_value': sup_answer.get('raw_value')})
    if float(sup_answer['raw_value']) != float(adm['super_raw_value']):
        return _reject('SUPER_RAW_VALUE_DRIFT', gates,
                       {'expected': adm['super_raw_value'],
                        'actual': sup_answer.get('raw_value')})
    gates['super_values'] = {'row_id': sup_row.get('row_id'),
                             'record_id': sup_answer.get('record_id'),
                             'raw_value': sup_answer.get('raw_value'),
                             'base_raw_value': adm['raw_value']}

    # ---- D7 原记录链（charainfo.pattern0→ bosspattern→skillid0→bossskill，唯一 type27）
    chain, chain_err = chain_of(tab, cid)
    if chain_err:
        return _reject('CHAIN_%s' % chain_err, gates)
    gates['chain'] = {'pointer': 'charainfo.pattern0',
                      'pattern_id': chain['pattern_id'],
                      'pattern_index': chain['pattern_index'],
                      'charainfo_index': chain['charainfo_index'],
                      'child_ids': [c['skillid'] for c in chain['children']],
                      'child_types': [c['type'] for c in chain['children']]}
    if chain['pattern_id'] != adm['pattern_id']:
        return _reject('PATTERN_POINTER_DRIFT', gates,
                       {'expected': adm['pattern_id'], 'actual': chain['pattern_id']})
    if chain['pattern_id'] != peer_skill.get('record_id'):
        return _reject('PATTERN_PEER_MISMATCH', gates,
                       {'pattern': chain['pattern_id'],
                        'peer_record': peer_skill.get('record_id')})
    carriers = [c for c in chain['children'] if c['type'] == CARRIER_TYPE]
    gates['carrier_records'] = [c['skillid'] for c in carriers]
    if len(carriers) != 1:
        return _reject('CARRIER_NOT_UNIQUE(%d)' % len(carriers), gates)
    bound = carriers[0]
    if bound['slot'] != 'skillid0':
        return _reject('CARRIER_SLOT_DRIFT', gates, {'slot': bound['slot']})
    if bound['skillid'] != adm['record_id']:
        return _reject('CARRIER_RECORD_DRIFT', gates,
                       {'expected': adm['record_id'], 'actual': bound['skillid']})
    gates['carrier'] = {'slot': bound['slot'], 'skillid': bound['skillid'],
                        'index': bound['index'], 'type': bound['type'],
                        'params': {k: v for k, v in bound['params'].items()}}
    raw = bound['params'].get(PARAM)
    state = raw_state(raw, present=PARAM in bound['params'])
    gates['params'] = {PARAM: raw,
                       LIMIT_FIELD: bound['params'].get(LIMIT_FIELD),
                       COUNT_FIELD: bound['params'].get(COUNT_FIELD)}
    gates['param_states'] = {
        PARAM: state,
        LIMIT_FIELD: raw_state(bound['params'].get(LIMIT_FIELD),
                               present=LIMIT_FIELD in bound['params']),
        COUNT_FIELD: raw_state(bound['params'].get(COUNT_FIELD),
                               present=COUNT_FIELD in bound['params']),
    }
    if state != 'FINITE':
        return _reject('PARAM_%s_%s' % (PARAM.upper(), state), gates, {PARAM: raw})
    if float(raw) <= 0:
        return _reject('PARAM_%s_NON_POSITIVE' % PARAM.upper(), gates, {PARAM: raw})
    if float(raw) != float(adm['raw_value']):
        return _reject('PARAM_VALUE_DRIFT', gates,
                       {'expected': adm['raw_value'], 'actual': raw})
    for field in (LIMIT_FIELD, COUNT_FIELD):
        st = gates['param_states'][field]
        if st != 'FINITE' or float(bound['params'][field]) <= 0:
            return _reject('PARAM_%s_%s' % (field.upper(), st), gates,
                           {field: bound['params'].get(field)})
    if [c['skillid'] for c in chain['children']] != adm['chain_ids']:
        return _reject('CHAIN_IDS_DRIFT', gates,
                       {'expected': adm['chain_ids'],
                        'actual': [c['skillid'] for c in chain['children']]})
    if [c['type'] for c in chain['children']] != adm['chain_types']:
        return _reject('CHAIN_TYPES_DRIFT', gates,
                       {'expected': adm['chain_types'],
                        'actual': [c['type'] for c in chain['children']]})

    # ---- D8 基档答案 source 指针必须指向同一 bossskill 记录
    source = peer_answer.get('source') if isinstance(peer_answer.get('source'), dict) else None
    gates['peer_source'] = source
    if source is None:
        return _reject('PEER_SOURCE_MISSING', gates)
    if source.get('source_key') != BOSS_SOURCE_KEY:
        return _reject('PEER_SOURCE_KEY_DRIFT', gates, {'source_key': source.get('source_key')})
    if source.get('table') != BOSS_TABLE or source.get('layer') != LAYER:
        return _reject('PEER_SOURCE_TABLE_LAYER_DRIFT', gates)
    if str(source.get('field') or '') != FIELD:
        return _reject('PEER_SOURCE_FIELD_DRIFT', gates, {'field': source.get('field')})
    if source.get('record_id') != bound['skillid']:
        return _reject('PEER_SOURCE_RECORD_DRIFT', gates,
                       {'source_record_id': source.get('record_id'),
                        'chain_record_id': bound['skillid']})
    expected_pointer = '/bossinfo/bossskill/%d' % bound['index']
    if source.get('json_pointer') != expected_pointer:
        return _reject('PEER_SOURCE_POINTER_DRIFT', gates,
                       {'expected': expected_pointer,
                        'actual': source.get('json_pointer')})
    if source.get('field_json_pointer') != expected_pointer + FIELD:
        return _reject('PEER_SOURCE_FIELD_POINTER_DRIFT', gates,
                       {'actual': source.get('field_json_pointer')})

    # ---- D9 句面唯一（基档 pattern 正文）
    sinfo = str(chain['pattern'].get('sinfo') or '')
    if not canon(sinfo):
        return _reject('PATTERN_SINFO_MISSING', gates)
    n_body = canon(sinfo).count(text)
    n_mech = len(MECH_RX.findall(canon(sinfo)))
    gates['sentence'] = {'body_occurrences': n_body, 'mechanism_occurrences': n_mech}
    if n_body != 1:
        return _reject('ROW_BODY_NOT_UNIQUE_IN_PATTERN', gates)
    if n_mech != 1:
        return _reject('MECHANISM_NOT_UNIQUE_IN_PATTERN', gates)

    # ---- D10 批前未答＋幂等（不覆盖既有答案）
    existing = [a for a in (row.get('answers') or []) if isinstance(a, dict)]
    key_hits = [a for a in existing if a.get('rule_key') == RULE_KEY]
    gates['existing_same_rule_key'] = [_answer_view(a) for a in key_hits]
    same_rec_value = [a for a in key_hits
                      if a.get('record_id') == bound['skillid']
                      and raw_state(a.get('raw_value')) == 'FINITE'
                      and float(a['raw_value']) == float(raw)]
    if same_rec_value:
        return _reject('ALREADY_PRESENT_SAME', gates)
    if key_hits:
        same_value = [a for a in key_hits if raw_state(a.get('raw_value')) == 'FINITE'
                      and float(a['raw_value']) == float(raw)]
        return _reject('ALREADY_ANSWERED', gates,
                       {'dedup': ('SAME_VALUE_DIFF_RECORD_EXISTING' if same_value
                                  else 'CONFLICT_EXISTING_VALUE'),
                        'existing': gates['existing_same_rule_key'],
                        'selected': {'record_id': bound['skillid'], 'raw_value': raw}})
    other_claims = [a for a in existing
                    if a.get('table') == BOSS_TABLE and str(a.get('field_path') or '') == FIELD]
    if other_claims:
        return _reject('ALREADY_ANSWERED', gates,
                       {'dedup': 'OTHER_RECORD_SAME_FIELD',
                        'existing': [_answer_view(a) for a in other_claims]})

    # ---- D11 账本效果 1:1（一条答案恰关闭一个未解主张）
    effects = None
    if ledger:
        try:
            import effect_ledger as ledger_mod
        except Exception as exc:  # pragma: no cover - 环境缺模块时显式失败
            return _reject('LEDGER_UNAVAILABLE', gates, {'error': repr(exc)})
        probe = dict(row)
        probe['answers'] = [a for a in existing if a.get('rule_key') != RULE_KEY]
        analyzed = ledger_mod.analyze_row(probe, TABLE)
        effects = analyzed.get('effects') or []
        unresolved = [e.get('effect_type') for e in effects
                      if e.get('status') == 'unresolved']
        gates['effects'] = {'count': len(effects),
                            'unresolved': unresolved,
                            'all_types': [e.get('effect_type') for e in effects]}
        if len(effects) != 1 or unresolved != ['回復（词表外）']:
            return _reject('EFFECT_SET_MISMATCH', gates)

    return {'accepted': True, 'rejection': None, 'gates': gates, 'claim': RULE_KEY,
            'clause': {'kind': 'periodic_heal', 'text': adm['text']},
            'adm': adm, 'skill': skill, 'peer_skill': peer_skill, 'peer_row': peer_row,
            'peer_answer': peer_answer, 'super_skill': sup_skill, 'super_row': sup_row,
            'super_answer': sup_answer, 'pattern_id': chain['pattern_id'],
            'chain': chain, 'bound': bound, 'params': {PARAM: raw},
            'extra_params': {LIMIT_FIELD: bound['params'].get(LIMIT_FIELD),
                             COUNT_FIELD: bound['params'].get(COUNT_FIELD)},
            'existing': existing, 'effects': effects, 'detail': None}


# ---------------------------------------------------------------- 答案构造
def _source(bound, chain, adm):
    pointer = '/bossinfo/bossskill/%d' % bound['index']
    return {
        'table': BOSS_TABLE, 'record_id': bound['skillid'], 'layer': LAYER,
        'field_path': FIELD,
        'source_key': BOSS_SOURCE_KEY,
        'original_file': 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw',
        'json_pointer': pointer,
        'field': FIELD,
        'field_json_pointer': pointer + FIELD,
        'record_key': '%s#%s' % (BOSS_SOURCE_KEY, pointer),
        'source_resolution': 'RESOLVED_EXACT_DECODED_RECORD',
        'snapshot_id': SNAPSHOT_ID,
        'note': ('按解码 JSON 的 bossinfo.bossskill 记录号唯一命中；经同卡基档行 %s'
                 '（charainfo.pattern0 / pattern %s）链内唯一 type27（skillid0）定源；'
                 '本行 skilltext 只作同卡同档位镜像，无独立执行链'
                 % (adm['peer_row_id'], chain['pattern_id'])),
    }


def _value_text(adm, chain, bound, params, sup):
    """值文：既有 C8 公式句＋镜像来源＋p2/p3 只披露＋超共鳴排除披露。"""
    num = _num(params[PARAM])
    return ('周期回复输入：floor/clamp(float32(B × {n}))（B=getBasicSkillAttack(true)，'
            '已含 Chain；整数化 0x14374bc）；对象：味方全体（句面）；镜像行'
            '（0 新增唯一数值）：同卡基档行 {peer}（{ref} / pattern {pid}）已交付同规则键'
            '同记录同原值 {n}；本行 skilltext 文本块标签为【共鳴必殺】（非超共鳴），按同卡'
            '同文基础档镜像归位到 bossskill 记录 {rec} 的 skillparam1={n}；回复间隔字段 '
            'skillparam2={p2} 游戏秒、回复次数字段 skillparam3={p3} 次（已确认字段值，'
            '不换算实机间隔）；不证明最终 HP 回复量、超上限保留比例、实际触发间隔与次数；'
            '同文超共鳴行 {sup}（{sref} / pattern {spid}）原值 {sraw}（记录 {srec}）只披露、'
            '不并入（关联推断）'
            .format(n=num, peer=adm['peer_row_id'], ref=adm['peer_ref'],
                    pid=chain['pattern_id'], rec=bound['skillid'],
                    p2=_num(params[LIMIT_FIELD]), p3=_num(params[COUNT_FIELD]),
                    sup=adm['super_row_id'], sref=adm['super_ref'],
                    spid=adm['super_pattern_id'], sraw=_num(adm['super_raw_value']),
                    srec=adm['super_record_id']))


def _marker(adm, chain, bound, params, sup_answer, gates):
    return {
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'module': MODULE_VERSION,
        'cid': adm['cid'],
        'row_id': adm['row_id'],
        'rule_key': RULE_KEY,
        'field_path': FIELD,
        'table': BOSS_TABLE,
        'record_id': bound['skillid'],
        'layer': LAYER,
        'carrier_type': CARRIER_TYPE,
        'carrier_slot': bound['slot'],
        'carrier_record_type': bound['type'],
        'row_tier_label': (gates.get('tier') or {}).get('row_label'),
        'peer_row_id': adm['peer_row_id'],
        'peer_reference_field': adm['peer_ref'],
        'peer_stage': (gates.get('peer') or {}).get('stage'),
        'pattern_id': chain['pattern_id'],
        'pattern_pointer': 'charainfo.pattern0',
        'pattern_index': chain['pattern_index'],
        'charainfo_index': chain['charainfo_index'],
        'chain_ids': [c['skillid'] for c in chain['children']],
        'chain_types': [c['type'] for c in chain['children']],
        'params': {PARAM: params[PARAM]},
        'field_values_disclosed': {
            LIMIT_FIELD: {'raw': params[LIMIT_FIELD], 'unit': '游戏秒（fixedDeltaTime累计）',
                          'meaning_zh': '回复间隔输入（存入 _regenerationTimeMax）',
                          'answer_written': False},
            COUNT_FIELD: {'raw': params[COUNT_FIELD], 'unit': '次',
                          'meaning_zh': '回复次数（向零截断后存入 _regenerationNum）',
                          'answer_written': False},
        },
        'super_row': {'row_id': adm['super_row_id'],
                      'reference_field': adm['super_ref'],
                      'pattern_id': adm['super_pattern_id'],
                      'record_id': sup_answer.get('record_id'),
                      'raw_value': sup_answer.get('raw_value')},
        'same_text_pattern_rows': gates.get('same_text_pattern_rows'),
        'peer_mirror': gates.get('peer_answer'),
        'existing_same_rule_key': gates.get('existing_same_rule_key'),
        'effects_at_eval': gates.get('effects'),
        'not_written': ('p2/p3 只作字段值披露，不写答案、不换算实机秒数与次数；'
                        '「全状態異常も回復」等其余子句、最终 HP 回复量与超上限保留比例、'
                        'Boss 模式 pattern 选取均不写'),
        'admission': ('SAME_CARD_SAME_TEXT_BASE_TIER_UNIQUE_PEER_MIRROR'
                      '（同卡同文＋同块【共鳴必殺】标签＋唯一基档行＋超共鳴同文异值＋'
                      'charainfo.pattern0→bosspattern→skillid0→bossskill 逐位相等＋'
                      '批前未答＋效果 1:1）'),
        'association': '推断',
        'limits': LIMIT,
    }


def build_answers(data, cid, row, res, tab=None):
    """为本行构造答案（数量恰 1）；任何规则缺失即返回 None（不静默沿用）。"""
    import rules as R
    if not res.get('accepted'):
        return None
    adm = res['adm']
    chain, bound, params = res['chain'], res['bound'], res['params']
    raw = params[PARAM]
    converted = R.answer_for(BOSS_TABLE, CARRIER_TYPE, FIELD, raw, bound['record'],
                             source_layer=LAYER)
    if converted is None:
        return None
    rule = R.rule_for(BOSS_TABLE, CARRIER_TYPE, FIELD) or {}
    if not rule or '已确认' not in str(rule.get('status') or ''):
        return None
    value = _value_text(adm, chain, bound, bound['params'], res['super_answer'])
    if any(word in value for word in FORBIDDEN_PHRASES):
        return None
    if _num(raw) not in value:
        return None
    marker = _marker(adm, chain, bound, bound['params'], res['super_answer'], res['gates'])
    answer = {
        'value': value,
        'quantity_kind': converted.get('quantity_kind'),
        'unit': converted.get('unit'),
        'value_text': converted.get('value_text'),
        'raw_value': raw,
        'effective_float32': _f32(raw),
        'quantitative': True,
        'numeric_source': '复用既有已确认规则＋同卡基档行同键同字段同记录同原值；本行归属为推断',
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'evidence_scope': SCOPE,
        'answer_status': 'CONFIRMED_FORMULA_ONLY',
        'rule_key': RULE_KEY,
        'table': BOSS_TABLE,
        'record_id': bound['skillid'],
        'layer': LAYER,
        'field_path': FIELD,
        'source': _source(bound, chain, adm),
        'rule_status': rule.get('status'),
        'conversion': rule.get('conversion'),
        'base_definition': rule.get('base_definition'),
        'conditions': rule.get('applicability'),
        'rule_limits': rule.get('limits'),
        'condition_label': ('本行 skilltext 属【共鳴必殺】档；同卡基档行 %s（%s / pattern %s）'
                            '链内唯一 type27（skillid0）生效时'
                            % (adm['peer_row_id'], adm['peer_ref'], chain['pattern_id'])),
        'target': '味方全体（由句面给出；rules.target 为空，受疗对象选择未复查）',
        'binding': {BINDING_KEY: marker},
        'context': 'skilltext 同卡同档位镜像行（t27 周期回复）',
        'note': ('仅已确认静态规则下单次回复系数的同卡镜像实例；同卡同文＋唯一基档行＋'
                 '原记录链逐位相等，关联仍为推断；0 新增唯一数值、0 新规则键；'
                 '不写最终 HP、不写行完整。' + LIMIT),
        'evidence': EVIDENCE[:],
    }
    return [answer]


# ---------------------------------------------------------------- 行级写入
_NOTE_PREFIX = 'C13-P2：'
_STALE_REASONS = {
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应',
}


def apply_answers(row, answers, res, *, change_row_class=True):
    """把本行答案写入行（只追加，不覆盖；不删 S7/hint 文本）。"""
    key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    existing = {key(a) for a in row.get('answers') or []}
    added = 0
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault('answers', []).append(answer)
        existing.add(key(answer))
        added += 1
    if not added:
        return 0
    adm = res['adm']
    if change_row_class:
        row['row_class'] = 'A'
        row['partial'] = True
        row['evidence_label'] = ('推断（C13-P2 skilltext 同卡同档位 t27 镜像：同卡同文＋唯一基档行'
                                '已交付同键同记录同原值＋原记录链逐位相等；0 新增唯一数值）')
    row['evidence'] = '推断'
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = list(dict.fromkeys([str(s) for s in scopes] + [SCOPE]))
    reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
    reasons.append(_NOTE_PREFIX + 'skilltext 同卡同档位镜像——同卡基档行 %s（%s / pattern %s）'
                   '链内唯一 type27（记录 %s）已交付同规则键同字段同原值 skillparam1=%s；'
                   '本行按同卡同文＋【共鳴必殺】标签＋超共鳴同文异值归位（0 新增唯一数值）；'
                   'skillparam2=%s 游戏秒／skillparam3=%s 次只作已确认字段值披露；'
                   '同句「全状態異常も回復」等其余机制、最终 HP、实机间隔与次数、'
                   'Boss 模式 pattern 选取仍未验证。'
                   % (adm['peer_row_id'], adm['peer_ref'], res['pattern_id'],
                      res['bound']['skillid'], _num(res['params'][PARAM]),
                      _num(res['extra_params'][LIMIT_FIELD]),
                      _num(res['extra_params'][COUNT_FIELD])))
    row['unknown_reasons'] = list(dict.fromkeys(reasons))
    marker = row.setdefault(MARKER_KEY, dict(answers[0]['binding'][BINDING_KEY]))
    marker.setdefault('bindings', [])
    for answer in answers:
        m = answer['binding'][BINDING_KEY]
        marker['bindings'].append({'rule_key': m['rule_key'], 'field_path': m['field_path'],
                                   'record_id': m['record_id'], 'params': m['params']})
    marker['bindings'] = list({(b['rule_key'], b['field_path']): b
                               for b in marker['bindings']}.values())
    return added


def _merge_disclosure(row, res):
    adm = res.get('adm') or ADMITTED.get(row.get('row_id')) or {}
    marker = row.setdefault(MARKER_KEY, {
        'scope': SCOPE, 'module': MODULE_VERSION, 'row_id': row.get('row_id'),
        'bindings': []})
    marker.setdefault('disclosures', []).append({
        'dedup': (res.get('detail') or {}).get('dedup'),
        'rule_key': RULE_KEY,
        'existing': (res.get('detail') or {}).get('existing'),
        'selected': (res.get('detail') or {}).get('selected'),
        'peer_row_id': adm.get('peer_row_id'),
        'disclosure': ('本行已有同 rule_key 答案；本批选中的记录与原值如 selected，'
                       '不新增答案、不改写既有值，只披露。'),
    })


# ---------------------------------------------------------------- 正式页消费
def apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None):
    """正式页消费（候选未接线）：只为声明范围内卡片的冻结 skilltext 行写镜像答案。

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
    rows = {r.get('row_id'): r for _, _, r in card_rows(groups)}
    for adm in sorted(ADMITTED.values(), key=lambda a: a['row_id']):
        if adm['cid'] != cid:
            continue
        row = rows.get(adm['row_id'])
        if row is None:
            report['rejections'].append({'row_id': adm['row_id'], 'reason': 'ROW_NOT_FOUND'})
            continue
        report['evaluated'] += 1
        report['in_scope_rows'].append(adm['row_id'])
        res = evaluate(data, cid, row, groups=groups, tab=tab)
        if not res['accepted']:
            code = res['rejection']
            if code == 'ALREADY_PRESENT_SAME':
                report['skipped_existing'] += 1
            elif code == 'ALREADY_ANSWERED':
                _merge_disclosure(row, res)
                report['disclosures'].append({'row_id': adm['row_id'], 'reason': code,
                                              'detail': res.get('detail')})
            else:
                report['rejections'].append({'row_id': adm['row_id'], 'reason': code,
                                             'detail': res.get('detail')})
            continue
        answers = build_answers(data, cid, row, res, tab=tab)
        if answers is None:
            report['rejections'].append({'row_id': adm['row_id'],
                                         'reason': 'RULE_UNAVAILABLE'})
            continue
        added = apply_answers(row, answers, res)
        if added:
            report['answers_added'] += added
            report['rows_changed'] += 1
            for answer in answers:
                report['additions'].append({'row_id': adm['row_id'],
                                            'rule_key': answer['rule_key'],
                                            'record_id': answer['record_id'],
                                            'field_path': answer['field_path'],
                                            'raw_value': answer['raw_value']})
        else:
            report['skipped_existing'] += 1
    return report


if __name__ == '__main__':
    raise SystemExit('候选模块不提供写入口；只读探针请用 '
                     'output/character_skills/c13_p2_t27_mirror_20261031/check_candidate.py'
                     '（本批不运行正式生成）')
