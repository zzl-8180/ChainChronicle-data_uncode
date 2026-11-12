# -*- coding: utf-8 -*-
"""C18-P1 ``skilllist`` ability 1095 **仅攻击部分绑定**——2 项非 Y.G. 同类外推候选（**未接线**）。

任务卡 ``docs/tasks/20261106-c18-p1-1095-attack-partial.md``；C18 周期卡
``docs/tasks/20261106-c18-cycle.md``；方法 ``docs/角色技能完整解读实施方案.md`` §1.3／§1.6。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；
``rules.json``／``rules.py``／``effect_ledger.py``／C16／C17 模块／正式 ``pages``／账本均未改动；
本阶段不运行正式全库生成或 resume。模块只读当前快照解码 JSON、``profiles/rules.json``，
并由调用方传入真实 ``card_page_data.Inputs`` 与页面行对象（``build_card`` 产物）。

作用域（严格 2 个非 Y.G. effect，全部 slot=``/param1``）
=====================================================  ======================================================  ======  ==========
cid                                                     row_id                                                  effect  句面
=====================================================  ======================================================  ======  ==========
6341                                                    ``6341-ability-ability-skillid_1_-lvorder0-f0``         #e00    攻撃力
20333                                                   ``20333-ability-ability-skillid_1_-lvorder0-f0``        #e00    攻撃力
=====================================================  ======================================================  ======  ==========

**冻结表只含身份**（cid／row_id／effect_id／槽／主张／rule_key／句面原文／句外线索／排除槽名）。
本模块不保存、不导入任何预筛 raw 或载体 ID；raw 与派生值一律由
「真实角色 → 父 skilllist → 唯一 1095 子记录 → 字段 → ``rules.answer_for``」重算。
任务卡与预筛清单给出的载体 ID、载体原值与额外槽原值，只在 ``check_candidate.py``
**计算之后**作回归比对；本模块的源码与运行期都不读取、不命名、不导入这些数值。

逐行硬门（任一不符即拒绝，不猜、不取邻近记录、不补零）
------------------------------------------------------
R1  **角色上游**：``charainfo[cid]`` 在 CACHE 解码表唯一存在。
R2  **角色身份**：行 ``cid`` 与调用 cid 相同。
R3  **引用形态**：行 ``group == 'ability'`` 且 ``reference_field`` 恰为 ``skillid[n]``。
R4  **槽位**：``charainfo.skillid[n]`` 存在（不越界）。
R5  **父记录唯一**：该 skillid 在 CACHE ``skilllist`` 全表恰出现 1 次；``Inputs`` 记录与原文逐值相同。
R6  **行来源指针**：行 ``source.json_pointer == /skilllist/<父下标>`` 且字段指针为 ``.../text``。
R7  **片段归属**：行日语（NFKC、去空白）在父 ``text`` 中恰出现 1 次。
R8  **子记录唯一**：父 ``sub[]`` 每个 skillid 全表唯一命中，且 ``Inputs`` 记录与原文相同。
R9  **载体唯一**：``sub[]`` 中 ``ability == 1095`` 的记录恰 1 条（按真实下标解引用）。
R10 **字段解引用**：只取冻结槽位 ``/param1``；``missing／null／非有限／负值／真零`` 分别登记且都不出答案。
R11 **规则复用**：只调用 ``rules.answer_for('skilllist', 1095, '/param1', raw, 载体, source_layer='CACHE')``；
    不新增公式、不新增规则键。
R12 **本句范围**：行日语与冻结句面逐字相同（NFKC 去空白），且载体 ``/param1`` 状态为 present；
    载体上 ``/param6`` 等非主张槽只登记排除，**不得并入**本句。
R13 **句外线索**：冻结的句外条件线索必须在父 ``text`` 中出现、且**不得**出现在本行日语中
    （证明“句外条件强化”确实在句外，且未被本句吸收）。

**部分绑定边界**：两项载体均带非中性 ``param6``（不等于中性 1.5），但本行句面只有“攻撃力が上がる”，
因此 ``param6`` 登记为 ``EXCLUDED_FIELD_NOT_CLAIMED``，**不并入**；这不是删除旧 P4，也不是放宽
B11／B12／B14，本模块不 import、不引用、不改动这三者与旧 P4 模块，也不复用或改动 C17 模块。
句外其他效果（其他友方在场增强、必杀技玛娜减少、攻击计数获玛娜、追击、敌方减益、
暴击／反击等）只披露、不并入。

证据分档（不得升格）
--------------------
R1–R13 与字段原值为结构／原值证据；句面主张→该 1095 子记录字段的归属为**推断**。答案写
``numeric_evidence='确认'``（既有静态及受控原生局部规则＋CACHE 原始记录）、
``association_evidence='推断'``、``binding='inferred'``、``runtime_verified=False``、
``evidence_scope=SCOPE``。这是“既有规则体与当前原值已确认”，不是完整语义确认，也不是实机确认。

明确不处理
----------
* 额外 ``param6``（各载体原值）与同段其他句子的条件强化：只披露、不并入。
* 其他机制族、其他 1095 载体、其他槽位（p2／p3／p5／p6）、type108、新原生、实机、新缓存。
* 精确同句但未通过链门的 9 项（``NEGATIVE_SAME_SENTENCE_ITEMS``）：缺 CACHE 上游或缺唯一
  1095 载体，一律拒绝，不强行做成答案。
"""
from __future__ import annotations

import sys
from pathlib import Path
from project_layout_paths import read_path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:            # 允许从任意工作目录直接导入
    sys.path.insert(0, str(_HERE))

import effect_ledger as LEDGER                       # 只读：真实消费者
import rules as R                                    # 只读：既有规则与公式
import card_page_inference_c16_p1_1095_partial as C16  # 只读：已审查的真实链解析复用

MODULE_VERSION = 'c18_p1_1095_attack_partial_20261106'
#: 本作用域（缺省／错误 scope 一律硬拒绝；见 ``ScopeError``）。
SCOPE = 'C18_P1_1095_ATTACK_PARTIAL_20261106'
CARRIER_ABILITY = 1095
SLOT = 'param1'
RULE_KEY = 'skilllist|1095|/param1'
CLAIM = '攻撃力'
SENTENCE_ZH = '攻击力上升'
DECODED_REL = C16.DECODED_REL
SKILLLIST_REL = C16.SKILLLIST_REL
CHARAINFO_REL = C16.CHARAINFO_REL
RESOLVED_EXACT = C16.RESOLVED_EXACT
UNIT = '攻击倍率（无量纲）；本项增加以百分比表示'

#: 已审查的 C16 模块哈希（C16 独立审查对象的模块版本）。本模块只读复用它，
#: 若该文件变化，``check_candidate.py`` 会失败而不是静默沿用旧结论。
C16_MODULE_SHA256 = 'd03fa45c451c364e58f4c27bdf5dbed1cc41b2914f3ebae90d8172ff4bff679a'


def _target(cid, row_id, effect_id, sentence, cues, summary, excluded=('param6',)):
    return dict(cid=cid, row_id=row_id, effect_id=effect_id, slot=SLOT, claim=CLAIM,
                rule_key=RULE_KEY, sentence=sentence,
                out_of_sentence_cues=tuple(cues),
                out_of_sentence_summary=summary,
                excluded_slots=tuple(excluded))


#: 2 项非 Y.G. effect 冻结身份。``sentence`` 是行日语原文；``out_of_sentence_summary``
#: 只是同段其他句子的可读归纳，其每条 ``out_of_sentence_cues`` 由 R13 逐条验证确实在父文
#: 且不在本行。
TARGETS = (
    _target(
        6341, '6341-ability-ability-skillid_1_-lvorder0-f0',
        '6341-ability-ability-skillid_1_-lvorder0-f0#e00',
        '攻撃力が上がる。',
        ('戦場に自身以外の味方がいる', '必殺技を発動する時に必要なマナが2つ減る',
         '弾き飛ばなくなり', '接触範囲攻撃', 'クリティカル攻撃時', 'カウンター'),
        '其他友方在场时效果增强、必杀技玛娜减少2、抗击退与范围普攻、暴击攻击与反击'),
    _target(
        20333, '20333-ability-ability-skillid_1_-lvorder0-f0',
        '20333-ability-ability-skillid_1_-lvorder0-f0#e00',
        '攻撃力が上がる。',
        ('攻撃を250回当てるたび', 'マナを1つ獲得する', '追撃効果',
         '攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる', 'クリティカル攻撃時', '範囲攻撃になる'),
        '攻击250次获得玛娜、追击效果、敌方减益、暴击攻击与范围攻击'),
)

TARGET_CIDS = tuple(t['cid'] for t in TARGETS)
BY_ROW = {(t['cid'], t['row_id']): t for t in TARGETS}
BY_EFFECT = {t['effect_id']: t for t in TARGETS}
TARGET_ROW_IDS = {cid: {t['row_id'] for t in TARGETS if t['cid'] == cid} for cid in TARGET_CIDS}

#: 明确拒绝的邻近集合（结构上不可达，零新增）：C17 已交付三卡（旧答案须保持）、
#: C16 同族卡、保护卡、以及 20607 待补卡。本模块不认领其中任何 effect。
NEGATIVE_CIDS = (30110, 30237, 30333, 30246, 20822, 30236, 30239, 30102, 20234, 20607)

#: 精确同句（「攻撃力が上がる。」）但**未通过链门**的 9 项：只登记身份与预期拒绝码，
#: 不产出任何答案。``expected_reject`` 由 ``check_candidate.py`` 用只读的
#: ``C16.resolve_chain`` 独立复核；``evaluate``／``apply_to_groups`` 对这些行返回
#: ``ROW_OUT_OF_SCOPE``／``OUT_OF_SCOPE``、+0。
NEGATIVE_SAME_SENTENCE_ITEMS = (
    dict(cid=1063, row_id='1063-ability-ability-skillid_1_-lvorder0-f1',
         expected_reject='R1_CHARAINFO_RECORD_MISSING',
         note='CACHE charainfo 无该 cid：原始角色上游缺失'),
    dict(cid=1238, row_id='1238-ability-ability-skillid_2_-lvorder1-f0',
         expected_reject='R1_CHARAINFO_RECORD_MISSING',
         note='CACHE charainfo 无该 cid：原始角色上游缺失'),
    dict(cid=12220, row_id='12220-ability-ability-skillid_1_-lvorder0-f0',
         expected_reject='R1_CHARAINFO_RECORD_MISSING',
         note='CACHE charainfo 无该 cid：原始角色上游缺失'),
    dict(cid=2329, row_id='2329-ability-ability-skillid_1_-lvorder0-f0',
         expected_reject='R9_CARRIER_1095_NOT_UNIQUE',
         note='父 sub[] 中 ability=1095 记录 0 条：无载体，不借邻近记录'),
    dict(cid=7611, row_id='7611-ability-ability-skillid_1_-lvorder0-f0',
         expected_reject='R9_CARRIER_1095_NOT_UNIQUE',
         note='父 sub[] 中 ability=1095 记录 0 条：无载体，不借邻近记录'),
    dict(cid=7612, row_id='7612-ability-ability-skillid_1_-lvorder0-f0',
         expected_reject='R9_CARRIER_1095_NOT_UNIQUE',
         note='父 sub[] 中 ability=1095 记录 0 条：无载体，不借邻近记录'),
    dict(cid=7687, row_id='7687-ability-ability-skillid_1_-lvorder0-f0',
         expected_reject='R9_CARRIER_1095_NOT_UNIQUE',
         note='父 sub[] 中 ability=1095 记录 0 条：无载体，不借邻近记录'),
    dict(cid=20838, row_id='20838-ability-ability-skillid_1_-lvorder0-f0',
         expected_reject='R9_CARRIER_1095_NOT_UNIQUE',
         note='父 sub[] 中 ability=1095 记录 0 条：无载体，不借邻近记录'),
    dict(cid=30263, row_id='30263-ability-ability-skillid_1_-lvorder0-f0',
         expected_reject='R9_CARRIER_1095_NOT_UNIQUE',
         note='父 sub[] 中 ability=1095 记录 0 条：无载体，不借邻近记录'),
)


class ScopeError(RuntimeError):
    """缺省／错误 scope——硬拒绝，不做默认回退。"""


def require_scope(scope):
    if scope is None:
        raise ScopeError(f'缺少 scope 参数：必须显式传入 {SCOPE!r}（不设默认值）')
    if scope != SCOPE:
        raise ScopeError(f'scope 不符：收到 {scope!r}，本模块只接受 {SCOPE!r}')


# ---------------------------------------------------------------- 文本／数值小工具（只读）
canon = C16.canon
raw_state = C16.raw_state
num_text = C16.num_text
percent_text = C16.percent_text
sha256_file = C16.sha256_file
raw_tables = C16.raw_tables


# ---------------------------------------------------------------- 链解析（R1–R13）
def _gate(gates, code, ok, detail, **extra):
    gates.append(dict(code=code, ok=bool(ok), detail=detail, **extra))
    return bool(ok)


def _reject(gates, code, detail, **extra):
    _gate(gates, code, False, detail, **extra)
    return dict(status='REJECTED', reason=code, detail=detail, gates=gates)


def resolve_chain(data, cid, row, skill=None, target=None):
    """真实角色→父 skilllist→唯一 1095 子记录，并施加 C18 的 R12／R13 本句范围门。

    R1–R11 直接复用已审查的 C16 真实链解析（同一 ``Inputs``、同一解码原文、同一唯一性判据），
    本模块不复制一套解析逻辑，也不放宽任何既有门。
    """
    chain = C16.resolve_chain(data, cid, row, skill=skill)
    if chain['status'] != 'RESOLVED':
        return chain
    gates = list(chain.get('gates') or [])
    tgt = target if target is not None else BY_ROW.get((cid, row.get('row_id')))
    if tgt is None:
        return _reject(gates, 'R12_ROW_NOT_IN_SCOPE',
                       f'行 {row.get("row_id")!r} 不在 C18-P1 冻结表内')

    # R12-a 行日语与冻结句面逐字相同（不按同文跨行认领）
    frag = canon(row.get('japanese'))
    if frag != canon(tgt['sentence']):
        return _reject(gates, 'R12_SENTENCE_MISMATCH',
                       f'行日语 {row.get("japanese")!r} 与冻结句面 {tgt["sentence"]!r} 不相同')
    _gate(gates, 'R12_SENTENCE_MISMATCH', True, '行日语与冻结句面逐字相同（NFKC 去空白）')

    # R12-b 只认领 /param1；其他槽（含 param6）只登记排除
    states = chain['field_states']
    if states.get(tgt['slot']) != 'present':
        return _reject(gates, 'R12_CLAIM_SLOT_NOT_PRESENT',
                       f'载体 /{tgt["slot"]} 状态={states.get(tgt["slot"])}：不补零、不借相邻记录')
    extra = {}
    for slot in tgt['excluded_slots']:
        extra[slot] = dict(state=states.get(slot), raw_value=chain['carrier']['record'].get(slot))
    _gate(gates, 'R12_CLAIM_SLOT_NOT_PRESENT', True,
          f'载体 /{tgt["slot"]} 状态=present；本句不主张槽 {sorted(extra)} 只登记排除',
          excluded_extra=extra)

    # R13 句外线索：必须在父文出现、且不在本行
    parent = raw_tables(data.root)['skilllist'][chain['parent']['index']]
    parent_text = canon(parent.get('text'))
    cue_rows = []
    ok_cues = True
    for cue in tgt['out_of_sentence_cues']:
        cue_c = canon(cue)
        in_parent = bool(cue_c) and cue_c in parent_text
        in_frag = cue_c in frag
        ok_cues &= in_parent and not in_frag
        cue_rows.append(dict(cue=cue, in_parent_text=in_parent, in_row_fragment=in_frag))
    if not ok_cues:
        return _reject(gates, 'R13_OUT_OF_SENTENCE_CUE_UNVERIFIED',
                       '句外条件线索未在父文出现或出现在本行内：披露与句面边界不一致',
                       cues=cue_rows)
    _gate(gates, 'R13_OUT_OF_SENTENCE_CUE_UNVERIFIED', True,
          f'{len(cue_rows)} 条句外线索均在父文、均不在本行（句外条件强化未并入）',
          cues=cue_rows)

    out = dict(chain)
    out['gates'] = gates
    out['c18'] = dict(sentence=tgt['sentence'],
                      out_of_sentence=cue_rows,
                      out_of_sentence_summary=tgt['out_of_sentence_summary'],
                      extra_slots=extra,
                      parent_text=parent.get('text'))
    return out


# ---------------------------------------------------------------- 答案构造（R10/R11/R12）
def _source_block(chain, slot, data):
    block = C16._source_block(chain, slot)
    block.update({
        'parent_text': chain['c18']['parent_text'],
        'row_sentence': chain['c18']['sentence'],
        'carrier_ability': CARRIER_ABILITY,
        'competition': C16._competition_block(chain, data),
        'source_resolution': RESOLVED_EXACT,
    })
    return block


def player_sentence(raw, target):
    """玩家可读中文（§1.3）：对象／量／基准／条件／句外未并入部分／未解边界。

    默认层不使用 param／载体／槽位／delta／floor 等内部术语充当答案。
    """
    pct = (float(raw) - 1.0) * 100
    return (f'自身攻击力提高 {percent_text(pct)}%'
            f'（本能力单独生效时攻击力变为 {num_text(raw)} 倍）。'
            f'本项只对应「{SENTENCE_ZH}」这一句；同一能力描述中其他句子写的其他效果'
            f'（{target["out_of_sentence_summary"]}）不并入本项；最终数值未实机验证。')


def build_answer(chain, target, data):
    """按冻结 target 构造单条答案；字段缺失/零/规则缺失 → ``(None, reason)``。"""
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
        '仅本项单一记录、单一槽位的局部贡献；不含同段描述其他句子与其他来源',
        '本条来自 CACHE 静态记录；运行时装载与资格未实机验证',
    ]
    unknowns = [
        '运行时实际装载与资格未核实（未实机）',
        '与其他来源的实际叠加与最终战斗数值未验证',
        '本句面到该能力记录该槽位的归属为推断，不当作完整语义确认',
        f'同段其他句子的条件强化（{target["out_of_sentence_summary"]}）未并入本项，其数值另论',
    ]
    excluded = C16.collect_exclusions(chain, {slot})
    answer = {
        'value': rule.get('value_text'),
        'normalized_value': C16.normalized_value(slot, raw),
        'player_text': player_sentence(raw, target),
        'player_scope': {
            'object': '自身（接受者）',
            'quantity': rule.get('quantity_kind'),
            'unit': UNIT,
            'conditions': conditions,
            'duration': '本句未涉及持续时间；同段描述的时限与句外条件强化未纳入本项',
            'unknowns': unknowns,
        },
        'quantity_kind': rule.get('quantity_kind'),
        'unit': UNIT,
        'rule_unit': rule.get('unit'),
        'raw_value': raw,
        'field_path': '/' + slot,
        'numeric_source': ('既有已确认规则（profiles/rules.json 的 ' + RULE_KEY +
                           '＋ordinary_effects/ability1095）＋CACHE skilllist 原始记录'),
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'answer_status': rule.get('answer_status'),
        'evidence_scope': SCOPE,
        'rule_key': RULE_KEY,
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
        'not_included': {
            'sentence_scope': f'仅「{target["sentence"]}」这一句',
            'out_of_sentence_cues': [dict(c) for c in chain['c18']['out_of_sentence']],
            'out_of_sentence_summary': target['out_of_sentence_summary'],
            'extra_slots_excluded': [dict(e, slot=e_slot, code='EXCLUDED_FIELD_NOT_CLAIMED',
                                          note='载体存在该槽非中性值，本句未主张：不并入（存在≠归属）')
                                     for e_slot, e in chain['c18']['extra_slots'].items()],
            'note': ('额外数值槽与同段其他句子的条件强化都不并入本项；'
                     '本项不是整条能力记录的合计'),
        },
        'excluded_carrier_fields': excluded,
        'source': _source_block(chain, slot, data),
        'binding': {'c18_p1_1095_attack_partial_binding': {
            'scope': SCOPE,
            'row_id': target['row_id'],
            'effect_id': target['effect_id'],
            'claim': target['claim'],
            'slot': slot,
            'rule_key': RULE_KEY,
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
    target = BY_ROW.get((cid, row.get('row_id')))
    if target is None:
        out['status'] = 'ROW_OUT_OF_SCOPE'
        out['reason'] = 'ROW_NOT_IN_FROZEN_SCOPE'
        return out

    chain = resolve_chain(data, cid, row, skill=skill, target=target)
    out['chain'] = dict(status=chain['status'], reason=chain.get('reason'),
                        detail=chain.get('detail'), gates=chain.get('gates') or [],
                        carrier=(None if chain['status'] != 'RESOLVED' else dict(
                            record_id=chain['carrier']['record_id'],
                            index=chain['carrier']['index'],
                            carrier_slot=chain['carrier_slot'],
                            parent_record_id=chain['parent']['record_id'],
                            parent_index=chain['parent']['index'])),
                        field_states=chain.get('field_states'),
                        c18=chain.get('c18'))
    if chain['status'] != 'RESOLVED':
        out['status'] = 'REJECTED'
        out['reason'] = chain.get('reason')
        return out

    analysis = LEDGER.analyze_row(row, table='skilllist')
    effects = [e for e in analysis.get('effects') or []
               if e.get('record_type') == 'effect' and '#e' in e.get('effect_id', '')]
    by_id = {e['effect_id']: e for e in effects}
    effect = by_id.get(target['effect_id'])
    if effect is None:
        out['missing_targets'].append(dict(effect_id=target['effect_id'],
                                          detail='该 effect_id 未出现在当前解析结果'))
        out['status'] = 'RESOLVED_PARTIAL'
        return out
    claim_ok = effect.get('effect_type') == target['claim']
    out['matched_effects'].append(dict(
        effect_id=target['effect_id'], effect_type=effect.get('effect_type'),
        direction=effect.get('direction'), status_before=effect.get('status'),
        claim_expected=target['claim'], claim_matches=claim_ok))
    if not claim_ok:
        out['rejected'].append(dict(effect_id=target['effect_id'], slot=target['slot'],
                                    code='CLAIM_MISMATCH',
                                    detail=f'行内 effect 类型 {effect.get("effect_type")!r} '
                                           f'与冻结主张 {target["claim"]!r} 不符'))
    else:
        answer, why = build_answer(chain, target, data)
        if answer is None:
            out['rejected'].append(dict(effect_id=target['effect_id'],
                                        slot=target['slot'], **why))
        else:
            out['answers'].append(answer)

    out['excluded_fields'] = C16.collect_exclusions(chain, {target['slot']})
    out['status'] = 'RESOLVED_ALL' if len(out['answers']) == 1 else 'RESOLVED_PARTIAL'
    out['analysis_summary'] = dict(
        effect_status=[dict(effect_id=e['effect_id'], effect_type=e['effect_type'],
                            status=e['status']) for e in effects],
        split_flags=analysis.get('split_flags'),
        unmatched_answer_refs=[r for r in analysis.get('answer_refs') or []
                               if r.get('matched_effect_id') is None])
    return out


def apply_to_groups(data, cid, groups, *, scope=None):
    """把 C18 答案写入 ``build_card`` 产出的 groups（仅内存）；幂等，第二次 0 新增。"""
    require_scope(scope)
    report = dict(cid=cid, scope=scope, module_version=MODULE_VERSION,
                  status='OUT_OF_SCOPE', rows=[], added=0, skipped=0, conflicts=0,
                  rejected=0, excluded_fields=0)
    if cid not in TARGET_CIDS:
        report['detail'] = (f'cid={cid} 不在 C18-P1 两项白名单：零新增'
                            '（C17 已交付卡/C16 同族卡/保护卡/待补卡/同句未过链卡结构上不可达）')
        return report
    report['status'] = 'APPLIED'
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                rid = row.get('row_id')
                if rid not in TARGET_ROW_IDS.get(cid, set()):
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


def scope_dump():
    """机器可读冻结作用域（只含身份，不含 raw／value／载体 ID）。"""
    return dict(module_version=MODULE_VERSION, scope=SCOPE,
                targets=[dict(t) for t in TARGETS],
                negative_cids=list(NEGATIVE_CIDS),
                negative_same_sentence_items=[dict(i) for i in NEGATIVE_SAME_SENTENCE_ITEMS],
                counts=dict(items=len(TARGETS), cids=len(TARGET_CIDS),
                            rows=len(BY_ROW), slots=sorted({t['slot'] for t in TARGETS}),
                            rule_keys=sorted({t['rule_key'] for t in TARGETS})))


def module_hashes(root):
    """模块与关键输入的 SHA-256（README/检查结果记录用）。"""
    root = Path(root)
    files = [Path(__file__), _HERE / 'card_page_inference_c16_p1_1095_partial.py',
             _HERE / 'effect_ledger.py', _HERE / 'card_page_data.py', _HERE / 'rules.py',
             root / 'output/character_skills/profiles/rules.json',
             root / SKILLLIST_REL, root / CHARAINFO_REL]
    return {str(p.relative_to(root)).replace('\\', '/'): sha256_file(p) for p in files}
