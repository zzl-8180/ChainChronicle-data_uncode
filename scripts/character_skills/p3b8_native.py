"""Bounded P3B8 current-byte branch/consumer execution; explicit runtime stubs."""
import hashlib,json,math,struct,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent.parent)]
import common as C
from il2cpp_sample_code import Native
from metadata_targets import Metadata
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
import unicorn.arm64_const as A
OUT=C.ROOT/'output/character_skills/description_bindings/p3b8_boss'

def evidence(n,md):
 checks=[];d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 def ck(name,ok,**kw):checks.append(dict(name=name,passed=bool(ok),**kw))
 def op(a):
  i=next(d.disasm(n.raw[a:a+4],a));return i.mnemonic+' '+i.op_str
 def reg(u,r,v):u.reg_write(getattr(A,'UC_ARM64_REG_'+r),v)
 def get(u,r):return u.reg_read(getattr(A,'UC_ARM64_REG_'+r))
 def q(u,a,v):u.mem_write(a,struct.pack('<Q',v))
 def w(u,a,v):u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def f(u,a,v):u.mem_write(a,struct.pack('<f',v))
 def rq(u,a):return struct.unpack('<Q',u.mem_read(a,8))[0]
 def rw(u,a):return struct.unpack('<I',u.mem_read(a,4))[0]
 def sf(u,r,v):reg(u,'Q'+str(r),int.from_bytes(struct.pack('<f',v),'little'))
 def gf(u,r):return struct.unpack('<f',(get(u,'Q'+str(r))&0xffffffff).to_bytes(4,'little'))[0]
 def machine():
  u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,(len(n.raw)+4095)&~4095);u.mem_write(0,n.raw)
  u.mem_map(0x40000000,0x80000);reg(u,'SP',0x4007e000);reg(u,'LR',0x4007f000);return u
 nativehash=hashlib.sha256(n.raw).hexdigest();metahash=hashlib.sha256(md.raw).hexdigest()
 reused=[C.ROOT/p for p in ['output/character_skills/description_bindings/p3b6_batch/type5_native_evidence.json','output/character_skills/review/p3b6_20261019_batch_bindings/native_audit.json','output/character_skills/boss_heal_types/type_rules.json','output/character_skills/boss_heal_types/native_checks.json','output/character_skills/cp_paths/path_evidence.json']]
 b6=C.load_json(reused[0]);ck('same_native_and_metadata_as_reused_b6',nativehash==b6['native_sha256']and metahash==b6['metadata_sha256'])
 ti={md.string(t[0]):i for i,t in enumerate(md.types)}
 expected={'bhSkillUtil':{'_type':'0x14','_skillparam1':'0x30','_skillparam2':'0x34','_iparam0':'0x70','_attacker':'0xb8'},'BattleManager':{'_aChara_Player':'0x70','_aChara_Enemy':'0x78'},'CharaBehavior':{'_isActive':'0x118','_isVisible':'0x119','_heroWork':'0x3e8','_isEnableAppearAnim':'0x470'},'Bullet':{'_attackFlag':'0x58','_dmgType':'0x78'}}
 actual={t:{z['name']:z['offset']for z in n.fields(ti[t])}for t in expected}
 ck('metadata_fields',all(actual[t].get(k)==v for t,ff in expected.items()for k,v in ff.items()),expected=expected)
 pins={0x1311568:'tbnz w26, #0, #0x13116f8',0x1187e40:'ldr w1, [x23, #0x14]',0x1187e44:'mov w2, #1',0x1187e48:'mov w4, #1',0x1187e50:'mov w3, wzr',0x1187e54:'mov w5, wzr',0x1187e5c:'bl #0x10b6440',0x1187e64:'ldr w1, [x23, #0x70]',0x1187e70:'bl #0x13ab324',0x10b64e8:'b #0x10bd0d8',0x13ab384:'cbz w19, #0x13ab43c',0x1188354:'bl #0x1182ed8',0x1188358:'ldr s1, [x22, #0x30]',0x1188360:'fmul s0, s0, s1',0x1188364:'bl #0x14374bc',0x1188390:'bl #0x1541158'}
 ck('current_dispatch_and_consumer_pins',all(op(a)==s for a,s in pins.items()),pins=[dict(rva=hex(a),expected=s,actual=op(a))for a,s in pins.items()])
 u=machine();reg(u,'W21',1);reg(u,'X19',0x40000100);u.emu_start(0x12987c0,0x12988c4,count=12)
 ck('type11_real_dispatch_mode1_act0',[(r,get(u,r))for r in ['W1','W2','W3','W4']]==[('W1',1),('W2',1),('W3',0),('W4',11)])
 # Actual single/multi branches consume 0 or 3 prequalified collision tuples.
 # Collision qualification/geometry/once-fire evidence is reused from B6/D.
 shoot=[]
 for flag in [0,1024,1,1025]:
  for count in [0,3]:
   u=machine();bullet=0x40001000;items=0x40002000;caster=0x40003000;klass=0x40004000
   for r,v in [('X19',bullet),('X20',caster),('X21',items),('X22',count),('X24',0x40005000),('X23',0x40005000),('X25',0x40005000),('W26',flag)]:reg(u,r,v)
   q(u,0x40005000,klass);w(u,klass+0xe0,1);q(u,bullet+0x48,0x40008000);q(u,bullet,klass);q(u,klass+0x188,0x40009000);q(u,klass+0x190,0);q(u,bullet+0x58,flag);w(u,bullet+0x78,1);f(u,bullet+0x50,1)
   targets=[0x40006000+i*0x100 for i in range(count)]
   for i,t in enumerate(targets):q(u,items+16*i,t)
   attacks=[];route=[]
   def hook(uu,a,s,data):
    if a in [0x131156c,0x13116f8]:route.append(a)
    if a in [0x131165c,0x13119ec]:uu.emu_stop()
    elif a in [0x1311598,0x131173c]:reg(uu,'W0',int(a==0x1311598));reg(uu,'PC',a+4)
    elif a in [0x13115b0,0x1311750,0x13117c4]:reg(uu,'W0',123);reg(uu,'PC',a+4)
    elif a in [0x13115f0,0x1311790]:attacks.append(dict(caster=get(uu,'X0'),target=get(uu,'X2'),dmgtype=get(uu,'W1'),damage=get(uu,'W3')));reg(uu,'PC',a+4)
    elif a in [0x1311600,0x13117a0,0x13117ac,0x13117d8]:reg(uu,'PC',a+4)
   u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x1311568,0x13119f0,count=600)
   expected_count=count if flag&1 else min(count,1)
   shoot.append(dict(flag=flag,targets=count,route=[hex(x)for x in route],attacks=attacks,expected=expected_count,passed=len(attacks)==expected_count and [x['target']for x in attacks]==targets[:expected_count]and all(x['dmgtype']==1 and x['damage']==123 for x in attacks)))
 ck('four_flags_single_multihit_zero_three_targets',all(x['passed']for x in shoot),samples=shoot)

 def heal_fixture(side,candidates,jobflag=0,coefficient=4.5,base=37.75,already=0,request=1,motion=0):
  u=machine();util=0x40000100;manager=0x40001000;heap=[0x40050000];alloc=[];heals=[];basic=[];members=[];jobs=[]
  def initlist(ptr,items):
   backing=ptr+0x200;q(u,ptr+0x10,backing);w(u,ptr+0x18,len(items));w(u,backing+0x18,64)
   for i,t in enumerate(items):q(u,backing+0x20+8*i,t)
  def values(ptr):return [rq(u,rq(u,ptr+0x10)+0x20+8*i)for i in range(rw(u,ptr+0x18))]
  for globaladdr,slot,klass in [(0x29f0b88,0x40030000,0x40031000),(0x29a8520,0x40033000,0x40034000),(0x29ffd80,0x40035000,0x40036000),(0x29be1b8,0x40037000,0x40038000),(0x29d5fa0,0x40039000,0x4003a000),(0x29b2c30,0x4003b000,0x4003c000),(0x29f5b48,0x4003d000,0x4003e000),(0x29bab78,0x4003f000,0x40040000)]:
   q(u,globaladdr,slot);q(u,slot,klass);w(u,klass+0xe0,1)
  q(u,0x400310b8,0x40032000);q(u,0x40032010,manager)
  for addr in [0x2bd04ff,0x2bcfe23,0x2bcfe24,0x2bd17c9,0x2bd0501,0x2bd24ed]:u.mem_write(addr,b'\x01')
  own=[];opponent=[]
  for i,c in enumerate(candidates):
   ptr=0x40008000+0x1000*i;bp=ptr+0x600;own.append(ptr);q(u,ptr+0x28,bp);q(u,bp+0x68,bp+0x100);w(u,bp+0x100,c.get('hp',100));w(u,ptr+0x1c,c.get('state',0))
   q(u,bp+0xf8,bp+0x108);w(u,bp+0x108,c.get('job',i%6));u.mem_write(ptr+0x118,bytes([c.get('active',1)]));u.mem_write(ptr+0x119,bytes([c.get('visible',1)]));u.mem_write(ptr+0x470,bytes([c.get('appearance',0)]));u.mem_write(ptr+0x3e8,bytes([c.get('hero',0)]))
  opposite=0x40020000;opbp=opposite+0x600;q(u,opposite+0x28,opbp);q(u,opbp+0x68,opbp+0x100);w(u,opbp+0x100,100);q(u,opbp+0xf8,opbp+0x108);w(u,opbp+0x108,5);u.mem_write(opposite+0x118,b'\x01');opponent.append(opposite)
  initlist(0x40002000,own if side==0 else opponent);initlist(0x40003000,own if side==1 else opponent);q(u,manager+0x70,0x40002000);q(u,manager+0x78,0x40003000)
  w(u,util+0x14,side);w(u,util+0x70,jobflag);f(u,util+0x30,coefficient);f(u,util+0x34,0);q(u,util+0x60,0x40042000);q(u,util+0xb8,0x40043000)
  flags=0x40044000;u.mem_write(flags,bytes([already,request]));args=(util,motion,flags,flags+1,1,0,11)
  for i,v in enumerate(args):reg(u,'X'+str(i),v)
  def ret(uu,value=None):
   if value is not None:reg(uu,'X0',value)
   reg(uu,'PC',get(uu,'LR'))
  def hook(uu,a,size,data):
   if a==0x4007f000:uu.emu_stop()
   elif a==0x88d910:
    ptr=heap[0];heap[0]+=0x1000;initlist(ptr,[]);alloc.append(ptr);ret(uu,ptr)
   elif a in [0xa83f78,0xa83fe4]:ret(uu)
   elif a==0xa84484:ret(uu,values(get(uu,'X0'))[get(uu,'W1')])
   elif a==0xa85b64:
    ptr=get(uu,'X0');vv=values(ptr);vv.remove(get(uu,'X1'));initlist(ptr,vv);ret(uu,1)
   elif a in [0x1eb8358,0x1ec91b8]:ret(uu,int((get(uu,'X0')==0)if a==0x1eb8358 else(get(uu,'X0')!=0)))
   elif a in [0xa926f0,0xa92534]:ret(uu,rw(uu,get(uu,'X0')))
   elif a==0xa928d8:ret(uu,rq(uu,get(uu,'X0')))
   elif a==0x1182b4c:f(uu,get(uu,'X2'),0);ret(uu,get(uu,'X1'))
   elif a==0x1182ed8:basic.append(get(uu,'W1'));sf(uu,0,base);ret(uu)
   elif a==0x1541158:
    heals.append(dict(target=get(uu,'X0'),heal_value=get(uu,'W1'),attacker=get(uu,'X4'),over_ratio=gf(uu,0)));ret(uu)
   elif a==0x1187e60:members[:]=values(get(uu,'X0'))
   elif a==0x1187e74:jobs[:]=values(rq(uu,get(uu,'SP')+0x28))
  u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x1187c80,0x4007f004,count=18000)
  return dict(side=side,fixture=candidates,jobflag=jobflag,coefficient=coefficient,B=base,already=already,request=request,motion=motion,own_targets=own,opposite_targets=opponent,member_result=members,job_result=jobs,heals=heals,basic_true_args=basic,after_flags=list(u.mem_read(flags,2)))
 cases=[dict(active=0),dict(active=1,appearance=0,hero=0),dict(active=1,appearance=1,hero=0),dict(active=1,appearance=1,hero=1),dict(active=1,hp=0),dict(active=1,state=12),dict(active=1,visible=0),dict(active=1,job=5)]
 side_samples=[heal_fixture(side,cases)for side in [0,1]]
 accepted=[1,3,6,7]
 ck('type11_real_same_side_active_appearance_hero_alive',all(s['member_result']==[s['own_targets'][i]for i in accepted]and s['job_result']==s['member_result']and [h['target']for h in s['heals']]==s['member_result']and not set(s['opposite_targets'])&set(s['member_result'])for s in side_samples),samples=side_samples,alive='Real IsAlive executes HP>=1 and state!=12; only protected HP getter is stubbed')
 jobs=[heal_fixture(0,[dict(job=j)for j in range(6)],flag)for flag in [0,1,1<<3,(1<<0)|(1<<5)]]
 ck('type11_zero_jobflag_keeps_all_jobs_nonzero_filters',all(s['job_result']==[p for j,p in enumerate(s['own_targets'])if s['jobflag']==0 or s['jobflag']&(1<<j)]and[h['target']for h in s['heals']]==s['job_result']for s in jobs),samples=jobs)
 gates=[heal_fixture(0,[dict(job=0),dict(job=5)],already=a,request=r,motion=m)for a,r,m in [(0,0,0),(0,1,0),(0,0,1),(0,1,1),(1,1,1)]]
 ck('type11_once_request_motion_gate',all(len(s['heals'])==(2 if not s['already']and(s['request']or s['motion'])else 0)and(s['after_flags']==[1,0]if s['heals']else True)for s in gates),samples=gates)
 formula=[heal_fixture(0,[dict(job=0),dict(job=2)],coefficient=c,base=b)for b,c in [(37.75,4.5),(123.125,3.5),(-.25,6.5)]]
 for s in formula:s['expected_heal_input']=math.floor(struct.unpack('<f',struct.pack('<f',s['B']*s['coefficient']))[0])&0xffffffff
 ck('type11_common_real_sp1_float32_integerisation_each_target',all(len(s['heals'])==2 and all(h['heal_value']==s['expected_heal_input']for h in s['heals'])and s['basic_true_args']==[1,1]for s in formula),samples=formula)
 ranges=[(0x12987c0,0x12987d8),(0x1299c74,0x1299ce0),(0x1187c80,0x1188194),(0x10b6440,0x10b64f0),(0x10bd0d8,0x10bd310),(0x13ab324,0x13ab454),(0x1535abc,0x1535afc),(0x1188224,0x118839c),(0x1188624,0x1188638),(0x14374bc,0x1437554),(0x1311568,0x131165c),(0x13116f8,0x13117f8)]
 return dict(status='C_BOUNDED_NATIVE_SELF_CHECK_NOT_D',generated_by='scripts/character_skills/p3b8_native.py',native_sha256=nativehash,metadata_sha256=metahash,checks=checks,passed=sum(c['passed']for c in checks),total=len(checks),reused_evidence=[dict(path=str(p.relative_to(C.ROOT)).replace('\\','/'),sha256=C.sha256_file(p))for p in reused],slices=[dict(start=hex(a),end=hex(b),sha256=hashlib.sha256(n.raw[a:b]).hexdigest(),instructions=[dict(rva=hex(i.address),op=i.mnemonic+' '+i.op_str)for i in d.disasm(n.raw[a:b],a)])for a,b in ranges],stubs=['Type-init flags and static class/singleton metadata are initialized fixtures; managed allocator/constructors and generic list get/remove are stubs. Native list appending, branch and loop instructions execute.','Unity object null/equality is a fixture predicate; protected int/long getters read fixture scalars. Real IsAlive body and its HP/state branches execute.','getBasicSkillAttack(true) returns declared runtime B; HealSkill_HealFlag uses declared no-external-enhancement fixture. Real float32 multiply and integerisation body execute.','Attack/Heal/virtual callback, AddHitList and damage-protection setters are intercepted requests; no final HP or real battle objects.'],limits='Only intrinsic F0 execution requests. No nearest-target guarantee, actual installed loadout, final HP, whole engine or device verification. B6 geometry/qualification/once-fire evidence reused without rerun.')

if __name__=='__main__':
 C.enable_utf8_console();md=Metadata(C.ROOT/'work/protection/metadata_aei_decoded.bin');ev=evidence(Native(md),md);C.write_json(OUT/'native_evidence.json',ev)
 print(json.dumps(dict(passed=ev['passed'],total=ev['total'],failed=[c['name']for c in ev['checks']if not c['passed']]),ensure_ascii=False))
 if ev['passed']!=ev['total']:raise SystemExit(1)
