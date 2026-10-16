"""Extend existing ability1095 attack/defence evidence to the current cache type.

Only the ID-independent getter/multiply paths run. Eligibility is explicitly
supplied; this is not a player installation or complete battle simulation.
"""
import hashlib
import json
import math
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_S8, UC_ARM64_REG_X29
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_ordinary_rules import LocalGuest
from phase_d_chain_probe import fbits, fvalue

OUT=Path('output/ordinary_effects/ability1095')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')


def main():
    records=[json.loads(s) for s in SOURCE.open(encoding='utf-8')]
    selected=[r for r in records if r['table']=='skilllist' and r['raw'].get('ability')==1095]
    rows={r['raw']['skillid']:r['raw'] for r in selected}
    assert len(rows)==len(selected) and selected
    for r in selected:
        assert all(type(r['raw'][f]) in (int,float) and math.isfinite(r['raw'][f]) for f in ('param1','param3'))
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m)
    prior=Path('output/card_comparison_cid30236/ordinary_rules/trace.json')
    old=json.loads(prior.read_text(encoding='utf-8'))
    assert old['native_sha256']==hashlib.sha256(n.raw).hexdigest()
    enum=next(f for f in n.fields(718) if f['name']=='Always3')
    assert n.default(enum['index'])['value']==1095
    fragments=dict(attack_dispatch=(0x1107680,0x11076ac),attack_getter=(0x1107958,0x110797c),
                   attack_multiply=(0x1107c84,0x1107c88),defence_dispatch=(0x1107fec,0x1108018),
                   defence_getter_multiply=(0x1108124,0x1108148))
    OUT.mkdir(parents=True,exist_ok=True)
    d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    for name,(begin,end) in fragments.items():
        lines=[]
        for ins in d.disasm(n.raw[begin:end],begin):
            methods=n.method_by_rva.get(int(ins.op_str[1:],16),[]) if ins.mnemonic in ('bl','b') and ins.op_str.startswith('#0x') else []
            note=' ; '+','.join(n.method(i)['declaring_type']+'.'+n.method(i)['name'] for i in methods) if methods else ''
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    ids=(111503,40022000,40008901,43023601,65000001,75000012,40129301,41223601)
    assert set(ids)<=rows.keys()
    for field in ('param1','param3'):
        assert {min(r[field] for r in rows.values()),max(r[field] for r in rows.values())} <= {rows[i][field] for i in ids}
    checks=[]
    for sid in ids:
        for field in ('param1','param3'):
            for gate in (True,False):
                g=LocalGuest(n.raw,rows,enabled=gate);obj=g.skill(sid)
                g.setreg(22,g.alloc(0x100));g.setreg(23,1);g.setreg(21,1)
                g.uc.reg_write(UC_ARM64_REG_X29,obj)
                g.uc.reg_write(UC_ARM64_REG_S8,fbits(1.2))
                begin,end=(0x1107680,0x1107c88) if field=='param1' else (0x1107fec,0x1108148)
                g.run(begin,1095,stop=end)
                actual=fvalue(g.uc.reg_read(UC_ARM64_REG_S8))
                expected=fvalue(fbits(fvalue(fbits(1.2))*fvalue(fbits(rows[sid][field] if gate else 1))))
                assert actual==expected and len(g.qualifiers)==1,(sid,field,gate,actual,expected)
                assert g.reads==([dict(source_id=sid,field=field,raw=rows[sid][field],origin='SOURCE')] if gate else [])
                checks.append(dict(name=f'{sid}_{field}_gate_{gate}',skill_id=sid,field=field,raw_value=rows[sid][field],
                                   qualifier=gate,initial_factor=1.2,expected_float32=expected,result=actual,reads=g.reads,passed=True))
    summary={field:dict(present_records=len(selected),minimum=min(r[field] for r in rows.values()),
                       maximum=max(r[field] for r in rows.values())) for field in ('param1','param3')}
    trace=dict(effect_type=1095,namespace='ordinary skilllist',
               native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
               source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               reused_proof=dict(path=str(prior),sha256=hashlib.sha256(prior.read_bytes()).hexdigest()),
               ability_enum=dict(enum,default=n.default(enum['index'])),source_records=selected,
               record_count=len(selected),present_field_count=2*len(selected),field_summary=summary,sample_ids=list(ids),
               fragments={name:[hex(a),hex(b)] for name,(a,b) in fragments.items()},
               generalization_basis='Native ability==1095 branches use the current skill object and param1/param3 getters; no skill-ID-specific numeric branch between supplied eligibility and multiplication.',
               limits=['Only current CACHE skilllist ability1095 and present finite param1/param3.',
                       'IsEnableAbility result and engine scalar access are explicit fixtures; actual eligibility and installation remain unknown.',
                       'Attack/defence are local multiplicative contributions, not final attack, total reduction or final HP loss.',
                       'Other fields, namespaces and effect types are not generalized.'])
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
                                                          limits=trace['limits']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(records=len(selected),fields=2*len(selected),native_checks=len(checks))))


if __name__=='__main__':main()
