"""Prove StrengthJob2 recipient/self/job gates and scoped multiplicative values.

Candidate-member and ability-list selection is explicitly modeled; recipient job
loads, self comparisons, param0 conversion, mask checks and multiplications run
in the recovered native image. Fixture overrides never change source records.
"""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_X29
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_ordinary_rules import LocalGuest
from phase_d_chain_probe import BASE,STACK,fbits,fvalue

OUT=Path('output/ordinary_effects/ability1017')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')
JOB_ZH={'WARRIOR':'战士','ARCHERY':'弓手','WIZARD':'法师','HEALER':'僧侣','SHIELD':'骑士','ALMIGHTY':'ALMIGHTY（枚举5；实际对象另论）'}


class JobGuest(LocalGuest):
    def __init__(self,native,rows):
        super().__init__(native,rows)
        self.integer_reads=[]

    def hook(self,cpu,address,size,unused):
        if address-BASE==0xa92534:
            pointer=self.reg(0)
            self.integer_reads.append(dict(pointer=hex(pointer),value=self.integers.get(pointer)))
        super().hook(cpu,address,size,unused)


def run_case(native,source_record,field,job,same,override=None):
    raw=source_record['raw'];sid=raw['skillid'];configured=dict(raw)
    if override is not None:configured['param0']=override
    g=JobGuest(native,{sid:configured});skill=g.skill(sid)
    receiver=g.alloc(0x500);provider=receiver if same else g.alloc(0x500)
    receiver_job=g.alloc(0x20);g.integers[receiver_job]=job;g.put64(receiver+0xf8,receiver_job)
    if not same:
        provider_job=g.alloc(0x20);g.integers[provider_job]=(job+1)%6;g.put64(provider+0xf8,provider_job)
    g.put64(provider+0x1e0,g.array([skill]))
    frame=STACK+0xe0000;g.uc.reg_write(UC_ARM64_REG_X29,frame)
    span=g.alloc(1,b'\0');g.put64(frame-0xe8,span)
    g.uc.mem_write(frame-0x94,struct.pack('<f',1.2))
    if field=='param1':
        g.setreg(24,receiver)
        g.run(0x15937d8,stop=0x15937f4)
        g.run(0x15938f0,stop=0x1593914)
        actual_bit=g.reg(27)&0xffffffff
        g.setreg(28,provider);g.setreg(24,receiver);g.setreg(8,1)
        g.run(0x1594538,stop=0x15945c0)
    else:
        g.setreg(21,receiver)
        g.run(0x1599efc,stop=0x1599f30)
        g.run(0x1599fcc,stop=0x1599ff4)
        actual_bit=g.u32(frame-0x150)
        cell=g.alloc(8);g.put64(cell,provider)
        g.setreg(25,cell);g.setreg(24,receiver);g.setreg(20,0)
        g.run(0x159ac64,stop=0x159ace8)
    assert actual_bit==1<<job,(sid,field,job,actual_bit,g.integer_reads,g.u32(frame-0x1e0),g.u32(frame-0xdc))
    self_allowed=int(configured['param0'])!=0 or not same
    qualified=self_allowed and bool(raw['iParam0']&(1<<job))
    expected=fvalue(fbits(fvalue(fbits(1.2))*fvalue(fbits(raw[field] if qualified else 1))))
    result=struct.unpack('<f',g.uc.mem_read(frame-0x94,4))[0]
    assert result==expected,(sid,field,job,same,override,result,expected)
    assert g.integer_reads[0]['pointer']==hex(receiver_job) and g.integer_reads[0]['value']==job
    mask_pointer=g.u64(skill+0x80)
    assert any(r['pointer']==hex(mask_pointer) for r in g.integer_reads)==self_allowed
    assert [r['field'] for r in g.reads]==['param0']+([field] if qualified else [])
    return dict(name=f'{sid}_{field}_job{job}_same{same}_override{override}',skill_id=sid,field=field,
                source_param0=raw['param0'],fixture_param0_override=override,fixture_kind='SOURCE_VALUE' if override is None else 'CONTROL_ONLY_NOT_GAME_DATA',
                source_job_mask=raw['iParam0'],receiver_job=job,receiver_job_bit=actual_bit,provider_is_receiver=same,
                self_allowed=self_allowed,qualified=qualified,raw_value=raw[field],initial_factor=1.2,
                expected_float32=expected,result=result,float_fields_read=[r['field'] for r in g.reads],passed=True)


def main():
    records=[json.loads(s) for s in SOURCE.open(encoding='utf-8')]
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('ability')==1017]
    assert len(selected)==321
    assert all(set(('param0','iParam0','param1','param3'))<=r['raw'].keys() for r in selected)
    assert all(r['raw']['param0']==1 for r in selected)
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    enum=next(f for f in n.fields(718) if f['name']=='StrengthJob2')
    assert n.default(enum['index'])['value']==1017
    jobs=[]
    for f in n.fields(714):
        if f['name'] in JOB_ZH:
            value=n.default(f['index'])
            jobs.append(dict(f,default=value,bit=1<<value['value'],meaning_zh=JOB_ZH[f['name']]))
    assert [j['default']['value'] for j in jobs]==list(range(6))
    fragments=dict(attack_receiver=(0x15935ec,0x15935f8),attack_job_load=(0x15937d8,0x15937f4),
                   attack_job_bit=(0x15938f0,0x1593914),attack_provider=(0x1593970,0x1593988),
                   attack_gate_multiply=(0x15944ec,0x15945c0),defence_receiver=(0x1599d24,0x1599d40),
                   defence_job_load=(0x1599efc,0x1599f30),defence_job_bit=(0x1599fcc,0x1599ff4),
                   defence_provider=(0x159a040,0x159a068),defence_gate_multiply=(0x159ac1c,0x159ace8),
                   type_cached_index=(0x1576c78,0x1576c8c))
    OUT.mkdir(parents=True,exist_ok=True)
    for name,(begin,end) in fragments.items():
        lines=[]
        for ins in d.disasm(n.raw[begin:end],begin):
            indices=n.method_by_rva.get(int(ins.op_str[1:],16),[]) if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#0x') else []
            note=' ; '+','.join(n.method(i)['declaring_type']+'.'+n.method(i)['name'] for i in indices) if indices else ''
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    samples={}
    for r in selected:samples.setdefault(r['raw']['iParam0'],r)
    assert len(samples)==15
    checks=[]
    for mask,r in samples.items():
        for job in range(6):
            for field in ('param1','param3'):checks.append(run_case(n.raw,r,field,job,True))
    control=next(r for r in selected if r['raw']['skillid']==43023605)
    for value in (0,1,.5,-.5,-1,2):
        for same in (True,False):
            for job in (0,5):
                for field in ('param1','param3'):checks.append(run_case(n.raw,control,field,job,same,value))
    extreme_ids=set()
    for field in ('param1','param3'):
        extreme_ids.add(min(selected,key=lambda r:r['raw'][field])['raw']['skillid'])
        extreme_ids.add(max(selected,key=lambda r:r['raw'][field])['raw']['skillid'])
    for r in selected:
        if r['raw']['skillid'] in extreme_ids:
            job=next(j for j in range(5) if r['raw']['iParam0']&(1<<j))
            for field in ('param1','param3'):checks.append(run_case(n.raw,r,field,job,True))
    prior=Path('output/card_comparison_cid30236/ordinary_rules/trace.json')
    old=json.loads(prior.read_text(encoding='utf-8'))
    assert old['native_sha256']==hashlib.sha256(n.raw).hexdigest()
    trace=dict(effect_type=1017,namespace='ordinary skilllist',source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               fixture_scripts={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('scripts/chica_ordinary_rules.py','scripts/phase_d_chain_probe.py')},
               reused_proof=dict(path=str(prior),sha256=hashlib.sha256(prior.read_bytes()).hexdigest()),
               ability_enum=dict(enum,default=n.default(enum['index'])),job_enum=jobs,source_records=selected,
               record_count=321,present_field_count=1284,source_param0_values=[1],source_job_masks=sorted(samples),
               mask_sample_ids={str(mask):r['raw']['skillid'] for mask,r in samples.items()},extreme_ids=sorted(extreme_ids),
               fragments={name:[hex(a),hex(b)] for name,(a,b) in fragments.items()},
               receiver_fields=[f for f in n.fields(503) if f['name'] in ('_jobType','_listSkill')],
               provider_field=next(f for f in n.fields(664) if f['name']=='_param'),
               cached_index=next(f for f in n.fields(719) if f['name']=='_StrengthJob2'),methods=[n.method(i) for i in (8887,8892)],
               gate_rule='param0==+Infinity or trunc(param0)!=0 or providerBattleParam!=receiverBattleParam; then (iParam0 & (1 << receiver._jobType)) != 0',
               limits=['Only current CACHE ordinary1017 present fields param0/iParam0/param1/param3; all 321 source param0 values are 1.',
                       'param0 overrides are control fixtures only, not additional source records; +Infinity bypass is static evidence only.',
                       'Candidate members, installed ability list and engine ParamS access are explicit fixtures; full party/backups and activation are not proven.',
                       'Job bits use the receiver job; mask31 covers jobs0..4 and excludes ALMIGHTY5; actual use of ALMIGHTY is not inferred.',
                       'Local multiplicative values only, not final total attack/defence/HP; other fields and types are not generalized.'])
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],
                                                          checks=checks,limits=trace['limits']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=321,fields=1284,masks=15,native_checks=len(checks))))


if __name__=='__main__':main()
