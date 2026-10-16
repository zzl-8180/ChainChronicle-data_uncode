"""Find immediate AArch64 B/BL encodings; candidates require context review."""
import argparse
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--target", required=True, action="append", type=lambda s: int(s, 0))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw, hits = args.source.read_bytes(), []
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    with args.source.open("rb") as stream:
        elf = ELFFile(stream)
        if elf.header.e_machine != "EM_AARCH64":
            raise ValueError("Expected AArch64")
        for segment in elf.iter_segments():
            if segment["p_type"] != "PT_LOAD" or not segment["p_flags"] & 1:
                continue
            data = raw[segment["p_offset"]:segment["p_offset"]+segment["p_filesz"]]
            base = segment["p_vaddr"]
            for pos in range(0, len(data)-3, 4):
                word = struct.unpack_from("<I", data, pos)[0]
                if word & 0x7c000000 != 0x14000000:
                    continue
                imm = word & 0x3ffffff
                if imm & 0x2000000:
                    imm -= 0x4000000
                target = base + pos + imm * 4
                if target not in args.target:
                    continue
                begin = max(0, pos-80)
                hits.append({"site": hex(base+pos), "target": hex(target),
                             "kind": "BL" if word & 0x80000000 else "B",
                             "context": [f"{hex(i.address)}: {i.mnemonic} {i.op_str}"
                                         for i in md.disasm(data[begin:pos+16], base+begin)]})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"source": str(args.source), "targets": [hex(t) for t in args.target],
                                      "hits": hits, "scope": "Aligned immediate B/BL encodings in file-backed executable PT_LOAD; not a complete CFG"}, indent=2), encoding="utf-8")
    print(json.dumps({"hits": len(hits), "sites": [r["site"] for r in hits]}))


if __name__ == "__main__":
    main()
