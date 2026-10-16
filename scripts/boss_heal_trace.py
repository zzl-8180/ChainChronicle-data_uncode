"""Bounded static evidence for heal cap and timer callers, using existing recovered code."""
import json,hashlib
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
out=Path('output/boss_heal');out.mkdir(exist_ok=True)
ids=[7355,7358,3622,6370,7079,6979,7087,34609,7078];methods=[]
for ix in ids:
 r=n.method(ix);start=int(r['native_rva'],16);end=min(p for p in n.pointers if p>start);ins=list(md.disasm(n.raw[start:end],start));assert sum(i.size for i in ins)==end-start
 lines=[]
 for i in ins:
  comment=''
  if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):
   comment=' ; '+' | '.join(n.method(j)['declaring_type']+'.'+n.method(j)['name'] for j in n.method_by_rva.get(int(i.op_str[1:],16),[]))
  lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{comment}')
 (out/f'{ix}.txt').write_text('\n'.join(lines),encoding='utf-8');methods.append(r)
 print(ix,r['name'],len(ins))
result={'native_sha256':hashlib.sha256(n.raw).hexdigest(),'metadata_sha256':hashlib.sha256(m.raw).hexdigest(),'methods':methods,'attack_flag_enum':[dict(f,default=n.default(f['index'])) for f in n.fields(723) if 'OVER_HEAL' in f['name']]}
(out/'trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


# Resolve InitializeArray field handles instead of guessing constants from enum names.
import struct
constants={}
for label,slot,fmt in [('values',0x29c9ab0,'<6f'),('bits',0x29f3ae0,'<6i')]:
 usage=n.unpack('<Q',slot)[0];encoded=n.unpack('<Q',usage)[0];assert encoded>>29&7==4
 index=(encoded&0x1ffffffe)>>1;type_index,field_local=m.rows('fieldRefs','<ii')[index]
 type_def=n.type_info(type_index)['data'];field_index=m.types[type_def][8]+field_local
 defaults=[r for r in m.defaults if r[0]==field_index];assert len(defaults)==1
 offset=m.sections['fieldAndParameterDefaultValueData']['offset']+defaults[0][2]
 blob=m.raw[offset:offset+24];assert len(blob)==24
 constants[label]={'slot':hex(slot),'encoded':hex(encoded),'field_index':field_index,'field_name':m.string(m.fields[field_index][0]),'metadata_offset':hex(offset),'raw_hex':blob.hex(),'values':list(struct.unpack(fmt,blob))}
assert constants['bits']['values']==[40,35,41,42,43,44]
assert all(abs(a-b)<1e-6 for a,b in zip(constants['values']['values'],[1.2,1.3,1.4,1.6,1.8,2.0]))
constants['mask']={'value':0x1f0800000000,'code':'7355.txt:15777d4/15777e4'}
constants['loader_literals']=[n.literal(s) for s in (0x299f838,0x29e1460)]
assert [r['text'] for r in constants['loader_literals']]==['skillflag0_0','skillflag0_1']
constants['hp_fields']=[f for f in n.fields(503) if f['offset'] in ('0x58','0x68')]
unity=Native(m,'UnityEngine.CoreModule.dll');constants['time_getter']=unity.method(69362);assert constants['time_getter']['native_rva']=='0x1ebd4f0'
constants['time_unit_documentation']={'url':'https://docs.unity.cn/2021.3/Documentation/ScriptReference/Time-fixedDeltaTime.html','accessed':'2026-10-15','paraphrase':'Seconds of in-game fixed-step time, affected by game time scale; not wall-clock duration. External API documentation only, no game values imported.'}
core=Native(m,'mscorlib.dll');constants['array_initializer']=core.method(48546);assert constants['array_initializer']['native_rva']=='0x12f2c6c'
(out/'constants.json').write_text(json.dumps(constants,ensure_ascii=False,indent=2),encoding='utf-8')
