"""Ability29 request multiplier and a targeted APK fallback, preserving float32 raw."""
import hashlib
import json
import struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from sample_trace import locate_record
from phase_d_chain_probe import Guest,fbits,fvalue
from unicorn.arm64_const import UC_ARM64_REG_S8

OUT=Path('output/card_comparison_cid30236/skill_power')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('output/cache_full_20261015_v3/records.jsonl')
    records=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    assert not any(r['table']=='skilllist' and r['raw'].get('skillid')==106001 for r in records)
    cache=next(r for r in records if r['table']=='skilllist' and r['raw'].get('skillid')==43023615)
    apk=Path('output/base_master/_mdSkill.json');raw=apk.read_bytes();allrows=json.loads(raw)['skilllist']
    indices=[i for i,r in enumerate(allrows) if r['skillid']==106001];assert len(indices)==1
    row,loc=locate_record(raw,'skilllist',indices[0])
    base_report=json.loads(Path('output/base_master/report.json').read_text(encoding='utf-8'))
    fallback=dict(record_key='APK_AB:skilllist:106001',layer='APK_AB',table='skilllist',raw=row,
        original_file=str(apk),source_sha256=hashlib.sha256(raw).hexdigest(),location=loc,
        location_scope='Exported TypedTree JSON byte offsets, not original Unity binary record bytes',
        original_component={k:base_report[k] for k in ('source_sha256','serialized_file','object_path_id','object_sha256')})
    assert cache['raw']['ability']==row['ability']==29
    m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ranges=dict(type29_index=(0x15766d8,0x15766ec),request_type_list=(0x1547558,0x1547628),
        request_to_boss_util=(0x1181a00,0x1181a24),skill_base_chain=(0x1182f84,0x1182fcc))
    for name,(a,b) in ranges.items():
        lines=[]
        for i in d.disasm(n.raw[a:b],a):
            note=''
            if i.mnemonic=='bl':note=' ; '+','.join(n.method(k)['declaring_type']+'.'+n.method(k)['name'] for k in n.method_by_rva.get(int(i.op_str[1:],16),[]))
            lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{note}')
        (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
    trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_records=[cache,fallback],fallback_rule='Cache ordinary106001 absent -> APK ordinary106001, per-ID fallback; no field merge',
        fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},
        methods=[n.method(i) for i in (6376,5351,5360)],
        cached_type_field=next(f for f in n.fields(719) if f['name']=='_ExtraChainRate'))
    (OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
    checks=[];rows={r['raw']['skillid']:r['raw'] for r in [cache,fallback]}
    for sid in rows:
        for initial in (1,1.4,2):
            g=Guest(n.raw,rows);obj=g.skill(sid);chara=g.alloc(0x400);util=g.alloc(0x400)
            g.uc.mem_write(chara+0x12c,struct.pack('<f',initial));g.setreg(19,chara)
            g.run(0x1547614,obj,stop=0x1547628)
            value=struct.unpack('<f',g.uc.mem_read(chara+0x12c,4))[0]
            want=fvalue(fbits(fvalue(fbits(initial))*fvalue(fbits(rows[sid]['param0']))))
            assert value==want,(sid,initial,value,want)
            # Use actual Boss initialization transfer (positive request input, no default substitution).
            g.setreg(22,chara);g.setreg(19,util);g.run(0x1181a10,stop=0x1181a20)
            util_value=struct.unpack('<f',g.uc.mem_read(util+0x18,4))[0];assert value==util_value
            checks.append(dict(skill_id=sid,field='param0',raw=rows[sid]['param0'],initial_request_factor=initial,
                modified_request_factor=value,boss_skill_chain_rate=util_value,passed=True))
    (OUT/'native_checks.json').write_text(json.dumps(dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
        limits=['Party/type list membership and installed skill supplied; original source values only.',
            'Actual RequestSkill param0 multiplication and Boss transfer execute; no final damage or complete Chain system.',
            'APK fallback valid if this cache is primary and APK component is loaded; current player state unknown.']),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=len(checks),APK_fallback_id=106001)))


if __name__=='__main__':main()
