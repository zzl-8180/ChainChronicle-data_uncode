"""Locate direct ADRP+ADD references to metadata filename in a guest image.

Original ELF supplies executable boundaries; all byte access uses guest RVAs.
This does not claim a complete call graph.
"""
import hashlib
import io
import json
import struct
from pathlib import Path

from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from elftools.elf.elffile import ELFFile


def main():
    raw = Path("work/apk/lib/arm64-v8a/libil2cpp.so").read_bytes()
    image = Path("work/protection/il2cpp_loader_seed1.bin").read_bytes()
    targets = []
    pos = 0
    while True:
        pos = image.find(b"global-metadata.dat\0",pos)
        if pos < 0:
            break
        targets.append(pos)
        pos += 1
    md = Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    md.detail = True
    refs = []
    elf = ELFFile(io.BytesIO(raw))
    for segment in elf.iter_segments():
        if segment["p_type"] != "PT_LOAD" or not segment["p_flags"] & 1:
            continue
        begin,end = segment["p_vaddr"],segment["p_vaddr"]+segment["p_filesz"]
        for rva in range(begin,end-4,4):
            word = struct.unpack_from("<I",image,rva)[0]
            if word & 0x9f000000 != 0x90000000:
                continue
            imm = ((word>>5 & 0x7ffff)<<2) | (word>>29 & 3)
            if imm & 0x100000:
                imm -= 0x200000
            page = (rva & ~0xfff)+(imm<<12)
            target = next((t for t in targets if t & ~0xfff == page),None)
            if target is None:
                continue
            reg = word & 31
            for step in range(4,65,4):
                add = struct.unpack_from("<I",image,rva+step)[0]
                between = list(md.disasm(image[rva+4:rva+step],rva+4))
                if sum(i.size for i in between) != step-4:
                    break
                if any(i.mnemonic in {"bl","b","blr","br","ret","cbz","cbnz","tbz","tbnz"}
                       or i.mnemonic.startswith("b.") for i in between):
                    break
                if any(md.reg_name(w) in {f"x{reg}",f"w{reg}"} for i in between for w in i.regs_access()[1]):
                    break
                if add & 0xffc00000 == 0x91000000 and add>>5 & 31 == reg and page+(add>>10 & 0xfff)==target:
                    context = list(md.disasm(image[max(begin,rva-96):rva+step+112],max(begin,rva-96)))
                    refs.append({"adrp_rva":hex(rva),"use_rva":hex(rva+step),"string_rva":hex(target),
                                 "context":[f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in context]})
    output = Path("output/il2cpp")
    output.mkdir(parents=True,exist_ok=True)
    result = {"original_library_sha256":hashlib.sha256(raw).hexdigest(),"guest_image_sha256":hashlib.sha256(image).hexdigest(),
              "filename_rvas":[hex(t) for t in targets],"references":refs,
              "scope":"Direct ADRP+ADD in original executable ranges; recovered image, not full CFG"}
    (output/"metadata_entry_refs.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"filename_rvas":result["filename_rvas"],"use_rvas":[r["use_rva"] for r in refs]}))


if __name__ == "__main__":
    main()
