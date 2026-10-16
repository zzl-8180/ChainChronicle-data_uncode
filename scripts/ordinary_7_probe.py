"""TargetStage eligibility with actual current-stage/BG flag and effect paths.

Run IsEnableAbility7, IsTargetStage, GroundManager.GetStageNo, GetBgFlag and
bounded attack/defence dispatch/getter/multiply. Database row selection and
engine ParamS access are explicit models; installation and full combat excluded.
"""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_S8,UC_ARM64_REG_X29
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_timed_support import TimedGuest
from phase_d_chain_probe import Guest,BASE,fbits,fvalue

OUT=Path('output/ordinary_effects/ability7')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')


def indices(code):return [v for v in (code%100,(code//100)%100,(code//10000)%100) if v]


class StageGuest(TimedGuest):
    def __init__(self,native,rows,backgrounds):
        super().__init__(native,rows)
        self.metadata(0x29e8dc0)
        for flag in (0x2bd01b1,0x2bcf5c0,0x2bd2b45):self.uc.mem_write(BASE+flag,b'\1')
        self.ground=self.alloc(0x200);self.change=self.alloc(0x20);self.battle=self.alloc(0x40);self.database=self.alloc(0x40)
        self.put64(self.statics[0x29e8dc0]+0xb0,self.ground);self.put64(self.ground+0x148,self.change)
        self.backgrounds=backgrounds;self.bg_reads=[]

    def configure_stage(self,stage_id,override=None):
        self.put32(self.battle+0x18,stage_id);self.uc.mem_write(self.change+0x10,bytes([override is not None]))
        self.put32(self.change+0x14,override or 0)

    def hook(self,cpu,address,size,unused):
        a=address-BASE
        if a in (0x1112574,0x1117e60):Guest.hook(self,cpu,address,size,unused)
        elif a==0x18008e0:self.ret(self.battle)
        elif a==0x1801e78:self.ret(self.database)
        elif a==0x1a71320:
            sid=self.reg(1)&0xffffffff;row=self.backgrounds.get(sid);self.bg_reads.append(sid)
            if row is None:self.ret(0)
            else:
                obj=self.alloc(0x40);self.put32(obj+0x10,sid);self.put32(obj+0x14,row['flag']);self.ret(obj)
        else:super().hook(cpu,address,size,unused)


def main():
    records=[json.loads(s) for s in SOURCE.open(encoding='utf-8')]
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('ability')==7]
    bgs=[r for r in records if r['table']=='battle_bg'];backgrounds={r['raw']['id']:r['raw'] for r in bgs}
    assert len(selected)==64 and len(bgs)==99 and len(backgrounds)==99
    assert all(all(f in r['raw'] for f in ('param0','param1','param3')) for r in selected)
    codes=sorted({r['raw']['param0'] for r in selected});assert len(codes)==13
    assert all(type(c) is int and c>0 and all(0<i<32 for i in indices(c)) for c in codes)
    rows={r['raw']['skillid']:r['raw'] for r in selected}
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    enum=next(f for f in n.fields(718) if f['name']=='TargetStage');assert n.default(enum['index'])['value']==7
    ranges=dict(eligibility_dispatch=(0x1112720,0x1112750),eligibility_param0=(0x1112fd8,0x1113034),
        target_stage=(0x1117e60,0x1117fd8),current_stage=(0x156aa54,0x156aad4),bg_flag_getter=(0x1a71454,0x1a7146c),
        attack_dispatch=(0x1107680,0x11076ac),attack_type_gate=(0x1107940,0x110797c),attack_multiply=(0x1107c84,0x1107c88),
        defence_dispatch=(0x1107fec,0x1108020),defence_gate_multiply=(0x1108104,0x1108148))
    OUT.mkdir(parents=True,exist_ok=True)
    for name,(a,b) in ranges.items():
        lines=[]
        for ins in d.disasm(n.raw[a:b],a):
            ids=n.method_by_rva.get(int(ins.op_str[1:],16),[]) if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#0x') else []
            note=' ; '+','.join(n.method(i)['declaring_type']+'.'+n.method(i)['name'] for i in ids) if ids else ''
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    checks=[];g=StageGuest(n.raw,rows,backgrounds);code_matches={}
    # All observed encodings against the small related BG table, reusing one guest.
    for code in codes:
        code_matches[code]=[];mask=sum(1<<i for i in set(indices(code)))
        for record in bgs:
            bg=record['raw'];sid=bg['id'];g.configure_stage(sid);result,_=g.run(0x1117e60,code)
            want=bool(mask&bg['flag']&0xfffffffe);assert result==int(want)
            if want:code_matches[code].append(sid)
            checks.append(dict(name=f'condition_{code}_bg{sid}',param0=code,background_id=sid,background_flag=bg['flag'],matches=bool(result),passed=True))
    # Code-only fixtures exercise the zero shortcut, third group and ignored bit0.
    g.backgrounds[999998]={'flag':1}  # synthetic bit0-only row, never exported as source
    for code,sid,want in ((0,999999,True),(200004,4,True),(200004,100,True),(200004,2,False),(100,4,False),(100,999998,False),(4,999999,False)):
        g.configure_stage(sid);reads=len(g.bg_reads);result,_=g.run(0x1117e60,code);assert result==int(want)
        if code==0:assert len(g.bg_reads)==reads
        checks.append(dict(name=f'code_fixture_{code}_bg{sid}',fixture_param0=code,background_id=sid,matches=bool(result),source_value_fixture_only=True,
                           synthetic_background_flag=1 if sid==999998 else None,passed=True))
    g.backgrounds.pop(999998)
    for base,override,want in ((4,2,False),(2,4,True)):
        g.configure_stage(base,override);result,_=g.run(0x1117e60,4);assert result==int(want) and g.bg_reads[-1]==override
        checks.append(dict(name=f'current_stage_{base}_override{override}',base_stage_id=base,override_stage_id=override,condition_param0=4,matches=bool(result),passed=True))
    # Cover every numeric value and encoding, including the unusual enemy values.
    sample_ids={43023607,102071};seen=set()
    for field in ('param0','param1','param3'):
        seen.clear()
        for r in selected:
            value=r['raw'][field]
            if value not in seen:seen.add(value);sample_ids.add(r['raw']['skillid'])
    for sid in sorted(sample_ids):
        raw=rows[sid];passing=code_matches[raw['param0']][0]
        for field in ('param1','param3'):
            for sid_bg in (passing,1):
                h=StageGuest(n.raw,{sid:raw},backgrounds);h.configure_stage(sid_bg);obj=h.skill(sid)
                h.setreg(22,h.alloc(0xa80));h.setreg(23,1);h.setreg(21,1);h.uc.reg_write(UC_ARM64_REG_X29,obj)
                h.uc.reg_write(UC_ARM64_REG_S8,fbits(1.2))
                a,b=(0x1107680,0x1107c88) if field=='param1' else (0x1107fec,0x1108148)
                h.run(a,7,stop=b);actual=fvalue(h.uc.reg_read(UC_ARM64_REG_S8));qualifies=sid_bg==passing
                expected=fvalue(fbits(fvalue(fbits(1.2))*fvalue(fbits(raw[field] if qualifies else 1))))
                assert actual==expected
                assert h.reads==[dict(source_id=sid,field='param0',raw=raw['param0'],origin='SOURCE')]+([dict(source_id=sid,field=field,raw=raw[field],origin='SOURCE')] if qualifies else [])
                checks.append(dict(name=f'effect_{sid}_{field}_bg{sid_bg}',skill_id=sid,field=field,raw_value=raw[field],param0=raw['param0'],background_id=sid_bg,
                    qualifies=qualifies,initial_factor=1.2,result=actual,expected_float32=expected,reads=h.reads,passed=True))
    for stage_id,want in ((4,True),(2,False)):
        g.configure_stage(stage_id);obj=g.skill(102071);result,_=g.run(0x1112574,g.alloc(0xa80),obj,0);assert result==int(want)
        checks.append(dict(name=f'102071_code_vs_text_bg{stage_id}',skill_id=102071,source_param0=4,background_id=stage_id,code_matches=bool(result),source_text_unchanged=True,passed=True))
    bg_indices=sorted({i for c in codes for i in indices(c)})
    labels={i:dict(index=i,bit=1<<i,background_ids=[r['raw']['id'] for r in bgs if r['raw']['flag']&(1<<i)],
                   background_names_ja=list(dict.fromkeys(r['raw']['bg_name'] for r in bgs if r['raw']['flag']&(1<<i))),
                   status='SOURCE_BG_NAMES_WITH_SHARED_BIT_NOT_A_UNIQUE_DISPLAY_ENUM') for i in bg_indices}
    prior=Path('output/card_comparison_cid30236/ordinary_rules/trace.json');old=json.loads(prior.read_text(encoding='utf-8'))
    assert old['native_sha256']==hashlib.sha256(n.raw).hexdigest()
    trace=dict(effect_type=7,namespace='ordinary skilllist',source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fixture_scripts={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('scripts/chica_timed_support.py','scripts/chica_ordinary_rules.py','scripts/phase_d_chain_probe.py')},
        reused_proof=dict(path=str(prior),sha256=hashlib.sha256(prior.read_bytes()).hexdigest()),ability_enum=dict(enum,default=n.default(enum['index'])),
        source_records=selected,background_source_records=bgs,record_count=64,present_field_count=192,field_counts=dict(param0=64,param1=64,param3=64),
        param0_values=codes,code_background_matches=code_matches,terrain_bit_sources=labels,sample_ids=sorted(sample_ids),native_check_count=len(checks),
        fragments={name:[hex(a),hex(b)] for name,(a,b) in ranges.items()},
        eligibility_jump=dict(table_rva='0x206dc28',entry_index=6,raw_hex=n.raw[0x206dc34:0x206dc36].hex(),target=hex(0x1112750+int.from_bytes(n.raw[0x206dc34:0x206dc36],'little')*4)),
        methods=[n.method(i) for i in (7683,34643)],background_row_fields=n.fields(4304),current_stage_field=next(f for f in n.fields(775) if f['name']=='_bgChangeCurrentData'),
        limits=['Only current CACHE ordinary7 present param0/param1/param3; no other TargetStage types or fields generalized.',
            'Positive source integer param0 splits into up to three base100 groups, each becoming a BG flag bit; bit0 ignored. Source values use first two groups and bits2..25; zero/third group are code-only fixtures.',
            'IsEnable7/IsTargetStage/current-stage and BG flag getter execute; database get returns the selected actual source BG row. Installation and exact runtime lookup population remain outside scope.',
            'BG names are row labels; one bit may match multiple labels or combined flags. No invented unique official Chinese enum for shared night/sea bits.',
            'param1 multiplies local attack factor; param3 multiplies incoming factor, including source2/250. Derived reduction may be negative; never clamp source to0/1.',
            '102071 source name says desert/text says forest; source param0=4 matches desert-flag16 and rejects forest-flag4. Original text and discrepancy retained.',
            'Actual installed/unlocked state, sub-effect installation/activation, other fields and final battle HP remain outside scope.'])
    assert trace['eligibility_jump']['target']=='0x1112fd8'
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,limits=trace['limits']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=64,fields=192,background_records=99,sample_records=len(sample_ids),native_checks=len(checks))))


if __name__=='__main__':main()
