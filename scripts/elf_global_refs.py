"""Find bounded AArch64 ADRP memory/address references, not exhaustive xrefs."""
import argparse
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--slot", type=lambda x: int(x, 0), required=True)
    parser.add_argument("--window", type=int, default=64,
                        help="maximum ADRP-to-use distance in bytes; multiple of four")
    parser.add_argument("--output", type=Path, default=Path("output/protection/global_refs.json"))
    args = parser.parse_args()
    if args.window < 4 or args.window % 4:
        parser.error("--window must be a positive multiple of four")
    raw = args.source.read_bytes()
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    refs = []
    with args.source.open("rb") as stream:
        elf = ELFFile(stream)
        if elf.header.e_machine != "EM_AARCH64":
            raise ValueError("Expected AArch64")
        for segment in elf.iter_segments():
            if segment["p_type"] != "PT_LOAD" or not segment["p_flags"] & 1:
                continue
            data = raw[segment["p_offset"]:segment["p_offset"]+segment["p_filesz"]]
            base = segment["p_vaddr"]
            for pos in range(0, len(data)-4, 4):
                adrp = struct.unpack_from("<I", data, pos)[0]
                if adrp & 0x9f000000 != 0x90000000:
                    continue
                reg = adrp & 31
                imm = ((adrp >> 5 & 0x7ffff) << 2) | (adrp >> 29 & 3)
                if imm & 0x100000:
                    imm -= 0x200000
                page = ((base+pos) & ~0xfff) + (imm << 12)
                for step in range(4, min(args.window, len(data)-pos-4)+1, 4):
                    intermediates = list(md.disasm(data[pos+4:pos+step], base+pos+4))
                    if sum(i.size for i in intermediates) != step-4:
                        continue
                    if any(i.mnemonic in ("b", "bl", "br", "blr", "ret", "cbz", "cbnz", "tbz", "tbnz")
                           or i.mnemonic.startswith("b.") for i in intermediates):
                        break
                    if any(md.reg_name(written) in (f"x{reg}", f"w{reg}")
                           for inst in intermediates for written in inst.regs_access()[1]):
                        break
                    ldr = struct.unpack_from("<I", data, pos+step)[0]
                    if (ldr >> 5 & 31) != reg:
                        continue
                    if ldr & 0x3b000000 == 0x39000000 and not ldr & 0x04000000:
                        # Integer unsigned-immediate LDR/STR, including byte flags.
                        scale, operation = ldr >> 30, ldr >> 22 & 3
                        if operation not in (0, 1):
                            continue
                        target = page + ((ldr >> 10 & 0xfff) << scale)
                        access = "LDR_GOT" if operation == 1 and scale == 3 else (
                            "LOAD_FROM_ADDRESS" if operation == 1 else "STR_TO_ADDRESS")
                    elif ldr & 0xff800000 == 0x91000000:
                        target = page + ((ldr >> 10 & 0xfff) << (12 if ldr & 0x400000 else 0))
                        access = "ADD_ADDRESS"
                    else:
                        continue
                    if target != args.slot:
                        continue
                    begin, end = max(0, pos-32), min(len(data), pos+step+48)
                    context = [f"0x{i.address:x}: {i.mnemonic} {i.op_str}" for i in md.disasm(data[begin:end], base+begin)]
                    refs.append({"adrp_address": base+pos, "ldr_address": base+pos+step,
                                 "slot": target, "access": access, "context": context,
                                 "window_bytes": args.window,
                                 "status": "STATIC_REFERENCE; register flow/branch context still requires review"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(refs, indent=2), encoding="utf-8")
    print(json.dumps(refs, indent=2))


if __name__ == "__main__":
    main()
