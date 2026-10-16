"""Bounded v31 metadata reader; resolve selected game methods only.

Layout reference: Perfare/Il2CppDumper MetadataClass.cs, version 31 branches.
No game values are imported from external sources.
"""
import hashlib
import json
import struct
from pathlib import Path

SECTIONS = "stringLiteral stringLiteralData string events properties methods parameterDefaultValues fieldDefaultValues fieldAndParameterDefaultValueData fieldMarshaledSizes parameters fields genericParameters genericParameterConstraints genericContainers nestedTypes interfaces vtableMethods interfaceOffsets typeDefinitions images assemblies fieldRefs referencedAssemblies attributeData attributeDataRange unresolvedVirtualCallParameterTypes unresolvedVirtualCallParameterRanges windowsRuntimeTypeNames windowsRuntimeStrings exportedTypeDefinitions".split()


class Metadata:
    def __init__(self, path):
        self.raw = path if isinstance(path, bytes) else Path(path).read_bytes()
        if len(self.raw)<256:
            raise ValueError('Truncated metadata header')
        if struct.unpack_from('<II', self.raw) != (0xfab11baf, 31):
            raise ValueError('Expected decoded v31 metadata')
        self.sections = {}
        previous_end = 256
        for i, name in enumerate(SECTIONS):
            offset, size = struct.unpack_from('<II', self.raw, 8+8*i)
            if offset < previous_end or offset+size > len(self.raw):
                raise ValueError(f'Section boundary/overlap: {name}')
            self.sections[name] = {'offset': offset, 'size': size}
            previous_end = offset+size
        if previous_end != len(self.raw):
            raise ValueError('Metadata final boundary differs from file size')
        self.types = self.rows('typeDefinitions', '<IIiiiiiIiiiiiiii8HII')
        self.methods = self.rows('methods', '<IiiiiiI4H')
        self.fields = self.rows('fields', '<IiI')
        self.parameters = self.rows('parameters', '<IIi')
        self.images = self.rows('images', '<IiiIiIiIiI')
        self.defaults = self.rows('fieldDefaultValues', '<iii')
        self.type_images = {}
        for image in self.images:
            name = self.string(image[0])
            if image[2] < 0 or image[2]+image[3] > len(self.types):
                raise ValueError('Image type range')
            for index in range(image[2], image[2]+image[3]):
                if index in self.type_images:
                    raise ValueError('Overlapping image type ranges')
                self.type_images[index] = name
        for ti, row in enumerate(self.types):
            self.string(row[0]); self.string(row[1])
            fs, ms, mc, fc = row[8], row[9], row[16], row[18]
            if fc and not 0 <= fs <= fs+fc <= len(self.fields):
                raise ValueError('Type field range')
            if mc and not 0 <= ms <= ms+mc <= len(self.methods):
                raise ValueError('Type method range')
            for mi in range(ms, ms+mc):
                if self.methods[mi][1] != ti:
                    raise ValueError('Method declaring type mismatch')
        for row in self.methods:
            self.string(row[0])
            ps, pc = row[4], row[10]
            if pc and not 0 <= ps <= ps+pc <= len(self.parameters):
                raise ValueError('Method parameter range')
        for row in self.fields+self.parameters:
            self.string(row[0])

    def rows(self, name, fmt):
        section = self.sections[name]
        stride = struct.calcsize(fmt)
        if section['size'] % stride:
            raise ValueError(f'Unaligned table {name}, stride {stride}')
        return list(struct.iter_unpack(fmt, self.raw[section['offset']:section['offset']+section['size']]))

    def string(self, index):
        section = self.sections['string']
        if not 0 <= index < section['size']:
            raise ValueError('String index out of range')
        start = section['offset']+index
        end = self.raw.find(b'\0', start, section['offset']+section['size'])
        if end < 0:
            raise ValueError('Unterminated metadata string')
        return self.raw[start:end].decode('utf-8')

    def method(self, mi):
        row = self.methods[mi]
        ti = row[1]
        return {'index': mi, 'metadata_byte_offset': self.sections['methods']['offset']+mi*36,
                'name': self.string(row[0]), 'declaring_type_index': ti,
                'declaring_type': self.string(self.types[ti][0]), 'image': self.type_images[ti],
                'token': hex(row[6]), 'return_type_index': row[2],
                'parameters': [{'name': self.string(p[0]), 'type_index': p[2]}
                               for p in self.parameters[row[4]:row[4]+row[10]]]}


def main():
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    methods = [m.method(i) for i, row in enumerate(m.methods)
               if any(t in m.string(row[0]) for t in ('HighHPAll', 'IntervalFall'))]
    target_types = []
    for ti, row in enumerate(m.types):
        name = m.string(row[0])
        names = [m.string(f[0]) for f in m.fields[row[8]:row[8]+row[18]]]
        if ('param0' in names or 'HighHPAll' in names or 'IntervalFallWeapon' in names):
            target_types.append({'index':ti, 'name':name,'image':m.type_images[ti],
                                 'fields':[{'index':row[8]+i,'name':m.string(f[0]),'type_index':f[1],'token':hex(f[2])}
                                           for i,f in enumerate(m.fields[row[8]:row[8]+row[18]])]})
    report = {'decoded_sha256':hashlib.sha256(m.raw).hexdigest(), 'metadata_version':31,
              'validation':'PASS: all 31 section boundaries, table strides, type ownership, method parameter ranges and referenced UTF8 names',
              'counts':{'types':len(m.types),'methods':len(m.methods),'fields':len(m.fields),'images':len(m.images)},
              'sections':m.sections,'methods':methods,'target_types':target_types,
              'schema_source':'https://raw.githubusercontent.com/Perfare/Il2CppDumper/master/Il2CppDumper/Il2Cpp/MetadataClass.cs'}
    Path('output/il2cpp/metadata_targets.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'validation':report['validation'],'counts':report['counts'],'methods':methods,
                      'target_types':[(t['index'],t['name'],len(t['fields'])) for t in target_types]},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
