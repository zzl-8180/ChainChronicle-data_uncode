"""Bounded extra-ability native evidence; does not build profiles or pages."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from il2cpp_sample_code import Native
from metadata_targets import Metadata
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
import unicorn.arm64_const as U

OUT = ROOT/'output/character_skills/type1082'
MD = ROOT/'work/protection/metadata_aei_decoded.bin'
IMAGE = ROOT/'work/protection/il2cpp_loader_seed1.bin'


class Fixture:
    def __init__(self, raw):
        self.u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        self.u.mem_map(0, (len(raw)+4095)&~4095)
        self.u.mem_write(0, raw)
        self.u.mem_map(0x40000000, 0x100000)
        self.u.reg_write(U.UC_ARM64_REG_SP, 0x400e0000)
        self.u.reg_write(U.UC_ARM64_REG_TPIDR_EL0, 0x400f0000)
        self.cursor = 0x40001000
        self.hooks, self.calls, self.executed = {}, [], set()
        self.u.hook_add(UC_HOOK_CODE, self.hook)
        # IL2CPP metadata/class initialization and Object construction are fixture boundaries.
        self.hooks[0x88d81c] = lambda: None
        self.hooks[0x88d8fc] = lambda: None
        self.hooks[0x11e52ac] = lambda: None

    def alloc(self, size=0x200):
        ptr = self.cursor
        self.cursor += (size+15)&~15
        return ptr

    def q(self, at, val): self.u.mem_write(at, struct.pack('<Q', val))
    def w(self, at, val): self.u.mem_write(at, struct.pack('<I', val & 0xffffffff))
    def readq(self, at): return struct.unpack('<Q', self.u.mem_read(at, 8))[0]
    def readw(self, at): return struct.unpack('<I', self.u.mem_read(at, 4))[0]
    def reg(self, name, value=None):
        number = getattr(U, 'UC_ARM64_REG_'+name.upper())
        if value is not None: self.u.reg_write(number, value)
        return self.u.reg_read(number)

    def string(self, value):
        ptr = self.alloc(0x20+len(value)*2)
        self.w(ptr+0x10, len(value))
        self.u.mem_write(ptr+0x14, value.encode('utf-16le')+b'\0\0')
        return ptr

    def usage(self, slot, value):
        holder = self.alloc(8)
        self.q(slot, holder); self.q(holder, value)

    def hook(self, uc, address, size, data):
        self.executed.add(address)
        if address in self.hooks:
            self.calls.append(hex(address))
            value = self.hooks[address]()
            if value is not None: self.reg('x0', value)
            self.reg('pc', self.reg('lr'))

    def run(self, start, stop=0x400ff000, **regs):
        for key, value in regs.items(): self.reg(key, value)
        self.reg('lr', stop)
        try:
            self.u.emu_start(start, stop, count=20000)
        except Exception as error:
            raise RuntimeError(f'Native fixture failed at PC={self.reg("pc"):#x}; x0={self.reg("x0"):#x}, x8={self.reg("x8"):#x}') from error
        if self.reg('pc') != stop:
            raise AssertionError(f'Instruction limit before stop: {self.reg("pc"):#x}')
        return self.reg('x0')

    def number_format(self):
        klass = self.alloc()
        self.usage(0x29dab08, klass)
        self.w(klass+0xe0, 1)
        fmt = self.alloc()
        plus, minus = self.string('+'), self.string('-')
        self.q(fmt+0x28, plus); self.q(fmt+0x30, minus)
        self.usage(0x29febb8, plus); self.usage(0x29f3e78, minus)
        self.hooks[0x143ff8c] = lambda: fmt


def main():
    md = Metadata(MD)
    n, lib = Native(md), Native(md, 'mscorlib.dll')
    assert hashlib.sha256(n.raw).hexdigest() == '562a6975fe722d39842a3c7daa3982785c04beaf503c4fe1cc6fbbec3cd047c1'
    assert hashlib.sha256(md.raw).hexdigest() == '07d582df6318e128424e41b93a8a6e86b238b9be14832756a780e47fb70443b1'
    ti = {md.string(t[0]): i for i,t in enumerate(md.types) if md.type_images[i]=='Assembly-CSharp.dll'}
    extra_field = next(f for f in n.fields(ti['ABILITY_TYPE']) if f['name']=='ExtraAbility')
    enum_default = n.default(extra_field['index'])
    assert enum_default['value'] == 1082
    selected_types = ['ExtraAbilityParam','ExtraAbility','ExtraAbilityInfo','CardInfo','skillParameter','BattleParam']
    fields = {t: [f for f in n.fields(ti[t]) if t.startswith('Extra') or f['name'] in
                   ('limit_break','_extra_ability','_ability','_str0','_listSkill')] for t in selected_types}
    def method(addr):
        return [obj.method(i) for obj in (n,lib) for i in obj.method_by_rva.get(addr, [])]
    def dis(lo,hi):
        rows=[]
        for i in Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(n.raw[lo:hi],lo):
            r=dict(rva=hex(i.address), bytes=i.bytes.hex(), op=i.mnemonic+' '+i.op_str)
            if i.mnemonic in ('b','bl'):
                target=int(i.op_str.removeprefix('#'),16)
                if method(target): r['callee']=method(target)
            rows.append(r)
        return rows
    # Inputs: one raw extra parent, with levels kept separate. No profile rec_key lookup.
    extra_path=ROOT/'output/cache_full_20261015_v3/decoded/extraabilitylist.data5.json.raw'
    skill_path=ROOT/'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw'
    extra=json.loads(extra_path.read_bytes())['extra_ability_info']
    parent=next(r for r in extra if r['cid']==30236)
    skills={r['skillid']:r for r in json.loads(skill_path.read_bytes())['skilllist']}
    # Exact wrapper samples from the first two distinct levels.
    wrappers=[]
    for idx in (0,1):
        sid=parent['extra_abilities'][idx]['skill_ids'][1]
        row=skills[sid]
        assert row['ability']==1082
        wrappers.append(dict(cid=30236, level_index=idx, level=parent['extra_abilities'][idx]['lv'],
                             reference_field=f'extra_abilities[{idx}].skill_ids[1]', wrapper=row,
                             target_record=skills[int(row['str0'])]))
    # 1. Actual CardInfo -> limit_break -> array-index selection, including invalid index cases.
    f=Fixture(n.raw); card=f.alloc(); info=f.alloc(); arr=f.alloc(); f.q(card+0x120,info); f.q(info+0x18,arr); f.w(arr+0x18,5)
    level_ptrs=[]
    for i, raw in enumerate(parent['extra_abilities']):
        obj=f.alloc(); ids=f.alloc(); level_ptrs.append(obj)
        f.q(arr+0x20+i*8,obj); f.q(obj+0x20,ids); f.q(ids+0x18,len(raw['skill_ids']))
    selections=[]
    for level in (-1,0,1,4,5):
        f.w(card+0x84,level)
        actual=f.run(0x1a78124,x0=card)
        expected=level_ptrs[level] if 0<=level<5 else 0
        assert actual==expected
        selections.append(dict(limit_break=level,selected_index=level if actual else None,returned_pointer=hex(actual)))
    # 2. Run the actual wrapper initializer. daSkill.get is a fixture database lookup;
    # protected getters return the declared decoded field. String/Int32 parsing runs native.
    forwarding=[]
    for sample in wrappers:
        row=sample['wrapper']; f=Fixture(n.raw); f.number_format()
        obj,record,wrapped_string,wrapped_float=f.alloc(),f.alloc(),f.alloc(),f.alloc()
        text=f.string(row['str0']); f.q(record+0xa8,wrapped_string); f.q(wrapped_string+0x10,text)
        f.q(record+0x30,wrapped_float); f.w(obj+0x10,row['skillid'])
        f.w(obj+0x14,-1)
        manager_class=f.alloc(); f.usage(0x29d4ed0,manager_class); f.w(manager_class+0xe0,1)
        # Reflection Enum.ToObject is outside the forwarding chain: stop after param0 call.
        lookup=[]
        f.hooks[0x1801970]=lambda: 0x400ff100
        def lookup_wrapper():
            lookup.append(f.reg('w1')); return record
        f.hooks[0x181be68]=lookup_wrapper
        f.hooks[0xa92bb8]=lambda: f.readq(f.reg('x0')+0x10)
        f.run(0xfa15ac,0xfa1680,x0=obj)
        target=f.readw(obj+0x14)
        assert lookup==[row['skillid']] and target==int(row['str0'])
        assert {0xfa165c,0x1dbd4b0,0xfa167c,0x10ca54c,0x10d60b8} <= f.executed
        # Native GetSkillParam reads the stored target and tail-calls the DB consumer.
        target_record=f.alloc(); target_lookup=[]
        def lookup_target():
            target_lookup.append(f.reg('w1')); return target_record
        f.hooks[0x181be68]=lookup_target
        result=f.run(0xfa1740,x0=obj)
        assert target_lookup==[target] and result==target_record
        forwarding.append(dict(wrapper_id=row['skillid'],str0=row['str0'],stored_target_id=target,
                               first_lookup=lookup,target_lookup=target_lookup,
                               native_parser_executed=True,native_getter_executed=True,
                               target_returned=True,native_rvas=sorted(hex(x) for x in f.executed
                               if 0xfa15ac<=x<0xfa17c4 or 0x10ca54c<=x<0x10ca7a8 or 0x10d60b8<=x<0x10d68f4)))
    # 3. Run actual scope selector body and following BattleParam target lookup/list store.
    # Dictionary enumeration and span constructors remain explicit managed boundaries.
    dispatch=[]
    for sample in wrappers:
        target=int(sample['wrapper']['str0']); f=Fixture(n.raw)
        param,arr,output=f.alloc(),f.alloc(),f.alloc(); f.w(arr+0x18,1); f.q(arr+0x20,param); f.w(param+0x14,target)
        for scope,party_order,holder_order,wanted in [(0,2,2,True),(0,1,2,False),(1,1,2,True),(2,0,2,True),(2,1,2,False),(3,2,2,True),(3,1,2,False)]:
            f.w(param+0x18,scope); f.w(output,0)
            regs=dict(x22=arr,x8=1,x9=0,x19=output,x20=64,x21=party_order,x23=holder_order,x24=0)
            f.run(0xfa2d14,0xfa2da0,**regs)
            observed=f.readw(output)
            assert observed==(target if wanted else 0)
            dispatch.append(dict(wrapper_id=sample['wrapper']['skillid'],target_id=target,target_selector=scope,
                                 holder_order=holder_order,party_order=party_order,emitted_id=observed))
        # Existing list with capacity to avoid shared generic List.Add growth routine.
        target_row=skills[target]
        db,list_obj,items,record,ids=f.alloc(),f.alloc(),f.alloc(),f.alloc(),f.alloc()
        frame=f.alloc(); f.q(frame-0x70,ids); f.w(ids,target); f.q(list_obj+0x10,items); f.w(items+0x18,4)
        f.q(record+0x28,f.alloc()); f.q(0x29b6f18,f.alloc())
        f.hooks[0x181be68]=lambda: record
        f.hooks[0xa92534]=lambda: target_row['ability']
        looked=[]
        def target_lookup(): looked.append(f.reg('w1')); return record
        f.hooks[0x181be68]=target_lookup
        f.run(0x110398c,0x1103a18,x21=db,x29=frame,x19=0,x20=list_obj)
        assert looked==[target] and f.readq(items+0x20)==record and f.readw(list_obj+0x18)==1
        dispatch.append(dict(wrapper_id=sample['wrapper']['skillid'],target_id=target,target_type=target_row['ability'],
                             lookup_ids=looked,target_record_added_to_battle_list=True,
                             native_ability_getter=0x1dbcf0c in f.executed))
    ranges={'extra_master_loader':(0xfa21a0,0xfa2398),
            'extra_parent_loader':(0xfa1964,0xfa1f00),'wrapper_handler':(0xfa15ac,0xfa17c4),
            'parent_selection':(0x1a78124,0x1a78140),'active_extra_scope':(0xfa2cd0,0xfa2da4),
            'battle_target_load':(0x1103934,0x1103a34),'skill_str0_getter':(0x1dbd484,0x1dbd4e0),
            'integer_parser_entry':(0x10ca54c,0x10ca7a8),'extra_battle_selection':(0xfa2a9c,0xfa2b78),
            'extra_parent_lookup':(0xfa2470,0xfa24b0),'battle_party_population':(0xfa28dc,0xfa292c)}
    ranges.update(active_extra_list_entry=(0xfa2c54,0xfa2cd0),
                  active_extra_list_return=(0xfa2da4,0xfa2e2c),
                  skill_lookup_cache_and_apk_fallback=(0x181be68,0x181bea0),
                  final_battle_skill_array=(0x1103ad0,0x1103b50))
    literal_keys=[n.literal(x) for x in (0x29f0318,0x29adb40,0x29a5648,0x29a7508)]
    assert [x['text'] for x in literal_keys]==['skill_ids','lv','extra_abilities','cid']
    assert all(not (i['op'].startswith('bl ') and '0x1dbcf0c' in i['op'])
               for lo,hi in [(0xfa15ac,0xfa1740),(0xfa1ac8,0xfa1bf8)] for i in dis(lo,hi))
    report=dict(verdict='FORWARD',evidence_kind='STATIC_NATIVE_CALL_CHAIN_AND_CONTROLLED_NATIVE_FRAGMENTS',
                inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                        for p in (IMAGE,MD,extra_path,skill_path)],enum_identity=dict(field=extra_field,default=enum_default),
                version=dict(package='com.sega.chainchronicle',version_name='5.6.2',version_code=56021,
                             source='output/apk/phase_a_report.md; source library/image binding: output/il2cpp/metadata_entry_refs.json',
                             original_library_sha256='2ca5c29269ce85baed25665dd82d821bc6ea0194a748a7f4dbe4f71ab6ed6f27'),
                fields=fields,literal_keys=literal_keys,fixtures=wrappers,
                checks=[dict(name='extra_parent_load_and_limit_break_selection',passed=True,observations=selections,
                             evidence=['extra_master_loader','extra_parent_loader','parent_selection','extra_battle_selection','extra_parent_lookup','battle_party_population'],
                             call_chain='ExtraAbilityMaster.InitMasterData -> ExtraAbilityInfo.InitData -> ExtraAbility.InitData -> InitAbilityParam; CardInfo.GetCurrentExtraAbility -> GetExtraAbility(limit_break)',
                             fixture_boundary='Raw JSON to managed arrays statically traced; native CardInfo/ExtraAbilityInfo selection executed for five indices.'),
                        dict(name='type1082_extra_preprocessing_str0_integer_and_target_lookup',passed=True,observations=forwarding,
                             evidence=['wrapper_handler','extra_parent_loader','skill_str0_getter','integer_parser_entry'],
                             call_chain='skill_ids[i] -> _extraAbiId -> daSkill.get -> get_str0 -> Int32.TryParse(out _skillId) -> GetSkillParam -> daSkill.get(_skillId)',
                             fixture_boundary='DB and protected value decoding stubbed; native string getter pointer load, IsNullOrEmpty, Int32.TryParse, Number.TryParseInt32 and decimal loop executed. Scope enum conversion not executed.'),
                        dict(name='target_scope_filter_and_battle_skill_list_dispatch',passed=True,observations=dispatch,
                             evidence=['active_extra_scope','battle_target_load'],
                             call_chain='active _abilityParams -> target qualification -> _skillId output -> BattleParam.SetSkillList -> daSkill.get(target) -> get_ability(target) -> List<skillParameter> store',
                             fixture_boundary='Dictionary/span helper boundaries not executed; scope body and final lookup/list-store slices executed with explicit fixtures. Ability protected scalar decoder stubbed; actual get_ability pointer load executes.')],
                instruction_evidence={name:dis(*span) for name,span in ranges.items()},
                limitations=['Not real-device execution or a full engine reproduction.',
                             'ExtraAbilityParam initialization is the extra-specific handler; it does not first dispatch the wrapper through the generic ability switch.',
                             'Database lookup, protected string/int decoding, IL2CPP metadata initialization and allocation are fixture boundaries. Int32.TryParse and its decimal digit parsing execute native.',
                             'Initializer execution stops at 0xfa1680 before target-scope Enum.ToObject; scope filters execute separately with explicit selector values 0/1/2/3, without assigning unproved names to other values or resolving missing raw param0 defaults.',
                             'Dictionary enumeration and Span-return helpers are statically traced, not executed end-to-end.',
                             'No assertion that all extra wrappers are active or all parent text fragments uniquely bind to target effects.',
                             'Supplied aggregate counts are quoted by README and were not recomputed.'],
                remaining_breakpoints=['Full managed dictionary population/iteration and runtime account/party state were not emulated.',
                                       'Unknown selector values and individual sentence-to-effect attribution remain outside this verdict.'])
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'native_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(verdict=report['verdict'],checks=[dict(name=c['name'],passed=c['passed'],samples=len(c['observations'])) for c in report['checks']]),ensure_ascii=True))


if __name__=='__main__': main()
