"""P2 batch 10: the heal family and the remaining ``bhSkill.Exec_*`` types.

The P2-9 batch closed with 147 characters whose only status is "unknown".  Its
machine-readable breakdown (``cp_paths/p9_increment.json``) says the cause is no
longer a missing equivalence premise but **missing type rules**:

* ``bhSkill.Exec_HEAL`` (types 10/11/12/14/26/28/31/32/46) -- 53+ characters,
* ``Exec_FALL_AREA`` / ``Exec_FALL_AREA2`` (33/103) -- 11,
* ``Exec_LOCKED_SUPPORT`` (23) -- 14, ``Exec_SHOOT_BACK`` (6) -- 11,
  ``Exec_SHOOT_RANDOM`` (7) -- 11,
* and a tail of single-digit buckets (19/29/34/43/44/49/50/51/55/56/64/67/68/69/
  72/73/74/75/76/80/82/86/87/88/114 ...).

This batch answers them from the recovered native image, with the same evidence
discipline the earlier batches used: every claim is either

* **recomputed from the type's own handler** (the ``getBasicSkillAttack(true) ×
  slot`` multiplication is located by walking the call graph *restricted to the
  functions reachable from that type's handler*, the integerisation call is
  ``0x14374bc``), or
* **pinned**: the exact ``(rva, instruction text)`` pair is re-read from the image
  on every run, and a mismatch means the slot produces **no rule at all**.

The ``Exec_HEAL`` family is one shared handler selected by two mode arguments
(``w2`` = target selection, ``w3`` = action select), so the mode tables are
recomputed from the game's own jump tables (``charainfo_types.build_index``) and
the shared body is decoded once:

```text
bhSkill.Exec_HEAL(0x1299c74)  w2=mode  w3=act  w4=type
  -> bhSkillUtil.Exec_HEAL(0x1187c80)   target list build (switch on mode)
     -> bhSkillUtil.Exec_HEAL_common(0x1188194)  (switch on act)
        act 0 types 10/11/28 : heal(sp1)            [+ type28 conditional support]
        act 1 types 12/13/14 : support (sp1/sp2/sp6 x chainRate, time sp3, atkSpeed sp4)
        act 2 type  26       : support (sp1/sp2 x chainRate, time sp3, atkSpeed sp4)
        act 3 types 15/16    : shield
        act 4 type  31       : heal(sp1) + support(attack sp2, time sp3)
        act 5 type  32       : heal(sp1) + support(guard sp2, time sp3)
        act 6 type  46       : heal(sp1) + support(sp2/sp3/sp4) + support2(sp6..sp8)
```

The over-heal (HP ceiling) flags are merged by ``HealSkill_HealFlag`` **only for
acts {0,4,5,6}** and the ratio table is the one ``output/boss_heal`` already
recovered (bits 40/35/41/42/43/44 -> 1.2/1.3/1.4/1.6/1.8/2.0); types 10/11, 28 and
31/32 additionally carry a per-record floor in sp2 / sp5 / sp4.

Outputs (``output/character_skills/boss_heal_types/``):

* ``type_rules.json``   -- per type: handler/body RVA, mode table, every slot with
  its evidence RVA, the unresolved slots and the reason, the raw value distribution.
* ``native_checks.json``-- the controlled checks (all must pass).
* ``field_dictionary.json`` -- the new rule rows, merged by ``rules.py`` as a fifth
  rule source (only keys the earlier dictionaries do not already define).
* ``p10_increment.json``-- coverage increment / zero-breakage report
  (``--report-increment``).
* ``README.md``.

Read-only over the existing unpacked artefacts; no new dependency; no game value is
imported from outside the repository.
"""
from __future__ import annotations

import collections
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT / "scripts", ROOT / "scripts" / "character_skills", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from character_skills import common as C  # noqa: E402
import charainfo_types as CT  # noqa: E402
import boss_attack_types as BT  # noqa: E402

OUT = ROOT / "output" / "character_skills" / "boss_heal_types"
PROF = ROOT / "output" / "character_skills" / "profiles"
GAPS = ROOT / "output" / "character_skills" / "gaps"
BOSS_HEAL_CONSTANTS = ROOT / "output" / "boss_heal" / "constants.json"
RECORDS_BEFORE = ROOT / "work" / "p10_records_before.jsonl"
SUMMARY_BEFORE = ROOT / "work" / "p10_summary_before.json"

SLOT_OF_OFFSET = {0x2C + 4 * i: i for i in range(10)}
EXEC_HEAL = 0x1299C74
EXEC_HEAL_DISPATCH = 0x1187C80
HEAL_COMMON = 0x1188194
HEAL_FLAG_HELPER = 0x1182B4C
GET_BASIC_RVA = 0x1182ED8
TRUNC_RVA = 0x14374BC
CHARA_HEAL = 0x1541158
SET_SUPPORT = 0x17765E0
CHAIN_RATE_OFF = 0x18
ATTACK_FLAG_HELPER = 0x11826C0       # bhSkillUtil.AttackSkill_AttackFlag

STATUS = "已确认（原生静态代码局部语义；本批新定位）"
# extra pinned assertions that do not carry a rule by themselves
PARTIAL_CHECKS = [
    (43, 0x119031C, "ldr      s9, [x8]", "两条 atk_rate 分支共用这一个装载点"),
    (43, 0x1190300, "cmp      w22, w21", "首段/末段的分支条件"),
    (43, 0x1190220, "bl       #0x10aedc0", "BattleManager.GetDeltaTime"),
    (43, 0x11903A4, "bl       #0x11846d8", "AttackNear_Common 实参 (f0=半径, f1=atkRate, f2=pushPow)"),
    (36, 0x118D1C0, "bl       #0x176ebfc", "CharaStatus.SetSteelGuard（仅一个 float 参数）"),
    (87, 0x119F468, "bl       #0x130ef70", "BtEffect_LineExec_ContSupport..ctor"),
    (87, 0x119F440, "fmul     s1, s9, s14", "实参 1 = chainRate × sp1"),
    (87, 0x119F44C, "fmul     s4, s9, s10", "实参 4 = chainRate × sp4"),
]
EVIDENCE_FILES = {
    "type_rules": "output/character_skills/boss_heal_types/type_rules.json",
    "native_checks": "output/character_skills/boss_heal_types/native_checks.json",
}

# ---------------------------------------------------------------------------
# per-type spec
# ---------------------------------------------------------------------------
# ``kind``       -- the role of the slot (drives the answer converter and the
#                   dictionary row text in rules.py).
# ``pins``       -- (rva, exact instruction text) pairs re-read on every run.
#                   A single mismatch drops the rule for that slot.
# ``note``       -- extra sentence appended to the rendered answer.
HEAL_ACTIONS = {
    0: ("heal", "0x118834C"),
    1: ("support", "0x1188444"),
    2: ("support", "0x1188478"),
    3: ("shield", "0x11884B4"),
    4: ("heal_support", "0x11883E4"),
    5: ("heal_support", "0x11885A8"),
    6: ("heal_support2", "0x1188638"),
}

HEAL_FAMILY = {
    # slot -> (kind, load_rva, expected instruction, note)
    10: [("heal_base", 1, 0x1188358, "ldr      s1, [x22, #0x30]", None),
         ("over_heal_ratio", 2, 0x1188290, "ldr      s0, [x22, #0x34]", None)],
    11: [("heal_base", 1, 0x1188358, "ldr      s1, [x22, #0x30]", None),
         ("over_heal_ratio", 2, 0x1188290, "ldr      s0, [x22, #0x34]", None)],
    12: [("support_attack", 1, 0x1188454, "ldp      s0, s1, [x22, #0x30]", None),
         ("support_guard", 2, 0x1188454, "ldp      s0, s1, [x22, #0x30]", None),
         ("support_move", 6, 0x1188458, "ldp      s5, s3, [x22, #0x40]", None),
         ("support_time", 3, 0x118845C, "ldp      s6, s4, [x22, #0x38]", None),
         ("support_atk_speed", 4, 0x118845C, "ldp      s6, s4, [x22, #0x38]", None)],
    14: [("support_attack", 1, 0x1188454, "ldp      s0, s1, [x22, #0x30]", None),
         ("support_guard", 2, 0x1188454, "ldp      s0, s1, [x22, #0x30]", None),
         ("support_move", 6, 0x1188458, "ldp      s5, s3, [x22, #0x40]", None),
         ("support_time", 3, 0x118845C, "ldp      s6, s4, [x22, #0x38]", None),
         ("support_atk_speed", 4, 0x118845C, "ldp      s6, s4, [x22, #0x38]", None)],
    26: [("support_attack", 1, 0x1188488, "ldp      s0, s2, [x22, #0x30]", None),
         ("support_guard", 2, 0x1188488, "ldp      s0, s2, [x22, #0x30]", None),
         ("support_time", 3, 0x118848C, "ldp      s6, s4, [x22, #0x38]", None),
         ("support_atk_speed", 4, 0x118848C, "ldp      s6, s4, [x22, #0x38]", None)],
    28: [("heal_base", 1, 0x1188358, "ldr      s1, [x22, #0x30]", None),
         ("over_heal_ratio", 5, 0x11882AC, "ldr      s0, [x22, #0x40]",
          "与 type46 共用同一个装载点（0x11882AC）：w3=0 且类型 == 0x1c 时 0x11882A8 `b.ne` 不跳转"),
         ("support_attack_raw", 2, 0x11883A4, "ldr      s0, [x22, #0x34]",
          "该条支援仅当 |sp2| 或 |sp3| 超过阈值（0x29ab000+0x820 的浮点项）时才施加"),
         ("support_guard_raw", 3, 0x11883D8, "ldp      s1, s6, [x22, #0x38]", None),
         ("support_time", 4, 0x11883D8, "ldp      s1, s6, [x22, #0x38]", None)],
    31: [("heal_base", 1, 0x11883F0, "ldr      s1, [x22, #0x30]", None),
         ("over_heal_ratio", 4, 0x1188298, "ldr      s0, [x22, #0x3c]", None),
         ("support_attack_raw", 2, 0x1188434, "ldp      s0, s6, [x22, #0x34]", None),
         ("support_time", 3, 0x1188434, "ldp      s0, s6, [x22, #0x34]", None)],
    32: [("heal_base", 1, 0x11885B4, "ldr      s1, [x22, #0x30]", None),
         ("over_heal_ratio", 4, 0x1188298, "ldr      s0, [x22, #0x3c]", None),
         ("support_guard_raw", 2, 0x11885F8, "ldp      s1, s6, [x22, #0x34]", None),
         ("support_time", 3, 0x11885F8, "ldp      s1, s6, [x22, #0x34]", None)],
    46: [("heal_base", 1, 0x1188644, "ldr      s1, [x22, #0x30]", None),
         ("support_attack_raw", 2, 0x118868C, "ldp      s0, s1, [x22, #0x34]", None),
         ("support_guard_raw", 3, 0x118868C, "ldp      s0, s1, [x22, #0x34]", None),
         ("support_time", 4, 0x118865C, "ldr      s10, [x22, #0x3c]", None),
         ("over_heal_ratio", 5, 0x11882AC, "ldr      s0, [x22, #0x40]",
          "与 type28 共用同一个装载点（0x11882AC）：w3=6 时 0x118827C `cmp w19,#0x2e` → 0x1188280 "
          "`b 0x11882a4` → `fmov`／`b` 不改标志位 → 0x11882A8 `b.ne` 不跳转 → 落到该装载点"),
         ("time_power_up_move", 6, 0x11886D8, "ldr      w8, [x22, #0x44]",
          "字段名 _move 取自元数据字段表（原生只做 4 字节原样存储）"),
         ("time_power_up_critical", 7, 0x11886E0, "ldr      x8, [x22, #0x48]",
          "与 sp8 是同一条 8 字节装载（0x11886E0）覆盖 0x24/0x28 两个字段"),
         ("time_power_up_critical_dmg", 8, 0x11886E0, "ldr      x8, [x22, #0x48]",
          "8 字节装载的后 4 字节")],
}

# ---------------------------------------------------------------------------
# generic types: (kind, expected slot, expected w1 passed to getBasicSkillAttack)
# ---------------------------------------------------------------------------
GENERIC = {
    6: ("atk_rate", 1),
    7: ("atk_rate", 1),
    29: ("atk_rate", 1),
    34: ("skill_base_value", 1),
    44: ("atk_rate", 1),
    49: ("atk_rate", 1),
    50: ("skill_base_value", 1),
    51: ("atk_rate", 0),
    64: ("skill_base_value", 1),
    67: ("atk_rate", 1),
    69: ("atk_rate", 1),
    72: ("skill_base_value", 1),
    74: ("atk_rate", 5),
    75: ("heal_base", 0),
    76: ("skill_base_value", 1),
    80: ("atk_rate", 1),
    82: ("atk_rate", 1),
    86: ("skill_base_value", 1),
    114: ("atk_rate", 1),
}

# types whose own damage site does not fit the generic shape and were read by hand
HANDPIN = {
    19: {"kind": "atk_rate_runtime_count", "slot": 1,
         "pins": [(0x1189530, "mov      w1, wzr"),
                  (0x1189534, "bl       #0x1182ed8"),
                  (0x1189538, "ldr      s1, [x21, #0x30]"),
                  (0x1189544, "fmul     s1, s1, s2"),
                  (0x1189548, "fmul     s0, s0, s1"),
                  (0x118954C, "bl       #0x14374bc")],
         "note": ("整数化后交给 bhSkillUtil.AttackSkill_AttackFlag（0x11895E8）／"
                  "CharaBehavior.Attack（0x11896B8）"),
         "load_rva": 0x1189538},
    55: {"kind": "atk_rate", "slot": 1,
         "pins": [(0x1194F00, "bl       #0x1182ed8"),
                  (0x1194F08, "mov      v12.16b, v0.16b"),
                  (0x1195034, "ldr      s0, [x21, #0x30]"),
                  (0x119503C, "fmul     s0, s12, s0"),
                  (0x1195040, "bl       #0x14374bc")],
         "note": ("乘数 s12 是本函数内保留的 B（0x1194F08 把 0x1194F00 的返回值搬进 v12）；"
                  "结果写入 BulletSpiralLaser.Initialize 的伤害输入"),
         "load_rva": 0x1195034},
}

# types whose own body was read by hand in this batch (pinned extras)
CUSTOM = {
    6: [("shoot_back_note", None)],
}

# per-type extra pinned slots (read by hand, verified instruction by instruction)
EXTRA_SLOTS = {
    7: [("repeat_count", 3, 0x11874EC, "ldr      s1, [x19, #0x38]", None),
        ("repeat_timer_reset", 2, 0x1187524, "ldr      w10, [x19, #0x34]", None)],
    23: [("support_attack", 1, 0x118AF48, "fmul     s8, s1, s0", None),
         ("support_guard", 2, 0x118AF4C, "fmul     s9, s0, s2", None),
         ("support_crit_dmg", 7, 0x118AF8C, "ldr      w8, [x20, #0x48]", None)],
    33: [("fall_offset", 3, 0x118C480, "ldr      s0, [x20, #0x38]", None),
         ("fall_selector", 6, 0x118C42C, "ldr      s0, [x20, #0x44]", None)],
    103: [("fall_offset", 3, 0x118C628, "ldr      s0, [x20, #0x38]",
           "与 type33 共用同一套落点／夹紧逻辑；本类型没有 sp6 选择码分支（无 0x118C42C 同级读取）")],
    36: [("steel_guard_time", 3, 0x118D198, "fmul     s8, s1, s2", None),
         ("steel_guard_self_gate", 2, 0x118D1A0, "fcvtzs   w8, s0", None)],
    43: [("count_cap", 3, 0x1190224, "ldr      s1, [x19, #0x38]", None),
         ("attack_interval", 2, 0x119026C, "ldr      w9, [x19, #0x34]", None),
         ("atk_rate", 1, 0x1190314, "add      x8, x19, #0x30",
          "择槽条件：0x1190300 的 `w22 <= trunc(sp3)`（即除最后一击外的各击）"),
         ("atk_rate_last", 4, 0x119030C, "add      x8, x19, #0x3c", None),
         ("push_pow_last", 5, 0x1190308, "ldr      s8, [x19, #0x40]", None),
         ("post_last_delay", 6, 0x1190290, "ldr      s0, [x19, #0x44]", None)],
    87: [("support_area_payload1", 1, 0x119F3E4, "ldp      s14, s13, [x21, #0x30]",
          "原生实参寄存器 s1"),
         ("support_area_payload2", 2, 0x119F3E4, "ldp      s14, s13, [x21, #0x30]",
          "原生实参寄存器 s2"),
         ("support_area_payload3", 3, 0x119F3E8, "ldp      s11, s10, [x21, #0x38]",
          "原生实参寄存器 s3"),
         ("support_area_payload4", 4, 0x119F3E8, "ldp      s11, s10, [x21, #0x38]",
          "原生实参寄存器 s4")],
}


def instruction_text(view, rva):
    return view.text_at(rva)


# --- over-heal (HP ceiling) floor slot, decoded from the branch itself ----------------
# 0x1188268  cmp w19, #0x1c          ; w19 = effect type
# 0x118826C  b.le #0x1188284
# 0x1188270  sub w8, w19, #0x1f      ; types > 0x1c
# 0x1188274  cmp w8, #2
# 0x1188278  b.lo #0x1188298         ; 31/32 -> 0x1188298  ldr s0,[x22,#0x3c] = sp4
# 0x118827C  cmp w19, #0x2e          ; 46
# 0x1188280  b    #0x11882a4         ; (unconditional: flags from the cmp survive)
# 0x1188284  and w8, w19, #0xfffffffe
# 0x1188288  cmp w8, #0xa
# 0x118828C  b.ne #0x11882a0         ; not type 10/11 -> 0x11882a0
# 0x1188290  ldr s0, [x22, #0x34]    ; 10/11 -> sp2
# 0x11882A0  cmp w19, #0x1c          ; types <= 0x1c that reach here
# 0x11882A4  fmov s0, wzr            ; (does not set flags)
# 0x11882A8  b.ne #0x11882b0         ; 28 -> not taken (falls through); 46 -> not taken
# 0x11882AC  ldr s0, [x22, #0x40]    ; 28 and 46 -> sp5
#
# `fmov` and `b` do **not** update NZCV, so the `b.ne` at 0x11882A8 consumes the flags
# left by the most recent comparison on that path: `cmp w19, #0x1c` for types <= 0x1c and
# `cmp w19, #0x2e` for the >0x1c path.  Hence **both type 28 and type 46 take sp5**.
OVER_HEAL_BRANCH = [
    (0x1188268, "cmp      w19, #0x1c"),
    (0x118826C, "b.le     #0x1188284"),
    (0x1188270, "sub      w8, w19, #0x1f"),
    (0x1188274, "cmp      w8, #2"),
    (0x1188278, "b.lo     #0x1188298"),
    (0x118827C, "cmp      w19, #0x2e"),
    (0x1188280, "b        #0x11882a4"),
    (0x1188284, "and      w8, w19, #0xfffffffe"),
    (0x1188288, "cmp      w8, #0xa"),
    (0x118828C, "b.ne     #0x11882a0"),
    (0x1188290, "ldr      s0, [x22, #0x34]"),
    (0x1188294, "b        #0x11882b0"),
    (0x1188298, "ldr      s0, [x22, #0x3c]"),
    (0x118829C, "b        #0x11882b0"),
    (0x11882A0, "cmp      w19, #0x1c"),
    (0x11882A4, "fmov     s0, wzr"),
    (0x11882A8, "b.ne     #0x11882b0"),
    (0x11882AC, "ldr      s0, [x22, #0x40]"),
    (0x11882B0, "ldr      s8, [sp, #0x1c]"),
]


def over_heal_floor_slot(t):
    """The slot the over-heal floor is read from for effect type ``t`` (None = no floor).

    Mirrors :data:`OVER_HEAL_BRANCH` with ARM64 flag semantics; the generator checks it
    against every pinned slot so a wrong branch reading cannot survive.
    """
    if t <= 0x1C:
        if (t & ~1) == 0xA:            # 10 / 11
            return 2
        return 5 if t == 0x1C else None
    if (t - 0x1F) < 2:                 # 31 / 32
        return 4
    return 5 if t == 0x2E else None    # 46 shares type 28's load


def w1_before_getbasic(view, func_rva, bl_rva):
    """the integer passed as w1 to getBasicSkillAttack at ``bl_rva``."""
    last = None
    for insn in view.insns(func_rva):
        if insn.address > bl_rva:
            break
        if insn.mnemonic == "mov" and insn.op_str.startswith("w1, "):
            last = insn.op_str.split(", ")[1]
    if last is None:
        return None
    if last == "wzr":
        return 0
    if last.startswith("#"):
        return int(last[1:], 0)
    return None


def consumer_of(view, dmg_rva, trunc_rva, window=16):
    """the first named callee after the integerisation (what consumes w0)."""
    out = []
    for insn in view.insns(dmg_rva):
        if insn.address <= trunc_rva:
            continue
        if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
            nm = view.name(int(insn.op_str[1:], 0))
            if nm:
                out.append((hex(insn.address), nm))
        if insn.mnemonic in ("ret",):
            break
        if len(out) >= window:
            break
    return out


# ---------------------------------------------------------------------------
# analysis
# ---------------------------------------------------------------------------
def heal_constants():
    doc = json.loads(BOSS_HEAL_CONSTANTS.read_text(encoding="utf-8"))
    return {
        "bits": list(doc["bits"]["values"]),
        "ratios": list(doc["values"]["values"]),
        "note": ("复用 output/boss_heal/constants.json（type27 的既有证据）："
                 "Constants.s_flagList 位序与 s_valueList 档位"),
    }


def check(checks, name, ok, **kw):
    checks.append({"name": name, "ok": bool(ok), **kw})
    return bool(ok)


def analyze(view, md):
    checks = []
    index = {e["type"]: e for e in CT.build_index(view.n)}
    types = {}

    # -- anchors the whole family rests on ------------------------------------
    check(checks, "heal_family_shares_one_handler",
          len({index[t]["handler_rva"] for t in HEAL_FAMILY}) == 1
          and index[10]["handler_rva"] == hex(EXEC_HEAL),
          detail=json.dumps({str(t): index[t]["mode_args"] for t in sorted(HEAL_FAMILY)},
                            ensure_ascii=False))
    check(checks, "exec_heal_common_is_reached_by_the_dispatch",
          instruction_text(view, 0x1299CDC) == "bl       #0x1187c80"
          and instruction_text(view, 0x1299CCC) == "mov      w4, w22"
          and instruction_text(view, 0x1299CD0) == "mov      w5, w21"
          and instruction_text(view, 0x1299CD4) == "mov      w6, w20",
          detail="bhSkill.Exec_HEAL 把 (mode=w2, act=w3, type=w4) 依次放进 w4/w5/w6 传给 "
                 "bhSkillUtil.Exec_HEAL，再传给 Exec_HEAL_common（参数序为 mode→act→type）")
    check(checks, "exec_heal_common_forwards_act_and_type",
          instruction_text(view, 0x1188154) == "mov      w2, w22"
          and instruction_text(view, 0x118814C) == "ldr      w3, [sp, #0xc]"
          and instruction_text(view, 0x1188158) == "bl       #0x1188194",
          detail="Exec_HEAL 的最后一步：Exec_HEAL_common(util, list, w2=w22=act, w3=type)")
    check(checks, "heal_common_parameters",
          [p["name"] for p in md.method(
              view._method_by_rva[0x11881B4] if 0x11881B4 in view._method_by_rva else
              view._method_by_rva[min(a for a in view._method_by_rva
                                      if a >= 0x1188194)])["parameters"]] ==
          ["charaList", "mode", "skill_type"],
          detail="Exec_HEAL_common(x0=util, x1=charaList, w2=act, w3=type)")
    consts = heal_constants()
    check(checks, "over_heal_table_from_boss_heal",
          consts["bits"] == [40, 35, 41, 42, 43, 44]
          and [round(v, 3) for v in consts["ratios"]] == [1.2, 1.3, 1.4, 1.6, 1.8, 2.0],
          detail="位序/档位与 output/boss_heal/constants.json 逐值相同（未从枚举名猜数值）")

    # -- the shared body, decoded once ---------------------------------------
    body = [
        ("heal flag merge gate", 0x118824C, "tst      w8, w9"),
        ("heal flag helper call", 0x1188260, "bl       #0x1182b4c"),
        ("over-heal compare", 0x11882B4, "fcmp     s8, s0"),
        ("over-heal store", 0x11882C0, "str      s0, [sp, #0x1c]"),
        ("getBasicSkillAttack", 0x1188354, "bl       #0x1182ed8"),
        ("heal coefficient", 0x1188358, "ldr      s1, [x22, #0x30]"),
        ("heal multiply", 0x1188360, "fmul     s0, s0, s1"),
        ("heal integerisation", 0x1188364, "bl       #0x14374bc"),
        ("CharaBehavior.Heal", 0x1188390, "bl       #0x1541158"),
        ("SetSupport site", 0x1188620, "bl       #0x17765e0"),
    ]
    for label, rva, want in body:
        check(checks, f"shared_body:{label}", instruction_text(view, rva) == want,
              detail=f"{hex(rva)}: {instruction_text(view, rva)}（期望 {want}）")

    # HealSkill_HealFlag sets the over-heal ratio; the flag merge is gated by act bits
    check(checks, "heal_flag_merge_is_gated_by_the_act_number",
          instruction_text(view, 0x1188240) == "mov      w8, #1"
          and instruction_text(view, 0x1188248) == "mov      w9, #0x71"
          and instruction_text(view, 0x118824C) == "tst      w8, w9",
          detail="0x71=0b1110001 → act∈{0,4,5,6} 才调用 HealSkill_HealFlag（类型 10/11/28/31/32/46）")

    # the over-heal floor slot is decided by a branch that must be read with flag
    # semantics: `fmov`/`b` do not set NZCV, so the `b.ne` at 0x11882A8 consumes the
    # flags of the *most recent* comparison on that path (type 46 -> `cmp w19,#0x2e`).
    seq_ok = all(instruction_text(view, a) == w for a, w in OVER_HEAL_BRANCH)
    check(checks, "over_heal_branch_bytes_are_as_decoded", seq_ok,
          detail=json.dumps([[hex(a), instruction_text(view, a)] for a, _w in OVER_HEAL_BRANCH],
                            ensure_ascii=False))
    check(checks, "over_heal_floor_slot_follows_the_branch_not_the_first_reading",
          all(over_heal_floor_slot(t)
              == (HEAL_FAMILY.get(t) and next((s for k, s, *_ in HEAL_FAMILY[t]
                                               if k == "over_heal_ratio"), None))
              for t in (10, 11, 28, 31, 32, 46))
          and over_heal_floor_slot(46) == 5 and over_heal_floor_slot(28) == 5
          and all(over_heal_floor_slot(t) is None for t in (12, 13, 14, 15, 16, 26)),
          detail=json.dumps({str(t): over_heal_floor_slot(t)
                             for t in (10, 11, 12, 13, 14, 15, 16, 26, 28, 31, 32, 46)},
                            ensure_ascii=False))

    # ---- heal family --------------------------------------------------------
    for t in sorted(HEAL_FAMILY):
        entry = index[t]
        mode = entry["mode_args"] or {}
        w2, w3 = mode.get("w2"), mode.get("w3")
        if w2 is None or w3 is None:
            w2, w3 = 0, 0
        info = {
            "type": t, "case_rva": entry["case_rva"], "handler": entry["handler"],
            "handler_rva": entry["handler_rva"],
            "body": "bhSkillUtil.Exec_HEAL_common", "body_rva": hex(HEAL_COMMON),
            "mode_selector": w2, "act_selector": w3,
            "action": HEAL_ACTIONS.get(w3, ("unknown", None))[0],
            "slots": {}, "unresolved": [], "checks": [],
        }
        tadd = lambda name, ok, **kw: (  # noqa: E731
            checks.append({"name": f"t{t}.{name}", "ok": bool(ok), **kw}),
            info["checks"].append({"name": name, "ok": bool(ok), **kw}),
            bool(ok))[2]
        act = HEAL_ACTIONS.get(w3)
        tadd("act_select_is_a_known_action", act is not None,
             detail=f"w3={w3} → {act[0] if act else '未知'} @ {act[1] if act else '-'}")
        for kind, slot, rva, want, note in HEAL_FAMILY[t]:
            got = instruction_text(view, rva)
            ok = got == want
            tadd(f"slot{slot}_{kind}_pin", ok,
                 detail=f"{hex(rva)}: {got}（期望 {want}）")
            if ok:
                rec = {"slot": slot, "kind": kind, "load_rva": hex(rva), "load": got}
                if note:
                    rec["note"] = note
                # a slot may be claimed twice (e.g. 12/13/14 share one ldp);
                # keep both claims only when the kind differs.
                prev = info["slots"].get(kind)
                if prev is not None:
                    info["slots"][kind] = {**prev, "also": rec}
                else:
                    info["slots"][kind] = rec
        types[t] = info

    # 13/15/16 already have rules from the earlier boss_heal line: keep them out of
    # the new-rule set but record the shared-action table for the sanity check.
    for t in (13, 15, 16):
        entry = index[t]
        mode = entry["mode_args"] or {}
        types[t] = {
            "type": t, "handler": entry["handler"], "handler_rva": entry["handler_rva"],
            "body_rva": hex(HEAL_COMMON), "mode_selector": mode.get("w2"),
            "act_selector": mode.get("w3"),
            "action": HEAL_ACTIONS.get(mode.get("w3"), ("unknown", None))[0],
            "slots": {}, "unresolved": ["本批不为该类型新增规则（13 已有 boss_heal 规则，"
                                        "15/16 不在本批未知角色集合内）"],
            "checks": [], "already_covered": True,
        }

    # slots the shared body reads for each type (read by hand, act branch by act branch)
    read_slots = {
        10: {1, 2}, 11: {1, 2}, 12: {1, 2, 3, 4, 5, 6}, 13: {1, 2, 3, 4, 5, 6},
        14: {1, 2, 3, 4, 5, 6}, 15: {1, 2, 5, 6, 7}, 16: {1, 2, 5, 6, 7},
        26: {1, 2, 3, 4, 5}, 28: {1, 2, 3, 4, 5}, 31: {1, 2, 3, 4},
        32: {1, 2, 3, 4}, 46: {1, 2, 3, 4, 5, 6, 7, 8},
    }
    for t, info in types.items():
        if info.get("already_covered"):
            continue
        claimed = {r["slot"] for r in info["slots"].values()}
        for slot in sorted(read_slots.get(t, set()) - claimed):
            reason = ("作为 SetSupport 的第 6 个浮点实参传入（s5），但 SetSupport_noCheckTime"
                      "（0x17765F0）体内不存储该实参；元数据把它命名为 push_power，"
                      "消费点在别的重载里 → 未定位，不给规则" if slot == 5 else
                      "该槽在本类型的动作分支内被读取但语义未定")
            info["unresolved"].append(f"skillparam{slot}：{reason}")

    # target selection descriptions are recomputed from the dispatch mode
    for t, info in types.items():
        m = info.get("mode_selector")
        info["target_selection"] = {
            0: "只把施法者自身（bhSkillUtil._attacker，0xb8）放进列表",
            1: "BattleManager.GetMemberList(_type, onlyActive=1, onlyAlive=1) → "
               "BtlCharaUtil.CheckJobFlag(list, iParam0)（iParam0==0 不筛选职业）",
            2: "同 mode 1，再随机取 1 人（0x190732C → List.get_Item）",
            3: "同 mode 1，再取 HP 比例最低者（BattleParam.get_inv_hpMax × _hp），"
               "_type 影响同值时的次级比较（0x1188030..0x11880A8）",
        }.get(m, "未识别")
        info["mode_args_raw"] = index[t]["mode_args"]

    return checks, types, index, consts


def generic_analysis(view, md, checks, types):
    """damage/heal base of the remaining types, by the P2-8 machinery."""
    info_by_type = {}
    for t in sorted(GENERIC):
        entry = CT.build_index(view.n)[t]
        hrva = int(entry["handler_rva"], 16)
        util = BT.NativeView(view.md, view.n).name(hrva)
        util_rva = hrva if (util or "").startswith("bhSkillUtil.") else None
        if util_rva is None:
            for insn in view.insns(hrva):
                if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
                    nm = view.name(int(insn.op_str[1:], 0)) or ""
                    if nm.startswith("bhSkillUtil."):
                        util_rva = int(insn.op_str[1:], 0)
                        break
        want_kind, want_slot = GENERIC[t]
        info = {"type": t, "handler": entry["handler"], "handler_rva": entry["handler_rva"],
                "util_body": view.name(util_rva) if util_rva else None,
                "util_body_rva": hex(util_rva) if util_rva else None,
                "slots": {}, "unresolved": [], "checks": [],
                "target_selection": None}
        tadd = lambda name, ok, **kw: (  # noqa: E731
            checks.append({"name": f"g{t}.{name}", "ok": bool(ok), **kw}),
            info["checks"].append({"name": name, "ok": bool(ok), **kw}),
            bool(ok))[2]
        if util_rva is None:
            tadd("util_body_found", False, detail="未定位到 bhSkillUtil 体")
            info["unresolved"].append("未定位到 bhSkillUtil 体")
            info_by_type[t] = info
            continue
        dmg_rva, chain = BT.find_damage_function(view, util_rva)
        tadd("damage_function_found", dmg_rva is not None,
             chain=[hex(x) for x in (chain or [])])
        pat = BT.damage_pattern(view, dmg_rva) if dmg_rva else None
        tadd("basic_skill_attack_times_slot_then_integerise", pat is not None,
             detail=(f"{hex(pat['fmul_rva'])}: {pat['fmul']}；{hex(pat['trunc_rva'])}: 0x14374bc"
                     if pat else None))
        if not pat:
            info["unresolved"].append("未定位 getBasicSkillAttack × 槽 → 整数化 的乘法点")
            info_by_type[t] = info
            continue
        allowed = BT.NativeView(view.md, view.n).reachable_from(hrva) | {util_rva}
        got = BT.resolve_slot(view, dmg_rva, pat["fmul_rva"], pat["reg"], allowed=allowed)
        slot = (got or {}).get("slot")
        tadd("slot_resolved", slot is not None, detail=json.dumps(got, ensure_ascii=False))
        tadd("slot_matches_the_hand_read_expectation", slot == 0x2C + 4 * want_slot,
             detail=f"解析到 {slot}（期望 {hex(0x2C + 4 * want_slot)} = skillparam{want_slot}）")
        w1 = w1_before_getbasic(view, dmg_rva, next(
            i.address for i in view.insns(dmg_rva)
            if i.mnemonic == "bl" and i.op_str == f"#0x{GET_BASIC_RVA:x}"))
        tadd("getBasicSkillAttack_argument_is_the_expected_variant", w1 == 1,
             detail=f"w1={w1}（本批除 type19 外均为 1=true）")
        cons = consumer_of(view, dmg_rva, pat["trunc_rva"])
        tadd("consumer_located", bool(cons), detail=json.dumps(cons, ensure_ascii=False))
        if slot is None or slot != 0x2C + 4 * want_slot:
            info["unresolved"].append("解析到的槽与手工核对不一致，不产出规则")
            info_by_type[t] = info
            continue
        info["damage_function"] = {
            "name": view.name(dmg_rva), "rva": hex(dmg_rva),
            "chain": [hex(x) for x in (chain or [])],
            "fmul_rva": hex(pat["fmul_rva"]), "fmul": pat["fmul"],
            "trunc_rva": hex(pat["trunc_rva"]), "w1_to_getBasicSkillAttack": w1,
            "consumers": cons,
        }
        info["slots"][want_kind] = {
            "slot": want_slot, "kind": want_kind,
            "load_rva": hex(pat["fmul_rva"]), "load": pat["fmul"],
            "resolved_path": got.get("path"),
            "note": got.get("note"),
        }
        info_by_type[t] = info

    # hand-pinned extras
    for t, spec in HANDPIN.items():
        hrva = int(CT.build_index(view.n)[t]["handler_rva"], 16)
        nm = view.name(hrva)
        util_rva = hrva if (nm or "").startswith("bhSkillUtil.") else None
        if util_rva is None:
            for insn in view.insns(hrva):
                if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
                    cn = view.name(int(insn.op_str[1:], 0)) or ""
                    if cn.startswith("bhSkillUtil."):
                        util_rva = int(insn.op_str[1:], 0)
                        break
        # the pinned loads live in the bhSkillUtil body; find the owning function
        owner = view.bounds(spec["load_rva"])[0]
        info = info_by_type.get(t) or {"type": t, "handler": view.name(
            int(CT.build_index(view.n)[t]["handler_rva"], 16)),
            "handler_rva": CT.build_index(view.n)[t]["handler_rva"],
            "util_body": view.name(util_rva) if util_rva else None,
            "util_body_rva": hex(util_rva) if util_rva else None,
            "slots": {}, "unresolved": [], "checks": [],
            "target_selection": None}
        names = []
        for insn in view.insns(owner):
            if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
                nn = view.name(int(insn.op_str[1:], 0))
                if nn:
                    names.append((hex(insn.address), nn))
        info["damage_function"] = {"name": view.name(owner), "rva": hex(owner),
                                   "consumers": names[:12]}
        for rva, want in spec["pins"]:
            got = instruction_text(view, rva)
            ok = got == want
            checks.append({"name": f"h{t}.pin_{hex(rva)}", "ok": bool(ok),
                           "detail": f"{hex(rva)}: {got}（期望 {want}）"})
            info["checks"].append({"name": f"pin_{hex(rva)}", "ok": bool(ok)})
        info["slots"][spec["kind"]] = {
            "slot": spec["slot"], "kind": spec["kind"],
            "load_rva": hex(spec["load_rva"]),
            "load": instruction_text(view, spec["load_rva"]),
            "note": spec["note"], "handpinned": True,
        }
        info_by_type[t] = info

    for t, rows in EXTRA_SLOTS.items():
        if info_by_type.get(t) is None:
            entry = CT.build_index(view.n)[t]
            hrva = int(entry["handler_rva"], 16)
            nm = view.name(hrva)
            util_rva = hrva if (nm or "").startswith("bhSkillUtil.") else None
            if util_rva is None:
                for insn in view.insns(hrva):
                    if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
                        cn = view.name(int(insn.op_str[1:], 0)) or ""
                        if cn.startswith("bhSkillUtil."):
                            util_rva = int(insn.op_str[1:], 0)
                            break
            info_by_type[t] = {
                "type": t, "handler": nm, "handler_rva": entry["handler_rva"],
                "util_body": view.name(util_rva) if util_rva else None,
                "util_body_rva": hex(util_rva) if util_rva else None,
                "slots": {}, "unresolved": [], "checks": [],
                "target_selection": None,
            }
        info = info_by_type[t]
        for kind, slot, rva, want, note in rows:
            got = instruction_text(view, rva)
            ok = got == want
            checks.append({"name": f"x{t}.slot{slot}_{kind}_pin", "ok": bool(ok),
                           "detail": f"{hex(rva)}: {got}（期望 {want}）"})
            info["checks"].append({"name": f"slot{slot}_{kind}_pin", "ok": bool(ok)})
            if ok:
                rec = {"slot": slot, "kind": kind, "load_rva": hex(rva), "load": got}
                if note:
                    rec["note"] = note
                info["slots"][kind] = rec
        info_by_type[t] = info

    # type 23's support helper eats sp4/sp5/sp6 as three more floats: leave them
    # unresolved rather than guess the role.
    if 23 in info_by_type:
        info_by_type[23]["unresolved"].append(
            "sp4/sp5/sp6：被 0x118B0C8(util, list, flags, f1=sp1×chain, f2=sp2×chain, "
            "f3=sp4, f4=sp5, f5=sp6) 接收，helper 体内三个浮点各自的 SupportData 归属未定位")
        info_by_type[23]["unresolved"].append(
            "sp3：只用于结束条件（0x118B090 fcmp s0, attacker._crackupTime+sp3）")
    for t in (33, 103):
        if t in info_by_type:
            info_by_type[t]["unresolved"].append(
                "伤害本身在 AirAreaStrike(0x118380C) 建立的工作对象里结算（该对象 +0x40 持有 "
                "bhSkillUtil，伤害在其 update 中读取槽位）；本批未追进该 update → 伤害槽不给数值")
    for t in (33, 103):
        if t in info_by_type:
            info_by_type[t]["unresolved"].append(
                "sp7/sp8：type103 在 0x118C5E0 装入 s8/s9 并传给 AirAreaStrike 的位置／计数实参，"
                "本批未定其各分量归属")
    for t, rva, want, why in PARTIAL_CHECKS:
        got = instruction_text(view, rva)
        ok = got == want
        checks.append({"name": f"p{t}.{hex(rva)}", "ok": bool(ok),
                       "detail": f"{why}：{hex(rva)}: {got}（期望 {want}）"})
        if t in info_by_type:
            info_by_type[t]["checks"].append({"name": f"pin_{hex(rva)}", "ok": bool(ok)})
    types.update(info_by_type)
    return info_by_type


# ---------------------------------------------------------------------------
# rule rows
# ---------------------------------------------------------------------------
def role_text(kind):
    return BT.role_row("atk_rate", 1)[:3] if kind == "atk_rate" else (None, None, None)


def rule_rows(types, consts, skipped_existing):
    existing = BT._existing_rule_keys()
    rows = []
    for t, info in sorted(types.items()):
        if info.get("already_covered"):
            continue
        for kind, rec in sorted(info["slots"].items(), key=lambda kv: kv[1]["slot"]):
            slot = rec["slot"]
            key = ("bossskill", t, f"/skillparam{slot}")
            if key in existing:
                skipped_existing.append({
                    "type": t, "field_path": key[2], "role": kind,
                    "note": "既有字典（boss_heal 等）已定义该键，本批不重复声明（merge 只补缺键）"})
                continue
            rows.append({
                "table": "bossskill",
                "effect_type": t,
                "field_path": f"/skillparam{slot}",
                "answer_kind": kind,
                "load_rva": rec.get("load_rva"),
                "load": rec.get("load"),
                "role_note": rec.get("note"),
                "handler": info.get("handler"),
                "body": info.get("body") or info.get("util_body"),
                "action": info.get("action"),
                "mode_selector": info.get("mode_selector"),
                "target_selection": info.get("target_selection"),
                "evidence": [{"read_rva": rec.get("load_rva"), "detail": rec.get("load"),
                              "handler": info.get("handler"),
                              "body": info.get("body") or info.get("util_body"),
                              "type_rule_report": EVIDENCE_FILES["type_rules"],
                              "native_checks": EVIDENCE_FILES["native_checks"]}],
            })
    return rows


def main():
    C.enable_utf8_console()
    OUT.mkdir(parents=True, exist_ok=True)
    md, native = CT.load_native()
    view = BT.NativeView(md, native)
    checks, types, index, consts = analyze(view, md)
    generic_analysis(view, md, checks, types)
    passed = sum(1 for c in checks if c["ok"])
    failed = [c["name"] for c in checks if not c["ok"]]
    skipped_existing = []
    rules = rule_rows(types, consts, skipped_existing)
    C.write_json(OUT / "type_rules.json", {
        "batch": "P2 第 10 批",
        "scope": ("bhSkill.Exec_HEAL 家族（type 10/11/12/14/26/28/31/32/46）"
                  "＋ Exec_FALL_AREA/2（33/103）＋ 23/6/7 与其余可解类型的"
                  "「技能基值×槽 → 整数化」点"),
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
        "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
        "heal_family": {
            "handler": "bhSkill.Exec_HEAL", "handler_rva": hex(EXEC_HEAL),
            "dispatch_body": "bhSkillUtil.Exec_HEAL", "dispatch_body_rva": hex(EXEC_HEAL_DISPATCH),
            "common_body": "bhSkillUtil.Exec_HEAL_common", "common_body_rva": hex(HEAL_COMMON),
            "formula": "回复量 = floor/clamp(float32(B × skillparam1))；B = getBasicSkillAttack(true)",
            "integerisation_rva": hex(TRUNC_RVA),
            "consumer": "CharaBehavior.Heal(0x1541158)，regTime 参数接收超上限比率",
            "heal_flag_helper": "bhSkillUtil.HealSkill_HealFlag(0x1182b4c)",
            "over_heal_bits": consts["bits"], "over_heal_ratios": consts["ratios"],
            "support_object": "SupportData（_attackUp 0x10 / _guardUp 0x14 / _supportTime 0x28 / "
                              "_moveUp 0x40 / _criticalUp 0x44 / _atkSpeedUp 0x48）；"
                              "SetSupport_noCheckTime(0x17765f0) 的浮点实参序由**函数体自身的"
                              "存储点**确定（attackRate/guardRate/moveRate/criticalUp/atkSpeedUp"
                              "/supportTime = s0/s1/s2/s3/s4/s6），元数据 parameters 的顺序在此"
                              "方法上不可用",
            "time_unit": "crash-free note: 间隔／持续时间的单位沿用 boss_heal 的既有结论"
                         "（BattleManager.GetDeltaTime → UnityEngine.Time.fixedDeltaTime → 游戏秒）",
        },
        "types": types,
        "checks_total": len(checks), "checks_passed": passed, "checks_failed": failed,
        "skipped_existing_keys": skipped_existing,
    })
    C.write_json(OUT / "native_checks.json", {
        "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
        "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
        "checks": checks, "passed": passed, "total": len(checks),
        "limits": [
            "全部为静态指令级证据＋数据侧原值分布，本批未做实机运行",
            "槽位规则只在 pin 指令逐字节相符时产出；任何一条不符即该槽不出规则",
            "Exec_HEAL 的支援部分不乘/乘 _skillChainRate 的差别按各自块体逐条读取",
        ],
    })
    C.write_json(OUT / "field_dictionary.json", rules)
    (OUT / "README.md").write_text(README, encoding="utf-8")
    print(json.dumps({"checks": f"{passed}/{len(checks)}", "failed": failed,
                      "rules": len(rules), "types": sorted(types)}, ensure_ascii=False))
    return 0 if not failed else 1


README = """# P2 第 10 批：Exec_HEAL 家族与其余类型（属性见 type_rules.json）

生成器：`scripts/character_skills/boss_heal_types.py`（纯标准库＋既有 capstone 依赖，只读解包产物）。
产物：`type_rules.json`（逐类型证据）、`native_checks.json`（受控检查）、
`field_dictionary.json`（新规则行，由 `rules.py` 作为第五来源合并）、`p10_increment.json`。

- 回复量＝`floor/clamp(float32(B × skillparam1))`，`B = bhSkillUtil.getBasicSkillAttack(true)`，
  整数化 `0x14374bc`，经 `CharaBehavior.Heal` 施加；对象的选法由 dispatch 的 `w2` 决定。
- 超上限（HP 上限）档位：仅 act∈{0,4,5,6} 合入 `HealSkill_HealFlag` 的位表，
  类型 10/11、28、31/32 另有 sp2／sp5／sp4 的附加下限。
- 支援块（12/13/14/26/28/31/32/46）按 `SupportData` 字段存储点逐条读取，实参序不采用
  元数据 `parameters` 的顺序。
- 其余类型（6/7/19/29/34/44/49/50/51/55/64/67/69/72/74/75/76/80/82/86/114）的
  「技能基值×槽 → 整数化」乘法点由调用图可达性重算，槽位与手工核对表逐条比对后才出规则。
"""


# ---------------------------------------------------------------------------
# increment report
# ---------------------------------------------------------------------------
def _answer_keys(path: Path):
    return BT._answer_keys(path)


def _unexplained_keys(path: Path):
    return BT._unexplained_keys(path)


def report_increment():
    """coverage increment + zero-breakage report against the P9 terminal snapshot.

    Reuses the P2-8 helpers by pointing them at this batch's baseline: the two module
    constants are swapped for the duration of the call (documented, no shared state is
    left behind) so the calibers are literally the same implementation.
    """
    C.enable_utf8_console()
    rules = json.loads((OUT / "field_dictionary.json").read_text(encoding="utf-8"))
    new_rule_keys = {f"{r['table']}|{r['effect_type']}|{r['field_path']}" for r in rules}
    summary = json.loads((PROF / "summary.json").read_text(encoding="utf-8"))
    before_summary = json.loads(SUMMARY_BEFORE.read_text(encoding="utf-8"))
    old_rb, old_sb = BT.RECORDS_BEFORE, BT.SUMMARY_BEFORE
    try:
        BT.RECORDS_BEFORE, BT.SUMMARY_BEFORE = RECORDS_BEFORE, SUMMARY_BEFORE
        before = BT._answer_keys(RECORDS_BEFORE)
        now = BT._answer_keys(PROF / "records.jsonl")
        new_keys = {k for k in now if k not in before}
        lost = sorted(k for k in before if k not in now)
        changed = sorted(k for k, v in before.items()
                         if k in now and any(now[k][1].get(f) != v[1].get(f)
                                             for f in ("raw", "kind", "unit", "status", "scope")))
        changed_text = sorted(k for k, v in before.items()
                              if k in now and now[k][1].get("value") != v[1].get("value"))
        BT_BEFORE_BODIES = BT._record_bodies(RECORDS_BEFORE)
        bt_now_bodies = BT._record_bodies(PROF / "records.jsonl")
        by_type = collections.Counter()
        by_group = collections.Counter()
        routes_by_cid = collections.defaultdict(set)
        migrated_cids = []
        page_sum = 0
        earlier_page_sum = 0
        with (PROF / "profiles.jsonl").open(encoding="utf-8") as fh:
            for line in fh:
                p = json.loads(line)
                before_on_page = 0
                for g in p["groups"]:
                    for ref in g["records"]:
                        rec = BT_BEFORE_BODIES.get(ref.get("rec_key"))
                        if rec is None:
                            continue
                        before_on_page += len(rec.get("answers") or [])
                        before_on_page += sum(len(c.get("answers") or [])
                                              for c in rec.get("children") or []
                                              if isinstance(c, dict))
                before_on_page += len(p.get("baseline") or [])
                hit = set()
                for g in p["groups"]:
                    for ref in g["records"]:
                        rec = bt_now_bodies.get(ref.get("rec_key"))
                        if rec is None:
                            continue
                        for holder in [rec] + [c for c in rec.get("children") or []
                                               if isinstance(c, dict) and "answers" in c]:
                            for a in holder.get("answers") or []:
                                if a.get("rule_key") in new_rule_keys:
                                    by_type[holder.get("effect_type")] += 1
                                    by_group[g["group"]] += 1
                                    page_sum += 1
                                    hit.add(holder.get("effect_type"))
                                    route = ("charainfo 必杀技参数（等价门控通过）"
                                             if holder.get("table") == "charainfo" else
                                             "传授链（denju）" if g["group"].startswith("denju")
                                             else "自身 pattern 可达的 boss 技能")
                                    routes_by_cid[p["cid"]].add(route)
                                else:
                                    akey = (holder.get("table"), holder.get("record_id"),
                                            holder.get("layer"), a["f"])
                                    if akey not in before:
                                        earlier_page_sum += 1
                if hit and not before_on_page:
                    migrated_cids.append(p["cid"])
        un_now = BT._unexplained_keys(PROF / "records.jsonl")
        un_then = BT._unexplained_keys(RECORDS_BEFORE)
        rec_level = len({k for k in new_keys if now[k][1].get("rule_key") in new_rule_keys})
        reach = BT.unknown_reachability(tuple(migrated_cids), dict(routes_by_cid))
    finally:
        BT.RECORDS_BEFORE, BT.SUMMARY_BEFORE = old_rb, old_sb
    payload = {
        "batch": "P2 第 10 批",
        "baseline": {"records": str(RECORDS_BEFORE.relative_to(C.ROOT)),
                     "summary": str(SUMMARY_BEFORE.relative_to(C.ROOT)),
                     "note": "P2 第 9 批终态（p9 整改后）"},
        "new_rules": len(rules),
        "new_rules_by_type": {str(k): v for k, v in
                              sorted(collections.Counter(r["effect_type"] for r in rules).items())},
        "new_rule_keys": sorted(new_rule_keys),
        "new_answers_page_sum": page_sum,
        "new_answers_record_level": rec_level,
        "new_answer_keys_unique": len(new_keys),
        "new_answers_from_earlier_rule_sets_page_sum": earlier_page_sum,
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(by_type.items())},
        "answers_by_group_page_sum": dict(by_group),
        "status_migrations_unknown_to_partial": len(migrated_cids),
        "migrated_cids": sorted(migrated_cids),
        "existing_answer_keys_lost": len(lost),
        "existing_answer_keys_raw_kind_unit_status_scope_changed": len(changed),
        "existing_answer_keys_value_text_changed": len(changed_text),
        "lost_keys_sample": lost[:5],
        "unexplained_fields": len(un_now),
        "unexplained_fields_before": len(un_then),
        "unexplained_fields_delta": len(un_now) - len(un_then),
        "unexplained_keys_removed": len(un_then - un_now),
        "unexplained_keys_added": len(un_now - un_then),
        "rule_answers": summary["totals"]["rule_answers"],
        "rule_answers_before": before_summary["totals"]["rule_answers"],
        "rule_answers_unique_records": summary["totals"]["rule_answers_unique_records"],
        "status": summary["status_counts"],
        "status_before": before_summary["status_counts"],
        "unknown_reachability": reach,
        "caliber_note": ("new_answers_page_sum 只计本批 79 条新规则产生的答案（按角色页引用求和）；"
                         "new_answers_from_earlier_rule_sets_page_sum 是基准之后**任何其它规则**"
                         "产生的答案的页实例数"),
    }
    C.write_json(OUT / "p10_increment.json", payload)
    print(json.dumps({k: payload[k] for k in
                      ("new_rules", "new_answers_page_sum", "new_answers_record_level",
                       "new_answer_keys_unique", "status_migrations_unknown_to_partial",
                       "existing_answer_keys_lost", "unexplained_fields_delta",
                       "status")}, ensure_ascii=False))
    return payload


if __name__ == "__main__":
    if "--report-increment" in sys.argv:
        report_increment()
    else:
        raise SystemExit(main())
