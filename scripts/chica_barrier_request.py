"""Trace ability1080's automatic request without fitting the screenshot's 5%."""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from phase_d_chain_probe import Guest, BASE, STACK, fbits, fvalue
from unicorn.arm64_const import UC_ARM64_REG_S0, UC_ARM64_REG_X8, UC_ARM64_REG_X29

OUT = Path('output/card_comparison_cid30236/barrier_request')
SOURCE = Path('output/cache_full_20261015_v3/records.jsonl')


class RequestGuest(Guest):
    def __init__(self, raw, rows):
        super().__init__(raw, rows)
        self.requests = []
        self.parsed_pattern = int(rows[43023603]['str0'])
        for slot in (0x29d2468, 0x29de7c8, 0x29c1f70, 0x29c3300,
                     0x29d6c70, 0x29a9430, 0x29c16b0, 0x29e5dc8):
            self.metadata(slot)
        for flag in (0x2bcf57d, 0x2bcf5bb, 0x2bd01be, 0x2bd2a4b, 0x2bd00e7, 0x2bd5465):
            self.uc.mem_write(BASE + flag, b'\1')
        self.world = self.alloc(0x100)
        self.put64(self.statics[0x29c3300], self.world)
        wave = self.alloc(0x20)
        self.put64(self.world + 0x50, wave)
        self.integers[wave] = 0
        self.battle = 0

    def hook(self, cpu, address, size, unused):
        rva = address - BASE
        if rva == 0x11e52ac:  # System.Object ctor has no relevant behavior.
            self.ret()
        elif rva == 0xa927c8:
            value = fvalue(cpu.reg_read(UC_ARM64_REG_S0))
            self.floats[self.reg(0)] = (None, 'rule_ctor_float', value, 'NATIVE_CTOR_ARGUMENT')
            self.ret()
        elif rva == 0xa924cc:
            self.integers[self.reg(0)] = self.reg(1) & 0xffffffff
            self.ret()
        elif rva == 0x1dbd484:
            # Managed string allocation/getter and integer parser are explicit models.
            self.ret(self.alloc(0x20))
        elif rva == 0x10ca54c:
            self.put32(self.reg(1), self.parsed_pattern)
            self.ret(1)
        elif rva == 0x12960f8:
            # Pattern construction is already evidenced; preserve actual requested ID.
            self.requests.append(self.reg(1))
            self.ret()
        elif rva == 0x18008e0:
            self.ret(self.battle)
        elif rva == 0xa84484:
            data, count = self.span(self.reg(0))
            index = self.reg(1)
            assert index < count
            self.ret(self.u64(data + index * 8))
        elif rva == 0x143732c:
            # Safe addition wrapper uses engine dispatch. Native fallback arithmetic
            # is independently exercised below; no division or damage factor modeled.
            values = [self.reg(i) & 0xffffffff for i in (0, 1)]
            left, right = [v - 0x100000000 if v >= 0x80000000 else v for v in values]
            self.ret(max(-0x80000000, min(0x7fffffff, left + right)) & 0xffffffff)
        else:
            super().hook(cpu, address, size, unused)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = [json.loads(s) for s in SOURCE.read_text(encoding='utf-8').splitlines()]
    selected = [r for r in records if
                (r['table'] == 'skilllist' and r['raw'].get('skillid') == 43023603)
                or (r['table'] == 'bossskill' and r['raw'].get('skillid') == 43023614)
                or (r['table'] == 'bosspattern' and r['raw'].get('patternid') == 43023603)]
    ability = next(r for r in selected if r['table'] == 'skilllist')
    pattern = next(r for r in selected if r['table'] == 'bosspattern')
    shield = next(r for r in selected if r['table'] == 'bossskill' and r['raw']['skillid'] == 43023614)
    assert ability['raw']['ability'] == 1080 and ability['raw']['str0'] == '43023603'
    assert pattern['raw']['skillid1'] == shield['raw']['skillid']
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    n = Native(m)
    d = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    ranges = dict(
        setup_dispatch=(0x10f4d00, 0x10f4d2c), setup_table=(0x10f4ef4, 0x10f4f10),
        setup_work=(0x10f5dec, 0x10f5e80), auto_ctor=(0x1001564, 0x1001730),
        auto_enable=(0x100175c, 0x1001824), wave_modulo=(0x1001864, 0x1001894),
        queue_auto=(0x1128208, 0x1128474), execute_auto=(0x111499c, 0x11149e0),
        request_at_id=(0x1547754, 0x1547850), default_rule=(0x10fdeb4, 0x10fe034),
        default_struct=(0x10756f8, 0x1075710), player_rule_read=(0x10fa28c, 0x10fa2a0),
        player_rule_store=(0x10fa58c, 0x10fa5a8), extra_chain_getter=(0x10f267c, 0x10f2698),
        rule_extra_getter=(0x1a68a78, 0x1a68a94), request_transfer=(0x1181a00, 0x1181a20),
        support_guard_sum=(0x1776e5c, 0x1776f0c), guard_cache_write=(0x176e7e8, 0x176e7f8), guard_damage_read=(0x177199c, 0x17719cc),
        guard_other_additions=(0x1771b24, 0x1771b38), guard_damage_subtract=(0x1771d54, 0x1771d80),
        safe_add_fallback=(0x1437488, 0x14374a8), rule_ctor=(0x1a68ab0, 0x1a68c78),
        local_load_filename=(0x1a697d0, 0x1a69810))
    for name, (a, b) in ranges.items():
        lines = []
        for ins in d.disasm(n.raw[a:b], a):
            note = ''
            if ins.mnemonic in ('bl', 'b') and ins.op_str.startswith('#0x'):
                note = ' ; ' + ','.join(n.method(k)['declaring_type'] + '.' + n.method(k)['name']
                                      for k in n.method_by_rva.get(int(ins.op_str[1:], 16), []))
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT / (name + '.txt')).write_text('\n'.join(lines), encoding='utf-8')
    enum = next(f for f in n.fields(718) if f['name'] == 'AutoSkill')
    enum_value = n.default(enum['index'])
    assert enum_value['value'] == 1080
    table_entry = n.unpack('<H', 0x206dbb2 + (1080 - 0x421) * 2)[0]
    assert 0x10f4f10 + table_entry * 4 == 0x10f5dec
    trace = dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),
                 metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
                 source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                 script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 source_records=selected, ability_enum=dict(enum, default=enum_value),
                 trigger_enum=[dict(f, default=n.default(f['index'])) for f in n.fields(493) if f['name'] != 'value__'],
                 setup_dispatch=dict(table_rva='0x206dbb2', entry=table_entry, branch_rva='0x10f5dec'),
                 fragments={k: [hex(a), hex(b)] for k, (a, b) in ranges.items()},
                 methods=[n.method(i) for i in (4057, 4063, 4466, 4467, 4839, 4842, 4845, 6378, 6985, 7091, 34446)],
                 rule='Auto request = BattleParam.extraChainRate; GetForceDebuff defaults to 1 without a battle rule, otherwise reads daBattleRule.extra_chain_rate. No automatic .25 is established.',
                 apk_coverage=[], rule_extra_field=next(f for f in n.fields(4286) if f['name']=='_debuff_extra_chain_rate'),
                 local_load_probe=dict(method=n.method(34472), filename_literal=n.literal(0x29b7e98),
                                       limit='Load reads helper.data5 here; not a captured battle-rule source'))
    digest_path = Path('output/cache_full_20261015_v3/decoded/questdigest.data5.json.raw')
    digest_bytes = digest_path.read_bytes()
    digest = json.loads(digest_bytes)
    rule_views = []
    for group, quests in enumerate(digest['questdigest']):
        if not isinstance(quests, list):
            continue
        for ordinal, quest in enumerate(quests):
            if isinstance(quest, dict) and 'battle_rule' in quest:
                rule_views.append(dict(table='questdigest', record_id=quest.get('quest_id'),
                                       record_key='CACHE/questdigest.data5.json.raw#/questdigest/'+str(group),
                                       field_path='/battle_rule', json_pointer=f'/questdigest/{group}/{ordinal}/battle_rule',
                                       raw_value=quest['battle_rule']))
    assert len(rule_views) == 1064 and all(v['raw_value'] == {'rule': 0} for v in rule_views)
    parent_keys = {v['record_key'] for v in rule_views}
    trace['cached_rule_coverage'] = dict(path=digest_path.as_posix(), sha256=hashlib.sha256(digest_bytes).hexdigest(),
                                       views=rule_views, count=len(rule_views),
                                       parent_locations=[{k: r[k] for k in ('record_key','table','original_file','source_sha256','location')}
                                                         for r in records if r['record_key'] in parent_keys],
                                       conclusion='All 1064 captured quest rule summaries are {rule:0}; no explicit extra_chain_rate supplied. The meaning of rule=0 is not inferred.')
    for filename, table, field, sid in (('_mdSkill.json', 'skilllist', 'skillid', 43023603),
                                        ('_mdBossInfo.json', 'bosspattern', 'patternid', 43023603),
                                        ('_mdBossInfo.json', 'bossskill', 'skillid', 43023614)):
        path = Path('output/base_master') / filename
        data = json.loads(path.read_text(encoding='utf-8'))
        hits = [r for r in data[table] if r.get(field) == sid]
        assert not hits
        trace['apk_coverage'].append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                          table=table, id_field=field, record_id=sid, matches=hits))
    (OUT / 'trace.json').write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = {43023603: ability['raw']}
    checks = []

    def check(name, **data):
        checks.append(dict(name=name, **data, passed=True))

    def work_fixture(g):
        obj, work = g.skill(43023603), g.alloc(0x80)
        g.run(0x1001564, work, obj)
        assert g.u64(work + 0x10) == 3 and g.u32(work + 0x20) == 1
        assert g.u32(work + 0x18) == 0xffffffff and g.u32(work + 0x34) == 43023603
        return work

    g = RequestGuest(n.raw, rows)
    work = work_fixture(g)
    check('source_ctor_entry_and_every_wave', flag_mask=3, wave_divisor=1, max_executions=-1, boss_pattern_id=43023603,
          missing_param6_7='Native getter returns 0 for null; source remains absent')
    for flag, want in ((0, 1), (1, 1), (2, 0), (3, 0), (4, 0)):
        actual = g.run(0x100175c, work, flag)[0]
        assert actual == want
        check('native_trigger_' + str(flag), trigger=flag, result=actual)
    for wave in (0, 1, 2, 10):
        actual = g.run(0x1001864, work, wave)[0]
        assert actual == int(wave >= 1)
        check('wave_divisor_' + str(wave), wave=wave, result=actual)
    # GetForceDebuff executes its real default constructor; no battle rule supplied.
    for label, battle_ptr in (('no_battle', 0), ('no_rule', g.alloc(0x100))):
        g.battle = battle_ptr
        result = g.alloc(0x30)
        g.uc.reg_write(UC_ARM64_REG_X8, result)
        g.run(0x10fdeb4)
        rate = struct.unpack('<f', g.uc.mem_read(result + 0x14, 4))[0]
        assert rate == 1
        check(label + '_default_extra_chain_rate', result=rate)
    rule = g.alloc(0xe0)
    g.run(0x1a68ab0, rule)
    g.run(0x1a68a78, rule)
    rate = fvalue(g.uc.reg_read(UC_ARM64_REG_S0))
    assert rate == 1
    check('present_rule_ctor_default_extra_chain_rate', result=rate, field='_debuff_extra_chain_rate', offset='0xd0',
          engine_model='ParamS constructors/getter supplied; native rule ctor constant and field assignment execute')
    g.battle = g.alloc(0x100)
    g.put64(g.battle + 0x60, rule)
    result = g.alloc(0x30)
    g.uc.reg_write(UC_ARM64_REG_X8, result)
    g.run(0x10fdeb4)
    rate = struct.unpack('<f', g.uc.mem_read(result + 0x14, 4))[0]
    assert rate == 1
    check('present_rule_force_debuff_default_extra_chain_rate', result=rate)
    for flag in (0, 1):
        for extra_rate in (1, .25, 1.4):
            g = RequestGuest(n.raw, rows)
            work = work_fixture(g)
            bp, actor, status, pending = g.alloc(0x900), g.alloc(0x400), g.alloc(0x300), g.alloc(0x40)
            g.put64(bp + 0x3f0, actor)
            g.put64(actor + 0xa0, status)
            g.put64(actor + 0x28, bp)
            g.put64(bp + 0x8c8, g.collection([work]))
            g.put64(bp + 0x8d0, pending)
            rate_obj = g.alloc(0x20)
            g.floats[rate_obj] = (None, 'runtime_extra_chain_rate', extra_rate, 'EXPLICIT_FIXTURE')
            g.put64(bp + 0x1d8, rate_obj)
            # Supply the existing bhSkill behavior instance and its real type ancestry.
            obj, cls = g.alloc(0x40), g.alloc(0x180)
            cell = g.u64(BASE + 0x29d6c70)
            type_cls = g.u64(cell)
            g.uc.mem_write(type_cls + 0x12c, b'\1')
            g.uc.mem_write(cls + 0x12c, b'\1')
            g.put64(cls + 0xc8, g.array([type_cls]) + 0x20)
            g.put64(obj, cls)
            g.put64(actor + 0x140, g.array([obj]))
            g.run(0x1128208, bp, flag, 1)
            assert g.u64(pending + 0x10) == work
            g.run(0x111499c, bp)
            request = struct.unpack('<f', g.uc.mem_read(actor + 0x12c, 4))[0]
            assert g.requests == [43023603] and request == fvalue(fbits(extra_rate))
            util = g.alloc(0x200)
            g.setreg(22, actor)
            g.setreg(19, util)
            g.uc.reg_write(UC_ARM64_REG_S0 + 1, fbits(1))
            g.run(0x1181a10, stop=0x1181a20)
            stored = struct.unpack('<f', g.uc.mem_read(util + 0x18, 4))[0]
            assert stored == request
            check(f'auto_{flag}_extra_rate_{extra_rate}', trigger=flag, supplied_battle_rule_factor=extra_rate,
                  requested_pattern_id=g.requests[0], request_factor=request, boss_skill_chain_rate=stored)
    # Existing fixed-guard proof establishes storage; aggregation adds it unchanged.
    for guards in ((5000,), (1250,), (5000, 750)):
        g = RequestGuest(n.raw, rows)
        status = g.alloc(0x300)
        items = [g.alloc(0x80) for _ in guards]
        for obj, value in zip(items, guards):
            g.put32(obj + 0x14, value)
        g.put64(status + 0x1f0, g.collection(items))
        g.uc.mem_write(BASE + 0x2bd37d7, b'\1')
        for slot in (0x299f8d0, 0x29e1f10):
            g.metadata(slot)
        actual = g.run(0x1776e5c, status)[0]
        assert actual == sum(guards)
        check('guard_sum_' + '_'.join(map(str, guards)), stored_guards=list(guards), summed_guard=actual)
    for damage, guard, want in ((10000, 5000, 5000), (10000, 1250, 8750), (1500, 5000, 1)):
        g = RequestGuest(n.raw, rows)
        g.setreg(19, (-guard) & 0xffffffff)
        g.setreg(20, damage)
        g.run(0x1437488, stop=0x14374a8)
        signed = g.reg(0) & 0xffffffff
        signed = signed - 0x100000000 if signed >= 0x80000000 else signed
        assert signed == damage - guard
        check(f'native_add_fallback_{damage}_{guard}', damage=damage, negative_guard=-guard, result=signed)
        frame, value = STACK + 0xe0000, g.alloc(0x20)
        g.put32(value, damage)
        g.put64(frame - 0x108, value)
        g.uc.reg_write(UC_ARM64_REG_X29, frame)
        g.setreg(24, guard)
        g.metadata(0x29ab820)
        g.run(0x1771d54, stop=0x1771d80)
        actual = g.u32(value)
        assert actual == want
        check(f'fixed_guard_damage_step_{damage}_{guard}', input_damage=damage, aggregated_fixed_guard=guard,
              damage_after_this_step=actual, safe_add_dispatch='modeled; native arithmetic fallback separately checked')
    result = dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT', native_sha256=trace['native_sha256'], checks=checks,
                  limits=['Installed source work/list, available bhSkill behavior and neutral status are fixtures; engine list/string utilities modeled.',
                          'Native constructor, trigger qualification, queue, RequestSkillAtId and request transfer execute. No real player or full battle executed.',
                          'Extra rule factors .25/1.4 are sensitivity fixtures, not actual cid30236 battle settings. Default1 is separately executed with no rule and with a native-constructed rule object.',
                          'ParamS constructors/getter are explicit scalar models; rule ctor constant/field assignment and GetForceDebuff are native execution. Captured quest summaries are not runtime battle rule objects.',
                          'Guard aggregation and fixed-guard subtraction have no quarter scaling. The tested damage step is max(1,damage-guard); safe-add wrapper dispatch is modeled, fallback native arithmetic separately executes.',
                          'Full damage path eligibility, later HP loss, shield flag/lifecycle and active battle rule remain outside these fragments.',
                          'APK exports lack the three requested IDs; this is no evidence of an old .5 guard coefficient.'])
    (OUT / 'native_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=len(checks), automatic_request='battle rule extra_chain_rate; default1')))


if __name__ == '__main__':
    main()
