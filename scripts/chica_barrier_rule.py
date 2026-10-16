"""Boss16 shield fixed-guard coefficient; no assumed automatic request multiplier."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_ordinary_rules import LocalGuest
from phase_d_chain_probe import fbits,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_S8

OUT=Path('output/card_comparison_cid30236/barrier')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    row=next(r for r in records if r['table']=='bossskill' and r['raw'].get('skillid')==43023614)
    assert row['raw']['skillid0']==16 and row['raw']['skillparam1']==2
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ranges=dict(type16_shield_arguments=(0x11884b4,0x118856c),receiver_fixed_guard=(0x1776ab8,0x1776b00))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic=='bl':note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_records=[row],fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},
        methods=[n.method(i) for i in (5398,7085)],normal_atk_basis='Reuse ../boss_chain/type13_basis/trace.json: receiver current normalAtk; nominal player construction scale .1 is conditional')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    checks=[]
    for normal,request,want in ((2500,1,5000),(2500,1.2,6000),(2500,.25,1250),(13,1,26)):
        g=LocalGuest(n.raw,{});util=g.alloc(0x200);target=g.alloc(0x200);status=g.alloc(0x300);bp=g.alloc(0x200);iv=g.alloc(0x20);data=g.alloc(0x80)
        g.put64(target+0xa0,status);g.put64(status+0xc0,target);g.put64(target+0x28,bp);g.put64(bp+0x70,iv);g.integers[iv]=normal
        for off,val in ((0x18,request),(0x30,2),(0x34,10),(0x40,1)):
            g.uc.mem_write(util+off,struct.pack('<f',val))
        g.setreg(22,util);g.setreg(25,target);g.setreg(23,194806)
        g.run(0x11884f0,stop=0x1188568)
        coefficient=fvalue(g.uc.reg_read(UC_ARM64_REG_S0));assert abs(coefficient-request*2)<1e-6 and g.reg(2)==10
        g.setreg(19,status);g.setreg(20,data);g.uc.reg_write(UC_ARM64_REG_S8,fbits(coefficient))
        g.run(0x1776ab8,stop=0x1776afc)
        actual=g.u32(data+0x14);assert actual==want,(normal,request,actual,want)
        checks.append(dict(normal_atk=normal,request_factor=request,raw_param1=2,shield_coefficient=coefficient,stored_fixed_guard=actual,charges=10,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Receiver normalAtk and request factor are explicit inputs; not actual automatic-trigger context.',
            'Arguments not relevant to guard coefficient use neutral fixture values; missing source fields stay missing in exports.',
            'Screenshot nominal5% would require request factor .25 under the same .1 player basis; that actual trigger factor is unverified.',
            'No final shield mitigation, flag interpretation or full barrier lifecycle executed.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),raw_param1=2)))


if __name__=='__main__':main()
