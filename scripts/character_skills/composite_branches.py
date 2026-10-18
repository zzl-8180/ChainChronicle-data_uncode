"""Trace the composite skilllist branches (types 67 / 80 / 96 / 1036) end to end.

P2 batch 5. The four types above do not fall on a single-slot branch like type 8: their
branch bodies read several parameters and call helpers (party counting, mana class
judgement) before feeding an accumulator -- or, in some cases, never reach the shared
accumulate op at all. This script prints every such branch body line by line with the
``bl`` targets resolved to ``Type.Method`` names, so the conversion chain can be read
and cited by address.

Read-only: it loads the recovered native image plus the decoded metadata and prints.
Nothing under ``output/`` is written by the exploration mode; ``--write`` emits the
evidence file ``composite_branches.json``.

    .venv\\Scripts\\python.exe -B scripts/character_skills/composite_branches.py
    .venv\\Scripts\\python.exe -B scripts/character_skills/composite_branches.py --type 67 --kind attack
    .venv\\Scripts\\python.exe -B scripts/character_skills/composite_branches.py --write
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT / "scripts", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import common as C  # noqa: E402
import skilllist_types as S  # noqa: E402

OUT = ROOT / "output" / "character_skills" / "skilllist_types"
COMPOSITE_TYPES = (67, 80, 96, 1036)
WINDOW = 0x400


def name_for_rva(md, native, rva):
    """``Type.Method`` for a call target, plus the sig when the metadata has it."""
    entry = rva
    idx = native.method_by_rva.get(entry)
    if not idx:
        # a thunk (e.g. a shared `b`) -- look through a single unconditional branch
        insn = S.first_insn(native, rva)
        if insn is not None and insn.mnemonic == "b" and insn.op_str.startswith("#"):
            entry2 = int(insn.op_str[1:], 0)
            idx = native.method_by_rva.get(entry2)
            if idx:
                entry = entry2
    if not idx:
        return None, None, entry
    meth = md.method(idx[0])
    sig = f"{meth['name']}({', '.join(p['name'] for p in meth['parameters'])})"
    return meth["declaring_type"] + "." + sig, meth, entry


def body(native, leaf, window=WINDOW):
    """The branch body: from ``leaf`` to the first unconditional control transfer.

    The declared ``exit`` from the dispatch map is not a safe linear bound -- for some
    entries it lies *before* the leaf (the shared tail is earlier in the image), and
    disassembling across it would print neighbouring branches as if they belonged to
    this one. A branch body here always ends with its own terminal ``b`` (to the path's
    loop tail) or a ``ret``/``br``, so walking to that point is the correct bound.
    """
    out = []
    for insn in S.DIS.disasm(native.raw[leaf:leaf + window], leaf):
        out.append(insn)
        m = insn.mnemonic
        if m in ("ret", "br", "brk") or m == "b" or m == "bx":
            break
    return out


def trace(native, md, kind, ability_type, leaf, exit_rva):
    rows = []
    for insn in body(native, leaf, exit_rva):
        row = {"rva": hex(insn.address), "text": f"{insn.mnemonic}\t{insn.op_str}"}
        if insn.mnemonic in ("bl", "b") and insn.op_str.startswith("#"):
            target = int(insn.op_str[1:], 0)
            nm, meth, entry = name_for_rva(md, native, target)
            row["call_target"] = hex(target)
            if nm:
                row["call_name"] = nm
                row["thunk_via"] = hex(entry) if entry != target else None
                if meth:
                    row["call_metadata"] = {"declaring_type": meth["declaring_type"],
                                            "name": meth["name"],
                                            "params": [p["name"] for p in meth["parameters"]]}
        if insn.mnemonic.startswith("b.") and insn.op_str.startswith("#"):
            row["branch_target"] = hex(int(insn.op_str[1:], 0))
        rows.append(row)
    return rows


def reachable(native, leaf, lo, hi, stop=(), max_nodes=1200):
    """CFG walk from ``leaf`` inside [lo, hi): follow every branch, stop at calls.

    The branches of 67/80/96 on one path are *merged* by the compiler: they jump into
    shared labels inside one worker region, so a linear listing of one leaf cannot show
    its real chain. This walk returns the reachable instructions in address order plus
    the set of call sites and the terminal instruction, which is what the conversion
    chain has to be read from.
    """
    todo = [leaf]
    seen = {}
    calls = []
    terminals = []
    stop = set(stop)
    while todo:
        addr = todo.pop()
        if addr in seen or not (lo <= addr < hi) or len(seen) > max_nodes:
            continue
        if addr in stop:
            seen[addr] = next(iter(S.DIS.disasm(native.raw[addr:addr + 4], addr)), None)
            terminals.append(seen[addr])
            continue
        insn = next(iter(S.DIS.disasm(native.raw[addr:addr + 4], addr)), None)
        if insn is None:
            continue
        seen[addr] = insn
        m = insn.mnemonic
        op = insn.op_str
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
        if m.startswith("b.") or m == "cbz" or m == "cbnz" or m == "tbz" or m == "tbnz":
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


def collect(native, md, maps):
    ev = {}
    for kind in ("attack", "defence", "move", "crit_rate", "crit_dmg"):
        per = maps[kind]
        for t in COMPOSITE_TYPES:
            e = per.get(t)
            if not e or e.get("leaf") in (None, "None") or e.get("neutral"):
                continue
            key = f"{kind}/{t}"
            leaf = int(e["leaf"], 16)
            seen, calls, terms = reachable(
                native, leaf, S.FUNCS[kind]["head"], S.FUNCS[kind]["entry"] + 0x8000,
                stop=(S.NEUTRAL[kind], S.TAIL_MUL[kind]))
            rows = sorted(({"rva": hex(a), "text": f"{i.mnemonic}	{i.op_str}"}
                           for a, i in seen.items()), key=lambda r: int(r["rva"], 16))
            calls = [{"rva": hex(i.address), "target": hex(int(i.op_str[1:], 0)),
                      "name": name_for_rva(md, native, int(i.op_str[1:], 0))[0]}
                     for i in calls if i.op_str.startswith("#")]
            terms = [{"rva": hex(i.address), "text": f"{i.mnemonic}	{i.op_str}"} for i in terms]
            term = terms[0] if terms else None
            calls = [r for r in rows if r.get("call_name")]
            ev[key] = {
                "kind": kind, "type": t, "leaf": e["leaf"], "exit": e["exit"],
                "gate_rva": e.get("gate_rva"), "slots": e["slots"],
                "slot_calls": e["slot_calls"],
                "reaches_accumulate_op": e["reaches_accumulate_op"],
                "body_terminal": term and {"rva": term["rva"], "text": term["text"],
                                           "target": term.get("call_target") or term.get("branch_target")},
                "declared_exit": e["exit"],
                "accumulate_op": S.ACCUM_OP[kind],
                "calls": calls,
                "terminals": terms,
                "reachable_count": len(rows),
                "body": rows,
            }
    return ev


def main():
    C.enable_utf8_console()
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", type=int, default=None)
    ap.add_argument("--kind", default=None)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--calls-only", action="store_true")
    ap.add_argument("--max-rows", type=int, default=200)
    ap.add_argument("--brief", action="store_true",
                    help="only the rows that carry meaning: calls, compares, float math, branches")
    args = ap.parse_args()

    md, native = S.load_native()
    resolver = S.Resolver(native)
    maps = S.build_maps(native, resolver)
    ev = collect(native, md, maps)

    if args.write:
        payload = {
            "generated_by": "scripts/character_skills/composite_branches.py",
            "native_sha256": C.sha256_file(S.NATIVE) if hasattr(S, "NATIVE") else None,
            "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
            "note": ("每个复合分支的完整分支体（leaf→exit）逐指令列出，bl 目标按元数据解析为 "
                     "Type.Method；用于引用换算链各段的 RVA。窗口上限 0x400 字节。"),
            "branches": ev,
        }
        C.write_json(OUT / "composite_branches.json", payload)
        print(json.dumps({"wrote": str(OUT / "composite_branches.json"),
                          "branches": sorted(ev)}, ensure_ascii=False))
        return 0

    for key in sorted(ev):
        kind, t = key.split("/")
        if args.type is not None and int(t) != args.type:
            continue
        if args.kind and kind != args.kind:
            continue
        b = ev[key]
        print(f"\n===== {key}  leaf={b['leaf']} exit={b['exit']} gate={b['gate_rva']} "
              f"slots={b['slots']} reaches_accum={b['reaches_accumulate_op']} ({b['accumulate_op']})")
        for c in b["calls"]:
            print(f"   call {c['rva']} -> {c['target']} {c['name']}")
        if not args.calls_only:
            print("   " + "-" * 66)
            show = b["body"]
            if args.brief:
                keys = ("bl	", "cmp	", "cmp ", "fcmp", "fmul", "fadd", "fdiv", "fmov",
                        "scvtf", "fcvtzs", "csel", "ccmp", "tbnz", "tbz", "cbnz", "cbz",
                        "b.lt", "b.eq", "b.ne", "b.gt", "b.le", "b.ge", "cset", "and	")
                show = [r for r in b["body"] if any(k in r["text"] for k in keys)]
            for r in show[: args.max_rows]:
                extra = ""
                if r.get("call_name"):
                    extra = f"   ; {r['call_name']}"
                elif r.get("branch_target"):
                    extra = f"   ; -> {r['branch_target']}"
                print(f"   {r['rva']}  {r['text']}{extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
