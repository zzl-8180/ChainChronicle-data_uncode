"""Boss66 field duration: source getter to GroundManager deltaTime counter."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from phase_d_chain_probe import Guest,BASE,fbits,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_S8

OUT=Path('output/card_comparison_cid30236/field_time')


class FieldGuest(Guest):
    def hook(self,cpu,address,size,unused):
        if address==BASE+0x1ebd478:
            cpu.reg_write(UC_ARM64_REG_S0,fbits(self.delta));self.ret()
        else:super().hook(cpu,address,size,unused)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    selected=[r for r in records if (r['table']=='bossskill' and r['raw'].get('skillid')==43023613) or (r['table']=='bosspattern' and r['raw'].get('patternid') in (43023603,43023604)) or (r['table']=='skilllist' and r['raw'].get('skillid') in (43023603,43023610))]
    row=next(r for r in selected if r['table']=='bossskill')
    assert row['raw']['skillid0']==66 and row['raw']['skillparam5']==300
    assert len(selected)==5
    for sid,pid in ((43023603,43023603),(43023610,43023604)):
        assert next(r for r in selected if r['table']=='skilllist' and r['raw']['skillid']==sid)['raw']['str0']==str(pid)
        assert next(r for r in selected if r['table']=='bosspattern' and r['raw']['patternid']==pid)['raw']['skillid0']==43023613
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    branch=0x1297d4c+n.unpack('<H',0x206ee04+66*2)[0]*4;assert branch==0x12989a4
    ranges=dict(dispatch66=(branch,branch+36),source_getter=(0x1a6e6d4,0x1a6e6ec),source_to_util=(0x1181ab4,0x1181ad0),
        exec66=(0x1196b38,0x1196d9c),start_field=(0x156abd0,0x156ade8),counter=(0x1568ad8,0x1568b40),
        return_field=(0x1568bf8,0x1568d1c),battle_update_gate=(0x15687cc,0x15687fc),delta_wrapper=(0x1ebd478,0x1ebd4a0))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    string_rva=0x209ad1c;icall=n.raw[string_rva:n.raw.index(b'\0',string_rva)].decode();assert icall=='UnityEngine.Time::get_deltaTime()'
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_records=selected,fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},methods=[n.method(i) for i in (5351,7687,7689)],
        data_fields=n.fields(774),delta_icall=dict(rva=hex(string_rva),text=icall),limits='Positive source duration only; full trigger, graphics and other field overwrites excluded.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    g=FieldGuest(n.raw,{});obj=g.alloc(0x100);param=g.alloc(0x20);util=g.alloc(0x100)
    g.floats[param]=(43023613,'skillparam5',300,'SOURCE');g.put64(obj+0x48,param)
    g.setreg(19,util);g.setreg(20,obj);g.run(0x1181ac0,obj,stop=0x1181ad0)
    actual=struct.unpack('<f',g.uc.mem_read(util+0x40,4))[0];assert actual==300
    checks=[dict(name='source_getter_to_util_param5',source_value=300,util_value=actual,passed=True)]
    g.setreg(19,util);g.run(0x1196c10,stop=0x1196c14);g.run(0x1196d48,stop=0x1196d4c)
    actual=fvalue(g.uc.reg_read(UC_ARM64_REG_S0));assert actual==300
    checks.append(dict(name='exec66_passes_change_time_unchanged',change_time=actual,passed=True))
    g.run(0x156ac2c,stop=0x156ac30)
    ground=g.alloc(0x200);data=g.alloc(0x50);g.put64(ground+0x148,data)
    g.setreg(20,ground);g.setreg(21,3);g.setreg(22,1);g.setreg(23,4)
    g.run(0x156ad58,stop=0x156ad98)
    duration=struct.unpack('<f',g.uc.mem_read(data+0x18,4))[0]
    assert duration==300 and g.u32(data+0x1c)==0 and g.uc.mem_read(data+0x10,1)==b'\1'
    checks.append(dict(name='start_field_stores_duration_and_zero_counter',duration=duration,counter=0,active=True,passed=True))
    for before,delta,want,expired in ((0,0,0,False),(299,.5,299.5,False),(299.5,.5,300,True),(299.5,1,300.5,True)):
        g.uc.mem_write(data+0x1c,struct.pack('<f',before));g.delta=delta;g.setreg(19,ground)
        g.run(0x1568b14,stop=0x1568b40 if expired else 0x1568b38)
        after=struct.unpack('<f',g.uc.mem_read(data+0x1c,4))[0];assert after==want
        checks.append(dict(name=f'counter_{before}_{delta}',before=before,delta=delta,after=after,expiry_branch=expired,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['ParamS float getter and Unity deltaTime supplied; source getter/copy, duration pass/store, counter addition and threshold branch execute.',
            'Does not run complete field switch/graphics/return, early death return or actual trigger installation.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),duration_game_seconds=300,delta_icall=icall)))


if __name__=='__main__':main()
