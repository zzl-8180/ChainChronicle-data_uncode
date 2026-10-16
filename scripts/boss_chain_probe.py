"""Bounded native regeneration and support-argument experiments; no game runtime."""
import json,struct,hashlib
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
BASE,HEAP,STACK,STOP=0x50000000,0x10000000,0x20000000,0x30000000
raw=Path('work/protection/il2cpp_loader_seed1.bin').read_bytes()
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def val(x):return struct.unpack('<f',struct.pack('<I',x))[0]
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(BASE,(len(raw)+4095)&~4095);u.mem_write(BASE,raw)
for a in (HEAP,STACK,STOP):u.mem_map(a,0x10000)
def w(a,x):u.mem_write(a,struct.pack('<I',x))
def q(a,x):u.mem_write(a,struct.pack('<Q',x))
def r(a):return struct.unpack('<I',u.mem_read(a,4))[0]
def f(i,x):u.reg_write(UC_ARM64_REG_S0+i,bits(x))
def x(i,v):u.reg_write(UC_ARM64_REG_X0+i,v)
calls=[];support=[]
def hook(uc,addr,size,data):
 if addr==BASE+0x1541158:
  calls.append({'amount':uc.reg_read(UC_ARM64_REG_X1),'flags':uc.reg_read(UC_ARM64_REG_X2)})
  uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_LR))
 elif addr==BASE+0x17765e0:
  support.append([val(uc.reg_read(UC_ARM64_REG_S0+i)) for i in range(7)]);uc.emu_stop()
u.hook_add(UC_HOOK_CODE,hook)
def run(a):
 u.reg_write(UC_ARM64_REG_SP,STACK+0xf000);u.reg_write(UC_ARM64_REG_LR,STOP)
 u.emu_start(BASE+a,STOP,count=2000)
 if u.reg_read(UC_ARM64_REG_PC)!=STOP and a!=0x1188444:raise ValueError('instruction bound or unexpected return')
def setup(count=15,interval=2,amount=150):
 u.mem_write(HEAP,bytes(0x1000));q(HEAP+0xc0,HEAP+0x800)
 x(0,HEAP);x(1,count);x(2,amount);x(3,0);f(0,interval);f(1,0);run(0x17706c4)
def update(dt):x(0,HEAP);f(0,dt);run(0x176f73c)
checks=[]
setup();update(0);assert len(calls)==1 and r(HEAP+0x1d8)==14
checks.append({'name':'initial_timer_zero_first_update_heals','pass':True})
update(1);assert len(calls)==1;update(1);assert len(calls)==2
checks.append({'name':'interval_boundary_two_delta_units','pass':True})
for _ in range(13):update(2)
update(2);assert len(calls)==15 and r(HEAP+0x1d8)==0
checks.append({'name':'fifteen_calls_then_stop','pass':True,'calls':len(calls)})
setup(0);before=len(calls);update(2);assert len(calls)==before
checks.append({'name':'zero_count_no_heal','pass':True})
setup();update(100);assert r(HEAP+0x1d8)==14
checks.append({'name':'large_delta_one_call_no_catchup','pass':True})
setup(3,4,900);assert r(HEAP+0x1d8)==3 and r(HEAP+0x1dc)==900 and r(HEAP+0x1d0)==0
checks.append({'name':'setter_overwrites_prior_regeneration','pass':True})
for p1,p2,p6,chain in ((.6,.3,.3,1),(.7,.35,.35,1.2)):
 util=HEAP+0x2000; recipient=HEAP+0x3000
 q(recipient+0xa0,HEAP);u.reg_write(UC_ARM64_REG_X25,recipient);u.reg_write(UC_ARM64_REG_X22,util);u.reg_write(UC_ARM64_REG_X23,0)
 for off,v in ((0x18,chain),(0x30,p1),(0x34,p2),(0x38,30),(0x3c,0),(0x40,0),(0x44,p6)):w(util+off,bits(v))
 run(0x1188444);expected=[p1*chain,p2*chain,p6*chain,0,0,0,30]
 assert all(abs(a-b)<1e-6 for a,b in zip(support[-1],expected))
 checks.append({'name':f'support_argument_block_chain_{chain}','pass':True,'s0_to_s6':support[-1], 'missing_fields':'param4/5 explicitly zero scenario inputs; not source defaults'})
result={'evidence_kind':'CONTROLLED_NATIVE_FRAGMENT','native_sha256':hashlib.sha256(raw).hexdigest(),'checks':checks,'limits':['Heal is intercepted; no actual HP or flag behavior tested','Support starts at mode1 branch, stops at SetSupport call; engine selection and full execution are not emulated','Delta units are supplied inputs; no wall-clock seconds claim','No actual player state or final multiplier']}
Path('output/boss_chain/native_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(checks)}))
