"""Execute type105 arithmetic/counter code with explicit engine/ability stubs."""
import hashlib
import json
import math
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

BASE, HEAP, STACK, STOP = 0x50000000, 0x10000000, 0x20000000, 0x30000000
raw = Path('work/protection/il2cpp_loader_seed1.bin').read_bytes()
u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
u.mem_map(BASE, (len(raw) + 4095) & ~4095)
u.mem_write(BASE, raw)
for address in (HEAP, STACK, STOP):
    u.mem_map(address, 0x10000)

def w(a, v): u.mem_write(a, struct.pack('<I', v & 0xffffffff))
def q(a, v): u.mem_write(a, struct.pack('<Q', v))
def r(a): return struct.unpack('<I', u.mem_read(a, 4))[0]
def wf(a, v): u.mem_write(a, struct.pack('<f', v))
def sf(i, v): u.reg_write(UC_ARM64_REG_S0 + i, struct.unpack('<I', struct.pack('<f', v))[0])
def rf(i): return struct.unpack('<f', struct.pack('<I', u.reg_read(UC_ARM64_REG_S0 + i)))[0]
def x(i, v): u.reg_write(UC_ARM64_REG_X0 + i, v)
def ret(): u.reg_write(UC_ARM64_REG_PC, u.reg_read(UC_ARM64_REG_LR))

UTIL, ATTACKER, PARAM, STATUS = [HEAP + i for i in (0, 0x1000, 0x2000, 0x3000)]
LIST, FLAGS = HEAP + 0x4000, HEAP + 0x4800
CLASS_REF, CLASS, STATIC = [HEAP + i for i in (0x5000, 0x5100, 0x5300)]
calls, bases, counters = [], [], []
scenario = {}
dt = 0.1

def hook(uc, address, size, data):
    a = address - BASE
    if a == 0xa92830:  # ParamS_float.get_Value: explicit plaintext fixture adapter.
        sf(0, struct.unpack('<f', u.mem_read(u.reg_read(UC_ARM64_REG_X0) + 0x10, 4))[0]); ret()
    elif a == 0xa928d8: x(0, 0); ret()  # Fixture attack flags are zero.
    elif a in (0x111541c, 0x11155a4): ret()  # Charge side effects excluded.
    elif a == 0x10f19c4: sf(0, scenario['weapon']); ret()
    elif a == 0x1115e74: sf(0, scenario['ability']); ret()
    elif a == 0x1116c78: x(0, 0); ret()  # Both mana-dependent abilities absent.
    elif a == 0x118319c: sf(0, scenario['skill_ability']); ret()
    elif a == 0x1183194: bases.append(rf(0))  # Native base returned before param1.
    elif a in (0x11826c0, 0x1180a78, 0x1184f68): x(0, 0); ret()
    elif a == 0xa84484: x(0, counters[u.reg_read(UC_ARM64_REG_W1)]); ret()
    elif a == 0x1eb8358: x(0, 0); ret()  # Fixture targets are valid Unity objects.
    elif a == 0x10aedc0: sf(0, dt); ret()
    elif a == 0x1ec9a98:
        is_target = u.reg_read(UC_ARM64_REG_X0) != ATTACKER + 0x800
        sf(0, scenario['target_x'] if is_target else 0); sf(1, 0); sf(2, 0); ret()
    elif a == 0x10f25bc: sf(0, 0.5); ret()
    elif a == 0x10f38e8: sf(0, 1); ret()
    elif a == 0x153b090:
        calls.append(dict(target=hex(u.reg_read(UC_ARM64_REG_X2)),
                          damage_input=u.reg_read(UC_ARM64_REG_W3)))
        ret()  # Do not execute target defence, HP, flags or hit effects.
    elif a == 0x88d920:
        raise AssertionError('Unexpected null/error path')

hook_handle = u.hook_add(UC_HOOK_CODE, hook)

def setup(p1=3.5, count=5, targets=1, **overrides):
    global scenario, counters
    scenario = dict(skill_atk=100, status=1, chain=1, weapon=0, ability=1,
                    shortcut=1, support=[1, 1, 1], skill_ability=1, target_x=0)
    scenario.update(overrides)
    u.mem_write(HEAP, bytes(0x10000))
    calls.clear(); bases.clear()
    q(CLASS_REF, CLASS); w(CLASS + 0xe0, 1); q(CLASS + 0xb8, STATIC)
    for slot in (0x29e25e0, 0x29fc098, 0x29b2c30, 0x29f0b88, 0x29bab78):
        q(BASE + slot, CLASS_REF)
    for flag in (0x2bd04dd, 0x2bd0509, 0x2bd24ed):
        u.mem_write(BASE + flag, b'\x01')
    q(UTIL + 0xb8, ATTACKER); q(ATTACKER + 0x28, PARAM)
    q(ATTACKER + 0xa0, STATUS); q(ATTACKER + 0x160, ATTACKER + 0x800)
    q(UTIL + 0x108, LIST); w(LIST + 0x18, targets)
    for off, value in ((0x30, p1), (0x34, 6.75), (0x38, 3.5), (0x3c, 1.5),
                       (0x40, .1), (0x44, count), (0x48, 0),
                       (0x18, scenario['chain']), (0x120, scenario['shortcut'])):
        wf(UTIL + off, value)
    w(UTIL + 0x14, 1)
    for off, value, loc in ((0x20, scenario['skill_atk'], HEAP + 0x6000),
                            (0x58, scenario['status'], HEAP + 0x6100)):
        q(UTIL + off, loc); wf(loc + 0x10, value)
    for i, value in enumerate(scenario['support']):
        ctrl, support = HEAP + 0x6200 + i * 0x100, HEAP + 0x6600 + i * 0x100
        q(STATUS + 0x230 + i * 8, ctrl); q(ctrl + 0x18, support); wf(support + 0x18, value)
    counters = []
    for i in range(targets):
        target, counter = HEAP + 0x7000 + i * 0x400, HEAP + 0x8000 + i * 0x100
        q(target + 0x160, target + 0x200); q(target + 0x28, PARAM)
        q(counter + 0x10, target); counters.append(counter)
    u.mem_write(FLAGS, b'\x01\x01')  # Existing per-target list; creation is outside probe.

def update(delta=.1):
    global dt
    dt = delta
    x(0, UTIL); x(1, 1); x(2, FLAGS); x(3, FLAGS + 1); x(4, 0)
    u.reg_write(UC_ARM64_REG_SP, STACK + 0xf000)
    u.reg_write(UC_ARM64_REG_LR, STOP)
    u.emu_start(BASE + 0x118a20c, STOP, count=6000)
    assert u.reg_read(UC_ARM64_REG_PC) == STOP, 'Instruction limit or unexpected exit'

if __name__ == '__main__':
    checks = []
    for p1, chain, expected in ((3.5, 1, 350), (3.5, 1.2, 420), (3.75, 1, 375), (4.25, 1, 425)):
        setup(p1=p1, chain=chain)
        counts = []
        for _ in range(7):
            update(); counts.append(len(calls))
        assert counts == [1, 2, 3, 4, 5, 5, 5]
        assert all(c['damage_input'] == expected for c in calls)
        checks.append(dict(name=f'p1_{p1}_chain_{chain}_five_calls', passed=True,
                           native_base=bases[0], damage_input=expected, cumulative_calls=counts))

    setup(p1=3.5, skill_atk=80, status=1.5, chain=1.2, weapon=.1, ability=1.3,
          shortcut=1.1, support=[1.2, 1.1, 1.05], skill_ability=1.4)
    update()
    expected_base = 80 * 1.5 * 1.2 * 1.3 * 1.1 * 1.35 * 1.1 * 1.4
    assert abs(bases[0] - expected_base) < .001
    assert calls[0]['damage_input'] == math.floor(expected_base * 3.5)
    checks.append(dict(name='non_neutral_base_factors_then_param1_floor', passed=True,
                       inputs=scenario, native_base=bases[0], damage_input=calls[0]['damage_input']))

    setup(targets=2)
    for _ in range(7): update()
    assert len(calls) == 10 and [r(c + 0x18) for c in counters] == [5, 5]
    checks.append(dict(name='counter_is_per_target', passed=True, calls=len(calls)))
    setup(count=5.9)
    for _ in range(7): update()
    assert len(calls) == 5
    checks.append(dict(name='positive_fractional_count_truncates', passed=True))
    setup(count=0); update()
    assert not calls
    checks.append(dict(name='zero_count_no_attack', passed=True))
    setup(); update(100)
    assert len(calls) == 1 and r(counters[0] + 0x18) == 1
    checks.append(dict(name='large_delta_one_attempt_per_target_per_update', passed=True))
    setup(); update(0); update(.01)
    assert len(calls) == 1
    checks.append(dict(name='reset_interval_blocks_early_next_attempt', passed=True))
    setup(target_x=100)
    for _ in range(5): update()
    scenario['target_x'] = 0; update()
    assert not calls and r(counters[0] + 0x18) == 5
    checks.append(dict(name='out_of_range_consumes_attempt_budget', passed=True))

    result = dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT',
                  native_sha256=hashlib.sha256(raw).hexdigest(), checks=checks,
                  executed=['full Exec_ATTACK_FRONT_REPEAT with existing target list',
                            'full getBasicSkillAttack(true) arithmetic with listed stubs',
                            '0x14374bc floor/clamp conversion, ordinary finite inputs'],
                  limits=['Engine object/list/position access, ParamS getters and ability providers are modeled.',
                          'No list creation, pattern selection, runtime initialization or actual player state.',
                          'Attack is intercepted: damage_input is before target defence and actual HP reduction.',
                          'Base provider values are fixture inputs; no panel ATK conversion or final battle multiplier proven.'])
    Path('output/boss_chain/type105/native_checks.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=len(checks))))
