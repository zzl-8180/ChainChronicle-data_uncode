"""模板作用域推断层——批 5：type1017 严格句跨表扩展（job_ability／supporterskill）。

设计与范围依据：``output/character_skills/inference_inventory/b5_xtable_scope.md``
（批 5 前置审计；逐行明细 work/character_skills_b5_xtable/row_classification.json：
全库 257 行 C 行＝211 晋级候选（job_ability 194＋supporterskill 17）＋46 留 hint
（所属 27＋句后文本 19）；Y.G. 111 行＝108 晋级＋3 留 hint）。

精确范围（scope §5.1，全部满足才进入本批）：

* 行记录表 ``table ∈ {job_ability, supporterskill}`` 且晋级前无既有答案（调用点
  ``not answers`` 守卫；30236 同文 job 行已是 A/确认，不进入本层）；
* 日文正文严格匹配试点正则（**逐字节复用** ``card_page_inference_1017.STRICT_PATTERN``，
  含 その後、/さらに 前缀、``所属`` 变体、INFR-06 全/半角占位）；
* 同文在记录正文恰 1 次（守卫保留，实测 257/257 满足）；
* 严格句所在段无句后文本（实测 job 194 行满足；supporterskill 19 行不满足→hint）；
* 链解析＋对象审核＋方向/未主张槽审核通过（scope §5.3/§5.4）。

跨记录映射（本批核心，scope §5.2；批 4 §5.2 双记录标注同法）——两张表的行记录自身
**无参数槽**，值在链上 skilllist 记录：

* **job_ability 行**：``jobabilityinfo.data5.json.raw#/job_ability/<i>``（``cids`` 含本 cid，
  CACHE 专属表，APK 无 jobabilityinfo）；严格句所在 ◆ 段号 N ↔ ``skill_ids[N-1]`` 位置序
  （审计 §2.2 旁证 15/15，实施逐行重验；段数≠skill_ids 数的记录位置对应不成立则留 hint）。
  第 2◆段严格句 → ``skilllist|65000002|CACHE|ability=1017``（16 条 job 记录共享）。
  值行 3 条：param1=1.5→``攻击×1.5（本项提高 50%）``、param2=1.15→``移动速度×1.15（+15%）``、
  param3=0.85→``受伤量×0.85（本项减伤 15%；不是固定防御量）``（rules.py 换算器产出）。
* **supporterskill 行**：``ability=2`` 容器，值在 ``abi0``/``abi1`` 子记录。段位 N ↔
  ``abi(N-1)`` 位置序（scope §2.4；link 层仅引用 abi0/abi1，abi2+ 无已核实对应→留 hint）。
  本批 17 行晋级全部第 2◆段 → abi1 → ``skilllist|121009|APK|ability=1017``（共享）。
  值行 2 条：param1=1.03→``攻击×1.03（本项提高 3%）``、param3=0.97→
  ``受伤量×0.97（本项减伤 3%；不是固定防御量）``；param2=1.0 未主张中性（如实登记）。

硬边界（scope §5.5/§5.6/§6，逐行强制）：

* **只升「推断」，绝不升「确认」**：值行 numeric_evidence/association_evidence 一律「推断」，
  行级标注「推断（模板批 5 跨表 type1017）」、evidence_scope=TEMPLATE_BATCH5_XTABLE；
  不进入整行确认统计；65000002 在 321 条已核样本域内只改善披露口径，不改变档位。
* **不得跨记录合并**（§6.2）：job 行值只含 65000002 三参数，不得与 65000001（第 1 段记录）、
  30236 基线 A 行或同卡其他 skill 记录合并/连乘；supporterskill 行值只含 121009 参数，
  不得与 abi0 玛那记录合并；不同来源记录的同名字段不折叠为一条值行。
* **归属为推断性质**（§6.3）：段位↔链位置对应是数据侧结构对应；行级 summary 逐行披露
  「sub/link 关联的引擎侧装载路径无原生核实」；实施时位置对应破坏（ability≠1017、abi 缺失、
  段位超出链长）的行留 hint。
* **对象审核**（§5.3，试点同法）：味方句要求链记录 iParam0 覆盖玩家职业全集且无高位
  （31=bits 0..4）；所属句一律留 hint；param0（提供者自身参与开关）只注记。
* **方向与未主张槽审核**（§5.4）：param1/param2>1、param3<1（受伤量乘数方向按代码；
  原值 1 如实登记中性）；链记录 param1/2/3 中未被句主张者必须中性，否则 P-D 留 hint；
  句外参数登记「句外参数未分配」注记。
* **crit 变体 12 行与 fam17 18 行（Y.G.）不进本批**（§3/§4）：其行不匹配本批纯句式审核路径
  （同段句后条件扩展→trailing hint ／ 非本批句式→不进入本层），维持 C 行。
* **多段披露**（§5.5-5）：晋级行登记「本记录另含其他◆段（共 N 段）」＋链上其余位置记录
  未消费披露；不假设段数＝skill_ids 数（scope §2.2 披露点）。
* **逐字段证据**（INFR-01）：值行 evidence 按字段复用试点解析（param1/param3→
  output/ordinary_effects/ability1017/ 三件；param2→output/card_comparison_cid30236/movement/
  三件），证据文件缺失显式失败（复用 ``card_page_inference_1017._field_evidence``）。
* **适用范围披露按记录分支**（INFR-02/R-02）：来源记录在规则已核样本域内（65000002∈
  321 条 CACHE；65000002∈param2 已核 ID）→写明「在其内」；APK 记录（121009）不在域内→
  逐行外推披露。不硬编码「不在其内」。
* **逐行处理、不折叠**（§5.5-6）：194 行虽共享同一 65000002，值相同仍逐行产出，不按同文/
  同值去重；跨行合并数值答案为禁止项（§6.1）。
"""
from __future__ import annotations

import math
import re

import rules as R
import card_page_inference_1017 as PILOT1017
import card_page_inference_type8 as TYPE8

B5_TAG = '推断（模板批 5 跨表 type1017）'
B5_SCOPE = 'TEMPLATE_BATCH5_XTABLE'
B5_FAMILY = 'type1017 严格句跨表扩展（job_ability／supporterskill→链上 skilllist 记录）'

TABLES = ('job_ability', 'supporterskill')

# 句式→字段 1:1 映射与方向（复用试点/批 3 同表；param3＝受伤量乘数，方向按代码）。
ATTR_FIELD = PILOT1017.ATTR_FIELD
FULL_MASK = PILOT1017.FULL_MASK
CONFIRMED_PARAM2_IDS = PILOT1017.CONFIRMED_PARAM2_IDS
PARAM13_CACHE_CONFIRMED_RECORDS = PILOT1017.PARAM13_CACHE_CONFIRMED_RECORDS


def _pilot_section_no(body, pos):
    """试点公式段号（card_page_inference_1017.py:183-197 同法；本批行集按试点公式审计，
    与 TYPE8._section_no 的段中句口径不同——为不漂移于审计行集，此处沿用试点公式）。"""
    back = pos
    while back > 0 and body[back - 1] in ' \r\t\n':
        back -= 1
    before = back - 1 if (back > 0 and body[back - 1] == '◆') else pos
    return body.count('◆', 0, before) + 1


def _mask_note(chain_record):
    raw = chain_record.get('iParam0')
    mask = PILOT1017._decode_mask(raw) if raw is not None else None
    if mask is None:
        return f'iParam0 原值 {raw!r}（缺失或非有限数值）'
    return PILOT1017._mask_phrase(mask)


def _scope_note(field, chain_record_id, chain_layer):
    """值行适用范围披露（INFR-02；按来源记录分支——R-02 教训，不硬编码「不在其内」）。

    * param1/param3：已核样本域＝v3 CACHE 普通 ability1017 的 321 条记录；
      来源记录在其内（65000002）→写明在其内；APK 记录→逐行外推披露（scope §5.5-3）。
    * param2：已核 ID 仅 43023605、65000002；按来源记录 id 分支。
    """
    if field == 'param2':
        in_domain = chain_record_id in CONFIRMED_PARAM2_IDS
        ids = '、'.join(str(i) for i in CONFIRMED_PARAM2_IDS)
        return (f'param2 移动规则已核 ID 仅 {len(CONFIRMED_PARAM2_IDS)} 个（{ids}），'
                + ('本行来源记录在其已核 ID 内' if in_domain else
                   f'本行来源记录 {chain_record_id} 不在其内，按同类型（ability1017）规则外推，'
                   '不属逐记录确认'))
    if chain_layer == 'APK':
        return (f'param1/param3 规则已核样本为 v3 CACHE 普通 ability1017 的 '
                f'{PARAM13_CACHE_CONFIRMED_RECORDS} 条记录，本行来源记录来自 APK 主表，'
                '按同类型规则外推，不属逐记录确认')
    return (f'来源记录属 param1/param3 规则已核样本域（v3 CACHE 普通 ability1017 的 '
            f'{PARAM13_CACHE_CONFIRMED_RECORDS} 条记录）')


def _chain_refs(table, skill_refs):
    """link 层 skill_refs → 位置映射。job_ability：skill_ids[i]；supporterskill：abiN。"""
    out = {}
    for r in (skill_refs or []):
        if not r.get('resolved') or r.get('table') != 'skilllist':
            continue
        rf = r.get('reference_field') or ''
        m1 = re.fullmatch(re.escape(table) + r'\.skill_ids\[(\d+)\]', rf)
        m2 = re.fullmatch(re.escape(table) + r'\.abi(\d+)', rf)
        if m1:
            out.setdefault(('pos', int(m1.group(1))), r)
        elif m2:
            out.setdefault(('abi', int(m2.group(1))), r)
    return out


def _others_disclosure(table, skill_refs, used_pos):
    """链上其余位置记录披露（未被本句消费、本轮不归属；不假设段数＝链长）。"""
    others = []
    for (kind, idx), r in sorted(_chain_refs(table, skill_refs).items()):
        if (kind, idx) == used_pos:
            continue
        rec = r.get('record') or {}
        others.append(f"skilllist|{r.get('reference_id')}|{r.get('layer')}"
                      f"|ability={rec.get('ability')}（链位置 {'skill_ids[%d]' % idx if kind == 'pos' else 'abi%d' % idx}，位置旁证）")
    return others


def _promote(record, frag, table, layer, record_id, body, pos, section_no, section_count,
             subject, attrs, chain_record, chain_id, chain_layer, chain_pos, chain_pos_desc,
             skill_refs):
    """晋级行：值行全部来自链上 skilllist|…|ability=1017 记录，逐行注明来源记录链（scope §5.2）。"""
    if table == 'job_ability':
        chain_rec_key = f'skilllist|{chain_id}|{chain_layer}|ability=1017'
        via = f'经 jobabilityinfo 记录（cids 含本 cid）的 skill_ids[{chain_pos[1]}] 关联'
        numeric_source = (f'模板推断（批 5 跨表：job_ability→skill_ids[{chain_pos[1]}]'
                          f'→skilllist|{chain_id}|{chain_layer}）')
        belonging = ('jobabilityinfo 段位↔skill_ids 位置序＋段文属性数↔链记录活性参数形状一致'
                     '（b5_xtable_scope.md §2.2 旁证）')
    else:
        chain_rec_key = f'skilllist|{chain_id}|{chain_layer}|ability=1017'
        via = f'经 supporterskill.abi{chain_pos[1]} 关联（段位↔abi0/abi1 位置序）'
        numeric_source = (f'模板推断（批 5 跨表：supporterskill.abi{chain_pos[1]}'
                          f'→skilllist|{chain_id}|{chain_layer}）')
        belonging = ('supporterskill 段位↔abi0/abi1 位置序＋子记录语义一致（非逐字）'
                     '（b5_xtable_scope.md §2.4；B5-R02 口径修正：121009 正文与句义一致但'
                     '非逐字同文，不称「自文一致性」）')
    mask_note = _mask_note(chain_record)
    self_text = (chain_record.get('text') or '').strip()
    answers = []
    claimed = set()
    for attr in attrs:
        field = ATTR_FIELD[attr]
        rule = R.rule_for('skilllist', 1017, '/' + field)
        value = chain_record.get(field)
        verdict, direction_text = TYPE8._direction_check(field, value)
        converted = R.answer_for('skilllist', 1017, '/' + field, value, chain_record)
        evidence_dir, evidence_files = PILOT1017._field_evidence(field)
        scope = _scope_note(field, chain_id, chain_layer)
        claimed.add(field)
        # B5-R04（批5审查）：supporterskill 行（121009，APK）不在 param 规则已核样本域内——
        # 值行 conditions 追加「规则级适用范围（本行域外）」限定；job 行（65000002 在域内）不变。
        conditions_value = converted.get('conditions')
        if table == 'supporterskill':
            conditions_value = ((conditions_value + '；') if conditions_value else '') + \
                '规则级适用范围（本行域外）：' + scope
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=value, field_path='/' + field,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B5_SCOPE,
            rule_key=f'skilllist|1017|/{field}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), conditions=conditions_value,
            rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=chain_id, layer=chain_layer,
                        record_key=chain_rec_key),
            note=(f'模板批 5 跨表 type1017 值行（来源记录＝{chain_rec_key}，{via}）；'
                  f'句中「{attr}」→/{field} 1:1 映射；规则键 skilllist|1017|/{field}；'
                  f'原值 {value}；方向审核 {direction_text}；证据目录 {evidence_dir}；'
                  f'对象审核 {mask_note}；适用范围：{scope}'
                  + ('；本项中性（原值 1）' if value == 1 else '')
                  + (f'；链记录正文旁证——语义一致（非逐字）（B5-R02）：「{self_text}」' if self_text else
                     '；链记录无自有正文')),
            quantitative=True))

    # --- 晋级行注记（不改变「推断」档位） --------------------------------------------------
    extra = []
    extra.append('跨记录归属依据（scope §5.5-4）：句→记录归属为数据侧结构对应——' + belonging +
                 '；sub/link 关联的引擎侧装载路径无原生核实')
    extra.append('不跨记录合并（scope §6.2）：本行值行仅含来源记录 ' + chain_rec_key +
                 ' 的参数换算，不与链上其他记录、30236 基线 A 行或同卡其他 skill 记录的值合并/连乘')
    unclaimed = []
    for key in sorted(chain_record):
        if not re.match(r'^(param|iParam|iparam|skillparam|flag|skillflag)\d+$', key):
            continue
        if key in claimed or key in ('iParam0', 'param0'):
            continue
        value = chain_record[key]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            unclaimed.append(f'/{key}={value}' + ('（未被本句主张，原值中性）' if value == 1 else ''))
    if unclaimed:
        extra.append('链记录句外参数未分配（不归属本句，仅登记原值；param1/2/3 未主张者均中性，'
                     '无未主张活性槽——scope §5.4）：' + '、'.join(unclaimed))
    param0 = chain_record.get('param0')
    if param0 is not None:
        extra.append(f'param0（提供者自身参与开关）原值 {param0}；只做注记，本轮不裁决')
    if section_count is not None and section_count > 1:
        extra.append(f'本记录另含其他◆段（共 {section_count} 段），其效果未被本句消费、本轮不归属'
                     '（INFR-05 多段披露；段数≠链 skill_ids 数时不逐段对应）')
    others = _others_disclosure(table, skill_refs, chain_pos)
    if others:
        extra.append('链上其余位置记录（未被本句消费、本轮不归属，位置旁证口径同 scope §2.2）：'
                     + '、'.join(others))
    scope_parts = [_scope_note('param1', chain_id, chain_layer)]
    if 'param2' in claimed:
        scope_parts.append(_scope_note('param2', chain_id, chain_layer))
    summary = (B5_TAG + '：行记录（' + table + '）自身无参数槽，严格句值行来源＝' + chain_rec_key +
               '（' + via + '；段位 ' + str(section_no) + '↔链位置 ' + chain_pos_desc + '）；'
               '值行全部「推断」，不升「确认」，不进入整行确认。跨记录归属依据：句→记录归属为'
               '数据侧结构对应——' + belonging + '；sub/link 关联的引擎侧装载路径无原生核实。'
               '适用范围披露：' + '；'.join(scope_parts) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject, attrs=[a for a in attrs], table=table,
                chain_record_id=chain_id, chain_layer=chain_layer,
                section_no=section_no, section_count=section_count)


def evaluate(record: dict, frag: str, table: str, layer: str | None = None, record_id=None,
             text: str | None = None, skill_refs=None):
    """对一行做批 5 跨表审核，返回 None（不属本批范围）或审核结果 dict。

    table：行记录表（'job_ability'/'supporterskill'）；layer／record_id：行记录来源层与 id；
    text：行记录正文字段全文（clean 后）；skill_refs：link 层该 entry 的 skilllist 引用
    （job_ability＝skill_ids[i] 位置序；supporterskill＝abi0/abi1 位置序）。

    结果 dict：kind='promote'（answers/summary_reason/extra_reasons）或 'hint'（reasons）。
    """
    if table not in TABLES or not isinstance(record, dict):
        return None
    match = PILOT1017.STRICT_PATTERN.match(frag)
    if not match:
        return None
    # INFR-06：全/半角尖括号占位归一后判定（试点同法；归一只改判定口径，不改变原文）。
    subject = match.group(2).replace('＜', '<').replace('＞', '>')
    attrs = list(dict.fromkeys(re.findall(r'攻撃力|防御力|移動速度', frag)))

    # --- 句位/段位/同文次数/句后文本（试点公式＋TYPE8 同口径 helpers） ---------------------
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    body = body[:cut] if cut >= 0 else body
    starts = TYPE8._occurrences(body, frag) if body else []
    if not starts:
        return None  # 正文不可用/句不在正文：句位无法核验，交既有口径（审计行集内无此类）
    pos = starts[0]
    section_no = _pilot_section_no(body, pos)
    first = body.find('◆')
    head = body[:first] if first >= 0 else body
    section_count = body.count('◆') + (1 if head.strip(' \r\t\n') else 0)
    trailing = TYPE8._trailing(body, pos, frag)

    # --- 通用句级归属排除（audit classify_rows 同序） --------------------------------------
    reasons = []
    if len(starts) > 1:
        reasons.append(f'同文在记录正文出现 {len(starts)} 次（第 '
                       + '、'.join(str(_pilot_section_no(body, p)) for p in starts)
                       + ' 段），句级归属歧义')
    if trailing:
        reasons.append('同段句后有后续文本（条件扩展/其他效果），其与链记录参数的归属未核实'
                       '（批 3 §4「句后条件扩展」同款保守排除）；句后文本原文：「' + trailing + '」')
    if subject.endswith('所属'):
        reasons.append(f'占位符「{subject}」是所属（出身）限定，所属→接受者映射无已确认规则，'
                       '本批无证据裁决对象位图')

    # --- 链解析（scope §5.2；逐行重验段位↔链位置对应） -------------------------------------
    refs = _chain_refs(table, skill_refs)
    chain_record = None
    chain_id = None
    chain_layer = None
    chain_pos = None
    chain_pos_desc = None
    si0 = section_no - 1
    if table == 'job_ability':
        skill_ids = record.get('skill_ids') or []
        ref = refs.get(('pos', si0))
        sid = skill_ids[si0] if si0 < len(skill_ids) else None
        if sid is None or ref is None:
            reasons.append(f'段位 {section_no} 无对应链位置（skill_ids 位置缺失或 link 层引用未解析；'
                           '段数≠skill_ids 数时段位↔位置对应不成立，scope §2.2 披露点）')
        elif ref.get('reference_id') != sid:
            reasons.append(f'段位↔链位置对应不一致（skill_ids[{si0}]={sid} 与 link 层引用 '
                           f"{ref.get('reference_id')} 不符），保守留 hint")
        else:
            chain_pos = ('pos', si0)
            chain_pos_desc = f'skill_ids[{si0}]'
            chain_record = ref.get('record') or {}
            chain_id = ref.get('reference_id')
            chain_layer = ref.get('layer')
            ability = chain_record.get('ability')
            if ability != 1017:
                reasons.append(f'段位↔skill_ids 位置对应记录 skilllist|{chain_id}|{chain_layer} '
                               f'ability={ability}≠1017，无 skilllist|1017 规则可映射，保守留 hint')
    else:
        ref = refs.get(('abi', si0))
        chain_pos_desc = f'abi{si0}'
        if ref is None:
            reasons.append(f'段位 {section_no} 无对应 abi 子记录（link 层仅引用 abi0/abi1；'
                           '段↔abi 位置对应缺失）')
        else:
            chain_pos = ('abi', si0)
            chain_record = ref.get('record') or {}
            chain_id = ref.get('reference_id')
            chain_layer = ref.get('layer')
            ability = chain_record.get('ability')
            if ability != 1017:
                self_text = (chain_record.get('text') or '').strip()
                reasons.append(f'位置对应 abi 子记录 skilllist|{chain_id}|{chain_layer} '
                               f'ability={ability}，该类型无本句属性的已确认规则'
                               + (f'（子记录自文：{self_text[:40]!r}）' if self_text else ''))

    # --- 对象位图＋属性方向＋未主张活性槽审核（chain 就绪时；scope §5.3/§5.4） --------------
    if chain_record is not None:
        mask_raw = chain_record.get('iParam0')
        mask = PILOT1017._decode_mask(mask_raw) if mask_raw is not None else None
        mask_note = _mask_note(chain_record)
        mask_ok = False
        if subject in ('味方', '<味方>'):
            mask_ok = (mask is not None and (mask & FULL_MASK) == FULL_MASK
                       and not (mask & ~FULL_MASK))
            if not mask_ok:
                reasons.append('「味方」句对象位图未覆盖玩家职业全集或含未解释高位（要求 bits 0..4 '
                               '全置位且无高位）：' + mask_note)
        elif not subject.endswith('所属'):
            reasons.append(f'占位符「{subject}」的职业名→位映射缺证据（JobType 枚举外），'
                           '本批无证据裁决对象位图')
        if mask_ok:
            vals = []
            for attr in attrs:
                field = ATTR_FIELD[attr]
                value = chain_record.get(field)
                verdict, direction_text = TYPE8._direction_check(field, value)
                if verdict == 'invalid':
                    reasons.append(f'{attr}（/{field}）链记录缺有限原值（{value!r}），保守留 hint')
                    break
                if verdict == 'conflict':
                    reasons.append(f'{attr}（/{field}={value}）方向冲突（{direction_text}），保守留 hint')
                    break
                vals.append((attr, field, value))
            else:
                # 未主张活性槽（批 4 P-D 同款）：param1/2/3 中未主张者必须中性。
                unclaimed_active = [f'/{f}={chain_record.get(f)}' for f in ('param1', 'param2', 'param3')
                                    if f not in {x[1] for x in vals}
                                    and isinstance(chain_record.get(f), (int, float))
                                    and not isinstance(chain_record.get(f), bool)
                                    and chain_record.get(f) != 1]
                if unclaimed_active:
                    reasons.append('链记录存在句中未主张的活性槽（文本与记录分工不一致，批 4 P-D 同款'
                                   '保守留 hint）：' + '、'.join(unclaimed_active))
                elif not reasons:
                    return _promote(record, frag, table, layer, record_id, body, pos, section_no,
                                    section_count, subject, attrs, chain_record, chain_id,
                                    chain_layer, chain_pos, chain_pos_desc, skill_refs)
    if not reasons:
        reasons.append('本句所有属性均无可推断数值')
    return dict(kind='hint', reasons=reasons, subject=subject, attrs=attrs, table=table,
                section_no=section_no, section_count=section_count, trailing=trailing)
