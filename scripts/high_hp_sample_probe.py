"""Execute actual HighHPAll comparison/switch/loop on selected real records.

Explicit input model: filtered membership is supplied; ParamS_float.get_Value
returns the integrity-checked JSON value as float32. Its engine icall, Unity,
list construction, initialization and battle damage are outside this experiment.
"""
import hashlib
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import (UC_ARM64_REG_X0, UC_ARM64_REG_X20,
                                UC_ARM64_REG_X21, UC_ARM64_REG_X22,
                                UC_ARM64_REG_X24, UC_ARM64_REG_X30,
                                UC_ARM64_REG_S0, UC_ARM64_REG_S8,
                                UC_ARM64_REG_SP, UC_ARM64_REG_PC)

BASE, HEAP, STACK = 0x50000000, 0x10000000, 0x20000000


def bits(value):
    return struct.unpack('<I',struct.pack('<f',value))[0]


def number(value):
    return struct.unpack('<f',struct.pack('<I',value))[0]


def probe(image, records, hp_bits, apply_type):
    uc = Uc(UC_ARCH_ARM64,UC_MODE_ARM)
    uc.mem_map(BASE,(len(image)+4095)&~4095)
    uc.mem_write(BASE,image)
    uc.mem_map(HEAP,0x10000)
    uc.mem_map(STACK,0x10000)
    bp, array, indices = HEAP,HEAP+0x1000,HEAP+0x2000
    uc.mem_write(bp+0x1e0,struct.pack('<Q',array))
    uc.mem_write(array+0x18,struct.pack('<Q',len(records)))
    uc.mem_write(indices,bytes(range(len(records))))
    wrappers = {}
    for ri, row in enumerate(records):
        skill = HEAP+0x3000+ri*0x1000
        uc.mem_write(array+0x20+ri*8,struct.pack('<Q',skill))
        for pi in range(6):
            if f'param{pi}' not in row:
                continue
            wrapper = skill+0x100+pi*0x20
            uc.mem_write(skill+0x30+pi*8,struct.pack('<Q',wrapper))
            value_bits = bits(row[f'param{pi}'])
            wrappers[wrapper] = (row['skillid'], f'param{pi}', value_bits)
    uc.reg_write(UC_ARM64_REG_SP,STACK+0xf000)
    uc.reg_write(UC_ARM64_REG_X20,bp)
    uc.reg_write(UC_ARM64_REG_X21,apply_type)
    uc.reg_write(UC_ARM64_REG_X22,indices)
    uc.reg_write(UC_ARM64_REG_X24,len(records))
    uc.reg_write(UC_ARM64_REG_S0,hp_bits)
    uc.reg_write(UC_ARM64_REG_S8,bits(1.0 if apply_type<3 else 0.0))
    allowed = [(0x1593418,0x15934d4),(0x1593594,0x1593594),
               (0x1dbcf24,0x1dbcf2c),(0x1dbcf3c,0x1dbcf44),
               (0x1dbcf54,0x1dbcf5c),(0x1dbcf6c,0x1dbcf74),
               (0x1dbcf84,0x1dbcf8c),(0x1dbcf9c,0x1dbcfb0)]
    reads, failures, completed = [], [], []
    def hook(cpu,address,size,unused):
        rva = address-BASE
        if rva==0x1593594:
            completed.append(True)
            cpu.emu_stop()
        elif rva==0xa92830:
            pointer = cpu.reg_read(UC_ARM64_REG_X0)
            if pointer not in wrappers:
                failures.append('Unknown parameter object')
                cpu.emu_stop()
                return
            sid, field, value_bits = wrappers[pointer]
            reads.append({'skill_id':sid,'field':field,'float32_bits':hex(value_bits)})
            cpu.reg_write(UC_ARM64_REG_S0,value_bits)
            cpu.reg_write(UC_ARM64_REG_PC,cpu.reg_read(UC_ARM64_REG_X30))
        elif not any(lo<=rva<=hi for lo,hi in allowed):
            failures.append(f'Outside declared native slice: {hex(rva)}')
            cpu.emu_stop()
    uc.hook_add(UC_HOOK_CODE,hook)
    uc.emu_start(BASE+0x1593418,BASE+len(image),timeout=1000000,count=10000)
    if failures or not completed:
        raise ValueError(failures or 'Native slice did not complete')
    actual = uc.reg_read(UC_ARM64_REG_S8)
    expected = 1.0 if apply_type<3 else 0.0
    field = ('param1','param2','param3','param4','param5')[apply_type]
    for row in records:
        if number(hp_bits)>=number(bits(row['param0'])):
            value = number(bits(row[field]))
            expected = number(bits(expected*value if apply_type<3 else expected+value))
    if actual != bits(expected):
        raise ValueError(f'Native comparison/aggregation differs: {number(actual)} vs {expected}')
    return {'hp_float32':number(hp_bits),'hp_bits':hex(hp_bits),'apply_type':apply_type,
            'parameter_field':field,'output':number(actual),'output_bits':hex(actual),
            'native_parameter_reads':reads,'expected_matches':'PASS'}


def main():
    image = Path('work/protection/il2cpp_loader_seed1.bin').read_bytes()
    sample = json.loads(Path('output/sample/sample.json').read_text(encoding='utf-8'))
    records = [sample['skill_raw'],sample['subskills_raw'][0]]
    assert all(r['ability']==1105 for r in records)
    hp_values = [bits(0),bits(0.25)-1,bits(0.25),bits(0.25)+1,
                 bits(0.5)-1,bits(0.5),bits(0.5)+1,bits(1.0)]
    # These records omit param4; do not invent a critical-rate default.
    cases = [probe(image,records,hp,apply_type) for hp in hp_values for apply_type in (0,1,2,4)]
    result = {'status':'PASS','native_image_sha256':hashlib.sha256(image).hexdigest(),
              'skill_ids':[r['skillid'] for r in records],'entry_rva':'0x1593418','stop_rva':'0x1593594',
              'model':'Known filtered membership and plaintext float32 parameter getter supplied; actual recovered ARM64 comparison, switch, multiplication/addition and loop execute unchanged',
              'limits':['Does not run ParamS_float engine icall or normal game initialization',
                        'Filtered skill eligibility/subskill installation not demonstrated by this slice',
                        'Local loop outputs are not final game damage or whole-party stacked effects',
                        'HP ratio computation verified statically separately; ratio is an input here'],
              'case_count':len(cases),'cases':cases}
    Path('output/validation/high_hp_sample.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'case_count':len(cases),'limits':result['limits']}))


if __name__=='__main__':
    main()
