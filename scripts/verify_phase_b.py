"""Verify acquisition evidence and bounded trial arithmetic with synthetic positives."""
import hashlib
import json
import struct
from pathlib import Path

from bounded_decode import byte_table, json_prefix, rol32, word_transform


def main():
    payload = json.dumps({"synthetic_fixture": "known", "unknown_field": None}).encode("utf-8")
    bits, key = 3, 0x57
    encoded = bytes((((value ^ key) << bits) | ((value ^ key) >> (8-bits))) & 255 for value in payload)
    decoded = encoded.translate(byte_table(bits, key))
    assert decoded == payload and json_prefix(decoded[:64])
    assert json.loads(decoded)["unknown_field"] is None
    aligned = payload + b" " * ((-len(payload)) % 4)
    encoded_words = b"".join(rol32(value, 27).to_bytes(4, "little") for (value,) in struct.iter_unpack("<I", aligned))
    assert word_transform(encoded_words, 5, False) == aligned
    assert word_transform(word_transform(aligned, 0, True), 0, True) == aligned
    acquired = json.loads(Path("output/phone/collected_files.json").read_text(encoding="utf-8"))
    for row in acquired:
        raw = Path(row["local"]).read_bytes()
        assert len(raw) == row["bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["sha256_local"]
    trials = json.loads(Path("output/phone/bounded_trials/report.json").read_text(encoding="utf-8"))
    assert trials["total_hypotheses"] == 46464 and len(trials["inputs"]) == 11
    result = {"status": "PASS", "acquired_files_unchanged": len(acquired),
              "synthetic_byte_rotation_xor_roundtrip": True, "synthetic_word_rotation_byte_order_roundtrip": True,
              "null_preserved_in_synthetic_fixture": True,
              "real_structured_hits": len(trials["structured_hits"]), "real_skill_semantics_verified": False}
    Path("output/validation/phase_b_checks.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
