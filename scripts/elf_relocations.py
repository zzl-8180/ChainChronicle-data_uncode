"""Resolve AArch64 ELF dynamic relocations even when section names are removed."""
import argparse
import json
import struct
from pathlib import Path
from project_layout_paths import read_path, write_path, path_reference
from versioned_outputs import fresh_output, require_new_files, write_new_text

from elftools.elf.elffile import ELFFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--slot", action="append", type=lambda x: int(x, 0), default=[])
    parser.add_argument("--output", type=Path, help="Path to a new report file")
    args = parser.parse_args()
    args.source = read_path(args.source)
    output = write_path(args.output) if args.output else (
        fresh_output("projects/unpack/reports/phase_c", "relocations") / "relocations.json"
    )
    require_new_files(output)
    raw = args.source.read_bytes()
    with args.source.open("rb") as stream:
        elf = ELFFile(stream)
        if elf.header.e_machine != "EM_AARCH64":
            raise ValueError("Only AArch64 relocation types are interpreted here")
        loads = [s for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"]
        dynamic = next(s for s in elf.iter_segments() if s["p_type"] == "PT_DYNAMIC")
        tags = {tag.entry.d_tag: tag.entry.d_val for tag in dynamic.iter_tags()}
        syms = next(s for s in elf.iter_sections() if s["sh_type"] == "SHT_DYNSYM")

        def offset(address):
            for segment in loads:
                if segment["p_vaddr"] <= address < segment["p_vaddr"] + segment["p_filesz"]:
                    return segment["p_offset"] + address - segment["p_vaddr"]
            return None

        def word(address):
            pos = offset(address)
            return struct.unpack_from("<Q", raw, pos)[0] if pos is not None else None

        relocs = []
        for addr_tag, size_tag in [("DT_RELA", "DT_RELASZ"), ("DT_JMPREL", "DT_PLTRELSZ")]:
            if addr_tag not in tags:
                continue
            start = offset(tags[addr_tag])
            if start is None:
                raise ValueError("Relocation address is not mapped to file")
            for pos in range(start, start + tags[size_tag], 24):
                address, info, addend = struct.unpack_from("<QQq", raw, pos)
                sym_index, reloc_type = info >> 32, info & 0xffffffff
                name = syms.get_symbol(sym_index).name if sym_index else None
                relocs.append({"slot": address, "type": reloc_type, "symbol": name, "addend": addend,
                               "relocation_file_offset": pos, "unrelocated_slot_value": word(address)})
        by_slot = {r["slot"]: r for r in relocs}
        results = []
        for slot in args.slot:
            row = {"slot": slot, "slot_hex": hex(slot), "relocation": by_slot.get(slot)}
            reloc = by_slot.get(slot)
            if reloc and reloc["type"] == 1027:  # R_AARCH64_RELATIVE: module base + addend
                target = reloc["addend"]
                row.update(relative_target=target, relative_target_hex=hex(target),
                           target_unrelocated_file_value=word(target))
            results.append(row)
        write_new_text(output, json.dumps({"source": path_reference(args.source), "selected_slots": results,
                                           "all_relocations": relocs}, indent=2))
        print(json.dumps({"relocation_count": len(relocs), "selected_slots": results}, indent=2))


if __name__ == "__main__":
    main()
