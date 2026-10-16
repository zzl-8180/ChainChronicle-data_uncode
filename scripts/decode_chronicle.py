"""Execute real bundle transform on chronicle.dat and parse target MonoBehaviour.

Input experiment injects existing APK bytes into DWARF-identified buffer globals
and skips only Java fetching. It proves file conversion, not Android fetch origin.
"""
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

import UnityPy
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_PC, UC_ARM64_REG_X30, UC_ARM64_REG_SP

from decode_data5 import NativeDecoder, LIBRARY_BASE
from protection_emulate import BASE, STACK


def main():
    source = Path('work/apk/assets/chronicle.dat')
    raw = source.read_bytes()
    if not 64 <= len(raw) <= 8*1024*1024:
        raise ValueError('Bundle candidate size outside experiment bound')
    decoder = NativeDecoder()
    e = decoder.e
    buffer = e.allocate(len(raw),raw)
    output_pointer = e.allocate(8)
    symbols = {r['name']:r for r in json.loads(Path('output/native/recovered_symbols.json').read_text())}
    aliases = [(0x51e30,'s_pBundleMasterData'),(0x51e38,'s_nBundleMasterData_decrypt'),(0x51e40,'s_nBundleMasterDataSize')]
    for slot,name in aliases:
        e.uc.mem_write(LIBRARY_BASE+slot,struct.pack('<Q',LIBRARY_BASE+symbols[name]['address']))
    e.uc.mem_write(LIBRARY_BASE+symbols['s_pBundleMasterData']['address'],struct.pack('<Q',buffer))
    e.uc.mem_write(LIBRARY_BASE+symbols['s_nBundleMasterDataSize']['address'],struct.pack('<I',len(raw)))
    e.uc.mem_write(LIBRARY_BASE+symbols['s_nBundleMasterData_decrypt']['address'],struct.pack('<I',1))
    def skip_java(cpu,address,size,unused):
        cpu.reg_write(UC_ARM64_REG_PC,cpu.reg_read(UC_ARM64_REG_X30))
    e.uc.hook_add(UC_HOOK_CODE,skip_java,begin=LIBRARY_BASE+0x200ac,end=LIBRARY_BASE+0x200ac)
    e.uc.reg_write(UC_ARM64_REG_SP,STACK+0xe0000)
    returned = e.call(LIBRARY_BASE-BASE+0x26cfc,output_pointer,instruction_limit=100000000)
    converted = bytes(e.uc.mem_read(buffer,len(raw)))
    if returned != len(raw) or converted[:8]!=b'UnityFS\0':
        raise ValueError('Native InitializeData did not accept input')
    pointer = struct.unpack('<Q',bytes(e.uc.mem_read(output_pointer,8)))[0]
    if pointer!=buffer:
        raise ValueError('Unexpected native output pointer')
    cursor = 12
    for _ in range(2):
        cursor = converted.index(b'\0',cursor)+1
    declared_size = struct.unpack_from('>Q',converted,cursor)[0]
    if declared_size!=len(converted):
        raise ValueError('UnityFS declared file size differs')
    env = UnityPy.load(converted)
    objects = list(env.objects)
    monobehaviours = [o for o in objects if o.type.name=='MonoBehaviour']
    if len(monobehaviours)!=1:
        raise ValueError('Master component not unique')
    obj = monobehaviours[0]
    data = obj.read_typetree()
    script = obj.assets_file.objects[data['m_Script']['m_PathID']].read_typetree()
    if script['m_ClassName']!='ChronicleArchiveData':
        raise ValueError('Unexpected master component class')
    directory = Path('output/base_master')
    directory.mkdir(exist_ok=True)
    blob = obj.get_raw_data()
    if len(blob)!=obj.byte_size:
        raise ValueError('MonoBehaviour raw object boundary')
    (directory/'ChronicleArchiveData.bin').write_bytes(blob)
    (directory/'ChronicleArchiveData.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    summaries = []
    identifiers = {'charainfo':'cid','skilllist':'skillid','supporterskill':'ability_id'}
    for field in ('_mdCharacter','_mdSkill','_mdBossInfo','_mdSAbirity'):
        table = data[field]
        (directory/f'{field}.json').write_text(json.dumps(table,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
        for name,rows in table.items():
            summary = {'json_pointer':f'/{field}/{name}','records':len(rows)}
            if name in identifiers and rows and identifiers[name] in rows[0]:
                ids = [r[identifiers[name]] for r in rows]
                if len(ids)!=len(set(ids)):
                    raise ValueError('Master record identifiers not unique')
                summary['unique_ids'] = len(set(ids))
            summaries.append(summary)
    if source.read_bytes()!=raw:
        raise ValueError('Input changed')
    Path('work/protection/chronicle_decoded.unityfs').write_bytes(converted)
    report = {'status':'NATIVE_TRANSFORM_AND_COMPLETE_UNITY_MASTER_COMPONENT','source':str(source),
              'source_sha256':hashlib.sha256(raw).hexdigest(),'converted_sha256':hashlib.sha256(converted).hexdigest(),
              'converted_bytes':len(converted),'unityfs_declared_bytes':declared_size,
              'decoder':decoder.provenance,'entry_rva':'0x26cfc',
              'model':'Inject source into retained-symbol buffer globals, decrypt flag1; supply GOT aliases; skip Java fetch0x200ac; run actual InitializeData unchanged',
              'globals':[{'GOT_slot':hex(slot),'symbol':name,'symbol_rva':hex(symbols[name]['address'])} for slot,name in aliases],
              'objects':dict(Counter(o.type.name for o in objects)),
              'serialized_file':obj.assets_file.name,'object_path_id':obj.path_id,
              'object_byte_start_in_serialized_file':obj.byte_start,'object_byte_size':obj.byte_size,
              'object_sha256':hashlib.sha256(blob).hexdigest(),'script':script,'tables':summaries,
              'limits':['Conversion/file schema verified, actual Java asset fetch origin not traced',
                        'APK base master and phone tables remain separate; runtime override priority not assumed',
                        'Unity object fields are typed binary values; exported JSON is not original on-disk JSON']}
    (directory/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'sha256':report['converted_sha256'],'tables':summaries},ensure_ascii=False))


if __name__=='__main__':
    main()
