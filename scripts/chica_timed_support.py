"""Wave / enemy-debuff mapping to TimePowerUpData and Support2 local factors."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_ordinary_rules import LocalGuest
from phase_d_chain_probe import BASE,fbits,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_S8

OUT=Path('output/card_comparison_cid30236/timed_support')


class TimedGuest(LocalGuest):
    def __init__(self,raw,rows):
        super().__init__(raw,rows)
        for slot in (0x29c4f90,0x29ad260):self.metadata(slot)
        for flag in (0x2bd357e,0x2bd357f,0x2bd3581):self.uc.mem_write(BASE+flag,b'\1')

    def skill(self,sid):
        obj=super().skill(sid)
        for i in range(6,10):
            key=f'param{i}';off=0x30+i*8
            if key in self.rows[sid] and not self.u64(obj+off):
                p=self.alloc(0x20);self.floats[p]=(sid,key,self.rows[sid][key],'SOURCE');self.put64(obj+off,p)
        return obj


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('skillid') in (43023608,43023609,43023616,43023611)]
    rows={r['raw']['skillid']:r['raw'] for r in selected};assert len(rows)==4
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ranges=dict(wave64_mapping=(0x1545df8,0x154607c),wave65_mapping=(0x1546540,0x15467c0),
        drain_enemy_mapping=(0x1121e0c,0x1121e94),drain_duration=(0x1121cc8,0x1121cdc),
        support_data_duration=(0x1777598,0x17775b4),attack_addition=(0x172e938,0x172e984),
        defence_addition=(0x172eb9c,0x172ebe4),incoming_support2=(0x1771d80,0x1771dc8),
        game_delta=(0x176c92c,0x176c940),delta_to_support=(0x176ccf8,0x176cd10),
        support_time_countdown=(0x172e55c,0x172e578),sympathy_mapping=(0x15a7c54,0x15a7c8c),
        sympathy_duration=(0x15a7cfc,0x15a7d18),sympathy_support3=(0x155b2cc,0x155b330),
        skill_attack_addition=(0x172e938,0x172ea5c))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic=='bl':note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_records=selected,fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},
        cached_type_fields=[f for f in n.fields(719) if f['name'] in ('_WaveSupport','_WaveSupportAll','_PowerDrain')],
        time_power_fields=n.fields(697),methods=[n.method(i) for i in (6372,4309,7222,7225,6985,6979)])
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    g=TimedGuest(n.raw,rows);data={};checks=[]
    for sid,a,b,skill_reg,data_reg in ((43023609,0x1545f9c,0x1545fec,23,28),(43023608,0x15466e0,0x1546730,24,25),(43023616,0x1121e0c,0x1121e3c,23,24)):
        obj=g.skill(sid);p=g.alloc(0x60);g.setreg(skill_reg,obj);g.setreg(data_reg,p);g.run(a,stop=b)
        actual={name:struct.unpack('<f',g.uc.mem_read(p+off,4))[0] for name,off in [('attack',0x10),('defence',0x20)]}
        fields=('param7','param9') if sid==43023616 else ('param1','param3')
        assert actual['attack']==fvalue(fbits(rows[sid][fields[0]])) and actual['defence']==fvalue(fbits(rows[sid][fields[1]]))
        data[sid]=p;checks.append(dict(name=f'{sid}_source_to_time_data',skill_id=sid,fields=list(fields),stored=actual,passed=True))
    obj=g.skill(43023611);closure=g.alloc(0x40);p=g.alloc(0x60)
    g.put64(closure+0x10,obj);g.put64(closure+0x20,p);g.setreg(20,closure);g.setreg(22,p)
    g.run(0x15a7c5c,stop=0x15a7c8c)
    normal,skill=struct.unpack('<ff',g.uc.mem_read(p+0x14,8))
    assert normal==skill==fvalue(fbits(.1));g.setreg(20,closure)
    g.run(0x15a7cfc,stop=0x15a7d18)
    assert struct.unpack('<f',g.uc.mem_read(closure+0x28,4))[0]==45
    data[43023611]=p;checks.append(dict(name='sympathy_normal_skill_and_duration',skill_id=43023611,normal=normal,skill=skill,duration=45,passed=True))
    # Execute actual Support2 additive aggregate; default clamp [0.5,2] stays active.
    for ids,want_attack,want_def in (((43023608,),1.15,.85),((43023609,),1.1,.9),((43023608,43023609),1.25,.75),((43023616,),.7,1.3),((43023611,),1.1,1)):
        entries=[]
        for sid in ids:
            p=g.alloc(0x80);g.put64(p+0x50,data[sid]);entries.append(p)
        ctrl=g.alloc(0x40);g.put64(ctrl+0x10,g.collection(entries))
        outputs=[]
        for a in (0x172e8c0,0x172eb24):
            g.run(a,ctrl);outputs.append(fvalue(g.uc.reg_read(UC_ARM64_REG_S0)))
        assert abs(outputs[0]-want_attack)<1e-6 and abs(outputs[1]-want_def)<1e-6,(ids,outputs)
        checks.append(dict(name='aggregate_'+','.join(map(str,ids)),records=list(ids),attack_factor=outputs[0],incoming_factor=outputs[1],passed=True))
    g.run(0x172e98c,ctrl);skill_factor=fvalue(g.uc.reg_read(UC_ARM64_REG_S0));assert abs(skill_factor-1.1)<1e-6
    checks.append(dict(name='sympathy_skill_aggregate',skill_factor=skill_factor,passed=True))
    # Real 64 class-mask gate: source iParam0=1 accepts job0, rejects job1.
    for job,expected in ((0,0x1545f4c),(1,0x15460d0)):
        h=TimedGuest(n.raw,rows);target=h.alloc(0x200);bp=h.alloc(0x200);iv=h.alloc(0x20)
        h.put64(target+0x28,bp);h.put64(bp+0xf8,iv);h.integers[iv]=job
        h.setreg(27,target);h.setreg(19,rows[43023609]['iParam0']);h.run(0x1545f00,stop=expected)
        checks.append(dict(name=f'wave64_job_{job}',job=job,mask=1,qualifies=job==0,passed=True))
    # Positive countdown subtracts game delta. Time unit follows existing GetDeltaTime/fixedDeltaTime proof.
    for seconds,delta,want in ((120,.25,119.75),(30,.25,29.75),(45,.25,44.75)):
        h=TimedGuest(n.raw,{});entry=h.alloc(0x80);h.uc.mem_write(entry+0x30,struct.pack('<f',seconds))
        h.setreg(0,entry);h.uc.reg_write(UC_ARM64_REG_S8,fbits(delta));h.run(0x172e55c,stop=0x172e578)
        actual=struct.unpack('<f',h.uc.mem_read(entry+0x30,4))[0];assert actual==want
        checks.append(dict(name=f'countdown_{seconds}',initial_seconds=seconds,delta=delta,remaining=actual,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Source list/targets/installation supplied; mapping, type2 aggregation and 64 job gate execute.',
            'Support2 same-category addition and default clamp tested; no whole-battle stacking or final HP.',
            'Time game-delta chain is static, with bounded countdown arithmetic; no wall-clock assertion.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),records=len(rows))))


if __name__=='__main__':main()
