"""Associate one real cached card and ability, preserving all unknown fields."""
import argparse
import hashlib
import json
from pathlib import Path


def attach_code_evidence(result):
    """Promote only when the matching recovered-image evidence is available."""
    path = Path('output/il2cpp/sample_code.json')
    checks_path = Path('output/validation/high_hp_sample.json')
    if not path.exists() or not checks_path.exists():
        return False
    code = json.loads(path.read_text(encoding='utf-8'))
    checks = json.loads(checks_path.read_text(encoding='utf-8'))
    native_hash = hashlib.sha256(Path('work/protection/il2cpp_loader_seed1.bin').read_bytes()).hexdigest()
    metadata_hash = hashlib.sha256(Path('work/protection/metadata_aei_decoded.bin').read_bytes()).hexdigest()
    if code['native_image_sha256']!=native_hash or checks['native_image_sha256']!=native_hash or code['metadata_sha256']!=metadata_hash:
        raise ValueError('Code evidence differs from current recovered inputs')
    if checks['status']!='PASS' or code['enums']['ABILITY_TYPE']['HighHPAll']['value']!=result['effect_code_raw']:
        raise ValueError('Effect/code boundary evidence failed')
    meanings = {'param0':'HP ratio threshold, inclusive; 0.25 means 25%',
                'param1':'Attack contribution multiplied into this effect accumulator; 1.15 is nominal +15%',
                'param2':'Movement contribution multiplied into this effect accumulator; 1.15 is nominal +15%',
                'param3':'Defence contribution multiplied into this effect accumulator; 1 is neutral',
                'param5':'Critical damage contribution added into this effect accumulator; raw +0.15'}
    for row in result['interpretations']:
        field = row['field']
        row.update({'status':'CONFIRMED_STATIC_AND_BOUNDED_NATIVE','meaning':meanings[field],
                    'evidence':'ability enum1105; PlayerManager.subAbilityApply_HighHPAll@0x159321c; typed apply switch/getters and 32 native boundary checks; output/il2cpp/sample_code.json',
                    'limit':'Confirmed for this effect accumulator. Input membership and float getter supplied in experiment; live eligibility, engine value icall and final battle damage not executed'})
    result['native_code_provenance'] = {'report':str(path),'boundary_checks':str(checks_path),
                                       'native_image_sha256':native_hash,'metadata_sha256':metadata_hash,
                                       'effect_enum_name':'ABILITY_TYPE.HighHPAll','handler_rva':'0x159321c'}
    result['confirmed'].append('Recovered native effect handler confirms inclusive HP threshold and parameter-specific multiply/add operations')
    result['unknown'][0] = 'Live skill eligibility/subskill installation, engine ParamS_float icall and final damage formula'
    return True


def skip_space(text, pos):
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos


def attach_phase_d_evidence(result, required=False):
    paths = [Path('output/phase_d/chain_probe.json'), Path('output/phase_d/source_rule_36000358.json')]
    if not any(p.exists() for p in paths) and not required:
        return False
    if not all(p.exists() for p in paths) or 'native_code_provenance' not in result:
        raise ValueError('Phase D delivery requires both reports and matching code evidence')
    chain, rule = [json.loads(p.read_text(encoding='utf-8')) for p in paths]
    native_hash = result['native_code_provenance']['native_image_sha256']
    if any(r['native_image_sha256']!=native_hash for r in (chain,rule)):
        raise ValueError('Phase D reports belong to another recovered image')
    if chain['status']!='PASS' or len(chain['cases'])!=11 or any(c['status']!='PASS' for c in chain['cases']):
        raise ValueError('Phase D chain checks incomplete')
    if chain['absent_root']['installed_ids'] or chain['absent_root']['selected_ids']:
        raise ValueError('Absent root incorrectly installed')
    for key in ('card_raw','skill_raw','subskills_raw'):
        if chain['source_sample'][key]!=result[key]:
            raise ValueError(f'Stale phase D source sample: {key}')
    for key,location in chain['source_sample']['record_locations'].items():
        if result['record_locations'][key]!=location:
            raise ValueError('Phase D record location differs')
    for source in rule['source_records'].values():
        raw = Path(source['file']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=source['file_sha256']:
            raise ValueError('Source conflict evidence stale')
        record,location = locate_record(raw,'skilllist',source['location']['ordinal_zero_based'])
        if record!=source['record'] or location!=source['location']:
            raise ValueError('Source conflict record/location differs')
    if len(rule['cases'])!=4 or any(c['status']!='PASS' for c in rule['cases']) or rule['actual_current_device_value']['value'] is not None:
        raise ValueError('Source rule checks incomplete or current value promoted without device evidence')
    result['phase_d'] = {
        'status':'CONDITIONAL_ASSOCIATION_CONFIRMED', 'chain_report':str(paths[0]),
        'evidence_level':chain['evidence_level'], 'controlled_case_count':12,
        'native_scope':chain['native_scope'], 'models':chain['models'], 'limits':chain['limits'],
        'installation':{'input':'CardInfo.skillid; scenario input, not current player observation',
                        'entry_rva':'0x10f9648','root_selection_slice':['0x10fb1b0','0x10fb288'],
                        'sub_expansion_rva':'0x10f8368','filter_rva':'0x10ff968','eligibility_rva':'0x1112574',
                        'selected_ids':[40232705,40232706]},
        'actor_roles':{'status':'STATIC_AND_CONTROLLED_NATIVE','hp_threshold_actor':'recipient',
                       'skill_list_actor':'provider','both_must_be_alive':True,
                       'outer_provider_guard':'STATIC: PLAYER list and active provider in this attack-stat path',
                       'self_excluded':False,'attack_target_hp_used_in_threshold':False},
        'tier_accumulation':{'status':'CONDITIONAL_NATIVE_LOCAL_ATTACK_ONLY',
                             'receiver_hp_at_least':0.5,'raw_multipliers':[1.15,1.05],
                             'float32_contribution':chain['cases'][3]['attack_contribution_float32'],
                             'current_live_or_final_multiplier':None},
        'unknowns':chain['unknowns'],
        'code_report':'output/phase_d/cid2327_关联链与来源规则.md'}
    result['source_resolution'] = {'report':str(paths[1]),'skill_id':36000358,
                                   'source_records':rule['source_records'],'native_rule':rule['native_rule'],
                                   'actual_current_device_value':rule['actual_current_device_value'],
                                   'evidence_level':'STATIC_AND_BOUNDED_NATIVE','limits':rule['limits']}
    result['external_references'] = []
    reference = Path('output/phase_d/external_reference/cid2327_database_20261015.json')
    if reference.exists():
        external = json.loads(reference.read_text(encoding='utf-8'))
        original = external['source']
        if hashlib.sha256(Path(original['retained_file']).read_bytes()).hexdigest()!=original['sha256']:
            raise ValueError('External screenshot differs from retained evidence')
        result['external_references'].append({'report':str(reference),'evidence_level':external['evidence_level'],
                                              'identity':external['identity'],'not_established':external['not_established']})
    for row in result['interpretations']:
        row['limit'] = 'Local handler semantics only; installation/filtering now demonstrated with explicit models, not current player state, engine icall or final battle damage'
        if row['field']=='param0':
            row['meaning'] = 'Recipient HP ratio threshold, inclusive; provider must remain alive'
    result['confirmed'].append('Conditional ordinary-player install -> sub expansion -> native eligibility/filter -> HighHPAll chain; both tiers can accumulate locally')
    result['unknown'] = ['Current owned CardInfo.skillid, required level/unlock quest and current activation',
                         'Current accepted JSON master version; current skill36000358 param1 remains unknown',
                         'Engine ParamS scalar icall and full final battle damage/multiplier',
                         'Other subeffect parameter semantics and active skill following heal/buff stages',
                         'Complete live-game coverage; collected snapshots only']
    return True


def locate_record(raw, key, ordinal):
    """Return exact UTF-8 byte span of a top-level array member."""
    text, decoder = raw.decode("utf-8"), json.JSONDecoder()
    pos = skip_space(text, 0)
    if text[pos] != "{":
        raise ValueError("Expected JSON object")
    pos += 1
    while True:
        pos = skip_space(text, pos)
        field, pos = decoder.raw_decode(text, pos)
        pos = skip_space(text, pos)
        if text[pos] != ":":
            raise ValueError("Missing object colon")
        pos = skip_space(text, pos+1)
        if field == key:
            if text[pos] != "[":
                raise ValueError("Expected selected array")
            pos += 1
            for index in range(ordinal+1):
                pos = skip_space(text, pos)
                begin = pos
                value, pos = decoder.raw_decode(text, pos)
                if index == ordinal:
                    byte_begin = len(text[:begin].encode("utf-8"))
                    byte_end = len(text[:pos].encode("utf-8"))
                    if json.loads(raw[byte_begin:byte_end]) != value:
                        raise ValueError("Record byte span mismatch")
                    return value, {"json_pointer": f"/{key}/{ordinal}","ordinal_zero_based": ordinal,
                                   "byte_begin": byte_begin,"byte_end_exclusive": byte_end,
                                   "raw_record_sha256": hashlib.sha256(raw[byte_begin:byte_end]).hexdigest()}
                pos = skip_space(text, pos)
                if text[pos] != ",":
                    raise ValueError("Selected array ordinal exceeds boundary")
                pos += 1
        _, pos = decoder.raw_decode(text, pos)
        pos = skip_space(text, pos)
        if text[pos] == "}":
            raise ValueError("Array field not found")
        if text[pos] != ",":
            raise ValueError("Invalid object separator")
        pos += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-phase-d',action='store_true')
    args = parser.parse_args()
    directory = Path("output/decoded")
    card_raw = (directory/"charainfo.data5.json.raw").read_bytes()
    skill_raw = (directory/"skilllist.data5.json.raw").read_bytes()
    cards = json.loads(card_raw)["charainfo"]
    skills = json.loads(skill_raw)["skilllist"]
    evidence = {}

    def selected(rows, raw, array_key, id_key, identifier):
        matches = [i for i,row in enumerate(rows) if row.get(id_key) == identifier]
        if len(matches) != 1:
            raise ValueError(f"{id_key}={identifier} is not unique")
        record, location = locate_record(raw, array_key, matches[0])
        evidence[str(identifier)] = location
        return record

    card = selected(cards,card_raw,"charainfo","cid",2327)
    root = selected(skills,skill_raw,"skilllist","skillid",40232705)
    if root["skillid"] not in card["skillid"]:
        raise ValueError("Missing explicit card skill reference")
    children = [selected(skills,skill_raw,"skilllist","skillid",sid) for sid in root["sub"]]
    cross = [selected(skills,skill_raw,"skilllist","skillid",sid) for sid in (143001,143002)]
    assert root["ability"] == children[0]["ability"] == cross[0]["ability"] == cross[1]["ability"] == 1105
    assert (root["param0"],children[0]["param0"]) == (0.25,0.5)
    assert (cross[0]["param0"],cross[0]["param1"],cross[1]["param0"],cross[1]["param1"]) == (0.25,1.05,0.5,1.025)
    assert "25%" in root["text"] and "50%" in root["text"]
    assert "25%" in cross[0]["text"] and "(5%)" in cross[0]["text"]
    assert "50%" in cross[1]["text"] and "(2.5%)" in cross[1]["text"]
    report = json.loads((directory/"report.json").read_text())
    sources = {Path(row["source"]).name:row for row in report["files"]}
    collection = json.loads(Path("output/phone/collected_files.json").read_text())
    original_sources = [row for row in collection if Path(row.get("local","")).name in ("charainfo.data5","skilllist.data5")]
    for original in original_sources:
        name = Path(original["local"]).name
        if hashlib.sha256(Path(original["local"]).read_bytes()).hexdigest() != sources[name]["source_sha256"]:
            raise ValueError("Collected original/work input differs")
    interpretations = [
        {"field":"param0","raw":0.25,"status":"INFERRED","meaning":"HP threshold ratio 0.25, corresponding to HP >=25%",
         "evidence":"Root local text explicitly says HP25%; same ability1105 records143001/143002 pair0.25/0.5 with25%/50%; linked40232706 uses0.5 for second threshold",
         "limit":"Actual numeric comparison implementation and threshold rounding not recovered"},
        {"field":"param1","raw":1.15,"status":"INFERRED","meaning":"Attack multiplier1.15, nominal attack increase15%",
         "evidence":"Same ability1105 record143001 hasparam1=1.05 and local text attack(5%);143002 has1.025 andattack(2.5%). Root text confirms attack increase",
         "limit":"Battle damage formula, stacking with sub40232706 or other buffs not confirmed"},
        {"field":"param2","raw":root["param2"],"status":"UNKNOWN"},
        {"field":"param3","raw":root["param3"],"status":"UNKNOWN"},
        {"field":"param5","raw":root["param5"],"status":"UNKNOWN"}]
    result = {"status":"ONE_REAL_CARD_ABILITY_CHAIN","card_id":2327,"skill_id":40232705,"effect_code_raw":1105,
              "card_raw":card,"skill_raw":root,"subskills_raw":children,"interpretation_cross_records_raw":cross,
              "record_locations":evidence,"input_provenance":original_sources,
              "decode_provenance":{name:sources[name] for name in ("charainfo.data5","skilllist.data5")},
              "confirmed":["Real card cid2327 and name/title from integrity-checked decrypted JSON",
                           "card.skillid[2]=40232705 explicitly matches skilllist.skillid",
                           "ability=1105 and all four sub links are present and uniquely resolved",
                           "Local skill description: allies withHP>=25% gain attack/movement/critical power,HP>=50% strengthens effect"],
              "interpretations":interpretations,
              "unknown":["Effect-code enum/class name; exact execution formula","Slot-role implementation and active skill116 handler",
                         "Mana/other subeffect parameter semantics; no aggregate bonus calculated",
                         "Complete live game coverage and uncollected base tables"],
              "coverage":{"card_records":len(cards),"skill_records":len(skills),"complete_sample_chains":1}}
    has_code = attach_code_evidence(result)
    active_path = Path('output/sample/active_skill_trace.json')
    if active_path.exists():
        active = json.loads(active_path.read_text(encoding='utf-8'))
        if active['card_id']!=card['cid']:
            raise ValueError('Active trace belongs to another card')
        result['active_trace_artifact'] = str(active_path)
        result['unknown'][1] = 'Active following heal/buff stages and full live-game execution not confirmed'
    if Path('output/base_master/report.json').exists():
        result['unknown'][-1] = 'Complete live game coverage and APK/cache runtime override priority not confirmed; APK base tables exported separately'
    has_phase_d = attach_phase_d_evidence(result,args.require_phase_d)
    output = Path("output/sample")
    output.mkdir(parents=True,exist_ok=True)
    (output/"sample.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    location_lines = "\n".join(f"| {identifier} | {row['json_pointer']} | {row['byte_begin']}–{row['byte_end_exclusive']} |" for identifier,row in evidence.items())
    text = f"""# 单卡技能证据链

本轮实测样本：**エレミア／すこやかなるメイド，cid=2327**；能力技能 `40232705`「メイド・オブ・ザ・ユグド」，效果代码原值 `1105`。这是能力技能样本；卡牌自带必杀 `116` 的执行逻辑没有据此恢复。

## 原文件到记录

原始手机文件与工作副本一致；SHA-256 见 sample.json。`libChronicleNUtils.so::loadFile@0x22f1c` 的实际文件名派生 key/IV 与 AES 入口 `0x2e10c` 成功解开两文件，原生包头边界及全部 20 字节 SHA-1 均通过。

初始化来源由本地代码追得：JNI `init_body@0x1ec6c` → `PackageInfo.signatures[0]` → `Signature.toCharsString()` → JNI GetStringUTFChars/GetStringLength → `initializeNative@0x1c9f0`。本 APK v2 证书 879 字节，其小写 hex 共 1758 字符，生成校验值 `0x8bf8c20d`，等于代码内常量。这里使用 APK 自身证书，不使用网上游戏数值。

密文整个文件 → 原生 `c_AES__DecryptN_CSTM@0x2e10c` 结果 → `[36,36+payload_length)` 的 SHA-1 校验负载 → 保留负载前 6 字节 → 从偏移 6 开始 gzip → UTF-8 JSON。gzip 在转换结果偏移 42；压缩流使单条记录与密文偏移不能简单一一对应。这个原生 CSTM 模式没有直接称为标准 CBC。

下表是**解压后原始 JSON 的 UTF-8 字节区间，右端不包含**；每个切片都独立解析并与相应记录相等。

| 标识 | JSON pointer | 字节区间 |
|---|---|---|
{location_lines}

`/charainfo` 来自 charainfo.data5；其余 `/skilllist` 来自 skilllist.data5。原始解压字节保存在 output/decoded/*.json.raw；格式化 JSON 不用于计算这些偏移。

## 标识、效果、参数

已确认：卡牌记录 `skillid[2]=40232705` 与技能表标识完全一致；技能 `ability=1105`，`sub=[40232706,40232707,40232708,40232709]` 四条均存在且唯一。原始卡、技能及所有子技能字段完整保存在 sample.json。

同一原始技能描述明确说：HP 25%以上的队友攻击力、移动速度、暴击威力提升；HP 50%以上时进一步增强。

| 字段 | 原值 | 判断 | 解释依据 |
|---|---:|---|---|
| param0 | 0.25 | 推断：HP 阈值比率 25% | 本技能文本；同效果1105的143001/143002分别以0.25/0.5对应25%/50% |
| param1 | 1.15 | 推断：攻击乘数1.15，名义增加15% | 143001的1.05对应本地文本攻击5%；143002的1.025对应2.5% |
| param2 | 1.15 | 未知 | 原值保留 |
| param3 | 1 | 未知 | 原值保留 |
| param5 | 0.15 | 未知 | 原值保留 |

子技能40232706同为效果1105，param0=0.5、param1=1.05；可作为第二档阈值线索。**未确定叠加算法，不把两个攻击参数合成总倍率，不把攻击乘数直接等同最终伤害倍率。** 数值解释依据全部来自本次本地数据；它们仍是推断，执行代码、边界舍入和实机表现未确认。

## 重跑和范围

```powershell
& .\\.venv\\Scripts\\python.exe scripts/signal_region_probe.py --loader-probe
& .\\.venv\\Scripts\\python.exe scripts/decode_data5.py
& .\\.venv\\Scripts\\python.exe scripts/sample_trace.py
# 本轮两种子验证的第二份镜像；日常只解码可省略
& .\\.venv\\Scripts\\python.exe scripts/signal_region_probe.py --seed 2 --loader-probe
& .\\.venv\\Scripts\\python.exe scripts/verify_data5.py
```

保护库恢复使用受控 CPU 仿真及明确的候选 key 指针；不是正常 Android 启动观测。两个种子恢复 NUtils 镜像完全一致。NUtils 在库链接后段停止，但本次使用的初始化、派生、AES 函数已恢复，11 个输入均以原生包头/SHA-1/gzip CRC 验证对应关系。

本快照可解析卡牌记录 {len(cards)}、技能记录 {len(skills)}，不代表全游戏覆盖。这里只确认一个完整能力技能样本链；其余字段、必杀路径及批量语义归属仍需逐步研究。
"""
    if has_code:
        table_begin = text.index('| 字段 | 原值 | 判断 | 解释依据 |')
        table_end = text.index('## 重跑和范围',table_begin)
        text = text[:table_begin]+'''| 字段 | 原值 | 判断 | 代码依据 |
|---|---:|---|---|
| param0 | 0.25 | 已确认：HP 比率门槛，相等时生效 | get_hpRate → fcmp → b.mi；阈值相邻 float32 实验通过 |
| param1 | 1.15 | 已确认：攻击分支的乘算贡献，名义 +15% | Attack=0 → get_param1 → fmul；上层 GetAbilityAttack 继续乘算 |
| param2 | 1.15 | 已确认：移动分支的乘算贡献，名义 +15% | Move=1 → get_param2 → fmul |
| param3 | 1 | 已确认：防御分支的乘算贡献，本值中性 | Defence=2 → get_param3 → fmul |
| param5 | 0.15 | 已确认：暴击伤害分支的加算贡献 +0.15 | CriDmg=4 → get_param5 → fadd；不等同最终伤害 +15% |

确认层级是**静态代码与限定原生实验**。效果枚举 `ABILITY_TYPE.HighHPAll=1105` 来自本 APK 解码元数据，字段默认值偏移 5618419、原字节 `88a2`。方法 token `0x060022b7` 通过本库方法指针数组定位至 `0x159321c`，不是仅凭字符串猜测。

技能 JSON 初始化代码的实际字符串引用为 param0..param5，写入字段偏移与 get_param0..get_param5 的读取一致。HP 比率函数读取 `_hp` 与 `_invhpMax` 相乘并钳制到 [0,1]；参数读取仍调用受保护的 ParamS_float 引擎入口，该入口没有在本实验里恢复。

子技能 40232706 同为效果1105，param0=0.5、param1=1.05。实际循环对列表中满足 HP 条件的条目逐项乘算攻击/移动/防御、加算暴击率/暴击伤害。32 项边界实验提供这两条记录作为筛选后列表，运行原生比较、switch 和循环；不声称游戏当前一定把两条都装入列表，亦不输出最终战斗总倍率。param4 在这两条记录中缺失，未补成默认值。

详细证据：[处理器与参数报告](../il2cpp/sample_code.json)、[限定边界实验](../validation/high_hp_sample.json)。其他子效果、必杀后续治疗与增益、实机生效优先级及最终伤害公式仍未知。

'''+text[table_end:]
        text = text.replace('必杀 `116` 的执行逻辑没有据此恢复。','必杀类型 `116` 的进一步追踪见 active_skill_trace.json，不能把它当作 skilllist 中缺失的技能记录。')
    if has_phase_d:
        begin = text.index('子技能 40232706 同为效果1105')
        end = text.index('## 重跑和范围',begin)
        text = text[:begin]+'''## 阶段 D：安装、资格与作用对象

普通队员 CreatePlayer@0x10f9648 读取 **玩家实例 CardInfo.skillid**，查到非零 ability 后安装；它不同于卡牌主表的定义数组。addSubAbility@0x10f8368 保留根40232705并展开一层sub；实际筛选 GetAbilityListOnFlagIndex@0x10ff968 调用 IsEnableAbility@0x1112574，两条1105记录均留下。该安装循环和1105资格分支没有额外等级/任务比较；实例列表和上游解锁条件仍未知，不能据此宣称从1级开放。

处理器使用 **接受者** 的HP比例判断25%/50%门槛；提供者及接受者均须存活。外层攻击属性路径从PLAYER列表选存活、active提供者（静态证据），接受者是正在计算属性的角色，不是被攻击目标。处理器不排除自身。

新增11项安装→展开→筛选→完整HighHPAll场景和1项根缺失负例通过。根安装、记录存在且满足资格时，接受者HP≥50%可让两档连续参与局部攻击累积，float32结果约1.20749986。**不是当前实机生效或最终战斗倍率。** 先前32项实验仅针对给定列表的局部边界；新实验执行真实安装片段、展开、资格与筛选，但场景实例列表、集合/元数据及引擎标量getter仍有明确模型；未执行整个CreatePlayer和外层PlayerManager。

param4原记录保持缺失。构造器float0初始化是独立代码依据，受控读取标为NATIVE_CTOR_DEFAULT，不补写原值、不冒充实机引擎读取。

## 来源规则与外部参考

技能36000358分别保留缓存param1=400、APK=300.0及两份定位。实际daSkill.get先查JSON整条ID，缺ID才回退APK，无逐字段合并。4项分支实验通过；**当前装载JSON版本和当前生效值仍未知**，不按时间或“缓存”名称选值。

用户提供的CC数据库截图单列为EXTERNAL_REFERENCE。名称、25%/50%及15%/5%标签吻合；未提供原始测量、解锁条件或当前玩家实例，不用于覆盖解包原值。

标准样本JSON现已包含phase_d、source_resolution、external_references；源记录、缺失字段和精确字节定位仍完整保留。详情：[关联链与来源规则](../phase_d/cid2327_关联链与来源规则.md)、[安装关联实验](../phase_d/chain_probe.json)、[来源规则实验](../phase_d/source_rule_36000358.json)、[外部参考对照](../phase_d/external_reference/cid2327_database_20261015.md)。其他效果及必杀后续段未在本轮扩展。

'''+text[end:]
        begin = text.index('```powershell',text.index('## 重跑和范围'))
        end = text.index('```',begin+3)+3
        text = text[:begin]+'''```powershell
$env:PYTHONIOENCODING='utf-8'
# 已有解码、代码及D证据时，仅更新标准交付
& .\\.venv\\Scripts\\python.exe scripts/sample_trace.py --require-phase-d
# 重新实验后更新交付（无需重做A/B/C）
& .\\.venv\\Scripts\\python.exe scripts/phase_d_chain_probe.py
& .\\.venv\\Scripts\\python.exe scripts/phase_d_source_rule.py
& .\\.venv\\Scripts\\python.exe scripts/sample_trace.py --require-phase-d
```'''+text[end:]
    (output/"sample_trace.md").write_text(text,encoding="utf-8")
    print(json.dumps(result["coverage"]))


if __name__ == "__main__":
    main()
