"""Execute the actual secondary conversion for descriptor 0x260.

Only native conversion slices run. Frame allocation is executed from its real
prologue. JNI calls and intervening environment code are not synthesized.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_SP, UC_ARM64_REG_X0, UC_ARM64_REG_X29

from jni_prefix_probe import prepare_experiment
from protection_emulate import BASE, STACK


def stop_at(e, rva, label):
    def hook(uc, address, size, data):
        e.failure = label
        uc.emu_stop()
    return e.uc.hook_add(UC_HOOK_CODE, hook, begin=BASE+rva, end=BASE+rva)


def attempt(e, rva, *args, **kwargs):
    try:
        return {"entry": hex(rva), "status": "RETURNED", "value": hex(e.call(rva, *args, **kwargs))}
    except ValueError as error:
        return {"entry": hex(rva), "status": "STOPPED", "reason": str(error)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--callback-region", action="store_true",
                        help="controlled descriptor 0xe0/key-source 0x13f63c candidate; not observed runtime mapping")
    parser.add_argument("--loader-probe", action="store_true", help="probe callback with mapped NUtils; implies callback-region")
    parser.add_argument("--library-name", choices=("libChronicleNUtils.so", "libil2cpp.so"), default="libChronicleNUtils.so",
                        help="limit the loader probe to one existing APK library")
    parser.add_argument("--resume-chunks", type=int, default=0, choices=range(9),
                        help="bounded additional 100M-instruction slices after execution-limit stops")
    parser.add_argument("--accelerate-lz4", action="store_true", help="verified, bounded LZ4 model for bulk decompression")
    args = parser.parse_args()
    if args.loader_probe:
        args.callback_region = True
    heap_size = 0x4000000 if args.library_name == "libil2cpp.so" else 0x1000000
    e, raw, preparatory = prepare_experiment(args.seed, heap_size=heap_size)
    Path("work/protection").mkdir(parents=True, exist_ok=True)
    Path("output/protection").mkdir(parents=True, exist_ok=True)
    lz4_model = None
    if args.accelerate_lz4:
        from guest_lz4 import install
        lz4_model = install(e)
    steps = []
    # DT_INIT partial state already has descriptor 0x80 decoded. Running
    # JNI_OnLoad's prefix again would re-encode that key-source region.
    hook = stop_at(e, 0x14ef6c, "STOP_AFTER_PRIMARY_FRAME_ALLOCATION")
    e.uc.reg_write(UC_ARM64_REG_SP, STACK+0xf0000)
    steps.append(attempt(e, 0x14ee40, e.allocate(8), 0))
    e.uc.hook_del(hook)
    hook = stop_at(e, 0x15179c, "STOP_BEFORE_SECONDARY_INIT_CALL")
    frame = e.uc.reg_read(UC_ARM64_REG_X0+19)
    ctx = struct.unpack("<Q", e.uc.mem_read(frame+0x60, 8))[0]
    e.uc.reg_write(UC_ARM64_REG_X0+22, ctx)
    # Flattened converter's initial dispatcher is a live-in, established by
    # MOV/MOVK at 14f1ac/14f1d0 in the earlier conversion. Set that exact
    # constant explicitly since the already-converted prefix was skipped.
    e.uc.reg_write(UC_ARM64_REG_X0+27, 0xd90e836e)
    primary_regs = {reg: e.uc.reg_read(reg) for reg in
                    [UC_ARM64_REG_SP, UC_ARM64_REG_X29] + [UC_ARM64_REG_X0+i for i in (19,20,21,22,28)]}
    steps.append(attempt(e, 0x150e70))
    e.uc.hook_del(hook)
    # Allocate every local buffer with the secondary function's real prologue.
    hook = stop_at(e, 0x14b828, "STOP_AFTER_SECONDARY_FRAME_ALLOCATION")
    e.uc.reg_write(UC_ARM64_REG_SP, STACK+0xc0000)
    steps.append(attempt(e, 0x14b6b4, 0, 0))
    e.uc.hook_del(hook)
    frame = e.uc.reg_read(UC_ARM64_REG_X29)
    ctx = struct.unpack("<Q", e.uc.mem_read(frame-0xd8, 8))[0]
    if not STACK <= ctx < frame:
        raise ValueError(f"Secondary frame invalid: ctx={hex(ctx)}, frame={hex(frame)}, steps={steps}")
    context = struct.unpack("<Q", e.uc.mem_read(BASE+0x1a4558, 8))[0]
    descriptor = bytes(e.uc.mem_read(context+0x260, 32))
    address, end, length, mask = struct.unpack("<QQQQ", descriptor)
    assert end-address == length and BASE <= address < end <= BASE+0x200000
    key_source = struct.unpack("<Q", e.uc.mem_read(context+0x80, 8))[0]
    key = bytes(e.uc.mem_read(key_source, 16))
    before = bytes(e.uc.mem_read(address, length))
    hook = stop_at(e, 0x14db04, "STOP_BEFORE_CALLBACK_ASSIGNMENT")
    steps.append(attempt(e, 0x14d250))
    e.uc.hook_del(hook)
    code = bytes(e.uc.mem_read(address, length))
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    native = list(md.disasm(code, address-BASE))
    assert sum(i.size for i in native) == length, "Conversion did not produce a complete instruction region"
    callback_region = None
    if args.callback_region:
        # The first 16 bytes are XORed with the key bytes by the real loop.
        # A prefix search has ONE unique key among recovered module bytes that
        # turns the target into a complete four-instruction stack prologue.
        # Its 43 occurrences are identical; runtime pointer selection unknown.
        saved_desc = bytes(e.uc.mem_read(context, 32))
        saved_key_pointer = bytes(e.uc.mem_read(context+0xc0, 8))
        target_desc = bytes(e.uc.mem_read(context+0xe0, 32))
        target, target_end, target_size = struct.unpack("<QQQ", target_desc[:24])
        assert target_end-target == target_size
        e.uc.mem_write(context, target_desc)
        e.uc.mem_write(context+0xc0, struct.pack("<Q", BASE+0x13f63c))
        for reg, value in primary_regs.items():
            e.uc.reg_write(reg, value)
        e.uc.reg_write(UC_ARM64_REG_X0+27, 0xd90e836e)
        hook = stop_at(e, 0x15179c, "STOP_AFTER_CONTROLLED_CALLBACK_REGION_CONVERSION")
        candidate_step = attempt(e, 0x150e70)
        e.uc.hook_del(hook)
        candidate = bytes(e.uc.mem_read(target, target_size))
        ins = list(md.disasm(candidate, target-BASE))
        callback_region = {"status": "CONTROLLED_KEY_CANDIDATE", "step": candidate_step,
                           "rva": hex(target-BASE), "bytes": target_size, "key_source_candidate": "0x13f63c",
                           "decoded_prefix_bytes": sum(i.size for i in ins),
                           "sha256": hashlib.sha256(candidate).hexdigest()}
        Path(f"work/protection/callback_region_seed{args.seed}.bin").write_bytes(candidate)
        Path(f"output/protection/callback_region_seed{args.seed}.txt").write_text("\n".join(f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in ins), encoding="utf-8")
        e.uc.mem_write(context, saved_desc)
        e.uc.mem_write(context+0xc0, saved_key_pointer)
    steps.append(attempt(e, 0x91a2c))
    loader_probe = None
    if args.loader_probe:
        source = Path("work/apk/lib/arm64-v8a")/args.library_name
        library = source.read_bytes()
        elf = ELFFile(io.BytesIO(library))
        library_base = 0x50000000
        mapped_size = max(0x100000, max((s["p_vaddr"]+s["p_memsz"]+0xfff) & ~0xfff
                                      for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"))
        e.uc.mem_map(library_base, mapped_size)
        e.lz4_module_range = (library_base,library_base+mapped_size)
        for segment in elf.iter_segments():
            if segment["p_type"] == "PT_LOAD":
                e.uc.mem_write(library_base+segment["p_vaddr"], segment.data())
        init = next(t.entry.d_val for s in elf.iter_segments() if s["p_type"] == "PT_DYNAMIC"
                    for t in s.iter_tags() if t.entry.d_tag == "DT_INIT")
        # These two builds use ADRP X0 to the init's page as the descriptor.
        assert library[init:init+4] == bytes.fromhex("00000090")
        descriptor_rva = init & ~0xfff
        maps = []
        for module, base, data in (("libcompatible.so", BASE, raw),
                                   (args.library_name, library_base, library)):
            for segment in ELFFile(io.BytesIO(data)).iter_segments():
                if segment["p_type"] == "PT_LOAD":
                    begin = base + (segment["p_vaddr"] & ~0xfff)
                    map_end = base + ((segment["p_vaddr"]+segment["p_memsz"]+0xfff) & ~0xfff)
                    mode = "r-xp" if segment["p_flags"] & 1 else "rw-p"
                    maps.append(f"{begin:x}-{map_end:x} {mode} {segment['p_offset'] & ~0xfff:08x} 00:00 0 /guest/{module}\n")
            e.guest_files[f"/guest/{module}".encode()] = data
        e.guest_files[b"/proc/self/maps"] = "".join(maps).encode()
        e.uc.reg_write(UC_ARM64_REG_SP, STACK+0x60000)
        library_before = bytes(e.uc.mem_read(library_base, mapped_size))
        loader_step = attempt(e, 0x165764, library_base+descriptor_rva, instruction_limit=100000000)
        loader_chunks = [loader_step]
        for index in range(args.resume_chunks):
            if "Execution limit" not in loader_step.get("reason", ""):
                break
            try:
                value = e.resume()
                loader_step = {"status": "RETURNED", "value": hex(value)}
            except ValueError as error:
                loader_step = {"status": "STOPPED", "reason": str(error)}
            loader_chunks.append(loader_step)
        library_after = bytes(e.uc.mem_read(library_base, mapped_size))
        library_label = "nutils" if args.library_name == "libChronicleNUtils.so" else "il2cpp"
        Path(f"work/protection/{library_label}_loader_seed{args.seed}.bin").write_bytes(library_after)
        function_prefixes = {hex(rva): {"changed_bytes": sum(a != b for a,b in zip(library_before[rva:rva+64], library_after[rva:rva+64])),
                                       "decoded_prefix_bytes": sum(i.size for i in md.disasm(library_after[rva:rva+64], rva))}
                             for rva in (0x22f1c,0x26cfc,0x207d0,0x2097c)}
        loader_probe = {"source": str(source), "sha256": hashlib.sha256(library).hexdigest(),
                        "guest_base": hex(library_base), "init_rva": hex(init), "guest_input_descriptor": hex(descriptor_rva), "step": loader_step,
                        "controlled_proc_maps": maps,
                        "instruction_limit": 100000000, "changed_bytes": sum(a != b for a,b in zip(library_before,library_after)),
                        "mapped_bytes": mapped_size,
                        "controlled_heap_bytes": heap_size,
                        "loader_chunks": loader_chunks,
                        "function_prefixes": function_prefixes,
                        "syscalls": e.syscalls[-8:]}
    e.uc.reg_write(UC_ARM64_REG_SP, STACK+0x90000)
    hook = stop_at(e, 0x13094c, "STOP_BEFORE_PLATFORM_SYMBOL_RESOLVER")
    steps.append(attempt(e, 0x1303c8))
    e.uc.hook_del(hook)
    if "STOP_BEFORE_PLATFORM_SYMBOL_RESOLVER" in steps[-1].get("reason", ""):
        # Isolate the following transformation from platform symbol discovery.
        # No resolver return value is supplied. Unknown indirect calls stop.
        steps.append(attempt(e, 0x130950))
    output = Path("output/protection/signal_region")
    output.mkdir(parents=True, exist_ok=True)
    Path(f"work/protection/signal_region_seed{args.seed}.bin").write_bytes(code)
    Path(f"work/protection/compatible_signal_seed{args.seed}.bin").write_bytes(bytes(e.uc.mem_read(BASE, 0x200000)))
    (output/f"code_seed{args.seed}.txt").write_text("\n".join(f"{hex(i.address)}: {i.mnemonic} {i.op_str}" for i in native), encoding="utf-8")
    result = {"source_sha256": hashlib.sha256(raw).hexdigest(), "seed": args.seed,
              "preparatory": preparatory, "steps": steps,
              "descriptor": {"offset": "0x260", "start_rva": hex(address-BASE), "end_rva": hex(end-BASE),
                             "length": length, "last_qword_raw": hex(mask)},
              "key_source_rva": hex(key_source-BASE), "key_raw_hex": key.hex(),
              "controlled_live_in": {"w27": "0xd90e836e", "purpose": "primary flattened dispatcher initial state"},
              "changed_bytes": sum(a != b for a,b in zip(before, code)),
              "decoded_prefix_bytes": sum(i.size for i in native),
              "sha256": hashlib.sha256(code).hexdigest(), "tracked_writes": e.tracked_writes,
              "callback_region": callback_region,
              "loader_probe": loader_probe,
              "optional_lz4_model": lz4_model,
              "limits": ["Controlled slice re-entry after partial DT_INIT, not normal Android startup",
                         "No JavaVM/JNI functions invoked; real prologue allocates guest buffers",
                         "Callback candidate uses explicit descriptor/key pointer replacement when requested",
                         "No host syscall forwarding; loader address-to-library mapping is controlled"]}
    suffix = "_il2cpp" if args.library_name == "libil2cpp.so" else ""
    (output/f"report_seed{args.seed}{'_callback_candidate' if args.callback_region else ''}{suffix}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
