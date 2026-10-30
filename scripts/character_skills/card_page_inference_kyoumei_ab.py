"""共鳴必殺本体（YG1）A/B 档推断模块——阶段一（筛选 + B 档规则化 + 答案构建 + scratch 探针）。

范围与边界（任务书 docs/tasks/20261025-character-skills-kyoumei-ab.md）：
* ① 对当前 YG1（page_group=special_move）backlog 效果项逐项重筛分档（A/B/C/HINT/P）；
  ② 定义并校验 B 档空壳键规则（只允许 7 键：55 p1、74 p5、51 p0、114 p1、64 p1、76 p1、103 p3）；
  ③ 提供 A 档既有键消费与 B 档公式级答案的构建函数（build_answers）。
* **不写** pages / effect_ledger / 选题链 / 正式四 cohort；不改 card_page_dependencies.py；不做新原生提取。
* 数值只来自既有 origin 记录与已确认规则；未证项保持未知，缺失/null/0 分开，不补乘项。
* 证据档沿用 cid 89/93/283 先例：answer_status=CONFIRMED_FORMULA_ONLY（公式级，不是最终 HP），
  evidence_scope=BY_TYPE_EXTRAPOLATED（类型级规则外推到该记录）。

分档定义
--------
A    : 效果主张的核心数值事实可由 rules.json 已确认键直接消费（或已在同行答案交付），且逐行门控通过。
B    : 至少一个核心事实只能经允许的 7 键（55 p1、74 p5、51 p0、114 p1、64 p1、76 p1、103 p3）中的空壳键
       升级后消费。
C    : 至少一个核心事实无键可用（handler 未定位 / 槽位语义未核 / 载体归属未证），或需允许清单外的空壳键。
HINT : 无数值载体可指认、非数值机制，或属触发链·Chain·超共鳴升级层（本批不补乘项，只披露适用条件）。
P    : C 批固定 289 池遗留 113 项——维持原处置，本模块只登记不重开。

类型语义的硬约束（不得反过来把槽当倍率用）
------------------------------------------
* ``bossskill|103|/skillparam3`` 是 **落点偏移 fall_offset**，不是伤害倍率；type103 的伤害在
  ``AirAreaStrike.update``（未追）。因此「大ダメージ」类主张仍为 C，不能借这枚键出数。
* ``bossskill|74|/skillparam5`` 是 **首次直接范围伤害**倍率，不解释其后反響/重复小伤害。
* ``bossskill|51|/skillparam0``、``|114|/skillparam1``、``|76|/skillparam1`` 是 ``atk_rate/技能基值``
  读数点（``fmul`` → ``0x14374bc`` 整数化）；``|64|/skillparam1`` 是 reactive heal 基值。
"""

from __future__ import annotations

import collections
import json
import math
import re
from pathlib import Path

MODULE_VERSION = "kyoumei_ab_20261025.phase1"

# ---------------------------------------------------------------------------
# 允许的 7 键（任务书 §1）与现状
# ---------------------------------------------------------------------------
ALLOWED_SHELL_KEYS = (
    "bossskill|55|/skillparam1",
    "bossskill|74|/skillparam5",
    "bossskill|51|/skillparam0",
    "bossskill|114|/skillparam1",
    "bossskill|64|/skillparam1",
    "bossskill|76|/skillparam1",
    "bossskill|103|/skillparam3",
)
# 已由 2026-10-24 批 1/批 2 升级为已确认的两键（本批不改值，仅复验）
ALREADY_CONFIRMED_KEYS = ("bossskill|55|/skillparam1", "bossskill|74|/skillparam5")
EVIDENCE_55_74 = {
    "bossskill|55|/skillparam1": {"report": "output/character_skills/boss_heal_types/native_checks.json",
                                  "checks": ["h55.pin_0x1194f00", "h55.pin_0x1194f08", "h55.pin_0x1195034",
                                             "h55.pin_0x119503c", "h55.pin_0x1195040"]},
    "bossskill|74|/skillparam5": {"report": "output/character_skills/boss_heal_types/native_checks.json",
                                  "checks": ["g74.damage_function_found", "g74.basic_skill_attack_times_slot_then_integerise",
                                             "g74.slot_resolved", "g74.slot_matches_the_hand_read_expectation",
                                             "g74.getBasicSkillAttack_argument_is_the_expected_variant", "g74.consumer_located"]},
}

# ---------------------------------------------------------------------------
# 类型 → (事实, 参数) 能力表（依据 rules.json 现状 + type_rules.json 槽位）
# ---------------------------------------------------------------------------
RATE = {0: "/skillparam1", 1: "/skillparam1", 2: "/skillparam1", 3: "/skillparam1", 22: "/skillparam1",
        55: "/skillparam1", 74: "/skillparam5", 105: "/skillparam1", 110: "/skillparam1", 112: "/skillparam1",
        51: "/skillparam0", 114: "/skillparam1", 76: "/skillparam1"}
COUNT = {110: "/skillparam6", 105: "/skillparam6", 1: "/skillparam3", 112: "/skillparam5", 55: "/skillparam0"}
INTERVAL = {110: "/skillparam5", 105: "/skillparam5", 1: "/skillparam2", 112: "/skillparam4"}
HEAL = {27: "/skillparam1", 64: "/skillparam1"}
HEAL_INTERVAL = {27: "/skillparam2"}
HEAL_COUNT = {27: "/skillparam3"}
DAMAGE_TYPES = frozenset({0, 1, 2, 3, 4, 5, 6, 7, 19, 22, 29, 33, 34, 43, 44, 47, 49, 51, 52, 55, 64, 67, 69,
                          72, 74, 76, 80, 82, 86, 103, 105, 110, 112, 114, 116, 117, 119})
HEAL_TYPES = frozenset({10, 11, 12, 14, 26, 27, 28, 31, 32, 46, 50, 64, 75, 76, 88, 108, 52})
# handler 未定位（可作候选载体，但不能消费其槽）
UNLOCATED_TYPES = frozenset({16, 52, 88, 100, 104, 108, 116, 117, 119})

CLAIM_RULES = (
    ("必殺技の威力", "SKILL_POWER_UPGRADE"),
    ("必殺技が使えるマナ", "MANA_GRANT"),
    ("マナが多いほど", "MANA_SCALED_PROB"),
    ("一定確率で必殺技", "PROB_SKILL_POWER"),
    ("ダメージを受けなくなる", "INVULN"),
    ("ダメージを受けず", "INVULN"),
    ("回ダメージを受けるまで", "HIT_LIMIT_DURATION"),
    ("経過すると効果が上がる", "STAGE_ADVANCE"),
    ("攻撃を50回当てた時", "HIT_COUNT_TRIGGER"),
    ("ランダムで1つが発生", "RANDOM_BRANCH"),
    ("攻撃速度", "ATTACK_SPEED"),
    ("凍結/ダウンも回復", "STATUS_CLEAR"),
    ("ドラゴン種", "RACE_DAMAGE"),
    ("固定ダメージ", "FIXED_DAMAGE"),
    ("HPが回復", "HP_HEAL"),
    ("一定間隔", "INTERVAL_OR_HEAL"),
    ("回復", "HEAL_INTERVAL"),
    ("攻撃力", "ATK_BUFF"),
    ("防御力", "DEF_BUFF"),
    ("回ダメージ", "MULTI_DAMAGE"),
    ("大ダメージ", "BIG_DAMAGE"),
    ("ダメージ", "DAMAGE"),
)
FACTS = {
    "DAMAGE": ["rate"], "BIG_DAMAGE": ["rate"], "MULTI_DAMAGE": ["rate", "count"],
    "INTERVAL_DAMAGE": ["rate", "interval"], "HEAL_INTERVAL": ["heal", "heal_interval", "heal_count"],
    "HP_HEAL": ["heal"], "ATK_BUFF": ["buff_attack", "buff_duration"],
    "DEF_BUFF": ["buff_defense", "buff_duration"],
}
HINT_REASONS = {
    "SKILL_POWER_UPGRADE": "必殺技威力/敵味方效果上昇属技能级强化（Chain·超共鳴升级层）；bossskill 无对应参数键，"
                           "触发链内部无证据——只披露适用条件，不补乘项",
    "PROB_SKILL_POWER": "概率型技能威力上昇：概率与载体均未定位",
    "MANA_GRANT": "效果结束时获得玛娜：非数值增益，无参数键",
    "MANA_SCALED_PROB": "概率随玛娜变化：机制语义未解析",
    "INVULN": "一定时间不受伤害：状态机制，无数值倍率可出（不以 0 或占位代替）",
    "HIT_LIMIT_DURATION": "「受 N 次伤害为止」属持续条件而非伤害倍率；条件语义未解析",
    "STAGE_ADVANCE": "经过一定时间效果上升：多阶段推进，阶段值与推进/装载未证（与 C 批 HOLD18 同源）",
    "HIT_COUNT_TRIGGER": "命中计数触发条件：阈值与效果载体未定位",
    "RANDOM_BRANCH": "随机 1/3 分支：分支表与概率未定位",
    "STATUS_CLEAR": "状态解除：非数值机制，无倍率可出",
    "RACE_DAMAGE": "种族限定伤害增减：无参数键，且与本体倍率不可相加",
    "FIXED_DAMAGE": "「固定ダメージ」是独立机制；55 的 p0/p1/p3 属激光段配置，不能据此推固定伤害值",
    "ATTACK_SPEED": "攻撃速度增益载体未定位（候选 SA2012 p7/p8、type119，均未证）",
    "TRIGGER_WORD_DAMAGE": "句中「ダメージを受ける」是受击触发词，不是造成伤害主张；效果项误桶，真实主张见同文回復/增益项",
}
COND_RE = re.compile(r"マナが\d+つ以上|一定確率|WAVE|発動した場合|HPが|戦闘不能|たびに")
TIER_ORDER = {"A": 0, "B": 1, "C": 2}


# ---------------------------------------------------------------------------
# B 档规则升级草案（5 个现存空壳键；55/74 已于 2026-10-24 升级，不再改）
# 证据：boss_heal_types/type_rules.json 槽位解析 + native_checks.json(219/219, native 562a6975…)
#      + 本批 output/character_skills/kyoumei_ab_20261025/scratch/pin_recheck.json 逐键字节复验
# ---------------------------------------------------------------------------
_PIN_REPORT = "output/character_skills/kyoumei_ab_20261025/scratch/pin_recheck.json"

# rules.json 每条规则的字段形状（与 scripts/character_skills/profiles.py::register_rule 一致）。
# 生成链把 rule["applicability"] 映射为 rules.json 的 "conditions"，故本模块的 RULE_UPGRADES
# 用 "conditions" 作为规范字段，由 apply_rule_upgrades 直接写 rules.json、由 rules.py 的
# _kyoumei_ab_shell_dictionary 写 applicability（同一文本）。
RULE_JSON_FIELDS = ("table", "effect_type", "field_path", "meaning_zh", "unit", "conversion",
                    "base_definition", "target", "conditions", "evidence", "status", "limits",
                    "occurrences", "origin")
_TYPE_RULES = "output/character_skills/boss_heal_types/type_rules.json"
_NATIVE_CHECKS = "output/character_skills/boss_heal_types/native_checks.json"
_BASE = "B=getBasicSkillAttack(true)，已包含 Chain，不再重复乘 Chain。"
_BASE_DEF = "B=getBasicSkillAttack(true)，已包含 Chain，不再重复乘 Chain。槽位 = ParamS_long +0x2c + 4×N（0x2c=p0、0x30=p1、0x38=p3）。"

RULE_UPGRADES = {
    "bossskill|51|/skillparam0": {
        "meaning_zh": "范围伤害输入倍率",
        "unit": "倍（相对B）",
        "conversion": "伤害输入 = floor/clamp(float32(B × skillparam0))",
        "base_definition": _BASE_DEF,
        "target": "该处理器选出的敌方目标；描述与载体需另行绑定",
        "conditions": "当前已核原生版本的 Boss 类型处理器；CACHE 记录逐源取值，charainfo 仅记录级等价时作为副本。"
                      "缺失/null/非有限值不得补 0 套公式。",
        "status": "已确认（原生静态局部公式；描述归属另作推断）",
        "limits": "非最终 HP 扣减；不证明命中次数、实际选档或完整技能。读取点 0x1191b2c 为 fmul，"
                  "0x1191b30 为整数化 0x14374bc；槽位实参 0x2c = skillparam0。",
        "evidence": [
            {"read_rva": "0x1191b24", "detail": "ldr      s1, [x21, #0x2c]", "handler": "bhSkillUtil.Exec_DAMAGE_AREA"},
            {"read_rva": "0x1191b2c", "detail": "fmul     s0, s0, s1", "handler": "bhSkillUtil.Exec_DAMAGE_AREA"},
            {"read_rva": "0x1191b30", "detail": "bl       #0x14374bc（整数化）", "handler": "bhSkillUtil.Exec_DAMAGE_AREA"},
            {"report": _TYPE_RULES, "scope": "type51 slots.atk_rate slot=0（0x2c）/ type_rules checks 全过"},
            {"report": _NATIVE_CHECKS, "scope": "g51.damage_function_found / g51.basic_skill_attack_times_slot_then_integerise / "
                                                 "g51.slot_resolved / g51.slot_matches_the_hand_read_expectation / "
                                                 "g51.getBasicSkillAttack_argument_is_the_expected_variant / g51.consumer_located 六项 True（219/219）"},
            {"report": "output/character_skills/boss_attack_types/native_checks.json",
             "scope": "Exec_ATTACK 家族 86/86（t0–t5 伤害点位；51 的 fmul+整数化同族）"},
            {"report": _PIN_REPORT, "scope": "本批逐键字节复验"},
        ],
        "origin": "scripts/character_skills/card_page_inference_kyoumei_ab.py::RULE_UPGRADES",
    },
    "bossskill|114|/skillparam1": {
        "meaning_zh": "冲刺重复攻击单次伤害输入倍率",
        "unit": "倍（相对B）",
        "conversion": "伤害输入 = floor/clamp(float32(B × skillparam1))",
        "base_definition": _BASE_DEF,
        "target": "该处理器选出的敌方目标；描述与载体需另行绑定",
        "conditions": "当前已核原生版本的 Boss 类型处理器；CACHE 记录逐源取值，charainfo 仅记录级等价时作为副本。"
                      "缺失/null/非有限值不得补 0 套公式。",
        "status": "已确认（原生静态局部公式；描述归属另作推断）",
        "limits": "非最终 HP 扣减；不证明重复次数、间隔、实际选档或完整技能。"
                  "读取点 0x1185574 为 fmul，0x1185578 为整数化 0x14374bc；槽位实参 0x30 = skillparam1。",
        "evidence": [
            {"read_rva": "0x118556c", "detail": "ldr      s1, [x19, #0x30]", "handler": "bhSkillUtil.Exec_ATTACK_DASH_REPEAT2"},
            {"read_rva": "0x1185574", "detail": "fmul     s0, s0, s1", "handler": "bhSkillUtil.Exec_ATTACK_DASH_REPEAT2"},
            {"read_rva": "0x1185578", "detail": "bl       #0x14374bc（整数化）", "handler": "bhSkillUtil.Exec_ATTACK_DASH_REPEAT2"},
            {"report": _TYPE_RULES, "scope": "type114 slots.atk_rate slot=1（0x30）"},
            {"report": _NATIVE_CHECKS, "scope": "g114.damage_function_found / g114.basic_skill_attack_times_slot_then_integerise / "
                                                 "g114.slot_resolved / g114.slot_matches_the_hand_read_expectation / "
                                                 "g114.getBasicSkillAttack_argument_is_the_expected_variant / g114.consumer_located 六项 True（219/219）"},
            {"report": _PIN_REPORT, "scope": "本批逐键字节复验"},
        ],
        "origin": "scripts/character_skills/card_page_inference_kyoumei_ab.py::RULE_UPGRADES",
    },
    "bossskill|64|/skillparam1": {
        "meaning_zh": "受击反应回复（reactive heal）基值系数",
        "unit": "系数（相对B）",
        "conversion": "reactive heal 输入 = floor/clamp(float32(B × skillparam1))；写入 CharaStatus.setReactiveHeal",
        "base_definition": _BASE_DEF,
        "target": "能力持有者/受击对象；描述与载体需另行绑定",
        "conditions": "当前已核原生版本的 Boss 类型处理器；仅 reactive heal 路径；缺失/null/非有限值不得补 0 套公式。",
        "status": "已确认（原生静态局部公式；reactive heal 基值；描述归属另作推断）",
        "limits": "非最终 HP 回复；不证明触发条件、次数、间隔或超上限比例。"
                  "读取点 0x1196988 为 fmul，0x119698c 为整数化 0x14374bc；槽位实参 0x30 = skillparam1。",
        "evidence": [
            {"read_rva": "0x119697c", "detail": "ldr      s1, [x19, #0x30]", "handler": "bhSkillUtil.Exec_REACTIVE_HEAL"},
            {"read_rva": "0x1196988", "detail": "fmul     s0, s0, s1", "handler": "bhSkillUtil.Exec_REACTIVE_HEAL"},
            {"read_rva": "0x119698c", "detail": "bl       #0x14374bc（整数化）", "handler": "bhSkillUtil.Exec_REACTIVE_HEAL"},
            {"read_rva": "0x1196aa4", "detail": "CharaStatus.setReactiveHeal", "handler": "bhSkillUtil.Exec_REACTIVE_HEAL"},
            {"report": _TYPE_RULES, "scope": "type64 slots.skill_base_value slot=1（0x30）"},
            {"report": _NATIVE_CHECKS, "scope": "g64.damage_function_found / g64.basic_skill_attack_times_slot_then_integerise / "
                                                 "g64.slot_resolved / g64.slot_matches_the_hand_read_expectation / "
                                                 "g64.getBasicSkillAttack_argument_is_the_expected_variant / g64.consumer_located 六项 True（219/219）"},
            {"report": _PIN_REPORT, "scope": "本批逐键字节复验"},
        ],
        "origin": "scripts/character_skills/card_page_inference_kyoumei_ab.py::RULE_UPGRADES",
    },
    "bossskill|76|/skillparam1": {
        "meaning_zh": "追加浮游炮（funnel）攻击基值系数",
        "unit": "系数（相对B）",
        "conversion": "funnel 攻击输入 = floor/clamp(float32(B × skillparam1))；写入 FunnelBullet.Initialize",
        "base_definition": _BASE_DEF,
        "target": "该处理器创建/选出的目标；描述与载体需另行绑定",
        "conditions": "当前已核原生版本的 Boss 类型处理器；缺失/null/非有限值不得补 0 套公式。",
        "status": "已确认（原生静态局部公式；funnel 攻击基值；描述归属另作推断）",
        "limits": "非最终 HP 扣减；不证明浮游炮数量、存续时间、命中次数或选档。"
                  "读取点 0x119cf6c 为 fmul，0x119cf70 为整数化 0x14374bc；槽位实参 0x30 = skillparam1。",
        "evidence": [
            {"read_rva": "0x119cf64", "detail": "ldr      s1, [x21, #0x30]", "handler": "bhSkillUtil.Exec_ADD_FUNNEL"},
            {"read_rva": "0x119cf6c", "detail": "fmul     s0, s0, s1", "handler": "bhSkillUtil.Exec_ADD_FUNNEL"},
            {"read_rva": "0x119cf70", "detail": "bl       #0x14374bc（整数化）", "handler": "bhSkillUtil.Exec_ADD_FUNNEL"},
            {"read_rva": "0x119d254", "detail": "FunnelBullet.Initialize", "handler": "bhSkillUtil.Exec_ADD_FUNNEL"},
            {"report": _TYPE_RULES, "scope": "type76 slots.skill_base_value slot=1（0x30）"},
            {"report": _NATIVE_CHECKS, "scope": "g76.damage_function_found / g76.basic_skill_attack_times_slot_then_integerise / "
                                                 "g76.slot_resolved / g76.slot_matches_the_hand_read_expectation / "
                                                 "g76.getBasicSkillAttack_argument_is_the_expected_variant / g76.consumer_located 六项 True（219/219）"},
            {"report": _PIN_REPORT, "scope": "本批逐键字节复验"},
        ],
        "origin": "scripts/character_skills/card_page_inference_kyoumei_ab.py::RULE_UPGRADES",
    },
    "bossskill|103|/skillparam3": {
        "meaning_zh": "落点偏移（fall offset）输入，非伤害倍率",
        "unit": "落点偏移量",
        "conversion": "float32(skillparam3) 作为 AirAreaStrike 落点偏移输入；不进入 0x14374bc 伤害整数化",
        "base_definition": "与 type33 共用落点/夹紧逻辑；本类型无 sp6 选择码分支",
        "target": "落点计算，不是伤害对象",
        "conditions": "当前已核原生版本；type103 的伤害在 AirAreaStrike.update 内结算，本键不参与。",
        "status": "已确认（原生静态槽位语义：落点偏移；非伤害倍率）",
        "limits": "**不得作为「大ダメージ」倍率消费**。读取点 0x118c628 之后的下一条 bl 是 0x1ec9a98，"
                  "不是整数化 0x14374bc；伤害槽位仍未定位。",
        "evidence": [
            {"read_rva": "0x118c628", "detail": "ldr      s0, [x20, #0x38]", "handler": "bhSkillUtil.Exec_FALL_AREA2"},
            {"report": _TYPE_RULES, "scope": "type103 slots.fall_offset slot=3（0x38）；unresolved=伤害在 AirAreaStrike.update 未追"},
            {"report": _NATIVE_CHECKS, "scope": "x103.slot3_fall_offset_pin True（219/219）"},
            {"report": _PIN_REPORT, "scope": "本批逐键字节复验（含 bl 目标核对）"},
        ],
        "origin": "scripts/character_skills/card_page_inference_kyoumei_ab.py::RULE_UPGRADES",
    },
}

# B 档答案规格：事实 → 公式文本模板（正式重建时由 card_page_data 生成 answer 记录）
B_ANSWER_FORMULA = {
    "rate": "floor/clamp(float32(B × {value}))",
    "heal": "floor/clamp(float32(B × {value}))（reactive heal 基值）",
}


def apply_rule_upgrades(rules: dict) -> tuple[dict, dict]:
    """把 RULE_UPGRADES 应用到一份 rules 映射的副本；返回 (新映射, 变更记录)。不改入参。"""
    out = json.loads(json.dumps(rules, ensure_ascii=False))
    log = {"changed": [], "missing": []}
    for key, patch in RULE_UPGRADES.items():
        if key not in out:
            log["missing"].append(key)
            continue
        before = dict(out[key])
        shaped = {k: v for k, v in patch.items() if k in RULE_JSON_FIELDS}
        out[key] = {**before, **json.loads(json.dumps(shaped, ensure_ascii=False))}
        log["changed"].append({"key": key, "before_status": before.get("status"), "after_status": patch["status"]})
    return out, log


# ---------------------------------------------------------------------------
# 逐项重筛
# ---------------------------------------------------------------------------
def _claim_class(clause: str, effect_type: str | None = None) -> str:
    # 词表外「ダメージ」效果若句中伤害词是「ダメージを受ける」（受击触发），不是造成伤害主张：
    # 该效果项属误桶，真实主张在同文的回復/增益项（例：30310 反応回復行）。
    if (effect_type or "").startswith("ダメージ") and "ダメージを受け" in clause and "ダメージを与" not in clause:
        return "TRIGGER_WORD_DAMAGE"
    for k, v in CLAIM_RULES:
        if k in clause:
            if v == "INTERVAL_OR_HEAL":
                return "HEAL_INTERVAL" if "回復" in clause else "INTERVAL_DAMAGE"
            return v
    return "UNKNOWN"


def _first_slot(slots, types):
    for e in slots:
        if e.get("type") in types:
            return e
    return None


def _key_state(rules: dict, key):
    if key is None:
        return "NO_KEY"
    if key in rules and rules[key].get("status"):
        return "CONFIRMED"
    if key in rules:
        return "SHELL_ALLOWED" if key in ALLOWED_SHELL_KEYS else "SHELL_OUTSIDE"
    return "NO_KEY"


def _already(row_answers, record_id, field_path):
    if field_path is None:
        return None
    for a in row_answers or []:
        if a.get("table") == "bossskill" and a.get("record_id") == record_id and a.get("field_path") == field_path:
            return a.get("rule_key")
    return None


def _fact_status(fact, slots, item, cc, rules):
    ans = item.get("answers") or []
    if fact == "rate":
        s = _first_slot(slots, DAMAGE_TYPES)
        if s is None:
            return "NO_CARRIER", None, None, None, "链内无伤害处理器槽"
        ty = s["type"]
        if ty == 74 and cc in ("INTERVAL_DAMAGE", "MULTI_DAMAGE"):
            return "NO_KEY", ty, s["skillid"], None, "type74 p5 仅首次直接范围伤害；重复/回響伤害比例来源未证"
        if ty == 103:
            return "NO_KEY", ty, s["skillid"], None, "type103 p3=fall_offset 非伤害倍率；伤害槽在 AirAreaStrike.update 未追"
        f = RATE.get(ty)
        k = f"bossskill|{ty}|{f}" if f else None
        st = _key_state(rules, k)
        if st == "CONFIRMED" and _already(ans, s["skillid"], f):
            st = "ALREADY"
        return st, ty, s["skillid"], k, f"伤害倍率载体 slot {s['slot']} type{ty}"
    if fact in ("count", "interval"):
        s = _first_slot(slots, DAMAGE_TYPES)
        if s is None:
            return "NO_CARRIER", None, None, None, "链内无伤害处理器槽"
        table = COUNT if fact == "count" else INTERVAL
        f = table.get(s["type"])
        k = f"bossskill|{s['type']}|{f}" if f else None
        st = _key_state(rules, k)
        if st == "CONFIRMED" and _already(ans, s["skillid"], f):
            st = "ALREADY"
        return st, s["type"], s["skillid"], k, f"{'次数' if fact == 'count' else '间隔'}载体 slot {s['slot']} type{s['type']}"
    if fact in ("heal", "heal_interval", "heal_count"):
        s = _first_slot(slots, HEAL_TYPES)
        if s is None:
            return "NO_CARRIER", None, None, None, "链内无回复类载体槽"
        table = {"heal": HEAL, "heal_interval": HEAL_INTERVAL, "heal_count": HEAL_COUNT}[fact]
        f = table.get(s["type"])
        k = f"bossskill|{s['type']}|{f}" if f else None
        st = _key_state(rules, k)
        if st == "CONFIRMED" and _already(ans, s["skillid"], f):
            st = "ALREADY"
        return st, s["type"], s["skillid"], k, f"回复事实载体 slot {s['slot']} type{s['type']}"
    if fact in ("buff_attack", "buff_defense", "buff_duration"):
        s = _first_slot(slots, {13})
        if s is None:
            return "NO_CARRIER", None, None, None, "链内无 type13 支援槽"
        f = {"buff_attack": "/skillparam1", "buff_defense": "/skillparam2", "buff_duration": "/skillparam3"}[fact]
        k = f"bossskill|13|{f}"
        st = _key_state(rules, k)
        if st == "CONFIRMED" and _already(ans, s["skillid"], f):
            st = "ALREADY"
        return st, 13, s["skillid"], k, f"增益事实载体 slot {s['slot']} type13"
    return "NO_KEY", None, None, None, "未知事实"


def classify_items(ctx_items: list[dict], rules: dict, c_remnant: dict | None = None) -> list[dict]:
    """对 YG1 上下文项逐项分档；返回 candidates_rescreen 记录列表（不含 C 批遗留时 c_batch=None）。"""
    c_remnant = c_remnant or {}
    row_chain = {i["row_id"]: (i.get("pattern_chain") or {}).get("skillids") or []
                 for i in ctx_items if i["page_table"] == "bosspattern"}
    text_index = collections.defaultdict(set)
    for i in ctx_items:
        text_index[(i["cid"], (i.get("japanese") or "").strip())].add(i["row_id"])

    out = []
    for it in ctx_items:
        if it["kind"] != "effect":
            continue
        clause = it.get("clause") or it.get("sentence") or ""
        cc = _claim_class(clause, it.get("effect_type"))
        slots = (it.get("pattern_chain") or {}).get("skillids") or []
        if it["page_table"] == "charainfo":
            checks = it.get("mirror_checks") or []
            eq = [c for c in checks if c["verdict"] == "PARAM_EQUAL"]
            src = (eq or checks)[0]["mirror_row"] if checks else None
            slots = row_chain.get(src, [])
        same_rows = sorted(text_index[(it["cid"], (it.get("japanese") or "").strip())])
        gate = {
            "mirror_gate": None,
            "record_level": "BOSSPATTERN_CACHE" if it["page_table"] == "bosspattern" else None,
            "same_text_rows": same_rows,
            "multi_carrier": len(same_rows) > 1,
            "condition_in_sentence": bool(COND_RE.search(it.get("japanese") or "")),
        }
        if it["page_table"] == "charainfo":
            if it.get("mirror_of"):
                gate["mirror_gate"] = "PASS_MIRROR_EXISTS"
                gate["record_level"] = "CHARAINFO_MIRROR_OF:" + it["mirror_of"][0]
                gate["charainfo_value_diffs"] = [
                    {"mirror_row": c["mirror_row"], "verdict": c["verdict"]}
                    for c in (it.get("mirror_checks") or []) if c["verdict"] != "PARAM_EQUAL"
                ]
            else:
                gate["mirror_gate"] = "FAIL_NO_MIRROR"
                gate["record_level"] = "CHARAINFO_ONLY"
        base = {
            "effect_id": it["backlog_id"], "row_id": it["row_id"], "cid": it["cid"],
            "page_group": it["page_group"], "page_table": it["page_table"],
            "effect_type": it["effect_type"], "clause": it["clause"], "japanese": it["japanese"],
            "context_basis": it["context_basis"],
            "chain_signature": [(e.get("slot"), e.get("type")) for e in slots],
            "sa_abilities": sorted({a for e in slots for a in (e.get("s_ability_types") or []) if a is not None}),
            "slots_unlocated": sorted({e.get("type") for e in slots if e.get("type") in UNLOCATED_TYPES}),
            "damage_handler_count": sum(1 for e in slots if e.get("type") in DAMAGE_TYPES),
            "claim_class": cc, "claim_facts": FACTS.get(cc), "fact_details": [], "gating": gate,
            "c_batch": c_remnant.get(it["backlog_id"]),
        }
        if FACTS.get(cc) is None:
            reason = HINT_REASONS.get(cc, "无数值载体可指认")
            tier = "HINT"
            if cc in ("SKILL_POWER_UPGRADE", "ATTACK_SPEED") and base["slots_unlocated"]:
                tier = "C"
                reason += f"；链内存在未定位候选载体 type{base['slots_unlocated']}，需新原生定位后才能判归属"
            out.append({**base, "tier": "P" if base["c_batch"] else tier, "independent_tier": tier, "reason": reason,
                        "disposition": "C_REMNANT_PRESERVED" if base["c_batch"] else
                        ("C_KEEP_UNKNOWN_REGISTERED" if tier == "C" else "HINT_KEEP_UNKNOWN"),
                        "deliverable": None})
            continue
        facts = list(FACTS[cc])
        if cc == "HEAL_INTERVAL" and "受けるたび" in clause:
            facts = ["heal"]
        worst, no_carrier = None, False
        for f in facts:
            if (f == "rate" and cc == "MULTI_DAMAGE" and 52 in [e.get("type") for e in slots]
                    and 114 in [e.get("type") for e in slots]):
                s114 = _first_slot(slots, {114})
                fpath = RATE[114]
                key114 = f"bossskill|114|{fpath}"
                st114 = _key_state(rules, key114)
                base["fact_details"].append({"fact": f, "status": "SHELL_ALLOWED", "carrier_type": 114,
                                             "carrier_record": s114["skillid"], "rule_key": key114,
                                             "note": "52+114 链：倍率候选 114 p1（ATTACK_DASH_REPEAT2）；slot0 52 handler 未定位"})
                if worst is None or TIER_ORDER["B"] > TIER_ORDER[worst]:
                    worst = "B"
                continue
            st, ty, rid, key, note = _fact_status(f, slots, it, cc, rules)
            base["fact_details"].append({"fact": f, "status": st, "carrier_type": ty, "carrier_record": rid,
                                         "rule_key": key, "note": note})
            if st == "NO_CARRIER":
                no_carrier = True
                continue
            if st == "ALREADY":
                continue
            # 本批规则化键（RULE_UPGRADES）即使已确认，仍按 B 档（公式级/BY_TYPE_EXTRAPOLATED）交付，
            # 以保持重筛结果在 rules 写入前后稳定，并与答案证据档一致。
            if st == "CONFIRMED" and key in RULE_UPGRADES:
                t = "B"
            else:
                t = "A" if st == "CONFIRMED" else ("B" if st == "SHELL_ALLOWED" else "C")
            if worst is None or TIER_ORDER[t] > TIER_ORDER[worst]:
                worst = t
        if worst is None and no_carrier:
            out.append({**base, "tier": "P" if base["c_batch"] else "HINT", "independent_tier": "HINT",
                        "reason": "所需事实在链内找不到载体槽",
                        "disposition": "C_REMNANT_PRESERVED" if base["c_batch"] else "HINT_KEEP_UNKNOWN",
                        "deliverable": None})
            continue
        if worst is None:
            out.append({**base, "tier": "P" if base["c_batch"] else "ALREADY_COVERED", "independent_tier": "ALREADY_COVERED",
                        "reason": "核心事实已在同行答案交付；效果项仍在账本（主张/绑定未登记），不重复出答案",
                        "disposition": "C_REMNANT_PRESERVED" if base["c_batch"] else "KEEP_LEDGER_NO_DUP_ANSWER",
                        "deliverable": None})
            continue
        tier, extra = worst, []
        if gate["mirror_gate"] == "FAIL_NO_MIRROR" and tier in ("A", "B"):
            tier = "HINT"
            extra.append("charainfo 无同文 bosspattern 对照，不得消费其内联值")
        if gate["condition_in_sentence"] and tier in ("A", "B") and "マナが" in (it.get("japanese") or ""):
            tier = "HINT"
            extra.append("句内含玛娜阈值条件，条件→载体的绑定未证")
        if cc == "DEF_BUFF" and "回まで" in clause and tier in ("A", "B"):
            tier = "HINT"
            extra.append("「15回まで」重复施加次数载体未证（108/76 与 t13 并存）")
        if cc == "ATK_BUFF" and "徐々に" in clause and tier in ("A", "B"):
            tier = "C" if base["slots_unlocated"] else "HINT"
            extra.append("「徐々に」渐增调度未证（C 批 6 项渐增同处置）；t13 p1/p3 仅平铺增益输入")
        if cc == "INTERVAL_DAMAGE" and base["damage_handler_count"] >= 2 and tier in ("A", "B"):
            tier = "C"
            extra.append("链内 ≥2 个伤害处理器槽，『小ダメージ一定间隔』载体归属未证（需逐槽窗口）")
        if cc == "MULTI_DAMAGE" and 52 in [e.get("type") for e in slots] and 114 in [e.get("type") for e in slots]:
            tier = "B"
            extra.append("倍率候选 114 p1（ATTACK_DASH_REPEAT2，与「ダッシュ範囲」对应）；slot0 52 handler 未定位，"
                         "文字 N 回不另行验证")
        deliverable = []
        for d in base["fact_details"]:
            if d["status"] not in ("CONFIRMED", "SHELL_ALLOWED") or not d["rule_key"]:
                continue
            pname = d["rule_key"].split("|")[2].lstrip("/")
            slot = next((e for e in slots if e.get("skillid") == d["carrier_record"]), None)
            raw = (slot or {}).get("params", {}).get(pname)
            deliverable.append({**d, "param": pname, "raw_value": raw,
                                "formula_template": B_ANSWER_FORMULA.get(d["fact"], "floor/clamp(float32(B × {value}))")})
        disposition = {"A": "A_CONSUME_EXISTING_KEY", "B": "B_SHELL_UPGRADE_THEN_CONSUME",
                       "C": "C_KEEP_UNKNOWN_REGISTERED", "HINT": "HINT_KEEP_UNKNOWN"}[tier]
        if base["c_batch"]:
            disposition = "C_REMNANT_PRESERVED"
        final_tier = "P" if base["c_batch"] else tier
        not_consumed = None
        if final_tier in ("C", "HINT", "P") and deliverable:
            not_consumed = deliverable
            deliverable = []
        out.append({**base, "tier": final_tier, "independent_tier": tier,
                    "reason": "核心事实最大档位＝" + worst + ("；" + "；".join(extra) if extra else ""),
                    "disposition": disposition, "deliverable": deliverable,
                    "candidate_keys_not_consumed": not_consumed})
    return out


def summary(records: list[dict]) -> dict:
    non_p = [r for r in records if r["tier"] != "P"]
    return {
        "module_version": MODULE_VERSION,
        "total_effect_items": len(records),
        "tier_counts_final": dict(collections.Counter(r["tier"] for r in records)),
        "independent_tier_counts": dict(collections.Counter(r["independent_tier"] for r in records)),
        "non_p_tier_counts": dict(collections.Counter(r["tier"] for r in non_p)),
        "disposition_counts": dict(collections.Counter(r["disposition"] for r in records)),
        "c_remnant_found": sum(1 for r in records if r["c_batch"]),
        "mirror_gate": dict(collections.Counter(r["gating"]["mirror_gate"] for r in records)),
        "multi_carrier": sum(1 for r in records if r["gating"]["multi_carrier"]),
        "condition_in_sentence": sum(1 for r in records if r["gating"]["condition_in_sentence"]),
    }


def b_answer_specs(records: list[dict]) -> list[dict]:
    """B 档待交付答案规格（正式重建时由 card_page_data 消费；本阶段只出规格）。"""
    specs = []
    for r in records:
        if r["tier"] != "B":
            continue
        for d in r.get("deliverable") or []:
            specs.append({
                "effect_id": r["effect_id"], "row_id": r["row_id"], "cid": r["cid"],
                "clause": r["clause"], "fact": d["fact"], "rule_key": d["rule_key"],
                "carrier_type": d["carrier_type"], "record_id": d["carrier_record"],
                "field_path": d["rule_key"].split("|")[2],
                "formula_template": B_ANSWER_FORMULA.get(d["fact"], "floor/clamp(float32(B × {value}))"),
                "note": d["note"],
            })
    return specs


# ---------------------------------------------------------------------------
# 逐行门控：charainfo 记录级等价门（复用批 1 的 equivalence.py；fail-closed）
# ---------------------------------------------------------------------------
_EQUIV_CACHE: dict[tuple[int, str], tuple[bool, str]] = {}


def equivalence_gate(cid: int, field_path: str) -> tuple[bool, str]:
    """charainfo 副本能否承载该字段的 boss 规则。

    批 1 先例（``scripts/character_skills/equivalence.py``）：charainfo 是伤害侧**未执行副本**，
    只有记录级等价成立时才能沿用 boss 侧槽位语义；不成立时不得消费其内联值。
    模块不可用、cid 不在名册或字段超出等价范围一律 fail-closed。
    """
    key = (int(cid), field_path)
    if key in _EQUIV_CACHE:
        return _EQUIV_CACHE[key]
    try:
        import sys as _sys
        root = Path(__file__).resolve().parents[2]
        for p in (root / "scripts" / "character_skills", root / "scripts"):
            if str(p) not in _sys.path:
                _sys.path.insert(0, str(p))
        import equivalence  # noqa: PLC0415
        res = equivalence.field_allowed(int(cid), field_path)
    except Exception as exc:  # fail-closed：不用猜测替代
        res = (False, f"EQUIVALENCE_UNAVAILABLE:{type(exc).__name__}")
    _EQUIV_CACHE[key] = res
    return res


# ---------------------------------------------------------------------------
# 答案披露（公式级；不含最终扣血/乘项）
# ---------------------------------------------------------------------------
DISCLOSURES = {
    "rate_base": "B=bhSkillUtil.getBasicSkillAttack(true)，已包含 Chain，不再重复乘 Chain；float32 乘积后 floor/clamp 到 int32。",
    "trigger": "共鳴成立条件、超共鳴升级与 sympathy 系数无原生证据；答案仅在该 pattern 被选中时适用，不补乘项、不推测选档。",
    "55": "type55 只给激光伤害输入倍率；间隔/范围槽未证（p0=段启用上限、p6=段生成调度阈值，非秒）。",
    "74": "type74 p5=首次直接范围伤害倍率；p2 位图、p4/p6 与反響反射比例未证，本答案不解释其后反響伤害。",
    "13": "type13 数值乘 skillChainRate 后进入支持对象（boss_chain/type13_basis）：p1=1+该值的局部攻击因子，"
          "p2 经接受者当前 _normalAtk 整数化为固定防御，p3=supportTime 输入（真实秒未证），均非最终面板/最终扣血。",
    "27": "type27 回复量=floor/clamp(float32(B×p1))；p2 间隔与 update delta 同单位但真实秒未证；p3 次数向零截断。",
    "64": "type64 为 reactive heal 基值；触发条件（受击）、次数与超上限比例未证。",
    "103": "type103 p3 是落点偏移 fall_offset，不是伤害倍率；伤害在 AirAreaStrike.update 未追，不得借本键出伤害数。",
}


def _disclosures(slots) -> list[str]:
    out = [DISCLOSURES["rate_base"], DISCLOSURES["trigger"]]
    types = {e.get("type") for e in slots}
    for t in (13, 27, 55, 64, 74, 103):
        if t in types:
            out.append(DISCLOSURES[str(t)])
    return out


# ---------------------------------------------------------------------------
# A/B 答案构建（公式级；不写页面，由正式重建的 card_page_data 消费）
# ---------------------------------------------------------------------------
ANSWER_FORMULA = {
    "rate": "floor/clamp(float32(B × {v}))",
    "count": "int32(trunc(float32({v})))",
    "interval": "float32({v})（重复攻击间隔输入；真实秒未证）",
    "heal": "floor/clamp(float32(B × {v}))（reactive heal 基值）",
    "buff_attack": "局部攻击因子 = 1 + {v}×skillChainRate（Chain 档由施放时决定）",
    "buff_defense": "固定防御 = trunc(float32(接受者当前normalAtk × float32({v}×skillChainRate)))",
    "buff_duration": "supportTime 输入 = {v}（真实秒未证）",
}
ANSWER_QUANTITY = {
    "rate": ("伤害输入倍率", "倍率（相对B）"),
    "count": ("次数上限", "次"),
    "interval": ("重复攻击间隔输入", "游戏秒（未证）"),
    "heal": ("回复量输入（reactive heal 基值）", "系数（相对B）"),
    "buff_attack": ("局部攻击增益输入", "相对1的加算"),
    "buff_defense": ("固定防御系数（名义原始ATK）", "系数"),
    "buff_duration": ("增益持续时间输入", "游戏秒（未证）"),
}


def _blocked(reason: str, **kw) -> dict:
    return {"reason": reason, **kw}


def row_gates(item: dict, claim_class: str, slots: list[dict]) -> list[str]:
    """与重筛分档共用的一组「行内门控」原因码（builder 与 classify 必须同口径）。"""
    clause = item.get("clause") or ""
    jp = item.get("japanese") or ""
    out = []
    if claim_class == "TRIGGER_WORD_DAMAGE":
        out.append("COMPETING_SENTENCE_TRIGGER_WORD")
    if "マナが" in jp and COND_RE.search(jp):
        out.append("CONDITION_UNBOUND")
    if claim_class == "DEF_BUFF" and "回まで" in clause:
        out.append("COUNT_UNPROVEN")
    if claim_class == "ATK_BUFF" and "徐々に" in clause:
        out.append("RAMP_UNPROVEN")
    if claim_class == "INTERVAL_DAMAGE" and sum(1 for e in slots if e.get("type") in DAMAGE_TYPES) >= 2:
        out.append("MULTI_CARRIER_ATTRIBUTION_UNPROVEN")
    return out


def build_answers(item: dict, patterns: list[dict], rules: dict) -> dict:
    """为一行的效果项构建 A/B 答案（逐 pattern 枚举）。

    ``item``：rescreen 记录或同结构 dict（需 effect_type/clause/japanese/cid/row_id/page_table/
              answers/charainfo_params）。
    ``patterns``：``[{"pattern_id":..., "reference_field":..., "conditions_raw": {...},
                     "slots": [{slot, skillid, type, params, s_ability_types}]}]``。
    返回 ``{"answers": [...], "blocked": [...], "gating": {...}}``；不修改任何文件。
    """
    clause = item.get("clause") or item.get("sentence") or ""
    cc = _claim_class(clause, item.get("effect_type"))
    result = {"answers": [], "blocked": [], "gating": {}}
    if item.get("c_batch"):
        result["blocked"].append(_blocked("C_BATCH_REMNANT_PRESERVED"))
        return result
    if cc == "TRIGGER_WORD_DAMAGE":
        result["blocked"].append(_blocked("COMPETING_SENTENCE_TRIGGER_WORD"))
        return result
    if "マナが" in (item.get("japanese") or "") and COND_RE.search(item.get("japanese") or ""):
        result["blocked"].append(_blocked("CONDITION_UNBOUND"))
        return result
    if FACTS.get(cc) is None:
        result["blocked"].append(_blocked("NON_NUMERIC_OR_OTHER_LAYER", claim_class=cc))
        return result
    facts = list(FACTS[cc])
    if cc == "HEAL_INTERVAL" and "受けるたび" in clause:
        facts = ["heal"]
    if not patterns:
        result["blocked"].append(_blocked("NO_CARRIER_PATTERN"))
        return result
    charainfo = item.get("page_table") == "charainfo"
    ca_params = item.get("charainfo_params") or {}
    for pat in patterns:
        slots = pat.get("slots") or []
        result["gating"].setdefault("patterns", []).append({
            "pattern_id": pat.get("pattern_id"),
            "reference_field": pat.get("reference_field"),
            "chain": [(e.get("slot"), e.get("type")) for e in slots],
        })
        # multi-carrier：同一 pattern 内 ≥2 个伤害处理器槽时，「一定间隔小伤害」归属未证
        gates = row_gates(item, cc, slots)
        if gates:
            result["blocked"].append(_blocked("ROW_GATE", pattern_id=pat.get("pattern_id"), gates=gates))
            continue
        dmg_slots = [e for e in slots if e.get("type") in DAMAGE_TYPES]
        if cc == "INTERVAL_DAMAGE" and len(dmg_slots) >= 2:
            result["blocked"].append(_blocked("MULTI_CARRIER_ATTRIBUTION_UNPROVEN",
                                              pattern_id=pat.get("pattern_id"),
                                              damage_slots=[(e.get("slot"), e.get("type")) for e in dmg_slots]))
            continue
        for fact in facts:
            if (fact == "rate" and cc == "MULTI_DAMAGE" and 52 in [e.get("type") for e in slots]
                    and 114 in [e.get("type") for e in slots]):
                s114 = _first_slot(slots, {114})
                fpath = RATE[114]
                key = f"bossskill|114|{fpath}"
                carrier = s114
                note_extra = "52+114 链：倍率候选 114 p1（ATTACK_DASH_REPEAT2）；slot0 52 handler 未定位"
            else:
                _, ty, rid, key, note = _fact_status(fact, slots, item, cc, rules)
                carrier = next((e for e in slots if e.get("skillid") == rid), None)
                note_extra = note
            if carrier is None:
                result["blocked"].append(_blocked("NO_CARRIER", fact=fact, pattern_id=pat.get("pattern_id")))
                continue
            if key is None:
                result["blocked"].append(_blocked("NO_RULE_KEY", fact=fact,
                                                  carrier_type=carrier.get("type"),
                                                  record_id=carrier.get("skillid")))
                continue
            st = _key_state(rules, key)
            if st == "SHELL_OUTSIDE":
                result["blocked"].append(_blocked("SHELL_KEY_OUTSIDE_ALLOWED", fact=fact, rule_key=key))
                continue
            if st == "NO_KEY":
                result["blocked"].append(_blocked("NO_RULE_KEY", fact=fact, carrier_type=carrier.get("type")))
                continue
            fpath = key.split("|")[2]
            pname = fpath.lstrip("/")
            raw = (carrier.get("params") or {}).get(pname)
            if raw is None:
                result["blocked"].append(_blocked("VALUE_MISSING", fact=fact, rule_key=key,
                                                  record_id=carrier.get("skillid")))
                continue
            if isinstance(raw, float) and not math.isfinite(raw):
                result["blocked"].append(_blocked("VALUE_NOT_FINITE", fact=fact, rule_key=key))
                continue
            if charainfo:
                ok, why = equivalence_gate(item.get("cid"), fpath)
                if not ok:
                    result["blocked"].append(_blocked("CHARAINFO_EQUIVALENCE_GATE_UNMET", fact=fact,
                                                      rule_key=key, detail=why))
                    continue
                if ca_params.get(pname) is not None and ca_params.get(pname) != raw:
                    result["blocked"].append(_blocked("CHARAINFO_COPY_DIFFERS_FROM_PATTERN", fact=fact,
                                                      rule_key=key, charainfo_value=ca_params.get(pname),
                                                      pattern_value=raw))
                    continue
            if _already(item.get("answers"), carrier.get("skillid"), fpath):
                result["blocked"].append(_blocked("ALREADY_ANSWERED", fact=fact, rule_key=key))
                continue
            qty, unit = ANSWER_QUANTITY[fact]
            is_b = st == "SHELL_ALLOWED" or key in RULE_UPGRADES
            result["answers"].append({
                "fact": fact,
                "claim_class": cc,
                "value_text": ANSWER_FORMULA[fact].format(v=raw),
                "quantity_kind": qty,
                "unit": unit,
                "raw_value": raw,
                "quantitative": True,
                "numeric_source": "已有原生静态局部公式＋源记录",
                "numeric_evidence": "确认",
                "association_evidence": "推断",
                "answer_status": "CONFIRMED_FORMULA_ONLY",
                "evidence_scope": "BY_TYPE_EXTRAPOLATED",
                "tier": "B" if is_b else "A",
                "rule_key": key,
                "table": "bossskill",
                "field_path": fpath,
                "record_id": carrier.get("skillid"),
                "pattern_id": pat.get("pattern_id"),
                "reference_field": pat.get("reference_field"),
                "condition_label": f"{pat.get('reference_field')} / pattern {pat.get('pattern_id')} 被选中时",
                "binding": {
                    "pattern_id": pat.get("pattern_id"),
                    "slot": carrier.get("slot"),
                    "conditions_raw": pat.get("conditions_raw"),
                },
                "note": note_extra + ("；本批 B 档规则化键（证据见批次 build_report.md）" if is_b else "")
                        + "；" + " ".join(_disclosures(slots)),
                "disclosures": _disclosures(slots),
            })
    # 去重（同一 pattern 同一键只出一条）
    seen, uniq = set(), []
    for a in result["answers"]:
        k = (a["pattern_id"], a["rule_key"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(a)
    result["answers"] = uniq
    return result


# ---------------------------------------------------------------------------
# 正式页消费入口（阶段二）：把 B 档 8 条公式级答案加进页面行
# ---------------------------------------------------------------------------
KYOUMEI_SCOPE = "KYOUMEI_AB_FORMULA_ONLY"
ADMITTED_CIDS = frozenset({30252, 30255, 30306, 30310})
# 行级准入边界：这 8 行是当前账本中带未解 B 档主张的行（来自 candidates_rescreen.jsonl）。
# 这是准入范围（与 CID 集合同性质），不是数值表：数值仍逐件取自 CACHE 记录。
ADMITTED_ROWS = frozenset({
    "30310-special_move-special_move-pattern0-lvorder0-f0",
    "30310-special_move-special_move-pattern1-lvorder1-f0",
    "30310-special_move-special_move-skilltext-lvorder2-f0",
    "30252-special_move-special_move-pattern0-lvorder0-f0",
    "30252-special_move-special_move-pattern2-lvorder2-f0",
    "30255-special_move-special_move-pattern0-lvorder0-f0",
    "30306-special_move-special_move-pattern0-lvorder0-f0",
    "30306-special_move-special_move-pattern1-lvorder1-f0",
})
REACTIVE_HEAL_RE = re.compile(
    r"^(?:【[^】]*】)?味方全体にダメージを受けるたびに上限を超えて小回復し")
DASH_RE = re.compile(
    r"^(?:【[^】]*】)?ダッシュ範囲上にいる全ての敵に(\d+)回ダメージを与え")


def _ky_graph(data, cid):
    """按既有模块口径取该卡 chara + 各 pattern 的有序子记录；任一源不符即整体拒绝。"""
    import card_page_inference_attack_interval as A
    import card_page_inference_attack_interval2 as B
    import card_page_inference_yg1_multihit as M
    graph = B._patterns(data, cid)
    if graph is None:
        return None
    chara, patterns = graph
    out = {}
    for ref, (entry, item) in patterns.items():
        edges, issues = M.ordered(data, entry)
        if issues:
            return None
        for edge in edges:
            child = A.node(data, "bossskill", edge["child_id"])
            if child is None or child["raw"] != edge["record"]:
                return None
            edge["item"] = child
        out[ref] = dict(entry=entry, item=item, edges=edges)
    return chara, out


def _ky_answer(data, row, parent, edge, raw, rule_key, field, kind, unit, value, note, target,
               conditions, scope_slot):
    source = data.precise_source(edge["item"])
    ident = edge["child_id"]
    pattern_id = parent["entry"]["reference_id"]
    ref_field = parent["entry"]["reference_field"]
    return {
        "value": value,
        "quantity_kind": kind,
        "unit": unit,
        "raw_value": raw,
        "quantitative": True,
        "numeric_source": "已有原生静态局部公式＋源记录",
        "numeric_evidence": "确认",
        "association_evidence": "推断",
        "answer_status": "CONFIRMED_FORMULA_ONLY",
        "evidence_scope": "BY_TYPE_EXTRAPOLATED",
        "rule_key": rule_key,
        "field_path": field,
        "table": "bossskill",
        "record_id": ident,
        "layer": "CACHE",
        "source": {**source, "table": "bossskill", "record_id": ident, "field_path": field},
        "context": row.get("japanese"),
        "condition_label": f"{ref_field} / pattern {pattern_id} 被选中时",
        "conditions": conditions,
        "target": target,
        "note": note,
        "evidence": [
            "output/character_skills/boss_heal_types/type_rules.json",
            "output/character_skills/boss_heal_types/native_checks.json",
            "output/character_skills/boss_attack_types/native_checks.json",
            "output/character_skills/kyoumei_ab_20261025/scratch/pin_recheck.json",
        ],
        "kyoumei_ab_binding": {
            "scope": KYOUMEI_SCOPE,
            "pattern_id": pattern_id,
            "slot": scope_slot,
            "child_id": ident,
            "rule_key": rule_key,
        },
    }


def _ky_append(row, answer, report, kind):
    def key(a):
        b = a.get("kyoumei_ab_binding") or {}
        return (a.get("rule_key"), a.get("record_id"), a.get("field_path"), b.get("pattern_id"))
    if any(key(a) == key(answer) for a in row.get("answers") or []):
        return False
    row.setdefault("answers", []).append(answer)
    row["row_class"] = "A"
    row["evidence"] = "推断"
    row["evidence_label"] = "推断（共鳴必殺A/B公式级来源绑定）"
    row["partial"] = True
    row["evidence_scope"] = list(dict.fromkeys(list(row.get("evidence_scope") or []) + ["BY_TYPE_EXTRAPOLATED"]))
    marker = row.setdefault("inference_kyoumei_ab", {"scope": KYOUMEI_SCOPE, "pattern_ids": []})
    pid = answer["kyoumei_ab_binding"]["pattern_id"]
    if pid not in marker["pattern_ids"]:
        marker["pattern_ids"].append(pid)
    report["answers_added"] += 1
    report["additions"].append({"row_id": row["row_id"], "kind": kind,
                                "rule_key": answer["rule_key"], "record_id": answer["record_id"],
                                "pattern_id": pid})
    return True


def apply_to_groups(data, cid, groups):
    """正式页消费：为 4 张卡的 B 档 8 条答案加行内答案（不覆盖/不删除既有答案）。"""
    import equivalence as EQ
    report = {"scope": KYOUMEI_SCOPE, "cid": cid, "answers_added": 0, "additions": [], "rejections": []}
    if cid not in ADMITTED_CIDS:
        return report
    if "Y.G." not in str((data.profiles.get(cid) or {}).get("title") or ""):
        report["rejections"].append({"reason": "NOT_YG_CARD"})
        return report
    graph = _ky_graph(data, cid)
    if graph is None:
        report["rejections"].append({"reason": "CURRENT_GRAPH_SOURCE_MISMATCH"})
        return report
    chara, patterns = graph
    sinfo = {ref: str(p["entry"]["record"].get("sinfo") or "") for ref, p in patterns.items()}
    for group in groups:
        if group.get("group") != "special_move":
            continue
        for skill in group.get("skills", []):
            table = skill.get("table")
            for row in skill.get("rows", []):
                if row.get("row_id") not in ADMITTED_ROWS:
                    continue
                text = str(row.get("japanese") or "").strip()
                # 找该行对应的 pattern：bosspattern 用 reference_field；charainfo 用同文前缀镜像
                if table == "bosspattern":
                    parent = patterns.get(skill.get("reference_field"))
                elif table == "charainfo":
                    probe = text.rstrip("。")
                    hits = [ref for ref, s in sinfo.items() if s.startswith(probe)]
                    parent = patterns.get(hits[0]) if len(hits) == 1 else None
                else:
                    continue
                if parent is None:
                    report["rejections"].append({"row_id": row.get("row_id"), "reason": "PATTERN_MIRROR_UNPROVEN"})
                    continue
                if cid == 30310 and REACTIVE_HEAL_RE.match(text):
                    carrier = next((e for e in parent["edges"] if e["type"] == 64), None)
                    if carrier is None:
                        report["rejections"].append({"row_id": row.get("row_id"), "reason": "TYPE64_CARRIER_MISSING"})
                        continue
                    raw = carrier["record"].get("skillparam1")
                    if raw is None or (isinstance(raw, float) and not math.isfinite(raw)):
                        report["rejections"].append({"row_id": row.get("row_id"), "reason": "VALUE_MISSING"})
                        continue
                    if table == "charainfo":
                        ok, why = EQ.field_allowed(cid, "/skillparam1")
                        if not ok:
                            report["rejections"].append({"row_id": row.get("row_id"),
                                                         "reason": f"CHARAINFO_EQUIVALENCE_GATE_UNMET:{why}"})
                            continue
                        if (chara or {}).get("skillparam1") is not None and chara["skillparam1"] != raw:
                            report["rejections"].append({"row_id": row.get("row_id"),
                                                         "reason": "CHARAINFO_COPY_DIFFERS_FROM_PATTERN"})
                            continue
                    note = (f"对象：味方全体；回复量 = 本技能基础攻击 × {raw:g}（该技能自身的基础攻击，已含 Chain）；"
                            "条件：本档发动期间，味方每次受到伤害触发，可超过 HP 上限；"
                            "时长：按受击触发，无固定间隔；"
                            "未知：单场触发次数上限、超上限保留比例、共鳴/超共鳴升级条件、最终实际回复量。")
                    ans = _ky_answer(
                        data, row, parent, carrier, raw,
                        "bossskill|64|/skillparam1", "/skillparam1",
                        "回复量输入（reactive heal 基值）", "系数（相对B）",
                        f"floor/clamp(float32(B × {raw:g}))（reactive heal 基值）",
                        note, "味方/受击对象（type64 触发条件未证）",
                        "仅该档必杀（pattern %d）被选中时适用；共鳴成立/超共鳴升级条件无原生证据。" % parent["entry"]["reference_id"],
                        str(carrier["slot"]),
                    )
                    _ky_append(row, ans, report, "reactive_heal_base")
                elif cid in (30252, 30255, 30306) and DASH_RE.match(text):
                    m = DASH_RE.match(text)
                    count = m.group(1)
                    s52 = next((e for e in parent["edges"] if e["type"] == 52), None)
                    s114 = next((e for e in parent["edges"] if e["type"] == 114), None)
                    if s52 is None or s114 is None:
                        report["rejections"].append({"row_id": row.get("row_id"), "reason": "TYPE52_114_CARRIER_MISSING"})
                        continue
                    raw = s114["record"].get("skillparam1")
                    if raw is None or (isinstance(raw, float) and not math.isfinite(raw)):
                        report["rejections"].append({"row_id": row.get("row_id"), "reason": "VALUE_MISSING"})
                        continue
                    note = (f"对象：冲刺范围内的所有敌人；每回伤害 = 本技能基础攻击 × {raw:g}（已含 Chain）；"
                            f"条件：该档必杀发动、敌人位于冲刺范围内；"
                            f"时长：原文写 {count} 回连续攻击（次数为文本值，未由处理器参数验证）；"
                            "未知：是否每回命中、间隔、共鳴/超共鳴升级条件、最终扣血。")
                    ans = _ky_answer(
                        data, row, parent, s114, raw,
                        "bossskill|114|/skillparam1", "/skillparam1",
                        "伤害输入倍率", "倍率（相对B）",
                        f"floor/clamp(float32(B × {raw:g}))",
                        note, "冲刺范围内的敌人（target_selection 未证）",
                        "仅该档必杀（pattern %d）被选中时适用；共鳴成立/超共鳴升级条件无原生证据。" % parent["entry"]["reference_id"],
                        str(s114["slot"]),
                    )
                    _ky_append(row, ans, report, "dash_repeat_rate")
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="YG1 共鳴必殺 A/B 档重筛（阶段一，只读输入，写指定 JSONL）")
    ap.add_argument("--context", required=True, help="scratch/yg1_context.json")
    ap.add_argument("--rules", default="output/character_skills/profiles/rules.json")
    ap.add_argument("--c-outcomes", default="output/character_skills/yg1_remaining_ab_batch1_20261025/candidate_outcomes.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary-out")
    args = ap.parse_args(argv)
    ctx = json.loads(Path(args.context).read_text(encoding="utf-8"))
    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    c_rem = {}
    p = Path(args.c_outcomes)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r["after_status"] != "has_answer":
                c_rem[r["effect_id"]] = {"workstream": r["workstream"], "disposition": r["disposition"],
                                         "historical_tier": r["historical_tier"]}
    records = classify_items(ctx["items"], rules, c_rem)
    Path(args.out).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    s = summary(records)
    if args.summary_out:
        Path(args.summary_out).write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(s, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
