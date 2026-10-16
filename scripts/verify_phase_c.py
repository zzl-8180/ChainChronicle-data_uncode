"""Regression for the concrete 20-byte callback-reference miss and false hits."""
import hashlib
import io
import json
import struct
import subprocess
import sys
from pathlib import Path
from elftools.elf.elffile import ELFFile


def main():
    source = Path("work/apk/lib/arm64-v8a/libcompatible.so")
    raw = source.read_bytes()
    elf = ELFFile(io.BytesIO(raw))
    assert any(s["p_type"] == "PT_LOAD" and s["p_offset"] == s["p_vaddr"]
               and s["p_vaddr"] <= 0x91a2c < 0x91aa4 <= s["p_vaddr"] + s["p_filesz"]
               for s in elf.iter_segments())
    before = hashlib.sha256(raw).hexdigest()
    work = Path("work/phase_c_checks")
    work.mkdir(parents=True, exist_ok=True)

    def scan(path, window, label, slot="0x19c6e0"):
        output = work / f"{label}.json"
        subprocess.run([sys.executable, "scripts/elf_global_refs.py", str(path), "--slot", slot,
                        "--window", str(window), "--output", str(output)],
                       check=True, stdout=subprocess.DEVNULL)
        return json.loads(output.read_text())

    short = scan(source, 16, "real_16")
    broad = scan(source, 64, "real_64")
    assert {r["adrp_address"] for r in short} == {0x99b58}
    assert {r["adrp_address"] for r in broad} == {0x91a9c, 0x99b58}
    changed = bytearray(raw)
    # This build's executable segment maps RVA to identical file offset here.
    struct.pack_into("<I", changed, 0x91aa0, 0xaa1f03ed)  # MOV x13, xzr: invalidates ADRP base
    copy = work / "clobbered_base.so"
    copy.write_bytes(changed)
    assert {r["adrp_address"] for r in scan(copy, 64, "clobbered_64")} == {0x99b58}
    # Byte writes were previously unsupported: exercise a controlled STRB.
    changed = bytearray(raw)
    pages = (0x1a4000 - (0x91a2c & ~0xfff)) >> 12
    adrp = 0x90000000 | ((pages & 3) << 29) | (((pages >> 2) & 0x7ffff) << 5) | 8
    struct.pack_into("<II", changed, 0x91a2c, adrp, 0x39000000 | (0x6a0 << 10) | (8 << 5) | 9)
    copy = work / "synthetic_flag_store.so"
    copy.write_bytes(changed)
    flag_refs = scan(copy, 64, "synthetic_flag", "0x1a46a0")
    assert any(r["ldr_address"] == 0x91a30 and r["access"] == "STR_TO_ADDRESS" for r in flag_refs)
    subprocess.run([sys.executable, "scripts/callback_sample.py"], check=True, stdout=subprocess.DEVNULL)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    sample = json.loads(Path("output/protection/callback_sample.json").read_text())
    assert sample["sha256"] == before and sample["instruction_count"] == 40
    result = {"status": "PASS", "checks": ["16-byte miss reproduced; 64-byte finds actual write reference",
              "Intervening register overwrite rejected", "Synthetic byte store recognized",
              "Complete callback assignment block modeled for two flag values and two load biases",
              "Original library unchanged"],
              "limits": "Synthetic flag/store/load biases are not game runtime observations; main-table decoding unverified"}
    Path("output/validation/phase_c_checks.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
