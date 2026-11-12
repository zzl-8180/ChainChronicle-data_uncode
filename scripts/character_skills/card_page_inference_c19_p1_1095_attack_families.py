# -*- coding: utf-8 -*-
"""C19-P1 ``skilllist`` ability 1095 **攻击同族逐效果部分绑定**——130 项候选实现（**未接线**）。

任务卡 ``docs/tasks/20261107-c19-p1-1095-attack-families.md``；周期卡
``docs/tasks/20261107-c19-cycle.md``；方向评估 ``docs/tasks/20261107-c19-direction-assessment.md``
与 ``docs/tasks/20261106-c19-direction-assessment.md``；方法
``docs/角色技能完整解读实施方案.md`` §1.3／§1.6。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；
``rules.json``／``rules.py``／``effect_ledger.py``／C16／C17／C18 模块／正式 ``pages``／账本均未改动；
本阶段不运行正式全库生成或 resume。模块只读当前快照解码 JSON、``profiles/rules.json``，
并由调用方传入真实 ``card_page_data.Inputs`` 与页面行对象（``build_card`` 产物）。

作用域
======
130 个 CACHE ``skilllist`` ability 1095 行的**攻撃力** effect（每卡一行一个），
另对同一 1095 载体的 ``param2``／``param3``／``param5``／``param6`` 逐效果扫描：
仅当该效果在本行句面明确出现、当前 effect 未解析、且既有规则与账本映射可消费时才出答案。
``param4``／``param7``／``param8`` 只登记，不解释。

**冻结表只含身份**（cid／row_id／槽／主张／rule_key／分组）。本模块不保存、不导入任何预筛 raw、
载体 ID 或句面原文；raw、载体、父文、fragment 与 source span、可绑定槽位一律由
「真实角色 → 父 skilllist →（父自身或唯一 sub）1095 载体 → 字段 → ``rules.answer_for``」重算。
任务卡与预筛清单给出的载体 ID、载体原值与句面，只在 ``check_candidate.py`` **计算之后**
作回归比对；本模块的源码与运行期都不读取、不命名、不导入这些数值。

两种真实引用形态（不得混用、不得任选）
--------------------------------------
* ``PARENT_SELF``：父 ``skilllist`` 记录自身 ``ability == 1095``，载体即父记录；
* ``SUB_SINGLE``：父记录自身不是 1095，且 ``sub[]`` 中 ``ability == 1095`` 的记录恰 1 条，
  按**真实下标** ``sub[i]`` 解引用；
* 父自身 1095 与 sub 内 1095 同时存在 → ``R9_AMBIGUOUS_SELF_AND_SUB`` 拒绝，不任选其一。

逐行硬门（任一不符即拒绝，不猜、不取邻近记录、不补零）
------------------------------------------------------
R1  **角色上游**：``charainfo[cid]`` 在 CACHE 解码表**唯一存在**。
R2  **角色身份**：行 ``cid`` 与调用 cid 相同。
R3  **引用形态**：行 ``group == 'ability'`` 且 ``reference_field`` 恰为 ``skillid[n]``。
R4  **槽位**：``charainfo.skillid[n]`` 存在（不越界）。
R5  **父记录唯一**：该 skillid 在 CACHE ``skilllist`` 全表**恰出现 1 次**；``Inputs`` 记录与原文逐值相同。
R6  **行来源指针**：行 ``source.json_pointer == /skilllist/<父下标>`` 且字段指针为 ``.../text``。
R7  **片段归属与 span**：行日语在父 ``text`` 中**恰出现 1 次**（NFKC 去空白后亦恰 1 次），
    并记录该片段在父文原文中的 start／end 字符偏移；不按同文跨行复制。
R8  **子记录登记**：父 ``sub[]`` 每个 skillid 全表唯一命中且 ``Inputs`` 一致（只登记竞争载体）。
R9  **载体唯一**：见上两种形态；0 条或多条 → 拒绝。
R10 **字段解引用**：``param1`` 必须 present（有限正数）；``param2/3/5/6`` 在句面明确时同样要求
    present；``missing／null／非有限／负值／真零`` 分别登记且都不出答案（不补零、不借相邻记录）。
R11 **规则复用**：只调用 ``rules.answer_for('skilllist', 1095, '/<槽>', raw, 载体, source_layer='CACHE')``；
    不新增公式、不新增规则键；账本映射沿用 ``effect_ledger._RULE_KEY_EFFECT`` 既有五键。
R12 **本句范围（子句级）**：把行日语按「、」「。」切子句；含 stat 词的子句若无
    非自身主语／条件线索，才是可认领子句；首个可认领子句之前的子句含条件标记 → 整句条件化，拒绝。
    因此「敵陣にいると」「WAVEが進むたび」「1stキャラクターに…付与」「味方の…」一律不认领。
R13 **句外不并入**：父文其余句子（含条件增强「効果が上がる」、WAVE、击杀、地形、自动必杀等）
    只在 ``not_included`` 完整披露，不并入本项数值、也不跨句取数；``param6`` 等未在本句出现的槽不得并入。

部分绑定边界
------------
某槽「存在」不证明属于当前句。只有句面同一子句明确写出的 stat 才认领；同句其他效果
（通常回復の回復量／攻撃間隔／状態異常無効／追撃など）只披露。句外其他句子的条件强化同样只披露。
这不是删除旧 P4，也不是放宽 B11／B12／B14；本模块不 import、不引用、不改动这三者与旧 P4 模块。

证据分档（不得升格）
--------------------
R1–R13 与字段原值为结构／原值证据；句面主张→该 1095 载体字段的归属为**推断**。答案写
``numeric_evidence='确认'``（既有静态及受控原生局部规则＋CACHE 原始记录）、
``association_evidence='推断'``、``binding='inferred'``、``runtime_verified=False``、
``evidence_scope=SCOPE``。这是“既有规则体与当前原值已确认”，不是完整语义确认，也不是实机确认。

明确不处理
----------
* 7687（父 ability=1110，无 1095 载体）、20607／20638／20708（CACHE charainfo 缺该 cid）、
  30236／30239／30102／20234（保护卡）、已有答案行、C16／C17／C18 已答项：一律零新增。
* 条件增强、友方、近战、WAVE、击杀、地形、静止、命中、反击、自动必杀、マナスロット等
  句内条件子句：不认领；句外同段条件只披露。
* 其他机制族、type108、其他 1095 载体与槽位、新原生、实机、新缓存、清理、Git、发布。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from project_layout_paths import read_path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:            # 允许从任意工作目录直接导入
    sys.path.insert(0, str(_HERE))

import effect_ledger as LEDGER                       # 只读：真实消费者
import rules as R                                    # 只读：既有规则与公式
import card_page_inference_c16_p1_1095_partial as C16  # 只读：已审查的真实链工具复用

MODULE_VERSION = 'c19_p1_1095_attack_families_20261107'
#: 本作用域（缺省／错误／空 scope 一律硬拒绝；见 ``ScopeError``）。
SCOPE = 'C19_P1_1095_ATTACK_FAMILIES_20261107'
CARRIER_ABILITY = 1095
BLOCKING_KEY = 'c19_p1_1095_attack_families_binding'
DECODED_REL = C16.DECODED_REL
SKILLLIST_REL = C16.SKILLLIST_REL
CHARAINFO_REL = C16.CHARAINFO_REL
RESOLVED_EXACT = C16.RESOLVED_EXACT
SHAPE_SELF = 'PARENT_SELF'
SHAPE_SUB = 'SUB_SINGLE'

#: 句面主张 → 1095 槽位。取值依据＝``effect_ledger._RULE_KEY_EFFECT`` 既有五键
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
RULE_KEY_FOR_SLOT = {slot: f'skilllist|1095|/{slot}' for slot in CLAIM_FOR_SLOT}
CLAIMABLE_SLOTS = ('param1', 'param2', 'param3', 'param5', 'param6')
#: 载体上需要登记的全部槽位（param4／param7／param8 只登记，无 1095 既有规则）。
CARRIER_SLOTS = ('param1', 'param2', 'param3', 'param4', 'param5', 'param6', 'param7', 'param8')
#: 既有规则口径的中性值（只用于“中性≠主张”登记与检查，不用来补值）。
NEUTRAL_VALUES = {'param1': 1.0, 'param2': 1.0, 'param3': 1.0, 'param4': 1.0,
                  'param5': 0.0, 'param6': 1.5}
UNIT_FOR_SLOT = {
    'param1': '攻击倍率（无量纲）；本项增加以百分比表示',
    'param2': '移动速度倍率；本项增加以百分比表示',
    'param3': '受伤量倍率（无量纲）；本项减伤以百分比表示，不是固定防御值',
    'param5': '暴击概率百分点（对 0 的加算增量）',
    'param6': '暴击伤害系数增量（在 1.5 基准上的加算）',
}
STAT_ZH = {
    'param1': '攻击力',
    'param2': '移动速度',
    'param3': '受到伤害的减轻量',
    'param5': '暴击率',
    'param6': '暴击伤害系数',
}
#: 子句内出现即表示“该 stat 不是自身无条件基础增益”（非自身主语／句内条件／其他机制限定）。
CLAUSE_SUBJECT_CUES = ('味方', '1stキャラクター', '他キャラクター', 'サブパーティ',
                       '敵', '自陣', '敵陣')
CLAUSE_CONDITION_CUES = ('時', 'たび', '場合', 'につき', 'ごと', 'いると', 'すると',
                         'ていると', 'ほど', '以上', '以下', 'まで')
CLAUSE_OTHER_CUES = ('近接', '静止', '命中', '当てる', 'カウンター', '自動', '付与',
                     '共鳴', '連撃', '一定確率')


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


def fragments(text):
    """父文句子片段（按「。」「\n」「◆」切分）；用于句外披露与片段唯一性。"""
    body = str(text or '')
    cut = body.find('[i][c]')
    if cut >= 0:
        body = body[:cut]
    out = []
    for part in body.replace('\n', '◆').split('◆'):
        for seg in part.split('。'):
            seg = seg.strip(' \r\t')
            if not seg or seg.startswith('[i]'):
                continue
            if set(seg) <= set('\\n \t'):      # 原文里的字面转义 \n 片段不是句子
                continue
            if not canon(seg):
                continue
            out.append(seg)
    return out


def clauses(fragment):
    """行日语子句（按「、」「。」切分），用于 R12 子句级条件判定。"""
    return [c for c in str(fragment or '').replace('\n', '。').split('、')
            if c.strip(' 。\r\t')]


def _gate(gates, code, ok, detail, **extra):
    gates.append(dict(code=code, ok=bool(ok), detail=detail, **extra))
    return bool(ok)


def _reject(gates, code, detail, **extra):
    _gate(gates, code, False, detail, **extra)
    return dict(status='REJECTED', reason=code, detail=detail, gates=gates)


def _target(cid, row_id, group):
    return dict(cid=cid, row_id=row_id, group=group, slot='param1', claim='攻撃力',
                rule_key=RULE_KEY_FOR_SLOT['param1'])


_t = _target


#: 130 项 CACHE 1095 攻撃力 effect 冻结身份（cid／row_id／分组／槽／主张／rule_key）。
#: 本表**不含**任何 raw、载体 ID、句面原文或额外槽位：这些一律在运行期由真实记录重算。
TARGETS = (
    _t(220, '220-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(223, '223-ability-ability-skillid_1_-lvorder0-f0', 'G2'),
    _t(341, '341-ability-ability-skillid_1_-lvorder0-f2', 'G3'),
    _t(342, '342-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(345, '345-ability-ability-skillid_1_-lvorder0-f0', 'G1_D5'),
    _t(346, '346-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(347, '347-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(353, '353-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(1217, '1217-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(1219, '1219-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(1244, '1244-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(1267, '1267-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(1297, '1297-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(1299, '1299-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(2287, '2287-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(2324, '2324-ability-ability-skillid_1_-lvorder0-f0', 'G1_D4'),
    _t(2328, '2328-ability-ability-skillid_1_-lvorder0-f0', 'G1_D5'),
    _t(2329, '2329-ability-ability-skillid_1_-lvorder0-f0', 'G0'),
    _t(4254, '4254-ability-ability-skillid_1_-lvorder0-f0', 'G1_D4'),
    _t(4295, '4295-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(4312, '4312-ability-ability-skillid_1_-lvorder0-f4', 'G3'),
    _t(5264, '5264-ability-ability-skillid_1_-lvorder0-f0', 'G2'),
    _t(5300, '5300-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(5305, '5305-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(5306, '5306-ability-ability-skillid_1_-lvorder0-f0', 'G1_D4'),
    _t(6234, '6234-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(6306, '6306-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(6315, '6315-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(6334, '6334-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(6336, '6336-ability-ability-skillid_1_-lvorder0-f0', 'G1_D4'),
    _t(7201, '7201-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(7203, '7203-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(7231, '7231-ability-ability-skillid_1_-lvorder0-f0', 'G2'),
    _t(7249, '7249-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(7250, '7250-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(7509, '7509-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(7518, '7518-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(7597, '7597-ability-ability-skillid_1_-lvorder0-f0', 'G1_D5'),
    _t(7611, '7611-ability-ability-skillid_1_-lvorder0-f0', 'G0'),
    _t(7612, '7612-ability-ability-skillid_1_-lvorder0-f0', 'G0'),
    _t(7676, '7676-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(8399, '8399-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(8400, '8400-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(8401, '8401-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(8402, '8402-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(8403, '8403-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(8424, '8424-ability-ability-skillid_1_-lvorder0-f0', 'G2'),
    _t(8425, '8425-ability-ability-skillid_1_-lvorder0-f0', 'G2'),
    _t(9228, '9228-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(9238, '9238-ability-ability-skillid_1_-lvorder0-f4', 'G4'),
    _t(9239, '9239-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(9242, '9242-ability-ability-skillid_1_-lvorder0-f0', 'G1_D7'),
    _t(10212, '10212-ability-ability-skillid_1_-lvorder0-f4', 'G3'),
    _t(10215, '10215-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(11233, '11233-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(11234, '11234-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(12236, '12236-ability-ability-skillid_1_-lvorder0-f4', 'G4'),
    _t(12237, '12237-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(12238, '12238-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(13225, '13225-ability-ability-skillid_1_-lvorder0-f0', 'G1_D4'),
    _t(13228, '13228-ability-ability-skillid_1_-lvorder0-f0', 'G1_D6'),
    _t(20105, '20105-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20106, '20106-ability-ability-skillid_1_-lvorder0-f1', 'G4'),
    _t(20115, '20115-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20131, '20131-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20201, '20201-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20219, '20219-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20225, '20225-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(20226, '20226-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(20236, '20236-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(20316, '20316-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20321, '20321-ability-ability-skillid_1_-lvorder0-f0', 'G1_D5'),
    _t(20323, '20323-ability-ability-skillid_1_-lvorder0-f0', 'G1_D5'),
    _t(20417, '20417-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(20512, '20512-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20521, '20521-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20523, '20523-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(20603, '20603-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20619, '20619-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20632, '20632-ability-ability-skillid_1_-lvorder0-f0', 'G1_D4'),
    _t(20640, '20640-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20644, '20644-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(20645, '20645-ability-ability-skillid_1_-lvorder0-f0', 'G2'),
    _t(20713, '20713-ability-ability-skillid_1_-lvorder0-f2', 'G3'),
    _t(20725, '20725-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20727, '20727-ability-ability-skillid_1_-lvorder0-f0', 'G1_D5'),
    _t(20728, '20728-ability-ability-skillid_1_-lvorder0-f0', 'G1_D5'),
    _t(20801, '20801-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20804, '20804-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20805, '20805-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20806, '20806-ability-ability-skillid_1_-lvorder0-f2', 'G3'),
    _t(20808, '20808-ability-ability-skillid_1_-lvorder0-f2', 'G3'),
    _t(20811, '20811-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20813, '20813-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20814, '20814-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20815, '20815-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20816, '20816-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20817, '20817-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20818, '20818-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20821, '20821-ability-ability-skillid_1_-lvorder0-f0', 'G1_D4'),
    _t(20825, '20825-ability-ability-skillid_1_-lvorder0-f0', 'G1_D2'),
    _t(20826, '20826-ability-ability-skillid_1_-lvorder0-f0', 'G1_D3'),
    _t(20827, '20827-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20830, '20830-ability-ability-skillid_1_-lvorder0-f0', 'G3'),
    _t(20836, '20836-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(20838, '20838-ability-ability-skillid_1_-lvorder0-f0', 'G0'),
    _t(20839, '20839-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(20909, '20909-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(20913, '20913-ability-ability-skillid_1_-lvorder0-f2', 'G3'),
    _t(20918, '20918-ability-ability-skillid_1_-lvorder0-f1', 'G3'),
    _t(30107, '30107-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(30109, '30109-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(30113, '30113-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(30214, '30214-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(30215, '30215-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(30220, '30220-ability-ability-skillid_1_-lvorder0-f0', 'G1_D6'),
    _t(30222, '30222-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(30241, '30241-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(30247, '30247-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(30250, '30250-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(30251, '30251-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(30254, '30254-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(30255, '30255-ability-ability-skillid_1_-lvorder0-f0', 'G1_D1'),
    _t(30258, '30258-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(30261, '30261-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
    _t(30263, '30263-ability-ability-skillid_1_-lvorder0-f0', 'G0'),
    _t(30310, '30310-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(30314, '30314-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(30326, '30326-ability-ability-skillid_1_-lvorder0-f0', 'G4'),
    _t(30338, '30338-ability-ability-skillid_1_-lvorder0-f2', 'G4'),
)

TARGET_CIDS = tuple(t['cid'] for t in TARGETS)
BY_ROW = {(t['cid'], t['row_id']): t for t in TARGETS}
TARGET_ROW_IDS = {cid: {t['row_id'] for t in TARGETS if t['cid'] == cid} for cid in TARGET_CIDS}
TARGET_GROUPS = {}
for _t0 in TARGETS:
    TARGET_GROUPS.setdefault(_t0['group'], []).append(_t0['cid'])

#: 明确拒绝的邻近集合（结构上不可达，零新增）：7687／20607／20638／20708、保护卡、
#: C16／C17／C18 已交付卡与已有答案卡。本模块不认领其中任何 effect。
NEGATIVE_CIDS = (7687, 20607, 20638, 20708, 30236, 30239, 30102, 20234,
                 30110, 30237, 30333, 30246, 20822, 6341, 20333, 20906, 20905,
                 20828, 20829, 6257, 20127, 20701, 1063, 1238, 12220)
#: 缺 CACHE charainfo 的邻近卡（R1 拒绝；不借 APK 上游、不跨源拼接）。
NO_CACHE_CHARAINFO_CIDS = (20607, 20638, 20708, 1063, 1238, 12220)
#: 保护卡（整卡零新增，旧答案原样保留）。
PROTECTED_CIDS = (30236, 30239, 30102, 20234)
#: C16／C17／C18 已交付卡（旧答案原样保留，不重复认领、不计本批收益）。
PRIOR_DELIVERED_CIDS = (30204, 30206, 30221, 30224, 30225, 30230, 30234, 30244,
                        30246, 30248, 30302, 30303, 30307, 30315, 30317,
                        20822, 6257, 20127, 20701, 20906, 20905, 20829, 20828,
                        30110, 30237, 30333, 6341, 20333)


# ---------------------------------------------------------------- 链解析（R1–R10）
def resolve_chain(data, cid, row, skill=None):
    """真实角色 → 父 skilllist → 1095 载体（父自身或唯一 sub），返回结构证据与 span。"""
    gates = []
    raw = raw_tables(data.root)

    chara = data.cache_chara.get(cid)
    if chara is None:
        return _reject(gates, 'R1_CHARAINFO_RECORD_MISSING',
                       f'CACHE charainfo 无 cid={cid}：原始角色上游缺失，不借 APK/页面/相邻记录补值',
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
                       'ability skillid[n]：非 1095 能力行结构上不适用',
                       group=row.get('group'), reference_field=ref)
    slot_index = int(m.group(1))
    _gate(gates, 'R3_ROW_NOT_ABILITY_SKILLID_REFERENCE', True, f'ability {ref} 引用形态成立')

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
                       f"skill.record_id={skill.get('record_id')!r} != "
                       f'charainfo.skillid[{slot_index}]={sid}')
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
    parent_text = str(parent.get('text') or '')
    if not frag or canon(parent_text).count(frag) != 1:
        return _reject(gates, 'R7_PARENT_TEXT_NOT_FRAGMENT',
                       '行日语片段在父 text 中出现次数 != 1（0 或多处均拒绝）')
    raw_frag = str(row.get('japanese') or '')
    start = parent_text.find(raw_frag)
    if start < 0 or parent_text.count(raw_frag) != 1:
        return _reject(gates, 'R7_FRAGMENT_SPAN_NOT_UNIQUE',
                       f'行日语原文 {raw_frag!r} 在父 text 原文中出现 '
                       f'{parent_text.count(raw_frag)} 次：无法给出唯一 source span')
    span = dict(start=start, end=start + len(raw_frag), unit='char',
                basis='CACHE/skilllist.data5.json.raw 父记录 text（原文偏移，不做规范化）',
                fragment=raw_frag)
    _gate(gates, 'R7_PARENT_TEXT_NOT_FRAGMENT', True,
          f'行日语片段在父 text 恰 1 次，原文 span [{span["start"]}, {span["end"]})')

    subs = parent.get('sub') or []
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
          f'父 sub[] 共 {len(sub_records)} 条，逐条唯一命中（只登记竞争载体）')

    self_1095 = parent.get('ability') == CARRIER_ABILITY
    sub_1095 = [i for i, x in enumerate(sub_records)
                if x.get('ability') == CARRIER_ABILITY]
    if self_1095 and sub_1095:
        return _reject(gates, 'R9_AMBIGUOUS_SELF_AND_SUB',
                       '父自身 ability=1095 且 sub[] 内亦有 1095：不得任选其一',
                       self_1095=True, sub_1095=[i for i in sub_1095])
    if self_1095:
        carrier = dict(skillid=sid, index=pidx, record=parent,
                       ability=CARRIER_ABILITY, shape=SHAPE_SELF, sub_slot=None)
    elif len(sub_1095) == 1:
        sub_pos = sub_1095[0]
        carrier = dict(skillid=sub_records[sub_pos]['skillid'],
                       index=sub_records[sub_pos]['index'],
                       record=sub_records[sub_pos]['record'],
                       ability=CARRIER_ABILITY, shape=SHAPE_SUB, sub_slot=sub_pos)
    else:
        return _reject(gates, 'R9_CARRIER_1095_NOT_UNIQUE',
                       f'父自身非 1095 且 sub[] 中 ability=1095 记录 {len(sub_1095)} 条，'
                       '要求恰 1 条（不按 sub[0] 假设、不取邻近记录）',
                       parent_ability=parent.get('ability'),
                       abilities=[x.get('ability') for x in sub_records])
    _gate(gates, 'R9_CARRIER_1095_NOT_UNIQUE', True,
          (f'载体形态 {carrier["shape"]}：skillid={carrier["skillid"]} '
           + ('@ 父记录自身' if carrier['shape'] == SHAPE_SELF
              else f'@ sub[{carrier["sub_slot"]}]')
           + f'（/skilllist/{carrier["index"]}）'))

    if carrier['shape'] == SHAPE_SUB:
        # 子载体本身也必须有唯一父记录位置；其 sub[] 不参与本行主张（只登记）。
        _gate(gates, 'R10_SUBCARRIER_SUBS', True,
              f'子载体 skillid={carrier["skillid"]} 的 sub[]={carrier["record"].get("sub") or []} '
              '只登记，不借值')

    states = {slot: raw_state(carrier['record'], slot) for slot in CARRIER_SLOTS}
    _gate(gates, 'R10_FIELD_STATES', True,
          '载体字段状态：' + '，'.join(f'{k}={v}' for k, v in states.items()))
    p1 = carrier['record'].get('param1')
    if states.get('param1') != 'present':
        return _reject(gates, 'R10_CLAIM_PARAM1_NOT_POSITIVE',
                       f'载体 /param1 状态={states.get("param1")}（{p1!r}）：不补零、不借相邻记录')
    if not (isinstance(p1, (int, float)) and not isinstance(p1, bool) and p1 > 0):
        return _reject(gates, 'R10_CLAIM_PARAM1_NOT_POSITIVE',
                       f'载体 /param1={p1!r} 不是有限正数：不补零、不借相邻记录')
    _gate(gates, 'R10_CLAIM_PARAM1_NOT_POSITIVE', True,
          f'载体 /param1={p1} 为有限正数')

    return dict(
        status='RESOLVED', reason=None, gates=gates, cid=cid, row_id=row.get('row_id'),
        charainfo=dict(table='charainfo', record_id=cid, index=chara_idx[0],
                       json_pointer=f'/charainfo/{chara_idx[0]}',
                       field_json_pointer=f'/charainfo/{chara_idx[0]}/skillid',
                       reference_field=ref, skillid_slot=slot_index),
        parent=dict(table='skilllist', record_id=sid, index=pidx,
                    json_pointer=f'/skilllist/{pidx}', ability=parent.get('ability'),
                    text=parent_text),
        carrier=dict(table='skilllist', record_id=carrier['skillid'],
                     index=carrier['index'],
                     json_pointer=f'/skilllist/{carrier["index"]}',
                     ability=CARRIER_ABILITY, shape=carrier['shape'],
                     record=carrier['record'],
                     record_key=f'CACHE/skilllist.data5.json.raw#/skilllist/{carrier["index"]}',
                     sub_slot=carrier['sub_slot'],
                     carrier_slot=(f'sub[{carrier["sub_slot"]}]'
                                   if carrier['shape'] == SHAPE_SUB else 'parent_self')),
        carrier_slot=(carrier['sub_slot'] if carrier['shape'] == SHAPE_SUB else 'parent'),
        carrier_shape=carrier['shape'],
        sub_abilities=[dict(skillid=x['skillid'], ability=x['ability'], index=x['index'])
                       for x in sub_records],
        field_states=states,
        fragment=dict(row_id=row.get('row_id'), japanese=row.get('japanese'),
                      parent_field_json_pointer=want_ptr + '/text',
                      fragment_index=row.get('fragment_index'), span=span,
                      parent_text=parent_text),
    )


# ---------------------------------------------------------------- 句面 claim 判定（R12）
def claim_clauses(fragment):
    """返回 (可认领子句, 非认领子句, 前置条件子句)；子句级判定，见 R12。"""
    cls = clauses(fragment)
    claim, non = [], []
    for idx, c in enumerate(cls):
        if not any(stat in c for stat in CLAIM_FOR_SLOT.values()):
            continue
        subj = [x for x in CLAUSE_SUBJECT_CUES if x in c]
        cond = [x for x in CLAUSE_CONDITION_CUES if x in c]
        other = [x for x in CLAUSE_OTHER_CUES if x in c]
        if subj or cond or other:
            non.append(dict(index=idx, clause=c, subject_cues=subj,
                            condition_cues=cond, other_cues=other))
        else:
            claim.append(idx)
    prefix = []
    if claim:
        for c in cls[:claim[0]]:
            hit = [x for x in CLAUSE_CONDITION_CUES if x in c]
            if hit:
                prefix.append(dict(clause=c, condition_cues=hit))
    return [cls[i] for i in claim], non, prefix


def claimed_slots(fragment, effect_types):
    """句面可认领的槽位 → 该槽在本行 effect 中的唯一性证据。

    ``effect_types`` 是真实 ``analyze_row`` 的 effect 类型序列；同一 claim 出现多次即歧义，
    不认领（不按顺序猜测、不取第一个）。
    """
    claim, non, prefix = claim_clauses(fragment)
    out = []
    for c in claim:
        for claim_name, slot in SLOT_FOR_CLAIM.items():
            if claim_name not in c:
                continue
            hits = [x for x in effect_types if x == claim_name]
            out.append(dict(slot=slot, claim=claim_name, clause=c,
                            effect_count=len(hits),
                            unique=len(hits) == 1))
    return out, non, prefix


def _effect_index(analysis):
    """真实 analyze_row 的 effect 列表 → {effect_type: [effect, ...]} 与有序表。"""
    effects = [e for e in analysis.get('effects') or []
               if e.get('record_type') == 'effect' and '#e' in str(e.get('effect_id'))]
    by_type = {}
    for e in effects:
        by_type.setdefault(e.get('effect_type'), []).append(e)
    return effects, by_type


# ---------------------------------------------------------------- 答案构造
def _source_block(chain, slot, data):
    carrier = chain['carrier']
    parent = chain['parent']
    subs = []
    skill_list = raw_tables(data.root)['skilllist']
    for sub in chain['sub_abilities']:
        rec = skill_list[sub['index']]
        subs.append(dict(skillid=sub['skillid'], ability=sub['ability'], index=sub['index'],
                         json_pointer=f'/skilllist/{sub["index"]}',
                         relevant_fields={s: rec.get(s) for s in CARRIER_SLOTS if s in rec}))
    return {
        'layer': 'CACHE', 'table': 'skilllist', 'record_id': carrier['record_id'],
        'record_index': carrier['index'], 'record_key': carrier['record_key'],
        'source_key': 'CACHE/skilllist.data5.json.raw',
        'original_file': SKILLLIST_REL,
        'json_pointer': carrier['json_pointer'],
        'field_path': '/' + slot,
        'field': '/' + slot,
        'field_json_pointer': f'{carrier["json_pointer"]}/{slot}',
        'carrier_slot': carrier['carrier_slot'],
        'carrier_shape': chain['carrier_shape'],
        'carrier_ability': CARRIER_ABILITY,
        'parent_record_id': parent['record_id'],
        'parent_record_index': parent['index'],
        'parent_json_pointer': parent['json_pointer'],
        'parent_text': parent['text'],
        'row_fragment': chain['fragment'],
        'row_sentence': chain['fragment'].get('japanese'),
        'fragment_span': chain['fragment']['span'],
        'charainfo': chain['charainfo'],
        'competition': {
            'carrier_ability': CARRIER_ABILITY,
            'carrier_count': 1,
            'carrier_shape': chain['carrier_shape'],
            'sub_records': subs,
            'other_carriers': [s for s in subs if s['ability'] != CARRIER_ABILITY],
            'note': ('同父记录仅消费被主张的 1095 载体字段；其他 ability 记录（含同样带 param 字段者）'
                     '只登记为竞争载体，不借用其数值或公式；子载体自身的 sub[] 亦不借值'),
        },
        'source_resolution': RESOLVED_EXACT,
    }


def _other_sentences(chain):
    frag = canon(chain['fragment'].get('japanese')).rstrip('。')
    out = []
    for f in fragments(chain['parent']['text']):
        if not canon(f) or canon(f).rstrip('。') == frag:
            continue
        out.append(f)
    return out


def other_summary(others):
    """同父其他句子的可读披露（不并入数值）。"""
    if not others:
        return '无'
    quotes = '；'.join('「' + o[:34] + ('…」' if len(o) > 34 else '」') for o in others[:3])
    more = f' 等 {len(others)} 句' if len(others) > 3 else ''
    return quotes + more


def player_sentence(slot, raw, sentence, others):
    """玩家可读中文（§1.3）：对象／量／基准／本句边界／句外未并入部分／未解边界。"""
    summary = other_summary(others)
    if slot == 'param1':
        pct = (float(raw) - 1.0) * 100
        return (f'自身攻击力提高 {percent_text(pct)}%'
                f'（本能力单独生效时攻击力变为 {num_text(raw)} 倍）。'
                f'本项只对应「{sentence}」这一句；同一能力描述中的其他句子（{summary}）'
                f'写的其他效果与条件强化不并入本项；最终数值未实机验证。')
    if slot == 'param2':
        pct = (float(raw) - 1.0) * 100
        return (f'自身移动速度提高 {percent_text(pct)}%'
                f'（本能力单独生效时移动速度变为 {num_text(raw)} 倍）。'
                f'本项只对应「{sentence}」这一句；同一能力描述中的其他句子（{summary}）'
                f'不并入本项，地形等其他来源另论。')
    if slot == 'param3':
        pct = (1.0 - float(raw)) * 100
        return (f'自身受到的伤害减少 {percent_text(pct)}%'
                f'（本能力单独生效时受到的伤害变为 {num_text(raw)} 倍；这是按比例减伤，'
                f'不是固定防御值）。本项只对应「{sentence}」这一句；同一能力描述中的其他句子'
                f'（{summary}）不并入本项；最终数值未实机验证。')
    if slot == 'param5':
        return (f'自身暴击率提高 {percent_text(float(raw) * 100)} 个百分点'
                f'（本能力单独生效时直接加算，不等于最终暴击率）。'
                f'本项只对应「{sentence}」这一句；同一能力描述中的其他句子（{summary}）'
                f'不并入本项。')
    if slot == 'param6':
        delta = float(raw) - 1.5
        return (f'自身暴击伤害系数提高 {percent_text(delta)}'
                f'（在 1.5 基准系数之上加算；不是相对现有伤害的百分比）。'
                f'本项只对应「{sentence}」这一句；同一能力描述中的其他句子（{summary}）'
                f'不并入本项；最终暴击伤害与扣血未验证。')
    raise ValueError(f'未定义的 1095 槽位：{slot!r}')


def build_answer(chain, target, slot, effect, data, others):
    """按真实载体字段构造单条答案；字段状态／规则／账本映射缺失 → ``(None, reason)``。"""
    carrier = chain['carrier']['record']
    state = chain['field_states'].get(slot)
    if state != 'present':
        return None, dict(code='FIELD_' + state.upper(),
                          detail=f'1095 载体 skillid={chain["carrier"]["record_id"]} 字段 /{slot} '
                                 f'状态={state}：不补零、不借相邻记录')
    raw = carrier[slot]
    rule_key = RULE_KEY_FOR_SLOT[slot]
    if LEDGER._RULE_KEY_EFFECT.get(rule_key) != CLAIM_FOR_SLOT[slot]:
        return None, dict(code='RULE_MAPPING_MISSING',
                          detail=f'effect_ledger 既有映射不含 {rule_key} → '
                                 f'{CLAIM_FOR_SLOT[slot]!r}：不新增映射')
    rule = R.answer_for('skilllist', CARRIER_ABILITY, '/' + slot, raw, carrier,
                        source_layer='CACHE')
    if not rule:
        return None, dict(code='RULE_MISSING',
                          detail=f'rules.answer_for 未返回 skilllist|1095|/{slot}')
    sentence = chain['fragment'].get('japanese')
    conditions = [
        '接受者自身已装载该能力，且对应能力列表/类型分派（能力编号 1095）通过时生效',
        '仅本项单一记录、单一槽位的局部贡献；不含同段描述其他句子、句中其他效果与其他来源',
        '本条来自 CACHE 静态记录；运行时装载与资格未实机验证',
    ]
    unknowns = [
        '运行时实际装载与资格未核实（未实机）',
        '与其他来源的实际叠加与最终战斗数值未验证',
        '本句面到该能力记录该槽位的归属为推断，不当作完整语义确认',
        f'同段其他句子的条件强化与机制（{other_summary(others)}）未并入本项，其数值另论',
    ]
    if slot == 'param3':
        unknowns.append('这是受伤量倍率（按比例减伤），不是固定防御量')
    if slot == 'param5':
        unknowns.append('不等于最终暴击率；同类上限与其他来源另论')
    if slot == 'param6':
        unknowns.append('基准 1.5 之上的加算不等于相对现有伤害的百分比')
    answer = {
        'value': rule.get('value_text'),
        'normalized_value': C16.normalized_value(slot, raw),
        'player_text': player_sentence(slot, raw, sentence, others),
        'player_scope': {
            'object': '自身（接受者）',
            'quantity': rule.get('quantity_kind'),
            'unit': UNIT_FOR_SLOT[slot],
            'conditions': conditions,
            'duration': '本句未涉及持续时间；同段描述的时限与句外条件强化未纳入本项',
            'unknowns': unknowns,
        },
        'quantity_kind': rule.get('quantity_kind'),
        'unit': UNIT_FOR_SLOT[slot],
        'rule_unit': rule.get('unit'),
        'raw_value': raw,
        'field_path': '/' + slot,
        'numeric_source': ('既有已确认规则（profiles/rules.json 的 ' + rule_key +
                           '＋ordinary_effects/ability1095）＋CACHE skilllist 原始记录'),
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'answer_status': rule.get('answer_status'),
        'evidence_scope': SCOPE,
        'rule_key': rule_key,
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
        'original_text': sentence,
        'not_included': {
            'sentence_scope': f'仅「{sentence}」这一句（父文 span '
                              f'{chain["fragment"]["span"]["start"]}-'
                              f'{chain["fragment"]["span"]["end"]}）',
            'other_sentences': others,
            'other_sentences_summary': other_summary(others),
            'extra_slots_excluded': [],
            'note': ('额外数值槽、同句其他效果与同段其他句子的条件强化都不并入本项；'
                     '本项不是整条能力记录的合计'),
        },
        'excluded_carrier_fields': [],
        'source': _source_block(chain, slot, data),
        'binding': {BLOCKING_KEY: {
            'scope': SCOPE,
            'group': target['group'],
            'row_id': target['row_id'],
            'effect_id': effect.get('effect_id'),
            'claim': CLAIM_FOR_SLOT[slot],
            'slot': slot,
            'rule_key': rule_key,
            'carrier_table': 'skilllist',
            'carrier_record_id': chain['carrier']['record_id'],
            'carrier_layer': 'CACHE',
            'carrier_shape': chain['carrier_shape'],
            'carrier_slot': chain['carrier']['carrier_slot'],
            'parent_record_id': chain['parent']['record_id'],
            'charainfo_record_id': chain['cid'],
            'raw_value': raw,
            'sentence': sentence,
            'fragment_span': chain['fragment']['span'],
            'binding': 'inferred',
            'runtime_verified': False,
        }},
        'details': rule,
    }
    return answer, None


def collect_row_exclusions(chain, claimed, analysis):
    """句面未主张的载体槽位／句面未认领的子句：只登记，不产出答案。"""
    out = []
    accepted = set(claimed)
    for slot in CARRIER_SLOTS:
        if slot in accepted:
            continue
        state = chain['field_states'].get(slot)
        raw = chain['carrier']['record'].get(slot)
        if slot in ('param4', 'param7', 'param8'):
            code = 'EXCLUDED_SLOT_NO_1095_RULE'
            detail = '该槽不在 1095 既有五键规则内：只登记不解释（不推广、不补值）'
        elif state in ('missing', 'null'):
            code = 'EXCLUDED_FIELD_ABSENT'
            detail = '载体无该字段或为 null：不产出（不补零、不借相邻类型）'
        elif state == 'present' and abs(float(raw) - NEUTRAL_VALUES[slot]) < 1e-9:
            code = 'EXCLUDED_FIELD_NEUTRAL'
            detail = '载体为该槽中性值，本句亦未主张：不产出'
        elif state == 'zero':
            code = 'EXCLUDED_FIELD_ZERO'
            detail = '载体存 0：不当作答案（不补零、不借相邻类型）'
        else:
            code = 'EXCLUDED_FIELD_NOT_CLAIMED'
            detail = ('载体存在该值，但本句未在可认领子句中主张：不并入本项'
                      '（存在≠归属；可能属同父其他句子，不跨句取数）')
        out.append(dict(slot=slot, state=state, raw_value=raw, code=code, detail=detail,
                        rule_available=slot in RULE_KEY_FOR_SLOT))
    return out


# ---------------------------------------------------------------- 公开 API
def evaluate(data, cid, row, *, scope=None, skill=None):
    """解析单行并返回候选答案（不写入）。``scope`` 缺省/错误/空 → ``ScopeError``。"""
    require_scope(scope)
    out = dict(cid=cid, row_id=row.get('row_id'), scope=scope,
               module_version=MODULE_VERSION, answers=[], rejected=[],
               excluded_fields=[], matched_effects=[], missing_targets=[],
               unclaimed_clauses=[], prefix_conditions=[])
    target = BY_ROW.get((cid, row.get('row_id')))
    if target is None:
        out['status'] = 'ROW_OUT_OF_SCOPE'
        out['reason'] = 'ROW_NOT_IN_FROZEN_SCOPE'
        return out

    chain = resolve_chain(data, cid, row, skill=skill)
    out['chain'] = dict(status=chain['status'], reason=chain.get('reason'),
                        detail=chain.get('detail'), gates=chain.get('gates') or [],
                        carrier=(None if chain['status'] != 'RESOLVED' else dict(
                            record_id=chain['carrier']['record_id'],
                            index=chain['carrier']['index'],
                            shape=chain['carrier_shape'],
                            carrier_slot=chain['carrier']['carrier_slot'],
                            parent_record_id=chain['parent']['record_id'],
                            parent_index=chain['parent']['index'])),
                        field_states=chain.get('field_states'),
                        fragment=(None if chain['status'] != 'RESOLVED' else
                                  chain['fragment']))
    if chain['status'] != 'RESOLVED':
        out['status'] = 'REJECTED'
        out['reason'] = chain.get('reason')
        return out

    analysis = LEDGER.analyze_row(row, table='skilllist')
    effects, by_type = _effect_index(analysis)
    sentence = row.get('japanese') or ''
    cand, non, prefix = claimed_slots(sentence, [e.get('effect_type') for e in effects])
    out['unclaimed_clauses'] = non
    out['prefix_conditions'] = prefix
    if prefix:
        out['status'] = 'REJECTED'
        out['reason'] = 'R12_SENTENCE_CONDITIONALIZED'
        out['rejected'].append(dict(code='R12_SENTENCE_CONDITIONALIZED',
                                    detail=f'首个可认领子句之前存在条件子句：{prefix}'))
        return out

    others = _other_sentences(chain)
    existing = {(a.get('rule_key'), a.get('field_path')) for a in row.get('answers') or []}
    own_keys = {(RULE_KEY_FOR_SLOT[x['slot']], '/' + x['slot']) for x in cand}
    foreign = [a for a in row.get('answers') or []
               if (a.get('rule_key'), a.get('field_path')) not in own_keys]
    if foreign:
        out['status'] = 'REJECTED'
        out['reason'] = 'R14_ROW_HAS_FOREIGN_ANSWERS'
        out['rejected'].append(dict(
            code='R14_ROW_HAS_FOREIGN_ANSWERS',
            detail=(f'目标行已有 {len(foreign)} 条非本项答案：冻结前提 answers=0 被破坏，'
                    '不追加、不改写'),
            answers=[dict(rule_key=a.get('rule_key'), field_path=a.get('field_path'))
                     for a in foreign]))
        return out
    claimed = []
    for item in cand:
        slot = item['slot']
        list_hits = by_type.get(item['claim']) or []
        eff = list_hits[0] if item['unique'] and list_hits else None
        out['matched_effects'].append(dict(
            slot=slot, claim=item['claim'], clause=item['clause'],
            effect_id=(eff or {}).get('effect_id'), effect_count=item['effect_count'],
            status_before=(eff or {}).get('status'),
            direction=(eff or {}).get('direction'),
            rule_key=RULE_KEY_FOR_SLOT[slot],
            already_answered=(RULE_KEY_FOR_SLOT[slot], '/' + slot) in existing))
        if eff is None:
            out['rejected'].append(dict(slot=slot, claim=item['claim'],
                                        code='CLAIM_EFFECT_NOT_UNIQUE',
                                        detail=f'行内 {item["claim"]} effect 出现 '
                                               f'{item["effect_count"]} 次：歧义，不认领'))
            continue
        already = (RULE_KEY_FOR_SLOT[slot], '/' + slot) in existing
        if not already and eff.get('status') != 'unresolved':
            out['rejected'].append(dict(slot=slot, effect_id=eff.get('effect_id'),
                                        code='EFFECT_NOT_UNRESOLVED',
                                        detail=f'目标 effect 当前状态 {eff.get("status")!r} '
                                               '不是 unresolved：不重复认领'))
            continue
        if eff.get('direction') != 'up':
            out['rejected'].append(dict(slot=slot, effect_id=eff.get('effect_id'),
                                        code='CLAIM_DIRECTION_NOT_UP',
                                        detail=f'目标 effect 方向 {eff.get("direction")!r}：'
                                               '非自身增益，不认领'))
            continue
        answer, why = build_answer(chain, target, slot, eff, data, others)
        if answer is None:
            out['rejected'].append(dict(slot=slot, effect_id=eff.get('effect_id'), **why))
            continue
        claimed.append(slot)
        out['answers'].append(answer)

    exclusions = collect_row_exclusions(chain, set(claimed), analysis)
    out['excluded_fields'] = exclusions
    excluded_view = [dict(e) for e in exclusions if e['code'] != 'EXCLUDED_SLOT_NO_1095_RULE']
    for answer in out['answers']:
        answer['excluded_carrier_fields'] = [dict(e) for e in exclusions]
        answer['not_included']['extra_slots_excluded'] = [
            dict(e, slot=e['slot'], code=e['code'],
                 note=('该槽只登记、不并入本项：存在≠归属；不补零、不跨句取数'))
            for e in excluded_view]
    out['status'] = ('RESOLVED_ALL' if 'param1' in claimed else 'RESOLVED_PARTIAL')
    out['analysis_summary'] = dict(
        effect_status=[dict(effect_id=e.get('effect_id'), effect_type=e.get('effect_type'),
                            status=e.get('status')) for e in effects],
        split_flags=analysis.get('split_flags'),
        answer_refs=[dict(rule_key=r.get('rule_key'), field_path=r.get('field_path'),
                          matched_effect_id=r.get('matched_effect_id'))
                     for r in analysis.get('answer_refs') or []],
        unmatched_answer_refs=[r for r in analysis.get('answer_refs') or []
                               if r.get('matched_effect_id') is None])
    return out


def apply_to_groups(data, cid, groups, *, scope=None):
    """把 C19 答案写入 ``build_card`` 产出的 groups（仅内存）；幂等，第二次 0 新增。"""
    require_scope(scope)
    report = dict(cid=cid, scope=scope, module_version=MODULE_VERSION,
                  status='OUT_OF_SCOPE', rows=[], added=0, skipped=0, conflicts=0,
                  rejected=0, excluded_fields=0, slots=[],
                  candidate_group=next((t['group'] for t in TARGETS if t['cid'] == cid), None))
    if cid not in TARGET_CIDS:
        if cid in NO_CACHE_CHARAINFO_CIDS:
            why = '缺 CACHE charainfo 上游：整卡零新增（不借 APK/页面记录补值）'
        elif cid in PROTECTED_CIDS:
            why = '保护卡：整卡零新增，旧答案原样保留'
        elif cid in PRIOR_DELIVERED_CIDS:
            why = 'C16/C17/C18 已交付卡：整卡零新增，旧答案原样保留'
        else:
            why = '不在 C19-P1 冻结作用域：整卡零新增'
        report['detail'] = why
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
                             added=0, skipped=0, conflicts=0, slots=[])
                if result['status'] == 'REJECTED':
                    report['rejected'] += 1
                    report['rows'].append(entry)
                    continue
                before = len(row.get('answers') or [])
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
                    entry['slots'].append(answer['field_path'])
                    report['added'] += 1
                    report['slots'].append(answer['field_path'])
                entry['answers_before'] = before
                entry['answers_after'] = len(existing)
                entry['excluded_fields'] = result.get('excluded_fields')
                report['excluded_fields'] += len(result.get('excluded_fields') or [])
                report['rows'].append(entry)
    return report


def scope_dump():
    """机器可读冻结作用域（只含身份，不含 raw／value／载体 ID／句面）。"""
    return dict(module_version=MODULE_VERSION, scope=SCOPE, blocking_key=BLOCKING_KEY,
                targets=[dict(t) for t in TARGETS],
                negative_cids=list(NEGATIVE_CIDS),
                no_cache_charainfo_cids=list(NO_CACHE_CHARAINFO_CIDS),
                protected_cids=list(PROTECTED_CIDS),
                counts=dict(items=len(TARGETS), cids=len(TARGET_CIDS),
                            rows=len(BY_ROW), slots=['param1'],
                            groups={k: len(v) for k, v in TARGET_GROUPS.items()},
                            rule_keys=sorted({t['rule_key'] for t in TARGETS})))


def module_hashes(root):
    """模块与关键输入的 SHA-256（README/检查结果记录用）。"""
    root = Path(root)
    files = [Path(__file__), _HERE / 'card_page_inference_c16_p1_1095_partial.py',
             _HERE / 'effect_ledger.py', _HERE / 'card_page_data.py', _HERE / 'rules.py',
             root / 'output/character_skills/profiles/rules.json',
             root / SKILLLIST_REL, root / CHARAINFO_REL]
    return {str(p.relative_to(root)).replace('\\', '/'): sha256_file(p) for p in files}
