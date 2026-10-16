"""Resolve game method tokens/field offsets using recovered native registrations."""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from metadata_targets import Metadata


class Native:
    def __init__(self, metadata, image_name='Assembly-CSharp.dll'):
        self.m = metadata
        self.image_name = image_name
        self.raw = Path('work/protection/il2cpp_loader_seed1.bin').read_bytes()
        name = image_name.encode('utf-8')+b'\0'
        string = self.raw.index(name)
        if self.raw.find(name, string+1) >= 0:
            raise ValueError('Ambiguous game module name')
        refs = self.refs(struct.pack('<Q', string))
        candidates = []
        method_count = sum(1 for r in metadata.methods if metadata.type_images[r[1]]==image_name)
        for ref in refs:
            values = self.unpack('<17Q', ref)
            if values[1] == method_count and values[2]+method_count*8 <= len(self.raw):
                candidates.append((ref, values))
        if len(candidates) != 1:
            raise ValueError('Game codegen module not uniquely validated')
        self.module_rva, values = candidates[0]
        self.method_array = values[2]
        self.pointers = self.unpack(f'<{method_count}Q', self.method_array)
        count = len(metadata.types)
        candidates = []
        for ref in self.refs(struct.pack('<Q', count)):
            if ref < 80:
                continue
            values = self.unpack('<16Q',ref-80)
            if values[10] == values[12] == count and values[11]+count*8 <= len(self.raw) and values[13]+count*8 <= len(self.raw):
                candidates.append((ref-80, values))
        if len(candidates)!=1:
            raise ValueError('Metadata registration not unique')
        self.registration_rva, values = candidates[0]
        self.type_count, self.type_array = values[6:8]
        self.field_array = values[11]
        self.method_by_rva = {}
        for index, row in enumerate(metadata.methods):
            if metadata.type_images[row[1]] != image_name:
                continue
            rid = row[6] & 0xffffff
            if not 1 <= rid <= len(self.pointers):
                raise ValueError('Game method token out of native array')
            address = self.pointers[rid-1]
            if address and (address % 4 or address >= len(self.raw)):
                raise ValueError('Native method pointer boundary')
            self.method_by_rva.setdefault(address, []).append(index)

    def refs(self, pattern):
        pos = 0
        results = []
        while (pos := self.raw.find(pattern, pos)) >= 0:
            if not pos % 8:
                results.append(pos)
            pos += 1
        return results

    def unpack(self, fmt, offset):
        if not 0 <= offset <= len(self.raw)-struct.calcsize(fmt):
            raise ValueError('Native read exceeds image')
        return struct.unpack_from(fmt,self.raw,offset)

    def type_info(self, index):
        if not 0 <= index < self.type_count:
            raise ValueError('Native type index')
        pointer = self.unpack('<Q',self.type_array+index*8)[0]
        data, bits = self.unpack('<QI',pointer)
        return {'index':index, 'rva':hex(pointer),'data':data,'bits':hex(bits),'kind':bits>>16 & 255}

    def fields(self, ti):
        row = self.m.types[ti]
        array = self.unpack('<Q',self.field_array+ti*8)[0]
        return [{'index':row[8]+i,'name':self.m.string(f[0]),'type_index':f[1],
                 'offset':hex(self.unpack('<I',array+i*4)[0])}
                for i,f in enumerate(self.m.fields[row[8]:row[8]+row[18]])]

    def default(self, fi):
        matches = [r for r in self.m.defaults if r[0] == fi]
        if len(matches)!=1 or matches[0][2]<0:
            raise ValueError('Field default missing/ambiguous')
        _, type_index, data_index = matches[0]
        section = self.m.sections['fieldAndParameterDefaultValueData']
        position = section['offset']+data_index
        if not 0 <= data_index < section['size']:
            raise ValueError('Default data index')
        kind = self.type_info(type_index)['kind']
        byte = self.m.raw[position]
        if kind in (4,5):
            value, length = (byte-256 if kind==4 and byte>=128 else byte), 1
        elif kind in (8,9):
            if byte < 128:
                unsigned, length = byte, 1
            elif byte < 192:
                unsigned, length = ((byte & 63)<<8)|self.m.raw[position+1],2
            elif byte < 224:
                unsigned, length = ((byte & 31)<<24)|int.from_bytes(self.m.raw[position+1:position+4],'big'),4
            elif byte == 240:
                unsigned, length = struct.unpack_from('<I',self.m.raw,position+1)[0],5
            elif byte in (254,255):
                unsigned, length = (0xfffffffe if byte==254 else 0xffffffff),1
            else:
                raise ValueError('Unsupported compressed integer prefix')
            value = unsigned if kind==9 else -(unsigned>>1)-1 if unsigned & 1 else unsigned>>1
        else:
            raise ValueError(f'Unsupported default primitive: {kind}')
        if data_index+length > section['size']:
            raise ValueError('Default record boundary')
        return {'field_index':fi, 'type_index':type_index,'primitive_kind':kind,
                'data_index':data_index,'metadata_byte_offset':position,
                'raw_hex':self.m.raw[position:position+length].hex(),'value':value}

    def method(self, index):
        if self.m.type_images[self.m.methods[index][1]]!=self.image_name:
            raise ValueError('Method belongs to another codegen module')
        result = self.m.method(index)
        result['native_rva'] = hex(self.pointers[(self.m.methods[index][6]&0xffffff)-1])
        return result

    def literal(self, slot):
        usage = self.unpack('<Q',slot)[0]
        encoded = self.unpack('<Q',usage)[0]
        if encoded>>29 & 7 != 5:
            raise ValueError('Not an encoded string literal usage')
        index = (encoded & 0x1ffffffe)>>1
        rows = self.m.rows('stringLiteral','<Ii')
        if not 0 <= index < len(rows):
            raise ValueError('Literal index')
        size, offset = rows[index]
        section = self.m.sections['stringLiteralData']
        if not 0 <= offset <= offset+size <= section['size']:
            raise ValueError('Literal boundary')
        name = self.m.raw[section['offset']+offset:section['offset']+offset+size].decode('utf-8')
        return {'slot_rva':hex(slot),'usage_rva':hex(usage),'encoded':hex(encoded),
                'literal_index':index,'text':name}


def main():
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    n = Native(m)
    md = Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    methods = []
    out = Path('output/il2cpp/sample_code')
    out.mkdir(exist_ok=True)
    for index in (8886,3849,4175,38581,38583,38585,38587,38589,38591,38652):
        row = n.method(index)
        start = int(row['native_rva'],16)
        end = min(p for p in n.pointers if p>start)
        insns = list(md.disasm(n.raw[start:end],start))
        if sum(i.size for i in insns)!=end-start:
            raise ValueError('Method contains undecodable bytes')
        calls = []
        for insn in insns:
            if insn.mnemonic in ('bl','b') and insn.op_str.startswith('#0x'):
                target = int(insn.op_str[1:],16)
                for mi in n.method_by_rva.get(target,[]):
                    calls.append({'instruction_rva':hex(insn.address),'callee':n.method(mi)})
        row.update({'next_known_method_rva':hex(end),'calls':calls,
                    'boundary_limit':'Next native method entry; exceptional tail may follow final RET'})
        filename = f"{row['declaring_type']}_{row['name']}.txt"
        (out/filename).write_text('\n'.join(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in insns),encoding='utf-8')
        methods.append(row)
    enums = {}
    for ti in (718,725):
        enums[m.string(m.types[ti][0])] = {f['name']:n.default(f['index']) for f in n.fields(ti) if f['name']!='value__'}
    assert enums['ABILITY_TYPE']['HighHPAll']['value']==1105
    assert [enums['AbilityApplyType'][s]['value'] for s in ('Attack','Move','Defence','CriRate','CriDmg','AttackFlag')]==list(range(6))
    jump = list(n.raw[0x207426b:0x2074271])
    branch_addresses = [hex(0x1593474+4*x) for x in jump]
    json_keys = [n.literal(slot) for slot in (0x29d0c78,0x29f69c8,0x29b08c0,0x29b1970,0x29f0ae8,0x29f0e50)]
    assert [r['text'] for r in json_keys]==[f'param{i}' for i in range(6)]
    report = {'native_image_sha256':hashlib.sha256(n.raw).hexdigest(),
              'metadata_sha256':hashlib.sha256(m.raw).hexdigest(),
              'game_module_rva':hex(n.module_rva),'method_pointer_array_rva':hex(n.method_array),
              'metadata_registration_rva':hex(n.registration_rva),
              'pointer_state':'Unrelocated guest RVAs; target method entries fully ARM64 decoded',
              'enums':enums,'methods':methods,
              'fields':{m.string(m.types[ti][0]):n.fields(ti) for ti in (503,5002,5003,719)},
              'HighHPAll_apply_branch_rvas':branch_addresses,
              'InitializeData_JSON_key_usages':json_keys,
              'schema_source':'https://raw.githubusercontent.com/Perfare/Il2CppDumper/master/Il2CppDumper/Il2Cpp/Il2CppClass.cs'}
    Path('output/il2cpp/sample_code.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'HighHPAll':enums['ABILITY_TYPE']['HighHPAll'],'apply_branches':branch_addresses,
                     'handler':n.method(8886),'registration':hex(n.registration_rva)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
