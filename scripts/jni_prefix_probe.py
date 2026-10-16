"""Recover only JNI_OnLoad's conversion prefix, stop before JavaVM GetEnv.

The preceding DT_INIT run stops at an unmodeled Android call. Re-entering
JNI_OnLoad is a controlled experiment on that partial state, not normal startup.
"""
import hashlib
import argparse
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_SP, UC_ARM64_REG_PC, UC_ARM64_REG_X0

from protection_emulate import Experiment, SOURCE, BASE, STACK


def prepare_experiment(seed=1, heap_size=0x1000000):
    """Return live partial DT_INIT state, including its guest heap."""
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "79b6ae193625494b5facbc1c7eafa5bb16c4252dd9050fe10caee2393aa8767c"
    experiment = Experiment(raw, seed, heap_size=heap_size)
    prefix = experiment.decrypt(raw[0x1458cc:0x1458dc], raw[0x14007c:0x14007c+612])
    experiment.uc.mem_write(BASE+0x1458cc, prefix)
    header = experiment.allocate(0x1070, raw[0x1407a8:0x1407a8+0x70])
    experiment.uc.mem_write(BASE+0x1a6948, struct.pack("<QQ", header, BASE))
    preparatory = []
    for rva in (0x1458cc, 0x146820, 0x1471b4):
        try:
            returned = experiment.call(rva)
            preparatory.append({"rva": hex(rva), "status": "RETURNED", "return": hex(returned)})
        except ValueError as error:
            preparatory.append({"rva": hex(rva), "status": "STOPPED", "error": str(error)})
            break
    assert len(preparatory) == 3 and preparatory[-1]["status"] == "STOPPED"
    return experiment, raw, preparatory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment", type=lambda value: int(value, 0),
                        help="controlled reuse of the conversion routine with a different 32-byte descriptor")
    args = parser.parse_args()
    if args.segment is not None and (args.segment % 32 or not 0 <= args.segment < 0x300):
        parser.error("segment must be a 32-byte descriptor offset below 0x300")
    experiment, raw, preparatory = prepare_experiment()
    before = bytes(experiment.uc.mem_read(BASE, 0x200000))
    reached = []

    def stop_before_getenv(uc, address, size, _):
        reached.append(hex(address-BASE))
        experiment.failure = "STOP_BEFORE_JavaVM_GetEnv"
        uc.emu_stop()

    getenv_hook = experiment.uc.hook_add(UC_HOOK_CODE, stop_before_getenv, begin=BASE+0x7e080, end=BASE+0x7e080)
    experiment.uc.reg_write(UC_ARM64_REG_SP, STACK+0xf0000)
    placeholder_vm = experiment.allocate(8)
    try:
        experiment.call(0x14ee40, placeholder_vm, 0)
        stop = "RETURNED"
    except ValueError as error:
        stop = str(error)
    after = bytes(experiment.uc.mem_read(BASE, 0x200000))
    Path("work/protection/compatible_jni_prefix.bin").write_bytes(after)
    # Explicitly isolate the later pure conversion region, with its original
    # frame/context pointers. No skipped JavaVM/environment result is invented.
    experiment.uc.hook_del(getenv_hook)
    conversion_stop = []

    def stop_before_secondary_call(uc, address, size, _):
        conversion_stop.append(hex(address-BASE))
        experiment.failure = "STOP_BEFORE_SECONDARY_INIT_CALL"
        uc.emu_stop()

    experiment.uc.hook_add(UC_HOOK_CODE, stop_before_secondary_call, begin=BASE+0x15179c, end=BASE+0x15179c)
    frame = experiment.uc.reg_read(UC_ARM64_REG_X0+19)
    ctx = struct.unpack("<Q", experiment.uc.mem_read(frame+0x60, 8))[0]
    experiment.uc.reg_write(UC_ARM64_REG_X0+22, ctx)
    try:
        experiment.call(0x150e70)
        conversion_result = "RETURNED"
    except ValueError as error:
        conversion_result = str(error)
    conversion_image = bytes(experiment.uc.mem_read(BASE, 0x200000))
    Path("work/protection/compatible_jni_conversion.bin").write_bytes(conversion_image)
    conversion_range = []
    segment_result = None
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    if conversion_stop:
        context_pointer = struct.unpack("<Q", experiment.uc.mem_read(BASE+0x1a4558, 8))[0]
        address, end_address, length = struct.unpack("<QQQ", experiment.uc.mem_read(context_pointer, 24))
        assert end_address-address == length
        if not (BASE <= address <= BASE+0x200000 and length <= BASE+0x200000-address):
            raise ValueError("Conversion control range is outside the mapped module")
        else:
            code = bytes(experiment.uc.mem_read(address, length))
        native = list(Cs(CS_ARCH_ARM64, CS_MODE_ARM).disasm(code, address-BASE))
        conversion_range = [{"rva": hex(address-BASE), "bytes": length,
                             "decoded_prefix_bytes": sum(i.size for i in native),
                             "sha256": hashlib.sha256(code).hexdigest()}]
        Path("output/protection/jni_secondary.txt").write_text("\n".join(f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in native), encoding="utf-8")
        if args.segment is not None:
            descriptor = bytes(experiment.uc.mem_read(context_pointer+args.segment, 32))
            original_descriptor = bytes(experiment.uc.mem_read(context_pointer, 32))
            experiment.uc.mem_write(context_pointer, descriptor)
            frame = experiment.uc.reg_read(UC_ARM64_REG_X0+19)
            ctx = struct.unpack("<Q", experiment.uc.mem_read(frame+0x60, 8))[0]
            experiment.uc.reg_write(UC_ARM64_REG_X0+22, ctx)
            try:
                experiment.call(0x150e70)
                segment_stop = "RETURNED"
            except ValueError as error:
                segment_stop = str(error)
            address, end_address, length = struct.unpack("<QQQ", descriptor[:24])
            assert end_address-address == length
            code = bytes(experiment.uc.mem_read(address, length))
            native = list(md.disasm(code, address-BASE))
            segment_result = {"descriptor_offset": hex(args.segment), "rva": hex(address-BASE), "bytes": length,
                              "stop": segment_stop, "decoded_prefix_bytes": sum(i.size for i in native),
                              "sha256": hashlib.sha256(code).hexdigest(),
                              "status": "CONTROLLED_DESCRIPTOR_REUSE; semantics not yet verified"}
            Path(f"output/protection/segment_{args.segment:x}.txt").write_text("\n".join(f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in native), encoding="utf-8")
            Path(f"work/protection/segment_{args.segment:x}.bin").write_bytes(code)
            Path(f"work/protection/compatible_segment_{args.segment:x}.bin").write_bytes(bytes(experiment.uc.mem_read(BASE, 0x200000)))
            experiment.uc.mem_write(context_pointer, original_descriptor)
    changes = []
    # Small gaps combine instruction bytes that happen to stay equal.
    start, last = None, None
    for offset in range(0x50000, 0x193ee0):
        if before[offset] != after[offset]:
            if last is not None and offset-last > 32:
                changes.append((start, last+1))
                start = None
            if start is None:
                start = offset
            last = offset
    if start is not None:
        changes.append((start, last+1))
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    output = Path("output/protection/jni_prefix")
    output.mkdir(parents=True, exist_ok=True)
    ranges = []
    for begin, end in changes:
        begin, end = begin & ~3, (end+3) & ~3
        instructions = list(md.disasm(after[begin:end], begin))
        ranges.append({"begin": hex(begin), "end": hex(end), "bytes": end-begin,
                       "decoded_prefix_bytes": sum(i.size for i in instructions),
                       "sha256": hashlib.sha256(after[begin:end]).hexdigest()})
        (output/f"range_{begin:x}.txt").write_text("\n".join(f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in instructions), encoding="utf-8")
    result = {"source_sha256": hashlib.sha256(raw).hexdigest(), "preparatory": preparatory,
              "entry": "0x14ee40", "stop": stop, "reached_GetEnv": reached,
              "changed_ranges": ranges, "flag_writes": experiment.tracked_writes,
              "isolated_conversion": {"entry": "0x150e70", "stop": conversion_result,
                                      "reached_stop": conversion_stop, "recovered_range": conversion_range,
                                      "assumption": "Re-enter conversion region before normal JNI/environment path; frame context reused"},
              "controlled_segment": segment_result,
              "context_qwords": {hex(i): hex(struct.unpack("<Q", experiment.uc.mem_read(context_pointer+i, 8))[0])
                                  for i in range(0, 0x300, 8)} if conversion_stop else {},
              "limits": ["Re-entry into partial initialization is controlled, not observed normal startup",
                         "No JavaVM/JNI function invoked or modeled",
                         "Changed-range boundaries are byte-difference groups, not function boundaries"]}
    (output/(f"segment_{args.segment:x}_report.json" if args.segment is not None else "report.json")).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "context_qwords"}, indent=2))


if __name__ == "__main__":
    main()
