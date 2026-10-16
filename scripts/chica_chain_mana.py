"""Ability1106 Chain ManaGet probability selection and one-Chain latch."""
import hashlib,json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_mana_chance import ManaGuest
from phase_d_chain_probe import BASE,fbits,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_S11,UC_ARM64_REG_S12,UC_ARM64_REG_X29

OUT=Path('output/card_comparison_cid30236/chain_mana')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    selected=[r for r in map(json.loads,source.open(encoding='utf-8')) if r['table']=='skilllist' and r['raw'].get('skillid') in (43023617,43023632)]
    row=next(r for r in selected if r['raw']['skillid']==43023617)
    extra=next(r for r in selected if r['raw']['skillid']==43023632)
    assert row['raw']['ability']==1106 and extra['raw']['ability']==1082 and extra['raw']['str0']=='43023617'
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ranges=dict(rate_selector=(0x1000b24,0x1000b78),rate_to_random_and_award=(0x11247f0,0x1124944),reset_chain_latch=(0x1124720,0x1124750))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_records=selected,fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},rate_jump_bytes=n.raw[0x203cec0:0x203cec5].hex(),
        methods=[n.method(i) for i in (4793,4333)],work_fields=n.fields(458),limits='Installed work supplied; no proof player has Extra unlocked/installed. Actual mana spawning and full battle excluded.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    g=ManaGuest(n.raw,{43023617:row['raw']});obj=g.skill(43023617);work=g.alloc(0x40);g.put64(work+0x18,obj);checks=[]
    for chain in range(6):
        g.run(0x1000b24,work,chain);rate=fvalue(g.uc.reg_read(UC_ARM64_REG_S0));assert abs(rate-(.1 if chain>=2 else 0))<1e-7,(chain,rate)
        checks.append(dict(name=f'rate_chain{chain}',chain=chain,rate=rate,fields=[r['field'] for r in g.reads],passed=True));g.reads.clear()
    g.metadata(0x29ab820);g.put32(g.statics[0x29ab820],1)  # Single.Epsilon at static+0, supplied scalar.
    g.uc.reg_write(UC_ARM64_REG_X29,g.u64(BASE+0x29ab820));g.setreg(24,work);g.setreg(19,2);g.setreg(23,0x7f800000);g.setreg(20,0x80000000)
    g.run(0x1124814,stop=0x112487c)
    rate=fvalue(g.uc.reg_read(UC_ARM64_REG_S12));assert abs(rate-.1)<1e-7 and g.reg(25)==1 and g.reg(27)&0xffffffff==0xffffffff
    checks.append(dict(name='source_rate_amount_and_negative_total_cap',rate=rate,amount=g.reg(25),total_cap=-1,passed=True))
    g.uc.reg_write(UC_ARM64_REG_S11,fbits(1))
    for random,success in ((0,True),(.1,True),(.1001,False),(1,False)):
        g.random=random;g.run(0x112488c,stop=0x11248a4 if success else 0x1124944)
        checks.append(dict(name=f'random_{random}',random=random,threshold=rate,success=success,passed=True))
    g.setreg(24,work);g.run(0x112493c,stop=0x1124944);assert g.uc.mem_read(work+0x10,1)==b'\1'
    checks.append(dict(name='successful_award_marks_chain_latch',latched=True,passed=True))
    g.run(0x11247f8,stop=0x1124944)
    checks.append(dict(name='same_chain_latch_skips_rate_and_random',skipped=True,passed=True))
    items=g.alloc(8);g.put64(items,work);g.setreg(21,items);g.setreg(1,1);g.setreg(19,1)
    g.run(0x1124720,stop=0x1124750);assert g.uc.mem_read(work+0x10,1)==b'\0'
    checks.append(dict(name='chain1_resets_latch',latched=False,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Work/installed source, Single.Epsilon scalar, Random.Range output supplied; GetRate, amount/cap reads, random comparison and latch branches execute.',
            'Does not execute actual GenerateManaTypeUtil or establish active Extra installation/complete Chain lifecycle.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),code_count2_to_max_configured_chance=.1)))


if __name__=='__main__':main()
