"""Decode and validate one actual protection record; not a game data5 decoder."""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from protection_emulate import Experiment, SOURCE

EXPECTED = "79b6ae193625494b5facbc1c7eafa5bb16c4252dd9050fe10caee2393aa8767c"


def parse_record(raw, experiment):
    # Header pointer: GOT 0x19c6f8 -> symbol at 0x1407a8;
    # field +0x60 gives 0x141638. Native init copies 0x1000 bytes from +20.
    header = struct.unpack_from("<14Q", raw, 0x1407a8)
    address = header[12]
    length = struct.unpack_from("<I", raw, address)[0]
    if address+20+0x1000 > len(raw) or length == 0 or length > 0x1000:
        raise ValueError("Truncated or invalid control-record input")
    block = raw[address+20:address+20+0x1000]
    size = length & ~15  # actual AND mask at 0x14345c
    decoded = experiment.decrypt(raw[address+4:address+20], block[:size]) + block[size:]
    count = struct.unpack_from("<I", decoded)[0]
    if count == 0 or 4+count*12 > size:
        raise ValueError("Invalid descriptor count")
    descriptors, destination = [], 0
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    for index in range(count):
        identifier, offset, extent = struct.unpack_from("<III", decoded, 4+index*12)
        source = offset if offset & 1 == 0 else offset-1
        if extent == 0 or source < 4+count*12 or source+extent > len(decoded) or destination+extent > 0x1000:
            raise ValueError("Descriptor exceeds source/destination boundary")
        payload = decoded[source:source+extent]
        insts = list(md.disasm(payload, destination))
        if sum(i.size for i in insts) != extent or not any(i.mnemonic == "svc" for i in insts):
            raise ValueError("Payload is not a complete SVC instruction fragment")
        descriptors.append({"record_index": index, "descriptor_offset": 4+index*12,
                            "identifier_raw": identifier, "source_offset_raw": offset, "size_raw": extent,
                            "destination_offset": destination, "payload_sha256": hashlib.sha256(payload).hexdigest(),
                            "instructions": [f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in insts]})
        destination += (extent+3) & ~3
    if len({r["identifier_raw"] for r in descriptors}) != count:
        raise ValueError("Duplicate control identifiers")
    return decoded, {"source_record_file_offset": address, "length_raw": length,
                     "converted_bytes": size, "copied_bytes": 0x1000, "count": count,
                     "assembled_bytes": destination, "descriptors": descriptors}


def main():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED, "Pinned build only; locate rules again for other input"
    experiment = Experiment(raw, 1)
    # Validate the actual library's AES routine against independent published vector.
    known = experiment.decrypt(bytes.fromhex("000102030405060708090a0b0c0d0e0f"), bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a"))
    assert known.hex() == "00112233445566778899aabbccddeeff"
    decoded, record = parse_record(raw, experiment)
    repeat, repeat_record = parse_record(raw, Experiment(raw, 1))
    assert decoded == repeat and record == repeat_record
    try:
        parse_record(raw[:record["source_record_file_offset"]+20+0xfff], Experiment(raw, 1))
    except ValueError:
        truncated = "REJECTED"
    else:
        raise AssertionError("Truncated copied input accepted")
    prefix = experiment.decrypt(raw[0x1458cc:0x1458dc], raw[0x14007c:0x14007c+612])
    complete = prefix + raw[0x1458cc+612:0x146820]
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    instructions = list(md.disasm(complete, 0x1458cc))
    assert len(complete) == 3924 and sum(i.size for i in instructions) == 3924
    assert instructions[0].mnemonic == "stp" and any(i.mnemonic == "ret" for i in instructions[-3:])
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    Path("work/protection").mkdir(parents=True, exist_ok=True)
    Path("work/protection/init_control_record.bin").write_bytes(decoded)
    Path("work/protection/init_stage1_full.bin").write_bytes(complete)
    result = {"status": "PASS_PROTECTION_SAMPLE", "source": str(SOURCE), "source_sha256": EXPECTED,
              "rule_basis": ["0x1432bc-0x1432d4: key/IV same buffer, key/block widths 16",
                             "0x14345c-0x143470: whole-block length, mode argument 0",
                             "0x12ca2c-0x12ca68: independent block decryption, no IV chaining",
                             "0x1434a8-0x14370c: count, 12-byte descriptors, source selection and aligned destination"],
              "record": record, "native_AES_FIPS197": "PASS", "repeat": "IDENTICAL", "truncated": truncated,
              "stage1_code": {"rva": "0x1458cc", "converted_prefix": 612, "complete_bytes": 3924,
                              "instruction_count": len(instructions), "sha256": hashlib.sha256(complete).hexdigest()},
              "limits": ["This is a protection-layer sample, not a card/skill record",
                         "AES-ECB here does not establish an algorithm for data5 or chronicle.dat",
                         "Instruction recovery is separate from actual Android runtime behavior"]}
    output = Path("output/protection/protection_sample.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "record"} |
                     {"record_count": record["count"], "assembled_bytes": record["assembled_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
