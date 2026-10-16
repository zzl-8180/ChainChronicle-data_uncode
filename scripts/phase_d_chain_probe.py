"""Execute installation/expansion/filter/HighHPAll with explicit runtime models.

CardInfo.skillid is a scenario input, NOT copied from the master skillid array.
Managed collections, metadata initialization and engine scalar getters are modeled;
native root-selection, sub expansion, eligibility, filtering, alive/HP and effect
control flow execute from the existing recovered image. No Android/host syscall.
"""
import hashlib
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

BASE, HEAP, STACK, STOP = 0x50000000,0x10000000,0x20000000,0x30000000


def fbits(value):
    return struct.unpack('<I',struct.pack('<f',value))[0]


def fvalue(value):
    return struct.unpack('<f',struct.pack('<I',value))[0]


class Guest:
    def __init__(self, native, rows):
        self.uc = Uc(UC_ARCH_ARM64,UC_MODE_ARM)
        self.uc.mem_map(BASE,(len(native)+4095)&~4095)
        self.uc.mem_write(BASE,native)
        self.uc.mem_map(HEAP,0x400000)
        self.uc.mem_map(STACK,0x100000)
        self.uc.mem_map(STOP,4096)
        self.cursor = HEAP
        self.rows, self.skills, self.integers, self.floats = rows,{}, {},{}
        self.lookups, self.reads, self.eligibility = [],[],[]
        self.failure = None
        self.statics = {}
        for slot in (0x29fb900,0x29c9c58,0x29d4ed0,0x29fc768,0x29b2c98,
                     0x29b6f18,0x29f9340,0x29a7f40,0x29b2c30,0x29f0b88,
                     0x29e25e0,0x29fbd08,0x29b3260,0x29f2990,0x29b6980,
                     0x29bda68,0x29b76e0,0x29d5fa0,0x29d5498,0x29aa7e0):
            self.metadata(slot)
        for rva in (0x2bd00e4,0x2bd0111,0x2bd0116,0x2bd2c92,0x2bcf5ba,0x2bd2c16):
            self.uc.mem_write(BASE+rva,b'\1')
        self.uc.hook_add(UC_HOOK_CODE,self.hook)

    def alloc(self,size,data=b''):
        p = self.cursor
        self.cursor += (size+15)&~15
        if self.cursor>HEAP+0x400000:
            raise ValueError('Guest heap exceeded')
        if data:
            self.uc.mem_write(p,data)
        return p

    def u32(self,p): return struct.unpack('<I',bytes(self.uc.mem_read(p,4)))[0]
    def u64(self,p): return struct.unpack('<Q',bytes(self.uc.mem_read(p,8)))[0]
    def put32(self,p,v): self.uc.mem_write(p,struct.pack('<I',v & 0xffffffff))
    def put64(self,p,v): self.uc.mem_write(p,struct.pack('<Q',v))
    def reg(self,i): return self.uc.reg_read(UC_ARM64_REG_X0+i)
    def setreg(self,i,v): self.uc.reg_write(UC_ARM64_REG_X0+i,v)

    def metadata(self,slot):
        cls,statics,cell = self.alloc(0x180),self.alloc(0x800),self.alloc(8)
        self.put32(cls+0xe0,1)
        self.uc.mem_write(cls+0x132,b'\1')
        self.put64(cls+0x20,cls)  # generic type slot, collection model only
        self.put64(cls+0xb8,statics)
        context,method = self.alloc(0x80),self.alloc(0x20)
        self.put64(cls+0xc0,context)
        self.put64(context+0x58,method)
        self.put64(method+8,STOP+0x100)  # declared managed AddWithResize model
        self.put64(cell,cls)
        self.put64(BASE+slot,cell)
        self.statics[slot] = statics

    def array(self,values,fmt='Q',capacity=None):
        capacity = len(values) if capacity is None else capacity
        p = self.alloc(32+struct.calcsize('<'+fmt)*capacity)
        self.put64(p+24,capacity)
        if values:
            self.uc.mem_write(p+32,struct.pack('<'+fmt*len(values),*values))
        return p

    def collection(self,values,capacity=32):
        p = self.alloc(0x30)
        self.put64(p+0x10,self.array(values,capacity=max(capacity,len(values))))
        self.put32(p+0x18,len(values))
        return p

    def skill(self,sid):
        if sid not in self.rows: return 0
        if sid in self.skills: return self.skills[sid]
        row = self.rows[sid]
        obj = self.alloc(0x100)
        self.skills[sid] = obj
        for offset,value in ((0x10,sid),(0x28,row['ability'])):
            p = self.alloc(0x20)
            self.integers[p] = value
            self.put64(obj+offset,p)
        for i in range(6):
            key = f'param{i}'
            # Constructor proves param0..4 start as float0; optional param5 null.
            if key not in row and i==5: continue
            p = self.alloc(0x20)
            self.floats[p] = (sid,key,row.get(key,0.0),'SOURCE' if key in row else 'NATIVE_CTOR_DEFAULT')
            self.put64(obj+0x30+i*8,p)
        sub = []
        for child in row.get('sub',[]):
            p = self.alloc(0x20)
            self.integers[p] = child
            sub.append(p)
        self.put64(obj+0xa0,self.collection(sub))
        return obj

    def span(self,obj):
        return (self.u64(obj+0x10)+32,self.u32(obj+0x18)) if obj else (0,0)

    def ret(self,value=None,second=None):
        if value is not None: self.setreg(0,value)
        if second is not None: self.setreg(1,second)
        self.uc.reg_write(UC_ARM64_REG_PC,self.uc.reg_read(UC_ARM64_REG_X30))

    def hook(self,cpu,address,size,unused):
        try:
            rva = address-BASE
            if address==STOP:
                cpu.emu_stop(); return
            if address==STOP+0x100:
                obj,item = self.reg(0),self.reg(1)
                array,count = self.span(obj)
                capacity = self.u32(array-8)
                values = [self.u64(array+i*8) for i in range(count)]+[item]
                self.put64(obj+0x10,self.array(values,capacity=max(capacity*2,count+1)))
                self.put32(obj+0x18,count+1)
                self.ret(); return
            if address==getattr(self,'slice_stop',None):
                self.slice_done = True
                cpu.emu_stop(); return
            if rva in (0x18238f8,0x1823a54):
                sid = self.reg(1)&0xffffffff
                result = self.skill(sid) if rva==0x18238f8 else 0
                self.lookups.append({'id':sid,'layer':'JSON' if rva==0x18238f8 else 'APK','found':bool(result)})
                self.ret(result)
            elif rva==0x1801970:
                self.ret(self.database)
            elif rva in (0xa92534,0xa926f0):
                p = self.reg(0)
                if p not in self.integers: raise ValueError('Unknown engine integer object')
                self.ret(self.integers[p])
            elif rva==0xa92830:
                p = self.reg(0)
                if p not in self.floats: raise ValueError('Unknown engine float object')
                sid,key,value,origin = self.floats[p]
                self.reads.append({'source_id':sid,'field':key,'raw':value,'origin':origin})
                cpu.reg_write(UC_ARM64_REG_S0,fbits(value))
                self.ret()
            elif rva in (0x1279020,0x703444):
                self.ret(*self.span(self.reg(0)))
            elif rva==0x88d910:
                self.ret(self.alloc(0x30))
            elif rva==0xa83fe4:
                self.put64(self.reg(0)+0x10,self.array([],capacity=self.reg(1)))
                self.put32(self.reg(0)+0x18,0)
                self.ret()
            elif rva==0x1610698:  # ReadOnlySpan<sbyte>(pointer,length)
                self.ret()
            elif rva==0x1eb8358:  # Unity destroyed/null predicate is supplied
                self.ret(int(self.reg(0)==0))
            elif rva in (0x88d81c,0x88d8fc):
                raise ValueError('Unexpected metadata initialization beyond declared fixture')
            elif rva in (0x88d920,0x88d928):
                raise ValueError(f'Native null/bounds exception at {hex(rva)}')
            elif rva==0x1112574:
                self.eligibility.append({'skill_object':hex(self.reg(1)),'target':hex(self.reg(2)),
                                         'note':'Native IsEnableAbility executes; no result replacement'})
            elif not (BASE<=address<BASE+0x2e00000):
                raise ValueError(f'Undeclared guest execution {hex(address)}')
        except Exception as error:
            self.failure = str(error)
            cpu.emu_stop()

    def run(self,start,*args,stop=None):
        self.failure = None
        self.slice_stop = BASE+stop if stop else None
        self.slice_done = False
        self.uc.reg_write(UC_ARM64_REG_SP,STACK+0xf0000)
        self.uc.reg_write(UC_ARM64_REG_X30,STOP)
        for i,v in enumerate(args): self.setreg(i,v)
        try:
            self.uc.emu_start(BASE+start,STOP+4,timeout=2000000,count=200000)
        except Exception as error:
            raise ValueError(f'{error} at guest RVA {hex(self.uc.reg_read(UC_ARM64_REG_PC)-BASE)}') from error
        if self.failure: raise ValueError(self.failure)
        if self.uc.reg_read(UC_ARM64_REG_PC)!=STOP and not self.slice_done:
            raise ValueError('Guest did not reach declared return/boundary')
        return self.reg(0),self.reg(1)

    def install(self,owned_ids):
        self.database = self.alloc(0x30)
        self.bp = self.alloc(0xa80)
        cid = self.alloc(0x20)
        self.integers[cid] = 2327
        self.put64(self.bp+0x48,cid)
        info = self.alloc(0x180)
        self.put64(info+0xa8,self.array(owned_ids,'I'))
        roots = self.collection([])
        frame = STACK+0x80000
        self.uc.reg_write(UC_ARM64_REG_X29,frame)
        self.put64(frame-0xa8,roots)
        for i,v in ((19,self.bp),(21,info),(22,self.database),(23,roots)):self.setreg(i,v)
        self.run(0x10fb1b0,stop=0x10fb288)
        ref = self.alloc(8,struct.pack('<Q',roots))
        self.run(0x10f8368,ref)
        installed = self.u64(ref)
        arr,count = self.span(installed)
        ptrs = [self.u64(arr+i*8) for i in range(count)]
        reverse = {v:k for k,v in self.skills.items()}
        self.installed_ids = [reverse[p] for p in ptrs]
        # Native caller converts expanded list to array, storing BattleParam+0x1e0.
        self.put64(self.bp+0x1e0,self.array(ptrs))
        enum = json.loads(Path('output/il2cpp/sample_code.json').read_text())['enums']['ABILITY_TYPE']
        values = sorted(v['value'] for v in enum.values())
        self.flag_index = values.index(1105)
        self.put64(self.statics[0x29bda68]+0x18,self.array(values,'I'))
        self.uc.mem_write(self.statics[0x29e25e0]+0x136,struct.pack('<H',self.flag_index))
        bit_array = self.alloc(0x20)
        self.put64(bit_array+0x10,self.array([0]*8,'I'))
        self.put32(bit_array+0x18,256)
        self.put64(self.bp+0x398,bit_array)
        for sid in self.installed_ids:
            ability = self.rows[sid]['ability']
            self.run(0x13caf74,bit_array,values.index(ability),1,0)
        return self.installed_ids

    def actor(self,hp,maxhp,state=0,bp=None):
        bp = self.alloc(0xa80) if bp is None else bp
        actor = self.alloc(0x600)
        self.put64(actor+0x28,bp)
        self.put32(actor+0x1c,state)
        self.uc.mem_write(actor+0x118,b'\1')  # active scenario; outer manager guard is static evidence
        self.put64(bp+0x3f0,actor)
        p = self.alloc(0x20);self.integers[p]=hp;self.put64(bp+0x68,p)
        p = self.alloc(0x20);self.floats[p]=('actor','_invhpMax',1/maxhp,'SCENARIO');self.put64(bp+0x60,p)
        return actor

    def effect(self,receiver_hp,owner_hp,owner_state=0,receiver_state=0,same_actor=False,target_hp=None):
        owner = self.actor(owner_hp,100,owner_state,self.bp)
        if same_actor:
            assert (receiver_hp,receiver_state)==(owner_hp,owner_state)
        receiver = owner if same_actor else self.actor(receiver_hp,100,receiver_state)
        target = self.actor(target_hp,100) if target_hp is not None else 0
        manager = self.alloc(0x400)
        actors = self.collection([owner,receiver])
        self.put64(manager+0x70,actors)
        self.put64(self.statics[0x29f0b88]+0x10,manager)
        indices = self.alloc(64)
        filtered,count = self.run(0x10ff968,self.bp,indices,64,self.flag_index,0)
        selected = [self.installed_ids[bytes(self.uc.mem_read(filtered+i,1))[0]] for i in range(count)]
        self.reads = []
        value,_ = self.run(0x159321c,0,0,receiver,owner,target,indices,64,0,0)
        return {'receiver_hp':receiver_hp,'owner_hp':owner_hp,'owner_state':owner_state,'receiver_state':receiver_state,
                'same_actor':same_actor,'attack_target_hp':target_hp,'actor_active_scenario':True,
                'installed_ids':self.installed_ids,'selected_ids':selected,
                'attack_contribution_float32':fvalue(value & 0xffffffff),'value_bits':hex(value & 0xffffffff),
                'native_parameter_reads':self.reads,'eligibility_invocations':len(self.eligibility)}


def main():
    native = Path('work/protection/il2cpp_loader_seed1.bin').read_bytes()
    rows = {r['skillid']:r for r in json.loads(Path('output/decoded/skilllist.data5.json').read_text(encoding='utf-8'))['skilllist']}
    cases = []
    for receiver_hp,owner_hp,owner_state,receiver_state,same_actor,target_hp in (
        (24,100,0,0,False,None),(25,100,0,0,False,None),(49,1,0,0,False,None),
        (50,1,0,0,False,None),(100,1,0,0,False,None),(50,0,0,0,False,None),
        (50,100,12,0,False,None),(50,100,0,12,False,None),
        (50,50,0,0,True,None),(50,100,0,0,False,0),(50,100,0,0,False,100)):
        owned = [40232705]
        guest = Guest(native,rows)
        guest.install(owned)
        result = guest.effect(receiver_hp,owner_hp,owner_state,receiver_state,same_actor,target_hp)
        assert result['selected_ids']==[40232705,40232706]
        expected = 1.0
        if receiver_hp>=1 and owner_hp>=1 and owner_state!=12 and receiver_state!=12:
            for sid in result['selected_ids']:
                if fvalue(fbits(receiver_hp*fvalue(fbits(0.01))))>=fvalue(fbits(rows[sid]['param0'])):
                    expected = fvalue(fbits(expected*fvalue(fbits(rows[sid]['param1']))))
        assert result['value_bits']==hex(fbits(expected)),(result,expected)
        result['CardInfo_skillid_input'] = owned
        result['status'] = 'PASS'
        cases.append(result)
    # Root absent: installer does not manufacture it from the master card record.
    empty = Guest(native,rows)
    assert empty.install([])==[]
    absent = empty.effect(50,100)
    assert absent['selected_ids']==[] and absent['value_bits']==hex(fbits(1.0))
    output = Path('output/phase_d')
    output.mkdir(exist_ok=True)
    sample = json.loads(Path('output/sample/sample.json').read_text(encoding='utf-8'))
    report = {'status':'PASS','native_image_sha256':hashlib.sha256(native).hexdigest(),
              'evidence_level':'CONTROLLED_NATIVE_WITH_MODELS; outer call sites are STATIC; no DEVICE evidence',
              'source_sample':{'card_raw':sample['card_raw'],'skill_raw':sample['skill_raw'],
                               'subskills_raw':sample['subskills_raw'],
                               'record_locations':{k:v for k,v in sample['record_locations'].items()
                                                   if k in ('2327','40232705','40232706','40232707','40232708','40232709')},
                               'input_provenance':sample['input_provenance'],
                               'missing_fields_preserved':True},
              'unknowns':{'current_CardInfo_skillid':None,'required_level_or_unlock_quest':None,
                          'current_device_activation':None,'final_battle_multiplier':None},
              'cases':cases,'absent_root':absent,
              'native_scope':['CreatePlayer root-selection slice0x10fb1b0..0x10fb288',
                              'addSubAbility, daSkill.get fallback control flow, IsEnableAbility and GetAbilityListOnFlagIndex',
                              'Native BitArray Set/Get, IsAlive, get_hpRate and entire HighHPAll handler'],
              'models':['Scenario CardInfo.skillid; actual device list unavailable',
                        'JSON lookup and absent APK lookup supplied for these APK-absent records',
                        'Managed collection allocation/span conversion; metadata class state',
                        'Engine scalar getters; enum flag map derives from metadata Enum.GetValues ordering',
                        'No extra event/weapon/etc abilities supplied; full CreatePlayer outside root slice not executed'],
              'limits':['Conditional static/native association, not observed current phone activation',
                        'PlayerManager outer PLAYER-list/active-provider selection traced statically, not executed here',
                        'No final global battle multiplier or damage claim; other effect contributions omitted']}
    (output/'chain_probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','case_count':len(cases),'cases':[(r['receiver_hp'],r['owner_hp'],r['attack_contribution_float32']) for r in cases]}))


if __name__=='__main__':
    main()
