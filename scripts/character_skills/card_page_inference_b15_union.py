"""模板作用域推断层——批 15：t13 槽 ∪ 2012 暴击链并集归属（批 6×批 8/14 跨批衔接断点修复）。

设计与范围依据：整改任务书 ``docs/tasks/20261022-character-skills-goal-rectification-prompt.md``
§三.3（修复批 6 与批 8/14 组合的选择/合并/待办传播规则，通用规则覆盖同类描述）；任务卡
``docs/tasks/20261022-character-skills-goal-rectification.md`` P2；第三方审查
``output/character_skills/review/independent_20261022_codex_b14/GOAL_ALIGNMENT.md`` G01
（cid349/cid6335：批 8/14 补暴击段后，同句非暴击段无任何待办踪迹——断点根因＝批 6 G4
「句含クリティカル属性→整行留 hint」（card_page_inference_b6_bossbuff.py:33,317-319）
＋批 8/14 只消费 skilllist|2012|/param4|/param5（card_page_inference_b8_crit2012.py:574-576），
无环节回评非暴击段）。

通用规则（唯一规则，覆盖全部同类描述，非逐 cid 手工补丁）：

* **触发前提**：本行已由批 8/14 经 s_ability→2012 链出暴击值行（``crit_promotion.kind==
  'promote'`` 且 relay_type==13），且批 6 对本行留 hint（或不在批 6 范围）；
* **并集归属门（全部通过才晋级；任一不过→返回 hint 并登记具体缺口，不猜）**：
  * **U1 crit 覆盖核对**：句面 crit 主张全部已被批 8/14 值行兑现（``claims``）；
  * **U2 归属载体＝批 6 同一条链**：父记录唯一 type13 子记录（G2 同法；charainfo 行经
    同页同文 pattern 记录 G5 同法）；中继须与批 8/14 所用 t13 中继同记录（不同→链歧义
    hint）；
  * **U3 并集形状（双向）**：t13 非 crit 活性槽 {p1,p2,p6 原值≠0} == 句非 crit 主张槽
    （攻撃力→p1、防御力→p2、移動速度→p6）；时长主张（一定時間）⇔ p3≠0——
    ``B6._gate_parent(..., has_crit=False)`` 承接批 6 原形状门与残余门（G7 同文一次/
    fam1 多句/fam11·fam13 竞争/G6 竞争句检测），一刀切 G4 仅在本门内解除；
  * **U4 方向**：句为「上がる」方向；非 crit 槽与时长槽原值>0（负值→hint，批 6 §5.4）；
  * **U5 fam 冲突（非 FAM1 句）**：句非批 6 家族时，父记录不得另有 fam1/fam11/fam13
    句（t13 可能被其主张）；
* **归属产出**：按属性分别归属——非 crit 属性与时长值行来自 t13 skillparam 槽
  （rules.json ``bossskill|13|/skillparam1|2|3|6`` 现行 conversion，批 6 已确认规则；
  D1 裁决：时长值行归 t13 /skillparam3，不消费 2012 载体 param0）；暴击值行维持批 8/14
  既有答案不动；每答案各注来源载体与层，不合并不乘积；一行内两组值行并存、
  互不换算。

硬边界（逐行强制）：

* **只升「推断」，绝不升「确认」**：值行 numeric_evidence/association_evidence 一律
  「推断」；行级标注 ``B15_TAG``、evidence_scope=TEMPLATE_BATCH15_UNION、行级键
  ``inference_b15``（行级替换 inference_b6_hint/批 14 让渡注记——不残留 hint 键、
  不双登记，原注记记入元数据 ``b6_yield_note_replaced``；批 14/批 8 先例同法）；
  「唯一 t13＋并集形状匹配」是数据侧结构对应，引擎侧装载路径无原生核实，永不升「确认」。
* **规则本体与本条归属分层披露**（rule_body_status 分层）：值行 note 固定写明
  「规则本体：已确认（静态及受控原生局部规则）——指规则本身；本条数值归属＝推断
  （模板批 15 并集归属），不升确认」。
* **批 8/14 既有答案零触碰**：本批不修改、不撤销任何 2012 链值行；跨行 hint 键零触碰。
* **证据按字段**（INFR-01）：值行 evidence 取 rules.json bossskill|13|/skillparamN 的
  evidence（p1/p3/p6→output/boss_heal 字典；p2→output/boss_chain/type13_basis），
  存在性检查缺失显式失败（B6._field_evidence 复用）。
* **样本域披露**（INFR-02）：B6._sample_domain_note 同法按 rules.json 登记口径。
* **槽位登记**：t13 句外槽（含 s_ability/crit 槽 p4/p5）原值照实登记不分配。
* **hint 行同样不双登记（DeepSeek 整改审查 DS-GR-06 修复，20261023）**：并集归属不成立
  的 hint 行，批 6 hint 键同样行级并入——不残留独立 ``inference_b6_hint`` 键，批 6 原注记
  文本并入 ``inference_b15_hint``（由 card_page_data.py hint 写出分支执行）；键级口径
  「每行至多一个 hint 键承载批 6 信息」对晋级行与 hint 行一致。
"""
from __future__ import annotations

import collections
import re

import rules as R
import card_page_inference_b6_bossbuff as B6

B15_TAG = '推断（模板批 15 并集归属：t13 槽∪2012 暴击链）'
B15_SCOPE = 'TEMPLATE_BATCH15_UNION'
B15_FAMILY = ('味方全体の⟨ATTR⟩（含 crit）が一定時間上がる。——批 8/14 已出 crit 值行的行，'
              '非 crit/时长主张由同链 t13 活性槽并集归属（批 6 G4 一刀切的并集解除）')

_G4_MARK = '句含クリティカル属性'
_UNMAPPED_MARK = '无映射属性'


def _case_a(b6_result):
    """批 6 G4 一刀切 hint（可被并集解除）：唯一原因是 G4 或 G4＋无映射属性披露。"""
    if not b6_result or b6_result.get('kind') != 'hint':
        return False
    reasons = b6_result.get('reasons') or []
    return bool(reasons) and all(
        _G4_MARK in r or _UNMAPPED_MARK in r for r in reasons)


def _union_value_row(attr, param, raw, child, child_key, parent_chain, crit_chain_desc,
                     crit_prom, via_desc, slot_desc, sent_no, sent_total, section_no,
                     section_count, dur=False):
    rule = R.rule_for('bossskill', 13, '/' + param)
    converted = R.answer_for('bossskill', 13, '/' + param, raw, child)
    evidence_dir, evidence_files = B6._field_evidence(param)
    attr_label = B6.DUR_ATTR if dur else attr
    chain_desc = f'{parent_chain}→{child_key}'
    numeric_source = (f'模板推断（批 15 并集归属：非 crit/时长段←{chain_desc}；'
                      f'crit 段←{crit_chain_desc}）')
    note = (
        f'模板批 15 并集归属值行（{("时长" if dur else "非 crit 属性")}段；来源载体＝'
        f'{child_key}，bossskill type13；父链 {parent_chain}）；句中「{attr_label}」→'
        f'/{param} 1:1 映射；规则键 bossskill|13|/{param}；原值 {raw}；方向审核 '
        f'{B6._direction_text(param, raw)}；证据目录 {evidence_dir}；'
        f'对象「{crit_prom.get("subject") or "味方全体"}」为句面依据，该 type13 处理器的'
        f'接受者选择逻辑无已确认规则（{B6._iparam_note(child)}）；'
        f'样本域：{B6._sample_domain_note(param, rule)}；{slot_desc}；'
        f'并集归属：句主张属性集＝t13 非 crit 活性槽∪批 8/14 2012 暴击链，按属性分别归属'
        f'——本值为非 crit/时长段（t13 槽）；crit 段由本行既有批 8/14 值行兑现'
        f'（{crit_chain_desc}，证据 scope {crit_prom.get("evidence_scope","TEMPLATE_BATCH8_CRIT2012")}），'
        '两组值行不合并不乘积；时长单位为游戏秒（D1 裁决：时长值行归 t13 /skillparam3，'
        f'不消费 2012 载体 param0）；本条数值归属＝推断（模板批 15 并集归属），'
        '引擎侧装载路径无原生核实，不升确认'
        + (f'；正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）'
           if sent_no else '；正文句序未能定位')
        + (f'；◆ 段：第 {section_no}／共 {section_count} 段（◆段口径不传达句序）'
           if section_no else ''))
    return dict(
        value=converted['value_text'],
        quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
        raw_value=raw, field_path='/' + param,
        numeric_source=numeric_source, numeric_evidence='推断',
        association_evidence='推断', evidence_scope=B15_SCOPE,
        rule_key=f'bossskill|13|/{param}',
        rule_body_status=rule.get('status'), rule_status=rule.get('status'),
        conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
        conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
        evidence=list(evidence_files),
        source=dict(table='bossskill', record_id=child.get('record_id'),
                    layer=child.get('layer'), record_key=child_key),
        note=note, quantitative=True)


def evaluate(record: dict, frag: str, table: str, layer: str | None = None, record_id=None,
             text: str | None = None, data=None, cid=None, boss_skill_refs=None,
             b6_result=None, crit_promotion=None):
    """批 15 并集归属审核。

    前提（由 card_page_data 调用点保证）：批 8/14 已对本行出 crit 值行
    （``crit_promotion.kind=='promote'``）；批 6 对本行留 hint 或不在批 6 范围。
    返回 None（无并集工作可做）或 dict(kind='promote'|'hint')。
    """
    if data is None or cid is None or table not in B6.TABLES or not isinstance(record, dict):
        return None
    crit = crit_promotion
    if (not crit or crit.get('kind') != 'promote' or crit.get('relay_type') != 13
            or not crit.get('relay_record_id')):
        return None
    template = B6._norm_text(frag)
    fam = B6._family_of(template)
    case = 'A' if _case_a(b6_result) else 'B'
    if case == 'A' and fam != B6.FAM1:
        return None  # G4 解除只对批 6 家族句成立；异常形态不猜
    if case == 'B' and fam == B6.FAM1:
        return None  # FAM1 句批 6 留 hint 但非 G4 原因（形状/竞争等）——批 6 原门维持
    attrs = [a for a in B6._ATTR_DETECT if a in template]
    noncrit = [a for a in attrs if a in B6.ATTR_PARAM]
    # 裸「クリティカル」是「クリティカル発生率/威力」的子串（b6 _ATTR_DETECT 同法逐字包含），
    # 不构成独立主张；仅当句只有裸「クリティカル」（発生率/威力未区分）时并集无法核对覆盖。
    crit_attrs = [a for a in attrs if a.startswith('クリティカル') and a != 'クリティカル']
    bare_crit = ('クリティカル' in attrs) and not crit_attrs
    dur_claimed = B6.DUR_ATTR in frag
    if not noncrit and not dur_claimed and not crit_attrs and not bare_crit:
        return None
    # U1：crit 覆盖核对（句 crit 主张须全部被批 8/14 值行兑现）
    claims = crit.get('claims') or {}
    missing = [a for a in crit_attrs if not claims.get(a)]
    if missing or bare_crit:
        msg = (['并集不完整（U1）：句 crit 主张 %s 未被批 8/14 值行兑现' % '、'.join(missing)]
               if missing else
               ['并集不完整（U1）：句 crit 主张仅裸「クリティカル」（発生率/威力未区分），'
                '无法核对批 8/14 覆盖'])
        return dict(kind='hint', case=case, subject=crit.get('subject'),
                    attrs=attrs, table=table, reasons=msg)
    # 方向门（U4 前置）：并集归属只解「上がる」增益句
    if not re.search(r'上がる|上がり|上げる', frag):
        return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                    table=table, reasons=['并集归属方向门（U4）：句无「上がる」增益方向词'])

    ctx = B6._page_ctx(data, cid)
    # 父记录/同文数/竞争句（批 6 同法；charainfo 经 G5 同文 pattern）
    if table == 'charainfo':
        matched = [(e, frags) for e, frags in ctx['pattern_frags'] if frag in frags]
        pat_ids = {(str(e.get('reference_id')), e.get('layer')) for e, _ in matched}
        if not matched or len(pat_ids) > 1:
            return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                        table=table,
                        reasons=['并集归属链不可达（U2/G5）：charainfo 行同文 pattern 记录'
                                 + ('缺失' if not matched else '不唯一（归属歧义）')])
        pe = matched[0][0]
        pkey = ('bosspattern', str(pe.get('reference_id')), pe.get('layer'))
        parent = ctx['rec_index'].get(pkey)
        ptext = str((pe.get('record') or {}).get('sinfo', '') or '').replace('\\n', '\n')
        cut = ptext.find('[i][c]')
        wb = ptext[:cut] if cut >= 0 else ptext
        same_count = ptext.count(frag.strip())
        parent_chain = f'charainfo|{record_id}|{layer}→同页同文 bosspattern|{pe.get("reference_id")}|{pe.get("layer")}'
        parent_bsr = pe.get('boss_skill_refs')
        via_desc = (f'charainfo 行经同页同文 bosspattern 记录（自身 skillparam* 为伤害侧'
                    '未执行副本，不消费）')
    else:
        pkey = (table, str(record_id), layer)
        parent = ctx['rec_index'].get(pkey)
        body = (text or '').replace('\\n', '\n')
        cut = body.find('[i][c]')
        wb = body[:cut] if cut >= 0 else body
        same_count = body.count(frag.strip())
        parent_chain = f'{table}|{record_id}|{layer}'
        parent_bsr = boss_skill_refs
        via_desc = '行记录自身 type13 子记录'
    if parent is None:
        return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                    table=table,
                    reasons=['并集归属链不可达（U2）：父记录 %s 未定位' % (pkey,)])
    # U5（非 FAM1 句）：t13 不得被父记录上的批 6 家族句主张
    if case == 'B':
        famc = ctx['fam_counts'].get(pkey, collections.Counter())
        if famc.get(B6.FAM1) or famc.get(B6.FAM11) or famc.get(B6.FAM13):
            return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                        table=table,
                        reasons=['并集归属冲突（U5）：父记录另有批 6 家族句（%s），唯一 t13 '
                                 '可能被其主张，归属不能唯一化解'
                                 % '、'.join(f'{k}×{v}' for k, v in famc.items())])
    # U2/U3/U4 残余门：批 6 同一门（G2 唯一 t13→G3 并集形状→p3→G7 同文→fam→竞争句），
    # has_crit=False 使 G4 一刀切不再阻断；非 crit 主张槽 = 并集形状门。
    competitors = B6._competing_ally_buffs(wb, noncrit)
    sub_reasons, child = B6._gate_parent(parent, noncrit, False, same_count,
                                         ctx['fam_counts'].get(pkey, collections.Counter()),
                                         competitors)
    if child is None:
        return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                    table=table,
                    reasons=['并集归属不成立（批 15 复核批 6 残余门，槽缺/形状不符/多载体/'
                             '同文多次/竞争句——保留具体缺口）：' + '；'.join(sub_reasons)])
    # 中继一致性（U2）：批 6 链上的 t13 与批 8/14 所用中继须同记录
    if str(child.get('record_id')) != str(crit.get('relay_record_id')):
        return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                    table=table,
                    reasons=['并集归属链歧义（U2）：批 6 链 t13（bossskill|%s|%s）与批 8/14 '
                             '中继（bossskill|%s）不同记录，不猜'
                             % (child.get('record_id'), child.get('layer'),
                                crit.get('relay_record_id'))])
    # U4 方向/负值门：非 crit 槽与时长槽原值>0
    raws = {q: B6._raw_of(child, q) for q in ('skillparam1', 'skillparam2', 'skillparam6',
                                              'skillparam3')}
    neg = [q for q, v in raws.items() if B6._num(v) and v <= 0
           and (q != 'skillparam3' or dur_claimed)]
    neg = [q for q in neg if q in {B6.ATTR_PARAM[a] for a in noncrit} | {B6.DUR_PARAM}]
    if neg:
        return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                    table=table,
                    reasons=['方向冲突（U4）：槽 %s 原值 %s 非正，句称上升；批 6 §5.4 保守留 hint'
                             % ('、'.join(neg), {q: raws[q] for q in neg})])

    # --- 归属产出：非 crit 属性＋时长值行（t13 槽）；crit 段由批 8/14 既有值行兑现 ---------
    child_id = child.get('record_id')
    child_layer = child.get('layer')
    child_key = f'bossskill|{child_id}|{child_layer}'
    crit_chain_desc = (f"批 8/14 2012 链：bosspattern|{crit.get('pattern_record_id')}"
                       f"→bossskill|{crit.get('relay_record_id')}(type13,slot "
                       f"{crit.get('relay_slot')})→s_ability→skilllist|"
                       f"{crit.get('carrier_record_id')}|{crit.get('carrier_layer')}"
                       '(ability2012)')
    slot = None
    for r in parent_bsr or []:
        if r.get('table') == 'bossskill' and str(r.get('reference_id')) == str(child_id):
            slot = r.get('slot')
            break
    slot_desc = (f'bossskill 子记录经父记录 boss_skill_refs 槽位 {slot} 引用'
                 if slot else 'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）')
    section_no = crit.get('section_no') if crit.get('section_no') is not None \
        else (b6_result or {}).get('section_no')
    section_count = crit.get('section_count') if crit.get('section_count') is not None \
        else (b6_result or {}).get('section_count')
    answers = []
    claimed_slots = set()
    for attr in noncrit:
        param = B6.ATTR_PARAM[attr]
        raw = raws[param]
        if not (B6._num(raw) and raw != 0):
            return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                        table=table,
                        reasons=[f'形状不符（U3）：句主张「{attr}」但槽 /{param} 不活性'
                                 f'（{raw!r}）——缺失不补 0'])
        claimed_slots.add(param)
        answers.append(_union_value_row(attr, param, raw, child, child_key, parent_chain,
                                        crit_chain_desc, crit, via_desc, slot_desc,
                                        crit.get('sent_no'), crit.get('sent_total'),
                                        section_no, section_count))
    if dur_claimed:
        raw = raws[B6.DUR_PARAM]
        if not (B6._num(raw) and raw != 0):
            return dict(kind='hint', case=case, subject=crit.get('subject'), attrs=attrs,
                        table=table,
                        reasons=[f'形状不符（U3）：句主张「{B6.DUR_ATTR}」但时长槽 '
                                 f'/{B6.DUR_PARAM} 无非零值（{raw!r}）'])
        claimed_slots.add(B6.DUR_PARAM)
        answers.append(_union_value_row(None, B6.DUR_PARAM, raw, child, child_key,
                                        parent_chain, crit_chain_desc, crit, via_desc,
                                        slot_desc, crit.get('sent_no'),
                                        crit.get('sent_total'), section_no, section_count,
                                        dur=True))
    # --- 行注记 ---------------------------------------------------------------------------
    extra = []
    extra.append('并集归属依据（批 15）：句主张属性集＝' + ('、'.join(attrs) or '（无）')
                 + '；t13 非 crit 活性槽 ' + str(sorted(q for q in ('skillparam1', 'skillparam2',
                                                                    'skillparam6') if B6._num(raws[q]) and raws[q] != 0))
                 + '∪批 8/14 2012 暴击链（p4/p5）覆盖全部主张；按属性分别归属，两组值行'
                 '不合并不乘积；引擎侧装载路径无原生核实，全部「推断」不升「确认」')
    extra.append('批 8/14 既有 crit 值行零触碰：本批只新增非 crit/时长值行（来源 t13 槽）；'
                 'crit 段见本行既有 2012 链值行（各自注来源载体与层）')
    unclaimed = []
    for u in (child.get('answers') or []) + (child.get('unexplained') or []):
        f = u.get('f') or ''
        # DS-GR-05 修复（20261023）：原正则 r'/skill(param\d+|flag\d+_?\d*)' 把 '/skillparam1'
        # 切成 group('param1')——与 claimed_slots 的完整槽名（skillparam1 等）永不相同，导致
        # 本行已由并集归属分配的槽被重复列入「句外槽未分配」（与本行已分配槽自相矛盾，
        # 482/482 晋级行可见）。改为捕获完整字段名（param/iParam/iparam/skillparam/
        # skillflag/flag 全形），与 claimed_slots 按完整槽名比对。
        m = re.fullmatch(r'/(param\d+|iParam\d+|iparam\d+|skillparam\d+|skillflag\d+|flag\d+_?\d*)', f)
        if not m or m.group(1) in claimed_slots:
            continue
        unclaimed.append(f'{f}={u.get("raw")!r}' + ('（原值 0，未被本句主张）' if u.get('raw') == 0 else ''))
    if unclaimed:
        extra.append('t13 子记录句外槽未分配（不归属本句，仅登记原值；crit 槽 p4/p5 由 2012 链'
                     '消费）：' + '、'.join(dict.fromkeys(unclaimed)))
    summary = (B15_TAG + '：非 crit/时长值行来源＝' + parent_chain + '→' + child_key
               + '（t13 活性槽并集归属；' + via_desc + '）；crit 值行＝批 8/14 既有 2012 链'
               '值行（零触碰）。值行全部「推断」，不升「确认」，不进入整行确认。'
               + '；'.join(extra))
    return dict(kind='promote', case=case, answers=answers, summary_reason=summary,
                extra_reasons=extra, subject=crit.get('subject') or '味方全体',
                attrs=attrs, crit_attrs=crit_attrs, noncrit_attrs=noncrit,
                dur_claimed=dur_claimed, table=table,
                parent_chain=parent_chain,
                chain_record_id=child_id, chain_layer=child_layer, chain_key=child_key,
                crit_pattern_record_id=crit.get('pattern_record_id'),
                crit_relay_record_id=crit.get('relay_record_id'),
                crit_relay_type=crit.get('relay_type'),
                crit_relay_slot=crit.get('relay_slot'),
                crit_carrier_record_id=crit.get('carrier_record_id'),
                crit_carrier_layer=crit.get('carrier_layer'),
                crit_promotion_key=('inference_b14' if crit.get('b14_ext') else 'inference_b8'),
                replaces_hint='inference_b6_hint' if case == 'A' else None,
                b6_yield_note_replaced=('；'.join(b6_result['reasons']) if case == 'A' else None),
                sent_no=crit.get('sent_no'), sent_total=crit.get('sent_total'))
