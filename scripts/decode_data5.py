"""Decode this build's data5 via recovered native loadFile key/AES routines.

Prerequisite: signal_region_probe.py --loader-probe creates the pinned guest image.
No host files or JavaVM are accessible to guest code.
"""
import argparse
import gzip
import hashlib
import io
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_SP, UC_ARM64_REG_X0, UC_ARM64_REG_X29

from apk_certificate import certificates
from protection_emulate import Experiment, SOURCE, BASE, STACK

LIBRARY_BASE = 0x50000000
IMAGE_SHA = "3fd354b5baa099fc97df7ab33de8acd9bfdf1b8048e8a11650379e46ca756444"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_plaintext(plaintext):
    if len(plaintext) < 36:
        raise ValueError("Truncated native envelope")
    header = struct.unpack_from("<4I", plaintext)
    length = header[3]
    if header[1] != 20 or length > len(plaintext)-36:
        raise ValueError("Native envelope digest-size constant or payload boundary invalid")
    payload = plaintext[36:36+length]
    if hashlib.sha1(payload).digest() != plaintext[16:36]:
        raise ValueError("Native payload SHA1 mismatch")
    if len(payload) < 6 or payload[6:9] != b"\x1f\x8b\x08":
        raise ValueError("Observed gzip signature at payload+6 missing")
    with gzip.GzipFile(fileobj=io.BytesIO(payload[6:])) as compressed:
        decoded = compressed.read(64*1024*1024+1)
    if len(decoded) > 64*1024*1024:
        raise ValueError("Decoded JSON exceeds 64 MiB bound")
    record = json.loads(decoded.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(record, dict):
        raise ValueError("Expected observed top-level JSON object")
    return record, payload, decoded, {"header_u32": list(header), "payload_length": length,
                                    "payload_prefix6_hex": payload[:6].hex(), "sha1_match": True,
                                    "gzip_decoded_bytes": len(decoded), "gzip_crc_and_size": "PASS",
                                    "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
                                    "json_raw_sha256": hashlib.sha256(decoded).hexdigest()}


class NativeDecoder:
    def __init__(self, image=Path("work/protection/nutils_loader_seed1.bin"), apk=Path("チェンクロ.apk"),
                 cert_hex=None, protection=None):
        native = Path(image).read_bytes()
        if hashlib.sha256(native).hexdigest() != IMAGE_SHA:
            raise ValueError("Recovered native image differs from verified build")
        if cert_hex is not None:
            # 便携入口：直接使用预提取的 APK 签名证书（公开信息，随每份 APK 分发）
            cert = bytes.fromhex(cert_hex.strip())
        else:
            rows, _ = certificates(Path(apk).read_bytes())
            if len(rows) != 1:
                raise ValueError("Multiple signer/certificate selection requires explicit evidence")
            cert = rows[0]["bytes"]
        signature = cert.hex().encode("ascii")  # Android Signature.toCharsString
        protection = Path(protection).read_bytes() if protection is not None else SOURCE.read_bytes()
        if hashlib.sha256(protection).hexdigest() != "79b6ae193625494b5facbc1c7eafa5bb16c4252dd9050fe10caee2393aa8767c":
            raise ValueError("Protection import/relocation model differs from verified build")
        self.e = Experiment(protection, 1)
        self.e.uc.mem_map(LIBRARY_BASE, 0x100000)
        self.e.uc.mem_write(LIBRARY_BASE, native)
        self.call(0x1c9f0, self.e.allocate(len(signature)+1, signature+b"\0"), len(signature))
        constants = bytes(self.e.uc.mem_read(LIBRARY_BASE+0x56474, 0x3c))
        magic = struct.unpack_from("<I", constants, 8)[0]
        if magic != 0x8bf8c20d:
            raise ValueError("Certificate-derived initialization fails native magic")
        self.provenance = {"native_image_sha256": IMAGE_SHA, "certificate_sha256": hashlib.sha256(cert).hexdigest(),
                           "signature_char_count": len(signature), "native_initialize_magic": hex(magic),
                           "native_constants_hex": constants.hex()}

    def call(self, rva, *args):
        self.e.uc.reg_write(UC_ARM64_REG_SP, STACK+0xe0000)
        return self.e.call(LIBRARY_BASE-BASE+rva, *args)

    def decode(self, data, filename):
        if len(data) < 36 or len(data) % 16:
            raise ValueError("Native loadFile input must be >=36 bytes and multiple of 16")
        if len(data) > 8*1024*1024:
            raise ValueError("Input exceeds bounded guest allocation")
        e = self.e
        path = ("/guest/"+filename).encode("utf-8")
        if b"\0" in path:
            raise ValueError("NUL in filename")
        input_pointer = e.allocate(len(data), data)
        output_pointer = e.allocate(len(data))
        stack, frame = STACK+0x80000, STACK+0x80060
        e.uc.reg_write(UC_ARM64_REG_SP, stack)
        e.uc.reg_write(UC_ARM64_REG_X29, frame)
        e.uc.mem_write(stack+0x10, struct.pack("<QQ", input_pointer, output_pointer))
        e.uc.mem_write(stack+0x20, bytes(16))
        for i, value in {19: output_pointer,20: output_pointer,21: len(data),22: input_pointer,
                         23: e.allocate(len(path)+1, path+b"\0"),0: len(path)}.items():
            e.uc.reg_write(UC_ARM64_REG_X0+i, value)

        def stop(uc, address, size, unused):
            e.failure = "STOP_BEFORE_NATIVE_AES"
            uc.emu_stop()

        hook = e.uc.hook_add(UC_HOOK_CODE, stop, begin=LIBRARY_BASE+0x232d4, end=LIBRARY_BASE+0x232d4)
        try:
            e.call(LIBRARY_BASE-BASE+0x23014)
            raise ValueError("Key slice unexpectedly returned")
        except ValueError as error:
            if "STOP_BEFORE_NATIVE_AES" not in str(error):
                raise
        finally:
            e.uc.hook_del(hook)
        args = [e.uc.reg_read(UC_ARM64_REG_X0+i) for i in range(6)]
        if args[1:5] != [128,input_pointer,output_pointer,len(data)]:
            raise ValueError("Native AES slice argument mismatch")
        key = bytes(e.uc.mem_read(args[0], 16))
        iv = bytes(e.uc.mem_read(args[5], 16))
        returned = self.call(0x2e10c, e.allocate(16,key),128,input_pointer,output_pointer,len(data),e.allocate(16,iv))
        if returned != len(data):
            raise ValueError("Native AES length mismatch")
        plaintext = bytes(e.uc.mem_read(output_pointer, len(data)))
        record, payload, decoded, meta = parse_plaintext(plaintext)
        meta.update({"filename": filename, "source_bytes": len(data), "source_sha256": hashlib.sha256(data).hexdigest(),
                     "key_hex": key.hex(), "iv_hex": iv.hex(), "returned": returned,
                     "native_cipher_symbol": "c_AES__DecryptN_CSTM", "native_cipher_rva": "0x2e10c"})
        return {"record": record,"payload": payload,"json_raw": decoded,"plaintext": plaintext,"meta": meta}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("work/phone_candidates"))
    parser.add_argument("--output", type=Path, default=Path("output/decoded"))
    parser.add_argument("--apk", type=Path, default=Path("チェンクロ.apk"),
                        help="compatible APK supplying the signing certificate (default: repo-root name)")
    args = parser.parse_args()
    sources = sorted(args.input.glob("*.data5")) if args.input.is_dir() else [args.input]
    if not sources:
        raise ValueError("No data5 input")
    args.output.mkdir(parents=True, exist_ok=True)
    decoder, reports = NativeDecoder(apk=args.apk), []
    for source in sources:
        decoded = decoder.decode(source.read_bytes(), source.name)
        (args.output/(source.name+".json")).write_text(json.dumps(decoded["record"],ensure_ascii=False,indent=2),encoding="utf-8")
        (args.output/(source.name+".json.raw")).write_bytes(decoded["json_raw"])
        reports.append(decoded["meta"] | {"source": str(source),"json_type": "dict"})
    report = decoder.provenance | {"files": reports,"status": "PASS",
                                  "scope": "This APK/cache snapshot; decoded records are not all game records"}
    (args.output/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"status": "PASS","files": len(reports),"decoded_json_bytes": sum(r["gzip_decoded_bytes"] for r in reports)}))


if __name__ == "__main__":
    main()
