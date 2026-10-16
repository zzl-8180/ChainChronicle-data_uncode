"""Bounded cid30236 ordinary attack / incoming-damage factors, not battle totals."""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from phase_d_chain_probe import Guest, BASE, STACK, fbits, fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0, UC_ARM64_REG_S8, UC_ARM64_REG_X29

OUT=Path('output/card_comparison_cid30236/ordinary_rules')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')


class LocalGuest(Guest):
    def __init__(self,raw,rows,enabled=True,stage=True):
        super().__init__(raw,rows)
        self.metadata(0x29bab78)
        self.uc.mem_write(BASE+0x2bd24ed,b'\1')
        self.enabled,self.stage=enabled,stage
        self.qualifiers=[]

    def skill(self,sid):
        obj=super().skill(sid)
        if obj and not self.u64(obj+0x80):
            # iParam0 is present only where sourced; no absent source value is exported as zero.
            row=self.rows[sid]
            if 'iParam0' in row:
                p=self.alloc(0x20);self.integers[p]=row['iParam0'];self.put64(obj+0x80,p)
        return obj

    def hook(self,cpu,address,size,unused):
        a=address-BASE
        if a==0x1112574:
            self.qualifiers.append(dict(kind='IsEnableAbility',supplied=self.enabled))
            self.ret(int(self.enabled))
        elif a==0x1117e60:
            self.qualifiers.append(dict(kind='IsTargetStage',input=self.reg(0),supplied=self.stage))
            self.ret(int(self.stage))
        else:super().hook(cpu,address,size,unused)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    records=[json.loads(s) for s in SOURCE.read_text(encoding='utf-8').splitlines()]
    ids=(43023601,43023605,43023606,43023607,65000001,65000002,102070,102071,75000012,75000102,75015002,75015102)
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('skillid') in ids]
    assert len(selected)==len(ids)
    rows={r['raw']['skillid']:r['raw'] for r in selected}
    ranges=dict(self_attack_dispatch=(0x1107680,0x11076ac),self_attack_small_types=(0x1107944,0x110797c),
        self_attack_multiply=(0x1107c84,0x1107c88),self_defence_dispatch=(0x1107fec,0x1108020),
        self_defence_gate=(0x1108108,0x1108148),
        family1008_index=(0x1576c14,0x1576c28),family1017_index=(0x1576c78,0x1576c8c),
        party_stage_attack=(0x1594274,0x159434c),party_stage_defence=(0x159a99c,0x159aa68),
        party_job_attack=(0x15944ec,0x15945c0),party_job_defence=(0x159ac1c,0x159ace8),
        defence_caller=(0x153d394,0x153d3bc),incoming_multiply=(0x153d74c,0x153d770),
        list_type_filter=(0x10ffa0c,0x10ffaa0))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):
                note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        methods=[n.method(i) for i in (4189,4192,8887,8892,7348,6355)],
        fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},
        cached_type_fields=[f for f in n.fields(719) if f['name'] in ('_TargetStageAll','_StrengthJob2')],
        source_records=selected,
        limits='Only configured local factors; installation, player unlock, full stacking and final HP loss excluded.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    checks=[]
    for sid in ids:
        row=rows[sid];ability=row['ability']
        for field in ('param1','param3'):
            if sid in (43023601,102070,102071,75000012,75000102,75015002,75015102) and field=='param3':continue
            for gate in (True,False):
                g=LocalGuest(n.raw,rows,enabled=gate,stage=gate);obj=g.skill(sid)
                frame=STACK+0xe0000;g.uc.reg_write(UC_ARM64_REG_X29,frame)
                g.uc.reg_write(UC_ARM64_REG_S8,fbits(1.2))
                if ability in (1095,7):
                    g.setreg(22,g.alloc(0x100));g.setreg(23,1);g.setreg(21,1)
                    g.uc.reg_write(UC_ARM64_REG_X29,obj)
                    start,end=(0x1107680,0x1107c88) if field=='param1' else (0x1107fec,0x1108148)
                    g.run(start,ability,stop=end)
                    actual=fvalue(g.uc.reg_read(UC_ARM64_REG_S8))
                elif ability in (1008,1017):
                    # Enter after existing party/type list selection; type identity is retained in trace.
                    g.uc.mem_write(frame-0x94,struct.pack('<f',1.2))
                    if ability==1008:
                        g.setreg(19,obj);g.setreg(25,0x7f800000)
                        start,end=(0x15942e0,0x159434c) if field=='param1' else (0x159aa04,0x159aa68)
                    else:
                        # Actual param0/self and iParam0/job-mask gate execute, including negative mask case.
                        g.setreg(19,obj);g.setreg(25,0x7f800000);g.setreg(21,0);g.setreg(27,1 if gate else 32)
                        g.put32(frame-0x150,1 if gate else 32)
                        start,end=(0x1594560,0x15945c0) if field=='param1' else (0x159ac84,0x159ace8)
                    g.run(start,stop=end)
                    actual=struct.unpack('<f',g.uc.mem_read(frame-0x94,4))[0]
                else:raise ValueError(ability)
                want=1.2*(row[field] if gate else 1)
                assert abs(actual-want)<2e-6,(sid,field,gate,actual,want)
                checks.append(dict(name=f'{sid}_{field}_gate_{gate}',skill_id=sid,ability=ability,field=field,
                    raw=row[field],initial_factor=1.2,result=actual,qualifier=gate,passed=True))
    # Confirm the caller uses the defence result as an incoming-damage multiplier, before later guard/HP stages.
    for factor,want in ((.5,500),(.85,850),(.875,875),(.95,950),(1,1000)):
        g=LocalGuest(n.raw,{});frame=STACK+0xe0000;g.uc.reg_write(UC_ARM64_REG_X29,frame)
        g.put32(frame-0xa8,1000);g.uc.reg_write(UC_ARM64_REG_S8,fbits(factor))
        g.uc.reg_write(UC_ARM64_REG_S8+1,fbits(1))
        g.run(0x153d74c,stop=0x153d770)
        actual=g.u32(frame-0xa8);assert actual==want,(factor,actual,want)
        checks.append(dict(name=f'incoming_factor_{factor}',input_damage=1000,defence_factor=factor,
            result_before_later_stages=actual,passed=True))
    result=dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Engine ParamS/list and source installation use explicit fixtures.',
            'IsEnableAbility and stage eligibility supplied; exact installed player state is not proven.',
            'For 1017 the native self/param0 and job-mask checks execute; list selection itself is static evidence.',
            'Caller block tests incoming multiplier only; later barriers, fixed guard, rounding and HP excluded.'])
    (OUT/'native_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),records=len(selected))))


if __name__=='__main__':main()
