"""Leader category2 job list, Warrior0 and minimum matching count4."""
import hashlib,json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from phase_d_chain_probe import Guest

OUT=Path('output/card_comparison_cid30236/leader_condition')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    row=next(r for r in map(json.loads,source.open(encoding='utf-8')) if r['table']=='leader_ability' and r['raw'].get('cid')==30236)
    assert row['raw']['border']==4 and row['raw']['category']==2 and row['raw']['conditions']==[0]
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    job=n.default(next(f['index'] for f in n.fields(714) if f['name']=='WARRIOR'));assert job['value']==0
    label=n.literal(0x29c2068);assert label['text']=='戦士'
    literals={key:n.literal(slot) for key,slot in (('border',0x29f7d58),('category',0x29bc2c8),('conditions',0x29e05b0),('target',0x29a4168))}
    assert all(x['text']==key for key,x in literals.items())
    assert 0xe21e54+n.unpack('<H',0x2028bb0+4)[0]*4==0xe21f34
    registration=n.unpack('<16Q',n.registration_rva);helpers=[]
    for slot,want in ((0x29b4a90,'Intersect'),(0x29a6350,'Any')):
        usage=n.unpack('<Q',slot)[0];encoded=n.unpack('<Q',usage)[0];index=(encoded&0x1ffffffe)>>1
        assert encoded>>29&7==6 and index<registration[8]
        spec_address=registration[9]+index*12;spec=n.unpack('<iii',spec_address);method=m.method(spec[0])
        assert method['image']=='System.Core.dll' and method['declaring_type']=='Enumerable' and method['name']==want
        helpers.append(dict(slot=hex(slot),usage=hex(usage),encoded=hex(encoded),method_spec_index=index,method_spec_rva=hex(spec_address),method_spec=list(spec),method=method))
    ranges=dict(border_and_target_load=(0xe21c60,0xe21ce8),category_dispatch=(0xe21de0,0xe21e54),
        category2_store_and_job0_label=(0xe21f34,0xe22000),job_input=(0xe23a84,0xe23ab0),
        job_membership=(0xe23e80,0xe23e9c),membership_helper=(0xe22c9c,0xe22d20),count_and_border=(0xe23ef0,0xe23f54))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_records=[row],
        fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},literals=literals,job0_enum=job,job0_label=label,
        fields=n.fields(n.method(36311)['declaring_type_index']),methods=[n.method(i) for i in (36311,36317,36326)],generic_helpers=helpers,
        limits='Job category and minimum count only. Candidate party/backups/buddy population and full activation not emulated; raw target0 only known to load _rule.')
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    g=Guest(n.raw,{});g.run(0xe21e10,2,stop=0xe21f34)
    checks=[dict(name='category2_routes_job_branch',category=2,branch='0xe21f34',passed=True)]
    data=g.alloc(0xa0);conditions=g.array([0],'i');g.setreg(19,data);g.run(0xe21f58,conditions,stop=0xe21f64)
    assert g.u64(data+0x28)==conditions and g.u32(data+0x98)==2
    checks.append(dict(name='conditions_stored_in_target_job',category=2,conditions=[0],passed=True))
    g.put32(data+0x48,4)
    for before,job_match,want,qualified in ((2,0,2,False),(2,1,3,False),(3,0,3,False),(3,1,4,True),(4,0,4,True),(4,1,5,True)):
        for reg,val in ((8,data),(14,before),(22,0),(23,job_match),(24,0),(25,0)):g.setreg(reg,val)
        g.run(0xe23f00,0,stop=0xe23f34 if qualified else 0xe23a08)
        assert g.reg(11)==want
        checks.append(dict(name=f'count_{before}_job{job_match}',previous_count=before,job_match=bool(job_match),new_count=want,border=4,qualified=qualified,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['JSON-decoded category/conditions and per-candidate membership booleans supplied; real category jump, target_job store and cumulative minimum comparison execute.',
            'Does not execute generic LINQ intersection or full party enumeration/activation; source job enum and label are static metadata evidence.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),job=0,minimum_count=4)))


if __name__=='__main__':main()
