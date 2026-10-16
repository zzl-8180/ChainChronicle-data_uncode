"""Run exact GetOverHealRate and bounded HP cap fragment with explicit models."""
import json,struct,hashlib
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
BASE,HEAP,STACK,STOP=0x50000000,0x10000000,0x20000000,0x30000000
raw=Path('work/protection/il2cpp_loader_seed1.bin').read_bytes();e=json.loads(Path('output/boss_heal/constants.json').read_text(encoding='utf-8'))
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(BASE,(len(raw)+4095)&~4095);u.mem_write(BASE,raw)
for a in (HEAP,STACK,STOP):u.mem_map(a,0x10000)
def q(a,v):u.mem_write(a,struct.pack('<Q',v))
def w(a,v):u.mem_write(a,struct.pack('<I',v&0xffffffff))
def xr(i,v):u.reg_write(UC_ARM64_REG_X0+i,v)
def x(i):return u.reg_read(UC_ARM64_REG_X0+i)
def val(v):return struct.unpack('<f',struct.pack('<I',v))[0]
cell,cls,static=HEAP,HEAP+0x100,HEAP+0x300
q(BASE+0x29bda68,cell);q(cell,cls);w(cls+0xe0,1);q(cls+0xb8,static)
u.mem_write(BASE+0x2bd2c0d,b'\1');q(static+0x38,e['mask']['value'])
for off,key,fmt in ((0x50,'values','f'),(0x58,'bits','i')):
 array=HEAP+0x500+off*8;q(static+off,array);w(array+0x18,6);u.mem_write(array+0x20,struct.pack('<6'+fmt,*e[key]['values']))
ints={};writes=[];slice_mode=False

def ret(value):xr(0,value);u.reg_write(UC_ARM64_REG_PC,u.reg_read(UC_ARM64_REG_LR))
def hook(uc,address,size,data):
 if slice_mode and address==BASE+0x15414cc:uc.emu_stop()
 elif address==BASE+0xa926f0:ret(ints[x(0)])
 elif address==BASE+0xa92640:ints[x(0)]=x(1)&0xffffffff;writes.append(ints[x(0)]);ret(0)
 elif address==BASE+0x143732c:
  # Bounded small positive inputs only; this helper is modeled, not interpreted.
  assert x(0)<100000 and x(1)<100000;ret(x(0)+x(1))
u.hook_add(UC_HOOK_CODE,hook)
def run(start,end):
 u.reg_write(UC_ARM64_REG_SP,STACK+0xf000);u.reg_write(UC_ARM64_REG_LR,STOP)
 u.emu_start(BASE+start,STOP,count=10000)
 assert u.reg_read(UC_ARM64_REG_PC)==end,'Did not reach declared boundary'
checks=[]
for flag,expected in [(0,1),(1<<42,1.6),(1<<43,1.8),((1<<42)|(1<<43),1.8),(1<<35,1.3),(1<<1,1),((1<<40)|(1<<44),2)]:
 xr(0,flag);run(0x1578404,STOP);actual=val(u.reg_read(UC_ARM64_REG_S0));assert abs(actual-expected)<1e-6
 checks.append({'case':'native_flag_rate','flag':flag,'result':actual,'expected':expected,'pass':True})
chara,param,hpmax,hp=HEAP+0x2000,HEAP+0x3000,HEAP+0x4000,HEAP+0x4100
q(chara+0x28,param);q(param+0x58,hpmax);q(param+0x68,hp)
slice_mode=True
for flag,maximum,current,amount,expected in [(1<<42,1000,1500,200,1600),(1<<43,1000,1500,500,1800),(1<<42,1000,1600,100,1600),(1<<42,1000,1800,100,1800),(0,1000,900,200,1000),(1<<42,1001,1500,200,1601)]:
 ints.update({hpmax:maximum,hp:current});writes.clear();xr(0,current);xr(19,chara);xr(20,flag);xr(24,amount);xr(25,current);xr(27,cell)
 run(0x15413bc,BASE+0x15414cc);assert ints[hp]==expected,(flag,maximum,current,amount,ints[hp],expected,writes)
 checks.append({'case':'native_hp_cap_fragment','flag':flag,'hp_max':maximum,'hp_before':current,'heal_argument':amount,'hp_after':ints[hp],'setter_calls':len(writes),'expected':expected,'pass':True})
result={'status':'PASS','evidence':'CONTROLLED_NATIVE_FRAGMENT','native_sha256':hashlib.sha256(raw).hexdigest(),'constants_sha256':hashlib.sha256(Path('output/boss_heal/constants.json').read_bytes()).hexdigest(),'checks':checks,'models':['Static arrays copied from recovered metadata, class marked initialized','ParamS int getter/setter modeled','0x143732c modeled as addition only for small positive test inputs'],'limits':['Heal entry eligibility, reverse/cut, visuals, later CalcHeal not executed','No real device or actual player state','Not a final healing prediction']}
Path('output/boss_heal/checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS',len(checks))
