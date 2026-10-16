"""Probe data5 with the recovered NUtils filename/certificate key derivation.

No JNI environment is fabricated: initializeNative receives the local APK
certificate's toCharsString bytes; the pure loadFile slice supplies AES inputs.
"""
import hashlib
import gzip
import io
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_SP, UC_ARM64_REG_X0, UC_ARM64_REG_X29

from protection_emulate import Experiment, SOURCE, BASE, STACK

LIBRARY_BASE = 0x50000000


def main():
    native = Path("work/protection/nutils_loader_seed1.bin").read_bytes()
    e = Experiment(SOURCE.read_bytes(), 1)
    e.uc.mem_map(LIBRARY_BASE, 0x100000)
    e.uc.mem_write(LIBRARY_BASE, native)

    def call(rva, *args):
        e.uc.reg_write(UC_ARM64_REG_SP, STACK+0xe0000)
        return e.call(LIBRARY_BASE-BASE+rva, *args)

    cert = Path("output/apk/certificates/signer_0_certificate_0.der").read_bytes()
    signature = cert.hex().encode("ascii")
    call(0x1c9f0, e.allocate(len(signature)+1, signature+b"\0"), len(signature))
    constants = bytes(e.uc.mem_read(LIBRARY_BASE+0x56474, 0x3c))
    initialized_magic = struct.unpack_from("<I", constants, 8)[0]
    output = Path("output/native/data_probe")
    output.mkdir(parents=True, exist_ok=True)
    work = Path("work/decoded_candidates")
    work.mkdir(parents=True, exist_ok=True)
    rows = []
    for source in sorted(Path("work/phone_candidates").glob("*.data5")):
        data = source.read_bytes()
        if len(data) < 36 or len(data) % 16:
            raise ValueError(f"{source}: native loadFile requires >=36, multiple of 16")
        # Begin after fread and strlen. All values correspond to actual slice
        # inputs; source path suffix/bytes are supplied explicitly.
        path = ("/guest/"+source.name).encode()
        input_pointer = e.allocate(len(data), data)
        output_pointer = e.allocate(len(data))
        stack = STACK+0x80000
        frame = stack+0x60
        e.uc.reg_write(UC_ARM64_REG_SP, stack)
        e.uc.reg_write(UC_ARM64_REG_X29, frame)
        # Live stack slots established by 23008/2300c before this slice.
        e.uc.mem_write(stack+0x10, struct.pack("<QQ", input_pointer, output_pointer))
        e.uc.mem_write(stack+0x20, bytes(16))
        e.uc.reg_write(UC_ARM64_REG_X0+19, e.allocate(len(data)))
        e.uc.reg_write(UC_ARM64_REG_X0+20, output_pointer)
        e.uc.reg_write(UC_ARM64_REG_X0+22, input_pointer)
        e.uc.reg_write(UC_ARM64_REG_X0+21, len(data))
        e.uc.reg_write(UC_ARM64_REG_X0+23, e.allocate(len(path)+1, path+b"\0"))
        e.uc.reg_write(UC_ARM64_REG_X0, len(path))

        def stop_before_aes(uc, address, size, _):
            e.failure = "STOP_BEFORE_NATIVE_AES"
            uc.emu_stop()

        hook = e.uc.hook_add(UC_HOOK_CODE, stop_before_aes, begin=LIBRARY_BASE+0x232d4, end=LIBRARY_BASE+0x232d4)
        try:
            e.call(LIBRARY_BASE-BASE+0x23014)
            raise ValueError("Key slice unexpectedly returned")
        except ValueError as error:
            if "STOP_BEFORE_NATIVE_AES" not in str(error):
                raise
        finally:
            e.uc.hook_del(hook)
        args = [e.uc.reg_read(UC_ARM64_REG_X0+i) for i in range(6)]
        assert args[1:5] == [128, input_pointer, output_pointer, len(data)]
        key = bytes(e.uc.mem_read(args[0], 16))
        iv = bytes(e.uc.mem_read(args[5], 16))
        # Run actual native AES entry with the slice's actual arguments.
        # Copy keys to heap before resetting the stack for a standalone call.
        key_pointer, iv_pointer = e.allocate(16, key), e.allocate(16, iv)
        try:
            returned = call(0x2e10c, key_pointer, args[1], args[2], args[3], args[4], iv_pointer)
            plaintext = bytes(e.uc.mem_read(output_pointer, len(data)))
            (work/(source.name+".native_aes.bin")).write_bytes(plaintext)
            header = struct.unpack_from("<4I", plaintext)
            payload_length = header[3]
            valid_boundary = header[1] == 20 and payload_length+36 <= len(data)
            payload = plaintext[36:36+payload_length] if valid_boundary else b""
            digest_match = valid_boundary and hashlib.sha1(payload).digest() == plaintext[16:36]
            record = None
            gzip_bytes = None
            if digest_match:
                try:
                    if payload[6:9] != b"\x1f\x8b\x08":
                        raise ValueError("Expected observed gzip at payload+6")
                    with gzip.GzipFile(fileobj=io.BytesIO(payload[6:])) as compressed:
                        decoded = compressed.read(64*1024*1024+1)
                    if len(decoded) > 64*1024*1024:
                        raise ValueError("Decoded size exceeds bound")
                    gzip_bytes = len(decoded)
                    record = json.loads(decoded)
                    (work/(source.name+".payload.bin")).write_bytes(payload)
                    (work/(source.name+".json.raw")).write_bytes(decoded)
                    (output/(source.name+".json")).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                except (ValueError, UnicodeError):
                    pass
            rows.append({"source": str(source), "source_sha256": hashlib.sha256(data).hexdigest(),
                         "key_hex": key.hex(), "iv_hex": iv.hex(), "returned": returned,
                         "header_u32": header, "native_boundary": valid_boundary, "sha1_match": digest_match,
                         "payload_prefix6_hex": payload[:6].hex(), "gzip_decoded_bytes": gzip_bytes,
                         "json_type": type(record).__name__ if record is not None else None,
                         "plaintext_sha256": hashlib.sha256(plaintext).hexdigest()})
        except ValueError as error:
            rows.append({"source": str(source), "error": str(error)})
            break
    result = {"certificate_sha256": hashlib.sha256(cert).hexdigest(), "signature_char_count": len(signature),
              "native_initialize_magic": hex(initialized_magic), "expected_native_magic": "0x8bf8c20d",
              "native_constants_hex": constants.hex(), "files": rows,
              "limits": ["Recovered NUtils image from controlled protection loader, not observed Android startup",
                         "Filename/certificate correspondence validated only if full native header and SHA1 match"]}
    (output/"report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
