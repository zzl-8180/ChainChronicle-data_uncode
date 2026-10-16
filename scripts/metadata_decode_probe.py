"""Execute recovered AEI conversion on existing metadata, preserve original."""
import hashlib
import argparse
import json
import struct
from pathlib import Path

from jni_prefix_probe import prepare_experiment
from protection_emulate import STACK
from metadata_targets import Metadata
from unicorn.arm64_const import UC_ARM64_REG_SP


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--accelerate-lz4',action='store_true')
    args = parser.parse_args()
    source = Path("work/apk/assets/bin/Data/Managed/Metadata/global-metadata.dat")
    raw = source.read_bytes()
    assert raw[:3] == b"AEI"
    e, _, preparatory = prepare_experiment(heap_size=0x4000000)
    lz4_model = None
    if args.accelerate_lz4:
        from guest_lz4 import install
        lz4_model = install(e)
    address = e.allocate(len(raw),raw)
    e.uc.reg_write(UC_ARM64_REG_SP,STACK+0x90000)
    steps = []
    try:
        returned = e.call(0xf3ed8,address,len(raw),0,instruction_limit=100000000)
        steps.append({"status":"RETURNED","value":hex(returned)})
    except ValueError as error:
        steps.append({"status":"STOPPED","reason":str(error)})
    for index in range(6):
        if "Execution limit" not in steps[-1].get("reason",""):
            break
        try:
            returned = e.resume()
            steps.append({"status":"RETURNED","value":hex(returned)})
        except ValueError as error:
            steps.append({"status":"STOPPED","reason":str(error)})
    decoded = bytes(e.uc.mem_read(address,len(raw)))
    if steps[-1] != {'status':'RETURNED','value':'0x0'}:
        raise ValueError(f'AEI conversion did not finish: {steps[-1]}')
    metadata = Metadata(decoded)
    if source.read_bytes()!=raw:
        raise ValueError('Source changed during conversion')
    output = Path("output/il2cpp")
    output.mkdir(parents=True,exist_ok=True)
    Path("work/protection/metadata_aei_decoded.bin").write_bytes(decoded)
    result = {"source":str(source),"source_sha256":hashlib.sha256(raw).hexdigest(),
              "AEI_header_fields_u32_at_3_7_11":list(struct.unpack_from("<III",raw,3)),
              "preparatory":preparatory,"entry_rva":"0xf3ed8","mode":0,"steps":steps,
              "changed_bytes":sum(a!=b for a,b in zip(raw,decoded)),"result_head_hex":decoded[:64].hex(),
              "decoded_sha256":hashlib.sha256(decoded).hexdigest(),
              "schema_validation":"PASS: v31 full section boundaries, core strides, type/method ownership and referenced names",
              "counts":{"types":len(metadata.types),"methods":len(metadata.methods),"fields":len(metadata.fields)},
              "optional_lz4_model":lz4_model,
              "standard_metadata_magic_offsets":[hex(i) for i in range(len(decoded)-4) if decoded[i:i+4]==bytes.fromhex("af1bb1fa")][:10],
              "limits":["Controlled native conversion, not normal Android file hook observation",
                        "Native metadata transform proven; normal Android file hook not executed"]}
    (output/"metadata_aei_probe.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    variant = 'lz4_model' if args.accelerate_lz4 else 'native'
    (output/f"metadata_aei_probe_{variant}.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!='preparatory'},indent=2))


if __name__ == "__main__":
    main()
