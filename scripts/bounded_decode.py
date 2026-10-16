"""Bounded weak-transform hypotheses, not AES key brute force or a game decoder.

Only accept complete JSON dictionaries/lists. Rejected hypotheses are preserved.
No field semantics or table identity are inferred from this test.
"""
import codecs
import hashlib
import json
import struct
from pathlib import Path


def json_prefix(raw):
    clean = raw.lstrip(b" \r\n\t")
    if not clean.startswith((b"{", b"[", b"\xef\xbb\xbf{", b"\xef\xbb\xbf[", b"\xff\xfe", b"\xfe\xff")):
        return False
    try:
        encoding = "utf-16" if clean.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        codecs.getincrementaldecoder(encoding)().decode(clean, final=False)
        return True
    except UnicodeError:
        return False


def rol32(value, bits):
    return ((value << bits) | (value >> ((32-bits) % 32))) & 0xffffffff


def byte_table(bits, key):
    return bytes((((value >> bits) | (value << ((8-bits) % 8))) & 255) ^ key for value in range(256))


def word_transform(raw, bits, swap):
    result = bytearray()
    for (value,) in struct.iter_unpack("<I", raw):
        result.extend(rol32(value, bits).to_bytes(4, "big" if swap else "little"))
    return bytes(result)


def main():
    rows = json.loads(Path("output/phone/cache_formats.json").read_text(encoding="utf-8"))
    output = Path("output/phone/bounded_trials")
    output.mkdir(parents=True, exist_ok=True)
    results, hits = [], []
    for row in rows:
        source = Path(row["work_file"])
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["source_sha256"]:
            raise ValueError("Work input does not match acquired bytes")
        tested, prefixes = 0, 0

        def validate(data, hypothesis):
            nonlocal prefixes
            prefixes += 1
            try:
                parsed = json.loads(data)
            except (ValueError, UnicodeError):
                return
            if not isinstance(parsed, (dict, list)):
                return
            hit = {"source": row["source_file"], "source_sha256": row["source_sha256"],
                   "hypothesis": hypothesis, "json_type": type(parsed).__name__, "count": len(parsed),
                   "status": "STRUCTURE_ONLY; loading-route and semantics unconfirmed"}
            dest = output / f"{source.name}_{len(hits)}.json"
            dest.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
            hit["output"] = dest.as_posix()
            hits.append(hit)

        for offset in (0, 16):
            payload = raw[offset:]
            prefix = payload[:64]
            for bits in range(8):
                for key in range(256):
                    tested += 1
                    table = byte_table(bits, key)
                    candidate = prefix.translate(table)
                    if json_prefix(candidate):
                        validate(payload.translate(table), {"family": "byte_rotate_then_single_byte_xor",
                                                            "rotate_right": bits, "xor": key, "offset": offset})
            if len(payload) % 4 == 0:
                for bits in range(32):
                    for swap in (False, True):
                        tested += 1
                        candidate = word_transform(prefix, bits, swap)
                        if json_prefix(candidate):
                            validate(word_transform(payload, bits, swap),
                                     {"family": "word_rotate_and_byte_order", "rotate_left": bits,
                                      "big_endian_output": swap, "offset": offset})
        results.append({"name": source.name, "tested_hypotheses": tested,
                        "plausible_prefixes_full_json_tested": prefixes})
    report = {"families": ["single-byte XOR and byte rotation", "32-bit rotation and byte order"],
              "offset_hypotheses": [0, 16], "inputs": results, "structured_hits": hits,
              "total_hypotheses": sum(r["tested_hypotheses"] for r in results),
              "aes_keys_tested": 0,
              "limits": "No complete JSON dict/list found for these simple families at offsets 0/16; does not rule out other output formats/compression, identify encryption, prove impossibility, or cover repeating multi-byte keys"}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"inputs": len(results), "hypotheses": report["total_hypotheses"], "structured_hits": len(hits)}))


if __name__ == "__main__":
    main()
