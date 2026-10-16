"""Optional standard LZ4 fast-decompress model, bounded to guest heap buffers.

Checks against the actual native function before substituting the bulk copy.
No change to encryption or loader/control logic.
"""
import hashlib
import struct

import lz4.block
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X30, UC_ARM64_REG_PC

from protection_emulate import BASE, HEAP, Experiment


def compressed_span(data, expected):
    pos, produced = 0, 0
    def extended(length):
        nonlocal pos
        if length == 15:
            while True:
                if pos >= len(data):
                    raise ValueError("Truncated LZ4 length")
                byte = data[pos]
                pos += 1
                length += byte
                if byte != 255:
                    break
        return length
    while produced < expected:
        if pos >= len(data):
            raise ValueError("Truncated LZ4 token")
        token = data[pos]
        pos += 1
        literal = extended(token >> 4)
        pos += literal
        produced += literal
        if pos > len(data) or produced > expected:
            raise ValueError("LZ4 literal exceeds bounds")
        if produced == expected:
            return pos
        if pos+2 > len(data):
            raise ValueError("Truncated LZ4 offset")
        offset = struct.unpack_from("<H",data,pos)[0]
        pos += 2
        if not 0 < offset <= produced:
            raise ValueError("LZ4 invalid backreference")
        produced += extended(token & 15)+4
        if produced > expected:
            raise ValueError("LZ4 match exceeds output")
    raise ValueError("Empty output unsupported by this bounded model")


def install(e):
    checks = []
    test_e = Experiment(e.raw,1)
    for size in (32,211,4096):
        plain = bytes((i*17+i//31) & 255 for i in range(size))
        compressed = lz4.block.compress(plain,store_size=False)
        assert compressed_span(compressed,size) == len(compressed)
        source = test_e.allocate(len(compressed)+64,compressed+bytes(64))
        dest = test_e.allocate(size+64)
        assert test_e.call(0xb19b4,source,dest,size) == len(compressed)
        assert bytes(test_e.uc.mem_read(dest,size)) == plain
        checks.append({"plain_bytes":size,"compressed_bytes":len(compressed),"native_match":"PASS"})
    records = []
    def decompress(uc,address,size,unused):
        source,dest,expected = [uc.reg_read(UC_ARM64_REG_X0+i) for i in range(3)]
        try:
            destinations = [(HEAP,e.heap_limit),(BASE,BASE+0x200000)]
            if hasattr(e,"lz4_module_range"):
                destinations.append(e.lz4_module_range)
            if not 0 < expected <= 32*1024*1024 or not any(begin <= dest and dest+expected <= end for begin,end in destinations):
                raise ValueError("LZ4 output outside bounds")
            source_end = next((end for begin,end in destinations if begin <= source < end),None)
            if source_end is None:
                raise ValueError(f"LZ4 source outside guest ranges: {hex(source)}")
            available = min(expected+expected//255+64,source_end-source)
            data = bytes(uc.mem_read(source,available))
            consumed = compressed_span(data,expected)
            plain = lz4.block.decompress(data[:consumed],uncompressed_size=expected)
            if len(plain) != expected:
                raise ValueError("LZ4 output length mismatch")
            uc.mem_write(dest,plain)
            records.append({"input_pointer":hex(source),"output_pointer":hex(dest),"compressed_bytes":consumed,
                            "plain_bytes":expected,"compressed_sha256":hashlib.sha256(data[:consumed]).hexdigest(),
                            "plain_sha256":hashlib.sha256(plain).hexdigest()})
            uc.reg_write(UC_ARM64_REG_X0,consumed)
            uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
        except Exception as error:
            e.failure = "LZ4 bounded model: "+str(error)
            uc.emu_stop()
    e.uc.hook_add(UC_HOOK_CODE,decompress,begin=BASE+0xb19b4,end=BASE+0xb19b4)
    return {"native_known_inputs":checks,"guest_blocks":records}
