"""TimeWedge normal5 / ClockUp8 constant and CharaStatus game timer."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from phase_d_chain_probe import Guest,BASE,fbits
from unicorn.arm64_const import UC_ARM64_REG_S8

OUT=Path('output/card_comparison_cid30236/wedge_time')


class WedgeGuest(Guest):
    def __init__(self,raw):
        super().__init__(raw,{})
        self.alive=True;self.resurrecting=False

    def hook(self,cpu,address,size,unused):
        rva=address-BASE
        if rva==0x1535abc:self.ret(int(self.alive))
        elif rva==0x15349ec:self.ret(int(self.resurrecting))
        elif rva in (0x13a884c,0x11b8494,0x154cb4c,0x1548120):self.ret()  # visuals/status/motion side effects.
        else:super().hook(cpu,address,size,unused)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.open(encoding='utf-8')]
    row=next(r for r in records if r['table']=='skilllist' and r['raw'].get('skillid')==43023600)
    assert row['raw']['ability']==1110 and row['raw']['param0']==1
    card=next(r for r in records if r['table']=='charainfo' and r['raw'].get('cid')==30236)
    assert card['raw']['Aparam']>>25&1==1
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    instruction=next(d.disasm(n.raw[0x13a8830:0x13a8834],0x13a8830));assert instruction.mnemonic=='fmov' and instruction.op_str=='s1, #5.00000000'
    constant=dict(record_key='NATIVE::9093::0x13a8830',table='NATIVE_METHOD',record_id=9093,field_path='/instructions/0x13a8830/immediate',raw_value=5.0,
        original_file='work/protection/il2cpp_loader_seed1.bin',source_sha256=hashlib.sha256(n.raw).hexdigest(),location=dict(kind='native_rva',rva='0x13a8830',byte_begin=0x13a8830,byte_end_exclusive=0x13a8834,raw_hex=n.raw[0x13a8830:0x13a8834].hex()),instruction='fmov s1, #5.00000000')
    ranges=dict(mode_initialize=(0x13a7f58,0x13a7f78),mode_from_setup=(0x10b4af4,0x10b4b5c),mode_to_initialize=(0x10b4c24,0x10b4c3c),
        enemy_list=(0x13a8110,0x13a8134),delay_delivery=(0x13a8dc0,0x13a8dd8),
        select_and_set=(0x13a87b4,0x13a884c),status_timer=(0x176e300,0x176e3b4),
        delta_input=(0x176c934,0x176c940),timer_countdown=(0x176cab0,0x176cae0))
    cctor_end=min(x for x in n.pointers if x>0x15764a4)
    ins=list(d.disasm(n.raw[0x15764a4:cctor_end],0x15764a4));j=next(j for j,i in enumerate(ins) if i.mnemonic=='strh' and '#0x13e]' in i.op_str)
    ranges['clockup1112_cached']=(ins[j-4].address,ins[j].address+4)
    assert any(i.mnemonic=='mov' and i.op_str=='w0, #0x458' for i in ins[j-4:j])
    j=next(j for j,i in enumerate(ins) if i.mnemonic=='strh' and '#0x13c]' in i.op_str)
    ranges['timestopcount1111_cached']=(ins[j-4].address,ins[j].address+4)
    assert any(i.mnemonic=='mov' and i.op_str=='w0, #0x457' for i in ins[j-4:j])
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    enemy=n.default(next(f['index'] for f in n.fields(729) if f['name']=='ENEMY'));assert enemy['value']==1
    trace=dict(native_sha256=constant['source_sha256'],metadata_sha256=hashlib.sha256(m.raw).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_records=[row,card],code_constants=[constant],enemy_enum=enemy,
        fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},methods=[n.method(i) for i in (9086,9088,9093,7019,6979)],
        limits='Normal TimeWedge mode0 input5; ClockUp mode1 uses8. Full party mode/eligibility and visual coroutine excluded; current timer adds positive input.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    g=WedgeGuest(n.raw);wedge=g.alloc(0x40);chara=g.alloc(0x300);status=g.alloc(0x300);g.put64(chara+0xa0,status);g.put64(status+0xc0,chara);g.put64(chara+0x48,g.alloc(0x100))
    checks=[]
    for mode,before,alive,resurrect,want in ((0,0,True,False,5),(1,0,True,False,8),(0,2,True,False,7),(0,0,False,False,0),(0,0,True,True,0)):
        g.uc.mem_write(wedge+0x24,bytes([mode]));g.uc.mem_write(status+0x164,struct.pack('<f',before));g.alive=alive;g.resurrecting=resurrect
        g.run(0x13a87b4,wedge,chara,0);actual=struct.unpack('<f',g.uc.mem_read(status+0x164,4))[0];assert actual==want
        checks.append(dict(name=f'set_mode{mode}_before{before}_alive{alive}_resurrect{resurrect}',clock_up_mode=mode,before=before,alive=alive,resurrecting=resurrect,timer_after=actual,passed=True))
    for before,delta,want in ((5,.25,4.75),(.25,.25,0),(.25,.5,0),(0,.5,0)):
        g.uc.mem_write(status+0x164,struct.pack('<f',before));g.uc.reg_write(UC_ARM64_REG_S8,fbits(delta));g.setreg(19,status)
        g.run(0x176cab0,stop=0x176cae0);actual=struct.unpack('<f',g.uc.mem_read(status+0x164,4))[0];assert actual==want
        checks.append(dict(name=f'countdown_{before}_{delta}',before=before,delta=delta,timer_after=actual,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Alive/resurrection qualification, status visuals and motion side effects supplied; full TimeWedgeSkill.SetTimeStop and CharaStatus timer arithmetic execute.',
            'Countdown delta supplied; unit chain reuses same BattleManager.GetDeltaTime evidence. Does not prove all enemies/current party mode/actual motion immunity.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),normal_game_seconds=5,clock_up_game_seconds=8)))


if __name__=='__main__':main()
