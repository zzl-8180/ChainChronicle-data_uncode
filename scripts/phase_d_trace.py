"""Export only requested method bodies/calls for phase D sample investigation."""
import argparse
import bisect
import hashlib
import json
import re
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from il2cpp_sample_code import Native
from metadata_targets import Metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('methods',nargs='+',type=int)
    parser.add_argument('--callers',action='store_true')
    args = parser.parse_args()
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    n = Native(m)
    md = Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    out = Path('output/phase_d/code')
    out.mkdir(parents=True,exist_ok=True)
    report = []
    for index in args.methods:
        row = n.method(index)
        start = int(row['native_rva'],16)
        end = min(p for p in n.pointers if p>start)
        insns = list(md.disasm(n.raw[start:end],start))
        if sum(i.size for i in insns)!=end-start:
            raise ValueError('Undecodable method body')
        row['calls'] = []
        lines = []
        for i in insns:
            annotation = ''
            if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):
                target = int(i.op_str[1:],16)
                callees = [n.method(ci) for ci in n.method_by_rva.get(target,[])]
                row['calls'].append({'instruction_rva':hex(i.address),'target_rva':hex(target),'callees':callees})
                annotation = ' ; '+', '.join(f"{c['declaring_type']}.{c['name']} [{c['index']}]" for c in callees) if callees else ''
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}'+annotation)
        row['end_next_known_method'] = hex(end)
        row['native_image_sha256'] = hashlib.sha256(n.raw).hexdigest()
        row['metadata_sha256'] = hashlib.sha256(m.raw).hexdigest()
        stem = re.sub(r'[<>:"/\\|?*]', '_',f'{index}_{row["declaring_type"]}_{row["name"]}')
        (out/(stem+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
        (out/(stem+'.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
        report.append({'index':index,'type':row['declaring_type'],'name':row['name'],'start':hex(start),'bytes':end-start})
    print(json.dumps(report,ensure_ascii=False))
    if args.callers:
        targets = {int(n.method(mi)['native_rva'],16):mi for mi in args.methods}
        starts = sorted(k for k in n.method_by_rva if k)
        refs = []
        for ordinal,(word,) in enumerate(struct.iter_unpack('<I',n.raw[:0x28a079c])):
            if word & 0xfc000000 != 0x94000000:
                continue
            immediate = word & 0x3ffffff
            if immediate & 0x2000000:
                immediate -= 0x4000000
            address = ordinal*4
            target = address+immediate*4
            if target not in targets:
                continue
            parent = starts[bisect.bisect_right(starts,address)-1]
            refs.append({'call_rva':hex(address),'target_method':targets[target],
                         'candidate_parents':[n.method(i) for i in n.method_by_rva[parent]],
                         'scope':'Direct BL; nearest known game method candidate, verify exported body'})
        (out.parent/('callers_'+ '_'.join(map(str,args.methods))+'.json')).write_text(json.dumps(refs,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps([{'call':r['call_rva'],'target':r['target_method'],
                           'parent_indices':[p['index'] for p in r['candidate_parents']]} for r in refs]))


if __name__=='__main__':
    main()
