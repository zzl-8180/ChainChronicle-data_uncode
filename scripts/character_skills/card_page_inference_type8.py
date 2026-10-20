"""模板作用域推断层——批 3：家族 #3「⟨ATTR⟩が上がる。」的 type8 子集。

设计与范围依据：``output/character_skills/inference_inventory/b3_type8_scope.md``（批 3 前置
审计产物；逐行清单 work/character_skills_b3_type8/type8_tier1.json）。实施纪律沿用 type1017
试点（``card_page_inference_1017.py``）及 DeepSeek 审查教训（INFR-01/02/05；R-02：适用范围
披露按记录分支，不硬编码；R-03：段号按精确片段位置）。

精确范围（Tier1，审计实测 40 行 / 40 cid，全部 APK；六条件须同时满足）：

* 记录类型 ``skilllist`` 且 ``ability == 8``（type8＝Always 常时能力，0 行多 effect_type）；
* 严格句：仅由属性名词用「と」连接、以「が上がる。」结尾（不得含句首连接词その後、/さらに/
  また/更に/ただし、——含则只留 hint；不含条件词/占位/下がる——本子集实测 0 行）；
* 句位＝记录正文第 1 个◆段的首句；段内句后无实质后续文本；同文在正文仅出现 1 次；
  晋级前该行无既有答案（调用点 ``not answers`` 守卫）。

句式→字段 1:1 映射（rules.json 键 ``skilllist|8|/paramN``，均「已确认数值换算」）：

==========  ========  =============================================================
句中属性    字段       规则语义（conversion 原文）
==========  ========  =============================================================
攻撃力      /param1   本项攻击 +(param1-1)×100%（GetAbilityAttack 0x1107958）
移動速度    /param2   移动速度 ×param2（GetAbilityWalkSpeed 0x1118c28）
防御力      /param3   本项减伤 (1-param3)×100%；正文写「防御」、乘受伤量因子，
                      方向按代码不按名称（GetAbilityDefence 0x1108124）
==========  ========  =============================================================

与 type1017 试点的关键差异（审计 §1.2/§1.4）：type8 三条规则 **occurrences 均为 null**
（无 1017 式「v3 CACHE 321 条逐记录文本核验」大样本）——已核样本域按 native 口径另行披露，
任何层（含 CACHE）的 type8 值行都逐行披露「同类型（ability8）原生规则外推，未逐记录审定」。

硬边界（逐行强制）：

* **只升「推断」，绝不升「确认」**：值行 numeric_evidence / association_evidence 一律「推断」，
  行级标注「推断（模板批 3 type8）」、evidence_scope=[TEMPLATE_BATCH3_TYPE8]；不进入整行确认。
* **方向审核（type8 新增）**：主张属性必须方向一致——param1>1、param2>1、param3<1（受伤量
  乘数语义）；原值恰为 1 如实登记「本项中性（原值 1）」，不因此拒绝；方向冲突整行留 hint。
* **暴击名词不映射**：type8 原生路径不读暴击槽（native_checks type8_gated_by_isenable）；
  PART 行（句中含クリティカル発生率/威力等）暴击属性留 attr-level hint、其余属性照常晋级；
  暴击-only 行（句中全部属性无可映射字段）整行留 hint。
* **对象审核（type8 简化）**：Tier1 句式无对象限定词；接受者＝能力持有者自身，由 type8 原生
  apply 路径（乘自身因子）支撑。param0/param4 无读取路径（type8_slots_attack_move_defence、
  type8_param4_param0_scope_two_sources），只做「句外参数未分配（原生三条路径不读取）」注记。
* **逐字段证据（INFR-01 同法）**：值行 evidence 按字段取 rules.json ``rule["evidence"]``
  （三字段同源：skilllist_types.py、skilllist_types/native_checks.json、GetAbility* 分支地址）；
  证据中路径型条目缺失时显式失败，不产出死指针。
* **非首段降级（INFR-05 同法；R-03 教训）**：段号按本片段在正文中的精确出现位置计算；
  同文多次出现时不取首次出现——登记全部出现位置并按句级归属歧义留 hint。
* **多段披露**：晋级行登记「本记录另含其他◆段（共 N 段）」（Tier1 全部 40 条记录为 2–3 段，
  对本批全部行生效）。
* **逐行处理、不按同文去重**（cid 221 在子集内有 2 行：1 行 Tier1、1 行暴击-only，
  「每卡恰一行」在本批不成立）。
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import rules as R

TYPE8_TAG = '推断（模板批 3 type8）'
TYPE8_SCOPE = 'TEMPLATE_BATCH3_TYPE8'
TYPE8_FAMILY = '⟨ATTR⟩が上がる。'

# 严格句：属性名词（含暴击类，暴击类只留 hint 不映射）用「と」连接＋「が上がる。」结尾。
# 句首连接词（その後、/さらに/また/更に/ただし、）在 type8 一律不晋级（b3_type8_scope.md §3.1
# 条件 2），但为排除登记（§4 非首段/段中类含 1 行 その後、句）仍纳入审核、只留 hint。
_ATTR = r'攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力|クリティカル率|クリティカル'
_CONNECTIVE = r'(?:その後、|さらに|また|更に|ただし、)'
STRICT_PATTERN = re.compile(r'^(?:' + _CONNECTIVE + r')?(?:' + _ATTR + r')(?:と(?:' + _ATTR + r'))*が上がる。$')
CONNECTIVE_PATTERN = re.compile(r'^' + _CONNECTIVE)
ATTR_PATTERN = re.compile(_ATTR)

ATTR_FIELD = {'攻撃力': 'param1', '移動速度': 'param2', '防御力': 'param3'}
# param3＝受伤量乘数（正文写「防御」）：上がる（防御）要求 param3<1；param1/param2 要求 >1。
DIRECTION = {'param1': 'gt1', 'param2': 'gt1', 'param3': 'lt1'}

# 已核对照样本（native_checks.json，evidence_kind=CONTROLLED_NATIVE_FRAGMENT，53/53 通过）：
# * type8_move_only_record_has_neutral_param3：正文只提攻撃+移動的记录 param3 必须为 1，样本 46000341；
# * type8_param1_param3_match_record_text：正文直写「攻撃X防御Y」对照 1 条（checks 未登记记录 id）；
# * type8_param4_param0_scope_two_sources：分源范围核对 CACHE 328 条/APK 2209 条（仅覆盖
#   param4/param0 不给规则的依据）。
# R-02 教训：适用范围披露按记录 id 分支（本记录是否为已核样本），不硬编码「不在其内」。
VERIFIED_SAMPLE_RECORDS = {46000341: 'param3 中性/仅攻撃+移動对照（type8_move_only_record_has_neutral_param3）'}
PARAM4P0_SCOPE_NOTE = ('CACHE 328 条/APK 2209 条记录的分源范围核对仅覆盖 param4/param0 不给规则的依据'
                       '（type8_param4_param0_scope_two_sources）')


def _resolve_field_evidence(field):
    """按字段取 rules.json rule["evidence"]；路径型条目做存在性检查（INFR-01 同法，缺失显式失败）。"""
    rule = R.rule_for('skilllist', 8, '/' + field)
    if rule is None:
        raise ValueError(f'模板批 3 type8 证据解析异常（INFR-01）：rules.json 无 skilllist|8|/{field} 规则')
    entries = list(rule.get('evidence') or [])
    if not entries:
        raise ValueError(f'模板批 3 type8 证据解析异常（INFR-01）：skilllist|8|/{field} 的 rules.json evidence 为空')
    path_files = [e for e in entries if e.startswith(('scripts/', 'output/'))]
    missing = [p for p in path_files if not Path(p).is_file()]
    if missing:
        raise FileNotFoundError(f'模板批 3 type8 证据文件缺失（INFR-01）：{missing}')
    return entries, path_files


_EVIDENCE_CACHE = {}


def _field_evidence(field):
    if field not in _EVIDENCE_CACHE:
        _EVIDENCE_CACHE[field] = _resolve_field_evidence(field)
    return _EVIDENCE_CACHE[field]


def _occurrences(body, frag):
    """frag 在正文中的全部出现起点（R-03：不取首次出现，逐处登记）。"""
    starts = []
    pos = body.find(frag)
    while pos >= 0:
        starts.append(pos)
        pos = body.find(frag, pos + 1)
    return starts


def _section_no(body, pos):
    """片段所在 ◆ 段号（R-03：按片段精确位置；段中句按其所在段的开启 ◆ 计数）。

    片段前紧邻 ◆（段首）时该 ◆ 是所在段的开启标记，不计入段数；段中句取其前面最近的一个 ◆
    作为所在段开启标记（试点公式对段中句会把自身段的开启 ◆ 重复计入、段号虚增 1，本模块不沿用）。
    """
    back = pos
    while back > 0 and body[back - 1] in ' \r\t\n':
        back -= 1
    at_head = back == 0 or body[back - 1] == '◆'
    opening = back - 1 if (back > 0 and body[back - 1] == '◆') else body.rfind('◆', 0, pos)
    return (body.count('◆', 0, opening) + 1 if opening >= 0 else 1), at_head


def _section_count(body):
    first = body.find('◆')
    return body.count('◆') + (1 if (body[:first] if first >= 0 else body).strip(' \r\t\n') else 0)


def _trailing(body, pos, frag):
    """片段之后、同段（下一个 ◆ 或正文尾）之前是否有实质文本（句后条件扩展判定）。"""
    nxt = body.find('◆', pos + len(frag))
    end = nxt if nxt >= 0 else len(body)
    return ''.join(body[pos + len(frag):end].split())


def _direction_check(field, value):
    """返回 ('ok'|'neutral'|'conflict'|'invalid', 说明)。param3 语义＝受伤量乘数（方向按代码）。"""
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        return 'invalid', f'记录缺有限原值（{value!r}）'
    if value == 1:
        return 'neutral', '本项中性（原值 1）'
    if DIRECTION[field] == 'gt1':
        if value > 1:
            return 'ok', f'方向一致（v={value}>1）'
        return 'conflict', f'方向冲突（v={value}<1，句称上升而记录参数为缩减）'
    if value < 1:
        return 'ok', f'方向一致（param3={value}<1，减伤 (1-{value})×100%，按代码方向）'
    return 'conflict', (f'方向冲突（param3={value}>1 即增伤，句称「防御力が上がる」；param3 语义为受伤量乘数，'
                        '方向按代码不按名称「防御」）')


def _scope_note(record_id, field, layer):
    """值行适用范围披露（INFR-02 同法，type8 口径；按记录 id 分支——R-02 教训）。"""
    sample = VERIFIED_SAMPLE_RECORDS.get(record_id if isinstance(record_id, int) else None)
    if sample:
        return (f'本记录为 type8 已核对照样本（{sample}）；该核对属受控原生分支解析的对照样本，'
                '仍不构成逐记录全部字段的审定')
    return ('type8 规则无逐记录文本核验样本（rules.json skilllist|8|/* 的 occurrences 未登记）；'
            '已核依据为受控原生分支解析（Unicorn+静态双路解析 53/53 通过）＋正文数值直写对照 1 条＋'
            f'param3 中性核对 1 条（46000341）；{PARAM4P0_SCOPE_NOTE}。'
            f'本记录来自 {layer or "未知"} 层、不在已核对照样本内，本值行按同类型（ability8）原生规则外推，'
            '未逐记录审定，不属逐记录确认')


def evaluate(record: dict, frag: str, layer: str | None = None, record_id=None, text: str | None = None):
    """对一行做 type8 模板作用域审核，返回 None（不属本批范围）或审核结果 dict。

    layer／record_id：记录来源层与记录 id（适用范围披露按记录分支，R-02）。
    text：记录正文全文（clean 后；句位/段位/同文次数判定用）。

    结果 dict 字段：kind='promote'|'hint'；promote 时含 answers、summary_reason、extra_reasons；
    hint 时含 reasons（登记进 unknown_reasons）。
    """
    if not isinstance(record, dict) or record.get('ability') != 8:
        return None
    if not STRICT_PATTERN.match(frag):
        return None
    connected = CONNECTIVE_PATTERN.match(frag) is not None
    attrs = list(dict.fromkeys(ATTR_PATTERN.findall(frag)))
    mapped = [a for a in attrs if a in ATTR_FIELD]
    crit = [a for a in attrs if a not in ATTR_FIELD]

    # --- 句位/段位/同文次数（R-03：按精确片段位置，逐处登记） -----------------------------
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    body = body[:cut] if cut >= 0 else body
    starts = _occurrences(body, frag) if body else []
    positions = [_section_no(body, pos) + (_trailing(body, pos, frag) != '',) for pos in starts] \
        if starts else []
    if not body:
        return dict(kind='hint', reasons=['记录正文不可用，句位/段内句后文本无法核验，保守留 hint'],
                    attrs=attrs)
    if len(starts) > 1:
        nos = '、'.join(str(p[0]) for p in positions)
        return dict(kind='hint', attrs=attrs, reasons=[
            f'同文在记录正文出现 {len(starts)} 次（第 {nos} 段），句级归属歧义；'
            '记录的 param1/param2/param3 为记录级参数，无法判定本行对应哪处出现，保守留 hint'])
    if not starts:
        return dict(kind='hint', attrs=attrs, reasons=[
            '严格句未能在记录正文中定位（片段与正文不一致），保守留 hint'])
    section_no, at_head, has_trailing = positions[0]

    # --- 逐属性审核：字段映射＋方向＋原值 ------------------------------------------------
    attr_hints = []          # 属性级 hint（不阻断其余属性晋级）
    row_reasons = []         # 整行级 hint 原因
    answers = []
    neutrals = []
    directions = {}
    for attr in mapped:
        field = ATTR_FIELD[attr]
        rule = R.rule_for('skilllist', 8, '/' + field)
        value = record.get(field)
        verdict, detail = _direction_check(field, value)
        directions[field] = verdict
        if verdict == 'conflict':
            row_reasons.append(f'{attr}（/{field}）{detail}；不晋级')
        elif verdict == 'invalid':
            attr_hints.append(f'{attr}（/{field}）{detail}，留 hint 不造数')
        elif rule is None:
            attr_hints.append(f'{attr}（/{field}）在该记录类型上无已确认规则，留 hint 不造数')
        else:
            converted = R.answer_for('skilllist', 8, '/' + field, value, record)
            if not converted or not converted.get('value_text'):
                attr_hints.append(f'{attr}（/{field}）换算器未给出答案，留 hint 不造数')
                continue
            entries, path_files = _field_evidence(field)
            if verdict == 'neutral':
                neutrals.append(attr)
            answers.append(dict(
                value=converted['value_text'],
                quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
                raw_value=value, field_path='/' + field,
                numeric_source='模板推断（type8 批 3）', numeric_evidence='推断',
                association_evidence='推断', evidence_scope=TYPE8_SCOPE,
                rule_key=f'skilllist|8|/{field}', rule_status=rule.get('status'),
                conversion=rule.get('conversion'), conditions=converted.get('conditions'),
                rule_limits=rule.get('limits'),
                evidence=list(rule.get('evidence') or []),
                evidence_paths=list(path_files),
                note=(f'模板批 3 type8：句中「{attr}」→/{field} 1:1 映射；规则键 skilllist|8|/{field}；'
                      f'原值 {value}；方向审核 {detail}；证据按 rules.json rule["evidence"]'
                      f'（路径件 {path_files}）；适用范围：{_scope_note(record_id, field, layer)}'
                      + ('；本项中性（原值 1）' if verdict == 'neutral' else '')),
                quantitative=True))
    for attr in crit:
        attr_hints.append(
            f'{attr}（句中属性）：type8 三条 apply 路径不读暴击槽（native_checks '
            f'type8_gated_by_isenable），本记录类型无字段可映射，其实现位置（兄弟记录/其他机制）'
            '本层不裁决，留 hint 不造数')

    # --- 整行级排除判定（b3_type8_scope.md §3.1 六条件 / §4 四类文案） --------------------
    if connected:
        row_reasons.append('句含句首连接词（その後、/さらに/また/更に/ただし、）：本批严格范围不接受'
                           '连接词句（scope §3.1 条件 2），保守留 hint')
    if section_no > 1:
        row_reasons.append(f'本严格句位于记录第 {section_no} 个◆段（非首段）；记录的 param1/param2/param3 '
                           '为记录级参数，多段记录中句级归属存在歧义，本轮保守降级留 hint，不晋级（INFR-05）')
    elif not at_head:
        row_reasons.append(f'本严格句为第 {section_no} 段的段中句（非段首句）；记录级 param 的句级归属'
                           '存在歧义，保守留 hint（INFR-05 同法）')
    if has_trailing:
        row_reasons.append('同段句后有后续文本（条件扩展/其他效果句）：记录级 param1/2/3 与条件增幅的'
                           '数值归属无法从本记录分离（条件增幅疑由兄弟记录承载，仅 31020500 记录链 1 例'
                           '核实，不足以普遍裁决），按「宁可排除」留 hint（批 3 待补证二批）')
    if not mapped:
        row_reasons.append('句中属性在 type8 记录上无字段可映射（type8 三条 apply 路径只读 '
                           'param1/param2/param3，不读暴击槽），整行留 hint')
    if row_reasons or not answers:
        reasons = row_reasons + list(attr_hints)
        if not reasons:
            reasons.append('本句所有属性均无可推断数值')
        result = dict(kind='hint', reasons=reasons, attrs=attrs,
                      section_no=section_no, section_count=_section_count(body))
        return result

    # --- 晋级行注记（不改变「推断」档位） ------------------------------------------------
    extra = []
    mapped_fields = {a['field_path'][1:] for a in answers}
    other = []
    for key in sorted(record):
        if re.match(r'^(param|iParam|iparam|skillparam|flag|skillflag)\d+$', key) \
                and key not in mapped_fields:
            value = record[key]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                other.append(f'/{key}={value}')
    if other:
        extra.append('句外参数未分配（不归属本句，仅登记原值；type8 三条 apply 路径不读取 '
                     'param0/param4 槽——native_checks type8_slots_attack_move_defence、'
                     'type8_param4_param0_scope_two_sources）：' + '、'.join(other))
    if attr_hints:  # 部分属性留 hint 但其余有据：逐项交付，行仍晋级
        extra.append('部分属性留 hint：' + '；'.join(attr_hints))
    section_count = _section_count(body)
    if section_count > 1:
        extra.append(f'本记录另含其他◆段（共 {section_count} 段），其效果未被本句消费、本轮不归属'
                     '（INFR-05 多段披露）')
    scope_note = _scope_note(record_id if isinstance(record_id, int) else None,
                             mapped[0], layer)
    summary = (TYPE8_TAG + '：句式→字段映射由已确认规则（skilllist|8）支撑，方向逐行审核通过；'
               'type8 规则无逐记录文本核验样本（rules.json occurrences 未登记），'
               '按同类型（ability8）原生规则外推，未逐记录审定，不升「确认」，不进入整行确认统计。'
               f'适用范围披露：{scope_note}。')
    return dict(kind='promote', answers=answers, summary_reason=summary,
                extra_reasons=extra, attrs=attrs, section_no=section_no,
                section_count=section_count, neutrals=neutrals)
