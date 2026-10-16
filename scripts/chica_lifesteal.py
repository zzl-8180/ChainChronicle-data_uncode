"""Ability21 critical lifesteal amount, ordinary flag packing and Heal cap."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_timed_support import TimedGuest
from phase_d_chain_probe import BASE,STACK,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_X29

OUT=Path('output/card_comparison_cid30236/lifesteal')


class HealGuest(TimedGuest):
    def __init__(self,raw,rows,constants):
        super().__init__(raw,rows)
        static=self.statics[0x29bda68]
        self.put64(static+0x38,constants['mask']['value'])
        self.put64(static+0x50,self.array(constants['values']['values'],'f'))
        self.put64(static+0x58,self.array(constants['bits']['values'],'i'))
        for flag in (0x2bd2c0d,0x2bcd363):self.uc.mem_write(BASE+flag,b'\1')

    def hook(self,cpu,address,size,unused):
        a=address-BASE
        if a==0xa92640:self.integers[self.reg(0)]=self.reg(1)&0xffffffff;self.ret()
        elif a==0x143732c:
            # Existing bounded positive-add adapter; no game arithmetic changes.
            assert self.reg(0)<100000 and self.reg(1)<100000
            self.ret(self.reg(0)+self.reg(1))
        else:super().hook(cpu,address,size,unused)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    row=next(r for r in records if r['table']=='skilllist' and r['raw'].get('skillid')==65000003)
    assert row['raw']['ability']==21 and row['raw']['param1']==.25 and row['raw']['flag0_1']==512
    constants_path=Path('output/boss_heal/constants.json');constants=json.loads(constants_path.read_text(encoding='utf-8'))
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ranges=dict(returned_damage=(0x153c0a8,0x153c0d4),damage_to_hp_ability=(0x153c324,0x153c338),
        type21_list_and_rates=(0x154067c,0x1540724),amount_math=(0x1540dcc,0x1540ec8),
        ordinary_flag_pack=(0x1dbff78,0x1dc0000),heal_flag_mask=(0x1540730,0x154077c),
        heal_delivery=(0x1540d2c,0x1540d74),heal_cap=(0x15413bc,0x15414cc))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic=='bl':note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        constants_sha256=hashlib.sha256(constants_path.read_bytes()).hexdigest(),source_records=[row],
        fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},methods=[n.method(i) for i in (6345,6348,38652)],
        high_word_literal=n.literal(0x29a6070),basis='Target Attacked return value passed as dmg into subAttackAbilityHP; not necessarily actual HP loss after overkill.',
        limits='Current installation and full battle excluded; only source-specific amount and flag/cap path.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    checks=[];rows={65000003:row['raw']}
    for damage_type,damage,want in ((2,1000,250),(2,1001,250),(2,4,1),(2,1,0),(0,1000,0),(1,1000,0)):
        g=HealGuest(n.raw,rows,constants);obj=g.skill(65000003);frame=STACK+0xe0000
        g.uc.reg_write(UC_ARM64_REG_X29,frame);g.put32(frame-0xe8,damage);g.put32(frame-0xe4,damage_type);g.setreg(20,obj)
        g.run(0x15406e4,stop=0x1540724);result=g.reg(0)&0xffffffff;assert result==want,(damage_type,damage,result,want)
        checks.append(dict(name=f'amount_type{damage_type}_damage{damage}',damage_type=damage_type,damage_input=damage,raw_param1=.25,heal_amount=result,passed=True))
    g=HealGuest(n.raw,rows,constants);obj=g.skill(65000003);g.setreg(19,obj);g.setreg(21,0)
    g.run(0x1dbffdc,512,stop=0x1dbfffc);packed=g.reg(1);assert packed==1<<41
    frame=STACK+0xe0000;g.uc.reg_write(UC_ARM64_REG_X29,frame);g.setreg(19,g.u64(BASE+0x29bda68));g.setreg(23,packed)
    g.run(0x154075c,stop=0x154077c);retained=g.u64(frame-0xd8);assert retained==packed
    checks.append(dict(name='flag0_1_512_packs_and_survives_heal_mask',raw_high_word=512,packed=packed,retained=retained,passed=True))
    g.run(0x1578404,retained);rate=fvalue(g.uc.reg_read(UC_ARM64_REG_S0));assert abs(rate-1.4)<1e-6
    checks.append(dict(name='actual_source_flag_overheal_rate',flag=retained,rate=rate,passed=True))
    for maximum,current,amount,want in ((1000,1000,250,1250),(1000,1300,250,1400),(1000,1400,250,1400),(1000,1500,100,1500),(1001,1400,250,1401)):
        g=HealGuest(n.raw,{},constants);chara=g.alloc(0x300);bp=g.alloc(0x100);mx=g.alloc(0x20);hp=g.alloc(0x20)
        g.put64(chara+0x28,bp);g.put64(bp+0x58,mx);g.put64(bp+0x68,hp);g.integers[mx]=maximum;g.integers[hp]=current
        g.setreg(19,chara);g.setreg(20,retained);g.setreg(24,amount);g.setreg(25,current);g.setreg(27,g.u64(BASE+0x29bda68))
        g.run(0x15413bc,current,stop=0x15414cc);actual=g.integers[hp];assert actual==want,(maximum,current,actual,want)
        checks.append(dict(name=f'cap_{maximum}_{current}_{amount}',hp_max=maximum,hp_before=current,heal_amount=amount,hp_after=actual,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Missing param0/2 use previously verified native constructor defaults in fixture; source exports retain missing fields.',
            'Type-list installation supplied; amount caller/selector, native flag pack/mask, GetOverHealRate and cap fragment execute.',
            'ParamS getter/setter, initialized static arrays and small-positive addition modeled; no full Heal entry eligibility or final battle.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),critical_ratio=.25,overheal_rate=rate)))


if __name__=='__main__':main()
