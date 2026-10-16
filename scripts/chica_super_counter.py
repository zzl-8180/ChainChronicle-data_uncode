"""Shared K/SSympathy count10 native constant and readiness flag."""
import hashlib,json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from phase_d_chain_probe import Guest,BASE

OUT=Path('output/card_comparison_cid30236/super_counter')


class CounterGuest(Guest):
    def hook(self,cpu,address,size,unused):
        if address==BASE+0x1584c08:self.ret()  # GUI count refresh only.
        else:super().hook(cpu,address,size,unused)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.open(encoding='utf-8')]
    selected=[r for r in records if (r['table']=='charainfo' and r['raw'].get('cid')==30236) or (r['table']=='bosspattern' and r['raw'].get('patternid')==43023602)]
    assert len(selected)==2 and next(r for r in selected if r['table']=='charainfo')['raw']['pattern2']==43023602
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    instruction=next(d.disasm(n.raw[0x1584b30:0x1584b34],0x1584b30));assert instruction.mnemonic=='cmp' and instruction.op_str=='w8, #0xa'
    constant=dict(record_key='NATIVE::8828::0x1584b30',table='NATIVE_METHOD',record_id=8828,field_path='/instructions/0x1584b30/immediate',raw_value=10,
        original_file='work/protection/il2cpp_loader_seed1.bin',source_sha256=hashlib.sha256(n.raw).hexdigest(),location=dict(kind='native_rva',rva='0x1584b30',byte_begin=0x1584b30,byte_end_exclusive=0x1584b34,raw_hex=n.raw[0x1584b30:0x1584b34].hex()),instruction='cmp w8, #0xa')
    ranges=dict(start_skill_event=(0x1295db8,0x1295e28),counter_and_dispatch=(0x1584b10,0x1584bf4),set_and_use_super=(0x112a8c0,0x112a928))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=constant['source_sha256'],metadata_sha256=hashlib.sha256(m.raw).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_records=selected,code_constants=[constant],
        fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},methods=[n.method(i) for i in (5178,8828,4529,4530,4531,4532)],
        limits='Shared party counter, not cid-specific master numeric field. Eligible event/SSympathy installation supplied; actual party dispatch/selection excluded.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    g=CounterGuest(n.raw,{});pm=g.alloc(0x200);g.put64(pm+0x58,g.alloc(8));checks=[]
    for before,after,threshold in ((0,1,False),(8,9,False),(9,10,True)):
        g.uc.mem_write(pm+0xd8,bytes([before]));g.setreg(19,pm)
        g.run(0x1584b18,stop=0x1584b38 if threshold else 0x1584bf4)
        assert g.uc.mem_read(pm+0xd8,1)==bytes([after])
        checks.append(dict(name=f'counter_{before}_to_{after}',before=before,after=after,threshold_reached=threshold,passed=True))
    g.run(0x1584b38,stop=0x1584b40);assert g.uc.mem_read(pm+0xd8,1)==b'\0'
    checks.append(dict(name='threshold_resets_shared_counter',counter=0,passed=True))
    bp=g.alloc(0xb00);g.uc.mem_write(bp+0xa50,b'\1');g.uc.mem_write(bp+0xa52,b'\1')
    g.run(0x112a8c0,bp);g.run(0x112a8d4,bp);assert g.reg(0)==1
    checks.append(dict(name='eligible_super_set_ready',can_super=True,passed=True))
    g.run(0x112a8fc,bp);g.run(0x112a8d4,bp);assert g.reg(0)==0 and g.uc.mem_read(bp+0x92b,1)==b'\1'
    checks.append(dict(name='super_use_consumes_ready',can_super=False,executing=True,passed=True))
    g.run(0x112a910,bp);assert g.uc.mem_read(bp+0x92b,1)==b'\0'
    checks.append(dict(name='finish_clears_executing',executing=False,passed=True))
    g.uc.mem_write(bp+0xa52,b'\0');g.run(0x112a8c0,bp);g.run(0x112a8d4,bp);assert g.reg(0)==0
    checks.append(dict(name='missing_super_ability_does_not_enable',can_super=False,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['GUI refresh bypassed; real increment/threshold/reset and BattleParam readiness/use/finish functions execute.',
            'Event qualification, installed skill and party iteration eligibility not emulated.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),threshold=10)))


if __name__=='__main__':main()
