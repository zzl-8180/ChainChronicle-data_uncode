"""SA_SupportTarget action gate, bounded application and present critical fields.

The real OnAction wrapper/dispatch/handler runs. GetMemberList, allocation,
managed list indexing, ParamS access and setSupport2 submission are modeled.
Missing source fields stay missing; constructor/getter defaults are recorded
only as runtime-fixture outputs, never exported as found source parameters.
"""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_S0,UC_ARM64_REG_S8
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_timed_support import TimedGuest
from phase_d_chain_probe import BASE,fbits,fvalue

OUT=Path('output/ordinary_effects/ability2012')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')


class SupportGuest(TimedGuest):
    def __init__(self,native,rows,target_count=3):
        super().__init__(native,rows)
        for slot in (0x29f0b88,0x29bc5a0,0x29d5fa0):self.metadata(slot)
        for flag in (0x2bd057a,0x2bcf5ba,0x2bd17c9,0x2bd3582,0x2bd3583):self.uc.mem_write(BASE+flag,b'\1')
        self.put64(self.statics[0x29f0b88]+0x10,self.alloc(0x100))
        self.targets=[]
        for _ in range(target_count):
            target=self.alloc(0x200);self.put64(target+0xa0,self.alloc(0x300));self.targets.append(target)
        self.target_list=self.collection(self.targets)
        self.selections=[];self.applications=[];self.handler_calls=0

    def skill(self,sid):
        obj=super().skill(sid)
        if obj and not self.u64(obj+0x90):
            pointer=self.alloc(0x20);self.integers[pointer]=self.rows[sid]['flag'];self.put64(obj+0x90,pointer)
        return obj

    def hook(self,cpu,address,size,unused):
        a=address-BASE
        if a==0x11a4e64:self.handler_calls+=1
        if a==0x10be3c8:
            self.selections.append(dict(chara_type=self.reg(1)&0xffffffff,target_selector=self.reg(2)&0xffffffff,attacker=hex(self.reg(3))))
            self.uc.mem_write(self.reg(5),b'\0')  # explicit bAll fixture
            self.ret(self.target_list)
        elif a==0xa928d8:
            self.ret(self.integers[self.reg(0)])
        elif a==0xa84484:
            pointer,count=self.span(self.reg(0));index=self.reg(1)&0xffffffff
            assert index<count
            self.ret(self.u64(pointer+index*8))
        elif a==0x88d910:
            self.ret(self.alloc(0x60))
        elif a==0x1777374:
            data=self.reg(6)
            self.applications.append(dict(ability_id=self.reg(3)&0xffffffff,ability_type=self.reg(4)&0xffffffff,
                                          support_time=fvalue(cpu.reg_read(UC_ARM64_REG_S0)),
                                          stored_chance=struct.unpack('<f',cpu.mem_read(data+0x24,4))[0],
                                          stored_damage=struct.unpack('<f',cpu.mem_read(data+0x28,4))[0],
                                          data_pointer=data))
            self.ret()
        else:super().hook(cpu,address,size,unused)


def action_case(native,record,chain_rate,target_count=3,already=False):
    raw=record['raw'];sid=raw['skillid'];g=SupportGuest(native,{sid:raw},target_count)
    skill=g.skill(sid);actor=g.alloc(0x300);util=g.alloc(0x200)
    g.put32(actor+0x18,0);g.uc.mem_write(actor+0x12c,struct.pack('<f',chain_rate))
    g.put64(util+0xb8,actor);g.put64(util+0x150,g.array([skill]))
    g.uc.mem_write(util+0x160,bytes([int(already)]))
    g.run(0x11a3e78,util)
    calls=g.handler_calls;applications=len(g.applications)
    limit=int(raw.get('param7',0));expected=0 if already else min(target_count,limit if limit>0 else 1)
    assert applications==expected and calls==int(not already)
    if not already:
        assert len(g.selections)==1 and g.selections[0]['target_selector']==int(raw['param8'])
    for applied in g.applications:
        assert applied['ability_id']==sid and applied['ability_type']==2012
        assert applied['support_time']==fvalue(fbits(raw['param0']))
        assert applied['stored_chance']==fvalue(fbits(raw.get('param4',0)))
        assert applied['stored_damage']==fvalue(fbits(raw.get('param5',0)))
    g.run(0x11a3e78,util)
    assert g.handler_calls==calls and len(g.applications)==applications
    assert g.uc.mem_read(util+0x160,1)==b'\1'
    return dict(name=f'action_{sid}_chain{chain_rate}_targets{target_count}_already{already}',skill_id=sid,
                source_fields={f:dict(present=f in raw,raw_value=raw.get(f)) for f in ('param0','param4','param5','param7','param8')},
                chain_rate_fixture=chain_rate,target_count_fixture=target_count,already_processed=already,
                handler_calls=calls,application_count=applications,repeated_action_additional_calls=0,
                applications=[{k:v for k,v in item.items() if k!='data_pointer'} for item in g.applications],
                limits='Candidate list and setter submission modeled; absent getters may produce runtime defaults, not source values.',passed=True),g


def main():
    records=[json.loads(s) for s in SOURCE.open(encoding='utf-8')]
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('ability')==2012]
    assert len(selected)==406 and all(r['raw']['param0']>0 for r in selected)
    counts={field:sum(field in r['raw'] for r in selected) for field in ('param0','param4','param5')}
    assert counts=={'param0':406,'param4':308,'param5':311}
    assert all('iParam0' not in r['raw'] for r in selected)
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    enum=next(f for f in n.fields(718) if f['name']=='SA_SupportTarget');assert n.default(enum['index'])['value']==2012
    selectors=[dict(f,default=n.default(f['index'])) for f in n.fields(722) if f['name'] in ('pGROUP_ALL','MYSELF')]
    assert [s['default']['value'] for s in selectors]==[31,64]
    fragments=dict(action_wrapper=(0x11a3e78,0x11a3ee8),action_dispatch=(0x11a3ee8,0x11a405c),
                   enabled_types=(0x11a3208,0x11a3248),support_target=(0x11a4e64,0x11a5160),
                   absent_param5_getter=(0x1dbcf9c,0x1dbcfb4),absent_job_getter=(0x1dbd30c,0x1dbd320),
                   zero_job_filter_bypass=(0x13ab338,0x13ab38c),job_filter_return=(0x13ab43c,0x13ab458),
                   probability_sum=(0x172ebec,0x172ecb4),damage_sum=(0x172ecb4,0x172ed7c),
                   duration_store=(0x1777598,0x17775b4),countdown=(0x172e55c,0x172e578))
    OUT.mkdir(parents=True,exist_ok=True)
    for name,(begin,end) in fragments.items():
        lines=[]
        for ins in d.disasm(n.raw[begin:end],begin):
            ids=n.method_by_rva.get(int(ins.op_str[1:],16),[]) if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#0x') else []
            note=' ; '+','.join(n.method(i)['declaring_type']+'.'+n.method(i)['name'] for i in ids) if ids else ''
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    # One representative per observed numeric value, plus source absence shapes.
    sample_ids=set()
    for field in ('param0','param4','param5'):
        seen=set()
        for r in selected:
            if field in r['raw'] and r['raw'][field] not in seen:
                seen.add(r['raw'][field]);sample_ids.add(r['raw']['skillid'])
    for predicate in (lambda r:'param4' not in r and 'param5' in r,lambda r:'param4' not in r and 'param5' not in r,lambda r:'param7' not in r):
        sample_ids.add(next(r['raw']['skillid'] for r in selected if predicate(r['raw'])))
    checks=[]
    for r in selected:
        if r['raw']['skillid'] in sample_ids:
            for rate in (.5,2):
                result,_=action_case(n.raw,r,rate);checks.append(result)
    example=next(r for r in selected if r['raw']['skillid']==43023612)
    for targets,already in ((0,False),(3,True)):
        result,_=action_case(n.raw,example,1,targets,already);checks.append(result)
    # Independent supplied lists test Support2 addition/default class limits.
    chosen=[]
    for value in (.3,.35,.375):chosen.append(next(r for r in selected if r['raw'].get('param4')==value and r['raw'].get('param5')==value))
    for subset in (chosen[:1],chosen[:2],chosen):
        g=SupportGuest(n.raw,{})
        entries=[]
        for r in subset:
            blob=g.alloc(0x60);g.uc.mem_write(blob+0x24,struct.pack('<ff',r['raw']['param4'],r['raw']['param5']))
            entry=g.alloc(0x80);g.put64(entry+0x50,blob);entries.append(entry)
        ctrl=g.alloc(0x40);g.put64(ctrl+0x10,g.collection(entries))
        outputs=[]
        for address in (0x172ebec,0x172ecb4):
            g.run(address,ctrl);outputs.append(fvalue(g.uc.reg_read(UC_ARM64_REG_S0)))
        sums=[sum(r['raw'][f] for r in subset) for f in ('param4','param5')]
        assert abs(outputs[0]-min(.5,sums[0]))<1e-6 and abs(outputs[1]-min(1,sums[1]))<1e-6
        checks.append(dict(name='support2_sum_'+str(len(subset)),skill_ids=[r['raw']['skillid'] for r in subset],
                           probability_delta=outputs[0],damage_delta=outputs[1],default_limits=[[0,.5],[-1.5,1]],passed=True))
    for seconds in sorted({r['raw']['param0'] for r in selected}):
        for delta in (.25,seconds):
            g=SupportGuest(n.raw,{})
            entry=g.alloc(0x80);g.uc.mem_write(entry+0x30,struct.pack('<f',seconds))
            g.uc.reg_write(UC_ARM64_REG_S8,fbits(delta));g.run(0x172e55c,entry,stop=0x172e578)
            result=struct.unpack('<f',g.uc.mem_read(entry+0x30,4))[0]
            expected=fvalue(fbits(fvalue(fbits(seconds))-fvalue(fbits(delta))))
            assert result==expected
            checks.append(dict(name=f'time_{seconds}_{delta}',source_time=seconds,game_delta_fixture=delta,remaining=result,expected_float32=expected,passed=True))
    reused=[]
    for path in ('output/card_comparison_cid30236/critical/trace.json','output/card_comparison_cid30236/timed_support/trace.json','output/boss_heal/trace.json'):
        proof=json.loads(Path(path).read_text(encoding='utf-8'));assert proof['native_sha256']==hashlib.sha256(n.raw).hexdigest()
        reused.append(dict(path=path,sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest()))
    trace=dict(effect_type=2012,namespace='ordinary skilllist',source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               fixture_scripts={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('scripts/chica_timed_support.py','scripts/chica_ordinary_rules.py','scripts/phase_d_chain_probe.py')},
               reused_proofs=reused,ability_enum=dict(enum,default=n.default(enum['index'])),target_selector_enum=selectors,
               source_records=selected,record_count=406,present_field_count=sum(counts.values()),field_counts=counts,sample_ids=sorted(sample_ids),
               source_absence_counts={'param4':98,'param5':95,'iParam0':406,'param7':2},
               fragments={name:[hex(a),hex(b)] for name,(a,b) in fragments.items()},methods=[n.method(i) for i in (5540,5541,5546,3705,9121,7104,7220,7226,7227)],
               action_gate_field=next(f for f in n.fields(579) if f['name']=='_isSkillAbilityAction'),
               chain_rate_field=next(f for f in n.fields(664) if f['name']=='_skillChainRate'),
               jump_table=dict(rva='0x206deae',ability2012_index=5,target=hex(0x11a3f34+n.raw[0x206deae+5]*4)),
               limits=['Present fields only: param0 game-time input, param4 probability delta, param5 critical coefficient delta; missing raw fields stay absent.',
                       'OnAction wrapper checks _isSkillAbilityAction and then marks it processed; exact animation timing and external resets not emulated.',
                       'Target selector31=pGROUP_ALL and64=MYSELF; actual GetMemberList population is modeled, so full member/back-up selection remains outside scope.',
                       'All current iParam0 absent; native getter returns0 and CheckJobFlag bypasses. No source iParam0=0 is exported.',
                       'setSupport2 submissions captured; existing Support2 time-store/game-delta evidence reused. Reapplication/expiry removal and final battle HP not simulated.',
                       'Critical fields bypass caster skillChainRate; default-category aggregation limits are local and may be overridden elsewhere.'])
    assert trace['jump_table']['target']=='0x11a4014'
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,limits=trace['limits']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=406,present_fields=sum(counts.values()),sample_records=len(sample_ids),native_checks=len(checks))))


if __name__=='__main__':main()
