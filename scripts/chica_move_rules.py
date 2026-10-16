"""Selected movement and attack-interval contributions, with explicit context."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_timed_support import TimedGuest
from phase_d_chain_probe import BASE,STACK,fbits,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_X29

OUT=Path('output/card_comparison_cid30236/movement')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    ids=(43023605,43023606,43023607,65000001,65000002,43023608,43023609,43023616)
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('skillid') in ids]
    rows={r['raw']['skillid']:r['raw'] for r in selected};assert len(rows)==8
    card=next(r for r in records if r['table']=='charainfo' and r['raw'].get('cid')==30236)
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ranges=dict(walk_self_dispatch=(0x1118a14,0x1118a40),walk_small_types=(0x1118be4,0x1118c4c),
        party1008=(0x15977c8,0x1597894),party1017=(0x1597a34,0x1597b04),
        wave65_move=(0x15466f8,0x1546708),wave64_move=(0x1545fb4,0x1545fc4),
        enemy_move=(0x1121e24,0x1121e34),support_move_sum=(0x172ea5c,0x172eb24),
        interval_type7=(0x111a008,0x111a1c4),interval_clip=(0x111a200,0x111a21c),
        interval_caller=(0x1007524,0x1007558),set_attack_time=(0x1539c58,0x1539ca8))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic=='bl':note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_records=selected,card_record=card,fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},
        methods=[n.method(i) for i in (4191,8890,4197,4911)]+[n.method(i) for i in n.method_by_rva[0x1539c58]],scope='Selected local movement multipliers / Support2 increments / 7.param7 interval multiplier; not final animation cadence.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    checks=[]
    def sf(g,i,value):g.uc.reg_write(UC_ARM64_REG_S0+i,fbits(value))
    def rf(g,i):return fvalue(g.uc.reg_read(UC_ARM64_REG_S0+i))
    for sid in (43023605,43023606,43023607,65000001,65000002):
        for enabled in (True,False):
            g=TimedGuest(n.raw,rows);g.enabled=enabled;g.stage=enabled;obj=g.skill(sid);ability=rows[sid]['ability']
            if ability in (7,1095):
                g.setreg(26,obj);g.setreg(19,g.alloc(0x100));sf(g,8,1.2)
                g.run(0x1118a14,ability,stop=0x1118c4c);result=rf(g,8)
            else:
                frame=STACK+0xe0000;g.uc.reg_write(UC_ARM64_REG_X29,frame);g.uc.mem_write(frame-0x94,struct.pack('<f',1.2));g.setreg(19,obj)
                if ability==1008:g.run(0x1597824,stop=0x1597894)
                else:
                    g.setreg(21,0);g.uc.mem_write(frame-0x160,struct.pack('<I',1 if enabled else 32))
                    g.run(0x1597a98,stop=0x1597b04)
                result=struct.unpack('<f',g.uc.mem_read(frame-0x94,4))[0]
            want=1.2*(rows[sid]['param2'] if enabled else 1);assert abs(result-want)<1e-6,(sid,enabled,result,want)
            checks.append(dict(name=f'{sid}_move_{enabled}',skill_id=sid,field='param2',raw=rows[sid]['param2'],enabled=enabled,initial=1.2,result=result,passed=True))
    for sid,start,end,sreg,dreg,field in ((43023608,0x15466f8,0x1546708,24,25,'param2'),(43023609,0x1545fb4,0x1545fc4,23,28,'param2'),(43023616,0x1121e24,0x1121e34,23,24,'param8')):
        g=TimedGuest(n.raw,rows);obj=g.skill(sid);data=g.alloc(0x60);g.setreg(sreg,obj);g.setreg(dreg,data)
        g.run(start,obj,stop=end);stored=struct.unpack('<f',g.uc.mem_read(data+0x1c,4))[0];assert stored==fvalue(fbits(rows[sid][field]))
        checks.append(dict(name=f'{sid}_move_to_data',skill_id=sid,field=field,raw=rows[sid][field],stored=stored,passed=True))
        entry=g.alloc(0x80);g.put64(entry+0x50,data);ctrl=g.alloc(0x40);g.put64(ctrl+0x10,g.collection([entry]))
        g.uc.mem_write(BASE+0x2bd3580,b'\1');g.run(0x172ea5c,ctrl);result=rf(g,0)
        assert abs(result-1-stored)<1e-6
        checks.append(dict(name=f'{sid}_move_sum',result=result,passed=True))
    for enabled in (True,False):
        g=TimedGuest(n.raw,rows);g.enabled=enabled;obj=g.skill(43023607);g.setreg(21,obj);g.setreg(19,g.alloc(0x100));sf(g,9,1)
        g.run(0x111a008,7,stop=0x111a1c4);result=rf(g,9);assert abs(result-(.75 if enabled else 1))<1e-6
        checks.append(dict(name=f'interval_7_{enabled}',skill_id=43023607,field='param7',raw=.75,enabled=enabled,result=result,passed=True))
    g=TimedGuest(n.raw,{});sf(g,0,card['raw']['atkspeed']);sf(g,9,.75);sf(g,8,0)
    g.run(0x1539c80,stop=0x1539c88);interval=rf(g,0);assert interval==1.125
    checks.append(dict(name='nominal_card_interval_times_ability',source_atkspeed=card['raw']['atkspeed'],ability_factor=.75,other_factors=1,offset=0,nominal_interval=interval,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Source installation/list and stage eligibility supplied; 1017 self/job-mask gate executes.',
            'Timing sample uses original atkspeed1.5 with neutral other factors, not final observed hit cadence.',
            'Support2 local addition/clamp tested, not whole-battle stacking.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),fields=9)))


if __name__=='__main__':main()
