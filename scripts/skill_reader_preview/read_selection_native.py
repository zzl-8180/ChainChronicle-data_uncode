"""Bounded read of existing recovered image; no emulation or game mutation."""
import bisect
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

HERE = ROOT / 'output/character_skills/reader_full_20261106/audit/selection_order_20261107/native'
HERE.mkdir(parents=True, exist_ok=True)
m = Metadata(ROOT / 'work/protection/metadata_aei_decoded.bin')
n = Native(m)
dis = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
starts = sorted(n.method_by_rva)


def dump(index):
    method = n.method(index)
    start = int(method['native_rva'], 16)
    end = starts[bisect.bisect_right(starts, start)]
    lines = []
    for i in dis.disasm(n.raw[start:end], start):
        label = ''
        if i.mnemonic in ('bl', 'b') and i.op_str.startswith('#0x'):
            target = int(i.op_str[1:], 16)
            label = '; ' + ' / '.join(
                n.method(mi)['declaring_type'] + '.' + n.method(mi)['name']
                for mi in n.method_by_rva.get(target, []))
        lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str} {label}'.rstrip())
    (HERE / f'{index}_{method["declaring_type"]}_{method["name"]}.txt').write_text(
        '\n'.join(lines), encoding='utf-8')
    return method


if __name__ == '__main__':
    chosen = [int(x) for x in sys.argv[1:]] or [4927, 4928, 4925, 4932, 8233, 8234, 8237, 8266, 7894]
    methods = [dump(index) for index in chosen]
    targets = {0x100a0f0, 0x1008d40, 0x1244ce4}
    refs = []
    # Scan only the already mapped game code span for direct BL references.
    for off, (word,) in enumerate(struct.iter_unpack('<I', n.raw[0x880000:0x1f00000])):
        if word & 0xfc000000 != 0x94000000:
            continue
        pc = 0x880000 + off * 4
        imm = word & 0x3ffffff
        if imm & 0x2000000:
            imm -= 0x4000000
        target = pc + imm * 4
        if target not in targets:
            continue
        start = starts[bisect.bisect_right(starts, pc) - 1]
        refs.append({'call_rva': hex(pc), 'target': hex(target),
                     'callers': [n.method(mi) for mi in n.method_by_rva[start]]})
    (HERE / 'direct_callers.json').write_text(json.dumps(refs, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'methods': [(x['index'], x['declaring_type'], x['name']) for x in methods],
                      'callers': [(r['call_rva'], r['target'], [(c['index'], c['declaring_type'], c['name']) for c in r['callers']]) for r in refs]}, ensure_ascii=False))
