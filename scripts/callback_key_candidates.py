"""Recover the unique local 16-byte candidate under an evidenced XOR prefix rule."""
import hashlib
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM


def main():
    raw = Path("work/apk/lib/arm64-v8a/libcompatible.so").read_bytes()
    image = Path("work/protection/compatible_stage3_seed1.bin").read_bytes()
    target = raw[0x153200:0x153210]
    md = Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    # Confirm the first-block rule on two actually executed conversions.
    for target_rva,key_rva,decoded_file in ((0x14b6b4,0x14ee40,"work/protection/compatible_jni_conversion.bin"),
                                          (0x1303c8,0xea3a0,"work/protection/compatible_signal_seed1.bin")):
        decoded = Path(decoded_file).read_bytes()[target_rva:target_rva+16]
        assert bytes(a^b for a,b in zip(raw[target_rva:target_rva+16],image[key_rva:key_rva+16])) == decoded
    candidates = {}
    for rva in range(0x50000,0x193ee0,4):
        key = image[rva:rva+16]
        prefix = bytes(a^b for a,b in zip(target,key))
        instructions = list(md.disasm(prefix,0x153200))
        if len(instructions) != 4:
            continue
        first = instructions[0]
        if first.mnemonic != "stp" or not first.op_str.startswith("x29, x30, [sp,"):
            continue
        if any(i.mnemonic not in {"stp","str","mov","sub","adrp","add","mrs"} for i in instructions[1:]):
            continue
        entry = candidates.setdefault(key.hex(),{"occurrences":[],"derived_prefix_hex":prefix.hex(),
                                                  "derived_instructions":[f"{i.mnemonic} {i.op_str}" for i in instructions]})
        entry["occurrences"].append(hex(rva))
    assert len(candidates) == 1 and "0x13f63c" in next(iter(candidates.values()))["occurrences"]
    result = {"raw_source_sha256":hashlib.sha256(raw).hexdigest(),"partial_image_sha256":hashlib.sha256(image).hexdigest(),
              "target_rva":"0x153200","candidates":candidates,
              "method":"Evidenced first16-byte XOR rule + four-instruction stack prologue constraint; one distinct key",
              "limit":"Runtime selection of the key pointer is UNKNOWN; full native conversion/loader/data5 integrity corroborate candidate"}
    Path("output/protection/callback_key_candidates.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"distinct_keys":len(candidates),"occurrences":len(next(iter(candidates.values()))["occurrences"])}))


if __name__ == "__main__":
    main()
