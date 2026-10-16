"""Extract targeted DWARF signatures and call-site arguments from retained bytes.

No association between a disk filename and a native function is assumed.
"""
import hashlib
import inspect
import io
import json
from pathlib import Path

from elftools.dwarf.dwarfinfo import DWARFInfo, DebugSectionDescriptor, DwarfConfig
from elftools.dwarf.dwarf_expr import DWARFExprParser

SOURCE = Path("work/apk/lib/arm64-v8a/libChronicleNUtils.so")
TARGETS = {"loadFile", "saveFile", "InitializeData", "initializeNative", "initializeNative_type0",
           "DecodeRotData", "DecodeXorData", "Native_CheckHashM", "InitializeEnesetDataNative_body"}
TARGETS.update({"Java_com_sega_chainchronicle_MainActivity_init_body", "callJavaTest00", "callJavaTest03"})


def main():
    raw = SOURCE.read_bytes()
    recovery = json.loads(Path("output/native/debug_recovery.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == recovery["source_sha256"]
    kwargs = {k: None for k in inspect.signature(DWARFInfo).parameters if k != "config"}
    for name, (start, end) in recovery["ranges"].items():
        kwargs[name] = DebugSectionDescriptor(io.BytesIO(raw[start:end]), name, start, end-start, 0)
    dwarf = DWARFInfo(config=DwarfConfig(True, "AArch64", 8), **kwargs)
    expr = DWARFExprParser(dwarf.structs)

    def name(die):
        if "DW_AT_name" in die.attributes:
            return die.attributes["DW_AT_name"].value.decode("utf-8", "backslashreplace")
        for key in ("DW_AT_abstract_origin", "DW_AT_specification"):
            if key in die.attributes:
                return name(die.get_DIE_from_attribute(key))
        return None

    def attrs(die):
        result = {}
        for key, attr in die.attributes.items():
            value = attr.value.decode("utf-8", "backslashreplace") if isinstance(attr.value, bytes) else attr.value
            row = {"form": attr.form, "value": value}
            if attr.form == "DW_FORM_exprloc":
                row["expression"] = [{"op": op.op_name, "args": op.args} for op in expr.parse_expr(attr.value)]
            result[key] = row
        return result

    def type_name(die, depth=0):
        if depth > 12:
            return "UNKNOWN_TYPE"
        if "DW_AT_type" not in die.attributes:
            return name(die) or "void"
        suffix = {"DW_TAG_pointer_type": "*", "DW_TAG_reference_type": "&", "DW_TAG_array_type": "[]"}.get(die.tag, "")
        if suffix:
            return type_name(die.get_DIE_from_attribute("DW_AT_type"), depth+1) + suffix
        if die.tag == "DW_TAG_const_type":
            return type_name(die.get_DIE_from_attribute("DW_AT_type"), depth+1) + " const"
        child = die.get_DIE_from_attribute("DW_AT_type")
        return type_name(child, depth+1)

    functions, edges, variables = [], [], []

    def walk(die, function=None):
        if die.tag == "DW_TAG_subprogram":
            function = name(die)
            if function in TARGETS:
                children = list(die.iter_children())
                functions.append({"name": function, "die_offset": die.offset, "attributes": attrs(die),
                                  "parameters": [{"name": name(c), "type": type_name(c), "attributes": attrs(c)}
                                                 for c in children if c.tag == "DW_TAG_formal_parameter"],
                                  "locals": [{"name": name(c), "type": type_name(c), "attributes": attrs(c)}
                                             for c in children if c.tag == "DW_TAG_variable"]})
        if die.tag == "DW_TAG_GNU_call_site" and "DW_AT_abstract_origin" in die.attributes:
            callee = name(die.get_DIE_from_attribute("DW_AT_abstract_origin"))
            if function in TARGETS or callee in TARGETS:
                edges.append({"caller": function, "callee": callee, "die_offset": die.offset,
                              "attributes": attrs(die), "arguments": [attrs(c) for c in die.iter_children()]})
        if die.tag == "DW_TAG_variable" and (name(die) in {"master_data", "master_bundle_nandoku"}
                                             or (name(die) or "").startswith("s_pBundleMasterData")
                                             or (name(die) or "").startswith("s_nBundleMasterData")):
            variables.append({"name": name(die), "function_scope": function, "die_offset": die.offset,
                              "type": type_name(die), "attributes": attrs(die)})
        for child in die.iter_children():
            walk(child, function)

    for cu in dwarf.iter_CUs():
        walk(cu.get_top_DIE())
    result = {"source": str(SOURCE), "sha256": recovery["source_sha256"], "functions": functions,
              "call_sites": edges, "variables": variables,
              "limits": ["DWARF call sites do not recover executable control flow or all callers",
                         "data5, chronicle.dat and resource bundle input mappings remain UNKNOWN"]}
    Path("output/native/readpaths.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"functions": len(functions), "call_sites": len(edges), "variables": len(variables),
                      "incoming": [{"caller": e["caller"], "callee": e["callee"]}
                                   for e in edges if e["callee"] in TARGETS]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
