"""P3B5: six directly consumed Boss namespace fields; no description binding."""
from __future__ import annotations
import hashlib
import json
import struct
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
import common as C
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from il2cpp_sample_code import Native
from metadata_targets import Metadata
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM
import unicorn.arm64_const as U

OUT=C.ROOT/'output/character_skills/remaining_five'
LIMITS=('仅原生局部消费/计时规则，未实机验证；实际装载与传授/英雄技替代另论；'
        'charainfo须通过既有E/F0门控；缺失/null不补零；类型73仅玩家执行分支；不承诺最终伤害/异常实际持续时间')
SPEC={
 (24,3):('持续施法结束时间阈值','游戏秒','BattleTime >= caster._behaviorTime + skillparam3 时置结束请求；不乘Chain',
         'Exec_LOCKED_CURSE持续施法路径；这是相对caster._behaviorTime的结束阈值，不保证整条技能或每个目标暗闇持续时长'),
 (56,2):('默认异常时长系数','无量纲系数','exec_curse bDefaultTime=true，fDefaultRate=skillparam2；各异常基准时间×本系数',
         'Exec_TARGET_CURSE已选中目标、exec_curse可施加分支；bit5 SetStop请求时间=10×p，bit7 SetSlow请求时间=60×p、速度输入0.5；其余异常分支不在本换算范围'),
 (68,4):('玛那返还工作对象计时阈值','游戏秒','skillparam4 -> cSkillManaCycleWork._timerBCount；_timerB += deltaTime，达到阈值才进入期限终结判定',
         'type68建立的ManaCycle对象且阈值大于运行时epsilon；计数/结束状态/玛那生成条件另有门控，本项不承诺返还数量或所有增益持续时间'),
 (73,5):('玩家炮击候选遍历入口时间阈值','游戏秒','候选遍历入口检查正时间阈值：_limitTimeCounter >= skillparam5 时不进入本轮候选遍历；不乘Chain',
         'Exec_MODE_LAUNCHER_player；计时从模式初始化零开始，按GetDeltaTime累加；次数门槛也在入口检查，结束动作还受motion状态约束；不宣称每发后重查时间/次数'),
 (73,6):('玩家炮击候选遍历入口正次数门槛','次','N=trunc_int32(float32(skillparam6))；候选遍历入口仅在N>=1时检查_numCounter>=N，不满足时才可进入本轮候选遍历',
         'Exec_MODE_LAUNCHER_player；每次attack后计数加1；循环内不重查次数，skillparam7非正时同轮多个候选可越过门槛，不能当无条件硬上限；不是命中目标数或保证发射次数'),
 (73,7):('玩家炮击发射后冷却重置','游戏秒','每次attack后_timeCounter=skillparam7；正值使本轮停止继续遍历，后续按GetDeltaTime递减；非正值可在同轮继续候选遍历',
         'Exec_MODE_LAUNCHER_player；初始计时为0，第一发不先等待本项；入口要求冷却<=0并检查次数/期限，仍须目标/触控/动作门控；非正冷却同轮可越过次数门槛'),
}

def rule_rows():
 return [dict(table='bossskill',effect_type=t,field_path=f'/skillparam{s}',meaning_zh=v[0],unit=v[1],
              conversion=v[2],applicability=v[3],limits=LIMITS,status='已确认原生局部消费；未实机验证',
              answer_kind='remaining_five',origin='output/character_skills/remaining_five/field_dictionary.json',
              evidence=['scripts/character_skills/remaining_five.py','output/character_skills/remaining_five/native_evidence.json'] +
                       (['output/character_skills/remaining_five/f1_native_evidence.json'] if t==73 else []))
         for (t,s),v in SPEC.items()]

def convert(t,field,value,record):
 s=int(field.removeprefix('/skillparam'));kind,unit,formula,condition=SPEC[t,s];p=f'{value:.7g}'
 if (t,s)==(24,3):text=f'施法结束阈值：caster._behaviorTime + {p} 游戏秒（非目标异常时长）'
 elif (t,s)==(56,2):
  flag=record.get('skillflag0_0')
  if flag==32:text=f'默认异常时长系数 ×{p}；仅bit5 SetStop分支请求10×{p} 游戏秒（非实际持续保证）'
  elif flag==128:text=f'默认异常时长系数 ×{p}；仅bit7 SetSlow分支请求60×{p} 游戏秒，速度输入0.5（非实际持续保证）'
  else:text=f'传给exec_curse的默认异常时长系数 {p}（本记录flag具体分支未在本批确认）'
 elif (t,s)==(68,4):text=f'ManaCycle计时阈值 {p} 游戏秒（仅正阈值计时路径；返还仍有门控）'
 elif (t,s)==(73,5):text=(f'玩家炮击候选遍历入口时间阈值 {p} 游戏秒' if value>0 else '本项非正：不启用正时间入口阈值')
 elif (t,s)==(73,6):
  f=struct.unpack('<f',struct.pack('<f',value))[0];n=max(-2147483648,min(2147483647,int(f)))
  text=f'玩家炮击候选遍历入口正次数门槛 {n} 次（向零整数化；非正冷却同轮可越过）' if n>=1 else f'整数化为 {n}：不启用正次数入口门槛'
 else:text=f'每次发射后冷却重置 {p} 游戏秒（正值停止本轮继续遍历；第一发不预等）'
 return dict(quantity_kind=kind,unit=unit,value_text=text,note=condition+'；'+formula+'；'+LIMITS,
             answer_status='CONFIRMED_NUMERIC')

def native_evidence(n,md):
 dis=Cs(CS_ARCH_ARM64,CS_MODE_ARM);checks=[]
 def check(name,ok,**detail):checks.append(dict(name=name,passed=bool(ok),**detail))
 def op(a):i=next(dis.disasm(n.raw[a:a+4],a));return i.mnemonic+' '+i.op_str
 pins={0x118b87c:'ldr s1, [x8, #0x14c]',0x118b880:'ldr s2, [x20, #0x38]',0x118b884:'fadd s1, s1, s2',
       0x118b888:'fcmp s0, s1',0x118b88c:'b.lt #0x118b898',0x118b894:'strb w8, [x19]',
       0x11955e4:'ldr s8, [x19, #0x34]',0x1195638:'mov w3, #1',0x119564c:'mov v0.16b, v8.16b',0x1195650:'bl #0x1183f54',
       0x1184270:'tbz w20, #5, #0x11842a4',0x118427c:'fmov s0, #10.00000000',0x1184280:'fmul s0, s8, s0',0x11842a0:'bl #0x176e164',
       0x11843e8:'tbz w20, #7, #0x1184424',0x11843f4:'mov w8, #0x42700000',0x11843fc:'fmul s1, s8, s0',
       0x1184410:'fmov s0, #0.50000000',0x1184420:'bl #0x176c094',
       0x119711c:'b #0x1197120',0x11971c0:'mov x1, x19',0x11971d4:'b #0x11276a0',0x11276ac:'b #0x11276b0',
       0x112772c:'cmp w23, #0x44',0x1127788:'ldr w9, [x21, #0x3c]',0x112778c:'str w9, [x8, #0x34]',
       0x110de00:'fadd s3, s1, s8',0x110de28:'str s3, [x8, #0x30]',0x110de68:'ldp s0, s1, [x8, #0x30]',
       0x110de70:'b.lt #0x110def4',0x110ded0:'cmp w1, #1',0x110dee0:'bl #0x11279c0',
       0x119931c:'cbz w8, #0x119932c',0x1199334:'b #0x119933c',0x1199490:'ldp s13, s1, [x19, #0x40]',
       0x11994a0:'fcvtzs w8, s1',0x1199538:'fadd s0, s8, s0',0x119953c:'str s0, [x19, #0xc4]',
       0x11995b4:'str wzr, [x19, #0xc8]',0x11995b8:'str xzr, [x19, #0xc0]',
       0x119996c:'fcmp s0, s13',0x1199980:'cmp w8, w29',0x1199d64:'bl #0x119a47c',
       0x119a614:'add w8, w8, #1',0x119a618:'str w8, [x19, #0xc8]',
       0x119a60c:'ldr w9, [x19, #0x48]',0x119a61c:'str w9, [x19, #0xc0]'}
 check('direct_load_conversion_gate_consumer_pins',all(op(a)==v for a,v in pins.items()),pins=[dict(rva=hex(a),expected=v,actual=op(a)) for a,v in pins.items()])
 types={md.string(t[0]):i for i,t in enumerate(md.types)}
 fields={t:{r['name']:r['offset'] for r in n.fields(types[t])} for t in ['bhSkillUtil','cSkillManaCycleWork','CharaBehavior']}
 check('metadata_slot_and_timer_identity',all(fields['bhSkillUtil'][f'_skillparam{s}']==hex(0x2c+4*s) for s in range(10)) and
       fields['cSkillManaCycleWork']['_timerBCount']=='0x34' and fields['CharaBehavior']['_behaviorTime']=='0x14c',fields=fields)
 methods={a:[n.method(j) for j in n.method_by_rva.get(a,[])] for a in [0x118b680,0x1195444,0x1183f54,0x176e164,0x176c094,0x1197120,0x11276a0,0x11276b0,0x110dc94,0x119933c,0x119a47c]}
 expected={0x118b680:('bhSkillUtil','Exec_LOCKED_CURSE'),0x1195444:('bhSkillUtil','Exec_TARGET_CURSE'),
   0x1183f54:('bhSkillUtil','exec_curse'),0x176e164:('CharaStatus','SetStop'),0x176c094:('CharaStatus','SetSlow'),
   0x1197120:('bhSkillUtil','common_Exec_MANA_CYCLE'),0x11276a0:('BattleParam','startManaCycle'),
   0x11276b0:('BattleParam','initManaCycle'),0x110dc94:('BattleParam','update_ManaCycle'),
   0x119933c:('bhSkillUtil','Exec_MODE_LAUNCHER_player'),0x119a47c:('bhSkillUtil','Exec_MODE_LAUNCHER_attack')}
 check('metadata_workers_and_setters',all(any((r['declaring_type'],r['name'])==expected[a] for r in vv) for a,vv in methods.items()),methods={hex(k):v for k,v in methods.items()})
 # Each fragment is executed from the recovered image. No production converter
 # supplies the expected values; setter calls/end blocks are boundaries.
 def machine():
  u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,(len(n.raw)+4095)&~4095);u.mem_write(0,n.raw)
  u.mem_map(0x40000000,0x20000);u.reg_write(U.UC_ARM64_REG_SP,0x4001f000);return u
 def sf(u,r,v):u.reg_write(getattr(U,f'UC_ARM64_REG_S{r}'),struct.unpack('<I',struct.pack('<f',v))[0])
 def gf(u,r):return struct.unpack('<f',struct.pack('<I',u.reg_read(getattr(U,f'UC_ARM64_REG_S{r}'))))[0]
 time_samples=[]
 for elapsed,expected in [(29,0),(30,1),(31,1)]:
  u=machine();u.reg_write(U.UC_ARM64_REG_X8,0x40001000);u.reg_write(U.UC_ARM64_REG_X20,0x40002000);u.reg_write(U.UC_ARM64_REG_X19,0x40003000)
  u.mem_write(0x4000114c,struct.pack('<f',100));u.mem_write(0x40002038,struct.pack('<f',30));sf(u,0,100+elapsed)
  u.emu_start(0x118b87c,0x118b898,count=20);actual=u.mem_read(0x40003000,1)[0]
  time_samples.append(dict(elapsed=elapsed,expected=expected,actual=actual))
 check('locked_curse_duration_boundary',all(v['expected']==v['actual'] for v in time_samples),samples=time_samples)
 samples=[]
 for bit,start,end,outreg,scale in [(5,0x1184270,0x11842a0,0,10),(7,0x11843e8,0x1184420,1,60)]:
  for p in [0,.5,1,2]:
   u=machine();u.reg_write(U.UC_ARM64_REG_W20,1<<bit);u.reg_write(U.UC_ARM64_REG_W19,1);u.reg_write(U.UC_ARM64_REG_X21,0x40001000);sf(u,8,p)
   u.emu_start(start,end,count=30);actual=gf(u,outreg);samples.append(dict(bit=bit,p=p,expected=scale*p,actual=actual))
 check('default_status_duration_coefficient',all(v['expected']==v['actual'] for v in samples),samples=samples)
 samples=[]
 for elapsed,expected in [(16,True),(17,False),(18,False)]:
  u=machine();u.reg_write(U.UC_ARM64_REG_X8,0x40001000);u.mem_write(0x40001030,struct.pack('<ff',elapsed,17))
  u.emu_start(0x110de68,0x110def4 if expected else 0x110de74,count=4)
  actual=u.reg_read(U.UC_ARM64_REG_PC)==0x110def4;samples.append(dict(elapsed=elapsed,continues=actual,expected=expected))
 check('mana_cycle_timer_boundary',all(v['continues']==v['expected'] for v in samples),samples=samples)
 samples=[]
 for time,cap,count,expected in [(39,6,5,1),(40,6,5,0),(39,6,6,0),(39,0,99,1),(40,0,0,0)]:
  u=machine();u.reg_write(U.UC_ARM64_REG_X19,0x40001000);u.reg_write(U.UC_ARM64_REG_W29,cap);sf(u,13,40)
  u.mem_write(0x400010c0,struct.pack('<ffI',0,time,count));u.emu_start(0x1199960,0x119999c,count=25)
  actual=u.reg_read(U.UC_ARM64_REG_W25);samples.append(dict(time=time,cap=cap,count=count,expected=expected,allowed=actual))
 check('launcher_entry_time_or_count_gate',all(v['expected']==v['allowed'] for v in samples),samples=samples)
 u=machine();u.reg_write(U.UC_ARM64_REG_X19,0x40001000);u.mem_write(0x40001048,struct.pack('<f',.5));u.mem_write(0x400010c8,struct.pack('<I',2))
 u.emu_start(0x119a608,0x119a620,count=8)
 check('launcher_shot_increments_and_resets_cooldown',struct.unpack('<I',u.mem_read(0x400010c8,4))[0]==3 and struct.unpack('<f',u.mem_read(0x400010c0,4))[0]==.5)
 return dict(evidence_kind='STATIC_AND_CONTROLLED_NATIVE_FRAGMENTS',image_sha256=hashlib.sha256(n.raw).hexdigest(),
             metadata_sha256=hashlib.sha256((C.ROOT/'work/protection/metadata_aei_decoded.bin').read_bytes()).hexdigest(),
             checks=checks,passed=sum(c['passed'] for c in checks),total=len(checks),not_tested='Full battle engine/device execution; actual active loadout')

def main():
 C.enable_utf8_console();md=Metadata(C.ROOT/'work/protection/metadata_aei_decoded.bin');n=Native(md);e=native_evidence(n,md)
 C.write_json(OUT/'native_evidence.json',e)
 if e['passed']!=e['total']:raise SystemExit('native evidence failed; no dictionary generated')
 C.write_json(OUT/'field_dictionary.json',rule_rows());print(f"native {e['passed']}/{e['total']}; rules {len(SPEC)}")

if __name__=='__main__':main()
