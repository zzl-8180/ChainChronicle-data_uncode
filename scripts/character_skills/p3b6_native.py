"""Bounded native evidence for the frozen P3B6 type5 sentence family."""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
import common as C
from il2cpp_sample_code import Native
from metadata_targets import Metadata
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
import unicorn.arm64_const as U
from skilllist_types import enum_values
OUT=C.ROOT/'output/character_skills/description_bindings/p3b6_batch'

def evidence(n,md):
 dis=Cs(CS_ARCH_ARM64,CS_MODE_ARM);checks=[]
 def ck(name,passed,**kw):checks.append(dict(name=name,passed=bool(passed),**kw))
 def op(a):
  i=next(dis.disasm(n.raw[a:a+4],a));return i.mnemonic+' '+i.op_str
 pins={0x1299780:'b #0x1186e38',0x1186e9c:'ldr s8, [x21, #0x30]',
  0x1186ea0:'ldr s9, [x21, #0x38]',0x1186eb4:'ldr s2, [x21, #0x3c]',
  0x1186ecc:'mov w3, wzr',0x1186ed0:'bl #0x1186ef4',0x1186f50:'mov w1, #1',
  0x1186f5c:'bl #0x1182ed8',0x1186f60:'fmul s0, s0, s10',0x1186f68:'bl #0x14374bc',
  0x1186f94:'bl #0x11826c0',0x1187034:'orr x5, x24, x23',0x1187044:'mov w6, #1',
  0x1187068:'bl #0x131046c',0x131052c:'str w21, [sp]',0x1310530:'bl #0x131055c',
  0x13107fc:'str w8, [x20, #0x18]',0x13107f8:'stp s9, s11, [x20, #0x38]',
  0x1310808:'str w8, [x20, #0x40]',0x131080c:'str s10, [x20, #0x44]',
  0x1310830:'str x9, [x20, #0x58]',0x1310838:'str w21, [x20, #0x78]',
  0x13108c4:'orr x8, x21, #0x200000000000',0x13113fc:'b #0x1311404',
  0x13113d4:'fmul s3, s0, s1',0x13113d8:'fmul s1, s0, s2',
  0x1311ce4:'cset w21, eq',0x1311d38:'mov w1, w21',0x1311d40:'bl #0x10b62a0',
  0x1311dbc:'cbz w8, #0x1311ff0',0x1311dcc:'b.lo #0x1311ff0',
  0x1311e10:'bl #0x1569bc0',0x1311e38:'tbnz w0, #0, #0x1311ff0',
  0x1311e4c:'b.ne #0x1311ff0',0x1311f14:'b.hi #0x1311ff0',
  0x1311f24:'b.hi #0x1311ff0',0x1311568:'tbnz w26, #0, #0x13116f8',
  0x1311790:'bl #0x153b120',0x13117ac:'bl #0x1309248',0x13117ec:'b.ne #0x131171c',
  0x11827b0:'tbz w0, #0, #0x11827c8',0x11827bc:'bl #0x111b8cc',
  0x11827c0:'mov x19, x0',0x1182b04:'bl #0x111b554',0x1182b08:'orr x19, x0, x19'}
 ck('native_dataflow_pins',all(op(a)==s for a,s in pins.items()),pins=[dict(rva=hex(a),expected=s,actual=op(a))for a,s in pins.items()])
 ts={md.string(t[0]):i for i,t in enumerate(md.types)}
 fields={t:{f['name']:f['offset']for f in n.fields(ts[t])}for t in ['bhSkillUtil','Bullet','CharaBehavior','BattleManager']}
 expected={'bhSkillUtil':{'_type':'0x14','_skillparam1':'0x30','_skillparam3':'0x38','_skillparam4':'0x3c'},
  'Bullet':{'_myType':'0x18','_velocity':'0x38','_radius':'0x40','_radius_h':'0x44','_attackFlag':'0x58','_hitList':'0x68','_dmgType':'0x78'},
  'BattleManager':{'_aChara_Player':'0x70','_aChara_Enemy':'0x78'},'CharaBehavior':{'_type':'0x18','_state':'0x1c','_isActive':'0x118','_isVisible':'0x119'}}
 ck('metadata_fields',all(fields[t][k]==v for t,ff in expected.items()for k,v in ff.items()),fields=expected)
 flags=enum_values(n,md,'ATTACK_FLAG');damage=enum_values(n,md,'eDamageType')
 ck('control_bits_and_damage_type',flags['MULTIHIT']==0 and flags['ISMAGIC']==10 and flags['ISBULLET']==45 and damage['Skill']==1,attack_flag_bits=flags,damage_types=damage)
 def machine():
  u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
  for a,size in [(0x1186000,0x2000),(0x1310000,0x5000),(0x10b6000,0x1000),(0x2015000,0x1000)]:
   u.mem_map(a,size);u.mem_write(a,n.raw[a:a+size])
  u.mem_map(0x40000000,0x20000);u.reg_write(U.UC_ARM64_REG_SP,0x4001e000)
  return u
 def sf(u,r,v):u.reg_write(getattr(U,'UC_ARM64_REG_Q'+str(r)),int.from_bytes(struct.pack('<f',v),'little'))
 def gf(u,r):return struct.unpack('<f',(u.reg_read(getattr(U,'UC_ARM64_REG_Q'+str(r)))&0xffffffff).to_bytes(4,'little'))[0]
 def w(u,a,v):u.mem_write(a,struct.pack('<I',v))
 def q(u,a,v):u.mem_write(a,struct.pack('<Q',v))
 side=[]
 for typ in [0,1,2]:
  u=machine();u.reg_write(U.UC_ARM64_REG_X19,0x40001000);u.reg_write(U.UC_ARM64_REG_X0,0x40002000);w(u,0x40001018,typ)
  u.emu_start(0x1311cd8,0x1311ce8,count=10);opponent=u.reg_read(U.UC_ARM64_REG_W21)
  u.reg_write(U.UC_ARM64_REG_X0,0x40003000);u.reg_write(U.UC_ARM64_REG_W1,opponent)
  q(u,0x40003068,0x40004000);q(u,0x40003070,0x40005000);q(u,0x40003078,0x40006000)
  u.emu_start(0x10b62a0,0x10b62c0,count=12)
  side.append(dict(caster_type=typ,opponent_type=opponent,list_pointer=hex(u.reg_read(U.UC_ARM64_REG_X0))))
 ck('player_enemy_opponent_lists',[(v['opponent_type'],v['list_pointer'])for v in side]==[(1,'0x40006000'),(0,'0x40005000'),(0,'0x40005000')],samples=side)
 radius=[]
 for value in [0,1.5,2.5]:
  u=machine();sf(u,9,value);u.emu_start(0x1186fac,0x1186fe0,count=20);radius.append(dict(raw_sp4=value,radius_h=gf(u,9)))
 ck('real_sp4_zero_is_point_one_radius',abs(radius[0]['radius_h']-.1)<1e-7 and abs(radius[1]['radius_h']-.1)<1e-7 and abs(radius[2]['radius_h']-.6)<1e-7,samples=radius)
 geometry=[]
 for dx,dz in [(0,0),(.29,0),(.31,0),(-.29,0),(-.31,0),(0,.29),(0,.31),(0,-.31),(.29,.29)]:
  u=machine();bullet=0x40001000;target=0x40002000;sp=0x4001e000
  u.reg_write(U.UC_ARM64_REG_X19,bullet);u.reg_write(U.UC_ARM64_REG_X23,target);q(u,target+0x28,0x40003000);q(u,target+0x160,0x40004000)
  u.mem_write(sp+8,struct.pack('<ff',.1,.1));u.mem_write(bullet+0x38,struct.pack('<f',1));sf(u,11,0);sf(u,10,0)
  reached=[]
  def gh(uu,a,s,d):
   if a in [0x1311e5c,0x1311e70]:sf(uu,0,.2 if a==0x1311e5c else 1);uu.reg_write(U.UC_ARM64_REG_PC,a+4)
   elif a in [0x1311e88,0x1311e98]:
    sf(uu,0,dx);sf(uu,1,0);sf(uu,2,dz);uu.reg_write(U.UC_ARM64_REG_PC,a+4)
   elif a==0x1311ef4:uu.reg_write(U.UC_ARM64_REG_W0,0);uu.reg_write(U.UC_ARM64_REG_PC,a+4)
   elif a in [0x1311f34,0x1311ff0]:reached.append(a);uu.emu_stop()
  u.hook_add(UC_HOOK_CODE,gh);u.emu_start(0x1311e50,0x1311ff4,count=140)
  geometry.append(dict(dx=dx,dz=dz,accepted=reached==[0x1311f34],expected=abs(dx)<=.3 and abs(dz)<=.3))
 ck('rectangular_collision_inside_outside',all(s['accepted']==s['expected']for s in geometry),samples=geometry,fixture='bodyRadius=.2,statusRadius=1,radius=.1,radius_h=.1,jump=false')
 gates=[]
 for active,state in [(0,0),(1,0),(1,11),(1,12),(1,13)]:
  u=machine();u.reg_write(U.UC_ARM64_REG_X23,0x40002000);u.mem_write(0x40002118,bytes([active]));w(u,0x4000201c,state);hit=[]
  def gate(uu,a,s,d):
   if a in [0x1311dd0,0x1311ff0]:hit.append(a);uu.emu_stop()
  u.hook_add(UC_HOOK_CODE,gate);u.emu_start(0x1311db8,0x1311ff4,count=12)
  gates.append(dict(active=active,state=state,accepted=hit==[0x1311dd0]))
 ck('active_and_state_exclusions',all(v['accepted']==bool(v['active']and v['state']not in [11,12])for v in gates),samples=gates)
 duplicate=[]
 for seen in [0,1]:
  u=machine();u.reg_write(U.UC_ARM64_REG_X20,0x40005000);u.reg_write(U.UC_ARM64_REG_X29,0x40006000)
  q(u,0x40006000,0x40006100);q(u,0x40006138,0x40006200);q(u,0x40006208,0x40006300);q(u,0x40006308,0x40006400);hit=[]
  def dup(uu,a,s,d):
   if a==0x1311e34:uu.reg_write(U.UC_ARM64_REG_W0,seen);uu.reg_write(U.UC_ARM64_REG_PC,a+4)
   elif a in [0x1311e3c,0x1311ff0]:hit.append(a);uu.emu_stop()
  u.hook_add(UC_HOOK_CODE,dup);u.emu_start(0x1311e18,0x1311ff4,count=15)
  duplicate.append(dict(already_hit=seen,accepted=hit==[0x1311e3c]))
 ck('already_hit_target_rejected',duplicate==[dict(already_hit=0,accepted=True),dict(already_hit=1,accepted=False)],samples=duplicate)
 routes=[]
 for flag in [1024,1025]:
  u=machine();u.reg_write(U.UC_ARM64_REG_W26,flag);hit=[]
  def route(uu,a,s,d):
   if a in [0x131156c,0x13116f8]:hit.append(a);uu.emu_stop()
  u.hook_add(UC_HOOK_CODE,route);u.emu_start(0x1311568,0x1311700,count=4)
  routes.append(dict(raw_flag=flag,multihit=hit==[0x13116f8]))
 ck('multihit_control_bit_distinguishes_single_target',routes==[dict(raw_flag=1024,multihit=False),dict(raw_flag=1025,multihit=True)],samples=routes)
 # The real loop traverses two fixture target tuples, preserving one attack per
 # accepted target; system calls are stubbed, no game objects or HP simulated.
 u=machine();bullet=0x40001000;items=0x40002000;caster=0x40003000;klass=0x40004000
 u.reg_write(U.UC_ARM64_REG_X19,bullet);u.reg_write(U.UC_ARM64_REG_X20,caster);u.reg_write(U.UC_ARM64_REG_X21,items)
 u.reg_write(U.UC_ARM64_REG_X24,0x40005000);q(u,0x40005000,klass);w(u,klass+0xe0,1)
 u.reg_write(U.UC_ARM64_REG_X28,2);u.reg_write(U.UC_ARM64_REG_W29,1)
 q(u,items,0x40006000);q(u,items+0x10,0x40007000);q(u,bullet+0x48,0x40008000);q(u,bullet,klass)
 q(u,klass+0x188,0x40009000);q(u,klass+0x190,0);w(u,bullet+0x78,1);q(u,bullet+0x58,1025);u.mem_write(bullet+0x50,struct.pack('<f',1))
 attacks=[];hits=[]
 def loop(uu,a,s,d):
  if a==0x131173c:uu.reg_write(U.UC_ARM64_REG_W0,0);uu.reg_write(U.UC_ARM64_REG_PC,a+4)
  elif a==0x1311750:uu.reg_write(U.UC_ARM64_REG_W0,400);uu.reg_write(U.UC_ARM64_REG_PC,a+4)
  elif a==0x1311790:
   attacks.append(dict(caster=hex(uu.reg_read(U.UC_ARM64_REG_X0)),target=hex(uu.reg_read(U.UC_ARM64_REG_X2)),damage_type=uu.reg_read(U.UC_ARM64_REG_W1),damage=uu.reg_read(U.UC_ARM64_REG_W3)))
   uu.reg_write(U.UC_ARM64_REG_PC,a+4)
  elif a==0x13117a0:uu.reg_write(U.UC_ARM64_REG_PC,a+4)
  elif a==0x13117ac:hits.append(hex(uu.reg_read(U.UC_ARM64_REG_X1)));uu.reg_write(U.UC_ARM64_REG_PC,a+4)
  elif a==0x13117c4:uu.reg_write(U.UC_ARM64_REG_W0,400);uu.reg_write(U.UC_ARM64_REG_PC,a+4)
  elif a==0x13117d8:uu.reg_write(U.UC_ARM64_REG_PC,a+4)
  elif a==0x13119ec:uu.emu_stop()
 u.hook_add(UC_HOOK_CODE,loop);u.emu_start(0x131171c,0x13119f0,count=180)
 ck('multihit_two_targets_actual_loop',len(attacks)==2 and hits==['0x40006000','0x40007000']and all(a['damage_type']==1 and a['damage']==400 and a['caster']==hex(caster)for a in attacks),attacks=attacks,hit_list_updates=hits)
 ranges=[(0x1299764,0x1299788),(0x1186e38,0x1187110),(0x131046c,0x131055c),
  (0x13107ec,0x13108d0),(0x13113bc,0x1311404),(0x1311cd4,0x1311d50),
  (0x1311db8,0x1311f34),(0x1311560,0x1311630),(0x13116f8,0x13117f8),
  (0x10b62a0,0x10b62c4),(0x1182798,0x11827cc),(0x1182afc,0x1182b24)]
 return dict(generated_by='scripts/character_skills/p3b6_native.py',native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(md.raw).hexdigest(),checks=checks,passed=sum(x['passed']for x in checks),total=len(checks),slices=[dict(start=hex(a),end=hex(b),sha256=hashlib.sha256(n.raw[a:b]).hexdigest(),instructions=[dict(rva=hex(i.address),op=i.mnemonic+' '+i.op_str)for i in dis.disasm(n.raw[a:b],a)])for a,b in ranges],limits='有界原生片段；系统/对象调用为显式夹具stub。仅固有基础技能发射和命中请求；运行时能力可覆盖/追加攻击flag，武器flag另OR；不承诺命中所有敌人、实机或最终扣血。伤害公式复用既有boss_attack_types证据，不新增字段规则。')

def main():
 C.enable_utf8_console();md=Metadata(C.ROOT/'work/protection/metadata_aei_decoded.bin');n=Native(md)
 ev=evidence(n,md);C.write_json(OUT/'type5_native_evidence.json',ev)
 print(json.dumps(dict(passed=ev['passed'],total=ev['total'],failed=[c['name']for c in ev['checks']if not c['passed']]),ensure_ascii=False))
 if ev['passed']!=ev['total']:raise SystemExit(1)
if __name__=='__main__':main()
