# -*- coding: utf-8 -*-
"""C14-P2 ``charainfo.pattern0`` → ``bossskill`` 直接链伤害行（候选实现，10 行 / 9 卡）。

任务卡 ``docs/tasks/20261102-c14-p2-boss-damage-direct.md``；C14 总卡
``docs/tasks/20261102-c14-cycle.md``；方案 ``docs/角色技能完整解读实施方案.md``
（2026-11-02 现行）。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；
``rules.json``／``rules.py``／``effect_ledger.py``／正式 ``pages``／账本均未改动；
本阶段不运行正式全库生成。模块只读：
``output/cache_full_20261015_v3/decoded/{charainfo,bossinfo,denju}.data5.json.raw``、
同快照 ``decode_report.json``、``profiles/rules.json`` 与当前正式
``pages/<cid>/card.json``；输出只写自身候选目录。

本批做什么
----------
只处理 Y.G. 卡 ``charainfo.skilltext`` 行中**自身经** ``charainfo.pattern0`` →
``bosspattern`` → ``bossskill`` 可直接定源的对敌伤害段。每行重新满足（逐行硬门，
任一不符即拒绝，不猜、不取邻近档位）：

R1  **行身份**：当前正式页 ``row_id`` 在冻结表内；``group == special_move``、
    ``reference_field == skilltext``、``table == charainfo``、``record_id == cid``、
    ``layer == CACHE``；``fragment_index`` 与冻结表一致。
R2  **父记录**：CACHE ``charainfo[cid]`` 存在；页内 ``skill.original_text``、
    行 ``context_text`` 与 ``charainfo.skilltext`` 逐字（canon）相同；行日语片段是父文本
    的逐字子串；行的 ``source`` 指针等于该记录在解码表中的实际下标
    ``/charainfo/<i>``／``/charainfo/<i>/skilltext``。
R3  **链可达**：``charainfo.pattern0`` 非空，在该层 ``bosspattern`` 唯一命中；
    ``pattern.sinfo`` 与父文本逐字相同；``skillid0..N`` 槽位从 0 连续，每个子记录在
    ``bossskill`` 全表唯一命中。
R4  **句面**：行日语片段必须是**对敌伤害实例**（含「ダメージ」、含「敵」；含「受ける／受け／
    味方」或「ダメージが上がる／下がる／増／減」即拒绝）；形态分 MULTIHIT／BIGMID／INTERVAL／
    PLAIN，PLAIN（无 N回・大／中・一定間隔限定）拒绝。
R5  **形态选型唯一**：``N回ダメージ`` → 多段型 type105／110 且 ``skillparam6 == N`` **恰 1 条**；
    大／中／一定間隔 → 单发型 type3／22／55／74 **恰 1 条**。同链多条候选即拒绝
    （不按值相同任取）；同父文本另一片段落到同一子记录也拒绝。
R6  **槽位唯一**：``profiles/rules.json`` 中该 type 的已确认规则里**恰有 1 条**伤害倍率槽
    （unit 含「倍／相对」），且与冻结表槽位相同；否则拒绝。
R7  **原值分档**：缺失／null／非有限／负值／真零分别拒绝；命中值必须 FINITE 且 > 0。
R8  **来源**：答案 ``source`` 直接指向选中 ``bossskill`` 记录的 JSON 指针与字段；
    重新从解码 JSON 读该下标，``skillid``、字段原值与页面链选中值逐位相等；不取
    ``charainfo``、``pattern`` 或同卡其他答案作数值来源。
R9  **冻结与幂等**：``(row_id, pattern_id, child_slot, record_id, type, slot, raw,
    rule_key)`` 必须与冻结准入表逐项相等；本行已有同 ``rule_key`` 答案时不新增、不改写
    （同记录同值 → ``SKIP_ALREADY_PRESENT``；其余 → 拒绝并登记）。
R10 **范围**：只读 CACHE；APK 同名主表**从不打开**（静态可核）；保护卡
    30236／30239、30102、20234 与 denju 行在结构上不可达或显式拒绝。

明确不处理
----------
* denju 非首段 6 行（7250 f1／f2、30105 f2、30301 f1、30329 f1、30334 f2）**保持未知**；
  本模块不评估其链、不复制对应 ``charainfo`` 新答案。denju 原始链独立于 charainfo
  （7250 的 ``denju.patternid0=40725003`` 是另一条 pattern），即使记录号相同也不合并。
* 30102、20234、30236、30239 不处理；APK 同号记录不与 CACHE 合并。
* 同卡其他档位（pattern1..4，含超共鳴）逐行登记为排除值，不并入、不反推。
* 最终扣血、保证命中、运行时选档、弹射／ダウン／状态异常、t16、1095、t11／t84 等不在本批。

证据分档（不得升格）
--------------------
R1–R3、R5 的 ``param6``、R6、R7、R8 是结构／类型／原值证据；R4 的「N回 ↔ param6」「大／中／
一定間隔 ↔ 单发型」是类型语义＋一致性推断。因此答案 ``numeric_evidence = 确认``、
``association_evidence = 推断``、``evidence_scope = BY_TYPE_EXTRAPOLATED``、
``answer_status = CONFIRMED_FORMULA_ONLY``；不写最终伤害、不写秒数、不称实机验证。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import unicodedata
from pathlib import Path

MODULE_VERSION = 'c14_p2_boss_damage_direct_20261102'
#: 账本消费用 scope：复用既有 G1-B1 来源限定窄映射（effect_ledger.G1B1_SCOPE）。
LEDGER_SCOPE = 'G1_B1_MIRROR_20261029'
#: 本批自身结构 marker scope（行级 marker 与答案 binding 附带）。
STRUCTURE_SCOPE = 'C14_P2_BOSS_DAMAGE_DIRECT_20261102'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'

SNAPSHOT_REL = 'output/cache_full_20261015_v3'
DECODED_REL = SNAPSHOT_REL + '/decoded'
PAGES_REL = 'output/character_skills/pages'
RULES_REL = 'output/character_skills/profiles/rules.json'
DECODE_REPORT_REL = SNAPSHOT_REL + '/decode_report.json'
OUT_DIR_REL = 'output/character_skills/c14_p2_boss_damage_direct_20261102'

#: 只有这些 CID 的 charainfo.skilltext 行可能准入（9 卡 10 行）。
ADMITTED_CIDS = (7250, 30105, 30107, 30220, 30223, 30225, 30301, 30329, 30334)
#: 保护卡：G0 豁免不扩大（任务卡 §明确排除）。
ZERO_TOUCH_CIDS = frozenset({30236, 30239})
#: 边界卡：显式不处理，只登记排除（30102 任务卡点名；20234 为 APK 层保护项）。
OUT_OF_SCOPE_CIDS = frozenset({30102, 20234})
#: 排除清单需覆盖的页面（9 准入卡 + 4 边界卡）。
INVENTORY_CIDS = tuple(ADMITTED_CIDS) + (30102, 30236, 30239, 20234)

#: 类型 → 已确认伤害槽（逐键取自 profiles/rules.json，本批不新增键）。
DAMAGE_SLOT = {3: 'skillparam1', 22: 'skillparam1', 55: 'skillparam1',
               74: 'skillparam5', 105: 'skillparam1', 110: 'skillparam1'}
SINGLE_TYPES = (3, 22, 55, 74)
MULTI_TYPES = (105, 110)
#: effect_ledger.G1B1_RULE_EFFECT 覆盖的 6 个既有确认规则键。
LEDGER_MAPPED_RULE_KEYS = frozenset('bossskill|%d|/%s' % (t, s)
                                    for t, s in DAMAGE_SLOT.items())

#: 冻结准入表（2026-11-02 逐行从 CACHE 重导后冻结）。任何一项不同即拒绝。
FROZEN = (
    dict(cid=7250, fragment_index=1,
         row_id='7250-special_move-special_move-skilltext-lvorder3-f1',
         pattern_id=40725000, mode='MULTIHIT', n=10, child_slot=2,
         record_id=40725002, type=105, slot='skillparam1', raw=1,
         rule_key='bossskill|105|/skillparam1'),
    dict(cid=7250, fragment_index=2,
         row_id='7250-special_move-special_move-skilltext-lvorder3-f2',
         pattern_id=40725000, mode='BIGMID', n=None, child_slot=3,
         record_id=40725003, type=22, slot='skillparam1', raw=15,
         rule_key='bossskill|22|/skillparam1'),
    dict(cid=30105, fragment_index=2,
         row_id='30105-special_move-special_move-skilltext-lvorder2-f2',
         pattern_id=43010500, mode='MULTIHIT', n=5, child_slot=1,
         record_id=43010501, type=110, slot='skillparam1', raw=8,
         rule_key='bossskill|110|/skillparam1'),
    dict(cid=30107, fragment_index=3,
         row_id='30107-special_move-special_move-skilltext-lvorder2-f3',
         pattern_id=43010700, mode='MULTIHIT', n=6, child_slot=2,
         record_id=43010702, type=110, slot='skillparam1', raw=4,
         rule_key='bossskill|110|/skillparam1'),
    dict(cid=30220, fragment_index=1,
         row_id='30220-special_move-special_move-skilltext-lvorder2-f1',
         pattern_id=43022000, mode='MULTIHIT', n=2, child_slot=1,
         record_id=43022001, type=110, slot='skillparam1', raw=12.5,
         rule_key='bossskill|110|/skillparam1'),
    dict(cid=30223, fragment_index=3,
         row_id='30223-special_move-special_move-skilltext-lvorder2-f3',
         pattern_id=43022300, mode='BIGMID', n=None, child_slot=2,
         record_id=43022302, type=3, slot='skillparam1', raw=15,
         rule_key='bossskill|3|/skillparam1'),
    dict(cid=30225, fragment_index=1,
         row_id='30225-special_move-special_move-skilltext-lvorder3-f1',
         pattern_id=43022500, mode='MULTIHIT', n=5, child_slot=1,
         record_id=43022502, type=110, slot='skillparam1', raw=5,
         rule_key='bossskill|110|/skillparam1'),
    dict(cid=30301, fragment_index=1,
         row_id='30301-special_move-special_move-skilltext-lvorder3-f1',
         pattern_id=43030100, mode='MULTIHIT', n=5, child_slot=1,
         record_id=43030102, type=110, slot='skillparam1', raw=8,
         rule_key='bossskill|110|/skillparam1'),
    dict(cid=30329, fragment_index=1,
         row_id='30329-special_move-special_move-skilltext-lvorder3-f1',
         pattern_id=43032900, mode='MULTIHIT', n=8, child_slot=1,
         record_id=43032901, type=110, slot='skillparam1', raw=5,
         rule_key='bossskill|110|/skillparam1'),
    dict(cid=30334, fragment_index=2,
         row_id='30334-special_move-special_move-skilltext-lvorder3-f2',
         pattern_id=43033400, mode='MULTIHIT', n=10, child_slot=2,
         record_id=43033402, type=110, slot='skillparam1', raw=4,
         rule_key='bossskill|110|/skillparam1'),
)
FROZEN_BY_ROW = {item['row_id']: item for item in FROZEN}

#: 冻结行文本身份（``sha256(canon(japanese))``）：页面行文与冻结时逐字一致才准入。
FROZEN_TEXT_SHA256 = {
    '7250-special_move-special_move-skilltext-lvorder3-f1':
        '1b197b6139a3140d80d1119f570e3e372b376c64f63567f17ffcd19efda20184',
    '7250-special_move-special_move-skilltext-lvorder3-f2':
        '9433fc7057a58d2237453648828be1ba99fddb18a1d5e8c8f0bfef983080f1ef',
    '30105-special_move-special_move-skilltext-lvorder2-f2':
        '25e5bbd3ff055555f60b5d387dbe28933c2aadb210af9a69958364a1c31e7727',
    '30107-special_move-special_move-skilltext-lvorder2-f3':
        '716aad85bd4a63874fcde8bc9c2acd1f4e337a2d581fa8e6dc283e0efc5cd053',
    '30220-special_move-special_move-skilltext-lvorder2-f1':
        'de69cf15d9322a5758bbc04e5405048a5309e7f43d62555b932df68a452fcefb',
    '30223-special_move-special_move-skilltext-lvorder2-f3':
        '9433fc7057a58d2237453648828be1ba99fddb18a1d5e8c8f0bfef983080f1ef',
    '30225-special_move-special_move-skilltext-lvorder3-f1':
        'd92ce4cf5e2e05e76a797bc636bb7521b90062a79d2a63e9ca542a0f05bb4756',
    '30301-special_move-special_move-skilltext-lvorder3-f1':
        '7a98f2a6dada01e030204d2d31756105c94115bac05b086ba337a6dacd937e21',
    '30329-special_move-special_move-skilltext-lvorder3-f1':
        '38866f29cce59d6ec19614187701594099bf0cc31e4c648bc0ec8ddb323c7a4d',
    '30334-special_move-special_move-skilltext-lvorder3-f2':
        'cbf82dafd4271902a89259d7694850be1b368fe13332dd2de7c0b2c65f6fef64',
}

#: 任务卡点名的 denju 非首段 6 行：只登记排除，不评估、不复制。
DENJU_NON_FIRST_ROWS = (
    '7250-denju-denju-denju_denju_id____cid-lvorder0-f1',
    '7250-denju-denju-denju_denju_id____cid-lvorder0-f2',
    '30105-denju-denju-denju_denju_id____cid-lvorder0-f2',
    '30301-denju-denju-denju_denju_id____cid-lvorder0-f1',
    '30329-denju-denju-denju_denju_id____cid-lvorder0-f1',
    '30334-denju-denju-denju_denju_id____cid-lvorder0-f2',
)
_DENJU_ROW_SET = frozenset(DENJU_NON_FIRST_ROWS)

MULTIHIT_RX = re.compile(r'(\d+)回ダメージ')
BIGMID_RX = re.compile(r'(?:大|中)ダメージ')
INTERVAL_RX = re.compile(r'一定間隔でダメージ')
RECEIVE_MARKS = ('受ける', '受け', '味方')
MODIFIER_MARKS = ('ダメージが上がる', 'ダメージが下がる', 'ダメージが増', 'ダメージが減')
TAG_RX = re.compile(r'^(?:【[^】]*】)+')
FIRST_TAG_RX = re.compile(r'^【([^】]*)】')
WANTED_TITLE_RX = re.compile(r'《Y\.G\.')

MARKER_KEY = 'inference_c14_p2_boss_damage_direct'

#: 与 G1／C7-P3 同一处「未知原因」清理口径（本批覆盖伤害子句后这些理由失效）。
_STALE_REASONS = {
    '原文未提供该效果数值，尚无已审定的句内字段归属',
    '此描述尚无可适用的已确认数值或新增机制证据',
    '尚无已审定的句内字段归属；原文数字仅确认原文，不猜参数对应',
}

MODE_LABEL = {'MULTIHIT': '%d回ダメージ', 'BIGMID': '大／中ダメージ',
              'INTERVAL': '一定間隔ダメージ'}


# ---------------------------------------------------------------- 纯函数

def canon(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def first_tag(japanese):
    m = FIRST_TAG_RX.match(str(japanese or ''))
    return m.group(1) if m else None


def classify_clause(japanese):
    """片段 → 伤害子句形态 ``(form, detail)``；form∈{MULTIHIT,BIGMID,INTERVAL,PLAIN,None}。"""
    text = str(japanese or '')
    if 'ダメージ' not in text:
        return None, {'reason': 'NO_DAMAGE_WORD'}
    for mark in MODIFIER_MARKS:
        if mark in text:
            return None, {'reason': 'DAMAGE_MODIFIER_NOT_INSTANCE', 'mark': mark}
    for mark in RECEIVE_MARKS:
        if mark in text:
            return None, {'reason': 'DAMAGE_RECEIVER_NOT_ENEMY', 'mark': mark}
    if '敵' not in text:
        return None, {'reason': 'NO_ENEMY_TARGET'}
    m = MULTIHIT_RX.search(text)
    if m:
        return 'MULTIHIT', {'n': int(m.group(1)), 'clause': m.group(0)}
    m = BIGMID_RX.search(text)
    if m:
        return 'BIGMID', {'clause': m.group(0)}
    m = INTERVAL_RX.search(text)
    if m:
        return 'INTERVAL', {'clause': m.group(0)}
    return 'PLAIN', {'reason': 'DAMAGE_WITHOUT_QUALIFIER'}


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


def f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def num_text(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return ('%.6f' % f).rstrip('0').rstrip('.')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def is_damage_multiplier_rule(rule):
    """已确认规则是否为伤害倍率槽：unit 同时含「倍」与「相对」。"""
    unit = str((rule or {}).get('unit') or '')
    return '倍' in unit and '相对' in unit


def unique_damage_slot(rules, etype):
    """该 type 在 rules.json 中恰有 1 条伤害倍率槽时返回 ``(slot, keys)``，否则 ``(None, keys)``。"""
    prefix = 'bossskill|%d|/' % etype
    keys = sorted(k for k in rules if k.startswith(prefix)
                  and is_damage_multiplier_rule(rules[k]))
    if len(keys) != 1:
        return None, keys
    return keys[0].rsplit('/', 1)[1], keys


# ---------------------------------------------------------------- 输入（只读 CACHE）

class Inputs:
    """只读输入集合：解码 JSON + 声明哈希 + rules + 当前正式页。

    **不打开** 任何 APK 主表；结构上没有跨层取值分支。
    """

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.decoded = self.root / DECODED_REL
        self.pages = self.root / PAGES_REL
        self.rules_path = self.root / RULES_REL
        self.decode_report_path = self.root / DECODE_REPORT_REL
        self.versions = {}
        self.rules = json.loads(self.rules_path.read_text(encoding='utf-8'))
        self._load_verified('charainfo')
        self._load_verified('bossinfo')
        self._load_verified('denju')
        self._cards = {}

    # -- 哈希核对（声明值来自同快照 decode_report.json）
    def _load_verified(self, stem):
        report = json.loads(self.decode_report_path.read_text(encoding='utf-8'))
        filename = stem + '.data5'
        entry = next((f for f in report.get('files') or []
                      if f.get('filename') == filename), None)
        if entry is None:
            raise ValueError('decode_report 缺少声明: %s' % filename)
        path = self.decoded / (stem + '.data5.json.raw')
        actual = sha256_file(path)
        declared = entry.get('json_raw_sha256')
        if declared != actual:
            raise ValueError('输入哈希与声明不符: %s declared=%s actual=%s'
                             % (path, declared, actual))
        doc = json.loads(path.read_text(encoding='utf-8-sig'))
        self.versions[stem] = {
            'path': path.relative_to(self.root).as_posix(),
            'declared_sha256': declared,
            'actual_sha256': actual,
            'match': True,
        }
        if stem == 'charainfo':
            self.charainfo_rows = doc['charainfo']
            self.charainfo_index = {r['cid']: i for i, r in enumerate(self.charainfo_rows)}
            self.charainfo = {r['cid']: r for r in self.charainfo_rows}
        elif stem == 'bossinfo':
            boss = doc['bossinfo']
            self.pattern_docs = boss.get('bosspattern') or []
            self.skill_docs = boss.get('bossskill') or []
            self.pattern_index = {}
            for i, rec in enumerate(self.pattern_docs):
                self.pattern_index.setdefault(rec.get('patternid'), []).append(i)
            self.skill_index = {}
            for i, rec in enumerate(self.skill_docs):
                self.skill_index.setdefault(rec.get('skillid'), []).append(i)
            self.patterns = {pid: self.pattern_docs[idx[0]]
                             for pid, idx in self.pattern_index.items()}
            self.skills = {sid: self.skill_docs[idx[0]]
                           for sid, idx in self.skill_index.items()}
        elif stem == 'denju':
            rows = doc['denju']
            self.denju = {}
            for rec in rows:
                did = rec.get('denju_id')
                self.denju.setdefault(did, []).append(rec)

    # -- 页面
    def card(self, cid):
        if cid not in self._cards:
            path = self.pages / str(cid) / 'card.json'
            self._cards[cid] = {
                'path': path,
                'sha256': sha256_file(path),
                'doc': json.loads(path.read_text(encoding='utf-8')),
            }
        return self._cards[cid]['doc']

    def page_sha256(self, cid):
        self.card(cid)
        return self._cards[cid]['sha256']

    def card_title(self, cid):
        doc = self.card(cid)
        for field in (doc.get('basic') or {}).get('fields') or []:
            if field.get('key') == 'title':
                return field.get('raw_value')
        return None

    def card_name(self, cid):
        doc = self.card(cid)
        for field in (doc.get('basic') or {}).get('fields') or []:
            if field.get('key') == 'name':
                return field.get('raw_value')
        return None

    def charainfo_record(self, cid):
        return self.charainfo.get(cid)

    def denju_first_sentence(self, cid):
        rows = self.denju.get(cid) or []
        if len(rows) != 1:
            return None, 'DENJU_NOT_UNIQUE'
        stext = str(rows[0].get('stext') or '')
        if not stext:
            return None, 'DENJU_STEXT_MISSING'
        return stext.split('。')[0] + '。', None

    def unique_pattern(self, pattern_id):
        hits = self.pattern_index.get(pattern_id) or []
        if len(hits) != 1:
            return None, len(hits)
        return self.pattern_docs[hits[0]], None

    def unique_skill(self, skill_id):
        hits = self.skill_index.get(skill_id) or []
        if len(hits) != 1:
            return None, len(hits)
        return self.skill_docs[hits[0]], None


class RawView:
    """从**只读原始解码文件**建立的记录视图，供真实 ``card_page_data.Inputs`` 消费。

    生产 ``card_page_data.Inputs`` 只暴露 ``root``／``decoded``／``rule_metadata`` 等属性，
    没有本批判定需要的 pattern／skill 索引与查询方法；本类**不修改** ``Inputs`` 类、不给
    实例打补丁、不 monkey patch，只用它的 ``root``／``decoded``／``rule_metadata`` 读同一
    份 CACHE 解码文件，并复用 ``decode_report.json`` 的 ``json_raw_sha256`` 做哈希门。

    本类只读；``apply_to_groups`` 仍把答案追加到调用方传入的**正式内存行**上，行身份、
    ``source`` 与 ``binding`` 由本视图的原始记录构造，不重载或替换页面行。
    """

    def __init__(self, root, decoded=None, rules=None):
        self.root = Path(root).resolve()
        if decoded is None:
            self.decoded = self.root / DECODED_REL
        else:
            dpath = Path(decoded)
            self.decoded = (dpath if dpath.is_absolute() else self.root / dpath).resolve()
        self.pages = self.root / PAGES_REL
        self.versions = {}
        self._cards = {}
        snapshot = self.decoded.parent
        report_path = snapshot / 'decode_report.json'
        report = json.loads(report_path.read_text(encoding='utf-8'))
        declared = {f.get('filename'): f.get('json_raw_sha256')
                    for f in report.get('files') or []}
        for stem in ('charainfo', 'bossinfo', 'denju'):
            self._load_verified(stem, declared)
        if isinstance(rules, dict) and rules:
            self.rules = rules
        else:
            self.rules = json.loads(
                (self.root / RULES_REL).read_text(encoding='utf-8'))

    def _load_verified(self, stem, declared):
        filename = stem + '.data5'
        path = self.decoded / (stem + '.data5.json.raw')
        actual = sha256_file(path)
        want = declared.get(filename)
        if want != actual:
            raise ValueError('输入哈希与声明不符: %s declared=%s actual=%s'
                             % (path, want, actual))
        doc = json.loads(path.read_text(encoding='utf-8-sig'))
        self.versions[stem] = {'path': path.relative_to(self.root).as_posix(),
                               'declared_sha256': want, 'actual_sha256': actual,
                               'match': True}
        if stem == 'charainfo':
            self.charainfo_rows = doc['charainfo']
            self.charainfo_index = {r['cid']: i for i, r in enumerate(self.charainfo_rows)}
            self.charainfo = {r['cid']: r for r in self.charainfo_rows}
        elif stem == 'bossinfo':
            boss = doc['bossinfo']
            self.pattern_docs = boss.get('bosspattern') or []
            self.skill_docs = boss.get('bossskill') or []
            self.pattern_index = {}
            for i, rec in enumerate(self.pattern_docs):
                self.pattern_index.setdefault(rec.get('patternid'), []).append(i)
            self.skill_index = {}
            for i, rec in enumerate(self.skill_docs):
                self.skill_index.setdefault(rec.get('skillid'), []).append(i)
            self.patterns = {pid: self.pattern_docs[idx[0]]
                             for pid, idx in self.pattern_index.items()}
            self.skills = {sid: self.skill_docs[idx[0]]
                           for sid, idx in self.skill_index.items()}
        elif stem == 'denju':
            self.denju = {}
            for rec in doc['denju']:
                self.denju.setdefault(rec.get('denju_id'), []).append(rec)

    def card(self, cid):
        if cid not in self._cards:
            path = self.pages / str(cid) / 'card.json'
            self._cards[cid] = {'path': path, 'sha256': sha256_file(path),
                                'doc': json.loads(path.read_text(encoding='utf-8'))}
        return self._cards[cid]['doc']

    def page_sha256(self, cid):
        self.card(cid)
        return self._cards[cid]['sha256']

    def card_title(self, cid):
        for field in (self.card(cid).get('basic') or {}).get('fields') or []:
            if field.get('key') == 'title':
                return field.get('raw_value')
        return None

    def card_name(self, cid):
        for field in (self.card(cid).get('basic') or {}).get('fields') or []:
            if field.get('key') == 'name':
                return field.get('raw_value')
        return None

    def charainfo_record(self, cid):
        return self.charainfo.get(cid)

    def denju_first_sentence(self, cid):
        rows = self.denju.get(cid) or []
        if len(rows) != 1:
            return None, 'DENJU_NOT_UNIQUE'
        stext = str(rows[0].get('stext') or '')
        if not stext:
            return None, 'DENJU_STEXT_MISSING'
        return stext.split('。')[0] + '。', None

    def unique_pattern(self, pattern_id):
        hits = self.pattern_index.get(pattern_id) or []
        if len(hits) != 1:
            return None, len(hits)
        return self.pattern_docs[hits[0]], None

    def unique_skill(self, skill_id):
        hits = self.skill_index.get(skill_id) or []
        if len(hits) != 1:
            return None, len(hits)
        return self.skill_docs[hits[0]], None


#: 本模块判定所需的只读视图接口（自带 Inputs 与 RawView 都实现）。
_VIEW_REQUIRED = ('rules', 'charainfo', 'charainfo_index', 'pattern_index',
                  'skill_index', 'pattern_docs', 'skill_docs', 'patterns', 'skills',
                  'charainfo_record', 'unique_pattern', 'unique_skill')


def view_for(data):
    """把真实 ``card_page_data.Inputs`` 或本模块 ``Inputs`` 归一为只读记录视图。

    * 已实现本批接口的对象（自带 ``Inputs``／``RawView``）原样返回；
    * 其他对象（例如真实 ``card_page_data.Inputs``）只取其 ``root``／``decoded``／
      ``rule_metadata``，新建 ``RawView``；**不修改**对象、类或全局状态。
    """
    if all(hasattr(data, name) for name in _VIEW_REQUIRED):
        return data
    root = getattr(data, 'root', None)
    if root is None:
        raise TypeError('apply_to_groups 需要带 root 的 Inputs 或只读记录视图')
    decoded = getattr(data, 'decoded', None)
    rules = getattr(data, 'rule_metadata', None)
    return RawView(root, decoded=decoded, rules=rules)


# ---------------------------------------------------------------- 单行判定

def evaluate(data, cid, row, *, skill=None, bossinfo=None, parent_record=None,
             siblings=None):
    """单行判定（不写入）。返回结构见模块头注 R1–R10。

    ``bossinfo``／``parent_record`` 注入**只用于自检反例**：即使所有门都过，注入路径也
    以 ``SYNTHETIC_INPUT_NOT_ADMISSIBLE`` 拒绝，绝不允许用注入结构制造准入。
    """
    data = view_for(data)
    out = {'cid': cid, 'row_id': (row or {}).get('row_id'), 'decision': 'REJECT',
           'rejection': None, 'reason': None, 'gates': {}, 'parent': None,
           'pattern': None, 'children': None, 'selected': None, 'frozen': None,
           'existing_answers': [], 'synthetic': bossinfo is not None or parent_record is not None}
    row_id = out['row_id']
    synthetic = out['synthetic']
    skill = skill or {}

    def reject(code, **detail):
        out['decision'] = 'REJECT'
        out['rejection'] = code
        out['reason'] = code
        if detail:
            out['gates'].setdefault('reject_detail', {}).update(detail)
        return out

    # R10 / 保护卡（先于任何主表访问）
    if cid in ZERO_TOUCH_CIDS:
        return reject('ZERO_TOUCH_CID')
    if cid in OUT_OF_SCOPE_CIDS or cid not in ADMITTED_CIDS:
        return reject('OUT_OF_SCOPE_CID')
    if not row_id:
        return reject('ROW_ID_MISSING')

    # R1 行身份（先判族，denju 行即使不在冻结表也必须报 DENJU_ROW_NOT_IN_SCOPE）
    group = row.get('group') or skill.get('original_group')
    out['gates']['R1_identity'] = {
        'group': group, 'reference_field': row.get('reference_field'),
        'table': skill.get('table'), 'record_id': skill.get('record_id'),
        'layer': skill.get('layer'), 'fragment_index': row.get('fragment_index'),
    }
    if group != 'special_move' or row.get('reference_field') != 'skilltext':
        if group == 'denju':
            return reject('DENJU_ROW_NOT_IN_SCOPE')
        return reject('ROW_NOT_CHARAINFO_SKILLTEXT')
    if skill.get('reference_field') != 'skilltext':
        return reject('ROW_NOT_CHARAINFO_SKILLTEXT')
    if skill.get('table') != 'charainfo':
        return reject('ROW_NOT_CHARAINFO_SKILLTEXT')
    if skill.get('record_id') != cid:
        return reject('PAGE_RECORD_ID_MISMATCH')
    if skill.get('layer') != 'CACHE':
        return reject('LAYER_NOT_CACHE')
    if row.get('cid') not in (None, cid):
        return reject('ROW_CID_MISMATCH')
    frozen = FROZEN_BY_ROW.get(row_id)
    if frozen is None:
        return reject('ROW_NOT_FROZEN')
    out['frozen'] = dict(frozen)
    if row.get('fragment_index') != frozen['fragment_index']:
        return reject('FRAGMENT_INDEX_MISMATCH')

    # R2 父记录与文本
    parent = parent_record if parent_record is not None else data.charainfo_record(cid)
    if parent is None:
        return reject('CHARAINFO_RECORD_MISSING')
    index = data.charainfo_index.get(cid)
    stext = parent.get('skilltext')
    out['gates']['R2_parent'] = {
        'charainfo_index': index,
        'pattern0': parent.get('pattern0'),
        'skilltext_sha_head': hashlib.sha256(str(stext or '').encode('utf-8')).hexdigest()[:16],
    }
    if not stext:
        return reject('PARENT_TEXT_MISSING')
    if canon(skill.get('original_text')) != canon(stext):
        return reject('PAGE_SKILL_ORIGINAL_TEXT_MISMATCH')
    if canon(row.get('context_text')) != canon(stext):
        return reject('CONTEXT_TEXT_MISMATCH')
    japanese = str(row.get('japanese') or '')
    if not canon(japanese):
        return reject('ROW_TEXT_EMPTY')
    if canon(japanese) not in canon(stext):
        return reject('FRAGMENT_NOT_IN_PARENT_TEXT')
    text_sha = hashlib.sha256(canon(japanese).encode('utf-8')).hexdigest()
    out['gates']['R2_text_sha256'] = text_sha
    if text_sha != FROZEN_TEXT_SHA256.get(row_id):
        return reject('ROW_TEXT_NOT_FROZEN')
    src = row.get('source') or {}
    want_record = '/charainfo/%s' % index
    want_field = want_record + '/skilltext'
    if index is None or src.get('json_pointer') != want_record:
        return reject('CHARAINFO_SOURCE_POINTER_MISMATCH',
                      want=want_record, got=src.get('json_pointer'))
    if src.get('field_json_pointer') not in (None, want_field):
        return reject('CHARAINFO_FIELD_POINTER_MISMATCH',
                      want=want_field, got=src.get('field_json_pointer'))

    # R3 链
    pattern_id = parent.get('pattern0')
    if not pattern_id:
        return reject('PATTERN0_MISSING')
    if pattern_id != frozen['pattern_id']:
        return reject('PATTERN_ID_MISMATCH')
    if bossinfo is None:
        pattern, dup = data.unique_pattern(pattern_id)
        if pattern is None:
            return reject('BOSSPATTERN_NOT_FOUND' if dup == 0 else 'BOSSPATTERN_NOT_UNIQUE',
                          hits=dup)
        pattern_index = data.pattern_index[pattern_id][0]
    else:
        hits = (bossinfo.get('patterns') or {}).get(pattern_id) or []
        if len(hits) != 1:
            return reject('BOSSPATTERN_NOT_FOUND' if not hits else 'BOSSPATTERN_NOT_UNIQUE',
                          hits=len(hits))
        pattern = hits[0]
        pattern_index = (bossinfo.get('pattern_indices') or {}).get(pattern_id)
    sinfo = pattern.get('sinfo')
    out['gates']['R3_pattern'] = {
        'pattern_id': pattern_id,
        'sinfo_present': bool(sinfo),
        'sinfo_equals_parent_text': canon(sinfo) == canon(stext),
    }
    if not sinfo:
        return reject('PATTERN_SINFO_MISSING')
    if canon(sinfo) != canon(stext):
        return reject('PARENT_TEXT_NOT_PATTERN_SINFO')
    out['parent'] = {'table': 'charainfo', 'pointer': 'charainfo.pattern0',
                     'record_key': (src or {}).get('record_key'),
                     'json_pointer': src.get('json_pointer'),
                     'field_json_pointer': src.get('field_json_pointer'),
                     'pattern_id': pattern_id, 'pattern_index': pattern_index,
                     'index': index, 'record': parent}
    out['pattern'] = dict(pattern)

    children = []
    for slot in range(7):
        sid = pattern.get('skillid%d' % slot)
        if not sid:
            continue
        if bossinfo is None:
            rec, dup = data.unique_skill(sid)
            if rec is None:
                return reject('CHILD_RECORD_MISSING' if dup == 0 else 'CHILD_RECORD_NOT_UNIQUE',
                              skillid=sid, hits=dup)
            ridx = data.skill_index[sid][0]
        else:
            hits = (bossinfo.get('skills') or {}).get(sid) or []
            if len(hits) != 1:
                return reject('CHILD_RECORD_MISSING' if not hits else 'CHILD_RECORD_NOT_UNIQUE',
                              skillid=sid, hits=len(hits))
            rec = hits[0]
            ridx = (bossinfo.get('skill_indices') or {}).get(sid)
        children.append({'slot': slot, 'skillid': sid, 'index': ridx,
                         'type': rec.get('skillid0'),
                         'params': {k: v for k, v in rec.items()
                                    if k.startswith('skillparam')},
                         'record': rec})
    if [c['slot'] for c in children] != list(range(len(children))):
        return reject('SLOT_NOT_CONTIGUOUS', slots=[c['slot'] for c in children])
    out['children'] = [{'slot': c['slot'], 'skillid': c['skillid'], 'type': c['type']}
                       for c in children]

    # R4 句面
    form, detail = classify_clause(japanese)
    out['gates']['R4_clause'] = {'form': form, **detail}
    if form is None:
        return reject(detail.get('reason') or 'NO_DAMAGE_CLAUSE')
    if form == 'PLAIN':
        return reject('DAMAGE_WITHOUT_QUALIFIER')
    if form != frozen['mode']:
        return reject('MODE_MISMATCH', want=frozen['mode'], got=form)
    if form == 'MULTIHIT' and detail.get('n') != frozen['n']:
        return reject('N_MISMATCH', want=frozen['n'], got=detail.get('n'))

    # R5 形态选型唯一
    if form == 'MULTIHIT':
        n = detail['n']
        typed = [c for c in children if c.get('type') in MULTI_TYPES]
        hits = [c for c in typed if c['params'].get('skillparam6') == n]
        if not hits:
            return reject('NO_MULTIHIT_PARAM6_MATCH', n=n,
                          typed=[c['skillid'] for c in typed])
        if len(hits) > 1:
            return reject('MULTI_MULTIHIT_NOT_UNIQUE', n=n,
                          records=sorted(c['skillid'] for c in hits))
        chosen = hits[0]
        selection = {'mode': 'MULTIHIT', 'n': n, 'param6': n,
                     'typed': [c['skillid'] for c in typed],
                     'records': [chosen['skillid']], 'record_note': 'RECORD_UNIQUE',
                     'basis': '句面 N回ダメージ ↔ 多段型 type105/110 且 skillparam6==N'}
    else:
        typed = [c for c in children if c.get('type') in SINGLE_TYPES]
        if not typed:
            return reject('NO_SINGLE_TYPE_CARRIER')
        if len(typed) > 1:
            return reject('MULTI_SINGLE_TYPE_AMBIGUOUS',
                          records=sorted(c['skillid'] for c in typed))
        chosen = typed[0]
        selection = {'mode': form, 'typed': [chosen['skillid']],
                     'records': [chosen['skillid']], 'record_note': 'RECORD_UNIQUE',
                     'basis': '句面 大/中/一定間隔ダメージ ↔ 单发型 type3/22/55/74 恰 1 条'}
    out['gates']['R5_select'] = selection
    if chosen['slot'] != frozen['child_slot']:
        return reject('CHILD_SLOT_MISMATCH', want=frozen['child_slot'], got=chosen['slot'])
    if chosen['skillid'] != frozen['record_id']:
        return reject('RECORD_ID_MISMATCH', want=frozen['record_id'], got=chosen['skillid'])
    if chosen['type'] != frozen['type']:
        return reject('TYPE_MISMATCH', want=frozen['type'], got=chosen['type'])

    # R6 槽位唯一
    slot, slot_keys = unique_damage_slot(data.rules, chosen['type'])
    out['gates']['R6_slot_rule'] = {'type': chosen['type'], 'keys': slot_keys, 'slot': slot}
    if slot is None:
        return reject('SLOT_NOT_UNIQUE_FOR_TYPE' if slot_keys else 'TYPE_WITHOUT_DAMAGE_RULE',
                      keys=slot_keys)
    if slot != DAMAGE_SLOT.get(chosen['type']) or slot != frozen['slot']:
        return reject('SLOT_RULE_MISMATCH', want=frozen['slot'], got=slot)
    rule_key = 'bossskill|%d|/%s' % (chosen['type'], slot)
    if rule_key != frozen['rule_key'] or rule_key not in LEDGER_MAPPED_RULE_KEYS:
        return reject('RULE_KEY_MISMATCH', want=frozen['rule_key'], got=rule_key)

    # R7 原值分档
    present = slot in chosen['params']
    raw = chosen['params'].get(slot) if present else None
    state = raw_state(raw, present)
    out['gates']['R7_raw'] = {'type': chosen['type'], 'slot': slot, 'raw': raw,
                              'present': present, 'raw_state': state}
    if state == 'MISSING':
        return reject('RAW_VALUE_MISSING')
    if state == 'NULL':
        return reject('RAW_VALUE_NULL')
    if state == 'NON_FINITE':
        return reject('RAW_VALUE_NON_FINITE')
    if state == 'NEGATIVE':
        return reject('RAW_VALUE_NEGATIVE')
    if state == 'ZERO':
        return reject('RAW_VALUE_ZERO')
    if float(raw) <= 0:
        return reject('RAW_VALUE_NON_POSITIVE')
    if float(raw) != float(frozen['raw']):
        return reject('FROZEN_EXPECTATION_MISMATCH', field='raw',
                      want=frozen['raw'], got=raw)

    # R8 来源（真实链重新读解码 JSON；注入结构不进入该分支）
    if bossinfo is None:
        idx = chosen['index']
        doc_rec = data.skill_docs[idx]
        if doc_rec is not chosen['record'] or doc_rec.get('skillid') != chosen['skillid']:
            return reject('SOURCE_RECORD_MISMATCH')
        if doc_rec.get(slot) != raw:
            return reject('SOURCE_FIELD_VALUE_MISMATCH')
        if pattern.get('skillid%d' % chosen['slot']) != chosen['skillid']:
            return reject('SOURCE_PATTERN_LINK_MISMATCH')
        if pattern_index is None or data.pattern_docs[pattern_index] is not pattern:
            return reject('SOURCE_PATTERN_INDEX_MISMATCH')
    else:
        idx = chosen['index']

    # R5b 同父文本片段 → 子记录不重复（注入性）
    if siblings:
        for other in siblings:
            if other is row or other.get('row_id') == row_id:
                continue
            if other.get('reference_field') != 'skilltext':
                continue
            oform, odetail = classify_clause(other.get('japanese'))
            if oform is None or oform == 'PLAIN':
                continue
            osel = _select_from_children(children, oform, odetail)
            if osel is not None and osel['skillid'] == chosen['skillid']:
                return reject('DUPLICATE_FRAGMENT_RECORD',
                              other_row_id=other.get('row_id'),
                              record_id=chosen['skillid'])

    # R9 既有答案（同 rule_key 不新增、不改写）
    same_key = [a for a in row.get('answers') or []
                if a.get('rule_key') == rule_key]
    out['existing_answers'] = [{'rule_key': a.get('rule_key'),
                                'record_id': a.get('record_id'),
                                'raw_value': a.get('raw_value')} for a in same_key]
    same_record_value = [a for a in same_key
                         if a.get('record_id') == chosen['skillid']
                         and a.get('raw_value') == raw]
    if same_record_value:
        out['selected'] = _selected(chosen, slot, raw, state, rule_key)
        out['decision'] = 'SKIP_ALREADY_PRESENT'
        out['rejection'] = None
        out['reason'] = 'ALREADY_ANSWERED_SAME'
        return out
    if same_key:
        out['selected'] = _selected(chosen, slot, raw, state, rule_key)
        same_value = any(a.get('raw_value') == raw for a in same_key)
        out['decision'] = 'REJECT'
        out['rejection'] = ('EXISTING_ANSWER_SAME_VALUE_DIFF_RECORD' if same_value
                            else 'EXISTING_ANSWER_CONFLICT')
        out['reason'] = out['rejection']
        return out

    # R10 注入结构不得制造准入
    if synthetic:
        return reject('SYNTHETIC_INPUT_NOT_ADMISSIBLE')

    out['selected'] = _selected(chosen, slot, raw, state, rule_key)
    out['decision'] = 'ACCEPT'
    out['reason'] = 'ADMITTED'
    return out


def _selected(chosen, slot, raw, state, rule_key):
    return {'skillid': chosen['skillid'], 'type': chosen['type'], 'slot': '/' + slot,
            'field': slot, 'raw': raw, 'raw_state': state, 'rule_key': rule_key,
            'record_index': chosen['index'], 'child_slot': chosen['slot']}


def _select_from_children(children, form, detail):
    """复用 R5 的选型纯函数（仅用于注入性检查）。"""
    if form == 'MULTIHIT':
        n = detail.get('n')
        hits = [c for c in children if c.get('type') in MULTI_TYPES
                and c['params'].get('skillparam6') == n]
        return hits[0] if len(hits) == 1 else None
    typed = [c for c in children if c.get('type') in SINGLE_TYPES]
    return typed[0] if len(typed) == 1 else None


# ---------------------------------------------------------------- 档位与同号披露

def other_tiers(data, cid, selected, pattern_id):
    """同卡 pattern1..4 的伤害载体逐条登记（排除值／同记录披露，不并入）。"""
    parent = data.charainfo_record(cid) or {}
    out = []
    for i in range(1, 5):
        pid = parent.get('pattern%d' % i)
        if not pid or pid == pattern_id:
            continue
        pattern, dup = data.unique_pattern(pid)
        if pattern is None:
            out.append({'pointer': 'charainfo.pattern%d' % i, 'pattern_id': pid,
                        'missing': True, 'hits': dup})
            continue
        sinfo = pattern.get('sinfo')
        prefix = None
        if sinfo:
            m = re.match(r'^【([^】]*)】', sinfo)
            prefix = m.group(1) if m else None
        for slot in range(7):
            sid = pattern.get('skillid%d' % slot)
            if not sid:
                continue
            rec, dup = data.unique_skill(sid)
            if rec is None:
                out.append({'pointer': 'charainfo.pattern%d' % i, 'pattern_id': pid,
                            'child_slot': slot, 'record_id': sid, 'missing': True})
                continue
            etype = rec.get('skillid0')
            dslot = DAMAGE_SLOT.get(etype)
            if dslot is None:
                continue
            present = dslot in rec
            raw = rec.get(dslot) if present else None
            same_type = etype == selected['type']
            if etype == selected['type'] and sid == selected['skillid'] and raw == selected['raw']:
                relation = 'SAME_RECORD_SAME_VALUE'
            elif etype == selected['type'] and raw == selected['raw']:
                relation = 'DIFFERENT_RECORD_SAME_VALUE'
            elif etype == selected['type']:
                relation = 'DIFFERENT_VALUE'
            else:
                relation = 'OTHER_DAMAGE_TYPE'
            out.append({
                'pointer': 'charainfo.pattern%d' % i, 'pattern_id': pid,
                'sinfo_present': bool(sinfo), 'sinfo_prefix': prefix,
                'child_slot': slot, 'record_id': sid, 'type': etype,
                'field': '/' + dslot, 'raw': raw,
                'raw_state': raw_state(raw, present),
                'same_type': same_type, 'relation': relation,
                'note': ('同卡其他档位值：只登记排除，不并入本行、不反推'
                         if same_type else '同卡其他档位的其他伤害类型载体：只披露'),
            })
    return out


def carriers_in_pattern(data, pattern, selected_skillid):
    """选中 pattern 内其余伤害载体（披露，不是排除值）。"""
    out = []
    for slot in range(7):
        sid = pattern.get('skillid%d' % slot)
        if not sid or sid == selected_skillid:
            continue
        rec, _dup = data.unique_skill(sid)
        if rec is None:
            continue
        etype = rec.get('skillid0')
        dslot = DAMAGE_SLOT.get(etype)
        if dslot is None:
            continue
        out.append({'child_slot': slot, 'record_id': sid, 'type': etype,
                    'field': '/' + dslot, 'raw': rec.get(dslot),
                    'note': '同 pattern 另一伤害载体（属于同句其他片段），本行不取'})
    return out


def charainfo_slot0_equivalence(parent, pattern, data):
    """charainfo 记录 skillparam* 只对应 pattern 首槽记录；逐槽披露（不用于伤害来源）。"""
    first_sid = pattern.get('skillid0')
    rec, _dup = data.unique_skill(first_sid) if first_sid else (None, 0)
    if rec is None:
        return {'first_child': first_sid, 'available': False}
    diffs = []
    compared = []
    for i in range(10):
        key = 'skillparam%d' % i
        a_present, b_present = key in parent, key in rec
        a, b = parent.get(key), rec.get(key)
        if a_present or b_present:
            compared.append(key)
        if (a_present, a) != (b_present, b):
            diffs.append({'slot': key, 'charainfo': a, 'slot0_record': b})
    return {'first_child': first_sid, 'available': True, 'compared': compared,
            'differing': diffs, 'equal': not diffs,
            'note': ('charainfo 记录参数只镜像 pattern 首槽记录；伤害子记录不是 charainfo 的'
                     '副本，故不以记录级等价作伤害来源')}


def id_collision(data, record_id, pattern_id):
    """同号跨表披露：skillid 与 patternid 数值空间独立，但同号可能同时存在。"""
    return {
        'record_id_is_also_pattern_id': record_id in data.pattern_index,
        'pattern_id_is_also_skill_id': pattern_id in data.skill_index,
        'record_id': record_id,
        'pattern_id': pattern_id,
        'note': ('bossskill.skillid 与 bosspattern.patternid 是两套独立命名空间；'
                 '本模块按 pattern.skillidN 取子记录，再按 skillid 在 bossskill 唯一命中，'
                 '不做同号互推'),
    }


# ---------------------------------------------------------------- 答案

QUANTITY_UNIT = '倍率（相对B）'


def build_answer(data, cid, row, res, tiers, carriers, slot0, collision, page_sha):
    selected = res['selected']
    pattern = res['pattern']
    parent = res['parent']
    frozen = res['frozen']
    raw = selected['raw']
    rule_key = selected['rule_key']
    rule = data.rules.get(rule_key) or {}
    etype = selected['type']
    slot = selected['field']
    rid = selected['skillid']
    idx = selected['record_index']
    meaning = rule.get('meaning_zh') or '伤害输入倍率'
    num = num_text(raw)
    src_key = 'CACHE/bossinfo.data5.json.raw'
    record_key = '%s#/bossinfo/bossskill/%d' % (src_key, idx)
    excluded = [t for t in tiers if t.get('same_type') and t.get('relation') == 'DIFFERENT_VALUE']
    same_record = [t for t in tiers if t.get('same_type')
                   and t.get('relation') == 'SAME_RECORD_SAME_VALUE']
    other_types = [t for t in tiers if t.get('relation') == 'OTHER_DAMAGE_TYPE']
    if excluded:
        exc_text = '、'.join('%s（%s）' % (num_text(t['raw']), t['record_id']) for t in excluded)
        exc_tail = '同卡其他档位伤害输入 %s 已登记排除、未并入本行' % exc_text
    else:
        exc_tail = '本档无链外同类型档位值'
    same_rec_tail = ''
    if same_record:
        same_rec_tail = '；%s 亦被同卡其他 pattern 以同记录同值引用（只披露）' % '、'.join(
            sorted({t['pointer'] for t in same_record}))
    form = frozen['mode']
    if form == 'MULTIHIT':
        form_text = '句面「%d回ダメージ」↔ 该记录 skillparam6=%d' % (frozen['n'], frozen['n'])
    else:
        form_text = '句面「%s」↔ 单发型 type%d' % (MODE_LABEL[form], etype)
    value = ('该段对敌伤害输入 = floor/clamp(float32(B × %s))；原值 %s（%s，相对B）；'
             '对象：敌方；来源：CACHE bossskill %s（type%d %s）；链：charainfo.pattern0 %s '
             '第%d槽 → bossskill %s。%s。%s%s。仅局部伤害输入公式，未验证最终扣血、'
             '保证命中与运行时选档。'
             % (num, num, meaning, rid, etype, '/' + slot, parent['pattern_id'],
                selected['child_slot'], rid, form_text, exc_tail, same_rec_tail))
    player = ('这一句对敌方造成伤害：伤害输入按技能基础攻击的 %s 倍计算（原值 %s，相对B%s）。'
              '这是局部公式，实际扣血和命中尚未验证。%s。'
              % (num, num,
                 '，共 %d 回' % frozen['n'] if form == 'MULTIHIT' else '',
                 ('同卡其他档位另有 %s 的伤害输入，已单独登记、未并入本句'
                  % '、'.join(num_text(t['raw']) for t in excluded)) if excluded
                 else '同卡其他档位未登记同类型伤害输入'))
    conditions_raw = {k: pattern.get(k) for k in
                      ('flag', 'hpend', 'priority', 'scost', 'sname',
                       'skillid0', 'skillid1', 'skillid2', 'skillid3', 'sinfo')
                      if pattern.get(k) is not None}
    marker = {
        'scope': LEDGER_SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'module': MODULE_VERSION,
        'gate': 'charainfo.pattern0',
        'row_id': res['row_id'],
        'cid': cid,
        'rule_key': rule_key,
        'table': 'bossskill',
        'record_id': rid,
        'record_index': idx,
        'layer': 'CACHE',
        'field_path': '/' + slot,
        'raw_value': raw,
        'raw_state': selected['raw_state'],
        'pattern_id': parent['pattern_id'],
        'pattern_slot': 'charainfo.pattern0',
        'child_slot': selected['child_slot'],
        'charainfo': {'table': 'charainfo', 'record_id': cid,
                      'index': parent['index'],
                      'json_pointer': parent['json_pointer'],
                      'field_json_pointer': parent['field_json_pointer']},
        'source': {'source_key': src_key,
                   'original_file': DECODED_REL + '/bossinfo.data5.json.raw',
                   'json_pointer': '/bossinfo/bossskill/%d' % idx,
                   'field_json_pointer': '/bossinfo/bossskill/%d/%s' % (idx, slot),
                   'record_key': record_key},
        'frozen_identity': dict(frozen),
        'selection': res['gates'].get('R5_select'),
        'charainfo_slot0_equivalence': slot0,
        'other_tiers': tiers,
        'same_pattern_other_carriers': carriers,
        'id_collision': collision,
        'page_sha256': page_sha,
        'association': '推断',
        'value_basis': '原值直接取自选中 bossskill 记录字段；句面→该记录的归属为类型语义＋一致性推断',
        'native_evidence': 'none（本批不新增原生点；类型语义＋param6 一致性推断）',
        'conditions_raw': conditions_raw,
    }
    answer = {
        'value': value,
        'player_text': player,
        'quantity_kind': meaning,
        'unit': QUANTITY_UNIT,
        'unit_raw': rule.get('unit'),
        'raw_value': raw,
        'effective_float32': f32(raw),
        'quantitative': True,
        'numeric_source': '原生静态局部规则＋CACHE bossskill 原始记录',
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'answer_status': 'CONFIRMED_FORMULA_ONLY',
        'evidence_scope': 'BY_TYPE_EXTRAPOLATED',
        'rule_key': rule_key,
        'field_path': '/' + slot,
        'table': 'bossskill',
        'record_id': rid,
        'layer': 'CACHE',
        'source': {
            'table': 'bossskill', 'record_id': rid, 'layer': 'CACHE',
            'field_path': '/' + slot, 'field': '/' + slot,
            'source_key': src_key,
            'original_file': DECODED_REL + '/bossinfo.data5.json.raw',
            'json_pointer': '/bossinfo/bossskill/%d' % idx,
            'field_json_pointer': '/bossinfo/bossskill/%d/%s' % (idx, slot),
            'record_key': record_key,
            'record_index': idx,
            'source_resolution': EXACT,
            'note': ('按解码 JSON 的 bossskill.skillid 唯一命中；本行经 charainfo.pattern0 → '
                     'bosspattern %s 第%d槽直接定源，不是同文复制、不取 charainfo 参数'
                     % (parent['pattern_id'], selected['child_slot'])),
        },
        'context': '直接链（charainfo.skilltext 行）',
        'condition_label': 'charainfo.pattern0 → bosspattern %s 被选中时' % parent['pattern_id'],
        'target': '敌',
        'binding': {
            'g1_b1_binding': marker,
            'c14_p2_boss_damage_direct_binding': {
                'scope': STRUCTURE_SCOPE,
                'module': MODULE_VERSION,
                'verdict': 'DIRECT_CHAIN_VALUE_AND_SOURCE',
                'dedup': 'NEW_ANSWER_NO_EXISTING_RULE_KEY',
            },
            'fields': [{'f': '/' + slot, 'raw': raw}],
        },
        'note': ('仅局部伤害输入公式（B=getBasicSkillAttack(true) 等沿用 rules.json 原定义），'
                 '未验证最终扣血、保证命中与运行时选档；原值直接取自选中 bossskill 字段，'
                 '不是最终伤害。同卡其他档位只登记排除；APK 同号记录未读取。'
                 '结构判定见 card_page_inference_c14_p2_boss_damage_direct.py 模块头注 R1–R10。'),
        'evidence': ['docs/tasks/20261102-c14-p2-boss-damage-direct.md',
                     'docs/tasks/20261102-c14-cycle.md',
                     'docs/角色技能完整解读实施方案.md',
                     OUT_DIR_REL + '/README.md'],
    }
    return answer


# ---------------------------------------------------------------- 候选构建

def _iter_rows(card):
    for group in card.get('groups') or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                yield group.get('group'), skill, row


def _denju_exclusion(data, cid, row):
    """denju 行：只判定排除原因，不评估链、不出答案。"""
    row_id = row.get('row_id')
    if cid in ZERO_TOUCH_CIDS:
        return ('ZERO_TOUCH_CID', '保护卡（含其 denju 行）零触碰', {})
    if cid in OUT_OF_SCOPE_CIDS or cid not in ADMITTED_CIDS:
        return ('OUT_OF_SCOPE_CID', '不在本批 9 卡准入范围（含其 denju 行）', {})
    if row_id in _DENJU_ROW_SET:
        first, err = data.denju_first_sentence(cid)
        detail = {'first_sentence': first, 'error': err,
                  'is_first_sentence': False if err is None else None}
        if err is None:
            detail['is_first_sentence'] = canon(first) == canon(row.get('japanese'))
        return ('DENJU_NON_FIRST_SEGMENT_EXCLUDED',
                '任务卡点名的 denju 非首段行：本批保持未知，不评估 denju 链、不复制 '
                'charainfo 新答案', detail)
    return ('DENJU_ROW_NOT_IN_SCOPE',
            'denju 行不属于本批 charainfo.pattern0 直接链；不处理', {})


def build_candidates(root):
    """构建候选与排除清单（纯内存、确定性；不写盘）。"""
    data = Inputs(root)
    accepted, exclusions = [], []
    row_count = 0
    skilltext_count = 0
    denju_count = 0
    for cid in INVENTORY_CIDS:
        card = data.card(cid)
        title = data.card_title(cid)
        is_yg = bool(WANTED_TITLE_RX.search(str(title or '')))
        for group, skill, row in _iter_rows(card):
            if group not in ('special_move', 'denju'):
                continue
            if group == 'denju':
                row_count += 1
                denju_count += 1
                code, reason, detail = _denju_exclusion(data, cid, row)
                exclusions.append({'category': 'DENJU', 'cid': cid, 'row_id': row.get('row_id'),
                                   'group': group, 'reference_field': row.get('reference_field'),
                                   'japanese': row.get('japanese'), 'reason_code': code,
                                   'reason': reason, 'detail': detail})
                continue
            if skill.get('reference_field') != 'skilltext':
                continue
            row_count += 1
            skilltext_count += 1
            siblings = [r for g2, s2, r in _iter_rows(card)
                        if g2 == 'special_move' and s2.get('reference_field') == 'skilltext']
            res = evaluate(data, cid, row, skill=skill, siblings=siblings)
            base = {'cid': cid, 'row_id': row.get('row_id'),
                    'fragment_index': row.get('fragment_index'),
                    'japanese': row.get('japanese'),
                    'context_text': row.get('context_text'),
                    'page_source': row.get('source'),
                    'group': group, 'reference_field': row.get('reference_field'),
                    'layer': skill.get('layer'), 'table': skill.get('table'),
                    'record_id': skill.get('record_id'), 'yg': is_yg}
            if res['decision'] == 'ACCEPT':
                selected = res['selected']
                tiers = other_tiers(data, cid, selected, res['parent']['pattern_id'])
                carriers = carriers_in_pattern(data, res['pattern'], selected['skillid'])
                slot0 = charainfo_slot0_equivalence(res['parent']['record'],
                                                    res['pattern'], data)
                collision = id_collision(data, selected['skillid'],
                                         res['parent']['pattern_id'])
                answer = build_answer(data, cid, row, res, tiers, carriers, slot0,
                                      collision, data.page_sha256(cid))
                accepted.append({
                    **base,
                    'cid_name': data.card_name(cid),
                    'cid_title': title,
                    'parent': {'table': 'charainfo', 'record_id': cid,
                               'index': res['parent']['index'],
                               'json_pointer': res['parent']['json_pointer'],
                               'field_json_pointer': res['parent']['field_json_pointer'],
                               'pattern0': res['parent']['pattern_id']},
                    'pattern': {'pattern_id': res['parent']['pattern_id'],
                                'pattern_index': res['parent']['pattern_index'],
                                'sinfo': res['pattern'].get('sinfo'),
                                'sname': res['pattern'].get('sname'),
                                'skillids': [{'slot': c['slot'], 'skillid': c['skillid'],
                                              'type': c['type']} for c in res['children']]},
                    'chain': ['charainfo.pattern0=%s' % res['parent']['pattern_id'],
                              'bosspattern.skillid%d=%s' % (selected['child_slot'],
                                                            selected['skillid']),
                              'bossskill.skillid=%s' % selected['skillid']],
                    'selected': selected,
                    'verdict': res['decision'],
                    'gates': res['gates'],
                    'other_tiers': tiers,
                    'same_pattern_other_carriers': carriers,
                    'charainfo_slot0_equivalence': slot0,
                    'id_collision': collision,
                    'answer': answer,
                    'evidence_grade': {'numeric': '确认', 'association': '推断',
                                       'scope': 'BY_TYPE_EXTRAPOLATED',
                                       'native': 'none'},
                })
                continue
            reason = res['reason'] or res['rejection'] or 'REJECTED'
            if res['decision'] == 'SKIP_ALREADY_PRESENT':
                code = 'ALREADY_ANSWERED_SAME'
            elif reason.startswith('EXISTING_ANSWER'):
                code = reason
            elif res['rejection']:
                code = res['rejection']
            else:
                code = 'REJECTED'
            completeness = {}
            if code == 'ROW_NOT_FROZEN':
                # 完整性审计：9 卡内非冻结 skilltext 行若仍是伤害实例，必须显式暴露，
                # 不能靠“不在冻结表”静默略过。
                form, detail = classify_clause(row.get('japanese'))
                completeness = {'form': form, **detail}
                if form in ('MULTIHIT', 'BIGMID', 'INTERVAL'):
                    code = 'DAMAGE_INSTANCE_OUTSIDE_FROZEN_SET'
                elif form == 'PLAIN':
                    code = 'DAMAGE_WITHOUT_QUALIFIER'
                elif form is None:
                    code = detail.get('reason') or 'NO_DAMAGE_CLAUSE'
            exclusions.append({**base, 'category': 'SKILLTEXT', 'reason_code': code,
                               'reason': _reason_text(code),
                               'detail': {'gates': res.get('gates'),
                                          'completeness': completeness,
                                          'frozen': res.get('frozen'),
                                          'existing_answers': res.get('existing_answers')}})
    # 同卡其他档位值：逐条平铺进排除清单（与候选行 other_tiers 同源，不并入、不反推）
    tier_items = 0
    for r in accepted:
        for t in r['other_tiers']:
            relation = t.get('relation')
            if t.get('missing'):
                code = 'ALTERNATE_TIER_RECORD_MISSING'
            elif relation == 'DIFFERENT_VALUE':
                code = 'ALTERNATE_TIER_VALUE_EXCLUDED'
            elif relation == 'SAME_RECORD_SAME_VALUE':
                code = 'ALTERNATE_TIER_SAME_RECORD_DISCLOSED'
            elif relation == 'DIFFERENT_RECORD_SAME_VALUE':
                code = 'ALTERNATE_TIER_SAME_VALUE_DIFF_RECORD'
            else:
                code = 'ALTERNATE_TIER_OTHER_DAMAGE_TYPE'
            exclusions.append({
                'category': 'OTHER_TIER_VALUE',
                'cid': r['cid'], 'row_id': r['row_id'],
                'pointer': t.get('pointer'), 'pattern_id': t.get('pattern_id'),
                'sinfo_present': t.get('sinfo_present'),
                'sinfo_prefix': t.get('sinfo_prefix'),
                'child_slot': t.get('child_slot'), 'record_id': t.get('record_id'),
                'type': t.get('type'), 'field': t.get('field'), 'raw': t.get('raw'),
                'relation': relation, 'reason_code': code,
                'reason': _reason_text(code),
            })
            tier_items += 1

    # 边界卡整页登记（含非 special_move 组不逐行展开；只列 skilltext/denju 行）
    cand = {
        'schema': 'c14-p2-boss-damage-direct-candidate-1',
        'module': MODULE_VERSION,
        'module_sha256': sha256_file(Path(__file__).resolve()),
        'candidate_only': True,
        'ledger_scope': LEDGER_SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'scope': {
            'admitted_cids': list(ADMITTED_CIDS),
            'inventory_cids': list(INVENTORY_CIDS),
            'zero_touch_cids': sorted(ZERO_TOUCH_CIDS),
            'out_of_scope_cids': sorted(OUT_OF_SCOPE_CIDS),
            'denju_non_first_rows': list(DENJU_NON_FIRST_ROWS),
            'rule_keys': sorted(LEDGER_MAPPED_RULE_KEYS),
            'allowed_types_multi': list(MULTI_TYPES),
            'allowed_types_single': list(SINGLE_TYPES),
        },
        'frozen': [dict(item, japanese_sha256=FROZEN_TEXT_SHA256[item['row_id']])
                   for item in FROZEN],
        'inputs': {
            'snapshot': SNAPSHOT_REL,
            'decode_report': DECODE_REPORT_REL,
            'decoded': {k: v for k, v in data.versions.items()},
            'rules': {'path': RULES_REL,
                      'sha256': sha256_file(data.rules_path),
                      'key_count': len(data.rules)},
            'pages': {str(cid): {'path': PAGES_REL + '/%d/card.json' % cid,
                                 'sha256': data.page_sha256(cid)}
                      for cid in INVENTORY_CIDS},
        },
        'rows': accepted,
        'answers': [r['answer'] for r in accepted],
        'counts': {
            'rows_in_inventory': row_count,
            'skilltext_rows': skilltext_count,
            'denju_rows': denju_count,
            'rows_evaluated': skilltext_count,
            'candidates': len(accepted),
            'answers': sum(len([r['answer']]) for r in accepted),
            'cids': len({r['cid'] for r in accepted}),
            'exclusions': len(exclusions),
            'row_exclusions': sum(1 for e in exclusions
                                  if e.get('category') in ('SKILLTEXT', 'DENJU')),
            'alternate_tier_items': tier_items,
            'damage_instances_outside_frozen_set': sum(
                1 for e in exclusions
                if e.get('reason_code') == 'DAMAGE_INSTANCE_OUTSIDE_FROZEN_SET'),
        },
        'limits': [
            '候选实现：未接入 card_page_data.py／effect_ledger.py；未改正式 pages／账本／rules。',
            '未运行正式全库生成；候选独立审查通过前不得合并冻结。',
            'association_evidence 全为推断：句面→bossskill 记录的归属是类型语义＋param6 一致性推断；'
            '直接链不等于引擎运行时已验证，未实机。',
            '不写最终扣血、保证命中次数、面板 ATK→_skillAtk 换算与 Chain 运行时因子。',
            '同卡其他档位值只登记排除；APK 同号记录不读取、不合并。',
            'denju 非首段 6 行保持未知；30102／20234／30236／30239 不处理。',
        ],
    }
    exc = {
        'schema': 'c14-p2-boss-damage-direct-exclusions-1',
        'module': MODULE_VERSION,
        'candidate_only': True,
        'policy': ('逐一登记本批候选宇宙内所有被排除的行／档位；排除不等于“无效果”，'
                   '只表示本批不产出答案。denju 非首段保持未知。'),
        'items': exclusions,
        'counts': {
            'items': len(exclusions),
            'by_reason': _reason_counts(exclusions),
            'by_category': _category_counts(exclusions),
            'denju_non_first': sum(1 for e in exclusions
                                   if e.get('reason_code') == 'DENJU_NON_FIRST_SEGMENT_EXCLUDED'),
            'alternate_tier_items': tier_items,
            'row_exclusions': sum(1 for e in exclusions
                                  if e.get('category') in ('SKILLTEXT', 'DENJU')),
        },
    }
    return cand, exc


def _reason_text(code):
    return {
        'DAMAGE_WITHOUT_QUALIFIER': '有「ダメージ」但不是 N回／大／中／一定間隔形态，本批不取',
        'NO_DAMAGE_WORD': '句面无「ダメージ」，不是伤害段',
        'NO_ENEMY_TARGET': '句面无「敵」，不是对敌伤害实例',
        'DAMAGE_RECEIVER_NOT_ENEMY': '句面为受击／味方对象，不是对敌伤害实例',
        'DAMAGE_MODIFIER_NOT_INSTANCE': '句面为伤害增减修饰，不是伤害实例',
        'ALREADY_ANSWERED_SAME': '本行已有同 rule_key 同记录同值答案，幂等跳过',
        'EXISTING_ANSWER_CONFLICT': '本行已有同 rule_key 异值答案，冲突不覆盖',
        'EXISTING_ANSWER_SAME_VALUE_DIFF_RECORD': '本行已有同值异记录答案，不重复新增',
        'ZERO_TOUCH_CID': '保护卡，零触碰',
        'OUT_OF_SCOPE_CID': '不在本批 9 卡准入范围（30102／20234 等显式不处理）',
        'ROW_NOT_FROZEN': '不在冻结准入表（非预筛行）',
        'DENJU_ROW_NOT_IN_SCOPE': 'denju 行不属于 charainfo.pattern0 直接链',
        'DENJU_NON_FIRST_SEGMENT_EXCLUDED':
            '任务卡点名的 denju 非首段行：保持未知，不评估 denju 链、不复制 charainfo 答案',
        'DAMAGE_INSTANCE_OUTSIDE_FROZEN_SET':
            '9 卡 skilltext 内仍是伤害实例但不在冻结表：必须复核，不得静默略过',
        'ZERO_TOUCH_OR_OUT_OF_SCOPE_CID': '保护卡或范围外卡',
        'CID_NOT_IN_DECLARED_SCOPE': 'cid 不在调用方声明范围',
        'ALTERNATE_TIER_VALUE_EXCLUDED':
            '同卡其他档位的同类型伤害输入不同值：只登记排除，不并入本行',
        'ALTERNATE_TIER_SAME_RECORD_DISCLOSED':
            '同卡其他 pattern 以同记录同值引用：只披露，不重复新增数值',
        'ALTERNATE_TIER_SAME_VALUE_DIFF_RECORD':
            '同卡其他档位异记录同值：只披露，不按值配对',
        'ALTERNATE_TIER_OTHER_DAMAGE_TYPE':
            '同卡其他档位的其他伤害类型载体：只披露，不并入本行',
        'ALTERNATE_TIER_RECORD_MISSING': '同卡其他档位的记录缺失：只登记，不取值',
    }.get(code, code)


def _reason_counts(items):
    out = {}
    for item in items:
        code = item.get('reason_code') or 'UNKNOWN'
        out[code] = out.get(code, 0) + 1
    return dict(sorted(out.items()))


def _category_counts(items):
    out = {}
    for item in items:
        cat = item.get('category') or 'UNKNOWN'
        out[cat] = out.get(cat, 0) + 1
    return dict(sorted(out.items()))


# ---------------------------------------------------------------- 写盘（只限候选目录）

def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + '\n'


def write_outputs(root, *, run_record=True):
    """写候选／排除 JSON；``run_record`` 额外写运行回执（含时间戳，不参与幂等比较）。"""
    import datetime
    root = Path(root).resolve()
    out_dir = root / OUT_DIR_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    cand, exc = build_candidates(root)
    cpath = out_dir / 'candidates.json'
    epath = out_dir / 'exclusions.json'
    ctext, etext = _dump(cand), _dump(exc)
    # 用 bytes 写入，避免 Windows 文本模式把 LF 转成 CRLF 导致回执哈希与实际文件不一致。
    cpath.write_bytes(ctext.encode('utf-8'))
    epath.write_bytes(etext.encode('utf-8'))
    written = {'candidates': str(cpath), 'exclusions': str(epath),
               'candidates_sha256': hashlib.sha256(ctext.encode('utf-8')).hexdigest(),
               'exclusions_sha256': hashlib.sha256(etext.encode('utf-8')).hexdigest()}
    if run_record:
        record = {
            'schema': 'c14-p2-boss-damage-direct-run-record-1',
            'module': MODULE_VERSION,
            'module_path': 'scripts/character_skills/card_page_inference_c14_p2_boss_damage_direct.py',
            'module_sha256': sha256_file(Path(__file__).resolve()),
            'command': ('./.venv/Scripts/python.exe -B scripts/character_skills/'
                        'card_page_inference_c14_p2_boss_damage_direct.py --write'),
            'generated_at_utc': datetime.datetime.now(datetime.timezone.utc)
                                .replace(microsecond=0).isoformat(),
            'inputs': cand['inputs'],
            'counts': cand['counts'],
            'outputs': written,
            'note': ('candidates.json／exclusions.json 不含时间戳，重跑逐字节一致；'
                     '本回执含运行时间，仅供追溯，不参与幂等比较。'),
        }
        rpath = out_dir / 'run_record.json'
        rpath.write_bytes(_dump(record).encode('utf-8'))
        written['run_record'] = str(rpath)
    return {'counts': cand['counts'], 'outputs': written}


# ---------------------------------------------------------------- 正式页消费（候选未接线）

def apply_to_groups(data, cid, groups, *, scope_cids=None):
    """把本批答案追加到**内存** groups（候选未接线；不写盘、不改共享账本）。

    ``scope_cids`` 必须显式声明且包含 cid；默认只接受 ``ADMITTED_CIDS``。幂等：
    同 rule_key 同记录同值已在时零新增。
    """
    report = {'scope': STRUCTURE_SCOPE, 'cid': cid, 'answers_added': 0,
              'skipped_existing': 0, 'rejections': [], 'additions': []}
    allowed = frozenset(scope_cids) if scope_cids is not None else frozenset(ADMITTED_CIDS)
    if cid not in allowed:
        report['rejections'].append({'reason': 'CID_NOT_IN_DECLARED_SCOPE'})
        return report
    if cid in ZERO_TOUCH_CIDS or cid in OUT_OF_SCOPE_CIDS:
        report['rejections'].append({'reason': 'ZERO_TOUCH_OR_OUT_OF_SCOPE_CID'})
        return report
    # 范围检查先于任何原始输入读取；范围外/保护卡零读取、零新增。
    view = view_for(data)
    rows = [(g.get('group'), s, r) for g in groups or []
            for s in g.get('skills') or [] for r in s.get('rows') or []]
    siblings = [r for gn, s, r in rows if s.get('reference_field') == 'skilltext']
    for group, skill, row in rows:
        if skill.get('reference_field') != 'skilltext':
            continue
        res = evaluate(view, cid, row, skill=skill, siblings=siblings)
        if res['decision'] == 'SKIP_ALREADY_PRESENT':
            report['skipped_existing'] += 1
            continue
        if res['decision'] != 'ACCEPT':
            report['rejections'].append({'row_id': row.get('row_id'),
                                         'reason': res['reason'] or res['rejection']})
            continue
        selected = res['selected']
        tiers = other_tiers(view, cid, selected, res['parent']['pattern_id'])
        carriers = carriers_in_pattern(view, res['pattern'], selected['skillid'])
        slot0 = charainfo_slot0_equivalence(res['parent']['record'], res['pattern'], view)
        collision = id_collision(view, selected['skillid'], res['parent']['pattern_id'])
        page_sha_fn = getattr(view, 'page_sha256', None)
        if page_sha_fn is not None:
            page_sha = page_sha_fn(cid)
        elif getattr(view, 'root', None) is not None:
            page_sha = sha256_file(Path(view.root) / PAGES_REL / str(cid) / 'card.json')
        else:
            page_sha = None
        answer = build_answer(view, cid, row, res, tiers, carriers, slot0, collision,
                              page_sha)
        key = lambda a: (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
        if any(key(a) == key(answer) for a in row.get('answers') or []):
            report['skipped_existing'] += 1
            continue
        row.setdefault('answers', []).append(answer)
        row['row_class'] = 'A'
        row['partial'] = True
        row['association_evidence'] = '推断'
        row['numeric_evidence'] = '确认'
        row['evidence_scope'] = list(dict.fromkeys(
            list(row.get('evidence_scope') or []) + ['BY_TYPE_EXTRAPOLATED']))
        reasons = [r for r in (row.get('unknown_reasons') or []) if r not in _STALE_REASONS]
        reasons.append('C14-P2：本行对敌伤害段已按 charainfo.pattern0 直接链绑定伤害输入倍率'
                       '（同卡其他档位值已登记排除）；同句其余机制仍登记待办。')
        row['unknown_reasons'] = reasons
        row[MARKER_KEY] = {'scope': STRUCTURE_SCOPE, 'module': MODULE_VERSION,
                           'row_id': row.get('row_id'),
                           'rule_key': answer['rule_key'],
                           'record_id': answer['record_id'],
                           'raw_value': answer['raw_value'],
                           'association': '推断',
                           'note': '候选 marker：不新增/不改写答案时也保留判定与披露。'}
        report['answers_added'] += 1
        report['additions'].append({'row_id': row.get('row_id'),
                                    'rule_key': answer['rule_key'],
                                    'record_id': answer['record_id'],
                                    'raw_value': answer['raw_value']})
    return report


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(
        description='C14-P2 charainfo.pattern0→bossskill 直接链伤害候选（只写候选目录）')
    ap.add_argument('--write', action='store_true',
                    help='写 candidates.json／exclusions.json／run_record.json 到候选目录')
    ap.add_argument('--json', action='store_true', help='打印汇总 JSON')
    ap.add_argument('--root', default=None, help='仓库根（默认由脚本位置推断）')
    args = ap.parse_args(argv)
    root = Path(args.root) if args.root else Path(__file__).resolve().parents[2]
    if args.write:
        result = write_outputs(root)
    else:
        cand, exc = build_candidates(root)
        result = {'counts': cand['counts'],
                  'module': MODULE_VERSION,
                  'ledger_scope': LEDGER_SCOPE}
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=1))
    else:
        c = result['counts']
        print('C14-P2 candidate: rows=%s candidates=%s answers=%s cids=%s exclusions=%s'
              % (c['rows_evaluated'], c['candidates'], c['answers'], c['cids'],
                 c['exclusions']))
        if args.write:
            for key, value in result['outputs'].items():
                print('%s: %s' % (key, value))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
