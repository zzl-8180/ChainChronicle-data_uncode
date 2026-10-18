"""P2 batch 8: attack-family boss skill types -- where the damage base comes from.

The batch answers one question the P2-1 batch had to leave open: for the
``bhSkill.Exec_ATTACK_*`` family (types 0/1/2/3/4/5/22/47/110) the handler reads
``skillparamN``, but **which value is the damage base** was unknown, so no numeric
rule could be given (``charainfo_types/head_types.json`` said "the global skill
table is not located").

Result (all recomputed from the recovered native image, never hard-coded from a
previous batch's note):

* the damage input of every type in the family is
  ``floor/clamp(float32(B × skillparamN))`` with **B = bhSkillUtil.getBasicSkillAttack(true)**
  (``0x1182ed8``, called with ``w1=1``) -- the *same* shared function the type105 /
  type112 lines already confirmed.  The integerisation helper is ``0x14374bc``.
* the "global skill table" (``[[0x29e9000+0x6e8]]+0xb8``) that the P2-1 note called a
  candidate damage table supplies the attack **origin offset** (a three-float vector
  scaled by ``skillparam4``) consumed by ``BattleManager.FindNearPosition``; it is
  **not** a damage table.
* ``skillparam1`` is therefore the damage coefficient (``atkRate``) for the whole
  family except type 47 (``skillparam0``) -- and for type 47 exactly which slot is
  the coefficient is decided by the multiply site.

The slot facts are re-derived per type:

* **atkRate** (damage coefficient): found by walking from the type's handler to the
  function that calls ``getBasicSkillAttack`` and reading the ``fmul s0, s0, sR``
  operand register, resolved back to a ``_skillparamN`` load through the call graph
  (a small symbolic interpreter, see :class:`NativeView` / :func:`resolve_slot`).
* **pushPow** (push-power input): the register the victim ``CharaBehavior.Attack``
  receives as its ``pushPower`` parameter, or -- for the bullet types -- the value
  that ends up in ``Bullet._pushPower`` / ``SpreadBullet._pushPower`` (field offset
  ``0x60`` of the game's own field table).
* the remaining slots are pinned to an explicit RVA whose instruction the script
  re-reads and checks byte for byte (``extras`` in :data:`SPEC`); a mismatch emits
  no rule for that slot.

Outputs (``output/character_skills/boss_attack_types/``):

* ``type_rules.json`` -- per type: handler/case RVA, the recomputed chain, every slot
  with its evidence RVA, the unresolved slots with the exact break point, the raw
  value distribution of each slot and the reference-lead conflicts.
* ``native_checks.json`` -- the controlled checks (all of them must pass).
* ``field_dictionary.json`` -- the new rule rows, merged by ``rules.py`` as a fourth
  rule source (only keys the earlier dictionaries do not already define).
* ``p8_increment.json`` -- three-caliber increment + zero-breakage report
  (``--report-increment``).
* ``README.md``.

No game value is imported from outside the repository; no new dependency; the script
only writes its own output directory and ``work/p8_*``.
"""
from __future__ import annotations

import bisect
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

OUT = ROOT / "output" / "character_skills" / "boss_attack_types"
PROF = ROOT / "output" / "character_skills" / "profiles"
GAPS = ROOT / "output" / "character_skills" / "gaps"
HEAD_TYPES = ROOT / "output" / "character_skills" / "charainfo_types" / "head_types.json"
RECORDS_BEFORE = ROOT / "work" / "p8_records_before.jsonl"
SUMMARY_BEFORE = ROOT / "work" / "p8_summary_before.json"

DIS = CT.DIS
PARAM_OFFS = {0x2C + 4 * i: i for i in range(10)}
TRUNC_RVA = 0x14374BC          # int32 floor/clamp helper (already confirmed by type105/112)
GET_BASIC_RVA = 0x1182ED8      # bhSkillUtil.getBasicSkillAttack
ATTACK_RVAS = {0x153AFC4, 0x153B0DC, 0x153B120, 0x153B234, 0x153B090, 0x153B278}
# the two float tokens seen in the recovered metadata: 15563 is used for atkRate /
# pushPow / pushPower / fLength / attack_radius / len / bomb_radius*, 15580 for height.
FLOAT_TOKENS = {15563, 15580}
VECTOR_TOKENS = {17527: 3, 17510: 2}   # pos (Vector3) / vel (x,y + const z)
BULLET_PUSH_FIELD = 0x60               # Bullet._pushPower / SpreadBullet._pushPower
GLOBAL_OFFSET_TABLE = "[[0x29e9000+0x6e8]]+0xb8"

# ---------------------------------------------------------------------------
# roles: what a slot means, and the rule row + answer text it produces
# ---------------------------------------------------------------------------
STATUS = "已确认（原生静态代码局部语义；本批新定位）"
CONDITION = ("以该必杀技经 initialize_ExAttack 进入对应 type 的 bhSkill.Exec_* 处理器为前提；"
             "charainfo 侧还需记录级等价门控通过（P2 第 1 批）")
LIMITS = ("给出的是处理器收到的伤害输入／参数，不是最终扣血；B 的运行时因子（Chain／状态／能力）"
          "不在此展开；不含等级成长")
ATKRATE_LIMITS = ("给出的是处理器收到的伤害输入，不是最终扣血；B=getBasicSkillAttack(true) 的运行时"
                  "因子（Chain／状态／能力）不在此展开；面板 ATK 到 _skillAtk 的换算仍未闭合")


def role_row(kind: str, slot: int):
    """(meaning_zh, unit, rule/conversion, limits) for one role."""
    p = f"skillparam{slot}"
    table = {
        "atk_rate": (
            "单次伤害的技能基值倍率",
            "倍（相对 B）",
            f"伤害输入 = floor/clamp(float32(B × {p}))；B = bhSkillUtil.getBasicSkillAttack(true)（0x1182ed8，w1=1；已含 Chain），"
            "整数化＝0x14374bc（frintm/fcvtms 向下取整，再夹到 int32 范围；+inf 时取 int32 最小值）",
            ATKRATE_LIMITS),
        "atk_rate_second": (
            "第二段伤害的技能基值倍率",
            "倍（相对 B）",
            f"第二段伤害输入 = floor/clamp(float32(B × {p}))，仅当 {p} 超过全局表的阈值项时取代第一段；"
            "B = bhSkillUtil.getBasicSkillAttack(true)（0x1182ed8）",
            ATKRATE_LIMITS + "；阈值项的来源表只读到一个比较值，未展开"),
        "push_pow": (
            "推力输入（pushPower）",
            "推力输入（无量纲输入，不是倍率）",
            f"{p} 作为 CharaBehavior.Attack 的 pushPower 原样传入；正推力在 CalcAttackedPost 里请求受击状态 DamageL(10)",
            "推力不是伤害倍率，也不是位移距离；受击方免推位与锁定条件在既有 type112 证据内"),
        "push_pow_chain_bullet": (
            "推力输入（pushPower，经子弹中转且乘技能链系数）",
            "推力输入（无量纲输入，不是倍率）",
            f"{p} 先乘 _skillChainRate（bhSkillUtil+0x18）再经 Bullet.Initialize 存入 Bullet._pushPower（0x60）；"
            "子弹命中时该字段作为 CharaBehavior.Attack 的 pushPower 传入（0x153b120）",
            "「原样传入 CharaBehavior.Attack」不成立：中间乘了 _skillChainRate 且经 Bullet._pushPower 中转；"
            "推力不是伤害倍率，也不是位移距离；受击方免推位与锁定条件在既有 type112 证据内"),
        "push_pow_spread_bullet": (
            "推力输入（pushPower，经扩散子弹中转）",
            "推力输入（无量纲输入，不是倍率）",
            f"{p} 经 SpreadBullet._pushPower（0x60）中转（本类型不乘 _skillChainRate）；"
            "引爆时该字段作为 CharaBehavior.Attack 的 pushPower 传入",
            "经子弹对象中转而不是直接传给攻击调用；推力不是伤害倍率，也不是位移距离"),
        "area_len": (
            "范围搜索长度",
            "位置单位长度",
            f"{p} 作为 BattleManager.FindNearPosition 的 fLength（搜索半径）",
            "位置单位的作用距离；不换算为格数或像素"),
        "origin_scale": (
            "攻击起点偏移的缩放系数",
            "缩放系数",
            f"攻击起点三维偏移 = {GLOBAL_OFFSET_TABLE} 的固定偏移 × {p}（再叠加施法者位置）",
            "该全局表只提供起点偏移，不是伤害基准值；表本身的业务名未定位"),
        "front_reach": (
            "前方到达距离的延长量",
            "位置单位长度",
            f"前方判定上限 = 目标体半径项 + {p}（沿朝向的到达距离）",
            "与目标半径项相加后比较；半径项由 BattleParam.get_bodyRadius/get_statusBodyRadius 运行时给出"),
        "front_width": (
            "前方横向判定宽度输入",
            "位置单位长度（原值为宽度的两倍）",
            f"横向判定半宽 = {p} × 0.5 + 目标体半径项（即原值 {p} 表示宽度）",
            "只影响命中判定，不影响伤害数值"),
        "interval": (
            "重复攻击的间隔",
            "游戏秒",
            f"{p} 作为重复攻击定时器的重置值；计时器每帧按 BattleManager.GetDeltaTime 递减，≤0 时触发一次并重置为 {p}",
            "一次 update 至多触发一次；无敌/不在场时是否累积按对应类型的既有证据分别处理"),
        "count_cap": (
            "重复攻击的次数上限",
            "次（每目标）",
            f"{p} 向零截断后作为该次攻击的尝试上限（含等于；范围外也消耗预算）",
            "是尝试次数上限，不保证命中次数；+inf 会截成 int32 最小值（该边界不产出实际数值）"),
        "count_cap_repeat1": (
            "重复攻击的追加回数（总攻击次数 = 该值 + 1）",
            "次（每目标，追加回数）",
            f"{p} 向零截断后作为追加回数：循环条件为 _numCounter > trunc({p}) 时结束，"
            f"而首次攻击在 _numCounter == 0 时就已经发出（0x1184994 自增在后），"
            f"因此**总攻击次数 = trunc({p}) + 1**（含等于；范围外也消耗预算）",
            "是攻击次数（不是命中次数）；同名数值在 type105／110 上是总次数（无 +1），"
            "两个类型的循环结构不同，不能互套；+inf 会截成 int32 最小值（该边界不产出实际数值）"),
        "count_cap_area_repeat": (
            "每目标重复攻击的次数上限",
            "次（每目标）",
            f"{p} 向零截断后作为每目标的尝试上限（含等于）：计时到期即消耗一次预算并攻击；"
            "目标在清单建立后不再做范围重判",
            "是尝试次数上限，不保证命中次数；措辞不含 type105 的「范围外也消耗预算」结构（该类型无范围重判）；"
            "+inf 会截成 int32 最小值（该边界不产出实际数值）"),
        "move_offset": (
            "突进位移",
            "位置单位长度（原值可为负）",
            f"{p} 作为突进的位置偏移（按 _type 决定是否取负后加到施法者方向上）",
            "是位置偏移，不是速度或伤害倍率"),
        "bomb_type": (
            "爆炸类型码",
            "枚举（int 向零截断）",
            f"{p} 向零截断后写入 SpreadBullet.m_BombType（0xf8）",
            "枚举含义表未定位；只给码值"),
        "bomb_radius0": (
            "爆炸半径 0",
            "位置单位长度",
            f"{p} 写入 SpreadBullet.m_BombRadius0（0xfc）",
            "位置单位；爆炸伤害是否按半径衰减不在本批范围"),
        "bomb_radius1": (
            "爆炸半径 1",
            "位置单位长度",
            f"{p} 写入 SpreadBullet.m_BombRadius1（0x100）",
            "位置单位；爆炸伤害是否按半径衰减不在本批范围"),
        "bullet_radius_h": (
            "子弹横向半径输入",
            "位置单位长度（经分段映射）",
            f"子弹横向半径 _radius_h = 0.1 + max(0, {p} − 1.5) × 0.5（即 {p} ≤ 1.5 时为 0.1）",
            "只影响子弹碰撞横向半径；映射常量为 0x2015000+0xcf4=0.1"),
    }
    return table[kind]


# ---------------------------------------------------------------------------
# per-type spec
# ---------------------------------------------------------------------------
# A slot's *rule text* may differ from the shared role text even when the role (and the
# numeric conversion) is the same -- the P2-9 batch's p2b8 review fixes and the type1
# repeat-count caliber live here.  Keyed by (type, role kind) -> text kind.
ROLE_TEXT_OVERRIDE = {
    (5, "push_pow"): "push_pow_chain_bullet",       # p2b8 P3-1: sp3 × _skillChainRate -> Bullet._pushPower
    (47, "push_pow"): "push_pow_spread_bullet",     # p2b8 P3-1: 经 SpreadBullet._pushPower 中转
    (110, "count_cap"): "count_cap_area_repeat",    # p2b8 P3-3: 无「范围外也消耗预算」结构
    (1, "count_cap"): "count_cap_repeat1",          # P2-9: 总次数 = trunc(sp3) + 1
}
# ``extras`` entries are *pinned*: the script re-reads every listed RVA and requires
# the exact instruction, plus optionally an anchor check against the callee's own
# metadata parameter names (``anchor``).
SPEC = {
    0: {"extras": []},
    1: {"extras": [
        {"slot": 2, "kind": "interval", "load_rva": 0x118497C,
         "load": "ldr      w9, [x19, #0x34]",
         "peer_rva": 0x1184990, "peer": "str      w9, [x19, #0xc0]"},
        {"slot": 3, "kind": "count_cap", "load_rva": 0x1184920,
         "load": "ldr      s1, [x19, #0x38]",
         "peer_rva": 0x1184934, "peer": "fcvtzs   w8, s1"},
    ]},
    2: {"extras": [
        {"slot": 2, "kind": "move_offset", "load_rva": 0x1184B48,
         "load": "ldr      s0, [x19, #0x34]"},
    ]},
    3: {"extras": [
        {"slot": 2, "kind": "area_len", "load_rva": 0x1185F54,
         "load": "ldr      s3, [x21, #0x34]",
         "anchor": {"callee": 0x10BBD00, "reg": 3, "param": "fLength"}},
        {"slot": 4, "kind": "origin_scale", "load_rva": 0x1185E88,
         "load": "ldr      s0, [x21, #0x3c]"},
    ]},
    4: {"extras": []},
    5: {"extras": [
        {"slot": 4, "kind": "bullet_radius_h", "load_rva": 0x1186EB4,
         "load": "ldr      s2, [x21, #0x3c]"},
    ],
        "push": {"kind": "bullet_push", "call_rva": 0x1187068, "callee": 0x131046C,
                 "arg_reg": 2, "chain": [(0x13104AC, "mov      v9.16b, v2.16b"),
                                          (0x1310520, "mov      v2.16b, v9.16b"),
                                          (0x131059C, "mov      v8.16b, v2.16b"),
                                          (0x131082C, "str      s8, [x20, #0x60]")]}},
    22: {"extras": [
        {"slot": 2, "kind": "front_reach", "load_rva": 0x118A13C,
         "load": "ldr      s1, [x21, #0x34]"},
        {"slot": 3, "kind": "front_width", "load_rva": 0x118A150,
         "load": "ldr      s1, [x21, #0x38]"},
    ]},
    47: {"extras": [
        {"slot": 1, "kind": "bomb_type", "load_rva": 0x1190ADC,
         "load": "fcvtzs   w9, s13",
         "peer_rva": 0x155E48C, "peer": "str      w27, [x19, #0xf8]"},
        {"slot": 2, "kind": "bomb_radius0", "load_rva": 0x1190B04,
         "load": "mov      v3.16b, v9.16b",
         "peer_rva": 0x155E490, "peer": "stp      s12, s11, [x19, #0xfc]"},
        {"slot": 3, "kind": "bomb_radius1", "load_rva": 0x1190B08,
         "load": "mov      v4.16b, v10.16b",
         "peer_rva": 0x155E490, "peer": "stp      s12, s11, [x19, #0xfc]"},
        {"slot": 5, "kind": "atk_rate_second", "load_rva": 0x11908D4,
         "load": "ldr      s0, [x21, #0x40]",
         "peer_rva": 0x11908F8, "peer": "bl       #0x14374bc"},
    ],
        "push": {"kind": "bullet_push", "call_rva": 0x1190B28, "callee": 0x155E3B8,
                 "arg_reg": 2, "chain": [(0x155E3F8, "mov      v8.16b, v2.16b"),
                                          (0x155E5C8, "str      s8, [x19, #0x60]")],
                 # p2b9 review F3: type47 gets the same bullet-intermediary note type5
                 # carries, so the rendered answer does not read as a direct pass-through
                 "note": ("经 SpreadBullet._pushPower（0x60）中转（本类型不乘 _skillChainRate）；"
                          "引爆时作为 CharaBehavior.Attack 的 pushPower 传入")}},
    105: {"extras": [
        {"slot": 5, "kind": "interval", "load_rva": 0x118A67C,
         "load": "ldr      w8, [x20, #0x40]"},
    ]},
    110: {"extras": [
        {"slot": 2, "kind": "area_len", "load_rva": 0x1186414,
         "load": "ldr      s3, [x20, #0x34]",
         "anchor": {"callee": 0x10BBD00, "reg": 3, "param": "fLength"}},
        {"slot": 4, "kind": "origin_scale", "load_rva": 0x1186338,
         "load": "ldr      s0, [x20, #0x3c]"},
        {"slot": 5, "kind": "interval", "load_rva": 0x1186684,
         "load": "ldr      w8, [x20, #0x40]"},
        {"slot": 6, "kind": "count_cap", "load_rva": 0x11865C8,
         "load": "ldr      s0, [x20, #0x44]",
         "peer_rva": 0x11865D8, "peer": "fcvtzs   w8, s0"},
    ]},
}
# slots whose read site was located but whose role was *not* established this batch
UNRESOLVED_NOTES = {
    (0, 1): "w8=0 分支另一组偏移",           # placeholder replaced below
}
KNOWN_UNRESOLVED = {
    1: ["skillparam4：读到（0x1184978）后只用于 AttackNear_Common 的方向随机化条件，语义未确认"],
    22: [],
    105: ["skillparam7：读到（0x118a37c → 0x118a67c 同级）后只作为 CharaBehavior.Attack 的 bool 栈参数，未命名"],
    110: ["skillparam7：读到（0x11862fc）后仅与 0 比较，作为 CharaBehavior.Attack 的首个 bool 栈参数（hitEffect 位），未命名"],
    47: ["skillparam6：缓存 19 行中仅 1 行出现，读取点未定位"],
    5: ["skillparam2：本批未在 type5 处理器体内找到读取点（缓存 16 行均无该键）"],
    0: [],
    2: [],
    3: ["skillparam0：无读取点（缓存 234 行均无该键）"],
    4: [],
}

BULLET_FIELD_CLASS = {0x131046C: "Bullet", 0x131055C: "Bullet", 0x155E3B8: "SpreadBullet"}


# ---------------------------------------------------------------------------
# native access
# ---------------------------------------------------------------------------
class NativeView:
    def __init__(self, md, native):
        self.md = md
        self.n = native
        self.entries = sorted(set(p for p in native.pointers if p))
        self._method_by_rva = {}
        for i, row in enumerate(md.methods):
            try:
                rva = native.pointers[(row[6] & 0xffffff) - 1]
            except Exception:
                continue
            if rva:
                self._method_by_rva.setdefault(rva, i)
        self._callers = None
        self._insns = {}
        self._util_fields = {}
        for ti, row in enumerate(md.types):
            if md.string(row[0]) == "bhSkillUtil":
                for f in native.fields(ti):
                    self._util_fields[int(f["offset"], 16)] = f["name"]

    # -- basics ------------------------------------------------------------
    def bounds(self, rva):
        i = bisect.bisect_right(self.entries, rva) - 1
        lo = self.entries[i]
        hi = self.entries[i + 1] if i + 1 < len(self.entries) else len(self.n.raw)
        return lo, hi

    def method(self, rva):
        i = self._method_by_rva.get(rva)
        return self.md.method(i) if i is not None else None

    def name(self, rva):
        m = self.method(rva)
        return f"{m['declaring_type']}.{m['name']}" if m else None

    def insns(self, rva):
        if rva not in self._insns:
            lo, hi = self.bounds(rva)
            self._insns[rva] = list(DIS.disasm(self.n.raw[lo:hi], lo))
        return self._insns[rva]

    def words(self, rva, count=1):
        return [f"{i.address:08x}  {i.mnemonic:<8} {i.op_str}" for i in self.insns(rva)[:count]]

    def text_at(self, rva):
        for insn in self.insns(rva):
            if insn.address == rva:
                return f"{insn.mnemonic:<8} {insn.op_str}"
        return None

    def float_reg_names(self, rva, limit=8):
        m = self.method(rva)
        names = []
        if not m:
            return names
        for p in m["parameters"]:
            ti = p["type_index"]
            if ti in FLOAT_TOKENS:
                names.append(p["name"])
            elif ti in VECTOR_TOKENS:
                names.extend([p["name"]] * VECTOR_TOKENS[ti])
        return names[:limit]

    def util_field_name_of_insn(self, text):
        """``ldr sN, [xU, #off]`` -> the bhSkillUtil field name at that offset, if any."""
        if not text or not text.startswith("ldr") or "[" not in text:
            return None
        try:
            off = int(text.split("[", 1)[1].split("]", 1)[0].split(",")[1].strip()[1:], 0)
        except (IndexError, ValueError):
            return None
        if off not in self._util_fields:
            return None
        return self._util_fields[off]

    def reachable_from(self, rva, depth=4):
        """Forward closure of function entries reachable from ``rva`` (bl/b targets)."""
        out = {rva}
        frontier = [(rva, 0)]
        while frontier:
            f, d = frontier.pop()
            if d >= depth:
                continue
            for insn in self.insns(f):
                if insn.mnemonic in ("bl", "b") and insn.op_str.startswith("#"):
                    t = int(insn.op_str[1:], 0)
                    nm = self.name(t)
                    if not nm:
                        continue
                    lo, hi = self.bounds(t)
                    if t != lo or hi - lo > 0x8000 or t in out:
                        continue
                    out.add(t)
                    frontier.append((t, d + 1))
        return out

    def callers(self):
        if self._callers is None:
            out = collections.defaultdict(list)
            for a in self.entries:
                lo, hi = self.bounds(a)
                if hi - lo > 0x8000:
                    continue
                for insn in DIS.disasm(self.n.raw[lo:hi], lo):
                    if insn.mnemonic in ("bl", "b") and insn.op_str.startswith("#"):
                        t = int(insn.op_str[1:], 0)
                        out[t].append((a, insn.address))
            self._callers = out
        return self._callers


# --- symbolic interpretation of a function body -----------------------------
def _sreg(tok):
    return int(tok[1:]) if tok and tok[0] == "s" and tok[1:].isdigit() else None


def _mem(op):
    """('s8', base, offset) for 's8, [x21, #0x30]' style operands."""
    if "[" not in op:
        return None
    dest, _, rest = op.partition(",")
    inside = rest.split("[", 1)[1].split("]", 1)[0]
    parts = [p.strip() for p in inside.split(",")]
    base = parts[0]
    off = 0
    for p in parts[1:]:
        if p.startswith("#"):
            off = int(p[1:], 0)
    return dest.strip(), base, off


def interpret(view, rva, stop_addr=None):
    """Symbolic state of the float registers of the function at ``rva``.

    Symbols: ``("slot", param_offset)`` / ``("arg", k)`` / ``("zero",)`` / ``("unk",)``.
    ``s0..s7`` start as ``("arg", k)`` so a value can be followed back through the
    call graph by :func:`resolve_slot`.  ``sp`` stores are tracked as well (type105
    parks pushPower in the frame before the Attack call).

    ``mov vA.16b, vB.16b`` is a full 16-byte copy; the scalar code only ever reads the
    *low* lane of a vector register, and the low lane of ``vN`` is exactly ``sN``, so
    the copy is modelled as ``sA <- sB`` (the upper lanes have no scalar name).
    """
    s = {i: (("arg", i) if i < 8 else ("unk",)) for i in range(32)}
    stk = {}
    prod = {}
    util = None
    util_fixed = False
    for idx, insn in enumerate(view.insns(rva)):
        if stop_addr is not None and insn.address >= stop_addr:
            break
        op = insn.op_str
        mn = insn.mnemonic
        if not util_fixed:
            if mn == "mov" and op.endswith(", x0"):
                reg = op.split(",")[0].strip()
                if reg.startswith("x") and reg[1:].isdigit():
                    util = reg
                    util_fixed = True
        if mn in ("ldr", "ldrb", "ldrh", "ldrsw", "ldrsh"):
            parsed = _mem(op)
            if parsed:
                dest, base, off = parsed
                r = _sreg(dest)
                if r is not None:
                    if base == util and off in PARAM_OFFS:
                        s[r] = ("slot", off)
                    elif base == "sp" and off in stk:
                        s[r] = stk[off]
                    else:
                        s[r] = ("unk",)
                    prod[r] = insn.address
        elif mn == "ldp":
            dest, _, rest = op.partition(",")
            dest2 = rest.split(",", 1)[0].strip()
            parsed = _mem(op)
            if parsed:
                _d, base, off = parsed
                for d, o in ((dest.strip(), off), (dest2, off + 4)):
                    r = _sreg(d)
                    if r is not None:
                        if base == util and o in PARAM_OFFS:
                            s[r] = ("slot", o)
                        elif base == "sp" and o in stk:
                            s[r] = stk[o]
                        else:
                            s[r] = ("unk",)
                        prod[r] = insn.address
        elif mn == "mov":
            dest, _, src = op.partition(",")
            dest, src = dest.strip(), src.strip()
            if dest.startswith("v") and src.startswith("v"):
                try:
                    dq = int(dest[1:].split(".")[0])
                    sq = int(src[1:].split(".")[0])
                except ValueError:
                    continue
                if dq < 32:
                    s[dq] = s.get(sq, ("unk",)) if sq < 32 else ("unk",)
                    prod[dq] = insn.address
            else:
                r = _sreg(dest)
                if r is not None:
                    r2 = _sreg(src)
                    s[r] = s.get(r2, ("unk",)) if r2 is not None else (
                        ("zero",) if src == "wzr" else ("unk",))
                    prod[r] = insn.address
        elif mn == "fmov":
            dest, _, src = op.partition(",")
            dest, src = dest.strip(), src.strip()
            r = _sreg(dest)
            if r is not None:
                r2 = _sreg(src)
                if r2 is not None:
                    s[r] = s.get(r2, ("unk",))
                elif src == "wzr":
                    s[r] = ("zero",)
                else:
                    s[r] = ("unk",)
                prod[r] = insn.address
        elif mn == "str":
            parsed = _mem(op)
            if parsed:
                src, base, off = parsed
                r = _sreg(src)
                if r is not None and base == "sp":
                    stk[off] = s[r]
        elif mn in ("fmul", "fadd", "fsub", "fdiv", "fnmul", "fsqrt", "fcvtzs", "scvtf",
                    "fcvt", "fcsel", "fabs", "fneg", "fmin", "fmax", "fminnm", "fmaxnm"):
            dest = op.split(",")[0].strip()
            r = _sreg(dest)
            if r is not None:
                s[r] = ("unk",)
                prod[r] = insn.address
        elif mn == "bl":
            for i in range(4):
                s[i] = ("basic",) if (i == 0 and op.startswith("#")
                                      and int(op[1:], 0) == GET_BASIC_RVA) else ("unk",)
                prod[i] = insn.address
    return s, stk, util, prod


_MUL_OPS = {
    "fmul": (0, 1, 2), "fadd": (0, 1, 2), "fsub": (0, 1, 2), "fdiv": (0, 1, 2),
    "fnmul": (0, 1, 2), "fmin": (0, 1, 2), "fmax": (0, 1, 2),
    "fminnm": (0, 1, 2), "fmaxnm": (0, 1, 2),
}


def _operands(op):
    parts = [p.strip() for p in op.split(",")]
    return [_sreg(p) for p in parts]


def resolve_slot(view, func_rva, addr, reg, depth=0, path=None, allowed=None):
    """Follow float register ``reg`` at ``addr`` in ``func_rva`` back to a slot.

    Returns ``{"slot": param_offset, "path": [...], "note": str|None}`` or None.
    A value produced by one arithmetic step whose *other* operand is a slot is
    accepted with a note (type5/type47 push power is ``_skillChainRate × slot``).
    ``allowed`` restricts the upstream walk to the functions reachable from *this*
    type's handler, so a shared body called from several types cannot be resolved
    through another type's call site.
    """
    path = path or []
    if depth > 5:
        return None
    state, _stk, util, prod = interpret(view, func_rva, stop_addr=addr)
    sym = state.get(reg)
    if not sym:
        return None
    if sym[0] == "slot":
        return {"slot": sym[1], "path": path + [(hex(func_rva), hex(addr), f"s{reg}", "slot")],
                "note": None}
    if sym[0] == "zero":
        return {"slot": None, "zero": True,
                "path": path + [(hex(func_rva), hex(addr), f"s{reg}", "zero")], "note": None}
    if sym[0] == "arg":
        k = sym[1]
        for caller, call_addr in view.callers().get(func_rva, []):
            if allowed is not None and caller not in allowed:
                continue
            got = resolve_slot(view, caller, call_addr, k, depth + 1,
                               path + [(hex(func_rva), hex(addr), f"s{reg}", f"arg{k}")],
                               allowed)
            if got:
                return got
        return None
    # an arithmetic result: try its operands (bounded, one level of arithmetic)
    pa = prod.get(reg)
    if pa is not None:
        text = view.text_at(pa) or ""
        mn = text.split()[0] if text else ""
        if mn in _MUL_OPS:
            rest = text.split(None, 1)[1] if " " in text else ""
            ops = _operands(rest)
            for o in ops:
                if o is None or o == reg:
                    continue
                got = resolve_slot(view, func_rva, pa, o, depth + 1,
                                   path + [(hex(func_rva), hex(pa), f"s{reg}", f"{mn} s{o}")],
                                   allowed)
                if got and got.get("slot") is not None:
                    others = [x for x in ops if x is not None and x != reg]
                    oo = next((x for x in others if x != o), None)
                    src = ""
                    if oo is not None:
                        _ps, _sk, _ut, pp = interpret(view, func_rva, stop_addr=pa)
                        prod2 = pp.get(oo)
                        t2 = view.text_at(prod2) if prod2 else None
                        src = f"；另一操作数 s{oo} 由 `{t2}` 提供" if t2 else ""
                        fname = view.util_field_name_of_insn(t2)
                        if fname:
                            src += f"（bhSkillUtil.{fname}，运行时系数）"
                    got["note"] = f"{mn}（{text}）{src}"
                    return got
    return None


def resolve_call_arg(view, call_rva, reg, allowed=None):
    """Slot behind the float register ``reg`` at the call instruction ``call_rva``."""
    caller = view.bounds(call_rva)[0]
    return resolve_slot(view, caller, call_rva, reg, allowed=allowed)


def find_damage_function(view, util_rva):
    """BFS from the handler body to the first bhSkill function calling getBasicSkillAttack.

    Tail branches (``b``) are followed as well: the type1 handler reaches the shared
    attack body through a tail call, not through ``bl``.
    """
    frontier = [(util_rva, [util_rva])]
    seen = {util_rva}
    while frontier:
        f, path = frontier.pop(0)
        if any(i.mnemonic == "bl" and i.op_str == f"#0x{GET_BASIC_RVA:x}" for i in view.insns(f)):
            return f, path
        if len(path) > 3:
            continue
        for insn in view.insns(f):
            if insn.mnemonic in ("bl", "b") and insn.op_str.startswith("#"):
                t = int(insn.op_str[1:], 0)
                nm = view.name(t)
                if not nm or not (nm.startswith("bhSkillUtil.") or nm.startswith("bhSkill.")):
                    continue
                lo, hi = view.bounds(t)
                if t != lo or hi - lo > 0x4000 or t in seen:
                    continue
                seen.add(t)
                frontier.append((t, path + [t]))
    return None, None


def damage_pattern(view, f_rva):
    """(fmul_addr, operand_reg, trunc_addr, slot) for the damage multiplication."""
    insns = view.insns(f_rva)
    for i, insn in enumerate(insns):
        if insn.mnemonic == "bl" and insn.op_str == f"#0x{GET_BASIC_RVA:x}":
            for j in range(i + 1, min(i + 8, len(insns))):
                m = insns[j]
                if m.mnemonic == "fmul" and m.op_str.startswith("s0, s0, s"):
                    reg = _sreg(m.op_str.split(",")[-1].strip())
                    for k in range(j + 1, min(j + 5, len(insns))):
                        if insns[k].mnemonic == "bl" and insns[k].op_str == f"#0x{TRUNC_RVA:x}":
                            return {"fmul_rva": m.address, "fmul": f"{m.mnemonic} {m.op_str}",
                                    "reg": reg, "trunc_rva": insns[k].address}
    return None


def attack_call_site(view, *funcs):
    for f in funcs:
        if f is None:
            continue
        for insn in view.insns(f):
            if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
                t = int(insn.op_str[1:], 0)
                if t in ATTACK_RVAS:
                    return f, insn.address, t
    return None


def crosscheck_push_sentinel(types, checks):
    """Data-side cross-check: the 'almost no push' value 0.001 sits in the push slot.

    type112 ``param7`` was already confirmed as ``Attack.pushPower`` by the earlier
    boss line, and 86 of its 91 cache records carry exactly 0.001.  If the slot this
    batch resolves as the push input is the same role, it must concentrate the same
    sentinel value while the damage slot does not.
    """
    rows = C.cache_rows("bossskill")
    by_type = collections.defaultdict(list)
    for r in rows:
        by_type[r.get("skillid0")].append(r)
    detail = {}
    ok = True
    for t in sorted(types):
        push = (types[t]["slots"].get("push_pow") or {}).get("slot")
        atk = (types[t]["slots"].get("atk_rate") or {}).get("slot")
        if push is None or atk is None:
            continue
        rs = by_type.get(t, [])
        push001 = sum(1 for r in rs if r.get(f"skillparam{push}") == 0.001)
        atk001 = sum(1 for r in rs if r.get(f"skillparam{atk}") == 0.001)
        detail[str(t)] = {"push_slot": f"skillparam{push}", "push_0.001": push001,
                          "damage_slot": f"skillparam{atk}", "damage_0.001": atk001,
                          "records": len(rs)}
        if push001 == 0:
            ok = False
        if atk001:
            ok = False
    ok_atk = all(v["damage_0.001"] == 0 for v in detail.values())
    hits = [v for v in detail.values() if v["push_0.001"] > 0]
    total = sum(v["push_0.001"] for v in detail.values())
    checks.append({"name": "push_slot_carries_the_0.001_sentinel_of_the_type112_line",
                   "ok": bool(detail) and ok_atk and len(hits) >= 5 and total >= 200,
                   "detail": json.dumps({
                       "per_type": detail,
                       "types_with_sentinel": len(hits),
                       "records_with_sentinel_in_a_push_slot": total,
                       "records_with_sentinel_in_a_damage_slot": 0 if ok_atk else ">0",
                       "note": ("0.001 是既有 type112 param7（=Attack.pushPower）在 86/91 条上出现的"
                                "「几乎不推」值；本批独立解出的推力槽复现同一分布，伤害槽上没有该值。"
                                "type0 的 9 条记录不含 0.001，故只要求多数类型命中")},
                       ensure_ascii=False)})


# ---------------------------------------------------------------------------
# controlled execution of the game's own bytes (Unicorn)
# ---------------------------------------------------------------------------
def _emulate_image(view):
    from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
    base = 0x50000000
    uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    size = (len(view.n.raw) + 0xFFFF) & ~0xFFFF
    uc.mem_map(base, size)
    uc.mem_write(base, view.n.raw)
    scratch = base + size
    uc.mem_map(scratch, 0x1000)
    return uc, base, scratch


def _write_f(uc, reg, value):
    uc.reg_write(reg, int.from_bytes(struct.pack("<f", float(value)), "little"))


def _read_f(uc, reg):
    return struct.unpack("<f", int(uc.reg_read(reg)).to_bytes(4, "little"))[0]


def emulate_multiply(view, fmul_rva, b, coef, reg):
    """Execute the handler's own ``fmul s0, s0, sReg`` byte and read the result."""
    from unicorn.arm64_const import UC_ARM64_REG_S0
    uc, base, _scratch = _emulate_image(view)
    _write_f(uc, UC_ARM64_REG_S0, b)
    _write_f(uc, UC_ARM64_REG_S0 + reg, coef)
    uc.emu_start(base + fmul_rva, 0, count=1)
    return _read_f(uc, UC_ARM64_REG_S0)


def emulate_integerisation(view, value):
    """Execute ``0x14374bc`` (floor + int32 clamp) on the recovered bytes."""
    from unicorn import UC_HOOK_CODE
    from unicorn.arm64_const import UC_ARM64_REG_S0, UC_ARM64_REG_SP, UC_ARM64_REG_W0
    uc, base, scratch = _emulate_image(view)
    # take the already-initialised path: the class-init flag is pre-set and the
    # dereferenced receiver reports a non-zero state, so no ``bl`` into the runtime
    # metadata helper is taken
    uc.mem_write(base + 0x2BD2000 + 0x4ED, b"\x01")
    uc.mem_write(base + 0x29BA000 + 0xB78, scratch.to_bytes(8, "little"))
    uc.mem_write(scratch, (scratch + 0x100).to_bytes(8, "little"))   # dereferenced receiver
    uc.mem_write(scratch + 0x100 + 0xE0, b"\x01\x00\x00\x00")        # non-zero state
    uc.reg_write(UC_ARM64_REG_SP, scratch + 0x800)      # the prologue pushes onto the stack
    _write_f(uc, UC_ARM64_REG_S0, value)
    stopped = {"ret": None}

    def hook(u, addr, size, data):
        if u.mem_read(addr, 4) == b"\xc0\x03\x5f\xd6":      # ret
            stopped["ret"] = addr
            u.emu_stop()

    h = uc.hook_add(UC_HOOK_CODE, hook)
    uc.emu_start(base + TRUNC_RVA, 0, count=64)
    uc.hook_del(h)
    w = uc.reg_read(UC_ARM64_REG_W0) & 0xFFFFFFFF
    return w - (1 << 32) if w >= (1 << 31) else w


def emulation_checks(view, types):
    checks = []

    def add(name, ok, **kw):
        checks.append({"name": name, "ok": bool(ok), **kw})

    add("integerisation_is_floor_not_truncation",
        view.text_at(0x1437508) == "frintm   s0, s8"
        and view.text_at(0x1437510) == "fcvtms   x8, s8",
        detail=(f"{hex(0x1437508)}: {view.text_at(0x1437508)}；{hex(0x1437510)}: "
                f"{view.text_at(0x1437510)}（frintm/fcvtms 是向下取整；负值处与向零截断不同）"))
    samples = [(12.7, 12), (12.0, 12), (-0.5, -1), (-1.5, -2), (0.0, 0),
               (3.0e9, 0x7FFFFFFF), (float("inf"), -0x80000000)]
    got = []
    for v, want in samples:
        try:
            r = emulate_integerisation(view, v)
        except Exception as exc:                                      # pragma: no cover
            r = f"error:{exc}"
        got.append({"value": v, "expected": want, "got": r})
    add("integerisation_emulated_on_the_game_bytes",
        all(g["got"] == g["expected"] for g in got),
        detail=json.dumps(got, ensure_ascii=False))

    # the damage multiplication itself, on each type's own instruction bytes
    mul = []
    for t in sorted(types):
        rec = types[t]["slots"].get("atk_rate") or {}
        fmul_rva = rec.get("fmul_rva")
        if not fmul_rva:
            continue
        reg = int(rec["fmul"].split(",")[-1].strip()[1:])
        b, coef = 7.5, 2.4
        try:
            got_v = emulate_multiply(view, int(fmul_rva, 16), b, coef, reg)
        except Exception as exc:                                      # pragma: no cover
            got_v = f"error:{exc}"
        want = struct.unpack("<f", struct.pack("<f", b * coef))[0]
        mul.append({"type": t, "fmul_rva": fmul_rva, "reg": reg,
                    "expected": want, "got": got_v,
                    "ok": abs(got_v - want) < 1e-6 if isinstance(got_v, float) else False})
        types[t]["slots"]["atk_rate"]["emulated_fmul"] = {
            "input_B": b, "input_coefficient": coef, "expected": want, "got": got_v}
    add("damage_multiplication_emulated_per_type", bool(mul) and all(m["ok"] for m in mul),
        detail=json.dumps(mul, ensure_ascii=False))
    return checks
def analyze(view):
    index = {e["type"]: e for e in CT.build_index(view.n)}
    checks = []
    types = {}

    def add(name, ok, **kw):
        checks.append({"name": name, "ok": bool(ok), **kw})
        return bool(ok)

    # ---- anchors that the whole family rests on -------------------------
    md = view.md
    add("simple_database_number_placeholder", True, note="replaced below")
    checks.pop()

    # the metadata names the damage leaf's coefficient parameter `atkRate` and the
    # push-power parameter `pushPow`; the Attack overloads carry exactly one float
    # (pushPower).  Those names are the anchor for the slot roles.
    leaf_names = {}
    for label, rva in (("AttackList_Common", 0x1185FE4), ("AttackNear_Common", 0x11846D8),
                       ("ShootBullet_Common", 0x1186EF4)):
        leaf_names[label] = view.float_reg_names(rva)
    add("callee_metadata_names_atkRate_pushPow",
        leaf_names["AttackList_Common"][:2] == ["atkRate", "pushPow"]
        and leaf_names["AttackNear_Common"][:3] == ["attack_radius", "atkRate", "pushPow"],
        detail=json.dumps(leaf_names, ensure_ascii=False))
    attack_float_names = {hex(r): view.float_reg_names(r) for r in sorted(ATTACK_RVAS)}
    add("chara_attack_has_exactly_one_float_pushPower",
        all(v == ["pushPower"] for v in attack_float_names.values()),
        detail=json.dumps(attack_float_names, ensure_ascii=False))
    add("push_power_field_is_0x60_on_Bullet_and_SpreadBullet",
        all(f["offset"] == hex(BULLET_PUSH_FIELD) and f["name"] == "_pushPower"
            for ti, row in enumerate(md.types)
            if md.string(row[0]) in ("Bullet", "SpreadBullet")
            for f in view.n.fields(ti) if f["offset"] == hex(BULLET_PUSH_FIELD)),
        detail="Bullet/SpreadBullet 的 0x60 字段名为 _pushPower")
    add("global_offset_table_is_not_a_damage_table",
        view.text_at(0x1185E94) == "ldp      s1, s2, [x8, #0x3c]"
        and view.text_at(0x1185E98) == "ldr      s3, [x8, #0x44]"
        and view.text_at(0x1185F58) == "fadd     s0, s10, s0",
        detail=(f"{hex(0x1185E94)}: {view.text_at(0x1185E94)}；"
                f"{hex(0x1185F58)}: {view.text_at(0x1185F58)}（表值被加到一个位置上）"))

    for t in sorted(SPEC):
        entry = index[t]
        handler_rva = int(entry["handler_rva"], 16)
        util_name = view.name(handler_rva)
        # the dispatch case body may be a thin bhSkill.Exec_* wrapper over the real
        # bhSkillUtil.Exec_* body; when the index already points at a bhSkillUtil
        # method (types 5/23/33/47/51/52/103/112) that body *is* the util body.
        util_rva = None
        if util_name and util_name.startswith("bhSkillUtil."):
            util_rva = handler_rva
        else:
            for insn in view.insns(handler_rva):
                if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
                    cand = int(insn.op_str[1:], 0)
                    nm = view.name(cand) or ""
                    if nm.startswith("bhSkillUtil."):
                        util_rva = cand
                        break
        info = {"type": t, "case_rva": entry["case_rva"], "handler": util_name,
                "handler_rva": hex(handler_rva), "util_body": view.name(util_rva),
                "util_body_rva": hex(util_rva) if util_rva else None,
                "slots": {}, "unresolved": KNOWN_UNRESOLVED.get(t, []), "checks": []}

        def tadd(name, ok, **kw):
            add(f"t{t}.{name}", ok, **kw)
            info["checks"].append({"name": name, "ok": bool(ok), **kw})
            return bool(ok)

        tadd("handler_leads_to_a_bhSkillUtil_body", util_rva is not None)
        # the upstream walk may only cross call sites reachable from *this* type's
        # handler: the shared bodies are called from many types (type1 and type0 both
        # reach AttackNear_Common), so an unrestricted walk would attribute another
        # type's slot.
        allowed = view.reachable_from(handler_rva) | ({util_rva} if util_rva else set())

        # ---- atkRate ------------------------------------------------------
        dmg_rva, chain = find_damage_function(view, util_rva)
        tadd("damage_function_found", dmg_rva is not None,
             chain=[hex(x) for x in (chain or [])])
        info["damage_function"] = {"name": view.name(dmg_rva) if dmg_rva else None,
                                   "rva": hex(dmg_rva) if dmg_rva else None,
                                   "chain": [hex(x) for x in (chain or [])]}
        pat = damage_pattern(view, dmg_rva) if dmg_rva else None
        tadd("damage_pattern_getBasicSkillAttack_times_slot_then_truncate",
             pat is not None,
             detail=(f"{hex(pat['fmul_rva'])}: {pat['fmul']}；{hex(pat['trunc_rva'])}: 整数化"
                     if pat else None))
        atk_slot = None
        if pat:
            got = resolve_slot(view, dmg_rva, pat["fmul_rva"], pat["reg"], allowed=allowed)
            atk_slot = PARAM_OFFS.get(got["slot"]) if got and got["slot"] in PARAM_OFFS else None
            info["slots"]["atk_rate"] = {
                "slot": atk_slot, "fmul_rva": hex(pat["fmul_rva"]), "fmul": pat["fmul"],
                "trunc_rva": hex(pat["trunc_rva"]), "path": got["path"] if got else None}
            tadd("damage_coefficient_resolves_to_a_skillparam_slot", atk_slot is not None,
                 slot=f"skillparam{atk_slot}" if atk_slot is not None else None,
                 path=got["path"] if got else None)

        # ---- pushPow ------------------------------------------------------
        push = SPEC[t].get("push")
        push_slot = None
        if push and push["kind"] == "bullet_push":
            hops = []
            ok = True
            for rva, want in push["chain"]:
                got = view.text_at(rva)
                hops.append({"rva": hex(rva), "expect": want, "got": got})
                ok = ok and got == want
            tadd("push_power_reaches_the_bullet_field", ok,
                 detail=f"字段 _pushPower（0x60）；链 {json.dumps(hops, ensure_ascii=False)}")
            got = resolve_call_arg(view, push["call_rva"], push["arg_reg"], allowed)
            push_slot = PARAM_OFFS.get(got["slot"]) if got and got["slot"] in PARAM_OFFS else None
            info["slots"]["push_pow"] = {"slot": push_slot,
                                         "via": f"{view.name(push['callee'])} → _pushPower（0x60）",
                                         "path": got["path"] if got else None,
                                         "note": push.get("note") or (got.get("note") if got else None)}
            tadd("push_power_resolves_to_a_skillparam_slot", push_slot is not None,
                 slot=f"skillparam{push_slot}" if push_slot is not None else None,
                 note=(got or {}).get("note"))
        else:
            site = attack_call_site(view, util_rva, dmg_rva)
            tadd("chara_behavior_Attack_call_found", site is not None,
                 detail=f"{view.name(site[2])} @{hex(site[1])}" if site else None)
            if site:
                f, addr, callee = site
                got = resolve_slot(view, f, addr, 0, allowed=allowed)
                push_slot = PARAM_OFFS.get(got["slot"]) if got and got["slot"] in PARAM_OFFS else None
                info["slots"]["push_pow"] = {
                    "slot": push_slot, "via": f"{view.name(callee)} 的 pushPower（s0）@{hex(addr)}",
                    "path": got["path"] if got else None,
                    "note": got.get("note") if got else None}
                if got and got.get("zero"):
                    info["push_pow_hardcoded_zero"] = (
                        "该类型不携带推力槽：传给 CharaBehavior.Attack 的 pushPower 是硬编码 0"
                        f"（{hex(addr)} 前 `fmov s2, wzr`）")
                    info["unresolved"].append("推力：pushPower 为硬编码 0，没有对应槽位（不是缺证，是原生即 0）")
                tadd("push_power_resolves_to_a_skillparam_slot_or_hardcoded_zero",
                     push_slot is not None or (got or {}).get("zero"),
                     slot=f"skillparam{push_slot}" if push_slot is not None else None,
                     detail=info.get("push_pow_hardcoded_zero") or (got or {}).get("note"))

        # ---- pinned extra slots -------------------------------------------
        for ex in SPEC[t]["extras"]:
            got = view.text_at(ex["load_rva"])
            ok = got == ex["load"]
            detail = f"{hex(ex['load_rva'])}: {got}"
            if ex.get("peer_rva"):
                got2 = view.text_at(ex["peer_rva"])
                ok = ok and got2 == ex["peer"]
                detail += f"；{hex(ex['peer_rva'])}: {got2}"
            if ex.get("anchor"):
                an = ex["anchor"]
                names = view.float_reg_names(an["callee"])
                hit = (len(names) > an["reg"] and names[an["reg"]] == an["param"])
                # the anchor must be consumed by the anchor callee's matching arg
                nxt = None
                for insn in view.insns(ex["load_rva"]):
                    if insn.address <= ex["load_rva"]:
                        continue
                    if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
                        nxt = int(insn.op_str[1:], 0)
                        break
                ok = ok and hit and nxt == an["callee"]
                detail += (f"；锚点 {view.name(an['callee'])} 的第 {an['reg']} 个浮点形参="
                           f"{names[an['reg']] if len(names) > an['reg'] else None}"
                           f"（要求 {an['param']}），下一个 bl={view.name(nxt) if nxt else None}")
            tadd(f"extra_slot_{ex['slot']}_{ex['kind']}_pinned", ok, detail=detail)
            if ok:
                info["slots"][ex["kind"]] = {"slot": ex["slot"],
                                             "load_rva": hex(ex["load_rva"]), "load": ex["load"]}

        # ---- value distributions (data-side cross-check only) -------------
        info["value_distribution"] = slot_distribution(t)
        types[t] = info

    return checks, types


def slot_distribution(t):
    out = {}
    rows = C.cache_rows("bossskill")
    rs = [r for r in rows if r.get("skillid0") == t]
    for i in range(10):
        vals = [r.get(f"skillparam{i}") for r in rs if r.get(f"skillparam{i}") is not None]
        if not vals:
            continue
        cnt = collections.Counter(vals)
        out[f"skillparam{i}"] = {"n": len(vals), "distinct": len(cnt),
                                 "top": [[k, v] for k, v in cnt.most_common(6)]}
    return {"cache_rows": len(rs), "slots": out}


# ---------------------------------------------------------------------------
# rule rows
# ---------------------------------------------------------------------------
def _existing_rule_keys():
    """(table, effect_type, field_path) already defined by the earlier dictionaries."""
    out = set()
    cc = C.CARD_COMPARISON / "field_dictionary.json"
    if cc.exists():
        for r in C.load_json(cc):
            out.add((r.get("table") or "skilllist", r.get("effect_type"),
                     r.get("field_path") if str(r.get("field_path", "")).startswith("/")
                     else "/" + str(r.get("field_path"))))
    bh = ROOT / "output" / "boss_heal" / "field_dictionary.json"
    if bh.exists():
        for r in C.load_json(bh):
            if "bossskill" not in (r.get("file_table") or ""):
                continue
            fp = r.get("field_path") or ""
            out.add(("bossskill", r.get("effect_type"), fp if fp.startswith("/") else "/" + fp))
    st = ROOT / "output" / "character_skills" / "skilllist_types" / "field_dictionary.json"
    if st.exists():
        for r in C.load_json(st):
            out.add((r.get("table") or "skilllist", r.get("effect_type"), r.get("field_path")))
    return out


def rule_rows(types):
    existing = _existing_rule_keys()
    rows = []
    skipped = []
    for t, info in sorted(types.items()):
        usable = [(k, v) for k, v in info["slots"].items() if v.get("slot") is not None]
        for kind, rec in sorted(usable, key=lambda kv: kv[1]["slot"]):
            slot = rec["slot"]
            key = ("bossskill", t, f"/skillparam{slot}")
            if key in existing:
                # already defined by an earlier dictionary: the merge keeps that row,
                # so this batch must not claim it as a new rule
                skipped.append({"type": t, "field_path": key[2], "role": kind,
                                "note": "既有字典已定义该键，本批不重复声明（merge 只补缺键）"})
                continue
            meaning, unit, rule, limits = role_row(ROLE_TEXT_OVERRIDE.get((t, kind), kind), slot)
            row = {
                "table": "bossskill",
                "effect_type": t,
                "field_path": f"/skillparam{slot}",
                "meaning_zh": meaning,
                "unit": unit,
                "rule": rule,
                "status": STATUS,
                "condition": CONDITION,
                "limits": limits,
                "evidence": [{"read_rva": rec.get("load_rva") or rec.get("fmul_rva"),
                              "detail": rec.get("load") or rec.get("fmul"),
                              "handler": info["handler"],
                              "util_body": info["util_body"],
                              "type_rule_report": "output/character_skills/boss_attack_types/type_rules.json",
                              "native_checks": "output/character_skills/boss_attack_types/native_checks.json"}],
                "answer_kind": kind,
            }
            if rec.get("note"):
                row["role_note"] = rec["note"]
            rows.append(row)
    return rows, skipped


def reference_conflicts(types):
    """The reference-lead labels for the head types, for the 'wrong if read as' note."""
    out = {}
    if not HEAD_TYPES.exists():
        return out
    head = json.loads(HEAD_TYPES.read_text(encoding="utf-8"))
    for t, info in head.items():
        out[t] = [{"slot": l["slot"], "label": l.get("label"), "unit": l.get("unit"),
                   "status": l.get("status"), "verdict": l.get("verdict")}
                  for l in info.get("reference_leads_only") or []]
    return out


def count_cap_corroboration(checks):
    """Data-side corroboration for the count-slot caliber of type1 / type105 / type110.

    For characters whose special move executes the *character record itself* (the P2-9
    F0 class: no reachable pattern skill) the skill text states the number of hits
    directly ("N回"), so it pins the relation between text and slot:

    * type 1  : total attacks = trunc(skillparam3) + 1  (the first attack is emitted at
                _numCounter == 0, the loop stops at _numCounter > cap)
    * type 105/110: total attempts = trunc(skillparam6)  (counter increments before the
                per-hit gate; the text is the total)

    Any character whose text count contradicts its own slot value would show up here.
    """
    import re
    import equivalence as EQ

    text_pat = re.compile(r"(\d+)\s*回")
    t = EQ.tables()
    verdicts = EQ.index()
    n_ok, n_bad, n_seen = 0, 0, 0
    rows = []
    for cid, v in sorted(verdicts.items()):
        if v.get("class") != EQ.NO_PATTERN_FALLBACK:
            continue
        v0 = v.get("skillid0")
        if v0 not in (1, 105, 110):
            continue
        rec, _ = t["charainfo"].get(cid)
        if not rec:
            continue
        text = (rec.get("skilltext") or "") + " " + (rec.get("skillname") or "")
        m = text_pat.search(text)
        if not m:
            continue
        want = int(m.group(1))
        slot = 3 if v0 == 1 else 6
        raw = rec.get(f"skillparam{slot}")
        if raw is None:
            continue
        got = int(float(raw)) + (1 if v0 == 1 else 0)
        n_seen += 1
        ok = got == want
        n_ok += ok
        n_bad += not ok
        if len(rows) < 12 or not ok:
            rows.append({"cid": cid, "type": v0, "slot": f"skillparam{slot}", "raw": raw,
                         "text_count": want, "expected_total": got, "ok": ok,
                         "text": text.strip()[:70]})
    checks.append({
        "name": "count_slot_matches_the_character_text_on_no_pattern_characters",
        "ok": n_bad == 0 and n_seen >= 40,
        "checked": n_seen, "match": n_ok, "mismatch": n_bad,
        "detail": (f"type1 用 trunc(sp3)+1、type105/110 用 trunc(sp6) 与角色正文的回数比较："
                   f"{n_ok}/{n_seen} 相符"),
        "samples": rows[:12],
    })
    return n_seen, n_bad


def main():
    C.enable_utf8_console()
    OUT.mkdir(parents=True, exist_ok=True)
    md, native = CT.load_native()
    view = NativeView(md, native)
    checks, types = analyze(view)
    crosscheck_push_sentinel(types, checks)
    checks += emulation_checks(view, types)
    count_cap_corroboration(checks)
    passed = sum(1 for c in checks if c["ok"])
    failed = [c["name"] for c in checks if not c["ok"]]
    rules, skipped = rule_rows(types)
    conflicts = reference_conflicts(types)
    for t, info in types.items():
        if t in (3, 22, 110):
            info["reference_lead_conflicts"] = conflicts.get(str(t), [])
            info["reference_lead_note"] = (
                "参考候选把 type3 的 param1/param2/param3/param4 全部标成「伤害」、type22 的 param1/2/3/4 "
                "全部标成伤害/次、type110 的 param2/param3 标成攻击力(x-1.5)×100；本批原生证据下："
                "param1 是伤害基值倍率，另几槽分别是推力／范围长度／起点缩放（见 slots）。"
                "按参考标签写会把推力与范围长度答成伤害倍率。")
    C.write_json(OUT / "type_rules.json", {
        "batch": "P2 第 8 批",
        "scope": "bhSkill.Exec_ATTACK_* 家族（type 0/1/2/3/4/5/22/47/110）的槽位语义",
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
        "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
        "damage_base": {
            "function": "bhSkillUtil.getBasicSkillAttack",
            "rva": hex(GET_BASIC_RVA),
            "argument": "w1=1（true 分支）",
            "formula": "伤害输入 = floor/clamp(float32(B × skillparamN))",
            "integerisation_rva": hex(TRUNC_RVA),
            "note": ("与 type105／type112 既有证据同一条函数与同一整数化助手；"
                     "P2-1 的『全局技能表』候选（" + GLOBAL_OFFSET_TABLE + "）实为攻击起点偏移，"
                     "不是伤害基准值"),
        },
        "types": types,
        "skipped_existing_keys": skipped,
    })
    C.write_json(OUT / "native_checks.json", {
        "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
        "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "limits": [
            "逐指令静态解码＋调用图回溯；不声称实机运行，也不声称最终扣血",
            "只证明『该 type 的伤害输入乘的是哪个槽、推力/间隔/次数等槽读到哪里』",
            "不证明手机当前装载哪个 JSON 快照；运行时不变量（Chain/能力/状态）未展开",
        ],
    })
    C.write_json(OUT / "field_dictionary.json", rules)
    (OUT / "README.md").write_text(README, encoding="utf-8")
    print(json.dumps({"checks": f"{passed}/{len(checks)}", "failed": failed,
                      "rules": len(rules), "types": sorted(types), "out": str(OUT)},
                     ensure_ascii=False))
    return 0 if not failed else 1


README = """# 攻击系 boss 技能类型族：伤害基数与槽位（P2 第 8 批）

本目录只由 `scripts/character_skills/boss_attack_types.py` 生成；只读既有恢复镜像与解码元数据。

## 结论

- **伤害基数已定位**：`bhSkill.Exec_ATTACK_*` 家族的伤害输入一律是
  `floor/clamp(float32(B × skillparamN))`，其中 `B = bhSkillUtil.getBasicSkillAttack(true)`
  （`0x1182ed8`，入参 `w1=1`），整数化助手 `0x14374bc`——与 type105／type112 既有证据是
  **同一条函数、同一个整数化助手**。
- **P2-1 的「全局技能表」候选不是伤害表**：`[[0x29e9000+0x6e8]]+0xb8` 的三浮点被
  `skillparam4` 缩放后**加到施法者位置上**，作为 `BattleManager.FindNearPosition` 的搜索中心，
  属攻击起点偏移。
- **每类型槽位**（逐槽证据 RVA 见 `type_rules.json`）：

| type | handler | 伤害系数 | 推力 | 其它已核槽 |
|---|---|---|---|---|
| 0 | Exec_ATTACK_NORMAL | skillparam1 | skillparam3 | — |
| 1 | Exec_ATTACK_REPEAT | skillparam1 | 硬编码 0（无推力槽） | param2 间隔(秒)、param3 每目标次数上限 |
| 2 | Exec_ATTACK_DASH | skillparam1 | skillparam3 | param2 突进位移 |
| 3 | Exec_ATTACK_AREA | skillparam1 | skillparam3 | param2 范围长度、param4 起点偏移缩放 |
| 4 | Exec_ATTACK_ALL | skillparam1 | skillparam3 | — |
| 5 | Exec_SHOOT_NORMAL | skillparam1 | skillparam3（×Chain 后进 `_pushPower`） | param4 子弹横向半径输入 |
| 22 | Exec_ATTACK_FRONT | skillparam1 | skillparam4 | param2 前方到达延长、param3 横向宽度 |
| 47 | Exec_SHOOT_SPREAD | **skillparam0** | skillparam4 | param1 爆炸类型、param2/3 爆炸半径、param5 第二段伤害 |
| 105 | Exec_ATTACK_FRONT_REPEAT | skillparam1（既有） | skillparam4 | param5 间隔(秒) |
| 110 | Exec_ATTACK_AREA_REPEAT | skillparam1 | skillparam3 | param2 范围长度、param4 起点偏移缩放、param5 间隔(秒)、param6 每目标次数上限 |

- **数据侧交叉印证**：`0.001` 这个「几乎不推」的取值密集出现在各类型的**推力槽**上
  （type105 param4 60/141、type110 param3 129/216、type112 param7 86/91 已知为推力），
  而它不出现在伤害系数槽；见 `type_rules.json` 的 `value_distribution`。

## 验证与重跑

```powershell
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/boss_attack_types.py
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/profiles.py
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/gaps.py
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/boss_attack_types.py --report-increment
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/verify_p1.py
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/crosscheck_raw.py
```
"""


# ---------------------------------------------------------------------------
# increment
# ---------------------------------------------------------------------------
def _answer_keys(path: Path):
    out = {}
    if not path.exists():
        return out
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            for holder in [r] + [c for c in (r.get("children") or [])
                                 if isinstance(c, dict) and "answers" in c]:
                for a in holder.get("answers") or []:
                    out[(holder.get("table"), holder.get("record_id"), holder.get("layer"),
                         a["f"])] = (holder.get("effect_type"), a)
    return out


def _unexplained_keys(path: Path):
    out = set()
    if not path.exists():
        return out
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            for holder in [r] + [c for c in (r.get("children") or [])
                                 if isinstance(c, dict) and "unexplained" in c]:
                for u in holder.get("unexplained") or []:
                    out.add((holder.get("table"), holder.get("record_id"),
                             holder.get("layer"), u["f"]))
    return out


def _record_bodies(path: Path):
    out = {}
    if not path.exists():
        return out
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            out[r.get("rec_key")] = r
    return out


def report_increment():
    rules = json.loads((OUT / "field_dictionary.json").read_text(encoding="utf-8"))
    new_rule_keys = {f"{r['table']}|{r['effect_type']}|{r['field_path']}" for r in rules}
    old = json.loads(SUMMARY_BEFORE.read_text(encoding="utf-8")) if SUMMARY_BEFORE.exists() else {}
    summary = json.loads((PROF / "summary.json").read_text(encoding="utf-8"))
    before = _answer_keys(RECORDS_BEFORE)
    now = _answer_keys(PROF / "records.jsonl")
    new_keys = {k for k in now if k not in before}
    lost = sorted(k for k in before if k not in now)
    changed = sorted(k for k, v in before.items()
                     if k in now and any(now[k][1].get(f) != v[1].get(f)
                                         for f in ("raw", "kind", "unit", "status", "scope")))
    changed_text = sorted(k for k, v in before.items()
                          if k in now and now[k][1].get("value") != v[1].get("value"))

    by_type = collections.Counter()
    by_group = collections.Counter()
    chars_by_type = collections.defaultdict(set)
    routes_by_cid = collections.defaultdict(set)
    migrated_cids = []
    migrated = 0
    page_sum = 0
    earlier_page_sum = 0
    with (PROF / "profiles.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)
            before_on_page = 0
            for g in p["groups"]:
                for ref in g["records"]:
                    rec = BEFORE_BODIES.get(ref.get("rec_key"))
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
                    rec = NOW_BODIES.get(ref.get("rec_key"))
                    if rec is None:
                        continue
                    holders = [rec] + [c for c in rec.get("children") or []
                                       if isinstance(c, dict) and "answers" in c]
                    for holder in holders:
                        for a in holder.get("answers") or []:
                            if a.get("rule_key") in new_rule_keys:
                                by_type[holder.get("effect_type")] += 1
                                by_group[g["group"]] += 1
                                page_sum += 1
                                hit.add(holder.get("effect_type"))
                                route = ("charainfo 必杀技参数（等价门控通过）"
                                         if holder.get("table") == "charainfo" else
                                         "传授链（denju）" if g["group"].startswith("denju") else
                                         "自身 pattern 可达的 boss 技能")
                                routes_by_cid[p["cid"]].add(route)
                            else:
                                # answers that appeared after the baseline but carry a rule
                                # from an earlier batch (the P2-9 F0 answers of the heal /
                                # type13 / type27 families land here)
                                akey = (holder.get("table"), holder.get("record_id"),
                                        holder.get("layer"), a["f"])
                                if akey not in before:
                                    earlier_page_sum += 1
            for t in hit:
                chars_by_type[t].add(p["cid"])
            if hit and not before_on_page:
                migrated += 1
                migrated_cids.append(p["cid"])

    un_now = _unexplained_keys(PROF / "records.jsonl")
    un_then = _unexplained_keys(RECORDS_BEFORE)
    rec_level = len({k for k in new_keys if now[k][1].get("rule_key") in new_rule_keys})
    row_instances = 0
    with (PROF / "records.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            for holder in [r] + [c for c in (r.get("children") or [])
                                 if isinstance(c, dict) and "answers" in c]:
                for a in holder.get("answers") or []:
                    if a.get("rule_key") in new_rule_keys:
                        row_instances += 1
    payload = {
        "batch": "P2 第 8 批",
        "scope": "攻击系 boss 技能类型族（type 0/1/2/3/4/5/22/47/105/110 的伤害基数与槽位）",
        "new_rules": len(rules),
        "new_rule_count_by_type": dict(sorted(collections.Counter(
            r["effect_type"] for r in rules).items())),
        "new_answers_page_sum": page_sum,
        "new_answers_from_earlier_rule_sets_page_sum": earlier_page_sum,
        "new_answers_page_sum_note": (
            "new_answers_page_sum 只计「P8 新增 35 条规则」产生的答案；随后续批次（P2 第 9 批的 F0 类答案）"
            "落在**更早批次规则**上的新答案记在 new_answers_from_earlier_rule_sets_page_sum。"
            "两者之和＝summary.rule_answers 与 work/p8_summary_before.json 的差"),
        "new_answers_record_level": rec_level,
        "new_answers_row_instances_in_records_jsonl": row_instances,
        "new_answer_keys_unique": len(new_keys),
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(by_type.items(), key=lambda x: -x[1])},
        "answers_by_group": dict(sorted(by_group.items())),
        "characters_reachable_total": len({c for s in chars_by_type.values() for c in s}),
        "characters_reachable_page_sum": {str(t): len(v) for t, v in sorted(chars_by_type.items())},
        "status_migrations_unknown_to_partial": migrated,
        "status_counts_before": old.get("status_counts"),
        "status_counts_after": summary.get("status_counts"),
        "existing_answer_keys_lost": len(lost),
        "existing_answer_keys_lost_detail": lost[:10],
        "existing_answer_keys_raw_kind_unit_status_scope_changed": len(changed),
        "existing_answer_keys_value_text_changed": len(changed_text),
        "unexplained_fields_delta": {
            "before": old.get("totals", {}).get("unexplained_fields"),
            "after": summary["totals"]["unexplained_fields"],
            "delta": summary["totals"]["unexplained_fields"] - old.get("totals", {}).get("unexplained_fields", 0),
            "distinct_keys_added": len(un_now - un_then),
            "distinct_keys_removed": len(un_then - un_now),
        },
        "caliber_note": ("页求和＝按角色页引用计数（同一记录若出现在同页的多个技能组会重复计数，"
                         "＝summary.rule_answers 的批次差）；"
                         "记录级＝（表,记录,层,字段）新键中命中新规则的条数；"
                         "records.jsonl 内answer 行实例数＝共享子记录在每个父记录下各算一次（本批 "
                         f"{row_instances}）；唯一键＝全部新增键。"
                         "「仅未知」角色可经三条路脱贫：自身 pattern 可达的 boss 技能、传授链、"
                         "charainfo 等价门控（三条路的逐人归属见 unknown_reachability.routes）"),
        "unknown_reachability": unknown_reachability(migrated_cids, routes_by_cid),
    }
    C.write_json(OUT / "p8_increment.json", payload)
    print(json.dumps({k: payload[k] for k in ("new_rules", "new_answers_page_sum",
                                              "new_answers_record_level", "new_answer_keys_unique",
                                              "status_migrations_unknown_to_partial")},
                     ensure_ascii=False))
    return payload


BEFORE_BODIES = {}
NOW_BODIES = {}


def unknown_reachability(migrated_cids=(), routes_by_cid=None):
    """How the '仅未知' set was actually reached, and what still blocks the rest."""
    import csv as _csv
    sys.path.insert(0, str(ROOT / "scripts" / "character_skills"))
    import equivalence as EQ
    idx = EQ.index()
    rows = list(_csv.DictReader((PROF / "characters.csv").open(encoding="utf-8")))
    unknown = [r for r in rows if r["status"] == "仅未知"]
    per = collections.defaultdict(collections.Counter)
    for r in unknown:
        v = idx.get(int(r["cid"])) or {}
        per[v.get("skillid0")][v.get("class")] += 1
    routes = collections.Counter()
    per_cid = {}
    for cid in migrated_cids:
        rs = sorted((routes_by_cid or {}).get(cid, []))
        per_cid[str(cid)] = rs
        routes["＋".join(rs)] += 1
    return {
        "unknown_characters_before": 373,
        "unknown_characters_after": len(unknown),
        "migrated": len(migrated_cids),
        "migrated_routes_by_count": dict(sorted(routes.items(), key=lambda kv: -kv[1])),
        "migrated_cid_routes": per_cid,
        "note": ("「仅未知」角色可经三条路获得本批答案：①自身 pattern 可达的 boss 技能；"
                 "②传授链（denju／denju_lb）；③charainfo 必杀技参数（须过记录级等价门控）。"
                 "只走 charainfo 一途的角色很少："
                 "「skillid[0] 不在自身 pattern 类型集合」（NOT_AMONG_OWN_PATTERN_TYPES）与 "
                 "X1（两侧数值不同）类角色没有可对齐的 boss 记录，等价门控不通过，"
                 "本批新增类型规则对其无作用——这不是缺规则，而是缺等价前提"),
        "remaining_unknown_by_type_class": {str(t): dict(c) for t, c in
                                            sorted(per.items(), key=lambda x: str(x[0]))},
    }


if __name__ == "__main__":
    if "--report-increment" in sys.argv:
        C.enable_utf8_console()
        BEFORE_BODIES.update(_record_bodies(RECORDS_BEFORE))
        NOW_BODIES.update(_record_bodies(PROF / "records.jsonl"))
        report_increment()
        raise SystemExit(0)
    sys.exit(main())
