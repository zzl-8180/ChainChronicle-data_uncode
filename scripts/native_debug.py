"""Recover retained symbol/DWARF records in this specific APK's NUtils library.

The section header table has been reduced to four entries. These byte ranges
were located from intact DWARF v4 CU chains and the retained section-name table.
This reads debugging records; it does NOT restore protected executable code.
"""
import argparse
import hashlib
import inspect
import io
import json
import re
import struct
from pathlib import Path

from elftools.dwarf.dwarfinfo import DWARFInfo, DebugSectionDescriptor, DwarfConfig
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM


def normalize(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", "backslashreplace")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/native"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    raw = args.source.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    baseline = json.loads(Path("output/apk/baseline.json").read_text(encoding="utf-8"))
    expected = next(x["sha256"] for x in baseline["extracted"] if x["apk_entry"].endswith("libChronicleNUtils.so"))
    if sha != expected or sha != "adc5f1d91343b0885ff07357c0cad2a66310cd52cc6ed47659fb24e4732a92bb":
        raise ValueError("Input does not match baseline library; recover section ranges again for a new build")
    elf = ELFFile(io.BytesIO(raw))
    shstr = elf.get_section_by_name(".shstrtab")
    # Retained .strtab immediately follows .shstrtab; valid symbol entries end at .shstrtab.
    string_start = shstr["sh_offset"] + shstr["sh_size"]
    strings = raw[string_start:elf.header.e_shoff]
    symbols = []
    for pos in range(shstr["sh_offset"] - 24, 320368, -24):
        name, info, other, section, address, size = struct.unpack_from("<IBBHQQ", raw, pos)
        if name >= len(strings) or info & 15 > 6 or section not in [*range(35), 65521, 65522]:
            break
        symbols.append({"name": strings[name:].split(b"\0", 1)[0].decode("utf-8", "backslashreplace"),
                        "info": info, "section": section, "address": address,
                        "size": size, "sym_offset": pos})
    (args.output / "recovered_symbols.json").write_text(json.dumps(symbols, indent=2), encoding="utf-8")
    # .debug_str upper bound is a reading window, not a claimed original section size.
    ranges = {"debug_abbrev_sec": (864944, 883593), "debug_info_sec": (883593, 1297392),
              "debug_str_sec": (1443888, 1806240)}
    kwargs = {k: None for k in inspect.signature(DWARFInfo).parameters if k != "config"}
    for name, (start, end) in ranges.items():
        kwargs[name] = DebugSectionDescriptor(io.BytesIO(raw[start:end]), name, start, end-start, 0)
    dwarf = DWARFInfo(config=DwarfConfig(True, "AArch64", 8), **kwargs)
    units, records, selected, calls, layouts = [], [], [], [], []
    for cu in dwarf.iter_CUs():
        top = cu.get_top_DIE()
        units.append({"offset": cu.cu_offset, "size": cu.size,
                      "name": normalize(top.attributes.get("DW_AT_name").value)})
        for die in cu.iter_DIEs():
            attrs = {k: {"form": v.form, "value": normalize(v.value)} for k, v in die.attributes.items()}
            row = {"die_offset": die.offset, "file_offset": ranges["debug_info_sec"][0] + die.offset,
                   "cu_offset": cu.cu_offset, "tag": die.tag, "attributes": attrs}
            records.append(row)
            name = attrs.get("DW_AT_name", {}).get("value", "")
            if die.tag in ("DW_TAG_structure_type", "DW_TAG_class_type") and name in ("binDataFormatHeader", "FileHashTable", "EnesetListNative"):
                layout = dict(row)
                layout["members"] = [{k: normalize(v.value) for k, v in child.attributes.items()}
                                     for child in die.iter_children() if child.tag == "DW_TAG_member"]
                layouts.append(layout)
            if die.tag == "DW_TAG_subprogram" and isinstance(name, str) and re.search("InitializeData|loadFile|breakData|Decode|bundle|master", name, re.I):
                for child in die.iter_children():
                    if child.tag != "DW_TAG_GNU_call_site" or "DW_AT_abstract_origin" not in child.attributes:
                        continue
                    origin = child.get_DIE_from_attribute("DW_AT_abstract_origin")
                    call_name = origin.attributes.get("DW_AT_name")
                    calls.append({"caller": name, "caller_die": die.offset,
                                  "call_site_die": child.offset,
                                  "return_pc": normalize(child.attributes["DW_AT_low_pc"].value) if "DW_AT_low_pc" in child.attributes else None,
                                  "callee": normalize(call_name.value) if call_name else None,
                                  "callee_die": origin.offset,
                                  "basis": "DWARF GNU call-site abstract_origin; executable code not restored"})
            if isinstance(name, str) and re.search("BundleMaster|InitializeData|loadFile|breakData|Decode|Hash.*Master|daCharacter|skill0|master_data", name):
                row = dict(row)
                row["children"] = [{"tag": child.tag, "die_offset": child.offset,
                                    "attributes": {k: {"form": v.form, "value": normalize(v.value)}
                                                   for k, v in child.attributes.items()}}
                                   for child in die.iter_children()]
                selected.append(row)
    for filename, rows in [("dwarf_records.jsonl", records), ("loader_debug.jsonl", selected)]:
        with (args.output / filename).open("w", encoding="utf-8") as out:
            for row in rows:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
    (args.output / "loader_calls.json").write_text(json.dumps(calls, indent=2), encoding="utf-8")
    (args.output / "binary_layouts.json").write_text(json.dumps(layouts, indent=2), encoding="utf-8")
    probes = []
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    for symbol in symbols:
        if symbol["name"] not in ("loadFile", "InitializeData", "DecodeXorData", "c_AES__DecryptN_CSTM"):
            continue
        address = symbol["address"]
        segment = next(s for s in elf.iter_segments() if s["p_type"] == "PT_LOAD" and
                       s["p_vaddr"] <= address < s["p_vaddr"] + s["p_filesz"])
        offset = segment["p_offset"] + address - segment["p_vaddr"]
        code = raw[offset:offset+min(symbol["size"], 64)]
        insts = list(md.disasm(code, address))
        probes.append({"name": symbol["name"], "address": address, "file_offset": offset,
                       "first_64_hex": code.hex(), "decoded_prefix_bytes": sum(i.size for i in insts),
                       "instruction_count": len(insts), "tested_bytes": len(code),
                       "status": "EXECUTABLE_CODE_NOT_RECOVERED"})
    (args.output / "code_probe.json").write_text(json.dumps(probes, indent=2), encoding="utf-8")
    result = {"source_sha256": sha, "ranges": ranges, "symbols": len(symbols),
              "dwarf_records": len(records), "selected": len(selected), "compilation_units": units}
    (args.output / "debug_recovery.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "compilation_units"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
