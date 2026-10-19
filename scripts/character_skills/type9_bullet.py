"""P3B4: Bullet param0 is post-hit damage retention, not critical probability."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import common as C
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from il2cpp_sample_code import Native
from metadata_targets import Metadata
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
import unicorn.arm64_const as U

OUT = C.ROOT / 'output/character_skills/type9_crit'
KIND = '子弹贯通命中后伤害保留系数'
CONDITION = ('本记录已装载并通过类型9资格筛选；Bullet.Initialize 的 bCheckAbility=true 且 '
             'dmgtype≠Skill(1) 才读取。消费为 MULTIHIT(bit0) 逐命中路径，或非MULTIHIT且'
             'SHOT_THROUGH(bit20)置位、_bStopMultihit=false、目标对象存在且命中后IsAlive=false的继续路径；'
             '首次命中先用当前伤害输入，命中后更新供后续命中使用')
FORMULA = ('p=max(本子弹初始化时已启用type9的param0)；'
           'D下一次=clamp_int32(trunc(float32(float32(D本次)×float32(p))))；每次命中后重复更新')
LIMITS = ('D为Bullet._damage中的运行时整数攻击输入，不是最终扣血或面板ATK；初始D、目标/命中次数、'
          '其他字段与效果、实际装载及实机结果不在本规则范围；同类p择最大，不相加/叠乘；缺失/null不补值')


def convert(value, record):
    if value == 1:
        direction = '系数1（中性）；仍经float32和整数化，可能因精度变化'
    elif value == 0:
        direction = '下一次输入归零'
    elif value > 1:
        direction = '后续输入增加'
    elif value > 0:
        direction = '后续输入衰减'
    else:
        direction = '保留原始负系数，按有符号公式计算，不推定有效负伤害'
    return dict(quantity_kind=KIND, value_text=f'贯通命中后伤害输入 ×{value:.7g}（{direction}；首次不乘本项；逐次整数化）',
                unit='无量纲系数（非概率/百分点）', note=CONDITION+'；'+FORMULA+'；'+LIMITS)


def rule_rows(native=None, md=None):
    return [dict(file_table='skilllist.ability9', table='skilllist', effect_type=9, field_path='/param0',
                 meaning_zh=KIND, unit='无量纲系数（非概率/百分点）', rule=FORMULA,
                 status='已确认局部消费与换算；类型级规则，未实机验证', condition=CONDITION, limits=LIMITS,
                 evidence=['scripts/character_skills/type9_bullet.py',
                           'output/character_skills/type9_crit/native_evidence.json',
                           'Bullet.checkBulletAbility 0x1310a0c..0x1310b28；checkBulletCollision 0x1311744..0x13117d8'])]


def native_evidence(n, md):
    dis=Cs(CS_ARCH_ARM64,CS_MODE_ARM);checks=[]
    def check(name,passed,**detail):checks.append(dict(name=name,passed=bool(passed),**detail))
    def op(a):
        i=next(dis.disasm(n.raw[a:a+4],a));return i.mnemonic+' '+i.op_str
    pins={
        0x1576548:'mov w0, #9',0x157654c:'bl #0x15771e8',0x1576558:'strh w0, [x8, #8]',
        0x1310a0c:'ldrh w3, [x8, #8]',0x1310a10:'bl #0x10ff968',
        0x10ffa14:'bl #0x1578da0',0x10ffa6c:'bl #0x1dbcf0c',0x10ffa70:'cmp w0, w22',
        0x10ffa74:'b.ne #0x10ffa9c',0x10ffa84:'bl #0x1112574',0x10ffa88:'tbz w0, #0, #0x10ffa9c',
        0x1310834:'str w8, [x20, #0x50]',0x1310824:'mov w8, #0x3f800000',
        0x131088c:'cmp w21, #1',0x1310898:'b.eq #0x13108b0',0x13108a0:'tbz w8, #0, #0x13108b0',
        0x13108ac:'bl #0x131090c',0x1310ab4:'bl #0x1dbcf24',0x1310ac4:'bl #0x1dbcf24',
        0x1310ac8:'fcmp s9, s0',0x1310acc:'b.pl #0x1310ad4',0x1310ad0:'mov x21, x23',
        0x1310b24:'bl #0x1dbcf24',0x1310b28:'str s0, [x19, #0x50]',
        0x1311568:'tbnz w26, #0, #0x13116f8',0x1311750:'bl #0xa92534',
        0x13115f0:'bl #0x153b120',0x1311608:'cbnz w8, #0x131165c',
        0x1311620:'tbz w20, #0x14, #0x131165c',0x1311654:'bl #0x1535abc',
        0x1311658:'tbz w0, #0, #0x1311a10',
        0x1311778:'mov w3, w23',0x1311790:'bl #0x153b120',0x13117ac:'bl #0x1309248',
        0x13117b0:'ldr s0, [x19, #0x50]',0x13117b8:'scvtf s1, w23',0x13117c0:'fmul s0, s0, s1',
        0x13117c4:'bl #0x14376ec',0x13117d8:'bl #0xa9250c',
        0x1311a30:'ldr s0, [x19, #0x50]',0x1311a3c:'fmul s0, s0, s1',0x1311a40:'bl #0x14376ec',
        0x14376f4:'fcvtzs x8, s0',0x14376fc:'fcmp s0, s1',0x143770c:'b.gt #0x1437724',
    }
    check('static_chain_pins',all(op(a)==v for a,v in pins.items()),
          pins=[dict(rva=hex(a),expected=v,actual=op(a)) for a,v in pins.items()])
    types={md.string(t[0]):i for i,t in enumerate(md.types)}
    fields={t:{f['name']:f for f in n.fields(types[t])} for t in ['Bullet','AbilityTypeCachedFlagIndex','BattleParam']}
    check('metadata_field_identity',fields['Bullet']['_decRate']['offset']=='0x50' and
          fields['Bullet']['_damage']['offset']=='0x48' and fields['AbilityTypeCachedFlagIndex']['_Bullet']['offset']=='0x8',fields=fields)
    methods={a:[n.method(i) for i in n.method_by_rva.get(a,[])] for a in
             [0x131055c,0x131090c,0x1311404,0x10ff968,0x15771e8,0x1578da0,0x1dbcf24,0x153b120]}
    expected_methods={0x131055c:('Bullet','Initialize'),0x131090c:('Bullet','checkBulletAbility'),
        0x1311404:('Bullet','checkBulletCollision'),0x10ff968:('BattleParam','GetAbilityListOnFlagIndex'),
        0x15771e8:('Constants','AbilityType2FlagIndex'),0x1578da0:('Constants','FlagIndex2AbilityType'),
        0x1dbcf24:('skillParameter','get_param0'),0x153b120:('CharaBehavior','Attack')}
    check('metadata_method_identity',all(any((v['declaring_type'],v['name'])==expected_methods[a] for v in vv)
          for a,vv in methods.items()),methods={hex(a):v for a,v in methods.items()})
    import skilllist_types as S
    names=S.ability_type_names(md,n);damage=S.enum_values(n,md,'eDamageType');flags=S.enum_values(n,md,'ATTACK_FLAG')
    check('enum_identity',names.get(9)=='Bullet' and names.get(51)=='CriticalRate' and
          damage['Skill']==1 and flags['MULTIHIT']==0 and flags['SHOT_THROUGH']==20,
          ability9=names.get(9),ability51=names.get(51),damage=damage,shot_through_bit_index=flags['SHOT_THROUGH'],
          multihit_bit_index=flags['MULTIHIT'],multihit_mask=1<<flags['MULTIHIT'])
    resolver=S.Resolver(n)
    leaves={k:resolver.resolve(k,9) for k in S.FUNCS}
    check('five_generic_paths_neutral',all(leaves[k]==S.NEUTRAL[k] for k in leaves),leaves={k:hex(v) for k,v in leaves.items()})
    # Type9's qualification exits with the preloaded true; no target/status reads.
    trace=[]
    def eligibility(u,a,s,d):
        r=a-S.BASE;trace.append(hex(r))
        if r in [0x1113900,0x1113904]:u.emu_stop()
    h=resolver.uc.hook_add(UC_HOOK_CODE,eligibility)
    resolver.uc.reg_write(U.UC_ARM64_REG_W0,9);resolver.uc.reg_write(U.UC_ARM64_REG_W8,9)
    resolver.uc.emu_start(S.BASE+0x111264c,0,count=128);resolver.uc.hook_del(h)
    check('type9_unconditional_qualification',trace[-1]=='0x1113904' and resolver.uc.reg_read(U.UC_ARM64_REG_W0)==1,trace=trace)

    def machine():
        uc=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
        for start,size in [(0x1310000,0x2000),(0x1437000,0x1000),(0x10ff000,0x1000)]:
            uc.mem_map(start,size);uc.mem_write(start,n.raw[start:start+size])
        uc.mem_map(0x40000000,0x20000);uc.mem_map(0x29bd000,0x1000)
        uc.reg_write(U.UC_ARM64_REG_SP,0x4001f000)
        return uc
    def sf(u,r,v):u.reg_write(getattr(U,'UC_ARM64_REG_Q'+str(r)),int.from_bytes(struct.pack('<f',v),'little'))
    # Only the exact comparison and gate fragment is exercised; fixtures supply the cache inverse type.
    filters=[]
    for ability in [8,9,10,51]:
        for enabled in [0,1]:
            uc=machine();uc.reg_write(U.UC_ARM64_REG_W22,9);uc.reg_write(U.UC_ARM64_REG_W20,64)
            uc.reg_write(U.UC_ARM64_REG_X19,0x40001000);hit=[]
            def hook(u,a,s,d):
                if a in [0x10ffa6c,0x10ffa84]:
                    u.reg_write(U.UC_ARM64_REG_W0,ability if a==0x10ffa6c else enabled);u.reg_write(U.UC_ARM64_REG_PC,a+4)
                if a in [0x10ffa94,0x10ffa9c]:hit.append(a);u.emu_stop()
            uc.hook_add(UC_HOOK_CODE,hook);uc.emu_start(0x10ffa64,0x10ffaa0,count=35)
            filters.append(dict(ability=ability,enabled=enabled,accepted=hit==[0x10ffa94]))
    check('exact_type_and_enable_filter',all(v['accepted']==(v['ability']==9 and v['enabled']==1) for v in filters),samples=filters)
    gates=[]
    for dmg in [0,1,2,3]:
        for enabled in [0,1]:
            uc=machine();uc.reg_write(U.UC_ARM64_REG_W21,dmg);uc.mem_write(0x4001f00c,struct.pack('<I',enabled));hit=[]
            def hook(u,a,s,d):
                if a in [0x13108ac,0x13108b0]:hit.append(a);u.emu_stop()
            uc.hook_add(UC_HOOK_CODE,hook);uc.emu_start(0x131088c,0x13108b4,count=20)
            gates.append(dict(dmgtype=dmg,bCheckAbility=enabled,reads_ability=hit==[0x13108ac]))
    check('initialize_read_gate',all(v['reads_ability']==(v['dmgtype']!=1 and v['bCheckAbility']==1) for v in gates),samples=gates)
    hit_routes=[]
    for flag in [0,1,1<<20,(1<<20)|1]:
        uc=machine();uc.reg_write(U.UC_ARM64_REG_W26,flag);reached=[]
        def route(u,a,s,d):
            if a in [0x131156c,0x13116f8]:reached.append(a);u.emu_stop()
        uc.hook_add(UC_HOOK_CODE,route);uc.emu_start(0x1311568,0x1311700,count=4)
        hit_routes.append(dict(flag=flag,multihit=reached==[0x13116f8]))
    check('multihit_route_bit0',all(v['multihit']==bool(v['flag']&1) for v in hit_routes),samples=hit_routes)
    killed=[]
    for stop in [0,1]:
        for flag in [0,1<<20]:
            for alive in [0,1]:
                uc=machine();bullet=0x40001000;slot=0x40002000;klass=0x40003000
                uc.reg_write(U.UC_ARM64_REG_X19,bullet);uc.reg_write(U.UC_ARM64_REG_X21,0x40004000)
                uc.reg_write(U.UC_ARM64_REG_X23,slot);uc.reg_write(U.UC_ARM64_REG_X24,slot)
                uc.mem_write(slot,struct.pack('<Q',klass));uc.mem_write(klass+0xe0,struct.pack('<I',1))
                uc.mem_write(bullet+0x88,bytes([stop]));uc.mem_write(bullet+0x58,struct.pack('<Q',flag));reached=[]
                def route(u,a,s,d):
                    if a in [0x1311640,0x1311654]:
                        u.reg_write(U.UC_ARM64_REG_W0,1 if a==0x1311640 else alive);u.reg_write(U.UC_ARM64_REG_PC,a+4)
                    if a in [0x131165c,0x1311a10]:reached.append(a);u.emu_stop()
                uc.hook_add(UC_HOOK_CODE,route);uc.emu_start(0x1311604,0x1311a14,count=40)
                killed.append(dict(stop=stop,flag=flag,alive=alive,updates=reached==[0x1311a10]))
    check('non_multihit_shot_through_killed_target_gate',all(v['updates']==(not v['stop'] and v['flag']==1<<20 and not v['alive']) for v in killed),samples=killed)
    # Run complete selection loop with declared enabled records. param3=0 and param2=0
    # isolate p0: the flag-probability and initial-damage fields do not supply p0.
    selected=[]
    for values,want in [([0.5],0.5),([0],0),([1,2],2),([2,1],2),([1.25,1.25],1.25),([-0.5,0],0)]:
        uc=machine();bullet=0x40001000;parent=0x40002000;bp=0x40003000;arr=0x40004000;idx=0x40005000
        uc.mem_write(parent+0x28,struct.pack('<Q',bp));uc.mem_write(bp+0x1e0,struct.pack('<Q',arr))
        recs={0x40006000+i*0x100:v for i,v in enumerate(values)}
        for i,ptr in enumerate(recs):uc.mem_write(arr+0x20+8*i,struct.pack('<Q',ptr))
        uc.mem_write(idx,bytes(range(len(values))));uc.reg_write(U.UC_ARM64_REG_X0,idx);uc.reg_write(U.UC_ARM64_REG_W1,len(values))
        uc.reg_write(U.UC_ARM64_REG_X19,bullet);uc.reg_write(U.UC_ARM64_REG_X20,parent)
        uc.mem_map(0x29ab000,0x1000);uc.mem_write(0x29ab820,struct.pack('<Q',0x40007000))
        uc.mem_write(0x40007000,struct.pack('<Q',0x40008000))
        uc.mem_write(0x400080b8,struct.pack('<Q',0x40009000));uc.mem_write(0x40009000,struct.pack('<f',0.000001))
        def hook(u,a,s,d):
            if a in [0x1310a64,0x1310ab4,0x1310ac4,0x1310adc,0x1310b24]:
                ptr=u.reg_read(U.UC_ARM64_REG_X0);sf(u,0,recs[ptr] if a in [0x1310ab4,0x1310ac4,0x1310b24] else 0)
                u.reg_write(U.UC_ARM64_REG_PC,a+4)
            if a==0x1310aa0:u.reg_write(U.UC_ARM64_REG_X0,0);u.reg_write(U.UC_ARM64_REG_PC,a+4)
        uc.hook_add(UC_HOOK_CODE,hook);uc.emu_start(0x1310a14,0x1310b2c,count=400)
        actual=struct.unpack('<f',uc.mem_read(bullet+0x50,4))[0]
        selected.append(dict(inputs=values,expected=want,actual=actual))
    check('native_selects_max_including_zero',all(v['actual']==v['expected'] for v in selected),samples=selected)
    # Execute Attack -> post-hit multiply -> REAL converter -> writeback over 3 hits.
    # Expected sequences are literal, independent of the production formatter.
    sequences=[]
    for p,start,want in [(2,101,[101,202,404,808]),(.5,101,[101,50,25,12]),(1.25,101,[101,126,157,196]),
                         (1,101,[101,101,101,101]),(0,101,[101,0,0,0]),(-.5,101,[101,-50,25,-12])]:
        uc=machine();bullet=0x40001000;damageptr=0x40002000
        uc.reg_write(U.UC_ARM64_REG_X19,bullet);uc.reg_write(U.UC_ARM64_REG_X20,0x40003000)
        uc.mem_write(bullet+0x48,struct.pack('<Q',damageptr));uc.mem_write(bullet+0x50,struct.pack('<f',p))
        uc.mem_write(bullet,struct.pack('<Q',0x40004000));uc.mem_write(damageptr+0x10,struct.pack('<i',start))
        attacks=[]
        def hook(u,a,s,d):
            if a==0x1311750:u.reg_write(U.UC_ARM64_REG_W0,struct.unpack('<i',u.mem_read(damageptr+0x10,4))[0]&0xffffffff);u.reg_write(U.UC_ARM64_REG_PC,a+4)
            if a==0x1311790:attacks.append(u.reg_read(U.UC_ARM64_REG_W3));u.reg_write(U.UC_ARM64_REG_PC,a+4)
            if a in [0x13117a0,0x13117ac]:u.reg_write(U.UC_ARM64_REG_PC,a+4)
            if a==0x13117d8:u.mem_write(damageptr+0x10,struct.pack('<I',u.reg_read(U.UC_ARM64_REG_W1)));u.reg_write(U.UC_ARM64_REG_PC,a+4)
        uc.hook_add(UC_HOOK_CODE,hook)
        for _ in range(3):uc.emu_start(0x1311744,0x13117dc,count=100)
        actual=[x-(1<<32) if x&(1<<31) else x for x in attacks]+[struct.unpack('<i',uc.mem_read(damageptr+0x10,4))[0]]
        sequences.append(dict(p=p,expected=want,actual=actual))
    check('native_first_then_repeated_post_hit_update',all(v['actual']==v['expected'] for v in sequences),samples=sequences)
    integers=[]
    for value,want in [(1.9,1),(-1.9,-1),(2147483648.,2147483647),(-2147483904.,-2147483648),
                       (16777217.,16777216),(float('inf'),-2147483648),(float('-inf'),-2147483648),(float('nan'),0)]:
        uc=machine();sf(uc,0,value);reached=[]
        def ret(u,a,s,d):
            if a in [0x1437720,0x1437728]:reached.append(a);u.emu_stop()
        uc.hook_add(UC_HOOK_CODE,ret);uc.emu_start(0x14376ec,0x143772c,count=25)
        got=uc.reg_read(U.UC_ARM64_REG_W0);got=got-(1<<32) if got&(1<<31) else got
        integers.append(dict(input=str(value),expected=want,actual=got))
    check('real_float32_integer_converter_boundaries',all(v['expected']==v['actual'] for v in integers),samples=integers)
    ranges=[(0x1576548,0x157655c),(0x10ffa0c,0x10ffab0),(0x1112634,0x11126b0),
            (0x1310814,0x13108b0),(0x13109d0,0x1310b2c),(0x1311544,0x1311578),
            (0x1311578,0x131165c),(0x13116f8,0x13117f8),(0x1311a10,0x1311a58),(0x14376ec,0x143772c)]
    slices=[dict(start=hex(a),end=hex(b),sha256=hashlib.sha256(n.raw[a:b]).hexdigest(),
                 instructions=[dict(rva=hex(i.address),op=i.mnemonic+' '+i.op_str) for i in dis.disasm(n.raw[a:b],a)]) for a,b in ranges]
    return dict(generated_by='scripts/character_skills/type9_bullet.py',evidence_kind='CONTROLLED_NATIVE_FRAGMENT',
                native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(md.raw).hexdigest(),
                checks=checks,passed=sum(c['passed'] for c in checks),total=len(checks),slices=slices,
                rejected_lead='type9 param0不是暴击率；(x−1)×100不能标为暴击概率或百分点',
                formula=FORMULA,condition=CONDITION,limits=LIMITS,
                caveat='仅列出原生片段与受控夹具；getter/Attack/列表与初始化作stub，不是实机/完整战斗仿真')


def main():
    C.enable_utf8_console();md=Metadata(C.ROOT/'work/protection/metadata_aei_decoded.bin');n=Native(md)
    ev=native_evidence(n,md);C.write_json(OUT/'native_evidence.json',ev)
    if ev['passed']!=ev['total']:raise SystemExit('type9 native checks failed')
    rules=rule_rows(n,md);C.write_json(OUT/'field_dictionary.json',rules)
    path=C.ROOT/'output/character_skills/skilllist_types/field_dictionary.json';old=C.load_json(path)
    keys={(r['table'],r['effect_type'],r['field_path']) for r in old}
    for r in rules:
        key=(r['table'],r['effect_type'],r['field_path'])
        if key not in keys:old.append(r)
        else:
            idx=next(i for i,v in enumerate(old) if (v['table'],v['effect_type'],v['field_path'])==key)
            if 'scripts/character_skills/type9_bullet.py' not in old[idx].get('evidence',[]):raise ValueError('foreign rule collision')
            old[idx]=r
    C.write_json(path,old)
    print(json.dumps(dict(native_checks=f"{ev['passed']}/{ev['total']}",rules=len(rules)),ensure_ascii=False))


if __name__=='__main__':main()
