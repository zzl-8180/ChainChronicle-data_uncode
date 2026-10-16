"""Trace existing card active type116 into native interval weapon setup."""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from il2cpp_sample_code import Native
from metadata_targets import Metadata


def main():
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    n = Native(m)
    sample = json.loads(Path('output/sample/sample.json').read_text(encoding='utf-8'))
    card = sample['card_raw']
    active_type = card['skillid'][0]
    matches = [f for f in n.fields(717) if f['name']!='value__' and n.default(f['index'])['value']==active_type]
    if len(matches)!=1 or matches[0]['name']!='INTERVAL_FALL2':
        raise ValueError('Active enum mapping differs')
    enum = n.default(matches[0]['index'])
    table_rva, branch_base = 0x206ee04,0x1297d4c
    entry = n.unpack('<H',table_rva+active_type*2)[0]
    branch = branch_base+entry*4
    md = Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    context = list(md.disasm(n.raw[branch:branch+36],branch))
    if not any(i.mnemonic=='bl' and i.op_str=='#0x119d924' for i in context):
        raise ValueError('Active dispatch does not call expected handler')
    methods = []
    directory = Path('output/il2cpp/active_code')
    directory.mkdir(exist_ok=True)
    for mi in (5191,5275,5350,5486,5487,8770,8771,8772,8773):
        row = n.method(mi)
        start = int(row['native_rva'],16)
        end = min(p for p in n.pointers if p>start)
        insns = list(md.disasm(n.raw[start:end],start))
        if sum(i.size for i in insns)!=end-start:
            raise ValueError('Undecodable active method')
        row['calls'] = []
        for insn in insns:
            if insn.mnemonic in ('bl','b') and insn.op_str.startswith('#0x'):
                target = int(insn.op_str[1:],16)
                for ci in n.method_by_rva.get(target,[]):
                    row['calls'].append({'rva':hex(insn.address),'callee':n.method(ci)})
        (directory/f"{row['declaring_type']}_{row['name']}.txt").write_text('\n'.join(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in insns),encoding='utf-8')
        methods.append(row)
    fields = {m.string(m.types[ti][0]):n.fields(ti) for ti in (503,579,899)}
    target = next(f for f in n.fields(722) if f['name']=='oRANDOM')
    target_enum = n.default(target['index'])
    assert target_enum['value']==card['skillparam3']==32
    bindings = [
        ('skillparam0','effTime','_effTime','0x119d75c → s8 → s0@119d898 → str s13@15572cc', 'Duration-control input -1; exact lifetime follows FixedUpdate'),
        ('skillparam1','interval','_interval','0x119d75c → s9 → s1@119d89c → _interval@0x3c', 'Interval input 1; timer accumulates update delta'),
        ('skillparam2','shootNum','_shootNum','0x119d740 → fcvtzs@119d750 → w3@119d890 → _shootNum@0x44', 'Count15; decremented only after Attack returns true; zero ends object'),
        ('skillparam3','targetType','_targetType','0x119d740 → fcvtzs@119d774 → w2@119d890 → _targetType@0x40', 'TARGET_TYPE.oRANDOM=32'),
        ('skillparam4','atkValue','_atkValue','0x119d760 → s13 * getBasicSkillAttack@119d810 → w4@119d8b0', 'Factor1 before basic-skill-attack integer conversion; final damage unknown'),
        ('skillparam5','pushPow','_pushPow','0x119d760 → s10 → s2@119d8a0 → _pushPow@0x58', 'Push parameter0.001; world unit/knockdown rule unknown'),
        ('skillparam6','expRange','_expRange','0x119d7ac → s11 → s3@119d8a4 → _expRange@0x78', 'Explosion-range input1.5; world unit unknown'),
        ('skillparam7','expAtkValue','_expAtkValue','0x119d7ac → s14 * basic attack@119d820 → w6@119d8b4', 'Factor1 before explosion attack integer conversion; final damage unknown'),
        ('skillparam8','hitDelay','(forwarded setup argument)','type116 cmp@119d834 → ldp s12,s13@119d83c → s5@119d8ac', 'Hit delay input0.5; missing skillparam9 effectDelay remains unfilled')]
    result = {'status':'ACTIVE_DISPATCH_AND_SETUP_STATIC_TRACE','card_id':card['cid'],
              'card_record_location':sample['record_locations'][str(card['cid'])],
              'raw_source':'charainfo.data5, not a skilllist row with skillid116',
              'active_type_raw':active_type,'active_type_enum':'SKILL_TYPE.INTERVAL_FALL2','enum_evidence':enum,
              'native_image_sha256':hashlib.sha256(n.raw).hexdigest(),'metadata_sha256':hashlib.sha256(m.raw).hexdigest(),
              'dispatch':{'table_rva':hex(table_rva),'entry_index':active_type,'entry_u16':entry,
                          'branch_rva':hex(branch),'instructions':[f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in context]},
              'methods':methods,'fields':fields,'target_enum':target_enum,
              'parameter_bindings':[{'field':field,'raw':card[field],'status':'CONFIRMED_STATIC_SETUP_ARGUMENT',
                                     'argument':argument,'stored_field':stored,'code_path':evidence,'meaning_limit':meaning}
                                    for field,argument,stored,evidence,meaning in bindings],
              'unknown':['charainfo JSON through full battle initialization not executed; initialize_param statically copies named BattleParam getters',
                         'Live timing, target availability and final damage not tested',
                         'Integer conversion helper0x14374bc formula not resolved',
                         'skillparam9 absent in source; not filled with an invented default',
                         'Following heal/buff stages of active skill still require separate pattern/load path analysis'],
              'local_description':card['skilltext']}
    Path('output/sample/active_skill_trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'type':result['active_type_enum'],'dispatch_branch':hex(branch),
                      'parameters':[(r['field'],r['raw'],r['argument']) for r in result['parameter_bindings']]},ensure_ascii=False))


if __name__=='__main__':
    main()
