"""效果账本生成器（目标整改 P1）——由当前页面描述驱动的逐描述、逐效果账本＋正式待办＋指标。

任务与验收依据（本模块实现的条款）：
* ``docs/tasks/20261022-character-skills-goal-rectification-prompt.md`` §三.1（效果账本）、
  §三.2（部分完成行入正式待办）、§三.4（指标）、§四 A2/A3/A4（覆盖/对账/待办不漏项）；
* 任务卡 ``docs/tasks/20261022-character-skills-goal-rectification.md``（P1 方案＋允许写入范围）；
* 第三方审查 ``output/character_skills/review/independent_20261022_codex_b14/GOAL_ALIGNMENT.md``
  G01（部分获值后同句剩余效果退出队列）/G02（缺效果级账本）/G03（Y.G. 优先未落实）。

输入＝当前 ``output/character_skills/pages/<cid>/card.json``（与页面同快照；卡数/行数从
当前文件重算，不硬编码旧数字）。输出目录 ``output/character_skills/effect_ledger/``：
* ``ledger.jsonl``——每条效果一行（record_type='effect'），每条描述另有一行
  （record_type='description'，含未识别任何效果的行——描述入口不因零效果而缺席）；
* ``backlog.json``——正式待办：全部未解决效果＋全部拆分待核查描述（A4 集合差证明见 checks）；
* ``metrics.json``——任务书 §三.4 指标（定义＋分母＋Y.G. 单列；证据档与完整度分开）＋自检结果；
* ``README.md``——字段定义/分母/优先级规则/复跑命令/诚实边界。

效果识别词表与边界规则来源（复用既有实现，不自造词表）：
* 属性词表与形状谓词＝批 6 ``card_page_inference_b6_bossbuff.py:112-118``（_ATTRS/_PRED）；
* 攻/防/移三属性与 ``(?<!属性)`` 负向断言边界规则＝批 9
  ``card_page_inference_b9_debuff.py:106-108,234-239``（_sentence_attrs，直接 import 复用）；
* 暴击/攻/防/移答案类型 taxonomy＝审查 ``goal_alignment.py:10``（攻撃力→攻击、
  防御力→受伤、移動速度→移动的对应关系）＋各推断批次头注的句式→槽位映射表
  （批 6 :56-61、批 8 2012 p4/p5、批 9/13 skilllist|99/2003 p7/p8/p9/p0、
  批 11/12 skilllist|1095 p1/p2/p3/p5/p6、试点 skilllist|1017 p1/p2/p3、批 7 skilllist|3000）。

诚实边界（本生成器刻意保守，均为任务书要求）：
* 「拆分待核查」七种触发：S1 零效果识别（不能以关键词缺失证明语义完整）、
  S2 数字语义未确认（R2 复审整改 20261023 第二轮：数字映射按角色绑定——先判文本角色
  （条件提示→条件角色；效果谓语→效果量角色；Nst/nd/rd/th→对象选择），再按角色匹配
  答案 quantity_kind/单位/换算口径与文本位置（效果量角色须被同子句主张消费）；数值
  相等只是必要线索，角色不符不映射；词面角色标签见 card_page_data.py:136-224）、
  S3 存在未被效果主张覆盖的正文子句（定性机制核查未完成）、
  S3b 词表外离散机制词/谓词模板无结构化覆盖（逐子句扫描；R2 复审整改 20261023 第二轮：
  只认 quantity_kind 指认或注记结构化载体披露，「未知/未解析/待核查/未分配」否定注记
  与纯词面提及不构成完成证据；监视表扩至バリア/盾/ガード等＋谓词模板〈宾语〉を付与/
  無効化/吸収/軽減）、
  S4 已映射类型的答案未对应任何句面主张、
  S5 HP 档位分支覆盖不完整／「随HP变化」句的增益答案缺 HP 档位条件绑定
  （R1 整改 20261023；仅 charainfo/denju 两表，bosspattern 行源记录即分支记录豁免）、
  S6 概率类条件无载体映射与解析状态（R2 整改 20261023；条件引用须有解析状态＋对应
  答案/证据映射或入待办——86 的「一定確率」→载体 skilllist|50009|APK /param3 即正式映射先例）
  ——全部显式登记并入队；
* 「有依据的不适用」不自动兜底：P1 仅对「…できない」禁止型子句（无数值词、无增减谓词、
  无属性词、非条件语境）出具逐条依据（na_basis）的定性 NA 判定；其余纯定性机制一律
  未解决，理由写进 gap；
* 已识别效果分母只是「当前词表从句面识别出的效果主张数」，不是全库全部效果数；
* 同号 ID 跨源不合并：效果/描述条目一律带行级命名空间（layer/table/record_id/source_key）。
"""
from __future__ import annotations

import argparse
import collections
import math
import datetime
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
from card_page_inference_b9_debuff import ATTRS3, _sentence_attrs  # noqa: F401  复用批 9 边界规则实现
import card_page_inference_b6_bossbuff as B6  # 复用批 6 属性词表与形状谓词

OUT_DEFAULT = Path('output/character_skills/effect_ledger')
PAGES_DEFAULT = Path('output/character_skills/pages')
RULES_PATH = Path('output/character_skills/profiles/rules.json')
CAMPAIGN_LATEST = Path('output/character_skills/pages/_batch/campaign_latest.json')

# ---- 效果类型词表（任务书 §三.1：至少含攻撃力/防御力/移動速度/クリティカル発生率/
#      クリティカル威力/HP回復/継続時間/定性机制）------------------------------------
CORE_TYPES = ('攻撃力', '防御力', '移動速度', 'クリティカル発生率', 'クリティカル威力',
              'HP回復', '継続時間')
NA_TYPE = '定性机制'
BREAKPOINT_CLAIM_TYPES = ('攻撃力', '防御力', '移動速度', '継続時間')
CRIT_ATTACK_MECHANISM = 'クリティカル攻撃机制（非暴击率/暴伤）'
_CRIT_POWER_RATE_SENTINEL = '__crit_power_and_rate__'

# 词面→效果类型（长词优先：正则交替按表序，命中即消费，避免「クリティカル威力」被「威力」
# 重复命中）。词表取自 B6._ATTRS（批 6 :112-114）＋「ダメージ/威力/回復」泛化项；
# 标注（词表外）的类型属已识别主张但当前效果词表未收录，一律未解决并登记词表扩展需求。
_WORD_TABLE = [
    # 批18词面三修（候选）：最长明确形先消费；裸 crit 仅作其余真实未知的回退。
    ('クリティカル攻撃時の威力と発生率', _CRIT_POWER_RATE_SENTINEL),
    ('クリティカル攻撃時の威力', 'クリティカル威力'),
    ('クリティカル攻撃の威力', 'クリティカル威力'),
    ('クリティカルの威力', 'クリティカル威力'),
    ('クリティカルの発生率', 'クリティカル発生率'),
    ('クリティカル発生率', 'クリティカル発生率'),
    ('クリティカル威力', 'クリティカル威力'),
    ('クリティカル率', 'クリティカル発生率'),
    ('クリティカル', 'クリティカル（発生率/威力未区分）'),   # 其余真实未知保留；攻撃机制另分流
    ('通常攻撃威力', '通常攻撃威力（词表外）'),
    ('攻撃間隔', '攻撃間隔（词表外）'),
    ('攻撃速度', '攻撃速度（词表外）'),
    ('移動速度', '移動速度'),
    ('防御力', '防御力'),
    ('攻撃力', '攻撃力'),
    ('受けるダメージ', '受けるダメージ（词表外）'),
    ('与えるダメージ', '与えるダメージ（词表外）'),
    ('ダメージ', 'ダメージ（词表外）'),
    ('効果', '効果（词表外）'),
    ('威力', '威力（词表外）'),
    ('回復', '回復（词表外）'),
]
_WORD_RE = re.compile('|'.join(re.escape(w) for w, _ in _WORD_TABLE))
_WORD_TYPE = dict(_WORD_TABLE)
_WORD_SET = {w for w, _ in _WORD_TABLE}
_HP_HEAL_RE = re.compile(r'HP[^。、]{0,6}?(?:回復する|回復し|回復)')
_DURATION_RE = re.compile(r'一定時間|\d+秒(?:間)?')

# 谓词（形状核心＝批 6 :117 _PRED 的动词集；「減る/増える」为本账本记录的扩展谓词，
# 批 6 家族门未用过、仅在账本侧标记主张方向，不参与任何晋级/晋级判定）。
_UP_VERBS = ('上がる', '上がり', '上げる', '増える', '早くなる', '回復する', '回復し')
_DOWN_VERBS = ('下がる', '下がり', '下げる', '遅くなる', '減る')
_CLAUSE_RE = re.compile(r'[^。、！？\n]+')
# 句级切分（R2 复审整改第二轮：效果量消费位置「同句跨子句」回退的坐标系；
# 与 assign_candidates/_SENT_RE 同法——「。！？\n」切分、允许句尾无标点）
_SENT_RE = re.compile(r'[^。！？\n]*[。！？]?')
# 连接词剥离（批 6 :119 同法；子句切分不含「、」本字，故带顿号与不带顿号两种形态都剥）。
_CONNECTIVES = tuple(B6._CONNECTIVES) + tuple(c.rstrip('、') for c in B6._CONNECTIVES)
# S5 非地形段（2026-10-26，主持裁决①）：概率玛那获得——来源限定消费。
# 只消费带 ``binding.s5_binding``（scope=S5_NONTERRAIN_20261026）的答案；无合格答案行
# 不新增主张、不改拆分。30236/30239 无本批答案，自然零触碰。
# S5 地形段（2026-10-26 批2）：独立 scope S5_TERRAIN_20261026，只收 param4/param5（地形附加），
# 与批次1 的 param0/1/2 答案池互不相交；主张只覆盖地形条件子句＋其后的玛那子句，
# 不覆盖本行前面的击杀基础概率子句（5092/7546 仍留 S3）。
S5_CHANCE_TYPE = '確率マナ獲得'
S5_SCOPE = 'S5_NONTERRAIN_20261026'
S5_TERRAIN_SCOPE = 'S5_TERRAIN_20261026'
S5_RULE_SLOTS = {'skilllist|28|/param0': 'param0',
                 'skilllist|28|/param1': 'param1',
                 'skilllist|28|/param2': 'param2'}
S5_TERRAIN_RULE_SLOTS = {'skilllist|28|/param4': 'param4',
                         'skilllist|28|/param5': 'param5'}
_S5_SCOPE_SLOTS = {S5_SCOPE: S5_RULE_SLOTS, S5_TERRAIN_SCOPE: S5_TERRAIN_RULE_SLOTS}
# 获珠相对句批（2026-10-29，主持授权 dwfq-0e41fa8d-1）：来源限定窄映射。相对句
# 「必殺技で倒すと獲得しやすくなる。」句面无「マナ」二字，既有 _S5_MANA_RX 不匹配；
# 本批答案带 ``binding.s5_relative_binding`` 标记，**只对该标记行**新增一条「確率マナ獲得」
# 主张（覆盖句面相对子句），使行级归位答案可被既有 S5 槽位映射消费。无标记行
# （含全部旧页与其他族）行为零变化；不整族映射 type28、不改 S5_RULE_SLOTS。
S5_RELATIVE_MARK = 's5_relative_binding'
_S5_RELATIVE_RX = re.compile(r'獲得しやすくな|獲得しやすく')
# G1-B1 必殺ダメージ镜像行绑定批（2026-10-29）：来源限定窄映射。只消费本批模块
# （card_page_inference_g1_b1.py）写入、带 ``binding.g1_b1_binding``
# （scope＝G1_B1_MIRROR_20261029）的答案，且 rule_key / field_path / record_id / layer
# 与标记逐项一致；只补 6 个既有确认规则键 → ダメージ（词表外）。
# 不整族映射 bossskill 3/22/55/74/105/110（其余伤害键 76/112/51/47 不由本批消费、不登记）；
# 无标记行（含全部旧页与其他族）行为零变化；不改 _RULE_KEY_EFFECT / S5_RULE_SLOTS。
G1B1_SCOPE = 'G1_B1_MIRROR_20261029'
G1B1_RULE_EFFECT = {
    'bossskill|3|/skillparam1': 'ダメージ（词表外）',
    'bossskill|22|/skillparam1': 'ダメージ（词表外）',
    'bossskill|55|/skillparam1': 'ダメージ（词表外）',
    'bossskill|74|/skillparam5': 'ダメージ（词表外）',
    'bossskill|105|/skillparam1': 'ダメージ（词表外）',
    'bossskill|110|/skillparam1': 'ダメージ（词表外）',
}
# C8-P1 t27 周期回复批（2026-10-30，主持裁决）：来源限定窄映射。只消费本批模块
# （card_page_inference_c8_p1_t27.py）写入、带 ``binding.c8_p1_t27_binding``
# （scope＝C8_P1_T27_HEAL_20261030）的答案，且 rule_key / field_path / table / record_id /
# layer 与标记逐项一致；只把 ``bossskill|27|/skillparam1`` 绑到句面已有的「回復（词表外）」
# 词表主张（不新增规则键、不改 rules.json）。
# **不整族映射 type27**（p2 回复间隔 / p3 回复次数 / skillflag0_1 均不映射），无标记行
# （含全部旧页与其他族）映射行为零变化；不改 _RULE_KEY_EFFECT / G1B1_RULE_EFFECT。
C8P1_T27_SCOPE = 'C8_P1_T27_HEAL_20261030'
C8P1_T27_RULE_KEY = 'bossskill|27|/skillparam1'
C8P1_T27_EFFECT = '回復（词表外）'
# C10-P1 skilltext 同卡镜像整理批（2026-10-30，主持裁决）：来源限定窄映射。只消费本批模块
# （card_page_inference_c10_p1_mirror.py）写入、带 ``binding.c10_p1_mirror_binding``
# （scope＝C10_P1_T27_SKILLTEXT_MIRROR_20261030）的答案，且 rule_key / field_path / table /
# record_id / layer 与标记逐项一致；只把 ``bossskill|27|/skillparam1`` 绑到句面已有的
# 「回復（词表外）」词表主张（不新增规则键、不改 rules.json）。
# **不整族映射 type27**，不改 C8 的 C8P1_T27 分支、_RULE_KEY_EFFECT／G1B1_RULE_EFFECT；
# 无标记行（含全部旧页与其他族）映射行为零变化。t64 走既有全局映射，不在此表。
C10P1_T27_SCOPE = 'C10_P1_T27_SKILLTEXT_MIRROR_20261030'
C10P1_T27_RULE_KEY = 'bossskill|27|/skillparam1'
C10P1_T27_EFFECT = '回復（词表外）'
# C13-P2 t27 skilltext 镜像：只消费带本批 binding 的 p1，规则键／槽／表／记录／层逐项一致；
# p2/p3 仍只披露，不整族映射 type27，其他 t27 批次与无标记行行为不变。
C13P2_T27_SCOPE = 'C13_P2_T27_MIRROR_20261031'
C13P2_T27_RULE_KEY = 'bossskill|27|/skillparam1'
C13P2_T27_EFFECT = '回復（词表外）'
# type67 阶梯批（2026-10-28）：来源限定的槽位↔主张类型映射。只消费本批模块写入、
# 带 binding.type67_binding（scope＝TYPE67_BATCH_20261028）的答案；不整族映射 type67，
# 不改既有 P3B9/P3B10 等单记录条件答案的映射路径。
_T67_SCOPE = 'TYPE67_BATCH_20261028'
_T67_SLOT_EFFECT = {'param1': '攻撃力', 'param2': '移動速度', 'param3': '防御力',
                    'param6': 'クリティカル発生率', 'param7': 'クリティカル威力'}
# 金币/经验批（2026-10-28 批2）：来源限定的槽位↔主张映射。只消费本批模块写入、带
# ``binding.gold_exp_binding``（scope＝GOLD_EXP_BATCH_20261028）的答案；不整族映射
# skilllist 100/102，不改其他族、既有开局マナ与 B 档答案的映射路径。词表没有金币/经验
# 主张，故按 S5 同法**只对有本批合格答案的行**补一条来源限定主张（无答案行不新增主张）。
_GE_SCOPE = 'GOLD_EXP_BATCH_20261028'
_GE_RULE_SLOTS = {'skilllist|100|/param0': (100, '金币获得（词表外）'),
                  'skilllist|102|/param0': (102, '经验值获得（词表外）')}
_GE_ABILITY_MARK = {100: 'ゴールド', 102: '経験値'}
# 回复间隔两段乘数批（2026-10-28 批3）：来源限定窄映射。只消费本批模块写入、带
# ``binding.heal_interval_binding``（scope＝HEAL_INTERVAL_20261028）的答案；**不新增主张**，
# 只把它们绑到句面「回復速度」处已存在的「回復（词表外）」主张上（该主张的 span 落在
# 「回復速度」词形内部），基础段为主答案、条件段作 variant。无标记/错 scope/错槽位一律不消费；
# 不整族映射 type19/1033，不改其他族、既有开局マナ与 B 档答案的映射路径。
# type80（HoldMana 一次性条件增益）＋type96（ManaCountUp 逐珠线性）成对批（2026-10-28 批4）：
# 来源限定窄映射。只消费本批模块写入、带 ``binding.type80_96_binding``
# （scope＝TYPE80_96_BATCH_20261028）的答案；不整族映射 skilllist 80/96，不改其他族、
# 既有开局マナ/B 档（mana_b_binding）、type67、金币/经验、回复间隔答案的映射路径。
# 两族形态严格分开：80＝ONE_SHOT（一次性乘/加一次），96＝PER_UNIT_LINEAR（每颗×计数）。
_T8096_SCOPE = 'TYPE80_96_BATCH_20261028'
# 槽位→主张类型**按能力分表**：type80 的暴击槽是 param7（率）／param8（伤），
# type96 的是 param6（率）／param7（伤）——两族同号槽位语义不同（C2 的同一处易错点），
# 合表会把 80 的 param7 误记为「クリティカル威力」而无法绑定「クリティカル発生率」主张。
_T8096_SLOT_EFFECT = {
    80: {'param1': '攻撃力', 'param2': '移動速度', 'param3': '防御力',
         'param7': 'クリティカル発生率', 'param8': 'クリティカル威力'},
    96: {'param4': '移動速度', 'param5': '防御力',
         'param6': 'クリティカル発生率', 'param7': 'クリティカル威力'},
}
_T8096_FAMILIES = ('hold_mana_oneshot', 'mana_count_up_linear',
                   'mana_count_up_scrap_condition')
_T8096_EFFECT_TYPES = frozenset(v for table in _T8096_SLOT_EFFECT.values()
                                for v in table.values())
_HI_SCOPE = 'HEAL_INTERVAL_20261028'
_HI_RULE_SLOTS = {'skilllist|19|/param2': (19, 'param2'),
                  'skilllist|1033|/param3': (1033, 'param3')}
_HI_SPEED_WORD = '回復速度'
_HI_EFFECT = '回復（词表外）'
# G0-B1／G7-B0 合并小批（2026-10-28 批5）：来源限定窄映射。只消费本批模块写入、带
# ``binding.g0g7_binding``（scope＝G0_G7B0_20261028）的答案，且必须与该行主张的
# **span＋子句号**逐值相等（句面点名槽位）——不整族映射 skilllist 29／1008，不改其他族、
# 既有开局マナ/B 档/type67/金币经验/回复间隔/type80·96 答案的映射路径。
# G0＝bond 行「必殺技の威力」主张（威力（词表外）），G7＝地形句的 攻撃力／移動速度 主张
# （1008 p1/p2；p3 受伤量不映射，主持 2026-10-26 裁决）。
_G0G7_SCOPE = 'G0_G7B0_20261028'
_G0G7_RULE_SLOTS = {
    'g0_bond_power': {'skilllist|29|/param0': ('param0', '威力（词表外）')},
    'g7b0_terrain': {'skilllist|1008|/param1': ('param1', '攻撃力'),
                     'skilllist|1008|/param2': ('param2', '移動速度')},
}


def _g0g7_binding_of_answer(answer: dict):
    """本批答案标记 → (family, binding dict)；无标记返回 None。"""
    binding = answer.get('binding') if isinstance(answer.get('binding'), dict) else {}
    if not isinstance(binding, dict):
        return None
    got = binding.get('g0g7_binding')
    if not isinstance(got, dict) or got.get('scope') != _G0G7_SCOPE:
        return None
    return got.get('family'), got


def _ge_binding_of_answer(answer: dict):
    binding = answer.get('binding') if isinstance(answer.get('binding'), dict) else {}
    ge = binding.get('gold_exp_binding') if isinstance(binding, dict) else None
    return ge if isinstance(ge, dict) else None


def _ge_answer_slots(row: dict):
    """行内本批来源合格答案 → [(ability, answer_index, raw, rule_key)]（scope 精确）。"""
    out = []
    for idx, a in enumerate(row.get('answers') or []):
        ge = _ge_binding_of_answer(a)
        if not ge or ge.get('scope') != _GE_SCOPE:
            continue
        hit = _GE_RULE_SLOTS.get(a.get('rule_key'))
        if hit is None or a.get('field_path') != '/param0' or a.get('table') != 'skilllist':
            continue
        if hit[0] != ge.get('ability') or ge.get('rule_key') != a.get('rule_key'):
            continue
        if a.get('record_id') != ge.get('carrier_record_id') or a.get('layer') != ge.get('carrier_layer'):
            continue
        raw = a.get('raw_value')
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            continue
        out.append((hit[0], idx, raw, a.get('rule_key')))
    return out


def _hi_binding_of_answer(answer: dict):
    binding = answer.get('binding') if isinstance(answer.get('binding'), dict) else {}
    hi = binding.get('heal_interval_binding') if isinstance(binding, dict) else None
    return hi if isinstance(hi, dict) else None


def _hi_answer_slots(row: dict):
    """行内本批来源合格答案 → [(ability, answer_index, raw, rule_key)]（scope/槽/载体精确）。"""
    out = []
    for idx, a in enumerate(row.get('answers') or []):
        hi = _hi_binding_of_answer(a)
        if not hi or hi.get('scope') != _HI_SCOPE:
            continue
        hit = _HI_RULE_SLOTS.get(a.get('rule_key'))
        if hit is None or a.get('table') != 'skilllist':
            continue
        ability, slot = hit
        if (hi.get('ability') != ability or hi.get('slot') != slot
                or hi.get('rule_key') != a.get('rule_key')):
            continue
        if a.get('field_path') != '/' + slot:
            continue
        if a.get('record_id') != hi.get('carrier_record_id') or a.get('layer') != hi.get('carrier_layer'):
            continue
        raw = a.get('raw_value')
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            continue
        out.append((ability, idx, raw, a.get('rule_key')))
    return out
_S5_MANA_RX = re.compile(r'(?:一定確率|必ず)[^。]{0,30}?マナを獲得|マナを獲得しやすく')
_S5_KILL_RE = re.compile(r'敵に止めを刺した|敵に止めを刺す|止めを刺した|止めを刺す|'
                         r'敵を倒した|敵を倒す|倒した|倒す')
_S5_TRIGGER_QUALIFIERS = ('クリティカル', '必殺技', '通常攻撃', '攻撃', '自身',
                          '場合', 'たび', 'とき', '時', 'と', 'で', 'か', 'が', '、', ' ')
_S5T_COND_RX = re.compile(r'^(?:また|さらに)*(?:地形|戦場)が[^。]{1,40}?(?:の場合|の時|のとき)$')
_S5T_MANA_RX = re.compile(r'(?:さらに|また)*(?:必ず)?マナを獲得(?:しやすくな|しやすく|する)')

# R2 整改（20261023 复审）：数字 token 支持小数——「12.5%」此前被切成 '12' 与 '5' 两个
# 整数 token，导致值 12.5% 的既有答案（raw 5.5/0.125）永远无法映射（完整行误带未覆盖数字）。
_DIGIT_RE = re.compile(r'\d+(?:\.\d+)?')

# 条件/对象线索词（公共引用，供多效果共享；词表可扩，登记为引用不登记为效果）。
# DS-GR 条件关联修复（20261023，审查 §一「条件关联不完整」）：补 13205「戦場に<魔>武器の
# 味方がいると」、9221/319「サブパーティにいると」「WAVEが進むたび」类句面条件线索——
# 条件引用只登记关联，不改变任何效果状态/答案。
_SUBJECT_WORDS = ('味方全体', '自身', '敵', '味方')
_CONDITION_CUES = ('攻撃時', '命中時', '被ダメージ時', 'クリティカル時', 'バトル開始時',
                   '使用時', '発動時', '一定確率', '1stChain', '2ndChain', '3rdChain',
                   '範囲内', '近接', '遠距離', '残りHP', 'ダウン中', '戦闘不能',
                   '戦場に', '味方がいる', 'サブパーティ', 'WAVEが進むたび',
                   'マナ')  # R2 整改（20261023）：マナ所持条件入词表（61 完整行此前为词表外残余）
# R2 整改（20261023 复审 §R2）：概率类条件——句面未写实际概率（隐藏值在数据载体，如
# skilllist 触发门 param3），须有答案注记/适用条件的载体映射与解析状态；未映射→S6 待办。
# 其余条件词（范围/存在/状态/时机）全句已陈述（无隐藏数值），按句面限定解析并保留共享引用。
_PROBABILITY_CUES = frozenset({'一定確率'})
# 批 13 注记的概率载体披露形态（86 实例：「载体 /param3=0.15000000596046448（APK 特有形态：
# Skill 型着弹 15% 概率触发——逐行披露；概率值登记不分配）」）。
_CARRIER_PROB_RE = re.compile(r'载体 /param(\d+)=([0-9]+(?:\.[0-9]+)?)（[^（）]*概率')
# R2-Low 复审整改（20261023，R2-PROBABILITY-DISCLOSED-NO-VALUE）：批 13 注记的第二种概率
# 披露形态——「来源载体＝skilllist|<id>|<layer>…分数概率阈值 V1/V2…概率值登记不分配」
# （221/325/4217/6321/7606/8222/12216 实例）。载体键＋阈值原值结构化登记（多值/多字段），
# 不再以 disclosed（无载体值）结清；阈值↔参数槽对应未逐行确认（三路门 Normal=p1/Skill=p3/
# Critical=p2 为批 10 §2.1 既有类型语义、b13_apkext_scope.md 登记），登记不分配。
_CARRIER_KEY_RE = re.compile(r'来源载体＝(skilllist\|(\d+)\|(\w+))')
_THRESH_LIST_RE = re.compile(r'分数概率阈值 ([0-9]+(?:\.[0-9]+)?(?:/[0-9]+(?:\.[0-9]+)?)*)')
# R2 复审整改第三轮（20261023 root-fix，复审 §R2 根因②）：载体→效果族登记表——注记概率
# 载体披露里出现的能力号及其已登记可解释的效果族（依据各推断批的既有登记口径，不虚构）：
#   ability 99（批 9 b9_debuff：三路门攻/防ステータス減益，output/ordinary_effects/ability99/）；
#   ability 2003（批 13 b13_apkext：SA_PowerDrain デバフ系，output/ordinary_effects/ability2003/）；
#   ability 2012（批 8：クリティカル概率/威力加算贡献，output/ordinary_effects/ability2012/）。
# 20261023 全库实测：注记「来源载体＝skilllist|…，ability=…」披露的能力号仅此三号
# （99×373／2012×1,040／2003×1,532 答案）——均为属性值载体，不解释下方任何机制词族。
# 未登记能力号不虚构族对应：对应关系只由槽位绑定披露（_NOTE_SLOT_BIND_RE）单独作证。
_CARRIER_ABILITY_FAMILY = {
    '99': dict(family='ステータス減益（デバフ）', families=frozenset({'ステータス減益'}),
               source='批 9 b9_debuff／output/ordinary_effects/ability99/ 登记口径'),
    '2003': dict(family='ステータス減益（デバフ）', families=frozenset({'ステータス減益'}),
                 source='批 13 b13_apkext／output/ordinary_effects/ability2003/ 登记口径'),
    '2012': dict(family='クリティカル加算（バフ）', families=frozenset({'クリティカル加算'}),
                 source='批 8 crit2012／output/ordinary_effects/ability2012/ 登记口径'),
}
# 残余机制监视词→效果族（有限登记，逐词显式；审计口径同 _RESIDUAL_MECHANISM_WORDS）。
# 机制词族与属性值载体族（上表）当前无交集——已登记能力号的载体不得为状态/防御等
# 无关机制作证（复审 §R2 根因②；「仅作为对照/不属于」式对照性措辞因不含槽位绑定
# 披露被排除，不依赖否定词黑名单）。
_MECHANISM_WORD_FAMILY = {
    **{w: '状態異常' for w in ('暗闇', '猛毒', '毒', '凍結', '転倒', 'スタン', 'ダウン',
                               '眠り', '石化', '呪い', '魅了', '沈黙')},
    **{w: '特殊戦闘機構' for w in ('チャージ', 'カウンター', '迎撃', '追撃', '反射',
                                   '復活', '蘇生', 'テンション', 'ブレイク')},
    **{w: '吸収系' for w in ('ドレイン', '吸収')},
    **{w: '防御・無効化機構' for w in ('バリア', '盾', 'シールド', 'ガード', '無効化',
                                       '軽減', '弱点')},
}
# R2 整改：残余机制监视表（效果词表外的离散机制名词——出现在正文而任何答案的结构化
# 引用未覆盖时→S3b 拆分待核查；逐词登记词形依据，不做泛化猜测。仅监视，不参与答案映射）。
# R2 复审整改（20261023 第二轮）：扩表——バリア/盾/シールド/ガード/軽減/弱点此前在 24 词
# 表外，同句机制从监视表漏出（复审 §R2 反例：349＋「と同時にバリアを付与する。」判完整；
# 实测当前 4,000 完整行均不含下列任何词面，扩表零真实完整行翻转，差异清单见
# work/character_skills_rectification_r2r3/）。
_RESIDUAL_MECHANISM_WORDS = (
    '暗闇', '猛毒', '毒', '凍結', '転倒', 'スタン', 'ダウン', '眠り', '石化', '呪い',
    '魅了', '沈黙', 'チャージ', 'カウンター', '迎撃', '追撃', '反射', '復活', '蘇生',
    'テンション', 'ブレイク', 'ドレイン', '吸収', '無効化',
    'バリア', '盾', 'シールド', 'ガード', '軽減', '弱点')
# R2 复审整改（20261023）：机制谓词模板（谓词＋宾语形态，有限清单＋审计口径）——
# 宾语不含监视表名词/效果词表属性词时单独登记（如「≪決戦必殺≫を付与する」的宾语是
# 词表外机制名）；宾语含监视名词或属性词的由名词/属性主张覆盖，不重复登记。
# 审计口径：谓词取自 _MECHANISM_PREDICATES 有限清单；宾语捕获窗口 ≤16 字符（无顿号/句号）；
# 每处命中逐字登记谓词＋宾语＋子句位置，待办写缺口/已有证据/下一步。
_MECHANISM_PREDICATES = ('付与', '無効化', '吸収', '軽減')
# 宾语捕获：を 前的名词短语——排除 に格标记（「味方全体に炎属性を付与」的宾语是「炎属性」
# 不是「味方全体に…」），窗口 ≤12 字符、不含顿号/句号/に。
_MECHANISM_PRED_RE = re.compile(r'([^、。！？\nに]{1,12})を('
                                + '|'.join(_MECHANISM_PREDICATES) + r')')
# 否定解析状态标记：答案注记/quantity_kind/条件含这些词面时，该答案不构成机制覆盖证据
# （「暗闇机制尚未解析，待核查。」式否定注记不是完成证据——复审 §R2 反例；「尚未解析」
# 含子串「未解析」，同被拦）。
_UNRESOLVED_NOTE_MARKERS = ('未知', '未解析', '待核查', '未分配')
# 次数上限线索（319「3回まで」类）：kind='limit' 的公共引用（DS-GR 条件关联修复）。
_LIMIT_RE = re.compile(r'\d+回まで')

# ---- 对象维度（DS-GR-R1 修复，20261023 复验）----------------------------------------
# 缺陷：ダメージ 答案与主张同类型贪心先到先得——「自身受到伤害」答案被先出现的敌方
# ダメージ 主张消费，真正自伤主张仍未解决（复验 checks/object_swap.json 恰 9 行）。
# 修复：主张与答案都做对象分类，同类型匹配加对象约束；跨对象不硬配（留未解决并注明）。
# ダメージ 类效果类型（对象约束的作用域；攻/防/移等对象由对象词自明，不在此约束——
# 收窄作用域避免对既有非伤害匹配造成改道）。
_DAMAGE_TYPES = frozenset({'ダメージ（词表外）', '受けるダメージ（词表外）',
                           '与えるダメージ（词表外）'})
_SELF_MARKS_ANSWER = ('自身受到伤害', '自分')      # 自伤答案标记（「自身最大HP」是基数说明，不构成对象标记）
_ENEMY_MARKS_ANSWER = ('对敌', '敵')               # 敌方伤害答案标记（如「对敌伤害（基数：自身最大HP）」）
_SELF_MARKS_CLAUSE = ('自身', '自分')
_ENEMY_MARKS_CLAUSE = ('敵',)


def _answer_object(answer: dict):
    """答案对象分类（仅ダメージ 类答案参与约束）：self/enemy/None。"""
    text = (str(answer.get('quantity_kind') or '') + str(answer.get('value') or ''))
    if any(m in text for m in _SELF_MARKS_ANSWER):
        return 'self'
    if any(m in text for m in _ENEMY_MARKS_ANSWER):
        return 'enemy'
    return None


def _clause_object(clause: str):
    """主张子句对象分类（ダメージ 类匹配约束与 effect.object 用）：self/enemy/None。

    词典序优先动词（复验实测 8,514 个ダメージ 主张上零误配，恰覆盖 9 行错配）：
    「与え」＝向外赋予（对象＝敵侧——含「自身の最大HPのダメージを与える」这类以自身
    HP 为基数的向外伤害，基数说明词「自身の」不是目标）；**DS-GR-R1b 修复（20261023）**：
    「自身に／自分に…与える」是自我指向赋予（に格＝赋予对象，如 30230「一定間隔ごとに
    自身に小ダメージを与える」应 self 非 enemy）——に格自身标记存在且无「敵に」时判
    self；「敵に」并存时对象不可判归 enemy 侧原口径不变（保守）；「受け/負う」＝自身
    承受；动词缺失时退回对象词面（自身/自分 ↔ 敵；両标记并存或均缺失＝对象不可判 None，
    不硬配）。"""
    if '与え' in clause:
        self_dat = '自身に' in clause or '自分に' in clause
        if self_dat and '敵に' not in clause:
            return 'self'
        return 'enemy'
    if '受け' in clause or '負う' in clause:
        return 'self'
    has_self = any(m in clause for m in _SELF_MARKS_CLAUSE)
    has_enemy = any(m in clause for m in _ENEMY_MARKS_CLAUSE)
    if has_self and not has_enemy:
        return 'self'
    if has_enemy and not has_self:
        return 'enemy'
    return None

# ---- 答案→效果类型映射（rule_key 精确表；来源见模块头注各批次映射表）--------------
_RULE_KEY_EFFECT = {
    'skilllist|2012|/param4': 'クリティカル発生率', 'skilllist|2012|/param5': 'クリティカル威力',
    # 批18小范围消费者：只接收 own-record 明确「クリティカル率」词面可消费的
    # ability64 /param4。其余槽不借整行补齐扩域；值来源仍标规则外推。
    'skilllist|64|/param4': 'クリティカル発生率',
    # 共鳴必殺A/B 批（2026-10-26）：64 p1＝reactive heal 基值（回复主张）；
    # 114 p1＝冲刺重复攻击倍率（伤害主张）。仅这两键，不改其他映射。
    'bossskill|64|/skillparam1': '回復（词表外）',
    'bossskill|114|/skillparam1': 'ダメージ（词表外）',
    'bossskill|13|/skillparam1': '攻撃力', 'bossskill|13|/skillparam2': '防御力',
    'bossskill|13|/skillparam3': '継続時間', 'bossskill|13|/skillparam6': '移動速度',
    'skilllist|99|/param7': '攻撃力', 'skilllist|99|/param8': '移動速度',
    'skilllist|99|/param9': '防御力', 'skilllist|99|/param0': '継続時間',
    'skilllist|2003|/param7': '攻撃力', 'skilllist|2003|/param8': '移動速度',
    'skilllist|2003|/param9': '防御力', 'skilllist|2003|/param0': '継続時間',
    'skilllist|1095|/param1': '攻撃力', 'skilllist|1095|/param2': '移動速度',
    'skilllist|1095|/param3': '防御力', 'skilllist|1095|/param5': 'クリティカル発生率',
    'skilllist|1095|/param6': 'クリティカル威力',
    'skilllist|1017|/param1': '攻撃力', 'skilllist|1017|/param2': '移動速度',
    'skilllist|1017|/param3': '防御力',
    'skilllist|3000|/param1': '攻撃力', 'skilllist|3000|/param2': '攻撃力',
    'skilllist|3000|/param8': 'クリティカル威力', 'skilllist|3000|/param6': '継続時間',
    # マナ账本映射批（2026-10-26，窄门）：**仅** マナ批已上线的三个已消费键接入账本；
    # 不整族映射 type26（boost／職種限定／時の楔／Chain／コスト／スロット／所持 等
    # 未确认族不在此表，也不据 ability 号反向外推）。
    'skilllist|26|/param0': '開局マナ', 'skilllist|26|/param4': '開局マナ',
    'skilllist|26|/param7': '開局マナ',
    # クリティカル吸収批（2026-10-26，主持裁决 (a)）：**仅** ability21／65000003 的两个
    # 已确认规则键接入账本（回復（词表外）主张）；两键均具来源限定（规则 conditions 明写
    # 「仅普通65000003」，本批载体恰在域内）；不整族映射 ability21，不改其他族映射。
    'skilllist|21|/param1': '回復（词表外）', 'skilllist|21|/flag0_1': '回復（词表外）',
    # C11-P2 UnionCount 批（2026-10-31，主持裁决窄门）：**仅** skilllist 1059 的五个值槽
    # 接入账本；param0（人数阈值）、param6/param7（周期回复）与筛位不映射，不整族映射 1059。
    'skilllist|1059|/param1': '攻撃力',
    'skilllist|1059|/param2': '移動速度',
    'skilllist|1059|/param3': '防御力',
    'skilllist|1059|/param4': 'クリティカル発生率',
    'skilllist|1059|/param5': 'クリティカル威力',
}
# 上表各键的映射依据文本（_answer_effect_type 的 basis 用；未列键沿用通用依据）。
_RULE_KEY_EFFECT_BASIS = {
    'skilllist|26|/param0': 'マナ账本映射批三键精确映射（rule_key 精确匹配；不整族映射 type26）'
                            '＋来源限定主张（同槽位来源合格答案、原值整数化＝句中数字）',
    'skilllist|26|/param4': 'マナ账本映射批三键精确映射（rule_key 精确匹配；不整族映射 type26）'
                            '＋来源限定主张（同槽位来源合格答案、原值整数化＝句中数字）',
    'skilllist|26|/param7': 'マナ账本映射批三键精确映射（rule_key 精确匹配；不整族映射 type26）'
                            '＋来源限定主张（同槽位来源合格答案、原值整数化＝句中数字）',
    'skilllist|21|/param1': 'クリティカル吸収批两键精确映射（rule_key 精确匹配；不整族映射'
                            'ability21）＋载体来源限定（skilllist|65000003|CACHE ability21；'
                            '规则 conditions「仅普通65000003」）＋本批 binding 标记双槽同主张消费',
    'skilllist|21|/flag0_1': 'クリティカル吸収批两键精确映射（rule_key 精确匹配；不整族映射'
                             'ability21）＋载体来源限定（skilllist|65000003|CACHE ability21；'
                             '规则 conditions「仅普通65000003」）＋本批 binding 标记双槽同主张消费',
}
_BREAKPOINT_CRIT_KEYS = frozenset({'skilllist|2012|/param4', 'skilllist|2012|/param5'})
# P4（A2 复核修正，20261023）：99/2003 的 /param9＝「防御力下がる」的表现层（受伤量倍率
# 加算，正值→受伤量因子上升；批 9 映射表 card_page_inference_b9_debuff.py:11-12/:57 已
# 确认该对应）——方向按此固定，不用原值符号猜（原值符号对 p9 恰好反向）。
_RULE_KEY_DIRECTION = {'skilllist|99|/param9': 'down', 'skilllist|2003|/param9': 'down'}
# ---- マナ账本映射批（20261026，窄门）：開局マナ 三键接入 ------------------------------
# 范围（docs/tasks/20261026-mana-ledger-mapping.md §1）：只把マナ批已上线的三个已消费键
# 接入效果账本，使 has_answer/backlog 如实反映：
#   ``skilllist|26|/param0``（素マナ）｜``/param4``（全職業，iParam1=31）｜``/param7``（万象）。
# 禁止整族映射 type26：boost（param0×param5）／職種限定マナ／時の楔／Chain／コスト／
# スロット／所持 等未确认族**不登记主张**（生产侧已逐行拒答；本表不按 ability 号外推）。
# 主张为**来源限定主张**（source-qualified claim，与 _attack_interval_binding 同口径）：
# 仅当同一行内已有该槽位的来源合格答案（rule_key 精确、field_path 一致、table=skilllist、
# record_id 整数、raw_value 有限且整数化＝句中数字、quantity_kind 含「玛那数量」）且行文
# 命中三个开局句式之一时登记。没有该答案的行不登记主张——S1/S3 原样保留，**不把无答案项
# 标成有答案**（30236/30239 零触碰 12 行与 323 的 1 行保持既有待办）。
MANA_START_TYPE = '開局マナ'
MANA_START_RULE_KEYS = {'skilllist|26|/param0': 'param0',
                        'skilllist|26|/param4': 'param4',
                        'skilllist|26|/param7': 'param7'}
# 三个已确认开局句式（NFKC 后子句级搜索；span 取本匹配）
_MANA_START_RE = re.compile(
    r'(万象マナ|全ての職業で使用できるマナ|(?:自身の職業の)?マナ)を(\d+)つ持った状態で戦闘を開始')
# 生产侧未确认族（不登记主张）：必殺技 boost／時の楔；素マナ前的職種・使用・戦場限定词
_MANA_START_REJECT = ('必殺技', '時の楔')
_MANA_START_PLAIN_BLOCK = ('戦士', '騎士', '弓使い', '僧侶', '魔法使い', '魔神', '天魔',
                           '使用でき', '使え', '戦場に')

# マナB 批（2026-10-26，主持裁决）：两个**来源限定**开局句式分支——只在同一行已有
# 合格 26 答案时登记主张；无合格答案的行不登记（30236/30239 零触碰前提）。
# 句式精确锚定行首；仍拒绝 Chain/コスト/スロット/所持/消費/WAVE/地形/撃破/時の楔 等族。
# 第二周期整改 R02（2026-10-26 第三方审查）：B 档分支必须校验本批 scope/family/binding
# 标记（``binding.mana_b_binding``）；映射批三键答案不要求该标记（不得误杀 1,209 条）。
_MANA_B_SCOPE = 'MANA_B_BATCH_20261026'
_MANA_B_FAMILIES = ('start_boost', 'start_job')
_MANA_B_JOBWORD = r'(?:戦士|弓使い|魔法使い|僧侶|騎士)'
_MANA_B_JOBSEQ = _MANA_B_JOBWORD + r'(?:(?:と|か|、|または)' + _MANA_B_JOBWORD + r')*'
_MANA_B_S1_RE = re.compile(
    r'^全ての必殺技が使えるマナを(\d+)つ持った状態で戦闘を開始')
_MANA_B_JOB_BOOST_RE = re.compile(
    r'^(' + _MANA_B_JOBSEQ + r')の全ての必殺技が使えるマナを(\d+)つ持った状態で戦闘を開始')
_MANA_B_JOB_USABLE_RE = re.compile(
    r'^(' + _MANA_B_JOBSEQ + r')(?:で使用できる|の性質を持った)マナを(\d+)つ持った状態で戦闘を開始')
_MANA_B_BLOCK = ('Chain', 'チェイン', 'コスト', 'スロット', '所持', '消費', '必要',
                 'WAVE', '地形', '撃破', '倒し', '時の楔')
# R02：普通开局句式前的前缀触发词（Chain/スロット/コスト）——同子句「前缀＋开局后缀」
# 不得当作开局主张（合成反例 1stChain以上／マナスロットで／コストが低い時）。只在**同一
# 子句匹配点之前**判词，故 7211「…マナスロットのマナ数が多いほど…」的合法开局部分保留
#（スロット 在其后）；不用整行黑名单。
_MANA_START_PREFIX_BLOCK = ('Chain', 'チェイン', 'スロット', 'コスト')


def _mana_start_claim_text(text: str):
    """子句→(slot, number, local_span, snippet, gate)|None。

    三个已确认句式（映射批，gate='mapping'）＋マナB 两个来源限定句式（gate='mana_b'；
    S1 boost→param4；S2 职业限定 boost/usable/性質→auto＝按唯一合格答案取 param0 或
    param4）。新分支仍拒绝 Chain/コスト/スロット/所持/消費/WAVE/地形/撃破/時の楔 等未确认族；
    R02 起普通句式的前缀带 Chain/スロット/コスト 也拒绝（同子句前缀＋开局后缀形态）。
    """
    if not any(w in text for w in _MANA_B_BLOCK):
        m = _MANA_B_JOB_BOOST_RE.search(text) or _MANA_B_JOB_USABLE_RE.search(text)
        if m:
            return 'auto', int(m.group(2)), [m.start(), m.end()], m.group(0), 'mana_b'
        m = _MANA_B_S1_RE.search(text)
        if m:
            return 'param4', int(m.group(1)), [m.start(), m.end()], m.group(0), 'mana_b'
    if any(w in text for w in _MANA_START_REJECT):
        return None
    m = _MANA_START_RE.search(text)
    if not m:
        return None
    prefix = text[:m.start()]
    if any(w in prefix for w in _MANA_START_PREFIX_BLOCK):
        return None
    head = m.group(1)
    if head == '万象マナ':
        slot = 'param7'
    elif head == '全ての職業で使用できるマナ':
        slot = 'param4'
    else:
        if any(w in prefix for w in _MANA_START_PLAIN_BLOCK):
            return None
        slot = 'param0'
    return slot, int(m.group(2)), [m.start(), m.end()], m.group(0), 'mapping'


def _mana_b_marker_ok(answer: dict, slot: str):
    """R02：B 档开局分支的绑定门——本批 scope／family／slot／record_id 与答案一致。"""
    binding = answer.get('binding') if isinstance(answer.get('binding'), dict) else None
    marker = (binding or {}).get('mana_b_binding') if isinstance(binding, dict) else None
    if not isinstance(marker, dict):
        return False
    if marker.get('scope') != _MANA_B_SCOPE:
        return False
    if marker.get('family') not in _MANA_B_FAMILIES:
        return False
    if marker.get('slot') != slot:
        return False
    marker_rid, answer_rid = marker.get('record_id'), answer.get('record_id')
    if marker_rid is None:
        # 开局分支（start_boost/start_job）标记不写 record_id；scope/family/slot 足够。
        return True
    if isinstance(marker_rid, bool) or not isinstance(marker_rid, int):
        return False
    return marker_rid == answer_rid


def _mana_start_answer_slots(row: dict):
    """行内三键来源合格答案 → {slot: [(int_value, answer_index, mana_b_marked), ...]}。

    第三项＝该答案是否带本批 ``binding.mana_b_binding``（scope/family/slot/record_id 一致）；
    B 档开局分支只消费 marked 项，映射批分支不要求（R02）。
    """
    out = collections.defaultdict(list)
    for idx, a in enumerate(row.get('answers') or []):
        slot = MANA_START_RULE_KEYS.get(a.get('rule_key'))
        if slot is None or a.get('field_path') != '/' + slot:
            continue
        if a.get('table') != 'skilllist':
            continue
        rid = a.get('record_id')
        if not isinstance(rid, int) or isinstance(rid, bool):
            continue
        if '玛那数量' not in str(a.get('quantity_kind') or ''):
            continue
        raw = a.get('raw_value')
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            continue
        if int(raw) != raw or raw < 1:
            continue
        if str(a.get('status') or '') == 'unresolved':
            continue
        if '未知' in str(a.get('numeric_evidence') or '')                 or '未知' in str(a.get('association_evidence') or ''):
            continue
        out[slot].append((int(raw), idx, _mana_b_marker_ok(a, slot)))
    return out
# rule_key 未命中时按 quantity_kind/value 词面回退（顺序敏感；审查 goal_alignment.py:10 同法）。
# DS-GR-07 修复（20261023）：「伤害」先于「攻击/攻撃」——「远程通常攻击伤害效果量百分比」
# 类答案此前词面命中「攻击」被映射为攻撃力（84 条，应归ダメージ）；伤害语义优先于攻击词面。
# 全库模拟核对：改动后当前已匹配答案零翻转（无既有攻撃力匹配被改道）；词面改道共 226 处
# ＝84 条攻撃力→ダメージ＋142 条此前无映射→ダメージ（DS-GR-R5 计数口径，20261023 复验
# 更正：142 中 124 条获得 has_answer、18 条成为新 S4 未对应主张登记）；均只影响账本归属，
# 页面答案值零变化。对象维度的后续修正见 _DAMAGE_TYPES/_answer_object（DS-GR-R1）。
_QK_KEYWORDS = (('必杀技威力', '威力（词表外）'), ('必殺技威力', '威力（词表外）'),
                ('暴击威力', 'クリティカル威力'), ('暴击发生率', 'クリティカル発生率'),
                ('回复量', 'HP回復'), ('回复', 'HP回復'), ('回復量', 'HP回復'),
                ('暴击率', 'クリティカル発生率'), ('暴击概率', 'クリティカル発生率'),
                ('暴击伤害', 'クリティカル威力'), ('暴伤', 'クリティカル威力'),
                ('伤害', 'ダメージ（词表外）'),
                ('移动', '移動速度'), ('移動', '移動速度'),
                ('固定防御', '防御力'), ('受伤', '防御力'), ('防御', '防御力'),
                ('攻击', '攻撃力'), ('攻撃', '攻撃力'),
                ('持续时间', '継続時間'), ('时长', '継続時間'))
# R2 复审整改第二轮补齐（DeepSeek 复验 R2-S2-CONSUMPTION-319，20261023）：新增前四组——
# 必杀技威力→威力（词表外）、暴击威力→クリティカル威力、暴击发生率→クリティカル発生率、
# 回复量→HP回復（与既有「回复」同目标）。审计口径：319 行（314 same_full_label＋5 混合）
# 的同标签有效结构化答案此前因类型未识别未被同子句主张消费（消费链断裂，非无答案）；
# 补齐后由同子句威力/クリティカル威力/HP回復 主张消费。全库 qk 扫描（223 种）确认新增
# 关键词此前不命中任何已映射 qk（零既有映射翻转）；批 8 暴击答案（2012 p4/p5 的
# 「暴击概率加算贡献」「暴击伤害系数加算贡献」）仍命中其既有键（暴击概率/暴击伤害），
# 消费关系零冲突（重建后 349 等批 8 行回归验证）。泛化 qk（效果量百分比/效果固定量，
# 数值类型不确定）不映射——由 _resolve_digit 的精确同标签结构化回退按位置绑定数字。


def _nfkc(t: str) -> str:
    return unicodedata.normalize('NFKC', t or '')


def _short_sha(t: str) -> str:
    return hashlib.sha256(t.encode('utf-8')).hexdigest()[:16]


def _boundary_attrs(s: str, words):
    """批 9 _sentence_attrs（b9:234-239）同一 ``(?<!属性)`` 负向断言，推广到任意词表。"""
    return [w for w in words if re.search(r'(?<!属性)' + re.escape(w), s)]


def _direction(clause: str):
    if any(v in clause for v in _UP_VERBS):
        return 'up'
    if any(v in clause for v in _DOWN_VERBS):
        return 'down'
    return None


def _s5_chance_answer_slots(row: dict):
    """本批概率玛那合格答案（来源限定）：rule_key/field_path/table/scope/数量类型一致。

    返回 ``(slot, answer_index, answer, scope)``；非地形段（param0/1/2）与地形段
    （param4/param5）按各自 scope 取各自槽位，互不相交。
    """
    out = []
    for idx, a in enumerate(row.get('answers') or []):
        binding = a.get('binding') if isinstance(a.get('binding'), dict) else {}
        s5 = binding.get('s5_binding') if isinstance(binding.get('s5_binding'), dict) else {}
        slots_map = _S5_SCOPE_SLOTS.get(s5.get('scope'))
        if slots_map is None:
            continue
        slot = slots_map.get(a.get('rule_key'))
        if slot is None or a.get('field_path') != '/' + slot:
            continue
        if a.get('table') != 'skilllist':
            continue
        if s5.get('record_id') != a.get('record_id'):
            continue
        if slot not in (s5.get('slots') or []):
            continue
        if '玛那概率阈值' not in str(a.get('quantity_kind') or ''):
            continue
        raw = a.get('raw_value')
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            continue
        if not (0.0 <= float(raw) <= 1.0):
            continue
        out.append((slot, idx, a, s5.get('scope')))
    return out


def _s5_relative_answer_slots(row: dict):
    """获珠相对句批（2026-10-29）：带 ``binding.s5_relative_binding`` 标记的归位答案。

    守卫逐项一致才消费：标记 scope＝S5_NONTERRAIN_20261026、标记含 base_row_id/slots、
    rule_key↔槽位、field_path、table=skilllist、record_id＝标记的 base_record_id、
    quantity_kind 含「玛那概率阈值」、raw 有限且在 0..1。无标记答案（含旧页全部答案）不入选。
    返回 ``(slot, answer_index, answer)``。
    """
    out = []
    for idx, a in enumerate(row.get('answers') or []):
        binding = a.get('binding') if isinstance(a.get('binding'), dict) else {}
        rel = binding.get(S5_RELATIVE_MARK) if isinstance(binding, dict) else None
        if not isinstance(rel, dict) or rel.get('scope') != S5_SCOPE:
            continue
        slot = S5_RULE_SLOTS.get(a.get('rule_key'))
        if slot is None or a.get('field_path') != '/' + slot:
            continue
        if a.get('table') != 'skilllist':
            continue
        if slot not in (rel.get('slots') or []):
            continue
        if not rel.get('base_row_id') or a.get('record_id') != rel.get('base_record_id'):
            continue
        if '玛那概率阈值' not in str(a.get('quantity_kind') or ''):
            continue
        raw = a.get('raw_value')
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            continue
        if not (0.0 <= float(raw) <= 1.0):
            continue
        out.append((slot, idx, a))
    return out


def _s5_terrain_claim_clauses(clauses):
    """地形段主张覆盖的子句索引：地形条件子句＋其后连续的玛那/接续子句。

    不覆盖条件之前的击杀基础概率子句（5092/7546），也不越过第一个无关子句
    （5092 的「さらに騎士マナか弓使いマナ…」）。无地形条件子句返回 None。
    """
    conds = [ci for ci, (clause, _span) in enumerate(clauses)
             if _S5T_COND_RX.match(clause.strip())]
    if not conds:
        return None
    covered = [conds[-1]]
    j = conds[-1] + 1
    while j < len(clauses):
        core = clauses[j][0]
        for c in _CONNECTIVES:
            if core.startswith(c):
                core = core[len(c):]
                break
        if not core.strip():
            covered.append(j)
            j += 1
            continue
        if _S5T_MANA_RX.search(core) or _S5T_COND_RX.match(core.strip()):
            covered.append(j)
            j += 1
            continue
        break
    return covered


def _s5_trigger_clause_ok(clause: str):
    """击杀触发子句（允许 クリティカル/必殺技/通常攻撃/自身/接续词 等限定）；
    夹带台词或其它子句内容时不覆盖（避免把 flavor 一并算作已覆盖）。"""
    core = clause.strip('。、！？ \n')
    for c in _CONNECTIVES:
        if core.startswith(c):
            core = core[len(c):]
    m = _S5_KILL_RE.search(core)
    if not m:
        return False
    resid = core[:m.start()] + core[m.end():]
    for w in _S5_TRIGGER_QUALIFIERS:
        resid = resid.replace(w, '')
    return resid.strip('。、！？ \n') == ''


def _answer_effect_type(answer: dict):
    """答案→效果类型映射；返回 (type|None, basis)。"""
    rk = answer.get('rule_key')
    binding = answer.get('binding') if isinstance(answer.get('binding'), dict) else {}
    ge = binding.get('gold_exp_binding') if isinstance(binding, dict) else None
    if isinstance(ge, dict) and ge.get('scope') == _GE_SCOPE:
        hit = _GE_RULE_SLOTS.get(rk)
        if (hit is not None and answer.get('field_path') == '/param0'
                and hit[0] == ge.get('ability') and ge.get('rule_key') == rk
                and answer.get('record_id') == ge.get('carrier_record_id')
                and answer.get('layer') == ge.get('carrier_layer')):
            return hit[1], ('金币/经验批：binding.gold_exp_binding 来源限定（scope/ability/'
                            'rule_key/载体记录逐项一致；不整族映射 skilllist 100/102）')
    t8096 = binding.get('type80_96_binding') if isinstance(binding, dict) else None
    if isinstance(t8096, dict) and t8096.get('scope') == _T8096_SCOPE:
        slot = (answer.get('field_path') or '').lstrip('/')
        etype = (_T8096_SLOT_EFFECT.get(t8096.get('ability')) or {}).get(slot)
        if (etype is not None and t8096.get('slot') == slot
                and t8096.get('rule_key') == rk
                and t8096.get('family') in _T8096_FAMILIES
                and answer.get('record_id') == t8096.get('carrier_record_id')
                and answer.get('layer') == t8096.get('carrier_layer')):
            return etype, ('type80/96 成对批：binding.type80_96_binding 来源限定'
                           '（scope/形态/槽/rule_key/载体记录与层逐项一致；'
                           '不整族映射 skilllist 80/96）')
    hb = binding.get('heal_interval_binding') if isinstance(binding, dict) else None
    if isinstance(hb, dict) and hb.get('scope') == _HI_SCOPE:
        hit = _HI_RULE_SLOTS.get(rk)
        if (hit is not None and hb.get('ability') == hit[0] and hb.get('slot') == hit[1]
                and hb.get('rule_key') == rk
                and answer.get('field_path') == '/' + hit[1]
                and answer.get('record_id') == hb.get('carrier_record_id')
                and answer.get('layer') == hb.get('carrier_layer')):
            return _HI_EFFECT, ('回复间隔两段乘数批：binding.heal_interval_binding 来源限定'
                                '（scope/ability/槽/载体记录逐项一致；只绑到句面「回復速度」处的'
                                '既有回復主张，不整族映射 skilllist 19/1033）')
    g0g7 = _g0g7_binding_of_answer(answer)
    if g0g7:
        family, gb = g0g7
        hit = (_G0G7_RULE_SLOTS.get(family) or {}).get(rk)
        if (hit is not None and gb.get('slot') == hit[0]
                and gb.get('rule_key') == rk
                and answer.get('field_path') == '/' + hit[0]
                and answer.get('record_id') == gb.get('carrier_record_id')
                and answer.get('layer') == gb.get('carrier_layer')):
            return hit[1], ('G0-B1／G7-B0 合并小批：binding.g0g7_binding 来源限定'
                            '（scope/形态/槽/rule_key/载体记录与层逐项一致＋span/子句逐值相等；'
                            '不整族映射 skilllist 29／1008）')
    s5 = binding.get('s5_binding') if isinstance(binding.get('s5_binding'), dict) else {}
    _s5_slots = _S5_SCOPE_SLOTS.get(s5.get('scope'))
    if (_s5_slots is not None and rk in _s5_slots
            and answer.get('field_path') == '/' + _s5_slots[rk]
            and '玛那概率阈值' in str(answer.get('quantity_kind') or '')):
        return S5_CHANCE_TYPE, 'S5 概率玛那：binding.s5_binding 来源限定（occurrences=1 类型外推）'
    # G1-B1 必殺ダメージ镜像行绑定批（2026-10-29，来源限定窄映射；见模块头注）：
    # 只认带 binding.g1_b1_binding（scope 精确）且 rule_key/槽/载体记录/层逐项一致的答案；
    # 只补 6 个既有确认规则键，不整族映射 bossskill，无标记行行为零变化。
    g1b1 = binding.get('g1_b1_binding') if isinstance(binding, dict) else None
    if isinstance(g1b1, dict) and g1b1.get('scope') == G1B1_SCOPE:
        hit = G1B1_RULE_EFFECT.get(rk)
        if (hit is not None
                and g1b1.get('rule_key') == rk
                and answer.get('field_path') == g1b1.get('field_path')
                and answer.get('table') == 'bossskill'
                and answer.get('record_id') == g1b1.get('record_id')
                and answer.get('layer') == g1b1.get('layer')):
            return hit, ('G1-B1 镜像行绑定批：binding.g1_b1_binding 来源限定'
                         '（scope/rule_key/槽/载体记录与层逐项一致；只补 6 个既有确认规则键，'
                         '不整族映射 bossskill）')
    # C8-P1 t27 周期回复批（2026-10-30，来源限定窄映射；见模块头注）：
    # 只认带 binding.c8_p1_t27_binding（scope 精确）且 rule_key/槽/表/载体记录/层逐项一致的
    # 答案；只补『回復（词表外）』一词表主张，不整族映射 type27，无标记行行为零变化。
    t27 = binding.get('c8_p1_t27_binding') if isinstance(binding, dict) else None
    if isinstance(t27, dict) and t27.get('scope') == C8P1_T27_SCOPE:
        if (rk == C8P1_T27_RULE_KEY and t27.get('rule_key') == rk
                and answer.get('field_path') == '/skillparam1'
                and answer.get('table') == 'bossskill'
                and answer.get('record_id') == t27.get('record_id')
                and answer.get('layer') == t27.get('layer')):
            return C8P1_T27_EFFECT, ('C8-P1 周期回复批：binding.c8_p1_t27_binding 来源限定'
                                     '（scope/rule_key/槽/表/载体记录与层逐项一致；只补一条'
                                     '既有词表主张，不整族映射 type27）')
    # C10-P1 skilltext 镜像整理批（2026-10-30，来源限定窄映射；见模块头注）：
    # 只认带 binding.c10_p1_mirror_binding（scope 精确）且 rule_key/槽/表/载体记录/层逐项一致的
    # 答案；只补『回復（词表外）』一词表主张，不整族映射 type27，无标记行行为零变化。
    c10 = binding.get('c10_p1_mirror_binding') if isinstance(binding, dict) else None
    if isinstance(c10, dict) and c10.get('scope') == C10P1_T27_SCOPE:
        if (rk == C10P1_T27_RULE_KEY and c10.get('rule_key') == rk
                and answer.get('field_path') == '/skillparam1'
                and answer.get('table') == 'bossskill'
                and answer.get('record_id') == c10.get('record_id')
                and answer.get('layer') == c10.get('layer')):
            return C10P1_T27_EFFECT, ('C10-P1 skilltext 镜像整理批：binding.c10_p1_mirror_binding '
                                     '来源限定（scope/rule_key/槽/表/载体记录与层逐项一致；只补一条'
                                     '既有词表主张，不整族映射 type27）')
    # C13-P2：只认本批 skilltext 镜像 binding；不消费 p2/p3，不改 C8/C10 分支。
    # binding、答案顶层与 source 必须同源一致；缺字段、错槽或来源矛盾均不得消费。
    c13p2 = binding.get('c13_p2_t27_mirror_binding') if isinstance(binding, dict) else None
    if isinstance(c13p2, dict) and c13p2.get('scope') == C13P2_T27_SCOPE:
        source = answer.get('source') or {}
        if (rk == C13P2_T27_RULE_KEY and c13p2.get('rule_key') == rk
                and c13p2.get('field_path') == answer.get('field_path') == source.get('field_path') == source.get('field') == '/skillparam1'
                and c13p2.get('table') == answer.get('table') == source.get('table') == 'bossskill'
                and type(c13p2.get('record_id')) is int and c13p2.get('record_id') > 0
                and c13p2.get('record_id') == answer.get('record_id') == source.get('record_id')
                and c13p2.get('layer')
                and c13p2.get('layer') == answer.get('layer') == source.get('layer')
                and c13p2.get('carrier_slot') == 'skillid0'
                and source):
            return C13P2_T27_EFFECT, ('C13-P2 t27 skilltext 镜像：binding.c13_p2_t27_mirror_binding '
                                     '来源限定（scope/rule_key/槽/表/载体记录与层逐项一致；只补一条'
                                     '既有回复主张，不整族映射 type27）')
    if (rk in ('skilllist|7|/param7', 'skilllist|2012|/param6', 'skilllist|1016|/param6',
               'skilllist|56|/param9','bossskill|68|/skillparam9','bossskill|118|/skillparam9')
            or answer.get('quantity_kind') == '攻击间隔乘数'):
        return '攻撃間隔（词表外）', '攻速字段精确键；速度词面归属须受控行绑定'
    if rk:
        hit = _RULE_KEY_EFFECT.get(rk)
        if hit:
            return hit, (_RULE_KEY_EFFECT_BASIS.get(rk)
                         or 'rule_key 映射表（各推断批次句式→槽位映射，见模块头注）')
    for probe in (answer.get('quantity_kind') or '', answer.get('value') or ''):
        for kw, eff in _QK_KEYWORDS:
            if kw in probe:
                return eff, (f'quantity_kind/value 词面回退（关键词「{kw}」；'
                             '审查 goal_alignment.py:10 taxonomy 同法）')
    return None, None


def _attack_interval_binding(row, answer_index, answer):
    """Only producer-validated source/span bindings may consume attack cadence claims."""
    marker = row.get('attack_interval') or {}
    if marker.get('contribution_only'):
        return None  # StopUp does not establish the preceding unconditional base interval.
    if marker.get('scope') not in ('ATTACK_INTERVAL_BATCH1_LOCAL_FORMULA_ONLY',
                                   'ATTACK_INTERVAL_BATCH2_LOCAL_FORMULA_ONLY',
                                   'ATTACK_INTERVAL_BATCH3_LOCAL_FORMULA_ONLY'):
        return None
    original_source = answer.get('source') or {}
    allowed = {'skilllist|7|/param7': '/param7', 'skilllist|2012|/param6': '/param6'}
    if marker.get('scope') == 'ATTACK_INTERVAL_BATCH2_LOCAL_FORMULA_ONLY':
        allowed['skilllist|1016|/param6'] = '/param6'
    if marker.get('scope') == 'ATTACK_INTERVAL_BATCH3_LOCAL_FORMULA_ONLY':
        allowed={'skilllist|56|/param9':'/param9',
            'bossskill|68|/skillparam9':'/skillparam9','bossskill|118|/skillparam9':'/skillparam9'}
    matches = []
    text = _nfkc(row.get('japanese'))
    for b in marker.get('bindings', []):
        key = answer.get('rule_key')
        source = original_source
        raw = answer.get('raw_value')
        if isinstance(source, list):
            # The reviewed legacy answer is immutable and carries field proofs
            # in a list rather than top-level raw/rule fields.
            if (answer.get('effect_id') != 'other_a2_attack_interval'
                    or answer.get('quantity_kind') != '攻击间隔乘数'
                    or answer.get('numeric_evidence') != '确认'
                    or b.get('rule_key') != 'skilllist|7|/param7'):
                continue
            proofs = [s for s in source if isinstance(s, dict)
                      and s.get('present') is True and s.get('ability_type') == 7
                      and s.get('field_path') == '/param7'
                      and s.get('record_key') == b.get('record_key')]
            if len(proofs) != 1:
                continue
            source = proofs[0]; raw = source.get('raw_value');key = b['rule_key']
        field = allowed.get(key)
        if (not isinstance(source, dict) or field is None or isinstance(raw, bool)
                or not isinstance(raw, (int, float)) or not math.isfinite(raw)
                or source.get('layer') != 'CACHE' or source.get('table') != key.split('|')[0]
                or source.get('field_path') != field):
            continue
        if (key == 'skilllist|7|/param7' and raw <= 0
                or key=='skilllist|56|/param9' and not 0<raw<1
                or key in ('skilllist|2012|/param6','skilllist|1016|/param6',
                           'bossskill|68|/skillparam9','bossskill|118|/skillparam9') and raw >= 0):
            continue  # This batch's source-qualified acceleration domain only.
        if (b.get('answer_index') != answer_index or b.get('row_id') != row.get('row_id')
                or b.get('rule_key') != key or b.get('effect_type') not in
                ('攻撃間隔（词表外）', '攻撃速度（词表外）')):
            continue
        if any(b.get(k) != source.get(k) or source.get(k) is None
               for k in ('layer', 'table', 'record_id', 'field_path', 'record_key')):
            continue
        span = b.get('span')
        if (not isinstance(span, list) or len(span) != 2
                or not all(isinstance(x, int) for x in span)
                or not 0 <= span[0] < span[1] <= len(text)
                or text[span[0]:span[1]] != b['effect_type'].split('（')[0]):
            continue
        matches.append(b)
    return matches[0] if len(matches) == 1 else None


def _answer_direction(answer: dict):
    """方向判定：先按规则键固定映射（p9＝防御力下降的表现层，见 _RULE_KEY_DIRECTION 依据），
    再对加算类数量按原值符号；其余不猜方向。"""
    rk = answer.get('rule_key')
    if rk and rk in _RULE_KEY_DIRECTION:
        return _RULE_KEY_DIRECTION[rk]
    kind = answer.get('quantity_kind') or ''
    if '加算' in kind:
        raw = answer.get('raw_value')
        if isinstance(raw, (int, float)):
            return 'up' if raw > 0 else ('down' if raw < 0 else None)
    return None


# ---- R2 复审整改（20261023 第二轮）：数字→角色绑定 -----------------------------------
# 根因（复审 §R2a）：旧 _digit_mapping 首环只要数字等于整行任一答案 raw 或其百分比即映射，
# 无数量角色/语义位置核对——349 前置「HPが30%以上のとき」的 30 被映射到既有暴击答案
# raw 0.3×100 判完整（HP40% 又判待核查——判定依赖数字碰巧相等，非语义）。
# 修复口径：先判数字的文本角色（条件提示→条件角色；效果谓词语境→效果量角色；
# Nst/nd/rd/th→对象选择），再按角色匹配答案/证据的 quantity_kind/单位/换算口径与
# 文本位置（效果量角色要求答案被同子句主张消费）。数值相等仅为必要线索，角色不符不映射。
_ROLE_CLASS_QK_KEYWORDS = {
    'threshold': ('阈值',), 'probability': ('概率', '確率'),
    'duration': ('时长', '持续', '時間', '継続'), 'limit': ('上限',),
    'count': ('次数',), 'quantity': ('数量',),
    # effect_amount 别名不走此表（R2-ROLE-ALIAS-105：改为 _AMOUNT_SUBTYPE_TABLE 同子类型）
    'effect_amount': (),
    'heal': ('回复', '回復'), 'multiplier': ('倍',), 'mana': ('玛那', 'マナ', '费用'),
    'ordinal': (), 'narrative': (), 'other': (),
}


def _digit_role_class(label):
    """角色标签→角色类别（有限判定表；顺序即优先级，先具体后一般）。"""
    if not label:
        return None
    if '序数' in label:
        return 'ordinal'
    if '叙述' in label:
        return 'narrative'
    if '阈值' in label:
        return 'threshold'
    if '確率' in label or '概率' in label:
        return 'probability'
    if '上限' in label:
        return 'limit'
    if '效果量' in label:
        return 'effect_amount'
    if '回复' in label or '回復' in label:
        return 'heal'
    if '时长' in label:
        return 'duration'
    if '次数' in label:
        return 'count'
    if '数量' in label:
        return 'quantity'
    if '玛那' in label or 'マナ' in label or '费用' in label:
        return 'mana'
    if '倍' in label:
        return 'multiplier'
    return 'other'


def _core_role(label):
    """剥离主体/所属前缀（「味方全体/攻击力效果量百分比」→「攻击力效果量百分比」）；
    card_page_data 角色标签的「/」语义即主体限定，数量类型在最后一段。"""
    return (label or '').split('/')[-1]


# R2 复审整改第二轮（DeepSeek R2-ROLE-ALIAS-105）：effect_amount 类别别名收紧——
# 旧别名表只看「效果量」字面，使「必杀技威力/暴击威力效果量百分比」角色可配
# 「攻击力效果量百分比」答案（105 行旧映射即此类子类型错配）。收紧：效果量别名须
# **同子类型**（威力↔威力、攻击↔攻击、回复↔回复…）；子类型识别词表如下（长词优先，
# 双语收录；数值类型不确定的泛化标签「效果量百分比/效果固定量」无子类型——别名不放行，
# 仅精确包含路径可用）。
_AMOUNT_SUBTYPE_TABLE = (
    ('必杀技威力', '威力'), ('必殺技威力', '威力'),
    ('暴击威力', 'クリティカル威力'), ('暴击伤害', 'クリティカル威力'), ('暴伤', 'クリティカル威力'),
    ('暴击发生率', 'クリティカル発生率'), ('暴击率', 'クリティカル発生率'),
    ('暴击概率', 'クリティカル発生率'),
    ('攻击力', '攻撃'), ('攻撃力', '攻撃'),
    ('固定防御', '防御'), ('防御力', '防御'), ('受伤', '防御'), ('防御', '防御'),
    ('移動速度', '移動'), ('移动速度', '移動'), ('移动', '移動'), ('移動', '移動'),
    ('回复量', '回复'), ('回復量', '回复'), ('回复', '回复'), ('回復', '回复'),
    ('ダメージ', '伤害'), ('伤害', '伤害'),
)


def _amount_subtype(label):
    """效果量标签→数量子类型（长词优先；无子类型返回 None＝泛化，别名不放行）。"""
    core = _core_role(label)
    for kw, canon in _AMOUNT_SUBTYPE_TABLE:
        if kw in core:
            return canon
    return None


def _role_qk_compat(role_label, role_class, qk):
    """角色↔答案 quantity_kind 兼容性：核心段包含（双向）优先；effect_amount 的类别别名
    收紧为同子类型（_AMOUNT_SUBTYPE_TABLE）；其余类别沿用有限别名表。"""
    qk = str(qk or '')
    if not qk or role_class == 'narrative' or role_class == 'ordinal':
        return False
    cr, cq = _core_role(role_label), _core_role(qk)
    if cr and cq and (cr in cq or cq in cr):
        return True
    if role_class == 'effect_amount':
        sr, sq = _amount_subtype(role_label), _amount_subtype(qk)
        return sr is not None and sq is not None and sr == sq
    return any(kw in qk for kw in _ROLE_CLASS_QK_KEYWORDS.get(role_class, ()))


def _digit_num_eq(lit, rv):
    """数值相等（必要线索，非充分）：原值相等或百分比口径（raw×100）相等；原文数字串同值。"""
    try:
        if isinstance(rv, bool):
            return False
        if isinstance(rv, (int, float)):
            v = float(lit)
            return abs(v - float(rv)) < 1e-9 or abs(v - float(rv) * 100) < 1e-9
        return abs(float(lit) - float(rv)) < 1e-9
    except (ValueError, TypeError):
        return False


def _digit_text_role(lit, clause, dstart):
    """无原文数字项（original_numeric_items）时的子句词形角色回退——有限可审计模式，
    逐字匹配；不识别的词形返回 None（不映射，并入 S2），不做泛化猜测。
    dstart＝该数字 token 在子句内的起点（角色按本处出现位置的上下文判定，不全文搜索）。"""
    if re.match(re.escape(lit) + r'(?:st|nd|rd|th)', clause[dstart:]):
        return '对象选择（序数词形）'
    right = clause[dstart + len(lit):dstart + len(lit) + 8]
    if re.match(r'\s*%?\s*(?:以上|以下|未満|より|を超え)', right):
        left = clause[max(0, dstart - 8):dstart]
        # text_n 已 NFKC——全角ＨＰ归一为 ASCII HP（与 card_page_data 标签口径一致）
        if re.search(r'(?:残り)?[Hｈ][Pｐ][がは]?$', left):
            return 'HP条件阈值'
        return '条件阈值'
    if re.match(r'%?の?確率', right) or re.search(r'確率[^、。]{0,6}$', clause[:dstart]):
        return '確率（句面概率值）'
    if re.match(r'回まで', right):
        return '次数上限'
    if re.match(r'秒(?:間)?', right):
        return '时长'
    if re.match(r'回', right):
        return '次数'
    return None


def analyze_row(row: dict, table: str | None = None):
    """对一条描述做词面效果拆分＋答案匹配，返回账本行结构（未含快照锚点）。

    table（R1 整改 20261023 新增，可选）：行命名空间表名（_emit_row 传 skill.table）——
    仅 charainfo/denju 两表参与「HP 变量句未绑定」完成判定（bosspattern 行源记录即分支
    记录、dlb/heroic 无 pattern 引用，均豁免）。"""
    row_id = row['row_id']
    text_n = _nfkc(row['japanese'])
    clauses = [(m.group(0), [m.start(), m.end()]) for m in _CLAUSE_RE.finditer(text_n)]
    refs, claims, claim_by_clause = [], [], {}
    covered_clause_idx = set()
    # マナ：来源限定主张的合格答案池（三键精确；见模块头注 §マナ账本映射批）
    mana_answers = _mana_start_answer_slots(row)

    # ---- 逐子句：效果主张＋条件/对象共享引用 ----------------------------------------
    for ci, (clause, span) in enumerate(clauses):
        core = clause
        for c in _CONNECTIVES:
            if core.startswith(c):
                core = core[len(c):]
        if not core.strip():
            covered_clause_idx.add(ci)   # 纯连接词子句不构成内容
            continue
        here = []                        # 本子句主张
        cdir = _direction(clause)
        # 对象维度（DS-GR-R1）：句面词面分类，供ダメージ 类主张的匹配约束与 c15 内容级核对
        cobj = _clause_object(clause)
        m = _HP_HEAL_RE.search(clause)
        if m:
            sp = [span[0] + m.start(), span[0] + m.end()]
            here.append(dict(effect_type='HP回復', direction='up', clause_index=ci,
                             span=sp, snippet=text_n[sp[0]:sp[1]]))
        for m in _WORD_RE.finditer(clause):
            w = m.group(0)
            etype = _WORD_TYPE[w]
            if etype == _CRIT_POWER_RATE_SENTINEL:
                # 「…の威力と発生率」是一条句面中的两个明确子类型；分别登记数值主张，
                # 不复用旧的裸 crit，也不把二者互相替代。
                local = m.group(0)
                for part, part_type in (('威力', 'クリティカル威力'),
                                        ('発生率', 'クリティカル発生率')):
                    off = local.index(part)
                    sp = [span[0] + m.start() + off,
                          span[0] + m.start() + off + len(part)]
                    here.append(dict(effect_type=part_type, direction=cdir,
                                     clause_index=ci, span=sp, snippet=part))
                continue
            if w == 'クリティカル' and 'クリティカル攻撃' in clause:
                # 批18三修之一：攻擊時/がN回/で X 等是触发或机制上下文。保留为未解决
                # 机制主张，禁止冒充暴击率/暴伤，也不以 NA 或删除来“清账”。
                if not any(c.get('effect_type') == CRIT_ATTACK_MECHANISM for c in here):
                    mech = 'クリティカル攻撃'
                    off = clause.index(mech)
                    sp = [span[0] + off, span[0] + off + len(mech)]
                    here.append(dict(effect_type=CRIT_ATTACK_MECHANISM,
                                     direction=None, clause_index=ci,
                                     span=sp,
                                     snippet=text_n[sp[0]:sp[1]]))
                continue
            if w == 'クリティカル' and text_n[span[0] + m.end():span[0] + m.end() + 1] == '時':
                continue  # 「クリティカル時」为条件线索，不是暴击主张
            if etype == '回復（词表外）' and _HP_HEAL_RE.search(clause):
                continue  # 已由 HP回復 主张覆盖
            if etype == '効果（词表外）' and not _boundary_attrs(clause, ['効果']):
                continue  # 「属性効果」类边界守卫（与 b9 同法收窄）
            sp = [span[0] + m.start(), span[0] + m.end()]
            here.append(dict(effect_type=etype, direction=cdir, clause_index=ci,
                             span=sp, snippet=text_n[sp[0]:sp[1]],
                             **({'object': cobj} if etype in _DAMAGE_TYPES else {})))
        # 时长主张：增减谓词子句内的 一定時間/N秒（間）——一个子句一条时长主张（公共引用）
        if cdir:
            m = _DURATION_RE.search(clause)
            if m:
                sp = [span[0] + m.start(), span[0] + m.end()]
                here.append(dict(effect_type='継続時間', direction=None, clause_index=ci,
                                 span=sp, snippet=text_n[sp[0]:sp[1]], shared_duration=True))
        # マナ开局主张（来源限定）：句面三句式＋同槽位唯一来源合格答案，原值整数化＝句中数字
        if mana_answers:
            msc = _mana_start_claim_text(clause)
            if msc:
                slot, num, local, _snip, gate = msc
                # R02：B 档（新分支）只消费带本批 mana_b_binding 的答案；映射批三键
                # 答案不接受该门（零标记，1,209 条保留）。
                pool = ({s: [t for t in v if t[2]] for s, v in mana_answers.items()}
                        if gate == 'mana_b' else mana_answers)
                if slot == 'auto':
                    hits = [s for s in ('param0', 'param4')
                            if len(pool.get(s) or []) == 1
                            and pool[s][0][0] == num]
                    slot = hits[0] if len(hits) == 1 else None
                cands = pool.get(slot) or []
                if slot and len(cands) == 1 and cands[0][0] == num:
                    sp = [span[0] + local[0], span[0] + local[1]]
                    here.append(dict(effect_type=MANA_START_TYPE, direction=None, clause_index=ci,
                                     span=sp, snippet=text_n[sp[0]:sp[1]],
                                     mana_slot='/' + slot, mana_answer_index=cands[0][1]))
        if here:
            claim_by_clause[ci] = here
            covered_clause_idx.add(ci)
            claims.extend(here)
        for j, cue in enumerate(c for c in _CONDITION_CUES if c in clause):
            refs.append(dict(ref_id=f'r{ci:02d}#cond{j}', kind='condition', clause_index=ci,
                             span=span, text=cue))
        for j, subj in enumerate(s for s in _SUBJECT_WORDS if s in clause):
            refs.append(dict(ref_id=f'r{ci:02d}#subj{j}', kind='subject', clause_index=ci,
                             span=span, text=subj))
        # 次数上限引用（DS-GR 条件关联修复：319「3回まで」类——登记为 limit 引用）
        for j, m in enumerate(_LIMIT_RE.finditer(clause)):
            refs.append(dict(ref_id=f'r{ci:02d}#lim{j}', kind='limit', clause_index=ci,
                             span=span, text=m.group(0)))

    # ---- 数字覆盖：数字随所在子句主张登记（number_refs 公共引用）；映射在答案消费后
    #      按「角色绑定」解析（R2 复审整改 20261023 第二轮，见 _digit_role_class 等帮助
    #      函数头注）：每个数字先判文本角色（original_numeric_items 词面角色标签优先，
    #      无则子句词形回退），再按角色匹配答案 quantity_kind/单位/换算口径与文本位置
    #      （效果量角色要求答案被同子句主张消费）；数值相等仅为必要线索，角色不符不映射；
    #      无角色依据的数字不映射（并入 S2），叙述性数字永不映射。 ----
    number_refs, uncovered_digits = [], []
    oni = row.get('original_numeric_items') or []

    def _oni_item_for(lit, sp):
        """原文数字项对齐：span 相交（oni 坐标＝NFKC 后整行文本，与本函数 text_n 一致），
        其中值逐字相等者优先；范围值「1～6」等复合 token 按 span 相交取角色。"""
        cands = [it for it in oni
                 if (it.get('normalized_span') or [0, 0])[0] < sp[1]
                 and sp[0] < (it.get('normalized_span') or [0, 0])[1]]
        for it in cands:
            if str(it.get('value') or '') == lit:
                return it
        return cands[0] if cands else None

    for ci, (clause, span) in enumerate(clauses):
        for m in _DIGIT_RE.finditer(clause):
            sp = [span[0] + m.start(), span[0] + m.end()]
            ref = dict(ref_id=f'n{len(number_refs):02d}', kind='number', clause_index=ci,
                       span=sp, literal=m.group(0),
                       semantic_status='原文数字（角色解析中——映射随答案消费后按角色绑定判定）')
            oi = _oni_item_for(m.group(0), sp)
            if oi is not None and oi.get('role'):
                ref['original_numeric_role'] = oi.get('role')
                ref['role_label'] = oi.get('role')
                ref['role_unit'] = oi.get('unit')
                ref['role_source'] = 'original_numeric_items（card_page_data.py:136-224 词面角色标签）'
            else:
                ref['role_label'] = _digit_text_role(m.group(0), clause, m.start())
                ref['role_source'] = ('子句词形回退（effect_ledger._digit_text_role）'
                                      if ref['role_label'] else None)
            if ref.get('role_label'):
                ref['role_class'] = _digit_role_class(ref['role_label'])
            else:
                ref['role_class'] = None
            number_refs.append(ref)
            if ci in claim_by_clause:
                for c in claim_by_clause[ci]:
                    c.setdefault('number_ref_ids', []).append(ref['ref_id'])

    # ---- R2 整改（20261023 复审 §R2）：条件主张解析状态 --------------------------------
    # DS-GR 的条件引用此前「只登记关联、无解析状态」（复审 R2 对 86 的批评：把概率当作
    # 一个无解析状态的 condition 词条，不能证明已逐项完成）。升级：
    #   * 概率类（_PROBABILITY_CUES，句面隐藏数值）：须有答案注记/适用条件披露并解析出
    #     载体值（如 86：批 13 注记「载体 /param3=0.15000000596046448（…概率触发…概率值
    #     登记不分配）」→ 本处正式登记映射：值+字段+来源+证据档，推断档，各注来源）；
    #     无披露 → S6 待办（不重新描述为数值未知，也不以关键词登记结清）。
    #   * 范围/存在/状态/时机类：全句已陈述（无隐藏数值）→ 解析为句面限定（与主语/对象
    #     共享引用同依据）；答案注记另有披露的标 mapped 并注答案序号。
    def _answer_disclosure_indices(cue):
        return [i for i, a in enumerate(row['answers'])
                if cue in (str(a.get('note') or '') + ' ' + str(a.get('conditions') or '')
                           + ' ' + str(a.get('quantity_kind') or ''))]

    unresolved_conditions = []
    for ref in refs:
        if ref['kind'] != 'condition':
            continue
        cue = ref['text']
        disc = _answer_disclosure_indices(cue)
        if cue in _PROBABILITY_CUES:
            if ref['clause_index'] not in claim_by_clause:
                continue  # 无主张子句的条件引用已由 S1/S3 覆盖，不重复入队
            if disc:
                a0 = row['answers'][disc[0]]
                m = None
                for i in disc:
                    m = _CARRIER_PROB_RE.search(str(row['answers'][i].get('note') or ''))
                    if m:
                        a0 = row['answers'][i]
                        break
                src = a0.get('source') if isinstance(a0.get('source'), dict) else {}
                if m:
                    ref['resolution'] = dict(
                        status='mapped（推断）', kind='概率触发（载体参数，共享引用）',
                        value=float(m.group(2)), field_path=f'/param{m.group(1)}',
                        source=dict(table=src.get('table'), record_id=src.get('record_id'),
                                    layer=src.get('layer'), record_key=src.get('record_key')),
                        evidence_grade=a0.get('numeric_evidence'),
                        answer_indices=disc,
                        basis='答案注记披露的概率载体（原文形态「载体 /param%s=%s（…概率触发…）」'
                              '——登记不分配→本映射为正式登记；数值归属仍为推断档，'
                              '不升确认，各注来源' % (m.group(1), m.group(2)))
                else:
                    # R2-Low 复审整改（20261023）：注记披露「来源载体…分数概率阈值 V1/V2」
                    # 形态→结构化登记（多值；来源＝载体记录键）；仍无结构化披露→S6 待办。
                    m_car = m_thr = None
                    for i in disc:
                        n = str(row['answers'][i].get('note') or '')
                        mc, mt = _CARRIER_KEY_RE.search(n), _THRESH_LIST_RE.search(n)
                        if mc and mt:
                            m_car, m_thr = mc, mt
                            break
                    if m_car and m_thr:
                        vals = [float(x) for x in m_thr.group(1).split('/')]
                        ref['resolution'] = dict(
                            status='mapped（推断）',
                            kind='概率触发（注记披露载体阈值→结构化登记，多值/多字段）',
                            value=vals, field_path=None,
                            threshold_slot_correspondence=(
                                '阈值↔参数槽对应未逐行确认（三路门 Normal=p1/Skill=p3/'
                                'Critical=p2 为批 10 §2.1 既有类型语义，'
                                'b13_apkext_scope.md 登记口径）——本条登记注记披露的阈值'
                                '原值，不分配到具体槽、不并入任何效果值'),
                            source=dict(table='skilllist', record_id=int(m_car.group(2)),
                                        layer=m_car.group(3), record_key=m_car.group(1)),
                            evidence_grade=a0.get('numeric_evidence'),
                            answer_indices=disc,
                            basis='答案注记披露的概率载体（%s）与分数概率阈值（%s，原值逐字）'
                                  '→结构化登记；三路阈值为多值非单一载体值，数值归属仍为'
                                  '推断档，不升确认，各注来源'
                                  % (m_car.group(1), m_thr.group(1)))
                    else:
                        ref['resolution'] = None   # 落入下方 S6（披露不等于载体值已解析）
                        ref['disclosed_note'] = (
                            '答案注记/适用条件含该条件词面披露（答案序号 %s）但无可解析的'
                            '载体/阈值披露形态——披露不等于载体值已结构化' % disc)
                        unresolved_conditions.append(ref)
            else:
                unresolved_conditions.append(ref)
        else:
            ref['resolution'] = (dict(status='mapped', answer_indices=disc,
                                      basis='答案注记/适用条件披露该条件词面')
                                 if disc else
                                 dict(status='scope_qualifier',
                                      basis='句面逐字范围/存在/状态/时机限定——条件语义已由'
                                            '原句完整陈述（无独立数值载体主张）；本子句值行的'
                                            '适用条件继承句面（对象/主语共享引用同依据）'))

    # ---- S5 概率玛那主张（2026-10-26，主持裁决①；来源限定）--------------------------
    # 只有本批合格答案存在的行才登记主张：无答案行不新增未解决主张/拆分；30236/30239
    # 无本批答案，自然零触碰。一行可有多条概率子句（如 7527），合并为一条主张，覆盖
    # 全部概率玛那子句与击杀触发子句；夹带台词/其它子句的触发句不覆盖（仍留 S3）。
    s5_answers = _s5_chance_answer_slots(row)
    _s5_nt = [x for x in s5_answers if x[3] == S5_SCOPE]
    _s5_t = [x for x in s5_answers if x[3] == S5_TERRAIN_SCOPE]
    if _s5_nt and not any(c.get('effect_type') == S5_CHANCE_TYPE for c in claims):
        mana_cis = [ci for ci, (clause, _span) in enumerate(clauses)
                    if _S5_MANA_RX.search(clause)]
        if mana_cis:
            trigger_cis = [ci for ci, (clause, _span) in enumerate(clauses)
                           if _s5_trigger_clause_ok(clause)]
            sp0 = clauses[mana_cis[0]][1][0]
            sp1 = clauses[mana_cis[-1]][1][1]
            s5_claim = dict(effect_type=S5_CHANCE_TYPE, direction='up',
                            clause_index=mana_cis[0], span=[sp0, sp1],
                            snippet=text_n[sp0:sp1], s5_chance=True,
                            s5_answer_index=_s5_nt[0][1],
                            s5_slots=[x[0] for x in _s5_nt])
            claims.append(s5_claim)
            claim_by_clause.setdefault(mana_cis[0], []).append(s5_claim)
            covered_clause_idx.update(mana_cis)
            covered_clause_idx.update(trigger_cis)

    # ---- 获珠相对句主张（2026-10-29；来源限定，仅认 s5_relative_binding 标记）--------
    # 相对句「…で倒すと獲得しやすくなる。」句面无「マナ」，既有 _S5_MANA_RX 不匹配；
    # 只有带本批标记的答案行才登记一条確率マナ獲得主张，覆盖句面相对子句。无标记行
    # （旧页、其他族、范围外相对句）不新增主张，账本行为零变化。
    _s5_rel = _s5_relative_answer_slots(row)
    if _s5_rel and not any(c.get('effect_type') == S5_CHANCE_TYPE for c in claims):
        rel_cis = [ci for ci, (clause, _span) in enumerate(clauses)
                   if _S5_RELATIVE_RX.search(clause)]
        if rel_cis:
            sp0 = clauses[rel_cis[0]][1][0]
            sp1 = clauses[rel_cis[-1]][1][1]
            s5_rel_claim = dict(effect_type=S5_CHANCE_TYPE, direction='up',
                                clause_index=rel_cis[0], span=[sp0, sp1],
                                snippet=text_n[sp0:sp1], s5_chance=True, s5_relative=True,
                                s5_answer_index=_s5_rel[0][1],
                                s5_slots=[x[0] for x in _s5_rel])
            claims.append(s5_rel_claim)
            claim_by_clause.setdefault(rel_cis[0], []).append(s5_rel_claim)
            covered_clause_idx.update(rel_cis)

    # ---- S5 地形段概率玛那主张（2026-10-26 批2；独立 scope，来源限定）-----------------
    # 只覆盖地形条件子句＋其后连续的玛那/接续子句；条件之前的击杀基础概率子句不覆盖
    # （5092/7546 仍留 S3，行仍「拆分待核查」）。无地形段答案的行不新增主张。
    if _s5_t:
        _t_cis = _s5_terrain_claim_clauses(clauses)
        if _t_cis:
            sp0 = clauses[_t_cis[0]][1][0]
            sp1 = clauses[_t_cis[-1]][1][1]
            s5t_claim = dict(effect_type=S5_CHANCE_TYPE, direction='up',
                             clause_index=_t_cis[0], span=[sp0, sp1],
                             snippet=text_n[sp0:sp1], s5_chance=True,
                             s5_terrain=True,
                             s5_answer_index=_s5_t[0][1],
                             s5_slots=[x[0] for x in _s5_t])
            claims.append(s5t_claim)
            claim_by_clause.setdefault(_t_cis[0], []).append(s5t_claim)
            covered_clause_idx.update(_t_cis)

    # ---- 金币/经验主张（2026-10-28 批2；来源限定）--------------------------------------
    # 词表没有「ゴールド／経験値」效果类型；只有本批合格答案存在的行才登记一条来源限定主张，
    # 覆盖该能力在句面点名的子句（经验值/金币分别登记，值方向按 param0>1/<1）。无答案行不新增
    # 未解决主张、不新增拆分；30236/30239 无本批答案，自然零触碰。
    for _ab, _idx, _raw, _rk in _ge_answer_slots(row):
        _etype = _GE_RULE_SLOTS[_rk][1]
        if any(c.get('effect_type') == _etype for c in claims):
            continue
        _mark = _GE_ABILITY_MARK[_ab]
        _cis = [ci for ci, (clause, _span) in enumerate(clauses) if _mark in clause]
        if not _cis:
            continue
        _sp0 = clauses[_cis[0]][1][0]
        _sp1 = clauses[_cis[-1]][1][1]
        _ge_claim = dict(effect_type=_etype, direction=('up' if _raw > 1 else 'down'),
                         clause_index=_cis[0], span=[_sp0, _sp1],
                         snippet=text_n[_sp0:_sp1], gold_exp=True,
                         gold_exp_ability=_ab, gold_exp_answer_index=_idx)
        claims.append(_ge_claim)
        claim_by_clause.setdefault(_cis[0], []).append(_ge_claim)
        covered_clause_idx.update(_cis)

    # ---- 有依据的不适用窄类预检测（先于拆分标志；NA 子句计为已覆盖）--------------------
    na_clause_idx = set()
    na_tmp = []
    for ci, (clause, span) in enumerate(clauses):
        core = clause
        for c in _CONNECTIVES:
            if core.startswith(c):
                core = core[len(c):]
        if not core.strip() or ci in claim_by_clause:
            continue
        if (core.rstrip('。、！？').endswith('できない') and not _DIGIT_RE.search(clause)
                and not _boundary_attrs(clause, _WORD_SET) and not _DURATION_RE.search(clause)
                and '場合' not in clause):
            na_tmp.append((ci, clause, span))
            na_clause_idx.add(ci)

    unclassified_clauses = [
        dict(clause_index=ci, text=clauses[ci][0], span=clauses[ci][1])
        for ci in range(len(clauses))
        if ci not in covered_clause_idx and ci not in na_clause_idx]

    # ---- 答案映射与消费 ---------------------------------------------------------------
    answer_refs = []
    for idx, a in enumerate(row['answers']):
        etype, basis = _answer_effect_type(a)
        attack_binding = _attack_interval_binding(row, idx, a)
        if attack_binding:
            etype, basis = attack_binding['effect_type'], '攻速消费者精确来源＋行/词span绑定'
        src = a.get('source') if isinstance(a.get('source'), dict) else None
        # R1 整改（20261023）：HP 档位分支标签随答案引用保留（条件绑定可对账）。
        _cl = a.get('condition_label')
        answer_refs.append(dict(
            answer_index=idx, rule_key=a.get('rule_key'), field_path=a.get('field_path'),
            raw_value=a.get('raw_value'), value=a.get('value'), unit=a.get('unit'),
            quantity_kind=a.get('quantity_kind'), conversion=a.get('conversion'),
            conditions=a.get('conditions'), base_definition=a.get('base_definition'),
            condition_label=_cl,
            effect_binding=a.get('effect_binding'),
            numeric_evidence=a.get('numeric_evidence'),
            association_evidence=a.get('association_evidence'),
            numeric_source=a.get('numeric_source'),
            source_record=(None if src is None else
                           {k: src.get(k) for k in ('table', 'record_id', 'layer', 'record_key')}),
            mapped_effect_type=etype, mapping_basis=basis,
            direction=None if attack_binding else _answer_direction(a),
            matched_effect_id=None, attack_interval_binding=attack_binding))

    # 逐类型贪心匹配：先同方向，再无方向答案；不跨方向消费。
    # DS-GR-R1（20261023 复验）：ダメージ 类主张与答案加对象约束——自伤答案只配
    # 自身/自分 子句、敌方伤害答案只配 敵 子句；对象不符的答案不消费（跨对象不硬配），
    # 主张留未解决并注明（object_unmatched_note）。非伤害类型不引入约束（避免改道既有匹配）。
    def _t67_binding(ref):
        """type67 阶梯批（20261028）答案标记；无标记＝其他族答案，走原贪心路径。"""
        try:
            a = row['answers'][ref['answer_index']]
        except (IndexError, KeyError):
            return None
        b = a.get('binding') if isinstance(a.get('binding'), dict) else None
        t67 = b.get('type67_binding') if isinstance(b, dict) else None
        return t67 if isinstance(t67, dict) else None

    def _ge_binding(ref):
        """金币/经验批（20261028 批2）答案标记；无标记＝其他族答案，走原贪心路径。"""
        try:
            a = row['answers'][ref['answer_index']]
        except (IndexError, KeyError):
            return None
        return _ge_binding_of_answer(a)

    claims_sorted = sorted(range(len(claims)),
                           key=lambda i: (claims[i]['clause_index'], claims[i]['span'][0]))
    ans_by_type = collections.defaultdict(list)
    for ref in answer_refs:
        if ref['mapped_effect_type']:
            ref['object'] = _answer_object(ref)
            ans_by_type[ref['mapped_effect_type']].append(ref)
    matched = {}
    object_blocked = set()
    # R1 整改（20261023）：HP 档位分支变体组——同一主张类型带 HP condition_label 的答案
    # 是同一效果在不同 HP 档位下的逐分支值（各注来源分支与条件），随首个命中主张整体消费；
    # 不再作为 S4「未对应主张」。仅 HP 前缀标签进入变体组（批 4/14 职业等条件语义不变）。
    def _is_hp_variant(ref):
        return str(ref.get('condition_label') or '').startswith('HP ')

    def _explicit_variant(ref, claim):
        # YG1: multiple source patterns answer one precisely located claim.
        # A label/value alone is insufficient; require row/type/span identity.
        binding = ref.get('effect_binding') or {}
        answer = row['answers'][ref['answer_index']]
        source = answer.get('source') or {}
        carrier = answer.get('binding') or {}
        pattern_ids = row.get('inference_yg1', {}).get('pattern_ids', [])
        multihit = row.get('inference_yg1_multihit') or {}
        if (carrier.get('scope') == 'YG1_BATCH3_MULTIHIT_FORMULA_ONLY'
                and multihit.get('scope') == carrier['scope']
                and carrier.get('type') in (105, 110, 3, 22)
                and answer.get('rule_key') == f"bossskill|{carrier['type']}|/skillparam1"):
            pattern_ids = multihit.get('pattern_ids', [])
        if (binding.get('row_id') == row_id and binding.get('effect_type') == claim['effect_type']
                and binding.get('span') == claim['span'] and binding.get('pattern_id') is not None
                and binding.get('pattern_id') == carrier.get('pattern_id')
                and binding.get('pattern_id') in pattern_ids
                and all(answer.get(k) == source.get(k) and source.get(k) is not None
                        for k in ('table', 'record_id', 'layer', 'field_path'))
                and ref.get('condition_label') and ref.get('source_record')
                and ref['source_record'].get('table') == 'bossskill'):
            return binding.get('variant_group')
        return None

    for etype in {claims[i]['effect_type'] for i in claims_sorted}:
        pool = list(ans_by_type.get(etype, []))
        constrain = etype in _DAMAGE_TYPES
        for i in [i for i in claims_sorted if claims[i]['effect_type'] == etype]:
            cdir = claims[i]['direction']
            cobj = claims[i].get('object') if constrain else None
            cand_pool = ([r for r in pool if r.get('object') in (None, cobj)]
                         if constrain and cobj is not None else pool)
            # Explicit bindings never fall back to the unbound greedy path.
            cand_pool = [r for r in cand_pool if r.get('attack_interval_binding')
                        or r.get('effect_binding') is None
                         or _explicit_variant(r, claims[i])]
            # These source-qualified cadence answers never use greedy matching.
            cand_pool = [r for r in cand_pool if
                         ((r.get('rule_key') not in ('skilllist|7|/param7', 'skilllist|2012|/param6', 'skilllist|1016|/param6',
                              'skilllist|56|/param9','bossskill|68|/skillparam9','bossskill|118|/skillparam9')
                           and r.get('quantity_kind') != '攻击间隔乘数')
                          or (r.get('attack_interval_binding') and
                              r['attack_interval_binding']['span'] == claims[i]['span']))]
            # type67 阶梯批（20261028，来源限定）：带 type67_binding 标记的答案不走贪心路径，
            # 只由本批专用块按槽位↔主张类型绑定（避免多值阶梯答案被同类型其他主张抢配）。
            cand_pool = [r for r in cand_pool if _t67_binding(r) is None]
            # 金币/经验批（20261028 批2，来源限定）：带 gold_exp_binding 标记的答案同样不走
            # 贪心路径，只由本批专用块按能力↔主张类型绑定（避免被同句其它类型主张抢配）。
            cand_pool = [r for r in cand_pool if _ge_binding(r) is None]
            # 回复间隔两段乘数批（20261028 批3，来源限定）：带 heal_interval_binding 标记的
            # 答案不走贪心路径，只由本批专用块绑到「回復速度」处的那一条回復主张。
            cand_pool = [r for r in cand_pool if _hi_binding_of_answer(
                row['answers'][r['answer_index']]) is None]
            # G0-B1／G7-B0 合并小批（20261028 批5，来源限定）：带 g0g7_binding 标记的答案
            # 不走贪心路径，只由本批专用块按「主张 span＋子句号」绑定（防止 30334 的
            # 「遠距離通常攻撃の威力」被同类型贪心抢配）。
            cand_pool = [r for r in cand_pool if _g0g7_binding_of_answer(
                row['answers'][r['answer_index']]) is None]
            pick = None
            if cdir:
                pick = next((r for r in cand_pool if r['direction'] == cdir), None)
            if pick is None:
                pick = next((r for r in cand_pool if r['direction'] is None), None)
            if pick is None and not cdir and cand_pool:
                pick = cand_pool[0]
            if pick is not None:
                pool.remove(pick)
                matched[i] = pick
                if _is_hp_variant(pick):
                    for vr in [r for r in pool if _is_hp_variant(r)]:
                        pool.remove(vr)
                        matched.setdefault(f'variant:{i}:{vr["answer_index"]}', vr)
                group = _explicit_variant(pick, claims[i])
                if group:
                    seen_patterns = {pick['effect_binding']['pattern_id']}
                    for vr in list(pool):
                        if (vr in cand_pool and _explicit_variant(vr, claims[i]) == group
                                and vr['direction'] == pick['direction']
                                and vr['effect_binding']['pattern_id'] not in seen_patterns):
                            seen_patterns.add(vr['effect_binding']['pattern_id'])
                            pool.remove(vr)
                            matched[f'variant:{i}:{vr["answer_index"]}'] = vr
            elif constrain and cobj is not None and pool:
                object_blocked.add(i)   # 有同类型答案但对象全不符——不硬配

    # ---- マナB 批（2026-10-26，主持裁决）：来源限定变体绑定 -------------------------
    # 仅消费带 ``binding.mana_b_binding`` 标记的答案（本批模块写入），且只在已有
    # 「効果（词表外）」主张/攻撃力主张消费时把同源多槽答案绑为 variant_refs：
    #   (b) S3「効果が上がる」展开出的攻/移/防/暴击率答案 → 该唯一効果主张的变体；
    #   (c) S4/96「攻撃力」的 param2/param3 两档 → 同一攻撃力主张的两个变体。
    # 不新增主张、不改无答案行；既有 1,209 条三键开局答案与其他族不受影响。
    _MB_TYPES = {'攻撃力', '移動速度', '防御力', 'クリティカル発生率', 'クリティカル威力'}
    _mb_used = {r['answer_index'] for r in matched.values() if isinstance(r, dict)}

    def _mb_binding(ref):
        try:
            a = row['answers'][ref['answer_index']]
        except (IndexError, KeyError):
            return None
        b = a.get('binding') if isinstance(a.get('binding'), dict) else None
        mb = (b or {}).get('mana_b_binding') if isinstance(b, dict) else None
        return mb if isinstance(mb, dict) else None

    _effect_claims = [i for i in claims_sorted if claims[i]['effect_type'] == '効果（词表外）']
    if len(_effect_claims) == 1 and _effect_claims[0] not in matched:
        _ci = _effect_claims[0]
        _cands = [r for r in answer_refs
                  if r['answer_index'] not in _mb_used
                  and r['mapped_effect_type'] in _MB_TYPES
                  and (_mb_binding(r) or {}).get('family') in ('hold_mana', 'mana_count_up')]
        if _cands:
            matched[_ci] = _cands[0]
            _mb_used.add(_cands[0]['answer_index'])
            for _vr in _cands[1:]:
                matched[f'variant:{_ci}:{_vr["answer_index"]}'] = _vr
                _mb_used.add(_vr['answer_index'])
    for _i in claims_sorted:
        if claims[_i]['effect_type'] != '攻撃力' or _i not in matched:
            continue
        _base = matched[_i]
        _brec = (_base.get('source_record') or {}).get('record_id')
        for _r in answer_refs:
            if _r['answer_index'] in _mb_used:
                continue
            _mb = _mb_binding(_r) or {}
            if _mb.get('family') != 'mana_count_up':
                continue
            if _r['mapped_effect_type'] != '攻撃力':
                continue
            if (_r.get('source_record') or {}).get('record_id') != _brec:
                continue
            if _r.get('quantity_kind') != _base.get('quantity_kind'):
                continue
            matched[f'variant:{_i}:{_r["answer_index"]}'] = _r
            _mb_used.add(_r['answer_index'])
    # 既有原文数字答案已消费同一主张时（如 292 的「效果量百分比」行）：把来源限定的
    # 结构化答案换为主答案、旧答案降为同一主张的 variant——旧答案对象不改值/不丢失，
    # 仅新增结构化来源并消除未消费标志。仅对带 mana_b_binding 的答案生效。
    for _i in claims_sorted:
        if _i not in matched or claims[_i]['effect_type'] not in _MB_TYPES:
            continue
        _base = matched[_i]
        if _mb_binding(_base):
            continue
        _same_claims = [j for j in claims_sorted
                        if claims[j]['effect_type'] == claims[_i]['effect_type'] and j in matched]
        if len(_same_claims) != 1:
            continue
        _cands = [r for r in answer_refs
                  if r['answer_index'] not in _mb_used
                  and r['mapped_effect_type'] == claims[_i]['effect_type']
                  and (_mb_binding(r) or {}).get('family') in ('hold_mana', 'mana_count_up')]
        if len(_cands) != 1:
            continue
        _mr = _cands[0]
        matched[_i] = _mr
        matched[f'variant:{_i}:{_base["answer_index"]}'] = _base
        _mb_used.add(_mr['answer_index'])

    # ---- クリティカル吸収批（2026-10-26，主持裁决 (a)）：来源限定双槽同主张 -----------
    # 仅消费带 ``binding.crit_absorb_binding`` 标记的答案（本批模块写入）；同一
    # 「回復（词表外）」主张下 param1（回復比例）与 flag0_1（上限档位）作为该效果的
    # 两个答案引用（后者记 variant），不新增主张、不改无答案行。
    # 三重来源限定：scope＝本批、row_id 与标记一致、载体 record=65000003/ability=21/CACHE，
    # 且 rule_key 在批内两键、映射类型＝回復（词表外）。无标记/错 scope/错 record 一律不消费
    # （保持 S4 可见，不静默吞掉其他族答案）。
    _CA_SCOPE = 'CRIT_ABSORB_BATCH_20261026'
    _CA_KEYS = ('skilllist|21|/param1', 'skilllist|21|/flag0_1')
    _CA_EFFECT = '回復（词表外）'

    def _ca_binding(ref):
        try:
            a = row['answers'][ref['answer_index']]
        except (IndexError, KeyError):
            return None
        b = a.get('binding') if isinstance(a.get('binding'), dict) else None
        ca = b.get('crit_absorb_binding') if isinstance(b, dict) else None
        return ca if isinstance(ca, dict) else None

    def _ca_valid(ref, ca):
        src = ref.get('source_record') or {}
        return (ca.get('scope') == _CA_SCOPE
                and ca.get('row_id') == row_id
                and ca.get('carrier_record_id') == 65000003
                and ca.get('carrier_ability') == 21
                and ca.get('carrier_layer') == 'CACHE'
                and ca.get('rule_key') == ref.get('rule_key')
                and ref.get('rule_key') in _CA_KEYS
                and ref.get('mapped_effect_type') == _CA_EFFECT
                and src.get('table') == 'skilllist'
                and src.get('record_id') == 65000003
                and src.get('layer') == 'CACHE')

    _ca_claims = [i for i in claims_sorted if claims[i]['effect_type'] == _CA_EFFECT]
    if len(_ca_claims) == 1 and _ca_claims[0] in matched:
        _ci = _ca_claims[0]
        _ca_base = matched[_ci]
        _ca_base_b = _ca_binding(_ca_base)
        if _ca_base_b and _ca_valid(_ca_base, _ca_base_b):
            _ca_used = {r['answer_index'] for r in matched.values() if isinstance(r, dict)}
            for _r in answer_refs:
                if _r['answer_index'] in _ca_used:
                    continue
                _b2 = _ca_binding(_r)
                if not _b2 or not _ca_valid(_r, _b2):
                    continue
                matched[f'variant:{_ci}:{_r["answer_index"]}'] = _r
                _ca_used.add(_r['answer_index'])

    # ---- type67 阶梯批（2026-10-28，来源限定）：槽位↔主张精确绑定 -------------------
    # 仅消费带 ``binding.type67_binding`` 标记的答案（本批模块写入，scope＝TYPE67_BATCH_
    # 20261028），按槽位对应的属性类型一对一绑定到同类型主张；无标记/错 scope/错槽位一律
    # 不消费（保持未解决，不静默吞掉其他族答案）。不新增主张、不改其他族映射。
    def _t67_valid(ref, t67, etype):
        src = ref.get('source_record') or {}
        return (t67.get('scope') == _T67_SCOPE
                and t67.get('family') == 'type67_ladder'
                and t67.get('row_id') == row_id
                and t67.get('slot') == (ref.get('field_path') or '').lstrip('/')
                and _T67_SLOT_EFFECT.get(t67.get('slot')) == etype
                and ref.get('mapped_effect_type') == etype
                and ref.get('rule_key') == f"skilllist|67|/{t67.get('slot')}"
                and src.get('table') == 'skilllist'
                and src.get('record_id') == t67.get('carrier_record_id')
                and src.get('layer') == t67.get('carrier_layer'))

    _t67_used = {r['answer_index'] for r in matched.values() if isinstance(r, dict)}
    for _i in claims_sorted:
        if _i in matched:
            continue
        _etype = claims[_i]['effect_type']
        if _etype not in set(_T67_SLOT_EFFECT.values()):
            continue
        _pick = None
        for _r in answer_refs:
            if _r['answer_index'] in _t67_used:
                continue
            _t67 = _t67_binding(_r)
            if not _t67 or not _t67_valid(_r, _t67, _etype):
                continue
            _pick = _r
            break
        if _pick is not None:
            matched[_i] = _pick
            _t67_used.add(_pick['answer_index'])

    # ---- 金币/经验批（2026-10-28 批2，来源限定）：能力↔主张精确绑定 ------------------
    # 仅消费带 ``binding.gold_exp_binding``（scope＝GOLD_EXP_BATCH_20261028）的答案，按
    # ability/rule_key/载体记录与层逐项核对；无标记/错 scope/错能力一律不消费。
    def _ge_valid(ref, claim):
        ge = _ge_binding(ref)
        src = ref.get('source_record') or {}
        if not ge or ge.get('scope') != _GE_SCOPE:
            return False
        hit = _GE_RULE_SLOTS.get(ge.get('rule_key'))
        return (hit is not None
                and hit[0] == claim.get('gold_exp_ability')
                and hit[1] == claim.get('effect_type')
                and ge.get('row_id') == row_id
                and ge.get('slot') == 'param0'
                and ref.get('field_path') == '/param0'
                and ref.get('rule_key') == ge.get('rule_key')
                and ref.get('mapped_effect_type') == claim.get('effect_type')
                and src.get('table') == 'skilllist'
                and src.get('record_id') == ge.get('carrier_record_id')
                and src.get('layer') == ge.get('carrier_layer'))

    _ge_used = {r['answer_index'] for r in matched.values() if isinstance(r, dict)}
    for _i in claims_sorted:
        if _i in matched:
            continue
        _claim = claims[_i]
        if not _claim.get('gold_exp'):
            continue
        _pick = None
        for _r in answer_refs:
            if _r['answer_index'] in _ge_used:
                continue
            if _ge_valid(_r, _claim):
                _pick = _r
                break
        if _pick is not None:
            matched[_i] = _pick
            _ge_used.add(_pick['answer_index'])

    # ---- type80/96 成对批（2026-10-28 批4，来源限定）：槽位↔主张精确绑定 --------------
    # 仅消费带 ``binding.type80_96_binding``（scope＝TYPE80_96_BATCH_20261028）的答案，
    # 按 family(形态)/槽/rule_key/载体记录与层逐项核对；无标记/错 scope/错槽位一律不消费
    # （保持未解决，不静默吞掉其他族答案）。不新增主张、不改其他族映射。
    def _t8096_binding(ref):
        try:
            a = row['answers'][ref['answer_index']]
        except (IndexError, KeyError):
            return None
        b = a.get('binding') if isinstance(a.get('binding'), dict) else None
        t = b.get('type80_96_binding') if isinstance(b, dict) else None
        return t if isinstance(t, dict) else None

    def _t8096_valid(ref, t8096, etype):
        src = ref.get('source_record') or {}
        slot = (ref.get('field_path') or '').lstrip('/')
        ability = t8096.get('ability')
        return (t8096.get('scope') == _T8096_SCOPE
                and t8096.get('family') in _T8096_FAMILIES
                and t8096.get('row_id') == row_id
                and t8096.get('slot') == slot
                and ((_T8096_SLOT_EFFECT.get(ability) or {}).get(slot)) == etype
                and ref.get('mapped_effect_type') == etype
                and ref.get('rule_key') == f'skilllist|{ability}|/{slot}'
                and t8096.get('rule_key') == ref.get('rule_key')
                and src.get('table') == 'skilllist'
                and src.get('record_id') == t8096.get('carrier_record_id')
                and src.get('layer') == t8096.get('carrier_layer'))

    _t8096_used = {r['answer_index'] for r in matched.values() if isinstance(r, dict)}
    for _i in claims_sorted:
        if _i in matched:
            continue
        _etype = claims[_i]['effect_type']
        if _etype not in _T8096_EFFECT_TYPES:
            continue
        _pick = None
        for _r in answer_refs:
            if _r['answer_index'] in _t8096_used:
                continue
            _t = _t8096_binding(_r)
            if not _t or not _t8096_valid(_r, _t, _etype):
                continue
            _pick = _r
            break
        if _pick is not None:
            matched[_i] = _pick
            _t8096_used.add(_pick['answer_index'])

    # ---- 回复间隔两段乘数批（2026-10-28 批3，来源限定）：回復速度处既有主张↔两段答案 ----
    # **不新增主张**：把本批答案绑到句面「回復速度」词形内部唯一的那条「回復（词表外）」
    # 主张上（基础段 19.p2 为主答案、条件段 1033.p3 为同一主张的 variant）。要求 scope/
    # row_id/槽/载体记录与层逐项一致、方向与主张一致（<1＝间隔缩短＝速度 up）；=1 不绑。
    # 无标记/错 scope/多义主张一律不消费（保持未解决，不静默吞掉其他族答案）。
    _hi_slots = _hi_answer_slots(row)
    if _hi_slots:
        _occ, _from = [], text_n.find(_HI_SPEED_WORD)
        while _from >= 0:
            _occ.append((_from, _from + len(_HI_SPEED_WORD)))
            _from = text_n.find(_HI_SPEED_WORD, _from + 1)
        if len(_occ) == 1:
            _o0, _o1 = _occ[0]
            _hi_claims = [i for i in claims_sorted
                          if claims[i]['effect_type'] == _HI_EFFECT
                          and _o0 <= claims[i]['span'][0] and claims[i]['span'][1] <= _o1]
            if len(_hi_claims) == 1:
                _ci = _hi_claims[0]

                def _hi_valid(ref):
                    hi = _hi_binding_of_answer(row['answers'][ref['answer_index']])
                    src = ref.get('source_record') or {}
                    hit = _HI_RULE_SLOTS.get(ref.get('rule_key'))
                    if (not hi or hi.get('scope') != _HI_SCOPE or hit is None
                            or hit[0] != hi.get('ability') or hit[1] != hi.get('slot')
                            or hi.get('row_id') != row_id
                            or hi.get('rule_key') != ref.get('rule_key')
                            or ref.get('mapped_effect_type') != _HI_EFFECT
                            or ref.get('field_path') != '/' + hi.get('slot')
                            or src.get('table') != 'skilllist'
                            or src.get('record_id') != hi.get('carrier_record_id')
                            or src.get('layer') != hi.get('carrier_layer')):
                        return None
                    raw = ref.get('raw_value')
                    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                        return None
                    if abs(float(raw) - 1.0) < 1e-12:
                        return None
                    cdir = claims[_ci].get('direction')
                    if cdir in ('up', 'down') and ((float(raw) < 1.0) != (cdir == 'up')):
                        return None
                    return hi

                _hi_used = {r['answer_index'] for r in matched.values() if isinstance(r, dict)}
                _hi_cands = [r for r in answer_refs
                             if r['answer_index'] not in _hi_used and _hi_valid(r)]
                _hi_cands.sort(key=lambda r: (
                    0 if _hi_binding_of_answer(row['answers'][r['answer_index']]).get('ability') == 19
                    else 1, r['answer_index']))
                if _hi_cands:
                    matched[_ci] = _hi_cands[0]
                    for _vr in _hi_cands[1:]:
                        matched[f'variant:{_ci}:{_vr["answer_index"]}'] = _vr

    # ---- G0-B1／G7-B0 合并小批（2026-10-28 批5，来源限定）：答案必须与该行主张的
    #      **span＋子句号**逐值相等才绑定。G0＝「必殺技の威力」中的「威力」主张
    #      （30334 的「遠距離通常攻撃の威力」是另一条同类主张，本批不消费）；G7＝地形句的
    #      攻撃力/移動速度 主张。无标记答案不进本块，本块也不改其他族匹配结果。 ----------
    _g0g7_used = {r['answer_index'] for r in matched.values() if isinstance(r, dict)}
    for _ref in answer_refs:
        if _ref['answer_index'] in _g0g7_used:
            continue
        _got = _g0g7_binding_of_answer(row['answers'][_ref['answer_index']])
        if not _got:
            continue
        _family, _gb = _got
        _hit = (_G0G7_RULE_SLOTS.get(_family) or {}).get(_ref.get('rule_key'))
        if _hit is None:
            continue
        _slot, _etype = _hit
        _src = _ref.get('source_record') or {}
        if (_gb.get('row_id') != row_id or _gb.get('slot') != _slot
                or _gb.get('rule_key') != _ref.get('rule_key')
                or _ref.get('mapped_effect_type') != _etype
                or _ref.get('field_path') != '/' + _slot
                or _src.get('table') != 'skilllist'
                or _src.get('record_id') != _gb.get('carrier_record_id')
                or _src.get('layer') != _gb.get('carrier_layer')):
            continue
        _raw = _ref.get('raw_value')
        if isinstance(_raw, bool) or not isinstance(_raw, (int, float)) or _raw <= 0:
            continue
        _wanted = [int(x) for x in (_gb.get('effect_span') or [])]
        if len(_wanted) != 2:
            continue
        _cands = [i for i in claims_sorted
                  if i not in matched
                  and claims[i]['effect_type'] == _etype
                  and claims[i]['clause_index'] == _gb.get('clause_index')
                  and [int(x) for x in claims[i]['span']] == _wanted]
        if len(_cands) != 1:
            continue
        _cdir = claims[_cands[0]].get('direction')
        if _cdir == 'up' and float(_raw) < 1.0:
            continue
        matched[_cands[0]] = _ref
        _g0g7_used.add(_ref['answer_index'])

    # ---- R2 复审整改（20261023 第二轮）：数字映射按角色绑定解析（在答案消费后执行，
    #      效果量角色要求「答案被数字所在子句的主张消费」＝文本位置绑定；条件/阈值/
    #      数量等辅助角色不要求主张消费但要求角色↔quantity_kind 兼容＋数值相等＋单位
    #      兼容（双方已知时）。角色不符不映射——数值相等只是必要线索。 -----------------
    consumed_clause_by_ref = {}
    for i, ref in matched.items():
        consumed_clause_by_ref[id(ref)] = claims[i]['clause_index'] \
            if isinstance(i, int) else claims[int(i.split(':')[1])]['clause_index']
    # 句级位置（R2 复审整改第二轮，R2-S2-CONSUMPTION-319 的回复量族）：
    # 「与えたダメージのN%、自身のHPが回復する」——数字与消费主张分处同句相邻子句，
    # 子句级位置绑定过严；效果量角色的消费位置放宽为「同句」（优先同子句，回退同句并注明）。
    _sent_spans = [(m.start(), m.end()) for m in _SENT_RE.finditer(text_n)
                   if m.group(0).strip()]

    def _sent_idx(pos):
        for k, (s, e) in enumerate(_sent_spans):
            if s <= pos < e:
                return k
        return None

    _clause_sent = [_sent_idx(sp[0]) for _cl, sp in clauses]

    def _resolve_digit(ref):
        lit = ref['literal']
        rclass = ref.get('role_class')
        if rclass == 'ordinal':
            return dict(basis='ordinal_selector',
                        detail='对象选择标识词形（Nst/ND/RD 序数词；非效果量）')
        if rclass is None or rclass == 'narrative':
            return None
        rl = ref.get('role_label')
        cands = []
        for r in answer_refs:
            if not _role_qk_compat(rl, rclass, r['quantity_kind']):
                continue
            if not _digit_num_eq(lit, r['raw_value']):
                continue
            if rclass == 'effect_amount':
                cc = consumed_clause_by_ref.get(id(r))
                if cc is None:
                    continue   # 效果量角色：须被主张消费（文本位置绑定）
                if cc != ref['clause_index'] and \
                        (_clause_sent[cc] is None or _clause_sent[cc] != _clause_sent[ref['clause_index']]):
                    continue   # 消费位置＝同子句优先；放宽仅限同一句内（跨句不绑定）
            ou, au = ref.get('role_unit'), str(r.get('unit') or '')
            if ou and au and str(ou) not in au and au not in str(ou):
                continue   # 单位/换算口径不符（双方已知时）
            cands.append(r)
        if cands:
            cr = _core_role(rl)
            # 绑定优先序：全标签精确相等 > 核心段相等 > 仅子类型别名（R2-ROLE-ALIAS-105
            # 配套：同值多候选时优先语义最精确绑定；同序内按答案序稳定）
            cands.sort(key=lambda r: (0 if str(r['quantity_kind']) == rl else
                                      1 if _core_role(r['quantity_kind']) == cr else 2,
                                      r['answer_index']))
            r = cands[0]
            if rclass == 'effect_amount':
                cc = consumed_clause_by_ref.get(id(r))
                pos = ('；被同子句主张消费' if cc == ref['clause_index']
                       else '；被同句相邻子句主张消费（sentence 级位置绑定——如「与えた'
                            'ダメージのN%、HPが回復」型）')
            else:
                pos = ''
            return dict(basis='role_bound_answer',
                        detail=f'答案[{r["answer_index"]}] quantity_kind=「{r["quantity_kind"]}」'
                               f'与数字角色「{rl}」兼容（核心段「{_core_role(r["quantity_kind"])}」），'
                               f'raw_value={r["raw_value"]!r}（原值/百分比口径数值相等）{pos}')
        if rclass == 'effect_amount' and ref['clause_index'] in claim_by_clause:
            # 精确同标签结构化回退（R2-S2-CONSUMPTION-319 建议路径，20261023）：答案与数字
            # 角色核心标签**精确相等**＋值/单位相等、未被任何主张消费（其效果类型未入词表
            # 属独立缺口）、数字所在子句存在主张——数字绑定成立；所属主张的未解决状态另行
            # 登记（不据此判主张已解、不据此判完整）。
            crl = _core_role(rl)
            for r in answer_refs:
                if id(r) in consumed_clause_by_ref:
                    continue
                if _core_role(r['quantity_kind']) != crl:
                    continue
                if not _digit_num_eq(lit, r['raw_value']):
                    continue
                ou, au = ref.get('role_unit'), str(r.get('unit') or '')
                if ou and au and str(ou) not in au and au not in str(ou):
                    continue
                return dict(basis='exact_label_structured_answer',
                            detail=f'答案[{r["answer_index"]}] quantity_kind 与数字角色核心标签'
                                   f'精确相等（「{crl}」），raw_value={r["raw_value"]!r}＋单位兼容；'
                                   '该答案效果类型未入词表、未被任何主张消费（独立缺口随主张'
                                   '登记）——数字绑定成立，不据此判主张已解')
        ref['same_label_answer_present'] = False
        return None

    for ref in number_refs:
        mp = _resolve_digit(ref)
        if mp:
            ref['mapping'] = mp
            ref['semantic_status'] = ('已映射：' + mp['detail']
                                      + '；角色/单位/数值三重绑定，原文角色标签仍为词面'
                                        '启发式，语义以映射依据与消费位置为准')
        else:
            rl = ref.get('role_label')
            rc = ref.get('role_class')
            same_label = [r for r in answer_refs
                          if rc == 'effect_amount' and _core_role(r['quantity_kind']) == _core_role(rl)
                          and _digit_num_eq(ref['literal'], r['raw_value'])]
            ref['same_label_answer_present'] = bool(same_label)
            if rl is None:
                why = '文本角色未识别（无角色依据不作映射）'
            elif rc == 'narrative':
                # R2-NARRATIVE-S2（DeepSeek 复验 Low，20261023）：叙述性数字文案精确化——
                # 它不是「语义未确认的量」，而是不构成效果量/条件主张的叙述成分。
                why = ('叙述性数字（角色＝叙述性时间/数字——非效果量、非条件主张，'
                       '本就不参与数值映射；如后续证据表明其承载效果语义应推翻并入待办）')
            elif same_label:
                why = (f'角色「{rl}」存在同标签且数值相等的答案（answer[{same_label[0]["answer_index"]}]）'
                       '但未满足消费/位置绑定——绑定链未闭合；如本条在效果类型词表补齐后仍出现，'
                       '应视为效果类型识别缺陷排查')
            else:
                why = (f'角色「{rl}」无兼容 quantity_kind（同子类型）＋数值相等（原值/百分比口径）'
                       '＋单位兼容＋消费位置绑定的答案——角色/子类型不符不映射，'
                       '数值相等不构成语义证明')
            ref['unmapped_why'] = why
            ref['semantic_status'] = f'原文数字（未映射：{why}）'
            uncovered_digits.append(ref)

    # ---- effect 组装（主张效果：eNN 顺序稳定；NA 判定：qNN） --------------------------
    effects = []
    for n, i in enumerate(claims_sorted):
        c = claims[i]
        ref_answer = matched.get(i)
        _prefix = f'variant:{i}:'
        variant_refs = [matched[k] for k in sorted(k for k in matched
                                                   if isinstance(k, str) and k.startswith(_prefix))]
        effect_id = f'{row_id}#e{n:02d}'
        entry = dict(record_type='effect', effect_id=effect_id, description_ref=row_id,
                     effect_type=c['effect_type'], direction=c['direction'],
                     span=c['span'], snippet=c['snippet'], clause_index=c['clause_index'],
                     number_ref_ids=c.get('number_ref_ids') or [],
                     shared_duration=bool(c.get('shared_duration')),
                     status='has_answer' if ref_answer is not None else 'unresolved')
        if 'object' in c:
            entry['object'] = c['object']   # ダメージ 类主张的对象维度（DS-GR-R1/c15 内容级核对）
        if 'mana_slot' in c:
            entry['mana_slot'] = c['mana_slot']   # 開局マナ 主张的槽位（三键来源限定）
        if i in object_blocked:
            entry['object_unmatched_note'] = True   # 同类型答案存在但对象不符——跨对象不硬配
        if ref_answer is not None:
            all_refs = [ref_answer] + variant_refs
            for r in all_refs:
                r['matched_effect_id'] = effect_id
            entry['evidence_grades'] = sorted({g for r in all_refs for g in
                                               (r.get('numeric_evidence'),
                                                r.get('association_evidence')) if g})
            hp_labels = sorted({r.get('condition_label') for r in all_refs
                                if str(r.get('condition_label') or '').startswith('HP ')})
            if hp_labels:
                entry['condition_variants'] = hp_labels   # HP 档位分支（R1 整改）
            entry['answer_refs'] = [dict(
                answer_index=r['answer_index'], rule_key=r['rule_key'],
                field_path=r['field_path'], raw_value=r['raw_value'],
                condition_label=r.get('condition_label'),
                mapping_basis=r['mapping_basis'],
                resolvable_key=dict(row_id=row_id, field_path=r['field_path'],
                                    raw_value=r['raw_value'],
                                    answer_index=r['answer_index']))
                for r in all_refs]
        else:
            entry['evidence_grades'] = []
            entry['answer_refs'] = []
        effects.append(entry)

    # ---- NA 效果条目（预检测结果 na_tmp；判定依据见上）--------------------------------
    q = 0
    for ci, clause, span in na_tmp:
        effects.append(dict(
            record_type='effect', effect_id=f'{row_id}#q{q:02d}', description_ref=row_id,
            effect_type=NA_TYPE, direction=None, span=span, snippet=clause,
            clause_index=ci, number_ref_ids=[], shared_duration=False,
            status='justified_na', evidence_grades=[], answer_refs=[],
            na_basis=f'句面为「できない」禁止型机制表述（「{clause}」）：无数量词、无增减谓词、'
                     '无属性主张词——不适用固定数值；该判定仅对本子句面成立，如后续证据表明'
                     '其含数值语义应推翻并入待办'))
        q += 1

    # ---- R2 复审整改（20261023 第二轮）：残余机制监视——逐子句扫描＋结构化覆盖判定＋
    #      谓词模板。旧判定（任一答案注记/类型/条件含机制词即 covered）是词面覆盖：
    # 「暗闇机制尚未解析，待核查。」式否定注记也被当完成证据（复审 §R2b 反例）。
    # 第二轮口径：只认有解析状态的结构化引用——①答案 quantity_kind 指认该机制（且该答案
    # 无「未知/未解析/待核查/未分配」标记）；②注记带结构化载体/阈值披露形态（与 S6
    # 同一披露正则族）且无否定标记。注记/条件中的纯词面出现不再构成覆盖。
    # R2 复审整改（20261023 第三轮 root-fix，复审 §R2 根因 ①②）：上述判定仍是
    # 「有字段/提到词」式覆盖——
    #   根因①：quantity_kind 命中机制词即返回覆盖，不检查答案本身的值/原值/证据/状态
    #     （quantity_kind=暗闇＋value=未知＋raw_value=null＋证据未知＋status=unresolved
    #     的答案仍判覆盖）。
    #   根因②：注记分支只要求机制词与概率载体/阈值特征同在一个 note，不验证该载体实际
    #     解释的是哪个效果（「暗闇仅作为对照词，不属于上述概率载体解释的效果。」式对照性
    #     注记仍判覆盖）。
    # 第三轮口径：覆盖必须指向有效解析结果及其状态与对应关系——
    #   * quantity_kind 命中后须答案构成有效解析（_answer_effective_resolution：status 非
    #     unresolved、value 非未知/空、两项证据非未知/缺失、数值型答案 raw_value 非 null——
    #     数字串原值形态算有效原值；定性机制答案（未声明 quantitative）不强制数值，
    #     但证据仍须有效——「提到机制名称」不等于已解释）；
    #   * 注记载体分支须建立载体→效果对应：载体披露形态在场之外，还须注记自身把该机制词
    #     绑定到载体参数槽（「〈词〉」→/param… 映射披露——批 8/13/15 同一披露形态），且
    #     已登记能力族的载体不得为非同族机制作证（_CARRIER_ABILITY_FAMILY，如 50009 为
    #     ability2003 デバフ系，不得为暗闇/バリア等状态/防御机制作证）；无法建立对应→
    #     不覆盖（不设否定词黑名单、不硬编码反例 CID，对照性措辞因不含绑定披露而自然排除）；
    #   * 未知/未解析答案与无对应载体注记一律保留为缺口（facet→gap/have/next_step）。
    def _answer_effective_resolution(a):
        """答案是否构成该机制的有效解析（检查现行答案结构实际字段名）。

        返回 (ok, why)。字段名依据当前答案结构（20261023 全库 30,287 答案实测）：
        value/raw_value/quantity_kind/numeric_evidence/association_evidence/status/
        quantitative。
        """
        if str(a.get('status') or '') == 'unresolved':
            return False, 'status=unresolved（解析器自记未解决）'
        val = str(a.get('value') or '')
        if not val.strip():
            return False, 'value 为空'
        mk = next((m for m in _UNRESOLVED_NOTE_MARKERS if m in val), None)
        if mk:
            return False, f'value 含未解析标记「{mk}」'
        nev, aev = str(a.get('numeric_evidence') or ''), str(a.get('association_evidence') or '')
        if not nev.strip() or not aev.strip():
            return False, 'numeric/association evidence 缺失（无证据档不构成解析）'
        if '未知' in nev or '未知' in aev:
            return False, 'numeric/association evidence=未知'
        # 数值型答案（声明 quantitative 或显式携带 raw_value 键）须有非 null 原值；
        # 数字串原值形态（str）算有效原值（20261023 全库实测：16,745 条 str 原值答案）。
        # 定性机制答案（未声明 quantitative 且无 raw_value 键）不强制数值，但上方
        # 值/证据/状态检查仍然全量适用。
        if a.get('quantitative') is True or 'raw_value' in a:
            if a.get('raw_value') is None:
                return False, 'raw_value=null（数值型答案无原值）'
        return True, ''

    # 注记载体→机制词对应：注记把机制词绑定到载体参数槽的披露形态
    # （「〈短语〉」→/paramN … 映射——批 8「句中「クリティカル発生率」→/param4」、
    # 批 13「…的「防御力」→/param9」、批 15「句中「移動速度」→/skillparam6」同形）。
    _NOTE_SLOT_BIND_RE = re.compile(r'「([^」]+)」→(/param\w+|/skillparam\w+)')
    # 载体注记披露的能力号（批 8/13/15 形态「来源载体＝skilllist|<id>|<layer>，ability=<n>」）。
    _NOTE_ABILITY_RE = re.compile(r'来源载体＝skilllist\|\d+\|\w+，ability=(\d+)')

    def _carrier_note_correspondence(word, note):
        """验证载体实际解释的是当前机制。返回 (ok, why)。

        对应关系两路（须至少一路成立，且不与已登记能力族矛盾）：
        a) 槽位绑定：该机制词出现在本注记的「〈短语〉」→/param… 绑定披露中
           （载体槽与机制词的 1:1 映射披露——不是词面同现）；
        b) 能力族：注记披露的能力号已登记（_CARRIER_ABILITY_FAMILY）且机制词族
           属该能力可解释族。未登记能力号不虚构族对应——仅槽位绑定可作证。
        """
        binds = _NOTE_SLOT_BIND_RE.findall(note)
        bound = [ph for ph, _slot in binds if word in ph]
        ab = _NOTE_ABILITY_RE.search(note)
        ab_note = ab.group(1) if ab else None
        fam = _MECHANISM_WORD_FAMILY.get(word)
        reg = _CARRIER_ABILITY_FAMILY.get(ab_note) if ab_note else None
        if reg and fam and fam not in reg['families']:
            return False, (f'载体能力族不符：ability={ab_note} 登记为「{reg["family"]}」'
                           f'（{reg["source"]}），不解释{fam}类机制「{word}」')
        if bound:
            slots = sorted({_slot for ph, _slot in binds if word in ph})
            return True, (f'注记把「{word}」绑定到载体槽位 {",".join(slots)}'
                          + (f'（ability={ab_note}）' if ab_note else ''))
        return False, ('注记无「{w}」→载体槽位的绑定披露（词面同现不构成对应）'
                       .format(w=word))

    def _mechanism_structural_coverage(word):
        covered_basis, facet_only = None, []
        for idx, a in enumerate(row['answers']):
            qk = str(a.get('quantity_kind') or '')
            note = str(a.get('note') or '')
            cond = str(a.get('conditions') or '')
            blob = qk + ' ' + note + ' ' + cond
            if word not in blob:
                continue
            marker = next((mk for mk in _UNRESOLVED_NOTE_MARKERS if mk in blob), None)
            if marker:
                facet_only.append(dict(answer_index=idx, kind='unresolved_note',
                                       marker=marker))   # 否定注记＝缺口，不是完成证据
                continue
            if word in qk:
                ok, why = _answer_effective_resolution(a)
                if ok:
                    basis = (f'答案[{idx}] quantity_kind=「{qk}」指认该机制'
                             f'（结构化答案有效解析：{why or "值/原值/证据/状态检查通过"}）')
                    return True, basis, facet_only
                # 第三轮：命中机制词但答案本身未知/未解析——保留为缺口，不解除待办
                facet_only.append(dict(answer_index=idx, kind='unresolved_answer', why=why))
                continue
            if word in note and (_CARRIER_PROB_RE.search(note)
                                 or (_CARRIER_KEY_RE.search(note)
                                     and _THRESH_LIST_RE.search(note))
                                 or (_CARRIER_KEY_RE.search(note)
                                     and any(word in ph for ph, _sl in
                                             _NOTE_SLOT_BIND_RE.findall(note)))):
                if str(a.get('status') or '') != 'unresolved' and _answer_effective_resolution(a)[0]:
                    ok, why = _carrier_note_correspondence(word, note)
                    if ok:
                        return True, f'答案[{idx}] 注记载体披露与该机制对应（{why}）', facet_only
                    facet_only.append(dict(answer_index=idx,
                                           kind='carrier_no_correspondence', why=why))
                    continue
                facet_only.append(dict(answer_index=idx, kind='unresolved_answer',
                                       why=_answer_effective_resolution(a)[1]))
                continue
            facet_only.append(dict(answer_index=idx, kind='note_facet'))   # 纯词面提及
        return False, covered_basis, facet_only

    residual_hits = []
    # R2-S3B-PRECISION（DeepSeek 复验 Low，20261023）：叙事/说明语境低置信注记——
    # 不排除命中（保守登记不变，不得据此宣称机制已解析），只对疑似叙事过报的命中附
    # confidence='low' 注记（README 登记已知过报范围）：①命中词附近（±12 字符）有
    # 伝える/説明/語る/物語 等叙事动词；②谓词模板宾语为泛化代名词（あらゆるもの等）。
    _NARRATIVE_CTX_RE = re.compile(r'伝える|伝え|説明|語る|語り|物語|設定|好物|という')
    _GENERIC_OBJECTS = ('あらゆるもの', 'あらゆる', 'すべて', '全て')

    def _narrative_note(word, clause, obj=None):
        if obj is not None and any(g in obj for g in _GENERIC_OBJECTS):
            return ('低置信：谓词宾语为泛化代名词（「%s」）——疑似叙事文本，保守登记'
                    '不判解析、不据此宣称机制已解析' % obj)
        pos = clause.find(word)
        if pos >= 0 and _NARRATIVE_CTX_RE.search(clause[max(0, pos - 12):pos + len(word) + 12]):
            return '低置信：命中词附近有叙事/说明动词——疑似叙述文本，保守登记不判解析'
        return None

    def _facet_have(facet, noun):
        """把 facet 缺口类型转成待办「已有证据」描述（第三轮：未知答案/无对应载体
        也要能说出为何不构成覆盖，不笼统写「无解析状态」）。"""
        if not facet:
            return f'无答案提及该{noun}'
        f0 = facet[0]
        if f0['kind'] == 'unresolved_note':
            return (f'既有答案仅词面提及该{noun}且注记含否定标记「{f0["marker"]}」'
                    '（否定注记不是完成证据）')
        if f0['kind'] == 'unresolved_answer':
            return (f'既有答案 quantity_kind 指认该{noun}但答案本身未解析'
                    f'（{f0["why"]}）——未知/未解析答案不解除待办')
        if f0['kind'] == 'carrier_no_correspondence':
            return (f'既有答案注记含载体/阈值披露但未建立该{noun}的载体对应'
                    f'（{f0["why"]}）——其他效果的载体不作证')
        return f'既有答案仅词面提及该{noun}（无解析状态）'

    for ci, (clause, _sp) in enumerate(clauses):
        seen = set()
        for w in _RESIDUAL_MECHANISM_WORDS:
            if w not in clause or w in seen:
                continue
            seen.add(w)
            covered, basis, facet = _mechanism_structural_coverage(w)
            if covered:
                continue
            residual_hits.append(dict(
                word=w, clause_index=ci, clause=clause[:80], template='名词监视表',
                confidence=(_narrative_note(w, clause) or 'normal'),
                coverage=(facet or '本行答案未提及该机制'),
                gap=f'机制词「{w}」在正文子句#{ci}出现，但无结构化覆盖：无 quantity_kind '
                    '指认该机制的有效解析答案（值/原值/证据/状态任一未知即不算），'
                    '注记载体披露亦未建立与该机制的槽位绑定/能力族对应',
                have=(f'子句「{clause[:60]}」；' + _facet_have(facet, '机制')),
                next_step=('按机制谓词模板（付与/無効化/吸収/バリア/盾等家族，'
                           'effect_ledger._RESIDUAL_MECHANISM_WORDS 审计口径）核查该机制的'
                           '载体与数值；建立 quantity_kind 指认该机制且值/原值/证据/状态'
                           '有效的结构化答案（或注记载体对该机制的槽位绑定披露）后本待办'
                           '可解除（不一律判未知）')))
        for pm in _MECHANISM_PRED_RE.finditer(clause):
            obj, pred = pm.group(1), pm.group(2)
            if any(w in obj for w in _RESIDUAL_MECHANISM_WORDS) or _WORD_RE.search(obj):
                continue   # 宾语含监视名词/效果属性词——由名词/属性主张覆盖，不重复登记
            key = ('pred', obj, pred)
            if key in seen:
                continue
            seen.add(key)
            covered, basis, facet = _mechanism_structural_coverage(obj)
            if covered:
                continue
            residual_hits.append(dict(
                word=f'{obj}を{pred}', clause_index=ci, clause=clause[:80],
                template=f'谓词模板「〈宾语〉を{pred}」',
                confidence=(_narrative_note(f'{obj}を{pred}', clause, obj=obj) or 'normal'),
                coverage=(facet or '本行答案未提及该宾语'),
                gap=f'机制谓词「{pred}」的宾语「{obj}」（词表外机制名）在正文子句#{ci}出现，'
                    '但无结构化覆盖：无 quantity_kind 指认该宾语的有效解析答案，'
                    '注记载体披露亦未建立与该宾语的槽位绑定/能力族对应',
                have=(f'子句「{clause[:60]}」；' + _facet_have(facet, '宾语')),
                next_step=('核查该谓词宾语机制的载体与数值（有限模板清单：'
                           'effect_ledger._MECHANISM_PREDICATES）；建立值/证据/状态有效'
                           '的结构化答案后本待办可解除（不一律判未知）')))

    # F1: a lexical cue alone is not coverage. Only source-bound, consumed
    # answers can resolve these two complete qualifier forms; other clauses
    # and every other split flag retain their existing semantics.
    qualifier_resolutions = {}
    consumed_indices = {r['answer_index'] for r in answer_refs
                        if r.get('matched_effect_id') is not None}
    def qualifier_answer_valid(a):
        return (a.get('status') != 'unresolved'
                and a.get('value') not in (None, '', '未知', '未解析')
                and all(a.get(k) and '未知' not in str(a[k])
                        for k in ('numeric_evidence', 'association_evidence')))

    if effects and all(e['status'] == 'has_answer' for e in effects):
        used = [(i, row['answers'][i]) for i in sorted(consumed_indices)]
        for u in unclassified_clauses:
            ci, clause = u['clause_index'], u['text']
            bound = []
            if clause == '自身の場合' and row.get('group') == 'ability':
                bound = [i for i, a in used if qualifier_answer_valid(a)
                         and a.get('target') == '自身'
                         and _attack_interval_binding(row, i, a)]
            elif (clause == '【共鳴アビリティ】自身を含む<味方>が≪共鳴必殺≫を発動するたび'
                  and row.get('group') == 'sympathy'
                  and str(row.get('reference_field', '')).startswith('sympathy_skill_info[')
                  and row.get('source', {}).get('source_key') == 'CACHE/skilllist.data5.json.raw'):
                identity = row.get('merge_key')
                row_source = row.get('source') or {}
                position = row.get('source_position') or {}
                parent_id = None
                if (isinstance(identity, list) and len(identity) == 12
                        and identity[:3] == [row.get('cid'), 'sympathy', 'sympathy']
                        and identity[3:6] == [row_source.get('source_key'), row_source.get('field_json_pointer'), 'skilllist']
                        and isinstance(identity[6], int) and not isinstance(identity[6], bool)
                        and isinstance(identity[9], dict)
                        and identity[9].get('reference_slot') == row.get('reference_field')
                        and position.get('field_pointer') == row_source.get('field_json_pointer')
                        and position.get('source_key') == row_source.get('source_key')
                        and identity[10:] == position.get('raw_span')):
                    parent_id = identity[6]
                # This legacy composite answer has no generic parent-child
                # binding object. Pin the independently verified source version,
                # not a CID or a numerically similar donor. No new runtime input
                # or unverified neighbouring record is introduced.
                pinned_parent = (row_source.get('source_key'), row_source.get('field_json_pointer'),
                                 parent_id, row_source.get('raw_record_sha256'),
                                 row_source.get('byte_begin'), row_source.get('byte_end_exclusive'),
                                 row_source.get('layer'), row_source.get('record_key'), row_source.get('json_pointer'))
                if pinned_parent != ('CACHE/skilllist.data5.json.raw', '/skilllist/6407/text',
                        43023610, '12b291dfb4ad2d9b629d56056283be7b2b080d853014aedbd7932a0dab7aca42',
                        3247656, 3248985, 'CACHE',
                        'CACHE/skilllist.data5.json.raw#/skilllist/6407', '/skilllist/6407'):
                    continue
                pinned_child_pointer = '/skilllist/6408'
                pinned_child_hash = '386af4d2f041049ab60f9f540d3ae01c36543a8c602a884f972fd17af8917fb2'
                pinned_fields = {'/param0': 1, '/param1': 0.1, '/param2': 0.1,
                                 '/param6': 45, '/param8': 0.1}
                # Existing confirmed 3000 answers preserve per-field raw-byte
                # locations. Accept their exact M -> M+1 carrier relation only;
                # a text-only condition, an APK source or a different receiver
                # cannot stand in for this proof.
                for i, a in used:
                    src = a.get('source')
                    if not (qualifier_answer_valid(a) and a.get('table') == 'skilllist'
                            and a.get('target') == '战场味方'
                            and '3000共鸣技能开始事件' in str(a.get('conditions', ''))
                            and parent_id is not None
                            and a.get('record_id') == parent_id
                            and a.get('baseline_declared_description_id') == parent_id
                            and a.get('evidence_scope') == 'REVIEWED_RECORD'
                            and isinstance(src, list) and src):
                        continue
                    if all(isinstance(s, dict) and s.get('table') == 'skilllist'
                           and s.get('layer') == 'CACHE' and s.get('ability_type') == 3000
                           and s.get('record_id') == a['record_id'] + 1
                           and s.get('present') is True
                           and s.get('field_path') in ('/param0', '/param1', '/param2', '/param6', '/param8')
                           and isinstance(s.get('raw_value'), (int, float))
                           and not isinstance(s['raw_value'], bool) and math.isfinite(s['raw_value'])
                           and s.get('record_key') == 'CACHE/skilllist.data5.json.raw#' + pinned_child_pointer
                           and s.get('json_pointer') == pinned_child_pointer + s['field_path']
                           and s.get('location', {}).get('json_pointer') == pinned_child_pointer
                           and s.get('location', {}).get('ordinal_zero_based') == 6408
                           and s.get('location', {}).get('raw_record_sha256') == pinned_child_hash
                           and s.get('location', {}).get('byte_begin') == 3248986
                           and s.get('location', {}).get('byte_end_exclusive') == 3249344
                           and s['raw_value'] == pinned_fields[s['field_path']]
                           for s in src) and any(s['field_path'] == '/param0' and s['raw_value'] == 1 for s in src):
                        bound.append(i)
                if (set(bound) != consumed_indices
                        or not any('含自身味方发动共鸣必杀' in str(a.get('conditions', ''))
                                   for i, a in used if i in bound)):
                    bound = []
            if bound:
                resolution = dict(status='bound_qualifier', answer_indices=bound,
                    effect_ids=[e['effect_id'] for e in effects
                                if any(r['answer_index'] in bound for r in e['answer_refs'])],
                    basis='整子句仅为限定；已消费答案的对象/触发披露及限定来源满足F1窄门；不确认实机装载。')
                qualifier_resolutions[ci] = resolution
                refs.append(dict(ref_id=f'r{ci:02d}#bound', kind='bound_qualifier',
                                 clause_index=ci, span=u['span'], text=clause,
                                 resolution=resolution))
        unclassified_clauses = [u for u in unclassified_clauses
                                if u['clause_index'] not in qualifier_resolutions]

    # ---- 拆分待核查标志（在答案消费完成后计算；NA 子句不重复计 S1/S3）----------------
    unconsumed_typed = [r for r in answer_refs
                        if r['mapped_effect_type'] and r['matched_effect_id'] is None]
    split_flags = []
    if not claims and not na_tmp:
        split_flags.append(dict(
            code='S1_zero_claims',
            reason='词表未从句面识别任何效果主张；不能以关键词缺失证明语义完整，'
                   '描述可能包含词表外效果——显式登记拆分待核查'))
    if uncovered_digits:
        split_flags.append(dict(
            code='S2_unconfirmed_numbers',
            reason='原文含数字且其数值语义未经角色绑定映射（R2 复审整改 20261023 第二轮：'
                   '须数字角色↔答案 quantity_kind/单位/换算口径/文本位置多重绑定；数值相等'
                   '只是必要线索，角色/子类型不符不映射）',
            detail=[dict(ref_id=d['ref_id'], literal=d['literal'],
                         clause=clauses[d['clause_index']][0][:80],
                         in_claim_clause=d['clause_index'] in claim_by_clause,
                         original_numeric_role=d.get('original_numeric_role'),
                         role_label=d.get('role_label'), role_class=d.get('role_class'),
                         role_source=d.get('role_source'),
                         same_label_answer_present=d.get('same_label_answer_present'),
                         gap=f'数字「{d["literal"]}」：{d.get("unmapped_why") or "无映射依据"}',
                         have=('子句「%s」；角色来源 %s' % (clauses[d['clause_index']][0][:60],
                               d.get('role_source') or '无（子句词形未识别）')),
                         next_step=('叙述性数字（角色说明见 gap）无需数值映射，仅须确认其确为'
                                    '叙述成分；其余情形为该角色建立结构化答案（quantity_kind '
                                    '与数字角色同子类型、raw_value 原值/百分比口径逐字、unit '
                                    '登记）或登记该数字语义的核查记录后本待办可解除'
                                    '（不一律判未知）'))
                    for d in uncovered_digits]))
    if unclassified_clauses:
        split_flags.append(dict(
            code='S3_uncovered_clauses',
            reason='存在未被任何效果主张覆盖的正文子句（定性机制语义核查未完成，不登记为不适用）',
            detail=[dict(clause_index=u['clause_index'], text=u['text'][:120])
                    for u in unclassified_clauses[:20]]))
    if unconsumed_typed:
        split_flags.append(dict(
            code='S4_unconsumed_typed_answers',
            reason='存在已映射效果类型的答案未对应到任何句面主张——词面拆分与答案归属存在缺口',
            detail=[dict(answer_index=r['answer_index'], mapped_effect_type=r['mapped_effect_type'],
                         value=r['value']) for r in unconsumed_typed[:20]]))
    # ---- R1 整改（20261023）：HP 档位分支覆盖——完成判定按分支覆盖重新判定 --------------
    # S5a：行内已绑定 ≥2 个 HP 档位标签时，每个已匹配主张类型须覆盖全部档位标签；
    #      缺档位（或行登记的 hp_branch_conditions_expected 少于应答标签）→ 分支覆盖不完整。
    # S5b：charainfo/denju 行的家族句（味方全体…一定時間上がる）在上下文写明「随HP变化」
    #      而答案无任何 HP 档位标签——增益答案缺条件单独结清，不得判完整。
    hp_labels = sorted({r.get('condition_label') for r in answer_refs
                        if str(r.get('condition_label') or '').startswith('HP ')})
    ctx_text = (row.get('context_text') or '') + row['japanese']
    hp_var_ctx = '残りHP' in ctx_text and '変化' in ctx_text
    expected_labels = sorted({str(x) for x in (row.get('hp_branch_conditions_expected') or [])
                              if x})
    if len(hp_labels) >= 2 or len(expected_labels) >= 2:
        covered = {}
        for e in effects:
            if e['status'] != 'has_answer':
                continue
            labs = {r.get('condition_label') for r in e.get('answer_refs') or []
                    if str(r.get('condition_label') or '').startswith('HP ')}
            covered.setdefault(e['effect_type'], set()).update(labs)
        missing = [dict(effect_type=t, missing_labels=sorted(l for l in (expected_labels or hp_labels)
                                                           if l not in labs))
                   for t, labs in covered.items()
                   if any(l not in labs for l in (expected_labels or hp_labels))]
        uncovered_expected = [l for l in expected_labels
                              if l not in hp_labels]
        if missing or uncovered_expected:
            split_flags.append(dict(
                code='S5_hp_branch_coverage',
                reason='HP 档位分支覆盖不完整（R1 整改 20261023）：源记录引用多个 HP 档位分支，'
                       '每个已匹配主张类型须逐档位有值行或具体待办——存在缺档位',
                detail=dict(missing=missing,
                            uncovered_expected_labels=uncovered_expected,
                            bound_labels=hp_labels, expected_labels=expected_labels)))
    elif hp_var_ctx and table in ('charainfo', 'denju') and row['answers'] \
            and B6._family_of(B6._norm_text(row['japanese'])) == B6.FAM1:
        split_flags.append(dict(
            code='S5_hp_variation_unbound',
            reason='上下文写明效果量随自身剩余HP变化（「%s」句），而本行增益答案无任何 HP 档位'
                   '条件标签——增益答案缺条件单独结清，不得判完整（R1 整改 20261023）'
                   % next((s for s in re.findall(r'[^。]*。', ctx_text)
                           if '残りHP' in s and '変化' in s), '…残りHP…変化…'),
            detail=dict(namespace_table=table, answers=len(row['answers']),
                        bound_labels=[])))
    # ---- R2 整改（20261023 复审 §R2）：残余机制与未解析条件 -----------------------------
    if residual_hits:
        split_flags.append(dict(
            code='S3b_residual_mechanisms',
            reason='正文含效果词表外的机制词/谓词模板命中（状态异常/特殊机制监视表，逐子句'
                   '扫描）且无结构化覆盖——答案 quantity_kind 指认或注记结构化披露才算覆盖，'
                   '注记/条件中的纯词面与「未知/未解析/待核查/未分配」否定注记不构成完成'
                   '证据；疑似叙事过报的命中附 confidence=low 注记（保守登记不判解析）；'
                   '词表外残余内容未核实，不得判完整（R2 复审整改 20261023 第二轮）',
            detail=residual_hits[:20]))
    if unresolved_conditions:
        split_flags.append(dict(
            code='S6_unresolved_conditions',
            reason='概率类条件主张（句面隐藏数值）无载体映射与解析状态——概率值须映射到'
                   '载体触发参数（如 skilllist 触发门 /paramN）或经答案注记披露，'
                   '不能以关键词登记结清（R2 整改 20261023）',
            detail=[dict(ref_id=r['ref_id'], text=r['text'], clause_index=r['clause_index'],
                         clause=clauses[r['clause_index']][0][:80],
                         disclosed_note=r.get('disclosed_note'),
                         gap='缺：该概率条件的载体记录/触发参数映射与证据档',
                         have=('句面条件词「%s」＋%s' % (r['text'], r.get('disclosed_note')
                              or '本行答案 %d 条（均未披露该条件）' % len(row['answers']))),
                         next_step='从行链载体（own/s_ability/skill_ids 等）核对触发门参数'
                                   '（概率/条件参数）并按推断档登记映射；确认无载体时'
                                   '登记句面依据与该结论的核查记录')
                    for r in unresolved_conditions]))

    # ---- R1-High 复审整改（20261023）：same_cond 其余 pattern→t13 异值待办 --------------
    # 行 JSON 已由 card_page_data 注入结构化披露（same_cond_alt_t13，其余 pattern→t13
    # 槽值原值逐字）；选取维度（突破档/优先级/条件句对应）未解析→拆分待核查＋backlog
    # 具体项（缺口/已有证据/下一步）。不把单值 sinfo 命中行写成无条件完整。
    _sc = row.get('same_cond_alt_t13') or {}
    if _sc.get('has_diff') and (_sc.get('branches') or []):
        split_flags.append(dict(
            code='S7_same_cond_alt_t13',
            reason='源记录同一 HP 条件组内存在槽值不同的其余 pattern→t13 分支（R1-High 复审'
                   '整改 20261023 产品层披露）：本行值行为 sinfo 文本命中分支，其余分支异值'
                   '已逐字披露于行 JSON（same_cond_alt_t13）但未绑定任何条件——选取维度'
                   '（突破档/优先级/条件句↔pattern 对应）未解析，不得判完整',
            detail=[dict(slot=b.get('slot'), pid=b.get('pid'), layer=b.get('layer'),
                         t13_key=b.get('t13_key'), raws=b.get('raws'),
                         cond_label=b.get('cond_label'), sinfo_empty=b.get('sinfo_empty'),
                         same_as_selected=(b.get('sig') == _sc.get('selected_sig')),
                         gap=('缺：该分支值的选取维度证据（突破档/优先级/条件句↔pattern 对应）'
                              '与文本可解析条件分支的绑定归属'),
                         have=('已有：行 JSON same_cond_alt_t13 披露的其余 pattern→t13 槽值'
                               '原值（逐字）＋本行取值分支（sinfo 文本命中）'),
                         next_step=('引擎侧装载证据或逐 pattern 文本对照解析选取维度；对条件'
                                    '句可解析的分支（如「地形が森林の時」）按既有门逐分支评估'
                                    '绑定——能绑则各注来源条件，不能绑保留本待办；不猜测'))
                    for b in _sc['branches']]))

    # ---- 断点识别（批 6×批 8/14 跨批衔接断点，GOAL_ALIGNMENT.md G01 同构）--------------
    has_crit_2012 = any(r['rule_key'] in _BREAKPOINT_CRIT_KEYS
                        for r in answer_refs)
    unresolved_core = [e for e in effects
                       if e['status'] == 'unresolved' and e['effect_type'] in BREAKPOINT_CLAIM_TYPES]
    breakpoint = bool(has_crit_2012 and unresolved_core)

    return dict(row_id=row_id, text_n=text_n, clauses=clauses, refs=refs,
                number_refs=number_refs, effects=effects, answer_refs=answer_refs,
                split_flags=split_flags, unclassified_clauses=unclassified_clauses,
                breakpoint=breakpoint)


_OUTSIDE_TYPES = frozenset(t for t in _WORD_TYPE.values() if '词表外' in t) | {
    'クリティカル（発生率/威力未区分）'}

# ---- DS-GR-08 修复（20261023）：断点/hint 行 blocker 与 next_step 具体化 -----------------
# 缺陷：断点类未解决项 blocker 固定写「批 6 形状门遇含クリティカル句整行留 hint」，与行
# 携带的批 15 逐门失败原因（U1–U5/多 t13）不符；next_step 仍是通用核对句。
# 修复口径（审查 issues.jsonl DS-GR-08 required_fix）：
#   * 行携带 inference_b15_hint → blocker＝批 15 hint 键值逐字（批 15 reasons；promoted_b8
#     行该键还并入批 6 原注记，一并保留），next_step 按命中门生成具体核查动作；
#   * 无批 15 hint 但批 6 hint 为多 t13 歧义（审查例 20510 denju f1：「父记录有 2 个
#     type13 子记录（传授多 pattern）」）→ blocker＝多 t13 归属歧义（批 6 原因逐字），
#     next_step＝逐 pattern 区分；其余无批 15 hint 的行 blocker/next_step 不变。
# b6 G2 多 t13 原因文本锚（card_page_inference_b6_bossbuff.py:307）。
_MULTI_T13_MARK = '个 type13 子记录（传授多 pattern）'
_MULTI_T13_STEP = ('多 t13 归属歧义核查：父记录有多个 type13 子记录（传授多 pattern），'
                   '须先逐 pattern 区分本行文本对应哪条 t13（句面 pattern/段位/技能名逐字'
                   '对照并核对 boss_skill_refs 槽位），唯一化后再按并集形状归属；唯一化'
                   '不成立则逐 pattern 登记具体缺口，不猜')
_B15_GATE_STEPS = (
    ('U1', 'U1 crit 覆盖核对：逐句核对批 8/14 crit 值行（skilllist|2012 /param4 /param5）'
           '是否兑现句面全部クリティカル発生率/威力主张；缺哪项补哪项的归属证据'),
    ('U2', 'U2 链一致核对：核对批 6 链 t13 与批 8/14 中继是否同一 bossskill 记录'
           '（charainfo 行并核对同文 bosspattern 记录唯一性），排除链可达性/歧义'),
    ('U3', 'U3 并集形状核对：句主张槽（攻→/skillparam1、防→/skillparam2、移→/skillparam6、'
           '时长→/skillparam3）与 t13 活性槽双向核对；槽缺/形状不符/同文多次/竞争句'
           '逐项登记具体缺口'),
    ('U4', 'U4 方向核对：句须为「上がる」增益方向，且非 crit/时长槽原值>0；'
           '原值非正的槽按批 6 §5.4 保守留 hint，复核原值符号与句面方向'),
    ('U5', 'U5 fam 竞争核对：父记录是否另有批 6 家族句（FAM1/FAM11/FAM13）可能主张'
           '同一 t13；冲突则归属不能唯一化解，须先化解句间归属'),
)


def _b15_gate_next_step(b15_hint_text: str) -> str:
    """按批 15 hint 文本命中的门（U1–U5/多 t13）生成具体核查动作（多门并存按序全列）。

    门识别两级：①显式门码 U1–U5（b15 evaluate 直写的 hint 文本）；
    ②残余门子原因词面（b15 经 B6._gate_parent 复核批 6 残余门时，子原因不带货码——
    依据 b6 :300-330 的固定文本逐类映射：形状不符/时长槽缺/同文多次→U3；家族句/竞争句
    →U5；多 type13→多 t13；无可解析 type13→U2）。"""
    text = b15_hint_text
    gates = set()
    for g in ('U1', 'U2', 'U3', 'U4', 'U5'):
        if g in text:
            gates.add(g)
    # 残余门子原因：通用前缀本身枚举「槽缺/形状不符/多载体/同文多次/竞争句」等词，
    # 不得据以前缀判门——剥离前缀，只对「保留具体缺口）：」之后的子原因词面映射。
    parts = text.split('——保留具体缺口）：', 1)
    sub_reason = parts[1] if len(parts) == 2 else ''
    if '残余门' in text and sub_reason:
        if ('形状不符' in sub_reason or '持续时间槽' in sub_reason
                or '同文在记录正文出现' in sub_reason):
            gates.add('U3')
        if ('另有自身バフ' in sub_reason or '另有批 6 家族句' in sub_reason
                or '竞争' in sub_reason):
            gates.add('U5')
        if _MULTI_T13_MARK in sub_reason:
            gates.add('multi')
        if '无可解析的 type13' in sub_reason:
            gates.add('U2')
    if _MULTI_T13_MARK in text:
        gates.add('multi')
    steps = [desc for gate, desc in _B15_GATE_STEPS if gate in gates]
    if 'multi' in gates:
        steps.append(_MULTI_T13_STEP)
    if not steps:
        steps.append('复核批 15 hint 登记的具体缺口（见 blocker 原文），按门语义逐项核查后归属')
    return '；'.join(steps)


def _b17_gate_next_step(b17_hint_text: str) -> str:
    """批 17（P0 收尾）hint 文本→具体核查动作（分区/硬前提/映射三类缺口按词面全列）。"""
    text = b17_hint_text
    steps = []
    if '槽位分区不成立' in text or '相交' in text:
        steps.append('槽位分区复核：竞争句属性主张映射槽与 t13 活性槽相交——先化解句间归属'
                     '（确认竞争句载体或扩展槽词表），再按分区规则归属')
    if '全字段复核' in text:
        steps.append('t13 全字段复核：已分配槽外存在非零槽——核实该槽承载的主张归属后'
                     '再评分区前提')
    if '硬前提①' in text:
        steps.append('H2 硬前提①复核：兄弟 FAM1 行是否已由批 6 以同一 t13 晋级（本批运行时'
                     '重放复验未通过——核对兄弟行晋级状态与链记录）')
    if '硬前提②' in text:
        steps.append('H2 硬前提②复核：2012 载体 param0 与 t13 /skillparam3 两值不一致'
                     '（hint 内逐字披露）——需主持裁决时长归属路径后再配值')
    if '映射不唯一' in text or '归属歧义' in text:
        steps.append('多 t13 映射复核：patternidN→sinfo 唯一命中或 boss_skill_refs 归属登记'
                     '不唯一——逐 pattern 对照片段与登记后唯一化，不成立则逐 pattern 登记缺口')
    if '方向' in text:
        steps.append('方向复核：槽原值非正与句「上がる」方向冲突——核对原值符号与句面方向')
    if not steps:
        steps.append('复核批 17 hint 登记的具体缺口（见 blocker 原文），按门语义逐项核查后归属')
    return '；'.join(steps)


def _unresolved_detail(eff, row, row_meta):
    """未解决效果的缺口/候选来源/阻塞/下一步/优先级（不得只写「归批6」「以后研究」）。"""
    direction_txt = {'up': '上升', 'down': '下降', None: ''}[eff['direction']]
    hint_keys = row_meta['hint_keys']
    # DS-GR-08：行级 hint 覆盖物（批 15 逐门原因／多 t13 歧义）先于通用文本求值。
    # 批 17（20261023）：inference_b17_hint（P0 收尾未成立的具体缺口）行级替换 b15/b6
    # hint 键——blocker 优先取本行实际存在的最新 hint 键。
    b15_hint_text = row.get('inference_b17_hint') or row.get('inference_b15_hint') or None
    b15_hint_is_b17 = bool(row.get('inference_b17_hint'))
    multi_t13_txt = next((str(row.get(k)) for k in hint_keys
                          if _MULTI_T13_MARK in str(row.get(k) or '')), None)
    if eff['effect_type'] in _OUTSIDE_TYPES:
        gap = (f"句面主张「{eff['effect_type']}」{direction_txt}（片段「{eff['snippet']}」），"
               '该类型在当前效果词表外，尚无对应答案')
        if (eff['effect_type'] in _DAMAGE_TYPES and eff.get('object')
                and eff.get('object_unmatched_note')):
            # DS-GR-R1：同类型答案存在但对象不符——跨对象不硬配，未解决并注明对象歧义
            gap += ('；同类型答案存在但其对象＝'
                    + ('自身' if eff.get('object') == 'enemy' else '敵')
                    + '侧，与主张对象（'
                    + ('自身' if eff['object'] == 'self' else '敵')
                    + '）不符——跨对象不硬配（DS-GR-R1），待对象归属复核后消费')
        candidate = ['效果词表扩展：为该类型建立语义定义与来源字段映射后纳入相应专项批次']
        blocker = '效果类型词表未收录该主张；无已确认规则映射到来源字段'
        next_step = '语义分类该主张（对象/条件/数值能力），扩展词表并建立候选载体核查路径'
    else:
        gap = (f"句面主张{eff['effect_type']}{direction_txt}（片段「{eff['snippet']}」），"
               '但该行逐描述答案中没有可归属到该效果类型的条目')
        if row_meta['breakpoint']:
            candidate = ['已有2012 /param4或/param5暴击答案；其他核心效果的候选载体须由本行'
                         'source链或实际hint另行定位，暴击断点本身不证明存在type13']
            if b15_hint_text:
                # DS-GR-08 修复：blocker＝批 15/17 逐门失败原因（键值逐字，含 promoted_b8
                # 行并入的批 6 原注记）；next_step 按命中门具体化。通用批 6 G4 文本不再
                # 冒充真实阻塞。批 17 hint（行级替换 b15/b6）同法承载。
                blocker = ('批 17 P0 收尾未成立（逐门原因）：' if b15_hint_is_b17
                           else '批 15 并集归属不成立（逐门原因，DS-GR-08 修复）：') + b15_hint_text
                next_step = _b17_gate_next_step(b15_hint_text) if b15_hint_is_b17                     else _b15_gate_next_step(b15_hint_text)
            elif multi_t13_txt:
                # 审查例 20510 denju f1：无批 15 hint（批 8/14 未晋级、批 15 未评估），
                # 真实阻塞＝批 6 G2 多 t13 歧义——blocker/next_step 随之具体化。
                blocker = '多 t13 归属歧义（批 6 G2，DS-GR-08 修复）：' + multi_t13_txt \
                          + '——唯一 t13 前提不成立，批 15 并集归属未评估'
                next_step = _MULTI_T13_STEP
            else:
                blocker = '已有暴击答案，但其他核心效果尚无已证明的字段归属；不能由断点优先级推定载体类型'
                next_step = ('从本行source记录链核对剩余主张的对象、条件与活性字段；实际找到候选后'
                             '逐项绑定，未找到则保留未知，不预设type13')
        else:
            candidate = ([f'既有 hint 线索（{k}）' for k in hint_keys]
                         or ['从行记录 source 链定位候选载体记录（先 own sub/s_ability，后跨表）'])
            if b15_hint_text:
                # 非 breakpoint 但行携带批 15/17 hint（如未解决主张均在词表外的复合行）：
                # blocker 同样以批 15/17 逐门原因为准（hint 键是行级事实）。
                blocker = ('批 17 P0 收尾未成立（逐门原因）：' if b15_hint_is_b17
                           else '批 15 并集归属不成立（逐门原因，DS-GR-08 修复）：') + b15_hint_text
                next_step = _b17_gate_next_step(b15_hint_text) if b15_hint_is_b17                     else _b15_gate_next_step(b15_hint_text)
            elif multi_t13_txt:
                blocker = '多 t13 归属歧义（批 6 G2，DS-GR-08 修复）：' + multi_t13_txt \
                          + '——唯一 t13 前提不成立，候选载体不唯一'
                next_step = _MULTI_T13_STEP
            else:
                blocker = '无已确认规则将该句面效果映射到来源字段；归属未经证明，不硬填'
                next_step = ('复核既有 hint 线索对应的载体与规则；无线索则从行 source 记录链'
                             '定位候选载体，核对活性槽与句面属性形状后再出值')
    if hint_keys:
        candidate += [f'{k}: {str(row.get(k))[:160]}' for k in hint_keys]
    return dict(gap=gap, candidate_sources=candidate, blocker=blocker,
                next_step=next_step)  # priority 由行级统一填


def _card_title_yg(card):
    title = ''.join(f.get('raw_value') or '' for f in card['basic']['fields']
                    if f.get('key') == 'title')
    return 'Y.G.' in _nfkc(title)


def build(pages_root: Path):
    """扫描全部卡页并产出（snapshot, descriptions, effects, cards, yg_cards）。"""
    rules_sha = hashlib.sha256(RULES_PATH.read_bytes()).hexdigest()[:16] if RULES_PATH.exists() else None
    campaign_sig = None
    if CAMPAIGN_LATEST.exists():
        ptr = json.loads(CAMPAIGN_LATEST.read_text(encoding='utf-8-sig'))
        rep_path = pages_root / ptr['report']
        if rep_path.exists():
            campaign_sig = json.loads(rep_path.read_text(encoding='utf-8-sig')).get('signature')
    snapshot = dict(pages_root=pages_root.as_posix(),
                    campaign_signature=campaign_sig,
                    rules_json=RULES_PATH.as_posix(),
                    rules_json_sha256_16=rules_sha,
                    generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    snapshot_id = f"{(campaign_sig or 'nosig')[:8]}-{rules_sha or 'norules'}"
    snapshot['snapshot_id'] = snapshot_id

    descriptions, effects = [], []
    cards = yg_cards = 0
    for d in sorted(pages_root.iterdir(), key=lambda p: (len(p.name), p.name)):
        p = d / 'card.json'
        if not (d.is_dir() and p.is_file()):
            continue
        try:
            int(d.name)
        except ValueError:
            continue
        card = json.loads(p.read_text(encoding='utf-8-sig'))
        cards += 1
        is_yg = _card_title_yg(card)
        yg_cards += is_yg
        for g in card['groups']:
            for s in g['skills']:
                for row in s['rows']:
                    _emit_row(row, s, is_yg, snapshot, snapshot_id, descriptions, effects)
    return snapshot, descriptions, effects, cards, yg_cards


B18_OWN_RECORD_KEYS = frozenset({'skilllist|64|/param4'})
B18_EVIDENCE_SCOPE = 'B18_OWN_RECORD_B64_PARAM4_EXTRAPOLATED'
B18_ROW_ALLOWLIST = {
    6037: {
        'row_id': '6037-ability-ability-skillid_1_-lvorder0-f0',
        'skill_id': '6037/ability/ability/skillid[1]',
        'record_id': 13507,
        'record_key': 'APK/_mdSkill.json#/skilllist/2137',
        'source_key': 'APK/_mdSkill.json',
        'layer': 'APK',
        'original_file': 'output/base_master/_mdSkill.json',
        'json_pointer': '/skilllist/2137',
        'raw_record_sha256': '8a3318160cf1a0883b12b65852b0a3691e1fd126902bbc64e890cddce401839f',
        'master_source': 'work\\apk\\assets\\chronicle.dat',
        'master_source_sha256': 'd1af417ee34b07f84ecd66c2404b34880d25fd2c7634a66b4f57046762386b7d',
        'master_converted_sha256': '46972b0bb5003c982548473cee6fe4b3fcbd9bb28ca04f69d202155eaf975f5f',
        'field_json_pointer': '/skilllist/2137/text',
        'clean_span': [0, 82],
        'raw_span': [0, 82],
        'phrase': 'クリティカル率',
        'phrase_start': 57,
        'row_text': 'どうにもこうにも斬りたくてしょうがないんですよ…さあ、死合いましょう！WAVEが進むたび、自身の攻撃力と移動速度とクリティカル率が一定時間上がるが、防御力も下がる。',
        'row_text_sha256': 'f6d94f3324db58f7a7adcbab8fc66146d657a33d048e2064fffcecde2165d2ed',
        'skill_text_sha256': '8a808079e5cbfce5f31d7e76ec4cc68de08641a53a762014175146c405c61657',
    },
    6055: {
        'row_id': '6055-ability-ability-skillid_1_-lvorder0-f0',
        'skill_id': '6055/ability/ability/skillid[1]',
        'record_id': 13537,
        'record_key': 'APK/_mdSkill.json#/skilllist/2167',
        'source_key': 'APK/_mdSkill.json',
        'layer': 'APK',
        'original_file': 'output/base_master/_mdSkill.json',
        'json_pointer': '/skilllist/2167',
        'raw_record_sha256': '272b1f4384c114094de4aef50318d8e92f689af69971cdbc217dde718f1d4c4f',
        'master_source': 'work\\apk\\assets\\chronicle.dat',
        'master_source_sha256': 'd1af417ee34b07f84ecd66c2404b34880d25fd2c7634a66b4f57046762386b7d',
        'master_converted_sha256': '46972b0bb5003c982548473cee6fe4b3fcbd9bb28ca04f69d202155eaf975f5f',
        'field_json_pointer': '/skilllist/2167/text',
        'clean_span': [0, 50],
        'raw_span': [0, 50],
        'phrase': 'クリティカル率',
        'phrase_start': 34,
        'row_text': '我こそが海を総べる第十領主である！WAVEが進むたび、自身の攻撃力とクリティカル率を一定時間上げる。',
        'row_text_sha256': '5cc9811b3ab0e699ee61914487f359650a4aaa9df5680a0cd23a0d556ce5320d',
        'skill_text_sha256': '577cc42ebafdececbc3b457921669341f57fea1b94b72c504710145298ea7073',
    },
}


def _b18_text_sha256(text: str) -> str:
    return hashlib.sha256(str(text).encode('utf-8')).hexdigest()


def _b18_row_spec(row: dict):
    row_id = str(row.get('row_id') or '')
    try:
        cid = int(row_id.split('-', 1)[0])
    except (TypeError, ValueError):
        return None, None
    spec = B18_ROW_ALLOWLIST.get(cid)
    if spec is None or row_id != spec['row_id']:
        return None, None
    return cid, spec


B18_APK_SKILL_PATH = read_path(Path('output/base_master/_mdSkill.json'))
_B18_APK_SKILL_INDEX: dict[int, dict] | None = None
B18_SOURCE_IDENTITY_FIELDS = (
    'record_key', 'source_key', 'layer', 'original_file', 'json_pointer',
    'raw_record_sha256', 'master_source', 'master_source_sha256',
    'master_converted_sha256',
)


def _b18_actual_apk_record(data, record_id: int) -> dict | None:
    """取同源真实 APK skilllist 记录；优先使用当前 Inputs.apk_skill。"""
    if data is not None and hasattr(data, 'apk_skill'):
        hit = data.apk_skill.get(record_id)
        if hit is not None:
            return hit[1] if isinstance(hit, tuple) and len(hit) == 2 else hit
        return None
    global _B18_APK_SKILL_INDEX
    if _B18_APK_SKILL_INDEX is None:
        doc = json.loads(B18_APK_SKILL_PATH.read_text(encoding='utf-8-sig'))
        _B18_APK_SKILL_INDEX = {r.get('skillid'): r for r in doc.get('skilllist') or []}
    return _B18_APK_SKILL_INDEX.get(record_id)


def _b18_finite_number(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _b18_source_identity_matches(source: dict, spec: dict) -> list[str]:
    return [f'{field} 不符' for field in B18_SOURCE_IDENTITY_FIELDS
            if (source or {}).get(field) != spec[field]]


def validate_b18_own_record(row: dict, skill: dict, data=None, cid: int | None = None):
    """验证并返回唯一已绑定的 (spec, evidence, answer, failures)。

    身份链：调用 cid＝row.cid＝row_id 前缀；row/skill/evidence 三侧 source 同源；
    evidence 与真实 APK payload 全对象相等；answer.raw 精确等于真实 payload.param4。
    """
    inferred_cid, spec = _b18_row_spec(row)
    if spec is None:
        return None, None, None, ['row_id 不在 6037/6055 显式准入表']
    failures = []
    if cid is not None and inferred_cid != cid:
        failures.append('调用 cid 与 row_id 前缀不符')
    if row.get('cid') != inferred_cid:
        failures.append('row.cid 与 row_id 前缀不符')
    if skill.get('table') != 'skilllist' or skill.get('skill_id') != spec['skill_id']:
        failures.append('skill table/id 不符')
    if skill.get('record_id') != spec['record_id']:
        failures.append('skill record_id 不符')
    if skill.get('layer') != spec['layer']:
        failures.append('skill layer 不符')
    if row.get('japanese') != spec['row_text']:
        failures.append('row 正文不逐字匹配')
    if _b18_text_sha256(row.get('japanese') or '') != spec['row_text_sha256']:
        failures.append('row 正文 SHA-256 不符')
    if _b18_text_sha256(skill.get('original_text') or '') != spec['skill_text_sha256']:
        failures.append('skill original_text SHA-256 不符')
    if str(row.get('japanese') or '').find(spec['phrase']) != spec['phrase_start']:
        failures.append('明确 crit 率子句位置不符')

    row_source = row.get('source') or {}
    skill_source = skill.get('source') or {}
    source_position = row.get('source_position') or {}
    failures.extend(f'row.source.{x}' for x in _b18_source_identity_matches(row_source, spec))
    failures.extend(f'skill.source.{x}' for x in _b18_source_identity_matches(skill_source, spec))
    if row_source.get('field') != '/text':
        failures.append('row.source.field 不是 /text')
    if row_source.get('field_json_pointer') != spec['field_json_pointer']:
        failures.append('row.source.field_json_pointer 不符')
    if source_position.get('clean_span') != spec['clean_span']:
        failures.append('row.source_position.clean_span 不符')
    if source_position.get('raw_span') != spec['raw_span']:
        failures.append('row.source_position.raw_span 不符')
    if source_position.get('field_pointer') != spec['field_json_pointer']:
        failures.append('row.source_position.field_pointer 不符')
    if source_position.get('source_key') != spec['source_key']:
        failures.append('row.source_position.source_key 不符')

    original_text = str(skill.get('original_text') or '')
    if original_text[spec['clean_span'][0]:spec['clean_span'][1]] != spec['row_text']:
        failures.append('skill.original_text 的 clean_span 不指向本行正文')

    # 先收集同 record_id/ability 的全部候选；任一重复（即使值相同或看似无效）都拒绝。
    candidates = []
    for evidence in skill.get('record_evidence') or []:
        raw = evidence.get('raw_record') or {}
        if evidence.get('record_id') == spec['record_id'] and raw.get('ability') == 64:
            candidates.append(evidence)
    if len(candidates) != 1:
        failures.append(f'own-record evidence 不唯一（命中 {len(candidates)}）')
        return spec, None, None, failures
    evidence = candidates[0]
    raw = evidence.get('raw_record') or {}
    ev_source = evidence.get('source') or {}
    if raw.get('skillid') != spec['record_id']:
        failures.append('raw_record.skillid 不符')
    failures.extend(f'evidence.source.{x}' for x in _b18_source_identity_matches(ev_source, spec))

    answers = [a for a in (evidence.get('answers') or [])
               if a.get('rule_key') == 'skilllist|64|/param4' and a.get('f') == '/param4']
    if len(answers) != 1:
        failures.append(f'/param4 原证据不唯一（命中 {len(answers)}）')
        return spec, evidence, None, failures
    answer = answers[0]

    actual = _b18_actual_apk_record(data, spec['record_id'])
    if actual is None:
        failures.append('同源 APK 记录不存在')
    else:
        if raw != actual:
            failures.append('raw_record payload 与同源 APK 记录不完全相等')
        if 'param4' not in raw or raw.get('param4') is None:
            failures.append('raw_record.param4 缺失或 null')
        elif not _b18_finite_number(raw.get('param4')):
            failures.append('raw_record.param4 非有限数值')
        if 'param4' not in actual or actual.get('param4') is None:
            failures.append('同源 APK param4 缺失或 null')
        actual_param4 = actual.get('param4')
        if not _b18_finite_number(actual_param4):
            failures.append('同源 APK param4 非有限数值')
        answer_raw = answer.get('raw')
        if not _b18_finite_number(answer_raw):
            failures.append('evidence answer.raw 非有限数值')
        if (_b18_finite_number(answer_raw) and _b18_finite_number(actual_param4)
                and answer_raw != actual_param4):
            failures.append('evidence answer.raw 与同源 APK param4 不相等')
    return spec, evidence, answer, failures


def consume_b18_own_record_answers(row: dict, skill: dict, data=None, cid: int | None = None) -> list[dict]:
    """仅消费 validate 返回的同一 evidence/answer 对象；不重新 next 选择。"""
    spec, evidence, answer, failures = validate_b18_own_record(row, skill, data=data, cid=cid)
    if failures:
        return []
    existing = {a.get('rule_key') for a in (row.get('answers') or [])}
    if existing & B18_OWN_RECORD_KEYS:
        return []
    ev_source = dict(evidence.get('source') or {})
    note = ('批18 own-record 消费：值来自 ability64 的既有 /param4 规则（已核样本 occ1），'
            '本条 APK 记录适用域、中文表述及句内关联均为规则外推；不等于逐记录原生确认。')
    return [dict(
        table='skilllist', record_id=evidence.get('record_id'), layer=ev_source.get('layer'),
        rule_key=answer['rule_key'], field_path='/param4',
        raw_value=answer.get('raw'), value=answer.get('value'),
        quantity_kind=answer.get('kind'), unit=answer.get('unit'),
        conversion=answer.get('conversion'), conditions=answer.get('conditions'),
        base_definition=answer.get('base_definition'), note=note,
        numeric_evidence='推断', association_evidence='推断',
        numeric_source='既有 ability64 规则字段（occ1 外推）',
        evidence_scope=B18_EVIDENCE_SCOPE, quantitative=True,
        source=ev_source, source_key=ev_source.get('source_key'),
        json_pointer=ev_source.get('json_pointer'),
        raw_record_sha256=ev_source.get('raw_record_sha256'),
    )]


def apply_to_groups(data, cid: int, groups: list[dict]) -> list[dict]:
    """coverage 前只追加两条允许行的 /param4，并保留旧答案。"""
    if cid not in B18_ROW_ALLOWLIST or (hasattr(data, 'cids') and cid not in data.cids):
        return []
    applied = []
    for group in groups:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                promoted = consume_b18_own_record_answers(row, skill, data=data, cid=cid)
                if not promoted:
                    continue
                answer = promoted[0]
                before = list(row.get('answers') or [])
                if any(a.get('rule_key') == answer['rule_key'] for a in before):
                    continue
                answers = before + [answer]
                row['answers'] = answers
                before_class = row.get('row_class')
                row['row_class'] = 'A'
                row['evidence'] = '推断'
                row['numeric_evidence'] = '推断'
                row['association_evidence'] = '推断'
                row['partial'] = True
                scopes = set(row.get('evidence_scope') or [])
                scopes.add(B18_EVIDENCE_SCOPE)
                row['evidence_scope'] = sorted(scopes)
                reasons = list(row.get('unknown_reasons') or [])
                reason = ('批18：/param4 来自 ability64 规则外推，非本 APK 记录逐记录原生确认；'
                          '其余句面主张未由本接口补值。')
                if reason not in reasons:
                    reasons.append(reason)
                row['unknown_reasons'] = reasons
                row['inference_b18_wordface'] = True
                row['b18_wordface_answer_keys'] = [answer['rule_key']]
                applied.append(dict(cid=cid, row_id=row['row_id'],
                                    before_class=before_class, after_class='A',
                                    before_answer_count=len(before), after_answer_count=len(answers),
                                    rule_key=answer['rule_key'], raw_value=answer['raw_value'],
                                    source=answer['source']))
    return applied


def _emit_row(row, skill, is_yg, snapshot, snapshot_id, descriptions, effects):
    row_id = row['row_id']
    # 页面答案必须先由 apply_to_groups 写入 row['answers']；这里不临时拼接 phantom answer。
    res = analyze_row(row, table=skill.get('table'))
    # 只把已经存在于页面答案中的批18来源复制到效果 provenance，便于正式 checker 追源。
    for answer_index, answer in enumerate(row.get('answers') or []):
        if answer.get('evidence_scope') != B18_EVIDENCE_SCOPE:
            continue
        matched_effects = [effect for effect in res['effects']
                           if any(ref.get('answer_index') == answer_index
                                  and ref.get('rule_key') == answer.get('rule_key')
                                  and ref.get('raw_value') == answer.get('raw_value')
                                  for ref in (effect.get('answer_refs') or []))]
        for effect in matched_effects:
            effect.setdefault('promotion_provenance', []).append(dict(
                rule_key=answer.get('rule_key'), field_path=answer.get('field_path'),
                raw_value=answer.get('raw_value'), value=answer.get('value'),
                table=answer.get('table'), record_id=answer.get('record_id'),
                layer=answer.get('layer'), source=dict(answer.get('source') or {}),
                evidence_scope=answer.get('evidence_scope'),
                numeric_evidence=answer.get('numeric_evidence'),
                association_evidence=answer.get('association_evidence'),
                note=answer.get('note'),
            ))
    src = row['source'] or {}
    # 批次推断键是行级顶层键（inference_bN 晋级／inference_bN_hint 留守；行键清单无 metadata 键）
    inference_keys = sorted(k for k in row if k.startswith('inference_'))
    hint_keys = [k for k in inference_keys if k.endswith('_hint')]
    promo_keys = [k for k in inference_keys if not k.endswith('_hint')]
    row_meta = dict(hint_keys=hint_keys, breakpoint=res['breakpoint'])
    # 行级优先级（README 写明规则）：P0 衔接断点 > P1 Y.G. > P2 其他
    priority = 'P0' if res['breakpoint'] else ('P1' if is_yg else 'P2')

    # P1 复查修正（20261023）：行级 source 无 table 键（此前 namespace.table 恒 None）；
    # 来源表取自所属 skill 条目（审查 audit.py:72 同法），回退行 source。
    namespace = dict(layer=src.get('layer'), table=skill.get('table') or src.get('table'),
                     record_id=src.get('record_id'), source_key=src.get('source_key'))
    for eff in res['effects']:
        if eff['status'] == 'unresolved':
            eff['unresolved'] = _unresolved_detail(eff, row, row_meta)
            eff['unresolved']['priority'] = priority
        eff['snapshot_id'] = snapshot_id
        eff['namespace'] = namespace
        eff['cid'] = row['cid']
        effects.append(eff)

    statuses = [e['status'] for e in res['effects']]
    n_answer = statuses.count('has_answer')
    n_unres = statuses.count('unresolved')
    n_na = statuses.count('justified_na')
    if res['split_flags'] or not res['effects']:
        row_status = '拆分待核查'
    elif n_unres == 0:
        row_status = '完整'
    elif n_answer + n_na > 0:
        row_status = '部分'
    else:
        row_status = '未解析'

    descriptions.append(dict(
        record_type='description', ledger_id=row_id, row_id=row_id, cid=row['cid'], yg=is_yg,
        input_snapshot=dict(snapshot_id=snapshot_id,
                            campaign_signature=snapshot['campaign_signature'],
                            rules_json_sha256_16=snapshot['rules_json_sha256_16'],
                            pages_root=snapshot['pages_root']),
        namespace=namespace, skill_category=row['group'], skill=skill.get('skill'),
        slot=dict(stage=row['stage'], reference_field=row['reference_field'],
                  fragment_index=row['fragment_index'], level=row['level']),
        japanese=row['japanese'], japanese_nfkc=res['text_n'],
        japanese_nfkc_sha256_16=_short_sha(res['text_n']),
        row_class=row['row_class'], row_evidence=row['evidence'],
        original_A=row.get('original_A'), legacy_partial_flag=row.get('partial'),
        evidence_label=row.get('evidence_label'), evidence_scope=row.get('evidence_scope'),
        hint_keys=hint_keys, promotion_keys=promo_keys,
        refs=res['refs'], number_refs=res['number_refs'],
        effect_ids=[e['effect_id'] for e in res['effects']],
        effect_status_counts=dict(has_answer=n_answer, unresolved=n_unres, justified_na=n_na),
        ledger_row_status=row_status, split_flags=res['split_flags'],
        breakpoint=res['breakpoint'],
        unmatched_answer_refs=[r for r in res['answer_refs'] if r['matched_effect_id'] is None],
        answer_ref_count=len(res['answer_refs'])))
    # R1 整改（20261023）：共享条件引用——「随HP变化」句行引用同技能内已按 HP 档位绑定
    # 的增益行（前句↔后续句共享同一 HP 档位条件结构；不新增/不改任何状态与答案）。
    _desc = descriptions[-1]
    if '残りHP' in res['text_n'] and '変化' in res['text_n']:
        _sibs = []
        for _sr in (skill.get('rows') or []):
            if _sr is row or not _sr.get('answers'):
                continue
            if B6._family_of(B6._norm_text(_sr['japanese'])) != B6.FAM1:
                continue
            _labs = sorted({str(a.get('condition_label')) for a in _sr['answers']
                            if str(a.get('condition_label') or '').startswith('HP ')})
            if _labs:
                _sibs.append(dict(row_id=_sr['row_id'], hp_branch_conditions=_labs))
        if _sibs:
            _desc['shared_condition_refs'] = _sibs
    _hp_bound = sorted({str(a.get('condition_label')) for _sr in ([row] + list(skill.get('rows') or []))
                        for a in (_sr.get('answers') or [])
                        if str(a.get('condition_label') or '').startswith('HP ')})
    if _hp_bound:
        _desc['hp_branch_conditions'] = _hp_bound


def run(pages_root: Path, out_dir: Path):
    snapshot, descriptions, effects, cards, yg_cards = build(pages_root)
    desc_by_id = {d['row_id']: d for d in descriptions}

    # ---- 自检（A2 覆盖 / A3 对账 / A4 集合差） ---------------------------------------
    checks = []
    row_ids = [d['row_id'] for d in descriptions]
    checks.append(dict(check='A2 描述入口唯一（每行恰一入口，row_id 无重复）',
                       passed=len(row_ids) == len(set(row_ids)),
                       detail=dict(description_entries=len(row_ids),
                                   unique_row_ids=len(set(row_ids)))))
    eff_ids = [e['effect_id'] for e in effects]
    checks.append(dict(check='A2 effect_id 唯一', passed=len(eff_ids) == len(set(eff_ids)),
                       detail=dict(effects=len(eff_ids), unique=len(set(eff_ids)))))
    dangling = [e['effect_id'] for e in effects if e['description_ref'] not in desc_by_id]
    checks.append(dict(check='A2 无悬空效果引用', passed=not dangling,
                       detail=dict(dangling=len(dangling), examples=dangling[:5])))

    st = collections.Counter(e['status'] for e in effects)
    total_status = st['has_answer'] + st['unresolved'] + st['justified_na']
    checks.append(dict(check='A3 已识别效果总数=有答案+未解决+有依据不适用（三类互斥）',
                       passed=total_status == len(effects),
                       detail=dict(effects_total=len(effects), has_answer=st['has_answer'],
                                   unresolved=st['unresolved'], justified_na=st['justified_na'])))

    # A3：答案引用全部可解析（row_id+field_path+raw_value+answer_index 独立重读页面核对）
    # 读卡复用（2026-10-29，C7-P1 工程项，只改性能）：仍对**每张卡独立重读一次**页面文件
    # （不复用 build 阶段已解析对象，来源核验语义不变），并按卡建立 row_id→首次出现行的
    # 临时索引，核该卡全部行后随 cid 切换整体释放，不跨卡/跨运行保留。取三元组与错误行为
    # （行缺失、r['answers'] 缺失）与原逐描述重读逐字一致：索引只做首次出现选择（原
    # next(...) 同法），三元组仍在该行被引用时按原位表达式求值。
    answer_index_by_row = {}
    bad_refs, resolved = [], 0
    card_row_index = {}
    card_row_index_cid = None
    for d in descriptions:
        if d['cid'] != card_row_index_cid:
            card = json.loads((pages_root / str(d['cid']) / 'card.json').read_text(encoding='utf-8-sig'))
            card_row_index = {}
            for g in card['groups']:
                for s in g['skills']:
                    for r in s['rows']:
                        card_row_index.setdefault(r['row_id'], r)  # 同 row_id 取首次出现
            card_row_index_cid = d['cid']
            del card  # 只保留本卡行对象索引；切卡时旧索引被回收
        r = card_row_index.get(d['row_id'])
        if r is None:
            bad_refs.append(dict(row_id=d['row_id'], reason='行在页面中不存在'))
            continue
        answer_index_by_row[d['row_id']] = [(a.get('field_path'), a.get('raw_value'))
                                            for a in r['answers']]
    card_row_index = {}
    card_row_index_cid = None
    for e in effects:
        for ref in e.get('answer_refs') or []:
            key = ref['resolvable_key']
            triples = answer_index_by_row.get(key['row_id'])
            if triples is None:
                bad_refs.append(dict(effect_id=e['effect_id'], reason='行缺失'))
                continue
            idx = key['answer_index']
            if not (0 <= idx < len(triples)):
                bad_refs.append(dict(effect_id=e['effect_id'], reason='answer_index 越界'))
                continue
            fp, rv = triples[idx]
            if fp == key['field_path'] and rv == key['raw_value']:
                resolved += 1
            else:
                bad_refs.append(dict(effect_id=e['effect_id'], reason='field_path/raw_value 不一致',
                                     ledger=dict(field_path=key['field_path'], raw_value=key['raw_value']),
                                     page=dict(field_path=fp, raw_value=rv)))
    checks.append(dict(check='A3 答案引用可解析（row_id+field_path+raw_value+answer_index，页面独立重读）',
                       passed=not bad_refs, detail=dict(resolved=resolved, failures=len(bad_refs),
                                                        examples=bad_refs[:5])))
    bad_complete = [d['row_id'] for d in descriptions
                    if d['ledger_row_status'] == '完整'
                    and (d['effect_status_counts']['unresolved'] > 0 or d['split_flags'])]
    checks.append(dict(check='A3 完整描述未解决项=0 且无拆分待核查标志',
                       passed=not bad_complete, detail=dict(violations=len(bad_complete),
                                                            examples=bad_complete[:5])))
    bad_na = [e['effect_id'] for e in effects
              if e['status'] == 'justified_na' and not e.get('na_basis')]
    checks.append(dict(check='A3 有依据不适用项必须带逐条 na_basis',
                       passed=not bad_na, detail=dict(violations=len(bad_na))))

    # ---- 正式待办（A4） ----------------------------------------------------------------
    backlog = []
    for e in effects:
        if e['status'] == 'unresolved':
            d = desc_by_id[e['description_ref']]
            backlog.append(dict(kind='effect', backlog_id=e['effect_id'],
                                row_id=e['description_ref'], cid=e['cid'], yg=d['yg'],
                                effect_type=e['effect_type'], direction=e['direction'],
                                snippet=e['snippet'], gap=e['unresolved']['gap'],
                                candidate_sources=e['unresolved']['candidate_sources'],
                                blocker=e['unresolved']['blocker'],
                                next_step=e['unresolved']['next_step'],
                                priority=e['unresolved']['priority'],
                                breakpoint=d['breakpoint']))
    for dsc in descriptions:
        if dsc['ledger_row_status'] == '拆分待核查':
            # R1-High/R2-Low 复审整改（20261023）：标志携带 gap/have/next_step 的（S5 部分/
            # S6/S7）把具体待办结构化并入 backlog 条目（缺口/已有证据/下一步）。
            _fd = []
            for f in dsc['split_flags']:
                det = f.get('detail')
                for it in (det if isinstance(det, list) else
                           ([det] if isinstance(det, dict) else [])):
                    if isinstance(it, dict) and it.get('gap'):
                        _fd.append(dict(code=f['code'], gap=it['gap'],
                                        have=it.get('have'), next_step=it.get('next_step')))
            _item = dict(
                kind='description_split_check', backlog_id=f"{dsc['row_id']}#split",
                row_id=dsc['row_id'], cid=dsc['cid'], yg=dsc['yg'],
                effect_type=None, direction=None, snippet=dsc['japanese'][:120],
                gap='；'.join(f['reason'] for f in dsc['split_flags']) or '拆分可靠性未确认',
                candidate_sources=[f['code'] for f in dsc['split_flags']],
                blocker='效果拆分可靠性未确认：零识别/未覆盖子句/数字语义未确认/答案未对应主张',
                next_step='人工语义核查该描述的效果构成；确认后逐效果登记进账本并可退出本类待办',
                priority=('P0' if dsc['breakpoint'] else ('P1' if dsc['yg'] else 'P2')),
                breakpoint=dsc['breakpoint'],
                split_flag_codes=[f['code'] for f in dsc['split_flags']])
            if _fd:
                _item['flag_detail'] = _fd
            backlog.append(_item)
    backlog.sort(key=lambda x: ({'P0': 0, 'P1': 1, 'P2': 2}.get(x.get('priority') or 'P2', 2),
                                x['cid'], x['row_id']))

    unresolved_ids = {e['effect_id'] for e in effects if e['status'] == 'unresolved'}
    split_ids = {d['row_id'] for d in descriptions if d['ledger_row_status'] == '拆分待核查'}
    backlog_effect_ids = {b['backlog_id'] for b in backlog if b['kind'] == 'effect'}
    backlog_split_ids = {b['row_id'] for b in backlog if b['kind'] == 'description_split_check'}
    missing_in_backlog = (unresolved_ids - backlog_effect_ids) | (split_ids - backlog_split_ids)
    extra_in_backlog = (backlog_effect_ids - unresolved_ids) | (backlog_split_ids - split_ids)
    checks.append(dict(
        check='A4 待办集合差双向为空（账本未解决∪拆分待核查 ↔ backlog）',
        passed=not missing_in_backlog and not extra_in_backlog,
        detail=dict(unresolved_effects=len(unresolved_ids), split_check_rows=len(split_ids),
                    backlog_items=len(backlog),
                    missing_in_backlog=len(missing_in_backlog),
                    extra_in_backlog=len(extra_in_backlog),
                    examples_missing=sorted(missing_in_backlog)[:5],
                    examples_extra=sorted(extra_in_backlog)[:5])))
    probe = collections.Counter()
    for b in backlog:
        d = desc_by_id.get(b['row_id'])
        if d is None:
            continue
        if d['row_class'] == 'A' and d['legacy_partial_flag']:
            probe['A_partial'] += 1
        if d['promotion_keys']:
            probe['promoted'] += 1
        if d['hint_keys']:
            probe['hinted'] += 1
        if d['original_A']:
            probe['original_A'] += 1
    checks.append(dict(check='A4 backlog 构成可见（A 类部分行/已晋级/带 hint/原文A 行均在队）',
                       passed=True, detail=dict(probe)))

    failed = [c for c in checks if not c['passed']]

    # ---- 指标（任务书 §三.4；证据档与完整度分开；Y.G. 单列） ---------------------------
    def count_desc(pred):
        return dict(all=sum(1 for d in descriptions if pred(d)),
                    yg=sum(1 for d in descriptions if d['yg'] and pred(d)))

    def count_eff(pred):
        return dict(all=sum(1 for e in effects if pred(e)),
                    yg=sum(1 for e in effects
                           if pred(e) and desc_by_id[e['description_ref']]['yg']))

    effect_grade_profile = collections.Counter(
        ('+'.join(e['evidence_grades']) or '未知')
        for e in effects if e['status'] == 'has_answer')
    effect_grade_yg = collections.Counter(
        ('+'.join(e['evidence_grades']) or '未知')
        for e in effects if e['status'] == 'has_answer'
        and desc_by_id[e['description_ref']]['yg'])

    metrics = dict(
        generated_at=snapshot['generated_at'], snapshot=snapshot,
        definitions=dict(
            descriptions_total='描述总数＝当前 pages 全部 card.json 的行数（从文件重算；分母＝全部行，含 A/C 各类）',
            descriptions_split_check='拆分待核查描述数＝账本行级状态为拆分待核查的行（S1 零识别/S2 数字语义未确认（角色绑定映射——数值相等只是必要线索，R2 复审整改 20261023 第二轮）/S3 未覆盖子句/S3b 词表外机制词/谓词模板无结构化覆盖（否定注记不构成完成证据，R2 复审整改 20261023 第二轮）/S4 答案未对应主张/S5 HP 档位分支覆盖不完整或「随HP变化」句增益答案缺条件绑定——R1 整改/S6 概率类条件无载体映射——R2 整改/S7 同 HP 条件组其余 pattern→t13 异值、选取维度未解析——R1-High 复审整改 20261023）',
            descriptions_complete='完整描述数＝行内全部已识别效果为有答案或有依据不适用、且无拆分待核查标志（≥1 个已识别效果）',
            descriptions_partial='部分描述数＝既有有答案/不适用效果、又有未解决效果，且无拆分待核查标志',
            descriptions_unparsed='未解析描述数＝有已识别效果但全部未解决，且无拆分待核查标志',
            effects_identified_total='已识别效果数＝当前词表从句面识别出的效果主张＋定性 NA 判定条目；'
                                     '注意：这不是全库全部效果数——拆分待核查行中未被识别的效果未计入，'
                                     '不得把该分母宣传为全库总效果数或据此计算总完成率',
            effects_has_answer='有答案效果数（证据档在 evidence_grades）',
            effects_unresolved='未解决效果数（进入 backlog kind=effect）',
            effects_justified_na='有依据的不适用项数（每项带逐条 na_basis；P1 仅出具「できない」禁止型窄类判定，'
                                 '其余纯定性机制一律未解决，不把 NA 当兜底）',
            evidence_grades='证据档计数独立于完整度：按效果所引答案的 numeric/association 证据档组合统计',
            yg='Y.G.＝卡 title 含「Y.G.」（审查 audit.py:63 同法）；每指标单列 yg 计数',
            priority='优先级规则：P0＝衔接断点行（已有 2012 暴击答案且句面攻/防/移/时长主张未解决——批6×批8/14 断点）；'
                     'P1＝Y.G. 卡其余未解决/待核查；P2＝其他。衔接断点与 Y.G. 优先（任务书 §五）',
            snapshot_anchor='输入快照锚点：campaign 签名与 rules.json SHA-256 前 16 位均从当前文件重算',
            row_status_vs_partial='行级完整度由账本派生，独立于 A/C 与 legacy partial 标志；'
                                  '两者差异可由 descriptions.legacy_partial_cross 对账，未强行对齐'),
        rows=dict(cards=cards, descriptions=len(descriptions), effects=len(effects),
                  yg_cards=yg_cards),
        descriptions=dict(
            total=count_desc(lambda d: True),
            complete=count_desc(lambda d: d['ledger_row_status'] == '完整'),
            partial=count_desc(lambda d: d['ledger_row_status'] == '部分'),
            unparsed=count_desc(lambda d: d['ledger_row_status'] == '未解析'),
            split_check=count_desc(lambda d: d['ledger_row_status'] == '拆分待核查'),
            by_ledger_status=dict(collections.Counter(d['ledger_row_status'] for d in descriptions)),
            by_row_class=dict(collections.Counter(d['row_class'] for d in descriptions)),
            breakpoint_rows=count_desc(lambda d: d['breakpoint']),
            row_evidence_grades=dict(collections.Counter(d['row_evidence'] for d in descriptions)),
            row_evidence_grades_yg=dict(collections.Counter(d['row_evidence'] for d in descriptions if d['yg'])),
            legacy_partial_cross={'/'.join(map(str, k)): v for k, v in collections.Counter(
                (d['ledger_row_status'], bool(d['legacy_partial_flag'])) for d in descriptions).items()},
        ),
        effects=dict(
            identified_total=count_eff(lambda e: True),
            by_status={k: count_eff(lambda e, k=k: e['status'] == k) for k in st},
            by_type=dict(collections.Counter(e['effect_type'] for e in effects)),
            by_type_yg=dict(collections.Counter(e['effect_type'] for e in effects
                                                if desc_by_id[e['description_ref']]['yg'])),
            evidence_grade_profiles=dict(effect_grade_profile),
            evidence_grade_profiles_yg=dict(effect_grade_yg),
            answers=dict(total=sum(d['answer_ref_count'] for d in descriptions),
                         matched_to_effects=sum(len(e.get('answer_refs') or []) for e in effects),
                         unmatched_refs=sum(len(d['unmatched_answer_refs']) for d in descriptions)),
        ),
        backlog=dict(total=len(backlog),
                     by_kind=dict(collections.Counter(b['kind'] for b in backlog)),
                     by_priority=dict(collections.Counter(b['priority'] for b in backlog)),
                     yg_total=sum(1 for b in backlog if b['yg'])),
        checks=checks,
        all_checks_passed=not failed,
    )

    # ---- 写出 ------------------------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / 'ledger.jsonl').open('w', encoding='utf-8', newline='\n') as f:
        for dsc in descriptions:
            f.write(json.dumps(dsc, ensure_ascii=False) + '\n')
        for e in effects:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    (out_dir / 'backlog.json').write_text(json.dumps(backlog, ensure_ascii=False, indent=1),
                                          encoding='utf-8')
    (out_dir / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=1),
                                          encoding='utf-8')
    (out_dir / 'README.md').write_text(render_readme(metrics), encoding='utf-8')
    return metrics


def render_readme(metrics: dict) -> str:
    s = metrics['snapshot']
    rows = metrics['rows']
    d = metrics['descriptions']
    e = metrics['effects']
    b = metrics['backlog']
    return f"""# 角色技能效果账本（目标整改 P1）

生成器：`scripts/character_skills/effect_ledger.py`；生成时间 {s['generated_at']}。

## 输入快照锚点（从当前文件重算，非硬编码）

| 锚点 | 值 |
|---|---|
| 页面数据根 | `{s['pages_root']}`（与页面同快照；卡数 {rows['cards']}，描述 {rows['descriptions']} 行） |
| campaign 签名 | `{s['campaign_signature']}`（读自 `output/character_skills/pages/_batch/campaign_latest.json` 指向的 campaign_report.json） |
| rules.json | `{s['rules_json']}`，SHA-256 前 16 位 `{s['rules_json_sha256_16']}` |
| snapshot_id | `{s['snapshot_id']}`（campaign 前 8 位＋rules SHA 前 8 位；每条账本条目携带） |

## 输出与字段

- **ledger.jsonl**：`record_type=description` 每条描述一行（全量，唯一入口）＋
  `record_type=effect` 每条效果一行。描述条目：`input_snapshot`/`namespace`
  （layer/table/record_id/source_key，同号跨源不合并）/`cid`/`skill_category`/`skill`/
  `slot`（stage/reference_field/fragment_index/level）/`row_id`/`japanese`＋`japanese_nfkc`
  ＋`japanese_nfkc_sha256_16`（内容校验）/`effect_ids`/`refs`（条件/对象/上限共享引用）/
  `number_refs`（数字公共引用）/`ledger_row_status`/`split_flags`/`breakpoint`/
  `unmatched_answer_refs`。效果条目：`effect_id`（=`row_id#eNN` 主张／`#qNN` 定性 NA）/
  `description_ref`/`effect_type`/`direction`/`span`/`snippet`/`clause_index`/
  `status`（has_answer|unresolved|justified_na，互斥）/`evidence_grades`/`answer_refs`
  （row_id+field_path+raw_value+answer_index 可解析引用；多字段答案保留 conversion/
  conditions/base_definition/unit 完整映射）/未解决项的
  `unresolved{{gap,candidate_sources,blocker,next_step,priority}}`/NA 项的 `na_basis`。
- **backlog.json**：正式待办＝全部未解决效果（kind=effect）＋全部拆分待核查描述
  （kind=description_split_check）；每项含 gap/candidate_sources/blocker/next_step/priority。
- **metrics.json**：下述指标＋自检结果（checks，任一失败 all_checks_passed=false）。

## 指标定义与分母

| 指标 | 定义 | 分母 |
|---|---|---|
| 描述总数 | 当前 pages 全部 card.json 行 | 全部行（重算，不硬编码） |
| 拆分待核查描述 | S1 零效果识别／S2 数字语义未确认（角色绑定映射：角色↔quantity_kind/单位/换算口径/文本位置多重绑定，数值相等只是必要线索，R2 复审整改 20261023 第二轮）／S3 未覆盖子句／S3b 词表外机制词/谓词模板无结构化覆盖（否定注记不构成完成证据，R2 复审整改 20261023 第二轮）／S4 答案未对应主张／S5 HP 档位分支覆盖不完整或「随HP变化」句增益答案缺条件绑定（R1 整改）／S6 概率类条件无载体映射（R2 整改）／S7 同 HP 条件组其余 pattern→t13 异值、选取维度未解析（R1-High 复审整改 20261023） 的行 | 描述总数 |
| 完整描述 | ≥1 已识别效果，全部有答案或有依据不适用，无拆分待核查标志 | 描述总数 |
| 部分/未解析描述 | 部分效果有答案/部分未解决；或全部未解决（均无拆分待核查标志） | 描述总数 |
| 已识别效果数 | 当前词表从句面识别的效果主张＋定性 NA 条目 | **不是全库全部效果数**：拆分待核查行中未识别效果未计入，不得据此算总完成率 |
| 有答案/未解决/有依据不适用 | 三态互斥，和＝已识别效果数 | 已识别效果数 |
| 证据档 | 效果所引答案的 numeric/association 证据档组合（确认/类型外推/推断） | 有答案效果数；独立于完整度计数 |
| Y.G. | 卡 title 含「Y.G.」 | 每指标单列 `yg` |

## 优先级规则（backlog.priority）

- **P0 衔接断点**：行已有 2012 暴击答案（仅精确键 `skilllist|2012|/param4` 或 `/param5`）而句面攻/防/移/时长主张
  未解决（批 6 形状门×批 8/14 断点，GOAL_ALIGNMENT.md G01；349/6335 属此类）；
- **P1 Y.G.**：Y.G. 卡的其余未解决/待核查；
- **P2 其他**：非 Y.G.、非断点。

## 「有依据的不适用」规则

P1 仅对「…できない」禁止型子句（无数量词、无增减谓词、无属性主张词、非条件语境）出具
定性 NA 判定，每条带逐字子句依据（`na_basis`）。其余纯定性机制一律记未解决并写明缺口，
不用 NA 兜底；原文数字的角色标签（数量/次数等）是词面启发式（card_page_data.py:136-224），
数字语义未确认的行一律拆分待核查，不判完整。

## 复跑命令

```
./.venv/Scripts/python.exe -B scripts/character_skills/effect_ledger.py
# 可选：--pages-root <页面根> --output <输出目录>
#   默认 output/character_skills/pages → output/character_skills/effect_ledger
#   验证可复跑：--output 指向独立目录（如 work/character_skills_goal_rectification/ledger_replay）
```

依赖：只读页面 card.json、`output/character_skills/profiles/rules.json`、
campaign_report.json 与 `card_page_inference_b9_debuff.py`/`card_page_inference_b6_bossbuff.py`
的词表与边界规则；无手机/逆向输入。同输入重跑输出一致（`generated_at` 除外）。

## 诚实边界

- 已识别效果分母≠全库全部效果数；未完成语义拆分前不宣称总完成率。
- 描述完整度由账本派生，独立于 A/C 行类、legacy partial 标志与证据档；两者差异见
  `metrics.descriptions.legacy_partial_cross`（报告差异，不强行对齐）。
- **S3b 叙事过报已知范围（R2-S3B-PRECISION，20261023）**：弱点/吸収等监视词在叙事/说明句
  （「敵の特徴や弱点を伝える情報屋」「あらゆるものを吸収」类）也会命中——此类命中已附
  `confidence=low` 注记（叙事动词±12 字符窗口或泛化代名词宾语），保守登记不判解析、
  不据此宣称机制已解析；全部 S3b 命中行本就为非完整行，未造成完整行翻转。
- **叙述性数字（R2-NARRATIVE-S2，20261023）**：role_class=narrative（N秒先等叙述成分）
  不参与数值映射；其 S2 登记的 gap 文案为角色说明（非效果量/条件主张——不构成未确认数值），
  并注「如后续证据表明其承载效果语义应推翻并入待办」。
- **效果量消费位置（R2-S2-CONSUMPTION-319，20261023）**：优先同子句主张消费；「与えた
  ダメージのN%、HPが回復」型同句跨子句以 sentence 级位置绑定回退并逐项注明；
  泛化标签（效果量百分比/效果固定量）答案不入类型词表——数字经精确同标签结构化回退绑定
  （basis=exact_label_structured_answer），其所属主张的未解决状态另行登记，不据此判完整。
- 本账本不改 pages/、不改 card.json、不重建页面、不触碰 30236 基线行值、不改 rules.json。

（自动生成指标摘要：完整 {d['complete']['all']}／部分 {d['partial']['all']}／未解析
{d['unparsed']['all']}／拆分待核查 {d['split_check']['all']}；已识别效果
{e['identified_total']['all']}＝有答案 {e['by_status'].get('has_answer', {}).get('all', 0)}
＋未解决 {e['by_status'].get('unresolved', {}).get('all', 0)}＋有依据不适用
{e['by_status'].get('justified_na', {}).get('all', 0)}；backlog {b['total']} 项。）
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pages-root', type=Path, default=PAGES_DEFAULT)
    ap.add_argument('--output', type=Path, default=OUT_DEFAULT)
    args = ap.parse_args()
    metrics = run(args.pages_root, args.output)
    print(json.dumps(dict(
        snapshot=metrics['snapshot'], rows=metrics['rows'],
        descriptions=metrics['descriptions'], effects=metrics['effects'],
        backlog=metrics['backlog'],
        all_checks_passed=metrics['all_checks_passed'],
        checks=[dict(check=c['check'], passed=c['passed']) for c in metrics['checks']]),
        ensure_ascii=False, indent=1))
    if not metrics['all_checks_passed']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()






