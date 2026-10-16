"""Bound the Chain probability to one button event and one installed work."""
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from chica_mana_chance import ManaGuest
from phase_d_chain_probe import BASE, fbits
from unicorn.arm64_const import UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2

OUT = Path('output/card_comparison_cid30236/chain_dispatch')
SOURCE = Path('output/cache_full_20261015_v3/records.jsonl')


class DispatchGuest(ManaGuest):
    def __init__(self, raw, rows):
        super().__init__(raw, rows)
        self.draws, self.awards, self.dispatches = [], [], []
        self.random_values = [.15]
        self.alive = set()
        for slot in (0x29fbd08, 0x29df6b0, 0x29a7ed8, 0x29a24c0, 0x29ee778,
                     0x29ab820, 0x29d5498, 0x29de4a8, 0x29f2098):
            self.metadata(slot)
        for flag in (0x2bd2ca2, 0x2bd2cc0, 0x2bd016b, 0x2bcf5bc):
            self.uc.mem_write(BASE + flag, b'\1')
        self.put32(self.statics[0x29ab820], 1)  # Single.Epsilon, explicit scalar.
        self.player = self.alloc(0x100)
        self.put64(self.statics[0x29d5498], self.player)
        self.put64(self.player + 0x58, self.alloc(0x100))
        self.uc.mem_write(self.player + 0x72, b'\1')  # Supplied request eligibility.
        self.actor, self.bp, self.work = self.alloc(0x400), self.alloc(0x900), self.alloc(0x40)
        self.put64(self.actor + 0x28, self.bp)
        self.put64(self.actor + 0x160, self.alloc(0x40))
        self.put64(self.bp + 0x3f0, self.actor)
        self.put64(self.work + 0x18, self.skill(43023617))
        self.put64(self.bp + 0x6d0, self.collection([self.work]))
        self.members = self.collection([self.actor])
        self.alive.add(self.actor)

    def hook(self, cpu, address, size, unused):
        rva = address - BASE
        if rva == 0x10b6440:
            self.ret(self.members)
        elif rva == 0x1535abc:
            self.ret(int(self.reg(0) in self.alive))
        elif rva == 0x1ec9a98:
            for register in (UC_ARM64_REG_S0, UC_ARM64_REG_S1, UC_ARM64_REG_S2):
                cpu.reg_write(register, fbits(0))
            self.ret()
        elif rva == 0x19072ec:
            assert self.random_values, 'Unexpected additional random draw'
            self.random = self.random_values.pop(0)
            self.draws.append(self.random)
            super().hook(cpu, address, size, unused)
        elif rva == 0x158eb6c:
            self.awards.append(dict(mana_kind=self.reg(1), param6=self.reg(2), amount=self.reg(3)))
            self.ret()
        else:
            if rva == 0x1124674:
                self.dispatches.append(dict(battle_param=self.reg(0), chain_num=self.reg(2)))
            super().hook(cpu, address, size, unused)

    def chain(self, count):
        obj = self.alloc(0x30)
        self.put64(obj + 0x10, self.array(list(range(count)), fmt='I', capacity=max(count, 8)))
        self.put32(obj + 0x18, count)
        self.put64(self.player + 0x38, obj)

    def button_dispatch(self, count):
        self.chain(count)
        self.setreg(28, self.player)
        self.setreg(19, self.actor)
        self.run(0x13a24b8, stop=0x13a24d8)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = [json.loads(s) for s in SOURCE.read_text(encoding='utf-8').splitlines()]
    selected = [r for r in records if (r['table'] == 'skilllist' and r['raw'].get('skillid') in (43023617, 43023632))
                or (r['table'] == 'extra_ability_info' and r['raw'].get('cid') == 30236)]
    extra = next(r for r in selected if r['table'] == 'extra_ability_info')
    assert all(level['skill_ids'].count(43023632) == 1 for level in extra['raw']['extra_abilities'])
    rows = {r['raw']['skillid']: r['raw'] for r in selected if r['table'] == 'skilllist'}
    m = Metadata('work/protection/metadata_aei_decoded.bin')
    n = Native(m)
    d = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    ranges = dict(button_order=(0x13a2224, 0x13a2244), button_count_to_dispatch=(0x13a24b8, 0x13a24d8),
                  chain_append=(0x15a915c, 0x15a91c8), chain_getter=(0x15a4088, 0x15a40d4),
                  member_dispatch=(0x15a39c4, 0x15a3b10), work_event=(0x1124674, 0x1124980))
    for name, (a, b) in ranges.items():
        lines = []
        for ins in d.disasm(n.raw[a:b], a):
            note = ''
            if ins.mnemonic in ('bl', 'b') and ins.op_str.startswith('#0x'):
                note = ' ; ' + ','.join(n.method(k)['declaring_type'] + '.' + n.method(k)['name']
                                      for k in n.method_by_rva.get(int(ins.op_str[1:], 16), []))
            lines.append(f'{ins.address:08x}: {ins.mnemonic} {ins.op_str}{note}')
        (OUT / (name + '.txt')).write_text('\n'.join(lines), encoding='utf-8')
    previous = OUT.parent / 'chain_mana' / 'trace.json'
    assert json.loads(previous.read_text(encoding='utf-8'))['native_sha256'] == hashlib.sha256(n.raw).hexdigest()
    trace = dict(native_sha256=hashlib.sha256(n.raw).hexdigest(), metadata_sha256=hashlib.sha256(m.raw).hexdigest(),
                 source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                 script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), source_records=selected,
                 fragments={k: [hex(a), hex(b)] for k, (a, b) in ranges.items()},
                 methods=[n.method(i) for i in (7894, 8902, 8943, 8945, 4333)],
                 reused_rate_proof=dict(path=previous.as_posix(), sha256=hashlib.sha256(previous.read_bytes()).hexdigest()),
                 limits='Only selected button dispatch slices, a supplied unique live member and one installed work; no full button flow, roster or actual mana object.')
    (OUT / 'trace.json').write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding='utf-8')
    checks = []

    def check(name, **data):
        checks.append(dict(name=name, **data, passed=True))

    for before in range(5):
        g = DispatchGuest(n.raw, rows)
        g.chain(before)
        g.setreg(19, g.player)
        g.setreg(20, g.actor)
        g.run(0x15a915c, stop=0x15a91c8)
        count = g.run(0x15a4088, g.player)[0]
        assert count == before + 1
        check('native_chain_append_' + str(before), list_count_before=before, list_count_after=count)
    for count in (0, 1, 2, 3, 4, 5, 6):
        g = DispatchGuest(n.raw, rows)
        g.button_dispatch(count)
        assert g.dispatches == [dict(battle_param=g.bp, chain_num=min(count, 5))]
        assert len(g.draws) == int(count >= 2) and not g.awards
        check('button_one_work_' + str(count), list_count=count, dispatched_chain_num=min(count, 5),
              work_calls=len(g.dispatches), random_calls=len(g.draws), random_values=g.draws, award_count=0)
    for sequence, counts, expected_draws, expected_awards in (
            ([.15, .15, .15, .15], (2, 3, 4, 5), 4, 0),
            ([.15, .05], (2, 3, 4, 5), 2, 1),
            ([.05, .15], (2, 3, 1, 2), 2, 1)):
        g = DispatchGuest(n.raw, rows)
        g.random_values = list(sequence)
        for count in counts:
            g.button_dispatch(count)
        assert len(g.draws) == expected_draws and len(g.awards) == expected_awards
        assert all(a['amount'] == 1 and a['param6'] == 4 for a in g.awards)
        check('sequence_' + '_'.join(map(str, counts)) + '_' + str(sequence[0]), chain_list_counts=list(counts),
              random_values=g.draws, random_calls=len(g.draws), award_inputs=g.awards,
              latched=bool(g.uc.mem_read(g.work + 0x10, 1)[0]))
    g = DispatchGuest(n.raw, rows)
    dead = g.alloc(0x400)
    g.members = g.collection([g.actor, dead, 0])
    g.button_dispatch(2)
    assert len(g.dispatches) == len(g.draws) == 1
    check('unique_live_member_dead_and_null', roster_entries=3, supplied_live_entries=1, work_calls=1, random_calls=1)
    check('each_extra_level_has_one_reference', level_count=len(extra['raw']['extra_abilities']), reference_id=43023632,
          count_per_level=1, note='Levels are alternative records; their presence does not prove runtime installation.')
    result = dict(evidence_kind='CONTROLLED_NATIVE_FRAGMENT', native_sha256=trace['native_sha256'], checks=checks,
                  limits=['UI predicate before the selected button slice is bypassed; member list, alive status, transform position and installed work are explicit fixtures.',
                          'Real GetSkillChainNum, member iteration, full OnExecSkillAbilityChainManaGet and existing GetRate/threshold/latch branches execute; RNG outputs supplied and mana generation intercepted.',
                          'A unique live member with one work has one random threshold test per eligible dispatch while unlatched. There is no fixed double test in this bounded case.',
                          'Failed attempts can retry on later button events; per-attempt 10% is not a whole-Chain cumulative probability. No independence/statistical RNG experiment.',
                          'Internal list count2 is the first eligible value; displayed 1stChain text/rendering and complete roster/source installation are not proven.'])
    (OUT / 'native_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(passed=len(checks), per_eligible_event='one 10% threshold test per unlatched work')))


if __name__ == '__main__':
    main()
