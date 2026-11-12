# -*- coding: utf-8 -*-
"""C16-P1 ``skilllist`` ability 1095 逐效果部分绑定——**代表样本试点候选实现（未接线）**。

任务卡 ``docs/tasks/20261104-c16-p1-1095-partial-binding.md``；C16 周期卡
``docs/tasks/20261104-c16-cycle.md``；方法 ``docs/角色技能完整解读实施方案.md`` §1.3／§1.6；
方案 ``docs/tasks/20261104-mechanism-first-next-batch-plan.md``。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；
``rules.json``／``rules.py``／``effect_ledger.py``／正式 ``pages``／账本均未改动；
本阶段不运行正式全库生成或 resume。模块只读当前快照解码 JSON、``profiles/rules.json``，
并由调用方传入真实 ``card_page_data.Inputs`` 与页面行对象（``build_card`` 产物）。

本文件包含两层，互不取代：

* **试点层**（``PILOT_CIDS``／``FROZEN_TARGETS``／``evaluate``／``apply_to_groups``）：
  3 卡 11 effect 的代表样本，行为保持原样，供 ``pilot/check_pilot.py`` 回归。
* **全批候选层**（``YG_TARGETS``／``NON_YG_TARGETS``／``BATCH_TARGETS``／``evaluate_batch``／
  ``apply_batch_to_groups``）：C16-P1 全批 49 项／23 卡，见文件末尾“全批候选层”段。
  两层都不接线、不写正式 pages／ledger／rules。

试点作用域（严格 11 个 effect）
-------------------------------
==========  ==================================================  ================  ======================  ==========
cid         row_id                                              effect_id         槽位                     句面主张
==========  ==================================================  ================  ======================  ==========
20822       ``…skillid_1_-lvorder0-f2``                         ``#e00``          param1                  攻撃力
20822       同上                                                ``#e01``          param3                  防御力
20822       同上                                                ``#e02``          param2                  移動速度
20822       同上                                                ``#e03``          param5                  クリティカル発生率
20906       ``…skillid_1_-lvorder0-f1``                         ``#e00``          param1                  攻撃力
20906       同上（1095 在 ``sub[1]``）                           ``#e01``          param3                  防御力
20906       同上                                                ``#e02``          param2                  移動速度
20906       同上                                                ``#e03``          param5                  クリティカル発生率
30246       ``…skillid_1_-lvorder0-f2``                         ``#e00``          param1                  攻撃力
30246       同上                                                ``#e01``          param5                  クリティカル発生率
30246       同上                                                ``#e02``          param6                  クリティカル威力
==========  ==================================================  ================  ======================  ==========

**冻结表只含身份，不含任何数值**：``FROZEN_TARGETS`` 保存 cid／row_id／effect_id／槽位／
rule_key／句面主张。raw 与派生值一律由「真实角色 → 父 skilllist → 唯一 1095 子记录 → 字段」
重算；``check_pilot.py`` 只把交接包种子在**计算之后**比对（本模块不读取、不命名、不导入该种子文件）。

逐行硬门（任一不符即拒绝，不猜、不取邻近记录、不补零）
------------------------------------------------------
R1  **角色上游**：``charainfo[cid]`` 在 CACHE 解码表**唯一存在**（20607 无此记录 → 拒绝）。
R2  **角色身份**：行 ``cid`` 与调用 cid 相同。
R3  **引用形态**：行 ``group == 'ability'`` 且 ``reference_field`` 恰为 ``skillid[n]``
    （special_move ``pattern0`` 等 type108 行在此拒绝，结构上不可达）。
R4  **槽位**：``charainfo.skillid[n]`` 存在（不越界）。
R5  **父记录唯一**：该 skillid 在 CACHE ``skilllist`` 全表**恰出现 1 次**；``Inputs`` 记录
    与解码原文逐值相同。
R6  **行来源指针**：行 ``source.json_pointer == /skilllist/<父下标>`` 且
    ``field_json_pointer == /skilllist/<父下标>/text``。
R7  **片段归属**：行日语（NFKC、去空白）在父 ``text`` 中**恰出现 1 次**。
R8  **子记录唯一**：父 ``sub[]`` 每个 skillid 在全表唯一命中，且 ``Inputs`` 记录与原文相同。
R9  **载体唯一**：``sub[]`` 中 ``ability == 1095`` 的记录**恰 1 条**（0 或多条 → 拒绝；
    20906 命中 ``sub[1]``，按真实下标解引用，不按 ``sub[0]`` 假设）。
R10 **字段解引用**：只在冻结 effect 对应槽位上取值；``missing／null／非有限／负值／真零``
    分别登记且**都不产出答案**（不补零、不借相邻类型）。
R11 **规则复用**：只调用 ``rules.answer_for('skilllist', 1095, '/<槽>', raw, 载体,
    source_layer='CACHE')``；本模块不新增公式、不新增规则键。规则缺失 → 拒绝。

**部分绑定边界**：某槽位“存在”不证明属于当前句。20822 的载体同时有 ``param6 = 2``，但本片段
句面只有攻撃力／防御力／移動速度／クリティカル発生率四项，因此 ``param6`` 被登记为
``EXCLUDED_FIELD_NOT_CLAIMED``，**不并入**基础句（与旧 P4 形状不符判据同向，不全局删除 P4）。

证据分档（不得升格）
--------------------
R1–R9 与字段原值为结构／原值证据；句面主张→该 1095 子记录字段的归属为**推断**。答案写
``numeric_evidence='确认'``（静态及受控原生局部规则＋CACHE 原始记录）、
``association_evidence='推断'``、``answer_status`` 取 ``rules.answer_for`` 的返回；
``evidence_scope = SCOPE``；``runtime_verified = False``。不称完全确认、不称实机验证。

明确不处理
----------
* 20607 四项 ``PENDING_RAW_UPSTREAM`` 与暴击率未知项：缺原始角色上游，本模块拒绝，不补值。
* type108 七项（350／30252／30214／20832／2323／13228／343）：非 1095 ability 行，未知保持。
* 30236／30239／30102／20234：零新增（结构上不在试点作用域）。
* 不改 ``effect_ledger.py``：11 个目标效果由既有 ``_RULE_KEY_EFFECT``
  （``effect_ledger.py:469-471``，1095 五键）消费，不需要新映射。
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from project_layout_paths import read_path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:            # 允许从任意工作目录直接导入
    sys.path.insert(0, str(_HERE))

import effect_ledger as LEDGER             # 只读：真实消费者
import rules as R                          # 只读：既有规则与公式

MODULE_VERSION = 'c16_p1_1095_partial_20261104'
#: 本试点作用域（缺省／错误 scope 一律硬拒绝；见 ``ScopeError``）。
SCOPE = 'C16_P1_1095_PARTIAL_20261104'
STRUCTURE_SCOPE = SCOPE
CARRIER_ABILITY = 1095
DECODED_REL = 'output/cache_full_20261015_v3/decoded'
SKILLLIST_REL = DECODED_REL + '/skilllist.data5.json.raw'
CHARAINFO_REL = DECODED_REL + '/charainfo.data5.json.raw'
RESOLVED_EXACT = 'RESOLVED_EXACT_DECODED_RECORD'

#: 句面主张 → 1095 槽位。取值依据＝``effect_ledger.py:469-471`` 既有映射
#: （攻撃力→param1／移動速度→param2／防御力→param3／クリティカル発生率→param5／
#: クリティカル威力→param6），本模块不新增映射。
CLAIM_FOR_SLOT = {
    'param1': '攻撃力',
    'param2': '移動速度',
    'param3': '防御力',
    'param5': 'クリティカル発生率',
    'param6': 'クリティカル威力',
}
SLOT_FOR_CLAIM = {v: k for k, v in CLAIM_FOR_SLOT.items()}

#: 试点 3 卡（apply 白名单）。
PILOT_CIDS = (20822, 20906, 30246)
#: 保护／边界卡：零新增。
ZERO_TOUCH_CIDS = (30236, 30239, 30102, 20234)
#: 待补原始上游（20607 四项 + 暴击率未知）。
PENDING_CIDS = (20607,)
#: type108 七项未知所在卡。
TYPE108_UNKNOWN_CIDS = (350, 30252, 30214, 20832, 2323, 13228, 343)

#: 逐卡负面行（check_pilot 用；本模块只登记身份，不据此产出答案）。
NEGATIVE_ROWS = {
    20607: ('20607-ability-ability-skillid_1_-lvorder0-f1',),
    350: ('350-special_move-special_move-pattern0-lvorder0-f3',),
    30252: ('30252-special_move-special_move-pattern0-lvorder0-f2',),
    30214: ('30214-special_move-special_move-pattern0-lvorder0-f0',),
    20832: ('20832-special_move-special_move-pattern0-lvorder0-f2',),
    2323: ('2323-special_move-special_move-pattern1-lvorder1-f0',),
    13228: ('13228-special_move-special_move-pattern0-lvorder0-f2',),
    343: ('343-special_move-special_move-pattern0-lvorder0-f3',),
}
#: 20822 额外 param6 不得并入基础句（载体确有该字段，属“存在≠归属”反例）。
FORBIDDEN_FIELDS = {20822: ('param6',)}


def _frozen(cid, row_id, effect_id, slot, rule_key):
    return dict(cid=cid, row_id=row_id, effect_id=effect_id, slot=slot,
                claim=CLAIM_FOR_SLOT[slot], rule_key=rule_key)


FROZEN_TARGETS = (
    _frozen(20822, '20822-ability-ability-skillid_1_-lvorder0-f2',
            '20822-ability-ability-skillid_1_-lvorder0-f2#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20822, '20822-ability-ability-skillid_1_-lvorder0-f2',
            '20822-ability-ability-skillid_1_-lvorder0-f2#e01', 'param3', 'skilllist|1095|/param3'),
    _frozen(20822, '20822-ability-ability-skillid_1_-lvorder0-f2',
            '20822-ability-ability-skillid_1_-lvorder0-f2#e02', 'param2', 'skilllist|1095|/param2'),
    _frozen(20822, '20822-ability-ability-skillid_1_-lvorder0-f2',
            '20822-ability-ability-skillid_1_-lvorder0-f2#e03', 'param5', 'skilllist|1095|/param5'),
    _frozen(20906, '20906-ability-ability-skillid_1_-lvorder0-f1',
            '20906-ability-ability-skillid_1_-lvorder0-f1#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20906, '20906-ability-ability-skillid_1_-lvorder0-f1',
            '20906-ability-ability-skillid_1_-lvorder0-f1#e01', 'param3', 'skilllist|1095|/param3'),
    _frozen(20906, '20906-ability-ability-skillid_1_-lvorder0-f1',
            '20906-ability-ability-skillid_1_-lvorder0-f1#e02', 'param2', 'skilllist|1095|/param2'),
    _frozen(20906, '20906-ability-ability-skillid_1_-lvorder0-f1',
            '20906-ability-ability-skillid_1_-lvorder0-f1#e03', 'param5', 'skilllist|1095|/param5'),
    _frozen(30246, '30246-ability-ability-skillid_1_-lvorder0-f2',
            '30246-ability-ability-skillid_1_-lvorder0-f2#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30246, '30246-ability-ability-skillid_1_-lvorder0-f2',
            '30246-ability-ability-skillid_1_-lvorder0-f2#e01', 'param5', 'skilllist|1095|/param5'),
    _frozen(30246, '30246-ability-ability-skillid_1_-lvorder0-f2',
            '30246-ability-ability-skillid_1_-lvorder0-f2#e02', 'param6', 'skilllist|1095|/param6'),
)
FROZEN_BY_ROW = {}
for _t in FROZEN_TARGETS:
    FROZEN_BY_ROW.setdefault((_t['cid'], _t['row_id']), []).append(_t)
FROZEN_ROW_IDS = {cid: {rid for (c, rid) in FROZEN_BY_ROW if c == cid} for cid in PILOT_CIDS}


class ScopeError(RuntimeError):
    """缺省／错误 scope——硬拒绝，不做默认回退。"""


def require_scope(scope):
    if scope is None:
        raise ScopeError(f'缺少 scope 参数：必须显式传入 {SCOPE!r}（不设默认值）')
    if scope != SCOPE:
        raise ScopeError(f'scope 不符：收到 {scope!r}，本模块只接受 {SCOPE!r}')


# ---------------------------------------------------------------- 文本／数值小工具（只读）
def canon(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def raw_state(record, slot):
    """字段状态分档（missing／null／bool／non-finite／negative／zero／present）。"""
    if slot not in record:
        return 'missing'
    value = record[slot]
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'bool'
    if not isinstance(value, (int, float)):
        return 'non-numeric'
    if not math.isfinite(value):
        return 'non-finite'
    if value < 0:
        return 'negative'
    if value == 0:
        return 'zero'
    return 'present'


def num_text(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    text = ('%.6f' % f).rstrip('0').rstrip('.')
    return text or '0'


def percent_text(value):
    """派生百分比文本；派生式只复述 ``rules.json`` 既有 conversion，不新增公式。"""
    if value is None:
        return None
    r = round(float(value), 6)
    if abs(r - round(r)) < 1e-9:
        return str(int(round(r)))
    return ('%.6f' % r).rstrip('0').rstrip('.')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- 只读解码表（唯一性用）
_RAW_CACHE = {}


def raw_tables(root):
    """按 root 缓存 skilllist／charainfo 原文与 skillid／cid → 下标列表（含重复计数）。"""
    key = str(Path(root).resolve())
    if key not in _RAW_CACHE:
        base = Path(root)
        skill = json.loads(read_path(base / SKILLLIST_REL, root=base).read_text(encoding='utf-8-sig'))['skilllist']
        chara = json.loads(read_path(base / CHARAINFO_REL, root=base).read_text(encoding='utf-8-sig'))['charainfo']
        skill_index = {}
        for i, rec in enumerate(skill):
            skill_index.setdefault(rec.get('skillid'), []).append(i)
        chara_index = {}
        for i, rec in enumerate(chara):
            chara_index.setdefault(rec.get('cid'), []).append(i)
        _RAW_CACHE[key] = dict(skilllist=skill, charainfo=chara,
                               skill_index=skill_index, chara_index=chara_index,
                               skilllist_sha256=sha256_file(read_path(base / SKILLLIST_REL, root=base)),
                               charainfo_sha256=sha256_file(read_path(base / CHARAINFO_REL, root=base)))
    return _RAW_CACHE[key]


# ---------------------------------------------------------------- 链解析（R1–R10）
def _gate(gates, code, ok, detail, **extra):
    gates.append(dict(code=code, ok=bool(ok), detail=detail, **extra))
    return bool(ok)


def _reject(gates, code, detail, **extra):
    _gate(gates, code, False, detail, **extra)
    return dict(status='REJECTED', reason=code, detail=detail, gates=gates)


def resolve_chain(data, cid, row, skill=None):
    """真实角色→父 skilllist→唯一 1095 子记录；返回结构证据，不产出任何数值答案。"""
    gates = []
    raw = raw_tables(data.root)

    chara = data.cache_chara.get(cid)
    if chara is None:
        return _reject(gates, 'R1_CHARAINFO_RECORD_MISSING',
                       f'CACHE charainfo 无 cid={cid}：原始角色上游缺失，不借页面/相邻记录补值',
                       cid=cid)
    _gate(gates, 'R1_CHARAINFO_RECORD_MISSING', True, 'CACHE charainfo 记录存在')
    chara_idx = raw['chara_index'].get(cid) or []
    if len(chara_idx) != 1:
        return _reject(gates, 'R1_CHARAINFO_NOT_UNIQUE',
                       f'charainfo cid={cid} 匹配 {len(chara_idx)} 条，要求恰 1 条', cid=cid)

    if int(row.get('cid', -1)) != int(cid):
        return _reject(gates, 'R2_ROW_CID_MISMATCH',
                       f"行 cid={row.get('cid')!r} 与调用 cid={cid} 不一致")

    ref = str(row.get('reference_field') or '')
    m = re.fullmatch(r'skillid\[(\d+)\]', ref)
    if not m or row.get('group') != 'ability':
        return _reject(gates, 'R3_ROW_NOT_ABILITY_SKILLID_REFERENCE',
                       f'行 group={row.get("group")!r}／reference_field={ref!r} 不是 '
                       'ability skillid[n]：非 1095 能力行（含 type108 pattern 行）结构上不适用',
                       group=row.get('group'), reference_field=ref)
    slot_index = int(m.group(1))
    _gate(gates, 'R3_ROW_NOT_ABILITY_SKILLID_REFERENCE', True,
          f'ability {ref} 引用形态成立')

    skillids = chara.get('skillid') or []
    if slot_index >= len(skillids) or not isinstance(skillids[slot_index], int):
        return _reject(gates, 'R4_CHARAINFO_SKILLID_SLOT_MISSING',
                       f'charainfo.skillid[{slot_index}] 缺失或非整数：{skillids!r}')
    sid = skillids[slot_index]
    _gate(gates, 'R4_CHARAINFO_SKILLID_SLOT_MISSING', True,
          f'charainfo.skillid[{slot_index}] = {sid}')

    parent_idx = raw['skill_index'].get(sid) or []
    if len(parent_idx) != 1:
        return _reject(gates, 'R5_PARENT_NOT_UNIQUE',
                       f'skillid={sid} 在 CACHE 全表匹配 {len(parent_idx)} 条，要求恰 1 条',
                       parent_skillid=sid)
    pidx = parent_idx[0]
    parent = raw['skilllist'][pidx]
    bound = data.cache_skill.get(sid)
    if bound is None or bound[1] != parent:
        return _reject(gates, 'R5_PARENT_INPUT_MISMATCH',
                       f'Inputs 中 skillid={sid} 与解码原文记录不一致', parent_skillid=sid)
    if skill is not None and skill.get('record_id') not in (None, sid):
        return _reject(gates, 'R5_PARENT_INPUT_MISMATCH',
                       f"skill.record_id={skill.get('record_id')!r} != charainfo.skillid["
                       f'{slot_index}]={sid}')
    _gate(gates, 'R5_PARENT_NOT_UNIQUE', True,
          f'父记录唯一：skillid={sid} @ /skilllist/{pidx}')

    src = row.get('source') or {}
    want_ptr = f'/skilllist/{pidx}'
    if src.get('json_pointer') != want_ptr or src.get('field_json_pointer') != want_ptr + '/text':
        return _reject(gates, 'R6_ROW_SOURCE_POINTER_MISMATCH',
                       f'行来源指针 {src.get("json_pointer")!r}／'
                       f'{src.get("field_json_pointer")!r} 与父记录 {want_ptr} 不符')
    _gate(gates, 'R6_ROW_SOURCE_POINTER_MISMATCH', True, f'行来源指针 = {want_ptr}/text')

    frag = canon(row.get('japanese'))
    if not frag or canon(parent.get('text')).count(frag) != 1:
        return _reject(gates, 'R7_PARENT_TEXT_NOT_FRAGMENT',
                       '行日语片段在父 text 中出现次数 != 1（0 或多处均拒绝）')
    _gate(gates, 'R7_PARENT_TEXT_NOT_FRAGMENT', True, '行日语片段在父 text 中恰出现 1 次')

    subs = parent.get('sub') or []
    if not subs:
        return _reject(gates, 'R8_SUBS_MISSING', '父记录 sub[] 为空')
    sub_records = []
    for sub_sid in subs:
        idx_list = raw['skill_index'].get(sub_sid) or []
        if len(idx_list) != 1:
            return _reject(gates, 'R8_SUB_NOT_UNIQUE',
                           f'sub skillid={sub_sid} 在全表匹配 {len(idx_list)} 条',
                           sub_skillid=sub_sid)
        srec = raw['skilllist'][idx_list[0]]
        bind = data.cache_skill.get(sub_sid)
        if bind is None or bind[1] != srec:
            return _reject(gates, 'R8_SUB_INPUT_MISMATCH',
                           f'sub skillid={sub_sid} 的 Inputs 记录与解码原文不一致')
        sub_records.append(dict(skillid=sub_sid, index=idx_list[0], record=srec,
                                ability=srec.get('ability')))
    _gate(gates, 'R8_SUBS_MISSING', True,
          f'父 sub[] 共 {len(sub_records)} 条，逐条唯一命中')

    carriers = [x for x in sub_records if x.get('ability') == CARRIER_ABILITY]
    if len(carriers) != 1:
        return _reject(gates, 'R9_CARRIER_1095_NOT_UNIQUE',
                       f'父 sub[] 中 ability=1095 的记录 {len(carriers)} 条，要求恰 1 条'
                       '（不按 sub[0] 假设、不取邻近记录）',
                       abilities=[x.get('ability') for x in sub_records])
    carrier = carriers[0]
    carrier_slot = sub_records.index(carrier)
    _gate(gates, 'R9_CARRIER_1095_NOT_UNIQUE', True,
          f'唯一 1095 载体：skillid={carrier["skillid"]} @ sub[{carrier_slot}] '
          f'（/skilllist/{carrier["index"]}）')

    states = {slot: raw_state(carrier['record'], slot) for slot in CLAIM_FOR_SLOT}
    _gate(gates, 'R10_FIELD_STATES', True,
          '载体字段状态：' + '，'.join(f'{k}={v}' for k, v in states.items()))

    return dict(
        status='RESOLVED', reason=None, gates=gates, cid=cid, row_id=row.get('row_id'),
        charainfo=dict(table='charainfo', record_id=cid, index=chara_idx[0],
                       json_pointer=f'/charainfo/{chara_idx[0]}',
                       field_json_pointer=f'/charainfo/{chara_idx[0]}/skillid',
                       reference_field=ref, skillid_slot=slot_index),
        parent=dict(table='skilllist', record_id=sid, index=pidx,
                    json_pointer=f'/skilllist/{pidx}', ability=parent.get('ability')),
        carrier=dict(table='skilllist', record_id=carrier['skillid'], index=carrier['index'],
                     json_pointer=f'/skilllist/{carrier["index"]}', ability=CARRIER_ABILITY,
                     carrier_slot=carrier_slot, record=carrier['record'],
                     record_key=f'CACHE/skilllist.data5.json.raw#/skilllist/{carrier["index"]}'),
        carrier_slot=carrier_slot,
        sub_abilities=[dict(skillid=x['skillid'], ability=x['ability'], index=x['index'])
                       for x in sub_records],
        field_states=states,
        fragment=dict(row_id=row.get('row_id'), japanese=row.get('japanese'),
                      parent_field_json_pointer=want_ptr + '/text',
                      fragment_index=row.get('fragment_index')),
    )


# ---------------------------------------------------------------- 答案构造（R10/R11）
def _source_block(chain, slot):
    carrier = chain['carrier']
    return {
        'layer': 'CACHE', 'table': 'skilllist', 'record_id': carrier['record_id'],
        'record_index': carrier['index'], 'record_key': carrier['record_key'],
        'source_key': 'CACHE/skilllist.data5.json.raw',
        'original_file': SKILLLIST_REL,
        'json_pointer': carrier['json_pointer'],
        'field_path': '/' + slot,
        'field': '/' + slot,
        'field_json_pointer': f'{carrier["json_pointer"]}/{slot}',
        'carrier_slot': f'sub[{chain["carrier_slot"]}]',
        'parent_record_id': chain['parent']['record_id'],
        'parent_record_index': chain['parent']['index'],
        'parent_json_pointer': chain['parent']['json_pointer'],
        'charainfo': chain['charainfo'],
        'row_fragment': chain['fragment'],
        'source_resolution': RESOLVED_EXACT,
    }


def player_sentence(slot, raw):
    """玩家可读中文（§1.3）：对象／数值／单位／条件／未解边界；不使用内部术语当答案。"""
    if slot == 'param1':
        pct = (float(raw) - 1.0) * 100
        return (f'自身攻击力提高 {percent_text(pct)}%（本能力单项：攻击因子×{num_text(raw)}；'
                '不含其他来源与后续条件强化，最终数值未实机验证）')
    if slot == 'param2':
        pct = (float(raw) - 1.0) * 100
        return (f'自身移动速度提高 {percent_text(pct)}%（本能力单项：移动因子×{num_text(raw)}；'
                '不含地形等其他来源）')
    if slot == 'param3':
        pct = (1.0 - float(raw)) * 100
        return (f'自身受到的伤害减少 {percent_text(pct)}%（本能力单项：受伤量×{num_text(raw)}；'
                '这是按比例减伤，不是固定防御值；最终数值未实机验证）')
    if slot == 'param5':
        return (f'自身暴击率提高 {percent_text(float(raw) * 100)} 个百分点'
                '（本能力单项：对 0 的加算增量；不等于最终暴击率）')
    if slot == 'param6':
        delta = float(raw) - 1.5
        return (f'自身暴击伤害系数提高 {percent_text(delta)}'
                '（本能力单项：在 1.5 基准系数之上加算；不是相对现有伤害的百分比）')
    raise ValueError(f'未定义的 1095 槽位：{slot!r}')


def build_answer(chain, target):
    """按冻结 target 构造单条答案；字段缺失/零/规则缺失 → ``(None, reason)``。"""
    slot = target['slot']
    carrier = chain['carrier']['record']
    state = chain['field_states'].get(slot)
    if state != 'present':
        return None, dict(code='FIELD_' + state.upper(),
                          detail=f'载体 skillid={chain["carrier"]["record_id"]} 字段 /{slot} '
                                 f'状态={state}：不补零、不借相邻记录')
    raw = carrier[slot]
    rule = R.answer_for('skilllist', CARRIER_ABILITY, '/' + slot, raw, carrier,
                        source_layer='CACHE')
    if not rule:
        return None, dict(code='RULE_MISSING',
                          detail=f'rules.answer_for 未返回 skilllist|1095|/{slot}')
    answer = {
        'value': rule.get('value_text'),
        'player_text': player_sentence(slot, raw),
        'player_scope': {
            'object': '自身（接受者）',
            'quantity': rule.get('quantity_kind'),
            'unit': rule.get('unit'),
            'conditions': [
                '接受者自身已装载该能力（当前载体为 CACHE ability1095 子记录）',
                '相应资格／能力列表／类型分派通过时生效',
                '仅本项单一载体的局部贡献，不含其他来源与后续条件增强',
            ],
            'unknowns': [
                '运行时实际装载与资格未核实（未实机）',
                '与其他来源的实际叠加与最终战斗数值未验证',
                '本句面→该 1095 子记录字段的句内归属为推断',
            ],
        },
        'quantity_kind': rule.get('quantity_kind'),
        'unit': rule.get('unit'),
        'raw_value': raw,
        'field_path': '/' + slot,
        'numeric_source': '既有已确认规则（profiles/rules.json＋ordinary_effects/ability1095）'
                          '＋CACHE skilllist 原始记录',
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'answer_status': rule.get('answer_status'),
        'evidence_scope': SCOPE,
        'rule_key': target['rule_key'],
        'table': 'skilllist',
        'record_id': chain['carrier']['record_id'],
        'layer': 'CACHE',
        'target': rule.get('target'),
        'conversion': rule.get('conversion'),
        'base_definition': rule.get('base_definition'),
        'conditions': '；'.join(rule.get('conditions') or [])
                      if isinstance(rule.get('conditions'), list) else rule.get('conditions'),
        'rule_limits': rule.get('rule_limits'),
        'rule_status': rule.get('rule_status'),
        'source': _source_block(chain, slot),
        'binding': {'c16_p1_1095_partial_binding': {
            'scope': SCOPE,
            'row_id': target['row_id'],
            'effect_id': target['effect_id'],
            'claim': target['claim'],
            'slot': slot,
            'rule_key': target['rule_key'],
            'carrier_table': 'skilllist',
            'carrier_record_id': chain['carrier']['record_id'],
            'carrier_layer': 'CACHE',
            'carrier_slot': f'sub[{chain["carrier_slot"]}]',
            'parent_record_id': chain['parent']['record_id'],
            'charainfo_record_id': chain['cid'],
            'raw_value': raw,
            'binding': 'inferred',
            'runtime_verified': False,
        }},
        'details': rule,
    }
    return answer, None


# ---------------------------------------------------------------- 公开 API
def evaluate(data, cid, row, *, scope=None, skill=None):
    """解析单行并返回候选答案（不写入）。``scope`` 缺省/错误 → ``ScopeError``。"""
    require_scope(scope)
    out = dict(cid=cid, row_id=row.get('row_id'), scope=scope,
               module_version=MODULE_VERSION, answers=[], rejected=[],
               excluded_fields=[], matched_effects=[], missing_targets=[])
    chain = resolve_chain(data, cid, row, skill=skill)
    out['chain'] = dict(status=chain['status'], reason=chain.get('reason'),
                        detail=chain.get('detail'), gates=chain.get('gates') or [],
                        carrier=(None if chain['status'] != 'RESOLVED' else dict(
                            record_id=chain['carrier']['record_id'],
                            index=chain['carrier']['index'],
                            carrier_slot=chain['carrier_slot'],
                            parent_record_id=chain['parent']['record_id'],
                            parent_index=chain['parent']['index'])),
                        field_states=chain.get('field_states'))
    if chain['status'] != 'RESOLVED':
        out['status'] = 'REJECTED'
        out['reason'] = chain.get('reason')
        return out

    targets = FROZEN_BY_ROW.get((cid, row.get('row_id')))
    if not targets:
        out['status'] = 'ROW_OUT_OF_SCOPE'
        out['reason'] = 'ROW_NOT_IN_FROZEN_SCOPE'
        return out

    analysis = LEDGER.analyze_row(row, table='skilllist')
    effects = [e for e in analysis.get('effects') or []
               if e.get('record_type') == 'effect' and '#e' in e.get('effect_id', '')]
    by_id = {e['effect_id']: e for e in effects}

    frozen_ids = {t['effect_id'] for t in targets}
    for t in targets:
        effect = by_id.get(t['effect_id'])
        if effect is None:
            out['missing_targets'].append(dict(effect_id=t['effect_id'],
                                               detail='该 effect_id 未出现在当前解析结果'))
            continue
        out['matched_effects'].append(dict(
            effect_id=t['effect_id'], effect_type=effect.get('effect_type'),
            direction=effect.get('direction'), status_before=effect.get('status'),
            claim_expected=t['claim'], claim_matches=effect.get('effect_type') == t['claim']))
        answer, why = build_answer(chain, t)
        if answer is None:
            out['rejected'].append(dict(effect_id=t['effect_id'], slot=t['slot'], **why))
            continue
        out['answers'].append(answer)

    # 句面未主张的载体字段：登记排除，不产出答案（20822 param6=2 属此列）。
    claimed_slots = {t['slot'] for t in targets}
    for slot, state in chain['field_states'].items():
        if slot in claimed_slots:
            continue
        out['excluded_fields'].append(dict(
            slot=slot, state=state, raw_value=chain['carrier']['record'].get(slot),
            code='EXCLUDED_FIELD_NOT_CLAIMED',
            detail=('载体存在该字段，但本片段句面无对应主张：不并入基础句'
                    '（存在≠归属；不删旧 P4、不全局放宽）')))

    out['status'] = ('RESOLVED_ALL' if len(out['answers']) == len(targets)
                     else 'RESOLVED_PARTIAL')
    out['effect_ids'] = sorted(frozen_ids)
    out['analysis_summary'] = dict(
        effect_status=[dict(effect_id=e['effect_id'], effect_type=e['effect_type'],
                            status=e['status']) for e in effects],
        split_flags=analysis.get('split_flags'),
        unmatched_answer_refs=[r for r in analysis.get('answer_refs') or []
                               if r.get('matched_effect_id') is None])
    return out


def apply_to_groups(data, cid, groups, *, scope=None):
    """把试点答案写入 ``build_card`` 产出的 groups（仅内存）；幂等，第二次 0 新增。"""
    require_scope(scope)
    report = dict(cid=cid, scope=scope, module_version=MODULE_VERSION,
                  status='OUT_OF_SCOPE', rows=[], added=0, skipped=0, conflicts=0,
                  rejected=0, excluded_fields=0)
    if cid not in PILOT_CIDS:
        report['detail'] = (f'cid={cid} 不在试点白名单 {PILOT_CIDS}：零新增'
                            '（保护卡/待补卡/type108 卡结构上不可达）')
        return report
    report['status'] = 'APPLIED'
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                rid = row.get('row_id')
                in_scope = rid in FROZEN_ROW_IDS.get(cid, set())
                if not in_scope:
                    continue
                result = evaluate(data, cid, row, scope=scope, skill=skill)
                entry = dict(row_id=rid, status=result['status'],
                             reason=result.get('reason'),
                             matched_effects=result.get('matched_effects'),
                             rejected=result.get('rejected'),
                             excluded_fields=result.get('excluded_fields'),
                             added=0, skipped=0, conflicts=0)
                if result['status'] == 'REJECTED':
                    report['rejected'] += 1
                    report['rows'].append(entry)
                    continue
                existing = row.setdefault('answers', [])
                for answer in result['answers']:
                    same = [a for a in existing
                            if a.get('rule_key') == answer.get('rule_key')
                            and a.get('field_path') == answer.get('field_path')]
                    if same:
                        if all(a.get('raw_value') == answer.get('raw_value') for a in same):
                            entry['skipped'] += 1
                            report['skipped'] += 1
                        else:
                            entry['conflicts'] += 1
                            report['conflicts'] += 1
                        continue
                    existing.append(answer)
                    entry['added'] += 1
                    report['added'] += 1
                entry['excluded_fields'] = result.get('excluded_fields')
                report['excluded_fields'] += len(result.get('excluded_fields') or [])
                report['rows'].append(entry)
    return report


def frozen_scope_dump():
    """机器可读冻结作用域（只含身份，不含数值）。"""
    return dict(module_version=MODULE_VERSION, scope=SCOPE,
                pilot_cids=list(PILOT_CIDS),
                zero_touch_cids=list(ZERO_TOUCH_CIDS),
                pending_cids=list(PENDING_CIDS),
                type108_unknown_cids=list(TYPE108_UNKNOWN_CIDS),
                forbidden_fields={str(k): list(v) for k, v in FORBIDDEN_FIELDS.items()},
                targets=[dict(t) for t in FROZEN_TARGETS])


def module_hashes(root):
    """模块与关键输入的 SHA-256（README/检查结果记录用）。"""
    root = Path(root)
    files = [Path(__file__), _HERE / 'effect_ledger.py', _HERE / 'card_page_data.py',
             _HERE / 'rules.py', root / 'output/character_skills/profiles/rules.json',
             root / SKILLLIST_REL, root / CHARAINFO_REL]
    return {str(p.relative_to(root)).replace('\\', '/') if p.is_relative_to(root)
            else p.name: sha256_file(p) for p in files}

# ============================================================================
# 全批候选层（C16-P1：49 项／23 卡／23 描述／23 载体）
# ============================================================================
#: 本层与试点层共用同一 ``SCOPE``；两层都不接线、不写正式产物。
BATCH_SCOPE = SCOPE
BATCH_MODULE_VERSION = MODULE_VERSION

#: Y.G. 23 项／15 卡（先完成；任务书 §2 核心成熟子集）。
YG_CIDS = (30204, 30206, 30221, 30224, 30225, 30230, 30234, 30244, 30246,
           30248, 30302, 30303, 30307, 30315, 30317)
#: 同域非 Y.G. 26 项／8 卡（Y.G. 完成且无新增机制/证据负担后才连带）。
NON_YG_CIDS = (20822, 6257, 20127, 20701, 20906, 20905, 20829, 20828)
BATCH_CIDS = YG_CIDS + NON_YG_CIDS

#: 冻结表只含身份（cid／row_id／effect_id／槽位／rule_key／句面主张）；
#: raw 与派生值一律由真实角色→父 skilllist→唯一 1095 子记录→字段→
#: ``rules.answer_for`` 重算，不保存、不导入交接实验数值。
YG_TARGETS = (
    _frozen(30204, '30204-ability-ability-skillid_1_-lvorder0-f0',
            '30204-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30248, '30248-ability-ability-skillid_1_-lvorder0-f2',
            '30248-ability-ability-skillid_1_-lvorder0-f2#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30248, '30248-ability-ability-skillid_1_-lvorder0-f2',
            '30248-ability-ability-skillid_1_-lvorder0-f2#e01', 'param5', 'skilllist|1095|/param5'),
    _frozen(30221, '30221-ability-ability-skillid_1_-lvorder0-f0',
            '30221-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30221, '30221-ability-ability-skillid_1_-lvorder0-f0',
            '30221-ability-ability-skillid_1_-lvorder0-f0#e01', 'param5', 'skilllist|1095|/param5'),
    _frozen(30302, '30302-ability-ability-skillid_1_-lvorder0-f0',
            '30302-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30303, '30303-ability-ability-skillid_1_-lvorder0-f0',
            '30303-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30303, '30303-ability-ability-skillid_1_-lvorder0-f0',
            '30303-ability-ability-skillid_1_-lvorder0-f0#e01', 'param5', 'skilllist|1095|/param5'),
    _frozen(30317, '30317-ability-ability-skillid_1_-lvorder0-f0',
            '30317-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30317, '30317-ability-ability-skillid_1_-lvorder0-f0',
            '30317-ability-ability-skillid_1_-lvorder0-f0#e01', 'param5', 'skilllist|1095|/param5'),
    _frozen(30206, '30206-ability-ability-skillid_1_-lvorder0-f0',
            '30206-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30244, '30244-ability-ability-skillid_1_-lvorder0-f0',
            '30244-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30307, '30307-ability-ability-skillid_1_-lvorder0-f0',
            '30307-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30315, '30315-ability-ability-skillid_1_-lvorder0-f0',
            '30315-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30224, '30224-ability-ability-skillid_1_-lvorder0-f0',
            '30224-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30246, '30246-ability-ability-skillid_1_-lvorder0-f2',
            '30246-ability-ability-skillid_1_-lvorder0-f2#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30246, '30246-ability-ability-skillid_1_-lvorder0-f2',
            '30246-ability-ability-skillid_1_-lvorder0-f2#e01', 'param5', 'skilllist|1095|/param5'),
    _frozen(30246, '30246-ability-ability-skillid_1_-lvorder0-f2',
            '30246-ability-ability-skillid_1_-lvorder0-f2#e02', 'param6', 'skilllist|1095|/param6'),
    _frozen(30230, '30230-ability-ability-skillid_1_-lvorder0-f0',
            '30230-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30225, '30225-ability-ability-skillid_1_-lvorder0-f0',
            '30225-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30225, '30225-ability-ability-skillid_1_-lvorder0-f0',
            '30225-ability-ability-skillid_1_-lvorder0-f0#e01', 'param5', 'skilllist|1095|/param5'),
    _frozen(30234, '30234-ability-ability-skillid_1_-lvorder0-f0',
            '30234-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(30234, '30234-ability-ability-skillid_1_-lvorder0-f0',
            '30234-ability-ability-skillid_1_-lvorder0-f0#e01', 'param5', 'skilllist|1095|/param5'),
)

NON_YG_TARGETS = (
    _frozen(20822, '20822-ability-ability-skillid_1_-lvorder0-f2',
            '20822-ability-ability-skillid_1_-lvorder0-f2#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20822, '20822-ability-ability-skillid_1_-lvorder0-f2',
            '20822-ability-ability-skillid_1_-lvorder0-f2#e01', 'param3', 'skilllist|1095|/param3'),
    _frozen(20822, '20822-ability-ability-skillid_1_-lvorder0-f2',
            '20822-ability-ability-skillid_1_-lvorder0-f2#e02', 'param2', 'skilllist|1095|/param2'),
    _frozen(20822, '20822-ability-ability-skillid_1_-lvorder0-f2',
            '20822-ability-ability-skillid_1_-lvorder0-f2#e03', 'param5', 'skilllist|1095|/param5'),
    _frozen(6257, '6257-ability-ability-skillid_1_-lvorder0-f1',
            '6257-ability-ability-skillid_1_-lvorder0-f1#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(6257, '6257-ability-ability-skillid_1_-lvorder0-f1',
            '6257-ability-ability-skillid_1_-lvorder0-f1#e01', 'param3', 'skilllist|1095|/param3'),
    _frozen(6257, '6257-ability-ability-skillid_1_-lvorder0-f1',
            '6257-ability-ability-skillid_1_-lvorder0-f1#e02', 'param2', 'skilllist|1095|/param2'),
    _frozen(20127, '20127-ability-ability-skillid_1_-lvorder0-f1',
            '20127-ability-ability-skillid_1_-lvorder0-f1#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20127, '20127-ability-ability-skillid_1_-lvorder0-f1',
            '20127-ability-ability-skillid_1_-lvorder0-f1#e01', 'param3', 'skilllist|1095|/param3'),
    _frozen(20127, '20127-ability-ability-skillid_1_-lvorder0-f1',
            '20127-ability-ability-skillid_1_-lvorder0-f1#e02', 'param2', 'skilllist|1095|/param2'),
    _frozen(20701, '20701-ability-ability-skillid_1_-lvorder0-f1',
            '20701-ability-ability-skillid_1_-lvorder0-f1#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20701, '20701-ability-ability-skillid_1_-lvorder0-f1',
            '20701-ability-ability-skillid_1_-lvorder0-f1#e01', 'param3', 'skilllist|1095|/param3'),
    _frozen(20701, '20701-ability-ability-skillid_1_-lvorder0-f1',
            '20701-ability-ability-skillid_1_-lvorder0-f1#e02', 'param2', 'skilllist|1095|/param2'),
    _frozen(20701, '20701-ability-ability-skillid_1_-lvorder0-f1',
            '20701-ability-ability-skillid_1_-lvorder0-f1#e03', 'param5', 'skilllist|1095|/param5'),
    _frozen(20906, '20906-ability-ability-skillid_1_-lvorder0-f1',
            '20906-ability-ability-skillid_1_-lvorder0-f1#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20906, '20906-ability-ability-skillid_1_-lvorder0-f1',
            '20906-ability-ability-skillid_1_-lvorder0-f1#e01', 'param3', 'skilllist|1095|/param3'),
    _frozen(20906, '20906-ability-ability-skillid_1_-lvorder0-f1',
            '20906-ability-ability-skillid_1_-lvorder0-f1#e02', 'param2', 'skilllist|1095|/param2'),
    _frozen(20906, '20906-ability-ability-skillid_1_-lvorder0-f1',
            '20906-ability-ability-skillid_1_-lvorder0-f1#e03', 'param5', 'skilllist|1095|/param5'),
    _frozen(20905, '20905-ability-ability-skillid_1_-lvorder0-f1',
            '20905-ability-ability-skillid_1_-lvorder0-f1#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20905, '20905-ability-ability-skillid_1_-lvorder0-f1',
            '20905-ability-ability-skillid_1_-lvorder0-f1#e01', 'param3', 'skilllist|1095|/param3'),
    _frozen(20905, '20905-ability-ability-skillid_1_-lvorder0-f1',
            '20905-ability-ability-skillid_1_-lvorder0-f1#e02', 'param2', 'skilllist|1095|/param2'),
    _frozen(20905, '20905-ability-ability-skillid_1_-lvorder0-f1',
            '20905-ability-ability-skillid_1_-lvorder0-f1#e03', 'param5', 'skilllist|1095|/param5'),
    _frozen(20829, '20829-ability-ability-skillid_1_-lvorder0-f0',
            '20829-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20829, '20829-ability-ability-skillid_1_-lvorder0-f0',
            '20829-ability-ability-skillid_1_-lvorder0-f0#e01', 'param5', 'skilllist|1095|/param5'),
    _frozen(20828, '20828-ability-ability-skillid_1_-lvorder0-f0',
            '20828-ability-ability-skillid_1_-lvorder0-f0#e00', 'param1', 'skilllist|1095|/param1'),
    _frozen(20828, '20828-ability-ability-skillid_1_-lvorder0-f0',
            '20828-ability-ability-skillid_1_-lvorder0-f0#e01', 'param5', 'skilllist|1095|/param5'),
)
BATCH_TARGETS = YG_TARGETS + NON_YG_TARGETS
BATCH_BY_ROW = {}
for _t in BATCH_TARGETS:
    BATCH_BY_ROW.setdefault((_t['cid'], _t['row_id']), []).append(_t)
BATCH_ROW_IDS = {cid: {rid for (c, rid) in BATCH_BY_ROW if c == cid} for cid in BATCH_CIDS}
TARGET_BY_EFFECT = {t['effect_id']: t for t in BATCH_TARGETS}

#: 4 项待补原始上游（20607；只登记身份，不产出数值）。
PENDING4_ITEMS = (
    dict(cid=20607, row_id='20607-ability-ability-skillid_1_-lvorder0-f1',
         effect_id='20607-ability-ability-skillid_1_-lvorder0-f1#e00', slot='param1'),
    dict(cid=20607, row_id='20607-ability-ability-skillid_1_-lvorder0-f1',
         effect_id='20607-ability-ability-skillid_1_-lvorder0-f1#e01', slot='param3'),
    dict(cid=20607, row_id='20607-ability-ability-skillid_1_-lvorder0-f1',
         effect_id='20607-ability-ability-skillid_1_-lvorder0-f1#e02', slot='param2'),
    dict(cid=20607, row_id='20607-ability-ability-skillid_1_-lvorder0-f1',
         effect_id='20607-ability-ability-skillid_1_-lvorder0-f1#e04', slot='param6'),
)
#: 8 项保留未知（20607 暴击率 1＋type108 回复 7；不补零、不借相邻类型）。
UNKNOWN8_ITEMS = (
    dict(cid=20607, row_id='20607-ability-ability-skillid_1_-lvorder0-f1',
         effect_id='20607-ability-ability-skillid_1_-lvorder0-f1#e03', slot='param5',
         kind='crit_rate_missing_param5'),
    dict(cid=350, row_id='350-special_move-special_move-pattern0-lvorder0-f3',
         effect_id='350-special_move-special_move-pattern0-lvorder0-f3#e00', slot=None,
         kind='type108'),
    dict(cid=30252, row_id='30252-special_move-special_move-pattern0-lvorder0-f2',
         effect_id='30252-special_move-special_move-pattern0-lvorder0-f2#e00', slot=None,
         kind='type108'),
    dict(cid=30214, row_id='30214-special_move-special_move-pattern0-lvorder0-f0',
         effect_id='30214-special_move-special_move-pattern0-lvorder0-f0#e00', slot=None,
         kind='type108'),
    dict(cid=20832, row_id='20832-special_move-special_move-pattern0-lvorder0-f2',
         effect_id='20832-special_move-special_move-pattern0-lvorder0-f2#e00', slot=None,
         kind='type108'),
    dict(cid=2323, row_id='2323-special_move-special_move-pattern1-lvorder1-f0',
         effect_id='2323-special_move-special_move-pattern1-lvorder1-f0#e00', slot=None,
         kind='type108'),
    dict(cid=13228, row_id='13228-special_move-special_move-pattern0-lvorder0-f2',
         effect_id='13228-special_move-special_move-pattern0-lvorder0-f2#e00', slot=None,
         kind='type108'),
    dict(cid=343, row_id='343-special_move-special_move-pattern0-lvorder0-f3',
         effect_id='343-special_move-special_move-pattern0-lvorder0-f3#e00', slot=None,
         kind='type108'),
)

#: 1095 五种已有规则键的槽位；批内不新增。
BATCH_SLOTS = ('param1', 'param2', 'param3', 'param5', 'param6')
#: 载体上需检查的全部槽位（param4／param7 无 1095 规则，只登记排除）。
CARRIER_SLOTS = ('param1', 'param2', 'param3', 'param4', 'param5', 'param6', 'param7')
#: 中性值（既有规则口径：p1/p2/p3 中性 1；p5 缺席/0 为中性；p6 中性 1.5；
#: p4 未推广；p7 语义未知，不判中性）。
NEUTRAL_VALUES = {'param1': 1.0, 'param2': 1.0, 'param3': 1.0, 'param4': 1.0,
                  'param5': 0.0, 'param6': 1.5}
UNIT_FOR_SLOT = {
    'param1': '攻击倍率（无量纲）；本项增加以百分比表示',
    'param2': '移动速度倍率；本项增加以百分比表示',
    'param3': '受伤量倍率（无量纲）；本项减伤以百分比表示，不是固定防御值',
    'param5': '暴击概率百分点（对 0 的加算增量）',
    'param6': '暴击伤害系数增量（在 1.5 基准上的加算）',
}

#: 全批作用域不包含的负面卡：20607 待补；type108 七卡未知；四张保护卡零新增。
BATCH_NEGATIVE_CIDS = (20607, 350, 30252, 30214, 20832, 2323, 13228, 343,
                       30236, 30239, 30102, 20234)


def batch_tier(cid):
    if cid in YG_CIDS:
        return 'YG'
    if cid in NON_YG_CIDS:
        return 'NON_YG'
    return None


def normalized_value(slot, raw):
    """既有 ``rules.json`` conversion 的归一化表达（仅回归比对/展示，不新增公式）。"""
    if slot in ('param1', 'param2'):
        return round((float(raw) - 1.0) * 100, 6)
    if slot == 'param3':
        return round((1.0 - float(raw)) * 100, 6)
    if slot == 'param5':
        return round(float(raw) * 100, 6)
    if slot == 'param6':
        return round(float(raw) - 1.5, 6)
    raise ValueError(f'无既有归一化定义的 1095 槽位：{slot!r}')


def player_sentence_batch(slot, raw):
    """全批玩家可读中文（§1.3）：对象／量／基准／条件／未解边界；默认层不用内部术语。"""
    if slot == 'param1':
        pct = (float(raw) - 1.0) * 100
        return (f'自身攻击力提高 {percent_text(pct)}%（本能力单独生效时攻击力变为 '
                f'{num_text(raw)} 倍；不含其他来源与后续条件强化，最终数值未实机验证）')
    if slot == 'param2':
        pct = (float(raw) - 1.0) * 100
        return (f'自身移动速度提高 {percent_text(pct)}%（本能力单独生效时移动速度变为 '
                f'{num_text(raw)} 倍；不含地形等其他来源）')
    if slot == 'param3':
        pct = (1.0 - float(raw)) * 100
        return (f'自身受到的伤害减少 {percent_text(pct)}%（本能力单独生效时受到的伤害变为 '
                f'{num_text(raw)} 倍；这是按比例减伤，不是固定防御值；最终数值未实机验证）')
    if slot == 'param5':
        return (f'自身暴击率提高 {percent_text(float(raw) * 100)} 个百分点'
                '（本能力单独生效时直接加算；不等于最终暴击率）')
    if slot == 'param6':
        delta = float(raw) - 1.5
        return (f'自身暴击伤害系数提高 {percent_text(delta)}'
                '（在 1.5 基准系数之上加算；不是相对现有伤害的百分比）')
    raise ValueError(f'未定义的 1095 槽位：{slot!r}')


def _is_neutral(slot, value):
    if slot not in NEUTRAL_VALUES:
        return None
    try:
        return abs(float(value) - NEUTRAL_VALUES[slot]) < 1e-9
    except (TypeError, ValueError):
        return None


def collect_exclusions(chain, claimed_slots):
    """句面未主张的载体槽位：只登记，不产出答案（存在≠归属）。

    中性值（p1/p2/p3=1、p5=0、p6=1.5）与真正未主张的活性值分开登记；
    param4／param7 没有 1095 规则，按“未分配槽”登记为未主张。
    """
    record = chain['carrier']['record']
    out = []
    for slot in CARRIER_SLOTS:
        if slot in claimed_slots:
            continue
        state = raw_state(record, slot)
        raw = record.get(slot)
        neutral = _is_neutral(slot, raw) if state == 'present' else None
        if state in ('missing', 'null'):
            code = 'EXCLUDED_FIELD_ABSENT'
            detail = '载体无该字段（缺席＝不产出，不补零）'
        elif state == 'zero':
            code = 'EXCLUDED_FIELD_NEUTRAL' if neutral else 'EXCLUDED_FIELD_ZERO'
            detail = '载体存 0；不当作答案（不补零、不借相邻类型）'
        elif state == 'present' and neutral is True:
            code = 'EXCLUDED_FIELD_NEUTRAL'
            detail = '载体为该槽中性值，本句亦未主张：不产出'
        elif slot in ('param4', 'param7'):
            code = 'EXCLUDED_FIELD_NOT_CLAIMED'
            detail = '该槽不在 1095 既有五键规则内，且本句未主张：只登记不解释'
        else:
            code = 'EXCLUDED_FIELD_NOT_CLAIMED'
            detail = ('载体存在非中性值，但本片段句面无对应主张：不并入基础句'
                      '（存在≠归属；可能属同父记录其他句子，不跨句取数）')
        out.append(dict(slot=slot, state=state, raw_value=raw, neutral=neutral,
                        code=code, detail=detail))
    return out


def _competition_block(chain, data):
    """竞争载体：记录父 sub[] 全部记录与相关字段，证明只消费 ability=1095。"""
    raw = raw_tables(data.root)['skilllist']
    subs = []
    for sub in chain['sub_abilities']:
        rec = raw[sub['index']]
        subs.append(dict(skillid=sub['skillid'], ability=sub['ability'], index=sub['index'],
                         json_pointer=f'/skilllist/{sub["index"]}',
                         relevant_fields={s: rec.get(s) for s in CARRIER_SLOTS if s in rec}))
    others = [s for s in subs if s['ability'] != CARRIER_ABILITY]
    return dict(carrier_ability=CARRIER_ABILITY,
                carrier_count=sum(1 for s in subs if s['ability'] == CARRIER_ABILITY),
                sub_records=subs,
                other_carriers=others,
                note=('同父 sub[] 中仅 ability=1095 记录被本模块消费；其他 ability 记录'
                      '（含同样带 param 字段者）只登记为竞争载体，不借用其数值或公式'))


def _source_block_batch(chain, slot, data):
    carrier = chain['carrier']
    parent = raw_tables(data.root)['skilllist'][chain['parent']['index']]
    block = _source_block(chain, slot)
    block.update({
        'parent_text': parent.get('text'),
        'competition': _competition_block(chain, data),
        'row_fragment_index': chain['fragment'].get('fragment_index'),
        'carrier_ability': CARRIER_ABILITY,
    })
    return block


def build_answer_batch(chain, target, data):
    """按冻结 target 构造全批答案；字段缺失/零/规则缺失 → ``(None, reason)``。"""
    slot = target['slot']
    carrier = chain['carrier']['record']
    state = chain['field_states'].get(slot)
    if state != 'present':
        return None, dict(code='FIELD_' + state.upper(),
                          detail=f'1095 载体 skillid={chain["carrier"]["record_id"]} 字段 /{slot} '
                                 f'状态={state}：不补零、不借相邻记录')
    raw = carrier[slot]
    rule = R.answer_for('skilllist', CARRIER_ABILITY, '/' + slot, raw, carrier,
                        source_layer='CACHE')
    if not rule:
        return None, dict(code='RULE_MISSING',
                          detail=f'rules.answer_for 未返回 skilllist|1095|/{slot}')
    conditions = [
        '接受者自身已装载该能力，且对应能力列表/类型分派（能力编号 1095）通过时生效',
        '仅本项单一记录贡献；不含其他来源、后续条件强化与最终叠加',
        '本条来自 CACHE 静态记录；运行时装载与资格未实机验证',
    ]
    unknowns = [
        '运行时实际装载与资格未核实（未实机）',
        '与其他来源的实际叠加与最终战斗数值未验证',
        '本句面到该能力记录字段的归属为推断，不当作完全确认',
    ]
    if slot == 'param5':
        unknowns.append('不等于最终暴击率；同类上限与其他来源另论')
    if slot == 'param6':
        unknowns.append('最终暴击伤害与扣血未验证；基准 1.5 之上的加算不等于相对现有伤害的百分比')
    answer = {
        'value': rule.get('value_text'),
        'normalized_value': normalized_value(slot, raw),
        'player_text': player_sentence_batch(slot, raw),
        'player_scope': {
            'object': '自身（接受者）',
            'quantity': rule.get('quantity_kind'),
            'unit': UNIT_FOR_SLOT[slot],
            'conditions': conditions,
            'duration': '本句未涉及持续时间；句外条件强化与时限未纳入本项',
            'unknowns': unknowns,
        },
        'quantity_kind': rule.get('quantity_kind'),
        'unit': UNIT_FOR_SLOT[slot],
        'rule_unit': rule.get('unit'),
        'raw_value': raw,
        'field_path': '/' + slot,
        'numeric_source': ('既有已确认规则（profiles/rules.json 的 skilllist|1095|/' + slot +
                           '＋ordinary_effects/ability1095）＋CACHE skilllist 原始记录'),
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'answer_status': rule.get('answer_status'),
        'evidence_scope': SCOPE,
        'rule_key': target['rule_key'],
        'table': 'skilllist',
        'record_id': chain['carrier']['record_id'],
        'layer': 'CACHE',
        'target': rule.get('target'),
        'conversion': rule.get('conversion'),
        'base_definition': rule.get('base_definition'),
        'conditions': '；'.join(conditions),
        'rule_applicability': rule.get('conditions'),
        'rule_limits': rule.get('rule_limits'),
        'rule_status': rule.get('rule_status'),
        'original_text': chain['fragment'].get('japanese'),
        'source': _source_block_batch(chain, slot, data),
        'binding': {'c16_p1_1095_partial_binding': {
            'scope': SCOPE,
            'tier': batch_tier(target['cid']),
            'row_id': target['row_id'],
            'effect_id': target['effect_id'],
            'claim': target['claim'],
            'slot': slot,
            'rule_key': target['rule_key'],
            'carrier_table': 'skilllist',
            'carrier_record_id': chain['carrier']['record_id'],
            'carrier_layer': 'CACHE',
            'carrier_slot': f'sub[{chain["carrier_slot"]}]',
            'parent_record_id': chain['parent']['record_id'],
            'charainfo_record_id': chain['cid'],
            'raw_value': raw,
            'binding': 'inferred',
            'runtime_verified': False,
        }},
        'details': rule,
    }
    return answer, None


def evaluate_batch(data, cid, row, *, scope=None, skill=None):
    """全批单行解析（不写入）。``scope`` 缺省/错误 → ``ScopeError``。"""
    require_scope(scope)
    out = dict(cid=cid, row_id=row.get('row_id'), scope=scope,
               module_version=BATCH_MODULE_VERSION, tier=batch_tier(cid),
               answers=[], rejected=[], excluded_fields=[], matched_effects=[],
               missing_targets=[], competition=None)
    chain = resolve_chain(data, cid, row, skill=skill)
    out['chain'] = dict(status=chain['status'], reason=chain.get('reason'),
                        detail=chain.get('detail'), gates=chain.get('gates') or [],
                        carrier=(None if chain['status'] != 'RESOLVED' else dict(
                            record_id=chain['carrier']['record_id'],
                            index=chain['carrier']['index'],
                            carrier_slot=chain['carrier_slot'],
                            parent_record_id=chain['parent']['record_id'],
                            parent_index=chain['parent']['index'])),
                        field_states=chain.get('field_states'))
    if chain['status'] != 'RESOLVED':
        out['status'] = 'REJECTED'
        out['reason'] = chain.get('reason')
        return out

    targets = BATCH_BY_ROW.get((cid, row.get('row_id')))
    if not targets:
        out['status'] = 'ROW_OUT_OF_SCOPE'
        out['reason'] = 'ROW_NOT_IN_FROZEN_SCOPE'
        return out

    out['competition'] = _competition_block(chain, data)
    analysis = LEDGER.analyze_row(row, table='skilllist')
    effects = [e for e in analysis.get('effects') or []
               if e.get('record_type') == 'effect' and '#e' in e.get('effect_id', '')]
    by_id = {e['effect_id']: e for e in effects}

    for t in targets:
        effect = by_id.get(t['effect_id'])
        if effect is None:
            out['missing_targets'].append(dict(effect_id=t['effect_id'],
                                               detail='该 effect_id 未出现在当前解析结果'))
            continue
        claim_ok = effect.get('effect_type') == t['claim']
        out['matched_effects'].append(dict(
            effect_id=t['effect_id'], effect_type=effect.get('effect_type'),
            direction=effect.get('direction'), status_before=effect.get('status'),
            claim_expected=t['claim'], claim_matches=claim_ok))
        if not claim_ok:
            out['rejected'].append(dict(effect_id=t['effect_id'], slot=t['slot'],
                                        code='CLAIM_MISMATCH',
                                        detail=f'行内 effect 类型 {effect.get("effect_type")!r} '
                                               f'与冻结主张 {t["claim"]!r} 不符'))
            continue
        answer, why = build_answer_batch(chain, t, data)
        if answer is None:
            out['rejected'].append(dict(effect_id=t['effect_id'], slot=t['slot'], **why))
            continue
        out['answers'].append(answer)

    claimed_slots = {t['slot'] for t in targets}
    out['excluded_fields'] = collect_exclusions(chain, claimed_slots)
    out['status'] = ('RESOLVED_ALL' if len(out['answers']) == len(targets)
                     else 'RESOLVED_PARTIAL')
    out['effect_ids'] = sorted(t['effect_id'] for t in targets)
    out['analysis_summary'] = dict(
        effect_status=[dict(effect_id=e['effect_id'], effect_type=e['effect_type'],
                            status=e['status']) for e in effects],
        split_flags=analysis.get('split_flags'),
        unmatched_answer_refs=[r for r in analysis.get('answer_refs') or []
                               if r.get('matched_effect_id') is None])
    return out


def apply_batch_to_groups(data, cid, groups, *, scope=None):
    """把全批答案写入 ``build_card`` 产出的 groups（仅内存）；幂等。"""
    require_scope(scope)
    report = dict(cid=cid, scope=scope, module_version=BATCH_MODULE_VERSION,
                  tier=batch_tier(cid), status='OUT_OF_SCOPE', rows=[], added=0,
                  skipped=0, conflicts=0, rejected=0, excluded_fields=0)
    if cid not in BATCH_CIDS:
        report['detail'] = (f'cid={cid} 不在全批白名单：零新增'
                            '（待补卡/type108 卡/保护卡结构上不可达）')
        return report
    report['status'] = 'APPLIED'
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                rid = row.get('row_id')
                if rid not in BATCH_ROW_IDS.get(cid, set()):
                    continue
                result = evaluate_batch(data, cid, row, scope=scope, skill=skill)
                entry = dict(row_id=rid, status=result['status'],
                             reason=result.get('reason'),
                             matched_effects=result.get('matched_effects'),
                             rejected=result.get('rejected'),
                             excluded_fields=result.get('excluded_fields'),
                             added=0, skipped=0, conflicts=0)
                if result['status'] == 'REJECTED':
                    report['rejected'] += 1
                    report['rows'].append(entry)
                    continue
                existing = row.setdefault('answers', [])
                for answer in result['answers']:
                    same = [a for a in existing
                            if a.get('rule_key') == answer.get('rule_key')
                            and a.get('field_path') == answer.get('field_path')]
                    if same:
                        if all(a.get('raw_value') == answer.get('raw_value') for a in same):
                            entry['skipped'] += 1
                            report['skipped'] += 1
                        else:
                            entry['conflicts'] += 1
                            report['conflicts'] += 1
                        continue
                    existing.append(answer)
                    entry['added'] += 1
                    report['added'] += 1
                entry['excluded_fields'] = result.get('excluded_fields')
                report['excluded_fields'] += len(result.get('excluded_fields') or [])
                report['rows'].append(entry)
    return report


def batch_scope_dump():
    """机器可读全批冻结作用域（只含身份，不含 raw／value）。"""
    return dict(module_version=BATCH_MODULE_VERSION, scope=BATCH_SCOPE,
                yg_cids=list(YG_CIDS), non_yg_cids=list(NON_YG_CIDS),
                batch_cids=list(BATCH_CIDS),
                counts=dict(yg=len(YG_TARGETS), non_yg=len(NON_YG_TARGETS),
                            total=len(BATCH_TARGETS), cids=len(BATCH_CIDS),
                            rows=len(BATCH_BY_ROW)),
                pending_raw_upstream=[dict(i) for i in PENDING4_ITEMS],
                unknown_retained=[dict(i) for i in UNKNOWN8_ITEMS],
                negative_cids=list(BATCH_NEGATIVE_CIDS),
                targets=[dict(t) for t in BATCH_TARGETS])
