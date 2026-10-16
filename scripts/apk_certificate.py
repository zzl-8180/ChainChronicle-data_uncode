"""Read v2 signer certificates with explicit length boundaries, no APK mutation.

This extracts evidence; it does not claim cryptographic APK signature verification.
Format: https://source.android.com/docs/security/features/apksigning/v2
"""
import hashlib
import json
import struct
from pathlib import Path


def lp32(data, offset=0):
    if offset < 0 or offset+4 > len(data):
        raise ValueError("Truncated length prefix")
    length = struct.unpack_from("<I", data, offset)[0]
    end = offset+4+length
    if end > len(data):
        raise ValueError("Length-prefixed field exceeds container")
    return data[offset+4:end], end


def certificates(raw):
    eocd = raw.rfind(b"PK\x05\x06", max(0, len(raw)-65557))
    if eocd < 0 or eocd+22 > len(raw):
        raise ValueError("ZIP EOCD missing")
    comment = struct.unpack_from("<H", raw, eocd+20)[0]
    if eocd+22+comment != len(raw):
        raise ValueError("ZIP EOCD length mismatch")
    central = struct.unpack_from("<I", raw, eocd+16)[0]
    if central < 32 or raw[central-16:central] != b"APK Sig Block 42":
        raise ValueError("APK signing block footer missing")
    size = struct.unpack_from("<Q", raw, central-24)[0]
    start = central-size-8
    if start < 0 or struct.unpack_from("<Q", raw, start)[0] != size:
        raise ValueError("APK signing block sizes disagree")
    offset, limit, rows = start+8, central-24, []
    while offset < limit:
        if offset+12 > limit:
            raise ValueError("Truncated signing pair")
        length, identifier = struct.unpack_from("<QI", raw, offset)
        end = offset+8+length
        if length < 4 or end > limit:
            raise ValueError("Signing pair exceeds block")
        if identifier == 0x7109871a:
            signers, consumed = lp32(raw[offset+12:end])
            if consumed != length-4:
                raise ValueError("Trailing v2 signer bytes")
            pos, signer_index = 0, 0
            while pos < len(signers):
                signer, pos = lp32(signers, pos)
                signed, _ = lp32(signer)
                _, signed_pos = lp32(signed)  # digests
                chain, _ = lp32(signed, signed_pos)
                cp, certificate_index = 0, 0
                while cp < len(chain):
                    cert, cp = lp32(chain, cp)
                    rows.append({"signer_index": signer_index, "certificate_index": certificate_index,
                                 "bytes": cert, "sha256": hashlib.sha256(cert).hexdigest()})
                    certificate_index += 1
                signer_index += 1
        offset = end
    if offset != limit or not rows:
        raise ValueError("No bounded v2 certificates found")
    return rows, {"block_offset": start, "block_size": size+8, "central_directory_offset": central}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", type=Path, default=Path("チェンクロ.apk"),
                        help="compatible APK to read (default: repo-root name)")
    parser.add_argument("--hex", action="store_true",
                        help="include certificate hex in report and stdout (for --cert-hex usage)")
    args = parser.parse_args()
    source = args.apk
    raw = source.read_bytes()
    rows, layout = certificates(raw)
    output = Path("output/apk/certificates")
    output.mkdir(parents=True, exist_ok=True)
    report = []
    for row in rows:
        destination = output/f"signer_{row['signer_index']}_certificate_{row['certificate_index']}.der"
        destination.write_bytes(row["bytes"])
        entry = {k:v for k,v in row.items() if k != "bytes"} | {"size": len(row["bytes"]), "local": str(destination)}
        if args.hex:
            entry["hex"] = row["bytes"].hex()
        report.append(entry)
    (output/"report.json").write_text(json.dumps({"source_sha256": hashlib.sha256(raw).hexdigest(),
                                               "layout": layout, "certificates": report,
                                               "scope": "Extraction only; APK signature not verified"}, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
