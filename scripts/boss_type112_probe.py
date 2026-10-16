"""Bounded type112 damage-transfer checks; reuse the type105 native-base fixture."""
import hashlib
import json
import math
import struct
from pathlib import Path

import boss_type105_probe as f
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import *

u, BASE, HEAP, STACK = f.u, f.BASE, f.HEAP, f.STACK
TRAP, BULLET, DAMAGE, FLAGS = [HEAP + a for a in (0x9000, 0xa000, 0xb000, 0xb100)]
bullet_args, attack_inputs = [], []
push_inputs,state_requests=[],[]
attacker_present = True
capture_trap_init = False
trap_args = []
enemy_count = 1
fire_events, deleted_points = [], []
testing_updates = False
testing_layout = False
grid_positions, cleanup_calls = [], []
GRID = HEAP+0xd000
stop_boundary=None

def hook(uc, address, size, data):
    if address==stop_boundary:
        uc.emu_stop();return
    a = address - BASE
    if a == 0xa9250c:  # Plaintext ParamS_int adapter; preserve the native input.
        f.w(u.reg_read(UC_ARM64_REG_X0) + 0x10, u.reg_read(UC_ARM64_REG_W1)); f.ret()
    elif a == 0xa92534:
        f.x(0, f.r(u.reg_read(UC_ARM64_REG_X0) + 0x10)); f.ret()
    elif a == 0xa928b0:
        f.q(u.reg_read(UC_ARM64_REG_X0) + 0x10, u.reg_read(UC_ARM64_REG_X1)); f.ret()
    elif a == 0xa928d8:
        f.x(0, struct.unpack('<Q', u.mem_read(u.reg_read(UC_ARM64_REG_X0) + 0x10, 8))[0]); f.ret()
    elif a == 0x15794fc and capture_trap_init:
        sp=u.reg_read(UC_ARM64_REG_SP)
        trap_args.append(dict(damage=u.reg_read(UC_ARM64_REG_W4),attacker=u.reg_read(UC_ARM64_REG_X1),fire_count=u.reg_read(UC_ARM64_REG_W6),fire_type=u.reg_read(UC_ARM64_REG_W7),interval=struct.unpack('<f',u.mem_read(sp+8,4))[0],push_power=f.rf(0)))
        f.ret()
    elif a == 0x10f2c14:f.x(0,f.scenario.get('target_aparam',0));f.ret()
    elif a == 0x1117404:f.x(0,0);f.ret()
    elif a == 0x10f1b24:f.sf(0,0);f.ret()
    elif a == 0x1538064:state_requests.append(u.reg_read(UC_ARM64_REG_W1));f.ret()
    elif a == 0x1535abc: f.x(0,1);f.ret()  # Explicit live attacker fixture.
    elif a == 0x10bd0d8:
        f.w(u.reg_read(UC_ARM64_REG_X1)+0x18,enemy_count);f.ret()
    elif a == 0x12e6800: f.ret()  # Array.Clear only; managed list metadata is native.
    elif a == 0x1579c6c and testing_updates:
        fire_events.append(dict(point=hex(u.reg_read(UC_ARM64_REG_X0)),fire_count=f.r(u.reg_read(UC_ARM64_REG_X0)+0x70)));f.ret()
    elif a == 0x10bfca4:
        deleted_points.append(hex(u.reg_read(UC_ARM64_REG_X1)));f.ret()
    elif a == 0x10bfcfc:
        cleanup_calls.append(hex(u.reg_read(UC_ARM64_REG_X1)));f.ret()
    elif a == 0x13b1548 and testing_layout:
        f.w(GRID+0x18,3)
        for row in range(3):
            p=HEAP+0xe000+row*0x100
            f.q(GRID+0x20+row*8,p);f.w(p+0x18,6);u.mem_write(p+0x20,bytes(6))
        f.x(0,GRID);f.ret()
    elif a == 0x70e148 and testing_layout:
        f.x(0,GRID+0x20);f.x(1,3);f.ret()  # Managed array/span view adapter.
    elif a == 0x15690a0 and testing_layout:
        col,row=u.reg_read(UC_ARM64_REG_W0),u.reg_read(UC_ARM64_REG_W1)
        grid_positions.append([col,row]);f.sf(0,1.5*(col+.5));f.sf(1,0);f.sf(2,1.5*(row+.5));f.ret()
    elif a in (0x88d910,0x132c460,0x1ec51b8) and testing_layout:
        f.x(0,TRAP if a==0x132c460 else HEAP+0xc900);f.ret()
    elif a in (0x1ec5540,0x1eca4a0,0x10bfbf0) and testing_layout: f.ret()
    elif a == 0x12157f0 and testing_layout: f.x(0,1);f.ret()
    elif a == 0x15793e4: f.x(0,HEAP+0xc900);f.ret()
    elif a == 0x1ec8d4c: f.ret()  # Unity destruction is recorded by the manager callback.
    elif a == 0x15ac398:
        bullet_args.append(dict(damage=u.reg_read(UC_ARM64_REG_W6), parent=u.reg_read(UC_ARM64_REG_X2),push_power=f.rf(3)))
        f.ret()  # The storage fragment is executed separately below.
    elif a == 0x15acd54: f.x(0, f.LIST); f.ret()  # Target selection outside this probe.
    elif a == 0xa84484:
        counter = f.counters[u.reg_read(UC_ARM64_REG_W1)]
        f.x(0, struct.unpack('<Q', u.mem_read(counter + 0x10, 8))[0]); f.ret()
    elif a == 0x1ec91b8: f.x(0, int(attacker_present and u.reg_read(UC_ARM64_REG_X0)!=0)); f.ret()
    elif a in (0x153afc4, 0x15418dc):
        reg = UC_ARM64_REG_W3 if a == 0x153afc4 else UC_ARM64_REG_W2
        attack_inputs.append(dict(entry='Attack' if a == 0x153afc4 else 'AttackOther',
                                  damage_input=u.reg_read(reg)))
        push_inputs.append(f.rf(0))
        f.ret()  # Target defence, elements, flags and HP are outside the boundary.
    else:
        f.hook(uc, address, size, data)

u.hook_del(f.hook_handle)
u.hook_add(UC_HOOK_CODE, hook)

def run(start, end):
    global stop_boundary
    stop_boundary=BASE+end
    try:
        u.emu_start(BASE + start, BASE + end, count=6000)
    except Exception as error:
        raise RuntimeError(f'fragment {start:x}, PC={u.reg_read(UC_ARM64_REG_PC)-BASE:x}') from error
    assert u.reg_read(UC_ARM64_REG_PC) == BASE + end, 'Bounded fragment did not reach stop'
    stop_boundary=None

def setup(p1=.75, **kwargs):
    f.setup(p1=p1, **kwargs)
    bullet_args.clear(); attack_inputs.clear(); trap_args.clear();fire_events.clear();deleted_points.clear();push_inputs.clear();state_requests.clear()
    f.q(TRAP + 0x28, DAMAGE); f.q(TRAP + 0x30, FLAGS)
    f.q(BULLET + 0x48, DAMAGE + 0x200)
    for slot in (0x29bda68, 0x29d5fa0, 0x29ebaf0,0x29ab820): f.q(BASE + slot, f.CLASS_REF)
    f.q(f.STATIC+0x10,HEAP+0xc100)
    for flag in (0x2bd2c1d, 0x2bd2cd5,0x2bd2c1e,0x2bd2c1f,0x2bcf5ba): u.mem_write(BASE + flag, b'\x01')
    u.reg_write(UC_ARM64_REG_SP, STACK + 0xe000)

def compute():
    # Only the native skill-base/multiply/floor block; no placement loop is executed.
    u.reg_write(UC_ARM64_REG_X29, f.UTIL)
    run(0x1198ce8, 0x1198d08)
    return f.r(u.reg_read(UC_ARM64_REG_SP) + 0xb4)

def store_in_trap(value,count=5,interval=.25,fire_type=1,push_power=.001):
    global capture_trap_init
    # Execute the real call site that loads the computed integer from caller stack.
    sp = u.reg_read(UC_ARM64_REG_SP)
    f.w(sp + 0xb4, value); f.w(sp + 0xb0, count); f.w(sp + 0x9c, 0);f.w(sp+0x78,fire_type)
    f.sf(14,interval);f.sf(15,0);f.sf(9,push_power)
    f.x(0, TRAP); f.x(27, f.UTIL); f.x(28, 0)
    capture_trap_init = True
    run(0x11991c4, 0x1199234)
    capture_trap_init = False
    assert all(trap_args[-1][k]==v for k,v in dict(damage=value,attacker=f.ATTACKER,fire_count=count,fire_type=fire_type,interval=interval).items())
    assert abs(trap_args[-1]['push_power']-push_power)<1e-9
    # Enter the real initialize prologue and stop after core data stores, before media.
    f.x(0, TRAP); f.x(1, f.ATTACKER); f.x(2, 1); f.x(3, 0)
    f.x(4, value); f.x(5, 0); f.x(6, count); f.x(7, fire_type)
    for i in range(8): f.sf(i, 0)
    f.sf(0,push_power)
    run(0x15794fc, 0x1579690)
    # The fragment stops inside a prologue; reset the stack for the next bounded entry.
    u.reg_write(UC_ARM64_REG_SP, STACK + 0xe000)
    assert f.r(DAMAGE + 0x10) == value

def shoot_and_store_bullet():
    # Real trap -> BulletDelay.Initialize argument transfer, stopping after that call.
    f.x(19, TRAP); f.x(20, BULLET)
    run(0x1579d90, 0x1579e24)
    value = bullet_args[-1]['damage']
    # Real BulletDelay damage/flag stores; other registers are explicit fixture context.
    sp = u.reg_read(UC_ARM64_REG_SP)
    f.w(sp + 4, value); f.x(19, BULLET); f.x(22, 0); f.x(24, 1)
    f.x(25, f.ATTACKER); f.x(26, HEAP + 0xc000); f.x(27, 1)
    f.x(28, 0); u.reg_write(UC_ARM64_REG_X29, 1); f.sf(9, bullet_args[-1]['push_power'])
    run(0x15ac564, 0x15ac5c4)
    assert f.r(DAMAGE + 0x210) == value
    return value

def attack():
    f.x(0, BULLET); f.x(1, f.ATTACKER)
    u.reg_write(UC_ARM64_REG_LR, BASE + 0x15ad170)  # Bounded sentinel, never executed.
    run(0x15acbac, 0x15ad170)

checks = []
for p1, chain, expected in ((.75, 1, 75), (.875, 1, 87), (1.125, 1, 112), (.75, 1.2, 90)):
    setup(p1=p1, chain=chain)
    value = compute(); assert value == expected
    store_in_trap(value); assert shoot_and_store_bullet() == expected
    attack(); assert attack_inputs == [dict(entry='Attack',damage_input=expected)]
    checks.append(dict(name=f'p1_{p1}_chain_{chain}_stored_and_forwarded',passed=True,
                       native_base=f.bases[0],trap_damage=value,bullet_damage=expected,
                       attack_inputs=list(attack_inputs)))

setup(p1=.875, skill_atk=80, status=1.5, chain=1.2, weapon=.1, ability=1.3,
      shortcut=1.1, support=[1.2,1.1,1.05],skill_ability=1.4)
value = compute(); expected = math.floor(80*1.5*1.2*1.1*1.3*1.1*1.35*1.4*.875)
assert value == expected
store_in_trap(value); shoot_and_store_bullet(); attack()
assert attack_inputs[-1]['damage_input'] == expected
checks.append(dict(name='non_neutral_base_then_fractional_floor',passed=True,
                   inputs=f.scenario,native_base=f.bases[0],damage_input=value))

setup(); value=compute(); store_in_trap(value)
f.wf(f.UTIL + 0x18, 2); f.wf(f.UTIL + 0x30, 9)
assert shoot_and_store_bullet() == value
attack(); assert attack_inputs[-1]['damage_input'] == value and len(f.bases) == 1
checks.append(dict(name='stored_damage_does_not_resample_base_or_chain_on_shoot',passed=True,damage_input=value))

setup(p1=.875,targets=2); value=compute(); store_in_trap(value); shoot_and_store_bullet(); attack()
assert [a['damage_input'] for a in attack_inputs] == [87,87]
checks.append(dict(name='one_bullet_two_targets_same_stored_input',passed=True))
setup(); value=compute(); store_in_trap(value); shoot_and_store_bullet()
attacker_present=False; attack(); attacker_present=True
assert attack_inputs == [dict(entry='AttackOther',damage_input=value)]
checks.append(dict(name='attacker_absent_branch_forwards_same_input',passed=True))

def count_input(raw_count):
    f.wf(f.UTIL+0x40,raw_count)
    u.reg_write(UC_ARM64_REG_X29,f.UTIL)
    run(0x1198d08,0x1198d64)
    return f.r(u.reg_read(UC_ARM64_REG_SP)+0xb0)

def prepare_updates(count=5,interval=.25,fire_type=1):
    global enemy_count,testing_updates
    setup(targets=2);enemy_count=1;testing_updates=True
    decoded=count_input(count)
    store_in_trap(75,decoded,interval,fire_type)
    assert f.r(TRAP+0x6c)==decoded and f.r(TRAP+0x80)==fire_type
    f.q(TRAP+0xb0,f.LIST);f.wf(TRAP+0x68,1)
    f.w(TRAP+0x70,0);f.wf(TRAP+0x74,0);f.wf(TRAP+0x78,0)
    return decoded

def update(delta):
    f.dt=delta
    f.x(0,TRAP);u.reg_write(UC_ARM64_REG_SP,STACK+0xe000)
    u.reg_write(UC_ARM64_REG_LR,BASE+0x15ad170)
    run(0x1579998,0x15ad170)

prepare_updates();timeline=[]
for delta in (.125,.125,.25,.25,.25,.25):
    update(delta);timeline.append((len(fire_events),len(deleted_points)))
assert timeline==[(0,0),(1,0),(2,0),(3,0),(4,0),(5,1)]
checks.append(dict(name='param5_to_max_count_five_interval_boundary_then_remove',passed=True,timeline=timeline))
prepare_updates();enemy_count=0
for _ in range(8):update(.25)
assert not fire_events and f.r(TRAP+0x70)==0 and not deleted_points
enemy_count=1;update(0)
assert len(fire_events)==1 and f.r(TRAP+0x70)==1
checks.append(dict(name='no_enemy_does_not_consume_count_accumulated_timer_fires_on_return',passed=True))
prepare_updates();enemy_count=2;update(.25)
assert len(fire_events)==1 and f.r(TRAP+0x70)==1
checks.append(dict(name='multiple_targets_consume_one_shared_point_fire_count',passed=True))
prepare_updates();update(100)
assert len(fire_events)==1 and f.r(TRAP+0x70)==1
checks.append(dict(name='large_delta_one_fire_no_catchup',passed=True))
prepare_updates(count=2.9)
update(.25);update(.25)
assert len(fire_events)==2 and len(deleted_points)==1
checks.append(dict(name='positive_fractional_param5_truncates_to_two',passed=True))
prepare_updates(fire_type=0);enemy_count=0;update(.25)
assert len(fire_events)==1
checks.append(dict(name='fire_type_zero_does_not_gate_on_enemy_presence',passed=True))
prepare_updates(count=0);update(0)
assert not fire_events and len(deleted_points)==1
prepare_updates(count=0);update(.25)
assert len(fire_events)==1 and len(deleted_points)==1
checks.append(dict(name='zero_count_is_post_fire_stop_check_not_unlimited',passed=True))
testing_updates=False
mode_results=[]
for raw_mode in (1,2):
    setup();f.wf(f.UTIL+0x2c,raw_mode)
    u.reg_write(UC_ARM64_REG_X29,f.UTIL)
    run(0x1198e5c,0x1198e84)
    run(0x1199108,0x1199114)
    result_mode=f.r(u.reg_read(UC_ARM64_REG_SP)+0x78)
    assert result_mode==(1 if raw_mode==1 else 0)
    mode_results.append(dict(raw_param0=raw_mode,fire_type=result_mode))
checks.append(dict(name='param0_one_presence_gate_two_timer_mode',passed=True,modes=mode_results))

def layout(mask=88725,anchor_x=3,anchor_z=1):
    global testing_layout
    setup();testing_layout=True
    f.q(BASE+0x29e8dc0,f.CLASS_REF);f.q(BASE+0x29ed460,f.CLASS_REF)
    f.w(f.STATIC,6);f.w(f.STATIC+4,3)
    for flag in (0x2bd17fb,0x2bcf5bf,0x2bcf93a,0x2bd0efd):u.mem_write(BASE+flag,b'\x01')
    # Native caller converts the float param8 and supplies bEdge=true.
    u.reg_write(UC_ARM64_REG_X29,HEAP+0xc100)
    f.x(19,anchor_x);f.x(20,anchor_z);f.sf(12,mask)
    run(0x11990a0,0x11990d8)
    cells=[]
    for row in range(3):
        p=HEAP+0xe000+row*0x100
        for col,b in enumerate(u.mem_read(p+0x20,6)):
            if b:cells.append([col,row])
    return cells

layouts=[]
for ax,az in ((3,1),(0,0),(5,2)):
    cells=layout(anchor_x=ax,anchor_z=az)
    ox=0
    expected=[[ox+c,r] for r,cols in enumerate(((0,2,4),(1,3,5),(0,2,4))) for c in cols]
    assert cells==expected
    layouts.append(dict(anchor=[ax,az],cells=cells))
checks.append(dict(name='88725_nine_cells_native_mask_and_edge_clamp',passed=True,layouts=layouts))
assert layout(mask=1)==[[0,0]] and layout(mask=1<<17)==[[5,2]]
assert len(layout(mask=(1<<18)-1))==18 and layout(mask=0)==[]
checks.append(dict(name='bit0_bit17_full_and_empty_mask_orientation',passed=True))

cells=layout();grid_positions.clear();trap_args.clear()
for slot in (0x29a5e98,0x29fd0a8,0x29ea600):f.q(BASE+slot,f.CLASS_REF)
sp=u.reg_read(UC_ARM64_REG_SP)
f.q(sp+0x68,GRID);f.q(sp+0x70,3)
f.w(sp+0xb4,75);f.w(sp+0xb0,5);f.w(sp+0x78,1)
f.x(0,GRID);f.x(19,0);f.x(27,f.UTIL);f.x(28,0)
capture_trap_init=True
run(0x1199114,0x11992c4)
capture_trap_init=False
assert len(trap_args)==9 and grid_positions==cells
checks.append(dict(name='placement_loop_nine_initialize_calls_at_native_mask_cells',passed=True,cells=cells))
grid_positions.clear();trap_args.clear()
for _ in range(2):
    f.x(0,GRID);f.x(19,0);f.x(27,f.UTIL);f.x(28,0)
    capture_trap_init=True;run(0x1199114,0x11992c4);capture_trap_init=False
assert len(trap_args)==18 and grid_positions==cells+cells
checks.append(dict(name='two_identical_placement_segments_18_calls_nine_double_positions',passed=True))
for raw_keep in (1,0):
    setup();cleanup_calls.clear();f.wf(f.UTIL+0x50,raw_keep)
    u.reg_write(UC_ARM64_REG_X29,f.UTIL)
    u.mem_write(BASE+0x2bcf5ba,b'\x01')
    run(0x1198c04,0x1198c88)
    assert len(cleanup_calls)==(0 if raw_keep else 1)
checks.append(dict(name='param9_one_skips_old_point_cleanup_zero_calls_cleanup',passed=True))
testing_layout=False

setup();value=compute();store_in_trap(value);shoot_and_store_bullet();attack()
assert abs(push_inputs[-1]-.001)<1e-9
checks.append(dict(name='param7_push_power_through_trap_bullet_attack',passed=True,push_power=push_inputs[-1]))
for push,locked,aparam,flags,want in ((.001,0,0,1<<48,[10]),(0,0,0,1<<48,[]),(.001,1,0,1<<48,[]),(.001,0,0x2000,1<<48,[]),(.001,0,0x2000,(1<<48)|(1<<51),[10])):
    setup();f.scenario['target_aparam']=aparam
    f.q(f.STATUS+0xc0,HEAP+0x7000)
    f.x(19,f.STATUS);f.x(24,flags);f.x(25,locked);f.x(27,f.CLASS_REF);f.sf(8,push)
    run(0x1772b50,0x1772ca4)
    assert state_requests==want
checks.append(dict(name='positive_push_requests_DamageL_state10_with_lock_and_immunity_gates',passed=True,scenarios=5))

result=dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',
            native_sha256=hashlib.sha256(f.raw).hexdigest(),checks=checks,
            executed=['type112 0x1198ce8–0x1198d08 including full shared getBasicSkillAttack arithmetic and floor conversion',
                      'type112 0x11991c4–0x1199234 transfer of computed integer to intercepted CoveringFirePoint.initialize',
                      'CoveringFirePoint.initialize prologue/core stores, before media',
                      'CoveringFirePoint.ShootDelayBullet damage transfer to intercepted BulletDelay.Initialize',
                      'BulletDelay.Initialize core damage/flag stores',
                      'BulletDelay.Attack with supplied valid target list',
                      'type112 param5 integer conversion and initialize argument/core stores',
                      'full CoveringFirePoint.FixedUpdate and IsInEnemy with supplied engine/list/position fixtures',
                      'native param8 conversion, MakeFieldBitArea bit loop/edge handling on initial 6x3 board',
                      'placement loop with object allocation/media calls modeled; nine initialize calls per segment',
                      'param9 cleanup branch',
                      'param7 push-power transfer and CalcAttackedPost bounded push-state gate'],
            limits=['ParamS plaintext adapters, ability providers and target selection use explicit fixtures.',
                    'Fragments are connected by declared fixtures; full placement, media, trigger and runtime loops are not emulated.',
                    'Layout uses cctor initial 6x3 board; runtime battlefield size changes and media instantiation not emulated.',
                    'Push requests DamageL in tested branch; animation/visual correspondence to 転倒 is inferred; target final resistance/state and HP not simulated.',
                    'ShootDelayBullet is intercepted during counter tests; manager deletion is captured, Unity destruction modeled.',
                    'Attack/AttackOther intercepted before defence, elements, flags and actual HP changes.',
                    'Shared base fixture is from boss_type105_probe; no panel ATK conversion or current player state.'])
Path('output/boss_chain/type112/native_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=len(checks))))
