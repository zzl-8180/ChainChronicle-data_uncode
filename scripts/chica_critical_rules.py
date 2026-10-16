"""Confirm Always3 critical probability and critical-damage baseline separately."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_timed_support import TimedGuest
from phase_d_chain_probe import BASE,STACK,fbits,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_X29

OUT=Path('output/card_comparison_cid30236/critical')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    ids=(43023601,65000001,43023607,43023606,43023608,43023609,43023612,43023613,43023614,43023611)
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('skillid') in ids]
    rows={r['raw']['skillid']:r['raw'] for r in selected};assert len(rows)==len(ids)
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ranges=dict(damage_baseline_and_dispatch=(0x153c95c,0x153c9d8),
        attack_always3_list=(0x153b5ac,0x153b614),attack_critical_base=(0x153b6d4,0x153b710),
        chance_dispatch_and_add=(0x1105e0c,0x1105e60),chance_always3_caller=(0x10ff37c,0x10ff47c),
        stage7_chance=(0x11192e4,0x1119388),stage7_damage=(0x11199fc,0x1119a6c),
        stage1008_chance=(0x159dae8,0x159dbb4),stage1008_damage=(0x15a0a38,0x15a0afc),
        wave64_critical=(0x1545fd4,0x1545fec),wave65_critical=(0x1546718,0x1546730),
        support2012_critical=(0x11a5004,0x11a5030),support2012_store=(0x11a5080,0x11a5090),
        support2012_duration=(0x11a4fb0,0x11a4fcc),support2012_apply=(0x11a50d4,0x11a5118),
        sympathy_critical=(0x15a7ca8,0x15a7cc4),support_chance_sum=(0x172ebec,0x172ecb4),
        support_damage_sum=(0x172ecb4,0x172ed7c),attack_support_critical=(0x153b630,0x153b710))
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
        methods=[n.method(i) for i in (6343,6344,4092,4093)],
        damage_baseline=dict(value=1.5,subtraction_rva='0x153c960',add_back_rva='0x153b6e4'),
        scope='Selected card critical fields only; each ability family retains its own field mapping and baseline.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    checks=[]
    def sf(g,i,value):g.uc.reg_write(UC_ARM64_REG_S0+i,fbits(value))
    def rf(g,i):return fvalue(g.uc.reg_read(UC_ARM64_REG_S0+i))
    for sid in (43023601,65000001):
        for seed in (0,.25):
            g=TimedGuest(n.raw,rows);obj=g.skill(sid);g.setreg(23,obj);g.setreg(19,0)
            sf(g,8,seed);sf(g,10,-1.5);g.run(0x153c980,stop=0x153c9d8)
            result=rf(g,8);want=seed+rows[sid]['param6']-1.5;assert abs(result-want)<1e-6
            checks.append(dict(name=f'{sid}_damage_delta_seed{seed}',skill_id=sid,field='param6',raw=rows[sid]['param6'],baseline=1.5,initial_delta=seed,resulting_delta=result,passed=True))
        # Actual attack adds the 1.5 base back; unrelated critical additions supplied as zero.
        g=TimedGuest(n.raw,rows);sf(g,8,rows[sid]['param6']-1.5);sf(g,9,0)
        g.run(0x153b6e4,stop=0x153b6f0);result=rf(g,2);assert result==rows[sid]['param6']
        checks.append(dict(name=f'{sid}_critical_base_added_back',resulting_critical_factor=result,passed=True))
    for seed in (0,.4):
        g=TimedGuest(n.raw,rows);obj=g.skill(65000001);g.setreg(22,obj);g.setreg(19,0);sf(g,8,seed)
        g.run(0x1105e0c,stop=0x1105e60);result=rf(g,8);assert abs(result-seed-.4)<1e-6
        checks.append(dict(name=f'65000001_probability_seed{seed}',skill_id=65000001,field='param5',raw=.4,initial_probability=seed,resulting_probability=result,passed=True))
    # Stage7 uses param5 for probability and param6 for damage, directly additive.
    for field,start,end in (('param5',0x11191a8,0x11195bc),('param6',0x1119930,0x1119dd0)):
        for enabled in (True,False):
            g=TimedGuest(n.raw,rows);g.enabled=enabled;obj=g.skill(43023607)
            g.setreg(27,obj);g.setreg(19,g.alloc(0x100));g.setreg(21,0);g.setreg(26,1)
            g.uc.reg_write(UC_ARM64_REG_X29,1);sf(g,9,.2)
            g.run(start,7,stop=end);result=rf(g,9);assert abs(result-(.2+(.05 if enabled else 0)))<1e-6
            checks.append(dict(name=f'7_{field}_{enabled}',skill_id=43023607,field=field,raw=.05,enabled=enabled,initial_delta=.2,result=result,passed=True))
    for field,start,end,offset in (('param4',0x159db44,0x159dbb4,0xa4),('param5',0x15a0a8c,0x15a0afc,0x94)):
        for enabled in (True,False):
            g=TimedGuest(n.raw,rows);g.stage=enabled;obj=g.skill(43023606);frame=STACK+0xe0000
            g.uc.reg_write(UC_ARM64_REG_X29,frame);g.uc.mem_write(frame-offset,struct.pack('<f',.2));g.setreg(19,obj)
            g.run(start,stop=end);result=struct.unpack('<f',g.uc.mem_read(frame-offset,4))[0];assert abs(result-(.2+(.125 if enabled else 0)))<1e-6
            checks.append(dict(name=f'1008_{field}_{enabled}',skill_id=43023606,field=field,raw=.125,enabled=enabled,initial_delta=.2,result=result,passed=True))
    # Preserve the distinct mapping for each timed effect family.
    for sid in (43023608,43023609,43023612,43023613,43023614,43023611):
        g=TimedGuest(n.raw,rows);obj=g.skill(sid);data=g.alloc(0x60)
        if sid==43023608:
            fields=('param4','param6');g.setreg(24,obj);g.setreg(25,data);g.run(0x1546718,obj,stop=0x1546730)
        elif sid==43023609:
            fields=('param4','param8');g.setreg(23,obj);g.setreg(28,data);g.run(0x1545fd4,obj,stop=0x1545fec)
        elif rows[sid]['ability']==2012:
            fields=('param4','param5');g.setreg(19,obj);g.run(0x11a5004,stop=0x11a5030)
            g.setreg(21,data);g.run(0x11a5088,stop=0x11a508c)
        else:
            fields=(None,'param8');closure=g.alloc(0x40);g.put64(closure+0x10,obj);g.put64(closure+0x20,data);g.setreg(20,closure)
            g.run(0x15a7ca8,stop=0x15a7cc4)
        actual=struct.unpack('<ff',g.uc.mem_read(data+0x24,8))
        for field,value in zip(fields,actual):
            if field is not None:assert value==fvalue(fbits(rows[sid][field]))
        checks.append(dict(name=f'{sid}_critical_mapping',skill_id=sid,fields=list(fields),stored_chance=actual[0],stored_damage=actual[1],passed=True))
        entry=g.alloc(0x80);g.put64(entry+0x50,data);ctrl=g.alloc(0x40);g.put64(ctrl+0x10,g.collection([entry]))
        for field,offset,start in ((fields[0],0,0x172ebec),(fields[1],1,0x172ecb4)):
            if field is None:continue
            g.uc.mem_write(BASE+(0x2bd3582 if offset==0 else 0x2bd3583),b'\1')
            g.run(start,ctrl);result=rf(g,0);assert result==actual[offset]
            checks.append(dict(name=f'{sid}_{field}_sum_from_zero',skill_id=sid,field=field,raw=rows[sid][field],result=result,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Skill installation/type-list membership supplied; source values are unchanged.',
            'Probability direct addition and critical-damage subtraction/add-back execute separately.',
            'No random draw, whole-battle critical cap, other source stacking or final HP simulated.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),fields=18)))


if __name__=='__main__':main()
