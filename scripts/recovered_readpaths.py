"""Export precisely bounded NUtils functions using retained DWARF sizes."""
import hashlib
import json
from pathlib import Path

from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM

from decode_data5 import IMAGE_SHA


def main():
    image = Path("work/protection/nutils_loader_seed1.bin").read_bytes()
    assert hashlib.sha256(image).hexdigest() == IMAGE_SHA
    original = Path("work/apk/lib/arm64-v8a/libChronicleNUtils.so").read_bytes()
    source = json.loads(Path("output/native/readpaths.json").read_text())
    md = Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    output = Path("output/native/recovered_readpaths")
    output.mkdir(parents=True,exist_ok=True)
    rows = []
    for function in source["functions"]:
        attrs = function["attributes"]
        if "DW_AT_low_pc" not in attrs or "DW_AT_high_pc" not in attrs:
            continue
        begin = attrs["DW_AT_low_pc"]["value"]
        size = attrs["DW_AT_high_pc"]["value"]
        code = image[begin:begin+size]
        instructions = list(md.disasm(code,begin))
        assert sum(i.size for i in instructions) == size
        (output/f"{function['name']}.txt").write_text("\n".join(f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in instructions),encoding="utf-8")
        rows.append({"name":function["name"],"rva":hex(begin),"bytes":size,"instruction_count":len(instructions),
                     "code_sha256":hashlib.sha256(code).hexdigest(),"boundary_source":"retained DWARF low_pc/high_pc"})
    result = {"original_library_sha256":hashlib.sha256(original).hexdigest(),"controlled_guest_image_sha256":IMAGE_SHA,
              "functions":rows,"limit":"Guest memory snapshot, not a reconstructed ELF or normal Android startup"}
    (output/"report.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"functions":len(rows),"instruction_bytes":sum(r["bytes"] for r in rows)}))


if __name__ == "__main__":
    main()
