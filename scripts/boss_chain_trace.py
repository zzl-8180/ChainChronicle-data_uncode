import sys,json
from pathlib import Path
sys.path.insert(0,'scripts')
from metadata_targets import Metadata
from il2cpp_sample_code import Native
from capstone import *
m=Metadata('work/protection/metadata_aei_decoded.bin');n=Native(m);d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
ids=[5177,5179,34548,5351,5174,7084,7083,5188,5398,4540,4542,4544,34609,5396,5359,5360,34626,34627,34618,34619,34620,34621,34622,34623,34549,34550,34611,9114,9115,5350,5416,7077,7078]+n.method_by_rva[0x1299c74]
p=Path('output/boss_chain');p.mkdir(exist_ok=True)
for ix in ids:
 a=n.method(ix); s=int(a['native_rva'],16);e=min(x for x in n.pointers if x>s); ins=list(d.disasm(n.raw[s:e],s)); assert sum(i.size for i in ins)==e-s
 lines=[]
 for i in ins:
  comment=''
  if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):
   comment=' ; '+' | '.join(n.method(j)['declaring_type']+'.'+n.method(j)['name'] for j in n.method_by_rva.get(int(i.op_str[1:],16),[]))
  lines.append(f'{i.address:08x}: {i.mnemonic} {i.op_str}{comment}')
 (p/f'{ix}.txt').write_text('\n'.join(lines),encoding='utf-8')
 print(ix,a['declaring_type'],a['name'],len(ins))





# Persist method identities, fields and branch evidence alongside bounded dumps.
import hashlib
fields={}
for name in ('BattleBossPattern','BattleBossSkill','BattleBossSkill_J','bhSkillUtil','bhSkill','CharaStatus','SupportData','daBattleBossParameter','BattleParam'):
 ti=next(i for i,r in enumerate(m.types) if m.string(r[0])==name)
 fields[name]=n.fields(ti)
dispatch={}
for t in (13,27):
 branch=0x1297d4c+n.unpack('<H',0x206ee04+t*2)[0]*4
 dispatch[str(t)]={'branch':hex(branch),'instructions':[f'{i.address:x}: {i.mnemonic} {i.op_str}' for i in d.disasm(n.raw[branch:branch+36],branch)]}
assert 0x118834c+n.unpack('<H',0x206de48+2)[0]*4==0x1188444
assert 0x1187e00+n.raw[0x206de44+1]*4==0x1187e3c
result={'native_sha256':hashlib.sha256(n.raw).hexdigest(),'metadata_sha256':hashlib.sha256(m.raw).hexdigest(),'methods':[n.method(i) for i in ids],'fields':fields,'dispatch':dispatch,'support_mode1_branch':'0x1188444','support_target1_branch':'0x1187e3c','limits':'Static fragments only; no current player execution proven'}
(p/'trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
