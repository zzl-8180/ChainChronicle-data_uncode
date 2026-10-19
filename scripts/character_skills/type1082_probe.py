"""Small read-only metadata/native locator for the bounded type1082 question."""
import argparse
import bisect
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from il2cpp_sample_code import Native
from metadata_targets import Metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--find')
    parser.add_argument('--dis', nargs=2, type=lambda x: int(x, 0))
    parser.add_argument('--xref', type=lambda x: int(x, 0))
    parser.add_argument('--brief', action='store_true')
    parser.add_argument('--library', default='Assembly-CSharp.dll')
    args = parser.parse_args()
    md = Metadata(ROOT/'work/protection/metadata_aei_decoded.bin')
    native = Native(md, args.library)
    starts = sorted(x for x in native.method_by_rva if x)
    def methods(address):
        return [native.method(i) for i in native.method_by_rva.get(address, [])]
    def owner(address):
        at = bisect.bisect_right(starts, address)-1
        return dict(start=hex(starts[at]), methods=methods(starts[at])) if at >= 0 else None
    if args.find:
        pattern = re.compile(args.find, re.I)
        results = []
        for ti, typ in enumerate(md.types):
            if md.type_images[ti] != args.library:
                continue
            name = md.string(typ[0])
            matched = [native.method(i) for i in range(typ[9], typ[9]+typ[16])
                       if pattern.search(name+'.'+md.string(md.methods[i][0]))]
            fields = [x for x in native.fields(ti) if pattern.search(name+'.'+x['name'])]
            if matched or fields:
                results.append(dict(type=name, index=ti, fields=fields, methods=matched))
        print(json.dumps(results, ensure_ascii=False, indent=2))
    if args.dis:
        rows = []
        for ins in Cs(CS_ARCH_ARM64, CS_MODE_ARM).disasm(native.raw[args.dis[0]:args.dis[1]], args.dis[0]):
            row = dict(rva=hex(ins.address), bytes=ins.bytes.hex(), op=ins.mnemonic+' '+ins.op_str)
            if ins.mnemonic in ('b', 'bl'):
                target = int(ins.op_str.removeprefix('#'), 16)
                if methods(target):
                    row['calls'] = [m['declaring_type']+'.'+m['name'] for m in methods(target)]
            rows.append(row)
        if args.brief:
            for row in rows:
                print(row['rva'], row['bytes'], row['op'], ','.join(row.get('calls', [])))
        else:
            print(json.dumps(dict(owner=owner(args.dis[0]), instructions=rows), ensure_ascii=False, indent=2))
    if args.xref:
        rows = []
        for pos in range(0, len(native.raw)-3, 4):
            word = struct.unpack_from('<I', native.raw, pos)[0]
            if word & 0x7c000000 == 0x14000000:
                imm = word & 0x3ffffff
                if imm & 0x2000000:
                    imm -= 0x4000000
                if pos + imm*4 == args.xref:
                    rows.append(dict(rva=hex(pos), bytes=native.raw[pos:pos+4].hex(),
                                     branch='bl' if word & 0x80000000 else 'b', owner=owner(pos)))
        print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
