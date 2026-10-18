"""skilllist ability-type dispatch: which parameter slots each type really reads.

The player-side apply pipeline (``BattleParam``) accumulates one multiplicative factor
per ability, by switching on ``skillParameter.get_ability()`` and reading specific
``paramN`` / ``iParamN`` slots in the matching branch:

* ``BattleParam.GetAbilityAttack``     (0x1107390) -> attack factor
* ``BattleParam.GetAbilityDefence``    (0x1107df0) -> damage-taken factor
* ``BattleParam.GetAbilityWalkSpeed``  (0x1118900) -> walk-speed factor

Each branch is:

    IsEnableAbility(this, skill, target)   ; eligibility gate
    skillParameter.get_paramN              ; the slot that carries the effect
    fmul factor, factor, paramN            ; into the accumulator (multiplicative)

This module resolves the per-type branch by *executing the switch prologue* of the
three functions under Unicorn (the game's own instruction bytes) and then reads the
resolved branch statically to list the slots it touches. It is the skilllist
counterpart of the P2 batch-1 ``bhSkill.ExecSkill`` index.

Outputs (``output/character_skills/skilllist_types/``):

* ``dispatch_map.json``  -- per ability type: attack/defence/move branch + slots read
* ``native_checks.json`` -- controlled native fragments (emulated switch resolution,
  tail instruction identity, branch slot sets, agreement with already-confirmed rules)
* ``field_dictionary.json`` -- the new rules this batch confirms, in the same shape the
  existing rule sources use (consumed by ``rules.py``)
* ``type_evidence.json`` -- per target type (8/26/67/1059): raw records, representative
  characters, reference candidates as leads only, native slots, confirmed rule or the
  named missing evidence
* ``README.md``
"""
from __future__ import annotations

import bisect
import collections
import csv
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT / "scripts", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import common as C  # noqa: E402
import rules as R  # noqa: E402

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM  # noqa: E402
from il2cpp_sample_code import Native  # noqa: E402
from metadata_targets import Metadata  # noqa: E402
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE  # noqa: E402
from unicorn.arm64_const import (UC_ARM64_REG_PC, UC_ARM64_REG_X0,  # noqa: E402
                                 UC_ARM64_REG_X8, UC_ARM64_REG_X21, UC_ARM64_REG_X23)
import unicorn.arm64_const as _uac  # noqa: E402

# X0..X30 by name: ``UC_ARM64_REG_X0 + n`` is *not* valid -- X29/X30 are separate
# constants (X29 is 0x1), so naming them explicitly is the only correct mapping
REG_X = {f"x{i}": getattr(_uac, f"UC_ARM64_REG_X{i}") for i in range(31)}

OUT = ROOT / "output" / "character_skills" / "skilllist_types"
METADATA = ROOT / "work" / "protection" / "metadata_aei_decoded.bin"
DIS = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
BASE = 0x50000000

# --- the three apply functions and their type switches -----------------------
# (name, entry_rva, switch_head_rva, terminal_rvas, tail_rva, loop_preamble_rva)
FUNCS = {
    "attack": dict(entry=0x1107390, head=0x1107680, tail=0x1107C88,
                   terminals={0x11076CC, 0x1107768, 0x1107824, 0x1107958,
                              0x110797C, 0x110799C, 0x11077C8, 0x1107C88, 0x1107C98}),
    "defence": dict(entry=0x1107DF0, head=0x1107FEC, tail=0x1108148,
                    terminals={0x110803C, 0x11080EC, 0x1108108, 0x1108124, 0x1108148,
                               0x1108158, 0x110821C, 0x110823C}),
    "move": dict(entry=0x1118900, head=0x1118A14, tail=0x1118C4C,
                 terminals={0x1118C28, 0x1118C4C, 0x1118BC8, 0x1118D74}),
        # P2 batch 3: the two critical accumulators. Both are *additive* (fadd) and each
    # branch ends by branching to its own loop tail, so there is no separate multiply
    # tail -- the accumulate happens inline in the branch.
    "crit_rate": dict(entry=0x1119018, head=0x11191A8, tail=0x11195BC,
                      terminals={0x11195BC, 0x111933C, 0x1119388, 0x111920C,
                                 0x1119530, 0x11193D4, 0x11191D0}),
    "crit_dmg": dict(entry=0x1119794, head=0x1119930, tail=0x1119DD0,
                     terminals={0x1119DD0, 0x1119A48, 0x1119A70, 0x1119ABC,
                                0x111997C, 0x1119B90, 0x1119CE8, 0x1119B74}),
}
NEUTRAL = {"attack": 0x1107C88, "defence": 0x1108148, "move": 0x1118C4C,
           "crit_rate": 0x11195BC, "crit_dmg": 0x1119DD0}
# the shared accumulate tail of the multiplicative paths (the crit paths accumulate
# inline with fadd, so their tail is the loop tail itself)
TAIL_MUL = {"attack": 0x1107C84, "defence": 0x1108144, "move": 0x1118C48,
            "crit_rate": 0x11195BC, "crit_dmg": 0x1119DD0}
ACCUM_OP = {"attack": "fmul s8,s8,s0", "defence": "fmul s8,s8,s0", "move": "fmul s8,s8,s0",
            "crit_rate": "fadd s9,s9,s0", "crit_dmg": "fadd s9,s9,s0"}
MULTIPLICATIVE = ("attack", "defence", "move")
# the switch leaves whose bodies open with pure instructions (``mov``/``adrp``) and so
# must be declared as stop points; every other leaf starts with real work (a load or a
# call) and is discovered automatically from the branch targets
PURE_LEAVES = {
    "attack": {0x1107958, 0x1107C88},
    "defence": {0x110803C, 0x1108124, 0x1108148},
    "move": {0x1118C28, 0x1118C4C},
    "crit_rate": {0x11195BC, 0x111933C, 0x1119388, 0x111920C, 0x1119530, 0x11193D4},
    "crit_dmg": {0x1119DD0, 0x1119A48, 0x1119A70, 0x1119ABC, 0x111997C,
                 0x1119B90, 0x1119CE8},
}
ISENABLE = 0x1112574
ISABLE_END = 0x1113958
SETUPABILITY = 0x10F402C
GET_ABILITY = 0x1DBCF0C
GETTERS = {f"skillParameter.get_param{i}": f"param{i}" for i in range(10)}
GETTERS.update({f"skillParameter.get_iParam{i}": f"iParam{i}" for i in range(2)})
GETTERS["skillParameter.get_flag"] = "flag"
PURE = {"cmp", "b", "tst", "lsl", "lsr", "asr", "mov", "movz", "movk", "movn",
        "add", "sub", "and", "orr", "ands", "eor", "csel", "csinc", "cset", "adr", "adrp"}
MAX_TYPE = 3000


def is_pure(insn):
    """Switch-prologue ops: compares, register math, and (conditional) branches.

    ``bl`` is deliberately excluded: it is the first real work of a leaf.
    """
    if insn is None:
        return False
    m = insn.mnemonic
    if m == "bl":
        return False
    if m == "b" or m.startswith("b."):
        return True
    return m in PURE


def load_native():
    md = Metadata(str(METADATA))
    return md, Native(md)


def first_insn(native, rva):
    return next(iter(DIS.disasm(native.raw[rva:rva + 4], rva)), None)


class Resolver:
    def __init__(self, native):
        self.n = native
        self.uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        size = (len(native.raw) + 0xFFF) & ~0xFFF
        self.uc.mem_map(BASE, size)
        self.uc.mem_write(BASE, native.raw)

    def mask_registers(self, kind):
        """The 1-constants the function's prologue loads into callee-saved registers.

        The switch is compiled as bit tests over ``1 << type`` with the constant 1 kept in
        a register preset once in the prologue -- attack ``x23``, defence ``x21``,
        crit_rate ``x26``, crit_dmg ``x29``. Emulation starts at the switch head, so those
        presets have to be seeded; without them every ``tst`` reads 0 and *every* type
        falls to the loop tail (which is exactly how the low crit types were mis-filed as
        neutral -- see ``review/p2b3_20261017_thirdparty/REPORT.md`` problem 1).
        """
        cfg = FUNCS[kind]
        regs = {}
        for ins in DIS.disasm(self.n.raw[cfg["entry"]:cfg["head"]], cfg["entry"]):
            if ins.mnemonic == "mov" and re.match(r"^[wx]\d+, #(?:1|0x1)$", ins.op_str):
                reg = ins.op_str.split(",")[0]
                regs[reg] = 1
        return regs

    def resolve(self, kind, ability_type, x21=1, x23=1):
        """Emulate one switch prologue; return the *branch target* it lands on.

        The reported address is the start of the basic block that does the real work:
        it is tracked during emulation (every executed branch starts a new block), so a
        leaf reached by fall-through is reported correctly, and a leaf whose body opens
        with a pure prologue (``adrp``/``mov``) is not shifted by it.
        """
        cfg = FUNCS[kind]
        cfg["terminals"] = derive_terminals(self.n, kind)
        hit = {"rva": None}
        state = {"block": cfg["head"], "new_block": False}

        def hook(u, addr, sz, data):
            rva = addr - BASE
            if state["new_block"]:
                # the previous executed instruction was a branch, so this PC begins a
                # new basic block -- that entry is the branch target we want to report
                state["block"] = rva
            ins = first_insn(self.n, rva)
            if rva in cfg["terminals"] or not is_pure(ins):
                hit["rva"] = state["block"]
                u.emu_stop()
                return
            state["new_block"] = (ins.mnemonic == "b" or ins.mnemonic.startswith("b."))
        h = self.uc.hook_add(UC_HOOK_CODE, hook)
        self.uc.reg_write(UC_ARM64_REG_X0, ability_type & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM64_REG_X21, x21)
        self.uc.reg_write(UC_ARM64_REG_X23, x23)
        for reg, value in self.mask_registers(kind).items():
            # 'wN' and 'xN' name the same register; writing xN also sets the low 32 bits
            self.uc.reg_write(REG_X["x" + reg[1:]], value)
        try:
            self.uc.emu_start(BASE + cfg["head"], 0, count=128)
        except Exception as exc:  # pragma: no cover - only on unmodelled input
            hit["rva"] = f"FAULT:{type(exc).__name__}"
        self.uc.hook_del(h)
        return hit["rva"]


def leaf_slots(native, kind, leaf):
    """Slots a resolved branch touches, plus whether IsEnableAbility gates it.

    The branch body is bounded by *itself*: scanning stops at the first
    unconditional ``b`` (every branch ends with exactly one branch out), at the shared
    ``fmul s8,s8,s0`` multiply, or at the scan window end. An earlier version also
    stopped as soon as the instruction address passed the loop tail, which silently
    truncated every branch that sits *after* the loop tail in the image
    (defence 67/96/1036, move 96/1036) -- those types were then filed as neutral
    because their slot list came back empty. See the review report
    ``output/character_skills/review/p2b2_20261017_thirdparty/REPORT.md`` problem 1.
    """
    if not isinstance(leaf, int) or leaf in (NEUTRAL[kind],) or str(leaf).startswith("FAULT"):
        return {"slots": [], "gated_by_isenable": False, "exit": None,
                "reaches_accumulate_op": False, "note": "中性/无法解析"}
    cfg = FUNCS[kind]
    slots, gated, exit_target, hits_mul = [], False, None, False
    gate_rva, slot_calls = None, []
    for insn in DIS.disasm(native.raw[leaf:leaf + 0x400], leaf):
        if insn.mnemonic == "bl" and insn.op_str.startswith("#0x"):
            tgt = int(insn.op_str[1:], 16)
            name = None
            for j in native.method_by_rva.get(tgt, []):
                m = native.method(j)
                name = f"{m['declaring_type']}.{m['name']}"
                break
            if name in GETTERS and GETTERS[name] not in slots:
                slots.append(GETTERS[name])
                slot_calls.append({"field": GETTERS[name], "rva": hex(insn.address)})
            elif tgt == ISENABLE:
                gated = True
                gate_rva = hex(insn.address)
        if f"{insn.mnemonic} {insn.op_str}".replace(" ", "") == ACCUM_OP[kind].replace(" ", ""):
            hits_mul = True
        if insn.mnemonic == "b" and insn.op_str.startswith("#0x"):
            exit_target = int(insn.op_str[1:], 16)
            if exit_target == TAIL_MUL[kind]:
                hits_mul = True
            break
    # a branch may hand its value to the accumulate by branching straight at it
    # (crit 3/1036 exit to the shared ``fadd`` site), so also test the exit target
    if not hits_mul and exit_target is not None:
        tail_ins = first_insn(native, exit_target)
        if tail_ins is not None and                 f"{tail_ins.mnemonic} {tail_ins.op_str}".replace(" ", "") ==                 ACCUM_OP[kind].replace(" ", ""):
            hits_mul = True
    return {"slots": slots, "gated_by_isenable": gated, "gate_rva": gate_rva,
            "slot_calls": slot_calls,
            "exit": hex(exit_target) if exit_target is not None else None,
            "reaches_accumulate_op": hits_mul}


def _compact(kind, per):
    """Entries plus the neutral ranges, so the JSON stays readable.

    ``neutral`` means exactly "the resolved leaf is the loop tail", i.e. the type
    contributes no factor on this path. A branch that resolved to real code but whose
    slot scan found nothing inside the window is a *separate* class
    (``branch_no_slots_in_window``) and is never folded into the neutral bucket.
    """
    cfg = FUNCS[kind]
    entries, neutral, no_slots, ranges, start = {}, [], [], [], None
    for t in range(MAX_TYPE + 1):
        v = per[t]
        is_neutral = (v["leaf"] == hex(cfg["tail"])) or str(v["leaf"]).startswith("FAULT")
        if is_neutral:
            neutral.append(t)
            if start is None:
                start = t
            continue
        if not v["slots"]:
            no_slots.append({"type": t, "leaf": v["leaf"], "exit": v.get("exit"),
                             "gated_by_isenable": v["gated_by_isenable"],
                             "gate_rva": v.get("gate_rva")})
            if start is None:
                start = t
            continue
        if start is not None:
            ranges.append([start, t - 1])
            start = None
        entries[str(t)] = {"leaf": v["leaf"], "slots": v["slots"],
                           "gated_by_isenable": v["gated_by_isenable"],
                           "gate_rva": v.get("gate_rva"),
                           "slot_calls": v.get("slot_calls"),
                           "exit": v.get("exit"),
                           "reaches_accumulate_op": v.get("reaches_accumulate_op")}
    if start is not None:
        ranges.append([start, MAX_TYPE])
    return {"entries": entries, "neutral_ranges": ranges,
            "neutral_count": len(neutral), "entries_count": len(entries),
            "branch_no_slots_in_window": no_slots,
            "branch_no_slots_count": len(no_slots)}


def branch_targets(native, kind):
    """Every in-region branch target of the switch tree (decision nodes and leaves)."""
    cfg = FUNCS[kind]
    end = min(p for p in native.pointers if p > cfg["entry"])
    targets = set()
    for insn in DIS.disasm(native.raw[cfg["head"]:end], cfg["head"]):
        if insn.mnemonic == "b" or insn.mnemonic.startswith("b."):
            if insn.op_str.startswith("#0x"):
                t = int(insn.op_str[1:], 16)
                if cfg["head"] <= t < end:
                    targets.add(t)
    return sorted(targets)


def derive_terminals(native, kind):
    """Declared pure-starting leaves plus every branch target that does real work."""
    cfg = FUNCS[kind]
    # only the *pure-starting* declared terminals are stop points: the declared list
    # also names the switch's decision nodes, which must be traversed (stopping on them
    # would report the node instead of the branch it selects)
    explicit = set(PURE_LEAVES[kind])
    for t in branch_targets(native, kind):
        if not is_pure(first_insn(native, t)):
            explicit.add(t)
    return explicit


def build_maps(native, resolver):
    maps = {}
    for kind in FUNCS:
        per = {}
        for t in range(MAX_TYPE + 1):
            leaf = resolver.resolve(kind, t)
            per[t] = {"leaf": leaf if isinstance(leaf, str) else hex(leaf),
                      "neutral": leaf == NEUTRAL[kind],
                      **leaf_slots(native, kind, leaf)}
        maps[kind] = per
    return maps


# ---------------------------------------------------------------------------
# item 1: static switch evaluator (the "sim vs static" dual-path check)
# ---------------------------------------------------------------------------
def _parse_ops(op_str):
    """Split an operand list, dropping the shift suffix from ``movk ... , lsl #32``."""
    parts = [x.strip() for x in op_str.split(",")]
    shift = 0
    # the shift is its own comma-separated token ("movk x9, #0x15, lsl #32"), and it is
    # the *last* token -- looking at the second-to-last one silently discarded the shift
    if parts and parts[-1].startswith("lsl"):
        shift = int(parts[-1].split("#", 1)[1], 0)
        parts = parts[:-1]
    return [p.lstrip("#") for p in parts], shift


def _rname(tok):
    """Normalise ``w21``/``x21`` to one key (``x21``); ``None`` for non-registers."""
    if tok in ("wzr", "xzr"):
        return None
    if tok and tok[0] in "wx" and tok[1:].isdigit():
        return "x" + tok[1:]
    return None


def _value(tok, regs):
    """Register value (width-agnostic), else the integer immediate.

    Two traps this avoids: (a) ``w21`` and ``x21`` are the same register -- keying on the
    literal name made ``lsl x8, x21, x8`` read 0 because the preset was stored as ``w21``;
    (b) ``str.isdigit()`` is false for hex immediates (``cmp w0, #0x44``), which would
    silently compare against 0.
    """
    name = _rname(tok)
    if name is not None:
        return regs.get(name, 0)
    if tok in ("wzr", "xzr"):
        return 0
    try:
        return int(tok, 0)
    except ValueError:
        return 0


def _set(tok, value, regs):
    name = _rname(tok)
    if name is None:
        return
    bits = 64 if tok[0] == "x" else 32
    regs[name] = value & ((1 << bits) - 1)


def _flags_sub(a, b, bits):
    """NZCV for ``a - b`` at the given width."""
    mask = (1 << bits) - 1
    res = (a - b) & mask
    n = (res >> (bits - 1)) & 1
    z = 1 if res == 0 else 0
    c = 1 if (a & mask) >= (b & mask) else 0          # no-borrow
    sa, sb, sr = (a >> (bits - 1)) & 1, (b >> (bits - 1)) & 1, n
    v = 1 if (sa != sb) and (sr != sa) else 0
    return {"n": n, "z": z, "c": c, "v": v}


def _flags_and(a, b, bits):
    mask = (1 << bits) - 1
    return _flags_sub(a & b, 0, bits), mask


def _cond_holds(mnemonic, f):
    cond = mnemonic.split(".", 1)[1]
    n, z, c, v = f["n"], f["z"], f["c"], f["v"]
    table = {
        "eq": z == 1, "ne": z == 0,
        "hi": c == 1 and z == 0, "ls": not (c == 1 and z == 0),
        "cc": c == 0, "cs": c == 1, "hs": c == 1, "lo": c == 0,
        "mi": n == 1, "pl": n == 0,
        "ge": n == v, "lt": n != v,
        "gt": z == 0 and n == v, "le": not (z == 0 and n == v),
        "al": True,
    }
    return table.get(cond, False)


def static_leaf_map(native, kind, terminals):
    """Evaluate the switch chain *statically* for every type (no Unicorn).

    Mirrors :meth:`Resolver.resolve` step for step -- same stop condition (first
    non-pure instruction) and same basic-block reporting -- but takes the bit-test
    constant from the prologue *instruction text* instead of trusting an emulator
    register file. That independence is the point: it catches a missing register
    preset, which is exactly the defect this batch's review found (a type silently
    folding into the loop tail).
    """
    cfg = FUNCS[kind]
    end = min([p for p in native.pointers if p > cfg["entry"]], default=len(native.raw))
    code = {i.address: i for i in DIS.disasm(native.raw[cfg["head"]:end], cfg["head"])}
    presets = {_rname(k) or k: v for k, v in _prologue_presets(native, kind).items()}
    out = {}
    for ability_type in range(MAX_TYPE + 1):
        regs = dict(presets)
        regs["x0"] = ability_type
        pc, block, prev_branch = cfg["head"], cfg["head"], False
        stop = None
        for _ in range(256):
            ins = code.get(pc)
            if prev_branch:
                block = pc
                prev_branch = False
            if ins is None or not is_pure(ins) or pc in terminals:
                stop = block
                break
            m, ops, shift = ins.mnemonic, *_parse_ops(ins.op_str)
            nxt = pc + ins.size
            if m == "b" and ops[0].startswith("0x"):
                pc, prev_branch = int(ops[0], 16), True
                continue
            if m.startswith("b."):
                taken = _cond_holds(m, regs.get("__flags__") or {"n": 0, "z": 0, "c": 0, "v": 0})
                pc = int(ops[0], 16) if taken else nxt
                # a *not-taken* conditional branch also ends the basic block, so the
                # next instruction starts a new one -- same rule as the emulator, which
                # is what makes the two results comparable
                prev_branch = True
                continue
            if m == "cmp":
                bits = 64 if ops[0][0] == "x" else 32
                a, b = _value(ops[0], regs), _value(ops[1], regs)
                regs["__flags__"] = _flags_sub(a, b, bits)
            elif m == "tst":
                bits = 64 if ops[0][0] == "x" else 32
                a, b = _value(ops[0], regs), _value(ops[1], regs)
                regs["__flags__"] = _flags_sub(a & b, 0, bits)
            elif m in ("mov", "movz", "adrp", "adr"):
                # adrp/adr only need *a* concrete value: the next instruction is a load
                # (non-pure), so the walk stops right after it either way
                _set(ops[0], _value(ops[1], regs), regs)
            elif m == "movk":
                imm = (_value(ops[1], regs) & 0xFFFF) << shift
                cur = _value(ops[0], regs)
                _set(ops[0], (cur & ~(0xFFFF << shift)) | imm, regs)
            elif m in ("add", "sub"):
                a, b = _value(ops[1], regs), _value(ops[2], regs)
                _set(ops[0], a + b if m == "add" else a - b, regs)
            elif m == "lsl":
                _set(ops[0], _value(ops[1], regs) << _value(ops[2], regs), regs)
            elif m in ("and", "orr"):
                a, b = _value(ops[1], regs), _value(ops[2], regs)
                _set(ops[0], a & b if m == "and" else a | b, regs)
            else:
                stop = f"UNMODELLED:{m}@{hex(pc)}"
                break
            pc = nxt
        if stop is None:
            stop = f"UNRESOLVED:{hex(pc)}"
        out[ability_type] = stop
    return out


def _prologue_presets(native, kind):
    """``{'w23': 1, ...}`` for every ``mov wN/xN, #1`` in the function prologue."""
    cfg = FUNCS[kind]
    regs = {}
    for ins in DIS.disasm(native.raw[cfg["entry"]:cfg["head"]], cfg["entry"]):
        if ins.mnemonic == "mov" and re.match(r"^[wx]\d+, #(?:1|0x1)$", ins.op_str):
            regs[ins.op_str.split(",")[0]] = 1
    return regs


# ---------------------------------------------------------------------------
# item 2: is there a read path for a slot that the five indexed paths miss?
# ---------------------------------------------------------------------------
def owner_of(native, rva):
    """(method entry RVA, method dicts) for the method containing ``rva``."""
    addrs = sorted(set(native.pointers))
    i = bisect.bisect_right(addrs, rva) - 1
    entry = addrs[i]
    return entry, [native.method(j) for j in native.method_by_rva.get(entry, [])]


def slot_readers(native, slot_rva):
    """Every call site of ``skillParameter.get_paramN`` (image-wide BL scan)."""
    sites = []
    for off in range(0, len(native.raw) - 4, 4):
        w = struct.unpack_from("<I", native.raw, off)[0]
        if w >> 26 != 0b100101:
            continue
        imm = w & 0x3FFFFFF
        if imm & 0x2000000:
            imm -= 0x4000000
        if off + imm * 4 == slot_rva:
            sites.append(off)
    return sites


def unindexed_reader_evidence(native):
    """Two bounded questions, both answered from the image.

    1. Of the functions that switch on ``get_ability`` (the only ones that can be
       type-dispatched), does a *type-8* record's branch read ``param4`` or ``param0``?
       Every such function is resolved for type 8 and its branch's slot list read.
    2. Are there readers of ``param4`` that do **not** switch on the ability type?
       Those cannot be excluded by a type-based index and are listed with the call site.
    """
    # switchers: every get_ability call site, with its owner
    switchers = {}
    for off in range(0, len(native.raw) - 4, 4):
        w = struct.unpack_from("<I", native.raw, off)[0]
        if w >> 26 != 0b100101:
            continue
        imm = w & 0x3FFFFFF
        if imm & 0x2000000:
            imm -= 0x4000000
        if off + imm * 4 != GET_ABILITY:
            continue
        entry, _ = owner_of(native, off)
        switchers.setdefault(entry, []).append(off)

    resolver = Resolver(native)
    type8_hits = []
    resolver_targets = {k: v for k, v in FUNCS.items()}
    checked = 0
    for entry, sites in sorted(switchers.items()):
        end = min([p for p in native.pointers if p > entry], default=len(native.raw))
        for site in sites:
            head = site + 4
            if not (entry <= head < end):
                continue
            checked += 1
            leaf = resolve_generic(resolver, head, end, 8)
            if not isinstance(leaf, int):
                continue
            if leaf == generic_tail(native, head, end):
                continue
            fields = branch_fields(native, leaf, end)
            if "param4" in fields or "param0" in fields:
                names = [m["declaring_type"] + "." + m["name"]
                         for m in (native.method(j) for j in native.method_by_rva.get(entry, []))]
                type8_hits.append({"owner_rva": hex(entry), "owner": names,
                                   "site": hex(site), "leaf": hex(leaf), "fields": fields})

    # non-dispatched readers of param4
    readers = []
    for site in slot_readers(native, 0x1DBCF84):
        entry, _ = owner_of(native, site)
        if entry in switchers and any(entry <= s < site for s in switchers[entry]):
            # the read may still sit outside the switch branch; keep it, flagged
            readers.append({"site": hex(site), "owner_rva": hex(entry),
                            "owner": [m["declaring_type"] + "." + m["name"]
                                      for m in (native.method(j)
                                                for j in native.method_by_rva.get(entry, []))],
                            "in_a_type_switching_owner": True})
        else:
            readers.append({"site": hex(site), "owner_rva": hex(entry),
                            "owner": [m["declaring_type"] + "." + m["name"]
                                      for m in (native.method(j)
                                                for j in native.method_by_rva.get(entry, []))],
                            "in_a_type_switching_owner": False})
    non_switching = [r for r in readers if not r["in_a_type_switching_owner"]]
    return {
        "type_switching_functions_checked": checked,
        "type8_branches_reading_param4_or_param0": type8_hits,
        "param4_readers_total": len(readers),
        "param4_readers_not_in_a_type_switcher": non_switching[:20],
        "param4_readers_not_in_a_type_switcher_count": len(non_switching),
    }


def resolve_generic(resolver, head, end, ability_type):
    """Resolve a switch head that has no declared leaf list (block tracking only)."""
    cfg = {"head": head, "entry": head, "tail": None,
           "terminals": set()}
    targets = set()
    for ins in DIS.disasm(resolver.n.raw[head:end], head):
        if (ins.mnemonic == "b" or ins.mnemonic.startswith("b.")) and ins.op_str.startswith("#0x"):
            t = int(ins.op_str[1:], 16)
            if head <= t < end:
                targets.add(t)
    cfg["terminals"] = {t for t in targets if not is_pure(first_insn(resolver.n, t))}
    st = {"block": head, "new": False}
    hit = {"rva": None}

    def hook(u, addr, sz, data):
        rva = addr - BASE
        if st["new"]:
            st["block"] = rva
        ins = first_insn(resolver.n, rva)
        if rva in cfg["terminals"] or not is_pure(ins):
            hit["rva"] = st["block"]
            u.emu_stop()
            return
        st["new"] = (ins.mnemonic == "b" or ins.mnemonic.startswith("b."))
    h = resolver.uc.hook_add(UC_HOOK_CODE, hook)
    resolver.uc.reg_write(UC_ARM64_REG_X0, ability_type)
    try:
        resolver.uc.emu_start(BASE + head, 0, count=128)
    except Exception:
        hit["rva"] = None
    resolver.uc.hook_del(h)
    return hit["rva"]


def generic_tail(native, head, end):
    for ins in DIS.disasm(native.raw[head:end], head):
        if ins.mnemonic == "add" and ins.op_str.startswith("w") and ", #1" in ins.op_str:
            nxt = list(DIS.disasm(native.raw[ins.address:ins.address + 12], ins.address))
            if len(nxt) >= 3 and nxt[1].mnemonic == "cmp" and nxt[2].mnemonic == "b.ne":
                return ins.address
    return None


def branch_fields(native, leaf, end):
    out = []
    for ins in DIS.disasm(native.raw[leaf:min(leaf + 0x400, end)], leaf):
        if ins.mnemonic == "bl" and ins.op_str.startswith("#0x"):
            t = int(ins.op_str[1:], 16)
            for j in native.method_by_rva.get(t, []):
                nm = native.method(j)
                cand = f"{nm['declaring_type']}.{nm['name']}"
                if cand in GETTERS and GETTERS[cand] not in out:
                    out.append(GETTERS[cand])
        if ins.mnemonic == "b" and ins.op_str.startswith("#0x"):
            break
    return out


# ---------------------------------------------------------------------------
# the new rules (field_dictionary shape used by the existing rule sources)
# ---------------------------------------------------------------------------
# every ability type that has a critical-accumulator branch (1036 included: it has a
# branch but no records; the low types 1/2/6/7/34 gained rules in the p2b3 rectification)
CRIT_TYPES_ALL = (1, 2, 3, 6, 7, 34, 36, 1003, 1005, 1026, 1036)
# branches that read one slot but scale it by a runtime int before accumulating
# (``param × int([BattleParam+0x328]) / 1000``) -- a plain slot rule would be wrong
SCALED_CRIT_TYPES = {1036}
CRIT_PATH_LABEL = {"crit_rate": ("暴击率", "百分点（原值×100）",
                                 "暴击率 += SN ×100 个百分点；本路径汇总后夹在 [0, 0.5]"),
                   "crit_dmg": ("暴击伤害系数", "系数增量",
                                "暴伤系数 += SN（不减 1.5 基准）；本路径汇总后夹在 [-1, 2]")}


def crit_rule_rows(maps):
    """Crit rules derived from the corrected dispatch map (data-driven, cannot go stale).

    A row is emitted for every single-slot, IsEnableAbility-gated branch that reaches the
    shared ``fadd``. The slot name differs per type (``param4``/``param5``/``param6`` on the
    rate path, ``param5``/``param6``/``param7`` on the damage path), which is exactly why
    the rule is keyed by (type, field) and never by field alone.
    """
    rows = []
    for path in ("crit_rate", "crit_dmg"):
        label, unit, rule = CRIT_PATH_LABEL[path]
        for t, entry in sorted(maps[path].items(), key=lambda kv: kv[0]):
            slots = entry.get("slots") or []
            if entry.get("neutral") or len(slots) != 1:
                continue
            if not entry.get("gated_by_isenable") or not entry.get("reaches_accumulate_op"):
                continue
            if t in SCALED_CRIT_TYPES:
                continue
            field = slots[0]
            slot_rva = next((c["rva"] for c in entry.get("slot_calls") or []
                             if c["field"] == field), None)
            rows.append(dict(
                file_table=f"skilllist.ability{t}", table="skilllist", effect_type=t,
                field_path=f"/{field}", answer_kind=path,
                meaning_zh=(f"{label}加算贡献（对{label}加算的增量，不是相对提高）"),
                unit=unit,
                rule=rule.replace("SN", field),
                status=("已确认数值换算（加算路径与夹紧范围原生核实）"
                        + ("；该 type 记录中此槽非零值 0 条，答案为 +0（中性）"
                           if _crit_slot_nonzero(t, field) == 0 else "")),
                condition=("type 记录装载且 IsEnableAbility 通过；只在"
                           + ("暴击率" if path == "crit_rate" else "暴击伤害") + "累加路径上成立"),
                evidence=[f"GetAbility{'Critical' if path == 'crit_rate' else 'CriticalDmgRate'} "
                          f"分支 {entry['leaf']}（gate {entry.get('gate_rva')}，"
                          f"slot 读取 {slot_rva}）：IsEnableAbility → get_{field} → fadd",
                          "scripts/character_skills/skilllist_types.py",
                          "output/character_skills/skilllist_types/dispatch_map.json"]))
    return rows


def _crit_slot_nonzero(ability_type, field):
    rows = C.cache_rows("skilllist") + C.apk_rows("skilllist")
    return sum(1 for r in rows if r.get("ability") == ability_type and r.get(field))


# types that share the *very same* single-slot branch as type 8 on the attack / move /
# damage-taken paths (verified against dispatch_map: identical leaf, gate and slot rva)
SAME_LEAF_AS_TYPE8 = (36, 1003, 1005, 1026)
SAME_LEAF_FIELDS = (("attack", "/param1", "attack_mult"), ("move", "/param2", "move_mult"),
                    ("defence", "/param3", "take_mult"))


def same_leaf_as_type8_rows(maps):
    """Rows for types whose branch is literally type 8's -- emitted only when the map says so.

    The type-8 rule text is reused verbatim (same leaf, same slot, same conversion); the
    evidence records the branch address so the claim is checkable rather than assumed.
    """
    rows = []
    for t in SAME_LEAF_AS_TYPE8:
        for path, field, kind in SAME_LEAF_FIELDS:
            here, base = maps[path][t], maps[path][8]
            if here.get("neutral") or here["leaf"] != base["leaf"]                     or here["slots"] != base["slots"] or here["slots"] != [field.lstrip("/")]:
                continue
            slot_rva = next((c["rva"] for c in here.get("slot_calls") or []
                             if c["field"] == field.lstrip("/")), None)
            rows.append(dict(
                file_table=f"skilllist.ability{t}", table="skilllist", effect_type=t,
                field_path=field, answer_kind=kind,
                meaning_zh={
                    "attack_mult": "本项攻击乘数（与 type 8 同一分支）",
                    "move_mult": "移动速度乘数（与 type 8 同一分支）",
                    "take_mult": ("本项受伤量乘数（正文写作「防御」；乘进受伤量因子，"
                                  "不是固定防御量；与 type 8 同一分支）"),
                }[kind],
                unit={"attack_mult": "无量纲倍率", "move_mult": "速度倍率",
                      "take_mult": "无量纲倍率"}[kind],
                rule={"attack_mult": "本项攻击 +(param1-1)×100%（乘进自身攻击因子）",
                      "move_mult": "移动速度 ×param2",
                      "take_mult": "本项减伤 (1-param3)×100%（param3>1 时为负减伤即增伤）"}[kind],
                status="已确认数值换算；分支与 type 8 同叶同槽，规则复用",
                condition=("type 记录装载且 IsEnableAbility 通过；"
                           + {"attack_mult": "乘进自身攻击因子",
                              "move_mult": "乘进移动速度因子",
                              "take_mult": "乘进受伤量因子"}[kind]),
                evidence=[f"dispatch_map 的 {path} 路径 type {t} 与 type 8 同为分支 {here['leaf']}"
                          f"（gate {here.get('gate_rva')}、{field.lstrip('/')} 读取 {slot_rva}）",
                          "scripts/character_skills/skilllist_types.py",
                          "output/character_skills/skilllist_types/dispatch_map.json",
                          "换算复用 type 8（其依据见 ordinary_effects/ability7）"]))
    return rows


# ---------------------------------------------------------------------------
# P2 batch 5: the composite branches (types 67 / 80 / 96 / 1036)
# ---------------------------------------------------------------------------
# These four types do not fall on a single-slot branch. On one apply path the compiler
# merged 67/80/96 into *one* worker region that the three leaves enter at different
# labels, so a linear scan of a leaf cannot show its chain; the walk below follows every
# branch inside the function instead. 1036 is a separate single-slot branch that scales
# its parameter by the character's hyper gauge.
COMPOSITE_TYPES = (67, 80, 96, 1036)
CALC_CHARA_NUM = 0x1113C8C
MANA_JOB_OR = 0x124320C
MANA_JOB_AND = 0x1242FAC
MANA_CURRENT = 0x1242CD8
MANA_SCRAP = 0x1242DF0            # GetCurrentScrapManaNum = mov w1,#0x20; b MANA_CURRENT
SCRAP_MANA_FLAG = 0x20
PARAM_INT_VALUE = 0xA92534
HYPER_GAUGE_OFFSET = 0x328
HYPER_GAUGE_GETTER = 0x10F3C10       # BattleParam.get_hyperGauge -> [this+0x328].get_Value()
HYPER_DIVISOR = 1000.0               # 0x447a0000
CHAIN_HELPERS = {
    CALC_CHARA_NUM: "BattleParam.CalcCharaNum",
    MANA_JOB_OR: "PanelManaGage.isCurrentManaJob_or",
    MANA_JOB_AND: "PanelManaGage.isCurrentManaJob_and",
    MANA_CURRENT: "PanelManaGage.GetCurrentManaNum",
    MANA_SCRAP: "PanelManaGage.GetCurrentScrapManaNum",
    PARAM_INT_VALUE: "ParamS_int.get_Value",
    0x1243148: "PanelManaGage.CountManaByColor",
    ISENABLE: "BattleParam.IsEnableAbility",
    0x10BD338: "BattleManager.GetMemberList",
    0x15787E4: "Constants.ConvJobFlagToElementFlag",
    0xA928D8: "ParamS_long.get_Value",
    0x1113958: "BattleParam.IsTargetHome",
}
# (path -> field, answer_kind) per type. 96's attack branch reads param2 *and* param3 in
# one body; the coefficient is selected at run time by the caller-level flag
# [sp+0x18] == (eDamageType damageType == 1 Skill), so both slots are listed with their
# own condition (P2 batch 6).
COMPOSITE_FIELDS = {
    67: {"attack": ("param1", "attack_mult"), "move": ("param2", "move_mult"),
         "defence": ("param3", "take_mult"), "crit_rate": ("param6", "crit_rate"),
         "crit_dmg": ("param7", "crit_dmg")},
    80: {"attack": ("param1", "attack_mult"), "move": ("param2", "move_mult"),
         "defence": ("param3", "take_mult"), "crit_rate": ("param7", "crit_rate"),
         "crit_dmg": ("param8", "crit_dmg")},
    96: {"attack": [("param2", "mana_coeff_attack_nonskill"),
                    ("param3", "mana_coeff_attack_skill")],
         "move": ("param4", "mana_coeff_move"), "defence": ("param5", "mana_coeff_take"),
         "crit_rate": ("param6", "mana_coeff_crit_rate"),
         "crit_dmg": ("param7", "mana_coeff_crit_dmg")},
    1036: {"attack": ("param1", "hyper_attack_mult"),
           "move": ("param2", "hyper_move_mult"),
           "defence": ("param3", "hyper_take_mult"),
           "crit_rate": ("param4", "hyper_crit_rate"),
           "crit_dmg": ("param5", "hyper_crit_dmg")},
}
# non-multiplier slots that still carry a single numeric meaning
COMPOSITE_EXTRA_FIELDS = {
    67: [("param0", "chara_count_threshold")],
    80: [("param0", "mana_count_threshold"), ("param6", "mana_selector")],
    96: [("param1", "mana_count_cap")],
}
COMPOSITE_TYPE_NAMES = {67: "HeroOne", 80: "HoldMana", 96: "ManaCountUp", 1036: "HyperModeUp"}
COMPOSITE_CONDITIONS = {
    67: ("命中角色数 >= int(param0)：count = CalcCharaNum(cType, 职业位图=iParam0, "
         "武器位图=_flag 低 32 位（记录字段 flag0_0，掩码 0x7fc00000=bit22..30）, "
         "出身筛选=int(param8), 成员列表)，只统计存活且三项筛选都命中的角色；"
         "比较为含等于（cmp w0,w19; b.lt 跳过）"),
    80: ("当前玛那条件成立：isCurrentManaJob_or/and(job_flag=iParam0, num=int(param0))；"
         "param6 为有限值且 int(param6)==0 时用 or（任一命中），否则用 and（全部命中）；"
         "iParam0==0 时比较当前玛那总数；比较为含等于"),
    96: ("计数对象由 int(param0) 选择：int(param0)==0 → 斯库拉普玛那"
         "（PanelManaGage.GetCurrentScrapManaNum 0x1242df0 ＝ 标志 0x20 的 "
         "GetCurrentManaNum），否则（含 param0 为 +inf）→ 按 iParam0 经 "
         "Constants.ConvJobFlagToElementFlag 选取的当前玛那；两条路径共用后续："
         "计数 >= 1 才生效，并按 min(计数, int(param1)) 计入，int(param1) < 1 时不设上限"),
    1036: "type 记录装载且 IsEnableAbility 通过；本项随角色 hyperGauge 变化",
}


def enum_values(native, md, type_name):
    """``name -> value`` for a metadata enum, read from the field default table."""
    out = {}
    if md is None:
        return out
    for ti, row in enumerate(md.types):
        if md.string(row[0]) != type_name:
            continue
        for f in native.fields(ti):
            if f["name"] == "value__":
                continue
            try:
                out[f["name"]] = native.default(f["index"])["value"]
            except Exception:
                out[f["name"]] = None
        break
    return out


def callers_of(native, targets):
    """Every ``bl`` in a known method body that targets one of ``targets``.

    Bounded linear sweep of the recovered image's method entries; used to prove which
    call sites pass which argument (e.g. the damageType of GetAbilityAttack).
    """
    tset = set(targets)
    ptrs = sorted(set(p for p in native.pointers if p))
    out = []
    for i, a in enumerate(ptrs):
        b = ptrs[i + 1] if i + 1 < len(ptrs) else len(native.raw)
        if b - a > 0x40000:
            continue
        for ins in DIS.disasm(native.raw[a:b], a):
            if ins.mnemonic == "bl" and ins.op_str.startswith("#"):
                t = int(ins.op_str[1:], 0)
                if t in tset:
                    out.append((ins.address, ins.mnemonic, t, a))
    return out


def func_bounds(native, rva):
    """(start, end) of the method containing ``rva``, from the native pointer array."""
    ptrs = sorted(set(native.pointers))
    i = bisect.bisect_right(ptrs, rva) - 1
    start = ptrs[i]
    end = ptrs[i + 1] if i + 1 < len(ptrs) else len(native.raw)
    return start, end


def reachable_body(native, kind, leaf, max_nodes=4000):
    """Every instruction reachable from ``leaf`` within its own function.

    Branch bodies on these paths are merged by the compiler (67/80/96 enter one worker
    at different labels), so this follows both targets of every conditional branch and
    stops at the path's loop tail / shared accumulate tail, treating calls as call sites.
    """
    lo, end = func_bounds(native, leaf)
    stop = {NEUTRAL[kind], TAIL_MUL[kind]}
    todo, seen, calls, terminals = [leaf], {}, [], []
    while todo:
        addr = todo.pop()
        if addr in seen or not (lo <= addr < end) or len(seen) > max_nodes:
            continue
        insn = next(iter(DIS.disasm(native.raw[addr:addr + 4], addr)), None)
        if insn is None:
            continue
        seen[addr] = insn
        if addr in stop:
            terminals.append(insn)
            continue
        m, op = insn.mnemonic, insn.op_str
        if m in ("ret", "br", "brk") or m == "bx":
            terminals.append(insn)
            continue
        if m == "bl":
            calls.append(insn)
            todo.append(addr + 4)
            continue
        if m == "b":
            if op.startswith("#"):
                todo.append(int(op[1:], 0))
            else:
                terminals.append(insn)
            continue
        if m.startswith("b.") or m in ("cbz", "cbnz", "tbz", "tbnz"):
            tgt = None
            for tok in op.split(","):
                tok = tok.strip()
                if tok.startswith("#") and ("0x" in tok or tok[1:].isdigit()):
                    tgt = int(tok[1:], 0)
            if tgt is not None:
                todo.append(tgt)
            todo.append(addr + 4)
            continue
        todo.append(addr + 4)
    return seen, calls, terminals


def chain_events(native, kind, leaf):
    """Ordered evidence for one composite branch: slots read, helpers called, the
    accumulate site, the compare/branch pairs that gate it, and the float maths."""
    seen, calls, terminals = reachable_body(native, kind, leaf)
    out = {"leaf": hex(leaf), "instructions": len(seen), "slots": [], "helpers": [],
           "accumulate": None, "compares": [], "float_ops": [], "terminals": [],
           "gauge_loads": [], "scrap_flag_sites": []}
    acc = ACCUM_OP[kind].replace(" ", "")
    for addr in sorted(seen):
        insn = seen[addr]
        text = (insn.mnemonic + " " + insn.op_str).replace(" ", "")
        if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
            tgt = int(insn.op_str[1:], 0)
            nm = None
            for j in native.method_by_rva.get(tgt, []):
                m = native.method(j)
                nm = m["declaring_type"] + "." + m["name"]
                break
            if nm in GETTERS:
                out["slots"].append({"field": GETTERS[nm], "rva": hex(addr)})
            elif tgt in CHAIN_HELPERS:
                out["helpers"].append({"name": CHAIN_HELPERS[tgt], "rva": hex(addr),
                                       "target": hex(tgt)})
        if text == acc:
            out["accumulate"] = {"rva": hex(addr), "op": ACCUM_OP[kind]}
        if insn.mnemonic in ("cmp", "fcmp", "ccmp", "tst"):
            nxt = seen.get(addr + 4)
            if nxt is not None and (nxt.mnemonic.startswith("b.")
                                    or nxt.mnemonic in ("cbz", "cbnz", "tbz", "tbnz")):
                out["compares"].append({"rva": hex(addr),
                                        "test": insn.mnemonic + " " + insn.op_str,
                                        "branch": nxt.mnemonic + " " + nxt.op_str,
                                        "branch_rva": hex(addr + 4)})
        if insn.mnemonic in ("fmul", "fadd", "fdiv", "scvtf", "fcvtzs"):
            out["float_ops"].append({"rva": hex(addr),
                                     "op": insn.mnemonic + " " + insn.op_str})
        if ("#0x%x]" % HYPER_GAUGE_OFFSET) in insn.op_str:
            out["gauge_loads"].append({"rva": hex(addr),
                                       "op": insn.mnemonic + " " + insn.op_str})
        # type 96 selects its counting object here: mov w1,#0x20 is the scrap-mana flag
        if insn.mnemonic == "mov" and insn.op_str.replace(" ", "") == "w1,#0x%x" % SCRAP_MANA_FLAG:
            out["scrap_flag_sites"].append({"rva": hex(addr),
                                            "op": insn.mnemonic + " " + insn.op_str})
    for t in terminals:
        out["terminals"].append({"rva": hex(t.address), "op": t.mnemonic + " " + t.op_str})
    return out


# answer_kind -> (label, unit) and the rule text; the *kind* drives the wording because
# the mana / hyper coefficients also sit on the multiplicative paths, so a path-driven
# table cannot cover them (96's move/defence coefficients are multipliers, its crit ones
# addends; 1036 spreads over all five paths).
KIND_META = {
    "attack_mult": ("本项攻击乘数", "无量纲倍率"),
    "move_mult": ("移动速度乘数", "速度倍率"),
    "take_mult": ("本项受伤量乘数", "无量纲倍率"),
    "crit_rate": ("暴击率加算贡献", "百分点（原值×100）"),
    "crit_dmg": ("暴击伤害系数加算贡献", "系数增量"),
    "mana_coeff_move": ("移动速度乘数（玛那计数项）", "速度倍率"),
    "mana_coeff_attack_nonskill": ("本项攻击倍率（玛那计数项；非 Skill 伤害时）", "无量纲倍率"),
    "mana_coeff_attack_skill": ("本项攻击倍率（玛那计数项；Skill 必杀技伤害时）", "无量纲倍率"),
    "mana_coeff_take": ("本项受伤量乘数（玛那计数项）", "无量纲倍率"),
    "mana_coeff_crit_rate": ("暴击率加算贡献（玛那计数项）", "百分点（原值×100，另乘玛那计数因子）"),
    "mana_coeff_crit_dmg": ("暴击伤害系数加算贡献（玛那计数项）", "系数增量（另乘玛那计数因子）"),
    "hyper_attack_mult": ("本项攻击倍率（hyper 项）", "无量纲倍率"),
    "hyper_move_mult": ("移动速度倍率（hyper 项）", "速度倍率"),
    "hyper_take_mult": ("本项受伤量倍率（hyper 项）", "无量纲倍率"),
    "hyper_crit_rate": ("暴击率加算贡献（hyper 项）", "百分点（原值×100，另乘 hyperGauge）"),
    "hyper_crit_dmg": ("暴击伤害系数加算贡献（hyper 项）", "系数增量（另乘 hyperGauge）"),
}
KIND_RULE = {
    "attack_mult": "本项攻击 ×{f}（条件成立时乘进自身攻击因子）",
    "move_mult": "移动速度 ×{f}（条件成立时）",
    "take_mult": "本项受伤量 ×{f}（条件成立时；不是固定防御量）",
    "crit_rate": "暴击率 += {f} ×100 个百分点（条件成立时）",
    "crit_dmg": "暴击伤害系数 += {f}（条件成立时）",
    "mana_coeff_move": "移动速度 ×(1 + {f} × min(玛那计数, param1))（计数对象见条件：int(param0)==0 为斯库拉普玛那）",
    "mana_coeff_attack_nonskill": ("本项攻击 ×(1 + {f} × min(玛那计数, param1))；仅当本次伤害类型 "
                                   "≠ eDamageType.Skill(=1)（非必杀技伤害）时生效"),
    "mana_coeff_attack_skill": ("本项攻击 ×(1 + {f} × min(玛那计数, param1))；仅当本次伤害类型 "
                                "== eDamageType.Skill(=1)（必杀技伤害）时生效"),
    "mana_coeff_take": "本项受伤量 ×(1 + {f} × min(玛那计数, param1))（计数对象见条件：int(param0)==0 为斯库拉普玛那）",
    "mana_coeff_crit_rate": "暴击率 += {f} × min(玛那计数, param1) ×100 个百分点（计数对象见条件：int(param0)==0 为斯库拉普玛那）",
    "mana_coeff_crit_dmg": "暴击伤害系数 += {f} × min(玛那计数, param1)（计数对象见条件：int(param0)==0 为斯库拉普玛那）",
    "hyper_attack_mult": "本项攻击 ×(1 + {f} × hyperGauge ÷ 1000)",
    "hyper_move_mult": "移动速度 ×(1 + {f} × hyperGauge ÷ 1000)",
    "hyper_take_mult": "本项受伤量 ×(1 + {f} × hyperGauge ÷ 1000)",
    "hyper_crit_rate": "暴击率 += {f} × hyperGauge ÷ 1000 ×100 个百分点",
    "hyper_crit_dmg": "暴击伤害系数 += {f} × hyperGauge ÷ 1000",
}


COMPOSITE_FIELD_CONDITION = {
    (96, "param2"): ("攻击路径的系数选择（RVA 0x1107c48）：BattleParam.GetAbilityAttack 的序言按 "
                     "第 4 个实参 damageType（eDamageType）走两条基础缩放路径；只有 "
                     "damageType==1（Skill）走扩展路径并把 [sp+0x18] 置 1。该分支因此按 "
                     "damageType 择槽：!=Skill 读 param2（本行），==Skill 读 param3"),
    (96, "param3"): ("攻击路径的系数选择（RVA 0x1107c48）：damageType==1（eDamageType.Skill）时 "
                     "读 param3（本行），其余伤害类型读 param2。两条路径的调用方已核实："
                     "CharaBehavior.Attack 把当次伤害类型透传；BattleParam.UpdateParam 固定传 0"),
}
COMPOSITE_FIELD_LIMITS = {
    (96, "param2"): ("槽的选择条件来自调用方实参 damageType，不是本记录自身的字段；"
                     "记录只有受到某种伤害类型时才用该槽"),
    (96, "param3"): ("槽的选择条件来自调用方实参 damageType，不是本记录自身的字段；"
                     "记录只有受到某种伤害类型时才用该槽"),
}


def _composite_field_specs(t):
    """``path -> [(field, answer_kind), ...]``; a single tuple means one slot."""
    out = {}
    for path, spec in COMPOSITE_FIELDS[t].items():
        out[path] = [spec] if isinstance(spec, tuple) else list(spec)
    return out


def composite_rule_rows(native, maps):
    """Field rows for 67 / 80 / 96 / 1036, emitted only when the branch re-reads verify.

    Every row is gated on the *recovered branch itself*: the field must be one of the
    get_paramN calls reachable from that branch, and the branch must reach the path's
    accumulate site. A stale or over-broad table therefore cannot produce a row.
    """
    rows = []
    for t in COMPOSITE_TYPES:
        for path, specs in _composite_field_specs(t).items():
            entry = maps[path].get(t) or {}
            if entry.get("neutral") or not entry.get("leaf"):
                continue
            leaf = int(entry["leaf"], 16)
            ev = chain_events(native, path, leaf)
            acc = ev.get("accumulate") or {}
            for field, kind in specs:
                slot = next((s for s in ev["slots"] if s["field"] == field), None)
                if slot is None:
                    continue
                meta = KIND_META.get(kind)
                if meta is None:
                    continue
                label, unit = meta
                value_rule = KIND_RULE[kind].replace("{f}", field)
                extra = COMPOSITE_FIELD_CONDITION.get((t, field))
                rows.append(dict(
                    file_table="skilllist.ability" + str(t), table="skilllist", effect_type=t,
                    field_path="/" + field, answer_kind=kind,
                    meaning_zh=(label + "（" + COMPOSITE_TYPE_NAMES[t] + "，复合分支；与 type 8 不同叶）"),
                    unit=unit, rule=value_rule,
                    status=("已确认数值换算（分支体与喂入路径原生核实）" if t != 96 else
                            "已确认数值换算（系数槽、上限槽与攻击路径择槽条件均原生核实）"),
                    condition=(COMPOSITE_CONDITIONS[t] + ("；" + extra if extra else "")),
                    evidence=["分支 " + entry["leaf"] + "：get_" + field + " @ " + slot["rva"]
                              + ((" → 累加 " + str(acc.get("op")) + " @ " + str(acc.get("rva")))
                                 if acc else " → 条件满足后写入累加器"),
                              "scripts/character_skills/skilllist_types.py（composite_rule_rows 由分支可达体重算）",
                              "output/character_skills/skilllist_types/dispatch_map.json",
                              "output/character_skills/skilllist_types/composite_chains.json"],
                    limits=COMPOSITE_FIELD_LIMITS.get((t, field))))
        for field, kind in COMPOSITE_EXTRA_FIELDS.get(t, []):
            ev = None
            for path, per in maps.items():
                e = per.get(t) or {}
                if e.get("neutral") or not e.get("leaf"):
                    continue
                cand = chain_events(native, path, int(e["leaf"], 16))
                if any(s["field"] == field for s in cand["slots"]):
                    ev = cand
                    break
            if ev is None:
                continue
            slot = next(s for s in ev["slots"] if s["field"] == field)
            rows.append(dict(
                file_table="skilllist.ability" + str(t), table="skilllist", effect_type=t,
                field_path="/" + field, answer_kind=kind,
                meaning_zh={
                    "chara_count_threshold": "触发所需命中角色数（含等于）",
                    "mana_count_threshold": "触发所需的当前玛那数量（含等于）",
                    "mana_selector": "玛那条件的组合语义选择码",
                    "mana_count_cap": "计入项数上限（与玛那计数取较小者；计数对象见条件）",
                }[kind],
                unit={"chara_count_threshold": "个（int 向零截断）",
                      "mana_count_threshold": "个（int 向零截断）",
                      "mana_selector": "选择码（int 向零截断）",
                      "mana_count_cap": "个（int 向零截断）"}[kind],
                rule={
                    "chara_count_threshold": "命中角色数 >= int(param0) 时本项才生效",
                    "mana_count_threshold": "当前玛那（按 iParam0 职业位图选取）>= int(param0) 时本项才生效",
                    "mana_selector": "int(param6)==0 → 任一命中职业满足即可（or）；非 0 → 所有命中职业都要满足（and）",
                    "mana_count_cap": ("本项按 min(玛那计数, int(param1)) 计入；int(param1)<1 时"
                                       "不设上限（按计数结果计入，不是按 0 计）——本快照无记录触发该分支"),
                }[kind],
                status="已确认数值换算（分支体原生核实）",
                condition=COMPOSITE_CONDITIONS[t],
                evidence=["分支 " + ev["leaf"] + "：get_" + field + " @ " + slot["rva"],
                          "scripts/character_skills/skilllist_types.py",
                          "output/character_skills/skilllist_types/composite_chains.json"]))
    return rows


# ---------------------------------------------------------------------------
# P2 batch 6: filter slots + type 1059 UnionCount
# ---------------------------------------------------------------------------
# The three filters a count condition can use. 67's count (CalcCharaNum) requires all
# three; 1059's count (IsEnableAbility case 0x423) requires any one of them. The weapon
# word read natively is skillParameter._flag@0x90 / _flag1@0x98; the export splits each
# 64-bit word into a low/high pair, and the weapon bits (22..30) all live in the low word.
FILTER_SLOT_RULES = {
    67: [("iParam0", "job_bitmap", "命中计数用的职业位图（CalcCharaNum 的 paramJob）"),
         ("flag0_0", "weapon_bitmap",
          "命中计数用的武器位图（CalcCharaNum 的 wepFlags＝skillParameter._flag@0x90 的低 32 位）"),
         ("param8", "home_filter", "命中计数用的出身筛选值（IsTargetHome 的 targetHome）")],
    80: [("iParam0", "job_bitmap", "玛那谓词的职业位图（isCurrentManaJob_or/and 的 job_flag）")],
    96: [("iParam0", "job_bitmap",
          "计数对象选取用的职业位图（经 ConvJobFlagToElementFlag 取属性玛那）")],
}
UNION_COUNT = 1059
UNION_COUNT_FILTER_SLOTS = [
    ("iParam0", "job_bitmap", "计数筛选用的职业位图（任一命中即计入）"),
    ("flag0_0", "weapon_bitmap", "计数筛选用的武器位图（任一命中即计入）"),
    ("param8", "home_filter", "计数筛选用的出身筛选值（任一命中即计入）"),
    ("iParam1", "job_bitmap", "受益对象筛选用的职业位图（回复/加成的对象）"),
    ("flag1_0", "weapon_bitmap", "受益对象筛选用的武器位图（回复/加成的对象）"),
    ("param9", "home_filter", "受益对象筛选用的出身筛选值（回复/加成的对象）"),
]
UNION_COUNT_FIELDS = [
    ("param0", "union_count_threshold"),
    ("param1", "union_atk_mult"),
    ("param2", "union_move_mult"),
    ("param3", "union_take_mult"),
    ("param4", "union_crit_rate"),
    ("param5", "union_crit_dmg"),
    ("param6", "union_heal_coeff"),
    ("param7", "union_heal_interval"),
]
UNION_COUNT_KIND_TEXT = {
    "union_count_threshold": ("触发所需命中角色数（任一命中即计入，含等于）", "个（int 向零截断）",
                              "满足任一筛选的存活角色数 >= int(param0) 时本项才生效"),
    "union_atk_mult": ("队伍攻击倍率", "无量纲倍率", "队伍攻击率 ×param1（条件成立时）"),
    "union_move_mult": ("移动速度倍率", "速度倍率", "移动速度 ×param2（条件成立时）"),
    "union_take_mult": ("受伤量倍率", "无量纲倍率",
                        "受伤量 ×param3（条件成立时；不是固定防御量）"),
    "union_crit_rate": ("暴击率加算贡献", "百分点（原值×100）", "暴击率 += param4 ×100 个百分点"),
    "union_crit_dmg": ("暴击伤害系数加算贡献", "系数增量", "暴击伤害系数 += param5"),
    "union_heal_coeff": ("周期回复量系数", "系数（×目标最大HP）",
                         "每触发一次回复 int(param6 × 目标最大HP)（向零截断）"),
    "union_heal_interval": ("周期回复间隔", "游戏秒", "回复间隔 param7 游戏秒"),
}
UNION_COUNT_CONDITION = (
    "type 1059 的两段机制共用同一个计数条件：BattleParam.IsEnableAbility 的 case 0x423 用 "
    "BattleManager.GetAllCharaList 取战场角色列表，逐个要求（0x1eb8358 排除）→ IsAlive → "
    "[chara+0x118]!=0，再按 **任一** 命中计数：职业位图 iParam0（1<<([chara+0x28]+0xf8) 职业 id）、"
    "武器位图 _flag（[chara+0x28]+0x1b0 的 ParamS_long）、出身 int(param8)（BattleParam.IsTargetHome）；"
    "特例域是「iParam0 与 int(param8) 均不为正」（原生为 cmp #0／b.gt，即 ≤0；现有记录两字段均为非负，"
    "等价于 ==0）：此时引擎另要求 _flag 与全体武器掩码有交集；计数 >= int(param0) 才生效，"
    "比较为含等于（cmp w28,w8 → cset ge）。修正是关键的：67 的同名三项是**同时**满足（并），"
    "1059 是**任一**满足（或）")


def _linear(native, rva, n):
    return list(DIS.disasm(native.raw[rva:rva + 4 * n], rva))


def _named_call(native, insn):
    if insn is None or insn.mnemonic != "bl" or not insn.op_str.startswith("#"):
        return None
    t = int(insn.op_str[1:], 0)
    idx = native.method_by_rva.get(t)
    if not idx:
        return None
    return _md_global.method(idx[0])["declaring_type"] + "." + _md_global.method(idx[0])["name"]


# ``composite_checks`` and the evidence writers need the metadata reader; the module
# keeps the last loaded one so helpers do not have to thread it through every call.
_md_global = None


def union_count_evidence(native, md):
    """Recompute the whole type-1059 chain from the image; every claim is a re-read.

    Returns a dict with the four segments (gate / setup / apply / player-side consumers)
    plus the enum and master-table dictionaries the answer text depends on. The rule rows
    are only emitted when ``verified`` is true, so a stale table cannot produce answers.
    """
    global _md_global
    _md_global = md
    ev = {"generated_by": "scripts/character_skills/skilllist_types.py",
          "native_sha256": hashlib.sha256(native.raw).hexdigest(),
          "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
          "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
          "type": UNION_COUNT, "type_name": "UnionCount"}

    # (1) gate: IsEnableAbility case 0x423
    lo, hi = func_bounds(native, ISENABLE)
    body = list(DIS.disasm(native.raw[lo:ISABLE_END], lo))
    case = next((i for i, x in enumerate(body)
                 if x.mnemonic == "cmp" and x.op_str.replace(" ", "") == "w8,#0x423"), None)
    gate = {"case_rva": hex(body[case].address) if case is not None else None,
            "calls": [], "compares": [], "terminals": []}
    if case is not None:
        for x in body[case:case + 130]:
            nm = _named_call(native, x)
            if nm:
                gate["calls"].append({"rva": hex(x.address), "call": nm})
            if x.mnemonic in ("cmp", "tst") and x.address + 4 < len(native.raw):
                nxt = first_insn(native, x.address + 4)
                if nxt is not None and nxt.mnemonic.startswith("b"):
                    gate["compares"].append({"rva": hex(x.address),
                                             "test": x.mnemonic + " " + x.op_str,
                                             "branch": nxt.mnemonic})
    wanted_gate = {"BattleManager.GetAllCharaList", "CharaBehavior.IsAlive",
                   "skillParameter.get_iParam0", "skillParameter.get_flag",
                   "skillParameter.get_param8", "skillParameter.get_param0",
                   "BattleParam.IsTargetHome"}
    gate_names = {c["call"] for c in gate["calls"]}
    gate["verified"] = wanted_gate <= gate_names
    ev["gate"] = gate

    # (2) setup: setupAbility's jump table row for 0x423 must be the block that builds the
    #     union-count work (cAbilityUnionCountWork..ctor) and keeps it in _abilityUnionCountWorkList
    setup = {}
    base = None
    page = None
    for x in DIS.disasm(native.raw[SETUPABILITY:SETUPABILITY + 0x1000], SETUPABILITY):
        if x.mnemonic == "adrp" and x.op_str.startswith("x28, #"):
            page = int(x.op_str.split("#")[1], 0)
        if x.mnemonic == "add" and x.op_str.replace(" ", "").startswith("x28,x28,#0xbb2") and page:
            base = page + int(x.op_str.rsplit("#", 1)[1], 0)
    if base:
        entry = int.from_bytes(native.raw[base + 2 * (UNION_COUNT - 0x421):
                                         base + 2 * (UNION_COUNT - 0x421) + 2], "little")
        target = 0x10F4F10 + 4 * entry
        blk = _linear(native, target, 60)
        names = [n for n in (_named_call(native, x) for x in blk) if n]
        setup = {"jump_table_rva": hex(base), "case_index": UNION_COUNT - 0x421,
                 "block_rva": hex(target), "calls": names,
                 "reads_param6": any(x.mnemonic == "bl" and x.op_str == "#0x1dbd04c" for x in blk),
                 "reads_param7": any(x.mnemonic == "bl" and x.op_str == "#0x1dbd0fc" for x in blk),
                 "writes_work_list": any(x.mnemonic == "str" and x.op_str.replace(" ", "").endswith("#0x728]")
                                        for x in blk),
                 "makes_work": "cAbilityUnionCountWork..ctor" in names}
        setup["verified"] = bool(setup["makes_work"] and setup["writes_work_list"]
                                 and setup["reads_param6"] and setup["reads_param7"])
    ev["setup"] = setup

    # (3) apply: update_ability processes _abilityUnionCountWorkList and heals each member
    upd = list(DIS.disasm(native.raw[0x110BC28:0x110BE64], 0x110BC28))
    apply_calls = [n for n in (_named_call(native, x) for x in upd) if n]
    apply = {"rva_range": "0x110bc28..0x110be64",
             "reads_work_list": any(x.mnemonic == "ldr" and x.op_str.replace(" ", "") == "x0,[x19,#0x728]"
                                    for x in upd),
             "calls": apply_calls,
             "heals": "CharaBehavior.Heal" in apply_calls,
             "filters": {"get_iParam1": any(x.op_str == "#0x1dbd3a8" for x in upd if x.mnemonic == "bl"),
                         "get_flag1": any(x.op_str == "#0x1dbd45c" for x in upd if x.mnemonic == "bl"),
                         "get_param9": any(x.op_str == "#0x1dbd25c" for x in upd if x.mnemonic == "bl"),
                         "get_param6": any(x.op_str == "#0x1dbd04c" for x in upd if x.mnemonic == "bl"),
                         "hpMax_load_0x58": any(x.mnemonic == "ldr" and x.op_str.replace(" ", "") == "x0,[x8,#0x58]"
                                                for x in upd),
                         "truncate_helper_0x14376ec": any(x.mnemonic == "bl" and x.op_str == "#0x14376ec"
                                                          for x in upd),
                         "IsEnableAbility_gate": any(x.mnemonic == "bl" and x.op_str == "#0x1112574"
                                                     for x in upd)}}
    apply["verified"] = (apply["reads_work_list"] and apply["heals"]
                         and all(apply["filters"].values()))
    ev["apply"] = apply

    # (4) player-side consumers: the five PlayerManager.GetAbility* read the flag index of
    #     this type out of the static rank array (offset 2*rank)
    rank = _flag_index_rank(native)
    ev["flag_index"] = {"rank": rank, "static_offset": hex(2 * rank),
                        "array": "Constants 静态区 +0x0..（AbilityTypeCachedFlagIndex..cctor 按序写入）"}
    consumers = {}
    for nm, entry in (("PlayerManager.GetAbilityAttack", 0x15935B0),
                      ("PlayerManager.GetAbilityWalkSpeed", 0x1596BB8),
                      ("PlayerManager.GetAbilityDefence", 0x1599CF0),
                      ("PlayerManager.GetAbilityCritical", 0x159CF04),
                      ("PlayerManager.GetAbilityCriticalDmg", 0x15A1B00)):
        lo, hi = func_bounds(native, entry)
        hits = [hex(x.address) for x in DIS.disasm(native.raw[lo:hi], lo)
                if x.mnemonic == "ldrh" and x.op_str.replace(" ", "").endswith("#0x%x]" % (2 * rank))]
        consumers[nm] = hits
    ev["player_side_consumers"] = consumers
    ev["player_side_paramn_aggregation"] = {
        "aggregation": "极值选择（EXTREMUM_SELECTION）",
        "note": ("GetAbilityOnFlagIndex_ParamN 对每个启用能力重新过 IsEnableAbility 后按调用方实参"
                 "取 min／max（方向由调用方实参决定），**不是叠乘叠加**。交接与规则文本按单记录写"
                 "「×paramN」，在单能力情形精确；多个 1059 能力同时生效时的聚合语义未写入本产物，"
                 "也未与本产物冲突（p2b6 审查注记 4）。"),
    }
    ev["verified"] = bool(ev["gate"].get("verified") and ev["setup"].get("verified")
                          and apply["verified"] and all(consumers.values()))
    return ev


def _flag_index_rank(native):
    """Rank of type 1059 in Constants.AbilityTypeCachedFlagIndex..cctor's type list."""
    lo, hi = func_bounds(native, 0x15764A4)
    seq, pending = [], None
    for ins in DIS.disasm(native.raw[lo:hi], lo):
        if ins.mnemonic == "mov" and ins.op_str.startswith("w0, #"):
            pending = int(ins.op_str.split("#")[1], 0)
        elif ins.mnemonic == "bl" and ins.op_str.startswith("#") and int(ins.op_str[1:], 0) == 0x15771E8:
            if pending is not None:
                seq.append(pending)
            pending = None
    return seq.index(UNION_COUNT) if UNION_COUNT in seq else -1


def filter_rule_rows():
    """Rule rows for the filter slots that now have readable values."""
    rows = []
    for t, slots in FILTER_SLOT_RULES.items():
        for field, kind, meaning in slots:
            rows.append(dict(
                file_table="skilllist.ability" + str(t), table="skilllist", effect_type=t,
                field_path="/" + field, answer_kind=kind,
                meaning_zh=meaning + "（筛选参数，不是数值贡献）",
                unit=("位图 1<<JOB_TYPE" if kind == "job_bitmap" else
                      "位图 bit22..30（0x7fc00000）" if kind == "weapon_bitmap" else
                      "两位十进制分组的 homelist.home_id"),
                rule=("逐位解码为职业（JOB_TYPE：0 戦士/1 弓使い/2 魔法使い/3 僧侶/4 騎士/5 ALMIGHTY）"
                      if kind == "job_bitmap" else
                      "取低 32 位与 0x7fc00000 相交后逐位解码为武器种类"
                      if kind == "weapon_bitmap" else
                      "按 1/100/10000 位各取两位十进制分组，逐个查 homelist；0 表示不筛选"),
                status="已确认字典（元数据枚举＋原生位测试／原生比较点；取值分布与正文对照见 filter_dictionary.json）",
                condition=COMPOSITE_CONDITIONS.get(t),
                evidence=["output/character_skills/skilllist_types/filter_dictionary.json",
                          "scripts/character_skills/skilllist_types.py（filter_rule_rows）"]))
    return rows


def union_count_rule_rows(native, md):
    """Rule rows for type 1059, emitted only after the chain is recomputed."""
    ev = union_count_evidence(native, md)
    if not ev.get("verified"):
        return []
    rows = []
    for field, kind in UNION_COUNT_FIELDS:
        meaning, unit, rule = UNION_COUNT_KIND_TEXT[kind]
        rows.append(dict(
            file_table="skilllist.ability1059", table="skilllist", effect_type=UNION_COUNT,
            field_path="/" + field, answer_kind=kind,
            meaning_zh=meaning + "（UnionCount；玩家侧队伍范围）", unit=unit, rule=rule,
            status="已确认数值换算（玩家侧 apply 与计数条件原生核实）",
            condition=UNION_COUNT_CONDITION,
            limits=("玩家侧 GetAbilityOnFlagIndex_ParamN 对多个启用能力是**极值选择**（按调用方实参取 "
                    "min／max），不是叠乘叠加；本条按单记录写「×paramN」，多 1059 能力同开时的聚合"
                    "语义未声称、也不冲突（详见 union_count_chains.json 的 "
                    "player_side_paramn_aggregation）"),
            evidence=["output/character_skills/skilllist_types/union_count_chains.json",
                      "BattleParam.IsEnableAbility case 0x423（%s）" % ev["gate"].get("case_rva"),
                      "BattleParam.setupAbility case 1059（%s）→ cAbilityUnionCountWork..ctor" % ev["setup"].get("block_rva"),
                      "BattleParam.update_ability 0x110bc28..0x110be64（_abilityUnionCountWorkList）",
                      "PlayerManager.GetAbilityAttack/WalkSpeed/Defence/Critical/CriticalDmg "
                      "（ldrh w1,[x8,#%s]）" % ev["flag_index"]["static_offset"]]))
    for field, kind, meaning in UNION_COUNT_FILTER_SLOTS:
        rows.append(dict(
            file_table="skilllist.ability1059", table="skilllist", effect_type=UNION_COUNT,
            field_path="/" + field, answer_kind=kind,
            meaning_zh=meaning + "（筛选参数，不是数值贡献）",
            unit=("位图 1<<JOB_TYPE" if kind == "job_bitmap" else
                  "位图 bit22..30（0x7fc00000）" if kind == "weapon_bitmap" else
                  "两位十进制分组的 homelist.home_id"),
            rule=("逐位解码为职业（JOB_TYPE）" if kind == "job_bitmap" else
                  "取低 32 位与 0x7fc00000 相交后逐位解码为武器种类" if kind == "weapon_bitmap" else
                  "按 1/100/10000 位各取两位十进制分组，逐个查 homelist；0 表示不筛选"),
            status="已确认字典（同 filter_dictionary.json）",
            condition=UNION_COUNT_CONDITION,
            limits=("玩家侧 GetAbilityOnFlagIndex_ParamN 对多个启用能力是**极值选择**（按调用方实参取 "
                    "min／max），不是叠乘叠加；本条按单记录写（详见 union_count_chains.json 的 "
                    "player_side_paramn_aggregation）"),
            evidence=["output/character_skills/skilllist_types/union_count_chains.json",
                      "output/character_skills/skilllist_types/filter_dictionary.json"]))
    return rows


def rule_rows(affected, maps=None, native=None, md=None):
    """Field rows for the types this batch (and the previous batches) confirm."""
    crit = crit_rule_rows(maps) if maps else []
    same_leaf = same_leaf_as_type8_rows(maps) if maps else []
    composite = composite_rule_rows(native, maps) if (maps and native) else []
    union = union_count_rule_rows(native, md) if (native and md) else []
    return crit + same_leaf + composite + union + filter_rule_rows() + [
        dict(file_table="skilllist.ability8", table="skilllist", effect_type=8,
             field_path="/param1",
             meaning_zh="本项攻击乘数（Always：常时生效的攻击强化）",
             answer_kind="attack_mult",
             unit="无量纲倍率", rule="本项攻击 +(param1-1)×100%（乘进自身攻击因子）",
             status="已确认数值换算；未乘 Chain，不承诺最终伤害",
             condition="type=8 记录被装载即生效：IsEnableAbility 对该 type 无条件返回 true",
             evidence=["scripts/character_skills/skilllist_types.py",
                       "output/character_skills/skilllist_types/native_checks.json",
                       "GetAbilityAttack 分支 0x1107958；换算复用 ordinary_effects/ability7"]),
        dict(file_table="skilllist.ability8", table="skilllist", effect_type=8,
             field_path="/param2",
             meaning_zh="移动速度乘数（常时的移动速度强化）",
             answer_kind="move_mult",
             unit="速度倍率", rule="移动速度 ×param2",
             status="已确认数值换算", condition="同上（IsEnableAbility 无条件下通过）",
             evidence=["scripts/character_skills/skilllist_types.py",
                       "output/character_skills/skilllist_types/native_checks.json",
                       "GetAbilityWalkSpeed 分支 0x1118c28；换算复用 ordinary_effects/ability7"]),
        dict(file_table="skilllist.ability8", table="skilllist", effect_type=8,
             field_path="/param3",
             meaning_zh="本项受伤量乘数（正文写作「防御」；乘进受伤量因子，不是固定防御量）",
             answer_kind="take_mult",
             unit="无量纲倍率", rule="本项减伤 (1-param3)×100%（param3>1 时为负减伤即增伤）",
             status="已确认数值换算；方向按代码，不按名称「防御」改动",
             condition="同上（IsEnableAbility 无条件下通过）",
             evidence=["scripts/character_skills/skilllist_types.py",
                       "output/character_skills/skilllist_types/native_checks.json",
                       "GetAbilityDefence 分支 0x1108124；换算复用 ordinary_effects/ability7"]),
        dict(file_table="skilllist.ability26", table="skilllist", effect_type=26,
             field_path="/param4",
             meaning_zh="战斗开始时追加的玛那数量（受 iParam1 职业位图限定）",
             unit="个", rule="int(param4) 次 ProduceManaForce(jobFlags=iParam1 展开, 属性标志=(param5==1))；param4<1 不产出",
             status="已确认数值换算；是否真正生效仍受装载/开局流程影响",
             condition="type=26 记录进入 PlayerManager.PartyAbilityInit 的 ManaGet 分支",
             evidence=["scripts/character_skills/skilllist_types.py",
                       "output/character_skills/skilllist_types/native_checks.json",
                       "PlayerManager.subPartyAbilityInit_ManaGet 0x158ce2c..0x158cef0"]),
        dict(file_table="skilllist.ability26", table="skilllist", effect_type=26,
             field_path="/iParam1",
             meaning_zh="该追加玛那可被使用的职业位图（1<<JobType；0 表示不产出受职业限定的玛那）",
             unit="位图 1<<JobType",
             rule="逐位 i：Constants.GetJobMana(i) → ManaIcon.transELEMENT_TYPE_FLAG，并集作为 ProduceManaForce 的职业旗标",
             status="已确认数值换算（位展开规则）",
             condition="同上；iParam1=0 时该分支整体跳过",
             evidence=["scripts/character_skills/skilllist_types.py",
                       "output/character_skills/skilllist_types/native_checks.json"]),
        dict(file_table="skilllist.ability26", table="skilllist", effect_type=26,
             field_path="/param6",
             meaning_zh="生效范围选择码（0／1／2 三分支）",
             unit="选择码（整数化）",
             rule="int(param6)==1 总是生效；==0 仅当角色对象 [chara+0x118] 标志非 0；==2 仅当该标志为 0；其他值不生效",
             status="已确认分支语义；该标志字段的业务名未确认",
             condition="同上",
             evidence=["scripts/character_skills/skilllist_types.py",
                       "output/character_skills/skilllist_types/native_checks.json"]),
        dict(file_table="skilllist.ability26", table="skilllist", effect_type=26,
             field_path="/param7",
             meaning_zh="战斗开始时另行追加的玛那数量（不受职业限定）",
             unit="个", rule="int(param7) 次 ProduceMana(elementFlag=transELEMENT_TYPE_FLAG(8))；param7<1 不产出",
             status="已确认数值换算", condition="同上；int(param7)=0 时该分支跳过",
             evidence=["scripts/character_skills/skilllist_types.py",
                       "output/character_skills/skilllist_types/native_checks.json"]),
    ]


def filter_dictionary(native, md):
    """The job / weapon / home dictionaries, with the native and data evidence.

    Every entry is recomputed here: enum values from the metadata default table, the
    weapon bit table from the jump table of ``Constants.WeaponKind2AttackFlag``, the home
    ids from the game's own ``homelist`` master table, and the discriminative agreement
    counts from the records whose text names exactly one job/weapon/home.
    """
    md = md or Metadata(str(METADATA))
    rows = C.apk_rows("skilllist")
    cache_rows = C.cache_rows("skilllist")
    jobs = enum_values(native, md, "JOB_TYPE")
    weapons = enum_values(native, md, "WeaponKind")
    homes = {int(r["home_id"]): r["name"] for r in
             C.load_json(C.DECODED / "homelist.data5.json.raw")["homelist"]}

    # weapon kind -> attack flag, from the game's own jump table
    table_base = None
    flag_cases = {}
    for x in DIS.disasm(native.raw[0x1578560:0x157869C], 0x1578560):
        if x.mnemonic == "adrp" and "x9, #0x2074000" in x.op_str:
            table_base = int(x.op_str.split("#")[1], 0) + 0x180
    if table_base:
        for k in range(11):
            off = native.raw[table_base + k]
            tgt = 0x15785BC + 4 * off
            val = None
            for y in DIS.disasm(native.raw[tgt:tgt + 0x18], tgt):
                if y.mnemonic == "mov" and y.op_str.startswith("w0, #"):
                    val = int(y.op_str.split("#")[1], 0)
            flag_cases[k] = val
    weapon_bits = {v: {"bit": (v.bit_length() - 1) if v else None,
                       "kind": k, "kind_name": None} for k, v in flag_cases.items() if v}
    for k, v in list(flag_cases.items()):
        if not v:
            continue
        name = next((n for n, val in weapons.items() if val == k), None)
        weapon_bits[v]["kind_name"] = name

    def job_bits(v):
        return [i for i in range(6) if int(v) & (1 << i)]

    def weapon_bits_of(r, field="flag0_0"):
        m = (r.get(field) or 0) & 0x7FC00000
        return [i for i in range(22, 31) if m & (1 << i)]

    def home_groups(v):
        n = int(v)
        return [x for x in (n % 100, (n // 100) % 100, (n // 10000) % 100) if x]

    job_word = {"戦士": 0, "弓": 1, "魔法": 2, "僧侶": 3, "騎士": 4}
    wep_word = {"斬": 22, "打": 23, "突": 24, "弓": 25, "魔": 26, "聖": 27, "拳": 28, "銃": 29}
    checks = {"job": {"n": 0, "agree": 0, "samples": []},
              "weapon": {"n": 0, "agree": 0, "samples": []},
              "home": {"n": 0, "agree": 0, "samples": []}}
    for r in rows:
        text = r.get("text") or ""
        # Ability descriptions in scope always talk about 味方/conditions; records whose
        # "text" is only a display label (e.g. "…のサブアビリティ1") would otherwise be
        # read as if the label were the description.
        if text == (r.get("name") or "") or "味方" not in text:
            continue
        ip = r.get("iParam0")
        if ip and bin(int(ip)).count("1") == 1:
            words = [w for w in job_word if w in text]
            if len(words) == 1:
                bit = int(ip).bit_length() - 1
                checks["job"]["n"] += 1
                ok = bit == job_word[words[0]]
                checks["job"]["agree"] += ok
                if len(checks["job"]["samples"]) < 6:
                    checks["job"]["samples"].append(
                        {"skillid": r["skillid"], "ability": r["ability"], "iParam0": ip,
                         "decoded": R.JOB_TYPE_NAMES.get(bit), "text_word": words[0], "ok": ok})
        wb = weapon_bits_of(r)
        if len(wb) == 1:
            words = [w for w in wep_word if w in text]
            if len(words) == 1:
                checks["weapon"]["n"] += 1
                ok = wb[0] == wep_word[words[0]]
                checks["weapon"]["agree"] += ok
                if len(checks["weapon"]["samples"]) < 6:
                    checks["weapon"]["samples"].append(
                        {"skillid": r["skillid"], "ability": r["ability"],
                         "flag0_0": hex(r.get("flag0_0") or 0), "bit": wb[0],
                         "text_word": words[0], "ok": ok})
        p8 = r.get("param8")
        if r.get("ability") == 67 and p8:
            groups = home_groups(p8)
            named = [v for k, v in homes.items() if k in groups and v in text]
            if len(named) == 1 and len(groups) == 1:
                checks["home"]["n"] += 1
                ok = homes.get(groups[0]) == named[0]
                checks["home"]["agree"] += ok
                if len(checks["home"]["samples"]) < 6:
                    checks["home"]["samples"].append(
                        {"skillid": r["skillid"], "param8": p8, "groups": groups,
                         "name": homes.get(groups[0]), "text_word": named[0], "ok": ok})

    slot_usage = {}
    for t in (67, 80, 96, UNION_COUNT):
        slot_usage[str(t)] = {
            "record_fields": [f for f, _k, _m in FILTER_SLOT_RULES.get(t, [])]
            + [f for f, _k, _m in UNION_COUNT_FILTER_SLOTS if t == UNION_COUNT],
            "read_sites": {
                "iParam0": "skillParameter.get_iParam0（0x1dbd30c）→ 1<<jobId 位测试（CalcCharaNum 0x1113e14）"
                           if t in (67, UNION_COUNT) else "skillParameter.get_iParam0（0x1dbd30c）",
                "flag0_0": "skillParameter.get_flag（0x1dbd444，_flag@0x90 低 32 位）→ tst x0,wepFlags",
                "param8": "skillParameter.get_param8（0x1dbd1ac）→ BattleParam.IsTargetHome（0x1113958）",
            },
        }
    data = {
        "generated_by": "scripts/character_skills/skilllist_types.py",
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
        "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
        "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
        "note": ("筛选位字典：iParam0（职业位图）、flag（武器位图）、param8／param9（出身筛选值）。"
                 "职业名来自元数据枚举 JOB_TYPE，武器名来自 WeaponKind＋游戏自身的 "
                 "Constants.WeaponKind2AttackFlag 跳转表，出身名来自游戏主表 homelist。"),
        "job": {
            "field": "iParam0 / iParam1（skillParameter._iParam0／_iParam1）",
            "bit_shape": "位 i 置位 = 该 JOB_TYPE 值 i 命中；比较方式是 1<<jobId 后 tst",
            "enum": jobs,
            "names_zh": {"WARRIOR": "戦士", "ARCHERY": "弓使い", "WIZARD": "魔法使い",
                         "HEALER": "僧侶", "SHIELD": "騎士", "ALMIGHTY": "ALMIGHTY"},
            "character_side": ("jobId = ParamS_int.get_Value([chara+0x28]+0xf8)；"
                               "BattleParam 字段表 _jobType@0xf8"),
            "native_evidence": ["BattleParam.CalcCharaNum 0x1113e08..0x1113e1c："
                                "ldr x0,[x8,#0xf8]; bl ParamS_int.get_Value; lsl w8,w29,w0; tst w8,w22",
                                "BattleParam.IsEnableAbility case 0x423 0x1111293c 同形位测试"],
            "observed_values_cache": sorted({r["iParam0"] for r in cache_rows if r.get("iParam0")}),
            "observed_values_apk": sorted({r["iParam0"] for r in rows if r.get("iParam0")})[:24],
            "text_crosscheck": checks["job"],
        },
        "weapon": {
            "field": "flag0_0 / flag1_0（skillParameter._flag@0x90／_flag1@0x98 的低 32 位）",
            "bit_shape": "bit = 22 + weaponKind；掩码 0x7fc00000",
            "enum": weapons,
            "kind_to_bit": {str(k): (hex(v) if v else None) for k, v in flag_cases.items()},
            "bits": {hex(v): {"bit": d["bit"], "kind": d["kind"], "kind_name": d["kind_name"]}
                     for v, d in weapon_bits.items()},
            "character_side": ("[chara+0x28]+0x1b0 ＝ BattleParam._weaponTypeAttackFlag（ParamS_long），"
                               "由 BattleParam.CreateByID 用 Constants.WeaponKind2AttackFlag(weaponKind) 写入"),
            "native_evidence": ["Constants.WeaponKind2AttackFlag 0x1578560（跳转表 0x2074180＋基址 0x15785bc）",
                                "该跳转表的表项是**字节**（不是 uint16／u32）："
                                "`ldrb w11,[x9,x8]` + `add x10,x10,x11,lsl #2`，即 entry = 基址 + 表项字节×4",
                                "BattleParam.CreateByID 0x10fdcac..0x10fdcc8："
                                "WeaponKind2AttackFlag([weapon+0x30]) → ParamS_long.set_Value([x19+0x1b0])"],
            "text_crosscheck": checks["weapon"],
        },
        "home": {
            "field": "param8（67/1059 的计数筛选）与 param9（1059 的受益对象筛选）",
            "coding": ("按 1／100／10000 位各取两位十进制分组，逐个与角色的 home／battle_home 比较；"
                       "0 表示不筛选（targetHome==0 时 IsTargetHome 直接为真）"),
            "table": {"source": "output/cache_full_20261015_v3/decoded/homelist.data5.json.raw",
                      "ids": homes},
            "character_side": ("charaParameter.get_home／get_battle_home（BattleParam._CharaParameter@0x338）"),
            "native_evidence": ["BattleParam.IsTargetHome 0x10fdd50..0x10fdeb0："
                                "targetHome%100、targetHome/100%100、targetHome/10000%100 三组分别比较 "
                                "home 与 battle_home",
                                "BattleParam.CalcCharaNum 0x1113e58 以 int(param8) 为 homeFlags"],
            "text_crosscheck": checks["home"],
            "known_boundary": ("引擎逐组比较时不排除取值为 0 的组；home 缺省（记录无 home 字段）时 "
                               "get_home 的返回值未经确认，因此「0 组是否命中缺省角色」保持未验证"),
        },
        "slot_usage": slot_usage,
    }
    return data


def union_count_filter_rows():
    """Filter rows for the union-count family (kept next to the other union rows)."""
    return [dict(
        file_table="skilllist.ability1059", table="skilllist", effect_type=UNION_COUNT,
        field_path="/" + f, answer_kind=k, meaning_zh=m, unit="筛选参数",
        rule="同 filter_dictionary.json", status="已确认字典",
        condition=UNION_COUNT_CONDITION,
        evidence=["output/character_skills/skilllist_types/filter_dictionary.json"])
        for f, k, m in UNION_COUNT_FILTER_SLOTS]


def p6_checks(native, md):
    """Checks for the P2 batch-6 items: filter dictionaries + type 1059 UnionCount."""
    checks = []

    def add(name, ok, **kw):
        item = dict(name=name, **kw)
        item["pass"] = bool(ok)
        checks.append(item)

    fd = filter_dictionary(native, md)
    jobs = fd["job"]["enum"]
    add("filter_job_enum_matches_native_bit_test",
        jobs.get("WARRIOR") == 0 and jobs.get("ARCHERY") == 1 and jobs.get("WIZARD") == 2
        and jobs.get("HEALER") == 3 and jobs.get("SHIELD") == 4 and jobs.get("ALMIGHTY") == 5,
        enum=jobs, note="JOB_TYPE 元数据枚举；与 1<<jobId 的位测试顺序一致")
    # the job id really comes from BattleParam._jobType@0xf8 and is shifted by 1<<id
    calc = list(DIS.disasm(native.raw[CALC_CHARA_NUM:CALC_CHARA_NUM + 0x1A0], CALC_CHARA_NUM))
    add("filter_job_bit_test_in_calccharanum",
        any(x.mnemonic == "ldr" and x.op_str.replace(" ", "") == "x0,[x8,#0xf8]" for x in calc)
        and any(x.mnemonic == "lsl" and x.op_str.replace(" ", "").startswith("w8,w29,w0") for x in calc)
        and any(x.mnemonic == "tst" and x.op_str.replace(" ", "") == "w8,w22" for x in calc),
        site="BattleParam.CalcCharaNum 0x1113e08..0x1113e1c",
        note="jobId = ParamS_int([chara+0x28]+0xf8=_jobType) → 1<<jobId → tst paramJob")
    kinds = fd["weapon"]["kind_to_bit"]
    add("filter_weapon_table_bits",
        kinds.get("0") == "0x400000" and kinds.get("5") == "0x8000000"
        and kinds.get("8") == "0x10000000" and kinds.get("9") == "0x20000000"
        and kinds.get("10") == "0x40000000" and kinds.get("6") is None and kinds.get("7") is None,
        kinds=kinds, note="WeaponKind 0..10 → 攻击位 22..30（6/7 = OTHER/ALL 返回 0）")
    add("filter_weapon_character_side_is_0x1b0",
        any(x.mnemonic == "ldr" and x.op_str.replace(" ", "") == "x8,[x19,#0x1b0]"
            for x in DIS.disasm(native.raw[0x10FDC80:0x10FDCE0], 0x10FDC80)),
        note="BattleParam.CreateByID 把 WeaponKind2AttackFlag(weaponKind) 写入 _weaponTypeAttackFlag@0x1b0")
    homes = fd["home"]["table"]["ids"]
    add("filter_home_table_from_master",
        homes.get(4) == "副都" and homes.get(5) == "聖都" and homes.get(6) == "賢者の塔"
        and homes.get(12) == "大海" and homes.get(22) == "幻獣の世界" and 0 not in homes,
        ids={str(k): v for k, v in list(homes.items())[:8]},
        note="出身名来自游戏主表 homelist（不是外部数据库）")
    tc = {k: (fd[k]["text_crosscheck"]["n"], fd[k]["text_crosscheck"]["agree"])
          for k in ("job", "weapon", "home")}
    add("filter_text_crosscheck_all_agree",
        all(n > 0 and n == a for n, a in tc.values()), counts=tc,
        note="只取「正文恰好只出现一个该维度词、位图恰好只有一位」的样本做区分性对照，必须全一致")

    ev = union_count_evidence(native, md)
    add("union_count_gate_chain", ev["gate"].get("verified"),
        case=ev["gate"].get("case_rva"), calls=[c["call"] for c in ev["gate"].get("calls", [])],
        note="IsEnableAbility case 1059：GetAllCharaList + 存活检查 + iParam0/flag/param8 三项任一 + "
             "IsTargetHome + param0 阈值")
    add("union_count_setup_creates_work", ev["setup"].get("verified"),
        block=ev["setup"].get("block_rva"), calls=ev["setup"].get("calls"),
        note="setupAbility 跳转表 case 1059 → cAbilityUnionCountWork(_ability,_timer=param7) 入 "
             "_abilityUnionCountWorkList@0x728")
    add("union_count_apply_heals_members", ev["apply"].get("verified"),
        filters=ev["apply"].get("filters"),
        note="update_ability 遍历 _abilityUnionCountWorkList：IsEnableAbility 门控 → 计时器 → "
             "CharaBehavior.Heal(int(param6×成员最大HP))，目标按 iParam1/flag1/param9 筛选")
    add("union_count_player_side_consumers", all(ev["player_side_consumers"].values()),
        consumers=ev["player_side_consumers"],
        note="五个 PlayerManager.GetAbility* 都按静态 rank 数组取本类型的 flag index（offset 2*rank），"
             "因此 1059 的 param1..5 在玩家侧（队伍范围）被应用；这是 P2-2「三条乘算路径落中性」的正解")
    add("union_count_chain_verified_so_rules_emitted", ev.get("verified"),
        rules=len(union_count_rule_rows(native, md)),
        note="规则行只在整链重算通过后才产出（与 composite_rule_rows 同一约束）")
    return checks


def write_field_dictionary(affected, maps=None, native=None, md=None):
    rows = rule_rows(affected, maps, native, md)
    C.write_json(OUT / "field_dictionary.json", rows)
    return rows


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------
def controlled_checks(native, md, resolver, maps):
    checks = []

    def add(name, ok, **extra):
        checks.append({"name": name, "pass": bool(ok), **extra})

    # 1. switch heads really follow a skillParameter.get_ability call
    for kind, cfg in FUNCS.items():
        prev = next((i for i in DIS.disasm(native.raw[cfg["head"] - 4:cfg["head"]], cfg["head"] - 4)), None)
        add(f"{kind}_switch_follows_get_ability",
            prev is not None and prev.mnemonic == "bl" and prev.op_str == f"#0x{GET_ABILITY:x}",
            prev=f"{prev.mnemonic} {prev.op_str}" if prev else None)

    # 2. the shared tail really multiplies the read slot into the accumulator
    for kind in MULTIPLICATIVE:
        ins = first_insn(native, TAIL_MUL[kind])
        add(f"{kind}_tail_is_fmul", ins is not None and ins.mnemonic == "fmul"
            and ins.op_str.replace(" ", "") == "s8,s8,s0",
            got=f"{ins.mnemonic} {ins.op_str}" if ins else None,
            note="共享尾巴把该槽读出的值乘进累加因子")
    # the crit accumulators are additive and accumulate inline in each branch
    for kind, probe in (("crit_rate", 36), ("crit_dmg", 1003)):
        leaf = maps[kind][probe]["leaf"]
        found = []
        if isinstance(leaf, str) and leaf.startswith("0x"):
            for insn in DIS.disasm(native.raw[int(leaf, 16):int(leaf, 16) + 0x60], int(leaf, 16)):
                found.append(f"{insn.mnemonic} {insn.op_str}")
        op = ACCUM_OP[kind].replace(" ", "")
        add(f"{kind}_accumulate_is_inline_fadd",
            any(line.replace(" ", "") == op for line in found),
            probe_type=probe, leaf=leaf, expected=ACCUM_OP[kind],
            window=found[:12],
            note="两条暴击路径按 fadd 加算进累加器（不是乘算），加算发生在分支体内")

    # 3. the mask registers are neutralised before the loop, so branch selection
    #    does not depend on the entry arguments
    a = first_insn(native, 0x1107660)   # attack: mov w23, #1
    d = first_insn(native, 0x1107F98)   # defence: stp w23, w21, [sp, #0x18]
    e = first_insn(native, 0x1107FCC)   # defence: mov w21, #1
    add("mask_registers_neutralised_before_loop",
        a.mnemonic == "mov" and a.op_str == "w23, #1"
        and d.mnemonic == "stp" and d.op_str.startswith("w23, w21")
        and e.mnemonic == "mov" and e.op_str == "w21, #1",
        attack=f"{a.mnemonic} {a.op_str}", defence_save=f"{d.mnemonic} {d.op_str}",
        defence_reset=f"{e.mnemonic} {e.op_str}",
        note="进入循环前把掩码寄存器置 1，故分支只由 type 决定，与调用方参数无关")

    # 4. named branch resolutions (hand-verified against the disassembly)
    want = {
        "attack": {7: 0x1107958, 8: 0x1107958, 1095: 0x1107958, 67: 0x110799C,
                   26: 0x1107C88, 64: 0x1107C88, 1059: 0x1107C88, 2012: 0x1107C88},
        "defence": {7: 0x1108124, 8: 0x1108124, 67: 0x110823C,
                    26: 0x1108148, 64: 0x1108148, 1059: 0x1108148, 2012: 0x1108148},
        "move": {7: 0x1118C28, 8: 0x1118C28, 26: 0x1118C4C, 1059: 0x1118C4C,
                 2012: 0x1118C4C},
    }
    for kind, cases in want.items():
        bad = {t: maps[kind][t]["leaf"] for t, exp in cases.items()
               if maps[kind][t]["leaf"] != hex(exp)}
        add(f"{kind}_named_branch_resolution", not bad, mismatches=bad,
            checked=len(cases))

    # 5. type 8 reads exactly param1 / param2 / param3 across the three apply paths
    got8 = {k: maps[k][8]["slots"] for k in MULTIPLICATIVE}
    add("type8_slots_attack_move_defence",
        got8["attack"] == ["param1"] and got8["move"] == ["param2"]
        and got8["defence"] == ["param3"],
        got=got8, note="param0/param4 不被任何 apply 路径读取，故本批不给它们规则")

    # 6. every arm that reads a slot is gated by IsEnableAbility
    gated = {k: maps[k][8]["gated_by_isenable"] for k in MULTIPLICATIVE}
    add("type8_gated_by_isenable", all(gated.values()), got=gated,
        note="三条乘算路径的该 type 分支均由 IsEnableAbility 门控；type 8 不在两条暴击路径上")

    # 7. eligibility for type 8 and 26 is the unconditional-true epilogue
    elig = {}
    for t in (8, 26, 67, 1059):
        off = 0x206DC28 + (t - 1) * 2 if 1 <= t <= 7 else None
        elig[t] = None
    def elig_target(t):
        """Where IsEnableAbility's type switch lands for ``t``.

        0x1113904 is the shared epilogue (w0 keeps the entry value 1 -> eligible);
        0x1113900 is the ``w0 = 0`` epilogue -> not eligible.
        """
        stop = {"rva": None}

        def hook(u, addr, sz, data):
            rva = addr - BASE
            if rva in (0x1113900, 0x1113904) or not is_pure(first_insn(native, rva)):
                stop["rva"] = rva
                u.emu_stop()
        h = uc.hook_add(UC_HOOK_CODE, hook)
        uc.reg_write(UC_ARM64_REG_X0, t)
        uc.reg_write(UC_ARM64_REG_X8, t)
        try:
            uc.emu_start(BASE + 0x111264C, 0, count=128)   # mov w8, w0
        except Exception:
            pass
        uc.hook_del(h)
        return stop["rva"]

    uc = resolver.uc
    for t in (7, 8, 26, 67, 1059):
        elig[t] = elig_target(t)
    add("eligibility_types_8_26_are_unconditional",
        elig.get(8) == 0x1113904 and elig.get(26) == 0x1113904,
        note="types 8/26 直接进入函数尾声，w0 保持入口设定的 1（IsEnableAbility 无条件通过）",
        got=elig)

    # 8. cross-validation against the already-confirmed skilllist rules
    confirmed = collections.defaultdict(set)
    for rule in R.rules():
        if rule.get("table") != "skilllist":
            continue
        f = (rule.get("field_path") or "").lstrip("/")
        confirmed[rule.get("effect_type")].add(f)
    # Cross-validation with the already-confirmed skilllist rules. Types 7 and 1095
    # already have confirmed attack / move / damage-taken rules; those fields must be
    # exactly the ones this index attributes to the three accumulators.
    table = {}
    for t, fields in sorted(confirmed.items(), key=lambda kv: str(kv[0])):
        if not isinstance(t, int) or t not in maps["attack"]:
            continue
        by_path = {k: sorted(maps[k][t]["slots"]) for k in FUNCS}
        read = set().union(*[set(v) for v in by_path.values()])
        table[t] = {"confirmed_rule_fields": sorted(fields), "by_path": by_path,
                    "covered": sorted(f for f in fields if f in read),
                    "read_elsewhere": sorted(f for f in fields if f not in read)}
    must_cover = {7: {"param1", "param2", "param3"}, 1095: {"param1", "param2", "param3"}}
    missing_cover = {t: sorted(want - set(table.get(t, {}).get("covered") or []))
                     for t, want in must_cover.items()}
    type8_exact = {k: maps[k][8]["slots"] for k in MULTIPLICATIVE} == {
        "attack": ["param1"], "defence": ["param3"], "move": ["param2"]}
    add("apply_path_slots_agree_with_confirmed_rules",
        all(not v for v in missing_cover.values()) and type8_exact,
        must_cover={k: sorted(v) for k, v in must_cover.items()},
        missing_cover=missing_cover, type8_exact=type8_exact,
        coverage={t: {"covered": v["covered"], "read_elsewhere": v["read_elsewhere"]}
                  for t, v in table.items()},
        composite_types=["67", "80: attack/defence/move branches read several slots and call helpers",
                         "combined with the shared tail; disjointness is not asserted for them"],
        crit_accumulators=["BattleParam.GetAbilityCritical 0x1119018",
                           "BattleParam.GetAbilityCriticalDmgRate 0x1119794"],
        note="types 7/1095 的已确认攻击/移动/受伤量字段必须正好被本批三条路径覆盖；"
             "其余已确认字段（暴击率/暴击伤害系数、param0 地形、param7 间隔等）走别的读取路径，"
             "登记在 read_elsewhere —— 暴击走 GetAbilityCritical / GetAbilityCriticalDmgRate "
             "两条独立累加路径，不在本批索引范围，因此不把任何槽位标成暴击"
             "（这也是不采纳参考分析 type67/1059 暴击标签的原因）")

    # 9. the branches that the P2 batch-2 review found mis-filed as neutral must be
    #    real entries now (review/p2b2_20261017_thirdparty REPORT.md problem 1).
    #    Their bodies sit *after* the loop tail in the image, so the old
    #    "address >= tail -> stop" scan returned an empty slot list and _compact
    #    folded them into neutral_ranges.
    must_be_branches = {("defence", 67): 0x110823C, ("defence", 96): 0x11081B4,
                        ("defence", 1036): 0x1108168, ("move", 96): 0x1118D08,
                        ("move", 1036): 0x1118D74}
    compact = {kind: _compact(kind, per) for kind, per in maps.items()}
    mis = {}
    for (kind, t), rva in must_be_branches.items():
        entry = compact[kind]["entries"].get(str(t))
        in_neutral = any(a <= t <= b for a, b in compact[kind]["neutral_ranges"])
        if entry is None or entry["leaf"] != hex(rva) or not entry["slots"] or in_neutral:
            mis[f"{kind}:{t}"] = {"entry": entry, "in_neutral_range": in_neutral,
                                  "expected_leaf": hex(rva)}
    add("mis_bucketed_branches_are_real_entries",
        not mis, mismatches=mis, checked=len(must_be_branches),
        note=("这 5 个分支体位于循环尾之后，旧扫描把空槽位当中性；现在按分支体自身界定"
              "（首条无条件 b／fmul／窗口）后必须落 entries 且不入 neutral_ranges"))
    add("verified_every_entry_is_a_real_branch",
        all(e["slots"] for k in compact for e in compact[k]["entries"].values()),
        note="entries 只装扫到槽位的真实分支；中性＝解析到循环尾，两者口径分离")
    add("no_slots_class_is_separate",
        all("branch_no_slots_in_window" in compact[k] for k in FUNCS),
        no_slots={k: [x["type"] for x in compact[k]["branch_no_slots_in_window"]] for k in FUNCS},
        note="未扫到槽位的真实分支单列一类，不与中性混同（本批为 1112：其分支体无 getter 调用）")
# P2 batch 4, item 1 (review p2b3 systemic-risk suggestion): dual-path check.
    # A statically-evaluated switch must land every type on the same branch as the
    # emulated one. This catches the "missing register preset" class of silent failure
    # (a contributing type folding into the loop tail) without relying on Unicorn's
    # register file, and it covers *all five* paths, not just the two crit ones.
    static_divergence = []
    for kind in FUNCS:
        cfg = FUNCS[kind]
        cfg["terminals"] = derive_terminals(native, kind)
        st = static_leaf_map(native, kind, cfg["terminals"])
        sim = {t: maps[kind][t]["leaf"] for t in range(MAX_TYPE + 1)}
        for t in range(MAX_TYPE + 1):
            want = st[t]
            got = sim[t]
            if isinstance(want, int):
                want = hex(want)
            if want != got:
                static_divergence.append({"path": kind, "type": t,
                                          "static": want, "simulated": got})
    add("switch_resolution_sim_matches_static", not static_divergence,
        divergences=static_divergence[:10], divergence_count=len(static_divergence),
        types_checked=len(FUNCS) * (MAX_TYPE + 1),
        note=("双路核对：静态比较树求值器（位测试常量直接读序言 mov wN,#1，不依赖 Unicorn 寄存器）"
              "与仿真逐 type 比对分支叶，覆盖全部 5 条路径 0..MAX_TYPE；"
              "任何『仿真预置不完整导致误判中性』都会在这里报警"))

    # P2 batch 3: the two critical accumulators
    crit_rate_leaf = {t: maps["crit_rate"][t]["slots"] for t in (36, 1003, 1005, 1026)}
    crit_dmg_leaf = {t: maps["crit_dmg"][t]["slots"] for t in (1003, 1005, 1026)}
    add("crit_rate_branch_reads_param4_only",
        all(v == ["param4"] for v in crit_rate_leaf.values())
        and all(maps["crit_rate"][t]["gated_by_isenable"] for t in crit_rate_leaf)
        and all(maps["crit_rate"][t]["reaches_accumulate_op"] for t in crit_rate_leaf),
        got=crit_rate_leaf, note="暴击率路径：IsEnableAbility 门控 → get_param4 → fadd（加算）")
    add("crit_dmg_branch_reads_param5_only",
        all(v == ["param5"] for v in crit_dmg_leaf.values())
        and all(maps["crit_dmg"][t]["gated_by_isenable"] for t in crit_dmg_leaf),
        got=crit_dmg_leaf, note="暴伤路径：门控 → get_param5 → fadd")
    add("type3_crit_dmg_reads_param7_only",
        maps["crit_dmg"][3]["slots"] == ["param7"]
        and maps["crit_dmg"][3]["reaches_accumulate_op"],
        got=maps["crit_dmg"][3], note="BossBattle 的暴击威力落在 param7")
    add("crit_calibers_are_not_swapped",
        all(maps["crit_rate"][t]["slots"] != maps["crit_dmg"][t]["slots"]
            for t in (1003, 1005, 1026)),
        note="同一 type 的暴击率槽(param4)与暴伤槽(param5)是不同槽位，绝不互换")
    # the accumulators add (fadd), the three classic paths multiply (fmul)
    add("accumulator_ops_declared_per_path",
        ACCUM_OP["attack"].startswith("fmul") and ACCUM_OP["crit_rate"].startswith("fadd")
        and ACCUM_OP["crit_dmg"].startswith("fadd"),
        ops=ACCUM_OP, note="乘算路径 vs 加算路径的机制区分，产物按路径声明")

    # P2 batch 3 / item 3: the *existing* crit rules must not be attributed to these
    # two accumulators -- they all resolve to the neutral bucket here and are served by
    # other mechanisms, which stay registered as read_elsewhere
    anchored = {2012: "SkillAbility_SupportTarget → TimePowerUpData+24/+28 → setSupport2"
                       "（概率增量默认夹在 [0, .5]、暴伤系数增量夹在 [-1.5, 1]）",
                3000: "Support3 → _criticalDmgRate@28，经 CharaStatus._support3CtrlData@238 "
                      "进 SupportType2CtrlData",
                1008: "既有规则仅来自 cid30236 字段字典；本批确认不在两条暴击累加路径上，"
                      "实际读取路径未定位",
                1095: "既有规则仅来自 cid30236 字段字典；本批确认不在两条暴击累加路径上，"
                      "实际读取路径未定位"}
    neutral_on_crit = {t: (maps["crit_rate"][t]["neutral"] and maps["crit_dmg"][t]["neutral"])
                       for t in anchored}
    add("existing_crit_rules_are_not_on_the_two_accumulators",
        all(neutral_on_crit.values()), got=neutral_on_crit, mechanisms=anchored,
        note="2012/3000/1008/1095 在本批两条暴击累加路径上都落中性；口径一致（加算）"
             "但机制与夹紧范围不同，答案文本必须各自声明")

    add("runtime_pointer_deref_entries_kept_as_is",
        compact["attack"]["entries"].get("67") is not None
        and compact["attack"]["entries"].get("68") is not None,
        attack_67=compact["attack"]["entries"].get("67", {}).get("leaf"),
        attack_68=compact["attack"]["entries"].get("68", {}).get("leaf"),
        note=("attack 67/68 的分支依赖调用方栈帧的运行期指针解引用（审查者亦无法建模），"
              "按审查口径保持原静态结果并在 README 注明为下界估计"))

    # 10. data-side facts used by the rules
    rows = C.cache_rows("skilllist")
    t8 = [r for r in rows if r.get("ability") == 8]
    p4 = {r.get("param4") for r in t8}
    apk8 = [r for r in C.apk_rows("skilllist") if r.get("ability") == 8]
    apk_p4 = sorted({r.get("param4") for r in apk8})
    apk_p0 = {r.get("param0") for r in apk8}
    add("type8_param4_param0_scope_two_sources",
        p4 == {1} and not any(r.get("param0") is not None for r in t8)
        and len(apk8) == 2209 and len(apk_p4) > 1 and apk_p0 == {0.0},
        cache_records=len(t8), cache_param4=sorted(p4),
        cache_param0_present=sum(1 for r in t8 if r.get("param0") is not None),
        apk_records=len(apk8), apk_param4_distinct=len(apk_p4),
        apk_param4_min=apk_p4[0], apk_param4_max=apk_p4[-1], apk_param0=sorted(apk_p0),
        note=("口径必须分源：缓存 328 条 param4 恒为 1、无 param0 字段；"
              "APK 主表 2209 条 param4 有取值分布（0.0..2.5，多个非 1 值）、param0 存在且恒 0.0。"
              "不给规则的**实质依据**是三条 apply 路径与资格门控都不读取该槽，"
              "不是「值恒为 1」或「字段不存在」"))
    pat = re.compile(r"攻撃([0-9.]+)防御([0-9.]+)")
    hits = 0
    for r in t8:
        m = pat.search(r.get("text") or "")
        if m and abs(float(m.group(1)) - (r.get("param1") or 0)) < 1e-6 \
                and abs(float(m.group(2)) - (r.get("param3") or 0)) < 1e-6:
            hits += 1
    add("type8_param1_param3_match_record_text", hits >= 1, matches=hits,
        note="记录正文直接写出『攻撃X防御Y』时，X=param1、Y=param3")
    # discriminating sample: a record whose text names attack+move only has param3 == 1
    disc = [r for r in t8 if "移動速度" in (r.get("text") or "") and "防御" not in (r.get("text") or "")]
    add("type8_move_only_record_has_neutral_param3",
        bool(disc) and all(r.get("param3") == 1 for r in disc),
        samples=[(r["skillid"], r.get("param1"), r.get("param2"), r.get("param3")) for r in disc[:4]],
        note="正文只提攻撃力与移動速度的记录，param3 必须为 1（否则说明 slot 错配）")
    t26 = [r for r in rows if r.get("ability") == 26]
    with_pair = [r for r in t26 if r.get("iParam1") and r.get("param4") is not None]
    add("type26_iParam1_param4_are_the_traced_pair",
        len(with_pair) >= 80 and all(r.get("iParam1") for r in with_pair),
        records=len(t26), with_pair=len(with_pair),
        note="iParam1 与 param4 是原生分支里成对读取的两个槽")
    return checks


# ---------------------------------------------------------------------------
# per-type evidence pack
# ---------------------------------------------------------------------------
TARGET_TYPES = (8, 26, 67, 1059)
TYPE_NAMES = {8: "Always", 26: "ManaGet", 67: "HeroOne", 1059: "UnionCount"}
MISSING = {
    8: None,
    26: None,
    67: ("P2 第 5 批已把 HeroOne 的换算链逐段跟踪到累加器：五条 apply 路径的分支体都是"
         "『GetMemberList → get_param0／iParam0／param8／flag → BattleParam.CalcCharaNum(cType,"
         " 职业位图=iParam0, 武器位图=_flag 低 32 位（记录字段 flag0_0）, 出身筛选=int(param8), "
         "成员列表) → cmp w0, int(param0)"
         " → b.lt 跳过 → get_paramN → 累加』，即**命中角色数 ≥ int(param0) 时**把 paramN 乘进"
         "攻击／移动／受伤量因子，或加进暴击率/暴伤累加器。据此给出 5 条数值规则、1 条阈值规则与"
         "3 条筛选位字典规则（P2 第 6 批，见 filter_dictionary.json）；"
         "仍未命名的段：cType 的取值来源，故答案把它写进条件而不当成已知。"),
    1059: ("UnionCount（P2 第 6 批已闭环）：**玩家侧队伍范围**效果。条件＝BattleParam.IsEnableAbility "
           "case 1059（GetAllCharaList 逐角色，**任一**命中 iParam0／_flag／int(param8) 即计入，"
           "计数 ≥ int(param0) 生效）；数值＝五个 PlayerManager.GetAbility* 按静态 rank 表取本类型的 "
           "flag index 后应用 param1..param5，另有周期回复（param6×目标最大HP，间隔 param7 秒，"
           "目标按 iParam1／flag1／param9 筛选）。逐段地址见 union_count_chains.json。"
           "参考候选（只作线索）在此处与本地定位部分吻合：其 param1=攻击、param2=移动速度、"
           "param4=暴击率、param5=暴击威力、param6/param7=回复与本项目一致；"
           "其把 param3 标成（防御）而本地读到的槽是受伤量倍率（同一条 67 式语义），"
           "param0 被标成攻击类、本地定位为人数阈值，param8 被标成攻击类、本地定位为出身筛选——"
           "后三项不采纳，理由与证据见 union_count_chains.json 与 filter_dictionary.json。"),
}


def ability_type_names(md, native):
    out = {}
    row = md.types[718]
    for i, f in enumerate(md.fields[row[8]:row[8] + row[18]]):
        fn = md.string(f[0])
        if fn == "value__":
            continue
        try:
            v = native.default(row[8] + i)["value"]
        except Exception:
            continue
        out[v] = fn
    return out


def reference_leads():
    leads = collections.defaultdict(list)
    path = C.REFERENCE_ANALYSIS / "param_table_crosscheck.csv"
    if not path.exists():
        return leads
    with path.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row.get("table") != "skilllist":
                continue
            try:
                t = int(row.get("type"))
            except (TypeError, ValueError):
                continue
            if t in TARGET_TYPES:
                leads[t].append({"slot": row.get("slot"), "label": row.get("对方标签"),
                                 "conversion": row.get("对方换算"), "hits": row.get("hits"),
                                 "decisive": row.get("decisive"), "verdict": row.get("核对结论")})
    return leads


def composite_evidence(native, md, maps):
    """Per-branch evidence for the composite types: the whole chain, by address.

    For every (path, type) of 67/80/96/1036 this records the reachable branch body, the
    ``get_paramN`` call sites, the helper calls (CalcCharaNum / mana predicates /
    ParamS_int.get_Value), the accumulate site, and the compare+branch pairs that gate the
    contribution. A reviewer can therefore re-read any segment of the conversion chain at
    the address quoted in the rule rows.
    """
    out = {"generated_by": "scripts/character_skills/skilllist_types.py",
           "native_sha256": hashlib.sha256(native.raw).hexdigest(),
           "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
           "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
           "note": ("复合分支（67／80／96／1036）的换算链逐段地址：分支体为从 leaf 出发在所属函数内的"
                    "可达指令集（条件分支两支都跟，遇该路径循环尾／共享累加尾停止，bl 只记调用点）。"
                    "5 路径 × 4 类型逐一列出。"),
           "helpers_probed": {
               "BattleParam.CalcCharaNum": {
                   "rva": hex(CALC_CHARA_NUM),
                   "signature": "CalcCharaNum(cType, paramJob, wepFlags, homeFlags, allChara)",
                   "semantics": ("遍历成员列表：跳过 [chara+0x118]==0（非存活）者；paramJob!=0 时要求 "
                                 "1<<jobId 落在 paramJob 位图内（jobId 取自 [chara+0x28]+0xf8 的 "
                                 "ParamS_int）；wepFlags!=0 时要求 [chara+0x28]+0x1b0 的 ParamS_long "
                                 "与 wepFlags 有交集；再按 IsTargetHome(homeFlags, chara) 计入。"
                                 "返回命中数。"),
                   "loop_evidence": "0x1113ddc..0x1113e6c（IsTargetHome 调用 0x1113e58，计数 0x1113e60）",
                   "named_limits": ("wepFlags／homeFlags 的位与取值字典已在 P2 第 6 批建立，"
                                    "见 filter_dictionary.json（取 P2 第 6 批，top-level 文件）")},
               "PanelManaGage.isCurrentManaJob_or": {
                   "rva": hex(MANA_JOB_OR),
                   "semantics": ("job_flag 逐位：该属性当前玛那数 >= num 即真（任一命中）；"
                                 "job_flag==0 时比较当前玛那总数（0x1243290 分支，cset w0,ge）"),
                   "compare_evidence": "0x1243284 cmp w8,w19 / 0x1243288 b.lt 跳过；0x1243298 cmp / 0x124329c cset ge"},
               "PanelManaGage.isCurrentManaJob_and": {
                   "rva": hex(MANA_JOB_AND),
                   "semantics": "job_flag 逐位：任一属性当前玛那数 < num 即假（全部命中才真）",
                   "compare_evidence": "0x1243020 cmp w8,w19 / 0x1243028 b.ge 继续 / 0x124302c b 失败"},
               "PanelManaGage.GetCurrentManaNum": {
                   "rva": hex(MANA_CURRENT),
                   "semantics": "按 job_flag 取当前玛那数（job_flag==0 取总数）",
                   "compare_evidence": "调用点后 cmp w0,#1 / b.lt 跳过（type 96 要求 >= 1）"},
               "PanelManaGage.GetCurrentScrapManaNum": {
                   "rva": hex(MANA_SCRAP),
                   "semantics": "斯库拉普（scrap）玛那计数：mov w1,#0x20; b GetCurrentManaNum",
                   "type96_selector": ("type 96 的每条分支在 get_param0 后做 "
                                       "fcmp(+inf)→b.eq 与 fcvtzs+cbnz：int(param0)==0（含 +inf 之外"
                                       "的 0 值）时 w1=0x20 走本函数，否则走 iParam0 经 "
                                       "ConvJobFlagToElementFlag 的当前玛那；两条路径的门槛(>=1)与上限"
                                       "(min) 共用"),
                   "why_it_matters": ("param0==0 的记录（本快照 18 行／23 节点／115 条答案／18 角色）"
                                      "计数对象是斯库拉普玛那，写成「当前玛那」会让读者以为这些角色"
                                      "（当前玛那常为 0）无效")},
               "BattleParam.get_hyperGauge": {
                   "rva": hex(HYPER_GAUGE_GETTER),
                   "semantics": ("返回 [this+0x328] 经 ParamS_int.get_Value() 的整数值；"
                                 "对象为空时返回 0（cbz 后直接 ret）"),
                   "identity": ("双路钉死：① 元数据字段表——BattleParam（类型 503）的 "
                                "_hyperGauge 字段偏移 0x328，属 ParamS_int 族；② 具名 getter "
                                "BattleParam.get_hyperGauge(0x10f3c10)：ldr x0,[x0,#0x328]; cbz; "
                                "b ParamS_int.get_Value(0xa92534)。注：BattleParam..ctor 内对 "
                                "+0x328 无存储（其中两处 +0x328 访问是 adrp 静态基址的类初始化指针读取，"
                                "见 0x10f8740），此前记载的「ctor 在同一偏移写入」不成立。"),
                   "consumers": "type 1036 的五条 apply 分支：get_paramN → [x+0x328] → get_Value → scvtf → fmul → fdiv 1000.0"},
           },
           "branches": {}}
    for kind in ("attack", "defence", "move", "crit_rate", "crit_dmg"):
        for t in COMPOSITE_TYPES:
            e = maps[kind].get(t) or {}
            if e.get("neutral") or not e.get("leaf"):
                continue
            ev = chain_events(native, kind, int(e["leaf"], 16))
            key = kind + "/" + str(t)
            ev["declared_exit"] = e.get("exit")
            ev["gated_by_isenable"] = e.get("gated_by_isenable")
            ev["dispatch_map_slots"] = e.get("slots")
            out["branches"][key] = ev
    return out


def composite_checks(native, maps, md=None):
    """Checks for the composite-branch batch, all re-derived from the image.

    These are the claims a reviewer would otherwise have to take on trust: that the rule
    slots are really read by the branch, that the threshold comparison is inclusive, that
    the accumulate site is reached, that 67/80/96 have no IsEnableAbility gate while 1036
    has one, and that 96's attack coefficient is selected by the caller-level damageType.
    """
    checks = []

    def add(name, ok, **kw):
        # "pass" is the key the native_checks.json schema uses; it cannot be a kwarg name
        item = dict(name=name, **kw)
        item["pass"] = bool(ok)
        checks.append(item)

    rows = composite_rule_rows(native, maps)
    by_key = {(r["effect_type"], r["field_path"]): r for r in rows}

    # (a) every rule slot is an argument-read the branch itself performs
    bad = []
    for (t, fpath), r in by_key.items():
        field = fpath.lstrip("/")
        path = {"attack_mult": "attack", "move_mult": "move", "take_mult": "defence",
                "crit_rate": "crit_rate", "crit_dmg": "crit_dmg"}.get(r["answer_kind"])
        paths = [path] if path else ["attack", "defence", "move", "crit_rate", "crit_dmg"]
        hit = False
        for p in paths:
            e = maps[p].get(t) or {}
            if e.get("neutral") or not e.get("leaf"):
                continue
            ev = chain_events(native, p, int(e["leaf"], 16))
            if any(x["field"] == field for x in ev["slots"]):
                hit = True
        if not hit:
            bad.append({"type": t, "field": field})
    add("composite_rule_slots_are_read_by_their_branch", not bad, offenders=bad[:5],
        rules=len(rows))

    # (b) the threshold comparison is inclusive: cmp then b.lt <skip>
    gate = {}
    for kind, path_t in (("attack", 67), ("defence", 67), ("move", 67),
                         ("crit_rate", 67), ("crit_dmg", 67)):
        e = maps[kind].get(path_t) or {}
        if e.get("neutral") or not e.get("leaf"):
            continue
        ev = chain_events(native, kind, int(e["leaf"], 16))
        pair = [(c["test"], c["branch"]) for c in ev["compares"]
                if c["test"].startswith("cmp w0,") and c["branch"].startswith("b.lt")]
        gate[kind] = pair
    add("composite_67_threshold_is_inclusive_ge",
        len(gate) == 5 and all(len(v) == 1 for v in gate.values()),
        pairs=gate, note="count < param0 才跳过 => 生效条件是 count >= param0（含等于），五条路径同形")

    pred = {}
    for kind in ("attack", "defence", "move", "crit_rate", "crit_dmg"):
        e = maps[kind].get(80) or {}
        if e.get("neutral") or not e.get("leaf"):
            continue
        ev = chain_events(native, kind, int(e["leaf"], 16))
        names = [h["name"] for h in ev["helpers"]]
        pred[kind] = [n for n in names if "isCurrentManaJob" in n]
    add("composite_80_uses_both_mana_predicates",
        len(pred) == 5 and all(sorted(v) == ["PanelManaGage.isCurrentManaJob_and",
                                             "PanelManaGage.isCurrentManaJob_or"] for v in pred.values()),
        predicates=pred, note="param6 选择 or／and：两条谓词都必须在该分支体内出现")

    # (c) gate presence: 1036 has IsEnableAbility, 67/80/96 do not
    got = {}
    for t in COMPOSITE_TYPES:
        seen = False
        for kind in ("attack", "defence", "move", "crit_rate", "crit_dmg"):
            e = maps[kind].get(t) or {}
            if e.get("neutral") or not e.get("leaf"):
                continue
            ev = chain_events(native, kind, int(e["leaf"], 16))
            if any(h["name"] == "BattleParam.IsEnableAbility" for h in ev["helpers"]):
                seen = True
        got[str(t)] = seen
    add("composite_gate_matches_evidence",
        got.get("1036") is True and got.get("67") is False and got.get("80") is False
        and got.get("96") is False,
        observed=got, note="1036 由 IsEnableAbility 门控；67／80／96 各自另有条件（阈值/玛那），无该门控")

    # (d) 1036's chain: get_paramN -> [+0x328] -> ParamS_int.get_Value -> scvtf -> fmul -> fdiv
    shapes = {}
    for kind in ("attack", "defence", "move", "crit_rate", "crit_dmg"):
        e = maps[kind].get(1036) or {}
        if e.get("neutral") or not e.get("leaf"):
            continue
        ev = chain_events(native, kind, int(e["leaf"], 16))
        ops = [x["op"].replace(" ", "") for x in ev["float_ops"]]
        has_val = any(h["name"] == "ParamS_int.get_Value" for h in ev["helpers"])
        shapes[kind] = {
            "param_value": has_val,
            "gauge_load": bool(ev.get("gauge_loads")),
            "scvtf": any(o.startswith("scvtf") for o in ops),
            "fmul": any(o.startswith("fmul") for o in ops),
            "fdiv_1000": any(o.startswith("fdiv") for o in ops),
            "accumulate": bool(ev.get("accumulate")),
        }
    ok_shape = bool(shapes) and all(all(v.values()) for v in shapes.values())
    add("composite_1036_chain_shape", ok_shape, shapes=shapes,
        note="每条路径都必须出现 ParamS_int.get_Value、scvtf、fmul、fdiv(1000) 并抵达累加点")

    # (e) 96's attack coefficient: the two slots are now pinned by the caller-level flag,
    #     whose meaning is the 4th argument of BattleParam.GetAbilityAttack (eDamageType)
    ev96 = chain_events(native, "attack", int(maps["attack"][96]["leaf"], 16))
    reads_both = {s["field"] for s in ev96["slots"]} & {"param2", "param3"}
    rules96 = sorted(r["field_path"].lstrip("/") for (t, _f), r in by_key.items() if t == 96)
    sel_rva = {s["field"]: s["rva"] for s in ev96["slots"] if s["field"] in ("param2", "param3")}
    add("composite_96_attack_coefficient_selected_by_damage_type",
        reads_both == {"param2", "param3"} and {"param2", "param3"} <= set(rules96)
        and sel_rva.get("param2") == "0x1107c74" and sel_rva.get("param3") == "0x1107c58",
        fields=sorted(reads_both), slot_rvas=sel_rva, rules_for_96=rules96,
        flag_semantics=("调用级标志 [sp+0x18]：GetAbilityAttack 序言里 w23=w4=damageType；"
                        "cmp w23,#1（eDamageType.Skill=1）→ 扩展路径置 [sp+0x18]=1 → 读 param3；"
                        "否则 [sp+0x18]=0 → 读 param2（0x110759c str wzr）"),
        note="两个槽各按其 damageType 条件出行（param2 非 Skill／param3 Skill）；不再作为缺证保留")

    # (f) the damageType argument really is eDamageType and both call sites are known
    md_enum = enum_values(native, md, "eDamageType")
    callers = [hex(a) for a, _m, _t, _r in callers_of(native, [0x1107390])]
    add("composite_96_damage_type_is_e_damage_type",
        md_enum.get("Skill") == 1 and md_enum.get("Normal") == 0 and len(callers) == 2,
        enum=md_enum, callers=callers,
        note=("damageType 的类型是 eDamageType（元数据），Skill=1；只有两个调用方："
              "CharaBehavior.Attack（把当次伤害类型透传）与 BattleParam.UpdateParam"
              "（mov w4, wzr 固定 0）"))

    # (g) type 96: the counting object is selected by param0 -- every path must show
    # both the scrap flag materialisation (mov w1,#0x20) and the job-flag conversion call
    sel = {}
    for kind in ("attack", "defence", "move", "crit_rate", "crit_dmg"):
        e = maps[kind].get(96) or {}
        if e.get("neutral") or not e.get("leaf"):
            continue
        ev = chain_events(native, kind, int(e["leaf"], 16))
        names = [h["name"] for h in ev["helpers"]]
        sel[kind] = {"scrap_flag": [s["rva"] for s in ev.get("scrap_flag_sites") or []],
                     "job_flag_conv": "Constants.ConvJobFlagToElementFlag" in names}
    add("composite_96_param0_selects_the_counting_object",
        len(sel) == 5 and all(v["scrap_flag"] and v["job_flag_conv"] for v in sel.values()),
        selectors=sel,
        note=("96：int(param0)==0 → 斯库拉普玛那（mov w1,#0x20 → GetCurrentScrapManaNum）；"
              "否则 → iParam0 经 ConvJobFlagToElementFlag 的当前玛那。两条路径都必须在该分支体内可见"))

    # (f) the helper identities the chain depends on
    calc = chain_events(native, "attack", int(maps["attack"][67]["leaf"], 16))
    add("composite_67_calls_calccharanum_then_multiplies",
        any(h["name"] == "BattleParam.CalcCharaNum" for h in calc["helpers"])
        and any(s["field"] == "param1" for s in calc["slots"])
        and bool(calc.get("accumulate")),
        helpers=[h["name"] for h in calc["helpers"]],
        note="67：CalcCharaNum 计数 → 阈值比较 → get_param1 → fmul 累加")
    return checks


def affected_characters(types):
    """Characters whose profile reaches a skilllist record of one of ``types``."""
    counts = collections.Counter()
    records = {}
    if not (C.ROOT / "output" / "character_skills" / "profiles" / "records.jsonl").exists():
        return counts, records
    for line in (C.ROOT / "output" / "character_skills" / "profiles" / "records.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        records[r["rec_key"]] = r
    for line in (C.ROOT / "output" / "character_skills" / "profiles" / "profiles.jsonl").open(encoding="utf-8"):
        p = json.loads(line)
        seen = set()
        for g in p.get("groups") or []:
            for ref in g.get("records") or []:
                rec = records.get(ref.get("rec_key"))
                if rec is None:
                    continue
                for cand in [rec] + list(rec.get("children") or []):
                    if cand.get("table") == "skilllist" and cand.get("effect_type") in types:
                        seen.add(cand.get("effect_type"))
        for t in seen:
            counts[t] += 1
    return counts, records


def type_evidence(native, md, maps, names, leads, affected, records):
    out = {}
    rows = C.cache_rows("skilllist")
    for t in tuple(TARGET_TYPES) + tuple(COMPOSITE_TYPES):
        recs = [r for r in rows if r.get("ability") == t]
        reps = []
        for r in recs:
            reps.append({"skillid": r["skillid"], "name": r.get("name"),
                         "text": (r.get("text") or "")[:220],
                         "params": {f"param{i}": r.get(f"param{i}") for i in range(10)
                                    if r.get(f"param{i}") is not None},
                         "iParams": {f"iParam{i}": r.get(f"iParam{i}") for i in range(2)
                                     if r.get(f"iParam{i}") is not None},
                         "sub": r.get("sub") or []})
            if len(reps) >= 4:
                break
        answer_recs = [k for k, v in records.items()
                       if v.get("table") == "skilllist" and v.get("effect_type") == t
                       and v.get("answers")]
        out[str(t)] = {
            "type": t,
            "ability_name": TYPE_NAMES.get(t) or COMPOSITE_TYPE_NAMES.get(t),
            "enum_name_from_metadata": names.get(t),
            "records": len(recs),
            "affected_characters": affected.get(t, 0),
            "apply_paths": {k: {"leaf": maps[k][t]["leaf"], "slots": maps[k][t]["slots"],
                                "neutral": maps[k][t]["neutral"]} for k in FUNCS},
            "reference_leads_only": leads.get(t, []),
            "confirmed_rule": (t in (8, 26) or t in COMPOSITE_TYPES),
            "missing_evidence": MISSING.get(t),
            "representative_records": reps,
            "records_with_answers": len(answer_recs),
        }
    return out


# ---------------------------------------------------------------------------
BASELINE = ROOT / "work" / "character_skills_p2b2" / "profiles_baseline_before_skilllist_types.json"


def snapshot_baseline():
    """Capture the pre-change per-character numbers for the increment report."""
    prof = ROOT / "output" / "character_skills" / "profiles"
    summary = json.loads((prof / "summary.json").read_text(encoding="utf-8"))
    per = {}
    with (prof / "characters.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            per[row["cid"]] = {"status": row.get("status"),
                               "answers": int(row.get("answers") or 0),
                               "unexplained_fields": int(row.get("unexplained_fields") or 0)}
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    C.write_json(BASELINE, {"source": "output/character_skills/profiles/summary.json",
                            "summary": summary, "characters": per})
    print(json.dumps({"baseline": str(BASELINE), "characters": len(per)}, ensure_ascii=False))


def main():
    C.enable_utf8_console()
    OUT.mkdir(parents=True, exist_ok=True)
    md, native = load_native()
    resolver = Resolver(native)
    maps = build_maps(native, resolver)
    names = ability_type_names(md, native)
    checks = (controlled_checks(native, md, resolver, maps)
              + composite_checks(native, maps, md) + p6_checks(native, md))
    affected, records = affected_characters(set(TARGET_TYPES) | set(COMPOSITE_TYPES)
                                            | {UNION_COUNT})
    leads = reference_leads()
    write_field_dictionary(affected, maps, native, md)
    C.write_json(OUT / "filter_dictionary.json", filter_dictionary(native, md))
    C.write_json(OUT / "union_count_chains.json", union_count_evidence(native, md))

    C.write_json(OUT / "dispatch_map.json", {
        "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
        "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
        "functions": {k: {"entry": hex(cfg["entry"]), "switch_head": hex(cfg["head"]),
                          "loop_tail": hex(cfg["tail"]),
                          "multiply_tail": hex(TAIL_MUL[k]),
                          "terminals": sorted(hex(x) for x in cfg.get("terminals") or [])}
                      for k, cfg in FUNCS.items()},
        "pattern": ("每个 type 的分支：IsEnableAbility(this, skill, target) 门控 → "
                    "skillParameter.get_paramN → fmul 累加因子（三条路径分别为攻击/受伤量/移动速度）"),
        "types": {k: _compact(k, per) for k, per in maps.items()},
        "types_key": ("entries 只列扫到槽位的分支；neutral_ranges ＝解析到循环尾（该 type 在该路径"
                      "不贡献因子，例如 ManaGet/UnionCount 不走这三条路径）；"
                      "branch_no_slots_in_window ＝解析到真实代码但窗口内未扫到槽位（单列，不并入中性）"),
        "slot_list_scope": ("复合分支（如 defence 67/80/96/1036）的 slots 是**下界估计**："
                            "以该分支体（首条无条件 b 之前）为扫描窗口得到，可能少于运行期实际读取；"
                            "type 8/26 的结论均来自单槽分支，不受此限制"),
        "ability_type_enum": names,
        "source": {"native": "work/protection/il2cpp_loader_seed1.bin",
                   "metadata": "work/protection/metadata_aei_decoded.bin",
                   "cache": C.SNAPSHOT_ID},
    })
    C.write_json(OUT / "native_checks.json", {
        "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
        "checks": checks, "passed": sum(1 for c in checks if c["pass"]), "total": len(checks),
        "limits": [
            "switch 分支解析为真实 Unicorn 仿真（执行游戏自身指令字节）；槽位列表为静态解码",
            "只证明『该 type 读哪个槽、乘进哪条因子』，不证明最终伤害/治疗数值",
            "不证明手机当前装载的 JSON 快照与实机生效状态",
        ],
    })
    def _path_summary(path):
        rows = {}
        for t, e in sorted(maps[path].items(), key=lambda kv: kv[0]):
            if e.get("neutral"):
                continue
            slots = e["slots"]
            if not slots:
                klass = "no_param_read"
            elif len(slots) > 1:
                klass = "composite_multi_slot"
            elif t in SCALED_CRIT_TYPES:
                klass = "scaled_single_slot"
            elif e.get("gated_by_isenable") and e.get("reaches_accumulate_op"):
                klass = "single_slot_rule"
            else:
                klass = "unclassified"
            rows[str(t)] = {"leaf": e["leaf"], "slots": slots, "class": klass,
                            "gate_rva": e.get("gate_rva"),
                            "slot_calls": e.get("slot_calls"),
                            "reaches_accumulate_op": e.get("reaches_accumulate_op")}
        return rows
    C.write_json(OUT / "crit_anchoring.json", {
        "question": "既有暴击口径落在哪条路径（P2 第 3 批 item 3）",
        "two_accumulators": {
            "crit_rate": {"function": "BattleParam.GetAbilityCritical", "rva": "0x1119018",
                          "switch_head": "0x11191a8", "loop_tail": "0x11195bc",
                          "mask_register": "x26（序言 0x111918c mov w26,#1）",
                          "op": "fadd（加算）", "clamp": "[0, 0.5]",
                          "branches": _path_summary("crit_rate")},
            "crit_dmg": {"function": "BattleParam.GetAbilityCriticalDmgRate", "rva": "0x1119794",
                         "switch_head": "0x1119930", "loop_tail": "0x1119dd0",
                         "mask_register": "x29（序言 0x1119918 mov w29,#1）",
                         "op": "fadd（加算）", "clamp": "[-1, 2]",
                         "branches": _path_summary("crit_dmg")},
        },
        "slot_mapping": ("暴击率路径按 type 读 param4（1/2/36/1003/1005/1026）、param5（6/7）、param6（3/34）；"
                         "暴击伤害路径读 param5（1/2/36/1003/1005/1026）、param6（6/7）、param7（3）。"
                         "同一字段名在不同 type 上分属不同路径，故规则一律按 (type, 字段) 键控"),
        "needs_its_own_evidence": {
            "1036": ("分支虽读 param4／param5 并抵达共享 fadd，但先乘运行时整数再除以 1000"
                     "（param × int([BattleParam+0x328]) / 1000），量纲与基数未确认 → "
                     "**不套用** parametric 单槽规则；该 type 在缓存与 APK 均无记录"),
            "composite_branches": ("67（0x11193d4／0x1119b90）、80（0x111920c／0x1119abc）、"
                                   "96（0x1119530／0x111997c）读多槽并调用计数／职业判定 helper，"
                                   "喂入累加器的槽未定位 → 不给规则"),
            "1112": "两路径分支都不调用 get_paramN（只读运行时字段）",
        },
        "already_ruled_anchored": {
            "7": ("既有规则 skilllist|7|/param5（暴击率 111 条）与 /param6（暴伤 110 条）"
                  "与新定位一致：rate 分支 0x1119364 读 param5、dmg 分支 0x1119a24 读 param6；"
                  "**不改既有答案数值**，只登记锚定"),
        },
        "caliber_conclusion": ("两条累加路径都是**加算**：暴击率以百分点加算、暴击伤害以系数加算，"
                               "与 2012（百分点加算）一致；但**夹紧范围按机制不同**——本路径 "
                               "rate [0,0.5]／dmg [-1,2]，2012 的 support2 路径为 [0,.5]／[-1.5,1]，"
                               "引用时不得跨机制套用夹紧值"),
        "existing_rules_elsewhere": {
            "2012": "两条路径均中性 → support2 路径（SkillAbility_SupportTarget）；夹紧 [0,.5]／[-1.5,1]",
            "3000": "中性 → Support3（_criticalDmgRate@28 经 CharaStatus._support3CtrlData@238）",
            "1008": "中性 → 读取路径未定位（既有规则来自 cid30236 字段字典）",
            "1095": "中性 → 读取路径未定位（既有规则来自 cid30236 字段字典）",
        },
        "unchanged": "本批不改动上述任何既有答案；只把它们的路径归属登记清楚",
    })
    C.write_json(OUT / "unindexed_paths.json", {
        **unindexed_reader_evidence(native),
        "question": ("APK 主表 type8 param4（2209 条、36 个取值）是否存在未索引的读取路径？"),
        "answer": ("按类型分派的读取路径：无——185 个 get_ability 调用点上 type 8 的分支都不读 param4/param0"
                   "（24 个候选命中经抽查为伪命中：其所在位置并非类型分派，如 CreatePlayer 的装配循环、"
                   "CharaBehavior.Attacked 的 support2 组装块）。"
                   "不按类型分派的读取者：存在——178 个 param4 读取点中 136 个的所属函数不按类型分派，"
                   "其中 CharaBehavior.Attacked 0x153eb1c→0x153eca4 以 int(param0)∈{0,1,2} 与槽位表查表为门控，"
                   "把 param4 写入 TimePowerUpData 后 setSupport2。"
                   "结论：不能宣称 param4 没有任何读取路径，只能说没有按类型分派的读取路径；"
                   "该 support2 路径对 type-8 记录是否可达（槽位表内容与 type-8 是否入表）未确认，"
                   "且语义为 support2 载荷、与已确认的攻/移/伤读取不同，故本批**仍不给 param4 规则**。"),
        "limits": ["筛查为有界实验：24 个候选命中未逐一手工核实（已核实 2 个为伪命中）",
                   "只证明「存在不按类型分派的 param4 读取者」，不等于 type-8 记录必然经过该路径"],
    })
    C.write_json(OUT / "type_evidence.json",
                 type_evidence(native, md, maps, names, leads, affected, records))
    C.write_json(OUT / "composite_chains.json",
                 composite_evidence(native, md, maps))
    README = f"""# skilllist 能力类型派发索引与新规则（P2 第 2 批）

只由 `scripts/character_skills/skilllist_types.py` 生成。只读既有原生镜像与解码元数据。

## 结论（已确认）

玩家侧每个能力各自乘一条因子，实现是**按 `skillParameter.get_ability()` 分派**的三张 switch：
`BattleParam.GetAbilityAttack`（攻击因子）、`GetAbilityDefence`（受伤量因子）、
`GetAbilityWalkSpeed`（移动速度因子）。每个 type 的分支形状一致：

```
IsEnableAbility(this, skill, target)   ; 资格门控
skillParameter.get_paramN              ; 该 type 真正承载语义的槽
fmul factor, factor, paramN            ; 乘进累加因子
```

本脚本用 Unicorn **执行游戏自身的 switch 前导字节**解析出每个 type 落到的分支，
再静态读出该分支访问的槽位。`dispatch_map.json` 给出 0..{MAX_TYPE} 全部 type 的结果。

- **type 8 = Always**：攻击 ← `param1`、移动速度 ← `param2`、受伤量 ← `param3`；
  `param0`/`param4` 不被三条 apply 路径读取，故不给规则——**实质依据是无读取路径**，
  不是取值本身：缓存 328 条 `param4` 恒为 1 且无 `param0` 字段，但 APK 主表 2209 条
  `param4` 有取值分布（0.0..2.5，多个非 1 值）、`param0` 存在且恒 0.0（见
  `native_checks.json` 的 `type8_param4_param0_scope_two_sources`）。
  资格门控对该 type **无条件通过**（直接进入函数尾声，w0 保持 1）。
- **type 26 = ManaGet**：`param4` = 开局追加玛那个数（受 `iParam1` 职业位图限定，`int(param4)` 次
  `ProduceManaForce`）、`iParam1` = 职业位图、`param6` = 生效范围选择码（0/1/2）、
  `param7` = 不受职业限定的额外玛那个数。路径为 `PlayerManager.PartyAbilityInit` →
  `subPartyAbilityInit_ManaGet`。
- **type 67 = HeroOne**（P2 第 5 批补全）：命中角色数 ≥ `param0` 时把 `paramN` 乘进因子——
  计数由 `BattleParam.CalcCharaNum(cType, 职业位图=iParam0, 武器位图=_flag 低 32 位（记录字段
  `flag0_0`）, 出身筛选=int(param8), 成员列表)` 给出，只统计存活且**三项同时**命中的角色；比较含等于。
- **type 1059 = UnionCount**（P2 第 6 批补全）：**玩家侧队伍范围**效果。条件由
  `BattleParam.IsEnableAbility` 的 case 1059 给出（`BattleManager.GetAllCharaList` 逐角色，
  **任一**命中 iParam0／`_flag`／int(param8) 即计入，计数 ≥ `int(param0)` 生效）；
  数值由五个 `PlayerManager.GetAbility*` 按静态 rank 表取本类型的 flag index 后应用：
  攻击 ×`param1`／移动 ×`param2`／受伤量 ×`param3`／暴击率 += `param4`（pp）／暴伤 += `param5`；
  另有周期回复 `int(param6 × 目标最大HP)`、间隔 `param7` 秒，目标按 `iParam1`／`flag1`／`param9` 筛选。
  换算链逐段见 `union_count_chains.json`。
- **type 36/1003/1005/1026（P2 第 4 批）**：三条 apply 路径上落到的分支与 type 8 **完全是同一条**
  （同一 `leaf`、同一 `gate_rva`、同一 `slot_calls`），因此攻击 ← `param1`、移动速度 ← `param2`、
  受伤量 ← `param3` 的换算与 type 8 相同，规则复用不另写一套换算。`param0` 与其余槽位
  （`param6..param9`、`flag*`、`iParam*`）本批不解释，仍按未解释字段列出。

## 复合分支：67／80／96／1036（P2 第 5 批）

这四个类型不落单槽分支，编译后 67／80／96 在**同一条路径上被合并进同一个 worker**（三者的分支
从不同标签进入同一段代码），因此线性扫描单个 leaf 看不到真实换算链。本批改用**函数内可达性遍历**
（条件分支两支都跟，遇该路径循环尾/共享累加尾停止，`bl` 只记调用点），逐段定位并把地址写进
`composite_chains.json`：

| type | 条件 | 数值换算 |
|---|---|---|
| 67 HeroOne | 命中角色数 ≥ `int(param0)`（含等于） | 攻击 ×`param1`／移动 ×`param2`／受伤量 ×`param3`／暴击率 += `param6`（pp）／暴伤 += `param7` |
| 80 HoldMana | 当前玛那满足 `isCurrentManaJob_or/and(职业位图=iParam0, 数量=int(param0))`；`param6`==0 → or，否则 and | 攻击 ×`param1`／移动 ×`param2`／受伤量 ×`param3`／暴击率 += `param7`（pp）／暴伤 += `param8` |
| 96 ManaCountUp | 计数对象由 `int(param0)` 选择（0 → 斯库拉普玛那，否则按 iParam0），按 `min(计数, int(param1))` 计入；攻击路径的系数槽由调用方实参 `damageType` 择一 | 攻击 ×(1 + `param2`×计数)（非 Skill 伤害）／×(1 + `param3`×计数)（Skill 伤害）／移动 ×(1 + `param4`×计数)／受伤量 ×(1 + `param5`×计数)／暴击率 += `param6`×计数×100pp／暴伤 += `param7`×计数 |
| 1036 HyperModeUp | `IsEnableAbility` 通过 | 攻击/移动/受伤量 ×(1 + `paramN` × hyperGauge ÷ 1000)；暴击率/暴伤 += 同式 |

- **hyperGauge 已定位**：`BattleParam.get_hyperGauge`（`0x10f3c10`）= `[this+0x328]` 经
  `ParamS_int.get_Value()` 的整数；对象为空时为 0（该分支随即中性）。`paramN × hyperGauge ÷ 1000`
  的除数 `1000.0` 来自常量池 `0x447a0000`。
- **type 96 的攻击路径已定位（P2 第 6 批）**：`BattleParam.GetAbilityAttack` 的序言把第 4 个实参
  `damageType`（`eDamageType`，Skill=1）与 1 比较，只有 Skill 走扩展缩放路径并把 `[sp+0x18]` 置 1；
  分支体在 `0x1107c48` 读该标志择槽：`!=Skill → param2`、`==Skill → param3`。两个调用方为
  `CharaBehavior.Attack`（透传当次伤害类型）与 `BattleParam.UpdateParam`（固定传 0）。
- **筛选位字典已建立（P2 第 6 批）**：`iParam0`（职业位图，位 i = JOB_TYPE i，原生 `1<<jobId`
  位测试）、`flag`（武器位图，`_flag` 低 32 位，bit = 22 + WeaponKind，掩码 `0x7fc00000`）、
  `param8`／`param9`（出身筛选值，按两位十进制分组查游戏主表 `homelist`）。字典、原生位测试与
  正文区分性对照（位图单一位 ↔ 正文单一职业/武器/出身词）见 `filter_dictionary.json`。
  67 的计数三项是**同时**满足（并），1059 是**任一**满足（或）——这一处最容易抄错。
- 本快照中 **type 1036 无记录**（缓存与 APK 的 skilllist 都没有该类型），规则已写入
  `field_dictionary.json`，当前只产出 0 条答案。

## 双路核对（P2 第 4 批常驻检查）

仿真可能因为「switch 前导中位测试常量寄存器被预设成什么值」而悄悄走错分支：P2 第 3 批的审查
正是在这一点上抓到 11 个暴击分支被误判中性。为避免同类错误在未来路径上复发，本脚本现在同时
用两条独立路径解析每个 type：

- **仿真路径**：Unicorn 执行 switch 前导字节，`mask_registers(kind)` 扫描序言中 `mov wN,#1`
  的位测试常量寄存器并按序预置（不是人工钉死某个寄存器号）；
- **静态路径**：`static_leaf_map()` 只做指令解码，自己维护寄存器值与标志位，直接算出门控条件
  与 branch target，不做任何执行。

`native_checks.json` 的 `switch_resolution_sim_matches_static` 逐 type 比较两者的 `leaf`
（{len(FUNCS)} 条路径 × {MAX_TYPE + 1} 个 type）。**不一致即报错**，不静默取其一。

## 证据强度

`native_checks.json` 的 `evidence_kind` 是 `CONTROLLED_NATIVE_FRAGMENT`：switch 分支解析为真实
Unicorn 仿真；槽位列表为静态指令解码；并把各条 apply 路径的槽位与 `rules.json` 既有已确认规则
交叉核对（未落在这些路径上的既有字段登记在 `read_elsewhere`）。

**复合分支的槽位清单是下界估计**：槽位扫描以该分支体自身为窗口（首条无条件 `b` 之前、
或到共享 `fmul s8,s8,s0` 为止），因此可能少于运行期实际读取的槽位——例如 defence 67/80/96/1036
这类复合分支会在体内调用 `CalcCharaNum`／`GetMemberList` 等helper 后再读多个槽。
`dispatch_map.json` 的 `slot_list_scope` 字段记录同一口径；`leaf`＝分支目标、`gate_rva`＝分支体内
`bl IsEnableAbility` 的地址、`slot_calls`＝各槽读取指令地址，便于逐项复核。
type 8/26 的结论均来自单槽分支，不受该限制。

## 重跑

```powershell
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/skilllist_types.py
```
"""
    (OUT / "README.md").write_text(README, encoding="utf-8")
    print(json.dumps({"checks": f"{sum(1 for c in checks if c['pass'])}/{len(checks)}",
                      "affected": dict(affected), "out": str(OUT)}, ensure_ascii=False))


SAME_LEAF_RECORDS_BASELINE = ROOT / "work" / "character_skills_p4_records_before.jsonl"


SAME_LEAF_SUMMARY_BASELINE = ROOT / "work" / "character_skills_p4_summary_before.json"


CRIT_BASELINE = ROOT / "work" / "character_skills_p3" / "summary_before_p3.json"


CRIT_RECORDS_BASELINE = ROOT / "work" / "character_skills_p3" / "records_before_p3.jsonl"


def _answer_keys(path):
    """{(table, record_id, layer, field): (effect_type, kind)} over records + children.

    Sub-effect records carry no ``rec_key``, so the identity has to be built from the
    record coordinates; keying on ``rec_key`` alone collapses every child into one bucket.
    """
    out = {}
    for line in Path(path).open(encoding="utf-8"):
        r = json.loads(line)
        for holder in [r] + [c for c in (r.get("children") or [])
                             if isinstance(c, dict) and "answers" in c]:
            for a in holder.get("answers") or []:
                out[(holder.get("table"), holder.get("record_id"), holder.get("layer"),
                     a["f"])] = (holder.get("effect_type"), a.get("kind"))
    return out


def report_crit_increment():
    """Answers *added* by the critical batch, per type, in the dual caliber.

    "Added" is a snapshot diff against ``records_before_p3.jsonl`` -- counting all crit
    answers of these types would also include the pre-existing type 7 rules.
    """
    prof = ROOT / "output" / "character_skills" / "profiles"
    summary = json.loads((prof / "summary.json").read_text(encoding="utf-8"))
    base_sum = json.loads(CRIT_BASELINE.read_text(encoding="utf-8")) if CRIT_BASELINE.exists() else None
    now = _answer_keys(prof / "records.jsonl")
    before = _answer_keys(CRIT_RECORDS_BASELINE) if CRIT_RECORDS_BASELINE.exists() else {}
    added = {k: v for k, v in now.items() if k not in before and "暴击" in (v[1] or "")}

    recs = {}
    for line in (prof / "records.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        for holder in [r] + [c for c in (r.get("children") or [])
                             if isinstance(c, dict) and "answers" in c]:
            recs.setdefault(holder.get("rec_key") or id(holder), holder)

    page = collections.Counter()
    chars = collections.Counter()
    any_char = set()
    for line in (prof / "profiles.jsonl").open(encoding="utf-8"):
        pp = json.loads(line)

        def walk(rec, cid):
            et_hit = False
            for a in rec.get("answers") or []:
                k = (rec.get("table"), rec.get("record_id"), rec.get("layer"), a["f"])
                if k in added:
                    page[added[k][0]] += 1
                    et_hit = True
            for ch in rec.get("children") or []:
                if isinstance(ch, dict) and "answers" in ch:
                    et_hit = walk(ch, cid) or et_hit
            return et_hit
        hit = False
        for g in pp.get("groups") or []:
            for ref in g.get("records") or []:
                r = recs.get(ref.get("rec_key"))
                if r is not None:
                    hit = walk(r, pp["cid"]) or hit
        if hit:
            any_char.add(pp["cid"])
    for k, (et, _) in added.items():
        pass
    uniq = collections.Counter()
    for k, (et, _) in added.items():
        uniq[et] += 1

    def delta(key):
        if not base_sum:
            return None
        return [base_sum["totals"][key], summary["totals"][key]]

    payload = {
        "types": list(CRIT_TYPES_ALL),
        "new_answers_page_sum": sum(page.values()),
        "new_answers_unique_records": sum(uniq.values()),
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(page.items())},
        "answers_by_type_unique_records": {str(k): v for k, v in sorted(uniq.items())},
        "characters_with_added_crit_answers": len(any_char),
        "delta_vs_p2b2_baseline": {
            "answers_page_sum": delta("rule_answers"),
            "answers_unique_records": delta("rule_answers_unique_records"),
            "unexplained_fields": delta("unexplained_fields"),
            "status": [base_sum.get("status_counts"), summary["status_counts"]] if base_sum else None,
        },
        "caliber_note": ("页求和＝按角色页引用「本批新增」的暴击答案；唯一记录＝按"
                         "（表, 记录, 层, 字段）去重（子效果记录同键规则）；"
                         "两者都由 records.jsonl 与 work/character_skills_p3/records_before_p3.jsonl "
                         "的快照差集得到，因此不含 type 7 等既有暴击规则的旧答案"),
    }
    C.write_json(OUT / "crit_increment.json", payload)
    print(json.dumps(payload, ensure_ascii=False))


def report_same_leaf_increment():
    """Answers *added* by the same-leaf batch (P2 batch 4), per type, dual caliber.

    "Added" is a snapshot diff against ``work/character_skills_p4_records_before.jsonl``
    filtered to the three reused slots, so the pre-existing crit rules of the same four
    types (param4/param5, added in batch 3) are not counted again.

    The affected-character number is deliberately the reachability caliber: a character
    counts when its profile page can reach such a record, whether or not it already had
    answers for that type. That is why it is larger than the status-migration count,
    which only moves characters that had no answer at all before this batch.
    """
    prof = ROOT / "output" / "character_skills" / "profiles"
    summary = json.loads((prof / "summary.json").read_text(encoding="utf-8"))
    base_sum = (json.loads(SAME_LEAF_SUMMARY_BASELINE.read_text(encoding="utf-8"))
                if SAME_LEAF_SUMMARY_BASELINE.exists() else None)
    slots = {f.lstrip("/") for _, f, _ in SAME_LEAF_FIELDS}
    before = (_answer_keys(SAME_LEAF_RECORDS_BASELINE)
              if SAME_LEAF_RECORDS_BASELINE.exists() else {})
    now = _answer_keys(prof / "records.jsonl")
    added = {k: v for k, v in now.items()
             if k not in before and v[0] in SAME_LEAF_AS_TYPE8 and k[3].lstrip("/") in slots}

    recs = {}
    for line in (prof / "records.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        recs.setdefault(r.get("rec_key") or id(r), r)

    page = collections.Counter()
    by_type_any_char = collections.defaultdict(set)
    any_char = set()
    migrated = 0
    for line in (prof / "profiles.jsonl").open(encoding="utf-8"):
        pp = json.loads(line)
        preexisting = [False]

        def walk(rec):
            hit = set()
            for a in rec.get("answers") or []:
                k = (rec.get("table"), rec.get("record_id"), rec.get("layer"), a["f"])
                if k in added:
                    page[added[k][0]] += 1
                    hit.add(added[k][0])
                elif rec.get("table") and a["f"] is not None:
                    preexisting[0] = True
            for ch in rec.get("children") or []:
                if isinstance(ch, dict) and "answers" in ch:
                    hit |= walk(ch)
            return hit
        got = set()
        for g in pp.get("groups") or []:
            for ref in g.get("records") or []:
                r = recs.get(ref.get("rec_key"))
                if r is not None:
                    got |= walk(r)
        for t in got:
            by_type_any_char[t].add(pp["cid"])
        if got:
            any_char.add(pp["cid"])
            # "仅未知" means the page had no answer at all: so a character migrated iff
            # every answer it now carries is one this batch added
            if not preexisting[0]:
                migrated += 1

    uniq = collections.Counter()
    for _, (et, _k) in added.items():
        uniq[et] += 1
    # record-level caliber: a record counts its own answers plus its children's, in
    # place, so an answer living in a sub-effect record is counted once per parent that
    # embeds it (this is the caliber summary.rule_answers_unique_records uses)
    record_level = collections.Counter()
    for line in (prof / "records.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        for holder in [r] + [c for c in (r.get("children") or [])
                             if isinstance(c, dict) and "answers" in c]:
            for a in holder.get("answers") or []:
                k = (holder.get("table"), holder.get("record_id"), holder.get("layer"), a["f"])
                if k in added:
                    record_level[added[k][0]] += 1

    def delta(key):
        if not base_sum:
            return None
        return [base_sum["totals"].get(key), summary["totals"].get(key)]

    payload = {
        "types": list(SAME_LEAF_AS_TYPE8),
        "slots": sorted(slots),
        "new_answers_page_sum": sum(page.values()),
        "new_answers_unique_records": sum(uniq.values()),
        "new_answers_record_level": sum(record_level.values()),
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(page.items())},
        "answers_by_type_unique_records": {str(k): v for k, v in sorted(uniq.items())},
        "answers_by_type_record_level": {str(k): v for k, v in sorted(record_level.items())},
        "characters_reachable_page_sum": {str(t): len(v)
                                          for t, v in sorted(by_type_any_char.items())},
        "characters_reachable_total": len(any_char),
        "status_migrations_unknown_to_partial": migrated,
        "status_counts_dir": ["work/character_skills_p4_summary_before.json",
                              "output/character_skills/profiles/summary.json"],
        "status_counts_before": (base_sum or {}).get("status_counts"),
        "status_counts_after": summary.get("status_counts"),
        "delta_vs_p3_baseline": {
            "answers_page_sum": delta("rule_answers"),
            "answers_unique_records": delta("rule_answers_unique_records"),
            "unexplained_fields": delta("unexplained_fields"),
        },
        "caliber_note": (
            "页求和＝按角色页引用「本批新增」的同叶答案（同一 skilllist 记录被多角色共享则各计一次，"
            "子效果记录经父记录到达）；唯一记录＝按（表, 记录, 层, 字段）去重；记录级＝summary.rule_answers_unique_records 口径"
            "（每条记录计自身答案＋其子记录答案，子效果记录被嵌入几次就计几次）；"
            "可达角色＝档案页能到达过该类型记录的角色数（不要求此前无答案），"
            "因此大于状态迁移数（仅统计此前一条答案都没有、本批才得到答案的角色）。"
            "新增集合由 records.jsonl 与 work/character_skills_p4_records_before.jsonl 的快照差集得到，"
            f"并限定 slot ∈ {sorted(slots)}，故不含第 3 批已加入的 param4/param5 暴击答案"),
    }
    C.write_json(OUT / "same_leaf_increment.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=1))


COMPOSITE_RECORDS_BASELINE = ROOT / "work" / "p5_records_before.jsonl"


COMPOSITE_SUMMARY_BASELINE = ROOT / "work" / "p5_summary_before.json"


P6_RECORDS_BASELINE = ROOT / "work" / "p6_records_before.jsonl"
P6_SUMMARY_BASELINE = ROOT / "work" / "p6_summary_before.json"


def report_p6_increment():
    """Answers added by P2 batch 6 (96 attack slots, filter dictionaries, 1059).

    Same three calibers as the other batches; the delta is taken against the P5 final
    snapshot (``work/p6_records_before.jsonl``) so the P5 artifact stays historical.
    """
    prof = ROOT / "output" / "character_skills" / "profiles"
    summary = json.loads((prof / "summary.json").read_text(encoding="utf-8"))
    base_sum = (json.loads(P6_SUMMARY_BASELINE.read_text(encoding="utf-8"))
                if P6_SUMMARY_BASELINE.exists() else None)
    md, native = load_native()
    maps = build_maps(native, Resolver(native))
    rules = {}
    for r in (composite_rule_rows(native, maps) + filter_rule_rows()
              + union_count_rule_rows(native, md)):
        rules.setdefault(r["effect_type"], set()).add(r["field_path"].lstrip("/"))
    before = _answer_keys(P6_RECORDS_BASELINE) if P6_RECORDS_BASELINE.exists() else {}
    now = _answer_keys(prof / "records.jsonl")
    added = {k: v for k, v in now.items()
             if k not in before and v[0] in rules and k[3].lstrip("/") in rules[v[0]]}

    def _full_answers(path):
        out = {}
        for line in Path(path).open(encoding="utf-8"):
            r = json.loads(line)
            for holder in [r] + [c for c in (r.get("children") or [])
                                 if isinstance(c, dict) and "answers" in c]:
                for a in holder.get("answers") or []:
                    out[(holder.get("table"), holder.get("record_id"), holder.get("layer"),
                         a["f"])] = a
        return out

    full_before = _full_answers(P6_RECORDS_BASELINE) if P6_RECORDS_BASELINE.exists() else {}
    full_now = _full_answers(prof / "records.jsonl")
    lost = [k for k in full_before if k not in full_now]
    changed_raw = [k for k, v in full_before.items() if k in full_now
                   and any(full_now[k].get(f) != v.get(f)
                           for f in ("raw", "kind", "unit", "status", "scope"))]

    recs = {}
    for line in (prof / "records.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        recs.setdefault(r.get("rec_key") or id(r), r)
    page, record_level = collections.Counter(), collections.Counter()
    by_type_chars = collections.defaultdict(set)
    any_char = set()
    migrated = 0
    for line in (prof / "profiles.jsonl").open(encoding="utf-8"):
        pp = json.loads(line)
        preexisting = [False]

        def walk(rec):
            hit = set()
            for a in rec.get("answers") or []:
                k = (rec.get("table"), rec.get("record_id"), rec.get("layer"), a["f"])
                if k in added:
                    page[added[k][0]] += 1
                    record_level[added[k][0]] += 1
                    hit.add(added[k][0])
                elif rec.get("table"):
                    preexisting[0] = True
            for ch in rec.get("children") or []:
                if isinstance(ch, dict) and "answers" in ch:
                    hit |= walk(ch)
            return hit
        got = set()
        for g in pp.get("groups") or []:
            for ref in g.get("records") or []:
                r = recs.get(ref.get("rec_key"))
                if r is not None:
                    got |= walk(r)
        for t in got:
            by_type_chars[t].add(pp["cid"])
        if got:
            any_char.add(pp["cid"])
            if not preexisting[0]:
                migrated += 1
    uniq = collections.Counter()
    for _, (et, _k) in added.items():
        uniq[et] += 1

    def delta(key):
        if not base_sum:
            return None
        return [base_sum["totals"].get(key), summary["totals"].get(key)]

    payload = {
        "batch": "P2 第 6 批",
        "types": [96, 67, 80, 1059],
        "rules_added": {str(t): sorted(f) for t, f in sorted(rules.items())},
        "rule_count_added": sum(len(v) for v in rules.values()),
        "new_answers_page_sum": sum(page.values()),
        "new_answers_unique_records": sum(uniq.values()),
        "new_answers_record_level": sum(record_level.values()),
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(page.items())},
        "answers_by_type_unique_records": {str(k): v for k, v in sorted(uniq.items())},
        "answers_by_type_record_level": {str(k): v for k, v in sorted(record_level.items())},
        "characters_reachable_page_sum": {str(t): len(v) for t, v in sorted(by_type_chars.items())},
        "characters_reachable_total": len(any_char),
        "status_migrations_unknown_to_partial": migrated,
        "status_counts_before": (base_sum or {}).get("status_counts"),
        "status_counts_after": summary.get("status_counts"),
        "existing_answer_keys_lost": len(lost),
        "existing_answer_keys_raw_kind_status_changed": len(changed_raw),
        "delta_vs_p5_baseline": {
            "answers_page_sum": delta("rule_answers"),
            "answers_unique_records": delta("rule_answers_unique_records"),
            "unexplained_fields": delta("unexplained_fields"),
        },
        "caliber_note": ("页求和＝按角色页引用计数；唯一记录＝按（表, 记录, 层, 字段）去重；"
                         "记录级＝summary.rule_answers_unique_records 口径。新增集合由 records.jsonl "
                         "与 work/p6_records_before.jsonl（P5 终态）的快照差集得到，并限定在本批 "
                         "(type, 字段) 规则内。"),
    }
    C.write_json(OUT / "p6_increment.json", payload)
    print(json.dumps({k: payload[k] for k in
                      ("new_answers_page_sum", "new_answers_unique_records",
                       "answers_by_type_page_sum", "characters_reachable_page_sum",
                       "status_migrations_unknown_to_partial", "existing_answer_keys_lost")},
                     ensure_ascii=False, indent=1))


def report_composite_increment():
    """Answers *added* by the composite batch (P2 batch 5), per type, three calibers.

    Calibers: page sum (one answer instance per character-page reference), unique rows
    ((table, record_id, layer, field)) and the record-level caliber used by
    ``summary.rule_answers_unique_records`` (a record counts its own answers plus its
    children's, in place).
    """
    prof = ROOT / "output" / "character_skills" / "profiles"
    summary = json.loads((prof / "summary.json").read_text(encoding="utf-8"))
    base_sum = (json.loads(COMPOSITE_SUMMARY_BASELINE.read_text(encoding="utf-8"))
                if COMPOSITE_SUMMARY_BASELINE.exists() else None)
    _md, _native = load_native()
    _maps = build_maps(_native, Resolver(_native))
    rules = {}
    for r in composite_rule_rows(_native, _maps):
        rules.setdefault(r["effect_type"], set()).add(r["field_path"].lstrip("/"))
    before = (_answer_keys(COMPOSITE_RECORDS_BASELINE)
              if COMPOSITE_RECORDS_BASELINE.exists() else {})
    now = _answer_keys(prof / "records.jsonl")
    added = {k: v for k, v in now.items()
             if k not in before and v[0] in rules and k[3].lstrip("/") in rules[v[0]]}

    recs = {}
    for line in (prof / "records.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        recs.setdefault(r.get("rec_key") or id(r), r)

    page = collections.Counter()
    by_type_chars = collections.defaultdict(set)
    any_char = set()
    migrated = 0
    for line in (prof / "profiles.jsonl").open(encoding="utf-8"):
        pp = json.loads(line)
        preexisting = [False]

        def walk(rec):
            hit = set()
            for a in rec.get("answers") or []:
                k = (rec.get("table"), rec.get("record_id"), rec.get("layer"), a["f"])
                if k in added:
                    page[added[k][0]] += 1
                    hit.add(added[k][0])
                elif rec.get("table"):
                    preexisting[0] = True
            for ch in rec.get("children") or []:
                if isinstance(ch, dict) and "answers" in ch:
                    hit |= walk(ch)
            return hit
        got = set()
        for g in pp.get("groups") or []:
            for ref in g.get("records") or []:
                r = recs.get(ref.get("rec_key"))
                if r is not None:
                    got |= walk(r)
        for t in got:
            by_type_chars[t].add(pp["cid"])
        if got:
            any_char.add(pp["cid"])
            if not preexisting[0]:
                migrated += 1

    uniq = collections.Counter()
    for _, (et, _k) in added.items():
        uniq[et] += 1
    record_level = collections.Counter()
    for line in (prof / "records.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        for holder in [r] + [c for c in (r.get("children") or [])
                             if isinstance(c, dict) and "answers" in c]:
            for a in holder.get("answers") or []:
                k = (holder.get("table"), holder.get("record_id"), holder.get("layer"), a["f"])
                if k in added:
                    record_level[added[k][0]] += 1

    def delta(key):
        if not base_sum:
            return None
        return [base_sum["totals"].get(key), summary["totals"].get(key)]

    payload = {
        "types": list(COMPOSITE_TYPES),
        "rules": {str(t): sorted(f) for t, f in sorted(rules.items())},
        "unanswered_rule_slots": {"96": ["param2", "param3"],
                                  "why": ("攻击路径的系数在 param2／param3 之间由调用级标志 "
                                          "[sp+0x18] 选择，含义未定位")},
        "new_answers_page_sum": sum(page.values()),
        "new_answers_unique_records": sum(uniq.values()),
        "new_answers_record_level": sum(record_level.values()),
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(page.items())},
        "answers_by_type_unique_records": {str(k): v for k, v in sorted(uniq.items())},
        "answers_by_type_record_level": {str(k): v for k, v in sorted(record_level.items())},
        "characters_reachable_page_sum": {str(t): len(v) for t, v in sorted(by_type_chars.items())},
        "characters_reachable_total": len(any_char),
        "status_migrations_unknown_to_partial": migrated,
        "status_counts_before": (base_sum or {}).get("status_counts"),
        "status_counts_after": summary.get("status_counts"),
        "delta_vs_p4_baseline": {
            "answers_page_sum": delta("rule_answers"),
            "answers_unique_records": delta("rule_answers_unique_records"),
            "unexplained_fields": delta("unexplained_fields"),
        },
        "caliber_note": ("页求和＝按角色页引用计数；唯一记录＝按（表, 记录, 层, 字段）去重；"
                         "记录级＝summary.rule_answers_unique_records 口径（每条记录计自身答案＋"
                         "子记录答案）。新增集合由 records.jsonl 与 work/p5_records_before.jsonl 的"
                         "快照差集得到，并限定在本批 (type, 字段) 规则内。"
                         "type 1036 在本快照无记录，规则已发布但产出 0 条答案。"),
    }
    C.write_json(OUT / "composite_increment.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=1))


def report_increment():
    """New answers / unexplained drop / status migration for this batch."""
    prof = ROOT / "output" / "character_skills" / "profiles"
    summary = json.loads((prof / "summary.json").read_text(encoding="utf-8"))
    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else None
    records = [json.loads(l) for l in (prof / "records.jsonl").open(encoding="utf-8")]
    rec_by_key = {r["rec_key"]: r for r in records}
    per_type_page = collections.Counter()
    per_type_unique = collections.defaultdict(set)
    unique = set()
    nonlocal_page = [0]
    # page-sum counts one answer instance per character reference; sub-ability records
    # are reached through their parent's children, so the walk recurses.
    for line in (prof / "profiles.jsonl").open(encoding="utf-8"):
        pp = json.loads(line)

        def walk(rec):
            nonlocal_page[0] += 0
            if rec.get("table") == "skilllist" and rec.get("effect_type") in TARGET_TYPES:
                for a in rec.get("answers") or []:
                    per_type_page[rec["effect_type"]] += 1
                    per_type_unique[rec["effect_type"]].add(
                        (rec.get("rec_key") or rec.get("table"), a["f"]))
                    unique.add((rec.get("rec_key") or rec.get("table"), a["f"]))
                    nonlocal_page[0] += 1
            for ch in rec.get("children") or []:
                if isinstance(ch, dict) and "answers" in ch:
                    walk(ch)
        for g in pp.get("groups") or []:
            for ref in g.get("records") or []:
                rec = rec_by_key.get(ref.get("rec_key"))
                if rec is not None:
                    walk(rec)
    delta = None
    if base:
        bsum = base["summary"]
        bper = base["characters"]
        cur = {}
        with (prof / "characters.csv").open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                cur[row["cid"]] = {"status": row.get("status"),
                                   "answers": int(row.get("answers") or 0)}
        migrated = [c for c in bper if bper[c]["status"] == "仅未知"
                    and cur.get(c, {}).get("status") == "部分"]
        delta = {
            "baseline": str(BASELINE.relative_to(ROOT)).replace("\\", "/"),
            "answers_page_sum_before": bsum["totals"]["rule_answers"],
            "answers_page_sum_after": summary["totals"]["rule_answers"],
            "answers_unique_before": bsum["totals"]["rule_answers_unique_records"],
            "answers_unique_after": summary["totals"]["rule_answers_unique_records"],
            "unexplained_fields_before": bsum["totals"]["unexplained_fields"],
            "unexplained_fields_after": summary["totals"]["unexplained_fields"],
            "status_before": bsum["status_counts"], "status_after": summary["status_counts"],
            "characters_unknown_to_partial": len(migrated),
            "characters_unknown_to_partial_ids": migrated[:40],
        }
    gaps = json.loads((ROOT / "output" / "character_skills" / "gaps" / "gap_queue.json")
                      .read_text(encoding="utf-8"))["counts"]
    page = nonlocal_page[0]
    # record-store caliber (what summary.rule_answers_unique_records counts): each stored
    # record contributes its own answers plus every child's answers, so a record embedded
    # as a child effect is counted once per parent that carries it.
    standalone = child_rows = 0
    store = prof / "records.jsonl"
    for line in store.open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("table") == "skilllist" and r.get("effect_type") in TARGET_TYPES:
            standalone += len(r.get("answers") or [])
        for ch in r.get("children") or []:
            if (isinstance(ch, dict) and ch.get("table") == "skilllist"
                    and ch.get("effect_type") in TARGET_TYPES):
                child_rows += len(ch.get("answers") or [])
    drop = None
    if base:
        drop = (base["summary"]["totals"]["unexplained_fields"]
                - summary["totals"]["unexplained_fields"])
    payload = {
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(per_type_page.items())},
        "answers_by_type_unique_records": {str(k): len(v)
                                           for k, v in sorted(per_type_unique.items())},
        "new_answers_page_sum": page,
        "new_answers_unique_records": len(unique),
        "dual_caliber_note": ("三个口径并列：页求和＝按角色页引用计数；"
                              "全局唯一＝按（记录, 字段）去重；"
                              "记录级＝summary 口径（自身答案＋子记录答案）"),
        "unexplained_fields_drop": drop if drop is not None else len(unique),
        "new_answers_summary_caliber": standalone + child_rows,
        "new_answers_summary_caliber_detail": {
            "standalone_records": standalone, "as_children_of_a_record": child_rows,
            "note": ("summary.rule_answers_unique_records 按「存储记录」计数：每条记录计自身答案"
                     "＋其子记录的答案，因此被当作子效果嵌入的记录按每个父记录各计一次。"
                     "所以同一批增量有两个都正确的口径——全局唯一（记录,字段）"
                     f"{len(unique)} 与 记录级 {standalone + child_rows}"
                     f"（＝standalone {standalone} ＋ children {child_rows}）；"
                     "页求和口径见 new_answers_page_sum"),
        },
        "delta_vs_p2b1_baseline": delta,
        "gaps_after": gaps,
    }
    C.write_json(OUT / "increment.json", payload)
    print(json.dumps({k: v for k, v in payload.items() if k != "delta_vs_p2b1_baseline"},
                     ensure_ascii=False))
    if delta:
        print(json.dumps(delta, ensure_ascii=False))


if __name__ == "__main__":
    if "--report-p6-increment" in sys.argv:
        C.enable_utf8_console()
        report_p6_increment()
    elif "--report-composite-increment" in sys.argv:
        report_composite_increment()
    elif "--report-same-leaf-increment" in sys.argv:
        report_same_leaf_increment()
    elif "--report-crit-increment" in sys.argv:
        C.enable_utf8_console()
        report_crit_increment()
    elif "--report-increment" in sys.argv:
        C.enable_utf8_console()
        report_increment()
    elif "--snapshot-baseline" in sys.argv:
        C.enable_utf8_console()
        snapshot_baseline()
    else:
        main()
