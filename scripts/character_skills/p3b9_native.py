"""P3B9 bounded type67 list/count/threshold consumers; not a battle emulator."""
import hashlib,json,math,struct,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent.parent)]
import common as C
from il2cpp_sample_code import Native
from metadata_targets import Metadata
from skilllist_types import enum_values
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
import unicorn.arm64_const as A
OUT=C.ROOT/'output/character_skills/description_bindings/p3b9_batch'

def evidence(n,md):
 checks=[];d=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 def ck(name,ok,**kw):checks.append(dict(name=name,passed=bool(ok),**kw))
 def ops(lo,hi):return [dict(rva=hex(i.address),op=i.mnemonic+' '+i.op_str)for i in d.disasm(n.raw[lo:hi],lo)]
 def reg(u,r,v):u.reg_write(getattr(A,'UC_ARM64_REG_'+r),v)
 def get(u,r):return u.reg_read(getattr(A,'UC_ARM64_REG_'+r))
 def q(u,a,v):u.mem_write(a,struct.pack('<Q',v&0xffffffffffffffff))
 def w(u,a,v):u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def b(u,a,v):u.mem_write(a,bytes([v]))
 def rq(u,a):return struct.unpack('<Q',u.mem_read(a,8))[0]
 def rw(u,a):return struct.unpack('<I',u.mem_read(a,4))[0]
 def sf(u,r,v):reg(u,'Q'+str(r),int.from_bytes(struct.pack('<f',v),'little'))
 def gf(u,r):return struct.unpack('<f',(get(u,'Q'+str(r))&0xffffffff).to_bytes(4,'little'))[0]
 ti={md.string(t[0]):i for i,t in enumerate(md.types)}
 fields={t:{f['name']:f['offset']for f in n.fields(ti[t])}for t in ['CharaBehavior','BattleParam','BattleManager']}
 enums=enum_values(n,md,'ABILITY_TYPE')
 expected={'CharaBehavior':{'_isActive':'0x118','_isVisible':'0x119'},'BattleManager':{'_aChara_Player':'0x70','_aChara_Enemy':'0x78'}}
 ck('metadata_type67_and_active_member_identity',enums['HeroOne']==67 and all(fields[t].get(k)==v for t,ff in expected.items()for k,v in ff.items()),fields=fields,enum= {'HeroOne':enums['HeroOne']},methods={hex(a):[n.method(i)for i in n.method_by_rva.get(a,[])]for a in [0x1113c8c,0x10bd338,0x1535abc,0x1113958,0x10fdd50]})
 old=C.load_json(C.ROOT/'output/character_skills/skilllist_types/composite_chains.json')
 branch={p:old['branches'][p+'/67']for p in ['attack','defence','move','crit_rate','crit_dmg']}
 dispatch=C.load_json(C.ROOT/'output/character_skills/skilllist_types/dispatch_map.json')
 ck('same_image_existing_five_type67_consumers',old['native_sha256']==hashlib.sha256(n.raw).hexdigest() and old['metadata_sha256']==hashlib.sha256(md.raw).hexdigest()and all(dispatch['types'][p]['entries']['67']['leaf']==branch[p]['leaf']for p in branch))
 MAN=0x40010000;LIST=0x40012000;OUTLIST=0x40016000;SELF=0x40020000;PEER=0x40022000
 def listset(u,a,items):
  q(u,a+0x10,a+0x100);w(u,a+0x18,len(items));w(u,a+0x118,32)
  for i,v in enumerate(items):q(u,a+0x120+8*i,v)
 def char(u,a,job=0,home=4,battle_home=0,weapon=0x400000,active=1,hp=10,state=0,visible=1,appear=0,hero=0):
  param=a+0x600;cp=a+0xa00;q(u,a+0x28,param);w(u,a+0x1c,state);b(u,a+0x118,active);b(u,a+0x119,visible);b(u,a+0x470,appear);b(u,a+0x3e8,hero)
  for off,val in [(0xf8,job),(0x68,hp),(0x1b0,weapon)]:q(u,param+off,param+off+0x100);q(u,param+off+0x100,val)
  q(u,param+0x338,cp);w(u,cp,home);w(u,cp+4,battle_home)
 def machine():
  u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,(len(n.raw)+4095)&~4095);u.mem_write(0,n.raw);u.mem_map(0x40000000,0x80000);reg(u,'SP',0x4007d000);reg(u,'LR',0x4007f000)
  for a in [0x29d5fa0,0x29b2c30,0x29be1b8,0x29b76e0,0x29d5498,0x29c3300,0x29f0b88]:q(u,a,0x40000100)
  q(u,0x40000100,0x40001000)
  w(u,0x400010e0,1);q(u,0x400010b8,0x40002000);q(u,0x40002000,0x40003000);q(u,0x40002010,MAN)
  w(u,0x400030b8,0x3f);w(u,0x400030a8,0x3f)
  for a in [0x2bd011c,0x2bcf5bb,0x2bcf5bc,0x2bcfe25,0x2bd01b2,0x2bd01b3,0x2bcf5ba]:b(u,a,1)
  listset(u,LIST,[SELF,PEER]);listset(u,LIST+0x1000,[]);listset(u,OUTLIST,[]);q(u,MAN+0x70,LIST);q(u,MAN+0x78,LIST+0x1000)
  char(u,SELF);char(u,PEER);return u
 def hook(uu,a,size,data):
  if a in [0x88d81c,0x88d8fc]:reg(uu,'PC',get(uu,'LR'));return
  if a==0x88d920:raise AssertionError('unexpected native throw '+hex(get(uu,'LR')))
  if a==0xa84484:reg(uu,'X0',rq(uu,rq(uu,get(uu,'X0')+0x10)+0x20+8*get(uu,'W1')))
  elif a==0x1eb8358:reg(uu,'W0',int(get(uu,'X0')==get(uu,'X1')))
  elif a in [0xa92534,0xa926f0,0xa928d8]:reg(uu,'X0',rq(uu,get(uu,'X0')))
  elif a==0x180c974:reg(uu,'W0',rw(uu,get(uu,'X0')))
  elif a==0x180db90:reg(uu,'W0',rw(uu,get(uu,'X0')+4))
  else:return
  reg(uu,'PC',get(uu,'LR'))
 def run_count(u,job=1,wep=0,home=0,ctype=0):
  h=u.hook_add(UC_HOOK_CODE,hook);reg(u,'W0',ctype);reg(u,'W1',job);reg(u,'X2',wep);reg(u,'W3',home);reg(u,'X4',OUTLIST);reg(u,'LR',0x4007f000)
  u.emu_start(0x1113c8c,0x4007f000,count=10000);u.hook_del(h);return get(u,'W0')
 def member(u,ctype=0,active=0,alive=1,ground=0,visible=0):
  h=u.hook_add(UC_HOOK_CODE,hook);reg(u,'X0',MAN);reg(u,'X1',OUTLIST);reg(u,'W2',ctype);reg(u,'W3',active);reg(u,'W4',visible);reg(u,'W5',alive);reg(u,'W6',ground);reg(u,'LR',0x4007f000)
  u.emu_start(0x10bd338,0x4007f000,count=10000);u.hook_del(h);return [rq(u,OUTLIST+0x120+8*i)for i in range(rw(u,OUTLIST+0x18))]
 samples=[]
 cases=[('base',{},2),('self_inactive',{'active':0},1),('self_active2',{'active':2},2),('self_hp0',{'hp':0},1),('self_hp_negative',{'hp':-1},1),('self_state12',{'state':12},1),('self_state11',{'state':11},2),('self_invisible',{'visible':0},2),('self_appearance_hero0',{'appear':1,'hero':0},2),('self_other_job',{'job':1},1)]
 for label,changes,expected_count in cases:
  u=machine();char(u,SELF,**changes);selected=member(u);got=run_count(u);samples.append(dict(case=label,changes=changes,list_includes_self=SELF in selected,selected=len(selected),count=got,expected=expected_count))
 ck('actual_member_alive_then_calc_active_and_self_filter',all(x['count']==x['expected']for x in samples),samples=samples,interpretation='GetMemberList overload onlyAlive=1, onlyActive=0, onlyVisible=0 unused, onlyInGround=0. Calc separately requires _isActive!=0. This overload has no appearance/hero filter; no self removal.')
 combos=[]
 for selfmatch in [True,False]:
  for included in [True,False]:
   for peers in [0,1,2]:
    u=machine();char(u,SELF,job=0 if selfmatch else 1);char(u,PEER);char(u,PEER+0x2000);listset(u,LIST,([SELF]if included else[])+[PEER+0x2000*i for i in range(peers)])
    member(u);got=run_count(u);exp=int(selfmatch and included)+peers;combos.append(dict(self_matches=selfmatch,self_in_list=included,peers=peers,count=got,expected=exp,threshold1=got>=1,threshold2=got>=2))
 ck('self_matching_included_or_absent_peers0_1_2_thresholds',all(x['count']==x['expected']for x in combos),samples=combos)
 filters=[]
 for label,changes,j,wep,home,exp in [('job0',{},1,0,0,2),('job_nonmatch',{},2,0,0,0),('weapon_match',{},1,0x400000,0,2),('weapon_nonmatch',{},1,0x800000,0,0),('home_match',{},1,0,4,2),('home_nonmatch',{},1,0,9,0),('battle_home',{'battle_home':9},1,0,9,1),('all_three_and',{'job':1},1,0x400000,4,1)]:
  u=machine();char(u,SELF,**changes);member(u);got=run_count(u,j,wep,home);filters.append(dict(case=label,count=got,expected=exp))
 ck('real_job_weapon_home_and_battlehome_filters',all(x['count']==x['expected']for x in filters),samples=filters)
 sides=[]
 for ctype in [0,1]:
  u=machine();listset(u,LIST,[SELF]);listset(u,LIST+0x1000,[PEER]);selected=member(u,ctype);count=run_count(u,ctype=ctype);sides.append(dict(ctype=ctype,selected=selected,count=count))
 ck('actual_same_side_member_list_selection',sides==[dict(ctype=0,selected=[SELF],count=1),dict(ctype=1,selected=[PEER],count=1)],samples=sides)
 masks=[]
 for mask in [0,1,2,3]:
  u=machine();member(u);w(u,0x400030b8,mask);got=run_count(u);masks.append(dict(aggregate_job_bitmap=mask,count=got,expected=2 if mask&1 else 0))
 ck('actual_aggregate_job_bitmap_fast_gate',all(x['count']==x['expected']for x in masks),samples=masks,limit='Explicit consistent/inconsistent list-summary fixture; native checks summary intersection before its per-member job test. No claim that arbitrary stale summaries occur in gameplay.')
 # Run all five current type67 worker blocks with genuine count/helper calls.
 # Prebuilt list is a documented caller cache, not a count-result stub.
 runs=[];callargs=[]
 getrva={0x1dbcf24:'param0',0x1dbd30c:'iParam0',0x1dbd1ac:'param8',0x1dbd444:'flag',0x1dbcf3c:'param1',0x1dbcf7c:'param2'}
 # Derive actual named getter addresses from method metadata, not guessed spacing.
 for a,inds in n.method_by_rva.items():
  for mi in inds:
   m=n.method(mi)
   if m['declaring_type']=='skillParameter'and m['name']in ['get_param0','get_param1','get_param2','get_param3','get_param6','get_param7','get_param8','get_iParam0','get_flag']:getrva[a]=m['name'][4:]
 # Obtain worker entry registers from instructions and set the callee-saved set
 # uniformly; SP list/type slots differ by path and are fixed per actual bytes.
 setup={'attack':(0x10,0x1c,29),'defence':(0x8,0x1c,29),'move':(0x8,0x2c,26),'crit_rate':(0x8,0x1c,27),'crit_dmg':(0,0xc,27)}
 builds=[]
 for path,ev in branch.items():
  u=machine();bp=0x40040000;listset(u,OUTLIST,[])
  for i in range(19,30):reg(u,'X'+str(i),bp)
  if path=='crit_dmg':reg(u,'X26',0x40000100)
  for off in [0x448,0x450,0x458,0x460,0x468]:q(u,bp+off,OUTLIST)
  if path=='move':reg(u,'W20',0)
  listoff,typeoff,_=setup[path];q(u,get(u,'SP')+listoff,0);w(u,get(u,'SP')+typeoff,0)
  def capture(uu,a,s,data):
   if a==0x10bd338:
    builds.append(dict(path=path,manager=get(uu,'X0'),list=get(uu,'X1'),ctype=get(uu,'W2'),onlyActive=get(uu,'W3'),unusedVisibleArg=get(uu,'W4'),onlyAlive=get(uu,'W5'),onlyInGround=get(uu,'W6')));uu.emu_stop();return
   hook(uu,a,s,data)
  h=u.hook_add(UC_HOOK_CODE,capture);u.emu_start(int(ev['leaf'],16),0x4007f000,count=10000);u.hook_del(h)
 ck('five_real_worker_list_builder_arguments',len(builds)==5 and all(x['manager']==MAN and x['list']==OUTLIST and x['ctype']==0 and x['onlyActive']==0 and x['unusedVisibleArg']==0 and x['onlyAlive']==1 and x['onlyInGround']==0 for x in builds),samples=builds)
 for path,ev in branch.items():
  leaf=int(ev['leaf'],16);acc=int(ev['accumulate']['rva'],16)
  for threshold in [1.,2.,2.9]:
   for peers in [0,1,2]:
    u=machine();listset(u,OUTLIST,[SELF]+[PEER+0x2000*i for i in range(peers)]);char(u,PEER+0x2000)
    for i in range(19,30):reg(u,'X'+str(i),0x40040000)
    if path=='move':reg(u,'W20',0)
    sp=get(u,'SP');listoff,typeoff,rec=setup[path];q(u,sp+listoff,OUTLIST);w(u,sp+typeoff,0)
    sf(u,8,1.25);sf(u,9,0.75);values=dict(param0=threshold,param8=0.,iParam0=1,flag=0,param1=1.4,param2=1.3,param3=.85,param6=.2,param7=.4)
    seen=[]
    def worker(uu,a,s,data):
     if a in getrva:
      f=getrva[a];seen.append(f)
      if f in ['iParam0','flag']:reg(uu,'X0',values[f])
      else:sf(uu,0,values[f])
      reg(uu,'PC',get(uu,'LR'));return
     if a==0x1113c8c:callargs.append(dict(path=path,args=[get(uu,'W0'),get(uu,'W1'),get(uu,'X2'),get(uu,'W3'),get(uu,'X4')]))
     hook(uu,a,s,data)
    h=u.hook_add(UC_HOOK_CODE,worker)
    # Stop on the worker's skip target or immediately after its accumulate.
    compare=next(x for x in ev['compares']if x['test'].startswith('cmp w0,'));skip=int(compare['branch'].split('#')[1],16)
    def stop(uu,a,s,data):
     if a in [skip,acc+4]:uu.emu_stop()
    hs=u.hook_add(UC_HOOK_CODE,stop);u.emu_start(leaf,0x4007f000,count=20000);u.hook_del(h);u.hook_del(hs)
    fields={'attack':'param1','defence':'param3','move':'param2','crit_rate':'param6','crit_dmg':'param7'};base=1.25 if path in ['attack','defence','move']else .75;expected=base*(values[fields[path]]if 1+peers>=int(threshold)else 1)if path in ['attack','defence','move']else base+(values[fields[path]]if 1+peers>=int(threshold)else 0)
    actual=gf(u,8 if path in ['attack','defence','move']else 9);runs.append(dict(path=path,threshold=threshold,count=1+peers,actual=actual,expected=expected,getters=seen,passed=math.isclose(actual,expected,rel_tol=1e-6,abs_tol=1e-6)))
 ck('five_real_workers_count_threshold_conversion_and_numeric_units',all(x['passed']for x in runs),samples=runs,actual_count_call_arguments=callargs,getter_fixture='Only skillParameter protected getter outputs are explicit raw scalar inputs. Branch, float/int conversion, real CalcCharaNum, conjunction and accumulate instructions execute unchanged.')
 slices=[(0x1113c8c,0x1113e9c),(0x10bd338,0x10bd55c),(0x1535abc,0x1535afc),(0x1113958,0x1113a10),(0x10fdd50,0x10fdeb4)]
 reused=[C.ROOT/'output/character_skills/skilllist_types'/x for x in ['dispatch_map.json','composite_chains.json','filter_dictionary.json','native_checks.json']]
 return dict(status='C_BOUNDED_NATIVE_SELF_CHECK_NOT_D_OR_RUNTIME',native_sha256=hashlib.sha256(n.raw).hexdigest(),metadata_sha256=hashlib.sha256(md.raw).hexdigest(),checks=checks,passed=sum(x['passed']for x in checks),total=len(checks),slices=[dict(start=hex(a),end=hex(b),instructions=ops(a,b))for a,b in slices],reused_evidence=[dict(path=str(p.relative_to(C.ROOT)).replace('\\','/'),sha256=C.sha256_file(p))for p in reused],limits='Managed lists, static singleton/type initialization, scalar protected getters and Unity null comparison are explicit fixtures/stubs. List selection/filter/append, IsAlive, CalcCharaNum/home conjunction and five worker thresholds/accumulates run current instructions. Native count sees a supplied same-side list/cache and aggregate job bitmap; actual loadout, dynamic identity, all engine consumers and final combat values are not claimed.')

def main():
 C.enable_utf8_console();md=Metadata(C.ROOT/'work/protection/metadata_aei_decoded.bin');ev=evidence(Native(md),md);C.write_json(OUT/'native_evidence.json',ev);print(json.dumps(dict(passed=ev['passed'],total=ev['total'],failed=[x['name']for x in ev['checks']if not x['passed']]),ensure_ascii=False))
 if ev['passed']!=ev['total']:raise SystemExit(1)
if __name__=='__main__':main()
