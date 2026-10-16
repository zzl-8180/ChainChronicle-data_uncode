"""Recover direct managed-to-native bridge references in decoded modules.

Reports direct BL references only; nearest known parent is explicitly a candidate.
"""
import bisect
import io
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile
from il2cpp_sample_code import Native
from metadata_targets import Metadata


def main():
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    game = Native(m)
    plugin = Native(m,'Assembly-CSharp-firstpass.dll')
    selected = [81737,81741,81794,81833]
    rows = [plugin.method(i) for i in selected]
    targets = {int(r['native_rva'],16):r for r in rows}
    entries = dict(game.method_by_rva)
    for address,indices in plugin.method_by_rva.items():
        entries[address] = entries.get(address,[])+indices
    starts = sorted(a for a in entries if a)
    md = Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    calls = []
    elf = ELFFile(io.BytesIO(Path('work/apk/lib/arm64-v8a/libil2cpp.so').read_bytes()))
    segment = next(s for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_flags'] & 1)
    begin, end = segment['p_vaddr'], segment['p_vaddr']+segment['p_filesz']
    for ordinal,(word,) in enumerate(struct.iter_unpack('<I',game.raw[begin:end])):
        if word & 0xfc000000 != 0x94000000:
            continue
        immediate = word & 0x3ffffff
        if immediate & 0x2000000:
            immediate -= 0x4000000
        address = begin+ordinal*4
        target = address+4*immediate
        if target not in targets:
            continue
        parent = starts[bisect.bisect_right(starts,address)-1]
        context = list(md.disasm(game.raw[address-64:address+32],address-64))
        calls.append({'call_rva':hex(address),'callee':targets[target],
                      'nearest_known_parent_rva':hex(parent),'candidate_parents':[m.method(i) for i in entries[parent]],
                      'context':[f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in context]})
    bridge_names = {}
    for name,address in (('library_name',0x2015e90),('loadFile',0x2074a3f),('InitializeData',0x2074dd1)):
        end = game.raw.index(b'\0',address)
        bridge_names[name] = {'rva':hex(address),'text':game.raw[address:end].decode('utf-8')}
    archive_name = game.literal(0x29b28f0)
    assert archive_name['text']=='chronicle'
    report = {'methods':rows,'calls':calls,'PInvoke_string_arguments':bridge_names,
              'archive_asset_name_usage':archive_name,
              'scope':'Direct BL references in original executable extent; wrapper control flow exported. No complete CFG or actual Java asset-origin claim'}
    output = Path('output/il2cpp/native_paths')
    output.mkdir(exist_ok=True)
    for row in rows:
        start = int(row['native_rva'],16)
        end = min(p for p in plugin.pointers if p>start)
        (output/f"{row['name']}.txt").write_text('\n'.join(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in md.disasm(plugin.raw[start:end],start)),encoding='utf-8')
    for mi in (33682,38816):
        row = game.method(mi)
        start = int(row['native_rva'],16)
        end = min(p for p in game.pointers if p>start)
        (output/f'parent_{mi}.txt').write_text('\n'.join(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in md.disasm(game.raw[start:end],start)),encoding='utf-8')
    Path('output/il2cpp/nativeplugin_paths.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'methods':[(r['name'],r['native_rva']) for r in rows],'references':len(calls),'PInvoke':bridge_names},ensure_ascii=False))


if __name__=='__main__':
    main()
