"""TargetStageAll: real type filtering, current terrain and party contribution.

Reuse the terrain interpreter proved for7. Installed arrays, engine scalars and
candidate membership are fixtures; no installation or full battle simulation.
"""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_PC,UC_ARM64_REG_X29
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from ordinary_7_probe import StageGuest,indices
from phase_d_chain_probe import BASE,STACK,fbits,fvalue

OUT=Path('output/ordinary_effects/ability1008')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')


class PartyStageGuest(StageGuest):
    def __init__(self,native,rows,backgrounds,values):
        super().__init__(native,rows,backgrounds)
        self.metadata(0x29b5f18)
        self.put64(self.statics[0x29bda68]+0x18,self.array(values,'I'))
        self.flag_index=values.index(1008)
        self.uc.mem_write(self.statics[0x29e25e0]+0xb6,struct.pack('<H',self.flag_index))
        self.guard_boundaries=set();self.guard_reached=None

    def installed(self,bp,ids):
        self.put64(bp+0x1e0,self.array([self.skill(sid) for sid in ids]))
        cid=self.alloc(0x20);self.integers[cid]=1;self.put64(bp+0x48,cid)
        bits=self.alloc(0x20);self.put64(bits+0x10,self.array([0]*16,'I'));self.put32(bits+0x18,512);self.put64(bp+0x398,bits)
        if any(self.rows[sid]['ability']==1008 for sid in ids):self.run(0x13caf74,bits,self.flag_index,1,0)

    def hook(self,cpu,address,size,unused):
        if address-BASE in self.guard_boundaries:
            self.guard_reached=address-BASE;self.slice_done=True;cpu.emu_stop()
        else:super().hook(cpu,address,size,unused)


def effect_case(native,record,backgrounds,values,bg_id,same=False,job=0,override=None,installed=True,other=None):
    raw=record['raw'];sid=raw['skillid'];rows={sid:raw}
    if other is not None:rows[other['skillid']]=other
    g=PartyStageGuest(native,rows,backgrounds,values);g.configure_stage(bg_id,override)
    receiver=g.alloc(0xa80);provider=receiver if same else g.alloc(0xa80)
    p=g.alloc(0x20);g.integers[p]=job;g.put64(receiver+0xf8,p)
    g.installed(provider,([sid] if installed else [])+([other['skillid']] if other else []))
    frame=STACK+0xe0000;g.uc.reg_write(UC_ARM64_REG_X29,frame)
    buf=g.alloc(64);g.put64(frame-0x1a8,buf);g.put64(frame-0x1b0,buf)
    cell=g.alloc(8);g.put64(cell,provider)
    mask=sum(1<<i for i in set(indices(raw['param0'])))
    qualifies=installed and bool(mask&backgrounds[override or bg_id]['flag']&0xfffffffe)
    results=[]
    for field in ('param1','param3'):
        g.uc.mem_write(frame-0x94,struct.pack('<f',1.2));g.reads=[];g.eligibility=[]
        g.setreg(25,0x7f800000)
        if field=='param1':
            g.run(0x15935ec,0,receiver,stop=0x15935f8);assert g.reg(24)==receiver
            g.setreg(24,receiver);g.setreg(28,provider)
            g.run(0x1594258,stop=0x1594368)
        else:
            g.run(0x1599d24,0,receiver,0,0,0,stop=0x1599d34);assert g.reg(21)==receiver
            g.setreg(24,receiver);g.setreg(25,cell);g.setreg(28,g.u64(BASE+0x29e25e0))
            g.run(0x159a974,stop=0x159aa84)
        actual=struct.unpack('<f',g.uc.mem_read(frame-0x94,4))[0]
        expected=fvalue(fbits(fvalue(fbits(1.2))*fvalue(fbits(raw[field] if qualifies else 1))))
        assert actual==expected,(sid,field,bg_id,same,actual,expected)
        assert len(g.eligibility)==int(installed),(sid,field,g.eligibility)
        assert all(r['source_id']==sid for r in g.reads),(sid,field,g.reads)
        assert any(r['field']==field for r in g.reads)==qualifies
        results.append(dict(name=f'effect_{sid}_{field}_bg{bg_id}_same{same}_job{job}_override{override}_installed{installed}_other{bool(other)}',
            skill_id=sid,field=field,raw_value=raw[field],param0=raw['param0'],background_id=bg_id,override_background_id=override,
            provider_is_receiver=same,receiver_job_fixture=job,installed_fixture=installed,other_type_id=other['skillid'] if other else None,
            qualifies=qualifies,initial_factor=1.2,result=actual,expected_float32=expected,reads=g.reads,
            real_eligibility_calls=len(g.eligibility),passed=True))
    return results


def main():
    records=[json.loads(s) for s in SOURCE.open(encoding='utf-8')]
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('ability')==1008]
    bgs=[r for r in records if r['table']=='battle_bg'];backgrounds={r['raw']['id']:r['raw'] for r in bgs}
    assert len(selected)==37 and all(all(f in r['raw'] for f in ('param0','param1','param3')) for r in selected)
    prior=Path('output/ordinary_effects/ability7/trace.json');old=json.loads(prior.read_text(encoding='utf-8'))
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    assert old['native_sha256']==hashlib.sha256(n.raw).hexdigest() and old['background_source_records']==bgs
    enum=next(f for f in n.fields(718) if f['name']=='TargetStageAll');assert n.default(enum['index'])['value']==1008
    values=sorted(set(n.default(f['index'])['value'] for f in n.fields(718) if f['name']!='value__'))
    codes=sorted({r['raw']['param0'] for r in selected});new_codes=[c for c in codes if str(c) not in old['code_background_matches']]
    matches={str(c):old['code_background_matches'][str(c)] for c in codes if c not in new_codes};checks=[]
    g=PartyStageGuest(n.raw,{r['raw']['skillid']:r['raw'] for r in selected},backgrounds,values)
    for code in new_codes:
        matches[str(code)]=[]
        for bg in bgs:
            raw=bg['raw'];g.configure_stage(raw['id']);result,_=g.run(0x1117e60,code)
            expected=bool(sum(1<<i for i in set(indices(code)))&raw['flag']&0xfffffffe)
            assert result==int(expected)
            if expected:matches[str(code)].append(raw['id'])
            checks.append(dict(name=f'new_condition_{code}_bg{raw["id"]}',param0=code,background_id=raw['id'],background_flag=raw['flag'],matches=bool(result),passed=True))
    for r in selected:
        for bg in (matches[str(r['raw']['param0'])][0],1):checks+=effect_case(n.raw,r,backgrounds,values,bg)
    control=next(r for r in selected if r['raw']['skillid']==43023606)
    for same in (True,False):
        for job in range(6):checks+=effect_case(n.raw,control,backgrounds,values,4,same,job)
    for base,override in ((2,4),(4,2)):checks+=effect_case(n.raw,control,backgrounds,values,base,override=override)
    other=next(r['raw'] for r in records if r['table']=='skilllist' and r['raw'].get('skillid')==43023607)
    for present in (True,False):checks+=effect_case(n.raw,control,backgrounds,values,4,installed=present,other=other)
    # Run actual IsAlive and active guard. Inactive members take a separate backup
    # path, not the1008 block; do not replace that path with an all-party claim.
    for field in ('param1','param3'):
        for hp,active,want in ((100,1,'ACTIVE'),(0,1,'DEAD'),(100,0,'BACKUP'),(0,0,'DEAD')):
            h=PartyStageGuest(n.raw,{},backgrounds,values);actor=h.actor(hp,100);h.uc.mem_write(actor+0x118,bytes([active]))
            frame=STACK+0xe0000;h.uc.reg_write(UC_ARM64_REG_X29,frame)
            if field=='param1':
                start=0x1593970;bounds={0x159398c:'ACTIVE',0x1595530:'DEAD',0x1593a54:'BACKUP'};h.setreg(22,actor)
            else:
                start=0x159a040;bounds={0x159a070:'ACTIVE',0x159bd88:'DEAD',0x159a128:'BACKUP'};h.setreg(23,actor)
            h.guard_boundaries=set(bounds);h.run(start);assert bounds[h.guard_reached]==want
            checks.append(dict(name=f'provider_{field}_hp{hp}_active{active}',field=field,hp_fixture=hp,active_fixture=active,route=want,passed=True))
    manager=g.alloc(0x100);lists=[g.alloc(0x30) for _ in range(3)]
    for off,p in zip((0x68,0x70,0x78),lists):g.put64(manager+off,p)
    for kind,index in ((0,1),(1,2),(2,0)):
        result,_=g.run(0x10b62a0,manager,kind,0);assert result==lists[index]
        checks.append(dict(name=f'candidate_list_kind{kind}',kind=kind,selected_offset=hex((0x68,0x70,0x78)[index]),passed=True))
    ranges=dict(attack_receiver=(0x15935ec,0x15935f8),attack_receiver_and_candidates=(0x1593744,0x159377c),player_list_getter=(0x10b62a0,0x10b62c4),
        attack_candidate_loop=(0x1593934,0x159398c),attack_inactive_route=(0x1593a54,0x1593a90),attack_type_terrain_multiply=(0x1594258,0x1594368),
        defence_receiver=(0x1599d24,0x1599d40),defence_candidate_loop=(0x159a004,0x159a070),defence_inactive_route=(0x159a128,0x159a168),
        defence_type_terrain_multiply=(0x159a974,0x159aa84),type_filter=(0x10ff968,0x10ffb30),type_cached_index=(0x1576c14,0x1576c28),backup_generic_separate_type_and_home=(0x15926b4,0x1592798))
    OUT.mkdir(parents=True,exist_ok=True)
    for name,(a,b) in ranges.items():
        lines=[]
        for ins in d.disasm(n.raw[a:b],a):
            targets=n.method_by_rva.get(int(ins.op_str[1:],16),[]) if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#0x') else []
            note=' ; '+','.join(n.method(i)['declaring_type']+'.'+n.method(i)['name'] for i in targets) if targets else ''
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    limits=['Only current CACHE ordinary1008 present param0/param1/param3:37 records111fields; other types/fields excluded.',
        'PlayerManager receives the recipient BattleParam and enumerates BattleManager.GetAllCharaList(0), the _aChara_Player list. Candidate membership and installed arrays/bit cache are supplied; native filtering and IsEnableAbility execute.',
        'Live active candidates enter1008. This type block has no provider-self exclusion, recipient job mask or range/distance test. Same/other and receiver jobs0..5 are fixtures; no claim about actual ALMIGHTY usage.',
        'Inactive candidates take the separate generic backup path; no direct1008 contribution is proved there. Text claiming sub-party activation is retained as text, not promoted to runtime proof.',
        'Terrain parser/current stage/override reuse7 with identical native SHA; new codes3/607 tested against99source backgrounds. Background labels are not unique official enums.',
        'Local attack and incoming multipliers only; no Chain multiplication here. Final stacking/HP, actual installation/unlock and enemy-manager behavior excluded. Enemy-named ordinary source records are retained without asserting player-path activation.']
    trace=dict(effect_type=1008,namespace='ordinary skilllist',source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),native_sha256=hashlib.sha256(n.raw).hexdigest(),
        metadata_sha256=hashlib.sha256(m.raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fixture_scripts={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('scripts/ordinary_7_probe.py','scripts/chica_timed_support.py','scripts/chica_ordinary_rules.py','scripts/phase_d_chain_probe.py')},
        reused_proof=dict(path=str(prior),sha256=hashlib.sha256(prior.read_bytes()).hexdigest()),ability_enum=dict(enum,default=n.default(enum['index'])),
        source_records=selected,background_source_records=bgs,record_count=37,present_field_count=111,field_counts=dict(param0=37,param1=37,param3=37),
        param0_values=codes,new_param0_codes=new_codes,code_background_matches=matches,native_check_count=len(checks),
        fragments={name:[hex(a),hex(b)] for name,(a,b) in ranges.items()},methods=[n.method(i) for i in (8887,8892,3702)],
        player_candidate_field=next(f for f in n.fields(413) if f['name']=='_aChara_Player'),provider_fields=[f for f in n.fields(664) if f['name'] in ('_param','_isActive')],
        cached_index=next(f for f in n.fields(719) if f['name']=='_TargetStageAll'),limits=limits)
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,limits=limits),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=37,fields=111,new_codes=new_codes,native_checks=len(checks))))


if __name__=='__main__':main()
