"""Ability28 source-specific ManaHunter probability thresholds and terrain bonus."""
import hashlib,json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_timed_support import TimedGuest
from phase_d_chain_probe import BASE,STACK,fbits,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_S1,UC_ARM64_REG_S8,UC_ARM64_REG_S9,UC_ARM64_REG_X29

OUT=Path('output/card_comparison_cid30236/mana_chance')


class ManaGuest(TimedGuest):
    def hook(self,cpu,address,size,unused):
        if address==BASE+0x19072ec:
            assert fvalue(cpu.reg_read(UC_ARM64_REG_S0))==0 and fvalue(cpu.reg_read(UC_ARM64_REG_S1))==1
            cpu.reg_write(UC_ARM64_REG_S0,fbits(self.random));self.ret()
        else:super().hook(cpu,address,size,unused)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    row=next(r for r in map(json.loads,source.open(encoding='utf-8')) if r['table']=='skilllist' and r['raw'].get('skillid')==43023602)
    assert row['raw']['ability']==28
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ranges=dict(type28_cached=(0x15766c4,0x15766d8),type28_list=(0x1544398,0x1544418),
        damage_and_terrain=(0x1544f38,0x15450a0),random_threshold=(0x15450f8,0x1545114),
        source_terrain_flag=(0x15447c0,0x1544844),rng_wrapper=(0x19072ec,0x190732c))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    address=0x207888c;rng=n.raw[address:n.raw.index(b'\0',address)].decode();assert rng=='UnityEngine.Random::Range(System.Single,System.Single)'
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_records=[row],
        fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},methods=[n.method(i) for i in (6358,6359)],rng_icall=dict(rva=hex(address),text=rng),
        limits='Single eligible installed source supplied; full death/installation and mana generation excluded. Terrain flag16 corresponds to described desert candidate, runtime stage lookup not emulated.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    checks=[]
    for damage_type in (0,1,2):
        for terrain in (0,16):
            g=ManaGuest(n.raw,{43023602:row['raw']});obj=g.skill(43023602);frame=STACK+0xe0000
            g.uc.reg_write(UC_ARM64_REG_X29,frame);g.put32(frame-0x80,damage_type);g.put32(frame-0x7c,terrain)
            for reg,value in ((20,0),(21,0),(22,0x80000000),(23,g.alloc(4)),(25,g.alloc(4)),(28,1)):g.setreg(reg,value)
            g.uc.reg_write(UC_ARM64_REG_S8,0);g.uc.reg_write(UC_ARM64_REG_S9,0)
            g.run(0x1544f38,obj,stop=0x15450a0)
            base=fvalue(g.uc.reg_read(UC_ARM64_REG_S9));bonus=fvalue(g.uc.reg_read(UC_ARM64_REG_S8))
            assert abs(base-.2)<1e-7 and abs(bonus-(.8 if terrain else 0))<1e-7
            checks.append(dict(name=f'select_type{damage_type}_terrain{terrain}',damage_type=damage_type,terrain_flag=terrain,base=base,bonus=bonus,fields=[r['field'] for r in g.reads],passed=True))
            if damage_type:continue
            samples=((0,True),(.2,True),(.2001,False),(1,False)) if not terrain else ((0,True),(.2,True),(.9999,True),(1,True))
            for random,success in samples:
                g.random=random;g.run(0x15450f8,stop=0x1545114 if success else 0x15451b4)
                threshold=fvalue(g.uc.reg_read(UC_ARM64_REG_S1));assert abs(threshold-(1 if terrain else .2))<1e-7
                checks.append(dict(name=f'random_terrain{terrain}_{random}',terrain_flag=terrain,random=random,threshold=threshold,success=success,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Eligibility/list source and damage type/terrain flag supplied; real parameter getters, terrain mask, selection and random comparison execute.',
            'Random.Range output supplied at 0..1; confirms configured threshold, not statistical RNG distribution or complete mana awarding.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),base_threshold=.2,terrain16_threshold=1)))


if __name__=='__main__':main()
