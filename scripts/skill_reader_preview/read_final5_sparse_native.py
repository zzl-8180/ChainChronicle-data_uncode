"""Bounded native/metadata read. Owns only work/reader_final5_sparse outputs."""
import bisect
import hashlib
import json
import re
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'output/character_skills/reader_full_20261106/audit/final5_evidence_20261107/native/sparse'
HERE.mkdir(parents=True,exist_ok=True)
sys.path.insert(0, str(ROOT / 'scripts'))
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

if __name__ == '__main__':
    m = Metadata(ROOT / 'work/protection/metadata_aei_decoded.bin')
    n = Native(m)
    starts = sorted(n.method_by_rva)
    cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    chosen = [int(i) for i in sys.argv[1:]]
    records = []
    for index in chosen:
        row = n.method(index)
        start = int(row['native_rva'], 16)
        end = starts[bisect.bisect_right(starts, start)]
        lines = []
        for i in cs.disasm(n.raw[start:end], start):
            label = ''
            if i.mnemonic in ('bl', 'b') and i.op_str.startswith('#0x'):
                label = ' ; ' + ' / '.join(n.method(mi)['declaring_type'] + '.' + n.method(mi)['name']
                    for mi in n.method_by_rva.get(int(i.op_str[1:], 16), []))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{label}')
        filename = re.sub(r'[<>:"/\\|?*]', '_',
                          f'{index}_{row["declaring_type"]}_{row["name"]}.txt')
        path = HERE / filename
        path.write_text('\n'.join(lines), encoding='utf-8')
        records.append({**row, 'file': path.relative_to(ROOT).as_posix(),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (HERE / ('methods_' + '_'.join(map(str, chosen)) + '.json')).write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print([(r['index'], r['name'], r['native_rva']) for r in records])
