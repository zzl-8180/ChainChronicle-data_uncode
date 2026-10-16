"""PowerDrain native type/eligibility/probability gates and target Support2 data.

Execute installed-array filtering, real IsEnableAbility for99, complete handler
and Support2 wrappers. Installed arrays/bit cache, engine scalar access, random
draws and allocation are explicit fixtures. Capture the shared base submission;
test its time storage and bounded update separately. No installation or full
Attack/Attacked simulation and no claim about final damage or HP.
"""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_S8,UC_ARM64_REG_SP,UC_ARM64_REG_X29
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_timed_support import TimedGuest
from phase_d_chain_probe import Guest,BASE,STACK,fbits,fvalue

OUT=Path('output/ordinary_effects/ability99')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')
FIELDS=('param7','param9','param0')
ROUTES={0:'param1',1:'param3',2:'param2'}  # Normal, Skill, Critical (metadata)


class DrainGuest(TimedGuest):
    def __init__(self,native,rows,ability_values):
        super().__init__(native,rows)
        for slot in (0x29ab820,0x29bc5a0,0x29e95f0,0x29d2670,0x29ac170,0x29c1b58,0x29f3960,0x29a2f98,0x29fb370,0x29ebaf0):self.metadata(slot)
        for flag in (0x2bd0154,0x2bd37de,0x2bd357d,0x2bcf5b7):self.uc.mem_write(BASE+flag,b'\1')
        self.put32(self.statics[0x29ab820],1)  # supplied Single.Epsilon scalar
        self.put64(self.statics[0x29bda68]+0x18,self.array(ability_values,'I'))
        self.flag_index=ability_values.index(99)
        self.uc.mem_write(self.statics[0x29e25e0]+0xa6,struct.pack('<H',self.flag_index))
        self.submissions=[];self.random_value=.5;self.draws=[];self.params_updates=0
        self.capture_outer=False;self.outer_calls=0;self.broad_flag=True

    def actor(self,kind):
        bp=self.alloc(0xa80);actor=self.alloc(0x400);status=self.alloc(0x300)
        self.put64(bp+0x3f0,actor);self.put64(actor+0x28,bp);self.put32(actor+0x18,kind);self.put64(actor+0xa0,status)
        self.put64(status+0x230,self.alloc(0x40));self.put64(status+0x238,self.alloc(0x40))
        cid=self.alloc(0x20);self.integers[cid]=1;self.put64(bp+0x48,cid)
        return actor,bp

    def installed(self,bp,ids):
        self.put64(bp+0x1e0,self.array([self.skill(sid) for sid in ids]))
        bits=self.alloc(0x20);self.put64(bits+0x10,self.array([0]*16,'I'));self.put32(bits+0x18,512);self.put64(bp+0x398,bits)
        if any(self.rows[sid]['ability']==99 for sid in ids):self.run(0x13caf74,bits,self.flag_index,1,0)

    def hook(self,cpu,address,size,unused):
        a=address-BASE
        if a==0x1112574:Guest.hook(self,cpu,address,size,unused)  # real99 default eligibility executes
        elif a==0x88d910:self.ret(self.alloc(0x100))
        elif a==0x19072ec:
            self.draws.append(self.random_value);cpu.reg_write(UC_ARM64_REG_S0,fbits(self.random_value));self.ret()
        elif a==0x17774b0:
            data=self.reg(7);sp=cpu.reg_read(UC_ARM64_REG_SP)
            self.submissions.append(dict(controller=self.reg(0),supporter=self.reg(2),ability_id=self.reg(4),ability_type=self.reg(5),
                support_time=fvalue(cpu.reg_read(UC_ARM64_REG_S0)),multi_check=bool(cpu.mem_read(sp+8,1)[0]),
                attack_delta=struct.unpack('<f',cpu.mem_read(data+0x10,4))[0],incoming_delta=struct.unpack('<f',cpu.mem_read(data+0x20,4))[0]))
            self.ret()
        elif a==0xa84484:
            pointer,count=self.span(self.reg(0));index=self.reg(1)&0xffffffff;assert index<count;self.ret(self.u64(pointer+index*8))
        elif a==0xa85b64:
            values,count=self.span(self.reg(0));assert count==1 and self.u64(values)==self.reg(1)
            self.put32(self.reg(0)+0x18,0);self.ret(1)
        elif a==0x172e80c:self.params_updates+=1;self.ret()
        elif a==0x10f7378 and self.capture_outer:self.ret(int(self.broad_flag))
        elif a==0x1121be0 and self.capture_outer:self.outer_calls+=1;self.ret()
        else:super().hook(cpu,address,size,unused)


def handler_case(native,record,other,values,kind,chain,draw=.5,installed=True,owner_kind=0,threshold_override=None):
    source_raw=record['raw'];raw=dict(source_raw)
    if threshold_override is not None:raw[ROUTES[kind]]=threshold_override
    sid=raw['skillid'];g=DrainGuest(native,{sid:raw,other['skillid']:other},values)
    owner,bp=g.actor(owner_kind);target,_=g.actor(1-owner_kind)
    g.uc.mem_write(owner+0x12c,struct.pack('<f',chain));g.installed(bp,[other['skillid']]+([sid] if installed else []));g.random_value=draw
    g.run(0x1121be0,bp,g.alloc(64),64,target,kind,0)
    field=ROUTES.get(kind);threshold=raw.get(field,0) if field else 0
    want=installed and threshold>0 and draw<=threshold
    assert len(g.submissions)==(2 if want else 0) and len(g.draws)==int(installed and threshold>0)
    if want:
        for applied,recipient,supporter,fields in ((g.submissions[0],owner,target,('param4','param6')),(g.submissions[1],target,owner,('param7','param9'))):
            status=g.u64(recipient+0xa0)
            assert applied['controller']==g.u64(status+0x230) and applied['controller']!=g.u64(status+0x238)
            assert applied['supporter']==supporter and applied['ability_id']==sid and applied['ability_type']==99 and applied['multi_check']
            assert applied['support_time']==fvalue(fbits(raw['param0']))
            assert applied['attack_delta']==fvalue(fbits(raw.get(fields[0],0))) and applied['incoming_delta']==fvalue(fbits(raw.get(fields[1],0)))
    return dict(name=f'handler_{sid}_kind{kind}_chain{chain}_draw{draw}_installed{installed}_owner{owner_kind}',skill_id=sid,damage_type=kind,
        trigger_source_field=field,source_threshold_present=field in source_raw if field else False,source_threshold=source_raw.get(field),
        threshold_fixture_override=threshold_override,
        source_fields={f:dict(present=f in raw,raw_value=raw.get(f)) for f in FIELDS},chain_fixture=chain,random_fixture=draw,
        installed_fixture=installed,owner_kind_fixture=owner_kind,draw_count=len(g.draws),submissions=[{k:v for k,v in a.items() if k not in ('controller','supporter')} for a in g.submissions],
        target_recipient_count=int(want),passed=True)


def main():
    records=[json.loads(s) for s in SOURCE.open(encoding='utf-8')]
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('ability')==99]
    assert len(selected)==133
    counts={f:sum(f in r['raw'] for r in selected) for f in FIELDS};assert counts==dict(param7=126,param9=123,param0=133)
    assert all(r['raw']['flag']==0 for r in selected)
    assert all(r['raw'][f]==1 for r in selected for f in ('param1','param2','param3') if f in r['raw'])
    assert {r['raw']['param0'] for r in selected}=={-1,10,20,30,60}
    other=next(r['raw'] for r in records if r['table']=='skilllist' and r['raw'].get('skillid')==43023601)
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    enum=next(f for f in n.fields(718) if f['name']=='PowerDrain');assert n.default(enum['index'])['value']==99
    values=[]
    for f in n.fields(718):
        if f['name']!='value__':values.append(n.default(f['index'])['value'])
    values=sorted(set(values));assert len(values)<512
    damage_enum=[dict(f,default=n.default(f['index'])) for f in n.fields(642) if f['name'] in ('Normal','Skill','Critical')]
    assert [(f['name'],f['default']['value']) for f in damage_enum]==[('Normal',0),('Skill',1),('Critical',2)]
    ranges=dict(attack_return_damage=(0x153c0c4,0x153c0d4),attack_dispatch=(0x153c324,0x153c414),
        handler=(0x1121be0,0x1121ed0),type_and_eligibility_filter=(0x10ff968,0x10ffb34),
        eligibility_dispatch=(0x1112640,0x11126b0),eligibility_default99=(0x11134a0,0x11134a8),eligibility_return=(0x1113904,0x1113928),
        support2_route=(0x1777374,0x1777484),support_time_store=(0x1777568,0x17775b4),
        support_multi_check=(0x17775c8,0x1777634),time_update=(0x172e4a8,0x172e800),
        normal_sum=(0x172e8c0,0x172e98c),skill_sum=(0x172e98c,0x172ea5c),incoming_sum=(0x172eb24,0x172ebec),
        default_support2=(0x1778c4c,0x1778cac),bounds_constructor=(0x172dd30,0x172ddb0))
    OUT.mkdir(parents=True,exist_ok=True)
    for name,(a,b) in ranges.items():
        lines=[]
        for ins in d.disasm(n.raw[a:b],a):
            ids=n.method_by_rva.get(int(ins.op_str[1:],16),[]) if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#0x') else []
            note=' ; '+','.join(n.method(i)['declaring_type']+'.'+n.method(i)['name'] for i in ids) if ids else ''
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    sample_ids={43023616};seen_shapes=set()
    for field in FIELDS:
        seen=set()
        for r in selected:
            if field in r['raw'] and r['raw'][field] not in seen:seen.add(r['raw'][field]);sample_ids.add(r['raw']['skillid'])
    for r in selected:
        shape=tuple(f for f in ('param1','param2','param3','param7','param9') if f in r['raw'])
        if shape not in seen_shapes:seen_shapes.add(shape);sample_ids.add(r['raw']['skillid'])
        if r['raw']['param0']==-1:sample_ids.add(r['raw']['skillid'])
    checks=[]
    for r in selected:
        if r['raw']['skillid'] in sample_ids:
            for kind in (0,1,2):
                for chain in (.5,2):checks.append(handler_case(n.raw,r,other,values,kind,chain))
    example=next(r for r in selected if r['raw']['skillid']==43023616)
    for kwargs in (dict(kind=0,draw=1),dict(kind=3),dict(kind=0,installed=False),dict(kind=0,owner_kind=1),
                   dict(kind=0,draw=.25,threshold_override=.5),dict(kind=0,draw=.5,threshold_override=.5),dict(kind=0,draw=.75,threshold_override=.5)):
        checks.append(handler_case(n.raw,example,other,values,chain=1,**kwargs))
    # Positive returned damage and broad ability-presence gate in Attack; no full Attack emulation.
    for damage,broad in ((0,True),(-1,True),(1,False),(1,True)):
        g=DrainGuest(n.raw,{},values);g.capture_outer=True;g.broad_flag=broad;frame=STACK+0x80000;bp=g.alloc(0xa80);bp_ref=g.alloc(8,struct.pack('<Q',bp))
        g.uc.reg_write(UC_ARM64_REG_X29,frame);g.setreg(24,damage&0xffffffff);g.setreg(22,bp_ref)
        g.run(0x153c338,stop=0x153c440 if damage<1 else 0x153c414 if not broad else 0x153c3d4)
        assert g.outer_calls==int(damage>=1 and broad)
        checks.append(dict(name=f'outer_returned_damage{damage}_broadflag{broad}',attacked_return_fixture=damage,broad_flag_fixture=broad,drain_calls=g.outer_calls,passed=True))
    # Source99 IsEnableAbility has a default true branch; it is not replaced by LocalGuest.
    g=DrainGuest(n.raw,{example['raw']['skillid']:example['raw']},values)
    result,_=g.run(0x1112574,g.alloc(0xa80),g.skill(example['raw']['skillid']),0);assert result==1
    checks.append(dict(name='native_IsEnableAbility99_default_true',result=result,passed=True))
    for seconds in (-1,10,20,30,60):
        g=DrainGuest(n.raw,{},values);g.setreg(24,g.u64(BASE+0x29ab820));g.setreg(9,g.u64(BASE+0x29ac170))
        g.uc.reg_write(UC_ARM64_REG_S8,fbits(seconds));g.run(0x1777568,stop=0x17775b4)
        entry=g.reg(27);stored=struct.unpack('<ff',g.uc.mem_read(entry+0x30,8));assert stored==(seconds,seconds)
        checks.append(dict(name=f'time_store_{seconds}',source_time=seconds,support_time=stored[0],support_full_time=stored[1],passed=True))
        for delta in (.25,seconds if seconds>0 else 1000):
            g=DrainGuest(n.raw,{},values);entry=g.alloc(0x80);g.uc.mem_write(entry+0x30,struct.pack('<f',seconds))
            ctrl=g.alloc(0x40);items=g.collection([entry]);g.put64(ctrl+0x10,items)
            g.uc.reg_write(UC_ARM64_REG_S0,fbits(delta));g.run(0x172e4a8,ctrl,g.alloc(0x300))
            remaining=struct.unpack('<f',g.uc.mem_read(entry+0x30,4))[0];removed=g.u32(items+0x18)==0
            assert remaining==(seconds-delta if seconds>0 else -1) and removed==(seconds>0 and delta>=seconds)
            checks.append(dict(name=f'time_update_{seconds}_delta{delta}',source_time=seconds,game_delta_fixture=delta,remaining=remaining,removed=removed,passed=True))
    # Actual category0 bounds objects, kept separate from Support3.
    g=DrainGuest(n.raw,{},values);top,bottom=g.alloc(0x60),g.alloc(0x60)
    g.run(0x172dd30,top,0,1);g.run(0x172dd30,bottom,0,0)
    bounds={k:[struct.unpack('<f',g.uc.mem_read(p+off,4))[0] for p in (bottom,top)] for k,off in (('normal',0x14),('skill',0x18),('incoming',0x20))}
    assert all(b==[.5,2] for b in bounds.values())
    for count in (1,2,4):
        entries=[]
        for _ in range(count):
            data=g.alloc(0x60);g.uc.mem_write(data+0x10,struct.pack('<f',-.3));g.uc.mem_write(data+0x20,struct.pack('<f',.3))
            entry=g.alloc(0x80);g.put64(entry+0x50,data);entries.append(entry)
        ctrl=g.alloc(0x40);g.put64(ctrl+0x10,g.collection(entries));g.put64(ctrl+0x20,top);g.put64(ctrl+0x28,bottom)
        results=[]
        for address in (0x172e8c0,0x172e98c,0x172eb24):g.run(address,ctrl);results.append(fvalue(g.uc.reg_read(UC_ARM64_REG_S0)))
        assert all(abs(a-b)<1e-6 for a,b in zip(results,[max(.5,1-count*.3)]*2+[min(2,1+count*.3)]))
        checks.append(dict(name=f'support2_sum_{count}',count=count,normal_factor=results[0],skill_factor=results[1],incoming_factor=results[2],passed=True))
    reused=[]
    for p in ('output/card_comparison_cid30236/timed_support/trace.json','output/card_comparison_cid30236/difference_sources/trace.json','output/card_comparison_cid30236/mana_chance/trace.json','output/phase_d/chain_probe.json'):
        if not Path(p).is_file():continue
        proof=json.loads(Path(p).read_text(encoding='utf-8'));native_hash=proof.get('native_sha256',proof.get('native_image_sha256'))
        if native_hash is not None:assert native_hash==hashlib.sha256(n.raw).hexdigest()
        reused.append(dict(path=p,sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest()))
    trace=dict(effect_type=99,namespace='ordinary skilllist',source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fixture_scripts={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('scripts/chica_timed_support.py','scripts/chica_ordinary_rules.py','scripts/phase_d_chain_probe.py')},
        ability_enum=dict(enum,default=n.default(enum['index'])),damage_type_enum=damage_enum,
        cached_type_field=next(f for f in n.fields(719) if f['name']=='_PowerDrain'),source_records=selected,record_count=133,
        field_counts=counts,present_field_count=sum(counts.values()),source_absence_counts={f:133-counts[f] for f in FIELDS},sample_ids=sorted(sample_ids),native_check_count=len(checks),
        probability_field_presence={f:sum(f in r['raw'] for r in selected) for f in ('param1','param2','param3')},default_support2_bounds=bounds,
        fragments={name:[hex(a),hex(b)] for name,(a,b) in ranges.items()},reused_proofs=reused,
        methods=[n.method(i) for i in (4309,6343,7104,7222,7223,7225)],
        limits=['Only ordinary99 present param7 attack delta, param9 incoming delta, param0 positive time or source-1 sentinel; no absent field filled.',
            'Real installed-array/type filtering and IsEnableAbility99 execute; supplied installed array/bit-cache are not installation evidence.',
            'Outer Attack checks returned damage>=1 and broad ability-presence predicate (predicate/returned damage supplied); full Attack/Attacked and final HP not run.',
            'Normal0 uses param1, Skill1 uses param3, Critical2 uses param2; current present thresholds all1; absent runtime getters0 skip before RNG. Draws supplied, not random statistics.',
            'Self support uses param4/6, target support uses param7/9 and same param0; only target fields generalized. Target is the caller target, no enemy-faction selector in this handler.',
            'Both submissions use Support2 and multiCheck=true; actual repeat matching/replacement, death/wave resets and cross-category final stacking remain outside scope.',
            'Source-1 stores-1 and bypasses positive countdown; with no bad-status/alive-function conditions this update retains it. No unconditional forever claim.',
            'Support time store executes bounded native code; update executes with managed item access/removal modeled and ParamsUpdate intercepted. Engine values/allocations modeled; base submissions captured.'])
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,limits=trace['limits']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=133,present_fields=sum(counts.values()),sample_records=len(sample_ids),native_checks=len(checks))))


if __name__=='__main__':main()
