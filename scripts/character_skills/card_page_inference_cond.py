"""模板作用域推断层——批 4：句后条件扩展（基础 type8 记录＋兄弟 sub 记录条件增幅）。

设计与范围依据：``output/character_skills/inference_inventory/b4_cond_scope.md``（批 4 前置
结构审计产物；逐行明细 work/character_skills_b4_cond/b4_promotable.json、b4_hints.jsonl）。
独立于批 3 type8 模块（不共用范围、独立标记）；句位/句后文本/同文次数/方向判定复用
``card_page_inference_type8`` 的同口径实现（不复制逻辑，避免两批判定漂移）。

精确范围（审计实测 172 行行集＝批 3「同段句后有后续文本」163＋同文多次行结构带句后文本 9；
本模块逐行重判，须同时满足才进入本批）：

* 记录类型 ``skilllist`` 且 ``ability == 8``（基础 type8 记录，0 行多 effect_type）；
* 基础句（frag）匹配批 3 严格句正则（属性名词「と」连接＋「が上がる。」），不含句首连接词；
* 同段（下一个 ◆ 之前）句后有实质后续文本（tail）——无句后文本的行不在本批（交批 3 口径）。

结构分工判定模型（scope §2.4）：「（条件）、効果が上がり、さらに…」tail 的主张按槽位覆盖
匹配兄弟记录——基础句主张（攻撃力/移動速度/防御力）由父 type8 记录 param1/2/3 承载；tail
主张（効果が上がり→基础属性增幅、さらに…クリティカル→暴击两槽、HPが徐々に回復→周期回复）
由恰好一个兄弟记录承载：逐主张槽有已确认规则＋方向一致＋无未主张活性槽＋tail 按句消费后
无残余主张＋至多 1 个条件句（单条件链→单兄弟记录）。兄弟记录经父记录数据侧 ``sub`` 字段
关联（link_skills.py:612-630 单层展开，link_kind=sub_effect）；兄弟记录自身的 sub 链不在本批
裁决（scope §6.5）。

双记录映射（scope §4.2，本批核心）——每行产出两组值行、各自注明来源记录：

* 基础句值行：frag 主张属性 → 父 type8 记录 /param1/2/3（rules.json ``skilllist|8|/paramN``），
  note 注明「来源记录＝<parent_rec_key>（基础 type8 记录，无条件常时）」；
* 条件增幅值行：tail 主张槽 → 兄弟记录对应参数（rules.json ``skilllist|<child_type>|/paramN``，
  本批涉及 36/80/67/1005 四类、均「已确认数值换算」），note 注明「来源记录＝
  skilllist|<child_record_id>|<layer>|ability=<child_type>（经父记录 sub 字段关联的子效果记录，
  link_kind=sub_effect）＋条件文本逐字」。
* 两行都不得混合来源；禁止把「3.0×1.75」这类跨记录乘积写进任何值行（scope §6.1/§6.2）。

硬边界（逐行强制；scope §4/§6）：

* **只升「推断」**：值行 numeric_evidence/association_evidence 一律「推断」，行级标注
  「推断（模板批 4 条件扩展）」、evidence_scope=TEMPLATE_BATCH4_COND_EXT；不进入整行确认。
* **条件文本逐字**：条件前缀原样进 note，不做数值换算；兄弟记录 param0/iParam0/param6/param8
  等条件/筛选槽**不产出数值答案**、只注记原值（scope §6.3）。
* **门控证据分级披露（逐行，按兄弟类型）**：80/67＝A 级（条件谓词受控原生核实 native_checks
  composite_80 / composite_67）；36＝B 级（门控无原生证据；类型语料 27/27 条 type36 实质正文
  均为 HP 阈值条件增幅＋本行阈值数值一致）；1005＝C 级（仅值规则已确认，条件门控无原生/语料
  证据——audit §4.4 按结构通过列入候选、note 显式披露 C 级）。
* **方向审核父/子两侧**：父 param1/2>1、param3<1（受伤量乘数方向按代码）；兄弟槽 attack/move>1、
  defence<1、暴击/回复>0；冲突整行留 hint（scope §4.5）。
* **非首段/段中/同文多次行不晋级**（scope §6.6）：即使兄弟结构核实通过也留 hint（INFR-05/R-03
  行级归属歧义未被本批裁决）；基础句含暴击名词的 PART 行本批不产生候选（scope §4.6）。
* **INFR-01 字段级证据**：值行 evidence 按字段取 rules.json rule["evidence"]＋路径件存在性检查
  （缺失显式失败）；child 类型证据源含 dispatch_map.json。
* **INFR-02 适用范围披露（R-02 教训：按记录分支）**：type36/80/67/1005 规则同样 occurrences
  未登记、无逐记录文本核验大样本——兄弟记录值行与父记录值行同为「同类型原生规则外推，
  未逐记录审定」披露口径（scope §6.4）。
* **多段披露／句外参数注记**沿用批 3：晋级行登记「本记录另含其他◆段」；父记录未主张 param 槽
  注记原值（type8 三条 apply 路径不读取 param0/param4）；其余兄弟记录仅登记为其他段载体、
  不归属（scope §2.4 判定 5）。
"""
from __future__ import annotations

import math
import re

import rules as R
import card_page_inference_type8 as TYPE8

COND_TAG = '推断（模板批 4 条件扩展）'
COND_SCOPE = 'TEMPLATE_BATCH4_COND_EXT'
COND_FAMILY = '句后条件扩展（基础 type8＋兄弟记录条件增幅）'

NUMERIC_SOURCE_BASE = '模板推断（批 4 条件扩展·基础句）'
NUMERIC_SOURCE_COND = '模板推断（批 4 条件扩展·条件增幅）'

# tail 主张类 → 答案 quantity_kind 关键词（仅倍率/加算贡献类效果槽；条件/配置槽不参与匹配）。
# 与批 4 审计 match_b4.py CLAIM_KIND 同一分类。
CLAIM_KIND = {
    'attack': ('攻击倍率',),
    'move': ('移动速度乘数',),
    'defence': ('受伤量倍率',),
    'crit_rate': ('暴击概率加算',),
    'crit_power': ('暴击伤害系数加算',),
    'regen': ('周期回复量系数',),
}
CLAIM_LABEL = {'attack': '攻击增幅', 'move': '移动速度增幅', 'defence': '防御（受伤量）增幅',
               'crit_rate': '暴击发生率增幅', 'crit_power': '暴击威力增幅', 'regen': 'HP 周期回复'}
# 条件/配置槽 kind（不算效果主张，也不参与「未主张活性槽」检查）——audit match_b4.py 同表。
CONFIG_KIND_MARKS = ('位图', '筛选', '阈值', '条件', '选择码', '持续时间', '概率阈值',
                     '开局', '位索引', '上限档位', '计数上限', '开关', '编号', '配置')
# 兄弟类型 → 门控证据分级（b4_cond_scope.md §2.2/§3；按兄弟类型披露，逐行 note 落地）。
GATE_TIER = {36: 'B', 80: 'A', 67: 'A', 1005: 'C'}
GATE_TIER_NOTE = {
    'A': '条件谓词受控原生核实（native_checks composite_80_uses_both_mana_predicates／'
         'composite_67_threshold_is_inclusive_ge）；「sub 关联记录被该谓词门控」仍为数据侧结构推断',
    'B': '条件门控无原生证据；类型语料一致（27/27 条 type36 实质正文均为「HPがN%以上の時…」'
         '条件增幅）＋本行阈值数值一致（param0=0.NN ↔ 文本N%）',
    'C': '仅值规则已确认，条件门控无原生/语料证据（type1005 独立语料异质）',
}
CHILD_SCOPE_NOTE = {
    36: 'type36 规则无逐记录文本核验样本（rules.json skilllist|36|/* 的 occurrences 未登记）；'
        '已核依据为 dispatch_map 分支解析（type36 与 type8 同叶同槽）＋类型语料 27/27；'
        '本值行按同类型（ability36）原生规则外推，未逐记录审定，不属逐记录确认',
    80: 'type80 规则无逐记录文本核验样本（rules.json skilllist|80|/* 的 occurrences 未登记）；'
        '已核依据为复合分支原生核实（native_checks composite_80 等，Unicorn+静态双路解析 53/53）'
        '＋filter_dictionary 取值分布对照；本值行按同类型（ability80）原生规则外推，未逐记录审定，'
        '不属逐记录确认',
    67: 'type67 规则无逐记录文本核验样本（rules.json skilllist|67|/* 的 occurrences 未登记）；'
        '已核依据为复合分支原生核实（native_checks composite_67_threshold_is_inclusive_ge 等）'
        '＋filter_dictionary 取值分布对照；本值行按同类型（ability67）原生规则外推，未逐记录审定，'
        '不属逐记录确认',
    1005: 'type1005 仅值槽规则已确认（与 type8 同叶同槽、dispatch_map 分支解析）；条件门控无'
          '原生/语料证据（C 级）；本值行按同类型（ability1005）原生规则外推，未逐记录审定，'
          '不属逐记录确认',
}

# tail 主张解析（audit match_b4.py RECOGNIZED_PHRASES 同表；消费模型＝逐句剥除已识别主张短语）。
RECOGNIZED_PHRASES = [
    r'効果が上が[りる]',
    r'(さらに)?クリティカル発生率(とクリティカル威力)?が(一定時間)?上が[りる]',
    r'クリティカル威力が(一定時間)?上が[りる]',
    r'HPが徐々に回復する',
    r'また、?',
    r'さらに',
    r'一定時間',
]

_CLASS_OF_PARENT_FIELD = {'param1': 'attack', 'param2': 'move', 'param3': 'defence'}

_EVIDENCE_CACHE = {}


def _kind_is_config(kind):
    return any(m in (kind or '') for m in CONFIG_KIND_MARKS)


def _claim_class(kind):
    for cls, marks in CLAIM_KIND.items():
        if any(m in kind for m in marks):
            return cls
    return None


def _direction_ok(cls, raw):
    """兄弟槽方向：attack/move>1、defence<1（受伤量乘数方向按代码）、暴击/回复>0（audit 同口径）。"""
    if not isinstance(raw, (int, float)) or isinstance(raw, bool) or not math.isfinite(raw):
        return False
    if cls == 'defence':
        return raw < 1
    if cls in ('attack', 'move'):
        return raw > 1
    return raw > 0


def _child_field_evidence(child_type, field_path):
    """INFR-01：按字段取 rules.json rule["evidence"]；路径型条目缺失显式失败（child 类型同法）。

    复合类型（80/67 等）的路径件条目可带括注（如
    「scripts/character_skills/skilllist_types.py（composite_rule_rows 由分支可达体重算）」）——
    截取「（/(／空白之前」的路径部分核对存在性；截不出已存在文件的条目按缺失显式失败。
    """
    key = (child_type, field_path)
    if key not in _EVIDENCE_CACHE:
        rule = R.rule_for('skilllist', child_type, field_path)
        if rule is None:
            raise ValueError(f'模板批 4 条件扩展证据解析异常（INFR-01）：rules.json 无 '
                             f'skilllist|{child_type}|{field_path} 规则')
        entries = list(rule.get('evidence') or [])
        if not entries:
            raise ValueError(f'模板批 4 条件扩展证据解析异常（INFR-01）：skilllist|{child_type}|'
                             f'{field_path} 的 rules.json evidence 为空')
        from pathlib import Path
        path_files = []
        for e in entries:
            if not e.startswith(('scripts/', 'output/')):
                continue
            head = re.split(r'[（( \s]', e, 1)[0]
            if head and Path(head).is_file():
                if head not in path_files:
                    path_files.append(head)
            else:
                raise FileNotFoundError(f'模板批 4 条件扩展证据文件缺失（INFR-01）：'
                                        f'skilllist|{child_type}|{field_path} 条目 {e!r}')
        _EVIDENCE_CACHE[key] = (rule, entries, path_files)
    return _EVIDENCE_CACHE[key]


def parse_claims(tail, base_mapped):
    """tail → (claims, residuals, n_cond, cond_prefixes)。audit match_b4.py parse_claims 同口径：
    逐句剥掉已识别主张短语；条件前缀（首个主张短语之前）豁免并逐字保留；残余非空 → 其他主张。"""
    claims = set()
    residuals = []
    cond_prefixes = []
    n_cond = 0
    for s in (x for x in tail.split('。') if x.strip()):
        if re.search(r'効果が上が[りる]', s):
            claims |= set(base_mapped)
        if 'クリティカル発生率' in s:
            claims.add('crit_rate')
        if 'クリティカル威力' in s:
            claims.add('crit_power')
        if 'HPが徐々に回復する' in s:
            claims.add('regen')
        if re.search(r'(の時|の場合|ていると|ると|れば|たび|以上|以下)', s):
            n_cond += 1
        first_pos = min((m.start() for ph in RECOGNIZED_PHRASES for m in re.finditer(ph, s)),
                        default=-1)
        cond_prefix = s[:first_pos] if first_pos >= 0 else s
        if cond_prefix.strip('、'):
            cond_prefixes.append(cond_prefix.strip('、'))
        rest = s[first_pos:] if first_pos >= 0 else ''
        for ph in RECOGNIZED_PHRASES:
            rest = re.sub(ph, '', rest)
        rest = rest.strip('、。 \u3000')
        if rest:
            residuals.append(rest)
    return claims, residuals, n_cond, cond_prefixes


def _child_offers(child_record, child_type):
    """child 的效果主张供给：(claim_class -> [(field_path, raw)])；kind 取自 rules.json 换算器。"""
    offers = {}
    for key in sorted(child_record):
        if not R.is_param_like(key):
            continue
        value = child_record[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            continue
        ans = R.answer_for('skilllist', child_type, '/' + key, value, child_record)
        kind = (ans or {}).get('quantity_kind')
        if not kind or _kind_is_config(kind):
            continue
        cls = _claim_class(kind)
        if cls is not None:
            offers.setdefault(cls, []).append(('/' + key, value))
    return offers


def _child_condition_slots(child_record, claimed_fields):
    """条件/筛选槽＋未主张槽原值注记（不产出数值答案，scope §6.3）。"""
    out = []
    for key in sorted(child_record):
        if not R.is_param_like(key):
            continue
        value = child_record[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            continue
        if '/' + key in claimed_fields:
            continue
        out.append(f'/{key}={value}')
    return out


def _threshold_want(tail):
    m = re.search(r'HPが(\d+)％?%?(以上|以下)', tail)
    if m:
        return float(m.group(1)) / 100.0, 'HP' + m.group(2)
    m = re.search(r'(\d+)人以上', tail)
    if m:
        return float(m.group(1)), '人数'
    return None


def evaluate(record: dict, frag: str, layer: str | None = None, record_id=None,
             text: str | None = None, sub_children=None):
    """对一行做句后条件扩展审核，返回 None（不属本批范围）或审核结果 dict。

    sub_children：父记录 ``sub`` 字段单层展开的兄弟记录（resolved）列表，每项含
    reference_id／layer／record（调用点从 links 的 sub_effect_refs 取，link_kind=sub_effect）。

    结果 dict：kind='promote'（含 answers／summary_reason／extra_reasons）或 'hint'（含 reasons）。
    """
    if not isinstance(record, dict) or record.get('ability') != 8:
        return None
    if not TYPE8.STRICT_PATTERN.match(frag):
        return None
    if TYPE8.CONNECTIVE_PATTERN.match(frag):
        return None  # 连接词句交批 3 口径（本批行集内 0 行）
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    body = body[:cut] if cut >= 0 else body
    if not body:
        return None  # 正文不可用：句位/句后文本无法核验，交批 3 口径留 hint
    starts = TYPE8._occurrences(body, frag)
    if len(starts) > 1:
        pass  # 同文多次行在审计行集内（9 行，均兼非首段）：继续解析、行级强制留 hint
    if not starts:
        return None
    positions = [TYPE8._section_no(body, pos) + (TYPE8._trailing(body, pos, frag) != '',)
                 for pos in starts]
    if not any(p[2] for p in positions):
        return None  # 无句后文本：不在本批（批 3 tier1 或其他 hint 类）

    # --- 基础句主张与父记录方向审核（批 3 §5.3 同口径） ----------------------------------
    attrs = list(dict.fromkeys(TYPE8.ATTR_PATTERN.findall(frag)))
    mapped = [a for a in attrs if a in TYPE8.ATTR_FIELD]
    base_crit = [a for a in attrs if a not in TYPE8.ATTR_FIELD]
    base_mapped = [_CLASS_OF_PARENT_FIELD[TYPE8.ATTR_FIELD[a]] for a in mapped]

    tails = []
    for pos, (sec, _head, trail) in zip(starts, positions):
        if trail:
            tails.append(TYPE8._trailing(body, pos, frag))
    tail = '｜'.join(tails)
    claims, residuals, n_cond, cond_prefixes = parse_claims(tail, base_mapped)

    reasons = []
    attr_hints = []

    # --- 父记录两侧审核 ------------------------------------------------------------------
    parent_conflict = []
    for attr in mapped:
        field = TYPE8.ATTR_FIELD[attr]
        verdict, detail = TYPE8._direction_check(field, record.get(field))
        if verdict == 'conflict':
            parent_conflict.append(f'{attr}（/{field}）{detail}')
        elif verdict == 'invalid':
            attr_hints.append(f'{attr}（/{field}）{detail}，基础句值行无法产出')
    if base_crit:
        reasons.append('基础句含暴击名词：批 4 候选不含暴击基础句（scope §4.6），暴击名词映射沿用'
                       '批 3 口径（type8 三条 apply 路径不读暴击槽），本行不晋级')
    if parent_conflict:
        reasons.append('父记录方向冲突（沿用批 3 方向审核）：' + '；'.join(parent_conflict) + '；不晋级')
    field_by_cls = {'attack': '/param1', 'move': '/param2', 'defence': '/param3'}
    parent_unclaimed = [f'{field_by_cls[c]}={record.get(field_by_cls[c][1:])}'
                        for c in field_by_cls if c not in base_mapped
                        and isinstance(record.get(field_by_cls[c][1:]), (int, float))
                        and not isinstance(record.get(field_by_cls[c][1:]), bool)
                        and record.get(field_by_cls[c][1:]) != 1]
    if parent_unclaimed:
        reasons.append('父记录存在基础句未主张的活性 param1/2/3 槽：' + '、'.join(parent_unclaimed)
                       + '；基础句与记录参数分工不一致，保守留 hint')

    # --- 兄弟记录覆盖匹配（audit §2.4 判定模型） ------------------------------------------
    children = [c for c in (sub_children or []) if c.get('resolved') and c.get('record')]
    child_infos = []
    for c in children:
        child_record = c['record']
        child_type = child_record.get('ability')
        offers = _child_offers(child_record, child_type) if isinstance(child_type, int) else {}
        child_infos.append(dict(ref=c, child_record=child_record, child_type=child_type,
                                offers=offers))

    full_match = []
    if claims:
        for ci in child_infos:
            if not set(ci['offers']) >= claims:
                continue
            if all(all(_direction_ok(cls, raw) for _f, raw in ci['offers'][cls])
                   for cls in claims):
                full_match.append(ci)
    for ci in full_match:
        ci.setdefault('unclaimed_active', False)
        for cls, slots in ci['offers'].items():
            if cls not in claims and any(_direction_ok(cls, raw) for _f, raw in slots):
                ci['unclaimed_active'] = True

    threshold_note = None
    threshold_mismatch = False
    want = _threshold_want(tail)
    if full_match and want:
        p0 = full_match[0]['child_record'].get('param0')
        if isinstance(p0, (int, float)) and not isinstance(p0, bool) and math.isfinite(p0):
            threshold_note = (want[1], want[0], p0, abs(p0 - want[0]) < 1e-4)
            threshold_mismatch = not threshold_note[3]
        else:
            threshold_note = (want[1], want[0], None, None)

    # --- 结构 verdict（scope §3 分类；audit match_b4 同序——结构原因不被父侧/暴击问题抢占，
    #     后者作为附加 hint 原因登记并同样强制 hint） ------------------------------------------
    verdict = None
    if residuals:
        verdict = 'P-C'
        reasons.append('句后文本含无法由兄弟记录已确认规则承载的其他效果主张（消费后残余）：'
                       + '；'.join(residuals) + '；保守留 hint（scope §3 P-C）')
    elif n_cond > 1:
        verdict = 'P-E'
        reasons.append(f'句后文本含 {n_cond} 个条件句，超出「单条件链→单兄弟记录」模式，'
                       '保守留 hint（scope §3 P-E／§6.7）')
    elif parent_conflict or parent_unclaimed:
        verdict = 'PARENT'
    elif threshold_mismatch:
        verdict = 'THRESHOLD'
        reasons.append(f'条件阈值与兄弟记录 param0 不一致（文本「{threshold_note[0]}」'
                       f'阈值 {threshold_note[1]} vs 记录 param0={threshold_note[2]}），分工不成立，'
                       '保守留 hint')
    elif len(full_match) > 1:
        verdict = 'AMBIGUOUS'
        reasons.append(f'{len(full_match)} 个兄弟记录均可覆盖句后主张'
                       f'（{[ci["ref"].get("reference_id") for ci in full_match]}），归属歧义，'
                       '保守留 hint')
    elif not claims:
        verdict = 'NO_CLAIM'
        reasons.append('句后文本未解析出可映射效果主张，保守留 hint')
    elif not full_match:
        verdict = 'P-B'
        if not children:
            reasons.append('记录无 sub_ids/children（无兄弟记录可承载条件增幅），保守留 hint'
                           '（scope §3 P-B）')
        else:
            cov = {}
            for cls in sorted(claims):
                cov[cls] = sum(1 for ci in child_infos if cls in ci['offers']
                               and all(_direction_ok(cls, raw) for _f, raw in ci['offers'][cls]))
            reasons.append('兄弟记录无已确认规则或覆盖不齐（逐主张槽可承载兄弟计数：'
                           + '、'.join(f'{CLAIM_LABEL[c]}={n}' for c, n in cov.items())
                           + '；须同一兄弟记录覆盖全部主张；无规则类型如 type69/51/9/1079 等需另行'
                             '原生核实其槽位语义，本批不预设），保守留 hint（scope §3 P-B）')
    elif full_match[0].get('unclaimed_active'):
        verdict = 'P-D'
        reasons.append('唯一匹配兄弟记录存在文本未主张的活性效果槽（文本与记录分工不一致），'
                       '保守留 hint（scope §3 P-D）')
    else:
        verdict = 'CANDIDATE'

    # --- 行级遗留阻塞（scope §6.6：非首段/段中/同文多次行不晋级） --------------------------
    residual_blockers = []
    if len(starts) > 1:
        nos = '、'.join(str(p[0]) for p in positions)
        residual_blockers.append(
            f'同文在记录正文出现 {len(starts)} 次（第 {nos} 段），两处出现各有句后文本时链级归属叠加'
            '行级同文歧义，本批不晋级（scope §6.6）')
    section_no, at_head, _has_trailing = positions[0]
    if section_no > 1 or not at_head:
        residual_blockers.append(
            f'本行为第 {section_no} 段' + ('' if at_head else '的段中句')
            + '（非首段首句）：行级归属歧义，本批不晋级（scope §6.6）')

    if verdict != 'CANDIDATE' or residual_blockers or attr_hints or base_crit \
            or parent_conflict or parent_unclaimed or not mapped:
        if not mapped and not any('基础句含暴击名词' in r for r in reasons):
            reasons.append('基础句属性在 type8 记录上无字段可映射，保守留 hint')
        if attr_hints:
            reasons.extend(attr_hints)
        if verdict == 'CANDIDATE' and residual_blockers:
            reasons.insert(0, '兄弟记录结构核实通过（单条件链＋单兄弟记录精确覆盖，本应候选），'
                              '但行级存在下列遗留阻塞，本批留 hint（scope §3「结构通过但行级遗留阻塞」）')
        reasons.extend(residual_blockers)
        return dict(kind='hint', reasons=reasons, attrs=attrs, claims=sorted(claims),
                    tail=tail, verdict=verdict or 'HINT',
                    residual_blockers=residual_blockers, section_no=section_no,
                    section_count=TYPE8._section_count(body))
    return _promote(record, frag, layer, record_id, mapped, base_mapped, claims,
                    cond_prefixes, tail, full_match[0], child_infos, section_no, body,
                    threshold_note)


def _promote(record, frag, layer, record_id, mapped, base_mapped, claims, cond_prefixes,
             tail, ci, child_infos, section_no, body, threshold_note):
    """晋级行：双记录映射两组值行（基础句→父 type8；条件增幅→兄弟记录），各自注来源（scope §4.2）。"""
    parent_rec_key = f'skilllist|{record_id}|{layer}|ability=8'
    child = ci['ref']
    child_record = ci['child_record']
    child_type = ci['child_type']
    child_id = child.get('reference_id')
    child_layer = child.get('layer')
    child_rec_key = f'skilllist|{child_id}|{child_layer}|ability={child_type}'
    condition_verbatim = '；'.join(cond_prefixes)
    tier = GATE_TIER.get(child_type, '?')
    tier_note = GATE_TIER_NOTE.get(tier, '门控证据分级未知')
    extra = []

    answers = []
    # --- 基础句值行（父 type8 记录；来源记录逐行注明） -------------------------------------
    for attr in mapped:
        field = TYPE8.ATTR_FIELD[attr]
        rule = R.rule_for('skilllist', 8, '/' + field)
        value = record.get(field)
        verdict, detail = TYPE8._direction_check(field, value)
        converted = R.answer_for('skilllist', 8, '/' + field, value, record)
        entries, path_files = TYPE8._field_evidence(field)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=value, field_path='/' + field,
            numeric_source=NUMERIC_SOURCE_BASE, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=COND_SCOPE,
            rule_key=f'skilllist|8|/{field}', rule_status=rule.get('status'),
            conversion=rule.get('conversion'), conditions=converted.get('conditions'),
            rule_limits=rule.get('limits'),
            evidence=list(rule.get('evidence') or []),
            evidence_paths=list(path_files),
            note=(f'模板批 4 条件扩展·基础句值行（来源记录＝{parent_rec_key}，基础 type8 记录，'
                  f'无条件常时）；句中「{attr}」→/{field} 1:1 映射；规则键 skilllist|8|/{field}；'
                  f'原值 {value}；方向审核 {detail}；证据按 rules.json rule["evidence"]'
                  f'（路径件 {path_files}）；适用范围：{TYPE8._scope_note(record_id, field, layer)}'),
            quantitative=True))

    # B4-R01（DeepSeek 批4审查）：句外参数排除集合只记基础句值行字段；在追加条件增幅
    # 值行之前固定。此前用全量 answers 的 field_path 集合，子记录 /param4、/param5
    # （type36）、/param7、/param8（type80）、/param6、/param7（type67）与父记录同名字段
    # 相撞，父记录同名槽被误当作「已分配」而漏列（33/37 行；4227 整条注记缺失）。
    base_field_paths = {a['field_path'] for a in answers}

    # --- 条件增幅值行（兄弟记录；来源记录＋逐字条件＋门控分级逐行注明） ---------------------
    claimed_fields = {}
    for cls in sorted(claims):
        slots = ci['offers'].get(cls) or []
        if len(slots) != 1:
            return dict(kind='hint', attrs=mapped, claims=sorted(claims), tail=tail,
                        verdict='FIELD_AMBIGUOUS',
                        reasons=[f'主张类 {CLAIM_LABEL[cls]} 在兄弟记录 {child_rec_key} 上对应 '
                                 f'{len(slots)} 个已确认规则槽（{slots}），无法 1:1 归属，保守留 hint'],
                        residual_blockers=[], section_no=section_no,
                        section_count=TYPE8._section_count(body))
        claimed_fields[cls] = slots[0]
    for cls in sorted(claims):
        field_path, raw = claimed_fields[cls]
        rule, entries, path_files = _child_field_evidence(child_type, field_path)
        converted = R.answer_for('skilllist', child_type, field_path, raw, child_record)
        if _direction_ok(cls, raw):
            direction = {'attack': f'方向一致（v={raw}>1）', 'move': f'方向一致（v={raw}>1）',
                         'defence': f'方向一致（v={raw}<1，受伤量乘数方向按代码）'}.get(
                             cls, f'方向一致（v={raw}>0）')
        else:
            direction = f'方向审核未通过（v={raw}）'
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path=field_path,
            numeric_source=NUMERIC_SOURCE_COND, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=COND_SCOPE,
            rule_key=f'skilllist|{child_type}|{field_path}', rule_status=rule.get('status'),
            conversion=rule.get('conversion'), conditions=converted.get('conditions'),
            rule_limits=rule.get('limits'),
            evidence=list(rule.get('evidence') or []),
            evidence_paths=list(path_files),
            note=(f'模板批 4 条件扩展·条件增幅值行（来源记录＝{child_rec_key}，经父记录 '
                  f'{parent_rec_key} 的 sub 字段关联的子效果记录，link_kind=sub_effect）；'
                  f'对应句后主张：{CLAIM_LABEL[cls]}；条件文本（逐字）：「{condition_verbatim}」；'
                  f'门控证据分级 {tier}（{tier_note}）；规则键 skilllist|{child_type}|{field_path}；'
                  f'原值 {raw}；方向审核 {direction}；证据按 rules.json rule["evidence"]'
                  f'（路径件 {path_files}）；适用范围：{CHILD_SCOPE_NOTE.get(child_type, "")}'
                  f'；本值行不与基础句值行合并、不写跨记录乘积'),
            quantitative=True))

    # --- 晋级行注记 ------------------------------------------------------------------------
    extra.append('双记录映射边界（scope §6.1/§6.2）：基础句值行仅含父 type8 /param1/2/3 无条件值；'
                 '条件增幅值行仅含兄弟记录参数＋逐字条件；两值行不合并为一条数值答案、不写跨记录'
                 '乘积（引擎侧两记录分别乘入因子、触发条件不同，合并数无单记录证据）')
    other = []
    for key in sorted(record):
        if re.match(r'^(param|iParam|iparam|skillparam|flag|skillflag)\d+$', key) \
                and ('/' + key) not in base_field_paths:
            value = record[key]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                other.append(f'/{key}={value}')
    if other:
        extra.append('父记录句外参数未分配（不归属本句，仅登记原值；type8 三条 apply 路径不读取 '
                     'param0/param4 槽——native_checks type8_slots_attack_move_defence）：'
                     + '、'.join(other))
    cond_slots = _child_condition_slots(child_record,
                                        {f for f, _r in claimed_fields.values()})
    extra.append(f'兄弟记录条件/未主张槽原值注记（不产出数值答案，条件语义以原文逐字交付'
                 f'——scope §6.3；门控证据分级 {tier}）：'
                 + ('、'.join(cond_slots) if cond_slots else '（无数值槽）'))
    others = [f"skilllist|{o['ref'].get('reference_id')}（ability={o['child_type']}）"
              for o in child_infos if o is not ci]
    if others:
        extra.append('父记录 sub 数组另有其他兄弟记录（其他◆段载体，本行 tail 不归属，scope §2.4 '
                     '判定 5；单层展开为界，其自身 sub 链不裁决）：' + '、'.join(others))
    if threshold_note:
        ok = threshold_note[3]
        extra.append(f'阈值核对（旁证）：文本「{threshold_note[0]}」阈值 {threshold_note[1]} ↔ 兄弟记录 '
                     f'param0={threshold_note[2]}（{"一致" if ok else "不一致"}）')
    section_count = TYPE8._section_count(body)
    if section_count > 1:
        extra.append(f'本记录另含其他◆段（共 {section_count} 段），其效果未被本句消费、本轮不归属'
                     '（INFR-05 多段披露）')
    base_scope = TYPE8._scope_note(record_id if isinstance(record_id, int) else None,
                                   mapped[0], layer)
    summary = (COND_TAG + '：句后条件扩展按「基础 type8 记录＋兄弟 sub 记录条件增幅」双记录映射'
               '（scope §2.4）；基础句值行来源＝' + parent_rec_key + '（无条件常时，方向逐行审核），'
               '条件增幅值行来源＝' + child_rec_key + '（link_kind=sub_effect）＋条件文本逐字'
               '「' + condition_verbatim + '」；门控证据分级 ' + tier + '；两值行不合并、不写跨记录'
               '乘积；type36/80/67/1005 规则同样 occurrences 未登记，兄弟记录值行按同类型原生规则'
               '外推，未逐记录审定——行级「推断」，不升「确认」，不进入整行确认。基础句值行适用'
               '范围：' + base_scope)
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                attrs=mapped, claims=sorted(claims), tail=tail, verdict='PROMOTE',
                child_record_id=child_id, child_effect_type=child_type, gate_tier=tier,
                condition_verbatim=condition_verbatim, section_no=section_no,
                section_count=section_count)
