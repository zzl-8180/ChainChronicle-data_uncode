"""Bounded Boss type105/112 evidence, reusing recovered registrations."""
import argparse
import hashlib
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from metadata_targets import Metadata
from il2cpp_sample_code import Native

parser = argparse.ArgumentParser()
parser.add_argument('--effect-type', type=int, choices=(105, 112), default=105)
effect_type = parser.parse_args().effect_type
OUT = Path(f'output/boss_chain/type{effect_type}')
OUT.mkdir(parents=True, exist_ok=True)
m = Metadata('work/protection/metadata_aei_decoded.bin')
n = Native(m)
d = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
ids = [5215, 5409, 5360, 5351, 3855, 4011] if effect_type == 105 else [5466, 7401, 7403, 7404, 7405, 7406, 5846, 5850, 9180, 7641, 7652, 7655,7698,5358,6986]
methods = []
for ix in ids:
    method = n.method(ix)
    start = int(method['native_rva'], 16)
    end = min(p for p in n.pointers if p > start)
    ins = list(d.disasm(n.raw[start:end], start))
    assert sum(i.size for i in ins) == end - start
    lines = []
    for i in ins:
        comment = ''
        if i.mnemonic in ('bl', 'b') and i.op_str.startswith('#0x'):
            comment = ' ; ' + ' | '.join(
                n.method(j)['declaring_type'] + '.' + n.method(j)['name']
                for j in n.method_by_rva.get(int(i.op_str[1:], 16), []))
        lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{comment}')
    (OUT / f'{ix}.txt').write_text('\n'.join(lines), encoding='utf-8')
    methods.append(method)
    print(ix, method['name'], len(ins))

branch = 0x1297d4c + n.unpack('<H', 0x206ee04 + effect_type * 2)[0] * 4
assert branch == {105: 0x1298b74, 112: 0x1297d74}[effect_type]
fields = {}
for name in (('bhSkillUtil', 'CharaBehavior', 'BattleParam', 'CharaStatus')
             if effect_type == 105 else ('bhSkillUtil', 'CoveringFirePoint', 'BulletDelay','GroundManager')):
    ti = next(i for i, r in enumerate(m.types) if m.string(r[0]) == name)
    selected = n.fields(ti)
    if name not in ('bhSkillUtil', 'CoveringFirePoint', 'BulletDelay','GroundManager'):
        selected = [f for f in selected if any(s in f['name'].lower()
                    for s in ('atk', 'attack', 'chain', 'status', 'param', 'support'))]
    fields[name] = selected
result = dict(native_sha256=hashlib.sha256(n.raw).hexdigest(),
              metadata_sha256=hashlib.sha256(m.raw).hexdigest(), methods=methods,
              fields=fields, **{f'dispatch_type{effect_type}':hex(branch)},
              dispatch_instructions=[f'{i.address:x}: {i.mnemonic} {i.op_str}'
                  for i in d.disasm(n.raw[branch:branch + (20 if effect_type == 105 else 36)], branch)],
              scope='APK 5.6.2/56021 local code; current player execution unknown')
result['conversion_fragment'] = [f'{i.address:x}: {i.mnemonic} {i.op_str}'
    for i in d.disasm(n.raw[0x14374bc:0x1437554], 0x14374bc)]
if effect_type==112:
    result['ground_initializer']={'native_rva':'0x2073760','raw_hex':n.raw[0x2073760:0x2073770].hex(),'values':list(n.unpack('<4i',0x2073760)),'fields':['GroundManager._groundWidth','_groundDepth','_playerAreaWidth','_playerAreaDepth'],'limits':'cctor initial values; runtime battlefield changes not audited'}
    result['attack_flag_bits']=[dict(f,default=n.default(f['index'])) for f in n.fields(723) if f['name'] in ('DOWN','ISAIRSTRIKE','ISBULLET','IGNORENOTPUSH')]
    state_type=n.type_info(18281)['data']
    result['damage_reaction_state']=[dict(f,default=n.default(f['index'])) for f in n.fields(state_type) if f['name']=='DamageL']
(OUT / 'trace.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
