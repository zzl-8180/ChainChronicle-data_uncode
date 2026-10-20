"""模板作用域推断层——试点批次：type1017「戦場バフ」纯句式家族。

设计与范围依据：``output/character_skills/inference_inventory/pilot_design.md``（批 1 盘点产物，
同目录 TOP20.md / boundaries.md / template_inventory.json）。

精确范围（试点只取纯句式，设计稿实测 341 行 / 341 cid，每卡恰一行）：

* 记录类型 ``skilllist`` 且 ``ability == 1017``；
* 日文正文严格匹配 7 个模板（⟨X⟩＝原文尖括号占位，如 ``<戦士>``；占位符 ``<味方>`` 按
  「味方」同口径审核）::

      ^(その後、|さらに)?戦場にいる(味方|⟨X⟩|⟨X⟩所属(の味方)?)の
      (攻撃力|防御力|移動速度)(と(攻撃力|防御力|移動速度))*が上がる。$

明确排除（不匹配即不进入本层，维持原 C 行）：下がる句（敌方减益，边界 B1）、条件句
（如 7229「マナを所持していると…」type80，边界 B2）、无候选机制句（4009，边界 B3）、
共鳴 sympathy 命名空间（30338，边界 B4）、元语句（10212，边界 B5）、
type1017 更大的 2,203 行池（条件句 / Chain 句 / crit 句，留后续批次）。

句式→字段 1:1 映射（由 rules.json conversion 直接支撑，均为「已确认（静态及受控原生
局部规则）」）：

===============  =========  ==================================================
句中属性          字段        规则语义
===============  =========  ==================================================
攻撃力            /param1    攻击因子乘原值；增加比例=(原值-1)×100%
移動速度          /param2    移动因子乘原值
防御力            /param3    受伤量乘原值；减伤=(1-原值)×100%（正文写「防御」）
（对象）⟨X⟩/味方  /iParam0   接受者职业位图；param0=提供者自身参与开关（只注记）
===============  =========  ==================================================

硬边界（实施要求，逐行强制）：

* **只升「推断」，绝不升「确认」**：值行 numeric_evidence / association_evidence 一律
  「推断」，行级标注「推断（模板试点 type1017）」；不使用「确认」或「确认（类型外推）」
  （后者是 BY_TYPE_EXTRAPOLATED 专用字样）。推断行不进入整行确认统计。
* **逐行审核**：占位符与 iParam0 职业位图一致性逐行核对——「味方」句（含 ``<味方>``）
  要求位图覆盖玩家职业全集且无其他置位（31=bits 0..4）；``<职业>`` 句要求位图恰好命中
  该职业位；``所属`` 句当前无已确认映射，一律留 hint。位图不一致、缺证据、
  职业名→位映射缺依据的行**留 hint 不晋级**。
* **属性 1:1**：句中写了哪个属性取哪个 param；句中属性无已确认规则或记录缺原值时该属性
  留 hint 不造数（一条描述效果一行、逐项交付）；全无有据属性则整行留 hint。
* **中性值**：原值 1 的项如实沿用换算器文案「本项中性（原值 1）」，不隐藏。
* **多档同文**：逐记录逐行处理（同一技能多 lvorder 档各自按本记录 param 审核），
  不按同文去重。
* **句外参数**：记录内未被本句映射消费的参数（param4+ 等）不分配给本句，登记
  「句外参数未分配」注记；param0（自身参与开关）只做注记，本轮不裁决。
* **逐字段证据**（INFR-01，DeepSeek inference1017 审查）：值行 evidence/note 证据目录按字段
  取 rules.json 登记的 rule["evidence"]——param1/param3 用 output/ordinary_effects/ability1017/
  三件，param2 用 output/card_comparison_cid30236/movement/ 三件（ability1017 目录不含
  param2 规则）；证据文件缺失时显式失败，不产出死指针。
* **适用范围披露**（INFR-02）：值行与行级 summary 逐行披露规则样本域——param2 移动规则仅
  2 个已核 ID（43023605、65000002），全部 movement 值行属同类型外推；param1/param3 规则
  已核样本为 v3 CACHE 321 条，APK 主表的 173 类记录属同类型外推。披露不升级为「确认」。
* **非首段降级**（INFR-05）：严格句位于记录第 2 个及以后 ◆ 段的行保守降级留 hint（记录级
  param 的句级归属在多段记录中存在歧义，如 8157/8355）；非首段但本就因对象位图等原因留
  hint 的行（20902/20917），hint 同时保留原审核原因与降级原因。晋级的 337 行若记录另含
  其他◆段，在 unknown_reasons 登记多段披露。
* **占位符归一与去重守卫**（INFR-06）：全角尖括号占位（＜味方＞）按全/半角惯例归一后判定；
  句中重复属性按字段 1:1 去重并在注记登记（当前数据未触发，健壮性守卫）。
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import rules as R

PILOT_TAG = '推断（模板试点 type1017）'
PILOT_SCOPE = 'TEMPLATE_PILOT_1017'
PILOT_FAMILY = '戦場にいる（味方|⟨X⟩）の⟨ATTR⟩が上がる。'

# 7 个严格模板的正则表达（pilot_design.md；⟨X⟩＝原文尖括号占位，全/半角括号都接受）。
_PLACEHOLDER = r'[<＜]([^<>＜＞]{1,20})[>＞]'
STRICT_PATTERN = re.compile(
    r'^(その後、|さらに)?戦場にいる(味方|' + _PLACEHOLDER + r'所属(の味方)?|' + _PLACEHOLDER + r')'
    r'の(攻撃力|防御力|移動速度)(と(攻撃力|防御力|移動速度))*が上がる。$', re.S)

# 句式→字段 1:1 映射（rules.json 键 skilllist|1017|/paramN，均「已确认」）。
ATTR_FIELD = {'攻撃力': 'param1', '移動速度': 'param2', '防御力': 'param3'}
# 职业名→位（JobType 元数据枚举；rules.json skilllist|1017|/iParam0 base_definition）。
JOB_BIT = {'戦士': 0, '弓使い': 1, '魔法使い': 2, '僧侶': 3, '騎士': 4}
FULL_MASK = 31  # 玩家职业全集 bits 0..4（不含 ALMIGHTY bit5）
# INFR-02（DeepSeek inference1017 审查）：param2 移动规则的已核 ID 仅此 2 个（rules.json
# skilllist|1017|/param2 conditions）；本试点其余晋级行的 param2 值均为同类型外推，逐行披露。
CONFIRMED_PARAM2_IDS = (43023605, 65000002)
# param1/param3 规则已核样本域（rules.json conditions：仅当前 v3 CACHE 普通 ability1017 的
# 321 条记录）；APK 主表记录不在其内，逐行披露为同类型外推。
PARAM13_CACHE_CONFIRMED_RECORDS = 321

# INFR-01（DeepSeek inference1017 审查）：值行 evidence 按字段取 rules.json 登记的
# rule["evidence"]，不再对所有字段统一写 ability1017 目录（output/ordinary_effects/ability1017/
# README 明确「未知param2/flag等原样保留」，该目录不含 param2 规则）：
# * /param1 /param3 → rules.json evidence 中的 ../ordinary_effects/ability1017/* 三件
#   （解析为 output/ordinary_effects/ability1017/；审查裁定值行证据口径。rules.json 另登记的
#   ordinary_rules/* 为 param0/param1/param3 通用规则证据，不写入值行 evidence）；
# * /param2 → rules.json evidence 的 movement/* 相对路径，解析根为规则 origin
#   output/card_comparison_cid30236/（origin=output/card_comparison_cid30236/field_dictionary.json），
#   即 output/card_comparison_cid30236/movement/ 三件。
_CARD_COMPARISON_ROOT = 'output/card_comparison_cid30236/'


def _resolve_field_evidence(field):
    """按字段把 rules.json rule["evidence"] 解析为项目根相对路径，返回 (证据目录, 文件列表)。"""
    rule = R.rule_for('skilllist', 1017, '/' + field)
    files = []
    for entry in (rule or {}).get('evidence') or []:
        if entry.startswith('../'):
            files.append('output/' + entry[3:])
        elif entry.startswith('movement/'):
            files.append(_CARD_COMPARISON_ROOT + entry)
    if field in ('param1', 'param3'):
        files = [p for p in files if p.startswith('output/ordinary_effects/ability1017/')]
    expected_dir = (_CARD_COMPARISON_ROOT + 'movement/' if field == 'param2'
                    else 'output/ordinary_effects/ability1017/')
    if not files or any(not p.startswith(expected_dir) for p in files):
        raise ValueError(f'模板试点证据解析异常（INFR-01）：skilllist|1017|/{field} 的 rules.json '
                         f'evidence 未解析为 {expected_dir} 下的文件，实际 {files!r}')
    return expected_dir, files


_EVIDENCE_CACHE = {}


def _field_evidence(field):
    """按字段取已解析证据（含存在性检查：证据指针缺失时显式失败，不产出死指针）。"""
    if field not in _EVIDENCE_CACHE:
        evidence_dir, files = _resolve_field_evidence(field)
        missing = [p for p in files if not Path(p).is_file()]
        if missing:
            raise FileNotFoundError(f'模板试点证据文件缺失（INFR-01）：{missing}')
        _EVIDENCE_CACHE[field] = (evidence_dir, files)
    return _EVIDENCE_CACHE[field]


def _decode_mask(mask):
    try:
        m = int(mask)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(float(mask)):
        return None
    return m


def _mask_phrase(m):
    names = '、'.join(name for name, bit in JOB_BIT.items() if m & (1 << bit))
    extra = m & ~FULL_MASK
    return f'iParam0={m}（bits ' + ','.join(str(b) for b in range(6) if m & (1 << b)) + \
           (f'；职业 {names}' if names else '；无已命名职业') + \
           (f'；另有高位 0x{extra:x} 未解释' if extra else '') + '）'


def evaluate(record: dict, frag: str, layer: str | None = None, text: str | None = None):
    """对一行做模板作用域审核，返回 None（不属试点）或审核结果 dict。

    layer：记录来源层（'CACHE'/'APK'，INFR-02 分层适用范围披露用）。
    text：记录正文字段全文（clean 后；INFR-05 非首段降级与多段披露用）。

    结果 dict 字段：kind='promote'|'hint'；promote 时含 answers（值行，全部「推断」）、
    summary_reason、extra_reasons；hint 时含 reasons（登记进 unknown_reasons）。
    """
    if not isinstance(record, dict) or record.get('ability') != 1017:
        return None
    match = STRICT_PATTERN.match(frag)
    if not match:
        return None
    subject = match.group(2)
    # INFR-06（DeepSeek inference1017 审查）：全角尖括号占位（如 ＜味方＞）按既有全/半角
    # 处理惯例归一后再判定（模块正则本身同时接受全/半角括号，行 60 注释）；归一只改判定
    # 口径，不改变原文。此前 ＜味方＞ 会落入 <职业> 分支被当职业占位留 hint。
    subject = subject.replace('＜', '<').replace('＞', '>')

    # --- INFR-05（DeepSeek inference1017 审查）：非首段严格句保守降级 -----------------------
    # 片段在记录正文（[i][c] 之前）中的 ◆ 段号；记录的 param1/param2/param3 是记录级参数，
    # 多段记录中句级归属存在歧义（如 8157 第 1 段亦有「攻撃力と防御力が上がる」），本轮保守
    # 降级留 hint，不晋级（审查裁定：倾向保守）。非首段但本就因对象位图等原因留 hint 的行，
    # hint 同时保留原审核原因（如 20902/20917 仍显示位图原因）。
    section_reason = None
    section_no = None
    section_count = None
    if text:
        cut = text.find('[i][c]')
        body = text[:cut] if cut >= 0 else text
        pos = body.find(frag)
        if pos >= 0:
            # 段号口径：片段前紧邻的 ◆（仅隔空白/换行）是其所在段的开启标记，不计入段数；
            # 否则该片段是段内后句，计入其前的全部 ◆。段号 = 该片段所在段之前的 ◆ 数 + 1。
            back = pos
            while back > 0 and body[back - 1] in ' \r\t\n':
                back -= 1
            before = back - 1 if (back > 0 and body[back - 1] == '◆') else pos
            section_no = body.count('◆', 0, before) + 1
            first = body.find('◆')
            head = body[:first] if first >= 0 else body
            section_count = body.count('◆') + (1 if head.strip(' \r\t\n') else 0)
    if section_no is not None and section_no > 1:
        section_reason = (f'本严格句位于记录第 {section_no} 个◆段（非首段）；记录的 param1/param2/param3 '
                          '为记录级参数，多段记录中句级归属存在歧义（本记录其他段含其他效果描述，'
                          '无法逐句归属参数），本轮保守降级留 hint，不晋级（INFR-05）')
    attrs = re.findall(r'攻撃力|防御力|移動速度', frag)
    # INFR-06（DeepSeek inference1017 审查）：重复属性按字段 1:1 去重（同一字段只产出一条
    # 值行，不生成重复值行）；去重发生时在晋级行注记登记（当前数据未触发，健壮性守卫）。
    deduped = list(dict.fromkeys(attrs))
    attrs_deduped = len(deduped) < len(attrs)
    attrs = deduped

    # --- 逐行对象审核：占位符/味方 与 iParam0 职业位图一致性 -------------------
    # 对象审核不通过 → 整行留 hint 不晋级（位图错则全部属性值的接受者归属都不成立）。
    object_reasons = []
    mask_raw = record.get('iParam0')
    mask = _decode_mask(mask_raw) if mask_raw is not None else None
    mask_note = _mask_phrase(mask) if mask is not None else f'iParam0 原值 {mask_raw!r}（缺失或非有限数值）'
    if subject.endswith('所属'):
        # 所属→接受者映射无已确认规则（TOP20 #12 同款缺口）：一律留 hint。
        object_reasons.append(f'占位符「{subject}」是所属（出身）限定，所属→接受者映射无已确认规则，'
                              '本试点无证据裁决对象位图')
    elif subject in ('味方', '<味方>'):
        if mask is None:
            object_reasons.append('「味方」句要求位图覆盖玩家职业全集，但 ' + mask_note)
        elif (mask & FULL_MASK) != FULL_MASK:
            object_reasons.append('「味方」句对象位图未覆盖玩家职业全集（要求 bits 0..4 全置位）：' + mask_note)
        elif mask & ~FULL_MASK:
            object_reasons.append('「味方」句对象位图含已命名职业之外的高位，一致性无法裁决：' + mask_note)
    else:  # <职业> 占位符
        job = match.group(3) or match.group(5)
        bit = JOB_BIT.get(job)
        if bit is None:
            object_reasons.append(f'占位符「{subject}」的职业名→位映射缺证据（JobType 枚举外），'
                                  '本试点无证据裁决对象位图')
        elif mask is None:
            object_reasons.append(f'占位符「{subject}」要求位图命中 {job} 位，但 ' + mask_note)
        elif mask != (1 << bit):
            object_reasons.append(f'占位符「{subject}」与对象位图不一致（要求恰为 {job} 单位 '
                                  f'{1 << bit}）：' + mask_note)

    # --- 属性 1:1 映射 + 逐属性证据审核 ---------------------------------------
    mapped_fields = set()
    answers = []
    attr_hints = []
    # INFR-02（DeepSeek inference1017 审查）：逐字段适用范围披露——param2 移动规则仅 2 个
    # 已核 ID，本记录均不在其内；param1/param3 规则已核样本为 v3 CACHE 321 条，APK 记录不在
    # 其内（CACHE 记录在其内）。披露不改「推断」档位。
    def field_scope_note(field):
        if field == 'param2':
            return (f'适用范围：param2 移动规则已核 ID 仅 {len(CONFIRMED_PARAM2_IDS)} 个'
                    f'（{"、".join(str(i) for i in CONFIRMED_PARAM2_IDS)}），本记录不在其内，'
                    '按同类型（ability1017）规则外推，不属逐记录确认')
        if layer == 'APK':
            return (f'适用范围：param1/param3 规则已核样本为 v3 CACHE 普通 ability1017 的 '
                    f'{PARAM13_CACHE_CONFIRMED_RECORDS} 条记录，本记录来自 APK 主表，'
                    '按同类型规则外推，不属逐记录确认')
        return None
    for attr in attrs:
        field = ATTR_FIELD[attr]
        mapped_fields.add(field)
        rule = R.rule_for('skilllist', 1017, '/' + field)
        value = record.get(field)
        if rule is None:
            attr_hints.append(f'{attr}（/{field}）在该记录类型上无已确认规则，留 hint 不造数')
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            attr_hints.append(f'{attr}（/{field}）记录缺有限原值（{value!r}），留 hint 不造数')
            continue
        converted = R.answer_for('skilllist', 1017, '/' + field, value, record)
        if not converted or not converted.get('value_text'):
            attr_hints.append(f'{attr}（/{field}）换算器未给出答案，留 hint 不造数')
            continue
        neutral = value == 1
        evidence_dir, evidence_files = _field_evidence(field)
        scope_note = field_scope_note(field)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=value, field_path='/' + field,
            numeric_source='模板推断（type1017 试点）', numeric_evidence='推断',
            association_evidence='推断', evidence_scope=PILOT_SCOPE,
            rule_key=f'skilllist|1017|/{field}', rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            note=(f'模板试点 type1017：句中「{attr}」→/{field} 1:1 映射；规则键 skilllist|1017|/{field}；'
                  f'原值 {value}；证据目录 {evidence_dir}；对象审核 {mask_note}'
                  + (f'；{scope_note}' if scope_note else '')
                  + ('；本项中性（原值 1）' if neutral else '')),
            quantitative=True))

    # 对象审核不通过（或全属性无据，或非首段降级）→ 整行留 hint，不晋级。
    if section_reason is not None or object_reasons or not answers:
        reasons = ([section_reason] if section_reason else []) + list(object_reasons) + list(attr_hints)
        if not reasons:
            reasons.append('本句所有属性均无可推断数值')
        result = dict(kind='hint', reasons=reasons, subject=subject, attrs=attrs)
        if section_no is not None:
            result['section_no'] = section_no
        return result

    # --- 晋级行的注记（不改变「推断」档位） ------------------------------------
    extra = []
    other = []
    for key in sorted(record):
        if re.match(r'^(param|iParam|iparam|skillparam|flag|skillflag)\d+$', key) \
                and key not in mapped_fields and key not in ('iParam0', 'param0'):
            value = record[key]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                other.append(f'/{key}={value}')
    if other:
        extra.append('句外参数未分配（不归属本句，仅登记原值）：' + '、'.join(other))
    param0 = record.get('param0')
    if param0 is not None:
        extra.append(f'param0（提供者自身参与开关）原值 {param0}；只做注记，本轮不裁决')
    if attr_hints:  # 部分属性留 hint 但其余有据：逐项交付，行仍晋级
        extra.append('部分属性留 hint：' + '；'.join(attr_hints))
    if attrs_deduped:
        extra.append('句中同一属性重复提及，按字段 1:1 去重，同字段仅一条值行（INFR-06 守卫）')
    if section_count is not None and section_count > 1:
        extra.append(f'本记录另含其他◆段（共 {section_count} 段），其效果未被本句消费、本轮不归属'
                     '（INFR-05 多段披露）')
    # INFR-02：行级 summary 同步披露本行的规则适用范围（与值行「适用范围」注记同口径）。
    promoted_fields = {a['field_path'][1:] for a in answers}
    scope_parts = []
    if promoted_fields & {'param1', 'param3'} and layer == 'APK':
        scope_parts.append(f'param1/param3 规则已核样本为 v3 CACHE 普通 ability1017 的 '
                           f'{PARAM13_CACHE_CONFIRMED_RECORDS} 条记录，本行来自 APK 主表，属同类型外推')
    if 'param2' in promoted_fields:
        scope_parts.append(f'param2 移动规则已核 ID 仅 {len(CONFIRMED_PARAM2_IDS)} 个'
                           f'（{"、".join(str(i) for i in CONFIRMED_PARAM2_IDS)}），本行不在其内，属同类型外推')
    summary = (PILOT_TAG + '：句式→字段映射由已确认规则（skilllist|1017）支撑，'
               '对象位图逐行审核通过；未逐记录人工审定，不升「确认」，不进入整行确认统计。'
               + ('适用范围披露：' + '；'.join(scope_parts) + '。' if scope_parts else ''))
    return dict(kind='promote', answers=answers, summary_reason=summary,
                extra_reasons=extra, subject=subject, attrs=attrs)
