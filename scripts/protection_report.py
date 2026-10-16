"""Validate recovered code ranges and summarize natural versus controlled runs."""
import hashlib
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM


def main():
    sample = json.loads(Path("output/protection/protection_sample.json").read_text())
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    output = Path("output/protection/recovered_code")
    output.mkdir(parents=True, exist_ok=True)
    ranges = []
    for stage, rva, size in [(1, 0x146820, 2452), (2, 0x1471b4, 17664)]:
        first = Path(f"work/protection/compatible_stage{stage}_seed1.bin").read_bytes()[rva:rva+size]
        second = Path(f"work/protection/compatible_stage{stage}_seed2.bin").read_bytes()[rva:rva+size]
        if len(first) != size or first != second:
            raise ValueError("Recovered range differs between controlled seeds or is truncated")
        instructions = list(md.disasm(first, rva))
        if sum(i.size for i in instructions) != size:
            raise ValueError("Recovered range has an undecodable instruction gap")
        (output / f"range_{rva:x}.txt").write_text("\n".join(f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in instructions), encoding="utf-8")
        Path(f"work/protection/range_{rva:x}.bin").write_bytes(first)
        ranges.append({"rva": hex(rva), "bytes": size, "instructions": len(instructions),
                       "sha256": hashlib.sha256(first).hexdigest(), "two_seeds_identical": True,
                       "boundary_basis": "control descriptor; may include multiple functions"})
    runs = []
    for label in ["seed1", "seed2", "seed1_context0_omitctors", "seed1_context1_omitctors"]:
        path = Path(f"output/protection/emulation/stages_{label}.json")
        if "context" in label and not path.exists():
            continue  # Optional counterfactual runs are not a validation prerequisite.
        result = json.loads(path.read_text())
        assert result["source_sha256"] == sample["source_sha256"]
        runs.append({"label": label, "stages": result["stages"],
                     "controlled_context_result": result["controlled_context_result"],
                     "controlled_omit_constructors": result["controlled_omit_constructors"],
                     "tracked_writes": result["tracked_writes"]})
    result = {"status": "PASS_RECOVERED_RANGES", "source_sha256": sample["source_sha256"],
              "protection_record_count": sample["record"]["count"], "stage1_code": sample["stage1_code"],
              "recovered_ranges": ranges, "runs": runs,
              "limits": ["Controlled context returns and omitted constructors are counterfactual, not runtime validation",
                         "No flag or callback-cell write was observed in these bounded runs",
                         "NUtils loader code and game master tables remain unrecovered"]}
    Path("output/protection/recovery_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "recovered_ranges": ranges}, indent=2))


if __name__ == "__main__":
    main()
