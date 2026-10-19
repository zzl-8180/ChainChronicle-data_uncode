"""P3B7 bounded current-machine-code proof for the three startup consumers."""
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
import common as C
from il2cpp_sample_code import Native
from metadata_targets import Metadata
from skilllist_types import enum_values
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
import unicorn.arm64_const as U
OUT=C.ROOT/'output/character_skills/description_bindings/p3b7_batch'

def evidence(n,md):
 d=Cs(CS_ARCH_ARM64,CS_MODE_ARM);checks=[]
 def ck(name,ok,**kw):checks.append(dict(name=name,passed=bool(ok),**kw))
 def ins(lo,hi):return [dict(rva=hex(i.address),op=i.mnemonic+' '+i.op_str)for i in d.disasm(n.raw[lo:hi],lo)]
 ti={md.string(t[0]):i for i,t in enumerate(md.types)}
 fields={t:{f['name']:f['offset']for f in n.fields(ti[t])}for t in ['AbilityTypeCachedFlagIndex','Constants','skillParameter']}
 enums=enum_values(n,md,'ABILITY_TYPE');values=sorted(enums.values())
 ck('independent_metadata_enum_fields_and_offsets',enums['ManaGet']==26 and enums['TenmaMana']==1073 and enums['MajinMana']==1077 and fields['AbilityTypeCachedFlagIndex']['_ManaGet']=='0x2a' and fields['AbilityTypeCachedFlagIndex']['_TenmaMana']=='0x106' and fields['AbilityTypeCachedFlagIndex']['_MajinMana']=='0x108' and fields['Constants']['ABILITY_TYPE_ENUM_ARRAY']=='0x18',fields=fields,enum_identity={k:enums[k]for k in ['ManaGet','TenmaMana','MajinMana']})
 # Resolve generic call identities from the actual MethodSpec records. The two
 # shared int implementations are independently found through registration rows.
 reg=n.unpack('<16Q',n.registration_rva)
 def spec(slot):
  encoded=n.unpack('<Q',n.unpack('<Q',slot)[0])[0];idx=(encoded&0x1ffffffe)>>1
  method,klass,inst=n.unpack('<3i',reg[9]+idx*12)
  return dict(slot=hex(slot),encoded=hex(encoded),method_spec_index=idx,method=md.method(method),class_inst=klass,method_inst=inst)
 binary=spec(0x29faa10);span=spec(0x29b7748)
 library=Native(md,'mscorlib.dll')
 methods={hex(a):[library.method(i)for i in library.method_by_rva.get(a,[])]for a in [0x12c5338,0x12d3a14,0x12da810,0x11ebb60]}
 ck('runtime_array_search_and_cleanup_method_identities',binary['method']['name']=='BinarySearch' and binary['method']['declaring_type']=='MemoryExtensions' and span['method']['name']=='op_Implicit' and any(m['name']=='GetValues'for m in methods['0x12c5338']) and any(m['name']=='ClearWithReferences'for m in methods['0x12da810']),binary_search=binary,span_conversion=span,runtime_methods=methods)
 # This shared native BinarySearch(int, comparer) has a real comparator call;
 # it is not replaced by Python lookup or a stubbed index result.
 table=[n.unpack('<4i',reg[5]+i*16)for i in range(reg[4])]
 span_rows=[r for r in table if n.unpack('<3i',reg[9]+r[0]*12)[0]==43482]
 candidates=[]
 for r in span_rows:
  base=0x2900da8-r[1]*8
  if n.refs(struct.pack('<Q',base)):candidates.append(base)
 base=next(iter(set(candidates))) if len(set(candidates))==1 else 0
 search_row=next(r for r in table if r[0]==38634)
 search=n.unpack('<Q',base+search_row[1]*8)[0]if base else 0
 ck('shared_int_binary_search_native_registration',base==0x28cbfb8 and search==0x128a6d0 and n.unpack('<3i',reg[9]+38634*12)[0]==43494,generic_pointer_array=hex(base),pointer_array_reference=list(map(hex,n.refs(struct.pack('<Q',base)))),span_helpers_method=md.method(43494),method_spec=38634,registration_row=search_row,native_rva=hex(search))
 def machine():
  u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);size=(len(n.raw)+4095)&~4095
  u.mem_map(0,size);u.mem_write(0,n.raw);u.mem_map(0x40000000,0x20000)
  u.reg_write(U.UC_ARM64_REG_SP,0x4001e000)
  def q(a,v):u.mem_write(a,struct.pack('<Q',v))
  def w(a,v):u.mem_write(a,struct.pack('<I',v))
  def b(a,v=1):u.mem_write(a,bytes([v]))
  # Explicit initialized runtime fixture. Enum.GetValues supplies the full
  # 249-value sorted metadata enum array; managed allocation/reflection and
  # interface tables are fixture state. Search/compare/mapping code runs native.
  q(0x29bda68,0x40001000);q(0x40001000,0x40002000);w(0x400020e0,1);q(0x400020b8,0x40003000)
  q(0x40003018,0x40004000);q(0x40003000,0x40005000);w(0x40004018,len(values))
  u.mem_write(0x40004020,struct.pack('<'+'i'*len(values),*values))
  b(0x2bd2c15);b(0x2bd020a);b(0x2bd2c16);b(0x2bd2cd0)
  q(0x29b7748,0x40006000);q(0x40006000,0x40006100);q(0x40006120,0x40006200);b(0x40006332)
  q(0x29faa10,0x40007000);q(0x40007000,0x40007100);q(0x40007138,0x40007200)
  q(0x40007218,0x40007300);q(0x40007308,search);q(0x40007338,0x40007400)
  q(0x40007410,0x40007500);q(0x40007520,0x40007600);b(0x40007732)
  q(0x400076c0,0x40007700);q(0x40007708,0x40007800);b(0x40007932)
  q(0x40005000,0x40005100);u.mem_write(0x4000522a,struct.pack('<H',1));q(0x400051b0,0x40005300)
  q(0x40005300,0x40007800);w(0x40005308,0);q(0x40005238,0x15793dc);q(0x40005240,0)
  q(0x40008000,0x40009000);q(0x400090b8,0x4000a000)
  return u
 u=machine();rounds=[]
 for typ in [26,1073,1077]:
  u.reg_write(U.UC_ARM64_REG_W0,typ);u.reg_write(U.UC_ARM64_REG_LR,0x4001f000)
  u.emu_start(0x15771e8,0x4001f000,count=5000);index=u.reg_read(U.UC_ARM64_REG_W0)
  u.reg_write(U.UC_ARM64_REG_X0,index);u.reg_write(U.UC_ARM64_REG_LR,0x4001f000)
  u.emu_start(0x1578da0,0x4001f000,count=200);back=u.reg_read(U.UC_ARM64_REG_W0)
  rounds.append(dict(ability_type=typ,actual_cached_flag_index=index,roundtrip_type=back,expected_index=values.index(typ)))
 ck('actual_native_forward_binary_search_and_reverse_roundtrip',all(r['actual_cached_flag_index']==r['expected_index']and r['roundtrip_type']==r['ability_type']for r in rounds),samples=rounds,fixture='完整249枚举值来自metadata；GetValues的分配/反射已初始化；索引搜索、原生Compare、ushort写回及逆向取数组均执行当前机器码，没有stub搜索结果')
 ctors=[(26,0x157669c,0x15766b0,0x2a),(1073,0x1576f34,0x1576f48,0x106),(1077,0x1576f48,0x1576f5c,0x108)]
 stored=[]
 for typ,lo,hi,off in ctors:
  u.reg_write(U.UC_ARM64_REG_X19,0x40008000);u.emu_start(lo,hi,count=5000)
  got=struct.unpack('<H',u.mem_read(0x4000a000+off,2))[0]
  stored.append(dict(type=typ,field_offset=hex(off),actual_stored_index=got))
 ck('real_ctor_type_argument_to_field_with_unstubbed_forward_mapping',all(x['actual_stored_index']==values.index(x['type'])for x in stored),samples=stored)
 # Execute each consumer's actual ldrh field read. Other instructions and
 # generic scratch-buffer setup are retained in the full slices for audit.
 loads=[(1073,0x158c48c,0x158c494,28),(1077,0x158c748,0x158c750,23),(26,0x158ca24,0x158ca2c,25)]
 loaded=[]
 for typ,lo,hi,regno in loads:
  u.reg_write(U.UC_ARM64_REG_X8,0x40009000);u.emu_start(lo,hi,count=8)
  got=u.reg_read(getattr(U,'UC_ARM64_REG_W'+str(regno)))
  loaded.append(dict(type=typ,read_rva=hex(lo),flag_index=got))
 ck('real_consumer_flag_field_loads',all(r['flag_index']==values.index(r['type'])for r in loaded),samples=loaded)
 # Actual getter and exact compare run for all 65 child types and all three
 # startup types; no stub returns the expected ability value.
 queue=[r for r in map(json.loads,(OUT/'type26_extended_inventory.jsonl').open(encoding='utf-8'))if r['selected']]
 subtypes=sorted({c['effect_type']for r in queue for c in r['children']})
 ability_offset=int(fields['skillParameter']['_ability'],16)
 samples=[];hit=[]
 def hook(uu,a,s,data):
  if a==0xa92534:
   # ParamS_int's protected-value runtime decoder is an explicit boundary stub;
   # skillParameter.get_ability's real pointer load and the type compare run.
   ptr=uu.reg_read(U.UC_ARM64_REG_X0)
   uu.reg_write(U.UC_ARM64_REG_W0,struct.unpack('<I',uu.mem_read(ptr+0x10,4))[0]);uu.reg_write(U.UC_ARM64_REG_PC,uu.reg_read(U.UC_ARM64_REG_LR))
  if a in [0x1117c08,0x1117c34]:hit.append(a);uu.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook)
 for request in loaded:
  u.reg_write(U.UC_ARM64_REG_X0,request['flag_index']);u.reg_write(U.UC_ARM64_REG_LR,0x4001f000)
  u.emu_start(0x1578da0,0x4001f000,count=200);wanted=u.reg_read(U.UC_ARM64_REG_W0)
  for actual in sorted(set(subtypes+[26,1073,1077])):
   hit.clear();u.mem_write(0x4000c000+ability_offset,struct.pack('<Q',0x4000d000));u.mem_write(0x4000d010,struct.pack('<I',actual));u.reg_write(U.UC_ARM64_REG_X23,0x4000c000);u.reg_write(U.UC_ARM64_REG_W21,wanted)
   u.emu_start(0x1117bf4,0x1117c48,count=25)
   samples.append(dict(requested_type=request['type'],flag_index=request['flag_index'],actual_getter_type=actual,accepted=hit==[0x1117c08]))
 ck('all_three_exact_getter_filters_and_65_other_child_types',all(s['accepted']==(s['requested_type']==s['actual_getter_type'])for s in samples),samples=samples,child_types=subtypes,child_instances=sum(len(r['children'])for r in queue),records=len(queue),stub='ParamS_int.get_Value保护值解码返回明确夹具值；get_ability真实字段指针读取和比较/分支不stub')
 # Current call/dataflow pins supplement the executed fragments; existing
 # eligibility and param0 conversion/grant evidence are reused without edits.
 pins={0x158c4d8:'mov x3, x28',0x158c4e0:'bl #0x1117a20',0x158c790:'mov x3, x23',0x158c798:'bl #0x1117a20',0x158ca6c:'mov x3, x25',0x158ca74:'bl #0x1117a20',0x1117aec:'bl #0x1578da0',0x1117af0:'mov w3, w0',0x1117b00:'bl #0x1117b54',0x1117bfc:'bl #0x1dbcf0c',0x1117c00:'cmp w0, w21',0x1117c04:'b.ne #0x1117c34',0x158c3d8:'bl #0x1244250',0x158c464:'bl #0x1244250',0x158c5e8:'bl #0x1244280',0x158c610:'bl #0x158c678',0x158c628:'bl #0x158c958',0x158c8f4:'bl #0x1244280',0x158c950:'b #0x12da810'}
 actual={hex(a):ins(a,a+4)[0]['op']for a in pins}
 ck('actual_caller_helpers_filter_and_other_grant_paths_preserved',all(actual[hex(a)]==s for a,s in pins.items()),pins=actual)
 ranges=[(0x157669c,0x15766b0),(0x1576f34,0x1576f5c),(0x15771e8,0x157732c),(0x1577720,0x15777bc),(0x1578da0,0x1578e08),(0x15793dc,0x15793e4),(0x14a40a4,0x14a40dc),(0xca61f4,0xca6200),(0x128a6d0,0x128a7f4),(0x1117a20,0x1117ca0),(0x158c234,0x158cf80),(0x1dbcf0c,0x1dbcf24)]
 return dict(generated_by='scripts/character_skills/p3b7_native.py',status='P3B7_C_SELF_CHECK_NOT_INDEPENDENT_D',native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(md.raw).hexdigest(),checks=checks,passed=sum(c['passed']for c in checks),total=len(checks),enum_array_values=values,slices=[dict(start=hex(lo),end=hex(hi),sha256=hashlib.sha256(n.raw[lo:hi]).hexdigest(),instructions=ins(lo,hi))for lo,hi in ranges],limits='仅PartyAbilityInit普通ManaGet基础产线的消费者分离。GetValues排序枚举数组、对象、泛型/接口表为明确初始化夹具；ParamS_int保护值解码调用为stub；搜索/比较/双向映射/ctor与消费者读取/get_ability字段读取和精确类型筛选执行原生字节。非完整托管运行时、全引擎或实机验证；继续战斗/w5系统授予、Tenma/Majin、ManaGet其他产线确实存在，不称本记录数字是队伍总量。')

if __name__=='__main__':
 C.enable_utf8_console();m=Metadata(C.ROOT/'work/protection/metadata_aei_decoded.bin');n=Native(m);ev=evidence(n,m);C.write_json(OUT/'native_evidence.json',ev)
 print(json.dumps(dict(passed=ev['passed'],total=ev['total'])));raise SystemExit(0 if ev['passed']==ev['total']else 1)
