"""模板作用域推断层——批 17：P0 断点收尾（三族规则改动一次落地＋P2 溢出）。

设计与范围依据：批 16 选题审计
``output/character_skills/inference_inventory/b16_backlog_audit_scope.md``（P0 182 项＝
59 行三族分诊＋P2 溢出 75 行）＋逐行明细 ``work/character_skills_b16_audit/
p0_triage.json``；批 15 硬边界 ``card_page_inference_b15_union.py:34-53``；批 6 G6/
ATTR_PARAM 槽词表 ``card_page_inference_b6_bossbuff.py:325-331,145``。H2 时长路径经
主持 D1 级裁决（2026-10-23）：采方案①时长槽共享（与批 15 D1「时长值行归 t13
/skillparam3、不消费 2012 载体 param0」一致）。

四条路径（同一 evaluate 分派；全部保持「推断」档，绝不升「确认」）：

* **H1/P2 槽位分区**（H1＝31 行 FAM1+crit×FAM11 词表外属性竞争句；P2 溢出＝b6 hint
  fam11/13 冲突 45 行＋同属性竞争句 30 行中适用者）：批 6 G6/批 15 U5 从「存在竞争句
  即 hint」升级为**槽位分区**——竞争句（FAM11/FAM13 家族句＋G6 扩展同属性竞争句）的
  属性主张按 ATTR_PARAM 词表（card_page_inference_b6_bossbuff.py:145，仅攻/防/移）
  映射后与 t13 非 crit 活性槽**不相交**时，竞争句结构上不能持有该 t13 任何槽；再加
  **t13 全字段复核**（已分配槽＝本行非 crit 主张槽∪时长槽∪{p4,p5}（crit 主张已由
  2012 链消费时）之外无非零槽）→ 竞争句载体非本 t13、其「一定時間」随其载体走 →
  本行获 t13 全活性槽＋/skillparam3 时长值行（推断档）。分区不成立或全字段复核出
  已分配槽外非零槽 → inference_b17_hint 记具体缺口（不硬配）。
* **H2 时长槽共享**（27 行条件暴击句，Y.G. 0）：唯一未解＝継続時間。**主持 D1 级
  裁决＝时长槽共享**：本行时长值行引同一 t13 /skillparam3（同一支援施加的时长；
  句面「も」＝同 buff 追加语义），注记「槽共享／各注来源／不合并不乘积」，与批 15
  D1 裁决一致（不消费 2012 载体 param0）。硬前提（逐行复验，任一不满足→hint 不硬配）：
  ①同记录兄弟 FAM1 行（味方全体句）已被批 6 以**同一 t13** 晋级（本批运行时对兄弟
  片段真实重放 B6.evaluate 复验）；②本行 2012 载体 param0 原值与 t13 p3 原值一致
  （数值/float32 精度相等）——两值不一致的行留 hint 并逐字披露两值。
* **MULTI_T13 denju patternid 映射**（20510 P0 1 行/4 效果；2320/10210 P2 各 4 效果；
  charainfo 行同法可解性未测、本批不做）：b6 G2 多 t13 歧义行，经 links
  ``denju_pattern_refs``（patternidN→bosspattern sinfo 含本行片段**唯一命中**）＋
  ``boss_skill_refs`` reference_field（``bosspattern[pid].skillidX`` 归属登记）确定
  唯一 t13 后按批 6 同门（形状/时长/方向/同文一次/fam 分区/全字段复核）出值；命中
  不唯一 → hint。

通用硬边界（批 15 :34-53 逐条沿用）：

* 只升「推断」，绝不升「确认」；行级键 ``inference_b17``（行级替换既有唯一 hint 键
  ``inference_b15_hint``/``inference_b6_hint``——不残留、不双登记，原注记逐字记入元
  数据 ``replaced_hint_text``/``b6_yield_note_replaced``）；evidence_scope=
  TEMPLATE_BATCH17_P0FINALE。
* 批 8/14 既有 crit 值行零触碰（crit provenance 记入本键 ``crit_chain``，批 15 先例）。
* 证据按字段（INFR-01，B6._field_evidence 复用）；样本域披露（INFR-02，B6 复用）；
  槽位登记（句外槽原值照实登记不分配）；不跨记录合并（槽共享仅指同一 t13 的
  /skillparam3 按裁决由两行各注来源引用，两行值行不合并不乘积）；同号跨命名空间
  不合并、不跨层取值（t13 子记录按其自身 layer 取值）。
* 值行逐行注明：规则本体已确认（静态及受控原生局部规则）——指规则本身；本条数值
  归属＝推断（模板批 17），引擎侧装载路径无原生核实，不升确认。
"""
from __future__ import annotations

import math
import re
import struct

import rules as R
import card_page_inference_b6_bossbuff as B6
import card_page_inference_type8 as TYPE8
from card_page_positions import fragment_positions

B17_TAG = '推断（模板批 17 P0 收尾：槽位分区/时长槽共享/denju patternid 映射）'
B17_SCOPE = 'TEMPLATE_BATCH17_P0FINALE'
B17_FAMILY = ('批 6/15 竞争句行与多 t13 行的收尾归属——槽位分区（竞争句映射主张槽与 t13 '
              '活性槽不相交＋全字段复核）、条件暴击行时长槽共享（D1 裁决）、denju '
              'patternidN→pattern 文本→t13 唯一映射')

_MULTI_T13_MARK = '个 type13 子记录（传授多 pattern）'
_FAM_MARK = '另有自身バフ/上げる句家族行'
_COMPET_MARK = '竞争 ally-buff 句'
_U5_MARK = '并集归属冲突（U5）'
_SLOT_RE = re.compile(r'/(param\d+|iParam\d+|iparam\d+|skillparam\d+|skillflag\d+|flag\d+_?\d*)')
# 任意 ally 主语竞争短语（批 6 _COMPET_SUBJ/_COMPET_RUN 复用；谓词扩 任意属性）
_COMPET_ANY = re.compile(
    r'(味方全体|範囲内の味方|味方|自身)の' + B6._COMPET_RUN + B6._COMPET_PRED)


def _reason_comp_class(reasons):
    """hint 原因是否为竞争句/家族句类（分区路径的调用资格——非竞争类原因的行不进
    本批，既有 hint 键零触碰，不产生对账噪声）。"""
    return any((_FAM_MARK in r) or (_COMPET_MARK in r) or (_U5_MARK in r) for r in reasons)


def _f32(x):
    """float32 回舍（B13-R02 同口径：表示差不记为值差）。"""
    return struct.unpack('f', struct.pack('f', float(x)))[0]


def _num_eq(a, b):
    """数值一致（原值或 float32 精度）。"""
    if isinstance(a, bool) or isinstance(b, bool):
        return False
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if not (math.isfinite(fa) and math.isfinite(fb)):
        return False
    return fa == fb or _f32(fa) == _f32(fb)


# 注记文本补全用的词表外属性（B17-R02 修复）：B6._ATTR_DETECT 不含、但 B6._ATTRS
# 家族属性词表内的属性词（如 H1 竞争句「自身の攻撃速度が一定時間上がる」的「攻撃速度」）。
# 仅用于注记文本逐字披露；**不进 ATTR_PARAM 映射**（映射槽集合不变，门判定零变化）。
# 「効果」为泛称不属属性主张，不入本表。
_ATTR_NOTE_EXTRA = tuple(a for a in ('通常攻撃威力', '攻撃間隔', '攻撃速度')
                         if a not in B6._ATTR_DETECT)


def _sent_attrs(text):
    """句面属性主张（批 6 _ATTR_DETECT 同法逐字包含）；映射槽按 ATTR_PARAM。
    注记文本补全（B17-R02）：词表外属性 _ATTR_NOTE_EXTRA 一并逐字写进 attrs，仅用于
    注记文本；mapped 仍只按 ATTR_PARAM（词表外→∅），门的 ∅ 映射语义零变化。"""
    t = B6._norm_text(text)
    attrs = [a for a in B6._ATTR_DETECT if a in t]
    attrs += [a for a in _ATTR_NOTE_EXTRA if a in t]
    return attrs, sorted({B6.ATTR_PARAM[a] for a in attrs if a in B6.ATTR_PARAM})


def _competitor_sents(wb, row_frag):
    """父记录正文上的竞争句清单（FAM11/FAM13 家族句＋任意 ally 主语（範囲内の味方/味方/
    自身）の「一定時間上がる/上がり」短语——批 6 G6 扩展检测的**任意属性**推广，供分区
    判定求交集；批 6 原检测只收同属性集合竞争句），排除本行自身句与味方全体 主语句
    （FAM1 双句已由 fam1_n 门覆盖）。返回 dict 列表（text/fam/attrs/mapped/dur/via）。"""
    out = []
    norm_row = B6._norm_text(row_frag).strip()
    seen = set()

    def _add(text, fam, via):
        nf = B6._norm_text(text)
        key = nf.strip()
        if key == norm_row or key in seen:
            return
        seen.add(key)
        attrs, mapped = _sent_attrs(text)
        out.append(dict(text=text, fam=fam, attrs=attrs, mapped=mapped,
                        dur='一定時間' in nf, via=via))

    for sp in fragment_positions(wb or ''):
        f = sp['japanese']
        nf = B6._norm_text(f)
        fam = B6._family_of(nf)
        if fam in (B6.FAM11, B6.FAM13):
            _add(f, fam, 'family')
            continue
        # 非家族整句：任意 ally 主语の⟨ATTR⟩が一定時間上がる/上がり 短语（G6 扩展推广）
        for m in _COMPET_ANY.finditer(nf):
            if m.group(1) == '味方全体':
                continue
            _add(f, '（G6 扩展 ally-buff 短语）', 'competitor_ext')
            break
    return out


def _locate_parent(frag, table, layer, record_id, text, data, cid, boss_skill_refs=None):
    """批 15 同法父记录定位。返回 (parent, pkey, wb, same_count, fam_counter,
    via_desc, parent_bsr, pattern_rec_key|None) 或 (None, None, None, None, None,
    None, None, None)＋错误原因由调用方经返回的 hint 组装（此处返回 err 文本）。"""
    ctx = B6._page_ctx(data, cid)
    if table == 'charainfo':
        matched = [(e, frags) for e, frags in ctx['pattern_frags'] if frag in frags]
        pat_ids = {(str(e.get('reference_id')), e.get('layer')) for e, _ in matched}
        if not matched or len(pat_ids) > 1:
            return None, None, None, None, None, None, None, None
        pe = matched[0][0]
        pkey = ('bosspattern', str(pe.get('reference_id')), pe.get('layer'))
        parent = ctx['rec_index'].get(pkey)
        ptext = str((pe.get('record') or {}).get('sinfo', '') or '').replace('\\n', '\n')
        cut = ptext.find('[i][c]')
        wb = ptext[:cut] if cut >= 0 else ptext
        same_count = ptext.count(frag.strip())
        via_desc = (f'charainfo|{record_id}|{layer}→同页同文 '
                    f'bosspattern|{pe.get("reference_id")}|{pe.get("layer")}')
        return (parent, pkey, wb, same_count, ctx['fam_counts'].get(pkey),
                via_desc, pe.get('boss_skill_refs'), f'bosspattern|{pe.get("reference_id")}|{pe.get("layer")}')
    pkey = (table, str(record_id), layer)
    parent = ctx['rec_index'].get(pkey)
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    same_count = body.count(frag.strip())
    via_desc = f'{table}|{record_id}|{layer}'
    return (parent, pkey, wb, same_count, ctx['fam_counts'].get(pkey),
            via_desc, boss_skill_refs, None)


def _full_field_review(child, claimed_slots, crit_claimed):
    """t13 全字段复核（批 17 新增门）：answers∪unexplained 中全部槽形字段里，
    已分配槽（非 crit 主张槽∪时长槽∪{p4,p5}（crit 主张已由 2012 链消费时））之外
    的非零槽 → 违例清单；零值槽与 p4/p5 照实登记不分配（批 6/15 槽位披露同口径）。"""
    claimed = set(claimed_slots) | {B6.DUR_PARAM}
    if crit_claimed:
        claimed |= {'skillparam4', 'skillparam5'}
    violations, zeros = [], []
    for u in (child.get('answers') or []) + (child.get('unexplained') or []):
        m = _SLOT_RE.fullmatch(u.get('f') or '')
        if not m:
            continue
        v = u.get('raw')
        if B6._num(v) and v != 0 and m.group(1) not in claimed:
            violations.append(f'{u["f"]}={v!r}')
        elif B6._num(v) and v == 0 and m.group(1) not in claimed:
            zeros.append(f'{u["f"]}={v!r}')
    return violations, sorted(claimed), zeros


def _partition_gate(parent, noncrit, same_count, fam_counter, competitors, crit_claimed):
    """槽位分区门（批 6 G2/G3/G7/fam1 原文复用；fam11/13/竞争句升级为分区判定；
    追加全字段复核）。返回 (reasons, child|None, info|None)。"""
    boss_kids = [c for c in parent.get('children') or [] if c.get('table') == 'bossskill']
    ets = [c.get('effect_type') for c in boss_kids]
    t13 = [c for c in boss_kids if c.get('effect_type') == 13]
    if not t13:
        return ['父记录无可解析的 type13 增益子记录（链上类型=%s）' % (ets,)], None, None
    if len(t13) > 1:
        return ['父记录有 %d 个 type13 子记录（传授多 pattern），本行无逐 pattern 文本对应' % len(t13)], None, None
    c = t13[0]
    raws = {q: B6._raw_of(c, q) for q in ('skillparam1', 'skillparam2', 'skillparam6',
                                          'skillparam3', 'skillparam4', 'skillparam5')}
    exp = {B6.ATTR_PARAM[a] for a in noncrit if a in B6.ATTR_PARAM}
    act = {q for q in ('skillparam1', 'skillparam2', 'skillparam6')
           if B6._num(raws.get(q)) and raws.get(q) != 0}
    if act != exp:
        return ['形状不符（U3）：句属性槽 %s ≠ 活性槽 %s' % (sorted(exp), sorted(act))], None, None
    if not (B6._num(raws[B6.DUR_PARAM]) and raws[B6.DUR_PARAM] != 0):
        return ['持续时间槽 skillparam3 无非零值'], None, None
    if same_count > 1:
        return ['同文在记录正文出现 %d 次' % same_count], None, None
    if fam_counter.get(B6.FAM1, 0) > 1:
        return ['同记录有 %d 条 FAM1 家族句（多 buff 句共享同一 type13）'
                % fam_counter.get(B6.FAM1, 0)], None, None
    # --- 槽位分区（批 17）：竞争句映射主张槽 ∩ 本 t13 非 crit 活性槽 == ∅ 才可分区 ------
    blockers = []
    for comp in competitors:
        inter = sorted(set(comp['mapped']) & act)
        if inter:
            blockers.append(
                '竞争句「%s」（%s）属性主张（%s）映射槽 %s 与本 t13 活性槽 %s 相交（%s）——'
                '竞争句可能持有本 t13 槽，槽位分区不成立，归属不能唯一化解'
                % (comp['text'], comp['fam'], '、'.join(comp['attrs']) or '（无）',
                   comp['mapped'], sorted(act), inter))
    violations, claimed, zeros = _full_field_review(c, exp, crit_claimed)
    if blockers:
        return blockers, None, None
    if violations:
        return ['t13 全字段复核（批 17）：存在已分配槽（%s）之外的非零槽 %s——「竞争句'
                '载体非本 t13」的结构性前提不成立，留 hint' % (claimed, violations)], None, None
    info = dict(t13=c, raws=raws, active=sorted(act), claimed=sorted(exp | {B6.DUR_PARAM}),
                zeros=zeros, competitors=competitors)
    return [], c, info


def _dur_argument_note(partition_competitors):
    """H1 时长化解论证（逐字披露在行注记——批 16 审计 §一.族 1 要求）。"""
    if not partition_competitors:
        return ''
    parts = []
    for comp in partition_competitors:
        parts.append('竞争句「%s」属性主张（%s）不在/不交 bossskill|13 槽词表'
                     '（ATTR_PARAM 仅攻撃力/防御力/移動速度，card_page_inference_b6_bossbuff.py:145；'
                     '词表外属性逐字披露、不进映射——∅ 映射语义不变）'
                     '→ 本 t13 无槽可承载其属性主张'
                     % (comp['text'], '、'.join(comp['attrs']) or '未检出'))
    return ('；时长槽化解论证（批 17，逐字披露）：' + '；'.join(parts)
            + '；且 t13 全字段复核无已分配槽外非零槽 → 竞争句的载体不是本 t13，'
              '其句面「一定時間」随其自身载体走，与本 t13 /skillparam3 无涉——'
              '时长 p3 归本行。此为推断链（数据侧结构对应），引擎侧无原生核实')


def _value_row(attr, param, raw, child, child_key, parent_chain, slot_desc,
               sent_no, sent_total, section_no, section_count, arg_note, dur=False,
               object_desc=None, condition_label=None, hp_branch_note=None):
    """批 17 值行（批 15 _union_value_row 同结构；tag/scope/注记换批 17）。
    object_desc（B17-R01 修复）：对象/条件句面依据陈述——默认（H1/P2/multi，味方全体句）
    「对象「味方全体」为句面依据」；H2 条件暴击句传入「条件「…味方の場合」／对象「…味方」」
    （含句面条件逐字短语，与行级 subject「味方（条件句）」一致）。
    condition_label/hp_branch_note（R1 整改，20261023）：HP 档位分支值行——标签＝原值逐字
    拼接（如「HP 51–100%」）；hp_branch_note 逐字披露该档位来源分支与边界待核查说明。"""
    rule = R.rule_for('bossskill', 13, '/' + param)
    converted = R.answer_for('bossskill', 13, '/' + param, raw, child)
    evidence_dir, evidence_files = B6._field_evidence(param)
    attr_label = B6.DUR_ATTR if dur else attr
    # R08-R1 整改（20261023，复审 B17-R08）：multi 路径的 parent_chain 已以 child 结尾
    # （「…→bossskill|<id>|<layer>（boss_skill_refs reference_field 归属登记）」）——
    # numeric_source 父链去重：parent_chain 已含本 child（允许尾随括注）时不再追加一次。
    _pc_base = re.sub(r'（[^）]*）$', '', parent_chain or '')
    chain_desc = parent_chain if _pc_base.endswith(child_key) \
        else f'{parent_chain}→{child_key}'
    note = (
        f'模板批 17 P0 收尾值行（{"时长" if dur else "非 crit 属性"}段；来源载体＝'
        f'{child_key}，bossskill type13；父链 {parent_chain}）；句中「{attr_label}」→'
        f'/{param} 1:1 映射；规则键 bossskill|13|/{param}；原值 {raw}；方向审核 '
        f'{B6._direction_text(param, raw)}；证据目录 {evidence_dir}；'
        f'{object_desc or "对象「味方全体」为句面依据"}，该 type13 处理器的接受者选择'
        f'逻辑无已确认规则（{B6._iparam_note(child)}）；样本域：'
        f'{B6._sample_domain_note(param, rule)}；'
        f'{slot_desc}；{arg_note}；规则本体：已确认（静态及受控原生局部规则）——指规则'
        '本身；本条数值归属＝推断（模板批 17 P0 收尾），引擎侧装载路径无原生核实，'
        '不升确认'
        + (f'；{hp_branch_note}' if hp_branch_note else '')
        + (f'；正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）'
           if sent_no else '；正文句序未能定位')
        + (f'；◆ 段：第 {section_no}／共 {section_count} 段（◆段口径不传达句序）'
           if section_no else ''))
    row = dict(
        value=converted['value_text'],
        quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
        raw_value=raw, field_path='/' + param,
        numeric_source=f'模板推断（批 17 P0 收尾：{chain_desc}）',
        numeric_evidence='推断', association_evidence='推断', evidence_scope=B17_SCOPE,
        rule_key=f'bossskill|13|/{param}',
        rule_body_status=rule.get('status'), rule_status=rule.get('status'),
        conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
        conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
        evidence=list(evidence_files),
        source=dict(table='bossskill', record_id=child.get('record_id'),
                    layer=child.get('layer'), record_key=child_key),
        note=note, quantitative=True)
    if condition_label:
        row['condition_label'] = condition_label
    return row


def _answers_and_meta(info, parent_chain, child_key, slot_desc, sent_no, sent_total,
                      section_no, section_count, arg_note, noncrit, object_desc=None):
    """按属性分别归属：非 crit 值行＋时长值行（t13 槽；不合并不乘积）。"""
    child = info['t13']
    raws = info['raws']
    answers = []
    claimed_slots = set()
    for attr in noncrit:
        if attr not in B6.ATTR_PARAM:
            continue
        param = B6.ATTR_PARAM[attr]
        raw = raws[param]
        if not (B6._num(raw) and raw != 0):
            return None, [f'形状不符（U3）：句主张「{attr}」但槽 /{param} 不活性（{raw!r}）——缺失不补 0']
        claimed_slots.add(param)
        answers.append(_value_row(attr, param, raw, child, child_key, parent_chain,
                                  slot_desc, sent_no, sent_total, section_no,
                                  section_count, arg_note, object_desc=object_desc))
    raw = raws[B6.DUR_PARAM]
    if not (B6._num(raw) and raw != 0):
        return None, [f'形状不符（U3）：句主张「{B6.DUR_ATTR}」但时长槽 /{B6.DUR_PARAM} 无非零值（{raw!r}）']
    claimed_slots.add(B6.DUR_PARAM)
    answers.append(_value_row(None, B6.DUR_PARAM, raw, child, child_key, parent_chain,
                              slot_desc, sent_no, sent_total, section_no, section_count,
                              arg_note, dur=True, object_desc=object_desc))
    return answers, list(claimed_slots)


def _unclaimed_note(child, claimed_slots, crit_claimed):
    """句外槽登记（批 15 DS-GR-05 修复后同法：完整槽名比对）。"""
    claimed = set(claimed_slots) | ({'skillparam4', 'skillparam5'} if crit_claimed else set())
    unclaimed = []
    for u in (child.get('answers') or []) + (child.get('unexplained') or []):
        m = _SLOT_RE.fullmatch(u.get('f') or '')
        if not m or m.group(1) in claimed:
            continue
        unclaimed.append(f'{u["f"]}={u.get("raw")!r}'
                         + ('（原值 0，未被本句主张）' if u.get('raw') == 0 else ''))
    return unclaimed


def _sent_pos(wb, frag):
    """句序/段位（批 6 B6-RV-04 同法：◆段＋「。」句序）；无 crit 结果时（P2 溢出行）自算。"""
    starts = TYPE8._occurrences(wb, frag) if wb else []
    section_no = TYPE8._section_no(wb, starts[0])[0] if starts else None
    section_count = TYPE8._section_count(wb) if wb else None
    _sents = re.findall(r'[^。]*。', wb or '')
    sent_no = next((i + 1 for i, sn in enumerate(_sents) if frag.strip() in sn), None)
    return sent_no, len(_sents), section_no, section_count


def _prior_hint_text(b15_result, b6_result):
    """既有唯一 hint 键的文本（b15 键含并入的批 6 注记；data.py DS-GR-06 同法复制）。"""
    if b15_result and b15_result.get('kind') == 'hint':
        t = '；'.join(b15_result.get('reasons') or [])
        if b6_result and b6_result.get('kind') == 'hint':
            t += ('；批 6 hint 并入本键（行级不残留 inference_b6_hint 键）：'
                  + '；'.join(b6_result.get('reasons') or []))
        return 'inference_b15_hint', t
    if b6_result and b6_result.get('kind') == 'hint':
        return 'inference_b6_hint', '；'.join(b6_result.get('reasons') or [])
    return None, None


# ---------------------------------------------------------------------------
# 路径实现
# ---------------------------------------------------------------------------

def _run_partition(frag, table, layer, record_id, text, data, cid, boss_skill_refs,
                   crit_promotion, prior_key, prior_text, via_note, batch_label,
                   hint_on_fail=True):
    """H1/P2 共用：槽位分区归属。crit_promotion 为 None 时即 P2 溢出行。
    hint_on_fail=False（P2 溢出）时门不通过返回 None——既有 hint 键零触碰
    （「不适用者留 hint」），不产生对账噪声。"""
    template = B6._norm_text(frag)
    attrs = [a for a in B6._ATTR_DETECT if a in template]
    noncrit = [a for a in attrs if a in B6.ATTR_PARAM]
    unmapped = [a for a in attrs if not a.startswith('クリティカル') and a not in B6.ATTR_PARAM]
    crit_claimed = crit_promotion is not None
    parent, pkey, wb, same_count, fam_counter, via_desc, p_bsr, _ = _locate_parent(
        frag, table, layer, record_id, text, data, cid, boss_skill_refs)
    if parent is None:
        if not hint_on_fail:
            return None
        return dict(kind='hint', path='H1_partition', replaces_hint=prior_key,
                    reasons=['槽位分区链不可达：父记录未定位或同文 pattern %s' % (pkey or via_desc,)])
    competitors = _competitor_sents(wb, frag)
    reasons, child, info = _partition_gate(parent, noncrit, same_count, fam_counter,
                                           competitors, crit_claimed)
    if child is None:
        if not hint_on_fail:
            return None
        return dict(kind='hint', path='H1_partition', replaces_hint=prior_key,
                    reasons=reasons)
    # U4 方向门：句须为「上がる」增益方向；活性槽/时长槽原值>0
    if not re.search(r'上がる|上がり|上げる', frag):
        if not hint_on_fail:
            return None
        return dict(kind='hint', path='H1_partition', replaces_hint=prior_key,
                    reasons=['槽位分区方向门（U4）：句无「上がる」增益方向词'])
    neg = [q for q in info['active'] + ['skillparam3'] if B6._num(info['raws'].get(q))
           and info['raws'].get(q) <= 0]
    if neg:
        if not hint_on_fail:
            return None
        return dict(kind='hint', path='H1_partition', replaces_hint=prior_key,
                    reasons=['方向冲突（U4）：槽 %s 原值 %s 非正，句称上升；批 6 §5.4 保守留 hint'
                             % ('、'.join(neg), {q: info['raws'][q] for q in neg})])
    child_id = child.get('record_id')
    child_layer = child.get('layer')
    child_key = f'bossskill|{child_id}|{child_layer}'
    parent_chain = via_desc
    # 槽位披露（links boss_skill_refs）
    slot = None
    for r in p_bsr or []:
        if r.get('table') == 'bossskill' and str(r.get('reference_id')) == str(child_id):
            slot = r.get('slot')
            break
    slot_desc = (f'bossskill 子记录经父记录 boss_skill_refs 槽位 {slot} 引用'
                 if slot else 'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）')
    sent_no = (crit_promotion or {}).get('sent_no')
    sent_total = (crit_promotion or {}).get('sent_total')
    section_no = (crit_promotion or {}).get('section_no')
    section_count = (crit_promotion or {}).get('section_count')
    if crit_promotion is None or sent_total is None:
        sent_no, sent_total, section_no, section_count = _sent_pos(wb, frag)
    sent_total = sent_total or 0
    arg_note = ('槽位分区归属（批 17）：同记录竞争句经映射主张槽核查与 t13 全字段复核'
                '后结构上不能持有本 t13 任何槽' + _dur_argument_note(
                    [c for c in info['competitors'] if c['via'] == 'family' and not c['mapped']])
                + ('；本行句内无映射属性主张（%s）不出值行（bossskill|13 无对应已确认规则，'
                   '其载体另寻）' % '、'.join(unmapped) if unmapped else ''))
    answers, claimed_slots = _answers_and_meta(info, parent_chain, child_key, slot_desc,
                                               sent_no, sent_total, section_no,
                                               section_count, arg_note, noncrit)
    if answers is None:
        if not hint_on_fail:
            return None
        return dict(kind='hint', path='H1_partition', replaces_hint=prior_key, reasons=claimed_slots)
    extra = []
    extra.append('槽位分区依据（批 17）：本行非 crit 主张槽 %s＝t13 活性槽；同记录竞争句 '
                 '（%s）映射主张槽与活性槽不相交＋t13 全字段复核（已分配槽 %s；句外零值槽 %s）'
                 '——竞争句结构上不能持有本 t13 任何槽（批次：%s）'
                 % (info['active'],
                    '；'.join(c['text'] for c in info['competitors']) or '（无）',
                    info['claimed'], info['zeros'] or '（无）', batch_label))
    if crit_claimed:
        crit_chain_desc = ("批 8/14 2012 链：bosspattern|%s→bossskill|%s(type13,slot %s)→"
                           "s_ability→skilllist|%s|%s(ability2012)"
                           % (crit_promotion.get('pattern_record_id'),
                              crit_promotion.get('relay_record_id'),
                              crit_promotion.get('relay_slot'),
                              crit_promotion.get('carrier_record_id'),
                              crit_promotion.get('carrier_layer')))
        extra.append('批 8/14 既有 crit 值行零触碰：本批只新增非 crit/时长值行（来源 t13 槽）；'
                     'crit 段见本行既有 2012 链值行（' + crit_chain_desc + '）')
    unclaimed = _unclaimed_note(child, claimed_slots, crit_claimed)
    if unclaimed:
        extra.append('t13 子记录句外槽未分配（不归属本句，仅登记原值'
                     + ('；crit 槽 p4/p5 由 2012 链消费）' if crit_claimed else '）：')
                     + '、'.join(dict.fromkeys(unclaimed)))
    summary = (B17_TAG + '（%s）：值行来源＝' % batch_label + parent_chain + '→'
               + child_key + '（t13 活性槽按属性分别归属' + via_note + '）；值行全部「推断」，'
               '不升「确认」，不进入整行确认。' + '；'.join(extra))
    return dict(kind='promote', path='H1_partition', answers=answers,
                summary_reason=summary, extra_reasons=extra,
                subject='味方全体', attrs=attrs, noncrit_attrs=noncrit,
                table=table, parent_chain=parent_chain,
                chain_record_id=child_id, chain_layer=child_layer, chain_key=child_key,
                crit_promotion_key=(('inference_b14' if crit_promotion.get('b14_ext')
                                     else 'inference_b8') if crit_claimed else None),
                crit_pattern_record_id=(crit_promotion or {}).get('pattern_record_id'),
                crit_relay_record_id=(crit_promotion or {}).get('relay_record_id'),
                crit_relay_type=(crit_promotion or {}).get('relay_type'),
                crit_relay_slot=(crit_promotion or {}).get('relay_slot'),
                crit_carrier_record_id=(crit_promotion or {}).get('carrier_record_id'),
                crit_carrier_layer=(crit_promotion or {}).get('carrier_layer'),
                replaces_hint=prior_key, replaced_hint_text=prior_text,
                b6_yield_note_replaced=(prior_text if prior_key == 'inference_b6_hint' else None),
                sent_no=sent_no, sent_total=sent_total)


def _run_h2(frag, table, layer, record_id, text, data, cid, boss_skill_refs,
            crit_promotion, prior_key, prior_text, record=None):
    """H2：条件暴击行时长槽共享（主持 D1 级裁决 2026-10-23，方案①）。
    record＝行记录本体（charainfo 行的兄弟行层级披露 B17-R06 复评用；可为 None——
    仅 charainfo 路径需要）。"""
    template = B6._norm_text(frag)
    attrs = [a for a in B6._ATTR_DETECT if a in template]
    noncrit = [a for a in attrs if a in B6.ATTR_PARAM]
    if noncrit or B6.DUR_ATTR not in frag:
        return None  # H2 形状＝仅 crit＋时长主张；其余形态不属本路径
    parent, pkey, wb, same_count, fam_counter, via_desc, p_bsr, _ = _locate_parent(
        frag, table, layer, record_id, text, data, cid, boss_skill_refs)
    if parent is None:
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['时长槽共享链不可达：父记录未定位或同文 pattern 记录缺失/不唯一'])
    boss_kids = [c for c in parent.get('children') or [] if c.get('table') == 'bossskill']
    t13 = [c for c in boss_kids if c.get('effect_type') == 13]
    if not t13:
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['时长槽共享链不可达（U2）：父记录无可解析的 type13 子记录（链上类型=%s）'
                             % [c.get('effect_type') for c in boss_kids]])
    if len(t13) > 1:
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['时长槽共享链不可达（U2）：父记录有 %d 个 type13 子记录，归属歧义' % len(t13)])
    child = t13[0]
    # 硬前提①：同记录恰一条 FAM1 兄弟句，且已被批 6 以同一 t13 晋级（运行时真实重放）
    if fam_counter.get(B6.FAM1, 0) != 1:
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['硬前提①不成立：父记录 FAM1 家族句数=%d（须恰 1 条味方全体句'
                             '作为同 buff 兄弟行）' % fam_counter.get(B6.FAM1, 0)])
    sib_frags = []
    for sp in fragment_positions(wb or ''):
        nf = B6._norm_text(sp['japanese'])
        if B6._family_of(nf) == B6.FAM1 and nf.strip() != template.strip():
            if sp['japanese'] not in sib_frags:
                sib_frags.append(sp['japanese'])
    if len(sib_frags) != 1:
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['硬前提①不成立：父记录正文 FAM1 兄弟句定位到 %d 条（须恰 1）'
                             % len(sib_frags)])
    sib_frag = sib_frags[0]
    if table == 'charainfo':
        pe_key = pkey
        pe = next((e for e, _ in B6._page_ctx(data, cid)['pattern_frags']
                   if ('bosspattern', str(e.get('reference_id')), e.get('layer')) == pe_key), None)
        sib_eval = B6.evaluate(pe.get('record'), sib_frag, table='bosspattern',
                               layer=pe.get('layer'), record_id=pe.get('reference_id'),
                               text=str((pe.get('record') or {}).get('sinfo', '') or ''),
                               data=data, cid=cid, boss_skill_refs=pe.get('boss_skill_refs'))
    else:
        sib_eval = B6.evaluate(parent, sib_frag, table=table, layer=layer,
                               record_id=record_id, text=text, data=data, cid=cid,
                               boss_skill_refs=boss_skill_refs)
    if not sib_eval or sib_eval.get('kind') != 'promote':
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['硬前提①不成立：兄弟 FAM1 句「%s」批 6 门未晋级（%s）'
                             % (sib_frag, '；'.join((sib_eval or {}).get('reasons') or ['评估返回 None']))])
    if str(sib_eval.get('chain_record_id')) != str(child.get('record_id')):
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['硬前提①不成立：兄弟 FAM1 句批 6 晋级链 t13（bossskill|%s|%s）'
                             '与本行链 t13（bossskill|%s|%s）不同记录——不跨记录取值'
                             % (sib_eval.get('chain_record_id'), sib_eval.get('chain_layer'),
                                child.get('record_id'), child.get('layer'))])
    # 硬前提②：2012 载体 param0 原值 == t13 p3 原值（数值/float32 精度）
    p3 = B6._raw_of(child, B6.DUR_PARAM)
    carrier = data.skill(crit_promotion.get('carrier_record_id')) if \
        crit_promotion.get('carrier_record_id') is not None else None
    if carrier is None:
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['硬前提②不可核：批 8/14 载体 skilllist|%s 未定位'
                             % crit_promotion.get('carrier_record_id')])
    p0 = (carrier.get('record') or {}).get('param0')
    if not (B6._num(p3) and B6._num(p0) and _num_eq(p0, p3)):
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['硬前提②不成立（时长槽共享不作）：本行 2012 载体 '
                             'skilllist|%s|%s /param0 原值 %r 与 t13 bossskill|%s|%s '
                             '/skillparam3 原值 %r 两值不一致——逐字披露两值，不硬选'
                             % (crit_promotion.get('carrier_record_id'),
                                carrier.get('layer'), p0,
                                child.get('record_id'), child.get('layer'), p3)])
    # U4：p3>0；fam11/13 不得并存（共享例外仅限兄弟 FAM1 一条）
    if fam_counter.get(B6.FAM11) or fam_counter.get(B6.FAM13):
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['父记录另有自身バフ/上げる句家族行——共享例外仅限兄弟 FAM1 一条，'
                             '归属不能唯一化解'])
    if not (B6._num(p3) and p3 > 0):
        return dict(kind='hint', path='H2_duration_share', replaces_hint=prior_key,
                    reasons=['方向冲突（U4）：时长槽原值 %r 非正' % p3])
    child_id = child.get('record_id')
    child_layer = child.get('layer')
    child_key = f'bossskill|{child_id}|{child_layer}'
    parent_chain = via_desc
    slot = None
    for r in p_bsr or []:
        if r.get('table') == 'bossskill' and str(r.get('reference_id')) == str(child_id):
            slot = r.get('slot')
            break
    slot_desc = (f'bossskill 子记录经父记录 boss_skill_refs 槽位 {slot} 引用'
                 if slot else 'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）')
    # 对象/条件句面依据（B17-R01 修复）：H2 行对象为条件味方（行级 subject「味方（条件句）」），
    # 注记写出句面条件逐字短语（如「弓使いの味方の場合」），不再写「味方全体」。
    m_cond = re.search(r'[^。、]*味方の場合', frag)
    cond_phrase = m_cond.group(0) if m_cond else None
    if cond_phrase:
        object_desc = ('条件「%s」／对象「%s」为句面依据'
                       % (cond_phrase, cond_phrase[:-len('の場合')]))
    else:
        object_desc = '对象「味方（条件句）」为句面依据（句面条件短语未检出，如实登记）'
    # 兄弟行晋级层级披露（B17-R06 修复）：charainfo 行的兄弟 FAM1 晋级是 pattern 级
    # （bosspattern 链）；同 skilltext 的 charainfo 兄弟行单独复评并如实披露其状态
    # （实测 5 行为 0 答案仍 hint——G5 同文多 pattern 歧义），避免页面级误读。
    sib_chara_note = ''
    if table == 'charainfo':
        sib_chara = B6.evaluate(record, sib_frag, table='charainfo', layer=layer,
                                record_id=record_id, text=text, data=data, cid=cid,
                                boss_skill_refs=boss_skill_refs)
        if sib_chara and sib_chara.get('kind') == 'promote':
            sib_chara_note = ('；兄弟 FAM1 行晋级为 pattern 级（同页同文 bosspattern 记录链）；'
                              '同 skilltext 的 charainfo 兄弟行实测亦已晋级（批 6，同 t13）')
        else:
            sib_chara_note = ('；兄弟 FAM1 行晋级为 pattern 级（同页同文 bosspattern 记录链）；'
                              '同 skilltext 的 charainfo 兄弟行实测 0 答案仍 hint（批 6 门：%s）'
                              '——本行时长值行引 pattern 级 t13 /skillparam3，不依赖该兄弟行'
                              % '；'.join((sib_chara or {}).get('reasons') or ['评估返回 None']))
    arg_note = (
        '时长槽共享（批 17，主持 D1 级裁决 2026-10-23 方案①）：/skillparam3 非独占——'
        '同一 t13 同时服务兄弟 FAM1 行与本条件暴击行（句面「も」＝同 buff 追加语义）；'
        '各注来源、不合并不乘积；与批 15 D1 裁决一致（时长值行归 t13 /skillparam3，'
        '不消费 2012 载体 param0）。硬前提①（兄弟行「%s」已由批 6 以同一 t13 晋级，'
        '本批逐行实测复验：链 %s）与硬前提②（本行 2012 载体 skilllist|%s|%s /param0 '
        '原值 %r 与本 t13 /skillparam3 原值 %r 逐值核对一致——一致性核对披露，'
        '不作为值来源）均实测成立%s' % (sib_frag,
                                      f"bossskill|{sib_eval.get('chain_record_id')}|"
                                      f"{sib_eval.get('chain_layer')}",
                                      crit_promotion.get('carrier_record_id'),
                                      carrier.get('layer'), p0, p3, sib_chara_note))
    answers = [_value_row(None, B6.DUR_PARAM, p3, child, child_key, parent_chain,
                          slot_desc, crit_promotion.get('sent_no'),
                          crit_promotion.get('sent_total') or 0,
                          crit_promotion.get('section_no'), crit_promotion.get('section_count'),
                          arg_note, dur=True, object_desc=object_desc)]
    crit_chain_desc = ("批 8/14 2012 链：bosspattern|%s→bossskill|%s(type13,slot %s)→"
                       "s_ability→skilllist|%s|%s(ability2012)"
                       % (crit_promotion.get('pattern_record_id'),
                          crit_promotion.get('relay_record_id'),
                          crit_promotion.get('relay_slot'),
                          crit_promotion.get('carrier_record_id'),
                          crit_promotion.get('carrier_layer')))
    extra = ['时长槽共享依据（批 17/D1 裁决）：兄弟 FAM1 行与本行共享同一 t13 的 '
             '/skillparam3；本行时长值行引同槽并注「槽共享／各注来源／不合并不乘积」；'
             '暴击段由既有批 8/14 值行兑现（' + crit_chain_desc + '），零触碰',
             '硬前提逐行复验（批 17）：①兄弟 FAM1 句「%s」批 6 晋级链＝bossskill|%s|%s'
             '（与本行同一 t13）；②载体 param0 原值 %r ＝ t13 p3 原值 %r（数值/float32 '
             '精度一致）' % (sib_frag, sib_eval.get('chain_record_id'),
                             sib_eval.get('chain_layer'), p0, p3)]
    unclaimed = _unclaimed_note(child, {B6.DUR_PARAM} | set(
        B6.ATTR_PARAM[a] for a in (sib_eval.get('attrs') or []) if a in B6.ATTR_PARAM),
        True)
    if unclaimed:
        extra.append('t13 子记录句外槽未分配（不归属本行，仅登记原值；p1/p2(/p6) 由兄弟 '
                     'FAM1 行按批 6 既有值行兑现、crit 槽 p4/p5 由 2012 链消费）：'
                     + '、'.join(dict.fromkeys(unclaimed)))
    summary = (B17_TAG + '（H2 时长槽共享）：时长值行来源＝' + parent_chain + '→' + child_key
               + '（/skillparam3 槽共享；D1 裁决 2026-10-23）；值行「推断」，不升「确认」，'
               '不进入整行确认；crit 值行＝批 8/14 既有 2012 链值行（零触碰）。'
               + '；'.join(extra))
    return dict(kind='promote', path='H2_duration_share', answers=answers,
                summary_reason=summary, extra_reasons=extra,
                subject='味方（条件句）', attrs=attrs, noncrit_attrs=[],
                table=table, parent_chain=parent_chain,
                chain_record_id=child_id, chain_layer=child_layer, chain_key=child_key,
                crit_promotion_key=('inference_b14' if crit_promotion.get('b14_ext')
                                    else 'inference_b8'),
                crit_pattern_record_id=crit_promotion.get('pattern_record_id'),
                crit_relay_record_id=crit_promotion.get('relay_record_id'),
                crit_relay_type=crit_promotion.get('relay_type'),
                crit_relay_slot=crit_promotion.get('relay_slot'),
                crit_carrier_record_id=crit_promotion.get('carrier_record_id'),
                crit_carrier_layer=crit_promotion.get('carrier_layer'),
                replaces_hint=prior_key, replaced_hint_text=prior_text,
                sent_no=crit_promotion.get('sent_no'),
                sent_total=crit_promotion.get('sent_total'))


def _run_multi_branches(frag, table, layer, record_id, text, data, cid, boss_skill_refs,
                        denju_pattern_refs, crit_promotion, prior_key, prior_text):
    """R1 整改（20261023）：denju 引用 ≥2 个 pattern 且 hpstart/hpend 分成多个 HP 档位
    条件组时——沿全部引用保留分支（空 sinfo 不排除），逐档位出值行（condition_label＝
    原值逐字，如「HP 51–100%」），各档位值各注来源分支与 HP 条件，不合并不平均不选代表值。
    非多档位返回 None（调用方走原单命中路径）。"""
    refs = []
    for p in denju_pattern_refs:
        pid = p.get('reference_id')
        prec, lay2 = B6.pattern_record_of(pid, prefer_layer=p.get('layer'))
        refs.append((p.get('slot'), pid, lay2, prec))
    if len(refs) <= 1:
        return None
    conds = {(p.get('hpstart'), p.get('hpend')) for _, _, _, p in refs if p is not None}
    if len(conds) <= 1:
        return None
    parent, pkey, wb, same_count, fam_counter, via_desc, p_bsr, _ = _locate_parent(
        frag, table, layer, record_id, text, data, cid, boss_skill_refs)
    if parent is None:
        return None  # 链不可达由原路径 hint（原因文本不变）
    template = B6._norm_text(frag)
    attrs = [a for a in B6._ATTR_DETECT if a in template]
    noncrit = [a for a in attrs if a in B6.ATTR_PARAM]
    crit_claimed = crit_promotion is not None
    competitors = _competitor_sents(wb, frag)
    pool, t13_kids = {}, []
    for c in parent.get('children') or []:
        if c.get('table') == 'bossskill' and c.get('effect_type') == 13:
            pool[f'bossskill|{c.get("record_id")}|{c.get("layer")}'] = c
            t13_kids.append(c)
    hits = [pid for slot, pid, lay2, p in refs
            if p is not None and frag in {sp['japanese'] for sp in
                                          fragment_positions(str(p.get('sinfo') or '')
                                                             .replace('\\n', '\n'))}]
    groups, _sigs = B6.build_hp_branches(refs, pool,
                                         sinfo_hit_pid=hits[0] if len(hits) == 1 else None)
    # 行级门（与原路径同门；分支级门在下方逐档执行）
    gate_fails = []
    if same_count > 1:
        gate_fails.append('同文在记录正文出现 %d 次' % same_count)
    if fam_counter.get(B6.FAM1, 0) > 1:
        gate_fails.append('同记录有 %d 条 FAM1 家族句（多 buff 句共享同一 type13）'
                          % fam_counter.get(B6.FAM1, 0))
    if not re.search(r'上がる|上がり|上げる', frag):
        gate_fails.append('方向门（U4）：句无「上がる」增益方向词')
    if gate_fails:
        return dict(kind='hint', path='MULTI_T13_PATTERNID', hp_branch_mode=True,
                    replaces_hint=prior_key, reasons=gate_fails)
    # 逐档位门＋出值
    answers, labels, branch_todos, others_disc = [], [], [], []
    claimed = set()
    # 增益 t13 各档位是否逐槽同值（R1-Low 整改：HP 变化句对象为ダメージ量时的归因措辞依据）
    _gains_sigs = {g['sig'] for g in groups if g['child'] is not None and g['sig'] is not None}
    gains_uniform = len(_gains_sigs) == 1 if _gains_sigs else None
    for g in groups:
        if g['fail'] and g['child'] is None:
            branch_todos.append('档位待办（%s，pattern 引用：%s）：%s'
                                % (g['label'],
                                   '、'.join(f'{m["slot"]}＝bosspattern|{m["pid"]}|{m["layer"]}'
                                             for m in g['members']),
                                   g['fail']))
            continue
        child = g['child']
        raws = {q: B6._raw_of(child, q) for q in ('skillparam1', 'skillparam2', 'skillparam6',
                                                  'skillparam3')}
        exp = {B6.ATTR_PARAM[a] for a in noncrit}
        act = {q for q in ('skillparam1', 'skillparam2', 'skillparam6')
               if B6._num(raws.get(q)) and raws.get(q) != 0}
        fail = None
        if act != exp:
            fail = ('形状不符（U3）：句属性槽 %s ≠ 本档位 t13 活性槽 %s'
                    % (sorted(exp), sorted(act)))
        elif not (B6._num(raws[B6.DUR_PARAM]) and raws[B6.DUR_PARAM] != 0):
            fail = '持续时间槽 skillparam3 无非零值'
        else:
            violations, claimed_f, zeros = _full_field_review(child, exp, crit_claimed)
            if violations:
                fail = ('t13 全字段复核（批 17）：本档位 t13 存在已分配槽（%s）之外的非零槽 %s'
                        % (claimed_f, violations))
            else:
                neg = [q for q in sorted(act) + ['skillparam3']
                       if B6._num(raws.get(q)) and raws.get(q) <= 0]
                if neg:
                    fail = '方向冲突（U4）：槽 %s 原值非正' % neg
        if fail:
            branch_todos.append('档位待办（%s）：%s' % (g['label'], fail))
            continue
        # R1-Medium 复审整改 20261023：父链/槽位只在本档位成员内对号（同值 t13 跨档引用时
        # 不得固定首档——B6._member_of 全组搜索的 20332 缺陷同款）
        m = B6._member_in_group(g, g['child_key'],
                                prefer_pid=hits[0] if len(hits) == 1 else None)
        slot_m = m['slot'] if m else '?'
        pid_m = m['pid'] if m else '?'
        lay_m = m['layer'] if m else '?'
        slot = None
        for r in p_bsr or []:
            if r.get('table') == 'bossskill' and \
                    str(r.get('reference_id')) == str(child.get('record_id')) and \
                    str(r.get('reference_field') or '').startswith(f'bosspattern[{pid_m}].'):
                slot = r.get('slot')
                break
        if slot is None and pid_m != '?':
            # R1-Medium 复审整改 20261023：links boss_skill_refs 按子记录去重（同 t13 跨
            # pattern 只登记首 pattern 的 reference_field）——槽位回退读本档 pattern 原始
            # 记录 skillidX（数据侧事实，非顺序推断）。
            prec_m, _ = B6.pattern_record_of(pid_m, prefer_layer=lay_m)
            slot = next((f'skillid{j}' for j in range(8)
                         if str((prec_m or {}).get(f'skillid{j}'))
                         == str(child.get('record_id'))), None)
            slot_desc = (f'bossskill 子记录经 pattern 记录（bosspattern|{pid_m}|{lay_m}）的 '
                         f'{slot} 槽引用（links boss_skill_refs 该 pattern 未单独登记——'
                         '登记按子记录去重；槽位读自 pattern 原始记录）' if slot else
                         'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）')
        else:
            slot_desc = (f'bossskill 子记录经父记录 boss_skill_refs reference_field'
                         f'「bosspattern[{pid_m}].{slot}」归属登记'
                         if slot else 'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）')
        arg_note = ('多 t13 归属（批 17，R1 整改）：denju patternidN→全部 pattern 引用按 '
                    'hpstart/hpend 分档保留（空 sinfo 不排除）→各档位 t13 经 boss_skill_refs '
                    f'reference_field「bosspattern[{pid_m}].skillidX」归属登记；'
                    '同号跨命名空间不合并、不跨层取值')
        parent_chain_b = f'{via_desc}→{slot_m}→bosspattern|{pid_m}|{lay_m}'
        hp_note = B6.hp_branch_note_of(g['label'], g['cond'], g['members'], g['peers'],
                                       B6.hp_var_sentence(text),
                                       gains_uniform=gains_uniform)
        child_key = g['child_key']
        for attr in noncrit:
            param = B6.ATTR_PARAM[attr]
            claimed.add(param)
            answers.append(_value_row(attr, param, raws[param], child, child_key,
                                      parent_chain_b, slot_desc, None, 0, None, None,
                                      arg_note, condition_label=g['label'],
                                      hp_branch_note=hp_note))
        claimed.add(B6.DUR_PARAM)
        answers.append(_value_row(None, B6.DUR_PARAM, raws[B6.DUR_PARAM], child, child_key,
                                  parent_chain_b, slot_desc, None, 0, None, None,
                                  arg_note, dur=True, condition_label=g['label'],
                                  hp_branch_note=hp_note))
        labels.append(g['label'])
    if not answers:
        return dict(kind='hint', path='MULTI_T13_PATTERNID', hp_branch_mode=True,
                    replaces_hint=prior_key,
                    reasons=(branch_todos or ['HP 条件分支保留（R1 整改）：无档位可出值']))
    sent_no, sent_total, section_no, section_count = _sent_pos(wb, frag)
    if sent_no:
        for a in answers:
            a['note'] += (f'；正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句'
                          '（以「。」切分）')
            if section_no:
                a['note'] += (f'；◆ 段：第 {section_no}／共 {section_count} 段'
                              '（◆段口径不传达句序）')
    extra = ['%s——源记录引用 %d 个 pattern、分 %d 个 HP 档位条件组（%s）；各档位 t13 值'
             '逐项绑定该分支条件，不合并不平均不选代表值；值行全部「推断」，不升「确认」'
             % (B6._R1_BRANCH_NOTE, len(refs), len(groups), '、'.join(labels))]
    extra += branch_todos
    for g in groups:
        if g['child'] is not None and g['peers']:
            extra.append('档位 %s 同值兜底披露：本档位取值＝%s；其余 pattern 引用 t13 %s'
                         % (g['label'], g['child_key'],
                            '；'.join(f'{k}（值签名 {s}）' for k, s in g['peers'])))
    if crit_claimed:
        extra.append('批 8/14 既有 crit 值行零触碰：crit 段见本行既有 2012 链值行；HP 档位'
                     '分支值行只新增非 crit/时长段（各注来源档位）')
    unclaimed = []
    for g in groups:
        if g['child'] is None:
            continue
        for u in (g['child'].get('answers') or []) + (g['child'].get('unexplained') or []):
            f = u.get('f') or ''
            m2 = _SLOT_RE.fullmatch(f)
            if not m2 or m2.group(1) in claimed:
                continue
            unclaimed.append(f'[{g["label"]}] {f}={u.get("raw")!r}'
                             + ('（原值 0，未被本句主张）' if u.get('raw') == 0 else ''))
    if unclaimed:
        extra.append('t13 子记录句外槽未分配（不归属本句，仅登记原值；按档位分组）：'
                     + '、'.join(dict.fromkeys(unclaimed)))
    first = next((g for g in groups if g['child'] is not None), None)
    summary = (B17_TAG + '（多 t13 denju patternid 映射→HP 条件分支，R1 整改）：按源记录'
               '全部 pattern 引用分 %d 个 HP 档位条件组（%s）逐档出值；空 sinfo 分支不排除；'
               'HP 边界运行时语义待核查（原值保留＋推断档）；值行全部「推断」，不升「确认」。'
               % (len(groups), '、'.join(labels)) + '；'.join(extra))
    return dict(kind='promote', path='MULTI_T13_PATTERNID', hp_branch_mode=True,
                answers=answers, summary_reason=summary, extra_reasons=extra,
                hp_branch_conditions=labels, hp_branch_conditions_expected=labels,
                subject='味方全体', attrs=attrs, noncrit_attrs=noncrit,
                table=table, parent_chain=f'{via_desc}→全部 patternid 引用按 HP 档位分档',
                chain_record_id=(first['child'].get('record_id') if first else None),
                chain_layer=(first['child'].get('layer') if first else None),
                chain_key=(first['child_key'] if first else None),
                crit_promotion_key=(('inference_b14' if crit_promotion.get('b14_ext')
                                     else 'inference_b8') if crit_claimed else None),
                crit_pattern_record_id=(crit_promotion or {}).get('pattern_record_id'),
                crit_relay_record_id=(crit_promotion or {}).get('relay_record_id'),
                crit_relay_type=(crit_promotion or {}).get('relay_type'),
                crit_relay_slot=(crit_promotion or {}).get('relay_slot'),
                crit_carrier_record_id=(crit_promotion or {}).get('carrier_record_id'),
                crit_carrier_layer=(crit_promotion or {}).get('carrier_layer'),
                replaces_hint=prior_key, replaced_hint_text=prior_text,
                sent_no=sent_no, sent_total=sent_total)


def _run_multi(frag, table, layer, record_id, text, data, cid, boss_skill_refs,
               denju_pattern_refs, crit_promotion, prior_key, prior_text):
    """MULTI_T13：denju patternidN→pattern 文本→boss_skill_refs 归属登记→唯一 t13。
    R1 整改（20261023）：源记录引用 ≥2 个 pattern 且分成多个 HP 档位条件组时改走
    _run_multi_branches（空 sinfo 不排除、逐档出值）；单档/同档位行为零变化。"""
    if table != 'denju':
        return None  # charainfo 等表多 t13 行同法可解性未测，本批不做（留原 hint）
    if not denju_pattern_refs:
        return dict(kind='hint', path='MULTI_T13_PATTERNID', replaces_hint=prior_key,
                    reasons=['多 t13 映射不可达：links 该 denju 记录无 denju_pattern_refs 登记'])
    br = _run_multi_branches(frag, table, layer, record_id, text, data, cid,
                             boss_skill_refs, denju_pattern_refs, crit_promotion,
                             prior_key, prior_text)
    if br is not None:
        return br
    # patternidN→pattern：sinfo 非空且含本行片段的须恰 1 个（唯一命中）
    hits = []
    for p in denju_pattern_refs:
        sinfo = str(p.get('sinfo') or '').replace('\\n', '\n')
        if not sinfo:
            continue
        fragset = {sp['japanese'] for sp in fragment_positions(sinfo)}
        if frag in fragset:
            hits.append(p)
    if len(hits) != 1:
        return dict(kind='hint', path='MULTI_T13_PATTERNID', replaces_hint=prior_key,
                    reasons=['多 t13 映射不唯一（批 17）：本行片段命中 %d 个 sinfo 非空的 '
                             'pattern（%s）——归属歧义，不猜'
                             % (len(hits), '、'.join(str(h.get('reference_id')) for h in hits) or '无')])
    pat = hits[0]
    pid = pat.get('reference_id')
    # boss_skill_refs：reference_field 登记该 pattern 槽位引用的 bossskill 子记录中
    # 恰 1 个 type13（父记录 children 实测）
    parent, pkey, wb, same_count, fam_counter, via_desc, p_bsr, _ = _locate_parent(
        frag, table, layer, record_id, text, data, cid, boss_skill_refs)
    if parent is None:
        return dict(kind='hint', path='MULTI_T13_PATTERNID', replaces_hint=prior_key,
                    reasons=['多 t13 映射链不可达：父记录 %s 未定位' % (pkey,)])
    ref_ids = [str(r.get('reference_id')) for r in (p_bsr or [])
               if r.get('table') == 'bossskill'
               and str(r.get('reference_field') or '').startswith(f'bosspattern[{pid}].')]
    boss_kids = [c for c in parent.get('children') or [] if c.get('table') == 'bossskill']
    t13_kids = [c for c in boss_kids if c.get('effect_type') == 13]
    selected = [c for c in t13_kids if str(c.get('record_id')) in ref_ids]
    if len(selected) != 1:
        return dict(kind='hint', path='MULTI_T13_PATTERNID', replaces_hint=prior_key,
                    reasons=['多 t13 映射不唯一（批 17）：pattern bosspattern|%s 经 '
                             'boss_skill_refs reference_field 登记命中 %d 个本链 type13 子记录'
                             '（登记 %s，children t13 %s）——归属歧义，不猜'
                             % (pid, len(selected), ref_ids,
                                [c.get('record_id') for c in t13_kids])])
    child = selected[0]
    # 批 6 同门（形状/时长/同文一次/fam1 数）＋分区竞争句＋全字段复核
    # （G2 多 t13 已由上方 pattern 映射取代——对选中 t13 逐门复核，其余 t13 不取值）
    template = B6._norm_text(frag)
    attrs = [a for a in B6._ATTR_DETECT if a in template]
    noncrit = [a for a in attrs if a in B6.ATTR_PARAM]
    crit_claimed = crit_promotion is not None
    competitors = _competitor_sents(wb, frag)
    raws = {q: B6._raw_of(child, q) for q in ('skillparam1', 'skillparam2', 'skillparam6',
                                              'skillparam3', 'skillparam4', 'skillparam5')}
    exp = {B6.ATTR_PARAM[a] for a in noncrit}
    act = {q for q in ('skillparam1', 'skillparam2', 'skillparam6')
           if B6._num(raws.get(q)) and raws.get(q) != 0}
    gate_reasons = []
    if act != exp:
        gate_reasons.append('形状不符（U3）：句属性槽 %s ≠ 选中 t13 活性槽 %s' % (sorted(exp), sorted(act)))
    if not (B6._num(raws[B6.DUR_PARAM]) and raws[B6.DUR_PARAM] != 0):
        gate_reasons.append('持续时间槽 skillparam3 无非零值')
    if same_count > 1:
        gate_reasons.append('同文在记录正文出现 %d 次' % same_count)
    if fam_counter.get(B6.FAM1, 0) > 1:
        gate_reasons.append('同记录有 %d 条 FAM1 家族句（多 buff 句共享同一 type13）'
                            % fam_counter.get(B6.FAM1, 0))
    for comp in competitors:
        inter = sorted(set(comp['mapped']) & act)
        if inter:
            gate_reasons.append('竞争句「%s」（%s）映射槽 %s 与选中 t13 活性槽 %s 相交（%s）——'
                                '分区不成立' % (comp['text'], comp['fam'], comp['mapped'],
                                                sorted(act), inter))
    violations, claimed, zeros = _full_field_review(child, exp, crit_claimed)
    if violations:
        gate_reasons.append('t13 全字段复核（批 17）：选中 t13 存在已分配槽（%s）之外的非零槽 %s'
                            % (claimed, violations))
    if not re.search(r'上がる|上がり|上げる', frag):
        gate_reasons.append('方向门（U4）：句无「上がる」增益方向词')
    neg = [q for q in sorted(act) + ['skillparam3'] if B6._num(raws.get(q)) and raws.get(q) <= 0]
    if neg:
        gate_reasons.append('方向冲突（U4）：槽 %s 原值非正' % neg)
    if gate_reasons:
        return dict(kind='hint', path='MULTI_T13_PATTERNID', replaces_hint=prior_key,
                    reasons=gate_reasons)
    child_id = child.get('record_id')
    child_layer = child.get('layer')
    child_key = f'bossskill|{child_id}|{child_layer}'
    _pslot = next(p["slot"] for p in denju_pattern_refs if p.get("reference_id") == pid)
    parent_chain = (f'{via_desc}→{_pslot}→bosspattern|{pid}|{pat.get("layer")}'
                    f'→{child_key}（boss_skill_refs reference_field 归属登记）')
    slot = None
    for r in p_bsr or []:
        if r.get('table') == 'bossskill' and str(r.get('reference_id')) == str(child_id):
            slot = r.get('slot')
            break
    slot_desc = (f'bossskill 子记录经父记录 boss_skill_refs 槽位 {slot} 引用'
                 if slot else 'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）')
    # 其余 t13 子记录同值/异值兜底披露
    others = []
    for c in t13_kids:
        if str(c.get('record_id')) == str(child_id):
            continue
        oraws = {q: B6._raw_of(c, q) for q in ('skillparam1', 'skillparam2', 'skillparam3',
                                               'skillparam6')}
        same = all(_num_eq(raws[q], oraws[q]) for q in raws if q in oraws)
        others.append('bossskill|%s|%s 槽值 %s（%s）'
                      % (c.get('record_id'), c.get('layer'), oraws,
                         '与本行选中 t13 逐槽同值' if same else '与本行选中 t13 槽值不同——归属唯一性'
                         '由 pattern 映射保证，不跨记录取值'))
    arg_note = ('多 t13 归属（批 17）：denju patternidN→bosspattern sinfo 含本行片段唯一命中'
                '（bosspattern|%s|%s）→boss_skill_refs reference_field「bosspattern[%s].skillidX」'
                '归属登记→唯一 t13 %s；其余 t13 子记录：%s'
                % (pid, pat.get('layer'), pid, child_key,
                   '；'.join(others) or '（无）'))
    section_no = (crit_promotion or {}).get('section_no')
    section_count = (crit_promotion or {}).get('section_count')
    sent_no = (crit_promotion or {}).get('sent_no')
    sent_total = (crit_promotion or {}).get('sent_total') or 0
    # B17-R07 修复：crit_promotion 为 None（P2 多 t13 行）时也经 _sent_pos 定位句序/段位
    # （与 _run_partition 同法）；此前未调用致注记误写「正文句序未能定位」。
    if crit_promotion is None or sent_no is None:
        sent_no, sent_total, section_no, section_count = _sent_pos(wb, frag)
    answers, claimed_slots = _answers_and_meta(
        dict(t13=child, raws=raws, active=sorted(act), claimed=sorted(exp | {B6.DUR_PARAM}),
             zeros=zeros, competitors=competitors),
        parent_chain, child_key, slot_desc, sent_no, sent_total, section_no, section_count,
        arg_note, noncrit)
    if answers is None:
        return dict(kind='hint', path='MULTI_T13_PATTERNID', replaces_hint=prior_key,
                    reasons=claimed_slots)
    extra = ['多 t13 归属依据（批 17）：本行片段在 patternidN→bosspattern sinfo 中唯一命中；'
             'boss_skill_refs reference_field 显式登记该 pattern 的 bossskill 槽位引用；'
             '其余 t13 不取值（%s）' % ('；'.join(others) or '（无其他 t13）')]
    if crit_claimed:
        extra.append('批 8/14 既有 crit 值行零触碰：crit 段见本行既有 2012 链值行（crit 载体 '
                     's_ability 链两 pattern 共用，provenance 不变）')
    unclaimed = _unclaimed_note(child, claimed_slots, crit_claimed)
    if unclaimed:
        extra.append('t13 子记录句外槽未分配（不归属本句，仅登记原值）：'
                     + '、'.join(dict.fromkeys(unclaimed)))
    summary = (B17_TAG + '（多 t13 denju patternid 映射）：值行来源＝' + parent_chain
               + '；唯一 t13＝父链末位记录，其余 t13 不取值（兜底披露见注记）；值行全部'
               '「推断」，不升「确认」。' + '；'.join(extra))
    return dict(kind='promote', path='MULTI_T13_PATTERNID', answers=answers,
                summary_reason=summary, extra_reasons=extra,
                subject='味方全体', attrs=attrs, noncrit_attrs=noncrit,
                table=table, parent_chain=parent_chain,
                chain_record_id=child_id, chain_layer=child_layer, chain_key=child_key,
                crit_promotion_key=(('inference_b14' if crit_promotion.get('b14_ext')
                                     else 'inference_b8') if crit_claimed else None),
                crit_pattern_record_id=(crit_promotion or {}).get('pattern_record_id'),
                crit_relay_record_id=(crit_promotion or {}).get('relay_record_id'),
                crit_relay_type=(crit_promotion or {}).get('relay_type'),
                crit_relay_slot=(crit_promotion or {}).get('relay_slot'),
                crit_carrier_record_id=(crit_promotion or {}).get('carrier_record_id'),
                crit_carrier_layer=(crit_promotion or {}).get('carrier_layer'),
                replaces_hint=prior_key, replaced_hint_text=prior_text,
                sent_no=sent_no, sent_total=sent_total)


def evaluate(record: dict, frag: str, table: str, layer: str | None = None, record_id=None,
             text: str | None = None, data=None, cid=None, boss_skill_refs=None,
             denju_pattern_refs=None, b6_result=None, b15_result=None, crit_promotion=None):
    """批 17 P0 收尾审核。返回 None（不属本批范围/门前置不成立）或
    dict(kind='promote'|'hint', path=H1_partition|H2_duration_share|MULTI_T13_PATTERNID)。"""
    if data is None or cid is None or table not in B6.TABLES or not isinstance(record, dict):
        return None
    prior_key, prior_text = _prior_hint_text(b15_result, b6_result)
    if prior_key is None:
        return None
    b6_reasons = (b6_result.get('reasons') or []) if b6_result and b6_result.get('kind') == 'hint' else []
    # 路径 1：多 t13（b6 G2 歧义行；denju）
    if any(_MULTI_T13_MARK in r for r in b6_reasons):
        return _run_multi(frag, table, layer, record_id, text, data, cid, boss_skill_refs,
                          denju_pattern_refs, crit_promotion, prior_key, prior_text)
    crit_ok = (crit_promotion is not None and crit_promotion.get('kind') == 'promote'
               and crit_promotion.get('relay_type') == 13)
    if crit_ok and b15_result and b15_result.get('kind') == 'hint':
        reasons = b15_result.get('reasons') or []
        if b15_result.get('case') == 'A':
            # H1：FAM1+crit 行（批 6 G4×批 15 残余门竞争句）→ 槽位分区
            # （非竞争类原因——U1/方向/U2 链——不进本批，既有 hint 零触碰）
            if _reason_comp_class(reasons):
                return _run_partition(frag, table, layer, record_id, text, data, cid,
                                      boss_skill_refs, crit_promotion, prior_key,
                                      prior_text,
                                      '；crit 段由批 8/14 既有 2012 链值行兑现（零触碰）',
                                      'H1 槽位分区')
            return None
        if b15_result.get('case') == 'B':
            template_chk = B6._norm_text(frag)
            noncrit_chk = [a for a in B6._ATTR_DETECT if a in template_chk
                           and a in B6.ATTR_PARAM]
            if noncrit_chk:
                # case B 带 noncrit 主张（如【共鳴必殺】前缀行，b6 不评估）——竞争类
                # hint 走槽位分区（H1 同法）
                if _reason_comp_class(reasons):
                    return _run_partition(frag, table, layer, record_id, text, data, cid,
                                          boss_skill_refs, crit_promotion, prior_key,
                                          prior_text,
                                          '；crit 段由批 8/14 既有 2012 链值行兑现（零触碰）',
                                          'H1 槽位分区')
                return None
            if (B6.DUR_ATTR in frag
                    and all(_U5_MARK in r for r in reasons)):
                # H2：条件暴击行（仅 crit＋时长主张）→ 时长槽共享（D1 裁决）
                return _run_h2(frag, table, layer, record_id, text, data, cid,
                               boss_skill_refs, crit_promotion, prior_key, prior_text,
                               record=record)
            return None
        return None
    if not crit_ok and b6_reasons and _reason_comp_class(b6_reasons):
        # P2 溢出：b6 hint fam11/13 冲突/同属性竞争句行（无 crit）→ 同法槽位分区
        # （B17-R08：标签内不再嵌套括号/叠词——汇总模板也不再追加「：槽位分区」）
        return _run_partition(frag, table, layer, record_id, text, data, cid,
                              boss_skill_refs, None, prior_key, prior_text,
                              '；本行无暴击主张', 'P2 溢出：fam 竞争句槽位分区',
                              hint_on_fail=False)
    return None
