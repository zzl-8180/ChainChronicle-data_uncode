"""P3B3: bounded native evidence for ManaGet param0; no text-template inference."""
from __future__ import annotations

import collections
import functools
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import common as C
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from il2cpp_sample_code import Native
from metadata_targets import Metadata
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
import unicorn.arm64_const as U

OUT = C.ROOT / "output/character_skills/type26_mana"
KIND = "开局基础玛那数量（持有者职业）"
UNIT = "个（float32→有符号int32向零截断；小于1不授予）"
CONDITION = ("PartyAbilityInit 的非继续战斗路径：传入列表中的存活角色、BattleParam.isHero=false、"
             "已装载的普通type26能力；param6整数码=1，或=0且CharaBehavior._isActive非0，"
             "或=2且_isActive为0。其他码跳过；有效PanelManaGage为授予对象")
LIMITS = ("仅param0这条基础产线的授予调用数，不是队伍开局玛那总数，也不计其他能力/其他产线；"
          "不证明当前账号装载或最终玛那库存；没有实机验证。_isActive字段名已由元数据确认，"
          "不据此推断前后备的完整业务状态")
REVIEWED = {
    3101: ('da4a5d023ab1dd098be9f0a793b195b59efe49bf07bc79ef26a2523826799dee',
           'マナを１つ持った状態で戦闘を開始する'),
    3102: ('58ee4d9f03f10079f7bc0cad7bd5b221c4f32eb4b902472becf5f1ff1f5f296c',
           'マナを２つ持った状態で戦闘を開始する'),
}


@functools.lru_cache(maxsize=1)
def published_native():
    return C.load_json(OUT/'native_evidence.json')


def bind_type26(entry, fragment, answers, children):
    """Only two whole-record editorial decisions, with exact change guards."""
    rec=entry.get('record') or {};spec=REVIEWED.get(entry.get('reference_id'))
    if entry.get('table')!='skilllist':return None,'OUTSIDE_ORDINARY_SKILLLIST'
    if entry.get('layer')!='APK' or not spec:return None,'RECORD_NOT_IN_TYPE26_REVIEWED_PAIR'
    sha,text=spec
    blob=json.dumps(rec,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    if hashlib.sha256(blob).hexdigest()!=sha:return None,'REVIEWED_RECORD_CHANGED'
    source=entry.get('source') or {}
    if source.get('layer')!='APK' or source.get('raw_record_sha256')!=sha:return None,'SOURCE_STAMP_MISMATCH'
    if rec.get('ability')!=26 or fragment!=text:return None,'FRAGMENT_NOT_REVIEWED'
    if rec.get('sub') or children:return None,'SUBEFFECT_NOT_REVIEWED'
    if any(rec.get(f)!=0 for f in ['param1','param2','param3','param4','param5','param6','param7','iParam0','iParam1']):
        return None,'OTHER_MANA_LINE_OR_GATE_CHANGED'
    ev=published_native()
    if ev['passed']!=ev['total']:return None,'NATIVE_EVIDENCE_FAILED'
    hits=[a for a in answers if a['f']=='/param0' and a['kind']==KIND and a['status']=='CONFIRMED_NUMERIC']
    if len(hits)!=1 or hits[0]['raw']!=rec['param0']:return None,'LOCAL_NUMERIC_ANSWER_NOT_UNIQUE'
    a=hits[0]
    return dict(template_id=f'type26_start_mana_{entry["reference_id"]}',
        strength='逐记录人工语义对应＋原值与原生效果规则支持；不是机器码解析日文',
        status='已确认（限定本记录的描述对应）',target='传入PanelManaGage；颜色由能力持有者职业决定',
        condition=CONDITION+'；本记录param6=0，须_isActive非0',duration='开局一次授予；不是持续时间或每WAVE',
        rationale='完整原文只有开局玛那一句；无sub；其他产线零值经原生分支核对不贡献；原文１/２只作区分性对照，答案由param0原值和原生换算生成',
        source=source,fields=[dict(f=a['f'],raw=a['raw'],value=a['value'],kind=a['kind'],unit=a['unit'],
            status=a['status'],evidence_scope=a['scope'],rule_key=a['rule_key'],table='skilllist',
            record_id=entry['reference_id'],semantic_effect='开局基础玛那',native_path='ManaGet.param0',
            native=dict(read='0x158cb8c',conversion='0x158cb90..0x158cba4',consume='0x158cbc8'))],
        siblings=[],native_evidence='output/character_skills/type26_mana/native_evidence.json',
        eligibility_evidence='output/character_skills/type26_mana/native_evidence.json#static_consumption_chain',
        limits=LIMITS),None


def signed_count(value):
    """The actual s0 float32 / fcvtzs w8 / +infinity override at 0x158cb90."""
    try:
        v = struct.unpack('<f', struct.pack('<f', value))[0]
    except OverflowError:
        v = math.copysign(math.inf, value)
    if v == math.inf or v <= -2147483648:
        return -2147483648
    if math.isnan(v):
        return 0
    return min(2147483647, math.trunc(v))


def convert(value, record):
    n = signed_count(value)
    body = (f"战斗开始时按持有者职业授予 {n} 个基础玛那（param0产线）" if n >= 1 else
            f"原值 {value} → 原生整数化 {n} < 1：param0这条基础产线不授予玛那")
    return {"quantity_kind": KIND, "value_text": body, "unit": UNIT,
            "note": CONDITION + "；isBoost=(param5==1)；" + LIMITS}


def native_evidence(native, md):
    dis = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    checks = []
    def check(name, passed, **detail):
        checks.append(dict(name=name, passed=bool(passed), **detail))
    def at(addr):
        i = next(dis.disasm(native.raw[addr:addr+4], addr))
        return i.mnemonic + ' ' + i.op_str
    # Every link is checked against current image bytes, not a saved disassembly.
    expected = {
        0x157669c:'mov w0, #0x1a', 0x15766a0:'bl #0x15771e8',
        0x15766ac:'strh w0, [x8, #0x2a]', 0x158ca28:'ldrh w25, [x8, #0x2a]',
        0x158ca6c:'mov x3, x25', 0x158ca74:'bl #0x1117a20',
        0x1117aec:'bl #0x1578da0', 0x1117af0:'mov w3, w0',
        0x1117b00:'bl #0x1117b54', 0x1117bfc:'bl #0x1dbcf0c',
        0x1117c00:'cmp w0, w21', 0x1117c04:'b.ne #0x1117c34',
        0x1117c14:'bl #0x1112574',
        0x158c350:'bl #0x1535abc', 0x158c354:'tbz w0, #0, #0x158c644',
        0x158c358:'tbz w22, #0, #0x158c3e0', 0x158c3dc:'b #0x158c644',
        0x158c628:'bl #0x158c958', 0x158c9ec:'ldrb w8, [x24, #0x1f]',
        0x158c9f0:'cbnz w8, #0x158cf54', 0x158c9fc:'ldrb w9, [x22, #0x118]',
        0x158cac0:'bl #0x1dbd04c', 0x158cb24:'ldr x0, [x8, #0xf8]',
        0x158cb2c:'bl #0xa92534', 0x158cb58:'bl #0x15787c4',
        0x158cb7c:'bl #0x13a5f34', 0x158cb80:'mov w26, w0',
        0x158cb8c:'bl #0x1dbcf24', 0x158cb98:'fcvtzs w8, s0',
        0x158cb9c:'fcmp s0, s1', 0x158cba4:'csel w23, w9, w8, eq',
        0x158cba8:'cmp w23, #1', 0x158cbac:'b.lt #0x158cbd4',
        0x158cbb4:'fcmp s8, s9', 0x158cbb8:'cset w2, eq',
        0x158cbbc:'mov x0, x20', 0x158cbc0:'mov w1, w26',
        0x158cbc8:'bl #0x1244280', 0x158cbcc:'subs w23, w23, #1',
        0x158cbd0:'b.ne #0x158cbb4', 0x158ceac:'bl #0x1dbcf84',
        0x158cee8:'bl #0x1244280', 0x158cf3c:'bl #0x1244268',
        0x124428c:'mov w4, #1', 0x1244294:'b #0x1243db8',
    }
    got = {hex(a):at(a) for a in expected}
    check('static_consumption_chain', all(at(a)==op for a,op in expected.items()), instructions=got)
    types = {md.string(t[0]):i for i,t in enumerate(md.types)}
    fields = {'AbilityTypeCachedFlagIndex':('_ManaGet','0x2a'),
              'BattleParam':('_jobType','0xf8'), 'CharaBehavior':('_isActive','0x118')}
    offsets = {t:next(f for f in native.fields(types[t]) if f['name']==v[0]) for t,v in fields.items()}
    hero = next(f for f in native.fields(types['BattleParam']) if f['name']=='isHero')
    check('metadata_fields', all(offsets[t]['offset']==v[1] for t,v in fields.items())
          and hero['offset']=='0x1f', fields=offsets, hero=hero)
    methods = {0x15771e8:('Constants','AbilityType2FlagIndex'),
               0x1578da0:('Constants','FlagIndex2AbilityType'),
               0x1117a20:('BattleParam','GetAbilityListOnFlagIndex'),
               0x1dbcf0c:('skillParameter','get_ability'), 0x1dbcf24:('skillParameter','get_param0'),
               0x158c234:('PlayerManager','PartyAbilityInit'),
               0x158c958:('PlayerManager','subPartyAbilityInit_ManaGet'),
               0x1244280:('PanelManaGage','ProduceManaForce'), 0x1243db8:('PanelManaGage','AddMana')}
    resolved={hex(a):[native.method(mi) for mi in native.method_by_rva.get(a,[])] for a in methods}
    check('metadata_method_identity', all(any((m['declaring_type'],m['name'])==want
          for m in resolved[hex(a)]) for a,want in methods.items()), methods=resolved)

    def machine(lo, size=0x1000):
        uc=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
        uc.mem_map(lo,size);uc.mem_write(lo,native.raw[lo:lo+size])
        uc.mem_map(0x40000000,0x10000);uc.reg_write(U.UC_ARM64_REG_SP,0x40008000)
        return uc
    # Execute getter→conversion→loop with only the getter and grant-call stubs.
    samples=[]
    for value in [-2,-.75,0,.75,1,1.9,2,3,math.nan,math.inf,-math.inf]:
        for boost in [0,1,2]:
            uc=machine(0x158c000);calls=[]
            bits=int.from_bytes(struct.pack('<f',value),'little')
            uc.reg_write(U.UC_ARM64_REG_X20,0x40000100)
            uc.reg_write(U.UC_ARM64_REG_X26,8)
            uc.reg_write(U.UC_ARM64_REG_Q8,int.from_bytes(struct.pack('<f',boost),'little'))
            uc.reg_write(U.UC_ARM64_REG_Q9,int.from_bytes(struct.pack('<f',1),'little'))
            def hook(u,addr,size,data):
                if addr==0x158cb8c:
                    u.reg_write(U.UC_ARM64_REG_Q0,bits);u.reg_write(U.UC_ARM64_REG_PC,addr+4)
                elif addr==0x158cbc8:
                    calls.append([u.reg_read(U.UC_ARM64_REG_X0),u.reg_read(U.UC_ARM64_REG_W1),u.reg_read(U.UC_ARM64_REG_W2)])
                    u.reg_write(U.UC_ARM64_REG_PC,addr+4)
            uc.hook_add(UC_HOOK_CODE,hook);uc.emu_start(0x158cb84,0x158cbd4,count=1000)
            converted=uc.reg_read(U.UC_ARM64_REG_W23)
            want=max(0,signed_count(value))
            samples.append(dict(input_float32_bits=hex(bits),value=str(value),param5=boost,
                                expected_calls=want,calls=calls,final_counter=converted))
    check('native_conversion_and_grant_loop', all(len(s['calls'])==s['expected_calls']
          and all(c==[0x40000100,8,int(s['param5']==1)] for c in s['calls']) for s in samples), samples=samples)
    # Large conversion boundaries stop before entering a potentially huge grant loop.
    boundaries=[]
    for value in [2147483648.,-2147483904.,16777217.,1e30]:
        uc=machine(0x158c000);uc.reg_write(U.UC_ARM64_REG_Q0,int.from_bytes(struct.pack('<f',value),'little'))
        uc.emu_start(0x158cb90,0x158cba8,count=20)
        gotn=uc.reg_read(U.UC_ARM64_REG_W23);gotn=gotn-(1<<32) if gotn&(1<<31) else gotn
        boundaries.append(dict(input=value,actual=gotn,expected=signed_count(value)))
    check('float32_int32_boundaries', all(x['actual']==x['expected'] for x in boundaries), samples=boundaries)
    gates=[]
    for mode in [-1,0,1,2,3]:
        for active in [0,1]:
            uc=machine(0x158c000);uc.reg_write(U.UC_ARM64_REG_W23,mode&0xffffffff)
            uc.mem_write(0x40008028,struct.pack('<I',active));reached=[]
            def gate(u,a,s,d):
                if a in [0x158cb1c,0x158cf48]:reached.append(a);u.emu_stop()
            uc.hook_add(UC_HOOK_CODE,gate);uc.emu_start(0x158caf4,0x158cf54,count=40)
            want=mode==1 or mode==0 and active!=0 or mode==2 and active==0
            gates.append(dict(mode=mode,active=active,passed=reached==[0x158cb1c],expected=want))
    check('native_param6_scope_gate', all(x['passed']==x['expected'] for x in gates), samples=gates)
    # Execute the ability equality test with type 26 and a distinct negative type.
    type_tests=[]
    for ability in [8,25,26,27]:
        uc=machine(0x1117000);uc.reg_write(U.UC_ARM64_REG_W21,26);reached=[]
        def typ(u,a,s,d):
            if a==0x1117bfc:u.reg_write(U.UC_ARM64_REG_W0,ability);u.reg_write(U.UC_ARM64_REG_PC,a+4)
            if a in [0x1117c08,0x1117c34]:reached.append(a);u.emu_stop()
        uc.hook_add(UC_HOOK_CODE,typ);uc.emu_start(0x1117bf4,0x1117c48,count=30)
        type_tests.append(dict(ability=ability,accepted=reached==[0x1117c08]))
    check('native_exact_ability_filter', all(x['accepted']==(x['ability']==26) for x in type_tests), samples=type_tests)
    job_tests=[]
    for job in [-1,0,1,2,3,4,5,6]:
        uc=machine(0x1578000);uc.mem_map(0x2074000,0x1000)
        uc.mem_write(0x2074000,native.raw[0x2074000:0x2075000]);uc.reg_write(U.UC_ARM64_REG_W0,job&0xffffffff)
        def job_ret(u,a,s,d):
            if a in [0x15787d8,0x15787e0]:u.emu_stop()
        uc.hook_add(UC_HOOK_CODE,job_ret);uc.emu_start(0x15787c4,0x15787e4,count=20)
        color=uc.reg_read(U.UC_ARM64_REG_W0)
        trans=machine(0x13a5000);trans.reg_write(U.UC_ARM64_REG_W0,color)
        trans.emu_start(0x13a5f34,0x13a5f70,count=30)
        job_tests.append(dict(job=job,mana_type=color,element_flag=trans.reg_read(U.UC_ARM64_REG_W0)))
    check('native_holder_job_color', [s['mana_type'] for s in job_tests]==[0,3,4,2,1,0,0,0]
          and all(s['element_flag']==1<<s['mana_type'] for s in job_tests), samples=job_tests)
    # The two editorial records have zero iParam0/param3/iParam1/param7.
    # Execute those sibling-line skips rather than inferring neutrality from text.
    uc=machine(0x158c000);uc.reg_write(U.UC_ARM64_REG_W24,0);extra_calls=[]
    def zero_lines(u,a,s,d):
        ins=next(dis.disasm(native.raw[a:a+4],a))
        if ins.mnemonic=='bl':
            extra_calls.append(a)
            if a not in [0x158cbdc,0x158cbf8,0x158ccb4,0x158ce2c]:
                raise ValueError('unexpected consumer in zero sibling lines: '+hex(a))
            u.reg_write(U.UC_ARM64_REG_W0,0);u.reg_write(U.UC_ARM64_REG_Q0,0)
            u.reg_write(U.UC_ARM64_REG_PC,a+4)
    uc.hook_add(UC_HOOK_CODE,zero_lines);uc.emu_start(0x158cbd4,0x158cf48,count=200)
    check('reviewed_pair_zero_sibling_lines',uc.reg_read(U.UC_ARM64_REG_PC)==0x158cf48,
          calls=[hex(a) for a in extra_calls],input_fields='iParam0=param1=param2=param3=iParam1=param4=param7=0')
    # Full bounded slices are retained so reviewers can inspect checks' context.
    ranges=[(0x157669c,0x15766b0),(0x1117a80,0x1117b10),(0x1117bf4,0x1117c34),
            (0x158c330,0x158c3e4),(0x158c600,0x158c62c),(0x158c9e0,0x158cbd4),
            (0x158cbd4,0x158ce2c),(0x158ce2c,0x158cf48),(0x1244280,0x1244298)]
    slices=[dict(start=hex(lo),end=hex(hi),bytes_sha256=hashlib.sha256(native.raw[lo:hi]).hexdigest(),
                 instructions=[dict(rva=hex(i.address),op=i.mnemonic+' '+i.op_str) for i in dis.disasm(native.raw[lo:hi],lo)])
            for lo,hi in ranges]
    return dict(generated_by='scripts/character_skills/type26_mana.py',
                evidence_kind='CONTROLLED_NATIVE_FRAGMENT',native_sha256=hashlib.sha256(native.raw).hexdigest(),
                metadata_sha256=hashlib.sha256(md.raw).hexdigest(),checks=checks,
                passed=sum(c['passed'] for c in checks),total=len(checks),slices=slices,
                condition=CONDITION,limits=LIMITS,
                caveat='调用与系统初始化作stub；仅执行列出的原生片段，不是完整战斗或实机验证；旗标缓存字段保存AbilityType2FlagIndex(26)，其数值未假定等于26')


def rule_rows(native, md):
    ev=native_evidence(native,md)
    if ev['passed']!=ev['total']:
        raise ValueError('type26 param0 native evidence failed')
    return [dict(file_table='skilllist.ability26',table='skilllist',effect_type=26,field_path='/param0',
                 meaning_zh=KIND,unit=UNIT,rule='float32(param0) → fcvtzs int32（+inf显式置INT_MIN）；n>=1时ProduceManaForce调用n次，否则本产线0次；职业取持有者_jobType',
                 status='已确认数值换算；类型级规则，不新增逐记录字段评审',condition=CONDITION,
                 evidence=['output/character_skills/type26_mana/native_evidence.json',
                           'scripts/character_skills/type26_mana.py','PlayerManager.subPartyAbilityInit_ManaGet 0x158cb1c..0x158cbd4'])]


def main():
    C.enable_utf8_console()
    md=Metadata(C.ROOT/'work/protection/metadata_aei_decoded.bin');native=Native(md)
    evidence=native_evidence(native,md)
    C.write_json(OUT/'native_evidence.json',evidence)
    if evidence['passed']!=evidence['total']:raise SystemExit('native checks failed')
    rows=rule_rows(native,md)
    C.write_json(OUT/'field_dictionary.json',rows)
    # Preserve old generated rules verbatim; the main skilllist generator also calls rule_rows.
    path=C.ROOT/'output/character_skills/skilllist_types/field_dictionary.json'
    old=C.load_json(path);keys={(r['table'],r['effect_type'],r['field_path']) for r in old}
    for r in rows:
        key=(r['table'],r['effect_type'],r['field_path'])
        if key not in keys:
            old.append(r)
        else:
            idx=next(i for i,v in enumerate(old) if (v['table'],v['effect_type'],v['field_path'])==key)
            if 'scripts/character_skills/type26_mana.py' not in old[idx].get('evidence',[]):
                raise ValueError('type26 param0 rule belongs to another source; refusing overwrite')
            old[idx]=r
    C.write_json(path,old)
    sources=[]
    for layer,records in [('APK',C.apk_rows('skilllist')),('CACHE',C.cache_rows('skilllist'))]:
        rr=[r for r in records if r.get('ability')==26]
        sources.append(dict(layer=layer,records=len(rr),param0_present=sum('param0'in r for r in rr),
            param0_missing=sum('param0'not in r for r in rr),param0_null=sum('param0'in r and r['param0'] is None for r in rr),
            param0_distribution=dict(collections.Counter(str(r.get('param0','MISSING')) for r in rr))))
    C.write_json(OUT/'source_inventory.json',dict(snapshot=C.SNAPSHOT_ID,sources=sources,
        scope='普通skilllist type26；CACHE按ID优先，APK仅缺ID回退，不逐字段补缺；缓存111条缺param0仍未知'))
    print(json.dumps(dict(native_checks=f"{evidence['passed']}/{evidence['total']}",rules=len(rows)),ensure_ascii=False))


if __name__=='__main__':main()
