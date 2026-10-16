"""Meaningful checks of actual decoded files and rejection boundaries."""
import hashlib
import json
import zipfile
from pathlib import Path

from asn1crypto import cms

from apk_certificate import certificates
from decode_data5 import NativeDecoder, parse_plaintext
from sample_trace import locate_record


def main():
    apk = Path("チェンクロ.apk").read_bytes()
    rows, _ = certificates(apk)
    with zipfile.ZipFile("チェンクロ.apk") as archive:
        v1 = cms.ContentInfo.load(archive.read("META-INF/CERT.RSA"))
    v1_certs = [cert.chosen.dump() for cert in v1["content"]["certificates"]]
    assert rows[0]["bytes"] in v1_certs, "APK v1/v2 certificate mismatch"
    try:
        certificates(apk[:-1])
        raise AssertionError("Truncated APK accepted")
    except ValueError:
        pass
    decoder = NativeDecoder()
    # Independent NIST standard CBC vector checks the native AES primitive.
    # data5 itself calls c_AES__DecryptN_CSTM, not standard CBC decryption.
    key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
    iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    cipher = bytes.fromhex("7649abac8119b246cee98e9b12e9197d5086cb9b507219ee95db113a917678b273bed6b8e3c1743b7116e69e222295163ff1caa1681fac09120eca307586e1a7")
    expected = bytes.fromhex("6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e5130c81c46a35ce411e5fbc1191a0a52eff69f2445df4f9b17ad2b417be66c3710")
    e = decoder.e
    destination = e.allocate(len(cipher)+16)
    assert decoder.call(0x2de9c,e.allocate(16,key),128,e.allocate(len(expected),expected),destination,len(expected),e.allocate(16,iv)) == len(cipher)+16
    assert bytes(e.uc.mem_read(destination,len(cipher))) == cipher
    for size in (16,32,272):
        plain = bytes(i & 255 for i in range(size))
        encrypted,decoded = e.allocate(size),e.allocate(size)
        assert decoder.call(0x2dfd4,e.allocate(16,key),128,e.allocate(size,plain),encrypted,size,e.allocate(16,iv)) == size
        assert decoder.call(0x2e10c,e.allocate(16,key),128,encrypted,decoded,size,e.allocate(16,iv)) == size
        assert bytes(e.uc.mem_read(decoded,size)) == plain
    checks = ["Independent NIST four-block CBC known answer via native CBC encrypt primitive",
              "Actual CSTM encrypt/decrypt roundtrip for 16/32/272 bytes (not labeled CBC)", "APK v1 and v2 DER certificate bytes identical",
              "Truncated APK signing container rejected"]
    before = {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in
              [Path("チェンクロ.apk"),Path("work/apk/lib/arm64-v8a/libChronicleNUtils.so")] + list(Path("work/phone_candidates").glob("*.data5"))}
    for name in ("charainfo.data5","skilllist.data5"):
        source = Path("work/phone_candidates")/name
        data = source.read_bytes()
        first = decoder.decode(data,name)
        second = decoder.decode(data,name)
        assert first["json_raw"] == second["json_raw"] == (Path("output/decoded")/(name+".json.raw")).read_bytes()
        assert first["meta"] == second["meta"]
        assert first["record"] == second["record"]
        checks.append(f"{name}: repeat exact plaintext/JSON/key/IV; full SHA1/gzip CRC/JSON boundaries")
        damaged = bytearray(data)
        damaged[len(damaged)//2] ^= 1
        cases = [(data[:-1],name,"1-byte truncation"),(data[:-16],name,"aligned truncation"),
                 (bytes(damaged),name,"ciphertext bit flip"),(data,name+"x","wrong filename")]
        for bad,filename,label in cases:
            try:
                decoder.decode(bad,filename)
                raise AssertionError(f"{name}: {label} accepted")
            except (ValueError,EOFError,OSError):
                checks.append(f"{name}: {label} rejected")
        # Recompute outer hash after truncating gzip, so the gzip-boundary check
        # is exercised independently instead of only the outer SHA1 check.
        payload = first["payload"][:-1]
        forged = bytearray(first["plaintext"])
        forged[12:16] = len(payload).to_bytes(4,"little")
        forged[16:36] = hashlib.sha1(payload).digest()
        forged[36:36+len(payload)] = payload
        try:
            parse_plaintext(bytes(forged))
            raise AssertionError("Truncated gzip accepted")
        except (ValueError,EOFError,OSError):
            checks.append(f"{name}: truncated gzip with valid outer SHA1 rejected")
    sample = json.loads(Path("output/sample/sample.json").read_text(encoding="utf-8"))
    for identifier,location in sample["record_locations"].items():
        is_card = identifier == str(sample["card_id"])
        name,array = ("charainfo","charainfo") if is_card else ("skilllist","skilllist")
        raw = Path(f"output/decoded/{name}.data5.json.raw").read_bytes()
        record,found = locate_record(raw,array,location["ordinal_zero_based"])
        assert found == location
        assert record["cid" if is_card else "skillid"] == int(identifier)
    assert sample["card_raw"]["skillid"][2] == sample["skill_raw"]["skillid"]
    assert sample["skill_raw"]["sub"] == [s["skillid"] for s in sample["subskills_raw"]]
    checks.append("Real card/ability/sub links and exact JSON byte spans")
    assert before == {path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in before}
    for row in sample["input_provenance"]:
        assert hashlib.sha256(Path(row["local"]).read_bytes()).hexdigest() == row["sha256_local"]
    checks.append("APK, source library, work inputs and two original collected inputs unchanged")
    assert Path("work/protection/nutils_loader_seed1.bin").read_bytes() == Path("work/protection/nutils_loader_seed2.bin").read_bytes()
    checks.append("Recovered NUtils guest image identical across two seeds")
    result = {"status":"PASS","checks":checks,"complete_sample_chains":1,
              "limits":["Decoder checks do not validate parameter semantics; see separate native code/boundary evidence. No real-device battle confirmation",
                        "No complete cache coverage or full Android initialization claim"]}
    Path("output/validation/data5_checks.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
