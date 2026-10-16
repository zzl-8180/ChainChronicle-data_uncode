"""Bounded SAutoMotion qualification, mapping, Support3 routing and aggregation.

Native qualification and the complete common handler/target selector/callback/
Support3 wrapper execute. Candidate lists, engine values, allocation, delegate
construction and home/weapon predicates are explicit fixtures. Base support
submission and Heal are intercepted; this is not a complete battle simulation.
"""
import hashlib
import json
import math
import struct
from pathlib import Path

from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_S8,UC_ARM64_REG_TPIDR_EL0
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_timed_support import TimedGuest
from phase_d_chain_probe import BASE,fbits,fvalue

OUT=Path('output/ordinary_effects/ability3000')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')
FIELDS=('param1','param2','param6','param8')
WEAPON_MASK=0x7fc00000


class SympathyGuest(TimedGuest):
    def __init__(self,native,rows):
        super().__init__(native,rows)
        for slot in (0x29e3b90,0x29bc5a0,0x29b0e90,0x29b9aa8,0x29d2670):self.metadata(slot)
        for flag in (0x2bd2cb5,0x2bd2cb8,0x2bd2ac6,0x2bd37df,0x2bd2caf,0x2bd2ca8,0x2bd3583):self.uc.mem_write(BASE+flag,b'\1')
        self.uc.reg_write(UC_ARM64_REG_TPIDR_EL0,self.alloc(0x100))
        self.applications=[];self.heals=[];self.home_match=True;self.weapon_flags=0
        self.home_calls=[];self.capture_event=False;self.event_calls=0
        self.put64(self.statics[0x29bda68]+0x20,WEAPON_MASK)

    def skill(self,sid):
        obj=super().skill(sid)
        if not self.u64(obj+0x90):
            for off,lo,hi in ((0x90,'flag0_0','flag0_1'),(0x98,'flag1_0','flag1_1')):
                pointer=self.alloc(0x20);raw=self.rows[sid]
                self.integers[pointer]=raw.get(lo,raw.get('flag',0) if off==0x90 else 0)|(raw.get(hi,0)<<32)
                self.put64(obj+off,pointer)
        return obj

    def actor(self,active=True,hp=100,job=0,hero=False):
        actor=self.alloc(0x400);bp=self.alloc(0xa80);status=self.alloc(0x300)
        self.put64(actor+0x28,bp);self.put64(actor+0xa0,status)
        self.uc.mem_write(actor+0x118,bytes([active]));self.uc.mem_write(bp+0x1f,bytes([hero]))
        for off,value in ((0x68,hp),(0x58,100),(0xf8,job)):
            pointer=self.alloc(0x20);self.integers[pointer]=value;self.put64(bp+off,pointer)
        for off in (0x230,0x238):self.put64(status+off,self.alloc(0x40))
        return actor

    def hook(self,cpu,address,size,unused):
        a=address-BASE
        if a==0x88d910:self.ret(self.alloc(0x100))
        elif a==0xa928d8:self.ret(self.integers[self.reg(0)])
        elif a==0xa84484:
            pointer,count=self.span(self.reg(0));index=self.reg(1)&0xffffffff
            assert index<count;self.ret(self.u64(pointer+index*8))
        elif a==0x155a914:
            # Model only managed delegate layout, not the target's execution.
            self.put64(self.reg(0)+0x18,BASE+0x155b1b4);self.put64(self.reg(0)+0x40,self.reg(1));self.ret()
        elif a==0x14374bc:self.ret(math.floor(fvalue(cpu.reg_read(UC_ARM64_REG_S0))))
        elif a==0x1541158:self.heals.append(self.reg(1));self.ret()
        elif a==0x1ec91b8:self.ret(int(self.reg(0)!=self.reg(1)))
        elif a==0x1113958:
            self.home_calls.append(self.reg(0));self.ret(int(self.home_match))
        elif a==0x10f2604:self.ret(self.weapon_flags)
        elif a==0x1584ac8:self.ret()
        elif a==0x15a6ddc and self.capture_event:self.event_calls+=1;self.ret()
        elif a==0x17774b0:
            data=self.reg(7)
            self.applications.append(dict(controller=self.reg(0),ability_id=self.reg(4),ability_type=self.reg(5),
                support_time=fvalue(cpu.reg_read(UC_ARM64_REG_S0)),
                normal_delta=struct.unpack('<f',cpu.mem_read(data+0x14,4))[0],
                skill_delta=struct.unpack('<f',cpu.mem_read(data+0x18,4))[0],
                critical_damage_delta=struct.unpack('<f',cpu.mem_read(data+0x28,4))[0]))
            self.ret()
        else:super().hook(cpu,address,size,unused)


def application_case(native,record,chain,active=True,hp=100):
    raw=record['raw'];sid=raw['skillid'];g=SympathyGuest(native,{sid:raw})
    owner=g.actor();targets=[owner,g.actor(),g.actor(active=active,hp=hp)]
    g.uc.mem_write(owner+0x12c,struct.pack('<f',chain))
    g.run(0x15a7474,0,owner,g.skill(sid),g.collection(targets))
    expected_targets=[owner] if int(raw.get('param0',0))==0 else [t for t in targets if t!=targets[-1] or (active and hp>0)]
    assert len(g.applications)==len(expected_targets)
    for applied,target in zip(g.applications,expected_targets):
        assert applied['controller']==g.u64(g.u64(target+0xa0)+0x238)
        assert applied['controller']!=g.u64(g.u64(target+0xa0)+0x230)
        assert applied['ability_id']==sid and applied['ability_type']==3000
        for field,key in (('param1','normal_delta'),('param2','skill_delta'),('param6','support_time'),('param8','critical_damage_delta')):
            assert applied[key]==fvalue(fbits(raw.get(field,0)))
    return dict(name=f'apply_{sid}_chain{chain}_active{active}_hp{hp}',skill_id=sid,chain_fixture=chain,
        source_fields={f:dict(present=f in raw,raw_value=raw.get(f)) for f in FIELDS},
        application_count=len(g.applications),support_category='Support3',
        submissions=[{k:v for k,v in a.items() if k!='controller'} for a in g.applications],passed=True)


def main():
    records=[json.loads(s) for s in SOURCE.open(encoding='utf-8')]
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('ability')==3000]
    assert len(selected)==382
    counts={f:sum(f in r['raw'] for r in selected) for f in FIELDS}
    assert counts==dict(param1=303,param2=303,param6=348,param8=144)
    assert sum('param0' in r['raw'] for r in selected)==376 and all(r['raw'].get('param0',1)==1 for r in selected)
    assert sum('iParam0' in r['raw'] for r in selected)==7 and sum('param9' in r['raw'] for r in selected)==86
    assert all(((r['raw'].get('flag0_0',r['raw'].get('flag',0))|(r['raw'].get('flag0_1',0)<<32))&WEAPON_MASK)==0 for r in selected)
    assert all(r['raw'][f] in ((45,60) if f=='param6' else (.05,.1)) for r in selected for f in FIELDS if f in r['raw'])
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    enum=next(f for f in n.fields(718) if f['name']=='SAutoMotion');assert n.default(enum['index'])['value']==3000
    ranges=dict(skill_start_sympathy_flags=(0x1295db8,0x1295e28),event_gate=(0x15a6ddc,0x15a6f24),provider_gate_and_dispatch=(0x15a6fc0,0x15a7084),
        qualification=(0x15a67a8,0x15a696c),dispatch=(0x15a7474,0x15a74c8),
        common_mapping=(0x15a7b84,0x15a7d68),target_selector=(0x1591e84,0x1592004),
        receiver_callback=(0x155b1b4,0x155b348),support3_route=(0x17777bc,0x17778cc),
        support_store=(0x1777598,0x17775cc),default_support3=(0x1778cac,0x1778d04),
        bounds_constructor=(0x172dd30,0x172ddb0),normal_sum=(0x172e8c0,0x172e98c),
        skill_sum=(0x172e98c,0x172ea5c),critical_damage_sum=(0x172ecb4,0x172ed7c),
        delta_support3=(0x176cd10,0x176cd28),countdown=(0x172e55c,0x172e578),weapon_mask_init=(0x15777bc,0x15777e4))
    OUT.mkdir(parents=True,exist_ok=True)
    for name,(begin,end) in ranges.items():
        lines=[]
        for ins in d.disasm(n.raw[begin:end],begin):
            ids=n.method_by_rva.get(int(ins.op_str[1:],16),[]) if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#0x') else []
            note=' ; '+','.join(n.method(i)['declaring_type']+'.'+n.method(i)['name'] for i in ids) if ids else ''
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    sample_ids={43023611};seen=set()
    for r in selected:
        shape=tuple(f for f in FIELDS if f in r['raw'])
        values=tuple((f,r['raw'][f]) for f in FIELDS if f in r['raw'])
        key=(shape,values,r['raw'].get('param0'))
        if key not in seen:seen.add(key);sample_ids.add(r['raw']['skillid'])
    checks=[]
    g=SympathyGuest(n.raw,{});g.setreg(8,g.statics[0x29bda68]);g.run(0x15777bc,stop=0x15777e4)
    assert struct.unpack_from('<Q',n.raw,0x2073f10)[0]==WEAPON_MASK==g.u64(g.statics[0x29bda68]+0x20)
    checks.append(dict(name='native_weapon_mask_init_and_all382_bypass',mask=WEAPON_MASK,source_records_with_intersection=0,passed=True))
    for r in selected:
        if r['raw']['skillid'] in sample_ids:
            for chain in (.5,2):checks.append(application_case(n.raw,r,chain))
    example=next(r for r in selected if r['raw']['skillid']==43023611)
    for active,hp in ((False,100),(True,0)):checks.append(application_case(n.raw,example,1,active,hp))
    # The actual record-level qualification checks the triggering actor's job/home,
    # and the owner's active state only for runtime param0=0.
    qualification_records=[next(r for r in selected if r['raw'].get('iParam0')==mask) for mask in (7,13,16,19)]
    qualification_records.append(example)
    for r in qualification_records:
        for job in range(6):
            raw=r['raw'];g=SympathyGuest(n.raw,{raw['skillid']:raw});owner=g.actor();actor=g.actor(job=job)
            result,_=g.run(0x15a67a8,0,actor,owner,g.skill(raw['skillid']),job)
            want=not raw.get('iParam0') or bool(raw['iParam0']&(1<<job))
            assert result==int(want)
            checks.append(dict(name=f'qualification_{raw["skillid"]}_trigger_job{job}',skill_id=raw['skillid'],trigger_job=job,qualifies=bool(result),passed=True))
    missing=next(r for r in selected if 'param0' not in r['raw'])
    for record in (missing,example):
        for active in (False,True):
            raw=record['raw'];g=SympathyGuest(n.raw,{raw['skillid']:raw});actor=g.actor();owner=g.actor(active=active)
            result,_=g.run(0x15a67a8,0,actor,owner,g.skill(raw['skillid']),0);assert result==int(active or raw.get('param0')==1)
            checks.append(dict(name=f'param0_{raw.get("param0")}_owner_active{active}',skill_id=raw['skillid'],source_param0_present='param0' in raw,qualifies=bool(result),passed=True))
    home=next(r for r in selected if r['raw'].get('param9') and not r['raw'].get('iParam0') and not r['raw'].get('flag0_0') and not r['raw'].get('flag0_1'))
    for matches in (False,True):
        raw=home['raw'];g=SympathyGuest(n.raw,{raw['skillid']:raw});actor=g.actor();owner=g.actor();g.home_match=matches
        result,_=g.run(0x15a67a8,0,actor,owner,g.skill(raw['skillid']),0)
        assert result==int(matches) and g.home_calls==[int(raw['param9'])]
        checks.append(dict(name=f'trigger_home_predicate{matches}',skill_id=raw['skillid'],home_selector=raw['param9'],predicate_fixture=matches,qualifies=bool(result),passed=True))
    for flags in range(8):
        g=SympathyGuest(n.raw,{});skill=g.alloc(0x100);actor=g.actor();manager=g.alloc(0x100);g.capture_event=True
        for bit in range(3):g.uc.mem_write(skill+0x7c+bit,bytes([bool(flags&(1<<bit))]))
        for reg,value in ((19,skill),(20,actor),(21,1),(22,manager)):g.setreg(reg,value)
        g.run(0x1295db8,stop=0x1295e28);assert g.event_calls==int(flags!=0)
        checks.append(dict(name=f'skill_start_sympathy_flags_{flags}',sympathy=bool(flags&1),k_sympathy=bool(flags&2),s_sympathy=bool(flags&4),dispatch_count=g.event_calls,passed=True))
    # Global dispatch and owner presence gates, bounded before collection lookup.
    for null,party,hp,kind in ((False,True,100,0),(True,True,100,0),(False,False,100,0),(False,True,0,0),(False,True,100,1)):
        g=SympathyGuest(n.raw,{});manager=g.alloc(0x100);actor=g.actor(hp=hp);g.put32(actor+0x18,kind)
        g.uc.mem_write(manager+0x78,bytes([party]));g.run(0x15a6ddc,manager,0 if null else actor,1,stop=0x15a6ee8)
        expected=not null and party and hp>0 and kind==0;assert g.slice_done==expected
        checks.append(dict(name=f'event_null{null}_party{party}_hp{hp}_kind{kind}',enters_candidate_lookup=expected,passed=True))
    for alive,has,hero in ((True,True,False),(False,True,False),(True,False,False),(True,True,True)):
        g=SympathyGuest(n.raw,{});owner=g.actor(hp=100 if alive else 0,hero=hero)
        g.uc.mem_write(owner+0x294,bytes([has]));g.setreg(27,owner)
        passes=alive and has and not hero;g.run(0x15a6fc0,stop=0x15a6fec if passes else 0x15a7428)
        checks.append(dict(name=f'owner_alive{alive}_has{has}_hero{hero}',enters_ability_lookup=passes,passed=True))
    # Support3 configured default bounds (category=1), not null-controller defaults.
    g=SympathyGuest(n.raw,{})
    top,bottom=g.alloc(0x60),g.alloc(0x60)
    g.run(0x172dd30,top,1,1);g.run(0x172dd30,bottom,1,0)
    bounds={name:[struct.unpack('<f',g.uc.mem_read(p+off,4))[0] for p in (bottom,top)] for name,off in (('normal',0x14),('skill',0x18),('critical_damage',0x28))}
    assert bounds==dict(normal=[.5,2],skill=[.5,2],critical_damage=[-1.5,1])
    checks.append(dict(name='support3_default_bound_constructor',bounds=bounds,passed=True))
    for count in (1,2,12):
        entries=[]
        for _ in range(count):
            data=g.alloc(0x60)
            for off in (0x14,0x18,0x28):g.uc.mem_write(data+off,struct.pack('<f',.1))
            entry=g.alloc(0x80);g.put64(entry+0x50,data);entries.append(entry)
        ctrl=g.alloc(0x40);g.put64(ctrl+0x10,g.collection(entries));g.put64(ctrl+0x20,top);g.put64(ctrl+0x28,bottom)
        results=[]
        for address in (0x172e8c0,0x172e98c,0x172ecb4):g.run(address,ctrl);results.append(fvalue(g.uc.reg_read(UC_ARM64_REG_S0)))
        expected=[min(2,1+count*.1)]*2+[min(1,count*.1)]
        assert all(abs(a-b)<1e-6 for a,b in zip(results,expected))
        checks.append(dict(name=f'support3_sum_{count}',supplied_contribution=.1,count=count,normal_factor=results[0],skill_factor=results[1],critical_damage_delta=results[2],passed=True))
    for seconds in (45,60):
        for delta in (.25,seconds):
            g=SympathyGuest(n.raw,{});entry=g.alloc(0x80);g.uc.mem_write(entry+0x30,struct.pack('<f',seconds))
            g.uc.reg_write(UC_ARM64_REG_S8,fbits(delta));g.run(0x172e55c,entry,stop=0x172e578)
            result=struct.unpack('<f',g.uc.mem_read(entry+0x30,4))[0];assert result==seconds-delta
            checks.append(dict(name=f'time_{seconds}_delta{delta}',source_time=seconds,game_delta_fixture=delta,remaining=result,passed=True))
    reused=[]
    for p in ('output/card_comparison_cid30236/timed_support/trace.json','output/card_comparison_cid30236/critical/trace.json','output/ordinary_effects/ability1017/trace.json'):
        proof=json.loads(Path(p).read_text(encoding='utf-8'));assert proof['native_sha256']==hashlib.sha256(n.raw).hexdigest()
        reused.append(dict(path=p,sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest()))
    trace=dict(effect_type=3000,namespace='ordinary skilllist',source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fixture_scripts={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('scripts/chica_timed_support.py','scripts/chica_ordinary_rules.py','scripts/phase_d_chain_probe.py')},
        ability_enum=dict(enum,default=n.default(enum['index'])),source_records=selected,record_count=382,present_field_count=sum(counts.values()),field_counts=counts,
        source_absence_counts={f:382-counts[f] for f in FIELDS},records_without_requested_fields=34,sample_ids=sorted(sample_ids),native_check_count=len(checks),
        fragments={name:[hex(a),hex(b)] for name,(a,b) in ranges.items()},reused_proofs=reused,default_support3_bounds=bounds,
        time_power_fields=n.fields(697),support3_field=next(f for f in n.fields(702) if f['name']=='_support3CtrlData'),
        sympathy_skill_fields=[f for f in n.fields(550) if f['offset'] in ('0x7c','0x7d','0x7e')],
        weapon_mask=dict(field=next(f for f in n.fields(745) if f['name']=='sAttackFlagWeaponMask'),value=WEAPON_MASK,
                         literal_rva='0x2073f10',literal_hex=n.raw[0x2073f10:0x2073f18].hex(),source_intersection_count=0),
        methods=[n.method(i) for i in (8908,8931,7108,7111,7222,7223,7227)],
        limits=['Only current CACHE ordinary3000 present param1/2/6/8 generalized. Missing raw fields never filled.',
            'Qualification checks trigger job/home and conditional owner activity; actual initialized weapon mask0x7fc00000 is checked, all382 source flags bypass this branch. Full weapon name mapping remains outside scope.',
            'Event dispatch requires party flag, living player trigger; candidate owners must be alive, have sympathy ability and not hero. Real installation and event timing are not emulated.',
            'Runtime param0=1 loops supplied candidates; missing getter0 uses owner. Callback requires alive/active recipient. Full party/back-up list composition not emulated.',
            'Common handler, target selector, callback and Support3 wrappers execute; allocation/delegate layout/scalar getters/home predicates modeled, Heal and base support submission intercepted.',
            'Support3 default configured normal/skill [.5,2], critical increment [-1.5,1] tested separately. Overrides, reapplication/expiry removal, full battle stacking and final HP outside scope.',
            'Only present positive45/60 game-time inputs generalized; missing param6 not treated as permanent or exported as0.'])
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,limits=trace['limits']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=382,present_fields=sum(counts.values()),sample_records=len(sample_ids),native_checks=len(checks))))


if __name__=='__main__':main()
