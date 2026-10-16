"""List ELF symbols and disassemble selected functions using current APK evidence."""
import argparse
import json
import re
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--match", default="Master|master|decrypt|Decrypt|Chronicle|Skill|skill|CSTM")
    parser.add_argument("--output", type=Path, default=Path("output/native"))
    parser.add_argument("--disassemble", action="store_true")
    parser.add_argument("--address", action="append", type=lambda x: int(x, 0), default=[])
    parser.add_argument("--size", type=int, default=256, help="bounded byte window; not a confirmed function size")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with args.source.open("rb") as stream:
        elf = ELFFile(stream)
        symbols = {}
        for section in elf.iter_sections():
            if section.header.sh_type not in ("SHT_SYMTAB", "SHT_DYNSYM"):
                continue
            for symbol in section.iter_symbols():
                if symbol.name and re.search(args.match, symbol.name):
                    symbols[(symbol.name, symbol["st_value"])] = {
                        "name": symbol.name, "address": symbol["st_value"],
                        "size": symbol["st_size"], "type": symbol["st_info"]["type"],
                        "section": str(symbol["st_shndx"])}
        rows = sorted(symbols.values(), key=lambda r: (r["address"], r["name"]))
        rows.extend({"name": f"manual_window_{address:x}", "address": address, "size": args.size,
                     "type": "STT_FUNC", "section": "UNKNOWN", "boundary_status": "UNKNOWN"}
                    for address in args.address)
        (args.output / "symbols.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        if args.disassemble:
            if elf.header.e_machine != "EM_AARCH64":
                raise ValueError("This disassembler is limited to AArch64 inputs")
            md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
            with (args.output / "disassembly.txt").open("w", encoding="utf-8") as out:
                for row in rows:
                    if row["type"] != "STT_FUNC" or not row["size"]:
                        continue
                    for seg in elf.iter_segments():
                        start = seg["p_vaddr"]
                        if seg["p_type"] == "PT_LOAD" and start <= row["address"] < start + seg["p_filesz"]:
                            stream.seek(seg["p_offset"] + row["address"] - start)
                            code = stream.read(row["size"])
                            out.write(f"\n{row['name']} @ 0x{row['address']:x} size {row['size']}\n")
                            for inst in md.disasm(code, row["address"]):
                                out.write(f"{inst.address:08x}: {inst.mnemonic:8s} {inst.op_str}\n")
                            break
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
