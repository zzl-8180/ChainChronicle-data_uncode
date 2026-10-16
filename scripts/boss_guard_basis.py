"""Trace and execute the local player-ATK scale -> type13 fixed-guard basis."""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
import boss_type105_probe as f
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *

OUT=Path('output/boss_chain/type13_basis');OUT.mkdir(parents=True,exist_ok=True)
m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
ranges={'player_card_atk':(0x10fa624,0x10fa688),'player_atk_scale':(0x10faf5c,0x10fb02c),
        'support_guard':(0x1776790,0x17767d0),'integer_truncation':(0x14376ec,0x143772c),
        'addition_fallback':(0x1437488,0x14374a8),'type13_arguments':(0x1188444,0x1188478)}
for name,(a,b) in ranges.items():
    lines=[]
    for i in d.disasm(n.raw[a:b],a):
        comment=''
        if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):
            comment=' ; '+' | '.join(n.method(j)['declaring_type']+'.'+n.method(j)['name'] for j in n.method_by_rva.get(int(i.op_str[1:],16),[]))
        lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{comment}')
    (OUT/(name+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
scale=n.unpack('<f',0x2015cf4)[0];assert abs(scale-.1)<1e-8
trace=dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
           methods=[n.method(i) for i in (4062,7084,5398)],fragments={k:[hex(a),hex(b)] for k,(a,b) in ranges.items()},
           player_scale=dict(rva='0x2015cf4',raw_hex=n.raw[0x2015cf4:0x2015cf8].hex(),float32=scale),
           fields={name:n.fields(ti) for name,ti in [('BattleParam',503),('SupportData',next(i for i,r in enumerate(m.types) if m.string(r[0])=='SupportData'))]},
           limits='APK player construction branch; setup modifiers and actual CardInfo values remain runtime inputs')
(OUT/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')

u,BASE,HEAP,STACK=f.u,f.BASE,f.HEAP,f.STACK
NORMAL,SKILL,BELOVED,CARD,CARD_ATK,SUPPORT=[HEAP+a for a in (0x9000,0x9100,0x9200,0x9300,0x9400,0x9500)]
stop=None;guard_argument=[]
def hook(uc,address,size,data):
    if address==stop:uc.emu_stop();return
    a=address-BASE
    if a==0xa92534:f.x(0,f.r(u.reg_read(UC_ARM64_REG_X0)+0x10));f.ret()
    elif a==0xa9250c:f.w(u.reg_read(UC_ARM64_REG_X0)+0x10,u.reg_read(UC_ARM64_REG_W1));f.ret()
    elif a==0x143732c:
        # Small positive CardInfo + beloved addition adapter; native fallback saved above.
        f.x(0,u.reg_read(UC_ARM64_REG_W0)+u.reg_read(UC_ARM64_REG_W1));f.ret()
    elif a==0x17765e0:
        guard_argument.append(f.rf(1));uc.emu_stop()
    else:f.hook(uc,address,size,data)
u.hook_del(f.hook_handle);u.hook_add(UC_HOOK_CODE,hook)
def run(a,b):
    global stop
    stop=BASE+b;u.emu_start(BASE+a,BASE+b,count=3000)
    assert u.reg_read(UC_ARM64_REG_PC)==BASE+b,(hex(a),hex(u.reg_read(UC_ARM64_REG_PC)))
    stop=None

checks=[]
for atk,beloved,p2,chain,modifier,want_normal,want_guard in ((25000,0,.3,1,1,2500,750),
        (25000,0,.325,1,1,2500,812),(25000,0,.375,1,1,2500,937),
        (25000,0,.3,1.2,1,2500,900),(25000,0,.3,1,1.2,3000,900),
        (25000,100,.3,1,1,2510,753),(137,0,.375,1,1,13,4)):
    f.setup();guard_argument.clear()
    for off,p in ((0x70,NORMAL),(0x78,SKILL),(0xd8,BELOVED)):f.q(f.PARAM+off,p)
    f.q(CARD+0x30,CARD_ATK);f.w(CARD_ATK+0x10,atk);f.w(BELOVED+0x10,beloved)
    f.x(19,f.PARAM);f.x(21,CARD)
    u.reg_write(UC_ARM64_REG_SP,STACK+0xe000)
    run(0x10fa624,0x10fa688)
    assert f.r(NORMAL+0x10)==atk+beloved
    # Explicit neutral setup context, except one varied setup multiplier.
    for off in (0x408,0x428,0x42c,0x438,0x420):f.wf(f.PARAM+off,1)
    f.wf(f.PARAM+0x408,modifier)
    frame=STACK+0xd000;u.reg_write(UC_ARM64_REG_X29,frame)
    for off in (0x144,0x150,0x148):f.wf(frame-off,1)
    for i in (8,10,11,15):f.sf(i,1)
    f.x(19,f.PARAM);run(0x10faf5c,0x10fb02c)
    assert f.r(NORMAL+0x10)==f.r(SKILL+0x10)==want_normal
    # Existing type13 argument multiplication, ending at actual SetSupport boundary.
    f.wf(f.UTIL+0x18,chain);f.wf(f.UTIL+0x34,p2)
    f.q(HEAP+0x7000+0xa0,f.STATUS)
    f.x(25,HEAP+0x7000);f.x(22,f.UTIL);f.x(23,0)
    u.reg_write(UC_ARM64_REG_SP,STACK+0xe000)
    run(0x1188444,0x17765e0)
    guard_argument.append(f.rf(1))
    assert abs(guard_argument[-1]-p2*chain)<1e-6
    f.q(f.STATUS+0xc0,HEAP+0x7000);f.q(HEAP+0x7000+0x28,f.PARAM)
    f.x(19,f.STATUS);f.x(20,SUPPORT);f.sf(11,guard_argument[-1]);f.sf(8,30);f.sf(14,1)
    run(0x1776790,0x17767d0)
    assert f.r(SUPPORT+0x14)==want_guard
    checks.append(dict(name=f'atk{atk}_beloved{beloved}_p2{p2}_chain{chain}_setup{modifier}',passed=True,
                       card_atk_input=atk,beloved_atk=beloved,setup_modifier=modifier,param2=p2,chain=chain,
                       normal_atk=want_normal,stored_guard=want_guard))
result=dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=trace['native_sha256'],checks=checks,
            rule='observed_CreatePlayer_scaling_block=trunc(float32((CardInfo.ATK+belovedAtk)*0.1*supplied_setup_factors)); guard=trunc(float32(current_normalAtk*float32(param2*chain)))',
            limits=['CardInfo/ParamS access and small positive addition use explicit fixtures.',
                    'Player construction setup modifiers are supplied context; no actual player/card level/buff state.',
                    'Later SetupAlwaysAbility/upskilling/mutate paths may further change normalAtk; not simulated here.',
                    'Nominal 3/3.25/3.75% correspondence requires accounting for the 0.1 scale; two integer conversions and setup modifiers remain.',
                    'No full support aggregation or final damage reduction simulated.'])
(OUT/'native_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=len(checks),normal_atk_scale=scale)))
