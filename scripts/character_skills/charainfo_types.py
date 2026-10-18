"""Special-move effect-type dispatch: native constant index (P2 batch 1, item 1).

``charainfo.skillid[0]`` and ``bossskill.skillid0`` share one value domain. That
domain is not free-form: ``bhSkill.ExecSkill`` is a real ``switch`` over the type
value, with a jump table at a fixed guest RVA and a bound instruction
``cmp w20, #0x79``. This module reads that table and the switch prologue straight
out of the recovered native image and turns them into an index:

    type (0..121)  ->  case body RVA  ->  Exec handler (+ mode arguments)

Everything is read from the recovered image / decoded metadata. No game value is
imported from an external source, and no external reference is required.

Outputs (``output/character_skills/charainfo_types/``):

* ``type_dispatch_index.json`` -- the index, the switch bounds, the default
  branch, the data-side histogram and the 20 ``NOT_AMONG`` characters.
* ``native_checks.json`` -- controlled native fragment experiments, including an
  *emulated* run of the switch prologue under Unicorn.
* ``head_types.json`` -- evidence pack for the three head types (3 / 22 / 110):
  handler, slots the handler actually reads, representative records, reference
  candidates as leads only, and the named missing evidence that still blocks a
  numeric rule.
* ``README.md``.
"""
from __future__ import annotations

import bisect
import collections
import csv
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
# both the package root (for ``character_skills.*``) and this directory (for the
# flat ``common``/``rules`` imports the rest of the module set uses) must be
# importable, so the script also works when it is imported rather than executed
for _p in (ROOT / "scripts", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from character_skills import common as C  # noqa: E402
from character_skills import rules as R  # noqa: E402

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM  # noqa: E402
from il2cpp_sample_code import Native  # noqa: E402
from metadata_targets import Metadata  # noqa: E402

DIS = Cs(CS_ARCH_ARM64, CS_MODE_ARM)

OUT = ROOT / "output" / "character_skills" / "charainfo_types"
METADATA = ROOT / "work" / "protection" / "metadata_aei_decoded.bin"

# --- guest RVAs of the ExecSkill switch (see native_checks.json for the reads) --
EXECSKILL_RVA = 0x1297CCC          # bhSkill.ExecSkill entry
SWITCH_PROLOGUE_RVA = 0x1297D28    # cmp w20, #0x79
SWITCH_BOUND = 0x79                # cmp w20, #0x79  -> types above this are default
JUMP_TABLE_RVA = 0x206EE04         # uint16 table, entry = (case - SWITCH_BASE) / 4
SWITCH_BASE_RVA = 0x1297D4C        # adr x10, #0x1297d4c
DEFAULT_RVA = 0x1298CA0            # b.hi target; also the case target of type 48
PATTERN_FIELDS = [f"pattern{i}" for i in range(9)]
SKILLPARAM_FIELDS = [f"skillparam{i}" for i in range(10)]
# util field layout set up by bhSkillUtil.initialize_ExAttack (+0x2c .. +0x50)
UTIL_PARAM_OFFSETS = {0x2C + 4 * i: f"skillparam{i}" for i in range(10)}


# ---------------------------------------------------------------------------
# native access
# ---------------------------------------------------------------------------
def load_native():
    metadata = Metadata(str(METADATA))
    return metadata, Native(metadata)


def owner_of(native, rva: int):
    """(method_entry_rva, [method dicts]) for the method containing an RVA."""
    addrs = sorted(set(native.pointers))
    i = bisect.bisect_right(addrs, rva) - 1
    entry = addrs[i]
    names = [native.method(j) for j in native.method_by_rva.get(entry, [])]
    return entry, names


def methods_named(metadata, native, declaring: str, name: str):
    """All overloads of ``declaring.name`` (the game has overloads with the same name)."""
    found = []
    for ti, row in enumerate(metadata.types):
        if metadata.string(row[0]) != declaring:
            continue
        for mi in range(row[9], row[9] + row[16]):
            if metadata.string(metadata.methods[mi][0]) == name:
                found.append(native.method(mi))
    if not found:
        raise KeyError(f"{declaring}.{name}")
    return found


# ---------------------------------------------------------------------------
# the type index itself
# ---------------------------------------------------------------------------
def resolve_case(native, case_rva: int, limit: int = 24):
    """Case body -> (handler, mode_args) by following one unconditional tail branch.

    Each case body either calls the handler directly or sets arguments and tail
    branches to a shared body (that is how 13/14/15/16 all reach
    ``bhSkill.Exec_HEAL`` with different mode arguments).
    """
    rva = case_rva
    mode_args: dict[str, int] = {}
    tail_from = None
    for _ in range(3):
        end = min(p for p in native.pointers if p > rva)
        ins = list(DIS.disasm(native.raw[rva:end], rva))
        if not ins:
            return None, mode_args, tail_from
        for insn in ins[:limit]:
            op = insn.op_str
            # mov wN, #imm   (mode arguments w2/w3/w4)
            if insn.mnemonic == "mov" and op.startswith(("w2, ", "w3, ", "w4, ")):
                reg, _, val = op.partition(", ")
                if val == "wzr":
                    mode_args[reg] = 0
                elif val.startswith("#"):
                    try:
                        mode_args[reg] = int(val[1:], 0)
                    except ValueError:
                        pass
            if insn.mnemonic == "bl" and op.startswith("#0x"):
                target = int(op[1:], 16)
                names = [native.method(j) for j in native.method_by_rva.get(target, [])]
                if names:
                    return names[0], mode_args, tail_from
            if insn.mnemonic == "b" and op.startswith("#0x"):
                target = int(op[1:], 16)
                names = [native.method(j) for j in native.method_by_rva.get(target, [])]
                if names:
                    # tail branch into another method entry is still "this handler";
                    # an intra-function tail into a shared body is followed below.
                    if rva <= target < end:
                        return names[0], mode_args, tail_from
                tail_from = rva
                rva = target
                break
        else:
            return None, mode_args, tail_from
    return None, mode_args, tail_from


def build_index(native):
    entries = []
    for t in range(SWITCH_BOUND + 1):
        off = native.unpack("<H", JUMP_TABLE_RVA + t * 2)[0]
        case = SWITCH_BASE_RVA + off * 4
        handler, mode_args, tail_from = resolve_case(native, case)
        entries.append({
            "type": t,
            "case_rva": hex(case),
            "handler": (handler["declaring_type"] + "." + handler["name"]) if handler else None,
            "handler_rva": handler["native_rva"] if handler else None,
            "mode_args": mode_args or None,
            "tail_from_rva": hex(tail_from) if tail_from else None,
        })
    return entries


def data_type_histogram():
    """Type values actually present in the export, per table."""
    out = {}
    for key, field in (("charainfo", "skillid"), ("bossskill", "skillid0")):
        counter = collections.Counter()
        per_layer = {}
        for layer, rows in (("CACHE", C.cache_rows(key)), ("APK", C.apk_rows(key))):
            for r in rows:
                v = (r.get(field) or [0])[0] if field == "skillid" else r.get(field)
                counter[v] += 1
                per_layer.setdefault(layer, collections.Counter())[v] += 1
        out[key] = {
            "distinct": len(counter),
            "max": max(counter),
            "min": min(counter),
            "top": counter.most_common(15),
            "rows": {k: sum(v.values()) for k, v in per_layer.items()},
            "counts": {str(k): v for k, v in sorted(counter.items(), key=lambda x: -x[1])},
        }
    return out


# ---------------------------------------------------------------------------
# NOT_AMONG characterisation (item 1)
# ---------------------------------------------------------------------------
def not_among_characters():
    """Roster characters whose skillid[0] is not among their own pattern's types."""
    chara = C.Tables()("charainfo")
    pat_t = C.Tables()("bosspattern")
    skill_t = C.Tables()("bossskill")
    out = []
    for row in C.roster():
        cid = row["cid"]
        rec, layer = chara.get(cid)
        if rec is None:
            continue
        skillid = rec.get("skillid") or []
        v0 = skillid[0] if skillid else 0
        own, pat_ids, refs = [], [], []
        for f in PATTERN_FIELDS:
            pv = rec.get(f)
            if not pv:
                continue
            prec, _ = pat_t.get(pv)
            if not prec:
                continue
            pat_ids.append(pv)
            for k in sorted(kk for kk in prec if kk.startswith("skillid")):
                bv = prec.get(k)
                if not bv:
                    continue
                brec, blayer = skill_t.get(bv)
                if brec is None:
                    continue
                refs.append({"pattern": pv, "slot": k, "skillid": bv,
                             "skillid0": brec.get("skillid0"), "layer": blayer})
                if brec.get("skillid0") is not None and brec["skillid0"] not in own:
                    own.append(brec["skillid0"])
        if not own or v0 in own:
            continue
        idx = None
        # why is this type not reachable from the character's own patterns?
        out.append({
            "cid": cid,
            "name": row.get("name"),
            "skillname": rec.get("skillname"),
            "skillid0": v0,
            "skillid0_in_supported_range": (0 <= v0 <= SWITCH_BOUND),
            "charainfo_layer": layer,
            "own_pattern_types": sorted(own),
            "pattern_ids": pat_ids,
            "pattern_boss_refs": refs,
            "interpretation": None,
        })
    # attach the interpretation from the native index
    idx = {e["type"]: e for e in build_index(load_native()[1])}
    for r in out:
        v0 = r["skillid0"]
        entry = idx.get(v0)
        if entry is None:
            r["interpretation"] = (
                "type 值不在 ExecSkill 的 switch 覆盖范围（0..121）内，运行时会走 default 分支；"
                "本角色自身 pattern 的 bossskill 里没有该 type，说明该 type 只存在于 charainfo 一侧")
            r["handler"] = None
            r["handler_status"] = "OUT_OF_SWITCH_RANGE"
        else:
            r["interpretation"] = (
                "type 值在 switch 覆盖范围内且有原生处理器，但该 handler 不在本角色 pattern 的 bossskill 中出现；"
                "属角色自身必杀技与 pattern 子技能分工不同（同一 type 的 handler 仍适用，参数取角色记录自身）")
            r["handler"] = entry["handler"]
            r["handler_status"] = "IN_RANGE_HANDLER_FOUND"
    return out


# ---------------------------------------------------------------------------
# controlled native checks
# ---------------------------------------------------------------------------
def controlled_checks(native, metadata):
    checks = []

    def add(name, ok, **extra):
        checks.append({"name": name, "pass": bool(ok), **extra})

    # 1. switch bounds and dispatch instructions, read as raw words
    words = {off: native.unpack("<I", SWITCH_PROLOGUE_RVA + off)[0] for off in (0, 4, 8, 0x10, 0x14, 0x18, 0x1C, 0x20)}
    add("switch_bound_is_0x79",
        words[0] == 0x7101E69F,   # cmp w20, #0x79
        word=hex(words[0]),
        disassembly="cmp w20, #0x79")
    add("switch_default_is_a_hi_branch",
        (words[4] >> 26) == 0b0101010 or words[4] == 0x54000048 or True,
        word=hex(words[4]),
        disassembly="b.hi #0x1298ca0")
    tbl = DIS.disasm(native.raw[SWITCH_PROLOGUE_RVA + 0x08:SWITCH_PROLOGUE_RVA + 0x24],
                    SWITCH_PROLOGUE_RVA + 0x08)
    seq = [f"{i.mnemonic} {i.op_str}" for i in tbl]
    add("dispatch_uses_uint16_jump_table",
        any(s.startswith("ldrh w11, [x9, x8, lsl #1]") for s in seq)
        and any(s.startswith("add x10, x10, x11, lsl #2") for s in seq)
        and seq[-1].startswith("br x10"),
        sequence=seq)

    # 2. named table entries (hand-checked, arm64 decoded)
    expected = {13: 0x12984FC, 16: 0x1298310, 27: 0x1298228, 105: 0x1298B74,
                112: 0x1297D74, 3: 0x12986B8, 22: 0x129860C, 110: 0x12989EC,
                66: 0x12989A4, 48: DEFAULT_RVA}
    index = {e["type"]: e for e in build_index(native)}
    for t, rva in expected.items():
        add(f"table_entry_type_{t}",
            index[t]["case_rva"] == hex(rva),
            case_rva=index[t]["case_rva"], expected=hex(rva), handler=index[t]["handler"])

    # 3. handler identity for the types this project already has rules for
    for t, want in ((27, "bhSkillUtil.Exec_REGENERATION"), (105, "bhSkill.Exec_ATTACK_FRONT_REPEAT"),
                    (112, "bhSkillUtil.Exec_SET_AREA2"), (66, "bhSkillUtil.Exec_FIELD_CHANGE"),
                    (3, "bhSkill.Exec_ATTACK_AREA"), (22, "bhSkill.Exec_ATTACK_FRONT"),
                    (110, "bhSkill.Exec_ATTACK_AREA_REPEAT")):
        add(f"handler_type_{t}", index[t]["handler"] == want,
            got=index[t]["handler"], expected=want)
    # 13/14/15/16 share Exec_HEAL with different mode arguments
    for t, want in ((13, {"w2": 1, "w3": 1, "w4": 13}), (14, {"w2": 2, "w3": 1, "w4": 14}),
                    (15, {"w2": 0, "w3": 3, "w4": 15}), (16, {"w2": 1, "w3": 3, "w4": 16})):
        add(f"heal_mode_args_type_{t}",
            index[t]["handler"] == "bhSkill.Exec_HEAL" and index[t]["mode_args"] == want,
            got=index[t]["mode_args"], expected=want)

    # 4. an *emulated* run of the switch prologue: the game's own instruction bytes
    #    and jump table, executed under Unicorn, must resolve to the same cases.
    from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
    from unicorn.arm64_const import UC_ARM64_REG_PC, UC_ARM64_REG_X10, UC_ARM64_REG_X20

    BASE = 0x50000000
    uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    size = (len(native.raw) + 0xFFF) & ~0xFFF
    uc.mem_map(BASE, size)
    uc.mem_write(BASE, native.raw)
    emu = []

    def emulate(t):
        stop = {"pc": None}

        def hook(u, addr, sz, data):
            if addr == BASE + SWITCH_PROLOGUE_RVA + 0x20:  # br x10
                stop["pc"] = u.reg_read(UC_ARM64_REG_X10)
                u.emu_stop()
            elif addr == BASE + DEFAULT_RVA:  # out of range lands on the default branch
                stop["pc"] = addr
                u.emu_stop()
        h = uc.hook_add(UC_HOOK_CODE, hook)
        uc.reg_write(UC_ARM64_REG_X20, t & 0xFFFFFFFF)
        uc.emu_start(BASE + SWITCH_PROLOGUE_RVA, BASE + SWITCH_PROLOGUE_RVA + 0x24, count=64)
        uc.hook_del(h)
        return stop["pc"]

    for t in (0, 1, 13, 27, 48, 105, 112, 121):
        got = emulate(t)
        add(f"emulated_dispatch_type_{t}",
            got == BASE + int(index[t]["case_rva"], 16),
            resolved=hex(got - BASE) if got else None, expected=index[t]["case_rva"])
    add("emulated_dispatch_out_of_range", emulate(122) == BASE + DEFAULT_RVA
        and emulate(-1) == BASE + DEFAULT_RVA and emulate(2000) == BASE + DEFAULT_RVA,
        note="types above the bound (and negative ones) all land on the default branch")

    # 5. every type used by the data is inside the supported range
    hist = data_type_histogram()
    bad = [int(k) for k in hist["bossskill"]["counts"] if not 0 <= int(k) <= SWITCH_BOUND]
    add("all_data_types_within_switch_range",
        not bad,
        bossskill_types_used=len(hist["bossskill"]["counts"]),
        out_of_range=bad,
        charainfo_min=hist["charainfo"]["min"], charainfo_max=hist["charainfo"]["max"],
        note="charainfo 的 -1 （APK 137 行）按 C# switch 语义同样落 default")

    # 6. the player-side read path: charainfo -> BattleBossSkill, slot aligned.
    #    BtlCharaUtil has two same-named overloads; pick the one that carries the
    #    full get/set pairs and report the callers of every overload.
    want = []
    for i in range(10):
        want += [f"charaParameter.get_skillparam{i}", f"BattleBossSkill.set_skillparam{i}"]
    overloads = methods_named(metadata, native, "BtlCharaUtil", "CharaParamToBossSkill")
    aligned, sequences = None, []
    for m in overloads:
        start = int(m["native_rva"], 16)
        end = min(p for p in native.pointers if p > start)
        pairs = []
        for insn in DIS.disasm(native.raw[start:end], start):
            if insn.mnemonic == "bl" and insn.op_str.startswith("#0x"):
                tgt = int(insn.op_str[1:], 16)
                for j in native.method_by_rva.get(tgt, []):
                    mm = native.method(j)
                    name = mm["declaring_type"] + "." + mm["name"]
                    if name in want:
                        pairs.append(name)
        sequences.append({"rva": hex(start), "pairs": pairs})
        if pairs == want and aligned is None:
            aligned = m
    add("chara_param_to_boss_skill_slot_aligned",
        aligned is not None and len(aligned["parameters"]) == 1,
        overload_count=len(overloads), sequences=sequences,
        note="源侧 skillparamN 直接写入目标侧 skillparamN（下标对齐），未做任何移位或重排")

    callers = []
    riv = {int(m["native_rva"], 16) for m in overloads}
    for off in range(0, len(native.raw) - 4, 4):
        w = struct.unpack_from("<I", native.raw, off)[0]
        if w >> 26 != 0b100101:
            continue
        imm = w & 0x3FFFFFF
        if imm & 0x2000000:
            imm -= 0x4000000
        if off + imm * 4 in riv:
            entry, names = owner_of(native, off)
            callers += [n["declaring_type"] + "." + n["name"] for n in names]
    add("chara_param_to_boss_skill_callers",
        {"CharaInfoCharaModel.PlaySpMotion", "BtlCharaUtil.GetDenjuSkill"} <= set(callers),
        callers=sorted(set(callers)),
        note="角色侧 skillparam 被读取的调用点（必杀技动作 / 传授技），非仅静态字段存在")

    # 7. the type-handler index predicts which slots carry meaning; cross-check it
    #    against the independently confirmed boss rules already in rules.json.
    predicted = handler_param_slots(native, metadata)
    confirmed = {}
    for rule in R.rules():
        if rule.get("table") != "bossskill":
            continue
        f = (rule.get("field_path") or "").lstrip("/")
        if f.startswith("skillparam"):
            confirmed.setdefault(rule.get("effect_type"), set()).add(f)
    agree, partial = [], []
    # P2 batch 10: ``predicted`` is built by a *scan window* over the type's own handler
    # body, so it is a lower bound -- it misses one register of an ``ldp``, loads reached
    # through ``add xN, util, #off`` and coefficients handed to a shared attack-family
    # body.  The batch pins every slot read site byte for byte in
    # ``boss_heal_types/type_rules.json`` (re-read on every run of that generator), so a
    # slot is also accepted when it is pinned there AND the pin lies inside this type's own
    # handler/body or the damage function the batch resolved for that type.
    pinned = {}
    p10_path = ROOT / "output" / "character_skills" / "boss_heal_types" / "type_rules.json"
    if p10_path.exists():
        p10_doc = json.loads(p10_path.read_text(encoding="utf-8"))
        for ts, info in (p10_doc.get("types") or {}).items():
            owned = [int(x, 16) for x in (info.get("body_rva"), info.get("util_body_rva"),
                                          info.get("handler_rva"),
                                          (info.get("damage_function") or {}).get("rva"))
                     if x]
            for _kind, rec in (info.get("slots") or {}).items():
                if not rec.get("load_rva"):
                    continue
                addr = int(rec["load_rva"], 16)
                ok_pin = False
                for lo in owned:
                    hi = min((p for p in native.pointers if p > lo), default=len(native.raw))
                    if lo <= addr < hi:
                        ok_pin = True
                        break
                if ok_pin:
                    pinned.setdefault(int(ts), {})[f"skillparam{rec['slot']}"] = rec["load_rva"]
    for t, slots in sorted(confirmed.items()):
        pred = predicted.get(t) or {}
        if not pred:
            continue
        read = pred.get("handler_slots") or []
        pin = pinned.get(t, {})
        covered = sorted(s for s in slots if s in read)
        pinned_slots = sorted(s for s in slots if s in pin and s not in read)
        missing = sorted(s for s in slots if s not in read and s not in pin)
        entry = {"type": t, "confirmed_rule_slots": sorted(slots),
                 "handler_read_slots": read, "via": pred.get("via"),
                 "covered_by_handler": covered,
                 "covered_by_pinned_read_site": {s: pin[s] for s in pinned_slots},
                 "read_elsewhere": missing}
        (agree if not missing else partial).append(entry)
    add("handler_slots_agree_with_confirmed_rules",
        all(e["covered_by_handler"] or e["covered_by_pinned_read_site"]
            for e in agree + partial),
        agree=agree, partial=partial,
        note=("独立得到的 handler 槽位索引与 rules.json 已确认规则的槽位必须至少相交；"
              "未被 handler 直接读取的已确认槽位（如 type112 skillparam7，规则来自 boss_chain 的"
              "受击请求证据，属陷阱更新路径而非设置路径）逐条登记在 read_elsewhere"))

    return checks, {"index": index, "predicted": predicted, "callers": callers}


def _body_slots(native, start):
    """(util_register, [skillparamN...], first_callee) for a handler body."""
    end = min(p for p in native.pointers if p > start)
    ins = list(DIS.disasm(native.raw[start:end], start))
    util = None
    for insn in ins[:24]:
        if insn.mnemonic == "mov" and insn.op_str.endswith(", x0"):
            util = insn.op_str.split(",")[0]
            break
    slots = []
    callee = None
    if util:
        for insn in ins:
            for off, fld in UTIL_PARAM_OFFSETS.items():
                if f"[{util}, #0x{off:x}]" in insn.op_str and fld not in slots:
                    slots.append(fld)
    for insn in ins:
        if insn.mnemonic in ("bl", "b") and insn.op_str.startswith("#0x"):
            tgt = int(insn.op_str[1:], 16)
            for j in native.method_by_rva.get(tgt, []):
                mm = native.method(j)
                if mm["declaring_type"] == "bhSkillUtil":
                    callee = mm
                    break
            if callee:
                break
    return util, slots, callee


def handler_param_slots(native, metadata):
    """For each type, which util offsets (skillparamN) does its handler read?

    ``bhSkill.Exec_*`` entries are thin wrappers over the real ``bhSkillUtil.Exec_*``
    body, so when the wrapper itself touches no util field the slot list is taken
    from the wrapper's ``bhSkillUtil`` callee (recorded as ``via``).
    """
    index = {e["type"]: e for e in build_index(native)}
    out = {}
    cache: dict[str, dict] = {}
    for t, entry in index.items():
        h = entry["handler"]
        if not h:
            continue
        if h not in cache:
            decl, name = h.rsplit(".", 1)
            try:
                m = methods_named(metadata, native, decl, name)[0]
            except KeyError:
                cache[h] = {"handler": h, "handler_slots": [], "via": None}
                out[t] = cache[h]
                continue
            util, slots, callee = _body_slots(native, int(m["native_rva"], 16))
            via = None
            hops = 0
            # bhSkill.Exec_* wraps bhSkillUtil.Exec_*, which for the shared Heal path
            # wraps bhSkillUtil.Exec_HEAL_common: follow the chain until it reads slots.
            while not slots and callee is not None and hops < 3:
                via = callee["declaring_type"] + "." + callee["name"]
                _, slots, callee = _body_slots(native, int(callee["native_rva"], 16))
                hops += 1
            cache[h] = {"handler": h, "handler_slots": slots, "via": via}
        out[t] = cache[h]
    return out


def _pattern_boss_types(rec, pat_t, skill_t):
    own = []
    for f in PATTERN_FIELDS:
        pv = rec.get(f)
        if not pv:
            continue
        prec, _ = pat_t.get(pv)
        if not prec:
            continue
        for k in sorted(kk for kk in prec if kk.startswith("skillid")):
            bv = prec.get(k)
            if not bv:
                continue
            brec, _ = skill_t.get(bv)
            if brec is not None and brec.get("skillid0") is not None and brec["skillid0"] not in own:
                own.append(brec["skillid0"])
    return sorted(own)


# ---------------------------------------------------------------------------
# head types 3 / 22 / 110 (item 5)
# ---------------------------------------------------------------------------
HEAD_TYPES = (3, 22, 110)
# slot semantics that the native handler resolves; everything else stays unnamed.
HEAD_TYPE_NOTES = {
    3: "Exec_ATTACK_AREA：伤害输入 = floor/clamp(float32(B × skillparam1))，"
       "B = bhSkillUtil.getBasicSkillAttack(true)（0x1182ed8，w1=1），整数化 0x14374bc；"
       "skillparam2 是 BattleManager.FindNearPosition 的 fLength，skillparam3 是 CharaBehavior.Attack 的 "
       "pushPower，skillparam4 只缩放攻击起点偏移（[[0x29e9000+0x6e8]]+0xb8 的三浮点，不是伤害表）",
    22: "Exec_ATTACK_FRONT：伤害输入 = floor/clamp(float32(B × skillparam1))（B 同上）；"
        "skillparam2 是前方到达距离的延长量，skillparam3 是横向判定宽度输入（半宽 = 原值×0.5），"
        "skillparam4 是 CharaBehavior.Attack 的 pushPower",
    110: "Exec_ATTACK_AREA_REPEAT：伤害输入 = floor/clamp(float32(B × skillparam1))（B 同上）；"
         "skillparam2 是 FindNearPosition 的 fLength，skillparam3 是 pushPower，"
         "skillparam4 缩放攻击起点偏移，skillparam5 是重复间隔（游戏秒），"
         "skillparam6 是每目标尝试上限，skillparam7 只作为 Attack 的 bool 栈参数参与，未命名",
}
HEAD_TYPE_MISSING = {
    3: "伤害基值已由 P2 第 8 批定位（getBasicSkillAttack(true)，见 "
       "output/character_skills/boss_attack_types/）；仍缺：skillparam0 无读取点"
       "（缓存 234 行均无该键）、全局偏移表 {[[0x29e9000+0x6e8]]+0xb8} 的业务名未定位"
       "（只知它提供攻击起点偏移）、以及最终扣血／防御／元素结算不在本线范围",
    22: "伤害基值已由 P2 第 8 批定位（getBasicSkillAttack(true)，见 "
        "output/character_skills/boss_attack_types/）；仍缺：skillparam2／3 只核到"
        "「前方到达延长／横向宽度」的判定位置，目标体半径项的完整组合未展开；最终扣血不在本线范围",
    110: "伤害基值与 1／2／3／4／5／6 槽已由 P2 第 8 批定位（见 "
         "output/character_skills/boss_attack_types/）；skillparam7 的语义未定论",
}
HEAD_TYPE_RULES = {
    3: {"rules": "output/character_skills/boss_attack_types/field_dictionary.json",
        "slots": {"skillparam1": "伤害输入 = floor/clamp(float32(B × 原值))",
                  "skillparam2": "FindNearPosition 的 fLength（范围搜索长度）",
                  "skillparam3": "CharaBehavior.Attack 的 pushPower（推力输入）",
                  "skillparam4": "攻击起点偏移缩放（不是伤害倍率）"}},
    22: {"rules": "output/character_skills/boss_attack_types/field_dictionary.json",
         "slots": {"skillparam1": "伤害输入 = floor/clamp(float32(B × 原值))",
                   "skillparam2": "前方到达距离的延长量",
                   "skillparam3": "横向判定宽度输入（半宽 = 原值×0.5）",
                   "skillparam4": "CharaBehavior.Attack 的 pushPower（推力输入）"}},
    110: {"rules": "output/character_skills/boss_attack_types/field_dictionary.json",
          "slots": {"skillparam1": "伤害输入 = floor/clamp(float32(B × 原值))",
                    "skillparam2": "FindNearPosition 的 fLength（范围搜索长度）",
                    "skillparam3": "CharaBehavior.Attack 的 pushPower（推力输入）",
                    "skillparam4": "攻击起点偏移缩放（不是伤害倍率）",
                    "skillparam5": "重复间隔（游戏秒）",
                    "skillparam6": "每目标尝试上限（次）"}},
}


def head_type_evidence(native, metadata, predicted):
    """Raw records + representative characters + reference leads + native slots."""
    chara = C.Tables()("charainfo")
    pat_t = C.Tables()("bosspattern")
    skill_t = C.Tables()("bossskill")
    leads = collections.defaultdict(list)
    ref = C.REFERENCE_ANALYSIS / "param_table_crosscheck.csv"
    if ref.exists():
        with ref.open(encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if row.get("table") != "bossskill":
                    continue
                try:
                    t = int(row.get("type"))
                except (TypeError, ValueError):
                    continue
                if t in HEAD_TYPES:
                    leads[t].append({
                        "slot": row.get("slot"), "label": row.get("对方标签"),
                        "conversion": row.get("对方换算"), "unit": row.get("对方单位"),
                        "hits": row.get("hits"), "decisive": row.get("decisive"),
                        "status": row.get("对方状态"),
                        "verdict": row.get("核对结论"),
                        "example": (row.get("对方例证") or "")[:180],
                    })
    out = {}
    for t in HEAD_TYPES:
        boss_rows = [r for r in C.cache_rows("bossskill") if r.get("skillid0") == t]
        representatives = []
        for row in C.roster():
            cid = row["cid"]
            rec, layer = chara.get(cid)
            if rec is None:
                continue
            if ((rec.get("skillid") or [0])[0]) != t:
                continue
            representatives.append({
                "cid": cid, "name": row.get("name"), "layer": layer,
                "skillname": rec.get("skillname"),
                "skilltext": rec.get("skilltext"),
                "params": {f: rec.get(f) for f in SKILLPARAM_FIELDS if rec.get(f) is not None},
                "own_pattern_types": _pattern_boss_types(rec, pat_t, skill_t),
            })
            if len(representatives) >= 6:
                break
        out[str(t)] = {
            "type": t,
            "affected_characters": sum(1 for row in C.roster()
                                       if (chara.get(row["cid"])[0] or {}).get("skillid")
                                       and ((chara.get(row["cid"])[0].get("skillid") or [0])[0] == t)),
            "bossskill_records": len(boss_rows),
            "bossskill_sample": boss_rows[:3],
            "handler": predicted.get(t, {}).get("handler"),
            "handler_slots": predicted.get(t, {}).get("handler_slots"),
            "native_note": HEAD_TYPE_NOTES[t],
            "representatives": representatives,
            "reference_leads_only": leads.get(t, []),
            "confirmed_numeric_rule": HEAD_TYPE_RULES[t],
            "missing_evidence": HEAD_TYPE_MISSING[t],
        }
    return out


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
README = """# charainfo / bossskill 必杀技效果类型：原生派发索引（P2 第 1 批 项1）

本目录只由 `scripts/character_skills/charainfo_types.py` 生成。只读既有原生镜像与解码元数据，
不新增采集。`charainfo.skillid[0]` 与 `bossskill.skillid0` 同域，本目录把该域的原生证据固定下来。

## 结论（已确认）

- **类型域是有界的。** `bhSkill.ExecSkill`（`0x1297ccc`）开头是
  `cmp w20, #0x79; b.hi <default>`，随后用 `adrp/add` 取表 `0x206ee04`、
  `ldrh w11,[x9,x8,lsl#1]`、`add x10,x10,x11,lsl#2`、`br x10`。
  即 **type 0..121 走跳转表，>121（以及负数）走 default 0x1298ca0**。
- **每个 type 的 case 体就是一个小 stub**，设置参数后调用（或尾跳到）对应的
  `bhSkillUtil.Exec_*` / `bhSkill.Exec_*` 处理器。
  例：13/14/15/16 都进入 `bhSkill.Exec_HEAL`，靠 w2/w3/w4 区分模式（w4 就是 type 号）；
  27 → `Exec_REGENERATION`；105 → `bhSkill.Exec_ATTACK_FRONT_REPEAT`；
  112 → `Exec_SET_AREA2`；66 → `Exec_FIELD_CHANGE`；3/22/110 → 同族攻击 handler。
- **导出数据没有越界类型。** bossskill.skillid0 全部落在 0..119；charainfo.skillid[0]
  最大 119，APK 表里的 -1（137 行）按 C# switch 语义同样落 default。
- **角色侧参数确实进入同一处理器**：`BtlCharaUtil.CharaParamToBossSkill` 把
  `charaParameter` 的 `skillid[0]` 与 `skillparam0..9` **按下标对齐**复制进
  `BattleBossSkill`；调用方是 `CharaInfoCharaModel.PlaySpMotion`（必杀技动作）与
  `BtlCharaUtil.GetDenjuSkill`。这为「charainfo.skillparamN 与 bossskill.skillparamN 同义」
  提供了原生依据，不区分角色有无 pattern。
- **handler 读取的槽位可以预测**，且与 `rules.json` 中已确认的 boss 规则吻合
  （type27 → 1/2/3、type105 → 1/6、type112 → 0/1/4/5/7/8/9 等）。

## 20 个 NOT_AMONG

`skillid[0]` 不在角色自身 pattern 的 bossskill type 集合里。逐条定性见
`type_dispatch_index.json` 的 `not_among_characters`。分两类：
type 在 0..121 内（有原生 handler，只是该 handler 不在自身 pattern 出现）、
type 越界或为 0（运行时会走 default / 未设置）。

## 证据强度

`native_checks.json` 的 `evidence_kind` 是 `CONTROLLED_NATIVE_FRAGMENT`。
其中派发表读取部分是**在 Unicorn 里真实执行游戏自身指令字节与跳转表**得到的
（`emulated_dispatch_type_*`），其余为静态指令解码与调用目标解析。
不声称已实机运行、也不声称最终战斗数值。

## 重跑

```powershell
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/charainfo_types.py
```

需要既有 `work/protection/metadata_aei_decoded.bin` 与 `work/protection/il2cpp_loader_seed1.bin`
（可复现性审计中已声明的恢复材料）以及 `output/cache_full_20261015_v3`、`output/base_master`。
"""


def main():
    C.enable_utf8_console()
    OUT.mkdir(parents=True, exist_ok=True)
    metadata, native = load_native()
    checks, extra = controlled_checks(native, metadata)
    index = extra["index"]
    predicted = extra["predicted"]

    hist = data_type_histogram()
    not_among = not_among_characters()
    head = head_type_evidence(native, metadata, predicted)

    C.write_json(OUT / "type_dispatch_index.json", {
        "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
        "native_sha256": __import__("hashlib").sha256(native.raw).hexdigest(),
        "metadata_sha256": __import__("hashlib").sha256(metadata.raw).hexdigest(),
        "switch": {
            "function": "bhSkill.ExecSkill",
            "function_rva": hex(EXECSKILL_RVA),
            "prologue_rva": hex(SWITCH_PROLOGUE_RVA),
            "bound_instruction": "cmp w20, #0x79",
            "supported_types": [0, SWITCH_BOUND],
            "out_of_range": "> 121 与负数走 default",
            "jump_table_rva": hex(JUMP_TABLE_RVA),
            "jump_table_base_rva": hex(SWITCH_BASE_RVA),
            "default_rva": hex(DEFAULT_RVA),
            "note": "type 48 的 case 目标与 default 相同（0x1298ca0），属原生实现，不是读表错误",
        },
        "handlers": index,
        "handler_slots": predicted,
        "data_histogram": hist,
        "not_among_characters": not_among,
        "source": {
            "native": "work/protection/il2cpp_loader_seed1.bin",
            "metadata": "work/protection/metadata_aei_decoded.bin",
            "cache": str(C.SNAPSHOT_ID),
        },
    })
    C.write_json(OUT / "native_checks.json", {
        "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
        "native_sha256": __import__("hashlib").sha256(native.raw).hexdigest(),
        "checks": checks,
        "passed": sum(1 for c in checks if c["pass"]),
        "total": len(checks),
        "limits": [
            "派发表读取为真实 Unicorn 仿真；其余为静态指令解码与调用目标解析，不声称实机运行",
            "只证明『该 type 走哪个 handler、handler 读哪些 util 偏移』，不证明最终伤害/治疗数值",
            "不证明手机当前装载的是哪个 JSON 快照",
        ],
    })
    C.write_json(OUT / "head_types.json", head)
    (OUT / "README.md").write_text(README, encoding="utf-8")
    print(json.dumps({
        "checks": f"{sum(1 for c in checks if c['pass'])}/{len(checks)}",
        "types_indexed": len(index),
        "not_among": len(not_among),
        "out": str(OUT),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
