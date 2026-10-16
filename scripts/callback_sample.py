"""Evaluate only the actual straight-line callback assignment block, offline.

This is a bounded instruction model, not Android/native execution or a decoder.
The flag and module bias are controlled experiment inputs, not runtime evidence.
"""
import hashlib
import io
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_REG, ARM64_OP_MEM, ARM64_CC_EQ
from elftools.elf.elffile import ELFFile

SOURCE = Path("work/apk/lib/arm64-v8a/libcompatible.so")
START, END = 0x91a2c, 0x91acc  # complete straight-line block ending in RET
FLAG, CELL = 0x1a46a0, 0x1a61e0


def evaluate(instructions, relocations, flag, bias):
    registers, memory, stores = {}, {}, []
    for row in relocations:
        if row["type"] == 1027:
            memory[bias + row["slot"]] = bias + row["addend"]
    memory[bias + FLAG] = flag
    equal = None

    def regname(reg):
        return instructions[0].reg_name(reg)

    def read_reg(reg):
        name = regname(reg)
        return registers["x" + name[1:]] & (0xffffffff if name[0] == "w" else 0xffffffffffffffff)

    def value(op):
        if op.type == ARM64_OP_IMM:
            return op.imm
        if op.type == ARM64_OP_REG:
            return read_reg(op.reg)
        raise ValueError("Unsupported operand")

    def write(reg, val):
        name = regname(reg)
        registers["x" + name[1:]] = val & (0xffffffff if name[0] == "w" else 0xffffffffffffffff)

    def address(op):
        if op.type != ARM64_OP_MEM or op.mem.index:
            raise ValueError("Unsupported memory addressing")
        return read_reg(op.mem.base) + op.mem.disp

    for inst in instructions:
        ops, mnemonic = inst.operands, inst.mnemonic
        if mnemonic == "adrp":
            write(ops[0].reg, bias + ops[1].imm)
        elif mnemonic == "mov":
            write(ops[0].reg, value(ops[1]))
        elif mnemonic == "add":
            if any(op.shift.value for op in ops):
                raise ValueError("Unsupported shifted ADD")
            write(ops[0].reg, value(ops[1]) + value(ops[2]))
        elif mnemonic in ("ldr", "ldrb"):
            val = memory[address(ops[1])]
            write(ops[0].reg, val & 255 if mnemonic == "ldrb" else val)
        elif mnemonic == "cmp":
            equal = value(ops[0]) == value(ops[1])
        elif mnemonic == "csel":
            if inst.cc != ARM64_CC_EQ or equal is None:
                raise ValueError("Unsupported/uninitialized condition")
            write(ops[0].reg, value(ops[1] if equal else ops[2]))
        elif mnemonic == "str":
            addr, val = address(ops[1]), value(ops[0])
            memory[addr] = val
            stores.append({"instruction_rva": hex(inst.address), "cell_rva": hex(addr-bias),
                           "value": hex(val)})
        elif mnemonic == "ret":
            if inst.address != END - 4:
                raise ValueError("Unexpected RET")
        else:
            raise ValueError(f"Unsupported instruction {mnemonic}")
    target = memory[bias + CELL]
    return {"controlled_flag": flag, "controlled_load_bias": hex(bias), "stores": stores,
            "callback_value": hex(target), "callback_rva_if_in_module": hex(target-bias) if target >= bias else None}


def main():
    raw = SOURCE.read_bytes()
    elf = ELFFile(io.BytesIO(raw))
    segment = next(s for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"
                   and s["p_vaddr"] <= START < END <= s["p_vaddr"] + s["p_filesz"])
    offset = segment["p_offset"] + START - segment["p_vaddr"]
    code = raw[offset:offset + END-START]
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    instructions = list(md.disasm(code, START))
    assert sum(i.size for i in instructions) == len(code) and instructions[-1].mnemonic == "ret"
    relocations = json.loads(Path("output/protection/relocations.json").read_text())["all_relocations"]
    # Reject relocation evidence from a different binary before modeling it.
    for slot, target in [(0x19c4f8, FLAG), (0x19c6e0, CELL), (0x19c6c8, 0x165764)]:
        row = next(r for r in relocations if r["slot"] == slot)
        assert row["type"] == 1027 and row["addend"] == target
        assert tuple(int.from_bytes(raw[row["relocation_file_offset"]+i:row["relocation_file_offset"]+i+8], "little")
                     for i in (0, 8, 16)) == (slot, 1027, target)
    experiments = [evaluate(instructions, relocations, flag, bias)
                   for bias in (0, 0x10000000) for flag in (0, 1)]
    for row in experiments:
        bias = int(row["controlled_load_bias"], 0)
        expected = 0x4580 if row["controlled_flag"] == 0 else bias + 0x165764
        assert int(row["callback_value"], 0) == expected
        assert any(s["instruction_rva"] == "0x91abc" and s["cell_rva"] == hex(CELL) for s in row["stores"])
    result = {"status": "PASS_OFFLINE_BLOCK_MODEL", "source": str(SOURCE),
              "sha256": hashlib.sha256(raw).hexdigest(), "block_file_offset": offset,
              "block_rva": hex(START), "block_bytes": len(code), "instruction_count": len(instructions),
              "disassembly": [f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in instructions],
              "experiments": experiments,
              "limits": ["Flag value, module load bias and block invocation in the game remain UNKNOWN",
                         "No protected instructions, native callbacks or Android code executed",
                         "No data5 or chronicle.dat conversion rule established"]}
    out = Path("output/protection/callback_sample.json")
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "block_bytes", "instruction_count", "experiments")}, indent=2))


if __name__ == "__main__":
    main()
