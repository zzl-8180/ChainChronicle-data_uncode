"""模板作用域推断层——批 10：SA_PowerDrain（ability2003）载体解析（批 9 C1 遗留闭合）。

设计与范围依据：``output/character_skills/inference_inventory/b10_sa2003_scope.md``
（批 10 前置审计；逐行明细 work/character_skills_b10_sa2003/c1_promotion.json、
代表样本 b10_samples.json）。对象＝批 9 审查遗留 **431 行 C1 hint**
（C1-carrier-2003：载体 2003（SA_PowerDrain）形状与 ability99 同构、批 9 时无规则）。
批 10 已在 rules.py 2003 注册处登记 5 条规则（skilllist|2003|/param0|/param3|/param7|
/param8|/param9；样本域＝当前 v3 CACHE 普通 skilllist ability==2003 全部 265 条，
occurrences 265/265/265/258/263）。

执行侧结论（scope §2，本轮实施复用、未重跑）：2003 是独立处理器
``AttackEffectCtrl.ExecSA_PowerDrain``@0x1037a08（方法 3373），与 99 的
``OnAttackAbilityPowerDrain``@0x1121be0 **不同函数**；但目标侧数据路径与 99 同一：
param7/8/9→TimePowerUpData(_attack/_move/_defense)→setSupport2（multiCheck=true、
时间 param0），Support2 聚合/倒计时链共用（复用 99/timed_support 既有证据）。
**触发差异（与 99 三路不同，逐行披露）**：仅 damageType==1（Skill）读 param3×
Random.Range 门；Normal/Critical 阈值恒 0 永不触发；param3 全 265 条=1 → 当前域内
实为 Skill 着弹即触发。受控原生检查 8 项全过（native_checks.json）。

行集与门（scope §4，批 9 §5.1 骨架复用但表/类型/载体独立；431 行逐行审核＋批 9
C3 六行 multi-carrier 亦归本批披露）：

* **P1 句面**（批 9 同法）：行 japanese 含「敵」＋下降谓词＋攻/防/移属性；
  「敵から受ける」我方被击句不在本批；敵減益半句（首个下降谓词句段）须同时含「敵」
  与 ≥1 属性名（30338 防线镜像门：我方半句不挂敌方减益值）；
* **链（表独立）**：行记录∈bosspattern/denju/dlb/charainfo；载体＝own children 中
  link_kind=``boss_skill.s_ability`` 的 skilllist ability==2003 记录（批 9 §3.1 审计
  同法；**sub_effect 链不消费**——B1 防线：pattern 行 sub_effect children 含 profiles
  装配 ID 碰撞伪影，99 的 34 行 C1 行内 99 亦为伪影、批 9 已披露不消费）；
  charainfo 行经同页同文 bosspattern 行（G5 同法：同文 pattern 须唯一）；
  行 s_ability 链上若另有 ability99 → 返回 None（99 家族归批 9，防跨批混用样本域）；
* **P3 载体唯一**：恰 1 个（≥2 → hint:multi-carrier，批 9 C3 同法；审计实测 6 行）；
* **P2 样本域**：载体∈当前 v3 CACHE 普通 ability2003 的 265 条；APK 148 条载体经批 13
  扩域（rules.json 五键两域分源＋occurrences_apk）委托
  card_page_inference_b13_apkext.handle_2003_apk 按载体层域接管（晋级键 inference_b13
  或 hint；本批旧域外 hint 口径仅对扩域前有效）；
* **P4 形状（双向）**：敵減益半句属性 ⇔ 载体 p7/p8/p9 活性（缺槽=缺失不补 0）；
* **P5 方向（代码语义）**：p7/p8≤0（负值加算=下降）、p9≥0（受伤量加算=「防御力
  下がる」的表现层口径，不是固定防御减少）；例外 47000844 p7=+1 方向冲突门兜底
  （当前 431 行不含该载体）；
* **P6 跨 cid 载体竞争守卫**（进程内登记；审计实测 0 例）。

值行（rule_key 只允许 ``skilllist|2003|/param0|/param7|/param8|/param9``；经 rules.py
2003 换算器出值）：攻撃力→/param7、移動速度→/param8、防御力→/param9（1:1）；
「一定時間」＋载体 p0>0 → /param0 时长值行（游戏秒）；p0=-1=无正计时标记不出值行。
载体 param3 无句面槽（触发条件逐行披露入 note，不出值行）；param4/5/6（自身侧提交，
复合句自身半句）**未登记换算，登记原值不分配**（scope §3）。

硬边界（沿用批 9 §5.2 口径）：

* 只升「推断」：值行 numeric/association 一律「推断」；行级标注
  「推断（模板批 10 SA2003）」、evidence_scope=TEMPLATE_BATCH10_SA2003、行级 metadata
  键 ``inference_b10``；不进整行确认；「唯一 s_ability→2003 载体＋形状匹配」是数据侧
  结构对应，永不升「确认」。
* **规则本体与本条归属分开披露**：值行 note 固定写明「规则本体：已确认（静态及受控
  原生局部规则）——指规则本身；本条数值归属＝推断（模板批 10），不升确认」。
* **证据按字段**（INFR-01）：值行 evidence 取 rules.json skilllist|2003|/paramN 的
  evidence——output/ordinary_effects/ability2003/（本轮新增三件＋反汇编片段）＋复用
  output/card_comparison_cid30236/timed_support/ 与 output/ordinary_effects/ability99/；
  存在性检查，缺失显式失败。
* **样本域披露按登记口径**（INFR-02）：occurrences 265/265/265/258/263 以键级汇总在行级
  披露一次（含触发阈值 /param3 的 265；批 10 定向审查 B10-RV-03/-04 后口径）；
  载体记录未逐条核对，不属逐记录确认。
* **30338 防线与 99 混淆防线**：我方半句不挂敌方减益值；2003 与 99 命名空间分清
  （2003 样本域 265 条、99 样本域 133 条互不混用；行侧 99 伪影不消费）。
* **不跨记录合并**：载体句外槽只登记原值不分配；既有批 1–9 晋级行与 hint 键不动
  （本批行是批 9 C1/C3 hint 行，批 9 对这些行的 hint 由本批接管/改写，其余批 hint 保留）。
"""
from __future__ import annotations

import json
import re

import rules as R
import card_page_inference_b6_bossbuff as B6
import card_page_inference_b8_crit2012 as B8
import card_page_inference_b9_debuff as B9

B10_TAG = '推断（模板批 10 SA2003）'
B10_SCOPE = 'TEMPLATE_BATCH10_SA2003'
_B10_FAMILY_LEAD = ('敵デバフ家族・ability2003 载体（批 9 C1 遗留：「攻撃した敵の⟨ATTR⟩が'
                    '（一定時間）下がる。」及同形变体；')
# 家族文案表感知（批 10 复验 B10-RV-06）：bosspattern/denju/dlb 行**逐字节保留**原家族
# 文案（含表清单，218 行零变化）；charainfo 记录 own children=0（records.jsonl/links
# 实测），链经同页同文 bosspattern（G5 唯一）→s_ability→载体，charainfo 行改用专用
# 文案、不再断言 own children。
B10_FAMILY = (_B10_FAMILY_LEAD +
              'bosspattern/denju/dlb/charainfo 行 own children→boss_skill.s_ability→'
              'skilllist ability2003 SA_PowerDrain 载体）')
B10_FAMILY_CHARAINFO = (_B10_FAMILY_LEAD +
                        'charainfo 记录无 own children；载体主张经同页同文 bosspattern'
                        '（G5 唯一）→s_ability→skilllist ability2003 SA_PowerDrain 载体）')


def family_for(table):
    """表感知家族文案（B10-RV-06）：charainfo 行用同页同文 pattern 中继口径。"""
    return B10_FAMILY_CHARAINFO if table == 'charainfo' else B10_FAMILY

# P2：行记录表（431 行 C1 的实表分布 bosspattern/denju/charainfo；dlb 防御性保留）。
TABLES = ('bosspattern', 'denju', 'denju_limit_break_info', 'charainfo')

ATTRS3 = B9.ATTRS3
SLOT_OF = B9.SLOT_OF

# ---- INFR-01：rules.json skilllist|2003|/paramN 的 evidence 解析（本批规则 evidence ----
# ---- 为仓库根相对路径；存在性检查，缺失显式失败） ----
_EVIDENCE_DIRS = ('output/ordinary_effects/ability2003/',
                  'output/card_comparison_cid30236/timed_support/',
                  'output/ordinary_effects/ability99/')
_EVIDENCE_CACHE = {}


def _field_evidence(param):
    if param in _EVIDENCE_CACHE:
        return _EVIDENCE_CACHE[param]
    rule = R.rule_for('skilllist', 2003, '/' + param)
    files = []
    for entry in (rule or {}).get('evidence') or []:
        items = entry if isinstance(entry, (list, tuple)) else [entry]
        for e in items:
            e = str(e)
            if not e.startswith(_EVIDENCE_DIRS):
                raise ValueError(f'批 10 证据解析异常（INFR-01）：skilllist|2003|/{param} 的 '
                                 f'rules.json evidence 条目 {e!r} 不在允许前缀 {_EVIDENCE_DIRS} 内')
            files.append(e)
    missing = [p for p in files if not B8.Path(p).is_file()]
    if missing:
        raise FileNotFoundError(f'批 10 证据文件缺失（INFR-01）：{missing}')
    _EVIDENCE_CACHE[param] = files
    return files


# ---- P2 样本域：当前 v3 CACHE 普通 ability2003 的 265 条记录 ----
def _domain2003(data):
    return {sid for sid, (i, rec) in data.cache_skill.items() if (rec or {}).get('ability') == 2003}


def _sample_domain_note(rule, param):
    return (f'该规则登记已核出现 {rule.get("occurrences")} 次（CACHE 存在数口径，批 13 未改）'
            f'＋occurrences_apk={rule.get("occurrences_apk")}（APK 存在数；origin '
            f'{rule.get("origin")}；样本域＝批 13 扩域后两域分源：①当前 v3 CACHE 普通 '
            'skilllist ability2003（SA_PowerDrain）的 265 条记录；②APK 主表 '
            'output/base_master/_mdSkill.json ability2003 的 148 条记录——命名空间不合并、'
            '5 个同号记录中 4 组为两域真实参数值分歧、1 组仅缺省/float32 表示差'
            '（逐组明细见 rules.json 九键 conditions；行侧载体按载体所在层取值不得跨层）；'
            '本行来源载体记录'
            '未逐条核对，按规则适用条件披露，不属逐记录确认')


def _sample_domain_summary():
    """行级适用范围披露：五键 occurrences＋occurrences_apk 键级汇总一次（含触发阈值 /param3）。

    批 10 定向审查 B10-RV-03/-04：行摘要不再按 claimed param 重复同一段样本域披露，
    改为键级汇总一次（p3 的 occurrence 亦在行级出现）。值行 note 内的逐参数
    _sample_domain_note 保留（该值行所用规则键的单键口径）。批 13 扩域后追加 APK
    侧存在数（occurrences_apk）与两域分源措辞。"""
    occ = '、'.join(
        f'/{p}={R.rule_for("skilllist", 2003, "/" + p).get("occurrences")}'
        f'+{R.rule_for("skilllist", 2003, "/" + p).get("occurrences_apk")}'
        for p in ('param0', 'param3', 'param7', 'param8', 'param9'))
    return ('（键级 occurrences（CACHE）＋occurrences_apk（APK）汇总披露一次，含触发阈值 '
            '/param3；origin rules.json 登记值）'
            f'：{occ}；样本域＝批 13 扩域后两域分源：①当前 v3 CACHE 普通 skilllist '
            'ability2003（SA_PowerDrain）的 265 条记录；②APK 主表 _mdSkill.json '
            'ability2003 的 148 条记录——命名空间不合并、不得跨层取值；本行来源载体记录'
            '未逐条核对，按规则适用条件披露，不属逐记录确认')


_TRIGGER_NOTE = ('触发条件（与 ability99 的 param1/param3/param2 三路不同，逐行披露）：'
                 '仅 Skill 型着弹（damageType==1）经 param3×Random.Range 门触发；'
                 '载体 /param3=1 → 当前域内实为 Skill 着弹即触发；Normal/Critical 永不触发'
                 '（output/ordinary_effects/ability2003/ 受控 type_gate_kind0/kind2 实测 0 提交）')

_NATIVE_TARGET = ('记录侧＝setSupport2 受击目标路径（ExecSA_PowerDrain@0x1037a08 两次提交：'
                  'param7/8/9→TimePowerUpData(_attack/_move/_defense)→setSupport2，'
                  'multiCheck=true、时间 param0；受控实测目标 attack=-0.3/move=-0.3/'
                  'incoming=+0.3 写入 status+0x230）——output/ordinary_effects/ability2003/ 口径；'
                  'Support2 聚合/倒计时链与 ability99 共用（复用既有证据，未重跑）')

def _b1_disclosure(table):
    """B1 防线披露（表感知，批 10 复验 B10-RV-06）：链口径按行表区分——charainfo 行
    不写 own children（该表 own children=0），写同页同文 bosspattern 中继口径。"""
    if table == 'charainfo':
        lead = '本批载体主张只认同页同文 bosspattern 的 s_ability 链'
    else:
        lead = ('本批载体主张只认行记录 own children 的 boss_skill.s_ability 链'
                '（批 9 §3.1 审计同法）')
    return ('B1 防线披露（30338 防线镜像门＋99 混淆防线）：' + lead + '；pattern 行 '
            'sub_effect children 含 profiles 装配的 ID 碰撞伪影（profiles.py:426-428）'
            '——不消费；行侧若见 ability99 亦为伪影（2003 与 99 命名空间分清：2003 '
            '样本域 265 条、99 样本域 133 条，互不混用）')


def _hint(table, reasons, subject=None, attrs=(), sent_no=None, sent_total=0, **extra):
    out = dict(kind='hint', reasons=reasons, subject=subject, attrs=list(attrs), table=table,
               sent_no=sent_no, sent_total=sent_total)
    out.update(extra)
    return out


def _shape_check(attrs, crec):
    """P4 形状（双向）：句面属性 ⇔ 载体 p7/p8/p9 活性。返回 (ok, 明细文案)。"""
    mism, parts = [], []
    for attr, slot in SLOT_OF.items():
        raw = crec.get(slot)
        act = B9._active(raw)
        claimed = attr in attrs
        if claimed and not act:
            mism.append(f'敵減益半句含{attr}但载体 /{slot} 不活性({raw!r})')
        if (not claimed) and act:
            mism.append(f'载体 /{slot} 活性({raw!r})但敵減益半句无{attr}')
        parts.append(f'{attr}↔/{slot}=' + (f'活性({raw!r})' if act else f'不活性({raw!r})'))
    return (not mism), ('；'.join(parts)), mism


def _direction_note(param, raw):
    if param == 'param7':
        return (f'方向一致（原值 {raw}<0：负值加算＝攻撃力下降贡献——直接写目标 _attack、'
                'Σ 汇总后 clamp(1+Σ)；加算池与增益同池，非乘数<1、非独立 debuff 槽；与句'
                '「下がる/下げる」方向一致）' if raw < 0 else
                f'方向冲突（原值 {raw}>0 与攻撃力下降冲突——加算正值为上升贡献；'
                '样本域方向例外 47000844 p7=+1 同类，须逐行冲突披露）')
    if param == 'param8':
        return (f'方向一致（原值 {raw}<0：负值加算＝移動速度下降贡献——直接写目标 _move、'
                'Σ 汇总后 clamp(1+Σ)；与句「下がる/下げる」方向一致）' if raw < 0 else
                f'方向冲突（原值 {raw}>0 与移動速度下降冲突——加算正值为上升贡献）')
    if param == 'param9':
        return (f'方向一致（原值 {raw}>0：受伤量倍率加算＝受击目标受伤量因子上升——正文写作'
                '「防御力下がる」的表现层口径（规则 conversion 原口径，不是固定防御减少）；'
                '加算池与增益同池，非独立负向槽）' if raw > 0 else
                f'方向冲突（原值 {raw}<0 与受伤量加算口径（防御下降的表现层）冲突）')
    return f'方向登记（原值 {raw!r}）'


def _p0_note(p0_raw, with_row):
    if isinstance(p0_raw, (int, float)) and not isinstance(p0_raw, bool) and p0_raw > 0:
        if with_row:
            return (f'载体 /param0={p0_raw}（支持计时输入，{p0_raw} 游戏秒，游戏 delta 扣减、'
                    '不乘 Chain；攻击者与受击目标两次提交共用计时；本行已出时长值行）；')
        return (f'载体 /param0={p0_raw}（支持计时输入，{p0_raw} 游戏秒——登记口径；'
                '句面无「一定時間」时长主张，不出时长值行）；')
    if p0_raw == -1:
        return ('载体 /param0=-1（无正计时标记（受控 minus1_time_cache 实测 -1 原样提交；'
                '登记口径），实际持续语义未核——不出时长值行）；')
    return f'载体 /param0={p0_raw!r}（缺失/非正值不补数，不出时长值行）；'


def _slots_note(crec, claimed_slots):
    """载体槽位登记：本句消费槽＋句外槽原值（不分配给本句，仅登记）。"""
    consumed, idle = [], []
    for key in sorted(crec):
        if not re.match(r'^(param|iParam|iparam|skillparam|flag|skillflag)\d', key):
            continue
        raw = crec.get(key)
        entry = f'/{key}={raw!r}'
        (consumed if key in claimed_slots else idle).append(entry)
    parts = ['载体槽位登记：本句消费 ' + '、'.join(consumed)]
    if idle:
        parts.append('句外槽未分配（不归属本句，仅登记原值；param0 为支持计时（本句时长值行'
                     '消费时另行列示）；param3 为 Skill 型触发阈值（载体恒 1，触发条件披露'
                     '于值行 note，不出值行）；param1/param2 全库无记录、param4/5/6 自身侧'
                     '提交未登记换算——复合句自身半句不属本批，登记不分配）：' + '、'.join(idle))
    return '；'.join(parts)


def _promote(frag, table, layer, record_id, cid, attrs, claims, subject_phrase, clause,
             carrier, sent_no, sent_total, competitors, self_half_slots, via_pattern=None):
    """晋级行：值行全部来自唯一 skilllist 2003 载体（p7/p8/p9＋p0）——批 9 _promote 骨架，
    表/类型/载体与触发披露独立。

    via_pattern：charainfo 行的实际中继（pid, player）——charainfo 记录 own children=0
    （records.jsonl/links 实测），链经同页同文 bosspattern 行→s_ability→载体；链文本须写
    实际中继 pattern id（批 10 审查 B10-RV-01），不得写「own children」。"""
    carrier_id, crec = carrier
    carrier_key = f'skilllist|{carrier_id}|CACHE'
    row_key = f'{table}|{record_id}|{layer}'
    if via_pattern:
        pid, player = via_pattern
        chain_desc = (f'charainfo|{record_id}|{layer} 经同页同文 bosspattern|{pid}|{player}'
                      f'→s_ability→{carrier_key}'
                      f'(ability2003,SA_PowerDrain"{(crec.get("name") or "")[:20]}")')
    else:
        chain_desc = (f'{row_key} own children→boss_skill.s_ability→{carrier_key}'
                      f'(ability2003,SA_PowerDrain"{(crec.get("name") or "")[:20]}")')
    numeric_source = f'模板推断（批 10 SA2003：{chain_desc}）'
    answers = []
    claimed_slots = []
    p0_raw = crec.get('param0')
    p0_row_due = bool('一定時間' in frag and isinstance(p0_raw, (int, float))
                      and not isinstance(p0_raw, bool) and p0_raw > 0)
    for attr in ATTRS3:
        if attr not in attrs:
            continue
        param = SLOT_OF[attr]
        claimed_slots.append(param)
        raw = crec.get(param)
        rule = R.rule_for('skilllist', 2003, '/' + param)
        converted = R.answer_for('skilllist', 2003, '/' + param, raw, crec)
        evidence_files = _field_evidence(param)
        if param == 'param7':
            unit_desc = '单位：攻击倍率加算增量（显示百分点；负值＝加算下降贡献，非乘数）'
        elif param == 'param8':
            unit_desc = '单位：速度因子加算增量（负值＝加算下降贡献；occurrences 258 样本域）'
        else:
            # 括注百分比与主值同一口径（:g 格式化；批 9 B9-R01 同法）。
            unit_desc = ('受伤量倍率 +{}（受伤量因子 {}；不是固定防御减少 {}%）——正文写作「防御」'
                         '的表现层口径'.format(raw, 1 + raw, f'{raw * 100:g}'))
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B10_SCOPE,
            rule_key=f'skilllist|2003|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_id, layer='CACHE',
                        record_key=carrier_key),
            note=(f'模板批 10 SA2003 值行（来源载体＝{carrier_key}，ability=2003；链：'
                  f'{chain_desc}）；句中敵減益半句「{clause}」的「{attr}」→/{param} 1:1 映射；'
                  f'规则键 skilllist|2003|/{param}；原值 {raw}；{unit_desc}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）；'
                  '本条数值归属＝推断（模板批 10：唯一 s_ability→2003 载体＋句面形状匹配为'
                  '数据侧结构对应，引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'方向审核：{_direction_note(param, raw)}；'
                  f'证据目录 output/ordinary_effects/ability2003/（受控原生检查 8 项，'
                  f'native_checks.json）；'
                  f'对象披露（双源）：句面依据「{subject_phrase}」逐字在句（对象=敌方，逐字）；'
                  f'{_NATIVE_TARGET}；'
                  f'条件逐字：句面「{frag}」；{_TRIGGER_NOTE}；'
                  f'{_p0_note(p0_raw, with_row=p0_row_due)}'
                  f'样本域：{_sample_domain_note(rule, param)}'),
            quantitative=True))
    # 时长值行（一定時間→/param0；p0>0 才出值行，-1/缺失按登记口径）
    if p0_row_due:
        param = 'param0'
        claimed_slots.append(param)
        rule = R.rule_for('skilllist', 2003, '/' + param)
        converted = R.answer_for('skilllist', 2003, '/' + param, p0_raw, crec)
        evidence_files = _field_evidence(param)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=p0_raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B10_SCOPE,
            rule_key='skilllist|2003|/param0',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_id, layer='CACHE',
                        record_key=carrier_key),
            note=(f'模板批 10 SA2003 时长值行（来源载体＝{carrier_key}，ability=2003；链：'
                  f'{chain_desc}）；句中「一定時間」→/param0 1:1 映射；规则键 '
                  f'skilllist|2003|/param0；原值 {p0_raw}；单位：游戏秒（支持计时输入，'
                  '游戏 delta 扣减、不乘 Chain；攻击者与受击目标两次提交共用计时）；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）；'
                  '本条数值归属＝推断（模板批 10：唯一 s_ability→2003 载体＋句面形状匹配为'
                  '数据侧结构对应，引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'证据目录 output/ordinary_effects/ability2003/（受控 minus1_time_cache 等'
                  f'8 项，native_checks.json）；'
                  f'条件逐字：句面「{frag}」；{_TRIGGER_NOTE}；'
                  f'样本域：{_sample_domain_note(rule, param)}'),
            quantitative=True))

    # --- 晋级行注记（不改变「推断」档位） --------------------------------------------------
    extra = []
    extra.append(_NATIVE_TARGET)
    extra.append(_TRIGGER_NOTE)
    # P2/P3 链口径表感知（批 10 复验 B10-RV-06）：charainfo 行链经同页同文 bosspattern，
    # 不写 own children。
    if table == 'charainfo':
        p23 = ('P2/P3：同页同文 bosspattern 的 s_ability 链恰 1 个 CACHE 层 '
               'ability2003 记录∈265 条样本域')
    else:
        p23 = ('P2/P3：own children 的 boss_skill.s_ability 链恰 1 个 CACHE 层 '
               'ability2003 记录∈265 条样本域')
    extra.append('跨记录归属依据（b10 scope §4）：句→2003 载体为数据侧结构对应：唯一 '
                 's_ability→2003 载体（' + p23 + '）＋敵減益半句属性↔载体活性槽'
                 '形状匹配（P4 双向）＋方向按符号（P5：p7/p8≤0 加算下降、p9≥0 受伤量加算）；'
                 '处理器/筛选/触发/提交侧为批 10 静态＋受控原生证据（8 项），但引擎侧行→载体'
                 '装载路径（本行运行时实际装载该载体）无原生核实，行保持推断——永不据此升「确认」')
    extra.append(_b1_disclosure(table))
    if competitors:
        extra.append('P4b 竞争句披露（不阻塞；本批按审计门集 P2–P6 判定，竞争句仅登记）：'
                     '本记录正文内另有敵下降句（'
                     + '、'.join(c.strip()[:40] for c in competitors) + '）；本句按唯一载体＋'
                     '敵減益半句形状匹配化解归属（批 6 §4.1 裁决口径沿用）')
    if self_half_slots:
        extra.append('复合句自身半句披露：本句「自身の…」半句对应载体自身侧提交槽 '
                     + '、'.join(f'/{k}={v!r}' for k, v in sorted(self_half_slots.items()))
                     + '（受控 self_side_p4_and_zero_slots_apk 实测双向提交）；param4/5/6 '
                     '未登记换算（scope §3），登记不分配、不属本批值行')
    extra.append('复合句披露：'
                 + ('本句另含非本批半句（「自身/味方…」侧、或回復等），其数值不属批 10'
                    '（fam11/自身バフ等侧另行处理），登记不分配' if re.search(r'自身|味方', frag)
                    else '本句为单一敵減益句'))
    extra.append(_slots_note(crec, set(claimed_slots)))
    summary = (B10_TAG + '：敵デバフ值行来源＝' + chain_desc + '；值行全部「推断」，不升'
               '「确认」，不进入整行确认。句→载体归属为数据侧结构对应：唯一 s_ability→2003 '
               '载体（批 13 扩域后两域分源样本域；本行载体为 CACHE 层）＋敵減益半句形状匹配＋方向按符号（p7/p8 负值加算下降、'
               'p9 正值受伤量加算＝「防御」表现层）；触发仅 Skill 型着弹（Normal/Critical '
               '不触发，与 99 三路不同）；引擎侧行→载体装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露' + _sample_domain_summary() + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject_phrase, attrs=list(claims), claims=dict(claims),
                table=table, carrier_record_id=carrier_id, carrier_layer='CACHE',
                carrier_name=crec.get('name'), via='s_ability_chain',
                # via_pattern 存 list（非 tuple）：页面 validate 以 json.loads(html payload)
                # 与 card 全等比对，tuple 经 JSON 往返会变 list 导致断言失败。
                via_pattern=list(via_pattern) if via_pattern else None,
                sent_no=sent_no, sent_total=sent_total)


# ---- P6 跨 cid 载体竞争守卫（进程内登记；审计全库交叉检查实测 0 例）----
_CLAIMS = {}


def _pattern_chain(data, pc, kids, table, subject, attrs, sent_no, sent_total):
    """行 children 中的 s_ability→2003 载体盘点（批 9 §3.1 审计同法；sub_effect 不消费）。

    返回 None（无 2003 载体/另有 99 → 批 9 照常处理）、{'kind':'hint',…} 或
    {'kind':'carrier','carrier':(sid,lay,crec),'dup_relay':…,'attrs':…,'subject':…}。"""
    sa2003, sa99 = [], []
    for c in kids:
        if c.get('table') != 'skilllist' or c.get('link_kind') != 'boss_skill.s_ability':
            continue
        sid = c.get('record_id')
        lay, crec = B9._ability_by_id(data, sid)
        if crec is None:
            continue
        ab = crec.get('ability')
        if ab == 2003:
            sa2003.append((sid, lay, crec))
        elif ab == 99:
            sa99.append((sid, lay, crec))
    if sa99:
        return None  # 99 家族归批 9（防跨批混用样本域；审计实测 C1 行 s_ability 链无 99）
    if not sa2003:
        return None  # 不属本批（批 9 照常处理）
    uniq = {}
    for sid, lay, crec in sa2003:
        uniq.setdefault((sid, lay), crec)
    dup_relay = len(sa2003) > len(uniq)
    if len(uniq) > 1:
        det = '；'.join(f'skilllist|{sid}|{lay}' for (sid, lay) in uniq)
        return _hint(table, [f'C3：链上 {len(uniq)} 个不同 s_ability→2003（SA_PowerDrain）'
                             f'载体（归属歧义，multi-carrier）：{det}'
                             + ('；另有多中继同指（dup_relay）' if dup_relay else '')
                             + '——ability2003 规则已登记，但载体不唯一，句→载体归属未化解，'
                               '不晋级'], subject=subject, attrs=attrs,
                     sent_no=sent_no, sent_total=sent_total)
    (sid, lay), crec = next(iter(uniq.items()))
    return dict(kind='carrier', carrier=(sid, lay, crec), dup_relay=dup_relay,
                attrs=attrs, subject=subject)


def evaluate(record: dict, frag: str, table: str, layer: str | None = None, record_id=None,
             text: str | None = None, data=None, cid=None):
    """对一行做批 10 SA2003 审核，返回 None（不属本批范围）或审核结果 dict。

    table：行记录表（TABLES 四表）；layer/record_id：行记录来源层与 id；text：行记录
    正文字段全文（clean 后）；data/cid：页级 Inputs 与 cid（data.old 子记录索引）。
    返回非 None ⇔ 行 s_ability 链上存在 2003 载体（本批接管批 9 对该行的 C1/C3 hint）。
    """
    if data is None or cid is None or table not in TABLES or not isinstance(record, dict):
        return None
    j = frag
    # --- P1 句面（批 9 同法） ----------------------------------------------------------------
    if '敵' not in j:
        return None
    if not any(w in j for w in B9.DOWN_WORDS):
        return None
    if not any(a in j for a in ATTRS3):
        return None
    if '敵から受ける' in j:
        return None  # 我方被击减伤句（非敌方减益），不在本批
    clause, attrs, subject = B9._debuff_clause(j)
    if clause is None or not attrs or not subject:
        return None  # B1 逐字对象门不成立 → 批 9 照常处理（镜像门 hint 归批 9）

    # --- 句序披露（批 9 同法） ----------------------------------------------------------------
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    _sents = [s for s in re.findall(r'[^。]*。', wb)]
    sent_no = next((i + 1 for i, s in enumerate(_sents) if frag.strip() in s), None)
    sent_total = len(_sents)

    pc = B9._chain_index(data)
    jk = lambda t: B6.unicodedata.normalize('NFKC', t).strip().rstrip('。').strip()
    if table == 'charainfo':
        # G5 同法（批 6/批 8/批 9）：同页同文 bosspattern 记录须唯一；且本批只在候选
        # pattern 链确实含 2003 载体时接管（否则返回 None，批 9 照常处理）
        ctx = B6._page_ctx(data, cid)
        matched = []
        for e, fragset in ctx['pattern_frags']:
            for fs in fragset:
                if jk(frag) in jk(fs) or jk(fs) in jk(frag):
                    matched.append(e)
                    break
        pat_ids = {(str(e.get('reference_id')), e.get('layer')) for e in matched}
        if not pat_ids:
            return None  # 同页无同文 pattern 行 → 批 9 照常处理
        cands = []
        for pid, player in sorted(pat_ids):
            pkids = pc.get(('bosspattern', pid, player), [])
            n2003, n99 = 0, 0
            for c in pkids:
                if c.get('table') != 'skilllist' or c.get('link_kind') != 'boss_skill.s_ability':
                    continue
                lay2, crec2 = B9._ability_by_id(data, c.get('record_id'))
                if crec2 is None:
                    continue
                ab = crec2.get('ability')
                if ab == 2003:
                    n2003 += 1
                elif ab == 99:
                    n99 += 1
            cands.append((pid, player, pkids, n2003, n99))
        if not any(n2003 for _p, _l, _k, n2003, _n in cands):
            return None  # 候选 pattern 链均无 2003 载体 → 批 9 照常处理（t13 等口径不变）
        if len(pat_ids) > 1:
            det = '；'.join(f'bosspattern|{p}|{l}(2003×{n})' for p, l, _k, n, _n in cands)
            return _hint(table, [f'charainfo 行：同文对应 {len(pat_ids)} 个 pattern 记录'
                                 f'（{det}），2003 载体归属歧义（G5 同法）——不晋级'],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
        pid, player, kids, _n2003, n99 = cands[0]
        if n99:
            return None  # 候选 pattern 链含 ability99 → 批 9 照常处理（防跨批混用样本域）
        via_note = f'charainfo 经同页同文 bosspattern|{pid}|{player}；'
    else:
        kids = pc.get((table, str(record_id), layer), [])
        via_note = ''
    if not kids:
        return None  # 链缺口 → 批 9 照常处理（C-no-children/C-no-pattern 口径）

    found = _pattern_chain(data, pc, kids, table, subject, attrs, sent_no, sent_total)
    if found is None:
        return None  # 无 2003 载体 / 另有 99 → 批 9 照常处理
    if found['kind'] == 'hint':
        return found
    sid, lay, crec = found['carrier']
    attrs = found['attrs']
    subject = found['subject']
    dup_relay = found['dup_relay']

    def _pre(reasons):
        return [via_note + r for r in reasons]

    # --- P2 样本域（批 13 APK 扩域：APK 载体委托 B13 接管；CACHE 域外防御分支不变） -------
    if lay != 'CACHE' or sid not in _domain2003(data):
        # 批 13（2026-10-22）：rules.json skilllist|2003 五键样本域已扩至 CACHE＋APK
        # 两域分源（occurrences_apk 登记），APK 载体（148 条扩后域）在此委托批 13 模块
        # 按载体层域接管：P4/P5/P6 门控后晋级（行级键 inference_b13，替换本批旧域外
        # hint，不双登记）或 hint。返回 dict 带 b13_ext 标记。
        import card_page_inference_b13_apkext as B13
        return B13.handle_2003_apk(frag=frag, table=table, layer=layer, record_id=record_id,
                                   cid=cid, subject=subject, attrs=attrs, clause=clause,
                                   sent_no=sent_no, sent_total=sent_total,
                                   via_note=via_note, dup_relay=dup_relay,
                                   sid=sid, lay=lay, crec=crec, text=text,
                                   via_pattern=(pid, player) if table == 'charainfo' else None)
    # --- P4 形状（双向） -----------------------------------------------------------------------
    ok, detail, mism = _shape_check(attrs, crec)
    if not ok:
        return _hint(table, _pre([f'P4：形状不符：' + '；'.join(mism) +
                                  '（缺槽＝缺失不补 0，rules limits 口径）']),
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    # --- P5 方向（代码语义；2003 例外 47000844 p7=+1 由本门兜底） ------------------------------
    dir_bad = []
    for param in ('param7', 'param8'):
        raw = crec.get(param)
        if B9._active(raw) and raw > 0:
            label = '攻撃力' if param == 'param7' else '移動速度'
            dir_bad.append(f'/{param}={raw}>0 与{label}下降冲突（加算正值为上升贡献）')
    p9 = crec.get('param9')
    if B9._active(p9) and p9 < 0:
        dir_bad.append(f'/param9={p9}<0 与受伤量加算口径（防御下降的表现层）冲突')
    if dir_bad:
        return _hint(table, _pre(['P5：方向冲突（direction-mismatch）：' + '；'.join(dir_bad)]),
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    # --- P6 跨 cid 载体竞争守卫 ------------------------------------------------------------------
    others = _CLAIMS.get(sid, set()) - {cid}
    if others:
        return _hint(table, _pre([f'P6：跨 cid 载体竞争：载体 skilllist|{sid}|CACHE 已被 '
                                  f'cid {",".join(map(str, sorted(others)))} 的行主张'
                                  '（进程内登记；审计全库交叉检查实测 0 例，本守卫为防御性保留）']),
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    _CLAIMS.setdefault(sid, set()).add(cid)
    # 自身半句载体槽（p4/5/6，登记不分配）
    self_half_slots = {}
    if '自身の' in j:
        self_half_slots = {p: crec.get(p) for p in ('param4', 'param5', 'param6')
                           if isinstance(crec.get(p), (int, float))
                           and not isinstance(crec.get(p), bool) and crec.get(p) != 0}
    competitors = B9._competing_debuff_sentences(text, frag, attrs)
    out = _promote(frag, table, layer, record_id, cid, attrs,
                   {a: True for a in attrs}, subject, clause, (sid, crec),
                   sent_no, sent_total, competitors, self_half_slots,
                   via_pattern=(pid, player) if table == 'charainfo' else None)
    if dup_relay:
        out['extra_reasons'].append('多中继披露（不阻塞）：链上多条 s_ability 中继指向同一 2003 '
                                    f'载体 skilllist|{sid}|CACHE（dup_relay）；载体唯一性按 '
                                    '去重后恰 1 个判定（批 9 §3.1 审计同法）')
    return out
